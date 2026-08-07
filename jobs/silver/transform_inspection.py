from jobs.common.logger import logger
from jobs.common.spark_session import get_spark_session
from jobs.common.config import settings
from jobs.common.minio_client import MinioStorageClient

from jobs.silver.readers.bronze_reader import read_bronze_parquet
from jobs.silver.writers.silver_writer import write_silver_parquet

from jobs.silver.quality.data_quality import InspectionDataQuality
from jobs.silver.transformation.cleaner import InspectionCleaner
from jobs.silver.transformation.standardizer import InspectionStandardizer
from jobs.silver.transformation.enricher import InspectionEnricher

def transform_inspection() -> None:
    """
    Pipeline Silver.

    Bronze
        ↓
    Data Quality
        ↓
    Cleaner
        ↓
    Data Quality
        ↓
    Standardizer
        ↓
    Data Quality
        ↓
    Enricher
        ↓
    Data Quality
        ↓
    Silver
    """
    logger.info("=" * 70)
    logger.info("SILVER TRANSFORMATION START")
    logger.info("=" * 70)

    spark = get_spark_session(settings.PROJECT_NAME)
    minio_client = MinioStorageClient()
    latest_partition = minio_client.get_latest_partition(bucket_name=settings.BRONZE_BUCKET,prefix="inspection")
    bronze_path = (
        f"s3a://"
        f"{settings.BRONZE_BUCKET}/"
        f"{latest_partition}"
    )


    quality = InspectionDataQuality()

    cleaner = InspectionCleaner()
    standardizer = InspectionStandardizer()
    enricher = InspectionEnricher()

    try:

        logger.info("Lecture des données Bronze...")

        dataframe = read_bronze_parquet(spark,bronze_path)

        logger.info(f"Lecture terminée ({dataframe.count():,} lignes).")

        # -------------------------------------------------
        # Validation structure
        # -------------------------------------------------

        quality.validate_required_columns(dataframe)

        # -------------------------------------------------
        # Nettoyage
        # -------------------------------------------------

        dataframe = cleaner.clean(dataframe)

        # -------------------------------------------------
        # Validation qualité
        # -------------------------------------------------

        quality.validate_null_ratio(dataframe)

        # -------------------------------------------------
        # Standardisation
        # -------------------------------------------------

        dataframe = standardizer.standardize(dataframe)

        # -------------------------------------------------
        # Validation schéma
        # -------------------------------------------------

        quality.validate_schema(dataframe)

        # -------------------------------------------------
        # Enrichissement
        # -------------------------------------------------

        dataframe = enricher.enrich(dataframe)

        # -------------------------------------------------
        # Validation métier
        # -------------------------------------------------

        quality.validate_numeric_ranges(dataframe)

        # -------------------------------------------------
        # Ecriture Silver
        # -------------------------------------------------

        #!!!!!!!!!!!!!!!!!!!!!!!!! writer ici !!!!!!!!!!!!!!!!!!!!!!!

        logger.info("=" * 70)
        logger.success("Transformation Silver terminée.")
        logger.info("=" * 70)

    except Exception:
        logger.exception(
            "Le pipeline Silver a échoué."
        )
        raise

    if __name__ == "__main__":
        transform_inspection()





