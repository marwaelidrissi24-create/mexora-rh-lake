"""
Script : build_step4_report_dashboard.py
Projet : Mexora RH Intelligence

Objectif :
Générer les livrables de l'Étape 4 :
- Dashboard de synthèse avec 4 visualisations minimum
- Rapport analytique orienté DRH, non technique, en Markdown

Sorties :
reports/etape4/
├── figures/
│   ├── dashboard_synthese.png
│   ├── carte_maroc_bubbles.png
│   ├── top15_competences.png
│   ├── boxplot_salaires_profils.png
│   └── evolution_mensuelle_data.png
├── dashboard_synthese.html
└── rapport_analytique_mexora.md
"""

from pathlib import Path
import textwrap

import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import plotly.express as px


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_LAKE_ROOT = PROJECT_ROOT / "data_lake_mexora_rh"
GOLD_DIR = DATA_LAKE_ROOT / "gold"
SILVER_DIR = DATA_LAKE_ROOT / "silver"

OUTPUT_DIR = PROJECT_ROOT / "reports" / "etape4"
FIGURES_DIR = OUTPUT_DIR / "figures"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

SILVER_OFFRES = (SILVER_DIR / "offres_clean" / "offres_clean.parquet").as_posix()
GOLD_TOP_COMP = (GOLD_DIR / "top_competences.parquet").as_posix()
GOLD_SALAIRES = (GOLD_DIR / "salaires_par_profil.parquet").as_posix()
GOLD_OFFRES_VILLE = (GOLD_DIR / "offres_par_ville.parquet").as_posix()
GOLD_ENTREPRISES = (GOLD_DIR / "entreprises_recruteurs.parquet").as_posix()
GOLD_TENDANCES = (GOLD_DIR / "tendances_mensuelles.parquet").as_posix()


THEME = {
    "rose": "#F8BBD0",
    "rose_dark": "#D81B60",
    "violet": "#CE93D8",
    "violet_dark": "#6A1B9A",
    "lavender": "#F3E5F5",
    "white": "#FFFFFF",
    "ink": "#2D2433",
    "muted": "#6C5A72",
    "grid": "#E8DDEE",
    "green": "#7CB342",
}


def verifier_fichiers() -> None:
    fichiers = [
        SILVER_OFFRES,
        GOLD_TOP_COMP,
        GOLD_SALAIRES,
        GOLD_OFFRES_VILLE,
        GOLD_ENTREPRISES,
        GOLD_TENDANCES,
    ]
    manquants = [f for f in fichiers if not Path(f).exists()]
    if manquants:
        raise FileNotFoundError(
            "Fichiers manquants. Exécuter d'abord : python main.py\n"
            + "\n".join(manquants)
        )


