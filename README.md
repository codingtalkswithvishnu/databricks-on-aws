# Databricks on AWS

Companion examples for **Databricks on AWS: From Raw Data to Governed AI and
Intelligent Agents** by **Vishnu VG**. Build and run apps, agents and AI on your data.

The enterprise example follows **Northstar Health Network**, a fictional
multi-facility outpatient provider. All records and policies are invented.
The project concerns appointment operations and administrative support.

Start at [00-start-here](00-start-here/README.md). Preserve the complete project
and use a separate practice branch at the revision pinned in your book.
The manuscript, cover, EPUB, private reviews and credentials are outside this repository.

## Follow the main pipeline

| Chapters | Reference | Accepted result |
| --- | --- | --- |
| 1–3 | 00-start-here, sample-data | Requirements, explicit schemas, dates and approved environment. |
| 4 | 01-lakehouse/01_ingest.py | 6 raw appointments, 40 historical visits, 20 later outcomes; 3 tickets and 3 selected policies. |
| 5 | 01-lakehouse/02_clean.py | 3 accepted appointments, 2 rejected arrivals, 1 identical duplicate; typed history/outcomes. |
| 6–7 | 02-analytics/03_report.py | Stable operations.appointments view and FAC01/FAC02/FAC03 counts of 1 each. |
| 8 | 06-integrations/README.md, events.jsonl | Optional isolated three-event Kinesis exercise. |
| 9 | 03-prediction/04_train_score.py | 20 dated feature/label rows, 16/4 split, observed metric/run reference, 3 March scores and human review queue. |
| 10–12 | 06-integrations/README.md | Identity, network, storage and object-access evidence. |
| 13 | databricks.yml, .github/workflows/local-checks.yml | Four-task ingest → clean → report → predict job and separate local CI. |
| 14–15 | 06-integrations/05_classify_tickets.py, 02_genie_conversation.py | Optional materialized classification and aggregate-only Genie conversation. |
| 16 | 04-assistant, 05-agent, 06-integrations/03_managed_policy_search.py | Versioned policy evidence, bounded read tools, optional managed retrieval. |
| 17 | 06-integrations/04_compare_providers.py | Same fixed cases through two explicitly selected compatible model endpoints. |
| 18–19 | Earlier stages, tools/check_local.py, tools/check_spark.py | Evidence scorecard and reproducible healthcare capstone. |
| 20–24 | 06-integrations/README.md, 05-agent | Ownership, products, agent limits, qualified case studies and recovery evidence. |
| Appendix D | 01-lakehouse/03_incremental_updates.py, 04_fhir_mapping.py | Separate versioned-MERGE and nested R4-shaped source demonstrations. |

All main table names belong to analytics. The gold facility report is a fixed
March snapshot with two columns, not an appendable multi-period time series.
Patient-level scores have a different access contract from facility aggregates.

## Run the local route

Python 3.10+; standard library only for these commands, from the repository root:

```shell
python -W error tools/check_local.py
python 04-assistant/assistant.py --question "How much notice is needed for appointment rescheduling?"
python 04-assistant/assistant.py --question "What is the parking fee?"
python 05-agent/agent.py --question "How many accepted appointments are there by facility?"
python 05-agent/agent.py --question "Cancel the patient appointment"
```

The assistant defaults to lexical retrieval and an extractive answer. The agent
defaults to a simulated plan. `--live` replaces generation/planning with a model
request and can incur charges; its tools still use local fixtures. Read the folder
instructions before selecting that route. There is no patient lookup, contact,
appointment-write tool or clinical model in this application.

## Run the Spark and cloud routes separately

With compatible PySpark and Java, `python tools/check_spark.py` exercises actual
DataFrame transformations without table writes. See [VALIDATION.md](VALIDATION.md)
for the checked local runtimes and 31 local / 14 Spark results.

Cloud source notebooks require an approved disposable analytics catalog,
schema/table privileges, compatible Spark ML/MLflow compute and the complete
project. Open/import the project together; `%run` and shared module paths matter.
The four-task bundle uses an explicit approved existing cluster. From a signed-in
CLI environment, validate, deploy and run with your approved cluster variable;
the book explains each evidence boundary.

Quality preflight checks all inputs before the four output writes. Those writes
are separate Delta commits. A partial failure needs reconciliation rather than
an assumption of one transaction. Full fixture resets overwrite only the agreed
disposable tables; they are not an operational incremental ingestion strategy.

Optional model lifecycle, feature-table and AutoML recipes are in 03-prediction/
05–07. Optional integrations have separate prerequisites and are excluded from
the default job. No signed-in Databricks/AWS execution is claimed here.
