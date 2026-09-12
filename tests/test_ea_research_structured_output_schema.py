from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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
    "metafx_ea_research_structured_output_brief_support",
    BRIEF_TEST_PATH,
)


class EAResearchStructuredOutputSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_module(
            "metafx_ea_research_structured_output_runner",
            RUNNER_PATH,
        )

    @staticmethod
    def ready_brief() -> dict:
        return copy.deepcopy(BRIEF_SUPPORT.valid_brief())

    @staticmethod
    def result_payload(brief: dict) -> dict:
        return {
            "status": "completed",
            "summary": "EA Strategy Brief research completed",
            "findings": ["Closed-bar entry and exit prose is implementation-ready"],
            "nextSteps": ["Review the ten A-J Sheet fields before saving"],
            "evidence": [
                {
                    "label": f"Public source {index}",
                    "url": url,
                    "note": "Opened by the research worker",
                }
                for index, url in enumerate(brief["sourceLinks"], start=1)
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

    def parse(self, brief: dict) -> dict:
        return self.runner.parse_work_result(
            json.dumps(self.result_payload(brief), ensure_ascii=False),
            64_000,
            "trading_system_research",
        )

    def test_embedded_schema_is_exact_compact_supported_subset(self) -> None:
        embedded = self.runner.build_work_output_schema(
            64_000,
            "trading_system_research",
        )
        research = embedded["properties"]["research"]
        expected = {
            "schemaVersion",
            "systemName",
            "systemOverview",
            "entryRules",
            "recoveryRules",
            "exitRules",
            "moneyManagement",
            "orderExecution",
            "displayRequirements",
            "additionalNotes",
            "sourceLinks",
            "checkedAt",
            "limitations",
        }

        self.assertEqual(research["type"], "object")
        self.assertIs(research["additionalProperties"], False)
        self.assertEqual(set(research["properties"]), expected)
        self.assertEqual(set(research["required"]), expected)
        self.assertEqual(
            research["properties"]["schemaVersion"]["enum"],
            ["ea-strategy-brief/1.0.0"],
        )
        self.assertEqual(
            research["properties"]["sourceLinks"]["minItems"],
            2,
        )
        self.assertEqual(
            research["properties"]["sourceLinks"]["maxItems"],
            2,
        )
        self.assertEqual(embedded["properties"]["evidence"]["minItems"], 2)
        self.assertEqual(embedded["properties"]["evidence"]["maxItems"], 2)
        self.assertNotIn("$defs", embedded)

    def test_direct_compact_brief_projects_exact_backend_fields(self) -> None:
        brief = self.ready_brief()
        parsed = self.parse(brief)
        fields = {item["field"]: item["value"] for item in parsed["contractFields"]}

        self.assertEqual(
            list(fields),
            list(self.runner.TRADING_SYSTEM_RESEARCH_CONTRACT_FIELDS),
        )
        self.assertEqual(json.loads(fields["strategyBrief"]), brief)
        self.assertRegex(fields["sourceDigest"], r"^[0-9a-f]{64}$")
        self.assertEqual(json.loads(fields["sourceLinks"]), brief["sourceLinks"])
        self.assertEqual(fields["checkedAt"], "2026-09-10T12:00:00+07:00")
        self.assertEqual(json.loads(fields["limitations"]), brief["limitations"])

    def test_missing_operational_fields_receive_versioned_defaults_before_projection(self) -> None:
        brief = self.ready_brief()
        for field in (
            "recoveryRules",
            "exitRules",
            "moneyManagement",
            "orderExecution",
        ):
            brief.pop(field)

        parsed = self.parse(brief)
        fields = {item["field"]: item["value"] for item in parsed["contractFields"]}
        restored = json.loads(fields["strategyBrief"])

        self.assertIn("RecoveryMode=none", restored["recoveryRules"])
        self.assertIn("StopLossPoints=300", restored["exitRules"])
        self.assertIn("TakeProfitPoints=600", restored["exitRules"])
        self.assertIn("PositionSizingMode=fixed_lot", restored["moneyManagement"])
        self.assertIn("FixedLot=0.01", restored["moneyManagement"])
        self.assertIn(
            "MaxOpenPositionsPerSymbolMagic=1",
            restored["moneyManagement"],
        )
        self.assertIn("Market Buy/Sell", restored["orderExecution"])
        self.assertNotIn("COMPONENT=closed_bar_execution", restored["orderExecution"])
        self.assertIn("compact-ea-safe-inputs-v2", restored["additionalNotes"])
        self.assertIn(
            "INPUT_METADATA_VERSION=ea-optimization-inputs-v1",
            restored["additionalNotes"],
        )
        self.assertIn("DEFAULTED_COMPONENTS=", restored["additionalNotes"])

    def test_text_is_normalized_and_safe_optional_defaults_are_restored(self) -> None:
        brief = self.ready_brief()
        brief["systemName"] = "  EMA   crossover  "
        for field in (
            "recoveryRules",
            "displayRequirements",
            "additionalNotes",
            "limitations",
        ):
            brief.pop(field)

        parsed = self.parse(brief)
        fields = {item["field"]: item["value"] for item in parsed["contractFields"]}
        restored = json.loads(fields["strategyBrief"])

        self.assertEqual(restored["systemName"], "EMA crossover")
        self.assertIn("RecoveryMode=none", restored["recoveryRules"])
        self.assertIn("Balance", restored["displayRequirements"])
        self.assertIn(
            BRIEF_SUPPORT.BRIEF.IMPLEMENTATION_DEFAULT_MARKER,
            restored["additionalNotes"],
        )
        self.assertIn("DEFAULTED_COMPONENTS=recovery", restored["additionalNotes"])
        self.assertTrue(restored["limitations"])

    def test_required_null_unknown_field_and_invalid_timestamp_fail_closed(self) -> None:
        cases: list[tuple[str, dict, str]] = []

        missing = self.ready_brief()
        missing["entryRules"] = None
        cases.append(("required null", missing, "BRIEF_TEXT_REQUIRED"))

        unknown = self.ready_brief()
        unknown["legacyBlueprint"] = {}
        cases.append(("unknown field", unknown, "BRIEF_FIELDS_UNEXPECTED"))

        invalid_time = self.ready_brief()
        invalid_time["checkedAt"] = "not-a-date"
        cases.append(("timestamp", invalid_time, "BRIEF_CHECKED_AT_INVALID"))

        for label, brief, issue_code in cases:
            with self.subTest(label=label), self.assertRaisesRegex(
                self.runner.EAResearchSemanticValidationError,
                issue_code,
            ):
                self.parse(brief)

    def test_source_links_require_two_unique_independent_public_hosts(self) -> None:
        cases = []

        duplicate = self.ready_brief()
        duplicate["sourceLinks"] = [duplicate["sourceLinks"][0]] * 2
        cases.append(("duplicate", duplicate, "BRIEF_SOURCE_LINK_DUPLICATE"))

        same_host = self.ready_brief()
        same_host["sourceLinks"] = [
            "https://www.investopedia.com/a",
            "https://academy.investopedia.com/b",
        ]
        cases.append(("same host", same_host, "BRIEF_SOURCE_HOST_NOT_INDEPENDENT"))

        private = self.ready_brief()
        private["sourceLinks"] = [
            "http://127.0.0.1/private",
            private["sourceLinks"][1],
        ]
        cases.append(("private", private, "BRIEF_SOURCE_LINK_INVALID"))

        for label, brief, issue_code in cases:
            payload = self.result_payload(brief)
            payload["evidence"] = [
                {"label": "A", "url": "https://www.investopedia.com/a", "note": ""},
                {"label": "B", "url": "https://www.babypips.com/b", "note": ""},
            ]
            with self.subTest(label=label), self.assertRaisesRegex(
                self.runner.EAResearchSemanticValidationError,
                issue_code,
            ):
                self.runner.parse_work_result(
                    json.dumps(payload, ensure_ascii=False),
                    64_000,
                    "trading_system_research",
                )

    def test_semantic_failure_exposes_bounded_code_path_and_message_for_revision(self) -> None:
        invalid = self.ready_brief()
        invalid.pop("entryRules")
        invalid["unexpected"] = "legacy"

        with self.assertRaises(
            self.runner.EAResearchSemanticValidationError,
        ) as raised:
            self.parse(invalid)

        issues = raised.exception.issues
        self.assertIn("BRIEF_FIELDS_MISSING", {item["code"] for item in issues})
        self.assertIn("BRIEF_FIELDS_UNEXPECTED", {item["code"] for item in issues})
        self.assertTrue(all(item["path"].startswith("$") for item in issues))
        self.assertTrue(all(item["message"] for item in issues))
        self.assertLessEqual(len(issues), 40)


if __name__ == "__main__":
    unittest.main()
