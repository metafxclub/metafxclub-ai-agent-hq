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
        cls.report_contract = json.loads(
            (ROOT / "contracts" / "reports" / "report-contract.json").read_text(
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

    def test_factory_has_one_click_coordinator_and_manual_recovery(self):
        self.assertEqual(self.contract["mode"], "one_click_with_manual_stage_recovery")
        self.assertFalse(self.contract["scheduled"])
        self.assertTrue(self.contract["automaticLoop"])
        self.assertFalse(self.contract["oneUserActionAdvancesOneStage"])
        self.assertTrue(self.contract["oneUserClickAdvancesVerifiedStageChain"])
        self.assertTrue(
            self.contract["oneCoordinatorIterationAdvancesAtMostOneStage"]
        )
        one_click = self.contract["oneClick"]
        self.assertEqual(
            one_click["endpoint"],
            "POST /api/props/right_server_racks/ea-factory/builds/:buildId/run",
        )
        self.assertEqual(one_click["requestFields"], ["idempotencyKey"])
        self.assertFalse(one_click["phaseGateBypassAllowed"])
        self.assertTrue(one_click["visibleMetaEditorRequired"])
        self.assertTrue(one_click["visibleStrategyTesterRequired"])
        self.assertEqual(one_click["supportedVisiblePlatforms"], ["mt4"])
        self.assertEqual(
            one_click["unsupportedVisiblePlatforms"]["mt5"],
            "manual_stage_by_stage_only_until_verified_visible_adapter_exists",
        )
        self.assertTrue(one_click["selectedTerminalMustAlreadyBeRunning"])
        self.assertFalse(one_click["terminalProcessLaunchAllowed"])
        self.assertTrue(one_click["visualModeRequired"])
        self.assertFalse(one_click["liveTradingAllowed"])
        result_contract = one_click["visibleStageResultContract"]
        self.assertTrue(result_contract["persistSuccessOnlyAfterEvidenceValidation"])
        self.assertEqual(
            result_contract["compileArtifactAliases"],
            ["compiled_binary", "visible_window", "compile_log", "adapter_receipt"],
        )
        self.assertEqual(
            result_contract["backtestArtifactAliases"],
            [
                "tester_settings",
                "tester_input_preset",
                "tester_input_preset_set",
                "tester_input_readback_set",
                "tester_result",
                "tester_report_proof",
                "tester_report",
                "adapter_receipt",
            ],
        )
        self.assertFalse(one_click["testerPolicy"]["zeroTradeIsSuccess"])
        self.assertTrue(one_click["testerPolicy"]["zeroTradeExecutionIsCompleted"])
        self.assertTrue(one_click["testerPolicy"]["zeroTradeRequiresAttention"])
        self.assertFalse(
            one_click["testerPolicy"]["zeroTradePerformanceEvaluationAllowed"]
        )
        self.assertTrue(one_click["testerPolicy"]["mismatchedChartErrorsParsed"])
        self.assertTrue(
            one_click["testerPolicy"]["historyQualityErrorExecutionIsCompleted"]
        )
        self.assertTrue(
            one_click["testerPolicy"]["historyQualityErrorRequiresAttention"]
        )
        self.assertFalse(
            one_click["testerPolicy"][
                "historyQualityErrorPerformanceEvaluationAllowed"
            ]
        )
        self.assertTrue(
            one_click["testerPolicy"]["combinedAttentionReasonDeterministic"]
        )
        self.assertFalse(one_click["testerPolicy"]["shutdownTerminalAfterTest"])
        preset = one_click["testerPolicy"]["canSlimExternalFactsSimulation"]
        self.assertEqual(preset["scope"], "mt4_strategy_tester_only")
        self.assertTrue(preset["visibleExpertPropertiesInputsRequired"])
        self.assertTrue(preset["savedSetReadbackRequired"])
        self.assertTrue(preset["fullCertifiedInputSnapshotRequired"])
        self.assertEqual(preset["certifiedInputCount"], 13)
        self.assertEqual(len(preset["certifiedInputNames"]), 13)
        self.assertIn("MaxSpreadPoints", preset["certifiedInputNames"])
        self.assertFalse(preset["staleTesterInputInheritanceAllowed"])
        self.assertTrue(preset["testerReportParametersMatchRequired"])
        self.assertEqual(
            preset["savedSetOptimizationMetadataSuffixAllowlist"],
            ["F", "1", "2", "3"],
        )
        self.assertTrue(preset["digestBoundToExactSource"])
        self.assertFalse(preset["appliedToLiveChart"])
        generic = one_click["testerPolicy"]["mt4ExactSourceInputReset"]
        self.assertEqual(
            generic["scope"],
            "every_mt4_expert_advisor_strategy_tester_run",
        )
        self.assertEqual(generic["supportedScalarTypes"], ["bool", "int", "double"])
        self.assertEqual(generic["maximumInputCount"], 64)
        self.assertTrue(generic["fullExactSourceInputSnapshotRequiredWhenInputsExist"])
        self.assertTrue(generic["resetEverySupportedInputToSourceLiteralDefault"])
        self.assertTrue(generic["unsupportedInputContractBlocksBeforeVisibleUi"])
        simulation = generic["historicalBoolSimulation"]
        self.assertTrue(simulation["directIndividualFailClosedReturnGuardRequired"])
        self.assertFalse(simulation["liveOrSafetySwitchSimulationAllowed"])
        self.assertIn("External", simulation["inputNameMustContainAny"])
        self.assertEqual(
            self.contract["api"]["runBuild"],
            "POST /api/props/right_server_racks/ea-factory/builds/:buildId/run",
        )
        self.assertEqual(self.contract["requestLimits"]["createBuildBriefMaxCharacters"], 900)

    def test_artifact_kind_contract_defaults_to_ea_and_bounds_custom_indicator(self):
        kinds = self.contract["artifactKinds"]
        self.assertEqual(kinds["default"], "expert_advisor")
        self.assertEqual(
            kinds["allowed"],
            ["expert_advisor", "custom_indicator"],
        )
        indicator = kinds["custom_indicator"]
        self.assertEqual(indicator["platforms"], ["mt4", "mt5"])
        self.assertEqual(indicator["requiredEntryPoint"], "OnCalculate")
        self.assertTrue(indicator["indicatorBufferRequired"])
        self.assertFalse(indicator["tradingFunctionsAllowed"])
        self.assertTrue(indicator["compileStageRequired"])
        self.assertFalse(indicator["backtestApplicable"])
        self.assertFalse(indicator["chartAttachmentAllowed"])
        self.assertEqual(
            self.contract["api"]["createBuildArtifactKindDefault"],
            "expert_advisor",
        )
        self.assertIn(
            "artifactKind",
            self.contract["api"]["createBuildFields"],
        )
        self.assertEqual(
            self.contract["stages"][4]["notApplicableArtifactKinds"],
            ["custom_indicator"],
        )

    def test_report_contract_tracks_report_tab_proof_and_history_quality_attention(self):
        backtest = self.report_contract["typed_report_schemas"]["ea_build_report"][
            "backtestRecheck"
        ]
        self.assertEqual(
            backtest["testerReportScreenshotArtifactAlias"],
            "tester_report_proof",
        )
        self.assertEqual(backtest["testerReportArtifactAlias"], "tester_report")
        self.assertIn("mismatchedChartErrors", backtest)
        self.assertIn("historyQualityIssue", backtest)
        self.assertIn("historyQualityVerified", backtest)
        self.assertEqual(
            backtest["attentionReasonCode"].split("|"),
            [
                "backtest_zero_trades",
                "backtest_history_quality_errors",
                "backtest_zero_trades_and_history_quality_errors",
                "null",
            ],
        )
        self.assertEqual(
            backtest["executionOutcome"].split("|"),
            [
                "completed_with_trades",
                "completed_zero_trades",
                "completed_with_trades_history_quality_errors",
                "completed_zero_trades_with_history_quality_errors",
                "null",
            ],
        )
        stage = next(
            item
            for item in self.contract["stages"]
            if item["id"] == "backtest_recheck"
        )
        self.assertIn("tester_report_proof", stage["successEvidence"])
        connection = next(
            item
            for item in self.connections["profiles"]["right_server_racks"]["connections"]
            if item["id"] == "strategy_tester_adapter"
        )
        self.assertIn("tester_report_proof", connection["successEvidence"])
        self.assertIn("history_quality_attention", connection["successEvidence"])

    def test_deep_research_source_maps_to_exact_compact_ten_fields(self):
        source = self.contract["sourceContract"]
        columns = source["columns"]
        google_sheet = source["googleSheets"]
        self.assertEqual(google_sheet["tabName"], "Deep_Research")
        self.assertEqual(google_sheet["sharedConsumerPropId"], "left_server_racks")
        self.assertEqual(
            google_sheet["sourceRangeRequired"],
            "A-J (10 exact Strategy Brief headers)",
        )
        self.assertEqual(
            google_sheet["internalMapping"],
            "One prose Strategy Brief with 10 authoritative fields",
        )
        self.assertEqual(source["columnRange"], "A-J")
        self.assertEqual(
            source["columnRangeSemantics"],
            "authoritative_deep_research_strategy_brief_sheet_range",
        )
        self.assertEqual(source["coreColumns"], "A-J")
        self.assertIsNone(source["downstreamColumns"])
        self.assertEqual([row["column"] for row in columns], list("ABCDEFGHIJ"))
        self.assertEqual(
            [row["id"] for row in columns],
            [
                "record_id",
                "system_name",
                "system_overview",
                "entry_rules",
                "recovery_rules",
                "exit_rules",
                "money_management",
                "order_execution",
                "display_requirements",
                "additional_notes",
            ],
        )
        self.assertEqual(len(columns), 10)
        self.assertTrue(all(row["group"] == "strategy_brief" for row in columns))
        self.assertTrue(all(row["required"] is True for row in columns))

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

    def test_visible_one_click_is_mt4_only_and_never_launches_terminal(self):
        mt4 = self.contract["platforms"]["mt4"]
        mt5 = self.contract["platforms"]["mt5"]
        self.assertTrue(mt4["oneClickVisibleAvailable"])
        self.assertTrue(mt4["terminalMustAlreadyBeRunning"])
        self.assertFalse(mt4["terminalProcessLaunchRequired"])
        self.assertIn("one_click_visible", mt4["compileMode"])
        self.assertIn("one_click_visible", mt4["backtestMode"])
        self.assertFalse(mt5["oneClickVisibleAvailable"])
        self.assertEqual(
            mt5["oneClickBlockedReasonCode"],
            "one_click_visible_mt5_not_implemented",
        )
        self.assertTrue(mt5["terminalMustAlreadyBeRunning"])
        self.assertFalse(mt5["terminalProcessLaunchRequired"])
        self.assertEqual(mt5["compileMode"], "manual_stage_by_stage_visible_metaeditor")
        self.assertEqual(
            mt5["backtestMode"],
            "manual_stage_by_stage_visible_strategy_tester",
        )
        self.assertFalse(
            self.contract["security"]["oneClickMayLaunchSelectedTerminalProcess"]
        )

    def test_source_repair_and_manual_retry_are_bounded(self):
        generation = self.contract["stages"][1]
        self.assertEqual(generation["semanticRepair"]["automaticAttempts"], 1)
        self.assertTrue(generation["semanticRepair"]["validatorFindingsOnly"])
        self.assertTrue(generation["semanticRepair"]["sameImmutableStrategySpec"])
        self.assertTrue(generation["semanticRepair"]["materializeOnlyAfterPass"])
        retry = generation["manualRetry"]
        self.assertEqual(retry["allowedFailureCodes"], ["invalid_output"])
        self.assertTrue(retry["requiresNoSourceOrVersion"])
        self.assertTrue(retry["freshMission"])
        self.assertEqual(retry["maximumAttempts"], 3)
        self.assertEqual(
            self.contract["api"]["retryBuildStage"],
            "POST /api/props/right_server_racks/ea-factory/builds/:buildId/retry",
        )
        self.assertEqual(
            self.contract["api"]["retryBuildStageFields"],
            ["stageId", "failedMissionId", "idempotencyKey"],
        )

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
        mapped_flow = self.plugin_map["equipment"]["right_server_racks"]["factoryFlow"]
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
        self.assertEqual(
            profile["operation"]["defaultMode"],
            "one_click_with_manual_stage_recovery",
        )
        self.assertFalse(profile["operation"]["scheduled"])
        self.assertTrue(profile["operation"]["automaticLoop"])
        self.assertFalse(profile["operation"]["oneUserActionAdvancesOneStage"])
        self.assertTrue(
            profile["operation"]["oneUserClickAdvancesVerifiedStageChain"]
        )
        self.assertEqual(mapped_flow["oneClick"]["supportedVisiblePlatforms"], ["mt4"])
        self.assertEqual(mapped_flow["oneClick"]["mt5Mode"], "manual_stage_by_stage_only")
        self.assertFalse(mapped_flow["oneClick"]["terminalProcessLaunchAllowed"])
        compile_stage = next(
            row for row in mapped_flow["stages"] if row["id"] == "compile_validate"
        )
        self.assertEqual(
            compile_stage["platformPolicy"]["mt5"],
            "manual_stage_by_stage_visible_metaeditor",
        )
        self.assertFalse(compile_stage["oneClickTerminalLaunchAllowed"])
        compile_connection = next(
            row for row in profile["connections"]
            if row["id"] == "metaeditor_compile_adapter"
        )
        self.assertEqual(compile_connection["verifiedOneClickPlatforms"], ["mt4"])
        self.assertEqual(compile_connection["mt5Status"], "manual_stage_by_stage_only")
        self.assertFalse(compile_connection["oneClickTerminalLaunchAllowed"])

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
