from typing import Tuple
import pandas as pd

from jobs.common.logger import logger


class TemporalTrainTestSplitter :
    """ Effectue une séparation temporelle des données d'inspection pour l'entraînement et le test des modèles Machine Learning.
     La séparation est réalisée indépendamment pour chaque équipement :
      - les inspections les plus anciennes sont utilisées pour le TRAIN ;
      - les inspections les plus récentes sont utilisées pour le TEST.
       Cette stratégie évite d'utiliser des observations futures pendant l'entraînement du modèle.
        Parameters
        ----------
        test_ratio : float Proportion des observations de chaque équipement réservées au jeu de test.
        min_train_samples : int Nombre minimum d'observations nécessaires dans le jeu d'entraînement pour conserver un équipement dans le split.
         min_test_samples : int Nombre minimum d'observations nécessaires dans le jeu de test pour conserver un équipement dans le split.
    """

    def __init__(self, test_ratio: float = 0.20, min_train_samples: int = 5, min_test_samples: int = 1, ) -> None:
        if not 0 < test_ratio < 1:
            raise ValueError("test_ratio doit être compris entre 0 et 1.")
        if min_train_samples < 1:
            raise ValueError("min_train_samples doit être supérieur ou égal à 1.")
        if min_test_samples < 1:
            raise ValueError("min_test_samples doit être supérieur ou égal à 1.")

        self.test_ratio = test_ratio
        self.min_train_samples = min_train_samples
        self.min_test_samples = min_test_samples



    @staticmethod
    def _validate_input(dataframe: pd.DataFrame, ) -> None:
        """ Vérifie que les colonnes nécessaires sont présentes. """
        if dataframe is None:
            raise ValueError("Le DataFrame reçu par TemporalTrainTestSplitter est None.")
        if dataframe.empty:
            raise ValueError("Le DataFrame reçu par TemporalTrainTestSplitter est vide.")
        required_columns = ["id_inspection", "id_equipement", "date", ]
        missing_columns = [
            column
            for column in required_columns
            if column not in dataframe.columns
        ]
        if missing_columns:
            raise ValueError(f"Colonnes obligatoires absentes du DataFrame : {missing_columns}")
        if dataframe["date"].isna().any():
            raise ValueError(
                "La colonne 'date' contient des valeurs NULL/NaN."
                 "Impossible d'effectuer une séparation temporelle fiable."
            )
        if dataframe["id_equipement"].isna().any():
            raise ValueError("La colonne 'id_equipement' contient des valeurs NULL/NaN.")


    @staticmethod
    def _validate_temporal_order(train_dataframe: pd.DataFrame, test_dataframe: pd.DataFrame, ) -> None:
        """ Vérifie qu'aucune observation TEST n'est antérieure à la dernière observation TRAIN du même équipement. """
        train_last_dates = (train_dataframe.groupby("id_equipement")["date"].max())
        test_first_dates = (test_dataframe.groupby("id_equipement")["date"].min())
        common_equipments = train_last_dates.index.intersection(test_first_dates.index)
        invalid_equipments = common_equipments[
            test_first_dates.loc[common_equipments] < train_last_dates.loc[common_equipments]
        ]
        if not invalid_equipments.empty:
            raise ValueError("Violation de l'ordre temporel détectée pour " f"les équipements : {invalid_equipments.tolist()}")



    def split(self, dataframe: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """ Sépare les inspections en TRAIN et TEST selon leur date, indépendamment pour chaque équipement.
         Returns
         -------
         Tuple[pd.DataFrame, pd.DataFrame] train_dataframe, test_dataframe
         """
        self._validate_input(dataframe)

        dataframe = dataframe.copy()
        dataframe["date"] = pd.to_datetime(dataframe["date"], errors="raise", )

        train_parts = []
        test_parts = []
        logger.info("Début de la séparation temporelle " "TRAIN / TEST.")

        for id_equipement, equipment_dataframe in dataframe.groupby("id_equipement", sort=False, ):
            equipment_dataframe = equipment_dataframe.sort_values(
                by=["date", "id_inspection"],
                ascending=[True, True],
            ).reset_index(drop=True)

            total_samples = len(equipment_dataframe)
            test_samples = max(int(total_samples * self.test_ratio), self.min_test_samples, )
            train_samples = total_samples - test_samples

            if train_samples < self.min_train_samples:
                logger.warning(
                f"Équipement {id_equipement} ignoré du split : "
                f"{total_samples} observations disponibles, " 
                f"{train_samples} TRAIN et {test_samples} TEST."
                )
                continue

            train_equipment = equipment_dataframe.iloc[:train_samples].copy()
            test_equipment = equipment_dataframe.iloc[train_samples:].copy()

            train_parts.append(train_equipment)
            test_parts.append(test_equipment)

            logger.info(
                f"Équipement {id_equipement} : " 
                f"{total_samples} observations → " 
                f"{len(train_equipment)} TRAIN / " 
                f"{len(test_equipment)} TEST | " 
                f"TRAIN jusqu'au " 
                f"{train_equipment['date'].max().date()} | " 
                f"TEST à partir du " 
                f"{test_equipment['date'].min().date()}"
            )

        if not train_parts or not test_parts:
            raise ValueError(
                "Impossible de construire les jeux TRAIN et TEST. " 
                "Vérifiez le nombre d'observations par équipement."
            )

        train_dataframe = pd.concat(train_parts, ignore_index=True, )
        test_dataframe = pd.concat(test_parts, ignore_index=True, )

        train_dataframe = train_dataframe.sort_values(
            by=["date", "id_equipement", "id_inspection"]
        ).reset_index(drop=True)

        test_dataframe = test_dataframe.sort_values(
            by=["date", "id_equipement", "id_inspection"]
        ).reset_index(drop=True)

        self._validate_temporal_order(train_dataframe, test_dataframe, )

        logger.success(
            "Séparation temporelle terminée : " 
            f"{len(train_dataframe):,} TRAIN / " 
            f"{len(test_dataframe):,} TEST."
        )

        return train_dataframe, test_dataframe







