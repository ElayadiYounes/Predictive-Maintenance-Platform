from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def build_fact_inspection(dataframe: DataFrame, dim_time: DataFrame, dim_equipement: DataFrame, dim_user: DataFrame) -> DataFrame:
    """
    Construit la table fact_inspection à partir des données Silver
    et des dimensions Gold.

    Les clés étrangères sont récupérées par jointure avec les
    dimensions :
        - id_time
        - id_equipement
        - id_user

    Les mesures d'enrichissement sont déjà calculées dans Silver
    et ne sont donc pas recalculées ici.
    """

    # ---------------------------------------------------------
    # Préparation des dimensions
    # ---------------------------------------------------------

    dim_time_ref = dim_time.select(
        "id_time",
        "date",
    )

    dim_equipement_ref = dim_equipement.select(
        "id_equipement",
        "zone",
        "instal",
    )

    dim_user_ref = dim_user.select(
        "id_user",
        F.col("nom").alias("utilisateur"),
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
    # Sélection du schéma final
    # ---------------------------------------------------------

    fact = fact.select(
        # Identifiants
        F.col("id").alias("id_inspection"),
        F.col("id_time"),
        F.col("id_equipement"),
        F.col("id_user"),

        # Attributs binaires
        F.col("p_produit"),
        F.col("huile_graisse"),
        F.col("ailette"),
        F.col("boulonneries"),
        F.col("cable"),
        F.col("plaque_a_borne"),
        F.col("graisseur"),

        #Température originales
        F.col("t_av"),
        F.col("t_ar"),

        # Température entichies
        F.col("temperature_max"),
        F.col("temperature_mean"),
        F.col("temperature_difference"),

        # Vibrations originales
        F.col("av_ax"),
        F.col("av_h"),
        F.col("av_v"),
        F.col("ar_ax"),
        F.col("ar_h"),
        F.col("ar_v"),

        # Vibrations enrichies
        F.col("vibration_av_max"),
        F.col("vibration_ar_max"),
        F.col("vibration_max"),
        F.col("vibration_av_mean"),
        F.col("vibration_ar_mean"),
        F.col("vibration_mean"),
        F.col("vibration_difference"),

        # Informations métier
        F.col("observation"),
        F.col("action"),
    )

    return fact