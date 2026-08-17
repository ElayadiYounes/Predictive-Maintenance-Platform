from pyspark.sql import DataFrame

from jobs.common.logger import logger
from jobs.common.exceptions import DataLakeConnectionError


def write_gold_table(dataframe: DataFrame, table_name: str, gold_path: str) -> None:
    """
    Écrit une table Gold dans MinIO et l'enregistre dans Hive Metastore.

    Parameters
    ----------
    dataframe : DataFrame
        DataFrame Gold à écrire.

    table_name : str
        Nom complet de la table Hive.
        Exemple :
            gold.dim_time
            gold.dim_equipement
            gold.dim_user
            gold.fact_inspection

    gold_path : str
        Chemin S3A correspondant à la table.
        Exemple :
            s3a://gold/inspection/dim_time
    """

    logger.info(
        f"Écriture de la table Gold '{table_name}'..."
    )

    if dataframe is None:
        raise ValueError(
            f"Le DataFrame fourni pour '{table_name}' est None."
        )

    if not dataframe.columns:
        raise ValueError(
            f"Le DataFrame fourni pour '{table_name}' "
            "ne contient aucune colonne."
        )

    try:

        # -------------------------------------------------
        # Vérification rapide du DataFrame
        # -------------------------------------------------

        row_count = dataframe.count()

        logger.info(
            f"Table '{table_name}' : "
            f"{row_count:,} lignes."
        )

        if row_count == 0:
            logger.warning(
                f"La table '{table_name}' est vide."
            )

        # -------------------------------------------------
        # Écriture Parquet + enregistrement Hive
        # -------------------------------------------------

        (
            dataframe.write
            .mode("overwrite")
            .format("parquet")
            .option("path", gold_path)
            .saveAsTable(table_name)
        )

        logger.success(
            f"Table Gold '{table_name}' écrite avec succès."
        )

        logger.debug(
            f"Emplacement physique : {gold_path}"
        )

    except Exception as exc:

        logger.exception(
            f"Erreur lors de l'écriture de la table "
            f"Gold '{table_name}'."
        )

        raise DataLakeConnectionError(
            f"Impossible d'écrire la table Gold "
            f"'{table_name}'.",
            str(exc),
        ) from exc