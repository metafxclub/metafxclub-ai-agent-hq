"""A due FX job must refresh quota without a browser or another Mission."""
import tempfile
import unittest
from datetime import timedelta
from unittest import mock

import test_fx28_trend_runner as fixtures
import test_radar_batch_repair_lifecycle as lifecycle
import test_radar_daily_batch_corrective_retry as daily


class Fx28HeadlessQuotaTests(unittest.TestCase):
    runtime = lifecycle.RadarBatchRepairLifecycleTests.runtime
    setUp = lifecycle.RadarBatchRepairLifecycleTests.setUp

    @classmethod
    def setUpClass(cls):
        cls.bridge = lifecycle.load_module("fx28_headless_bridge", lifecycle.BRIDGE_PATH)

    def test_cold_cache_real_admission_gate_refreshes_and_get_stays_passive(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            snapshot, now = fixtures.market_snapshot(self.bridge.fx_trend)
            with mock.patch.dict(self.bridge.CODEX_RATE_LIMIT_CACHE, {"payload": None, "fetchedMonotonic": 0}, clear=True), \
                 mock.patch.object(self.bridge, "_fx_trend_collect", return_value=snapshot), \
                 mock.patch.object(self.bridge, "_fx_trend_news_sources", return_value=[]), \
                 mock.patch.object(self.bridge, "mission_worker_read_model", return_value={"operational": True}), \
                 mock.patch.object(self.bridge, "codex_rate_limits", return_value=daily.RadarDailyBatchCorrectiveRetryTests.quota()) as refresh:
                self.assertEqual(self.bridge.peek_codex_rate_limits()["status"], "not_checked")
                # Use the actual admission and quota gates; no browser, queued
                # work, Council run or GET populates the cold cache for us.
                result = self.bridge.fx_trend_service_tick(now=now)
                self.assertEqual(result["ai"]["status"], "queued", result)
                refresh.assert_called_once_with(force=True)
                mission_id = result["ai"]["missionId"]
                self.assertEqual(len(self.bridge.load_missions()), 1)
                self.assertEqual(self.bridge._fx_trend_read_model(now=now)["ai"]["missionId"], mission_id)
                replay = self.bridge.fx_trend_service_tick(now=now + timedelta(seconds=30))
                self.assertEqual(replay["ai"]["missionId"], mission_id)
                self.assertEqual(len(self.bridge.load_missions()), 1)
                refresh.assert_called_once_with(force=True)

    def test_unavailable_quota_remains_deferred_then_recovers_on_background_tick(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            snapshot, now = fixtures.market_snapshot(self.bridge.fx_trend)
            with mock.patch.dict(self.bridge.CODEX_RATE_LIMIT_CACHE, {"payload": None, "fetchedMonotonic": 0}, clear=True), \
                 mock.patch.object(self.bridge, "_fx_trend_collect", return_value=snapshot), \
                 mock.patch.object(self.bridge, "_fx_trend_news_sources", return_value=[]), \
                 mock.patch.object(self.bridge, "mission_worker_read_model", return_value={"operational": True}), \
                 mock.patch.object(self.bridge, "codex_rate_limits", side_effect=[{"ok": False, "status": "unavailable"}, daily.RadarDailyBatchCorrectiveRetryTests.quota()]) as refresh:
                blocked = self.bridge.fx_trend_service_tick(now=now)
                self.assertEqual(blocked["ai"]["status"], "deferred")
                self.assertEqual(blocked["ai"]["quota"]["status"], "quota_unavailable")
                self.assertEqual(self.bridge.load_missions(), [])
                admitted = self.bridge.fx_trend_service_tick(now=now + timedelta(seconds=30))
                self.assertEqual(admitted["ai"]["status"], "queued", admitted)
                self.assertEqual(len(self.bridge.load_missions()), 1)
                self.assertEqual(refresh.call_args_list, [mock.call(force=True), mock.call(force=True)])


if __name__ == "__main__":
    unittest.main()
