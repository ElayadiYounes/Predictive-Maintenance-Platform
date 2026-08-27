from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

def build_fact_inspection(dataframe: DataFrame, dim_time: DataFrame, dim_equipement: DataFrame, dim_user: DataFrame) -> DataFrame:
    """
    Construit la table fact_inspection à partir des données Silver
    et des dimensions Gold. Inclut le Feature Engineering pour le ML (Ratios & RUL).
    """

    # ---------------------------------------------------------
    # Préparation des dimensions (Enrichie avec les seuils)
    # ---------------------------------------------------------
    dim_time_ref = dim_time.select("id_time", "date")

    # On récupère ici les seuils intégrés à l'étape précédente
    dim_equipement_ref = dim_equipement.select(
        "id_equipement",
        "zone",
        "instal",
        "seuil_danger_temp",
        "seuil_danger_vib_axiale",
        "seuil_danger_vib_horiz",
        "seuil_danger_vib_vert"
    )

    dim_user_ref = dim_user.select(
        "id_user",
        F.col("nom").alias("utilisateur")
    )

    # ---------------------------------------------------------
    # Jointure avec dim_time
    # ---------------------------------------------------------

    fact = dataframe.join(
        dim_time_ref,
        on="date",
        how="left",
    )

    # ---------------------------------------------------------
    # Jointure avec dim_equipement
    # ---------------------------------------------------------

    fact = fact.join(
        dim_equipement_ref,
        on=["zone", "instal"],
        how="left",
    )

    # ---------------------------------------------------------
    # Jointure avec dim_user
    # ---------------------------------------------------------

    fact = fact.join(
        dim_user_ref,
        on="utilisateur",
        how="left",
    )

    # ---------------------------------------------------------
    # FEATURE ENGINEERING 1 : Ratios de Danger (Isolation Forest)
    # ---------------------------------------------------------
    # On compare la valeur mesurée la plus haute (ex: av_ax ou ar_ax) au seuil de la machine
    fact = fact.withColumn(
        "ratio_temp",
        F.greatest(F.col("t_av"), F.col("t_ar")) / F.col("seuil_danger_temp")
    ).withColumn(
        "ratio_vib_axiale",
        F.greatest(F.col("av_ax"), F.col("ar_ax")) / F.col("seuil_danger_vib_axiale")
    ).withColumn(
        "ratio_vib_horiz",
        F.greatest(F.col("av_h"), F.col("ar_h")) / F.col("seuil_danger_vib_horiz")
    ).withColumn(
        "ratio_vib_vert",
        F.greatest(F.col("av_v"), F.col("ar_v")) / F.col("seuil_danger_vib_vert")
    )

    # ---------------------------------------------------------
    # FEATURE ENGINEERING 2 : Calcul de la cible target_rul (XGBoost)
    # ---------------------------------------------------------
    # Étape A : On définit un état de panne (ex: si une mesure dépasse son seuil de danger)
    # Si vous avez un vrai drapeau 'panne' dans vos données d'origine, remplacez cette condition par votre colonne.
    is_broken_cond = (
            (F.col("ratio_temp") >= 1.0) |
            (F.col("ratio_vib_axiale") >= 1.0) |
            (F.col("ratio_vib_horiz") >= 1.0) |
            (F.col("ratio_vib_vert") >= 1.0)
    )
    fact = fact.withColumn("date_panne", F.when(is_broken_cond, F.col("date")).otherwise(None))

    # Étape B : Fenêtre glissante pour trouver la date de la PROCHAINE panne pour CET équipement
    # On regarde du point actuel jusqu'à la fin des temps (unboundedFollowing)
    window_future = (
        Window.partitionBy("id_equipement")
        .orderBy("date")
        .rowsBetween(Window.currentRow, Window.unboundedFollowing)
    )

    # ---------------------------------------------------------
    # Sélection du schéma final
    # ---------------------------------------------------------
    return fact.select(
        # Identifiants
        F.col("id").alias("id_inspection"),
        F.col("id_time"),
        F.col("id_equipement"),
        F.col("id_user"),

        # Attributs binaires
        "p_produit", "huile_graisse", "ailette", "boulonneries", "cable", "plaque_a_borne", "graisseur",

        # Températures et Vibrations originales
        "t_av", "t_ar", "av_ax", "av_h", "av_v", "ar_ax", "ar_h", "ar_v",

        # Températures et Vibrations enrichies dans Silver
        "temperature_max", "temperature_mean", "temperature_difference",
        "vibration_av_max", "vibration_ar_max", "vibration_max",
        "vibration_av_mean", "vibration_ar_mean", "vibration_mean", "vibration_side_difference",

        # --- NOUVELLES COLONNES POUR LE MACHINE LEARNING ---
        "ratio_temp",
        "ratio_vib_axiale",
        "ratio_vib_horiz",
        "ratio_vib_vert",
        "target_rul",

        # Informations métier
        "observation", "action"
    )