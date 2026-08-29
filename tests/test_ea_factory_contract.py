import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EaFactoryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(
            (ROOT / "contracts" / "workflows" / "ea-factory-contract.json").read_text(
                encoding="utf-8"
            )
        )
        cls.connections = json.loads(
            (
                ROOT
                / "contracts"
                / "connections"
                / "dashboard-connection-contract.json"
            ).read_text(encoding="utf-8")
        )
        cls.plugin_map = json.loads(
            (
                ROOT
                / "contracts"
                / "workflows"
                / "equipment-plugin-map.json"
            ).read_text(encoding="utf-8")
        )

    def test_factory_is_manual_and_never_scheduled(self):
        self.assertEqual(self.contract["mode"], "manual_stage_by_stage")
        self.assertFalse(self.contract["scheduled"])
        self.assertFalse(self.contract["automaticLoop"])
        self.assertTrue(self.contract["oneUserActionAdvancesOneStage"])
        self.assertEqual(self.contract["requestLimits"]["createBuildBriefMaxCharacters"], 900)

    def test_deep_research_source_maps_to_exact_internal_twenty_three_fields(self):
        source = self.contract["sourceContract"]
        columns = source["columns"]
        google_sheet = source["googleSheets"]
        self.assertEqual(google_sheet["tabName"], "Deep_Research")
        self.assertEqual(google_sheet["sharedConsumerPropId"], "left_server_racks")
        self.assertEqual(
            google_sheet["sourceRangeRequired"],
            "A-AW (49 required headers; extra columns allowed)",
        )
        self.assertEqual(google_sheet["internalMapping"], "23 EA strategy fields (not a Sheet range)")
        self.assertEqual(source["columnRange"], "A-W")
        self.assertEqual(source["columnRangeSemantics"], "internal_normalized_fields_not_google_sheet_range")
        self.assertEqual(source["coreColumns"], "A-M")
        self.assertEqual(source["downstreamColumns"], "N-W")
        self.assertEqual([row["column"] for row in columns], list("ABCDEFGHIJKLMNOPQRSTUVW"))
        self.assertEqual(len(columns), 23)
        self.assertTrue(all(row["group"] == "core" for row in columns[:13]))
        self.assertTrue(all(row["group"] == "downstream" for row in columns[13:]))
        self.assertEqual(columns[5]["id"], "entry_rules")
        self.assertEqual(columns[6]["id"], "exit_rules")
        self.assertEqual(columns[9]["id"], "recovery")
        self.assertEqual(columns[10]["id"], "lot_risk")

    def test_stage_order_and_pine_branch_are_explicit(self):
        stages = self.contract["stages"]
        self.assertEqual(
            [row["id"] for row in stages],
            [
                "strategy_spec",
                "generate_source",
                "source_review",
                "compile_validate",
                "backtest_recheck",
                "final_report",
            ],
        )
        self.assertEqual(stages[4]["notApplicablePlatforms"], ["tradingview"])
        self.assertFalse(self.contract["platforms"]["tradingview"]["terminalRequired"])
        self.assertFalse(self.contract["platforms"]["tradingview"]["backtestRequired"])

    def test_workspace_and_security_are_fail_closed(self):
        workspace = self.contract["workspace"]
        self.assertEqual(workspace["root"], "workspace/ea-factory/<buildId>")
        self.assertEqual(
            workspace["folders"],
            ["Source", "EA_Versions", "Reports", "Sets", "Screenshots", "Summaries"],
        )
        self.assertTrue(workspace["immutableVersions"])
        self.assertFalse(workspace["frontendReceivesAbsolutePaths"])
        security = self.contract["security"]
        self.assertTrue(security["frontendIntentOnly"])
        self.assertFalse(security["credentialsAcceptedFromFrontend"])
        self.assertFalse(security["liveTradingAllowed"])
        self.assertTrue(security["terminalPlatformMustMatch"])
        self.assertTrue(security["backtestCannotBeInferredWithoutVisualProof"])

    def test_artifacts_are_manifest_bound_and_download_route_is_canonical(self):
        artifacts = self.contract["artifactReadModel"]
        self.assertEqual(artifacts["sourceOfTruth"], "persisted_artifact_manifest_only")
        self.assertTrue(artifacts["downloadRequiresDigestAndLineageMatch"])
        self.assertFalse(artifacts["absoluteFilesystemPathExposed"])
        self.assertIn("fileId", artifacts["fields"])
        self.assertIn("sha256", artifacts["fields"])
        self.assertIn("stageId", artifacts["fields"])
        self.assertIn("reportId", artifacts["fields"])
        self.assertIn("downloadUrl", artifacts["frontendSafeFields"])
        self.assertNotIn("relativePath", artifacts["frontendSafeFields"])
        self.assertEqual(
            self.contract["api"]["downloadArtifact"],
            "GET /api/props/right_server_racks/ea-factory/builds/:buildId/files/:fileId",
        )

    def test_dashboard_tabs_match_factory_journey(self):
        profile = self.connections["profiles"]["right_server_racks"]
        self.assertEqual(
            [row["id"] for row in profile["localTabs"]],
            [
                "source",
                "strategy_spec",
                "generate_source",
                "source_review",
                "compile_validate",
                "backtest_recheck",
                "final_report",
            ],
        )
        self.assertEqual(profile["operation"]["defaultMode"], "manual_stage_by_stage")
        self.assertFalse(profile["operation"]["scheduled"])
        self.assertFalse(profile["operation"]["automaticLoop"])

    def test_runner_output_contract_carries_factory_integrity_bindings(self):
        actions = self.plugin_map["equipment"]["right_server_racks"]["actions"]
        generation_fields = set(actions["build_strategy_code"]["outputFields"])
        review_fields = set(actions["review_source_code"]["outputFields"])
        binding_fields = {"sourceRecordDigest", "strategySpecDigest", "platform"}
        self.assertTrue(binding_fields.issubset(generation_fields))
        self.assertTrue(binding_fields.issubset(review_fields))
        self.assertIn("strategyCoverage", review_fields)


if __name__ == "__main__":
    unittest.main()
