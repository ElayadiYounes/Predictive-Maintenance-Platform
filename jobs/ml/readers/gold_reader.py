from io import BytesIO

import pandas as pd

from jobs.common.logger import logger
from jobs.common.minio_client import MinioStorageClient
from jobs.common.config import settings

def reade_fact_inspection() -> pd.DataFrame:
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
    minio_client = MinioStorageClient()
    try:
        # Vérification des infrastructures
        minio_client.check_connection()
        logger.info("Lecture de la table fact_inspection ...")