def savefig(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()


def get_dataframes() -> dict:
    con = duckdb.connect(database=":memory:")

    top_comp = con.execute(f"""
        SELECT
            famille,
            competence,
            nb_offres_mentionnent,
            pct_offres_total
        FROM read_parquet('{GOLD_TOP_COMP}')
        WHERE profil = 'tous'
        ORDER BY nb_offres_mentionnent DESC
        LIMIT 15
    """).df()

    villes = con.execute(f"""
        SELECT
            ville,
            SUM(nb_offres) AS nb_offres,
            SUM(nb_offres_remote_hybrid) AS nb_remote_hybrid,
            ROUND(SUM(nb_offres_remote_hybrid) * 100.0 / NULLIF(SUM(nb_offres), 0), 1) AS pct_remote_hybrid
        FROM read_parquet('{GOLD_OFFRES_VILLE}')
        GROUP BY ville
        ORDER BY nb_offres DESC
    """).df()

    salaires_raw = con.execute(f"""
        SELECT
            profil_normalise AS profil,
            salaire_median_mad
        FROM read_parquet('{SILVER_OFFRES}')
        WHERE salaire_connu = TRUE
          AND salaire_median_mad IS NOT NULL
          AND profil_normalise IN (
              'Data Engineer',
              'Data Analyst',
              'Data Scientist',
              'DevOps / SRE',
              'Cloud Engineer',
              'Développeur Full Stack',
              'Développeur Backend',
              'Développeur Frontend'
          )
    """).df()

    tendances = con.execute(f"""
        SELECT
            annee,
            mois,
            mois_partition,
            profil,
            SUM(nb_offres) AS nb_offres
        FROM read_parquet('{GOLD_TENDANCES}')
        WHERE profil IN ('Data Engineer', 'Data Analyst', 'Data Scientist')
        GROUP BY annee, mois, mois_partition, profil
        ORDER BY annee, mois, profil
    """).df()

    salaires_nat = con.execute(f"""
        SELECT
            profil,
            SUM(nb_offres) AS nb_offres_total,
            SUM(nb_offres_avec_salaire) AS nb_avec_salaire,
            ROUND(SUM(nb_offres_avec_salaire) * 100.0 / NULLIF(SUM(nb_offres), 0), 1) AS pct_salaire_communique,
            ROUND(MEDIAN(salaire_median_mad), 0) AS salaire_median_mad,
            MIN(salaire_min_observe) AS salaire_plancher,
            MAX(salaire_max_observe) AS salaire_plafond
        FROM read_parquet('{GOLD_SALAIRES}')
        GROUP BY profil
        ORDER BY salaire_median_mad DESC NULLS LAST
    """).df()

    tanger_salaires = con.execute(f"""
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
                ROUND(MEDIAN(salaire_median_mad), 0) AS salaire_median_tanger,
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
            t.salaire_median_tanger,
            t.salaire_q1_mad,
            t.salaire_q3_mad,
            n.salaire_median_national,
            ROUND(t.salaire_median_tanger - n.salaire_median_national, 0) AS ecart_vs_national
        FROM tanger t
        LEFT JOIN national n
            ON t.profil = n.profil
        ORDER BY t.salaire_median_tanger DESC NULLS LAST
    """).df()

    contrats = con.execute(f"""
        SELECT
            type_contrat_std AS type_contrat,
            COUNT(*) AS nb_offres,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_offres
        FROM read_parquet('{SILVER_OFFRES}')
        GROUP BY type_contrat_std
        ORDER BY nb_offres DESC
    """).df()

    concurrents_tanger = con.execute(f"""
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
        ORDER BY salaire_moyen_propose DESC NULLS LAST
    """).df()

    corr = con.execute(f"""
        WITH base AS (
            SELECT
                profil_normalise AS profil,
                experience_min_ans,
                salaire_median_mad
            FROM read_parquet('{SILVER_OFFRES}')
            WHERE salaire_connu = TRUE
              AND experience_min_ans IS NOT NULL
              AND salaire_median_mad IS NOT NULL
        )
        SELECT
            profil,
            ROUND(CORR(experience_min_ans, salaire_median_mad), 3) AS correlation_pearson
        FROM base
        GROUP BY profil
        ORDER BY correlation_pearson DESC NULLS LAST
    """).df()

    kpis = con.execute(f"""
        SELECT
            COUNT(*) AS nb_offres,
            COUNT(DISTINCT entreprise) AS nb_entreprises,
            COUNT(DISTINCT ville_std) AS nb_villes,
            COUNT(*) FILTER (WHERE is_remote_or_hybrid = TRUE) AS nb_remote_hybrid,
            ROUND(COUNT(*) FILTER (WHERE is_remote_or_hybrid = TRUE) * 100.0 / COUNT(*), 1) AS pct_remote_hybrid,
            COUNT(*) FILTER (WHERE salaire_connu = TRUE) AS nb_salaires_connus
        FROM read_parquet('{SILVER_OFFRES}')
    """).df()

    con.close()

    return {
        "top_comp": top_comp,
        "villes": villes,
        "salaires_raw": salaires_raw,
        "tendances": tendances,
        "salaires_nat": salaires_nat,
        "tanger_salaires": tanger_salaires,
        "contrats": contrats,
        "concurrents_tanger": concurrents_tanger,
        "corr": corr,
        "kpis": kpis,
    }


def figure_carte_maroc_bubbles(villes: pd.DataFrame) -> Path:
    """
    Carte bubble du Maroc avec Plotly.
    - Suppression des lignes géopolitiques indésirables
    - Affichage du nom de la ville + nombre d'offres
    """
    coords = {
        "Casablanca": (-7.62, 33.59),
        "Rabat": (-6.84, 34.02),
        "Tanger": (-5.80, 35.76),
        "Tetouan": (-5.37, 35.57),
        "Marrakech": (-8.00, 31.63),
        "Fes": (-5.00, 34.03),
        "Meknes": (-5.55, 33.89),
        "Agadir": (-9.60, 30.42),
        "Oujda": (-1.91, 34.68),
        "Kenitra": (-6.57, 34.26),
        "Mohammedia": (-7.38, 33.69),
        "El_Jadida": (-8.50, 33.23),
    }

    df = villes.copy()
    df["lon"] = df["ville"].map(lambda v: coords.get(v, (None, None))[0])
    df["lat"] = df["ville"].map(lambda v: coords.get(v, (None, None))[1])
    df = df.dropna(subset=["lon", "lat"])

    # Texte de l'offre au-dessus de chaque ville : nom de la ville + nombre d'offres
    df["label_affichage"] = df.apply(
        lambda row: f"{row['ville']}<br>{int(row['nb_offres'])}",
        axis=1
    )

    fig = px.scatter_geo(
        df,
        lat="lat",
        lon="lon",
        size="nb_offres",
        hover_name="ville",
        hover_data={"nb_offres": True, "lat": False, "lon": False},
        text="label_affichage",
        projection="mercator",
        size_max=45
    )

    fig.update_traces(
        marker=dict(
            color=THEME["violet"],
            line=dict(color=THEME["violet_dark"], width=1.5),
            opacity=0.78
        ),
        textposition="top center",
        textfont=dict(
            size=12,
            color=THEME["ink"]
        ),
        hovertemplate="<b>%{hovertext}</b><br>Nombre d’offres: %{customdata[0]}<extra></extra>"
    )

    fig.update_geos(
        scope="africa",
        showland=True,
        landcolor="#F3E5F5",
        showocean=True,
        oceancolor="#FFFFFF",
        showlakes=False,
        showrivers=False,

        showcountries=False,
        showsubunits=False,

        showcoastlines=True,
        coastlinecolor=THEME["violet_dark"],
        coastlinewidth=1.2,

        showframe=False,
        bgcolor="#FFF7FB",

        lataxis_range=[27.5, 36.5],
        lonaxis_range=[-11.5, -0.5],
        projection_type="mercator"
    )

    fig.update_layout(
        title=dict(
            text="Carte du Maroc — volume d’offres IT par ville",
            x=0.5,
            font=dict(size=22, color=THEME["violet_dark"])
        ),
        paper_bgcolor="#FFF7FB",
        plot_bgcolor="#FFF7FB",
        margin=dict(l=20, r=20, t=70, b=20),
        font=dict(color=THEME["ink"], size=12)
    )

    path = FIGURES_DIR / "carte_maroc_bubbles.png"
    fig.write_image(str(path), width=1000, height=800)
    return path

def figure_top15_competences(top_comp: pd.DataFrame) -> Path:
    df = top_comp.sort_values("nb_offres_mentionnent", ascending=True)

    plt.figure(figsize=(10, 7))
    colors = [THEME["rose_dark"] if i >= len(df) - 5 else THEME["violet"] for i in range(len(df))]
    plt.barh(df["competence"], df["nb_offres_mentionnent"], color=colors)
    plt.title("Top 15 compétences IT les plus demandées", fontsize=15, color=THEME["violet_dark"], weight="bold")
    plt.xlabel("Nombre d’offres")
    plt.ylabel("Compétence")
    plt.grid(axis="x", alpha=0.25, color=THEME["grid"])

    path = FIGURES_DIR / "top15_competences.png"
    savefig(path)
    return path


def figure_boxplot_salaires(salaires_raw: pd.DataFrame) -> Path:
    profils_order = (
        salaires_raw.groupby("profil")["salaire_median_mad"]
        .median()
        .sort_values(ascending=False)
        .index
        .tolist()
    )

    data = [
        salaires_raw[salaires_raw["profil"] == profil]["salaire_median_mad"].dropna().values
        for profil in profils_order
    ]

    plt.figure(figsize=(12, 7))
    box = plt.boxplot(
        data,
        tick_labels=profils_order,
        patch_artist=True,
        vert=True,
        showfliers=False
    )

    for patch in box["boxes"]:
        patch.set_facecolor(THEME["lavender"])
        patch.set_edgecolor(THEME["violet_dark"])

    for median in box["medians"]:
        median.set_color(THEME["rose_dark"])
        median.set_linewidth(2)

    plt.title("Distribution des salaires par profil IT", fontsize=15, color=THEME["violet_dark"], weight="bold")
    plt.ylabel("Salaire mensuel brut MAD")
    plt.xticks(rotation=35, ha="right")
    plt.grid(axis="y", alpha=0.25, color=THEME["grid"])

    path = FIGURES_DIR / "boxplot_salaires_profils.png"
    savefig(path)
    return path


def figure_evolution_mensuelle(tendances: pd.DataFrame) -> Path:
    df = tendances.copy()
    df["date"] = pd.to_datetime(df["annee"].astype(str) + "-" + df["mois"].astype(str) + "-01")

    pivot = df.pivot_table(
        index="date",
        columns="profil",
        values="nb_offres",
        aggfunc="sum"
    ).fillna(0)

    plt.figure(figsize=(12, 6))

    colors = {
        "Data Engineer": THEME["violet_dark"],
        "Data Analyst": THEME["rose_dark"],
        "Data Scientist": "#8E44AD",
    }

    for col in pivot.columns:
        plt.plot(
            pivot.index,
            pivot[col],
            marker="o",
            linewidth=2.2,
            label=col,
            color=colors.get(col, None)
        )

    plt.title("Évolution mensuelle des offres Data — Janvier 2023 à Novembre 2024", fontsize=15, color=THEME["violet_dark"], weight="bold")
    plt.xlabel("Mois")
    plt.ylabel("Nombre d’offres")
    plt.legend()
    plt.grid(True, alpha=0.25, color=THEME["grid"])

    path = FIGURES_DIR / "evolution_mensuelle_data.png"
    savefig(path)
    return path


def figure_dashboard_synthese(dfs: dict, paths: dict) -> Path:
    kpi = dfs["kpis"].iloc[0]

    top_comp = dfs["top_comp"].head(8).sort_values("nb_offres_mentionnent", ascending=True)
    villes = dfs["villes"].head(6)
    tendances = dfs["tendances"].copy()
    tendances["date"] = pd.to_datetime(tendances["annee"].astype(str) + "-" + tendances["mois"].astype(str) + "-01")
    pivot = tendances.pivot_table(index="date", columns="profil", values="nb_offres", aggfunc="sum").fillna(0)

    fig = plt.figure(figsize=(16, 10), facecolor="#FFF7FB")
    gs = fig.add_gridspec(3, 4, height_ratios=[0.75, 2.1, 2.2], hspace=0.55, wspace=0.55)

    fig.suptitle(
        "Dashboard de Synthèse — Marché de l’Emploi IT au Maroc",
        fontsize=21,
        weight="bold",
        color=THEME["violet_dark"],
        y=0.98,
    )

    kpis = [
        ("Offres analysées", f"{int(kpi['nb_offres']):,}".replace(",", " ")),
        ("Entreprises", f"{int(kpi['nb_entreprises'])}"),
        ("Villes couvertes", f"{int(kpi['nb_villes'])}"),
        ("Remote / hybride", f"{kpi['pct_remote_hybrid']}%"),
    ]

    for i, (label, value) in enumerate(kpis):
        ax = fig.add_subplot(gs[0, i])
        ax.axis("off")
        card = patches.FancyBboxPatch(
            (0.02, 0.08),
            0.96,
            0.82,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            linewidth=1.2,
            edgecolor=THEME["violet"],
            facecolor=THEME["white"],
        )
        ax.add_patch(card)
        ax.text(0.08, 0.62, value, fontsize=22, weight="bold", color=THEME["rose_dark"], transform=ax.transAxes)
        ax.text(0.08, 0.32, label, fontsize=10.5, color=THEME["muted"], transform=ax.transAxes)

    ax1 = fig.add_subplot(gs[1, :2])
    ax1.barh(top_comp["competence"], top_comp["nb_offres_mentionnent"], color=THEME["violet"])
    ax1.set_title("Top compétences", color=THEME["violet_dark"], weight="bold")
    ax1.grid(axis="x", alpha=0.2)

    ax2 = fig.add_subplot(gs[1, 2:])
    ax2.bar(villes["ville"], villes["nb_offres"], color=THEME["rose"])
    ax2.set_title("Offres par ville", color=THEME["violet_dark"], weight="bold")
    ax2.tick_params(axis="x", rotation=30)
    ax2.grid(axis="y", alpha=0.2)

    ax3 = fig.add_subplot(gs[2, :])
    for col in pivot.columns:
        ax3.plot(pivot.index, pivot[col], marker="o", linewidth=2.2, label=col)
    ax3.set_title("Tendance mensuelle — profils Data", color=THEME["violet_dark"], weight="bold")
    ax3.legend()
    ax3.grid(True, alpha=0.2)

    path = FIGURES_DIR / "dashboard_synthese.png"
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def write_dashboard_html(paths: dict, dfs: dict) -> Path:
    kpi = dfs["kpis"].iloc[0]

    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Dashboard Mexora RH Intelligence</title>
<style>
body {{
    margin: 0;
    font-family: "Segoe UI", Arial, sans-serif;
    background: linear-gradient(135deg, #FFF7FB, #F3E5F5);
    color: #2D2433;
}}
.container {{
    max-width: 1180px;
    margin: 32px auto;
    padding: 24px;
}}
.header {{
    background: linear-gradient(135deg, #F8BBD0, #CE93D8);
    color: white;
    padding: 28px 34px;
    border-radius: 24px;
    box-shadow: 0 14px 35px rgba(106, 27, 154, 0.18);
}}
.header h1 {{
    margin: 0;
    font-size: 32px;
}}
.header p {{
    margin: 8px 0 0;
    font-size: 16px;
    opacity: 0.95;
}}
.kpis {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 18px;
    margin: 26px 0;
}}
.card {{
    background: white;
    border-radius: 20px;
    padding: 22px;
    box-shadow: 0 10px 24px rgba(106, 27, 154, 0.10);
    border: 1px solid #F3D7EE;
}}
.kpi-value {{
    color: #D81B60;
    font-weight: 800;
    font-size: 28px;
}}
.kpi-label {{
    color: #6C5A72;
    margin-top: 6px;
}}
.grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 22px;
}}
.figure {{
    background: white;
    border-radius: 22px;
    padding: 18px;
    box-shadow: 0 12px 28px rgba(106, 27, 154, 0.10);
    border: 1px solid #F3D7EE;
}}
.figure img {{
    width: 100%;
    border-radius: 16px;
}}
.full {{
    grid-column: span 2;
}}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>Dashboard de Synthèse — Marché de l’Emploi IT au Maroc</h1>
        <p>Mexora RH Intelligence — analyse décisionnelle pour la stratégie de recrutement</p>
    </div>

    <div class="kpis">
        <div class="card"><div class="kpi-value">{int(kpi['nb_offres'])}</div><div class="kpi-label">Offres analysées</div></div>
        <div class="card"><div class="kpi-value">{int(kpi['nb_entreprises'])}</div><div class="kpi-label">Entreprises recruteuses</div></div>
        <div class="card"><div class="kpi-value">{int(kpi['nb_villes'])}</div><div class="kpi-label">Villes couvertes</div></div>
        <div class="card"><div class="kpi-value">{kpi['pct_remote_hybrid']}%</div><div class="kpi-label">Remote ou hybride</div></div>
    </div>

    <div class="grid">
        <div class="figure"><img src="figures/carte_maroc_bubbles.png"></div>
        <div class="figure"><img src="figures/top15_competences.png"></div>
        <div class="figure"><img src="figures/boxplot_salaires_profils.png"></div>
        <div class="figure"><img src="figures/evolution_mensuelle_data.png"></div>
        <div class="figure full"><img src="figures/dashboard_synthese.png"></div>
    </div>
