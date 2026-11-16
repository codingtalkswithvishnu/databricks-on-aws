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
from datetime import timedelta
from databricks.sdk import WorkspaceClient
from genie_contract import summarize_genie_message

w = WorkspaceClient()
space_id = os.environ.get("DATABRICKS_GENIE_SPACE_ID", "")
if not space_id:
    raise ValueError("Set the approved aggregate-only Genie space ID")

first = w.genie.start_conversation_and_wait(
    space_id=space_id,
    content="How many accepted appointments are scheduled at each facility?",
    timeout=timedelta(seconds=60),
)
first_summary = summarize_genie_message(first.as_dict())
follow = w.genie.create_message_and_wait(
    space_id=space_id,
    conversation_id=first_summary["conversation_id"],
    content="Now show only FAC01.",
    timeout=timedelta(seconds=60),
)
follow_summary = summarize_genie_message(follow.as_dict())

query_results = []
for message in [first_summary, follow_summary]:
    for query in message["queries"]:
        query_results.append(w.genie.get_message_attachment_query_result(
            space_id=space_id,
            conversation_id=message["conversation_id"],
            message_id=message["message_id"],
            attachment_id=query["attachment_id"],
        ))
print("Completed conversation:", first_summary["conversation_id"])
print("Query result objects retained for inspection:", len(query_results))
