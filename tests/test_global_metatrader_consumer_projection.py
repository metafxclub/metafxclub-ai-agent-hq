from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
MAIN_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "main.js"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "global_metatrader_consumer_projection_bridge",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def function_source(source: str, name: str) -> str:
    match = re.search(rf"(?:async\s+)?function\s+{re.escape(name)}\s*\(", source)
    if not match:
        raise AssertionError(f"missing frontend function {name}")
    remainder = source[match.start() + 1 :]
    next_match = re.search(
        r"\n(?:async\s+)?function\s+[A-Za-z0-9_$]+\s*\(",
        remainder,
    )
    if not next_match:
        return source[match.start() :]
    return source[match.start() : match.start() + 1 + next_match.start()]


class GlobalMetatraderConsumerProjectionTests(unittest.TestCase):
    """Exercise the durable selection through each production consumer shape."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()
        cls.main_source = MAIN_PATH.read_text(encoding="utf-8")

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir(parents=True)
        self.mt4_path = self.root / "terminal-mt4"
        self.mt5_path = self.root / "terminal-mt5"
        (self.mt4_path / "MQL4").mkdir(parents=True)
        (self.mt5_path / "MQL5").mkdir(parents=True)
        self.mt4_id = "mtc-" + ("4" * 28)
        self.mt5_id = "mtc-" + ("5" * 28)

        self.original_runtime_dir = self.bridge.RUNTIME_DIR
        self.original_cache = dict(self.bridge.METATRADER_CACHE)
        self.bridge.RUNTIME_DIR = self.runtime
        self._write_target_store()
        self.terminal_model = self.bridge.metatrader_status_read_model(
            {"mt4": 1, "mt5": 1},
            {"supported": True, "mt4": 0, "mt5": 0},
            [
                self.bridge._public_metatrader_candidate(
                    self._candidate_record("mt4", self.mt4_id, self.mt4_path, 1)
                ),
                self.bridge._public_metatrader_candidate(
                    self._candidate_record("mt5", self.mt5_id, self.mt5_path, 1)
                ),
            ],
        )
        self.bridge.METATRADER_CACHE.clear()
        self.bridge.METATRADER_CACHE.update(
            {"payload": self.terminal_model, "fetchedMonotonic": 0.0}
        )

    def tearDown(self) -> None:
        self.bridge.RUNTIME_DIR = self.original_runtime_dir
        self.bridge.METATRADER_CACHE.clear()
        self.bridge.METATRADER_CACHE.update(self.original_cache)
        self.temp.cleanup()

    def _candidate_record(
        self,
        platform: str,
        candidate_id: str,
        path: Path,
        ordinal: int,
    ) -> dict:
        local_path = self.bridge._canonical_metatrader_location(path)
        return {
            "candidateId": candidate_id,
            "identityKey": self.bridge._metatrader_identity_key(platform, local_path),
            "platform": platform,
            "ordinal": ordinal,
            "localPath": local_path,
            "installPath": None,
            "dataPath": local_path,
            "firstSeenAt": "2026-09-07T00:00:00Z",
            "lastSeenAt": "2026-09-07T00:00:00Z",
            "available": True,
            "runningState": "not_running_detected",
        }

    def _write_target_store(self) -> None:
        self.bridge.write_json(
            self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME,
            {
                "schemaVersion": self.bridge.METATRADER_TARGET_STORE_SCHEMA_VERSION,
                "candidates": {
                    self.mt4_id: self._candidate_record(
                        "mt4", self.mt4_id, self.mt4_path, 1
                    ),
                    self.mt5_id: self._candidate_record(
                        "mt5", self.mt5_id, self.mt5_path, 1
                    ),
                },
                "selections": {},
                "updatedAt": "2026-09-07T00:00:00Z",
            },
        )

    def _selection_action_patches(self) -> ExitStack:
        stack = ExitStack()
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "check_rate_limit",
                return_value=(True, 0),
            )
        )
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "create_mission",
                return_value={
                    "id": "mission-consumer-projection",
                    "owner": "manager",
                    "targetId": self.bridge.GLOBAL_METATRADER_DISCOVERY_PROP_ID,
                },
            )
        )
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "create_report",
                side_effect=lambda payload: {
                    "id": "report-consumer-projection",
                    **payload,
                },
            )
        )
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "report_read_model_item",
                side_effect=lambda report: report,
            )
        )
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "_complete_diagnostic_mission",
                side_effect=lambda mission, report, result: mission,
            )
        )
        stack.enter_context(mock.patch.object(self.bridge, "append_audit"))
        return stack

    def _dashboard_checklist(self, prop_id: str) -> dict:
        bridge_status = {
            "mode": "Codex Runner Ready",
            "status": "guarded",
            "codex": {"status": "ready"},
            "mcp": {"status": "config_present", "configPresent": True},
            "time": "2026-09-07T00:00:00Z",
        }
        quota = {
            "ok": True,
            "status": "ready",
            "stale": False,
            "limitReached": False,
            "checkedAt": "2026-09-07T00:00:00Z",
            "primary": {"usedPercent": 10, "remainingPercent": 90},
        }
        snapshot = {
            "adapter": {"ready": False, "status": "awaiting_snapshot"},
            "chartSnapshot": {"available": False},
        }
        automation = {
            "config": {"enabled": False},
            "state": {"status": "disabled", "reason": "automation_disabled"},
        }
        with (
            mock.patch.object(
                self.bridge,
                "metatrader_snapshot_read_model",
                return_value=snapshot,
            ),
            mock.patch.object(
                self.bridge,
                "load_operator_mode_record",
                return_value={"mode": "manual_guarded"},
            ),
            mock.patch.object(
                self.bridge,
                "ai_trade_council_automation_read_model",
                return_value=automation,
            ),
        ):
            return self.bridge.dashboard_connection_checklist(
                prop_id,
                bridge=bridge_status,
                quota=quota,
                terminals=self.terminal_model,
                missions=[],
                gateway_snapshot={
                    "status": "awaiting_ea",
                    "connected": False,
                    "initStatus": {},
                },
                research_sheet={
                    "configured": False,
                    "adapterStatus": "not_configured",
                    "consumers": [],
                },
            )

    def _ea_factory_read_model(self) -> dict:
        sheet_model = {
            "configured": False,
            "adapterStatus": "not_configured",
            "consumers": [],
        }
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=self.bridge._empty_ea_factory_state(),
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
            mock.patch.object(
                self.bridge,
                "research_sheet_hub_read_model",
                return_value=sheet_model,
            ),
            mock.patch.object(
                self.bridge,
                "peek_metatrader_status",
                return_value=self.terminal_model,
            ),
        ):
            return self.bridge.ea_factory_read_model()

    def _node_binary(self) -> str:
        candidates = [
            shutil.which("node"),
            str(
                Path.home()
                / ".cache"
                / "codex-runtimes"
                / "codex-primary-runtime"
                / "dependencies"
                / "node"
                / "bin"
                / "node.exe"
            ),
        ]
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                return candidate
        self.skipTest("Node.js is required for the EA Optimization consumer test")

    def _ea_optimization_projection(self, checklist: dict, platform: str) -> dict:
        helpers = [
            "safeDashboardDisplayText",
            "normalizeConnectionStatus",
            "normalizeMetatraderCandidate",
            "getMetatraderSelectionModel",
            "workflowDomainObject",
            "normalizeEaOptimizationLabDomain",
            "getEaOptimizationLabTerminalGate",
        ]
        script = "\n".join(
            [
                "const state = {modal:{eaOptimizationLab:{platform:''}}};",
                "function normalizeEaOptimizationReport(value) { return value; }",
                *(function_source(self.main_source, name) for name in helpers),
                f"const checklist = {json.dumps(checklist, ensure_ascii=False)};",
                f"const session = {{platform:{json.dumps(platform)}}};",
                "const domain = normalizeEaOptimizationLabDomain({mode:'plan_only'}, {connectionChecklist:checklist,reports:[]});",
                "const gate = getEaOptimizationLabTerminalGate(domain, session);",
                "process.stdout.write(JSON.stringify({domain,gate}));",
            ]
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "global-mt-consumer-projection.js"
            path.write_text(script, encoding="utf-8")
            result = subprocess.run(
                [self._node_binary(), str(path)],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        return json.loads(result.stdout)

    def test_one_mt4_selection_reaches_all_three_consumers(self) -> None:
        with self._selection_action_patches():
            applied = self.bridge.select_global_metatrader_target(
                "mt4",
                self.mt4_id,
            )

        self.assertEqual(
            set(applied["targetPropIds"]),
            {
                "left_analytics_console",
                "right_server_racks",
                "right_tool_console",
            },
        )

        council = self._dashboard_checklist("left_analytics_console")
        council_selection = council["metatraderSelection"]
        self.assertEqual(council_selection["configurationStatus"], "configured")
        self.assertEqual(
            council_selection["selectedCandidate"]["candidateId"],
            self.mt4_id,
        )
        self.assertEqual(council_selection["selectedCandidate"]["platform"], "mt4")

        factory = self._ea_factory_read_model()
        self.assertEqual(factory["terminalSelection"]["selectedTerminalId"], self.mt4_id)
        self.assertIn(
            self.mt4_id,
            {
                candidate["candidateId"]
                for candidate in factory["terminalSelection"]["candidates"]
            },
        )
        self.assertEqual(factory["terminalGate"]["mt4"]["candidateId"], self.mt4_id)
        self.assertEqual(factory["terminalGate"]["mt4"]["platform"], "mt4")

        lab_checklist = self._dashboard_checklist("right_tool_console")
        lab = self._ea_optimization_projection(lab_checklist, "MT4")
        self.assertEqual(lab["domain"]["selectedTerminal"]["candidateId"], self.mt4_id)
        self.assertEqual(lab["gate"]["effectiveTerminalId"], self.mt4_id)
        self.assertTrue(lab["gate"]["backendBound"])
        self.assertFalse(lab["gate"]["ready"])

    def test_mt5_reaches_only_factory_and_lab_without_false_council_binding(self) -> None:
        with self._selection_action_patches():
            applied = self.bridge.select_global_metatrader_target(
                "mt5",
                self.mt5_id,
            )

        self.assertEqual(
            set(applied["targetPropIds"]),
            {"right_server_racks", "right_tool_console"},
        )
        stored = self.bridge.read_json(
            self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME,
            {},
        )
        self.assertNotIn("left_analytics_console", stored["selections"])

        council = self._dashboard_checklist("left_analytics_console")
        council_selection = council["metatraderSelection"]
        self.assertEqual(council_selection["configurationStatus"], "not_configured")
        self.assertIsNone(council_selection["selectedCandidate"])
        self.assertTrue(
            all(
                candidate["platform"] == "mt4"
                for candidate in council_selection["candidates"]
            )
        )

        factory = self._ea_factory_read_model()
        self.assertEqual(factory["terminalSelection"]["selectedTerminalId"], self.mt5_id)
        self.assertEqual(factory["terminalGate"]["mt5"]["candidateId"], self.mt5_id)
        self.assertEqual(factory["terminalGate"]["mt5"]["platform"], "mt5")

        lab_checklist = self._dashboard_checklist("right_tool_console")
        lab = self._ea_optimization_projection(lab_checklist, "MT5")
        self.assertEqual(lab["domain"]["selectedTerminal"]["candidateId"], self.mt5_id)
        self.assertEqual(lab["domain"]["selectedTerminal"]["platform"], "MT5")
        self.assertEqual(lab["gate"]["effectiveTerminalId"], self.mt5_id)
        self.assertTrue(lab["gate"]["backendBound"])
        self.assertFalse(lab["gate"]["ready"])


if __name__ == "__main__":
    unittest.main()
