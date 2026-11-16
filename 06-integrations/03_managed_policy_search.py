# Databricks notebook source
# Optional configured cloud exercise; no live execution claimed.
import sys
import os
from pathlib import Path
configured_root = (dbutils.widgets.getAll().get("book_root") if "dbutils" in globals() else None) or os.environ.get("DATABRICKS_BOOK_ROOT")
if configured_root and not Path(configured_root).is_absolute():
    raise RuntimeError("DATABRICKS_BOOK_ROOT must be an absolute project directory")
candidates = ([Path(configured_root) / "shared"] if configured_root else
              [Path.cwd() / "shared", Path.cwd().parent / "shared"])
module_root = next((p for p in candidates if (p / "healthcare.py").is_file()), None)
if module_root is None:
    raise RuntimeError("Set DATABRICKS_BOOK_ROOT to the complete project directory")
sys.path.insert(0, str(module_root))

# COMMAND ----------
import os
import json
from datetime import timedelta
from databricks.ai_search.client import AISearchClient
from healthcare import answer, chat, policies
from search_contract import policy_hits, POLICY_FIELDS

search_endpoint = os.environ.get("DATABRICKS_AI_SEARCH_ENDPOINT", "")
embedding_endpoint = os.environ.get("DATABRICKS_EMBEDDING_ENDPOINT", "")
if not search_endpoint or not embedding_endpoint:
    raise ValueError("Set the approved search and embedding endpoint identifiers")
client = AISearchClient()
index = client.create_delta_sync_index_and_wait(
    endpoint_name=search_endpoint,
    index_name="analytics.support.northstar_policy_index_demo",
    primary_key="article_id",
    source_table_name="analytics.support.help_articles",
    pipeline_type="TRIGGERED",
    embedding_source_column="body",
    embedding_model_endpoint_name=embedding_endpoint,
    timeout=timedelta(minutes=5),
)
index.sync()
index.wait_until_ready(timeout=timedelta(minutes=5), wait_for_updates=True)
expected_sources = {document["article_id"]:document for document in policies()}

def managed_fixture_retrieve(question):
    hits = index.similarity_search(
        query_text=question, columns=list(POLICY_FIELDS), num_results=2
    )
    documents = policy_hits(hits)
    if any(expected_sources.get(document["article_id"]) != document for document in documents):
        raise ValueError("Search content/version differs from the approved fixture snapshot")
    return documents

question = "How much notice is needed for appointment rescheduling?"
retrieved = managed_fixture_retrieve(question)
assert retrieved and retrieved[0]["article_id"] == "P001"
result = answer(question, model_call=chat, retriever=lambda _:retrieved)
print(json.dumps(result, indent=2))
