from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def build_dim_user(dataframe: DataFrame) -> DataFrame:
    """
    Construit la dimension utilisateur.
    """

    return (
        dataframe
        .select(
            F.col("utilisateur").alias("nom"),
        )
        .dropDuplicates()
        .withColumn(
            "id_user",
            F.xxhash64(F.col("nom")),
        )
        .select(
            "id_user",
            "nom",
        )
    )