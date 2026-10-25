"""Retired market paths must never compete with Sentiment Universe.

All mutable state is temporary. Collectors, processes, and HTTP providers are
mocked; the HTTP tests call the handler directly without opening a socket.
"""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

import test_radar_batch_repair_lifecycle as lifecycle


REASON = "replaced_by_sentiment_universe"
LEGACY_ACTIONS = (
    "analyze_fx28_trends", "save_news_bias_schedule",
    "refresh_daily_market_news", "analyze_daily_market_news", "build_fx_pair_bias",
)


class MarketPipelineRetirementTests(unittest.TestCase):
    runtime = lifecycle.RadarBatchRepairLifecycleTests.runtime
    setUp = lifecycle.RadarBatchRepairLifecycleTests.setUp

    @classmethod
    def setUpClass(cls):
        cls.bridge = lifecycle.load_module("market_pipeline_retirement_bridge", lifecycle.BRIDGE_PATH)

    def assert_retired_error(self, callback):
        with self.assertRaises(self.bridge.RequestError) as caught:
            callback()
        self.assertEqual(caught.exception.status, 410)
        self.assertEqual(str(caught.exception), REASON)

    @staticmethod
    def mission(action, status="queued", *, identity="old-market", prop="left_signal_cube"):
        return {
            "id": identity, "status": status, "toolId": "codex_web_research",
            "executionMode": "auto_guarded", "autoEligible": True,
            "workflowContext": {
                "schemaVersion": "dashboard-workflow-lineage-v1", "propId": prop,
                "actionId": action, "inputs": {}, "inputDigest": "0" * 64,
                "submittedAt": "2026-10-25T01:00:00Z", "triggerSource": "schedule",
            },
        }

    def test_fresh_and_upgraded_settings_cannot_enable_legacy_news(self):
        self.assertFalse(self.bridge._default_dashboard_workflow_settings()["newsBiasSchedule"]["requestedEnabled"])
        old = {
            "newsBiasSchedule": {
                "requestedEnabled": True, "times": ["00:00", "12:00"],
                "directServiceVersion": 3, "savedAt": "2026-10-24T00:00:00Z",
                "pendingSlotKey": "newsBiasSchedule:2026-10-25:1200",
                "pendingScheduledAt": "2026-10-25T05:00:00Z",
            },
            "fx28TrendSchedule": {"requestedEnabled": True},
        }
        for value in ({}, old, self.bridge._default_dashboard_workflow_settings()):
            with self.subTest(value=value):
                shaped = self.bridge._dashboard_workflow_settings_shape(value)
                news = shaped["newsBiasSchedule"]
                self.assertFalse(news["requestedEnabled"])
                self.assertFalse(news.get("pendingSlotKey"))
                self.assertFalse(news.get("pendingScheduledAt"))
                self.assertEqual(news.get("retirementReason"), REASON)
                if "fx28TrendSchedule" in shaped:
                    self.assertFalse(shaped["fx28TrendSchedule"]["requestedEnabled"])
                # Re-reading the normalized data must not resurrect old work.
                self.assertEqual(self.bridge._dashboard_workflow_settings_shape(shaped), shaped)
                for active in ("discoverySchedule", "indicatorScoutSchedule"):
                    self.assertTrue(shaped[active]["requestedEnabled"])
                    self.assertEqual(shaped[active]["times"], ["09:00"])

    def test_legacy_news_has_no_scheduler_job_but_radar_and_discovery_remain(self):
        keys = {job["settingsKey"] for job in self.bridge.DASHBOARD_WORKFLOW_SCHEDULE_JOBS}
        self.assertNotIn("newsBiasSchedule", keys)
        self.assertNotIn("fx28TrendSchedule", keys)
        self.assertTrue({"indicatorScoutSchedule", "discoverySchedule"}.issubset(keys))

    def test_manual_and_trusted_schedule_actions_reject_before_dispatch(self):
        with mock.patch.object(self.bridge, "run_bridge_task") as runner, \
             mock.patch.object(self.bridge, "find_room_prop") as lookup:
            for action in LEGACY_ACTIONS:
                for trigger in (None, "schedule"):
                    with self.subTest(action=action, trigger=trigger):
                        kwargs = {"trusted_trigger_source": trigger} if trigger else {}
                        self.assert_retired_error(lambda: self.bridge.run_dashboard_workflow_action(
                            "left_signal_cube", {"actionId": action, "form": {}}, **kwargs))
        runner.assert_not_called()
        lookup.assert_not_called()

    def test_direct_refresh_and_schedule_cannot_fetch_or_save(self):
        with mock.patch.object(self.bridge.fx_news_direct, "collect_official_sources") as fetch, \
             mock.patch.object(self.bridge, "_save_fx_daily_news_direct_store") as write, \
             mock.patch.object(self.bridge, "_save_dashboard_schedule_preference") as schedule, \
             mock.patch.object(self.bridge, "run_safe_command") as runner:
            self.assert_retired_error(lambda: self.bridge.refresh_deterministic_daily_fx_news(trigger_source="schedule"))
            self.assert_retired_error(lambda: self.bridge.save_direct_daily_fx_news_schedule({"enabled": True, "times": ["12:00"]}))
        for operation in (fetch, write, schedule, runner):
            operation.assert_not_called()

    def test_http_legacy_news_routes_return_410_without_provider_calls(self):
        for path, payload in (
            ("/api/props/left_signal_cube/news/refresh", {}),
            ("/api/props/left_signal_cube/news/schedule", {"enabled": True, "times": ["12:00"]}),
        ):
            with self.subTest(path=path):
                handler = self.bridge.BridgeHandler.__new__(self.bridge.BridgeHandler)
                handler.path = path
                handler.validate_local_request = mock.Mock()
                handler.validate_full_agent_mutation_request = mock.Mock()
                handler.read_payload = mock.Mock(return_value=payload)
                handler.send_json_disconnect_safe = mock.Mock()
                handler.send_result = mock.Mock()
                with mock.patch.object(self.bridge.fx_news_direct, "collect_official_sources") as fetch, \
                     mock.patch.object(self.bridge, "run_safe_command") as runner:
                    handler.do_POST()
                response = handler.send_json_disconnect_safe.call_args
                self.assertIsNotNone(response)
                self.assertEqual(response.kwargs["status"], 410)
                self.assertIn(REASON, json.dumps(response.args[0]))
                handler.send_result.assert_not_called()
                fetch.assert_not_called()
                runner.assert_not_called()

    def test_fx_tick_cannot_collect_refresh_quota_or_admit_mission(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder), \
             mock.patch.object(self.bridge, "_fx_trend_collect") as collect, \
             mock.patch.object(self.bridge, "_dashboard_workflow_scheduler_gate") as quota, \
             mock.patch.object(self.bridge, "run_dashboard_workflow_action") as dispatch, \
             mock.patch.object(self.bridge, "run_safe_command") as runner:
            for hour in (0, 1, 8, 12, 23):
                result = self.bridge.fx_trend_service_tick(now=datetime(2026, 10, 25, hour, tzinfo=timezone.utc))
                self.assertEqual(result["status"], "retired")
                self.assertEqual(result["reasonCode"], REASON)
            self.assertEqual(self.bridge.load_missions(), [])
        for operation in (collect, quota, dispatch, runner):
            operation.assert_not_called()

    def test_direct_legacy_collector_is_closed_even_if_invoked_outside_tick(self):
        with mock.patch.object(self.bridge, "run_safe_command") as runner:
            self.assert_retired_error(lambda: self.bridge._fx_trend_collect({}))
        runner.assert_not_called()

    def test_daily_admission_is_passive_and_preserves_archival_input(self):
        store = {"model": {"status": "ready", "snapshotId": "archived"},
                 "ai": {"status": "completed", "missionId": "old-daily"}, "history": [{"snapshotId": "old"}]}
        before = copy.deepcopy(store)
        with mock.patch.object(self.bridge, "find_mission_by_idempotency") as find, \
             mock.patch.object(self.bridge, "_dashboard_workflow_scheduler_gate") as quota, \
             mock.patch.object(self.bridge, "run_dashboard_workflow_action") as dispatch:
            result = self.bridge._fx_trend_daily_admission(store, datetime(2026, 10, 25, 12, tzinfo=timezone.utc))
        self.assertEqual(store, before)
        self.assertEqual(result["ai"]["status"], "retired")
        self.assertEqual(result["model"], before["model"])
        self.assertEqual(result["history"], before["history"])
        for operation in (find, quota, dispatch):
            operation.assert_not_called()

    def test_dashboard_start_creates_only_shared_scheduler_not_fx_thread(self):
        created = []
        def make_thread(*args, **kwargs):
            thread = mock.Mock()
            thread.is_alive.return_value = True
            created.append(kwargs)
            return thread
        with mock.patch.object(self.bridge, "DASHBOARD_WORKFLOW_SCHEDULER_THREAD", None), \
             mock.patch.object(self.bridge, "FX_TREND_THREAD", None), \
             mock.patch.object(self.bridge, "_dashboard_workflow_scheduler_runtime_update"), \
             mock.patch.object(self.bridge.threading, "Thread", side_effect=make_thread):
            first = self.bridge.start_dashboard_workflow_scheduler()
            self.assertIs(self.bridge.start_dashboard_workflow_scheduler(), first)
        self.assertEqual([row["name"] for row in created], ["metafx-dashboard-workflow-scheduler"])
        self.assertEqual(created[0]["target"], self.bridge.dashboard_workflow_scheduler_loop)

    def test_retired_mission_detection_does_not_match_radar_or_council(self):
        for action in LEGACY_ACTIONS:
            self.assertTrue(self.bridge._legacy_market_mission_retired(self.mission(action)))
        for prop, action in (("left_audit_crystals", "discover_new_indicators"),
                             ("codex_mcp_portal", "discover_trading_systems"),
                             ("ai_trade_council", "analyze_ai_trade_council")):
            self.assertFalse(self.bridge._legacy_market_mission_retired(self.mission(action, prop=prop)))
        self.assertFalse(self.bridge._legacy_market_mission_retired({"toolId": "codex_web_research", "detail": "FX28"}))

    def test_upgrade_cancels_only_unstarted_legacy_work_and_is_idempotent(self):
        queued = self.mission("analyze_fx28_trends", identity="old-queued")
        approval = self.mission("refresh_daily_market_news", "waiting_approval", identity="old-approval")
        approval["approval"] = {"required": True, "state": "pending"}
        approval["execution"] = {"nextAttemptAt": "2026-10-25T05:00:00Z", "dispatchState": "deferred"}
        untouched = [
            self.mission("analyze_fx28_trends", "completed", identity="old-complete"),
            self.mission("analyze_fx28_trends", "running", identity="old-running"),
            self.mission("discover_new_indicators", identity="radar", prop="left_audit_crystals"),
            self.mission("analyze_ai_trade_council", identity="council", prop="ai_trade_council"),
        ]
        before = copy.deepcopy(untouched)
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder), \
             mock.patch.object(self.bridge, "run_safe_command") as runner, \
             mock.patch.object(self.bridge, "codex_rate_limits") as quota:
            self.bridge.save_missions([queued, approval, *untouched])
            self.assertEqual(self.bridge._retire_legacy_market_pending_missions(), 2)
            records = {row["id"]: row for row in self.bridge.load_missions()}
            for identity in ("old-queued", "old-approval"):
                retired = records[identity]
                self.assertEqual(retired["status"], "cancelled")
                self.assertEqual(retired["errorCode"], REASON)
                self.assertFalse(retired["autoEligible"])
                self.assertIsNone(retired["execution"]["nextAttemptAt"])
            self.assertEqual(records["old-approval"]["approval"]["state"], "invalidated")
            for original in before:
                self.assertEqual(records[original["id"]], original)
            first_pass = copy.deepcopy(self.bridge.load_missions())
            self.assertEqual(self.bridge._retire_legacy_market_pending_missions(), 0)
            self.assertEqual(self.bridge.load_missions(), first_pass)
        runner.assert_not_called()
        quota.assert_not_called()

    def test_create_rejects_legacy_lineage_before_persisting_or_dispatch(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder), \
             mock.patch.object(self.bridge, "save_missions") as save, \
             mock.patch.object(self.bridge, "run_safe_command") as runner:
            for action in LEGACY_ACTIONS:
                with self.subTest(action=action):
                    self.assert_retired_error(lambda: self.bridge.create_mission(
                        {"prompt": "Archived market request"},
                        workflow_context=self.mission(action)["workflowContext"],
                    ))
        save.assert_not_called()
        runner.assert_not_called()

    def test_manual_approval_execution_and_auto_authorization_reject_legacy_work(self):
        mission = self.mission("analyze_fx28_trends", "waiting_approval")
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder), \
             mock.patch.object(self.bridge, "run_safe_command") as runner, \
             mock.patch.object(self.bridge, "codex_rate_limits") as quota:
            self.bridge.save_missions([mission])
            before = copy.deepcopy(self.bridge.load_missions())
            approved = self.bridge.approve_mission(mission["id"], {"decision": "approve"})
            executed = self.bridge.execute_mission(mission["id"], {"confirmMissionId": mission["id"]})
            for result in (approved, executed):
                self.assertEqual(result["_httpStatus"], 410)
                self.assertEqual(result["kind"], REASON)
            self.assertEqual(self.bridge.auto_execution_authorization_error(mission), REASON)
            self.assertEqual(self.bridge.load_missions(), before)
        runner.assert_not_called()
        quota.assert_not_called()

    def test_restored_queue_cannot_acquire_worker_lease(self):
        mission = self.mission("analyze_fx28_trends")
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder), \
             mock.patch.object(self.bridge, "auto_execution_authorization_error") as authorize, \
             mock.patch.object(self.bridge, "run_safe_command") as runner:
            self.bridge.save_missions([mission])
            self.assertIsNone(self.bridge.claim_auto_mission(mission["id"], "retirement-test-worker"))
            rejected = self.bridge.find_mission(mission["id"])
            self.assertNotEqual(rejected["status"], "running")
            self.assertFalse((rejected.get("execution") or {}).get("leaseId"))
        authorize.assert_not_called()
        runner.assert_not_called()

    def test_worker_entry_retires_restored_queue_without_configuration_or_quota(self):
        mission = self.mission("analyze_fx28_trends")
        stop = mock.Mock()
        stop.is_set.return_value = False
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder), \
             mock.patch.object(self.bridge, "MISSION_WORKER_STOP", stop), \
             mock.patch.object(self.bridge, "mission_worker_config") as config, \
             mock.patch.object(self.bridge, "codex_rate_limits") as quota, \
             mock.patch.object(self.bridge, "run_safe_command") as runner:
            self.bridge.save_missions([mission])
            self.bridge.process_auto_mission("retirement-test-worker", mission)
            self.assertEqual(self.bridge.find_mission(mission["id"])["status"], "cancelled")
        for operation in (config, quota, runner):
            operation.assert_not_called()

    def test_runtime_upgrade_persists_disabled_settings_and_retirement_marker(self):
        mission = self.mission("analyze_fx28_trends")
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder), \
             mock.patch.object(self.bridge, "run_safe_command") as runner:
            self.bridge.write_json(self.bridge.DASHBOARD_WORKFLOW_SETTINGS_PATH, {
                "newsBiasSchedule": {"requestedEnabled": True, "automaticDailyCalendarVersion": 3},
            })
            self.bridge.save_missions([mission])
            first = self.bridge.retire_legacy_market_runtime()
            self.assertEqual(first["retiredMissionCount"], 1)
            persisted = self.bridge.read_json(self.bridge.DASHBOARD_WORKFLOW_SETTINGS_PATH, {})
            self.assertFalse(persisted["newsBiasSchedule"]["requestedEnabled"])
            marker = self.bridge.RUNTIME_DIR / "legacy-market-retirement.json"
            initial_marker = marker.read_bytes()
            self.assertEqual(self.bridge.retire_legacy_market_runtime()["retiredMissionCount"], 0)
            self.assertEqual(marker.read_bytes(), initial_marker)
        runner.assert_not_called()

    def test_public_legacy_dashboard_is_an_archive_and_never_claims_live_service(self):
        historical = {"status": "ready", "dataStatus": "verified", "sourceStatus": "verified",
                      "currentDataAvailable": True, "events": [{"id": "historical-release"}]}
        before = copy.deepcopy(historical)
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder), \
             mock.patch.object(self.bridge, "find_property_role", return_value={}), \
             mock.patch.object(self.bridge, "_workflow_transfer_sources", return_value=[]), \
             mock.patch.object(self.bridge, "_workflow_agent_transfer_destinations", return_value=[]), \
             mock.patch.object(self.bridge, "_load_fx_daily_news_direct_store", return_value=self.bridge.fx_news_direct.empty_store()), \
             mock.patch.object(self.bridge, "_fx_trend_store", return_value={}), \
             mock.patch.object(self.bridge, "_fx_news_read_model", return_value=historical), \
             mock.patch.object(self.bridge, "_fx_bias_read_model", return_value=historical), \
             mock.patch.object(self.bridge, "run_safe_command") as runner, \
             mock.patch.object(self.bridge.fx_news_direct, "collect_official_sources") as fetch:
            model = self.bridge.workflow_dashboard_read_model(
                "left_signal_cube", reports=[], missions=[], bridge={"codex": {"status": "ready"}},
            )
        self.assertEqual(model["status"], "retired")
        self.assertEqual(model["primaryViews"], ["history"])
        self.assertEqual(model["actions"], [])
        self.assertFalse(model["newsTruth"]["liveFeedConnected"])
        self.assertFalse(model["newsTruth"]["automaticSchedulerImplemented"])
        self.assertIsNone(model["leftRail"]["refreshEndpoint"])
        self.assertIsNone(model["leftRail"]["scheduleEndpoint"])
        self.assertTrue(model["leftRail"]["readOnly"])
        for key in ("marketNews", "fxBias"):
            self.assertTrue(model[key]["archiveOnly"])
            self.assertEqual(model[key]["dataStatus"], "archived")
            self.assertEqual(model[key]["archivedDataStatus"], "verified")
            self.assertFalse(model[key]["currentDataAvailable"])
            self.assertEqual(model[key]["events"], before["events"])
        self.assertEqual(historical, before)
        runner.assert_not_called()
        fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
