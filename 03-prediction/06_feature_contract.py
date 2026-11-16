# Databricks notebook source
# Optional: creates a separate fixed-snapshot feature demonstration table.
from databricks.feature_engineering import FeatureEngineeringClient

feature_data = spark.table("analytics.ml.appointment_features").select(
    "patient_id", "prior_visits", "prior_missed_visits", "avg_lead_days", "feature_cutoff"
)
assert feature_data.count() == feature_data.select("patient_id").distinct().count() == 20
fe = FeatureEngineeringClient()
fe.create_table(
    name="analytics.ml.attendance_features_demo",
    primary_keys=["patient_id"],
    df=feature_data,
    description="Northstar synthetic attendance predictors at the fixed February cutoff",
)
print("Created the separate fixed-snapshot feature demonstration")
