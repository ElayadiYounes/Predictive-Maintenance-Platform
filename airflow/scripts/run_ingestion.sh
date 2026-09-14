#!/bin/bash
# ------------------------------------------------------------------
# Script d'automatisation Airflow - Étape 1 : Ingestion Bronze
# ------------------------------------------------------------------

# Force l'arrêt immédiat du script au moindre problème technique
set -e

echo "⏳ [Airflow] Déclenchement de l'extraction des inspections..."

# Exécution non-interactive directe du script Python dans le conteneur
python /opt/jobs/bronze/db/extract_inspection.py

echo "✅ [Airflow] Ingestion Bronze terminée avec succès."

