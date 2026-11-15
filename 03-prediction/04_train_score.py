# Databricks notebook source
# Requires compatible Spark ML and MLflow; no live execution claimed.
features = spark.sql("""
    SELECT customer_id,
           COUNT(*) AS orders_count,
           AVG(order_total) AS avg_spend,
           MAX(churned) AS churned
    FROM analytics.sales.orders
    GROUP BY customer_id
""")
inconsistent = spark.sql("""
    SELECT customer_id
    FROM analytics.sales.orders
    GROUP BY customer_id
    HAVING MIN(churned) <> MAX(churned)
""")
assert inconsistent.count() == 0
assert features.count() == 20
features.write.format("delta").mode("overwrite").saveAsTable(
    "analytics.customers.churn_features"
)

# COMMAND ----------
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.sql import functions as F
import mlflow

training = VectorAssembler(
    inputCols=["orders_count", "avg_spend"],
    outputCol="features",
).transform(spark.table("analytics.customers.churn_features"))

# A reproducible fixture split: C005, C010, C015, C020 are held out.
number = F.regexp_extract("customer_id", r"(\d+)$", 1).cast("int")
train = training.filter(number % 5 != 0)
test = training.filter(number % 5 == 0)
assert train.count() == 16 and test.count() == 4
assert train.select("churned").distinct().count() == 2
assert test.select("churned").distinct().count() == 2

with mlflow.start_run(run_name="cedar-retail-fixture"):
    model = LogisticRegression(
        featuresCol="features", labelCol="churned"
    ).fit(train)
    predictions = model.transform(test)
    auc = BinaryClassificationEvaluator(
        labelCol="churned"
    ).evaluate(predictions)
    mlflow.log_metric("fixture_test_auc", auc)
    mlflow.log_param("fixture_customers", 20)
    print("Held-out fixture AUC:", auc)

# COMMAND ----------
scored = model.transform(training)
at_risk = (
    scored.filter(F.col("prediction") == 1.0)
    .select("customer_id", "avg_spend", "prediction")
)
at_risk.write.format("delta").mode("overwrite").saveAsTable(
    "analytics.gold.at_risk"
)
assert at_risk.select("customer_id").distinct().count() == at_risk.count()
