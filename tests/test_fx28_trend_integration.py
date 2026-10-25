"""Compatibility projections retain FX28 history without running its pipeline.

The retired admission/Runner tests are replaced by archive integration tests.
Pure calculation and report validation remain in test_fx28_trend_engine and
test_fx28_trend_runner. Execute through work/run-hq-final-isolated.py.
"""
import copy
import tempfile
import unittest
from datetime import timedelta
from unittest import mock

import test_fx28_trend_runner as fixtures
import test_radar_batch_repair_lifecycle as lifecycle


class Fx28TrendIntegrationTests(unittest.TestCase):
    runtime = lifecycle.RadarBatchRepairLifecycleTests.runtime
    setUp = lifecycle.RadarBatchRepairLifecycleTests.setUp

    @classmethod
    def setUpClass(cls):
        cls.bridge = lifecycle.load_module("fx28_integration_bridge", lifecycle.BRIDGE_PATH)
        cls.engine = cls.bridge.fx_trend

    def archived_store(self):
        snapshot, now = fixtures.market_snapshot(self.engine)
        model = self.engine.build_read_model(snapshot, now=now)
        store = {"model": model, "ai": {"status": "completed", "summaryTh": "Archived daily explanation"},
                 "history": [{"snapshotId": "old", "marketDate": "2026-10-22"}],
                 "nextPriceAt": self.engine.iso(now + timedelta(minutes=15))}
        return store, now

    def test_archive_rows_and_explanation_remain_available_with_retired_status(self):
        store, now = self.archived_store()
        before = copy.deepcopy(store)
        with mock.patch.object(self.bridge, "_fx_trend_store", return_value=store):
            model = self.bridge._fx_trend_read_model(now=now)
        self.assertEqual(model["status"], "retired")
        self.assertTrue(model["archiveOnly"])
        self.assertEqual(model["ai"]["status"], "retired")
        self.assertEqual(model["archivedAi"]["summaryTh"], "Archived daily explanation")
        self.assertEqual(len(model["rows"]), 28)
        self.assertEqual(model["snapshotDigest"], before["model"]["snapshotDigest"])
        self.assertEqual(model["updatedAt"], before["model"]["updatedAt"])
        self.assertEqual(model["history"], before["history"])
        self.assertEqual(store, before)

    def test_archive_projection_has_no_future_price_or_ai_run(self):
        store, now = self.archived_store()
        with mock.patch.object(self.bridge, "_fx_trend_store", return_value=store):
            model = self.bridge._fx_trend_read_model(now=now)
        self.assertIsNone(model["schedule"]["priceNextRunAt"])
        self.assertIsNone(model["schedule"]["aiNextRunAt"])

    def test_missing_stale_and_future_archives_are_never_presented_as_current(self):
        store, now = self.archived_store()
        for offset in (-timedelta(hours=2), timedelta(hours=2)):
            archived = copy.deepcopy(store)
            archived["model"]["updatedAt"] = self.engine.iso(now + offset)
            with self.subTest(offset=offset), mock.patch.object(self.bridge, "_fx_trend_store", return_value=archived):
                model = self.bridge._fx_trend_read_model(now=now)
            self.assertEqual(model["status"], "retired")
            self.assertTrue(model["stale"])
            self.assertTrue(model["archiveOnly"])
        with mock.patch.object(self.bridge, "_fx_trend_store", return_value={}):
            model = self.bridge._fx_trend_read_model(now=now)
        self.assertEqual(model["status"], "retired")
        self.assertTrue(model["stale"])

    def test_read_then_tick_does_not_write_archive_or_create_work(self):
        store, now = self.archived_store()
        before = copy.deepcopy(store)
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder), \
             mock.patch.object(self.bridge, "_fx_trend_store", return_value=store), \
             mock.patch.object(self.bridge, "_fx_trend_save") as write, \
             mock.patch.object(self.bridge, "_fx_trend_collect") as collect, \
             mock.patch.object(self.bridge, "codex_rate_limits") as quota, \
             mock.patch.object(self.bridge, "run_safe_command") as runner, \
             mock.patch.object(self.bridge, "run_dashboard_workflow_action") as dispatch:
            for moment in (now, now + timedelta(minutes=15), now + timedelta(days=1)):
                self.bridge._fx_trend_read_model(now=moment)
                self.bridge.fx_trend_service_tick(now=moment)
            self.assertEqual(self.bridge.load_missions(), [])
        self.assertEqual(store, before)
        for operation in (write, collect, quota, runner, dispatch):
            operation.assert_not_called()

    def test_archived_completed_mission_cannot_trigger_daily_replay(self):
        store, now = self.archived_store()
        store["ai"]["missionId"] = "historic-completed"
        mission = {"id": "historic-completed", "status": "completed", "result": "Archived result"}
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder), \
             mock.patch.object(self.bridge, "_fx_trend_store", return_value=store), \
             mock.patch.object(self.bridge, "run_dashboard_workflow_action") as dispatch:
            self.bridge.save_missions([mission])
            before = copy.deepcopy(self.bridge.load_missions())
            self.assertEqual(self.bridge._fx_trend_read_model(now=now)["archivedAi"]["missionId"], mission["id"])
            self.bridge.fx_trend_service_tick(now=now + timedelta(days=1))
            self.assertEqual(self.bridge.load_missions(), before)
        dispatch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
