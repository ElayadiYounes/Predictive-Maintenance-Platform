import pandas as pd
from jobs.common.logger import logger


class InspectionAnomalyValidator:
    """ Valide les anomalies détectées par Isolation Forest à partir des seuils métier propres à chaque équipement.
    Logique :
    Isolation Forest
       |
       | anomaly_flag
       v
    Validation seuils
       |
       v
    validated_anomaly
    Une anomalie est considérée comme validée lorsque :
    anomaly_flag == 1 ET au moins une mesure dépasse son seuil métier.
    """

    REQUIRED_COLUMNS = [
        # Les identifiants
        "id_inspection",
        "id_equipement",

        # Température (avant)
        "t_av",

        # Vibration
        "av_ax", "av_h", "av_v",
        "ar_ax", "ar_h", "ar_v",

        # Caractéristiques techniques binaires
        "p_produit",
        "huile_graisse",
        "ailette", "boulonneries",
        "cable",
        "plaque_a_borne",
        "graisseur",

        # Seuils métier
        "seuil_danger_temp",
        "seuil_danger_vib_axiale",
        "seuil_danger_vib_horiz",
        "seuil_danger_vib_vert",

        # Ratios pré-calculés par rapport aux seuils
        "ratio_temp",
        "ratio_vib_axiale",
        "ratio_vib_horiz",
        "ratio_vib_vert",
    ]
    MODEL_COLUMNS = [
        "anomaly_score",
        "anomaly_flag",
        "model_type",
    ]

    def __init__(self)->None:
        """Initialise le validateur métier."""
        pass

    

