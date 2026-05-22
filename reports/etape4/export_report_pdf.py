"""
Script : export_report_pdf.py
Projet : Mexora RH Intelligence

Objectif :
Convertir le rapport analytique Markdown de l'Étape 4 en HTML puis PDF.

Sorties :
- reports/etape4/rapport_analytique_mexora.html
- reports/etape4/rapport_analytique_mexora.pdf

Méthode :
1. Lecture du rapport Markdown
2. Conversion simple en HTML
3. Application d'un CSS professionnel compact
4. Impression PDF via Microsoft Edge en mode headless
5. Contrôle du nombre de pages avec pypdf
"""

from pathlib import Path
import subprocess
import shutil
import sys
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ETAPE4_DIR = PROJECT_ROOT / "reports" / "etape4"

MD_PATH = ETAPE4_DIR / "rapport_analytique_mexora.md"
HTML_PATH = ETAPE4_DIR / "rapport_analytique_mexora.html"
PDF_PATH = ETAPE4_DIR / "rapport_analytique_mexora.pdf"


def install_if_missing(package: str) -> None:
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def markdown_to_html_basic(md: str) -> str:
    """
    Conversion Markdown simple adaptée au rapport généré.
    On évite une dépendance lourde pour garder le projet facile à reproduire.
    """
    lines = md.splitlines()
    html = []
    in_table = False
    in_ul = False

    def close_ul():
        nonlocal in_ul
        if in_ul:
            html.append("</ul>")
            in_ul = False

    def close_table():
        nonlocal in_table
        if in_table:
            html.append("</table>")
            in_table = False

    for line in lines:
        raw = line.rstrip()

        if raw.strip() == "":
            close_ul()
            close_table()
            continue

        if raw.startswith("---"):
            close_ul()
            close_table()
            html.append("<hr>")
            continue

        if raw.startswith("# "):
            close_ul()
            close_table()
            html.append(f"<h1>{raw[2:].strip()}</h1>")
            continue

        if raw.startswith("## "):
            close_ul()
            close_table()
            html.append(f"<h2>{raw[3:].strip()}</h2>")
            continue

        if raw.startswith("### "):
            close_ul()
            close_table()
            html.append(f"<h3>{raw[4:].strip()}</h3>")
            continue

        if raw.startswith("![") and "](" in raw and raw.endswith(")"):
            close_ul()
            close_table()
            alt = raw.split("](")[0].replace("![", "")
            src = raw.split("](")[1].replace(")", "")
            html.append(f'<figure><img src="{src}" alt="{alt}"><figcaption>{alt}</figcaption></figure>')
            continue

        if raw.startswith("- "):
            close_table()
            if not in_ul:
                html.append("<ul>")
                in_ul = True
            html.append(f"<li>{raw[2:].strip()}</li>")
            continue

        if raw.startswith("|") and raw.endswith("|"):
            close_ul()
            cells = [c.strip() for c in raw.strip("|").split("|")]

            # Ligne séparatrice Markdown
            if all(set(c.replace(":", "").replace("-", "")) == set() for c in cells):
                continue

            if not in_table:
                html.append("<table>")
                in_table = True
                html.append("<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>")
            else:
                html.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
            continue

        close_ul()
        close_table()

        # Gras Markdown simple
        text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", raw)
        html.append(f"<p>{text}</p>")

    close_ul()
    close_table()
    return "\n".join(html)


