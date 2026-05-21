from pathlib import Path
import nbformat as nbf

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REPORT_PATH = PROJECT_ROOT / "reports" / "etape3" / "analyse_marche_resultats.md"
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "analyse_marche_it_maroc.ipynb"

if not REPORT_PATH.exists():
    raise FileNotFoundError(
        f"Rapport Étape 3 introuvable : {REPORT_PATH}\n"
        "Exécuter d'abord : python analysis/analyse_marche.py"
    )

markdown = REPORT_PATH.read_text(encoding="utf-8")

# Adapter les chemins des images, car le notebook est dans /notebooks
markdown = markdown.replace("](figures/", "](../reports/etape3/figures/")

nb = nbf.v4.new_notebook()

nb["metadata"] = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    },
    "language_info": {
        "name": "python",
        "pygments_lexer": "ipython3"
    }
}

intro = """# Analyse du Marché de l’Emploi IT au Maroc  
## Mexora RH Intelligence — Étape 3

Ce notebook répond aux cinq questions analytiques demandées dans le miniprojet.

Il contient pour chaque question :

- la requête DuckDB documentée ;
- le résultat sous forme de tableau ;
- une visualisation ;
- une interprétation textuelle orientée décision RH.

Les données utilisées proviennent des tables Gold générées dans le Data Lake.
"""

setup_code = r'''from pathlib import Path
import sys
import pandas as pd
import duckdb
import matplotlib.pyplot as plt

PROJECT_ROOT = Path.cwd()
if PROJECT_ROOT.name == "notebooks":
    PROJECT_ROOT = PROJECT_ROOT.parent

DATA_LAKE_ROOT = PROJECT_ROOT / "data_lake_mexora_rh"
GOLD_DIR = DATA_LAKE_ROOT / "gold"
SILVER_DIR = DATA_LAKE_ROOT / "silver"
REPORTS_DIR = PROJECT_ROOT / "reports" / "etape3"

print("Project root:", PROJECT_ROOT)
print("Gold exists:", GOLD_DIR.exists())
print("Reports exists:", REPORTS_DIR.exists())
'''

reproduce_code = r'''# Reproduire automatiquement les résultats de l'Étape 3
# Cette cellule relance le script d'analyse DuckDB et régénère les CSV, figures et rapport Markdown.

import sys
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.analyse_marche import main as run_market_analysis

run_market_analysis()
'''

check_code = r'''# Vérification rapide des livrables générés

resultats = sorted((REPORTS_DIR / "resultats").glob("*.csv"))
figures = sorted((REPORTS_DIR / "figures").glob("*.png"))

print("Nombre de fichiers CSV générés :", len(resultats))
for f in resultats:
    print("-", f.name)

print("\nNombre de figures générées :", len(figures))
for f in figures:
    print("-", f.name)
'''

nb.cells = [
    nbf.v4.new_markdown_cell(intro),
    nbf.v4.new_code_cell(setup_code),
    nbf.v4.new_code_cell(reproduce_code),
    nbf.v4.new_code_cell(check_code),
    nbf.v4.new_markdown_cell(markdown),
]

NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)

with NOTEBOOK_PATH.open("w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"[OK] Notebook généré : {NOTEBOOK_PATH}")
