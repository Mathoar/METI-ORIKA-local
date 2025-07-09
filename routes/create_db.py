# routes/create_db.py
from flask import Blueprint, jsonify
from services.fournisseur_service import create_fournisseur_actif_table
from services.utils import get_db_path

create_db_bp = Blueprint('create_db', __name__)

@create_db_bp.route('/create_frs_db')
def create_frs_db():
    db_path = get_db_path()
    create_fournisseur_actif_table(db_path)
    return jsonify({"message": "La base de données Fournisseur_actif a été créée avec succès."})
