from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "backend" / "local-runner" / "bridge_server.py"
RUNNER_PATH = ROOT / "runner" / "codex_cli_runner.py"
BRIEF_TEST_PATH = ROOT / "tests" / "test_ea_strategy_brief.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BRIEF_SUPPORT = load_module(
    "metafx_ea_research_pipeline_brief_support",
    BRIEF_TEST_PATH,
)


class EAResearchPipelineV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_module(
            "metafx_ea_research_pipeline_runner",
            RUNNER_PATH,
        )
        cls.bridge = load_module(
            "metafx_ea_research_pipeline_bridge",
            BRIDGE_PATH,
        )

    def ready_blueprint(self) -> dict:
        """Return the compact Strategy Brief used by the A-J handoff."""

        return copy.deepcopy(BRIEF_SUPPORT.valid_brief())

    def test_deep_research_prompt_preserves_rules_when_optional_metadata_exceeds_cap(self) -> None:
        action = self.bridge.DASHBOARD_WORKFLOW_ACTIONS["deep_research_system"]
        form = self.bridge._sanitize_dashboard_workflow_form(
            action,
            {
                "sourceReportId": "world-report-one",
                "sourceRecordId": "world-system-one",
                "brief": "ตรวจฝั่ง Buy/Sell และกฎแก้ไม้ " + ("ละเอียด " * 80),
            },
        )
        source = {
            "structuredPayload": {
                "reportId": "world-report-one",
                "recordId": "world-system-one",
                "sourceMissionId": "world-mission-one",
                "verificationStatus": "verified",
                "sourceUrls": [
                    "https://tradingfinder.com/education/ema-cross",
                    "https://forex-station.com/ema-cross-confirmation",
                ],
                "system": {
                    "systemName": "EMA 10/60 Cross",
                    "strategyFamily": "trend_following",
                    "market": "Forex",
                    "symbols": ["EURUSD"],
                    "timeframes": ["H1"],
                    "sessions": ["London"],
                    "setupConditions": [
                        "Evaluate only after a new H1 bar closes",
                        "Spread must be below the documented maximum",
                    ],
                    "sourceTitle": "Optional catalog detail " + ("source detail " * 150),
                    "risksAndLimitations": ["optional risk note " * 100],
                    "unknowns": ["optional unknown note " * 100],
                    "indicatorSettings": [
                        {
                            "name": "EMA",
                            "settings": "10 and 60, exponential, close price",
                            "role": "entry",
                            "truthStatus": "fact",
                        }
                    ],
                    "entrySteps": [
                        {
                            "stepNo": 1,
                            "rule": "EMA10[2] <= EMA60[2] and EMA10[1] > EMA60[1]",
                            "truthStatus": "fact",
                        }
                    ],
                    "exitSteps": [
                        {
                            "stepNo": 1,
                            "rule": "EMA10[2] >= EMA60[2] and EMA10[1] < EMA60[1]",
                            "truthStatus": "fact",
                        }
                    ],
                    "tradeManagementSteps": [
                        {
                            "stepNo": 1,
                            "rule": "Move stop only after one ATR profit",
                            "truthStatus": "fact",
                        }
                    ],
                    "riskManagement": {
                        "positionSizing": "fixed fractional",
                        "maxRiskPerTrade": "1%",
                        "maxOpenPositions": 1,
                        "dailyOrEquityStop": "3% daily loss",
                        "stopLoss": "documented swing low",
                        "takeProfit": "opposite cross",
                        "recoveryMethod": "none",
                        "recoveryRules": [],
                    },
                },
            }
        }
        profile = self.bridge._trusted_workflow_plugin_profile(
            "left_server_racks",
            "deep_research_system",
            form,
        )
        preset = profile["inputPreset"]["brief"]
        self.assertIn("compact-ea-safe-inputs-v2", preset)
        self.assertIn("IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT", preset)
        self.assertLessEqual(len(preset), 800)
        prompt = self.bridge._workflow_prompt(
            "deep_research_system",
            form,
            source,
            profile,
        )
        block = prompt.split("[UNTRUSTED_SOURCE_REPORT_BEGIN]", 1)[1].split(
            "[UNTRUSTED_SOURCE_REPORT_END]",
            1,
        )[0]
        source_json = block[block.index("{") :].strip()
        decoded = json.loads(source_json)
        self.assertLessEqual(
            len(prompt),
            self.bridge.TRADING_SYSTEM_RESEARCH_BUILDER_PROMPT_MAX_CHARS,
        )
        self.assertIn("fast[2] <= slow[2]", prompt)
        self.assertIn("compact-ea-safe-inputs-v2", prompt)
        self.assertIn("component by component", prompt)
        self.assertIn("RecoveryMode=none", prompt)
        self.assertEqual(decoded["recordId"], "world-system-one")
        self.assertEqual(len(decoded["sourceUrls"]), 2)
        self.assertTrue(decoded["sourceContextTruncated"])
        self.assertEqual(decoded["truncationScope"], "optional_metadata_only")
        for field in (
            "systemName",
            "strategyFamily",
            "market",
            "symbols",
            "timeframes",
            "sessions",
            "setupConditions",
            "indicatorSettings",
            "entrySteps",
            "exitSteps",
            "tradeManagementSteps",
            "riskManagement",
        ):
            self.assertIn(field, decoded["system"])
        self.assertEqual(
            decoded["system"]["entrySteps"][0]["rule"],
            "EMA10[2] <= EMA60[2] and EMA10[1] > EMA60[1]",
        )
        self.assertEqual(
            decoded["system"]["riskManagement"]["dailyOrEquityStop"],
            "3% daily loss",
        )
        self.assertEqual(
            decoded["system"]["riskManagement"]["recoveryRules"],
            [],
        )
        self.assertEqual(decoded["system"]["timeframes"], ["H1"])
        self.assertEqual(decoded["system"]["sessions"], ["London"])
        self.assertEqual(
            decoded["system"]["setupConditions"][0],
            "Evaluate only after a new H1 bar closes",
        )
        self.assertNotIn("sourceTitle", decoded["system"])
        self.assertNotIn("[TRUNCATED]", source_json)

    def test_deep_research_prompt_keeps_five_thousand_character_source_exact(self) -> None:
        entry_rule = "ENTRY:" + ("E" * 1450)
        exit_rule = "EXIT:" + ("X" * 1350)
        management_rule = "MANAGE:" + ("M" * 900)
        setup_rule = "SETUP:" + ("S" * 650)
        stop_rule = "STOP:" + ("R" * 450)
        form = self.bridge._sanitize_dashboard_workflow_form(
            self.bridge.DASHBOARD_WORKFLOW_ACTIONS["deep_research_system"],
            {
                "sourceReportId": "large-real-sheet-report",
                "sourceRecordId": "large-real-sheet-record",
            },
        )
        source = {
            "structuredPayload": {
                "reportId": "large-real-sheet-report",
                "recordId": "large-real-sheet-record",
                "verificationStatus": "verified",
                "sourceUrls": [
                    "https://tradingfinder.com/education/large-system",
                    "https://forex-station.com/large-system",
                ],
                "system": {
                    "systemName": "Large verified Sheet system",
                    "strategyFamily": "trend_following",
                    "market": "Forex",
                    "symbols": ["EURUSD"],
                    "timeframes": ["H1"],
                    "sessions": ["London"],
                    "setupConditions": [setup_rule],
                    "indicatorSettings": [
                        {"name": "EMA", "settings": "10/60", "role": "entry"}
                    ],
                    "entrySteps": [{"stepNo": 1, "rule": entry_rule}],
                    "exitSteps": [{"stepNo": 1, "rule": exit_rule}],
                    "tradeManagementSteps": [
                        {"stepNo": 1, "rule": management_rule}
                    ],
                    "riskManagement": {
                        "positionSizing": "fixed fractional",
                        "maxRiskPerTrade": "1%",
                        "stopLoss": stop_rule,
                        "recoveryMethod": "none",
                        "recoveryRules": [],
                        "truthStatus": "partial",
                    },
                },
            }
        }
        profile = self.bridge._trusted_workflow_plugin_profile(
            "left_server_racks",
            "deep_research_system",
            form,
        )

        prompt = self.bridge._workflow_prompt(
            "deep_research_system",
            form,
            source,
            profile,
        )
        block = prompt.split("[UNTRUSTED_SOURCE_REPORT_BEGIN]", 1)[1].split(
            "[UNTRUSTED_SOURCE_REPORT_END]",
            1,
        )[0]
        decoded = json.loads(block[block.index("{") :].strip())
        encoded = json.dumps(
            decoded,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        self.assertGreaterEqual(len(encoded), 5015)
        self.assertLessEqual(
            len(encoded),
            self.bridge.TRADING_SYSTEM_RESEARCH_SOURCE_PROMPT_MAX_CHARS,
        )
        self.assertLessEqual(
            len(prompt),
            self.bridge.TRADING_SYSTEM_RESEARCH_BUILDER_PROMPT_MAX_CHARS,
        )
        self.assertEqual(decoded["system"]["entrySteps"][0]["rule"], entry_rule)
        self.assertEqual(decoded["system"]["exitSteps"][0]["rule"], exit_rule)
        self.assertEqual(
            decoded["system"]["tradeManagementSteps"][0]["rule"],
            management_rule,
        )
        self.assertEqual(decoded["system"]["setupConditions"], [setup_rule])
        self.assertEqual(decoded["system"]["riskManagement"]["stopLoss"], stop_rule)
        self.assertEqual(
            decoded["system"]["riskManagement"]["recoveryRules"],
            [],
        )

    def test_runner_prompt_limit_is_larger_only_for_trading_system_research(self) -> None:
        research_prompt = "R" * 12000
        self.assertEqual(
            self.runner.bound_mission_prompt(
                research_prompt,
                "trading_system_research",
            ),
            research_prompt,
        )
        with self.assertRaises(ValueError):
            self.runner.bound_mission_prompt(
                research_prompt + "R",
                "trading_system_research",
            )
        with self.assertRaises(ValueError):
            self.runner.bound_mission_prompt("G" * 8001, "general")

    def test_deep_research_prompt_fails_closed_when_essential_rules_exceed_cap(self) -> None:
        action = self.bridge.DASHBOARD_WORKFLOW_ACTIONS["deep_research_system"]
        form = self.bridge._sanitize_dashboard_workflow_form(
            action,
            {
                "sourceReportId": "oversize-report",
                "sourceRecordId": "oversize-record",
            },
        )
        source = {
            "structuredPayload": {
                "reportId": "oversize-report",
                "recordId": "oversize-record",
                "verificationStatus": "verified",
                "sourceUrls": [
                    "https://tradingfinder.com/education/oversize-rules",
                    "https://forex-station.com/oversize-rules",
                ],
                "system": {
                    "systemName": "Oversize deterministic system",
                    "strategyFamily": "trend_following",
                    "indicatorSettings": [
                        {"name": "EMA", "settings": "10 and 60", "role": "entry"}
                    ],
                    "entrySteps": [
                        {
                            "stepNo": 1,
                            "rule": "x" * 2100,
                            "truthStatus": "fact",
                        }
                    ],
                    "exitSteps": [{"stepNo": 1, "rule": "opposite cross"}],
                    "tradeManagementSteps": [],
                    "riskManagement": {
                        "positionSizing": "fixed fractional",
                        "maxRiskPerTrade": "1%",
                    },
                },
            }
        }
        profile = self.bridge._trusted_workflow_plugin_profile(
            "left_server_racks",
            "deep_research_system",
            form,
        )

        with self.assertRaises(self.bridge.RequestError) as raised:
            self.bridge._workflow_prompt(
                "deep_research_system",
                form,
                source,
                profile,
            )

        self.assertEqual(raised.exception.status, 422)
        self.assertIn("indicator/entry/exit/management/risk", str(raised.exception))

    def non_ready_blueprint(self) -> dict:
        brief = self.ready_blueprint()
        brief.pop("entryRules")
        return brief

    @staticmethod
    def result_payload(blueprint: dict) -> dict:
        evidence = [
            {
                "label": f"Public source {index}",
                "url": str(url),
                "note": "Public source opened by the research worker",
            }
            for index, url in enumerate(blueprint.get("sourceLinks", []), start=1)
        ]
        return {
            "status": "completed",
            "summary": "EA-ready deterministic research completed",
            "findings": ["Closed-bar rules were expanded into typed expressions"],
            "nextSteps": ["Archive the canonical blueprint in Deep_Research"],
            "evidence": evidence,
            "blockedCapability": "",
            "research": blueprint,
            "evidenceKinds": [
                "at_least_two_source_urls",
                "checked_at",
                "limitations",
                "source_digest",
            ],
        }

    def parse_and_project(self, blueprint: dict) -> tuple[dict, dict, dict]:
        parsed = self.runner.parse_work_result(
            json.dumps(self.result_payload(blueprint), ensure_ascii=False),
            64_000,
            "trading_system_research",
        )
        profile = self.bridge.equipment_action_profile(
            "left_server_racks",
            "deep_research_system",
        )
        mission = {
            "budget": {"outputLimitChars": 64_000},
            "workflowContext": {"pluginProcedure": profile},
        }
        receipt = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            parsed,
        )
        metrics = self.bridge.dashboard_workflow_output_metrics(receipt)
        return parsed, receipt, metrics

    @staticmethod
    def report_from_metrics(metrics: dict, *, suffix: str = "ready") -> dict:
        return {
            "id": f"report-ea-research-pipeline-{suffix}",
            "type": "trading_system_research_report",
            "title": "Deep research: EMA closed-bar cross",
            "status": "ready",
            "linkedPropId": "left_server_racks",
            "linkedMissionId": f"mission-ea-research-pipeline-{suffix}",
            "ownerAgentId": "mission_archivist",
            "createdAt": "2026-09-08T09:30:00+07:00",
            "updatedAt": "2026-09-08T09:35:00+07:00",
            "workflowContext": {
                "propId": "left_server_racks",
                "actionId": "deep_research_system",
                "source": {
                    "recordId": f"world-ema-cross-{suffix}",
                    "systemId": f"TS-world-ema-cross-{suffix}",
                    "reportId": "report-world-system-source",
                    "missionId": "mission-world-system-source",
                },
            },
            "metrics": copy.deepcopy(metrics),
        }

    def deep_rows_from_metrics(
        self,
        metrics: dict,
        *,
        suffix: str = "ready",
    ) -> tuple[dict, list[dict]]:
        report = self.report_from_metrics(metrics, suffix=suffix)
        version_index = self.bridge._research_sheet_build_deep_version_index([report])
        rows, factory_rows = self.bridge._research_sheet_deep_rows(
            report,
            version_index=version_index,
        )
        self.assertEqual(len(rows), 1)
        return rows[0], factory_rows

    def ready_factory_record(self) -> tuple[dict, dict, dict]:
        _parsed, receipt, metrics = self.parse_and_project(self.ready_blueprint())
        self.assertTrue(receipt["valid"], receipt)
        row, _factory_rows = self.deep_rows_from_metrics(metrics)
        records = self.bridge._ea_factory_deep_research_records(
            [row],
            source_key="sheet-ea-research-pipeline-aj",
            strict=True,
        )
        self.assertEqual(len(records), 1)
        return records[0], row, metrics

    def test_runner_direct_research_becomes_valid_backend_receipt_and_projection(self) -> None:
        blueprint = self.ready_blueprint()
        parsed, receipt, metrics = self.parse_and_project(blueprint)

        self.assertEqual(
            {item["field"] for item in parsed["contractFields"]},
            set(self.runner.TRADING_SYSTEM_RESEARCH_CONTRACT_FIELDS),
        )
        self.assertTrue(receipt["valid"], receipt)
        self.assertEqual(receipt["missingFields"], [])
        self.assertEqual(receipt["missingEvidenceKinds"], [])
        self.assertEqual(receipt["entryErrors"], [])

        normalized = BRIEF_SUPPORT.BRIEF.normalize_strategy_brief(blueprint)
        digest = BRIEF_SUPPORT.BRIEF.compute_strategy_brief_digest(normalized)
        self.assertEqual(metrics["strategyBrief"], normalized)
        self.assertEqual(metrics["sourceDigest"], digest)
        self.assertEqual(metrics["briefDigest"], digest)
        self.assertIn("fast[2]", metrics["strategyBrief"]["entryRules"])

    def test_component_defaults_survive_backend_sheet_and_factory_handoff(self) -> None:
        brief = self.ready_blueprint()
        brief["recoveryRules"] = "not_publicly_stated"
        brief["exitRules"] = (
            "Source-backed StopLoss=20 pips; Take Profit not_publicly_stated; "
            "Trailing Stop not_publicly_stated."
        )
        brief["moneyManagement"] = (
            "Source-backed RiskPercent=0.5%; max positions not_publicly_stated."
        )
        brief.pop("orderExecution")

        _parsed, receipt, metrics = self.parse_and_project(brief)

        self.assertTrue(receipt["valid"], receipt)
        projected = metrics["strategyBrief"]
        self.assertIn("StopLoss=20 pips", projected["exitRules"])
        self.assertNotIn("StopLossPoints=300", projected["exitRules"])
        self.assertIn("TakeProfitPoints=600", projected["exitRules"])
        self.assertIn("TrailingStop=false", projected["exitRules"])
        self.assertIn("RiskPercent=0.5%", projected["moneyManagement"])
        self.assertNotIn("RiskPercent=1.0", projected["moneyManagement"])
        self.assertIn("LossPerLotAtSL", projected["moneyManagement"])
        self.assertIn(
            "MaxOpenPositionsPerSymbolMagic=1",
            projected["moneyManagement"],
        )
        self.assertIn("RecoveryMode=none", projected["recoveryRules"])
        self.assertIn("Market Buy/Sell", projected["orderExecution"])
        self.assertIn("compact-ea-safe-inputs-v2", projected["additionalNotes"])
        self.assertIn(
            "INPUT_METADATA_VERSION=ea-optimization-inputs-v1",
            projected["additionalNotes"],
        )

        row, _factory_rows = self.deep_rows_from_metrics(
            metrics,
            suffix="implementation-defaults",
        )
        self.assertEqual(row["exit_rules"], projected["exitRules"])
        self.assertEqual(row["money_management"], projected["moneyManagement"])
        records = self.bridge._ea_factory_deep_research_records(
            [row],
            source_key="sheet-component-defaults",
            strict=True,
        )
        self.assertEqual(len(records), 1)
        self.assertTrue(records[0]["buildReady"])
        self.assertEqual(
            " ".join(records[0]["strategyBrief"]["exitRules"].split()),
            " ".join(row["exit_rules"].split()),
        )
        self.assertEqual(
            records[0]["strategyBriefDigest"],
            self.bridge._ea_factory_sheet_strategy_brief_digest(
                records[0]["recordId"],
                {
                    sheet_name: records[0]["strategyBrief"][camel_name]
                    for sheet_name, camel_name in self.bridge.EA_STRATEGY_BRIEF_SHEET_TO_CAMEL.items()
                },
            ),
        )

    def test_backend_projection_does_not_truncate_large_compact_notes(self) -> None:
        blueprint = self.ready_blueprint()
        notes = "bounded-note;" * 280
        blueprint["additionalNotes"] = notes

        _parsed, receipt, metrics = self.parse_and_project(blueprint)

        self.assertTrue(receipt["valid"], receipt)
        self.assertEqual(metrics["strategyBrief"]["additionalNotes"], notes)
        self.assertEqual(
            self.bridge.compute_strategy_brief_digest(metrics["strategyBrief"]),
            metrics["briefDigest"],
        )

    def test_runner_rejects_incomplete_brief_and_wrong_schema(self) -> None:
        cases: list[tuple[str, dict, str]] = []

        incomplete = self.ready_blueprint()
        incomplete["entryRules"] = ""
        cases.append(("missing entry prose", incomplete, "BRIEF_TEXT_REQUIRED"))

        wrong_schema = self.ready_blueprint()
        wrong_schema["schemaVersion"] = "ea-strategy-brief/0.9.0"
        cases.append(("wrong schema", wrong_schema, "BRIEF_SCHEMA_VERSION_INVALID"))

        for label, blueprint, expected_code in cases:
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError, expected_code):
                    self.runner.parse_work_result(
                        json.dumps(self.result_payload(blueprint), ensure_ascii=False),
                        64_000,
                        "trading_system_research",
                    )

    def test_report_projects_one_exact_a_j_row_and_preserves_brief_digest(self) -> None:
        blueprint = self.ready_blueprint()
        _parsed, receipt, metrics = self.parse_and_project(blueprint)
        self.assertTrue(receipt["valid"], receipt)

        row, factory_rows = self.deep_rows_from_metrics(metrics)
        self.assertEqual(len(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS), 10)
        self.assertEqual(set(row), set(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS))
        self.assertEqual(factory_rows, [])
        normalized = metrics["strategyBrief"]
        digest = metrics["briefDigest"]
        field_map = {
            "system_name": "systemName",
            "system_overview": "systemOverview",
            "entry_rules": "entryRules",
            "recovery_rules": "recoveryRules",
            "exit_rules": "exitRules",
            "money_management": "moneyManagement",
            "order_execution": "orderExecution",
            "display_requirements": "displayRequirements",
            "additional_notes": "additionalNotes",
        }
        for sheet_field, brief_field in field_map.items():
            self.assertEqual(row[sheet_field], normalized[brief_field])
        sheet_factory_values = self.bridge._ea_factory_deep_research_values(row)
        self.assertTrue(sheet_factory_values["_humanConfirmationValid"])
        self.assertEqual(
            self.bridge.compute_strategy_brief_digest(normalized),
            digest,
        )

    def test_sheet_entry_cell_preserves_long_prose_and_digest(self) -> None:
        blueprint = self.ready_blueprint()
        long_line = "IF closed bar is confirmed THEN " + ("ตรวจเงื่อนไข;" * 350)
        self.assertGreater(len(long_line), 4000)
        blueprint["entryRules"] = long_line

        _parsed, receipt, metrics = self.parse_and_project(blueprint)
        self.assertTrue(receipt["valid"], receipt)
        row, _factory_rows = self.deep_rows_from_metrics(
            metrics,
            suffix="long-pseudocode",
        )

        self.assertEqual(row["entry_rules"], long_line)
        records = self.bridge._ea_factory_deep_research_records(
            [row],
            source_key="sheet-long-entry",
            strict=True,
        )
        self.assertEqual(records[0]["strategyBrief"]["entryRules"], long_line)
        self.assertEqual(
            records[0]["strategyBriefDigest"],
            self.bridge._ea_factory_sheet_strategy_brief_digest(
                row["record_id"],
                row,
            ),
        )

    def test_strategy_brief_rejects_oversize_entry_before_outbox_item_exists(self) -> None:
        blueprint = self.ready_blueprint()
        blueprint["entryRules"] = "X" * 8_001
        with self.assertRaisesRegex(
            self.bridge.StrategyBriefValidationError,
            "BRIEF_TEXT_TOO_LONG",
        ):
            self.bridge.normalize_strategy_brief(blueprint)

    def test_catalog_falls_back_from_corrupt_sheet_duplicate_to_ready_runtime(self) -> None:
        valid_sheet, _row, _metrics = self.ready_factory_record()
        valid_runtime = copy.deepcopy(valid_sheet)
        valid_runtime.update({
            "sourceKind": "verified_deep_research",
            "sourceKey": "runtime-complete-report",
        })
        corrupt_sheet = copy.deepcopy(valid_sheet)
        corrupt_sheet.update({
            "sourceKey": "central-sheet-corrupt",
            "buildReady": False,
            "readinessIssues": ["incomplete compact Sheet projection"],
        })
        self.assertTrue(valid_runtime["buildReady"])
        self.assertFalse(corrupt_sheet["buildReady"])
        self.assertEqual(valid_runtime["recordId"], corrupt_sheet["recordId"])

        def catalog_for(sheet_record: dict) -> list[dict]:
            with (
                mock.patch.object(
                    self.bridge,
                    "_research_sheet_hub_internal",
                    return_value={"sheetId": "central-sheet-id"},
                ),
                mock.patch.object(
                    self.bridge,
                    "_research_sheet_cached_rows",
                    return_value=[],
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_deep_research_records",
                    return_value=[sheet_record],
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_google_sheet_records",
                    return_value=[],
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_research_source_records",
                    return_value=[valid_runtime],
                ),
            ):
                return self.bridge._ea_factory_source_catalog(state={})

        fallback_catalog = catalog_for(corrupt_sheet)
        self.assertEqual(len(fallback_catalog), 1)
        self.assertEqual(
            fallback_catalog[0]["sourceRecordId"],
            valid_runtime["sourceRecordId"],
        )
        self.assertEqual(fallback_catalog[0]["sourceKind"], "verified_deep_research")

        authoritative_catalog = catalog_for(valid_sheet)
        self.assertEqual(len(authoritative_catalog), 1)
        self.assertEqual(
            authoritative_catalog[0]["sourceRecordId"],
            valid_sheet["sourceRecordId"],
        )
        self.assertEqual(
            authoritative_catalog[0]["sourceKind"],
            "verified_deep_research_sheet",
        )

    def test_deep_row_normalizes_to_ea_ready_factory_record(self) -> None:
        record, _row, metrics = self.ready_factory_record()

        self.assertTrue(record["buildReady"], record)
        self.assertEqual(record["missingCoreFields"], [])
        self.assertEqual(record["readinessIssues"], [])
        self.assertEqual(record["strategyBrief"]["systemName"], metrics["strategyBrief"]["systemName"])
        self.assertRegex(record["strategyBriefDigest"], r"^[0-9a-f]{64}$")
        self.assertIsNone(record["eaImplementationBlueprint"])
        self.assertIsNone(record["eaBlueprintDigest"])

    def test_strategy_spec_v3_workspace_revalidates_from_sheet_source(self) -> None:
        record, _row, _metrics = self.ready_factory_record()
        build_id = "ea-build-research-pipeline-v2"
        platform = "mt4"
        brief = ""
        mission = {"id": "mission-ea-spec-pipeline-v2"}
        report = {"id": "report-ea-spec-pipeline-v2"}

        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            with mock.patch.object(self.bridge, "PROJECT_ROOT", project_root):
                workspace = self.bridge._ea_factory_create_build_workspace(
                    build_id,
                    record,
                    platform,
                )
                build = {
                    "schemaVersion": "ea-factory-build-v1",
                    "id": build_id,
                    "sourceRecordId": record["sourceRecordId"],
                    "sourceDisplayName": record["displayName"],
                    "sourceRecordDigest": record["recordDigest"],
                    "sourceReportId": report["id"],
                    "sourceMissionId": mission["id"],
                    "platform": platform,
                    "brief": brief,
                    "status": "ready",
                    "workspace": workspace,
                    "stages": self.bridge._ea_factory_initial_stages(
                        platform,
                        mission,
                        report,
                    ),
                    "versions": [],
                    "createIdempotencyKey": None,
                    "createIdempotencyKeys": [],
                    "createRequestDigest": self.bridge._ea_factory_create_request_digest(
                        record["sourceRecordId"],
                        platform,
                        brief,
                    ),
                    "createdAt": "2026-09-08T09:40:00+07:00",
                    "updatedAt": "2026-09-08T09:40:00+07:00",
                }
                artifacts = self.bridge._ea_factory_register_artifacts(
                    build,
                    [
                        {
                            "relativePath": workspace["strategySpecFile"],
                            "stageId": "strategy_spec",
                            "reportId": report["id"],
                            "artifactKind": "strategy_spec",
                        }
                    ],
                )
                self.bridge._ea_factory_stage_row(build, "strategy_spec")[
                    "artifacts"
                ] = [item["fileId"] for item in artifacts]

                spec_path = (
                    project_root
                    / "workspace"
                    / "ea-factory"
                    / build_id
                    / workspace["strategySpecFile"]
                )
                spec = json.loads(spec_path.read_text(encoding="utf-8"))
                self.assertEqual(spec["schemaVersion"], "ea-factory-strategy-spec-v3")
                self.assertEqual(
                    spec["strategyBriefDigest"],
                    record["strategyBriefDigest"],
                )
                self.assertEqual(spec["strategyBrief"], record["strategyBrief"])
                self.assertNotIn("eaImplementationBlueprint", spec)

                validated = self.bridge._ea_factory_revalidated_build(build)

        self.assertEqual(validated["id"], build_id)
        self.assertEqual(validated["sourceRecordId"], record["sourceRecordId"])
        self.assertFalse(validated["coverageUpgradeRequired"])
        self.assertEqual(validated["coverageStatus"], "compact_current")

    def test_persisted_compact_v3_loads_as_current_without_legacy_coverage(self) -> None:
        record, _row, _metrics = self.ready_factory_record()
        build_id = "ea-build-research-persisted-compact-v3"
        platform = "mt4"
        mission = {"id": "mission-ea-spec-persisted-compact-v3"}
        report = {"id": "report-ea-spec-persisted-compact-v3"}

        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            runtime_dir = project_root / "runtime"
            runtime_dir.mkdir(parents=True, exist_ok=True)
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_dir),
            ):
                workspace = self.bridge._ea_factory_create_build_workspace(
                    build_id,
                    record,
                    platform,
                )
                build = {
                    "schemaVersion": "ea-factory-build-v1",
                    "id": build_id,
                    "sourceRecordId": record["sourceRecordId"],
                    "sourceDisplayName": record["displayName"],
                    "sourceRecordDigest": record["recordDigest"],
                    "sourceReportId": report["id"],
                    "sourceMissionId": mission["id"],
                    "platform": platform,
                    "brief": "",
                    "status": "ready",
                    "workspace": workspace,
                    "stages": self.bridge._ea_factory_initial_stages(
                        platform,
                        mission,
                        report,
                    ),
                    "versions": [],
                    "createIdempotencyKey": None,
                    "createIdempotencyKeys": [],
                    "createRequestDigest": self.bridge._ea_factory_create_request_digest(
                        record["sourceRecordId"],
                        platform,
                        "",
                    ),
                    "createdAt": "2026-09-08T09:40:00+07:00",
                    "updatedAt": "2026-09-08T09:40:00+07:00",
                }
                artifacts = self.bridge._ea_factory_register_artifacts(
                    build,
                    [{
                        "relativePath": workspace["strategySpecFile"],
                        "stageId": "strategy_spec",
                        "reportId": report["id"],
                        "artifactKind": "strategy_spec",
                    }],
                )
                self.bridge._ea_factory_stage_row(build, "strategy_spec")[
                    "artifacts"
                ] = [item["fileId"] for item in artifacts]
                persisted = self.bridge._empty_ea_factory_state()
                persisted["builds"] = [build]
                state_path = self.bridge._ea_factory_state_path()
                state_path.write_text(
                    json.dumps(persisted, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

                loaded_build = self.bridge._load_ea_factory_state_unlocked()["builds"][0]
                model = self.bridge._ea_factory_build_read_model(loaded_build)
                spec_path = (
                    project_root
                    / "workspace"
                    / "ea-factory"
                    / build_id
                    / workspace["strategySpecFile"]
                )
                spec = json.loads(spec_path.read_text(encoding="utf-8"))

        self.assertEqual(spec["schemaVersion"], "ea-factory-strategy-spec-v3")
        self.assertNotIn("eaImplementationBlueprint", spec)
        self.assertFalse(loaded_build["coverageUpgradeRequired"])
        self.assertEqual(loaded_build["coverageStatus"], "compact_current")
        self.assertFalse(model["rebuildRequired"])

    def test_legacy_v1_deep_row_is_rejected_before_factory(self) -> None:
        _record, row, _metrics = self.ready_factory_record()
        legacy_row = copy.deepcopy(row)
        legacy_row["entry_rules"] = ""

        with self.assertRaisesRegex(
            self.bridge.RequestError,
            "incomplete Strategy Brief row",
        ):
            self.bridge._ea_factory_deep_research_records(
                [legacy_row],
                source_key="sheet-ea-research-pipeline-v1",
                strict=True,
            )

    def test_incomplete_strategy_brief_never_reaches_sheet_or_factory(self) -> None:
        with self.assertRaisesRegex(
            self.runner.EAResearchSemanticValidationError,
            "BRIEF_FIELDS_MISSING",
        ):
            self.parse_and_project(self.non_ready_blueprint())


if __name__ == "__main__":
    unittest.main()
