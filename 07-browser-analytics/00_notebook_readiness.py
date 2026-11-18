# Databricks notebook source
# Synthetic session exercise; does not access S3 or create persisted tables.
assert spark.range(3).count() == 3

# COMMAND ----------
learning_rows = [("FAC01", 1), ("FAC02", 1), ("FAC03", 1)]
learning_df = spark.createDataFrame(
    learning_rows, ["facility_id", "appointments"]
)
learning_df.createOrReplaceTempView("learning_facility_check")
assert learning_df.count() == 3
learning_df.show(truncate=False)

# COMMAND ----------
# MAGIC %sql
# MAGIC SELECT SUM(appointments) AS accepted_appointments
# MAGIC FROM learning_facility_check;
