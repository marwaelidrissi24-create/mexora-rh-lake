# Mexora RH Intelligence  
## Data Lake & Analyse du Marché de l’Emploi IT au Maroc

---

## 1. Présentation du projet

Ce projet s’inscrit dans le cadre du miniprojet **Data Lake & Analyse du Marché de l’Emploi IT au Maroc**.

L’entreprise fictive **Mexora** souhaite renforcer son équipe data en recrutant de nouveaux profils dans les six prochains mois : **Data Engineers**, **Data Analysts** et **Data Scientist**. Avant de publier les offres et de fixer les salaires, la direction RH souhaite comprendre le marché marocain de l’emploi IT afin de répondre à plusieurs questions stratégiques :

- Quelles sont les compétences IT les plus demandées au Maroc ?
- Quel est le salaire médian d’un Data Engineer à Tanger ?
- Quelles villes concentrent le plus d’opportunités IT ?
- Les entreprises recrutent-elles davantage en CDI, freelance ou autres contrats ?
- Qui sont les principaux concurrents de Mexora sur le marché du talent ?

Pour répondre à ces besoins, ce projet met en place un **Data Lake local** organisé en trois zones : **Bronze**, **Silver** et **Gold**.

---

## 2. Objectifs du projet

Le projet vise à :

- Concevoir une architecture Data Lake en zones Bronze / Silver / Gold.
- Générer un dataset réaliste de 5 000 offres d’emploi IT marocaines.
- Ingestérer les données brutes dans une zone Bronze immuable.
- Nettoyer, standardiser et typer les données dans une zone Silver.
- Extraire les compétences IT depuis du texte libre avec une approche NLP basique par regex.
- Construire des tables analytiques Gold exploitables avec DuckDB.
- Préparer les données pour l’analyse de marché, le dashboard et le rapport final.

---

## 3. Stack technique utilisée

| Outil | Usage |
|---|---|
| Python 3.11+ | Développement et orchestration du pipeline |
| pandas | Manipulation, nettoyage et transformation des données |
| pyarrow | Lecture et écriture des fichiers Parquet |
| DuckDB | Requêtes SQL analytiques sur fichiers Parquet |
| re | Extraction de compétences par expressions régulières |
| Git / GitHub | Versioning du code et des livrables |
| VS Code | Environnement de développement |

---

## 4. Architecture générale du Data Lake

Le Data Lake est organisé en trois zones :

```text
data_lake_mexora_rh/
├── bronze/
│   ├── rekrute/
│   ├── marocannonce/
│   └── linkedin/
├── silver/
│   ├── offres_clean/
│   └── competences_extraites/
└── gold/
    ├── top_competences.parquet
    ├── salaires_par_profil.parquet
    ├── offres_par_ville.parquet
    ├── entreprises_recruteurs.parquet
    └── tendances_mensuelles.parquet
```

### 4.1 Zone Bronze

La zone Bronze contient les données brutes au format JSON, sans modification des offres.  
Elle représente l’archive fidèle des données reçues.

Partitionnement :

```text
data_lake_mexora_rh/bronze/{source}/{YYYY_MM}/offres_raw.json
```

Exemple :

```text
data_lake_mexora_rh/bronze/rekrute/2024_08/offres_raw.json
```

### 4.2 Zone Silver

La zone Silver contient les données nettoyées, standardisées et typées au format Parquet.

Elle contient principalement :

```text
data_lake_mexora_rh/silver/offres_clean/offres_clean.parquet
data_lake_mexora_rh/silver/competences_extraites/competences.parquet
```

Une version partitionnée par ville et par mois est également générée :

```text
data_lake_mexora_rh/silver/offres_clean/ville=Casablanca/mois=2024_08/offres_clean.parquet
```

### 4.3 Zone Gold

La zone Gold contient les tables analytiques prêtes à l’emploi pour DuckDB, les notebooks, les visualisations et le rapport final.

---

## 5. Structure du projet

