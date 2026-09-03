import os

from pyhive import hive
from jobs.common.logger import logger
from jobs.common.config import settings


class AnomalyCatalog:
    """
    Gestion du catalogue Hive pour les tables ML.

    Le catalogue Hive pointe vers les fichiers Parquet
    déjà présents dans MinIO Gold.
    """

    DATABASE_NAME = "gold"
    TABLE_NAME = "fact_inspection_anomaly"

    TABLE_LOCATION = (
        "s3a://gold/inspection/fact_inspection_anomaly/"
    )

    def __init__(self):
        self.host = settings.SPARK_THRIFT_HOST

        self.port = settings.SPARK_THRIFT_PORT

    def register_anomaly_table(self) -> None:
        """
        Enregistre gold.fact_inspection_anomaly
        dans le catalogue Hive.

        La table pointe vers les fichiers Parquet
        déjà écrits dans MinIO Gold.
        """

        logger.info("=" * 70)
        logger.info("HIVE CATALOG REGISTRATION START")
        logger.info("=" * 70)

        connection = None
        cursor = None

        try:
            logger.info(
                f"Connexion au Spark Thrift Server : "
                f"{self.host}:{self.port}"
            )

            connection = hive.Connection(
                host=self.host,
                port=self.port,
                database="default",
            )

            cursor = connection.cursor()

            # --------------------------------------------------
            # 1. Création de la base Gold
            # --------------------------------------------------

            logger.info(
                f"Vérification de la base : {self.DATABASE_NAME}"
            )

            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {self.DATABASE_NAME}"
            )

            # --------------------------------------------------
            # 2. Création de la table externe
            # --------------------------------------------------

            logger.info(
                f"Enregistrement de la table : "
                f"{self.DATABASE_NAME}.{self.TABLE_NAME}"
            )

            # CORRECTION : Ajout de model_version et prediction_date
            # et alignement des types d'ID (BIGINT ou INT selon votre schéma d'origine)
            cursor.execute(
                f"""
                CREATE EXTERNAL TABLE IF NOT EXISTS {self.DATABASE_NAME}.{self.TABLE_NAME}
                (
                    id_inspection INT,
                    id_equipement BIGINT,
                    anomaly_score DOUBLE,
                    anomaly_flag INT,
                    model_type STRING,
                    model_name STRING,
                    model_version STRING,
                    prediction_date TIMESTAMP,
                    alert_temperature INT,
                    alert_vib_axiale INT,
                    alert_vib_horiz INT,
                    alert_vib_vert INT,
                    threshold_alert INT,
                    validated_anomaly INT,
                    anomaly_status STRING
                )
                STORED AS PARQUET
                LOCATION '{self.TABLE_LOCATION}'
                """
            )

            # --------------------------------------------------
            # 3. Vérification
            # --------------------------------------------------

            logger.info("Vérification de la table enregistrée...")

            cursor.execute(
                f"DESCRIBE {self.DATABASE_NAME}.{self.TABLE_NAME}"
            )

            columns = cursor.fetchall()

            if not columns:
                raise RuntimeError(
                    "La table Hive n'a pas pu être vérifiée."
                )

            logger.success(
                f"Table enregistrée avec succès : "
                f"{self.DATABASE_NAME}.{self.TABLE_NAME}"
            )

            logger.info(
                f"LOCATION : {self.TABLE_LOCATION}"
            )

        except Exception:
            logger.exception(
                "Erreur lors de l'enregistrement de la table dans Hive."
            )
            raise

        finally:
            # CORRECTION : Gestion plus robuste des fermetures en cas d'échec
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

            logger.info("=" * 70)
            logger.success("HIVE CATALOG REGISTRATION TERMINÉ.")
            logger.info("=" * 70)