</div>
</body>
</html>
"""
    path = OUTPUT_DIR / "dashboard_synthese.html"
    path.write_text(html, encoding="utf-8")
    return path


def format_markdown_table(df: pd.DataFrame, max_rows: int = 10) -> str:
    df = df.head(max_rows).copy().fillna("")
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(row[c]).replace("\n", " ") for c in cols) + " |")
    return "\n".join([header, sep] + rows)


def write_report_md(dfs: dict, paths: dict) -> Path:
    kpi = dfs["kpis"].iloc[0]
    top_comp = dfs["top_comp"]
    villes = dfs["villes"]
    salaires_nat = dfs["salaires_nat"]
    tanger_salaires = dfs["tanger_salaires"]
    contrats = dfs["contrats"]
    concurrents = dfs["concurrents_tanger"]
    corr = dfs["corr"]

    top_comp_10 = top_comp.head(10)
    top_villes = villes.head(5)
    data_profiles = salaires_nat[salaires_nat["profil"].isin(["Data Engineer", "Data Analyst", "Data Scientist"])]

    data_engineer_tanger = tanger_salaires[tanger_salaires["profil"] == "Data Engineer"]
    if not data_engineer_tanger.empty:
        salaire_de_tanger = int(data_engineer_tanger.iloc[0]["salaire_median_tanger"])
        q1_de = int(data_engineer_tanger.iloc[0]["salaire_q1_mad"])
        q3_de = int(data_engineer_tanger.iloc[0]["salaire_q3_mad"])
    else:
        salaire_de_tanger = None
        q1_de = None
        q3_de = None

    top_skill = top_comp.iloc[0]
    top_city = villes.iloc[0]

    content = f"""
