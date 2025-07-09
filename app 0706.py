import logging
from flask import Flask
from routes import register_blueprints
from services.utils import get_db_path
from services import init_db  # ✅ import directement depuis services.__init__

app = Flask(__name__)
app.secret_key = 'dev_0706_secret_key_meti_orika'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation base de données + enregistrement des blueprints
with app.app_context():
    init_db()
    register_blueprints(app)

# Filtre Jinja pour pagination (permet de garder les autres paramètres sans "page")
@app.template_filter('remove_page_arg')
def remove_page_arg(args_dict):
    if args_dict and 'page' in args_dict:
        args_dict = dict(args_dict)
        args_dict.pop('page', None)
    return args_dict

if __name__ == '__main__':
    app.run(debug=True)

