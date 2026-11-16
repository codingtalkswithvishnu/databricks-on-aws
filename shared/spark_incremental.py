"""Versioned update rules for the isolated appointment MERGE exercise."""
from pyspark.sql import functions as F, Window
from spark_clean import check_appointment_rows, reject_conflicts

PAYLOAD = ["patient_id", "scheduled_date", "facility_id"]


def prepare_updates(raw):
    checked = check_appointment_rows(raw).withColumn(
        "source_version", F.when(F.col("source_version").rlike(r"^[1-9]\d*$"),
                                  F.expr("try_cast(source_version AS INT)")))
    if checked.filter(F.col("rejection_reason").isNotNull()
                      | F.col("source_version").isNull()).limit(1).count():
        raise ValueError("Update rows require valid appointment fields and a positive integer source version")
    typed = checked.select("appointment_id", "patient_id",
                           F.col("parsed_date").alias("scheduled_date"),
                           "facility_id", "source_version")
    reject_conflicts(typed, ["appointment_id", "source_version"], PAYLOAD)
    return typed.dropDuplicates(["appointment_id", "source_version"])


def latest_updates(prepared):
    order = Window.partitionBy("appointment_id").orderBy(F.col("source_version").desc())
    return (prepared.withColumn("_rank", F.row_number().over(order))
            .filter(F.col("_rank") == 1).drop("_rank"))


def validate_target(target, prepared):
    if dict(target.dtypes).get("source_version") != "int":
        raise ValueError("Target source_version must use the accepted integer type")
    checked = check_appointment_rows(target)
    if checked.filter(F.col("rejection_reason").isNotNull()).limit(1).count():
        raise ValueError("Target appointment fields do not satisfy the accepted contract")
    for key in ["appointment_id", "patient_id", "facility_id"]:
        if target.filter(F.col(key) != F.regexp_replace(key, r"^\s+|\s+$", "")).limit(1).count():
            raise ValueError("Target keys must already have their accepted canonical representation")
    if target.filter(F.col("appointment_id").isNull() | F.col("source_version").isNull()
                     | (F.col("source_version") <= 0)).limit(1).count():
        raise ValueError("Target key/version contract is invalid")
    if target.groupBy("appointment_id").count().filter(F.col("count") > 1).limit(1).count():
        raise ValueError("Target appointment keys must be unique")
    matched = prepared.alias("s").join(target.alias("t"),
        (F.col("s.appointment_id") == F.col("t.appointment_id"))
        & (F.col("s.source_version") == F.col("t.source_version")))
    source_payload = F.struct(*[F.col("s." + name).alias(name) for name in PAYLOAD])
    target_payload = F.struct(*[F.col("t." + name).alias(name) for name in PAYLOAD])
    if matched.filter(~source_payload.eqNullSafe(target_payload)).limit(1).count():
        raise ValueError("An existing source version cannot acquire a different payload")
