"""
Script : main.py
Projet : Mexora RH Intelligence

Objectif :
Orchestrer l'ensemble du pipeline Data Lake :
1. Génération des fichiers sources
2. Ingestion Bronze
3. Transformation Silver
4. Extraction NLP des compétences
5. Agrégation Gold
"""

from pathlib import Path

from pipeline.generate_sources import main as generate_sources_main
from pipeline.bronze_ingestion import ingerer_bronze
from pipeline.silver_transform import construire_silver
from pipeline.silver_nlp import construire_competences_silver
from pipeline.gold_aggregation import construire_gold


def main() -> None:
    project_root = Path(__file__).resolve().parent

    data_lake_root = project_root / "data_lake_mexora_rh"
    source_file = project_root / "data_sources" / "raw" / "offres_emploi_it_maroc.json"
    referentiel_path = project_root / "data_sources" / "reference" / "referentiel_competences_it.json"
    report_path = project_root / "docs" / "rapport_pipeline.md"

    print("\n==============================")
    print("MEXORA RH INTELLIGENCE PIPELINE")
    print("==============================\n")

    print("[1/5] Génération des fichiers sources")
    generate_sources_main()

    print("\n[2/5] Ingestion Bronze")
    ingerer_bronze(
        filepath_source=source_file,
        data_lake_root=data_lake_root,
        clean_before=True
    )

    print("\n[3/5] Transformation Silver")
    construire_silver(
        data_lake_root=data_lake_root,
        report_path=report_path
    )

    print("\n[4/5] Extraction NLP des compétences")
    construire_competences_silver(
        data_lake_root=data_lake_root,
        referentiel_path=referentiel_path,
        report_path=report_path
    )

    print("\n[5/5] Construction Gold")
    construire_gold(
        data_lake_root=data_lake_root,
        report_path=report_path
    )

    print("\n==============================")
    print("PIPELINE TERMINÉ AVEC SUCCÈS")
    print("==============================")


if __name__ == "__main__":
    main()