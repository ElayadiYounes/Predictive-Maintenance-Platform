import os
from io import BytesIO
from datetime import datetime, timezone

import pandas as pd
import joblib

from jobs.common.logger import logger
from jobs.common.config import settings
from jobs.common.minio_client import MinioStorageClient

class AnomalyWriter:
    """ Writer indépendant de la couche ML. Responsabilités :
     1. Sauvegarder les résultats de détection d'anomalies dans le bucket Gold.
     2. Sauvegarder les modèles entraînés dans le bucket Models.
     """

    REQUIRED_COLUMNS = [
        "id_inspection",
        "id_equipement",

        "anomaly_score",
        "anomaly_flag",
        "model_type",
    ]

    OPTIONAL_COLUMNS = [
        "alert_temperature",
        "alert_vib_axiale",
        "alert_vib_horiz",
        "alert_vib_vert",
        "threshold_alert",
        "validated_anomaly",
        "anomaly_status",
    ]


    ANOMALY_TABLE_PATH = (
       "inspection/fact_inspection_anomaly"
    )

    def __init__(self) -> None:
        """Initialise le client MinIO."""
        self.minio_client = MinioStorageClient()

    # Validation des résultats d'anomalies

    def _validate_anomaly_results(self,dataframe : pd.DataFrame) -> None:
        """ Vérifie le DataFrame contenant les résultats de détection d'anomalies. """
        if dataframe is None :
            raise ValueError("le dataframe des Anomalies est None")
        if dataframe.empty:
            raise ValueError("le dataframe des Anomalies est vide")

        missing_columns = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in dataframe.columns
        ]
        if missing_columns:
            raise ValueError(f"Colonnes obligatoires absentes du DataFrame des anomalies : {missing_columns}")




    # Préparation des résultats d'anomalies
    def _prepare_anomaly_results(self,dataframe : pd.DataFrame) -> pd.DataFrame:
        """ Prépare le DataFrame final de fact_inspection_anomaly.
         La table contient uniquement les résultats ML et les informations nécessaires à leur interprétation.
        """
        result = dataframe.copy()

        if "model_name" not in result.columns:
            result["model_name"] = "isolation_forest"

        if "model_version" not in result.columns:
            result["model_version"] = "v1"

        if "prediction_date" not in result.columns:
            result["prediction_date"] = datetime.now(timezone.utc)

        output_columns = list(self.REQUIRED_COLUMNS) + ["model_version", "prediction_date"]

        for column in self.OPTIONAL_COLUMNS:
            if column in result.columns:
                output_columns.append(column)

        return result[output_columns].copy()

    # Écriture fact_inspection_anomaly
    def write_anomaly_results(self, dataframe : pd.DataFrame) -> None:
        """ Sauvegarde les résultats Isolation Forest dans Gold.
         Emplacement : s3a://gold/inspection/fact_inspection_anomaly Contrairement à Bronze et Silver
        """
        logger.info("=" * 70)
        logger.info("ML ANOMALY RESULTS WRITING START")
        logger.info("=" * 70)

        # Validation
        self._validate_anomaly_results(dataframe)

        #preparation
        result = self._prepare_anomaly_results(dataframe)

        #vérification
        if result["id_inspection"].isna().any():
            raise ValueError("Certains id_inspection sont invalides.")
        if result["id_equipement"].isna().any():
            raise ValueError("Certains id_equipement sont invalides.")

        # Chemin Gold
        object_key = (
            f"{self.ANOMALY_TABLE_PATH}/"
            "fact_inspection_anomaly.parquet"
        )

        logger.info(f"Ecriture des résultats ML vers : {settings.GOLD_BUCKET}/{object_key}")

        with BytesIO() as buffer:
            result.to_parquet(buffer, engine="pyarrow", index=False, )
            buffer.seek(0)
            self.minio_client.s3_client.upload_fileobj(
                Fileobj=buffer,
                Bucket=settings.GOLD_BUCKET,
                Key=object_key,
            )
        logger.success("fact_inspection_anomaly écrite avec succès.")
        logger.info(f"Lignes écrites : {len(result):,}")
        logger.info(f"Emplacement : " f"s3://{settings.GOLD_BUCKET}/{object_key}")

        logger.info("=" * 70)
        logger.success("ML ANOMALY RESULTS WRITING TERMINÉ.")
        logger.info("=" * 70)


    def write_anomaly_model(self, model, model_name : str = "isolation_forest",
                             model_version : str = "v1", model_type : str = "global",
                             id_equipement : int | None = None) -> None:
        """ Sauvegarde un modèle ML dans le bucket Models.
         Parameters
         ----------
         model : Modèle entraîné compatible avec joblib.
         model_name : str Type du modèle.
         model_version : str Version du modèle.
         model_type : str Portée du modèle : global equipment
         id_equipement: int | None Identifiant équipement pour un modèle dédié à un équipement.
         Examples
         --------
         Modèle global :
          models/
           └── isolation_forest/
                  └── v1/
                       └── global/
                             └── model.joblib
        Modèle équipement :
        models/
          └── isolation_forest/
                 └── v1/
                   └── equipment/
                          └── 123/
                               └── model.joblib
        """
        logger.info("=" * 70)
        logger.info("ML MODEL WRITING START")
        logger.info("=" * 70)

        if model is None:
            raise ValueError("Le modèle à sauvegarder est None.")
        if not model_name:
            raise ValueError("model_name ne peut pas être vide.")
        if not model_version:
            raise ValueError("model_version ne peut pas être vide.")
        if model_type not in {"global", "equipment", }:
            raise ValueError("model_scope doit être 'global' " "ou 'equipment'.")
        if model_type == "equipment" and id_equipement is None:
            raise ValueError("equipment_id est obligatoire pour " "un modèle dédié à un équipement.")

        #construction du chemin
        if model_type == "global" :
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

        logger.info(f"Sauvgarde du modèle vers : {settings.MODELS_BUCKET}/{object_key}")

        #sérialisation du modèle
        with BytesIO() as model_bytes:
            joblib.dump(model, model_bytes)
            model_bytes.seek(0)

            self.minio_client.s3_client.upload_fileobj(
                Fileobj=model_bytes,
                Bucket=settings.MODELS_BUCKET,
                Key=object_key,
            )
        logger.success("Modèle ML sauvegardé avec succès.")
        logger.info(f"Emplacement : " f"s3://{settings.MODELS_BUCKET}/{object_key}")
        logger.info("=" * 70)
        logger.success("ML MODEL WRITING TERMINÉ.")
        logger.info("=" * 70)
















