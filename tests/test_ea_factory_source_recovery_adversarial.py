"""Independent Source recovery provenance checks using isolated real stores."""
from __future__ import annotations

import copy
import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

import test_ea_factory_operator_source_recovery as recovery_support
import test_ea_factory_followup_hardening as bridge_support


class SourceRecoveryAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = bridge_support.load_bridge()

    def setUp(self):
        self.f = recovery_support.OperatorSourceRecoveryTests()
        self.f.bridge = self.bridge
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)

    def test_replay_after_state_commit_interruption_reuses_one_receipt_and_no_ai(self):
        f, b = self.f, self.bridge
        original_mission = copy.deepcopy(f.mission)
        with mock.patch.object(b, "_write_ea_factory_state_unlocked", side_effect=OSError("simulated commit failure")):
            with self.assertRaises(OSError):
                f.submit()
        self.assertEqual(len(b.load_missions()), 2)
        result = f.submit()
        current = f.reload()
        self.assertEqual(len(b.load_missions()), 2)
        self.assertEqual(len(current["sourceRecoveryHistory"]), 1)
        self.assertEqual(len(current["versions"]), 1)
        self.assertEqual(next(row for row in b.load_missions() if row["id"] == original_mission["id"]), original_mission)
        self.assertFalse(result["workerStarted"])
        f.dispatch.assert_not_called()
        f.start.assert_not_called()

    def test_reservation_owns_exact_request_after_materializer_interruption(self):
        f, b = self.f, self.bridge
        writer = b._ea_factory_source_recovery_runner()
        with mock.patch.object(writer, "materialize_ea_factory_source_result", side_effect=OSError("simulated writer failure")):
            with self.assertRaises(OSError):
                f.submit()
        journal, archive = b._ea_factory_source_recovery_files(f.build)
        reservation = journal.read_bytes()
        self.assertFalse(archive.exists())
        self.assertEqual(b.load_missions(), [f.mission])
        with self.assertRaises(b.RequestError) as caught:
            f.submit({**f.payload, "content": f.content + "\n"})
        self.assertEqual(caught.exception.status, 409)
        self.assertEqual(journal.read_bytes(), reservation)
        f.submit()
        self.assertEqual(journal.read_bytes(), reservation)
        self.assertEqual(len(f.reload()["sourceRecoveryHistory"]), 1)

    def test_missing_or_changed_archive_denies_restart_and_replay(self):
        f, b = self.f, self.bridge
        f.submit()
        current = f.reload()
        for path in b._ea_factory_source_recovery_files(current):
            original = path.read_bytes()
            for replacement in (b"{}", b"null"):
                with self.subTest(file=path.name, replacement=replacement):
                    path.write_bytes(replacement)
                    with self.assertRaises(b.DataIntegrityError):
                        f.reload()
                    with self.assertRaises(b.DataIntegrityError):
                        f.submit()
                    path.write_bytes(original)
            self.assertEqual(f.reload()["sourceRecoveryHistory"], current["sourceRecoveryHistory"])

    def test_spec_and_version_tamper_deny_restart(self):
        f, b = self.f, self.bridge
        f.submit()
        current = f.reload()
        root = f.root / "workspace" / "ea-factory" / f.build["id"]
        for path in (root / "Source" / "strategy-spec-v01.json", root / current["versions"][0]["versionFile"]):
            original = path.read_bytes()
            with self.subTest(file=path.name):
                path.write_bytes(original + b"\n ")
                with self.assertRaises(b.DataIntegrityError):
                    f.reload()
                path.write_bytes(original)
                self.assertEqual(f.reload()["versions"], current["versions"])

    def test_original_failure_report_content_is_immutable_after_recovery(self):
        f, b = self.f, self.bridge
        f.submit()
        path = f.reports / (f.failure["id"] + ".json")
        original = path.read_bytes()
        changed = json.loads(original)
        changed["summary"] = "Changed failure explanation"
        b.write_json(path, changed)
        with self.assertRaises(b.DataIntegrityError):
            f.reload()
        path.write_bytes(original)
        f.reload()

    def test_bookkeeping_mission_tamper_cannot_claim_ai_execution(self):
        f, b = self.f, self.bridge
        result = f.submit()
        original = b.load_missions()
        for field, value in (("attemptCount", 1), ("autoEligible", True), ("toolId", "codex_cli_task")):
            changed = copy.deepcopy(original)
            next(row for row in changed if row["id"] == result["recoveryMissionId"])[field] = value
            with self.subTest(field=field):
                b.save_missions(changed)
                with self.assertRaises(b.DataIntegrityError):
                    f.reload()
                b.save_missions(original)
        current = f.reload()
        recovery = next(row for row in original if row["id"] == result["recoveryMissionId"])
        self.assertIsNone(b._mission_existing_credit_consent(recovery, self.credit_settings(current)))

    def credit_settings(self, build):
        now = datetime.now(timezone.utc)
        return {"existingCreditPolicy": {"schemaVersion": "existing-credit-policy-v1", "grants": [{
            "buildId": build["id"], "buildIdentityDigest": self.bridge._existing_credit_build_identity_digest(build),
            "allowedAt": (now - timedelta(minutes=1)).isoformat(),
            "expiresAt": (now + timedelta(hours=1)).isoformat(), "allowExistingCredits": True,
        }]}}

    def create_review_lineage(self):
        f, b = self.f, self.bridge
        result = f.submit()
        build = f.reload()
        report = b.read_json(f.reports / (result["reportId"] + ".json"), None)
        missions = b.load_missions()
        source = b._workflow_source_binding("right_server_racks", "review_source_code", report, missions)
        self.assertIsNotNone(source)
        transfer = {**copy.deepcopy(f.mission["workflowContext"]["agentTransfer"]), **source}
        raw_source = {"reportId": result["reportId"], "sourceKind": "report",
                      "sourcePropId": "right_server_racks", "sourceMissionId": result["recoveryMissionId"],
                      "transferAgentId": "ea_developer", "type": "ea_build_report", "status": "ready",
                      "agentTransfer": transfer}
        review = b._ea_factory_stage_row(build, "source_review")
        review.update(status="queued", missionId="mission-independent-recovery-review", startedAt=b.utc_now(),
                      requestIdempotencyKey="independent-recovery-review")
        review["requestDigest"] = b._ea_factory_advance_request_digest(build, "source_review")
        review["missionIdempotencyKey"] = b._ea_factory_stage_mission_idempotency_key(build["id"], "source_review", review["requestIdempotencyKey"])
        inputs = {"sourceReportId": result["reportId"], "platform": build["platform"], "brief": b._ea_factory_review_brief(build)}
        context = b._dashboard_workflow_lineage("right_server_racks", "review_source_code", inputs, raw_source,
            trigger_source="backend", plugin_profile=b._trusted_workflow_plugin_profile("right_server_racks", "review_source_code", inputs))
        mission = {**copy.deepcopy(f.mission), "id": review["missionId"], "idempotencyKey": review["missionIdempotencyKey"],
                   "status": "queued", "errorCode": None, "attemptCount": 0, "completedAt": None, "reportIds": [],
                   "execution": {"processStarted": False, "dispatchState": "queued"}, "workflowContext": context}
        missions.append(mission)
        b.save_missions(missions)
        build["oneClickRun"].update(status="queued", currentStageId="source_review", completedAt=None, failureCode=None)
        state = b._load_ea_factory_state_unlocked()
        state["builds"] = [build]
        b._write_ea_factory_state_unlocked(state)
        return build, mission, result

    def test_normal_review_transport_and_credit_consent_accept_recovered_source_only(self):
        b = self.bridge
        build, mission, result = self.create_review_lineage()
        current = self.f.reload()
        sandbox = b._trusted_backend_ea_factory_worker_sandbox(mission)
        self.assertIsNotNone(sandbox)
        self.assertEqual(sandbox["stageId"], "source_review")
        packet = b._ea_factory_source_review_transport_for_mission(mission, sandbox)
        self.assertIn(self.f.payload["fileName"], json.dumps(packet))
        self.assertIn(result["sourceDigest"], json.dumps(packet))
        grant = b._mission_existing_credit_consent(mission, self.credit_settings(current))
        self.assertIsNotNone(grant)
        self.assertEqual(grant["buildId"], build["id"])
        recovery = next(row for row in b.load_missions() if row["id"] == result["recoveryMissionId"])
        self.assertIsNone(b._mission_existing_credit_consent(recovery, self.credit_settings(current)))
        forged = copy.deepcopy(mission)
        forged["workflowContext"]["inputs"]["sourceReportId"] = self.f.failure["id"]
        self.assertIsNone(b._mission_existing_credit_consent(forged, self.credit_settings(current)))
        with self.assertRaises(b.DataIntegrityError):
            b._ea_factory_source_review_transport_for_mission(forged, sandbox)

    def test_terminal_marked_failed_with_live_owned_process_cannot_recover(self):
        f, b = self.f, self.bridge
        with mock.patch.dict(b.MISSION_WORKER_PROCESSES, {f.mission["id"]: {"process": object()}}):
            with self.assertRaises(b.RequestError):
                f.submit()
        self.assertFalse(any(path.exists() for path in b._ea_factory_source_recovery_files(f.build)))
        self.assertEqual(b.load_missions(), [f.mission])

    def test_lone_surrogate_returns_request_error_before_reservation(self):
        with self.assertRaises(self.bridge.RequestError) as caught:
            self.f.submit({**self.f.payload, "content": "\ud800"})
        self.assertEqual(caught.exception.status, 422)
        self.assertFalse(any(path.exists() for path in self.bridge._ea_factory_source_recovery_files(self.f.build)))

    def test_conflicting_bookkeeping_id_is_not_rewritten_or_adopted(self):
        f, b = self.f, self.bridge
        digest = b.payload_digest(b.EA_FACTORY_SOURCE_RECOVERY_SCHEMA, f.build["id"], f.payload)
        conflicting = {"id": "mission-eaf-recovery-" + digest[:24], "toolId": "manager_mission",
                       "status": "completed", "owner": "risk_guard", "targetId": "right_server_racks",
                       "idempotencyKey": "unrelated-request", "reportIds": [], "attemptCount": 0,
                       "autoEligible": False, "requiresHumanApproval": False}
        b.save_missions([f.mission, conflicting])
        before = b.load_missions()
        with self.assertRaises((b.RequestError, b.DataIntegrityError)):
            f.submit()
        self.assertEqual(b.load_missions(), before)
        self.assertFalse(b._ea_factory_source_program_exists(f.build))
        self.assertFalse(any(path.exists() for path in b._ea_factory_source_recovery_files(f.build)))

    def test_origin_marker_cannot_replace_committed_recovery_receipt(self):
        f, b = self.f, self.bridge
        forged = copy.deepcopy(f.build)
        stage = b._ea_factory_stage_row(forged, "generate_source")
        stage.update(status="completed", evidenceVerified=True, sourceOrigin="operator_recovery",
                     sourceRecoveryId="ea-source-recovery-forged")
        with self.assertRaises(b.DataIntegrityError):
            b._ea_factory_revalidated_source_recovery(forged)
        with self.assertRaises(b.DataIntegrityError):
            b._ea_factory_sync_build_status(forged, missions=[f.mission], reports=[f.failure])
        self.assertEqual(b.load_missions(), [f.mission])


if __name__ == "__main__":
    unittest.main()
