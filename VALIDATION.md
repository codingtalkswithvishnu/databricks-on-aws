# Healthcare companion validation — 16 November 2026

## Observed local results

- **31 standard-library checks passed**, CPython 3.14.10, Windows, command
  `python -W error tools/check_local.py`. Covers fixture reconciliation, conflicts,
  date/cohort boundaries, policy versions, source retention, agent dispatch,
  fake-model/HTTP error handling, redirects, bounded response parsing, Genie/search
  response adapters and parsing every repository Python source.
- **14 actual Spark DataFrame checks passed**, CPython 3.12.10, PySpark 4.0.1,
  Py4J 0.10.9.9, Java 21.0.13 on Windows; local[2], 2 shuffle partitions, UI disabled.
  Command `python tools/check_spark.py`. Runtime 89.458 seconds in the final run.
  Covers cleaning/rejections/conflicts, historical values and timing, label/cohort
  contracts, Spark/offline feature agreement, versioned-update preparation/target
  conflicts, and nested healthcare mapping/ambiguity.

Spark fixtures are literal JVM DataFrames created through Spark SQL functions.
They exercise actual transformations; they avoid Python RDD worker dependencies
in this Windows embedded-Python setup. No vendor package was patched. This local
Spark version is the observed test environment, not a selected Databricks Runtime.

The GitHub workflow separately runs the local suite on Python 3.10 and 3.14 on
Ubuntu. Its actual run status is visible in GitHub Actions; this document does not
infer success from the workflow definition.

## Expected contracts

6 appointment arrivals = 2 rejected + 1 identical valid duplicate + 3 accepted.
FAC01/FAC02/FAC03 each count 1. History has 40 prior visits; later labels cover
20 patients. Features precede 1 February; outcomes are scheduled/observed on
15/16 February; the held-out patient split is 16/4. The model notebook must score
3 accepted March appointments and retain cutoff/run reference. No model score or
AUC was produced by the local checks.

The isolated MERGE demo should finish with 4 keys, newer A001/FAC02/v2 and added
A007/v1, and preserve state on repeat/stale input. Only preparation/target checks
were executed locally, not the Delta MERGE. The nested mapper reproduces the
accepted CSV rows; its Delta writes were not executed.

## Not executed

No signed-in Databricks/AWS authentication, actual S3 read, UC access test, Delta
table write/MERGE/history operation, Spark ML fit, MLflow server/artifact/model
registry call, feature-store/AutoML call, CLI bundle validate/deploy/run, paid model
request, AI Function, managed search synchronization, Genie query, Redshift/Kinesis
connection, network-path validation, actual cost measurement or resource retirement
was performed. Standard-library model/HTTP checks use fakes; Genie/search checks
exercise pure response adapters, not their services.

The bundle's ingest → clean → report → predict tasks are a reviewed definition.
The optional cloud notebooks need configured owners, resources, package versions
and actual result checks. The 20-patient synthetic fixture, three policies and
three tickets establish teaching contracts, not clinical or production quality.
