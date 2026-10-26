"""An admitted current bar keeps its original budget after slow local capture."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest
from unittest import mock

import test_ai_trade_council_per_bar_automation as fixtures


class CouncilAdmittedSchedulerGapTests(unittest.TestCase):
    def fixture(self):
        fixture = fixtures.AiTradeCouncilPerBarAutomationTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        b = fixture.bridge
        b.MISSIONS_PATH = b.RUNTIME_DIR / "missions.json"
        start = datetime.now(timezone.utc)

        class Clock(datetime):
            instant = start

            @classmethod
            def now(cls, tz=None):
                return cls.instant.astimezone(tz) if tz else cls.instant.replace(tzinfo=None)

        self.enterContext(mock.patch.object(b, "datetime", Clock))
        self.enterContext(mock.patch.object(fixtures, "datetime", Clock))
        return fixture, b, Clock, start

    def pending(self, fixture, b):
        fixture._save_observed_store()
        fixture._advance_bar()
        first = b.ai_trade_council_automation_tick()
        self.assertEqual(first["kind"], "ai_trade_council_automation_settling")
        return b.load_ai_trade_council_automation_store()["state"]["pendingQueue"][0]

    def change_pending(self, b, **changes):
        store = b.load_ai_trade_council_automation_store()
        for key in ("coverageRecords", "pendingQueue"):
            for record in store["state"][key]:
                if record["status"] == "pending":
                    record.update(changes)
        b._save_ai_trade_council_automation_store(store)

    def assert_baselined_without_work(self, fixture, b):
        result = b.ai_trade_council_automation_tick()
        self.assertEqual(result["kind"], "ai_trade_council_automation_baseline")
        self.assertEqual(fixture.calls, [])
        self.assertEqual(b.load_ai_trade_council_automation_store()["state"]["pendingQueue"], [])
        b.ai_trade_council_automation_tick()
        self.assertEqual(fixture.calls, [])

    def test_slow_trigger_preparation_does_not_discard_already_admitted_current_bar(self):
        fixture, b, Clock, start = self.fixture()

        def slow_quota(_config, refresh):
            Clock.instant = start + timedelta(seconds=65)
            return {"allowed": True, "reason": "ready", "remainingPercent": 80}

        with mock.patch.object(b, "_collaboration_quota_gate", side_effect=slow_quota):
            pending = self.pending(fixture, b)
        self.assertEqual(b.parse_iso(pending["triggerExpiresAt"]), start + timedelta(seconds=300))
        # Same startup, stream and bar; the quota was admitted during the
        # observed new-bar event. The 65s were spent inside that tick, not
        # in an unobserved outage or a quota wait/backfill queue.
        second = b.ai_trade_council_automation_tick()
        self.assertEqual(second["kind"], "ai_trade_council_queued", second.get("reason"))
        self.assertEqual(len(fixture.calls), 1)
        self.assertEqual(fixture.calls[0]["automationContext"]["triggerExpiresAt"],
                         pending["triggerExpiresAt"])
        b.ai_trade_council_automation_tick()
        self.assertEqual(len(fixture.calls), 1)

    def test_exact_expiry_does_not_gain_scheduler_gap_grace(self):
        fixture, b, Clock, start = self.fixture()
        self.pending(fixture, b)
        Clock.instant = start + timedelta(seconds=300)
        self.assert_baselined_without_work(fixture, b)

    def test_changed_bar_is_baselined_even_if_previous_bar_was_admitted(self):
        fixture, b, Clock, start = self.fixture()
        self.pending(fixture, b)
        fixture._advance_bar()
        Clock.instant = start + timedelta(seconds=65)
        self.assert_baselined_without_work(fixture, b)

    def test_restart_cannot_resume_previous_startup_admission(self):
        fixture, b, Clock, start = self.fixture()
        self.pending(fixture, b)
        Clock.instant = start + timedelta(seconds=65)
        b.SERVER_STARTED_AT = "different-fixture-startup"
        self.assert_baselined_without_work(fixture, b)

    def test_stream_switch_cannot_reuse_old_chart_admission(self):
        fixture, b, Clock, start = self.fixture()
        self.pending(fixture, b)
        Clock.instant = start + timedelta(seconds=65)
        fixture.symbol = "EURUSD"
        self.assert_baselined_without_work(fixture, b)

    def test_missing_admission_never_becomes_a_paid_backlog(self):
        fixture, b, Clock, start = self.fixture()
        self.pending(fixture, b)
        self.change_pending(b, quotaAdmittedAt=None)
        Clock.instant = start + timedelta(seconds=65)
        self.assert_baselined_without_work(fixture, b)

    def test_future_admission_is_not_treated_as_existing_budget(self):
        fixture, b, Clock, start = self.fixture()
        self.pending(fixture, b)
        self.change_pending(b, quotaAdmittedAt=(start + timedelta(seconds=75)).isoformat())
        Clock.instant = start + timedelta(seconds=65)
        self.assert_baselined_without_work(fixture, b)

    def test_overlong_admission_is_not_treated_as_existing_budget(self):
        fixture, b, Clock, start = self.fixture()
        self.pending(fixture, b)
        self.change_pending(b, triggerExpiresAt=(start + timedelta(seconds=301)).isoformat())
        Clock.instant = start + timedelta(seconds=65)
        self.assert_baselined_without_work(fixture, b)

    def test_legacy_60_second_expiry_is_not_renewed(self):
        fixture, b, Clock, start = self.fixture()
        self.pending(fixture, b)
        self.change_pending(b, triggerExpiresAt=(start + timedelta(seconds=60)).isoformat())
        Clock.instant = start + timedelta(seconds=65)
        self.assert_baselined_without_work(fixture, b)

    def test_quota_recovery_after_real_gap_waits_for_next_observed_bar(self):
        fixture, b, Clock, start = self.fixture()
        fixture._save_observed_store()
        fixture._advance_bar()
        with mock.patch.object(b, "_collaboration_quota_gate", return_value={"allowed": False, "reason": "codex_limit_reached"}):
            skipped = b.ai_trade_council_automation_tick()
        self.assertEqual(skipped["kind"], "ai_trade_council_automation_skipped")
        Clock.instant = start + timedelta(seconds=65)
        self.assert_baselined_without_work(fixture, b)
        fixture._advance_bar()
        Clock.instant = start + timedelta(seconds=66)
        self.assertEqual(b.ai_trade_council_automation_tick()["kind"], "ai_trade_council_automation_settling")
        Clock.instant = start + timedelta(seconds=86)
        self.assertEqual(b.ai_trade_council_automation_tick()["kind"], "ai_trade_council_queued")
        self.assertEqual(len(fixture.calls), 1)
        self.assertEqual(fixture.calls[0]["automationContext"]["closedBarTime"], fixture.closed_bar_time)


if __name__ == "__main__":
    unittest.main()
