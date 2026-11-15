"""Batch quality rules used by the cleaning notebook; requires PySpark."""
from pyspark.sql import functions as F


def reject_conflicts(frame, keys, values):
    variants = frame.groupBy(*keys).agg(
        F.countDistinct(F.struct(*values)).alias("variants"))
    if variants.filter(F.col("variants") > 1).limit(1).count():
        raise ValueError("Conflicting duplicates need an accepted winner rule")


def prepare_signups(raw):
    checked = (raw.withColumn("email", F.regexp_replace("email", r"^\s+|\s+$", ""))
               .withColumn("parsed_date", F.expr("try_cast(signup_date AS DATE)")))
    valid = checked.filter(F.col("email").isNotNull() & (F.length("email") > 0)
                           & F.col("parsed_date").isNotNull())
    reject_conflicts(valid, ["email"], ["parsed_date", "country"])
    clean = valid.select("email", F.col("parsed_date").alias("signup_date"),
                         "country").dropDuplicates(["email"])
    return valid, clean


def prepare_orders(raw):
    checked = (raw.withColumn("customer_id", F.regexp_replace("customer_id", r"^\s+|\s+$", ""))
               .withColumn("order_id", F.regexp_replace("order_id", r"^\s+|\s+$", ""))
               .withColumn("order_date", F.expr("try_cast(order_date AS DATE)"))
               .withColumn("order_total", F.expr("try_cast(order_total AS DOUBLE)"))
               .withColumn("churned", F.expr("try_cast(churned AS INT)")))
    invalid = checked.filter(
        F.col("customer_id").isNull() | (F.length("customer_id") == 0)
        | F.col("order_id").isNull() | (F.length("order_id") == 0)
        | F.col("order_date").isNull() | F.col("order_total").isNull()
        | F.isnan("order_total") | F.col("order_total").isin(float("inf"), float("-inf"))
        | (F.col("order_total") < 0) | F.col("churned").isNull()
        | (~F.col("churned").isin(0, 1)))
    if invalid.limit(1).count():
        raise ValueError("Order rows violate the key, date, amount or label contract")
    reject_conflicts(checked, ["customer_id", "order_id"],
                     ["order_date", "order_total", "churned"])
    return checked.dropDuplicates(["customer_id", "order_id"])
