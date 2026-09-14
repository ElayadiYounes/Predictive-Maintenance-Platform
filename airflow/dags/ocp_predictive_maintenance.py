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
    "retry_delay": timedelta(minutes=5),
}

# ------------------------------------------------------------------
# DAG MAIN : Pipeline de Production Continu (Inférence + Alertes)
# ------------------------------------------------------------------
with DAG(
    "ocp_predictive_maintenance_pipeline",
    default_args=default_args,
    description="Pipeline OCP continu d'ingestion, de traitement et d'inférence d'anomalies",
    schedule_interval="*/15 * * * *",  # S'exécute TOUTES LES 15 MINUTES de façon autonome
    catchup=False,
    max_active_runs=1,
) as dag_production:

    task_ingestion = BashOperator(
        task_id="run_bronze_ingestion",
        bash_command="/opt/airflow/scripts/run_ingestion.sh",
    )

    task_silver = BashOperator(
        task_id="run_silver_transformation",
        bash_command="/opt/airflow/scripts/run_bronze_to_silver.sh",
    )

    task_gold = BashOperator(
        task_id="run_gold_modeling",
        bash_command="/opt/airflow/scripts/run_silver_to_gold.sh",
    )

    task_ml_inference = BashOperator(
        task_id="run_ml_inference",
        bash_command="/opt/airflow/scripts/run_predict_new_data.sh",
    )

    task_notifications = BashOperator(
        task_id="run_api_notifications",
        bash_command="/opt/airflow/scripts/run_sent_notification.sh",
    )

    # Définition de l'enchaînement strict (Pipeline Data de Production)
    task_ingestion >> task_silver >> task_gold >> task_ml_inference >> task_notifications
