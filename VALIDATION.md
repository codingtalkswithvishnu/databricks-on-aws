# Companion validation record

Date: 16 November 2026.

- Local runtime: CPython 3.14.10, Windows.
- Command: python tools/check_local.py, from the companion root.
- Observed result: 17 tests passed, including a run with Python warnings treated as errors.
- Checks: six-row signup contract and expected counts; conflicting duplicate refusal;
  order-key uniqueness and two-class 16/4 split; supported/unsupported policy questions;
  source-ID validation with a fake model; allowlisted agent tools; malformed,
  unknown and extra-argument plans; no model call when no source evidence exists;
  parsing of the supplied Python files; read questions containing action words;
  duplicate-key, nested, oversized and nonstandard model JSON; approved-host and
  token validation; bounded HTTP request shape; redirect refusal; sanitized
  transport errors; malformed and oversized endpoint responses.
- Default assistant mode: lexical retrieval plus an extractive answer.
- Default agent mode: simulated plan, then one read-only dispatch.
- Fake-model checks validate response/plan handling, not live model quality.
- Standard-library local code has no third-party package dependencies.
- The HTTP checks use fake responses and TEST_ONLY credentials, with no live calls.
- Spark-specific regression suite: tools/check_spark.py, five test methods with
  invalid-value subcases. Added and syntax-checked, not executed in Spark here.
  It covers fixture outputs, identical/conflicting duplicates in both input
  orders, null/blank keys, bad dates/labels and NaN/infinite/negative amounts.
  It calls the same shared/spark_clean.py functions as the cleaning notebook.

Not executed: Spark transformations, Spark ML fitting, MLflow runs, CLI bundle
validation/deployment, AWS access, Kinesis producer/consumer, live Databricks
model calls, Genie, AI Search, provider changes, and actual account permissions
or networking. These require the approved environment described in the book.
The runtime/access-mode and package versions for those checks remain to be selected
and recorded by the operator.

Repository: https://github.com/codingtalkswithvishnu/databricks-on-aws
The local source is prepared separately from the commercial book. Git publication
status is recorded by the author's final repository handoff.

