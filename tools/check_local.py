"""Offline contract and boundary checks. No AWS/Databricks credentials required."""
import ast
import http.client
import io
import json
import os
import sys
import unittest
import urllib.error
import urllib.request
from email.message import Message
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
import cedar

class ContractChecks(unittest.TestCase):
    def test_signup_expected_result_and_rejections(self):
        source = cedar.records("signups.csv")
        clean, invalid, duplicates = cedar.clean_signups(source)
        self.assertEqual((len(source), len(clean), len(invalid), duplicates), (6,3,2,1))
        self.assertEqual(cedar.signup_summary(), {"GB":1,"IN":1,"US":1})

    def test_conflicting_duplicate_needs_a_rule(self):
        rows = cedar.records("signups.csv")[:1]
        rows += [{**rows[0], "country":"US"}]
        with self.assertRaises(ValueError):
            cedar.clean_signups(rows)

    def test_order_keys_and_split_cover_both_classes(self):
        rows = cedar.records("orders.csv")
        self.assertEqual(len(rows), 40)
        self.assertEqual(len({r["order_id"] for r in rows}), 40)
        customers = {r["customer_id"]:int(r["churned"]) for r in rows}
        self.assertEqual(len(customers), 20)
        train = {k:v for k,v in customers.items() if int(k[1:]) % 5}
        test = {k:v for k,v in customers.items() if not int(k[1:]) % 5}
        self.assertEqual((len(train),len(test)),(16,4))
        self.assertEqual(set(train.values()), {0,1})
        self.assertEqual(set(test.values()), {0,1})

    def test_policy_sources_and_unknown_question(self):
        known = cedar.answer("What is the return window?")
        self.assertEqual(known["citations"], ["P001"])
        self.assertIn("30 days",known["answer"])
        unknown = cedar.answer("What are the acquisition plans?")
        self.assertEqual(unknown["answer"], cedar.NOT_FOUND)
        self.assertEqual(unknown["citations"], [])

    def test_live_answer_structural_contract_with_fake_model(self):
        reply = lambda _: json.dumps({"answer":"30 days after delivery","citations":["P001"]})
        self.assertEqual(cedar.answer("return window",reply)["mode"], "live-model")
        invalid = lambda _: json.dumps({"answer":"Claim","citations":["P999"]})
        with self.assertRaises(ValueError):
            cedar.answer("return window", invalid)
        missing = lambda _: json.dumps({"answer":"Claim","citations":[]})
        with self.assertRaises(ValueError):
            cedar.answer("return window", missing)

    def test_agent_allows_one_read_and_refuses_write_request(self):
        result = cedar.agent("How many valid signups are there?")
        self.assertEqual(result["result"], {"GB":1,"IN":1,"US":1})
        self.assertEqual(result["mode"],"simulated-plan")
        self.assertEqual(cedar.agent("Delete customer records")["status"],"refused")

    def test_tool_dispatcher_rejects_unknown_and_extra_arguments(self):
        plans = [
            {"tool":"run_sql","arguments":{"sql":"DROP TABLE customers"}},
            {"tool":"signup_summary","arguments":{"catalog":"private"}},
            {"tool":"search_policies","arguments":{"query":"return","path":"secrets"}},
            {"tool":"search_policies","arguments":{"query":12}},
            {"tool":"search_policies","arguments":{"query":"x"*301}},
            {"tool":"signup_summary","arguments":{},"next_step":"anything"},
            {"tool":[],"arguments":{}},
        ]
        for plan in plans:
            with self.subTest(plan=plan):
                with self.assertRaises(ValueError):
                    cedar.execute_plan(plan)

    def test_model_plan_is_validated_before_dispatch(self):
        valid = lambda _: '{"tool":"signup_summary","arguments":{}}'
        self.assertEqual(cedar.agent("signup count",valid)["mode"],"live-model-plan")
        unknown = lambda _: '{"tool":"delete_data","arguments":{}}'
        with self.assertRaises(ValueError):
            cedar.agent("show a summary", unknown)
        malformed = lambda _: "This is not JSON"
        with self.assertRaises(ValueError):
            cedar.agent("show a summary",malformed)

    def test_offline_unanswered_does_not_call_model(self):
        def forbidden(_):
            raise AssertionError("No evidence should cause no model call")
        self.assertEqual(cedar.answer("acquisition plans",forbidden)["mode"],"unanswered")

    def test_read_questions_with_action_words_are_allowed(self):
        for question in ["What is the billing email?", "Where should I send a billing question?"]:
            with self.subTest(question=question):
                result = cedar.agent(question)
                self.assertEqual(result["status"], "completed")
                self.assertIn("P003", result["citations"])
        for question in ["Please delete records", "Could you please email customers"]:
            self.assertEqual(cedar.agent(question)["status"], "refused")

    def test_ambiguous_or_nonstandard_model_json_is_rejected(self):
        replies = [
            '{"tool":"delete_data","tool":"signup_summary","arguments":{}}',
            '{"tool":"signup_summary","arguments":{},"arguments":{}}',
            '{"tool":"search_policies","arguments":{"query":"return","query":"billing"}}',
            '{"tool":"signup_summary","arguments":NaN}',
            "[" * 2000 + "]" * 2000,
            "x" * 20001, None,
        ]
        for reply in replies:
            with self.subTest(reply_type=type(reply).__name__):
                with self.assertRaises(ValueError):
                    cedar.agent("show a summary", lambda _, value=reply: value)
        with self.assertRaises(ValueError):
            cedar.answer("return window", lambda _: (
                '{"answer":"unsupported","answer":"30 days","citations":["P001"]}'))

