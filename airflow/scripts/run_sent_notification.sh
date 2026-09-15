#!/bin/bash
# ------------------------------------------------------------------
# Script Airflow - Notifications : Déclenchement automatique de l'API
# ------------------------------------------------------------------
set -e

echo "📡 [Airflow] Appel de l'API FastAPI pour l'envoi des e-mails d'alertes..."

cd /opt/airflow/

# Requête POST vers votre route de distribution des alertes
docker compose \
 --env-file .env.dev\
  -f docker-compose.dev.yml \
  exec -T api \
  curl -X POST "http://localhost:8000/api/v1/alerts/process-notifications" \
     -H "accept: application/json" \
     -H "Content-Type: application/json"

echo -e "\n✉️ [Airflow] Cycle de notification terminé."
