# Administrative policy assistant

From the repository root:

```shell
python 04-assistant/assistant.py --question "How much notice is needed for appointment rescheduling?"
python 04-assistant/assistant.py --question "What is the parking fee?"
```

The first answer cites P001 and the fictional 24-hour notice rule. The second
returns an unanswered result. P002 covers referral intake; P003 billing support.
The default is lexical retrieval with an extractive answer; no model is called.

Retrieval is not a semantic answerability check. A question about a rescheduling
fee can retrieve the notice policy even though that passage states no fee. Treat
that response as insufficient evidence; the local extractor does not classify
every unsupported question. Test this separately from the parking case, which
retrieves no eligible passage. Missing or unreadable source files return a
sanitized failed JSON result and exit status 1, rather than an unanswered result.

Select only approved policies effective by POLICY_AS_OF = 2026-03-01. Keep the
current eligible version per article ID and reject ambiguous versions sharing
an effective date. Preserve ID, version, effective date and owner in the result.
Draft/future records are excluded. At most two documents are retrieved.

## Optional live generation

The same command with `--live` requires process environment variables
DATABRICKS_HOST, DATABRICKS_TOKEN and DATABRICKS_MODEL_ENDPOINT. Obtain them
through your approved credential process; do not store tokens in source or logs.
The adapter accepts an HTTPS AWS Databricks workspace host under
*.cloud.databricks.com, a bounded endpoint identifier and an ASCII nonblank token.
It makes a chat-compatible serving-endpoint request. SDK notebook authentication
does not automatically populate these process variables.

The adapter refuses redirects, sanitizes HTTP/transport failures, limits response
body/content size, requests at most 350 tokens and uses a 20-second socket timeout.
That timeout is not a total request-duration guarantee. Model JSON must have the
expected answer/citation structure; duplicate keys, nonstandard constants and
unknown citation IDs are rejected. A valid source ID does not prove semantic
support for every generated claim: inspect content with representative cases.

`--live` still uses local lexical retrieval. The optional configured notebook
06-integrations/03_managed_policy_search.py separately uses managed AI Search,
validates returned source metadata/body against the fixture, and supplies those
retrieved documents to the same answer function. It needs an approved index,
endpoints, SDK, source table and cloud permissions; see its prerequisites.

A small keyword scope guard abstains on common clinical questions before a
retriever/model call. It is a teaching convenience, not a comprehensive clinical
classifier. No clinical or patient-record tool exists. Tests cover source
selection, abstention, malformed output and injected fake-model behavior;
they do not establish actual endpoint quality or production authorization.
