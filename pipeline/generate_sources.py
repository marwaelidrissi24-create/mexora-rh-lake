"""
Script : generate_sources.py
Projet : Mexora RH Intelligence

Objectif :
Générer les fichiers sources du miniprojet 2 :
- offres_emploi_it_maroc.json
- referentiel_competences_it.json
- entreprises_it_maroc.csv

Les données générées simulent des offres d’emploi IT marocaines brutes,
avec des anomalies volontaires conformes à l’énoncé du projet.
"""

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path


RANDOM_SEED = 42
NB_OFFRES = 5000

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data_sources" / "raw"
REF_DIR = PROJECT_ROOT / "data_sources" / "reference"

RAW_DIR.mkdir(parents=True, exist_ok=True)
REF_DIR.mkdir(parents=True, exist_ok=True)

random.seed(RANDOM_SEED)


def generate_referentiel_competences() -> dict:
    """
    Génère un référentiel de compétences IT organisé par familles.
    Le référentiel contient largement plus que l'extrait donné dans l'énoncé,
    afin de rendre l'extraction NLP plus réaliste.
    """
    return {
        "familles": {
            "langages": {
                "python": ["python", "python3", "py"],
                "javascript": ["javascript", "js", "node.js", "nodejs", "node"],
                "java": ["java", "java8", "java11", "java17"],
                "sql": ["sql", "mysql", "postgresql", "postgres", "oracle", "tsql"],
                "r": ["r", "rlang", "r-studio", "rstudio"],
                "scala": ["scala"],
                "typescript": ["typescript", "ts"],
                "php": ["php", "php8"],
                "csharp": ["c#", "csharp", ".net", "dotnet"],
                "go": ["go", "golang"],
            },
            "frameworks_web": {
                "react": ["react", "reactjs", "react.js"],
                "angular": ["angular", "angularjs"],
                "vue": ["vue", "vuejs", "vue.js"],
                "django": ["django", "django rest"],
                "flask": ["flask"],
                "spring": ["spring", "spring boot", "springboot"],
                "laravel": ["laravel"],
                "express": ["express", "express.js"],
                "nextjs": ["next.js", "nextjs", "next"],
            },
            "data_engineering": {
                "spark": ["spark", "apache spark", "pyspark"],
                "kafka": ["kafka", "apache kafka"],
                "airflow": ["airflow", "apache airflow"],
                "dbt": ["dbt", "data build tool"],
                "hadoop": ["hadoop", "hdfs", "mapreduce"],
                "etl": ["etl", "elt", "data pipeline", "pipeline data"],
                "databricks": ["databricks"],
                "snowflake": ["snowflake"],
                "data_lake": ["data lake", "datalake", "lakehouse"],
            },
            "cloud": {
                "aws": ["aws", "amazon web services", "ec2", "s3", "lambda"],
                "gcp": ["gcp", "google cloud", "bigquery", "cloud storage"],
                "azure": ["azure", "microsoft azure", "synapse"],
                "docker": ["docker", "container", "containers"],
                "kubernetes": ["kubernetes", "k8s"],
                "terraform": ["terraform", "iac"],
            },
            "bi_analytics": {
                "power_bi": ["power bi", "powerbi", "pbi"],
                "tableau": ["tableau", "tableau desktop"],
                "metabase": ["metabase"],
                "looker": ["looker", "looker studio"],
                "excel": ["excel", "power query", "power pivot"],
                "qlik": ["qlik", "qlik sense"],
            },
            "data_science": {
                "machine_learning": ["machine learning", "ml", "apprentissage automatique"],
                "deep_learning": ["deep learning", "dl", "réseaux de neurones"],
                "nlp": ["nlp", "traitement du langage naturel"],
                "computer_vision": ["computer vision", "vision par ordinateur"],
                "tensorflow": ["tensorflow", "tf"],
                "pytorch": ["pytorch", "torch"],
                "scikit_learn": ["scikit-learn", "sklearn", "scikit learn"],
                "pandas": ["pandas"],
                "numpy": ["numpy"],
            },
            "methodologies": {
                "agile": ["agile", "scrum", "kanban"],
                "git": ["git", "github", "gitlab"],
                "ci_cd": ["ci/cd", "cicd", "continuous integration"],
                "devops": ["devops"],
                "jira": ["jira"],
            },
            "databases": {
                "mongodb": ["mongodb", "mongo"],
                "redis": ["redis"],
                "elasticsearch": ["elasticsearch", "elastic search"],
                "sql_server": ["sql server", "mssql"],
                "mysql": ["mysql"],
                "postgresql": ["postgresql", "postgres"],
                "oracle": ["oracle database", "oracle"],
                "cassandra": ["cassandra"],
            },
            "cybersecurity": {
                "soc": ["soc", "security operations center"],
                "siem": ["siem", "splunk"],
                "pentest": ["pentest", "penetration testing"],
                "iso27001": ["iso 27001", "iso27001"],
            },
        }
    }