# RAPPORT : Analyse du Marché de l’Emploi IT au Maroc  
## Mexora RH Intelligence — Novembre 2024

---

## 1. Résumé exécutif

Mexora prépare le recrutement de nouveaux profils data dans un contexte où le marché marocain de l’emploi IT est fortement concentré autour de quelques pôles urbains et de compétences techniques clés. L’analyse réalisée sur **{int(kpi['nb_offres'])} offres d’emploi IT** met en évidence une forte demande pour les compétences liées aux méthodes projet, aux bases de données, au cloud, au développement et à la data.

### 5 chiffres clés

| Indicateur | Valeur |
|---|---:|
| Offres analysées | {int(kpi['nb_offres'])} |
| Entreprises recruteuses | {int(kpi['nb_entreprises'])} |
| Villes couvertes | {int(kpi['nb_villes'])} |
| Offres remote ou hybrides | {kpi['pct_remote_hybrid']}% |
| Salaires exploitables | {int(kpi['nb_salaires_connus'])} offres |

La compétence la plus visible dans les offres est **{top_skill['competence']}**, mentionnée dans **{top_skill['pct_offres_total']}%** des offres. La ville la plus active est **{top_city['ville']}**, avec **{int(top_city['nb_offres'])} offres**.

### 3 recommandations prioritaires

