import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from loguru import logger


BASE_DIR = Path(__file__).resolve().parents[2]
APP_ENV = os.getenv("APP_ENV", "dev").lower()
env_file_name = ".env.prod" if APP_ENV == "prod" else ".env.dev"
env_file_path = BASE_DIR / env_file_name


if env_file_path.exists():
    logger.info(f"Centralisation Config : Chargement depuis {env_file_name}")
else:
    logger.warning(f"Fichier {env_file_name} introuvable à la racine {BASE_DIR} ")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_file_path if env_file_path.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"

    )
    #######################################
    # GONFIGURATION GLOBAL
    #######################################
    PROJECT_NAME: str = "ocp-predictive-maintenance-platform"
    APP_ENV: str = "dev"
    DEBUG: bool = True

    #######################################
    # MYSQL (OCP SOURCE DATABASE)
    #######################################

    MYSQL_HOST : str = "host.docker.internal"
    MYSQL_PORT : int =  3306

    MYSQL_DATABASE : str

    MYSQL_USER : str
    MYSQL_PASSWORD : SecretStr

    MYSQL_CHARSET : str = "utf8mb4"

    @property
    def MYSQL_URL(self) -> str:
        return (
            f"mysql+pymysql://"
            f"{self.MYSQL_USER}:"
            f"{self.MYSQL_PASSWORD.get_secret_value()}@"
            f"{self.MYSQL_HOST}:{self.MYSQL_PORT}/"
            f"{self.MYSQL_DATABASE}"
            f"?charset={self.MYSQL_CHARSET}"
        )


    #######################################
    # MINIO (DATA LAKE)
    #######################################

    MINIO_ENDPOINT : str

    MINIO_API_PORT : int = 9000

    MINIO_CONSOLE_PORT : int = 9001

    MINIO_ROOT_USER : str
    MINIO_ROOT_PASSWORD : SecretStr

    BRONZE_BUCKET : str
    SILVER_BUCKET : str
    GOLD_BUCKET : str
    MODELS_BUCKET : str

    SPARK_THRIFT_HOST : str
    SPARK_THRIFT_PORT : int


    # ==========================================
    # DATABASE & CATALOG (POSTGRESQL & HIVE)
    # ==========================================
    POSTGRES_HOST : str = "postgres"

    POSTGRES_PORT : int = 5432

    POSTGRES_HIVE_DATABASE : str
    POSTGRES_AIRFLOW_DATABASE : str

    POSTGRES_USER : str

    POSTGRES_PASSWORD : SecretStr

    HIVE_METASTORE_HOST : str
    HIVE_METASTORE_PORT : int
    HIVE_WAREHOUSE_DIR : str

    @property
    def HIVE_METASTORE_URI(self) -> str:
        return (
            f"thrift://{self.HIVE_METASTORE_HOST}"
            f":{self.HIVE_METASTORE_PORT}"
        )




#Instanciation du Singleton de configuration
try:
    settings = Settings()
except Exception as e:
    logger.critical(f"Erreur critique de validation des variables d'environnement : {e}")
    raise e

    









