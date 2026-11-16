# Databricks notebook source
import sys
from pathlib import Path
candidates = [Path.cwd() / "shared", Path.cwd().parent / "shared"]
module_root = next((p for p in candidates if (p / "spark_clean.py").is_file()), None)
if module_root is None:
    raise RuntimeError("Open the complete companion project; shared/spark_clean.py is required")
sys.path.insert(0, str(module_root))
from spark_clean import prepare_appointments, prepare_history, prepare_outcomes, check_cohort

raw_appointments = spark.table("analytics.bronze.appointments")
valid, clean, rejected = prepare_appointments(raw_appointments)
history = prepare_history(spark.table("analytics.bronze.appointment_history"))
outcomes = prepare_outcomes(spark.table("analytics.bronze.attendance_outcomes"))
check_cohort(history, outcomes)
# Preflight every dataset before publishing. These Delta writes are separate
# commits; a job must detect and recover a partial multi-table refresh.
assert raw_appointments.count() == 6 and valid.count() == 4 and clean.count() == 3
assert rejected.count() == 2 and history.count() == 40 and outcomes.count() == 20
rejected.write.format("delta").mode("overwrite").saveAsTable("analytics.monitoring.appointment_rejections")
clean.write.format("delta").mode("overwrite").saveAsTable("analytics.silver.appointments")
history.write.format("delta").mode("overwrite").saveAsTable("analytics.operations.appointment_history")
outcomes.write.format("delta").mode("overwrite").saveAsTable("analytics.ml.attendance_outcomes")
print("Checked three appointments, two rejections, forty visits and twenty later outcomes.")

