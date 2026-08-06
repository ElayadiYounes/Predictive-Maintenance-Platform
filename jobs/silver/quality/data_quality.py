from pyspark.sql import DataFrame
from jobs.common.logger import logger
from jobs.common.exceptions import MissingRequiredColumnError, InvalidSchemaError
from pyspark.sql.types import (IntegerType, DoubleType, StringType, TimestampType)



class InspectionDataQuality :
    """
    Responsable de Vérifie la qualité de données avant cleaner
    """
    REQUIRED_COLUMNS = [
        "id",
        "date",
        "zone",
        "instal",
        "p_produit",
        "huile_graisse",
        "ailette",
        "boulonneries",
        "cable",
        "plaque_a_borne",
        "graisseur",
        "t_av",
        "t_ar",
        "av_ax",
        "av_h",
        "av_v",
        "ar_ax",
        "ar_h",
        "ar_v",
        "observation",
        "action",
        "utilisateur",
    ]
    EXPECTED_SCHEMA = {
        "id": IntegerType,
        "date": TimestampType,

        "zone": StringType,
        "instal": StringType,
        "observation": StringType,
        "action": StringType,
        "utilisateur": StringType,

        "p_produit": IntegerType,
        "huile_graisse": IntegerType,
        "ailette": IntegerType,
        "boulonneries": IntegerType,
        "cable": IntegerType,
        "plaque_a_borne": IntegerType,
        "graisseur": IntegerType,

        "t_av": DoubleType,
        "t_ar": DoubleType,

        "av_ax": DoubleType,
        "av_h": DoubleType,
        "av_v": DoubleType,

        "ar_ax": DoubleType,
        "ar_h": DoubleType,
        "ar_v": DoubleType,
    }

    def validate_required_columns(self,dataframe: DataFrame,) -> None:
        """
        Vérifie que toutes les colonnes métier
        obligatoires sont présentes.

        Cette méthode ne modifie pas le DataFrame.
        Elle lève une exception si au moins une
        colonne est absente.

        Parameters
        ----------
        dataframe : DataFrame
            DataFrame Spark à valider.
        """

        if dataframe is None:
            raise ValueError("Le DataFrame reçu est None.")

        logger.info("Validation des colonnes obligatoires.")

        missing_columns = sorted(
            set(self.REQUIRED_COLUMNS)
            - set(dataframe.columns)
        )

        if missing_columns:
            message = (
                    "Colonnes obligatoires absentes : "
                    + ", ".join(missing_columns)
            )
            logger.error(message)

            raise MissingRequiredColumnError(
                message
            )

        logger.success(
            "Toutes les colonnes obligatoires sont présentes."
        )


    #Cette méthode doit être exécutée après Standardizer, et non juste après le Reader
    def validate_schema(self, dataframe: DataFrame) -> None:
        """
        Vérifie que le schéma Spark correspond
        au schéma attendu.

        Cette méthode ne modifie pas le DataFrame.

        Parameters
        ----------
        dataframe : DataFrame
            DataFrame Spark à valider.
        """

        if dataframe is None:
            raise ValueError("Le DataFrame reçu est None.")

        logger.info("Validation du schéma Spark.")

        dataframe_schema = {
            field.name: type(field.dataType)
            for field in dataframe.schema.fields
        }

        invalid_columns = []

        for column, expected_type in self.EXPECTED_SCHEMA.items():

            current_type = dataframe_schema.get(column)

            if current_type is None:
                continue

            if current_type != expected_type:
                invalid_columns.append(
                    (
                        column,
                        expected_type.__name__,
                        current_type.__name__,
                    )
                )

        if invalid_columns:
            details = "\n".join(
                f"{column} : attendu={expected} | actuel={current}"
                for column, expected, current in invalid_columns
            )

            logger.error(
                "Schéma invalide.\n"
                + details
            )

            raise InvalidSchemaError(
                "Le schéma Spark est invalide.",
                details,
            )

        logger.success("Schéma Spark validé.")

