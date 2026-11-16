# Databricks notebook source
import os
if "dbutils" in globals():
    project_root = dbutils.widgets.getAll().get("book_root")
    if project_root:
        os.environ["DATABRICKS_BOOK_ROOT"] = project_root

# COMMAND ----------
# MAGIC %run ../00-start-here/00_setup

# COMMAND ----------
# These are synthetic fixture resets, never a production ingestion policy.
raw_appointments.write.format("delta").mode("overwrite").saveAsTable("analytics.bronze.appointments")
raw_history.write.format("delta").mode("overwrite").saveAsTable("analytics.bronze.appointment_history")
raw_outcomes.write.format("delta").mode("overwrite").saveAsTable("analytics.bronze.attendance_outcomes")
spark.createDataFrame(records("tickets.csv")).write.format("delta").mode("overwrite").saveAsTable(
    "analytics.support.tickets")
spark.createDataFrame(policies()).write.format("delta").mode("overwrite").saveAsTable(
    "analytics.support.help_articles")
spark.sql("""
    ALTER TABLE analytics.support.help_articles
    SET TBLPROPERTIES (delta.enableChangeDataFeed = true)
""")
assert spark.table("analytics.bronze.appointments").count() == 6
assert spark.table("analytics.bronze.appointment_history").count() == 40
assert spark.table("analytics.bronze.attendance_outcomes").count() == 20
assert spark.table("analytics.support.tickets").count() == 3
assert spark.table("analytics.support.help_articles").count() == 3

