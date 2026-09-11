import os
from io import BytesIO
from datetime import datetime, timezone

import pandas as pd
import joblib

from jobs.common.logger import logger
from jobs.common.config import settings
from jobs.common.minio_client import MinioStorageClient


class RULWriter:
    """
    Writer indépendant de la couche ML RUL. Responsabilités :
    1. Sauvegarder les résultats de prédiction de la RUL dans le bucket Gold.
    2. Sauvegarder les modèles de régression entraînés dans le bucket Models.
    """

    REQUIRED_COLUMNS = [
        "id_inspection",
        "id_equipement",
        "target_rul",
        "predicted_rul",
        "model_type",
    ]

    OPTIONAL_COLUMNS = [
        "date",
        "threshold_alert",
        "rul_error_raw",
        "rul_error_absolute",
        "rul_status",
        "decision_priority",
        "prescribed_action"
    ]

    RUL_TABLE_PATH = "inspection/fact_inspection_rul"

    def __init__(self) -> None:
        """Initialise le client MinIO."""
        self.minio_client = MinioStorageClient()

    # =========================================================
    # Validation et Préparation des résultats
    # =========================================================

    def _validate_rul_results(self, dataframe: pd.DataFrame) -> None:
        """Vérifie le DataFrame contenant les résultats de prédiction RUL."""
        if dataframe is None:
            raise ValueError("Le DataFrame des résultats RUL est None.")
        if dataframe.empty:
            raise ValueError("Le DataFrame des résultats RUL est vide.")

        missing_columns = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in dataframe.columns
        ]
        if missing_columns:
            raise ValueError(f"Colonnes obligatoires absentes du DataFrame RUL : {missing_columns}")

    def _prepare_rul_results(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Prépare le DataFrame final destiné à la table fact_inspection_rul."""
        result = dataframe.copy()

        if "model_version" not in result.columns:
            result["model_version"] = "v1"

        if "prediction_date" not in result.columns:
            result["prediction_date"] = datetime.now(timezone.utc)

        # LOGIQUE DE SÉCURITÉ ANTI-SPAM HISTORIQUE
        if "alert_sent" not in result.columns:
            result["alert_sent"] = 1
            result["alert_sent"] = result["alert_sent"].astype("Int32")
        else:
            result["alert_sent"] = result["alert_sent"].fillna(0).astype("int32")

        # Construction de la liste des colonnes de sortie
        output_columns = list(self.REQUIRED_COLUMNS) + ["model_version", "prediction_date","alert_sent"]

        for column in self.OPTIONAL_COLUMNS:
            if column in result.columns:
                output_columns.append(column)

        return result[output_columns].copy()

    # =========================================================
    # Écriture de la Table Gold fact_inspection_rul
    # =========================================================

    def write_rul_results(self, dataframe: pd.DataFrame) -> None:
        """Sauvegarde les prédictions RUL de XGBoost dans le bucket Gold."""
        logger.info("=" * 70)
        logger.info("ML RUL RESULTS WRITING START")
        logger.info("=" * 70)

        # Validation et préparation
        self._validate_rul_results(dataframe)
        result = self._prepare_rul_results(dataframe)

        # Vérification des clés primaires
        if result["id_inspection"].isna().any():
            raise ValueError("Certains id_inspection sont invalides (NaN).")
        if result["id_equipement"].isna().any():
            raise ValueError("Certains id_equipement sont invalides (NaN).")

        if "date" in result.columns:
            # .dt.strftime("%Y-%m-%d") convertit le datetime en texte propre
            result["date"] = pd.to_datetime(result["date"]).dt.strftime("%Y-%m-%d").astype(str)
        # Forçage des types entiers pour la compatibilité Parquet / Spark SQL
        result["id_inspection"] = result["id_inspection"].astype("int32")
        result["predicted_rul"] = result["predicted_rul"].astype("int32")
        result["target_rul"] = result["target_rul"].astype("int32")

        # Clé d'objet S3 de destination
        object_key = f"{self.RUL_TABLE_PATH}/fact_inspection_rul.parquet"

        logger.info(f"Écriture des résultats RUL vers : {settings.GOLD_BUCKET}/{object_key}")

        with BytesIO() as buffer:
            result.to_parquet(buffer, engine="pyarrow", index=False)
            buffer.seek(0)
            self.minio_client.s3_client.upload_fileobj(
                Fileobj=buffer,
                Bucket=settings.GOLD_BUCKET,
                Key=object_key,
            )

        logger.success("fact_inspection_rul écrite avec succès.")
        logger.info(f"Lignes écrites : {len(result):,}")
        logger.info(f"Emplacement : s3://{settings.GOLD_BUCKET}/{object_key}")
        logger.info("=" * 70)
        logger.success("ML RUL RESULTS WRITING TERMINÉ.")
        logger.info("=" * 70)

    # =========================================================
    # Écriture du Modèle .joblib dans Models
    # =========================================================

    def write_rul_model(self, model, model_name: str = "xgboost_rul",
                        model_version: str = "v1", model_type: str = "global",
                        id_equipement: int | None = None) -> None:
        """Sauvegarde le modèle de régression XGBoost RUL dans le bucket Models."""
        logger.info("=" * 70)
        logger.info("ML RUL MODEL WRITING START")
        logger.info("=" * 70)

        if model is None:
            raise ValueError("Le modèle RUL à sauvegarder est None.")
        if not model_name:
            raise ValueError("model_name ne peut pas être vide.")
        if not model_version:
            raise ValueError("model_version ne peut pas être vide.")
        if model_type not in {"global", "equipment"}:
            raise ValueError("model_type doit être 'global' ou 'equipment'.")
        if model_type == "equipment" and id_equipement is None:
            raise ValueError("id_equipement est obligatoire pour un modèle dédié.")

        # Construction dynamique de la clé d'objet S3
        if model_type == "global":
            object_key = (
                f"{model_name}/"
                f"{model_version}/"
                "global/"
                "model.joblib"
            )
        else:
            object_key = (
                f"{model_name}/"
                f"{model_version}/"
                "equipements/"
                f"{id_equipement}/"
                "model.joblib"
            )

        logger.info(f"Sauvegarde du modèle RUL vers : {settings.MODELS_BUCKET}/{object_key}")

        # Sérialisation et téléversement sécurisé
        with BytesIO() as model_bytes:
            joblib.dump(model, model_bytes)
            model_bytes.seek(0)

            self.minio_client.s3_client.upload_fileobj(
                Fileobj=model_bytes,
                Bucket=settings.MODELS_BUCKET,
                Key=object_key,
            )

        logger.success("Modèle ML RUL sauvegardé avec succès.")
        logger.info(f"Emplacement : s3://{settings.MODELS_BUCKET}/{object_key}")
        logger.info("=" * 70)
        logger.success("ML RUL MODEL WRITING TERMINÉ.")
        logger.info("=" * 70)
