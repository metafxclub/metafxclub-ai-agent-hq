from __future__ import annotations

import ast
import hashlib
import json
import math
import re
from collections.abc import Mapping


REQUIREMENTS_SCHEMA_VERSION = "ea-factory-blueprint-coverage-requirements-v4"
MANIFEST_SCHEMA_VERSION = "ea-factory-blueprint-coverage-manifest-v4"
COVERAGE_KEYS = (
    "blueprintDigests",
    "semanticDigests",
    "ruleIds",
    "inputIds",
    "indicatorIds",
    "stateIds",
    "testCaseIds",
)
_ID_FIELD_BY_KEY = {
    "inputIds": ("inputs", "inputId"),
    "indicatorIds": ("indicators", "indicatorId"),
    "stateIds": ("stateMachine", "state"),
    "testCaseIds": ("testCases", "caseId"),
}
_MARKER_PREFIX_BY_KEY = {
    "blueprintDigests": "BLUEPRINT",
    "semanticDigests": "SEMANTIC",
    "ruleIds": "RULE",
    "inputIds": "INPUT",
    "indicatorIds": "INDICATOR",
    "stateIds": "STATE",
    "testCaseIds": "TEST",
}
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_SUPPORTED_PLATFORMS = {"mt4", "mt5", "tradingview"}
_SEMANTIC_BINDING_KINDS = {
    "bar_semantics",
    "blueprint_section",
    "execution_contract",
    "indicator",
    "management_feature",
    "protection",
    "pseudocode",
    "recovery_safety",
    "risk_sizing",
    "rule_semantics",
    "state_transition",
    "test_vector",
}
_SEMANTIC_BINDING_ACTIONS = {
    "cancel_pending",
    "close_partial",
    "close_position",
    "entry",
    "entry_buy",
    "entry_sell",
    "exit",
    "indicator",
    "initialization",
    "management",
    "modify_pending",
    "move_stop_loss",
    "move_take_profit",
    "pending",
    "place_pending",
    "replace_pending",
    "scale_in",
    "scale_out",
    "state_decision",
    "verification",
}
_MQL_LIFECYCLE_ROOTS = {
    "OnInit",
    "OnTick",
    "OnTimer",
    "OnCalculate",
    "start",
    "init",
}
_MQL_TRADING_ROOTS = {"OnTick", "OnTimer", "start"}
_MQL_INITIALIZATION_ROOTS = {"OnInit", "init"}
_CONTROL_NAMES = {"if", "for", "while", "switch", "catch"}
_COMPARISON_PATTERN = re.compile(r"(?:<=|>=|==|!=|<|>)")
_RULE_PREDICATE_SCHEMA_VERSION = "ea-factory-rule-predicate-evidence-v1"
_RULE_PREDICATE_COMPARISON_OPS = {"<", "<=", ">", ">=", "==", "!="}
_SOURCE_NUMBER_PATTERN = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
_SOURCE_IDENTIFIER_ATOM_PATTERN = (
    r"[A-Za-z_][A-Za-z0-9_.]*\s*"
    r"(?:\(\s*[^(){}\n;]*\s*\)|\[\s*[^\[\]\n;]+\s*\])?"
)
_SOURCE_COMPARISON_CLAUSE_PATTERN = re.compile(
    rf"(?P<left>(?:{_SOURCE_NUMBER_PATTERN}|{_SOURCE_IDENTIFIER_ATOM_PATTERN}))\s*"
    rf"(?P<op><=|>=|==|!=|<|>)\s*"
    rf"(?P<right>(?:{_SOURCE_NUMBER_PATTERN}|{_SOURCE_IDENTIFIER_ATOM_PATTERN}))"
)
_INDICATOR_PATTERN = re.compile(
    r"(?:\bi[A-Z][A-Za-z0-9_]*\s*\(|\bCopyBuffer\s*\(|\bta\.[A-Za-z_][A-Za-z0-9_]*\s*\()"
)
_STATE_PATTERN = re.compile(
    r"\b(?:state|position|PositionsTotal|PositionSelect|PositionGet|OrdersTotal|OrderSelect|"
    r"strategy\.position_size)\b",
    re.IGNORECASE,
)
_MQL_ENTRY_PATTERN = re.compile(
    r"\bOrderSend\s*\([^;{}]*(?:OP_BUY|OP_SELL)",
    re.IGNORECASE,
)
_MQL_CTRADE_ENTRY_PATTERN = re.compile(
    r"\.\s*(?:Buy|Sell|PositionOpen|OrderOpen)\s*\(", re.IGNORECASE
)
_MQL_BUY_ENTRY_PATTERN = re.compile(
    r"\bOrderSend\s*\([^;{}]*\bOP_BUY\b|"
    r"\brequest\s*\.\s*type\s*=\s*ORDER_TYPE_BUY\b|"
    r"\.\s*Buy\s*\(",
    re.IGNORECASE,
)
_MQL_SELL_ENTRY_PATTERN = re.compile(
    r"\bOrderSend\s*\([^;{}]*\bOP_SELL\b|"
    r"\brequest\s*\.\s*type\s*=\s*ORDER_TYPE_SELL\b|"
    r"\.\s*Sell\s*\(",
    re.IGNORECASE,
)
_MQL_EXIT_PATTERN = re.compile(
    r"(?:\bOrderClose\s*\(|\brequest\s*\.\s*position\b[^;{}]*\bOrderSend\s*\()",
    re.IGNORECASE,
)
_MQL_CTRADE_EXIT_PATTERN = re.compile(
    r"\.\s*(?:PositionClose|PositionClosePartial)\s*\(", re.IGNORECASE
)
_MQL_PENDING_PATTERN = re.compile(
    r"\bOrderSend\s*\([^;{}]*(?:OP_BUYLIMIT|OP_BUYSTOP|OP_SELLLIMIT|OP_SELLSTOP)",
    re.IGNORECASE,
)
_MQL_CTRADE_PENDING_PATTERN = re.compile(
    r"\.\s*(?:BuyLimit|SellLimit|BuyStop|SellStop|BuyStopLimit|SellStopLimit|OrderOpen)\s*\(",
    re.IGNORECASE,
)
_PINE_ENTRY_PATTERN = re.compile(r"\bstrategy\.(?:entry|order)\s*\(")
_PINE_BUY_ENTRY_PATTERN = re.compile(
    r"\bstrategy\.(?:entry|order)\s*\([^\n]*(?:strategy\.long|\blong\b)",
    re.IGNORECASE,
)
_PINE_SELL_ENTRY_PATTERN = re.compile(
    r"\bstrategy\.(?:entry|order)\s*\([^\n]*(?:strategy\.short|\bshort\b)",
    re.IGNORECASE,
)
_PINE_EXIT_PATTERN = re.compile(r"\bstrategy\.(?:close|close_all|exit)\s*\(")
_PINE_PENDING_PATTERN = re.compile(
    r"\bstrategy\.(?:entry|order)\s*\([^\n]*(?:\bstop\s*=|\blimit\s*=)",
    re.IGNORECASE,
)
_STOP_LOSS_PATTERN = re.compile(
    r"\b(?:stoploss|stop_loss|sl_pips|sl_points|stopPrice|stop_price|sl)\b|"
    r"\bstop\s*=",
    re.IGNORECASE,
)
_TAKE_PROFIT_PATTERN = re.compile(
    r"\b(?:takeprofit|take_profit|tp_pips|tp_points|limitPrice|limit_price|tp)\b|"
    r"\blimit\s*=",
    re.IGNORECASE,
)

# Blueprint v2 is a closed contract.  A digest for every canonical top-level
# section prevents a stale source from being made current by replacing only
# the whole-document marker after, for example, a rule, input default,
# timeframe, symbol, cooldown or evidence binding changes.
_CANONICAL_BLUEPRINT_SECTIONS = (
    "assumptions",
    "barSemantics",
    "checkedAt",
    "completeness",
    "conflicts",
    "entry",
    "evidenceMap",
    "execution",
    "exit",
    "indicators",
    "inputs",
    "orderManagement",
    "precedence",
    "pseudocode",
    "recovery",
    "researchRevision",
    "riskAndSizing",
    "schemaVersion",
    "scope",
    "setup",
    "stateMachine",
    "strategyId",
    "testCases",
    "tpSl",
    "unknowns",
)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _rule_ids(node: object) -> set[str]:
    result: set[str] = set()
    if isinstance(node, Mapping):
        rule_id = node.get("ruleId")
        if isinstance(rule_id, str) and rule_id.strip():
            result.add(rule_id.strip())
        for value in node.values():
            result.update(_rule_ids(value))
    elif isinstance(node, (list, tuple)):
        for value in node:
            result.update(_rule_ids(value))
    return result


def _canonical_rule_phase(value: object) -> str:
    phase = str(value or "").strip().lower()
    # `modify` is the only management phase in the canonical Blueprint v2
    # schema.  Keep the legacy spellings fail-safe for an already persisted
    # document, but never depend on them when deriving the coverage contract.
    if phase in {"management", "order_management"}:
        return "modify"
    return phase


def _rule_action(phase: str, structural_action: str = "") -> str:
    if structural_action in {"pending", "recovery"}:
        return structural_action
    return {
        "entry": "entry",
        "exit": "exit",
        "modify": "management",
        "recovery": "recovery",
    }.get(phase, "other")


def _rule_roles(node: object) -> list[dict[str, str]]:
    """Collect the stable phase/side role for every canonical rule ID."""

    result: dict[str, dict[str, str]] = {}

    def visit(
        value: object,
        inherited_phase: str = "",
        inherited_side: str = "",
        inherited_action: str = "",
    ) -> None:
        if isinstance(value, Mapping):
            phase = _canonical_rule_phase(value.get("phase") or inherited_phase)
            side = str(value.get("side") or inherited_side).strip().lower()
            rule_id = value.get("ruleId")
            if isinstance(rule_id, str) and rule_id.strip():
                result[rule_id.strip()] = {
                    "id": rule_id.strip(),
                    "phase": phase or "other",
                    "side": side or "both",
                    "action": _rule_action(phase, inherited_action),
                }
            for key, child in value.items():
                child_phase = phase
                child_side = side
                child_action = inherited_action
                lexical_key = str(key).strip().lower()
                if lexical_key in {"setup", "entry", "exit", "management", "order_management"}:
                    child_phase = _canonical_rule_phase(lexical_key)
                if lexical_key == "recovery":
                    child_phase = "recovery"
                    child_action = "recovery"
                if lexical_key in {"pendingorders", "pending_orders"}:
                    child_action = "pending"
                if lexical_key in {"buy", "sell", "both"}:
                    child_side = lexical_key
                visit(child, child_phase, child_side, child_action)
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child, inherited_phase, inherited_side, inherited_action)

    visit(node)
    return [result[key] for key in sorted(result)]


def _semantic_profile(blueprint: Mapping[str, object]) -> dict:
    roles = _rule_roles(blueprint)
    bar_semantics = (
        blueprint.get("barSemantics")
        if isinstance(blueprint.get("barSemantics"), Mapping)
        else {}
    )
    tp_sl = blueprint.get("tpSl") if isinstance(blueprint.get("tpSl"), Mapping) else {}
    stop_loss = tp_sl.get("stopLoss") if isinstance(tp_sl.get("stopLoss"), Mapping) else {}
    take_profit = tp_sl.get("takeProfit") if isinstance(tp_sl.get("takeProfit"), Mapping) else {}
    management = (
        blueprint.get("orderManagement")
        if isinstance(blueprint.get("orderManagement"), Mapping)
        else {}
    )
    pending = (
        management.get("pendingOrders")
        if isinstance(management.get("pendingOrders"), Mapping)
        else {}
    )
    recovery = (
        blueprint.get("recovery")
        if isinstance(blueprint.get("recovery"), Mapping)
        else {}
    )
    enabled_management_features = sorted(
        key
        for key, value in management.items()
        if key != "rules"
        and isinstance(value, Mapping)
        and value.get("enabled") is True
    )
    state_machine = blueprint.get("stateMachine")
    pending_state_ids: set[str] = set()
    if isinstance(state_machine, list):
        for state in state_machine:
            if not isinstance(state, Mapping):
                continue
            state_id = str(state.get("state") or "").strip()
            transitions = state.get("transitions")
            transition_targets = {
                str(transition.get("to") or "").strip()
                for transition in transitions
                if isinstance(transitions, list) and isinstance(transition, Mapping)
            } if isinstance(transitions, list) else set()
            if state_id.upper() == "PENDING":
                pending_state_ids.add(state_id)
            if any(target.upper() == "PENDING" for target in transition_targets):
                pending_state_ids.add(state_id)
                pending_state_ids.update(
                    target for target in transition_targets if target.upper() == "PENDING"
                )
    entry = blueprint.get("entry") if isinstance(blueprint.get("entry"), Mapping) else {}
    pending_entry_rule_ids: set[str] = set()
    pending_entry_type = False
    for side in entry.values():
        if not isinstance(side, Mapping) or side.get("enabled") is not True:
            continue
        if str(side.get("orderType") or "market").strip().lower() == "market":
            continue
        pending_entry_type = True
        pending_entry_rule_ids.update(_rule_ids(side.get("rules")))
    if pending_entry_rule_ids:
        roles = [
            {**row, "action": "pending"}
            if row["id"] in pending_entry_rule_ids and row.get("action") == "entry"
            else row
            for row in roles
        ]
    def role_ids(action: str) -> list[str]:
        return sorted(row["id"] for row in roles if row.get("action") == action)

    profile = {
        "ruleRoles": roles,
        "managementRuleIds": role_ids("management"),
        "pendingRuleIds": role_ids("pending"),
        "recoveryRuleIds": role_ids("recovery"),
        "pendingStateIds": sorted(pending_state_ids),
        "enabledManagementFeatures": enabled_management_features,
        "requiresEntry": any(row["action"] in {"entry", "pending"} for row in roles),
        "requiresExit": any(row["action"] == "exit" for row in roles),
        "requiresManagement": bool(
            enabled_management_features or role_ids("management")
        ),
        "requiresPendingOrder": bool(
            pending.get("enabled") is True
            or role_ids("pending")
            or pending_state_ids
            or pending_entry_type
        ),
        "requiresRecovery": bool(
            recovery.get("enabled") is True or role_ids("recovery")
        ),
        "requiresStopLoss": stop_loss.get("enabled") is True,
        "requiresTakeProfit": take_profit.get("enabled") is True,
        "requiresClosedBar": (
            str(bar_semantics.get("evaluateOn") or "").lower() == "new_closed_bar"
        ),
    }
    profile["semanticBindings"] = _semantic_bindings(blueprint, profile)
    return profile


def _rule_predicate_operand_contract(
    value: object,
    *,
    forced_shift: int | None = None,
) -> dict[str, object] | None:
    """Project the source-observable parts of one canonical predicate operand."""

    shift: int | None = forced_shift
    number: int | float | None = None
    kind = "constant"
    identity = "#number"
    if isinstance(value, Mapping):
        kind = str(value.get("kind") or "").strip().lower()
        if not kind:
            return None
        if forced_shift is None and "shift" in value:
            raw_shift = value.get("shift")
            if not isinstance(raw_shift, int) or isinstance(raw_shift, bool):
                return None
            shift = raw_shift
        if kind == "constant":
            raw_number = value.get("value")
            if (
                not isinstance(raw_number, (int, float))
                or isinstance(raw_number, bool)
                or not math.isfinite(float(raw_number))
            ):
                return None
            number = raw_number
            # Constants do not acquire a bar shift when used as one side of a
            # crossover.  Only series operands are evaluated at both shifts.
            shift = None
        else:
            raw_identity = next(
                (
                    value.get(key)
                    for key in ("ref", "field", "inputId", "name", "id")
                    if isinstance(value.get(key), str) and str(value.get(key)).strip()
                ),
                None,
            )
            if not isinstance(raw_identity, str):
                return None
            identity = raw_identity.strip().lower()
    elif (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    ):
        number = value
        shift = None
    else:
        return None
    return {
        "kind": kind,
        "identity": identity,
        "shift": shift,
        "number": number,
    }


