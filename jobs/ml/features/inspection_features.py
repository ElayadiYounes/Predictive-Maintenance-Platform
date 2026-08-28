import pandas as pd
from jobs.common.logger import logger

class InspectionFeatureEngineering :
    """
    Construit les features d'inspection destinées au modèle
    Isolation Forest.

    Les features sont construites à partir :
        - des mesures de température ;
        - des mesures de vibration ;
        - des agrégations avant/arrière ;
        - des seuils de danger propres à chaque équipement.

    Cette classe ne produit pas :
        - anomaly_score ;
        - anomaly_flag ;
        - prédiction de panne ;
        - RUL.
    """
    REQUIRED_COLUMNS = [
        #les identifients
        "id_inspection",
        "id_equipement",

        #temperature (avant)
        "t_av",

        #vibration
        "av_ax",
        "av_h",
        "av_v",
        "ar_ax",
        "ar_h",
        "ar_v",

        # Seuils métier 
        "seuil_danger_temp",
        "seuil_danger_vib_axiale",
        "seuil_danger_vib_horiz",
        "seuil_danger_vib_vert",

        # Ratios par rapport aux seuils
        "ratio_temp",
        "ratio_vib_axiale",
        "ratio_vib_horiz",
        "ratio_vib_vert",
    ]

    FEATURE_COLUMNS = [

        # Vibration axiale
        "vibration_axiale_max",
        "vibration_axiale_mean",
        "vibration_axiale_difference",

        # Vibration horizontale
        "vibration_horiz_max",
        "vibration_horiz_mean",
        "vibration_horiz_difference",

        # Vibration verticale
        "vibration_vert_max",
        "vibration_vert_mean",
        "vibration_vert_difference",

    ]

    ###################### Methodes ##########################
    def __init__(self) -> None:
        """Initialise le Feature Engineer."""

    # =========================================================
    # Validation
    # =========================================================

    def _validate_input(self, dataframe : pd.DataFrame) -> None:
        """ Vérifie que le DataFrame contient les colonnes nécessaires. """
        if dataframe is None:
            raise ValueError("Le DataFrame d'inspection est None.")

        if dataframe.empty:
            raise ValueError("Le DataFrame d'inspection est None.")

        missing_columns = [column for column in self.REQUIRED_COLUMNS
                           if column not in dataframe.columns
        ]
        if missing_columns:
            raise ValueError(f"Les colonnes nécessaires aux features absentes sont : {missing_columns}")

    @staticmethod
    def _build_vibration_features(dataframe : pd.DataFrame) -> pd.DataFrame:
        """ Construit les features de vibration pour les axes :
          - axial ;
          - horizontal ;
          - vertical.
        """

        dataframe = dataframe.copy()

        # -----------------------------------------------------
        # Axiale
        # -----------------------------------------------------
        dataframe["vibration_axiale_max"] = dataframe[["av_ax","ar_ax"]].max(axis=1)
        dataframe["vibration_axiale_mean"] = dataframe[["av_ax", "ar_ax"]].mean(axis=1)
        dataframe["vibration_axiale_difference"] = (dataframe["av_ax"] - dataframe["ar_ax"]).abs()

        # -----------------------------------------------------
        # horizontal
        # -----------------------------------------------------
        dataframe["vibration_horiz_max"] = dataframe[["av_h", "ar_h"]].max(axis=1)
        dataframe["vibration_horiz_mean"] = dataframe[["av_h", "ar_h"]].mean(axis=1)
        dataframe["vibration_horiz_difference"] = (dataframe["av_h"] - dataframe["ar_h"]).abs()

        # -----------------------------------------------------
        # Axiale
        # -----------------------------------------------------
        dataframe["vibration_vert_max"] = dataframe[["av_v","ar_v"]].max(axis=1)
        dataframe["vibration_vert_mean"] = dataframe[["av_v", "ar_v"]].mean(axis=1)
        dataframe["vibration_vert_difference"] = (dataframe["av_v"] - dataframe["ar_v"]).abs()

        return dataframe


    def build_feature_engineering(self, dataframe : pd.DataFrame) -> pd.DataFrame:
        """ Construit le dataset de features ML à partir de Gold.
        Parameters
        ----------
        dataframe : pd.DataFrame Table Gold fact_inspection.
        Returns
        -------
        pd.DataFrame Dataset contenant les identifiants,
         les features et les informations nécessaires à la validation métier.
         """
        logger.info("=" * 70)
        logger.info("INSPECTION FEATURE ENGINEERING START")
        logger.info("=" * 70)

        self._validate_input(dataframe)
        logger.info(f"Dataset reçu : " f"{len(dataframe):,} lignes.")

        # -----------------------------------------------------
        # 3. Features vibrations
        # -----------------------------------------------------
        dataframe = self._build_vibration_features(dataframe)

        dataframe = dataframe.dropna(subset=self.FEATURE_COLUMNS).copy()

        if dataframe.empty:
            raise ValueError("Aucune observation valide après " "la construction des features.")

        output_columns = [
            "id_inspection",
            "id_equipement",

            "t_av",

            *self.FEATURE_COLUMNS,

            "seuil_danger_temp",
            "seuil_danger_vib_axiale",
            "seuil_danger_vib_horiz",
            "seuil_danger_vib_vert",

        ]
        features = dataframe[output_columns].copy()

        logger.success(
            f"Inspection Feature Engineering terminé : {len(features):,} lignes,"
            f" {len(self.FEATURE_COLUMNS)} features."
        )
        return features














