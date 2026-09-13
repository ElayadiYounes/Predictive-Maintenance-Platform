import requests
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

from jobs.common.logger import logger
from jobs.common.config import settings
from api.schema.alert_schema import MaintenanceAlertResponse


class NotificationService:
    """
    Responsable de l'envoi physique des alertes de maintenance.
    Exploite fastapi-mail de manière asynchrone pour la couche SMTP.
    """

    def __init__(self) -> None:
        #Lecture directe de votre nouveau schéma strict de settings
        self.mail_config = ConnectionConfig(
            MAIL_USERNAME=settings.SMTP_USERNAME,
            MAIL_PASSWORD=settings.SMTP_PASSWORD.get_secret_value(),
            MAIL_FROM=settings.SMTP_FROM,
            MAIL_PORT=settings.SMTP_PORT,
            MAIL_SERVER=settings.SMTP_HOST,
            MAIL_STARTTLS=settings.SMTP_TLS,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=False
        )

        self.team_email = settings.MAINTENANCE_TEAM_EMAIL
        # On garde l'attribut optionnel au cas où on ajoute Slack plus tard
        self.slack_webhook_url = getattr(settings, "SLACK_WEBHOOK_URL", None)
        self.fm = FastMail(self.mail_config)

    async def _send_email_async(self, subject: str, html_body: str) -> bool:
        """ Exploite la puissance asynchrone de fastapi-mail pour envoyer l'e-mail. """
        try:
            message = MessageSchema(
                subject=subject,
                recipients=[self.team_email],
                body=html_body,
                subtype=MessageType.html
            )
            # Envoi non bloquant pour l'API
            await self.fm.send_message(message)
            return True
        except Exception as e:
            logger.error(f"Échec de l'envoi asynchrone de l'e-mail (fastapi-mail) : {str(e)}")
            return False

    def _send_slack_webhook(self, text_message: str) -> bool:
        """ Envoie une alerte instantanée sur le canal Slack de la salle de contrôle. """
        if not self.slack_webhook_url:
            return False
        try:
            payload = {"text": text_message}
            response = requests.post(self.slack_webhook_url, json=payload, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Échec de l'envoi du Webhook Slack : {str(e)}")
            return False

    async def dispatch_alert(self, alert: MaintenanceAlertResponse) -> bool:
        """
        Formate et distribue l'alerte de manière asynchrone sur le bon canal selon sa priorité.
        """
        title = f"[{alert.decision_priority}] Alerte Machine - Équipement {alert.id_equipement}"

        body_text = (
            "⚠️ ALERTE DE MAINTENANCE ⚠️\n"
            f"• Équipement : {alert.id_equipement}\n"
            f"• Installation : {alert.instal}\n"
            f"• Zone : {alert.zone}\n"
            f"• Date d'inspection : {alert.date}\n" 
            f"• Statut IA : {alert.anomaly_status}\n" 
            f"• RUL estimé : {alert.predicted_rul} jour(s)\n" 
            f"• Priorité : {alert.decision_priority}\n" 
            f"• Action prescrite : {alert.prescribed_action}\n" 
            f"• Générée le : {alert.prediction_date.isoformat()}"
        )
        #gesion des couleurs :
        priority_colors = {
            "CRITIQUE": "#d9534f",
            "HAUTE": "#f0ad4e",
            "MOYENNE": "#f7c948",
            "FAIBLE": "#5bc0de",
        }
        priority_color = priority_colors.get(
            alert.decision_priority,
            "#777777",
        )

        body_html = f""" 
              <html> 
                    <body style=" font-family: Arial, sans-serif; color: #333; line-height: 1.5; " > 
                       <h2 style="color: {priority_color};"> {title} </h2> 
                       <table style=" border-collapse: collapse; width: 100%; max-width: 650px; " >
                         <tr> 
                            <td style="padding: 8px; font-weight: bold;"> Équipement </td>
                            <td style="padding: 8px;"> {alert.id_equipement} </td> 
                         </tr> 
                         <tr style="background-color: #f2f2f2;">
                           <td style="padding: 8px; font-weight: bold;"> Installation </td> 
                           <td style="padding: 8px;"> {alert.instal} </td> 
                        </tr> 
                        <tr> 
                           <td style="padding: 8px; font-weight: bold;"> Zone </td>
                           <td style="padding: 8px;"> {alert.zone} </td> 
                       </tr> 
                       <tr style="background-color: #f2f2f2;"> 
                          <td style="padding: 8px; font-weight: bold;"> Date d'inspection </td>
                          <td style="padding: 8px;"> {alert.date} </td> 
                      </tr> 
                      <tr> 
                          <td style="padding: 8px; font-weight: bold;"> Statut IA </td>
                          <td style="padding: 8px;"> {alert.anomaly_status} </td> 
                      </tr> 
                      <tr style="background-color: #f2f2f2;">
                          <td style="padding: 8px; font-weight: bold;"> RUL estimé </td>
                          <td style=" padding: 8px; font-weight: bold; color: {priority_color}; " > {alert.predicted_rul} jour(s) </td>
                      </tr>
                      <tr> 
                          <td style="padding: 8px; font-weight: bold;"> Priorité </td>
                          <td style=" padding: 8px; font-weight: bold; color: {priority_color}; " > {alert.decision_priority} </td>
                      </tr> 
                      <tr style="background-color: #f2f2f2;">
                          <td style="padding: 8px; font-weight: bold;"> Action prescrite </td>
                          <td style=" padding: 8px; font-style: italic; " > {alert.prescribed_action} </td>
                      </tr> 
                      <tr> 
                          <td style="padding: 8px; font-weight: bold;"> ID inspection </td>
                          <td style="padding: 8px;"> {alert.id_inspection} </td> 
                      </tr> 
                      <tr style="background-color: #f2f2f2;">
                          <td style="padding: 8px; font-weight: bold;"> Génération de la prédiction </td>
                          <td style="padding: 8px;"> {alert.prediction_date} </td> 
                      </tr> 
                   </table> 
                   <p style=" margin-top: 20px; font-size: 11px; color: #777; " > Alerte générée automatiquement par la plateforme de maintenance prédictive et prescriptive. </p> 
                </body> 
        </html> 
        """

        logger.info(f"Notification : Routage asynchrone de l'alerte de priorité [{alert.decision_priority}]...")

        # Appel attendu (await) de la fonction d'envoi d'email
        email_success = await self._send_email_async(subject=title, html_body=body_html)

        if alert.decision_priority == "CRITIQUE":
            # Le webhook Slack reste en synchrone/standard (léger)
            self._send_slack_webhook(text_message=f"🚨 *URGENCE CRITIQUE FLOTTE* 🚨\n{body_text}")

        return email_success
