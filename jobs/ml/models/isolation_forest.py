import pandas as pd
from sklearn.ensemble import IsolationForest
from jobs.common.logger import logger


class InspectionIsolationForest:

    """ Modèles Isolation Forest pour la détection d'anomalies sur les inspections des équipements.
     Stratégie hybride :
      - un modèle global entraîné sur l'ensemble des équipements ;
      - un modèle dédié pour les équipements disposant d'un nombre suffisant d'inspections ;
      - utilisation du modèle global comme fallback lorsque le modèle dédié n'est pas suffisamment fiable.
    """
    DEFAULT_N_ESTIMATORS = 200
    DEFAULT_CONTAMINATION = "auto"
    DEFAULT_RANDOM_STATE = 42
    DEFAULT_MIN_SAMPLES_DEDICATED = 30

    def __init__(self, n_estimators: int = DEFAULT_N_ESTIMATORS,
                 contamination : str | float =DEFAULT_CONTAMINATION,
                 random_state : int = DEFAULT_RANDOM_STATE,
                 min_samples_dedicated : int = DEFAULT_MIN_SAMPLES_DEDICATED
                 )->None:
        """ Initialise les paramètres des modèles Isolation Forest.
        Parameters
        ----------
        n_estimators : int Nombre d'arbres dans chaque Isolation Forest.
        contamination : str | float Proportion attendue d'anomalies. Peut être "auto" ou une valeur comprise entre 0 et 0.5.
        random_state : int Graine permettant de reproduire les résultats.
        min_samples_dedicated : int Nombre minimal d'inspections nécessaires pour entraîner un modèle dédié à un équipement.
        """

        if n_estimators <= 0:
            raise ValueError("n_estimators doit être strictement positif.")

        if isinstance(contamination, float):
            if not 0 < contamination <= 0.5:
                raise ValueError("contamination doit être comprise entre 0 et 0.5.")

        if min_samples_dedicated < 2:
            raise ValueError("min_samples_dedicated doit être supérieur ou égal à 2.")

        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self.min_samples_dedicated = min_samples_dedicated

        self.global_model: IsolationForest = None
        self.dedicated_models: dict[int, IsolationForest] = {}
        self.feature_columns: list[str] = []

    # =========================================================
    # Validation
    # =========================================================
    @staticmethod
    def _validate_training_data(dataframe : pd.DataFrame, feature_columns : list[str]) -> None:
        """ Vérifie que les données nécessaires à l'entraînement sont présentes et exploitables. """
        if dataframe is None:
            raise ValueError("Le DataFrame d'entraînement est None.")

        if dataframe.empty:
            raise ValueError("Le DataFrame d'entraînement est vide.")

        if not feature_columns:
            raise ValueError("Aucune feature n'a été fournie.")

        missing_feature_columns = [
            column
            for column in dataframe.columns
            if column not in feature_columns
        ]
        if missing_feature_columns:
            raise ValueError("Features absentes du DataFrame : " f"{missing_feature_columns}")

        if "id_equipement" not in dataframe.columns:
            raise ValueError("La colonne critique 'id_equipement' est obligatoire.")

    # =========================================================
    # Création d'un modèle
    # =========================================================

    def _create_modele(self) -> IsolationForest:
        """ Crée une nouvelle instance Isolation Forest. """
        return IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=-1,
        )

    # =========================================================
    # Modèle global
    # =========================================================
    def train_global(self, dataframe : pd.DataFrame, feature_columns : list[str]) -> IsolationForest:
        """ Entraîne le modèle global sur l'ensemble des inspections.
        Parameters
        ----------
        dataframe : pd.DataFrame Dataset contenant toutes les inspections.
        feature_columns : list[str] Variables utilisées par Isolation Forest.
        Returns
        -------
        IsolationForest Modèle global entraîné.
        """
        self._validate_training_data(dataframe, feature_columns)

        logger.info("Entraînement du modèle Isolation Forest global...")

        training_data = dataframe[feature_columns].copy()

        training_data = training_data.dropna()

        if training_data.empty:
            raise ValueError("Aucune donnée valide pour entraîner le modèle global.")

        model = self._create_modele()
        model.fit(training_data)
        self.global_model = model
        self.feature_columns = feature_columns

        logger.success(
            "Modèle global Isolation Forest entraîné : "
             f"{len(training_data):,} observations, " 
             f"{len(feature_columns)} features."
        )
        return model

    # =========================================================
    # Modèles dédiés
    # =========================================================

    def train_dedicated_models(self,dataframe : pd.DataFrame) -> dict[int, IsolationForest]:
        """ Entraîne un modèle Isolation Forest spécifique pour chaque équipement disposant d'un nombre suffisant d'inspections.
        Les équipements avec trop peu d'observations sont ignorés et utiliseront le modèle global.
        Returns
        -------
        dict[int, IsolationForest] Dictionnaire : id_equipement -> modèle dédié.
        """
        if self.global_model is None:
            raise RuntimeError("Le modèle global doit être entraîné avant " "les modèles dédiés.")

        if "id_equipement" not in dataframe.columns:
            raise ValueError("La colonne 'id_equipement' est obligatoire.")

        logger.info("Entraînement des modèles dédiés par équipement...")

        self.dedicated_models = {}
        grouped = dataframe.groupby("id_equipement")

        for id_equipment, equipment_data in grouped:
            valid_data = (
                equipment_data[self.feature_columns]
                .dropna()
            )
            sample_count = len(valid_data)

            if sample_count < self.min_samples_dedicated:
                logger.info(
                     f"Équipement {id_equipment} : "
                     f"{sample_count} observations. " "Modèle dédié non entraîné → fallback global."
                )
                continue

            model = self._create_modele()
            model.fit(valid_data)
            self.dedicated_models[id_equipment] = model

            logger.success(
                f"Modèle dédié entraîné pour équipement " 
                f"{id_equipment} : " f"{sample_count} observations."
            )

        logger.info(f"Nombre de modèles dédiés entraînés : {len(self.dedicated_models)}")

        return self.dedicated_models


    def predict(self,dataframe : pd.DataFrame) -> pd.DataFrame:
        """ Détecte les anomalies avec la stratégie hybride.
        Pour chaque inspection :
         modèle dédié disponible
         ↓
         OUI → modèle dédié
         ↓
         NON → modèle global
         Returns
         -------
         pd.DataFrame DataFrame contenant : - id_inspection - id_equipement - anomaly_score - anomaly_flag - model_type
         """

        if self.global_model is None:
            raise RuntimeError("Le modèle global n'est pas entraîné.")

        if dataframe is None or dataframe.empty:
            raise ValueError("Le DataFrame de prédiction est vide.")

        missing_columns = [
            column
            for column in self.feature_columns
            if column not in dataframe.columns
        ]

        if missing_columns:
            raise ValueError(f"Features absentes du DataFrame : {missing_columns}")

        if "id_equipement" not in dataframe.columns:
            raise ValueError("La colonne 'id_equipement' est obligatoire.")

        logger.info(f"Détection d'anomalies sur {len(dataframe):,} inspections...")

        results = dataframe[
            [column for column in ["id_inspection", "id_equipement", ]
             if column in dataframe.columns
            ]
        ].copy()

        results["anomaly_score"] = None
        results["anomaly_flag"] = None
        results["model_type"] = None

        for equipment_id, indexes in dataframe.groupby("id_equipement").groups.items():

            equipment_data = dataframe.loc[indexes, self.feature_columns,].copy()

            valid_mask = ~equipment_data.isna().any(axis=1)

            valid_data = equipment_data.loc[valid_mask]

            if valid_data.empty:
                continue

            if equipment_id in self.dedicated_models:
                model = self.dedicated_models[equipment_id]
                model_type = "dedicated"

            else:
                model = self.global_model
                model_type = "global"

            # decision_function :
            # score élevé → observation normale
            # score faible → observation atypique

            raw_scores = model.decision_function(valid_data)

            # On inverse le score afin que :
            # score élevé = anomalie importante

            anomaly_scores = -raw_scores
            predictions = model.predict(valid_data)

            # Isolation Forest :
            # 1 = normal
            # -1 = anomalie

            anomaly_flags = (predictions == -1).astype(int)
            results.loc[valid_data.index, "anomaly_score",] = anomaly_scores
            results.loc[valid_data.index, "anomaly_flag",] = anomaly_flags
            results.loc[valid_data.index, "model_type",] = model_type

        results["anomaly_score"] = pd.to_numeric(results["anomaly_score"], errors="coerce", )
        results["anomaly_flag"] = pd.to_numeric(results["anomaly_flag"], errors="coerce", ).astype("Int64")

        logger.success("Détection d'anomalies terminée.")

        return results

        