```text
mexora_rh_lake/
├── analysis/
│   └── analyse_marche.py
│
├── data_sources/
│   ├── raw/
│   │   └── offres_emploi_it_maroc.json
│   └── reference/
│       ├── referentiel_competences_it.json
│       └── entreprises_it_maroc.csv
│
├── data_lake_mexora_rh/
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── docs/
│   ├── conception_data_lake.md
│   ├── conception_data_lake_mexora.pdf
│   ├── schema_architecture.png
│   ├── structure_repertoires_data_lake.jpeg
│   └── rapport_pipeline.md
│
├── pipeline/
│   ├── __init__.py
│   ├── generate_sources.py
│   ├── bronze_ingestion.py
│   ├── silver_transform.py
│   ├── silver_nlp.py
│   ├── gold_aggregation.py
│   └── utils.py
│
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 6. Description des fichiers principaux

### `pipeline/generate_sources.py`

Ce script génère les fichiers sources du projet :

```text
data_sources/raw/offres_emploi_it_maroc.json
data_sources/reference/referentiel_competences_it.json
data_sources/reference/entreprises_it_maroc.csv
```

Le dataset généré contient 5 000 offres d’emploi IT marocaines entre janvier 2023 et novembre 2024.  
Les données sont synthétiques mais réalistes, avec des problèmes intentionnels afin de simuler des données issues du scraping.

Problèmes volontairement présents dans les données brutes :

- villes non standardisées : `casa`, `CASABLANCA`, `TNG`, `Tanja` ;
- salaires mixtes : `15000-20000 MAD`, `15K-20K`, `Selon profil`, `Confidentiel`, montants en EUR ;
- expériences hétérogènes : `3-5 ans`, `min 3 ans`, `Débutant accepté`, valeurs nulles ;
- contrats non uniformes : `CDI`, `cdi`, `Permanent`, `Contrat à durée indéterminée` ;
- dates mixtes et quelques dates incohérentes ;
- texte libre dans `description` et `competences_brut`.

### `pipeline/bronze_ingestion.py`

Ce script charge le fichier source brut dans la zone Bronze.

Règle fondamentale :

> La zone Bronze est une archive brute et immuable. Les données ne sont ni nettoyées, ni corrigées, ni standardisées.

Sortie :

```text
data_lake_mexora_rh/bronze/{source}/{mois}/offres_raw.json
```

### `pipeline/silver_transform.py`

Ce script nettoie et standardise les offres issues de la zone Bronze.

Transformations principales :

- normalisation des dates ;
- normalisation des villes ;
- normalisation des contrats ;
- normalisation des intitulés de poste ;
- normalisation des salaires ;
- normalisation de l’expérience requise ;
- ajout de flags qualité ;
- sauvegarde en Parquet consolidé et partitionné.

Sortie principale :

```text
data_lake_mexora_rh/silver/offres_clean/offres_clean.parquet
```

### `pipeline/silver_nlp.py`

Ce script extrait les compétences IT depuis deux champs :

- `competences_brut`
- `description`

La méthode utilisée repose sur un matching par expressions régulières à partir du référentiel :

```text
data_sources/reference/referentiel_competences_it.json
```

Sortie :

```text
data_lake_mexora_rh/silver/competences_extraites/competences.parquet
```

### `pipeline/gold_aggregation.py`

Ce script construit les tables analytiques Gold avec DuckDB.

Sorties :

```text
data_lake_mexora_rh/gold/top_competences.parquet
data_lake_mexora_rh/gold/salaires_par_profil.parquet
data_lake_mexora_rh/gold/offres_par_ville.parquet
data_lake_mexora_rh/gold/entreprises_recruteurs.parquet
data_lake_mexora_rh/gold/tendances_mensuelles.parquet
```

### `pipeline/utils.py`

Ce fichier contient des fonctions partagées :

- création de dossiers ;
- journalisation des étapes ;
- écriture automatique du rapport `docs/rapport_pipeline.md`.

### `main.py`

Ce fichier orchestre l’exécution complète du pipeline :

1. Génération des sources
2. Ingestion Bronze
3. Transformation Silver
4. Extraction NLP des compétences
5. Agrégation Gold

---

## 7. Installation du projet

### 7.1 Cloner le repository

```powershell
git clone https://github.com/marwaelidrissi24-create/mexora-rh-lake.git
cd mexora-rh-lake
```

### 7.2 Créer un environnement virtuel

```powershell
python -m venv .venv
```

### 7.3 Activer l’environnement virtuel

Sous Windows PowerShell :

```powershell
.venv\Scripts\Activate.ps1
```

Si PowerShell bloque l’activation, exécuter :

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Puis relancer :

```powershell
.venv\Scripts\Activate.ps1
```

### 7.4 Installer les dépendances

```powershell
pip install -r requirements.txt
```

---

## 8. Exécution complète du pipeline

Pour exécuter tout le pipeline :

```powershell
python main.py
```

Cette commande reconstruit tout le Data Lake :

```text
data_sources
     ↓
Bronze
     ↓
Silver
     ↓
Silver NLP
     ↓
Gold
```

---

## 9. Exécution étape par étape

Il est également possible d’exécuter chaque étape séparément.

### 9.1 Générer les fichiers sources

```powershell
python pipeline/generate_sources.py
```

### 9.2 Ingestion Bronze

```powershell
python pipeline/bronze_ingestion.py
```

### 9.3 Transformation Silver

```powershell
python pipeline/silver_transform.py
```

### 9.4 Extraction NLP des compétences

```powershell
python pipeline/silver_nlp.py
```

### 9.5 Agrégation Gold

```powershell
python pipeline/gold_aggregation.py
```

---

## 10. Résultats du dernier pipeline

Le dernier run complet du pipeline produit les résultats suivants.

### 10.1 Sources générées

```text
Nombre total d’offres : 5000
Période couverte      : janvier 2023 à novembre 2024
Sources               : Rekrute, MarocAnnonce, LinkedIn Maroc
```

### 10.2 Bronze

```text
Total offres ingérées        : 5000
Nombre de partitions Bronze  : 69

