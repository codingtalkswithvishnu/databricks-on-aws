# Databricks notebook source
# Optional: reruns the core fixture; requires approved MLflow artifact access.
# MAGIC %run ./04_train_score

# COMMAND ----------
from pyspark.ml import PipelineModel
from mlflow.models import infer_signature

packaged_model = PipelineModel(stages=[assembler, model])
probe = (
    spark.table("analytics.ml.appointment_features")
    .select("patient_id", *predictor_names).orderBy("patient_id").limit(2)
)
signature = infer_signature(
    probe.select(*predictor_names),
    packaged_model.transform(probe.select(*predictor_names)).select("prediction"),
)
with mlflow.start_run(run_name="northstar-model-artifact"):
    mlflow.log_param("training_run_id", model_run_id)
    mlflow.log_param("feature_cutoff", FEATURE_CUTOFF)
    model_info = mlflow.spark.log_model(
        packaged_model, artifact_path="model", signature=signature
    )

reloaded = mlflow.spark.load_model(model_info.model_uri)
expected = packaged_model.transform(probe).select("patient_id", "prediction").orderBy("patient_id").collect()
actual = reloaded.transform(probe).select("patient_id", "prediction").orderBy("patient_id").collect()
assert actual == expected
print("Logged and reloaded model:", model_info.model_uri)
REGISTER_MODEL = False  # Enable only in an approved practice copy with registry privileges.

# COMMAND ----------
if REGISTER_MODEL:
    mlflow.set_registry_uri("databricks-uc")
    candidate = mlflow.register_model(
        model_uri=model_info.model_uri,
        name="analytics.ml.appointment_attendance",
    )
    print("Candidate model version:", candidate.version)
else:
    print("Registry step skipped; the logged artifact remains the learning checkpoint")
