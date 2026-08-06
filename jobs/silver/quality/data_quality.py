from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from jobs.common.logger import logger
from jobs.common.exceptions import MissingRequiredColumnError, InvalidSchemaError, HighNullRatioError, InvalidNumericRangeError
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
    TEMPERATURE_COLUMNS = [
        "t_av",
        "t_ar",
    ]
    VIBRATION_COLUMNS = [
        "av_ax",
        "av_h",
        "av_v",
        "ar_ax",
        "ar_h",
        "ar_v",
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
    MAX_NULL_RATIO = 0.3
    NULL_RATIO_EXCLUDED_COLUMNS = [
        "observation",
        "action",
    ]

    #ces valeurs est provisiore je vais valider les vrais valeurs avac l'encadrent
    TEMPERATURE_MIN = 0
    TEMPERATURE_MAX = 120

    VIBRATION_MIN = 0
    VIBRATION_MAX = 50

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


    def validate_null_ratio(self, dataframe: DataFrame) -> None:
        """
        Vérifie que le pourcentage de valeurs
        manquantes de chaque colonne reste
        inférieur au seuil autorisé.

        Les colonnes dont le taux de valeurs
        manquantes dépasse le seuil provoquent
        une exception.

        Parameters
        ----------
        dataframe : DataFrame
            DataFrame Spark à valider.
        """

        if dataframe is None:
            raise ValueError("Le DataFrame reçu est None.")

        logger.info("Validation du taux de valeurs manquantes.")

        total_rows = dataframe.count()

        if total_rows == 0:
            logger.warning("Le DataFrame est vide.")
            return

        invalid_columns = []

        columns_to_validate = [
            column
            for column in dataframe.columns
            if column not in self.NULL_RATIO_EXCLUDED_COLUMNS
        ]

        for column in columns_to_validate:

            null_count = (
                dataframe
                .filter(F.col(column).isNull())
                .count()
            )

            null_ratio = null_count / total_rows

            logger.debug(
                f"{column} : "
                f"{null_count}/{total_rows} "
                f"({null_ratio:.2%})"
            )

            if null_ratio > self.MAX_NULL_RATIO:
                invalid_columns.append(
                    (
                        column,
                        null_count,
                        null_ratio,
                    )
                )

        if invalid_columns:
            details = "\n".join(
                (
                    f"{column} : "
                    f"{count} valeurs manquantes "
                    f"({ratio:.2%})"
                )
                for column, count, ratio in invalid_columns
            )

            logger.error(
                "Le taux de valeurs manquantes dépasse "
                "le seuil autorisé.\n"
                + details
            )

            raise HighNullRatioError(
                "Le taux de valeurs manquantes est trop élevé.",
                details,
            )

        logger.success("Validation du taux de valeurs manquantes terminée.")

    def validate_numeric_ranges(self, dataframe: DataFrame) -> None:
        """
        Vérifie que les mesures numériques
        restent dans des plages physiques
        plausibles.

        Les lignes ne sont pas supprimées.
        Une exception est levée lorsqu'une
        colonne contient des valeurs hors plage.
        """

        if dataframe is None:
            raise ValueError("Le DataFrame reçu est None.")

        logger.info("Validation des plages numériques.")

        invalid_columns = []

        # -----------------------------
        # Températures
        # -----------------------------
        for column in self.TEMPERATURE_COLUMNS:

            if column not in dataframe.columns:
                continue

            invalid_count = (
                dataframe
                .filter( (F.col(column) < self.TEMPERATURE_MIN) | (F.col(column) > self.TEMPERATURE_MAX)
                )
                .count()
            )

            if invalid_count > 0:
                invalid_columns.append(
                    (
                        column,
                        invalid_count,
                        f"[{self.TEMPERATURE_MIN}, {self.TEMPERATURE_MAX}]",
                    )
                )

        # -----------------------------
        # Vibrations
        # -----------------------------
        for column in self.VIBRATION_COLUMNS:

            if column not in dataframe.columns:
                continue

            invalid_count = (
                dataframe
                .filter(
                    (F.col(column) < self.VIBRATION_MIN)
                    |
                    (F.col(column) > self.VIBRATION_MAX)
                )
                .count()
            )

            if invalid_count > 0:
                invalid_columns.append(
                    (
                        column,
                        invalid_count,
                        f"[{self.VIBRATION_MIN}, {self.VIBRATION_MAX}]",
                    )
                )

        if invalid_columns:
            details = "\n".join(
                f"{column} : {count} valeur(s) hors plage {expected_range}"
                for column, count, expected_range in invalid_columns
            )

            logger.error(
                "Valeurs numériques incohérentes détectées.\n"
                + details
            )

            raise InvalidNumericRangeError(
                "Des valeurs numériques sont hors des plages autorisées.",
                details,
            )

        logger.success("Validation des plages numériques terminée.")


    """
    pour v1  ça suffisant, et par la suite on va implémenter quelque chose comme : 
    validate_unique_primary_key()

    validate_future_dates()

    validate_binary_values()

    validate_string_length()

    validate_duplicate_primary_key() 
    ....
    """



