"""
Script : utils.py
Projet : Mexora RH Intelligence

Fonctions utilitaires partagées entre les scripts du pipeline.
"""

from datetime import datetime
from pathlib import Path
from typing import Any


def ensure_directory(path: str | Path) -> Path:
    """
    Crée un dossier s'il n'existe pas déjà.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def log_step(
    report_path: str | Path,
    step_name: str,
    rule: str,
    rows_before: int | None,
    rows_after: int | None,
    details: str = ""
) -> None:
    """
    Ajoute une entrée dans le rapport pipeline Markdown.

    Le projet demande de documenter pour chaque transformation :
    - la règle appliquée ;
    - le nombre de lignes avant / après ;
    - les cas limites rencontrés et leur traitement.
    """
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    if not report_path.exists():
        report_path.write_text(
            "# Rapport de traitement — Pipeline Mexora RH Intelligence\n\n"
            "Ce document trace les transformations appliquées pendant l'Étape 2 du projet.\n\n",
            encoding="utf-8"
        )

    before = "N/A" if rows_before is None else str(rows_before)
    after = "N/A" if rows_after is None else str(rows_after)

    entry = f"""
## {step_name}

- Date d'exécution : {datetime.now().isoformat(timespec="seconds")}
- Règle appliquée : {rule}
- Nombre de lignes avant : {before}
- Nombre de lignes après : {after}
- Détails / cas limites : {details}

"""
    with open(report_path, "a", encoding="utf-8") as f:
        f.write(entry)


def print_quality_indicator(label: str, value: Any) -> None:
    """
    Affiche un indicateur de qualité de manière lisible.
    """
    print(f"[QUALITY] {label}: {value}")