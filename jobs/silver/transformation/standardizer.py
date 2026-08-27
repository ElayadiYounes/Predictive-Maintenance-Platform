import re
from typing import Optional

from jobs.common.logger import logger
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

class InspectionStandardizer :
    """
    Responsable de l'uniformisation des données d'inspection.

    Responsabilités :
    - standardiser les noms des colonnes ;
    - uniformiser les valeurs textuelles ;
    - corriger les problèmes d'encodage ;
    - harmoniser les types de données.
    """

    TEXT_COLUMNS = [
        "zone",
        "instal",
        "observation",
        "action",
        "utilisateur",
    ]

    BINARY_COLUMNS = [
        "p_produit",
        "huile_graisse",
        "ailette",
        "boulonneries",
        "cable",
        "plaque_a_borne",
        "graisseur",
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

    LIMITE_COLUMNS = {
        "INSTALL" : "instal",
        "TAV" : "t_av_limite",
        "VAX" : "v_ax_limite",
        "VH" : "v_h_limite",
        "VV" : "v_v_limite"
    }

    LIMITE_NUMIRIC_COLUMNS = [
        "t_av_limite",
        "v_ax_limite",
        "v_h_limite",
        "v_v_limite"
    ]



    @staticmethod
    def standardize_column_names(dataframe : DataFrame) -> DataFrame :
        """ Standardise les noms des colonnes.
         Règles :
         - conversion en minuscules ;
         - remplacement des caractères non alphanumériques par un underscore ;
         - suppression des underscores au début et à la fin ;
         - réduction des underscores multiples.
        """

        logger.info("Début de la Standardisation des noms de colonnes ")

        standardized_dataframe = dataframe

        for old_name in dataframe.columns :

            new_name = old_name.strip().lower()

            new_name = re.sub(r"[^a-z0-9]+", "_", new_name, )

            new_name = re.sub(r"_+", "_", new_name, )

            new_name = new_name.strip("_")

            if new_name != old_name :
                logger.debug(f"Colonne Renommée : {old_name} => {new_name}")
                standardized_dataframe = (
                standardized_dataframe
                .withColumnRenamed(old_name, new_name, )
                )

        logger.success("Standardisation des noms de colonnes Terminée.")

        return standardized_dataframe

    @staticmethod
    def _fix_encoding(value: Optional[str]) -> Optional[str]:
        """ Corrige certains textes UTF-8 interprétés à tort comme des caractères Latin-1.
            Exemple : DÃ©chargement -> Déchargement Si la correction est impossible ou inutile,
            la valeur originale est conservée.
          """
        if value is None:
            return None

        try:
            return value.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError,):
            return value



    def standardize_text_values(self, dataframe : DataFrame) -> DataFrame :
        """ Standardise les valeurs des colonnes textuelles.
         Opérations :
          - correction de certains problèmes d'encodage ;
          - suppression des espaces au début et à la fin ;
          - réduction des espaces multiples ;
          - uniformisation de la colonne instal.
         Les valeurs NULL sont conservées.
        """
        logger.info("Début de la standardisation des valeurs textuelles.")

        standardized_dataframe = dataframe

        fix_encoding_udf = F.udf(self._fix_encoding, StringType(), )

        available_columns = [
            column for column in self.TEXT_COLUMNS
            if column in standardized_dataframe.columns
        ]

        for column in available_columns :
            standardized_dataframe = (
                standardized_dataframe
                .withColumn(column, fix_encoding_udf(F.col(column)))
            )

        # La référence de l'installation doit être uniforme.
        if "instal" in standardized_dataframe.columns:
            standardized_dataframe = (
                standardized_dataframe
                .withColumn( "instal", F.upper( F.col("instal") ) )
            )

        logger.success("Standardization des valeurs textuelles Terminée .")

        return standardized_dataframe


    def standardize_data_types(self, dataframe : DataFrame) -> DataFrame:
        """
        Standardise les types de données des colonnes
        de la table inspection.

        Règles :
        - id : IntegerType ;
        - date : TimestampType ;
        - indicateurs binaires : IntegerType ;
        - températures : DoubleType ;
        - vibrations : DoubleType ;
        - colonnes textuelles : StringType.

        Les valeurs NULL sont conservées.
        """

        logger.info("Début de la standardisation des types de données .")

        standardized_dataframe = dataframe

        # étape 1 : conversion type id
        if "id" in standardized_dataframe.columns:
            standardized_dataframe = (
                standardized_dataframe
                .withColumn("id", F.col("id").cast("int"), )
            )
        #étape 2 : conversion type date
        if "date" in standardized_dataframe.columns:
            standardized_dataframe = (
            standardized_dataframe
            .withColumn("date", F.col("date").cast("date"), )
            )
        #étape 3 : les indicateur binaires
        for column in self.BINARY_COLUMNS:
            if column in standardized_dataframe.columns:
                standardized_dataframe = (
                standardized_dataframe
                .withColumn(column, F.col(column).cast("int"), )
                )
        #étape 4 : conversion temperature
        for column in self.TEMPERATURE_COLUMNS:
            if column in standardized_dataframe.columns:
                standardized_dataframe = (
                    standardized_dataframe
                    .withColumn(column, F.col(column).cast("double"), )
                )

        # Vibrations
        for column in self.VIBRATION_COLUMNS:
            if column in standardized_dataframe.columns:
                standardized_dataframe = (
                    standardized_dataframe
                    .withColumn(column, F.col(column).cast("double"), )
                )

        # Colonnes textuelles
        for column in self.TEXT_COLUMNS:
            if column in standardized_dataframe.columns:
                standardized_dataframe = (
                    standardized_dataframe
                    .withColumn(
                        column,
                        F.col(column).cast("string"),
                    )
                )

        logger.success("Standardisation des types de données Terminée")

        return standardized_dataframe

    def limite_standardize_column_names(self,dataframe : DataFrame) -> DataFrame:

        logger.info("Début de la Standardisation des noms de colonnes ")

        standardized_dataframe = dataframe

        for old_name , new_name in self.LIMITE_COLUMNS :
            if old_name in standardized_dataframe.columns:
                logger.debug(f"Colonne Renommée : {old_name} => {new_name}")
                standardized_dataframe = (
                        standardized_dataframe
                        .withColumnRenamed(old_name, new_name, )
                )
        logger.success("Standardisation des noms de colonnes Terminée.")

        return standardized_dataframe

    def limite_standardize_data_types(self,dataframe : DataFrame) -> DataFrame:

        logger.info("Début de la standardisation des types de données .")

        standardized_dataframe = dataframe

        # La référence de l'installation doit être uniforme.de type string
        if "instal" in standardized_dataframe.columns:
            standardized_dataframe = (
                standardized_dataframe
                .withColumn("instal", F.upper(F.col("instal").cast("string")), )
            )


        for column in self.LIMITE_NUMIRIC_COLUMNS:
            if column in standardized_dataframe.columns:
                standardized_dataframe = (
                        standardized_dataframe
                        .withColumn(column, F.col(column).cast("double"), )
                    )

        logger.success("Standardisation des types de données Terminée")

        return standardized_dataframe










    






    




