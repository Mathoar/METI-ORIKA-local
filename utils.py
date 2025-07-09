import sqlite3
import pandas as pd
import logging
import unicodedata
import re

# Logger
logger = logging.getLogger(__name__)

# Nom de la base
DB_NAME = "price_comparison.db"

def normalize_column_name(col):
    """Normalize column names: remove accents, special chars, uppercase."""
    col = unicodedata.normalize('NFKD', str(col)).encode('ASCII', 'ignore').decode('utf-8')
    col = re.sub(r'[^a-zA-Z0-9]', '_', col)
    col = re.sub(r'_+', '_', col).strip('_')
    return col.upper()

def insert_stock_data(df):
    """Insert stock data into the 'stock' table in the database."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            # Normaliser les noms de colonnes
            df.columns = [normalize_column_name(col) for col in df.columns]
            logger.info(f"Colonnes stock normalisées : {df.columns.tolist()}")

            # Mappage attendu
            expected_mapping = {
                'MAGASIN': 'magasin',
                'DEPARTEMENT': 'departement',
                'RAYON': 'rayon',
                'FAMILLE': 'famille',
                'SOUS_FAMILLE': 'sous_famille',
                'VAR': 'variete',
                'CODE_ART': 'code_article',
                'ARTICLE': 'article',
                'STOCK_ARTICLE': 'stock_article',
                'DERN_ENTREE': 'derniere_entree',
                'TYP': 'type',
                'MARQUE': 'marque'
            }

            # Vérification colonnes manquantes
            missing = [col for col in expected_mapping if col not in df.columns]
            if missing:
                logger.error(f"Colonnes manquantes dans le fichier stock : {missing}")
                return False

            # Renommer les colonnes
            df = df.rename(columns=expected_mapping)

            # Nettoyage
            df['stock_article'] = pd.to_numeric(df['stock_article'], errors='coerce').fillna(0)
            for col in ['magasin', 'departement', 'rayon', 'famille', 'sous_famille',
                        'variete', 'code_article', 'article', 'derniere_entree', 'type', 'marque']:
                df[col] = df[col].fillna('Inconnu').astype(str)

            # Insertion
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT INTO stock (
                        magasin, departement, rayon, famille, sous_famille,
                        variete, code_article, article, stock_article,
                        derniere_entree, type, marque
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(row[col] for col in expected_mapping.values()))

            conn.commit()
            logger.info(f"{len(df)} lignes insérées dans la table stock.")
            return True

    except Exception as e:
        logger.error(f"Erreur insertion données stock : {e}")
        return False
