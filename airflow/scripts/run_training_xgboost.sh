#!/bin/bash
# ------------------------------------------------------------------
# Script d'automatisation Airflow - Étape 4 : XGBOOST ML
# ------------------------------------------------------------------


set -e

echo "[Airflow] Démarrage du ré-entraînement  de XGBOOST..."

python /opt/jobs/ml/run_xgboost_rul.py

echo "[Airflow] Entraînement xgboost terminé avec succès."

