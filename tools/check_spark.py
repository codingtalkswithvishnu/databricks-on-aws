# Databricks notebook source
"""Run with compatible Spark, or %run ../tools/check_spark in Databricks.

Uses synthetic DataFrames only; creates no tables and makes no model requests.
"""
import sys
import unittest
from pathlib import Path
from pyspark.sql import SparkSession

ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()
if not (ROOT / "shared").is_dir():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "shared"))
from cedar import records
from spark_clean import prepare_signups, prepare_orders


class SparkQualityChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()

    def signups(self, rows):
        return self.spark.createDataFrame(rows, "email STRING, signup_date STRING, country STRING")

    def orders(self, rows):
        return self.spark.createDataFrame(rows, "customer_id STRING, order_id STRING, "
                                          "order_date STRING, order_total STRING, churned STRING")

    def test_signup_fixture_and_identical_duplicate(self):
        valid, clean = prepare_signups(self.signups(records("signups.csv")))
        self.assertEqual((valid.count(), clean.count()), (4, 3))
        counts = {row.country:row["count"] for row in clean.groupBy("country").count().collect()}
        self.assertEqual(counts, {"GB":1, "IN":1, "US":1})

    def test_conflicting_signup_in_either_input_order(self):
        original = records("signups.csv")[0]
        for country in ["US", None]:
            conflict = {**original, "country":country}
            for rows in [[original, conflict], [conflict, original]]:
                with self.subTest(country=country), self.assertRaises(ValueError):
                    prepare_signups(self.signups(rows))

    def test_order_fixture_and_identical_duplicate(self):
        rows = records("orders.csv")
        result = prepare_orders(self.orders(rows + [rows[0]]))
        self.assertEqual(result.count(), 40)
        self.assertEqual(dict(result.dtypes)["order_total"], "double")

    def test_invalid_order_is_not_hidden_by_duplicate_removal(self):
        original = records("orders.csv")[0]
        invalid_values = {"customer_id":[None, "   ", "\t\n"], "order_id":[None, "", "\t"],
                          "order_date":[None, "not-a-date"],
                          "order_total":[None, "bad", "-1", "NaN", "Infinity", "-Infinity"],
                          "churned":[None, "2", "bad"]}
        for field, values in invalid_values.items():
            for value in values:
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    prepare_orders(self.orders([original, {**original, field:value}]))

    def test_conflicting_valid_order_in_either_input_order(self):
        original = records("orders.csv")[0]
        conflict = {**original, "order_total":"999"}
        for rows in [[original, conflict], [conflict, original]]:
            with self.assertRaises(ValueError):
                prepare_orders(self.orders(rows))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SparkQualityChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError("Spark quality checks failed")
