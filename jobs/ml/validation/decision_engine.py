import pandas as pd
from jobs.common.logger import logger


class MaintenanceDecisionEngine:
    """
    Moteur de Décision (Prescriptive Analytics) pour la maintenance.

    Croise les statuts d'anomalies de l'Isolation Forest et le compte à rebours
    de RUL de XGBoost pour prescrire des actions correctives claires et des
    niveaux de priorité pour les équipes sur le terrain.
    """

    REQUIRED_COLUMNS = [
        "anomaly_status",
        "predicted_rul"
    ]

    def __init__(self) -> None:
        """ Initialise le moteur de décision réglementaire. """
        pass

    def _validate_input(self, dataframe: pd.DataFrame) -> None:
        """ S'assure que les colonnes calculées par l'IA en amont sont bien présentes. """
        if dataframe is None or dataframe.empty:
            raise ValueError("Le DataFrame transmis au Moteur de Décision est invalide ou vide.")

        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in dataframe.columns]
        if missing_columns:
            raise ValueError(f"Colonnes d'entrées IA manquantes pour prendre une décision : {missing_columns}")


    @staticmethod
    def _apply_rules_row(row: pd.Series) -> dict:
        """
        Applique la matrice de règles métiers complétée sur 100% des cas.
        """
        status = row["anomaly_status"]
        rul = row["predicted_rul"]

        # ==================================================================
        # ZONE ROUGE : URGENCE CRITIQUE 🚨 (Peu importe le statut, si RUL <= 2 jours)
        # ==================================================================
        if rul <= 2 and status in ("validated_anomaly", "threshold_alert_only", "ml_anomaly_only"):
            return {
                "decision_priority": "CRITIQUE",
                "prescribed_action": "Arrêt d'urgence requis sous 48h. Remplacement ou réparation immédiate de l'organe défaillant."
            }

        # ==================================================================
        # ZONE ORANGE : PRIORITÉ HAUTE ⚠️ (Danger à court terme 3-7 jours ou anomalie lourde)
        # ==================================================================
        elif (status == "validated_anomaly" and 3 <= rul <= 7) or (
                status == "threshold_alert_only" and 3 <= rul <= 7) or (status == "validated_anomaly" and rul > 7):
            return {
                "decision_priority": "HAUTE",
                "prescribed_action": "Planifier une intervention de maintenance préventive (vérification alignement, mécanique) sous 5 jours."
            }

        # ==================================================================
        # ZONE JAUNE : PRIORITÉ MOYENNE ⏳ (Signaux IA ou dérives à moyen/long terme)
        # ==================================================================
        elif status == "ml_anomaly_only" and rul >= 3:
            return {
                "decision_priority": "MOYENNE",
                "prescribed_action": "Dérive suspecte détectée par l'IA. Programmer une inspection visuelle lors de la prochaine ronde technique."
            }

        # ==================================================================
        # ZONE BLEUE : PRIORITÉ FAIBLE 🔍 (Alerte de seuil isolée sans dérive stable)
        # ==================================================================
        elif status == "threshold_alert_only" and rul > 7:
            return {
                "decision_priority": "FAIBLE",
                "prescribed_action": "Alerte de seuil isolée sans dérive globale stable. Placer l'équipement sous surveillance vibratoire renforcée."
            }

        # ==================================================================
        # ZONE VERTE : AUCUNE ACTION 🍏 (Situation normale)
        # ==================================================================
        else:
            return {
                "decision_priority": "AUCUNE",
                "prescribed_action": "Aucune action requise. Équipement stable et sain."
            }

    def process_decisions(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Prend un DataFrame contenant les résultats IA et l'enrichit avec
        les prescriptions de maintenance ('decision_priority' et 'prescribed_action').

        Parameters
        ----------
        dataframe : pd.DataFrame
            Dataset enrichi en sortie du RULResultsValidator.

        Returns
        -------
        pd.DataFrame
            Dataset final prêt pour l'écriture Gold.
        """
        logger.info("=" * 70)
        logger.info("MAINTENANCE DECISION ENGINE PROCESS START")
        logger.info("=" * 70)

        self._validate_input(dataframe)

        result = dataframe.copy()

        logger.info("Application de la matrice de règles sur le flux d'inspections...")

        # Application de la logique ligne par ligne
        decisions_series = result.apply(self._apply_rules_row, axis=1)

        # Éclatement du dictionnaire généré en deux colonnes distinctes
        result["decision_priority"] = [d["decision_priority"] for d in decisions_series]
        result["prescribed_action"] = [d["prescribed_action"] for d in decisions_series]

        # Statistiques rapides pour le rapport de production
        stats = result["decision_priority"].value_counts()
        logger.info("Bilan des décisions prescriptives générées :")
        for priority, count in stats.items():
            logger.info(f"  [{priority}] : {count:,} ligne(s)")

        logger.success("Calcul des prescriptions de maintenance terminé avec succès.")
        logger.info("=" * 70)

        return result