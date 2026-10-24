"""Proven-unused child quota must survive Radar's same-mission repair branch."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import test_radar_batch_repair_lifecycle as lifecycle
import test_radar_daily_batch_corrective_retry as daily
import test_radar_prompt_preflight_regressions as preflight


class RadarRepairHourlySettlementTests(unittest.TestCase):
    runtime = lifecycle.RadarBatchRepairLifecycleTests.runtime
    scheduled_radar = lifecycle.RadarBatchRepairLifecycleTests.scheduled_radar
    prime_daily_schedule = lifecycle.RadarBatchRepairLifecycleTests.prime_daily_schedule
    write_artifact = lifecycle.RadarBatchRepairLifecycleTests.write_artifact
    urls = staticmethod(lifecycle.RadarBatchRepairLifecycleTests.urls)
    entries = lifecycle.RadarBatchRepairLifecycleTests.entries
    valid_six_result = lifecycle.RadarBatchRepairLifecycleTests.valid_six_result
    apply_batch_repair = lifecycle.RadarBatchRepairLifecycleTests.apply_batch_repair
    make_running = lifecycle.RadarBatchRepairLifecycleTests.make_running
    add_verification_manifest = daily.RadarDailyBatchCorrectiveRetryTests.add_verification_manifest
    write_source_artifact = daily.RadarDailyBatchCorrectiveRetryTests.write_source_artifact
    reserved_running_mission = preflight.RadarPromptPreflightRegressions.reserved_running_mission
    persisted_slots = preflight.RadarPromptPreflightRegressions.persisted_slots
    setUp = preflight.RadarPromptPreflightRegressions.setUp

    @classmethod
    def setUpClass(cls):
        cls.bridge = lifecycle.load_module("radar_repair_hourly_bridge", lifecycle.BRIDGE_PATH)
        cls.runner = lifecycle.load_module("radar_repair_hourly_runner", lifecycle.RUNNER_PATH)

    def running_result(self, temp_dir, main_open_count=6):
        mission, lease, key, unrelated, _, _ = self.reserved_running_mission()
        self.bridge._dashboard_workflow_update_schedule_state("indicatorScoutSchedule", {"requestedEnabled": True})
        tier = self.bridge.load_orchestration_contract()["modelTiers"][mission["modelTier"]]
        mission["execution"]["correctiveOpenHourlyReservation"]["maximumRunsPerHour"] = self.bridge.clamp_int(tier.get("maxRunsPerHour"), 12, 1, 200)
        mission["execution"].update(processStarted=True, dispatchState="running", workingDirectory="workspace",
                                    writeRoots=[], controlPlaneWritable=False, webSearchEnabled=True, webSearchUsed=True)
        self.bridge.replace_mission(mission)
        result = self.valid_six_result(temp_dir, final_name="repair-result.final.md", run_id="run-repair-result")
        result = self.add_verification_manifest(temp_dir, result, self.urls(), main_open_count=main_open_count,
                                               run_id="run-repair-result")
        result["artifacts"]["final"] = self.write_source_artifact(temp_dir, self.urls(), name="repair-result.final.md")
        if main_open_count >= 1:
            receipt = self.bridge._bounded_radar_corrective_open_verification_receipt(mission, result)
            self.assertTrue(receipt["valid"], receipt)
            self.assertIsNotNone(self.bridge._corrective_open_hourly_release_plan(mission, receipt))
        return mission, lease, key, unrelated, {"ok": True, "exitCode": 0, "processStarted": True}, result

    def finish_duplicate(self, mission, lease, runner, result):
        duplicate = self.bridge._radar_source_key(self.urls()[0])
        with (mock.patch.object(self.bridge, "_radar_existing_catalog_identities", return_value=(set(), {duplicate})),
              mock.patch.object(self.bridge, "create_report") as report):
            finished = self.bridge.finish_auto_mission(mission["id"], lease, runner, result)
        report.assert_not_called()
        self.assertIsNotNone(finished)
        self.assertEqual(finished["status"], "queued")
        self.assertEqual(finished["id"], mission["id"])
        self.assertEqual(finished["idempotencyKey"], mission["idempotencyKey"])
        self.assertEqual(finished["radarBatchRepair"]["lastObservedItemCount"], 5)
        self.assertFalse(finished["radarBatchRepair"]["newDailyReservation"])
        self.assertEqual(self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]["dailyExecutionCount"], 1)
        return finished

    def running_repaired_result(self, temp_dir, main_open_count=6):
        mission, lease, key, unrelated, runner, result = self.running_result(temp_dir, main_open_count)
        original = copy.deepcopy(mission["execution"]["correctiveOpenHourlyReservation"])
        failure = self.write_artifact(temp_dir, "previous-incomplete.final.md", {"status": "invalid_output", "evidence": []})
        mission = self.apply_batch_repair(mission, failure)
        reservation_digest, error, dynamic = self.bridge._radar_dynamic_open_reservation_digest(mission)
        self.assertIsNone(error)
        self.assertTrue(dynamic)
        reservation = self.bridge._corrective_open_hourly_reservation_record(
            key, mission["modelTier"], original["maximumRunsPerHour"], mission["id"], lease,
            reservation_digest, [original["mainSlotStamp"], *original["childSlotStamps"]])
        reservation["reservedAt"] = original["reservedAt"]
        mission["execution"]["correctiveOpenHourlyReservation"] = reservation
        mission = self.make_running(mission, lease)
        receipt = self.bridge._bounded_radar_corrective_open_verification_receipt(mission, result)
        self.assertTrue(receipt["valid"], receipt)
        self.assertIsNotNone(self.bridge._corrective_open_hourly_release_plan(mission, receipt))
        return mission, lease, key, unrelated, runner, result

    def finish_success(self, mission, lease, runner, result):
        with (mock.patch.object(self.bridge, "_radar_existing_catalog_identities", return_value=(set(), set())),
              mock.patch.object(self.bridge, "queue_radar_publisher_image_enrichment")):
            finished = self.bridge.finish_auto_mission(mission["id"], lease, runner, result)
        self.assertIsNotNone(finished)
        self.assertEqual(finished["status"], "completed")
        self.assertEqual(finished["radarBatchRepair"]["status"], "completed")
        self.assertFalse(finished["radarBatchRepair"]["automaticRetry"])
        self.assertFalse(finished["execution"]["automaticRetry"])
        self.assertEqual(len(finished["reportIds"]), 1)
        report_path = self.bridge.RUNTIME_REPORTS_DIR / f"{finished['reportIds'][0]}.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "ready")
        self.assertEqual(len(report["metrics"]["entries"]), 6)
        return finished, report_path

    def test_successful_repaired_report_settles_only_unused_children_and_never_retries(self):
        for main_opens in (6, 3):
            with self.subTest(main_opens=main_opens), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                mission, lease, key, unrelated, runner, result = self.running_repaired_result(temp_dir, main_opens)
                reservation = copy.deepcopy(mission["execution"]["correctiveOpenHourlyReservation"])
                child_runs = 6 - main_opens
                expected = sorted([*unrelated, reservation["mainSlotStamp"], *reservation["childSlotStamps"][:child_runs]])
                finished, report_path = self.finish_success(mission, lease, runner, result)
                self.assertEqual(self.persisted_slots(key), expected)
                self.assertEqual(finished["execution"]["correctiveOpenHourlyReservation"]["state"], "reconciled")
                before_report = report_path.read_bytes()
                before_schedule = copy.deepcopy(self.bridge.load_dashboard_workflow_settings())
                self.assertIsNone(self.bridge.finish_auto_mission(mission["id"], lease, runner, result))
                self.assertEqual(self.persisted_slots(key), expected)
                self.assertEqual(report_path.read_bytes(), before_report)
                self.assertEqual(self.bridge.load_dashboard_workflow_settings(), before_schedule)
                self.assertEqual(self.bridge.find_mission(mission["id"])["status"], "completed")

    def completed_with_unsettled_reservation(self, temp_dir):
        mission, lease, key, unrelated, runner, result = self.running_repaired_result(temp_dir)
        reservation = copy.deepcopy(mission["execution"]["correctiveOpenHourlyReservation"])
        # Reproduce the previous deployed success path: real durable report and
        # terminal mission, but the post-commit accounting settlement was skipped.
        with mock.patch.object(self.bridge, "_settle_corrective_open_hourly_reservation", return_value=None):
            completed, report_path = self.finish_success(mission, lease, runner, result)
        self.assertEqual(completed["execution"]["correctiveOpenHourlyReservation"]["state"], "reserved")
        self.assertEqual(len(self.persisted_slots(key)), 7)
        return completed, lease, key, unrelated, reservation, report_path, result

    def test_completed_success_recovery_and_crash_replay_preserve_report_main_and_later_slots(self):
        for crash_point in ("legacy_completed", "pending_intent", "after_release", "reconciled_snapshot"):
            with self.subTest(crash_point=crash_point), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                completed, lease, key, unrelated, reservation, report_path, _ = self.completed_with_unsettled_reservation(temp_dir)
                before_report = report_path.read_bytes()
                before_schedule = copy.deepcopy(self.bridge.load_dashboard_workflow_settings())
                allowed, _, later = self.bridge.reserve_rate_limit_slots(key, reservation["maximumRunsPerHour"], 3, consume=True)
                self.assertTrue(allowed)
                expected = sorted([*unrelated, reservation["mainSlotStamp"], *later])
                real_save = self.bridge.save_missions
                real_release = self.bridge.release_rate_limit_slots

                def crash_during_save(rows):
                    value = real_save(rows)
                    current = next(row for row in rows if row["id"] == completed["id"])
                    state = current["execution"]["correctiveOpenHourlyReservation"]["state"]
                    if (crash_point == "pending_intent" and state == "settlement_pending"
                            or crash_point == "reconciled_snapshot" and state == "reconciled"):
                        raise SystemExit("Synthetic crash after completed accounting save")
                    return value

                def crash_during_release(*args, **kwargs):
                    value = real_release(*args, **kwargs)
                    if crash_point == "after_release":
                        raise SystemExit("Synthetic crash after completed exact slot release")
                    return value

                if crash_point != "legacy_completed":
                    with (mock.patch.object(self.bridge, "save_missions", side_effect=crash_during_save),
                          mock.patch.object(self.bridge, "release_rate_limit_slots", side_effect=crash_during_release)):
                        with self.assertRaises(SystemExit):
                            self.bridge.reconcile_completed_radar_batch_hourly_reservations()
                    self.assertEqual(self.bridge.find_mission(completed["id"])["status"], "completed")
                with self.bridge.RATE_LIMIT_LOCK:
                    self.bridge.RATE_LIMIT_STATE.clear()
                self.bridge._invalidate_missions_read_cache()
                with mock.patch.object(self.bridge, "create_report") as create_report:
                    recovered = self.bridge.reconcile_completed_radar_batch_hourly_reservations()
                    again = self.bridge.reconcile_completed_radar_batch_hourly_reservations()
                create_report.assert_not_called()
                self.assertEqual(recovered, 0 if crash_point == "reconciled_snapshot" else 1)
                self.assertEqual(again, 0)
                self.assertEqual(self.persisted_slots(key), expected)
                current = self.bridge.find_mission(completed["id"])
                self.assertEqual(current["status"], "completed")
                self.assertFalse(current["execution"]["automaticRetry"])
                self.assertFalse(current["radarBatchRepair"]["automaticRetry"])
                self.assertEqual(current["reportIds"], completed["reportIds"])
                self.assertEqual(current["completedAt"], completed["completedAt"])
                self.assertEqual(current["attemptCount"], completed["attemptCount"])
                self.assertEqual(current["idempotencyKey"], completed["idempotencyKey"])
                self.assertEqual(current["execution"]["correctiveOpenHourlyReservation"]["state"], "reconciled")
                self.assertEqual(report_path.read_bytes(), before_report)
                self.assertEqual(self.bridge.load_dashboard_workflow_settings(), before_schedule)

    def test_completed_success_recovery_rejects_missing_or_changed_proof_without_retry(self):
        for tamper in ("missing_report", "changed_report", "commit_digest", "missing_manifest", "changed_manifest",
                       "receipt_disagreement", "lease", "reservation_digest", "final_artifact", "mission_payload"):
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                completed, _, key, _, _, report_path, result = self.completed_with_unsettled_reservation(temp_dir)
                if tamper == "missing_report":
                    report_path.unlink()
                elif tamper == "changed_report":
                    report = json.loads(report_path.read_text(encoding="utf-8"))
                    report["metrics"]["entries"][0]["summaryTh"] += " altered"
                    report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
                elif tamper == "commit_digest":
                    completed["radarBatchReportCommit"]["reportDigest"] = "0" * 64
                elif tamper == "missing_manifest":
                    (Path(temp_dir) / result["correctiveOpenVerificationArtifact"]).unlink()
                elif tamper == "changed_manifest":
                    (Path(temp_dir) / result["correctiveOpenVerificationArtifact"]).write_text("{}", encoding="utf-8")
                elif tamper == "receipt_disagreement":
                    completed["execution"]["correctiveOpenVerificationReceipt"]["valid"] = False
                elif tamper == "lease":
                    completed["execution"]["leaseId"] = "lease-other"
                elif tamper == "reservation_digest":
                    completed["execution"]["correctiveOpenHourlyReservation"]["reservationDigest"] = "0" * 64
                elif tamper == "final_artifact":
                    (Path(temp_dir) / completed["artifactPath"]).write_text("{}", encoding="utf-8")
                else:
                    completed["detail"] += " Altered after completion."
                self.bridge.replace_mission(completed)
                before_slots = self.persisted_slots(key)
                before_schedule = copy.deepcopy(self.bridge.load_dashboard_workflow_settings())
                before_mission = copy.deepcopy(self.bridge.find_mission(completed["id"]))
                with mock.patch.object(self.bridge, "create_report") as create_report:
                    self.assertEqual(self.bridge.reconcile_completed_radar_batch_hourly_reservations(), 0)
                create_report.assert_not_called()
                self.assertEqual(self.persisted_slots(key), before_slots)
                self.assertEqual(self.bridge.find_mission(completed["id"]), before_mission)
                self.assertEqual(self.bridge.load_dashboard_workflow_settings(), before_schedule)

    def test_completed_lineage_copy_never_reenables_retry_or_admits_nonterminal_missions(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            completed, _, key, _, _, _, _ = self.completed_with_unsettled_reservation(temp_dir)
            before = copy.deepcopy(completed)
            before_slots = self.persisted_slots(key)
            validated = self.bridge._radar_completed_settlement_lineage(completed)
            self.assertIsNotNone(validated)
            self.assertTrue(validated["radarBatchRepair"]["automaticRetry"])
            self.assertEqual(completed, before)
            for status in ("queued", "running", "blocked", "failed"):
                with self.subTest(mission_status=status):
                    candidate = copy.deepcopy(completed)
                    candidate["status"] = status
                    self.assertIsNone(self.bridge._radar_completed_settlement_lineage(candidate))
            candidate = copy.deepcopy(completed)
            candidate["radarBatchReportCommit"]["status"] = "pending"
            self.assertIsNone(self.bridge._radar_completed_settlement_lineage(candidate))
            self.assertEqual(self.persisted_slots(key), before_slots)
            self.assertEqual(self.bridge.find_mission(completed["id"]), before)

    def test_completed_reserved_history_with_absent_or_expired_children_is_not_rewritten(self):
        for state in ("all_absent", "all_expired"):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                completed, _, key, _, reservation, _, _ = self.completed_with_unsettled_reservation(temp_dir)
                if state == "all_absent":
                    self.assertEqual(self.bridge.release_rate_limit_slots(key, reservation["childSlotStamps"]), 5)
                before_slots = self.persisted_slots(key)
                before_mission = copy.deepcopy(self.bridge.find_mission(completed["id"]))
                checked_time = max([reservation["mainSlotStamp"], *reservation["childSlotStamps"]])
                checked_time += 3601 if state == "all_expired" else 1
                with (mock.patch.object(self.bridge.time, "time", return_value=checked_time),
                      mock.patch.object(self.bridge, "save_missions", wraps=self.bridge.save_missions) as save,
                      mock.patch.object(self.bridge, "release_rate_limit_slots", wraps=self.bridge.release_rate_limit_slots) as release):
                    self.assertEqual(self.bridge.reconcile_completed_radar_batch_hourly_reservations(), 0)
                save.assert_not_called()
                release.assert_not_called()
                self.assertEqual(self.persisted_slots(key), before_slots)
                self.assertEqual(self.bridge.find_mission(completed["id"]), before_mission)

    def test_duplicate_repair_releases_only_proven_unused_children_and_keeps_main(self):
        for main_opens in (6, 3, 1):
            with self.subTest(main_opens=main_opens), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                mission, lease, key, unrelated, runner, result = self.running_result(temp_dir, main_opens)
                reservation = copy.deepcopy(mission["execution"]["correctiveOpenHourlyReservation"])
                child_runs = 6 - main_opens
                expected = sorted([*unrelated, reservation["mainSlotStamp"], *reservation["childSlotStamps"][:child_runs]])
                self.finish_duplicate(mission, lease, runner, result)
                self.assertEqual(self.persisted_slots(key), expected)
                # Replayed completion cannot debit or return anything again.
                self.assertIsNone(self.bridge.finish_auto_mission(mission["id"], lease, runner, result))
                self.assertEqual(self.persisted_slots(key), expected)

    def test_missing_or_tampered_verification_manifest_does_not_refund_used_main_or_unknown_children(self):
        cases = ("missing_digest", "wrong_digest", "missing_file", "wrong_run", "invented_zero_children")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                mission, lease, key, _, runner, result = self.running_result(temp_dir)
                before = self.persisted_slots(key)
                if case == "missing_digest":
                    result.pop("correctiveOpenVerificationDigest", None)
                elif case == "wrong_digest":
                    result["correctiveOpenVerificationDigest"] = "0" * 64
                elif case == "missing_file":
                    (Path(temp_dir) / result["correctiveOpenVerificationArtifact"]).unlink()
                elif case == "wrong_run":
                    path = Path(temp_dir) / result["correctiveOpenVerificationArtifact"]
                    manifest = json.loads(path.read_text(encoding="utf-8"))
                    manifest["runId"] = "run-other"
                    payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
                    path.write_bytes(payload)
                    result["correctiveOpenVerificationDigest"] = hashlib.sha256(payload).hexdigest()
                else:
                    result = self.add_verification_manifest(temp_dir, result, self.urls(), main_open_count=3, run_id="run-repair-result")
                    result["correctiveOpenVerificationCount"] = 0
                    result["correctiveOpenVerifications"] = []
                with mock.patch.object(self.bridge, "create_report"):
                    self.bridge.finish_auto_mission(mission["id"], lease, runner, result)
                self.assertEqual(self.persisted_slots(key), before)

    def test_no_main_url_open_cannot_become_a_verified_success_or_receive_unproven_refund(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, lease, key, _, runner, result = self.running_result(temp_dir, main_open_count=0)
            before = self.persisted_slots(key)
            result.update(ok=False, status="invalid_output", workStatus="invalid_output", webSearchEvidenceVerified=False,
                          structuredOutputError=self.bridge.RADAR_EVIDENCE_OPEN_ERROR)
            with mock.patch.object(self.bridge, "create_report") as report:
                finished = self.bridge.finish_auto_mission(mission["id"], lease, runner, result)
            report.assert_not_called()
            self.assertNotEqual(finished["status"], "completed")
            self.assertEqual(self.persisted_slots(key), before)

    def test_restart_recovers_before_or_after_exact_release_without_touching_later_reservation(self):
        for crash_point in ("failed_snapshot", "pending_intent", "after_release", "reconciled_snapshot"):
            with self.subTest(crash_point=crash_point), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                mission, lease, key, unrelated, runner, result = self.running_result(temp_dir)
                original_reservation = copy.deepcopy(mission["execution"]["correctiveOpenHourlyReservation"])
                real_release = self.bridge.release_rate_limit_slots
                real_save = self.bridge.save_missions
                save_count = 0

                def crash_during_save(rows):
                    nonlocal save_count
                    save_count += 1
                    value = real_save(rows)
                    if save_count == {"failed_snapshot": 1, "pending_intent": 2, "reconciled_snapshot": 3}.get(crash_point):
                        raise SystemExit("Synthetic crash after durable settlement write")
                    return value

                def crash_during_release(*args, **kwargs):
                    value = real_release(*args, **kwargs)
                    if crash_point == "after_release":
                        raise SystemExit("Synthetic crash after exact slot release")
                    return value

                duplicate = self.bridge._radar_source_key(self.urls()[0])
                with (mock.patch.object(self.bridge, "_radar_existing_catalog_identities", return_value=(set(), {duplicate})),
                      mock.patch.object(self.bridge, "release_rate_limit_slots", side_effect=crash_during_release),
                      mock.patch.object(self.bridge, "save_missions", side_effect=crash_during_save),
                      mock.patch.object(self.bridge, "create_report")):
                    with self.assertRaises(SystemExit):
                        self.bridge.finish_auto_mission(mission["id"], lease, runner, result)
                durable = self.bridge.find_mission(mission["id"])
                self.assertIn(durable["status"], {"failed", "blocked"})
                self.assertEqual(durable["execution"]["correctiveOpenHourlyReservation"]["state"],
                                 "reserved" if crash_point == "failed_snapshot" else
                                 "reconciled" if crash_point == "reconciled_snapshot" else "settlement_pending")
                self.assertEqual(durable["correctiveOpenVerificationReceipt"], durable["execution"]["correctiveOpenVerificationReceipt"])
                self.assertEqual(len(self.persisted_slots(key)), 2 if crash_point in ("after_release", "reconciled_snapshot") else 7)
                allowed, _, later_stamps = self.bridge.reserve_rate_limit_slots(key, original_reservation["maximumRunsPerHour"], 4, consume=True)
                self.assertTrue(allowed)
                # Simulate a new interpreter reading the durable journal/bucket.
                with self.bridge.RATE_LIMIT_LOCK:
                    self.bridge.RATE_LIMIT_STATE.clear()
                self.bridge._invalidate_missions_read_cache()
                with (mock.patch.object(self.bridge, "_radar_existing_catalog_identities", return_value=(set(), {duplicate})),
                      mock.patch.object(self.bridge, "create_report") as report):
                    recovered = self.bridge.reconcile_current_day_public_research_output_repairs()
                    again = self.bridge.reconcile_current_day_public_research_output_repairs()
                report.assert_not_called()
                self.assertEqual(recovered, 1)
                self.assertEqual(again, 0)
                self.assertEqual(self.persisted_slots(key), sorted([*unrelated, original_reservation["mainSlotStamp"], *later_stamps]))
                current = self.bridge.find_mission(mission["id"])
                self.assertEqual(current["status"], "queued")
                self.assertEqual(current["idempotencyKey"], mission["idempotencyKey"])
                self.assertEqual(current["radarBatchRepair"]["lastObservedItemCount"], 5)
                self.assertEqual(self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]["dailyExecutionCount"], 1)

    def test_settlement_io_failure_retains_terminal_proof_before_any_repair_retry(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, lease, key, _, runner, result = self.running_result(temp_dir)
            duplicate = self.bridge._radar_source_key(self.urls()[0])
            before = self.persisted_slots(key)
            with (mock.patch.object(self.bridge, "_radar_existing_catalog_identities", return_value=(set(), {duplicate})),
                  mock.patch.object(self.bridge, "release_rate_limit_slots", side_effect=OSError("Synthetic isolated quota-store failure")),
                  mock.patch.object(self.bridge, "create_report") as report):
                self.bridge.finish_auto_mission(mission["id"], lease, runner, result)
            report.assert_not_called()
            durable = self.bridge.find_mission(mission["id"])
            self.assertIn(durable["status"], {"failed", "blocked"})
            self.assertNotIn("radarBatchRepair", durable)
            self.assertEqual(durable["execution"]["correctiveOpenHourlyReservation"]["state"], "settlement_pending")
            self.assertEqual(durable["correctiveOpenVerificationReceipt"], durable["execution"]["correctiveOpenVerificationReceipt"])
            self.assertEqual(self.persisted_slots(key), before)
            self.assertEqual(durable["attemptCount"], 1)
            with mock.patch.object(self.bridge, "_radar_existing_catalog_identities", return_value=(set(), {duplicate})):
                self.assertEqual(self.bridge.reconcile_current_day_public_research_output_repairs(), 1)
            self.assertEqual(len(self.persisted_slots(key)), 2)

    def test_restart_rejects_changed_manifest_or_pending_settlement_identity(self):
        for tamper in ("manifest", "settlement_token", "child_count", "release_count", "lease",
                       "missing_checkpoint", "checkpoint_mission", "checkpoint_digest", "payload", "receipt_disagreement", "final_artifact"):
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                mission, lease, key, _, runner, result = self.running_result(temp_dir)
                duplicate = self.bridge._radar_source_key(self.urls()[0])
                with (mock.patch.object(self.bridge, "_radar_existing_catalog_identities", return_value=(set(), {duplicate})),
                      mock.patch.object(self.bridge, "release_rate_limit_slots", side_effect=SystemExit("Synthetic crash"))):
                    with self.assertRaises(SystemExit):
                        self.bridge.finish_auto_mission(mission["id"], lease, runner, result)
                durable = self.bridge.find_mission(mission["id"])
                reservation = durable["execution"]["correctiveOpenHourlyReservation"]
                if tamper == "manifest":
                    (Path(temp_dir) / result["correctiveOpenVerificationArtifact"]).write_text("{}", encoding="utf-8")
                elif tamper == "settlement_token":
                    reservation["settlementToken"] = "0" * 64
                elif tamper == "child_count":
                    reservation["actualChildRunCount"] = 1
                elif tamper == "release_count":
                    reservation["requestedUnusedChildReleaseCount"] = 4
                elif tamper == "lease":
                    durable["execution"]["leaseId"] = "lease-other"
                elif tamper == "missing_checkpoint":
                    durable.pop("radarFailedAttemptSettlement", None)
                elif tamper == "checkpoint_mission":
                    durable["radarFailedAttemptSettlement"]["missionId"] = "mission-other"
                elif tamper == "checkpoint_digest":
                    durable["radarFailedAttemptSettlement"]["receiptDigest"] = "0" * 64
                elif tamper == "payload":
                    durable["detail"] += " Changed after checkpoint."
                elif tamper == "receipt_disagreement":
                    durable["execution"]["correctiveOpenVerificationReceipt"]["valid"] = False
                else:
                    (Path(temp_dir) / durable["artifactPath"]).write_text("{}", encoding="utf-8")
                self.bridge.replace_mission(durable)
                before = self.persisted_slots(key)
                with self.bridge.RATE_LIMIT_LOCK:
                    self.bridge.RATE_LIMIT_STATE.clear()
                self.bridge._invalidate_missions_read_cache()
                with mock.patch.object(self.bridge, "_radar_existing_catalog_identities", return_value=(set(), {duplicate})):
                    self.assertEqual(self.bridge.reconcile_current_day_public_research_output_repairs(), 0)
                self.assertEqual(self.persisted_slots(key), before)
                self.assertIn(self.bridge.find_mission(mission["id"])["status"], {"failed", "blocked"})

    def test_strict_radar_runner_instructs_one_full_url_open_without_relaxing_safety(self):
        prompt = self.runner.build_prompt(
            "Find exactly six public sources.", "codex_mcp_operator", "mission-radar-single-url",
            "specialist_balanced", 20000, execution_mode="auto_guarded", web_search=True,
            result_mode="work_report", read_only_work=True, result_profile="radar_website_tool", radar_required_count=6)
        trusted = prompt.split("User mission:", 1)[0]
        self.assertIn("Open exactly one full final source URL per Native Web Search open call", trusted)
        self.assertIn("repeat separately for all six URLs", trusted)
        self.assertIn("Never fabricate a source, entry, URL, open event", trusted)
        self.assertIn("exactly six evidence rows and exactly six entries", trusted)
        self.assertIn("Do not edit, create, move, rename, or delete any file", trusted)
        self.assertIn("access MT4/MT5, broker software, Telegram, deployment", trusted)

    def test_batched_reference_or_search_events_do_not_count_as_direct_url_opens(self):
        first, second = self.urls()[:2]
        events = [
            {"id": "batch-json", "query": json.dumps({"open": [{"ref_id": first}, {"ref_id": second}]}), "action": {"type": "other"}},
            {"id": "batch-urls", "action": {"type": "open_page", "urls": [first, second]}},
            {"id": "reference-only", "action": {"type": "open_page", "url": "turn0search0"}},
            {"id": "search-only", "query": first, "action": {"type": "search", "query": first}},
            {"id": "direct-url", "query": first, "action": {"type": "other"}},
        ]
        lines = "\n".join(json.dumps({"type": "item.completed", "item": {"type": "web_search", **event}}) for event in events)
        self.assertEqual(self.runner.completed_web_search_opened_urls(lines), [first])


if __name__ == "__main__":
    unittest.main()
