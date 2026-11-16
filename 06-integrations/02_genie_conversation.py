# Databricks notebook source
# Optional configured cloud exercise; no live execution claimed.
import sys
from pathlib import Path
candidates = [Path.cwd() / "shared", Path.cwd().parent / "shared"]
module_root = next((p for p in candidates if (p / "healthcare.py").is_file()), None)
if module_root is None:
    raise RuntimeError("Open the complete companion project")
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
