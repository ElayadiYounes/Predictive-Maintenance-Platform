import pandas as pd
import xgboost as xgb
from jobs.common.logger import logger


class InspectionXGBoostRUL:
    """
    Modèle de régression XGBoost pour la prédiction de la RUL (Remaining Useful Life)
    sur les inspections des équipements.

    Stratégie globale :
      - Un modèle unique global entraîné sur l'historique complet de dégradation.
      - Apprentissage des signatures de vieillissement universelles à la flotte.
      - Prédiction d'un compte à rebours lissé et écrêté (target_rul).
    """

    DEFAULT_N_ESTIMATORS = 100
    DEFAULT_MAX_DEPTH = 5
    DEFAULT_LEARNING_RATE = 0.1
    DEFAULT_RANDOM_STATE = 42

    def __init__(self, n_estimators: int = DEFAULT_N_ESTIMATORS,
                 max_depth: int = DEFAULT_MAX_DEPTH,
                 learning_rate: float = DEFAULT_LEARNING_RATE,
                 random_state: int = DEFAULT_RANDOM_STATE) -> None:
        """
        Initialise les paramètres du régresseur XGBoost RUL.

        Parameters
        ----------
        n_estimators : int
            Nombre d'arbres de décision (boosted trees).
        max_depth : int
            Profondeur maximale de chaque arbre de décision.
        learning_rate : float
            Pas d'apprentissage (taux de shrinkage).
        random_state : int
            Graine aléatoire assurant la reproductibilité des entraînements.
        """
        if n_estimators <= 0:
            raise ValueError("n_estimators doit être strictement positif.")
        if max_depth <= 0:
            raise ValueError("max_depth doit être strictement positif.")
        if not 0 < learning_rate <= 1.0:
            raise ValueError("learning_rate doit être compris entre 0 et 1.0.")

        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.random_state = random_state

        self.global_model: xgb.XGBRegressor = None
        self.feature_columns: list[str] = []

    # =========================================================
    # Validation
    # =========================================================
    @staticmethod
    def _validate_training_data(dataframe: pd.DataFrame, feature_columns: list[str]) -> None:
        """ Vérifie que les données nécessaires à la régression RUL sont exploitables. """
        if dataframe is None:
            raise ValueError("Le DataFrame d'entraînement RUL est None.")
        if dataframe.empty:
            raise ValueError("Le DataFrame d'entraînement RUL est vide.")
        if not feature_columns:
            raise ValueError("Aucune feature n'a été fournie pour XGBoost.")

        missing_feature_columns = [
            col for col in feature_columns if col not in dataframe.columns
        ]
        if missing_feature_columns:
            raise ValueError(f"Features absentes du DataFrame : {missing_feature_columns}")

        if "target_rul" not in dataframe.columns:
            raise ValueError("La colonne cible 'target_rul' est obligatoire pour la régression XGBoost.")

    # =========================================================
    # Création de l'instance
    # =========================================================
    def _create_model(self) -> xgb.XGBRegressor:
        """ Crée une nouvelle instance de XGBRegressor configurée. """
        return xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=self.random_state,
            objective="reg:squarederror",  # Objectif : Minimisation de l'erreur quadratique moyenne (MSE)
            n_jobs=-1  # Utilisation de tous les threads CPU disponibles
        )

    # =========================================================
    # Modèle global de Régression
    # =========================================================
    def train(self, dataframe: pd.DataFrame, feature_columns: list[str]) -> xgb.XGBRegressor:
        """
        Entraîne le modèle global XGBoost sur la cible RUL.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Dataset complet après calcul du Feature Engineering de RUL.
        feature_columns : list[str]
            Variables d'entrées (physiques + anomaly_score).

        Returns
        -------
        xgb.XGBRegressor
            Le modèle de régression global entraîné.
        """
        self._validate_training_data(dataframe, feature_columns)

        logger.info("Entraînement du modèle XGBoost RUL global...")

        # Préparation des matrices
        x_train = dataframe[feature_columns].copy()
        y_train = dataframe["target_rul"]

        model = self._create_model()
        model.fit(x_train, y_train)

        self.global_model = model
        self.feature_columns = feature_columns

        logger.success(
            "Modèle global XGBoost RUL entraîné avec succès : "
            f"{len(x_train):,} observations, "
            f"{len(feature_columns)} features actives."
        )
        return model

    # =========================================================
    # Inférence / Prédiction de la RUL
    # =========================================================
    def predict(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Prédit la durée de vie utile restante (RUL) en jours pour chaque inspection.

        Returns
        -------
        pd.DataFrame
            DataFrame d'origine enrichi avec les colonnes :
            - 'predicted_rul' (int32) : Le nombre de jours restants arrondi et sécurisé.
            - 'model_type' (str) : 'xgboost_global' pour le traçage.
        """
        if self.global_model is None:
            raise RuntimeError("Le modèle global XGBoost RUL n'est pas entraîné.")
        if dataframe is None or dataframe.empty:
            raise ValueError("Le DataFrame de prédiction RUL est vide.")

        missing_columns = [col for col in self.feature_columns if col not in dataframe.columns]
        if missing_columns:
            raise ValueError(f"Features absentes du DataFrame de prédiction RUL : {missing_columns}")

        logger.info(f"Génération des prédictions RUL sur {len(dataframe):,} inspections...")

        result = dataframe.copy()
        x_pred = result[self.feature_columns]

        # Calcul des prédictions continues (float)
        raw_predictions = self.global_model.predict(x_pred)

        # Post-traitements métiers essentiels :
        # 1. Empêcher les valeurs négatives absurde (clip à 0 jour minimum)
        # 2. Arrondir à l'entier le plus proche (jours complets d'exploitation)
        result["predicted_rul"] = raw_predictions
        result["predicted_rul"] = result["predicted_rul"].clip(lower=0).round().astype("int32")
        result["model_type"] = "xgboost"

        logger.success(
            "Inférence RUL terminée. Plage des prédictions : "
            f"[{result['predicted_rul'].min()}j - {result['predicted_rul'].max()}j]."
        )
        return result
