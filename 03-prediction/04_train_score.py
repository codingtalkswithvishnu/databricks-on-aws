# Databricks notebook source
# Requires compatible Spark ML and MLflow; no live execution claimed.
import sys
import os
from pathlib import Path
from pyspark.sql import functions as F

configured_root = (dbutils.widgets.getAll().get("book_root") if "dbutils" in globals() else None) or os.environ.get("DATABRICKS_BOOK_ROOT")
if configured_root and not Path(configured_root).is_absolute():
    raise RuntimeError("DATABRICKS_BOOK_ROOT must be an absolute project directory")
candidates = ([Path(configured_root) / "shared"] if configured_root else
              [Path.cwd() / "shared", Path.cwd().parent / "shared"])
module_root = next((p for p in candidates if (p / "healthcare.py").is_file()), None)
if module_root is None:
    raise RuntimeError("Set DATABRICKS_BOOK_ROOT to the complete project directory")
sys.path.insert(0, str(module_root))
from healthcare import FEATURE_CUTOFF, SCORE_START

history = spark.table("analytics.operations.appointment_history")
labels = spark.table("analytics.ml.attendance_outcomes")
assert history.filter(F.col("visit_date") >= F.lit(FEATURE_CUTOFF).cast("date")).count() == 0
assert labels.count() == labels.select("patient_id").distinct().count() == 20
assert labels.filter(
    (F.col("scheduled_date") < F.lit(FEATURE_CUTOFF).cast("date"))
    | (F.col("observed_date") <= F.col("scheduled_date"))
).count() == 0

historical_features = spark.sql(f"""
    SELECT patient_id,
           COUNT(*) AS prior_visits,
           SUM(1 - attended) AS prior_missed_visits,
           AVG(lead_days) AS avg_lead_days
    FROM analytics.operations.appointment_history
    WHERE visit_date < DATE '{FEATURE_CUTOFF}'
    GROUP BY patient_id
""")
features = (
    historical_features.join(labels.select("patient_id", "no_show"), "patient_id")
    .withColumn("feature_cutoff", F.lit(FEATURE_CUTOFF).cast("date"))
)
assert features.count() == 20
features.write.format("delta").mode("overwrite").saveAsTable(
    "analytics.ml.appointment_features"
)

# COMMAND ----------
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import BinaryClassificationEvaluator
import mlflow

predictor_names = ["prior_visits", "prior_missed_visits", "avg_lead_days"]
assembler = VectorAssembler(inputCols=predictor_names, outputCol="features")
training = assembler.transform(spark.table("analytics.ml.appointment_features"))

# Fixed patient split for this learning fixture.
number = F.regexp_extract("patient_id", r"(\d+)$", 1).cast("int")
train = training.filter(number % 5 != 0)
test = training.filter(number % 5 == 0)
assert train.count() == 16 and test.count() == 4
assert train.select("no_show").distinct().count() == 2
assert test.select("no_show").distinct().count() == 2

with mlflow.start_run(run_name="northstar-attendance-fixture") as run:
    model = LogisticRegression(featuresCol="features", labelCol="no_show").fit(train)
    predictions = model.transform(test)
    auc = BinaryClassificationEvaluator(labelCol="no_show").evaluate(predictions)
    mlflow.log_metric("fixture_test_auc", auc)
    mlflow.log_param("fixture_patients", 20)
    mlflow.log_param("feature_cutoff", FEATURE_CUTOFF)
    mlflow.log_param("predictor_order", ",".join(predictor_names))
    mlflow.log_param("estimator", "LogisticRegression")
    mlflow.log_param("max_iter", model.getMaxIter())
    mlflow.log_param("reg_param", model.getRegParam())
    mlflow.log_param("prediction_threshold", model.getThreshold())
    model_run_id = run.info.run_id
    print("Held-out fixture AUC:", auc)

# COMMAND ----------
from pyspark.ml.functions import vector_to_array

upcoming = spark.table("analytics.operations.appointments")
last_observed = labels.agg(F.max("observed_date")).first()[0]
assert upcoming.filter(
    (F.col("scheduled_date") <= F.lit(last_observed))
    | (F.col("scheduled_date") < F.lit(SCORE_START).cast("date"))
).count() == 0
predictors = spark.table("analytics.ml.appointment_features").select(
    "patient_id", *predictor_names
)
score_input = upcoming.join(predictors, "patient_id", "left")
assert score_input.count() == 3
assert score_input.filter(F.col("prior_visits").isNull()).count() == 0

scored = (
    model.transform(assembler.transform(score_input))
    .withColumn("missed_appointment_probability", vector_to_array("probability")[1])
    .withColumn("feature_cutoff", F.lit(FEATURE_CUTOFF).cast("date"))
    .withColumn("model_run_id", F.lit(model_run_id))
    .select("appointment_id", "patient_id", "facility_id", "scheduled_date",
            "prediction", "missed_appointment_probability", "feature_cutoff", "model_run_id")
)
assert scored.count() == scored.select("appointment_id").distinct().count() == 3
scored.write.format("delta").mode("overwrite").saveAsTable(
    "analytics.gold.appointment_scores"
)
review_queue = scored.filter(F.col("prediction") == 1.0)
review_queue.write.format("delta").mode("overwrite").saveAsTable(
    "analytics.gold.outreach_review_queue"
)
