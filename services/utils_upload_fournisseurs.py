import pandas as pd
import sqlite3
import logging

logger = logging.getLogger(__name__)

def insert_fournisseurs_data(filepath, db_path):
    try:
        # Read CSV
        df = pd.read_csv(filepath, sep=';', encoding='utf-8')
        df.columns = df.columns.str.strip()
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        logger.info(f"Lignes dans le fichier CSV : {len(df)}")

        # Column mapping
        column_mapping = {
            'Département': 'departement',
            'Rayon': 'rayon',
            'Famille': 'famille',
            'Sous-famille': 'sous_famille',
            'Code UBS': 'code_ubs',
            'Article': 'article',
            'EAN': 'ean',
            'Libellé article': 'libelle_article',
            'Four.': 'fournisseur',
            'Var.': 'variete',
            'Prix tarif': 'prix_tarif',
            'Prix de vente': 'prix_de_vente',
            'Code etat': 'code_etat',
            'Nom fournisseur': 'nom_fournisseur',
            'Unité de mesure': 'unite_de_mesure',
            'Unite de vente': 'unite_de_vente',
            'Poids en (Kg)': 'poids_kg',
            'Code taxe': 'code_taxe',
            'Montant taxe': 'montant_taxe',
            'Code tva': 'code_tva',
            'PCB': 'pcb',
            'Réf. 1': 'ref_1',
            'Réf. 2': 'ref_2',
            'Libellé marque': 'libelle_marque',
            'Libellé compl.': 'libelle_complementaire',
            'Date dernière commande': 'date_derniere_commande',
            'Princ.': 'principal',
            'Code classe': 'code_classe',
            'Commandable ?': 'commandable',
            'Marge': 'marge',
            'Module': 'module',
            'PCB Mini commandable': 'pcb_mini_commandable',
            'Libellé famille': 'libelle_famille',
            'Taux TVA': 'taux_tva',
            'Libellé département': 'libelle_departement',
            'Libellé rayon': 'libelle_rayon',
            'Libellé sous-famille': 'libelle_sous_famille',
            'Libellé unité de besoin': 'libelle_unite_de_besoin',
            'Nom site': 'nom_site',
            'UL': 'ul',
            'SVAP TTC': 'svap_ttc',
            'Suivi en stock': 'suivi_en_stock',
            'PV conseillé': 'pv_conseille',
            'Article METI': 'article_meti',
            'Code prix cession': 'code_prix_cession',
            'Code marketing': 'code_marketing',
            'Code marque': 'code_marque',
            "Mode d'approvisionnement": 'mode_d_approvisionnement',
            'PCB Commandable': 'pcb_commandable'
        }

        df.rename(columns=column_mapping, inplace=True)

        # Define expected table columns
        table_columns = [
            'departement', 'rayon', 'famille', 'sous_famille', 'code_ubs', 'article',
            'ean', 'libelle_article', 'fournisseur', 'variete', 'prix_tarif',
            'prix_de_vente', 'code_etat', 'nom_fournisseur', 'unite_de_mesure',
            'unite_de_vente', 'poids_kg', 'code_taxe', 'montant_taxe', 'code_tva',
            'pcb', 'ref_1', 'ref_2', 'libelle_marque', 'libelle_complementaire',
            'date_derniere_commande', 'principal', 'code_classe', 'commandable',
            'marge', 'module', 'pcb_mini_commandable', 'libelle_famille', 'taux_tva',
            'libelle_departement', 'libelle_rayon', 'libelle_sous_famille',
            'libelle_unite_de_besoin', 'nom_site', 'ul', 'svap_ttc', 'suivi_en_stock',
            'pv_conseille', 'article_meti', 'code_prix_cession', 'code_marketing',
            'code_marque', 'mode_d_approvisionnement', 'pcb_commandable'
        ]

        # Select relevant columns
        df_filtered = df[[col for col in table_columns if col in df.columns]]
        logger.info(f"Lignes après sélection des colonnes : {len(df_filtered)}")

        # Filter for principal = '0'
        df_filtered = df_filtered[(df_filtered['principal'].astype(str) == 'O') & 
                          (df_filtered['pcb_commandable'].astype(str) == 'O')]
        logger.info(f"Lignes après filtrage principal = '0' : {len(df_filtered)}")

        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ref_frs")
        logger.info("Table ref_frs vidée avant insertion")

        # Insert filtered data
        if df_filtered.empty:
            logger.warning("Aucune ligne à insérer après filtrage principal = 'O'")
            conn.commit()
            conn.close()
            return {"status": "ok", "nb_lignes": 0, "message": "Aucune ligne à insérer après filtrage principal = '0'"}

        df_filtered.to_sql('ref_frs', conn, if_exists='append', index=False)
        conn.commit()
        logger.info(f"Insertion réussie : {len(df_filtered)} lignes insérées dans ref_frs")
        conn.close()

        return {"status": "ok", "nb_lignes": len(df_filtered), "message": f"{len(df_filtered)} lignes insérées avec principal = '0'"}

    except Exception as e:
        logger.error(f"Erreur lors de l'insertion : {str(e)}")
        if 'conn' in locals():
            conn.close()
        return {"status": "error", "message": f"Erreur lors de l'insertion : {str(e)}"}