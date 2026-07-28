import os
import sys
from pathlib import Path
from loguru import logger

# 1. Détermination de la racine des logs
# Remonte au dossier racine du projet pour écrire dans le dossier /logs/
BASE_DIR = Path(__file__).resolve().parents[2]
LOGS_ROOT = BASE_DIR / "logs"

# 2. Détection dynamique du composant pour trier les fichiers de logs
# Si le script s'exécute dans l'ingestion, le spark ou l'api, on isole son fichier
APP_NAME = os.getenv("PROJECT_NAME", "ocp-predictive-maintenance-platform")
APP_ENV = os.getenv("APP_ENV", "dev").lower()

# Détection de l'étape via les variables d'environnement Docker
SERVICE_NAME = os.getenv("SERVICE_NAME", "ingestion").lower()

LOG_CONFIG = {
    "ingestion": ("ingestion", "ingestion.log"),
    "spark": ("spark", "spark.log"),
    "airflow": ("airflow", "airflow.log"),
    "api": ("api", "api.log"),
    "ml": ("ml", "ml.log"),
}

log_subfolder, log_file_name = LOG_CONFIG.get(
    SERVICE_NAME,
    ("misc", "application.log")
)

LOG_FILE_PATH = LOGS_ROOT / log_subfolder / log_file_name
LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

# 3. Configuration des formats de sortie
# Format coloré et ultra-lisible pour la console de développement
CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# Format strict et détaillé pour le fichier de stockage persistant
FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{name}:{function}:{line} | "
    "{message}"
)

# 4. Initialisation et Nettoyage de la configuration par défaut de Loguru
logger.remove()

# SINK 1 : Ériture sur la console Docker (stdout)
# En production, on peut monter le niveau à INFO ou WARNING pour éviter le bruit
console_level = "DEBUG" if APP_ENV == "dev" else "INFO"
logger.add(
    sys.stdout,
    format=CONSOLE_FORMAT,
    level=console_level,
    colorize=True,
    backtrace=True,
    diagnose=True if APP_ENV == "dev" else False,
)

# SINK 2 : Ériture persistante dans le dossier racine /logs/ de votre machine Windows
try:
    logger.add(
        str(LOG_FILE_PATH),
        format=FILE_FORMAT,
        level="INFO",  # On garde au minimum les INFO, WARNING, ERROR et CRITICAL en fichier
        rotation="3 MB",  # Protège vos 30 Go de disque : crée un nouveau fichier à 3 Mo
        retention="5 days",  # Supprime automatiquement les vieux logs de plus de 5 days
        compression="zip",  # Compresse les anciens logs en .zip pour économiser l'espace
        enqueue=True,  # INDISPENSABLE EN DATA: thread-safe et asynchrone (ne ralentit pas Spark)
        encoding="utf-8",
    )
    logger.info(f"Système d observabilité initialisé. Fichier cible : logs/{log_subfolder}/{log_file_name}")
except Exception as e:
    # Si le conteneur n'a pas les droits d'écriture sur le dossier hôte, on avertit sur la console
    print(f"Impossible d initialiser le fichier de log persistant ({e}). Utilisation exclusive de la console.", file=sys.stderr)

# Exposer le logger configuré
# Vos autres scripts feront simplement : from jobs.common.logger import logger