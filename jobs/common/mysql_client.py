from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd


from jobs.common.config import settings
from jobs.common.logger import logger
from jobs.common.exceptions import SourceDBConnectionError, SourceDBQueryError

class MySQLClient:

    """
    Client centralisé permettant d'interagir avec la base MySQL source.
    """
    def __init__(self) -> None:

        """
        Initialise le moteur SQLAlchemy.
        """
        try:
            self.engine: Engine = create_engine(
                settings.MYSQL_URL,
                pool_pre_ping=True,
                pool_recycle=3600,
                future=True,
            )
            logger.info("Client MySQL initialisé avec succès.")


        except Exception as e:
            logger.exception("Impossible d'initialiser le client MySQL.")
            raise SourceDBConnectionError(
                "Impossible d'initialiser le client MySQL.",
                str(e)
            ) from e



    def check_connection(self) -> None:
        """
        Vérifie que la base MySQL est accessible.
        """
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Connexion à la base MySQL vérifiée avec succès.")

        except SQLAlchemyError as e:
            logger.exception("Connexion à la base MySQL impossible.")

            raise SourceDBConnectionError(
                "Impossible de se connecter à la base MySQL.",
                str(e)
            ) from e

    def read_table(self, table_name: str) -> pd.DataFrame:
        """
        Lit l'intégralité d'une table MySQL
        et retourne un DataFrame Pandas.
        """
        #vérification si table_name est un vrai nom de table sinon peut etre attaque de type SQL injection (amélioration de sécurité)
        if not table_name.isidentifier():
            raise ValueError(f"Nom de table invalide : '{table_name}'.")

        try:

            query = f"SELECT * FROM `{table_name}`"

            dataframe = pd.read_sql(
                sql=query,
                con=self.engine
            )

            logger.info(f"Table '{table_name}' chargée ({len(dataframe)} lignes).")
            return dataframe

        except SQLAlchemyError as e:
            logger.exception(f"Impossible de lire la table '{table_name}'.")
            raise SourceDBQueryError(
                f"Lecture impossible de la table '{table_name}'.",
                str(e)
            ) from e

    def close(self) -> None:
        self.engine.dispose()
        logger.info("Connexion MySQL fermée.")