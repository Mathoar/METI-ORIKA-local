import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import io

DB_PATH = "/Users/mhoar/Desktop/python_vscode/price_comparison.db"

def get_suggestions_commande(annee, semaine_debut, semaine_fin, niveau, methode, coverage=21, safety=1.2, filtres=None):
    """
    Génère des suggestions de commande basées sur l'analyse des ventes
    """
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Configuration des champs selon le niveau
        niveau_config = {
            'departement': ('departement', 'libelle_departement'),
            'rayon': ('rayon', 'libelle_rayon'),
            'famille': ('famille', 'libelle_famille'),
            'sous_famille': ('libelle_sous_famille', 'libelle_sous_famille'),
            'code_article': ('code_article', 'libelle_article'),
            'fournisseur': ('nom_fournisseur', 'nom_fournisseur')
        }
        
        group_by, label_field = niveau_config.get(niveau, ('departement', 'libelle_departement'))
        
        # Requête simplifiée pour SQLite
        # Si group_by et label_field sont identiques, ne sélectionner qu'une fois
        if group_by == label_field:
            query_ventes = f"""
                SELECT 
                    {group_by},
                    semaine,
                    SUM(ca) as ca,
                    SUM(qte) as qte,
                    AVG(prix_tarif) as prix_tarif_moyen,
                    AVG(prix_de_vente) as prix_vente_moyen,
                    MIN(pcb) as pcb_min,
                    MAX(pcb) as pcb_max,
                    MIN(pcb_mini_commandable) as pcb_mini,
                    AVG(marge) as marge_moyenne,
                    COUNT(DISTINCT code_article) as nb_articles
                FROM vente_meti
                WHERE annee = ?
                  AND semaine BETWEEN ? AND ?
            """
        else:
            query_ventes = f"""
                SELECT 
                    {group_by},
                    {label_field},
                    semaine,
                    SUM(ca) as ca,
                    SUM(qte) as qte,
                    AVG(prix_tarif) as prix_tarif_moyen,
                    AVG(prix_de_vente) as prix_vente_moyen,
                    MIN(pcb) as pcb_min,
                    MAX(pcb) as pcb_max,
                    MIN(pcb_mini_commandable) as pcb_mini,
                    AVG(marge) as marge_moyenne,
                    COUNT(DISTINCT code_article) as nb_articles
                FROM vente_meti
                WHERE annee = ?
                  AND semaine BETWEEN ? AND ?
            """
        
        # Ajouter le filtre sur commandable si on a l'info
        query_ventes += " AND (commandable = 'O' OR commandable IS NULL)"
        
        params = [annee, semaine_debut, semaine_fin]
        
        # Ajouter les filtres
        if filtres:
            for k, v in filtres.items():
                query_ventes += f" AND {k} = ?"
                params.append(v)
        
        if group_by == label_field:
            query_ventes += f" GROUP BY {group_by}, semaine"
        else:
            query_ventes += f" GROUP BY {group_by}, {label_field}, semaine"
        
        print(f"Query: {query_ventes}")  # Debug
        print(f"Params: {params}")  # Debug
        
        # Exécuter la requête
        df_ventes = pd.read_sql_query(query_ventes, conn, params=params)
        
        print(f"Nombre de lignes récupérées: {len(df_ventes)}")  # Debug
        
        if df_ventes.empty:
            print("Aucune donnée trouvée")
            return []
        
        # Requête pour récupérer les infos fournisseur (séparément)
        if group_by == label_field:
            query_fournisseurs = f"""
                SELECT DISTINCT
                    {group_by},
                    GROUP_CONCAT(DISTINCT nom_fournisseur) as fournisseurs_list
                FROM vente_meti
                WHERE annee = ?
                  AND semaine BETWEEN ? AND ?
            """
        else:
            query_fournisseurs = f"""
                SELECT DISTINCT
                    {group_by},
                    GROUP_CONCAT(DISTINCT nom_fournisseur) as fournisseurs_list
                FROM vente_meti
                WHERE annee = ?
                  AND semaine BETWEEN ? AND ?
            """
        
        if filtres:
            for k, v in filtres.items():
                query_fournisseurs += f" AND {k} = ?"
        
        query_fournisseurs += f" GROUP BY {group_by}"
        
        df_fournisseurs = pd.read_sql_query(query_fournisseurs, conn, params=params)
        
        # Requête pour le stock actuel
        df_stock = pd.DataFrame()
        if niveau == 'code_article':
            query_stock = """
                SELECT 
                    code_article,
                    stock_actuel,
                    prix_achat
                FROM stock_actuel
            """
            df_stock = pd.read_sql_query(query_stock, conn)
        
        # Calculer les suggestions
        suggestions = []
        
        # Grouper par article/niveau
        # Si group_by et label_field sont identiques, ne grouper que par un seul
        if group_by == label_field:
            grouped = df_ventes.groupby([group_by])
        else:
            grouped = df_ventes.groupby([group_by, label_field])
        
        for group_key, group_data in grouped:
            # Gérer le cas où on a un seul niveau de groupement
            if group_by == label_field:
                code = group_key
                libelle = group_key
            else:
                code, libelle = group_key
            # Calculer les métriques de vente
            ventes_semaine = group_data.groupby('semaine')['qte'].sum()
            nb_semaines = len(ventes_semaine)
            
            if nb_semaines == 0:
                continue
            
            # Calcul selon la méthode
            if methode == 'moyenne':
                vente_moyenne_hebdo = ventes_semaine.mean()
            elif methode == 'tendance':
                if nb_semaines > 1:
                    x = np.arange(nb_semaines)
                    y = ventes_semaine.values
                    z = np.polyfit(x, y, 1)
                    vente_moyenne_hebdo = z[0] * nb_semaines + z[1]
                    vente_moyenne_hebdo = max(0, vente_moyenne_hebdo)
                else:
                    vente_moyenne_hebdo = ventes_semaine.mean()
            elif methode == 'pic':
                vente_moyenne_hebdo = ventes_semaine.max()
            else:
                vente_moyenne_hebdo = ventes_semaine.mean()
            
            # Conversion en vente journalière
            vente_moyenne_jour = vente_moyenne_hebdo / 7
            
            # Récupérer les informations agrégées depuis les données moyennes
            prix_tarif = float(group_data['prix_tarif_moyen'].mean()) if pd.notna(group_data['prix_tarif_moyen'].mean()) else 0
            prix_vente = float(group_data['prix_vente_moyen'].mean()) if pd.notna(group_data['prix_vente_moyen'].mean()) else 0
            pcb = int(group_data['pcb_min'].min()) if pd.notna(group_data['pcb_min'].min()) and group_data['pcb_min'].min() > 0 else 1
            pcb_mini = int(group_data['pcb_mini'].min()) if pd.notna(group_data['pcb_mini'].min()) and group_data['pcb_mini'].min() > 0 else pcb
            marge = float(group_data['marge_moyenne'].mean()) if pd.notna(group_data['marge_moyenne'].mean()) else 0
            nb_articles = int(group_data['nb_articles'].mean()) if pd.notna(group_data['nb_articles'].mean()) else 1
            
            # Récupérer les fournisseurs
            fournisseurs = ''
            if not df_fournisseurs.empty:
                frs_row = df_fournisseurs[df_fournisseurs[group_by] == code]
                if not frs_row.empty:
                    fournisseurs = frs_row['fournisseurs_list'].values[0] or ''
            
            # Stock actuel
            stock_actuel = 0
            if niveau == 'code_article' and not df_stock.empty:
                stock_row = df_stock[df_stock['code_article'] == code]
                if not stock_row.empty:
                    stock_actuel = float(stock_row['stock_actuel'].values[0]) if pd.notna(stock_row['stock_actuel'].values[0]) else 0
            
            # Calcul de la couverture actuelle
            if vente_moyenne_jour > 0:
                couverture_actuelle = stock_actuel / vente_moyenne_jour
            else:
                couverture_actuelle = 999 if stock_actuel > 0 else 0
            
            # Calcul de la quantité suggérée
            besoin_theorique = vente_moyenne_jour * coverage * safety
            quantite_suggeree = max(0, besoin_theorique - stock_actuel)
            
            # Arrondir au PCB supérieur
            quantite_suggeree_pcb = quantite_suggeree
            if pcb > 1 and quantite_suggeree > 0:
                quantite_suggeree_pcb = np.ceil(quantite_suggeree / pcb) * pcb
            
            # Vérifier le PCB minimum
            if quantite_suggeree_pcb > 0 and quantite_suggeree_pcb < pcb_mini:
                quantite_suggeree_pcb = pcb_mini
            
            # Calcul de la tendance
            tendance = 0
            if nb_semaines >= 2:
                debut = ventes_par_semaine.iloc[:nb_semaines//2].mean()
                fin = ventes_par_semaine.iloc[nb_semaines//2:].mean()
                if debut > 0:
                    tendance = ((fin - debut) / debut) * 100
            
            # Déterminer les alertes
            rupture = stock_actuel == 0 and vente_moyenne_jour > 0
            stock_faible = couverture_actuelle < 7 and not rupture
            recommande = (tendance > 10) or rupture or stock_faible
            
            # CA moyen et montant estimé
            ca_moyen = group_data['ca'].sum() / nb_semaines
            montant_estime = quantite_suggeree_pcb * prix_tarif
            
            suggestions.append({
                'id': str(abs(hash(f"{code}_{libelle}"))),
                'code': str(code),
                'libelle': str(libelle),
                'vente_moyenne': round(vente_moyenne_hebdo, 0),
                'stock_actuel': round(stock_actuel, 0),
                'couverture': round(couverture_actuelle, 0),
                'quantite_suggeree': round(quantite_suggeree, 0),
                'quantite_suggeree_pcb': round(quantite_suggeree_pcb, 0),
                'pcb': pcb,
                'pcb_mini': pcb_mini,
                'tendance': round(tendance, 1),
                'ca_moyen': ca_moyen,
                'prix_tarif': prix_tarif,
                'prix_vente': prix_vente,
                'marge': round(marge, 1),
                'montant_estime': montant_estime,
                'fournisseurs': fournisseurs,
                'nb_articles': nb_articles if niveau != 'code_article' else 1,
                'rupture': rupture,
                'stock_faible': stock_faible,
                'recommande': recommande,
                'selected': recommande
            })
        
        # Trier par montant estimé décroissant
        suggestions.sort(key=lambda x: x['montant_estime'], reverse=True)
        
        print(f"Nombre de suggestions: {len(suggestions)}")  # Debug
        
        return suggestions
        
    except Exception as e:
        print(f"Erreur dans get_suggestions_commande: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        conn.close()

def calculer_statistiques_globales(suggestions):
    """
    Calcule les statistiques globales pour le tableau de bord
    """
    if not suggestions:
        return {
            'total_prevision': 0,
            'articles_rupture': 0,
            'couverture_moyenne': 0
        }
    
    # Total prévisionnel (basé sur le CA moyen)
    total_prevision = sum(s['ca_moyen'] for s in suggestions if s['selected'])
    
    # Articles en rupture
    articles_rupture = sum(1 for s in suggestions if s['rupture'])
    
    # Couverture moyenne (exclure les valeurs extrêmes)
    couvertures = [s['couverture'] for s in suggestions if s['couverture'] < 100]
    if couvertures:
        couverture_moyenne = round(sum(couvertures) / len(couvertures), 0)
    else:
        couverture_moyenne = 0
    
    return {
        'total_prevision': total_prevision,
        'articles_rupture': articles_rupture,
        'couverture_moyenne': couverture_moyenne
    }

def valider_commande_service(items, parameters):
    """
    Valide et enregistre une commande dans la base de données
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Créer la table des commandes si elle n'existe pas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commandes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                statut TEXT DEFAULT 'En attente',
                total_articles INTEGER,
                total_quantite INTEGER,
                parametres TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commandes_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                commande_id INTEGER,
                article_code TEXT,
                article_libelle TEXT,
                quantite INTEGER,
                FOREIGN KEY (commande_id) REFERENCES commandes(id)
            )
        """)
        
        # Enregistrer la commande
        cursor.execute("""
            INSERT INTO commandes (total_articles, total_quantite, parametres)
            VALUES (?, ?, ?)
        """, (
            len(items),
            sum(int(item['quantity']) for item in items),
            str(parameters)
        ))
        
        commande_id = cursor.lastrowid
        
        # Enregistrer les détails
        for item in items:
            cursor.execute("""
                INSERT INTO commandes_details (commande_id, article_code, quantite)
                VALUES (?, ?, ?)
            """, (commande_id, item['id'], item['quantity']))
        
        conn.commit()
        
        return {'commande_id': commande_id}
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def exporter_commande_excel(item_ids, annee, semaine_debut, semaine_fin, niveau):
    """
    Exporte une commande au format Excel en utilisant pandas
    """
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Créer un DataFrame avec les données de commande
        data = []
        
        for idx, item_id in enumerate(item_ids):
            # Simuler les données (à adapter selon votre structure réelle)
            data.append({
                'Code': f'ART{idx+1}',
                'Libellé': f'Article {idx+1}',
                'Quantité suggérée': 100,
                'Stock actuel': 50,
                'Couverture (j)': 7,
                'Tendance': '+5%',
                'Quantité à commander': 100
            })
        
        # Créer le DataFrame
        df = pd.DataFrame(data)
        
        # Créer un buffer en mémoire
        output = io.BytesIO()
        
        # Écrire le DataFrame dans Excel avec mise en forme
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Commande', index=False)
            
            # Obtenir la feuille de calcul
            worksheet = writer.sheets['Commande']
            
            # Appliquer une mise en forme basique
            # Ajuster la largeur des colonnes
            worksheet.column_dimensions['A'].width = 15
            worksheet.column_dimensions['B'].width = 40
            worksheet.column_dimensions['C'].width = 20
            worksheet.column_dimensions['D'].width = 15
            worksheet.column_dimensions['E'].width = 15
            worksheet.column_dimensions['F'].width = 12
            worksheet.column_dimensions['G'].width = 20
            
            # Mettre en forme l'en-tête
            for cell in worksheet[1]:
                cell.font = cell.font.copy(bold=True)
                cell.fill = cell.fill.copy(fgColor="4472C4")
        
        # Réinitialiser la position du buffer
        output.seek(0)
        
        return output.getvalue()
        
    except Exception as e:
        print(f"Erreur export Excel: {e}")
        raise e
    finally:
        conn.close()

def get_historique_commandes(limit=50):
    """
    Récupère l'historique des commandes
    """
    conn = sqlite3.connect(DB_PATH)
    
    try:
        query = """
            SELECT 
                id,
                date_creation,
                statut,
                total_articles,
                total_quantite,
                parametres
            FROM commandes
            ORDER BY date_creation DESC
            LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=[limit])
        
        # Convertir en liste de dictionnaires
        commandes = df.to_dict('records')
        
        # Formater les dates
        for commande in commandes:
            if commande['date_creation']:
                commande['date_creation'] = pd.to_datetime(commande['date_creation']).strftime('%d/%m/%Y %H:%M')
        
        return commandes
        
    except Exception as e:
        print(f"Erreur get_historique_commandes: {e}")
        return []
    finally:
        conn.close()

def get_details_commande(commande_id):
    """
    Récupère les détails d'une commande spécifique
    """
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Récupérer les infos de la commande
        query_commande = """
            SELECT 
                id,
                date_creation,
                statut,
                total_articles,
                total_quantite,
                parametres
            FROM commandes
            WHERE id = ?
        """
        
        commande = pd.read_sql_query(query_commande, conn, params=[commande_id]).to_dict('records')
        
        if not commande:
            return None
            
        commande = commande[0]
        
        # Récupérer les détails
        query_details = """
            SELECT 
                article_code,
                article_libelle,
                quantite
            FROM commandes_details
            WHERE commande_id = ?
            ORDER BY quantite DESC
        """
        
        details = pd.read_sql_query(query_details, conn, params=[commande_id]).to_dict('records')
        
        commande['details'] = details
        
        # Formater la date
        if commande['date_creation']:
            commande['date_creation'] = pd.to_datetime(commande['date_creation']).strftime('%d/%m/%Y %H:%M')
        
        return commande
        
    except Exception as e:
        print(f"Erreur get_details_commande: {e}")
        return None
    finally:
        conn.close()

def update_stock_article(article_code, article_libelle, stock_actuel):
    """
    Met à jour le stock d'un article
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Vérifier si l'article existe
        cursor.execute("""
            SELECT stock_actuel FROM stock_actuel WHERE code_article = ?
        """, (article_code,))
        
        old_stock = cursor.fetchone()
        
        if old_stock:
            # Mettre à jour le stock existant
            cursor.execute("""
                UPDATE stock_actuel 
                SET stock_actuel = ?, date_maj = CURRENT_TIMESTAMP
                WHERE code_article = ?
            """, (stock_actuel, article_code))
            
            # Enregistrer le mouvement
            cursor.execute("""
                INSERT INTO mouvements_stock 
                (type_mouvement, code_article, quantite, stock_avant, stock_apres, commentaire)
                VALUES ('AJUSTEMENT', ?, ?, ?, ?, 'Mise à jour manuelle depuis commande')
            """, (article_code, stock_actuel - old_stock[0], old_stock[0], stock_actuel))
        else:
            # Créer un nouvel enregistrement
            cursor.execute("""
                INSERT INTO stock_actuel 
                (code_article, libelle_article, stock_actuel, date_maj)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (article_code, article_libelle, stock_actuel))
            
            # Enregistrer le mouvement
            cursor.execute("""
                INSERT INTO mouvements_stock 
                (type_mouvement, code_article, quantite, stock_avant, stock_apres, commentaire)
                VALUES ('AJUSTEMENT', ?, ?, 0, ?, 'Création depuis commande')
            """, (article_code, stock_actuel, stock_actuel))
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Erreur update_stock_article: {e}")
        raise e
    finally:
        conn.close()

def update_stocks_batch(stocks):
    """
    Met à jour plusieurs stocks en une seule transaction
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updated = []
    
    try:
        for stock_data in stocks:
            article_code = stock_data.get('article_code')
            article_libelle = stock_data.get('article_libelle')
            stock_actuel = float(stock_data.get('stock_actuel', 0))
            
            # Vérifier le stock actuel
            cursor.execute("""
                SELECT stock_actuel FROM stock_actuel WHERE code_article = ?
            """, (article_code,))
            
            old_stock = cursor.fetchone()
            
            if old_stock:
                # Mettre à jour
                cursor.execute("""
                    UPDATE stock_actuel 
                    SET stock_actuel = ?, date_maj = CURRENT_TIMESTAMP
                    WHERE code_article = ?
                """, (stock_actuel, article_code))
                
                # Mouvement
                cursor.execute("""
                    INSERT INTO mouvements_stock 
                    (type_mouvement, code_article, quantite, stock_avant, stock_apres, commentaire)
                    VALUES ('AJUSTEMENT', ?, ?, ?, ?, 'Mise à jour batch depuis commande')
                """, (article_code, stock_actuel - old_stock[0], old_stock[0], stock_actuel))
            else:
                # Créer
                cursor.execute("""
                    INSERT INTO stock_actuel 
                    (code_article, libelle_article, stock_actuel, date_maj)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (article_code, article_libelle, stock_actuel))
                
                # Mouvement
                cursor.execute("""
                    INSERT INTO mouvements_stock 
                    (type_mouvement, code_article, quantite, stock_avant, stock_apres, commentaire)
                    VALUES ('AJUSTEMENT', ?, ?, 0, ?, 'Création batch depuis commande')
                """, (article_code, stock_actuel, stock_actuel))
            
            updated.append(article_code)
        
        conn.commit()
        return updated
        
    except Exception as e:
        conn.rollback()
        print(f"Erreur update_stocks_batch: {e}")
        raise e
    finally:
        conn.close()