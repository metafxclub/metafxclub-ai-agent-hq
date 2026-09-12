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
RUNNER_PATH = ROOT / "runner" / "codex_cli_runner.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DeepResearchSemanticRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_module(
            "metafx_deep_research_semantic_repair_runner",
            RUNNER_PATH,
        )
        cls.brief_support = load_module(
            "metafx_deep_research_semantic_repair_brief_support",
            ROOT / "backend" / "local-runner" / "ea_strategy_brief.py",
        )

    @staticmethod
    def ready_brief(urls: list[str]) -> dict:
        return {
            "schemaVersion": "ea-strategy-brief/1.0.0",
            "systemName": "EMA Closed-Bar Crossover",
            "systemOverview": (
                "ระบบตามแนวโน้มสำหรับ Forex; ใช้ timeframe ที่ผู้ใช้เลือกใน EA "
                "และประเมินสัญญาณจากแท่งที่ปิดแล้ว"
            ),
            "entryRules": (
                "Buy เมื่อ EMA 10 แท่งที่ 2 ไม่มากกว่า EMA 60 และ EMA 10 "
                "แท่งที่ 1 มากกว่า EMA 60; Sell ใช้เงื่อนไขกลับกัน"
            ),
            "recoveryRules": "ไม่มีการแก้ไม้ ห้าม Grid, Martingale, Averaging และ Hedging",
            "exitRules": "ปิดด้วย SL, TP, trailing stop หรือสัญญาณตัดกลับตามค่าที่ผู้ใช้กำหนด",
            "moneyManagement": "รองรับ fixed lot และ risk percent โดยเปิดได้ครั้งละหนึ่ง position",
            "orderExecution": "ส่งคำสั่ง Buy/Sell แบบ market order หลังแท่งสัญญาณปิด",
            "displayRequirements": "แสดงชื่อระบบ สถานะสัญญาณ Balance, Equity และ Spread",
            "additionalNotes": "ค่า period, SL, TP และ trailing ต้องเป็น EA inputs",
            "sourceLinks": list(urls),
            "checkedAt": "2026-09-10T10:00:00+07:00",
            "limitations": ["เป็นข้อกำหนดสร้าง Source EA ไม่ใช่ผล Backtest"],
        }

    def payload(self, brief: dict, urls: list[str]) -> dict:
        brief = copy.deepcopy(brief)
        brief["sourceLinks"] = list(urls)
        return {
            "status": "completed",
            "summary": "The selected source record was expanded into a detailed Blueprint.",
            "findings": [],
            "nextSteps": [],
            "evidence": [
                {
                    "label": f"Bound source {index}",
                    "url": url,
                    "note": "Opened by the primary read-only research pass",
                }
                for index, url in enumerate(urls, start=1)
            ],
            "blockedCapability": "",
            "research": brief,
            "evidenceKinds": [
                "at_least_two_source_urls",
                "checked_at",
                "limitations",
                "source_digest",
            ],
        }

    @staticmethod
    def fake_result(urls: list[str]) -> dict:
        return {
            "ok": True,
            "exitCode": 0,
            "durationMs": 1,
            "processStarted": True,
            "processTreeTerminated": False,
            "stdout": "",
            "stderr": "",
            "nativeWebSearchUsed": True,
            "nativeWebSearchBroadSearchUsed": False,
            "nativeWebSearchOpenedUrls": list(urls),
        }

    def run_case(self, repaired_brief_is_valid: bool) -> tuple[dict, list[dict]]:
        urls = [
            "https://tradingfinder.com/education/trading-strategy/",
            "https://forex-station.com/strategy-library-t8475202.html",
        ]
        valid = self.ready_brief(urls)
        invalid = copy.deepcopy(valid)
        invalid["entryRules"] = ""
        primary_payload = self.payload(invalid, urls)
        repaired_payload = self.payload(
            valid if repaired_brief_is_valid else invalid,
            urls,
        )
        calls: list[dict] = []

        def fake_chat(command, **kwargs):
            command_values = [str(value) for value in command]
            calls.append({"command": command_values, "prompt": str(kwargs.get("stdin") or "")})
            output_path = Path(command_values[command_values.index("-o") + 1])
            output_path.write_text(
                json.dumps(
                    primary_payload if len(calls) == 1 else repaired_payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
            return self.fake_result(urls)

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
            self.runner,
            "CODEX_RUNS_DIR",
            Path(temp_dir),
        ), mock.patch.object(
            self.runner,
            "chat_status",
            return_value={"ok": True, "status": "ready"},
        ), mock.patch.object(
            self.runner,
            "run_chat_command",
            side_effect=fake_chat,
        ), mock.patch.object(
            self.runner,
            "require_fresh_corrective_verifier_quota",
            return_value={"ok": True},
        ):
            result = self.runner.run_codex(
                "Expand only the Backend-selected strategy record.",
                "mission_archivist",
                "mission-semantic-repair-valid"
                if repaired_brief_is_valid
                else "mission-semantic-repair-exhausted",
                timeout=240,
                output_limit=64_000,
                execution_mode="auto_guarded",
                web_search=True,
                read_only_work=True,
                result_profile="trading_system_research",
                required_open_urls=urls,
            )
        return result, calls

    def test_one_bounded_revision_repairs_semantics_without_new_search(self) -> None:
        result, calls = self.run_case(True)

        self.assertTrue(result["ok"], result)
        self.assertEqual(len(calls), 2)
        self.assertIn("--search", calls[0]["command"])
        self.assertNotIn("--search", calls[1]["command"])
        self.assertIn("compact-ea-safe-inputs-v2", calls[0]["prompt"])
        self.assertIn("StopLossPoints=300", calls[0]["prompt"])
        self.assertIn("TakeProfitPoints=600", calls[0]["prompt"])
        self.assertIn("FixedLot=0.01", calls[0]["prompt"])
        self.assertIn("RiskPercent=1.0", calls[0]["prompt"])
        self.assertIn("RecoveryMode=none", calls[0]["prompt"])
        self.assertEqual(
            calls[1]["command"][calls[1]["command"].index("--sandbox") + 1],
            "read-only",
        )
        self.assertIn("BRIEF_TEXT_REQUIRED", calls[1]["prompt"])
        self.assertIn("ORIGINAL_RESULT_JSON_BEGIN", calls[1]["prompt"])
        self.assertIn("compact-ea-safe-inputs-v2", calls[1]["prompt"])
        self.assertIn("StopLossPoints=300", calls[1]["prompt"])
        self.assertIn("TakeProfitPoints=600", calls[1]["prompt"])
        self.assertIn("FixedLot=0.01", calls[1]["prompt"])
        self.assertIn("RiskPercent=1.0", calls[1]["prompt"])
        self.assertIn("component by component", calls[1]["prompt"])
        self.assertTrue(result["semanticRepair"]["attempted"])
        self.assertTrue(result["semanticRepair"]["succeeded"])
        self.assertEqual(result["semanticRepair"]["attemptCount"], 1)
        self.assertEqual(result["semanticRepair"]["remainingIssues"], [])

    def test_invalid_revision_stops_after_one_attempt_and_exposes_issue_paths(self) -> None:
        result, calls = self.run_case(False)

        self.assertFalse(result["ok"], result)
        self.assertEqual(result["status"], "invalid_output")
        self.assertEqual(len(calls), 2)
        repair = result["semanticRepair"]
        self.assertTrue(repair["attempted"])
        self.assertFalse(repair["succeeded"])
        self.assertEqual(repair["attemptCount"], 1)
        self.assertTrue(repair["remainingIssues"])
        self.assertEqual(repair["remainingIssues"][0]["code"], "BRIEF_TEXT_REQUIRED")
        self.assertTrue(repair["remainingIssues"][0]["path"].startswith("$."))

    def test_optional_compact_fields_receive_safe_defaults_without_second_codex_call(self) -> None:
        urls = [
            "https://tradingfinder.com/education/trading-strategy/",
            "https://forex-station.com/strategy-library-t8475202.html",
        ]
        brief = self.ready_brief(urls)
        brief.pop("recoveryRules")
        brief.pop("displayRequirements")
        brief.pop("additionalNotes")
        brief.pop("limitations")
        brief["systemName"] = "  EMA Closed-Bar Crossover  "
        primary_payload = self.payload(brief, urls)
        calls: list[dict] = []

        def fake_chat(command, **kwargs):
            command_values = [str(value) for value in command]
            calls.append({"command": command_values, "prompt": str(kwargs.get("stdin") or "")})
            output_path = Path(command_values[command_values.index("-o") + 1])
            output_path.write_text(
                json.dumps(primary_payload, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
            return self.fake_result(urls)

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
            self.runner,
            "CODEX_RUNS_DIR",
            Path(temp_dir),
        ), mock.patch.object(
            self.runner,
            "chat_status",
            return_value={"ok": True, "status": "ready"},
        ), mock.patch.object(
            self.runner,
            "run_chat_command",
            side_effect=fake_chat,
        ), mock.patch.object(
            self.runner,
            "require_fresh_corrective_verifier_quota",
            return_value={"ok": True},
        ):
            result = self.runner.run_codex(
                "Expand only the Backend-selected strategy record.",
                "mission_archivist",
                "mission-common-drift-canonicalized",
                timeout=240,
                output_limit=64_000,
                execution_mode="auto_guarded",
                web_search=True,
                read_only_work=True,
                result_profile="trading_system_research",
                required_open_urls=urls,
            )

        self.assertTrue(result["ok"], result)
        self.assertEqual(len(calls), 1)
        self.assertFalse(result["semanticRepair"]["attempted"])
        brief_field = next(
            item for item in result["contractFields"] if item["field"] == "strategyBrief"
        )
        normalized = json.loads(brief_field["value"])
        self.assertEqual(normalized["systemName"], "EMA Closed-Bar Crossover")
        self.assertIn("RecoveryMode=none", normalized["recoveryRules"])
        self.assertIn("Balance", normalized["displayRequirements"])
        self.assertIn(
            self.runner.IMPLEMENTATION_DEFAULT_MARKER
            if hasattr(self.runner, "IMPLEMENTATION_DEFAULT_MARKER")
            else "IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT",
            normalized["additionalNotes"],
        )
        self.assertTrue(normalized["limitations"])

    def test_exact_runner_formatted_report_is_recovered_without_second_codex_call(self) -> None:
        urls = [
            "https://tradingfinder.com/education/trading-strategy/",
            "https://forex-station.com/strategy-library-t8475202.html",
        ]
        primary_payload = self.payload(self.ready_brief(urls), urls)
        parsed = self.runner.parse_work_result(
            json.dumps(primary_payload, ensure_ascii=False, separators=(",", ":")),
            64_000,
            "trading_system_research",
        )
        formatted_report = self.runner.format_work_report(parsed, 64_000)
        calls: list[list[str]] = []

        def fake_chat(command, **kwargs):
            command_values = [str(value) for value in command]
            calls.append(command_values)
            output_path = Path(command_values[command_values.index("-o") + 1])
            output_path.write_text(formatted_report, encoding="utf-8")
            return self.fake_result(urls)

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
            self.runner,
            "CODEX_RUNS_DIR",
            Path(temp_dir),
        ), mock.patch.object(
            self.runner,
            "chat_status",
            return_value={"ok": True, "status": "ready"},
        ), mock.patch.object(
            self.runner,
            "run_chat_command",
            side_effect=fake_chat,
        ):
            result = self.runner.run_codex(
                "Expand only the Backend-selected strategy record.",
                "mission_archivist",
                "mission-formatted-report-recovery",
                timeout=240,
                output_limit=64_000,
                execution_mode="auto_guarded",
                web_search=True,
                read_only_work=True,
                result_profile="trading_system_research",
                required_open_urls=urls,
            )

        self.assertTrue(result["ok"], result)
        self.assertEqual(len(calls), 1)
        self.assertTrue(result["formatRecovery"]["attempted"])
        self.assertTrue(result["formatRecovery"]["succeeded"])
        self.assertEqual(result["formatRecovery"]["attemptCount"], 1)
        self.assertEqual(
            result["formatRecovery"]["strategy"],
            "strict_renderer_round_trip",
        )
        self.assertFalse(result["semanticRepair"]["attempted"])
        self.assertEqual(
            {item["field"] for item in result["contractFields"]},
            set(self.runner.TRADING_SYSTEM_RESEARCH_CONTRACT_FIELDS),
        )

    def test_formatted_report_projection_tamper_fails_closed_without_retry(self) -> None:
        urls = [
            "https://tradingfinder.com/education/trading-strategy/",
            "https://forex-station.com/strategy-library-t8475202.html",
        ]
        primary_payload = self.payload(self.ready_brief(urls), urls)
        parsed = self.runner.parse_work_result(
            json.dumps(primary_payload, ensure_ascii=False, separators=(",", ":")),
            64_000,
            "trading_system_research",
        )
        formatted_report = self.runner.format_work_report(parsed, 64_000)
        source_digest = next(
            item["value"]
            for item in parsed["contractFields"]
            if item["field"] == "sourceDigest"
        )
        tampered_report = formatted_report.replace(
            f"- sourceDigest: {source_digest}",
            f"- sourceDigest: {'0' * 64}",
            1,
        )
        calls = 0

        def fake_chat(command, **kwargs):
            nonlocal calls
            calls += 1
            command_values = [str(value) for value in command]
            output_path = Path(command_values[command_values.index("-o") + 1])
            output_path.write_text(tampered_report, encoding="utf-8")
            return self.fake_result(urls)

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
            self.runner,
            "CODEX_RUNS_DIR",
            Path(temp_dir),
        ), mock.patch.object(
            self.runner,
            "chat_status",
            return_value={"ok": True, "status": "ready"},
        ), mock.patch.object(
            self.runner,
            "run_chat_command",
            side_effect=fake_chat,
        ):
            result = self.runner.run_codex(
                "Expand only the Backend-selected strategy record.",
                "mission_archivist",
                "mission-formatted-report-tamper",
                timeout=240,
                output_limit=64_000,
                execution_mode="auto_guarded",
                web_search=True,
                read_only_work=True,
                result_profile="trading_system_research",
                required_open_urls=urls,
            )

        self.assertFalse(result["ok"], result)
        self.assertEqual(result["status"], "invalid_output")
        self.assertEqual(calls, 1)
        self.assertTrue(result["formatRecovery"]["attempted"])
        self.assertFalse(result["formatRecovery"]["succeeded"])
        self.assertIn("canonical round trip", result["formatRecovery"]["error"])
        self.assertFalse(result["semanticRepair"]["attempted"])

    def test_formatted_report_recovery_rejects_noncanonical_wrappers(self) -> None:
        urls = [
            "https://tradingfinder.com/education/trading-strategy/",
            "https://forex-station.com/strategy-library-t8475202.html",
        ]
        payload = self.payload(self.ready_brief(urls), urls)
        parsed = self.runner.parse_work_result(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            64_000,
            "trading_system_research",
        )
        report = self.runner.format_work_report(parsed, 64_000)

        with self.assertRaisesRegex(ValueError, "formatted report"):
            self.runner.recover_ea_research_from_formatted_report(
                "untrusted wrapper\n" + report,
                64_000,
            )

    def test_direct_valid_compact_brief_skips_semantic_repair_and_projects_digest(self) -> None:
        urls = [
            "https://tradingfinder.com/education/trading-strategy/",
            "https://forex-station.com/strategy-library-t8475202.html",
        ]
        primary_payload = self.payload(self.ready_brief(urls), urls)
        calls: list[dict] = []

        def fake_chat(command, **kwargs):
            command_values = [str(value) for value in command]
            calls.append({"command": command_values, "prompt": str(kwargs.get("stdin") or "")})
            output_path = Path(command_values[command_values.index("-o") + 1])
            output_path.write_text(
                json.dumps(primary_payload, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
            return self.fake_result(urls)

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
            self.runner,
            "CODEX_RUNS_DIR",
            Path(temp_dir),
        ), mock.patch.object(
            self.runner,
            "chat_status",
            return_value={"ok": True, "status": "ready"},
        ), mock.patch.object(
            self.runner,
            "run_chat_command",
            side_effect=fake_chat,
        ):
            result = self.runner.run_codex(
                "Expand only the Backend-selected strategy record.",
                "mission_archivist",
                "mission-incomplete-drift-canonicalized",
                timeout=240,
                output_limit=64_000,
                execution_mode="auto_guarded",
                web_search=True,
                read_only_work=True,
                result_profile="trading_system_research",
                required_open_urls=urls,
            )

        self.assertTrue(result["ok"], result)
        self.assertEqual(len(calls), 1)
        self.assertFalse(result["semanticRepair"]["attempted"])
        self.assertEqual(result["semanticRepair"]["attemptCount"], 0)
        fields = {
            item["field"]: item["value"] for item in result["contractFields"]
        }
        normalized = json.loads(fields["strategyBrief"])
        self.assertEqual(normalized["systemName"], "EMA Closed-Bar Crossover")
        self.assertRegex(fields["sourceDigest"], r"^[0-9a-f]{64}$")
        self.assertEqual(json.loads(fields["sourceLinks"]), urls)

    def test_timeout_is_reported_and_original_issues_remain_visible(self) -> None:
        urls = [
            "https://tradingfinder.com/education/trading-strategy/",
            "https://forex-station.com/strategy-library-t8475202.html",
        ]
        invalid = self.ready_brief(urls)
        invalid["entryRules"] = ""
        primary_payload = self.payload(invalid, urls)
        calls = 0

        def fake_chat(command, **kwargs):
            nonlocal calls
            calls += 1
            command_values = [str(value) for value in command]
            if calls == 1:
                output_path = Path(command_values[command_values.index("-o") + 1])
                output_path.write_text(
                    json.dumps(primary_payload, ensure_ascii=False, separators=(",", ":")),
                    encoding="utf-8",
                )
                return self.fake_result(urls)
            return {
                "ok": False,
                "exitCode": "timeout",
                "durationMs": 120_000,
                "processStarted": True,
                "processTreeTerminated": True,
                "stdout": "",
                "stderr": "Timed out after 120s",
            }

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
            self.runner,
            "CODEX_RUNS_DIR",
            Path(temp_dir),
        ), mock.patch.object(
            self.runner,
            "chat_status",
            return_value={"ok": True, "status": "ready"},
        ), mock.patch.object(
            self.runner,
            "run_chat_command",
            side_effect=fake_chat,
        ), mock.patch.object(
            self.runner,
            "require_fresh_corrective_verifier_quota",
            return_value={"ok": True},
        ):
            result = self.runner.run_codex(
                "Expand only the Backend-selected strategy record.",
                "mission_archivist",
                "mission-semantic-repair-timeout",
                timeout=240,
                output_limit=64_000,
                execution_mode="auto_guarded",
                web_search=True,
                read_only_work=True,
                result_profile="trading_system_research",
                required_open_urls=urls,
            )

        self.assertFalse(result["ok"], result)
        self.assertEqual(calls, 2)
        repair = result["semanticRepair"]
        self.assertEqual(repair["repairProcessStatus"], "timeout")
        self.assertTrue(repair["processTreeTerminated"])
        self.assertEqual(
            repair["remainingIssues"][0]["code"],
            "BRIEF_TEXT_REQUIRED",
        )


if __name__ == "__main__":
    unittest.main()
