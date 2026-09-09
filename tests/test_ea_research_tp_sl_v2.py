from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

from tests.test_ea_research_blueprint_v2 import CONTRACT, input_record, ready_blueprint


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "runner" / "codex_cli_runner.py"
SCHEMA_PATH = ROOT / "contracts" / "research" / "ea-implementation-blueprint-v2.schema.json"

METHOD_FIELDS = {
    "value",
    "valueInputRef",
    "atrIndicatorRef",
    "rrMultiple",
    "rrMultipleInputRef",
    "rrRiskReference",
    "lookbackBars",
    "lookbackInputRef",
    "swingShift",
    "indicatorRef",
    "indicatorShift",
    "basketPriceField",
    "basketScope",
    "bufferValue",
    "bufferInputRef",
    "formula",
}


def issue_codes(blueprint: dict) -> set[str]:
    return {
        item["code"]
        for item in CONTRACT.validate_blueprint(blueprint, require_ready=True)
    }


def configure(rule: dict, protection_type: str, **fields: object) -> None:
    for field in METHOD_FIELDS:
        rule.pop(field, None)
    rule.update(enabled=True, type=protection_type, **fields)


def add_input(blueprint: dict, input_id: str, default: int | float) -> None:
    blueprint["inputs"].append(input_record(input_id, default, []))


def add_indicator(
    blueprint: dict,
    indicator_id: str,
    kind: str,
    *,
    parameters: dict | None = None,
) -> None:
    blueprint["indicators"].append(
        {
            "indicatorId": indicator_id,
            "kind": kind,
            "timeframe": "signal",
            "parameters": dict(parameters or {}),
            "appliedPrice": "close",
            "outputLine": "main",
            "sourceStatus": "verified_fact",
            "sourceRefs": ["S1"],
        }
    )


def price_operand(**fields: object) -> dict:
    return {"op": "operand", "operand": fields}


