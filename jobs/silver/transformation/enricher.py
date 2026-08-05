from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from jobs.common.logger import logger


class InspectionEnricher:
    """
    Responsable de l'enrichissement des données
    d'inspection.

    Responsabilités :
    - créer des indicateurs dérivés à partir
      des températures ;
    - créer des indicateurs dérivés à partir
      des vibrations ;
    - produire des variables utiles pour
      l'analyse métier et les futurs modèles ML.

    Le composant ne modifie pas les mesures
    d'origine.
    """

    TEMPERATURE_COLUMNS = [
        "t_av",
        "t_ar",
    ]

    FRONT_VIBRATION_COLUMNS = [
        "av_ax",
        "av_h",
        "av_v",
    ]

    REAR_VIBRATION_COLUMNS = [
        "ar_ax",
        "ar_h",
        "ar_v",
    ]

    def enrich_temperature_features(self, dataframe : DataFrame) -> DataFrame :
        """
        Crée des variables dérivées à partir des
        températures avant et arrière.

        Variables créées :
        - temperature_max : température maximale entre l'avant et l'arrière ;
        - temperature_mean : température moyenne entre l'avant et l'arrière ;
        - temperature_difference : différence absolue entre les températures avant et arrière.
        Les colonnes originales t_av et t_ar sont conservées.
        Parameters
        ----------
        dataframe : DataFrame
            DataFrame Spark contenant les données
            d'inspection.
        Returns
        -------
        DataFrame
            DataFrame enrichi avec les variables
            de température.
        """

        if dataframe is None:
            raise ValueError("Le DataFrame reçu par " "enrich_temperature_features est None.")

        logger.info("Débute de l'enrichissement des variables de Température .")

        missing_columns = [
            column for column in self.TEMPERATURE_COLUMNS
            if column not in dataframe.columns
        ]

        if missing_columns:
            raise ValueError(f"Colonnes de température manquantes : {', '.join(missing_columns)}.")

        enriched_dataframe = (
            dataframe
            .withColumn(
                "temperature_max",
                 F.greatest(F.col("t_av"), F.col("t_ar"), ),
            )
            .withColumn(
                "temperature_mean",
                (F.col("t_av") + F.col("t_ar")) / F.lit(2.0),
            )
            .withColumn(
                "temperature_difference",
                 F.abs(F.col("t_av") - F.col("t_ar")),
            )
        )
        logger.success("Enrichissement des variables de température terminé.")

        return enriched_dataframe









