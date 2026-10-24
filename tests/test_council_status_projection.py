"""Standalone polling avoids unrelated archives while preserving selection guards."""
import copy
import unittest
from contextlib import ExitStack
from unittest import mock

import test_council_request_snapshot_reuse as fixtures


class CouncilStatusProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.CouncilRequestSnapshotReuseTests.setUpClass()

    def setUp(self):
        self.f = fixtures.CouncilRequestSnapshotReuseTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.b = self.f.bridge

    def test_status_uses_only_council_sources_and_one_request_snapshot(self):
        council_id = self.b.AI_TRADE_COUNCIL_PROP_ID
        missions = [{"id": "one", "targetId": council_id}, {"id": "two", "linkedPropId": council_id},
                    {"id": "unrelated", "targetId": "other"}]
        reports = [{"id": "report-one", "linkedPropId": council_id}, {"id": "report-other", "linkedPropId": "other"}]
        with ExitStack() as stack:
            for name in ("prop_report", "load_agent_events", "load_meeting_records", "search_memory_items",
                         "load_memory_index", "capability_registry", "_auto_trading_status_read_model",
                         "create_mission", "dispatch_ai_trade_council_trade_plan", "run_safe_command"):
                stack.enter_context(mock.patch.object(self.b, name, side_effect=AssertionError("unrelated work: " + name)))
            loader = stack.enter_context(mock.patch.object(self.b, "load_missions", return_value=missions))
            stack.enter_context(mock.patch.object(self.b, "load_runtime_reports", return_value=reports))
            result = self.b.ai_trade_council_status_read_model()
        loader.assert_called_once_with(shared_snapshot=True)
        self.f.council.assert_called_once()
        self.assertEqual(self.f.council.call_args.args[:2], (missions[:2], reports[:1]))
        self.f.reader.assert_called_once_with(council_id)
        self.assertEqual(result["chartSnapshot"], self.f.snapshot["chartSnapshot"])
        self.assertFalse(result["tradeGateway"]["liveOrderExecutionAvailable"])

    def test_status_selection_race_is_bounded_and_fails_closed(self):
        original = copy.deepcopy(self.f.snapshot)
        self.f.checklist_revision = 3
        result = self.b.ai_trade_council_status_read_model()
        self.assertEqual(self.f.capture.call_count, 2)
        self.assertEqual(self.f.reader.call_count, 2)
        self.assertFalse(result["chartSnapshot"]["available"])
        self.assertFalse(result["tradeGateway"]["connected"])
        self.assertEqual(self.f.snapshot, original)

    def test_status_has_no_cross_request_cache_or_timestamp_refresh(self):
        first = copy.deepcopy(self.f.snapshot)
        second = copy.deepcopy(first)
        second["chartSnapshot"].update(snapshotId="b" * 64, observedAt="2026-10-21T07:11:00Z", ageSeconds=2)
        self.f.reader.side_effect = [first, second]
        a = self.b.ai_trade_council_status_read_model()
        b = self.b.ai_trade_council_status_read_model()
        self.assertEqual(a["chartSnapshot"]["snapshotId"], "a" * 64)
        self.assertEqual(b["chartSnapshot"]["snapshotId"], "b" * 64)
        self.assertEqual(b["chartSnapshot"]["observedAt"], second["chartSnapshot"]["observedAt"])
        self.assertEqual(b["chartSnapshot"]["ageSeconds"], 2)


if __name__ == "__main__":
    unittest.main()
