from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.utils import AnalysisException

from jobs.common.logger import logger
from jobs.common.exceptions import DataLakeReadError

def read_bronze_parquet(spark : SparkSession, bronze_path : str) -> DataFrame:
    """
    Lit un fichier Parquet depuis la couche Bronze
    et retourne un DataFrame Spark.

    Parameters
    ----------
    spark : SparkSession
        Session Spark déjà initialisée et configurée.

    bronze_path : str
        Chemin complet du fichier Parquet dans MinIO.

        Exemple :
        s3a://bronze/inspection/2026/07/28/vibration.parquet

    Returns
    -------
    DataFrame
        DataFrame Spark représentant les données Bronze.
    """
    if not bronze_path or not bronze_path.strip():
        raise ValueError("Le chemin Bronze ne peut pas être vide.")

    logger.info(f"Lecture des données Bronze : {bronze_path}")

    try:
        dataframe = spark.read.parquet(bronze_path)
        logger.success("DataFrame Bronze créé avec succès.")
        return dataframe

    except AnalysisException as e:
        logger.exception(f"Impossible de lire les données Bronze : {bronze_path}")
        raise DataLakeReadError(
            "Lecture des données Bronze impossible.",
            str(e),
        ) from e

    except Exception:
        logger.exception("Erreur inattendue lors de la lecture de la couche Bronze.")
    raise

