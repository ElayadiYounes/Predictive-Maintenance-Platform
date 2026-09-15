#!/bin/bash
# ------------------------------------------------------------------
# Script d'automatisation Airflow - Étape 2 : Transformation Silver
# ------------------------------------------------------------------
set -e

echo "⏳ [Airflow] Lancement de la transformation Bronze → Silver..."

cd /opt/airflow

docker compose --env-file .env.dev -f docker-compose.dev.yml exec -T spark-master spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --conf spark.driver.bindAddress=0.0.0.0 \
  --conf spark.driver.host=spark-master \
  /app/jobs/silver/transform_inspection.py

echo "✅ [Airflow] Couche Silver mise à jour avec succès."
