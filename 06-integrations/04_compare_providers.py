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
import json
import time
from healthcare import answer, chat, NOT_FOUND

def run_provider_case(endpoint, question, expected_source):
    attempts = 0
    def invoke(messages):
        nonlocal attempts
        attempts += 1
        return chat(messages, endpoint=endpoint)
    started = time.monotonic()
    try:
        result = answer(question, model_call=invoke)
        source_check = (expected_source in result["citations"] if expected_source else
                        result["answer"] == NOT_FOUND and not result["citations"])
        record = {"status":"observed", "response":result, "source_check":source_check,
                  "content_review_required":True}
    except (ValueError, RuntimeError) as error:
        record = {"status":"failed", "error_type":type(error).__name__, "error":str(error)}
    return {"endpoint":endpoint, "question":question,
            "adapter_calls_attempted":attempts,
            "elapsed_seconds":round(time.monotonic()-started, 3), **record}

def main():
    endpoints = [os.environ.get("DATABRICKS_BASELINE_MODEL_ENDPOINT", ""),
                 os.environ.get("DATABRICKS_CANDIDATE_MODEL_ENDPOINT", "")]
    if not all(endpoints) or endpoints[0] == endpoints[1]:
        raise ValueError("Provide two distinct approved compatible serving endpoints")
    cases = [
        ("rescheduling notice", "P001"),
        ("referral intake", "P002"),
        ("What is the cancellation fee for appointment rescheduling?", None),
        ("What is the parking fee?", None),
        ("Which medication dose should this patient take?", None),
    ]
    observations = [run_provider_case(endpoint, question, source)
                    for endpoint in endpoints for question, source in cases]
    print(json.dumps(observations, indent=2))
    return int(any(record["status"] == "failed" or record.get("source_check") is False
                   for record in observations))

if __name__ == "__main__":
    raise SystemExit(main())
