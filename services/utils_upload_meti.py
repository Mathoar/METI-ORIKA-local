import sqlite3
import pandas as pd
import logging
from services.utils import DB_NAME
from services.utils_upload_shared import (
    normalize_column,
    clean_currency,
    clean_meti_excel
)

logger = logging.getLogger(__name__)

def insert_meti_data(df):
    try:
        logger.info(f"🔵 insert_meti_data() - lignes reçues : {df.shape[0]}")
        df.columns = [normalize_column(col) for col in df.columns]
        logger.info(f"🟢 Colonnes normalisées : {df.columns.tolist()}")

        required_columns = ['NOMENCLATUREARTICLE', 'CAHT', 'PASSAGE', 'MARGE', 'PM', 'TDM', 'POIDSPROMO']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Colonnes manquantes : {missing}")

        # Nettoyage des données
        df['NOMENCLATUREARTICLE'] = df['NOMENCLATUREARTICLE'].fillna('Unknown').astype(str)
        df['CAHT'] = df['CAHT'].apply(clean_currency)
        df['PASSAGE'] = df['PASSAGE'].fillna(0).astype(float)
        df['MARGE'] = df['MARGE'].apply(clean_currency)
        df['PM'] = df['PM'].apply(clean_currency)
        df['TDM'] = df['TDM'].fillna(0.0).astype(float)
        df['POIDSPROMO'] = df['POIDSPROMO'].fillna(0.0).astype(float)

        # Création des colonnes générées
        def split_nomenclature(val):
            if isinstance(val, str) and '-' in val:
                parts = val.split('-', 1)
                return parts[0].strip(), parts[1].strip().upper()
            return '', val.strip().upper() if isinstance(val, str) else ''

        df[['GENERATED_ID', 'GENERATED_ARTICLE']] = df['NOMENCLATUREARTICLE'].apply(lambda x: pd.Series(split_nomenclature(x)))

        # Colonnes finales pour insertion
        df = df[['NOMENCLATUREARTICLE', 'CAHT', 'PASSAGE', 'MARGE', 'PM', 'TDM', 'POIDSPROMO', 'GENERATED_ARTICLE', 'GENERATED_ID']]

        # Séparation des données valides et ruptures
        df_valid = df[df['CAHT'].notnull() & (df['CAHT'] > 0)]
        df_rupture = df[~(df['CAHT'].notnull() & (df['CAHT'] > 0))]

        logger.info(f"🟩 Lignes valides : {len(df_valid)} | 🟥 Ruptures : {len(df_rupture)}")
        logger.info("📋 Exemple ligne valide :\n" + df_valid.head(1).to_string(index=False))

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            for _, row in df_valid.iterrows():
                cursor.execute('''INSERT OR REPLACE INTO meti (
                    nomenclature, ca_ht, passage, marge, pm, tdm, poids_promo, generated_article, generated_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', tuple(row))

            for _, row in df_rupture.iterrows():
                cursor.execute('''INSERT INTO rupture_meti (
                    nomenclature, ca_ht, passage, marge, pm, tdm, poids_promo, generated_article, generated_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', tuple(row))

            conn.commit()

        logger.info("✅ Insertion dans la base réussie.")
        return True

    except Exception as e:
        logger.error(f"❌ Erreur dans insert_meti_data : {e}")
        return False


def process_meti_file(file_path, header_row, data_row):
    try:
        logger.info("🔄 process_meti_file() lancé")
        cleaned_path = file_path.replace('.xlsx', '_cleaned.xlsx')

        if not clean_meti_excel(file_path, cleaned_path, header_row, data_row):
            raise ValueError("Erreur lors du nettoyage du fichier METI.")

        logger.info(f"📄 Lecture du fichier nettoyé : {cleaned_path}")
        df = pd.read_excel(cleaned_path)
        logger.info(f"📊 Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

        success = insert_meti_data(df)

        if not success:
            raise ValueError("Erreur lors de l'insertion des données METI.")

        summary = {
            "nb_lignes": len(df),
            "nb_articles": df['NOMENCLATUREARTICLE'].nunique(),
            "ca_total": df['CAHT'].sum(),
            "passage_total": df['PASSAGE'].sum(),
            "marge_total": df['MARGE'].sum()
        }

        logger.info(f"📈 Synthèse METI : {summary}")
        return df[['GENERATED_ID', 'GENERATED_ARTICLE', 'CAHT', 'PASSAGE', 'MARGE', 'PM', 'TDM', 'POIDSPROMO']].values.tolist(), summary

    except Exception as e:
        logger.error(f"❌ Erreur dans process_meti_file : {e}")
        raise
