import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
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
    MYSQL_PASSWORD : str

    MYSQL_CHARSET : str = "utf8mb4"


    #######################################
    # MINIO (DATA LAKE)
    #######################################

    MINIO_ENDPOINT : str = "http: // minio: 9000"

    MINIO_API_PORT : int = 9000

    MINIO_CONSOLE_PORT : int = 9001

    MINIO_ROOT_USER : str
    MINIO_ROOT_PASSWORD : str

    BRONZE_BUCKET : str
    SILVER_BUCKET : str
    GOLD_BUCKET : str
    MODELS_BUCKET : str






#Instanciation du Singleton de configuration
try:
    settings = Settings()
except Exception as e:
    logger.critical(f"Erreur critique de validation des variables d'environnement : {e}")
    raise e

    









