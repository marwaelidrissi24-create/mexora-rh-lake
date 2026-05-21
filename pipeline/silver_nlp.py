"""
Script : silver_nlp.py
Projet : Mexora RH Intelligence

Objectif :
Extraire les compétences IT depuis les offres nettoyées Silver.

Sources utilisées :
- competences_brut : champ semi-structuré
- description : texte libre

Méthode :
Matching regex basé sur le référentiel referentiel_competences_it.json.

Sortie :
data_lake_mexora_rh/silver/competences_extraites/competences.parquet
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.utils import ensure_directory, log_step


def charger_offres_silver(data_lake_root: str | Path) -> pd.DataFrame:
    """
    Charge le fichier Silver consolidé des offres nettoyées.
    """
    data_lake_root = Path(data_lake_root)
    silver_file = data_lake_root / "silver" / "offres_clean" / "offres_clean.parquet"

    if not silver_file.exists():
        raise FileNotFoundError(
            f"Fichier Silver introuvable : {silver_file}. "
            "Exécuter d'abord pipeline/silver_transform.py."
        )

    df = pd.read_parquet(silver_file)
    print(f"[SILVER NLP] Offres Silver chargées : {len(df)}")
    return df


def charger_referentiel_competences(referentiel_path: str | Path) -> dict:
    """
    Charge le référentiel de compétences IT.
    """
    referentiel_path = Path(referentiel_path)

    if not referentiel_path.exists():
        raise FileNotFoundError(f"Référentiel introuvable : {referentiel_path}")

    with open(referentiel_path, "r", encoding="utf-8") as f:
        referentiel = json.load(f)

    if "familles" not in referentiel:
        raise ValueError("Le référentiel doit contenir une clé 'familles'.")

    return referentiel


def construire_index_alias(referentiel: dict) -> list[dict]:
    """
    Transforme le référentiel en index plat.

    Exemple :
    alias='python3' -> competence='python', famille='langages'

    Les alias sont triés par longueur décroissante pour éviter les faux matchs :
    - 'node.js' doit être testé avant 'node'
    - 'power bi' doit être testé avant 'bi'
    """
    alias_index = []

    for famille, competences in referentiel["familles"].items():
        for competence_normalisee, aliases in competences.items():
            for alias in aliases:
                alias_index.append(
                    {
                        "alias": str(alias).lower().strip(),
                        "competence": competence_normalisee,
                        "famille": famille,
                    }
                )

    alias_index = sorted(alias_index, key=lambda x: len(x["alias"]), reverse=True)
    return alias_index


def normaliser_texte(value: Any) -> str:
    """
    Normalise légèrement le texte pour le matching.

    Attention :
    Cette étape ne remplace pas le nettoyage Silver.
    Elle sert uniquement à fiabiliser l'extraction des compétences.
    """
    if pd.isna(value):
        return ""

    text = str(value).lower()
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def alias_present(alias: str, texte: str) -> bool:
    """
    Vérifie la présence d'un alias dans le texte.

    On utilise des frontières personnalisées pour mieux gérer :
    - node.js
    - c#
    - .net
    - power bi
    - ci/cd
    """
    if not alias:
        return False

    pattern = r"(?<![a-zA-Z0-9+#.])" + re.escape(alias) + r"(?![a-zA-Z0-9+#.])"
    return re.search(pattern, texte, flags=re.IGNORECASE) is not None


def extraire_competences(df_offres: pd.DataFrame, referentiel_path: str | Path, report_path: str | Path) -> pd.DataFrame:
    """
    Extrait les compétences IT depuis competences_brut et description.

    Règle métier :
    Une offre peut produire plusieurs lignes compétences.
    Chaque ligne représente une compétence détectée pour une offre.
    """
    rows_before = len(df_offres)

    referentiel = charger_referentiel_competences(referentiel_path)
    alias_index = construire_index_alias(referentiel)

    resultats = []

    for _, offre in df_offres.iterrows():
        id_offre = offre.get("id_offre")

        texte_competences = normaliser_texte(offre.get("competences_brut"))
        texte_description = normaliser_texte(offre.get("description"))

        texte_complet = f"{texte_competences} {texte_description}".strip()

        competences_trouvees = set()

        for item in alias_index:
            alias = item["alias"]
            competence = item["competence"]
            famille = item["famille"]

            if competence in competences_trouvees:
                continue

            if alias_present(alias, texte_complet):
                competences_trouvees.add(competence)

                source_detection = []
                if alias_present(alias, texte_competences):
                    source_detection.append("competences_brut")
                if alias_present(alias, texte_description):
                    source_detection.append("description")

                resultats.append(
                    {
                        "id_offre": id_offre,
                        "source": offre.get("source_std"),
                        "entreprise": offre.get("entreprise"),
                        "ville": offre.get("ville_std"),
                        "region_admin": offre.get("region_admin"),
                        "profil": offre.get("profil_normalise"),
                        "type_contrat": offre.get("type_contrat_std"),
                        "competence": competence,
                        "famille": famille,
                        "alias_detecte": alias,
                        "source_detection": "+".join(source_detection),
                        "date_pub": offre.get("date_publication_dt"),
                        "annee": offre.get("annee"),
                        "mois": offre.get("mois"),
                        "mois_partition": offre.get("mois_partition"),
                    }
                )

        if not competences_trouvees:
            resultats.append(
                {
                    "id_offre": id_offre,
                    "source": offre.get("source_std"),
                    "entreprise": offre.get("entreprise"),
                    "ville": offre.get("ville_std"),
                    "region_admin": offre.get("region_admin"),
                    "profil": offre.get("profil_normalise"),
                    "type_contrat": offre.get("type_contrat_std"),
                    "competence": "non_detecte",
                    "famille": "inconnu",
                    "alias_detecte": None,
                    "source_detection": "aucune",
                    "date_pub": offre.get("date_publication_dt"),
                    "annee": offre.get("annee"),
                    "mois": offre.get("mois"),
                    "mois_partition": offre.get("mois_partition"),
                }
            )

    df_competences = pd.DataFrame(resultats)

    nb_lignes = len(df_competences)
    nb_offres_avec_comp = df_competences[df_competences["competence"] != "non_detecte"]["id_offre"].nunique()
    pct_offres_avec_comp = round(nb_offres_avec_comp * 100 / rows_before, 2)

    top_competences = (
        df_competences[df_competences["competence"] != "non_detecte"]["competence"]
        .value_counts()
        .head(10)
        .to_dict()
    )

    log_step(
        report_path=report_path,
        step_name="Extraction des compétences IT",
        rule="Matching regex des alias du référentiel sur competences_brut et description. Une offre peut générer plusieurs lignes compétences.",
        rows_before=rows_before,
        rows_after=nb_lignes,
        details=(
            f"Offres avec au moins une compétence détectée: {nb_offres_avec_comp}/{rows_before} "
            f"({pct_offres_avec_comp}%). Top compétences: {top_competences}"
        )
    )

    print(f"[SILVER NLP] Lignes compétences extraites : {nb_lignes}")
    print(f"[SILVER NLP] Offres avec compétence détectée : {nb_offres_avec_comp}/{rows_before} ({pct_offres_avec_comp}%)")

    return df_competences


def sauvegarder_competences(df_competences: pd.DataFrame, data_lake_root: str | Path, report_path: str | Path) -> None:
    """
    Sauvegarde les compétences extraites au format Parquet.
    """
    rows_before = len(df_competences)

    data_lake_root = Path(data_lake_root)
    output_dir = data_lake_root / "silver" / "competences_extraites"
    ensure_directory(output_dir)

    output_file = output_dir / "competences.parquet"

    if output_file.exists():
        output_file.unlink()

    df_competences.to_parquet(output_file, index=False, compression="snappy")

    log_step(
        report_path=report_path,
        step_name="Sauvegarde des compétences extraites",
        rule="Sauvegarde du résultat NLP Silver en Parquet dans silver/competences_extraites/competences.parquet.",
        rows_before=rows_before,
        rows_after=len(df_competences),
        details=f"Fichier généré: {output_file}"
    )

    print(f"[SILVER NLP] Fichier sauvegardé : {output_file}")


def construire_competences_silver(
    data_lake_root: str | Path,
    referentiel_path: str | Path,
    report_path: str | Path
) -> pd.DataFrame:
    """
    Pipeline complet Silver NLP.
    """
    df_offres = charger_offres_silver(data_lake_root)

    df_competences = extraire_competences(
        df_offres=df_offres,
        referentiel_path=referentiel_path,
        report_path=report_path
    )

    sauvegarder_competences(
        df_competences=df_competences,
        data_lake_root=data_lake_root,
        report_path=report_path
    )

    print("\n[SILVER NLP] Extraction des compétences terminée avec succès")
    return df_competences


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]

    data_lake_root = project_root / "data_lake_mexora_rh"
    referentiel_path = project_root / "data_sources" / "reference" / "referentiel_competences_it.json"
    report_path = project_root / "docs" / "rapport_pipeline.md"

    construire_competences_silver(
        data_lake_root=data_lake_root,
        referentiel_path=referentiel_path,
        report_path=report_path
    )


if __name__ == "__main__":
    main()