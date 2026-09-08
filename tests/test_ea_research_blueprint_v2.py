from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "backend" / "local-runner" / "ea_research_blueprint.py"
SCHEMA_PATH = ROOT / "contracts" / "research" / "ea-implementation-blueprint-v2.schema.json"


def load_contract_module():
    spec = importlib.util.spec_from_file_location("ea_research_blueprint_v2_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("Could not load EA research blueprint module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CONTRACT = load_contract_module()


def source_operand(indicator_id: str) -> dict:
    return {"kind": "indicator", "ref": indicator_id}


def cross_rule(
    rule_id: str,
    op: str,
    *,
    phase: str,
    side: str,
    source_status: str = "verified_fact",
) -> dict:
    return {
        "ruleId": rule_id,
        "phase": phase,
        "side": side,
        "enabled": True,
        "sourceStatus": source_status,
        "sourceRefs": ["S1"],
        "expression": {
            "op": op,
            "left": source_operand("ema_fast"),
            "right": source_operand("ema_slow"),
        },
        "humanTextTh": "ทดสอบการตัดกันของ EMA จากแท่งปิด",
    }


def input_record(input_id: str, default: int | float, used_by: list[str]) -> dict:
    input_type = "int" if isinstance(default, int) else "double"
    minimum = 1 if input_type == "int" else 0.01
    return {
        "inputId": input_id,
        "label": input_id.replace("_", " "),
        "type": input_type,
        "unit": "bars" if "period" in input_id else "value",
        "default": default,
        "min": minimum,
        "max": 500,
        "step": 1,
        "optimizable": True,
        "sourceStatus": "verified_fact",
        "sourceRefs": ["S1"],
        "usedByRuleIds": used_by,
    }


def disabled_managed_feature() -> dict:
    return {
        "enabled": False,
        "sourceStatus": "verified_fact",
        "sourceRefs": ["S1"],
        "parameters": {},
        "rules": [],
    }


def ready_blueprint() -> dict:
    buy_entry = cross_rule("ENTRY_BUY_001", "cross_above", phase="entry", side="buy")
    buy_exit = cross_rule("EXIT_BUY_001", "cross_below", phase="exit", side="buy")
    return {
        "schemaVersion": "ea-ready-strategy-research/2.0.0",
        "strategyId": "ema-cross-v2",
        "researchRevision": 1,
        "checkedAt": "2026-09-08T09:30:00+07:00",
        "barSemantics": {
            "bar0": "forming",
            "signalBar": 1,
            "previousBar": 2,
            "evaluateOn": "new_closed_bar",
            "lookaheadForbidden": True,
            "equalityPolicy": "touch_then_break",
        },
        "scope": {
            "systemName": "EMA 10/60 Closed-bar Cross",
            "strategyFamily": "trend_following",
            "platforms": ["MT5", "MT4"],
            "market": "forex",
            "symbols": ["gbpusd", "eurusd"],
            "signalTimeframe": "h1",
            "executionTimeframe": "h1",
            "timezone": "UTC",
            "sessions": [],
            "enabledSides": ["buy"],
            "suitableFor": ["EA", "backtest"],
            "onePositionPerSymbol": True,
        },
        "inputs": [
            input_record("fast_period", 10, ["ENTRY_BUY_001", "EXIT_BUY_001"]),
            input_record("slow_period", 60, ["ENTRY_BUY_001", "EXIT_BUY_001"]),
            input_record("fixed_lot", 0.1, []),
            input_record("sl_pips", 30, []),
            input_record("tp_pips", 60, []),
        ],
        "indicators": [
            {
                "indicatorId": "ema_fast",
                "kind": "EMA",
                "timeframe": "signal",
                "parameters": {"period": {"inputRef": "fast_period"}},
                "appliedPrice": "close",
                "outputLine": "main",
                "sourceStatus": "verified_fact",
                "sourceRefs": ["S1"],
            },
            {
                "indicatorId": "ema_slow",
                "kind": "EMA",
                "timeframe": "signal",
                "parameters": {"period": {"inputRef": "slow_period"}},
                "appliedPrice": "close",
                "outputLine": "main",
                "sourceStatus": "verified_fact",
                "sourceRefs": ["S1"],
            },
        ],
        "setup": {"rules": []},
        "entry": {
            "buy": {
                "enabled": True,
                "disabledReason": "",
                "rules": [buy_entry],
                "orderType": "market",
                "cooldownBars": 1,
            },
            "sell": {
                "enabled": False,
                "disabledReason": "Source defines buy side only",
                "rules": [],
            },
        },
        "exit": {
            "buy": {
                "enabled": True,
                "disabledReason": "",
                "rules": [buy_exit],
            },
            "sell": {
                "enabled": False,
                "disabledReason": "Sell side is disabled",
                "rules": [],
            },
        },
        "orderManagement": {
            "breakEven": disabled_managed_feature(),
            "trailingStop": disabled_managed_feature(),
            "partialClose": {
                "enabled": False,
                "sourceStatus": "verified_fact",
                "sourceRefs": ["S1"],
                "steps": [],
                "rules": [],
            },
            "scaleIn": disabled_managed_feature(),
            "scaleOut": disabled_managed_feature(),
            "modifyStopLoss": disabled_managed_feature(),
            "modifyTakeProfit": disabled_managed_feature(),
            "pendingOrders": disabled_managed_feature(),
            "rules": [],
        },
        "tpSl": {
            "stopLoss": {
                "enabled": True,
                "type": "fixed_pips",
                "valueInputRef": "sl_pips",
                "unit": "pip",
                "reference": "entry_price",
                "placementTiming": "with_entry",
                "minimumStopDistancePolicy": "reject_entry",
                "freezeLevelPolicy": "reject_entry",
                "neverWorsen": True,
                "sourceStatus": "verified_fact",
                "sourceRefs": ["S1"],
            },
            "takeProfit": {
                "enabled": True,
                "type": "fixed_pips",
                "valueInputRef": "tp_pips",
                "unit": "pip",
                "reference": "entry_price",
                "placementTiming": "with_entry",
                "minimumStopDistancePolicy": "reject_entry",
                "freezeLevelPolicy": "reject_entry",
                "sourceStatus": "verified_fact",
                "sourceRefs": ["S1"],
            },
            "sideOverrides": {"buy": {}, "sell": {}},
        },
        "riskAndSizing": {
            "lotMode": "fixed_lot",
            "fixedLotInputRef": "fixed_lot",
            "maxOpenPositions": 1,
            "maxTotalLots": 1.0,
            "includeSpreadCommissionSlippage": True,
            "normalizeToBrokerLotStep": True,
        },
        "recovery": {
            "enabled": False,
            "mode": "none",
            "sourceStatus": "verified_fact",
            "sourceRefs": ["S1"],
        },
        "execution": {
            "evaluateOn": "new_closed_bar",
            "evaluationOrder": ["safety", "manage", "exit", "entry"],
            "entryOrderType": "market",
            "duplicateSignalPolicy": "one_decision_per_symbol_bar",
            "priceNormalization": {
                "useBrokerDigits": True,
                "useBrokerTickSize": True,
                "invalidPricePolicy": "normalize_nearest_tick",
            },
            "retryPolicy": {
                "maxRetries": 1,
                "retryableErrors": ["price_changed", "requote"],
                "backoffMilliseconds": 250,
                "exhaustedAction": "abort_signal",
            },
            "restartPersistence": {
                "restoreManagedTickets": True,
                "restoreStateMachine": True,
                "stateKey": "strategyId:symbol:magic",
                "missingStatePolicy": "reconstruct_from_broker",
            },
        },
        "stateMachine": [
            {
                "state": "FLAT",
                "transitions": [{"to": "LONG", "whenRuleIds": ["ENTRY_BUY_001"]}],
            },
            {
                "state": "LONG",
                "transitions": [{"to": "FLAT", "whenRuleIds": ["EXIT_BUY_001"]}],
            },
        ],
        "conflicts": [],
        "precedence": [
            "emergency_stop",
            "hard_stop",
            "normal_exit",
            "position_management",
            "new_entry",
        ],
        "pseudocode": {
            "language": "platform-neutral",
            "lines": [
                "On a new closed H1 bar, evaluate safety then existing positions.",
                "When ENTRY_BUY_001 is true and state is FLAT, open one Buy.",
                "When EXIT_BUY_001 is true, close the managed Buy.",
            ],
        },
        "testCases": [
            {
                "caseId": "entry-buy-positive",
                "kind": "positive",
                "ruleIds": ["ENTRY_BUY_001"],
                "given": {"fast2": 1.0, "slow2": 1.0, "fast1": 1.1, "slow1": 1.0},
                "when": "new closed bar",
                "expected": {"signal": "buy"},
            },
            {
                "caseId": "entry-buy-negative",
                "kind": "negative",
                "ruleIds": ["ENTRY_BUY_001"],
                "given": {"fast2": 1.1, "slow2": 1.0, "fast1": 1.2, "slow1": 1.0},
                "when": "new closed bar",
                "expected": {"signal": "none"},
            },
            {
                "caseId": "entry-buy-boundary",
                "kind": "boundary",
                "ruleIds": ["ENTRY_BUY_001"],
                "given": {"fast2": 1.0, "slow2": 1.0, "fast1": 1.0, "slow1": 1.0},
                "when": "new closed bar",
                "expected": {"signal": "none"},
            },
            {
                "caseId": "exit-buy-positive",
                "kind": "positive",
                "ruleIds": ["EXIT_BUY_001"],
                "given": {"fast2": 1.0, "slow2": 1.0, "fast1": 0.9, "slow1": 1.0},
                "when": "new closed bar",
                "expected": {"signal": "exit_buy"},
            },
            {
                "caseId": "exit-buy-negative",
                "kind": "negative",
                "ruleIds": ["EXIT_BUY_001"],
                "given": {"fast2": 0.9, "slow2": 1.0, "fast1": 0.8, "slow1": 1.0},
                "when": "new closed bar",
                "expected": {"signal": "none"},
            },
            {
                "caseId": "exit-buy-boundary",
                "kind": "boundary",
                "ruleIds": ["EXIT_BUY_001"],
                "given": {"fast2": 1.0, "slow2": 1.0, "fast1": 1.0, "slow1": 1.0},
                "when": "new closed bar",
                "expected": {"signal": "none"},
            },
            {
                "caseId": "exit-buy-lifecycle",
                "kind": "lifecycle",
                "ruleIds": ["EXIT_BUY_001"],
                "given": {"position": "buy", "cross": "below"},
                "when": "new closed bar",
                "expected": {"position": "flat"},
            },
        ],
        "evidenceMap": [
            {
                "sourceRef": "S1",
                "url": "https://example.com/ema-cross",
                "title": "EMA crossover specification",
                "checkedAt": "2026-09-08T09:30:00+07:00",
            },
            {
                "sourceRef": "S2",
                "url": "https://example.org/closed-bar-cross",
                "title": "Independent closed-bar crossover reference",
                "checkedAt": "2026-09-08T09:31:00+07:00",
            },
        ],
        "assumptions": [],
        "unknowns": [],
        "completeness": {
            "status": "ready",
            "score": 100,
            "eaHandoffAllowed": True,
            "deterministicBacktestAllowed": True,
            "blockingIssues": [],
            "warnings": [],
            "unknownPaths": [],
            "conflictPaths": [],
        },
    }


def activate_martingale_recovery(blueprint: dict) -> dict:
    recovery_trigger = {
        "op": ">=",
        "left": {"kind": "basket", "field": "floating_loss_currency"},
        "right": {"kind": "constant", "value": 10.0},
    }
    blueprint["recovery"] = {
        "enabled": True,
        "mode": "martingale",
        "trigger": copy.deepcopy(recovery_trigger),
        "spacing": {
            "method": "fixed_pips",
            "reference": "previous_recovery_entry",
            "unit": "pip",
            "value": 25.0,
            "adverseMoveOnly": True,
            "sourceStatus": "verified_fact",
            "sourceRefs": ["S1"],
        },
        "direction": "same",
        "maxLevels": 3,
        "lotFormula": {
            "mode": "multiplier",
            "baseLotInputRef": "fixed_lot",
            "multiplier": 2.0,
            "levelVariable": "recovery_level",
            "normalizeToBrokerLotStep": True,
            "sourceStatus": "verified_fact",
            "sourceRefs": ["S1"],
        },
        "lotCap": 0.4,
        "basketTakeProfit": {
            "enabled": True,
            "method": "fixed_currency",
            "reference": "basket_profit",
            "unit": "account_currency",
            "value": 10.0,
            "sourceStatus": "verified_fact",
            "sourceRefs": ["S1"],
        },
        "basketStopLoss": {
            "enabled": True,
            "method": "fixed_currency",
            "reference": "basket_loss",
            "unit": "account_currency",
            "value": 50.0,
            "sourceStatus": "verified_fact",
            "sourceRefs": ["S1"],
        },
        "equityStopPercent": 20.0,
        "maxBasketLots": 1.0,
        "maxDrawdownPercent": 20.0,
        "resetCondition": {
            "op": "==",
            "left": {"kind": "position", "field": "managed_count"},
            "right": {"kind": "constant", "value": 0},
        },
        "abortCondition": {
            "op": ">=",
            "left": {"kind": "account", "field": "drawdown_percent"},
            "right": {"kind": "constant", "value": 20.0},
        },
        "reentryPolicy": {
            "enabled": False,
            "allowedAfter": "never",
            "cooldownBars": 0,
            "maxReentries": 0,
            "sameSignalRequired": True,
            "sourceStatus": "verified_fact",
            "sourceRefs": ["S1"],
        },
        "levelRules": [
            {
                "ruleId": "RECOVERY_LEVEL_001",
                "phase": "recovery",
                "side": "both",
                "enabled": True,
                "sourceStatus": "verified_fact",
                "sourceRefs": ["S1"],
                "expression": copy.deepcopy(recovery_trigger),
                "humanTextTh": "เปิดไม้แก้เมื่อขาดทุนลอยตัวถึงเกณฑ์และราคาห่างตาม spacing",
            }
        ],
        "sourceStatus": "verified_fact",
        "sourceRefs": ["S1"],
    }
    blueprint["testCases"].append(
        {
            "caseId": "recovery-level-lifecycle",
            "kind": "lifecycle",
            "ruleIds": ["RECOVERY_LEVEL_001"],
            "given": {"floatingLoss": 10.0, "recoveryLevel": 0},
            "when": "a new recovery level is opened",
            "expected": {"recoveryLevel": 1, "lot": 0.2},
        }
    )
    return blueprint


def issue_codes(blueprint: object) -> set[str]:
    return {item["code"] for item in CONTRACT.validate_blueprint(blueprint)}


class EAResearchBlueprintV2Tests(unittest.TestCase):
    def test_schema_is_checked_in_and_names_the_canonical_contract(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(
            schema["properties"]["schemaVersion"]["const"],
            CONTRACT.SCHEMA_VERSION,
        )
        self.assertTrue(set(CONTRACT.CLOSED_BAR_SEMANTICS).issubset(schema["$defs"]["barSemantics"]["required"]))
        self.assertEqual(CONTRACT.SCHEMA_PATH.resolve(), SCHEMA_PATH.resolve())
        management_required = set(schema["$defs"]["orderManagement"]["required"])
        self.assertTrue(
            {
                "scaleIn",
                "scaleOut",
                "modifyStopLoss",
                "modifyTakeProfit",
            }.issubset(management_required)
        )
        self.assertIn("sideOverrides", schema["$defs"]["tpSl"]["required"])
        self.assertIn("lotSequence", schema["$defs"]["riskAndSizing"]["properties"])
        self.assertEqual(
            schema["$defs"]["execution"]["properties"]["priceNormalization"]["$ref"],
            "#/$defs/priceNormalizationPolicy",
        )
        self.assertEqual(
            schema["$defs"]["managedFeature"]["properties"]["action"]["$ref"],
            "#/$defs/managementAction",
        )
        self.assertEqual(
            set(schema["$defs"]["execution"]["properties"]["evaluationOrder"]["items"]["enum"]),
            {"safety", "recovery", "manage", "exit", "entry"},
        )

    def test_unknown_input_can_preserve_null_without_inventing_a_default(self) -> None:
        blueprint = ready_blueprint()
        blueprint["inputs"][0].update(
            default=None,
            sourceStatus="unknown",
            sourceRefs=[],
            usedByRuleIds=["RULE_PLACEHOLDER_UNKNOWN"],
        )

        self.assertIn("READINESS_UNRESOLVED", issue_codes(blueprint))
        blueprint["completeness"].update(
            status="needs_clarification",
            score=65,
            eaHandoffAllowed=False,
            deterministicBacktestAllowed=False,
            blockingIssues=[
                {
                    "code": "FAST_PERIOD_UNKNOWN",
                    "path": "$.inputs[0].default",
                    "messageTh": "ยังไม่ทราบค่า Fast MA period",
                    "questionTh": "โปรดยืนยันค่า Fast MA period",
                }
            ],
            unknownPaths=["$.inputs[0].default"],
        )
        self.assertEqual(CONTRACT.validate_blueprint(blueprint), [])
        with self.assertRaises(CONTRACT.BlueprintValidationError):
            CONTRACT.normalize_blueprint(blueprint, require_ready=True)

        verified = ready_blueprint()
        verified["inputs"][0].update(
            default=None,
            usedByRuleIds=["RULE_PLACEHOLDER_UNKNOWN"],
        )
        verified_codes = issue_codes(verified)
        self.assertIn("INPUT_DEFAULT_TYPE", verified_codes)
        self.assertIn("RULE_REF_UNDEFINED", verified_codes)

    def test_enabled_management_requires_idempotency_cadence_and_stop_guard(self) -> None:
        blueprint = ready_blueprint()
        blueprint["orderManagement"]["modifyStopLoss"].update(
            enabled=True,
            trigger={"op": "once_per_bar", "barShift": 1},
            action={"kind": "move_stop"},
        )
        codes = issue_codes(blueprint)
        self.assertIn("READINESS_UNRESOLVED", codes)

    def test_ready_requires_two_independent_public_evidence_domains(self) -> None:
        one_source = ready_blueprint()
        one_source["evidenceMap"] = one_source["evidenceMap"][:1]
        self.assertIn("READINESS_UNRESOLVED", issue_codes(one_source))

        same_domain = ready_blueprint()
        same_domain["evidenceMap"][1]["url"] = "https://docs.example.com/another-page"
        self.assertIn("READINESS_UNRESOLVED", issue_codes(same_domain))

        local_source = ready_blueprint()
        local_source["evidenceMap"][1]["url"] = "http://127.0.0.1:4186/evidence"
        self.assertIn("SOURCE_URL_NOT_PUBLIC", issue_codes(local_source))

    def test_operator_assumption_only_core_rules_cannot_claim_ready(self) -> None:
        blueprint = ready_blueprint()
        for section in ("entry", "exit"):
            blueprint[section]["buy"]["rules"][0]["sourceStatus"] = "operator_assumption"
        blueprint["assumptions"] = [
            {
                "assumptionId": "A1",
                "description": "Operator explicitly confirms the chosen entry and exit convention",
                "confirmed": True,
                "affectsExecution": True,
                "affectsPaths": ["$.entry.buy.rules[0]", "$.exit.buy.rules[0]"],
            }
        ]
        self.assertIn("READINESS_UNRESOLVED", issue_codes(blueprint))

        blueprint["exit"]["buy"]["rules"][0]["sourceStatus"] = "derived_expansion"
        self.assertEqual(CONTRACT.validate_blueprint(blueprint), [])

    def test_enabled_management_requires_trigger_action_parameters_rule_and_lifecycle(self) -> None:
        incomplete = ready_blueprint()
        incomplete["orderManagement"]["modifyStopLoss"].update(
            enabled=True,
            trigger={"op": "once_per_bar", "barShift": 1},
            action={"kind": "move_stop_loss"},
            cadence="new_closed_bar",
            idempotent=True,
            precedence=40,
            neverWorsenStop=True,
        )
        self.assertIn("READINESS_UNRESOLVED", issue_codes(incomplete))

        complete = ready_blueprint()
        rule = {
            "ruleId": "MODIFY_SL_001",
            "phase": "modify",
            "side": "buy",
            "enabled": True,
            "sourceStatus": "verified_fact",
            "sourceRefs": ["S1"],
            "expression": {"op": "once_per_bar", "barShift": 1},
            "humanTextTh": "เลื่อน Stop Loss หนึ่งครั้งต่อแท่งปิดตามพารามิเตอร์",
        }
        complete["orderManagement"]["modifyStopLoss"].update(
            enabled=True,
            trigger=copy.deepcopy(rule["expression"]),
            action={"kind": "move_stop_loss"},
            parameters={"target": "entry_price", "bufferPoints": 0},
            rules=[rule],
            cadence="new_closed_bar",
            idempotent=True,
            precedence=40,
            neverWorsenStop=True,
        )
        complete["testCases"].append(
            {
                "caseId": "modify-sl-lifecycle",
                "kind": "lifecycle",
                "ruleIds": ["MODIFY_SL_001"],
                "given": {"position": "long", "stop": "below_entry"},
                "when": "a new closed bar is processed",
                "expected": {"stop": "entry_price", "secondCall": "no_change"},
            }
        )
        complete["pseudocode"]["lines"].append(
            "When MODIFY_SL_001 is true, move the managed stop to entry price idempotently."
        )
        self.assertEqual(CONTRACT.validate_blueprint(complete), [])

    def test_lot_mode_and_execution_policies_are_typed_and_bounded(self) -> None:
        invalid_lot = ready_blueprint()
        invalid_lot["riskAndSizing"]["lotMode"] = "whatever"
        self.assertIn("LOT_MODE_INVALID", issue_codes(invalid_lot))

        sequence = ready_blueprint()
        sequence["riskAndSizing"]["lotMode"] = "sequence"
        self.assertIn("READINESS_UNRESOLVED", issue_codes(sequence))
        sequence["riskAndSizing"]["lotSequence"] = [0.1, 0.2, 0.3]
        self.assertEqual(CONTRACT.validate_blueprint(sequence), [])

        unsafe_order = ready_blueprint()
        unsafe_order["execution"]["evaluationOrder"] = ["entry", "exit"]
        self.assertIn("EXECUTION_ORDER_UNSAFE", issue_codes(unsafe_order))

        unbounded_retry = ready_blueprint()
        unbounded_retry["execution"]["retryPolicy"]["maxRetries"] = 99
        self.assertIn("RETRY_LIMIT_INVALID", issue_codes(unbounded_retry))

    def test_limit_entry_requires_deterministic_pending_lifecycle(self) -> None:
        incomplete = ready_blueprint()
        incomplete["entry"]["buy"]["orderType"] = "limit"
        incomplete["execution"]["entryOrderType"] = "limit"
        self.assertIn("READINESS_UNRESOLVED", issue_codes(incomplete))

        complete = ready_blueprint()
        complete["entry"]["buy"]["orderType"] = "limit"
        complete["execution"]["entryOrderType"] = "limit"
        pending_rule = cross_rule(
            "PENDING_PLACE_001",
            "cross_above",
            phase="modify",
            side="buy",
        )
        complete["orderManagement"]["pendingOrders"].update(
            enabled=True,
            trigger=copy.deepcopy(pending_rule["expression"]),
            action={"kind": "place_pending"},
            parameters={
                "orderType": "limit",
                "entryPrice": {
                    "method": "offset_pips",
                    "reference": "ask",
                    "direction": "below",
                    "value": 10.0,
                },
                "expiry": {"mode": "gtc"},
            },
            rules=[pending_rule],
            cadence="new_closed_bar",
            idempotent=True,
            precedence=80,
        )
        complete["stateMachine"][0]["transitions"][0]["to"] = "PENDING"
        complete["stateMachine"].append(
            {"state": "PENDING", "transitions": [{"to": "LONG", "whenRuleIds": []}]}
        )
        complete["testCases"].extend(
            [
                {
                    "caseId": "pending-place-boundary",
                    "kind": "boundary",
                    "ruleIds": ["PENDING_PLACE_001"],
                    "given": {"fast2": 1.0, "slow2": 1.0, "fast1": 1.0, "slow1": 1.0},
                    "when": "new closed bar",
                    "expected": {"pendingOrder": "none"},
                },
                {
                    "caseId": "pending-place-lifecycle",
                    "kind": "lifecycle",
                    "ruleIds": ["PENDING_PLACE_001"],
                    "given": {"state": "FLAT", "entrySignal": True},
                    "when": "limit order is accepted then filled",
                    "expected": {"states": ["PENDING", "LONG"]},
                },
            ]
        )
        complete["pseudocode"]["lines"].append(
            "When PENDING_PLACE_001 is true, place one Buy Limit and move FLAT to PENDING; on fill move to LONG."
        )
        self.assertEqual(CONTRACT.validate_blueprint(complete), [])

    def test_state_machine_and_pseudocode_cover_enabled_lifecycle(self) -> None:
        missing_state = ready_blueprint()
        missing_state["stateMachine"] = [missing_state["stateMachine"][0]]
        self.assertIn("READINESS_UNRESOLVED", issue_codes(missing_state))

        missing_pseudocode = ready_blueprint()
        missing_pseudocode["pseudocode"]["lines"] = ["Evaluate a generic strategy on each closed bar."]
        self.assertIn("READINESS_UNRESOLVED", issue_codes(missing_pseudocode))

    def test_side_specific_stop_override_cannot_worsen_risk(self) -> None:
        blueprint = ready_blueprint()
        override = copy.deepcopy(blueprint["tpSl"]["stopLoss"])
        override["neverWorsen"] = False
        blueprint["tpSl"]["sideOverrides"]["buy"]["stopLoss"] = override
        self.assertIn("READINESS_UNRESOLVED", issue_codes(blueprint))

    def test_cross_rules_require_boundary_test_coverage(self) -> None:
        blueprint = ready_blueprint()
        blueprint["testCases"] = [
            item for item in blueprint["testCases"] if item["kind"] != "boundary"
        ]
        self.assertIn("READINESS_UNRESOLVED", issue_codes(blueprint))

    def test_normalization_expands_closed_bar_crosses_exactly(self) -> None:
        normalized = CONTRACT.normalize_blueprint(ready_blueprint(), require_ready=True)
        above = normalized["entry"]["buy"]["rules"][0]["expression"]
        below = normalized["exit"]["buy"]["rules"][0]["expression"]

        self.assertEqual(
            above["expanded"]["all"],
            [
                {
                    "op": "<=",
                    "left": {"kind": "indicator", "ref": "ema_fast", "shift": 2},
                    "right": {"kind": "indicator", "ref": "ema_slow", "shift": 2},
                },
                {
                    "op": ">",
                    "left": {"kind": "indicator", "ref": "ema_fast", "shift": 1},
                    "right": {"kind": "indicator", "ref": "ema_slow", "shift": 1},
                },
            ],
        )
        self.assertEqual([item["op"] for item in below["expanded"]["all"]], [">=", "<"])
        self.assertEqual(normalized["scope"]["platforms"], ["MT4", "MT5"])
        self.assertEqual(normalized["scope"]["symbols"], ["EURUSD", "GBPUSD"])

    def test_wrong_cross_expansion_is_rejected_with_stable_path_and_code(self) -> None:
        blueprint = ready_blueprint()
        expression = blueprint["entry"]["buy"]["rules"][0]["expression"]
        expression["previousShift"] = 2
        expression["currentShift"] = 1
        expression["expanded"] = {
            "all": [
                {
                    "op": ">=",
                    "left": {"kind": "indicator", "ref": "ema_fast", "shift": 2},
                    "right": {"kind": "indicator", "ref": "ema_slow", "shift": 2},
                },
                {
                    "op": "<",
                    "left": {"kind": "indicator", "ref": "ema_fast", "shift": 1},
                    "right": {"kind": "indicator", "ref": "ema_slow", "shift": 1},
                },
            ]
        }
        issues = CONTRACT.validate_blueprint(blueprint)
        mismatch = next(item for item in issues if item["code"] == "CROSS_EXPANSION_MISMATCH")
        self.assertEqual(mismatch["path"], "$.entry.buy.rules[0].expression.expanded")

    def test_closed_bar_contract_rejects_any_forming_bar_operand(self) -> None:
        blueprint = ready_blueprint()
        blueprint["entry"]["buy"]["rules"][0]["expression"] = {
            "op": ">",
            "left": {"kind": "price", "field": "close", "shift": 0},
            "right": {"kind": "indicator", "ref": "ema_slow", "shift": 1},
        }
        self.assertIn("CLOSED_BAR_SHIFT_ZERO", issue_codes(blueprint))

    def test_reference_integrity_covers_sources_indicators_inputs_and_rules(self) -> None:
        cases: list[tuple[str, callable]] = [
            (
                "SOURCE_REF_UNDEFINED",
                lambda value: value["entry"]["buy"]["rules"][0].update(sourceRefs=["S404"]),
            ),
            (
                "INDICATOR_REF_UNDEFINED",
                lambda value: value["entry"]["buy"]["rules"][0]["expression"].update(
                    left={"kind": "indicator", "ref": "missing_indicator"}
                ),
            ),
            (
                "INPUT_REF_UNDEFINED",
                lambda value: value["indicators"][0]["parameters"].update(
                    period={"inputRef": "missing_input"}
                ),
            ),
            (
                "RULE_REF_UNDEFINED",
                lambda value: value["inputs"][0].update(usedByRuleIds=["ENTRY_MISSING"]),
            ),
        ]
        for expected_code, mutate in cases:
            with self.subTest(expected_code=expected_code):
                blueprint = ready_blueprint()
                mutate(blueprint)
                self.assertIn(expected_code, issue_codes(blueprint))

    def test_reference_integrity_covers_protection_risk_execution_and_states(self) -> None:
        cases: list[tuple[str, callable]] = [
            (
                "INPUT_REF_UNDEFINED",
                lambda value: value["tpSl"]["stopLoss"].update(
                    valueInputRef="missing_sl_input"
                ),
            ),
            (
                "INPUT_REF_UNDEFINED",
                lambda value: value["riskAndSizing"].update(
                    fixedLotInputRef="missing_lot_input"
                ),
            ),
            (
                "INPUT_REF_UNDEFINED",
                lambda value: value["execution"].update(
                    maxSpreadInputRef="missing_spread_input"
                ),
            ),
            (
                "STATE_REF_UNDEFINED",
                lambda value: value["stateMachine"][0]["transitions"][0].update(
                    to="MISSING_STATE"
                ),
            ),
            (
                "RULE_REF_UNDEFINED",
                lambda value: value["stateMachine"][0]["transitions"][0].update(
                    whenRuleIds=["ENTRY_MISSING"]
                ),
            ),
        ]
        for expected_code, mutate in cases:
            with self.subTest(expected_code=expected_code):
                blueprint = ready_blueprint()
                mutate(blueprint)
                self.assertIn(expected_code, issue_codes(blueprint))

    def test_partial_close_and_recovery_have_bounded_safety_contracts(self) -> None:
        blueprint = ready_blueprint()
        partial = blueprint["orderManagement"]["partialClose"]
        partial.update(
            enabled=True,
            steps=[
                {
                    "stepId": "partial-one",
                    "trigger": {
                        "op": ">=",
                        "left": {"kind": "price", "field": "close", "shift": 1},
                        "right": {"kind": "constant", "value": 1.0},
                    },
                    "closePercent": 60,
                    "onceOnly": True,
                },
                {
                    "stepId": "partial-two",
                    "trigger": {
                        "op": ">=",
                        "left": {"kind": "price", "field": "close", "shift": 1},
                        "right": {"kind": "constant", "value": 2.0},
                    },
                    "closePercent": 50,
                    "onceOnly": False,
                },
            ],
        )
        codes = issue_codes(blueprint)
        self.assertIn("PARTIAL_TOTAL_INVALID", codes)
        self.assertIn("PARTIAL_ONCE_REQUIRED", codes)

        recovery = ready_blueprint()
        recovery["recovery"].update(enabled=True, mode="martingale")
        self.assertIn("READINESS_UNRESOLVED", issue_codes(recovery))

    def test_detailed_active_recovery_is_ea_ready_and_canonical(self) -> None:
        blueprint = activate_martingale_recovery(ready_blueprint())
        normalized = CONTRACT.normalize_blueprint(blueprint)

        self.assertEqual(CONTRACT.validate_blueprint(normalized), [])
        self.assertEqual(normalized["recovery"]["spacing"]["method"], "fixed_pips")
        self.assertEqual(normalized["recovery"]["lotFormula"]["mode"], "multiplier")
        self.assertEqual(normalized["recovery"]["levelRules"][0]["phase"], "recovery")

    def test_active_recovery_rejects_nonsemantic_placeholder_objects(self) -> None:
        blueprint = activate_martingale_recovery(ready_blueprint())
        for field in ("spacing", "lotFormula", "basketTakeProfit", "basketStopLoss"):
            blueprint["recovery"][field] = {"garbage": True}

        issues = CONTRACT.validate_blueprint(blueprint)
        paths = {item["path"] for item in issues if item["code"] == "UNKNOWN_FIELD"}
        self.assertTrue(
            {
                "$.recovery.spacing.garbage",
                "$.recovery.lotFormula.garbage",
                "$.recovery.basketTakeProfit.garbage",
                "$.recovery.basketStopLoss.garbage",
            }.issubset(paths)
        )
        self.assertIn("READINESS_UNRESOLVED", {item["code"] for item in issues})

    def test_active_recovery_requires_caps_lifecycle_and_mode_determinants(self) -> None:
        blueprint = activate_martingale_recovery(ready_blueprint())
        del blueprint["recovery"]["maxBasketLots"]
        blueprint["recovery"]["maxDrawdownPercent"] = 101
        blueprint["recovery"]["lotFormula"]["multiplier"] = 1.0
        blueprint["recovery"]["reentryPolicy"].update(
            enabled=True,
            allowedAfter="basket_close",
            maxReentries=1,
        )
        blueprint["recovery"]["levelRules"] = []

        codes = issue_codes(blueprint)
        self.assertIn("RECOVERY_PERCENT_INVALID", codes)
        self.assertIn("READINESS_UNRESOLVED", codes)

    def test_hedging_requires_typed_open_close_and_lot_lifecycle(self) -> None:
        blueprint = activate_martingale_recovery(ready_blueprint())
        blueprint["recovery"].update(mode="hedging", hedgeLifecycle={"garbage": True})

        issues = CONTRACT.validate_blueprint(blueprint)
        self.assertIn("$.recovery.hedgeLifecycle.garbage", {item["path"] for item in issues})
        self.assertIn("READINESS_UNRESOLVED", {item["code"] for item in issues})

    def test_nonfinite_numbers_return_path_aware_error(self) -> None:
        blueprint = ready_blueprint()
        blueprint["riskAndSizing"]["maxTotalLots"] = float("nan")
        issues = CONTRACT.validate_blueprint(blueprint)
        issue = next(item for item in issues if item["code"] == "NUMBER_NOT_FINITE")
        self.assertEqual(issue["path"], "$.riskAndSizing.maxTotalLots")

    def test_unresolved_rule_cannot_claim_ea_handoff(self) -> None:
        blueprint = ready_blueprint()
        rule = blueprint["entry"]["buy"]["rules"][0]
        rule["sourceStatus"] = "unknown"
        rule["sourceRefs"] = []
        rule["expression"] = {"op": "unknown"}

        self.assertIn("READINESS_UNRESOLVED", issue_codes(blueprint))

        blueprint["completeness"].update(
            status="needs_clarification",
            score=65,
            eaHandoffAllowed=False,
            deterministicBacktestAllowed=False,
            blockingIssues=[
                {
                    "code": "ENTRY_UNKNOWN",
                    "path": "$.entry.buy.rules[0]",
                    "messageTh": "ยังไม่ทราบเงื่อนไขเข้า Buy",
                    "questionTh": "โปรดยืนยันเงื่อนไข",
                }
            ],
            unknownPaths=["$.entry.buy.rules[0]"],
        )
        self.assertEqual(CONTRACT.validate_blueprint(blueprint), [])
        with self.assertRaises(CONTRACT.BlueprintValidationError) as raised:
            CONTRACT.normalize_blueprint(blueprint, require_ready=True)
        self.assertIn("EA_HANDOFF_REQUIRED", {item["code"] for item in raised.exception.issues})

    def test_digest_is_independent_of_dict_and_set_like_input_order(self) -> None:
        first = ready_blueprint()
        second = copy.deepcopy(first)
        second["scope"]["platforms"].reverse()
        second["scope"]["symbols"].reverse()
        second["evidenceMap"].reverse()
        second = dict(reversed(list(second.items())))

        self.assertEqual(
            CONTRACT.compute_blueprint_digest(first),
            CONTRACT.compute_blueprint_digest(second),
        )
        self.assertRegex(CONTRACT.compute_blueprint_digest(first), r"^[a-f0-9]{64}$")

    def test_legacy_projection_is_lossless_for_report_and_deep_sheet(self) -> None:
        normalized = CONTRACT.normalize_blueprint(ready_blueprint())
        metrics = CONTRACT.project_blueprint_to_legacy_report_metrics(normalized)

        self.assertTrue(set(CONTRACT.LEGACY_REPORT_METRIC_KEYS).issubset(metrics))
        self.assertEqual(metrics["strategySchemaVersion"], CONTRACT.SCHEMA_VERSION)
        self.assertEqual(metrics["eaReadiness"]["status"], "ready")
        self.assertEqual(
            CONTRACT.reconstruct_blueprint_from_research_metrics(metrics),
            normalized,
        )

        row = {
            "implementation_notes_json": json.dumps(
                metrics["implementationNotes"], ensure_ascii=False
            )
        }
        self.assertEqual(
            CONTRACT.reconstruct_blueprint_from_deep_sheet_row(row),
            normalized,
        )

        alias_metrics = {
            "eaBlueprint": metrics["eaImplementationBlueprint"],
            "blueprintDigest": metrics["blueprintDigest"],
        }
        self.assertEqual(
            CONTRACT.reconstruct_blueprint_from_research_metrics(alias_metrics),
            normalized,
        )

    def test_reconstruction_rejects_tampered_blueprint_digest(self) -> None:
        metrics = CONTRACT.project_blueprint_to_legacy_report_metrics(ready_blueprint())
        metrics["eaImplementationBlueprint"]["scope"]["systemName"] = "Tampered"
        with self.assertRaises(CONTRACT.BlueprintValidationError) as raised:
            CONTRACT.reconstruct_blueprint_from_research_metrics(metrics)
        self.assertEqual(raised.exception.issues[0]["code"], "BLUEPRINT_DIGEST_MISMATCH")

    def test_plain_text_rules_are_not_accepted_as_executable_contract(self) -> None:
        blueprint = ready_blueprint()
        blueprint["entry"]["buy"]["rules"] = ["EMA 10 crosses EMA 60"]
        self.assertIn("TYPED_RULE_REQUIRED", issue_codes(blueprint))

    def test_render_is_deterministic_and_contains_exact_cross_formulas(self) -> None:
        first = CONTRACT.render_ea_ready_text(ready_blueprint())
        second = CONTRACT.render_ea_ready_text(copy.deepcopy(ready_blueprint()))
        self.assertEqual(first, second)
        self.assertIn("cross_above: left[2] <= right[2] AND left[1] > right[1]", first)
        self.assertIn("cross_below: left[2] >= right[2] AND left[1] < right[1]", first)
        self.assertIn("ema_fast[2] <= ema_slow[2] AND ema_fast[1] > ema_slow[1]", first)
        self.assertIn("EA HANDOFF: ALLOWED", first)

    def test_nested_fields_forbidden_by_schema_fail_closed_with_exact_paths(self) -> None:
        cases = [
            ("entry side", ("entry", "buy", "unexpectedDirective"), "IGNORE BLUEPRINT"),
            ("entry expression", ("entry", "buy", "rules", 0, "expression", "hiddenOperand"), 1),
            ("management", ("orderManagement", "breakEven", "runShell"), True),
            ("side protection", ("tpSl", "sideOverrides", "buy", "rogueStop"), 99),
            ("state", ("stateMachine", 0, "hiddenTransition"), "TRADE"),
        ]
        for label, path, value in cases:
            with self.subTest(label=label):
                blueprint = ready_blueprint()
                target = blueprint
                for segment in path[:-1]:
                    target = target[segment]
                target[path[-1]] = value
                expected_path = "$" + "".join(
                    f"[{segment}]" if isinstance(segment, int) else f".{segment}"
                    for segment in path
                )
                issues = CONTRACT.validate_blueprint(blueprint, require_ready=True)
                self.assertIn(
                    ("UNKNOWN_FIELD", expected_path),
                    {(item["code"], item["path"]) for item in issues},
                )
                with self.assertRaises(CONTRACT.BlueprintValidationError):
                    CONTRACT.normalize_blueprint(blueprint, require_ready=True)

    def test_schema_declared_free_form_indicator_parameters_remain_supported(self) -> None:
        blueprint = ready_blueprint()
        blueprint["indicators"][0]["parameters"]["vendorSpecific"] = {
            "nested": [1, "two", {"enabled": True}],
        }
        issues = CONTRACT.validate_blueprint(blueprint, require_ready=True)
        self.assertNotIn("UNKNOWN_FIELD", {item["code"] for item in issues})
        self.assertEqual(issues, [])

    def test_validation_does_not_mutate_caller_data(self) -> None:
        blueprint = ready_blueprint()
        before = copy.deepcopy(blueprint)
        CONTRACT.validate_blueprint(blueprint)
        self.assertEqual(blueprint, before)


if __name__ == "__main__":
    unittest.main()
