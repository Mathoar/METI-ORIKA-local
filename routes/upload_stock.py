# routes/upload_stock.py
from flask import Blueprint, request, redirect, url_for, render_template
import pandas as pd
import sqlite3
import os
import logging
from services.utils_upload_stock import insert_stock_data, reset_stock_table

upload_stock_bp = Blueprint('upload_stock', __name__)
logger = logging.getLogger(__name__)
DB_NAME = "price_comparison.db"


@upload_stock_bp.route('/upload_stock', methods=['POST'])
def upload_stock():
    """Import du fichier Excel stock (.xls/.xlsx) et reset de la table stock"""
    try:
        stock_file = request.files.get('stock_file')

        if not stock_file or not stock_file.filename.lower().endswith(('.xlsx', '.xls')):
            return render_template('stock.html', error_message="Fichier invalide (attendu .xls ou .xlsx)", stock_rows=[])

        # Sauvegarde temporaire
        temp_path = 'stock_temp.xlsx'
        stock_file.save(temp_path)

        # Lecture initiale pour détecter la colonne code_article
        df_stock = pd.read_excel(temp_path)
        logger.info(f"Excel file columns: {df_stock.columns.tolist()}")

        # Détection de la colonne code_article
        code_art_col = None
        possible_names = ['CODE_ART', 'CODE_ARTICLE', 'CODEART', 'Code Art', 'Code_Art', 'ARTICLE_CODE', 'ART_CODE']
        for col in df_stock.columns:
            if col.strip().upper() in [name.upper() for name in possible_names]:
                code_art_col = col
                break

        if code_art_col is None:
            os.remove(temp_path)
            error_msg = f"Colonne 'CODE_ART' non trouvée. Colonnes disponibles : {df_stock.columns.tolist()}"
            logger.error(error_msg)
            return render_template('stock.html', error_message=error_msg, stock_rows=[])

        # Relire en forçant le dtype de code_article en texte
        df_stock = pd.read_excel(temp_path, dtype={code_art_col: str})
        logger.info(f"Sample {code_art_col} values from Excel: {df_stock[code_art_col].head(10).tolist()}")
        os.remove(temp_path)

        # Avant chaque import, reset de la table stock
        if not reset_stock_table():
            return render_template('stock.html', error_message="Erreur lors de la réinitialisation de la table stock.", stock_rows=[])

        # Insertion des données
        if not insert_stock_data(df_stock):
            return render_template('stock.html', error_message="Erreur lors de l'import du fichier stock.", stock_rows=[])

        return redirect(url_for('upload_stock.stock'))

    except Exception as e:
        logger.error(f"Erreur lors de l'import du stock : {str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return render_template('stock.html', error_message=f"Erreur lors de l'import : {str(e)}", stock_rows=[])

@upload_stock_bp.route('/stock', methods=['GET'])
def stock():
    DB_NAME = "price_comparison.db"
    error_message = None
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page

    article = request.args.get('article', '').strip()
    code_article = request.args.get('code_article', '').strip()
    departement = request.args.get('departement', '')
    rayon = request.args.get('rayon', '')
    famille = request.args.get('famille', '')
    sous_famille = request.args.get('sous_famille', '')
    derniere_entree = request.args.get('derniere_entree', '')
    types_filter = request.args.getlist('type')
    marques_filter = request.args.getlist('marque')
    magasin = request.args.get('magasin', '')
    selected_columns = request.args.getlist('colonnes') or [
        'magasin', 'departement', 'rayon', 'famille', 'sous_famille',
        'article', 'code_article', 'stock_article'
    ]

    stock_rows = []
    departements = []
    rayons = []
    familles = []
    sous_familles = []
    types = []
    marques = []
    magasins = []
    colonnes_disponibles = []
    total_pages = 1
    pages = []

    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            filters = []
            params = []

            if article:
                filters.append("article LIKE ?"); params.append(f"%{article}%")
            if code_article:
                filters.append("code_article = ?"); params.append(code_article)
            if departement:
                filters.append("departement = ?"); params.append(departement)
            if rayon:
                filters.append("rayon = ?"); params.append(rayon)
            if famille:
                filters.append("famille = ?"); params.append(famille)
            if sous_famille:
                filters.append("sous_famille = ?"); params.append(sous_famille)
            if derniere_entree:
                filters.append("DATE(derniere_entree) = ?"); params.append(derniere_entree)
            if types_filter:
                p = ','.join('?' for _ in types_filter)
                filters.append(f"type IN ({p})"); params.extend(types_filter)
            if marques_filter:
                p = ','.join('?' for _ in marques_filter)
                filters.append(f"marque IN ({p})"); params.extend(marques_filter)
            if magasin:
                filters.append("magasin = ?"); params.append(magasin)

            base_query = "FROM stock WHERE 1=1"
            if filters:
                base_query += " AND " + " AND ".join(filters)

            cursor.execute(f"SELECT COUNT(*) {base_query}", params)
            total_rows = cursor.fetchone()[0]
            total_pages = max((total_rows + per_page - 1) // per_page, 1)

            sql = f"SELECT * {base_query} ORDER BY departement, rayon, famille, sous_famille, code_article LIMIT ? OFFSET ?"
            cursor.execute(sql, params + [per_page, offset])
            rows = cursor.fetchall()

            for row in rows:
                rec = []
                for col in selected_columns:
                    val = row[col] if col in row.keys() else ''
                    if col == 'code_article':
                        val = str(int(float(str(val).strip()))) if str(val).replace('.', '').isdigit() and pd.notna(val) else str(val).strip()
                    else:
                        val = str(val) if val is not None else ''
                    rec.append(val)
                stock_rows.append(tuple(rec))

            colonnes_disponibles = [c[1] for c in cursor.execute("PRAGMA table_info(stock)")]

            def get_distinct(column):
                q = f"SELECT DISTINCT {column} FROM stock WHERE {column} IS NOT NULL"
                if filters:
                    q += " AND " + " AND ".join(filters)
                q += f" ORDER BY {column}"
                cursor.execute(q, params)
                return [r[0] for r in cursor.fetchall() if r[0]]

            departements = get_distinct('departement')
            rayons = get_distinct('rayon')
            familles = get_distinct('famille')
            sous_familles = get_distinct('sous_famille')
            types = get_distinct('type')
            marques = get_distinct('marque')
            magasins = get_distinct('magasin')

            if total_pages <= 10:
                pages = list(range(1, total_pages + 1))
            else:
                s = {1, 2, total_pages - 1, total_pages, page - 1, page, page + 1}
                pages = sorted(x for x in s if 1 <= x <= total_pages)

            sample_codes = [row['code_article'] for row in rows[:10]]
            logger.info(f"Sample code_article values displayed: {sample_codes}")

    except Exception as e:
        logger.error(f"Error in stock route: {e}")
        error_message = str(e)

    return render_template('stock.html', stock_rows=stock_rows,
                           departements=departements, rayons=rayons,
                           familles=familles, sous_familles=sous_familles,
                           types=types, marques=marques, magasins=magasins,
                           colonnes_disponibles=colonnes_disponibles,
                           selected_columns=selected_columns,
                           page=page, total_pages=total_pages,
                           pages=pages,
                           error_message=error_message)
