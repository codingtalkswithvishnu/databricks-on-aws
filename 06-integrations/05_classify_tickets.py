# Databricks notebook source
# Optional configured cloud exercise; no live execution claimed.
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
    raise RuntimeError("Set DATABRICKS_BOOK_ROOT to the complete project directory")
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
