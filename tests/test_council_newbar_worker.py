"""New natural-bar admission cannot become a paid worker backlog.

All stores and terminal fixtures are temporary; runner/model calls are mocked.
"""
from __future__ import annotations

import copy
import json
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import test_ai_trade_council_failure_injection as fixtures


class CouncilNewBarWorkerTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.AiTradeCouncilFailureInjectionTests()
        self.f.setUp()
        self.b = self.f.bridge
        self.stack = ExitStack()
        for patch in self.f._analysis_patches():
            self.stack.enter_context(patch)
        self.stack.enter_context(mock.patch.object(
            self.b, "_metatrader_scope_header_locks_ready", return_value=True))
        self.stack.enter_context(mock.patch.object(self.b, "CODEX_RUNNER_PYTHON", Path(__file__)))
        self.stack.enter_context(mock.patch.object(self.b, "CODEX_RUNNER_SCRIPT", Path(__file__)))
        self.stack.enter_context(mock.patch.object(
            self.b, "_read_mt4_trade_gateway_ea_status",
            return_value=({"maxSnapshotAgeSeconds": 900}, None)))
        self.runner = self.stack.enter_context(mock.patch.object(self.b, "run_safe_command"))
        self.dispatch = self.stack.enter_context(mock.patch.object(self.b, "dispatch_ai_trade_council_trade_plan"))
        self.f._configure_selected_mt4()
        snapshot = self.b.metatrader_snapshot_read_model(self.b.AI_TRADE_COUNCIL_PROP_ID)
        self.f._queue_analysis(snapshot["chartSnapshot"]["snapshotId"])
        self.child = next(row for row in self.b.load_missions()
                          if (row.get("analysisContext") or {}).get("roleId") == "technical")
        now = datetime.now(timezone.utc)
        context = self.child["analysisContext"]
        context["automation"] = {
            "source": "backend_scheduler",
            "triggerMode": "last_closed_candle_time_change",
            "triggerPolicy": "new_closed_bar_only_no_backfill",
            "triggerStartupId": self.b.SERVER_STARTED_AT,
            "triggerExpiresAt": (now + timedelta(seconds=50)).isoformat(),
            "quotaAdmittedAt": (now - timedelta(seconds=5)).isoformat(),
            "executionPolicy": "current_exact_snapshot",
            "tradeCommandAllowed": True,
            **context["closedBarIdentity"],
        }
        self.save_child()

    def tearDown(self):
        self.stack.close()
        self.f.tearDown()

    def save_child(self):
        self.b._issue_backend_auto_safe_authorization(self.child)
        self.b.replace_mission(self.child)

    def stored(self):
        return self.b.find_mission(self.child["id"])

    def assert_skipped(self, reason):
        stored = self.stored()
        self.assertEqual(stored["status"], "blocked")
        self.assertEqual(stored["errorCode"], reason)
        self.assertEqual(stored["phase"], "council_bar_skipped")
        self.assertFalse(stored["execution"]["automaticRetry"])
        self.assertFalse(stored["execution"]["processStarted"])
        self.assertIsNone(stored["execution"]["nextAttemptAt"])
        self.assertFalse(stored["execution"]["roundExpired"])
        self.runner.assert_not_called()
        self.dispatch.assert_not_called()

    def test_fresh_exact_new_bar_is_admissible(self):
        self.assertIsNone(self.b._council_new_bar_start_error(self.child))

    def test_changed_quote_same_bar_does_not_invalidate_trigger(self):
        snapshot = self.b.metatrader_snapshot_read_model(self.b.AI_TRADE_COUNCIL_PROP_ID)
        snapshot["chartSnapshot"]["snapshotId"] = "f" * 64
        with mock.patch.object(self.b, "metatrader_snapshot_read_model", return_value=snapshot):
            self.assertIsNone(self.b._council_new_bar_start_error(self.child))

    def test_legacy_automatic_vote_is_retired_before_quota_or_claim(self):
        self.child["analysisContext"]["automation"].pop("triggerPolicy")
        self.save_child()
        with (mock.patch.object(self.b, "codex_rate_limits") as quota,
              mock.patch.object(self.b, "claim_auto_mission") as claim):
            self.b.process_auto_mission("legacy-upgrade", self.child)
        quota.assert_not_called()
        claim.assert_not_called()
        self.assert_skipped("council_legacy_automatic_backlog_skipped")
        self.assertEqual(self.stored()["attemptCount"], 0)

    def test_previous_startup_same_bar_is_retired(self):
        self.child["analysisContext"]["automation"]["triggerStartupId"] = "previous-startup"
        self.save_child()
        self.b.process_auto_mission("restarted", self.child)
        self.assert_skipped("council_new_bar_previous_startup_skipped")

    def test_historical_audit_only_automatic_vote_is_retired(self):
        self.child["analysisContext"]["automation"]["executionPolicy"] = "audit_only_no_stale_dispatch"
        self.save_child()
        self.b.process_auto_mission("historical", self.child)
        self.assert_skipped("council_new_bar_historical_snapshot_skipped")

    def test_expired_start_window_never_calls_runner(self):
        self.child["analysisContext"]["automation"]["triggerExpiresAt"] = (
            datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        self.save_child()
        self.b.process_auto_mission("too-late", self.child)
        self.assert_skipped("council_new_bar_start_window_expired")

    def test_missing_future_or_overlong_admission_is_rejected(self):
        for change in (
            {"quotaAdmittedAt": None},
            {"triggerExpiresAt": None},
            {"quotaAdmittedAt": (datetime.now(timezone.utc) + timedelta(seconds=10)).isoformat()},
            {"triggerExpiresAt": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()},
        ):
            mission = copy.deepcopy(self.child)
            mission["analysisContext"]["automation"].update(change)
            with self.subTest(change=change):
                self.assertEqual(self.b._council_new_bar_start_error(mission),
                                 "council_new_bar_admission_invalid")

    def test_new_bar_or_timeframe_or_channel_change_rejects_old_trigger(self):
        current, _ = self.b._ai_trade_council_closed_bar_identity(
            self.b.metatrader_snapshot_read_model(self.b.AI_TRADE_COUNCIL_PROP_ID))
        for field, value in (("lastClosedBarTime", current["lastClosedBarTime"] + 300),
                             ("timeframe", "H1"), ("candidateId", "mtc-" + "x" * 26)):
            with self.subTest(field=field), mock.patch.object(
                self.b, "_ai_trade_council_closed_bar_identity",
                return_value=({**current, field: value}, "ready")):
                self.assertEqual(self.b._council_new_bar_start_error(self.child),
                                 "council_new_bar_no_longer_current")

    def test_unavailable_current_snapshot_fails_closed(self):
        with mock.patch.object(self.b, "metatrader_snapshot_read_model", side_effect=OSError("offline")):
            self.b.process_auto_mission("offline", self.child)
        self.assert_skipped("council_new_bar_current_snapshot_unavailable")

    def test_corrupt_current_snapshot_fails_closed(self):
        with mock.patch.object(self.b, "metatrader_snapshot_read_model",
                               side_effect=self.b.DataIntegrityError("corrupt")):
            self.b.process_auto_mission("corrupt", self.child)
        self.assert_skipped("council_new_bar_current_snapshot_unavailable")

    def test_immutable_snapshot_expires_before_60_second_admission_window(self):
        self.child["analysisContext"]["snapshotObservedAt"] = (
            datetime.now(timezone.utc) - timedelta(seconds=45)).isoformat()
        self.save_child()
        with mock.patch.object(self.b, "_read_mt4_trade_gateway_ea_status",
                               return_value=({"maxSnapshotAgeSeconds": 30}, None)):
            self.b.process_auto_mission("expired-snapshot", self.child)
        self.assert_skipped("council_new_bar_analysis_snapshot_expired_before_start")

    def test_unavailable_ea_age_limit_skips_without_model(self):
        with mock.patch.object(self.b, "_read_mt4_trade_gateway_ea_status", return_value=(None, None)):
            self.b.process_auto_mission("missing-age-limit", self.child)
        self.assert_skipped("council_new_bar_execution_age_limit_unavailable_before_start")

    def test_quota_recovers_midbar_but_failed_admission_is_not_replayed(self):
        with mock.patch.object(self.b, "codex_rate_limits", return_value={"ok": False, "stale": True}):
            self.b.process_auto_mission("quota-missing", self.child)
        self.assert_skipped("council_new_bar_gate_skipped_quota_unavailable_or_stale")
        # Restoration cannot resurrect the terminal Mission, even within 60s.
        self.b.process_auto_mission("quota-returned", self.stored())
        self.assert_skipped("council_new_bar_gate_skipped_quota_unavailable_or_stale")
        self.assertEqual(self.stored()["attemptCount"], 0)

    def test_every_transient_worker_gate_skips_instead_of_deferring(self):
        for reason in ("runner_busy", "runner_missing", "local_rate_limited",
                       "codex_limit_reached", "quota_below_reserve"):
            with self.subTest(reason=reason):
                self.b.replace_mission(copy.deepcopy(self.child))
                with mock.patch.object(self.b, "defer_auto_mission") as defer:
                    self.b._defer_auto_mission_with_round_deadline(self.child, reason, 1)
                defer.assert_not_called()
                self.assert_skipped("council_new_bar_gate_skipped_" + reason)

    def test_after_claim_expiry_does_not_spend_local_or_model_budget(self):
        original = self.b._council_new_bar_start_error
        calls = 0
        def expires_after_claim(mission):
            nonlocal calls
            calls += 1
            return original(mission) if calls == 1 else "council_new_bar_start_window_expired"
        with (mock.patch.object(self.b, "_council_new_bar_start_error", side_effect=expires_after_claim),
              mock.patch.object(self.b, "check_rate_limit", return_value=(True, 0)) as rate):
            self.b.process_auto_mission("expires-after-claim", self.child)
        self.assertEqual(calls, 2)
        self.assertTrue(rate.called)
        self.assertTrue(all(call.kwargs.get("consume") is False for call in rate.call_args_list))
        self.assert_skipped("council_new_bar_start_window_expired")
        self.assertEqual(self.stored()["attemptCount"], 1)

    def test_quota_loss_after_claim_does_not_spend_model_budget(self):
        quota_ok = {"ok": True, "stale": False, "limitReached": False,
                    "primary": {"usedPercent": 10, "remainingPercent": 90}}
        with (mock.patch.object(self.b, "codex_rate_limits",
                                side_effect=[quota_ok, {"ok": False, "stale": True}]),
              mock.patch.object(self.b, "check_rate_limit", return_value=(True, 0)) as rate):
            self.b.process_auto_mission("quota-race", self.child)
        self.assertEqual(self.stored()["status"], "blocked")
        self.assertTrue(self.stored()["errorCode"].startswith("council_new_bar_gate_skipped_"))
        self.assertTrue(all(call.kwargs.get("consume") is False for call in rate.call_args_list))
        self.runner.assert_not_called()
        self.dispatch.assert_not_called()

    def test_last_moment_expiry_never_starts_model(self):
        calls = 0
        def expires_before_process(_mission):
            nonlocal calls
            calls += 1
            return None if calls < 3 else "council_new_bar_start_window_expired"
        with mock.patch.object(self.b, "_council_new_bar_start_error", side_effect=expires_before_process):
            self.b.process_auto_mission("last-moment-expiry", self.child)
        self.assertEqual(calls, 3)
        self.assert_skipped("council_new_bar_start_window_expired")

    def test_provider_429_finishes_without_same_bar_retry(self):
        claimed = self.b.claim_auto_mission(self.child["id"], "newbar-provider")
        lease = claimed["execution"]["leaseId"]
        result = {
            "ok": False, "processOk": False, "processStarted": True,
            "status": "rate_limited", "workStatus": "rate_limited",
            "message": "Provider HTTP 429", "finalMessage": "429 Too Many Requests",
            "providerFailure": {"schemaVersion": "codex-provider-http-failure-v1",
                                "httpStatus": 429, "retryable": True, "retryAfterSeconds": 1},
        }
        finished = self.b.finish_auto_mission(self.child["id"], lease, {"processStarted": True}, result)
        self.assertEqual(finished["status"], "failed")
        self.assertNotIn("councilProviderRetry", finished)
        self.assertNotIn(finished["execution"]["dispatchState"], {"queued", "deferred"})
        self.assertEqual(finished["attemptCount"], 1)
        self.assertIsNone(self.b.claim_auto_mission(self.child["id"], "retry"))
        self.dispatch.assert_not_called()

    def test_stale_queued_snapshot_cannot_cancel_already_running_vote(self):
        claimed = self.b.claim_auto_mission(self.child["id"], "already-running")
        execution = claimed["execution"]
        execution["processStarted"] = True
        self.b.replace_mission(claimed)
        stale = copy.deepcopy(self.child)
        stale["analysisContext"]["automation"].pop("triggerPolicy")
        self.b.process_auto_mission("stale-worker", stale)
        self.assertEqual(self.stored()["status"], "running")
        self.assertEqual(self.stored()["execution"], execution)
        self.runner.assert_not_called()

    def successful_result(self, child):
        context = child["analysisContext"]
        role = context["roleId"]
        vote = {
            "snapshotId": context["snapshotId"], "agentId": context["agentId"], "roleId": role,
            "decision": "HOLD", "confidence": 82, "horizonBars": context["horizonBars"],
            "validUntilBarTime": context["validUntilBarTime"], "stopLossPrice": None, "takeProfitPrice": None,
            "indicatorValidation": "PASS" if role == "technical" else None,
            "volatilityState": context["volatilityState"] if role == "technical" else None,
            "eventRisk": "HOLD" if role == "news" else None,
            "horizon": "next closed bar", "observations": [role + ": exact frozen snapshot"],
            "invalidation": "new closed bar",
            "evidence": [{"label": "snapshot", "observedAt": self.b.utc_now(), "sourceUrl": None}],
            "warnings": [],
        }
        return {"ok": True, "status": "completed", "workStatus": "completed",
                "processStarted": True, "finalMessage": json.dumps(vote)}

    def automatic_children(self):
        parent = self.b.find_mission(self.child["parentMissionId"])
        parent["analysisContext"]["automation"] = copy.deepcopy(self.child["analysisContext"]["automation"])
        self.b.replace_mission(parent)
        children = [row for row in self.b.load_missions()
                    if row.get("parentMissionId") == self.child["parentMissionId"]]
        for child in children:
            child["analysisContext"]["automation"] = copy.deepcopy(self.child["analysisContext"]["automation"])
            self.b._issue_backend_auto_safe_authorization(child)
            self.b.replace_mission(child)
        return children

    def queued_coverage(self):
        context = self.child["analysisContext"]
        self.b._save_ai_trade_council_coverage_records([{
            **context["closedBarIdentity"],
            "snapshotId": context["snapshotId"],
            "snapshotArtifact": context["snapshotArtifact"],
            "snapshotArtifactDigest": context["snapshotArtifactDigest"],
            "detectedAt": self.b.utc_now(),
            "executionPolicy": "current_exact_snapshot",
            "missionId": self.child["parentMissionId"], "status": "queued",
            "reasonCode": "analysis_queued",
        }])

    def test_all_three_unstarted_skips_are_audited_as_skipped_not_analyzed(self):
        children = self.automatic_children()
        self.queued_coverage()
        for child in children:
            self.b._defer_auto_mission_with_round_deadline(child, "codex_limit_reached", 1)
        parent = self.b.find_mission(self.child["parentMissionId"])
        reason = "council_new_bar_gate_skipped_codex_limit_reached"
        self.assertEqual(parent["phase"], "council_bar_skipped")
        self.assertEqual(parent["councilSkipReasonCode"], reason)
        store = self.b.load_ai_trade_council_automation_store()
        coverage = next(row for row in store["state"]["coverageRecords"]
                        if row.get("missionId") == parent["id"])
        self.assertEqual(coverage["status"], "skipped")
        self.assertEqual(coverage["reasonCode"], reason)
        self.assertIsNone(store["state"].get("lastAnalyzedClosedBarTime"))
        history = self.b._ai_trade_council_analysis_history_read_model(
            self.b.load_missions(), {"items": []}, scope={"mode": "all"})
        row = next(row for row in history["items"] if row.get("missionId") == parent["id"])
        self.assertEqual(row["coverageStatus"], "skipped")
        self.assertEqual(row["skipReasonCode"], reason)
        self.assertEqual(row["completeness"]["completedVotes"], 0)
        self.assertEqual(sum(row.get("missionId") == parent["id"] for row in history["items"]), 1)
        self.runner.assert_not_called()
        self.dispatch.assert_not_called()

    def test_partially_analyzed_round_is_not_relabelled_as_wholly_skipped(self):
        children = self.automatic_children()
        self.queued_coverage()
        claimed = self.b.claim_auto_mission(children[0]["id"], "partial-real-vote")
        self.b.finish_auto_mission(claimed["id"], claimed["execution"]["leaseId"],
                                   {"processStarted": True}, self.successful_result(claimed))
        for child in children[1:]:
            self.b._defer_auto_mission_with_round_deadline(child, "codex_limit_reached", 1)
        parent = self.b.find_mission(self.child["parentMissionId"])
        self.assertNotIn("councilSkipReasonCode", parent)
        history = self.b._ai_trade_council_analysis_history_read_model(
            self.b.load_missions(), {"items": []}, scope={"mode": "all"})
        row = next(row for row in history["items"] if row.get("missionId") == parent["id"])
        self.assertEqual(row["coverageStatus"], "analyzed")
        self.assertEqual(row["completeness"]["completedVotes"], 1)
        self.assertIsNone(row["skipReasonCode"])
        self.dispatch.assert_not_called()

    def test_skip_projection_requires_all_three_roles_and_no_started_process(self):
        children = self.automatic_children()
        parent = self.b.find_mission(self.child["parentMissionId"])
        for child in children:
            child.update(status="blocked", errorCode="council_new_bar_gate_skipped_runner_busy")
            child["execution"].update(newBarSkipped=True, processStarted=False)
        self.assertEqual(self.b._ai_trade_council_unstarted_skip_reason(parent, children),
                         "council_new_bar_gate_skipped_runner_busy")
        self.assertIsNone(self.b._ai_trade_council_unstarted_skip_reason(parent, children[:2]))
        children[0]["execution"]["processStarted"] = True
        self.assertIsNone(self.b._ai_trade_council_unstarted_skip_reason(parent, children))

    def test_picker_retires_future_legacy_retries_so_parent_cannot_block_next_bar(self):
        children = self.automatic_children()
        self.queued_coverage()
        for child in children:
            child["analysisContext"]["automation"].pop("triggerPolicy")
            child["execution"].update(dispatchState="deferred", nextAttemptAt=(
                datetime.now(timezone.utc) + timedelta(hours=1)).isoformat())
            self.b._issue_backend_auto_safe_authorization(child)
            self.b.replace_mission(child)
        self.assertIsNotNone(self.b._active_ai_trade_council_parent())
        self.assertIsNone(self.b.find_next_auto_mission(council_only=True))
        self.assertIsNone(self.b._active_ai_trade_council_parent())
        for child in children:
            stored = self.b.find_mission(child["id"])
            self.assertEqual(stored["errorCode"], "council_legacy_automatic_backlog_skipped")
            self.assertIsNone(stored["execution"]["nextAttemptAt"])
        self.runner.assert_not_called()
        self.dispatch.assert_not_called()

    def test_picker_retires_new_policy_deferral_without_waiting_for_retry_time(self):
        children = self.automatic_children()
        for child in children:
            child["execution"].update(dispatchState="deferred", nextAttemptAt=(
                datetime.now(timezone.utc) + timedelta(hours=1)).isoformat())
            self.b.replace_mission(child)
        self.assertIsNone(self.b.find_next_auto_mission(council_only=True))
        self.assertIsNone(self.b._active_ai_trade_council_parent())
        self.assertEqual(self.stored()["errorCode"], "council_new_bar_deferred_attempt_skipped")
        self.runner.assert_not_called()

    def test_retirement_preserves_manual_future_retry_and_running_automatic_vote(self):
        children = self.automatic_children()
        running = self.b.claim_auto_mission(children[0]["id"], "already-running")
        manual = children[1]
        manual["analysisContext"].pop("automation")
        manual["execution"].update(dispatchState="deferred", nextAttemptAt=(
            datetime.now(timezone.utc) + timedelta(hours=1)).isoformat())
        self.b._issue_backend_auto_safe_authorization(manual)
        self.b.replace_mission(manual)
        old = children[2]
        old["analysisContext"]["automation"].pop("triggerPolicy")
        self.b._issue_backend_auto_safe_authorization(old)
        self.b.replace_mission(old)
        self.assertEqual(self.b._retire_council_automatic_backlog(), 1)
        self.assertEqual(self.b.find_mission(running["id"]), running)
        self.assertEqual(self.b.find_mission(manual["id"]), manual)
        self.assertEqual(self.b.find_mission(old["id"])["status"], "blocked")
        self.runner.assert_not_called()

    def test_three_valid_current_votes_start_once_and_completed_rows_are_preserved(self):
        children = self.automatic_children()
        self.dispatch.return_value = {"status": "no_trade", "reasonCode": "consensus_threshold_not_met",
                                      "commandPublished": False}
        def complete_runner(command, **_kwargs):
            mission_id = command[command.index("--mission-id") + 1]
            child = self.b.find_mission(mission_id)
            return {"ok": True, "output": json.dumps(self.successful_result(child)),
                    "processStarted": True, "exitCode": 0}
        self.runner.side_effect = complete_runner
        for child in children:
            self.b.process_auto_mission("newbar-" + child["owner"], child)
            stored = self.b.find_mission(child["id"])
            self.assertEqual(stored["status"], "completed", (stored.get("errorCode"), stored.get("result")))
            self.assertEqual(stored["attemptCount"], 1)
            before = copy.deepcopy(stored)
            self.b.process_auto_mission("stale-picker", child)
            self.assertEqual(self.b.find_mission(child["id"]), before)
        self.assertEqual(self.runner.call_count, 3)
        parent = self.b.find_mission(self.child["parentMissionId"])
        self.assertEqual(parent["status"], "completed")
        self.assertEqual(parent["councilDecision"]["voteCount"], 3)
        self.dispatch.assert_called_once()

    def test_late_running_result_remains_recorded_but_round_deadline_still_fails(self):
        children = self.automatic_children()
        claimed = [self.b.claim_auto_mission(child["id"], "already-running") for child in children]
        parent_id = self.child["parentMissionId"]
        parent = self.b.find_mission(parent_id)
        parent["analysisContext"]["roundDeadlineAt"] = (
            datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        self.b.replace_mission(parent)
        self.dispatch.return_value = {"status": "blocked_before_publish",
                                      "reasonCode": "council_round_deadline_expired", "commandPublished": False}
        for child in claimed:
            result = self.b.finish_auto_mission(child["id"], child["execution"]["leaseId"],
                                               {"processStarted": True}, self.successful_result(child))
            self.assertEqual(result["status"], "completed")
        parent = self.b.find_mission(parent_id)
        self.assertEqual(parent["councilDecision"]["voteCount"], 3)
        self.assertIn("round_deadline_expired", parent["councilDecision"]["qualityGate"]["reasonCodes"])
        self.assertFalse(parent["councilDecision"]["qualityGate"]["passed"])
        self.runner.assert_not_called()

    def test_manual_round_keeps_its_own_deadline_policy(self):
        self.child["analysisContext"].pop("automation")
        self.save_child()
        with mock.patch.object(self.b, "metatrader_snapshot_read_model") as current:
            self.assertIsNone(self.b._council_new_bar_start_error(self.child))
        current.assert_not_called()
        deferred = self.b._defer_auto_mission_with_round_deadline(self.child, "runner_busy", 1)
        self.assertEqual(deferred["status"], "queued")
        self.assertEqual(deferred["execution"]["dispatchState"], "deferred")


if __name__ == "__main__":
    unittest.main()
