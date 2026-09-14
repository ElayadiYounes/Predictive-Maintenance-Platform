from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# Configuration des paramètres par défaut
default_args = {
    "owner": "ocp_data_team",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "email_on_failure": True,
    "email": "younesselayadi05@gmail.com",
    "retries": 1,
    "retry_delay": timedelta(minutes=15),
}

# ------------------------------------------------------------------
# DAG ML RETRAINING : Pipeline Historique Semestriel (Tous les 6 mois)
# ------------------------------------------------------------------
with DAG(
        "ocp_ml_retraining_pipeline",
        default_args=default_args,
        description="Pipeline global de ré-entraînement complet des modèles d'IA sur l'historique de 6 mois",
        schedule_interval="0 0 1 */6 *",  # S'exécute automatiquement tous les 6 mois
        catchup=False,
        max_active_runs=1,
) as dag_retraining:
    # --- ÉTAPE 1 : Ingestion complète de l'historique depuis la DB ---
    task_history_ingestion = BashOperator(
        task_id="run_bronze_history_ingestion",
        bash_command="/opt/airflow/scripts/run_ingestion.sh",
    )

    # --- ÉTAPE 2 : Nettoyage et typage distribué de l'historique complet ---
    task_history_silver = BashOperator(
        task_id="run_silver_history_transformation",
        bash_command="/opt/airflow/scripts/run_bronze_to_silver.sh",
    )

    # --- ÉTAPE 3 : Reconstruction et agrégation des tables Gold globales ---
    task_history_gold = BashOperator(
        task_id="run_gold_history_modeling",
        bash_command="/opt/airflow/scripts/run_silver_to_gold.sh",
    )

    # --- ÉTAPE 4A : Ré-entraînement Isolation Forest (Algorithme Python Pur) ---
    task_train_anomaly = BashOperator(
        task_id="train_isolation_forest",
        bash_command="/opt/airflow/scripts/run_training_isolation_forest.sh",
    )

    # --- ÉTAPE 4B : Ré-entraînement XGBoost RUL (Algorithme Python Pur) ---
    task_train_rul = BashOperator(
        task_id="train_xgboost_rul",
        bash_command="/opt/airflow/scripts/run_training_xgboost.sh",
    )

    # Le pipeline extrait et prépare d'abord l'ensemble des données d'historique,
    # puis lance l'entraînement des deux modèles d'IA en parallèle.

    task_history_ingestion >> task_history_silver >> task_history_gold >> [task_train_anomaly, task_train_rul]
