from pyspark.sql import DataFrame
from jobs.common.logger import logger
from jobs.common.exceptions import MissingRequiredColumnError



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

