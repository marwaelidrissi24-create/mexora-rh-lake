"""
Script : analyse_marche.py
Projet : Mexora RH Intelligence

Objectif :
Réaliser l'analyse du marché de l'emploi IT au Maroc avec DuckDB.

Ce script répond aux 5 questions analytiques demandées dans l'Étape 3 :
1. Quelles compétences sont les plus demandées au Maroc en IT ?
2. Tanger vs Casablanca vs Rabat : où se trouvent les opportunités IT ?
3. Quel est le salaire médian par profil IT au Maroc ?
4. Y a-t-il une corrélation entre expérience requise et salaire proposé ?
5. Quelles entreprises recrutent le plus ? Qui sont les concurrents de Mexora ?

Sorties générées :
- reports/etape3/resultats/*.csv
- reports/etape3/figures/*.png
- reports/etape3/analyse_marche_resultats.md

Ces sorties seront ensuite utilisées pour construire le notebook
notebooks/analyse_marche_it_maroc.ipynb.
"""

from pathlib import Path
import textwrap

import duckdb
import pandas as pd
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_LAKE_ROOT = PROJECT_ROOT / "data_lake_mexora_rh"

GOLD_DIR = DATA_LAKE_ROOT / "gold"
SILVER_DIR = DATA_LAKE_ROOT / "silver"

REPORTS_DIR = PROJECT_ROOT / "reports" / "etape3"
RESULTS_DIR = REPORTS_DIR / "resultats"
FIGURES_DIR = REPORTS_DIR / "figures"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

SILVER_OFFRES = (SILVER_DIR / "offres_clean" / "offres_clean.parquet").as_posix()

GOLD_TOP_COMPETENCES = (GOLD_DIR / "top_competences.parquet").as_posix()
GOLD_SALAIRES = (GOLD_DIR / "salaires_par_profil.parquet").as_posix()
GOLD_OFFRES_VILLE = (GOLD_DIR / "offres_par_ville.parquet").as_posix()
GOLD_ENTREPRISES = (GOLD_DIR / "entreprises_recruteurs.parquet").as_posix()
GOLD_TENDANCES = (GOLD_DIR / "tendances_mensuelles.parquet").as_posix()


def verifier_fichiers() -> None:
    """
    Vérifie que les fichiers nécessaires à l'analyse existent.
    """
    fichiers = [
        SILVER_OFFRES,
        GOLD_TOP_COMPETENCES,
        GOLD_SALAIRES,
        GOLD_OFFRES_VILLE,
        GOLD_ENTREPRISES,
        GOLD_TENDANCES,
    ]

    manquants = [f for f in fichiers if not Path(f).exists()]

    if manquants:
        raise FileNotFoundError(
            "Certains fichiers nécessaires à l'analyse sont introuvables :\n"
            + "\n".join(manquants)
            + "\nExécuter d'abord : python main.py"
        )


def sauvegarder_resultat(df: pd.DataFrame, nom_fichier: str) -> Path:
    """
    Sauvegarde un résultat d'analyse au format CSV.
    """
    output_path = RESULTS_DIR / nom_fichier
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def dataframe_to_markdown(df: pd.DataFrame, max_rows: int = 20) -> str:
    """
    Convertit un DataFrame en tableau Markdown sans dépendre de tabulate.
    """
    if df.empty:
        return "_Aucun résultat._"

    df_display = df.head(max_rows).copy()
    df_display = df_display.fillna("")

    columns = list(df_display.columns)

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"

    rows = []
    for _, row in df_display.iterrows():
        values = [str(row[col]).replace("\n", " ") for col in columns]
        rows.append("| " + " | ".join(values) + " |")

    return "\n".join([header, separator] + rows)


