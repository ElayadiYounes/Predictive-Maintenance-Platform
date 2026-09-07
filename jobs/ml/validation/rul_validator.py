import pandas as pd
from jobs.common.logger import logger


class RULResultsValidator:
    """
    Valide les prédictions RUL générées par XGBoost en calculant
    les écarts réels et en catégorisant la qualité des fenêtres de maintenance.

    Logique de classification des statuts RUL
    -----------------------------------------
    - exact_prediction     : L'erreur est de 0 ou ±1 jour.
    - early_prediction     : Le modèle prédit l'alerte trop tôt (sécuritaire).
    - dangerous_late_prediction : Le modèle prédit l'alerte trop tard (risque de casse).
    """

    REQUIRED_COLUMNS = [
        "id_inspection",
        "id_equipement",
        "target_rul",  # Compte à rebours réel (cible)
    ]

    MODEL_COLUMNS = [
        "predicted_rul",  # Prédiction générée par XGBoost
        "model_type"
    ]

    def __init__(self, safe_error_window_days: int = 1) -> None:
        """
        Initialise le validateur de résultats RUL.

        Parameters
        ----------
        safe_error_window_days : int
            Nombre de jours d'écart tolérés pour considérer une prédiction
            comme "exacte" (par défaut ±1 jour).
        """
        self.safe_error_window_days = safe_error_window_days

    def _validate_input(self, dataframe: pd.DataFrame) -> None:
        """ Vérifie que le DataFrame contient les colonnes nécessaires. """
        if dataframe is None:
            raise ValueError("Le DataFrame de résultats RUL est None.")
        if dataframe.empty:
            raise ValueError("Le DataFrame de résultats RUL est Vide.")

        required_columns = self.REQUIRED_COLUMNS + self.MODEL_COLUMNS

        missing_columns = [
            column for column in required_columns if column not in dataframe.columns
        ]
        if missing_columns:
            raise ValueError(f"Colonnes nécessaires à la validation RUL absentes : {missing_columns}")

    @staticmethod
    def _compute_rul_error_metrics(dataframe: pd.DataFrame) -> pd.DataFrame:
        """ Calcule l'écart mathématique absolu et brut entre le réel et le prédit. """
        dataframe = dataframe.copy()

        # Erreur brute : Réel - Prédit
        # (Si positif : le modèle sous-estime, si négatif : le modèle sur-estime)
        dataframe["rul_error_raw"] = dataframe["target_rul"] - dataframe["predicted_rul"]
        dataframe["rul_error_absolute"] = dataframe["rul_error_raw"].abs()

        return dataframe

    def _build_rul_prediction_status(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """ Catégorise chaque prédiction selon sa dangerosité ou sa précision pour la maintenance. """
        dataframe = dataframe.copy()
        dataframe["rul_status"] = "exact_prediction"

        # 1er cas : Prédiction en avance (Le modèle voit la panne arriver plus tôt qu'en réalité)
        # Signifie que raw_error < 0 (car predicted_rul > target_rul)
        dataframe.loc[
            (dataframe["rul_error_raw"] < -self.safe_error_window_days),
            "rul_status"
        ] = "early_prediction"

        # 2ème cas : Prédiction en retard CRITIQUE (Le modèle voit la panne arriver après sa vraie date)
        # Signifie que raw_error > 0 (car predicted_rul < target_rul) -> La machine franchit le seuil avant
        dataframe.loc[
            (dataframe["rul_error_raw"] > self.safe_error_window_days),
            "rul_status"
        ] = "dangerous_late_prediction"

        return dataframe

    def validate(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Analyse, segmente et affiche les statistiques d'évaluation du modèle XGBoost RUL.
        """
        logger.info("=" * 70)
        logger.info("XGBOOST RUL PREDICTIONS VALIDATION START")
        logger.info("=" * 70)

        self._validate_input(dataframe)
        logger.info(f"Dataset reçu : {len(dataframe):,} lignes.")

        # Étape 1 : Calcul des erreurs physiques
        dataframe = self._compute_rul_error_metrics(dataframe)

        # Étape 2 : Classification métier des prédictions
        dataframe = self._build_rul_prediction_status(dataframe)

        # Étape 3 : Calcul des indicateurs statistiques pour les logs de production
        total_inspections = len(dataframe)
        mean_absolute_error = dataframe["rul_error_absolute"].mean()

        exact_count = int((dataframe["rul_status"] == "exact_prediction").sum())
        early_count = int((dataframe["rul_status"] == "early_prediction").sum())
        late_count = int((dataframe["rul_status"] == "dangerous_late_prediction").sum())

        # Affichage des KPIs dans la console
        logger.info(f"Erreur Absolue Moyenne Globale (MAE) : {mean_absolute_error:.2f} jours.")

        logger.info(
            f"Prédictions Exactes (à ±{self.safe_error_window_days}j près) : {exact_count} ({exact_count / total_inspections:.2%})")
        logger.info(
            f"Prédictions en Avance (Planification anticipée) : {early_count} ({early_count / total_inspections:.2%})")
        logger.warning(
            f"Prédictions en Retard CRITIQUES (Risque d'arrêt) : {late_count} ({late_count / total_inspections:.2%})")

        logger.success("Validation et analyse des résultats RUL Terminée.")
        logger.info("=" * 70)

        return dataframe
