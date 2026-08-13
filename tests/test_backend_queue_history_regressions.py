from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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

    def test_513_pending_rows_never_leave_visible_unrunnable_work(self) -> None:
        rows = self.bridge._ai_trade_council_coverage_records(
            [self._coverage(index) for index in range(513)]
        )

        pending = [row for row in rows if row["status"] == "pending"]
        skipped = [row for row in rows if row["status"] == "skipped"]
        queue = self.bridge._ai_trade_council_pending_records(rows)

        self.assertEqual(len(rows), 513)
        self.assertEqual(len(pending), 512)
        self.assertEqual(queue, pending)
        self.assertEqual(len(skipped), 1)
        self.assertEqual(
            skipped[0]["reasonCode"],
            "pending_queue_capacity_exceeded",
        )
        self.assertEqual(
            skipped[0]["executionPolicy"],
            "audit_only_no_stale_dispatch",
        )
        self.assertEqual(
            [row["closedBarTime"] for row in pending],
            sorted(row["closedBarTime"] for row in pending),
        )

    def test_2049_pending_rows_preserve_fifo_head_and_terminalize_overflow(self) -> None:
        source = [self._coverage(index) for index in range(2_049)]
        rows = self.bridge._ai_trade_council_coverage_records(source)

        pending = [row for row in rows if row["status"] == "pending"]
        skipped = [row for row in rows if row["status"] == "skipped"]

        self.assertEqual(len(rows), 2_048)
        self.assertEqual(len(pending), 512)
        self.assertEqual(len(skipped), 1_536)
        self.assertEqual(
            [row["closedBarTime"] for row in pending],
            [row["closedBarTime"] for row in source[:512]],
        )
        self.assertTrue(
            all(
                row["reasonCode"] == "pending_queue_capacity_exceeded"
                for row in skipped
            )
        )
        self.assertEqual(
            self.bridge._ai_trade_council_pending_records(rows),
            pending,
        )

    def test_automation_read_model_exposes_gate_and_fifo_head(self) -> None:
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

            # This fixture exercises queue projection, not daily rollover.
            # Pin the Bangkok day so the fixed pending records remain runnable
            # regardless of the calendar date on which CI executes.
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
            "oldest_closed_bar_first",
        )
        self.assertEqual(model["backlogPolicy"]["staleTradeCommand"], "blocked")

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
