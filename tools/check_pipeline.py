"""Execute reviewed checkpoints with real local Delta/Spark ML and MLflow.

Use a supported Linux/Java environment and requirements-pipeline.txt. The only
source adaptation maps analytics.<schema> to isolated book_<schema> databases
in Spark's local catalog. Notebook %run shares its caller's namespace; separate
job stages use fresh namespaces. No AWS, Unity Catalog, model endpoint or paid
service is contacted. Delta Maven artifacts are resolved at startup.
"""
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'shared')]
os.environ['DATABRICKS_BOOK_ROOT'] = str(ROOT)
os.environ['MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING'] = 'false'
from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession, functions as F
import mlflow

ALLOWED = {'00-start-here/00_setup.py', '01-lakehouse/01_ingest.py',
           '01-lakehouse/02_clean.py', '02-analytics/03_report.py',
           '03-prediction/04_train_score.py', '01-lakehouse/03_incremental_updates.py',
           '01-lakehouse/04_fhir_mapping.py'}

def local_code(source):
    return source.replace('analytics.', 'book_')

def execute(path, namespace):
    path = path.resolve()
    relative = path.relative_to(ROOT).as_posix()
    assert relative in ALLOWED, relative
    namespace['__file__'] = str(path)
    source = path.read_text(encoding='utf-8')
    pending = []
    for line in source.splitlines():
        match = re.fullmatch(r'# MAGIC %run (.+)', line)
        if match:
            exec(compile(local_code('\n'.join(pending)), relative, 'exec'), namespace)
            pending = []
            target = (path.parent / match[1]).with_suffix('.py')
            execute(target, namespace)
        else:
            pending.append(line)
    exec(compile(local_code('\n'.join(pending)), relative, 'exec'), namespace)

def expect_failure(operation, exception, label):
    try:
        operation()
    except exception:
        return label
    raise AssertionError('Expected failure was not observed: ' + label)

