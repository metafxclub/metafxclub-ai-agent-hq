"""Canonical EA-ready strategy research contract.

This module deliberately has no dependency on the bridge, runner, or frontend.
It provides one strict, versioned representation that Deep Research can hand to
the EA Factory without asking the writer to reinterpret prose.  Legacy report
metrics remain projections of this object; the blueprint is the authority.

The public helpers return validation issues as dictionaries with stable
``code`` and JSONPath-like ``path`` values.  ``normalize_blueprint`` raises a
``BlueprintValidationError`` containing the same issue records when the input
is structurally invalid or makes an inconsistent readiness claim.
"""

from __future__ import annotations

import copy
import hashlib
import ipaddress
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Sequence
from urllib.parse import urlsplit


SCHEMA_VERSION = "ea-ready-strategy-research/2.0.0"
SCHEMA_ID = "https://metafxclub.local/contracts/ea-implementation-blueprint-v2.schema.json"
SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "research"
    / "ea-implementation-blueprint-v2.schema.json"
)

CLOSED_BAR_SEMANTICS = {
    "bar0": "forming",
    "signalBar": 1,
    "previousBar": 2,
    "evaluateOn": "new_closed_bar",
    "lookaheadForbidden": True,
    "equalityPolicy": "touch_then_break",
}

BLUEPRINT_ALIASES = (
    "eaImplementationBlueprint",
    "eaBlueprint",
    "eaReadyBlueprint",
    "strategyBlueprint",
    "blueprint",
)

LEGACY_REPORT_METRIC_KEYS = (
    "systemIdentity",
    "verifiedRules",
    "conflictingEvidence",
    "setupConditions",
    "indicatorSettings",
    "entrySteps",
    "exitSteps",
    "tradeManagementSteps",
    "riskModel",
    "recoveryAndAveragingRules",
    "specialConditions",
    "suitableMarket",
    "suitableTimeframe",
    "ohlcBacktestReadiness",
    "implementationNotes",
    "sourceLinks",
    "checkedAt",
    "limitations",
)

SOURCE_STATUSES = {
    "verified_fact",
    "derived_expansion",
    "operator_assumption",
    "unknown",
}
READINESS_STATUSES = {"ready", "needs_clarification", "not_ea_ready"}
SIDES = {"buy", "sell"}
ENTRY_ORDER_TYPES = {"market", "limit", "stop"}
LOT_MODES = {
    "fixed_lot",
    "fixed_fractional_balance",
    "fixed_fractional_equity",
    "free_margin_fraction",
    "sequence",
}
DUPLICATE_SIGNAL_POLICIES = {
    "one_decision_per_symbol_bar",
    "ignore_while_pending",
    "replace_pending_same_signal",
}
EXECUTION_EVALUATION_STEPS = {"safety", "manage", "exit", "recovery", "entry"}
INVALID_PRICE_POLICIES = {"reject_order", "normalize_nearest_tick"}
RETRY_EXHAUSTED_ACTIONS = {"abort_signal", "halt_new_entries"}
MISSING_STATE_POLICIES = {"reconstruct_from_broker", "halt_new_entries"}
MANAGEMENT_ACTION_KINDS = {
    "move_stop_loss",
    "move_take_profit",
    "close_partial",
    "close_position",
    "scale_in",
    "scale_out",
    "place_pending",
    "cancel_pending",
    "replace_pending",
    "modify_pending",
}
MANAGEMENT_ACTIONS_BY_FEATURE = {
    "breakEven": {"move_stop_loss"},
    "trailingStop": {"move_stop_loss"},
    "scaleIn": {"scale_in"},
    "scaleOut": {"scale_out", "close_partial", "close_position"},
    "modifyStopLoss": {"move_stop_loss"},
    "modifyTakeProfit": {"move_take_profit"},
    "pendingOrders": {
        "place_pending",
        "cancel_pending",
        "replace_pending",
        "modify_pending",
    },
}
PENDING_PRICE_METHODS = {"at_reference", "offset_points", "offset_pips", "indicator_buffer"}
PENDING_PRICE_REFERENCES = {"bid", "ask", "close_bar_1", "indicator"}
PENDING_PRICE_DIRECTIONS = {"above", "below", "exact"}
PENDING_EXPIRY_MODES = {"gtc", "bars", "datetime"}
RECOVERY_MODES = {"none", "grid", "martingale", "averaging", "hedging"}
RECOVERY_SPACING_METHODS = {
    "fixed_points",
    "fixed_pips",
    "atr",
    "percent",
    "indicator",
    "formula",
}
RECOVERY_SPACING_REFERENCES = {
    "previous_recovery_entry",
    "initial_entry",
    "basket_average_price",
    "market_price",
}
RECOVERY_LOT_MODES = {"fixed", "multiplier", "sequence", "risk_percent", "formula"}
BASKET_THRESHOLD_METHODS = {
    "none",
    "fixed_currency",
    "fixed_points",
    "fixed_pips",
    "percent",
    "price",
    "formula",
}
BASKET_THRESHOLD_REFERENCES = {
    "basket_profit",
    "basket_loss",
    "basket_average_price",
    "account_equity",
    "account_balance",
}
HEDGE_CLOSE_ORDERS = {
    "hedge_first",
    "original_first",
    "oldest_first",
    "newest_first",
    "all_together",
}
REENTRY_ALLOWED_AFTER = {
    "reset",
    "basket_close",
    "stop_loss",
    "abort",
    "opposite_signal",
    "never",
}
MANAGEMENT_CADENCES = {
    "every_tick",
    "new_closed_bar",
    "on_price_change",
    "once_per_position",
    "once_per_level",
}
PROTECTION_TYPES = {
    "none",
    "fixed_points",
    "fixed_pips",
    "atr",
    "swing",
    "percent",
    "rr",
    "indicator",
    "basket",
}
PROTECTION_REFERENCES = {
    "entry_price",
    "bid",
    "ask",
    "close",
    "swing_high",
    "swing_low",
    "indicator_value",
    "basket_price",
}
PROTECTION_UNITS = {
    "point",
    "pip",
    "percent",
    "atr_multiple",
    "risk_multiple",
    "price",
}
PROTECTION_BASKET_PRICE_FIELDS = {
    "average_entry_price",
    "break_even_price",
    "weighted_average_entry_price",
}
PROTECTION_BASKET_SCOPES = {"symbol_magic_side"}
RR_RISK_REFERENCES = {"initial_stop_loss_distance"}
PRICE_FORMULA_OPERATORS = {
    "operand",
    "add",
    "subtract",
    "multiply",
    "divide",
    "min",
    "max",
    "negate",
}
PRICE_FORMULA_OPERAND_KINDS = {"reference", "constant", "input", "indicator"}
PRICE_FORMULA_UNITS = {"price", "price_distance", "scalar"}
PRICE_FORMULA_REFERENCES = {
    "entry_price",
    "bid",
    "ask",
    "close",
    "swing_high",
    "swing_low",
    "basket_price",
    "initial_stop_distance",
    "current_stop_distance",
}
PRICE_FORMULA_REFERENCE_UNITS = {
    "entry_price": "price",
    "bid": "price",
    "ask": "price",
    "close": "price",
    "swing_high": "price",
    "swing_low": "price",
    "basket_price": "price",
    "initial_stop_distance": "price_distance",
    "current_stop_distance": "price_distance",
}
PROTECTION_PLACEMENT_TIMINGS = {"with_entry", "after_fill", "next_tick", "on_trigger"}
MINIMUM_STOP_POLICIES = {"reject_entry", "adjust_outward", "defer_modify"}
FREEZE_LEVEL_POLICIES = {"reject_entry", "defer_modify", "retry_bounded"}
INPUT_TYPES = {"int", "double", "bool", "enum", "string", "timeframe"}
EXPRESSION_OPERATORS = {
    "and",
    "or",
    "not",
    "<",
    "<=",
    ">",
    ">=",
    "==",
    "!=",
    "cross_above",
    "cross_below",
    "break_above",
    "break_below",
    "close_above",
    "close_below",
    "touch",
    "within",
    "rising",
    "falling",
    "once_per_bar",
    "unknown",
}
OPERAND_KINDS = {
    "indicator",
    "input",
    "constant",
    "price",
    "account",
    "position",
    "basket",
    "session",
    "spread",
    "time",
    "symbol_property",
}

_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_RULE_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_:-]{0,127}$")
_HTTP_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)
_ROOT_FIELDS = {
    "schemaVersion",
    "strategyId",
    "researchRevision",
    "checkedAt",
    "barSemantics",
    "scope",
    "inputs",
    "indicators",
    "setup",
    "entry",
    "exit",
    "orderManagement",
    "tpSl",
    "riskAndSizing",
    "recovery",
    "execution",
    "stateMachine",
    "conflicts",
    "precedence",
    "pseudocode",
    "testCases",
    "evidenceMap",
    "assumptions",
    "unknowns",
    "completeness",
}
_ROOT_REQUIRED = frozenset(_ROOT_FIELDS)


@dataclass(frozen=True)
class BlueprintIssue:
    """One stable validation failure."""

    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


class BlueprintValidationError(ValueError):
    """Raised when a blueprint cannot be normalized into a valid contract."""

    def __init__(self, issues: Iterable[BlueprintIssue | Mapping[str, str]]):
        normalized: list[dict[str, str]] = []
        for issue in issues:
            if isinstance(issue, BlueprintIssue):
                normalized.append(issue.as_dict())
            else:
                normalized.append(
                    {
                        "code": str(issue.get("code") or "BLUEPRINT_INVALID"),
                        "path": str(issue.get("path") or "$"),
                        "message": str(issue.get("message") or "Invalid EA research blueprint"),
                    }
                )
        self.issues = tuple(normalized)
        preview = "; ".join(
            f"{item['code']} at {item['path']}: {item['message']}"
            for item in self.issues[:5]
        )
        if len(self.issues) > 5:
            preview += f"; and {len(self.issues) - 5} more"
        super().__init__(preview or "Invalid EA research blueprint")


def _issue(issues: list[BlueprintIssue], code: str, path: str, message: str) -> None:
    issues.append(BlueprintIssue(code=code, path=path, message=message))


def _is_mapping(value: object) -> bool:
    return isinstance(value, Mapping)


def _parse_mapping(value: object, path: str) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise BlueprintValidationError(
                [
                    BlueprintIssue(
                        "BLUEPRINT_JSON_INVALID",
                        path,
                        f"JSON could not be decoded: {exc.msg}",
                    )
                ]
            ) from exc
    if not _is_mapping(value):
        raise BlueprintValidationError(
            [BlueprintIssue("BLUEPRINT_TYPE", path, "Blueprint must be a JSON object")]
        )
    return {str(key): copy.deepcopy(item) for key, item in value.items()}


