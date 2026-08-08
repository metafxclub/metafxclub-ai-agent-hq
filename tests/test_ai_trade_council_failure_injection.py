from __future__ import annotations

import importlib.util
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load bridge module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot_payload(candidate_id: str, bar_count: int = 140) -> dict:
    return {
        "schemaVersion": "metafx-hq-mt4-snapshot-v1",
        "adapterId": candidate_id,
        "mode": "read_only",
        "chart": {
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "bid": 2388.12,
            "ask": 2388.35,
            "spreadPoints": 23,
            "marketOpen": True,
            "marketSession": "TEST_OPEN",
            "bars": [
                {
                    "time": 1785196800 + index * 300,
                    "open": 2380 + index,
                    "high": 2385 + index,
                    "low": 2378 + index,
                    "close": 2383 + index,
                    "volume": 1000 + index,
                }
                for index in range(bar_count)
            ],
        },
        "daily": {
            "serverDay": "2026.08.08",
            "realizedProfit": 0,
            "floatingProfit": 0,
            "netPnl": 0,
            "tradesClosed": 0,
            "wins": 0,
            "losses": 0,
        },
        "accountSummary": {
            "currency": "USD",
            "balance": 10000,
            "equity": 10000,
            "margin": 0,
            "freeMargin": 10000,
        },
        "positionsSummary": {
            "count": 0,
            "buyCount": 0,
            "sellCount": 0,
            "totalLots": 0,
            "floatingProfit": 0,
        },
    }


