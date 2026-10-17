from __future__ import annotations

import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict:
    return json.loads((PROJECT_ROOT / relative_path).read_text(encoding="utf-8"))


class EaOptimizationLabContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reports = load_json("contracts/reports/report-contract.json")
        cls.equipment = load_json("contracts/workflows/equipment-plugin-map.json")
        cls.connections = load_json(
            "contracts/connections/dashboard-connection-contract.json"
        )
        cls.permissions = load_json("contracts/tools/tool-permission-contract.json")
        cls.bridge = load_json("contracts/bridge/bridge-contract.json")
        cls.report = cls.reports["typed_report_schemas"]["ea_experiment_report"]
        cls.action = cls.equipment["equipment"]["right_tool_console"]["actions"][
            "prepare_optimization_plan"
        ]
        cls.profile = cls.connections["profiles"]["right_tool_console"]
        cls.tools = {
            item["id"]: item
            for item in cls.permissions["tools"]
            if isinstance(item, dict) and item.get("id")
        }
        cls.bridge_lab = cls.bridge["ea_optimization_lab"]

    def test_v2_report_keeps_v1_and_legacy_aliases(self) -> None:
        self.assertEqual(self.report["schemaVersion"], "ea-experiment-report-v2")
        self.assertIn(
            "ea-experiment-report-v1",
            self.report["backwardCompatibleSchemaVersions"],
        )
        self.assertEqual(
            self.report["fieldAliases"],
            {
                "terminalCandidateId": "terminalId",
                "totalPasses": "passCount",
                "passes": "allPassRows",
                "parameterBands": "currentBands",
                "nextRanges": "nextParameterPlan",
                "candidates": "candidateGroups",
            },
        )
        self.assertIn("parameterRanges", self.report["plan"])
        self.assertIn("riskThresholds", self.report["plan"])
        self.assertIn("overfitWarnings", self.report["results"])

    def test_v2_report_has_round_identity_tester_settings_and_warnings(self) -> None:
        for field in ("runId", "roundId", "platform", "terminalId"):
            self.assertIn(field, self.report)
        settings = self.report["testerSettings"]
        for field in (
            "eaName",
            "eaVersion",
            "eaArtifactId",
            "eaSha256",
            "symbol",
            "timeframe",
            "testModel",
            "spread",
            "useDate",
            "dateRange",
            "deposit",
            "currency",
            "optimizationEnabled",
            "inputRangesSha256",
            "testShutdownTerminal",
        ):
            self.assertIn(field, settings)
        self.assertFalse(settings["testShutdownTerminal"])
        self.assertIn("warnings", self.report["results"])

    def test_execution_evidence_requires_visible_tester_and_hashed_artifacts(self) -> None:
        evidence = self.report["executionEvidence"]
        self.assertFalse(evidence["visibleTester"]["verified"])
        self.assertFalse(evidence["mtExecutionVerified"])
        self.assertFalse(evidence["optimizationProofVerified"])
        self.assertIn("sha256", evidence["resultReport"])
        self.assertIn("sha256", evidence["artifactManifest"])
        for field in ("runId", "roundId", "platform", "terminalId"):
            self.assertIn(field, evidence)

        base = self.reports["base_report_schema"]["executionEvidence"]
        for field in (
            "runId",
            "roundId",
            "platform",
            "terminalId",
            "terminalCandidateId",
            "visibleTester",
            "resultReport",
            "artifactManifest",
            "mtExecutionVerified",
            "optimizationProofVerified",
        ):
            self.assertIn(field, base)

        session = self.report["optimizationSession"]
        self.assertEqual(session["schemaVersion"], 1)
        self.assertIn("awaiting_visible_terminal", session["state"])
        self.assertIn("collecting", session["state"])
        self.assertTrue(session["oneActiveSessionAtATime"])
        self.assertTrue(session["durableRestartRecovery"])
        self.assertTrue(session["noDoubleStart"])
        self.assertFalse(session["liveTradingAllowed"])
        self.assertFalse(session["testShutdownTerminal"])

    def test_pass_rows_are_bounded_and_full_counts_are_separate(self) -> None:
        results = self.report["results"]
        for field in (
            "passCount",
            "profitablePassCount",
            "eligiblePassCount",
            "returnedPassCount",
            "storedPassRowCount",
            "allPassRowsSha256",
            "allPassRows",
            "allPassRowsTruncated",
            "currentBands",
            "nextParameterPlan",
            "candidateGroups",
            "analysisStatus",
            "analysisSha256",
            "analysisSourceRowsSha256",
            "riskThresholds",
            "nextParameterPlanAvailable",
            "nextParameterPlanReasonCode",
        ):
            self.assertIn(field, results)
        policy = results["allPassRowsPolicy"]
        self.assertGreater(policy["maxItems"], 0)
        self.assertLessEqual(policy["maxItems"], 5000)
        self.assertIn("hashed_artifact", policy["overflow"])
        self.assertIn("returnedPassCount", policy["completenessRule"])
        self.assertEqual(
            set(results["candidateGroups"]),
            {"maxProfit", "lowestDrawdown", "mostStable"},
        )
        self.assertEqual(policy["maxItems"], 100)

    def test_bridge_completion_contract_exposes_bound_backend_analysis(self) -> None:
        completion = self.bridge_lab["completionEvidence"]
        self.assertTrue(completion["initialDepositFromResolvedTesterSettingsRequired"])
        self.assertTrue(completion["immutableDeterministicAnalysisRequired"])
        self.assertTrue(completion["analysisBoundToExactSessionRoundAndResultRowsSha256"])
        self.assertTrue(completion["analysisUnavailableWhenVerifiedRowsIncomplete"])
        read_model = self.bridge_lab["readModelShape"]
        self.assertEqual(
            read_model["evidenceAnalysisFields"],
            ["analysis", "analysisSha256", "initialDeposit"],
        )
        for field in (
            "riskThresholds",
            "profitablePassCount",
            "eligiblePassCount",
            "candidateGroups",
            "nextParameterPlan",
        ):
            self.assertIn(field, read_model["analysisFields"])

    def test_equipment_action_runs_mt5_session_and_preserves_legacy_outputs(self) -> None:
        self.assertEqual(
            self.action["executionMode"],
            "backend_authoritative_mt5_visible_session",
        )
        self.assertTrue(self.action["planPreparationAvailable"])
        self.assertTrue(self.action["realExecutionAvailable"])
        self.assertEqual(self.action["realExecutionPlatforms"], ["mt5"])
        self.assertEqual(self.action["planOnlyPlatforms"], ["mt4"])
        self.assertEqual(
            self.action["inputPreset"]["validationMethod"],
            "single_verified_run",
        )
        self.assertFalse(self.action["frontendFilesystemPathsAllowed"])
        self.assertFalse(self.action["frontendEvidenceClaimsAllowed"])
        self.assertTrue(self.action["oneActiveSessionAtATime"])
        self.assertTrue(self.action["durableRestartRecovery"])
        self.assertTrue(self.action["noDoubleStart"])
        self.assertFalse(self.action["testShutdownTerminalAllowed"])
        self.assertFalse(self.action["liveTradingAllowed"])
        self.assertEqual(self.action["reportContractVersion"], "ea-experiment-report-v2")
        legacy_fields = {
            "parameterRanges",
            "startStepStop",
            "selectionCriteria",
            "overfitGuards",
            "validationSplit",
            "candidateGroups",
            "nextRanges",
        }
        self.assertTrue(legacy_fields.issubset(set(self.action["outputFields"])))
        canonical_fields = {
            "runId",
            "roundId",
            "platform",
            "terminalId",
            "testerSettings",
            "warnings",
            "executionEvidence",
            "passCount",
            "profitablePassCount",
            "allPassRows",
            "currentBands",
            "nextParameterPlan",
            "candidateGroups",
        }
        self.assertTrue(
            canonical_fields.issubset(set(self.action["optionalResultFieldsV2"]))
        )
        self.assertEqual(self.action["outputAliases"], self.report["fieldAliases"])
        self.assertEqual(self.action["resultBounds"]["allPassRowsMaxItems"], 5000)

    def test_dashboard_profile_exposes_guarded_mt5_session_and_same_aliases(self) -> None:
        self.assertEqual(
            self.profile["availability"]["execution"],
            "mt5_visible_optimization_session_fail_closed",
        )
        policy = self.profile["executionPolicy"]
        self.assertEqual(policy["mode"], "backend_authoritative_mt5_visible_session")
        self.assertTrue(policy["planPreparationAvailable"])
        self.assertTrue(policy["realExecutionAvailable"])
        self.assertEqual(policy["realExecutionPlatforms"], ["mt5"])
        self.assertEqual(policy["planOnlyPlatforms"], ["mt4"])
        self.assertFalse(policy["frontendMayClaimExecution"])
        self.assertTrue(policy["oneActiveSessionAtATime"])
        self.assertTrue(policy["durableRestartRecovery"])
        self.assertTrue(policy["noDoubleStart"])
        self.assertFalse(policy["testShutdownTerminalAllowed"])
        self.assertFalse(policy["liveTradingAllowed"])
        report_contract = self.profile["reportContract"]
        self.assertEqual(report_contract["schemaVersion"], "ea-experiment-report-v2")
        self.assertEqual(report_contract["outputAliases"], self.report["fieldAliases"])
        self.assertEqual(report_contract["allPassRowsMaxItems"], 5000)

    def test_unimplemented_lab_tools_remain_plan_only(self) -> None:
        for tool_id in (
            "prepare_backtest_plan",
            "prepare_ea_discovery_plan",
        ):
            tool = self.tools[tool_id]
            self.assertEqual(tool["adapterStatus"], "implemented_plan_only")
            self.assertEqual(tool["executionMode"], "plan_only")
            self.assertTrue(tool["planPreparationAvailable"])
            self.assertFalse(tool["realExecutionAvailable"])

    def test_mt5_optimization_tools_are_real_but_backend_authoritative(self) -> None:
        prepared = self.tools["prepare_optimization_plan"]
        self.assertEqual(
            prepared["executionMode"],
            "backend_authoritative_mt5_visible_session",
        )
        self.assertEqual(prepared["adapterStatus"], "implemented_mt5_visible_fail_closed")
        self.assertTrue(prepared["realExecutionAvailable"])
        self.assertEqual(prepared["realExecutionPlatforms"], ["mt5"])
        self.assertEqual(prepared["planOnlyPlatforms"], ["mt4"])
        self.assertFalse(prepared["frontendMaySendFilesystemPaths"])
        self.assertFalse(prepared["frontendMaySendDigestsOrTerminalBindings"])
        self.assertFalse(prepared["frontendMayClaimSuccess"])

        live = self.tools["run_optimization"]
        self.assertEqual(live["label"], "รัน Auto Optimization จริงบน MT5")
        self.assertEqual(live["defaultMode"], "backend_authoritative_mt5_visible_session")
        self.assertEqual(live["adapterStatus"], "implemented_mt5_visible_fail_closed")
        self.assertTrue(live["realExecutionAvailable"])
        self.assertTrue(live["autoRunnable"])
        self.assertEqual(live["supportedTargets"], ["mt5"])
        self.assertEqual(live["planOnlyTargets"], ["mt4"])
        self.assertFalse(live["frontendMayClaimSuccess"])
        self.assertFalse(live["syntheticSuccessAllowed"])
        self.assertFalse(live["testShutdownTerminalAllowed"])
        for guard in (
            "requiresExactSelectedTerminalPlatform",
            "requiresVerifiedFrontOfficeAdapter",
            "requiresVisibleStrategyTesterEvidence",
            "requiresOptimizationProof",
            "requiresRunAndRoundIdentity",
            "requiresSelectedTerminalId",
            "requiresResultReportSha256",
            "requiresArtifactManifestSha256",
            "requiresPassCountsFromVerifiedTester",
        ):
            self.assertTrue(live[guard], guard)
        self.assertEqual(live["allPassRowsMaxItems"], 5000)
        self.assertTrue(live["oneActiveSessionAtATime"])
        self.assertTrue(live["durableRestartRecovery"])
        self.assertTrue(live["noDoubleStart"])
        self.assertFalse(live["frontendMaySendFilesystemPaths"])
        self.assertFalse(live["frontendMaySendDigestsOrTerminalBindings"])

        optimization_tab = next(
            tab for tab in self.profile["localTabs"] if tab["id"] == "optimization"
        )
        self.assertEqual(
            optimization_tab["labelTh"],
            "MT5 Run • MT4 Plan",
        )

    def test_bridge_contract_declares_exact_mt5_session_boundary(self) -> None:
        lab = self.bridge_lab
        self.assertEqual(lab["schemaVersion"], "ea-optimization-lab-v1")
        self.assertEqual(lab["supportedRealExecutionPlatforms"], ["mt5"])
        self.assertEqual(lab["planOnlyPlatforms"], ["mt4"])
        self.assertTrue(lab["networkBoundary"]["loopbackOnly"])
        execution = lab["execution"]
        self.assertTrue(execution["backendAuthoritative"])
        self.assertTrue(execution["oneActiveSessionAtATime"])
        self.assertTrue(execution["durableRestartRecovery"])
        self.assertTrue(execution["noDoubleStart"])
        self.assertFalse(execution["terminalProcessLaunchAllowed"])
        self.assertFalse(execution["testShutdownTerminalAllowed"])
        self.assertFalse(execution["liveTradingAllowed"])

        policy = lab["requestPolicy"]
        self.assertEqual(policy["unknownFields"], "reject")
        self.assertFalse(policy["frontendMaySendFilesystemPaths"])
        self.assertFalse(policy["frontendMaySendCredentials"])
        self.assertFalse(policy["frontendMaySendDigestsOrTerminalBindings"])
        self.assertFalse(policy["frontendMayClaimEvidenceOrSuccess"])
        self.assertTrue(policy["strictIdempotency"])
        self.assertTrue(
            set(policy["browserIntentFields"]).isdisjoint(
                policy["backendResolvedFields"]
            )
        )

        expected = {
            "GET /api/ea-optimization-lab",
            "POST /api/ea-optimization-lab/sessions",
            "POST /api/ea-optimization-lab/sessions/:sessionId/resume",
            "POST /api/ea-optimization-lab/sessions/:sessionId/cancel",
        }
        self.assertEqual(
            {
                f'{shape["method"]} {shape["path"]}'
                for shape in lab["endpointShapes"].values()
            },
            expected,
        )
        for action in ("resumeSession", "cancelSession"):
            shape = lab["endpointShapes"][action]
            self.assertEqual(shape["allowedRequestFields"], ["idempotencyKey"])
            self.assertEqual(shape["requiredRequestFields"], [])
        self.assertTrue(expected.issubset(set(self.bridge["endpoints"])))
        completion = lab["completionEvidence"]
        self.assertTrue(completion["matchingSessionRoundOperationReceiptRequired"])
        self.assertTrue(completion["visibleTesterEvidenceSha256Required"])
        self.assertTrue(completion["resultReportSha256Required"])
        self.assertTrue(completion["artifactManifestSha256Required"])
        self.assertFalse(completion["syntheticSuccessAllowed"])


if __name__ == "__main__":
    unittest.main()