1. **Prioriser le recrutement de Data Engineer et Data Analyst**, car ce sont les profils les plus directement alignés avec les besoins analytiques de Mexora.
2. **Positionner les salaires de Tanger au niveau du marché national**, voire légèrement au-dessus pour les profils rares.
3. **Adopter une stratégie de recrutement hybride**, combinant bassin local de Tanger et sourcing Casablanca/Rabat en remote.

### Horizon de mise en œuvre

| Horizon | Action |
|---|---|
| 0-1 mois | Finaliser les fiches de poste et fourchettes salariales |
| 1-3 mois | Lancer les recrutements Data Engineer et Data Analyst |
| 3-6 mois | Recruter le Data Scientist et renforcer la formation interne |

---

## 2. Méthodologie

L’analyse repose sur un Data Lake local construit en trois zones : Bronze, Silver et Gold. Les données sources simulent des offres d’emploi IT marocaines publiées entre **janvier 2023 et novembre 2024** sur trois sources : Rekrute, MarocAnnonce et LinkedIn Maroc.

### Sources et période

| Élément | Description |
|---|---|
| Sources | Rekrute, MarocAnnonce, LinkedIn Maroc |
| Période | Janvier 2023 à novembre 2024 |
| Volume | 5 000 offres |
| Données | Offres IT marocaines structurées et semi-structurées |

