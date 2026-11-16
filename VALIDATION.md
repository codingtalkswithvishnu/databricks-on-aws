# Healthcare companion validation - 16 November 2026

## Observed local results

- **35 standard-library tests passed**, CPython 3.14.10, Windows,
  `python -W error tools/check_local.py`. Includes strict fixture headers/record
  widths/quoting, exact accepted rows, notebook-root selection/failure, structured
  CLI source errors, data/time/cohort contracts, policy versions, bounded tools,
  fake model/HTTP failures, redirects, response adapters and Python syntax.
- **15 actual Spark DataFrame tests passed**, CPython 3.12.10, PySpark 4.0.1,
  Py4J 0.10.9.9, Java 21.0.13, Windows local[2], two shuffle partitions, UI disabled.
  `python tools/check_spark.py`; 95.626 seconds. Includes the new invalid-target
  field/canonical-key/version guard before MERGE, plus source conflicts,
  rejections, dated feature agreement, cohort and limited nested mapping.
- **Actual model code passed locally** with Spark 4.0.1/MLflow 3.5.1: twenty
  features, 16/4 fitting/evaluation, three scores, one review-queue row, completed
  file-backed MLflow metric/parameter logging. Missing scoring features and
  duplicate feature keys stopped before publication. This Windows harness used
  literal DataFrames and temporary views in place of exactly three Delta writes;
  it establishes model execution, not table persistence. Observed fixture AUC
  was 1.0; four constructed holdout records establish no predictive quality.
- **A native Windows Delta write probe failed** because the Hadoop Windows
  tools were unavailable (`HADOOP_HOME`/`hadoop.home.dir` unset). This is an
  observed environment failure, not a successful Delta write or a defect hidden
  by weakening the acceptance rules.

The new CSV regressions first reproduced seven silently accepted structural
errors, then passed after the loader fix. Source-file exceptions in CLI tests
are injected; HTTP/model tests use fakes and make no paid requests. Spark fixture
construction uses literal JVM expressions, not a patched vendor implementation.

## Separate Linux pipeline verification

The GitHub workflow runs the standard-library suite on Python 3.10 and 3.14.
Its separate Python 3.12/Java 21 job installs tools/requirements-pipeline.txt,
runs the Spark suite, then tools/check_pipeline.py. Consult the actual
[Actions run](https://github.com/codingtalkswithvishnu/databricks-on-aws/actions)
and uploaded pipeline-check-results artifact for its observed outcome; a
workflow definition alone is not a pass.

The pipeline verifier executes the source notebooks with real local Delta
writes/history/MERGE, Spark ML and local MLflow metrics. It maps analytics schemas
to temporary book_* databases in Spark's single local catalog. Each core job
stage has a fresh namespace; notebook %run shares the calling namespace. It
checks nested mapping, update/insert/repeat/stale behavior, temporal dimension
SQL, landed-event parsing and failure guards before publication. Kinesis input
is represented by literal landed payloads; the verifier does not connect to it.

## Contracts and unverified boundaries

6 appointment arrivals = 2 rejected + 1 identical repeat + 3 accepted.
FAC01/FAC02/FAC03 each count 1. History contains 40 prior visits and labels cover
20 patients. Features precede 1 February; outcomes are scheduled/observed on
15/16 February; the held-out split is 16/4. March scores retain appointment keys,
cutoff and actual run reference. A missing/duplicate feature match blocks scoring.

The isolated update target should end with four keys, newer A001/FAC02/v2 and
added A007/v1, preserving state on repeat/stale input. Versions are positive
signed 32-bit integers; the target must satisfy the same appointment contract.
The limited nested mapper compares both directions against CSV before publishing
its accepted/rejection demo outputs. Neither extension changes the baseline.

No signed-in Databricks/AWS authentication, Unity Catalog authorization, actual
S3/Kinesis/Redshift connection, bundle deployment/run, managed search, Genie,
AI Function, paid model request, registered model/feature store/AutoML, network
path, operational cost or resource-retirement behavior is established by the
credential-free checks. Local Delta is not Unity Catalog. Model metrics are not
artifact reload or registry validation. The synthetic healthcare fixture and
three policies are teaching contracts, not clinical or production validation.
