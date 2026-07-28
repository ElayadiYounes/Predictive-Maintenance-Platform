import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import pandas as pd
from io import BytesIO
from datetime import datetime, UTC


from jobs.common.config import settings
from jobs.common.logger import logger
from jobs.common.exceptions import DataLakeConnectionError, DataLakeBucketNotFoundError



class MinioStorageClient:
    """
      Client centralisé permettant d'interagir avec le Data Lake MinIO.
    """

    def __init__(self) -> None:
        """Initialise le client S3 en utilisant les configurations centralisées."""
        try:
            # Configuration technique obligatoire pour MinIO (Path-Style Access)
            s3_config = Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"}
            )

            # Instanciation de la client boto3 globale
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=settings.MINIO_ENDPOINT,
                aws_access_key_id=settings.MINIO_ROOT_USER,
                aws_secret_access_key=settings.MINIO_ROOT_PASSWORD.get_secret_value(),
                config=s3_config,
                region_name="us-east-1"  # Région par défaut requise par boto3
            )
            logger.debug("Client MinIO S3 initialisé avec succès.")
        except Exception:
            logger.exception("Impossible d'initialiser le client MinIO.")
            raise

#################### Vérifie la connexion #####################
    def check_connection(self) -> None:
        """Vérifie si le Data Lake est en ligne et accessible."""
        try:
            self.s3_client.list_buckets()
        except ClientError as e:
            logger.exception("Connexion au Data Lake MinIO impossible.")
            raise DataLakeConnectionError(
                "Connexion à MinIO impossible",
                str(e)
            )

################## charger dataFrame #########################
    def upload_dataframe(self, dataframe: pd.DataFrame, bucket_name: str, file_name: str, prefix : str) -> None:
        """
        Convertit un DataFrame Pandas en Parquet puis
        l'envoie directement dans MinIO.

        Parameters
        ----------
        dataframe : pd.DataFrame
            DataFrame à sauvegarder.

        bucket_name : str
            Bucket cible.

        file_name : str
            le nom de fichier
            Exemple :
            maintenance.parquet
        prefix : str
            generalement le nom de table cible
        """
        now = datetime.now(UTC)
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")

        logger.info(f"Upload du DataFrame {file_name} vers {bucket_name}")

        try:
            # Vérification connexion
            self.check_connection()

            # Vérification bucket
            self.s3_client.head_bucket(Bucket=bucket_name)

            object_path = (
                f"{prefix}/"
                f"{year}/{month}/{day}/"
                f"{file_name}"
            )

            if dataframe.empty:
                logger.warning("Le DataFrame est vide.")
                return

            # Conversion mémoire et stockage vers minIo
            with BytesIO() as buffer:

                dataframe.to_parquet(
                    buffer,
                    engine="pyarrow",
                    index=False,
                )

                buffer.seek(0)

                self.s3_client.upload_fileobj(
                    Fileobj=buffer,
                    Bucket=bucket_name,
                    Key=object_path,
                )

            logger.success(f"DataFrame envoyé avec succès : {bucket_name}/{object_path}")

        except ClientError as e:

            error_code = (
                e.response
                .get("Error", {})
                .get("Code")
            )

            if error_code in ("404", "NoSuchBucket"):
                logger.exception(f"Bucket introuvable : {bucket_name}")

                raise DataLakeBucketNotFoundError(
                    f"Bucket '{bucket_name}' introuvable.",
                    str(e),
                )

            logger.exception("Erreur MinIO.")

            raise DataLakeConnectionError(
                "Erreur lors de l'upload vers MinIO.",
                str(e),
            )

        except Exception:
            logger.exception("Erreur inattendue lors de l'upload.")
            raise