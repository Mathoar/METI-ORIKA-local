import pandas as pd
import sqlite3
import logging
import unicodedata
from services.utils import DB_NAME

logger = logging.getLogger(__name__)

def normalize_column(col):
    if not isinstance(col, str):
        return str(col).upper()
    col = ''.join(c for c in unicodedata.normalize('NFD', col) if unicodedata.category(c) != 'Mn')
    return col.replace(' ', '').replace('-', '').replace('.', '').replace('°', '').upper()

def process_orika_file(file_path):
    try:
        logger.info("Lecture fichier ORIKA forcée à la ligne 10...")
        df = pd.read_csv(file_path, sep=";", encoding="utf-8", skiprows=9)
        logger.info(f"ORIKA : {len(df)} lignes chargées.")

        df.columns = [normalize_column(col) for col in df.columns]
        logger.info(f"Normalized columns in ORIKA DataFrame: {df.columns.tolist()}")

        required = ['LIBELLE', 'CATTC', 'NBARTICLESVENDUS']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns in ORIKA DataFrame: {missing}")

        # Suppression des entêtes dupliquées
        df = df[df['LIBELLE'].str.upper() != 'LIBELLE']
        df = df[df['CATTC'].astype(str).str.upper() != 'CATTC']
        df = df[df['NBARTICLESVENDUS'].astype(str).str.upper() != 'NBARTICLESVENDUS']

        # Nettoyage et conversion
        df['LIBELLE'] = df['LIBELLE'].str.strip().str.upper()
        df['CATTC'] = df['CATTC'].astype(str).str.replace(',', '.').astype(float)
        df['NBARTICLESVENDUS'] = df['NBARTICLESVENDUS'].astype(str).str.replace(',', '.').astype(float)

        # Prix unitaire
        df['PRIX_UNIT'] = df.apply(
            lambda x: x['CATTC'] / x['NBARTICLESVENDUS'] if x['NBARTICLESVENDUS'] else 0, axis=1
        )

        # Agrégation
        grouped = df.groupby('LIBELLE').agg({
            'CATTC': 'sum',
            'NBARTICLESVENDUS': 'sum',
            'PRIX_UNIT': ['min', 'max']
        }).reset_index()

        grouped.columns = ['libelle', 'cattc', 'nb_articles_vendus', 'prix_min', 'prix_max']
        grouped['prix_caisse'] = grouped.apply(
            lambda x: x['cattc'] / x['nb_articles_vendus'] if x['nb_articles_vendus'] else 0, axis=1
        )

        # Enrichissement via ref_frs
        with sqlite3.connect(DB_NAME) as conn:
            df_frs = pd.read_sql_query("SELECT article_meti, libelle_article, pcb_commandable FROM ref_frs", conn)
            df_frs = df_frs.dropna(subset=["article_meti", "libelle_article"])
            df_frs['libelle_normalise'] = df_frs['libelle_article'].str.strip().str.upper().str.replace(' ', '')
            df_frs['pcb_commandable'] = df_frs['pcb_commandable'].fillna('').astype(str)

            # Prioriser pcb_commandable = 0
            df_frs['priorite'] = df_frs['pcb_commandable'].apply(lambda x: 0 if x.strip() == "0" else 1)
            df_frs = df_frs.sort_values('priorite').drop_duplicates(subset=['libelle_normalise'], keep='first')

            grouped['libelle_normalise'] = grouped['libelle'].str.strip().str.upper().str.replace(' ', '')
            enriched = grouped.merge(
                df_frs[['article_meti', 'libelle_normalise']],
                on='libelle_normalise',
                how='left'
            )
            enriched = enriched.rename(columns={"article_meti": "Code_article"})
            enriched.drop(columns=['libelle_normalise'], inplace=True)

            # Insertion en base
            cursor = conn.cursor()
            cursor.execute("DELETE FROM orika")
            for _, row in enriched.iterrows():
                cursor.execute('''
                    INSERT INTO orika (libelle, cattc, nb_articles_vendus, prix_caisse, prix_min, prix_max, Code_article)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['libelle'],
                    row['cattc'],
                    row['nb_articles_vendus'],
                    row['prix_caisse'],
                    row['prix_min'],
                    row['prix_max'],
                    row.get('Code_article')
                ))
            conn.commit()

        logger.info("✅ Données ORIKA enrichies et insérées sans doublons via ref_frs.")

        summary = {
            "nb_lignes": len(df),
            "nb_articles": enriched['libelle'].nunique(),
            "ca_total": round(df['CATTC'].sum(), 2),
            "passage_total": int(df['NBARTICLESVENDUS'].sum()),
            "marge_total": round(
                df['MARGE'].astype(str).str.replace(',', '.').astype(float).sum(), 2
            ) if 'MARGE' in df.columns else 0.0
        }

        return enriched.to_dict(orient="records"), summary

    except Exception as e:
        logger.error(f"Erreur dans process_orika_file : {e}")
        raise
