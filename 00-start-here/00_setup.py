# Databricks notebook source
# Run in a disposable, administrator-approved analytics catalog.
import sys
import os
from pathlib import Path
configured_root = (dbutils.widgets.getAll().get("book_root") if "dbutils" in globals() else None) or os.environ.get("DATABRICKS_BOOK_ROOT")
if configured_root and not Path(configured_root).is_absolute():
    raise RuntimeError("DATABRICKS_BOOK_ROOT must be an absolute project directory")
candidates = ([Path(configured_root) / "shared"] if configured_root else
              [Path.cwd() / "shared", Path.cwd().parent / "shared"])
module_root = next((p for p in candidates if (p / "healthcare.py").is_file()), None)
if module_root is None:
    raise RuntimeError("Set DATABRICKS_BOOK_ROOT to the complete project directory containing shared/healthcare.py")
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

