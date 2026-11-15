# A policy assistant with visible evidence

Run from the repository root. Local mode uses supplied synthetic policies, a
lexical retriever and an extractive answer. The return-window query cites P001
and mentions 30 days. An acquisition-plans query has no evidence and abstains.

--live is a separate model request. Set DATABRICKS_HOST (approved HTTPS AWS
workspace), DATABRICKS_MODEL_ENDPOINT (chat-compatible permitted endpoint) and
DATABRICKS_TOKEN using the approved learning authentication process. Do not
commit or paste tokens into the repository. The adapter's token input is a
small demonstration; select supported OAuth/service-principal authentication
for a real service. Requests have a 20-second timeout and output-token bound.

The live response must be JSON containing answer and citations. Unknown source
IDs and malformed output fail. Structural validation does not prove that every
claim follows from a cited passage: inspect and evaluate that separately.

For managed retrieval, use the Chapter 16 checklist in 06-integrations. This
local lexical retriever does not claim to be a Databricks AI Search index.

This is a command-line learner application. It does not implement application
sign-in, per-user authorization, production hosting or a multi-user service.

