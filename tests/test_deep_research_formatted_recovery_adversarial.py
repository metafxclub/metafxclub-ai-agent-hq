from __future__ import annotations

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


class DeepResearchFormattedRecoveryAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_module(
            "metafx_deep_research_formatted_recovery_adversarial_runner",
            RUNNER_PATH,
        )
        cls.brief_support = load_module(
            "metafx_deep_research_formatted_recovery_adversarial_brief_support",
            ROOT / "tests" / "test_ea_strategy_brief.py",
        )

    @staticmethod
    def source_urls() -> list[str]:
        return [
            "https://tradingfinder.com/education/trading-strategy/",
            "https://forex-station.com/strategy-library-t8475202.html",
        ]

    def payload(self, urls: list[str]) -> dict:
        brief = self.brief_support.valid_brief()
        brief["sourceLinks"] = list(urls)
        return {
            "status": "completed",
            "summary": "The selected strategy was expanded without changing its sources.",
            "findings": ["The Blueprint passed the canonical semantic validator."],
            "nextSteps": ["Review the verified Blueprint before any EA handoff."],
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

    def report(self, urls: list[str] | None = None) -> str:
        payload = self.payload(urls or self.source_urls())
        parsed = self.runner.parse_work_result(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            64_000,
            "trading_system_research",
        )
        return self.runner.format_work_report(parsed, 64_000)

    @staticmethod
    def replace_contract_value(report: str, field: str, value: str) -> str:
        lines = report.split("\n")
        prefix = f"- {field}: "
        indexes = [index for index, line in enumerate(lines) if line.startswith(prefix)]
        if len(indexes) != 1:
            raise AssertionError(f"Expected exactly one {field} row")
        lines[indexes[0]] = prefix + value
        return "\n".join(lines)

    @staticmethod
    def contract_value(report: str, field: str) -> str:
        prefix = f"- {field}: "
        matches = [line[len(prefix) :] for line in report.split("\n") if line.startswith(prefix)]
        if len(matches) != 1:
            raise AssertionError(f"Expected exactly one {field} row")
        return matches[0]

    def test_exact_canonical_report_recovers_and_round_trips(self) -> None:
        report = self.report()
        recovered = self.runner.recover_ea_research_from_formatted_report(
            report,
            64_000,
        )
        parsed = self.runner.parse_work_result(
            recovered,
            64_000,
            "trading_system_research",
        )

        self.assertEqual(parsed["workStatus"], "completed")
        self.assertEqual(
            [item["field"] for item in parsed["contractFields"]],
            list(self.runner.TRADING_SYSTEM_RESEARCH_CONTRACT_FIELDS),
        )
        self.assertEqual(
            [item["url"] for item in parsed["evidence"]],
            self.source_urls(),
        )
        self.assertEqual(self.runner.format_work_report(parsed, 64_000), report)

    def test_evidence_label_with_colon_recovers_and_round_trips(self) -> None:
        payload = self.payload(self.source_urls())
        payload["evidence"][0]["label"] = "Trading strategy: RSI 2P - WH SelfInvest"
        parsed = self.runner.parse_work_result(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            64_000,
            "trading_system_research",
        )
        report = self.runner.format_work_report(parsed, 64_000)

        recovered = self.runner.recover_ea_research_from_formatted_report(
            report,
            64_000,
        )
        recovered_payload = self.runner.parse_work_result(
            recovered,
            64_000,
            "trading_system_research",
        )

        self.assertEqual(
            recovered_payload["evidence"][0]["label"],
            "Trading strategy: RSI 2P - WH SelfInvest",
        )
        self.assertEqual(self.runner.format_work_report(recovered_payload, 64_000), report)

    def test_transport_recovery_requires_matching_direct_and_formatted_results(self) -> None:
        payload = self.payload(self.source_urls())
        direct = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        parsed = self.runner.parse_work_result(
            direct,
            64_000,
            "trading_system_research",
        )
        report = self.runner.format_work_report(parsed, 64_000)

        recovered = self.runner.recover_ea_research_transport_result(
            report,
            direct,
            64_000,
        )

        self.assertTrue(recovered["ok"])
        self.assertEqual(recovered["workStatus"], "completed")
        self.assertEqual(recovered["contractFields"], parsed["contractFields"])
        self.assertEqual(recovered["evidence"], parsed["evidence"])
        self.assertFalse(recovered["recovery"]["aiInvoked"])
        self.assertFalse(recovered["recovery"]["webSearchInvoked"])
        self.assertFalse(recovered["recovery"]["externalWrites"])

        altered = self.payload(self.source_urls())
        altered["summary"] = "A different direct result must not be accepted."
        with self.assertRaisesRegex(ValueError, "representations do not match"):
            self.runner.recover_ea_research_transport_result(
                report,
                json.dumps(altered, ensure_ascii=False, separators=(",", ":")),
                64_000,
            )

    def test_transport_recovery_ignores_only_representation_char_count(self) -> None:
        payload = self.payload(self.source_urls())
        # The formatted-report parser reconstructs only the validated semantic
        # envelope. A schema-valid direct artifact can contain whitespace that
        # the Strategy Brief normalizer intentionally strips. The semantic
        # result is identical, but ``structuredResultChars`` records the larger
        # original envelope and must not create a false mismatch.
        payload["research"]["additionalNotes"] += "   "
        direct = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        direct_parsed = self.runner.parse_work_result(
            direct,
            64_000,
            "trading_system_research",
        )
        report = self.runner.format_work_report(direct_parsed, 64_000)

        recovered = self.runner.recover_ea_research_transport_result(
            report,
            direct,
            64_000,
        )

        compact_recovered_raw = self.runner.recover_ea_research_from_formatted_report(
            report,
            64_000,
        )
        compact_parsed = self.runner.parse_work_result(
            compact_recovered_raw,
            64_000,
            "trading_system_research",
        )
        self.assertNotEqual(
            compact_parsed["structuredResultChars"],
            direct_parsed["structuredResultChars"],
        )
        self.assertEqual(
            recovered["structuredResultChars"],
            direct_parsed["structuredResultChars"],
        )
        self.assertEqual(recovered["contractFields"], direct_parsed["contractFields"])

    def test_transport_recovery_rejects_non_schema_direct_artifact(self) -> None:
        payload = self.payload(self.source_urls())
        direct = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        parsed = self.runner.parse_work_result(
            direct,
            64_000,
            "trading_system_research",
        )
        report = self.runner.format_work_report(parsed, 64_000)

        unexpected = dict(payload)
        unexpected["unexpectedIgnoredField"] = "must-fail-closed"
        with self.assertRaisesRegex(ValueError, "unexpected direct-schema fields"):
            self.runner.recover_ea_research_transport_result(
                report,
                json.dumps(unexpected, ensure_ascii=False, separators=(",", ":")),
                64_000,
            )

        duplicate = direct.replace(
            '"summary":',
            '"summary":"duplicate","summary":',
            1,
        )
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            self.runner.recover_ea_research_transport_result(
                report,
                duplicate,
                64_000,
            )

        non_finite = direct.replace('"systemName":', '"systemName":NaN,"ignored":', 1)
        with self.assertRaisesRegex(ValueError, "non-finite JSON number"):
            self.runner.recover_ea_research_transport_result(
                report,
                non_finite,
                64_000,
            )

    def test_wrappers_whitespace_crlf_and_nul_are_rejected(self) -> None:
        report = self.report()
        attacks = {
            "prefix": "untrusted wrapper\n" + report,
            "suffix": report + "\nuntrusted wrapper",
            "leading_space": " " + report,
            "trailing_space": report + " ",
            "crlf": report.replace("\n", "\r\n"),
            "nul": report + "\x00",
        }

        for name, attack in attacks.items():
            with self.subTest(name=name), self.assertRaisesRegex(
                ValueError,
                "formatted report",
            ):
                self.runner.recover_ea_research_from_formatted_report(
                    attack,
                    64_000,
                )

    def test_contract_rows_must_be_complete_unique_and_in_canonical_order(self) -> None:
        report = self.report()
        lines = report.split("\n")
        contract_indexes = [
            index
            for index, line in enumerate(lines)
            if any(
                line.startswith(f"- {field}: ")
                for field in self.runner.TRADING_SYSTEM_RESEARCH_CONTRACT_FIELDS
            )
        ]
        self.assertEqual(len(contract_indexes), 5)

        missing = lines.copy()
        del missing[contract_indexes[2]]
        duplicate = lines.copy()
        duplicate.insert(contract_indexes[2], duplicate[contract_indexes[2]])
        reordered = lines.copy()
        first, second = contract_indexes[:2]
        reordered[first], reordered[second] = reordered[second], reordered[first]
        renamed = lines.copy()
        renamed[contract_indexes[1]] = renamed[contract_indexes[1]].replace(
            "- sourceDigest: ",
            "- sourceDigestAlias: ",
            1,
        )

        for name, attack_lines in {
            "missing": missing,
            "duplicate": duplicate,
            "reordered": reordered,
            "renamed": renamed,
        }.items():
            with self.subTest(name=name), self.assertRaisesRegex(
                ValueError,
                "contract field",
            ):
                self.runner.recover_ea_research_from_formatted_report(
                    "\n".join(attack_lines),
                    64_000,
                )

    def test_every_redundant_projection_row_is_bound_by_canonical_round_trip(self) -> None:
        report = self.report()
        projection_fields = [
            field
            for field in self.runner.TRADING_SYSTEM_RESEARCH_CONTRACT_FIELDS
            if field != "strategyBrief"
        ]
        self.assertEqual(
            projection_fields,
            [
                "sourceDigest",
                "sourceLinks",
                "checkedAt",
                "limitations",
            ],
        )

        for field in projection_fields:
            original = self.contract_value(report, field)
            attack = self.replace_contract_value(
                report,
                field,
                original + "__tampered__",
            )
            with self.subTest(field=field), self.assertRaisesRegex(
                ValueError,
                "canonical round trip",
            ):
                self.runner.recover_ea_research_from_formatted_report(
                    attack,
                    64_000,
                )

    def test_duplicate_nested_json_key_and_non_finite_numbers_are_rejected(self) -> None:
        report = self.report()
        raw_brief = self.contract_value(report, "strategyBrief")
        duplicate = raw_brief.replace(
            '"systemName":',
            '"systemName":"duplicate","systemName":',
            1,
        )
        duplicate_report = self.replace_contract_value(
            report,
            "strategyBrief",
            duplicate,
        )
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            self.runner.recover_ea_research_from_formatted_report(
                duplicate_report,
                64_000,
            )

        for value in ("NaN", "Infinity", "-Infinity"):
            attack_brief = raw_brief.replace("{", '{"nonFinite":' + value + ",", 1)
            attack_report = self.replace_contract_value(
                report,
                "strategyBrief",
                attack_brief,
            )
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.runner.recover_ea_research_from_formatted_report(
                    attack_report,
                    64_000,
                )

    def test_evidence_count_and_source_mismatch_are_rejected(self) -> None:
        report = self.report()
        lines = report.split("\n")
        evidence_start = lines.index("แหล่งข้อมูล") + 1
        next_step_index = lines.index("3. ขั้นตอนถัดไป")
        evidence_indexes = list(range(evidence_start, next_step_index - 1))
        self.assertEqual(len(evidence_indexes), 2)

        missing = lines.copy()
        del missing[evidence_indexes[1]]
        extra = lines.copy()
        extra.insert(evidence_indexes[1], extra[evidence_indexes[0]])
        mismatch = lines.copy()
        mismatch[evidence_indexes[0]] = mismatch[evidence_indexes[0]].replace(
            self.source_urls()[0],
            "https://example.com/unbound-source",
            1,
        )

        for name, attack_lines in {
            "missing": missing,
            "extra": extra,
            "source_mismatch": mismatch,
        }.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.runner.recover_ea_research_from_formatted_report(
                    "\n".join(attack_lines),
                    64_000,
                )

    def test_run_codex_rejects_canonical_report_with_unbound_source_pair(self) -> None:
        bound_urls = self.source_urls()
        alternate_urls = [
            "https://macro-ops.com/william-oneils-can-slim-trading-strategy-explained/",
            "https://www.businessinsider.com/how-does-can-slim-investing-work-2011-5",
        ]
        alternate_report = self.report(alternate_urls)
        calls: list[list[str]] = []

        def fake_chat(command, **kwargs):
            command_values = [str(value) for value in command]
            calls.append(command_values)
            output_path = Path(command_values[command_values.index("-o") + 1])
            output_path.write_text(alternate_report, encoding="utf-8")
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
                "nativeWebSearchOpenedUrls": list(bound_urls),
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
        ):
            result = self.runner.run_codex(
                "Expand only the Backend-selected strategy record.",
                "mission_archivist",
                "mission-formatted-recovery-unbound-source",
                timeout=240,
                output_limit=64_000,
                execution_mode="auto_guarded",
                web_search=True,
                read_only_work=True,
                result_profile="trading_system_research",
                required_open_urls=bound_urls,
            )

        self.assertFalse(result["ok"], result)
        self.assertEqual(result["status"], "invalid_output")
        self.assertEqual(len(calls), 1)
        self.assertTrue(result["formatRecovery"]["attempted"])
        self.assertTrue(result["formatRecovery"]["succeeded"])
        self.assertFalse(result["semanticRepair"]["attempted"])
        self.assertIn("Backend-bound", result["structuredOutputError"])


if __name__ == "__main__":
    unittest.main()