Répartition par source :
- rekrute       : 2046 offres
- linkedin      : 1728 offres
- marocannonce  : 1226 offres
```

### 10.3 Silver

```text
Nombre d’offres nettoyées : 5000
Nombre de colonnes        : 45
Villes non reconnues      : 0
Salaires connus           : 3873 / 5000
Expériences interprétées  : 4428 / 5000
Dates incohérentes        : 117
```

### 10.4 Silver NLP

```text
Nombre de lignes compétences extraites : 30817
Offres avec au moins une compétence    : 5000 / 5000
```

### 10.5 Gold

```text
top_competences.parquet          : 127 lignes
salaires_par_profil.parquet      : 482 lignes
offres_par_ville.parquet         : 2129 lignes
entreprises_recruteurs.parquet   : 82 lignes
tendances_mensuelles.parquet     : 253 lignes
```

---

## 11. Contrôles de vérification

### 11.1 Vérifier les fichiers Gold

```powershell
Get-ChildItem data_lake_mexora_rh\gold
```

### 11.2 Vérifier la taille des tables Gold

```powershell
python -c "import pandas as pd,pathlib; p=pathlib.Path('data_lake_mexora_rh/gold'); [print(f.name, pd.read_parquet(f).shape) for f in p.glob('*.parquet')]"
```

### 11.3 Vérifier les compétences les plus demandées

```powershell
python -c "import pandas as pd; df=pd.read_parquet('data_lake_mexora_rh/gold/top_competences.parquet'); print(df[df['profil']=='tous'].sort_values('nb_offres_mentionnent', ascending=False).head(20).to_string())"
```

### 11.4 Vérifier les salaires Data Engineer à Tanger

```powershell
python -c "import pandas as pd; df=pd.read_parquet('data_lake_mexora_rh/gold/salaires_par_profil.parquet'); print(df[(df['ville']=='Tanger') & (df['profil']=='Data Engineer')].to_string())"
```

### 11.5 Vérifier le rapport pipeline

```powershell
Get-Content docs\rapport_pipeline.md -Tail 120
```

---

## 12. Rapport de traitement

Le rapport technique du pipeline est disponible dans :

```text
docs/rapport_pipeline.md
```

Il documente pour chaque transformation :

- la règle appliquée ;
- le nombre de lignes avant ;
- le nombre de lignes après ;
- les cas limites rencontrés ;
- le traitement adopté.

Principales transformations documentées :

- chargement depuis Bronze ;
- normalisation des dates ;
- normalisation des villes ;
- normalisation des contrats ;
- normalisation des intitulés de poste ;
- normalisation des salaires ;
- normalisation de l’expérience ;
- enrichissement analytique Silver ;
- contrôles qualité Silver ;
- sauvegarde Silver ;
- extraction des compétences IT ;
- sauvegarde des compétences extraites ;
- construction des tables Gold.

---

## 13. Hypothèses de conception

Les fichiers sources sont générés par script, car aucun fichier réel n’est fourni avec l’énoncé.

Les données générées sont synthétiques mais réalistes. Elles reproduisent volontairement les problèmes courants rencontrés dans des données issues du scraping :

- valeurs manquantes ;
- formats hétérogènes ;
- incohérences de saisie ;
- texte libre non structuré ;
- dates incohérentes ;
- salaires non communiqués ;
- compétences mélangées dans des champs textuels.

Ces hypothèses permettent de tester réellement les capacités du pipeline de nettoyage, de standardisation, d’extraction NLP et d’agrégation analytique.

---

## 14. Livrables liés à l’Étape 2

| Livrable | Emplacement |
|---|---|
| Code Python complet | `pipeline/`, `main.py` |
| Instructions de reproduction | `README.md` |
| Rapport de traitement | `docs/rapport_pipeline.md` |
| Données sources | `data_sources/` |
| Données Bronze | `data_lake_mexora_rh/bronze/` |
| Données Silver | `data_lake_mexora_rh/silver/` |
| Données Gold | `data_lake_mexora_rh/gold/` |

---

## 15. Commandes Git utiles

Vérifier l’état du repository :

```powershell
git status
```

Ajouter les fichiers modifiés :

```powershell
git add .
```

Créer un commit :

```powershell
git commit -m "Complete step 2 Python data lake pipeline"
```

Envoyer vers GitHub :

```powershell
git push
```

---

## 16. État actuel du projet

À ce stade, l’Étape 2 est complète :

- le pipeline Python est fonctionnel ;
- les données sources sont générées ;
- la zone Bronze est construite ;
- la zone Silver est nettoyée et standardisée ;
- les compétences IT sont extraites ;
- les tables Gold sont générées ;
- le rapport de traitement est produit ;
- le pipeline peut être reproduit avec `python main.py`.

La prochaine étape est l’analyse du marché avec DuckDB dans `analysis/analyse_marche.py` et dans le notebook `analyse_marche_it_maroc.ipynb`.