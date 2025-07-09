#!/usr/bin/env python3
"""
Script pour initialiser tout le stock actuel à 1
"""

import sqlite3

DB_PATH = "/Users/mhoar/Desktop/python_vscode/price_comparison.db"

def init_all_stock_to_one():
    """Initialise tout le stock actuel à 1"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("📦 Initialisation de tous les stocks à 1...")
        
        # Vider la table existante
        cursor.execute("DELETE FROM stock_actuel")
        print("🗑️  Table stock_actuel vidée")
        
        # Récupérer tous les articles commandables
        query = """
            SELECT DISTINCT
                code_article,
                libelle_article,
                AVG(prix_tarif) as prix_tarif_moy,
                MIN(nom_fournisseur) as fournisseur
            FROM vente_meti
            WHERE annee = 2025
                AND code_article IS NOT NULL
                AND code_article != ''
                AND commandable = 'O'
            GROUP BY code_article, libelle_article
        """
        
        cursor.execute(query)
        articles = cursor.fetchall()
        
        print(f"📊 {len(articles)} articles trouvés")
        
        # Insérer tous les articles avec stock = 1
        count = 0
        for article in articles:
            code_article, libelle, prix_tarif, fournisseur = article
            
            # Prix d'achat estimé (70% du prix tarif)
            prix_achat = (prix_tarif or 10) * 0.7
            
            # Insérer avec stock = 1
            cursor.execute("""
                INSERT INTO stock_actuel 
                (code_article, libelle_article, stock_actuel, prix_achat, fournisseur_principal, date_maj)
                VALUES (?, ?, 1, ?, ?, CURRENT_TIMESTAMP)
            """, (code_article, libelle, prix_achat, fournisseur))
            
            count += 1
            
            if count % 500 == 0:
                print(f"   ✅ {count} articles traités...")
        
        conn.commit()
        print(f"\n✅ Stock initialisé à 1 pour {count} articles")
        
        # Vérification
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                MIN(stock_actuel) as stock_min,
                MAX(stock_actuel) as stock_max,
                AVG(stock_actuel) as stock_moy
            FROM stock_actuel
        """)
        
        stats = cursor.fetchone()
        print(f"\n📈 Vérification:")
        print(f"   - Total articles: {stats[0]}")
        print(f"   - Stock minimum: {stats[1]}")
        print(f"   - Stock maximum: {stats[2]}")
        print(f"   - Stock moyen: {stats[3]:.1f}")
        
        # Afficher quelques exemples
        cursor.execute("""
            SELECT code_article, libelle_article, stock_actuel
            FROM stock_actuel
            LIMIT 5
        """)
        
        print(f"\n📋 Exemples:")
        for row in cursor.fetchall():
            print(f"   - {row[0]}: {row[1][:50]}... (stock: {row[2]})")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Initialisation de tous les stocks à 1")
    print("=" * 50)
    
    init_all_stock_to_one()
    print("\n✅ Terminé! Tous les stocks sont maintenant à 1")