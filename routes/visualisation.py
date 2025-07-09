# routes/visualisation.py
from flask import Blueprint, render_template, request
import sqlite3
from services.utils import get_db_path

visualisation_bp = Blueprint('visualisation', __name__)

@visualisation_bp.route('/visualisation', methods=['GET'])
def visualisation():
    db_path = get_db_path()
    table = request.args.get('table')

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        # Récupère toutes les tables de la base
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = sorted([row[0] for row in cursor.fetchall()])

        table_data = []
        column_info = []
        total_rows = 0

        if table in all_tables:
            # Infos colonnes
            cursor.execute(f"PRAGMA table_info({table})")
            column_info = cursor.fetchall()

            # 10 premières lignes
            cursor.execute(f"SELECT * FROM {table} LIMIT 10")
            table_data = cursor.fetchall()

            # Total de lignes
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            total_rows = cursor.fetchone()[0]

    return render_template('visualisation.html',
                           all_tables=all_tables,
                           selected_table=table,
                           table_data=table_data,
                           column_info=column_info,
                           total_rows=total_rows)
