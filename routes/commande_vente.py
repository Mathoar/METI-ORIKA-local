from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for
from services.commande_vente import (
    get_suggestions_commande, 
    calculer_statistiques_globales,
    valider_commande_service,
    exporter_commande_excel
)
import json
import io

commande_vente_bp = Blueprint('commande_vente', __name__, url_prefix='/commande_vente')

@commande_vente_bp.route('/')
def commande_vente():
    # Paramètres de filtrage
    annee = int(request.args.get('annee', 2025))
    semaine_debut = int(request.args.get('semaine_debut', 1))
    semaine_fin = int(request.args.get('semaine_fin', 52))
    niveau = request.args.get('niveau', 'departement')
    methode = request.args.get('methode', 'moyenne')
    
    # Paramètres de calcul
    coverage = int(request.args.get('coverage', 21))  # Couverture cible en jours
    safety = float(request.args.get('safety', 1.2))  # Coefficient de sécurité
    
    # Filtres hiérarchiques
    parent_filter = request.args.get('parent_filter')
    parent_filters = []
    
    # Construction des filtres selon le niveau
    filtres = {}
    if parent_filter:
        if niveau == 'rayon':
            filtres['libelle_departement'] = parent_filter
            parent_filters.append(('Département', parent_filter))
        elif niveau == 'famille':
            filtres['libelle_rayon'] = parent_filter
            parent_filters.append(('Rayon', parent_filter))
        elif niveau == 'sous_famille':
            filtres['libelle_famille'] = parent_filter
            parent_filters.append(('Famille', parent_filter))
        elif niveau == 'code_article':
            filtres['libelle_sous_famille'] = parent_filter
            parent_filters.append(('Sous-famille', parent_filter))
    
    # Déterminer le prochain niveau
    next_niveau_map = {
        'departement': 'rayon',
        'rayon': 'famille',
        'famille': 'sous_famille',
        'sous_famille': 'code_article',
        'code_article': None
    }
    next_niveau = next_niveau_map.get(niveau)
    
    try:
        # Récupérer les suggestions
        suggestions = get_suggestions_commande(
            annee, semaine_debut, semaine_fin, 
            niveau, methode, coverage, safety, filtres
        )
        
        # Calculer les statistiques globales
        stats = calculer_statistiques_globales(suggestions)
        
        return render_template(
            "commande_vente.html",
            suggestions=suggestions,
            selected_annee=annee,
            semaine_debut=semaine_debut,
            semaine_fin=semaine_fin,
            niveau=niveau,
            methode=methode,
            next_niveau=next_niveau,
            parent_filters=parent_filters,
            total_prevision=stats['total_prevision'],
            articles_rupture=stats['articles_rupture'],
            couverture_stock=stats['couverture_moyenne']
        )
        
    except Exception as e:
        print(f"Erreur dans commande_vente: {e}")
        import traceback
        traceback.print_exc()
        return render_template(
            "commande_vente.html",
            suggestions=[],
            selected_annee=annee,
            semaine_debut=semaine_debut,
            semaine_fin=semaine_fin,
            niveau=niveau,
            methode=methode,
            next_niveau=next_niveau,
            parent_filters=parent_filters,
            total_prevision=0,
            articles_rupture=0,
            couverture_stock=0,
            error=str(e)
        )