def _rule_predicate_contract(rule: Mapping[str, object]) -> dict[str, object]:
    """Return a deliberately small, fail-closed static predicate contract.

    The digest still binds the complete rule record.  This contract supplies
    the comparison shape that source analysis can actually prove instead of
    accepting a newly pasted digest marker beside stale trading logic.
    """

    expression = rule.get("expression")
    op = (
        str(expression.get("op") or "").strip().lower()
        if isinstance(expression, Mapping)
        else ""
    )
    result: dict[str, object] = {
        "schemaVersion": _RULE_PREDICATE_SCHEMA_VERSION,
        "supported": False,
        "op": op,
        "clauses": [],
    }
    if not isinstance(expression, Mapping):
        return result

    clauses: list[dict[str, object]] = []
    if op in _RULE_PREDICATE_COMPARISON_OPS:
        left = _rule_predicate_operand_contract(expression.get("left"))
        right = _rule_predicate_operand_contract(expression.get("right"))
        if left is None or right is None:
            return result
        clauses.append({"op": op, "left": left, "right": right})
    elif op in {"cross_above", "cross_below"}:
        previous_shift = expression.get("previousShift")
        current_shift = expression.get("currentShift")
        if (
            not isinstance(previous_shift, int)
            or isinstance(previous_shift, bool)
            or not isinstance(current_shift, int)
            or isinstance(current_shift, bool)
        ):
            return result
        previous_left = _rule_predicate_operand_contract(
            expression.get("left"),
            forced_shift=previous_shift,
        )
        previous_right = _rule_predicate_operand_contract(
            expression.get("right"),
            forced_shift=previous_shift,
        )
        current_left = _rule_predicate_operand_contract(
            expression.get("left"),
            forced_shift=current_shift,
        )
        current_right = _rule_predicate_operand_contract(
            expression.get("right"),
            forced_shift=current_shift,
        )
        if any(
            item is None
            for item in (
                previous_left,
                previous_right,
                current_left,
                current_right,
            )
        ):
            return result
        previous_op, current_op = (
            ("<=", ">") if op == "cross_above" else (">=", "<")
        )
        clauses.extend((
            {
                "op": previous_op,
                "left": previous_left,
                "right": previous_right,
            },
            {
                "op": current_op,
                "left": current_left,
                "right": current_right,
            },
        ))
    else:
        return result

    result["supported"] = True
    result["clauses"] = clauses
    return result


def _rule_predicate_contract_valid(value: object) -> bool:
    if not isinstance(value, Mapping) or set(value) != {
        "schemaVersion",
        "supported",
        "op",
        "clauses",
    }:
        return False
    if (
        value.get("schemaVersion") != _RULE_PREDICATE_SCHEMA_VERSION
        or type(value.get("supported")) is not bool
        or not isinstance(value.get("op"), str)
        or not isinstance(value.get("clauses"), list)
    ):
        return False
    clauses = value["clauses"]
    if value["supported"] is not True:
        return clauses == []
    op = value["op"]
    expected_count = 2 if op in {"cross_above", "cross_below"} else 1
    if (
        op not in _RULE_PREDICATE_COMPARISON_OPS | {"cross_above", "cross_below"}
        or len(clauses) != expected_count
    ):
        return False
    for clause in clauses:
        if (
            not isinstance(clause, Mapping)
            or set(clause) != {"op", "left", "right"}
            or clause.get("op") not in _RULE_PREDICATE_COMPARISON_OPS
        ):
            return False
        for side in ("left", "right"):
            operand = clause.get(side)
            if not isinstance(operand, Mapping) or set(operand) != {
                "kind",
                "identity",
                "shift",
                "number",
            }:
                return False
            kind = operand.get("kind")
            identity = operand.get("identity")
            shift = operand.get("shift")
            number = operand.get("number")
            if (
                not isinstance(kind, str)
                or not kind
                or not isinstance(identity, str)
                or not identity
                or (number is None) != (kind != "constant")
                or (kind == "constant" and identity != "#number")
            ):
                return False
            if shift is not None and (
                not isinstance(shift, int) or isinstance(shift, bool)
            ):
                return False
            if number is not None and (
                not isinstance(number, (int, float))
                or isinstance(number, bool)
                or not math.isfinite(float(number))
            ):
                return False
    return True


def _semantic_binding(
    kind: str,
    identity: str,
    value: object,
    *,
    actions: tuple[str, ...] = (),
    predicate: Mapping[str, object] | None = None,
) -> dict[str, object]:
    digest = _sha256(value)
    identifier = f"{kind}:{identity}:{digest}"
    result = {
        "id": identifier,
        "kind": kind,
        "identity": identity,
        "digest": digest,
        "actions": sorted(set(actions)),
    }
    if predicate is not None:
        result["predicate"] = dict(predicate)
    return result


def _recovery_entry_actions(blueprint: Mapping[str, object]) -> tuple[str, ...]:
    """Return the concrete recovery order directions required by the spec."""

    recovery = blueprint.get("recovery")
    scope = blueprint.get("scope")
    if not isinstance(recovery, Mapping) or recovery.get("enabled") is not True:
        return ("entry",)
    enabled_sides = {
        str(side).strip().lower()
        for side in (
            scope.get("enabledSides", []) if isinstance(scope, Mapping) else []
        )
        if str(side).strip().lower() in {"buy", "sell"}
    }
    if not enabled_sides:
        return ("entry",)
    direction = str(recovery.get("direction") or "same").strip().lower()
    if direction == "opposite":
        enabled_sides = {
            "sell" if side == "buy" else "buy" for side in enabled_sides
        }
    elif direction == "both":
        enabled_sides = {"buy", "sell"}
    return tuple(f"entry_{side}" for side in sorted(enabled_sides))


def _entry_side_actions(blueprint: Mapping[str, object]) -> tuple[str, ...]:
    """Return the concrete market direction(s) enabled by the Blueprint."""

    entry = blueprint.get("entry")
    enabled: set[str] = set()
    if isinstance(entry, Mapping):
        for side in ("buy", "sell"):
            record = entry.get(side)
            if isinstance(record, Mapping) and record.get("enabled") is True:
                enabled.add(side)
    if not enabled:
        scope = blueprint.get("scope")
        if isinstance(scope, Mapping):
            enabled.update(
                str(side).strip().lower()
                for side in scope.get("enabledSides", [])
                if str(side).strip().lower() in {"buy", "sell"}
            )
    return (
        tuple(f"entry_{side}" for side in sorted(enabled))
        if enabled
        else ("entry",)
    )


def _rule_trade_actions(
    role: Mapping[str, object],
    fallback_action: str,
) -> tuple[str, ...]:
    """Bind side-specific entry rules to the matching order direction."""

    if fallback_action != "entry":
        return (fallback_action or "initialization",)
    side = str(role.get("side") or "").strip().lower()
    if side in {"buy", "sell"}:
        return (f"entry_{side}",)
    return ("entry",)


def _trade_call_contract(
    risk: Mapping[str, object],
    protection: Mapping[str, object],
) -> dict[str, object]:
    mode = str(risk.get("lotMode") or "").strip().lower()
    volume_ref = str(risk.get("fixedLotInputRef") or "").strip()
    result: dict[str, object] = {
        "schemaVersion": "ea-factory-trade-call-v1",
        "supported": mode == "fixed_lot" and bool(volume_ref),
        "volumeInputRef": volume_ref if mode == "fixed_lot" else "",
        "stopLossRequired": False,
        "stopLossInputRef": "",
        "takeProfitRequired": False,
        "takeProfitInputRef": "",
    }
    for key, required_key, ref_key in (
        ("stopLoss", "stopLossRequired", "stopLossInputRef"),
        ("takeProfit", "takeProfitRequired", "takeProfitInputRef"),
    ):
        record = protection.get(key)
        if not isinstance(record, Mapping):
            result["supported"] = False
            continue
        if record.get("enabled") is not True:
            continue
        input_ref = str(record.get("valueInputRef") or "").strip()
        placement = str(record.get("placementTiming") or "with_entry").strip().lower()
        protection_type = str(record.get("type") or "").strip().lower()
        if not input_ref or placement != "with_entry" or protection_type != "fixed_pips":
            result["supported"] = False
            continue
        result[required_key] = True
        result[ref_key] = input_ref
    return result


def _trade_call_contract_valid(value: object, *, kind: str) -> bool:
    if not isinstance(value, Mapping) or type(value.get("supported")) is not bool:
        return False
    expected = {
        "schemaVersion",
        "supported",
        "volumeInputRef",
        "stopLossRequired",
        "stopLossInputRef",
        "takeProfitRequired",
        "takeProfitInputRef",
    }
    return (
        kind in {"risk_sizing", "protection"}
        and set(value) == expected
        and value.get("schemaVersion") == "ea-factory-trade-call-v1"
        and isinstance(value.get("volumeInputRef"), str)
        and (value.get("supported") is False or bool(value.get("volumeInputRef")))
        and all(
            type(value.get(key)) is bool
            for key in ("stopLossRequired", "takeProfitRequired")
        )
        and all(
            isinstance(value.get(key), str)
            for key in ("stopLossInputRef", "takeProfitInputRef")
        )
        and all(
            not value.get(required_key) or bool(value.get(ref_key))
            for required_key, ref_key in (
                ("stopLossRequired", "stopLossInputRef"),
                ("takeProfitRequired", "takeProfitInputRef"),
            )
        )
    )


def _semantic_bindings(
    blueprint: Mapping[str, object],
    profile: Mapping[str, object],
) -> list[dict[str, object]]:
    """Bind exact executable subtrees, not only their stable record IDs.

    The whole-blueprint marker remains useful as an immutable provenance seal,
    but it is intentionally insufficient on its own.  These independently
    salted markers force generated source to acknowledge the exact canonical
    semantics at the action that consumes them.  Therefore replacing only the
    top-level digest marker cannot make stale code pass after an executable
    Blueprint mutation.
    """

    bindings: list[dict[str, object]] = []

    # The canonical Blueprint is a closed object.  Keep a deterministic
    # lifecycle-bound seal for every section, including non-trading metadata
    # that affects provenance/readiness, so a generator cannot acknowledge a
    # changed whole-document digest while silently retaining stale sections.
    for section_name in _CANONICAL_BLUEPRINT_SECTIONS:
        if section_name in blueprint:
            bindings.append(
                _semantic_binding(
                    "blueprint_section",
                    section_name,
                    blueprint[section_name],
                    actions=("initialization",),
                )
            )

    roles = {
        str(row.get("id")): row
        for row in profile.get("ruleRoles", [])
        if isinstance(row, Mapping) and isinstance(row.get("id"), str)
    }
    rule_records: dict[str, Mapping[str, object]] = {}

    def collect_rule_records(node: object) -> None:
        if isinstance(node, Mapping):
            rule_id = node.get("ruleId")
            if isinstance(rule_id, str) and rule_id.strip():
                rule_records[rule_id.strip()] = node
            for child in node.values():
                collect_rule_records(child)
        elif isinstance(node, (list, tuple)):
            for child in node:
                collect_rule_records(child)

    collect_rule_records(blueprint)
    recovery_entry_actions = _recovery_entry_actions(blueprint)
    for rule_id in sorted(rule_records):
        role = roles.get(rule_id, {})
        role_action = str(role.get("action") or "other")
        actions = {
            "entry": "entry",
            "exit": "exit",
            "management": "management",
            "pending": "pending",
        }.get(role_action)
        binding_actions = (
            recovery_entry_actions
            if role_action == "recovery"
            else _rule_trade_actions(role, actions or "initialization")
        )
        bindings.append(
            _semantic_binding(
                "rule_semantics",
                rule_id,
                rule_records[rule_id],
                actions=binding_actions,
                predicate=_rule_predicate_contract(rule_records[rule_id]),
            )
        )

    indicators = blueprint.get("indicators")
    input_defaults = {
        str(record.get("inputId") or "").strip(): record.get("default")
        for record in (
            blueprint.get("inputs") if isinstance(blueprint.get("inputs"), list) else []
        )
        if isinstance(record, Mapping)
        and isinstance(record.get("inputId"), str)
        and str(record.get("inputId") or "").strip()
    }
    if isinstance(indicators, list):
        for record in indicators:
            if not isinstance(record, Mapping):
                continue
            indicator_id = str(record.get("indicatorId") or "").strip()
            if indicator_id:
                binding = _semantic_binding(
                    "indicator",
                    indicator_id,
                    record,
                    actions=("indicator",),
                )
                binding["spec"] = json.loads(json.dumps(record, ensure_ascii=False))
                binding["inputDefaults"] = dict(input_defaults)
                bindings.append(binding)

    risk = blueprint.get("riskAndSizing")
    protection = blueprint.get("tpSl")
    shared_trade_call = (
        _trade_call_contract(risk, protection)
        if isinstance(risk, Mapping) and isinstance(protection, Mapping)
        else None
    )
    if isinstance(risk, Mapping):
        binding = _semantic_binding(
            "risk_sizing", "root", risk, actions=_entry_side_actions(blueprint)
        )
        binding["tradeCall"] = dict(shared_trade_call or {})
        bindings.append(binding)

    if isinstance(protection, Mapping):
        binding = _semantic_binding(
            "protection", "root", protection, actions=_entry_side_actions(blueprint)
        )
        binding["tradeCall"] = dict(shared_trade_call or {})
        bindings.append(binding)

    management = blueprint.get("orderManagement")
    enabled_features = set(profile.get("enabledManagementFeatures") or [])
    if isinstance(management, Mapping):
        for feature_name in sorted(enabled_features):
            if feature_name == "partialClose":
                continue
            feature = management.get(feature_name)
            if not isinstance(feature, Mapping):
                continue
            action_record = feature.get("action")
            action_kind = (
                str(action_record.get("kind") or "").strip()
                if isinstance(action_record, Mapping)
                else ""
            )
            bindings.append(
                _semantic_binding(
                    "management_feature",
                    feature_name,
                    feature,
                    actions=(action_kind or "management",),
                )
            )
        partial = management.get("partialClose")
        if isinstance(partial, Mapping) and partial.get("enabled") is True:
            bindings.append(
                _semantic_binding(
                    "management_feature",
                    "partialClose",
                    partial,
                    actions=("close_partial",),
                )
            )

    recovery = blueprint.get("recovery")
    if isinstance(recovery, Mapping) and recovery.get("enabled") is True:
        # Active recovery always has bounded entry and basket abort/reset/exit
        # semantics under Blueprint v2.  The same exact digest must therefore
        # participate in both reachable action families.
        bindings.append(
            _semantic_binding(
                "recovery_safety",
                str(recovery.get("mode") or "active"),
                recovery,
                actions=(*recovery_entry_actions, "exit"),
            )
        )

    state_machine = blueprint.get("stateMachine")
    if isinstance(state_machine, list):
        for state in state_machine:
            if not isinstance(state, Mapping):
                continue
            state_id = str(state.get("state") or "").strip()
            if not state_id:
                continue
            actions: set[str] = set()
            transitions = state.get("transitions")
            if isinstance(transitions, list):
                for transition in transitions:
                    if not isinstance(transition, Mapping):
                        continue
                    target = str(transition.get("to") or "").upper()
                    if state_id.upper() == "PENDING" or target == "PENDING":
                        actions.add("pending")
                    refs = transition.get("whenRuleIds")
                    if isinstance(refs, list):
                        for rule_id in refs:
                            role = roles.get(str(rule_id), {})
                            action = str(role.get("action") or "other")
                            actions.add("entry" if action == "recovery" else action)
            actions.discard("other")
            if not actions:
                actions.add("state_decision")
            bindings.append(
                _semantic_binding(
                    "state_transition",
                    state_id,
                    state,
                    actions=tuple(actions),
                )
            )

    test_cases = blueprint.get("testCases")
    if isinstance(test_cases, list):
        for record in test_cases:
            if not isinstance(record, Mapping):
                continue
            case_id = str(record.get("caseId") or "").strip()
            if case_id:
                bindings.append(
                    _semantic_binding(
                        "test_vector",
                        case_id,
                        record,
                        actions=("verification",),
                    )
                )

    pseudocode = blueprint.get("pseudocode")
    if isinstance(pseudocode, Mapping):
        bindings.append(
            _semantic_binding(
                "pseudocode",
                "root",
                pseudocode,
                actions=("initialization",),
            )
        )

    execution = blueprint.get("execution")
    precedence = blueprint.get("precedence")
    if isinstance(execution, Mapping) and isinstance(precedence, list):
        bindings.append(
            _semantic_binding(
                "execution_contract",
                "root",
                {"execution": execution, "precedence": precedence},
                actions=("initialization",),
            )
        )

    if isinstance(bar_semantics := blueprint.get("barSemantics"), Mapping):
        bindings.append(
            _semantic_binding(
                "bar_semantics",
                "root",
                bar_semantics,
                actions=("initialization",),
            )
        )
    return sorted(bindings, key=lambda row: str(row["id"]))


def _record_ids(blueprint: Mapping[str, object], array_key: str, id_key: str) -> list[str]:
    rows = blueprint.get(array_key)
    if not isinstance(rows, list):
        return []
    return sorted({
        str(row.get(id_key)).strip()
        for row in rows
        if isinstance(row, Mapping)
        and isinstance(row.get(id_key), str)
        and str(row.get(id_key)).strip()
    })


def coverage_marker(key: str, identifier: str) -> str:
    if key not in COVERAGE_KEYS or not isinstance(identifier, str) or not identifier:
        raise ValueError("EA Factory coverage marker input is invalid")
    lexical = re.sub(r"[^A-Za-z0-9]+", "_", identifier).strip("_").upper()
    # Keep the complete identifier below conservative MQL4/MQL5 identifier
    # limits. The hash preserves uniqueness after this bounded lexical prefix.
    lexical = lexical[:24] or "ID"
    suffix = hashlib.sha256(f"{key}\0{identifier}".encode("utf-8")).hexdigest()[:10].upper()
    return f"EA_COV_{_MARKER_PREFIX_BY_KEY[key]}_{lexical}_{suffix}"


