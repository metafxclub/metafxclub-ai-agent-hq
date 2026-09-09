from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "runner" / "codex_cli_runner.py"
BLUEPRINT_TEST_PATH = ROOT / "tests" / "test_ea_research_blueprint_v2.py"
SCHEMA_PATH = (
    ROOT
    / "contracts"
    / "research"
    / "ea-implementation-blueprint-v2.schema.json"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BLUEPRINT_SUPPORT = load_module(
    "metafx_ea_research_structured_output_blueprint_support",
    BLUEPRINT_TEST_PATH,
)


class EAResearchStructuredOutputSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_module(
            "metafx_ea_research_structured_output_runner",
            RUNNER_PATH,
        )

    def ready_blueprint(self) -> dict:
        blueprint = BLUEPRINT_SUPPORT.ready_blueprint()
        blueprint["evidenceMap"].append(
            {
                "sourceRef": "S3",
                "url": "https://www.metatrader4.com/en/trading-platform/help/analytics/tech_indicators/moving_average",
                "title": "Independent EMA reference",
                "checkedAt": blueprint["checkedAt"],
            }
        )
        return blueprint

    @staticmethod
    def result_payload(blueprint: dict) -> dict:
        return {
            "status": "completed",
            "summary": "EA-ready deterministic research completed",
            "findings": ["Closed-bar rules use typed expressions"],
            "nextSteps": ["Archive the canonical blueprint"],
            "evidence": [
                {
                    "label": item["title"],
                    "url": item["url"],
                    "note": "Public source opened by the research worker",
                }
                for item in blueprint["evidenceMap"]
            ],
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

    @staticmethod
    def tag_json(value: object) -> str:
        return "JSON:" + json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def tag_transport_free_form_values(self, blueprint: dict) -> None:
        for record in blueprint["inputs"]:
            record["default"] = self.tag_json(record["default"])
        for record in blueprint["indicators"]:
            record["parameters"] = self.tag_json(record["parameters"])
        for feature in blueprint["orderManagement"].values():
            if isinstance(feature, dict) and "parameters" in feature:
                feature["parameters"] = self.tag_json(feature["parameters"])
        for record in blueprint["testCases"]:
            for key in ("given", "when", "expected"):
                record[key] = self.tag_json(record[key])

    def test_transport_schema_is_recursive_supported_subset_without_mutating_canonical(self) -> None:
        canonical = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        original = copy.deepcopy(canonical)
        transport = self.runner._to_structured_output_schema(
            canonical,
            ref_prefix="#/$defs/",
        )
        self.assertEqual(canonical, original)

        canonical_keys: set[str] = set()
        forbidden_found: list[tuple[str, str]] = []
        invalid_objects: list[str] = []
        invalid_refs: list[str] = []
        references: list[str] = []
        forbidden = {
            "$id",
            "$schema",
            "allOf",
            "dependentRequired",
            "dependentSchemas",
            "else",
            "format",
            "if",
            "not",
            "oneOf",
            "patternProperties",
            "prefixItems",
            "propertyNames",
            "then",
            "unevaluatedProperties",
            "uniqueItems",
        }

        def walk(value: object, path: str, *, collect_canonical: bool = False) -> None:
            if isinstance(value, dict):
                if collect_canonical:
                    canonical_keys.update(value)
                else:
                    for key in forbidden.intersection(value):
                        forbidden_found.append((path, key))
                    if value.get("type") == "object":
                        properties = value.get("properties")
                        if (
                            not isinstance(properties, dict)
                            or set(value.get("required", [])) != set(properties)
                            or value.get("additionalProperties") is not False
                        ):
                            invalid_objects.append(path)
                    reference = value.get("$ref")
                    if isinstance(reference, str):
                        references.append(reference)
                        if not reference.startswith("#/$defs/"):
                            invalid_refs.append(reference)
                for key, child in value.items():
                    walk(child, f"{path}.{key}", collect_canonical=collect_canonical)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, f"{path}[{index}]", collect_canonical=collect_canonical)

        walk(canonical, "$", collect_canonical=True)
        walk(transport, "$")
        self.assertTrue({"uniqueItems", "allOf", "if", "then", "oneOf", "format"}.issubset(canonical_keys))
        self.assertEqual(forbidden_found, [])
        self.assertEqual(invalid_objects, [])
        self.assertEqual(invalid_refs, [])
        self.assertGreater(len(references), 100)
        self.assertTrue(
            all(reference[len("#/$defs/") :] in transport["$defs"] for reference in references)
        )

        definitions = transport["$defs"]
        input_schema = definitions["input"]
        self.assertEqual(
            input_schema["properties"]["min"],
            {"anyOf": [{"type": "number"}, {"type": "null"}]},
        )
        self.assertEqual(
            input_schema["properties"]["default"]["type"],
            "string",
        )
        self.assertNotIn("anyOf", input_schema["properties"]["default"])
        self.assertEqual(
            definitions["indicator"]["properties"]["parameters"]["type"],
            "string",
        )
        object_pattern = definitions["indicator"]["properties"]["parameters"]["pattern"]
        self.assertRegex("JSON:{}", object_pattern)
        self.assertNotRegex("JSON:null", object_pattern)
        self.assertEqual(
            definitions["managedFeature"]["properties"]["parameters"]["pattern"],
            object_pattern,
        )
        reset_condition = definitions["recovery"]["properties"]["resetCondition"]
        self.assertEqual(reset_condition["anyOf"][-1], {"type": "null"})
        self.assertIn("anyOf", reset_condition["anyOf"][0])
        for definition_name in (
            "recoverySpacing",
            "recoveryLotFormula",
            "basketThreshold",
            "hedgeLifecycle",
            "reentryPolicy",
        ):
            self.assertEqual(definitions[definition_name]["type"], "object")
            self.assertIs(definitions[definition_name]["additionalProperties"], False)
            self.assertEqual(
                set(definitions[definition_name]["required"]),
                set(definitions[definition_name]["properties"]),
            )

        embedded = self.runner.build_work_output_schema(
            64_000,
            "trading_system_research",
        )
        expected_research = copy.deepcopy(transport)
        expected_definitions = expected_research.pop("$defs")
        self.assertEqual(embedded["properties"]["research"], expected_research)
        self.assertEqual(embedded["$defs"], expected_definitions)
        self.assertNotIn("$defs", embedded["properties"]["research"])
        self.assertEqual(
            embedded["properties"]["research"]["properties"]["strategyId"]["$ref"],
            "#/$defs/id",
        )

    def test_transport_nulls_and_tagged_json_restore_to_canonical_blueprint(self) -> None:
        canonical = self.ready_blueprint()
        transport = copy.deepcopy(canonical)
        self.tag_transport_free_form_values(transport)

        # These fields are absent in the canonical value, but Structured
        # Outputs makes every optional property required and nullable.
        transport["inputs"][0]["allowedValues"] = None
        transport["entry"]["buy"]["expiry"] = None
        transport["recovery"]["trigger"] = None
        transport["evidenceMap"][0]["quoteOrFinding"] = None

        parsed = self.runner.parse_work_result(
            json.dumps(self.result_payload(transport), ensure_ascii=False),
            64_000,
            "trading_system_research",
        )
        fields = {item["field"]: item["value"] for item in parsed["contractFields"]}
        restored = json.loads(fields["eaBlueprint"])
        expected = self.runner.normalize_blueprint(canonical)
        self.assertEqual(restored, expected)
        self.assertNotIn("allowedValues", restored["inputs"][0])
        self.assertNotIn("expiry", restored["entry"]["buy"])
        self.assertNotIn("trigger", restored["recovery"])
        self.assertIsInstance(restored["indicators"][0]["parameters"], dict)
        self.assertIsInstance(restored["testCases"][0]["given"], dict)

    def test_required_null_and_bad_tagged_json_still_fail_canonical_gate(self) -> None:
        required_null = self.ready_blueprint()
        required_null["checkedAt"] = None
        with self.assertRaisesRegex(ValueError, "CHECKED_AT_INVALID"):
            self.runner.parse_work_result(
                json.dumps(self.result_payload(required_null), ensure_ascii=False),
                64_000,
                "trading_system_research",
            )

        malformed = self.ready_blueprint()
        malformed["inputs"][0]["default"] = "JSON:{not-json"
        with self.assertRaisesRegex(ValueError, "INPUT_DEFAULT_TYPE"):
            self.runner.parse_work_result(
                json.dumps(self.result_payload(malformed), ensure_ascii=False),
                64_000,
                "trading_system_research",
            )

    def test_removed_transport_constraints_remain_semantically_enforced(self) -> None:
        wrong_cross = self.runner.normalize_blueprint(self.ready_blueprint())
        wrong_cross["entry"]["buy"]["rules"][0]["expression"]["expanded"]["all"][0]["op"] = ">="

        duplicate_precedence = self.ready_blueprint()
        duplicate_precedence["precedence"].append(duplicate_precedence["precedence"][0])

        invalid_timestamp = self.ready_blueprint()
        invalid_timestamp["checkedAt"] = "not-a-date"

        for label, blueprint, issue_code in (
            ("conditional cross", wrong_cross, "CROSS_EXPANSION_MISMATCH"),
            ("unique precedence", duplicate_precedence, "PRECEDENCE_DUPLICATE"),
            ("date-time format", invalid_timestamp, "CHECKED_AT_INVALID"),
        ):
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError, issue_code):
                    self.runner.parse_work_result(
                        json.dumps(self.result_payload(blueprint), ensure_ascii=False),
                        64_000,
                        "trading_system_research",
                    )


if __name__ == "__main__":
    unittest.main()
