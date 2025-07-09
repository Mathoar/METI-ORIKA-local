import os
import sqlite3
import logging

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
                    moy_ca REAL,
                    prix_tarif REAL,
                    prix_de_vente REAL,
                    code_tva TEXT,
                    fournisseur TEXT,
                    nom_fournisseur TEXT,
                    pcb INTEGER,
                    date_derniere_commande TEXT,
                    commandable TEXT,
                    marge REAL,
                    pcb_mini_commandable INTEGER,
                    taux_tva REAL,
                    pv_conseille REAL,
                    pcb_commandable TEXT
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

            # ============ NOUVELLES TABLES POUR COMMANDE_VENTE ============

            # Table stock_actuel
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_actuel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code_article TEXT NOT NULL,
                    libelle_article TEXT,
                    stock_actuel REAL DEFAULT 0,
                    stock_reserve REAL DEFAULT 0,
                    prix_achat REAL DEFAULT 0,
                    fournisseur_principal TEXT,
                    delai_livraison INTEGER DEFAULT 7,
                    quantite_min_commande REAL DEFAULT 0,
                    date_maj TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(code_article)
                )
            """)
            logger.info("✅ Table créée : stock_actuel")

            # Table commandes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commandes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_validation TIMESTAMP,
                    date_envoi TIMESTAMP,
                    date_reception TIMESTAMP,
                    statut TEXT DEFAULT 'En attente',
                    type_commande TEXT DEFAULT 'Suggestion',
                    total_articles INTEGER DEFAULT 0,
                    total_quantite INTEGER DEFAULT 0,
                    total_montant REAL DEFAULT 0,
                    parametres TEXT,
                    utilisateur TEXT,
                    commentaire TEXT,
                    annee INTEGER,
                    semaine_debut INTEGER,
                    semaine_fin INTEGER
                )
            """)
            logger.info("✅ Table créée : commandes")

            # Table commandes_details
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commandes_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    commande_id INTEGER NOT NULL,
                    article_code TEXT NOT NULL,
                    article_libelle TEXT,
                    departement TEXT,
                    rayon TEXT,
                    famille TEXT,
                    sous_famille TEXT,
                    quantite_commandee INTEGER NOT NULL,
                    quantite_suggeree INTEGER,
                    quantite_recue INTEGER,
                    prix_unitaire REAL DEFAULT 0,
                    niveau_selection TEXT,
                    vente_moyenne REAL,
                    stock_au_moment REAL,
                    couverture_au_moment REAL,
                    tendance REAL,
                    commentaire TEXT,
                    FOREIGN KEY (commande_id) REFERENCES commandes(id)
                )
            """)
            logger.info("✅ Table créée : commandes_details")

            # Table parametres_commande
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parametres_commande (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom_parametre TEXT UNIQUE NOT NULL,
                    valeur TEXT NOT NULL,
                    type_parametre TEXT DEFAULT 'TEXT',
                    description TEXT,
                    modifiable BOOLEAN DEFAULT 1,
                    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("✅ Table créée : parametres_commande")

            # Table mouvements_stock
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mouvements_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_mouvement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    type_mouvement TEXT,
                    code_article TEXT NOT NULL,
                    quantite REAL NOT NULL,
                    stock_avant REAL,
                    stock_apres REAL,
                    commande_id INTEGER,
                    commentaire TEXT,
                    utilisateur TEXT,
                    FOREIGN KEY (commande_id) REFERENCES commandes(id)
                )
            """)
            logger.info("✅ Table créée : mouvements_stock")

            # Insérer les paramètres par défaut pour commande_vente
            parametres_defaut = [
                ('couverture_cible', '21', 'INTEGER', 'Nombre de jours de couverture cible'),
                ('coefficient_securite', '1.2', 'REAL', 'Coefficient de sécurité pour les commandes'),
                ('seuil_rupture', '0', 'INTEGER', 'Stock en dessous duquel on considère une rupture'),
                ('seuil_alerte', '7', 'INTEGER', 'Jours de couverture en dessous desquels on alerte'),
                ('methode_calcul_defaut', 'moyenne', 'TEXT', 'Méthode de calcul par défaut'),
                ('delai_livraison_defaut', '7', 'INTEGER', 'Délai de livraison par défaut en jours'),
            ]
            
            for param in parametres_defaut:
                cursor.execute("""
                    INSERT OR IGNORE INTO parametres_commande 
                    (nom_parametre, valeur, type_parametre, description) 
                    VALUES (?, ?, ?, ?)
                """, param)
            logger.info("✅ Paramètres par défaut insérés")

            # Créer les index pour améliorer les performances
            index_queries = [
                "CREATE INDEX IF NOT EXISTS idx_vente_meti_article ON vente_meti(code_article)",
                "CREATE INDEX IF NOT EXISTS idx_vente_meti_annee_semaine ON vente_meti(annee, semaine)",
                "CREATE INDEX IF NOT EXISTS idx_stock_article ON stock(code_article)",
                "CREATE INDEX IF NOT EXISTS idx_ref_frs_article ON ref_frs(article)",
                "CREATE INDEX IF NOT EXISTS idx_analyse_cde_article ON analyse_cde(code_article)",
                "CREATE INDEX IF NOT EXISTS idx_commandes_statut ON commandes(statut)",
                "CREATE INDEX IF NOT EXISTS idx_commandes_date ON commandes(date_creation)",
                "CREATE INDEX IF NOT EXISTS idx_commandes_details_commande ON commandes_details(commande_id)",
                "CREATE INDEX IF NOT EXISTS idx_commandes_details_article ON commandes_details(article_code)",
                "CREATE INDEX IF NOT EXISTS idx_stock_actuel_article ON stock_actuel(code_article)",
                "CREATE INDEX IF NOT EXISTS idx_mouvements_article ON mouvements_stock(code_article)",
                "CREATE INDEX IF NOT EXISTS idx_mouvements_date ON mouvements_stock(date_mouvement)"
            ]
            
            for query in index_queries:
                cursor.execute(query)
            logger.info("✅ Index créés")

            # Créer les vues utiles
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS v_commandes_en_cours AS
                SELECT 
                    c.id,
                    c.date_creation,
                    c.statut,
                    c.total_articles,
                    c.total_quantite,
                    c.total_montant,
                    c.utilisateur,
                    COUNT(cd.id) as nb_lignes
                FROM commandes c
                LEFT JOIN commandes_details cd ON c.id = cd.commande_id
                WHERE c.statut IN ('En attente', 'Validée', 'Envoyée')
                GROUP BY c.id
            """)
            logger.info("✅ Vue créée : v_commandes_en_cours")

            conn.commit()
            logger.info("✅ Base de données initialisée avec succès.")

    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation de la base : {e}")
        raise

def populate_stock_actuel_from_stock():
    """
    Peuple la table stock_actuel à partir de la table stock existante
    """
    path = get_db_path()
    
    try:
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()
            
            # Copier les données de stock vers stock_actuel
            cursor.execute("""
                INSERT OR REPLACE INTO stock_actuel (code_article, libelle_article, stock_actuel)
                SELECT 
                    code_article,
                    article as libelle_article,
                    COALESCE(stock_article, 0) as stock_actuel
                FROM stock
                WHERE code_article IS NOT NULL
                AND code_article != ''
            """)
            
            rows_affected = cursor.rowcount
            conn.commit()
            logger.info(f"✅ {rows_affected} articles copiés dans stock_actuel")
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du peuplement de stock_actuel : {e}")
        raise

# Section pour exécution directe
if __name__ == "__main__":
    # Configuration du logging pour l'exécution directe
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Initialisation de la base de données...")
    
    try:
        init_db()
        print("\n✅ Base de données initialisée avec succès!")
        
        # Optionnel : migrer les données de stock
        response = input("\n📦 Voulez-vous migrer les données de la table 'stock' vers 'stock_actuel'? (o/n): ")
        if response.lower() == 'o':
            populate_stock_actuel_from_stock()
            print("✅ Migration terminée!")
            
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()