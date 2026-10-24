"""FX28 dispatch/Runner/report integration with only temporary, mocked I/O.

Execute through work/run-radar-isolated.py. No collector, Codex process,
network, terminal or account is accessed by this suite.
"""
import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import test_fx28_trend_runner as fixtures
import test_radar_batch_repair_lifecycle as lifecycle
import test_radar_daily_batch_corrective_retry as daily


class Fx28TrendIntegrationTests(unittest.TestCase):
    runtime = lifecycle.RadarBatchRepairLifecycleTests.runtime
    setUp = lifecycle.RadarBatchRepairLifecycleTests.setUp
    quota = staticmethod(daily.RadarDailyBatchCorrectiveRetryTests.quota)

    @classmethod
    def setUpClass(cls):
        cls.bridge = lifecycle.load_module("fx28_integration_bridge", lifecycle.BRIDGE_PATH)
        cls.runner = fixtures.load_runner("fx28_integration_runner")
        cls.engine = cls.bridge.fx_trend

    def tick(self, *, quota_allowed=True, now=None, news=False):
        snapshot, default_now = fixtures.market_snapshot(self.engine)
        now = now or default_now
        with mock.patch.object(self.bridge, "_fx_trend_collect", return_value=snapshot), \
             mock.patch.object(self.bridge, "_fx_trend_news_sources", return_value=[{"url": "https://www.ecb.europa.eu/press/pr/date/2026/html/index.en.html", "title": "ECB statement"}] if news else []), \
             mock.patch.object(self.bridge, "_dashboard_workflow_scheduler_gate", return_value={"allowed": quota_allowed, "reason": "ready" if quota_allowed else "quota_limit_reached", "remainingPercent": 80 if quota_allowed else 0}):
            result = self.bridge.fx_trend_service_tick(now=now)
        return snapshot, now, result

    def admitted(self, *, news=False):
        snapshot, now, result = self.tick(news=news)
        self.assertEqual(result["ai"]["status"], "queued", result)
        mission = self.bridge.find_mission(result["ai"]["missionId"])
        self.assertIsNotNone(mission)
        return snapshot, now, mission

    def process(self, root, mission, *, mutate=None, failure=None, use_news=False):
        calls, child_calls = [], []

        def fake_chat(command, **kwargs):
            child_calls.append(command)
            assignment = self.engine.prompt_assignment(calls[-1][1]["input_text"])
            payload = fixtures.explanation_fixture(self.engine, assignment, news=use_news)
            if mutate:
                mutate(payload)
            Path(command[command.index("-o") + 1]).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            events = [json.dumps({"type": "item.completed", "item": {"id": row["id"], "type": "web_search", "action": {"type": "open_page", "url": row["url"]}}}) for row in assignment["sourceRefs"] if use_news and row["kind"] == "news"]
            return {"ok": True, "exitCode": 0, "processStarted": True, "durationMs": 1, "stdout": "\n".join(events), "stderr": ""}

        def fake_wrapper(command, **kwargs):
            command = [str(value) for value in command]
            calls.append((command, kwargs))
            if failure:
                return {"ok": True, "exitCode": 0, "processStarted": True, "output": json.dumps({
                    "ok": False, "status": failure, "workStatus": "failed", "processStarted": True,
                    "processTreeTerminated": True, "message": "Synthetic infrastructure failure"})}
            result = self.runner.run_codex(kwargs["input_text"], "codex_mcp_operator", mission["id"],
                execution_mode=command[command.index("--execution-mode") + 1],
                result_profile=command[command.index("--result-profile") + 1],
                read_only_work="--read-only-work" in command, web_search="--web-search" in command,
                output_limit=int(command[command.index("--output-limit") + 1]))
            return {"ok": True, "exitCode": 0, "processStarted": True, "output": json.dumps(result, ensure_ascii=False)}

        with mock.patch.object(self.bridge, "codex_rate_limits", return_value=self.quota()), \
             mock.patch.object(self.bridge, "_collaboration_quota_gate", return_value={"allowed": True, "reason": "ready"}), \
             mock.patch.object(self.bridge, "run_safe_command", side_effect=fake_wrapper), \
             mock.patch.object(self.bridge, "heartbeat_auto_mission"), \
             mock.patch.object(self.bridge, "update_mission_worker_state"), \
             mock.patch.object(self.bridge, "invalidate_codex_rate_limit_cache"), \
             mock.patch.object(self.runner, "PROJECT_ROOT", Path(root)), \
             mock.patch.object(self.runner, "CODEX_RUNS_DIR", Path(root) / "data/runtime/codex-runs"), \
             mock.patch.object(self.runner, "chat_status", return_value={"ok": True, "status": "ready"}), \
             mock.patch.object(self.runner, "run_chat_command", side_effect=fake_chat), \
             mock.patch.object(self.runner, "complete_radar_evidence_open_urls", side_effect=AssertionError("No corrective children")), \
             mock.patch.object(self.runner, "complete_trading_system_research_required_open_urls", side_effect=AssertionError("No corrective children")):
            self.bridge.process_auto_mission("fx28-worker-fixture", mission)
        return self.bridge.find_mission(mission["id"]), calls, child_calls

    def test_actual_daily_dispatch_runner_report_read_model_one_slot_no_children(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            snapshot, now, mission = self.admitted()
            self.assertLess(len(mission["detail"]), 8000)
            self.assertIsNotNone(self.bridge._trusted_workflow_guard_intent(mission))
            self.assertEqual(mission["workflowContext"]["actionId"], "analyze_fx28_trends")
            self.assertEqual(mission["workflowContext"]["triggerSource"], "schedule")
            done, calls, children = self.process(folder, mission)
            self.assertEqual(done["status"], "completed", done)
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(children), 1)
            command, kwargs = calls[0]
            self.assertEqual(command[command.index("--result-profile") + 1], "fx_trend_daily_v1")
            self.assertIn("--read-only-work", command)
            self.assertLessEqual(len(kwargs["input_text"]), 20000)
            self.assertNotIn("--required-open-url", command)
            self.assertNotIn("correctiveOpenHourlyReservation", done["execution"])
            self.assertEqual(len(done["reportIds"]), 1)
            report = json.loads((self.bridge.RUNTIME_REPORTS_DIR / (done["reportIds"][0] + ".json")).read_text(encoding="utf-8"))
            self.assertEqual(report["type"], "fx28_trend_report")
            self.assertEqual(report["status"], "ready")
            model = self.bridge._fx_trend_read_model(now=now)
            self.assertEqual(model["ai"]["status"], "completed", model["ai"])
            self.assertEqual(len(model["ai"]["analysis"]["pairExplanations"]), 28)
            self.assertEqual(model["snapshotDigest"], self.engine.digest(snapshot))
            self.assertEqual(len(model["rows"]), 28)
            key = f"real:{mission['owner']}:{mission['toolId']}:{mission['modelTier']}"
            self.assertEqual(len(self.bridge._load_persisted_rate_limits_unlocked().get(key, [])), 1)

    def test_read_model_news_links_only_cited_native_open_sources_and_locked_collection_time(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            raw, now, mission = self.admitted(news=True)
            done, _, _ = self.process(folder, mission, use_news=True)
            self.assertEqual(done["status"], "completed", done)
            model = self.bridge._fx_trend_read_model(now=now)
            ai = model["ai"]
            self.assertEqual(ai["status"], "completed")
            self.assertEqual(ai["collectedAt"], raw["collectedAt"])
            self.assertEqual(len(ai["newsSources"]), 1)
            source = ai["newsSources"][0]
            self.assertEqual(source["url"], "https://www.ecb.europa.eu/press/pr/date/2026/html/index.en.html")
            self.assertEqual(source["id"], ai["analysis"]["newsContext"][0]["sourceRef"])
            self.assertEqual(source["summaryTh"], ai["analysis"]["newsContext"][0]["summaryTh"])

    def test_same_daily_slot_replay_after_completion_does_not_create_or_run_again(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            _, now, mission = self.admitted()
            done, _, _ = self.process(folder, mission)
            self.assertEqual(done["status"], "completed", done)
            before = copy.deepcopy(self.bridge.load_missions())
            with mock.patch.object(self.bridge, "run_safe_command", side_effect=AssertionError("No process during tick replay")):
                _, _, result = self.tick(now=now + timedelta(minutes=1))
            self.assertEqual(result["ai"]["missionId"], mission["id"])
            self.assertEqual(result["ai"]["status"], "completed")
            self.assertEqual(self.bridge.load_missions(), before)

    def test_fresh_prices_stay_visible_when_quota_blocks_and_get_never_executes(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            snapshot, now, result = self.tick(quota_allowed=False)
            self.assertEqual(result["ai"]["status"], "deferred")
            self.assertEqual(self.bridge.load_missions(), [])
            with mock.patch.object(self.bridge, "run_safe_command", side_effect=AssertionError("GET must not execute")), \
                 mock.patch.object(self.bridge, "_fx_trend_collect", side_effect=AssertionError("GET must not collect")), \
                 mock.patch.object(self.bridge, "run_dashboard_workflow_action", side_effect=AssertionError("GET must not dispatch")):
                model = self.bridge._fx_trend_read_model(now=now)
            self.assertEqual(model["status"], "ready")
            self.assertEqual(model["summary"]["evaluatedPairCount"], 28)
            self.assertEqual(model["snapshotDigest"], self.engine.digest(snapshot))
            self.assertEqual(model["ai"]["quota"]["status"], "quota_limit_reached")

    def test_missing_or_stale_prices_do_not_create_daily_mission(self):
        for missing in (True, False):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as folder, self.runtime(folder):
                raw, now = fixtures.market_snapshot(self.engine)
                if missing:
                    raw["pairs"] = []
                else:
                    raw["collectedAt"] = self.engine.iso(now - timedelta(hours=2))
                with mock.patch.object(self.bridge, "_fx_trend_collect", return_value=raw), \
                     mock.patch.object(self.bridge, "_dashboard_workflow_scheduler_gate", return_value={"allowed": True}), \
                     mock.patch.object(self.bridge, "run_safe_command", side_effect=AssertionError("No process for missing data")):
                    result = self.bridge.fx_trend_service_tick(now=now)
                self.assertEqual(self.bridge.load_missions(), [])
                self.assertEqual(result["ai"]["status"], "waiting")

    def test_cold_history_partial_prices_show_but_daily_ai_waits_for_collection(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            raw, now = fixtures.market_snapshot(self.engine)
            raw["pairs"][-1]["series"] = {}
            raw["pairs"][-1]["errors"] = [{"timeframe": "W1", "code": "collection_time_budget_reached"}]
            with mock.patch.object(self.bridge, "_fx_trend_collect", return_value=raw), \
                 mock.patch.object(self.bridge, "_dashboard_workflow_scheduler_gate", return_value={"allowed": True}), \
                 mock.patch.object(self.bridge, "run_safe_command", side_effect=AssertionError("No AI during cold load")):
                result = self.bridge.fx_trend_service_tick(now=now)
            self.assertEqual(result["ai"]["status"], "waiting")
            self.assertEqual(self.bridge.load_missions(), [])
            model = self.bridge._fx_trend_read_model(now=now)
            self.assertEqual(model["status"], "partial")
            self.assertEqual(model["summary"]["evaluatedPairCount"], 27)
            self.assertEqual(self.bridge._load_persisted_rate_limits_unlocked(), {})

    def test_mutated_locked_snapshot_blocks_before_runner_and_quota_reservation(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            _, _, mission = self.admitted()
            digest = mission["workflowContext"]["inputs"]["snapshotDigest"]
            path = self.bridge._fx_trend_path("snapshots") / (digest + ".json")
            path.write_text("{}", encoding="utf-8")
            done, calls, children = self.process(folder, mission)
            self.assertEqual(calls, [])
            self.assertEqual(children, [])
            self.assertNotEqual(done["status"], "completed")
            self.assertIn("fx28_assignment_invalid", json.dumps(done))
            self.assertEqual(self.bridge._load_persisted_rate_limits_unlocked(), {})

    def test_wrong_result_digest_is_not_published_and_deterministic_prices_remain(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            raw, now, mission = self.admitted()
            before = self.bridge._fx_trend_read_model(now=now)["rows"]
            done, calls, _ = self.process(folder, mission, mutate=lambda value: value.update(snapshotDigest="0" * 64))
            self.assertEqual(len(calls), 1)
            self.assertNotEqual(done["status"], "completed")
            # A diagnostic failure report is part of the existing mission
            # contract; it must never become a ready FX explanation report.
            for report_id in done.get("reportIds", []):
                report = json.loads((self.bridge.RUNTIME_REPORTS_DIR / (report_id + ".json")).read_text(encoding="utf-8"))
                self.assertNotEqual(report["status"], "ready", report)
            model = self.bridge._fx_trend_read_model(now=now)
            self.assertEqual(model["rows"], before)
            self.assertNotIn("analysis", model["ai"])

    def test_persisted_result_tamper_is_rejected_on_read_without_changing_price_rows(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            _, now, mission = self.admitted()
            done, _, _ = self.process(folder, mission)
            self.assertEqual(done["status"], "completed", done)
            before = self.bridge._fx_trend_read_model(now=now)
            changed = copy.deepcopy(done)
            values = changed["workflowOutputContract"]["values"]
            payload = json.loads(values["fxTrendAnalysis"])
            payload["pairExplanations"][0]["short"]["sourceRefs"] = ["price:USDJPY:M15"]
            values["fxTrendAnalysis"] = json.dumps(payload, ensure_ascii=False)
            self.bridge.replace_mission(changed)
            with mock.patch.object(self.bridge, "run_safe_command", side_effect=AssertionError("GET must not execute")):
                after = self.bridge._fx_trend_read_model(now=now)
            self.assertEqual(after["ai"]["status"], "failed")
            self.assertNotIn("analysis", after["ai"])
            self.assertEqual(after["rows"], before["rows"])

    def test_manual_action_cannot_bypass_backend_only_daily_schedule(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            _, _, mission = self.admitted()
            before = copy.deepcopy(self.bridge.load_missions())
            with self.assertRaises(self.bridge.RequestError):
                self.bridge.run_dashboard_workflow_action("left_signal_cube", {"actionId": "analyze_fx28_trends", "form": mission["workflowContext"]["inputs"], "idempotencyKey": "manual-forbidden"})
            self.assertEqual(self.bridge.load_missions(), before)

    def test_rehashed_assignment_cannot_change_derived_price_direction(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            _, _, mission = self.admitted()
            inputs = copy.deepcopy(mission["workflowContext"]["inputs"])
            assignment = self.bridge._fx_trend_assignment(inputs)
            original = assignment["rows"][0]["horizons"]["short"]["bias"]
            assignment["rows"][0]["horizons"]["short"]["bias"] = "BEARISH" if original != "BEARISH" else "BULLISH"
            inputs["assignmentDigest"] = self.engine.digest(assignment)
            self.bridge.write_json(self.bridge._fx_trend_path("assignments") / (inputs["assignmentDigest"] + ".json"), assignment)
            with self.assertRaisesRegex(ValueError, "deriv|snapshot|assignment"):
                self.bridge._fx_trend_assignment(inputs)

    def test_yesterday_pending_daily_context_expires_before_quota_or_process(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            _, now, mission = self.admitted()
            tomorrow = now + timedelta(days=1)
            class NextDayClock(datetime):
                @classmethod
                def now(cls, tz=None):
                    return tomorrow.astimezone(tz) if tz else tomorrow.replace(tzinfo=None)
            with mock.patch.object(self.bridge, "datetime", NextDayClock):
                done, calls, children = self.process(folder, mission)
            self.assertEqual(calls, [])
            self.assertEqual(children, [])
            self.assertNotEqual(done["status"], "completed")
            self.assertIn("fx28_daily_context_expired", json.dumps(done))
            self.assertEqual(self.bridge._load_persisted_rate_limits_unlocked(), {})

    def test_retry_uses_same_mission_assignment_and_normal_second_quota_slot(self):
        for second_failure in (None, "timeout"):
            with self.subTest(second_failure=second_failure), tempfile.TemporaryDirectory() as folder, self.runtime(folder):
                self.setUp()  # Each subcase has an independent in-memory quota bucket.
                _, _, mission = self.admitted()
                original_inputs = copy.deepcopy(mission["workflowContext"]["inputs"])
                deferred, calls, _ = self.process(folder, mission, failure="timeout")
                self.assertEqual(deferred["status"], "queued", deferred)
                self.assertEqual(len(calls), 1)
                self.assertEqual(deferred["fxTrendRetry"]["retryCount"], 1)
                self.assertEqual(deferred["fxTrendRetry"]["maximumAttempts"], 2)
                self.assertEqual(deferred["workflowContext"]["inputs"], original_inputs)
                self.assertEqual(deferred["idempotencyKey"], mission["idempotencyKey"])
                not_due, calls, _ = self.process(folder, deferred)
                self.assertEqual(calls, [])
                self.assertEqual(not_due["status"], "queued")
                due = self.engine.timestamp(deferred["execution"]["nextAttemptAt"]) + timedelta(seconds=1)
                class RetryClock(datetime):
                    @classmethod
                    def now(cls, tz=None):
                        return due.astimezone(tz) if tz else due.replace(tzinfo=None)
                with mock.patch.object(self.bridge, "datetime", RetryClock):
                    done, calls, _ = self.process(folder, deferred, failure=second_failure)
                self.assertEqual(len(calls), 1)
                self.assertEqual(done["attemptCount"], 2)
                self.assertEqual(done["status"], "completed" if second_failure is None else "failed", done)
                self.assertEqual(done["fxTrendRetry"]["retryCount"], 1)
                self.assertEqual(done["workflowContext"]["inputs"], original_inputs)
                self.assertEqual(len(self.bridge.load_missions()), 1)
                key = f"real:{mission['owner']}:{mission['toolId']}:{mission['modelTier']}"
                self.assertEqual(len(self.bridge._load_persisted_rate_limits_unlocked().get(key, [])), 2)

    def test_invalid_output_never_retries_and_retry_gate_rejects_wrong_lease_or_day(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            _, now, mission = self.admitted()
            running = lifecycle.RadarBatchRepairLifecycleTests.make_running(self, mission, "fx28-negative-lease")
            before = copy.deepcopy(self.bridge.find_mission(mission["id"]))
            for code in ("invalid_output", "fx28_assignment_invalid", "provider_rate_limited"):
                self.assertIsNone(self.bridge._fx_trend_retry_infrastructure_failure(mission["id"], "fx28-negative-lease", {"processStarted": True}, {"ok": False, "status": code}))
            self.assertIsNone(self.bridge._fx_trend_retry_infrastructure_failure(mission["id"], "wrong-lease", {}, {"ok": False, "status": "timeout"}))
            late = datetime.fromisoformat("2026-10-23T23:58:00+07:00")
            class ClosingDayClock(datetime):
                @classmethod
                def now(cls, tz=None):
                    return late.astimezone(tz) if tz else late.replace(tzinfo=None)
            with mock.patch.object(self.bridge, "datetime", ClosingDayClock):
                self.assertIsNone(self.bridge._fx_trend_retry_infrastructure_failure(mission["id"], "fx28-negative-lease", {}, {"ok": False, "status": "runner_failed"}))
            self.assertEqual(self.bridge.find_mission(mission["id"]), before)

    def test_future_cache_is_not_current_and_cannot_admit_ai(self):
        with tempfile.TemporaryDirectory() as folder, self.runtime(folder):
            raw, now = fixtures.market_snapshot(self.engine)
            future = now + timedelta(hours=1)
            raw["collectedAt"] = self.engine.iso(future)
            model = self.engine.build_read_model(raw, now=future)
            self.assertEqual(model["status"], "ready")
            store = {"model": model, "nextPriceAt": self.engine.iso(future)}
            self.bridge._fx_trend_save(store)
            with mock.patch.object(self.bridge, "run_dashboard_workflow_action", side_effect=AssertionError("Future data must not dispatch")):
                waiting = self.bridge._fx_trend_daily_admission(store, now)
                view = self.bridge._fx_trend_read_model(now=now)
            self.assertEqual(waiting["ai"]["status"], "waiting")
            self.assertEqual(view["status"], "waiting")
            self.assertTrue(view["stale"])
            self.assertTrue(all(h["bias"] == "INSUFFICIENT_DATA" for row in view["rows"] for h in row["horizons"].values()))


if __name__ == "__main__":
    unittest.main()
