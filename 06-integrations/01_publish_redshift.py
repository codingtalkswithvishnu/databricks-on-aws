# Databricks notebook source
# Optional configured classic-compute route. No live connection claimed.
import json

options = json.loads(dbutils.secrets.get(
    scope="northstar-learning", key="redshift-demo-options"
))
required = {"url", "user", "password", "aws_iam_role", "tempdir", "dbtable"}
if not isinstance(options, dict) or not required.issubset(options):
    raise ValueError("The owner must provide complete approved Redshift options")
if options["dbtable"] != "reporting.northstar_facility_demo":
    raise ValueError("Use only the approved disposable Redshift target")
summary = spark.table("analytics.gold.appointments_by_facility")
assert set(summary.columns) == {"facility_id", "appointments"}
assert summary.count() == 3
assert {row.facility_id:row.appointments for row in summary.collect()} == {
    "FAC01":1, "FAC02":1, "FAC03":1
}
summary.write.format("redshift").options(**options).mode("errorifexists").save()
read_back = spark.read.format("redshift").options(**options).load()
assert read_back.count() == 3
assert {row.facility_id:row.appointments for row in read_back.collect()} == {
    "FAC01":1, "FAC02":1, "FAC03":1
}
print("Disposable facility aggregate published and read back")
