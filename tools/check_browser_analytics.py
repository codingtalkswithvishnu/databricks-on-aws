"""Run the actual browser SQL samples locally; no AWS/Databricks credentials.

Default: SQLite with catalog/schema qualifiers removed.
--spark: real local Spark SQL using the same samples and bound parameters.
"""
import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "07-browser-analytics"
sys.path.insert(0, str(ROOT / "shared"))
from healthcare import FACILITIES, clean_appointments, records


def statements(filename):
    text = (EXAMPLES / filename).read_text(encoding="utf-8")
    text = re.sub(r"^\s*--[^\n]*", "", text, flags=re.M)
    return [part.strip() for part in text.split(";") if part.strip()]


def local_sql(sql):
    return re.sub(r"analytics\.(?:learning_preview|gold)\.", "", sql)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spark", action="store_true")
    args = parser.parse_args()
    arrivals = records("appointments.csv")
    accepted, rejected, duplicates = clean_appointments(arrivals)
    assert (len(arrivals), len(accepted), len(rejected), duplicates) == (6, 3, 2, 1)
    lookup = [json.loads(line) for line in
              (EXAMPLES / "learning_facilities.json").read_text().splitlines() if line.strip()]
    assert sorted(row["facility_id"] for row in lookup) == list(FACILITIES)
    assert all(set(row) == {"facility_id", "facility_label"} and
               isinstance(row["facility_label"], str) and row["facility_label"].strip()
               for row in lookup)
    counts = [(key, sum(row["facility_id"] == key for row in accepted)) for key in FACILITIES]
    assert counts == [("FAC01", 1), ("FAC02", 1), ("FAC03", 1)]
    spark = None
    connection = None
    try:
        if args.spark:
            from pyspark.sql import SparkSession
            spark = (SparkSession.builder.master("local[2]").appName("Northstar browser SQL")
                     .config("spark.ui.enabled", "false")
                     .config("spark.sql.shuffle.partitions", "2").getOrCreate())
            spark.sparkContext.setLogLevel("ERROR")
            spark.createDataFrame(arrivals,
                "appointment_id STRING,patient_id STRING,scheduled_date STRING,facility_id STRING"
            ).createOrReplaceTempView("appointments_upload")
            spark.createDataFrame(lookup, "facility_id STRING,facility_label STRING"
            ).createOrReplaceTempView("facilities_upload")
            spark.createDataFrame(counts, "facility_id STRING,appointments LONG"
            ).createOrReplaceTempView("appointments_by_facility")

            def run(sql, parameters=None):
                return [tuple(row) for row in spark.sql(local_sql(sql), args=parameters or {}).collect()]
        else:
            connection = sqlite3.connect(":memory:")
            connection.execute("CREATE TABLE appointments_upload "
                "(appointment_id TEXT,patient_id TEXT,scheduled_date TEXT,facility_id TEXT)")
            connection.executemany("INSERT INTO appointments_upload VALUES "
                "(:appointment_id,:patient_id,:scheduled_date,:facility_id)", arrivals)
            connection.execute("CREATE TABLE facilities_upload (facility_id TEXT,facility_label TEXT)")
            connection.executemany("INSERT INTO facilities_upload VALUES (:facility_id,:facility_label)", lookup)
            connection.execute("CREATE TABLE appointments_by_facility (facility_id TEXT,appointments INTEGER)")
            connection.executemany("INSERT INTO appointments_by_facility VALUES (?,?)", counts)

            def run(sql, parameters=None):
                return connection.execute(local_sql(sql), parameters or {}).fetchall()

        checks = []
        if args.spark:
            notebook = (EXAMPLES / "00_notebook_readiness.py").read_text(encoding="utf-8")
            producer, consumer = notebook.split("# MAGIC %sql\n", 1)
            exec(compile(producer, "00_notebook_readiness.py", "exec"), {"spark": spark})
            sql = "\n".join(line.removeprefix("# MAGIC ") for line in consumer.splitlines())
            assert [tuple(row) for row in spark.sql(sql).collect()] == [(3,)]
            checks.append("actual notebook DataFrame producer and SQL temporary-view consumer")
        upload = statements("01_inspect_uploads.sql")
        assert len(upload) == 3
        assert run(upload[0]) == [(6,)]
        assert run(upload[1]) == [(key, 1) for key in FACILITIES]
        assert [row[2] for row in run(upload[2])] == [3, 2, 1]
        checks.append("raw arrival count, unique lookup keys, and 3/2/1 joined arrivals")
        report = statements("02_reference_report.sql")
        assert run(report[0]) == counts
        assert run(report[1]) == [(3, 3)]
        checks.append("aggregate 1/1/1, three represented facilities, three accepted appointments")
        parameter = statements("03_facility_parameter.sql")[0]
        for value, expected in [("ALL", counts), ("FAC02", [("FAC02", 1)]),
                                ("FAC99", []), ("FAC02' OR 1=1 --", [])]:
            assert run(parameter, {"facility": value}) == expected
        checks.append("bound parameters: ALL, one facility, absent code, SQL-shaped literal")
        assert run(statements("04_sum_vs_count.sql")[0]) == [(3, 4)]
        checks.append("isolated COUNT-versus-SUM counterexample without persisted writes")
        genie = statements("05_genie_examples.sql")
        assert run(genie[0]) == [(3,)] and run(genie[1]) == [("FAC02", 1)]
        checks.append("Genie reference SQL agrees with the manual aggregate")
        try:
            run(statements("negative_column_error.sql")[0])
        except Exception as error:
            text = str(error).lower()
            assert "no such column" in text or "unresolved_column" in text, text
        else:
            raise AssertionError("Intentional missing-column query unexpectedly succeeded")
        checks.append("expected missing-column failure; corrected measure query already passed")
        assert run(report[0]) == counts
        checks.append("hypothetical and negative exercises leave the canonical report unchanged")
        print(json.dumps({"engine": "local-spark" if args.spark else "sqlite",
            "checks": checks, "passed": len(checks),
            "boundary": "No Databricks UI, Unity Catalog authorization, live AI, or AWS execution"}, indent=2))
    finally:
        if connection is not None:
            connection.close()
        if spark is not None:
            spark.stop()


if __name__ == "__main__":
    main()
