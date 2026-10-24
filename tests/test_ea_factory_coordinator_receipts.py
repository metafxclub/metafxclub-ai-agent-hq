"""Coordinator acknowledgements must not block on the UI's full projection."""
import copy
import unittest
from contextlib import ExitStack
from unittest import mock

import test_ea_factory_backend as backend_support


class EaFactoryCoordinatorReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = backend_support.load_bridge()

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stage = {"id": "generate_source", "status": "pending", "missionId": None,
                      "reportId": None, "manualRetryCount": 0, "manualRetryHistory": []}
        self.build = {
            "id": "ea-build-coordinator-receipt", "coverageStatus": "compact_current",
            "platform": "mt5", "artifactKind": "expert_advisor", "versions": [],
            "stages": [{"id": "strategy_spec", "status": "completed"}, self.stage],
            "sourceReportId": "report-source-fixture", "sourceRecordId": "source-fixture",
            "sourceRecordDigest": "a" * 64, "createRequestDigest": "b" * 64,
            "brief": "Immutable fixture", "status": "ready",
        }
        self.state = {"builds": [self.build]}
        self.missions = []
        self.commits = []
        self.patch("_load_ea_factory_state_unlocked", return_value=self.state)
        self.patch("load_missions", side_effect=lambda **_kw: self.missions)
        self.patch("_ea_factory_sync_build_status", return_value=False)
        self.active = self.patch("_ea_factory_active_worker_payload", return_value=None)
        self.patch("_ea_factory_current_thread_owns_active_stage", return_value=False)
        self.source_exists = self.patch("_ea_factory_source_program_exists", return_value=False)
        self.patch("_ea_factory_recover_legacy_runner_writer_failure", return_value=None)
        self.patch("_ea_factory_recover_false_approval_stage_mission", return_value=None)
        self.locks = self.patch("_ea_factory_require_top_header_locks")
        self.advance_allowed = self.patch("_ea_factory_stage_can_advance", return_value=True)
        self.patch("_ea_factory_build_current_stage_id", return_value="generate_source")
        self.patch("_ea_factory_generation_brief", return_value="Exact fixture generation contract")
        self.patch("deliver_dashboard_report", return_value={"mission": {"id": "mission-transfer"}})
        self.dispatch = self.patch("run_dashboard_workflow_action", side_effect=self.dispatched)
        self.write = self.patch("_write_ea_factory_state_unlocked", side_effect=lambda value: self.commits.append(copy.deepcopy(value)))
        self.patch("append_audit")
        self.patch("mission_read_model_item", side_effect=lambda value: copy.deepcopy(value))
        self.patch("report_read_model_item", side_effect=lambda value: copy.deepcopy(value))
        self.full = {"schemaVersion": "ea-factory-v1", "builds": [{"id": self.build["id"], "projection": "full"}]}
        self.model = self.patch("ea_factory_read_model", return_value=self.full)
        self.project_build = self.patch("_ea_factory_build_read_model", return_value=self.full["builds"][0])

    def patch(self, name, **kwargs):
        return self.stack.enter_context(mock.patch.object(self.bridge, name, **kwargs))

    def dispatched(self, _prop, payload, **_kwargs):
        mission = {"id": "mission-committed-generation", "status": "queued",
                   "idempotencyKey": payload["idempotencyKey"]}
        self.missions.append(mission)
        return {"ok": True, "mission": mission}

    def advance(self, **kwargs):
        return self.bridge.advance_ea_factory_build(
            self.build["id"], {"stageId": "generate_source", "idempotencyKey": "advance-client-key"}, **kwargs
        )

    def retry(self, **kwargs):
        return self.bridge.retry_ea_factory_build_stage(
            self.build["id"], {"stageId": "generate_source", "failedMissionId": "mission-failed-source",
                               "idempotencyKey": "retry-client-key"}, **kwargs
        )

    def failed_source(self):
        self.stage.update(status="failed", missionId="mission-failed-source", blockedReasonCode="invalid_output")
        self.missions.append({"id": "mission-failed-source", "status": "failed", "errorCode": "invalid_output"})

    def assert_receipt(self, response):
        persisted = self.commits[-1]["builds"][0]["stages"][1]
        self.assertEqual(response["buildId"], self.build["id"])
        self.assertEqual(response["stageId"], persisted["id"])
        self.assertEqual(response["missionId"], persisted["missionId"])
        self.assertEqual(response["reportId"], persisted.get("reportId"))
        self.assertEqual(response["build"], {"id": self.build["id"]})
        self.assertEqual(response["mission"], {"id": persisted["missionId"]})
        for key in ("id", "status", "missionId", "reportId", "requestDigest", "requestIdempotencyKey"):
            self.assertEqual(response["stage"][key], persisted.get(key))
        self.assertNotIn("eaFactory", response)
        self.assertNotIn("canRun", response["build"])
        self.assertFalse(response["eaFactoryReadResult"]["readinessConfirmed"])
        self.model.assert_not_called()
        self.project_build.assert_not_called()

    def test_compact_advance_returns_committed_identity_without_any_projection(self):
        self.model.side_effect = AssertionError("Full projection must not block coordinator")
        self.project_build.side_effect = AssertionError("Build projection must not block coordinator")
        response = self.advance(include_read_model=False)
        self.assert_receipt(response)
        self.assertFalse(response["idempotentReplay"])
        self.dispatch.assert_called_once()
        self.assertEqual(len(self.commits), 2)
        self.assertEqual(self.commits[0]["builds"][0]["stages"][1]["status"], "pending")
        self.assertEqual(self.commits[-1]["builds"][0]["stages"][1]["status"], "queued")

    def test_compact_replay_keeps_same_mission_without_projection_or_redispatch(self):
        first = self.advance(include_read_model=False)
        response = self.advance(include_read_model=False)
        self.assert_receipt(response)
        self.assertTrue(response["idempotentReplay"])
        self.assertEqual(response["missionId"], first["missionId"])
        self.dispatch.assert_called_once()

    def test_public_default_advance_keeps_full_response_contract(self):
        response = self.advance()
        self.model.assert_called_once_with()
        self.assertEqual(response["eaFactory"], self.full)
        self.assertEqual(response["build"]["projection"], "full")

    def test_compact_retry_commits_one_receipt_and_propagates_compact_to_advance(self):
        self.failed_source()
        self.model.side_effect = AssertionError("Full projection must not block retry")
        response = self.retry(include_read_model=False)
        self.assert_receipt(response)
        self.assertEqual(response["kind"], "ea_factory_stage_retry_dispatched")
        self.assertEqual(response["retry"]["attempt"], 1)
        self.assertTrue(response["retry"]["freshMission"])
        self.assertEqual(self.stage["manualRetryCount"], 1)
        self.assertEqual(self.stage["manualRetryHistory"][0]["failedMissionId"], "mission-failed-source")
        self.dispatch.assert_called_once()

    def test_public_default_retry_still_returns_full_projection(self):
        self.failed_source()
        response = self.retry()
        self.model.assert_called_once_with()
        self.assertEqual(response["eaFactory"], self.full)

    def test_compact_early_stage_replay_avoids_read_projection_during_other_work(self):
        self.advance(include_read_model=False)
        self.active.return_value = {"buildId": "ea-build-other", "stageId": "generate_source"}
        response = self.advance(include_read_model=False)
        self.assert_receipt(response)
        self.assertTrue(response["idempotentReplay"])
        self.dispatch.assert_called_once()

    def test_compact_retry_replay_during_bound_work_never_resets_or_redispatches(self):
        self.failed_source()
        self.retry(include_read_model=False)
        self.active.return_value = {"buildId": self.build["id"], "stageId": "generate_source",
                                    "missionId": self.stage["missionId"]}
        response = self.retry(include_read_model=False)
        self.assert_receipt(response)
        self.assertTrue(response["idempotentReplay"])
        self.assertEqual(self.stage["manualRetryCount"], 1)
        self.dispatch.assert_called_once()

    def test_compact_option_does_not_bypass_precommit_admission(self):
        for gate in ("legacy", "coverage_upgrade", "top_lock", "busy", "stage_order"):
            with self.subTest(gate=gate):
                self.build["coverageStatus"] = "legacy" if gate == "legacy" else "compact_current"
                self.build["coverageUpgradeRequired"] = gate == "coverage_upgrade"
                self.locks.side_effect = self.bridge.RequestError("missing lock", 409) if gate == "top_lock" else None
                self.active.return_value = {"buildId": "ea-build-other", "stageId": "generate_source"} if gate == "busy" else None
                self.advance_allowed.return_value = gate != "stage_order"
                with self.assertRaises(self.bridge.RequestError):
                    self.advance(include_read_model=False)
                self.write.assert_not_called()
                self.dispatch.assert_not_called()
                self.model.assert_not_called()

    def test_compact_option_is_not_accepted_as_untrusted_payload_field(self):
        with self.assertRaises(self.bridge.RequestError):
            self.bridge.advance_ea_factory_build(self.build["id"], {
                "stageId": "generate_source", "idempotencyKey": "request", "include_read_model": False,
            })
        with self.assertRaises(self.bridge.RequestError):
            self.bridge.retry_ea_factory_build_stage(self.build["id"], {
                "stageId": "generate_source", "failedMissionId": "mission-failed-source",
                "idempotencyKey": "retry", "include_read_model": False,
            })
        self.write.assert_not_called()
        self.dispatch.assert_not_called()

    def test_compact_retry_preserves_lock_exact_failure_source_and_budget_guards(self):
        self.failed_source()
        for gate in ("top_lock", "wrong_mission", "source_exists", "retry_budget", "not_invalid_output"):
            with self.subTest(gate=gate):
                self.locks.side_effect = self.bridge.RequestError("missing lock", 409) if gate == "top_lock" else None
                self.stage["missionId"] = "mission-different" if gate == "wrong_mission" else "mission-failed-source"
                self.stage["blockedReasonCode"] = "model_unavailable" if gate == "not_invalid_output" else "invalid_output"
                self.source_exists.return_value = gate == "source_exists"
                self.stage["manualRetryHistory"] = [
                    {"idempotencyKey": f"previous-{i}", "attempt": i + 1}
                    for i in range(3)
                ] if gate == "retry_budget" else []
                with self.assertRaises(self.bridge.RequestError):
                    self.retry(include_read_model=False)
                self.write.assert_not_called()
                self.dispatch.assert_not_called()
                self.model.assert_not_called()

    def test_failed_dispatch_never_manufactures_a_committed_success_receipt(self):
        self.dispatch.side_effect = None
        self.dispatch.return_value = {"ok": False}
        with self.assertRaises(self.bridge.RequestError):
            self.advance(include_read_model=False)
        self.assertEqual(len(self.commits), 1)  # Only the original durable reservation.
        self.assertEqual(self.stage["status"], "pending")
        self.assertIsNone(self.stage["missionId"])
        self.model.assert_not_called()

    def test_worker_requests_only_compact_acknowledgements_then_rechecks_stage(self):
        actions = [{"kind": "advance", "stageId": "generate_source", "runId": "ea-run-exact"},
                   {"kind": "retry_source", "failedMissionId": "mission-failed-source", "attempt": 1, "runId": "ea-run-exact"},
                   {"kind": "stop"}]
        for action in actions[:2]:
            action["_expectedRunSnapshot"] = {"runId": "ea-run-exact"}
        with (
            mock.patch.object(self.bridge, "_ea_factory_one_click_next_action", side_effect=actions) as next_action,
            mock.patch.object(self.bridge, "advance_ea_factory_build", return_value={"ok": True}) as advance,
            mock.patch.object(self.bridge, "retry_ea_factory_build_stage", return_value={"ok": True}) as retry,
            mock.patch.object(self.bridge, "_ea_factory_one_click_finish") as finish,
        ):
            self.bridge._ea_factory_one_click_worker(self.build["id"])
        self.assertEqual(next_action.call_count, 3)
        advance.assert_called_once()
        retry.assert_called_once()
        self.assertEqual(advance.call_args.kwargs, {"include_read_model": False, "expected_run_id": "ea-run-exact"})
        self.assertEqual(retry.call_args.kwargs, {"include_read_model": False, "expected_run_id": "ea-run-exact"})
        self.assertEqual(retry.call_args.args[1]["failedMissionId"], "mission-failed-source")
        self.model.assert_not_called()
        finish.assert_not_called()


if __name__ == "__main__":
    unittest.main()
