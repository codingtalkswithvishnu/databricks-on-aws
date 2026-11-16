# Optional configured integrations and operating records

The default four-task pipeline needs none of the integrations below. These
source notebooks are reference exercises whose cloud operations have not been
executed as part of the local checks. Obtain the owner's approval for a concrete
workspace/resource configuration and record the selected versions and evidence.

## Exported exercises

| File | Prerequisites and checks |
| --- | --- |
| 01_publish_redshift.py | Approved compatible classic-compute Redshift connector; existing network/database/schema; secret scope northstar-learning/key redshift-demo-options containing url,user,password,aws_iam_role,tempdir,dbtable. Target exactly reporting.northstar_facility_demo. Starts from accepted facility gold, uses errorifexists, then reads back the 3 counts. Staging S3/KMS access, JDBC user and IAM role are separate. Never print the options. |
| 02_genie_conversation.py | Current Databricks SDK, approved Genie space over only the facility aggregate, DATABRICKS_GENIE_SPACE_ID, supported query compute and caller access. Uses bounded waits, retains conversation/message/query attachment IDs and fetches typed query results. Compare actual structured counts manually; natural-language text alone is insufficient. |
| 03_managed_policy_search.py | Current databricks-ai-search package with databricks.ai_search.client.AISearchClient; approved existing standard search endpoint and embedding endpoint in DATABRICKS_AI_SEARCH_ENDPOINT/DATABRICKS_EMBEDDING_ENDPOINT; CDF-enabled support.help_articles; required UC/service permissions and source support. Creates the new isolated analytics.support.northstar_policy_index_demo, synchronizes and waits. Existing-index conflict requires owner inspection; no automatic replacement. Checks current fixture metadata/body, P001 rank, then calls the bounded chat adapter using its separately configured process credentials. |
| 04_compare_providers.py | Local Python, common bounded chat credentials, and two distinct compatible serving endpoints in DATABRICKS_BASELINE_MODEL_ENDPOINT/DATABRICKS_CANDIDATE_MODEL_ENDPOINT. Five fixed questions per route; parking/clinical cases avoid calls. At most 6 adapter attempts overall. Prints observed latency/structure/source checks, returns failure on failed cases, and flags answers for content review. A passing structural result is not provider approval. |
| 05_classify_tickets.py | Approved AI Functions endpoint in DATABRICKS_MODEL_ENDPOINT, support.tickets and scoped rights. Materializes results once into separate support.ticket_classification_demo before read-back checks. Requires all 3 reference labels; reruns/retries can repeat paid requests. |

The Redshift classic options are not a claim that the newer serverless data-source
interface accepts the same configuration. A Unity AI Gateway model-provider
service name is also not a serving endpoint identifier. Configure the exact route
with its owner rather than substitute an unrelated model or object name.

## Pipeline extensions

- **S3:** preserve the declared appointment/history/outcome schemas; test permitted
  object reads and a known denied case with actual identities. Listing alone is
  insufficient. A local file read does not prove S3 access.
- **Auto Loader:** use an approved immutable source prefix, explicit appointment
  schema, separate analytics.bronze.appointments_incremental and a durable dedicated
  checkpoint. First/repeat fixture runs should remain at 6 raw arrivals under the
  declared file/progress contract. Business deduplication is a separate stage.
- **Kinesis:** a separate authorized producer sends the 3 events to the agreed
  isolated stream. Configure source authentication, earliest starting position
  for a fresh fixture checkpoint, AvailableNow and the documented connector route.
  Validate event IDs and appointment/facility associations, then the one-minute
  counts, one per facility. Do not point this replay exercise at an active stream.
- **Glue/federation:** choose the direction, supported formats and actual external
  catalog permissions; an ordinary UC table registration is not Glue integration.
- **Versioned updates:** 01-lakehouse/03_incremental_updates.py resets only its
  separate demo table. Highest accepted source_version wins; identical repeats
  collapse, conflicting ties fail, stale updates cannot roll back state. Expect
  4 final keys after A001 v2 and A007 v1, with no main baseline change.
- **Nested source:** 01-lakehouse/04_fhir_mapping.py preserves a single raw payload,
  maps 6 R4-shaped collection entries under explicit booked/UTC/relative-reference
  scope, and reproduces 3 accepted/2 rejected rows in separate demo tables. Compare
  both directions with the CSV baseline. This is not full FHIR validation.

## Optional prediction lifecycle

03-prediction/05_model_lifecycle.py explicitly reruns the core notebook, logs a
separate pipeline artifact with scalar-input signature, reloads and compares
predictions. Registration is off by default and needs an accepted UC model name
and privileges. 06_feature_contract.py creates a separate 20-row fixed-snapshot
feature table keyed by patient_id without the outcome label; it is not a
multi-cutoff feature history. 07_automl_recipe.py defines a recipe but never calls
it automatically: an approved larger synthetic training cohort and independent
holdout are required. The tiny fixture is unsuitable for broad model selection.

## Keep enterprise operating evidence

For every cloud exercise record code/source revisions, environment/runtime/access
mode, principal, configured route, scoped operation, expected/observed result,
run/resource references, cost observation and retirement owner. Deploying a job
definition, completing its run and accepting its data are separate checks.

For access, record allowed and denied tests as the intended reader/workload.
For a network claim, inspect actual routing/endpoints/policies for the selected
classic or serverless plane. For recurring products, assign schema/freshness
targets, owner, compatibility policy and failure contact. The two-column facility
fixture needs a reviewed period/as-of field before any multi-period append.

On failure preserve source versions, errors and checkpoint state; inspect partial
multi-table commits before replay. Record the cause supported by evidence,
owner-approved remedy, actual recovery and downstream reconciliation. Retire
unused compute, indices/endpoints, staging and disposable resources through their
owners; stopping one job does not stop every chargeable service.
