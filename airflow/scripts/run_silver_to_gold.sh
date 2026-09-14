#!/bin/bash
# ------------------------------------------------------------------
# Script d'automatisation Airflow - Étape 3 : Calcul des Tables Gold
# ------------------------------------------------------------------
set -e

echo "⏳ [Airflow] Lancement de la transformation Silver → Gold..."

# Exécution de votre script de modélisation Gold (ajustez le nom du script si nécessaire)
spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --conf spark.driver.bindAddress=0.0.0.0 \
  --conf spark.driver.host=spark-master \
  /opt/jobs/gold/build_gold.py

echo "✅ [Airflow] Tables Gold générées et disponibles."
