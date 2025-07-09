import sqlite3
import pandas as pd
import logging
import unicodedata
from services.utils import DB_NAME

logger = logging.getLogger(__name__)

def normalize_column(col):
    # Supprimer les accents et caractères spéciaux
    col = unicodedata.normalize('NFD', col).encode('ascii', 'ignore').decode('utf-8')
    col = col.strip().lower().replace(" ", "_").replace("-", "_")
    return col

def insert_vente_meti_data(df):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            df.columns = [normalize_column(col) for col in df.columns]

            df.to_sql("vente_meti", conn, if_exists="append", index=False)
            logger.info(f"{len(df)} lignes insérées dans vente_meti.")
        return True
    except Exception as e:
        logger.error(f"Erreur insertion vente_meti : {e}")
        return False

def process_vente_meti_file(file_path):
    try:
        df = pd.read_excel(file_path)
        success = insert_vente_meti_data(df)

        if not success:
            raise ValueError("Erreur lors de l'insertion des données vente METI.")

        return df.to_dict(orient='records')

    except Exception as e:
        logger.error(f"Erreur dans process_vente_meti_file : {e}")
        raise
