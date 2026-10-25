"""The retired collector adapter cannot read terminal selection or spawn work."""
import copy
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

import test_radar_batch_repair_lifecycle as lifecycle


class Fx28TrendClockBindingTests(unittest.TestCase):
    runtime = lifecycle.RadarBatchRepairLifecycleTests.runtime
    setUp = lifecycle.RadarBatchRepairLifecycleTests.setUp

    @classmethod
    def setUpClass(cls):
        cls.bridge = lifecycle.load_module("fx28_clock_bridge", lifecycle.BRIDGE_PATH)

    def test_retired_collector_never_uses_cached_terminal_clock_or_selection(self):
        now = datetime.now(timezone.utc)
        for clock in ({}, {"offsetSeconds": 10800, "verifiedAt": now.isoformat()},
                      {"offsetSeconds": 10800, "verifiedAt": (now - timedelta(days=9)).isoformat()}):
            with self.subTest(clock=clock), tempfile.TemporaryDirectory() as folder, self.runtime(folder):
                previous = {"terminalToken": {"candidateId": "mtc-fixture-a", "selectionRevision": 3},
                            "clock": clock}
                before = copy.deepcopy(previous)
                with mock.patch.object(self.bridge, "_global_metatrader_platform_context") as terminal, \
                     mock.patch.object(self.bridge, "run_safe_command") as runner:
                    with self.assertRaises(self.bridge.RequestError) as caught:
                        self.bridge._fx_trend_collect(previous)
                self.assertEqual(caught.exception.status, 410)
                self.assertEqual(str(caught.exception), "replaced_by_sentiment_universe")
                self.assertEqual(previous, before)
                terminal.assert_not_called()
                runner.assert_not_called()

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
