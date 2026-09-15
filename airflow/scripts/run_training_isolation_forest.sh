#!/bin/bash
# ------------------------------------------------------------------
# Script d'automatisation Airflow - Étape 3 : Isolation forest ML
# ------------------------------------------------------------------


set -e

echo "[Airflow] Démarrage du ré-entraînement  de l'Isolation Forest..."

cd /opt/airflow/

docker compose \
    --env-file .env.dev \
    -f docker-compose.dev.yml \
    exec -T ml \
    python /app/jobs/ml/run_isolation_forest.py

echo "[Airflow] Entraînement Isolation Forest terminé avec succès."

