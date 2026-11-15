# Databricks notebook source
import sys
from pathlib import Path
candidates = [Path.cwd() / "shared", Path.cwd().parent / "shared"]
module_root = next((p for p in candidates if (p / "spark_clean.py").is_file()), None)
if module_root is None:
    raise RuntimeError("Open the complete companion project; shared/spark_clean.py is required")
sys.path.insert(0, str(module_root))
from spark_clean import prepare_signups, prepare_orders

raw_signups = spark.table("analytics.bronze.signups")
valid, clean = prepare_signups(raw_signups)
orders = prepare_orders(spark.table("analytics.bronze.orders"))
# Preflight both datasets before publishing either output. The two Delta writes
# are separate commits; they are not a cross-table transaction.
assert raw_signups.count() == 6 and valid.count() == 4 and clean.count() == 3
assert orders.count() == 40
clean.write.format("delta").mode("overwrite").saveAsTable("analytics.silver.signups")
orders.write.format("delta").mode("overwrite").saveAsTable("analytics.sales.orders")
print("Checked three signups and forty typed orders.")

