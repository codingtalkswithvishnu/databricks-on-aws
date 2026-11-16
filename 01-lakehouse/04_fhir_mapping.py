# Databricks notebook source
# OPTIONAL: a limited synthetic envelope mapping into separate demo tables.
import sys
from pathlib import Path
candidates = [Path.cwd() / "shared", Path.cwd().parent / "shared"]
module_root = next((p for p in candidates if (p / "healthcare.py").is_file()), None)
if module_root is None:
    raise RuntimeError("Open the complete companion project")
sys.path.insert(0, str(module_root))
from healthcare import ROOT
from spark_fhir import extract_appointments
from spark_clean import prepare_appointments

payload = (ROOT / "sample-data" / "appointments_bundle.json").read_text(encoding="utf-8")
raw = spark.createDataFrame([(payload,)], "payload STRING")
raw.write.format("delta").mode("overwrite").saveAsTable("analytics.bronze.appointment_bundles_demo")
flattened = extract_appointments(spark.table("analytics.bronze.appointment_bundles_demo"))
valid, clean, rejected = prepare_appointments(flattened)
assert flattened.count() == 6 and valid.count() == 4
assert clean.count() == 3 and rejected.count() == 2
clean.write.format("delta").mode("overwrite").saveAsTable("analytics.silver.fhir_appointments_demo")
rejected.write.format("delta").mode("overwrite").saveAsTable("analytics.monitoring.fhir_appointment_rejections_demo")
baseline = spark.table("analytics.silver.appointments").select(clean.columns)
assert clean.join(baseline, clean.columns, "left_anti").count() == 0
assert baseline.join(clean, clean.columns, "left_anti").count() == 0
print("Mapped six fixture resources: three accepted appointments, two rejected rows and one identical duplicate.")
