from pyspark.sql import DataFrame

from jobs.common.logger import logger
from jobs.common.exceptions import DataLakeWriteError

def write_silver_parquet(df: DataFrame, silver_path: str, mode : str = 'overwrite') -> None:
    """
    Écrit un DataFrame Spark dans la couche Silver
    au format Parquet.

    Parameters
    ----------
    df : DataFrame
        DataFrame Spark déjà transformé et prêt
        à être stocké dans Silver.

    silver_path : str
        Chemin cible dans MinIO.

        Exemple :
        s3a://silver/inspection/

    mode : str, default="overwrite"
        Mode d'écriture Spark.

        Valeurs possibles :
        - overwrite
        - append
        - error
        - ignore
    """
    if not silver_path or not silver_path.strip():
        raise ValueError("Le chemin Silver ne peut pas être vide.")

    allowed_modes = {"overwrite", "append", "error", "ignore", }
    mode = mode.lower()

    if mode not in allowed_modes:
        raise ValueError(
        f"Mode d'écriture invalide : '{mode}'. "
        f"Modes autorisés : {sorted(allowed_modes)}."
        )

    logger.info(f"Écriture des données dans Silver : " f"{silver_path}")

    try:
        #j'ajoute partitionBY par la suit !!!!!!
        (
            df.write
            .mode(mode)
            .format("parquet")
            .save(silver_path)
        )
        logger.success(f"Données écrites avec succès dans Silver : " f"{silver_path}")

    except Exception as e:
        logger.exception(f"Impossible d'écrire les données dans Silver : {silver_path}")
        raise DataLakeWriteError(
            "Écriture des données dans la couche Silver impossible.",
             str(e),
        ) from e
