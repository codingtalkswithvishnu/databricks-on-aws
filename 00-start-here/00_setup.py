# Databricks notebook source
# Run in a disposable, administrator-approved analytics catalog.
import sys
from pathlib import Path
candidates = [Path.cwd() / "shared", Path.cwd().parent / "shared"]
module_root = next((p for p in candidates if (p / "healthcare.py").is_file()), None)
if module_root is None:
    raise RuntimeError("Open the complete companion project; shared/healthcare.py is required")
sys.path.insert(0, str(module_root))
from healthcare import records, policies, APPOINTMENT_SCHEMA, HISTORY_SCHEMA, OUTCOME_SCHEMA

assert spark.range(3).count() == 3
for schema in ["bronze", "silver", "gold", "operations", "ml", "support", "monitoring"]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS analytics.{schema}")

raw_appointments = spark.createDataFrame(records("appointments.csv"), APPOINTMENT_SCHEMA)
raw_history = spark.createDataFrame(records("appointment_history.csv"), HISTORY_SCHEMA)
raw_outcomes = spark.createDataFrame(records("attendance_outcomes.csv"), OUTCOME_SCHEMA)
assert raw_appointments.count() == 6 and raw_history.count() == 40 and raw_outcomes.count() == 20
print("Synthetic source fixtures ready. This does not verify S3 access.")

