Pipeline de donnees YouTube - ETL avec Docker et Airflow
Description

Ce projet extrait les donnees d'une chaine YouTube via l'API YouTube Data v3, les stocke dans une base PostgreSQL organisee en deux zones (Staging et Core), et automatise l'ensemble avec Apache Airflow. Tout l'environnement tourne dans Docker.

Architecture
YouTube Data API v3
        |
        v
   DAG 1 : youtube_extraction
   (recupere chaine -> playlist -> videos -> JSON)
        |
        v
   Fichier JSON (data/YTdataYYYY-MM-DD.json)
        |
        v
   DAG 2 : warehouse_update
   (charge Staging -> transforme -> charge Core)
        |
        v
   PostgreSQL
   - table staging : donnees brutes, proches du JSON
   - table core : donnees nettoyees, pretes pour l'analyse
Staging vs Core
staging : zone de depot. Les donnees sont chargees telles que l'API les retourne (durees en format ISO 8601, compteurs en texte). Insertion et mise a jour uniquement.
core : zone finale, utilisee pour l'analyse. Les donnees sont nettoyees et typees correctement (durees en secondes, compteurs en entiers). Insertion, mise a jour, et suppression des videos qui ne sont plus presentes dans la source.
Stack technique
Python 3.10
Apache Airflow 2.9.2 (CeleryExecutor)
PostgreSQL 13
Redis (broker Celery)
Docker / Docker Compose
SQLAlchemy / PostgresHook pour l'acces base de donnees
requests pour l'appel a l'API YouTube
Structure du projet
youtube-etl-pipeline/
├── docker-compose.yaml
├── Dockerfile
├── requirements.txt
├── dags/
│   ├── youtube_extraction.py
│   └── warehouse_update.py
├── include/
│   ├── youtube_client.py     (appels API YouTube)
│   ├── json_writer.py        (ecriture/lecture du fichier JSON)
│   ├── staging_loader.py     (sync table staging)
│   ├── transform.py          (transformation des donnees)
│   └── core_loader.py        (sync table core)
├── data/                  (fichiers JSON generes)
├── docker/postgres/
│   └── init-multiple-databases.sh
├── logs/
├── plugins/
└── config/
Installation et lancement
Prerequis
Docker Desktop installe et lance
Une cle API YouTube Data v3 (Google Cloud Console)
Etapes
Cloner le depot.
Creer un fichier .env a la racine avec les variables suivantes (voir .env.example si present, sinon les creer manuellement) :
AIRFLOW_UID
FERNET_KEY
AIRFLOW_WWW_USER_USERNAME
AIRFLOW_WWW_USER_PASSWORD
API_KEY (cle YouTube Data API v3)
CHANNEL_HANDLE (ex: @nomdelachaine)
POSTGRES_CONN_HOST, POSTGRES_CONN_PORT, POSTGRES_CONN_USERNAME, POSTGRES_CONN_PASSWORD
METADATA_DATABASE_NAME, METADATA_DATABASE_USERNAME, METADATA_DATABASE_PASSWORD
CELERY_BACKEND_NAME, CELERY_BACKEND_USERNAME, CELERY_BACKEND_PASSWORD
ELT_DATABASE_NAME, ELT_DATABASE_USERNAME, ELT_DATABASE_PASSWORD
Construire l'image :
   docker build -t youtube-airflow .
Initialiser Airflow :
   docker compose up airflow-init
Lancer l'ensemble des services :
   docker compose up -d
Ouvrir l'interface Airflow : http://localhost:8080
Utilisation
Dans l'interface Airflow, activer le DAG youtube_extraction.
Le declencher manuellement (ou attendre son planning).
Le DAG youtube_extraction extrait les donnees et declenche automatiquement le DAG warehouse_update a la fin.
Verifier les tables staging et core dans PostgreSQL pour confirmer le chargement.
Statut actuel
 Environnement Docker + Airflow fonctionnel
 Extraction des donnees YouTube (DAG 1)
 Chargement Staging (insert/update)
 Chargement Core (insert/update/delete)
 Transformation complete des donnees (en cours)
 Tests automatises
 Dashboard Power BI (bonus)
Auteur

Mohammed Oughlan
