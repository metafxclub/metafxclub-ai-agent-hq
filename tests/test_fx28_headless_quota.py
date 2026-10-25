"""Retired FX28 must not probe or consume quota, even without a browser."""
import copy
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

import test_radar_batch_repair_lifecycle as lifecycle
import test_radar_daily_batch_corrective_retry as daily


class Fx28HeadlessQuotaTests(unittest.TestCase):
    runtime = lifecycle.RadarBatchRepairLifecycleTests.runtime
    setUp = lifecycle.RadarBatchRepairLifecycleTests.setUp

    @classmethod
    def setUpClass(cls):
        cls.bridge = lifecycle.load_module("fx28_headless_bridge", lifecycle.BRIDGE_PATH)

    def assert_quota_remains_unused(self, payload):
        cache = {"payload": payload, "fetchedMonotonic": 0}
        before = copy.deepcopy(cache)
        now = datetime(2026, 10, 25, 1, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder), \
             mock.patch.dict(self.bridge.CODEX_RATE_LIMIT_CACHE, cache, clear=True), \
             mock.patch.object(self.bridge, "_fx_trend_collect") as collect, \
             mock.patch.object(self.bridge, "codex_rate_limits") as refresh, \
             mock.patch.object(self.bridge, "run_dashboard_workflow_action") as dispatch:
            for moment in (now, now + timedelta(seconds=30), now + timedelta(days=1)):
                self.assertEqual(self.bridge.fx_trend_service_tick(now=moment)["status"], "retired")
                self.assertEqual(self.bridge._fx_trend_read_model(now=moment)["status"], "retired")
            self.assertEqual(self.bridge.CODEX_RATE_LIMIT_CACHE, before)
            self.assertEqual(self.bridge.load_missions(), [])
        for operation in (collect, refresh, dispatch):
            operation.assert_not_called()

    def test_cold_cache_stays_cold_during_tick_and_read(self):
        self.assert_quota_remains_unused(None)

    def test_available_credit_or_unavailable_quota_cannot_reactivate_fx28(self):
        for payload in ({"ok": False, "status": "unavailable"}, daily.RadarDailyBatchCorrectiveRetryTests.quota()):
            with self.subTest(status=payload.get("status")):
                self.assert_quota_remains_unused(payload)


if __name__ == "__main__":
    unittest.main()
