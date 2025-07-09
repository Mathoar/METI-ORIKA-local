import sqlite3
import logging
import pandas as pd
from flask import request
from collections import defaultdict

logger = logging.getLogger(__name__)

def get_db_path():
    return "/Users/mhoar/Desktop/python_vscode/price_comparison.db"

def get_analyse_cde_data(request):
    db_path = get_db_path()
    filters = []
    params = []
    colonnes_standards = [
        'code_article', 'libelle_article', 'qte', 'ca', 'ca_ht', 'annee', 'nb_semaine',
        'nom_fournisseur', 'libelle_departement', 'libelle_rayon', 'libelle_famille',
        'libelle_sous_famille', 'ean', 'libelle_marque', 'prix_tarif', 'prix_de_vente',
        'code_tva', 'pcb', 'date_derniere_commande', 'commandable', 'marge', 'module',
        'pcb_mini_commandable', 'taux_tva', 'libelle_unite_de_besoin', 'svap_ttc',
        'pv_conseille', 'pcb_commandable', 'code_etat', 'dispo_sodex'
    ]
    selected_columns = request.args.getlist("colonnes") or colonnes_standards

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(analyse_cde)")
            all_columns = [row[1] for row in cursor.fetchall()]
            colonnes_optionnelles = sorted([col for col in all_columns if col not in colonnes_standards])

            query = f"SELECT {', '.join(selected_columns)} FROM analyse_cde WHERE 1=1 {' '.join(filters)}"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            rows_dicts = [{col: val for col, val in zip(selected_columns, row)} for row in rows]

            # Groupement par fournisseur puis par département
            grouped_by_fournisseur = defaultdict(lambda: defaultdict(list))
            for row in rows_dicts:
                nom_fournisseur = row.get("nom_fournisseur") or "Inconnu"
                departement = row.get("libelle_departement") or "Inconnu"
                grouped_by_fournisseur[nom_fournisseur][departement].append(row)

            regroupements = []
            for nom_fournisseur, deps in grouped_by_fournisseur.items():
                fournisseur_data = {
                    "group_name": nom_fournisseur,
                    "departements": [],
                    "total_nb_articles": 0,
                    "total_qte": 0,
                    "total_ca": 0
                }
                for departement, articles in deps.items():
                    qte = sum(float(a.get("qte") or 0) for a in articles)
                    ca = sum(float(a.get("ca") or 0) for a in articles)
                    articles_sorted = sorted(articles, key=lambda x: float(x.get("qte") or 0), reverse=True)
                    departement_data = {
                        "group_name": departement,
                        "nb_articles": len(articles),
                        "total_qte": round(qte, 2),
                        "total_ca": round(ca, 2),
                        "articles": articles_sorted
                    }
                    fournisseur_data["departements"].append(departement_data)
                    fournisseur_data["total_nb_articles"] += len(articles)
                    fournisseur_data["total_qte"] += qte
                    fournisseur_data["total_ca"] += ca

                regroupements.append(fournisseur_data)

            # Tri des fournisseurs par Total QTE ou Total CA
            sort_by = request.args.get("sort_by", "total_qte")
            reverse_order = request.args.get("order", "desc") == "desc"
            regroupements.sort(key=lambda g: g[sort_by], reverse=reverse_order)

            return {
                "grouped_rows": regroupements,
                "selected_columns": selected_columns,
                "colonnes_standards": colonnes_standards,
                "colonnes_optionnelles": colonnes_optionnelles,
            }
    except Exception as e:
        logging.error(f"Erreur analyse commande : {e}")
        return {
            "grouped_rows": [],
            "selected_columns": colonnes_standards,
            "colonnes_standards": colonnes_standards,
            "colonnes_optionnelles": [],
        }

def inserer_donnees_analyse_cde():
    try:
        with sqlite3.connect(get_db_path()) as conn:
            # Vente METI
            df_vente = pd.read_sql_query("""
                SELECT code_article, libelle_article, qte, ca, ca_ht, annee, nb_semaine FROM vente_meti
            """, conn)
            df_vente["code_etat"] = "Vente"

            # Rupture METI
            df_rupture = pd.read_sql_query("""
                SELECT generated_id AS code_article FROM rupture_meti
            """, conn)
            df_rupture = df_rupture.assign(
                libelle_article="", qte=0, ca=0, ca_ht=0, annee=2025, nb_semaine=1,
                code_etat="Rupture"
            )

            # Fournisseurs
            df_frs = pd.read_sql_query("SELECT * FROM ref_frs", conn)
            df_frs["article"] = df_frs["article"].astype(str)
            df_frs["libelle_article"] = df_frs["libelle_article"].fillna("")
            df_vente["code_article"] = df_vente["code_article"].astype(str)
            df_rupture["code_article"] = df_rupture["code_article"].astype(str)

            # Stock
            stock_codes = pd.read_sql_query("SELECT DISTINCT code_article FROM stock", conn)["code_article"].astype(str).tolist()

            # Fusion ventes + frs
            df_vente = df_vente.merge(df_frs, left_on="code_article", right_on="article", how="left")
            df_rupture = df_rupture.merge(df_frs, left_on="code_article", right_on="article", how="left")

            # Remplir les libellés manquants
            df_vente["libelle_article"] = df_vente["libelle_article_x"].combine_first(df_vente["libelle_article_y"])
            df_rupture["libelle_article"] = df_rupture["libelle_article_y"]

            # dispo_sodex
            def dispo(row):
                marque = row.get("code_marque", "")
                if marque == "MN":
                    return 3
                if marque in ("Inconnu", "", None):
                    return 0
                return 1 if row.get("code_article") in stock_codes else 0

            df_vente["dispo_sodex"] = df_vente.apply(dispo, axis=1)
            df_rupture["dispo_sodex"] = df_rupture.apply(dispo, axis=1)

            # Colonnes attendues
            colonnes = [
                "code_article", "libelle_article", "qte", "ca", "ca_ht", "annee", "nb_semaine",
                "fournisseur", "departement", "rayon", "famille", "sous_famille", "ean", "libelle_marque",
                "libelle_famille", "libelle_departement", "libelle_rayon", "libelle_sous_famille", "code_marque",
                "nom_fournisseur", "prix_tarif", "prix_de_vente", "code_tva", "pcb", "date_derniere_commande",
                "commandable", "marge", "module", "pcb_mini_commandable", "taux_tva", "libelle_unite_de_besoin",
                "svap_ttc", "pv_conseille", "pcb_commandable", "code_etat", "dispo_sodex"
            ]

            # Concat
            df_final = pd.concat([df_vente, df_rupture], ignore_index=True)

            # Ajout colonnes manquantes
            for col in colonnes:
                if col not in df_final.columns:
                    df_final[col] = ""

            # Réduction aux colonnes utiles
            df_final = df_final[colonnes].fillna("")
            df_final = df_final[df_final['pcb_commandable'].astype(str) == 'O']
            

            if df_final.empty:
                return {"status": "ok", "nb_lignes": 0, "message": "Aucune ligne après fusion"}

            df_final.to_sql("analyse_cde", conn, if_exists="replace", index=False)
            return {"status": "ok", "nb_lignes": len(df_final)}

    except Exception as e:
        return {"status": "error", "message": str(e)}
