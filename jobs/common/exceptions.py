class MaintenancePlatformException(Exception):
    """Exception de base pour l'ensemble de la plateforme .

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

# ==========================================
# 2. INGESTION & SOURCING EXCEPTIONS
# ==========================================

class SourceDBConnectionError(MaintenancePlatformException):
    """Levée lorsque la base de données source est inaccessible."""
    pass


class SourceDBQueryError(MaintenancePlatformException):
    """Levée lorsqu'une requête SQL échoue."""
    pass


class SourceTableNotFoundError(MaintenancePlatformException):
    """Levée lorsqu'une table source n'existe pas."""
    pass


class SourceDataExtractionError(MaintenancePlatformException):
    """Levée lorsqu'une extraction de données échoue."""
    pass


class DataLakeReadError(MaintenancePlatformException):
    """levée lorsque Spark n'est pas capable de lire couche bronze"""
    pass


class DataLakeWriteError(MaintenancePlatformException):
    """levée lorsque Spark n'est pas capable de écrire couche silver"""
    pass



class MissingRequiredColumnError(MaintenancePlatformException):
    """Une ou plusieurs colonnes obligatoires sont absentes. """
    pass

class InvalidSchemaError(MaintenancePlatformException):
    """
    Le schéma Spark ne correspond
    pas au schéma attendu.
    """
    pass
