from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from jobs.common.logger import logger

class InspectionCleaner:

    REQUIRED_COLUMNS = [
        "id",
        "date",
    ]

    TEXT_COLUMNS = [
        "zone",
        "instal",
        "observation",
        "action",
        "utilisateur",
    ]

    def clean(self, dataframe: DataFrame) -> DataFrame:
        """
        Nettoie le DataFrame Bronze et retourne
        un DataFrame prêt pour la standardisation.

        Étapes :
        1. Vérification du DataFrame ;
        2. Suppression des doublons exacts ;
        3. Suppression des lignes sans identifiant ;
        4. Suppression des lignes sans date ;
        5. Suppression des espaces inutiles ;
        6. Conversion des chaînes vides en NULL.
        """

        if dataframe is None:
            raise ValueError(
                "Le DataFrame reçu par InspectionCleaner est None."
            )

        initial_count = dataframe.count()

        logger.info( f"Début du nettoyage : {initial_count:,} lignes.")

        cleaned_dataframe = dataframe

        # 1. Suppression des doublons exacts

        cleaned_dataframe = cleaned_dataframe.dropDuplicates()

        after_duplicates_count = cleaned_dataframe.count()

        duplicates_removed = (initial_count - after_duplicates_count)

        logger.info(f"Doublons exacts supprimés : {duplicates_removed:,}.")

        # 2. Suppression des lignes sans identifiant

        cleaned_dataframe = cleaned_dataframe.filter(F.col("id").isNotNull())

        after_id_count = cleaned_dataframe.count()

        missing_id_removed = (
                after_duplicates_count - after_id_count
        )

        logger.info(
            f"Lignes sans identifiant supprimées : "
            f"{missing_id_removed:,}."
        )

        # 3. Suppression des lignes sans date

        cleaned_dataframe = cleaned_dataframe.filter(F.col("date").isNotNull())

        after_date_count = cleaned_dataframe.count()

        missing_date_removed = (after_id_count - after_date_count)

        logger.info(f"Lignes sans date supprimées : {missing_date_removed:,}.")

        # 4. Nettoyage des colonnes textuelles

        available_text_columns = [
            column
            for column in self.TEXT_COLUMNS
            if column in cleaned_dataframe.columns
        ]

        for column in available_text_columns:
            cleaned_dataframe = cleaned_dataframe.withColumn(
                column,
                F.when(
                    F.trim(F.col(column)) == "",
                    F.lit(None),
                ).otherwise(
                    F.trim(F.col(column))
                ),
            )

        logger.info(
            "Colonnes textuelles nettoyées : "
            f"{', '.join(available_text_columns)}."
        )

        final_count = cleaned_dataframe.count()

        total_removed = initial_count - final_count

        logger.success(
            "Nettoyage terminé : "
            f"{final_count:,} lignes conservées, "
            f"{total_removed:,} lignes supprimées."
        )

        return cleaned_dataframe


    def clean_missing_values(self, dataframe: DataFrame) -> DataFrame:
        """on va implementer par la suite"""
        pass




