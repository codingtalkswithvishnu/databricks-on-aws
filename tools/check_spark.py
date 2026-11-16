# Databricks notebook source
"""Synthetic DataFrame checks: python tools/check_spark.py with compatible Spark,
or %run ../tools/check_spark from a numbered notebook in the complete project.
No tables or model endpoints are created.
Literal-column fixture construction avoids a Python worker/UDF dependency.
"""
import sys
import json
import unittest
from pathlib import Path
from pyspark.sql import SparkSession, functions as F

ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()
if not (ROOT / "shared").is_dir():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "shared"))
from healthcare import ROOT as DATA_ROOT, records, training_rows, APPOINTMENT_SCHEMA, HISTORY_SCHEMA, OUTCOME_SCHEMA, UPDATE_SCHEMA
from spark_clean import prepare_appointments, prepare_history, prepare_outcomes, check_cohort
from spark_incremental import prepare_updates, latest_updates, validate_target
from spark_fhir import extract_appointments


class SparkQualityChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()

    def frame(self, rows, schema):
        fields = [part.strip().split()[0] for part in schema.split(",")]
        if any(part.strip().split()[1].upper() != "STRING" for part in schema.split(",")):
            raise ValueError("The raw fixture factory accepts explicit string schemas only")
        values = [F.struct(*[F.lit(row.get(name)).cast("string").alias(name) for name in fields])
                  for row in rows]
        if not values:
            return self.spark.range(0).select(*[F.lit(None).cast("string").alias(name) for name in fields])
        return self.spark.range(1).select(F.explode(F.array(*values)).alias("record")).select("record.*")

    def appointments(self, rows):
        return self.frame(rows, APPOINTMENT_SCHEMA)

    def history(self, rows):
        return self.frame(rows, HISTORY_SCHEMA)

    def outcomes(self, rows):
        return self.frame(rows, OUTCOME_SCHEMA)

    def test_appointment_fixture_and_rejection_reasons(self):
        valid, clean, rejected = prepare_appointments(self.appointments(records("appointments.csv")))
        self.assertEqual((valid.count(), clean.count(), rejected.count()), (4,3,2))
        counts = {r.facility_id:r["count"] for r in clean.groupBy("facility_id").count().collect()}
        self.assertEqual(counts, {"FAC01":1,"FAC02":1,"FAC03":1})
        self.assertEqual({r.rejection_reason for r in rejected.collect()},
                         {"missing appointment_id", "invalid scheduled_date"})

    def test_conflicting_appointment_in_either_input_order(self):
        original = records("appointments.csv")[0]
        for field, value in [("facility_id", "FAC02"), ("patient_id", "P020"),
                             ("scheduled_date", "2026-03-11")]:
            conflict = {**original, field:value}
            for rows in [[original, conflict], [conflict, original]]:
                with self.subTest(field=field), self.assertRaises(ValueError):
                    prepare_appointments(self.appointments(rows))

    def test_unknown_facility_and_blank_patient_are_quarantined(self):
        original = records("appointments.csv")[0]
        for change in [{"facility_id":"FAC99"}, {"patient_id":"\t "},
                       {"scheduled_date":"20260310"}]:
            _, clean, rejected = prepare_appointments(self.appointments([{**original, **change}]))
            self.assertEqual((clean.count(), rejected.count()), (0,1))

    def test_history_fixture_and_identical_duplicate(self):
        rows = records("appointment_history.csv")
        result = prepare_history(self.history(rows + [rows[0]]))
        self.assertEqual(result.count(), 40)
        self.assertEqual(dict(result.dtypes)["lead_days"], "double")

    def test_bad_or_future_history_is_not_hidden_by_deduplication(self):
        original = records("appointment_history.csv")[0]
        invalid_values = {"patient_id":[None, "   ", "\t"], "visit_id":[None, ""],
                          "visit_date":[None, "bad", "2026-02-01", "2026-02-15"],
                          "lead_days":[None, "bad", "-1", "NaN", "Infinity", "-Infinity"],
                          "attended":[None, "2", "bad"]}
        for field, values in invalid_values.items():
            for value in values:
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    prepare_history(self.history([original, {**original, field:value}]))

    def test_conflicting_valid_history_in_either_input_order(self):
        original = records("appointment_history.csv")[0]
        conflict = {**original, "lead_days":"999"}
        for rows in [[original, conflict], [conflict, original]]:
            with self.assertRaises(ValueError):
                prepare_history(self.history(rows))

    def test_outcome_timing_keys_and_values(self):
        rows = records("attendance_outcomes.csv")
        self.assertEqual(prepare_outcomes(self.outcomes(rows)).count(), 20)
        variants = [rows + [rows[0]],
                    [{**rows[0], "observed_date":"2026-02-15"}] + rows[1:],
                    [{**rows[0], "scheduled_date":"2026-01-20"}] + rows[1:],
                    [{**rows[0], "no_show":"2"}] + rows[1:],
                    [{**rows[0], "facility_id":"FAC99"}] + rows[1:]]
        for variant in variants:
            with self.assertRaises(ValueError):
                prepare_outcomes(self.outcomes(variant))

    def test_cohort_mismatch_fails_before_feature_join(self):
        history = prepare_history(self.history(records("appointment_history.csv")))
        outcomes = prepare_outcomes(self.outcomes(records("attendance_outcomes.csv")[:-1]))
        with self.assertRaises(ValueError):
            check_cohort(history, outcomes)

    def test_spark_features_match_the_offline_contract(self):
        history = prepare_history(self.history(records("appointment_history.csv")))
        outcomes = prepare_outcomes(self.outcomes(records("attendance_outcomes.csv")))
        check_cohort(history, outcomes)
        features = history.groupBy("patient_id").agg(
            F.count("*").alias("prior_visits"),
            F.sum(1-F.col("attended")).alias("prior_missed_visits"),
            F.avg("lead_days").alias("avg_lead_days"),
        ).join(outcomes.select("patient_id", "no_show"), "patient_id")
        actual = sorted([r.asDict() for r in features.collect()], key=lambda r:r["patient_id"])
        self.assertEqual(actual, training_rows())

    def test_incremental_source_collapses_identical_versions_and_selects_latest(self):
        raw = self.frame(records("appointment_updates.csv"), UPDATE_SCHEMA)
        prepared = prepare_updates(raw)
        self.assertEqual(prepared.count(), 3)
        latest = {r.appointment_id:r for r in latest_updates(prepared).collect()}
        self.assertEqual(set(latest), {"A001", "A007"})
        self.assertEqual((latest["A001"].facility_id, latest["A001"].source_version), ("FAC02",2))

    def test_incremental_conflicts_and_bad_versions_fail(self):
        original = records("appointment_updates.csv")[0]
        for change in [{"source_version":"0"}, {"source_version":"bad"},
                       {"source_version":"2147483648"}, {"patient_id":""}]:
            with self.assertRaises(ValueError):
                prepare_updates(self.frame([{**original, **change}], UPDATE_SCHEMA))
        with self.assertRaises(ValueError):
            prepare_updates(self.frame(
                [original, {**original, "facility_id":"FAC03"}], UPDATE_SCHEMA))

    def test_equal_version_cannot_change_target_payload(self):
        original = records("appointments.csv")[0]
        _, target, _ = prepare_appointments(self.appointments([original]))
        target = target.withColumn("source_version", F.lit(1))
        good = prepare_updates(self.frame(
            [{**original, "source_version":"1"}], UPDATE_SCHEMA))
        validate_target(target, good)
        conflict = prepare_updates(self.frame(
            [{**original, "source_version":"1", "facility_id":"FAC02"}], UPDATE_SCHEMA))
        with self.assertRaises(ValueError):
            validate_target(target, conflict)

    def test_nested_bundle_mapping_matches_the_csv_contract(self):
        payload = (DATA_ROOT / "sample-data" / "appointments_bundle.json").read_text(encoding="utf-8")
        mapped = extract_appointments(self.frame([{"payload":payload}], "payload STRING"))
        valid, clean, rejected = prepare_appointments(mapped)
        self.assertEqual((mapped.count(), valid.count(), clean.count(), rejected.count()), (6,4,3,2))
        _, expected, _ = prepare_appointments(self.appointments(records("appointments.csv")))
        self.assertEqual(clean.join(expected, clean.columns, "left_anti").count(), 0)
        self.assertEqual(expected.join(clean, clean.columns, "left_anti").count(), 0)

    def test_bundle_shape_and_ambiguous_references_fail(self):
        original = json.loads((DATA_ROOT / "sample-data" / "appointments_bundle.json").read_text(encoding="utf-8"))
        ambiguous = json.loads(json.dumps(original))
        ambiguous["entry"][0]["resource"]["participant"].append({
            "actor":{"reference":"Patient/P020"}, "status":"accepted"})
        for payload in ["not JSON", '{"resourceType":"Patient"}', json.dumps(ambiguous)]:
            with self.assertRaises(ValueError):
                extract_appointments(self.frame([{"payload":payload}], "payload STRING"))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SparkQualityChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError("Spark quality checks failed")
