import os
import sqlite3
import logging
from flask import current_app
from services.utils import DB_NAME  # si besoin

logger = logging.getLogger(__name__)

def get_db_path():
    return "/Users/mhoar/Desktop/python_vscode/price_comparison.db"

def init_db():
    """Initialise la base SQLite avec toutes les tables nécessaires."""
    path = get_db_path()
    logger.info(f"Initialisation de la base de données à : {path}")

    try:
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()

            # 🔄 Supprimer les anciennes tables
            cursor.executescript("""
                DROP TABLE IF EXISTS analyse_cde;
                DROP TABLE IF EXISTS vente_meti;
            """)
            logger.info("✅ Tables supprimées")

            # Table meti
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meti (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nomenclature TEXT NOT NULL,
                    ca_ht REAL NOT NULL,
                    passage REAL,
                    marge REAL,
                    pm REAL NOT NULL,
                    tdm REAL,
                    poids_promo REAL,
                    generated_article TEXT,
                    generated_id TEXT
                )
            """)
            logger.info("✅ Table créée : meti")

            # Table orika
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orika (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    libelle TEXT NOT NULL,
                    cattc REAL,
                    nb_articles_vendus REAL,
                    prix_caisse REAL,
                    prix_min REAL,
                    prix_max REAL,
                    Code_article TEXT
                )
            """)
            logger.info("✅ Table créée : orika")

            # Table vente_meti
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vente_meti (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    n_ligne INTEGER,
                    site TEXT,
                    libelle_site TEXT,
                    departement TEXT,
                    libelle_departement TEXT,
                    rayon TEXT,
                    libelle_rayon TEXT,
                    famille TEXT,
                    libelle_famille TEXT,
                    sous_famille TEXT,
                    libelle_sous_famille TEXT,
                    code_marque TEXT,
                    libelle_marque TEXT,
                    article_meti TEXT,
                    code_article TEXT,
                    libelle_article TEXT,
                    annee INTEGER,
                    semaine INTEGER,
                    qte REAL,
                    ca REAL,
                    ca_ht REAL,
                    nb_semaine INTEGER,
                    tot_qte REAL,
                    tot_ca REAL,
                    moy_qte REAL,
                    moy_ca REAL
                )
            """)
            logger.info("✅ Table créée : vente_meti")

            # Table rupture_meti
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rupture_meti (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nomenclature TEXT NOT NULL,
                    ca_ht REAL,
                    passage REAL,
                    marge REAL,
                    pm REAL NOT NULL,
                    tdm REAL,
                    poids_promo REAL,
                    generated_article TEXT,
                    generated_id TEXT
                )
            """)
            logger.info("✅ Table créée : rupture_meti")

            # Table ref_frs
            cursor.execute("""
               CREATE TABLE IF NOT EXISTS ref_frs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    departement TEXT,
                    rayon TEXT,
                    famille TEXT,
                    sous_famille TEXT,
                    code_ubs TEXT,
                    article TEXT,
                    ean TEXT,
                    libelle_article TEXT,
                    fournisseur TEXT,
                    variete TEXT,
                    prix_tarif REAL,
                    prix_de_vente REAL,
                    code_etat TEXT,
                    nom_fournisseur TEXT,
                    unite_de_mesure TEXT,
                    unite_de_vente TEXT,
                    poids_kg REAL,
                    code_taxe TEXT,
                    montant_taxe REAL,
                    code_tva TEXT,
                    pcb INTEGER,
                    ref_1 TEXT,
                    ref_2 TEXT,
                    libelle_marque TEXT,
                    libelle_complementaire TEXT,
                    date_derniere_commande TEXT,
                    principal TEXT,
                    code_classe TEXT,
                    commandable TEXT,
                    marge REAL,
                    module TEXT,
                    pcb_mini_commandable INTEGER,
                    libelle_famille TEXT,
                    taux_tva REAL,
                    libelle_departement TEXT,
                    libelle_rayon TEXT,
                    libelle_sous_famille TEXT,
                    libelle_unite_de_besoin TEXT,
                    nom_site TEXT,
                    ul TEXT,
                    svap_ttc REAL,
                    suivi_en_stock TEXT,
                    pv_conseille REAL,
                    article_meti TEXT,
                    code_prix_cession TEXT,
                    code_marketing TEXT,
                    code_marque TEXT,
                    mode_d_approvisionnement TEXT,
                    pcb_commandable TEXT
                )
            """)
            logger.info("✅ Table créée : ref_frs")

            # Table stock
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    magasin TEXT,
                    departement TEXT,
                    rayon TEXT,
                    famille TEXT,
                    sous_famille TEXT,
                    variete TEXT,
                    code_article TEXT,
                    article TEXT,
                    stock_article REAL,
                    derniere_entree TEXT,
                    type TEXT,
                    marque TEXT
                )
            """)
            logger.info("✅ Table créée : stock")

            # Table analyse_cde
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analyse_cde (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code_article TEXT,
                    libelle_article TEXT,
                    qte REAL,
                    ca REAL,
                    ca_ht REAL,
                    annee INTEGER,
                    nb_semaine INTEGER,
                    code_article_rupture TEXT,
                    fournisseur TEXT,
                    departement TEXT,
                    rayon TEXT,
                    famille TEXT,
                    sous_famille TEXT,
                    ean TEXT,
                    libelle_marque TEXT,
                    libelle_famille TEXT,
                    libelle_departement TEXT,
                    libelle_rayon TEXT,
                    libelle_sous_famille TEXT,
                    code_marque TEXT,
                    nom_fournisseur TEXT,
                    prix_tarif REAL,
                    prix_de_vente REAL,
                    code_tva TEXT,
                    pcb INTEGER,
                    date_derniere_commande TEXT,
                    commandable TEXT,
                    marge REAL,
                    module TEXT,
                    pcb_mini_commandable INTEGER,
                    taux_tva REAL,
                    libelle_unite_de_besoin TEXT,
                    svap_ttc REAL,
                    pv_conseille REAL,
                    pcb_commandable TEXT,
                    code_etat TEXT,
                    dispo_sodex INTEGER
                )
            """)
            logger.info("✅ Table créée : analyse_cde")

            conn.commit()
            logger.info("✅ Base de données initialisée avec succès.")

    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation de la base : {e}")
        raise
