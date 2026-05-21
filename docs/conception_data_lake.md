# Conception de l’Architecture Data Lake  
## Mexora RH Intelligence — Analyse du Marché de l’Emploi IT au Maroc

### 1. Objectif général

L’objectif du projet est de concevoir un Data Lake local permettant de stocker, nettoyer et analyser 5 000 offres d’emploi IT marocaines provenant de Rekrute, MarocAnnonce et LinkedIn Maroc, sur la période janvier 2023 à novembre 2024. L’architecture retenue suit une organisation en trois zones : Bronze, Silver et Gold. Cette séparation permet de conserver une trace fidèle des données brutes, de produire des données nettoyées et typées, puis de construire des tables analytiques directement exploitables avec DuckDB, Jupyter Notebook et le rapport stratégique destiné au DRH de Mexora.

---

### 2. Justification des formats de stockage


| Zone | Format choisi | Pourquoi ce format ? | Pourquoi pas les autres ? |
|---|---|---|---|
| Bronze | JSON | Le JSON conserve les offres dans un format proche de la donnée collectée par scraping. Il garde les champs textuels, les listes comme `langue_requise`, les valeurs manquantes et les anomalies d’origine. Il est donc adapté à une zone brute immuable. | Le CSV est trop limité pour représenter correctement des données semi-structurées. Le Parquet impose une logique plus structurée et convient mieux aux données nettoyées qu’aux données brutes. |
| Silver | Parquet | Le Parquet est adapté aux données nettoyées, standardisées et typées. Il est compressé, performant et optimisé pour les traitements analytiques avec pandas, pyarrow et DuckDB. | Le JSON devient lourd et moins performant pour l’analyse. Le CSV ne conserve pas correctement les types et augmente les risques d’erreurs sur les dates, nombres et valeurs manquantes. |
| Gold | Parquet | Les tables Gold sont des tables analytiques agrégées : compétences, salaires, villes, entreprises recruteurs et tendances mensuelles. Le Parquet permet des lectures rapides et efficaces par colonnes. | Le JSON et le CSV sont moins adaptés aux requêtes analytiques répétées, aux agrégations et aux lectures sélectives utilisées dans DuckDB. |

---

### 3. Pourquoi conserver les données brutes en Bronze sans les modifier ?

La zone Bronze doit contenir les données exactement telles qu’elles ont été reçues. Elle est immuable : une fois les fichiers chargés, ils ne sont jamais modifiés manuellement. Cette règle est essentielle pour garantir la traçabilité et la reproductibilité du projet.

Si les données brutes sont modifiées directement, plusieurs risques apparaissent : perte de l’état original, impossibilité de vérifier une erreur de transformation, difficulté à rejouer le pipeline, confusion entre données sources et données nettoyées, et perte de confiance dans les résultats. En conservant une Bronze intacte, il devient possible de revenir à la source, de corriger une règle de nettoyage et de reconstruire Silver et Gold proprement.

---

### 4. Schema-on-read et différence avec le Data Warehouse du miniprojet 1

Le Data Lake repose sur le principe du `schema-on-read`. Cela signifie que les données sont d’abord stockées dans leur format d’origine, puis leur structure est interprétée au moment de la lecture et du traitement. Ce fonctionnement est adapté aux données semi-structurées ou imparfaites, comme les offres d’emploi issues du scraping.

À l’inverse, le Data Warehouse du miniprojet 1 repose sur une logique `schema-on-write`. Le schéma est défini avant l’intégration des données : tables, colonnes, types, clés et contraintes. Les données doivent donc être nettoyées et conformes avant d’être chargées. Le Data Warehouse est plus strict, tandis que le Data Lake est plus flexible. Dans ce projet, cette flexibilité est importante car les champs comme `salaire_brut`, `experience_requise`, `ville` ou `competences_brut` contiennent des formats hétérogènes.

---

### 5. Définition du partitionnement

En zone Bronze, la partition est définie par `source` et par `mois`. Le chemin suit la logique :

`bronze/source/annee_mois/offres_raw.json`

Exemple :

`bronze/rekrute/2024_08/offres_raw.json`

Ce choix permet de séparer clairement les données selon leur origine : Rekrute, MarocAnnonce ou LinkedIn Maroc. Le partitionnement mensuel facilite aussi le suivi temporel des publications et permet de recharger ou vérifier un mois précis sans parcourir toute la base brute.

En zone Silver, la partition logique est définie par `ville` et par `mois`. Le chemin prévu est :

`silver/offres_clean/ville=Casablanca/mois=2024_08/offres_clean.parquet`

Ce choix est cohérent avec les besoins analytiques du projet. Le DRH de Mexora veut comparer les opportunités IT entre Tanger, Casablanca, Rabat et les autres villes. Le partitionnement par ville accélère ces analyses géographiques, tandis que le partitionnement par mois facilite l’étude des tendances du marché entre 2023 et 2024.

En zone Gold, les données ne sont pas organisées par partitions détaillées mais sous forme de tables analytiques prêtes à l’emploi : `top_competences.parquet`, `salaires_par_profil.parquet`, `offres_par_ville.parquet`, `entreprises_recruteurs.parquet` et `tendances_mensuelles.parquet`.

---

### 6. Gouvernance et prévention du Data Swamp

Un Data Lake peut devenir un Data Swamp si les fichiers sont déposés sans organisation, sans règles de nommage, sans documentation et sans contrôle qualité. Pour éviter cela, plusieurs règles de gouvernance sont appliquées.

Premièrement, les zones Bronze, Silver et Gold sont strictement séparées. Bronze conserve les données brutes, Silver contient les données nettoyées et Gold contient les indicateurs analytiques. Deuxièmement, les fichiers Bronze sont considérés comme immuables. Troisièmement, les transformations appliquées seront documentées dans `rapport_pipeline.md` : règle métier, nombre de lignes avant/après, cas limites et traitement adopté.

Des règles de nommage sont également imposées : noms de dossiers normalisés, partitionnement par source/mois et par ville/mois, formats cohérents et fichiers clairement identifiés. Les métadonnées d’ingestion seront conservées : source, date d’ingestion, partition et nombre d’offres. Enfin, des contrôles qualité seront appliqués sur les champs critiques : dates incohérentes, villes non standardisées, salaires invalides, expériences non interprétables, contrats non normalisés et compétences non détectées.

Cette gouvernance permet de garantir un Data Lake lisible, traçable, reproductible et exploitable pour l’analyse du marché IT marocain.