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

    def test_pass_rows_are_bounded_and_full_counts_are_separate(self) -> None:
        results = self.report["results"]
        for field in (
            "passCount",
            "profitablePassCount",
            "returnedPassCount",
            "allPassRows",
            "allPassRowsTruncated",
            "currentBands",
            "nextParameterPlan",
            "candidateGroups",
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

    def test_equipment_action_is_plan_only_and_preserves_legacy_outputs(self) -> None:
        self.assertEqual(self.action["executionMode"], "plan_only")
        self.assertTrue(self.action["planPreparationAvailable"])
        self.assertFalse(self.action["realExecutionAvailable"])
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

    def test_dashboard_profile_is_plan_only_and_uses_same_aliases(self) -> None:
        self.assertEqual(self.profile["availability"]["execution"], "plan_only")
        policy = self.profile["executionPolicy"]
        self.assertEqual(policy["mode"], "plan_only")
        self.assertTrue(policy["planPreparationAvailable"])
        self.assertFalse(policy["realExecutionAvailable"])
        self.assertFalse(policy["frontendMayClaimExecution"])
        report_contract = self.profile["reportContract"]
        self.assertEqual(report_contract["schemaVersion"], "ea-experiment-report-v2")
        self.assertEqual(report_contract["outputAliases"], self.report["fieldAliases"])
        self.assertEqual(report_contract["allPassRowsMaxItems"], 5000)

    def test_tools_fail_closed_until_visible_strategy_tester_adapter_exists(self) -> None:
        for tool_id in (
            "prepare_backtest_plan",
            "prepare_optimization_plan",
            "prepare_ea_discovery_plan",
        ):
            tool = self.tools[tool_id]
            self.assertEqual(tool["adapterStatus"], "implemented_plan_only")
            self.assertEqual(tool["executionMode"], "plan_only")
            self.assertTrue(tool["planPreparationAvailable"])
            self.assertFalse(tool["realExecutionAvailable"])

        live = self.tools["run_optimization"]
        self.assertEqual(live["defaultMode"], "disabled_until_adapter")
        self.assertEqual(live["adapterStatus"], "coming_soon")
        self.assertFalse(live["realExecutionAvailable"])
        self.assertFalse(live["autoRunnable"])
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


if __name__ == "__main__":
    unittest.main()
