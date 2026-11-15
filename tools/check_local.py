"""Offline contract and boundary checks. No AWS/Databricks credentials required."""
import ast
import json
import sys
import unittest
from pathlib import Path
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

    def test_python_sources_parse(self):
        for file in ROOT.rglob("*.py"):
            if ".git" not in file.parts:
                ast.parse(file.read_text(encoding="utf-8"), filename=str(file))

if __name__ == "__main__":
    unittest.main(verbosity=2)

