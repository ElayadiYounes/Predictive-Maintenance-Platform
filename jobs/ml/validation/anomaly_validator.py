import pandas as pd
from jobs.common.logger import logger


class InspectionAnomalyValidator:
    """ Valide les anomalies détectées par Isolation Forest à partir des seuils métier propres à chaque équipement.
    Logique :
    Isolation Forest
       |
       | anomaly_flag
       v
    Validation seuils
       |
       v
    validated_anomaly
    Une anomalie est considérée comme validée lorsque :
    anomaly_flag == 1 ET au moins une mesure dépasse son seuil métier.
    """

    REQUIRED_COLUMNS = [
        # Les identifiants
        "id_inspection",
        "id_equipement",

        # Température (avant)
        "t_av",

        # Vibration
        "av_ax", "av_h", "av_v",
        "ar_ax", "ar_h", "ar_v",

        # Caractéristiques techniques binaires
        "p_produit",
        "huile_graisse",
        "ailette", "boulonneries",
        "cable",
        "plaque_a_borne",
        "graisseur",

        # Seuils métier
        "seuil_danger_temp",
        "seuil_danger_vib_axiale",
        "seuil_danger_vib_horiz",
        "seuil_danger_vib_vert",

        # Ratios pré-calculés par rapport aux seuils
        "ratio_temp",
        "ratio_vib_axiale",
        "ratio_vib_horiz",
        "ratio_vib_vert",
    ]
    MODEL_COLUMNS = [
        "anomaly_score",
        "anomaly_flag",
        "model_type",
    ]

    ALERT_COLUMNS = [
        "threshold_alert_temp",
        "threshold_alert_vib_axiale",
        "threshold_alert_vib_horiz",
        "threshold_alert_vib_vert",
    ]

    def __init__(self)->None:
        """Initialise le validateur métier."""
        pass

    def _validate_input(self, dataframe : pd.DataFrame) -> None:
        """ Vérifie que le DataFrame contient les colonnes nécessaires. """
        if dataframe is None:
            raise ValueError("Le DataFrame d'anomalies est None.")
        if dataframe.empty:
            raise ValueError("Le DataFrame d'anomalies est Vide.")

        required_columns = [
            self.REQUIRED_COLUMNS +
            self.MODEL_COLUMNS
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in dataframe.columns
        ]

        if missing_columns:
            raise ValueError( f"Colonnes nécessaires à la validation absentes : {missing_columns}" )




     #-------------------- Validation par Mesure-------------------------------

    @staticmethod
    def _build_threshold_alerts(dataframe : pd.DataFrame)->pd.DataFrame:
        """ Construit les alertes métier à partir des mesures et des seuils propres à chaque équipement. """

        dataframe = dataframe.copy()

        # ------ Température --------
        dataframe["threshold_alert_temp"] =(
           dataframe["ratio_temp"] >= 1
        ).astype(int)

        # ------ vibration Axiale --------
        dataframe["threshold_alert_vib_axiale"] = (
            dataframe["ratio_vib_axiale"] >= 1
        ).astype(int)

        # ------ vibration horizontal--------
        dataframe["threshold_alert_vib_horiz"] = (
            dataframe["ratio_vib_horiz"] >= 1
        ).astype(int)

        # ------ vibration vertical --------
        dataframe["threshold_alert_vib_vert"] = (
            dataframe["ratio_vib_vert"] >= 1
        ).astype(int)

        return dataframe

    #---------------------------- Validation Global -----------------------------

    def _build_threshold_alert_global(self,dataframe : pd.DataFrame)->pd.DataFrame:
        """ Détermine si au moins un seuil métier est dépassé. """
        dataframe = dataframe.copy()

        dataframe["threshold_alert"] =(
            dataframe[self.ALERT_COLUMNS].max(axis=1)
        ).astype(int)

        return dataframe

    # Validation de l'anomalie ML
    @staticmethod
    def _build_validated_anomaly(dataframe : pd.DataFrame) -> pd.DataFrame:
        """ Combine la détection Isolation Forest et la validation par seuil métier.
         Une anomalie est validée si :
         anomaly_flag == 1 ET threshold_alert == 1
         """
        dataframe = dataframe.copy()

        dataframe["validated_anomaly"] = (
            (
                dataframe["anomaly_flag"] == 1
            )
            &
            (
                dataframe["threshold_alert"] == 1
            )
        ).astype(int)

        return dataframe

    #------------------------ Classification métier -------------------------
    @staticmethod
    def _build_anomaly_status(dataframe : pd.DataFrame) -> pd.DataFrame:
        """ Produit un statut permettant de distinguer les différents cas ML / métier. """
        dataframe = dataframe.copy()
        dataframe["anomaly_status"] = "normal"

        #-------------- 1er cas : ML uniquement -------------------
        dataframe.loc[
            (
                dataframe["anomaly_flag"] == 1
            )
            &
            (
                dataframe["threshold_alert"] == 0
            ),
            "anomaly_status"
        ] = "ml_anomaly_only"

        #------------------- 2eme cas : seuil métier uniquement -------------------------

        dataframe.loc[
            (
                dataframe["anomaly_flag"] == 0
            )
            &
            (
                dataframe["threshold_alert"] == 1
            ),
            "anomaly_status"
        ] = "threshold_alert_only"

        #------------------- 3eme cas : seuils + ML ---------------------
        dataframe.loc[
            (
                dataframe["anomaly_flag"] == 1
            )
            &
            (
                dataframe["threshold_alert"] == 1
            ),
            "anomaly_status"
        ] = "validated_anomaly"

        return dataframe

    













