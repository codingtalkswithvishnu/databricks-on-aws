# Companion validation record

Date: 16 November 2026.

- Local runtime: CPython 3.14.10, Windows.
- Command: python tools/check_local.py, from the companion root.
- Observed result: 10 tests passed.
- Checks: six-row signup contract and expected counts; conflicting duplicate refusal;
  order-key uniqueness and two-class 16/4 split; supported/unsupported policy questions;
  source-ID validation with a fake model; allowlisted agent tools; malformed,
  unknown and extra-argument plans; no model call when no source evidence exists;
  parsing of the supplied Python files.
- Default assistant mode: lexical retrieval plus an extractive answer.
- Default agent mode: simulated plan, then one read-only dispatch.
- Fake-model checks validate response/plan handling, not live model quality.
- Standard-library local code has no third-party package dependencies.

Not executed: Spark transformations, Spark ML fitting, MLflow runs, CLI bundle
validation/deployment, AWS access, Kinesis producer/consumer, live Databricks
model calls, Genie, AI Search, provider changes, and actual account permissions
or networking. These require the approved environment described in the book.
The runtime/access-mode and package versions for those checks remain to be selected
and recorded by the operator.

Repository: https://github.com/codingtalkswithvishnu/databricks-on-aws
The local source is prepared separately from the commercial book. Git publication
status is recorded by the author's final repository handoff.

