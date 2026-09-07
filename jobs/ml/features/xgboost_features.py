import pandas as pd
import numpy as np
from jobs.common.logger import logger

from jobs.ml.features.inspection_features import InspectionFeatureEngineering


class RULFeatureEngineering(InspectionFeatureEngineering):
    """
    Construit les features et la variable cible (RUL) destinées
    au modèle de régression XGBoost.

    Hérite de InspectionFeatureEngineering pour réutiliser le calcul
    des signatures vibratoires sans duplication de code.
    """

    def __init__(self, max_rul_days: int = 30) -> None:
        """
        Initialise le Feature Engineer pour XGBoost.

        Parameters
        ----------
        max_rul_days : int
            Seuil d'écrêtage maximal (Piecewise RUL) pour stabiliser
            l'apprentissage sur les machines neuves (par défaut 30 jours).
        """
        # Initialisation de la classe mère
        super().__init__()
        self.max_rul_days = max_rul_days

        # Surcharge des colonnes requises en entrée (Validation)
        self.REQUIRED_COLUMNS = list(set(self.REQUIRED_COLUMNS + [
            "date",  # Vraie date d'inspection (dim_time)
            "threshold_alert",  # Drapeau d'alerte global (fact_inspection_anomaly)
            "anomaly_score"  # Score de l'Isolation Forest (Feature clé)
        ]))

        # Surcharge des features d'entraînement pour inclure le score de l'IA
        self.FEATURE_COLUMNS = ["anomaly_score"] + self.FEATURE_COLUMNS

        # Surcharge des colonnes de contexte pour le livrable final
        self.CONTEXT_COLUMNS = [
            "id_inspection",
            "id_equipement",
            "date",
            "threshold_alert"
        ]

    def _compute_target_rul(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule le compte à rebours (RUL) en jours avant la prochaine threshold_alert,
        indépendamment pour chaque équipement.
        """
        logger.info("Calcul du compte à rebours RUL (Target) par équipement...")
        df = dataframe.copy()

        # Formatage de l'axe temporel
        df["date"] = pd.to_datetime(df["date"])

        # Tri chronologique indispensable pour le calcul fenêtré
        df = df.sort_values(by=["id_equipement", "date"]).reset_index(drop=True)
        processed_parts = []

        # Boucle par équipement pour isoler les cycles de dégradation
        for id_eq, group in df.groupby("id_equipement", sort=False):
            group = group.copy()

            # Extraction des vraies dates d'alertes de seuil (les points 0)
            alert_dates = group[group["threshold_alert"] == 1]["date"]

            if alert_dates.empty:
                # Si la machine ne dérive jamais, on ne peut pas entraîner de régression
                logger.debug(f"Équipement {id_eq} ignoré pour la RUL (aucune alerte de seuil).")
                continue

            # Fonction pour trouver le point 0 futur le plus proche
            def find_next_alert(current_date):
                future_alerts = alert_dates[alert_dates >= current_date]
                return future_alerts.min() if not future_alerts.empty else pd.NaT

            group["next_alert_date"] = group["date"].apply(find_next_alert)

            # On supprime les lignes situées après la toute dernière alerte (RUL impossible à calculer)
            group = group.dropna(subset=["next_alert_date"])

            # Calcul mathématique de la cible en jours
            group["target_rul"] = (group["next_alert_date"] - group["date"]).dt.days

            # Écrêtage à 30 jours (Piecewise RUL standard de l'industrie)
            group["target_rul"] = group["target_rul"].clip(upper=self.max_rul_days)

            processed_parts.append(group)

        if not processed_parts:
            raise ValueError(
                "Impossible de générer le dataset de RUL. "
                "Aucun équipement ne présente de cycle se terminant par une 'threshold_alert'."
            )

        return pd.concat(processed_parts, ignore_index=True)

    def build_feature_engineering(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Construit le dataset final pour XGBoost contenant les features physiques,
        le score de l'Isolation Forest et la variable cible 'target_rul'.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Dataset fusionné (fact_inspection_anomaly + fact_inspection + dim_time).

        Returns
        -------
        pd.DataFrame
            Dataset prêt pour l'entraînement ou l'inférence XGBoost.
        """
        logger.info("=" * 70)
        logger.info("XGBOOST RUL FEATURE ENGINEERING START")
        logger.info("=" * 70)

        # 1. Validation de la présence de toutes les colonnes (Physiques + ML + Temps)
        self._validate_input(dataframe)
        logger.info(f"Volume brut reçu : {len(dataframe):,} lignes.")

        # 2. Utilisation de la brique de vibrations de la classe mère (Héritage)
        dataframe = self._build_vibration_features(dataframe)

        # 3. Calcul de la cible temporelle (Target RUL)
        dataframe = self._compute_target_rul(dataframe)

        # 4. Nettoyage final des valeurs manquantes (NaNs) sur le périmètre XGBoost
        columns_to_check = self.FEATURE_COLUMNS + ["target_rul"]
        dataframe = dataframe.dropna(subset=columns_to_check).copy()

        if dataframe.empty:
            raise ValueError("Aucune observation valide après le calcul de la RUL et le dropna.")

        # 5. Extraction finale du schéma attendu par XGBoost
        output_columns = [
            *self.CONTEXT_COLUMNS,
            *self.FEATURE_COLUMNS,
            "target_rul"
        ]

        features_df = dataframe[output_columns].copy()

        # Conversion explicite des types pour garantir la compatibilité avec XGBoost et Parquet
        for col in self.FEATURE_COLUMNS:
            features_df[col] = pd.to_numeric(features_df[col], errors="coerce").astype("float32")
        features_df["target_rul"] = features_df["target_rul"].astype("int32")

        logger.success(
            f"RUL Feature Engineering terminé : {len(features_df):,} lignes générées. "
            f"Features actives : {len(self.FEATURE_COLUMNS)} (incluant 'anomaly_score')."
        )
        return features_df
