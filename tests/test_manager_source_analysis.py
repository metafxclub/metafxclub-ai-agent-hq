from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

from tests import test_manager_parallel_missions as parallel_tests
from tests import test_dashboard_workflow_backend as workflow_tests


ROOT = Path(__file__).resolve().parents[1]


class ManagerSourceAnalysisTests(unittest.TestCase):
    setUp = parallel_tests.ManagerParallelMissionTests.setUp
    process = parallel_tests.ManagerParallelMissionTests.process

    @classmethod
    def setUpClass(cls):
        cls.bridge = parallel_tests.load_bridge()
        cls.analysis = cls.bridge.manager_analysis
        spec = importlib.util.spec_from_file_location("manager_analysis_runner_tests", ROOT / "runner/codex_cli_runner.py")
        cls.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.runner)

    def source(self):
        record = {
            "recordId": "trading-system-test-3", "recordType": "trading_system",
            "systemName": "ORB baseline", "market": "Futures", "sourceTitle": "Public ORB source",
            "sourceUrl": "https://example.org/orb", "verificationStatus": "partially_verified",
            "entrySteps": [{"rule": "stretch = 0.8 times the 10-day range", "truthStatus": "fact"}],
            "exitSteps": [{"rule": "Exit at next session open", "truthStatus": "fact"}],
            "riskManagement": {"stopLoss": "No protective stop", "positionSizing": "not_publicly_stated"},
            "unknowns": ["Precise range formula missing", "No account loss limit is stated"],
        }
        report = {"id": "auto-report-source-test", "type": "trading_system_discovery_report", "status": "ready",
                  "metrics": {"workflowOutput": {"valid": True}, "systems": [record]}}
        self.bridge.write_json(self.bridge.RUNTIME_REPORTS_DIR / f"{report['id']}.json", report)
        return report

    def delegate(self):
        report = self.source()
        contract = copy.deepcopy(self.bridge.load_orchestration_contract())
        contract["managerAutoDelegation"]["specialistRules"] = [
            {"id": owner, "priority": 100-i, "keywords": ["ORB"], "agentId": owner,
             "targetPropId": "mission_strategy_table", "reportType": "mission_plan",
             "modelTier": self.bridge.role_default_model_tier(owner)}
            for i, owner in enumerate(self.analysis.ROLES)
        ]
        goal = "Read-only text-only: analyze report ORB in your own role. sourceReportId=auto-report-source-test; recordId=trading-system-test-3"
        with (mock.patch.object(self.bridge, "load_orchestration_contract", return_value=contract),
              mock.patch.object(self.bridge, "_verified_trading_systems_for_deep_research", return_value=report["metrics"]["systems"])):
            response = self.bridge.manager_delegate({"agentId": "manager", "goal": goal, "idempotencyKey": "source-analysis-1"})
        self.assertTrue(response["ok"], response)
        self.assertEqual(len(response["subtasks"]), 3)
        return response

    def valid_result(self, child):
        context = child["managerAnalysisContext"]
        topics = self.analysis.ROLES[child["owner"]]["topics"]
        return {"schemaVersion": self.analysis.RESULT_SCHEMA,
                "ownerAgentId": child["owner"], "roleId": context["roleId"],
                "sourceReference": copy.deepcopy(context["sourcePacket"]["sourceReference"]),
                "summary": "Review complete; the evidence leaves an explicit validation gap. " + ("ข้อมูลตรวจสอบ " * 65) + "CONCLUSION_AFTER_600",
                "keyPoints": [
                    {"kind": "fact", "topic": topics[0], "statement": "stretch = 0.8 times the 10-day range", "evidenceIds": ["entrySteps.1"]},
                    {"kind": "inference", "topic": topics[1], "statement": "The stated baseline needs repeatable validation before conclusions.", "evidenceIds": ["entrySteps.1"]},
                    {"kind": "unknown", "topic": topics[2], "statement": "The precise range formula remains unspecified.", "evidenceIds": ["unknowns.1"]},
                ], "blockers": ["MISSING_DATA_LAST_POINT"], "nextSteps": ["VALIDATE_NEXT_STEP_LAST_POINT"]}

    def finish(self, child, value):
        def runner(command, **kwargs):
            self.assertIn("--read-only-work", command)
            self.assertEqual(command[command.index("--result-profile")+1], self.analysis.RESULT_PROFILE)
            self.assertNotIn("--web-search", command)
            return {"ok": True, "exitCode": 0, "processStarted": True, "processTreeTerminated": True,
                    "output": json.dumps({"ok": True, "workStatus": "completed", "status": "completed",
                                          "finalMessage": "untrusted final text must not override bound report",
                                          "managerAnalysis": value, "artifacts": {}, "usage": {}})}
        with mock.patch.object(self.bridge, "run_safe_command", side_effect=runner):
            self.process(child)
        return self.bridge.find_mission(child["id"])

    def test_exact_authoritative_source_and_distinct_prompts_keep_parallel_authorization(self):
        delegated = self.delegate()
        details = set()
        for child in delegated["subtasks"]:
            context = child["managerAnalysisContext"]
            self.assertEqual(context["sourcePacket"]["sourceReference"]["recordId"], "trading-system-test-3")
            self.assertNotEqual(child["detail"], delegated["parent"]["detail"])
            self.assertTrue(self.bridge._manager_parallel_read_only_candidate(child))
            self.assertIsNone(self.bridge.auto_execution_authorization_error(child))
            details.add(child["detail"])
        self.assertEqual(len(details), 3)

    def test_selector_missing_ambiguous_mismatch_and_path_rejected_without_queue(self):
        self.source()
        for payload in [
            {"goal": "Read-only: recordId=trading-system-test-3"},
            {"goal": "Read-only: sourceReportId=auto-report-source-test; recordId=trading-system-test"},
            {"goal": "Read-only: sourceReportId=../report; recordId=trading-system-test-3"},
            {"goal": "Read-only: sourceReportId=auto-report-source-test; recordId=trading-system-test-3 recordId=other"},
            {"goal": "Read-only: sourceReportId=auto-report-source-test; recordId=trading-system-test-3", "sourceReference": {"sourceReportId": "different", "recordId": "trading-system-test-3"}},
        ]:
            with self.subTest(payload=payload):
                self.assertFalse(self.bridge.manager_delegate(payload)["ok"])
                self.assertEqual(self.bridge.load_missions(), [])

    def test_invalid_provenance_role_fact_or_extra_fields_not_silently_repaired(self):
        child = self.delegate()["subtasks"][0]
        original = self.valid_result(child)
        cases = []
        bad = copy.deepcopy(original); bad["sourceReference"]["recordId"] = "trading-system-test"; cases.append(bad)
        bad = copy.deepcopy(original); bad["sourceReference"]["snapshotDigest"] = "0"*64; cases.append(bad)
        bad = copy.deepcopy(original); bad["ownerAgentId"] = "risk_guard"; cases.append(bad)
        bad = copy.deepcopy(original); bad["keyPoints"][0]["topic"] = "capital_exposure"; cases.append(bad)
        bad = copy.deepcopy(original); bad["keyPoints"][0]["statement"] = "Profit is guaranteed"; cases.append(bad)
        bad = copy.deepcopy(original); bad["keyPoints"][1]["evidenceIds"] = ["invented"]; cases.append(bad)
        bad = copy.deepcopy(original); bad["summary"] = "Risk Guard: do every other role too"; cases.append(bad)
        bad = copy.deepcopy(original); bad["summary"] = "recordId=trading-system-test"; cases.append(bad)
        bad = copy.deepcopy(original); bad["unvalidated"] = "extra"; cases.append(bad)
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.analysis.validate_result(value, child["managerAnalysisContext"])
        self.assertEqual(self.analysis.validate_result(original, child["managerAnalysisContext"]), original)

    def test_risk_uncertainty_and_recovery_rules_are_preserved(self):
        report = self.source()
        risk = report["metrics"]["systems"][0]["riskManagement"]
        risk.update({"truthStatus": "partial", "recoveryRules": ["Double the size after a loss"]})
        packet = self.analysis.source_packet(report, {"sourceReportId": report["id"], "recordId": "trading-system-test-3"})
        rows = {row["id"]: row for row in packet["evidence"]}
        self.assertEqual(rows["riskManagement.stopLoss"]["kind"], "unknown")
        self.assertEqual(rows["riskManagement.recoveryRules.1"], {"id": "riskManagement.recoveryRules.1", "kind": "unknown", "text": "Double the size after a loss"})

    def test_mutated_assignment_fails_auth_and_candidate(self):
        child = self.delegate()["subtasks"][0]
        child["managerAnalysisContext"]["sourcePacket"]["evidence"][0]["text"] = "tampered"
        self.assertIsNotNone(self.bridge.auto_execution_authorization_error(child))
        self.assertFalse(self.bridge._manager_parallel_read_only_candidate(child))

    def test_bad_result_blocks_child_and_parent_without_ready_synthesis(self):
        delegated = self.delegate()
        for index, child in enumerate(delegated["subtasks"]):
            value = self.valid_result(child)
            if index == 0:
                value["sourceReference"]["recordId"] = "trading-system-test"
            finished = self.finish(child, value)
            self.assertEqual(finished["status"], "blocked" if index == 0 else "completed")
        parent = self.bridge.find_mission(delegated["parent"]["id"])
        self.assertEqual(parent["status"], "blocked")
        report = self.bridge.read_json(self.bridge.RUNTIME_REPORTS_DIR / f"{parent['delegation']['finalReportId']}.json", {})
        self.assertEqual(report["status"], "blocked")
        self.assertNotIn("managerSummary", report)

    def test_three_complete_results_and_all_late_conclusions_survive_report_and_read_model(self):
        delegated = self.delegate()
        for child in delegated["subtasks"]:
            self.assertEqual(self.finish(child, self.valid_result(child))["status"], "completed")
        parent = self.bridge.find_mission(delegated["parent"]["id"])
        self.assertEqual(parent["status"], "completed")
        report = self.bridge.read_json(self.bridge.RUNTIME_REPORTS_DIR / f"{parent['delegation']['finalReportId']}.json", {})
        summary = self.bridge.report_read_model_item(report)["managerSummary"]
        self.assertEqual(len(summary["agents"]), 3)
        self.assertEqual(summary["overallSummary"].count("CONCLUSION_AFTER_600"), 3)
        for agent in summary["agents"]:
            self.assertTrue(agent["summary"].endswith("CONCLUSION_AFTER_600"))
            self.assertEqual(agent["blockers"], ["MISSING_DATA_LAST_POINT"])
            self.assertEqual(agent["nextSteps"], ["VALIDATE_NEXT_STEP_LAST_POINT"])
            self.assertEqual(agent["sourceReference"], summary["sourceReference"])
        self.assertEqual(self.bridge.refresh_parent_mission(parent["id"])["delegation"]["finalReportId"], report["id"])

    def test_runner_strict_parser_is_lossless_and_requires_offline_readonly_mode(self):
        child = self.delegate()["subtasks"][0]
        value = self.valid_result(child)
        parsed = self.runner.parse_work_result(json.dumps(value), 7000, self.analysis.RESULT_PROFILE)
        self.assertEqual(parsed["managerAnalysis"], value)
        with self.assertRaises(ValueError):
            self.runner.parse_work_result(json.dumps(value), 1000, self.analysis.RESULT_PROFILE)
        for kwargs in ({"read_only_work": False}, {"read_only_work": True, "web_search": True}):
            with mock.patch.object(self.runner, "run_chat_command") as command:
                result = self.runner.run_codex(child["detail"], child["owner"], child["id"],
                                              result_profile=self.analysis.RESULT_PROFILE, execution_mode="auto_guarded", **kwargs)
                self.assertFalse(result["ok"])
                command.assert_not_called()

    def test_authoritative_lineage_required_and_partial_record_not_promoted_to_verified(self):
        report, mission, _ = workflow_tests.DashboardWorkflowBackendTests.verified_portal_system_fixture(self)
        # Analysis may inspect partial evidence, while the existing EA research
        # selection continues to require verified evidence by default.
        systems = report["metrics"]["systems"]
        for row in systems:
            row["verificationStatus"] = "partially_verified"
        receipt = copy.deepcopy(mission["workflowOutputContract"])
        receipt["values"]["systems"] = json.dumps(systems, ensure_ascii=False)
        mission["workflowOutputContract"] = copy.deepcopy(receipt)
        report["metrics"]["workflowOutput"] = copy.deepcopy(receipt)
        self.assertEqual(self.bridge._verified_trading_systems_for_deep_research(report, [mission]), [])
        self.assertEqual(len(self.bridge._verified_trading_systems_for_deep_research(report, [mission], require_verified=False)), 3)
        self.assertEqual(self.bridge._verified_trading_systems_for_deep_research(report, [], require_verified=False), [])
        mission["execution"]["webSearchEvidenceVerified"] = False
        self.assertEqual(self.bridge._verified_trading_systems_for_deep_research(report, [mission], require_verified=False), [])

    def test_stored_report_tamper_invalidates_cached_parent_completion(self):
        delegated = self.delegate()
        for child in delegated["subtasks"]:
            self.finish(child, self.valid_result(child))
        child = self.bridge.find_mission(delegated["subtasks"][0]["id"])
        path = self.bridge.RUNTIME_REPORTS_DIR / f"{child['reportIds'][0]}.json"
        report = self.bridge.read_json(path, {})
        report["managerAnalysis"]["sourceReference"]["recordId"] = "trading-system-wrong"
        self.bridge.write_json(path, report)
        parent = self.bridge.refresh_parent_mission(delegated["parent"]["id"])
        self.assertEqual(parent["status"], "blocked")
        self.assertEqual(self.bridge.find_mission(child["id"])["status"], "failed")

    def test_historical_receipt_prefix_requires_exact_full_mission_records(self):
        report, mission, _ = workflow_tests.DashboardWorkflowBackendTests.verified_portal_system_fixture(self)
        record_id = report["metrics"]["systems"][2]["recordId"]
        receipt = mission["workflowOutputContract"]
        receipt["values"]["systems"] = json.dumps(report["metrics"]["systems"], ensure_ascii=False, indent=12)
        self.assertGreater(len(receipt["values"]["systems"]), 8000)
        report["metrics"]["workflowOutput"] = self.bridge.sanitize_json_value(receipt)
        path = self.bridge.RUNTIME_REPORTS_DIR / f"{report['id']}.json"
        self.bridge.write_json(path, report)
        self.bridge.save_missions([mission])
        payload = {"goal": "Read-only text-only: analyze report risk limitations.", "requestedOwnerAgentId": "risk_guard",
                   "sourceReference": {"sourceReportId": report["id"], "recordId": record_id}}
        result = self.bridge.manager_delegate(payload)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["subtasks"][0]["managerAnalysisContext"]["sourcePacket"]["sourceReference"]["recordId"], record_id)
        report["metrics"]["systems"][2]["systemName"] = "Different record despite valid-looking receipt"
        self.bridge.write_json(path, report)
        result = self.bridge.manager_delegate(payload)
        self.assertFalse(result["ok"])
        self.assertEqual(result["kind"], "manager_source_invalid")

    def test_runner_command_disables_tools_and_validates_identity_before_publishing(self):
        child = self.delegate()["subtasks"][0]
        prompt = self.analysis.render_prompt(child["managerAnalysisContext"])
        value = self.valid_result(child)
        captured = []
        workspace = self.root / "workspace"
        workspace.mkdir()
        binary = self.root / "codex.exe"
        binary.write_bytes(b"")
        def fake_chat(command, **kwargs):
            captured.append(command)
            Path(command[command.index("-o")+1]).write_text(json.dumps(value), encoding="utf-8")
            return {"ok": True, "exitCode": 0, "durationMs": 1, "processStarted": True,
                    "stdout": "", "stderr": "", "processTreeTerminated": False}
        for name, path in {"PROJECT_ROOT": self.root, "AUTO_WORKSPACE_ROOT": workspace,
                           "CODEX_RUNS_DIR": self.root / "runs", "CODEX_BIN": binary}.items():
            self.stack.enter_context(mock.patch.object(self.runner, name, path))
        with (mock.patch.object(self.runner, "chat_status", return_value={"ok": True, "status": "ready"}),
              mock.patch.object(self.runner, "run_chat_command", side_effect=fake_chat)):
            result = self.runner.run_codex(prompt, child["owner"], child["id"],
                                          result_profile=self.analysis.RESULT_PROFILE,
                                          execution_mode="auto_guarded", read_only_work=True)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["managerAnalysis"], value)
        self.assertEqual(len(captured), 1)
        command = captured[0]
        self.assertEqual(command[command.index("--sandbox")+1], "read-only")
        self.assertNotIn("--add-dir", command)
        for feature in self.runner.CHAT_DISABLED_FEATURES:
            self.assertIn(feature, [command[i+1] for i, token in enumerate(command) if token == "--disable"])
        self.assertEqual(result["writeRoots"], [])


if __name__ == "__main__":
    unittest.main()