class AiTradeCouncilFailureInjectionTests(unittest.TestCase):
    """Failure injection only: no real Codex process and no MT4 order channel."""

    def setUp(self) -> None:
        self.bridge = load_bridge(
            f"metafx_bridge_failure_injection_{id(self)}_{threading.get_ident()}"
        )
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self._configure_runtime_paths(self.bridge, self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _configure_runtime_paths(bridge, root: Path) -> None:
        runtime = root / "runtime"
        bridge.RUNTIME_DIR = runtime
        bridge.MISSIONS_PATH = runtime / "missions.json"
        bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
        bridge.AGENT_EVENTS_PATH = runtime / "agent-events.jsonl"
        bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
        bridge.OPERATOR_MODE_PATH = runtime / "operator-mode.json"
        bridge.UI_SESSION_PATH = runtime / "ui-session.json"
        bridge.METATRADER_COMMON_FILES_DIR = root / "common"
        bridge.PROJECT_ROOT = root
        bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR = root / "workspace"
        bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR = (
            bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR
            / "ai-trade-council"
            / "snapshots"
        )

    def _configure_selected_mt4(self) -> str:
        install = self.root / "Program Files" / "RoboForex MT4 Terminal"
        data_root = self.root / "AppData" / "MetaQuotes" / "Terminal"
        data = data_root / "ROBOHASH"
        install.mkdir(parents=True)
        (install / "terminal.exe").write_bytes(b"MZ")
        (data / "MQL4").mkdir(parents=True)
        (data / "origin.txt").write_text(str(install), encoding="utf-16")

        discovered = self.bridge.discover_metatrader_installations(
            roots=[install.parent, data_root],
            include_candidates=True,
        )
        running = self.bridge.discover_running_metatrader(
            process_locations={"mt4": [str(install)], "mt5": []}
        )
        candidates = self.bridge._sync_metatrader_candidate_registry(
            discovered["_candidateLocations"],
            running,
        )
        self.assertEqual(len(candidates), 1)
        candidate_id = candidates[0]["candidateId"]
        with self.bridge.METATRADER_TARGETS_LOCK:
            store = self.bridge._load_metatrader_target_store_unlocked()
            store["selections"][self.bridge.AI_TRADE_COUNCIL_PROP_ID] = {
                "candidateId": candidate_id,
                "selectedAt": self.bridge.utc_now(),
            }
            self.bridge._write_metatrader_target_store_unlocked(store)
        snapshot_file = self.bridge._metatrader_snapshot_file(candidate_id)
        self.assertIsNotNone(snapshot_file)
        snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        snapshot_file.write_text(
            json.dumps(snapshot_payload(candidate_id), ensure_ascii=False),
            encoding="utf-8",
        )
        return candidate_id

    def _analysis_patches(self):
        return (
            mock.patch.object(
                self.bridge,
                "load_operator_mode_record",
                return_value={"mode": "auto_guarded", "updatedAt": self.bridge.utc_now()},
            ),
            mock.patch.object(
                self.bridge,
                "bridge_status",
                return_value={
                    "status": "guarded",
                    "codex": {"status": "ready_guarded"},
                    "mcp": {"status": "config_present"},
                    "policy": {"operatorMode": "auto_guarded"},
                    "time": self.bridge.utc_now(),
                },
            ),
            mock.patch.object(
                self.bridge,
                "codex_rate_limits",
                return_value={
                    "ok": True,
                    "status": "ready",
                    "stale": False,
                    "limitReached": False,
                    "primary": {"usedPercent": 10, "remainingPercent": 90},
                },
            ),
            mock.patch.object(
                self.bridge,
                "check_rate_limit",
                return_value=(True, 0),
            ),
        )

    def _queue_analysis(self, snapshot_id: str) -> dict:
        patches = self._analysis_patches()
        with patches[0], patches[1], patches[2], patches[3]:
            return self.bridge.run_ai_trade_council_analysis(
                {"snapshotId": snapshot_id}
            )

    def test_concurrent_same_snapshot_requests_create_only_one_round(self) -> None:
        self._configure_selected_mt4()
        snapshot_id = self.bridge.metatrader_snapshot_read_model(
            self.bridge.AI_TRADE_COUNCIL_PROP_ID
        )["chartSnapshot"]["snapshotId"]
        patches = self._analysis_patches()
        with patches[0], patches[1], patches[2], patches[3]:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(
                    pool.map(
                        lambda _index: self.bridge.run_ai_trade_council_analysis(
                            {"snapshotId": snapshot_id}
                        ),
                        range(2),
                    )
                )

        self.assertEqual(
            {item["kind"] for item in results},
            {"ai_trade_council_queued", "ai_trade_council_existing"},
        )
        missions = self.bridge.load_missions()
        parents = [
            item
            for item in missions
            if (item.get("analysisContext") or {}).get("kind")
            == "ai_trade_council_parent"
        ]
        self.assertEqual(len(parents), 1)
        self.assertEqual(
            len(
                [
                    item
                    for item in missions
                    if item.get("parentMissionId") == parents[0]["id"]
                ]
            ),
            3,
        )

    def test_new_snapshot_cannot_start_while_previous_council_round_is_active(self) -> None:
        candidate_id = self._configure_selected_mt4()
        first_snapshot_id = self.bridge.metatrader_snapshot_read_model(
            self.bridge.AI_TRADE_COUNCIL_PROP_ID
        )["chartSnapshot"]["snapshotId"]
        first = self._queue_analysis(first_snapshot_id)

        payload = snapshot_payload(candidate_id)
        payload["chart"]["bars"][-1]["close"] += 0.25
        payload["chart"]["bid"] += 0.25
        payload["chart"]["ask"] += 0.25
        snapshot_file = self.bridge._metatrader_snapshot_file(candidate_id)
        snapshot_file.write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )
        second_snapshot_id = self.bridge.metatrader_snapshot_read_model(
            self.bridge.AI_TRADE_COUNCIL_PROP_ID
        )["chartSnapshot"]["snapshotId"]
        self.assertNotEqual(first_snapshot_id, second_snapshot_id)

        patches = self._analysis_patches()
        with patches[0], patches[1], patches[2], patches[3]:
            with self.assertRaises(self.bridge.RequestError) as error:
                self.bridge.run_ai_trade_council_analysis(
                    {"snapshotId": second_snapshot_id}
                )
        self.assertEqual(error.exception.status, 409)
        self.assertIn("รอบวิเคราะห์", str(error.exception))

        parents = [
            mission
            for mission in self.bridge.load_missions()
            if (mission.get("analysisContext") or {}).get("kind")
            == "ai_trade_council_parent"
        ]
        self.assertEqual(len(parents), 1)
        self.assertEqual(parents[0]["id"], first["parent"]["id"])

    def test_stable_terminal_parent_is_not_rewritten_or_redispatched_by_reconcile(self) -> None:
        aggregated_at = datetime.now(timezone.utc)
        child_updated_at = aggregated_at - timedelta(seconds=5)
        parent = {
            "id": "mission-parent-stable",
            "status": "completed",
            "analysisContext": {"kind": "ai_trade_council_parent"},
            "delegation": {
                "lastAggregatedAt": aggregated_at.isoformat(),
                "finalReportId": "report-parent-stable",
            },
            "updatedAt": aggregated_at.isoformat(),
        }
        children = [
            {
                "id": f"mission-child-{index}",
                "parentMissionId": parent["id"],
                "owner": owner,
                "status": "completed",
                "updatedAt": child_updated_at.isoformat(),
            }
            for index, owner in enumerate(
                ("optimization_agent", "backtest_analyst", "codex_mcp_operator"),
                start=1,
            )
        ]
        self.bridge.save_missions([parent, *children])

        with mock.patch.object(
            self.bridge,
            "dispatch_ai_trade_council_trade_plan",
            side_effect=AssertionError("stable parent must not be redispatched"),
        ):
            refreshed = self.bridge.refresh_parent_mission(parent["id"])
            reconcile_count = self.bridge.reconcile_parent_mission_statuses()

        self.assertEqual(refreshed["updatedAt"], parent["updatedAt"])
        self.assertEqual(reconcile_count, 0)
        self.assertTrue(
            self.bridge._parent_mission_is_already_aggregated(parent, children)
        )

    def test_terminal_blocked_round_can_be_restarted_on_same_current_snapshot(self) -> None:
        """A no-command terminal round must not make a stable candle unrecoverable."""
        self._configure_selected_mt4()
        snapshot_id = self.bridge.metatrader_snapshot_read_model(
            self.bridge.AI_TRADE_COUNCIL_PROP_ID
        )["chartSnapshot"]["snapshotId"]
        first = self._queue_analysis(snapshot_id)
        missions = self.bridge.load_missions()
        old_parent_id = first["parent"]["id"]
        for mission in missions:
            if mission.get("id") == old_parent_id:
                mission.update(
                    {
                        "status": "blocked",
                        "phase": "review_required",
                        "completedAt": self.bridge.utc_now(),
                        "tradeGateway": {
                            "commandPublished": False,
                            "terminalActions": False,
                        },
                    }
                )
            elif mission.get("parentMissionId") == old_parent_id:
                mission.update(
                    {
                        "status": "blocked",
                        "phase": "council_round_expired",
                        "workStatus": "blocked",
                        "errorCode": "council_round_deadline_expired",
                        "completedAt": self.bridge.utc_now(),
                    }
                )
        self.bridge.save_missions(missions)

        retried = self._queue_analysis(snapshot_id)

        self.assertEqual(retried["kind"], "ai_trade_council_queued")
        self.assertNotEqual(retried["parent"]["id"], old_parent_id)
        self.assertEqual(len(retried["subtasks"]), 3)
        self.assertTrue(
            all(
                item["parentMissionId"] == retried["parent"]["id"]
                for item in retried["subtasks"]
            )
        )

    def test_local_hourly_rate_guard_survives_bridge_process_restart(self) -> None:
        """Restarting the local server must not reset the user-defined cost guard."""
        rate_key = "real:optimization_agent:codex_cli_task:specialist_balanced"
        self.assertEqual(
            self.bridge.check_rate_limit(rate_key, 1, consume=True),
            (True, 0),
        )
        self.assertFalse(
            self.bridge.check_rate_limit(rate_key, 1, consume=False)[0]
        )

        restarted = load_bridge("metafx_bridge_failure_injection_restart")
        self._configure_runtime_paths(restarted, self.root)
        allowed_after_restart, retry_after = restarted.check_rate_limit(
            rate_key,
            1,
            consume=False,
        )

        self.assertFalse(allowed_after_restart)
        self.assertGreater(retry_after, 0)

    def test_quota_backoff_never_schedules_council_vote_past_round_deadline(self) -> None:
        """A known-impossible retry should become terminal immediately, not stay blue."""
        deadline = datetime.now(timezone.utc) + timedelta(seconds=240)
        mission = {
            "id": "mission-quota-backoff-deadline",
            "title": "Technical Consultant",
            "owner": "optimization_agent",
            "toolId": "codex_cli_task",
            "modelTier": "specialist_balanced",
            "status": "queued",
            "phase": "auto_guarded_queued",
            "autoEligible": True,
            "executionMode": "auto_guarded",
            "attemptCount": 0,
            "analysisContext": {
                "kind": "ai_trade_council_vote",
                "snapshotId": "a" * 64,
                "agentId": "optimization_agent",
                "roleId": "technical",
                "roundDeadlineAt": deadline.isoformat(),
            },
            "execution": {
                "schema": "auto-guarded-execution-v1",
                "dispatchState": "queued",
                "processStarted": False,
            },
        }
        self.bridge.save_missions([mission])
        worker_config = {
            **self.bridge.mission_worker_config(),
            "quotaBackoffSeconds": 300,
        }
        with (
            mock.patch.object(
                self.bridge,
                "CODEX_RUNNER_PYTHON",
                Path(__file__),
            ),
            mock.patch.object(
                self.bridge,
                "CODEX_RUNNER_SCRIPT",
                Path(__file__),
            ),
            mock.patch.object(
                self.bridge,
                "mission_worker_config",
                return_value=worker_config,
            ),
            mock.patch.object(
                self.bridge,
                "bridge_status",
                return_value={"codex": {"status": "ready_guarded"}},
            ),
            mock.patch.object(
                self.bridge,
                "codex_rate_limits",
                return_value={
                    "ok": False,
                    "stale": True,
                    "limitReached": False,
                },
            ),
        ):
            self.bridge.process_auto_mission("worker-failure-injection", mission)

        stored = self.bridge.find_mission(mission["id"])
        self.assertEqual(stored["status"], "blocked")
        self.assertEqual(
            stored.get("errorCode"),
            "council_quota_backoff_exceeds_round_deadline",
        )
        self.assertFalse(stored["execution"].get("processStarted"))
        self.assertIsNone(stored["execution"].get("nextAttemptAt"))

    def test_vote_never_starts_when_its_own_timeout_cannot_fit_round(self) -> None:
        deadline = datetime.now(timezone.utc) + timedelta(seconds=120)
        mission = {
            "id": "mission-timeout-cannot-fit-round",
            "owner": "optimization_agent",
            "toolId": "codex_cli_task",
            "modelTier": "specialist_balanced",
            "status": "queued",
            "phase": "auto_guarded_queued",
            "autoEligible": True,
            "executionMode": "auto_guarded",
            "budget": {"timeoutSeconds": 120, "outputLimitChars": 7000},
            "analysisContext": {
                "kind": "ai_trade_council_vote",
                "snapshotId": "b" * 64,
                "agentId": "optimization_agent",
                "roleId": "technical",
                "roundDeadlineAt": deadline.isoformat(),
            },
            "execution": {
                "schema": "auto-guarded-execution-v1",
                "dispatchState": "queued",
                "processStarted": False,
            },
        }
        self.bridge.save_missions([mission])

        with mock.patch.object(
            self.bridge,
            "bridge_status",
            side_effect=AssertionError("runner preflight must not be reached"),
        ):
            self.bridge.process_auto_mission("worker-deadline-fit", mission)

        stored = self.bridge.find_mission(mission["id"])
        self.assertEqual(stored["status"], "blocked")
        self.assertEqual(
            stored.get("errorCode"),
            "council_round_deadline_insufficient",
        )
        self.assertFalse(stored["execution"].get("processStarted"))
        self.assertIsNone(stored["execution"].get("nextAttemptAt"))

    def test_malformed_analysis_payload_has_no_runtime_side_effect(self) -> None:
        with self.assertRaises(self.bridge.RequestError) as captured:
            self.bridge.run_ai_trade_council_analysis(
                {
                    "snapshotId": "a" * 64,
                    "sendOrder": True,
                    "token": "must-never-be-accepted",
                }
            )
        self.assertEqual(captured.exception.status, 422)
        self.assertFalse(self.bridge.MISSIONS_PATH.exists())
        self.assertFalse(self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR.exists())

    def test_corrupt_mission_store_fails_closed_without_rewriting_evidence(self) -> None:
        self.bridge.MISSIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        original = b'{"missions": [invalid-json]}'
        self.bridge.MISSIONS_PATH.write_bytes(original)

        with self.assertRaises(self.bridge.DataIntegrityError):
            self.bridge.load_missions()

        self.assertEqual(self.bridge.MISSIONS_PATH.read_bytes(), original)

    def test_corrupt_durable_rate_store_fails_closed_without_rewriting_evidence(self) -> None:
        rate_store = self.bridge._persisted_rate_limit_path()
        rate_store.parent.mkdir(parents=True, exist_ok=True)
        original = b'{"schemaVersion": "local-rate-limit-state-v1", "buckets": invalid}'
        rate_store.write_bytes(original)

        with self.assertRaises(self.bridge.DataIntegrityError):
            self.bridge.check_rate_limit(
                "real:optimization_agent:codex_cli_task:specialist_balanced",
                1,
                consume=False,
            )

        self.assertEqual(rate_store.read_bytes(), original)

    def test_council_status_uses_the_canonical_council_connection_source(self) -> None:
        """The status prop must not create an independent MT4 selection universe."""
        checklist_calls: list[str] = []
        snapshot_calls: list[str] = []

        def fake_checklist(prop_id: str, bridge=None) -> dict:
            checklist_calls.append(prop_id)
            return {
                "metatraderSelection": {
                    "status": "not_selected",
                    "candidates": [],
                    "selectedCandidate": None,
                },
                "items": [],
            }

        def fake_snapshot(prop_id: str) -> dict:
            snapshot_calls.append(prop_id)
            return self.bridge._empty_metatrader_snapshot_read_model(
                prop_id,
                "not_selected",
                "selected_terminal_missing",
            )

        with (
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(self.bridge, "load_agent_events", return_value=[]),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
            mock.patch.object(self.bridge, "load_meeting_records", return_value=[]),
            mock.patch.object(self.bridge, "search_memory_items", return_value=[]),
            mock.patch.object(self.bridge, "bridge_status", return_value={}),
            mock.patch.object(
                self.bridge,
                "capability_registry",
                return_value={"bridge": {}, "capabilities": []},
            ),
            mock.patch.object(
                self.bridge,
                "find_dashboard_connection_profile",
                return_value={"moduleNameTh": "test"},
            ),
            mock.patch.object(
                self.bridge,
                "dashboard_connection_checklist",
                side_effect=fake_checklist,
            ),
            mock.patch.object(
                self.bridge,
                "metatrader_snapshot_read_model",
                side_effect=fake_snapshot,
            ),
            mock.patch.object(
                self.bridge,
                "mt4_trade_gateway_status_read_model",
                return_value=self.bridge._empty_mt4_trade_gateway_status(),
            ),
            mock.patch.object(
                self.bridge,
                "load_ai_trade_council_automation_store",
                return_value=self.bridge._ai_trade_council_automation_default_store(),
            ),
        ):
            report = self.bridge.prop_report(
                self.bridge.AUTO_TRADING_STATUS_PROP_ID
            )

        self.assertEqual(
            report["connectionSourcePropId"],
            self.bridge.AI_TRADE_COUNCIL_PROP_ID,
        )
        self.assertEqual(
            checklist_calls,
            [self.bridge.AI_TRADE_COUNCIL_PROP_ID],
        )
        self.assertGreaterEqual(len(snapshot_calls), 2)
        self.assertEqual(
            set(snapshot_calls),
            {self.bridge.AI_TRADE_COUNCIL_PROP_ID},
        )
        self.assertEqual(
            report["metatraderReadOnly"]["propId"],
            self.bridge.AI_TRADE_COUNCIL_PROP_ID,
        )
        self.assertIn("autoTradingStatus", report)
        # The former signal-cube status surface has been repurposed for the
        # daily FX news workflow.  Status now lives on the canonical council
        # dashboard itself, so both read models intentionally share one
        # connection universe and one response.
        self.assertIn("aiTradeCouncil", report)

    def test_active_parent_reconcile_is_quiet_when_child_semantics_are_unchanged(self) -> None:
        snapshot_id = "1" * 64
        child_ids = [f"mission-active-child-{index}" for index in range(1, 4)]
        parent = {
            "id": "mission-active-parent",
            "status": "queued",
            "phase": "council_specialists_queued",
            "subtaskIds": child_ids,
            "analysisContext": {
                "kind": "ai_trade_council_parent",
                "snapshotId": snapshot_id,
                "contractDigest": "contract-test",
            },
            "createdAt": self.bridge.utc_now(),
            "updatedAt": self.bridge.utc_now(),
        }
        children = [
            {
                "id": child_id,
                "parentMissionId": parent["id"],
                "owner": owner,
                "toolId": self.bridge.AI_TRADE_COUNCIL_ALLOWED_TOOLS[owner],
                "status": "queued",
                "phase": "auto_guarded_queued",
                "result": "",
                "analysisContext": {
                    "kind": "ai_trade_council_vote",
                    "snapshotId": snapshot_id,
                    "contractDigest": "contract-test",
                    "agentId": owner,
                    "roleId": self.bridge.AI_TRADE_COUNCIL_AGENT_ROLES[owner],
                },
                "execution": {"dispatchState": "queued", "processStarted": False},
                "createdAt": self.bridge.utc_now(),
                "updatedAt": self.bridge.utc_now(),
            }
            for child_id, owner in zip(
                child_ids,
                ("optimization_agent", "backtest_analyst", "codex_mcp_operator"),
            )
        ]
        self.bridge.save_missions([parent, *children])

        first = self.bridge.refresh_parent_mission(parent["id"])
        audit_before = self.bridge.AUDIT_PATH.read_bytes()
        updated_before = first["updatedAt"]
        reconciled = self.bridge.reconcile_parent_mission_statuses()

        self.assertEqual(reconciled, 0)
        self.assertEqual(self.bridge.AUDIT_PATH.read_bytes(), audit_before)
        self.assertEqual(
            self.bridge.find_mission(parent["id"])["updatedAt"],
            updated_before,
        )
        self.assertRegex(
            first["delegation"]["childStateDigest"],
            r"^[0-9a-f]{64}$",
        )

    def test_concurrent_parent_refresh_has_one_report_and_one_audit_side_effect(self) -> None:
        parent = {
            "id": "mission-concurrent-refresh-parent",
            "status": "running",
            "phase": "specialists_running",
            "createdAt": self.bridge.utc_now(),
            "updatedAt": self.bridge.utc_now(),
        }
        children = [
            {
                "id": f"mission-concurrent-refresh-child-{index}",
                "parentMissionId": parent["id"],
                "owner": owner,
                "status": "completed",
                "phase": "completed",
                "result": f"result-{index}",
                "createdAt": self.bridge.utc_now(),
                "updatedAt": self.bridge.utc_now(),
                "completedAt": self.bridge.utc_now(),
            }
            for index, owner in enumerate(
                ("ea_developer", "backtest_analyst", "optimization_agent"),
                start=1,
            )
        ]
        self.bridge.save_missions([parent, *children])
        report_calls: list[str] = []

        def fake_report(payload: dict) -> dict:
            report_calls.append(str(payload.get("linkedMissionId") or ""))
            return {"id": "report-concurrent-refresh"}

        with mock.patch.object(self.bridge, "create_report", side_effect=fake_report):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(
                    pool.map(
                        lambda _index: self.bridge.refresh_parent_mission(parent["id"]),
                        range(2),
                    )
                )

        self.assertEqual(report_calls, [parent["id"]])
        self.assertTrue(all(item["status"] == "completed" for item in results))
        audits = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH, limit=20)
        self.assertEqual(
            sum(item.get("type") == "manager.parent_refreshed" for item in audits),
            1,
        )

    def test_archived_parent_is_not_resurrected_by_concurrent_refresh(self) -> None:
        parent = {
            "id": "mission-archive-refresh-parent",
            "status": "completed",
            "phase": "synthesized",
            "createdAt": self.bridge.utc_now(),
            "updatedAt": self.bridge.utc_now(),
            "completedAt": self.bridge.utc_now(),
        }
        children = [
            {
                "id": f"mission-archive-refresh-child-{index}",
                "parentMissionId": parent["id"],
                "owner": owner,
                "status": "completed",
                "phase": "completed",
                "result": "done",
                "createdAt": self.bridge.utc_now(),
                "updatedAt": self.bridge.utc_now(),
                "completedAt": self.bridge.utc_now(),
            }
            for index, owner in enumerate(
                ("ea_developer", "backtest_analyst", "optimization_agent"),
                start=1,
            )
        ]
        self.bridge.save_missions([parent, *children])

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(self.bridge.refresh_parent_mission, parent["id"]),
                pool.submit(self.bridge.archive_mission, parent["id"]),
            ]
            for future in futures:
                future.result()

        stored = self.bridge.find_mission(parent["id"])
        self.assertEqual(stored["status"], "archived")
        self.assertEqual(stored["archivedFromStatus"], "completed")

    def test_published_command_with_missing_ledger_record_never_redispatches(self) -> None:
        parent = {
            "id": "mission-published-command-parent",
            "tradeGateway": {
                "schemaVersion": "ai-trade-council-gateway-result-v1",
                "status": "queued",
                "reasonCode": "mt4_trade_command_published",
                "commandPublished": True,
                "commandId": "command-published-once",
            },
        }
        with (
            mock.patch.object(
                self.bridge,
                "_mt4_trade_gateway_command_read_model",
                return_value=None,
            ),
            mock.patch.object(
                self.bridge,
                "_mt4_trade_gateway_instance",
                side_effect=AssertionError("published command must never be queued again"),
            ),
        ):
            result = self.bridge.dispatch_ai_trade_council_trade_plan(parent, {})

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reasonCode"], "published_command_record_missing")
        self.assertTrue(result["commandPublished"])
        self.assertEqual(result["commandId"], "command-published-once")

    def test_archive_rejects_terminal_parent_with_active_child(self) -> None:
        parent = {
            "id": "mission-parent-active-child",
            "status": "blocked",
            "createdAt": self.bridge.utc_now(),
            "updatedAt": self.bridge.utc_now(),
        }
        child = {
            "id": "mission-active-child",
            "parentMissionId": parent["id"],
            "status": "queued",
            "createdAt": self.bridge.utc_now(),
            "updatedAt": self.bridge.utc_now(),
        }
        self.bridge.save_missions([parent, child])

        result = self.bridge.archive_mission(parent["id"])

        self.assertFalse(result["ok"])
        self.assertEqual(result["kind"], "mission_active")
        self.assertEqual(self.bridge.find_mission(parent["id"])["status"], "blocked")

    def test_stale_zero_child_council_parent_is_recovered_as_blocked(self) -> None:
        old = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        parent = {
            "id": "mission-zero-child-parent",
            "status": "running",
            "phase": "council_queue_assembling",
            "subtaskIds": [],
            "analysisContext": {
                "kind": "ai_trade_council_parent",
                "snapshotId": "2" * 64,
            },
            "createdAt": old,
            "updatedAt": old,
        }
        self.bridge.save_missions([parent])

        reconciled = self.bridge.reconcile_parent_mission_statuses()
        stored = self.bridge.find_mission(parent["id"])

        self.assertEqual(reconciled, 1)
        self.assertEqual(stored["status"], "blocked")
        self.assertEqual(stored["errorCode"], "council_queue_incomplete_recovered")

    def test_partial_queue_failure_blocks_every_created_child(self) -> None:
        self._configure_selected_mt4()
        snapshot_id = self.bridge.metatrader_snapshot_read_model(
            self.bridge.AI_TRADE_COUNCIL_PROP_ID
        )["chartSnapshot"]["snapshotId"]
        original_create = self.bridge.create_mission
        vote_creations = 0

        def flaky_create(payload: dict, *args, **kwargs):
            nonlocal vote_creations
            context = payload.get("analysisContext") if isinstance(payload, dict) else {}
            if isinstance(context, dict) and context.get("kind") == "ai_trade_council_vote":
                vote_creations += 1
                if vote_creations == 2:
                    raise RuntimeError("injected child creation failure")
            return original_create(payload, *args, **kwargs)

        patches = self._analysis_patches()
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3],
            mock.patch.object(self.bridge, "create_mission", side_effect=flaky_create),
        ):
            with self.assertRaisesRegex(RuntimeError, "injected child creation failure"):
                self.bridge.run_ai_trade_council_analysis({"snapshotId": snapshot_id})

        missions = self.bridge.load_missions()
        parents = [
            item
            for item in missions
            if (item.get("analysisContext") or {}).get("kind")
            == "ai_trade_council_parent"
        ]
        self.assertEqual(len(parents), 1)
        parent = parents[0]
        children = [
            item for item in missions if item.get("parentMissionId") == parent["id"]
        ]
        self.assertEqual(parent["status"], "blocked")
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0]["status"], "blocked")
        self.assertFalse((children[0].get("execution") or {}).get("processStarted"))

    def test_latest_retry_with_published_command_prevents_another_retry(self) -> None:
        self._configure_selected_mt4()
        snapshot_id = self.bridge.metatrader_snapshot_read_model(
            self.bridge.AI_TRADE_COUNCIL_PROP_ID
        )["chartSnapshot"]["snapshotId"]
        first = self._queue_analysis(snapshot_id)
        missions = self.bridge.load_missions()
        for mission in missions:
            if mission.get("id") == first["parent"]["id"]:
                mission.update({"status": "blocked", "phase": "review_required"})
            elif mission.get("parentMissionId") == first["parent"]["id"]:
                mission.update({"status": "blocked", "phase": "blocked"})
        self.bridge.save_missions(missions)
        second = self._queue_analysis(snapshot_id)
        missions = self.bridge.load_missions()
        second_parent_id = second["parent"]["id"]
        for mission in missions:
            if mission.get("id") == second_parent_id:
                mission.update({
                    "status": "blocked",
                    "phase": "review_required",
                    "tradeGateway": {
                        "commandPublished": True,
                        "commandId": "command-retry-two",
                    },
                })
            elif mission.get("parentMissionId") == second_parent_id:
                mission.update({"status": "blocked", "phase": "blocked"})
        self.bridge.save_missions(missions)

        third_attempt = self._queue_analysis(snapshot_id)

        self.assertEqual(third_attempt["kind"], "ai_trade_council_existing")
        self.assertEqual(third_attempt["parent"]["id"], second_parent_id)
        parents = [
            item
            for item in self.bridge.load_missions()
            if (item.get("analysisContext") or {}).get("kind")
            == "ai_trade_council_parent"
        ]
        self.assertEqual(len(parents), 2)

    def test_malformed_updated_at_falls_back_to_completed_at(self) -> None:
        aggregated_at = datetime.now(timezone.utc)
        parent = {
            "id": "mission-parent-malformed-child-time",
            "status": "completed",
            "phase": "synthesized",
            "delegation": {
                "finalReportId": "report-malformed-child-time",
                "lastAggregatedAt": aggregated_at.isoformat(),
            },
        }
        child = {
            "id": "mission-child-malformed-time",
            "parentMissionId": parent["id"],
            "status": "completed",
            "updatedAt": "not-a-time",
            "completedAt": (aggregated_at - timedelta(minutes=1)).isoformat(),
        }

        self.assertTrue(
            self.bridge._parent_mission_is_already_aggregated(parent, [child])
        )

    def test_retry_lineage_handles_double_digit_suffixes(self) -> None:
        base_key = "ai-trade-council:test-snapshot"
        missions = []
        for retry_index in (9, 10):
            missions.append({
                "id": f"mission-retry-{retry_index}",
                "idempotencyKey": f"{base_key}-retry-{retry_index}",
                "analysisContext": {"kind": "ai_trade_council_parent"},
                "status": "blocked",
            })
        self.bridge.save_missions(missions)

        retry_key, suffix = self.bridge._next_ai_trade_council_retry_idempotency(
            base_key
        )
        latest = self.bridge._latest_ai_trade_council_retry_parent(base_key)

        self.assertEqual(retry_key, f"{base_key}-retry-11")
        self.assertEqual(suffix, "-retry-11")
        self.assertEqual(latest["id"], "mission-retry-10")


if __name__ == "__main__":
    unittest.main()
