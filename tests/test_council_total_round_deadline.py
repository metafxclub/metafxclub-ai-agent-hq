"""One automatic deadline, tested only with temporary stores and inert fixtures."""
from __future__ import annotations

from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
import unittest
from unittest import mock

import test_ai_trade_council_failure_injection as creation_fixtures
import test_ai_trade_council_per_bar_automation as scheduler_fixtures
import test_ai_trade_council_gateway_e2e as mt4_fixtures
import test_mt5_council_gateway_e2e as mt5_fixtures


class CouncilTotalRoundDeadlineTests(unittest.TestCase):
    def setUp(self):
        self.fixture = creation_fixtures.AiTradeCouncilFailureInjectionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.bridge = self.fixture.bridge
        self.fixture._configure_selected_mt4()

    def admission(self, *, elapsed=0, seconds=300):
        admitted = datetime.now(timezone.utc) - timedelta(seconds=elapsed)
        return {
            "triggerPolicy": "new_closed_bar_only_no_backfill",
            "triggerStartupId": self.bridge.SERVER_STARTED_AT,
            "quotaAdmittedAt": admitted.isoformat(),
            "triggerExpiresAt": (admitted + timedelta(seconds=seconds)).isoformat(),
        }

    def test_deadline_reads_original_expiry_and_never_renews_legacy_admission(self):
        for seconds in (20, 60, 300):
            admission = self.admission(elapsed=10, seconds=seconds)
            self.assertEqual(
                self.bridge._ai_trade_council_automatic_deadline(admission),
                datetime.fromisoformat(admission["triggerExpiresAt"]),
            )
        for seconds in (0, -1, 301):
            self.assertIsNone(self.bridge._ai_trade_council_automatic_deadline(
                self.admission(seconds=seconds)))
        self.assertIsNone(self.bridge._ai_trade_council_automatic_deadline({}))

    def create_round(self, admission=None):
        b = self.bridge
        snapshot = b.metatrader_snapshot_read_model(b.AI_TRADE_COUNCIL_PROP_ID)
        identity, _ = b._ai_trade_council_closed_bar_identity(snapshot)
        context = None if admission is None else {
            "triggerMode": "last_closed_candle_time_change",
            "streamKey": identity["streamKey"], "symbol": identity["symbol"],
            "timeframe": identity["timeframe"], "closedBarTime": identity["lastClosedBarTime"],
            "analysisBarCount": b.AI_TRADE_COUNCIL_DEFAULT_ANALYSIS_BAR_COUNT,
            "dayKey": b._automation_day_key(), "executionPolicy": "current_exact_snapshot",
            "tradeCommandAllowed": True, **admission,
        }
        with ExitStack() as stack:
            for patch in self.fixture._analysis_patches():
                stack.enter_context(patch)
            result = b.run_ai_trade_council_analysis(
                {"snapshotId": identity["snapshotId"]},
                automation_context=context, _snapshot_model=snapshot,
            )
        parent_id = result["parent"]["id"]
        return [row for row in b.load_missions()
                if row["id"] == parent_id or row.get("parentMissionId") == parent_id]

    def test_preparation_time_is_inside_one_shared_300_second_budget(self):
        admission = self.admission(elapsed=80)
        missions = self.create_round(admission)
        self.assertEqual(len(missions), 4)
        for mission in missions:
            context = mission["analysisContext"]
            self.assertEqual(datetime.fromisoformat(context["roundStartedAt"].replace("Z", "+00:00")),
                             datetime.fromisoformat(admission["quotaAdmittedAt"]))
            self.assertEqual(datetime.fromisoformat(context["roundDeadlineAt"].replace("Z", "+00:00")),
                             datetime.fromisoformat(admission["triggerExpiresAt"]))
        timeouts = sorted(row["budget"]["timeoutSeconds"] for row in missions
                          if row.get("parentMissionId"))
        self.assertEqual(timeouts, [60, 60, 90])

    def test_old_60_second_admission_is_not_extended_during_creation(self):
        admission = self.admission(elapsed=10, seconds=60)
        missions = self.create_round(admission)
        for mission in missions:
            self.assertEqual(
                datetime.fromisoformat(mission["analysisContext"]["roundDeadlineAt"].replace("Z", "+00:00")),
                datetime.fromisoformat(admission["triggerExpiresAt"]),
            )

    def test_expired_future_and_overlong_admissions_create_no_round(self):
        for admission in (self.admission(elapsed=301), self.admission(elapsed=-10),
                          self.admission(seconds=301)):
            before = len(self.bridge.load_missions())
            with self.assertRaises(self.bridge.RequestError):
                self.create_round(admission)
            self.assertEqual(len(self.bridge.load_missions()), before)

    def test_manual_round_remains_start_relative_240_seconds(self):
        parent = next(row for row in self.create_round() if not row.get("parentMissionId"))
        context = parent["analysisContext"]
        started = self.bridge.parse_iso(context["roundStartedAt"])
        deadline = self.bridge.parse_iso(context["roundDeadlineAt"])
        self.assertEqual((deadline - started).total_seconds(), 240)
        self.assertFalse(context.get("automation"))

    def test_contract_separates_automatic_total_from_manual_policy(self):
        policy = self.bridge.load_ai_trade_council_prompt_contract()["sharedPolicy"]["qualityGate"]
        self.assertEqual(policy["automaticTotalBudgetSeconds"], 300)
        self.assertEqual(policy["roundDeadlineSeconds"], 240)


