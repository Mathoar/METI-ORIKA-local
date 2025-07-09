# Importation des Blueprints
from .dashboard import dashboard_bp
print("Imported dashboard_bp:", dashboard_bp)

from .upload import upload_bp
print("Imported upload_bp:", upload_bp)

from .fournisseurs import fournisseurs_bp
print("Imported fournisseurs_bp:", fournisseurs_bp)

from .upload_stock import upload_stock_bp
print("Imported upload_stock_bp:", upload_stock_bp)

from .visualisation import visualisation_bp
print("Imported visualisation_bp:", visualisation_bp)

from .analyse_cde import analyse_cde_bp
print("Imported analyse_cde_bp:", analyse_cde_bp)

from .analyse_vente import analyse_vente_bp
print("Imported analyse_vente_bp:", analyse_vente_bp)

from .Fournisseur_actif import fournisseur_actif_bp
print("Imported fournisseur_actif_bp:", fournisseur_actif_bp)

from .commande_vente import commande_vente_bp
print("Imported commande_vente_bp:", commande_vente_bp)

# Fonction d'enregistrement des blueprints
def register_blueprints(app):
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(upload_bp, url_prefix='/upload')
    app.register_blueprint(fournisseurs_bp, url_prefix='/fournisseurs')
    app.register_blueprint(upload_stock_bp, url_prefix='/upload_stock')
    app.register_blueprint(visualisation_bp, url_prefix='/visualisation')
    app.register_blueprint(analyse_cde_bp, url_prefix='/analyse')
    app.register_blueprint(analyse_vente_bp, url_prefix='/analyse_vente')
    app.register_blueprint(fournisseur_actif_bp, url_prefix='/create_db')
    app.register_blueprint(commande_vente_bp, url_prefix='/commande_vente')
