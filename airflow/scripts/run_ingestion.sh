#!/bin/bash
# ------------------------------------------------------------------
# Script d'automatisation Airflow - Étape 1 : Ingestion Bronze
# ------------------------------------------------------------------

# Force l'arrêt immédiat du script au moindre problème technique
set -e

echo "⏳ [Airflow] Déclenchement de l'extraction des inspections..."

cd /opt/airflow/

# Exécution non-interactive directe du script Python dans le conteneur
docker compose \
    --env-file .env.dev \
    -f docker-compose.dev.yml \
    exec -T ingestion \
    python /app/jobs/bronze/db/extract_inspection.py

echo "✅ [Airflow] Ingestion Bronze terminée avec succès."

