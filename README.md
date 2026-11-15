# Databricks on AWS

Companion examples for **Databricks on AWS: From Raw Data to Governed AI and
Intelligent Agents** by **Vishnu VG**.

Build and run apps, agents and AI on your data.

Repository: https://github.com/codingtalkswithvishnu/databricks-on-aws

The book's commercial product URL has not been supplied. This repository contains
examples and supporting instructions; it does not contain the manuscript, cover,
EPUB, private reviews or credentials.

Start at [00-start-here/README.md](00-start-here/README.md).
Use a separate practice copy so reference updates do not overwrite your work.
All data is synthetic and all example table resets require a disposable namespace.

## Two execution boundaries

1. **Local:** Python 3.10 or newer; the fixtures, assistant and bounded agent use
   the standard library and require no cloud credentials. The actual checked
   runtime and outcomes appear in [VALIDATION.md](VALIDATION.md).
2. **Databricks/AWS:** administrator-approved analytics catalog, schema/table
   creation privileges, compatible compute and required packages. Spark, MLflow,
   bundle deployment, S3/Kinesis, search and live model calls need their own
   authenticated checks. No successful live-cloud run is implied by local tests.

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
| 16 | 04-assistant/assistant.py | Extractive local answer; optional paid live generation. |
| 17 | 06-integrations/README.md | Optional provider comparison. |
| 18–19 | tools/check_local.py and earlier checkpoints | Evidence scorecard and capstone. |
| 20–21 | 06-integrations/README.md | Optional ownership/data-product decisions. |
| 22 | 05-agent/agent.py | One bounded read-only tool request. |
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