### Architecture utilisée

- **Bronze** : conservation des offres brutes au format JSON.
- **Silver** : nettoyage, normalisation et typage des données au format Parquet.
- **Gold** : tables analytiques prêtes pour DuckDB, dashboard et rapport.

### Limites et biais identifiés

Les données utilisées sont synthétiques mais construites pour reproduire des problèmes réalistes de scraping : salaires non communiqués, intitulés de poste hétérogènes, villes non standardisées, texte libre dans les descriptions et dates parfois incohérentes. Les résultats doivent donc être lus comme une **aide à la décision** et non comme une mesure officielle exhaustive du marché.

---

## 3. État du marché IT au Maroc

### Répartition géographique des opportunités

{format_markdown_table(top_villes[["ville", "nb_offres", "pct_remote_hybrid"]], 10)}

![Carte du Maroc — volume d’offres IT par ville](figures/carte_maroc_bubbles.png)

Le marché IT est fortement concentré autour de **Casablanca**, suivie par **Rabat** et **Tanger**. Pour Mexora, basée à Tanger, cela signifie que le bassin local existe mais reste plus limité que les grands pôles nationaux. Le recours au recrutement hybride peut donc devenir un levier stratégique.

### Types de contrats dominants

{format_markdown_table(contrats, 10)}

