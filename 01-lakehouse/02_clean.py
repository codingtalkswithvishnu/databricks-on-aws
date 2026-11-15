# Databricks notebook source
from pyspark.sql import functions as F
raw_signups = spark.table("analytics.bronze.signups")
checked = (raw_signups.withColumn("email", F.trim("email"))
    .withColumn("parsed_date", F.expr("try_cast(signup_date AS DATE)")))
valid = checked.filter(F.col("email").isNotNull() & (F.length("email") > 0)
    & F.col("parsed_date").isNotNull())
clean = valid.dropDuplicates(["email"]).select(
    "email", F.col("parsed_date").alias("signup_date"), "country")
assert raw_signups.count() == 6 and valid.count() == 4 and clean.count() == 3
clean.write.format("delta").mode("overwrite").saveAsTable("analytics.silver.signups")

orders = (spark.table("analytics.bronze.orders")
    .withColumn("order_date", F.expr("try_cast(order_date AS DATE)"))
    .withColumn("order_total", F.expr("try_cast(order_total AS DOUBLE)"))
    .withColumn("churned", F.expr("try_cast(churned AS INT)"))
    .dropDuplicates(["customer_id", "order_id"]))
invalid = orders.filter(
    F.col("customer_id").isNull() | F.col("order_id").isNull()
    | F.col("order_date").isNull() | F.col("order_total").isNull()
    | (F.col("order_total") < 0) | F.col("churned").isNull()
    | (~F.col("churned").isin(0, 1)))
assert invalid.count() == 0 and orders.count() == 40
orders.write.format("delta").mode("overwrite").saveAsTable("analytics.sales.orders")
print("Checked three signups and forty typed orders.")

