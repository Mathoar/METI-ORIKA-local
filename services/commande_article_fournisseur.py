import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

DB_PATH = "/Users/mhoar/Desktop/python_vscode/price_comparison.db"

def get_suggestions_articles_fournisseurs(annee, semaine_debut, semaine_fin, methode='moyenne', coverage=21, safety=1.2, filtres=None):
    """
    Génère des suggestions de commande au niveau article avec informations fournisseur
    Prend en compte les performances des produits
    """
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Requête pour récupérer les données article par article
        query = """
            SELECT 
                v.code_article,
                v.libelle_article,
                v.nom_fournisseur,
                v.fournisseur as code_fournisseur,
                v.semaine,
                SUM(v.qte) as qte,
                SUM(v.ca) as ca,
                AVG(v.prix_tarif) as prix_tarif,
                AVG(v.prix_de_vente) as prix_vente,
                v.pcb,
                v.pcb_mini_commandable as pcb_mini,
                AVG(v.marge) as marge,
                v.departement,
                v.libelle_departement,
                v.rayon,
                v.libelle_rayon,
                v.famille,
                v.libelle_famille,
                v.libelle_sous_famille
            FROM vente_meti v
            WHERE v.annee = ?
              AND v.semaine BETWEEN ? AND ?
              AND v.commandable = 'O'
              AND v.code_article IS NOT NULL
              AND v.nom_fournisseur IS NOT NULL
        """
        
        params = [annee, semaine_debut, semaine_fin]
        
        # Ajouter les filtres si nécessaire
        if filtres:
            if 'departement' in filtres:
                query += " AND v.libelle_departement = ?"
                params.append(filtres['departement'])
            if 'rayon' in filtres:
                query += " AND v.libelle_rayon = ?"
                params.append(filtres['rayon'])
            if 'famille' in filtres:
                query += " AND v.libelle_famille = ?"
                params.append(filtres['famille'])
            if 'fournisseur' in filtres:
                query += " AND v.nom_fournisseur = ?"
                params.append(filtres['fournisseur'])
        
        query += " GROUP BY v.code_article, v.libelle_article, v.nom_fournisseur, v.semaine, v.pcb, v.pcb_mini_commandable"
        
        # Exécuter la requête
        df_ventes = pd.read_sql_query(query, conn, params=params)
        
        if df_ventes.empty:
            return []
        
        # Récupérer le stock actuel
        query_stock = """
            SELECT 
                code_article,
                stock_actuel,
                prix_achat
            FROM stock_actuel
        """
        df_stock = pd.read_sql_query(query_stock, conn)
        stock_dict = df_stock.set_index('code_article')['stock_actuel'].to_dict()
        
        # Calculer les suggestions par article
        suggestions = []
        articles_grouped = df_ventes.groupby(['code_article', 'libelle_article', 'nom_fournisseur'])
        
        for (code_article, libelle_article, fournisseur), article_data in articles_grouped:
            # Calculer les ventes par semaine
            ventes_par_semaine = article_data.groupby('semaine')['qte'].sum()
            nb_semaines = len(ventes_par_semaine)
            
            if nb_semaines == 0:
                continue
            
            # Calcul selon la méthode
            if methode == 'moyenne':
                vente_moyenne_hebdo = ventes_par_semaine.mean()
            elif methode == 'tendance':
                if nb_semaines > 1:
                    x = np.arange(nb_semaines)
                    y = ventes_par_semaine.values
                    z = np.polyfit(x, y, 1)
                    vente_moyenne_hebdo = max(0, z[0] * nb_semaines + z[1])
                else:
                    vente_moyenne_hebdo = ventes_par_semaine.mean()
            elif methode == 'pic':
                vente_moyenne_hebdo = ventes_par_semaine.max()
            else:
                vente_moyenne_hebdo = ventes_par_semaine.mean()
            
            # Conversion en vente journalière
            vente_moyenne_jour = vente_moyenne_hebdo / 7
            
            # Informations article
            info = article_data.iloc[0]
            pcb = int(info['pcb']) if pd.notna(info['pcb']) and info['pcb'] > 0 else 1
            pcb_mini = int(info['pcb_mini']) if pd.notna(info['pcb_mini']) and info['pcb_mini'] > 0 else pcb
            prix_tarif = float(info['prix_tarif']) if pd.notna(info['prix_tarif']) else 0
            prix_vente = float(info['prix_vente']) if pd.notna(info['prix_vente']) else 0
            marge = float(info['marge']) if pd.notna(info['marge']) else 0
            
            # Stock actuel
            stock_actuel = stock_dict.get(code_article, 0)
            
            # Calcul de la couverture
            if vente_moyenne_jour > 0:
                couverture_actuelle = stock_actuel / vente_moyenne_jour
            else:
                couverture_actuelle = 999 if stock_actuel > 0 else 0
            
            # Calcul de la quantité suggérée
            besoin_theorique = vente_moyenne_jour * coverage * safety
            quantite_suggeree = max(0, besoin_theorique - stock_actuel)
            
            # Arrondir au PCB
            quantite_suggeree_pcb = 0
            if quantite_suggeree > 0:
                quantite_suggeree_pcb = np.ceil(quantite_suggeree / pcb) * pcb
                if quantite_suggeree_pcb < pcb_mini:
                    quantite_suggeree_pcb = pcb_mini
            
            # Calcul de la tendance
            tendance = 0
            if nb_semaines >= 2:
                debut = ventes_par_semaine.iloc[:nb_semaines//2].mean()
                fin = ventes_par_semaine.iloc[nb_semaines//2:].mean()
                if debut > 0:
                    tendance = ((fin - debut) / debut) * 100
            
            # Performance du produit (basée sur CA, marge et tendance)
            ca_total = article_data['ca'].sum()
            performance_score = (
                (ca_total / 1000) * 0.4 +  # CA normalisé
                (marge / 100) * 0.3 +       # Marge normalisée
                (tendance / 100) * 0.3      # Tendance normalisée
            )
            
            # Alertes
            rupture = stock_actuel == 0 and vente_moyenne_jour > 0
            stock_faible = couverture_actuelle < 7 and not rupture
            forte_rotation = vente_moyenne_hebdo > 50
            forte_marge = marge > 30
            recommande = rupture or stock_faible or (forte_rotation and forte_marge) or tendance > 20
            
            suggestions.append({
                'id': str(abs(hash(f"{code_article}_{fournisseur}"))),
                'code': code_article,
                'libelle': libelle_article,
                'fournisseur': fournisseur,
                'code_fournisseur': info['code_fournisseur'],
                'departement': info['libelle_departement'],
                'rayon': info['libelle_rayon'],
                'famille': info['libelle_famille'],
                'sous_famille': info['libelle_sous_famille'],
                'vente_moyenne': round(vente_moyenne_hebdo, 0),
                'stock_actuel': round(stock_actuel, 0),
                'couverture': round(couverture_actuelle, 0),
                'quantite_suggeree': round(quantite_suggeree, 0),
                'quantite_suggeree_pcb': round(quantite_suggeree_pcb, 0),
                'pcb': pcb,
                'pcb_mini': pcb_mini,
                'tendance': round(tendance, 1),
                'ca_total': round(ca_total, 0),
                'prix_tarif': prix_tarif,
                'prix_vente': prix_vente,
                'marge': round(marge, 1),
                'montant_estime': round(quantite_suggeree_pcb * prix_tarif, 0),
                'performance_score': round(performance_score, 2),
                'rupture': rupture,
                'stock_faible': stock_faible,
                'forte_rotation': forte_rotation,
                'forte_marge': forte_marge,
                'recommande': recommande,
                'selected': recommande,
                'nb_semaines_vente': nb_semaines
            })
        
        # Trier par performance et urgence
        suggestions.sort(key=lambda x: (
            -int(x['rupture']),  # Ruptures en premier
            -int(x['stock_faible']),  # Stock faible ensuite
            -x['performance_score'],  # Puis par performance
            -x['montant_estime']  # Enfin par montant
        ))
        
        return suggestions
        
    except Exception as e:
        print(f"Erreur dans get_suggestions_articles_fournisseurs: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        conn.close()

def get_top_fournisseurs(annee, semaine_debut, semaine_fin):
    """
    Récupère les top fournisseurs par CA et nombre d'articles
    """
    conn = sqlite3.connect(DB_PATH)
    
    try:
        query = """
            SELECT 
                nom_fournisseur,
                COUNT(DISTINCT code_article) as nb_articles,
                SUM(ca) as ca_total,
                AVG(marge) as marge_moyenne,
                COUNT(DISTINCT libelle_departement) as nb_departements
            FROM vente_meti
            WHERE annee = ?
              AND semaine BETWEEN ? AND ?
              AND commandable = 'O'
              AND nom_fournisseur IS NOT NULL
            GROUP BY nom_fournisseur
            ORDER BY ca_total DESC
            LIMIT 20
        """
        
        df = pd.read_sql_query(query, conn, params=[annee, semaine_debut, semaine_fin])
        return df.to_dict('records')
        
    finally:
        conn.close()