@commande_vente_bp.route('/valider', methods=['POST'])
def valider_commande():
    """Valide et enregistre une commande"""
    try:
        data = request.get_json()
        items = data.get('items', [])
        parameters = data.get('parameters', {})
        
        # Valider la commande
        result = valider_commande_service(items, parameters)
        
        return jsonify({
            'success': True,
            'message': 'Commande validée avec succès',
            'commande_id': result['commande_id']
        })
        
    except Exception as e:
        print(f"Erreur validation commande: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@commande_vente_bp.route('/export')
def export_commande():
    """Exporte la commande au format Excel"""
    try:
        # Récupérer les IDs des articles sélectionnés
        items_str = request.args.get('items', '')
        if not items_str:
            return "Aucun article sélectionné", 400
            
        item_ids = items_str.split(',')
        
        # Récupérer les paramètres actuels
        annee = int(request.args.get('annee', 2025))
        semaine_debut = int(request.args.get('semaine_debut', 1))
        semaine_fin = int(request.args.get('semaine_fin', 52))
        niveau = request.args.get('niveau', 'departement')
        
        # Générer le fichier Excel
        excel_buffer = exporter_commande_excel(
            item_ids, annee, semaine_debut, semaine_fin, niveau
        )
        
        # Envoyer le fichier
        return send_file(
            io.BytesIO(excel_buffer),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'commande_{annee}_S{semaine_debut}-S{semaine_fin}.xlsx'
        )
        
    except Exception as e:
        print(f"Erreur export commande: {e}")
        return f"Erreur lors de l'export: {str(e)}", 500

@commande_vente_bp.route('/ajax_recalcul')
def ajax_recalcul():
    """Recalcule les suggestions avec de nouveaux paramètres"""
    try:
        # Récupérer tous les paramètres
        annee = int(request.args.get('annee'))
        semaine_debut = int(request.args.get('semaine_debut'))
        semaine_fin = int(request.args.get('semaine_fin'))
        niveau = request.args.get('niveau')
        methode = request.args.get('methode')
        coverage = int(request.args.get('coverage', 21))
        safety = float(request.args.get('safety', 1.2))
        
        # Récupérer les filtres si présents
        parent_filter = request.args.get('parent_filter')
        filtres = {}
        if parent_filter:
            if niveau == 'rayon':
                filtres['libelle_departement'] = parent_filter
            elif niveau == 'famille':
                filtres['libelle_rayon'] = parent_filter
            elif niveau == 'sous_famille':
                filtres['libelle_famille'] = parent_filter
            elif niveau == 'code_article':
                filtres['libelle_sous_famille'] = parent_filter
        
        # Recalculer les suggestions
        suggestions = get_suggestions_commande(
            annee, semaine_debut, semaine_fin,
            niveau, methode, coverage, safety, filtres
        )
        
        # Calculer les statistiques
        stats = calculer_statistiques_globales(suggestions)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'stats': stats
        })
        
    except Exception as e:
        print(f"Erreur dans ajax_recalcul: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@commande_vente_bp.route('/historique')
def historique_commandes():
    """Affiche l'historique des commandes"""
    try:
        from services.commande_vente import get_historique_commandes
        
        commandes = get_historique_commandes()
        
        return render_template(
            "historique_commandes.html",
            commandes=commandes
        )
        
    except Exception as e:
        print(f"Erreur historique commandes: {e}")
        return render_template(
            "historique_commandes.html",
            commandes=[],
            error=str(e)
        )

@commande_vente_bp.route('/details/<int:commande_id>')
def details_commande(commande_id):
    """Affiche les détails d'une commande"""
    try:
        from services.commande_vente import get_details_commande
        
        details = get_details_commande(commande_id)
        
        return render_template(
            "details_commande.html",
            commande=details
        )
        
    except Exception as e:
        print(f"Erreur détails commande: {e}")
        return f"Erreur: {str(e)}", 500

@commande_vente_bp.route('/ajax_suggestions')
def ajax_suggestions():
    """Retourne les suggestions pour un sous-niveau (AJAX)"""
    try:
        # Paramètres de base
        annee = int(request.args.get('annee', 2025))
        semaine_debut = int(request.args.get('semaine_debut', 1))
        semaine_fin = int(request.args.get('semaine_fin', 52))
        niveau = request.args.get('niveau')
        methode = request.args.get('methode', 'moyenne')
        coverage = int(request.args.get('coverage', 21))
        safety = float(request.args.get('safety', 1.2))
        
        # Filtre parent
        parent_filter = request.args.get('parent_filter')
        
        # Construction des filtres selon le niveau
        filtres = {}
        if parent_filter and niveau:
            if niveau == 'rayon':
                filtres['libelle_departement'] = parent_filter
            elif niveau == 'famille':
                filtres['libelle_rayon'] = parent_filter
            elif niveau == 'sous_famille':
                filtres['libelle_famille'] = parent_filter
            elif niveau == 'code_article':
                filtres['libelle_sous_famille'] = parent_filter
        
        # Récupérer les suggestions
        suggestions = get_suggestions_commande(
            annee, semaine_debut, semaine_fin,
            niveau, methode, coverage, safety, filtres
        )
        
        # Si c'est une requête AJAX, retourner seulement le partial
        if request.args.get('ajax') == '1':
            return render_template(
                "partials/niveau_table_commande.html",
                suggestions=suggestions,
                niveau=niveau
            )
        else:
            # Sinon, rediriger vers la page complète
            return redirect(url_for('commande_vente.commande_vente', **request.args))
        
    except Exception as e:
        print(f"Erreur dans ajax_suggestions: {e}")
        import traceback
        traceback.print_exc()
        return f"<div class='alert alert-warning'>Erreur de chargement: {str(e)}</div>", 400

@commande_vente_bp.route('/update_stock', methods=['POST'])
def update_stock():
    """Met à jour le stock d'un article"""
    try:
        data = request.get_json()
        article_code = data.get('article_code')
        article_libelle = data.get('article_libelle')
        stock_actuel = float(data.get('stock_actuel', 0))
        
        from services.commande_vente import update_stock_article
        
        result = update_stock_article(article_code, article_libelle, stock_actuel)
        
        return jsonify({
            'success': True,
            'message': 'Stock mis à jour',
            'article_code': article_code
        })
        
    except Exception as e:
        print(f"Erreur update_stock: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@commande_vente_bp.route('/update_stocks_batch', methods=['POST'])
def update_stocks_batch():
    """Met à jour plusieurs stocks en une fois"""
    try:
        data = request.get_json()
        stocks = data.get('stocks', [])
        
        from services.commande_vente import update_stocks_batch as update_batch
        
        results = update_batch(stocks)
        
        return jsonify({
            'success': True,
            'message': f'{len(results)} stocks mis à jour',
            'updated': results
        })
        
    except Exception as e:
        print(f"Erreur update_stocks_batch: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400