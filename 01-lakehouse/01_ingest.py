# Databricks notebook source
# MAGIC %run ../00-start-here/00_setup

# COMMAND ----------
# These are synthetic fixture resets, never a production ingestion policy.
raw_signups.write.format("delta").mode("overwrite").saveAsTable("analytics.bronze.signups")
raw_orders.write.format("delta").mode("overwrite").saveAsTable("analytics.bronze.orders")
spark.createDataFrame(records("tickets.csv")).write.format("delta").mode("overwrite").saveAsTable(
    "analytics.support.tickets")
spark.createDataFrame(policies()).write.format("delta").mode("overwrite").saveAsTable(
    "analytics.support.help_articles")
spark.sql("""
    ALTER TABLE analytics.support.help_articles
    SET TBLPROPERTIES (delta.enableChangeDataFeed = true)
""")
assert spark.table("analytics.bronze.signups").count() == 6
assert spark.table("analytics.bronze.orders").count() == 40
assert spark.table("analytics.support.tickets").count() == 3
assert spark.table("analytics.support.help_articles").count() == 3

