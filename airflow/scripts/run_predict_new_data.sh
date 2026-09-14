#!/bin/bash
# ------------------------------------------------------------------
# Script d'automatisation Airflow - Étape 6: predire nouvelle donnees ML
# ------------------------------------------------------------------


set -e

echo "[Airflow] Démarrage du ré-entraînement  de Predict_new_Data..."

docker compose \
    --env-file .env.dev \
    -f docker-compose.dev.yml \
    exec -T ml \
    python /app/jobs/ml/predict_new_data.py

echo "[Airflow] Entraînement predict_new_data terminé avec succès."

