"""Shared Northstar batch-quality rules. Requires compatible PySpark."""
from pyspark.sql import functions as F
from healthcare import FACILITIES, FEATURE_CUTOFF


def reject_conflicts(frame, keys, values):
    variants = frame.groupBy(*keys).agg(
        F.countDistinct(F.struct(*values)).alias("variants"))
    if variants.filter(F.col("variants") > 1).limit(1).count():
        raise ValueError("Conflicting duplicates need an accepted winner rule")


def normalize_keys(frame, keys):
    for key in keys:
        frame = frame.withColumn(key, F.regexp_replace(key, r"^\s+|\s+$", ""))
    return frame


def blank(name):
    return F.col(name).isNull() | (F.length(name) == 0)


def parsed_date(name):
    return F.when(F.col(name).rlike(r"^\d{4}-\d{2}-\d{2}$"),
                  F.expr("try_cast(" + name + " AS DATE)"))


def check_appointment_rows(raw):
    checked = normalize_keys(raw, ["appointment_id", "patient_id", "facility_id"])
    checked = checked.withColumn("parsed_date", parsed_date("scheduled_date"))
    checked = checked.withColumn("rejection_reason",
        F.when(blank("appointment_id"), "missing appointment_id")
         .when(blank("patient_id"), "missing patient_id")
         .when(blank("facility_id") | (~F.col("facility_id").isin(*FACILITIES)), "unknown facility_id")
         .when(F.col("parsed_date").isNull(), "invalid scheduled_date"))
    return checked


def prepare_appointments(raw):
    checked = check_appointment_rows(raw)
    rejected = checked.filter(F.col("rejection_reason").isNotNull()).drop("parsed_date")
    valid = checked.filter(F.col("rejection_reason").isNull())
    reject_conflicts(valid, ["appointment_id"], ["patient_id", "parsed_date", "facility_id"])
    clean = valid.select("appointment_id", "patient_id",
                         F.col("parsed_date").alias("scheduled_date"), "facility_id")
    return valid, clean.dropDuplicates(["appointment_id"]), rejected


def prepare_history(raw):
    checked = normalize_keys(raw, ["patient_id", "visit_id"])
    checked = (checked.withColumn("visit_date", parsed_date("visit_date"))
               .withColumn("lead_days", F.expr("try_cast(lead_days AS DOUBLE)"))
               .withColumn("attended", F.when(F.col("attended").isin("0", "1"),
                                             F.col("attended").cast("int"))))
    invalid = checked.filter(
        blank("patient_id") | blank("visit_id") | F.col("visit_date").isNull()
        | (F.col("visit_date") >= F.lit(FEATURE_CUTOFF).cast("date"))
        | F.col("lead_days").isNull() | F.isnan("lead_days")
        | F.col("lead_days").isin(float("inf"), float("-inf"))
        | (F.col("lead_days") < 0) | F.col("attended").isNull())
    if invalid.limit(1).count():
        raise ValueError("History must precede the feature cutoff and meet the key/value contract")
    reject_conflicts(checked, ["visit_id"], ["patient_id", "visit_date", "lead_days", "attended"])
    return checked.dropDuplicates(["visit_id"])


def prepare_outcomes(raw):
    checked = normalize_keys(raw, ["patient_id", "appointment_id", "facility_id"])
    checked = (checked.withColumn("scheduled_date", parsed_date("scheduled_date"))
               .withColumn("observed_date", parsed_date("observed_date"))
               .withColumn("no_show", F.when(F.col("no_show").isin("0", "1"),
                                            F.col("no_show").cast("int"))))
    invalid = checked.filter(
        blank("patient_id") | blank("appointment_id") | blank("facility_id")
        | (~F.col("facility_id").isin(*FACILITIES))
        | F.col("scheduled_date").isNull() | F.col("observed_date").isNull()
        | (F.col("scheduled_date") < F.lit(FEATURE_CUTOFF).cast("date"))
        | (F.col("observed_date") <= F.col("scheduled_date")) | F.col("no_show").isNull())
    if invalid.limit(1).count():
        raise ValueError("Outcomes require a future appointment and a later observed binary label")
    # This teaching cohort permits exactly one target appointment per patient.
    for key in ["patient_id", "appointment_id"]:
        if checked.groupBy(key).count().filter(F.col("count") > 1).limit(1).count():
            raise ValueError("Outcome cohort keys must be unique")
    return checked


def check_cohort(history, outcomes):
    patients = history.select("patient_id").distinct()
    labels = outcomes.select("patient_id")
    if (patients.join(labels, "patient_id", "left_anti").limit(1).count()
            or labels.join(patients, "patient_id", "left_anti").limit(1).count()):
        raise ValueError("History and outcome cohorts must match")
