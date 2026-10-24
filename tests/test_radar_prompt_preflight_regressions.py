"""Radar prompt/zero-start quota regressions; run with the isolated harness.

Fixtures use temporary runtime state. All external readiness/process calls are
mocked; the harness independently blocks processes, sockets and production I/O.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import test_radar_batch_repair_lifecycle as lifecycle
import test_radar_daily_batch_corrective_retry as daily


class RadarPromptPreflightRegressions(unittest.TestCase):
    runtime = lifecycle.RadarBatchRepairLifecycleTests.runtime
    scheduled_radar = lifecycle.RadarBatchRepairLifecycleTests.scheduled_radar
    prime_daily_schedule = lifecycle.RadarBatchRepairLifecycleTests.prime_daily_schedule
    write_artifact = lifecycle.RadarBatchRepairLifecycleTests.write_artifact
    apply_batch_repair = lifecycle.RadarBatchRepairLifecycleTests.apply_batch_repair
    quota = staticmethod(daily.RadarDailyBatchCorrectiveRetryTests.quota)

    @classmethod
    def setUpClass(cls):
        cls.bridge = lifecycle.load_module("radar_prompt_regression_bridge", lifecycle.BRIDGE_PATH)
        cls.runner = lifecycle.load_module("radar_prompt_regression_runner", lifecycle.RUNNER_PATH)
        cls.projector = lifecycle.load_module(
            "radar_prompt_regression_projection",
            lifecycle.PROJECT_ROOT / "backend/local-runner/hq_backend/research/radar_prompt.py",
        )

    def setUp(self):
        self.bridge._invalidate_missions_read_cache()
        with self.bridge.RATE_LIMIT_LOCK:
            self.bridge.RATE_LIMIT_STATE.clear()
        readiness = mock.patch.object(self.bridge, "bridge_status", return_value={"codex": {"status": "ready"}})
        readiness.start()
        self.addCleanup(readiness.stop)
        for name, path in (("CODEX_RUNNER_PYTHON", Path(sys.executable)),
                           ("CODEX_RUNNER_SCRIPT", lifecycle.RUNNER_PATH)):
            patcher = mock.patch.object(self.bridge, name, path)
            patcher.start()
            self.addCleanup(patcher.stop)

    def catalog(self, rows=12):
        return {
            "items": [{"sourceUrl": f"https://public.example.org/tool-{i}-" + "x" * 90,
                       "duplicateFingerprint": f"{i:064x}"} for i in range(rows)],
            "included": rows, "total": rows, "truncated": False,
        }

    def catalog_block(self, document):
        return (self.projector.CATALOG_HEADER
                + json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n" + self.projector.CATALOG_END)

    def legacy_base(self, size=7867):
        # The deployed failure was 7,867 + two newlines + 696 repair chars.
        guards = ("Read-only public web. Exactly 6 unique verified entries. FREE-FIRST; "
                  "MQL5 last fallback maximum 1 of 6. Never invent evidence. "
                  "No downloads, attachments, credentials, writes, orders or unlicensed files.\n")
        text = guards + self.catalog_block(self.catalog()) + "\nPreserve all original safety requirements."
        self.assertLess(len(text), size)
        return text + "\n" + "p" * (size - len(text) - 1)

    def catalog_parts(self, text):
        start = text.index(self.projector.CATALOG_HEADER) + len(self.projector.CATALOG_HEADER)
        end = text.index(self.projector.CATALOG_END)
        return text[:start], json.loads(text[start:end]), text[end:]

    def test_actual_7867_plus_696_repair_fits_without_losing_fixed_instructions(self):
        base = self.legacy_base()
        repair = self.bridge._radar_batch_completion_repair_prompt_block()
        self.assertEqual(len(base), 7867)
        self.assertEqual(len(repair), 696)
        original = base + "\n\n" + repair
        self.assertEqual(len(original), 8565)
        projected = self.projector.project_radar_prompt(original)
        self.assertLessEqual(len(projected), 8000)
        prefix, catalog, suffix = self.catalog_parts(original)
        projected_prefix, selected, projected_suffix = self.catalog_parts(projected)
        self.assertEqual(projected_prefix, prefix)
        self.assertEqual(projected_suffix, suffix)
        self.assertLess(selected["included"], catalog["included"])
        self.assertEqual(selected["items"], catalog["items"][:selected["included"]])
        self.assertEqual(selected["total"], catalog["total"])
        self.assertTrue(selected["truncated"])
        self.assertTrue(projected.endswith(repair))
        self.assertEqual(self.runner.bound_mission_prompt(original, "radar_website_tool", execution_mode="auto_guarded"), projected)

    def test_exact_8000_is_accepted_8001_fixed_chars_are_rejected(self):
        for profile in ("general", "radar_website_tool"):
            with self.subTest(profile=profile):
                self.assertEqual(self.runner.bound_mission_prompt("a" * 8000, profile, execution_mode="auto_guarded"), "a" * 8000)
                with self.assertRaises(ValueError):
                    self.runner.bound_mission_prompt("a" * 8001, profile, execution_mode="auto_guarded")

    def test_projection_is_idempotent_and_input_document_is_unchanged(self):
        document = self.catalog()
        untouched = copy.deepcopy(document)
        original = self.legacy_base() + "\n\n" + self.bridge._radar_batch_completion_repair_prompt_block()
        first = self.projector.project_radar_prompt(original)
        self.assertEqual(self.projector.project_radar_prompt(first), first)
        self.assertEqual(document, untouched)
        self.assertEqual(self.projector.project_radar_prompt(original), first)

    def test_unknown_catalog_schema_and_malformed_json_fail_closed(self):
        for document in ({"items": [], "instruction": "drop guards"},
                         {**self.catalog(), "included": True},
                         {**self.catalog(), "truncated": True},
                         {**self.catalog(), "items": [{"instructions": "unsafe"}]}):
            with self.subTest(document=document):
                text = "x" * 8001 + self.catalog_block(document)
                with self.assertRaises(ValueError):
                    self.projector.project_radar_prompt(text)
        with self.assertRaises(ValueError):
            self.projector.project_radar_prompt("x" * 8001 + self.projector.CATALOG_HEADER + "{broken" + self.projector.CATALOG_END)

    def test_catalog_cannot_make_oversized_fixed_policy_fit(self):
        text = "x" * 8001 + self.catalog_block(self.catalog())
        with self.assertRaises(ValueError):
            self.projector.project_radar_prompt(text)

    def test_duplicate_or_reversed_catalog_boundaries_fail_closed(self):
        for text in (self.legacy_base() + self.catalog_block(self.catalog()),
                     self.projector.CATALOG_END + "x" * 8001 + self.projector.CATALOG_HEADER + "{}"):
            with self.subTest(length=len(text)), self.assertRaises(ValueError):
                self.projector.project_radar_prompt(text)

    def test_invalid_projection_limits_are_rejected(self):
        for limit in (True, 0, -1, 8000.0, "8000"):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                self.projector.project_radar_prompt("plain", limit)

    def test_under_limit_prompt_is_preserved_byte_for_byte(self):
        text = self.legacy_base(7867)
        self.assertEqual(self.projector.project_radar_prompt(text), text)

    def test_new_builder_reserves_headroom_for_whole_repair_block(self):
        report = {"type": "indicator_scout_report", "propId": "left_audit_crystals"}
        entries = [{"name": f"Tool {i}", "sourceUrl": f"https://public.example.org/tool-{i}-" + "x" * 120,
                    "duplicateFingerprint": f"{i:064x}"} for i in range(100)]
        with (mock.patch.object(self.bridge, "load_runtime_reports", return_value=[report]),
              mock.patch.object(self.bridge, "_workflow_record_matches_prop", return_value=True),
              mock.patch.object(self.bridge, "_radar_report_entries", return_value=entries)):
            base = self.bridge._workflow_prompt("discover_new_indicators", {"maxItems": 6}, None, radar_rotation_date="2026-10-23")
        repair = self.bridge._radar_batch_completion_repair_prompt_block()
        self.assertLessEqual(len(base), 8000 - len(repair) - 2)
        self.assertIn(self.projector.CATALOG_HEADER, base)
        full = base + "\n\n" + repair
        self.assertEqual(self.runner.bound_mission_prompt(full, "radar_website_tool", execution_mode="auto_guarded"), full)

    def test_runner_pre_ai_receipt_is_exact_and_starts_no_process(self):
        prompt = "read-only public research " + "x" * 8001
        with mock.patch.object(self.runner.subprocess, "Popen", side_effect=AssertionError("No process permitted")) as spawn:
            result = self.runner.run_codex(prompt, mission_id="mission-radar-regression", agent_id="codex_mcp_operator",
                execution_mode="auto_guarded", web_search=True, read_only_work=True, result_profile="radar_website_tool")
        spawn.assert_not_called()
        self.assertEqual(result["status"], "mission_prompt_too_large")
        self.assertIs(result["processStarted"], False)
        self.assertEqual(result["preAiFailure"], {
            "schemaVersion": "radar-pre-ai-failure-v1", "missionId": "mission-radar-regression",
            "promptDigest": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "failureCode": "mission_prompt_too_large", "aiProcessStarted": False, "childRunCount": 0,
        })

    def test_queued_legacy_projection_preserves_mission_authorization_and_daily_slot(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot)
            mission["detail"] = self.legacy_base()
            artifact = self.write_artifact(temp_dir, "incomplete.json", {"entries": []})
            self.apply_batch_repair(mission, artifact)
            self.bridge.replace_mission(mission)
            before = copy.deepcopy(mission)
            schedule_before = self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]
            first = self.bridge._radar_worker_prompt(mission)
            second = self.bridge._radar_worker_prompt(mission)
            self.assertEqual(first, second)
            self.assertLessEqual(len(first), 8000)
            self.assertEqual(mission, before)
            self.assertEqual(self.bridge.find_mission(mission["id"]), before)
            schedule_after = self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]
            self.assertEqual(schedule_after, schedule_before)
            self.assertEqual(schedule_after["dailyExecutionCount"], 1)
            self.assertEqual(schedule_after["dailyExecutionSlotKeys"], [slot])

    def test_oversized_fixed_prompt_blocks_before_claim_or_quota_reservation(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot)
            mission["detail"] = "Fixed instruction " + "x" * 8001
            self.bridge.replace_mission(mission)
            with (mock.patch.object(self.bridge, "reserve_rate_limit_slots") as reserve,
                  mock.patch.object(self.bridge, "codex_rate_limits") as quota,
                  mock.patch.object(self.bridge, "claim_auto_mission") as claim,
                  mock.patch.object(self.bridge, "run_safe_command") as runner):
                self.bridge.process_auto_mission("worker-radar-preflight", mission)
            reserve.assert_not_called()
            quota.assert_not_called()
            claim.assert_not_called()
            runner.assert_not_called()
            stored = self.bridge.find_mission(mission["id"])
            self.assertEqual(stored["status"], "blocked")
            self.assertEqual(stored["errorCode"], "mission_prompt_too_large")
            self.assertEqual(stored.get("attemptCount", 0), mission.get("attemptCount", 0))
            schedule = self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]
            self.assertEqual(schedule["dailyExecutionCount"], 1)

    def reserved_running_mission(self):
        # Each caller is a fresh temp runtime; do not share in-memory stamps
        # between independent negative subcases.
        with self.bridge.RATE_LIMIT_LOCK:
            self.bridge.RATE_LIMIT_STATE.clear()
        mission, slot = self.scheduled_radar()
        self.prime_daily_schedule(mission, slot)
        lease = "lease-radar-pre-ai-test"
        rate_key = f"real:{mission['owner']}:{mission['toolId']}:{mission['modelTier']}"
        digest, error, dynamic = self.bridge._radar_dynamic_open_reservation_digest(mission)
        self.assertIsNone(error)
        self.assertTrue(dynamic)
        allowed, _, other_stamps = self.bridge.reserve_rate_limit_slots(rate_key, 20, 1, consume=True)
        self.assertTrue(allowed)
        allowed, _, stamps = self.bridge.reserve_rate_limit_slots(rate_key, 20, 6, consume=True)
        self.assertTrue(allowed)
        reservation = self.bridge._corrective_open_hourly_reservation_record(
            rate_key, mission["modelTier"], 20, mission["id"], lease, digest, stamps)
        self.assertIsNotNone(reservation)
        mission.update(status="running", phase="auto_guarded_running", attemptCount=1)
        mission["execution"].update(leaseId=lease, workerId="worker-pre-ai", processStarted=False,
                                    correctiveOpenHourlyReservation=reservation)
        self.bridge.replace_mission(mission)
        runner = {"ok": True, "exitCode": 0, "processStarted": True}
        result = {"ok": False, "status": "mission_prompt_too_large", "workStatus": "failed", "processStarted": False,
                  "preAiFailure": {"schemaVersion": "radar-pre-ai-failure-v1", "missionId": mission["id"],
                    "promptDigest": hashlib.sha256(self.bridge._radar_worker_prompt(mission).encode("utf-8")).hexdigest(),
                    "failureCode": "mission_prompt_too_large", "aiProcessStarted": False, "childRunCount": 0}}
        return mission, lease, rate_key, other_stamps, runner, result

    def persisted_slots(self, key):
        with self.bridge.RATE_LIMIT_LOCK:
            return self.bridge._load_persisted_rate_limits_unlocked().get(key, [])

    def test_exact_zero_ai_receipt_refunds_only_its_six_slots_once(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, lease, key, other, runner, result = self.reserved_running_mission()
            self.assertEqual(len(self.persisted_slots(key)), 7)
            daily_before = self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]
            released = self.bridge._release_radar_pre_ai_reservation(mission["id"], lease, runner, result)
            self.assertIsNotNone(released)
            self.assertEqual(self.persisted_slots(key), other)
            reservation = released["execution"]["correctiveOpenHourlyReservation"]
            self.assertEqual(reservation["state"], "pre_ai_released")
            self.assertEqual(reservation["releasedPreAiRunCount"], 6)
            self.assertEqual(reservation["actualRunCount"], 0)
            self.assertIsNone(self.bridge._release_radar_pre_ai_reservation(mission["id"], lease, runner, result))
            self.assertEqual(self.persisted_slots(key), other)
            self.assertEqual(self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"], daily_before)

    def test_missing_ambiguous_or_started_runner_receipts_never_refund(self):
        cases = [
            ("wrapper_failed", "runner", "ok", False),
            ("wrapper_unknown", "runner", "processStarted", None),
            ("wrapper_bad_exit", "runner", "exitCode", 1),
            ("wrapper_boolean_exit", "runner", "exitCode", False),
            ("ai_started", "result", "processStarted", True),
            ("ai_unknown", "result", "processStarted", None),
            ("missing_receipt", "result", "preAiFailure", None),
            ("wrong_failure", "result", "status", "runner_failed"),
            ("receipt_started", "proof", "aiProcessStarted", True),
            ("child_started", "proof", "childRunCount", 1),
            ("boolean_child", "proof", "childRunCount", False),
            ("wrong_mission", "proof", "missionId", "mission-other"),
            ("wrong_prompt", "proof", "promptDigest", "0" * 64),
            ("wrong_schema", "proof", "schemaVersion", "untrusted-v1"),
        ]
        for name, target, field, value in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                mission, lease, key, _, runner, result = self.reserved_running_mission()
                before = self.persisted_slots(key)
                row = runner if target == "runner" else result if target == "result" else result["preAiFailure"]
                row[field] = value
                self.assertIsNone(self.bridge._release_radar_pre_ai_reservation(mission["id"], lease, runner, result))
                self.assertEqual(self.persisted_slots(key), before)
                self.assertEqual(self.bridge.find_mission(mission["id"])["execution"]["correctiveOpenHourlyReservation"]["state"], "reserved")

    def test_mismatched_lease_reservation_or_started_durable_mission_never_refund(self):
        cases = [
            ("changed_lease", "execution", "leaseId", "lease-other"),
            ("durable_started", "execution", "processStarted", True),
            ("durable_unknown", "execution", "processStarted", None),
            ("wrong_digest", "reservation", "reservationDigest", "0" * 64),
            ("wrong_bucket", "reservation", "rateKeyDigest", "0" * 64),
            ("wrong_candidate", "reservation", "candidateUrlDigest", "0" * 64),
            ("foreign_lease", "reservation", "leaseId", "lease-other"),
            ("wrong_mission", "reservation", "missionId", "mission-other"),
            ("missing_record", "execution", "correctiveOpenHourlyReservation", None),
            ("terminal", "mission", "status", "completed"),
            ("unbound_stamp", "reservation", "mainSlotStamp", 1.0),
        ]
        for name, target, field, value in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                mission, lease, key, _, runner, result = self.reserved_running_mission()
                before = self.persisted_slots(key)
                row = mission if target == "mission" else mission["execution"] if target == "execution" else mission["execution"]["correctiveOpenHourlyReservation"]
                row[field] = value
                self.bridge.replace_mission(mission)
                self.assertIsNone(self.bridge._release_radar_pre_ai_reservation(mission["id"], lease, runner, result))
                self.assertEqual(self.persisted_slots(key), before)

    def test_deterministic_prompt_failure_finishes_without_scheduled_retry(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, lease, key, other, runner, result = self.reserved_running_mission()
            self.bridge._dashboard_workflow_update_schedule_state("indicatorScoutSchedule", {"requestedEnabled": True})
            with mock.patch.object(self.bridge, "_apply_scheduled_public_research_completion_retry") as retry:
                finished = self.bridge.finish_auto_mission(mission["id"], lease, runner, result)
            retry.assert_not_called()
            self.assertIsNotNone(finished)
            self.assertIn(finished["status"], {"failed", "blocked"})
            self.assertEqual(finished["errorCode"], "mission_prompt_too_large")
            self.assertNotIn("scheduledCompletionRetry", finished)
            self.assertEqual(self.persisted_slots(key), other)
            self.assertIsNone(self.bridge.finish_auto_mission(mission["id"], lease, runner, result))
            self.assertEqual(self.persisted_slots(key), other)
            schedule = self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]
            self.assertEqual(schedule["dailyExecutionCount"], 1)

    def test_legacy_retry_three_of_six_remains_valid_without_new_authorization_or_slot(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot)
            self.bridge._dashboard_workflow_update_schedule_state("indicatorScoutSchedule", {"requestedEnabled": True})
            mission["detail"] = self.legacy_base(8565)
            # Seed the old durable record through the generic helper, then bind
            # the historical reason before the fixture authorization is issued.
            for _ in range(3):
                self.assertTrue(self.bridge._apply_scheduled_public_research_completion_retry(
                    mission, failure_code="runner_failed", failure_summary="Historical oversized prompt"))
            mission["scheduledCompletionRetry"]["lastFailureCode"] = "mission_prompt_too_large"
            mission["execution"]["lastDeferredReason"] = "mission_prompt_too_large"
            self.bridge._issue_backend_auto_safe_authorization(mission, issued_at=self.bridge.utc_now())
            self.bridge.replace_mission(mission)
            original = copy.deepcopy(mission)
            original_digest = self.bridge.mission_payload_digest(mission)
            state, error = self.bridge._scheduled_radar_completion_retry_state(mission, require_authorization=True)
            self.assertIsNone(error)
            self.assertEqual(state["attemptCount"], 3)
            self.assertEqual(state["maximumAttempts"], 6)
            for _ in range(2):
                self.assertLessEqual(len(self.bridge._radar_worker_prompt(mission)), 8000)
                self.assertEqual(self.bridge.mission_payload_digest(mission), original_digest)
                self.assertEqual(mission, original)
            self.assertFalse(self.bridge._apply_scheduled_public_research_completion_retry(
                mission, failure_code="mission_prompt_too_large", failure_summary="Unchanged deterministic failure"))
            self.assertEqual(mission, original)
            self.assertEqual(self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]["dailyExecutionCount"], 1)

    def test_non_radar_worker_prompt_does_not_project_other_workflows(self):
        original = self.legacy_base(8565)
        for mission in ({"detail": original},
                        {"toolId": "codex_web_research", "detail": original,
                         "workflowContext": {"propId": "other", "actionId": "discover_new_indicators"}},
                        {"toolId": "ai_trade_council_vote", "detail": original}):
            with self.subTest(tool=mission.get("toolId")):
                self.assertEqual(self.bridge._radar_worker_prompt(mission), original)

    def test_legacy_oversize_worker_uses_projected_stdin_in_same_daily_mission(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot)
            mission["detail"] = self.legacy_base()
            artifact = self.write_artifact(temp_dir, "legacy-worker-incomplete.json", {"entries": []})
            self.apply_batch_repair(mission, artifact)
            self.bridge.replace_mission(mission)
            original_detail = mission["detail"]
            original_idempotency = mission["idempotencyKey"]
            original_digest = self.bridge.mission_payload_digest(mission)
            capture = []

            def no_ai_runner(command, **kwargs):
                capture.append((command, kwargs.get("input_text")))
                return {"ok": False, "exitCode": 1, "processStarted": False,
                        "output": json.dumps({"ok": False, "status": "failed", "processStarted": False})}

            reserve = mock.Mock(wraps=self.bridge.reserve_rate_limit_slots)
            with (mock.patch.object(self.bridge, "codex_rate_limits", return_value=self.quota()),
                  mock.patch.object(self.bridge, "_collaboration_quota_gate", return_value={"allowed": True, "reason": "ready"}),
                  mock.patch.object(self.bridge, "reserve_rate_limit_slots", reserve),
                  mock.patch.object(self.bridge, "run_safe_command", side_effect=no_ai_runner),
                  mock.patch.object(self.bridge, "finish_auto_mission") as finish,
                  mock.patch.object(self.bridge, "heartbeat_auto_mission"),
                  mock.patch.object(self.bridge, "update_mission_worker_state"),
                  mock.patch.object(self.bridge, "invalidate_codex_rate_limit_cache")):
                self.bridge.process_auto_mission("worker-legacy-oversize", mission)
            self.assertEqual(len(capture), 1)
            command, stdin = capture[0]
            self.assertIn("--result-profile", command)
            self.assertEqual(command[command.index("--result-profile") + 1], "radar_website_tool")
            self.assertEqual(len(original_detail), 8565)
            self.assertEqual(stdin, self.bridge._radar_worker_prompt(mission))
            self.assertLessEqual(len(stdin), 8000)
            self.assertEqual(self.runner.bound_mission_prompt(stdin, "radar_website_tool", execution_mode="auto_guarded"), stdin)
            self.assertEqual([call.args[2] for call in reserve.call_args_list], [6, 6])
            self.assertEqual([call.kwargs["consume"] for call in reserve.call_args_list], [False, True])
            finish.assert_called_once()
            stored = self.bridge.find_mission(mission["id"])
            self.assertEqual(stored["detail"], original_detail)
            self.assertEqual(stored["idempotencyKey"], original_idempotency)
            self.assertEqual(self.bridge.mission_payload_digest(stored), original_digest)
            self.assertEqual(self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]["dailyExecutionCount"], 1)

    def assert_refund_io_failure_preserves_terminal_reason(self, fault, expected_state, expected_remaining):
        for error_type in (OSError, self.bridge.DataIntegrityError):
            with self.subTest(fault=fault, error=error_type.__name__), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                mission, lease, key, _, runner, result = self.reserved_running_mission()
                real_save = self.bridge.save_missions
                real_release = self.bridge.release_rate_limit_slots
                real_audit = self.bridge.append_audit
                save_calls = 0

                def save_with_fault(rows):
                    nonlocal save_calls
                    save_calls += 1
                    if save_calls == {"first_save": 1, "second_save": 2}.get(fault):
                        raise error_type("Synthetic isolated reservation persistence failure")
                    return real_save(rows)

                def release_with_fault(*args, **kwargs):
                    if fault == "release":
                        raise error_type("Synthetic isolated slot release failure")
                    return real_release(*args, **kwargs)

                def audit_with_fault(event):
                    if fault == "audit" and event.get("type") == "mission.radar_pre_ai_reservation_released":
                        raise error_type("Synthetic isolated audit write failure")
                    return real_audit(event)

                with (mock.patch.object(self.bridge, "save_missions", side_effect=save_with_fault),
                      mock.patch.object(self.bridge, "release_rate_limit_slots", side_effect=release_with_fault),
                      mock.patch.object(self.bridge, "append_audit", side_effect=audit_with_fault),
                      mock.patch.object(self.bridge, "_apply_scheduled_public_research_completion_retry") as retry):
                    finished = self.bridge.finish_auto_mission(mission["id"], lease, runner, result)
                retry.assert_not_called()
                self.assertIsNotNone(finished)
                stored = self.bridge.find_mission(mission["id"])
                self.assertIn(stored["status"], {"failed", "blocked"})
                self.assertEqual(stored["errorCode"], "mission_prompt_too_large")
                self.assertNotIn("scheduledCompletionRetry", stored)
                self.assertEqual(stored["execution"]["correctiveOpenHourlyReservation"]["state"], expected_state)
                self.assertEqual(len(self.persisted_slots(key)), expected_remaining)
                self.assertIsNone(self.bridge.finish_auto_mission(mission["id"], lease, runner, result))
                self.assertEqual(len(self.persisted_slots(key)), expected_remaining)
                self.assertEqual(self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]["dailyExecutionCount"], 1)

    def test_first_refund_save_failure_preserves_reservation_and_deterministic_failure(self):
        self.assert_refund_io_failure_preserves_terminal_reason("first_save", "reserved", 7)

    def test_refund_release_failure_preserves_pending_record_and_deterministic_failure(self):
        self.assert_refund_io_failure_preserves_terminal_reason("release", "pre_ai_release_pending", 7)

    def test_second_refund_save_failure_keeps_durable_pending_and_does_not_release_twice(self):
        self.assert_refund_io_failure_preserves_terminal_reason("second_save", "pre_ai_release_pending", 1)

    def test_refund_audit_failure_does_not_reclassify_or_retry_the_mission(self):
        self.assert_refund_io_failure_preserves_terminal_reason("audit", "pre_ai_released", 1)


if __name__ == "__main__":
    unittest.main()
