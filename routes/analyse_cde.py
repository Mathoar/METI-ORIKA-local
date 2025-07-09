from flask import Blueprint, request, jsonify, render_template
from services.analyse_cde import get_analyse_cde_data, inserer_donnees_analyse_cde

analyse_cde_bp = Blueprint('analyse_cde', __name__)

@analyse_cde_bp.route("/", methods=["GET"])
def analyse_commande():
    data = get_analyse_cde_data(request)
    return render_template("analyse_commande.html", **data)

@analyse_cde_bp.route("/proposer", methods=["POST"])
def proposer_commandes():
    result = inserer_donnees_analyse_cde()
    return jsonify(result)

@analyse_cde_bp.route("/data", methods=["GET"])
def get_data():
    df = get_analyse_cde_data(request)

    filters = {
        "libelle_article": request.args.get("libelle_article", "").lower(),
        "code_article": request.args.get("code_article", "").lower(),
        "module": request.args.get("module", "").lower(),
        "libelle_departement": request.args.get("libelle_departement", "").lower(),
        "libelle_rayon": request.args.get("libelle_rayon", "").lower(),
        "libelle_famille": request.args.get("libelle_famille", "").lower(),
        "libelle_sous_famille": request.args.get("libelle_sous_famille", "").lower(),
        "code_marque": request.args.get("code_marque", "").lower(),
        "fournisseur": request.args.get("fournisseur", "").lower(),
        "pcb_commandable": request.args.get("pcb_commandable", "").upper()
    }

    df_rows = df.get("analyse_cde_rows", [])
    selected_columns = df.get("selected_columns", [])

    filtered_data = []
    for row in df_rows:
        match = True
        for key, val in filters.items():
            if val and val not in str(row.get(key, "")).lower():
                match = False
                break
        if match:
            filtered_data.append({k: row.get(k, "") for k in selected_columns})

    return jsonify(filtered_data)