def _normalize_scalar(value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    return value


def _normalize_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key).strip(): _normalize_json(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_normalize_json(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize_json(item) for item in value]
    return _normalize_scalar(value)


def _enum(value: object) -> object:
    return value.strip().lower().replace("-", "_") if isinstance(value, str) else value


def _dedupe_sorted_strings(value: object, *, upper: bool = False) -> object:
    if not isinstance(value, list):
        return value
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            return value
        text = item.strip()
        if upper:
            text = text.upper()
        if text and text not in normalized:
            normalized.append(text)
    return sorted(normalized)


def _normalize_operand(value: object) -> object:
    if not isinstance(value, Mapping):
        return _normalize_json(value)
    result = {str(key): _normalize_json(item) for key, item in value.items()}
    if "kind" in result:
        result["kind"] = _enum(result["kind"])
    if "source" in result and isinstance(result["source"], str):
        result["source"] = result["source"].strip().lower()
    return result


def _expression_operator(value: object) -> object:
    normalized = _enum(value)
    aliases = {
        "crossabove": "cross_above",
        "crossbelow": "cross_below",
        "lte": "<=",
        "gte": ">=",
        "lt": "<",
        "gt": ">",
        "eq": "==",
        "neq": "!=",
    }
    return aliases.get(normalized, normalized)


def _normalize_expression(value: object) -> object:
    if not isinstance(value, Mapping):
        return _normalize_json(value)
    result: dict[str, Any] = {
        str(key): _normalize_json(item) for key, item in value.items()
    }
    if "op" in result:
        result["op"] = _expression_operator(result["op"])
    for key in ("left", "right", "value", "lower", "upper"):
        if key in result:
            result[key] = _normalize_operand(result[key])
    if "item" in result:
        result["item"] = _normalize_expression(result["item"])
    if isinstance(result.get("items"), list):
        result["items"] = [_normalize_expression(item) for item in result["items"]]
    if isinstance(result.get("all"), list):
        result["all"] = [_normalize_expression(item) for item in result["all"]]
    if isinstance(result.get("expanded"), Mapping):
        expanded = {
            str(key): _normalize_json(item)
            for key, item in result["expanded"].items()
        }
        if isinstance(expanded.get("all"), list):
            expanded["all"] = [
                _normalize_expression(item) for item in expanded["all"]
            ]
        result["expanded"] = expanded

    if result.get("op") in {"cross_above", "cross_below"}:
        result.setdefault("currentShift", 1)
        result.setdefault("previousShift", 2)
        if "expanded" not in result and isinstance(result.get("left"), Mapping) and isinstance(
            result.get("right"), Mapping
        ):
            result["expanded"] = _expected_cross_expansion(result)
    return result


def _normalize_protection_unit(value: object) -> object:
    normalized = _enum(value)
    aliases = {
        "points": "point",
        "pips": "pip",
        "%": "percent",
        "percentage": "percent",
        "atr": "atr_multiple",
        "atr multiple": "atr_multiple",
        "rr": "risk_multiple",
        "r": "risk_multiple",
        "r_multiple": "risk_multiple",
    }
    return aliases.get(normalized, normalized)


def _normalize_price_formula_operand(value: object) -> object:
    if not isinstance(value, Mapping):
        return _normalize_json(value)
    result = {str(key): _normalize_json(item) for key, item in value.items()}
    for key in ("kind", "reference", "unit"):
        if key in result:
            result[key] = _enum(result[key])
    return result


def _normalize_price_formula(value: object) -> object:
    if not isinstance(value, Mapping):
        return _normalize_json(value)
    result = {str(key): _normalize_json(item) for key, item in value.items()}
    if "op" in result:
        result["op"] = _enum(result["op"])
    if "operand" in result:
        result["operand"] = _normalize_price_formula_operand(result["operand"])
    for key in ("left", "right"):
        if key in result:
            result[key] = _normalize_price_formula(result[key])
    return result


def _series_without_shift(value: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(dict(value))
    result.pop("shift", None)
    return result


def _operand_at(value: Mapping[str, Any], shift: int) -> dict[str, Any]:
    result = _series_without_shift(value)
    result["shift"] = shift
    return result


def _expected_cross_expansion(expression: Mapping[str, Any]) -> dict[str, Any]:
    left = expression.get("left")
    right = expression.get("right")
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        return {"all": []}
    if expression.get("op") == "cross_above":
        previous_op, current_op = "<=", ">"
    else:
        previous_op, current_op = ">=", "<"
    return {
        "all": [
            {
                "op": previous_op,
                "left": _operand_at(left, 2),
                "right": _operand_at(right, 2),
            },
            {
                "op": current_op,
                "left": _operand_at(left, 1),
                "right": _operand_at(right, 1),
            },
        ]
    }


def _normalize_rules(node: object) -> object:
    if isinstance(node, list):
        return [_normalize_rules(item) for item in node]
    if not isinstance(node, Mapping):
        return _normalize_json(node)
    result: dict[str, Any] = {
        str(key): _normalize_rules(item) for key, item in node.items()
    }
    if "sourceStatus" in result:
        result["sourceStatus"] = _enum(result["sourceStatus"])
    if "sourceRefs" in result:
        result["sourceRefs"] = _dedupe_sorted_strings(result["sourceRefs"])
    if "expression" in result:
        result["expression"] = _normalize_expression(result["expression"])
    return result


def _normalize_candidate(value: object) -> dict[str, Any]:
    result = _parse_mapping(value, "$")
    result = _normalize_json(result)  # type: ignore[assignment]
    assert isinstance(result, dict)

    if isinstance(result.get("schemaVersion"), str):
        result["schemaVersion"] = result["schemaVersion"].strip()
    if isinstance(result.get("strategyId"), str):
        result["strategyId"] = result["strategyId"].strip()

    bar = result.get("barSemantics")
    if isinstance(bar, dict):
        if "bar0" in bar:
            bar["bar0"] = _enum(bar["bar0"])
        if "evaluateOn" in bar:
            bar["evaluateOn"] = _enum(bar["evaluateOn"])
        if "equalityPolicy" in bar:
            bar["equalityPolicy"] = _enum(bar["equalityPolicy"])

    scope = result.get("scope")
    if isinstance(scope, dict):
        scope["platforms"] = _dedupe_sorted_strings(scope.get("platforms"), upper=True)
        scope["symbols"] = _dedupe_sorted_strings(scope.get("symbols"), upper=True)
        scope["enabledSides"] = _dedupe_sorted_strings(scope.get("enabledSides"))
        scope["suitableFor"] = _dedupe_sorted_strings(scope.get("suitableFor"))
        scope["sessions"] = _dedupe_sorted_strings(scope.get("sessions"))
        for key in ("signalTimeframe", "executionTimeframe"):
            if isinstance(scope.get(key), str):
                scope[key] = scope[key].strip().upper()

    for key in ("inputs", "indicators"):
        records = result.get(key)
        if isinstance(records, list):
            for record in records:
                if isinstance(record, dict):
                    if key == "inputs" and "type" in record:
                        record["type"] = _enum(record["type"])
                    if "sourceStatus" in record:
                        record["sourceStatus"] = _enum(record["sourceStatus"])
                    if "sourceRefs" in record:
                        record["sourceRefs"] = _dedupe_sorted_strings(record["sourceRefs"])
                    if "usedByRuleIds" in record:
                        record["usedByRuleIds"] = _dedupe_sorted_strings(
                            record["usedByRuleIds"]
                        )

    for key in ("setup", "entry", "exit", "orderManagement"):
        if key in result:
            result[key] = _normalize_rules(result[key])

    for lifecycle_key in ("entry", "exit"):
        lifecycle = result.get(lifecycle_key)
        if isinstance(lifecycle, dict):
            for side in SIDES:
                side_record = lifecycle.get(side)
                if isinstance(side_record, dict) and "orderType" in side_record:
                    side_record["orderType"] = _enum(side_record["orderType"])

    management = result.get("orderManagement")
    if isinstance(management, dict):
        for feature_name in (
            "breakEven",
            "trailingStop",
            "partialClose",
            "scaleIn",
            "scaleOut",
            "modifyStopLoss",
            "modifyTakeProfit",
            "pendingOrders",
        ):
            feature = management.get(feature_name)
            if isinstance(feature, dict) and "sourceStatus" in feature:
                feature["sourceStatus"] = _enum(feature["sourceStatus"])
            if isinstance(feature, dict):
                if isinstance(feature.get("trigger"), Mapping):
                    feature["trigger"] = _normalize_expression(feature["trigger"])
                action = feature.get("action")
                if isinstance(action, dict) and "kind" in action:
                    action["kind"] = _enum(action["kind"])
                parameters = feature.get("parameters")
                if feature_name == "pendingOrders" and isinstance(parameters, dict):
                    for enum_key in ("orderType",):
                        if enum_key in parameters:
                            parameters[enum_key] = _enum(parameters[enum_key])
                    entry_price = parameters.get("entryPrice")
                    if isinstance(entry_price, dict):
                        for enum_key in ("method", "reference", "direction"):
                            if enum_key in entry_price:
                                entry_price[enum_key] = _enum(entry_price[enum_key])
                    expiry = parameters.get("expiry")
                    if isinstance(expiry, dict) and "mode" in expiry:
                        expiry["mode"] = _enum(expiry["mode"])
                if feature_name == "partialClose":
                    steps = feature.get("steps")
                    if isinstance(steps, list):
                        for step in steps:
                            if isinstance(step, dict) and isinstance(step.get("trigger"), Mapping):
                                step["trigger"] = _normalize_expression(step["trigger"])

    tp_sl = result.get("tpSl")
    if isinstance(tp_sl, dict):
        protection_groups = [tp_sl]
        side_overrides = tp_sl.get("sideOverrides")
        if isinstance(side_overrides, dict):
            protection_groups.extend(
                side_overrides.get(side)
                for side in SIDES
                if isinstance(side_overrides.get(side), dict)
            )
        for group in protection_groups:
            if not isinstance(group, dict):
                continue
            for protection_name in ("stopLoss", "takeProfit"):
                protection = group.get(protection_name)
                if isinstance(protection, dict):
                    for enum_key in (
                        "type",
                        "reference",
                        "sourceStatus",
                        "placementTiming",
                        "minimumStopDistancePolicy",
                        "freezeLevelPolicy",
                        "rrRiskReference",
                        "basketPriceField",
                        "basketScope",
                    ):
                        if enum_key in protection:
                            protection[enum_key] = _enum(protection[enum_key])
                    if "unit" in protection:
                        protection["unit"] = _normalize_protection_unit(protection["unit"])
                    if "formula" in protection:
                        protection["formula"] = _normalize_price_formula(protection["formula"])
                    for ref_key in ("activationRuleIds", "invalidationRuleIds"):
                        if ref_key in protection:
                            protection[ref_key] = _dedupe_sorted_strings(protection[ref_key])

    recovery = result.get("recovery")
    if isinstance(recovery, dict):
        result["recovery"] = _normalize_rules(recovery)
        recovery = result["recovery"]
        for enum_key in ("mode", "direction", "sourceStatus"):
            if enum_key in recovery:
                recovery[enum_key] = _enum(recovery[enum_key])
        for child_key, enum_keys in (
            ("spacing", ("method", "reference", "sourceStatus")),
            ("lotFormula", ("mode", "sourceStatus")),
            ("basketTakeProfit", ("method", "reference", "sourceStatus")),
            ("basketStopLoss", ("method", "reference", "sourceStatus")),
            ("hedgeLifecycle", ("closeOrder", "sourceStatus")),
            ("reentryPolicy", ("allowedAfter", "sourceStatus")),
        ):
            child = recovery.get(child_key)
            if not isinstance(child, dict):
                continue
            for enum_key in enum_keys:
                if enum_key in child:
                    child[enum_key] = _enum(child[enum_key])
        hedge = recovery.get("hedgeLifecycle")
        if isinstance(hedge, dict):
            hedge_lot = hedge.get("lotFormula")
            if isinstance(hedge_lot, dict):
                for enum_key in ("mode", "sourceStatus"):
                    if enum_key in hedge_lot:
                        hedge_lot[enum_key] = _enum(hedge_lot[enum_key])

    execution = result.get("execution")
    if isinstance(execution, dict):
        for enum_key in ("evaluateOn", "entryOrderType", "duplicateSignalPolicy"):
            if enum_key in execution:
                execution[enum_key] = _enum(execution[enum_key])
        for child_key, enum_keys in (
            ("priceNormalization", ("invalidPricePolicy",)),
            ("retryPolicy", ("exhaustedAction",)),
            ("restartPersistence", ("missingStatePolicy",)),
        ):
            child = execution.get(child_key)
            if isinstance(child, dict):
                for enum_key in enum_keys:
                    if enum_key in child:
                        child[enum_key] = _enum(child[enum_key])

    risk = result.get("riskAndSizing")
    if isinstance(risk, dict) and "lotMode" in risk:
        risk["lotMode"] = _enum(risk["lotMode"])

    conflicts = result.get("conflicts")
    if isinstance(conflicts, list):
        for conflict in conflicts:
            if isinstance(conflict, dict) and "resolutionStatus" in conflict:
                conflict["resolutionStatus"] = _enum(conflict["resolutionStatus"])

    evidence = result.get("evidenceMap")
    if isinstance(evidence, list):
        evidence.sort(
            key=lambda item: str(item.get("sourceRef") or "")
            if isinstance(item, Mapping)
            else ""
        )
    for key, id_key in (
        ("inputs", "inputId"),
        ("indicators", "indicatorId"),
        ("testCases", "caseId"),
        ("stateMachine", "state"),
        ("conflicts", "conflictId"),
        ("assumptions", "assumptionId"),
        ("unknowns", "unknownId"),
    ):
        records = result.get(key)
        if isinstance(records, list):
            records.sort(
                key=lambda item: str(item.get(id_key) or "")
                if isinstance(item, Mapping)
                else ""
            )

    completeness = result.get("completeness")
    if isinstance(completeness, dict):
        if "status" in completeness:
            completeness["status"] = _enum(completeness["status"])
        for key in ("unknownPaths", "conflictPaths"):
            completeness[key] = _dedupe_sorted_strings(completeness.get(key))

    return result


def _valid_iso_datetime(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    candidate = value.strip()
    try:
        parsed = datetime.fromisoformat(candidate[:-1] + "+00:00" if candidate.endswith("Z") else candidate)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _validate_required_mapping(
    value: object,
    path: str,
    required: Sequence[str],
    issues: list[BlueprintIssue],
) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        _issue(issues, "OBJECT_REQUIRED", path, "Expected a JSON object")
        return None
    for field in required:
        if field not in value:
            _issue(issues, "FIELD_REQUIRED", f"{path}.{field}", "Required field is missing")
    return value


def _validate_nonempty_string(
    value: object,
    path: str,
    issues: list[BlueprintIssue],
    *,
    pattern: re.Pattern[str] | None = None,
) -> bool:
    if not isinstance(value, str) or not value.strip():
        _issue(issues, "STRING_REQUIRED", path, "Expected a non-empty string")
        return False
    if pattern is not None and not pattern.fullmatch(value.strip()):
        _issue(issues, "IDENTIFIER_INVALID", path, "Identifier has an invalid format")
        return False
    return True


def _validate_json_values(value: object, path: str, issues: list[BlueprintIssue]) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            _issue(issues, "NUMBER_NOT_FINITE", path, "JSON numbers must be finite")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            _validate_json_values(item, f"{path}.{key}", issues)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_values(item, f"{path}[{index}]", issues)
        return
    _issue(
        issues,
        "JSON_TYPE_INVALID",
        path,
        f"Unsupported JSON value type {type(value).__name__}",
    )


@lru_cache(maxsize=1)
def _canonical_schema_contract() -> dict[str, Any]:
    """Load the checked-in closed-object contract used by the Python gate.

    Domain semantics retain their stable hand-written diagnostics below.  The
    schema is authoritative for legal object keys, preventing nested
    ``additionalProperties: false`` declarations from drifting away from the
    runtime validator.
    """

    try:
        value = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise BlueprintValidationError(
            [BlueprintIssue("SCHEMA_CONTRACT_UNAVAILABLE", "$", "Canonical EA research schema is unavailable")]
        ) from exc
    if not isinstance(value, dict) or value.get("$id") != SCHEMA_ID:
        raise BlueprintValidationError(
            [BlueprintIssue("SCHEMA_CONTRACT_INVALID", "$", "Canonical EA research schema identity is invalid")]
        )
    return value


def _schema_pointer_value(root: Mapping[str, Any], reference: object) -> Mapping[str, Any] | None:
    if not isinstance(reference, str) or not reference.startswith("#/"):
        return None
    current: object = root
    for raw_part in reference[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current if isinstance(current, Mapping) else None


def _resolved_schema_node(
    schema: Mapping[str, Any],
    root: Mapping[str, Any],
) -> Mapping[str, Any]:
    current = schema
    visited: set[str] = set()
    while isinstance(current.get("$ref"), str):
        reference = str(current["$ref"])
        if reference in visited:
            break
        visited.add(reference)
        target = _schema_pointer_value(root, reference)
        if target is None:
            break
        if len(current) == 1:
            current = target
            continue
        merged = dict(target)
        merged.update({key: item for key, item in current.items() if key != "$ref"})
        current = merged
    return current


def _schema_type_matches(value: object, expected: object) -> bool:
    if isinstance(expected, list):
        return any(_schema_type_matches(value, item) for item in expected)
    return {
        "object": isinstance(value, Mapping),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "null": value is None,
    }.get(str(expected), True)


def _schema_branch_matches(
    value: object,
    schema: Mapping[str, Any],
    root: Mapping[str, Any],
) -> bool:
    node = _resolved_schema_node(schema, root)
    expected_type = node.get("type")
    if expected_type is not None and not _schema_type_matches(value, expected_type):
        return False
    if "const" in node and value != node.get("const"):
        return False
    enum_values = node.get("enum")
    if isinstance(enum_values, list) and value not in enum_values:
        return False
    if isinstance(value, Mapping):
        required = node.get("required")
        if isinstance(required, list) and any(key not in value for key in required):
            return False
        properties = node.get("properties")
        if isinstance(properties, Mapping):
            for key, child_schema in properties.items():
                if key not in value or not isinstance(child_schema, Mapping):
                    continue
                child = _resolved_schema_node(child_schema, root)
                if "const" in child and value[key] != child.get("const"):
                    return False
                child_enum = child.get("enum")
                if isinstance(child_enum, list) and value[key] not in child_enum:
                    return False
    return True


def _schema_path_child(path: str, key: object) -> str:
    text = str(key)
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", text):
        return f"{path}.{text}"
    escaped = text.replace("\\", "\\\\").replace("'", "\\'")
    return f"{path}['{escaped}']"


def _validate_schema_unknown_fields(
    value: object,
    schema: Mapping[str, Any],
    root: Mapping[str, Any],
    path: str,
    issues: list[BlueprintIssue],
) -> None:
    """Reject keys forbidden by nested closed-object schema nodes.

    This validates shape allowlists only.  Types, references, cross expansion,
    safety caps, and readiness consistency remain under the domain validator,
    which provides strategy-specific error codes.
    """

    node = _resolved_schema_node(schema, root)

    for choice_key in ("oneOf", "anyOf"):
        choices = node.get(choice_key)
        if not isinstance(choices, list):
            continue
        candidates = [
            option
            for option in choices
            if isinstance(option, Mapping) and _schema_branch_matches(value, option, root)
        ]
        if not candidates:
            candidates = [option for option in choices if isinstance(option, Mapping)]
        if candidates:
            branch_results: list[list[BlueprintIssue]] = []
            for option in candidates:
                branch_issues: list[BlueprintIssue] = []
                _validate_schema_unknown_fields(value, option, root, path, branch_issues)
                branch_results.append(branch_issues)
            selected = min(
                branch_results,
                key=lambda result: (len(result), tuple((item.path, item.code) for item in result)),
            )
            issues.extend(selected)

    all_of = node.get("allOf")
    if isinstance(all_of, list):
        for fragment in all_of:
            if not isinstance(fragment, Mapping):
                continue
            condition = fragment.get("if")
            if isinstance(condition, Mapping):
                branch_key = "then" if _schema_branch_matches(value, condition, root) else "else"
                branch = fragment.get(branch_key)
                if isinstance(branch, Mapping):
                    _validate_schema_unknown_fields(value, branch, root, path, issues)
            else:
                _validate_schema_unknown_fields(value, fragment, root, path, issues)

    properties = node.get("properties")
    is_object = node.get("type") == "object" or isinstance(properties, Mapping)
    if is_object and isinstance(value, Mapping):
        patterns = node.get("patternProperties")
        additional = node.get("additionalProperties", True)
        for key, child_value in value.items():
            child_path = _schema_path_child(path, key)
            child_schema = properties.get(key) if isinstance(properties, Mapping) else None
            if isinstance(child_schema, Mapping):
                _validate_schema_unknown_fields(child_value, child_schema, root, child_path, issues)
                continue
            pattern_matches: list[Mapping[str, Any]] = []
            if isinstance(patterns, Mapping):
                for pattern, pattern_schema in patterns.items():
                    try:
                        matches = re.search(str(pattern), str(key)) is not None
                    except re.error:
                        matches = False
                    if matches and isinstance(pattern_schema, Mapping):
                        pattern_matches.append(pattern_schema)
            if pattern_matches:
                for pattern_schema in pattern_matches:
                    _validate_schema_unknown_fields(
                        child_value,
                        pattern_schema,
                        root,
                        child_path,
                        issues,
                    )
                continue
            if additional is False:
                _issue(
                    issues,
                    "UNKNOWN_ROOT_FIELD" if path == "$" else "UNKNOWN_FIELD",
                    child_path,
                    "Field is not permitted by the canonical EA research schema",
                )
            elif isinstance(additional, Mapping):
                _validate_schema_unknown_fields(
                    child_value,
                    additional,
                    root,
                    child_path,
                    issues,
                )
        return

    if node.get("type") == "array" and isinstance(value, list):
        item_schema = node.get("items")
        if isinstance(item_schema, Mapping):
            for index, item in enumerate(value):
                _validate_schema_unknown_fields(
                    item,
                    item_schema,
                    root,
                    f"{path}[{index}]",
                    issues,
                )


def _validate_string_list(
    value: object,
    path: str,
    issues: list[BlueprintIssue],
    *,
    min_items: int = 0,
    enum: set[str] | None = None,
) -> list[str]:
    if not isinstance(value, list):
        _issue(issues, "ARRAY_REQUIRED", path, "Expected an array")
        return []
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            _issue(issues, "STRING_REQUIRED", f"{path}[{index}]", "Expected a non-empty string")
            continue
        text = item.strip()
        result.append(text)
        if enum is not None and text not in enum:
            _issue(issues, "ENUM_INVALID", f"{path}[{index}]", f"Expected one of {sorted(enum)}")
    if len(result) < min_items:
        _issue(issues, "ARRAY_TOO_SHORT", path, f"Expected at least {min_items} item(s)")
    if len(result) != len(set(result)):
        _issue(issues, "ARRAY_DUPLICATE", path, "Array items must be unique")
    return result


def _validate_source_refs(
    value: object,
    path: str,
    evidence_ids: set[str],
    issues: list[BlueprintIssue],
    *,
    required: bool,
) -> None:
    refs = _validate_string_list(value, path, issues, min_items=1 if required else 0)
    for index, ref in enumerate(refs):
        if ref not in evidence_ids:
            _issue(
                issues,
                "SOURCE_REF_UNDEFINED",
                f"{path}[{index}]",
                f"Source reference {ref!r} is not defined in evidenceMap",
            )


def _validate_defined_ref(
    record: Mapping[str, Any],
    key: str,
    path: str,
    defined: set[str],
    issues: list[BlueprintIssue],
    *,
    required: bool = False,
    code: str = "INPUT_REF_UNDEFINED",
) -> None:
    value = record.get(key)
    if value in (None, ""):
        if required:
            _issue(issues, "FIELD_REQUIRED", f"{path}.{key}", "Required reference is missing")
        return
    if not isinstance(value, str) or value not in defined:
        _issue(issues, code, f"{path}.{key}", f"Unknown reference {value!r}")


def _is_positive_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) > 0
    )


def _validate_recovery_provenance(
    record: Mapping[str, Any],
    path: str,
    evidence_ids: set[str],
    issues: list[BlueprintIssue],
    unresolved_reasons: list[tuple[str, str]],
) -> None:
    source_status = record.get("sourceStatus")
    if source_status not in SOURCE_STATUSES:
        _issue(
            issues,
            "SOURCE_STATUS_INVALID",
            f"{path}.sourceStatus",
            f"Expected one of {sorted(SOURCE_STATUSES)}",
        )
    _validate_source_refs(
        record.get("sourceRefs"),
        f"{path}.sourceRefs",
        evidence_ids,
        issues,
        required=source_status == "verified_fact",
    )
    if source_status == "unknown":
        unresolved_reasons.append((path, "recovery execution detail is unresolved"))


def _validate_recovery_spacing(
    value: object,
    path: str,
    *,
    input_ids: set[str],
    indicator_ids: set[str],
    evidence_ids: set[str],
    issues: list[BlueprintIssue],
    unresolved_reasons: list[tuple[str, str]],
) -> None:
    record = _validate_required_mapping(
        value,
        path,
        ("method", "reference", "unit", "adverseMoveOnly", "sourceStatus", "sourceRefs"),
        issues,
    )
    if record is None:
        unresolved_reasons.append((path, "recovery spacing is not typed"))
        return
    method = record.get("method")
    if method not in RECOVERY_SPACING_METHODS:
        _issue(issues, "RECOVERY_SPACING_METHOD_INVALID", f"{path}.method", f"Expected one of {sorted(RECOVERY_SPACING_METHODS)}")
    if record.get("reference") not in RECOVERY_SPACING_REFERENCES:
        _issue(issues, "RECOVERY_SPACING_REFERENCE_INVALID", f"{path}.reference", f"Expected one of {sorted(RECOVERY_SPACING_REFERENCES)}")
    _validate_nonempty_string(record.get("unit"), f"{path}.unit", issues)
    if not isinstance(record.get("adverseMoveOnly"), bool):
        _issue(issues, "BOOLEAN_REQUIRED", f"{path}.adverseMoveOnly", "Expected a boolean")
    _validate_recovery_provenance(record, path, evidence_ids, issues, unresolved_reasons)
    _validate_defined_ref(record, "valueInputRef", path, input_ids, issues)
    _validate_defined_ref(
        record,
        "indicatorRef",
        path,
        indicator_ids,
        issues,
        code="INDICATOR_REF_UNDEFINED",
    )
    for key in ("value", "multiplier"):
        if key in record and not _is_positive_finite(record.get(key)):
            _issue(issues, "RECOVERY_SPACING_VALUE_INVALID", f"{path}.{key}", f"{key} must be finite and greater than zero")
    if method in {"fixed_points", "fixed_pips", "percent"} and record.get("value") is None and record.get("valueInputRef") in (None, ""):
        unresolved_reasons.append((path, f"{method} spacing requires value or valueInputRef"))
    if method == "atr":
        if record.get("indicatorRef") in (None, ""):
            unresolved_reasons.append((f"{path}.indicatorRef", "ATR spacing requires indicatorRef"))
        if not _is_positive_finite(record.get("multiplier")):
            unresolved_reasons.append((f"{path}.multiplier", "ATR spacing requires a positive multiplier"))
    if method == "indicator" and record.get("indicatorRef") in (None, ""):
        unresolved_reasons.append((f"{path}.indicatorRef", "indicator spacing requires indicatorRef"))
    if method == "formula" and (
        not isinstance(record.get("formula"), str)
        or not record.get("formula", "").strip()
    ):
        unresolved_reasons.append((f"{path}.formula", "formula spacing requires an explicit equation"))


def _validate_recovery_lot_formula(
    value: object,
    path: str,
    *,
    input_ids: set[str],
    evidence_ids: set[str],
    issues: list[BlueprintIssue],
    unresolved_reasons: list[tuple[str, str]],
) -> Mapping[str, Any] | None:
    record = _validate_required_mapping(
        value,
        path,
        ("mode", "levelVariable", "normalizeToBrokerLotStep", "sourceStatus", "sourceRefs"),
        issues,
    )
    if record is None:
        unresolved_reasons.append((path, "recovery lot progression is not typed"))
        return None
    mode = record.get("mode")
    if mode not in RECOVERY_LOT_MODES:
        _issue(issues, "RECOVERY_LOT_MODE_INVALID", f"{path}.mode", f"Expected one of {sorted(RECOVERY_LOT_MODES)}")
    _validate_nonempty_string(record.get("levelVariable"), f"{path}.levelVariable", issues)
    if record.get("normalizeToBrokerLotStep") is not True:
        unresolved_reasons.append((f"{path}.normalizeToBrokerLotStep", "recovery lots must be normalized to the broker lot step"))
    _validate_recovery_provenance(record, path, evidence_ids, issues, unresolved_reasons)
    for key in ("baseLotInputRef", "multiplierInputRef", "riskPercentInputRef"):
        _validate_defined_ref(record, key, path, input_ids, issues)
    for key in ("baseLot", "multiplier"):
        if key in record and not _is_positive_finite(record.get(key)):
            _issue(issues, "RECOVERY_LOT_VALUE_INVALID", f"{path}.{key}", f"{key} must be finite and greater than zero")
    base_is_defined = _is_positive_finite(record.get("baseLot")) or record.get("baseLotInputRef") not in (None, "")
    if mode in {"fixed", "multiplier"} and not base_is_defined:
        unresolved_reasons.append((path, f"{mode} lot mode requires baseLot or baseLotInputRef"))
    if mode == "multiplier" and not (
        _is_positive_finite(record.get("multiplier"))
        or record.get("multiplierInputRef") not in (None, "")
    ):
        unresolved_reasons.append((path, "multiplier lot mode requires multiplier or multiplierInputRef"))
    sequence = record.get("sequence")
    if mode == "sequence" and (
        not isinstance(sequence, list)
        or not sequence
        or any(not _is_positive_finite(item) for item in sequence)
    ):
        unresolved_reasons.append((f"{path}.sequence", "sequence lot mode requires a non-empty positive lot sequence"))
    if mode == "risk_percent" and record.get("riskPercentInputRef") in (None, ""):
        unresolved_reasons.append((f"{path}.riskPercentInputRef", "risk-percent lot mode requires riskPercentInputRef"))
    if mode == "formula" and (
        not isinstance(record.get("formula"), str)
        or not record.get("formula", "").strip()
    ):
        unresolved_reasons.append((f"{path}.formula", "formula lot mode requires an explicit equation"))
    return record


def _validate_basket_threshold(
    value: object,
    path: str,
    *,
    input_ids: set[str],
    evidence_ids: set[str],
    issues: list[BlueprintIssue],
    unresolved_reasons: list[tuple[str, str]],
) -> None:
    record = _validate_required_mapping(
        value,
        path,
        ("enabled", "method", "reference", "sourceStatus", "sourceRefs"),
        issues,
    )
    if record is None:
        unresolved_reasons.append((path, "basket protection is not typed"))
        return
    enabled = record.get("enabled")
    method = record.get("method")
    if not isinstance(enabled, bool):
        _issue(issues, "BOOLEAN_REQUIRED", f"{path}.enabled", "Expected a boolean")
    if method not in BASKET_THRESHOLD_METHODS:
        _issue(issues, "BASKET_THRESHOLD_METHOD_INVALID", f"{path}.method", f"Expected one of {sorted(BASKET_THRESHOLD_METHODS)}")
    if record.get("reference") not in BASKET_THRESHOLD_REFERENCES:
        _issue(issues, "BASKET_THRESHOLD_REFERENCE_INVALID", f"{path}.reference", f"Expected one of {sorted(BASKET_THRESHOLD_REFERENCES)}")
    _validate_recovery_provenance(record, path, evidence_ids, issues, unresolved_reasons)
    _validate_defined_ref(record, "valueInputRef", path, input_ids, issues)
    if "value" in record and not _is_positive_finite(record.get("value")):
        _issue(issues, "BASKET_THRESHOLD_VALUE_INVALID", f"{path}.value", "value must be finite and greater than zero")
    if enabled is True and method == "none":
        _issue(issues, "BASKET_THRESHOLD_ENABLEMENT_MISMATCH", f"{path}.method", "Enabled basket protection cannot use method none")
    if enabled is False and method != "none":
        _issue(issues, "BASKET_THRESHOLD_ENABLEMENT_MISMATCH", f"{path}.method", "Disabled basket protection must use method none")
    if enabled is True:
        _validate_nonempty_string(record.get("unit"), f"{path}.unit", issues)
        if method == "formula":
            if (
                not isinstance(record.get("formula"), str)
                or not record.get("formula", "").strip()
            ):
                unresolved_reasons.append((f"{path}.formula", "formula basket protection requires an explicit equation"))
        elif record.get("value") is None and record.get("valueInputRef") in (None, ""):
            unresolved_reasons.append((path, f"{method} basket protection requires value or valueInputRef"))


def _recovery_expression_is_unknown(value: object) -> bool:
    return isinstance(value, Mapping) and value.get("op") == "unknown"


def _validate_operand(
    value: object,
    path: str,
    issues: list[BlueprintIssue],
    *,
    input_ids: set[str],
    indicator_ids: set[str],
    closed_bar: bool,
) -> None:
    if not isinstance(value, Mapping):
        _issue(issues, "OPERAND_OBJECT_REQUIRED", path, "Expression operand must be an object")
        return
    kind = value.get("kind")
    if kind not in OPERAND_KINDS:
        _issue(issues, "OPERAND_KIND_INVALID", f"{path}.kind", f"Expected one of {sorted(OPERAND_KINDS)}")
        return
    if kind == "indicator":
        ref = value.get("ref") or value.get("indicatorId")
        if not isinstance(ref, str) or ref not in indicator_ids:
            _issue(issues, "INDICATOR_REF_UNDEFINED", f"{path}.ref", f"Unknown indicator reference {ref!r}")
    elif kind == "input":
        ref = value.get("ref") or value.get("inputId")
        if not isinstance(ref, str) or ref not in input_ids:
            _issue(issues, "INPUT_REF_UNDEFINED", f"{path}.ref", f"Unknown input reference {ref!r}")
    elif kind == "constant":
        constant = value.get("value")
        if constant is None or isinstance(constant, (dict, list)):
            _issue(issues, "CONSTANT_VALUE_REQUIRED", f"{path}.value", "Constant operand requires a scalar value")
    elif kind == "price":
        field = value.get("field")
        if field not in {"open", "high", "low", "close", "bid", "ask", "mid"}:
            _issue(issues, "PRICE_FIELD_INVALID", f"{path}.field", "Price field must name OHLC, bid, ask, or mid")

    if "shift" in value:
        shift = value.get("shift")
        if not isinstance(shift, int) or isinstance(shift, bool) or shift < 0:
            _issue(issues, "BAR_SHIFT_INVALID", f"{path}.shift", "Bar shift must be a non-negative integer")
        elif closed_bar and shift == 0:
            _issue(
                issues,
                "CLOSED_BAR_SHIFT_ZERO",
                f"{path}.shift",
                "Closed-bar rules cannot read forming bar 0",
            )


def _canonical_fragment(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _validate_expression(
    expression: object,
    path: str,
    issues: list[BlueprintIssue],
    *,
    input_ids: set[str],
    indicator_ids: set[str],
    closed_bar: bool,
) -> None:
    if not isinstance(expression, Mapping):
        _issue(issues, "EXPRESSION_OBJECT_REQUIRED", path, "Rule expression must be an object")
        return
    op = expression.get("op")
    if op not in EXPRESSION_OPERATORS:
        _issue(issues, "EXPRESSION_OPERATOR_INVALID", f"{path}.op", f"Expected one of {sorted(EXPRESSION_OPERATORS)}")
        return

    if op in {"and", "or"}:
        items = expression.get("items")
        if not isinstance(items, list) or len(items) < 1:
            _issue(issues, "EXPRESSION_ITEMS_REQUIRED", f"{path}.items", "Boolean expression requires at least one child")
            return
        for index, item in enumerate(items):
            _validate_expression(
                item,
                f"{path}.items[{index}]",
                issues,
                input_ids=input_ids,
                indicator_ids=indicator_ids,
                closed_bar=closed_bar,
            )
        return

    if op == "not":
        _validate_expression(
            expression.get("item"),
            f"{path}.item",
            issues,
            input_ids=input_ids,
            indicator_ids=indicator_ids,
            closed_bar=closed_bar,
        )
        return

    if op == "unknown":
        return

    if op in {"cross_above", "cross_below"}:
        left, right = expression.get("left"), expression.get("right")
        _validate_operand(left, f"{path}.left", issues, input_ids=input_ids, indicator_ids=indicator_ids, closed_bar=closed_bar)
        _validate_operand(right, f"{path}.right", issues, input_ids=input_ids, indicator_ids=indicator_ids, closed_bar=closed_bar)
        for key, expected in (("previousShift", 2), ("currentShift", 1)):
            if expression.get(key) != expected:
                _issue(
                    issues,
                    "CROSS_BAR_SEMANTICS_INVALID",
                    f"{path}.{key}",
                    f"Closed-bar crossover requires {key}={expected}",
                )
        if isinstance(left, Mapping) and "shift" in left:
            _issue(issues, "CROSS_SERIES_SHIFT_FORBIDDEN", f"{path}.left.shift", "Crossover series shift is defined by previousShift/currentShift")
        if isinstance(right, Mapping) and "shift" in right:
            _issue(issues, "CROSS_SERIES_SHIFT_FORBIDDEN", f"{path}.right.shift", "Crossover series shift is defined by previousShift/currentShift")
        expected_expansion = _expected_cross_expansion(expression)
        try:
            actual = _canonical_fragment(expression.get("expanded"))
            expected = _canonical_fragment(expected_expansion)
        except (TypeError, ValueError):
            actual, expected = "", "!"
        if actual != expected:
            formula = (
                "left[2] <= right[2] then left[1] > right[1]"
                if op == "cross_above"
                else "left[2] >= right[2] then left[1] < right[1]"
            )
            _issue(
                issues,
                "CROSS_EXPANSION_MISMATCH",
                f"{path}.expanded",
                f"{op} must expand exactly to {formula}",
            )
        expanded = expression.get("expanded")
        if isinstance(expanded, Mapping) and isinstance(expanded.get("all"), list):
            for index, item in enumerate(expanded["all"]):
                _validate_expression(
                    item,
                    f"{path}.expanded.all[{index}]",
                    issues,
                    input_ids=input_ids,
                    indicator_ids=indicator_ids,
                    closed_bar=closed_bar,
                )
        return

    if op == "once_per_bar":
        if expression.get("barShift") != 1:
            _issue(issues, "ONCE_PER_BAR_SHIFT_INVALID", f"{path}.barShift", "Closed-bar once_per_bar requires barShift=1")
        return

    if op in {"rising", "falling"}:
        _validate_operand(expression.get("value"), f"{path}.value", issues, input_ids=input_ids, indicator_ids=indicator_ids, closed_bar=closed_bar)
        bars = expression.get("bars")
        if not isinstance(bars, int) or isinstance(bars, bool) or bars < 1:
            _issue(issues, "LOOKBACK_INVALID", f"{path}.bars", "rising/falling requires bars >= 1")
        return

    if op == "within":
        for key in ("value", "lower", "upper"):
            _validate_operand(expression.get(key), f"{path}.{key}", issues, input_ids=input_ids, indicator_ids=indicator_ids, closed_bar=closed_bar)
        return

    for key in ("left", "right"):
        _validate_operand(expression.get(key), f"{path}.{key}", issues, input_ids=input_ids, indicator_ids=indicator_ids, closed_bar=closed_bar)


def _field_has_value(record: Mapping[str, Any], field: str) -> bool:
    return field in record and record.get(field) not in (None, "")


def _validate_numeric_protection_input(
    ref: object,
    path: str,
    input_records: Mapping[str, Mapping[str, Any]],
    issues: list[BlueprintIssue],
    *,
    integer: bool = False,
    allow_zero: bool = False,
) -> None:
    if not isinstance(ref, str) or ref not in input_records:
        return
    input_record = input_records[ref]
    expected_types = {"int"} if integer else {"int", "double"}
    if input_record.get("type") not in expected_types:
        _issue(
            issues,
            "PROTECTION_INPUT_TYPE_INVALID",
            path,
            f"Protection input must use one of {sorted(expected_types)}",
        )
        return
    default = input_record.get("default")
    valid_number = (
        isinstance(default, (int, float))
        and not isinstance(default, bool)
        and math.isfinite(float(default))
    )
    if not valid_number or (float(default) < 0 if allow_zero else float(default) <= 0):
        qualifier = "zero or greater" if allow_zero else "greater than zero"
        _issue(
            issues,
            "PROTECTION_INPUT_DEFAULT_INVALID",
            path,
            f"Protection input default must be finite and {qualifier}",
        )


def _validate_price_formula_operand(
    operand: object,
    path: str,
    issues: list[BlueprintIssue],
    *,
    input_records: Mapping[str, Mapping[str, Any]],
    indicator_records: Mapping[str, Mapping[str, Any]],
    referenced_prices: set[str],
    referenced_indicators: set[str],
) -> str | None:
    if not isinstance(operand, Mapping):
        _issue(issues, "PRICE_OPERAND_OBJECT_REQUIRED", path, "Price formula operand must be an object")
        return None
    kind = operand.get("kind")
    if kind not in PRICE_FORMULA_OPERAND_KINDS:
        _issue(
            issues,
            "PRICE_OPERAND_KIND_INVALID",
            f"{path}.kind",
            f"Expected one of {sorted(PRICE_FORMULA_OPERAND_KINDS)}",
        )
        return None
    unit = operand.get("unit")
    if unit not in PRICE_FORMULA_UNITS:
        _issue(
            issues,
            "PRICE_OPERAND_UNIT_INVALID",
            f"{path}.unit",
            f"Expected one of {sorted(PRICE_FORMULA_UNITS)}",
        )
        unit = None

    defining_fields = {
        "reference": {"reference"},
        "constant": {"value"},
        "input": {"inputRef"},
        "indicator": {"indicatorRef", "shift"},
    }[str(kind)]
    allowed_fields = {"kind", "unit"} | defining_fields
    for field in sorted(set(operand) - allowed_fields):
        _issue(
            issues,
            "PRICE_OPERAND_FIELD_INCOMPATIBLE",
            f"{path}.{field}",
            f"Field {field!r} is not valid for price operand kind {kind!r}",
        )

    if kind == "reference":
        reference = operand.get("reference")
        if reference not in PRICE_FORMULA_REFERENCES:
            _issue(
                issues,
                "PRICE_REFERENCE_INVALID",
                f"{path}.reference",
                f"Expected one of {sorted(PRICE_FORMULA_REFERENCES)}",
            )
        else:
            referenced_prices.add(str(reference))
            expected_unit = PRICE_FORMULA_REFERENCE_UNITS[str(reference)]
            if unit is not None and unit != expected_unit:
                _issue(
                    issues,
                    "PRICE_REFERENCE_UNIT_MISMATCH",
                    f"{path}.unit",
                    f"Reference {reference!r} requires unit {expected_unit!r}",
                )
    elif kind == "constant":
        value = operand.get("value")
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(float(value))
        ):
            _issue(issues, "PRICE_CONSTANT_INVALID", f"{path}.value", "Price formula constant must be finite")
    elif kind == "input":
        ref = operand.get("inputRef")
        if not isinstance(ref, str) or ref not in input_records:
            _issue(issues, "INPUT_REF_UNDEFINED", f"{path}.inputRef", f"Unknown input reference {ref!r}")
        else:
            _validate_numeric_protection_input(ref, f"{path}.inputRef", input_records, issues, allow_zero=True)
    else:
        ref = operand.get("indicatorRef")
        if not isinstance(ref, str) or ref not in indicator_records:
            _issue(issues, "INDICATOR_REF_UNDEFINED", f"{path}.indicatorRef", f"Unknown indicator reference {ref!r}")
        else:
            referenced_indicators.add(ref)
        shift = operand.get("shift")
        if not isinstance(shift, int) or isinstance(shift, bool) or shift < 1:
            _issue(issues, "PRICE_INDICATOR_SHIFT_INVALID", f"{path}.shift", "Price indicator shift must be an integer >= 1")
        if unit is not None and unit != "price":
            _issue(issues, "PRICE_INDICATOR_UNIT_MISMATCH", f"{path}.unit", "Indicator price operand requires unit 'price'")
    return str(unit) if unit in PRICE_FORMULA_UNITS else None


def _validate_price_formula(
    formula: object,
    path: str,
    issues: list[BlueprintIssue],
    *,
    input_records: Mapping[str, Mapping[str, Any]],
    indicator_records: Mapping[str, Mapping[str, Any]],
    referenced_prices: set[str],
    referenced_indicators: set[str],
) -> str | None:
    if not isinstance(formula, Mapping):
        _issue(issues, "PRICE_FORMULA_OBJECT_REQUIRED", path, "Price formula must be a typed arithmetic object")
        return None
    op = formula.get("op")
    if op not in PRICE_FORMULA_OPERATORS:
        _issue(
            issues,
            "PRICE_FORMULA_OPERATOR_INVALID",
            f"{path}.op",
            "Price formulas accept arithmetic operators only; boolean rule expressions are forbidden",
        )
        return None
    expected_fields = {
        "operand": {"op", "operand"},
        "negate": {"op", "left"},
    }.get(str(op), {"op", "left", "right"})
    for field in sorted(set(formula) - expected_fields):
        _issue(
            issues,
            "PRICE_FORMULA_FIELD_INCOMPATIBLE",
            f"{path}.{field}",
            f"Field {field!r} is not valid for price formula operator {op!r}",
        )
    for field in sorted(expected_fields - set(formula)):
        _issue(issues, "PRICE_FORMULA_FIELD_REQUIRED", f"{path}.{field}", f"Operator {op!r} requires {field}")

    if op == "operand":
        return _validate_price_formula_operand(
            formula.get("operand"),
            f"{path}.operand",
            issues,
            input_records=input_records,
            indicator_records=indicator_records,
            referenced_prices=referenced_prices,
            referenced_indicators=referenced_indicators,
        )

    left_unit = _validate_price_formula(
        formula.get("left"),
        f"{path}.left",
        issues,
        input_records=input_records,
        indicator_records=indicator_records,
        referenced_prices=referenced_prices,
        referenced_indicators=referenced_indicators,
    )
    if op == "negate":
        if left_unit == "price":
            _issue(issues, "PRICE_FORMULA_DIMENSION_INVALID", path, "An absolute price cannot be negated")
            return None
        return left_unit

    right_unit = _validate_price_formula(
        formula.get("right"),
        f"{path}.right",
        issues,
        input_records=input_records,
        indicator_records=indicator_records,
        referenced_prices=referenced_prices,
        referenced_indicators=referenced_indicators,
    )
    right_node = formula.get("right")
    if (
        op == "divide"
        and isinstance(right_node, Mapping)
        and right_node.get("op") == "operand"
        and isinstance(right_node.get("operand"), Mapping)
        and right_node["operand"].get("kind") == "constant"
        and right_node["operand"].get("value") == 0
    ):
        _issue(issues, "PRICE_FORMULA_DIVIDE_BY_ZERO", f"{path}.right", "Price formula cannot divide by zero")
        return None
    if left_unit is None or right_unit is None:
        return None
    if op in {"min", "max"}:
        if left_unit != right_unit:
            _issue(issues, "PRICE_FORMULA_DIMENSION_INVALID", path, f"{op} operands must have the same unit")
            return None
        return left_unit
    if op == "add":
        if left_unit == right_unit:
            return left_unit
        if {left_unit, right_unit} == {"price", "price_distance"}:
            return "price"
    elif op == "subtract":
        if left_unit == right_unit:
            return "price_distance" if left_unit == "price" else left_unit
        if left_unit == "price" and right_unit == "price_distance":
            return "price"
    elif op == "multiply":
        if left_unit == "scalar":
            return right_unit
        if right_unit == "scalar":
            return left_unit
    elif op == "divide":
        if right_unit == "scalar":
            return left_unit
        if left_unit == right_unit:
            return "scalar"
    _issue(
        issues,
        "PRICE_FORMULA_DIMENSION_INVALID",
        path,
        f"Operator {op!r} cannot combine {left_unit!r} with {right_unit!r}",
    )
    return None


def _iter_rule_records(node: object, path: str = "$") -> Iterable[tuple[str, Mapping[str, Any]]]:
    if isinstance(node, Mapping):
        if "ruleId" in node:
            yield path, node
            return
        for key, value in node.items():
            yield from _iter_rule_records(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, item in enumerate(node):
            yield from _iter_rule_records(item, f"{path}[{index}]")


def _validate_rule_lists(node: object, path: str, issues: list[BlueprintIssue]) -> None:
    if isinstance(node, Mapping):
        for key, value in node.items():
            child_path = f"{path}.{key}"
            if key == "rules":
                if not isinstance(value, list):
                    _issue(issues, "RULE_ARRAY_REQUIRED", child_path, "rules must be an array")
                else:
                    for index, item in enumerate(value):
                        if not isinstance(item, Mapping):
                            _issue(issues, "TYPED_RULE_REQUIRED", f"{child_path}[{index}]", "Executable rules cannot be plain text")
            _validate_rule_lists(value, child_path, issues)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _validate_rule_lists(item, f"{path}[{index}]", issues)


def _validate_input_default(record: Mapping[str, Any], path: str, issues: list[BlueprintIssue]) -> None:
    input_type = record.get("type")
    default = record.get("default")
    if default is None:
        # An incomplete research revision must be able to preserve an honestly
        # unknown input without inventing a value.  Readiness is blocked by the
        # source-status checks; verified/derived records still require a typed
        # concrete default.
        if record.get("sourceStatus") in {"unknown", "operator_assumption"}:
            return
        _issue(
            issues,
            "INPUT_DEFAULT_TYPE",
            f"{path}.default",
            f"Default does not match input type {input_type!r}",
        )
        return
    valid = True
    if input_type == "int":
        valid = isinstance(default, int) and not isinstance(default, bool)
    elif input_type == "double":
        valid = isinstance(default, (int, float)) and not isinstance(default, bool)
    elif input_type == "bool":
        valid = isinstance(default, bool)
    elif input_type in {"enum", "string", "timeframe"}:
        valid = isinstance(default, str) and bool(default.strip())
    if not valid:
        _issue(issues, "INPUT_DEFAULT_TYPE", f"{path}.default", f"Default does not match input type {input_type!r}")

    numeric_default = isinstance(default, (int, float)) and not isinstance(default, bool)
    if numeric_default:
        if not math.isfinite(float(default)):
            _issue(issues, "NUMBER_NOT_FINITE", f"{path}.default", "Numbers must be finite")
        minimum, maximum = record.get("min"), record.get("max")
        if isinstance(minimum, (int, float)) and default < minimum:
            _issue(issues, "INPUT_DEFAULT_RANGE", f"{path}.default", "Default is below min")
        if isinstance(maximum, (int, float)) and default > maximum:
            _issue(issues, "INPUT_DEFAULT_RANGE", f"{path}.default", "Default is above max")
        if isinstance(minimum, (int, float)) and isinstance(maximum, (int, float)) and minimum > maximum:
            _issue(issues, "INPUT_RANGE_INVALID", path, "min cannot exceed max")
        step = record.get("step")
        if step is not None and (not isinstance(step, (int, float)) or isinstance(step, bool) or step <= 0):
            _issue(issues, "INPUT_STEP_INVALID", f"{path}.step", "Numeric step must be greater than zero")
    if input_type == "enum":
        values = _validate_string_list(record.get("allowedValues"), f"{path}.allowedValues", issues, min_items=1)
        if isinstance(default, str) and default not in values:
            _issue(issues, "INPUT_ENUM_DEFAULT", f"{path}.default", "Enum default must appear in allowedValues")


def _public_evidence_independence_key(value: object) -> str | None:
    """Return a conservative host key for a structurally public HTTP(S) URL.

    This is deliberately an offline check: it rejects loopback/private/local
    addresses and collapses common ``www``/subdomain variants, while live URL
    opening remains the research worker's evidence obligation.
    """

    if not isinstance(value, str):
        return None
    try:
        parsed = urlsplit(value.strip())
    except ValueError:
        return None
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None
    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        return None
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None:
        if not address.is_global:
            return None
        return address.compressed
    labels = [part for part in host.split(".") if part]
    if len(labels) < 2:
        return None
    if labels[0] == "www":
        labels = labels[1:]
    common_second_level = {
        "co.uk",
        "org.uk",
        "com.au",
        "net.au",
        "co.jp",
        "co.th",
        "com.sg",
        "com.hk",
    }
    suffix2 = ".".join(labels[-2:])
    width = 3 if suffix2 in common_second_level and len(labels) >= 3 else 2
    return ".".join(labels[-width:])


def _iter_active_code_source_records(
    node: object,
    path: str = "$",
) -> Iterable[tuple[str, Mapping[str, Any]]]:
    """Yield active source-tagged records that can alter generated EA code."""

    if isinstance(node, Mapping):
        if "sourceStatus" in node:
            if node.get("enabled") is False:
                return
            yield path, node
        for key, value in node.items():
            if key in {"sourceStatus", "sourceRefs"}:
                continue
            if key in {"evidenceMap", "assumptions", "unknowns", "conflicts", "completeness"}:
                continue
            yield from _iter_active_code_source_records(value, _schema_path_child(path, key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _iter_active_code_source_records(value, f"{path}[{index}]")


def _assumption_covers_path(assumption_path: str, code_path: str) -> bool:
    left = assumption_path.rstrip(".")
    right = code_path.rstrip(".")
    return bool(
        left
        and right
        and (
            left == right
            or right.startswith(left + ".")
            or right.startswith(left + "[")
            or left.startswith(right + ".")
            or left.startswith(right + "[")
        )
    )


def _expressions_match(left: object, right: object) -> bool:
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        return False
    try:
        return _canonical_fragment(_normalize_expression(left)) == _canonical_fragment(
            _normalize_expression(right)
        )
    except (BlueprintValidationError, TypeError, ValueError):
        return False


def _expression_contains_unknown(value: object) -> bool:
    if isinstance(value, Mapping):
        if value.get("op") == "unknown":
            return True
        return any(_expression_contains_unknown(item) for item in value.values())
    if isinstance(value, list):
        return any(_expression_contains_unknown(item) for item in value)
    return False


def _validate_pending_order_parameters(
    value: object,
    path: str,
    *,
    expected_order_type: str,
    input_ids: set[str],
    indicator_ids: set[str],
    issues: list[BlueprintIssue],
    unresolved_reasons: list[tuple[str, str]],
) -> None:
    if not isinstance(value, Mapping):
        unresolved_reasons.append((path, "pending order parameters are missing"))
        return
    order_type = value.get("orderType")
    if order_type not in {"limit", "stop"}:
        _issue(issues, "PENDING_ORDER_TYPE_INVALID", f"{path}.orderType", "Pending orderType must be limit or stop")
    elif order_type != expected_order_type:
        _issue(issues, "PENDING_ORDER_TYPE_MISMATCH", f"{path}.orderType", "Pending orderType must match execution.entryOrderType")

    entry_price = value.get("entryPrice")
    price_path = f"{path}.entryPrice"
    if not isinstance(entry_price, Mapping):
        unresolved_reasons.append((price_path, "pending entry price is missing"))
    else:
        method = entry_price.get("method")
        reference = entry_price.get("reference")
        direction = entry_price.get("direction")
        if method not in PENDING_PRICE_METHODS:
            _issue(issues, "PENDING_PRICE_METHOD_INVALID", f"{price_path}.method", f"Expected one of {sorted(PENDING_PRICE_METHODS)}")
        if reference not in PENDING_PRICE_REFERENCES:
            _issue(issues, "PENDING_PRICE_REFERENCE_INVALID", f"{price_path}.reference", f"Expected one of {sorted(PENDING_PRICE_REFERENCES)}")
        if direction not in PENDING_PRICE_DIRECTIONS:
            _issue(issues, "PENDING_PRICE_DIRECTION_INVALID", f"{price_path}.direction", f"Expected one of {sorted(PENDING_PRICE_DIRECTIONS)}")
        _validate_defined_ref(entry_price, "valueInputRef", price_path, input_ids, issues)
        _validate_defined_ref(entry_price, "indicatorRef", price_path, indicator_ids, issues)
        if method in {"offset_points", "offset_pips"}:
            value_is_valid = _is_positive_finite(entry_price.get("value"))
            input_is_valid = isinstance(entry_price.get("valueInputRef"), str) and entry_price.get("valueInputRef") in input_ids
            if not value_is_valid and not input_is_valid:
                unresolved_reasons.append((price_path, f"{method} requires positive value or valueInputRef"))
        elif method == "indicator_buffer":
            if not isinstance(entry_price.get("indicatorRef"), str) or entry_price.get("indicatorRef") not in indicator_ids:
                unresolved_reasons.append((price_path, "indicator_buffer requires indicatorRef"))
        elif method == "at_reference" and direction != "exact":
            unresolved_reasons.append((f"{price_path}.direction", "at_reference requires direction=exact"))

    expiry = value.get("expiry")
    expiry_path = f"{path}.expiry"
    if not isinstance(expiry, Mapping):
        unresolved_reasons.append((expiry_path, "pending expiry policy is missing"))
    else:
        mode = expiry.get("mode")
        if mode not in PENDING_EXPIRY_MODES:
            _issue(issues, "PENDING_EXPIRY_MODE_INVALID", f"{expiry_path}.mode", f"Expected one of {sorted(PENDING_EXPIRY_MODES)}")
        _validate_defined_ref(expiry, "barsInputRef", expiry_path, input_ids, issues)
        if mode == "bars":
            bars = expiry.get("bars")
            bars_ref = expiry.get("barsInputRef")
            if (not isinstance(bars, int) or isinstance(bars, bool) or bars < 1) and (
                not isinstance(bars_ref, str) or bars_ref not in input_ids
            ):
                unresolved_reasons.append((expiry_path, "bars expiry requires bars >= 1 or barsInputRef"))
        elif mode == "datetime" and not _valid_iso_datetime(expiry.get("expiresAt")):
            unresolved_reasons.append((f"{expiry_path}.expiresAt", "datetime expiry requires ISO-8601 expiresAt with timezone"))


def _validate_blueprint_candidate(candidate: Mapping[str, Any], *, require_ready: bool) -> list[BlueprintIssue]:
    issues: list[BlueprintIssue] = []
    pre_unresolved_reasons: list[tuple[str, str]] = []
    _validate_json_values(candidate, "$", issues)
    try:
        schema_contract = _canonical_schema_contract()
    except BlueprintValidationError as exc:
        issues.extend(
            BlueprintIssue(
                str(issue.get("code") or "SCHEMA_CONTRACT_INVALID"),
                str(issue.get("path") or "$"),
                str(issue.get("message") or "Canonical EA research schema is invalid"),
            )
            for issue in exc.issues
        )
    else:
        _validate_schema_unknown_fields(candidate, schema_contract, schema_contract, "$", issues)
    for key in sorted(_ROOT_REQUIRED - set(candidate)):
        _issue(issues, "FIELD_REQUIRED", f"$.{key}", "Required field is missing")

    if candidate.get("schemaVersion") != SCHEMA_VERSION:
        _issue(issues, "SCHEMA_VERSION_UNSUPPORTED", "$.schemaVersion", f"Expected {SCHEMA_VERSION}")
    _validate_nonempty_string(candidate.get("strategyId"), "$.strategyId", issues, pattern=_ID_PATTERN)
    revision = candidate.get("researchRevision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        _issue(issues, "REVISION_INVALID", "$.researchRevision", "researchRevision must be an integer >= 1")
    if not _valid_iso_datetime(candidate.get("checkedAt")):
        _issue(issues, "CHECKED_AT_INVALID", "$.checkedAt", "checkedAt must be ISO-8601 with timezone")

    evidence_ids: set[str] = set()
    public_evidence_keys: set[str] = set()
    evidence = candidate.get("evidenceMap")
    if not isinstance(evidence, list):
        _issue(issues, "ARRAY_REQUIRED", "$.evidenceMap", "evidenceMap must be an array")
    else:
        for index, item in enumerate(evidence):
            path = f"$.evidenceMap[{index}]"
            record = _validate_required_mapping(item, path, ("sourceRef", "url", "title"), issues)
            if record is None:
                continue
            source_ref = record.get("sourceRef")
            if _validate_nonempty_string(source_ref, f"{path}.sourceRef", issues, pattern=_ID_PATTERN):
                if source_ref in evidence_ids:
                    _issue(issues, "SOURCE_REF_DUPLICATE", f"{path}.sourceRef", "sourceRef must be unique")
                evidence_ids.add(str(source_ref))
            url = record.get("url")
            if not isinstance(url, str) or not _HTTP_URL_PATTERN.match(url):
                _issue(issues, "SOURCE_URL_INVALID", f"{path}.url", "Evidence URL must use http or https")
            else:
                independence_key = _public_evidence_independence_key(url)
                if independence_key is None:
                    _issue(
                        issues,
                        "SOURCE_URL_NOT_PUBLIC",
                        f"{path}.url",
                        "Evidence URL must identify a public Internet source, not loopback/private/local infrastructure",
                    )
                else:
                    public_evidence_keys.add(independence_key)
            _validate_nonempty_string(record.get("title"), f"{path}.title", issues)
            if record.get("checkedAt") not in (None, "") and not _valid_iso_datetime(record.get("checkedAt")):
                _issue(issues, "CHECKED_AT_INVALID", f"{path}.checkedAt", "Evidence checkedAt must be ISO-8601 with timezone")

    bar = _validate_required_mapping(
        candidate.get("barSemantics"),
        "$.barSemantics",
        tuple(CLOSED_BAR_SEMANTICS),
        issues,
    )
    closed_bar = False
    if bar is not None:
        closed_bar = bar.get("evaluateOn") == "new_closed_bar"
        for key, expected in CLOSED_BAR_SEMANTICS.items():
            if bar.get(key) != expected:
                _issue(issues, "BAR_SEMANTICS_INVALID", f"$.barSemantics.{key}", f"Expected {expected!r}")

    scope = _validate_required_mapping(
        candidate.get("scope"),
        "$.scope",
        (
            "systemName",
            "strategyFamily",
            "platforms",
            "market",
            "symbols",
            "signalTimeframe",
            "executionTimeframe",
            "timezone",
            "sessions",
            "enabledSides",
            "suitableFor",
            "onePositionPerSymbol",
        ),
        issues,
    )
    enabled_sides: set[str] = set()
    if scope is not None:
        _validate_nonempty_string(scope.get("systemName"), "$.scope.systemName", issues)
        _validate_nonempty_string(scope.get("strategyFamily"), "$.scope.strategyFamily", issues)
        _validate_string_list(scope.get("platforms"), "$.scope.platforms", issues, min_items=1)
        _validate_nonempty_string(scope.get("market"), "$.scope.market", issues)
        _validate_string_list(scope.get("symbols"), "$.scope.symbols", issues, min_items=1)
        _validate_nonempty_string(scope.get("signalTimeframe"), "$.scope.signalTimeframe", issues)
        _validate_nonempty_string(scope.get("executionTimeframe"), "$.scope.executionTimeframe", issues)
        _validate_nonempty_string(scope.get("timezone"), "$.scope.timezone", issues)
        _validate_string_list(scope.get("sessions"), "$.scope.sessions", issues)
        enabled_sides = set(_validate_string_list(scope.get("enabledSides"), "$.scope.enabledSides", issues, min_items=1, enum=SIDES))
        _validate_string_list(scope.get("suitableFor"), "$.scope.suitableFor", issues)
        if not isinstance(scope.get("onePositionPerSymbol"), bool):
            _issue(issues, "BOOLEAN_REQUIRED", "$.scope.onePositionPerSymbol", "Expected a boolean")

    input_ids: set[str] = set()
    inputs = candidate.get("inputs")
    if not isinstance(inputs, list):
        _issue(issues, "ARRAY_REQUIRED", "$.inputs", "inputs must be an array")
    else:
        for index, item in enumerate(inputs):
            path = f"$.inputs[{index}]"
            record = _validate_required_mapping(
                item,
                path,
                ("inputId", "label", "type", "unit", "default", "optimizable", "sourceStatus", "sourceRefs", "usedByRuleIds"),
                issues,
            )
            if record is None:
                continue
            input_id = record.get("inputId")
            if _validate_nonempty_string(input_id, f"{path}.inputId", issues, pattern=_ID_PATTERN):
                if input_id in input_ids:
                    _issue(issues, "INPUT_ID_DUPLICATE", f"{path}.inputId", "inputId must be unique")
                input_ids.add(str(input_id))
            _validate_nonempty_string(record.get("label"), f"{path}.label", issues)
            if record.get("type") not in INPUT_TYPES:
                _issue(issues, "INPUT_TYPE_INVALID", f"{path}.type", f"Expected one of {sorted(INPUT_TYPES)}")
            _validate_nonempty_string(record.get("unit"), f"{path}.unit", issues)
            if not isinstance(record.get("optimizable"), bool):
                _issue(issues, "BOOLEAN_REQUIRED", f"{path}.optimizable", "Expected a boolean")
            if record.get("sourceStatus") not in SOURCE_STATUSES:
                _issue(issues, "SOURCE_STATUS_INVALID", f"{path}.sourceStatus", f"Expected one of {sorted(SOURCE_STATUSES)}")
            elif record.get("sourceStatus") == "unknown":
                pre_unresolved_reasons.append((path, "input value is unresolved"))
            if record.get("default") is None and record.get("sourceStatus") != "unknown":
                pre_unresolved_reasons.append((f"{path}.default", "input default is unresolved"))
            _validate_source_refs(record.get("sourceRefs"), f"{path}.sourceRefs", evidence_ids, issues, required=record.get("sourceStatus") == "verified_fact")
            _validate_string_list(record.get("usedByRuleIds"), f"{path}.usedByRuleIds", issues)
            _validate_input_default(record, path, issues)

    indicator_ids: set[str] = set()
    indicators = candidate.get("indicators")
    if not isinstance(indicators, list):
        _issue(issues, "ARRAY_REQUIRED", "$.indicators", "indicators must be an array")
    else:
        for index, item in enumerate(indicators):
            path = f"$.indicators[{index}]"
            record = _validate_required_mapping(
                item,
                path,
                ("indicatorId", "kind", "timeframe", "parameters", "appliedPrice", "outputLine", "sourceStatus", "sourceRefs"),
                issues,
            )
            if record is None:
                continue
            indicator_id = record.get("indicatorId")
            if _validate_nonempty_string(indicator_id, f"{path}.indicatorId", issues, pattern=_ID_PATTERN):
                if indicator_id in indicator_ids:
                    _issue(issues, "INDICATOR_ID_DUPLICATE", f"{path}.indicatorId", "indicatorId must be unique")
                indicator_ids.add(str(indicator_id))
            for key in ("kind", "timeframe", "appliedPrice", "outputLine"):
                _validate_nonempty_string(record.get(key), f"{path}.{key}", issues)
            if not isinstance(record.get("parameters"), Mapping):
                _issue(issues, "OBJECT_REQUIRED", f"{path}.parameters", "Indicator parameters must be an object")
            else:
                for parameter, parameter_value in record["parameters"].items():
                    if isinstance(parameter_value, Mapping) and "inputRef" in parameter_value:
                        ref = parameter_value.get("inputRef")
                        if ref not in input_ids:
                            _issue(issues, "INPUT_REF_UNDEFINED", f"{path}.parameters.{parameter}.inputRef", f"Unknown input reference {ref!r}")
            if record.get("sourceStatus") not in SOURCE_STATUSES:
                _issue(issues, "SOURCE_STATUS_INVALID", f"{path}.sourceStatus", f"Expected one of {sorted(SOURCE_STATUSES)}")
            elif record.get("sourceStatus") == "unknown":
                pre_unresolved_reasons.append((path, "indicator configuration is unresolved"))
            _validate_source_refs(record.get("sourceRefs"), f"{path}.sourceRefs", evidence_ids, issues, required=record.get("sourceStatus") == "verified_fact")

    for section in ("setup", "entry", "exit", "orderManagement"):
        if not isinstance(candidate.get(section), Mapping):
            _issue(issues, "OBJECT_REQUIRED", f"$.{section}", f"{section} must be an object")
    _validate_rule_lists(candidate.get("setup"), "$.setup", issues)
    _validate_rule_lists(candidate.get("entry"), "$.entry", issues)
    _validate_rule_lists(candidate.get("exit"), "$.exit", issues)
    _validate_rule_lists(candidate.get("orderManagement"), "$.orderManagement", issues)

    for lifecycle_section in ("entry", "exit"):
        section = candidate.get(lifecycle_section)
        if not isinstance(section, Mapping):
            continue
        for side in sorted(SIDES):
            side_path = f"$.{lifecycle_section}.{side}"
            side_record = _validate_required_mapping(section.get(side), side_path, ("enabled", "disabledReason", "rules"), issues)
            if side_record is None:
                continue
            if not isinstance(side_record.get("enabled"), bool):
                _issue(issues, "BOOLEAN_REQUIRED", f"{side_path}.enabled", "Expected a boolean")
            if side_record.get("enabled") is False and not isinstance(side_record.get("disabledReason"), str):
                _issue(issues, "DISABLED_REASON_REQUIRED", f"{side_path}.disabledReason", "Disabled side requires a reason string")
            if lifecycle_section == "entry" and ((side in enabled_sides) != (side_record.get("enabled") is True)):
                _issue(issues, "SIDE_ENABLEMENT_MISMATCH", f"{side_path}.enabled", "entry side must match scope.enabledSides")
            if lifecycle_section == "entry" and side_record.get("enabled") is True:
                if side_record.get("orderType") not in ENTRY_ORDER_TYPES:
                    _issue(issues, "ORDER_TYPE_INVALID", f"{side_path}.orderType", f"Expected one of {sorted(ENTRY_ORDER_TYPES)}")

    rule_ids: set[str] = set()
    rule_paths: dict[str, str] = {}
    unresolved_reasons: list[tuple[str, str]] = list(pre_unresolved_reasons)
    rule_records: list[tuple[str, Mapping[str, Any]]] = []
    for path, rule in _iter_rule_records(
        {
            "setup": candidate.get("setup"),
            "entry": candidate.get("entry"),
            "exit": candidate.get("exit"),
            "orderManagement": candidate.get("orderManagement"),
            "recovery": candidate.get("recovery"),
        }
    ):
        rule_records.append((path, rule))
        rule_id = rule.get("ruleId")
        if _validate_nonempty_string(rule_id, f"{path}.ruleId", issues, pattern=_RULE_ID_PATTERN):
            rule_id_text = str(rule_id)
            if rule_id_text in rule_ids:
                _issue(issues, "RULE_ID_DUPLICATE", f"{path}.ruleId", f"Duplicate ruleId {rule_id_text!r}")
            rule_ids.add(rule_id_text)
            rule_paths[rule_id_text] = path
        source_status = rule.get("sourceStatus")
        if source_status not in SOURCE_STATUSES:
            _issue(issues, "SOURCE_STATUS_INVALID", f"{path}.sourceStatus", f"Expected one of {sorted(SOURCE_STATUSES)}")
        _validate_source_refs(rule.get("sourceRefs"), f"{path}.sourceRefs", evidence_ids, issues, required=source_status == "verified_fact")
        if not isinstance(rule.get("enabled"), bool):
            _issue(issues, "BOOLEAN_REQUIRED", f"{path}.enabled", "Typed rule requires enabled boolean")
        if source_status == "unknown" or (isinstance(rule.get("expression"), Mapping) and rule["expression"].get("op") == "unknown"):
            unresolved_reasons.append((path, "rule is unresolved"))
        _validate_expression(
            rule.get("expression"),
            f"{path}.expression",
            issues,
            input_ids=input_ids,
            indicator_ids=indicator_ids,
            closed_bar=closed_bar,
        )

    for path, rule in rule_records:
        invalidation_refs = rule.get("invalidationRuleIds")
        if invalidation_refs is None:
            continue
        refs = _validate_string_list(
            invalidation_refs,
            f"{path}.invalidationRuleIds",
            issues,
        )
        for index, ref in enumerate(refs):
            if ref not in rule_ids:
                _issue(
                    issues,
                    "RULE_REF_UNDEFINED",
                    f"{path}.invalidationRuleIds[{index}]",
                    f"Unknown rule reference {ref!r}",
                )

    for side in sorted(enabled_sides):
        entry_side = candidate.get("entry", {}).get(side) if isinstance(candidate.get("entry"), Mapping) else None
        rules = entry_side.get("rules") if isinstance(entry_side, Mapping) else None
        if not isinstance(rules, list) or not rules:
            unresolved_reasons.append((f"$.entry.{side}.rules", "enabled entry side has no rules"))

    for index, item in enumerate(inputs if isinstance(inputs, list) else []):
        if not isinstance(item, Mapping):
            continue
        for ref_index, rule_ref in enumerate(item.get("usedByRuleIds") if isinstance(item.get("usedByRuleIds"), list) else []):
            if rule_ref not in rule_ids:
                # An unknown input may retain the source document's placeholder
                # link while the revision is explicitly blocked.  Verified,
                # derived, and assumed executable inputs remain strict.
                if item.get("sourceStatus") != "unknown":
                    _issue(issues, "RULE_REF_UNDEFINED", f"$.inputs[{index}].usedByRuleIds[{ref_index}]", f"Unknown rule reference {rule_ref!r}")

    tests = candidate.get("testCases")
    test_kinds: dict[str, set[str]] = {rule_id: set() for rule_id in rule_ids}
    if not isinstance(tests, list):
        _issue(issues, "ARRAY_REQUIRED", "$.testCases", "testCases must be an array")
    else:
        seen_cases: set[str] = set()
        for index, item in enumerate(tests):
            path = f"$.testCases[{index}]"
            record = _validate_required_mapping(item, path, ("caseId", "kind", "ruleIds", "given", "when", "expected"), issues)
            if record is None:
                continue
            case_id = record.get("caseId")
            if _validate_nonempty_string(case_id, f"{path}.caseId", issues, pattern=_ID_PATTERN):
                if case_id in seen_cases:
                    _issue(issues, "TEST_CASE_ID_DUPLICATE", f"{path}.caseId", "caseId must be unique")
                seen_cases.add(str(case_id))
            kind = record.get("kind")
            if kind not in {"positive", "negative", "boundary", "lifecycle"}:
                _issue(issues, "TEST_KIND_INVALID", f"{path}.kind", "Test kind must be positive, negative, boundary, or lifecycle")
            refs = _validate_string_list(record.get("ruleIds"), f"{path}.ruleIds", issues, min_items=1)
            for ref_index, ref in enumerate(refs):
                if ref not in rule_ids:
                    _issue(issues, "RULE_REF_UNDEFINED", f"{path}.ruleIds[{ref_index}]", f"Unknown rule reference {ref!r}")
                else:
                    test_kinds.setdefault(ref, set()).add(str(kind))
            for key in ("given", "when", "expected"):
                if not isinstance(record.get(key), (Mapping, list, str)):
                    _issue(issues, "TEST_PAYLOAD_INVALID", f"{path}.{key}", "Test payload must be an object, array, or string")

    for rule_path, rule in rule_records:
        rule_id = rule.get("ruleId")
        if rule.get("enabled") is not True or not isinstance(rule_id, str):
            continue
        observed = test_kinds.get(rule_id, set())
        phase = rule.get("phase")
        required_kinds = (
            {"positive", "negative"}
            if phase in {"setup", "entry", "exit", "safety"}
            else {"lifecycle"}
        )
        expression = rule.get("expression")
        if isinstance(expression, Mapping) and expression.get("op") in {"cross_above", "cross_below"}:
            required_kinds.add("boundary")
        missing = required_kinds - observed
        if missing:
            unresolved_reasons.append(
                (rule_path, f"rule {rule_id} lacks {', '.join(sorted(missing))} test coverage")
            )

    for key in ("tpSl", "riskAndSizing", "recovery", "execution", "pseudocode", "completeness"):
        if not isinstance(candidate.get(key), Mapping):
            _issue(issues, "OBJECT_REQUIRED", f"$.{key}", f"{key} must be an object")

    management = candidate.get("orderManagement")
    if isinstance(management, Mapping):
        for feature_name in (
            "breakEven",
            "trailingStop",
            "scaleIn",
            "scaleOut",
            "modifyStopLoss",
            "modifyTakeProfit",
            "pendingOrders",
        ):
            feature_path = f"$.orderManagement.{feature_name}"
            feature = _validate_required_mapping(
                management.get(feature_name),
                feature_path,
                ("enabled", "sourceStatus", "sourceRefs", "parameters", "rules"),
                issues,
            )
            if feature is None:
                continue
            if not isinstance(feature.get("enabled"), bool):
                _issue(issues, "BOOLEAN_REQUIRED", f"{feature_path}.enabled", "Expected a boolean")
            if feature.get("sourceStatus") not in SOURCE_STATUSES:
                _issue(issues, "SOURCE_STATUS_INVALID", f"{feature_path}.sourceStatus", f"Expected one of {sorted(SOURCE_STATUSES)}")
            _validate_source_refs(
                feature.get("sourceRefs"),
                f"{feature_path}.sourceRefs",
                evidence_ids,
                issues,
                required=feature.get("sourceStatus") == "verified_fact",
            )
            if feature.get("enabled") is True and feature.get("sourceStatus") == "unknown":
                unresolved_reasons.append((feature_path, f"enabled {feature_name} configuration is unresolved"))
            if not isinstance(feature.get("parameters"), Mapping):
                _issue(issues, "OBJECT_REQUIRED", f"{feature_path}.parameters", "Management parameters must be an object")
            if "cadence" in feature and feature.get("cadence") not in MANAGEMENT_CADENCES:
                _issue(
                    issues,
                    "MANAGEMENT_CADENCE_INVALID",
                    f"{feature_path}.cadence",
                    f"Expected one of {sorted(MANAGEMENT_CADENCES)}",
                )
            for boolean_field in ("onceOnly", "idempotent", "neverWorsenStop"):
                if boolean_field in feature and not isinstance(feature.get(boolean_field), bool):
                    _issue(
                        issues,
                        "BOOLEAN_REQUIRED",
                        f"{feature_path}.{boolean_field}",
                        "Expected a boolean",
                    )
            if "precedence" in feature and (
                not isinstance(feature.get("precedence"), int)
                or isinstance(feature.get("precedence"), bool)
                or feature.get("precedence", -1) < 0
            ):
                _issue(
                    issues,
                    "MANAGEMENT_PRECEDENCE_INVALID",
                    f"{feature_path}.precedence",
                    "precedence must be an integer >= 0",
                )
            if "action" in feature and not isinstance(feature.get("action"), Mapping):
                _issue(
                    issues,
                    "OBJECT_REQUIRED",
                    f"{feature_path}.action",
                    "Management action must be an object",
                )
            action = feature.get("action")
            if isinstance(action, Mapping):
                action_kind = action.get("kind")
                if action_kind not in MANAGEMENT_ACTION_KINDS:
                    _issue(
                        issues,
                        "MANAGEMENT_ACTION_KIND_INVALID",
                        f"{feature_path}.action.kind",
                        f"Expected one of {sorted(MANAGEMENT_ACTION_KINDS)}",
                    )
                elif action_kind not in MANAGEMENT_ACTIONS_BY_FEATURE[feature_name]:
                    _issue(
                        issues,
                        "MANAGEMENT_ACTION_FEATURE_MISMATCH",
                        f"{feature_path}.action.kind",
                        f"Action {action_kind!r} is not valid for {feature_name}",
                    )
            side_applicability = feature.get("sideApplicability")
            if side_applicability is not None:
                sides = _validate_string_list(
                    side_applicability,
                    f"{feature_path}.sideApplicability",
                    issues,
                )
                for index, side in enumerate(sides):
                    if side not in SIDES:
                        _issue(
                            issues,
                            "SIDE_INVALID",
                            f"{feature_path}.sideApplicability[{index}]",
                            f"Expected one of {sorted(SIDES)}",
                        )
            if isinstance(feature.get("trigger"), Mapping):
                _validate_expression(
                    feature.get("trigger"),
                    f"{feature_path}.trigger",
                    issues,
                    input_ids=input_ids,
                    indicator_ids=indicator_ids,
                    closed_bar=closed_bar,
                )
            if feature.get("enabled") is True:
                feature_rules = feature.get("rules")
                trigger = feature.get("trigger")
                if not isinstance(trigger, Mapping) or _expression_contains_unknown(trigger):
                    unresolved_reasons.append(
                        (f"{feature_path}.trigger", f"enabled {feature_name} requires a deterministic typed trigger")
                    )
                if not isinstance(action, Mapping) or action.get("kind") not in MANAGEMENT_ACTIONS_BY_FEATURE[feature_name]:
                    unresolved_reasons.append(
                        (f"{feature_path}.action", f"enabled {feature_name} requires an actionable typed action")
                    )
                parameters = feature.get("parameters")
                if not isinstance(parameters, Mapping) or not parameters:
                    unresolved_reasons.append(
                        (f"{feature_path}.parameters", f"enabled {feature_name} requires explicit non-empty parameters")
                    )
                enabled_feature_rules = [
                    rule
                    for rule in feature_rules
                    if isinstance(rule, Mapping) and rule.get("enabled") is True
                ] if isinstance(feature_rules, list) else []
                if not enabled_feature_rules:
                    unresolved_reasons.append(
                        (f"{feature_path}.rules", f"enabled {feature_name} requires at least one enabled typed rule")
                    )
                elif isinstance(trigger, Mapping) and not any(
                    _expressions_match(trigger, rule.get("expression"))
                    for rule in enabled_feature_rules
                ):
                    unresolved_reasons.append(
                        (f"{feature_path}.rules", f"enabled {feature_name} requires a rule whose expression matches its trigger")
                    )
                for rule in enabled_feature_rules:
                    rule_id = rule.get("ruleId")
                    if isinstance(rule_id, str) and "lifecycle" not in test_kinds.get(rule_id, set()):
                        unresolved_reasons.append(
                            (f"{feature_path}.rules", f"enabled {feature_name} rule {rule_id} requires lifecycle test coverage")
                        )
                for required_field in ("cadence", "idempotent", "precedence"):
                    if required_field not in feature:
                        unresolved_reasons.append(
                            (f"{feature_path}.{required_field}", f"enabled {feature_name} requires {required_field}")
                        )
                if feature.get("idempotent") is not True:
                    unresolved_reasons.append(
                        (f"{feature_path}.idempotent", f"enabled {feature_name} must be idempotent")
                    )
                if feature_name in {"breakEven", "trailingStop", "modifyStopLoss"} and feature.get("neverWorsenStop") is not True:
                    unresolved_reasons.append(
                        (f"{feature_path}.neverWorsenStop", f"enabled {feature_name} must never worsen the stop")
                    )

        partial_path = "$.orderManagement.partialClose"
        partial = _validate_required_mapping(
            management.get("partialClose"),
            partial_path,
            ("enabled", "sourceStatus", "sourceRefs", "steps", "rules"),
            issues,
        )
        if partial is not None:
            if not isinstance(partial.get("enabled"), bool):
                _issue(issues, "BOOLEAN_REQUIRED", f"{partial_path}.enabled", "Expected a boolean")
            if partial.get("sourceStatus") not in SOURCE_STATUSES:
                _issue(issues, "SOURCE_STATUS_INVALID", f"{partial_path}.sourceStatus", f"Expected one of {sorted(SOURCE_STATUSES)}")
            _validate_source_refs(
                partial.get("sourceRefs"),
                f"{partial_path}.sourceRefs",
                evidence_ids,
                issues,
                required=partial.get("sourceStatus") == "verified_fact",
            )
            steps = partial.get("steps")
            close_total = 0.0
            if not isinstance(steps, list):
                _issue(issues, "ARRAY_REQUIRED", f"{partial_path}.steps", "Partial-close steps must be an array")
            else:
                for index, step in enumerate(steps):
                    step_path = f"{partial_path}.steps[{index}]"
                    record = _validate_required_mapping(
                        step,
                        step_path,
                        ("stepId", "trigger", "closePercent", "onceOnly"),
                        issues,
                    )
                    if record is None:
                        continue
                    percent = record.get("closePercent")
                    if not isinstance(percent, (int, float)) or isinstance(percent, bool) or not math.isfinite(float(percent)) or not 0 < percent <= 100:
                        _issue(issues, "PARTIAL_PERCENT_INVALID", f"{step_path}.closePercent", "closePercent must be finite and in (0, 100]")
                    else:
                        close_total += float(percent)
                    if record.get("onceOnly") is not True:
                        _issue(issues, "PARTIAL_ONCE_REQUIRED", f"{step_path}.onceOnly", "Each partial-close step must execute once")
                    _validate_expression(
                        record.get("trigger"),
                        f"{step_path}.trigger",
                        issues,
                        input_ids=input_ids,
                        indicator_ids=indicator_ids,
                        closed_bar=closed_bar,
                    )
            if close_total > 100.0:
                _issue(issues, "PARTIAL_TOTAL_INVALID", f"{partial_path}.steps", "Partial-close percentages cannot exceed 100")
            if partial.get("enabled") is True and partial.get("sourceStatus") == "unknown":
                unresolved_reasons.append((partial_path, "enabled partial-close configuration is unresolved"))
            if partial.get("enabled") is True:
                if not isinstance(steps, list) or not steps:
                    unresolved_reasons.append((f"{partial_path}.steps", "enabled partialClose requires at least one deterministic close step"))
                elif any(
                    not isinstance(step, Mapping)
                    or not isinstance(step.get("trigger"), Mapping)
                    or _expression_contains_unknown(step.get("trigger"))
                    for step in steps
                ):
                    unresolved_reasons.append((f"{partial_path}.steps", "enabled partialClose contains a non-deterministic step trigger"))
                partial_rules = partial.get("rules")
                enabled_partial_rules = [
                    rule
                    for rule in partial_rules
                    if isinstance(rule, Mapping) and rule.get("enabled") is True
                ] if isinstance(partial_rules, list) else []
                if not enabled_partial_rules:
                    unresolved_reasons.append((f"{partial_path}.rules", "enabled partialClose requires at least one enabled typed rule"))
                else:
                    step_triggers = [
                        step.get("trigger")
                        for step in steps
                        if isinstance(step, Mapping) and isinstance(step.get("trigger"), Mapping)
                    ] if isinstance(steps, list) else []
                    if step_triggers and not all(
                        any(_expressions_match(trigger, rule.get("expression")) for rule in enabled_partial_rules)
                        for trigger in step_triggers
                    ):
                        unresolved_reasons.append((f"{partial_path}.rules", "each partialClose step trigger requires a matching typed rule"))
                    for rule in enabled_partial_rules:
                        rule_id = rule.get("ruleId")
                        if isinstance(rule_id, str) and "lifecycle" not in test_kinds.get(rule_id, set()):
                            unresolved_reasons.append((f"{partial_path}.rules", f"partialClose rule {rule_id} requires lifecycle test coverage"))

    tp_sl = candidate.get("tpSl")
    if isinstance(tp_sl, Mapping):
        protection_records: list[tuple[str, str, Mapping[str, Any]]] = []
        for name in ("stopLoss", "takeProfit"):
            raw_record = tp_sl.get(name)
            if isinstance(raw_record, Mapping):
                protection_records.append((f"$.tpSl.{name}", name, raw_record))
            else:
                _issue(issues, "OBJECT_REQUIRED", f"$.tpSl.{name}", "Protection rule must be an object")
        side_overrides = _validate_required_mapping(
            tp_sl.get("sideOverrides"),
            "$.tpSl.sideOverrides",
            ("buy", "sell"),
            issues,
        )
        if side_overrides is not None:
            for side in sorted(SIDES):
                side_record = side_overrides.get(side)
                if not isinstance(side_record, Mapping):
                    _issue(
                        issues,
                        "OBJECT_REQUIRED",
                        f"$.tpSl.sideOverrides.{side}",
                        "Side protection override must be an object",
                    )
                    continue
                for name in ("stopLoss", "takeProfit"):
                    raw_record = side_record.get(name)
                    if raw_record is not None:
                        if isinstance(raw_record, Mapping):
                            protection_records.append(
                                (f"$.tpSl.sideOverrides.{side}.{name}", name, raw_record)
                            )
                        else:
                            _issue(
                                issues,
                                "OBJECT_REQUIRED",
                                f"$.tpSl.sideOverrides.{side}.{name}",
                                "Protection override must be an object",
                            )

        input_records_by_id = {
            str(item.get("inputId")): item
            for item in candidate.get("inputs", [])
            if isinstance(item, Mapping) and isinstance(item.get("inputId"), str)
        }
        indicator_records_by_id = {
            str(item.get("indicatorId")): item
            for item in candidate.get("indicators", [])
            if isinstance(item, Mapping) and isinstance(item.get("indicatorId"), str)
        }

        for path, name, raw_record in protection_records:
            record = _validate_required_mapping(
                raw_record,
                path,
                ("enabled", "type", "sourceStatus", "sourceRefs"),
                issues,
            )
            if record is None:
                continue
            if not isinstance(record.get("enabled"), bool):
                _issue(issues, "BOOLEAN_REQUIRED", f"{path}.enabled", "Expected a boolean")
            if record.get("type") not in PROTECTION_TYPES:
                _issue(
                    issues,
                    "PROTECTION_TYPE_INVALID",
                    f"{path}.type",
                    f"Expected one of {sorted(PROTECTION_TYPES)}",
                )
            if "reference" in record and record.get("reference") not in PROTECTION_REFERENCES:
                _issue(
                    issues,
                    "PROTECTION_REFERENCE_INVALID",
                    f"{path}.reference",
                    f"Expected one of {sorted(PROTECTION_REFERENCES)}",
                )
            if "unit" in record and record.get("unit") not in PROTECTION_UNITS:
                _issue(
                    issues,
                    "PROTECTION_UNIT_INVALID",
                    f"{path}.unit",
                    f"Expected one of {sorted(PROTECTION_UNITS)}",
                )
            if "rrRiskReference" in record and record.get("rrRiskReference") not in RR_RISK_REFERENCES:
                _issue(
                    issues,
                    "RR_RISK_REFERENCE_INVALID",
                    f"{path}.rrRiskReference",
                    f"Expected one of {sorted(RR_RISK_REFERENCES)}",
                )
            if "basketPriceField" in record and record.get("basketPriceField") not in PROTECTION_BASKET_PRICE_FIELDS:
                _issue(
                    issues,
                    "BASKET_PRICE_FIELD_INVALID",
                    f"{path}.basketPriceField",
                    f"Expected one of {sorted(PROTECTION_BASKET_PRICE_FIELDS)}",
                )
            if "basketScope" in record and record.get("basketScope") not in PROTECTION_BASKET_SCOPES:
                _issue(
                    issues,
                    "BASKET_SCOPE_INVALID",
                    f"{path}.basketScope",
                    f"Expected one of {sorted(PROTECTION_BASKET_SCOPES)}",
                )
            if "placementTiming" in record and record.get("placementTiming") not in PROTECTION_PLACEMENT_TIMINGS:
                _issue(
                    issues,
                    "PROTECTION_PLACEMENT_INVALID",
                    f"{path}.placementTiming",
                    f"Expected one of {sorted(PROTECTION_PLACEMENT_TIMINGS)}",
                )
            if "minimumStopDistancePolicy" in record and record.get("minimumStopDistancePolicy") not in MINIMUM_STOP_POLICIES:
                _issue(
                    issues,
                    "MINIMUM_STOP_POLICY_INVALID",
                    f"{path}.minimumStopDistancePolicy",
                    f"Expected one of {sorted(MINIMUM_STOP_POLICIES)}",
                )
            if "freezeLevelPolicy" in record and record.get("freezeLevelPolicy") not in FREEZE_LEVEL_POLICIES:
                _issue(
                    issues,
                    "FREEZE_LEVEL_POLICY_INVALID",
                    f"{path}.freezeLevelPolicy",
                    f"Expected one of {sorted(FREEZE_LEVEL_POLICIES)}",
                )
            if "neverWorsen" in record and not isinstance(record.get("neverWorsen"), bool):
                _issue(issues, "BOOLEAN_REQUIRED", f"{path}.neverWorsen", "Expected a boolean")
            for numeric_field in ("value", "rrMultiple"):
                numeric_value = record.get(numeric_field)
                if numeric_value is not None and (
                    not isinstance(numeric_value, (int, float))
                    or isinstance(numeric_value, bool)
                    or not math.isfinite(float(numeric_value))
                    or float(numeric_value) <= 0
                ):
                    _issue(
                        issues,
                        "PROTECTION_VALUE_INVALID",
                        f"{path}.{numeric_field}",
                        f"{numeric_field} must be finite and greater than zero",
                    )
            buffer_value = record.get("bufferValue")
            if buffer_value is not None and (
                not isinstance(buffer_value, (int, float))
                or isinstance(buffer_value, bool)
                or not math.isfinite(float(buffer_value))
                or float(buffer_value) < 0
            ):
                _issue(
                    issues,
                    "PROTECTION_BUFFER_INVALID",
                    f"{path}.bufferValue",
                    "bufferValue must be finite and zero or greater",
                )
            for integer_field, minimum, maximum in (
                ("lookbackBars", 1, None),
                ("swingShift", 1, None),
                ("indicatorShift", 1, None),
                ("freezeRetryLimit", 1, 100),
                ("freezeRetryDelayMs", 1, 60000),
            ):
                integer_value = record.get(integer_field)
                if integer_value is not None and (
                    not isinstance(integer_value, int)
                    or isinstance(integer_value, bool)
                    or integer_value < minimum
                    or (maximum is not None and integer_value > maximum)
                ):
                    _issue(
                        issues,
                        "PROTECTION_INTEGER_INVALID",
                        f"{path}.{integer_field}",
                        f"{integer_field} must be an integer in the supported range",
                    )
            if record.get("sourceStatus") not in SOURCE_STATUSES:
                _issue(issues, "SOURCE_STATUS_INVALID", f"{path}.sourceStatus", f"Expected one of {sorted(SOURCE_STATUSES)}")
            _validate_source_refs(
                record.get("sourceRefs"),
                f"{path}.sourceRefs",
                evidence_ids,
                issues,
                required=record.get("sourceStatus") in {"verified_fact", "derived_expansion"},
            )
            for ref_field in ("valueInputRef", "rrMultipleInputRef", "lookbackInputRef", "bufferInputRef"):
                _validate_defined_ref(record, ref_field, path, input_ids, issues)
            for ref_field in ("atrIndicatorRef", "indicatorRef"):
                _validate_defined_ref(
                    record,
                    ref_field,
                    path,
                    indicator_ids,
                    issues,
                    code="INDICATOR_REF_UNDEFINED",
                )
            for ref_field, integer, allow_zero in (
                ("valueInputRef", False, False),
                ("rrMultipleInputRef", False, False),
                ("lookbackInputRef", True, False),
                ("bufferInputRef", False, True),
            ):
                if _field_has_value(record, ref_field):
                    _validate_numeric_protection_input(
                        record.get(ref_field),
                        f"{path}.{ref_field}",
                        input_records_by_id,
                        issues,
                        integer=integer,
                        allow_zero=allow_zero,
                    )
            enabled = record.get("enabled") is True
            protection_type = record.get("type")
            if enabled and protection_type == "none":
                _issue(issues, "PROTECTION_ENABLEMENT_MISMATCH", f"{path}.type", "Enabled protection cannot use type none")
            if not enabled and protection_type != "none":
                _issue(issues, "PROTECTION_ENABLEMENT_MISMATCH", f"{path}.type", "Disabled protection must use type none")

            method_fields = {
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
            allowed_method_fields = {
                "none": set(),
                "fixed_points": {"value", "valueInputRef"},
                "fixed_pips": {"value", "valueInputRef"},
                "percent": {"value", "valueInputRef"},
                "atr": {"value", "valueInputRef", "atrIndicatorRef"},
                "rr": {"rrMultiple", "rrMultipleInputRef", "rrRiskReference"},
                "swing": {"lookbackBars", "lookbackInputRef", "swingShift", "indicatorRef", "indicatorShift", "bufferValue", "bufferInputRef", "formula"},
                "indicator": {"indicatorRef", "indicatorShift", "bufferValue", "bufferInputRef", "formula"},
                "basket": {"value", "valueInputRef", "basketPriceField", "basketScope", "formula"},
            }.get(str(protection_type), set())
            for field in sorted(method_fields - allowed_method_fields):
                if _field_has_value(record, field):
                    _issue(
                        issues,
                        "PROTECTION_FIELD_INCOMPATIBLE",
                        f"{path}.{field}",
                        f"Field {field!r} is not valid for protection type {protection_type!r}",
                    )

            value_source_count = sum(_field_has_value(record, field) for field in ("value", "valueInputRef"))
            rr_source_count = sum(_field_has_value(record, field) for field in ("rrMultiple", "rrMultipleInputRef"))
            lookback_source_count = sum(_field_has_value(record, field) for field in ("lookbackBars", "lookbackInputRef"))
            buffer_source_count = sum(_field_has_value(record, field) for field in ("bufferValue", "bufferInputRef"))
            formula_present = _field_has_value(record, "formula")
            if value_source_count > 1:
                _issue(issues, "PROTECTION_VALUE_AMBIGUOUS", path, "Use exactly one of value or valueInputRef")
            if rr_source_count > 1:
                _issue(issues, "RR_MULTIPLE_AMBIGUOUS", path, "Use exactly one of rrMultiple or rrMultipleInputRef")
            if lookback_source_count > 1:
                _issue(issues, "SWING_LOOKBACK_AMBIGUOUS", path, "Use exactly one of lookbackBars or lookbackInputRef")
            if buffer_source_count > 1:
                _issue(issues, "PROTECTION_BUFFER_AMBIGUOUS", path, "Use at most one of bufferValue or bufferInputRef")

            expected_unit = {
                "fixed_points": "point",
                "fixed_pips": "pip",
                "percent": "percent",
                "atr": "atr_multiple",
                "rr": "risk_multiple",
                "swing": "price",
                "indicator": "price",
            }.get(str(protection_type))
            if enabled and expected_unit is not None and record.get("unit") != expected_unit:
                _issue(
                    issues,
                    "PROTECTION_UNIT_MISMATCH",
                    f"{path}.unit",
                    f"Protection type {protection_type!r} requires unit {expected_unit!r}",
                )
            expected_reference = {
                "fixed_points": "entry_price",
                "fixed_pips": "entry_price",
                "percent": "entry_price",
                "atr": "entry_price",
                "rr": "entry_price",
                "indicator": "indicator_value",
                "basket": "basket_price",
            }.get(str(protection_type))
            if enabled and expected_reference is not None and record.get("reference") != expected_reference:
                _issue(
                    issues,
                    "PROTECTION_REFERENCE_MISMATCH",
                    f"{path}.reference",
                    f"Protection type {protection_type!r} requires reference {expected_reference!r}",
                )

            if enabled and protection_type in {"fixed_points", "fixed_pips", "percent", "atr"} and value_source_count == 0:
                unresolved_reasons.append((path, f"enabled {protection_type} {name} requires exactly one value or valueInputRef"))
            if enabled and protection_type == "atr":
                atr_ref = record.get("atrIndicatorRef")
                if atr_ref in (None, ""):
                    unresolved_reasons.append((path, f"ATR {name} requires atrIndicatorRef"))
                elif atr_ref in indicator_records_by_id:
                    indicator_kind = re.sub(
                        r"[^a-z0-9]+",
                        "",
                        str(indicator_records_by_id[str(atr_ref)].get("kind") or "").lower(),
                    )
                    if indicator_kind not in {"atr", "averagetruerange"}:
                        _issue(
                            issues,
                            "ATR_INDICATOR_KIND_INVALID",
                            f"{path}.atrIndicatorRef",
                            "ATR protection must reference an ATR indicator definition",
                        )
            if enabled and protection_type == "rr":
                if rr_source_count == 0:
                    unresolved_reasons.append((path, f"RR {name} requires exactly one rrMultiple or rrMultipleInputRef"))
                if record.get("rrRiskReference") not in RR_RISK_REFERENCES:
                    unresolved_reasons.append((f"{path}.rrRiskReference", "RR protection requires initial_stop_loss_distance"))
                if name == "stopLoss":
                    _issue(issues, "RR_STOP_LOSS_FORBIDDEN", f"{path}.type", "RR is a take-profit method and cannot define stopLoss")
            if enabled and protection_type == "swing":
                indicator_source = _field_has_value(record, "indicatorRef")
                if lookback_source_count == 0 and not indicator_source:
                    unresolved_reasons.append((path, f"swing {name} requires a typed lookback or indicator source"))
                elif lookback_source_count > 0 and indicator_source:
                    _issue(issues, "SWING_SOURCE_AMBIGUOUS", path, "Use either an OHLC lookback or an indicator source for swing protection")
                if lookback_source_count > 0 and (
                    not isinstance(record.get("swingShift"), int)
                    or isinstance(record.get("swingShift"), bool)
                    or record.get("swingShift", 0) < 1
                ):
                    unresolved_reasons.append((f"{path}.swingShift", f"swing {name} lookback requires a confirmed closed-bar shift >= 1"))
                if indicator_source and (
                    not isinstance(record.get("indicatorShift"), int)
                    or isinstance(record.get("indicatorShift"), bool)
                    or record.get("indicatorShift", 0) < 1
                ):
                    unresolved_reasons.append((f"{path}.indicatorShift", f"swing {name} indicator requires a confirmed closed-bar shift >= 1"))
            if enabled and protection_type == "indicator":
                if record.get("indicatorRef") in (None, ""):
                    unresolved_reasons.append((path, f"indicator {name} requires indicatorRef"))
                if not isinstance(record.get("indicatorShift"), int) or isinstance(record.get("indicatorShift"), bool) or record.get("indicatorShift", 0) < 1:
                    unresolved_reasons.append((f"{path}.indicatorShift", f"indicator {name} requires a confirmed closed-bar shift >= 1"))
            if enabled and protection_type == "basket":
                target_count = value_source_count + int(formula_present)
                if target_count == 0:
                    unresolved_reasons.append((path, f"basket {name} requires exactly one value, valueInputRef, or formula"))
                elif target_count > 1:
                    _issue(issues, "BASKET_TARGET_AMBIGUOUS", path, "Use exactly one basket value, valueInputRef, or formula")
                if record.get("basketPriceField") not in PROTECTION_BASKET_PRICE_FIELDS:
                    unresolved_reasons.append((f"{path}.basketPriceField", "basket protection requires a typed basket price field"))
                if record.get("basketScope") not in PROTECTION_BASKET_SCOPES:
                    unresolved_reasons.append((f"{path}.basketScope", "basket protection requires symbol_magic_side scope"))
                if record.get("placementTiming") == "with_entry":
                    _issue(issues, "BASKET_PLACEMENT_INVALID", f"{path}.placementTiming", "Basket price does not exist before the first fill")
                if formula_present and record.get("unit") != "price":
                    _issue(issues, "PROTECTION_UNIT_MISMATCH", f"{path}.unit", "Basket formula target requires price unit")
                elif not formula_present and record.get("unit") not in {"point", "pip", "percent", "price"}:
                    _issue(issues, "PROTECTION_UNIT_MISMATCH", f"{path}.unit", "Basket value target requires point, pip, percent, or price unit")

            if enabled and record.get("reference") in (None, ""):
                unresolved_reasons.append((f"{path}.reference", f"enabled {name} requires reference"))
            if enabled and record.get("unit") in (None, ""):
                unresolved_reasons.append((f"{path}.unit", f"enabled {name} requires unit"))
            formula_price_refs: set[str] = set()
            formula_indicator_refs: set[str] = set()
            if formula_present:
                formula_unit = _validate_price_formula(
                    record.get("formula"),
                    f"{path}.formula",
                    issues,
                    input_records=input_records_by_id,
                    indicator_records=indicator_records_by_id,
                    referenced_prices=formula_price_refs,
                    referenced_indicators=formula_indicator_refs,
                )
                if formula_unit is not None and formula_unit != "price":
                    _issue(issues, "PRICE_FORMULA_RESULT_INVALID", f"{path}.formula", "Protection price formula must resolve to an absolute price")
                if (
                    protection_type == "swing"
                    and record.get("reference") not in formula_price_refs
                    and record.get("indicatorRef") not in formula_indicator_refs
                ):
                    _issue(issues, "SWING_FORMULA_SOURCE_MISSING", f"{path}.formula", "Swing formula must consume its declared swing or indicator source")
                if protection_type == "indicator" and record.get("indicatorRef") not in formula_indicator_refs:
                    _issue(issues, "INDICATOR_FORMULA_SOURCE_MISSING", f"{path}.formula", "Indicator formula must consume its declared indicatorRef")
                if protection_type == "basket" and "basket_price" not in formula_price_refs:
                    _issue(issues, "BASKET_FORMULA_SOURCE_MISSING", f"{path}.formula", "Basket formula must consume basket_price")
            for ref_key in ("activationRuleIds", "invalidationRuleIds"):
                refs = record.get(ref_key)
                if refs is None:
                    continue
                for index, ref in enumerate(
                    _validate_string_list(refs, f"{path}.{ref_key}", issues)
                ):
                    if ref not in rule_ids:
                        _issue(
                            issues,
                            "RULE_REF_UNDEFINED",
                            f"{path}.{ref_key}[{index}]",
                            f"Unknown rule reference {ref!r}",
                        )
            if enabled:
                for required_field in (
                    "placementTiming",
                    "minimumStopDistancePolicy",
                    "freezeLevelPolicy",
                ):
                    if required_field not in record:
                        unresolved_reasons.append(
                            (f"{path}.{required_field}", f"enabled {name} requires {required_field}")
                        )
                if record.get("placementTiming") == "on_trigger" and not record.get("activationRuleIds"):
                    unresolved_reasons.append(
                        (f"{path}.activationRuleIds", "on_trigger protection requires at least one activation rule")
                    )
                if record.get("freezeLevelPolicy") == "retry_bounded":
                    for retry_field in ("freezeRetryLimit", "freezeRetryDelayMs"):
                        if not _field_has_value(record, retry_field):
                            unresolved_reasons.append(
                                (f"{path}.{retry_field}", f"retry_bounded requires {retry_field}")
                            )
                else:
                    for retry_field in ("freezeRetryLimit", "freezeRetryDelayMs"):
                        if _field_has_value(record, retry_field):
                            _issue(
                                issues,
                                "PROTECTION_RETRY_FIELD_INCOMPATIBLE",
                                f"{path}.{retry_field}",
                                f"{retry_field} is valid only with freezeLevelPolicy retry_bounded",
                            )
                if name == "stopLoss" and record.get("neverWorsen") is not True:
                    unresolved_reasons.append(
                        (f"{path}.neverWorsen", "enabled stopLoss must never move farther from safety")
                    )
            if enabled and record.get("sourceStatus") == "unknown":
                unresolved_reasons.append((path, f"enabled {name} is unresolved"))

        if side_overrides is not None:
            defaults = {
                name: tp_sl.get(name)
                for name in ("stopLoss", "takeProfit")
                if isinstance(tp_sl.get(name), Mapping)
            }
            for side in sorted(enabled_sides):
                override_group = side_overrides.get(side)
                effective: dict[str, tuple[str, Mapping[str, Any]]] = {}
                for name in ("stopLoss", "takeProfit"):
                    override = override_group.get(name) if isinstance(override_group, Mapping) else None
                    if isinstance(override, Mapping):
                        effective[name] = (f"$.tpSl.sideOverrides.{side}.{name}", override)
                    elif isinstance(defaults.get(name), Mapping):
                        effective[name] = (f"$.tpSl.{name}", defaults[name])

                for name, (path, record) in effective.items():
                    if record.get("enabled") is not True or record.get("type") != "swing":
                        continue
                    expected_swing_reference = {
                        ("buy", "stopLoss"): "swing_low",
                        ("buy", "takeProfit"): "swing_high",
                        ("sell", "stopLoss"): "swing_high",
                        ("sell", "takeProfit"): "swing_low",
                    }[(side, name)]
                    if record.get("reference") != expected_swing_reference:
                        _issue(
                            issues,
                            "SWING_REFERENCE_DIRECTION_INVALID",
                            f"{path}.reference",
                            f"{side} {name} must reference {expected_swing_reference}",
                        )

                take_profit_path, effective_take_profit = effective.get("takeProfit", ("", {}))
                if effective_take_profit.get("enabled") is True and effective_take_profit.get("type") == "rr":
                    stop_path, effective_stop = effective.get("stopLoss", ("$.tpSl.stopLoss", {}))
                    if (
                        effective_stop.get("enabled") is not True
                        or effective_stop.get("type") in {None, "none", "rr", "basket"}
                    ):
                        _issue(
                            issues,
                            "RR_STOP_REFERENCE_INVALID",
                            f"{take_profit_path}.rrRiskReference",
                            f"RR takeProfit for {side} requires an enabled non-RR, non-basket effective stopLoss; found {stop_path}",
                        )

    risk = candidate.get("riskAndSizing")
    if isinstance(risk, Mapping):
        lot_mode = risk.get("lotMode")
        if lot_mode not in LOT_MODES:
            _issue(issues, "LOT_MODE_INVALID", "$.riskAndSizing.lotMode", f"Expected one of {sorted(LOT_MODES)}")
        if not isinstance(risk.get("maxOpenPositions"), int) or isinstance(risk.get("maxOpenPositions"), bool) or risk.get("maxOpenPositions", 0) < 1:
            _issue(issues, "MAX_OPEN_POSITIONS_INVALID", "$.riskAndSizing.maxOpenPositions", "maxOpenPositions must be an integer >= 1")
        _validate_defined_ref(
            risk,
            "fixedLotInputRef",
            "$.riskAndSizing",
            input_ids,
            issues,
            required=lot_mode == "fixed_lot",
        )
        _validate_defined_ref(
            risk,
            "riskPercentInputRef",
            "$.riskAndSizing",
            input_ids,
            issues,
            required=lot_mode in {"fixed_fractional_balance", "fixed_fractional_equity", "free_margin_fraction"},
        )
        if lot_mode in {"fixed_fractional_balance", "fixed_fractional_equity", "free_margin_fraction"}:
            for side in sorted(enabled_sides):
                default_stop = tp_sl.get("stopLoss") if isinstance(tp_sl, Mapping) else None
                side_overrides = tp_sl.get("sideOverrides") if isinstance(tp_sl, Mapping) else None
                side_record = side_overrides.get(side) if isinstance(side_overrides, Mapping) else None
                side_stop = side_record.get("stopLoss") if isinstance(side_record, Mapping) else None
                effective_stop = side_stop if isinstance(side_stop, Mapping) else default_stop
                if not isinstance(effective_stop, Mapping) or effective_stop.get("enabled") is not True:
                    unresolved_reasons.append(
                        (f"$.riskAndSizing.lotMode", f"risk-percent sizing for {side} requires a deterministic stop distance")
                    )
        if lot_mode == "sequence":
            lot_sequence = risk.get("lotSequence")
            if not isinstance(lot_sequence, list) or not lot_sequence:
                unresolved_reasons.append(("$.riskAndSizing.lotSequence", "sequence lotMode requires a non-empty lotSequence"))
            elif any(not _is_positive_finite(value) for value in lot_sequence):
                _issue(issues, "LOT_SEQUENCE_INVALID", "$.riskAndSizing.lotSequence", "Every lotSequence value must be finite and greater than zero")

    recovery = candidate.get("recovery")
    if isinstance(recovery, Mapping):
        mode = recovery.get("mode")
        if mode not in RECOVERY_MODES:
            _issue(issues, "RECOVERY_MODE_INVALID", "$.recovery.mode", f"Expected one of {sorted(RECOVERY_MODES)}")
        enabled = recovery.get("enabled")
        if not isinstance(enabled, bool):
            _issue(issues, "BOOLEAN_REQUIRED", "$.recovery.enabled", "Expected a boolean")
        if mode == "none" and enabled is not False:
            _issue(issues, "RECOVERY_ENABLEMENT_MISMATCH", "$.recovery.enabled", "mode none requires enabled=false")
        if mode != "none" and enabled is not True:
            _issue(issues, "RECOVERY_ENABLEMENT_MISMATCH", "$.recovery.enabled", "Active recovery mode requires enabled=true")
        if recovery.get("sourceStatus") not in SOURCE_STATUSES:
            _issue(issues, "SOURCE_STATUS_INVALID", "$.recovery.sourceStatus", f"Expected one of {sorted(SOURCE_STATUSES)}")
        _validate_source_refs(
            recovery.get("sourceRefs"),
            "$.recovery.sourceRefs",
            evidence_ids,
            issues,
            required=recovery.get("sourceStatus") == "verified_fact",
        )
        if isinstance(recovery.get("trigger"), Mapping):
            _validate_expression(
                recovery.get("trigger"),
                "$.recovery.trigger",
                issues,
                input_ids=input_ids,
                indicator_ids=indicator_ids,
                closed_bar=closed_bar,
            )
            if _recovery_expression_is_unknown(recovery.get("trigger")):
                unresolved_reasons.append(("$.recovery.trigger", "active recovery trigger is unknown"))
        if isinstance(recovery.get("resetCondition"), Mapping):
            _validate_expression(
                recovery.get("resetCondition"),
                "$.recovery.resetCondition",
                issues,
                input_ids=input_ids,
                indicator_ids=indicator_ids,
                closed_bar=closed_bar,
            )
            if _recovery_expression_is_unknown(recovery.get("resetCondition")):
                unresolved_reasons.append(("$.recovery.resetCondition", "recovery reset condition is unknown"))
        if isinstance(recovery.get("abortCondition"), Mapping):
            _validate_expression(
                recovery.get("abortCondition"),
                "$.recovery.abortCondition",
                issues,
                input_ids=input_ids,
                indicator_ids=indicator_ids,
                closed_bar=closed_bar,
            )
            if _recovery_expression_is_unknown(recovery.get("abortCondition")):
                unresolved_reasons.append(("$.recovery.abortCondition", "recovery abort condition is unknown"))
        if enabled is True and recovery.get("sourceStatus") == "unknown":
            unresolved_reasons.append(("$.recovery", "enabled recovery configuration is unresolved"))
        if mode in {"grid", "martingale", "averaging", "hedging"}:
            for field in (
                "trigger",
                "spacing",
                "direction",
                "maxLevels",
                "lotFormula",
                "lotCap",
                "basketTakeProfit",
                "basketStopLoss",
                "equityStopPercent",
                "maxBasketLots",
                "maxDrawdownPercent",
                "reentryPolicy",
                "resetCondition",
                "abortCondition",
                "levelRules",
            ):
                if field not in recovery or recovery.get(field) in (None, "", []):
                    unresolved_reasons.append((f"$.recovery.{field}", f"{mode} requires {field}"))
            _validate_recovery_spacing(
                recovery.get("spacing"),
                "$.recovery.spacing",
                input_ids=input_ids,
                indicator_ids=indicator_ids,
                evidence_ids=evidence_ids,
                issues=issues,
                unresolved_reasons=unresolved_reasons,
            )
            lot_formula = _validate_recovery_lot_formula(
                recovery.get("lotFormula"),
                "$.recovery.lotFormula",
                input_ids=input_ids,
                evidence_ids=evidence_ids,
                issues=issues,
                unresolved_reasons=unresolved_reasons,
            )
            _validate_basket_threshold(
                recovery.get("basketTakeProfit"),
                "$.recovery.basketTakeProfit",
                input_ids=input_ids,
                evidence_ids=evidence_ids,
                issues=issues,
                unresolved_reasons=unresolved_reasons,
            )
            _validate_basket_threshold(
                recovery.get("basketStopLoss"),
                "$.recovery.basketStopLoss",
                input_ids=input_ids,
                evidence_ids=evidence_ids,
                issues=issues,
                unresolved_reasons=unresolved_reasons,
            )
            for field in ("resetCondition", "abortCondition"):
                if not isinstance(recovery.get(field), Mapping):
                    unresolved_reasons.append(
                        (f"$.recovery.{field}", f"{mode} requires a typed {field} expression")
                    )
            max_levels = recovery.get("maxLevels")
            if max_levels not in (None, "") and (not isinstance(max_levels, int) or isinstance(max_levels, bool) or max_levels < 1):
                _issue(issues, "RECOVERY_MAX_LEVELS_INVALID", "$.recovery.maxLevels", "maxLevels must be an integer >= 1")
            for field in ("lotCap", "equityStopPercent", "maxBasketLots", "maxDrawdownPercent"):
                value = recovery.get(field)
                if value not in (None, "") and not _is_positive_finite(value):
                    _issue(issues, "RECOVERY_LIMIT_INVALID", f"$.recovery.{field}", f"{field} must be finite and greater than zero")
            for field in ("equityStopPercent", "maxDrawdownPercent"):
                value = recovery.get(field)
                if _is_positive_finite(value) and float(value) > 100:
                    _issue(issues, "RECOVERY_PERCENT_INVALID", f"$.recovery.{field}", f"{field} cannot exceed 100 percent")
            if _is_positive_finite(recovery.get("lotCap")) and _is_positive_finite(recovery.get("maxBasketLots")) and float(recovery["lotCap"]) > float(recovery["maxBasketLots"]):
                _issue(issues, "RECOVERY_CAP_ORDER_INVALID", "$.recovery.lotCap", "Per-level lotCap cannot exceed maxBasketLots")

            level_rules = recovery.get("levelRules")
            enabled_recovery_rules = [
                rule
                for rule in level_rules
                if isinstance(rule, Mapping)
                and rule.get("enabled") is True
                and rule.get("phase") == "recovery"
            ] if isinstance(level_rules, list) else []
            if not enabled_recovery_rules:
                unresolved_reasons.append(("$.recovery.levelRules", f"{mode} requires at least one enabled recovery-phase rule"))
            if isinstance(level_rules, list):
                for index, rule in enumerate(level_rules):
                    if isinstance(rule, Mapping) and rule.get("phase") != "recovery":
                        _issue(issues, "RECOVERY_RULE_PHASE_INVALID", f"$.recovery.levelRules[{index}].phase", "levelRules must use phase recovery")

            if mode == "martingale" and isinstance(lot_formula, Mapping):
                lot_mode = lot_formula.get("mode")
                if lot_mode not in {"multiplier", "sequence", "formula"}:
                    unresolved_reasons.append(("$.recovery.lotFormula.mode", "martingale requires an explicitly increasing multiplier, sequence, or formula"))
                if lot_mode == "multiplier" and _is_positive_finite(lot_formula.get("multiplier")) and float(lot_formula["multiplier"]) <= 1:
                    unresolved_reasons.append(("$.recovery.lotFormula.multiplier", "martingale multiplier must be greater than 1"))
                sequence = lot_formula.get("sequence")
                if lot_mode == "sequence" and isinstance(sequence, list) and len(sequence) > 1 and any(float(right) <= float(left) for left, right in zip(sequence, sequence[1:]) if _is_positive_finite(left) and _is_positive_finite(right)):
                    unresolved_reasons.append(("$.recovery.lotFormula.sequence", "martingale lot sequence must increase at every level"))

            reentry = _validate_required_mapping(
                recovery.get("reentryPolicy"),
                "$.recovery.reentryPolicy",
                ("enabled", "allowedAfter", "cooldownBars", "maxReentries", "sameSignalRequired", "sourceStatus", "sourceRefs"),
                issues,
            )
            if reentry is not None:
                _validate_recovery_provenance(reentry, "$.recovery.reentryPolicy", evidence_ids, issues, unresolved_reasons)
                if not isinstance(reentry.get("enabled"), bool):
                    _issue(issues, "BOOLEAN_REQUIRED", "$.recovery.reentryPolicy.enabled", "Expected a boolean")
                if reentry.get("allowedAfter") not in REENTRY_ALLOWED_AFTER:
                    _issue(issues, "REENTRY_EVENT_INVALID", "$.recovery.reentryPolicy.allowedAfter", f"Expected one of {sorted(REENTRY_ALLOWED_AFTER)}")
                for field in ("cooldownBars", "maxReentries"):
                    value = reentry.get(field)
                    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                        _issue(issues, "REENTRY_LIMIT_INVALID", f"$.recovery.reentryPolicy.{field}", f"{field} must be an integer >= 0")
                if not isinstance(reentry.get("sameSignalRequired"), bool):
                    _issue(issues, "BOOLEAN_REQUIRED", "$.recovery.reentryPolicy.sameSignalRequired", "Expected a boolean")
                if reentry.get("enabled") is True:
                    if reentry.get("allowedAfter") == "never" or not isinstance(reentry.get("maxReentries"), int) or reentry.get("maxReentries", 0) < 1:
                        unresolved_reasons.append(("$.recovery.reentryPolicy", "enabled re-entry requires an allowed event and maxReentries >= 1"))
                    trigger = reentry.get("trigger")
                    if not isinstance(trigger, Mapping) or _recovery_expression_is_unknown(trigger):
                        unresolved_reasons.append(("$.recovery.reentryPolicy.trigger", "enabled re-entry requires a typed known trigger"))
                    elif isinstance(trigger, Mapping):
                        _validate_expression(trigger, "$.recovery.reentryPolicy.trigger", issues, input_ids=input_ids, indicator_ids=indicator_ids, closed_bar=closed_bar)
                elif reentry.get("allowedAfter") != "never" or reentry.get("maxReentries") != 0:
                    _issue(issues, "REENTRY_ENABLEMENT_MISMATCH", "$.recovery.reentryPolicy", "Disabled re-entry must use allowedAfter=never and maxReentries=0")

            hedge = recovery.get("hedgeLifecycle")
            if mode == "hedging":
                hedge_record = _validate_required_mapping(
                    hedge,
                    "$.recovery.hedgeLifecycle",
                    ("openTrigger", "closeTrigger", "maxConcurrentHedges", "closeOrder", "lotFormula", "sourceStatus", "sourceRefs"),
                    issues,
                )
                if hedge_record is None:
                    unresolved_reasons.append(("$.recovery.hedgeLifecycle", "hedging requires a deterministic hedge lifecycle"))
                else:
                    _validate_recovery_provenance(hedge_record, "$.recovery.hedgeLifecycle", evidence_ids, issues, unresolved_reasons)
                    for trigger_name in ("openTrigger", "closeTrigger"):
                        trigger = hedge_record.get(trigger_name)
                        if not isinstance(trigger, Mapping) or _recovery_expression_is_unknown(trigger):
                            unresolved_reasons.append((f"$.recovery.hedgeLifecycle.{trigger_name}", f"hedge {trigger_name} must be a typed known expression"))
                        elif isinstance(trigger, Mapping):
                            _validate_expression(trigger, f"$.recovery.hedgeLifecycle.{trigger_name}", issues, input_ids=input_ids, indicator_ids=indicator_ids, closed_bar=closed_bar)
                    max_hedges = hedge_record.get("maxConcurrentHedges")
                    if not isinstance(max_hedges, int) or isinstance(max_hedges, bool) or max_hedges < 1:
                        _issue(issues, "HEDGE_LIMIT_INVALID", "$.recovery.hedgeLifecycle.maxConcurrentHedges", "maxConcurrentHedges must be an integer >= 1")
                    if hedge_record.get("closeOrder") not in HEDGE_CLOSE_ORDERS:
                        _issue(issues, "HEDGE_CLOSE_ORDER_INVALID", "$.recovery.hedgeLifecycle.closeOrder", f"Expected one of {sorted(HEDGE_CLOSE_ORDERS)}")
                    _validate_recovery_lot_formula(
                        hedge_record.get("lotFormula"),
                        "$.recovery.hedgeLifecycle.lotFormula",
                        input_ids=input_ids,
                        evidence_ids=evidence_ids,
                        issues=issues,
                        unresolved_reasons=unresolved_reasons,
                    )

    execution = candidate.get("execution")
    if isinstance(execution, Mapping):
        if execution.get("evaluateOn") != "new_closed_bar":
            _issue(issues, "EXECUTION_EVENT_INVALID", "$.execution.evaluateOn", "Closed-bar contract requires new_closed_bar")
        entry_order_type = execution.get("entryOrderType")
        if entry_order_type not in ENTRY_ORDER_TYPES:
            _issue(issues, "ORDER_TYPE_INVALID", "$.execution.entryOrderType", f"Expected one of {sorted(ENTRY_ORDER_TYPES)}")
        evaluation_order = _validate_string_list(execution.get("evaluationOrder"), "$.execution.evaluationOrder", issues, min_items=1)
        if len(evaluation_order) != len(set(evaluation_order)):
            _issue(issues, "EXECUTION_ORDER_DUPLICATE", "$.execution.evaluationOrder", "evaluationOrder entries must be unique")
        for index, phase in enumerate(evaluation_order):
            if phase not in EXECUTION_EVALUATION_STEPS:
                _issue(issues, "EXECUTION_ORDER_STEP_INVALID", f"$.execution.evaluationOrder[{index}]", f"Expected one of {sorted(EXECUTION_EVALUATION_STEPS)}")
        if "exit" not in evaluation_order or "entry" not in evaluation_order:
            unresolved_reasons.append(("$.execution.evaluationOrder", "execution order must include exit and entry"))
        elif evaluation_order.index("exit") > evaluation_order.index("entry"):
            _issue(issues, "EXECUTION_ORDER_UNSAFE", "$.execution.evaluationOrder", "exit must be evaluated before entry")

        duplicate_policy = execution.get("duplicateSignalPolicy")
        if duplicate_policy not in DUPLICATE_SIGNAL_POLICIES:
            _issue(issues, "DUPLICATE_SIGNAL_POLICY_INVALID", "$.execution.duplicateSignalPolicy", f"Expected one of {sorted(DUPLICATE_SIGNAL_POLICIES)}")

        price_policy = execution.get("priceNormalization")
        if not isinstance(price_policy, Mapping):
            _issue(issues, "OBJECT_REQUIRED", "$.execution.priceNormalization", "priceNormalization must be an object")
        else:
            for key in ("useBrokerDigits", "useBrokerTickSize"):
                if not isinstance(price_policy.get(key), bool):
                    _issue(issues, "BOOLEAN_REQUIRED", f"$.execution.priceNormalization.{key}", "Expected a boolean")
            if price_policy.get("useBrokerDigits") is not True or price_policy.get("useBrokerTickSize") is not True:
                unresolved_reasons.append(("$.execution.priceNormalization", "EA-ready execution must normalize price to broker digits and tick size"))
            if price_policy.get("invalidPricePolicy") not in INVALID_PRICE_POLICIES:
                _issue(issues, "INVALID_PRICE_POLICY", "$.execution.priceNormalization.invalidPricePolicy", f"Expected one of {sorted(INVALID_PRICE_POLICIES)}")

        retry_policy = execution.get("retryPolicy")
        if not isinstance(retry_policy, Mapping):
            _issue(issues, "OBJECT_REQUIRED", "$.execution.retryPolicy", "retryPolicy must be an object")
        else:
            retries = retry_policy.get("maxRetries")
            if not isinstance(retries, int) or isinstance(retries, bool) or not 0 <= retries <= 3:
                _issue(issues, "RETRY_LIMIT_INVALID", "$.execution.retryPolicy.maxRetries", "maxRetries must be an integer from 0 to 3")
            elif retries > 0:
                retryable = _validate_string_list(retry_policy.get("retryableErrors"), "$.execution.retryPolicy.retryableErrors", issues, min_items=1)
                backoff = retry_policy.get("backoffMilliseconds")
                if not isinstance(backoff, int) or isinstance(backoff, bool) or backoff < 0:
                    _issue(issues, "RETRY_BACKOFF_INVALID", "$.execution.retryPolicy.backoffMilliseconds", "backoffMilliseconds must be an integer >= 0")
                if retry_policy.get("exhaustedAction") not in RETRY_EXHAUSTED_ACTIONS:
                    _issue(issues, "RETRY_EXHAUSTED_ACTION_INVALID", "$.execution.retryPolicy.exhaustedAction", f"Expected one of {sorted(RETRY_EXHAUSTED_ACTIONS)}")
                if not retryable:
                    unresolved_reasons.append(("$.execution.retryPolicy.retryableErrors", "bounded retries require an explicit retryable error allowlist"))

        restart_policy = execution.get("restartPersistence")
        if not isinstance(restart_policy, Mapping):
            _issue(issues, "OBJECT_REQUIRED", "$.execution.restartPersistence", "restartPersistence must be an object")
        else:
            for key in ("restoreManagedTickets", "restoreStateMachine"):
                if not isinstance(restart_policy.get(key), bool):
                    _issue(issues, "BOOLEAN_REQUIRED", f"$.execution.restartPersistence.{key}", "Expected a boolean")
            if restart_policy.get("restoreManagedTickets") is not True or restart_policy.get("restoreStateMachine") is not True:
                unresolved_reasons.append(("$.execution.restartPersistence", "EA-ready restart must restore managed tickets and state-machine state"))
            _validate_nonempty_string(restart_policy.get("stateKey"), "$.execution.restartPersistence.stateKey", issues)
            if restart_policy.get("missingStatePolicy") not in MISSING_STATE_POLICIES:
                _issue(issues, "MISSING_STATE_POLICY_INVALID", "$.execution.restartPersistence.missingStatePolicy", f"Expected one of {sorted(MISSING_STATE_POLICIES)}")

        entry_section = candidate.get("entry")
        for side in sorted(enabled_sides):
            side_entry = entry_section.get(side) if isinstance(entry_section, Mapping) else None
            side_order_type = side_entry.get("orderType") if isinstance(side_entry, Mapping) else None
            if side_order_type in ENTRY_ORDER_TYPES and entry_order_type in ENTRY_ORDER_TYPES and side_order_type != entry_order_type:
                _issue(issues, "ORDER_TYPE_MISMATCH", f"$.entry.{side}.orderType", "Enabled side orderType must match execution.entryOrderType")

        pending_feature = management.get("pendingOrders") if isinstance(management, Mapping) else None
        if entry_order_type in {"limit", "stop"}:
            if not isinstance(pending_feature, Mapping) or pending_feature.get("enabled") is not True:
                unresolved_reasons.append(("$.orderManagement.pendingOrders", f"{entry_order_type} entry requires enabled pendingOrders lifecycle"))
            else:
                if not isinstance(pending_feature.get("action"), Mapping) or pending_feature["action"].get("kind") != "place_pending":
                    unresolved_reasons.append(("$.orderManagement.pendingOrders.action", f"{entry_order_type} entry requires action.kind=place_pending"))
                _validate_pending_order_parameters(
                    pending_feature.get("parameters"),
                    "$.orderManagement.pendingOrders.parameters",
                    expected_order_type=str(entry_order_type),
                    input_ids=input_ids,
                    indicator_ids=indicator_ids,
                    issues=issues,
                    unresolved_reasons=unresolved_reasons,
                )
        for key in ("maxSpreadInputRef", "slippageInputRef", "magicNumberInputRef"):
            _validate_defined_ref(execution, key, "$.execution", input_ids, issues)

    assumptions = candidate.get("assumptions")
    confirmed_execution_assumption_paths: set[str] = set()
    if not isinstance(assumptions, list):
        _issue(issues, "ARRAY_REQUIRED", "$.assumptions", "assumptions must be an array")
    else:
        for index, item in enumerate(assumptions):
            assumption_path = f"$.assumptions[{index}]"
            record = _validate_required_mapping(
                item,
                assumption_path,
                ("assumptionId", "description", "confirmed", "affectsExecution", "affectsPaths"),
                issues,
            )
            if record is None:
                continue
            _validate_nonempty_string(record.get("assumptionId"), f"{assumption_path}.assumptionId", issues, pattern=_ID_PATTERN)
            _validate_nonempty_string(record.get("description"), f"{assumption_path}.description", issues)
            for key in ("confirmed", "affectsExecution"):
                if not isinstance(record.get(key), bool):
                    _issue(issues, "BOOLEAN_REQUIRED", f"{assumption_path}.{key}", "Expected a boolean")
            affects_paths = _validate_string_list(record.get("affectsPaths"), f"{assumption_path}.affectsPaths", issues, min_items=1)
            if record.get("affectsExecution") is True and record.get("confirmed") is not True:
                unresolved_reasons.append((assumption_path, "execution assumption is not confirmed"))
            elif record.get("affectsExecution") is True and record.get("confirmed") is True:
                confirmed_execution_assumption_paths.update(affects_paths)

    active_code_source_records = list(_iter_active_code_source_records(candidate))
    for code_path, record in active_code_source_records:
        status = record.get("sourceStatus")
        source_refs = record.get("sourceRefs")
        if status in {"derived_expansion", "operator_assumption"} and (
            not isinstance(source_refs, list) or not source_refs
        ):
            unresolved_reasons.append((code_path, f"{status} code-affecting record requires evidence sourceRefs"))
        if status == "unknown":
            unresolved_reasons.append((code_path, "active code-affecting record is unknown"))
        if status == "operator_assumption" and not any(
            _assumption_covers_path(path, code_path)
            for path in confirmed_execution_assumption_paths
        ):
            unresolved_reasons.append((code_path, "operator assumption requires a confirmed execution assumption with matching affectsPaths"))

    executable_rule_statuses = [
        rule.get("sourceStatus")
        for _path, rule in rule_records
        if rule.get("enabled") is True and rule.get("phase") in {"setup", "entry", "exit", "safety"}
    ]
    if executable_rule_statuses and all(status == "operator_assumption" for status in executable_rule_statuses):
        unresolved_reasons.append(("$.entry", "all core executable rules are operator assumptions; at least one evidence-derived or verified rule is required"))

    if len(public_evidence_keys) < 2:
        unresolved_reasons.append(("$.evidenceMap", "EA readiness requires at least two independent public evidence domains"))

    unknowns = candidate.get("unknowns")
    if not isinstance(unknowns, list):
        _issue(issues, "ARRAY_REQUIRED", "$.unknowns", "unknowns must be an array")
    else:
        for index, item in enumerate(unknowns):
            if not isinstance(item, Mapping):
                _issue(issues, "OBJECT_REQUIRED", f"$.unknowns[{index}]", "Unknown must be an object")
            elif item.get("blocksExecution") is True:
                unresolved_reasons.append((f"$.unknowns[{index}]", "unknown blocks execution"))

    conflicts = candidate.get("conflicts")
    if not isinstance(conflicts, list):
        _issue(issues, "ARRAY_REQUIRED", "$.conflicts", "conflicts must be an array")
    else:
        for index, item in enumerate(conflicts):
            if not isinstance(item, Mapping):
                _issue(issues, "OBJECT_REQUIRED", f"$.conflicts[{index}]", "Conflict must be an object")
            else:
                _validate_source_refs(
                    item.get("sourceRefs"),
                    f"$.conflicts[{index}].sourceRefs",
                    evidence_ids,
                    issues,
                    required=False,
                )
                if item.get("resolutionStatus") != "resolved":
                    unresolved_reasons.append((f"$.conflicts[{index}]", "conflict is unresolved"))

    precedence = _validate_string_list(candidate.get("precedence"), "$.precedence", issues, min_items=1)
    if len(precedence) != len(set(precedence)):
        _issue(issues, "PRECEDENCE_DUPLICATE", "$.precedence", "Precedence entries must be unique")

    state_machine = candidate.get("stateMachine")
    state_ids: set[str] = set()
    state_records: dict[str, Mapping[str, Any]] = {}
    if not isinstance(state_machine, list) or not state_machine:
        _issue(issues, "STATE_MACHINE_REQUIRED", "$.stateMachine", "stateMachine requires at least one state")
    else:
        for index, state in enumerate(state_machine):
            path = f"$.stateMachine[{index}]"
            record = _validate_required_mapping(state, path, ("state", "transitions"), issues)
            if record is None:
                continue
            state_id = record.get("state")
            if _validate_nonempty_string(state_id, f"{path}.state", issues, pattern=_ID_PATTERN):
                if state_id in state_ids:
                    _issue(issues, "STATE_ID_DUPLICATE", f"{path}.state", "State names must be unique")
                state_ids.add(str(state_id))
                state_records[str(state_id).upper()] = record
        for index, state in enumerate(state_machine):
            if not isinstance(state, Mapping):
                continue
            path = f"$.stateMachine[{index}]"
            transitions = state.get("transitions")
            if not isinstance(transitions, list):
                _issue(issues, "ARRAY_REQUIRED", f"{path}.transitions", "transitions must be an array")
                continue
            for transition_index, transition in enumerate(transitions):
                transition_path = f"{path}.transitions[{transition_index}]"
                record = _validate_required_mapping(
                    transition,
                    transition_path,
                    ("to", "whenRuleIds"),
                    issues,
                )
                if record is None:
                    continue
                if record.get("to") not in state_ids:
                    _issue(issues, "STATE_REF_UNDEFINED", f"{transition_path}.to", f"Unknown state {record.get('to')!r}")
                refs = _validate_string_list(record.get("whenRuleIds"), f"{transition_path}.whenRuleIds", issues)
                for ref_index, ref in enumerate(refs):
                    if ref not in rule_ids:
                        _issue(issues, "RULE_REF_UNDEFINED", f"{transition_path}.whenRuleIds[{ref_index}]", f"Unknown rule reference {ref!r}")

        if "FLAT" not in state_records:
            unresolved_reasons.append(("$.stateMachine", "enabled strategy requires a FLAT state"))
        entry_section = candidate.get("entry")
        exit_section = candidate.get("exit")
        for side in sorted(enabled_sides):
            position_state = "LONG" if side == "buy" else "SHORT"
            if position_state not in state_records:
                unresolved_reasons.append(("$.stateMachine", f"enabled {side} side requires a {position_state} state"))
                continue
            entry_side = entry_section.get(side) if isinstance(entry_section, Mapping) else None
            entry_rule_ids = {
                str(rule.get("ruleId"))
                for rule in (entry_side.get("rules") if isinstance(entry_side, Mapping) and isinstance(entry_side.get("rules"), list) else [])
                if isinstance(rule, Mapping) and rule.get("enabled") is True and isinstance(rule.get("ruleId"), str)
            }
            flat = state_records.get("FLAT")
            flat_transitions = flat.get("transitions") if isinstance(flat, Mapping) else None
            pending_entry = isinstance(execution, Mapping) and execution.get("entryOrderType") in {"limit", "stop"}
            entry_target_state = "PENDING" if pending_entry else position_state
            has_entry_transition = any(
                isinstance(transition, Mapping)
                and str(transition.get("to") or "").upper() == entry_target_state
                and bool(entry_rule_ids.intersection(transition.get("whenRuleIds") if isinstance(transition.get("whenRuleIds"), list) else []))
                for transition in (flat_transitions if isinstance(flat_transitions, list) else [])
            )
            if not has_entry_transition:
                unresolved_reasons.append(("$.stateMachine", f"FLAT -> {entry_target_state} must reference an enabled {side} entry rule"))
            if pending_entry and "PENDING" in state_records:
                pending = state_records.get("PENDING")
                pending_transitions = pending.get("transitions") if isinstance(pending, Mapping) else None
                if not any(
                    isinstance(transition, Mapping)
                    and str(transition.get("to") or "").upper() == position_state
                    for transition in (pending_transitions if isinstance(pending_transitions, list) else [])
                ):
                    unresolved_reasons.append(("$.stateMachine", f"PENDING requires a fill transition to {position_state}"))

            exit_side = exit_section.get(side) if isinstance(exit_section, Mapping) else None
            exit_rule_ids = {
                str(rule.get("ruleId"))
                for rule in (exit_side.get("rules") if isinstance(exit_side, Mapping) and isinstance(exit_side.get("rules"), list) else [])
                if isinstance(rule, Mapping) and rule.get("enabled") is True and isinstance(rule.get("ruleId"), str)
            }
            if exit_rule_ids:
                position = state_records.get(position_state)
                position_transitions = position.get("transitions") if isinstance(position, Mapping) else None
                has_exit_transition = any(
                    isinstance(transition, Mapping)
                    and str(transition.get("to") or "").upper() == "FLAT"
                    and bool(exit_rule_ids.intersection(transition.get("whenRuleIds") if isinstance(transition.get("whenRuleIds"), list) else []))
                    for transition in (position_transitions if isinstance(position_transitions, list) else [])
                )
                if not has_exit_transition:
                    unresolved_reasons.append(("$.stateMachine", f"{position_state} -> FLAT must reference an enabled {side} exit rule"))

        if isinstance(execution, Mapping) and execution.get("entryOrderType") in {"limit", "stop"}:
            if "PENDING" not in state_records:
                unresolved_reasons.append(("$.stateMachine", "pending entry requires a PENDING state"))

    if not enabled_sides:
        unresolved_reasons.append(("$.scope.enabledSides", "no entry side is enabled"))
    def protection_enabled(side: str, name: str) -> bool:
        if not isinstance(tp_sl, Mapping):
            return False
        default_record = tp_sl.get(name)
        side_overrides = tp_sl.get("sideOverrides")
        side_record = side_overrides.get(side) if isinstance(side_overrides, Mapping) else None
        override = side_record.get(name) if isinstance(side_record, Mapping) else None
        effective = override if isinstance(override, Mapping) else default_record
        return isinstance(effective, Mapping) and effective.get("enabled") is True

    exit_section = candidate.get("exit")
    for side in sorted(enabled_sides):
        side_exit = exit_section.get(side) if isinstance(exit_section, Mapping) else None
        exit_rules = side_exit.get("rules") if isinstance(side_exit, Mapping) else None
        if (
            (not isinstance(exit_rules, list) or not exit_rules)
            and not protection_enabled(side, "stopLoss")
            and not protection_enabled(side, "takeProfit")
        ):
            unresolved_reasons.append((f"$.exit.{side}", "enabled side has no deterministic exit, stop loss, or take profit"))
    pseudocode = candidate.get("pseudocode")
    if isinstance(pseudocode, Mapping):
        _validate_nonempty_string(pseudocode.get("language"), "$.pseudocode.language", issues)
        pseudocode_lines = _validate_string_list(pseudocode.get("lines"), "$.pseudocode.lines", issues, min_items=1)
        pseudocode_text = "\n".join(pseudocode_lines).upper()
        required_pseudocode_rule_ids = {
            str(rule.get("ruleId"))
            for path, rule in rule_records
            if rule.get("enabled") is True
            and isinstance(rule.get("ruleId"), str)
            and (
                rule.get("phase") in {"setup", "entry", "exit", "safety"}
                or path.startswith("$.orderManagement")
            )
        }
        missing_pseudocode_rules = sorted(
            rule_id
            for rule_id in required_pseudocode_rule_ids
            if rule_id.upper() not in pseudocode_text
        )
        if missing_pseudocode_rules:
            unresolved_reasons.append(("$.pseudocode.lines", f"pseudocode does not cover enabled ruleIds: {', '.join(missing_pseudocode_rules)}"))

    completeness = candidate.get("completeness")
    if isinstance(completeness, Mapping):
        required = (
            "status",
            "score",
            "eaHandoffAllowed",
            "deterministicBacktestAllowed",
            "blockingIssues",
            "warnings",
            "unknownPaths",
            "conflictPaths",
        )
        for field in required:
            if field not in completeness:
                _issue(issues, "FIELD_REQUIRED", f"$.completeness.{field}", "Required field is missing")
        status = completeness.get("status")
        if status not in READINESS_STATUSES:
            _issue(issues, "READINESS_STATUS_INVALID", "$.completeness.status", f"Expected one of {sorted(READINESS_STATUSES)}")
        score = completeness.get("score")
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not math.isfinite(float(score)) or not 0 <= score <= 100:
            _issue(issues, "READINESS_SCORE_INVALID", "$.completeness.score", "score must be finite and between 0 and 100")
        handoff = completeness.get("eaHandoffAllowed")
        deterministic = completeness.get("deterministicBacktestAllowed")
        if not isinstance(handoff, bool):
            _issue(issues, "BOOLEAN_REQUIRED", "$.completeness.eaHandoffAllowed", "Expected a boolean")
        if not isinstance(deterministic, bool):
            _issue(issues, "BOOLEAN_REQUIRED", "$.completeness.deterministicBacktestAllowed", "Expected a boolean")
        blocking = completeness.get("blockingIssues")
        if not isinstance(blocking, list):
            _issue(issues, "ARRAY_REQUIRED", "$.completeness.blockingIssues", "blockingIssues must be an array")
        else:
            for index, blocker in enumerate(blocking):
                _validate_required_mapping(blocker, f"$.completeness.blockingIssues[{index}]", ("code", "path", "messageTh", "questionTh"), issues)
            if blocking:
                unresolved_reasons.append(("$.completeness.blockingIssues", "blocking issues remain"))
        for key in ("warnings", "unknownPaths", "conflictPaths"):
            if not isinstance(completeness.get(key), list):
                _issue(issues, "ARRAY_REQUIRED", f"$.completeness.{key}", f"{key} must be an array")
        if completeness.get("unknownPaths"):
            unresolved_reasons.append(("$.completeness.unknownPaths", "unknown executable paths remain"))
        if completeness.get("conflictPaths"):
            unresolved_reasons.append(("$.completeness.conflictPaths", "conflicting executable paths remain"))

        if unresolved_reasons and handoff is True:
            first_path, reason = unresolved_reasons[0]
            _issue(issues, "READINESS_UNRESOLVED", "$.completeness.eaHandoffAllowed", f"Cannot allow EA handoff while {reason} at {first_path}")
        if unresolved_reasons and status == "ready":
            _issue(issues, "READINESS_STATUS_INCONSISTENT", "$.completeness.status", "Ready status cannot contain unresolved executable research")
        if status == "ready" and handoff is not True:
            _issue(issues, "READINESS_HANDOFF_INCONSISTENT", "$.completeness.eaHandoffAllowed", "Ready status requires EA handoff")
        if handoff is True and status != "ready":
            _issue(issues, "READINESS_HANDOFF_INCONSISTENT", "$.completeness.status", "EA handoff requires ready status")
        if handoff is True and deterministic is not True:
            _issue(issues, "READINESS_BACKTEST_INCONSISTENT", "$.completeness.deterministicBacktestAllowed", "EA handoff requires deterministic backtest readiness")
        if require_ready and handoff is not True:
            _issue(issues, "EA_HANDOFF_REQUIRED", "$.completeness.eaHandoffAllowed", "This operation requires an EA-ready blueprint")

    return issues


def normalize_and_validate_blueprint(
    blueprint: object,
    *,
    require_ready: bool = False,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Return a canonical candidate and stable validation issue records."""

    try:
        candidate = _normalize_candidate(blueprint)
    except BlueprintValidationError as exc:
        return {}, [dict(issue) for issue in exc.issues]
    issues = _validate_blueprint_candidate(candidate, require_ready=require_ready)
    return candidate, [issue.as_dict() for issue in issues]


def validate_blueprint(
    blueprint: object,
    *,
    require_ready: bool = False,
) -> list[dict[str, str]]:
    """Return all errors without mutating or raising for invalid input."""

    _candidate, issues = normalize_and_validate_blueprint(
        blueprint,
        require_ready=require_ready,
    )
    return issues


def normalize_blueprint(
    blueprint: object,
    *,
    require_ready: bool = False,
) -> dict[str, Any]:
    """Return a canonical deep copy or raise ``BlueprintValidationError``."""

    candidate, issues = normalize_and_validate_blueprint(
        blueprint,
        require_ready=require_ready,
    )
    if issues:
        raise BlueprintValidationError(issues)
    return candidate


def canonical_blueprint_json(blueprint: object, *, require_ready: bool = False) -> str:
    """Serialize a validated blueprint using deterministic UTF-8 JSON rules."""

    normalized = normalize_blueprint(blueprint, require_ready=require_ready)
    return _canonical_fragment(normalized)


def compute_blueprint_digest(blueprint: object, *, require_ready: bool = False) -> str:
    """Return the lowercase SHA-256 digest of canonical blueprint JSON."""

    payload = canonical_blueprint_json(blueprint, require_ready=require_ready).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _all_rules(blueprint: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        rule
        for _path, rule in _iter_rule_records(
            {
                "setup": blueprint.get("setup"),
                "entry": blueprint.get("entry"),
                "exit": blueprint.get("exit"),
                "orderManagement": blueprint.get("orderManagement"),
                "recovery": blueprint.get("recovery"),
            }
        )
    ]


def project_blueprint_to_legacy_report_metrics(blueprint: object) -> dict[str, Any]:
    """Project a v2 blueprint into the existing Deep Research metric names.

    The direct ``eaImplementationBlueprint`` member and the copy inside
    ``implementationNotes`` make the projection lossless.  Other members are
    compatibility views for the current 49-column Deep_Research sheet and the
    23-field EA Factory adapter.
    """

    normalized = normalize_blueprint(blueprint)
    digest = compute_blueprint_digest(normalized)
    scope = normalized["scope"]
    completeness = normalized["completeness"]
    evidence = normalized["evidenceMap"]
    limitations = {
        "unknowns": normalized["unknowns"],
        "assumptions": normalized["assumptions"],
        "blockingIssues": completeness["blockingIssues"],
        "warnings": completeness["warnings"],
    }
    implementation_notes = {
        "schemaVersion": SCHEMA_VERSION,
        "blueprintDigest": digest,
        "eaImplementationBlueprint": normalized,
        "inputs": normalized["inputs"],
        "pseudocode": normalized["pseudocode"],
        "testCases": normalized["testCases"],
        "completeness": completeness,
    }
    metrics: dict[str, Any] = {
        "systemIdentity": {
            "strategyId": normalized["strategyId"],
            "systemName": scope["systemName"],
            "strategyFamily": scope["strategyFamily"],
            "researchRevision": normalized["researchRevision"],
        },
        "verifiedRules": _all_rules(normalized),
        "conflictingEvidence": normalized["conflicts"],
        "setupConditions": {
            "barSemantics": normalized["barSemantics"],
            "setup": normalized["setup"],
        },
        "indicatorSettings": normalized["indicators"],
        "entrySteps": normalized["entry"],
        "exitSteps": normalized["exit"],
        "tradeManagementSteps": {
            "orderManagement": normalized["orderManagement"],
            "stateMachine": normalized["stateMachine"],
        },
        "riskModel": {
            "riskAndSizing": normalized["riskAndSizing"],
            "stopLoss": normalized["tpSl"]["stopLoss"],
            "takeProfit": normalized["tpSl"]["takeProfit"],
        },
        "recoveryAndAveragingRules": normalized["recovery"],
        "specialConditions": {
            "execution": normalized["execution"],
            "precedence": normalized["precedence"],
        },
        "suitableMarket": {
            "market": scope["market"],
            "symbols": scope["symbols"],
            "sessions": scope["sessions"],
            "timezone": scope["timezone"],
            "suitableFor": scope["suitableFor"],
        },
        "symbols": scope["symbols"],
        "sessions": scope["sessions"],
        "suitableFor": scope["suitableFor"],
        "suitableTimeframe": sorted(
            {scope["signalTimeframe"], scope["executionTimeframe"]}
        ),
        "targetPlatforms": scope["platforms"],
        "ohlcBacktestReadiness": (
            "ready"
            if completeness["deterministicBacktestAllowed"]
            else "needs_clarification"
        ),
        "deterministicRuleKind": "typed_expression_ast_v2",
        "feasibilityStatus": completeness["status"],
        "feasibilityReasons": [
            item.get("messageTh")
            for item in completeness["blockingIssues"]
            if isinstance(item, Mapping) and item.get("messageTh")
        ],
        "implementationNotes": implementation_notes,
        "sourceLinks": sorted(
            {
                item["url"]
                for item in evidence
                if isinstance(item, Mapping) and isinstance(item.get("url"), str)
            }
        ),
        "checkedAt": normalized["checkedAt"],
        "limitations": limitations,
        "eaImplementationBlueprint": normalized,
        "strategySchemaVersion": SCHEMA_VERSION,
        "eaReadiness": completeness,
        "blueprintDigest": digest,
    }
    return metrics


def _extract_blueprint_candidate(value: object, path: str) -> tuple[object | None, str | None]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise BlueprintValidationError(
                [BlueprintIssue("BLUEPRINT_JSON_INVALID", path, f"JSON could not be decoded: {exc.msg}")]
            ) from exc
    if not isinstance(value, Mapping):
        return None, None
    for alias in BLUEPRINT_ALIASES:
        if alias in value:
            candidate = value[alias]
            if isinstance(candidate, str):
                try:
                    candidate = json.loads(candidate)
                except json.JSONDecodeError as exc:
                    raise BlueprintValidationError(
                        [BlueprintIssue("BLUEPRINT_JSON_INVALID", f"{path}.{alias}", f"JSON could not be decoded: {exc.msg}")]
                    ) from exc
            return candidate, f"{path}.{alias}"
    if (
        value.get("schemaVersion") == SCHEMA_VERSION
        and "barSemantics" in value
        and "scope" in value
    ):
        return value, path
    return None, None


def _verify_reconstructed_digest(
    normalized: Mapping[str, Any],
    container: Mapping[str, Any] | None,
    path: str,
) -> None:
    if not isinstance(container, Mapping):
        return
    expected = container.get("blueprintDigest")
    if expected in (None, ""):
        return
    actual = compute_blueprint_digest(normalized)
    if not isinstance(expected, str) or expected.lower() != actual:
        raise BlueprintValidationError(
            [
                BlueprintIssue(
                    "BLUEPRINT_DIGEST_MISMATCH",
                    f"{path}.blueprintDigest",
                    "Stored blueprint digest does not match canonical content",
                )
            ]
        )


def reconstruct_blueprint_from_implementation_notes(
    implementation_notes: object,
    *,
    require_ready: bool = False,
) -> dict[str, Any]:
    """Reconstruct a blueprint from ``implementation_notes_json`` content."""

    container = _parse_mapping(implementation_notes, "$.implementation_notes_json")
    candidate, candidate_path = _extract_blueprint_candidate(
        container,
        "$.implementation_notes_json",
    )
    if candidate is None:
        raise BlueprintValidationError(
            [
                BlueprintIssue(
                    "BLUEPRINT_NOT_FOUND",
                    "$.implementation_notes_json",
                    f"Expected one of {BLUEPRINT_ALIASES}",
                )
            ]
        )
    normalized = normalize_blueprint(candidate, require_ready=require_ready)
    _verify_reconstructed_digest(normalized, container, "$.implementation_notes_json")
    return normalized


def reconstruct_blueprint_from_research_metrics(
    metrics: object,
    *,
    require_ready: bool = False,
) -> dict[str, Any]:
    """Reconstruct from direct report metrics or nested implementation notes."""

    container = _parse_mapping(metrics, "$.metrics")
    candidate, candidate_path = _extract_blueprint_candidate(container, "$.metrics")
    if candidate is not None:
        normalized = normalize_blueprint(candidate, require_ready=require_ready)
        _verify_reconstructed_digest(normalized, container, "$.metrics")
        return normalized
    for key in ("implementationNotes", "implementation_notes_json"):
        if key in container:
            return reconstruct_blueprint_from_implementation_notes(
                container[key],
                require_ready=require_ready,
            )
    raise BlueprintValidationError(
        [BlueprintIssue("BLUEPRINT_NOT_FOUND", "$.metrics", f"Expected one of {BLUEPRINT_ALIASES} or implementationNotes")]
    )


def reconstruct_blueprint_from_deep_sheet_row(
    row: object,
    *,
    require_ready: bool = False,
) -> dict[str, Any]:
    """Reconstruct from a Deep_Research row without knowing bridge internals."""

    container = _parse_mapping(row, "$.row")
    for key in ("implementation_notes_json", "implementationNotes"):
        if key in container:
            return reconstruct_blueprint_from_implementation_notes(
                container[key],
                require_ready=require_ready,
            )
    candidate, _path = _extract_blueprint_candidate(container, "$.row")
    if candidate is not None:
        return normalize_blueprint(candidate, require_ready=require_ready)
    raise BlueprintValidationError(
        [BlueprintIssue("BLUEPRINT_NOT_FOUND", "$.row.implementation_notes_json", "Deep_Research row has no canonical blueprint")]
    )


def _operand_text(value: object) -> str:
    if not isinstance(value, Mapping):
        return _canonical_fragment(value)
    kind = value.get("kind")
    if kind in {"indicator", "input"}:
        name = value.get("ref") or value.get("indicatorId") or value.get("inputId") or "?"
    elif kind == "price":
        name = value.get("field") or "price"
    elif kind == "constant":
        name = value.get("value")
    else:
        name = value.get("field") or value.get("ref") or kind or "?"
    suffix = f"[{value['shift']}]" if isinstance(value.get("shift"), int) else ""
    return f"{name}{suffix}"


def _expression_text(expression: object) -> str:
    if not isinstance(expression, Mapping):
        return _canonical_fragment(expression)
    op = expression.get("op")
    if op in {"and", "or"}:
        joiner = " AND " if op == "and" else " OR "
        return "(" + joiner.join(_expression_text(item) for item in expression.get("items", [])) + ")"
    if op == "not":
        return f"NOT ({_expression_text(expression.get('item'))})"
    if op in {"cross_above", "cross_below"}:
        expanded = expression.get("expanded")
        comparisons = expanded.get("all", []) if isinstance(expanded, Mapping) else []
        return " AND ".join(_expression_text(item) for item in comparisons)
    if op in {"<", "<=", ">", ">=", "==", "!=", "break_above", "break_below", "close_above", "close_below", "touch"}:
        return f"{_operand_text(expression.get('left'))} {op} {_operand_text(expression.get('right'))}"
    if op == "within":
        return f"{_operand_text(expression.get('value'))} WITHIN {_operand_text(expression.get('lower'))}..{_operand_text(expression.get('upper'))}"
    if op in {"rising", "falling"}:
        return f"{_operand_text(expression.get('value'))} {str(op).upper()} {expression.get('bars')} bars"
    if op == "once_per_bar":
        return "ONCE PER CLOSED BAR [1]"
    if op == "unknown":
        return "UNRESOLVED"
    return _canonical_fragment(expression)


def render_ea_ready_text(blueprint: object) -> str:
    """Render deterministic, writer-facing text from the canonical contract."""

    normalized = normalize_blueprint(blueprint)
    digest = compute_blueprint_digest(normalized)
    scope = normalized["scope"]
    completeness = normalized["completeness"]
    lines = [
        f"EA RESEARCH CONTRACT: {SCHEMA_VERSION}",
        f"STRATEGY: {scope['systemName']} ({normalized['strategyId']})",
        f"RESEARCH REVISION: {normalized['researchRevision']}",
        f"BLUEPRINT SHA256: {digest}",
        f"EA HANDOFF: {'ALLOWED' if completeness['eaHandoffAllowed'] else 'BLOCKED'}",
        "",
        "[BAR SEMANTICS]",
        "bar[0]=forming; signal=bar[1]; previous=bar[2]; evaluate=new_closed_bar; lookahead=forbidden",
        "cross_above: left[2] <= right[2] AND left[1] > right[1]",
        "cross_below: left[2] >= right[2] AND left[1] < right[1]",
        "",
        "[SCOPE]",
        f"Platforms: {', '.join(scope['platforms'])}",
        f"Market/Symbols: {scope['market']} / {', '.join(scope['symbols'])}",
        f"Timeframes: signal={scope['signalTimeframe']}; execution={scope['executionTimeframe']}",
        f"Sessions: {', '.join(scope['sessions']) or 'all'}; timezone={scope['timezone']}",
        f"Enabled sides: {', '.join(scope['enabledSides'])}",
        "",
        "[INPUTS]",
    ]
    for item in normalized["inputs"]:
        limits = "; ".join(
            f"{name}={item[name]}" for name in ("min", "max", "step") if name in item
        )
        lines.append(
            f"- {item['inputId']} ({item['type']}, {item['unit']}): default={item['default']}"
            + (f"; {limits}" if limits else "")
        )
    lines.extend(["", "[INDICATORS]"])
    for item in normalized["indicators"]:
        lines.append(
            f"- {item['indicatorId']}: {item['kind']} timeframe={item['timeframe']} "
            f"appliedPrice={item['appliedPrice']} output={item['outputLine']} "
            f"parameters={_canonical_fragment(item['parameters'])}"
        )

    for section_name, section in (
        ("SETUP", normalized["setup"]),
        ("ENTRY", normalized["entry"]),
        ("EXIT", normalized["exit"]),
        ("ORDER MANAGEMENT", normalized["orderManagement"]),
    ):
        lines.extend(["", f"[{section_name}]"])
        found = False
        for path, rule in _iter_rule_records(section, f"$.{section_name.lower().replace(' ', '')}"):
            found = True
            human = rule.get("humanTextTh")
            expression = _expression_text(rule.get("expression"))
            lines.append(
                f"- {rule.get('ruleId')} ({rule.get('phase')}, source={rule.get('sourceStatus')}): "
                f"{human + ' | ' if isinstance(human, str) and human else ''}{expression}"
            )
        if not found:
            lines.append(f"- {_canonical_fragment(section)}")

    lines.extend(
        [
            "",
            "[TP/SL]",
            _canonical_fragment(normalized["tpSl"]),
            "",
            "[RISK AND LOT SIZING]",
            _canonical_fragment(normalized["riskAndSizing"]),
            "",
            "[RECOVERY / GRID / MARTINGALE / HEDGE]",
            _canonical_fragment(normalized["recovery"]),
            "",
            "[EXECUTION]",
            _canonical_fragment(normalized["execution"]),
            "",
            "[PRECEDENCE]",
        ]
    )
    lines.extend(f"{index}. {item}" for index, item in enumerate(normalized["precedence"], start=1))
    lines.extend(["", "[PSEUDOCODE]"])
    lines.extend(str(item) for item in normalized["pseudocode"]["lines"])
    lines.extend(["", "[TEST CASES]"])
    for item in normalized["testCases"]:
        lines.append(
            f"- {item['caseId']} [{item['kind']}] rules={','.join(item['ruleIds'])}; "
            f"expected={_canonical_fragment(item['expected'])}"
        )
    lines.extend(
        [
            "",
            "[READINESS]",
            f"status={completeness['status']}; score={completeness['score']}; "
            f"deterministicBacktestAllowed={str(completeness['deterministicBacktestAllowed']).lower()}",
        ]
    )
    for blocker in completeness["blockingIssues"]:
        if isinstance(blocker, Mapping):
            lines.append(
                f"- BLOCKER {blocker.get('code')} at {blocker.get('path')}: {blocker.get('messageTh')}"
            )
    return "\n".join(lines).rstrip() + "\n"


__all__ = [
    "BLUEPRINT_ALIASES",
    "CLOSED_BAR_SEMANTICS",
    "LEGACY_REPORT_METRIC_KEYS",
    "SCHEMA_ID",
    "SCHEMA_PATH",
    "SCHEMA_VERSION",
    "BlueprintIssue",
    "BlueprintValidationError",
    "canonical_blueprint_json",
    "compute_blueprint_digest",
    "normalize_and_validate_blueprint",
    "normalize_blueprint",
    "project_blueprint_to_legacy_report_metrics",
    "reconstruct_blueprint_from_deep_sheet_row",
    "reconstruct_blueprint_from_implementation_notes",
    "reconstruct_blueprint_from_research_metrics",
    "render_ea_ready_text",
    "validate_blueprint",
]
