from pyspark.sql import DataFrame

from jobs.common.minio_client import MinioStorageClient
from jobs.common.config import settings
from jobs.common.spark_session import get_spark_session
from jobs.common.logger import logger

from jobs.gold.readers.silver_reader import read_silver_parquet
from jobs.gold.transformation.date_dimension import build_dim_time
from jobs.gold.transformation.user_dimension import build_dim_user
from jobs.gold.transformation.equipement_dimension import build_dim_equipement
from jobs.gold.transformation.fact_inspection import build_fact_inspection

from jobs.gold.quality.gold_data_quality import GoldDataQuality
from jobs.gold.writer.gold_writer import write_gold_table

def build_gold() -> None:
    """
    Pipeline Gold.

    Silver
        ↓
    Dimensions
        ├── dim_time
        ├── dim_equipement
        └── dim_user
        ↓
    Fact
        └── fact_inspection
        ↓
    Gold Data Quality
        ↓
    MinIO + Hive
    """
    logger.info("=" * 70)
    logger.info("GOLD BUILD START")
    logger.info("=" * 70)

    spark = get_spark_session(settings.PROJECT_NAME)
    minio_client = MinioStorageClient()
    quality = GoldDataQuality()

    try:
        # =====================================================
        # 1. Détermination du chemin Silver
        # =====================================================

        latest_partition_inspection = minio_client.get_latest_partition(
            bucket_name=settings.SILVER_BUCKET,
            prefix="inspection",
        )
        latest_partition_limite = minio_client.get_latest_partition(
            bucket_name=settings.SILVER_BUCKET,
            prefix="limite"
        )

        logger.info(
            f"Dernière partition Silver inspection détectée : {latest_partition_inspection}"
        )
        logger.info(
            f"Dernière partition Silver limite détectée : {latest_partition_limite}"
        )

        minio_path_inspection = (
            f"s3a://"
            f"{settings.SILVER_BUCKET}/"
            f"{latest_partition_inspection}"
        )

        minio_path_limite = (
            f"s3a://"
            f"{settings.SILVER_BUCKET}/"
            f"{latest_partition_limite}"
        )

        # =====================================================
        # 2. Lecture Silver
        # =====================================================

        logger.info(
            f"Lecture des données Silver inspection depuis : {minio_path_inspection}"
        )

        dataframe_inspection = read_silver_parquet(
            spark=spark,
            silver_path=minio_path_inspection,
        )

        logger.info(
            f"Lecture des données Silver limite depuis : {minio_path_limite}"
        )

        dataframe_limite = read_silver_parquet(
            spark=spark,
            silver_path=minio_path_limite
        )

        silver_inspection_count = dataframe_inspection.count()

        silver_limite_count = dataframe_limite.count()

        logger.info(
            f"Lecture Silver inspection terminée : "
            f"{silver_inspection_count:,} lignes."
        )

        logger.info(
            f"Lecture Silver limite terminée : "
            f"{silver_limite_count:,} lignes."
        )

        if silver_limite_count == 0 or silver_inspection_count == 0:
            logger.warning(
                "Les données Silver sont vides."
            )
            return

        # =====================================================
        # 3. Construction des dimensions
        # =====================================================

        logger.info("Construction de Dim_time ...")
        dim_time = build_dim_time(dataframe_inspection)

        logger.info("Construction de Dim_equipement ...")
        dim_equipement = build_dim_equipement(dataframe_inspection,dataframe_limite)

        logger.info("Construction de Dim_user ...")
        dim_user = build_dim_user(dataframe_inspection)

        # =====================================================
        # 4. Construction de la fact
        # =====================================================

        logger.info("Construction Table de fait Fact_inspection ...")
        fact_inspection = build_fact_inspection(dataframe=dataframe_inspection,
                                                dim_time=dim_time,
                                                dim_equipement=dim_equipement,
                                                dim_user=dim_user
        )
        logger.success("La Construction des Tables Gold Terminé")

        # =====================================================
        # 5. Gold Data Quality
        # =====================================================

        logger.info("=" * 70)
        logger.info("GOLD DATA QUALITY")
        logger.info("=" * 70)

        #Validation des colonnes obligatoire
        quality.validate_required_columns(dim_time,
                                          ["id_time","date","inspection_year","inspection_month","inspection_day","month_name"],
                                          "dim_time"
        )
        quality.validate_required_columns(dim_equipement,
                                          ["id_equipement","zone","instal","seuil_danger_temp","seuil_danger_vib_axiale","seuil_danger_vib_horiz","seuil_danger_vib_vert"],
                                          "dim_equipement"
        )
        quality.validate_required_columns(dim_user,
                                          ["id_user","nom"],
                                          "dim_user"
        )
        quality.validate_required_columns(fact_inspection,
                                          ["id_inspection","id_time","id_equipement","id_user"],
                                          "fact_inspection"
        )

        #validation PK dimension
        quality.validate_dimension_keys(dim_time,"id_time","dim_time")
        quality.validate_dimension_keys(dim_equipement,"id_equipement","dim_equipement")
        quality.validate_dimension_keys(dim_user,"id_user","dim_user")

        #validation FK
        quality.validate_fact_foreign_keys(fact_inspection)

        quality.validate_foreign_key(fact_inspection,
                                     dim_time,
                                     "id_time",
                                     "id_time",
                                     "dim_time"
        )
        quality.validate_foreign_key(fact_inspection,
                                     dim_equipement,
                                     "id_equipement",
                                     "id_equipement",
                                     "dim_equipement"
        )
        quality.validate_foreign_key(fact_inspection,
                                     dim_user,
                                     "id_user",
                                     "id_user",
                                     "dim_user"
        )


        #validation les doublons
        quality.validate_fact_uniqueness(fact_inspection)

        #validation augmentation des ligne
        quality.validate_row_count_not_increased(dataframe_inspection,fact_inspection,"Silver","fact_inspection")

        logger.success("Gold Data Quality Validée avec Succés")

        # =====================================================
        # 6. Écriture Gold
        # =====================================================

        gold_base_path = (
            f"s3a://"
            f"{settings.GOLD_BUCKET}/"
            "inspection"
        )

        logger.info("=" * 70)
        logger.info("GOLD WRITING")
        logger.info("=" * 70)
        # Création du schéma Hive
        spark.sql(
            """
            CREATE DATABASE IF NOT EXISTS gold
             """
        )
        write_gold_table(dim_time,"gold.dim_time",f"{gold_base_path}/dim_time")
        write_gold_table(dim_equipement,"gold.dim_equipement",f"{gold_base_path}/dim_equipement")
        write_gold_table(dim_user,"gold.dim_user",f"{gold_base_path}/dim_user")
        write_gold_table(fact_inspection,"gold.fact_inspection",f"{gold_base_path}/fact_inspection")

        logger.info("=" * 70)
        logger.success("Pipeline Gold terminé avec succès.")
        logger.info("=" * 70)

    except Exception:

        logger.exception(
            "Le pipeline Gold a échoué."
        )

        raise

    finally:

        # On libère explicitement la SparkSession
        spark.stop()



if __name__ == "__main__":
    build_gold()

