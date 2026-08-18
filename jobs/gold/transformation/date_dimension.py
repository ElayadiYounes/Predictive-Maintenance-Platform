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
            "inspection_year",
            "inspection_month",
            "inspection_day",
        )
        .dropDuplicates(["date"])
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
            "inspection_year",
            "inspection_month",
            "inspection_day",
            "month_name",
        )
    )