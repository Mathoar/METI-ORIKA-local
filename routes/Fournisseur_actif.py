# routes/Fournisseur_actif.py
from flask import Blueprint, jsonify, render_template, request
from services.fournisseur_service import create_fournisseur_actif_table,get_article_statistics,get_articles_with_multiple_suppliers

from services.utils import get_db_path


fournisseur_actif_bp = Blueprint('fournisseur_actif', __name__)

@fournisseur_actif_bp.route('/create_frs_db', methods=['POST'])
def create_frs_db():
    try:
        db_path = get_db_path()
        table_data = create_fournisseur_actif_table(db_path)
        return jsonify({
            "success": True,
            "message": "La base de données Fournisseur_actif a été créée avec succès.",
            "data": table_data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Une erreur est survenue lors de la création de la base de données: {str(e)}"
        }), 500

@fournisseur_actif_bp.route('/page')
def fournisseur_actif_page():
    return render_template('Fournisseur_actif.html')

@fournisseur_actif_bp.route('/article_stats', methods=['GET'])
def article_stats():
    try:
        db_path = get_db_path()
        stats = get_article_statistics(db_path)
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Une erreur est survenue lors de la récupération des statistiques: {str(e)}"
        }), 500

@fournisseur_actif_bp.route('/articles_with_multiple_suppliers', methods=['GET'], endpoint='articles_with_multiple_suppliers_1')
def articles_with_multiple_suppliers():
    try:
        db_path = get_db_path()
        articles = get_articles_with_multiple_suppliers(db_path)
        return jsonify({
            "success": True,
            "data": articles
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Une erreur est survenue lors de la récupération des articles avec plusieurs fournisseurs: {str(e)}"
        }), 500


@fournisseur_actif_bp.route('/articles_with_multiple_suppliers', methods=['GET'])
def articles_with_multiple_suppliers():
    try:
        db_path = get_db_path()
        articles = get_articles_with_multiple_suppliers(db_path)
        return jsonify({"success": True, "data": articles})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500