def executer_requete(con: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    """
    Exécute une requête DuckDB et retourne un DataFrame pandas.
    """
    return con.execute(sql).df()


def interpretation_q1(df_top20: pd.DataFrame, df_top_data: pd.DataFrame) -> str:
    """
    Génère une interprétation textuelle pour la question 1.
    """
    top = df_top20.head(5)

    phrases_top = [
        f"{row['competence']} ({row['pct_offres_total']}% des offres)"
        for _, row in top.iterrows()
    ]

    profils = []
    for profil in ["Data Engineer", "Data Analyst", "Data Scientist"]:
        subset = df_top_data[df_top_data["profil"] == profil].head(5)
        comps = ", ".join(subset["competence"].astype(str).tolist())
        if comps:
            profils.append(f"Pour les {profil}, les compétences dominantes sont : {comps}.")

    interpretation = f"""
Les compétences les plus demandées globalement sont {", ".join(phrases_top)}.
Le marché marocain IT montre donc une forte demande sur les compétences transversales liées aux méthodes de travail, aux bases de données et à l’outillage technique.
SQL, Docker et Python ressortent comme des compétences centrales, ce qui confirme l’importance des profils capables de manipuler les données, déployer des applications et travailler dans des environnements modernes.
{" ".join(profils)}
Pour Mexora, ces résultats indiquent que les futurs recrutements data devront prioriser les compétences Python, SQL, cloud, data engineering et visualisation BI.
"""
    return textwrap.dedent(interpretation).strip()


def interpretation_q2(df_comparaison: pd.DataFrame, df_tanger: pd.DataFrame) -> str:
    """
    Génère une interprétation textuelle pour la question 2.
    """
    total_villes = (
        df_comparaison.groupby("ville", as_index=False)["nb_offres"]
        .sum()
        .sort_values("nb_offres", ascending=False)
    )

    ville_leader = total_villes.iloc[0]["ville"]
    nb_leader = int(total_villes.iloc[0]["nb_offres"])

    tanger_total = int(total_villes[total_villes["ville"] == "Tanger"]["nb_offres"].sum())

    profils_tanger = df_tanger.head(5)["profil"].tolist()

    interpretation = f"""
La ville qui concentre le plus d’opportunités IT dans le périmètre analysé est {ville_leader}, avec {nb_leader} offres.
Tanger représente {tanger_total} offres dans les profils étudiés, ce qui confirme l’existence d’un marché local, mais plus limité que Casablanca et Rabat.
Les profils les plus présents à Tanger sont notamment : {", ".join(profils_tanger)}.
Pour Mexora, basée à Tanger, cette situation implique deux options stratégiques : renforcer l’attractivité salariale locale ou ouvrir davantage le recrutement au remote/hybride depuis Casablanca et Rabat.
La part du remote/hybride permet aussi d’identifier les profils pour lesquels une stratégie de recrutement flexible peut compenser la taille plus réduite du bassin local.
"""
    return textwrap.dedent(interpretation).strip()


def interpretation_q3(df_salaires_nat: pd.DataFrame, df_salaires_tanger: pd.DataFrame) -> str:
    """
    Génère une interprétation textuelle pour la question 3.
    """
    top_salaires = df_salaires_nat.head(5)
    profils_hauts = ", ".join(
        [
            f"{row['profil']} ({int(row['salaire_median_mad'])} MAD)"
            for _, row in top_salaires.iterrows()
            if pd.notna(row["salaire_median_mad"])
        ]
    )

    data_tanger = df_salaires_tanger[
        df_salaires_tanger["profil"].isin(["Data Engineer", "Data Analyst", "Data Scientist"])
    ]

    lignes_tanger = []
    for _, row in data_tanger.iterrows():
        ecart = row["ecart_vs_mediane_nationale"]
        if pd.isna(ecart):
            sens = "non comparable"
        elif ecart > 0:
            sens = f"supérieur à la référence nationale de {int(ecart)} MAD"
        elif ecart < 0:
            sens = f"inférieur à la référence nationale de {abs(int(ecart))} MAD"
        else:
            sens = "équivalent à la référence nationale"

        lignes_tanger.append(f"{row['profil']} à Tanger est {sens}")

    interpretation = f"""
Les profils les mieux rémunérés au niveau national sont : {profils_hauts}.
Les salaires médians permettent de distinguer les profils stratégiques, notamment les profils Data, Cloud, DevOps et Architecture.
Pour Tanger, l’analyse est importante car Mexora y est implantée.
{"; ".join(lignes_tanger)}.
Ces résultats doivent aider Mexora à fixer des fourchettes salariales réalistes : rester trop bas par rapport à la médiane nationale risque de limiter l’attractivité, tandis qu’un positionnement légèrement supérieur peut accélérer le recrutement de profils rares.
"""
    return textwrap.dedent(interpretation).strip()


def interpretation_q4(df_corr: pd.DataFrame) -> str:
    """
    Génère une interprétation textuelle pour la question 4.
    """
    corr_profile = (
        df_corr[["profil", "correlation_pearson"]]
        .drop_duplicates()
        .dropna()
        .sort_values("correlation_pearson", ascending=False)
    )

    if corr_profile.empty:
        return "Les données disponibles ne permettent pas de calculer une corrélation fiable."

    top_corr = corr_profile.head(5)

    details = []
    for _, row in top_corr.iterrows():
        val = row["correlation_pearson"]
        if val >= 0.6:
            niveau = "forte"
        elif val >= 0.3:
            niveau = "modérée"
        elif val > 0:
            niveau = "faible"
        else:
            niveau = "nulle ou négative"

        details.append(f"{row['profil']} : corrélation {niveau} ({val})")

    interpretation = f"""
La corrélation de Pearson mesure la relation entre l’expérience minimale demandée et le salaire proposé.
Une valeur proche de 1 indique une relation positive forte ; une valeur proche de 0 indique une relation faible.
Les profils présentant les corrélations les plus importantes sont : {", ".join(details)}.
Lorsque la corrélation est forte ou modérée, cela signifie que les salaires progressent avec l’expérience.
Lorsque la corrélation est faible, le salaire dépend probablement d’autres facteurs : rareté des compétences, ville, type de contrat, entreprise recruteuse ou technologie demandée.
Pour Mexora, cette analyse permet de mieux calibrer les offres salariales selon le niveau d’expérience réellement attendu.
"""
    return textwrap.dedent(interpretation).strip()


def interpretation_q5(df_top_recruteurs: pd.DataFrame, df_concurrents_tanger: pd.DataFrame) -> str:
    """
    Génère une interprétation textuelle pour la question 5.
    """
    top5 = df_top_recruteurs.head(5)
    recruteurs = ", ".join(
        [
            f"{row['entreprise']} ({int(row['nb_offres_publiees'])} offres)"
            for _, row in top5.iterrows()
        ]
    )

    concurrents = df_concurrents_tanger.head(5)
    concurrents_text = ", ".join(
        [
            f"{row['entreprise']} - {row['niveau_competition']}"
            for _, row in concurrents.iterrows()
        ]
    )

    interpretation = f"""
Les entreprises qui recrutent le plus sur le marché IT marocain sont : {recruteurs}.
Elles constituent des acteurs importants du marché du talent, car elles publient un volume élevé d’offres et couvrent plusieurs profils IT.
À Tanger, les concurrents directs de Mexora sur les profils data sont notamment : {concurrents_text}.
Les entreprises avec un salaire moyen proposé élevé représentent une concurrence forte, car elles peuvent attirer plus facilement les candidats expérimentés.
Pour Mexora, il est recommandé de surveiller ces recruteurs, d’ajuster les fourchettes salariales et de mettre en avant des avantages différenciants : télétravail, évolution interne, formation data engineering et projets à forte valeur.
"""
    return textwrap.dedent(interpretation).strip()


def graphique_q1(df_top20: pd.DataFrame) -> Path:
    """
    Graphique : Top 15 compétences.
    """
    df_plot = df_top20.head(15).sort_values("nb_offres_mentionnent", ascending=True)

    plt.figure(figsize=(10, 7))
    plt.barh(df_plot["competence"], df_plot["nb_offres_mentionnent"])
    plt.title("Top 15 compétences IT les plus demandées")
    plt.xlabel("Nombre d'offres mentionnant la compétence")
    plt.ylabel("Compétence")
    plt.tight_layout()

    path = FIGURES_DIR / "q1_top15_competences.png"
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def graphique_q2(df_comparaison: pd.DataFrame) -> Path:
    """
    Graphique : Volume d'offres par ville.
    """
    df_plot = (
        df_comparaison.groupby("ville", as_index=False)["nb_offres"]
        .sum()
        .sort_values("nb_offres", ascending=False)
    )

    plt.figure(figsize=(9, 6))
    plt.bar(df_plot["ville"], df_plot["nb_offres"])
    plt.title("Volume d'offres IT par ville")
    plt.xlabel("Ville")
    plt.ylabel("Nombre d'offres")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    path = FIGURES_DIR / "q2_offres_par_ville.png"
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def graphique_q3(df_salaires_nat: pd.DataFrame) -> Path:
    """
    Graphique : salaires médians par profil.
    """
    df_plot = (
        df_salaires_nat.dropna(subset=["salaire_median_mad"])
        .sort_values("salaire_median_mad", ascending=True)
    )

    plt.figure(figsize=(10, 7))
    plt.barh(df_plot["profil"], df_plot["salaire_median_mad"])
    plt.title("Salaire médian par profil IT au Maroc")
    plt.xlabel("Salaire médian mensuel brut MAD")
    plt.ylabel("Profil")
    plt.tight_layout()

    path = FIGURES_DIR / "q3_salaires_medians_profils.png"
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def graphique_q4(df_corr: pd.DataFrame) -> Path:
    """
    Graphique : évolution du salaire médian par tranche d'expérience
    pour les profils data.
    """
    profils_data = ["Data Engineer", "Data Analyst", "Data Scientist"]
    ordre_tranches = {
        "0 — Débutant": 0,
        "1-2 ans": 1,
        "3-4 ans": 2,
        "5-7 ans": 3,
        "8+ ans Senior": 4,
        "Non précisé": 5,
    }

    df_plot = df_corr[df_corr["profil"].isin(profils_data)].copy()
    df_plot["ordre"] = df_plot["tranche_experience"].map(ordre_tranches)
    df_plot = df_plot.dropna(subset=["salaire_median", "ordre"])
    df_plot = df_plot.sort_values(["profil", "ordre"])

    plt.figure(figsize=(10, 6))

    for profil in profils_data:
        subset = df_plot[df_plot["profil"] == profil]
        if not subset.empty:
            plt.plot(
                subset["tranche_experience"],
                subset["salaire_median"],
                marker="o",
                label=profil
            )

    plt.title("Salaire médian selon l'expérience — profils data")
    plt.xlabel("Tranche d'expérience")
    plt.ylabel("Salaire médian mensuel brut MAD")
    plt.xticks(rotation=30, ha="right")
    plt.legend()
    plt.tight_layout()

    path = FIGURES_DIR / "q4_experience_salaire_profils_data.png"
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def graphique_q5(df_top_recruteurs: pd.DataFrame) -> Path:
    """
    Graphique : Top 15 entreprises recruteuses.
    """
    df_plot = df_top_recruteurs.head(15).sort_values("nb_offres_publiees", ascending=True)

    plt.figure(figsize=(10, 7))
    plt.barh(df_plot["entreprise"], df_plot["nb_offres_publiees"])
    plt.title("Top 15 entreprises recruteuses IT")
    plt.xlabel("Nombre d'offres publiées")
    plt.ylabel("Entreprise")
    plt.tight_layout()

    path = FIGURES_DIR / "q5_top_recruteurs.png"
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def ecrire_markdown(sections: list[dict]) -> Path:
    """
    Écrit un rapport Markdown de synthèse pour l'Étape 3.
    """
    output_path = REPORTS_DIR / "analyse_marche_resultats.md"

    content = [
        "# Analyse du marché de l'emploi IT au Maroc",
        "## Mexora RH Intelligence — Étape 3",
        "",
        "Ce document contient les requêtes DuckDB, les résultats sous forme de tableaux et les interprétations associées aux cinq questions analytiques du projet.",
        ""
    ]

    for section in sections:
        content.append(f"## {section['titre']}")
        content.append("")
        content.append("### Requête SQL")
        content.append("")
        content.append("```sql")
        content.append(section["sql"].strip())
        content.append("```")
        content.append("")
        content.append("### Résultat")
        content.append("")
        content.append(dataframe_to_markdown(section["df"], max_rows=20))
        content.append("")
        content.append("### Visualisation")
        content.append("")
        content.append(f"![{section['titre']}]({section['figure']})")
        content.append("")
        content.append("### Interprétation")
        content.append("")
        content.append(section["interpretation"])
        content.append("")

    output_path.write_text("\n".join(content), encoding="utf-8")
    return output_path


def main() -> None:
    """
    Exécute toutes les analyses de l'Étape 3.
    """
    verifier_fichiers()

    con = duckdb.connect(database=":memory:")

    sections = []

    # ------------------------------------------------------------------
    # Question 1
    # ------------------------------------------------------------------
    sql_q1_top20 = f"""
    -- Question 1 : Top 20 compétences toutes offres confondues
    SELECT
        famille,
        competence,
        nb_offres_mentionnent,
        pct_offres_total,
        rang_dans_profil
    FROM read_parquet('{GOLD_TOP_COMPETENCES}')
    WHERE profil = 'tous'
    ORDER BY nb_offres_mentionnent DESC
    LIMIT 20;
    """

    sql_q1_data = f"""
    -- Question 1 : Top 5 compétences par profil data
    SELECT
        profil,
        famille,
        competence,
        nb_offres_mentionnent,
        rang_dans_profil
    FROM read_parquet('{GOLD_TOP_COMPETENCES}')
    WHERE profil IN ('Data Engineer', 'Data Analyst', 'Data Scientist')
      AND rang_dans_profil <= 5
    ORDER BY profil, rang_dans_profil;
    """

    df_q1_top20 = executer_requete(con, sql_q1_top20)
    df_q1_data = executer_requete(con, sql_q1_data)

    sauvegarder_resultat(df_q1_top20, "q1_top20_competences_globales.csv")
    sauvegarder_resultat(df_q1_data, "q1_top5_competences_profils_data.csv")

    fig_q1 = graphique_q1(df_q1_top20)

    sections.append(
        {
            "titre": "Question 1 — Quelles compétences sont les plus demandées au Maroc en IT ?",
            "sql": sql_q1_top20 + "\n\n" + sql_q1_data,
            "df": df_q1_top20,
            "figure": fig_q1.relative_to(REPORTS_DIR).as_posix(),
            "interpretation": interpretation_q1(df_q1_top20, df_q1_data),
        }
    )

    # ------------------------------------------------------------------
    # Question 2
    # ------------------------------------------------------------------
    sql_q2_comparaison = f"""
    -- Question 2 : Comparaison des principales villes IT
    WITH agg AS (
        SELECT
            ville,
            profil,
            SUM(nb_offres) AS nb_offres,
            SUM(nb_offres_remote_hybrid) AS nb_offres_remote,
            ROUND(
                SUM(nb_offres_remote_hybrid) * 100.0 / NULLIF(SUM(nb_offres), 0),
                2
            ) AS pct_remote
        FROM read_parquet('{GOLD_OFFRES_VILLE}')
        WHERE ville IN ('Casablanca', 'Rabat', 'Tanger', 'Marrakech', 'Fes', 'Fès')
        GROUP BY ville, profil
    )
    SELECT
        ville,
        profil,
        nb_offres,
        nb_offres_remote,
        pct_remote,
        RANK() OVER (
            PARTITION BY profil
            ORDER BY nb_offres DESC
        ) AS rang_ville
    FROM agg
    ORDER BY profil, rang_ville;
    """

    sql_q2_tanger = f"""
    -- Question 2 : Focus Tanger avec ratio vs Casablanca
    WITH agg AS (
        SELECT
            ville,
            profil,
            SUM(nb_offres) AS nb_offres,
            SUM(nb_offres_remote_hybrid) AS nb_offres_remote,
            ROUND(
                SUM(nb_offres_remote_hybrid) * 100.0 / NULLIF(SUM(nb_offres), 0),
                2
            ) AS pct_remote
        FROM read_parquet('{GOLD_OFFRES_VILLE}')
        WHERE ville IN ('Casablanca', 'Rabat', 'Tanger', 'Marrakech', 'Fes', 'Fès')
        GROUP BY ville, profil
    ),
    ref_casa AS (
        SELECT
            profil,
            nb_offres AS nb_offres_casablanca
        FROM agg
        WHERE ville = 'Casablanca'
    )
    SELECT
        t.profil,
        t.nb_offres,
        t.nb_offres_remote,
        t.pct_remote,
        ROUND(
            t.nb_offres * 100.0 / NULLIF(c.nb_offres_casablanca, 0),
            1
        ) AS pct_vs_casa
    FROM agg t
    LEFT JOIN ref_casa c
        ON t.profil = c.profil
    WHERE t.ville = 'Tanger'
    ORDER BY t.nb_offres DESC;
    """

    df_q2_comparaison = executer_requete(con, sql_q2_comparaison)
    df_q2_tanger = executer_requete(con, sql_q2_tanger)

    sauvegarder_resultat(df_q2_comparaison, "q2_comparaison_villes_profils.csv")
    sauvegarder_resultat(df_q2_tanger, "q2_focus_tanger.csv")

    fig_q2 = graphique_q2(df_q2_comparaison)

    sections.append(
        {
            "titre": "Question 2 — Tanger vs Casablanca vs Rabat : où se trouvent les opportunités IT ?",
            "sql": sql_q2_comparaison + "\n\n" + sql_q2_tanger,
            "df": df_q2_comparaison,
            "figure": fig_q2.relative_to(REPORTS_DIR).as_posix(),
            "interpretation": interpretation_q2(df_q2_comparaison, df_q2_tanger),
        }
    )

    # ------------------------------------------------------------------
    # Question 3
    # ------------------------------------------------------------------
    sql_q3_national = f"""
    -- Question 3 : Salaires médians par profil, toutes villes
    SELECT
        profil,
        SUM(nb_offres) AS nb_offres_total,
        SUM(nb_offres_avec_salaire) AS nb_avec_salaire,
        ROUND(
            SUM(nb_offres_avec_salaire) * 100.0 / NULLIF(SUM(nb_offres), 0),
            1
        ) AS pct_salaire_communique,
        ROUND(MEDIAN(salaire_median_mad), 0) AS salaire_median_mad,
        MIN(salaire_min_observe) AS salaire_plancher,
        MAX(salaire_max_observe) AS salaire_plafond
    FROM read_parquet('{GOLD_SALAIRES}')
    GROUP BY profil
    ORDER BY salaire_median_mad DESC NULLS LAST;
    """

    sql_q3_tanger = f"""
    -- Question 3 : Salaires à Tanger vs médiane nationale
    WITH national AS (
        SELECT
            profil,
            ROUND(MEDIAN(salaire_median_mad), 0) AS salaire_median_national
        FROM read_parquet('{GOLD_SALAIRES}')
        GROUP BY profil
    ),
    tanger AS (
        SELECT
            profil,
            SUM(nb_offres) AS nb_offres,
            ROUND(MEDIAN(salaire_median_mad), 0) AS salaire_median_mad,
            ROUND(MEDIAN(salaire_q1_mad), 0) AS salaire_q1_mad,
            ROUND(MEDIAN(salaire_q3_mad), 0) AS salaire_q3_mad
        FROM read_parquet('{GOLD_SALAIRES}')
        WHERE ville = 'Tanger'
        GROUP BY profil
        HAVING SUM(nb_offres) >= 5
    )
    SELECT
        t.profil,
        t.nb_offres,
        t.salaire_median_mad,
        t.salaire_q1_mad,
        t.salaire_q3_mad,
        n.salaire_median_national,
        ROUND(
            t.salaire_median_mad - n.salaire_median_national,
            0
        ) AS ecart_vs_mediane_nationale
    FROM tanger t
    LEFT JOIN national n
        ON t.profil = n.profil
    ORDER BY t.salaire_median_mad DESC NULLS LAST;
    """

    df_q3_national = executer_requete(con, sql_q3_national)
    df_q3_tanger = executer_requete(con, sql_q3_tanger)

    sauvegarder_resultat(df_q3_national, "q3_salaires_medians_profils_national.csv")
    sauvegarder_resultat(df_q3_tanger, "q3_salaires_tanger_vs_national.csv")

    fig_q3 = graphique_q3(df_q3_national)

    sections.append(
        {
            "titre": "Question 3 — Quel est le salaire médian par profil IT au Maroc ?",
            "sql": sql_q3_national + "\n\n" + sql_q3_tanger,
            "df": df_q3_national,
            "figure": fig_q3.relative_to(REPORTS_DIR).as_posix(),
            "interpretation": interpretation_q3(df_q3_national, df_q3_tanger),
        }
    )

    # ------------------------------------------------------------------
    # Question 4
    # ------------------------------------------------------------------
    sql_q4 = f"""
    -- Question 4 : Corrélation expérience / salaire par profil
    WITH base AS (
        SELECT
            profil_normalise AS profil,
            experience_min_ans,
            salaire_median_mad,
            CASE
                WHEN experience_min_ans = 0 THEN '0 — Débutant'
                WHEN experience_min_ans BETWEEN 1 AND 2 THEN '1-2 ans'
                WHEN experience_min_ans BETWEEN 3 AND 4 THEN '3-4 ans'
                WHEN experience_min_ans BETWEEN 5 AND 7 THEN '5-7 ans'
                WHEN experience_min_ans >= 8 THEN '8+ ans Senior'
                ELSE 'Non précisé'
            END AS tranche_experience
        FROM read_parquet('{SILVER_OFFRES}')
        WHERE salaire_connu = TRUE
          AND experience_min_ans IS NOT NULL
          AND salaire_median_mad IS NOT NULL
    ),
    agregation AS (
        SELECT
            profil,
            tranche_experience,
            COUNT(*) AS nb_offres,
            ROUND(MEDIAN(salaire_median_mad), 0) AS salaire_median,
            ROUND(AVG(experience_min_ans), 2) AS experience_moyenne
        FROM base
        GROUP BY profil, tranche_experience
    ),
    correlation AS (
        SELECT
            profil,
            ROUND(CORR(experience_min_ans, salaire_median_mad), 3) AS correlation_pearson
        FROM base
        GROUP BY profil
    )
    SELECT
        a.profil,
        a.tranche_experience,
        a.nb_offres,
        a.salaire_median,
        c.correlation_pearson
    FROM agregation a
    LEFT JOIN correlation c
        ON a.profil = c.profil
    ORDER BY
        a.profil,
        CASE a.tranche_experience
            WHEN '0 — Débutant' THEN 0
            WHEN '1-2 ans' THEN 1
            WHEN '3-4 ans' THEN 2
            WHEN '5-7 ans' THEN 3
            WHEN '8+ ans Senior' THEN 4
            ELSE 5
        END;
    """

    df_q4 = executer_requete(con, sql_q4)

    sauvegarder_resultat(df_q4, "q4_correlation_experience_salaire.csv")

    fig_q4 = graphique_q4(df_q4)

    sections.append(
        {
            "titre": "Question 4 — Y a-t-il une corrélation entre expérience requise et salaire proposé ?",
            "sql": sql_q4,
            "df": df_q4,
            "figure": fig_q4.relative_to(REPORTS_DIR).as_posix(),
            "interpretation": interpretation_q4(df_q4),
        }
    )

    # ------------------------------------------------------------------
    # Question 5
    # ------------------------------------------------------------------
    sql_q5_top = f"""
    -- Question 5 : Top 20 entreprises recruteuses
    -- Mexora Analytics est exclue car l'objectif est d'identifier
    -- les recruteurs concurrents sur le marché du talent.
    SELECT
        entreprise,
        ville,
        nb_offres_publiees,
        nb_profils_differents,
        salaire_moyen_propose,
        RANK() OVER (
            ORDER BY nb_offres_publiees DESC
        ) AS rang_recruteur
    FROM read_parquet('{GOLD_ENTREPRISES}')
    WHERE entreprise <> 'Mexora Analytics'
    ORDER BY nb_offres_publiees DESC
    LIMIT 20;
    """

    sql_q5_tanger = f"""
    -- Question 5 : Concurrents directs de Mexora à Tanger sur les profils data
    SELECT
        entreprise,
        nb_offres_publiees,
        profils_recrutes,
        salaire_moyen_propose,
        CASE
            WHEN salaire_moyen_propose > 20000 THEN 'Compétiteur fort'
            WHEN salaire_moyen_propose > 12000 THEN 'Compétiteur moyen'
            ELSE 'Compétiteur faible'
        END AS niveau_competition
    FROM read_parquet('{GOLD_ENTREPRISES}')
    WHERE ville = 'Tanger'
      AND entreprise <> 'Mexora Analytics'
      AND (
            list_contains(profils_recrutes, 'Data Engineer')
         OR list_contains(profils_recrutes, 'Data Analyst')
         OR list_contains(profils_recrutes, 'Data Scientist')
      )
    ORDER BY salaire_moyen_propose DESC NULLS LAST;
    """

    df_q5_top = executer_requete(con, sql_q5_top)
    df_q5_tanger = executer_requete(con, sql_q5_tanger)

    sauvegarder_resultat(df_q5_top, "q5_top20_entreprises_recruteurs.csv")
    sauvegarder_resultat(df_q5_tanger, "q5_concurrents_tanger_profils_data.csv")

    fig_q5 = graphique_q5(df_q5_top)

    sections.append(
        {
            "titre": "Question 5 — Quelles entreprises recrutent le plus ? Qui sont les concurrents de Mexora ?",
            "sql": sql_q5_top + "\n\n" + sql_q5_tanger,
            "df": df_q5_top,
            "figure": fig_q5.relative_to(REPORTS_DIR).as_posix(),
            "interpretation": interpretation_q5(df_q5_top, df_q5_tanger),
        }
    )

    con.close()

    markdown_path = ecrire_markdown(sections)

    print("\n[ANALYSE] Étape 3 exécutée avec succès.")
    print(f"[ANALYSE] Résultats CSV : {RESULTS_DIR}")
    print(f"[ANALYSE] Figures : {FIGURES_DIR}")
    print(f"[ANALYSE] Rapport Markdown : {markdown_path}")


if __name__ == "__main__":
    main()