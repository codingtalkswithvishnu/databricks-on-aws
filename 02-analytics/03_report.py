# Databricks notebook source
spark.sql("""
    CREATE OR REPLACE VIEW analytics.operations.appointments AS
    SELECT appointment_id, patient_id, scheduled_date, facility_id
    FROM analytics.silver.appointments
""")
result = spark.sql("""
    SELECT facility_id, COUNT(*) AS appointments
    FROM analytics.operations.appointments GROUP BY facility_id ORDER BY facility_id
""")
actual = {r["facility_id"]:r["appointments"] for r in result.collect()}
assert actual == {"FAC01":1,"FAC02":1,"FAC03":1}
result.write.format("delta").mode("overwrite").saveAsTable("analytics.gold.appointments_by_facility")
result.show()

