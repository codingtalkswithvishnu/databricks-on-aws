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
import healthcare
from genie_contract import summarize_genie_message
from search_contract import policy_hits, POLICY_FIELDS

class ContractChecks(unittest.TestCase):
    def test_appointment_result_and_rejection_evidence(self):
        source = healthcare.records("appointments.csv")
        clean, invalid, duplicates = healthcare.clean_appointments(source)
        self.assertEqual((len(source), len(clean), len(invalid), duplicates), (6,3,2,1))
        self.assertEqual(healthcare.appointment_summary(), {"FAC01":1,"FAC02":1,"FAC03":1})
        self.assertEqual({row["rejection_reason"] for row in invalid},
                         {"missing appointment_id", "invalid scheduled_date"})

    def test_conflicting_duplicate_needs_a_rule(self):
        rows = healthcare.records("appointments.csv")[:1]
        rows += [{**rows[0], "facility_id":"FAC02"}]
        with self.assertRaises(ValueError):
            healthcare.clean_appointments(rows)

    def test_history_features_and_patient_split_cover_both_classes(self):
        rows = healthcare.records("appointment_history.csv")
        self.assertEqual(len(rows), 40)
        self.assertEqual(len({r["visit_id"] for r in rows}), 40)
        features = healthcare.training_rows()
        self.assertEqual(len(features), 20)
        self.assertEqual(features[0], {"patient_id":"P001", "prior_visits":2,
                         "prior_missed_visits":1, "avg_lead_days":18.5, "no_show":1})
        labels = {r["patient_id"]:r["no_show"] for r in features}
        train = {k:v for k,v in labels.items() if int(k[1:]) % 5}
        test = {k:v for k,v in labels.items() if not int(k[1:]) % 5}
        self.assertEqual((len(train),len(test)),(16,4))
        self.assertEqual(set(train.values()), {0,1})
        self.assertEqual(set(test.values()), {0,1})

    def test_history_at_or_after_feature_cutoff_is_rejected(self):
        rows = healthcare.records("appointment_history.csv")
        for value in [healthcare.FEATURE_CUTOFF, "2026-02-15"]:
            with self.subTest(date=value), self.assertRaisesRegex(ValueError, "cutoff"):
                healthcare.training_rows([{**rows[0], "visit_date":value}] + rows[1:])

    def test_labels_require_later_observation_unique_keys_and_matching_cohort(self):
        rows = healthcare.records("attendance_outcomes.csv")
        variants = [rows[:-1], rows + [rows[0]],
                    [{**rows[0], "observed_date":rows[0]["scheduled_date"]}] + rows[1:],
                    [{**rows[0], "scheduled_date":"2026-01-20"}] + rows[1:],
                    [{**rows[0], "no_show":"2"}] + rows[1:]]
        for variant in variants:
            with self.subTest(size=len(variant)), self.assertRaises(ValueError):
                healthcare.training_rows(outcomes=variant)

    def test_bad_history_and_conflicting_visit_are_rejected(self):
        rows = healthcare.records("appointment_history.csv")
        for value in ["NaN", "Infinity", "-Infinity", "-1", "bad"]:
            with self.subTest(lead=value), self.assertRaises(ValueError):
                healthcare.training_rows([{**rows[0], "lead_days":value}] + rows[1:])
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            healthcare.training_rows(rows + [{**rows[0], "attended":"0"}])

    def test_march_scoring_appointments_follow_observed_training_outcomes(self):
        appointments, _, _ = healthcare.clean_appointments(healthcare.records("appointments.csv"))
        features = {r["patient_id"] for r in healthcare.training_rows()}
        last_observed = max(r["observed_date"] for r in healthcare.records("attendance_outcomes.csv"))
        self.assertTrue(all(r["patient_id"] in features and r["scheduled_date"] >= healthcare.SCORE_START
                            and r["scheduled_date"] > last_observed for r in appointments))

    def test_missing_patient_or_unknown_facility_is_quarantined(self):
        original = healthcare.records("appointments.csv")[0]
        for change in [{"patient_id":"\t "}, {"facility_id":"FAC99"}, {"scheduled_date":"20260310"}]:
            clean, invalid, duplicates = healthcare.clean_appointments([{**original, **change}])
            self.assertEqual((len(clean), len(invalid), duplicates), (0,1,0))

    def test_policy_sources_and_unknown_question(self):
        known = healthcare.answer("How much notice is needed for appointment rescheduling?")
        self.assertEqual(known["citations"], ["P001"])
        self.assertIn("24 hours",known["answer"])
        unknown = healthcare.answer("What is the parking fee?")
        self.assertEqual(unknown["answer"], healthcare.NOT_FOUND)
        self.assertEqual(unknown["citations"], [])

    def test_policy_selection_excludes_drafts_and_future_versions(self):
        original = healthcare.policies()[0]
        future = {**original, "version":"2.0", "effective_from":"2026-04-01", "body":"Future"}
        draft = {**original, "version":"3.0", "status":"draft", "body":"Unapproved"}
        self.assertEqual(healthcare.approved_policies([original, future, draft]), [original])
        newer = {**original, "version":"1.1", "effective_from":"2026-02-01", "body":"Current"}
        self.assertEqual(healthcare.approved_policies([original, newer]), [newer])
        with self.assertRaises(ValueError):
            healthcare.approved_policies([original, {**original, "body":"Conflicting"}])

    def test_answer_retains_selected_policy_version_and_owner(self):
        result = healthcare.answer("rescheduling notice")
        self.assertEqual(result["policy_snapshot_date"], "2026-03-01")
        self.assertEqual(result["sources"], [{"article_id":"P001", "version":"1.0",
                         "effective_from":"2026-01-01", "owner":"scheduling_operations"}])

    def test_live_answer_structural_contract_with_fake_model(self):
        reply = lambda _: json.dumps({"answer":"24 hours before the appointment","citations":["P001"]})
        self.assertEqual(healthcare.answer("rescheduling notice",reply)["mode"], "live-model")
        invalid = lambda _: json.dumps({"answer":"Claim","citations":["P999"]})
        with self.assertRaises(ValueError):
            healthcare.answer("rescheduling notice", invalid)
        missing = lambda _: json.dumps({"answer":"Claim","citations":[]})
        with self.assertRaises(ValueError):
            healthcare.answer("rescheduling notice", missing)

    def test_agent_allows_one_read_and_refuses_write_request(self):
        result = healthcare.agent("How many accepted appointments are there by facility?")
        self.assertEqual(result["result"], {"FAC01":1,"FAC02":1,"FAC03":1})
        self.assertEqual(result["mode"],"simulated-plan")
        self.assertEqual(healthcare.agent("Delete patient records")["status"],"refused")

    def test_tool_dispatcher_rejects_unknown_and_extra_arguments(self):
        plans = [
            {"tool":"run_sql","arguments":{"sql":"DROP TABLE appointments"}},
            {"tool":"appointment_summary","arguments":{"catalog":"private"}},
            {"tool":"search_policies","arguments":{"query":"rescheduling","path":"secrets"}},
            {"tool":"search_policies","arguments":{"query":12}},
            {"tool":"search_policies","arguments":{"query":"x"*301}},
            {"tool":"appointment_summary","arguments":{},"next_step":"anything"},
            {"tool":[],"arguments":{}},
        ]
        for plan in plans:
            with self.subTest(plan=plan):
                with self.assertRaises(ValueError):
                    healthcare.execute_plan(plan)

    def test_model_plan_is_validated_before_dispatch(self):
        valid = lambda _: '{"tool":"appointment_summary","arguments":{}}'
        self.assertEqual(healthcare.agent("appointment count",valid)["mode"],"live-model-plan")
        unknown = lambda _: '{"tool":"delete_data","arguments":{}}'
        with self.assertRaises(ValueError):
            healthcare.agent("show a summary", unknown)
        malformed = lambda _: "This is not JSON"
        with self.assertRaises(ValueError):
            healthcare.agent("show a summary",malformed)

    def test_offline_unanswered_does_not_call_model(self):
        def forbidden(_):
            raise AssertionError("No evidence should cause no model call")
        self.assertEqual(healthcare.answer("parking fee",forbidden)["mode"],"unanswered")

    def test_clinical_questions_abstain_without_model_or_tool_execution(self):
        def forbidden(_):
            raise AssertionError("Clinical request must not call a model")
        question = "Which medication dose should this patient take before the appointment?"
        self.assertEqual(healthcare.answer(question, forbidden)["mode"], "unanswered")
        self.assertEqual(healthcare.agent(question, forbidden)["status"], "refused")

    def test_rescheduling_notice_question_does_not_route_to_counts(self):
        result = healthcare.agent("How many hours notice is needed for appointment rescheduling?")
        self.assertEqual(result["tool"], "search_policies")
        self.assertIn("P001", result["citations"])

    def test_genie_adapter_handles_query_before_text_and_retains_identifiers(self):
        payload = {"status":"COMPLETED", "message_id":"message-1", "conversation_id":"conversation-1",
                   "attachments":[{"attachment_id":"attachment-1", "query":{"query":"SELECT facility_id, appointments FROM analytics.gold.appointments_by_facility"}},
                                  {"text":{"content":"Three facilities have one appointment each"}}]}
        result = summarize_genie_message(payload)
        self.assertEqual(result["message_id"], "message-1")
        self.assertEqual(result["queries"][0]["attachment_id"], "attachment-1")
        self.assertEqual(len(result["texts"]), 1)

    def test_genie_adapter_rejects_failed_empty_or_malformed_responses(self):
        base = {"status":"COMPLETED", "message_id":"message-1", "conversation_id":"conversation-1"}
        with self.assertRaises(RuntimeError):
            summarize_genie_message({**base, "status":"FAILED"})
        for attachments in [[], [None], [{"query":{"query":"SELECT 1"}}], [{"text":{"content":None}}]]:
            with self.assertRaises(ValueError):
                summarize_genie_message({**base, "attachments":attachments})

    def test_search_response_uses_named_columns_and_rejects_incomplete_records(self):
        document = healthcare.policies()[0]
        names = list(reversed(POLICY_FIELDS)) + ["score"]
        payload = {"manifest":{"columns":[{"name":name} for name in names]},
                   "result":{"data_array":[[document[name] for name in names[:-1]] + [0.9]]}}
        self.assertEqual(policy_hits(payload), [{key:document[key] for key in POLICY_FIELDS}])
        with self.assertRaises(ValueError):
            policy_hits({"manifest":{"columns":[{"name":"body"}]}, "result":{"data_array":[]}})

    def test_external_retrieval_preserves_rank_and_approved_version_scope(self):
        docs = healthcare.policies()
        result = healthcare.answer("referral intake", retriever=lambda _:[docs[1], docs[0]])
        self.assertEqual(result["citations"], ["P002"])
        self.assertEqual(result["mode"], "retrieval-extractive")
        future = {**docs[0], "effective_from":"2026-04-01"}
        self.assertEqual(healthcare.answer("rescheduling", retriever=lambda _:[future])["mode"], "unanswered")
        def forbidden(_):
            raise AssertionError("Out-of-scope clinical case must not retrieve or generate")
        self.assertEqual(healthcare.answer("medication dose", forbidden, forbidden)["mode"], "unanswered")

    def test_read_questions_with_action_words_are_allowed(self):
        for question in ["What is the billing email?", "Where should I send a billing question?"]:
            with self.subTest(question=question):
                result = healthcare.agent(question)
                self.assertEqual(result["status"], "completed")
                self.assertIn("P003", result["citations"])
        for question in ["Please delete records", "Could you please email patients"]:
            self.assertEqual(healthcare.agent(question)["status"], "refused")

    def test_ambiguous_or_nonstandard_model_json_is_rejected(self):
        replies = [
            '{"tool":"delete_data","tool":"appointment_summary","arguments":{}}',
            '{"tool":"appointment_summary","arguments":{},"arguments":{}}',
            '{"tool":"search_policies","arguments":{"query":"rescheduling","query":"billing"}}',
            '{"tool":"appointment_summary","arguments":NaN}',
            "[" * 2000 + "]" * 2000,
            "x" * 20001, None,
        ]
        for reply in replies:
            with self.subTest(reply_type=type(reply).__name__):
                with self.assertRaises(ValueError):
                    healthcare.agent("show a summary", lambda _, value=reply: value)
        with self.assertRaises(ValueError):
            healthcare.answer("rescheduling notice", lambda _: (
                '{"answer":"unsupported","answer":"24 hours","citations":["P001"]}'))

