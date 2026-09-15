#!/bin/bash
# ------------------------------------------------------------------
# Script d'automatisation Airflow - Étape 3 : Calcul des Tables Gold
# ------------------------------------------------------------------
set -e

echo "⏳ [Airflow] Lancement de la transformation Silver → Gold..."

cd /opt/airflow/

# Exécution de votre script de modélisation Gold (ajustez le nom du script si nécessaire)
docker compose --env-file .env.dev -f docker-compose.dev.yml exec -T spark-master spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --conf spark.driver.bindAddress=0.0.0.0 \
  --conf spark.driver.host=spark-master \
  /app/jobs/gold/build_gold.py

echo "✅ [Airflow] Tables Gold générées et disponibles."
