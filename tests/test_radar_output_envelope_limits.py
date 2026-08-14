from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
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


class RadarOutputEnvelopeLimitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module("radar_output_limit_bridge", BRIDGE_PATH)
        cls.runner = load_module("radar_output_limit_runner", RUNNER_PATH)

    @staticmethod
    def compact(payload: dict) -> str:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def minimal_payload(value: str) -> dict:
        return {
            "status": "completed",
            "summary": "ok",
            "findings": [],
            "nextSteps": [],
            "evidence": [],
            "blockedCapability": "",
            "contractFields": [{"field": "entries", "value": value}],
            "evidenceKinds": [],
        }

    def test_contract_field_accepts_12000_and_rejects_12001_explicitly(self) -> None:
        accepted = self.runner.parse_work_result(
            self.compact(self.minimal_payload("x" * 12000)),
            20000,
            "radar_website_tool",
        )
        self.assertEqual(len(accepted["contractFields"][0]["value"]), 12000)

        with self.assertRaisesRegex(
            ValueError,
            "contractFields exceed output limit",
        ):
            self.runner.parse_work_result(
                self.compact(self.minimal_payload("x" * 12001)),
                20000,
                "radar_website_tool",
            )

    def envelope_payload(self, target_chars: int) -> dict:
        payload = {
            "status": "completed",
            "summary": "S" * 3000,
            "findings": ["F" * 4000, ""],
            "nextSteps": [],
            "evidence": [],
            "blockedCapability": "",
            "contractFields": [{"field": "blob", "value": "V" * 12000}],
            "evidenceKinds": [],
        }
        base_length = len(self.compact(payload))
        delta = target_chars - base_length
        if not 1 <= delta <= 4000:
            raise AssertionError((target_chars, base_length, delta))
        payload["findings"][1] = "G" * delta
        self.assertEqual(len(self.compact(payload)), target_chars)
        return payload

    def backend_generic_mission(self) -> dict:
        return {
            "id": "mission-envelope-boundary",
            "budget": {"outputLimitChars": 20000},
            "workflowContext": {
                "schemaVersion": "dashboard-workflow-lineage-v1",
                "propId": "left_server_racks",
                "actionId": "research_selected_system",
                "coordinationMode": self.bridge.DASHBOARD_WORKFLOW_COORDINATION_MODE,
                "source": None,
                "agentTransfer": None,
                "inputs": {},
                "inputDigest": "0" * 64,
                "submittedAt": "2026-08-14T00:00:00Z",
                "triggerSource": "backend",
                "pluginProcedure": {
                    "pluginSkillId": "test-envelope-procedure",
                    "procedureKind": "backend_procedure",
                    "outputFields": ["blob"],
                    "evidenceRequired": [],
                },
            },
        }

    def test_complete_envelope_accepts_20000_and_rejects_20001_runner_and_backend(self) -> None:
        exact_payload = self.envelope_payload(20000)
        exact = self.runner.parse_work_result(
            self.compact(exact_payload),
            20000,
            "general",
        )
        self.assertEqual(exact["structuredResultChars"], 20000)

        too_large_payload = json.loads(json.dumps(exact_payload))
        too_large_payload["findings"][1] += "x"
        self.assertEqual(len(self.compact(too_large_payload)), 20001)
        with self.assertRaisesRegex(ValueError, "envelope values exceed output limit"):
            self.runner.parse_work_result(
                self.compact(too_large_payload),
                20000,
                "general",
            )

        exact_backend = self.bridge.validate_dashboard_workflow_output_contract(
            self.backend_generic_mission(),
            exact,
        )
        self.assertTrue(exact_backend["valid"], exact_backend)
        self.assertEqual(exact_backend["resultEnvelopeChars"], 20000)

        too_large_backend_result = {
            **exact,
            "findings": [*exact["findings"][:-1], exact["findings"][-1] + "x"],
            "structuredResultChars": 20001,
        }
        rejected_backend = self.bridge.validate_dashboard_workflow_output_contract(
            self.backend_generic_mission(),
            too_large_backend_result,
        )
        self.assertFalse(rejected_backend["valid"])
        self.assertIn("__result__", rejected_backend["oversizedFields"])
        self.assertIn("__runner_result__", rejected_backend["oversizedFields"])

    def maximum_radar_entries(self) -> list[dict]:
        prefix = "https://example.com/"
        entries = []
        for index in range(6):
            source_url = prefix + str(index) + "x" * (320 - len(prefix) - 1)
            entries.append({
                "toolName": str(index) + "T" * 79,
                "toolKind": "indicator",
                "platform": "tradingview",
                "category": "C" * 40,
                "version": "V" * 32,
                "summaryTh": "S" * 240,
                "sourceTitle": "D" * 120,
                "sourceUrl": source_url,
                "publishedAt": "2026-08-14T08:55:00+07:00",
                "checkedAt": "2026-08-14T09:00:00+07:00",
                "verificationStatus": "partially_verified",
                "availability": "public",
                "eaReadiness": "needs_clarification",
                "missingRules": ["M" * 80, "N" * 80],
                "sourceLimitations": ["L" * 120, "Q" * 120],
                "screenshot": {
                    "available": False,
                    "status": "not_available",
                    "attachmentId": None,
                    "artifactRef": None,
                },
            })
        return entries

    def radar_mission(self) -> dict:
        procedure = self.bridge.equipment_action_profile(
            "left_audit_crystals",
            "discover_new_indicators",
        )
        return {
            "id": "mission-radar-true-maximum",
            "budget": {"outputLimitChars": 20000},
            "workflowContext": {
                "schemaVersion": "dashboard-workflow-lineage-v1",
                "propId": "left_audit_crystals",
                "actionId": "discover_new_indicators",
                "coordinationMode": self.bridge.DASHBOARD_WORKFLOW_COORDINATION_MODE,
                "source": None,
                "agentTransfer": None,
                "inputs": {"maxItems": 6},
                "inputDigest": "0" * 64,
                "submittedAt": "2026-08-14T00:00:00Z",
                "triggerSource": "backend",
                "pluginProcedure": procedure,
            },
        }

    def test_true_declared_six_entry_maximum_fits_both_limits(self) -> None:
        entries = self.maximum_radar_entries()
        entries_json = json.dumps(
            entries,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        evidence = [
            {
                "label": "E" * 120,
                "url": entry["sourceUrl"],
                "note": "N" * 160,
            }
            for entry in entries
        ]
        payload = {
            "status": "completed",
            "summary": "S" * 500,
            "findings": ["F" * 240] * 4,
            "nextSteps": ["N" * 240] * 3,
            "evidence": evidence,
            "blockedCapability": "",
            "contractFields": [{"field": "entries", "value": entries_json}],
            "evidenceKinds": [
                "source_url",
                "source_title",
                "checked_at",
                "ea_readiness",
                "public_availability_status",
            ],
        }
        raw = self.compact(payload)
        self.assertLessEqual(len(entries_json), 12000)
        self.assertLessEqual(len(raw), 20000)
        parsed = self.runner.parse_work_result(raw, 20000, "radar_website_tool")
        with mock.patch.object(
            self.bridge,
            "_radar_existing_catalog_fingerprints",
            return_value=set(),
        ):
            backend = self.bridge.validate_dashboard_workflow_output_contract(
                self.radar_mission(),
                parsed,
            )
        self.assertTrue(backend["valid"], backend)
        self.assertLessEqual(
            len(backend["values"]["entries"]),
            12000,
        )
        self.assertLessEqual(backend["resultEnvelopeChars"], 20000)

    def test_runner_command_enforces_read_only_without_add_dir_for_radar(self) -> None:
        commands: list[list[str]] = []

        def fake_chat(command, **_kwargs):
            commands.append([str(item) for item in command])
            return {
                "ok": False,
                "exitCode": 1,
                "durationMs": 1,
                "processStarted": True,
                "processTreeTerminated": False,
                "stdout": "",
                "stderr": "worker failed",
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            codex = root / "codex.exe"
            codex.write_bytes(b"")
            workspace = root / "workspace"
            extra = root / "docs"
            with mock.patch.object(self.runner, "CODEX_BIN", codex), mock.patch.object(
                self.runner,
                "CODEX_RUNS_DIR",
                root / "runs",
            ), mock.patch.object(
                self.runner,
                "AUTO_WORKSPACE_ROOT",
                workspace,
            ), mock.patch.object(
                self.runner,
                "AUTO_ADDITIONAL_WRITE_ROOTS",
                (extra,),
            ), mock.patch.object(
                self.runner,
                "AUTO_WRITE_ROOT_LABELS",
                ("workspace", "docs"),
            ), mock.patch.object(
                self.runner,
                "chat_status",
                return_value={"ok": True, "status": "ready"},
            ), mock.patch.object(
                self.runner,
                "run_chat_command",
                side_effect=fake_chat,
            ):
                radar = self.runner.run_codex(
                    "Research public indicators.",
                    "manager",
                    "mission-radar-command",
                    execution_mode="auto_guarded",
                    output_limit=20000,
                    read_only_work=True,
                    result_profile="radar_website_tool",
                )
                ordinary = self.runner.run_codex(
                    "Review workspace files.",
                    "manager",
                    "mission-workspace-command",
                    execution_mode="auto_guarded",
                )

        self.assertEqual(len(commands), 2)
        radar_command, ordinary_command = commands
        self.assertEqual(
            radar_command[radar_command.index("--sandbox") + 1],
            "read-only",
        )
        self.assertNotIn("--add-dir", radar_command)
        self.assertEqual(radar["requestedSandbox"], "read-only")
        self.assertEqual(radar["writeRoots"], [])
        self.assertEqual(
            ordinary_command[ordinary_command.index("--sandbox") + 1],
            "workspace-write",
        )
        self.assertIn("--add-dir", ordinary_command)
        self.assertEqual(ordinary["requestedSandbox"], "workspace-write")
        self.assertEqual(ordinary["writeRoots"], ["workspace", "docs"])


if __name__ == "__main__":
    unittest.main()
