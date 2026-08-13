from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
RUNNER_PATH = PROJECT_ROOT / "runner" / "codex_cli_runner.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EquipmentOutputContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module("metafx_equipment_output_bridge", BRIDGE_PATH)
        cls.runner = load_module("metafx_equipment_output_runner", RUNNER_PATH)

    def _mission(self) -> tuple[dict, dict]:
        procedure = self.bridge.equipment_action_profile(
            "codex_mcp_portal",
            "discover_trading_systems",
        )
        mission = {
            "id": "mission-output-contract-1",
            "workflowContext": {
                "schemaVersion": "dashboard-workflow-lineage-v1",
                "propId": "codex_mcp_portal",
                "actionId": "discover_trading_systems",
                "coordinationMode": self.bridge.DASHBOARD_WORKFLOW_COORDINATION_MODE,
                "source": None,
                "agentTransfer": None,
                "inputs": {},
                "inputDigest": "0" * 64,
                "submittedAt": self.bridge.utc_now(),
                "triggerSource": "schedule",
                "pluginProcedure": procedure,
            },
        }
        return mission, procedure

    def _mission_for_contract(
        self,
        *,
        output_fields: list[str],
        evidence_required: list[str],
        action_id: str = "semantic_evidence_test",
    ) -> dict:
        return {
            "id": f"mission-{action_id}",
            "workflowContext": {
                "schemaVersion": "dashboard-workflow-lineage-v1",
                "propId": "codex_mcp_portal",
                "actionId": action_id,
                "coordinationMode": self.bridge.DASHBOARD_WORKFLOW_COORDINATION_MODE,
                "source": None,
                "agentTransfer": None,
                "inputs": {},
                "inputDigest": "0" * 64,
                "submittedAt": self.bridge.utc_now(),
                "triggerSource": "schedule",
                "pluginProcedure": {
                    "pluginSkillId": "backend-semantic-evidence-test",
                    "pluginVersion": "backend-v1",
                    "procedureKind": "backend_procedure",
                    "outputFields": output_fields,
                    "evidenceRequired": evidence_required,
                },
            },
        }

    @staticmethod
    def _result(
        *,
        fields: dict[str, object] | None = None,
        evidence_kinds: list[str] | None = None,
        evidence: list[dict] | None = None,
        artifacts: dict | None = None,
    ) -> dict:
        result = {
            "contractFields": [
                {
                    "field": field,
                    "value": (
                        json.dumps(value, ensure_ascii=False, sort_keys=True)
                        if isinstance(value, (list, dict))
                        else str(value)
                    ),
                }
                for field, value in (fields or {}).items()
            ],
            "evidenceKinds": list(evidence_kinds or []),
            "evidence": list(evidence or []),
        }
        if artifacts is not None:
            result["artifacts"] = artifacts
        return result

    def test_runner_schema_requires_explicit_contract_and_evidence_declarations(self) -> None:
        schema = self.runner.build_work_output_schema(7000)
        self.assertIn("contractFields", schema["required"])
        self.assertIn("evidenceKinds", schema["required"])
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["properties"]["contractFields"]["items"]["properties"]["value"]["maxLength"],
            7000,
        )

        parsed = self.runner.parse_work_result(
            json.dumps(
                {
                    "status": "completed",
                    "summary": "ตรวจข้อมูลสาธารณะครบแล้ว",
                    "findings": ["พบระบบที่อธิบายกฎได้"],
                    "nextSteps": [],
                    "evidence": [
                        {
                            "label": "Public source",
                            "url": "https://example.com/system",
                            "note": "Read-only source",
                        }
                    ],
                    "blockedCapability": "",
                    "contractFields": [
                        {"field": "systemName", "value": "Example System"}
                    ],
                    "evidenceKinds": ["source_url"],
                },
                ensure_ascii=False,
            ),
            7000,
        )
        self.assertEqual(parsed["contractFields"][0]["field"], "systemName")
        self.assertEqual(parsed["evidenceKinds"], ["source_url"])

    def test_missing_declared_outputs_fail_closed(self) -> None:
        mission, procedure = self._mission()
        result = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            {
                "contractFields": [
                    {"field": "systemName", "value": "Only one field"}
                ],
                "evidenceKinds": [],
                "evidence": [],
            },
        )
        self.assertTrue(result["applicable"])
        self.assertFalse(result["valid"])
        self.assertIn("sourceUrl", result["missingFields"])
        self.assertIn("source_url", result["missingEvidenceKinds"])
        self.assertEqual(result["expectedFields"], procedure["outputFields"])

    def test_contract_value_over_budget_is_rejected_without_truncation(self) -> None:
        oversized = "x" * 7001
        raw_result = {
            "status": "completed",
            "summary": "Oversized contract value must fail closed.",
            "findings": [],
            "nextSteps": [],
            "evidence": [],
            "blockedCapability": "",
            "contractFields": [{"field": "payload", "value": oversized}],
            "evidenceKinds": [],
        }
        with self.assertRaisesRegex(ValueError, "exceed output limit"):
            self.runner.parse_work_result(
                json.dumps(raw_result, ensure_ascii=False),
                7000,
            )

        mission = self._mission_for_contract(
            output_fields=["payload"],
            evidence_required=[],
            action_id="oversized-contract-value",
        )
        direct_contract = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            raw_result,
        )
        self.assertFalse(direct_contract["valid"])
        self.assertEqual(direct_contract["missingFields"], ["payload"])
        self.assertIn("payload", direct_contract["oversizedFields"])
        self.assertIn("__aggregate__", direct_contract["oversizedFields"])

    def test_contract_field_aggregate_over_budget_fails_closed(self) -> None:
        raw_result = {
            "status": "completed",
            "summary": "Aggregate contract value must stay within the mission budget.",
            "findings": [],
            "nextSteps": [],
            "evidence": [],
            "blockedCapability": "",
            "contractFields": [
                {"field": "first", "value": "a" * 4000},
                {"field": "second", "value": "b" * 4000},
            ],
            "evidenceKinds": [],
        }
        with self.assertRaisesRegex(ValueError, "exceed output limit"):
            self.runner.parse_work_result(
                json.dumps(raw_result, ensure_ascii=False),
                7000,
            )

        mission = self._mission_for_contract(
            output_fields=["first", "second"],
            evidence_required=[],
            action_id="aggregate-contract-value",
        )
        contract = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            raw_result,
        )
        self.assertFalse(contract["valid"])
        self.assertIn("__aggregate__", contract["oversizedFields"])
        self.assertEqual(contract["contractValueLimitChars"], 7000)

    def test_complete_declared_outputs_and_real_public_url_pass(self) -> None:
        mission, procedure = self._mission()
        fields = [
            {
                "field": field,
                "value": (
                    "2026-08-09T01:23:45Z"
                    if field == "checkedAt"
                    else "https://example.com/system"
                    if field == "sourceUrl"
                    else f"verified:{field}"
                ),
            }
            for field in procedure["outputFields"]
        ]
        result = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            {
                "contractFields": fields,
                "evidenceKinds": list(procedure["evidenceRequired"]),
                "evidence": [
                    {
                        "label": "Primary public source",
                        "url": "https://example.com/system",
                        "note": "Checked read-only",
                    }
                ],
            },
        )
        self.assertTrue(result["valid"])
        self.assertEqual(result["missingFields"], [])
        self.assertEqual(result["missingEvidenceKinds"], [])
        self.assertEqual(result["sourceUrlCount"], 1)

    def test_duplicate_public_url_does_not_satisfy_two_source_requirement(self) -> None:
        mission = self._mission_for_contract(
            output_fields=[],
            evidence_required=["at_least_two_source_urls"],
            action_id="duplicate-source-check",
        )
        result = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                evidence_kinds=["at_least_two_source_urls"],
                evidence=[
                    {
                        "label": "Primary source",
                        "url": "https://example.com/research/system-a",
                        "note": "First citation",
                    },
                    {
                        "label": "Repeated source",
                        "url": "https://example.com/research/system-a",
                        "note": "The same URL must not count twice",
                    },
                ],
            ),
        )
        self.assertFalse(result["valid"])
        self.assertEqual(result["sourceUrlCount"], 1)
        self.assertIn("at_least_two_source_urls", result["missingEvidenceKinds"])

    def test_checked_at_requires_a_parseable_timestamp(self) -> None:
        mission = self._mission_for_contract(
            output_fields=["checkedAt"],
            evidence_required=["checked_at"],
            action_id="checked-at-check",
        )
        invalid = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"checkedAt": "checked sometime this morning"},
                evidence_kinds=["checked_at"],
            ),
        )
        valid = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"checkedAt": "2026-08-09T01:23:45Z"},
                evidence_kinds=["checked_at"],
            ),
        )
        self.assertFalse(invalid["valid"])
        self.assertIn("checked_at", invalid["missingEvidenceKinds"])
        self.assertTrue(valid["valid"])

    def test_project_relative_source_path_must_exist_inside_project(self) -> None:
        mission = self._mission_for_contract(
            output_fields=["sourceFiles"],
            evidence_required=["project_relative_source_path"],
            action_id="project-source-path-check",
        )
        outside = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"sourceFiles": "../../Windows/System32/drivers/etc/hosts"},
                evidence_kinds=["project_relative_source_path"],
            ),
        )
        missing = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"sourceFiles": "workspace/does-not-exist/ghost.mq4"},
                evidence_kinds=["project_relative_source_path"],
            ),
        )
        absolute = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={
                    "sourceFiles": str((PROJECT_ROOT / "frontend" / "index.html").resolve())
                },
                evidence_kinds=["project_relative_source_path"],
            ),
        )
        existing = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"sourceFiles": "frontend/index.html"},
                evidence_kinds=["project_relative_source_path"],
            ),
        )
        self.assertFalse(outside["valid"])
        self.assertFalse(missing["valid"])
        self.assertFalse(absolute["valid"])
        self.assertTrue(existing["valid"])

    def test_project_relative_source_path_accepts_existing_runner_artifact(self) -> None:
        mission = self._mission_for_contract(
            output_fields=[],
            evidence_required=["project_relative_source_path"],
            action_id="project-artifact-path-check",
        )
        artifact_root = PROJECT_ROOT / "outputs"
        artifact_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="equipment-contract-test-",
            dir=artifact_root,
        ) as temp_dir:
            artifact = Path(temp_dir) / "verified-source-artifact.txt"
            artifact.write_text("read-only test artifact", encoding="utf-8")
            artifact_ref = artifact.relative_to(PROJECT_ROOT).as_posix()
            result = self.bridge.validate_dashboard_workflow_output_contract(
                mission,
                self._result(
                    evidence_kinds=["project_relative_source_path"],
                    artifacts={"final": artifact_ref},
                ),
            )
        self.assertTrue(result["valid"])

    def test_source_digest_requires_a_hex_digest(self) -> None:
        mission = self._mission_for_contract(
            output_fields=["sourceDigest"],
            evidence_required=["source_digest"],
            action_id="source-digest-check",
        )
        invalid = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"sourceDigest": "not-a-digest"},
                evidence_kinds=["source_digest"],
            ),
        )
        valid = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"sourceDigest": "a" * 64},
                evidence_kinds=["source_digest"],
            ),
        )
        self.assertFalse(invalid["valid"])
        self.assertIn("source_digest", invalid["missingEvidenceKinds"])
        self.assertTrue(valid["valid"])

    def test_28_pair_rows_requires_structured_unique_rows(self) -> None:
        mission = self._mission_for_contract(
            output_fields=["pairBias"],
            evidence_required=["28_pair_rows"],
            action_id="fx-pair-row-check",
        )
        pairs = [
            "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD",
            "EURGBP", "EURJPY", "EURCHF", "EURAUD", "EURNZD", "EURCAD",
            "GBPJPY", "GBPCHF", "GBPAUD", "GBPNZD", "GBPCAD",
            "AUDJPY", "AUDCHF", "AUDNZD", "AUDCAD",
            "NZDJPY", "NZDCHF", "NZDCAD",
            "CADJPY", "CADCHF", "CHFJPY",
        ]
        valid_rows = [
            {
                "pair": pair,
                "shortBias": "UNKNOWN",
                "mediumBias": "UNKNOWN",
                "longBias": "UNKNOWN",
            }
            for pair in pairs
        ]
        human_claim = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"pairBias": "Completed all 28 currency pairs"},
                evidence_kinds=["28_pair_rows"],
            ),
        )
        only_27 = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"pairBias": valid_rows[:27]},
                evidence_kinds=["28_pair_rows"],
            ),
        )
        repeated_pair = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"pairBias": [valid_rows[0] for _ in range(28)]},
                evidence_kinds=["28_pair_rows"],
            ),
        )
        fabricated_rows = [dict(row) for row in valid_rows]
        fabricated_rows[0]["pair"] = "AAAAAA"
        fabricated = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"pairBias": fabricated_rows},
                evidence_kinds=["28_pair_rows"],
            ),
        )
        complete_payload = self._result(
            fields={"pairBias": valid_rows},
            evidence_kinds=["28_pair_rows"],
        )
        self.assertLessEqual(
            len(complete_payload["contractFields"][0]["value"]),
            4000,
        )
        complete_payload.update(
            {
                "status": "completed",
                "summary": "Structured 28-pair evidence is ready.",
                "findings": [],
                "nextSteps": [],
                "blockedCapability": "",
            }
        )
        parsed_complete = self.runner.parse_work_result(
            json.dumps(complete_payload),
            7000,
        )
        complete = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            parsed_complete,
        )
        self.assertFalse(human_claim["valid"])
        self.assertFalse(only_27["valid"])
        self.assertFalse(repeated_pair["valid"])
        self.assertFalse(fabricated["valid"])
        self.assertTrue(complete["valid"])

    def test_supported_pair_bias_must_reference_matching_public_evidence(self) -> None:
        mission = self._mission_for_contract(
            output_fields=["pairBias", "sourceLinks"],
            evidence_required=["source_url_per_supported_bias"],
            action_id="fx-pair-source-check",
        )
        pairs = [
            "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD",
            "EURGBP", "EURJPY", "EURCHF", "EURAUD", "EURNZD", "EURCAD",
            "GBPJPY", "GBPCHF", "GBPAUD", "GBPNZD", "GBPCAD",
            "AUDJPY", "AUDCHF", "AUDNZD", "AUDCAD",
            "NZDJPY", "NZDCHF", "NZDCAD",
            "CADJPY", "CADCHF", "CHFJPY",
        ]
        rows = [
            {
                "pair": pair,
                "shortBias": "BULLISH" if pair == "EURUSD" else "UNKNOWN",
                "mediumBias": "UNKNOWN",
                "longBias": "UNKNOWN",
                "verified": pair == "EURUSD",
                "sourceRefs": ["public-1"] if pair == "EURUSD" else [],
                "allHorizonsEvidence": pair == "EURUSD",
            }
            for pair in pairs
        ]
        evidence = [{"label": "Public", "url": "https://example.com/fx", "note": "Checked"}]
        valid = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={
                    "pairBias": rows,
                    "sourceLinks": [{"id": "public-1", "url": "https://example.com/fx"}],
                },
                evidence_kinds=["source_url_per_supported_bias"],
                evidence=evidence,
            ),
        )
        wrong_reference = [dict(row) for row in rows]
        wrong_reference[0]["sourceRefs"] = ["missing"]
        invalid = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={
                    "pairBias": wrong_reference,
                    "sourceLinks": [{"id": "public-1", "url": "http://127.0.0.1/private"}],
                },
                evidence_kinds=["source_url_per_supported_bias"],
                evidence=evidence,
            ),
        )
        self.assertTrue(valid["valid"])
        self.assertFalse(invalid["valid"])
        self.assertIn("source_url_per_supported_bias", invalid["missingEvidenceKinds"])

    def test_pair_bias_requires_all_three_horizons_and_unknown_when_unverified(self) -> None:
        mission = self._mission_for_contract(
            output_fields=["pairBias"],
            evidence_required=["28_pair_rows", "unknown_when_unverified"],
            action_id="fx-pair-horizon-check",
        )
        pairs = [
            "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD",
            "EURGBP", "EURJPY", "EURCHF", "EURAUD", "EURNZD", "EURCAD",
            "GBPJPY", "GBPCHF", "GBPAUD", "GBPNZD", "GBPCAD",
            "AUDJPY", "AUDCHF", "AUDNZD", "AUDCAD",
            "NZDJPY", "NZDCHF", "NZDCAD", "CADJPY", "CADCHF", "CHFJPY",
        ]
        rows = [
            {
                "pair": pair,
                "shortBias": "UNKNOWN",
                "mediumBias": "UNKNOWN",
                "longBias": "UNKNOWN",
                "verified": False,
            }
            for pair in pairs
        ]
        missing_horizon = [dict(row) for row in rows]
        missing_horizon[0].pop("longBias")
        unsupported_claim = [dict(row) for row in rows]
        unsupported_claim[0]["shortBias"] = "BULLISH"
        invalid_shape = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"pairBias": missing_horizon},
                evidence_kinds=["28_pair_rows", "unknown_when_unverified"],
            ),
        )
        invalid_claim = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"pairBias": unsupported_claim},
                evidence_kinds=["28_pair_rows", "unknown_when_unverified"],
            ),
        )
        valid = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"pairBias": rows},
                evidence_kinds=["28_pair_rows", "unknown_when_unverified"],
            ),
        )
        self.assertFalse(invalid_shape["valid"])
        self.assertFalse(invalid_claim["valid"])
        self.assertIn("unknown_when_unverified", invalid_claim["missingEvidenceKinds"])
        self.assertTrue(valid["valid"])

    def test_valid_contract_values_feed_fx_bias_dashboard_read_model(self) -> None:
        mission = self._mission_for_contract(
            output_fields=["pairBias", "sourceLinks", "updatedAt"],
            evidence_required=["28_pair_rows", "source_url_per_supported_bias", "unknown_when_unverified", "updated_at"],
            action_id="build_fx_pair_bias",
        )
        mission["workflowContext"]["propId"] = "left_signal_cube"
        pairs = [
            "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD",
            "EURGBP", "EURJPY", "EURCHF", "EURAUD", "EURNZD", "EURCAD",
            "GBPJPY", "GBPCHF", "GBPAUD", "GBPNZD", "GBPCAD",
            "AUDJPY", "AUDCHF", "AUDNZD", "AUDCAD",
            "NZDJPY", "NZDCHF", "NZDCAD", "CADJPY", "CADCHF", "CHFJPY",
        ]
        rows = [
            {
                "pair": pair,
                "shortBias": "BULLISH" if pair == "EURUSD" else "UNKNOWN",
                "mediumBias": "NEUTRAL" if pair == "EURUSD" else "UNKNOWN",
                "longBias": "UNKNOWN",
                "confidence": 72 if pair == "EURUSD" else None,
                "verified": pair == "EURUSD",
                "sourceRefs": ["source-1"] if pair == "EURUSD" else [],
                "allHorizonsEvidence": pair == "EURUSD",
            }
            for pair in pairs
        ]
        result = self._result(
            fields={
                "pairBias": rows,
                "sourceLinks": [{"id": "source-1", "url": "https://example.com/fx", "checkedAt": "2026-08-09T00:00:00+00:00"}],
                "updatedAt": "2026-08-09T00:00:00+00:00",
            },
            evidence_kinds=["28_pair_rows", "source_url_per_supported_bias", "unknown_when_unverified", "updated_at"],
            evidence=[{"label": "Public FX evidence", "url": "https://example.com/fx", "note": "Checked"}],
        )
        self.assertGreater(len(result["contractFields"][0]["value"]), 4000)
        result.update({
            "status": "completed",
            "summary": "สร้าง Bias ครบ 28 คู่เงินพร้อมหลักฐานแล้ว",
            "findings": [],
            "nextSteps": [],
            "blockedCapability": "",
        })
        parsed_result = self.runner.parse_work_result(
            json.dumps(result, ensure_ascii=False),
            7000,
        )
        contract = self.bridge.validate_dashboard_workflow_output_contract(mission, parsed_result)
        malformed_time_result = self._result(
            fields={
                "pairBias": rows,
                "sourceLinks": [{"id": "source-1", "url": "https://example.com/fx"}],
                "updatedAt": "not-a-time",
            },
            evidence_kinds=["28_pair_rows", "source_url_per_supported_bias", "unknown_when_unverified", "updated_at"],
            evidence=[{"label": "Public FX evidence", "url": "https://example.com/fx", "note": "Checked"}],
        )
        malformed_time_contract = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            malformed_time_result,
        )
        metrics = self.bridge.dashboard_workflow_output_metrics(contract)
        report = {
            "id": "fx-bias-report-contract",
            "linkedPropId": "left_signal_cube",
            "type": "fx_news_bias_report",
            "status": "ready",
            "workflowContext": {"propId": "left_signal_cube", "actionId": "build_fx_pair_bias"},
            "metrics": metrics,
            "evidence": [{"label": "Public FX evidence", "url": "https://example.com/fx", "note": "Checked"}],
            "updatedAt": "2026-08-09T00:00:00+00:00",
        }
        model = self.bridge._fx_bias_read_model(
            [report],
            now_local=datetime.fromisoformat("2026-08-09T08:00:00+00:00"),
        )
        eurusd = next(row for row in model["pairs"] if row["pair"] == "EURUSD")
        self.assertTrue(contract["valid"])
        self.assertFalse(malformed_time_contract["valid"])
        self.assertIn("updated_at", malformed_time_contract["missingEvidenceKinds"])
        self.assertIsInstance(metrics["pairBias"], list)
        self.assertEqual(model["verifiedPairCount"], 1)
        self.assertEqual(eurusd["shortBias"], "bullish")
        self.assertEqual(eurusd["mediumBias"], "sideway")
        self.assertEqual(eurusd["sourceLinks"][0]["url"], "https://example.com/fx")

    def test_unknown_evidence_kind_fails_closed(self) -> None:
        mission = self._mission_for_contract(
            output_fields=[],
            evidence_required=["future_unverified_evidence_kind"],
            action_id="unknown-evidence-check",
        )
        result = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(evidence_kinds=["future_unverified_evidence_kind"]),
        )
        self.assertFalse(result["valid"])

    def test_contract_declares_only_reviewed_evidence_kinds(self) -> None:
        contract = json.loads(
            (PROJECT_ROOT / "contracts" / "workflows" / "equipment-plugin-map.json")
            .read_text(encoding="utf-8")
        )
        actual = {
            evidence_kind
            for equipment in contract["equipment"].values()
            for action in equipment["actions"].values()
            for evidence_kind in action.get("evidenceRequired", [])
        }
        reviewed = {
            "28_pair_rows",
            "acceptance_criteria",
            "adapter_status_truth",
            "at_least_two_source_urls",
            "backend_observed_at",
            "backtest_plan",
            "baseline_reference",
            "change_summary",
            "checked_at",
            "compile_status_truth",
            "discovery_blueprint",
            "ea_readiness",
            "inspection_scope",
            "limitations",
            "local_health_snapshot",
            "frontend_safe_candidate_registry",
            "local_settings_record",
            "local_terminal_selection_record",
            "no_unverified_profit_claim",
            "overfit_guard",
            "parameter_plan",
            "project_relative_source_path",
            "public_availability_status",
            "published_or_event_time",
            "quoted_fact_summary",
            "rejection_criteria",
            "review_scope",
            "scheduler_state",
            "source_digest",
            "source_reference",
            "source_title",
            "source_url",
            "source_url_per_supported_bias",
            "uncompiled_status",
            "unknown_when_unverified",
            "updated_at",
        }
        self.assertEqual(actual, reviewed)
        self.assertEqual(
            set(self.bridge.REVIEWED_DASHBOARD_WORKFLOW_EVIDENCE_KINDS),
            reviewed,
        )

    def test_every_mapped_evidence_kind_has_verifier_prerequisite(self) -> None:
        contract = json.loads(
            (PROJECT_ROOT / "contracts" / "workflows" / "equipment-plugin-map.json")
            .read_text(encoding="utf-8")
        )

        # These evidence kinds are verified from another structured channel,
        # not from contractFields: public evidence rows, trusted mission input,
        # or Backend-owned procedure metadata.
        non_output_evidence_sources = {
            "source_url": "result.evidence",
            "at_least_two_source_urls": "result.evidence",
            "source_reference": "workflowContext.inputs-or-source",
            "baseline_reference": "workflowContext.inputs-or-source",
            "adapter_status_truth": "pluginProcedure.adapterStatus",
        }

        # All other evidence kinds need at least one matching declared output
        # field so the semantic verifier can evaluate truth rather than trusting
        # the evidenceKinds label alone.
        required_any_output = {
            "28_pair_rows": {"pairBias"},
            "acceptance_criteria": {"acceptanceCriteria"},
            "backend_observed_at": {"checkedAt", "backendObservedAt"},
            "backtest_plan": {"testModel", "dateRange", "artifactPlan"},
            "change_summary": {"changeSummary"},
            "checked_at": {"checkedAt", "entries"},
            "compile_status_truth": {"compileStatus"},
            "discovery_blueprint": {"blueprint", "versionPlan"},
            "ea_readiness": {"eaReadiness", "entries"},
            "inspection_scope": {
                "strategySummary",
                "codeRisks",
                "tradeLifecycle",
                "moneyManagement",
            },
            "limitations": {
                "limitations",
                "knownRisks",
                "riskNotes",
                "conflictingEvidence",
            },
            "local_health_snapshot": {
                "bridgeStatus",
                "missionWorkerStatus",
                "schedulerStatus",
                "codexStatus",
            },
            "frontend_safe_candidate_registry": {"candidates", "candidateCount", "privacy"},
            "local_settings_record": {
                "savedAt",
                "times",
                "language",
                "requestedEnabled",
            },
            "local_terminal_selection_record": {
                "selectedCandidate",
                "selectedAt",
            },
            "no_unverified_profit_claim": {
                "expectedTradeoffs",
                "validationPlan",
                "rejectionCriteria",
            },
            "overfit_guard": {"overfitGuards", "validationSplit"},
            "parameter_plan": {"parameterRanges", "startStepStop", "nextRanges"},
            "project_relative_source_path": {
                "sourceFiles",
                "changedFiles",
                "sourcePath",
                "downloadArtifacts",
            },
            "public_availability_status": {"availability", "entries"},
            "published_or_event_time": {"publishedAt", "eventAt", "events", "sourceLinks"},
            "quoted_fact_summary": {
                "entryRules",
                "exitRules",
                "strategySummary",
                "featureSummary",
            },
            "rejection_criteria": {"rejectionCriteria"},
            "review_scope": {"issues", "lineReferences", "reviewScope"},
            "scheduler_state": {"effectiveEnabled", "nextRunAt", "lastRunStatus"},
            "source_digest": {"sourceDigest"},
            "source_title": {"sourceTitle", "entries"},
            "source_url_per_supported_bias": {"pairBias"},
            "uncompiled_status": {
                "compileChecklist",
                "compileStatus",
                "nextValidationStep",
            },
            "unknown_when_unverified": {"pairBias"},
            "updated_at": {"updatedAt"},
        }

        reviewed = set(self.bridge.REVIEWED_DASHBOARD_WORKFLOW_EVIDENCE_KINDS)
        verifier_policy = set(required_any_output) | set(non_output_evidence_sources)
        self.assertEqual(
            verifier_policy,
            reviewed,
            "Every reviewed evidence kind must declare where its verifier reads truth from.",
        )

        missing_prerequisites: list[str] = []
        for equipment_id, equipment in contract["equipment"].items():
            for action_id, action in equipment["actions"].items():
                output_fields = set(action.get("outputFields", []))
                for evidence_kind in action.get("evidenceRequired", []):
                    if evidence_kind in non_output_evidence_sources:
                        if evidence_kind == "adapter_status_truth" and not (
                            str(action.get("adapterStatus") or "").strip()
                            or "adapterStatus" in output_fields
                        ):
                            missing_prerequisites.append(
                                f"{equipment_id}.{action_id}:{evidence_kind} "
                                "needs pluginProcedure.adapterStatus or output adapterStatus"
                            )
                        if evidence_kind in {"source_reference", "baseline_reference"}:
                            action_registry = self.bridge.DASHBOARD_WORKFLOW_ACTIONS.get(
                                action_id,
                                {},
                            )
                            form_ids = {
                                str(field.get("id") or "")
                                for field in action_registry.get("formFields", [])
                                if isinstance(field, dict)
                            }
                            preset_keys = {
                                str(key)
                                for key in (action.get("inputPreset") or {})
                            }
                            reference_keys = form_ids | preset_keys
                            if not any(
                                any(
                                    token in key.lower()
                                    for token in ("source", "report", "artifact", "path")
                                )
                                for key in reference_keys
                            ):
                                missing_prerequisites.append(
                                    f"{equipment_id}.{action_id}:{evidence_kind} "
                                    "needs a source/report/artifact/path input"
                                )
                        continue
                    expected = required_any_output[evidence_kind]
                    if not output_fields.intersection(expected):
                        missing_prerequisites.append(
                            f"{equipment_id}.{action_id}:{evidence_kind} "
                            f"needs one of {sorted(expected)}"
                        )

        self.assertEqual(
            missing_prerequisites,
            [],
            "Mapped evidence cannot be completed because verifier prerequisite fields are absent:\n"
            + "\n".join(missing_prerequisites),
        )

    def test_parser_accepts_explicit_empty_contract_arrays_for_plain_mission(self) -> None:
        parsed = self.runner.parse_work_result(
            json.dumps(
                {
                    "status": "completed",
                    "summary": "Plain mission completed without an equipment contract.",
                    "findings": [],
                    "nextSteps": [],
                    "evidence": [],
                    "blockedCapability": "",
                    "contractFields": [],
                    "evidenceKinds": [],
                }
            ),
            7000,
        )
        self.assertEqual(parsed["contractFields"], [])
        self.assertEqual(parsed["evidenceKinds"], [])


if __name__ == "__main__":
    unittest.main()
