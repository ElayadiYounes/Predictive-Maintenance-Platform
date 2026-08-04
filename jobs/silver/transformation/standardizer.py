import re

from jobs.common.logger import logger
from pyspark.sql import DataFrame

class InspectionStandardizer :
    """
    Responsable de l'uniformisation des données d'inspection.

    Responsabilités :
    - standardiser les noms des colonnes ;
    - uniformiser les valeurs textuelles ;
    - corriger les problèmes d'encodage ;
    - harmoniser les types de données.
    """


    def standardize_column_names(self,dataframe : DataFrame) -> DataFrame :
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

        logger.success("Standardisation des noms de colonnes terminée.")

        return standardized_dataframe

    




