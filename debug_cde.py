import sqlite3
import pandas as pd
from services.utils import DB_NAME

def debug_analyse_cde():
    print("🔧 Début du débogage analyse_cde")
    with sqlite3.connect(DB_NAME) as conn:
        # Lecture des tables
        df_vente = pd.read_sql_query("SELECT code_article, libelle_article, qte, ca, ca_ht, annee, nb_semaine FROM vente_meti", conn)
        df_rupture = pd.read_sql_query("SELECT generated_id AS code_article FROM rupture_meti", conn)
        df_frs = pd.read_sql_query("SELECT * FROM ref_frs", conn)

        print(f"📊 vente_meti : {df_vente.shape}")
        print(f"📊 rupture_meti : {df_rupture.shape}")
        print(f"📊 ref_frs : {df_frs.shape}")

        # Conversion en chaînes
        df_vente["code_article"] = df_vente["code_article"].astype(str)
        df_rupture["code_article"] = df_rupture["code_article"].astype(str)
        df_frs["article"] = df_frs["article"].astype(str)

        # Fusion test vente_meti avec ref_frs
        df_fusion = df_vente.merge(df_frs, left_on="code_article", right_on="article", how="left")

        print("🔍 Aperçu de la fusion vente_meti + ref_frs :")
        print(df_fusion[["code_article", "article", "libelle_article_x", "libelle_article_y"]].head(10))

        nb_total = len(df_fusion)
        nb_fournisseurs = df_fusion["fournisseur"].notna().sum()
        nb_nan = df_fusion["fournisseur"].isna().sum()

        print(f"✅ Fournisseurs trouvés : {nb_fournisseurs} / {nb_total}")
        print(f"❌ Lignes sans fournisseur : {nb_nan}")

        # Rupture + ref_frs (pour info)
        df_rupture_fusion = df_rupture.merge(df_frs, left_on="code_article", right_on="article", how="left")
        print("🔍 Aperçu fusion rupture_meti + ref_frs :")
        print(df_rupture_fusion[["code_article", "libelle_article_y", "fournisseur"]].head(5))

if __name__ == "__main__":
    debug_analyse_cde()
