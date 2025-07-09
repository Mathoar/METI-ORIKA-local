from flask import Blueprint

# Blueprint pour vos routes “analyse”
analyse_bp = Blueprint('analyse', __name__)

# vous pouvez déclarer ici vos @analyse_bp.route(...) si besoin...
# par exemple :
# @analyse_bp.route('/analyse_cde')
# def analyse_cde_view():
#     ...

from .dashboard import dashboard_bp
from .upload import upload_bp
from .fournisseurs import fournisseurs_bp

def register_blueprints(app):
    app.register_blueprint(dashboard_bp,    url_prefix='/')
    app.register_blueprint(upload_bp,       url_prefix='/upload')
    app.register_blueprint(fournisseurs_bp, url_prefix='/fournisseurs')
    app.register_blueprint(analyse_bp,      url_prefix='/analyse')