def generate_entreprises_csv() -> list[dict]:
    """
    Génère un référentiel réaliste d'entreprises IT au Maroc.

    Hypothèse de conception :
    - Le référentiel combine des entreprises connues du marché IT marocain
      et des entreprises fictives réalistes.
    - L'objectif est de couvrir plusieurs villes marocaines afin de permettre
      les analyses géographiques demandées par le projet.
    """
    entreprises = [
        # Casablanca
        ("Capgemini Maroc", "Services IT", "Grande Entreprise", "Casablanca", "https://www.capgemini.com/ma-en", "Conseil"),
        ("Inetum Maroc", "Services numériques", "Grande Entreprise", "Casablanca", "https://www.inetum.com", "SSII"),
        ("HPS", "Paiement électronique", "Grande Entreprise", "Casablanca", "https://www.hps-worldwide.com", "Produit"),
        ("Orange Business Maroc", "Télécom & Cloud", "Grande Entreprise", "Casablanca", "https://www.orange-business.com", "Telecom"),
        ("Atos Maroc", "Services IT", "Grande Entreprise", "Casablanca", "https://atos.net", "SSII"),
        ("Leyton Maroc", "Conseil & Innovation", "ETI", "Casablanca", "https://leyton.com", "Conseil"),
        ("DXC Technology Maroc", "Services IT", "Grande Entreprise", "Casablanca", "https://dxc.com", "SSII"),
        ("Sopra Steria Maroc", "Transformation digitale", "Grande Entreprise", "Casablanca", "https://www.soprasteria.com", "Conseil"),
        ("Dell Technologies Morocco", "Technologie", "Grande Entreprise", "Casablanca", "https://www.dell.com", "Produit"),
        ("IBM Maroc", "Technologie & Conseil", "Grande Entreprise", "Casablanca", "https://www.ibm.com", "Conseil"),
        ("Oracle Maroc", "Logiciels & Cloud", "Grande Entreprise", "Casablanca", "https://www.oracle.com", "Produit"),
        ("Microsoft Morocco", "Cloud & Logiciels", "Grande Entreprise", "Casablanca", "https://www.microsoft.com", "Produit"),
        ("Ericsson Maroc", "Télécom", "Grande Entreprise", "Casablanca", "https://www.ericsson.com", "Telecom"),
        ("inwi", "Télécom", "Grande Entreprise", "Casablanca", "https://www.inwi.ma", "Telecom"),
        ("Attijariwafa Bank IT", "Banque", "Grande Entreprise", "Casablanca", "https://www.attijariwafabank.com", "Banque"),
        ("BMCE Bank IT", "Banque", "Grande Entreprise", "Casablanca", "https://www.bankofafrica.ma", "Banque"),
        ("CIH Bank IT", "Banque", "Grande Entreprise", "Casablanca", "https://www.cihbank.ma", "Banque"),
        ("Casa Digital Factory", "Digital", "ETI", "Casablanca", "https://example.com", "SSII"),
        ("Atlas Cloud Services", "Cloud", "PME", "Casablanca", "https://example.com", "Conseil"),
        ("Casa Data Consulting", "Data & BI", "PME", "Casablanca", "https://example.com", "Conseil"),

        # Rabat
        ("SQLI Maroc", "Digital & IT", "Grande Entreprise", "Rabat", "https://www.sqli.com", "SSII"),
        ("Cegedim Maroc", "Santé & Logiciels", "ETI", "Rabat", "https://www.cegedim.com", "Produit"),
        ("ALTEN Maroc", "Ingénierie & IT", "Grande Entreprise", "Rabat", "https://www.alten.com", "Conseil"),
        ("Huawei Technologies Morocco", "Télécom & Cloud", "Grande Entreprise", "Rabat", "https://www.huawei.com", "Telecom"),
        ("Maroc Telecom", "Télécom", "Grande Entreprise", "Rabat", "https://www.iam.ma", "Telecom"),
        ("Bank Al-Maghrib IT", "Banque", "Grande Entreprise", "Rabat", "https://www.bkam.ma", "Banque"),
        ("Crédit Agricole du Maroc IT", "Banque", "Grande Entreprise", "Rabat", "https://www.creditagricole.ma", "Banque"),
        ("Rabat Analytics Lab", "Data Analytics", "Startup", "Rabat", "https://example.com", "Produit"),
        ("Rabat Cloud Engineering", "Cloud", "PME", "Rabat", "https://example.com", "Conseil"),
        ("Atlas GovTech Solutions", "Services numériques", "ETI", "Rabat", "https://example.com", "Produit"),

        # Tanger
        ("Mexora Analytics", "E-commerce", "ETI", "Tanger", "https://example.com", "Produit"),
        ("TangerTech Solutions", "Services IT", "PME", "Tanger", "https://example.com", "SSII"),
        ("North Data Factory", "Data & BI", "Startup", "Tanger", "https://example.com", "Produit"),
        ("Tanger Digital Services", "Transformation digitale", "PME", "Tanger", "https://example.com", "Conseil"),
        ("Tangier Software Hub", "Développement logiciel", "PME", "Tanger", "https://example.com", "SSII"),
        ("Detroit Data Morocco", "Data Engineering", "Startup", "Tanger", "https://example.com", "Produit"),
        ("Med Port Tech", "Logistique & IT", "ETI", "Tanger", "https://example.com", "Autre"),

        # Tetouan
        ("NTT DATA Morocco", "Conseil IT", "Grande Entreprise", "Tetouan", "https://www.nttdata.com", "Conseil"),
        ("Tetouan Web Services", "Web", "PME", "Tetouan", "https://example.com", "SSII"),
        ("Tetouan Digital Lab", "Digital", "Startup", "Tetouan", "https://example.com", "Produit"),
        ("North Cloud Tetouan", "Cloud", "PME", "Tetouan", "https://example.com", "Conseil"),
        ("Rif Software Solutions", "Développement logiciel", "PME", "Tetouan", "https://example.com", "SSII"),

        # Marrakech
        ("Marrakech Tech Hub", "Logiciels", "Startup", "Marrakech", "https://example.com", "Produit"),
        ("Marrakech Digital Agency", "Digital", "PME", "Marrakech", "https://example.com", "Conseil"),
        ("Atlas Tourism Tech", "Tourisme & IT", "Startup", "Marrakech", "https://example.com", "Produit"),
        ("Red City Software", "Développement logiciel", "PME", "Marrakech", "https://example.com", "SSII"),
        ("Marrakech BI Services", "BI & Analytics", "PME", "Marrakech", "https://example.com", "Conseil"),

        # Fes
        ("Fes Software House", "Développement logiciel", "PME", "Fes", "https://example.com", "SSII"),
        ("Fes Data Lab", "Data Analytics", "Startup", "Fes", "https://example.com", "Produit"),
        ("Atlas AI Fes", "IA", "Startup", "Fes", "https://example.com", "Produit"),
        ("Fes Digital Services", "Services IT", "PME", "Fes", "https://example.com", "SSII"),
        ("Smart Medina Tech", "Smart City", "PME", "Fes", "https://example.com", "Autre"),

        # Agadir
        ("Agadir Data Services", "Data", "PME", "Agadir", "https://example.com", "Conseil"),
        ("Souss Tech Solutions", "Services IT", "PME", "Agadir", "https://example.com", "SSII"),
        ("Agadir Cloud Factory", "Cloud", "Startup", "Agadir", "https://example.com", "Produit"),
        ("Souss Analytics", "BI & Analytics", "PME", "Agadir", "https://example.com", "Conseil"),
        ("Agadir Web Studio", "Web", "PME", "Agadir", "https://example.com", "SSII"),

        # Oujda
        ("Oujda AI Lab", "IA", "Startup", "Oujda", "https://example.com", "Produit"),
        ("Oriental Digital Services", "Services IT", "PME", "Oujda", "https://example.com", "SSII"),
        ("Oujda Data Consulting", "Data", "PME", "Oujda", "https://example.com", "Conseil"),
        ("Oriental Cloud Lab", "Cloud", "Startup", "Oujda", "https://example.com", "Produit"),
        ("Oujda Software Center", "Développement logiciel", "PME", "Oujda", "https://example.com", "SSII"),

        # Kenitra
        ("Kenitra Dev Center", "Services IT", "PME", "Kenitra", "https://example.com", "SSII"),
        ("Gharb Digital Factory", "Digital", "PME", "Kenitra", "https://example.com", "Conseil"),
        ("Kenitra Analytics", "Data Analytics", "Startup", "Kenitra", "https://example.com", "Produit"),
        ("AutoTech Kenitra", "Automobile & IT", "ETI", "Kenitra", "https://example.com", "Autre"),
        ("Kenitra Cloud Services", "Cloud", "PME", "Kenitra", "https://example.com", "Conseil"),

        # Meknes
        ("Meknes Software Lab", "Développement logiciel", "PME", "Meknes", "https://example.com", "SSII"),
        ("Meknes Data Services", "Data", "Startup", "Meknes", "https://example.com", "Produit"),
        ("Ismailia Tech Consulting", "Conseil IT", "PME", "Meknes", "https://example.com", "Conseil"),
        ("Meknes BI Factory", "BI & Analytics", "PME", "Meknes", "https://example.com", "Conseil"),
        ("AgroTech Meknes", "AgriTech & IT", "Startup", "Meknes", "https://example.com", "Produit"),

        # Mohammedia
        ("Mohammedia Digital Services", "Services IT", "PME", "Mohammedia", "https://example.com", "SSII"),
        ("Casa North Tech", "Digital", "PME", "Mohammedia", "https://example.com", "Conseil"),
        ("Mohammedia Data Lab", "Data Analytics", "Startup", "Mohammedia", "https://example.com", "Produit"),
        ("Zenata Cloud Solutions", "Cloud", "PME", "Mohammedia", "https://example.com", "Conseil"),
        ("Atlantic Software Mohammedia", "Développement logiciel", "PME", "Mohammedia", "https://example.com", "SSII"),

        # El Jadida
        ("El Jadida Tech Services", "Services IT", "PME", "El_Jadida", "https://example.com", "SSII"),
        ("Mazagan Digital Lab", "Digital", "Startup", "El_Jadida", "https://example.com", "Produit"),
        ("Jorf Tech Analytics", "Industrie & Data", "ETI", "El_Jadida", "https://example.com", "Autre"),
        ("El Jadida Cloud Services", "Cloud", "PME", "El_Jadida", "https://example.com", "Conseil"),
        ("Mazagan Software House", "Développement logiciel", "PME", "El_Jadida", "https://example.com", "SSII"),
    ]

    return [
        {
            "nom_entreprise": nom,
            "secteur": secteur,
            "taille": taille,
            "ville_siege": ville,
            "site_web": site,
            "type": type_
        }
        for nom, secteur, taille, ville, site, type_ in entreprises
    ]