def build_html() -> None:
    if not MD_PATH.exists():
        raise FileNotFoundError(f"Rapport Markdown introuvable : {MD_PATH}")

    md = MD_PATH.read_text(encoding="utf-8")

    # Supprimer le titre Markdown initial du rapport, car il est déjà présent
    # dans la page de garde. Cela évite une page presque vide après la couverture.
    md = re.sub(
        r"^# RAPPORT.*?\n## Mexora RH Intelligence — Novembre 2024\s*\n\s*---\s*\n",
        "",
        md,
        flags=re.DOTALL
    )

    body = markdown_to_html_basic(md)

    css = """
    @page {
        size: A4;
        margin: 10mm 10mm 11mm 10mm;
    }

    * {
        box-sizing: border-box;
    }

    body {
        font-family: "Segoe UI", Arial, sans-serif;
        color: #2D2433;
        background: #FFFFFF;
        font-size: 8.7pt;
        line-height: 1.23;
    }

    h1 {
        color: #6A1B9A;
        font-size: 19pt;
        text-align: center;
        margin: 0 0 5mm 0;
        padding-bottom: 3mm;
        border-bottom: 2px solid #CE93D8;
    }

    h2 {
        color: #6A1B9A;
        font-size: 13pt;
        margin: 5mm 0 2.5mm 0;
        padding: 1.8mm 2.5mm;
        background: #F3E5F5;
        border-left: 4px solid #D81B60;
        page-break-after: avoid;
    }

    h3 {
        color: #D81B60;
        font-size: 10.5pt;
        margin: 3.5mm 0 1.5mm 0;
        page-break-after: avoid;
    }

    p {
        margin: 0 0 2mm 0;
        text-align: justify;
    }

    ul {
        margin: 1mm 0 2mm 5mm;
        padding-left: 3mm;
    }

    li {
        margin-bottom: 1mm;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        margin: 2mm 0 3mm 0;
        font-size: 7.5pt;
        page-break-inside: avoid;
    }

    th {
        background: #6A1B9A;
        color: white;
        padding: 1.6mm;
        border: 0.3pt solid #CE93D8;
        text-align: left;
    }

    td {
        padding: 1.4mm;
        border: 0.3pt solid #E8DDEE;
        vertical-align: top;
    }

    tr:nth-child(even) td {
        background: #FFF7FB;
    }

    figure {
        margin: 2mm 0 4mm 0;
        text-align: center;
        page-break-inside: avoid;
    }

    figure img {
        max-width: 100%;
        max-height: 115mm;
        border: 0.6pt solid #E8DDEE;
        border-radius: 4px;
    }

    figcaption {
        font-size: 7.2pt;
        color: #6C5A72;
        margin-top: 1mm;
    }

    hr {
        border: none;
        border-top: 1px solid #E8DDEE;
        margin: 3mm 0;
    }

    /* Répartition propre pour respecter les 10 pages */
    h2:nth-of-type(1) { page-break-before: avoid; }
    h2:nth-of-type(2),
    h2:nth-of-type(3),
    h2:nth-of-type(4),
    h2:nth-of-type(5),
    h2:nth-of-type(6),
    h2:nth-of-type(7) {
        page-break-before: always;
    }
    .cover-page {
    height: 257mm;
    page-break-after: always;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 12mm 13mm;
    background: linear-gradient(135deg, #FFFFFF, #FFF7FB, #F3E5F5);
    border: 1.5px solid #CE93D8;
    overflow: hidden;
    }

    .logos {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        min-height: 34mm;
    }

    .logos img {
        max-height: 30mm;
        max-width: 45mm;
        object-fit: contain;
    }

    .cover-title {
        text-align: center;
        margin-top: 6mm;
    }

    .cover-title h1 {
        border: none;
        font-size: 23pt;
        color: #6A1B9A;
        margin: 0 0 7mm 0;
        padding: 0;
    }

    .cover-title h2 {
        background: none;
        border-left: none;
        font-size: 16pt;
        color: #D81B60;
        margin: 0 0 5mm 0;
        padding: 0;
        page-break-before: avoid;
    }

    .cover-title h3 {
        font-size: 12pt;
        color: #6A1B9A;
        margin: 0;
    }

    .cover-info {
        background: white;
        border-radius: 9px;
        border: 1px solid #CE93D8;
        padding: 7mm;
        font-size: 10pt;
        line-height: 1.35;
        margin-bottom: 4mm;
    }

    .cover-info p {
        text-align: center;
        margin: 0 0 1.8mm 0;
    }

    .report-content h1 {
        margin-top: 0;
    }
    """

    uae_logo = (ETAPE4_DIR / "assets" / "uae_logo.png").resolve().as_uri()
    fstt_logo = (ETAPE4_DIR / "assets" / "fstt_logo.png").resolve().as_uri()

    cover_html = f"""
    <section class="cover-page">
        <div class="logos">
            <img src="{uae_logo}" alt="Université Abdelmalek Essaâdi">
            <img src="{fstt_logo}" alt="FST Tanger">
        </div>

        <div class="cover-title">
            <h1>RAPPORT ANALYTIQUE</h1>
            <h2>Analyse du Marché de l’Emploi IT au Maroc</h2>
            <h3>Mexora RH Intelligence — Novembre 2024</h3>
        </div>

        <div class="cover-info">
            <p><strong>Mini-projet :</strong> Data Lake & Analyse du Marché de l’Emploi IT au Maroc</p>
            <p><strong>Module :</strong> Ingénierie de Données</p>
            <p><strong>Réalisé par :</strong></p>
            <p>MAROUA EL IDRISSI</p>
            <p>YOUSRA SAOUIKI</p>
            <p><strong>Encadré par :</strong> PR. H. ZILI</p>
            <p><strong>Année universitaire :</strong> 2025–2026</p>
            <p><strong>Repository GitHub :</strong> https://github.com/marwaelidrissi24-create/mexora-rh-lake</p>
        </div>
    </section>
    """

    html = f"""<!DOCTYPE html>
    <html lang="fr">
    <head>
    <meta charset="UTF-8">
    <title>Rapport analytique Mexora</title>
    <style>{css}</style>
    </head>
    <body>
    {cover_html}
    <main class="report-content">
    {body}
    </main>
    </body>
    </html>
    """

    HTML_PATH.write_text(html, encoding="utf-8")


def find_edge() -> str:
    """
    Trouve Microsoft Edge sur Windows.
    """
    candidates = [
        shutil.which("msedge"),
        r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
        r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    ]

    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)

    raise FileNotFoundError(
        "Microsoft Edge introuvable. "
        "Ouvre rapport_analytique_mexora.html dans le navigateur puis fais Ctrl+P > Save as PDF."
    )


def export_pdf() -> None:
    edge = find_edge()

    if PDF_PATH.exists():
        PDF_PATH.unlink()

    html_uri = HTML_PATH.resolve().as_uri()

    cmd = [
        edge,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--print-to-pdf-no-header",
        f"--print-to-pdf={PDF_PATH.resolve()}",
        html_uri,
    ]

    subprocess.run(cmd, check=True)

    if not PDF_PATH.exists():
        raise RuntimeError("Le PDF n'a pas été généré.")


def count_pages() -> int:
    install_if_missing("pypdf")
    from pypdf import PdfReader

    reader = PdfReader(str(PDF_PATH))
    return len(reader.pages)


def main() -> None:
    build_html()
    export_pdf()
    pages = count_pages()

    print("[PDF] Rapport HTML généré :", HTML_PATH)
    print("[PDF] Rapport PDF généré  :", PDF_PATH)
    print("[PDF] Nombre de pages     :", pages)

    if pages > 10:
        print("[ATTENTION] Le rapport dépasse 10 pages. Il faut compacter le style ou réduire le contenu.")
        sys.exit(1)

    print("[OK] Rapport conforme : 10 pages maximum.")


if __name__ == "__main__":
    main()