class AdapterChecks(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {
            "DATABRICKS_HOST": "https://unit.cloud.databricks.com",
            "DATABRICKS_MODEL_ENDPOINT": "unit-model", "DATABRICKS_TOKEN": "TEST_ONLY"})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def response(self, body):
        return patch.object(cedar.MODEL_OPENER, "open", return_value=io.BytesIO(body))

    def test_chat_request_contract_and_valid_response(self):
        messages = [{"role":"user", "content":"unit question"}]
        with self.response(b'{"choices":[{"message":{"content":"unit answer"}}]}') as opened:
            self.assertEqual(cedar.chat(messages), "unit answer")
        request = opened.call_args.args[0]
        self.assertEqual(request.full_url,
                         "https://unit.cloud.databricks.com/serving-endpoints/unit-model/invocations")
        self.assertEqual(request.get_header("Authorization"), "Bearer TEST_ONLY")
        self.assertEqual(json.loads(request.data), {
            "messages":messages, "max_tokens":350, "temperature":0})
        self.assertEqual(opened.call_args.kwargs["timeout"], 20)

    def test_invalid_configuration_never_sends_request_or_prints_token(self):
        configurations = [
            {"DATABRICKS_TOKEN":"TEST_ONLY\n"},
            {"DATABRICKS_TOKEN":"TEST_ONLY secret"},
            {"DATABRICKS_TOKEN":""},
            {"DATABRICKS_HOST":"http://unit.cloud.databricks.com"},
            {"DATABRICKS_HOST":"https://unit.cloud.databricks.com.attacker.example"},
            {"DATABRICKS_HOST":"https://unit.cloud.databricks.com:bad"},
            {"DATABRICKS_HOST":"https://unit.cloud.databricks.com?token=TEST_ONLY"},
            {"DATABRICKS_MODEL_ENDPOINT":"../other"},
        ]
        for config in configurations:
            with self.subTest(keys=list(config)), patch.dict(os.environ, config):
                with patch.object(cedar.MODEL_OPENER, "open") as opened:
                    with self.assertRaises(ValueError) as error:
                        cedar.chat([])
                    self.assertNotIn("TEST_ONLY", str(error.exception))
                    opened.assert_not_called()

    def test_redirects_fail_without_forwarding_authorization(self):
        handler = next(h for h in cedar.MODEL_OPENER.handlers if isinstance(h, cedar.NoRedirect))
        request = urllib.request.Request("https://unit.cloud.databricks.com/path", data=b"{}",
                                         headers={"Authorization":"Bearer TEST_ONLY"})
        for code in [301, 302, 303, 307, 308]:
            headers = Message()
            headers["Location"] = "https://unrelated.example/path"
            with self.subTest(code=code), self.assertRaises(urllib.error.HTTPError) as error:
                getattr(handler, "http_error_" + str(code))(
                    request, io.BytesIO(), code, "redirect", headers)
            error.exception.close()

    def test_transport_failures_are_sanitized(self):
        failures = [
            urllib.error.HTTPError("https://unit.cloud.databricks.com", 403,
                                   "TEST_ONLY", {}, io.BytesIO(b"TEST_ONLY")),
            urllib.error.URLError("TEST_ONLY"), TimeoutError("TEST_ONLY"),
            ConnectionResetError("TEST_ONLY"), http.client.IncompleteRead(b"TEST_ONLY"),
        ]
        for failure in failures:
            with self.subTest(kind=type(failure).__name__):
                with patch.object(cedar.MODEL_OPENER, "open", side_effect=failure):
                    with self.assertRaises(RuntimeError) as error:
                        cedar.chat([])
                    self.assertNotIn("TEST_ONLY", str(error.exception))

    def test_malformed_and_oversized_responses_fail_cleanly(self):
        bodies = [b"not JSON", b"null", b"[]", b'{"choices":[]}',
                  b'{"choices":[{"message":{"content":null}}]}',
                  b'{"choices":[{"message":{"content":" "}}]}', b"\xff",
                  json.dumps({"choices":[{"message":{"content":"x" * 20001}}]}).encode(),
                  b"x" * 1_000_001]
        for body in bodies:
            with self.subTest(length=len(body)), self.response(body):
                with self.assertRaises(ValueError):
                    cedar.chat([])

    def test_python_sources_parse(self):
        for file in ROOT.rglob("*.py"):
            if ".git" not in file.parts:
                ast.parse(file.read_text(encoding="utf-8"), filename=str(file))

if __name__ == "__main__":
    unittest.main(verbosity=2)

