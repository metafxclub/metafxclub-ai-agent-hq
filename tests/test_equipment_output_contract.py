from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock


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
            "startedAt": "2026-08-22T12:00:00+07:00",
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
    def _trading_system_rows() -> tuple[list[dict], list[dict]]:
        families = ("trend_following", "breakout", "mean_reversion")
        systems: list[dict] = []
        evidence: list[dict] = []
        for index, family in enumerate(families, start=1):
            primary = f"https://source{index}.example.com/system-{index}"
            corroborating = f"https://proof{index}.example.org/system-{index}"
            evidence.extend([
                {"label": f"Primary {index}", "url": primary, "note": "Public strategy rules"},
                {"label": f"Proof {index}", "url": corroborating, "note": "Independent corroboration"},
            ])
            systems.append({
                "recordType": "trading_system",
                "systemName": f"Verified System {index}",
                "strategyFamily": family,
                "creatorOrTrader": {
                    "name": f"Public Author {index}",
                    "role": "author",
                    "status": "publicly_stated",
                    "sourceUrl": primary,
                },
                "publicUsers": [{"name": f"Public Trader {index}", "sourceUrl": corroborating}],
                "market": "Forex",
                "symbols": ["EURUSD"],
                "timeframes": ["H1"],
                "sessions": ["London"],
                "indicatorSettings": [],
                "setupConditions": ["Wait for the documented setup"],
                "entrySteps": [
                    {"stepNo": 1, "rule": "Confirm the setup", "sourceUrl": primary, "truthStatus": "fact"},
                    {"stepNo": 2, "rule": "Enter after confirmation", "sourceUrl": primary, "truthStatus": "fact"},
                ],
                "exitSteps": [
                    {"stepNo": 1, "rule": "Place the documented stop", "sourceUrl": primary, "truthStatus": "fact"},
                    {"stepNo": 2, "rule": "Exit at the target or signal", "sourceUrl": corroborating, "truthStatus": "fact"},
                ],
                "riskManagement": {
                    "positionSizing": "Fixed fractional sizing",
                    "stopLoss": "Beyond the invalidation level",
                    "takeProfit": "At the documented target",
                    "maxRiskPerTrade": "1 percent",
                    "maxOpenPositions": "1",
                    "dailyOrEquityStop": "Stop after two losses",
                    "recoveryMethod": "none",
                    "recoveryRules": [],
                    "sourceUrl": primary,
                    "truthStatus": "fact",
                },
                "tradeManagementSteps": [],
                "sourceTitle": f"System {index} rules",
                "sourceUrl": primary,
                "corroboratingUrls": [corroborating],
                "checkedAt": "2026-08-22T12:00:00+07:00",
                "verificationStatus": "verified",
                "suitableFor": ["Rule-based traders"],
                "risksAndLimitations": ["Market regimes can change"],
                "unknowns": [],
            })
        return systems, evidence

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

    def test_deep_research_profile_requires_every_exact_field_and_evidence_kind(self) -> None:
        required_fields = self.runner.TRADING_SYSTEM_RESEARCH_CONTRACT_FIELDS
        schema = self.runner.build_work_output_schema(
            7000,
            "trading_system_research",
        )
        contract_schema = schema["properties"]["contractFields"]
        self.assertEqual(contract_schema["minItems"], len(required_fields))
        self.assertEqual(contract_schema["maxItems"], len(required_fields))
        self.assertEqual(
            set(contract_schema["items"]["properties"]["field"]["enum"]),
            set(required_fields),
        )
        self.assertEqual(schema["properties"]["status"]["enum"], ["completed"])
        self.assertEqual(schema["properties"]["evidence"]["minItems"], 2)

        contract_fields = [
            {
                "field": field,
                "value": (
                    "2026-08-22T18:45:00+07:00"
                    if field == "checkedAt"
                    else '["https://one.example/rules","https://two.example/proof"]'
                    if field == "sourceLinks"
                    else "not_publicly_stated"
                    if field == "conflictingEvidence"
                    else f"verified {field}"
                ),
            }
            for field in required_fields
        ]
        payload = {
            "status": "completed",
            "summary": "วิจัยระบบที่ Backend ผูกไว้ครบแล้ว",
            "findings": ["แยก fact และ unknown แล้ว"],
            "nextSteps": ["นำกฎที่ครบไปทดสอบกับ OHLC"],
            "evidence": [
                {"label": "Rules", "url": "https://one.example/rules", "note": "Primary public rules"},
                {"label": "Proof", "url": "https://two.example/proof", "note": "Independent public proof"},
            ],
            "blockedCapability": "",
            "contractFields": contract_fields,
            "evidenceKinds": [
                "at_least_two_source_urls",
                "checked_at",
                "limitations",
            ],
        }
        parsed = self.runner.parse_work_result(
            json.dumps(payload, ensure_ascii=False),
            7000,
            "trading_system_research",
        )
        self.assertEqual(len(parsed["contractFields"]), len(required_fields))
        self.assertEqual(
            set(parsed["evidenceKinds"]),
            {"at_least_two_source_urls", "checked_at", "limitations"},
        )

        payload["contractFields"] = contract_fields[:-1]
        with self.assertRaisesRegex(ValueError, "every exact contract field once"):
            self.runner.parse_work_result(
                json.dumps(payload, ensure_ascii=False),
                7000,
                "trading_system_research",
            )

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
        self.assertIn("systems", result["missingFields"])
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

    def test_full_result_envelope_over_budget_fails_even_when_contract_values_fit(self) -> None:
        raw_result = {
            "status": "completed",
            "summary": "Verified daily research result with a bounded structured receipt.",
            "findings": ["The published result was checked against the cited primary source. " * 5],
            "nextSteps": ["Refresh the same market date after the next scheduled release. " * 4],
            "evidence": [
                {
                    "label": "Official statistical release",
                    "url": "https://example.gov/releases/daily-market-update",
                    "note": "Read-only verification of the published value and timestamp.",
                }
            ],
            "blockedCapability": "",
            "contractFields": [
                {"field": "first", "value": "a" * 9800},
                {"field": "second", "value": "b" * 9800},
            ],
            "evidenceKinds": [],
        }
        compact_result = json.dumps(
            raw_result,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        self.assertLessEqual(
            sum(len(item["value"]) for item in raw_result["contractFields"]),
            20000,
        )
        self.assertGreater(len(compact_result), 20000)

        with self.assertRaisesRegex(ValueError, "result envelope values exceed output limit"):
            self.runner.parse_work_result(compact_result, 20000)

        mission = self._mission_for_contract(
            output_fields=["first", "second"],
            evidence_required=[],
            action_id="full-result-envelope",
        )
        mission["budget"] = {"outputLimitChars": 20000}
        contract = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            raw_result,
        )
        self.assertFalse(contract["valid"])
        self.assertNotIn("__aggregate__", contract["oversizedFields"])
        self.assertIn("__result__", contract["oversizedFields"])
        self.assertGreater(contract["resultEnvelopeChars"], 20000)
        self.assertEqual(contract["resultEnvelopeLimitChars"], 20000)

    def test_full_result_budget_uses_compact_json_not_pretty_print_whitespace(self) -> None:
        raw_result = {
            "status": "completed",
            "summary": "A compact structured receipt remains within budget.",
            "findings": ["Verified the bounded payload."],
            "nextSteps": ["No follow-up action is required."],
            "evidence": [],
            "blockedCapability": "",
            "contractFields": [{"field": "payload", "value": "x" * 6000}],
            "evidenceKinds": [],
        }
        compact_result = json.dumps(
            raw_result,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        pretty_result = json.dumps(
            raw_result,
            ensure_ascii=False,
            indent=100,
        )
        self.assertLess(len(compact_result), 7000)
        self.assertGreater(len(pretty_result), 7000)

        parsed = self.runner.parse_work_result(pretty_result, 7000)
        self.assertEqual(parsed["structuredResultChars"], len(compact_result))

    def test_complete_declared_outputs_and_real_public_url_pass(self) -> None:
        mission, procedure = self._mission()
        systems, evidence = self._trading_system_rows()
        fields = [{"field": "systems", "value": json.dumps(systems, ensure_ascii=False)}]
        result = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            {
                "contractFields": fields,
                "evidenceKinds": list(procedure["evidenceRequired"]),
                "evidence": evidence,
            },
        )
        self.assertTrue(result["valid"])
        self.assertEqual(result["missingFields"], [])
        self.assertEqual(result["missingEvidenceKinds"], [])
        self.assertEqual(result["sourceUrlCount"], 6)
        normalized = json.loads(result["values"]["systems"])
        self.assertEqual(len(normalized), 3)
        self.assertEqual({item["strategyFamily"] for item in normalized}, set(("trend_following", "breakout", "mean_reversion")))
        self.assertTrue(all(item["duplicateFingerprint"] for item in normalized))

    def test_trading_system_profile_converts_direct_systems_then_backend_accepts(self) -> None:
        mission, procedure = self._mission()
        mission["budget"] = {"outputLimitChars": 20000}
        systems, evidence = self._trading_system_rows()
        compact_systems = json.dumps(
            systems,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        payload = {
            "status": "completed",
            "summary": "ตรวจระบบเทรดสาธารณะครบสามระบบแล้ว",
            "findings": [],
            "nextSteps": [],
            "evidence": evidence,
            "blockedCapability": "",
            "systems": systems,
            "evidenceKinds": list(procedure["evidenceRequired"]),
        }
        parsed = self.runner.parse_work_result(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            20000,
            "trading_system_discovery",
        )
        receipt = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            parsed,
        )
        self.assertTrue(receipt["valid"], receipt)
        self.assertEqual(receipt["contractValueChars"], len(compact_systems))
        self.assertEqual(receipt["contractFieldLimitChars"], 16000)
        self.assertLess(len(receipt["values"]["systems"]), 12000)

    def test_backend_keeps_13000_character_legacy_system_field_compatibility(self) -> None:
        mission, procedure = self._mission()
        mission["budget"] = {"outputLimitChars": 20000}
        systems, evidence = self._trading_system_rows()
        compact_systems = json.dumps(
            systems,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        padded_systems = "[" + (" " * (13000 - len(compact_systems))) + compact_systems[1:]
        receipt = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            {
                "summary": "legacy compatibility",
                "findings": [],
                "nextSteps": [],
                "evidence": evidence,
                "contractFields": [{"field": "systems", "value": padded_systems}],
                "evidenceKinds": list(procedure["evidenceRequired"]),
            },
        )

        self.assertTrue(receipt["valid"], receipt)
        self.assertEqual(receipt["contractValueChars"], 13000)
        self.assertEqual(receipt["contractFieldLimitChars"], 16000)

    def test_trading_system_receipt_over_8000_chars_keeps_full_value_and_projects_array(self) -> None:
        mission, procedure = self._mission()
        mission["budget"] = {"outputLimitChars": 20000}
        systems, evidence = self._trading_system_rows()
        for system_index, system in enumerate(systems, start=1):
            system["setupConditions"] = [
                f"Setup {system_index}.{index}: " + ("documented condition " * 8)
                for index in range(1, 7)
            ]
            system["suitableFor"] = [
                f"Trader profile {system_index}.{index}: " + ("rule based workflow " * 4)
                for index in range(1, 6)
            ]
            system["risksAndLimitations"] = [
                f"Risk {system_index}.{index}: " + ("market regime limitation " * 5)
                for index in range(1, 7)
            ]
        result = self._result(
            fields={"systems": systems},
            evidence_kinds=list(procedure["evidenceRequired"]),
            evidence=evidence,
        )
        receipt = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            result,
        )

        self.assertTrue(receipt["valid"], receipt)
        self.assertGreater(len(receipt["values"]["systems"]), 8000)
        self.assertLessEqual(len(receipt["values"]["systems"]), 16000)
        projected = self.bridge.dashboard_workflow_output_metrics(receipt)
        self.assertIsInstance(projected["systems"], list)
        self.assertEqual(len(projected["systems"]), 3)

    def test_legacy_trading_system_projection_is_bound_to_receipts_and_two_run_artifacts(self) -> None:
        mission, _procedure = self._mission()
        systems, evidence = self._trading_system_rows()
        for system_index, system in enumerate(systems, start=1):
            system["setupConditions"] = [
                f"Setup {system_index}.{index}: " + ("documented condition " * 8)
                for index in range(1, 7)
            ]
            system["suitableFor"] = [
                f"Trader profile {system_index}.{index}: " + ("rule based workflow " * 4)
                for index in range(1, 6)
            ]
            system["risksAndLimitations"] = [
                f"Risk {system_index}.{index}: " + ("market regime limitation " * 5)
                for index in range(1, 7)
            ]
        normalized, errors = self.bridge._normalize_trading_system_contract_rows(
            mission,
            {},
            evidence,
            systems,
            existing_fingerprints_override=set(),
        )
        self.assertEqual(errors, [])
        canonical = json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        raw_systems = json.dumps(
            systems,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        self.assertGreater(len(canonical), 8000)
        self.assertLessEqual(len(canonical), 16000)
        self.assertLessEqual(len(raw_systems), 16000)
        prefix = canonical[:8000]
        urls = [row["url"] for row in evidence]
        run_id = "run-legacy-recovery"
        report_id = "report-legacy-recovery"
        artifact_reference = f"data/runtime/codex-runs/{run_id}.final.md"
        manifest_reference = (
            f"data/runtime/codex-runs/{run_id}.url-open-verification.json"
        )
        receipt = {
            "applicable": True,
            "valid": True,
            "procedureId": self.bridge.TRADING_SYSTEM_WORKFLOW_PROCEDURE_ID,
            "providedFields": ["systems"],
            "values": {"systems": prefix},
            "missingFields": [],
            "entryErrors": [],
            "oversizedFields": [],
            "contractValueChars": len(raw_systems),
            "sourceUrlCount": 6,
        }
        mission.update({
            "status": "completed",
            "phase": "auto_guarded_completed",
            "workStatus": "completed",
            "targetId": "codex_mcp_portal",
            "toolId": "codex_web_research",
            "requiresHumanApproval": False,
            "approval": {"required": False, "state": "not_required"},
            "reportIds": [report_id],
            "artifactPath": artifact_reference,
            "workflowOutputContract": receipt,
            "execution": {
                "workingDirectory": "workspace",
                "writeRoots": [],
                "controlPlaneWritable": False,
                "webSearchEnabled": True,
                "webSearchUsed": True,
                "webSearchEvidenceVerified": True,
                "correctiveOpenVerificationReceipt": {
                    "manifestArtifact": manifest_reference,
                },
            },
        })
        report = {
            "id": report_id,
            "type": "trading_system_discovery_report",
            "status": "ready",
            "linkedMissionId": mission["id"],
            "linkedPropId": "codex_mcp_portal",
            "metrics": {"systems": prefix, "workflowOutput": receipt},
            "evidence": evidence,
            "artifacts": [artifact_reference],
        }

        def stdout_event(payload_systems: list[dict]) -> str:
            payload = {
                "status": "completed",
                "systems": payload_systems,
                "evidence": evidence,
            }
            return json.dumps({
                "type": "item.completed",
                "item": {
                    "id": "item-1",
                    "type": "agent_message",
                    "text": json.dumps(
                        payload,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                },
            }, ensure_ascii=False, separators=(",", ":"))

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runtime = root / "data" / "runtime"
            run_dir = runtime / "codex-runs"
            run_dir.mkdir(parents=True)
            final_path = run_dir / f"{run_id}.final.md"
            stdout_path = run_dir / f"{run_id}.stdout.log"
            final_path.write_text(
                f"1. status\ncompleted\n\n- systems: {raw_systems}\n",
                encoding="utf-8",
            )
            stdout_path.write_text(stdout_event(systems) + "\n", encoding="utf-8")
            patches = (
                mock.patch.object(self.bridge, "PROJECT_ROOT", root),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime),
                mock.patch.object(self.bridge, "find_mission", return_value=mission),
                mock.patch.object(
                    self.bridge,
                    "_trading_system_required_open_urls_for_mission",
                    return_value=(urls, None),
                ),
                mock.patch.object(
                    self.bridge,
                    "_stored_trading_system_open_receipt_valid",
                    return_value=True,
                ),
            )
            with patches[0], patches[1], patches[2], patches[3], patches[4]:
                recovered = self.bridge._trading_system_report_recovered_systems(
                    report
                )
                self.assertEqual(
                    [item["systemName"] for item in recovered or []],
                    ["Verified System 1", "Verified System 2", "Verified System 3"],
                )
                projected = self.bridge.report_read_model_item(report)
                self.assertIsInstance(projected["metrics"]["systems"], list)
                self.assertEqual(len(projected["metrics"]["systems"]), 3)

                # A valid same-length suffix rewrite fails because the separate
                # stdout payload still contains the original full value.
                suffix_tamper = json.loads(raw_systems)
                suffix_tamper[-1]["risksAndLimitations"][-1] = (
                    suffix_tamper[-1]["risksAndLimitations"][-1][:-1] + "X"
                )
                tampered_raw = json.dumps(
                    suffix_tamper,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                self.assertEqual(len(tampered_raw), len(raw_systems))
                final_path.write_text(
                    f"1. status\ncompleted\n\n- systems: {tampered_raw}\n",
                    encoding="utf-8",
                )
                self.assertIsNone(
                    self.bridge._trading_system_report_recovered_systems(report)
                )

                # Changing both run artifacts in the persisted prefix still
                # fails against the three independent 8k receipt copies.
                prefix_tamper = json.loads(raw_systems)
                prefix_tamper[0]["systemName"] = "Verified Systen 1"
                tampered_raw = json.dumps(
                    prefix_tamper,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                self.assertEqual(len(tampered_raw), len(raw_systems))
                final_path.write_text(
                    f"1. status\ncompleted\n\n- systems: {tampered_raw}\n",
                    encoding="utf-8",
                )
                stdout_path.write_text(
                    stdout_event(prefix_tamper) + "\n",
                    encoding="utf-8",
                )
                self.assertIsNone(
                    self.bridge._trading_system_report_recovered_systems(report)
                )

                final_path.write_text(
                    f"1. status\ncompleted\n\n- systems: {raw_systems}\n",
                    encoding="utf-8",
                )
                stdout_path.write_text(stdout_event(systems) + "\n", encoding="utf-8")
                mission["execution"]["correctiveOpenVerificationReceipt"][
                    "manifestArtifact"
                ] = "data/runtime/codex-runs/run-other.url-open-verification.json"
                self.assertIsNone(
                    self.bridge._trading_system_report_recovered_systems(report)
                )

    def test_trading_system_contract_rejects_ea_records_and_low_diversity(self) -> None:
        mission, procedure = self._mission()
        systems, evidence = self._trading_system_rows()
        systems[0]["recordType"] = "ea"
        invalid_kind = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"systems": systems},
                evidence_kinds=list(procedure["evidenceRequired"]),
                evidence=evidence,
            ),
        )
        self.assertFalse(invalid_kind["valid"])
        self.assertIn("system_1_not_trading_system", invalid_kind["entryErrors"])

        systems, evidence = self._trading_system_rows()
        for system in systems:
            system["strategyFamily"] = "breakout"
        low_diversity = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"systems": systems},
                evidence_kinds=list(procedure["evidenceRequired"]),
                evidence=evidence,
            ),
        )
        self.assertFalse(low_diversity["valid"])
        self.assertIn("strategy_family_diversity_too_low", low_diversity["entryErrors"])

    def test_trading_system_contract_requires_real_public_creator_and_ordered_steps(self) -> None:
        mission, procedure = self._mission()
        systems, evidence = self._trading_system_rows()
        systems[0]["creatorOrTrader"] = {
            "name": None,
            "role": "author",
            "status": "publicly_stated",
            "sourceUrl": systems[0]["sourceUrl"],
        }
        missing_identity = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"systems": systems},
                evidence_kinds=list(procedure["evidenceRequired"]),
                evidence=evidence,
            ),
        )
        self.assertFalse(missing_identity["valid"])
        self.assertIn("system_1_invalid_creator_truth", missing_identity["entryErrors"])

        systems, evidence = self._trading_system_rows()
        systems[0]["creatorOrTrader"]["name"] = "unknown creator"
        placeholder_identity = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"systems": systems},
                evidence_kinds=list(procedure["evidenceRequired"]),
                evidence=evidence,
            ),
        )
        self.assertFalse(placeholder_identity["valid"])
        self.assertIn("system_1_invalid_creator_truth", placeholder_identity["entryErrors"])

        systems, evidence = self._trading_system_rows()
        systems[0]["creatorOrTrader"]["sourceUrl"] = systems[1]["sourceUrl"]
        wrong_system_source = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"systems": systems},
                evidence_kinds=list(procedure["evidenceRequired"]),
                evidence=evidence,
            ),
        )
        self.assertFalse(wrong_system_source["valid"])
        self.assertIn("system_1_invalid_creator_truth", wrong_system_source["entryErrors"])

        systems, evidence = self._trading_system_rows()
        systems[1]["entrySteps"][1]["stepNo"] = 3
        unordered = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"systems": systems},
                evidence_kinds=list(procedure["evidenceRequired"]),
                evidence=evidence,
            ),
        )
        self.assertFalse(unordered["valid"])
        self.assertIn("system_2_invalid_rules", unordered["entryErrors"])

    def test_trading_system_contract_rejects_source_not_present_in_evidence(self) -> None:
        mission, procedure = self._mission()
        systems, evidence = self._trading_system_rows()
        systems[2]["exitSteps"][0]["sourceUrl"] = "https://missing.example.net/rule"
        result = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"systems": systems},
                evidence_kinds=list(procedure["evidenceRequired"]),
                evidence=evidence,
            ),
        )
        self.assertFalse(result["valid"])
        self.assertIn("system_3_invalid_rules", result["entryErrors"])

    def test_trading_system_contract_requires_exactly_six_unique_evidence_urls(self) -> None:
        mission, procedure = self._mission()
        systems, evidence = self._trading_system_rows()
        evidence.append({
            "label": "Unused seventh source",
            "url": "https://unused.example.net/system",
            "note": "This source is not mapped to a trading system",
        })
        result = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"systems": systems},
                evidence_kinds=list(procedure["evidenceRequired"]),
                evidence=evidence,
            ),
        )
        self.assertFalse(result["valid"])
        self.assertIn(
            "trading_system_evidence_urls_count_not_6",
            result["entryErrors"],
        )

    def test_trading_system_contract_requires_one_distinct_corroborating_url(self) -> None:
        mission, procedure = self._mission()
        systems, evidence = self._trading_system_rows()
        systems[0]["corroboratingUrls"] = []
        missing = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"systems": systems},
                evidence_kinds=list(procedure["evidenceRequired"]),
                evidence=evidence,
            ),
        )
        self.assertFalse(missing["valid"])
        self.assertIn(
            "system_1_corroborating_url_count_not_1",
            missing["entryErrors"],
        )

        systems, evidence = self._trading_system_rows()
        systems[0]["corroboratingUrls"] = [systems[0]["sourceUrl"]]
        repeated = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"systems": systems},
                evidence_kinds=list(procedure["evidenceRequired"]),
                evidence=evidence,
            ),
        )
        self.assertFalse(repeated["valid"])
        self.assertIn("system_1_source_urls_not_distinct", repeated["entryErrors"])

    def test_trading_system_contract_requires_independent_source_hostnames(self) -> None:
        mission, procedure = self._mission()
        systems, evidence = self._trading_system_rows()
        old_url = systems[0]["corroboratingUrls"][0]
        same_host_url = "https://source1.example.com/independent-copy"
        systems[0]["corroboratingUrls"] = [same_host_url]
        systems[0]["publicUsers"][0]["sourceUrl"] = same_host_url
        systems[0]["exitSteps"][1]["sourceUrl"] = same_host_url
        for row in evidence:
            if row["url"] == old_url:
                row["url"] = same_host_url
        result = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"systems": systems},
                evidence_kinds=list(procedure["evidenceRequired"]),
                evidence=evidence,
            ),
        )
        self.assertFalse(result["valid"])
        self.assertIn(
            "system_1_source_hosts_not_independent",
            result["entryErrors"],
        )

    def test_trading_system_contract_requires_exact_evidence_mapping(self) -> None:
        mission, procedure = self._mission()
        systems, evidence = self._trading_system_rows()
        systems[2]["sourceUrl"] = systems[1]["sourceUrl"]
        systems[2]["corroboratingUrls"] = list(systems[1]["corroboratingUrls"])
        systems[2]["creatorOrTrader"]["sourceUrl"] = systems[1]["sourceUrl"]
        result = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"systems": systems},
                evidence_kinds=list(procedure["evidenceRequired"]),
                evidence=evidence,
            ),
        )
        self.assertFalse(result["valid"])
        self.assertIn(
            "trading_system_evidence_url_mapping_mismatch",
            result["entryErrors"],
        )

    def test_trading_system_contract_rejects_checked_at_before_mission_start(self) -> None:
        mission, procedure = self._mission()
        mission_started_at = datetime.now().astimezone() - timedelta(minutes=1)
        stale_checked_at = mission_started_at - timedelta(minutes=6)
        mission["startedAt"] = mission_started_at.isoformat()
        systems, evidence = self._trading_system_rows()
        for system in systems:
            system["checkedAt"] = stale_checked_at.isoformat()
        result = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"systems": systems},
                evidence_kinds=list(procedure["evidenceRequired"]),
                evidence=evidence,
            ),
        )
        self.assertFalse(result["valid"])
        self.assertIn("system_1_checked_at_stale", result["entryErrors"])
        self.assertIn("system_2_checked_at_stale", result["entryErrors"])
        self.assertIn("system_3_checked_at_stale", result["entryErrors"])

    def test_trading_system_contract_accepts_checked_at_within_mission_clock_skew(self) -> None:
        mission, procedure = self._mission()
        mission_started_at = datetime.now().astimezone() - timedelta(minutes=1)
        fresh_checked_at = mission_started_at - timedelta(minutes=4)
        mission["startedAt"] = mission_started_at.isoformat()
        systems, evidence = self._trading_system_rows()
        for system in systems:
            system["checkedAt"] = fresh_checked_at.isoformat()
        result = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            self._result(
                fields={"systems": systems},
                evidence_kinds=list(procedure["evidenceRequired"]),
                evidence=evidence,
            ),
        )
        self.assertTrue(result["valid"], result)

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
            "checked_at": {"checkedAt", "entries", "systems"},
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
                "systems",
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
                "systems",
            },
            "rejection_criteria": {"rejectionCriteria"},
            "review_scope": {"issues", "lineReferences", "reviewScope"},
            "scheduler_state": {"effectiveEnabled", "nextRunAt", "lastRunStatus"},
            "source_digest": {"sourceDigest"},
            "source_title": {"sourceTitle", "entries", "systems"},
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