def build_coverage_requirements(
    blueprint: Mapping[str, object],
    blueprint_digest: str,
) -> dict:
    claimed_blueprint_digest = str(blueprint_digest or "").lower()
    if (
        not isinstance(blueprint, Mapping)
        or not _SHA256_PATTERN.fullmatch(claimed_blueprint_digest)
        or _sha256(blueprint) != claimed_blueprint_digest
    ):
        raise ValueError("EA Factory Blueprint coverage binding is invalid")
    semantic_profile = _semantic_profile(blueprint)
    required_ids = {
        "blueprintDigests": [claimed_blueprint_digest],
        "semanticDigests": [
            str(row["id"])
            for row in semantic_profile["semanticBindings"]
        ],
        "ruleIds": sorted(_rule_ids(blueprint)),
        **{
            key: _record_ids(blueprint, array_key, id_key)
            for key, (array_key, id_key) in _ID_FIELD_BY_KEY.items()
        },
    }
    required_markers = {
        key: [
            {"id": identifier, "marker": coverage_marker(key, identifier)}
            for identifier in required_ids[key]
        ]
        for key in COVERAGE_KEYS
    }
    result = {
        "schemaVersion": REQUIREMENTS_SCHEMA_VERSION,
        "eaBlueprintDigest": claimed_blueprint_digest,
        "requiredIds": required_ids,
        "requiredMarkers": required_markers,
        "semanticProfile": semantic_profile,
    }
    result["requirementsDigest"] = _sha256(result)
    return result


def coverage_requirements_valid(
    value: object,
    blueprint: Mapping[str, object],
    blueprint_digest: str,
) -> bool:
    try:
        expected = build_coverage_requirements(blueprint, blueprint_digest)
    except (TypeError, ValueError):
        return False
    return isinstance(value, dict) and value == expected


def _strip_comments_and_strings(source: str) -> str:
    """Remove comment/string payloads while preserving executable identifiers."""

    result: list[str] = []
    index = 0
    state = "code"
    quote = ""
    while index < len(source):
        char = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if state == "code":
            if char == "/" and following == "/":
                result.extend("  ")
                index += 2
                state = "line_comment"
                continue
            if char == "/" and following == "*":
                result.extend("  ")
                index += 2
                state = "block_comment"
                continue
            if char in {'"', "'"}:
                quote = char
                result.append(" ")
                index += 1
                state = "string"
                continue
            result.append(char)
            index += 1
            continue
        if state == "line_comment":
            result.append("\n" if char == "\n" else " ")
            index += 1
            if char == "\n":
                state = "code"
            continue
        if state == "block_comment":
            if char == "*" and following == "/":
                result.extend("  ")
                index += 2
                state = "code"
            else:
                result.append("\n" if char == "\n" else " ")
                index += 1
            continue
        if state == "string":
            if char == "\\" and following:
                result.extend("  ")
                index += 2
            elif char == quote:
                result.append(" ")
                index += 1
                state = "code"
            else:
                result.append("\n" if char == "\n" else " ")
                index += 1
    return "".join(result)


