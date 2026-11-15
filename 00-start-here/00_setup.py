# Databricks notebook source
# Run in a disposable, administrator-approved analytics catalog.
import sys
from pathlib import Path
candidates = [Path.cwd() / "shared", Path.cwd().parent / "shared"]
module_root = next((p for p in candidates if (p / "cedar.py").is_file()), None)
if module_root is None:
    raise RuntimeError("Open the complete companion project; shared/cedar.py is required")
sys.path.insert(0, str(module_root))
from cedar import records, policies

assert spark.range(3).count() == 3
for schema in ["bronze", "silver", "gold", "customers", "sales", "ml", "support", "monitoring"]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS analytics.{schema}")

raw_signups = spark.createDataFrame(
    records("signups.csv"), "email STRING, signup_date STRING, country STRING")
raw_orders = spark.createDataFrame(
    records("orders.csv"),
    "customer_id STRING, order_id STRING, order_date STRING, order_total STRING, churned STRING")
assert raw_signups.count() == 6 and raw_orders.count() == 40
print("Synthetic source fixtures ready. This does not verify S3 access.")

