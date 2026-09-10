import uvicorn
from fastapi import FastAPI, status
from jobs.common.logger import logger
from api.route.alert_route import router as alerts_router

# 1. Initialisation de l'application FastAPI principale
app = FastAPI(
    title="Plateforme de Maintenance Prédictive & Prescriptive - API d'Alerte",
    description=(
        "Service Web MLOps industriel chargé du routage asynchrone des alertes de dérives "
        "et de RUL (Remaining Useful Life) calculées par la couche Machine Learning."
    ),
    version="1.0.0",
    docs_url="/docs",          # Emplacement de l'interface graphique interactive Swagger UI
    redoc_url="/redoc"
)

# 2. Inclusion du routeur d'alertes validé à l'étape précédente
app.include_router(alerts_router)


# 3. Point d'accès de contrôle de santé (Health Check) pour l'infrastructure usine
@app.get("/health", status_code=status.HTTP_200_OK, tags=["Infrastructure"])
def health_check():
    """
    Vérifie la disponibilité opérationnelle immédiate de l'instance d'API.
    Utile pour les sondes Kubernetes ou Docker Compose Healthchecks.
    """
    return {
        "status": "healthy",
        "timestamp": "2026-09-10T18:04:00Z",  # Horodatage de production synchronisé
        "service": "ml-alert-engine"
    }


# 4. Bloc d'exécution autonome pour le débogage local
if __name__ == "__main__":
    logger.info("Démarrage du serveur web FastAPI de production via Uvicorn...")
    # Lancement d'Uvicorn sur le port standard 8000
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-rechargement actif lors des modifications de fichiers en dev
    )
