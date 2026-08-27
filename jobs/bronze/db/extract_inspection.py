from jobs.common.logger import logger
from jobs.common.config import settings
from jobs.common.mysql_client import MySQLClient
from jobs.common.minio_client import MinioStorageClient


def extract_inspection() -> None:
    """
    Pipeline Bronze :
        MySQL  --->  Pandas DataFrame  --->  MinIO Bronze
    """
    logger.info("="*70)
    logger.info("BRONZE INGESTION START")
    logger.info("="*70)

    mysql_client = MySQLClient()
    minio_client = MinioStorageClient()
    try:
        # Vérification des infrastructures
        mysql_client.check_connection()
        minio_client.check_connection()

        logger.info("Lecture de la table inspection ...")

        df_inspection = mysql_client.read_table("inspection")

        logger.info(f"Extraction d'inspections terminée ({len(df_inspection):,} lignes).")

        logger.info("Lecture de la table limite ...")

        df_limite = mysql_client.read_table("limite")

        logger.info(f"Extraction de limite terminée ({len(df_limite):,} lignes).")

        minio_client.upload_dataframe(
            dataframe=df_inspection,
            bucket_name=settings.BRONZE_BUCKET,
            file_name="inspection.parquet",
            prefix="inspection",
        )

        minio_client.upload_dataframe(
            dataframe=df_limite,
            bucket_name=settings.BRONZE_BUCKET,
            file_name="limite.parquet",
            prefix="limite",
        )

        logger.info("=" * 70)
        logger.success("Ingestion Bronze terminée.")
        logger.info("=" * 70)

    except Exception:
        logger.exception("Le pipeline Bronze a échoué.")
        raise



if __name__ == "__main__":
    extract_inspection()