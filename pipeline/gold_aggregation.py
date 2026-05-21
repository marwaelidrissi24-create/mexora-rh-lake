"""
Script : gold_aggregation.py
Projet : Mexora RH Intelligence

Objectif :
Construire la zone Gold du Data Lake à partir des fichiers Silver.

Entrées :
- data_lake_mexora_rh/silver/offres_clean/offres_clean.parquet
- data_lake_mexora_rh/silver/competences_extraites/competences.parquet

Sorties Gold :
- top_competences.parquet
- salaires_par_profil.parquet
- offres_par_ville.parquet
- entreprises_recruteurs.parquet
- tendances_mensuelles.parquet

Outil principal :
DuckDB pour exécuter des requêtes SQL directement sur les fichiers Parquet.
"""

import sys
from pathlib import Path

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.utils import ensure_directory, log_step


def verifier_sources_silver(silver_offres: Path, silver_competences: Path) -> None:
    """
    Vérifie que les fichiers Silver nécessaires existent avant de construire Gold.
    """
    if not silver_offres.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {silver_offres}. "
            "Exécuter d'abord pipeline/silver_transform.py."
        )

    if not silver_competences.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {silver_competences}. "
            "Exécuter d'abord pipeline/silver_nlp.py."
        )


def clean_previous_gold_outputs(gold_path: Path) -> None:
    """
    Supprime les anciens fichiers Parquet Gold pour garantir un run reproductible.
    """
    ensure_directory(gold_path)

    for parquet_file in gold_path.glob("*.parquet"):
        parquet_file.unlink()


def construire_top_competences(con: duckdb.DuckDBPyConnection, silver_comp: str, silver_offres: str) -> pd.DataFrame:
    """
    Table Gold 1 :
    Top compétences demandées par profil + agrégat global 'tous'.

    Cette table répondra à la question :
    Quelles compétences sont les plus demandées au Maroc en IT ?
    """
    query = f"""
    WITH total_offres AS (
        SELECT COUNT(DISTINCT id_offre) AS total
        FROM read_parquet('{silver_offres}')
    ),

    competences_par_profil AS (
        SELECT
            profil,
            famille,
            competence,
            COUNT(DISTINCT id_offre) AS nb_offres_mentionnent
        FROM read_parquet('{silver_comp}')
        WHERE competence != 'non_detecte'
        GROUP BY profil, famille, competence
    ),

    competences_globales AS (
        SELECT
            'tous' AS profil,
            famille,
            competence,
            COUNT(DISTINCT id_offre) AS nb_offres_mentionnent
        FROM read_parquet('{silver_comp}')
        WHERE competence != 'non_detecte'
        GROUP BY famille, competence
    ),

    union_competences AS (
        SELECT * FROM competences_par_profil
        UNION ALL
        SELECT * FROM competences_globales
    )

    SELECT
        profil,
        famille,
        competence,
        nb_offres_mentionnent,
        ROUND(nb_offres_mentionnent * 100.0 / (SELECT total FROM total_offres), 2) AS pct_offres_total,
        RANK() OVER (
            PARTITION BY profil
            ORDER BY nb_offres_mentionnent DESC
        ) AS rang_dans_profil
    FROM union_competences
    ORDER BY profil, rang_dans_profil, competence
    """

    return con.execute(query).df()


def construire_salaires_par_profil(con: duckdb.DuckDBPyConnection, silver_offres: str) -> pd.DataFrame:
    """
    Table Gold 2 :
    Salaires par profil, ville et type de contrat.

    Cette table servira pour :
    - salaire médian par profil ;
    - comparaison Tanger vs médiane nationale ;
    - recommandations salariales pour Mexora.
    """
    query = f"""
    SELECT
        profil_normalise AS profil,
        ville_std AS ville,
        region_admin,
        type_contrat_std AS type_contrat,
        COUNT(*) AS nb_offres,
        COUNT(*) FILTER (WHERE salaire_connu = TRUE) AS nb_offres_avec_salaire,

        ROUND(
            COUNT(*) FILTER (WHERE salaire_connu = TRUE) * 100.0
            / NULLIF(COUNT(*), 0),
            2
        ) AS pct_salaire_communique,

        ROUND(MEDIAN(salaire_median_mad) FILTER (WHERE salaire_connu = TRUE), 0) AS salaire_median_mad,
        ROUND(AVG(salaire_median_mad) FILTER (WHERE salaire_connu = TRUE), 0) AS salaire_moyen_mad,
        ROUND(QUANTILE_CONT(salaire_median_mad, 0.25) FILTER (WHERE salaire_connu = TRUE), 0) AS salaire_q1_mad,
        ROUND(QUANTILE_CONT(salaire_median_mad, 0.75) FILTER (WHERE salaire_connu = TRUE), 0) AS salaire_q3_mad,
        ROUND(MIN(salaire_min_mad) FILTER (WHERE salaire_connu = TRUE), 0) AS salaire_min_observe,
        ROUND(MAX(salaire_max_mad) FILTER (WHERE salaire_connu = TRUE), 0) AS salaire_max_observe,

        SUM(nb_postes) AS nb_postes_total
    FROM read_parquet('{silver_offres}')
    GROUP BY profil_normalise, ville_std, region_admin, type_contrat_std
    HAVING COUNT(*) >= 3
    ORDER BY nb_offres DESC
    """

    return con.execute(query).df()


