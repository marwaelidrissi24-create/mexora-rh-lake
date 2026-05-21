"""
Script : silver_transform.py
Projet : Mexora RH Intelligence

Objectif :
Lire les données Bronze, nettoyer et standardiser les offres d'emploi IT,
puis sauvegarder la zone Silver au format Parquet.

Transformations principales :
- Chargement consolidé depuis Bronze
- Normalisation des dates
- Normalisation des villes
- Normalisation des contrats
- Normalisation des intitulés de poste
- Normalisation des salaires
- Normalisation de l'expérience
- Contrôles qualité
- Sauvegarde Silver en Parquet consolidé et partitionné par ville/mois
"""

import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.utils import ensure_directory, log_step, print_quality_indicator


def charger_depuis_bronze(data_lake_root: str | Path) -> pd.DataFrame:
    """
    Charge et consolide toutes les offres depuis la zone Bronze.

    Règle métier :
    La zone Bronze contient des fichiers JSON partitionnés par source/mois.
    On lit tous les fichiers offres_raw.json et on reconstruit un DataFrame unique.
    """
    data_lake_root = Path(data_lake_root)
    bronze_path = data_lake_root / "bronze"

    all_offres: list[dict] = []
    files = list(bronze_path.rglob("offres_raw.json"))

    if not files:
        raise FileNotFoundError(
            "Aucun fichier offres_raw.json trouvé en Bronze. "
            "Exécuter d'abord pipeline/bronze_ingestion.py."
        )

    for json_file in files:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        offres = data.get("offres", [])
        if isinstance(offres, list):
            all_offres.extend(offres)

    df = pd.DataFrame(all_offres)
    print(f"[SILVER] {len(df)} offres chargées depuis {len(files)} fichiers Bronze")
    return df


def normaliser_dates(df: pd.DataFrame, report_path: str | Path) -> pd.DataFrame:
    """
    Standardise les dates de publication et d'expiration.

    Problème traité :
    date_publication contient plusieurs formats :
    - YYYY-MM-DD
    - DD/MM/YYYY
    - Mon DD YYYY

    Règle métier :
    On conserve la colonne originale et on crée des colonnes typées :
    - date_publication_dt
    - date_expiration_dt
    - annee
    - mois
    - mois_partition
    - date_incoherente

    Correction importante :
    On parse explicitement les formats au lieu d'utiliser un parsing automatique
    ambigu, afin d'éviter les inversions mois/jour.
    """
    rows_before = len(df)

    def parse_date_safe(value: Any):
        if pd.isna(value):
            return pd.NaT

        raw = str(value).strip()

        if raw == "" or raw.lower() in ["null", "none", "nan"]:
            return pd.NaT

        formats = [
            "%Y-%m-%d",   # 2024-08-15
            "%d/%m/%Y",   # 15/08/2024
            "%b %d %Y",   # Aug 15 2024
            "%B %d %Y",   # August 15 2024
        ]

        for fmt in formats:
            try:
                return pd.Timestamp(datetime.strptime(raw, fmt))
            except ValueError:
                continue

        return pd.NaT

    df["date_publication_originale"] = df["date_publication"]
    df["date_expiration_originale"] = df["date_expiration"]

    df["date_publication_dt"] = df["date_publication"].apply(parse_date_safe)
    df["date_expiration_dt"] = df["date_expiration"].apply(parse_date_safe)

    df["date_incoherente"] = (
        df["date_publication_dt"].notna()
        & df["date_expiration_dt"].notna()
        & (df["date_publication_dt"] > df["date_expiration_dt"])
    )

    df["annee"] = df["date_publication_dt"].dt.year.astype("Int64")
    df["mois"] = df["date_publication_dt"].dt.month.astype("Int64")
    df["mois_partition"] = df["date_publication_dt"].dt.strftime("%Y_%m")
    df["mois_partition"] = df["mois_partition"].fillna("date_inconnue")

    invalid_dates = int(df["date_publication_dt"].isna().sum())
    incoherent_dates = int(df["date_incoherente"].sum())

    log_step(
        report_path=report_path,
        step_name="Normalisation des dates",
        rule="Parsing explicite des formats de dates vers datetime, conservation des valeurs originales et détection publication > expiration.",
        rows_before=rows_before,
        rows_after=len(df),
        details=f"Dates publication invalides: {invalid_dates}. Dates incohérentes publication > expiration: {incoherent_dates}."
    )

    print(f"[SILVER] Dates normalisées. Invalides: {invalid_dates}, incohérentes: {incoherent_dates}")
    return df

