import pandas as pd

from jobs.common.logger import logger
from jobs.common.minio_client import MinioStorageClient
from jobs.common.config import settings

def read_gold_table(table_name : str) -> pd.DataFrame:
    """
    Lit la table Gold fact_inspection depuis MinIO
    et retourne un DataFrame pandas destiné à la couche ML.

    Returns
    -------
    pd.DataFrame
        Données d'inspection Gold.
    """
    logger.info("=" * 70)
    logger.info("GOLD EXTRACTION START")
    logger.info("=" * 70)
    if not table_name:
        raise ValueError("Le nom de la table Gold ne peut pas être vide.")

    minio_client = MinioStorageClient()
    prefix = f"inspection/{table_name}"

    logger.info(f"Lecture de la table {table_name} ...")
    dataframe = minio_client.read_parquet_prefix(settings.GOLD_BUCKET, prefix)

    logger.info(f"Lecture de la table {table_name} Terminé avec succès : {len(dataframe):,} lignes.")

    return dataframe










