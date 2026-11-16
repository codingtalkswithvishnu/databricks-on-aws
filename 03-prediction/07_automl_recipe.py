# Databricks notebook source
# Recipe only; an approved larger training cohort must be supplied before invocation.
from databricks import automl

def start_automl_comparison(training_cohort):
    predictors = ["prior_visits", "prior_missed_visits", "avg_lead_days"]
    required = set(predictors + ["no_show"])
    if not required.issubset(training_cohort.columns):
        raise ValueError("Provide the accepted predictors and later attendance label")
    return automl.classify(
        dataset=training_cohort.select(*predictors, "no_show"),
        target_col="no_show",
        primary_metric="roc_auc",
        timeout_minutes=20,
    )

# Call only after the model owner supplies and reviews the comparison cohort:
# summary = start_automl_comparison(training_cohort)
# print(summary.best_trial.model_description)
