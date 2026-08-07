import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import pandas as pd
from io import BytesIO
from datetime import datetime, UTC


from jobs.common.config import settings
from jobs.common.logger import logger
from jobs.common.exceptions import DataLakeConnectionError, DataLakeBucketNotFoundError, NoPartitionFoundError



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

########################### retourner le chemin de derniere partition #############################################

    def get_latest_partition(self, bucket_name: str, prefix: str) -> str:
        """
        Retourne le chemin de la partition
        la plus récente d'un préfixe.

        Exemple
        -------
        inspection/
            2026/
                07/
                    26/
                    27/
                    28/

        Retourne
        --------
        inspection/2026/07/28
        """

        logger.info(
            f"Recherche de la dernière partition "
            f"'{prefix}' dans le bucket '{bucket_name}'."
        )

        try:

            # Vérification connexion
            self.check_connection()

            # Vérification bucket
            self.s3_client.head_bucket(
                Bucket=bucket_name,
            )

            partitions: dict[datetime, str] = {}

            paginator = self.s3_client.get_paginator(
                "list_objects_v2"
            )

            pages = paginator.paginate(
                Bucket=bucket_name,
                Prefix=f"{prefix}/",
            )

            for page in pages:

                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:

                    object_key = obj["Key"]

                    # Exemple :
                    # inspection/2026/07/28/vibration.parquet

                    parts = object_key.split("/")

                    if len(parts) < 5:
                        continue

                    try:

                        year = int(parts[1])
                        month = int(parts[2])
                        day = int(parts[3])

                        partition_date = datetime(
                            year,
                            month,
                            day,
                        )

                        partition_path = (
                            f"{parts[0]}/"
                            f"{parts[1]}/"
                            f"{parts[2]}/"
                            f"{parts[3]}"
                        )

                        partitions[partition_date] = partition_path

                    except ValueError:
                        # Ignore les chemins
                        # qui ne respectent pas
                        # YYYY/MM/DD
                        continue

            if not partitions:
                logger.error(
                    f"Aucune partition trouvée "
                    f"pour '{prefix}'."
                )

                raise NoPartitionFoundError(
                    f"Aucune partition trouvée "
                    f"pour '{prefix}'."
                )

            latest_date = max(
                partitions.keys()
            )

            latest_partition = partitions[
                latest_date
            ]

            logger.success(
                f"Dernière partition détectée : "
                f"{latest_partition}"
            )

            return latest_partition

        except ClientError as e:

            error_code = (
                e.response
                .get("Error", {})
                .get("Code")
            )

            if error_code in (
                    "404",
                    "NoSuchBucket",
            ):
                logger.exception(
                    f"Bucket introuvable : "
                    f"{bucket_name}"
                )

                raise DataLakeBucketNotFoundError(
                    f"Bucket '{bucket_name}' introuvable.",
                    str(e),
                )

            logger.exception(
                "Erreur MinIO."
            )

            raise DataLakeConnectionError(
                "Erreur lors de la récupération "
                "de la dernière partition.",
                str(e),
            )

        except Exception:

            logger.exception(
                "Erreur inattendue lors de la "
                "recherche de la dernière partition."
            )

            raise