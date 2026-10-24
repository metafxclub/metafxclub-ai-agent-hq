import copy
import unittest
from contextlib import ExitStack
from unittest import mock

from test_bridge_read_stability import load_bridge


class CouncilRequestSnapshotReuseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = load_bridge()

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.candidate = {"candidateId": "mtc-" + "a" * 26, "platform": "mt5"}
        self.hub = {
            "status": "configured", "selectedPlatform": "mt5", "selectedCandidate": self.candidate,
            "platforms": {"mt5": {"targets": [{"propId": self.bridge.AI_TRADE_COUNCIL_PROP_ID,
                "status": "configured", "selectedCandidate": self.candidate, "selectionRevision": 2}]}},
        }
        self.gateway = {"connected": False, "status": "execution_guard_blocked",
                        "reasonCode": "live_commission_policy_unconfirmed", "liveOrderExecutionAvailable": False}
        self.snapshot = {
            "propId": self.bridge.AI_TRADE_COUNCIL_PROP_ID,
            "selectedCandidateId": self.candidate["candidateId"],
            "selectedPlatform": "mt5", "adapter": {"ready": True, "status": "ready"},
            "chartSnapshot": {"available": True, "snapshotId": "a" * 64,
                "symbol": "XAUUSD", "timeframe": "H1", "observedAt": "2026-10-21T07:10:00Z", "ageSeconds": 1},
            "dailySummary": {"available": True}, "analysisReadiness": {"available": True},
        }
        self.checklist_args = []
        self.checklist_revision = 2

        def checklist(prop_id, **kwargs):
            self.checklist_args.append(kwargs)
            return {"metatraderSelection": {"selectedCandidate": self.candidate,
                        "selectionRevision": self.checklist_revision},
                    "items": [{"id": "ai_trader_ensemble", "status": "ready"}]}

        values = {
            "load_missions": [], "load_agent_events": [], "load_runtime_reports": [],
            "load_meeting_records": [], "search_memory_items": [], "load_memory_index": {"items": []},
            "bridge_status": {}, "capability_registry": {"bridge": {}, "capabilities": []},
            "find_dashboard_connection_profile": {"connections": []}, "workflow_dashboard_read_model": {},
            "_ai_trade_order_history_read_model": {}, "_ai_trade_council_analysis_history_read_model": {},
            "_ai_trade_council_managed_order_limit_model": {},
            "_ai_trade_council_platform_connections_read_model": {"items": []},
            "ai_trade_council_automation_read_model": {}, "_configured_ai_trade_council_required_votes": 3,
            "_configured_ai_trade_council_analysis_bar_count": 120,
        }
        for name, value in values.items():
            self.stack.enter_context(mock.patch.object(self.bridge, name, return_value=value))
        self.capture = self.stack.enter_context(mock.patch.object(
            self.bridge, "_capture_ai_trade_runtime_snapshots", return_value=(self.gateway, self.hub)))
        self.reader = self.stack.enter_context(mock.patch.object(
            self.bridge, "metatrader_snapshot_read_model", return_value=self.snapshot))
        self.stack.enter_context(mock.patch.object(self.bridge, "dashboard_connection_checklist", side_effect=checklist))
        self.council = self.stack.enter_context(mock.patch.object(
            self.bridge, "_ai_trade_council_read_model", wraps=self.bridge._ai_trade_council_read_model))

    def test_one_authoritative_snapshot_and_one_council_projection_per_request(self):
        original = copy.deepcopy(self.snapshot)
        result = self.bridge.prop_report(self.bridge.AI_TRADE_COUNCIL_PROP_ID)
        self.reader.assert_called_once_with(self.bridge.AI_TRADE_COUNCIL_PROP_ID)
        self.council.assert_called_once()
        self.assertIs(self.checklist_args[0]["metatrader_snapshot"], self.snapshot)
        self.assertIs(self.checklist_args[0]["global_metatrader"], self.hub)
        self.assertIs(result["metatraderReadOnly"], self.snapshot)
        self.assertEqual(result["aiTradeCouncil"]["chartSnapshot"], original["chartSnapshot"])
        self.assertEqual(self.snapshot, original)
        # Reusing the read model must not move a Council decision into the monitor.
        self.assertIn("consensus", result["aiTradeCouncil"]["liveAnalysis"])
        self.assertNotIn("consensus", result["autoTradingStatus"]["status"])
        self.assertIn("ensemble", result["aiTradeCouncil"]["runtimeTruth"])
        self.assertNotIn("ensemble", result["autoTradingStatus"]["runtimeTruth"])
        self.assertFalse(result["aiTradeCouncil"]["tradeGateway"]["liveOrderExecutionAvailable"])

    def test_monitor_nested_projection_does_not_alias_council(self):
        result = self.bridge.prop_report(self.bridge.AI_TRADE_COUNCIL_PROP_ID)
        original_council = copy.deepcopy(result["aiTradeCouncil"])
        result["autoTradingStatus"]["runtimeTruth"]["tradeGateway"]["connected"] = True
        result["autoTradingStatus"]["status"]["market"]["symbol"] = "OTHER"
        result["autoTradingStatus"]["status"]["eaHealth"]["available"] = True
        self.assertEqual(result["aiTradeCouncil"], original_council)

    def test_selection_race_retries_then_discards_captured_ready_snapshot(self):
        self.checklist_revision = 3
        result = self.bridge.prop_report(self.bridge.AI_TRADE_COUNCIL_PROP_ID)
        self.assertEqual(self.capture.call_count, 2)
        self.assertEqual(self.reader.call_count, 2)
        self.assertFalse(result["metatraderReadOnly"]["adapter"]["ready"])
        self.assertEqual(result["metatraderReadOnly"]["adapter"]["reasonCode"], "terminal_selection_changed_during_status_read")
        self.assertFalse(result["aiTradeCouncil"]["chartSnapshot"]["available"])
        self.assertFalse(result["aiTradeCouncil"]["tradeGateway"]["connected"])
        self.assertTrue(self.snapshot["adapter"]["ready"], "request fail-closed projection must not mutate its input")

    def test_reuse_has_no_cross_request_cache_and_preserves_observation_time(self):
        first_snapshot = copy.deepcopy(self.snapshot)
        second_snapshot = copy.deepcopy(self.snapshot)
        second_snapshot["chartSnapshot"].update(snapshotId="b" * 64, observedAt="2026-10-21T07:11:00Z", ageSeconds=2)
        self.reader.side_effect = [first_snapshot, second_snapshot]
        first = self.bridge.prop_report(self.bridge.AI_TRADE_COUNCIL_PROP_ID)
        second = self.bridge.prop_report(self.bridge.AI_TRADE_COUNCIL_PROP_ID)
        self.assertEqual(self.reader.call_count, 2)
        self.assertEqual(first["aiTradeCouncil"]["chartSnapshot"]["snapshotId"], "a" * 64)
        self.assertEqual(second["aiTradeCouncil"]["chartSnapshot"]["snapshotId"], "b" * 64)
        self.assertEqual(second["aiTradeCouncil"]["chartSnapshot"]["observedAt"], "2026-10-21T07:11:00Z")
        self.assertEqual(second["aiTradeCouncil"]["chartSnapshot"]["ageSeconds"], 2)

    def test_other_equipment_does_not_receive_the_council_snapshot(self):
        self.bridge.prop_report("terminal_workstation")
        self.capture.assert_not_called()
        self.council.assert_not_called()
        self.reader.assert_called_once_with("terminal_workstation")
        self.assertNotIn("metatrader_snapshot", self.checklist_args[0])


if __name__ == "__main__":
    unittest.main()
