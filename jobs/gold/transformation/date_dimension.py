from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def build_dim_time(dataframe: DataFrame) -> DataFrame:
    """
    Construit la dimension temporelle à partir des colonnes
    déjà enrichies dans Silver.
    """

    return (
        dataframe
        .select(
            "date",
            "year",
            "month",
            "day",
        )
        .dropDuplicates()
        .withColumn(
            "id_time",
            F.date_format(
                F.col("date"),
                "yyyyMMdd",
            ).cast("int"),
        )
        .withColumn(
            "month_name",
            F.date_format("date", "MMMM"),
        )
        .select(
            "id_time",
            "date",
            "year",
            "month",
            "day",
            "month_name",
        )
    )