def _matching_brace(source: str, opening_index: int) -> int | None:
    depth = 0
    for index in range(opening_index, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    return None


def _c_like_functions(source: str) -> list[dict[str, object]]:
    """Return bounded C-like function bodies from comment/string-free source."""

    functions: list[dict[str, object]] = []
    occupied_until = -1
    header_pattern = re.compile(
        r"\b([A-Za-z_][A-Za-z0-9_]{0,79})\s*"
        r"\((?P<parameters>[^;{}]{0,1000})\)\s*\{"
    )
    for match in header_pattern.finditer(source):
        name = match.group(1)
        if name in _CONTROL_NAMES or match.start() < occupied_until:
            continue
        opening = match.end() - 1
        closing = _matching_brace(source, opening)
        if closing is None:
            continue
        functions.append({
            "name": name,
            "start": match.start(),
            "bodyStart": opening + 1,
            "end": closing,
            "body": source[opening + 1:closing],
            "parameters": match.group("parameters"),
        })
        occupied_until = closing + 1
    return functions


def _reachable_function_names(
    functions: list[dict[str, object]],
    roots: set[str],
) -> set[str]:
    by_name = {str(row["name"]): row for row in functions}
    reachable = {name for name in roots if name in by_name}
    pending = list(reachable)
    while pending:
        name = pending.pop()
        body = str(by_name[name]["body"])
        for candidate in by_name:
            if candidate not in reachable and re.search(
                rf"\b{re.escape(candidate)}\s*\(", body
            ):
                reachable.add(candidate)
                pending.append(candidate)
    return reachable


def _marker_is_declaration(source: str, start: int, end: int) -> bool:
    line_start = source.rfind("\n", 0, start) + 1
    line_end = source.find("\n", end)
    if line_end < 0:
        line_end = len(source)
    prefix = source[line_start:start]
    suffix = source[end:line_end]
    if re.search(r"#\s*define\s*$", prefix):
        return True
    if re.search(
        r"(?:\bconst\s+)?\b(?:bool|int|long|double|float|string|datetime|uint|ulong)\s+$",
        prefix,
        re.IGNORECASE,
    ):
        return True
    # Pine permits an optional type followed by a top-level assignment.
    if re.fullmatch(r"\s*(?:var\s+)?(?:bool\s+)?", prefix) and re.match(
        r"\s*(?::=|=)", suffix
    ):
        return True
    return False


def _function_for_position(
    functions: list[dict[str, object]], position: int
) -> dict[str, object] | None:
    for row in functions:
        if int(row["bodyStart"]) <= position < int(row["end"]):
            return row
    return None


def _scope_has_controlled_comparison(scope: str) -> bool:
    return bool(
        _COMPARISON_PATTERN.search(scope)
        and re.search(r"\b(?:if|switch|return|bool)\b|(?::=|=)", scope)
    )


def _scope_has_shift(scope: str, shift: int) -> bool:
    return bool(
        re.search(rf"(?:\[|\()\s*{shift}\s*(?:\]|\))", scope)
        or re.search(rf",\s*{shift}\s*(?:,|\))", scope)
    )


def _marker_participates_in_expression(scope: str, marker: str) -> bool:
    escaped = re.escape(marker)
    return bool(
        re.search(rf"\bif\s*\([^)]*\b{escaped}\b[^)]*\)", scope)
        or re.search(rf"\breturn\b[^;\n]*\b{escaped}\b", scope)
        or re.search(rf"(?::=|=)[^;\n]*\b{escaped}\b", scope)
    )


def _marker_controls_returned_predicate(scope: str, marker: str) -> bool:
    """Reject metadata assignments that do not influence a helper result."""

    escaped = re.escape(marker)
    if re.search(rf"\breturn\b[^;\n]*\b{escaped}\b", scope):
        return True
    return any(
        re.search(rf"\b{escaped}\b", condition)
        and re.search(r"\breturn\b", body)
        for condition, body in _c_if_regions(scope)
    )


def _marker_predicate_fragments(
    scope: str,
    marker: str,
    *,
    target_platform: str,
) -> list[str]:
    """Extract only expressions in which the marker itself participates."""

    escaped = re.escape(marker)
    fragments: list[str] = []
    if target_platform != "tradingview":
        fragments.extend(
            match.group("expression")
            for match in re.finditer(
                r"\breturn\b(?P<expression>[^;\n]+)",
                scope,
            )
            if re.search(rf"\b{escaped}\b", match.group("expression"))
        )
        fragments.extend(
            condition
            for condition, _body in _c_if_regions(scope)
            if re.search(rf"\b{escaped}\b", condition)
        )
    for line in scope.splitlines():
        if not re.search(rf"\b{escaped}\b", line):
            continue
        assignment = re.search(r"(?::=|=)(?P<expression>[^;\n]+)", line)
        if (
            assignment is not None
            and re.search(rf"\b{escaped}\b", assignment.group("expression"))
        ):
            fragments.append(assignment.group("expression"))
    return list(dict.fromkeys(fragment.strip() for fragment in fragments if fragment.strip()))


def _source_atom_evidence(value: str) -> dict[str, object] | None:
    text = re.sub(r"\s+", "", str(value or ""))
    if re.fullmatch(_SOURCE_NUMBER_PATTERN, text):
        try:
            number = float(text)
        except ValueError:
            return None
        return {
            "base": "#number",
            "shift": None,
            "number": number,
        } if math.isfinite(number) else None
    indexed = re.fullmatch(
        r"(?P<base>[A-Za-z_][A-Za-z0-9_.]*)\[(?P<shift>-?\d+)\]",
        text,
    )
    if indexed:
        return {
            "base": indexed.group("base").lower(),
            "shift": int(indexed.group("shift")),
            "number": None,
        }
    shifted_call = re.fullmatch(
        r"(?P<base>[A-Za-z_][A-Za-z0-9_.]*)\((?P<shift>-?\d+)\)",
        text,
    )
    if shifted_call:
        return {
            "base": shifted_call.group("base").lower(),
            "shift": int(shifted_call.group("shift")),
            "number": None,
        }
    identifier = re.fullmatch(
        r"(?P<base>[A-Za-z_][A-Za-z0-9_.]*)(?:\([^(){};]*\))?",
        text,
    )
    if identifier:
        return {
            "base": identifier.group("base").lower(),
            "shift": None,
            "number": None,
        }
    return None


def _source_comparison_clauses(fragment: str) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for match in _SOURCE_COMPARISON_CLAUSE_PATTERN.finditer(fragment):
        left = _source_atom_evidence(match.group("left"))
        right = _source_atom_evidence(match.group("right"))
        if left is None or right is None:
            continue
        result.append({
            "op": match.group("op"),
            "left": left,
            "right": right,
        })
    return result


def _normalized_predicate_identity(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _predicate_operand_key(kind: object, identity: object) -> str:
    return f"{str(kind or '').strip().lower()}:{str(identity or '').strip().lower()}"


def _normalized_source_token(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _indicator_parameter_matches(
    expression: str,
    expected: object,
    input_defaults: Mapping[str, object],
) -> bool:
    text = _strip_balanced_outer_parentheses(expression)
    if isinstance(expected, Mapping):
        input_ref = str(expected.get("inputRef") or "").strip()
        if input_ref:
            if _normalized_source_token(text) == _normalized_source_token(input_ref):
                return True
            expected = input_defaults.get(input_ref)
        elif "value" in expected:
            expected = expected.get("value")
        else:
            return False
    if isinstance(expected, bool) or expected is None:
        return False
    if isinstance(expected, (int, float)):
        observed = _source_number(text)
        return bool(
            observed is not None
            and math.isclose(
                float(observed),
                float(expected),
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
        )
    return _normalized_source_token(text) == _normalized_source_token(expected)


def _indicator_timeframe_matches(expression: str, expected: object) -> bool:
    observed = _normalized_source_token(_strip_balanced_outer_parentheses(expression))
    timeframe = _normalized_source_token(expected)
    if timeframe in {"", "signal", "current", "chart"}:
        return observed in {"0", "period", "periodcurrent"}
    return observed in {timeframe, f"period{timeframe}"}


def _indicator_applied_price_matches(
    expression: str,
    expected: object,
    *,
    pine: bool = False,
) -> bool:
    observed = _normalized_source_token(_strip_balanced_outer_parentheses(expression))
    price = _normalized_source_token(expected)
    if pine:
        pine_prices = {
            "close": {"close"},
            "open": {"open"},
            "high": {"high"},
            "low": {"low"},
            "median": {"hl2"},
            "typical": {"hlc3"},
            "weighted": {"ohlc4"},
        }
        return observed in pine_prices.get(price, {price})
    return observed == f"price{price}"


def _indicator_call_arguments(source: str, call_pattern: str) -> list[list[str]]:
    return [arguments for _start, arguments in _call_argument_rows(source, call_pattern)]


def _mql_indicator_arguments_match(
    call_name: str,
    arguments: list[str],
    spec: Mapping[str, object],
    input_defaults: Mapping[str, object],
) -> bool:
    kind = _normalized_source_token(spec.get("kind"))
    parameters = spec.get("parameters")
    if not isinstance(parameters, Mapping):
        return False
    timeframe = spec.get("timeframe")
    applied_price = spec.get("appliedPrice")
    normalized_call = call_name.lower()
    ma_methods = {
        "ema": "modeema",
        "sma": "modesma",
        "smma": "modesmma",
        "lwma": "modelwma",
        "wma": "modelwma",
    }
    if kind in ma_methods:
        if normalized_call != "ima" or len(arguments) not in {6, 7}:
            return False
        if not (
            _indicator_timeframe_matches(arguments[1], timeframe)
            and _indicator_parameter_matches(
                arguments[2], parameters.get("period"), input_defaults
            )
            and _source_number(arguments[3]) == 0.0
            and _normalized_source_token(arguments[4]) == ma_methods[kind]
            and _indicator_applied_price_matches(arguments[5], applied_price)
        ):
            return False
        return len(arguments) == 6 or _normalized_source_token(arguments[6]) == "shift"
    if kind == "rsi":
        return bool(
            normalized_call == "irsi"
            and len(arguments) in {4, 5}
            and _indicator_timeframe_matches(arguments[1], timeframe)
            and _indicator_parameter_matches(
                arguments[2], parameters.get("period"), input_defaults
            )
            and _indicator_applied_price_matches(arguments[3], applied_price)
            and (
                len(arguments) == 4
                or _normalized_source_token(arguments[4]) == "shift"
            )
        )
    if kind == "atr":
        return bool(
            normalized_call == "iatr"
            and len(arguments) in {3, 4}
            and _indicator_timeframe_matches(arguments[1], timeframe)
            and _indicator_parameter_matches(
                arguments[2], parameters.get("period"), input_defaults
            )
            and (
                len(arguments) == 3
                or _normalized_source_token(arguments[3]) == "shift"
            )
        )
    # Unknown/custom indicator families remain fail-closed until their exact
    # call contract is modeled.  A suggestive helper name or generic i* call is
    # not evidence that the signed Blueprint indicator was implemented.
    return False


def _mql_indicator_function_matches_binding(
    source: str,
    function_body: str,
    binding: Mapping[str, object],
) -> bool:
    spec = binding.get("spec")
    input_defaults = binding.get("inputDefaults")
    if not isinstance(spec, Mapping) or not isinstance(input_defaults, Mapping):
        return False
    kind = _normalized_source_token(spec.get("kind"))
    call_by_kind = {
        "ema": "iMA",
        "sma": "iMA",
        "smma": "iMA",
        "lwma": "iMA",
        "wma": "iMA",
        "rsi": "iRSI",
        "atr": "iATR",
    }
    call_name = call_by_kind.get(kind)
    if not call_name:
        return False
    direct_calls = _indicator_call_arguments(
        function_body,
        rf"\breturn\s+{re.escape(call_name)}",
    )
    if any(
        _mql_indicator_arguments_match(call_name, arguments, spec, input_defaults)
        for arguments in direct_calls
    ):
        return True

    # MT5 helpers commonly return one CopyBuffer value from a handle created in
    # OnInit.  Bind the exact handle used by this helper back to its exact
    # indicator constructor before accepting the semantic alias.
    for _copy_start, copy_arguments in _call_argument_rows(
        function_body,
        r"\bCopyBuffer",
    ):
        if len(copy_arguments) < 5:
            continue
        handle = _strip_balanced_outer_parentheses(copy_arguments[0]).strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", handle):
            continue
        handle_calls = _indicator_call_arguments(
            source,
            rf"\b{re.escape(handle)}\s*=\s*{re.escape(call_name)}",
        )
        if any(
            _mql_indicator_arguments_match(call_name, arguments, spec, input_defaults)
            for arguments in handle_calls
        ):
            return True
    return False


def _pine_indicator_line_matches_binding(
    line: str,
    binding: Mapping[str, object],
) -> bool:
    spec = binding.get("spec")
    input_defaults = binding.get("inputDefaults")
    if not isinstance(spec, Mapping) or not isinstance(input_defaults, Mapping):
        return False
    kind = _normalized_source_token(spec.get("kind"))
    function_by_kind = {
        "ema": "ema",
        "sma": "sma",
        "smma": "rma",
        "lwma": "wma",
        "wma": "wma",
        "rsi": "rsi",
        "atr": "atr",
    }
    function_name = function_by_kind.get(kind)
    if not function_name:
        return False
    calls = _indicator_call_arguments(
        line,
        rf"\bta\s*\.\s*{re.escape(function_name)}",
    )
    parameters = spec.get("parameters")
    if not isinstance(parameters, Mapping):
        return False
    for arguments in calls:
        if kind == "atr":
            if len(arguments) == 1 and _indicator_parameter_matches(
                arguments[0], parameters.get("period"), input_defaults
            ):
                return True
            continue
        if len(arguments) != 2:
            continue
        if (
            _indicator_applied_price_matches(
                arguments[0], spec.get("appliedPrice"), pine=True
            )
            and _indicator_parameter_matches(
                arguments[1], parameters.get("period"), input_defaults
            )
        ):
            return True
    return False


def _semantic_indicator_operand_aliases(
    source: str,
    functions: list[dict[str, object]],
    *,
    target_platform: str,
    semantic_bindings: Mapping[str, Mapping[str, object]],
    semantic_markers: Mapping[str, str],
) -> dict[str, tuple[str, ...]]:
    """Bind source aliases to one unambiguous indicator semantic marker."""

    indicator_rows = [
        binding
        for binding in semantic_bindings.values()
        if binding.get("kind") == "indicator"
        and isinstance(binding.get("id"), str)
        and isinstance(binding.get("identity"), str)
    ]
    indicator_marker_tokens = {
        semantic_markers.get(str(binding["id"]), "") for binding in indicator_rows
    } - {""}
    result: dict[str, set[str]] = {}
    for binding in indicator_rows:
        marker = semantic_markers.get(str(binding["id"]), "")
        if not marker:
            continue
        key = _predicate_operand_key("indicator", binding["identity"])
        aliases = result.setdefault(key, set())
        if target_platform == "tradingview":
            for line in source.splitlines():
                if (
                    not re.search(rf"\b{re.escape(marker)}\b", line)
                    or not _INDICATOR_PATTERN.search(line)
                    or not _pine_indicator_line_matches_binding(line, binding)
                    or sum(
                        bool(re.search(rf"\b{re.escape(token)}\b", line))
                        for token in indicator_marker_tokens
                    )
                    != 1
                ):
                    continue
                assignment = re.match(
                    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?::=|=)",
                    line,
                )
                if assignment:
                    aliases.add(_normalized_predicate_identity(assignment.group(1)))
            continue

        for function in functions:
            body = strip_statically_dead_mql_regions(
                str(function.get("body") or "")
            )
            if (
                body is None
                or not re.search(rf"\b{re.escape(marker)}\b", body)
                or not _INDICATOR_PATTERN.search(body)
                or not _mql_indicator_function_matches_binding(source, body, binding)
                or not _marker_controls_returned_predicate(body, marker)
                or sum(
                    bool(re.search(rf"\b{re.escape(token)}\b", body))
                    for token in indicator_marker_tokens
                )
                != 1
            ):
                continue
            function_name = _normalized_predicate_identity(function.get("name"))
            if function_name:
                aliases.add(function_name)
    return {
        key: tuple(sorted(alias for alias in aliases if alias))
        for key, aliases in result.items()
    }


def semantic_indicator_operand_aliases_for_source(
    source: str,
    semantic_profile: object,
    semantic_marker_rows: object,
    *,
    target_platform: str,
) -> dict[str, tuple[str, ...]]:
    """Derive unambiguous indicator aliases from signed semantic marker uses.

    This public wrapper is shared by EA and Indicator coverage.  Any malformed,
    missing, ambiguous, comment-only, or declaration-only binding returns an
    empty mapping so callers cannot fall back to trusting a suggestive name.
    """

    platform = str(target_platform or "").strip().lower()
    if (
        not isinstance(source, str)
        or len(source) > 1_000_000
        or platform not in _SUPPORTED_PLATFORMS
        or not isinstance(semantic_profile, Mapping)
        or not isinstance(semantic_marker_rows, list)
    ):
        return {}
    binding_rows = semantic_profile.get("semanticBindings")
    if not isinstance(binding_rows, list):
        return {}
    indicator_bindings: dict[str, Mapping[str, object]] = {}
    expected_keys: set[str] = set()
    for row in binding_rows:
        if not isinstance(row, Mapping):
            return {}
        if row.get("kind") != "indicator":
            continue
        binding_id = row.get("id")
        identity = row.get("identity")
        if (
            not isinstance(binding_id, str)
            or not binding_id
            or binding_id in indicator_bindings
            or not isinstance(identity, str)
            or not identity.strip()
        ):
            return {}
        key = _predicate_operand_key("indicator", identity)
        if key in expected_keys:
            return {}
        expected_keys.add(key)
        indicator_bindings[binding_id] = row
    if not indicator_bindings:
        return {}

    marker_by_id: dict[str, str] = {}
    for row in semantic_marker_rows:
        if not isinstance(row, Mapping) or set(row) != {"id", "marker"}:
            return {}
        identifier = row.get("id")
        marker = row.get("marker")
        if (
            not isinstance(identifier, str)
            or identifier in marker_by_id
            or not isinstance(marker, str)
            or marker != coverage_marker("semanticDigests", identifier)
        ):
            return {}
        marker_by_id[identifier] = marker
    if not set(indicator_bindings).issubset(marker_by_id):
        return {}

    lexical_source = _strip_comments_and_strings(source)
    functions = _c_like_functions(lexical_source) if platform != "tradingview" else []
    aliases = _semantic_indicator_operand_aliases(
        lexical_source,
        functions,
        target_platform=platform,
        semantic_bindings=indicator_bindings,
        semantic_markers=marker_by_id,
    )
    if set(aliases) != expected_keys or any(not values for values in aliases.values()):
        return {}
    owner_by_alias: dict[str, str] = {}
    for key, values in aliases.items():
        for alias in values:
            previous_owner = owner_by_alias.setdefault(alias, key)
            if previous_owner != key:
                return {}
    return aliases


def _predicate_operand_alias_candidates(
    expected: Mapping[str, object],
    operand_aliases: Mapping[str, object] | None,
) -> set[str]:
    kind = str(expected.get("kind") or "").strip().lower()
    identity = str(expected.get("identity") or "").strip().lower()
    # Indicator names are not evidence: a function called ``ema_fast`` may
    # calculate the slow series while the signed fast marker is parked in an
    # unused helper.  Indicator operands therefore require an unambiguous
    # marker-derived alias supplied by the source verifier.
    candidates = set() if kind == "indicator" else {
        _normalized_predicate_identity(identity),
        _normalized_predicate_identity(f"{kind}_{identity}"),
    } - {""}
    if not isinstance(operand_aliases, Mapping):
        return candidates
    for alias_key in (_predicate_operand_key(kind, identity), identity):
        values = operand_aliases.get(alias_key)
        if isinstance(values, str):
            values = (values,)
        if not isinstance(values, (list, tuple, set, frozenset)):
            continue
        candidates.update(
            normalized
            for normalized in (
                _normalized_predicate_identity(value)
                for value in values
                if isinstance(value, str) and len(value) <= 160
            )
            if normalized
        )
    return candidates


def _predicate_operand_matches(
    expected: Mapping[str, object],
    observed: Mapping[str, object],
    operand_aliases: Mapping[str, object] | None,
) -> bool:
    if expected.get("shift") != observed.get("shift"):
        return False
    expected_number = expected.get("number")
    observed_number = observed.get("number")
    if expected_number is None:
        return bool(
            observed_number is None
            and _normalized_predicate_identity(observed.get("base"))
            in _predicate_operand_alias_candidates(expected, operand_aliases)
        )
    return bool(
        expected.get("kind") == "constant"
        and expected.get("identity") == "#number"
        and observed.get("base") == "#number"
        and observed_number is not None
        and math.isclose(
            float(expected_number),
            float(observed_number),
            rel_tol=1e-12,
            abs_tol=1e-12,
        )
    )


def _predicate_operand_aliases_unambiguous(
    clauses: list[object],
    operand_aliases: Mapping[str, object] | None,
) -> bool:
    owner_by_alias: dict[str, str] = {}
    for clause in clauses:
        if not isinstance(clause, Mapping):
            return False
        for side in ("left", "right"):
            operand = clause.get(side)
            if not isinstance(operand, Mapping) or operand.get("kind") == "constant":
                continue
            owner = _predicate_operand_key(
                operand.get("kind"), operand.get("identity")
            )
            for alias in _predicate_operand_alias_candidates(operand, operand_aliases):
                previous_owner = owner_by_alias.setdefault(alias, owner)
                if previous_owner != owner:
                    return False
    return True


def _predicate_clause_matches(
    expected: Mapping[str, object],
    observed: Mapping[str, object],
    operand_aliases: Mapping[str, object] | None,
) -> bool:
    return bool(
        expected.get("op") == observed.get("op")
        and isinstance(expected.get("left"), Mapping)
        and isinstance(expected.get("right"), Mapping)
        and isinstance(observed.get("left"), Mapping)
        and isinstance(observed.get("right"), Mapping)
        and _predicate_operand_matches(
            expected["left"], observed["left"], operand_aliases
        )
        and _predicate_operand_matches(
            expected["right"], observed["right"], operand_aliases
        )
    )


def rule_predicate_expression_supported(
    expression: str,
    contract: object,
    *,
    operand_aliases: Mapping[str, object] | None = None,
) -> bool:
    """Verify one expression against the same fail-closed EA predicate matcher."""

    if (
        not isinstance(expression, str)
        or not expression
        or len(expression) > 8192
        or not _rule_predicate_contract_valid(contract)
        or not isinstance(contract, Mapping)
        or contract.get("supported") is not True
    ):
        return False
    expected_clauses = contract.get("clauses")
    if (
        not isinstance(expected_clauses, list)
        or not _predicate_operand_aliases_unambiguous(
            expected_clauses,
            operand_aliases,
        )
    ):
        return False
    # Predicate evidence must be the exact positive conjunction represented by
    # the Blueprint contract.  Merely finding the expected comparisons inside
    # ``... || true``, ``!(...)`` or a ternary is not semantic evidence.
    if (
        re.search(r"\|\||\bor\b|\bnot\b|\?", expression, re.IGNORECASE)
        or re.search(r"(?<![=!<>])!(?!=)", expression)
        or re.search(r"(?<!&)&(?!&)|(?<!\|)\|(?!\|)|\^", expression)
        or re.search(r"\b(?:true|false)\b", expression, re.IGNORECASE)
    ):
        return False
    comparison_matches = list(_SOURCE_COMPARISON_CLAUSE_PATTERN.finditer(expression))
    # Additional positive-conjunction guards (for example OrdersTotal() > 0)
    # are legitimate execution safety checks.  They may not replace any
    # contract clause, but they also must not make an otherwise exact rule
    # fail merely because the branch is more restrictive.
    if len(comparison_matches) < len(expected_clauses):
        return False
    # Every top-level conjunct must itself be either a coverage marker or a
    # positive comparison.  This admits real safety guards whose operands use
    # arithmetic (which the exact atom parser intentionally does not try to
    # evaluate), while rejecting marker sinks such as ``marker && DoNothing()``.
    conjuncts = re.split(r"&&|\band\b", expression, flags=re.IGNORECASE)
    if not conjuncts or any(
        not (
            re.fullmatch(
                r"EA_COV_[A-Z0-9_]{1,120}",
                _strip_balanced_outer_parentheses(term).strip(),
                flags=re.IGNORECASE,
            )
            or _COMPARISON_PATTERN.search(term)
        )
        for term in conjuncts
    ):
        return False
    if any(_condition_statically_false(term) for term in conjuncts):
        return False
    observed = [
        {
            "op": match.group("op"),
            "left": _source_atom_evidence(match.group("left")),
            "right": _source_atom_evidence(match.group("right")),
        }
        for match in comparison_matches
    ]
    if any(row["left"] is None or row["right"] is None for row in observed):
        return False
    if len(expected_clauses) == 2:
        for first_index, first in enumerate(observed):
            if not _predicate_clause_matches(
                expected_clauses[0], first, operand_aliases
            ):
                continue
            for second in observed[first_index + 1:]:
                if not _predicate_clause_matches(
                    expected_clauses[1], second, operand_aliases
                ):
                    continue
                first_left = first.get("left")
                first_right = first.get("right")
                second_left = second.get("left")
                second_right = second.get("right")
                if (
                    isinstance(first_left, Mapping)
                    and isinstance(first_right, Mapping)
                    and isinstance(second_left, Mapping)
                    and isinstance(second_right, Mapping)
                    and first_left.get("base") == second_left.get("base")
                    and first_right.get("base") == second_right.get("base")
                ):
                    return True
        return False
    if len(expected_clauses) != 1:
        return False
    for candidate in observed:
        if not _predicate_clause_matches(
            expected_clauses[0], candidate, operand_aliases
        ):
            continue
        left = candidate.get("left")
        right = candidate.get("right")
        if not isinstance(left, Mapping) or not isinstance(right, Mapping):
            continue
        same_pair = [
            clause
            for clause in observed
            if isinstance(clause.get("left"), Mapping)
            and isinstance(clause.get("right"), Mapping)
            and clause["left"].get("base") == left.get("base")
            and clause["right"].get("base") == right.get("base")
        ]
        # A single-comparison rule must not be satisfied by one half of a
        # stale closed-bar crossover that happens to use the same operator.
        if len(same_pair) == 1:
            return True
    return False


def _rule_predicate_supported(
    scope: str,
    marker: str,
    contract: object,
    *,
    target_platform: str,
    operand_aliases: Mapping[str, object] | None,
) -> bool:
    """Prove a supported rule's comparison shape in the marker predicate."""

    return any(
        rule_predicate_expression_supported(
            fragment,
            contract,
            operand_aliases=operand_aliases,
        )
        for fragment in _marker_predicate_fragments(
            scope,
            marker,
            target_platform=target_platform,
        )
    )


def _matching_parenthesis(source: str, opening_index: int) -> int | None:
    depth = 0
    for index in range(opening_index, len(source)):
        if source[index] == "(":
            depth += 1
        elif source[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    return None


def _c_if_regions(source: str) -> list[tuple[str, str]]:
    """Extract C-like if conditions and their immediate guarded bodies."""

    regions: list[tuple[str, str]] = []
    for match in re.finditer(r"\bif\s*\(", source):
        opening = source.find("(", match.start(), match.end())
        closing = _matching_parenthesis(source, opening)
        if closing is None:
            continue
        cursor = closing + 1
        while cursor < len(source) and source[cursor].isspace():
            cursor += 1
        if cursor >= len(source):
            continue
        if source[cursor] == "{":
            body_end = _matching_brace(source, cursor)
            if body_end is None:
                continue
            body = source[cursor + 1:body_end]
        else:
            body_end = source.find(";", cursor)
            if body_end < 0:
                body_end = source.find("\n", cursor)
            if body_end < 0:
                body_end = len(source)
            body = source[cursor:body_end]
        regions.append((source[opening + 1:closing], body))
    return regions


def _expanded_fragment_source(
    fragment: str,
    functions: list[dict[str, object]],
) -> str:
    """Append only helper bodies transitively called by a guarded fragment."""

    by_name = {str(row["name"]): row for row in functions}
    expanded = [fragment]
    seen: set[str] = set()
    pending = [
        name
        for name in by_name
        if re.search(rf"\b{re.escape(name)}\s*\(", fragment)
    ]
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        body = str(by_name[name]["body"])
        expanded.append(body)
        for candidate in by_name:
            if candidate not in seen and re.search(
                rf"\b{re.escape(candidate)}\s*\(", body
            ):
                pending.append(candidate)
    return "\n".join(expanded)


def _strip_balanced_outer_parentheses(value: str) -> str:
    result = str(value or "").strip()
    while result.startswith("("):
        closing = _matching_parenthesis(result, 0)
        if closing != len(result) - 1:
            break
        result = result[1:-1].strip()
    return result


def _split_top_level_arguments(value: str) -> list[str] | None:
    arguments: list[str] = []
    start = 0
    stack: list[str] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for index, character in enumerate(value):
        if character in "([{":
            stack.append(character)
        elif character in ")]}":
            if not stack or stack[-1] != pairs[character]:
                return None
            stack.pop()
        elif character == "," and not stack:
            arguments.append(value[start:index].strip())
            start = index + 1
    if stack:
        return None
    arguments.append(value[start:].strip())
    return arguments


def _call_argument_rows(
    source: str,
    call_pattern: str,
) -> list[tuple[int, list[str]]]:
    rows: list[tuple[int, list[str]]] = []
    for match in re.finditer(rf"{call_pattern}\s*\(", source, re.IGNORECASE):
        opening = source.find("(", match.start(), match.end())
        closing = _matching_parenthesis(source, opening)
        if closing is None:
            continue
        arguments = _split_top_level_arguments(source[opening + 1:closing])
        if arguments is not None:
            rows.append((match.start(), arguments))
    return rows


def _function_parameter_names(function: Mapping[str, object]) -> list[str] | None:
    parameters = _split_top_level_arguments(str(function.get("parameters") or ""))
    if parameters is None:
        return None
    if parameters == [""]:
        return []
    result: list[str] = []
    for parameter in parameters:
        declaration = parameter.split("=", 1)[0]
        identifiers = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", declaration)
        if not identifiers:
            return None
        result.append(identifiers[-1])
    return result


def _latest_member_assignment(
    source: str,
    object_name: str,
    member_name: str,
) -> str | None:
    matches = list(re.finditer(
        rf"(?m)\b{re.escape(object_name)}\s*\.\s*{re.escape(member_name)}"
        rf"\s*=(?!=)\s*(?P<expression>[^;\n]+)",
        source,
        re.IGNORECASE,
    ))
    return matches[-1].group("expression").strip() if matches else None


def _expression_origin_identifiers(
    expression: str,
    source_prefix: str,
    parameter_environment: Mapping[str, str] | None = None,
    *,
    seen: set[str] | None = None,
) -> set[str]:
    """Resolve bounded local/parameter aliases to their originating inputs."""

    environment = {
        str(key).lower(): str(value)
        for key, value in (parameter_environment or {}).items()
    }
    seen = set() if seen is None else set(seen)
    if len(seen) > 16:
        return set()
    text = _strip_balanced_outer_parentheses(expression)
    if not text or len(text) > 4096:
        return set()
    origins: set[str] = set()
    for identifier in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text):
        lowered = identifier.lower()
        if lowered in seen:
            continue
        if lowered in environment:
            origins.update(_expression_origin_identifiers(
                environment[lowered],
                source_prefix,
                environment,
                seen=seen | {lowered},
            ))
            continue
        assignment = _latest_simple_assignment(source_prefix, identifier)
        if assignment is not None:
            origins.update(_expression_origin_identifiers(
                assignment,
                source_prefix,
                environment,
                seen=seen | {lowered},
            ))
            continue
        origins.add(lowered)
    return origins


def _resolve_trade_expression(
    expression: str,
    source_prefix: str,
    parameter_environment: Mapping[str, str] | None = None,
    *,
    seen: set[str] | None = None,
) -> str | None:
    """Resolve only bounded parameter/local aliases, preserving arithmetic.

    Keeping the arithmetic tree intact is important: identifier provenance
    alone cannot distinguish ``fixed_lot`` from ``fixed_lot*0+999``.
    """

    environment = {
        str(key).lower(): str(value)
        for key, value in (parameter_environment or {}).items()
    }
    seen = set() if seen is None else set(seen)
    text = _strip_balanced_outer_parentheses(expression)
    if not text or len(text) > 4096 or len(seen) > 16:
        return None

    exact_identifier = re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", text)
    if exact_identifier:
        name = exact_identifier.group(0)
        lowered = name.lower()
        if lowered in seen:
            return None
        replacement = environment.get(lowered)
        if replacement is None:
            replacement = _latest_simple_assignment(source_prefix, name)
        if replacement is None:
            return name
        return _resolve_trade_expression(
            replacement,
            source_prefix,
            environment,
            seen=seen | {lowered},
        )

    failed = False

    def replace_identifier(match: re.Match[str]) -> str:
        nonlocal failed
        name = match.group(0)
        lowered = name.lower()
        if lowered in seen:
            failed = True
            return name
        replacement = environment.get(lowered)
        if replacement is None:
            replacement = _latest_simple_assignment(source_prefix, name)
        if replacement is None:
            return name
        resolved = _resolve_trade_expression(
            replacement,
            source_prefix,
            environment,
            seen=seen | {lowered},
        )
        if resolved is None:
            failed = True
            return name
        return f"({resolved})"

    resolved = re.sub(r"[A-Za-z_][A-Za-z0-9_]*", replace_identifier, text)
    if failed or len(resolved) > 8192:
        return None
    return _strip_balanced_outer_parentheses(resolved)


def _entry_call_evidence(
    side: str,
    volume_expression: str,
    stop_expression: str,
    take_expression: str,
    source_prefix: str,
    parameter_environment: Mapping[str, str],
) -> dict[str, object]:
    resolved_volume = _resolve_trade_expression(
        volume_expression,
        source_prefix,
        parameter_environment,
    )
    resolved_stop = _resolve_trade_expression(
        stop_expression,
        source_prefix,
        parameter_environment,
    )
    resolved_take = _resolve_trade_expression(
        take_expression,
        source_prefix,
        parameter_environment,
    )
    return {
        "side": side,
        "volumeExpression": resolved_volume or "",
        "stopExpression": resolved_stop or "",
        "takeExpression": resolved_take or "",
        "volumeOrigins": sorted(_expression_origin_identifiers(
            volume_expression,
            source_prefix,
            parameter_environment,
        )),
        "stopOrigins": sorted(_expression_origin_identifiers(
            stop_expression,
            source_prefix,
            parameter_environment,
        )),
        "takeOrigins": sorted(_expression_origin_identifiers(
            take_expression,
            source_prefix,
            parameter_environment,
        )),
    }


def _mql_entry_call_evidence(
    fragment: str,
    functions: list[dict[str, object]],
    *,
    parameter_environment: Mapping[str, str] | None = None,
    visited: set[str] | None = None,
    source_context_prefix: str = "",
) -> list[dict[str, object]]:
    """Extract actual reachable entry direction/volume/SL/TP call evidence.

    This intentionally recognizes only the normal MT4 OrderSend, MT5 CTrade
    Buy/Sell or PositionOpen, and raw MqlTradeRequest forms.  Unknown wrappers
    and dynamic request construction fail closed instead of becoming textual
    proof of Blueprint execution.
    """

    environment = dict(parameter_environment or {})
    visited = set() if visited is None else set(visited)
    if len(visited) > 16:
        return []
    live_fragment = strip_statically_dead_mql_regions(fragment)
    if live_fragment is None:
        return []
    evidence: list[dict[str, object]] = []

    for call_start, arguments in _call_argument_rows(live_fragment, r"\bOrderSend"):
        prefix = source_context_prefix + live_fragment[:call_start]
        if len(arguments) >= 7:
            order_type = _strip_balanced_outer_parentheses(arguments[1]).upper()
            side = {"OP_BUY": "buy", "OP_SELL": "sell"}.get(order_type)
            if side:
                evidence.append(_entry_call_evidence(
                    side,
                    arguments[2],
                    arguments[5],
                    arguments[6],
                    prefix,
                    environment,
                ))
            continue
        if len(arguments) != 2:
            continue
        request_name = _strip_balanced_outer_parentheses(arguments[0])
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", request_name):
            continue
        if _latest_member_assignment(prefix, request_name, "position") is not None:
            continue
        action = _latest_member_assignment(prefix, request_name, "action")
        order_type = _latest_member_assignment(prefix, request_name, "type")
        volume = _latest_member_assignment(prefix, request_name, "volume")
        stop = _latest_member_assignment(prefix, request_name, "sl")
        take = _latest_member_assignment(prefix, request_name, "tp")
        if (
            action is None
            or _strip_balanced_outer_parentheses(action).upper()
            != "TRADE_ACTION_DEAL"
            or order_type is None
            or volume is None
        ):
            continue
        side = {
            "ORDER_TYPE_BUY": "buy",
            "ORDER_TYPE_SELL": "sell",
        }.get(_strip_balanced_outer_parentheses(order_type).upper())
        if side:
            evidence.append(_entry_call_evidence(
                side,
                volume,
                stop or "0",
                take or "0",
                prefix,
                environment,
            ))

    for method, side in (("Buy", "buy"), ("Sell", "sell")):
        for call_start, arguments in _call_argument_rows(
            live_fragment,
            rf"\.\s*{method}",
        ):
            if len(arguments) < 5:
                continue
            evidence.append(_entry_call_evidence(
                side,
                arguments[0],
                arguments[3],
                arguments[4],
                source_context_prefix + live_fragment[:call_start],
                environment,
            ))

    for call_start, arguments in _call_argument_rows(
        live_fragment,
        r"\.\s*PositionOpen",
    ):
        if len(arguments) < 6:
            continue
        side = {
            "ORDER_TYPE_BUY": "buy",
            "ORDER_TYPE_SELL": "sell",
        }.get(_strip_balanced_outer_parentheses(arguments[1]).upper())
        if side:
            evidence.append(_entry_call_evidence(
                side,
                arguments[2],
                arguments[4],
                arguments[5],
                source_context_prefix + live_fragment[:call_start],
                environment,
            ))

    by_name = {str(row.get("name") or ""): row for row in functions}
    for name, function in by_name.items():
        if not name or name in visited:
            continue
        parameters = _function_parameter_names(function)
        if parameters is None:
            continue
        for call_start, arguments in _call_argument_rows(
            live_fragment,
            rf"\b{re.escape(name)}",
        ):
            if len(arguments) != len(parameters):
                continue
            caller_prefix = source_context_prefix + live_fragment[:call_start]
            child_environment = {
                parameter.lower(): (
                    _resolve_trade_expression(
                        argument,
                        caller_prefix,
                        environment,
                    )
                    or ""
                )
                for parameter, argument in zip(parameters, arguments)
            }
            evidence.extend(_mql_entry_call_evidence(
                str(function.get("body") or ""),
                functions,
                parameter_environment=child_environment,
                visited=visited | {name},
            ))
    return evidence


def _named_call_argument(arguments: list[str], name: str) -> str | None:
    for argument in arguments:
        match = re.fullmatch(
            rf"\s*{re.escape(name)}\s*=\s*(?P<value>.+?)\s*",
            argument,
            re.IGNORECASE,
        )
        if match:
            return match.group("value")
    return None


def _pine_entry_call_evidence(fragment: str) -> list[dict[str, object]]:
    live_fragment = _strip_statically_dead_pine_regions(fragment)
    protection_rows: list[tuple[str, str]] = []
    for call_start, arguments in _call_argument_rows(
        live_fragment,
        r"\bstrategy\.exit",
    ):
        stop = _named_call_argument(arguments, "stop")
        take = _named_call_argument(arguments, "limit")
        if stop or take:
            protection_rows.append((stop or "0", take or "0"))
    # Multiple independent strategy.exit records cannot be associated with a
    # specific entry after string payloads are stripped.  Fail closed rather
    # than borrowing SL from one record and TP from another.
    stop_expression, take_expression = (
        protection_rows[0] if len(protection_rows) == 1 else ("0", "0")
    )
    evidence: list[dict[str, object]] = []
    for call_start, arguments in _call_argument_rows(
        live_fragment,
        r"\bstrategy\.(?:entry|order)",
    ):
        side: str | None = None
        if any(re.search(r"\bstrategy\.long\b", arg, re.IGNORECASE) for arg in arguments):
            side = "buy"
        elif any(re.search(r"\bstrategy\.short\b", arg, re.IGNORECASE) for arg in arguments):
            side = "sell"
        volume = _named_call_argument(arguments, "qty")
        if side and volume:
            evidence.append(_entry_call_evidence(
                side,
                volume,
                stop_expression,
                take_expression,
                live_fragment[:call_start],
                {},
            ))
    return evidence


def _source_number(value: str) -> float | None:
    text = _strip_balanced_outer_parentheses(value)
    if not re.fullmatch(_SOURCE_NUMBER_PATTERN, text):
        return None
    try:
        result = float(text)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def _latest_simple_assignment(
    source: str,
    name: str,
) -> str | None:
    escaped = re.escape(name)
    matches = list(re.finditer(
        rf"(?m)(?<![A-Za-z0-9_.])"
        rf"(?:double|float|int|long|uint|ulong)?\s*\b{escaped}\b\s*=(?!=)"
        rf"\s*(?P<expression>[^;\n]+)",
        source,
        re.IGNORECASE,
    ))
    return matches[-1].group("expression").strip() if matches else None


def _volume_base_expression_supported(
    expression: str,
    source_prefix: str,
    seen: set[str],
) -> bool:
    text = _strip_balanced_outer_parentheses(expression)
    if not text or _source_number(text) is not None:
        return False
    if not re.fullmatch(_SOURCE_IDENTIFIER_ATOM_PATTERN, text):
        return False
    if re.fullmatch(r"OrderLots\s*\(\s*\)", text, re.IGNORECASE):
        return True
    if re.fullmatch(
        r"PositionGetDouble\s*\(\s*POSITION_VOLUME\s*\)",
        text,
        re.IGNORECASE,
    ):
        return True
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", text) and text.lower() not in seen:
        # A declared EA input may legitimately be the original entry size.
        # Local aliases, however, must resolve to a real volume expression;
        # trusting a suggestive variable name alone lets ``fakeLots = 2.0``
        # masquerade as a partial close.
        if re.search(
            rf"\b(?:input|extern)\s+(?:(?:unsigned|signed)\s+)?"
            rf"(?:double|float|int|long|uint|ulong)\s+{re.escape(text)}\b",
            source_prefix,
            re.IGNORECASE,
        ) and re.search(r"(?:lot|volume|qty|size)", text, re.IGNORECASE):
            return True
        assignment = _latest_simple_assignment(source_prefix, text)
        if assignment is not None:
            return _volume_base_expression_supported(
                assignment,
                source_prefix,
                seen | {text.lower()},
            )
        if re.search(r"(?:lot|volume|qty|size)", text, re.IGNORECASE):
            return True
    return False


def _reduced_volume_expression(
    expression: str,
    source_prefix: str,
    *,
    seen: set[str] | None = None,
) -> bool:
    """Accept only a statically proven positive fraction of a volume value."""

    seen = set() if seen is None else set(seen)
    if len(seen) > 8:
        return False
    text = _strip_balanced_outer_parentheses(expression)
    variable = re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", text)
    if variable:
        name = variable.group(0)
        if name.lower() in seen:
            return False
        assignment = _latest_simple_assignment(source_prefix, name)
        return bool(
            assignment is not None
            and _reduced_volume_expression(
                assignment,
                source_prefix,
                seen=seen | {name.lower()},
            )
        )

    factor_on_right = re.fullmatch(
        rf"(?P<base>.+?)\s*\*\s*(?P<factor>{_SOURCE_NUMBER_PATTERN})",
        text,
    )
    factor_on_left = re.fullmatch(
        rf"(?P<factor>{_SOURCE_NUMBER_PATTERN})\s*\*\s*(?P<base>.+)",
        text,
    )
    for match in (factor_on_right, factor_on_left):
        if match is None:
            continue
        factor = _source_number(match.group("factor"))
        return bool(
            factor is not None
            and 0.0 < factor < 1.0
            and _volume_base_expression_supported(
                match.group("base"), source_prefix, seen
            )
        )

    divisor_match = re.fullmatch(
        rf"(?P<base>.+?)\s*/\s*(?P<divisor>{_SOURCE_NUMBER_PATTERN})",
        text,
    )
    if divisor_match is None:
        return False
    divisor = _source_number(divisor_match.group("divisor"))
    return bool(
        divisor is not None
        and divisor > 1.0
        and _volume_base_expression_supported(
            divisor_match.group("base"), source_prefix, seen
        )
    )


def _mql_partial_close_in_text(source: str, *, has_ctrade: bool) -> bool:
    for call_start, arguments in _call_argument_rows(source, r"\bOrderClose"):
        if len(arguments) >= 2 and _reduced_volume_expression(
            arguments[1], source[:call_start]
        ):
            return True
    if has_ctrade:
        for call_start, arguments in _call_argument_rows(
            source,
            r"\.\s*PositionClosePartial",
        ):
            if len(arguments) >= 2 and _reduced_volume_expression(
                arguments[1], source[:call_start]
            ):
                return True
    return False


def _pine_partial_close_in_text(source: str) -> bool:
    for call_start, arguments in _call_argument_rows(
        source,
        r"\bstrategy\.(?:close|exit)",
    ):
        for argument in arguments:
            percent = re.fullmatch(
                rf"\s*qty_percent\s*=\s*(?P<value>{_SOURCE_NUMBER_PATTERN})\s*",
                argument,
                re.IGNORECASE,
            )
            if percent:
                value = _source_number(percent.group("value"))
                if value is not None and 0.0 < value < 100.0:
                    return True
            quantity = re.fullmatch(
                r"\s*qty\s*=\s*(?P<value>.+?)\s*",
                argument,
                re.IGNORECASE,
            )
            if quantity and _reduced_volume_expression(
                quantity.group("value"), source[:call_start]
            ):
                return True
    return False


def _constant_numeric_expression(value: str) -> float | None:
    """Evaluate a tiny, bounded numeric-only expression without names/calls."""

    text = str(value or "").strip()
    if not text or len(text) > 256 or not re.fullmatch(r"[0-9eE.()\s+\-*/%]+", text):
        return None
    try:
        tree = ast.parse(text, mode="eval")
    except (SyntaxError, ValueError, MemoryError):
        return None
    operations = 0

    def visit(node: ast.AST, depth: int = 0) -> float | None:
        nonlocal operations
        if depth > 16 or operations > 32:
            return None
        if isinstance(node, ast.Expression):
            return visit(node.body, depth + 1)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                return None
            result = float(node.value)
            return result if math.isfinite(result) and abs(result) <= 1e100 else None
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            operations += 1
            operand = visit(node.operand, depth + 1)
            if operand is None:
                return None
            result = operand if isinstance(node.op, ast.UAdd) else -operand
            return result if math.isfinite(result) and abs(result) <= 1e100 else None
        if isinstance(node, ast.BinOp) and isinstance(
            node.op,
            (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod),
        ):
            operations += 1
            left = visit(node.left, depth + 1)
            right = visit(node.right, depth + 1)
            if left is None or right is None:
                return None
            try:
                if isinstance(node.op, ast.Add):
                    result = left + right
                elif isinstance(node.op, ast.Sub):
                    result = left - right
                elif isinstance(node.op, ast.Mult):
                    result = left * right
                elif isinstance(node.op, ast.Div):
                    result = left / right
                else:
                    result = left % right
            except (ArithmeticError, OverflowError):
                return None
            return result if math.isfinite(result) and abs(result) <= 1e100 else None
        return None

    return visit(tree)


def _condition_static_value(condition: str) -> bool | None:
    text = _strip_balanced_outer_parentheses(condition).strip()
    lowered = re.sub(r"\s+", "", text).lower()
    if lowered in {"false", "!true", "nottrue"}:
        return False
    if lowered in {"true", "!false", "notfalse"}:
        return True
    number = _constant_numeric_expression(text)
    if number is not None:
        return number != 0.0

    conjuncts = re.split(r"&&|\band\b", text, flags=re.IGNORECASE)
    if len(conjuncts) > 1:
        values = [_condition_static_value(part) for part in conjuncts]
        if False in values:
            return False
        return True if all(value is True for value in values) else None
    disjuncts = re.split(r"\|\||\bor\b", text, flags=re.IGNORECASE)
    if len(disjuncts) > 1:
        values = [_condition_static_value(part) for part in disjuncts]
        if True in values:
            return True
        return False if all(value is False for value in values) else None

    numeric_expression = r"[0-9eE.()\s+\-*/%]{1,256}"
    comparison = re.fullmatch(
        rf"\s*(?P<left>{numeric_expression})\s*"
        rf"(?P<op><=|>=|==|!=|<|>)\s*"
        rf"(?P<right>{numeric_expression})\s*",
        text,
    )
    if comparison is None:
        return None
    left = _constant_numeric_expression(comparison.group("left"))
    right = _constant_numeric_expression(comparison.group("right"))
    if left is None or right is None:
        return None
    return {
        "<": left < right,
        "<=": left <= right,
        ">": left > right,
        ">=": left >= right,
        "==": left == right,
        "!=": left != right,
    }[comparison.group("op")]


def _condition_statically_false(condition: str) -> bool:
    return _condition_static_value(condition) is False


def _condition_statically_true(condition: str) -> bool:
    return _condition_static_value(condition) is True


def _c_statement_range(source: str, cursor: int) -> tuple[int, int] | None:
    while cursor < len(source) and source[cursor].isspace():
        cursor += 1
    if cursor >= len(source):
        return None
    if source[cursor] == "{":
        body_end = _matching_brace(source, cursor)
        return (cursor, body_end + 1) if body_end is not None else None
    body_end = source.find(";", cursor)
    return (cursor, body_end + 1) if body_end >= 0 else None


def _strip_statically_dead_c_regions(source: str) -> str:
    dead_ranges: list[tuple[int, int]] = []
    for match in re.finditer(r"\bif\s*\(", source):
        opening = source.find("(", match.start(), match.end())
        closing = _matching_parenthesis(source, opening)
        if closing is None:
            continue
        condition_value = _condition_static_value(source[opening + 1:closing])
        if condition_value is None:
            continue
        then_range = _c_statement_range(source, closing + 1)
        if then_range is None:
            continue
        if condition_value is False:
            dead_ranges.append(then_range)
            continue
        cursor = then_range[1]
        while cursor < len(source) and source[cursor].isspace():
            cursor += 1
        else_match = re.match(r"else\b", source[cursor:])
        if else_match:
            else_range = _c_statement_range(
                source,
                cursor + else_match.end(),
            )
            if else_range is not None:
                dead_ranges.append(else_range)
    if not dead_ranges:
        return source
    characters = list(source)
    for start, end in dead_ranges:
        for index in range(start, min(end, len(characters))):
            if characters[index] not in "\r\n":
                characters[index] = " "
    return "".join(characters)


def _c_delimiters_balanced(source: str) -> bool:
    stack: list[str] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for character in source:
        if character in "([{":
            stack.append(character)
        elif character in ")]}":
            if not stack or stack.pop() != pairs[character]:
                return False
    return not stack


def strip_statically_dead_mql_regions(source: str) -> str | None:
    """Return lexical MQL with provably dead branches blanked, else ``None``."""

    if not isinstance(source, str) or len(source) > 1_000_000:
        return None
    lexical_source = _strip_comments_and_strings(source)
    if not _c_delimiters_balanced(lexical_source):
        return None
    for match in re.finditer(r"\bif\s*\(", lexical_source):
        opening = lexical_source.find("(", match.start(), match.end())
        closing = _matching_parenthesis(lexical_source, opening)
        if closing is None:
            return None
        then_range = _c_statement_range(lexical_source, closing + 1)
        if then_range is None:
            return None
        cursor = then_range[1]
        while cursor < len(lexical_source) and lexical_source[cursor].isspace():
            cursor += 1
        else_match = re.match(r"else\b", lexical_source[cursor:])
        if else_match and _c_statement_range(
            lexical_source,
            cursor + else_match.end(),
        ) is None:
            return None
    return _strip_statically_dead_c_regions(lexical_source)


def _mql_action_in_text(
    source: str,
    action: str,
    *,
    has_ctrade: bool,
) -> bool:
    has_order_send = bool(re.search(r"\bOrderSend\s*\(", source))
    has_position_binding = bool(
        re.search(
            r"\b(?:request\s*\.\s*position|position_id|position_ticket)\b",
            source,
            re.IGNORECASE,
        )
    )
    if action == "entry":
        return bool(
            _MQL_ENTRY_PATTERN.search(source)
            or (has_ctrade and _MQL_CTRADE_ENTRY_PATTERN.search(source))
            or (
                has_order_send
                and not has_position_binding
                and re.search(r"\bTRADE_ACTION_DEAL\b", source)
            )
        )
    if action == "entry_buy":
        return bool(_MQL_BUY_ENTRY_PATTERN.search(source))
    if action == "entry_sell":
        return bool(_MQL_SELL_ENTRY_PATTERN.search(source))
    if action == "pending":
        return bool(
            _MQL_PENDING_PATTERN.search(source)
            or (has_ctrade and _MQL_CTRADE_PENDING_PATTERN.search(source))
            or (
                has_order_send
                and re.search(r"\bTRADE_ACTION_PENDING\b", source)
                and re.search(
                    r"\bORDER_TYPE_(?:BUY|SELL)_(?:LIMIT|STOP|STOP_LIMIT)\b",
                    source,
                )
            )
        )
    if action == "exit":
        return bool(
            _MQL_EXIT_PATTERN.search(source)
            or (has_ctrade and _MQL_CTRADE_EXIT_PATTERN.search(source))
            or (
                has_order_send and has_position_binding
            )
        )
    if action == "management":
        return bool(
            re.search(r"\b(?:OrderModify|OrderDelete)\s*\(", source)
            or _mql_partial_close_in_text(source, has_ctrade=has_ctrade)
            or (
                has_ctrade
                and re.search(r"\.\s*PositionModify\s*\(", source, re.IGNORECASE)
            )
            or (
                has_order_send
                and re.search(r"\bTRADE_ACTION_SLTP\b", source)
            )
        )
    if action in {"move_stop_loss", "move_take_profit"}:
        return bool(
            re.search(r"\bOrderModify\s*\(", source)
            or (
                has_ctrade
                and re.search(r"\.\s*PositionModify\s*\(", source, re.IGNORECASE)
            )
            or (
                has_order_send
                and re.search(r"\bTRADE_ACTION_SLTP\b", source)
            )
        )
    if action == "close_partial":
        return _mql_partial_close_in_text(source, has_ctrade=has_ctrade)
    if action == "scale_out":
        return _mql_action_in_text(
            source,
            "close_partial",
            has_ctrade=has_ctrade,
        )
    if action == "close_position":
        return _mql_action_in_text(source, "exit", has_ctrade=has_ctrade)
    if action == "scale_in":
        return _mql_action_in_text(source, "entry", has_ctrade=has_ctrade)
    if action == "place_pending":
        return _mql_action_in_text(source, "pending", has_ctrade=has_ctrade)
    if action == "cancel_pending":
        return bool(
            re.search(r"\bOrderDelete\s*\(", source)
            or (
                has_ctrade
                and re.search(r"\.\s*OrderDelete\s*\(", source, re.IGNORECASE)
            )
            or (
                has_order_send
                and re.search(r"\bTRADE_ACTION_REMOVE\b", source)
            )
        )
    if action == "modify_pending":
        return bool(
            re.search(r"\bOrderModify\s*\(", source)
            or (
                has_ctrade
                and re.search(r"\.\s*OrderModify\s*\(", source, re.IGNORECASE)
            )
            or (
                has_order_send
                and re.search(r"\bTRADE_ACTION_MODIFY\b", source)
            )
        )
    if action == "replace_pending":
        return bool(
            _mql_action_in_text(source, "cancel_pending", has_ctrade=has_ctrade)
            and _mql_action_in_text(source, "pending", has_ctrade=has_ctrade)
        )
    return False


def _action_in_text(
    source: str,
    action: str,
    *,
    target_platform: str,
    has_ctrade: bool,
) -> bool:
    if target_platform == "tradingview":
        if action in {"close_partial", "scale_out"}:
            return _pine_partial_close_in_text(source)
        pattern = {
            "entry": _PINE_ENTRY_PATTERN,
            "entry_buy": _PINE_BUY_ENTRY_PATTERN,
            "entry_sell": _PINE_SELL_ENTRY_PATTERN,
            "exit": _PINE_EXIT_PATTERN,
            "management": _PINE_EXIT_PATTERN,
            "pending": _PINE_PENDING_PATTERN,
            "move_stop_loss": _PINE_EXIT_PATTERN,
            "move_take_profit": _PINE_EXIT_PATTERN,
            "close_position": _PINE_EXIT_PATTERN,
            "scale_in": _PINE_ENTRY_PATTERN,
            "place_pending": _PINE_PENDING_PATTERN,
            "modify_pending": _PINE_PENDING_PATTERN,
            "replace_pending": _PINE_PENDING_PATTERN,
            "cancel_pending": re.compile(r"\bstrategy\.(?:cancel|cancel_all)\s*\("),
        }.get(action)
        if pattern is None:
            return False
        return bool(pattern.search(source))
    return _mql_action_in_text(source, action, has_ctrade=has_ctrade)


def _pine_if_regions(source: str) -> list[tuple[str, str]]:
    """Extract conventional indentation-based Pine if branches."""

    lines = source.splitlines()
    regions: list[tuple[str, str]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^(\s*)if\s+(.+?)\s*$", line)
        if not match:
            continue
        base_indent = len(match.group(1).replace("\t", "    "))
        body: list[str] = []
        for child in lines[index + 1:]:
            if not child.strip():
                continue
            indent = len(child) - len(child.lstrip(" \t"))
            if indent <= base_indent:
                break
            body.append(child)
        regions.append((match.group(2), "\n".join(body)))
    return regions


def _strip_statically_dead_pine_regions(source: str) -> str:
    lines = source.splitlines()
    result: list[str] = []
    skipped_indent: int | None = None
    for line in lines:
        if not line.strip():
            if skipped_indent is None:
                result.append(line)
            continue
        indent = len(line) - len(line.lstrip(" \t"))
        if skipped_indent is not None:
            if indent > skipped_indent:
                continue
            skipped_indent = None
        match = re.match(r"^\s*if\s+(.+?)\s*$", line)
        if match and _condition_statically_false(match.group(1)):
            skipped_indent = indent
            continue
        result.append(line)
    return "\n".join(result)


def _marker_action_bound(
    marker: str,
    marker_scopes: list[dict[str, object]],
    action: str,
    *,
    source: str,
    target_platform: str,
    functions: list[dict[str, object]],
    trading_reachable: set[str],
    has_ctrade: bool,
) -> bool:
    """Require marker-derived decisions to guard the matching order action."""

    if target_platform == "tradingview":
        aliases = {marker}
        for line in source.splitlines():
            alias_match = re.match(
                rf"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?::=|=)[^\n]*\b{re.escape(marker)}\b",
                line,
            )
            if alias_match:
                aliases.add(alias_match.group(1))
        for condition, body in _pine_if_regions(source):
            if (
                _condition_static_value(condition) is None
                and any(
                    re.search(rf"\b{re.escape(name)}\b", condition)
                    for name in aliases
                )
                and (
                    any(
                        row.get("side") == action.removeprefix("entry_")
                        for row in _pine_entry_call_evidence(body)
                    )
                    if action in {"entry_buy", "entry_sell"}
                    else _action_in_text(
                        _strip_statically_dead_pine_regions(body),
                        action,
                        target_platform=target_platform,
                        has_ctrade=False,
                    )
                )
            ):
                return True
        return False

    signal_functions = {
        str(row.get("name") or "")
        for row in marker_scopes
        if str(row.get("name") or "")
        and _marker_controls_returned_predicate(
            str(row.get("body") or ""), marker
        )
    }
    for function in functions:
        function_name = str(function.get("name") or "")
        if function_name not in trading_reachable:
            continue
        for condition, body in _c_if_regions(str(function.get("body") or "")):
            if _condition_static_value(condition) is not None:
                continue
            marker_controls_branch = bool(
                re.search(rf"\b{re.escape(marker)}\b", condition)
                or any(
                    re.search(rf"\b{re.escape(name)}\s*\(", condition)
                    for name in signal_functions
                )
            )
            if not marker_controls_branch:
                continue
            live_body = strip_statically_dead_mql_regions(body)
            if live_body is None:
                continue
            expanded_body = strip_statically_dead_mql_regions(
                _expanded_fragment_source(live_body, functions)
            )
            if expanded_body is None:
                continue
            if action in {"entry_buy", "entry_sell"}:
                expected_side = action.removeprefix("entry_")
                function_body = str(function.get("body") or "")
                body_offset = function_body.find(body)
                context_prefix = (
                    function_body[:body_offset]
                    if body_offset >= 0
                    and function_body.find(body, body_offset + 1) < 0
                    else ""
                )
                if any(
                    row.get("side") == expected_side
                    for row in _mql_entry_call_evidence(
                        live_body,
                        functions,
                        source_context_prefix=context_prefix,
                    )
                ):
                    return True
                continue
            if _action_in_text(
                expanded_body,
                action,
                target_platform=target_platform,
                has_ctrade=has_ctrade,
            ):
                return True
    return False


def _normalized_trade_expression(value: object) -> str:
    return re.sub(
        r"\s+",
        "",
        _strip_balanced_outer_parentheses(str(value or "")),
    ).lower()


def _trade_expression_is_exact_input(value: object, input_ref: str) -> bool:
    return _normalized_trade_expression(value) == str(input_ref or "").strip().lower()


def _split_top_level_add_sub(value: str) -> tuple[str, str, str] | None:
    text = _strip_balanced_outer_parentheses(value)
    depth = 0
    matches: list[tuple[int, str]] = []
    for index, character in enumerate(text):
        if character in "([":
            depth += 1
        elif character in ")]":
            depth -= 1
            if depth < 0:
                return None
        elif depth == 0 and character in "+-" and index > 0:
            # A sign in a scientific-notation exponent is not a binary node.
            if (
                text[index - 1] in "eE"
                and index >= 2
                and (text[index - 2].isdigit() or text[index - 2] == ".")
                and index + 1 < len(text)
                and (text[index + 1].isdigit() or text[index + 1] == ".")
            ):
                continue
            matches.append((index, character))
    if depth != 0 or len(matches) != 1:
        return None
    index, operator = matches[0]
    left = text[:index].strip()
    right = text[index + 1:].strip()
    return (left, operator, right) if left and right else None


def _split_top_level_product(value: str) -> tuple[str, str] | None:
    text = _strip_balanced_outer_parentheses(value)
    depth = 0
    indexes: list[int] = []
    for index, character in enumerate(text):
        if character in "([":
            depth += 1
        elif character in ")]":
            depth -= 1
            if depth < 0:
                return None
        elif depth == 0 and character == "*":
            indexes.append(index)
    if depth != 0 or len(indexes) != 1:
        return None
    index = indexes[0]
    left = text[:index].strip()
    right = text[index + 1:].strip()
    return (left, right) if left and right else None


def _unwrap_normalize_price(value: str) -> str | None:
    text = _strip_balanced_outer_parentheses(value)
    match = re.fullmatch(r"NormalizeDouble\s*\((?P<args>.*)\)", text, re.IGNORECASE)
    if match is None:
        return text
    arguments = _split_top_level_arguments(match.group("args"))
    if arguments is None or len(arguments) != 2:
        return None
    precision = _normalized_trade_expression(arguments[1])
    if precision not in {"digits", "_digits"}:
        return None
    return _strip_balanced_outer_parentheses(arguments[0])


def _protection_distance_matches(value: str, input_ref: str) -> bool:
    if _trade_expression_is_exact_input(value, input_ref):
        return True
    product = _split_top_level_product(value)
    if product is None:
        return False
    left, right = product
    if _trade_expression_is_exact_input(left, input_ref):
        unit = _normalized_trade_expression(right)
    elif _trade_expression_is_exact_input(right, input_ref):
        unit = _normalized_trade_expression(left)
    else:
        return False
    return unit in {
        "point",
        "_point",
        "pip",
        "pip_size",
        "pipsize()",
        "pipvalue()",
    }


def _entry_price_base_matches(value: str, *, side: str, platform: str) -> bool:
    normalized = _normalized_trade_expression(value)
    if platform == "tradingview":
        return normalized == "close"
    if side == "buy":
        return normalized in {
            "ask",
            "symbolinfodouble(symbol(),symbol_ask)",
            "symbolinfodouble(_symbol,symbol_ask)",
        }
    if side == "sell":
        return normalized in {
            "bid",
            "symbolinfodouble(symbol(),symbol_bid)",
            "symbolinfodouble(_symbol,symbol_bid)",
        }
    return False


def _protection_expression_matches(
    value: object,
    input_ref: str,
    *,
    side: str,
    platform: str,
    stop_loss: bool,
) -> bool:
    unwrapped = _unwrap_normalize_price(str(value or ""))
    if unwrapped is None:
        return False
    operation = _split_top_level_add_sub(unwrapped)
    if operation is None:
        return False
    base, operator, distance = operation
    expected_operator = (
        "-" if (side == "buy") == stop_loss else "+"
    )
    return bool(
        operator == expected_operator
        and _entry_price_base_matches(base, side=side, platform=platform)
        and _protection_distance_matches(distance, input_ref)
    )


def _marker_trade_call_contract_bound(
    marker: str,
    marker_scopes: list[dict[str, object]],
    actions: list[str],
    contract: object,
    *,
    source: str,
    target_platform: str,
    functions: list[dict[str, object]],
    trading_reachable: set[str],
) -> bool:
    """Require marker-guarded entries to consume exact risk/protection inputs."""

    if not isinstance(contract, Mapping) or contract.get("supported") is not True:
        return False

    def evidence_matches(row: Mapping[str, object], action: str) -> bool:
        expected_side = action.removeprefix("entry_") if action.startswith("entry_") else ""
        if expected_side and row.get("side") != expected_side:
            return False
        actual_side = str(row.get("side") or "")
        if "volumeInputRef" in contract:
            expected_volume = str(contract.get("volumeInputRef") or "").lower()
            if (
                not expected_volume
                or not _trade_expression_is_exact_input(
                    row.get("volumeExpression"), expected_volume
                )
            ):
                return False
        for required_key, ref_key, evidence_key, stop_loss in (
            ("stopLossRequired", "stopLossInputRef", "stopExpression", True),
            ("takeProfitRequired", "takeProfitInputRef", "takeExpression", False),
        ):
            if contract.get(required_key) is not True:
                continue
            expected_ref = str(contract.get(ref_key) or "").lower()
            if (
                not expected_ref
                or not _protection_expression_matches(
                    row.get(evidence_key),
                    expected_ref,
                    side=actual_side,
                    platform=target_platform,
                    stop_loss=stop_loss,
                )
            ):
                return False
        return True

    guarded_evidence: list[dict[str, object]] = []
    if target_platform == "tradingview":
        aliases = {marker}
        for line in source.splitlines():
            alias_match = re.match(
                rf"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?::=|=)[^\n]*\b{re.escape(marker)}\b",
                line,
            )
            if alias_match:
                aliases.add(alias_match.group(1))
        for condition, body in _pine_if_regions(source):
            if (
                _condition_static_value(condition) is None
                and any(
                    re.search(rf"\b{re.escape(name)}\b", condition)
                    for name in aliases
                )
            ):
                guarded_evidence.extend(_pine_entry_call_evidence(body))
    else:
        signal_functions = {
            str(row.get("name") or "")
            for row in marker_scopes
            if str(row.get("name") or "")
            and _marker_controls_returned_predicate(
                str(row.get("body") or ""), marker
            )
        }
        for function in functions:
            function_name = str(function.get("name") or "")
            if function_name not in trading_reachable:
                continue
            for condition, body in _c_if_regions(str(function.get("body") or "")):
                if _condition_static_value(condition) is not None:
                    continue
                if not (
                    re.search(rf"\b{re.escape(marker)}\b", condition)
                    or any(
                        re.search(rf"\b{re.escape(name)}\s*\(", condition)
                        for name in signal_functions
                    )
                ):
                    continue
                function_body = str(function.get("body") or "")
                body_offset = function_body.find(body)
                context_prefix = (
                    function_body[:body_offset]
                    if body_offset >= 0
                    and function_body.find(body, body_offset + 1) < 0
                    else ""
                )
                guarded_evidence.extend(_mql_entry_call_evidence(
                    body,
                    functions,
                    source_context_prefix=context_prefix,
                ))

    required_actions = actions or ["entry"]
    return bool(guarded_evidence) and all(
        any(evidence_matches(row, action) for row in guarded_evidence)
        for action in required_actions
    )


def _source_capabilities(
    source: str,
    target_platform: str,
    functions: list[dict[str, object]],
    lifecycle_reachable: set[str],
    trading_reachable: set[str],
    *,
    original_source: str,
) -> dict[str, bool]:
    if target_platform == "tradingview":
        executable = source
        return {
            "entryPoint": bool(
                re.search(r"(?m)^\s*//@version=\d+\s*$", original_source)
                and re.search(r"(?m)^\s*strategy\s*\(", source)
            ),
            "tradeEntry": bool(_PINE_ENTRY_PATTERN.search(executable)),
            "tradeExit": bool(_PINE_EXIT_PATTERN.search(executable)),
            "tradeManagement": bool(_PINE_EXIT_PATTERN.search(executable)),
            "pendingOrder": bool(_PINE_PENDING_PATTERN.search(executable)),
            "stopLoss": bool(
                _PINE_EXIT_PATTERN.search(executable)
                and _STOP_LOSS_PATTERN.search(executable)
            ),
            "takeProfit": bool(
                _PINE_EXIT_PATTERN.search(executable)
                and _TAKE_PROFIT_PATTERN.search(executable)
            ),
            "closedBar": bool(_scope_has_shift(executable, 1) and _scope_has_shift(executable, 2)),
            "indicatorAccess": bool(_INDICATOR_PATTERN.search(executable)),
            "stateLogic": bool(_STATE_PATTERN.search(executable)),
            "controlledDecision": _scope_has_controlled_comparison(executable),
        }

    by_name = {str(row["name"]): row for row in functions}
    lifecycle_source = "\n".join(
        str(by_name[name]["body"])
        for name in sorted(lifecycle_reachable)
        if name in by_name
    )
    trading_source = "\n".join(
        str(by_name[name]["body"])
        for name in sorted(trading_reachable)
        if name in by_name
    )
    has_ctrade = bool(re.search(r"\bCTrade\s+[A-Za-z_][A-Za-z0-9_]*\b", source))
    action_sources = [
        str(by_name[name]["body"])
        for name in sorted(trading_reachable)
        if name in by_name
    ]
    entry_detected = any(
        _mql_action_in_text(body, "entry", has_ctrade=has_ctrade)
        for body in action_sources
    )
    exit_detected = any(
        _mql_action_in_text(body, "exit", has_ctrade=has_ctrade)
        for body in action_sources
    )
    pending_detected = any(
        _mql_action_in_text(body, "pending", has_ctrade=has_ctrade)
        for body in action_sources
    )
    return {
        "entryPoint": bool(trading_reachable),
        "tradeEntry": entry_detected,
        "tradeExit": exit_detected,
        "tradeManagement": any(
            _mql_action_in_text(body, "management", has_ctrade=has_ctrade)
            for body in action_sources
        ),
        "pendingOrder": pending_detected,
        "stopLoss": bool(entry_detected and _STOP_LOSS_PATTERN.search(trading_source)),
        "takeProfit": bool(entry_detected and _TAKE_PROFIT_PATTERN.search(trading_source)),
        "closedBar": bool(
            _scope_has_shift(lifecycle_source, 1) and _scope_has_shift(lifecycle_source, 2)
        ),
        "indicatorAccess": bool(_INDICATOR_PATTERN.search(lifecycle_source)),
        "stateLogic": bool(_STATE_PATTERN.search(lifecycle_source)),
        "controlledDecision": _scope_has_controlled_comparison(trading_source),
    }


def _semantic_marker_supported(
    key: str,
    identifier: str,
    marker: str,
    scopes: list[dict[str, object]],
    *,
    target_platform: str,
    capabilities: Mapping[str, bool],
    rule_roles: Mapping[str, Mapping[str, str]],
    semantic_bindings: Mapping[str, Mapping[str, object]],
    predicate_operand_aliases: Mapping[str, object],
    pending_state_ids: set[str],
    source: str,
    functions: list[dict[str, object]],
    initialization_reachable: set[str],
    trading_reachable: set[str],
    has_ctrade: bool,
) -> bool:
    if not scopes:
        return False
    for row in scopes:
        scope = str(row.get("body") or "")
        scope_name = str(row.get("name") or "")
        if not _marker_participates_in_expression(scope, marker):
            continue
        if key == "semanticDigests":
            binding = semantic_bindings.get(identifier, {})
            kind = str(binding.get("kind") or "")
            actions = [
                str(action)
                for action in binding.get("actions", [])
                if isinstance(action, str)
            ] if isinstance(binding.get("actions"), list) else []
            if kind in {
                "bar_semantics",
                "blueprint_section",
                "execution_contract",
                "pseudocode",
                "test_vector",
            }:
                if kind == "test_vector" and not _scope_has_controlled_comparison(scope):
                    continue
                if target_platform == "tradingview":
                    if _marker_action_bound(
                        marker,
                        scopes,
                        "entry",
                        source=source,
                        target_platform=target_platform,
                        functions=functions,
                        trading_reachable=trading_reachable,
                        has_ctrade=has_ctrade,
                    ):
                        return True
                    continue
                if (
                    scope_name in initialization_reachable
                    and re.search(r"(?:check|verify)", scope_name, re.IGNORECASE)
                    and _marker_controls_returned_predicate(scope, marker)
                ):
                    return True
                continue
            if kind == "rule_semantics":
                if not _rule_predicate_supported(
                    scope,
                    marker,
                    binding.get("predicate"),
                    target_platform=target_platform,
                    operand_aliases=predicate_operand_aliases,
                ):
                    continue
                if actions == ["initialization"]:
                    if target_platform == "tradingview":
                        if _marker_action_bound(
                            marker,
                            scopes,
                            "entry",
                            source=source,
                            target_platform=target_platform,
                            functions=functions,
                            trading_reachable=trading_reachable,
                            has_ctrade=has_ctrade,
                        ):
                            return True
                        continue
                    if (
                        scope_name in initialization_reachable
                        and re.search(r"(?:check|verify)", scope_name, re.IGNORECASE)
                        and _marker_controls_returned_predicate(scope, marker)
                    ):
                        return True
                    continue
                if (
                    row.get("tradingReachable") is True
                    and _scope_has_controlled_comparison(scope)
                    and actions
                    and all(
                        _marker_action_bound(
                            marker,
                            scopes,
                            action,
                            source=source,
                            target_platform=target_platform,
                            functions=functions,
                            trading_reachable=trading_reachable,
                            has_ctrade=has_ctrade,
                        )
                        for action in actions
                    )
                ):
                    return True
                continue
            if kind == "indicator":
                if _INDICATOR_PATTERN.search(scope):
                    return True
                continue
            if kind in {"risk_sizing", "protection"}:
                if (
                    row.get("tradingReachable") is True
                    and _scope_has_controlled_comparison(scope)
                    and _marker_trade_call_contract_bound(
                        marker,
                        scopes,
                        actions,
                        binding.get("tradeCall"),
                        source=source,
                        target_platform=target_platform,
                        functions=functions,
                        trading_reachable=trading_reachable,
                    )
                ):
                    return True
                continue
            if kind == "management_feature":
                if (
                    row.get("tradingReachable") is True
                    and _scope_has_controlled_comparison(scope)
                    and actions
                    and all(
                        _marker_action_bound(
                            marker,
                            scopes,
                            action,
                            source=source,
                            target_platform=target_platform,
                            functions=functions,
                            trading_reachable=trading_reachable,
                            has_ctrade=has_ctrade,
                        )
                        for action in actions
                    )
                ):
                    return True
                continue
            if kind == "recovery_safety":
                if (
                    row.get("tradingReachable") is True
                    and _scope_has_controlled_comparison(scope)
                    and actions
                    and all(
                        _marker_action_bound(
                            marker,
                            scopes,
                            action,
                            source=source,
                            target_platform=target_platform,
                            functions=functions,
                            trading_reachable=trading_reachable,
                            has_ctrade=has_ctrade,
                        )
                        for action in actions
                    )
                ):
                    return True
                continue
            if kind == "state_transition":
                action_bindings = [
                    action for action in actions if action != "state_decision"
                ]
                if (
                    row.get("tradingReachable") is True
                    and _STATE_PATTERN.search(scope)
                    and re.search(r"\b(?:if|switch|return)\b|=", scope)
                    and actions
                    and all(
                        _marker_action_bound(
                            marker,
                            scopes,
                            action,
                            source=source,
                            target_platform=target_platform,
                            functions=functions,
                            trading_reachable=trading_reachable,
                            has_ctrade=has_ctrade,
                        )
                        for action in action_bindings
                    )
                ):
                    return True
                continue
            continue
        if key == "blueprintDigests":
            if target_platform == "tradingview":
                if _marker_action_bound(
                    marker,
                    scopes,
                    "entry",
                    source=source,
                    target_platform=target_platform,
                    functions=functions,
                    trading_reachable=trading_reachable,
                    has_ctrade=has_ctrade,
                ):
                    return True
                continue
            if (
                str(row.get("name") or "") in initialization_reachable
                and re.search(r"(?:check|verify)", scope_name, re.IGNORECASE)
                and _marker_controls_returned_predicate(scope, marker)
            ):
                return True
            continue
        if key == "ruleIds":
            if row.get("tradingReachable") is not True:
                continue
            role = rule_roles.get(identifier, {})
            phase = str(role.get("phase") or "other")
            action = str(role.get("action") or _rule_action(phase))
            if not _scope_has_controlled_comparison(scope):
                continue
            if action in {"entry", "recovery"} and not capabilities.get("tradeEntry"):
                continue
            if action == "exit" and not capabilities.get("tradeExit"):
                continue
            if action == "management" and not capabilities.get("tradeManagement"):
                continue
            if action == "pending" and not capabilities.get("pendingOrder"):
                continue
            bound_action = "entry" if action == "recovery" else action
            if bound_action in {"entry", "exit", "management", "pending"} and not _marker_action_bound(
                marker,
                scopes,
                bound_action,
                source=source,
                target_platform=target_platform,
                functions=functions,
                trading_reachable=trading_reachable,
                has_ctrade=has_ctrade,
            ):
                continue
            return True
        if key == "indicatorIds":
            if _INDICATOR_PATTERN.search(scope):
                return True
            continue
        if key == "stateIds":
            required_actions = (
                ("pending",)
                if identifier in pending_state_ids
                else ("entry", "exit", "management", "pending")
            )
            if (
                row.get("tradingReachable") is True
                and _STATE_PATTERN.search(scope)
                and re.search(r"\b(?:if|switch|return)\b|=", scope)
                and any(
                    _marker_action_bound(
                        marker,
                        scopes,
                        action,
                        source=source,
                        target_platform=target_platform,
                        functions=functions,
                        trading_reachable=trading_reachable,
                        has_ctrade=has_ctrade,
                    )
                    for action in required_actions
                )
            ):
                return True
            continue
        if key == "testCaseIds":
            if (
                _scope_has_controlled_comparison(scope)
                and (
                    re.search(r"(?:test|check|verify)", scope_name, re.IGNORECASE)
                    or target_platform == "tradingview"
                )
            ):
                return True
            continue
        if key == "inputIds":
            if (
                _scope_has_controlled_comparison(scope)
                or _INDICATOR_PATTERN.search(scope)
                or _MQL_ENTRY_PATTERN.search(scope)
                or _MQL_CTRADE_ENTRY_PATTERN.search(scope)
                or _PINE_ENTRY_PATTERN.search(scope)
            ):
                return True
    return False


def build_coverage_manifest(
    requirements: object,
    source: str,
    *,
    strategy_spec_digest: str,
    source_digest: str,
    target_platform: str | None = None,
) -> dict:
    if (
        not isinstance(requirements, dict)
        or requirements.get("schemaVersion") != REQUIREMENTS_SCHEMA_VERSION
        or not _SHA256_PATTERN.fullmatch(str(strategy_spec_digest or "").lower())
        or not _SHA256_PATTERN.fullmatch(str(source_digest or "").lower())
    ):
        raise ValueError("EA Factory coverage manifest binding is invalid")
    required_ids = requirements.get("requiredIds")
    required_markers = requirements.get("requiredMarkers")
    semantic_profile = requirements.get("semanticProfile")
    if (
        not isinstance(required_ids, dict)
        or not isinstance(required_markers, dict)
        or not isinstance(semantic_profile, dict)
    ):
        raise ValueError("EA Factory coverage requirements are malformed")
    unsigned_requirements = dict(requirements)
    claimed_requirements_digest = unsigned_requirements.pop("requirementsDigest", None)
    if (
        not _SHA256_PATTERN.fullmatch(str(claimed_requirements_digest or "").lower())
        or _sha256(unsigned_requirements) != str(claimed_requirements_digest).lower()
    ):
        raise ValueError("EA Factory coverage requirements digest is invalid")
    raw_source = str(source or "")
    lexical_source = _strip_comments_and_strings(raw_source)
    platform = str(target_platform or "").strip().lower()
    if not platform:
        platform = (
            "tradingview"
            if re.search(r"(?m)^\s*strategy\s*\(", lexical_source)
            else "mt4"
        )
    if platform not in _SUPPORTED_PLATFORMS:
        raise ValueError("EA Factory coverage target platform is unsupported")

    functions = _c_like_functions(lexical_source) if platform != "tradingview" else []
    lifecycle_reachable = (
        _reachable_function_names(functions, _MQL_LIFECYCLE_ROOTS)
        if functions
        else set()
    )
    initialization_reachable = (
        _reachable_function_names(functions, _MQL_INITIALIZATION_ROOTS)
        if functions
        else set()
    )
    trading_reachable = (
        _reachable_function_names(functions, _MQL_TRADING_ROOTS)
        if functions
        else set()
    )
    capabilities = _source_capabilities(
        lexical_source,
        platform,
        functions,
        lifecycle_reachable,
        trading_reachable,
        original_source=raw_source,
    )
    has_ctrade = bool(
        re.search(r"\bCTrade\s+[A-Za-z_][A-Za-z0-9_]*\b", lexical_source)
    )
    rule_roles = {
        str(row.get("id")): row
        for row in semantic_profile.get("ruleRoles", [])
        if isinstance(row, Mapping) and isinstance(row.get("id"), str)
    }
    semantic_binding_rows = semantic_profile.get("semanticBindings")
    semantic_bindings = {
        str(row.get("id")): row
        for row in semantic_binding_rows
        if isinstance(semantic_binding_rows, list)
        and isinstance(row, Mapping)
        and isinstance(row.get("id"), str)
    } if isinstance(semantic_binding_rows, list) else {}
    if (
        required_ids.get("blueprintDigests")
        != [str(requirements.get("eaBlueprintDigest") or "").lower()]
        or set(rule_roles) != set(required_ids.get("ruleIds") or [])
        or any(
            str(role.get("phase") or "") == "management"
            or str(role.get("action") or "")
            not in {"entry", "exit", "management", "pending", "recovery", "other"}
            for role in rule_roles.values()
        )
        or any(
            not isinstance(semantic_profile.get(key), list)
            for key in (
                "managementRuleIds",
                "pendingRuleIds",
                "recoveryRuleIds",
                "pendingStateIds",
                "enabledManagementFeatures",
                "semanticBindings",
            )
        )
        or any(
            type(semantic_profile.get(key)) is not bool
            for key in (
                "requiresEntry",
                "requiresExit",
                "requiresManagement",
                "requiresPendingOrder",
                "requiresRecovery",
                "requiresStopLoss",
                "requiresTakeProfit",
                "requiresClosedBar",
            )
        )
    ):
        raise ValueError("EA Factory coverage semantic profile is malformed")
    semantic_ids = required_ids.get("semanticDigests")
    if (
        not isinstance(semantic_ids, list)
        or semantic_ids != sorted(semantic_bindings)
        or len(semantic_bindings) != len(semantic_binding_rows)
        or any(
            set(binding)
            != (
                {"id", "kind", "identity", "digest", "actions", "predicate"}
                if binding.get("kind") == "rule_semantics"
                else (
                    {
                        "id",
                        "kind",
                        "identity",
                        "digest",
                        "actions",
                        "spec",
                        "inputDefaults",
                    }
                    if binding.get("kind") == "indicator"
                    else (
                        {
                            "id",
                            "kind",
                            "identity",
                            "digest",
                            "actions",
                            "tradeCall",
                        }
                        if binding.get("kind") in {"risk_sizing", "protection"}
                        else {"id", "kind", "identity", "digest", "actions"}
                    )
                )
            )
            or str(binding.get("kind") or "") not in _SEMANTIC_BINDING_KINDS
            or not isinstance(binding.get("identity"), str)
            or not str(binding.get("identity") or "").strip()
            or not _SHA256_PATTERN.fullmatch(str(binding.get("digest") or ""))
            or binding.get("id")
            != (
                f"{binding.get('kind')}:{binding.get('identity')}:"
                f"{binding.get('digest')}"
            )
            or not isinstance(binding.get("actions"), list)
            or not binding.get("actions")
            or binding.get("actions") != sorted(set(binding.get("actions") or []))
            or any(
                not isinstance(action, str)
                or action not in _SEMANTIC_BINDING_ACTIONS
                for action in binding.get("actions", [])
            )
            or (
                binding.get("kind") == "rule_semantics"
                and not _rule_predicate_contract_valid(binding.get("predicate"))
            )
            or (
                binding.get("kind") == "indicator"
                and (
                    not isinstance(binding.get("spec"), Mapping)
                    or not isinstance(binding.get("inputDefaults"), Mapping)
                    or binding["spec"].get("indicatorId") != binding.get("identity")
                    or _sha256(binding["spec"]) != binding.get("digest")
                    or any(
                        not isinstance(key, str) or not key
                        for key in binding["inputDefaults"]
                    )
                )
            )
            or (
                binding.get("kind") in {"risk_sizing", "protection"}
                and not _trade_call_contract_valid(
                    binding.get("tradeCall"),
                    kind=str(binding.get("kind")),
                )
            )
            for binding in semantic_bindings.values()
        )
    ):
        raise ValueError("EA Factory coverage semantic bindings are malformed")
    binding_identities: dict[str, set[str]] = {}
    for binding in semantic_bindings.values():
        binding_identities.setdefault(str(binding["kind"]), set()).add(
            str(binding["identity"])
        )
    if (
        binding_identities.get("indicator", set())
        != set(required_ids.get("indicatorIds") or [])
        or binding_identities.get("blueprint_section", set())
        != set(_CANONICAL_BLUEPRINT_SECTIONS)
        or binding_identities.get("rule_semantics", set())
        != set(required_ids.get("ruleIds") or [])
        or binding_identities.get("state_transition", set())
        != set(required_ids.get("stateIds") or [])
        or binding_identities.get("test_vector", set())
        != set(required_ids.get("testCaseIds") or [])
        or binding_identities.get("management_feature", set())
        != set(semantic_profile.get("enabledManagementFeatures") or [])
        or len(binding_identities.get("risk_sizing", set())) != 1
        or len(binding_identities.get("protection", set())) != 1
        or len(binding_identities.get("pseudocode", set())) != 1
        or len(binding_identities.get("execution_contract", set())) != 1
        or len(binding_identities.get("bar_semantics", set())) != 1
        or (
            (semantic_profile.get("requiresRecovery") is True)
            != (len(binding_identities.get("recovery_safety", set())) == 1)
        )
    ):
        raise ValueError("EA Factory coverage semantic binding identities are malformed")
    expected_role_ids = {
        action: sorted(
            identifier
            for identifier, role in rule_roles.items()
            if str(role.get("action") or "") == action
        )
        for action in ("management", "pending", "recovery")
    }
    if any(
        semantic_profile.get(key) != expected_role_ids[action]
        for key, action in (
            ("managementRuleIds", "management"),
            ("pendingRuleIds", "pending"),
            ("recoveryRuleIds", "recovery"),
        )
    ):
        raise ValueError("EA Factory coverage semantic rule roles are malformed")
    pending_state_ids = set(semantic_profile.get("pendingStateIds") or [])
    if not pending_state_ids.issubset(set(required_ids.get("stateIds") or [])):
        raise ValueError("EA Factory coverage pending states are malformed")
    expected: dict[str, list[str]] = {}
    observed: dict[str, list[str]] = {}
    missing: dict[str, list[str]] = {}
    semantic_observed: dict[str, list[str]] = {}
    semantic_missing: dict[str, list[str]] = {}
    predicate_operand_aliases: dict[str, tuple[str, ...]] = {}
    for key in COVERAGE_KEYS:
        identifiers = required_ids.get(key)
        markers = required_markers.get(key)
        if not isinstance(identifiers, list) or not isinstance(markers, list):
            raise ValueError("EA Factory coverage requirement category is malformed")
        marker_by_id = {
            str(row.get("id")): str(row.get("marker"))
            for row in markers
            if isinstance(row, dict)
        }
        if set(marker_by_id) != set(identifiers) or any(
            marker_by_id.get(identifier) != coverage_marker(key, identifier)
            for identifier in identifiers
        ):
            raise ValueError("EA Factory coverage markers do not match required IDs")
        if key == "semanticDigests":
            predicate_operand_aliases = semantic_indicator_operand_aliases_for_source(
                lexical_source,
                semantic_profile,
                markers,
                target_platform=platform,
            )
        expected[key] = list(identifiers)
        marker_scopes: dict[str, list[dict[str, object]]] = {}
        for identifier in identifiers:
            marker = marker_by_id[identifier]
            scopes: list[dict[str, object]] = []
            # A preprocessor override changes every later use before the MQL
            # compiler sees it, so textual marker occurrences are not valid
            # evidence once that marker has been #define'd or #undef'd.
            if re.search(
                rf"(?mi)^\s*#\s*(?:define|undef)\s+{re.escape(marker)}\b",
                lexical_source,
            ):
                marker_scopes[identifier] = []
                continue
            for match in re.finditer(rf"\b{re.escape(marker)}\b", lexical_source):
                if _marker_is_declaration(lexical_source, match.start(), match.end()):
                    continue
                if platform == "tradingview":
                    scopes.append({
                        "name": "__pine_top__",
                        "body": lexical_source,
                        "tradingReachable": True,
                    })
                    continue
                function = _function_for_position(functions, match.start())
                if (
                    function is not None
                    and str(function.get("name") or "") in lifecycle_reachable
                ):
                    scopes.append({
                        **function,
                        "tradingReachable": (
                            str(function.get("name") or "") in trading_reachable
                        ),
                    })
            marker_scopes[identifier] = scopes
        observed[key] = [identifier for identifier in identifiers if marker_scopes[identifier]]
        missing[key] = [
            identifier for identifier in identifiers if identifier not in observed[key]
        ]
        semantic_observed[key] = [
            identifier
            for identifier in identifiers
            if _semantic_marker_supported(
                key,
                identifier,
                marker_by_id[identifier],
                marker_scopes[identifier],
                target_platform=platform,
                capabilities=capabilities,
                rule_roles=rule_roles,
                semantic_bindings=semantic_bindings,
                predicate_operand_aliases=predicate_operand_aliases,
                pending_state_ids=pending_state_ids,
                source=lexical_source,
                functions=functions,
                initialization_reachable=initialization_reachable,
                trading_reachable=trading_reachable,
                has_ctrade=has_ctrade,
            )
        ]
        semantic_missing[key] = [
            identifier
            for identifier in identifiers
            if identifier not in semantic_observed[key]
        ]

    capability_missing: list[str] = []
    management_semantic_ids = [
        identifier
        for identifier, binding in semantic_bindings.items()
        if binding.get("kind") == "management_feature"
    ]
    management_semantics_complete = bool(management_semantic_ids) and all(
        identifier in semantic_observed.get("semanticDigests", [])
        for identifier in management_semantic_ids
    )
    if not capabilities["entryPoint"]:
        capability_missing.append("REACHABLE_PROGRAM_ENTRY_MISSING")
    # A v2 EA source is not meaningful source code if it never submits an entry,
    # even when a malicious payload declares every marker token.
    if semantic_profile.get("requiresEntry") is not True:
        capability_missing.append("BLUEPRINT_ENTRY_RULE_MISSING")
    if not capabilities["tradeEntry"]:
        capability_missing.append("REACHABLE_TRADE_ENTRY_MISSING")
    if semantic_profile.get("requiresExit") is True and not capabilities["tradeExit"]:
        capability_missing.append("REACHABLE_TRADE_EXIT_MISSING")
    if (
        semantic_profile.get("requiresManagement") is True
        and not capabilities["tradeManagement"]
        and not management_semantics_complete
    ):
        capability_missing.append("REACHABLE_TRADE_MANAGEMENT_MISSING")
    if (
        semantic_profile.get("requiresPendingOrder") is True
        and not capabilities["pendingOrder"]
    ):
        capability_missing.append("REACHABLE_PENDING_ORDER_MISSING")
    if (
        semantic_profile.get("requiresRecovery") is True
        and not semantic_profile.get("recoveryRuleIds")
    ):
        capability_missing.append("BLUEPRINT_RECOVERY_RULE_MISSING")
    if (
        semantic_profile.get("requiresRecovery") is True
        and not capabilities["tradeEntry"]
    ):
        capability_missing.append("REACHABLE_RECOVERY_ENTRY_MISSING")
    if semantic_profile.get("requiresStopLoss") is True and not capabilities["stopLoss"]:
        capability_missing.append("STOP_LOSS_PATH_MISSING")
    if semantic_profile.get("requiresTakeProfit") is True and not capabilities["takeProfit"]:
        capability_missing.append("TAKE_PROFIT_PATH_MISSING")
    if semantic_profile.get("requiresClosedBar") is True and not capabilities["closedBar"]:
        capability_missing.append("CLOSED_BAR_SHIFT_EVIDENCE_MISSING")
    if expected["indicatorIds"] and not capabilities["indicatorAccess"]:
        capability_missing.append("INDICATOR_ACCESS_MISSING")
    if expected["stateIds"] and not capabilities["stateLogic"]:
        capability_missing.append("STATE_DECISION_PATH_MISSING")
    if not capabilities["controlledDecision"]:
        capability_missing.append("CONTROLLED_TRADING_DECISION_MISSING")

    result = {
        "schemaVersion": MANIFEST_SCHEMA_VERSION,
        "coverageMode": "blueprint_v4_section_and_rule_digest_bound_static_semantic_evidence",
        "targetPlatform": platform,
        "eaBlueprintDigest": requirements.get("eaBlueprintDigest"),
        "requirementsDigest": requirements.get("requirementsDigest"),
        "strategySpecDigest": str(strategy_spec_digest).lower(),
        "sourceDigest": str(source_digest).lower(),
        "expected": expected,
        "observed": observed,
        "missing": missing,
        "semanticObservedCounts": {
            key: len(semantic_observed[key]) for key in COVERAGE_KEYS
        },
        "semanticMissing": semantic_missing,
        "capabilityEvidence": capabilities,
        "capabilityMissing": capability_missing,
        "reachableFunctions": sorted(lifecycle_reachable)[:32],
        "complete": (
            all(not rows for rows in missing.values())
            and all(not rows for rows in semantic_missing.values())
            and not capability_missing
        ),
    }
    result["manifestDigest"] = _sha256(result)
    return result


def build_legacy_coverage_manifest(
    *,
    strategy_spec_digest: str,
    source_digest: str,
) -> dict:
    if (
        not _SHA256_PATTERN.fullmatch(str(strategy_spec_digest or "").lower())
        or not _SHA256_PATTERN.fullmatch(str(source_digest or "").lower())
    ):
        raise ValueError("EA Factory legacy coverage binding is invalid")
    empty = {key: [] for key in COVERAGE_KEYS}
    result = {
        "schemaVersion": MANIFEST_SCHEMA_VERSION,
        "coverageMode": "legacy_v1_a_m_only",
        "eaBlueprintDigest": None,
        "requirementsDigest": None,
        "strategySpecDigest": str(strategy_spec_digest).lower(),
        "sourceDigest": str(source_digest).lower(),
        "expected": empty,
        "observed": {key: [] for key in COVERAGE_KEYS},
        "missing": {key: [] for key in COVERAGE_KEYS},
        "complete": True,
    }
    result["manifestDigest"] = _sha256(result)
    return result
