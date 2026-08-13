from __future__ import annotations

import importlib.util
import json
import os
import re
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
RUNNER_PATH = PROJECT_ROOT / "runner" / "codex_cli_runner.py"
MQL4_PATH = PROJECT_ROOT / "integrations" / "mt4-readonly" / "MetafxHQReadOnlySnapshot.mq4"


def load_bridge():
    spec = importlib.util.spec_from_file_location("metafx_bridge_mt4_readonly_tests", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load bridge module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_runner():
    spec = importlib.util.spec_from_file_location("metafx_runner_mt4_council_tests", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load runner module")
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
            "timeframe": "H4",
            "bid": 2388.12,
            "ask": 2388.35,
            "spreadPoints": 23,
            "bars": [
                {
                    "time": 1785196800 + index * 14400,
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
            "serverDay": "2026.07.29",
            "realizedProfit": 120.5,
            "floatingProfit": -12.25,
            "netPnl": 108.25,
            "tradesClosed": 4,
            "wins": 3,
            "losses": 1,
        },
        "accountSummary": {
            "currency": "USD",
            "balance": 10000,
            "equity": 9987.75,
            "margin": 200,
            "freeMargin": 9787.75,
        },
        "positionsSummary": {
            "count": 1,
            "buyCount": 1,
            "sellCount": 0,
            "totalLots": 0.1,
            "floatingProfit": -12.25,
        },
    }


class Mt4ReadOnlyCouncilTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bridge = load_bridge()
        self.runner = load_runner()

    def test_decision_horizon_preserves_broker_clock_identity_across_offsets(self) -> None:
        observed = datetime(2026, 8, 13, 3, 0, 2, tzinfo=timezone.utc)

        for broker_offset_hours in (3, -5):
            with self.subTest(broker_offset_hours=broker_offset_hours):
                raw_broker_closed_bar = (
                    int(observed.timestamp())
                    + broker_offset_hours * 60 * 60
                    - 5 * 60
                )
                expected_broker_clock_identity = raw_broker_closed_bar + 2 * 5 * 60
                actual = self.bridge._ai_trade_council_expected_valid_until(
                    raw_broker_closed_bar,
                    "M5",
                    1,
                )

                self.assertEqual(actual, expected_broker_clock_identity)

    def test_decision_horizon_identity_fails_closed_on_invalid_inputs(self) -> None:
        for closed_bar_time in (
            None,
            True,
            "1786589700",
            100,
        ):
            with self.subTest(closed_bar_time=closed_bar_time):
                self.assertIsNone(
                    self.bridge._ai_trade_council_expected_valid_until(
                        closed_bar_time,
                        "M5",
                        1,
                    )
                )

    def test_analytics_connection_panel_uses_backend_closed_bar_automation_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.bridge.RUNTIME_DIR = root / "runtime"
            self.bridge.AUDIT_PATH = self.bridge.RUNTIME_DIR / "bridge-audit.jsonl"
            self.bridge.set_ai_trade_council_automation({"enabled": True})
            checklist = self.bridge.dashboard_connection_checklist(
                "left_analytics_console",
                bridge={
                    "mode": "Codex Runner Ready",
                    "status": "guarded",
                    "codex": {"status": "ready"},
                    "mcp": {"status": "config_present", "configPresent": True},
                    "time": "2026-07-31T00:00:00+00:00",
                },
                quota={
                    "ok": True,
                    "status": "ready",
                    "primary": {"usedPercent": 12, "remainingPercent": 88},
                },
                terminals=self.bridge.metatrader_status_read_model(
                    {"mt4": 0, "mt5": 0},
                    {"supported": True, "mt4": 0, "mt5": 0},
                ),
            )

            operation = checklist["operationMode"]
            self.assertEqual(operation["current"], "auto_on_new_closed_bar")
            self.assertEqual(operation["labelTh"], "อัตโนมัติเมื่อแท่งใหม่ปิด")
            self.assertTrue(operation["autoAnalysis"]["enabled"])
            self.assertEqual(operation["autoAnalysis"]["pollSeconds"], 5)
            self.assertNotIn("ไม่ใช้รอบอัตโนมัติ", operation["autoAnalysis"]["labelTh"])

    def _configure_selected_mt4(self, root: Path) -> str:
        runtime = root / "runtime"
        common = root / "common"
        install = root / "Program Files" / "RoboForex MT4 Terminal"
        data_root = root / "AppData" / "MetaQuotes" / "Terminal"
        data = data_root / "ROBOHASH"
        install.mkdir(parents=True)
        (install / "terminal.exe").write_bytes(b"MZ")
        (data / "MQL4").mkdir(parents=True)
        (data / "origin.txt").write_text(str(install), encoding="utf-16")

        self.bridge.RUNTIME_DIR = runtime
        self.bridge.MISSIONS_PATH = runtime / "missions.json"
        self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
        self.bridge.AGENT_EVENTS_PATH = runtime / "agent-events.jsonl"
        self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
        self.bridge.METATRADER_COMMON_FILES_DIR = common
        self.bridge.PROJECT_ROOT = root
        self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR = root / "workspace"
        self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR = (
            self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR
            / "ai-trade-council"
            / "snapshots"
        )

        discovered = self.bridge.discover_metatrader_installations(
            roots=[install.parent, data_root],
            include_candidates=True,
        )
        self.assertEqual(discovered["mt4"], 1)
        running = self.bridge.discover_running_metatrader(
            process_locations={"mt4": [str(install)], "mt5": []}
        )
        candidates = self.bridge._sync_metatrader_candidate_registry(
            discovered["_candidateLocations"],
            running,
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["runningState"], "platform_running_detected")
        with self.bridge.METATRADER_TARGETS_LOCK:
            store = self.bridge._load_metatrader_target_store_unlocked()
            store["selections"][self.bridge.AI_TRADE_COUNCIL_PROP_ID] = {
                "candidateId": candidate["candidateId"],
                "selectedAt": self.bridge.utc_now(),
            }
            self.bridge._write_metatrader_target_store_unlocked(store)
        return candidate["candidateId"]

    def test_broker_branded_discovery_pairs_origin_with_exact_running_process(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id = self._configure_selected_mt4(root)
            public = self.bridge._available_metatrader_candidates_from_store()
            self.assertEqual(public[0]["candidateId"], candidate_id)
            serialized = json.dumps(public, ensure_ascii=False).lower()
            self.assertNotIn(str(root).lower(), serialized)
            self.assertNotIn("processid", serialized)
            self.assertNotIn("terminalpath", serialized)

    def test_snapshot_reader_is_strict_fresh_and_frontend_safe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id = self._configure_selected_mt4(root)
            snapshot_file = self.bridge._metatrader_snapshot_file(candidate_id)
            self.assertIsNotNone(snapshot_file)
            snapshot_file.parent.mkdir(parents=True)
            snapshot_file.write_text(
                json.dumps(snapshot_payload(candidate_id), ensure_ascii=False),
                encoding="utf-8",
            )
            model = self.bridge.metatrader_snapshot_read_model(
                self.bridge.AI_TRADE_COUNCIL_PROP_ID
            )
            self.assertTrue(model["adapter"]["ready"])
            self.assertTrue(model["dailySummary"]["available"])
            self.assertEqual(model["dailySummary"]["netPnl"], 108.25)
            self.assertEqual(model["chartSnapshot"]["symbol"], "XAUUSD")
            self.assertEqual(model["chartSnapshot"]["timeframe"], "H4")
            self.assertEqual(model["chartSnapshot"]["barCount"], 140)
            technical = model["chartSnapshot"]["technicalIndicators"]
            self.assertTrue(technical["available"])
            self.assertEqual(
                technical["basis"],
                "backend_calculated_closed_bars_only",
            )
            self.assertEqual(technical["barCount"], 140)
            self.assertEqual(technical["seriesBarCount"], 140)
            self.assertEqual(technical["analysisBarCount"], 120)
            self.assertEqual(technical["scope"], "dashboard_source_window")
            self.assertEqual(
                technical["formulaVersion"],
                "metafx-deterministic-core20-price-action-v3",
            )
            self.assertEqual(len(technical["series"]), 140)
            self.assertIsNotNone(technical["ema12"])
            self.assertIsNotNone(technical["rsi14"])
            price_action = model["chartSnapshot"]["priceActionFeatures"]
            self.assertEqual(price_action["barCount"], 140)
            self.assertEqual(price_action["seriesBarCount"], 140)
            self.assertEqual(price_action["analysisBarCount"], 120)
            self.assertEqual(price_action["scope"], "dashboard_source_window")
            self.assertEqual(
                model["chartSnapshot"]["analysisWindow"]["requestedBars"],
                120,
            )
            self.assertEqual(
                model["chartSnapshot"]["analysisWindow"]["usedBars"],
                120,
            )
            self.assertEqual(
                [item["agentId"] for item in model["analysisReadiness"]["agents"]],
                ["optimization_agent", "backtest_analyst", "codex_mcp_operator"],
            )
            serialized = json.dumps(model, ensure_ascii=False).lower()
            for forbidden in (
                "accountlogin",
                "accountnumber",
                "brokerserver",
                "password",
                "terminalpath",
                "processid",
                "ticket",
                str(root).lower(),
            ):
                self.assertNotIn(forbidden, serialized)

            stale_time = snapshot_file.stat().st_mtime - 120
            os.utime(snapshot_file, (stale_time, stale_time))
            stale = self.bridge.metatrader_snapshot_read_model(
                self.bridge.AI_TRADE_COUNCIL_PROP_ID
            )
            self.assertFalse(stale["adapter"]["ready"])
            self.assertEqual(stale["adapter"]["status"], "stale")

    def test_deterministic_indicator_series_uses_closed_bar_formula_contract(self) -> None:
        bars = snapshot_payload("mtc-indicator-series")["chart"]["bars"]
        technical = self.bridge._technical_indicator_snapshot(bars)

        self.assertTrue(technical["available"])
        self.assertEqual(
            technical["formulaVersion"],
            "metafx-deterministic-core20-price-action-v3",
        )
        self.assertEqual(len(technical["series"]), len(bars))
        self.assertEqual(technical["series"][0]["time"], bars[0]["time"])
        self.assertIsNone(technical["series"][0]["rsi14"])
        self.assertIsNone(technical["series"][0]["atr14"])
        self.assertEqual(technical["rsi14"], 100.0)
        self.assertEqual(technical["atr14"], 7.0)
        self.assertIsNotNone(technical["macdSignal"])
        self.assertIsNotNone(technical["macdHistogram"])

    def test_backend_analysis_window_and_artifact_keep_exact_240_closed_bars(self) -> None:
        snapshot_id = "a" * 64
        chart = snapshot_payload("mtc-window-240", 240)["chart"]
        source = {
            "dailySummary": {"available": True},
            "chartSnapshot": {
                "available": True,
                "snapshotId": snapshot_id,
                **chart,
            },
        }
        windowed = self.bridge._ai_trade_council_windowed_snapshot(source, 240)
        analysis_window = windowed["chartSnapshot"]["analysisWindow"]
        self.assertEqual(analysis_window["requestedBars"], 240)
        self.assertEqual(analysis_window["usedBars"], 240)
        self.assertTrue(analysis_window["closedBarsOnly"])
        self.assertEqual(len(windowed["chartSnapshot"]["bars"]), 240)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original_workspace = self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR
            original_snapshot_dir = self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR
            try:
                self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR = root / "workspace"
                self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR = (
                    self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR
                    / "ai-trade-council"
                    / "snapshots"
                )
                artifact_relative = self.bridge._write_ai_trade_council_snapshot_artifact(
                    windowed
                )
                artifact = json.loads(
                    (
                        self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR
                        / artifact_relative
                    ).read_text(encoding="utf-8")
                )
            finally:
                self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR = original_workspace
                self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR = original_snapshot_dir

        policy = artifact["policy"]
        self.assertEqual(policy["analysisBarCountRequested"], 240)
        self.assertEqual(policy["analysisBarCountUsed"], 240)
        self.assertNotIn("requestedAnalysisBarCount", policy)
        self.assertNotIn("usedAnalysisBarCount", policy)
        self.assertEqual(
            policy["indicatorFormulaVersion"],
            "metafx-deterministic-core20-price-action-v3",
        )

        with self.assertRaises(self.bridge.RequestError) as blocked:
            self.bridge._ai_trade_council_windowed_snapshot(source, 300)
        self.assertEqual(blocked.exception.status, 409)

    def test_snapshot_reader_supports_only_selected_candidate_legacy_local_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id = self._configure_selected_mt4(root)
            with self.bridge.METATRADER_TARGETS_LOCK:
                store = self.bridge._load_metatrader_target_store_unlocked()
                record = dict(store["candidates"][candidate_id])
            legacy_file = self.bridge._legacy_metatrader_snapshot_file(
                record,
                candidate_id,
            )
            self.assertIsNotNone(legacy_file)
            legacy_file.parent.mkdir(parents=True)
            legacy_file.write_text(
                json.dumps(snapshot_payload(candidate_id), ensure_ascii=False),
                encoding="utf-8",
            )
            legacy_model = self.bridge.metatrader_snapshot_read_model(
                self.bridge.AI_TRADE_COUNCIL_PROP_ID
            )
            self.assertTrue(legacy_model["adapter"]["ready"])
            self.assertEqual(
                legacy_model["adapter"]["source"],
                "mt4_terminal_local_snapshot_legacy",
            )
            self.assertTrue(legacy_model["adapter"]["legacyFallback"])
            self.assertTrue(legacy_model["adapter"]["migrationNeeded"])
            serialized = json.dumps(legacy_model, ensure_ascii=False).lower()
            self.assertNotIn(str(root).lower(), serialized)

            common_file = self.bridge._metatrader_snapshot_file(candidate_id)
            common_file.parent.mkdir(parents=True)
            common_file.write_text(
                json.dumps(snapshot_payload(candidate_id), ensure_ascii=False),
                encoding="utf-8",
            )
            newer = max(common_file.stat().st_mtime, legacy_file.stat().st_mtime) + 2
            os.utime(common_file, (newer, newer))
            common_model = self.bridge.metatrader_snapshot_read_model(
                self.bridge.AI_TRADE_COUNCIL_PROP_ID
            )
            self.assertEqual(
                common_model["adapter"]["source"],
                "mt4_file_common_snapshot",
            )
            self.assertFalse(common_model["adapter"]["legacyFallback"])
            self.assertFalse(common_model["adapter"]["migrationNeeded"])

            unsafe_record = {**record, "dataPath": str(root / "other-terminal")}
            self.assertIsNone(
                self.bridge._legacy_metatrader_snapshot_file(
                    unsafe_record,
                    candidate_id,
                )
            )

    def test_analyze_endpoint_queues_exact_three_snapshot_bound_guarded_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id = self._configure_selected_mt4(root)
            snapshot_file = self.bridge._metatrader_snapshot_file(candidate_id)
            snapshot_file.parent.mkdir(parents=True)
            snapshot_file.write_text(
                json.dumps(snapshot_payload(candidate_id), ensure_ascii=False),
                encoding="utf-8",
            )
            originals = {
                "load_operator_mode_record": self.bridge.load_operator_mode_record,
                "bridge_status": self.bridge.bridge_status,
                "codex_rate_limits": self.bridge.codex_rate_limits,
                "check_rate_limit": self.bridge.check_rate_limit,
            }
            try:
                self.bridge.load_operator_mode_record = lambda: {
                    "mode": "auto_guarded",
                    "updatedAt": self.bridge.utc_now(),
                }
                self.bridge.bridge_status = lambda: {
                    "status": "guarded",
                    "codex": {"status": "ready"},
                    "mcp": {"status": "config_present"},
                    "policy": {"operatorMode": "auto_guarded"},
                    "time": self.bridge.utc_now(),
                }
                self.bridge.codex_rate_limits = lambda force=False: {
                    "ok": True,
                    "status": "ready",
                    "stale": False,
                    "limitReached": False,
                    "primary": {"usedPercent": 10, "remainingPercent": 90},
                }
                self.bridge.check_rate_limit = lambda *args, **kwargs: (True, 0)
                current_snapshot_id = self.bridge.metatrader_snapshot_read_model(
                    self.bridge.AI_TRADE_COUNCIL_PROP_ID
                )["chartSnapshot"]["snapshotId"]
                with self.assertRaises(self.bridge.RequestError) as changed:
                    self.bridge.run_ai_trade_council_analysis(
                        {"snapshotId": "f" * 64}
                    )
                self.assertEqual(changed.exception.status, 409)
                result = self.bridge.run_ai_trade_council_analysis(
                    {"snapshotId": current_snapshot_id}
                )
                replay = self.bridge.run_ai_trade_council_analysis(
                    {"snapshotId": current_snapshot_id}
                )
            finally:
                for name, value in originals.items():
                    setattr(self.bridge, name, value)

            self.assertTrue(result["ok"])
            self.assertEqual(result["kind"], "ai_trade_council_queued")
            self.assertEqual(len(result["subtasks"]), 3)
            self.assertEqual(result["parent"]["id"], result["manager"]["id"])
            self.assertEqual(replay["kind"], "ai_trade_council_existing")
            self.assertEqual(replay["snapshotId"], result["snapshotId"])
            self.assertFalse(result["terminalActions"])

            missions = self.bridge.load_missions()
            parent = next(item for item in missions if item["owner"] == "manager")
            children = [item for item in missions if item.get("parentMissionId") == parent["id"]]
            self.assertEqual(len(children), 3)
            self.assertEqual(
                {item["owner"] for item in children},
                {"optimization_agent", "codex_mcp_operator", "backtest_analyst"},
            )
            self.assertEqual(
                {item["toolId"] for item in children},
                {"codex_cli_task", "codex_web_research"},
            )
            parent_context = parent["analysisContext"]
            self.assertEqual(
                parent_context["validUntilBarTime"],
                parent_context["closedBarIdentity"]["closedBarTime"] + 2 * 4 * 60 * 60,
            )
            self.assertEqual(
                parent_context["validUntilBarTimeDomain"],
                "mt4_broker_clock",
            )
            self.assertEqual(
                parent_context["decisionExpirySource"],
                "round_deadline_at_utc",
            )
            artifact_reference = parent_context["snapshotArtifact"]
            artifact_digest = parent_context["snapshotArtifactDigest"]
            self.assertEqual(
                artifact_reference,
                self.bridge.ai_trade_council_snapshot_reference(
                    result["snapshotId"],
                    artifact_digest,
                ),
            )
            for child in children:
                self.assertTrue(child["autoEligible"])
                self.assertEqual(child["executionMode"], "auto_guarded")
                self.assertFalse(child["requiresHumanApproval"])
                self.assertEqual(
                    child["analysisContext"]["snapshotId"],
                    result["snapshotId"],
                )
                self.assertIn(result["snapshotId"], child["detail"])
                self.assertEqual(
                    child["analysisContext"]["snapshotArtifact"],
                    artifact_reference,
                )
                self.assertEqual(
                    child["analysisContext"]["snapshotArtifactDigest"],
                    artifact_digest,
                )
                self.assertLessEqual(child["budget"]["timeoutSeconds"], 180)
                self.assertLessEqual(child["budget"]["outputLimitChars"], 7000)
            artifact = (
                self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR
                / Path(artifact_reference).name
            )
            self.assertTrue(artifact.is_file())
            stored_artifact = self.bridge.read_json(artifact, {})
            self.assertEqual(stored_artifact["artifactDigest"], artifact_digest)
            self.assertEqual(
                self.bridge._ai_trade_council_snapshot_artifact_digest(
                    stored_artifact
                ),
                artifact_digest,
            )

    def test_dynamic_checklist_requires_fresh_snapshot_codex_quota_and_auto_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id = self._configure_selected_mt4(root)
            snapshot_file = self.bridge._metatrader_snapshot_file(candidate_id)
            snapshot_file.parent.mkdir(parents=True)
            snapshot_file.write_text(
                json.dumps(snapshot_payload(candidate_id), ensure_ascii=False),
                encoding="utf-8",
            )
            public_candidates = self.bridge._available_metatrader_candidates_from_store()
            terminals = self.bridge.metatrader_status_read_model(
                {"mt4": 1, "mt5": 0},
                {"supported": True, "mt4": 1, "mt5": 0},
                public_candidates,
            )
            fake_bridge = {
                "status": "guarded",
                "codex": {"status": "ready"},
                "mcp": {"status": "config_present"},
                "policy": {"operatorMode": "auto_guarded"},
                "time": self.bridge.utc_now(),
            }
            original_mode = self.bridge.load_operator_mode_record
            try:
                self.bridge.load_operator_mode_record = lambda: {
                    "mode": "auto_guarded",
                    "updatedAt": self.bridge.utc_now(),
                }
                ready = self.bridge.dashboard_connection_checklist(
                    self.bridge.AI_TRADE_COUNCIL_PROP_ID,
                    bridge=fake_bridge,
                    quota={
                        "ok": True,
                        "status": "ready",
                        "stale": False,
                        "limitReached": False,
                        "primary": {"usedPercent": 10, "remainingPercent": 90},
                    },
                    terminals=terminals,
                )
                ready_items = {item["id"]: item for item in ready["items"]}
                self.assertEqual(ready_items["trading_state_adapter"]["status"], "connected")
                self.assertEqual(ready_items["ai_trader_ensemble"]["status"], "ready")

                stale_time = snapshot_file.stat().st_mtime - 120
                os.utime(snapshot_file, (stale_time, stale_time))
                stale = self.bridge.dashboard_connection_checklist(
                    self.bridge.AI_TRADE_COUNCIL_PROP_ID,
                    bridge=fake_bridge,
                    quota={
                        "ok": True,
                        "status": "ready",
                        "stale": False,
                        "limitReached": False,
                        "primary": {"usedPercent": 10, "remainingPercent": 90},
                    },
                    terminals=terminals,
                )
                stale_items = {item["id"]: item for item in stale["items"]}
                self.assertEqual(stale_items["trading_state_adapter"]["status"], "stale")
                self.assertEqual(stale_items["ai_trader_ensemble"]["status"], "waiting_snapshot")
                self.assertEqual(stale["overallStatus"], "needs_attention")
            finally:
                self.bridge.load_operator_mode_record = original_mode

    def test_vote_validation_and_manager_consensus_are_same_snapshot_only(self) -> None:
        snapshot_id = "a" * 64
        now = datetime.now(timezone.utc)
        valid_until = int((now + timedelta(hours=1)).timestamp())
        round_deadline = (now + timedelta(minutes=4)).isoformat()
        news_observed_at = now.isoformat().replace("+00:00", "Z")
        parent = {
            "analysisContext": {
                "kind": "ai_trade_council_parent",
                "snapshotId": snapshot_id,
                "referencePrice": 2400.0,
                "horizonBars": 1,
                "validUntilBarTime": valid_until,
                "roundDeadlineAt": round_deadline,
                "contractDigest": "contract-v2",
                "closedBarIdentity": {
                    "candidateId": "mtc-test",
                    "streamKey": self.bridge.payload_digest(
                        "mtc-test",
                        "XAUUSD",
                        "H4",
                    ),
                    "symbol": "XAUUSD",
                    "timeframe": "H4",
                    "closedBarTime": int(now.timestamp()) - 14400,
                },
                "qualityGate": {
                    "passed": True,
                    "reasonCodes": [],
                    "confidenceFloorDefault": 70,
                    "confidenceFloorByRole": {
                        "technical": 70,
                        "price_action": 70,
                        "news": 70,
                    },
                    "minimumRewardRiskRatio": 1.0,
                    "technical": {"volatilityState": "NORMAL"},
                    "executionEligibility": {
                        "shadow": True,
                        "demo": False,
                        "live": False,
                    },
                },
            }
        }
        children = []
        for agent_id, role_id in self.bridge.AI_TRADE_COUNCIL_AGENT_ROLES.items():
            raw = {
                "snapshotId": snapshot_id,
                "agentId": agent_id,
                "roleId": role_id,
                "decision": "BUY",
                "confidence": 70,
                "horizonBars": 1,
                "validUntilBarTime": valid_until,
                "stopLossPrice": 2380.0 if role_id == "price_action" else None,
                "takeProfitPrice": 2420.0 if role_id == "price_action" else None,
                "indicatorValidation": "PASS" if role_id == "technical" else None,
                "volatilityState": "NORMAL" if role_id == "technical" else None,
                "eventRisk": "ALLOW" if role_id == "news" else None,
                "horizon": "4 ชั่วโมง",
                "observations": ["ข้อมูลสนับสนุนทิศทางเดียวกัน"],
                "invalidation": "โครงสร้างราคาเปลี่ยน",
                "evidence": (
                    [
                        {
                            "label": "Source one",
                            "observedAt": news_observed_at,
                            "sourceUrl": "https://example.com/one",
                        },
                        {
                            "label": "Source two",
                            "observedAt": news_observed_at,
                            "sourceUrl": "https://example.org/two",
                        },
                    ]
                    if role_id == "news"
                    else [
                        {
                            "label": "Snapshot",
                            "observedAt": "2026-07-29T00:00:00Z",
                            "sourceUrl": None,
                        }
                    ]
                ),
                "warnings": [],
            }
            context = {
                "snapshotId": snapshot_id,
                "agentId": agent_id,
                "roleId": role_id,
                "referencePrice": 2400.0,
                "horizonBars": 1,
                "validUntilBarTime": valid_until,
                "volatilityState": "NORMAL",
                "qualityPolicy": {
                    "maximumNewsAgeSeconds": 86400,
                    "maximumFutureEvidenceSkewSeconds": 300,
                    "minimumDistinctNewsDomains": 2,
                },
            }
            vote = self.bridge.validate_ai_trade_council_vote(
                json.dumps(raw, ensure_ascii=False),
                context,
            )
            self.assertIsNotNone(vote)
            children.append({"owner": agent_id, "councilVote": vote})
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        self.assertTrue(consensus["ready"])
        self.assertTrue(consensus["unanimous"])
        self.assertEqual(consensus["decision"], "BUY")
        self.assertTrue(consensus["qualityGate"]["passed"])
        self.assertEqual(
            consensus["tradePlan"]["priceAggregation"],
            "price_action_single_owner",
        )
        self.assertEqual(consensus["outcomeTracking"]["status"], "pending")
        self.assertFalse(consensus["riskGuard"]["voting"])
        self.assertEqual(
            consensus["riskGuard"]["status"],
            "not_evaluated_by_agent",
        )
        self.assertFalse(consensus["terminalActions"])

    def test_read_model_keeps_latest_consensus_when_live_snapshot_advances(self) -> None:
        analyzed_snapshot_id = "a" * 64
        current_snapshot_id = "b" * 64
        parent_mission_id = "mission-council-completed"
        candidate_id = "mtc-consensus-projection"
        closed_bar_identity = {
            "candidateId": candidate_id,
            "streamKey": self.bridge._ai_trade_council_stream_key(
                candidate_id,
                "XAUUSD",
                "H4",
            ),
            "symbol": "XAUUSD",
            "timeframe": "H4",
            "closedBarTime": 1_785_254_400,
        }
        parent = {
            "id": parent_mission_id,
            "title": "สภา AI Trade วิเคราะห์ XAUUSD H4",
            "owner": "manager",
            "status": "completed",
            "phase": "synthesized",
            "reportType": "ai_trade_council_report",
            "createdAt": "2026-07-29T00:00:00Z",
            "updatedAt": "2026-07-29T00:03:00Z",
            "analysisContext": {
                "kind": "ai_trade_council_parent",
                "snapshotId": analyzed_snapshot_id,
                "closedBarIdentity": closed_bar_identity,
            },
            "delegation": {
                "mode": "ai_trade_council_read_only",
                "snapshotId": analyzed_snapshot_id,
                "subtaskCount": 3,
            },
            "councilDecision": {
                "schemaVersion": "ai-trade-council-consensus-v1",
                "snapshotId": analyzed_snapshot_id,
                "ready": True,
                "decision": "NO_TRADE",
                "unanimous": False,
                "voteCount": 3,
                "votes": [
                    {
                        "snapshotId": analyzed_snapshot_id,
                        "agentId": agent_id,
                        "roleId": role_id,
                        "decision": "HOLD",
                        "confidence": 60,
                        "observations": ["หลักฐานทิศทางยังไม่ชัดเจน"],
                    }
                    for agent_id, role_id in self.bridge.AI_TRADE_COUNCIL_AGENT_ROLES.items()
                ],
                "averageConfidence": 60,
                "decisionProvenance": {
                    "schemaVersion": "ai-trade-council-decision-provenance-v1",
                    "snapshotId": analyzed_snapshot_id,
                    "closedBarIdentity": closed_bar_identity,
                },
                "riskGuard": {
                    "agentId": "risk_guard",
                    "voting": False,
                    "status": "passed_read_only_policy",
                    "terminalActions": False,
                },
                "terminalActions": False,
            },
        }
        snapshot = {
            "selectedCandidateId": candidate_id,
            "adapter": {"ready": True, "status": "ready", "reasonCode": "ready"},
            "chartSnapshot": {
                "available": True,
                "status": "ready",
                "snapshotId": current_snapshot_id,
                "observedAt": "2026-07-29T00:05:00Z",
                "symbol": "XAUUSD",
                "timeframe": "H4",
                "bid": 2388.12,
                "ask": 2388.35,
                "spreadPoints": 23,
            },
            "dailySummary": {"available": True},
            "analysisReadiness": {"available": True, "status": "ready"},
        }
        checklist = {
            "checkedAt": "2026-07-29T00:05:00Z",
            "metatraderSelection": {
                "selectedCandidate": {"id": "mt4-selected", "platform": "mt4"},
                "candidates": [],
            },
            "items": [
                {"id": "mt4_terminal", "status": "detected"},
                {"id": "trading_state_adapter", "status": "ready"},
                {"id": "ai_trader_ensemble", "status": "ready"},
                {"id": "risk_policy", "status": "ready"},
                {"id": "live_trading", "status": "disabled"},
            ],
        }
        original_snapshot_read_model = self.bridge.metatrader_snapshot_read_model
        unrelated_active = {
            "id": "mission-old-dashboard-task",
            "title": "งาน Dashboard เก่าที่ไม่ใช่ Council",
            "owner": "manager",
            "status": "queued",
            "createdAt": "2026-07-28T00:00:00Z",
        }
        older_parent = json.loads(json.dumps(parent))
        older_parent.update({
            "id": "mission-council-older-array-first",
            "createdAt": "2026-07-28T12:00:00Z",
            "updatedAt": "2026-07-28T12:03:00Z",
        })
        older_parent["councilDecision"]["snapshotId"] = "c" * 64
        older_parent["analysisContext"]["snapshotId"] = "c" * 64
        older_parent["delegation"]["snapshotId"] = "c" * 64
        try:
            self.bridge.metatrader_snapshot_read_model = lambda _prop_id: snapshot
            model = self.bridge._ai_trade_council_read_model(
                [unrelated_active, older_parent, parent],
                [],
                checklist,
            )
        finally:
            self.bridge.metatrader_snapshot_read_model = original_snapshot_read_model

        live_consensus = model["liveAnalysis"]["consensus"]
        pipeline_snapshot = model["decisionPipeline"]["snapshot"]
        self.assertTrue(live_consensus["available"])
        self.assertEqual(live_consensus["sourceMissionId"], parent_mission_id)
        self.assertEqual(live_consensus["snapshotId"], analyzed_snapshot_id)
        self.assertTrue(live_consensus["identityValid"])
        self.assertEqual(live_consensus["candidateId"], candidate_id)
        self.assertEqual(live_consensus["channelId"], candidate_id)
        self.assertEqual(
            live_consensus["streamKey"],
            closed_bar_identity["streamKey"],
        )
        self.assertEqual(live_consensus["symbol"], "XAUUSD")
        self.assertEqual(live_consensus["timeframe"], "H4")
        self.assertEqual(
            live_consensus["closedBarIdentity"],
            closed_bar_identity,
        )
        self.assertEqual(
            live_consensus["streamIdentity"]["snapshotId"],
            analyzed_snapshot_id,
        )
        self.assertEqual(
            live_consensus["decisionProvenance"]["closedBarIdentity"],
            closed_bar_identity,
        )
        self.assertEqual(live_consensus["currentSnapshotId"], current_snapshot_id)
        self.assertFalse(live_consensus["matchesCurrentSnapshot"])
        self.assertFalse(live_consensus["matchesCurrentContext"])
        self.assertEqual(pipeline_snapshot["id"], analyzed_snapshot_id)
        self.assertEqual(pipeline_snapshot["currentId"], current_snapshot_id)
        self.assertFalse(pipeline_snapshot["matchesCurrent"])
        self.assertIsNone(pipeline_snapshot["observedAt"])
        self.assertEqual(model["decisionPipeline"]["summary"]["total"], 2)
        self.assertEqual(model["decisionPipeline"]["summary"]["active"], 0)
        self.assertNotIn(
            unrelated_active["id"],
            {
                item["id"]
                for item in model["decisionPipeline"]["items"]
            },
        )

    def test_runner_schema_transports_exactly_one_snapshot_bound_vote(self) -> None:
        snapshot_id = "b" * 64
        valid_until = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        context = {
            "snapshotId": snapshot_id,
            "agentId": "optimization_agent",
            "roleId": "technical",
            "referencePrice": 2400.0,
            "horizonBars": 1,
            "validUntilBarTime": valid_until,
            "volatilityState": "NORMAL",
        }
        raw_vote = {
            "snapshotId": snapshot_id,
            "agentId": "optimization_agent",
            "roleId": "technical",
            "decision": "SELL",
            "confidence": 62,
            "horizonBars": 1,
            "validUntilBarTime": valid_until,
            "stopLossPrice": None,
            "takeProfitPrice": None,
            "indicatorValidation": "PASS",
            "volatilityState": "NORMAL",
            "eventRisk": None,
            "horizon": "1-3 แท่ง H4",
            "observations": ["ราคาอยู่ต่ำกว่า EMA200", "Momentum อ่อนตัว"],
            "invalidation": "ราคาปิดกลับเหนือแนวต้านล่าสุด",
            "evidence": [
                {
                    "label": "Snapshot H4",
                    "observedAt": "2026-07-29T00:00:00Z",
                    "sourceUrl": None,
                }
            ],
            "warnings": ["เป็นการวิเคราะห์แบบอ่านอย่างเดียว"],
        }
        encoded = json.dumps(raw_vote, ensure_ascii=False, separators=(",", ":"))
        runner_result = {
            "ok": True,
            "workStatus": "completed",
            "finalMessage": encoded,
        }
        vote = self.bridge.validate_ai_trade_council_vote_result(
            runner_result,
            context,
        )
        self.assertIsNotNone(vote)
        self.assertEqual(vote["decision"], "SELL")
        self.assertEqual(vote["confidence"], 62)

        duplicated = {
            **runner_result,
            "finalMessage": f"{encoded}\n{encoded}",
        }
        self.assertIsNone(
            self.bridge.validate_ai_trade_council_vote_result(duplicated, context)
        )
        wrong_snapshot = {
            **raw_vote,
            "snapshotId": "f" * 64,
        }
        self.assertIsNone(
            self.bridge.validate_ai_trade_council_vote_result(
                {
                    "finalMessage": json.dumps(
                        wrong_snapshot,
                        ensure_ascii=False,
                    )
                },
                context,
            )
        )

    def test_council_prompt_explains_schema_bound_embedded_snapshot(self) -> None:
        contract = self.bridge.load_ai_trade_council_prompt_contract()
        self.assertEqual(
            contract["sharedPolicy"]["runnerVoteTransport"],
            "schema_bound_final_json_v1",
        )
        self.assertEqual(
            contract["sharedPolicy"]["localSnapshotReadPolicy"],
            "backend_validated_embedded_read_only",
        )
        news_row = next(
            item
            for item in contract["agents"]
            if item["agentId"] == "codex_mcp_operator"
        )
        prompt = self.bridge._render_ai_trade_council_prompt(
            news_row,
            "c" * 64,
            "ai-trade-council/snapshots/test.json",
            contract["outputSchema"],
        )
        self.assertIn("ฝัง Snapshot JSON", prompt)
        self.assertIn("ห้ามใช้ Shell/Terminal", prompt)
        self.assertIn("JSON object เพียงหนึ่งก้อน", prompt)
        self.assertNotIn("COUNCIL_VOTE_JSON:", prompt)
        self.assertNotIn("Get-Content", prompt)
        self.assertLessEqual(len(prompt), 8000)

    def test_finish_auto_mission_accepts_schema_bound_vote(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._configure_selected_mt4(root)
            snapshot_id = "d" * 64
            mission_id = "mission-council-envelope-test"
            lease_id = "lease-council-envelope-test"
            valid_until = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
            context = {
                "kind": "ai_trade_council_vote",
                "snapshotId": snapshot_id,
                "agentId": "backtest_analyst",
                "roleId": "price_action",
                "readOnly": True,
                "referencePrice": 2400.0,
                "horizonBars": 1,
                "validUntilBarTime": valid_until,
            }
            mission = {
                "id": mission_id,
                "title": "ทดสอบผล Council จาก Runner",
                "detail": "วิเคราะห์ Snapshot แบบอ่านอย่างเดียว",
                "owner": "backtest_analyst",
                "toolId": "codex_cli_task",
                "targetId": self.bridge.AI_TRADE_COUNCIL_PROP_ID,
                "status": "running",
                "reportType": "ai_trade_council_report",
                "budget": {"outputLimitChars": 7000},
                "analysisContext": context,
                "execution": {"leaseId": lease_id, "workerId": "worker-test"},
                "reportIds": [],
            }
            self.bridge.save_missions([mission])
            raw_vote = {
                "snapshotId": snapshot_id,
                "agentId": "backtest_analyst",
                "roleId": "price_action",
                "decision": "HOLD",
                "confidence": 58,
                "horizonBars": 1,
                "validUntilBarTime": valid_until,
                "stopLossPrice": None,
                "takeProfitPrice": None,
                "indicatorValidation": None,
                "volatilityState": None,
                "eventRisk": None,
                "horizon": "แท่ง H4 ถัดไป",
                "observations": ["โครงสร้างราคายังไม่ยืนยันทิศทาง"],
                "invalidation": "เกิด breakout พร้อมแท่งปิดยืนยัน",
                "evidence": [
                    {
                        "label": "Snapshot H4",
                        "observedAt": "2026-07-29T00:00:00Z",
                        "sourceUrl": None,
                    }
                ],
                "warnings": [],
            }
            encoded = json.dumps(raw_vote, ensure_ascii=False, separators=(",", ":"))
            finished = self.bridge.finish_auto_mission(
                mission_id,
                lease_id,
                {"processStarted": True, "durationMs": 10},
                {
                    "ok": True,
                    "status": "completed",
                    "workStatus": "completed",
                    "finalMessage": encoded,
                    "findings": raw_vote["observations"],
                    "nextSteps": [],
                    "evidence": [],
                    "blockedCapability": "",
                    "processStarted": True,
                    "durationMs": 10,
                },
            )
            self.assertIsNotNone(finished)
            self.assertEqual(finished["status"], "completed")
            self.assertEqual(finished["phase"], "auto_guarded_completed")
            self.assertEqual(finished["councilVote"]["decision"], "HOLD")
            self.assertEqual(finished["workStatus"], "completed")

    def test_standalone_status_endpoint_reuses_canonical_prop_report(self) -> None:
        original_prop_report = self.bridge.prop_report
        expected = {
            "schemaVersion": "ai-trade-council-v2",
            "runtimeTruth": "backend_observed_only",
        }
        observed_prop_ids: list[str] = []
        try:
            self.bridge.prop_report = lambda prop_id: (
                observed_prop_ids.append(prop_id)
                or {"aiTradeCouncil": expected}
            )
            actual = self.bridge.ai_trade_council_status_read_model()
        finally:
            self.bridge.prop_report = original_prop_report

        self.assertIs(actual, expected)
        self.assertEqual(
            observed_prop_ids,
            [self.bridge.AI_TRADE_COUNCIL_PROP_ID],
        )
        source = BRIDGE_PATH.read_text(encoding="utf-8")
        self.assertIn(
            '"aiTradeCouncil": ai_trade_council_status_read_model()',
            source,
        )

    def test_closed_bar_automation_baselines_then_queues_once_after_settle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id = self._configure_selected_mt4(root)
            snapshot_file = self.bridge._metatrader_snapshot_file(candidate_id)
            self.assertIsNotNone(snapshot_file)
            snapshot_file.parent.mkdir(parents=True)
            payload = snapshot_payload(candidate_id)
            snapshot_file.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )
            store = self.bridge._ai_trade_council_automation_default_store()
            store["config"]["enabled"] = True
            self.bridge._save_ai_trade_council_automation_store(store)

            calls: list[dict] = []
            originals = {
                "load_operator_mode_record": self.bridge.load_operator_mode_record,
                "bridge_status": self.bridge.bridge_status,
                "_collaboration_quota_gate": self.bridge._collaboration_quota_gate,
                "run_ai_trade_council_analysis": self.bridge.run_ai_trade_council_analysis,
            }
            try:
                self.bridge.load_operator_mode_record = lambda: {"mode": "auto_guarded"}
                self.bridge.bridge_status = lambda: {
                    "codex": {"status": "ready_guarded"}
                }
                self.bridge._collaboration_quota_gate = (
                    lambda config, refresh: {
                        "allowed": True,
                        "reason": "ready",
                        "remainingPercent": 75,
                    }
                )

                def fake_council(
                    request,
                    *,
                    automation_context=None,
                    _snapshot_model=None,
                ):
                    calls.append({
                        "request": request,
                        "automation": automation_context,
                        "snapshotModel": _snapshot_model,
                    })
                    return {
                        "ok": True,
                        "kind": "ai_trade_council_queued",
                        "parent": {"id": "mission-auto-1"},
                    }

                self.bridge.run_ai_trade_council_analysis = fake_council

                baseline = self.bridge.ai_trade_council_automation_tick()
                self.assertEqual(
                    baseline["kind"],
                    "ai_trade_council_automation_baseline",
                )
                self.assertEqual(calls, [])

                payload["chart"]["bid"] = 2390.0
                snapshot_file.write_text(
                    json.dumps(payload, ensure_ascii=False),
                    encoding="utf-8",
                )
                same_bar = self.bridge.ai_trade_council_automation_tick()
                self.assertEqual(
                    same_bar["kind"],
                    "ai_trade_council_automation_idle",
                )
                self.assertEqual(calls, [])

                next_bar_time = payload["chart"]["bars"][-1]["time"] + 14400
                payload["chart"]["bars"].append({
                    "time": next_bar_time,
                    "open": 2400,
                    "high": 2405,
                    "low": 2398,
                    "close": 2403,
                    "volume": 1500,
                })
                snapshot_file.write_text(
                    json.dumps(payload, ensure_ascii=False),
                    encoding="utf-8",
                )
                detected = self.bridge.ai_trade_council_automation_tick()
                self.assertEqual(
                    detected["kind"],
                    "ai_trade_council_automation_settling",
                )
                self.assertEqual(calls, [])

                pending_store = self.bridge.load_ai_trade_council_automation_store()
                pending_store["state"]["pendingDetectedAt"] = (
                    self.bridge.datetime.now(self.bridge.timezone.utc)
                    - self.bridge.timedelta(seconds=20)
                ).isoformat()
                self.bridge._save_ai_trade_council_automation_store(pending_store)

                queued = self.bridge.ai_trade_council_automation_tick()
                self.assertEqual(queued["kind"], "ai_trade_council_queued")
                self.assertEqual(len(calls), 1)
                self.assertEqual(
                    calls[0]["automation"]["triggerMode"],
                    "last_closed_candle_time_change",
                )
                self.assertEqual(
                    calls[0]["automation"]["closedBarTime"],
                    next_bar_time,
                )
                self.assertIsInstance(calls[0]["snapshotModel"], dict)
                replay = self.bridge.ai_trade_council_automation_tick()
                self.assertEqual(
                    replay["kind"],
                    "ai_trade_council_automation_idle",
                )
                self.assertEqual(len(calls), 1)
            finally:
                for name, value in originals.items():
                    setattr(self.bridge, name, value)

            state = self.bridge.ai_trade_council_automation_read_model()["state"]
            self.assertEqual(state["lastObservedClosedBarTime"], next_bar_time)
            # Queueing is not completion. The analyzed cursor is advanced only
            # after the parent reaches a terminal state with durable children.
            self.assertIsNone(state["lastAnalyzedClosedBarTime"])
            self.assertEqual(state["dailyRunCount"], 1)
            self.assertEqual(state["lastMissionId"], "mission-auto-1")

    def test_closed_bar_automation_restart_and_unsupported_timeframe_do_not_catch_up(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id = self._configure_selected_mt4(root)
            snapshot_file = self.bridge._metatrader_snapshot_file(candidate_id)
            self.assertIsNotNone(snapshot_file)
            snapshot_file.parent.mkdir(parents=True)
            payload = snapshot_payload(candidate_id)
            payload["chart"]["timeframe"] = "M1"
            snapshot_file.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )
            store = self.bridge._ai_trade_council_automation_default_store()
            store["config"]["enabled"] = True
            self.bridge._save_ai_trade_council_automation_store(store)

            first = self.bridge.ai_trade_council_automation_tick()
            self.assertEqual(
                first["kind"],
                "ai_trade_council_automation_baseline",
            )
            unsupported = self.bridge.ai_trade_council_automation_tick()
            self.assertEqual(
                unsupported["kind"],
                "ai_trade_council_automation_unsupported_timeframe",
            )

            payload["chart"]["timeframe"] = "H4"
            snapshot_file.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )
            stream_change = self.bridge.ai_trade_council_automation_tick()
            self.assertEqual(
                stream_change["kind"],
                "ai_trade_council_automation_baseline",
            )
            payload["chart"]["bars"].append({
                "time": payload["chart"]["bars"][-1]["time"] + 14400,
                "open": 2400,
                "high": 2405,
                "low": 2398,
                "close": 2403,
                "volume": 1500,
            })
            snapshot_file.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )
            restart_store = self.bridge.load_ai_trade_council_automation_store()
            restart_store["state"]["startupId"] = "previous-process"
            self.bridge._save_ai_trade_council_automation_store(restart_store)
            restart = self.bridge.ai_trade_council_automation_tick()
            self.assertEqual(
                restart["kind"],
                "ai_trade_council_automation_baseline",
            )
            self.assertEqual(restart["reason"], "restart_baseline")
            state = self.bridge.load_ai_trade_council_automation_store()["state"]
            self.assertIsNone(state["pendingClosedBarTime"])

    def test_automation_config_allows_only_guard_fields(self) -> None:
        original_runtime = self.bridge.RUNTIME_DIR
        original_audit = self.bridge.AUDIT_PATH
        with tempfile.TemporaryDirectory() as directory:
            try:
                self.bridge.RUNTIME_DIR = Path(directory) / "runtime"
                self.bridge.AUDIT_PATH = self.bridge.RUNTIME_DIR / "bridge-audit.jsonl"
                invalid = self.bridge.set_ai_trade_council_automation({
                    "enabled": True,
                    "pollSeconds": 1,
                })
                self.assertEqual(
                    invalid["kind"],
                    "invalid_ai_trade_council_automation_request",
                )
                updated = self.bridge.set_ai_trade_council_automation({
                    "enabled": True,
                    "maxDailyRounds": 12,
                    "minRemainingPercent": 40,
                })
                config = updated["automation"]["config"]
                self.assertTrue(config["enabled"])
                self.assertEqual(config["maxDailyRounds"], 12)
                self.assertEqual(config["minRemainingPercent"], 40)
                self.assertEqual(config["pollSeconds"], 5)
                self.assertEqual(config["settleSeconds"], 10)
                self.assertEqual(
                    config["supportedTimeframes"],
                    ["M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"],
                )
                source = BRIDGE_PATH.read_text(encoding="utf-8")
                self.assertIn(
                    '"autoAnalysis": ai_trade_council_automation_read_model()',
                    source,
                )
            finally:
                self.bridge.RUNTIME_DIR = original_runtime
                self.bridge.AUDIT_PATH = original_audit

    def test_quality_gate_validates_mapping_and_shadow_only_fallback(self) -> None:
        payload = snapshot_payload("mtc-quality-test")
        bars = payload["chart"]["bars"]
        chart = {
            "available": True,
            **payload["chart"],
            "symbol": "XAUUSD.r",
            "technicalIndicators": self.bridge._technical_indicator_snapshot(bars),
        }
        policy = self.bridge.load_ai_trade_council_prompt_contract()["sharedPolicy"]["qualityGate"]
        gate = self.bridge._ai_trade_council_data_quality_gate(
            {"chartSnapshot": chart},
            policy,
        )
        self.assertTrue(gate["passed"])
        self.assertEqual(gate["canonicalInstrument"]["canonicalSymbol"], "XAUUSD")
        self.assertEqual(gate["higherTimeframeContext"]["requestedTimeframe"], "D1")
        self.assertEqual(gate["higherTimeframeContext"]["status"], "unavailable")
        self.assertTrue(gate["executionEligibility"]["shadow"])
        self.assertFalse(gate["executionEligibility"]["demo"])
        self.assertFalse(gate["executionEligibility"]["live"])
        market_ready = self.bridge._ai_trade_council_data_quality_gate(
            {
                "chartSnapshot": {
                    **chart,
                    "marketOpen": True,
                    "marketSession": "BROKER_FEED_ACTIVE",
                }
            },
            policy,
        )
        self.assertEqual(market_ready["marketState"]["status"], "available")
        self.assertEqual(
            market_ready["marketState"]["session"],
            "BROKER_FEED_ACTIVE",
        )
        self.assertTrue(market_ready["executionEligibility"]["demo"])
        self.assertTrue(market_ready["executionEligibility"]["live"])

        duplicate = [dict(item) for item in bars]
        duplicate[-1]["time"] = duplicate[-2]["time"]
        blocked = self.bridge._ai_trade_council_data_quality_gate(
            {
                "chartSnapshot": {
                    **chart,
                    "bars": duplicate,
                    "technicalIndicators": self.bridge._technical_indicator_snapshot(duplicate),
                }
            },
            policy,
        )
        self.assertFalse(blocked["passed"])
        self.assertIn("bar_times_not_strictly_ordered_unique", blocked["reasonCodes"])

    def test_vote_role_ownership_horizon_and_news_domains_are_enforced(self) -> None:
        snapshot_id = "e" * 64
        now = datetime.now(timezone.utc)
        observed_at = now.isoformat().replace("+00:00", "Z")
        valid_until = int((now + timedelta(hours=1)).timestamp())
        context = {
            "snapshotId": snapshot_id,
            "agentId": "codex_mcp_operator",
            "roleId": "news",
            "referencePrice": 2400.0,
            "horizonBars": 1,
            "validUntilBarTime": valid_until,
            "volatilityState": "NORMAL",
            "qualityPolicy": {
                "maximumNewsAgeSeconds": 86400,
                "maximumFutureEvidenceSkewSeconds": 300,
                "minimumDistinctNewsDomains": 2,
            },
        }
        vote = {
            "snapshotId": snapshot_id,
            "agentId": "codex_mcp_operator",
            "roleId": "news",
            "decision": "BUY",
            "confidence": 80,
            "horizonBars": 1,
            "validUntilBarTime": valid_until,
            "stopLossPrice": None,
            "takeProfitPrice": None,
            "indicatorValidation": None,
            "volatilityState": None,
            "eventRisk": "ALLOW",
            "horizon": "แท่งถัดไป",
            "observations": ["ข่าวสนับสนุนทิศทาง"],
            "invalidation": "ข่าวเปลี่ยน",
            "evidence": [
                {"label": "A", "observedAt": observed_at, "sourceUrl": "https://example.com/a"},
                {"label": "B", "observedAt": observed_at, "sourceUrl": "https://example.com/b"},
            ],
            "warnings": [],
        }
        self.assertIsNone(
            self.bridge.validate_ai_trade_council_vote(json.dumps(vote), context)
        )
        distinct = {
            **vote,
            "evidence": [
                vote["evidence"][0],
                {**vote["evidence"][1], "sourceUrl": "https://example.org/b"},
            ],
        }
        self.assertIsNotNone(
            self.bridge.validate_ai_trade_council_vote(json.dumps(distinct), context)
        )
        self.assertIsNone(
            self.bridge.validate_ai_trade_council_vote(
                json.dumps({**distinct, "horizonBars": 2}),
                context,
            )
        )
        self.assertIsNone(
            self.bridge.validate_ai_trade_council_vote(
                json.dumps({**distinct, "stopLossPrice": 2380.0}),
                context,
            )
        )

    def test_low_confidence_unanimous_vote_is_no_trade_and_not_dispatched(self) -> None:
        now = datetime.now(timezone.utc)
        snapshot_id = "f" * 64
        valid_until = int((now + timedelta(hours=1)).timestamp())
        parent = {
            "analysisContext": {
                "kind": "ai_trade_council_parent",
                "snapshotId": snapshot_id,
                "referencePrice": 2400.0,
                "horizonBars": 1,
                "validUntilBarTime": valid_until,
                "roundDeadlineAt": (now + timedelta(minutes=4)).isoformat(),
                "qualityGate": {
                    "passed": True,
                    "reasonCodes": [],
                    "confidenceFloorDefault": 70,
                    "confidenceFloorByRole": {
                        "technical": 70,
                        "price_action": 70,
                        "news": 70,
                    },
                    "minimumRewardRiskRatio": 1.0,
                    "technical": {"volatilityState": "NORMAL"},
                    "executionEligibility": {"shadow": True, "demo": False, "live": False},
                },
            }
        }
        children = []
        for agent_id, role_id in self.bridge.AI_TRADE_COUNCIL_AGENT_ROLES.items():
            children.append({
                "owner": agent_id,
                "councilVote": {
                    "snapshotId": snapshot_id,
                    "agentId": agent_id,
                    "roleId": role_id,
                    "decision": "BUY",
                    "confidence": 60,
                    "horizonBars": 1,
                    "validUntilBarTime": valid_until,
                    "stopLossPrice": 2380.0 if role_id == "price_action" else None,
                    "takeProfitPrice": 2420.0 if role_id == "price_action" else None,
                    "indicatorValidation": "PASS" if role_id == "technical" else None,
                    "volatilityState": "NORMAL" if role_id == "technical" else None,
                    "eventRisk": "ALLOW" if role_id == "news" else None,
                    "newsEvidence": (
                        {"fresh": True, "distinctDomains": 2, "requiredDistinctDomains": 2}
                        if role_id == "news"
                        else None
                    ),
                },
            })
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        self.assertTrue(consensus["ready"])
        self.assertTrue(consensus["unanimous"])
        self.assertEqual(consensus["decision"], "NO_TRADE")
        self.assertFalse(consensus["qualityGate"]["passed"])
        self.assertIn(
            "confidence_below_floor:technical",
            consensus["qualityGate"]["reasonCodes"],
        )
        original_gateway = self.bridge.mt4_trade_gateway_status_read_model
        try:
            self.bridge.mt4_trade_gateway_status_read_model = lambda: (_ for _ in ()).throw(
                AssertionError("gateway must not be queried")
            )
            result = self.bridge.dispatch_ai_trade_council_trade_plan(parent, consensus)
        finally:
            self.bridge.mt4_trade_gateway_status_read_model = original_gateway
        self.assertEqual(result["status"], "no_trade")
        self.assertEqual(result["reasonCode"], "decision_quality_gate_not_passed")

    def test_demo_and_live_fail_closed_when_market_state_is_unavailable(self) -> None:
        audit_directory = tempfile.TemporaryDirectory()
        self.addCleanup(audit_directory.cleanup)
        self.bridge.AUDIT_PATH = Path(audit_directory.name) / "bridge-audit.jsonl"
        now = datetime.now(timezone.utc)
        stream_key = "7" * 64
        parent = {
            "id": "mission-market-state-gate",
            "analysisContext": {
                "referencePrice": 100.0,
                "snapshotObservedAt": now.isoformat(),
                "roundDeadlineAt": (now + timedelta(minutes=4)).isoformat(),
                "closedBarIdentity": {
                    "candidateId": "mtc-market-state-test",
                    "streamKey": stream_key,
                    "symbol": "XAUUSD",
                    "timeframe": "M5",
                    "closedBarTime": int(now.timestamp()) - 300,
                },
            },
        }
        consensus = {
            "snapshotId": "6" * 64,
            "ready": True,
            "unanimous": True,
            "voteCount": 3,
            "validUntilBarTime": int((now + timedelta(minutes=5)).timestamp()),
            "qualityGate": {
                "passed": True,
                "executionEligibility": {
                    "shadow": True,
                    "demo": False,
                    "live": False,
                },
                "marketState": {
                    "status": "unavailable",
                    "marketOpen": None,
                },
            },
            "tradePlan": {
                "available": True,
                "direction": "BUY",
                "stopLossPrice": 95.0,
                "takeProfitPrice": 110.0,
            },
        }
        original_gateway = self.bridge.mt4_trade_gateway_status_read_model
        try:
            for mode in ("demo", "live"):
                with self.subTest(mode=mode):
                    self.bridge.mt4_trade_gateway_status_read_model = lambda mode=mode: {
                        "connected": True,
                        "selectedCandidateId": "mtc-market-state-test",
                        "symbol": "XAUUSD",
                        "timeframe": "M5",
                        "mode": mode,
                    }
                    result = self.bridge.dispatch_ai_trade_council_trade_plan(
                        parent,
                        consensus,
                    )
                    self.assertEqual(result["status"], "blocked")
                    self.assertEqual(
                        result["reasonCode"],
                        "market_state_unavailable_or_closed",
                    )
        finally:
            self.bridge.mt4_trade_gateway_status_read_model = original_gateway

    def test_outcome_evaluator_waits_for_closed_bars_then_records_1_3_5(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.bridge.RUNTIME_DIR = root / "runtime"
            self.bridge.MISSIONS_PATH = self.bridge.RUNTIME_DIR / "missions.json"
            self.bridge.AUDIT_PATH = self.bridge.RUNTIME_DIR / "bridge-audit.jsonl"
            self.bridge.RUNTIME_REPORTS_DIR = self.bridge.RUNTIME_DIR / "reports"
            candidate_id = "mtc-outcome-test"
            symbol = "XAUUSD"
            timeframe = "M5"
            stream_key = self.bridge.payload_digest(candidate_id, symbol, timeframe)
            decision_bar_time = 1000
            parent = {
                "id": "mission-outcome-test",
                "owner": "manager",
                "status": "completed",
                "analysisContext": {"referencePrice": 100.0},
                "reportIds": [],
                "councilDecision": {
                    "snapshotId": "a" * 64,
                    "decision": "BUY",
                    "tradePlan": {"stopLossPrice": 95.0, "takeProfitPrice": 110.0},
                    "decisionProvenance": {
                        "closedBarIdentity": {
                            "candidateId": candidate_id,
                            "streamKey": stream_key,
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "closedBarTime": decision_bar_time,
                        }
                    },
                    "outcomeTracking": {
                        "schemaVersion": "ai-trade-council-outcome-tracking-v1",
                        "status": "pending",
                        "evaluationBars": [1, 3, 5],
                        "evaluations": [],
                    },
                },
            }
            self.bridge.save_missions([parent])

            def snapshot(future_count: int) -> dict:
                bars = [{
                    "time": decision_bar_time,
                    "open": 100,
                    "high": 101,
                    "low": 99,
                    "close": 100,
                }]
                for index in range(1, future_count + 1):
                    bars.append({
                        "time": decision_bar_time + index * 300,
                        "open": 100 + index,
                        "high": 102 + index,
                        "low": 99 + index,
                        "close": 101 + index,
                    })
                return {
                    "selectedCandidateId": candidate_id,
                    "adapter": {"ready": True},
                    "chartSnapshot": {
                        "available": True,
                        "snapshotId": ("b" if future_count < 5 else "c") * 64,
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "bars": bars,
                    },
                }

            first = self.bridge.evaluate_ai_trade_council_outcomes(snapshot(2))
            self.assertEqual(first["updated"], 1)
            partial = self.bridge.find_mission(parent["id"])["councilDecision"]["outcomeTracking"]
            self.assertEqual(partial["status"], "pending")
            self.assertEqual(
                [item["barsAfterDecision"] for item in partial["evaluations"]],
                [1],
            )

            final = self.bridge.evaluate_ai_trade_council_outcomes(snapshot(5))
            self.assertEqual(final["updated"], 1)
            evaluated = self.bridge.find_mission(parent["id"])["councilDecision"]["outcomeTracking"]
            self.assertEqual(evaluated["status"], "evaluated")
            self.assertEqual(
                [item["barsAfterDecision"] for item in evaluated["evaluations"]],
                [1, 3, 5],
            )
            self.assertGreater(evaluated["evaluations"][-1]["mfePercent"], 0)

    def test_snapshot_poll_invokes_outcome_evaluator_even_when_auto_rounds_are_off(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.bridge.RUNTIME_DIR = Path(directory) / "runtime"
            self.bridge.AUDIT_PATH = self.bridge.RUNTIME_DIR / "bridge-audit.jsonl"
            calls = []
            original = self.bridge.evaluate_ai_trade_council_outcomes
            try:
                self.bridge.evaluate_ai_trade_council_outcomes = (
                    lambda snapshot_model=None: calls.append(snapshot_model) or {"updated": 0, "pending": 0}
                )
                result = self.bridge.ai_trade_council_automation_tick()
            finally:
                self.bridge.evaluate_ai_trade_council_outcomes = original
            self.assertEqual(result["kind"], "ai_trade_council_automation_disabled")
            self.assertEqual(calls, [None])

    def test_council_worker_pool_is_three_and_general_pool_stays_serial(self) -> None:
        acquired = [
            self.bridge.AI_TRADE_COUNCIL_RUN_SEMAPHORE.acquire(blocking=False)
            for _ in range(4)
        ]
        try:
            self.assertEqual(acquired, [True, True, True, False])
        finally:
            for success in acquired:
                if success:
                    self.bridge.AI_TRADE_COUNCIL_RUN_SEMAPHORE.release()
        self.assertTrue(self.bridge.REAL_RUN_SEMAPHORE.acquire(blocking=False))
        try:
            self.assertFalse(self.bridge.REAL_RUN_SEMAPHORE.acquire(blocking=False))
        finally:
            self.bridge.REAL_RUN_SEMAPHORE.release()
        source = BRIDGE_PATH.read_text(encoding="utf-8")
        self.assertIn("target=ai_trade_council_worker_loop", source)
        self.assertIn("for index in range(1, 4)", source)

    def test_order_history_joins_only_the_exact_mission_and_snapshot(self) -> None:
        snapshot_id = "a" * 64
        mission_id = "mission-order-history-001"
        council_decision_id = (
            f"council-{self.bridge.payload_digest(mission_id, snapshot_id)[:24]}"
        )
        order = {
            "commandId": "cmd-" + "1" * 24,
            "missionId": mission_id,
            "councilDecisionId": council_decision_id,
            "snapshotId": snapshot_id,
            "side": "BUY",
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "ticket": 983059471,
            "executionState": "OPEN",
            "provenByEa": True,
        }
        mission = {
            "id": mission_id,
            "title": "AI Council BUY XAUUSD M5",
            "councilDecision": {
                "ready": True,
                "snapshotId": snapshot_id,
                "selectedDirection": "BUY",
                "requiredVotes": 1,
                "voteCount": 3,
                "directionCounts": {
                    "BUY": 1,
                    "HOLD": 2,
                    "SELL": 0,
                    "NO_DATA": 0,
                },
                "votes": [
                    {
                        "agentId": "optimization_agent",
                        "roleId": "technical",
                        "decision": "HOLD",
                    },
                    {
                        "agentId": "backtest_analyst",
                        "roleId": "price_action",
                        "decision": "BUY",
                    },
                    {
                        "agentId": "codex_mcp_operator",
                        "roleId": "news",
                        "decision": "HOLD",
                    },
                ],
            },
        }

        model = self.bridge._ai_trade_order_history_read_model(
            {
                "available": True,
                "items": [order],
                "hasMore": False,
                "reasonCode": "ok",
            },
            [mission],
        )

        self.assertTrue(model["available"])
        self.assertEqual(model["summary"]["total"], 1)
        self.assertEqual(model["summary"]["verified"], 1)
        item = model["items"][0]
        self.assertTrue(item["verified"])
        self.assertTrue(item["councilProvenanceVerified"])
        self.assertEqual(item["councilDecisionId"], council_decision_id)
        self.assertEqual(item["requiredVotes"], 1)
        self.assertEqual(
            item["directionCounts"],
            {"BUY": 1, "HOLD": 2, "SELL": 0, "NO_DATA": 0},
        )
        self.assertEqual(item["directionalVoters"], ["Price Action Consultant"])
        self.assertEqual(item["voteSummaryTh"], "BUY 1 / HOLD 2 / SELL 0")
        self.assertIn("Price Action Consultant", item["reasonTh"])
        self.assertIn("BUY 1", item["reasonTh"])
        self.assertEqual(item["missionTitle"], mission["title"])

    def test_order_history_does_not_infer_votes_from_snapshot_mismatch(self) -> None:
        order_snapshot_id = "b" * 64
        mission_snapshot_id = "c" * 64
        mission_id = "mission-order-history-mismatch"
        council_decision_id = (
            f"council-{self.bridge.payload_digest(mission_id, order_snapshot_id)[:24]}"
        )
        order = {
            "commandId": "cmd-" + "2" * 24,
            "missionId": mission_id,
            "councilDecisionId": council_decision_id,
            "snapshotId": order_snapshot_id,
            "side": "SELL",
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "ticket": 983059472,
            "executionState": "OPEN",
            "provenByEa": True,
        }
        mission = {
            "id": mission_id,
            "title": "Mismatched council record",
            "councilDecision": {
                "ready": True,
                "snapshotId": mission_snapshot_id,
                "selectedDirection": "SELL",
                "requiredVotes": 1,
                "voteCount": 3,
                "directionCounts": {
                    "BUY": 0,
                    "HOLD": 2,
                    "SELL": 1,
                    "NO_DATA": 0,
                },
                "votes": [
                    {
                        "agentId": "optimization_agent",
                        "roleId": "technical",
                        "decision": "HOLD",
                    },
                    {
                        "agentId": "backtest_analyst",
                        "roleId": "price_action",
                        "decision": "SELL",
                    },
                    {
                        "agentId": "codex_mcp_operator",
                        "roleId": "news",
                        "decision": "HOLD",
                    },
                ],
            },
        }

        model = self.bridge._ai_trade_order_history_read_model(
            {"available": True, "items": [order]},
            [mission],
        )

        item = model["items"][0]
        self.assertFalse(item["councilProvenanceVerified"])
        self.assertFalse(item["verified"])
        self.assertIsNone(item["requiredVotes"])
        self.assertIsNone(item["directionCounts"])
        self.assertEqual(item["directionalVoters"], [])
        self.assertNotIn("Price Action Consultant", item["reasonTh"])
        self.assertEqual(
            item["voteSummaryTh"],
            "ไม่พบผลโหวตที่ยืนยันได้",
        )
        self.assertEqual(model["summary"]["verified"], 0)

    def test_order_history_rejects_non_deterministic_id_and_inconsistent_vote_evidence(self) -> None:
        snapshot_id = "d" * 64
        mission_id = "mission-order-history-integrity"
        council_decision_id = (
            f"council-{self.bridge.payload_digest(mission_id, snapshot_id)[:24]}"
        )
        order = {
            "commandId": "cmd-" + "3" * 24,
            "missionId": mission_id,
            "councilDecisionId": council_decision_id,
            "snapshotId": snapshot_id,
            "side": "BUY",
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "ticket": 983059473,
            "executionState": "OPEN",
            "provenByEa": True,
        }
        mission = {
            "id": mission_id,
            "title": "Integrity checked council record",
            "councilDecision": {
                "ready": True,
                "snapshotId": snapshot_id,
                "selectedDirection": "BUY",
                "requiredVotes": 1,
                "voteCount": 3,
                "directionCounts": {
                    "BUY": 1,
                    "HOLD": 2,
                    "SELL": 0,
                    "NO_DATA": 0,
                },
                "votes": [
                    {
                        "agentId": "optimization_agent",
                        "roleId": "technical",
                        "decision": "HOLD",
                    },
                    {
                        "agentId": "backtest_analyst",
                        "roleId": "price_action",
                        "decision": "BUY",
                    },
                    {
                        "agentId": "codex_mcp_operator",
                        "roleId": "news",
                        "decision": "HOLD",
                    },
                ],
            },
        }

        cases: list[tuple[str, dict, dict]] = []

        wrong_id_order = json.loads(json.dumps(order))
        wrong_id_order["councilDecisionId"] = "council-" + "f" * 24
        cases.append(("non_deterministic_council_id", wrong_id_order, mission))

        wrong_counts_mission = json.loads(json.dumps(mission))
        wrong_counts_mission["councilDecision"]["directionCounts"]["BUY"] = 2
        wrong_counts_mission["councilDecision"]["directionCounts"]["HOLD"] = 1
        cases.append(("counts_do_not_match_votes", order, wrong_counts_mission))

        wrong_vote_count_mission = json.loads(json.dumps(mission))
        wrong_vote_count_mission["councilDecision"]["voteCount"] = 2
        cases.append(("declared_vote_count_is_not_three", order, wrong_vote_count_mission))

        unmet_threshold_mission = json.loads(json.dumps(mission))
        unmet_threshold_mission["councilDecision"]["requiredVotes"] = 2
        cases.append(("threshold_exceeds_directional_votes", order, unmet_threshold_mission))

        duplicate_role_mission = json.loads(json.dumps(mission))
        duplicate_role_mission["councilDecision"]["votes"][2]["roleId"] = "technical"
        cases.append(("specialist_roles_are_not_exact", order, duplicate_role_mission))

        for case_name, case_order, case_mission in cases:
            with self.subTest(case=case_name):
                model = self.bridge._ai_trade_order_history_read_model(
                    {"available": True, "items": [case_order]},
                    [case_mission],
                )
                item = model["items"][0]
                self.assertFalse(item["councilProvenanceVerified"])
                self.assertFalse(item["verified"])
                self.assertIsNone(item["requiredVotes"])
                self.assertIsNone(item["directionCounts"])
                self.assertEqual(item["directionalVoters"], [])
                self.assertEqual(model["summary"]["verified"], 0)

    def test_gateway_order_history_filters_selected_channel_and_never_infers_lifecycle(self) -> None:
        now = int(datetime.now(timezone.utc).timestamp())
        selected_channel = "mtc-selected-history"

        def record(command_suffix: str, channel_id: str, ticket: int) -> dict:
            command_id = "cmd-" + command_suffix * 24
            return {
                "command": {
                    "commandId": command_id,
                    "channelId": channel_id,
                    "missionId": f"mission-{command_suffix}",
                    "snapshotId": command_suffix * 64,
                    "councilDecisionId": "council-" + command_suffix * 24,
                    "action": "BUY",
                    "symbol": "XAUUSD",
                    "timeframe": "M5",
                    "stopLoss": 4320.0,
                    "takeProfit": 4360.0,
                },
                "ack": {
                    "status": "EXECUTED",
                    "reasonCode": "ORDER_ACCEPTED",
                    "mode": "demo",
                    "observedAt": now,
                    "ticket": ticket,
                    "fixedLot": 0.01,
                    "filledPrice": 4340.0,
                    "filledSlippagePoints": 0,
                    "actualStopLoss": 4320.0,
                    "actualTakeProfit": 4360.0,
                    "actualMagicNumber": 4186001,
                    "actualComment": f"HQ:{command_id}",
                    "verificationStatus": "VERIFIED_OPEN",
                    "executionState": "OPEN",
                    "errorCode": 0,
                    "statePersisted": True,
                },
                "status": "ack_EXECUTED",
                "outstanding": False,
                "createdAt": "2026-08-11T11:06:18Z",
                "updatedAt": "2026-08-11T11:06:19Z",
            }

        missing = record("4", selected_channel, 1004)
        stale = record("5", selected_channel, 1005)
        mismatch = record("6", selected_channel, 1006)
        other_channel = record("7", "mtc-not-selected", 1007)
        outcomes = {
            stale["command"]["commandId"]: {
                "observedAt": now - 120,
                "ticket": 1005,
                "magicNumber": 4186001,
                "comment": stale["ack"]["actualComment"],
                "executionState": "OPEN",
                "lots": 0.01,
                "openPrice": 4340.0,
                "stopLoss": 4320.0,
                "takeProfit": 4360.0,
                "openedAt": now - 180,
            },
            mismatch["command"]["commandId"]: {
                "observedAt": now,
                "ticket": 9999,
                "magicNumber": 4186001,
                "comment": mismatch["ack"]["actualComment"],
                "executionState": "OPEN",
                "lots": 0.02,
                "openPrice": 4350.0,
                "stopLoss": 4330.0,
                "takeProfit": 4370.0,
                "openedAt": now - 60,
            },
            other_channel["command"]["commandId"]: {
                "observedAt": now,
                "ticket": 1007,
                "magicNumber": 4186001,
                "comment": other_channel["ack"]["actualComment"],
                "executionState": "OPEN",
                "lots": 0.01,
                "openPrice": 4340.0,
                "stopLoss": 4320.0,
                "takeProfit": 4360.0,
                "openedAt": now - 60,
            },
        }

        class FakeGateway:
            def __init__(self) -> None:
                self.requested_limits: list[int] = []

            def list_commands(self, limit: int) -> list[dict]:
                self.requested_limits.append(limit)
                return [missing, stale, mismatch, other_channel]

            def read_outcome(self, command_id: str) -> dict | None:
                return outcomes.get(command_id)

        gateway = FakeGateway()
        history = self.bridge._mt4_trade_gateway_order_history(
            gateway,
            selected_candidate_id=selected_channel,
            limit=10,
        )

        self.assertEqual(gateway.requested_limits, [500])
        self.assertTrue(history["available"])
        self.assertEqual(history["totalExecuted"], 3)
        self.assertEqual(len(history["items"]), 3)
        self.assertNotIn(
            other_channel["command"]["commandId"],
            {item["commandId"] for item in history["items"]},
        )

        by_command = {item["commandId"]: item for item in history["items"]}
        missing_item = by_command[missing["command"]["commandId"]]
        self.assertEqual(missing_item["executionState"], "CONFIRMED_UNKNOWN")
        self.assertFalse(missing_item["outcomeAvailable"])
        self.assertFalse(missing_item["outcomeIdentityVerified"])
        self.assertFalse(missing_item["outcomeFresh"])

        stale_item = by_command[stale["command"]["commandId"]]
        self.assertEqual(stale_item["executionState"], "CONFIRMED_UNKNOWN")
        self.assertTrue(stale_item["outcomeAvailable"])
        self.assertTrue(stale_item["outcomeIdentityVerified"])
        self.assertFalse(stale_item["outcomeFresh"])
        self.assertEqual(stale_item["outcomeObservedAtDomain"], "utc")
        self.assertEqual(stale_item["outcomeObservedAtSource"], "ea_now_utc")
        self.assertIsNone(stale_item["outcomeObservedAtBroker"])
        self.assertIsNotNone(stale_item["outcomeObservedAt"])
        self.assertIsNotNone(stale_item["outcomeAgeSeconds"])

        mismatch_item = by_command[mismatch["command"]["commandId"]]
        self.assertEqual(mismatch_item["executionState"], "CONFIRMED_UNKNOWN")
        self.assertTrue(mismatch_item["outcomeAvailable"])
        self.assertFalse(mismatch_item["outcomeIdentityVerified"])
        self.assertFalse(mismatch_item["outcomeFresh"])
        self.assertEqual(mismatch_item["lot"], 0.01)
        self.assertEqual(mismatch_item["openPrice"], 4340.0)

    def test_reconciled_order_history_does_not_use_late_outcome_time_as_open_time(self) -> None:
        channel_id = "mtc-selected"
        created_at = "2026-08-11T17:36:16.673Z"
        command_id = "cmd-" + "8" * 24
        record = {
            "command": {
                "commandId": command_id,
                "channelId": channel_id,
                "missionId": "mission-reconciled-time",
                "snapshotId": "8" * 64,
                "councilDecisionId": "council-" + "8" * 24,
                "action": "SELL",
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "stopLoss": 4384.0,
                "takeProfit": 4368.88,
            },
            "status": "ack_EXECUTED",
            "outstanding": False,
            "createdAt": created_at,
            "updatedAt": "2026-08-12T03:33:13.630Z",
            "ack": {
                "status": "EXECUTED",
                "reasonCode": "EXECUTION_RECONCILED_WITH_WARNING",
                "observedAt": 1786471199,
                "ticket": 983283721,
                "filledPrice": 4376.4,
                "actualStopLoss": 4384.0,
                "actualTakeProfit": 4368.88,
                "actualMagicNumber": 4186001,
                "actualComment": f"HQ:{command_id}",
                "verificationStatus": "VERIFIED_OPEN",
                "statePersisted": True,
                "mode": "demo",
            },
        }
        outcome = {
            "observedAt": 1786471199,
            "ticket": 983283721,
            "magicNumber": 4186001,
            "comment": f"HQ:{command_id}",
            "executionState": "OPEN",
            "lots": 0.01,
            "openPrice": 4376.4,
            "stopLoss": 4384.0,
            "takeProfit": 4368.88,
            "openedAt": 1786480577,
        }

        class FakeGateway:
            def list_commands(self, limit: int) -> list[dict]:
                return [record]

            def read_outcome(self, requested_command_id: str) -> dict:
                self_outer.assertEqual(requested_command_id, command_id)
                return outcome

        self_outer = self
        history = self.bridge._mt4_trade_gateway_order_history(
            FakeGateway(),
            selected_candidate_id=channel_id,
            limit=10,
        )
        self.assertEqual(history["items"][0]["openedAt"], created_at)
        self.assertEqual(
            history["items"][0]["openedAtSource"],
            "command_created_at_legacy_reconciliation_fallback",
        )

    def test_closed_outcome_upgrades_effective_verification_status(self) -> None:
        channel_id = "mtc-selected"
        command_id = "cmd-" + "c" * 24
        record = {
            "command": {
                "commandId": command_id,
                "channelId": channel_id,
                "missionId": "mission-closed-evidence",
                "snapshotId": "c" * 64,
                "councilDecisionId": "council-" + "c" * 24,
                "action": "BUY",
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "stopLoss": 4380.3,
                "takeProfit": 4420.45,
            },
            "status": "ack_EXECUTED",
            "outstanding": False,
            "createdAt": "2026-08-11T11:06:18Z",
            "updatedAt": "2026-08-11T15:34:29Z",
            "ack": {
                "status": "EXECUTED",
                "reasonCode": "ORDER_ACCEPTED",
                "observedAt": 1786471578,
                "ticket": 983059471,
                "fixedLot": 0.01,
                "filledPrice": 4391.41,
                "actualStopLoss": 4380.3,
                "actualTakeProfit": 4420.45,
                "actualMagicNumber": 4186001,
                "actualComment": f"HQ:cmd-{'c' * 16}[sl]",
                "verificationStatus": "VERIFIED_OPEN",
                "statePersisted": True,
                "mode": "demo",
            },
        }
        outcome = {
            "observedAt": 1786481669,
            "ticket": 983059471,
            "magicNumber": 4186001,
            "comment": f"HQ:{command_id}",
            "executionState": "CLOSED",
            "lots": 0.01,
            "openPrice": 4391.41,
            "stopLoss": 4380.3,
            "takeProfit": 4420.45,
            "openedAt": 1786471578,
            "closedAt": 1786481669,
            "closedPnl": -11.5,
        }

        class FakeGateway:
            def list_commands(self, limit: int) -> list[dict]:
                return [record]

            def read_outcome(self, requested_command_id: str) -> dict:
                self_outer.assertEqual(requested_command_id, command_id)
                return outcome

        self_outer = self
        history = self.bridge._mt4_trade_gateway_order_history(
            FakeGateway(),
            selected_candidate_id=channel_id,
            limit=10,
        )

        item = history["items"][0]
        self.assertEqual(item["executionState"], "CLOSED")
        self.assertEqual(item["verificationStatus"], "VERIFIED_CLOSED")
        self.assertEqual(item["closedPnl"], -11.5)
        self.assertTrue(item["provenByEa"])
        self.assertTrue(item["outcomeIdentityVerified"])
        self.assertIsNone(item["outcomeFresh"])
        self.assertIsNone(item["outcomeObservedAt"])
        self.assertEqual(item["outcomeObservedAtBroker"], 1786481669)
        self.assertEqual(item["outcomeObservedAtDomain"], "broker_server")
        self.assertEqual(
            item["outcomeObservedAtSource"],
            "ea_order_close_time_broker_clock",
        )
        self.assertIsNone(item["outcomeAgeSeconds"])

        record["ack"]["actualComment"] = f"HQ:cmd-{'d' * 16}[sl]"
        mismatched = self.bridge._mt4_trade_gateway_order_history(
            FakeGateway(),
            selected_candidate_id=channel_id,
            limit=10,
        )["items"][0]
        self.assertFalse(mismatched["outcomeIdentityVerified"])
        self.assertEqual(mismatched["executionState"], "CONFIRMED_UNKNOWN")
        self.assertIsNone(mismatched["closedPnl"])

    def test_runner_schema_binds_horizon_and_role_specific_ownership(self) -> None:
        snapshot_id = "9" * 64
        compact = {
            "policy": {
                "qualityGate": {
                    "horizonBars": 1,
                    "validUntilBarTime": 1900000000,
                    "technical": {"volatilityState": "NORMAL"},
                }
            }
        }
        technical = self.runner.build_ai_trade_council_output_schema(
            snapshot_id,
            "optimization_agent",
            "technical",
            compact,
        )
        self.assertEqual(technical["properties"]["horizonBars"]["enum"], [1])
        self.assertEqual(
            technical["properties"]["validUntilBarTime"]["enum"],
            [1900000000],
        )
        self.assertEqual(technical["properties"]["stopLossPrice"]["type"], "null")
        self.assertEqual(
            technical["properties"]["volatilityState"]["enum"],
            ["NORMAL"],
        )
        price_action = self.runner.build_ai_trade_council_output_schema(
            snapshot_id,
            "backtest_analyst",
            "price_action",
            compact,
        )
        self.assertEqual(
            price_action["properties"]["indicatorValidation"]["type"],
            "null",
        )
        self.assertEqual(
            price_action["properties"]["stopLossPrice"]["type"],
            ["number", "null"],
        )
        news = self.runner.build_ai_trade_council_output_schema(
            snapshot_id,
            "codex_mcp_operator",
            "news",
            compact,
        )
        self.assertEqual(news["properties"]["eventRisk"]["enum"], ["ALLOW", "HOLD", "VETO"])
        self.assertEqual(news["properties"]["takeProfitPrice"]["type"], "null")

    def test_mql4_asset_is_read_only_and_uses_common_file_snapshot(self) -> None:
        source = MQL4_PATH.read_text(encoding="utf-8")
        self.assertIn("metafx-hq-mt4-snapshot-v1", source)
        self.assertIn("FILE_COMMON", source)
        self.assertRegex(
            source,
            r"FileMove\(\s*temporary_name,\s*FILE_COMMON,\s*final_name,\s*FILE_COMMON\s*\|\s*FILE_REWRITE\s*\)",
        )
        self.assertIn("snapshot.json", source)
        self.assertIn("EventSetTimer", source)
        for forbidden_call in (
            "OrderSend",
            "OrderClose",
            "OrderModify",
            "OrderDelete",
            "WebRequest",
            "ShellExecute",
            "WinExec",
        ):
            self.assertIsNone(
                re.search(rf"\b{re.escape(forbidden_call)}\s*\(", source),
                forbidden_call,
            )
        self.assertNotIn("#import", source)


if __name__ == "__main__":
    unittest.main()
