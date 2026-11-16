# Databricks notebook source
import sys
import os
from pathlib import Path
configured_root = (dbutils.widgets.getAll().get("book_root") if "dbutils" in globals() else None) or os.environ.get("DATABRICKS_BOOK_ROOT")
if configured_root and not Path(configured_root).is_absolute():
    raise RuntimeError("DATABRICKS_BOOK_ROOT must be an absolute project directory")
candidates = ([Path(configured_root) / "shared"] if configured_root else
              [Path.cwd() / "shared", Path.cwd().parent / "shared"])
module_root = next((p for p in candidates if (p / "spark_clean.py").is_file()), None)
if module_root is None:
    raise RuntimeError("Set DATABRICKS_BOOK_ROOT to the complete project directory containing shared/spark_clean.py")
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
assert {(r.appointment_id, r.patient_id, str(r.scheduled_date), r.facility_id)
        for r in clean.collect()} == {
    ("A001", "P001", "2026-03-10", "FAC01"),
    ("A002", "P002", "2026-03-10", "FAC02"),
    ("A006", "P006", "2026-03-10", "FAC03"),
}
rejected.write.format("delta").mode("overwrite").saveAsTable("analytics.monitoring.appointment_rejections")
clean.write.format("delta").mode("overwrite").saveAsTable("analytics.silver.appointments")
history.write.format("delta").mode("overwrite").saveAsTable("analytics.operations.appointment_history")
outcomes.write.format("delta").mode("overwrite").saveAsTable("analytics.ml.attendance_outcomes")
print("Checked three appointments, two rejections, forty visits and twenty later outcomes.")

