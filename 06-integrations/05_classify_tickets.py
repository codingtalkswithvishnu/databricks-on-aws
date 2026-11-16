# Databricks notebook source
# Optional configured cloud exercise; no live execution claimed.
import sys
from pathlib import Path
candidates = [Path.cwd() / "shared", Path.cwd().parent / "shared"]
module_root = next((p for p in candidates if (p / "healthcare.py").is_file()), None)
if module_root is None:
    raise RuntimeError("Open the complete companion project")
sys.path.insert(0, str(module_root))

# COMMAND ----------
import os
import re
endpoint = os.environ.get("DATABRICKS_MODEL_ENDPOINT", "")
if not re.fullmatch(r"[A-Za-z0-9_.-]{1,200}", endpoint):
    raise ValueError("Set the approved model endpoint identifier in this notebook process")
result = spark.sql(f"""
    SELECT ticket_id, expected_category,
           ai_query(
               '{endpoint}',
               CONCAT(
                   'Return exactly billing, technical, or other. Ticket: ',
                   message
               )
           ) AS predicted_category
    FROM analytics.support.tickets
""")
result.write.format("delta").mode("overwrite").saveAsTable(
    "analytics.support.ticket_classification_demo"
)
from pyspark.sql import functions as F
checked = spark.table("analytics.support.ticket_classification_demo").withColumn(
    "predicted_category", F.lower(F.trim("predicted_category"))
)
assert checked.count() == 3
assert checked.filter(
    F.col("predicted_category").isNull()
    | (~F.col("predicted_category").isin("billing", "technical", "other"))
).count() == 0
assert checked.filter(F.col("predicted_category") != F.col("expected_category")).count() == 0
checked.show(truncate=False)
