import pandas as pd
from io import BytesIO

from jobs.common.logger import logger
from jobs.common.config import settings
from jobs.common.minio_client import MinioStorageClient

from api.schema.alert_schema import MaintenanceAlertResponse


class AlertService:
    """
    Logique métier de l'API : Extraction du Delta d'alertes non envoyées
    et mise à jour du statut d'archivage dans le Data Lake Gold.
    """

    OBJECT_PATH = "inspection/fact_inspection_rul/fact_inspection_rul.parquet"

    def __init__(self) -> None:
        self.minio_client = MinioStorageClient()

    def get_unnotified_alerts(self) -> list[MaintenanceAlertResponse]:
        """
        Lit la table Gold de manière native et extrait les alertes prioritaires
        qui n'ont pas encore fait l'objet d'une notification (alert_sent == 0).
        """
        logger.info("Service API : Extraction des alertes non notifiées...")

        try:
            #  Utilisation de votre fonction native download_dataframe
            df_rul = self.minio_client.download_dataframe(
                bucket_name=settings.GOLD_BUCKET,
                object_path=self.OBJECT_PATH
            )

            if df_rul.empty:
                return []

            # Application du filtre d'alerte : Priorités urgentes et non envoyées
            df_alerts = df_rul[
                (df_rul["decision_priority"].isin(["CRITIQUE", "HAUTE", "MOYENNE", "FAIBLE"])) &
                (df_rul["alert_sent"] == 0)
                ].copy()

            logger.info(f"Service API : {len(df_alerts)} nouvelle(s) alerte(s) détectée(s).")

            #  Utilisation de votre schéma Pydantic pour valider et typer la sortie
            # 'from_validate' ou l'initialisation Pydantic v2 convertit proprement le dictionnaire Pandas
            return [
                MaintenanceAlertResponse.model_validate(row)
                for row in df_alerts.to_dict(orient="records")
            ]

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des alertes : {str(e)}")
            return []

    def mark_alerts_as_sent(self, id_inspections_processed: list[int]) -> None:
        """
        Passe le drapeau 'alert_sent' de 0 à 1 pour les inspections traitées,
        puis réécrit le Parquet consolidé à l'aide des fonctions natives du client.
        """
        if not id_inspections_processed:
            return

        logger.info(f"Service API : Archivage de {len(id_inspections_processed)} alerte(s) (alert_sent 0 -> 1)...")

        try:
            #  Téléchargement natif de l'historique complet
            df_history = self.minio_client.download_dataframe(
                bucket_name=settings.GOLD_BUCKET,
                object_path=self.OBJECT_PATH
            )

            # Mise à jour de la colonne pour les IDs spécifiés
            df_history.loc[df_history["id_inspection"].isin(id_inspections_processed), "alert_sent"] = 1

            # Forçage des types pour la cohérence Spark SQL
            df_history["id_inspection"] = df_history["id_inspection"].astype("int32")
            df_history["id_equipement"] = df_history["id_equipement"].astype("int64")
            df_history["predicted_rul"] = df_history["predicted_rul"].astype("int32")
            df_history["target_rul"] = df_history["target_rul"].astype("int32")
            df_history["alert_sent"] = df_history["alert_sent"].astype("int32")
            df_history["date"] = df_history["date"].astype(str)

            with BytesIO() as buffer_write:
                df_history.to_parquet(buffer_write, engine="pyarrow", index=False)
                buffer_write.seek(0)

                self.minio_client.s3_client.upload_fileobj(
                    Fileobj=buffer_write,
                    Bucket=settings.GOLD_BUCKET,
                    Key=self.OBJECT_PATH  # "inspection/fact_inspection_rul/fact_inspection_rul.parquet"
                )
            logger.success("Service API : Archivage incrémental validé dans le Data Lake Gold.")

        except Exception as e:
            logger.error(f"Échec critique lors de la mise à jour des statuts alert_sent : {str(e)}")
            raise
