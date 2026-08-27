from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def build_dim_equipement(dataframe_inspection: DataFrame, dataframe_limite: DataFrame) -> DataFrame:
    """
    Construit la dimension équipement enrichie avec les seuils de danger réels.

    Parameters
    ----------
    dataframe_inspection : DataFrame
        Le DataFrame des inspections (Silver).
    dataframe_limite : DataFrame
        Le DataFrame des limites/seuils (Silver).
    """

    # 1. Extraction et dédoublonnage des équipements depuis les inspections
    df_base_equipement = (
        dataframe_inspection
        .select(
            "zone",
            "instal",
        )
        .dropDuplicates(["zone", "instal"])
        .withColumn(
            "id_equipement",
            F.xxhash64(F.col("zone"), F.col("instal")),
        )
    )

    # 2. Nettoyage de la table limite (Sécurité anti-doublons sur la clé 'instal')
    df_limite_unique = (
        dataframe_limite
        .select(
            "instal",
            F.col("t_av_limite").cast("double").alias("seuil_danger_temp"),
            F.col("v_ax_limite").cast("double").alias("seuil_danger_vib_axiale"),
            F.col("v_h_limite").cast("double").alias("seuil_danger_vib_horiz"),
            F.col("v_v_limite").cast("double").alias("seuil_danger_vib_vert")
        )
        .dropDuplicates(["instal"])
    )

    # 3. Jointure pour attacher les seuils à l'équipement via la clé 'instal'
    return (
        df_base_equipement
        .join(
            df_limite_unique,
            on="instal",
            how="left"  # Left join pour ne pas perdre une machine si son seuil n'est pas encore défini
        )
        .select(
            "id_equipement",
            "zone",
            "instal",
            "seuil_danger_temp",
            "seuil_danger_vib_axiale",
            "seuil_danger_vib_horiz",
            "seuil_danger_vib_vert"
        )
    )
