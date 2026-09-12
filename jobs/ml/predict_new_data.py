from io import BytesIO
import pandas as pd
import joblib

from jobs.common.logger import logger
from jobs.common.config import settings
from jobs.common.minio_client import MinioStorageClient

# Import de vos composants d'extraction et de transformation
from jobs.ml.readers.gold_reader import read_gold_table
from jobs.ml.features.inspection_features import InspectionFeatureEngineering
from jobs.ml.features.xgboost_features import RULFeatureEngineering

# Import de vos classes algorithmiques validées
from jobs.ml.models.isolation_forest import InspectionIsolationForest
from jobs.ml.models.xgboot_rul import InspectionXGBoostRUL

# Import de vos couches de validation et décision
from jobs.ml.validation.anomaly_validator import InspectionAnomalyValidator
from jobs.ml.validation.rul_validator import RULResultsValidator
from jobs.ml.validation.decision_engine import MaintenanceDecisionEngine

# Import de vos utilitaires de catalogue Hive
from jobs.ml.catalog.ml_catalog import AnomalyCatalog, RULCatalog


class IncrementalInferencePipeline:
    """
    Pipeline d'inférence incrémentale de production.
    Détecte les nouvelles données, enchaîne les modèles de manière native
    via leurs classes d'origine, applique le moteur de décision, et sauvegarde dans MinIO.
    """

    def __init__(self) -> None:
        """ Initialise les clients d'infrastructure et les moteurs de validation. """
        self.minio_client = MinioStorageClient()
        self.anomaly_validator = InspectionAnomalyValidator()
        self.rul_validator = RULResultsValidator()
        self.decision_engine = MaintenanceDecisionEngine()

    @staticmethod
    def detect_new_data() -> pd.DataFrame:
        """
           Détecte uniquement les nouvelles données (inspections absentes
           de la table fact_inspection_anomaly) à traiter.

           Returns
           -------
           pd.DataFrame
               - df_new_inspections :
                   Inspections absentes de fact_inspection_anomaly.
                   Elles doivent passer par l'Isolation Forest.
           """

        logger.info(
            "Étape 1/4 : Analyse de l'historique "
            "pour détecter le Delta (Nouvelles Inspections)..."
        )

        # ==============================================================
        # 1. Lecture de la source
        # ==============================================================

        df_fact = read_gold_table(
            table_name="fact_inspection"
        )

        # Normalisation des IDs
        df_fact["id_inspection"] = (
            df_fact["id_inspection"]
            .astype(int)
        )

        # ==============================================================
        # 2. Lecture de fact_inspection_anomaly
        # ==============================================================

        try:
            df_existing_anomaly = read_gold_table(
                table_name="fact_inspection_anomaly"
            )

            df_existing_anomaly["id_inspection"] = (
                df_existing_anomaly["id_inspection"]
                .astype(int)
            )

            anomaly_ids = set(
                df_existing_anomaly["id_inspection"]
            )

        except Exception:
            logger.warning(
                "Table fact_inspection_anomaly absente. "
                "Toutes les inspections seront considérées "
                "comme nouvelles pour la détection d'anomalies."
            )

            anomaly_ids = set()

        # ==============================================================
        # 3. Nouvelles inspections pour la détection d'anomalies
        # ==============================================================

        df_delta = df_fact[
            ~df_fact["id_inspection"].isin(anomaly_ids)
        ].copy()

        logger.success(f"Parmi {len(df_fact)} lignes de source, on a détecté {len(df_delta)} nouveaux lignes")

        return df_delta

    def execute_inference_chain(self, df_delta: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Étapes 2 & 3 : Applique de manière séquentielle en mémoire vos modèles d'IA
        puis injecte les règles du Moteur de Décision Prescriptif.
        """
        if df_delta.empty:
            return pd.DataFrame(), pd.DataFrame()

        logger.info("Étape 2/4 : Exécution séquentielle de la chaîne d'inférence en mémoire...")

        # ==================================================================
        # A. PIPELINE 1 : Détection d'Anomalies (Isolation Forest)
        # ==================================================================
        fe_anomaly = InspectionFeatureEngineering()
        df_features_anomaly = fe_anomaly.build_feature_engineering(df_delta)
        feature_columns_ml = fe_anomaly.FEATURE_COLUMNS

        # Utilisation de votre classe d'origine
        inspection_if = InspectionIsolationForest()
        inspection_if.feature_columns = feature_columns_ml

        # Chargement du modèle global
        global_if_buffer = BytesIO()
        self.minio_client.s3_client.download_fileobj(
            Bucket=settings.MODELS_BUCKET, Key="isolation_forest/v1/global/model.joblib", Fileobj=global_if_buffer
        )
        global_if_buffer.seek(0)
        inspection_if.global_model = joblib.load(global_if_buffer)

        # Remplissage préventif du dictionnaire des modèles dédiés de votre classe
        for id_eq in df_features_anomaly["id_equipement"].unique():
            id_eq_int = int(id_eq)
            eq_buffer = BytesIO()
            object_key_dedicated = f"isolation_forest/v1/equipements/{id_eq_int}/model.joblib"
            try:
                self.minio_client.s3_client.download_fileobj(
                    Bucket=settings.MODELS_BUCKET, Key=object_key_dedicated, Fileobj=eq_buffer
                )
                eq_buffer.seek(0)
                inspection_if.dedicated_models[id_eq_int] = joblib.load(eq_buffer)
            except Exception:
                pass  # Votre code gère lui-même le fallback si l'ID n'est pas dans le dict

        # Appel NATIF de votre méthode predict() (Inversion de signe et filtres NaNs gérés)
        df_anomaly_results = inspection_if.predict(dataframe=df_features_anomaly)

        # Consolidation : Re-fusion avec les paramètres physiques requis pour la suite
        df_anomaly_consolidated = df_features_anomaly.merge(
            df_anomaly_results[["id_inspection", "id_equipement", "anomaly_score", "anomaly_flag", "model_type"]],
            on=["id_inspection", "id_equipement"],
            how="inner"
        )
        # Validation : Génération automatique de threshold_alert, validated_anomaly, anomaly_status
        df_anomaly_final = self.anomaly_validator.validate(df_anomaly_consolidated)

        # ==================================================================
        # B. PIPELINE 2 : Prédiction de la RUL (XGBoost Regressor)
        # ==================================================================
        logger.info(
            "Étape 3 : Chargement et exécution du modèle XGBoost RUL..."
        )

        inspection_xgb = InspectionXGBoostRUL()

        # --------------------------------------------------------------
        # Chargement du modèle global
        # --------------------------------------------------------------

        rul_buffer = BytesIO()

        self.minio_client.s3_client.download_fileobj(
            Bucket=settings.MODELS_BUCKET,
            Key="xgboost_rul/v1/global/model.joblib",
            Fileobj=rul_buffer,
        )

        rul_buffer.seek(0)

        inspection_xgb.global_model = joblib.load(
            rul_buffer
        )

        feature_columns_xgb = [
            "anomaly_score",
            *feature_columns_ml,
        ]

        inspection_xgb.feature_columns = feature_columns_xgb

        # --------------------------------------------------------------
        # Préparation des données d'inférence
        # Aucun target_rul n'est calculé ici.
        # Aucun RULFeatureEngineering n'est utilisé.
        # --------------------------------------------------------------

        missing_rul_features = [
            column
            for column in feature_columns_xgb
            if column not in df_anomaly_final.columns
        ]

        if missing_rul_features:
            raise ValueError(
                "Features nécessaires à la prédiction XGBoost "
                f"absentes de df_anomaly_final : {missing_rul_features}"
            )

        # Le modèle a uniquement besoin des features X.
        df_features_rul = df_anomaly_final[
            [
                "id_inspection",
                "id_equipement",
                *feature_columns_xgb,
            ]
        ].copy()

        # --------------------------------------------------------------
        # Prédiction
        # --------------------------------------------------------------

        df_rul_predictions = inspection_xgb.predict(
            dataframe=df_features_rul
        )

        logger.success(
            "Prédiction XGBoost RUL terminée : "
            f"{len(df_rul_predictions):,} inspection(s)."
        )


        # ==================================================================
        # C. PIPELINE 3 : Application du Moteur de Décision Prescriptif
        # ==================================================================

        contexte_cols = ["id_inspection", "id_equipement", "anomaly_status", "threshold_alert"]

        contexte_cols_existantes = [c for c in contexte_cols if c in df_anomaly_final.columns]

        df_rul_predictions_with_context = df_rul_predictions.merge(
            df_anomaly_final[contexte_cols_existantes],
            on=["id_inspection", "id_equipement"],
            how="inner"
        )

        df_final_production_rul = self.decision_engine.process_decisions(
            df_rul_predictions_with_context
        )


        return df_anomaly_final, df_final_production_rul



    def save_incremental_results(self, df_anomaly: pd.DataFrame, df_rul: pd.DataFrame, df_delta: pd.DataFrame) -> None:
        """
        Étape 4 : Insère de manière incrémentale (Append Parquet) les DataFrames finaux
        dans le Data Lake Gold et réactive le catalogue Hive.
        """
        if df_anomaly.empty or df_rul.empty:
            logger.info("Aucune nouvelle donnée à enregistrer.")
            return

        logger.info("Étape 4/4 : Enregistrement incrémental (Append) sur MinIO...")

        # 1. Écriture incrémentale Anomalie
        self._append_to_minio_parquet(
            df_new_data=df_anomaly,
            object_key="inspection/fact_inspection_anomaly/fact_inspection_anomaly.parquet",
            writer_type="anomaly"
        )

        if "date" not in df_rul.columns:
            logger.info("Récupération de la colonne 'date' depuis dim_time via df_delta...")

            # 1. On récupère la table de correspondance id_time -> date
            df_time = read_gold_table(table_name="dim_time")

            # 2. On extrait les couples (id_inspection, id_time) depuis le flux source
            df_delta_time = df_delta[["id_inspection", "id_time"]].drop_duplicates()

            # 3. On associe l'id_inspection à sa date réelle
            df_inspection_date = df_delta_time.merge(
                df_time[["id_time", "date"]], on="id_time", how="left"
            )[["id_inspection", "date"]]

            # 4. On injecte la date dans le livrable RUL
            df_rul = df_rul.merge(df_inspection_date, on="id_inspection", how="left")

        # 2. Écriture incrémentale RUL (avec format texte strict sur la date)
        df_rul["date"] = pd.to_datetime(df_rul["date"]).dt.strftime("%Y-%m-%d").astype(str)
        self._append_to_minio_parquet(
            df_new_data=df_rul,
            object_key="inspection/fact_inspection_rul/fact_inspection_rul.parquet",
            writer_type="rul"
        )

        # 3. Synchronisation et rafraîchissement immédiat du Catalogue Hive pour Metabase
        logger.info("Mise à jour immédiate des structures du catalogue Hive...")
        AnomalyCatalog().register_anomaly_table()
        RULCatalog().register_rul_table()

    def _append_to_minio_parquet(self, df_new_data: pd.DataFrame, object_key: str, writer_type: str) -> None:
        """ Télécharge le fichier existant, y concatène le delta, et téléverse le tout. """
        try:
            existing_buffer = BytesIO()
            self.minio_client.s3_client.download_fileobj(
                Bucket=settings.GOLD_BUCKET, Key=object_key, Fileobj=existing_buffer
            )
            existing_buffer.seek(0)
            df_history = pd.read_parquet(existing_buffer)
            #assure que le delta contient des 0 pour qu'on trait ces ligne et envoi les alert
            if writer_type == "rul":
                df_new_data["alert_sent"] = 0

            df_consolidated = pd.concat([df_history, df_new_data], ignore_index=True)
        except Exception:
            logger.warning(f"Fichier historique {object_key} absent. Initialisation de la table.")
            df_consolidated = df_new_data

        # Forçage strict de types d'ID 32-bit/64-bit pour la compatibilité Spark SQL
        df_consolidated["id_inspection"] = df_consolidated["id_inspection"].astype("int32")
        df_consolidated["id_equipement"] = df_consolidated["id_equipement"].astype("int64")

        if "target_rul" not in df_consolidated.columns:
            df_consolidated["target_rul"] = -1

        if "rul_error_raw" not in df_consolidated.columns:
            df_consolidated["rul_error_raw"] = -1

        if "rul_error_absolute" not in df_consolidated.columns:
            df_consolidated["rul_error_absolute"] = -1

        if "predicted_rul" in df_consolidated.columns:
            df_consolidated["predicted_rul"] = df_consolidated["predicted_rul"].astype("int32")

        if "alert_sent" in df_consolidated.columns:
            df_consolidated["alert_sent"] = df_consolidated["alert_sent"].fillna(0).astype("int32")

        df_consolidated["target_rul"] = df_consolidated["target_rul"].fillna(-1).astype("int32")
        df_consolidated["rul_error_raw"] = df_consolidated["rul_error_raw"].fillna(-1).astype("int32")
        df_consolidated["rul_error_absolute"] = df_consolidated["rul_error_absolute"].fillna(-1).astype("int32")

        # Réécriture Parquet propre
        output_buffer = BytesIO()
        df_consolidated.to_parquet(
            output_buffer,
            engine="pyarrow",
            index=False
        )
        output_buffer.seek(0)
        self.minio_client.s3_client.upload_fileobj(
            Fileobj=output_buffer,
            Bucket=settings.GOLD_BUCKET,
            Key=object_key
        )
        logger.success(f"Insertion incrémentale réussie [{writer_type}]. Total lignes consolidées : {len(df_consolidated):,}")


def main():
    """Point d'entrèe principale du runner d'inférence de production"""
    try:
        pipeline = IncrementalInferencePipeline()

        #1-détection du delta
        df_delta = pipeline.detect_new_data()
        if df_delta.empty:
            logger.success("Tout est à jour. Aucun delta à traiter sur ce run.")
            return
        #2 et 3- inférence en chaine native et détection prespective
        df_anomaly_final, df_rul_final = pipeline.execute_inference_chain(df_delta)

        #sauvegarder et catalogage hive sql
        pipeline.save_incremental_results(df_anomaly_final, df_rul_final,df_delta)
        logger.success("PIPELINE D'INFERENCE INCRÉMENTALE DE PRODUCTION TERMINÉ AVEC SUCCÈS !")
    except Exception:
        logger.exception("Échec critique lors de l'exécution de l'inférence incrémentale de production.")
        raise

if __name__ == "__main__":
    main()