def construire_offres_par_ville(con: duckdb.DuckDBPyConnection, silver_offres: str) -> pd.DataFrame:
    """
    Table Gold 3 :
    Volume d'offres par ville, profil, année et mois.

    Cette table servira pour :
    - comparaison Tanger / Casablanca / Rabat ;
    - analyse du remote/hybride ;
    - carte ou dashboard par ville.
    """
    query = f"""
    SELECT
        ville_std AS ville,
        region_admin,
        profil_normalise AS profil,
        annee,
        mois,
        mois_partition,
        COUNT(*) AS nb_offres,
        SUM(nb_postes) AS nb_postes_total,

        COUNT(*) FILTER (WHERE is_remote_or_hybrid = TRUE) AS nb_offres_remote_hybrid,

        ROUND(
            COUNT(*) FILTER (WHERE is_remote_or_hybrid = TRUE) * 100.0
            / NULLIF(COUNT(*), 0),
            2
        ) AS pct_remote_hybrid,

        COUNT(*) FILTER (WHERE type_contrat_std = 'CDI') AS nb_cdi,
        COUNT(*) FILTER (WHERE type_contrat_std = 'Freelance') AS nb_freelance,
        COUNT(*) FILTER (WHERE type_contrat_std = 'CDD') AS nb_cdd,
        COUNT(*) FILTER (WHERE type_contrat_std = 'Stage') AS nb_stage
    FROM read_parquet('{silver_offres}')
    GROUP BY ville_std, region_admin, profil_normalise, annee, mois, mois_partition
    ORDER BY annee, mois, ville, profil
    """

    return con.execute(query).df()


def construire_entreprises_recruteurs(con: duckdb.DuckDBPyConnection, silver_offres: str) -> pd.DataFrame:
    """
    Table Gold 4 :
    Entreprises les plus recruteuses.

    Cette table servira pour :
    - identifier les concurrents de Mexora sur le marché du talent ;
    - repérer les entreprises actives par ville et profil.
    """
    query = f"""
    SELECT
        entreprise,
        ville_std AS ville,
        region_admin,
        COUNT(*) AS nb_offres_publiees,
        SUM(nb_postes) AS nb_postes_total,
        COUNT(DISTINCT profil_normalise) AS nb_profils_differents,

        ROUND(AVG(salaire_median_mad) FILTER (WHERE salaire_connu = TRUE), 0) AS salaire_moyen_propose,
        ROUND(MEDIAN(salaire_median_mad) FILTER (WHERE salaire_connu = TRUE), 0) AS salaire_median_propose,

        ARRAY_AGG(DISTINCT profil_normalise ORDER BY profil_normalise) AS profils_recrutes,
        ARRAY_AGG(DISTINCT type_contrat_std ORDER BY type_contrat_std) AS contrats_utilises,

        MIN(date_publication_dt) AS premiere_offre,
        MAX(date_publication_dt) AS derniere_offre,

        COUNT(*) FILTER (WHERE is_remote_or_hybrid = TRUE) AS nb_offres_remote_hybrid
    FROM read_parquet('{silver_offres}')
    WHERE entreprise IS NOT NULL
      AND entreprise != ''
      AND entreprise != 'Non renseignée'
    GROUP BY entreprise, ville_std, region_admin
    HAVING COUNT(*) >= 3
    ORDER BY nb_offres_publiees DESC, nb_postes_total DESC
    """

    return con.execute(query).df()


