"""Cross-boundary Radar v2 proof, publication, legacy and packaging regressions.

Run under the isolated runtime harness: no real Runner process or network is
used. Fixtures exercise the actual native-event parser and manifest writer,
then the actual Backend worker/report paths against temporary files.
"""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import test_radar_batch_repair_lifecycle as lifecycle
import test_radar_daily_batch_corrective_retry as daily


ROOT = Path(__file__).resolve().parents[1]
RADAR_CONTRACTS = (
    "contracts/research/radar-website-source-policy-v1.json",
    "contracts/research/radar-website-tool-compatibility-v1.json",
    "contracts/reports/report-contract.json",
    "contracts/tools/tool-permission-contract.json",
    "contracts/workflows/equipment-plugin-map.json",
)


class RadarFlexiblePackageTests(unittest.TestCase):
    def test_versioned_contracts_keep_legacy_and_expose_actual_zero_to_three(self):
        policy, compatibility, reports, tools, equipment = [
            json.loads((ROOT / name).read_text(encoding="utf-8")) for name in RADAR_CONTRACTS
        ]
        versions = policy["publicationPolicies"]
        self.assertEqual(versions["legacy"]["scheduledItemCount"], 6)
        self.assertEqual(policy["appliesTo"]["scheduledBatchSize"], 6)
        current = versions["current"]
        self.assertEqual((current["minimumItemCount"], current["maximumItemCount"]), (0, 3))
        self.assertEqual((current["mainProcessSlots"], current["correctiveChildSlots"]), (1, 0))
        self.assertTrue(current["completedSearchEventProofRequired"])
        self.assertFalse(current["scarcityRetryAllowed"])
        self.assertEqual(compatibility["entryContract"]["maximumItemsPerRun"], 6)
        self.assertEqual(compatibility["publicationPolicy"]["maximumItemsPerRun"], 3)
        self.assertEqual(compatibility["presentation"]["desktopGridColumns"], 3)
        self.assertTrue(compatibility["presentation"]["legacyHistoryMustNotBeTruncated"])
        action = next(row for row in tools["tools"] if row["id"] == "discover_new_indicators")
        self.assertEqual(action["minimumEvidenceUrls"], 1)
        self.assertEqual(action["publicationPolicyV2"]["minimumEvidenceUrls"], 0)
        profiles = equipment["equipment"]["left_audit_crystals"]["actions"]["discover_new_indicators"]
        self.assertEqual(profiles["inputPreset"]["maxItems"], 6)
        self.assertEqual(profiles["currentInputPresetV2"], {"radarPublicationVersion": 2, "maxItems": 3})
        report = next(value["indicator_scout_report"] for value in reports.values()
                      if isinstance(value, dict) and "indicator_scout_report" in value)
        self.assertEqual(report["workerOutputEnvelope"]["maximumItemsPerRun"], 6)
        self.assertEqual(report["publicationPolicyV2"]["maximumItemCount"], 3)

    def test_release_and_installer_require_portable_radar_modules_and_contracts(self):
        required = ("backend/local-runner/hq_backend/research/radar_prompt.py",
                    "backend/local-runner/hq_backend/research/radar_publication.py", *RADAR_CONTRACTS)
        installer = (ROOT / "installer/install.ps1").read_text(encoding="utf-8")
        release = (ROOT / ".github/workflows/publish-release.yml").read_text(encoding="utf-8")
        for relative in required:
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file())
                literal = '"' + relative.replace("/", "\\") + '"'
                self.assertIn(literal, installer)
                self.assertEqual(release.count(literal), 3)
                self.assertNotRegex((ROOT / relative).read_text(encoding="utf-8"), r"(?i)[A-Z]:[\\/]Users[\\/]")
        self.assertIn('"backend", "contracts", "docs", "frontend", "installer", "integrations", "runner"', installer)
        self.assertIn('git archive --format=zip', release)
        self.assertIn('".venv", "__pycache__", "node_modules"', installer)
        self.assertIn('"auth.json", "secrets.json"', installer)


