from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from jobs.common.logger import logger
from jobs.common.exceptions import MaintenancePlatformException
from typing import List


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
    @staticmethod
    def validate_fact_foreign_keys(fact: DataFrame) -> None:
        """
        Vérifie que les clés étrangères obligatoires
        de fact_inspection ne sont pas NULL.
        """

        required_keys = [
            "id_time",
            "id_equipement",
            "id_user",
        ]

        for column in required_keys:

            null_count = fact.filter(
                F.col(column).isNull()
            ).count()

            if null_count > 0:
                raise MaintenancePlatformException(
                    f"fact_inspection : "
                    f"{null_count} valeur(s) NULL "
                    f"détectée(s) dans '{column}'."
                )

    @staticmethod
    def validate_fact_uniqueness(fact: DataFrame) -> None:
        """
        Vérifie que l'identifiant d'inspection est :
        - présent
        - non NULL
        - unique
        """

        logger.info(
            "Validation de l'unicité de fact_inspection..."
        )

        if "id_inspection" not in fact.columns:
            raise MaintenancePlatformException(
                "fact_inspection : colonne 'id_inspection' absente."
            )

        null_count = (
            fact
            .filter(F.col("id_inspection").isNull())
            .count()
        )

        if null_count > 0:
            raise MaintenancePlatformException(
                f"fact_inspection : "
                f"{null_count} valeur(s) NULL détectée(s) "
                f"dans 'id_inspection'."
            )

        duplicate_count = (
            fact
            .groupBy("id_inspection")
            .count()
            .filter(F.col("count") > 1)
            .count()
        )

        if duplicate_count > 0:
            raise MaintenancePlatformException(
                f"fact_inspection : "
                f"{duplicate_count} inspection(s) dupliquée(s)."
            )

        logger.success(
            "Unicité de fact_inspection validée."
        )


    @staticmethod
    def validate_required_columns(dataframe: DataFrame, required_columns: List[str], dataframe_name: str) -> None:
        """
        Vérifie la présence des colonnes obligatoires.
        """

        missing_columns = [
            column
            for column in required_columns
            if column not in dataframe.columns
        ]

        if missing_columns:
            raise MaintenancePlatformException(
                f"{dataframe_name} : "
                f"colonnes manquantes : "
                f"{missing_columns}"
            )

    @staticmethod
    def validate_row_count_not_increased(
            source_dataframe: DataFrame,
            target_dataframe: DataFrame,
            source_name: str,
            target_name: str,
    ) -> None:
        """
        Vérifie que la transformation n'a pas augmenté
        le nombre de lignes du DataFrame.

        Une augmentation du nombre de lignes peut indiquer
        une jointure 1-N inattendue ou une duplication de données.
        """

        logger.info(
            f"Validation du nombre de lignes : "
            f"{source_name} → {target_name}..."
        )

        source_count = source_dataframe.count()
        target_count = target_dataframe.count()

        logger.info(
            f"{source_name}: {source_count:,} lignes"
        )

        logger.info(
            f"{target_name}: {target_count:,} lignes"
        )

        if target_count != source_count:
            raise MaintenancePlatformException(
                f"Le nombre de lignes a augmenté lors de la "
                f"transformation {source_name} → {target_name} : "
                f"{source_count:,} → {target_count:,}."
            )

        logger.success(
            f"Nombre de lignes valide : "
            f"{source_count:,} → {target_count:,}."
        )

