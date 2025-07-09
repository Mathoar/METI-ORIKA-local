# ===== FICHIER 1: routes/analyse_vente.py =====

from flask import Blueprint, render_template, request
from services.analyse_vente import get_vente_grouped_details

analyse_vente_bp = Blueprint('analyse_vente', __name__, url_prefix='/analyse_vente')

@analyse_vente_bp.route('/')
def analyse_vente():
    annee = int(request.args.get('annee', 2025))
    semaine_debut = int(request.args.get('semaine_debut', 1))
    semaine_fin = int(request.args.get('semaine_fin', 52))
    indicateur = request.args.get('indicateur', 'ca')

    group_by = 'departement'
    label_field = 'libelle_departement'

    groupes, _, semaines, total_par_semaine, total_general, total_var = get_vente_grouped_details(
        annee, semaine_debut, semaine_fin, group_by, label_field, indicateur
    )

    return render_template("analyse_vente.html",
                           groupes=groupes,
                           semaines=semaines,
                           selected_annee=annee,
                           semaine_debut=semaine_debut,
                           semaine_fin=semaine_fin,
                           indicateur=indicateur,
                           label_field=label_field,
                           total_par_semaine=total_par_semaine,
                           total_general=total_general,
                           total_var=total_var)

@analyse_vente_bp.route('/ajax_niveau')
def ajax_niveau():
    niveau = request.args.get("niveau")
    parent_value = request.args.get("parent_value")
    annee = int(request.args.get("annee"))
    semaine_debut = int(request.args.get("semaine_debut"))
    semaine_fin = int(request.args.get("semaine_fin"))
    indicateur = request.args.get("indicateur", "ca")

    # Mapping des niveaux hiérarchiques
    mapping = {
        "departement": ("rayon", "libelle_rayon", "libelle_departement"),
        "rayon": ("famille", "libelle_famille", "libelle_rayon"),
        "famille": ("libelle_sous_famille", "libelle_sous_famille", "libelle_famille"),
        "libelle_sous_famille": ("code_article", "libelle_article", "libelle_sous_famille")
    }

    result = mapping.get(niveau)
    if not result:
        return ""
    
    next_group_by, label_field, filter_field = result

    # Construction des filtres selon le niveau
    filtre = {filter_field: parent_value}

    try:
        groupes, _, semaines, _, _, _ = get_vente_grouped_details(
            annee, semaine_debut, semaine_fin, next_group_by, label_field, indicateur, filtre
        )

        return render_template("partials/niveau_table.html",
                               groupes=groupes,
                               semaines=semaines,
                               label_field=label_field,
                               niveau=next_group_by)
        
    except Exception as e:
        print(f"Erreur dans ajax_niveau: {e}")
        import traceback
        traceback.print_exc()
        return f"<div class='alert alert-warning'>Erreur de chargement</div>"