class AdapterChecks(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {
            "DATABRICKS_HOST": "https://unit.cloud.databricks.com",
            "DATABRICKS_MODEL_ENDPOINT": "unit-model", "DATABRICKS_TOKEN": "TEST_ONLY"})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def response(self, body):
        return patch.object(healthcare.MODEL_OPENER, "open", return_value=io.BytesIO(body))

    def test_chat_request_contract_and_valid_response(self):
        messages = [{"role":"user", "content":"unit question"}]
        with self.response(b'{"choices":[{"message":{"content":"unit answer"}}]}') as opened:
            self.assertEqual(healthcare.chat(messages), "unit answer")
        request = opened.call_args.args[0]
        self.assertEqual(request.full_url,
                         "https://unit.cloud.databricks.com/serving-endpoints/unit-model/invocations")
        self.assertEqual(request.get_header("Authorization"), "Bearer TEST_ONLY")
        self.assertEqual(json.loads(request.data), {
            "messages":messages, "max_tokens":350, "temperature":0})
        self.assertEqual(opened.call_args.kwargs["timeout"], 20)

    def test_explicit_comparison_endpoint_uses_the_same_validated_adapter(self):
        with self.response(b'{"choices":[{"message":{"content":"unit answer"}}]}') as opened:
            self.assertEqual(healthcare.chat([], endpoint="unit-candidate"), "unit answer")
        self.assertIn("/serving-endpoints/unit-candidate/invocations", opened.call_args.args[0].full_url)
        for endpoint in ["../other", "", 12]:
            with patch.object(healthcare.MODEL_OPENER, "open") as opened:
                with self.assertRaises(ValueError):
                    healthcare.chat([], endpoint=endpoint)
                opened.assert_not_called()

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
                with patch.object(healthcare.MODEL_OPENER, "open") as opened:
                    with self.assertRaises(ValueError) as error:
                        healthcare.chat([])
                    self.assertNotIn("TEST_ONLY", str(error.exception))
                    opened.assert_not_called()

    def test_redirects_fail_without_forwarding_authorization(self):
        handler = next(h for h in healthcare.MODEL_OPENER.handlers if isinstance(h, healthcare.NoRedirect))
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
                with patch.object(healthcare.MODEL_OPENER, "open", side_effect=failure):
                    with self.assertRaises(RuntimeError) as error:
                        healthcare.chat([])
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
                    healthcare.chat([])

    def test_python_sources_parse(self):
        for file in ROOT.rglob("*.py"):
            if ".git" not in file.parts:
                ast.parse(file.read_text(encoding="utf-8"), filename=str(file))

if __name__ == "__main__":
    unittest.main(verbosity=2)

