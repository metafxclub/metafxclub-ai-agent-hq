"""Real Mission lifecycle over temp stores; model/provider and MT5 never run."""
import copy
import json
import threading
import unittest
from datetime import datetime, timezone
from unittest import mock
from tests import test_manager_parallel_missions as base
from tests.test_sentiment_news_ai import fixture, result_for


class DailyNewsTests(unittest.TestCase):
    setUpBase = base.ManagerParallelMissionTests.setUp
    process = base.ManagerParallelMissionTests.process

    @classmethod
    def setUpClass(cls):
        cls.bridge = base.load_bridge()

    def setUp(self):
        self.setUpBase()
        # Admission has a Thai 00:10 gate. Fixtures must not depend on the
        # wall clock of the CI runner or cross midnight during the suite.
        self.now = datetime(2026, 10, 28, 12, 0, tzinfo=self.bridge.sentiment_news_daily.THAI)
        fixture_owner = self

        class FixtureClock(datetime):
            @classmethod
            def now(cls, tz=None):
                value = fixture_owner.now
                return value.astimezone(tz) if tz else value.replace(tzinfo=None)

        self.stack.enter_context(mock.patch.object(self.bridge.sentiment_news_daily, "datetime", FixtureClock))
        self.service = self.bridge.sentiment_news_daily.DailyNews(self.bridge)
        self.stack.enter_context(mock.patch.object(self.bridge, "_SENTIMENT_NEWS_DAILY", self.service))
        self.day = self.now.date().isoformat()
        self.news = fixture()
        self.news["dayThai"] = self.day
        self.news["lastSuccessAt"] = f"{self.day}T00:00:35Z"
        for event in self.news["events"]:
            event.update(dayThai=self.day, time=f"{self.day}T01:00:00Z")
        self.news["calendarEvents"] = copy.deepcopy(self.news["events"])
        self.stack.enter_context(mock.patch.object(self.service, "news", side_effect=lambda: copy.deepcopy(self.news)))
        self.gate = self.stack.enter_context(mock.patch.object(self.service, "council_gate", return_value=None))
        self.stack.enter_context(mock.patch.object(self.service, "timeout", return_value=180))
        self.stack.enter_context(mock.patch.object(self.bridge, "peek_codex_rate_limits", side_effect=self.quota))
        self.dispatched = []
        self.runner = self.stack.enter_context(mock.patch.object(self.bridge, "run_safe_command", side_effect=self.fake_runner))

    def queue(self):
        self.service.next_poll = 0
        self.service.tick()
        rows = self.bridge.load_missions()
        self.assertEqual(len(rows), 1, rows)
        mission = rows[0]
        self.assertTrue(mission["autoEligible"], mission)
        self.assertIsNone(self.bridge.auto_execution_authorization_error(mission))
        return mission

    def fake_runner(self, command, **kwargs):
        self.dispatched.append(command)
        self.assertIn("--read-only-work", command)
        self.assertNotIn("--web-search", command)
        self.assertNotIn("--allow-existing-credits", command)
        self.assertEqual(command[command.index("--result-profile") + 1], "sentiment_news_daily_v1")
        self.assertEqual(command[command.index("--timeout") + 1], "180")
        assignment = self.bridge.sentiment_news_ai.assignment_from_prompt(kwargs["input_text"])
        self.assertTrue(self.service.ledger(self.day)["attempted"], "Reservation must precede launch")
        result = {"ok": True, "workStatus": "completed", "status": "completed",
                  "newsAnalysis": result_for(assignment), "finalMessage": "All news covered", "artifacts": {}}
        return {"ok": True, "exitCode": 0, "processStarted": True, "output": json.dumps(result)}

    def test_real_mission_report_publication_and_restart_does_not_replay(self):
        mission = self.queue()
        self.process(mission)
        final = self.bridge.find_mission(mission["id"])
        self.assertEqual(final["status"], "completed", final)
        self.assertTrue(final["reportIds"])
        artifact = self.service.read(self.service.root / "result.json")
        self.assertEqual(len(artifact["result"]["events"]), 3)
        self.assertEqual(self.service.ledger(self.day)["status"], "ready")
        self.service.next_poll = 0
        self.service.tick()
        restarted = self.bridge.sentiment_news_daily.DailyNews(self.bridge)
        restarted.tick()
        self.assertEqual(len(self.dispatched), 1)
        self.assertEqual(len(self.bridge.load_missions()), 1)

    def test_thai_midnight_waits_until_0010_without_consuming_the_daily_attempt(self):
        for minute, second in ((0, 0), (9, 59)):
            with self.subTest(minute=minute, second=second):
                self.now = self.now.replace(hour=0, minute=minute, second=second)
                self.service.next_poll = 0
                self.service.tick()
                self.assertEqual(self.service.ledger(self.day)["reason"], "waiting_calendar")
                self.assertFalse(self.service.ledger(self.day)["attempted"])
                self.assertEqual(self.bridge.load_missions(), [])
                self.assertEqual(self.dispatched, [])
        self.now = self.now.replace(hour=0, minute=10, second=0)
        mission = self.queue()
        self.process(mission)
        self.assertEqual(self.bridge.find_mission(mission["id"])["status"], "completed")
        self.assertEqual(self.service.ledger(self.day)["status"], "ready")
        self.service.next_poll = 0
        self.service.tick()
        self.assertEqual(len(self.dispatched), 1)
        self.assertEqual(len(self.bridge.load_missions()), 1)

    def test_active_council_defers_before_model_and_attempt_is_not_consumed(self):
        mission = self.queue()
        self.gate.return_value = "council_busy"
        self.process(mission)
        self.assertEqual(self.dispatched, [])
        self.assertFalse(self.service.ledger(self.day)["attempted"])
        self.assertEqual(self.bridge.find_mission(mission["id"])["status"], "queued")

    def test_quota_block_and_operator_manual_do_not_create_mission(self):
        with mock.patch.object(self.bridge, "_collaboration_quota_gate", return_value={"allowed": False}):
            self.service.tick()
        self.assertEqual(self.bridge.load_missions(), [])
        self.assertFalse(self.service.ledger(self.day)["attempted"])
        self.service.next_poll = 0
        with mock.patch.object(self.bridge, "load_operator_mode_record", return_value={"mode": "manual"}):
            self.service.tick()
        self.assertEqual(self.bridge.load_missions(), [])

    def test_changed_calendar_fails_closed_before_dispatch(self):
        mission = self.queue()
        self.news["events"][0]["forecast"] = "9%"
        self.news["calendarEvents"] = copy.deepcopy(self.news["events"])
        self.process(mission)
        self.assertEqual(self.dispatched, [])

    def test_ambiguous_crash_after_reservation_never_replays(self):
        mission = self.queue()
        self.service.begin(mission)
        self.process(mission)
        self.assertEqual(self.dispatched, [])
        self.service.next_poll = 0
        self.service.tick()
        self.assertEqual(len(self.bridge.load_missions()), 1)
        self.assertTrue(self.service.ledger(self.day)["attempted"])

    def test_failed_result_has_no_partial_publication_or_retry(self):
        mission = self.queue()
        self.runner.side_effect = lambda *a, **k: {"ok": True, "processStarted": True,
            "output": json.dumps({"ok": True, "workStatus": "completed", "newsAnalysis": {"events": []}})}
        self.process(mission)
        self.assertEqual(self.bridge.find_mission(mission["id"])["status"], "failed")
        self.assertFalse((self.service.root / "result.json").exists())
        self.assertTrue(self.service.ledger(self.day)["attempted"])
        self.service.next_poll = 0
        self.service.tick()
        self.assertEqual(self.runner.call_count, 1)

    def test_prior_day_mission_cannot_dispatch_or_backfill(self):
        mission = self.queue()
        old = copy.deepcopy(mission)
        old["sentimentNewsContext"]["dayThai"] = "2000-01-01"
        old["idempotencyKey"] = "sentiment-news:2000-01-01"
        self.assertEqual(self.service.preflight(old), "day_expired")

    def test_council_priority_cancels_only_news_process_event(self):
        mission = self.queue()
        def slow_runner(command, **kwargs):
            self.gate.return_value = "council_busy"
            self.assertTrue(kwargs["cancel_event"].wait(3))
            self.assertFalse(self.bridge.MISSION_WORKER_STOP.is_set())
            return {"ok": False, "processStarted": True, "exitCode": "cancelled", "output": "{}"}
        self.runner.side_effect = slow_runner
        self.process(mission)
        self.assertFalse(self.bridge.MISSION_WORKER_STOP.is_set())
        self.assertEqual(self.service.ledger(self.day)["status"], "failed")

    def test_private_marker_and_requester_cannot_be_removed_or_retargeted(self):
        mission = self.queue()
        for mutation in (
            lambda m: m.pop("sentimentNewsContext"),
            lambda m: m.update(requester="human"),
            lambda m: m["sentimentNewsContext"].update(inputDigest="a" * 64),
        ):
            changed = copy.deepcopy(mission)
            mutation(changed)
            with self.subTest(change=changed.get("sentimentNewsContext")):
                self.assertNotEqual(self.bridge.mission_payload_digest(changed), self.bridge.mission_payload_digest(mission))
                self.assertIsNotNone(self.bridge.auto_execution_authorization_error(changed))

    def test_expired_assignment_after_model_finishes_is_not_published_or_replayed(self):
        mission = self.queue()
        def completes_after_day_rollover(command, **kwargs):
            returned = self.fake_runner(command, **kwargs)
            self.stack.enter_context(mock.patch.object(self.service, "assignment", side_effect=ValueError("day_expired")))
            return returned
        self.runner.side_effect = completes_after_day_rollover
        self.process(mission)
        self.assertNotEqual(self.bridge.find_mission(mission["id"])["status"], "completed")
        self.assertFalse((self.service.root / "result.json").exists())
        self.assertTrue(self.service.ledger(self.day)["attempted"])
        self.service.next_poll = 0
        self.service.tick()
        self.assertEqual(len(self.dispatched), 1)

    def test_fresh_coordinator_does_not_replay_reserved_day(self):
        mission = self.queue()
        self.service.begin(mission)
        restarted = self.bridge.sentiment_news_daily.DailyNews(self.bridge)
        with mock.patch.object(restarted, "news", return_value=copy.deepcopy(self.news)), mock.patch.object(restarted, "council_gate", return_value=None):
            restarted.tick()
        self.assertTrue(restarted.ledger(self.day)["attempted"])
        self.assertEqual(len(self.bridge.load_missions()), 1)
        self.assertEqual(self.dispatched, [])

    def test_duplicate_completion_without_current_lease_cannot_downgrade_ready_day(self):
        mission = self.queue()
        self.process(mission)
        final = self.bridge.find_mission(mission["id"])
        result_before = (self.service.root / "result.json").read_bytes()
        self.assertEqual(self.service.ledger(self.day)["status"], "ready")
        self.service.complete(mission, {"ok": True, "processStarted": True}, {"ok": True}, None)
        self.assertEqual(self.service.ledger(self.day)["status"], "ready")
        self.assertEqual((self.service.root / "result.json").read_bytes(), result_before)
        self.assertEqual(self.bridge.find_mission(mission["id"]), final)

    def test_no_process_receipt_cannot_claim_completed_ai_analysis(self):
        mission = self.queue()
        def no_process_receipt(command, **kwargs):
            returned = self.fake_runner(command, **kwargs)
            returned["processStarted"] = False
            return returned
        self.runner.side_effect = no_process_receipt
        self.process(mission)
        self.assertNotEqual(self.bridge.find_mission(mission["id"])["status"], "completed")
        self.assertFalse((self.service.root / "result.json").exists())
        self.assertNotEqual(self.service.ledger(self.day)["status"], "ready")

    def test_current_date_empty_feed_never_spends_a_model_attempt(self):
        self.news["events"] = []
        self.news["calendarEvents"] = []
        self.news["status"] = "empty"
        self.service.tick()
        self.assertEqual(self.bridge.load_missions(), [])
        self.assertEqual(self.service.ledger(self.day)["status"], "empty")
        self.assertFalse(self.service.ledger(self.day)["attempted"])
        self.assertEqual(self.dispatched, [])


if __name__ == "__main__":
    unittest.main()
