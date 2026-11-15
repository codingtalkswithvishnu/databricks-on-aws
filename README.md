# Databricks on AWS

Companion examples for **Databricks on AWS: From Raw Data to Governed AI and
Intelligent Agents** by **Vishnu VG**.

Build and run apps, agents and AI on your data.

Repository: https://github.com/codingtalkswithvishnu/databricks-on-aws

This repository contains examples and supporting instructions. The manuscript,
cover, EPUB, private reviews and credentials remain outside it.

Start at [00-start-here/README.md](00-start-here/README.md).
Use a separate practice copy so reference updates do not overwrite your work.
All data is synthetic and all example table resets require a disposable namespace.

## Choose an execution route

1. **Local:** Python 3.10 or newer; the fixtures, assistant and bounded agent use
   the standard library and require no cloud credentials. The actual checked
   runtime and outcomes appear in [VALIDATION.md](VALIDATION.md).
2. **Databricks fixtures:** approved analytics catalog, schema/table privileges,
   compatible compute and required packages. Synthetic inputs remove the need
   for customer-owned S3 access; Spark and MLflow still execute in Databricks.
3. **AWS/live AI extensions:** configured AWS identities, storage/connector paths,
   search or model endpoints and usage controls. These have separate signed-in
   checks; local success does not establish them.

## Chapter map

| Chapters | Folder/file | Output |
| --- | --- | --- |
| 1–3 | 00-start-here and sample-data | Brief, fixture contract, environment and compute check. |
| 4 | 01-lakehouse/01_ingest.py | Bronze inputs plus ticket/document fixtures. |
| 5 | 01-lakehouse/02_clean.py | Three valid signups and forty typed orders. |
| 6–7 | 02-analytics/03_report.py | Stable view and GB/IN/US counts of one each. |
| 8 | 06-integrations/README.md, events.jsonl | Optional isolated-stream evidence plan. |
| 9 | 03-prediction/04_train_score.py | Twenty feature rows, 16/4 split and actual scored table. |
| 10–12 | 06-integrations/README.md | Identity, network and catalog review records. |
| 13 | databricks.yml | Ingest → clean → report job definition. |
| 14–15 | 06-integrations/README.md, tickets.csv | Endpoint and classification/Genie checks. |
| 16 | 04-assistant/assistant.py and 05-agent/agent.py | Cited answer and one bounded read-only tool request; optional live model modes. |
| 17 | 06-integrations/README.md | Optional provider comparison. |
| 18–19 | tools/check_local.py and earlier checkpoints | Evidence scorecard and capstone. |
| 20–21 | 06-integrations/README.md | Optional ownership/data-product decisions. |
| 22 | 05-agent/agent.py and tools/check_local.py | Revisit the Chapter 16 agent's argument validation, refusals and enterprise access requirements. |
| 23–24 | 06-integrations/README.md | Source qualification and incident evidence template. |

## Run locally

From this repository root:

~~~shell
python tools/check_local.py
python 04-assistant/assistant.py --question "What is the return window?"
python 05-agent/agent.py --question "How many valid signups are there?"
~~~

The assistant defaults to lexical retrieval and an extractive answer, not an LLM.
The agent defaults to a simulated plan, not a model's reasoning. --live explicitly
requests a model and can incur charges; read the folder README first.

Cloud notebooks use Databricks source-notebook format. Import/open the complete
project; %run paths and shared module/fixture files must stay together. Plain
Python execution of those notebooks is not a local Spark validation.

Chapter 5's notebook uses shared/spark_clean.py. It rejects conflicting duplicate
keys instead of choosing an arbitrary winner and checks every order before
deduplication. Blank keys, invalid dates/labels and nonfinite or negative amounts
fail the order contract. Both datasets pass preflight before either table is
written; the two writes are separate Delta commits, not one atomic transaction.

With compatible Spark, run `python tools/check_spark.py`, or open the complete
project in Databricks and run `%run ../tools/check_spark` from a numbered notebook
folder. These checks exercise the actual cleaning functions with synthetic
DataFrames and create no tables. Their execution status is in VALIDATION.md.