def generate_niveau_table_html(groupes, semaines, label_field, niveau, indicateur="ca"):
    """Génère le HTML épuré pour un tableau de niveau"""
    if not groupes:
        return "<div class='alert alert-light text-center m-3'><i class='fas fa-info-circle mr-2'></i>Aucune donnée disponible</div>"
    
    # Configuration des niveaux épurée
    niveau_config = {
        'rayon': {'class': 'niveau-2', 'icon': 'fas fa-layer-group', 'label': 'Rayons'},
        'famille': {'class': 'niveau-3', 'icon': 'fas fa-tags', 'label': 'Familles'},
        'libelle_sous_famille': {'class': 'niveau-4', 'icon': 'fas fa-tag', 'label': 'Sous-familles'},
        'code_article': {'class': 'niveau-5', 'icon': 'fas fa-cube', 'label': 'Articles'}
    }
    
    config = niveau_config.get(niveau, {'class': 'niveau-2', 'icon': 'fas fa-list', 'label': 'Éléments'})
    
    html = ['<div class="card border-0 shadow-sm">']
    html.append('<div class="card-header bg-white border-bottom">')
    html.append(f'<h6 class="mb-0 text-muted"><i class="{config["icon"]} mr-2"></i>{config["label"]} ({len(groupes)})</h6>')
    html.append('</div>')
    html.append('<div class="card-body p-0">')
    html.append('<div class="table-responsive">')
    html.append('<table class="table">')
    
    # En-tête simple
    html.append('<thead><tr>')
    html.append(f'<th style="width: 40%;">{config["label"][:-1]}</th>')  # Enlever le 's' final
    for s in semaines:
        html.append(f'<th class="text-center">S{s}</th>')
    html.append('<th class="text-center">Total</th>')
    html.append('<th class="text-center">Évolution</th>')
    html.append('</tr></thead>')
    
    # Corps du tableau épuré
    html.append('<tbody>')
    for i, g in enumerate(groupes):
        evolution = g.get('VAR_%', 0)
        
        # Classes CSS simples
        if evolution > 5:
            css_class = f"{config['class']} progression"
        elif evolution < -5:
            css_class = f"{config['class']} regression"
        else:
            css_class = f"{config['class']} stable"
        
        html.append(f'<tr class="{css_class}">')
        
        # Première colonne épurée
        html.append('<td>')
        if niveau != 'code_article':
            clean_id = f"sous_{niveau}_{i}_{abs(hash(str(g[label_field])))}".replace('-', 'neg')
            html.append(f'''
                <a href="#" class="niveau-suivant" 
                   data-niveau="{niveau}"
                   data-parent-value="{g[label_field]}"
                   data-target-id="{clean_id}">
                    <i class="fas fa-plus-circle expand-icon"></i>
                    {g[label_field]}
                </a>
            ''')
        else:
            # Articles avec affichage épuré et couleur de police uniquement
            code = g.get(niveau, '')
            html.append(f'''
                <div class="article-info">
                    <span class="article-code">{code}</span>
                    <span class="article-libelle">{g[label_field]}</span>
                </div>
            ''')
        html.append('</td>')
        
        # Colonnes des semaines
        for s in semaines:
            valeur = g.get(s, 0)
            if indicateur == 'ca':
                formatted_value = f"{valeur:,.0f}€"
            else:
                formatted_value = f"{valeur:,.0f}"
            html.append(f'<td class="text-right">{formatted_value}</td>')
        
        # Total
        total = g.get('TOTAL', 0)
        if indicateur == 'ca':
            formatted_total = f"{total:,.0f}€"
        else:
            formatted_total = f"{total:,.0f}"
        html.append(f'<td class="text-right font-weight-medium">{formatted_total}</td>')
        
        # Évolution avec badge sobre
        if evolution > 5:
            badge_class = 'evolution-positive'
        elif evolution < -5:
            badge_class = 'evolution-negative'
        else:
            badge_class = 'evolution-stable'
        
        evolution_sign = '+' if evolution > 0 else ''
        html.append(f'<td class="text-center"><span class="evolution-badge {badge_class}">{evolution_sign}{evolution:.1f}%</span></td>')
        html.append('</tr>')
        
        # Ligne pour sous-niveaux
        if niveau != 'code_article':
            clean_id = f"sous_{niveau}_{i}_{abs(hash(str(g[label_field])))}".replace('-', 'neg')
            html.append(f'''
                <tr class="sous-niveau d-none" id="{clean_id}">
                    <td colspan="{len(semaines) + 3}" class="p-0 border-0"></td>
                </tr>
            ''')
    
    html.append('</tbody>')
    
    # Totaux si nécessaire
    if len(groupes) > 1:
        html.append('<tfoot><tr class="total-row">')
        html.append(f'<td><strong>Total {config["label"].lower()}</strong></td>')
        
        for s in semaines:
            total_semaine = sum(g.get(s, 0) for g in groupes)
            if indicateur == 'ca':
                formatted_total = f"{total_semaine:,.0f}€"
            else:
                formatted_total = f"{total_semaine:,.0f}"
            html.append(f'<td class="text-right"><strong>{formatted_total}</strong></td>')
        
        total_general = sum(g.get('TOTAL', 0) for g in groupes)
        if indicateur == 'ca':
            formatted_total_general = f"{total_general:,.0f}€"
        else:
            formatted_total_general = f"{total_general:,.0f}"
        html.append(f'<td class="text-right"><strong>{formatted_total_general}</strong></td>')
        
        evolutions = [g.get('VAR_%', 0) for g in groupes if g.get('VAR_%', 0) != 0]
        avg_evolution = sum(evolutions) / len(evolutions) if evolutions else 0
        html.append(f'<td class="text-center"><strong>{avg_evolution:.1f}%</strong></td>')
        html.append('</tr></tfoot>')
    
    html.append('</table></div></div></div>')
    return ''.join(html)


