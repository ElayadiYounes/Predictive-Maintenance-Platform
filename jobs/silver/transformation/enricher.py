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
                F.round((F.col("t_av") + F.col("t_ar")) / F.lit(2.0)),
            )
            .withColumn(
                "temperature_difference",
                 F.abs(F.col("t_av") - F.col("t_ar")),
            )
        )
        logger.success("Enrichissement des variables de température terminé.")

        return enriched_dataframe

    def enrich_vibration_features(self, dataframe : DataFrame) -> DataFrame :
        """
        Crée des variables dérivées à partir des
        mesures de vibration avant et arrière.

        Variables créées :
        - vibration_av_max :
          vibration maximale côté avant ;
        - vibration_ar_max :
          vibration maximale côté arrière ;
        - vibration_max :
          vibration maximale parmi les six mesures ;
        - vibration_av_mean :
          vibration moyenne côté avant ;
        - vibration_ar_mean :
          vibration moyenne côté arrière ;
        - vibration_mean :
          vibration moyenne globale ;
        - vibration_side_difference :
          différence absolue entre les vibrations
          moyennes avant et arrière.

        Les mesures originales sont conservées.

        Parameters
        ----------
        dataframe : DataFrame
            DataFrame Spark contenant les données
            d'inspection.

        Returns
        -------
        DataFrame
            DataFrame enrichi avec les variables
            dérivées des vibrations.
        """

        if dataframe is None:
            raise ValueError("DataFrame reçu par enrich_vibration_features est None.")

        required_columns = (self.REAR_VIBRATION_COLUMNS + self.FRONT_VIBRATION_COLUMNS)
        missing_columns = [
            column for column in required_columns
            if column not in dataframe.columns
        ]
        if missing_columns:
            raise ValueError(f"Colonnes de vibration manquantes : {', '.join(missing_columns)}.")

        enriched_dataframe = (
            dataframe
            # Vibration maximale côté avant
            .withColumn(
                "vibration_av_max",
                F.greatest( *[ F.col(column) for column in self.FRONT_VIBRATION_COLUMNS ] ),
            )
            # Vibration maximale côté arrière
            .withColumn(
                "vibration_ar_max",
                F.greatest( *[ F.col(column) for column in self.REAR_VIBRATION_COLUMNS ] ),
            )
            # Vibration maximale globale
            .withColumn(
                "vibration_max",
                F.greatest( *[ F.col(column) for column in required_columns ] ),
            )
            # Vibration moyenne côté avant
            .withColumn(
                "vibration_av_mean",
                F.round(( F.col("av_ax") + F.col("av_h") + F.col("av_v") ) / F.lit(3.0)),
            )
            # Vibration moyenne côté arrière
            .withColumn(
                "vibration_ar_mean",
                F.round(( F.col("ar_ax") + F.col("ar_h") + F.col("ar_v") ) / F.lit(3.0)),
            )
        )

    # Calcul de la moyenne globale et de la différence entre les deux côtés.
        enriched_dataframe = (
            enriched_dataframe
            .withColumn(
                "vibration_mean",
               F.round(( F.col("av_ax") + F.col("av_h") + F.col("av_v") + F.col("ar_ax") + F.col("ar_h") + F.col("ar_v") ) / F.lit(6.0)),
            )
            .withColumn(
                "vibration_side_difference",
                F.abs(F.col("vibration_av_mean") - F.col("vibration_ar_mean")), )
        )

        logger.success("L'enrichissement des variables de Vibration Terminé .")

        return enriched_dataframe

    @staticmethod
    def enrich_temporal_features(dataframe : DataFrame ) -> DataFrame:
        """
        Crée des variables temporelles à partir
        de la colonne date.

        Variables créées :
        - inspection_year :
          année de l'inspection ;
        - inspection_month :
          mois de l'inspection ;
        - inspection_day :
          jour du mois de l'inspection.

        La colonne date originale est conservée.

        Parameters
        ----------
        dataframe : DataFrame
            DataFrame Spark contenant les données
            d'inspection.

        Returns
        -------
        DataFrame
            DataFrame enrichi avec les variables
            temporelles.
        """

        if dataframe is None:
            raise ValueError("Le DataFrame reçu par enrich_temporal_features est None.")

        logger.info("Début d'enrichissement des variables temporelles .")

        if "date" not in dataframe.columns:
            raise ValueError("La colonne 'date' est absente du DataFrame.")

        enriched_dataframe = (
            dataframe
            .withColumn(
                "inspection_year",
                F.year(F.col("date")),
            )
            .withColumn(
                "inspection_month",
                F.month(F.col("date")),
            )
            .withColumn(
                "inspection_day",
                F.day(F.col("date")),
            )
        )
        logger.success("Enrichissement des variables temporelles terminé.")

        return enriched_dataframe

    def enrich(self, dataframe : DataFrame) -> DataFrame:
        """
        Orchestre l'ensemble des opérations
        d'enrichissement des données d'inspection.

        Étapes :
        1. création des variables de température ;
        2. création des variables de vibration ;
        3. création des variables temporelles.

        Parameters
        ----------
        dataframe : DataFrame
            DataFrame Spark à enrichir.

        Returns
        -------
        DataFrame
            DataFrame enrichi.
        """

        if dataframe is None:
            raise ValueError("Le DataFrame reçu par enrich() est None")

        logger.info("Début de l'enrichissement des données")

        enriched_dataframe = dataframe

        enriched_dataframe = self.enrich_temperature_features(enriched_dataframe)
        enriched_dataframe = self.enrich_vibration_features(enriched_dataframe)
        enriched_dataframe = self.enrich_temporal_features(enriched_dataframe)

        logger.success("Enrichissement Génerale Terminé avec succes.")

        return enriched_dataframe



    