class CouncilSchedulerDeadlineTests(unittest.TestCase):
    def test_natural_bar_assigns_300_seconds_once_from_detection(self):
        fixture = scheduler_fixtures.AiTradeCouncilPerBarAutomationTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        fixture._save_observed_store()
        fixture._advance_bar()
        fixture.bridge.ai_trade_council_automation_tick()
        state = fixture.bridge.load_ai_trade_council_automation_store()["state"]
        pending = state["pendingQueue"][0]
        admitted = fixture.bridge.parse_iso(pending["quotaAdmittedAt"])
        expires = fixture.bridge.parse_iso(pending["triggerExpiresAt"])
        self.assertEqual(admitted, fixture.bridge.parse_iso(pending["detectedAt"]))
        self.assertEqual((expires - admitted).total_seconds(), 300)
        fixture.bridge.ai_trade_council_automation_tick()
        repeated = fixture.bridge.load_ai_trade_council_automation_store()["state"]["pendingQueue"][0]
        self.assertEqual(repeated["triggerExpiresAt"], pending["triggerExpiresAt"])


class CouncilPublicationDeadlineTests(unittest.TestCase):
    def test_deadline_crossed_during_final_preflight_cannot_publish_mt4_or_mt5(self):
        for platform, fixture_type in (
            ("mt4", mt4_fixtures.AiTradeCouncilGatewayE2ETests),
            ("mt5", mt5_fixtures.MT5CouncilGatewayE2ETests),
        ):
            for overrun in (0, 1):
                with self.subTest(platform=platform, overrun=overrun):
                    fixture_type.setUpClass()
                    fixture = fixture_type()
                    fixture.setUp()
                    try:
                        b = fixture.bridge
                        if platform == "mt5":
                            parent, consensus = fixture.round()
                        else:
                            parent, children = fixture.council_round()
                            b.mt4_trade_gateway_status_read_model = fixture.gateway_status
                            consensus = b.ai_trade_council_consensus(parent, children)
                        deadline = b.parse_iso(parent["analysisContext"]["roundDeadlineAt"])

                        class Clock(datetime):
                            current = datetime.now(timezone.utc)

                            @classmethod
                            def now(cls, tz=None):
                                return cls.current.astimezone(tz) if tz else cls.current.replace(tzinfo=None)

                        # Advance after the quote check and final account-binding
                        # reads, immediately before publication admission. No sleeps,
                        # real terminal, Codex process or broker call are involved.
                        checked = False
                        original_preflight = b._ai_trade_council_execution_quote_preflight
                        original_gateway = b._mt4_trade_gateway_instance

                        def preflight(**kwargs):
                            nonlocal checked
                            result = original_preflight(**kwargs)
                            checked = True
                            return result

                        def gateway(**kwargs):
                            result = original_gateway(**kwargs)
                            if checked:
                                Clock.current = deadline + timedelta(seconds=overrun)
                            return result

                        with mock.patch.object(b, "datetime", Clock), \
                             mock.patch.object(b, "_ai_trade_council_execution_quote_preflight", side_effect=preflight), \
                             mock.patch.object(b, "_mt4_trade_gateway_instance", side_effect=gateway):
                            result = b.dispatch_ai_trade_council_trade_plan(parent, consensus)
                        self.assertTrue(checked)
                        self.assertEqual(result["reasonCode"], "decision_dispatch_window_expired")
                        self.assertFalse(result["commandPublished"])
                        stored_gateway = fixture.gateway() if platform == "mt5" else original_gateway()
                        self.assertEqual(stored_gateway.list_commands(limit=10), [])
                    finally:
                        fixture.tearDown()


if __name__ == "__main__":
    unittest.main()