def random_date_between(start: datetime, end: datetime) -> datetime:
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))


def maybe_incoherent_city(ville: str) -> str:
    variants = {
        "Casablanca": ["Casablanca", "CASABLANCA", "casa", "Casa", "Cblanca"],
        "Rabat": ["Rabat", "RABAT", "rbat", "Rabatt"],
        "Tanger": ["Tanger", "TANGER", "tanger", "Tanja", "TNG"],
        "Marrakech": ["Marrakech", "MARRAKECH", "Marrakesh", "marrakech"],
        "Fes": ["Fes", "Fès", "FES", "fez"],
        "Agadir": ["Agadir", "AGADIR", "agadir"],
        "Oujda": ["Oujda", "OUJDA", "oujda"],
        "Kenitra": ["Kenitra", "Kénitra", "KENITRA", "kenitra"],
        "Tetouan": ["Tetouan", "Tétouan", "TETOUAN", "tetouan"],
        "Meknes": ["Meknes", "Meknès", "MEKNES", "meknes"],
        "Mohammedia": ["Mohammedia", "MOHAMMEDIA", "mohammedia"],
        "El_Jadida": ["El Jadida", "EL JADIDA", "eljadida"],
    }
    return random.choice(variants.get(ville, [ville]))


def random_contract() -> str:
    return random.choice([
        "CDI", "cdi", "Contrat à durée indéterminée", "Permanent",
        "CDD", "Freelance", "Stage", "Contrat projet"
    ])


