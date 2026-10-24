"""Transport recovery is bounded, durable and never manufactures a Council vote."""
from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import test_ai_trade_council_failure_injection as council_fixture


class CouncilProviderRateLimitTests(unittest.TestCase):
    def setUp(self):
        self.fixture = council_fixture.AiTradeCouncilFailureInjectionTests()
        self.fixture.setUp()
        self.bridge = self.fixture.bridge
        self.stack = ExitStack()
        for patch in self.fixture._analysis_patches():
            self.stack.enter_context(patch)
        self.stack.enter_context(mock.patch.object(self.bridge, "_metatrader_scope_header_locks_ready", return_value=True))
        self.dispatch = self.stack.enter_context(mock.patch.object(self.bridge, "dispatch_ai_trade_council_trade_plan"))
        self.fixture._configure_selected_mt4()
        snapshot = self.bridge.metatrader_snapshot_read_model(self.bridge.AI_TRADE_COUNCIL_PROP_ID)
        self.round = self.fixture._queue_analysis(snapshot["chartSnapshot"]["snapshotId"])
        self.parent_id = self.round["parent"]["id"]
        self.child_id = next(row["id"] for row in self.bridge.load_missions() if (row.get("analysisContext") or {}).get("roleId") == "news")
        self.claimed = self.bridge.claim_auto_mission(self.child_id, "test-worker")
        self.assertIsNotNone(self.claimed)
        self.lease = self.claimed["execution"]["leaseId"]

    def tearDown(self):
        self.stack.close()
        self.fixture.tearDown()

    @staticmethod
    def failure(retry_after=None):
        return {
            "ok": False, "processOk": False, "processStarted": True,
            "status": "rate_limited", "workStatus": "rate_limited",
            "message": "Codex แจ้งว่า Rate Limit ยังไม่พร้อมสำหรับงานใหม่",
            "finalMessage": "exceeded retry limit, last status: 429 Too Many Requests",
            "providerFailure": {"schemaVersion": "codex-provider-http-failure-v1", "httpStatus": 429,
                                "retryable": True, "retryAfterSeconds": retry_after},
        }

    def defer(self, result=None):
        return self.bridge._defer_council_provider_rate_limit(
            self.child_id, self.lease, {"processStarted": True}, result or self.failure())

    def make_retry_due(self):
        class AfterProviderBackoff(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime.now(tz) + timedelta(seconds=60)
        self.stack.enter_context(mock.patch.object(self.bridge, "datetime", AfterProviderBackoff))

    def test_one_retry_keeps_ids_snapshot_attempt_history_and_waiting_parent(self):
        context = copy.deepcopy(self.claimed["analysisContext"])
        budget = copy.deepcopy(self.claimed["budget"])
        self.assertEqual(budget["maxRuns"], 2)
        retried = self.defer()
        self.assertEqual(retried["status"], "queued")
        self.assertEqual(retried["attemptCount"], 1)
        self.assertEqual(retried["analysisContext"], context)
        self.assertEqual(retried["budget"], budget)
        self.assertEqual(len(self.bridge.load_missions()), 4)
        self.assertEqual(retried["councilProviderRetry"]["history"][0]["leaseId"], self.lease)
        self.assertNotEqual(retried["execution"]["authorizationId"], self.claimed["execution"]["authorizationId"])
        self.assertIsNone(self.bridge.auto_execution_authorization_error(retried))
        self.assertIn(self.bridge.find_mission(self.parent_id)["status"], {"queued", "running"})
        self.assertIsNone(self.bridge.claim_auto_mission(self.child_id, "too-soon"))
        self.dispatch.assert_not_called()
        self.make_retry_due()
        second = self.bridge.claim_auto_mission(self.child_id, "second-worker")
        self.assertEqual(second["attemptCount"], 2)
        self.assertEqual(second["analysisContext"], context)
        self.assertIsNone(self.bridge._defer_council_provider_rate_limit(
            self.child_id, second["execution"]["leaseId"], {"processStarted": True}, self.failure()))

    def test_concurrent_finish_receipts_and_claims_cannot_duplicate_retry(self):
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda _: self.defer(), range(3)))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(len(self.bridge.find_mission(self.child_id)["councilProviderRetry"]["history"]), 1)
        self.make_retry_due()
        with ThreadPoolExecutor(max_workers=3) as pool:
            claims = list(pool.map(lambda index: self.bridge.claim_auto_mission(self.child_id, f"worker-{index}"), range(3)))
        self.assertEqual(sum(claim is not None for claim in claims), 1)
        self.assertEqual(self.bridge.find_mission(self.child_id)["attemptCount"], 2)
        self.dispatch.assert_not_called()

    def test_provider_retry_after_is_honored_or_deadline_denies_retry(self):
        retried = self.defer(self.failure(55))
        self.assertEqual(retried["councilProviderRetry"]["history"][0]["retryAfterSeconds"], 55)

    def test_wait_beyond_round_and_original_single_run_budget_are_not_extended(self):
        self.assertIsNone(self.defer(self.failure(3600)))
        mission = self.bridge.find_mission(self.child_id)
        mission["budget"]["maxRuns"] = 1
        mission["analysisContext"].pop("providerRetryPolicy")
        mission["execution"]["authorizationPayloadDigest"] = self.bridge.mission_payload_digest(mission)
        self.bridge.replace_mission(mission)
        self.assertIsNone(self.defer())
        self.assertEqual(self.bridge.find_mission(self.child_id)["attemptCount"], 1)
        self.dispatch.assert_not_called()

    def test_quota_auth_invalid_output_or_stopping_never_retries(self):
        for status in ("auth_required", "invalid_output", "timeout", "failed"):
            result = self.failure()
            result["status"] = status
            self.assertIsNone(self.defer(result))
        hard_stop = self.failure()
        hard_stop["providerFailure"]["retryable"] = False
        self.assertIsNone(self.defer(hard_stop))
        with mock.patch.object(self.bridge.MISSION_WORKER_STOP, "is_set", return_value=True):
            self.assertIsNone(self.defer())
        with mock.patch.object(self.bridge, "load_operator_mode_record", return_value={"mode": "manual_guarded"}):
            self.assertIsNone(self.defer())

    def test_digest_rejects_retry_history_mutation(self):
        retried = self.defer()
        retried["councilProviderRetry"]["history"][0]["retryAfterSeconds"] = 1
        self.assertEqual(self.bridge.auto_execution_authorization_error(retried), "auto_policy_digest_mismatch")

    def test_stale_worker_deferral_cannot_shorten_provider_backoff(self):
        retried = self.defer(self.failure(55))
        receipt = retried["councilProviderRetry"]["nextAttemptAt"]
        after = self.bridge.defer_auto_mission(self.child_id, "runner_busy", 1)
        self.assertEqual(after["execution"]["nextAttemptAt"], receipt)
        # Even a legacy caller rewriting only the mutable scheduling hint may
        # not evade the immutable, digest-bound provider deadline at claim.
        after["execution"]["nextAttemptAt"] = self.bridge.utc_now()
        self.bridge.replace_mission(after)
        self.assertIsNone(self.bridge.claim_auto_mission(self.child_id, "too-soon"))
        other = self.bridge.find_next_auto_mission(council_only=True)
        self.assertNotEqual((other or {}).get("id"), self.child_id)
        self.assertEqual(self.bridge.find_mission(self.child_id)["attemptCount"], 1)
        self.make_retry_due()
        self.assertEqual(self.bridge.claim_auto_mission(self.child_id, "after-wait")["attemptCount"], 2)

    def test_retry_dispatch_still_requires_fresh_quota_without_resetting_attempts(self):
        retried = self.defer()
        self.make_retry_due()
        with (
            mock.patch.object(self.bridge, "CODEX_RUNNER_PYTHON", Path(__file__)),
            mock.patch.object(self.bridge, "CODEX_RUNNER_SCRIPT", Path(__file__)),
            mock.patch.object(self.bridge, "codex_rate_limits", return_value={
                "ok": True, "stale": False, "limitReached": True,
                "primary": {"usedPercent": 100, "remainingPercent": 0},
            }),
            mock.patch.object(self.bridge, "run_safe_command") as run,
        ):
            self.bridge.process_auto_mission("quota-denied-worker", self.bridge.find_mission(self.child_id))
        run.assert_not_called()
        after = self.bridge.find_mission(self.child_id)
        self.assertEqual(after["attemptCount"], 1)
        self.assertEqual(after["councilProviderRetry"], retried["councilProviderRetry"])
        self.dispatch.assert_not_called()

    def test_restart_keeps_deferred_receipt_but_does_not_replay_running_retry(self):
        retried = self.defer()
        self.assertEqual(self.bridge.recover_interrupted_missions(), 0)
        self.assertEqual(self.bridge.find_mission(self.child_id)["councilProviderRetry"], retried["councilProviderRetry"])
        self.make_retry_due()
        self.bridge.claim_auto_mission(self.child_id, "retry-worker")
        self.assertEqual(self.bridge.recover_interrupted_missions(), 1)
        interrupted = self.bridge.find_mission(self.child_id)
        self.assertEqual(interrupted["status"], "failed")
        self.assertEqual(interrupted["attemptCount"], 2)
        self.assertIsNone(self.bridge.claim_auto_mission(self.child_id, "after-restart"))
        self.dispatch.assert_not_called()

    def test_exhausted_429_is_reported_as_provider_failure_not_schema_mismatch(self):
        result = self.failure(3600)
        finished = self.bridge.finish_auto_mission(self.child_id, self.lease, {"processStarted": True}, result)
        self.assertIn("429", finished["result"])
        self.assertNotIn("Output Schema", finished["result"])
        self.assertEqual(finished["errorCode"], "rate_limited")
        self.assertNotIn("councilVote", finished)

    def test_retry_finish_then_three_real_validated_votes_complete_one_parent(self):
        self.dispatch.return_value = {"status": "no_trade", "reasonCode": "consensus_threshold_not_met", "commandPublished": False}
        deferred = self.bridge.finish_auto_mission(self.child_id, self.lease, {"processStarted": True}, self.failure())
        self.assertEqual(deferred["status"], "queued")
        self.make_retry_due()
        children = [row for row in self.bridge.load_missions() if row.get("parentMissionId") == self.parent_id]
        for child in sorted(children, key=lambda row: row["id"] == self.child_id):
            claimed = self.bridge.claim_auto_mission(child["id"], "test-success")
            context = claimed["analysisContext"]
            role = context["roleId"]
            vote = {
                "snapshotId": context["snapshotId"], "agentId": context["agentId"], "roleId": role,
                "decision": "HOLD", "confidence": 82, "horizonBars": context["horizonBars"],
                "validUntilBarTime": context["validUntilBarTime"], "stopLossPrice": None, "takeProfitPrice": None,
                "indicatorValidation": "PASS" if role == "technical" else None,
                "volatilityState": context["volatilityState"] if role == "technical" else None,
                "eventRisk": "HOLD" if role == "news" else None, "horizon": "next closed bar",
                "observations": [f"{role}: exact frozen snapshot"], "invalidation": "new closed bar",
                "evidence": [{"label": "snapshot", "observedAt": self.bridge.utc_now(), "sourceUrl": None}], "warnings": [],
            }
            result = {"ok": True, "status": "completed", "workStatus": "completed", "processStarted": True,
                      "finalMessage": json.dumps(vote)}
            finished = self.bridge.finish_auto_mission(child["id"], claimed["execution"]["leaseId"], {"processStarted": True}, result)
            self.assertEqual(finished["status"], "completed")
            if child["id"] != self.child_id:
                self.dispatch.assert_not_called()
        parent = self.bridge.find_mission(self.parent_id)
        self.assertEqual(parent["status"], "completed")
        self.assertTrue(parent["councilDecision"]["ready"])
        self.assertEqual(parent["councilDecision"]["voteCount"], 3)
        self.assertEqual(self.bridge.find_mission(self.child_id)["attemptCount"], 2)
        self.assertEqual(len(self.bridge.load_missions()), 4)
        self.dispatch.assert_called_once()
        self.bridge.refresh_parent_mission(self.parent_id)
        self.dispatch.assert_called_once()


class RunnerProviderClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / "runner" / "codex_cli_runner.py"
        spec = importlib.util.spec_from_file_location("runner_provider_failure_test", path)
        cls.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.runner)

    def result(self, diagnostic):
        return {"ok": False, "exitCode": 1, "stdout": diagnostic, "stderr": ""}

    def test_observed_jsonl_transport_failure_is_429_not_generic_failure(self):
        observed = json.dumps({"type": "turn.failed", "error": {"message": "exceeded retry limit, last status: 429 Too Many Requests"}})
        failure = self.runner.provider_http_rate_limit_failure(self.result(observed))
        self.assertTrue(failure["retryable"])
        self.assertEqual(failure["httpStatus"], 429)
        self.assertEqual(self.runner._chat_failure_status(self.result(observed))[0], "rate_limited")

    def test_http429_does_not_retry_quota_spend_or_auth_hard_stops(self):
        for reason in ("insufficient_quota", "usage limit reached", "quota exhausted", "spend_control_reached", "insufficient credits", "unauthorized"):
            failure = self.runner.provider_http_rate_limit_failure(self.result(f"status: 429 Too Many Requests {reason}"))
            self.assertFalse(failure["retryable"], reason)

    def test_retry_after_seconds_and_dates_respect_provider(self):
        failure = self.runner.provider_http_rate_limit_failure(self.result("status: 429\nRetry-After: 150"))
        self.assertEqual(failure["retryAfterSeconds"], 150)
        future = datetime.now(timezone.utc) + timedelta(seconds=100)
        failure = self.runner.provider_http_rate_limit_failure(self.result("status: 429\nRetry-After: " + future.strftime("%a, %d %b %Y %H:%M:%S GMT")))
        self.assertGreaterEqual(failure["retryAfterSeconds"], 99)
        self.assertFalse(self.runner.provider_http_rate_limit_failure(self.result("status: 429\nRetry-After: unreadable"))["retryable"])

    def test_success_timeout_or_bare_number_does_not_create_transport_retry(self):
        for result in ({"ok": True, "stdout": "429 Too Many Requests"},
                       {"ok": False, "exitCode": "timeout", "stdout": "429 Too Many Requests"},
                       self.result("latestClose 429")):
            self.assertIsNone(self.runner.provider_http_rate_limit_failure(result))


if __name__ == "__main__":
    unittest.main()
