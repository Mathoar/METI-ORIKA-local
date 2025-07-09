# services/fournisseurs.py
import sqlite3
import logging
import os
import csv
import pandas as pd
from flask import render_template, request, flash, redirect, url_for, current_app

from services.utils_upload_fournisseurs import insert_fournisseurs_data
logger = logging.getLogger(__name__)


def get_db_path():
    return "price_comparison.db"

def get_fournisseurs_data(request):
    filters = []
    params = []

    article_filter = request.args.get('article', '').strip()
    code_article_filter = request.args.get('code_article', '').strip()
    module_filter = request.args.get('module', '').strip()
    libelle_departement_filter = request.args.get('libelle_departement', '').strip()
    libelle_rayon_filter = request.args.get('libelle_rayon', '').strip()
    code_marque_filter = request.args.get('code_marque', '').strip()
    fournisseur_filter = request.args.get('fournisseur', '').strip()
    pcb_filter = request.args.get('pcb_commandable', 'O').strip().upper()

    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page

    colonnes_standards = [
        'article', 'libelle_article','prix_tarif', 'prix_de_vente', 'marge', 'nom_fournisseur', 'libelle_marque', 'pcb_commandable','ean'
    ]

    selected_columns = request.args.getlist('colonnes') or colonnes_standards

    try:
        with sqlite3.connect(get_db_path()) as conn:
            cursor = conn.cursor()

            # Colonnes dynamiques
            cursor.execute("PRAGMA table_info(ref_frs)")
            all_columns = [row[1] for row in cursor.fetchall()]
            colonnes_optionnelles = sorted([col for col in all_columns if col not in colonnes_standards])

            base_query = f"SELECT {', '.join(selected_columns)} FROM ref_frs WHERE 1=1"
            count_query = "SELECT COUNT(*) FROM ref_frs WHERE 1=1"

            if pcb_filter in ('O', 'N'):
                filters.append(" AND TRIM(pcb_commandable) = ?")
                params.append(pcb_filter)
            if article_filter:
                filters.append(" AND libelle_article LIKE ?")
                params.append(f"%{article_filter}%")
            if code_article_filter:
                filters.append(" AND article = ?")
                params.append(code_article_filter)
            if module_filter:
                filters.append(" AND TRIM(module) = ?")
                params.append(module_filter)
            if libelle_departement_filter:
                filters.append(" AND TRIM(libelle_departement) = ?")
                params.append(libelle_departement_filter)
            if libelle_rayon_filter:
                filters.append(" AND TRIM(libelle_rayon) = ?")
                params.append(libelle_rayon_filter)
            if code_marque_filter:
                filters.append(" AND TRIM(code_marque) = ?")
                params.append(code_marque_filter)
            if fournisseur_filter:
                filters.append(" AND TRIM(nom_fournisseur) = ?")
                params.append(fournisseur_filter)

            # Pagination et données
            cursor.execute(count_query + ''.join(filters), params)
            total_rows = cursor.fetchone()[0]
            total_pages = max(1, (total_rows + per_page - 1) // per_page)

            paginated_query = base_query + ''.join(filters) + " LIMIT ? OFFSET ?"
            cursor.execute(paginated_query, params + [per_page, offset])
            ref_frs_rows = cursor.fetchall()

            def get_unique_values(column):
                dynamic_filters = list(filters)  # Clone
                dynamic_params = list(params)
                if f" AND TRIM({column}) = ?" in dynamic_filters:
                    index = dynamic_filters.index(f" AND TRIM({column}) = ?")
                    dynamic_filters.pop(index)
                    dynamic_params.pop(index)
                query = f"SELECT DISTINCT TRIM({column}) FROM ref_frs WHERE 1=1" + ''.join(dynamic_filters) + f" ORDER BY {column}"
                cursor.execute(query, dynamic_params)
                return [row[0] for row in cursor.fetchall() if row[0]]

            fournisseurs_uniques = get_unique_values("nom_fournisseur")
            codes_article = get_unique_values("article")
            modules = get_unique_values("module")
            departements = get_unique_values("libelle_departement")
            rayons = get_unique_values("libelle_rayon")
            codes_marque = get_unique_values("code_marque")

    except Exception as e:
        logger.error(f"Erreur chargement fournisseurs : {e}")
        return render_template(
            'fournisseurs.html',
            ref_frs_rows=[],
            fournisseurs_uniques=[],
            codes_article=[],
            modules=[],
            departements=[],
            rayons=[],
            codes_marque=[],
            page=1,
            total_pages=1,
            colonnes_standards=colonnes_standards,
            colonnes_optionnelles=[],
            selected_columns=colonnes_standards
        )

    return render_template(
        'fournisseurs.html',
        ref_frs_rows=ref_frs_rows,
        fournisseurs_uniques=fournisseurs_uniques,
        codes_article=codes_article,
        modules=modules,
        departements=departements,
        rayons=rayons,
        codes_marque=codes_marque,
        page=page,
        total_pages=total_pages,
        colonnes_standards=colonnes_standards,
        colonnes_optionnelles=colonnes_optionnelles,
        selected_columns=selected_columns
    )


def auto_import_ref_frs():
    file_path = '/Users/mhoar/Desktop/python_vscode/METI ORIKA/source/extr_arti_frs.csv'
    fallback_paths = [
        '/Users/mhoar/Desktop/python_vscode/METI ORIKA/EXTR_ARTI_FRS.csv',
        '/Users/mhoar/Desktop/EXTR_ARTI_FRS.csv'
    ]

    try:
        selected_path = None
        if os.path.exists(file_path) and os.access(file_path, os.R_OK):
            selected_path = file_path
            logger.info(f"Found file at primary path: {file_path}")
        else:
            for path in fallback_paths:
                if os.path.exists(path) and os.access(path, os.R_OK):
                    selected_path = path
                    logger.info(f"Found file at fallback path: {path}")
                    break

        if not selected_path:
            logger.warning("File not found in any configured paths.")
            return False

        logger.info(f"Importation à partir de : {selected_path}")
        insert_fournisseurs_data(selected_path, get_db_path())

        with sqlite3.connect(get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ref_frs")
            count = cursor.fetchone()[0]
            logger.info(f"Nombre de lignes insérées dans ref_frs : {count}")

        return True

    except Exception as e:
        logger.error(f"Erreur lors de l'import automatique : {e}")
        return False
