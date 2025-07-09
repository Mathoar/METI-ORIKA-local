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
        
        # TRI PAR TOTAL DÉCROISSANT - DU PLUS GRAND AU PLUS PETIT
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