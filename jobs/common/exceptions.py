class MaintenancePlatformException(Exception):
    """Exception de base pour l'ensemble de la plateforme universitaire.

    Toutes nos erreurs personnalisées héritent de celle-ci.
    """

    def __init__(self, message: str, details: str = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Détails: {self.details})"
        return self.message

# ==========================================
# 1. INFRASTRUCTURE & DATA LAKE EXCEPTIONS
# ==========================================
class DataLakeConfigurationError(MaintenancePlatformException):
    """Levée lorsque les variables d'accès à MinIO sont incorrectes."""
    pass


class DataLakeConnectionError(MaintenancePlatformException):
    """Levée lorsque MinIO est hors-ligne ou inaccessible par le réseau."""
    pass


class DataLakeBucketNotFoundError(MaintenancePlatformException):
    """Levée lorsqu'un bucket requis (ex: raw, curated) n'existe pas."""
    pass


