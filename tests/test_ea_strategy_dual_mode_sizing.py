"""Bounded proof of fixed-lot/default versus independently proven risk sizing."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "dual_mode_strategy_brief",
    ROOT / "backend/local-runner/hq_backend/ea/ea_strategy_brief.py",
)
BRIEF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BRIEF)

DECLARATION = "double lot=(PositionSizingMode==0 ? FixedLot : CalculateRiskLot(stopDistance,entryPrice,marginType));"
SOURCE = """
input int PositionSizingMode=0;
input double FixedLot=0.01;
void OnTick()
{
  double stopDistance=10;
  double entryPrice=100;
  ENUM_ORDER_TYPE marginType=ORDER_TYPE_BUY;
  DECLARATION
  if(lot<=0) return;
  if(!MathIsValidNumber(lot)) return;
  double marginRequired=0;
  if(!OrderCalcMargin(marginType,_Symbol,lot,entryPrice,marginRequired)) return;
  MqlTradeRequest request={};
  request.volume=lot;
  MqlTradeResult result={};
  OrderSend(request,result);
}
""".replace("DECLARATION", DECLARATION)


def matches(source: str, safe: set[str] | None = None) -> bool:
    lexical = BRIEF._indicator_lexical_views(source)
    code = lexical[0]
    bodies = BRIEF._compact_ea_function_map(code)["ontick"]
    before_volume = bodies[0].split("request.volume", 1)[0]
    dependency = BRIEF._mql_expression_dependency_text("lot", before_volume)
    return BRIEF._fixed_lot_dependency_matches(
        dependency, code, 0.01,
        safe_sizing_functions={"calculaterisklot"} if safe is None else safe,
    )


class DualModeSizingTests(unittest.TestCase):
    def test_actual_default_and_proven_risk_selector_pass(self):
        self.assertTrue(matches(SOURCE))
        self.assertTrue(matches(SOURCE.replace("double lot=(", "double lot=\n (")))

    def test_risk_helper_must_already_have_independent_safety_proof(self):
        self.assertFalse(matches(SOURCE, set()))
        self.assertFalse(matches(SOURCE, {"differenthelper"}))

    def test_wrong_scaled_swapped_or_constant_branches_fail(self):
        mutations = (
            ("? FixedLot :", "? FixedLot*2 :"),
            ("? FixedLot :", "? 0.02 :"),
            ("? FixedLot :", "? AlternateLot :"),
            ("PositionSizingMode==0", "PositionSizingMode==1"),
            ("PositionSizingMode==0", "false"),
            ("CalculateRiskLot(stopDistance,entryPrice,marginType)", "0.01"),
            ("CalculateRiskLot(stopDistance,entryPrice,marginType)", "UnsafeRiskLot(stopDistance,entryPrice,marginType)"),
            ("CalculateRiskLot(stopDistance,entryPrice,marginType)", "CalculateRiskLot(stopDistance,entryPrice,marginType)*2"),
            ("? FixedLot : CalculateRiskLot(stopDistance,entryPrice,marginType)", "? CalculateRiskLot(stopDistance,entryPrice,marginType) : FixedLot"),
            ("));\n  if(lot", "))*2;\n  if(lot"),
        )
        for old, new in mutations:
            with self.subTest(new=new):
                self.assertIn(old, SOURCE)
                self.assertFalse(matches(SOURCE.replace(old, new)))

    def test_wrong_or_shadowed_immutable_inputs_fail(self):
        mutations = (
            ("input double FixedLot=0.01;", "input double FixedLot=0.02;"),
            ("input int PositionSizingMode=0;", "input int PositionSizingMode=1;"),
            (DECLARATION, "double FixedLot=0.01;\n" + DECLARATION),
            (DECLARATION, "int PositionSizingMode=0;\n" + DECLARATION),
            (DECLARATION, "FixedLot=0.01;\n" + DECLARATION),
            (DECLARATION, "PositionSizingMode=0;\n" + DECLARATION),
        )
        for old, new in mutations:
            with self.subTest(new=new):
                self.assertFalse(matches(SOURCE.replace(old, new)))

    def test_volume_overrides_scaling_and_hidden_output_writes_fail(self):
        for mutation in (
            "lot=0.01;", "lot=FixedLot;", "lot*=2;", "lot++;", "++lot;",
            "--lot;", "lot<<=1;", "SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN,lot);",
            "SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN,(lot));",
            "SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN,((lot)));",
            "double lot=0.01;", "if(false) { lot=0.01; }",
        ):
            with self.subTest(mutation=mutation):
                self.assertFalse(matches(SOURCE.replace(DECLARATION, DECLARATION + mutation)))

    def test_dead_or_optional_declaration_and_literal_initializer_trick_fail(self):
        for replacement in (
            "if(false) { " + DECLARATION + " }",
            "if(Enabled) " + DECLARATION,
            "double lot=0.01;\n" + DECLARATION.replace("double lot", "lot"),
            "if(PositionSizingMode==0) return;\n" + DECLARATION,
            "if(PositionSizingMode!=0) return;\n" + DECLARATION,
            "if(PositionSizingMode==0 || PositionSizingMode==1) return;\n" + DECLARATION,
            "if((PositionSizingMode==0 || PositionSizingMode==1)) return;\n" + DECLARATION,
            "if(PositionSizingMode==0 || false) return;\n" + DECLARATION,
        ):
            with self.subTest(replacement=replacement):
                self.assertFalse(matches(SOURCE.replace(DECLARATION, replacement)))

    def test_existing_direct_literal_and_bound_input_still_work(self):
        self.assertTrue(BRIEF._fixed_lot_dependency_matches("0.01", SOURCE, 0.01))
        self.assertTrue(BRIEF._fixed_lot_dependency_matches("FixedLot", SOURCE, 0.01))
        self.assertFalse(BRIEF._fixed_lot_dependency_matches("FixedLot*2", SOURCE, 0.01))


if __name__ == "__main__":
    unittest.main()
