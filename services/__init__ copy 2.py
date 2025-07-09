#!/usr/bin/env python3
"""
Test simple de la requête commande_vente
"""

import sqlite3
import pandas as pd
import numpy as np

DB_PATH = "/Users/mhoar/Desktop/python_vscode/price_comparison.db"

def test_suggestions_simple():
    conn = sqlite3.connect(DB_PATH)
    
    try:
        print("🧪 Test de génération de suggestions\n")
        
        # 1. Récupérer les données par département
        query = """
            SELECT 
                departement,
                libelle_departement,
                semaine,
                SUM(ca) as ca,
                SUM(qte) as qte,
                AVG(prix_tarif) as prix_tarif_moyen,
                AVG(prix_de_vente) as prix_vente_moyen,
                MIN(pcb) as pcb_min,
                AVG(marge) as marge_moyenne,
                COUNT(DISTINCT code_article) as nb_articles
            FROM vente_meti
            WHERE annee = 2025
              AND semaine BETWEEN 1 AND 10
              AND (commandable = 'O' OR commandable IS NULL)
            GROUP BY departement, libelle_departement, semaine
        """
        
        df_ventes = pd.read_sql_query(query, conn)
        print(f"✅ Données récupérées: {len(df_ventes)} lignes")
        print(f"   Colonnes: {list(df_ventes.columns)}")
        
        # 2. Grouper par département
        print("\n📊 Groupement par département:")
        grouped = df_ventes.groupby(['departement', 'libelle_departement'])
        
        suggestions = []
        for (dept, libelle), group_data in grouped:
            # Calculer les ventes par semaine
            ventes_semaine = group_data.groupby('semaine')['qte'].sum()
            vente_moyenne_hebdo = ventes_semaine.mean()
            
            # Informations agrégées
            info = {
                'code': dept,
                'libelle': libelle,
                'vente_moyenne': round(vente_moyenne_hebdo, 0),
                'nb_semaines': len(ventes_semaine),
                'prix_tarif': round(group_data['prix_tarif_moyen'].mean(), 2),
                'pcb': int(group_data['pcb_min'].min()) if pd.notna(group_data['pcb_min'].min()) else 1,
                'marge': round(group_data['marge_moyenne'].mean(), 1),
                'nb_articles': int(group_data['nb_articles'].sum() / len(group_data))
            }
            
            suggestions.append(info)
            print(f"   - {libelle}: {info['vente_moyenne']} unités/sem, {info['nb_articles']} articles")
        
        # 3. Trier et afficher
        suggestions.sort(key=lambda x: x['vente_moyenne'], reverse=True)
        
        print(f"\n✅ Total: {len(suggestions)} départements")
        
        # 4. Vérifier le stock
        print("\n📦 Vérification du stock par département:")
        query_stock = """
            SELECT 
                v.departement,
                v.libelle_departement,
                COUNT(DISTINCT s.code_article) as articles_avec_stock,
                SUM(s.stock_actuel) as stock_total
            FROM vente_meti v
            LEFT JOIN stock_actuel s ON v.code_article = s.code_article
            WHERE v.annee = 2025
            GROUP BY v.departement, v.libelle_departement
        """
        
        df_stock = pd.read_sql_query(query_stock, conn)
        print(df_stock.head())
        
        # 5. Test calcul simple pour un département
        print("\n🔧 Test calcul pour DPH (département 1):")
        
        # Vente moyenne
        vente_dph = df_ventes[df_ventes['departement'] == '1'].groupby('semaine')['qte'].sum().mean()
        print(f"   - Vente moyenne hebdo: {vente_dph:.0f} unités")
        
        # Stock actuel
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT s.code_article), SUM(s.stock_actuel)
            FROM stock_actuel s
            WHERE s.code_article IN (
                SELECT DISTINCT code_article 
                FROM vente_meti 
                WHERE departement = '1' AND annee = 2025
            )
        """)
        nb_art, stock_total = cursor.fetchone()
        print(f"   - Articles avec stock: {nb_art}")
        print(f"   - Stock total: {stock_total}")
        
        # Calcul suggestion
        vente_jour = vente_dph / 7
        coverage = 21  # jours
        safety = 1.2
        besoin = vente_jour * coverage * safety
        suggestion = max(0, besoin - (stock_total or 0))
        
        print(f"   - Besoin théorique: {besoin:.0f} unités")
        print(f"   - Suggestion commande: {suggestion:.0f} unités")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    test_suggestions_simple()