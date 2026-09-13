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
        # ZONE ROUGE : URGENCE CRITIQUE 🚨 #
        # Une alerte métier forte est présente et le RUL est inférieur # ou égal à 2 jours.
        # ==================================================================
        if rul <= 2 and status in ("validated_anomaly", "threshold_alert_only"):
            return {
                "decision_priority": "CRITIQUE",
                "prescribed_action": "Intervention urgente requise sous 48h. Vérifier immédiatement l'état de l'organe concerné et préparer son remplacement ou sa réparation."
            }

        # ==================================================================
        # ZONE ORANGE : PRIORITÉ HAUTE ⚠️ #
        # 1. Anomalie prédictive ML seule mais RUL <= 2 jours :
        # intervention immédiate, sans prescrire automatiquement
        # un arrêt d'urgence sur le seul signal ML. #
        # 2. Alerte métier ou anomalie validée avec RUL entre 3 et 7 jours. #
        # 3. Anomalie validée avec RUL > 7 jours :
        # anomalie suffisamment forte pour rester prioritaire.
        # ==================================================================
        elif rul <= 2 and status == "ml_anomaly_only" :
            return {
                "decision_priority": "HAUTE",
                "prescribed_action": "RUL très court détecté par l'IA. Réaliser une inspection technique immédiate et préparer une intervention de maintenance."
            }

        elif 3 <= rul <= 7 and status in ("validated_anomaly", "threshold_alert_only") :
            return {
                "decision_priority": "HAUTE",
                "prescribed_action": "Planifier une intervention de maintenance préventive sous 5 jours : vérification de l'alignement, de l'état mécanique et du graissage."
            }

        elif rul > 7 and status == "validated_anomaly" :
            return {
                "decision_priority": "HAUTE",
                "prescribed_action": "Anomalie validée détectée. Planifier une intervention de maintenance préventive et effectuer une vérification mécanique approfondie."
            }

        # ==================================================================
        # ZONE JAUNE : PRIORITÉ MOYENNE ⏳
        # Anomalie détectée uniquement par l'IA avec un horizon supérieur  à 2 jours.
        # ==================================================================
        elif status == "ml_anomaly_only" and rul > 2:
            return {
                "decision_priority": "MOYENNE",
                "prescribed_action": "Dérive suspecte détectée par l'IA. Programmer une inspection visuelle et technique lors de la prochaine ronde de maintenance."
            }

        # ==================================================================
        # ZONE BLEUE : PRIORITÉ FAIBLE 🔍
        # Pic de seuil isolé avec un horizon supérieur à 7 jours.
        # ==================================================================
        elif status == "threshold_alert_only" and rul > 7:
            return {
                "decision_priority": "FAIBLE",
                "prescribed_action": "Alerte de seuil isolée sans dérive globale confirmée. Placer l'équipement sous surveillance renforcée et vérifier l'évolution des paramètres."
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