def random_experience(profile: str) -> str | None:
    options_common = [
        "3-5 ans", "3 à 5 ans", "min 3 ans", "2 ans minimum",
        "Débutant accepté", "Junior", "Senior (7+ ans)", None,
        "5 ans et plus", "1-2 ans", "Confirmé"
    ]
    if profile in ["Data Engineer", "Data Scientist", "Cloud Engineer"]:
        return random.choice(["3-5 ans", "min 3 ans", "5 ans et plus", "Senior (7+ ans)", "2 ans minimum", None])
    return random.choice(options_common)


def random_salary(profile: str) -> str | None:
    if random.random() < 0.22:
        return random.choice(["Selon profil", "Confidentiel", None, ""])

    base = {
        "Data Engineer": (12000, 28000),
        "Data Analyst": (8000, 20000),
        "Data Scientist": (13000, 30000),
        "Développeur Full Stack": (9000, 24000),
        "Développeur Backend": (9000, 23000),
        "Développeur Frontend": (8000, 20000),
        "DevOps / SRE": (14000, 32000),
        "Cloud Engineer": (14000, 34000),
        "Cybersécurité": (12000, 28000),
        "Chef de Projet IT": (15000, 35000),
        "Architecte IT": (22000, 45000),
    }.get(profile, (7000, 18000))

    mn = random.randint(base[0] // 1000, base[1] // 1000) * 1000
    mx = mn + random.choice([3000, 5000, 7000, 10000])

    formats = [
        f"{mn}-{mx} MAD",
        f"{mn // 1000}K-{mx // 1000}K",
        f"{mn} à {mx} DH",
        f"{round(mn / 10.8)}-{round(mx / 10.8)} EUR"
    ]
    return random.choice(formats)


def random_title(profile: str) -> str:
    titles = {
        "Data Engineer": [
            "Data Engineer", "Data Eng.", "Ingénieur Big Data", "Dev Data",
            "Ingénieur Data Pipeline", "ETL Developer", "Data Engineer Junior"
        ],
        "Data Analyst": [
            "Data Analyst", "Analyste Data", "Développeur BI", "BI Analyst",
            "Consultant Power BI", "Business Intelligence Analyst"
        ],
        "Data Scientist": [
            "Data Scientist", "Machine Learning Engineer", "Ingénieur IA",
            "NLP Engineer", "Data Science Consultant"
        ],
        "Développeur Full Stack": [
            "Développeur Full Stack React/Node.js", "Fullstack Developer",
            "Ingénieur Full Stack JavaScript", "Développeur MERN"
        ],
        "Développeur Backend": [
            "Backend Developer", "Développeur Backend Java", "Ingénieur Backend",
            "Développeur API"
        ],
        "Développeur Frontend": [
            "Frontend Developer", "Développeur Front React", "Angular Developer",
            "Intégrateur Frontend"
        ],
        "DevOps / SRE": [
            "DevOps Engineer", "Ingénieur DevOps", "SRE", "Site Reliability Engineer"
        ],
        "Cloud Engineer": [
            "Cloud Engineer", "AWS Engineer", "Azure Cloud Consultant",
            "Ingénieur Cloud"
        ],
        "Cybersécurité": [
            "Analyste SOC", "Ingénieur Cybersécurité", "Pentester", "Consultant Sécurité"
        ],
        "Chef de Projet IT": [
            "Chef de Projet IT", "Scrum Master", "Project Manager IT"
        ],
        "Architecte IT": [
            "Architecte Technique", "Architecte Data", "Architecte Cloud"
        ]
    }
    return random.choice(titles[profile])


def skills_for_profile(profile: str) -> list[str]:
    mapping = {
        "Data Engineer": ["Python", "SQL", "Spark", "Airflow", "Kafka", "dbt", "Docker", "AWS", "Git"],
        "Data Analyst": ["SQL", "Python", "Power BI", "Tableau", "Excel", "Metabase", "Looker Studio"],
        "Data Scientist": ["Python", "Machine Learning", "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "NLP"],
        "Développeur Full Stack": ["React", "Node.js", "JavaScript", "PostgreSQL", "Docker", "Git", "Agile"],
        "Développeur Backend": ["Java", "Spring Boot", "SQL", "PostgreSQL", "Docker", "Git"],
        "Développeur Frontend": ["React", "Angular", "Vue.js", "JavaScript", "TypeScript", "Git"],
        "DevOps / SRE": ["Docker", "Kubernetes", "Terraform", "AWS", "CI/CD", "Git"],
        "Cloud Engineer": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform"],
        "Cybersécurité": ["SOC", "SIEM", "Pentest", "ISO 27001", "Splunk"],
        "Chef de Projet IT": ["Agile", "Scrum", "Jira", "Power BI", "Git"],
        "Architecte IT": ["Cloud", "AWS", "Azure", "Data Lake", "Kubernetes", "PostgreSQL"],
    }
    return mapping.get(profile, ["SQL", "Git"])


def random_competences_brut(skills: list[str]) -> str:
    selected = random.sample(skills, k=random.randint(3, min(len(skills), 7)))
    sep = random.choice([", ", " / ", " • ", "\n", " | "])

    if random.random() < 0.20:
        return "Compétences demandées : " + sep.join(selected) + ". Une expérience projet est appréciée."

    return sep.join(selected)


def generate_description(profile: str, skills: list[str]) -> str:
    selected = random.sample(skills, k=random.randint(3, min(len(skills), 6)))
    phrases = [
        f"Nous recherchons un profil {profile} pour renforcer notre équipe IT au Maroc.",
        f"Le candidat devra maîtriser {', '.join(selected)}.",
        "Une bonne communication en français est requise.",
        "La connaissance de l'anglais technique est appréciée.",
        "Le poste implique la participation à des projets stratégiques et à des ateliers avec les équipes métier.",
        "Une expérience en méthode Agile et l'utilisation de Git sont fortement appréciées."
    ]

    if random.random() < 0.15:
        phrases.append("La description contient parfois des informations peu structurées comme des listes, retours à la ligne et séparateurs incohérents.")

    return " ".join(phrases)


def generate_offres(entreprises: list[dict]) -> dict:
    sources = ["rekrute", "marocannonce", "linkedin"]

    source_prefix = {
        "rekrute": "RK",
        "marocannonce": "MA",
        "linkedin": "LI",
    }

    profiles = [
        "Data Engineer", "Data Analyst", "Data Scientist",
        "Développeur Full Stack", "Développeur Backend", "Développeur Frontend",
        "DevOps / SRE", "Cloud Engineer", "Cybersécurité",
        "Chef de Projet IT", "Architecte IT"
    ]

    profile_weights = [0.13, 0.16, 0.08, 0.16, 0.12, 0.09, 0.08, 0.06, 0.04, 0.05, 0.03]

    start = datetime(2023, 1, 1)
    end = datetime(2024, 11, 30)

    offres = []

    for i in range(1, NB_OFFRES + 1):
        source = random.choices(sources, weights=[0.40, 0.25, 0.35], k=1)[0]
        profile = random.choices(profiles, weights=profile_weights, k=1)[0]
        entreprise = random.choice(entreprises)

        pub_date = random_date_between(start, end)
        expiration = pub_date + timedelta(days=random.choice([15, 30, 45, 60]))

        if random.random() < 0.025:
            expiration = pub_date - timedelta(days=random.randint(1, 10))

        date_formats = [
            pub_date.strftime("%Y-%m-%d"),
            pub_date.strftime("%d/%m/%Y"),
            pub_date.strftime("%b %d %Y"),
        ]
        date_publication = random.choice(date_formats)

        ville = maybe_incoherent_city(entreprise["ville_siege"])
        skills = skills_for_profile(profile)

        offre = {
            "id_offre": f"{source_prefix[source]}-{pub_date.year}-{i:05d}",
            "source": source,
            "titre_poste": random_title(profile),
            "description": generate_description(profile, skills),
            "competences_brut": random_competences_brut(skills),
            "entreprise": entreprise["nom_entreprise"],
            "ville": ville,
            "type_contrat": random_contract(),
            "experience_requise": random_experience(profile),
            "salaire_brut": random_salary(profile),
            "niveau_etudes": random.choice(["Bac+2", "Bac+3", "Bac+5", "Ingénieur", "Master", None]),
            "secteur": random.choice(["Informatique / Télécom", "Banque", "Conseil", "E-commerce", "Services numériques"]),
            "date_publication": date_publication,
            "date_expiration": expiration.strftime("%Y-%m-%d"),
            "nb_postes": random.choice([1, 1, 1, 2, 3, 5]),
            "teletravail": random.choice(["Présentiel", "Hybride", "Télétravail", "Remote", None]),
            "langue_requise": random.choice([
                ["Français"],
                ["Français", "Anglais"],
                ["Français", "Anglais", "Espagnol"],
                ["Anglais"],
            ])
        }

        offres.append(offre)

    return {
        "metadata": {
            "projet": "Mexora RH Intelligence",
            "description": "Dataset synthétique réaliste d'offres d'emploi IT au Maroc",
            "nb_offres": NB_OFFRES,
            "periode": "janvier 2023 - novembre 2024",
            "sources": sources,
            "generation": datetime.now().isoformat(),
            "note": "Données générées pour un miniprojet académique, avec anomalies intentionnelles."
        },
        "offres": offres
    }


def save_referentiel(referentiel: dict) -> None:
    path = REF_DIR / "referentiel_competences_it.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(referentiel, f, ensure_ascii=False, indent=2)
    print(f"[OK] Référentiel compétences généré : {path}")


def save_entreprises(entreprises: list[dict]) -> None:
    path = REF_DIR / "entreprises_it_maroc.csv"
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["nom_entreprise", "secteur", "taille", "ville_siege", "site_web", "type"]
        )
        writer.writeheader()
        writer.writerows(entreprises)
    print(f"[OK] Référentiel entreprises généré : {path}")


def save_offres(dataset: dict) -> None:
    path = RAW_DIR / "offres_emploi_it_maroc.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"[OK] Dataset offres généré : {path}")
    print(f"[OK] Nombre d'offres : {len(dataset['offres'])}")


def main() -> None:
    referentiel = generate_referentiel_competences()
    entreprises = generate_entreprises_csv()
    offres = generate_offres(entreprises)

    save_referentiel(referentiel)
    save_entreprises(entreprises)
    save_offres(offres)

    print("[DONE] Fichiers sources générés avec succès.")


if __name__ == "__main__":
    main()