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
BLUEPRINT_TEST_PATH = ROOT / "tests" / "test_ea_research_blueprint_v2.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BLUEPRINT_SUPPORT = load_module(
    "metafx_ea_research_pipeline_blueprint_support",
    BLUEPRINT_TEST_PATH,
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
        blueprint = BLUEPRINT_SUPPORT.ready_blueprint()
        blueprint["evidenceMap"].append(
            {
                "sourceRef": "S3",
                "url": "https://www.babypips.com/learn/forex/moving-averages",
                "title": "Moving average reference",
                "checkedAt": blueprint["checkedAt"],
            }
        )
        return blueprint

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
        blueprint = self.ready_blueprint()
        rule = blueprint["entry"]["buy"]["rules"][0]
        rule["sourceStatus"] = "unknown"
        rule["sourceRefs"] = []
        rule["expression"] = {"op": "unknown"}
        blueprint["completeness"].update(
            {
                "status": "needs_clarification",
                "score": 65,
                "eaHandoffAllowed": False,
                "deterministicBacktestAllowed": False,
                "blockingIssues": [
                    {
                        "code": "ENTRY_UNKNOWN",
                        "path": "$.entry.buy.rules[0]",
                        "messageTh": "ยังไม่ทราบเงื่อนไขเข้า Buy",
                        "questionTh": "โปรดยืนยันเงื่อนไขเข้า Buy",
                    }
                ],
                "warnings": [],
                "unknownPaths": ["$.entry.buy.rules[0]"],
                "conflictPaths": [],
            }
        )
        return blueprint

    @staticmethod
    def result_payload(blueprint: dict) -> dict:
        evidence = [
            {
                "label": str(item["title"]),
                "url": str(item["url"]),
                "note": "Public source opened by the research worker",
            }
            for item in blueprint["evidenceMap"]
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
                "ea_readiness",
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
            source_key="sheet-ea-research-pipeline-v2",
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

        normalized = BLUEPRINT_SUPPORT.CONTRACT.normalize_blueprint(blueprint)
        digest = BLUEPRINT_SUPPORT.CONTRACT.compute_blueprint_digest(normalized)
        self.assertEqual(metrics["eaBlueprint"], normalized)
        self.assertEqual(metrics["eaImplementationBlueprint"], normalized)
        self.assertEqual(metrics["sourceDigest"], digest)
        self.assertEqual(metrics["blueprintDigest"], digest)
        self.assertEqual(metrics["eaReadiness"]["status"], "ready")
        self.assertIn("cross_above", metrics["eaReadyText"])

    def test_backend_projection_does_not_truncate_241_canonical_warnings(self) -> None:
        blueprint = self.ready_blueprint()
        warnings = [f"bounded-warning-{index:03d}" for index in range(241)]
        blueprint["completeness"]["warnings"] = warnings

        _parsed, receipt, metrics = self.parse_and_project(blueprint)

        self.assertTrue(receipt["valid"], receipt)
        self.assertEqual(
            metrics["eaBlueprint"]["completeness"]["warnings"],
            warnings,
        )
        self.assertEqual(
            metrics["eaImplementationBlueprint"]["completeness"]["warnings"],
            warnings,
        )
        self.assertEqual(
            self.bridge.ea_research_blueprint_digest(metrics["eaBlueprint"]),
            metrics["blueprintDigest"],
        )

    def test_runner_rejects_plain_prose_and_wrong_cross_expansion(self) -> None:
        cases: list[tuple[str, dict, str]] = []

        prose = self.ready_blueprint()
        prose["entry"]["buy"]["rules"] = ["EMA 10 crosses EMA 60"]
        cases.append(("plain prose", prose, "TYPED_RULE_REQUIRED"))

        wrong_cross = self.ready_blueprint()
        expression = wrong_cross["entry"]["buy"]["rules"][0]["expression"]
        expression["expanded"] = {
            "all": [
                {
                    "op": ">=",
                    "left": {"kind": "indicator", "ref": "ema_fast", "shift": 2},
                    "right": {"kind": "indicator", "ref": "ema_slow", "shift": 2},
                },
                {
                    "op": "<",
                    "left": {"kind": "indicator", "ref": "ema_fast", "shift": 1},
                    "right": {"kind": "indicator", "ref": "ema_slow", "shift": 1},
                },
            ]
        }
        cases.append(("wrong cross", wrong_cross, "CROSS_EXPANSION_MISMATCH"))

        for label, blueprint, expected_code in cases:
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError, expected_code):
                    self.runner.parse_work_result(
                        json.dumps(self.result_payload(blueprint), ensure_ascii=False),
                        64_000,
                        "trading_system_research",
                    )

    def test_report_projects_one_49_header_row_and_preserves_blueprint_digest(self) -> None:
        blueprint = self.ready_blueprint()
        _parsed, receipt, metrics = self.parse_and_project(blueprint)
        self.assertTrue(receipt["valid"], receipt)

        row, factory_rows = self.deep_rows_from_metrics(metrics)
        self.assertEqual(len(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS), 49)
        self.assertEqual(set(row), set(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS))
        self.assertEqual(len(factory_rows), 1)
        self.assertEqual(row["verification_status"], "verified_deep_research")

        implementation = json.loads(row["implementation_notes_json"])
        normalized = metrics["eaBlueprint"]
        digest = metrics["blueprintDigest"]
        self.assertEqual(implementation["schemaVersion"], self.bridge.EA_RESEARCH_SCHEMA_VERSION)
        self.assertEqual(implementation["eaImplementationBlueprint"], normalized)
        self.assertEqual(implementation["blueprintDigest"], digest)
        self.assertEqual(
            self.bridge.reconstruct_ea_research_from_sheet(row),
            normalized,
        )
        risk_model = json.loads(row["risk_model_json"])
        sizing_rules = json.loads(row["position_sizing_rules_json"])
        self.assertEqual(risk_model, metrics["riskModel"])
        self.assertEqual(sizing_rules, normalized["riskAndSizing"])
        self.assertNotIn("stopLoss", sizing_rules)
        self.assertNotEqual(sizing_rules, risk_model)
        self.assertEqual(
            json.loads(factory_rows[0]["lot_risk"]),
            normalized["riskAndSizing"],
        )
        sheet_factory_values = self.bridge._ea_factory_deep_research_values(row)
        self.assertEqual(
            json.loads(sheet_factory_values["lot_risk"]),
            normalized["riskAndSizing"],
        )

    def test_sheet_blueprint_cell_preserves_long_pseudocode_and_digest(self) -> None:
        blueprint = self.ready_blueprint()
        long_line = "IF closed bar is confirmed THEN " + ("ตรวจเงื่อนไข;" * 700)
        self.assertGreater(len(long_line), 9000)
        blueprint["pseudocode"]["lines"].append(long_line)

        _parsed, receipt, metrics = self.parse_and_project(blueprint)
        self.assertTrue(receipt["valid"], receipt)
        row, _factory_rows = self.deep_rows_from_metrics(
            metrics,
            suffix="long-pseudocode",
        )

        self.assertLessEqual(
            len(row["implementation_notes_json"].encode("utf-16-le")) // 2,
            self.bridge.TRADING_SYSTEM_RESEARCH_SHEET_BLUEPRINT_CELL_MAX_CHARS,
        )
        implementation = json.loads(row["implementation_notes_json"])
        stored = implementation["eaImplementationBlueprint"]
        self.assertEqual(stored["pseudocode"]["lines"][-1], long_line)
        reconstructed = self.bridge.reconstruct_ea_research_from_sheet(row)
        self.assertEqual(reconstructed, metrics["eaBlueprint"])
        self.assertEqual(
            self.bridge.ea_research_blueprint_digest(reconstructed),
            metrics["blueprintDigest"],
        )

    def test_sheet_blueprint_cell_rejects_oversize_before_outbox_item_exists(self) -> None:
        blueprint = self.ready_blueprint()
        blueprint["pseudocode"]["lines"].append("X" * 45_000)
        with self.assertRaisesRegex(
            self.bridge.EAResearchBlueprintValidationError,
            "BLUEPRINT_TRANSPORT_SIZE_EXCEEDED",
        ):
            self.bridge.normalize_ea_research_blueprint(blueprint)

    def test_catalog_falls_back_from_corrupt_sheet_duplicate_to_ready_runtime(self) -> None:
        valid_sheet, _row, _metrics = self.ready_factory_record()
        values = {
            **copy.deepcopy(valid_sheet["columnValues"]),
            "eaImplementationBlueprint": copy.deepcopy(
                valid_sheet["eaImplementationBlueprint"]
            ),
        }
        valid_runtime = self.bridge._ea_factory_normalize_record(
            values,
            source_kind="verified_deep_research",
            source_key="runtime-complete-report",
            source_report_id="report-runtime-complete",
            source_mission_id="mission-runtime-complete",
        )
        corrupt_sheet = self.bridge._ea_factory_normalize_record(
            valid_sheet["columnValues"],
            source_kind="verified_deep_research_sheet",
            source_key="central-sheet-corrupt",
            source_report_id="report-sheet-corrupt",
            source_mission_id="mission-sheet-corrupt",
        )
        self.assertIsNotNone(valid_runtime)
        self.assertIsNotNone(corrupt_sheet)
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
        self.assertEqual(record["eaImplementationBlueprint"], metrics["eaBlueprint"])
        self.assertEqual(record["eaBlueprintDigest"], metrics["blueprintDigest"])
        self.assertEqual(record["eaReadiness"]["status"], "ready")
        self.assertIn("EA HANDOFF: ALLOWED", record["eaReadyText"])

    def test_strategy_spec_v2_workspace_revalidates_from_sheet_source(self) -> None:
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
                self.assertEqual(spec["schemaVersion"], "ea-factory-strategy-spec-v2")
                self.assertEqual(spec["eaBlueprintDigest"], record["eaBlueprintDigest"])
                self.assertEqual(
                    spec["eaImplementationBlueprint"],
                    record["eaImplementationBlueprint"],
                )

                validated = self.bridge._ea_factory_revalidated_build(build)

        self.assertEqual(validated["id"], build_id)
        self.assertEqual(validated["sourceRecordId"], record["sourceRecordId"])

    def test_legacy_v1_deep_row_is_visible_but_not_build_ready(self) -> None:
        _record, row, _metrics = self.ready_factory_record()
        legacy_row = copy.deepcopy(row)
        legacy_row["implementation_notes_json"] = json.dumps(
            {"notes": ["Legacy prose-only research"]},
            ensure_ascii=False,
            separators=(",", ":"),
        )

        records = self.bridge._ea_factory_deep_research_records(
            [legacy_row],
            source_key="sheet-ea-research-pipeline-v1",
            strict=True,
        )

        self.assertEqual(len(records), 1)
        self.assertFalse(records[0]["buildReady"])
        self.assertIsNone(records[0]["eaImplementationBlueprint"])
        self.assertIsNone(records[0]["eaBlueprintDigest"])
        self.assertIn(
            "legacy_or_invalid_ea_blueprint",
            records[0]["readinessIssues"],
        )

    def test_non_ready_blueprint_archives_as_authoritative_factory_tombstone(self) -> None:
        _parsed, receipt, metrics = self.parse_and_project(
            self.non_ready_blueprint()
        )
        self.assertTrue(receipt["valid"], receipt)
        self.assertEqual(metrics["eaReadiness"]["status"], "needs_clarification")

        row, factory_rows = self.deep_rows_from_metrics(
            metrics,
            suffix="needs-clarification",
        )
        self.assertEqual(len(factory_rows), 1)
        self.assertEqual(row["verification_status"], "needs_clarification")
        self.assertIn("วิจัยใหม่", row["next_action"])
        implementation = json.loads(row["implementation_notes_json"])
        self.assertEqual(
            implementation["eaImplementationBlueprint"]["completeness"]["status"],
            "needs_clarification",
        )

        handoff_records = self.bridge._ea_factory_deep_research_records(
            [row],
            source_key="sheet-ea-research-non-ready-v2",
            strict=True,
        )
        self.assertEqual(len(handoff_records), 1)
        self.assertFalse(handoff_records[0]["buildReady"])
        self.assertEqual(
            handoff_records[0]["eaReadiness"]["status"],
            "needs_clarification",
        )
        self.assertIn(
            "ea_blueprint_needs_clarification",
            handoff_records[0]["readinessIssues"],
        )


if __name__ == "__main__":
    unittest.main()
