# Databricks notebook source
spark.sql("""
    CREATE OR REPLACE VIEW analytics.customers.signups AS
    SELECT email, signup_date, country FROM analytics.silver.signups
""")
result = spark.sql("""
    SELECT country, COUNT(*) AS signups
    FROM analytics.customers.signups GROUP BY country ORDER BY country
""")
actual = {r["country"]:r["signups"] for r in result.collect()}
assert actual == {"GB":1,"IN":1,"US":1}
result.write.format("delta").mode("overwrite").saveAsTable("analytics.gold.signups_by_country")
result.show()