Les contrats CDI restent structurants dans le marché IT, mais la présence de formats freelance, CDD, stage ou contrat projet montre que les entreprises adaptent leurs besoins selon la rareté des profils et la nature des projets.

### Tendance des profils data

![Évolution mensuelle des offres Data](figures/evolution_mensuelle_data.png)

Les profils Data Engineer, Data Analyst et Data Scientist présentent une demande continue sur la période étudiée. Cette stabilité confirme que le besoin de compétences data n’est pas ponctuel mais structurel.

---

## 4. Compétences les plus demandées

### Top 10 compétences toutes offres confondues

{format_markdown_table(top_comp_10[["famille", "competence", "nb_offres_mentionnent", "pct_offres_total"]], 10)}

![Top 15 compétences IT](figures/top15_competences.png)

Les compétences les plus demandées combinent trois familles : méthodologies de travail, langages et cloud/data engineering. La présence de **SQL**, **Docker**, **Python**, **AWS** et **PostgreSQL** indique que le marché valorise les profils capables de manipuler la donnée, industrialiser les traitements et travailler dans des environnements modernes.

Pour Mexora, les fiches de poste doivent donc clairement intégrer : Python, SQL, Docker, cloud, orchestration data et outils BI. Les compétences transversales comme Git, Agile et DevOps doivent être considérées comme des prérequis opérationnels.

---

## 5. Analyse salariale

### Salaires médians par profil

{format_markdown_table(salaires_nat[["profil", "nb_offres_total", "nb_avec_salaire", "salaire_median_mad", "salaire_plancher", "salaire_plafond"]], 12)}

![Distribution des salaires par profil](figures/boxplot_salaires_profils.png)

Les salaires les plus élevés concernent généralement les profils à forte expertise technique : architecture, cloud, DevOps, data engineering et data science. Les écarts sont également influencés par l’expérience, la ville, le type de contrat et la rareté des compétences.

### Focus Tanger

{format_markdown_table(tanger_salaires[["profil", "nb_offres", "salaire_median_tanger", "salaire_q1_mad", "salaire_q3_mad", "salaire_median_national", "ecart_vs_national"]], 12)}