def normaliser_villes(df: pd.DataFrame, report_path: str | Path) -> pd.DataFrame:
    """
    Standardise les villes marocaines.

    Problème traité :
    ville contient des variantes comme casa, CASABLANCA, Cblanca, TNG, Tanja.

    Règle métier :
    On crée une colonne ville_std normalisée et une colonne region_admin.
    """
    rows_before = len(df)

    mapping_villes = {
        "casablanca": "Casablanca",
        "casa": "Casablanca",
        "cblanca": "Casablanca",
        "rabat": "Rabat",
        "rbat": "Rabat",
        "rabatt": "Rabat",
        "tanger": "Tanger",
        "tanja": "Tanger",
        "tng": "Tanger",
        "tetouan": "Tetouan",
        "tétouan": "Tetouan",
        "marrakech": "Marrakech",
        "marrakesh": "Marrakech",
        "fes": "Fes",
        "fès": "Fes",
        "fez": "Fes",
        "agadir": "Agadir",
        "oujda": "Oujda",
        "kenitra": "Kenitra",
        "kénitra": "Kenitra",
        "meknes": "Meknes",
        "meknès": "Meknes",
        "mohammedia": "Mohammedia",
        "el jadida": "El_Jadida",
        "el_jadida": "El_Jadida",
        "eljadida": "El_Jadida",
    }

    region_mapping = {
        "Casablanca": "Casablanca-Settat",
        "Mohammedia": "Casablanca-Settat",
        "El_Jadida": "Casablanca-Settat",
        "Rabat": "Rabat-Salé-Kénitra",
        "Kenitra": "Rabat-Salé-Kénitra",
        "Tanger": "Tanger-Tétouan-Al Hoceïma",
        "Tetouan": "Tanger-Tétouan-Al Hoceïma",
        "Marrakech": "Marrakech-Safi",
        "Fes": "Fès-Meknès",
        "Meknes": "Fès-Meknès",
        "Agadir": "Souss-Massa",
        "Oujda": "Oriental",
    }

    ville_norm = (
        df["ville"]
        .fillna("Non renseignée")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df["ville_std"] = ville_norm.map(mapping_villes)
    df["ville_std"] = df["ville_std"].fillna("Non renseignée")
    df["region_admin"] = df["ville_std"].map(region_mapping).fillna("Non renseignée")

    unknown = int((df["ville_std"] == "Non renseignée").sum())

    log_step(
        report_path=report_path,
        step_name="Normalisation des villes",
        rule="Mapping des variantes de villes vers une valeur standardisée dans ville_std et rattachement à une région administrative.",
        rows_before=rows_before,
        rows_after=len(df),
        details=f"Villes non reconnues ou non renseignées: {unknown}."
    )

    print(f"[SILVER] Villes normalisées. Non reconnues: {unknown}")
    return df


def normaliser_contrats(df: pd.DataFrame, report_path: str | Path) -> pd.DataFrame:
    """
    Standardise le type de contrat.

    Problème traité :
    CDI, cdi, Contrat à durée indéterminée, Permanent doivent être harmonisés.
    """
    rows_before = len(df)

    def parse_contract(value: Any) -> str:
        if pd.isna(value):
            return "Non renseigné"

        s = str(value).strip().lower()

        if s in ["cdi", "contrat à durée indéterminée", "permanent"]:
            return "CDI"
        if s in ["cdd", "contrat à durée déterminée"]:
            return "CDD"
        if "freelance" in s or "indépendant" in s:
            return "Freelance"
        if "stage" in s or "stagiaire" in s:
            return "Stage"
        if "projet" in s:
            return "Contrat projet"

        return "Autre"

    df["type_contrat_original"] = df["type_contrat"]
    df["type_contrat_std"] = df["type_contrat"].apply(parse_contract)

    log_step(
        report_path=report_path,
        step_name="Normalisation des contrats",
        rule="Regroupement des variantes de contrat vers CDI, CDD, Freelance, Stage, Contrat projet, Autre ou Non renseigné.",
        rows_before=rows_before,
        rows_after=len(df),
        details=f"Distribution contrats: {df['type_contrat_std'].value_counts().to_dict()}"
    )

    print("[SILVER] Contrats normalisés")
    return df


def nettoyer_titres_postes(df: pd.DataFrame, report_path: str | Path) -> pd.DataFrame:
    """
    Standardise les intitulés de poste en familles de profils IT.

    Problème traité :
    Dev Data, Ingénieur Big Data, Data Eng., Développeur BI, etc.

    Règle métier :
    Un titre est normalisé vers le profil IT le plus proche.
    """
    rows_before = len(df)

    mapping_profils = {
        # Data Engineering
        r"data\s*eng(ineer|\.?)|ing[eé]nieur\s+(big\s*)?data|dev\s+data|etl\s*developer|pipeline": "Data Engineer",
        r"etl|data\s*pipeline|big\s*data": "Data Engineer",

        # Data Analysis / BI
        r"data\s*analyst|analyste\s*data|bi\s*analyst|business\s*intelligence|d[eé]veloppeur\s*bi|power\s*bi": "Data Analyst",
        r"reporting|consultant\s*bi": "Data Analyst",

        # Data Science / IA
        r"data\s*scientist|machine\s*learning|ing[eé]nieur\s*ia|nlp|data\s*science": "Data Scientist",

        # Software Engineering
        r"full\s*stack|fullstack|mern": "Développeur Full Stack",
        r"backend|back\s*end|api": "Développeur Backend",
        r"frontend|front\s*end|react|angular": "Développeur Frontend",

        # Infrastructure
        r"devops|sre|site\s*reliability": "DevOps / SRE",
        r"cloud|aws|azure|gcp": "Cloud Engineer",

        # Cybersecurity
        r"cyber|s[eé]curit[eé]|soc|pentester": "Cybersécurité",

        # Management / Architecture
        r"chef\s*de\s*projet|scrum\s*master|project\s*manager": "Chef de Projet IT",
        r"architecte": "Architecte IT",
    }

    df["titre_original"] = df["titre_poste"]
    df["profil_source"] = df["titre_poste"].fillna("").astype(str).str.lower().str.strip()
    df["profil_normalise"] = "Autre IT"

    for pattern, profil in mapping_profils.items():
        mask = df["profil_source"].str.contains(pattern, regex=True, na=False)
        df.loc[mask, "profil_normalise"] = profil

    non_classes = int((df["profil_normalise"] == "Autre IT").sum())

    log_step(
        report_path=report_path,
        step_name="Normalisation des intitulés de poste",
        rule="Classification regex des intitulés non standardisés vers des profils IT normalisés.",
        rows_before=rows_before,
        rows_after=len(df),
        details=f"Offres classées Autre IT: {non_classes}. Distribution profils: {df['profil_normalise'].value_counts().to_dict()}"
    )

    print(f"[SILVER] Titres normalisés. Autre IT: {non_classes}")
    return df


def normaliser_salaires(df: pd.DataFrame, report_path: str | Path) -> pd.DataFrame:
    """
    Extrait et normalise les salaires en MAD mensuel brut.

    Problèmes traités :
    - 15000-20000 MAD
    - 15K-20K
    - Selon profil
    - Confidentiel
    - EUR à convertir en MAD

    Règles :
    - Fourchette -> salaire_min_mad, salaire_max_mad
    - Médiane -> salaire_median_mad
    - EUR -> conversion avec taux fixe 1 EUR = 10.8 MAD
    - salaire non exploitable -> salaire_connu = False
    """
    rows_before = len(df)
    taux_eur_mad = 10.8

    def parser_salaire(value: Any) -> tuple[float | None, float | None, bool]:
        if pd.isna(value):
            return None, None, False

        raw = str(value).strip().lower()

        if raw in ["", "null", "none", "selon profil", "confidentiel"]:
            return None, None, False

        s = raw.replace(" ", "").replace("\u202f", "")

        est_eur = "eur" in s or "€" in s
        s = (
            s.replace("eur", "")
            .replace("€", "")
            .replace("mad", "")
            .replace("dh", "")
            .replace("dhs", "")
        )

        s = re.sub(
            r"(\d+(?:\.\d+)?)k",
            lambda m: str(int(float(m.group(1)) * 1000)),
            s
        )

        numbers = re.findall(r"\d+(?:\.\d+)?", s)

        if not numbers:
            return None, None, False

        amounts = [float(n) for n in numbers]

        if est_eur:
            amounts = [amount * taux_eur_mad for amount in amounts]

        if len(amounts) >= 2:
            salaire_min = min(amounts[:2])
            salaire_max = max(amounts[:2])
        else:
            salaire_min = salaire_max = amounts[0]

        if salaire_min < 3000 or salaire_max > 100000 or salaire_min > salaire_max:
            return None, None, False

        return round(salaire_min, 2), round(salaire_max, 2), True

    parsed = df["salaire_brut"].apply(
        lambda x: pd.Series(
            parser_salaire(x),
            index=["salaire_min_mad", "salaire_max_mad", "salaire_connu"]
        )
    )

    df = pd.concat([df, parsed], axis=1)
    df["salaire_median_mad"] = (
        df["salaire_min_mad"] + df["salaire_max_mad"]
    ) / 2

    known_count = int(df["salaire_connu"].sum())
    pct_known = round(known_count * 100 / len(df), 2)

    log_step(
        report_path=report_path,
        step_name="Normalisation des salaires",
        rule="Extraction des montants, conversion K et EUR, calcul min/max/médiane, flag salaire_connu.",
        rows_before=rows_before,
        rows_after=len(df),
        details=f"Salaires connus et valides: {known_count}/{len(df)} ({pct_known}%). Taux EUR/MAD utilisé: {taux_eur_mad}."
    )

    print(f"[SILVER] Salaires normalisés. Connus: {known_count}/{len(df)} ({pct_known}%)")
    return df


def normaliser_experience(df: pd.DataFrame, report_path: str | Path) -> pd.DataFrame:
    """
    Transforme l'expérience requise en valeurs numériques.

    Exemples :
    - 3-5 ans -> min 3, max 5
    - min 3 ans -> min 3
    - Débutant accepté -> min 0, max 2
    - Senior (7+ ans) -> min 7
    """
    rows_before = len(df)

    def parser_experience(value: Any) -> tuple[int | None, int | None]:
        if pd.isna(value):
            return None, None

        s = str(value).strip().lower()

        if s in ["", "null", "none"]:
            return None, None

        if any(word in s for word in ["débutant", "debutant", "junior", "stage", "sans expérience"]):
            return 0, 2

        senior_match = re.search(r"(\d+)\s*\+", s)
        if senior_match:
            return int(senior_match.group(1)), None

        if any(word in s for word in ["senior", "confirmé", "confirme", "expert", "lead"]):
            return 5, None

        range_match = re.search(r"(\d+)\s*(?:-|à|a)\s*(\d+)", s)
        if range_match:
            return int(range_match.group(1)), int(range_match.group(2))

        min_match = re.search(r"(\d+)\s*(?:ans?|years?)", s)
        if min_match:
            return int(min_match.group(1)), None

        return None, None

    parsed = df["experience_requise"].apply(
        lambda x: pd.Series(
            parser_experience(x),
            index=["experience_min_ans", "experience_max_ans"]
        )
    )

    df = pd.concat([df, parsed], axis=1)

    known_exp = int(df["experience_min_ans"].notna().sum())
    pct_known = round(known_exp * 100 / len(df), 2)

    log_step(
        report_path=report_path,
        step_name="Normalisation de l'expérience",
        rule="Parsing regex des formats d'expérience vers experience_min_ans et experience_max_ans.",
        rows_before=rows_before,
        rows_after=len(df),
        details=f"Expériences interprétables: {known_exp}/{len(df)} ({pct_known}%)."
    )

    print(f"[SILVER] Expériences normalisées. Connues: {known_exp}/{len(df)} ({pct_known}%)")
    return df


def enrichir_champs_analytiques(df: pd.DataFrame, report_path: str | Path) -> pd.DataFrame:
    """
    Ajoute des champs utiles pour les analyses Gold et DuckDB.
    """
    rows_before = len(df)

    df["nb_postes"] = pd.to_numeric(df["nb_postes"], errors="coerce").fillna(1).astype(int)

    df["teletravail_std"] = (
        df["teletravail"]
        .fillna("Non renseigné")
        .astype(str)
        .str.strip()
    )

    df["is_remote_or_hybrid"] = (
        df["teletravail_std"].str.lower().str.contains("remote|hybride|télétravail|teletravail", regex=True)
    )

    df["source_std"] = (
        df["source"]
        .fillna("source_inconnue")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df["entreprise"] = df["entreprise"].fillna("Non renseignée").astype(str).str.strip()
    df["secteur"] = df["secteur"].fillna("Non renseigné").astype(str).str.strip()
    df["niveau_etudes"] = df["niveau_etudes"].fillna("Non renseigné").astype(str).str.strip()

    log_step(
        report_path=report_path,
        step_name="Enrichissement analytique Silver",
        rule="Création de champs standardisés utiles pour Gold : source_std, teletravail_std, is_remote_or_hybrid, nb_postes typé.",
        rows_before=rows_before,
        rows_after=len(df),
        details="Aucune suppression de lignes. Les champs analytiques sont ajoutés pour faciliter les agrégations Gold."
    )

    print("[SILVER] Champs analytiques ajoutés")
    return df


def controler_qualite_silver(df: pd.DataFrame, report_path: str | Path) -> pd.DataFrame:
    """
    Applique des contrôles qualité sans supprimer les lignes.

    Principe :
    Les anomalies sont tracées par des flags, afin de ne pas perdre
    d'information utile pour l'analyse.
    """
    rows_before = len(df)

    df["flag_ville_inconnue"] = df["ville_std"].eq("Non renseignée")
    df["flag_salaire_inconnu"] = ~df["salaire_connu"]
    df["flag_experience_inconnue"] = df["experience_min_ans"].isna()
    df["flag_date_publication_invalide"] = df["date_publication_dt"].isna()

    quality_summary = {
        "ville_inconnue": int(df["flag_ville_inconnue"].sum()),
        "salaire_inconnu": int(df["flag_salaire_inconnu"].sum()),
        "experience_inconnue": int(df["flag_experience_inconnue"].sum()),
        "date_publication_invalide": int(df["flag_date_publication_invalide"].sum()),
        "date_incoherente": int(df["date_incoherente"].sum()),
    }

    log_step(
        report_path=report_path,
        step_name="Contrôles qualité Silver",
        rule="Ajout de flags qualité au lieu de supprimer les lignes, pour préserver la traçabilité.",
        rows_before=rows_before,
        rows_after=len(df),
        details=f"Résumé qualité: {quality_summary}"
    )

    for key, value in quality_summary.items():
        print_quality_indicator(key, value)

    return df


def clean_previous_silver_outputs(data_lake_root: str | Path) -> None:
    """
    Nettoie les anciens fichiers Parquet Silver générés par le pipeline.
    Conserve les .gitkeep.
    """
    silver_root = Path(data_lake_root) / "silver" / "offres_clean"

    if not silver_root.exists():
        return

    for parquet_file in silver_root.rglob("*.parquet"):
        parquet_file.unlink()


def sauvegarder_silver(df: pd.DataFrame, data_lake_root: str | Path, report_path: str | Path) -> None:
    """
    Sauvegarde Silver en deux formes :
    1. Fichier consolidé : silver/offres_clean/offres_clean.parquet
    2. Fichiers partitionnés : silver/offres_clean/ville=.../mois=.../offres_clean.parquet

    Cette double sauvegarde respecte :
    - l'énoncé qui cite un fichier offres_clean.parquet ;
    - le principe de partitionnement Silver par ville et par mois.
    """
    rows_before = len(df)

    data_lake_root = Path(data_lake_root)
    silver_root = data_lake_root / "silver" / "offres_clean"
    ensure_directory(silver_root)

    clean_previous_silver_outputs(data_lake_root)

    consolidated_file = silver_root / "offres_clean.parquet"
    df.to_parquet(consolidated_file, index=False, compression="snappy")

    partition_count = 0

    for (ville, mois), group in df.groupby(["ville_std", "mois_partition"], dropna=False):
        safe_ville = str(ville).replace(" ", "_").replace("/", "_")
        safe_mois = str(mois)

        partition_dir = silver_root / f"ville={safe_ville}" / f"mois={safe_mois}"
        ensure_directory(partition_dir)

        output_file = partition_dir / "offres_clean.parquet"
        group.to_parquet(output_file, index=False, compression="snappy")
        partition_count += 1

    log_step(
        report_path=report_path,
        step_name="Sauvegarde Silver",
        rule="Sauvegarde des offres nettoyées en Parquet consolidé et en partitions ville/mois.",
        rows_before=rows_before,
        rows_after=len(df),
        details=f"Fichier consolidé: {consolidated_file}. Partitions Parquet créées: {partition_count}."
    )

    print(f"[SILVER] Fichier consolidé sauvegardé : {consolidated_file}")
    print(f"[SILVER] Partitions ville/mois créées : {partition_count}")


def construire_silver(data_lake_root: str | Path, report_path: str | Path) -> pd.DataFrame:
    """
    Pipeline complet Bronze -> Silver.
    """
    df = charger_depuis_bronze(data_lake_root)

    log_step(
        report_path=report_path,
        step_name="Chargement depuis Bronze",
        rule="Lecture de tous les fichiers offres_raw.json depuis la zone Bronze.",
        rows_before=None,
        rows_after=len(df),
        details="Consolidation des partitions Bronze dans un DataFrame pandas unique."
    )

    df = normaliser_dates(df, report_path)
    df = normaliser_villes(df, report_path)
    df = normaliser_contrats(df, report_path)
    df = nettoyer_titres_postes(df, report_path)
    df = normaliser_salaires(df, report_path)
    df = normaliser_experience(df, report_path)
    df = enrichir_champs_analytiques(df, report_path)
    df = controler_qualite_silver(df, report_path)

    sauvegarder_silver(df, data_lake_root, report_path)

    print("\n[SILVER] Construction Silver terminée avec succès")
    print(f"[SILVER] Nombre final d'offres : {len(df)}")

    return df


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    data_lake_root = project_root / "data_lake_mexora_rh"
    report_path = project_root / "docs" / "rapport_pipeline.md"

    construire_silver(
        data_lake_root=data_lake_root,
        report_path=report_path
    )


if __name__ == "__main__":
    main()