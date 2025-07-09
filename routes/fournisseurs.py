# routes/fournisseurs.py

from flask import Blueprint, request, redirect, url_for, flash
from services.fournisseurs import get_fournisseurs_data, auto_import_ref_frs
from services.utils_upload_fournisseurs import insert_fournisseurs_data
import logging
import os

fournisseurs_bp = Blueprint('fournisseurs', __name__)
logger = logging.getLogger(__name__)
DB_NAME = "/Users/mhoar/Desktop/python_vscode/price_comparison.db"

@fournisseurs_bp.route('/fournisseurs')
def fournisseurs():
    return get_fournisseurs_data(request)

@fournisseurs_bp.route('/rafraichir', methods=['POST'])
def rafraichir_fournisseurs():
    success = auto_import_ref_frs()
    if success:
        flash("Importation automatique des fournisseurs réussie.", "success")
    else:
        flash("Échec de l'importation automatique des fournisseurs.", "danger")
    return redirect(url_for('fournisseurs.fournisseurs'))

@fournisseurs_bp.route('/upload_fournisseurs', methods=['POST'])
def upload_fournisseurs():
    file = request.files.get('file')
    if not file or not file.filename.endswith('.csv'):
        flash("Veuillez sélectionner un fichier .csv valide.", "danger")
        return redirect(url_for('fournisseurs.fournisseurs'))

    try:
        upload_path = os.path.join('/tmp', file.filename)
        file.save(upload_path)
        insert_fournisseurs_data(upload_path, DB_NAME)
        flash("Fichier fournisseurs importé avec succès.", "success")
    except Exception as e:
        logger.exception("Erreur lors de l'import des fournisseurs :")
        flash(f"Erreur lors de l'import : {e}", "danger")

    return redirect(url_for('fournisseurs.fournisseurs'))
