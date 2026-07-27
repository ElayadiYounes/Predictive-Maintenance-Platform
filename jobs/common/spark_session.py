from pyspark.sql import SparkSession
from jobs.common.config import settings
from jobs.common.logger import logger


def get_spark_session(app_name: str) -> SparkSession:
    """Initialise ou récupère la SparkSession configurée pour Hive, MinIO et Hudi.

    Applique le pattern Singleton pour éviter la saturation de la mémoire du cluster.
    """
    logger.info(f"Initialisation de la SparkSession pour l'application : '{app_name}'...")

    try:
        spark = (
            SparkSession.builder
            .appName(app_name)

            # 1. Activation du catalogue de métadonnées centralisé Hive
            .enableHiveSupport()

            # 2. Configuration stricte des identifiants sécurisés de votre .env.dev
            .config("spark.hadoop.fs.s3a.access.key", settings.MINIO_ROOT_USER)
            .config("spark.hadoop.fs.s3a.secret.key", settings.MINIO_ROOT_PASSWORD)

            # 3. Paramètres d'optimisation complémentaires (Hadoop S3A)
            .config("spark.hadoop.fs.s3a.endpoint", settings.MINIO_ENDPOINT)
            .config("spark.hadoop.fs.s3a.path.style.access", "true")
            .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")

            .getOrCreate()
        )

        logger.success(f"SparkSession '{app_name}' opérationnelle .")
        return spark

    except Exception as e:
        logger.critical(f"Échec critique lors de la création de la SparkSession : {e}")
        raise e