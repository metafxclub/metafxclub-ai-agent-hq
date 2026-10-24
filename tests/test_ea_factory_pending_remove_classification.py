"""Removal is management, while malformed/ambiguous requests stay entries."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "backend/local-runner/hq_backend/ea/ea_strategy_brief.py"
spec = importlib.util.spec_from_file_location("pending_remove_strategy_brief", MODULE_PATH)
BRIEF = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BRIEF)

REMOVE = """
bool RemoveManagedPending(ulong ticket) {
  if(ticket == 0) return(false);
  if(!OrderSelect(ticket)) return(false);
  if(OrderGetString(ORDER_SYMBOL) != _Symbol) return(false);
  if(OrderGetInteger(ORDER_MAGIC) != MagicNumber) return(false);
  long selectedType = OrderGetInteger(ORDER_TYPE);
  if(selectedType != ORDER_TYPE_BUY_STOP && selectedType != ORDER_TYPE_SELL_STOP) return(false);
  MqlTradeRequest cancelRequest = {};
  MqlTradeResult cancelResult = {};
  cancelRequest.action = TRADE_ACTION_REMOVE;
  cancelRequest.order = ticket;
  cancelRequest.symbol = _Symbol;
  cancelRequest.magic = MagicNumber;
  if(!OrderSend(cancelRequest, cancelResult)) return(false);
  return(cancelResult.retcode == TRADE_RETCODE_DONE);
}
"""


class PendingRemoveClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Reuse the exact existing passing MT5 integration control without
        # importing its unittest class, Bridge, Runner, or Runtime stores.
        tree = ast.parse((ROOT / "tests/test_ea_strategy_brief.py").read_text(encoding="utf-8"))
        fixture = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "valid_brief")
        namespace = {"BRIEF": BRIEF}
        exec(compile(ast.Module(body=[fixture], type_ignores=[]), "<pure brief fixture>", "exec"), namespace)
        brief = namespace["valid_brief"]()
        brief.update({field: "not_publicly_stated" for field in ("recoveryRules", "exitRules", "moneyManagement", "orderExecution")})
        cls.brief = BRIEF.normalize_strategy_brief(BRIEF.apply_strategy_brief_implementation_defaults(brief))
        cls.digest = BRIEF.compute_strategy_brief_digest(cls.brief)
        test = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "test_mt5_ordersendasync_is_forbidden_even_when_reachable_and_bounded")
        assignment = next(node for node in test.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "source" for target in node.targets))
        cls.control = eval(compile(ast.Expression(assignment.value), "<existing MT5 control>", "eval"), {"brief_digest": cls.digest})

    def analysis(self, source: str) -> dict:
        return BRIEF.analyze_compact_ea_source(
            source,
            strategy_brief=self.brief,
            strategy_brief_digest=self.digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(source.encode()).hexdigest(),
            target_platform="mt5",
        )

    def combined(self, helper: str = REMOVE, call: str | None = None) -> str:
        if call is None:
            call = "ulong pendingTicket = OrderGetTicket(0);\n  if(pendingTicket > 0) RemoveManagedPending(pendingTicket);"
        return self.control.replace("  if(Bars(_Symbol, _Period) < 3) return;", "  " + call + "\n  if(Bars(_Symbol, _Period) < 3) return;", 1) + helper

    def entry_count(self, source: str) -> int:
        code = BRIEF._indicator_lexical_views(source)[0]
        reachable = BRIEF._compact_ea_reachable_code(BRIEF._compact_ea_function_map(code))
        return len(BRIEF._mql_trade_call_records(reachable, source_code=code))

    def assert_rejected_remove(self, helper: str) -> None:
        source = self.combined(helper)
        self.assertEqual(self.entry_count(source), 2)
        self.assertFalse(self.analysis(source)["complete"])

    def test_owned_pending_stop_remove_does_not_need_entry_sizing_or_sl_tp(self) -> None:
        self.assertTrue(self.analysis(self.control)["complete"])
        source = self.combined()
        result = self.analysis(source)
        self.assertTrue(result["complete"], result)
        self.assertEqual(self.entry_count(source), 1)
        self.assertTrue(result["checks"]["tradeCallGraphExclusive"])
        code = BRIEF._indicator_lexical_views(source)[0]
        self.assertEqual(BRIEF._mql_trade_side_effect_call_names(code).count("ordersend"), 2)

    def test_braced_fail_closed_returns_and_whitespace_preserve_proof(self) -> None:
        helper = REMOVE.replace("return(false);", "{ return false; }").replace("cancelRequest.action", "cancelRequest . action")
        result = self.analysis(self.combined(helper))
        self.assertTrue(result["complete"], result)

    def test_extracted_helper_without_source_ownership_context_stays_entry(self) -> None:
        body = BRIEF._compact_ea_function_map(BRIEF._indicator_lexical_views(REMOVE)[0])["removemanagedpending"][0]
        self.assertEqual(len(BRIEF._mql_trade_call_records(body)), 1)

    def test_tautological_local_magic_or_parameter_shadow_is_not_ownership(self) -> None:
        self.assert_rejected_remove(REMOVE.replace("  if(ticket == 0)", "  long MagicNumber = OrderGetInteger(ORDER_MAGIC);\n  if(ticket == 0)"))
        self.assert_rejected_remove(REMOVE.replace("ulong ticket)", "ulong ticket, long MagicNumber)"))
        self.assert_rejected_remove(REMOVE.replace("  if(ticket == 0)", "  long other, MagicNumber;\n  if(ticket == 0)"))

    def test_foreign_global_magic_is_not_the_actual_entry_magic(self) -> None:
        source = self.combined(REMOVE.replace("MagicNumber", "ForeignMagic"))
        source = "input long ForeignMagic = 43210;\n" + source
        self.assertEqual(self.entry_count(source), 2)
        self.assertFalse(self.analysis(source)["complete"])

    def test_unknown_mutated_unconfigured_or_zero_magic_stays_entry(self) -> None:
        for old, new in (
            ("input int MagicNumber = 4186001;", "long MagicNumber = 4186001;"),
            ("input int MagicNumber = 4186001;", "input int MagicNumber = 0;"),
            ("request.magic = MagicNumber;", "request.magic = OtherMagic;"),
            ("request.magic = MagicNumber;", "request.magic = OrderGetInteger(ORDER_MAGIC);"),
            ("request.magic = MagicNumber;", "MagicNumber++; request.magic = MagicNumber;"),
            ("request.magic = MagicNumber;", "MutateMagic(&MagicNumber); request.magic = MagicNumber;"),
        ):
            with self.subTest(replacement=new):
                source = self.combined().replace(old, new)
                self.assertEqual(self.entry_count(source), 2)
                self.assertFalse(self.analysis(source)["complete"])

    def test_success_requires_checked_send_and_exact_done_retcode(self) -> None:
        for result in (
            "true", "cancelResult.retcode != 0", "cancelResult.retcode == TRADE_RETCODE_PLACED",
            "cancelResult.retcode == TRADE_RETCODE_DONE || cancelResult.retcode == TRADE_RETCODE_REJECT",
        ):
            with self.subTest(result=result):
                self.assert_rejected_remove(REMOVE.replace("cancelResult.retcode == TRADE_RETCODE_DONE", result))
        self.assert_rejected_remove(REMOVE.replace("  if(ticket == 0)", "  if(ticket > 100) return(true);\n  if(ticket == 0)"))

    def test_actual_entry_magic_cannot_be_stale_conditional_or_aliased(self) -> None:
        changes = (
            ("  OrderSend(request, result);", "  request = otherRequest;\n  OrderSend(request, result);"),
            ("  OrderSend(request, result);", "  MqlTradeRequest alias = request;\n  OrderSend(request, result);"),
            ("  OrderSend(request, result);", "  MutateRequest(request);\n  OrderSend(request, result);"),
            ("request.magic = MagicNumber;", "if(otherFlag) request.magic = MagicNumber;"),
            ("request.magic = MagicNumber;", "if(otherFlag) { request.magic = MagicNumber; }"),
            ("request.action = TRADE_ACTION_DEAL;", "if(otherFlag) request.action = TRADE_ACTION_DEAL;"),
        )
        for old, new in changes:
            with self.subTest(replacement=new):
                source = self.combined().replace(old, new)
                self.assertEqual(self.entry_count(source), 2)
                self.assertFalse(self.analysis(source)["complete"])

    def test_each_ticket_scope_and_type_check_is_mandatory(self) -> None:
        guards = (
            "  if(ticket == 0) return(false);\n",
            "  if(!OrderSelect(ticket)) return(false);\n",
            "  if(OrderGetString(ORDER_SYMBOL) != _Symbol) return(false);\n",
            "  if(OrderGetInteger(ORDER_MAGIC) != MagicNumber) return(false);\n",
            "  if(selectedType != ORDER_TYPE_BUY_STOP && selectedType != ORDER_TYPE_SELL_STOP) return(false);\n",
        )
        for guard in guards:
            with self.subTest(guard=guard):
                self.assert_rejected_remove(REMOVE.replace(guard, ""))

    def test_wrong_ticket_magic_symbol_or_pending_type_are_not_exempt(self) -> None:
        replacements = (
            ("cancelRequest.order = ticket;", "cancelRequest.order = ticket + 1;"),
            ("OrderSelect(ticket)", "OrderSelect(otherTicket)"),
            ("cancelRequest.magic = MagicNumber;", "cancelRequest.magic = otherMagic;"),
            ("cancelRequest.symbol = _Symbol;", "cancelRequest.symbol = otherSymbol;"),
            ("ORDER_TYPE_BUY_STOP", "ORDER_TYPE_BUY"),
            ("ORDER_TYPE_SELL_STOP", "ORDER_TYPE_SELL_LIMIT"),
            ("cancelRequest.order = ticket;", ""),
        )
        for old, new in replacements:
            with self.subTest(replacement=new):
                self.assert_rejected_remove(REMOVE.replace(old, new))

    def test_nonliteral_or_changed_action_is_not_exempt(self) -> None:
        actions = (
            "TRADE_ACTION_MODIFY", "TRADE_ACTION_PENDING", "TRADE_ACTION_DEAL",
            "actionFromCaller", "ticket > 100 ? TRADE_ACTION_REMOVE : TRADE_ACTION_PENDING",
        )
        for action in actions:
            with self.subTest(action=action):
                self.assert_rejected_remove(REMOVE.replace("TRADE_ACTION_REMOVE", action))
        for mutation in (
            "cancelRequest.action = TRADE_ACTION_PENDING;",
            "if(ticket > 100) cancelRequest.action = TRADE_ACTION_PENDING;",
            "if(ticket > 100) { cancelRequest.action = TRADE_ACTION_REMOVE; }",
        ):
            with self.subTest(mutation=mutation):
                self.assert_rejected_remove(REMOVE.replace("cancelRequest.order = ticket;", mutation + "\n  cancelRequest.order = ticket;"))

    def test_conditional_action_or_sibling_guard_cannot_dominate_send(self) -> None:
        self.assert_rejected_remove(REMOVE.replace("cancelRequest.action = TRADE_ACTION_REMOVE;", "if(ticket > 100) cancelRequest.action = TRADE_ACTION_REMOVE;"))
        self.assert_rejected_remove(REMOVE.replace("if(ticket == 0)", "if(otherFlag) if(ticket == 0)"))
        self.assert_rejected_remove(REMOVE.replace("if(ticket == 0)", "if(otherFlag) Print(1); else if(ticket == 0)"))
        self.assert_rejected_remove(REMOVE.replace("if(ticket == 0) return(false);", "if(otherFlag) { if(ticket == 0) return(false); }"))
        self.assert_rejected_remove(REMOVE.replace("if(OrderGetInteger(ORDER_MAGIC) != MagicNumber) return(false);", "if(otherFlag) { if(OrderGetInteger(ORDER_MAGIC) != MagicNumber) return(false); } else { Print(1); }"))

    def test_guards_from_another_function_do_not_prove_current_send(self) -> None:
        helper = REMOVE.replace("  MqlTradeRequest cancelRequest = {};", "  return(true);\n}\nbool UnscopedSend(ulong ticket) {\n  MqlTradeRequest cancelRequest = {};")
        self.assert_rejected_remove(helper.replace("return(true);", "return UnscopedSend(ticket);", 1))

    def test_ticket_kind_or_request_mutations_and_unknown_calls_are_not_exempt(self) -> None:
        mutations = (
            "ticket = otherTicket;", "selectedType = ORDER_TYPE_BUY_STOP;",
            "OrderSelect(otherTicket);", "TouchSelectedOrder();",
            "MutateRequest(cancelRequest);", "ZeroMemory(cancelRequest);",
            "MqlTradeRequest alias = cancelRequest;", "cancelRequest = otherRequest;",
            "cancelRequest.type = ORDER_TYPE_BUY_STOP;", "cancelRequest.volume = FixedLot;",
            "cancelRequest.price = Ask;",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assert_rejected_remove(REMOVE.replace("  if(!OrderSend", "  " + mutation + "\n  if(!OrderSend"))

    def test_fresh_request_and_checked_send_are_required(self) -> None:
        for old, new in (
            ("MqlTradeRequest cancelRequest = {};", "MqlTradeRequest cancelRequest;"),
            ("MqlTradeRequest cancelRequest = {};", "MqlTradeRequest cancelRequest = savedRequest;"),
            ("if(!OrderSend(cancelRequest, cancelResult)) return(false);", "OrderSend(cancelRequest, cancelResult);"),
        ):
            with self.subTest(replacement=new):
                self.assert_rejected_remove(REMOVE.replace(old, new))

    def test_request_alias_or_reuse_after_send_prevents_exemption(self) -> None:
        for mutation in ("MqlTradeRequest alias = cancelRequest;", "cancelRequest.action = TRADE_ACTION_PENDING;", "ReadOrMutate(cancelRequest);"):
            with self.subTest(mutation=mutation):
                self.assert_rejected_remove(REMOVE.replace("  return(cancelResult.retcode", "  " + mutation + "\n  return(cancelResult.retcode"))

    def test_comment_or_string_remove_token_cannot_prove_action(self) -> None:
        self.assert_rejected_remove(REMOVE.replace("cancelRequest.action = TRADE_ACTION_REMOVE;", "// cancelRequest.action = TRADE_ACTION_REMOVE;"))
        self.assert_rejected_remove(REMOVE.replace("cancelRequest.action = TRADE_ACTION_REMOVE;", 'Print("cancelRequest.action = TRADE_ACTION_REMOVE;");'))

    def test_unreachable_remove_still_fails_trade_side_effect_exclusivity(self) -> None:
        result = self.analysis(self.control + REMOVE)
        self.assertFalse(result["complete"])
        self.assertIn("ea_trade_call_outside_ontick_forbidden", result["findings"])

    def test_remove_from_oninit_still_fails_trade_side_effect_exclusivity(self) -> None:
        source = (self.control + REMOVE).replace("int OnInit() { return(INIT_SUCCEEDED); }", "int OnInit() { RemoveManagedPending(OrderGetTicket(0)); return(INIT_SUCCEEDED); }")
        result = self.analysis(source)
        self.assertFalse(result["complete"])
        self.assertIn("ea_trade_call_outside_ontick_forbidden", result["findings"])

    def test_constant_dead_cancel_and_existing_unsafe_entry_remain_rejected(self) -> None:
        source = self.combined(call="if(false) { RemoveManagedPending(OrderGetTicket(0)); }")
        self.assertIn("ea_constant_dead_branch_forbidden", self.analysis(source)["findings"])
        without_cap = self.combined().replace("if(CountManagedPositions() >= MaxOpenPositionsPerSymbolMagic) return;", "")
        self.assertFalse(self.analysis(without_cap)["complete"])
        self.assertIn("ea_position_cap_guard_missing", self.analysis(without_cap)["findings"])


if __name__ == "__main__":
    unittest.main()
