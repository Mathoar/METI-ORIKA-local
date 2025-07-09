# services/fournisseur_service.py
import sqlite3
import pandas as pd
from collections import defaultdict

def create_fournisseur_actif_table(db_path):
    """Crée la table Fournisseur_actif dans la base de données et retourne les données."""
    try:
        conn = sqlite3.connect(db_path)
        ref_frs_data = pd.read_sql_query("SELECT * FROM ref_frs", conn)
        fournisseur_actif_data = ref_frs_data[
            ['article', 'ean', 'libelle_article', 'fournisseur', 'nom_fournisseur', 'prix_tarif']
        ].copy()
        fournisseur_actif_data['Actif'] = 'N'
        fournisseur_actif_data.to_sql('Fournisseur_actif', conn, if_exists='replace', index=False)

        # Récupérer les données de la table nouvellement créée
        created_table_data = pd.read_sql_query("SELECT * FROM Fournisseur_actif", conn)
        conn.close()
        return created_table_data.to_dict('records')
    except Exception as e:
        print(f"An error occurred: {e}")
        raise
def get_article_statistics(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Requête pour obtenir les statistiques des articles
    cursor.execute("""
        SELECT article, COUNT(DISTINCT fournisseur) as fournisseur_count
        FROM Fournisseur_actif
        GROUP BY article
        HAVING COUNT(DISTINCT fournisseur) > 1
    """)

    stats = cursor.fetchall()
    conn.close()

    # Convertir les résultats en dictionnaire
    stats_dict = {article: count for article, count in stats}
    return stats_dict

def get_articles_with_multiple_suppliers(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Requête pour obtenir les articles avec plusieurs fournisseurs
        cursor.execute("""
            SELECT article, GROUP_CONCAT(fournisseur, ', ') AS fournisseurs
            FROM Fournisseur_actif
            GROUP BY article
            HAVING COUNT(DISTINCT fournisseur) > 1
        """)

        articles = cursor.fetchall()
        conn.close()

        # Convertir les résultats en une liste de dictionnaires
        articles_list = [{'article': article, 'fournisseurs': fournisseurs.split(', ')} for article, fournisseurs in articles]
        return articles_list

    except Exception as e:
        print(f"Erreur lors de la récupération des articles avec plusieurs fournisseurs: {str(e)}")
        return []