Pour un **Data Engineer à Tanger**, la médiane observée est de **{salaire_de_tanger if salaire_de_tanger else "N/A"} MAD** avec une fourchette interquartile approximative entre **{q1_de if q1_de else "N/A"} MAD** et **{q3_de if q3_de else "N/A"} MAD**. Cette information doit servir de base aux packages salariaux de Mexora.

### Expérience et salaire

{format_markdown_table(corr.head(10), 10)}

La corrélation entre expérience et salaire varie selon les profils. Lorsque la corrélation est élevée, l’expérience explique une part importante du niveau salarial. Lorsque la corrélation est plus faible, d’autres facteurs entrent en jeu : rareté technologique, entreprise recruteuse, ville, cloud, data engineering ou responsabilité projet.

---

## 6. Recommandations pour Mexora

### Profils prioritaires

| Priorité | Profil | Justification |
|---|---|---|
| 1 | Data Engineer | Profil essentiel pour structurer les pipelines, le Data Lake et les flux analytiques |
| 2 | Data Analyst | Profil nécessaire pour produire les analyses métier et accompagner les décisions RH/commerciales |
| 3 | Data Scientist | Profil à recruter après stabilisation des données et des besoins analytiques avancés |

### Fourchettes salariales recommandées

| Profil | Recommandation salariale mensuelle brute |
|---|---:|
| Data Engineer | Se positionner autour de la médiane Tanger, avec marge haute pour profils Spark/Airflow/Cloud |
| Data Analyst | Se positionner au niveau médian national si compétences BI avancées |
| Data Scientist | Prévoir une fourchette supérieure pour profils ML/NLP expérimentés |

### Concurrents directs à Tanger

{format_markdown_table(concurrents[["entreprise", "nb_offres_publiees", "salaire_moyen_propose", "niveau_competition"]], 10)}

Les concurrents directs sont les entreprises de Tanger recrutant des profils Data Engineer, Data Analyst ou Data Scientist. Les compétiteurs forts doivent être surveillés en priorité, car ils peuvent attirer les mêmes candidats que Mexora.

### Recommandations opérationnelles

1. **Recruter d’abord un Data Engineer senior ou confirmé**, afin de renforcer la base technique du système analytique.
2. **Recruter ensuite un Data Analyst orienté BI**, capable de transformer les données Gold en tableaux de bord utiles aux métiers.
3. **Ouvrir les postes au mode hybride**, pour attirer des talents de Casablanca et Rabat sans limiter le recrutement au bassin local.
4. **Former en interne sur les compétences rares**, notamment orchestration data, cloud, Docker, SQL avancé et BI.
5. **Mettre en avant les projets à forte valeur**, car l’attractivité ne dépend pas uniquement du salaire mais aussi de la qualité des missions.

---

## Conclusion

Le marché IT marocain présente une forte demande pour les profils data, avec une concentration géographique autour de Casablanca et Rabat, mais une présence significative de Tanger. Pour Mexora, la stratégie recommandée consiste à combiner recrutement local, ouverture au remote/hybride, positionnement salarial compétitif et formation interne sur les compétences rares.
"""

    path = OUTPUT_DIR / "rapport_analytique_mexora.md"
    path.write_text(textwrap.dedent(content).strip(), encoding="utf-8")
    return path


def main() -> None:
    verifier_fichiers()
    dfs = get_dataframes()

    paths = {}
    paths["carte"] = figure_carte_maroc_bubbles(dfs["villes"])
    paths["top15"] = figure_top15_competences(dfs["top_comp"])
    paths["boxplot"] = figure_boxplot_salaires(dfs["salaires_raw"])
    paths["evolution"] = figure_evolution_mensuelle(dfs["tendances"])
    paths["dashboard"] = figure_dashboard_synthese(dfs, paths)

    html_path = write_dashboard_html(paths, dfs)
    report_path = write_report_md(dfs, paths)

    print("[ETAPE 4] Dashboard et rapport générés avec succès.")
    print(f"[ETAPE 4] Figures : {FIGURES_DIR}")
    print(f"[ETAPE 4] Dashboard HTML : {html_path}")
    print(f"[ETAPE 4] Rapport Markdown : {report_path}")


if __name__ == "__main__":
    main()