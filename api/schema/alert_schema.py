from pydantic import BaseModel, Field
from datetime import datetime



class MaintenanceAlertResponse(BaseModel):
    """
    Structure de validation de sortie pour une alerte de maintenance.
    Aligne les types de données de l'API avec le schéma de la table Gold.
    """
    id_inspection: int = Field(..., description="Identifiant unique de l'inspection")
    id_equipement: int = Field(..., description="Identifiant unique de l'équipement")
    date: str = Field(..., description="Vraie date physique de l'inspection (YYYY-MM-DD)")
    predicted_rul: int = Field(..., description="Nombre de jours restants calculé par XGBoost")
    anomaly_status: str = Field(..., description="Statut de dérive calculé par l'Isolation Forest")
    decision_priority: str = Field(..., description="Niveau d'urgence prioritaire prescrit")
    prescribed_action: str = Field(..., description="Consigne d'intervention textuelle pour le technicien")
    alert_sent: int = Field(..., description="Drapeau d'envoi de l'alerte (0 ou 1)")
    prediction_date: datetime = Field(..., description="Timestamp de génération de la prédiction")

    class Config:
        from_attributes = True  # Permet à Pydantic de lire directement un dictionnaire ou un objet Pandas
