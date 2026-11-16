# Databricks notebook source
# Optional provisioned Kinesis route; the producer and approved stream must exist.
events = (
    spark.readStream.format("kinesis")
    .option("streamName", "northstar-check-in-events")
    .option("region", "us-east-1")
    .option("initialPosition", "earliest")
    .load()
)
query = (
    events.writeStream.format("delta")
    .option("checkpointLocation",
            "s3://northstar-learning-lakehouse/_checkpoints/appointment_events/")
    .trigger(availableNow=True)
    .toTable("analytics.bronze.appointment_events")
)
query.awaitTermination()

# COMMAND ----------
from pyspark.sql import functions as F

spark.conf.set("spark.sql.session.timeZone", "UTC")
payload_schema = (
    "event_id STRING, appointment_id STRING, facility_id STRING, "
    "event_type STRING, event_time STRING"
)
landed = (
    spark.table("analytics.bronze.appointment_events")
    .select(F.from_json(F.col("data").cast("string"), payload_schema).alias("event"))
    .select("event.*")
    .withColumn("event_time", F.try_to_timestamp("event_time"))
)
assert landed.count() == 3
assert {row.event_id for row in landed.select("event_id").collect()} == {
    "E001", "E002", "E003"
}
assert landed.filter(
    F.col("event_time").isNull() | F.col("event_type").isNull()
    | (F.col("event_type") != "check_in")
).count() == 0
expected_pairs = {(row.appointment_id, row.facility_id) for row in
                  spark.table("analytics.operations.appointments").select(
                      "appointment_id", "facility_id").collect()}
assert {(row.appointment_id, row.facility_id) for row in landed.collect()} == expected_pairs
per_minute = landed.groupBy(F.window("event_time", "1 minute"), "facility_id").count()
assert per_minute.select("window").distinct().count() == 1
actual = {row.facility_id: row["count"] for row in per_minute.collect()}
assert actual == {"FAC01": 1, "FAC02": 1, "FAC03": 1}
per_minute.write.format("delta").mode("overwrite").saveAsTable(
    "analytics.gold.check_in_counts"
)
