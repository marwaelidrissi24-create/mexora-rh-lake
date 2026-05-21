# Rapport de traitement — Pipeline Mexora RH Intelligence

Ce document trace les transformations appliquées pendant l'Étape 2 du projet.


## Chargement depuis Bronze

- Date d'exécution : 2026-05-21T18:52:09
- Règle appliquée : Lecture de tous les fichiers offres_raw.json depuis la zone Bronze.
- Nombre de lignes avant : N/A
- Nombre de lignes après : 5000
- Détails / cas limites : Consolidation des partitions Bronze dans un DataFrame pandas unique.


## Normalisation des dates

- Date d'exécution : 2026-05-21T18:52:09
- Règle appliquée : Parsing explicite des formats de dates vers datetime, conservation des valeurs originales et détection publication > expiration.
- Nombre de lignes avant : 5000
- Nombre de lignes après : 5000
- Détails / cas limites : Dates publication invalides: 0. Dates incohérentes publication > expiration: 117.


## Normalisation des villes

- Date d'exécution : 2026-05-21T18:52:09
- Règle appliquée : Mapping des variantes de villes vers une valeur standardisée dans ville_std et rattachement à une région administrative.
- Nombre de lignes avant : 5000
- Nombre de lignes après : 5000
- Détails / cas limites : Villes non reconnues ou non renseignées: 0.


## Normalisation des contrats

- Date d'exécution : 2026-05-21T18:52:09
- Règle appliquée : Regroupement des variantes de contrat vers CDI, CDD, Freelance, Stage, Contrat projet, Autre ou Non renseigné.
- Nombre de lignes avant : 5000
- Nombre de lignes après : 5000
- Détails / cas limites : Distribution contrats: {'CDI': 2445, 'Stage': 671, 'Contrat projet': 655, 'CDD': 625, 'Freelance': 604}


## Normalisation des intitulés de poste

- Date d'exécution : 2026-05-21T18:52:09
- Règle appliquée : Classification regex des intitulés non standardisés vers des profils IT normalisés.
- Nombre de lignes avant : 5000
- Nombre de lignes après : 5000
- Détails / cas limites : Offres classées Autre IT: 0. Distribution profils: {'Data Analyst': 768, 'Développeur Frontend': 651, 'Data Engineer': 639, 'Développeur Full Stack': 619, 'Développeur Backend': 588, 'Data Scientist': 417, 'DevOps / SRE': 415, 'Cloud Engineer': 276, 'Chef de Projet IT': 242, 'Cybersécurité': 204, 'Architecte IT': 181}


## Normalisation des salaires

- Date d'exécution : 2026-05-21T18:52:10
- Règle appliquée : Extraction des montants, conversion K et EUR, calcul min/max/médiane, flag salaire_connu.
- Nombre de lignes avant : 5000
- Nombre de lignes après : 5000
- Détails / cas limites : Salaires connus et valides: 3873/5000 (77.46%). Taux EUR/MAD utilisé: 10.8.


## Normalisation de l'expérience

- Date d'exécution : 2026-05-21T18:52:11
- Règle appliquée : Parsing regex des formats d'expérience vers experience_min_ans et experience_max_ans.
- Nombre de lignes avant : 5000
- Nombre de lignes après : 5000
- Détails / cas limites : Expériences interprétables: 4428/5000 (88.56%).


## Enrichissement analytique Silver

- Date d'exécution : 2026-05-21T18:52:11
- Règle appliquée : Création de champs standardisés utiles pour Gold : source_std, teletravail_std, is_remote_or_hybrid, nb_postes typé.
- Nombre de lignes avant : 5000
- Nombre de lignes après : 5000
- Détails / cas limites : Aucune suppression de lignes. Les champs analytiques sont ajoutés pour faciliter les agrégations Gold.


## Contrôles qualité Silver

- Date d'exécution : 2026-05-21T18:52:11
- Règle appliquée : Ajout de flags qualité au lieu de supprimer les lignes, pour préserver la traçabilité.
- Nombre de lignes avant : 5000
- Nombre de lignes après : 5000
- Détails / cas limites : Résumé qualité: {'ville_inconnue': 0, 'salaire_inconnu': 1127, 'experience_inconnue': 572, 'date_publication_invalide': 0, 'date_incoherente': 117}


## Sauvegarde Silver

- Date d'exécution : 2026-05-21T18:52:14
- Règle appliquée : Sauvegarde des offres nettoyées en Parquet consolidé et en partitions ville/mois.
- Nombre de lignes avant : 5000
- Nombre de lignes après : 5000
- Détails / cas limites : Fichier consolidé: C:\Users\Surface PC\OneDrive\Desktop\mexora_rh_lake\data_lake_mexora_rh\silver\offres_clean\offres_clean.parquet. Partitions Parquet créées: 276.


## Extraction des compétences IT

- Date d'exécution : 2026-05-21T18:52:32
- Règle appliquée : Matching regex des alias du référentiel sur competences_brut et description. Une offre peut générer plusieurs lignes compétences.
- Nombre de lignes avant : 5000
- Nombre de lignes après : 30817
- Détails / cas limites : Offres avec au moins une compétence détectée: 5000/5000 (100.0%). Top compétences: {'agile': 2784, 'git': 2773, 'sql': 2614, 'docker': 2347, 'python': 1471, 'postgresql': 1426, 'aws': 1267, 'javascript': 1223, 'react': 1127, 'power_bi': 869}


## Sauvegarde des compétences extraites

- Date d'exécution : 2026-05-21T18:52:32
- Règle appliquée : Sauvegarde du résultat NLP Silver en Parquet dans silver/competences_extraites/competences.parquet.
- Nombre de lignes avant : 30817
- Nombre de lignes après : 30817
- Détails / cas limites : Fichier généré: C:\Users\Surface PC\OneDrive\Desktop\mexora_rh_lake\data_lake_mexora_rh\silver\competences_extraites\competences.parquet


## Construction des tables Gold

- Date d'exécution : 2026-05-21T18:52:33
- Règle appliquée : Agrégation analytique des données Silver avec DuckDB et sauvegarde en Parquet.
- Nombre de lignes avant : N/A
- Nombre de lignes après : 3073
- Détails / cas limites : Tables générées: {'top_competences': 127, 'salaires_par_profil': 482, 'offres_par_ville': 2129, 'entreprises_recruteurs': 82, 'tendances_mensuelles': 253}

