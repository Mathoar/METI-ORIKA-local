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

def update_vente_meti_from_ref_frs():
    """
    Met à jour les champs de vente_meti avec les données de ref_frs
    basé sur la correspondance code_article = article
    """
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            
            # Requête de mise à jour
            update_query = """
                UPDATE vente_meti
                SET 
                    prix_tarif = (
                        SELECT rf.prix_tarif 
                        FROM ref_frs rf 
                        WHERE rf.article = vente_meti.code_article
                        LIMIT 1
                    ),
                    prix_de_vente = (
                        SELECT rf.prix_de_vente 
                        FROM ref_frs rf 
                        WHERE rf.article = vente_meti.code_article
                        LIMIT 1
                    ),
                    code_tva = (
                        SELECT rf.code_tva 
                        FROM ref_frs rf 
                        WHERE rf.article = vente_meti.code_article
                        LIMIT 1
                    ),
                    fournisseur = (
                        SELECT rf.fournisseur 
                        FROM ref_frs rf 
                        WHERE rf.article = vente_meti.code_article
                        LIMIT 1
                    ),
                    nom_fournisseur = (
                        SELECT rf.nom_fournisseur 
                        FROM ref_frs rf 
                        WHERE rf.article = vente_meti.code_article
                        LIMIT 1
                    ),
                    pcb = (
                        SELECT rf.pcb 
                        FROM ref_frs rf 
                        WHERE rf.article = vente_meti.code_article
                        LIMIT 1
                    ),
                    date_derniere_commande = (
                        SELECT rf.date_derniere_commande 
                        FROM ref_frs rf 
                        WHERE rf.article = vente_meti.code_article
                        LIMIT 1
                    ),
                    commandable = (
                        SELECT rf.commandable 
                        FROM ref_frs rf 
                        WHERE rf.article = vente_meti.code_article
                        LIMIT 1
                    ),
                    marge = (
                        SELECT rf.marge 
                        FROM ref_frs rf 
                        WHERE rf.article = vente_meti.code_article
                        LIMIT 1
                    ),
                    pcb_mini_commandable = (
                        SELECT rf.pcb_mini_commandable 
                        FROM ref_frs rf 
                        WHERE rf.article = vente_meti.code_article
                        LIMIT 1
                    ),
                    taux_tva = (
                        SELECT rf.taux_tva 
                        FROM ref_frs rf 
                        WHERE rf.article = vente_meti.code_article
                        LIMIT 1
                    ),
                    pv_conseille = (
                        SELECT rf.pv_conseille 
                        FROM ref_frs rf 
                        WHERE rf.article = vente_meti.code_article
                        LIMIT 1
                    ),
                    pcb_commandable = (
                        SELECT rf.pcb_commandable 
                        FROM ref_frs rf 
                        WHERE rf.article = vente_meti.code_article
                        LIMIT 1
                    )
                WHERE EXISTS (
                    SELECT 1 
                    FROM ref_frs rf 
                    WHERE rf.article = vente_meti.code_article
                )
            """
            
            cursor.execute(update_query)
            rows_updated = cursor.rowcount
            conn.commit()
            
            logger.info(f"✅ {rows_updated} lignes mises à jour dans vente_meti avec les données de ref_frs")
            
            # Statistiques de mise à jour
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_ventes,
                    COUNT(CASE WHEN prix_tarif IS NOT NULL THEN 1 END) as avec_prix_tarif,
                    COUNT(CASE WHEN fournisseur IS NOT NULL THEN 1 END) as avec_fournisseur,
                    COUNT(CASE WHEN commandable = 'OUI' THEN 1 END) as commandables
                FROM vente_meti
            """)
            
            stats = cursor.fetchone()
            logger.info(f"📊 Statistiques après mise à jour:")
            logger.info(f"   - Total articles vente: {stats[0]}")
            logger.info(f"   - Avec prix tarif: {stats[1]}")
            logger.info(f"   - Avec fournisseur: {stats[2]}")
            logger.info(f"   - Commandables: {stats[3]}")
            
            return rows_updated
            
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour vente_meti : {e}")
        raise

def update_vente_meti_from_ref_frs_optimized():
    """
    Version optimisée de la mise à jour utilisant une jointure
    Plus rapide pour de gros volumes de données
    """
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            
            # Créer une table temporaire avec les jointures
            cursor.execute("""
                CREATE TEMP TABLE temp_vente_update AS
                SELECT 
                    v.id as vente_id,
                    rf.prix_tarif,
                    rf.prix_de_vente,
                    rf.code_tva,
                    rf.fournisseur,
                    rf.nom_fournisseur,
                    rf.pcb,
                    rf.date_derniere_commande,
                    rf.commandable,
                    rf.marge,
                    rf.pcb_mini_commandable,
                    rf.taux_tva,
                    rf.pv_conseille,
                    rf.pcb_commandable
                FROM vente_meti v
                INNER JOIN ref_frs rf ON v.code_article = rf.article
            """)
            
            # Mettre à jour en utilisant la table temporaire
            cursor.execute("""
                UPDATE vente_meti
                SET 
                    prix_tarif = t.prix_tarif,
                    prix_de_vente = t.prix_de_vente,
                    code_tva = t.code_tva,
                    fournisseur = t.fournisseur,
                    nom_fournisseur = t.nom_fournisseur,
                    pcb = t.pcb,
                    date_derniere_commande = t.date_derniere_commande,
                    commandable = t.commandable,
                    marge = t.marge,
                    pcb_mini_commandable = t.pcb_mini_commandable,
                    taux_tva = t.taux_tva,
                    pv_conseille = t.pv_conseille,
                    pcb_commandable = t.pcb_commandable
                FROM temp_vente_update t
                WHERE vente_meti.id = t.vente_id
            """)
            
            rows_updated = cursor.rowcount
            
            # Supprimer la table temporaire
            cursor.execute("DROP TABLE temp_vente_update")
            
            conn.commit()
            
            logger.info(f"✅ {rows_updated} lignes mises à jour (méthode optimisée)")
            return rows_updated
            
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour optimisée : {e}")
        raise

def process_vente_meti_file(file_path):
    try:
        df = pd.read_excel(file_path)
        success = insert_vente_meti_data(df)

        if not success:
            raise ValueError("Erreur lors de l'insertion des données vente METI.")
        
        # Mettre à jour avec les données de ref_frs après l'insertion
        logger.info("Mise à jour des données avec ref_frs...")
        rows_updated = update_vente_meti_from_ref_frs()
        logger.info(f"{rows_updated} lignes enrichies avec les données fournisseurs")

        return df.to_dict(orient='records')

    except Exception as e:
        logger.error(f"Erreur dans process_vente_meti_file : {e}")
        raise