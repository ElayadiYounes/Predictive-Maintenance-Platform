from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from jobs.common.logger import logger
from jobs.common.exceptions import MaintenancePlatformException


class GoldDataQuality:
    """
    Contrôles de qualité spécifiques aux tables Gold.

    Les contrôles métier généraux sont déjà réalisés dans Silver.
    Cette classe se concentre principalement sur l'intégrité
    du modèle dimensionnel.
    """
    @staticmethod
    def validate_dimension_keys(dataframe: DataFrame,key_column: str,dimension_name: str,) -> None:
        """
        Vérifie que la clé primaire d'une dimension est :
        - présente
        - non nulle
        - unique
        """

        logger.info(
            f"Validation de la clé de {dimension_name}..."
        )

        if key_column not in dataframe.columns:
            raise MaintenancePlatformException(
                f"Clé '{key_column}' absente de {dimension_name}."
            )

        null_count = dataframe.filter(
            F.col(key_column).isNull()
        ).count()

        if null_count > 0:
            raise MaintenancePlatformException(
                f"{dimension_name}: "
                f"{null_count} clé(s) NULL détectée(s)."
            )

        duplicate_count = (
            dataframe
            .groupBy(key_column)
            .count()
            .filter(F.col("count") > 1)
            .count()
        )

        if duplicate_count > 0:
            raise MaintenancePlatformException(
                f"{dimension_name}: "
                f"{duplicate_count} clé(s) dupliquée(s)."
            )

        logger.success(
            f"Clé {key_column} de {dimension_name} valide."
        )

    @staticmethod
    def validate_foreign_key(fact: DataFrame, dimension: DataFrame, fact_key: str,dimension_key: str, dimension_name: str) -> None:
        """
        Vérifie que toutes les clés étrangères de la fact
        correspondent à une clé existante dans la dimension.
        """

        logger.info(
            f"Validation FK {fact_key} → "
            f"{dimension_name}.{dimension_key}..."
        )

        missing_count = (
            fact
            .filter(F.col(fact_key).isNotNull())
            .join(
                dimension.select(
                    F.col(dimension_key).alias("_dimension_key")
                ),
                F.col(fact_key) == F.col("_dimension_key"),
                "left_anti",
            )
            .count()
        )

        if missing_count > 0:
            raise MaintenancePlatformException(
                f"Violation de clé étrangère : "
                f"{missing_count} ligne(s) de fact_inspection "
                f"ne possèdent pas de correspondance dans "
                f"{dimension_name}."
            )

        logger.success(
            f"FK {fact_key} → "
            f"{dimension_name}.{dimension_key} valide."
        )
