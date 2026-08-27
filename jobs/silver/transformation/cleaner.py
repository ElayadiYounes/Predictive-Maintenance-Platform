from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from jobs.common.logger import logger

class InspectionCleaner:

    INSPECTION_CRITICAL_COLUMNS = [
        "id",
        "date",
        "zone",
        "instal",
    ]

    INSPECTION_TEXT_COLUMNS = [
        "zone",
        "instal",
        "observation",
        "action",
        "utilisateur",
    ]

    INSPECTION_BINARY_COLUMNS = [
        "p_produit",
        "huile_graisse",
        "ailette",
        "boulonneries",
        "cable",
        "plaque_a_borne",
        "graisseur",
    ]

    INSPECTION_TEXT_DEFAULT_VALUES = {
        "observation": "non renseignee",
        "action": "aucune action renseignee",
        "utilisateur": "inconnu",
    }

    LIMITE_CRITICAL_COLUMNS = [
        "instal",
        "t_av_limite",
        "v_ax_limite",
        "v_h_limite",
        "v_v_limite"
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
            for column in self.INSPECTION_TEXT_COLUMNS
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

        """
           Traite les valeurs manquantes des données d'inspection.

           Règles :
            - suppression des lignes dont une information critique est manquante ;
            - remplacement des valeurs manquantes des indicateurs binaires par 0 ;
            - remplacement des valeurs manquantes des champs textuels par une valeur explicite ;
            - conservation des valeurs manquantes des mesures physiques.

            Les températures et les vibrations ne sont pas imputées dans cette étape afin d'éviter l'introduction de valeurs artificielles.
        """

        if dataframe is None:
            raise ValueError("Le DataFrame reçu par clean_missing_values est None.")

        logger.info("Début du traitement des valeurs manquantes.")

        cleaned_dataframe = dataframe

        # Colonnes critiques réellement présentes
        available_critical_columns = [
            column for column in self.INSPECTION_CRITICAL_COLUMNS
            if column in cleaned_dataframe.columns
        ]

        # Suppression des lignes inexploitables
        if available_critical_columns:
            rows_before = cleaned_dataframe.count()
            cleaned_dataframe = (
                cleaned_dataframe
                .dropna( subset=available_critical_columns )
            )
            rows_after = cleaned_dataframe.count()
            removed_rows = (rows_before - rows_after)
            if removed_rows > 0:
                logger.warning(f"{removed_rows} ligne(s) supprimée(s) à cause de valeurs manquantes dans les colonnes critiques.")

        # Les indicateurs binaires manquants sont considérés comme absents.
        available_binary_columns = [
            column for column in self.INSPECTION_BINARY_COLUMNS
            if column in cleaned_dataframe.columns
        ]

        if available_binary_columns:
            cleaned_dataframe = (
            cleaned_dataframe.fillna(0, subset=available_binary_columns, )
            )

        # Remplacement des valeurs manquantes dans les champs textuels.
        available_text_defaults = {
            column: default_value for column, default_value in self.INSPECTION_TEXT_DEFAULT_VALUES.items()
            if column in cleaned_dataframe.columns
        }

        if available_text_defaults:
            cleaned_dataframe = (
                cleaned_dataframe.fillna(available_text_defaults)
            )

        logger.success("Traitement les Valeurs Manquantes Terminée .")

        return cleaned_dataframe

    @staticmethod
    def limite_clean(dataframe: DataFrame) -> DataFrame:

        if dataframe is None:
            raise ValueError(
                "Le DataFrame reçu par InspectionCleaner est None."
            )
        initial_count = dataframe.count()

        logger.info(f"Début du nettoyage : {initial_count:,} lignes.")

        cleaned_dataframe = dataframe

        # 1. Suppression des doublons exacts

        cleaned_dataframe = cleaned_dataframe.dropDuplicates()

        after_duplicates_count = cleaned_dataframe.count()

        duplicates_removed = (initial_count - after_duplicates_count)

        logger.info(f"Doublons exacts supprimés : {duplicates_removed:,}.")

        # 2. Suppression des lignes sans identifiant

        cleaned_dataframe = cleaned_dataframe.filter(F.col("instal").isNotNull())

        after_id_count = cleaned_dataframe.count()

        missing_id_removed = (
                after_duplicates_count - after_id_count
        )

        logger.info(
            f"Lignes sans identifiant supprimées : "
            f"{missing_id_removed:,}."
        )
        final_count = cleaned_dataframe.count()

        total_removed = initial_count - final_count

        logger.success(
            "Nettoyage terminé : "
            f"{final_count:,} lignes conservées, "
            f"{total_removed:,} lignes supprimées."
        )

        return cleaned_dataframe

    def limite_clean_missing_values(self, dataframe: DataFrame) -> DataFrame:
        """"""
        pass


    #remarque on va par la suite optimiser la performence de ce code avec moins des actions spark (comme count, ...)


