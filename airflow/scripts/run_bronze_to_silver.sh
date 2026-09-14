#!/bin/bash
# ------------------------------------------------------------------
# Script d'automatisation Airflow - Étape 2 : Transformation Silver
# ------------------------------------------------------------------
set -e

echo "⏳ [Airflow] Lancement de la transformation Bronze → Silver..."

spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --conf spark.driver.bindAddress=0.0.0.0 \
  --conf spark.driver.host=spark-master \
  /opt/jobs/silver/transform_inspection.py

echo "✅ [Airflow] Couche Silver mise à jour avec succès."