class EAResearchTpSlV2Tests(unittest.TestCase):
    def test_schema_uses_arithmetic_price_formula_not_boolean_expression(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        protection = schema["$defs"]["protectionRule"]
        self.assertEqual(protection["properties"]["formula"]["$ref"], "#/$defs/priceFormula")
        self.assertNotEqual(protection["properties"]["formula"]["$ref"], "#/$defs/expression")
        self.assertEqual(
            set(schema["$defs"]["priceFormula"]["properties"]["op"]["enum"]),
            {"operand", "add", "subtract", "multiply", "divide", "min", "max", "negate"},
        )

    def test_positive_atr_rr_swing_indicator_and_basket_contracts(self) -> None:
        cases: list[tuple[str, dict]] = []

        atr = ready_blueprint()
        add_input(atr, "atr_multiplier", 2.0)
        add_indicator(atr, "atr_14", "ATR", parameters={"period": 14})
        configure(
            atr["tpSl"]["stopLoss"],
            "atr",
            valueInputRef="atr_multiplier",
            atrIndicatorRef="atr_14",
            unit="atr_multiple",
            reference="entry_price",
        )
        cases.append(("atr", atr))

        rr = ready_blueprint()
        configure(
            rr["tpSl"]["takeProfit"],
            "rr",
            rrMultiple=2.0,
            rrRiskReference="initial_stop_loss_distance",
            unit="risk_multiple",
            reference="entry_price",
        )
        cases.append(("rr", rr))

        swing = ready_blueprint()
        configure(
            swing["tpSl"]["stopLoss"],
            "swing",
            lookbackBars=20,
            swingShift=1,
            unit="price",
            reference="swing_low",
            formula=price_operand(kind="reference", reference="swing_low", unit="price"),
        )
        cases.append(("swing", swing))

        indicator = ready_blueprint()
        configure(
            indicator["tpSl"]["takeProfit"],
            "indicator",
            indicatorRef="ema_slow",
            indicatorShift=1,
            unit="price",
            reference="indicator_value",
            formula=price_operand(kind="indicator", indicatorRef="ema_slow", shift=1, unit="price"),
        )
        cases.append(("indicator", indicator))

        basket = ready_blueprint()
        configure(
            basket["tpSl"]["takeProfit"],
            "basket",
            valueInputRef="tp_pips",
            basketPriceField="weighted_average_entry_price",
            basketScope="symbol_magic_side",
            unit="pip",
            reference="basket_price",
        )
        basket["tpSl"]["takeProfit"]["placementTiming"] = "after_fill"
        cases.append(("basket", basket))

        for label, blueprint in cases:
            with self.subTest(label=label):
                self.assertEqual(CONTRACT.validate_blueprint(blueprint, require_ready=True), [])

    def test_fixed_requires_one_value_and_matching_unit_and_reference(self) -> None:
        ambiguous = ready_blueprint()
        ambiguous["tpSl"]["stopLoss"]["value"] = 30
        self.assertIn("PROTECTION_VALUE_AMBIGUOUS", issue_codes(ambiguous))

        mismatched = ready_blueprint()
        mismatched["tpSl"]["stopLoss"].update(unit="percent", reference="swing_low")
        self.assertTrue(
            {"PROTECTION_UNIT_MISMATCH", "PROTECTION_REFERENCE_MISMATCH"}.issubset(issue_codes(mismatched))
        )

    def test_atr_requires_multiplier_and_real_atr_indicator(self) -> None:
        missing_multiplier = ready_blueprint()
        configure(
            missing_multiplier["tpSl"]["stopLoss"],
            "atr",
            atrIndicatorRef="ema_fast",
            unit="atr_multiple",
            reference="entry_price",
        )
        codes = issue_codes(missing_multiplier)
        self.assertIn("ATR_INDICATOR_KIND_INVALID", codes)
        self.assertIn("READINESS_UNRESOLVED", codes)

    def test_rr_rejects_stop_loss_circularity_and_missing_effective_stop(self) -> None:
        circular = ready_blueprint()
        for name in ("stopLoss", "takeProfit"):
            configure(
                circular["tpSl"][name],
                "rr",
                rrMultiple=2.0,
                rrRiskReference="initial_stop_loss_distance",
                unit="risk_multiple",
                reference="entry_price",
            )
        codes = issue_codes(circular)
        self.assertIn("RR_STOP_LOSS_FORBIDDEN", codes)
        self.assertIn("RR_STOP_REFERENCE_INVALID", codes)

        no_stop = ready_blueprint()
        no_stop["tpSl"]["stopLoss"] = {
            "enabled": False,
            "type": "none",
            "sourceStatus": "verified_fact",
            "sourceRefs": ["S1"],
        }
        configure(
            no_stop["tpSl"]["takeProfit"],
            "rr",
            rrMultiple=2.0,
            rrRiskReference="initial_stop_loss_distance",
            unit="risk_multiple",
            reference="entry_price",
        )
        self.assertIn("RR_STOP_REFERENCE_INVALID", issue_codes(no_stop))

    def test_swing_indicator_and_basket_require_deterministic_sources(self) -> None:
        swing = ready_blueprint()
        configure(swing["tpSl"]["stopLoss"], "swing", unit="price", reference="swing_high")
        swing_codes = issue_codes(swing)
        self.assertIn("SWING_REFERENCE_DIRECTION_INVALID", swing_codes)
        self.assertIn("READINESS_UNRESOLVED", swing_codes)

        indicator = ready_blueprint()
        configure(indicator["tpSl"]["takeProfit"], "indicator", unit="price", reference="indicator_value")
        self.assertIn("READINESS_UNRESOLVED", issue_codes(indicator))

        basket = ready_blueprint()
        configure(
            basket["tpSl"]["takeProfit"],
            "basket",
            basketPriceField="average_entry_price",
            basketScope="symbol_magic_side",
            unit="pip",
            reference="basket_price",
        )
        basket["tpSl"]["takeProfit"]["placementTiming"] = "after_fill"
        self.assertIn("READINESS_UNRESOLVED", issue_codes(basket))

    def test_boolean_or_non_price_formula_is_rejected(self) -> None:
        boolean_formula = ready_blueprint()
        configure(
            boolean_formula["tpSl"]["takeProfit"],
            "indicator",
            indicatorRef="ema_slow",
            indicatorShift=1,
            unit="price",
            reference="indicator_value",
            formula={
                "op": ">",
                "left": price_operand(kind="indicator", indicatorRef="ema_slow", shift=1, unit="price"),
                "right": price_operand(kind="constant", value=1, unit="price"),
            },
        )
        self.assertIn("PRICE_FORMULA_OPERATOR_INVALID", issue_codes(boolean_formula))

        scalar_formula = copy.deepcopy(boolean_formula)
        scalar_formula["tpSl"]["takeProfit"]["formula"] = price_operand(
            kind="constant", value=2, unit="scalar"
        )
        self.assertIn("PRICE_FORMULA_RESULT_INVALID", issue_codes(scalar_formula))

        divide_by_zero = copy.deepcopy(boolean_formula)
        divide_by_zero["tpSl"]["takeProfit"]["formula"] = {
            "op": "divide",
            "left": price_operand(kind="indicator", indicatorRef="ema_slow", shift=1, unit="price"),
            "right": price_operand(kind="constant", value=0, unit="scalar"),
        }
        self.assertIn("PRICE_FORMULA_DIVIDE_BY_ZERO", issue_codes(divide_by_zero))

    def test_trigger_and_broker_retry_guards_are_bounded(self) -> None:
        blueprint = ready_blueprint()
        stop = blueprint["tpSl"]["stopLoss"]
        stop.update(placementTiming="on_trigger", freezeLevelPolicy="retry_bounded")
        self.assertIn("READINESS_UNRESOLVED", issue_codes(blueprint))

        stop.update(
            activationRuleIds=["ENTRY_BUY_001"],
            freezeRetryLimit=3,
            freezeRetryDelayMs=250,
        )
        self.assertEqual(CONTRACT.validate_blueprint(blueprint, require_ready=True), [])

    def test_structured_output_keeps_recursive_price_formula_closed_and_nullable(self) -> None:
        spec = importlib.util.spec_from_file_location("ea_tp_sl_runner_test", RUNNER_PATH)
        if spec is None or spec.loader is None:
            self.fail("Could not load runner")
        runner = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = runner
        spec.loader.exec_module(runner)
        canonical = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        transport = runner._to_structured_output_schema(canonical, ref_prefix="#/$defs/")

        formula = transport["$defs"]["priceFormula"]
        self.assertEqual(set(formula["required"]), set(formula["properties"]))
        self.assertIs(formula["additionalProperties"], False)
        self.assertEqual(
            transport["$defs"]["protectionRule"]["properties"]["formula"]["anyOf"][0]["$ref"],
            "#/$defs/priceFormula",
        )


if __name__ == "__main__":
    unittest.main()
