from flask import Blueprint, render_template
import sqlite3
import pandas as pd
import logging
from services import get_db_path

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')


@dashboard_bp.route('/', methods=['GET', 'POST'])
def dashboard():
    table = None
    report_path = None
    error_message = None
    meti_rows = []
    vente_meti_rows = []
    ref_frs_rows = []

    # Résumés
    meti_summary = {'nb_lignes': 0, 'nb_articles': 0, 'ca_total': 0.0, 'passage_total': 0.0, 'marge_total': 0.0}
    orika_summary = {'nb_lignes': 0, 'nb_articles': 0, 'ca_total': 0.0, 'passage_total': 0.0, 'marge_total': 0.0}
    ref_frs_summary = {'nb_lignes': 0, 'nb_articles': 0, 'prix_de_vente_total': 0.0}

    # Aperçus
    orika_preview = []
    orika_columns = []
    vente_meti_preview = []
    vente_meti_columns = []

    try:
        with sqlite3.connect(get_db_path()) as conn:
            # METI
            meti_df = pd.read_sql_query("SELECT * FROM meti", conn)
            if not meti_df.empty:
                meti_rows = meti_df[['generated_id', 'generated_article', 'ca_ht', 'passage', 'marge', 'pm', 'tdm', 'poids_promo']].values.tolist()
                meti_summary['nb_lignes'] = len(meti_df)
                meti_summary['nb_articles'] = meti_df['nomenclature'].nunique()
                meti_summary['ca_total'] = meti_df['ca_ht'].sum()
                meti_summary['passage_total'] = pd.to_numeric(meti_df['passage'], errors='coerce').sum()
                meti_summary['marge_total'] = meti_df['marge'].sum()

            # ORIKA
            full_orika_df = pd.read_sql_query("SELECT * FROM orika", conn)
            if not full_orika_df.empty:
                orika_summary['nb_lignes'] = len(full_orika_df)
                orika_summary['nb_articles'] = full_orika_df['libelle'].nunique()
                orika_summary['ca_total'] = full_orika_df['cattc'].sum()
                orika_summary['passage_total'] = full_orika_df['nb_articles_vendus'].sum()

                orika_df = full_orika_df.sort_values(by='cattc', ascending=False).head(50)
                orika_preview = orika_df.values.tolist()
                orika_columns = orika_df.columns.tolist()

            # VENTE METI
            full_vente_df = pd.read_sql_query("SELECT * FROM vente_meti", conn)
            if not full_vente_df.empty:
                vente_meti_df = full_vente_df.sort_values(by='ca_ht', ascending=False).head(50)
                vente_meti_preview = vente_meti_df[['n_ligne', 'site', 'libelle_article', 'ca_ht', 'qte']].values.tolist()
                vente_meti_columns = ['n_ligne', 'site', 'libelle_article', 'ca_ht', 'qte']

            # Ref Frs
            ref_frs_df = pd.read_sql_query("SELECT * FROM ref_frs", conn)
            if not ref_frs_df.empty:
                ref_frs_rows = ref_frs_df.sort_values(by='prix_de_vente', ascending=False).head(50).values.tolist()
                ref_frs_summary['nb_lignes'] = len(ref_frs_df)
                ref_frs_summary['nb_articles'] = ref_frs_df['article'].nunique()
                ref_frs_summary['prix_de_vente_total'] = ref_frs_df['prix_de_vente'].sum()

    except Exception as e:
        logger.error(f"Error fetching data for dashboard: {e}")
        error_message = f"Erreur lors du chargement du tableau de bord : {str(e)}"

    return render_template(
        'dashboard.html',
        table=table,
        report_path=report_path,
        error_message=error_message,
        meti_rows=meti_rows,
        orika_preview=orika_preview,
        orika_columns=orika_columns,
        vente_meti_rows=vente_meti_preview,
        vente_meti_columns=vente_meti_columns,
        ref_frs_rows=ref_frs_rows,
        meti_summary=meti_summary,
        orika_summary=orika_summary,
        ref_frs_summary=ref_frs_summary,
        chart_data={}
    )
