from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping


REQUIREMENTS_SCHEMA_VERSION = "ea-factory-blueprint-coverage-requirements-v3"
MANIFEST_SCHEMA_VERSION = "ea-factory-blueprint-coverage-manifest-v3"
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
    "execution_contract",
    "indicator",
    "management_feature",
    "protection",
    "pseudocode",
    "recovery_safety",
    "risk_sizing",
    "state_transition",
    "test_vector",
}
_SEMANTIC_BINDING_ACTIONS = {
    "cancel_pending",
    "close_partial",
    "close_position",
    "entry",
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
_MQL_EXIT_PATTERN = re.compile(
    r"(?:\bOrderClose\s*\(|\brequest\s*\.\s*position\b[^;{}]*\bOrderSend\s*\()",
    re.IGNORECASE,
)
_MQL_CTRADE_EXIT_PATTERN = re.compile(
    r"\.\s*(?:PositionClose|PositionClosePartial)\s*\(", re.IGNORECASE
)
_MQL_CTRADE_MANAGEMENT_PATTERN = re.compile(
    r"\.\s*(?:PositionModify|PositionClosePartial)\s*\(", re.IGNORECASE
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


def _semantic_binding(
    kind: str,
    identity: str,
    value: object,
    *,
    actions: tuple[str, ...] = (),
) -> dict[str, object]:
    digest = _sha256(value)
    identifier = f"{kind}:{identity}:{digest}"
    return {
        "id": identifier,
        "kind": kind,
        "identity": identity,
        "digest": digest,
        "actions": sorted(set(actions)),
    }


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
    indicators = blueprint.get("indicators")
    if isinstance(indicators, list):
        for record in indicators:
            if not isinstance(record, Mapping):
                continue
            indicator_id = str(record.get("indicatorId") or "").strip()
            if indicator_id:
                bindings.append(
                    _semantic_binding(
                        "indicator",
                        indicator_id,
                        record,
                        actions=("indicator",),
                    )
                )

    risk = blueprint.get("riskAndSizing")
    if isinstance(risk, Mapping):
        bindings.append(
            _semantic_binding("risk_sizing", "root", risk, actions=("entry",))
        )

    protection = blueprint.get("tpSl")
    if isinstance(protection, Mapping):
        bindings.append(
            _semantic_binding("protection", "root", protection, actions=("entry",))
        )

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
                actions=("entry", "exit"),
            )
        )

    roles = {
        str(row.get("id")): str(row.get("action") or "other")
        for row in profile.get("ruleRoles", [])
        if isinstance(row, Mapping) and isinstance(row.get("id"), str)
    }
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
                            action = roles.get(str(rule_id), "other")
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
        r"\b([A-Za-z_][A-Za-z0-9_]{0,79})\s*\([^;{}]{0,1000}\)\s*\{"
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
            or (has_ctrade and _MQL_CTRADE_MANAGEMENT_PATTERN.search(source))
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
        return bool(
            re.search(r"\bOrderClose\s*\(", source)
            or (
                has_ctrade
                and re.search(r"\.\s*PositionClosePartial\s*\(", source, re.IGNORECASE)
            )
            or (has_order_send and has_position_binding)
        )
    if action == "scale_out":
        return bool(
            _mql_action_in_text(source, "close_partial", has_ctrade=has_ctrade)
            or (
                has_ctrade
                and re.search(r"\.\s*PositionClose\s*\(", source, re.IGNORECASE)
            )
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
        pattern = {
            "entry": _PINE_ENTRY_PATTERN,
            "exit": _PINE_EXIT_PATTERN,
            "management": _PINE_EXIT_PATTERN,
            "pending": _PINE_PENDING_PATTERN,
            "move_stop_loss": _PINE_EXIT_PATTERN,
            "move_take_profit": _PINE_EXIT_PATTERN,
            "close_partial": _PINE_EXIT_PATTERN,
            "scale_out": _PINE_EXIT_PATTERN,
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
            if any(re.search(rf"\b{re.escape(name)}\b", condition) for name in aliases) and _action_in_text(
                body,
                action,
                target_platform=target_platform,
                has_ctrade=False,
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
            marker_controls_branch = bool(
                re.search(rf"\b{re.escape(marker)}\b", condition)
                or any(
                    re.search(rf"\b{re.escape(name)}\s*\(", condition)
                    for name in signal_functions
                )
            )
            if not marker_controls_branch:
                continue
            expanded_body = _expanded_fragment_source(body, functions)
            if _action_in_text(
                expanded_body,
                action,
                target_platform=target_platform,
                has_ctrade=has_ctrade,
            ):
                return True
    return False


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
            if kind == "indicator":
                if _INDICATOR_PATTERN.search(scope):
                    return True
                continue
            if kind in {"risk_sizing", "protection"}:
                if (
                    row.get("tradingReachable") is True
                    and _scope_has_controlled_comparison(scope)
                    and _marker_action_bound(
                        marker,
                        scopes,
                        "entry",
                        source=source,
                        target_platform=target_platform,
                        functions=functions,
                        trading_reachable=trading_reachable,
                        has_ctrade=has_ctrade,
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
            set(binding) != {"id", "kind", "identity", "digest", "actions"}
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
        expected[key] = list(identifiers)
        marker_scopes: dict[str, list[dict[str, object]]] = {}
        for identifier in identifiers:
            marker = marker_by_id[identifier]
            scopes: list[dict[str, object]] = []
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
        "coverageMode": "blueprint_v3_digest_bound_static_semantic_evidence",
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
