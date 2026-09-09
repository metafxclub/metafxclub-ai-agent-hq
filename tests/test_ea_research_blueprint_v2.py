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
        "evaluationEvent": "new_closed_bar",
        "sourceStatus": source_status,
        "sourceRefs": ["S1"],
        "expression": {
            "op": op,
            "left": source_operand("ema_fast"),
            "right": source_operand("ema_slow"),
            "previousShift": 2,
            "currentShift": 1,
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


def once_per_bar_with_position() -> dict:
    return {
        "op": "once_per_bar",
        "barShift": 1,
        "item": {
            "op": ">",
            "left": {"kind": "position", "field": "managed_count"},
            "right": {"kind": "constant", "value": 0},
        },
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
            "evaluationOrder": ["safety", "exit", "manage", "entry"],
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
                "url": "https://www.investopedia.com/terms/m/movingaverage.asp",
                "title": "EMA crossover specification",
                "checkedAt": "2026-09-08T09:30:00+07:00",
            },
            {
                "sourceRef": "S2",
                "url": "https://www.tradingview.com/support/solutions/43000592270-moving-average/",
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
                "evaluationEvent": "once_per_level",
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
    blueprint["execution"]["evaluationOrder"] = [
        "safety",
        "exit",
        "manage",
        "recovery",
        "entry",
    ]
    blueprint["precedence"].insert(3, "recovery_phase")
    long_state = next(
        state for state in blueprint["stateMachine"] if state["state"] == "LONG"
    )
    long_state["transitions"].append(
        {"to": "RECOVERY", "whenRuleIds": ["RECOVERY_LEVEL_001"]}
    )
    blueprint["stateMachine"].append(
        {
            "state": "RECOVERY",
            "transitions": [
                {"to": "LONG", "whenRuleIds": ["RECOVERY_LEVEL_001"]},
            ],
        }
    )
    blueprint["pseudocode"]["lines"].append(
        "When RECOVERY_LEVEL_001 is true in LONG, enter RECOVERY, add one capped level, then return to LONG after the rule-bound lifecycle step."
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
        self.assertTrue(
            {"side", "evaluationEvent", "humanTextTh"}.issubset(
                schema["$defs"]["rule"]["required"]
            )
        )
        self.assertIn("EMA", schema["$defs"]["indicator"]["properties"]["kind"]["enum"])
        self.assertNotIn(
            "QuantumMoonFilter",
            schema["$defs"]["indicator"]["properties"]["kind"]["enum"],
        )
        self.assertNotIn(
            "RSI",
            schema["$defs"]["indicator"]["properties"]["kind"]["enum"],
        )
        self.assertTrue(
            any(
                {"barShift", "item"}.issubset(fragment.get("then", {}).get("required", []))
                for fragment in schema["$defs"]["expression"]["allOf"]
            )
        )
        self.assertTrue(
            any(
                "field" in fragment.get("then", {}).get("required", [])
                for fragment in schema["$defs"]["operand"]["allOf"]
            )
        )

    def test_executable_rules_require_side_event_human_text_and_container_alignment(self) -> None:
        missing = ready_blueprint()
        rule = missing["entry"]["buy"]["rules"][0]
        rule.pop("side")
        rule.pop("evaluationEvent")
        rule.pop("humanTextTh")
        codes = issue_codes(missing)
        self.assertIn("RULE_SIDE_REQUIRED", codes)
        self.assertIn("RULE_EVALUATION_EVENT_REQUIRED", codes)
        self.assertIn("STRING_REQUIRED", codes)

        mismatched = ready_blueprint()
        mismatched_rule = mismatched["entry"]["buy"]["rules"][0]
        mismatched_rule.update(
            phase="exit",
            side="sell",
            evaluationEvent="every_tick",
        )
        mismatch_codes = issue_codes(mismatched)
        self.assertIn("RULE_CONTAINER_PHASE_MISMATCH", mismatch_codes)
        self.assertIn("RULE_CONTAINER_SIDE_MISMATCH", mismatch_codes)
        self.assertIn("CLOSED_BAR_EVALUATION_EVENT_INVALID", mismatch_codes)

        for lifecycle in ("entry", "exit"):
            with self.subTest(lifecycle=lifecycle, side="both"):
                shared_label = ready_blueprint()
                shared_label[lifecycle]["buy"]["rules"][0]["side"] = "both"
                normalized, shared_issues = (
                    CONTRACT.normalize_and_validate_blueprint(shared_label)
                )
                self.assertEqual(
                    normalized[lifecycle]["buy"]["rules"][0]["side"],
                    "both",
                )
                self.assertIn(
                    "RULE_CONTAINER_SIDE_MISMATCH",
                    {item["code"] for item in shared_issues},
                )

        setup_both = ready_blueprint()
        setup_rule = copy.deepcopy(setup_both["entry"]["buy"]["rules"][0])
        setup_rule.update(ruleId="SETUP_BOTH_001", phase="setup", side="both")
        setup_both["setup"]["rules"] = [setup_rule]
        setup_codes = issue_codes(setup_both)
        self.assertNotIn("SETUP_RULE_SIDE_INVALID", setup_codes)
        self.assertNotIn("RULE_CONTAINER_SIDE_MISMATCH", setup_codes)

    def test_parameterized_indicator_requires_bound_settings_and_timeframe(self) -> None:
        blueprint = ready_blueprint()
        blueprint["indicators"][0]["parameters"] = {}
        self.assertIn("INDICATOR_PERIOD_REQUIRED", issue_codes(blueprint))
        self.assertIn("READINESS_UNRESOLVED", issue_codes(blueprint))

        unbound_timeframe = ready_blueprint()
        unbound_timeframe["indicators"][0]["timeframe"] = "M15"
        self.assertIn(
            "INDICATOR_TIMEFRAME_UNBOUND",
            issue_codes(unbound_timeframe),
        )

    def test_moving_average_contract_rejects_nonsensical_code_parameters(self) -> None:
        cases = [
            (
                "zero period",
                lambda value: value["indicators"][0]["parameters"].update(period=0),
                "INDICATOR_PERIOD_INVALID",
            ),
            (
                "fractional period",
                lambda value: value["indicators"][0]["parameters"].update(period=10.5),
                "INDICATOR_PERIOD_INVALID",
            ),
            (
                "wrong input type",
                lambda value: value["indicators"][0]["parameters"].update(
                    period={"inputRef": "fixed_lot"}
                ),
                "INDICATOR_PERIOD_INPUT_TYPE_INVALID",
            ),
            (
                "invalid applied price",
                lambda value: value["indicators"][0].update(appliedPrice="banana"),
                "INDICATOR_APPLIED_PRICE_INVALID",
            ),
            (
                "invalid output line",
                lambda value: value["indicators"][0].update(outputLine="signal_7"),
                "INDICATOR_OUTPUT_LINE_INVALID",
            ),
            (
                "negative display shift",
                lambda value: value["indicators"][0]["parameters"].update(shift=-1),
                "INDICATOR_MA_SHIFT_INVALID",
            ),
        ]
        for label, mutate, expected_code in cases:
            with self.subTest(label=label):
                blueprint = ready_blueprint()
                mutate(blueprint)
                self.assertIn(expected_code, issue_codes(blueprint))

        generic = ready_blueprint()
        generic["indicators"][0]["kind"] = "MA"
        self.assertIn("INDICATOR_MA_METHOD_INVALID", issue_codes(generic))
        generic["indicators"][0]["parameters"]["method"] = "EMA"
        self.assertEqual(CONTRACT.validate_blueprint(generic), [])

        unknown_generic = ready_blueprint()
        unknown_generic["indicators"][0].update(
            kind="MA",
            sourceStatus="unknown",
            sourceRefs=[],
        )
        unknown_generic["indicators"][0]["parameters"]["method"] = "unknown"
        unknown_codes = issue_codes(unknown_generic)
        self.assertNotIn("INDICATOR_MA_METHOD_INVALID", unknown_codes)
        self.assertIn("READINESS_UNRESOLVED", unknown_codes)

        aliased_unknown_generic = ready_blueprint()
        aliased_unknown_generic["indicators"][0].update(
            kind="MA",
            sourceStatus="unknown",
            sourceRefs=[],
        )
        aliased_unknown_generic["indicators"][0]["parameters"] = {
            "periodInputRef": "fast_period",
            "method": "unknown_generic_moving_average",
            "shift": 0,
        }
        normalized, aliased_issues = CONTRACT.normalize_and_validate_blueprint(
            aliased_unknown_generic
        )
        aliased_codes = {item["code"] for item in aliased_issues}
        self.assertEqual(
            normalized["indicators"][0]["parameters"]["period"],
            {"inputRef": "fast_period"},
        )
        self.assertNotIn(
            "periodInputRef", normalized["indicators"][0]["parameters"]
        )
        self.assertEqual(
            normalized["indicators"][0]["parameters"]["method"], "unknown"
        )
        self.assertNotIn("INDICATOR_PERIOD_REQUIRED", aliased_codes)
        self.assertNotIn("INDICATOR_MA_METHOD_INVALID", aliased_codes)
        self.assertIn("READINESS_UNRESOLVED", aliased_codes)

        same_period_alias = ready_blueprint()
        same_period_alias["indicators"][0]["parameters"]["periodInputRef"] = (
            " fast_period "
        )
        normalized_same, same_issues = CONTRACT.normalize_and_validate_blueprint(
            same_period_alias
        )
        self.assertEqual(
            normalized_same["indicators"][0]["parameters"]["period"],
            {"inputRef": "fast_period"},
        )
        self.assertNotIn(
            "periodInputRef",
            normalized_same["indicators"][0]["parameters"],
        )
        self.assertNotIn(
            "INDICATOR_PERIOD_ALIAS_CONFLICT",
            {item["code"] for item in same_issues},
        )

        conflicting_period_alias = ready_blueprint()
        conflicting_period_alias["indicators"][0]["parameters"][
            "periodInputRef"
        ] = "slow_period"
        normalized_conflict, conflict_issues = (
            CONTRACT.normalize_and_validate_blueprint(conflicting_period_alias)
        )
        self.assertEqual(
            normalized_conflict["indicators"][0]["parameters"]["period"],
            {"inputRef": "fast_period"},
        )
        self.assertEqual(
            normalized_conflict["indicators"][0]["parameters"]["periodInputRef"],
            "slow_period",
        )
        self.assertIn(
            "INDICATOR_PERIOD_ALIAS_CONFLICT",
            {item["code"] for item in conflict_issues},
        )

        verified_record_with_unknown_method = ready_blueprint()
        verified_record_with_unknown_method["indicators"][0]["kind"] = "MA"
        verified_record_with_unknown_method["indicators"][0]["parameters"][
            "method"
        ] = "unknown"
        original_source_refs = copy.deepcopy(
            verified_record_with_unknown_method["indicators"][0]["sourceRefs"]
        )
        normalized_unknown, unknown_method_issues = (
            CONTRACT.normalize_and_validate_blueprint(
                verified_record_with_unknown_method
            )
        )
        unknown_method_codes = {item["code"] for item in unknown_method_issues}
        self.assertEqual(
            normalized_unknown["indicators"][0]["sourceStatus"], "unknown"
        )
        self.assertEqual(
            normalized_unknown["indicators"][0]["sourceRefs"],
            original_source_refs,
        )
        self.assertNotIn("INDICATOR_MA_METHOD_INVALID", unknown_method_codes)
        self.assertIn("READINESS_UNRESOLVED", unknown_method_codes)

    def test_reserved_documentation_domains_never_count_as_blueprint_evidence(self) -> None:
        for url in (
            "https://example.com/ema-cross",
            "https://docs.example.org/rules",
            "https://research.vendor.test/rules",
            "https://system.invalid/rules",
        ):
            with self.subTest(url=url):
                blueprint = ready_blueprint()
                blueprint["evidenceMap"][0]["url"] = url
                self.assertIn(
                    "SOURCE_URL_RESERVED_DOCUMENTATION_DOMAIN",
                    issue_codes(blueprint),
                )

    def test_account_operand_requires_explicit_field(self) -> None:
        blueprint = ready_blueprint()
        blueprint["entry"]["buy"]["rules"][0]["expression"] = {
            "op": ">=",
            "left": {"kind": "account"},
            "right": {"kind": "constant", "value": 10.0},
        }
        issues = CONTRACT.validate_blueprint(blueprint, require_ready=True)
        self.assertIn(
            ("ACCOUNT_FIELD_REQUIRED", "$.entry.buy.rules[0].expression.left.field"),
            {(item["code"], item["path"]) for item in issues},
        )

    def test_all_semantic_operands_require_explicit_fields(self) -> None:
        for kind in (
            "position",
            "basket",
            "session",
            "spread",
            "time",
            "symbol_property",
        ):
            with self.subTest(kind=kind):
                blueprint = ready_blueprint()
                blueprint["entry"]["buy"]["rules"][0]["expression"] = {
                    "op": ">",
                    "left": {"kind": kind},
                    "right": {"kind": "constant", "value": 0},
                }
                issues = CONTRACT.validate_blueprint(blueprint, require_ready=True)
                self.assertIn(
                    (
                        "OPERAND_FIELD_REQUIRED",
                        "$.entry.buy.rules[0].expression.left.field",
                    ),
                    {(item["code"], item["path"]) for item in issues},
                )

    def test_once_per_bar_requires_and_validates_nested_condition(self) -> None:
        missing = ready_blueprint()
        missing["entry"]["buy"]["rules"][0]["expression"] = {
            "op": "once_per_bar",
            "barShift": 1,
        }
        missing_issues = CONTRACT.validate_blueprint(missing, require_ready=True)
        self.assertIn(
            (
                "ONCE_PER_BAR_ITEM_REQUIRED",
                "$.entry.buy.rules[0].expression.item",
            ),
            {(item["code"], item["path"]) for item in missing_issues},
        )

        malformed = ready_blueprint()
        malformed["entry"]["buy"]["rules"][0]["expression"] = {
            "op": "once_per_bar",
            "barShift": 1,
            "item": {"left": {"kind": "constant", "value": 1}},
        }
        malformed_issues = CONTRACT.validate_blueprint(
            malformed,
            require_ready=True,
        )
        self.assertIn(
            (
                "EXPRESSION_OPERATOR_INVALID",
                "$.entry.buy.rules[0].expression.item.op",
            ),
            {(item["code"], item["path"]) for item in malformed_issues},
        )

    def test_research_timeframe_and_signal_age_operands_are_explicitly_supported(self) -> None:
        blueprint = ready_blueprint()
        blueprint["setup"]["rules"] = [
            {
                "ruleId": "SETUP_TIMEFRAME_001",
                "phase": "setup",
                "side": "both",
                "enabled": True,
                "evaluationEvent": "new_closed_bar",
                "sourceStatus": "derived",
                "sourceRefs": ["S1"],
                "expression": {
                    "op": "==",
                    "left": {"kind": "time", "field": "timeframe"},
                    "right": {"kind": "constant", "value": "D1"},
                },
                "humanTextTh": "ประเมินกฎนี้บนกรอบเวลา D1",
            }
        ]
        blueprint["entry"]["buy"]["rules"].append(
            {
                "ruleId": "ENTRY_BUY_RULE_C",
                "phase": "entry",
                "side": "buy",
                "enabled": True,
                "evaluationEvent": "new_closed_bar",
                "sourceStatus": "derived",
                "sourceRefs": ["S1"],
                "expression": {
                    "op": ">=",
                    "left": {
                        "kind": "position",
                        "field": "bars_since_initial_action_signal",
                    },
                    "right": {"kind": "constant", "value": 20},
                },
                "humanTextTh": "ครบ 20 แท่งหลังสัญญาณตั้งต้น",
            }
        )
        normalized, issues = CONTRACT.normalize_and_validate_blueprint(blueprint)
        codes = {item["code"] for item in issues}
        self.assertNotIn("OPERAND_FIELD_INVALID", codes)
        self.assertEqual(
            normalized["entry"]["buy"]["rules"][1]["expression"]["left"]["field"],
            "bars_since_initial_action_signal",
        )

        aliased = ready_blueprint()
        aliased["entry"]["buy"]["rules"][0]["expression"] = {
            "op": ">=",
            "left": {
                "kind": "position",
                "field": "bars_since_action_signal",
            },
            "right": {"kind": "constant", "value": 20},
        }
        aliased_normalized, aliased_issues = (
            CONTRACT.normalize_and_validate_blueprint(aliased)
        )
        self.assertNotIn(
            "OPERAND_FIELD_INVALID", {item["code"] for item in aliased_issues}
        )
        self.assertEqual(
            aliased_normalized["entry"]["buy"]["rules"][0]["expression"]["left"]["field"],
            "bars_since_initial_action_signal",
        )

    def test_daily_close_session_name_alias_fails_closed(self) -> None:
        blueprint = ready_blueprint()
        blueprint["setup"]["rules"] = [
            {
                "ruleId": "SET_DAILY_CLOSE",
                "phase": "setup",
                "side": "both",
                "enabled": True,
                "evaluationEvent": "new_closed_bar",
                "sourceStatus": "verified_fact",
                "sourceRefs": ["S1"],
                "expression": {
                    "op": "==",
                    "left": {
                        "kind": "session",
                        "ref": "session_type",
                        "field": "name",
                        "timeframe": "D1",
                    },
                    "right": {"kind": "constant", "value": "daily close"},
                    "barShift": 1,
                },
                "humanTextTh": "ประเมินเมื่อแท่ง D1 ปิดแล้ว",
            }
        ]

        normalized, issues = CONTRACT.normalize_and_validate_blueprint(blueprint)

        self.assertIn("OPERAND_FIELD_INVALID", {item["code"] for item in issues})
        self.assertEqual(
            normalized["setup"]["rules"][0]["expression"]["left"]["field"],
            "name",
        )

    def test_unknown_indicator_kind_and_unmapped_buffers_fail_closed(self) -> None:
        unknown = ready_blueprint()
        unknown["indicators"][0].update(
            kind="QuantumMoonFilter",
            parameters={"bogus": 123},
            appliedPrice="bananas",
            outputLine="not-a-buffer",
        )
        self.assertIn("INDICATOR_KIND_UNSUPPORTED", issue_codes(unknown))

        unsupported_builtin = ready_blueprint()
        unsupported_builtin["indicators"][0].update(
            kind="RSI",
            parameters={"period": 14},
        )
        self.assertIn(
            "INDICATOR_KIND_UNSUPPORTED",
            issue_codes(unsupported_builtin),
        )

        atr_without_period = ready_blueprint()
        atr_without_period["indicators"][0].update(
            kind="ATR",
            parameters={"bogus": 123},
        )
        self.assertIn("INDICATOR_PERIOD_REQUIRED", issue_codes(atr_without_period))

        wrong_line = ready_blueprint()
        wrong_line["indicators"][0].update(outputLine="signal")
        self.assertIn("INDICATOR_OUTPUT_LINE_INVALID", issue_codes(wrong_line))

    def test_entry_and_exit_parent_enablement_cannot_hide_child_rules(self) -> None:
        for section in ("entry", "exit"):
            with self.subTest(section=section):
                blueprint = ready_blueprint()
                child = copy.deepcopy(blueprint[section]["buy"]["rules"][0])
                child["ruleId"] = f"HIDDEN_{section.upper()}_SELL"
                child["side"] = "sell"
                blueprint[section]["sell"]["rules"] = [child]
                codes = issue_codes(blueprint)
                self.assertIn("DISABLED_SIDE_RULES_NOT_EMPTY", codes)
                self.assertIn("CHILD_RULE_ENABLEMENT_MISMATCH", codes)

        mismatched_exit = ready_blueprint()
        mismatched_exit["exit"]["buy"].update(
            enabled=False,
            disabledReason="Exit intentionally disabled",
            rules=[],
        )
        self.assertIn("SIDE_ENABLEMENT_MISMATCH", issue_codes(mismatched_exit))

    def test_enabled_exit_can_use_protection_without_signal_rules(self) -> None:
        blueprint = ready_blueprint()
        blueprint["exit"]["buy"]["rules"] = []
        for input_row in blueprint["inputs"]:
            input_row["usedByRuleIds"] = [
                rule_id
                for rule_id in input_row["usedByRuleIds"]
                if rule_id != "EXIT_BUY_001"
            ]
        blueprint["testCases"] = [
            case
            for case in blueprint["testCases"]
            if "EXIT_BUY_001" not in case["ruleIds"]
        ]
        blueprint["pseudocode"]["lines"] = [
            line
            for line in blueprint["pseudocode"]["lines"]
            if "EXIT_BUY_001" not in line
        ]
        next(
            state for state in blueprint["stateMachine"] if state["state"] == "LONG"
        )["transitions"] = []
        self.assertEqual(CONTRACT.validate_blueprint(blueprint), [])

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
            trigger=once_per_bar_with_position(),
            action={"kind": "move_stop"},
        )
        codes = issue_codes(blueprint)
        self.assertIn("READINESS_UNRESOLVED", codes)

    def test_ready_requires_two_independent_public_evidence_domains(self) -> None:
        one_source = ready_blueprint()
        one_source["evidenceMap"] = one_source["evidenceMap"][:1]
        self.assertIn("READINESS_UNRESOLVED", issue_codes(one_source))

        same_domain = ready_blueprint()
        same_domain["evidenceMap"][1]["url"] = "https://academy.investopedia.com/another-page"
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
            trigger=once_per_bar_with_position(),
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
            "evaluationEvent": "new_closed_bar",
            "sourceStatus": "verified_fact",
            "sourceRefs": ["S1"],
            "expression": once_per_bar_with_position(),
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

    def test_risk_limits_reject_unsafe_ranges_and_inverted_lot_caps(self) -> None:
        mutations = (
            ("maxTotalLots", -2, "RISK_LOT_CAP_INVALID"),
            ("maxRiskPerTradePercent", 500, "RISK_PERCENT_INVALID"),
            ("dailyLossStopPercent", -10, "RISK_PERCENT_INVALID"),
            ("weeklyLossStopPercent", 101, "RISK_PERCENT_INVALID"),
            ("equityStopPercent", 250, "RISK_PERCENT_INVALID"),
            ("consecutiveLossLimit", -1, "RISK_LIMIT_INVALID"),
            ("cooldownBars", -1, "RISK_LIMIT_INVALID"),
        )
        for field, value, expected_code in mutations:
            with self.subTest(field=field, value=value):
                blueprint = ready_blueprint()
                blueprint["riskAndSizing"][field] = value
                self.assertIn(expected_code, issue_codes(blueprint))

        smaller_than_fixed_lot = ready_blueprint()
        smaller_than_fixed_lot["riskAndSizing"]["maxTotalLots"] = 0.05
        self.assertIn(
            "RISK_LOT_CAP_ORDER_INVALID",
            issue_codes(smaller_than_fixed_lot),
        )

        invalid_boolean = ready_blueprint()
        invalid_boolean["riskAndSizing"]["normalizeToBrokerLotStep"] = "yes"
        self.assertIn("BOOLEAN_REQUIRED", issue_codes(invalid_boolean))

    def test_precedence_and_execution_order_are_safety_first(self) -> None:
        explicit_prefixes = ready_blueprint()
        explicit_prefixes["precedence"] = [
            "safety: enforce account hard stops",
            "exit: evaluate normal close rules",
            "manage: update managed positions",
            "entry: evaluate entry rules",
        ]
        explicit_codes = issue_codes(explicit_prefixes)
        self.assertNotIn("PRECEDENCE_PHASE_MISSING", explicit_codes)
        self.assertNotIn("PRECEDENCE_ORDER_UNSAFE", explicit_codes)

        explanatory_cross_references = ready_blueprint()
        explanatory_cross_references["precedence"] = [
            "safety: reject unsafe orders before any later phase",
            "exit: evaluate close rules before entry",
            "manage: manage open positions without worsening stops",
            "entry: evaluate entry only after exit and management",
        ]
        explanatory_codes = issue_codes(explanatory_cross_references)
        self.assertNotIn("PRECEDENCE_STEP_INVALID", explanatory_codes)
        self.assertNotIn("PRECEDENCE_PHASE_MISSING", explanatory_codes)
        self.assertNotIn("PRECEDENCE_ORDER_UNSAFE", explanatory_codes)

        precedence = ready_blueprint()
        precedence["precedence"] = [
            "emergency_stop",
            "position_management",
            "normal_exit",
            "new_entry",
        ]
        self.assertIn("PRECEDENCE_ORDER_UNSAFE", issue_codes(precedence))

        missing_management = ready_blueprint()
        missing_management["precedence"] = [
            "emergency_stop",
            "normal_exit",
            "new_entry",
        ]
        self.assertIn("PRECEDENCE_PHASE_MISSING", issue_codes(missing_management))

        execution = ready_blueprint()
        execution["execution"]["evaluationOrder"] = [
            "safety",
            "manage",
            "exit",
            "entry",
        ]
        self.assertIn("EXECUTION_ORDER_UNSAFE", issue_codes(execution))

        disabled_recovery = ready_blueprint()
        disabled_recovery["execution"]["evaluationOrder"].insert(3, "recovery")
        disabled_recovery["precedence"].insert(3, "recovery_phase")
        disabled_recovery_codes = issue_codes(disabled_recovery)
        self.assertIn(
            "EXECUTION_ORDER_PHASE_UNEXPECTED", disabled_recovery_codes
        )
        self.assertIn("PRECEDENCE_PHASE_UNEXPECTED", disabled_recovery_codes)

        mixed_phase = ready_blueprint()
        mixed_phase["precedence"][0] = "safety and entry are processed together"
        self.assertIn("PRECEDENCE_STEP_INVALID", issue_codes(mixed_phase))

        semantic_duplicate = ready_blueprint()
        semantic_duplicate["precedence"].insert(1, "hard_stop")
        self.assertIn(
            "PRECEDENCE_PHASE_DUPLICATE", issue_codes(semantic_duplicate)
        )

        valid_recovery = activate_martingale_recovery(ready_blueprint())
        valid_recovery_codes = issue_codes(valid_recovery)
        self.assertNotIn("EXECUTION_ORDER_UNSAFE", valid_recovery_codes)
        self.assertNotIn("PRECEDENCE_ORDER_UNSAFE", valid_recovery_codes)
        self.assertNotIn("EXECUTION_ORDER_PHASE_UNEXPECTED", valid_recovery_codes)
        self.assertNotIn("PRECEDENCE_PHASE_UNEXPECTED", valid_recovery_codes)

        recovery = activate_martingale_recovery(ready_blueprint())
        recovery["execution"]["evaluationOrder"].remove("recovery")
        recovery["precedence"].remove("recovery_phase")
        codes = issue_codes(recovery)
        self.assertIn("EXECUTION_ORDER_PHASE_MISSING", codes)
        self.assertIn("PRECEDENCE_PHASE_MISSING", codes)

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
            {
                "state": "PENDING",
                "transitions": [
                    {"to": "LONG", "whenRuleIds": ["PENDING_PLACE_001"]}
                ],
            }
        )
        complete["testCases"].extend(
            [
                {
                    "caseId": "pending-place-boundary",
                    "kind": "boundary",
                    "ruleIds": ["PENDING_PLACE_001"],
                    "given": {"fast2": 1.0, "slow2": 1.0, "fast1": 1.0, "slow1": 1.0},
                    "when": "new closed bar",
                    "expected": {"signal": "none", "pendingOrder": "none"},
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

    def test_state_transitions_and_active_recovery_are_rule_bound(self) -> None:
        empty_transition = ready_blueprint()
        empty_transition["stateMachine"][0]["transitions"][0]["whenRuleIds"] = []
        self.assertIn("ARRAY_TOO_SHORT", issue_codes(empty_transition))

        missing_recovery_state = activate_martingale_recovery(ready_blueprint())
        missing_recovery_state["stateMachine"] = [
            state
            for state in missing_recovery_state["stateMachine"]
            if state["state"] != "RECOVERY"
        ]
        self.assertIn("READINESS_UNRESOLVED", issue_codes(missing_recovery_state))

        unbound_recovery = activate_martingale_recovery(ready_blueprint())
        long_state = next(
            state for state in unbound_recovery["stateMachine"] if state["state"] == "LONG"
        )
        long_state["transitions"] = [
            transition
            for transition in long_state["transitions"]
            if transition["to"] != "RECOVERY"
        ]
        self.assertIn("READINESS_UNRESOLVED", issue_codes(unbound_recovery))

        missing_recovery_pseudocode = activate_martingale_recovery(ready_blueprint())
        missing_recovery_pseudocode["pseudocode"]["lines"] = [
            line
            for line in missing_recovery_pseudocode["pseudocode"]["lines"]
            if "RECOVERY_LEVEL_001" not in line
        ]
        self.assertIn("READINESS_UNRESOLVED", issue_codes(missing_recovery_pseudocode))

    def test_cross_test_cases_are_semantic_oracles_not_labels_only(self) -> None:
        previous_equality_then_strict_cross = ready_blueprint()
        boundary_true = next(
            case
            for case in previous_equality_then_strict_cross["testCases"]
            if case["caseId"] == "entry-buy-boundary"
        )
        boundary_true["given"] = {
            "fast2": 1.0,
            "slow2": 1.0,
            "fast1": 1.1,
            "slow1": 1.0,
        }
        boundary_true["expected"] = {"signal": "buy"}
        boundary_true_codes = issue_codes(previous_equality_then_strict_cross)
        self.assertNotIn("TEST_CROSS_FIXTURE_MISMATCH", boundary_true_codes)
        self.assertNotIn("TEST_CROSS_EXPECTED_INVALID", boundary_true_codes)

        current_equality_no_cross = ready_blueprint()
        boundary_false = next(
            case
            for case in current_equality_no_cross["testCases"]
            if case["caseId"] == "entry-buy-boundary"
        )
        boundary_false["given"] = {
            "fast2": 0.9,
            "slow2": 1.0,
            "fast1": 1.0,
            "slow1": 1.0,
        }
        boundary_false["expected"] = {"signal": "none"}
        boundary_false_codes = issue_codes(current_equality_no_cross)
        self.assertNotIn("TEST_CROSS_FIXTURE_MISMATCH", boundary_false_codes)
        self.assertNotIn("TEST_CROSS_EXPECTED_INVALID", boundary_false_codes)

        missing_boundary_signal = ready_blueprint()
        next(
            case
            for case in missing_boundary_signal["testCases"]
            if case["caseId"] == "entry-buy-boundary"
        )["expected"] = {"result": "boundary"}
        self.assertIn(
            "TEST_CROSS_EXPECTED_INVALID",
            issue_codes(missing_boundary_signal),
        )

        inverted_expected = ready_blueprint()
        inverted_expected["testCases"][0]["expected"] = {"signal": "none"}
        inverted_expected["testCases"][1]["expected"] = {"signal": "buy"}
        self.assertIn(
            "TEST_CROSS_EXPECTED_INVALID",
            issue_codes(inverted_expected),
        )

        false_positive_fixture = ready_blueprint()
        false_positive_fixture["testCases"][0]["given"] = {
            "fast2": 1.1,
            "slow2": 1.0,
            "fast1": 1.2,
            "slow1": 1.0,
        }
        self.assertIn(
            "TEST_CROSS_FIXTURE_MISMATCH",
            issue_codes(false_positive_fixture),
        )

        prose_only_fixture = ready_blueprint()
        prose_only_fixture["testCases"][0]["given"] = {
            "description": "fast EMA crosses slow EMA"
        }
        self.assertIn(
            "TEST_CROSS_FIXTURE_UNRESOLVED",
            issue_codes(prose_only_fixture),
        )

    def test_unknowns_and_conflicts_require_complete_traceable_records(self) -> None:
        malformed_unknown = ready_blueprint()
        malformed_unknown["unknowns"] = [{}]
        self.assertIn("FIELD_REQUIRED", issue_codes(malformed_unknown))

        nonblocking_unknown = ready_blueprint()
        nonblocking_unknown["unknowns"] = [
            {
                "unknownId": "U1",
                "path": "$.scope.suitableFor",
                "description": "Marketing suitability is not execution-critical",
                "blocksExecution": False,
            }
        ]
        self.assertEqual(CONTRACT.validate_blueprint(nonblocking_unknown), [])

        malformed_conflict = ready_blueprint()
        malformed_conflict["conflicts"] = [
            {"resolutionStatus": "resolved", "sourceRefs": []}
        ]
        self.assertIn("FIELD_REQUIRED", issue_codes(malformed_conflict))

        resolved_conflict = ready_blueprint()
        resolved_conflict["conflicts"] = [
            {
                "conflictId": "C1",
                "paths": ["$.scope.signalTimeframe"],
                "description": "Sources disagreed on the example timeframe",
                "resolutionStatus": "resolved",
                "resolution": "Use H1 because the primary specification names H1",
                "sourceRefs": ["S1", "S2"],
            }
        ]
        self.assertEqual(CONTRACT.validate_blueprint(resolved_conflict), [])

    def test_operands_use_a_deterministic_field_registry(self) -> None:
        for kind in ("account", "position", "basket", "session", "spread", "time", "symbol_property"):
            with self.subTest(kind=kind):
                blueprint = ready_blueprint()
                blueprint["entry"]["buy"]["rules"][0]["expression"] = {
                    "op": ">",
                    "left": {"kind": kind, "field": "banana_metric"},
                    "right": {"kind": "constant", "value": 0},
                }
                self.assertIn("OPERAND_FIELD_INVALID", issue_codes(blueprint))

    def test_management_parameters_must_match_the_typed_action(self) -> None:
        blueprint = ready_blueprint()
        rule = {
            "ruleId": "MODIFY_SL_001",
            "phase": "modify",
            "side": "buy",
            "enabled": True,
            "evaluationEvent": "new_closed_bar",
            "sourceStatus": "verified_fact",
            "sourceRefs": ["S1"],
            "expression": once_per_bar_with_position(),
            "humanTextTh": "เลื่อน Stop Loss ตามเป้าหมายที่กำหนด",
        }
        feature = blueprint["orderManagement"]["modifyStopLoss"]
        feature.update(
            enabled=True,
            trigger=copy.deepcopy(rule["expression"]),
            action={"kind": "move_stop_loss"},
            parameters={"garbage": "not executable"},
            rules=[rule],
            cadence="new_closed_bar",
            idempotent=True,
            precedence=40,
            neverWorsenStop=True,
        )
        blueprint["testCases"].append(
            {
                "caseId": "modify-sl-semantic-lifecycle",
                "kind": "lifecycle",
                "ruleIds": ["MODIFY_SL_001"],
                "given": {"position": "long"},
                "when": "a new closed bar is processed",
                "expected": {"stop": "unchanged"},
            }
        )
        blueprint["pseudocode"]["lines"].append(
            "When MODIFY_SL_001 is true, evaluate the typed stop target."
        )
        codes = issue_codes(blueprint)
        self.assertIn("MANAGEMENT_PARAMETER_UNKNOWN", codes)
        self.assertIn("READINESS_UNRESOLVED", codes)

        feature["parameters"] = {"target": "entry_price", "bufferPoints": -1}
        codes = issue_codes(blueprint)
        self.assertNotIn("MANAGEMENT_PARAMETER_UNKNOWN", codes)
        self.assertIn("MANAGEMENT_VALUE_INVALID", codes)

        feature["parameters"] = {
            "targetPrice": "entry_price",
            "target_price": "entry_price",
        }
        collision_codes = issue_codes(blueprint)
        self.assertIn(
            "MANAGEMENT_PARAMETER_ALIAS_CONFLICT",
            collision_codes,
        )

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

    def test_cross_requires_explicit_closed_bar_shift_contract(self) -> None:
        blueprint = ready_blueprint()
        expression = blueprint["entry"]["buy"]["rules"][0]["expression"]
        expression.pop("previousShift")
        expression.pop("currentShift")
        issues = CONTRACT.validate_blueprint(blueprint, require_ready=True)
        issue_pairs = {(item["code"], item["path"]) for item in issues}
        self.assertIn(
            (
                "CROSS_BAR_SEMANTICS_INVALID",
                "$.entry.buy.rules[0].expression.previousShift",
            ),
            issue_pairs,
        )
        self.assertIn(
            (
                "CROSS_BAR_SEMANTICS_INVALID",
                "$.entry.buy.rules[0].expression.currentShift",
            ),
            issue_pairs,
        )
        with self.assertRaises(CONTRACT.BlueprintValidationError):
            CONTRACT.normalize_blueprint(blueprint, require_ready=True)

    def test_break_series_operands_require_explicit_closed_bar_shift(self) -> None:
        blueprint = ready_blueprint()
        blueprint["entry"]["buy"]["rules"][0]["expression"] = {
            "op": "break_above",
            "left": {"kind": "price", "field": "close"},
            "right": {"kind": "indicator", "ref": "ema_slow"},
        }
        issues = CONTRACT.validate_blueprint(blueprint, require_ready=True)
        issue_pairs = {(item["code"], item["path"]) for item in issues}
        self.assertIn(
            (
                "CLOSED_BAR_SHIFT_REQUIRED",
                "$.entry.buy.rules[0].expression.left.shift",
            ),
            issue_pairs,
        )
        self.assertIn(
            (
                "CLOSED_BAR_SHIFT_REQUIRED",
                "$.entry.buy.rules[0].expression.right.shift",
            ),
            issue_pairs,
        )

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

    def test_expression_depth_limit_has_exact_safe_boundary(self) -> None:
        def nested_not(depth: int) -> dict:
            expression = {
                "op": ">",
                "left": {"kind": "constant", "value": 1},
                "right": {"kind": "constant", "value": 0},
            }
            for _index in range(depth - 1):
                expression = {"op": "not", "item": expression}
            return expression

        boundary = ready_blueprint()
        boundary["entry"]["buy"]["rules"][0]["expression"] = nested_not(
            CONTRACT.MAX_EXPRESSION_DEPTH
        )
        self.assertEqual(CONTRACT.validate_blueprint(boundary, require_ready=True), [])

        over_limit = ready_blueprint()
        over_limit["entry"]["buy"]["rules"][0]["expression"] = nested_not(
            CONTRACT.MAX_EXPRESSION_DEPTH + 1
        )
        issues = CONTRACT.validate_blueprint(over_limit, require_ready=True)
        self.assertIn("EXPRESSION_DEPTH_EXCEEDED", {item["code"] for item in issues})
        with self.assertRaises(CONTRACT.BlueprintValidationError) as raised:
            CONTRACT.normalize_blueprint(over_limit, require_ready=True)
        self.assertIn(
            "EXPRESSION_DEPTH_EXCEEDED",
            {item["code"] for item in raised.exception.issues},
        )

        normalized_growth = ready_blueprint()
        cross = copy.deepcopy(
            normalized_growth["entry"]["buy"]["rules"][0]["expression"]
        )
        for _index in range(CONTRACT.MAX_EXPRESSION_DEPTH - 1):
            cross = {"op": "not", "item": cross}
        normalized_growth["entry"]["buy"]["rules"][0]["expression"] = cross
        self.assertIn(
            "EXPRESSION_DEPTH_EXCEEDED",
            issue_codes(normalized_growth),
            "Auto-expanded cross nodes must be included in the frontend-safe depth budget",
        )

    def test_expression_node_limit_has_exact_safe_boundary(self) -> None:
        def wide_and(node_count: int) -> dict:
            return {
                "op": "and",
                "items": [
                    {
                        "op": ">",
                        "left": {"kind": "constant", "value": 1},
                        "right": {"kind": "constant", "value": 0},
                    }
                    for _index in range(node_count - 1)
                ],
            }

        boundary = ready_blueprint()
        boundary["entry"]["buy"]["rules"][0]["expression"] = wide_and(
            CONTRACT.MAX_EXPRESSION_NODES
        )
        self.assertEqual(CONTRACT.validate_blueprint(boundary, require_ready=True), [])

        over_limit = ready_blueprint()
        over_limit["entry"]["buy"]["rules"][0]["expression"] = wide_and(
            CONTRACT.MAX_EXPRESSION_NODES + 1
        )
        self.assertIn(
            "EXPRESSION_NODE_LIMIT_EXCEEDED",
            issue_codes(over_limit),
        )

    def test_test_case_payloads_are_nonempty_and_bounded(self) -> None:
        for key, empty_value in (("given", {}), ("when", "  "), ("expected", [])):
            with self.subTest(key=key):
                blueprint = ready_blueprint()
                blueprint["testCases"][0][key] = empty_value
                self.assertIn("TEST_PAYLOAD_EMPTY", issue_codes(blueprint))

        oversized = ready_blueprint()
        oversized["testCases"][0]["when"] = "x" * (
            CONTRACT.MAX_TEST_PAYLOAD_BYTES + 1
        )
        self.assertIn("TEST_PAYLOAD_TOO_LARGE", issue_codes(oversized))

    def test_canonical_blueprint_transport_budget_has_exact_boundary(self) -> None:
        boundary = ready_blueprint()
        boundary["pseudocode"]["lines"].append("")
        normalized_probe = CONTRACT._normalize_candidate(boundary)
        probe_size = len(CONTRACT._canonical_fragment(normalized_probe).encode("utf-8"))
        padding = CONTRACT.MAX_CANONICAL_BLUEPRINT_UTF8_BYTES - probe_size
        self.assertGreater(padding, 0)
        boundary["pseudocode"]["lines"][-1] = "X" * padding

        normalized_boundary = CONTRACT._normalize_candidate(boundary)
        boundary_json = CONTRACT._canonical_fragment(normalized_boundary)
        self.assertEqual(
            len(boundary_json.encode("utf-8")),
            CONTRACT.MAX_CANONICAL_BLUEPRINT_UTF8_BYTES,
        )
        self.assertLessEqual(
            len(boundary_json.encode("utf-16-le")) // 2,
            CONTRACT.MAX_CANONICAL_BLUEPRINT_UTF16_CODE_UNITS,
        )
        self.assertEqual(CONTRACT.validate_blueprint(boundary, require_ready=True), [])

        wrapper_json = json.dumps(
            {
                "schemaVersion": CONTRACT.SCHEMA_VERSION,
                "blueprintDigest": "0" * 64,
                "eaImplementationBlueprint": normalized_boundary,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        self.assertLessEqual(len(wrapper_json.encode("utf-16-le")) // 2, 49_000)

        over_limit = copy.deepcopy(boundary)
        over_limit["pseudocode"]["lines"][-1] += "X"
        self.assertIn("BLUEPRINT_TRANSPORT_SIZE_EXCEEDED", issue_codes(over_limit))

    def test_cross_test_outcomes_and_boundary_inputs_must_be_distinguishable(self) -> None:
        indistinguishable_outcome = ready_blueprint()
        positive = next(
            case
            for case in indistinguishable_outcome["testCases"]
            if case["kind"] == "positive" and "ENTRY_BUY_001" in case["ruleIds"]
        )
        negative = next(
            case
            for case in indistinguishable_outcome["testCases"]
            if case["kind"] == "negative" and "ENTRY_BUY_001" in case["ruleIds"]
        )
        negative["expected"] = copy.deepcopy(positive["expected"])
        self.assertIn(
            "TEST_CROSS_OUTCOMES_INDISTINGUISHABLE",
            issue_codes(indistinguishable_outcome),
        )

        fake_boundary = ready_blueprint()
        positive = next(
            case
            for case in fake_boundary["testCases"]
            if case["kind"] == "positive" and "ENTRY_BUY_001" in case["ruleIds"]
        )
        boundary = next(
            case
            for case in fake_boundary["testCases"]
            if case["kind"] == "boundary" and "ENTRY_BUY_001" in case["ruleIds"]
        )
        boundary["given"] = copy.deepcopy(positive["given"])
        self.assertIn(
            "TEST_CROSS_BOUNDARY_NOT_MEANINGFUL",
            issue_codes(fake_boundary),
        )

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