class RadarFlexibleBatchIntegrationTests(unittest.TestCase):
    runtime = lifecycle.RadarBatchRepairLifecycleTests.runtime
    prime_daily_schedule = lifecycle.RadarBatchRepairLifecycleTests.prime_daily_schedule
    write_artifact = lifecycle.RadarBatchRepairLifecycleTests.write_artifact
    entries = lifecycle.RadarBatchRepairLifecycleTests.entries
    urls = staticmethod(lifecycle.RadarBatchRepairLifecycleTests.urls)
    valid_six_result = lifecycle.RadarBatchRepairLifecycleTests.valid_six_result
    make_running = lifecycle.RadarBatchRepairLifecycleTests.make_running
    quota = staticmethod(daily.RadarDailyBatchCorrectiveRetryTests.quota)
    setUp = lifecycle.RadarBatchRepairLifecycleTests.setUp

    @classmethod
    def setUpClass(cls):
        cls.bridge = lifecycle.load_module("radar_flexible_integration_bridge", lifecycle.BRIDGE_PATH)
        cls.runner = lifecycle.load_module("radar_flexible_integration_runner", lifecycle.RUNNER_PATH)

    def scheduled_radar(self):
        today = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
        slot = f"indicatorScoutSchedule:{today}:0900"
        response = self.bridge.run_dashboard_workflow_action(
            "left_audit_crystals", {"actionId": "discover_new_indicators", "form": {},
                                    "idempotencyKey": f"dashboard-schedule:{slot}"},
            trusted_trigger_source="schedule")
        self.assertIn("mission", response, response)
        return response["mission"], slot

    def v2_result(self, temp_dir, count, *, include_search=True, open_count=None):
        run_id = f"run-radar-v2-{count}"
        result = self.valid_six_result(temp_dir, final_name=f"{run_id}.final.md", run_id=run_id)
        entries = self.entries()[:count]
        urls = self.urls()[:count]
        if count >= 2:
            entries[1]["toolKind"] = "ea"
        if count >= 3:
            urls[2] = "https://github.com/example/trading-research-kit"
            entries[2].update(toolName="Research Toolkit", toolKind="tool", platform="multi_platform",
                              category="research", availability="open_source", eaReadiness="not_ea_ready",
                              sourceLimitations=["MIT license stated on the public repository"])
        for entry, url in zip(entries, urls):
            entry["sourceUrl"] = url
        result["finalMessage"] = f"Radar found {count} qualifying new entries in this bounded search."
        result["contractFields"] = [{"field": "entries", "value": json.dumps(entries, ensure_ascii=False)}]
        result["evidence"] = [{"label": f"source-{index}", "url": url, "note": "opened"}
                              for index, url in enumerate(urls)]
        final_payload = {"status": "completed", "summary": result["finalMessage"],
                         "contractFields": result["contractFields"], "evidence": result["evidence"],
                         "evidenceKinds": result["evidenceKinds"]}
        self.write_artifact(temp_dir, f"{run_id}.final.md", final_payload)
        events = ([{"type": "item.completed", "item": {"id": "search-radar-v2", "type": "web_search",
                   "action": {"type": "search", "query": "new public indicators EA and research tools"}}}]
                  if include_search else [])
        for index, url in enumerate(urls[:count if open_count is None else open_count]):
            events.append({"type": "item.completed", "item": {"id": f"open-radar-{index}", "type": "web_search",
                           "action": {"type": "open_page", "url": url}}})
        stdout = "\n".join(json.dumps(event, ensure_ascii=False) for event in events)
        path = Path(temp_dir) / result["correctiveOpenVerificationArtifact"]
        with mock.patch.object(self.runner, "CODEX_RUNS_DIR", path.parent):
            digest, child_count = self.runner.write_radar_v2_verification_manifest(
                path, run_id=run_id, structured_result=result, stdout=stdout)
        self.assertEqual(child_count, 0)
        result["correctiveOpenVerificationDigest"] = digest
        return result

    def finish_v2(self, temp_dir, count):
        mission, slot = self.scheduled_radar()
        self.prime_daily_schedule(mission, slot)
        self.assertEqual(mission["workflowContext"]["inputs"]["radarPublicationVersion"], 2)
        self.assertEqual(mission["workflowContext"]["inputs"]["maxItems"], 3)
        lease = "lease-flexible-v2"
        mission = self.make_running(mission, lease)
        result = self.v2_result(temp_dir, count)
        receipt = self.bridge._bounded_radar_corrective_open_verification_receipt(mission, result)
        self.assertTrue(receipt["valid"], receipt)
        with mock.patch.object(self.bridge, "queue_radar_publisher_image_enrichment"):
            completed = self.bridge.finish_auto_mission(mission["id"], lease, {"ok": True, "exitCode": 0, "processStarted": True}, result)
        return mission, lease, result, completed

    def test_real_runner_manifest_and_backend_finish_publish_actual_zero_to_three(self):
        for count in range(4):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                mission, lease, result, completed = self.finish_v2(temp_dir, count)
                self.assertEqual(completed["status"], "completed")
                self.assertFalse(completed["execution"]["automaticRetry"])
                self.assertNotIn("radarBatchRepair", completed)
                self.assertNotIn("correctiveOpenHourlyReservation", completed["execution"])
                self.assertEqual(len(completed["reportIds"]), 1)
                report_path = self.bridge.RUNTIME_REPORTS_DIR / f"{completed['reportIds'][0]}.json"
                report = json.loads(report_path.read_text(encoding="utf-8"))
                self.assertEqual(report["status"], "ready")
                self.assertEqual(len(report["metrics"]["entries"]), count)
                publication = report["metrics"]["workflowOutput"]["radarPublication"]
                self.assertEqual(publication["version"], 2)
                self.assertEqual(publication["itemCount"], count)
                self.assertEqual(publication["verifiedEmpty"], count == 0)
                if count == 3:
                    self.assertEqual({entry["toolKind"] for entry in report["metrics"]["entries"]}, {"indicator", "ea", "tool"})
                if count == 0:
                    self.assertFalse(self.bridge._radar_report_needs_publisher_images(report))
                model = self.bridge._radar_website_tool_read_model(
                    [report], settings=self.bridge.load_dashboard_workflow_settings(),
                    bridge={"codex": {"status": "ready"}}, missions=[completed], schedule={})
                self.assertEqual(model["today"]["itemCount"], count)
                self.assertEqual(len(model["today"]["entries"]), count)
                self.assertEqual(model["today"]["verifiedEmpty"], count == 0)
                self.assertEqual(model["today"]["verifiedReadyBatchCount"], 1)
                self.assertEqual(model["todayPublicationPolicy"]["version"], 2)
                self.assertEqual(len(self.bridge._research_sheet_radar_rows(report)), count)
                before_report = report_path.read_bytes()
                before_settings = copy.deepcopy(self.bridge.load_dashboard_workflow_settings())
                self.assertIsNone(self.bridge.finish_auto_mission(mission["id"], lease, {"processStarted": True}, result))
                self.assertEqual(report_path.read_bytes(), before_report)
                self.assertEqual(self.bridge.load_dashboard_workflow_settings(), before_settings)
                if count in (0, 2):
                    replayed, _ = self.scheduled_radar()
                    self.assertEqual(replayed["id"], completed["id"])
                    self.assertEqual(replayed["status"], "completed")
                    self.assertEqual(replayed["reportIds"], completed["reportIds"])
                    self.assertEqual(self.bridge.load_dashboard_workflow_settings(), before_settings)

    def test_actual_worker_dispatch_uses_v2_profile_and_only_one_main_quota_slot(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot)
            self.assertLessEqual(len(self.bridge._radar_worker_prompt(mission)), 8000)
            result = self.v2_result(temp_dir, 1)
            captured = []

            def fake_runner(command, **_kwargs):
                captured.append([str(item) for item in command])
                return {"ok": True, "exitCode": 0, "processStarted": True, "output": json.dumps(result, ensure_ascii=False)}

            with (mock.patch.object(self.bridge, "bridge_status", return_value={"codex": {"status": "ready"}}),
                  mock.patch.object(self.bridge, "codex_rate_limits", return_value=self.quota()),
                  mock.patch.object(self.bridge, "_collaboration_quota_gate", return_value={"allowed": True, "reason": "ready"}),
                  mock.patch.object(self.bridge, "run_safe_command", side_effect=fake_runner),
                  mock.patch.object(self.bridge, "heartbeat_auto_mission"),
                  mock.patch.object(self.bridge, "update_mission_worker_state"),
                  mock.patch.object(self.bridge, "invalidate_codex_rate_limit_cache"),
                  mock.patch.object(self.bridge, "queue_radar_publisher_image_enrichment")):
                self.bridge.process_auto_mission("worker-flexible-v2", mission)
            self.assertEqual(len(captured), 1)
            command = captured[0]
            self.assertEqual(command[command.index("--result-profile") + 1], "radar_website_tool_v2")
            self.assertNotIn("--required-open-url", command)
            stored = self.bridge.find_mission(mission["id"])
            self.assertEqual(stored["status"], "completed")
            self.assertNotIn("correctiveOpenHourlyReservation", stored["execution"])
            key = f"real:{mission['owner']}:{mission['toolId']}:{mission['modelTier']}"
            with self.bridge.RATE_LIMIT_LOCK:
                slots = self.bridge._load_persisted_rate_limits_unlocked().get(key, [])
            self.assertEqual(len(slots), 1)

    def test_four_or_six_v2_entries_are_rejected_without_silent_truncation(self):
        for count in (4, 6):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                mission, _ = self.scheduled_radar()
                result = self.v2_result(temp_dir, 3)
                entries = self.entries()[:count]
                result["contractFields"][0]["value"] = json.dumps(entries, ensure_ascii=False)
                result["evidence"] = [{"label": f"source-{i}", "url": entry["sourceUrl"], "note": "opened"}
                                      for i, entry in enumerate(entries)]
                with self.assertRaises(ValueError):
                    self.runner.require_radar_v2_contract_evidence_alignment(result)
                contract = self.bridge.validate_dashboard_workflow_output_contract(mission, result)
                self.assertFalse(contract["valid"], contract)
                self.assertEqual(len(json.loads(result["contractFields"][0]["value"])), count)

    def test_empty_result_needs_actual_search_and_nonempty_result_needs_each_main_open(self):
        for count, search, opens in ((0, False, 0), (1, False, 1), (3, True, 2)):
            with self.subTest(count=count, search=search, opens=opens), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                with self.assertRaises(ValueError):
                    self.v2_result(temp_dir, count, include_search=search, open_count=opens)

    def test_actual_legacy_six_report_remains_visible_and_unchanged_under_v2_default(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            # Historical fixture creation uses the old pre-digest inputs; signed
            # context and authorization are never edited after creation.
            with mock.patch.object(self.bridge, "_radar_current_publication_inputs", side_effect=lambda form: dict(form)):
                mission, slot = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot)
            self.assertNotIn("radarPublicationVersion", mission["workflowContext"]["inputs"])
            lease = "lease-legacy-six-history"
            mission = self.make_running(mission, lease)
            result = self.valid_six_result(temp_dir, final_name="run-legacy-six.final.md", run_id="run-legacy-six")
            with mock.patch.object(self.bridge, "queue_radar_publisher_image_enrichment"):
                completed = self.bridge.finish_auto_mission(mission["id"], lease, {"processStarted": True}, result)
            self.assertEqual(completed["status"], "completed")
            path = self.bridge.RUNTIME_REPORTS_DIR / f"{completed['reportIds'][0]}.json"
            before = path.read_bytes()
            report = json.loads(before)
            self.assertEqual(len(report["metrics"]["entries"]), 6)
            model = self.bridge._radar_website_tool_read_model(
                [report], settings=self.bridge.load_dashboard_workflow_settings(),
                bridge={"codex": {"status": "ready"}}, missions=[completed], schedule={})
            self.assertEqual(model["today"]["itemCount"], 6)
            self.assertEqual(len(model["today"]["entries"]), 6)
            self.assertEqual(model["today"]["publicationPolicy"]["version"], 1)
            self.assertEqual(path.read_bytes(), before)

    def test_verified_duplicates_publish_only_actual_new_items_without_scarcity_retry(self):
        for duplicate_count in (1, 3):
            with self.subTest(duplicate_count=duplicate_count), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                keys = {self.bridge._radar_source_key(url) for url in
                        [self.urls()[0], self.urls()[1], "https://github.com/example/trading-research-kit"][:duplicate_count]}
                with mock.patch.object(self.bridge, "_radar_existing_catalog_identities", return_value=(set(), keys)):
                    _, _, _, completed = self.finish_v2(temp_dir, 3)
                self.assertEqual(completed["status"], "completed")
                self.assertNotIn("radarBatchRepair", completed)
                self.assertFalse(completed["execution"]["automaticRetry"])
                path = self.bridge.RUNTIME_REPORTS_DIR / f"{completed['reportIds'][0]}.json"
                report = json.loads(path.read_text(encoding="utf-8"))
                actual = 3 - duplicate_count
                self.assertEqual(len(report["metrics"]["entries"]), actual)
                publication = report["metrics"]["workflowOutput"]["radarPublication"]
                self.assertEqual(publication["itemCount"], actual)
                self.assertEqual(publication["verifiedEmpty"], actual == 0)
                before = path.read_bytes()
                model = self.bridge._radar_website_tool_read_model(
                    [report], settings=self.bridge.load_dashboard_workflow_settings(),
                    bridge={"codex": {"status": "ready"}}, missions=[completed], schedule={})
                self.assertEqual(model["today"]["itemCount"], actual)
                self.assertEqual(len(model["today"]["entries"]), actual)
                self.assertEqual(model["today"]["verifiedEmpty"], actual == 0)
                self.assertEqual(model["today"]["verifiedReadyBatchCount"], 1)
                self.assertEqual(model["todayPublicationPolicy"]["version"], 2)
                self.assertEqual(path.read_bytes(), before)

    def test_ready_report_replay_rejects_tampered_mission_and_signed_input_binding(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            _, _, _, completed = self.finish_v2(temp_dir, 1)
            path = self.bridge.RUNTIME_REPORTS_DIR / f"{completed['reportIds'][0]}.json"
            before = path.read_bytes()
            report = json.loads(before)
            for tamper in ("mission_id", "input_digest", "signed_inputs"):
                with self.subTest(tamper=tamper):
                    altered = copy.deepcopy(report)
                    if tamper == "mission_id":
                        altered["linkedMissionId"] = "mission-other"
                    elif tamper == "input_digest":
                        altered["workflowContext"]["inputDigest"] = "0" * 64
                    else:
                        altered["workflowContext"]["inputs"]["focus"] = "altered after signing"
                    model = self.bridge._radar_website_tool_read_model(
                        [altered], settings=self.bridge.load_dashboard_workflow_settings(),
                        bridge={"codex": {"status": "ready"}}, missions=[completed], schedule={})
                    self.assertEqual(model["today"]["verifiedReadyBatchCount"], 0)
                    self.assertEqual(model["today"]["itemCount"], 0)
                    self.assertFalse(model["today"]["verifiedEmpty"])
            self.assertEqual(path.read_bytes(), before)

    def test_publisher_image_descriptor_keeps_verified_publication_readable(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            _, _, _, completed = self.finish_v2(temp_dir, 1)
            path = self.bridge.RUNTIME_REPORTS_DIR / f"{completed['reportIds'][0]}.json"
            before = path.read_bytes()
            report = json.loads(before)
            report["artifacts"].append({"captureKind": self.bridge.RADAR_PUBLISHER_IMAGE_KIND,
                                        "attachmentId": "image-fixture", "sourceUrl": self.urls()[0]})
            model = self.bridge._radar_website_tool_read_model(
                [report], settings=self.bridge.load_dashboard_workflow_settings(),
                bridge={"codex": {"status": "ready"}}, missions=[completed], schedule={})
            self.assertEqual(model["today"]["itemCount"], 1)
            self.assertEqual(model["today"]["verifiedReadyBatchCount"], 1)
            report["artifacts"][-1]["captureKind"] = "untrusted-extra-artifact"
            invalid = self.bridge._radar_website_tool_read_model(
                [report], settings=self.bridge.load_dashboard_workflow_settings(),
                bridge={"codex": {"status": "ready"}}, missions=[completed], schedule={})
            self.assertEqual(invalid["today"]["verifiedReadyBatchCount"], 0)
            self.assertEqual(path.read_bytes(), before)

    def test_unknown_or_malformed_publication_version_never_falls_back_to_legacy(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, _ = self.scheduled_radar()
            result = self.v2_result(temp_dir, 1)
            for version, maximum in ((99, 3), ("2", 3), (True, 3), (2, 6), (2, True), (2, "3")):
                with self.subTest(version=version, maximum=maximum):
                    altered = copy.deepcopy(mission)
                    altered["workflowContext"]["inputs"].update(radarPublicationVersion=version, maxItems=maximum)
                    self.assertTrue(self.bridge.radar_publication.invalid_policy(altered))
                    contract = self.bridge.validate_dashboard_workflow_output_contract(altered, result)
                    self.assertFalse(contract["valid"], contract)

    def test_v2_technical_failure_retries_same_reservation_then_quarantines_at_ceiling(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot)
            self.bridge._dashboard_workflow_update_schedule_state("indicatorScoutSchedule", {"requestedEnabled": True})
            original_reservation = copy.deepcopy(mission["workflowContext"]["executionReservation"])
            running = self.make_running(mission, "lease-v2-technical-failure")
            failed_result = {"ok": False, "status": "invalid_output", "workStatus": "invalid_output",
                             "finalMessage": "No verified final artifact", "contractFields": [],
                             "evidence": [], "evidenceKinds": [], "artifacts": {}, "processStarted": True,
                             "webSearchUsed": True, "webSearchEvidenceVerified": False}
            with mock.patch.object(self.bridge, "create_report") as create_report:
                retry = self.bridge.finish_auto_mission(
                    mission["id"], running["execution"]["leaseId"], {"processStarted": True}, failed_result)
            create_report.assert_not_called()
            self.assertEqual(retry["status"], "queued")
            self.assertEqual(retry["id"], mission["id"])
            self.assertEqual(retry["idempotencyKey"], mission["idempotencyKey"])
            self.assertEqual(retry["workflowContext"]["executionReservation"], original_reservation)
            self.assertEqual(retry["scheduledCompletionRetry"]["attemptCount"], 1)
            self.assertFalse(retry["scheduledCompletionRetry"]["newDailyReservation"])
            self.assertNotIn("radarBatchRepair", retry)
            for _ in range(self.bridge.SCHEDULED_RADAR_COMPLETION_RETRY_MAX_ATTEMPTS - 1):
                self.assertTrue(self.bridge._apply_scheduled_public_research_completion_retry(
                    retry, failure_code="runner_failed", failure_summary="Technical failure fixture"))
            self.bridge.replace_mission(retry)
            self.assertTrue(self.bridge._expire_prior_day_radar_mission(retry))
            stored = self.bridge.find_mission(mission["id"])
            self.assertEqual(stored["status"], "blocked")
            self.assertEqual(stored["errorCode"], "radar_retry_quarantined")
            self.assertEqual(stored["scheduledCompletionRetry"]["remainingAttempts"], 0)
            self.assertFalse(stored["scheduledCompletionRetry"]["automaticRetry"])
            self.assertEqual(stored["workflowContext"]["executionReservation"], original_reservation)
            schedule = self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]
            self.assertEqual(schedule["dailyExecutionCount"], 1)
            self.assertEqual(schedule["dailyExecutionSlotKeys"], [slot])

    def test_backend_rejects_mismatched_v2_proof_without_publishing_ready_report(self):
        for tamper in ("v1_schema", "missing_search", "wrong_run", "wrong_digest", "missing_manifest", "wrong_open_indexes"):
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                mission, _ = self.scheduled_radar()
                result = self.v2_result(temp_dir, 3)
                path = Path(temp_dir) / result["correctiveOpenVerificationArtifact"]
                manifest = json.loads(path.read_text(encoding="utf-8"))
                if tamper == "v1_schema":
                    manifest["schemaVersion"] = "metafx-radar-url-open-verification-v1"
                elif tamper == "missing_search":
                    manifest["completedSearchCount"] = 0
                    manifest["completedSearchEvents"] = []
                elif tamper == "wrong_run":
                    manifest["runId"] = "run-other"
                elif tamper == "wrong_open_indexes":
                    manifest["mainRequiredOpenIndexes"] = [0, 1]
                data = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
                path.write_bytes(data)
                result["correctiveOpenVerificationDigest"] = hashlib.sha256(data).hexdigest()
                if tamper == "wrong_digest":
                    result["correctiveOpenVerificationDigest"] = "0" * 64
                if tamper == "missing_manifest":
                    path.unlink()
                receipt = self.bridge._bounded_radar_corrective_open_verification_receipt(mission, result)
                self.assertFalse(receipt["valid"], receipt)
                contract = self.bridge.validate_dashboard_workflow_output_contract(mission, result)
                self.assertFalse(contract["valid"], contract)


if __name__ == "__main__":
    unittest.main()