def main():
    started = time.monotonic()
    prior_directory = Path.cwd()
    report_path = prior_directory / 'pipeline-check-results.json'
    with tempfile.TemporaryDirectory(prefix='northstar-pipeline-') as directory:
        work = Path(directory).resolve()
        assert work.is_relative_to(Path(tempfile.gettempdir()).resolve())
        os.chdir(work)
        spark = None
        try:
            mlflow.set_tracking_uri((work / 'mlruns').as_uri())
            mlflow.set_registry_uri((work / 'mlruns').as_uri())
            builder = (SparkSession.builder.master('local[2]').appName('northstar-checkpoints')
                .config('spark.ui.enabled', 'false').config('spark.sql.shuffle.partitions', '2')
                .config('spark.databricks.delta.snapshotPartitions', '2')
                .config('spark.sql.warehouse.dir', (work / 'warehouse').as_uri())
                .config('spark.jars.repositories', 'https://repo.maven.apache.org/maven2')
                .config('spark.sql.extensions', 'io.delta.sql.DeltaSparkSessionExtension')
                .config('spark.sql.catalog.spark_catalog', 'org.apache.spark.sql.delta.catalog.DeltaCatalog'))
            spark = configure_spark_with_delta_pip(builder).getOrCreate()
            spark.sparkContext.setLogLevel('ERROR')
            stages = []
            prediction = None
            for path in ['01-lakehouse/01_ingest.py', '01-lakehouse/02_clean.py',
                         '02-analytics/03_report.py', '03-prediction/04_train_score.py']:
                namespace = {'spark': spark, '__name__': '__checkpoint__'}
                execute(ROOT / path, namespace)
                stages.append(path)
                if path.startswith('03-prediction'):
                    prediction = namespace

            # A retained actual Delta version reproduces the raw fixture.
            raw_table = 'book_bronze.appointments'
            version = spark.sql('DESCRIBE HISTORY ' + raw_table).first().version
            assert spark.sql(f'SELECT COUNT(*) AS n FROM {raw_table} VERSION AS OF {version}').first().n == 6
            raw = spark.table(raw_table)
            raw_rows, raw_schema = raw.collect(), raw.schema
            accepted_version = spark.sql('DESCRIBE HISTORY book_silver.appointments').first().version
            original_appointment = next(row for row in raw_rows if row.appointment_id == 'A001')
            conflict = spark.createDataFrame([original_appointment], raw_schema).withColumn('facility_id', F.lit('FAC02'))
            raw.unionByName(conflict).write.format('delta').mode('overwrite').saveAsTable('book_bronze.conflicting_source_demo')
            # Point this isolated source at the reviewed cleaning notebook without
            # changing its rules or overwriting the accepted source fixture.
            clean_source = (ROOT / '01-lakehouse/02_clean.py').read_text(encoding='utf-8')
            clean_source = local_code(clean_source).replace('book_bronze.appointments', 'book_bronze.conflicting_source_demo')
            failures = [expect_failure(lambda: exec(compile(clean_source, 'conflicting-source-check', 'exec'), {'spark': spark}),
                                       ValueError, 'conflicting accepted source stops before publication')]
            assert spark.sql('DESCRIBE HISTORY book_silver.appointments').first().version == accepted_version

            scores = spark.table('book_gold.appointment_scores').collect()
            assert len(scores) == 3 and {r.appointment_id for r in scores} == {'A001', 'A002', 'A006'}
            assert all(0 <= r.missed_appointment_probability <= 1 for r in scores)
            run = mlflow.get_run(prediction['model_run_id'])
            assert run.info.status == 'FINISHED'
            assert run.data.metrics['fixture_test_auc'] == prediction['auc']
            assert run.data.params['predictor_order'] == 'prior_visits,prior_missed_visits,avg_lead_days'
            queue_count = spark.table('book_gold.outreach_review_queue').count()
            assert 0 <= queue_count <= 3
            scoring = local_code((ROOT / '03-prediction/04_train_score.py').read_text(encoding='utf-8').split('# COMMAND ----------')[2])
            score_version = spark.sql('DESCRIBE HISTORY book_gold.appointment_scores').first().version
            spark.sql('''CREATE OR REPLACE VIEW book_operations.appointments AS
                SELECT appointment_id,
                       CASE WHEN appointment_id = 'A006' THEN 'P999' ELSE patient_id END AS patient_id,
                       scheduled_date, facility_id FROM book_silver.appointments''')
            failures.append(expect_failure(lambda: exec(compile(scoring, 'missing-feature-check', 'exec'), prediction),
                                           AssertionError, 'missing predictor stops score publication'))
            execute(ROOT / '02-analytics/03_report.py', {'spark': spark})
            feature_table = 'book_ml.appointment_features'
            features = spark.table(feature_table)
            rows, schema = features.collect(), features.schema
            spark.createDataFrame(rows + [next(r for r in rows if r.patient_id == 'P001')], schema).write.format('delta').mode('overwrite').saveAsTable(feature_table)
            failures.append(expect_failure(lambda: exec(compile(scoring, 'duplicate-feature-check', 'exec'), prediction),
                                           AssertionError, 'duplicate predictor stops score publication'))
            assert spark.sql('DESCRIBE HISTORY book_gold.appointment_scores').first().version == score_version
            spark.createDataFrame(rows, schema).write.format('delta').mode('overwrite').saveAsTable(feature_table)

            # Execute isolated update/insert/repeat/stale and nested-source demos.
            execute(ROOT / '01-lakehouse/03_incremental_updates.py', {'spark': spark})
            execute(ROOT / '01-lakehouse/04_fhir_mapping.py', {'spark': spark})
            assert spark.table('book_silver.appointments_incremental_demo').count() == 4
            assert spark.table('book_silver.fhir_appointments_demo').count() == 3
            assert spark.table('book_silver.appointments').count() == 3

            dimension_sql = (ROOT / '02-analytics/04_dimension_history.sql').read_text(encoding='utf-8')
            expected = {'A001': ('East', 1), 'A002': ('South', 1), 'A006': ('West', 1)}
            dimensions = spark.sql(dimension_sql).collect()
            assert {r.appointment_id: (r.region, r.dimension_matches) for r in dimensions} == expected
            earlier = spark.sql(dimension_sql.replace("('A002', 'FAC02', DATE '2026-03-10')", "('A002', 'FAC02', DATE '2026-02-15')")).collect()
            assert next(r for r in earlier if r.appointment_id == 'A002').region == 'North'
            missing = spark.sql(dimension_sql.replace("(30, 'FAC03',", "(30, 'MISSING',")).collect()
            assert next(r for r in missing if r.appointment_id == 'A006').dimension_matches == 0
            overlap = spark.sql(dimension_sql.replace("'North', DATE '2020-01-01', DATE '2026-03-01'", "'North', DATE '2020-01-01', DATE '2026-04-01'")).collect()
            assert len(overlap) == 4 and sum(r.dimension_matches == 2 for r in overlap) == 2

            # Check the landed-payload parsing/aggregate stage, not Kinesis access.
            events = [json.loads(line) for line in (ROOT / 'sample-data/events.jsonl').read_text(encoding='utf-8').splitlines()]
            event_table = 'book_bronze.appointment_events'
            def publish_payloads(messages):
                spark.createDataFrame([(json.dumps(row).encode(),) for row in messages], 'data BINARY').write.format('delta').mode('overwrite').saveAsTable(event_table)
            event_code = local_code((ROOT / '06-integrations/06_checkin_events.py').read_text(encoding='utf-8').split('# COMMAND ----------')[1])
            publish_payloads(events)
            exec(compile(event_code, 'landed-event-stage', 'exec'), {'spark': spark})
            event_version = spark.sql('DESCRIBE HISTORY book_gold.check_in_counts').first().version
            publish_payloads([{**events[0], 'event_time': 'bad-timestamp'}] + events[1:])
            failures.append(expect_failure(lambda: exec(compile(event_code, 'bad-event-time-check', 'exec'), {'spark': spark}),
                                           AssertionError, 'invalid event timestamp stops aggregate publication'))
            assert spark.sql('DESCRIBE HISTORY book_gold.check_in_counts').first().version == event_version

            report = {'status': 'passed', 'spark': spark.version, 'mlflow': mlflow.__version__,
                'java': spark._jvm.java.lang.System.getProperty('java.version'), 'python': sys.version.split()[0],
                'stages_executed': stages, 'source_count': 6, 'accepted_count': 3, 'rejections': 2,
                'features': 20, 'train': 16, 'heldout': 4, 'scores': 3, 'queue': queue_count,
                'observed_fixture_auc': prediction['auc'], 'delta_history_version_read': version,
                'incremental_update_repeat_stale': 'passed', 'nested_source_comparison': 'passed',
                'dimensional_lookup_cases': 4, 'landed_event_stage': 'passed', 'failure_guards': failures,
                'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(ALLOWED)},
                'elapsed_seconds': round(time.monotonic() - started, 3),
                'scope': 'Actual local Delta writes/history/MERGE, Spark ML fit/evaluate/score and file-backed MLflow metrics. Isolated single-catalog namespace substitution; no UC authorization, Databricks job runtime, AWS/Kinesis/Redshift or paid model service validation.'}
            report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
            print(json.dumps(report, indent=2))
        except Exception as error:
            report_path.write_text(json.dumps({'status': 'failed', 'error_type': type(error).__name__,
                'error': str(error)[:3000], 'elapsed_seconds': round(time.monotonic() - started, 3)}, indent=2) + '\n', encoding='utf-8')
            raise
        finally:
            if spark is not None:
                spark.stop()
            os.chdir(prior_directory)

if __name__ == '__main__':
    main()
