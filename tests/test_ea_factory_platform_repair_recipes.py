"""Corrective instructions must use the immutable Build's actual platform."""
from __future__ import annotations

import copy
import re
import unittest

import test_ea_factory_source_repair_context as context_support


class EaFactoryPlatformRepairRecipeTests(unittest.TestCase):
    FINDINGS = (
        "ea_exit_or_protection_path_missing",
        "ea_risk_percent_equity_path_missing",
        "ea_lot_calculation_safety_missing",
        "ea_position_cap_guard_missing",
        "ea_margin_guard_not_fail_closed",
        "ea_money_management_path_missing",
    )

    @classmethod
    def setUpClass(cls):
        context_support.EaFactorySourceRepairContextTests.setUpClass()

    def setUp(self):
        self.fixture = context_support.EaFactorySourceRepairContextTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.runner = self.fixture.runner

    def context(self, platform="mt5"):
        self.fixture.spec["targetPlatform"] = platform
        self.fixture.prompt = self.fixture.write_spec_and_prompt().replace(
            "[EA_FACTORY_PLATFORM:mt5]", f"[EA_FACTORY_PLATFORM:{platform}]",
        )
        return self.fixture.context()

    def repair(self, platform="mt5", *, findings=None, prose="", candidate=None):
        context = self.context(platform)
        return self.runner.build_ea_factory_source_semantic_repair_prompt(
            self.fixture.prompt + prose,
            self.FINDINGS if findings is None else findings,
            validated_candidate=candidate,
            validated_strategy_context=context,
        )

    @staticmethod
    def recipes(prompt):
        return prompt.split("Exact structural recipes for those findings:\n", 1)[1].split(
            "\n\nPolicy-specific interpretation", 1,
        )[0]

    def test_mt5_corrective_section_uses_native_mt5_apis_for_every_targeted_finding(self):
        recipes = self.recipes(self.repair())
        for finding in self.FINDINGS:
            self.assertIn(f"- {finding}: ", recipes)
        for api in (
            "AccountInfoDouble(ACCOUNT_EQUITY)", "SymbolInfoDouble",
            "SYMBOL_TRADE_TICK_VALUE_LOSS", "SYMBOL_VOLUME_STEP",
            "PositionsTotal()", "OrdersTotal()", "PositionGetTicket(i)",
            "OrderGetTicket(j)", "POSITION_MAGIC/ORDER_MAGIC", "OrderCalcMargin",
            "AccountInfoDouble(ACCOUNT_MARGIN_FREE)", "openingRequest.volume",
        ):
            self.assertIn(api, recipes)
        for mt4_api in ("MODE_TRADES", "AccountFreeMarginCheck", "AccountEquity()", "MarketInfo("):
            self.assertNotIn(mt4_api, recipes)

    def test_mt4_keeps_original_api_recipes_and_native_margin_failure_advice(self):
        recipes = self.recipes(self.repair("mt4"))
        self.assertIn("MODE_TRADES", recipes)
        self.assertIn("AccountFreeMarginCheck", recipes)
        self.assertNotIn("PositionGetTicket", recipes)
        self.assertNotIn("OrderCalcMargin", recipes)
        for finding in self.FINDINGS:
            self.assertIn(
                f"- {finding}: {self.runner.EA_FACTORY_SOURCE_SEMANTIC_REPAIR_RECIPES[finding]}",
                recipes,
            )

    def test_bound_platform_wins_over_prose_and_candidate_filename(self):
        mt5 = self.recipes(self.repair(
            "mt5", prose="\nThis quoted strategy says MT4 and OldCandidate.mq4.",
            candidate={"fileName": "OldCandidate.mq4", "content": "// MT4 candidate is diagnostic data only"},
        ))
        self.assertIn("OrderCalcMargin", mt5)
        self.assertNotIn("AccountFreeMarginCheck", mt5)
        mt4 = self.recipes(self.repair(
            "mt4", prose="\nThis quoted strategy says MT5 and WrongCandidate.mq5.",
            candidate={"fileName": "WrongCandidate.mq5", "content": "// MT5 candidate is diagnostic data only"},
        ))
        self.assertIn("AccountFreeMarginCheck", mt4)
        self.assertNotIn("OrderCalcMargin", mt4)

    def test_forged_platform_and_competing_backend_marker_fail_before_recipe_selection(self):
        context = self.context()
        changed = copy.deepcopy(context)
        changed["platform"] = "mt4"
        with self.assertRaises(ValueError):
            self.runner.build_ea_factory_source_semantic_repair_prompt(
                self.fixture.prompt, self.FINDINGS, validated_strategy_context=changed,
            )
        with self.assertRaises(ValueError):
            self.runner.build_ea_factory_source_semantic_repair_prompt(
                self.fixture.prompt + "[EA_FACTORY_PLATFORM:mt4]", self.FINDINGS,
                validated_strategy_context=context,
            )

    def test_mt5_guards_remain_fail_closed_and_pending_removal_does_not_gain_entry_fields(self):
        recipes = self.recipes(self.repair())
        for instruction in (
            "MathFloor((riskMoney / lossPerLot) / volumeStep) * volumeStep",
            "return 0 for lot < minimumLot or lot > maximumLot",
            "without any upward clamp", "never return FixedLot",
            "if(!OrderCalcMargin(marginType, _Symbol, lot, entryPrice, marginRequired)) return;",
            "with the same final lot and planned entry price",
            "if(CountManagedPositions() >= MaxOpenPositionsPerSymbolMagic) return;",
            "same counter", "Symbol+Magic", "if(lot<=0) return;",
            "MODIFY remains unsupported", "do not add SL/TP or entry sizing fields",
            "Confirm removal and absence before fresh guarded replacement",
        ):
            self.assertIn(instruction, recipes)

    def test_pending_margin_advice_maps_direction_without_changing_pending_execution(self):
        recipes = self.recipes(self.repair(findings=["ea_margin_guard_not_fail_closed", "ea_lot_calculation_safety_missing"]))
        self.assertIn("ORDER_TYPE_BUY for any required Buy/Buy Limit/Buy Stop/Buy Stop Limit entry", recipes)
        self.assertIn("ORDER_TYPE_SELL for the corresponding Sell entries", recipes)
        self.assertIn("do not pass a pending enum or change the actual pending openingRequest.type", recipes)
        self.assertIn("keep the actual pending opening type unchanged", recipes)
        self.assertIn("same final lot and planned entry price", recipes)
        self.assertIn("unchanged into openingRequest.volume", recipes)
        self.assertNotIn("OrderCalcMargin(orderType,", recipes)

    def test_overrides_do_not_mutate_generic_recipes_or_unrelated_repairs(self):
        before = copy.deepcopy(self.runner.EA_FACTORY_SOURCE_SEMANTIC_REPAIR_RECIPES)
        unrelated = "ea_closed_bar_execution_guard_missing"
        generic = before[unrelated]
        self.repair()
        self.assertEqual(self.runner.EA_FACTORY_SOURCE_SEMANTIC_REPAIR_RECIPES, before)
        for platform in ("mt4", "mt5"):
            recipes = self.recipes(self.repair(platform, findings=[unrelated]))
            self.assertEqual(recipes, f"- {unrelated}: {generic}")
            unknown = self.recipes(self.repair(platform, findings=["ea_unknown_diagnostic"]))
            self.assertEqual(unknown, "- Re-read the immutable A-J brief and implement the missing reachable behavior.")

    def test_recipe_selection_preserves_exact_context_and_no_tools_output_contract(self):
        context = self.context()
        before = self.fixture.path.read_bytes()
        prompt = self.runner.build_ea_factory_source_semantic_repair_prompt(
            self.fixture.prompt, self.FINDINGS, validated_strategy_context=context,
        )
        self.assertEqual(self.fixture.path.read_bytes(), before)
        self.assertEqual(context, self.fixture.context())
        self.assertEqual([item.name for item in self.fixture.source.iterdir()], ["strategy-spec-v01.json"])
        self.assertIn("only fileName and content", prompt)
        self.assertIn("No Markdown, explanation, extra fields, tools", prompt)
        self.assertIn("network, compiler, terminal, backtest, optimization, deployment, or live trade", prompt)
        self.assertIn("Keep every original guard and every immutable A-J requirement", prompt)

    def test_emitted_mt5_ticket_scans_satisfy_actual_loop_guard_without_truncating_cap(self):
        finding = "ea_for_loop_bounds_not_proven"
        recipes = self.recipes(self.repair(findings=[finding, "ea_position_cap_guard_missing"]))
        headers = re.findall(r"`(for\([^`]+\))`", recipes)
        position = next(header for header in headers if "PositionsTotal" in header)
        pending = next(header for header in headers if "OrdersTotal" in header)
        code = (
            "int CountManagedPositions(){ int count=0; "
            + position + " { ulong ticket=PositionGetTicket(i); if(ticket>0) count++; } "
            + pending + " { ulong ticket=OrderGetTicket(j); if(ticket>0) count++; } return count; }"
        )
        analyzer = context_support.pending_remove_support.BRIEF
        bounded = analyzer._compact_ea_for_loops_provably_bounded
        self.assertTrue(bounded(code))
        self.assertIn("Do not replace these with a fixed truncated scan", recipes)
        self.assertIn("Every other for loop needs a literal integer initializer", recipes)
        for bad in (
            code.replace("i>=0", "i>=minimumIndex"),
            code.replace("i--", "i++"),
            code.replace("PositionsTotal()-1", "PositionsTotal()+100"),
            code.replace("ulong ticket=PositionGetTicket(i);", "i=100; ulong ticket=PositionGetTicket(i);"),
            position + " count++;",
            position + " { " + pending + " { count++; } }",
        ):
            with self.subTest(source=bad):
                self.assertFalse(bounded(bad))
        mt4 = self.recipes(self.repair("mt4", findings=[finding]))
        self.assertEqual(mt4, f"- {finding}: {self.runner.EA_FACTORY_SOURCE_SEMANTIC_REPAIR_RECIPES[finding]}")
        self.assertNotIn("PositionsTotal", mt4)


if __name__ == "__main__":
    unittest.main()
