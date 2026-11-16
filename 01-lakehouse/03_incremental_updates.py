# Databricks notebook source
# OPTIONAL: resets only the named demo table, then tests repeat and stale-input behavior.
import sys
from pathlib import Path
from pyspark.sql import functions as F
candidates = [Path.cwd() / "shared", Path.cwd().parent / "shared"]
module_root = next((p for p in candidates if (p / "healthcare.py").is_file()), None)
if module_root is None:
    raise RuntimeError("Open the complete companion project")
sys.path.insert(0, str(module_root))
from healthcare import records, UPDATE_SCHEMA
from spark_incremental import prepare_updates, latest_updates, validate_target

TARGET = "analytics.silver.appointments_incremental_demo"
baseline = spark.table("analytics.silver.appointments")
assert baseline.count() == 3
baseline.withColumn("source_version", F.lit(1)).write.format("delta").mode("overwrite").saveAsTable(TARGET)
raw_updates = spark.createDataFrame(records("appointment_updates.csv"), UPDATE_SCHEMA)
assert raw_updates.count() == 4


def apply_batch(raw):
    prepared = prepare_updates(raw)
    validate_target(spark.table(TARGET), prepared)
    latest_updates(prepared).createOrReplaceTempView("northstar_updates_for_merge")
    spark.sql("""
        MERGE INTO analytics.silver.appointments_incremental_demo AS t
        USING northstar_updates_for_merge AS s
        ON t.appointment_id = s.appointment_id
        WHEN MATCHED AND s.source_version > t.source_version THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
    """)


apply_batch(raw_updates)
first = spark.table(TARGET).orderBy("appointment_id").collect()
assert len(first) == 4
by_id = {row.appointment_id:row for row in first}
assert by_id["A001"].facility_id == "FAC02" and by_id["A001"].source_version == 2
assert by_id["A007"].source_version == 1
apply_batch(raw_updates)
assert spark.table(TARGET).orderBy("appointment_id").collect() == first
stale = raw_updates.filter((F.col("appointment_id") == "A001") & (F.col("source_version") == "1"))
apply_batch(stale)
assert spark.table(TARGET).orderBy("appointment_id").collect() == first
assert spark.table("analytics.silver.appointments").count() == 3
print("Demo: four current rows; repeated batch and stale update preserve state; baseline remains three.")
