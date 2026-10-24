"""Collector adapter provenance; no real terminal/process is accessed."""
import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import test_radar_batch_repair_lifecycle as lifecycle


class Fx28TrendClockBindingTests(unittest.TestCase):
    runtime = lifecycle.RadarBatchRepairLifecycleTests.runtime
    setUp = lifecycle.RadarBatchRepairLifecycleTests.setUp

    @classmethod
    def setUpClass(cls):
        cls.bridge = lifecycle.load_module("fx28_clock_bridge", lifecycle.BRIDGE_PATH)

    def context(self, folder):
        terminal = Path(folder) / "terminal"
        terminal.mkdir(exist_ok=True)
        (terminal / "terminal64.exe").write_bytes(b"fixture only; never executed")
        return {"record": {"candidateId": "mtc-fixture-a", "installPath": str(terminal), "dataPath": str(terminal)},
                "token": {"candidateId": "mtc-fixture-a", "selectionRevision": 3, "platform": "mt5"}}

    def test_clock_hint_is_exact_terminal_and_selection_bound(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            context = self.context(folder)
            raw = {"schemaVersion": "fx28-market-snapshot-v1", "source": {"terminalCandidateId": "mtc-fixture-a"}}
            for case in ("same", "missing", "other_candidate", "other_selection", "expired", "future"):
                with self.subTest(case=case):
                    previous = {"terminalToken": copy.deepcopy(context["token"]), "clock": {"offsetSeconds": 10800, "verifiedAt": datetime.now(timezone.utc).isoformat()}}
                    if case == "missing": previous.pop("terminalToken")
                    elif case == "other_candidate": previous["terminalToken"]["candidateId"] = "mtc-fixture-b"
                    elif case == "other_selection": previous["terminalToken"]["selectionRevision"] = 2
                    elif case == "expired": previous["clock"]["verifiedAt"] = (datetime.now(timezone.utc) - timedelta(days=9)).isoformat()
                    elif case == "future": previous["clock"]["verifiedAt"] = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
                    with mock.patch.object(self.bridge, "_global_metatrader_platform_context", return_value=context), \
                         mock.patch.object(self.bridge, "run_safe_command", return_value={"ok": True, "output": json.dumps(raw)}) as run:
                        self.assertEqual(self.bridge._fx_trend_collect(previous), raw)
                    command = run.call_args.args[0]
                    self.assertEqual("--clock-offset-seconds" in command, case == "same")
                    self.assertEqual("--clock-verified-at" in command, case == "same")
                    self.assertIn("--terminal-pid", command)
                    self.assertEqual(command[command.index("--terminal-pid") + 1], "0")

    def test_switch_during_collection_rejects_result(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            context = self.context(folder)
            changed = copy.deepcopy(context)
            changed["token"]["selectionRevision"] = 4
            raw = {"schemaVersion": "fx28-market-snapshot-v1", "source": {"terminalCandidateId": "mtc-fixture-a"}}
            with mock.patch.object(self.bridge, "_global_metatrader_platform_context", side_effect=[context, changed]), \
                 mock.patch.object(self.bridge, "run_safe_command", return_value={"ok": True, "output": json.dumps(raw)}):
                with self.assertRaisesRegex(ValueError, "selected_terminal_changed"):
                    self.bridge._fx_trend_collect({})

    def test_collector_failure_exposes_only_safe_error_code(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            context = self.context(folder)
            for code, expected in (("broker_clock_unverified", "broker_clock_unverified"),
                                   ("C:/private/user/secret", "fx28_collector_failed")):
                with self.subTest(code=code), mock.patch.object(self.bridge, "_global_metatrader_platform_context", return_value=context), \
                     mock.patch.object(self.bridge, "run_safe_command", return_value={"ok": False, "output": json.dumps({"errorCode": code})}):
                    with self.assertRaisesRegex(ValueError, expected):
                        self.bridge._fx_trend_collect({})

    def test_daily_explanation_budget_is_scoped_and_bounded(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            baseline = {"timeoutSeconds": 120, "outputLimitChars": 7000, "rateReservePercent": 20, "modelTier": "specialist_balanced"}
            with mock.patch.object(self.bridge, "_dashboard_agent_preferences_read_model", return_value=baseline):
                effective = self.bridge._dashboard_workflow_execution_preferences("analyze_fx28_trends")
                self.assertEqual(effective["timeoutSeconds"], 300)
                self.assertEqual(effective["outputLimitChars"], 20000)
                self.assertEqual(effective["rateReservePercent"], 20)
                self.assertEqual(self.bridge._dashboard_workflow_execution_preferences("unrelated_action"), baseline)
            with mock.patch.object(self.bridge, "_dashboard_agent_preferences_read_model", return_value={**baseline, "timeoutSeconds": 9999}):
                self.assertEqual(self.bridge._dashboard_workflow_execution_preferences("analyze_fx28_trends")["timeoutSeconds"], 600)


if __name__ == "__main__":
    unittest.main()
