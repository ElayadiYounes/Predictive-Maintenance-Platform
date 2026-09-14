#!/bin/bash
# ------------------------------------------------------------------
# Script d'automatisation Airflow - Étape 4 : XGBOOST ML
# ------------------------------------------------------------------


set -e

echo "[Airflow] Démarrage du ré-entraînement  de XGBOOST..."

docker compose \
    --env-file .env.dev \
    -f docker-compose.dev.yml \
    exec -T ml \
    python /app/jobs/ml/run_xgboost_rul.py

echo "[Airflow] Entraînement xgboost terminé avec succès."

