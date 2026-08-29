import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EaFactoryBridgeToolContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = json.loads(
            (ROOT / "contracts" / "bridge" / "bridge-contract.json").read_text(
                encoding="utf-8"
            )
        )
        permissions = json.loads(
            (
                ROOT
                / "contracts"
                / "tools"
                / "tool-permission-contract.json"
            ).read_text(encoding="utf-8")
        )
        cls.tools = {row["id"]: row for row in permissions["tools"]}

    def test_four_factory_control_endpoints_and_safe_download_are_declared(self):
        core_expected = {
            "GET /api/props/right_server_racks/ea-factory",
            "POST /api/props/right_server_racks/ea-factory/sources/google-sheet/sync",
            "POST /api/props/right_server_racks/ea-factory/builds",
            "POST /api/props/right_server_racks/ea-factory/builds/:buildId/advance",
        }
        download = "GET /api/props/right_server_racks/ea-factory/builds/:buildId/files/:fileId"
        declared = {
            key for key in self.bridge["endpoints"] if "right_server_racks/ea-factory" in key
        }
        self.assertEqual(declared, core_expected | {download})

        shapes = self.bridge["ea_factory"]["endpointShapes"]
        self.assertEqual(
            {f'{row["method"]} {row["path"]}' for row in shapes.values()},
            core_expected | {download},
        )
        download_shape = shapes["downloadArtifact"]
        self.assertEqual(download_shape["requestBody"], "none")
        self.assertEqual(download_shape["sideEffects"], "local_audit_only")
        self.assertFalse(download_shape["domainOrExternalSideEffects"])
        self.assertTrue(download_shape["localAuditAppended"])
        self.assertEqual(download_shape["auditMeaning"], "artifact_stream_requested")
        self.assertTrue(download_shape["sameOriginOnly"])
        self.assertTrue(download_shape["opaqueIdentifiersOnly"])
        self.assertFalse(download_shape["absoluteFilesystemPathExposed"])

    def test_factory_requests_are_exact_intent_only_and_idempotent(self):
        factory = self.bridge["ea_factory"]
        self.assertTrue(factory["networkBoundary"]["loopbackOnly"])
        self.assertEqual(factory["networkBoundary"]["allowedHost"], "127.0.0.1")
        self.assertTrue(factory["networkBoundary"]["frontendIntentOnly"])
        self.assertFalse(factory["networkBoundary"]["crossOriginRequestsAllowed"])
        self.assertEqual(factory["requestPolicy"]["unknownFields"], "reject")
        self.assertFalse(factory["requestPolicy"]["frontendMaySendSecrets"])
        self.assertFalse(factory["requestPolicy"]["frontendMaySendCredentials"])
        self.assertEqual(
            factory["requestPolicy"]["idempotency"]["sameKeyDifferentIntent"],
            "reject_conflict",
        )

        shapes = factory["endpointShapes"]
        self.assertEqual(shapes["read"]["requestBody"], "none")
        self.assertFalse(shapes["read"]["sideEffects"])
        self.assertEqual(
            shapes["syncGoogleSheet"]["allowedRequestFields"],
            ["configRevision", "idempotencyKey", "googleSheetUrlOrId", "tabName"],
        )
        self.assertEqual(
            shapes["syncGoogleSheet"]["requiredRequestFields"],
            [],
        )
        self.assertEqual(
            shapes["syncGoogleSheet"]["defaults"],
            {
                "tabName": "Deep_Research",
                "sheetSource": "mission_strategy_table_central_config",
            },
        )
        self.assertEqual(
            shapes["createBuild"]["allowedRequestFields"],
            ["sourceRecordId", "platform", "brief", "idempotencyKey"],
        )
        self.assertEqual(
            shapes["createBuild"]["requiredRequestFields"],
            ["sourceRecordId", "platform"],
        )
        self.assertEqual(
            shapes["createBuild"]["platformValues"],
            ["mt4", "mt5", "tradingview"],
        )
        self.assertEqual(shapes["createBuild"]["limits"], {"briefMaxCharacters": 900})
        self.assertEqual(
            shapes["advanceBuild"]["allowedRequestFields"],
            ["stageId", "idempotencyKey"],
        )
        self.assertEqual(
            shapes["advanceBuild"]["stageIdValues"],
            [
                "strategy_spec",
                "generate_source",
                "source_review",
                "compile_validate",
                "backtest_recheck",
                "final_report",
            ],
        )

    def test_read_model_shape_is_manual_frontend_safe_and_stable(self):
        factory = self.bridge["ea_factory"]
        self.assertEqual(factory["execution"]["mode"], "manual_stage_by_stage")
        self.assertFalse(factory["execution"]["scheduled"])
        self.assertFalse(factory["execution"]["schedulerEnabled"])
        self.assertFalse(factory["execution"]["automaticLoop"])
        self.assertTrue(factory["execution"]["oneRequestAdvancesAtMostOneStage"])

        model = factory["readModelShape"]
        self.assertEqual(model["envelopeFields"], ["ok", "eaFactory"])
        self.assertEqual(
            model["topLevelFields"],
            [
                "schemaVersion",
                "mode",
                "scheduled",
                "schedulerEnabled",
                "sourceCatalog",
                "sourceSnapshots",
                "platforms",
                "stageDefinitions",
                "builds",
                "stages",
                "currentStageId",
                "terminalSelection",
                "terminalGate",
                "endpoints",
                "safety",
                "updatedAt",
            ],
        )
        self.assertEqual(
            model["sourceCatalogFields"],
            ["sheetSchema", "records", "googleSheets"],
        )
        self.assertEqual(
            model["sourceRecordFields"],
            [
                "sourceRecordId",
                "sourceKind",
                "displayName",
                "recordId",
                "core",
                "downstream",
                "sourceUrls",
                "missingCoreFields",
                "buildReady",
                "recordDigest",
                "sourceReportId",
                "sourceMissionId",
            ],
        )
        self.assertIn("evidenceVerified", model["stageFields"])
        self.assertIn("artifacts", model["stageFields"])
        self.assertEqual(
            model["fileFields"],
            [
                "fileId",
                "fileName",
                "folder",
                "extension",
                "byteSize",
                "sha256",
                "stageId",
                "reportId",
                "artifactKind",
                "immutable",
                "downloadUrl",
            ],
        )
        self.assertIn("artifactManifestDigest", model["artifactLineageFields"])
        self.assertEqual(model["fileDigestFields"], ["fileId", "sha256"])
        self.assertIn("platform", model["terminalCandidateFields"])
        self.assertIn("adapterReady", model["terminalGateFields"])
        self.assertIn("downloadArtifactTemplate", model["endpointFields"])
        self.assertNotIn("sheetId", model["frontendForbiddenFields"])
        self.assertNotIn("rawSheetId", model["frontendForbiddenFields"])
        self.assertIn("serviceAccountKey", model["frontendForbiddenFields"])
        self.assertIn("terminalPath", model["frontendForbiddenFields"])
        self.assertIn("absolutePath", model["frontendForbiddenFields"])

    def test_factory_sheet_read_is_separate_from_write_oriented_catalog_sync(self):
        write_tool = self.tools["google_sheet_catalog_sync"]
        read_tool = self.tools["ea_factory_google_sheet_read"]

        self.assertEqual(
            write_tool["adapterStatus"],
            "implemented_backend_google_sheets_api_fail_closed",
        )
        self.assertTrue(write_tool["realExecutionAvailable"])
        self.assertFalse(write_tool["externalWriteRequiresPerReportConfirmation"])
        self.assertNotIn("right_server_racks", write_tool["linkedPropIds"])

        self.assertEqual(read_tool["linkedPropIds"], ["right_server_racks"])
        self.assertEqual(read_tool["reportType"], "trading_system_research_report")
        self.assertTrue(read_tool["realExecutionAvailable"])
        self.assertFalse(read_tool["autoRunnable"])
        self.assertFalse(read_tool["approvalRequired"])
        self.assertTrue(read_tool["requiresMission"])
        self.assertTrue(read_tool["requiresAuditLog"])
        self.assertEqual(
            read_tool["frontendIntentFields"],
            ["configRevision", "idempotencyKey"],
        )
        self.assertEqual(
            read_tool["legacyCompatibilityFields"],
            ["googleSheetUrlOrId", "tabName"],
        )
        self.assertTrue(read_tool["publicOrLinkSharedSheetsSupported"])
        self.assertTrue(read_tool["privateSheetsSupportedWhenBackendAuthConfigured"])
        self.assertFalse(read_tool["credentialsAcceptedFromFrontend"])
        self.assertFalse(read_tool["externalWriteEnabled"])
        self.assertTrue(read_tool["rawSheetIdExposed"])
        self.assertFalse(read_tool["sheetIdIsCredential"])
        self.assertFalse(read_tool["oauthSecretsExposed"])
        self.assertFalse(read_tool["scheduled"])
        self.assertFalse(read_tool["automaticLoop"])

    def test_compile_and_strategy_tester_remain_truthfully_unavailable(self):
        compile_tool = self.tools["compile_strategy_code"]
        tester_tool = self.tools["run_strategy_tester"]
        self.assertEqual(compile_tool["label"], "Compile MQL4 / MQL5")
        self.assertNotIn("Pine", compile_tool["label"])
        for tool in (compile_tool, tester_tool):
            self.assertIn("right_server_racks", tool["linkedPropIds"])
            self.assertEqual(tool["adapterStatus"], "coming_soon")
            self.assertFalse(tool["realExecutionAvailable"])
            self.assertFalse(tool["autoRunnable"])
            self.assertTrue(tool["requiresExactSelectedTerminalPlatform"])
            self.assertTrue(tool["requiresVerifiedFrontOfficeAdapter"])
            self.assertFalse(tool["terminalSelectionIsExecutionProof"])
            self.assertFalse(tool["syntheticSuccessAllowed"])
            self.assertFalse(tool["frontendMayClaimSuccess"])
            self.assertFalse(tool["liveTradingAllowed"])

        self.assertFalse(compile_tool["processExitIsCompileProof"])
        self.assertEqual(
            compile_tool["pineScriptHandling"],
            "static_source_validation_only_compile_not_applicable",
        )
        self.assertFalse(tester_tool["processExitIsBacktestProof"])
        self.assertTrue(tester_tool["requiresVisibleStrategyTesterEvidence"])
        self.assertTrue(tester_tool["requiresVisualBacktestProof"])
        self.assertFalse(tester_tool["zeroTradePassAllowed"])
        self.assertEqual(tester_tool["pineScriptHandling"], "not_applicable")


if __name__ == "__main__":
    unittest.main()
