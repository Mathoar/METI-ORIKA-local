# services/utils_upload_stock.py
import pandas as pd
import sqlite3
import logging
import unicodedata
import re

logger = logging.getLogger(__name__)
DB_NAME = "price_comparison.db"

def normalize_column_name(col):
    """Nettoie et normalise les noms de colonnes."""
    col = unicodedata.normalize('NFKD', str(col)).encode('ASCII', 'ignore').decode('utf-8')
    col = re.sub(r'[^a-zA-Z0-9]', '_', col)
    col = re.sub(r'_+', '_', col).strip('_')
    return col.upper()


def reset_stock_table():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stock")
            conn.commit()
            logger.info("Table 'stock' cleared.")
        return True
    except Exception as e:
        logger.error(f"Error resetting stock table: {e}")
        return False

def insert_stock_data(df):
    """Insère les données stock dans la table SQLite."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            # Normaliser les colonnes
            df.columns = [normalize_column_name(col) for col in df.columns]
            logger.info(f"Colonnes stock normalisées : {df.columns.tolist()}")

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

            missing = [col for col in expected_mapping if col not in df.columns]
            if missing:
                logger.error(f"Colonnes manquantes pour import stock : {missing}")
                return False

            df = df.rename(columns=expected_mapping)
            logger.info(f"Sample code_article values before cleaning: {df['code_article'].head(10).tolist()}")  # Debug log

            # Clean code_article to remove .0 and handle all cases
            df['code_article'] = df['code_article'].apply(
                lambda x: str(int(float(str(x).strip()))) if pd.notna(x) and str(x).replace('.', '').isdigit() else str(x).strip()
            )
            logger.info(f"Sample code_article values after cleaning: {df['code_article'].head(10).tolist()}")  # Debug log

            # Clean other columns
            df['stock_article'] = pd.to_numeric(df['stock_article'], errors='coerce').fillna(0)
            for col in expected_mapping.values():
                if col not in ['stock_article', 'code_article']:
                    df[col] = df[col].fillna('Inconnu').astype(str)

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
            # Debug: Verify inserted data
            cursor.execute("SELECT code_article FROM stock LIMIT 10")
            inserted_codes = [row[0] for row in cursor.fetchall()]
            logger.info(f"Sample code_article values in database: {inserted_codes}")

            return True

    except Exception as e:
        logger.error(f"Erreur insertion données stock : {e}")
        return False