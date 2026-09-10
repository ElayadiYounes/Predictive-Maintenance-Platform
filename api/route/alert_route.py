from fastapi import APIRouter, HTTPException, status
from typing import list

from jobs.common.logger import logger
from api.schema.alert_schema import MaintenanceAlertResponse
from api.service.alert_service import AlertService
from api.notifications.alert_notification import NotificationService

# Instanciation du routeur FastAPI pour isoler les routes de l'application
router = APIRouter(
    prefix="/api/v1/alerts",
    tags=["Maintenance Alerts"]
)


@router.post("/process-notifications", response_model=dict, status_code=status.HTTP_200_OK)
async def process_and_send_new_alerts():
    """
    Endpoint de production : Détecte les alertes en attente (alert_sent = 0),
    déclenche leur routage asynchrone par E-mail/Slack, et met à jour le Data Lake Gold.

    Returns
    -------
    dict
        Bilan chiffré des notifications traitées et archivées.
    """
    logger.info("📡 API HTTP : Requête de traitement des nouvelles notifications reçue.")

    # Instanciation de vos couches de services et de communication
    alert_service = AlertService()
    notification_service = NotificationService()

    # 1. Extraction du delta des alertes non traitées
    unnotified_alerts: list[MaintenanceAlertResponse] = alert_service.get_unnotified_alerts()

    if not unnotified_alerts:
        logger.info("API HTTP : Aucun delta détecté. Toutes les alertes ont déjà été envoyées.")
        return {
            "status": "success",
            "message": "Aucune nouvelle alerte à envoyer. La flotte est à jour.",
            "processed_count": 0
        }

    logger.info(f"API HTTP : {len(unnotified_alerts)} alerte(s) prêtes pour la distribution.")

    ids_inspections_traitees = []
    success_count = 0

    # 2. Boucle asynchrone d'envoi des fiches d'interventions
    for alert in unnotified_alerts:
        # L'envoi est asynchrone grâce à fastapi-mail (await)
        dispatch_success = await notification_service.dispatch_alert(alert)

        if dispatch_success:
            success_count += 1
            # On stocke l'ID uniquement si le mail est parti pour mettre à jour MinIO de manière sécurisée
            ids_inspections_traitees.append(alert.id_inspection)
        else:
            logger.error(f"📡 API HTTP : Échec d'envoi pour l'inspection {alert.id_inspection}. Archivage ignoré.")

    # 3. Archivage incrémental dans le fichier Parquet fixe sur MinIO Gold
    if ids_inspections_traitees:
        try:
            alert_service.mark_alerts_as_sent(id_inspections_processed=ids_inspections_traitees)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur critique lors de la mise à jour des statuts dans le Data Lake : {str(e)}"
            )

    logger.success(f"API HTTP : Cycle terminé. {success_count}/{len(unnotified_alerts)} notification(s) envoyée(s).")

    return {
        "status": "success",
        "message": "Cycle de notifications exécuté et archivé avec succès.",
        "detected_alerts_count": len(unnotified_alerts),
        "successfully_sent_count": success_count
    }
