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
    silver_path = (
        f"s3a://"
        f"{settings.SILVER_BUCKET}/"
        f"{latest_partition}"
    )


    quality = InspectionDataQuality()

    cleaner = InspectionCleaner()
    standardizer = InspectionStandardizer()
    enricher = InspectionEnricher()

    try:

        logger.info("Lecture des données Bronze...")
        # -------------------------------------------------
        # Lecture Bronze
        # -------------------------------------------------
        dataframe = read_bronze_parquet(spark,bronze_path)

        logger.info(f"Lecture terminée ({dataframe.count():,} lignes).")

        #standardisation les noms des colonnes métier
        dataframe = standardizer.standardize_column_names(dataframe)

        #Validation les colonnes indispensable
        quality.validate_required_columns(dataframe)

        #Data Cleaning
        dataframe = cleaner.clean(dataframe)
        dataframe = cleaner.clean_missing_values(dataframe)

        #Validation taux de null
        quality.validate_null_ratio(dataframe)

        #standardisation text et types
        dataframe = standardizer.standardize_text_values(dataframe)
        dataframe= standardizer.standardize_data_types(dataframe)

        #Validation schema
        quality.validate_schema(dataframe)

        #enrichissement
        dataframe = enricher.enrich(dataframe)

        #Validation les intervalles des valeurs numerique
        quality.validate_numeric_ranges(dataframe)

        # -------------------------------------------------
        # Ecriture Silver
        # -------------------------------------------------

        write_silver_parquet(dataframe, silver_path)

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





