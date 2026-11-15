# Optional cloud boundaries and review records

These are configuration/evidence plans, not claims of completed deployments.

- **S3 and Unity Catalog:** record source account/region/prefix, IAM role purpose,
  trust/external-ID completion, bucket/KMS policies, storage credential/location,
  intended table grants and an actual allowed/denied fixture read.
- **Network:** identify classic/serverless plane, target, configured route,
  private endpoint if required, owner and observed test. A region/name printout
  is not a VPC validation.
- **Redshift:** exact endpoint/database/schema, supported connector, identity,
  staging S3/KMS permissions and network path. Write/read a disposable result
  and compare the three country counts before retiring it.
- **Glue federation:** select a direction, supported table format and read/write
  scope. Distinguish a named UC view from a demonstrated external catalog query.
- **Kinesis:** create an isolated approved learning stream; establish the external
  producer and connector identity; send sample-data/events.jsonl using that
  producer (no producer application is included here); save acknowledgements;
  use earliest initial position for a fresh checkpoint and a compatible finite
  trigger; check E001/E002/E003 and one minute window containing three events;
  rerun and inspect progress; retire only this stream through its owner.
- **Auto Loader:** use a dedicated checkpoint and a new optional branch table,
  analytics.bronze.signups_incremental. Preserve analytics.bronze.signups for the
  baseline cleaning/reporting path. Check six rows after one fixture file and
  the unchanged second run with no new input.
- **AI endpoint:** permitted exact identifier/interface, supported identity,
  a synthetic request, response contract, limits, error case and usage record.
- **Classification:** use tickets.csv and compare all expected categories.
  Invalid output is a failure, not another category to accept silently.
- **Genie:** curate the gold signup table, definitions and summary-table SQL
  (select country/signups rather than counting country rows); grant the actual
  analyst access to that named table. Check GB/IN/US answers and an unsupported
  question under that identity.
- **AI Search:** approved endpoint, exact source table analytics.support.help_articles,
  unique article_id, title/body, required source features/CDF, embedding endpoint,
  privileges, ready/synchronized state; retrieve P001 before generation.
- **Provider change:** choose one documented external-model/model-provider route,
  exact model/region/authentication, compatible chat adapter, identical questions,
  retrieved source IDs, quality, latency/usage and error results.
- **Model registry/serving:** signature/input example, model schema and caller
  privileges, reproducible feature lookup, approved deployment/cost owner,
  response/denial checks and retirement plan.
- **Multiple teams:** ownership/catalog/workspace matrix; data-product schema,
  quality/freshness targets, measured service level, compatibility and escalation.
- **Case studies:** dated official source, reported fact, author inference and
  applicability. Do not assign unreported components to a named customer.
- **Troubleshooting:** exact failing operation/principal/compute route, evidence,
  supported cause, owner-approved change, recovery check and retirement.

Record source revision, command and working directory, date, actual environment,
observed result, boundary checked, artifact location, remaining gap and owner.
Signed-in cloud runs, model calls, permissions and deployment are unverified
until that record contains the actual outcome.