# ===== FICHIER 2: services/analyse_vente.py =====

import sqlite3
import pandas as pd

DB_PATH = "/Users/mhoar/Desktop/python_vscode/price_comparison.db"

def get_vente_grouped_details(annee, semaine_debut, semaine_fin, group_by, label_field, indicateur, filtres=None):
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Déterminer le champ à utiliser
        if indicateur == "ca":
            value_field = "ca"
        elif indicateur == "qte":
            value_field = "qte"
        else:
            value_field = "ca"  # Par défaut
        
        # Agrégation directe dans la requête SQL
        query = f"""
            SELECT 
                {group_by}, 
                {label_field}, 
                semaine, 
                SUM({value_field}) as valeur
            FROM vente_meti
            WHERE annee = ?
              AND semaine BETWEEN ? AND ?
        """

        params = [annee, semaine_debut, semaine_fin]

        if filtres:
            for k, v in filtres.items():
                query += f" AND {k} = ?"
                params.append(v)

        query += f" GROUP BY {group_by}, {label_field}, semaine"

        # Exécution de la requête
        df = pd.read_sql_query(query, conn, params=params)
        
        # Nettoyage des données
        df = df.loc[:, ~df.columns.duplicated()].copy()
        for col in [group_by, label_field]:
            if col in df.columns:
                df[col] = df[col].astype(str)

        # Pivot des groupes
        index_fields = [group_by, label_field]
        if group_by == label_field:
            index_fields = [group_by]

        pivot_groupes = df.pivot_table(
            index=index_fields, 
            columns='semaine', 
            values='valeur',
            fill_value=0,
            aggfunc='sum'
        )

        sem_cols = sorted([col for col in pivot_groupes.columns if isinstance(col, int)])
        
        # Calcul des totaux et évolutions
        pivot_groupes['TOTAL'] = pivot_groupes[sem_cols].sum(axis=1)
        
        if len(sem_cols) >= 2:
            pivot_groupes['VAR_%'] = ((pivot_groupes[sem_cols[-1]] - pivot_groupes[sem_cols[0]]) / pivot_groupes[sem_cols[0]].replace(0, 1)) * 100
        else:
            pivot_groupes['VAR_%'] = 0
        
        pivot_groupes = pivot_groupes.reset_index()
        
        # TRI PAR TOTAL DÉCROISSANT
        pivot_groupes = pivot_groupes.sort_values('TOTAL', ascending=False)

        # Totaux globaux
        total_par_semaine = pivot_groupes[sem_cols].sum().to_dict()
        total_general = pivot_groupes['TOTAL'].sum()
        total_var = pivot_groupes['VAR_%'].mean()

        return (
            pivot_groupes.to_dict(orient="records"),
            [],  # articles vide pour compatibilité
            sem_cols,
            total_par_semaine,
            total_general,
            total_var
        )
        
    except Exception as e:
        print(f"Erreur dans get_vente_grouped_details: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        conn.close()