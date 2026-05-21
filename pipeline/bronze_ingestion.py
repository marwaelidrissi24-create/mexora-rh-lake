"""
Script : bronze_ingestion.py
Projet : Mexora RH Intelligence

Objectif :
Charger le fichier source brut offres_emploi_it_maroc.json dans la zone Bronze
du Data Lake, sans modifier les offres.

Règle fondamentale :
La zone Bronze est une archive brute et immuable.
On ne nettoie pas, on ne corrige pas, on ne standardise pas les données ici.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_publication_month(date_value: Any) -> str:
    """
    Détermine le mois de partition à partir de date_publication.

    Le dataset brut contient volontairement plusieurs formats :
    - YYYY-MM-DD
    - DD/MM/YYYY
    - Mon DD YYYY, ex: Aug 15 2024

    En Bronze, on ne modifie pas la valeur originale.
    On l'utilise seulement pour décider dans quel dossier écrire l'offre.
    """
    if date_value is None:
        return "date_inconnue"

    raw = str(date_value).strip()

    if raw == "":
        return "date_inconnue"

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%b %d %Y",
        "%B %d %Y",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed.strftime("%Y_%m")
        except ValueError:
            continue

    return "date_inconnue"


def normalize_source_for_path(source_value: Any) -> str:
    """
    Normalise uniquement le nom de source pour le chemin de partition.

    Attention :
    Cette fonction ne modifie pas le champ source dans l'offre.
    Elle sert seulement à construire le dossier Bronze.
    """
    if source_value is None:
        return "source_inconnue"

    source = str(source_value).strip().lower()

    mapping = {
        "rekrute": "rekrute",
        "marocannonce": "marocannonce",
        "maroc annonce": "marocannonce",
        "linkedin": "linkedin",
        "linkedin maroc": "linkedin",
    }

    return mapping.get(source, source.replace(" ", "_") or "source_inconnue")


def load_source_dataset(filepath_source: str | Path) -> list[dict]:
    """
    Charge le fichier JSON source.

    Le fichier attendu possède la forme :
    {
        "metadata": {...},
        "offres": [...]
    }
    """
    filepath_source = Path(filepath_source)

    if not filepath_source.exists():
        raise FileNotFoundError(f"Fichier source introuvable : {filepath_source}")

    with open(filepath_source, "r", encoding="utf-8") as f:
        data = json.load(f)

    offres = data.get("offres")

    if not isinstance(offres, list):
        raise ValueError("Le fichier source doit contenir une clé 'offres' de type liste.")

    return offres


def clean_previous_bronze_outputs(data_lake_root: str | Path) -> None:
    """
    Nettoie uniquement les fichiers offres_raw.json générés précédemment.

    Pourquoi ?
    Pendant le développement, on peut relancer l'ingestion plusieurs fois.
    Cette fonction supprime les anciennes sorties Bronze générées par le pipeline,
    mais elle conserve les dossiers et les .gitkeep.

    En contexte réel de production, la Bronze serait strictement append-only.
    Ici, pour le miniprojet, ce nettoyage rend les tests reproductibles.
    """
    bronze_root = Path(data_lake_root) / "bronze"

    if not bronze_root.exists():
        return

    for file in bronze_root.rglob("offres_raw.json"):
        file.unlink()


def ingerer_bronze(
    filepath_source: str | Path,
    data_lake_root: str | Path,
    clean_before: bool = True
) -> dict:
    """
    Charge les données brutes dans la zone Bronze sans modification des offres.

    Partitionnement :
    data_lake_mexora_rh/bronze/{source}/{YYYY_MM}/offres_raw.json

    Paramètres :
    - filepath_source : chemin vers offres_emploi_it_maroc.json
    - data_lake_root  : chemin vers data_lake_mexora_rh
    - clean_before    : supprime les sorties précédentes pour un run reproductible

    Retour :
    dictionnaire de statistiques d'ingestion.
    """
    filepath_source = Path(filepath_source)
    data_lake_root = Path(data_lake_root)

    if clean_before:
        clean_previous_bronze_outputs(data_lake_root)

    offres = load_source_dataset(filepath_source)

    stats = {
        "total": len(offres),
        "nb_partitions": 0,
        "par_source": {},
        "par_mois": {},
        "partitions": {},
    }

    partitions: dict[str, list[dict]] = {}

    for offre in offres:
        source_partition = normalize_source_for_path(offre.get("source"))
        mois_partition = parse_publication_month(offre.get("date_publication"))

        partition_key = f"{source_partition}/{mois_partition}"

        if partition_key not in partitions:
            partitions[partition_key] = []

        # Important :
        # On ajoute l'offre brute telle quelle. Aucune correction n'est appliquée.
        partitions[partition_key].append(offre)

    for partition_key, offres_partition in sorted(partitions.items()):
        source_partition, mois_partition = partition_key.split("/")

        partition_dir = data_lake_root / "bronze" / source_partition / mois_partition
        partition_dir.mkdir(parents=True, exist_ok=True)

        output_file = partition_dir / "offres_raw.json"

        payload = {
            "metadata": {
                "zone": "bronze",
                "principe": "raw_immutable",
                "source_fichier": str(filepath_source),
                "date_ingestion": datetime.now().isoformat(timespec="seconds"),
                "partition": partition_key,
                "source_partition": source_partition,
                "mois_partition": mois_partition,
                "nb_offres": len(offres_partition),
                "note": "Les offres sont conservées sans nettoyage ni standardisation."
            },
            "offres": offres_partition
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        stats["nb_partitions"] += 1
        stats["partitions"][partition_key] = len(offres_partition)
        stats["par_source"][source_partition] = (
            stats["par_source"].get(source_partition, 0) + len(offres_partition)
        )
        stats["par_mois"][mois_partition] = (
            stats["par_mois"].get(mois_partition, 0) + len(offres_partition)
        )

    print("\n[BRONZE] Ingestion terminée")
    print(f"[BRONZE] Total offres ingérées : {stats['total']}")
    print(f"[BRONZE] Nombre de partitions créées : {stats['nb_partitions']}")

    print("\n[BRONZE] Répartition par source")
    for source, count in sorted(stats["par_source"].items()):
        print(f"  - {source}: {count}")

    print("\n[BRONZE] Exemples de partitions")
    for partition, count in list(sorted(stats["partitions"].items()))[:10]:
        print(f"  - {partition}: {count} offres")

    return stats


def main() -> None:
    """
    Exécution directe du script.
    """
    project_root = Path(__file__).resolve().parents[1]

    source_file = project_root / "data_sources" / "raw" / "offres_emploi_it_maroc.json"
    data_lake_root = project_root / "data_lake_mexora_rh"

    ingerer_bronze(
        filepath_source=source_file,
        data_lake_root=data_lake_root,
        clean_before=True
    )


if __name__ == "__main__":
    main()