def construire_tendances_mensuelles(con: duckdb.DuckDBPyConnection, silver_offres: str) -> pd.DataFrame:
    """
    Table Gold 5 :
    Tendances mensuelles du marché IT.

    Cette table servira pour :
    - courbe temporelle 2023-2024 ;
    - évolution des profils data ;
    - analyse du dynamisme du marché.
    """
    query = f"""
    WITH monthly AS (
        SELECT
            annee,
            mois,
            mois_partition,
            profil_normalise AS profil,
            COUNT(*) AS nb_offres,
            SUM(nb_postes) AS nb_postes_total,
            ROUND(AVG(salaire_median_mad) FILTER (WHERE salaire_connu = TRUE), 0) AS salaire_moyen_mois,
            ROUND(MEDIAN(salaire_median_mad) FILTER (WHERE salaire_connu = TRUE), 0) AS salaire_median_mois,
            COUNT(*) FILTER (WHERE is_remote_or_hybrid = TRUE) AS nb_remote_hybrid
        FROM read_parquet('{silver_offres}')
        WHERE annee IS NOT NULL
          AND mois IS NOT NULL
        GROUP BY annee, mois, mois_partition, profil_normalise
    )

    SELECT
        annee,
        mois,
        mois_partition,
        profil,
        nb_offres,
        nb_postes_total,
        salaire_moyen_mois,
        salaire_median_mois,
        nb_remote_hybrid,

        LAG(nb_offres) OVER (
            PARTITION BY profil
            ORDER BY annee, mois
        ) AS nb_offres_mois_precedent,

        nb_offres
        - LAG(nb_offres) OVER (
            PARTITION BY profil
            ORDER BY annee, mois
        ) AS variation_nb_offres,

        ROUND(
            (nb_offres - LAG(nb_offres) OVER (
                PARTITION BY profil
                ORDER BY annee, mois
            )) * 100.0
            / NULLIF(LAG(nb_offres) OVER (
                PARTITION BY profil
                ORDER BY annee, mois
            ), 0),
            2
        ) AS variation_pct
    FROM monthly
    ORDER BY profil, annee, mois
    """

    return con.execute(query).df()


def sauvegarder_table_gold(df: pd.DataFrame, output_file: Path, table_name: str) -> None:
    """
    Sauvegarde une table Gold en Parquet.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_file, index=False, compression="snappy")
    print(f"[GOLD] {table_name} sauvegardée : {output_file} | lignes={len(df)}")


def construire_gold(data_lake_root: str | Path, report_path: str | Path) -> dict:
    """
    Construit toutes les tables Gold depuis les données Silver.
    """
    data_lake_root = Path(data_lake_root)
    report_path = Path(report_path)

    silver_offres_path = data_lake_root / "silver" / "offres_clean" / "offres_clean.parquet"
    silver_comp_path = data_lake_root / "silver" / "competences_extraites" / "competences.parquet"
    gold_path = data_lake_root / "gold"

    verifier_sources_silver(silver_offres_path, silver_comp_path)
    clean_previous_gold_outputs(gold_path)

    silver_offres = silver_offres_path.as_posix()
    silver_comp = silver_comp_path.as_posix()

    con = duckdb.connect(database=":memory:")

    stats = {}

    print("[GOLD] Construction top_competences...")
    df_top_competences = construire_top_competences(con, silver_comp, silver_offres)
    sauvegarder_table_gold(
        df_top_competences,
        gold_path / "top_competences.parquet",
        "top_competences"
    )
    stats["top_competences"] = len(df_top_competences)

    print("[GOLD] Construction salaires_par_profil...")
    df_salaires = construire_salaires_par_profil(con, silver_offres)
    sauvegarder_table_gold(
        df_salaires,
        gold_path / "salaires_par_profil.parquet",
        "salaires_par_profil"
    )
    stats["salaires_par_profil"] = len(df_salaires)

    print("[GOLD] Construction offres_par_ville...")
    df_villes = construire_offres_par_ville(con, silver_offres)
    sauvegarder_table_gold(
        df_villes,
        gold_path / "offres_par_ville.parquet",
        "offres_par_ville"
    )
    stats["offres_par_ville"] = len(df_villes)

    print("[GOLD] Construction entreprises_recruteurs...")
    df_entreprises = construire_entreprises_recruteurs(con, silver_offres)
    sauvegarder_table_gold(
        df_entreprises,
        gold_path / "entreprises_recruteurs.parquet",
        "entreprises_recruteurs"
    )
    stats["entreprises_recruteurs"] = len(df_entreprises)

    print("[GOLD] Construction tendances_mensuelles...")
    df_tendances = construire_tendances_mensuelles(con, silver_offres)
    sauvegarder_table_gold(
        df_tendances,
        gold_path / "tendances_mensuelles.parquet",
        "tendances_mensuelles"
    )
    stats["tendances_mensuelles"] = len(df_tendances)

    con.close()

    log_step(
        report_path=report_path,
        step_name="Construction des tables Gold",
        rule="Agrégation analytique des données Silver avec DuckDB et sauvegarde en Parquet.",
        rows_before=None,
        rows_after=sum(stats.values()),
        details=f"Tables générées: {stats}"
    )

    print("\n[GOLD] Construction Gold terminée avec succès")
    print(f"[GOLD] Tables générées dans : {gold_path}")
    print(f"[GOLD] Statistiques : {stats}")

    return stats


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    data_lake_root = project_root / "data_lake_mexora_rh"
    report_path = project_root / "docs" / "rapport_pipeline.md"

    construire_gold(
        data_lake_root=data_lake_root,
        report_path=report_path
    )


if __name__ == "__main__":
    main()