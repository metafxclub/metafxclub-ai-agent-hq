from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping


REQUIREMENTS_SCHEMA_VERSION = "ea-factory-blueprint-coverage-requirements-v2"
MANIFEST_SCHEMA_VERSION = "ea-factory-blueprint-coverage-manifest-v2"
COVERAGE_KEYS = (
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
    "ruleIds": "RULE",
    "inputIds": "INPUT",
    "indicatorIds": "INDICATOR",
    "stateIds": "STATE",
    "testCaseIds": "TEST",
}
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_SUPPORTED_PLATFORMS = {"mt4", "mt5", "tradingview"}
_MQL_LIFECYCLE_ROOTS = {
    "OnInit",
    "OnTick",
    "OnTimer",
    "OnCalculate",
    "start",
    "init",
}
_MQL_TRADING_ROOTS = {"OnTick", "OnTimer", "start"}
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
_PINE_ENTRY_PATTERN = re.compile(r"\bstrategy\.(?:entry|order)\s*\(")
_PINE_EXIT_PATTERN = re.compile(r"\bstrategy\.(?:close|close_all|exit)\s*\(")
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


def _rule_roles(node: object) -> list[dict[str, str]]:
    """Collect the stable phase/side role for every canonical rule ID."""

    result: dict[str, dict[str, str]] = {}

    def visit(value: object, inherited_phase: str = "", inherited_side: str = "") -> None:
        if isinstance(value, Mapping):
            phase = str(value.get("phase") or inherited_phase).strip().lower()
            side = str(value.get("side") or inherited_side).strip().lower()
            rule_id = value.get("ruleId")
            if isinstance(rule_id, str) and rule_id.strip():
                result[rule_id.strip()] = {
                    "id": rule_id.strip(),
                    "phase": phase or "other",
                    "side": side or "both",
                }
            for key, child in value.items():
                child_phase = phase
                child_side = side
                lexical_key = str(key).strip().lower()
                if lexical_key in {"setup", "entry", "exit", "management", "order_management"}:
                    child_phase = lexical_key.replace("order_", "")
                if lexical_key in {"buy", "sell", "both"}:
                    child_side = lexical_key
                visit(child, child_phase, child_side)
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child, inherited_phase, inherited_side)

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
    return {
        "ruleRoles": roles,
        "requiresEntry": any(row["phase"] == "entry" for row in roles),
        "requiresExit": any(row["phase"] == "exit" for row in roles),
        "requiresManagement": any(row["phase"] == "management" for row in roles),
        "requiresStopLoss": stop_loss.get("enabled") is True,
        "requiresTakeProfit": take_profit.get("enabled") is True,
        "requiresClosedBar": (
            str(bar_semantics.get("evaluateOn") or "").lower() == "new_closed_bar"
        ),
    }


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
    if not isinstance(blueprint, Mapping) or not _SHA256_PATTERN.fullmatch(
        str(blueprint_digest or "").lower()
    ):
        raise ValueError("EA Factory Blueprint coverage binding is invalid")
    required_ids = {
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
        "eaBlueprintDigest": str(blueprint_digest).lower(),
        "requiredIds": required_ids,
        "requiredMarkers": required_markers,
        "semanticProfile": _semantic_profile(blueprint),
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
    return False


def _action_in_text(
    source: str,
    action: str,
    *,
    target_platform: str,
    has_ctrade: bool,
) -> bool:
    if target_platform == "tradingview":
        pattern = _PINE_ENTRY_PATTERN if action == "entry" else _PINE_EXIT_PATTERN
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
    return {
        "entryPoint": bool(trading_reachable),
        "tradeEntry": entry_detected,
        "tradeExit": exit_detected,
        "tradeManagement": any(
            _mql_action_in_text(body, "management", has_ctrade=has_ctrade)
            for body in action_sources
        ),
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
    source: str,
    functions: list[dict[str, object]],
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
        if key == "ruleIds":
            if row.get("tradingReachable") is not True:
                continue
            role = rule_roles.get(identifier, {})
            phase = str(role.get("phase") or "other")
            if not _scope_has_controlled_comparison(scope):
                continue
            if phase == "entry" and not capabilities.get("tradeEntry"):
                continue
            if phase == "exit" and not capabilities.get("tradeExit"):
                continue
            if phase == "management" and not capabilities.get("tradeManagement"):
                continue
            if phase in {"entry", "exit", "management"} and not _marker_action_bound(
                marker,
                scopes,
                phase,
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
                    for action in ("entry", "exit", "management")
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
    if (
        set(rule_roles) != set(required_ids.get("ruleIds") or [])
        or any(
            type(semantic_profile.get(key)) is not bool
            for key in (
                "requiresEntry",
                "requiresExit",
                "requiresManagement",
                "requiresStopLoss",
                "requiresTakeProfit",
                "requiresClosedBar",
            )
        )
    ):
        raise ValueError("EA Factory coverage semantic profile is malformed")
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
                source=lexical_source,
                functions=functions,
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
    ):
        capability_missing.append("REACHABLE_TRADE_MANAGEMENT_MISSING")
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
        "coverageMode": "blueprint_v2_static_semantic_evidence",
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
