from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.utils import AnalysisException

from jobs.common.logger import logger
from jobs.common.exceptions import DataLakeReadError

def read_silver_parquet(spark : SparkSession, silver_path : str) -> DataFrame:
    """
    Lit un fichier Parquet depuis la couche silver
    et retourne un DataFrame Spark.

    Parameters
    ----------
    spark : SparkSession
        Session Spark déjà initialisée et configurée.

    silver_path : str
        Chemin complet du fichier Parquet dans MinIO.

        Exemple :
        s3a://silver/inspection/...

    Returns
    -------
    DataFrame
        DataFrame Spark représentant les données Bronze.
    """
    if not silver_path or not silver_path.strip():
        raise ValueError("Le chemin Silver ne peut pas être vide.")

    logger.info(f"Lecture des données Silver : {silver_path}")

    try:
        dataframe = spark.read.parquet(silver_path)
        logger.success("DataFrame Silver créé avec succès.")
        return dataframe

    except AnalysisException as e:
        logger.exception(f"Impossible de lire les données Silver : {silver_path}")
        raise DataLakeReadError(
            "Lecture des données Silver impossible.",
            str(e),
        ) from e

    except Exception:
        logger.exception("Erreur inattendue lors de la lecture de la couche Silver.")
        raise

