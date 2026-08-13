from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def build_dim_equipement(dataframe: DataFrame) -> DataFrame:
    """
    Construit la dimension équipement.
    """

    return (
        dataframe
        .select(
            "zone",
            "instal",
        )
        .dropDuplicates()
        .withColumn(
            "id_equipement",
            F.xxhash64(
                F.col("zone"),
                F.col("instal"),
            ),
        )
        .select(
            "id_equipement",
            "zone",
            "instal",
        )
    )