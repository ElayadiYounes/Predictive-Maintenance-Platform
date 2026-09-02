import pandas as pd
from jobs.common.logger import logger


class InspectionAnomalyValidator:
    """
    Valide les anomalies détectées par Isolation Forest
    en les confrontant aux alertes métier calculées dans Gold.

    Logique
    -------
    Gold
        |
        ├── alert_temperature
        ├── alert_vib_axiale
        ├── alert_vib_horiz
        └── alert_vib_vert
        |
        v
    threshold_alert
        |
        +----------------------+
        |                      |
        v                      v
    anomaly_flag          threshold_alert
        |                      |
        +----------+-----------+
                   |
                   v
          validated_anomaly

    Une anomalie est considérée comme validée lorsque :
        anomaly_flag == 1
        ET
        threshold_alert == 1.
    """

    REQUIRED_COLUMNS = [
        # Identifiants
        "id_inspection",
        "id_equipement",

        # Alertes métier calculées dans Gold
        "alert_temperature",
        "alert_vib_axiale",
        "alert_vib_horiz",
        "alert_vib_vert",
    ]

    MODEL_COLUMNS = [
        "anomaly_score",
        "anomaly_flag",
        "model_type",
    ]

    ALERT_COLUMNS = [
        "alert_temperature",
        "alert_vib_axiale",
        "alert_vib_horiz",
        "alert_vib_vert",
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

        required_columns = self.REQUIRED_COLUMNS + self.MODEL_COLUMNS

        missing_columns = [
            column
            for column in required_columns
            if column not in dataframe.columns
        ]

        if missing_columns:
            raise ValueError( f"Colonnes nécessaires à la validation absentes : {missing_columns}" )


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



    #--------------------- Pipeline Validation -------------------
    def validate(self,dataframe : pd.DataFrame) -> pd.DataFrame:
        """ Valide les anomalies détectées par Isolation Forest.
         Parameters
         ----------
         dataframe : pd.DataFrame Dataset contenant les données d'inspection, les seuils métier et les résultats Isolation Forest.
         Returns
         -------
         pd.DataFrame Dataset enrichi avec :
         - threshold_alert_temperature - threshold_alert_vib_axiale
         - threshold_alert_vib_horiz - threshold_alert_vib_vert
         - threshold_alert - validated_anomaly - anomaly_status
         """

        logger.info("=" * 70)
        logger.info("INSPECTION ANOMALY VALIDATION START")
        logger.info("=" * 70)

        self._validate_input(dataframe)
        logger.info(f"Dataset reçu : {len(dataframe):,} lignes.")

        #étape 1 : validation global
        dataframe = self._build_threshold_alert_global(dataframe)

        #étape 2 : validation ml
        dataframe = self._build_validated_anomaly(dataframe)

        #étape final : mettre le status de chaque validation
        dataframe = self._build_anomaly_status(dataframe)

        #statistique de validation

        ml_anomaly = int(
            dataframe["anomaly_flag"]
            .fillna(0)
            .sum()
        )

        threshold_alerts = int(
            dataframe["threshold_alert"]
            .fillna(0)
            .sum()
        )

        validated_anomaly = int(
            dataframe["validated_anomaly"]
            .fillna(0)
            .sum()
        )

        logger.info(f"Les Anomalies detectée par Isolation Forest :  {ml_anomaly} ")
        logger.info(f"Les alerts detectée par les Seuils Métier : {threshold_alerts} ")
        logger.info(f"Les Anomalies confirmée par Isolation Forest ET Seuils Métier : {validated_anomaly} ")

        normal = int(
            (dataframe["anomaly_status"] == "normal").sum()
        )

        ml_anomaly_only = int(
            (dataframe["anomaly_status"] == "ml_anomaly_only").sum()
        )

        threshold_alert_only = int(
            (dataframe["anomaly_status"] == "threshold_alert_only").sum()
        )

        validated_anomaly = int(
            (dataframe["anomaly_status"] == "validated_anomaly").sum()
        )

        logger.info(f"Cas normaux : {normal}")
        logger.info(f"Anomalies ML uniquement : {ml_anomaly_only}")
        logger.info(f"Alertes métier uniquement : {threshold_alert_only}")

        logger.success("Validation des Anomalies Terminée")

        return dataframe














