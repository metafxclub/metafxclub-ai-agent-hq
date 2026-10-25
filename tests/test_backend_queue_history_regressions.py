from __future__ import annotations

import importlib.util
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import test_ai_trade_council_per_bar_automation as automation_fixtures


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_bridge_backend_queue_history_regressions",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load bridge module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BackendQueueHistoryRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bridge = load_bridge()
        self.stream_key = "a" * 64

    def _coverage(self, index: int) -> dict:
        return {
            "recordId": f"coverage-{index}",
            "streamKey": self.stream_key,
            "candidateId": "mtc-regression",
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "closedBarTime": 1_780_000_000 + index * 300,
            "snapshotId": f"{index % 16:x}" * 64,
            "detectedAt": "2026-08-12T00:00:00+00:00",
            "status": "pending",
            "reasonCode": "new_closed_bar_detected",
            "executionPolicy": "audit_only_no_stale_dispatch",
        }

    def _assert_retirement_audit(self, events: list[dict], expected_ids: list[str]) -> None:
        summaries = [row for row in events if row.get("type") == "ai_trade_council.automation_backlog_skipped"]
        chunks = [row for row in events if row.get("type") == "ai_trade_council.automation_backlog_skipped_detail"]
        self.assertEqual(len(summaries), 1)
        summary = summaries[0]
        self.assertEqual(summary["skippedCount"], len(expected_ids))
        self.assertEqual(summary["chunkCount"], (len(expected_ids) + 99) // 100)
        self.assertEqual(len(chunks), summary["chunkCount"])
        self.assertEqual([row["chunkIndex"] for row in chunks], list(range(len(chunks))))
        self.assertTrue(all(0 < len(row["recordIds"]) <= 100 for row in chunks))
        self.assertTrue(all(row["retirementBatchId"] == summary["retirementBatchId"] and
                            row["chunkCount"] == len(chunks) for row in chunks))
        ids = [record_id for row in chunks for record_id in row["recordIds"]]
        self.assertEqual(ids, expected_ids)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreater(events.index(summary), max(events.index(row) for row in chunks))
        self.assertTrue(all(row["aiRunAllowed"] is False and row["tradeCommandAllowed"] is False
                            and row["terminalActions"] is False for row in [summary, *chunks]))

    def _assert_legacy_backlog_is_retired_before_one_new_bar(self, count: int) -> None:
        fixture = automation_fixtures.AiTradeCouncilPerBarAutomationTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        bridge = fixture.bridge
        bridge.load_missions = lambda: []
        fixture._save_observed_store()
        store = bridge.load_ai_trade_council_automation_store()
        source = [{
            **self._coverage(index),
            "streamKey": store["state"]["streamKey"],
            "candidateId": fixture.candidate_id,
            "closedBarTime": fixture.closed_bar_time - (count - index) * 300,
            "snapshotId": f"{index + 1:064x}",
        } for index in range(count)]
        store["state"]["coverageRecords"] = source
        saved = bridge._save_ai_trade_council_automation_store(store)
        # No unfinished evidence is lost merely because it exceeds the old
        # runnable/history window. The scheduler, not this reader, retires it.
        self.assertEqual(len(saved["state"]["coverageRecords"]), count)
        self.assertTrue(all(row["status"] == "pending" for row in saved["state"]["coverageRecords"]))

        bridge.ai_trade_council_automation_tick()
        state = bridge.load_ai_trade_council_automation_store()["state"]
        retained = min(count, bridge.AI_TRADE_COUNCIL_AUTOMATION_MAX_COVERAGE_RECORDS)
        self.assertEqual(len(state["coverageRecords"]), retained)
        self.assertEqual(state["pendingQueue"], [])
        self.assertEqual(bridge._ai_trade_council_pending_records(state["coverageRecords"]), [])
        self.assertTrue(all(row["status"] == "skipped" and
                            row["reasonCode"] == "new_bar_only_backlog_cancelled" and
                            row["executionPolicy"] == "audit_only_no_stale_dispatch"
                            for row in state["coverageRecords"]))
        self.assertEqual([row["closedBarTime"] for row in state["coverageRecords"]],
                         [row["closedBarTime"] for row in source[-retained:]])
        # Exercise the real sanitizer and durable JSONL writer. A mock would
        # miss the generic 100-item collection cap losing large-batch IDs.
        audit_rows = [json.loads(line) for line in bridge.AUDIT_PATH.read_text(encoding="utf-8").splitlines()]
        self._assert_retirement_audit(audit_rows, [row["recordId"] for row in source])
        self.assertEqual(fixture.calls, [])
        bridge.ai_trade_council_automation_tick()
        self.assertEqual(fixture.calls, [])

        fixture._advance_bar()
        bridge.ai_trade_council_automation_tick()
        fixture._finish_settle()
        bridge.ai_trade_council_automation_tick()
        self.assertEqual(len(fixture.calls), 1)
        context = fixture.calls[0]["automationContext"]
        self.assertEqual(context["closedBarTime"], fixture.closed_bar_time)
        self.assertEqual(context["triggerPolicy"], "new_closed_bar_only_no_backfill")
        self.assertTrue(context["tradeCommandAllowed"])

    def test_513_legacy_pending_rows_are_skipped_before_one_new_bar(self) -> None:
        self._assert_legacy_backlog_is_retired_before_one_new_bar(513)

    def test_2049_legacy_pending_rows_are_audited_before_history_retention(self) -> None:
        self._assert_legacy_backlog_is_retired_before_one_new_bar(2_049)

    def _batch_retirement_fixture(self, count: int = 4):
        fixture = automation_fixtures.AiTradeCouncilPerBarAutomationTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        bridge = fixture.bridge
        fixture._save_observed_store()
        store = bridge.load_ai_trade_council_automation_store()
        store["state"]["coverageRecords"] = [{
            **self._coverage(index),
            "streamKey": store["state"]["streamKey"],
            "candidateId": fixture.candidate_id,
            "closedBarTime": fixture.closed_bar_time - (count - index) * 300,
        } for index in range(count)]
        saved = bridge._save_ai_trade_council_automation_store(store)
        return bridge, copy.deepcopy(saved["state"]["coverageRecords"])

    def test_batch_retirement_preserves_queued_analyzed_and_refreshed_pending(self) -> None:
        bridge, captured = self._batch_retirement_fixture()
        original_capture = copy.deepcopy(captured)
        store = bridge.load_ai_trade_council_automation_store()
        store["state"]["coverageRecords"][0].update(status="queued", missionId="mission-queued")
        store["state"]["coverageRecords"][1].update(status="analyzed", missionId="mission-completed")
        store["state"]["coverageRecords"][2].update(snapshotId="f" * 64)
        current = bridge._save_ai_trade_council_automation_store(store)["state"]["coverageRecords"]
        with (
            mock.patch.object(bridge, "_save_ai_trade_council_automation_store", wraps=bridge._save_ai_trade_council_automation_store) as save,
            mock.patch.object(bridge, "_ai_trade_council_coverage_upsert", side_effect=AssertionError("per-record normalization is forbidden")),
            mock.patch.object(bridge, "append_audit") as audit,
        ):
            retired_count = bridge._ai_trade_council_skip_new_bars(captured, "new_bar_only_backlog_cancelled")
        self.assertEqual(retired_count, 1)
        save.assert_called_once()
        state = bridge.load_ai_trade_council_automation_store()["state"]
        self.assertEqual(state["coverageRecords"][:3], current[:3])
        self.assertEqual(state["coverageRecords"][3]["status"], "skipped")
        self.assertEqual(state["pendingQueue"], [current[2]])
        self.assertEqual(captured, original_capture)
        self._assert_retirement_audit([call.args[0] for call in audit.call_args_list], [captured[3]["recordId"]])

    def test_batch_retirement_deduplicates_captures_and_saves_once(self) -> None:
        bridge, captured = self._batch_retirement_fixture(1)
        with (
            mock.patch.object(bridge, "_save_ai_trade_council_automation_store", wraps=bridge._save_ai_trade_council_automation_store) as save,
            mock.patch.object(bridge, "append_audit") as audit,
        ):
            retired_count = bridge._ai_trade_council_skip_new_bars(captured * 3, "new_bar_only_backlog_cancelled")
        self.assertEqual(retired_count, 1)
        save.assert_called_once()
        self._assert_retirement_audit([call.args[0] for call in audit.call_args_list], [captured[0]["recordId"]])
        self.assertEqual(bridge.load_ai_trade_council_automation_store()["state"]["pendingQueue"], [])

    def test_batch_retirement_with_no_matching_capture_is_a_durable_noop(self) -> None:
        bridge, captured = self._batch_retirement_fixture(1)
        before = bridge._ai_trade_council_automation_store_path().read_bytes()
        for request in ([], [{**captured[0], "snapshotId": "e" * 64}],
                        [{**captured[0], "closedBarTime": captured[0]["closedBarTime"] - 300}]):
            with (
                self.subTest(request=request),
                mock.patch.object(bridge, "_save_ai_trade_council_automation_store") as save,
                mock.patch.object(bridge, "append_audit") as audit,
            ):
                self.assertEqual(bridge._ai_trade_council_skip_new_bars(request, "new_bar_only_backlog_cancelled"), 0)
                save.assert_not_called()
                audit.assert_not_called()
                self.assertEqual(bridge._ai_trade_council_automation_store_path().read_bytes(), before)

    def test_batch_retirement_never_audits_a_failed_durable_save(self) -> None:
        bridge, captured = self._batch_retirement_fixture(1)
        before = bridge._ai_trade_council_automation_store_path().read_bytes()
        with (
            mock.patch.object(bridge, "_save_ai_trade_council_automation_store", side_effect=OSError("write failed")),
            mock.patch.object(bridge, "append_audit") as audit,
        ):
            with self.assertRaises(OSError):
                bridge._ai_trade_council_skip_new_bars(captured, "new_bar_only_backlog_cancelled")
            audit.assert_not_called()
        self.assertEqual(bridge._ai_trade_council_automation_store_path().read_bytes(), before)

    def test_baseline_reports_actual_retirements_after_capture_changes(self) -> None:
        bridge, _ = self._batch_retirement_fixture(1)
        store = bridge.load_ai_trade_council_automation_store()
        store["state"]["startupId"] = "previous-process"
        bridge._save_ai_trade_council_automation_store(store)
        retire = bridge._ai_trade_council_skip_new_bars

        def refreshed_capture(records, reason):
            current = bridge.load_ai_trade_council_automation_store()
            current["state"]["coverageRecords"][0]["snapshotId"] = "e" * 64
            bridge._save_ai_trade_council_automation_store(current)
            return retire(records, reason)

        with (
            mock.patch.object(bridge, "_ai_trade_council_skip_new_bars", side_effect=refreshed_capture),
            mock.patch.object(bridge, "_ai_trade_council_recover_created_round", return_value=None),
            mock.patch.object(bridge, "append_audit") as audit,
        ):
            bridge.ai_trade_council_automation_tick()
        baseline = [call.args[0] for call in audit.call_args_list
                    if call.args[0].get("type") == "ai_trade_council.automation_baseline"]
        self.assertEqual(len(baseline), 1)
        self.assertEqual(baseline[0]["skippedCount"], 0)
        self.assertEqual(bridge.load_ai_trade_council_automation_store()["state"]["coverageRecords"][0]["snapshotId"], "e" * 64)

    def test_automation_read_model_exposes_gate_and_no_backfill_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.bridge.RUNTIME_DIR = root
            store = self.bridge._ai_trade_council_automation_default_store()
            store["config"]["enabled"] = True
            store["state"].update({
                "status": "waiting_gate",
                "reason": "quota_below_reserve",
                "coverageRecords": [self._coverage(0), self._coverage(1)],
                "pendingQueue": [self._coverage(0), self._coverage(1)],
            })
            self.bridge._save_ai_trade_council_automation_store(store)

            # This is legacy evidence before the first scheduler tick, not
            # permission to run it. Pin the day to isolate gate projection.
            with mock.patch.object(
                self.bridge,
                "_automation_day_key",
                return_value="2026-08-12",
            ):
                model = self.bridge.ai_trade_council_automation_read_model()

        self.assertEqual(model["state"]["status"], "waiting_gate")
        self.assertEqual(model["state"]["reasonCode"], "quota_below_reserve")
        self.assertTrue(model["state"]["waitingGate"]["active"])
        self.assertEqual(
            model["state"]["waitingGate"]["reasonCode"],
            "quota_below_reserve",
        )
        self.assertEqual(model["state"]["pending"]["queuePosition"], 1)
        self.assertEqual(model["state"]["pending"]["queueDepth"], 2)
        self.assertEqual(
            model["backlogPolicy"]["queueOrder"],
            "new_closed_bar_only",
        )
        self.assertEqual(model["backlogPolicy"]["staleTradeCommand"], "blocked")
        self.assertEqual(model["backlogPolicy"]["policy"], "new_closed_bar_only_no_backfill")
        self.assertEqual(model["backlogPolicy"]["staleAnalysis"], "skipped_without_ai")
        self.assertEqual(model["backlogPolicy"]["capacityPolicy"], "no_backfill")
        self.assertEqual(model["backlogPolicy"]["maximumRunnablePending"], 1)
        self.assertEqual(model["backlogPolicy"]["quotaResume"], "wait_for_next_closed_bar")

    def test_history_endpoint_rejects_invalid_cursor_instead_of_restarting_page_one(self) -> None:
        handler = object.__new__(self.bridge.BridgeHandler)
        handler.path = (
            "/api/ai-trade-council/history?kind=analysis&cursor=%2Fbad-cursor"
        )
        handler.validate_local_request = mock.Mock(return_value=None)

        with self.assertRaises(self.bridge.RequestError) as caught:
            handler._do_GET_guarded()

        self.assertEqual(caught.exception.status, 422)
        self.assertEqual(str(caught.exception), "Invalid history cursor.")

    def _parent(self, mission_id: str, snapshot_id: str, decision: str) -> dict:
        return {
            "id": mission_id,
            "title": mission_id,
            "status": "completed",
            "createdAt": "2026-08-12T00:00:00+00:00",
            "completedAt": "2026-08-12T00:01:00+00:00",
            "analysisContext": {
                "kind": "ai_trade_council_parent",
                "snapshotId": snapshot_id,
                "closedBarIdentity": {
                    "streamKey": self.stream_key,
                    "closedBarTime": 1_780_000_000,
                    "symbol": "XAUUSD",
                    "timeframe": "M5",
                },
                "automation": {
                    "executionPolicy": "audit_only_no_stale_dispatch",
                    "tradeCommandAllowed": False,
                },
            },
            "councilDecision": {
                "decision": decision,
                "selectedDirection": decision if decision in {"BUY", "SELL"} else None,
                "consensusReached": True,
                "requiredVotes": 3,
            },
        }

    def _children(self, parent_id: str, decision: str) -> list[dict]:
        return [
            {
                "id": f"{parent_id}-{role}",
                "owner": f"agent-{role}",
                "status": "completed",
                "parentMissionId": parent_id,
                "analysisContext": {
                    "kind": "ai_trade_council_vote",
                    "roleId": role,
                },
                "councilVote": {"decision": decision, "confidence": 80},
            }
            for role in ("technical", "price_action", "news")
        ]

    def test_history_keeps_attempts_and_pages_by_attempt_id(self) -> None:
        first_snapshot = "b" * 64
        second_snapshot = "c" * 64
        parents = [
            self._parent("mission-attempt-1", first_snapshot, "NO_TRADE"),
            self._parent("mission-attempt-2", second_snapshot, "BUY"),
        ]
        missions = [
            *parents,
            *self._children("mission-attempt-1", "HOLD"),
            *self._children("mission-attempt-2", "BUY"),
        ]
        with tempfile.TemporaryDirectory() as temporary_directory:
            self.bridge.RUNTIME_DIR = Path(temporary_directory)
            store = self.bridge._ai_trade_council_automation_default_store()
            self.bridge._save_ai_trade_council_automation_store(store)
            first_page = self.bridge._ai_trade_council_analysis_history_read_model(
                missions,
                {"available": True, "items": []},
                limit=1,
            )
            second_page = self.bridge._ai_trade_council_analysis_history_read_model(
                missions,
                {"available": True, "items": []},
                limit=1,
                cursor=first_page["nextCursor"],
            )

        self.assertTrue(first_page["available"])
        self.assertEqual(first_page["summary"]["expected"], 2)
        self.assertEqual(first_page["summary"]["completeThreeOfThree"], 2)
        self.assertEqual(first_page["summary"]["waiting"], 0)
        self.assertEqual(first_page["summary"]["running"], 0)
        self.assertEqual(first_page["summary"]["decisionCounts"]["BUY"], 1)
        self.assertEqual(first_page["summary"]["decisionCounts"]["NO_TRADE"], 1)
        self.assertEqual(len(first_page["items"]), 1)
        self.assertTrue(first_page["hasMore"])
        self.assertEqual(len(second_page["items"]), 1)
        self.assertNotEqual(
            first_page["items"][0]["attemptId"],
            second_page["items"][0]["attemptId"],
        )

    def test_history_is_explicitly_unavailable_when_coverage_store_fails(self) -> None:
        parent = self._parent("mission-attempt", "d" * 64, "BUY")
        with mock.patch.object(
            self.bridge,
            "load_ai_trade_council_automation_store",
            side_effect=self.bridge.DataIntegrityError("broken"),
        ):
            model = self.bridge._ai_trade_council_analysis_history_read_model(
                [parent, *self._children(parent["id"], "BUY")],
                {"available": True, "items": []},
            )

        self.assertFalse(model["available"])
        self.assertEqual(model["items"], [])
        self.assertEqual(
            model["reasonCode"],
            "automation_coverage_store_unavailable",
        )
        self.assertEqual(model["summary"]["expected"], 0)

    def test_history_summary_splits_waiting_coverage_from_running_parent(self) -> None:
        snapshot_id = "f" * 64
        running_parent = self._parent("mission-running", snapshot_id, "NO_DATA")
        running_parent["status"] = "running"
        running_parent["completedAt"] = None
        pending_record = self._coverage(1)
        with tempfile.TemporaryDirectory() as temporary_directory:
            self.bridge.RUNTIME_DIR = Path(temporary_directory)
            store = self.bridge._ai_trade_council_automation_default_store()
            store["state"].update({
                "coverageRecords": [pending_record],
                "pendingQueue": [pending_record],
            })
            self.bridge._save_ai_trade_council_automation_store(store)
            model = self.bridge._ai_trade_council_analysis_history_read_model(
                [running_parent],
                {"available": True, "items": []},
            )

        self.assertEqual(model["summary"]["pending"], 2)
        self.assertEqual(model["summary"]["waiting"], 1)
        self.assertEqual(model["summary"]["running"], 1)

    def test_order_linking_never_uses_snapshot_when_wrong_mission_is_supplied(self) -> None:
        snapshot_id = "e" * 64
        parent = self._parent("mission-correct", snapshot_id, "BUY")
        exact_wrong = {
            "available": True,
            "items": [{
                "commandId": "command-wrong",
                "missionId": "mission-does-not-exist",
                "snapshotId": snapshot_id,
                "ticket": 1,
                "side": "BUY",
                "executionState": "OPEN",
                "provenByEa": True,
            }],
        }
        legacy = {
            "available": True,
            "items": [{
                "commandId": "command-legacy",
                "missionId": None,
                "snapshotId": snapshot_id,
                "ticket": 2,
                "side": "BUY",
                "executionState": "OPEN",
                "provenByEa": True,
            }],
        }

        wrong_model = self.bridge._ai_trade_order_history_read_model(
            exact_wrong,
            [parent],
        )
        legacy_model = self.bridge._ai_trade_order_history_read_model(
            legacy,
            [parent],
        )
        invalid_reference = self.bridge._ai_trade_order_history_read_model(
            {
                "available": True,
                "items": [{
                    **legacy["items"][0],
                    "missionId": "not valid / supplied",
                }],
            },
            [parent],
        )

        self.assertEqual(wrong_model["items"][0]["missionLinkage"], "unavailable")
        self.assertIsNone(wrong_model["items"][0]["linkedMissionId"])
        self.assertEqual(
            legacy_model["items"][0]["missionLinkage"],
            "legacy_snapshot_without_mission_id",
        )
        self.assertEqual(
            legacy_model["items"][0]["linkedMissionId"],
            "mission-correct",
        )
        self.assertEqual(
            invalid_reference["items"][0]["missionLinkage"],
            "unavailable",
        )

    def test_startup_recovery_closes_local_settings_without_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            missions_path = root / "missions.json"
            audit_path = root / "audit.jsonl"
            missions = {
                "missions": [
                    {
                        "id": "mission-local-running",
                        "title": "Schedule",
                        "toolId": "save_discovery_schedule",
                        "targetId": "codex_mcp_portal",
                        "status": "running",
                        "workflowContext": {
                            "propId": "codex_mcp_portal",
                            "actionId": "save_discovery_schedule",
                        },
                    },
                    {
                        "id": "mission-unrelated-running",
                        "title": "Other",
                        "toolId": "manager_mission",
                        "status": "running",
                    },
                ]
            }
            missions_path.write_text(json.dumps(missions), encoding="utf-8")
            with (
                mock.patch.object(self.bridge, "MISSIONS_PATH", missions_path),
                mock.patch.object(self.bridge, "AUDIT_PATH", audit_path),
            ):
                self.bridge._invalidate_missions_read_cache()
                recovered = self.bridge.recover_interrupted_local_workflow_missions()
                stored = self.bridge.load_missions()
                audit = self.bridge.tail_jsonl(audit_path)

        self.assertEqual(recovered, 1)
        local = next(row for row in stored if row["id"] == "mission-local-running")
        unrelated = next(row for row in stored if row["id"] == "mission-unrelated-running")
        self.assertEqual(local["status"], "failed")
        self.assertEqual(
            local["errorCode"],
            "bridge_restart_local_workflow_interrupted",
        )
        self.assertEqual(unrelated["status"], "running")
        self.assertEqual(
            audit[-1]["type"],
            "dashboard.workflow_local_interrupted_recovered",
        )
        self.assertFalse(audit[-1]["localHandlerRerun"])

    def test_mission_summary_is_compact_and_points_to_detail_endpoint(self) -> None:
        mission = {
            "id": "mission-summary",
            "title": "Summary",
            "detail": "x" * 8_000,
            "result": "y" * 8_000,
            "owner": "manager",
            "toolId": "manager_mission",
            "targetId": "mission_strategy_table",
            "status": "completed",
            "reportIds": ["report-1"],
        }

        summary = self.bridge.mission_summary_read_model_item(mission)

        self.assertNotIn("detail", summary)
        self.assertNotIn("result", summary)
        self.assertEqual(summary["reportCount"], 1)
        self.assertEqual(
            summary["detailEndpoint"],
            "/api/missions/mission-summary",
        )

    def test_mission_table_defaults_to_compact_pages_and_full_is_explicit(self) -> None:
        missions = [
            {
                "id": f"mission-{index}",
                "title": f"Mission {index}",
                "detail": "x" * 8_000,
                "result": "y" * 8_000,
                "owner": "manager",
                "toolId": "manager_mission",
                "targetId": "mission_strategy_table",
                "status": "completed",
            }
            for index in range(250)
        ]
        reports = [
            {
                "id": f"report-{index}",
                "type": "mission_plan",
                "title": f"Report {index}",
                "summary": "z" * 8_000,
                "linkedPropId": "mission_strategy_table",
                "status": "ready",
            }
            for index in range(30)
        ]
        bridge_status = {
            "mode": "Local Runner",
            "status": "guarded",
            "codex": {"status": "ready"},
            "mcp": {"status": "config_present"},
        }
        with (
            mock.patch.object(self.bridge, "load_missions", return_value=missions),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=reports),
            mock.patch.object(self.bridge, "load_agent_events", return_value=[]),
            mock.patch.object(self.bridge, "load_meeting_records", return_value=[]),
            mock.patch.object(self.bridge, "search_memory_items", return_value=[]),
            mock.patch.object(self.bridge, "bridge_status", return_value=bridge_status),
            mock.patch.object(
                self.bridge,
                "capability_registry",
                return_value={"capabilities": [], "bridge": bridge_status},
            ),
            mock.patch.object(
                self.bridge,
                "dashboard_connection_checklist",
                return_value={},
            ),
        ):
            summary = self.bridge.prop_report("mission_strategy_table")
            full = self.bridge.prop_report(
                "mission_strategy_table",
                detail_scope="full",
            )

        self.assertEqual(summary["missionScope"], "global_summary_page")
        self.assertEqual(len(summary["missions"]), 100)
        self.assertNotIn("detail", summary["missions"][0])
        self.assertTrue(summary["missionPage"]["hasMore"])
        self.assertEqual(summary["missionPage"]["total"], 250)
        self.assertEqual(len(summary["reports"]), 20)
        self.assertNotIn("findings", summary["reports"][0])
        self.assertEqual(summary["reportSummary"]["total"], 30)
        self.assertEqual(full["missionScope"], "global_all_missions")
        self.assertEqual(len(full["missions"]), 250)
        self.assertIn("detail", full["missions"][0])
        self.assertEqual(len(full["reports"]), 30)


if __name__ == "__main__":
    unittest.main()
