from __future__ import annotations

import copy
import hashlib
import math
import re
from decimal import Decimal, InvalidOperation

from ea_factory_blueprint_coverage import (
    build_coverage_requirements,
    rule_predicate_expression_supported,
    semantic_indicator_operand_aliases_for_source,
    strip_statically_dead_mql_regions,
)


REQUIREMENTS_SCHEMA_VERSION = "ea-factory-indicator-coverage-requirements-v1"
MANIFEST_SCHEMA_VERSION = "ea-factory-indicator-coverage-manifest-v1"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_SUPPORTED_PLATFORMS = {"mt4", "mt5"}
_RULE_MARKER_PATTERN = re.compile(r"EA_COV_RULE_[A-Z0-9_]{1,80}")


def _payload_digest(*parts: object) -> str:
    # Keep byte-for-byte compatibility with bridge_server.payload_digest.  The
    # insertion order of these small trusted dictionaries is part of the
    # persisted v1 contract, so this intentionally does not sort/JSON-encode.
    joined = "\n".join(str(part or "") for part in parts)
    return hashlib.sha256(joined.encode("utf-8", errors="replace")).hexdigest()


def _mql_lexical_views(source_text: str) -> tuple[str, tuple[str, ...]] | None:
    """Return MQL code with comments/string literals replaced by whitespace."""

    output = list(source_text)
    strings: list[tuple[int, str]] = []
    index = 0
    length = len(source_text)
    state = "code"
    string_start = -1
    string_value: list[str] = []
    while index < length:
        current = source_text[index]
        following = source_text[index + 1] if index + 1 < length else ""
        if state == "code":
            if current == "/" and following == "/":
                output[index] = output[index + 1] = " "
                index += 2
                state = "line_comment"
                continue
            if current == "/" and following == "*":
                output[index] = output[index + 1] = " "
                index += 2
                state = "block_comment"
                continue
            if current == '"':
                string_start = index
                string_value = []
                output[index] = " "
                index += 1
                state = "string"
                continue
        elif state == "line_comment":
            if current in "\r\n":
                state = "code"
            else:
                output[index] = " "
            index += 1
            continue
        elif state == "block_comment":
            if current == "*" and following == "/":
                output[index] = output[index + 1] = " "
                index += 2
                state = "code"
                continue
            if current not in "\r\n":
                output[index] = " "
            index += 1
            continue
        elif state == "string":
            output[index] = " " if current not in "\r\n" else current
            if current == "\\" and index + 1 < length:
                string_value.append(source_text[index + 1])
                if source_text[index + 1] not in "\r\n":
                    output[index + 1] = " "
                index += 2
                continue
            if current == '"':
                strings.append((string_start, "".join(string_value)))
                state = "code"
                index += 1
                continue
            if current in "\r\n":
                return None
            string_value.append(current)
            index += 1
            continue
        index += 1
    if state not in {"code", "line_comment"}:
        return None
    code = "".join(output)
    descriptions: list[str] = []
    for start, value in strings:
        line_start = code.rfind("\n", 0, start) + 1
        prefix = code[line_start:start]
        if re.fullmatch(r"\s*#property\s+description\s*", prefix, flags=re.IGNORECASE):
            descriptions.append(value)
    return code, tuple(descriptions)


def _mql_function_records(code: str) -> list[dict] | None:
    """Return bounded function bodies with their exact source spans."""

    depth = 0
    for character in code:
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth < 0:
                return None
    if depth:
        return None
    records: list[dict] = []
    seen_names: set[str] = set()
    declaration = re.compile(
        r"\b(?:bool|int|void|double)\s+([A-Za-z_]\w*)\s*"
        r"\(([^;{}]{0,800})\)\s*\{",
        flags=re.IGNORECASE | re.DOTALL,
    )
    for match in declaration.finditer(code):
        normalized_name = match.group(1).lower()
        # Overloaded/duplicated names make the bounded call graph ambiguous.
        if normalized_name in seen_names:
            return None
        seen_names.add(normalized_name)
        opening = match.end() - 1
        nested = 1
        cursor = opening + 1
        while cursor < len(code) and nested:
            if code[cursor] == "{":
                nested += 1
            elif code[cursor] == "}":
                nested -= 1
            cursor += 1
        if nested:
            return None
        records.append({
            "name": match.group(1),
            "normalizedName": normalized_name,
            "parameters": match.group(2),
            "body": code[opening + 1 : cursor - 1],
            "bodyStart": opening + 1,
            "bodyEnd": cursor - 1,
        })
    return records


def _mql_function_bodies(code: str, name_pattern: str) -> list[str] | None:
    records = _mql_function_records(code)
    if records is None:
        return None
    return [
        str(record["body"])
        for record in records
        if re.search(name_pattern, str(record["name"]), flags=re.IGNORECASE)
    ]


def _balanced_close(text: str, opening: int, opener: str, closer: str) -> int | None:
    if opening >= len(text) or text[opening] != opener:
        return None
    depth = 1
    cursor = opening + 1
    while cursor < len(text):
        if text[cursor] == opener:
            depth += 1
        elif text[cursor] == closer:
            depth -= 1
            if depth == 0:
                return cursor
        cursor += 1
    return None


def _mql_if_region_records(code: str) -> list[dict] | None:
    """Return bounded ``if`` predicates, bodies, and exact source spans."""

    regions: list[dict] = []
    for match in re.finditer(r"\bif\s*\(", code, flags=re.IGNORECASE):
        opening = code.find("(", match.start(), match.end())
        closing = _balanced_close(code, opening, "(", ")")
        if closing is None:
            return None
        cursor = closing + 1
        while cursor < len(code) and code[cursor].isspace():
            cursor += 1
        if cursor >= len(code):
            return None
        if code[cursor] == "{":
            body_close = _balanced_close(code, cursor, "{", "}")
            if body_close is None:
                return None
            body = code[cursor + 1 : body_close]
            body_start = cursor + 1
            body_end = body_close
            region_end = body_close + 1
        else:
            statement_close = code.find(";", cursor, min(len(code), cursor + 2000))
            if statement_close < 0:
                return None
            body = code[cursor : statement_close + 1]
            body_start = cursor
            body_end = statement_close + 1
            region_end = statement_close + 1
        regions.append({
            "condition": code[opening + 1 : closing],
            "body": body,
            "start": match.start(),
            "end": region_end,
            "bodyStart": body_start,
            "bodyEnd": body_end,
        })
    return regions


def _mql_if_regions(code: str) -> list[tuple[str, str]] | None:
    """Return bounded ``if`` predicates and the statements they control."""

    records = _mql_if_region_records(code)
    if records is None:
        return None
    return [
        (str(record["condition"]), str(record["body"]))
        for record in records
    ]


def _indicator_contract_projection(ea_requirements: dict) -> dict:
    """Keep only the immutable semantic facts an Indicator must implement."""

    semantic_profile = ea_requirements.get("semanticProfile")
    required_markers = ea_requirements.get("requiredMarkers")
    if not isinstance(semantic_profile, dict) or not isinstance(required_markers, dict):
        raise ValueError("EA Factory Indicator semantic contract is malformed.")
    bindings = semantic_profile.get("semanticBindings")
    semantic_markers = required_markers.get("semanticDigests")
    rule_markers = required_markers.get("ruleIds")
    if (
        not isinstance(bindings, list)
        or not isinstance(semantic_markers, list)
        or not isinstance(rule_markers, list)
    ):
        raise ValueError("EA Factory Indicator semantic contract is malformed.")

    indicator_bindings = [
        copy.deepcopy(row)
        for row in bindings
        if isinstance(row, dict) and row.get("kind") == "indicator"
    ]
    indicator_binding_ids = {
        str(row.get("id") or "") for row in indicator_bindings
    }
    indicator_marker_rows = [
        copy.deepcopy(row)
        for row in semantic_markers
        if isinstance(row, dict) and str(row.get("id") or "") in indicator_binding_ids
    ]
    if len(indicator_marker_rows) != len(indicator_binding_ids):
        raise ValueError("EA Factory Indicator operand bindings are incomplete.")

    rule_binding_rows: dict[str, list[dict]] = {}
    for row in bindings:
        if not isinstance(row, dict) or row.get("kind") != "rule_semantics":
            continue
        identity = str(row.get("identity") or "")
        rule_binding_rows.setdefault(identity, []).append(row)
    rule_predicates: list[dict] = []
    for marker_row in rule_markers:
        rule_id = str(marker_row.get("id") or "") if isinstance(marker_row, dict) else ""
        matches = rule_binding_rows.get(rule_id, [])
        if not rule_id or len(matches) != 1:
            raise ValueError("EA Factory Indicator rule semantics are incomplete.")
        binding = matches[0]
        predicate = binding.get("predicate")
        if not isinstance(predicate, dict):
            raise ValueError("EA Factory Indicator rule predicate is missing.")
        rule_predicates.append({
            "ruleId": rule_id,
            "semanticBindingId": str(binding.get("id") or ""),
            "predicate": copy.deepcopy(predicate),
        })
    return {
        "indicatorSemanticProfile": {
            "semanticBindings": indicator_bindings,
        },
        "requiredIndicatorSemanticMarkers": indicator_marker_rows,
        "requiredRulePredicates": rule_predicates,
    }


def build_indicator_coverage_requirements(
    blueprint: dict,
    blueprint_digest: str,
) -> dict:
    """Project immutable rule identities into a no-trade Indicator contract."""

    ea_requirements = build_coverage_requirements(blueprint, blueprint_digest)
    required_markers = copy.deepcopy(
        (
            ea_requirements.get("requiredMarkers")
            if isinstance(ea_requirements.get("requiredMarkers"), dict)
            else {}
        ).get("ruleIds")
        or []
    )
    semantic_contract = _indicator_contract_projection(ea_requirements)
    result = {
        "schemaVersion": REQUIREMENTS_SCHEMA_VERSION,
        "eaBlueprintDigest": str(blueprint_digest).lower(),
        "requiredRuleMarkers": required_markers,
        **semantic_contract,
        "programRequirements": {
            "programKind": "custom_indicator",
            "calculationEntryPoint": "OnCalculate",
            "indicatorBufferRequired": True,
            "tradingFunctionsForbidden": True,
            "backtestApplicable": False,
        },
    }
    result["requirementsDigest"] = _payload_digest(
        REQUIREMENTS_SCHEMA_VERSION,
        result,
    )
    return result


def indicator_coverage_requirements_valid(
    value: object,
    blueprint: dict,
    blueprint_digest: str,
) -> bool:
    try:
        expected = build_indicator_coverage_requirements(blueprint, blueprint_digest)
    except (TypeError, ValueError):
        return False
    return isinstance(value, dict) and value == expected


def _condition_requires_rule_marker(
    condition: str,
    marker: str,
    all_rule_markers: set[str],
) -> bool:
    """Prove that a branch cannot execute when its one rule marker is false."""

    marker_word = rf"\b{re.escape(marker)}\b"
    if (
        re.search(marker_word, condition, flags=re.IGNORECASE) is None
        or re.search(r"\|\||\bor\b|\?|(?<![=!])!(?!=)", condition, flags=re.IGNORECASE)
        or re.search(
            rf"(?:!\s*{marker_word}|{marker_word}\s*(?:==\s*false|!=\s*true|==\s*0|!=\s*1))",
            condition,
            flags=re.IGNORECASE,
        )
    ):
        return False
    present_rule_markers = {
        candidate
        for candidate in all_rule_markers
        if re.search(rf"\b{re.escape(candidate)}\b", condition, flags=re.IGNORECASE)
    }
    return present_rule_markers == {marker}


def _strip_balanced_outer_parentheses(value: str) -> str:
    result = value.strip()
    while result.startswith("(") and result.endswith(")"):
        closing = _balanced_close(result, 0, "(", ")")
        if closing != len(result) - 1:
            break
        result = result[1:-1].strip()
    return result


_MQL_EXPRESSION_TOKEN = re.compile(
    r"\s*(?:"
    r"(?P<number>(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][+-]?\d+)?)|"
    r"(?P<identifier>[A-Za-z_]\w*)|"
    r"(?P<operator>\|\||&&|==|!=|<=|>=|[+\-*/%<>()\[\],!?:])"
    r")"
)
_MQL_BINARY_PRECEDENCE = {
    "||": 1,
    "&&": 2,
    "==": 3,
    "!=": 3,
    "<": 4,
    "<=": 4,
    ">": 4,
    ">=": 4,
    "+": 5,
    "-": 5,
    "*": 6,
    "/": 6,
    "%": 6,
}
_MQL_MARKET_ARRAYS = {
    "open",
    "high",
    "low",
    "close",
    "time",
    "tick_volume",
    "volume",
    "spread",
}
_MQL_MARKET_SCALARS = {"ask", "bid"}
_MQL_MARKET_CALLS = {
    "ima",
    "irsi",
    "iatr",
    "iadx",
    "ibands",
    "icci",
    "imacd",
    "imomentum",
    "istochastic",
    "iwpr",
    "icustom",
    "iclose",
    "iopen",
    "ihigh",
    "ilow",
    "itime",
    "ivolume",
    "copybuffer",
}
_MQL_VALUE_WRAPPERS = {
    "normalizedouble",
    "mathabs",
    "mathfloor",
    "mathceil",
    "mathround",
}
_MQL_ALIAS_EVENT = re.compile(
    r"\b(?:(?P<type>double|float|int|long|bool)\s+)?"
    r"(?P<name>[A-Za-z_]\w*)\s*"
    r"(?P<operator>\+=|-=|\*=|/=|%=|(?<![=!<>])=(?!=))\s*"
    r"(?P<value>[^;\r\n]{1,800});",
    flags=re.IGNORECASE,
)


def _tokenize_mql_expression(value: str) -> list[tuple[str, str]] | None:
    if not isinstance(value, str) or not value.strip() or len(value) > 800:
        return None
    tokens: list[tuple[str, str]] = []
    cursor = 0
    while cursor < len(value):
        match = _MQL_EXPRESSION_TOKEN.match(value, cursor)
        if match is None:
            if value[cursor:].strip():
                return None
            break
        kind = "number" if match.group("number") is not None else (
            "identifier" if match.group("identifier") is not None else "operator"
        )
        tokens.append((kind, str(match.group(kind))))
        if len(tokens) > 256:
            return None
        cursor = match.end()
    return tokens


class _MqlExpressionParser:
    def __init__(self, tokens: list[tuple[str, str]]):
        self.tokens = tokens
        self.index = 0

    def _peek(self, value: str | None = None) -> tuple[str, str] | None:
        token = self.tokens[self.index] if self.index < len(self.tokens) else None
        if value is not None and (token is None or token[1] != value):
            return None
        return token

    def _take(self, value: str | None = None) -> tuple[str, str] | None:
        token = self._peek(value)
        if token is not None:
            self.index += 1
        return token

    def parse(self) -> tuple | None:
        expression = self._expression(0)
        return expression if expression is not None and self.index == len(self.tokens) else None

    def _expression(self, minimum_precedence: int) -> tuple | None:
        left = self._unary()
        if left is None:
            return None
        while True:
            token = self._peek()
            operator = token[1] if token is not None else ""
            precedence = _MQL_BINARY_PRECEDENCE.get(operator)
            if precedence is None or precedence < minimum_precedence:
                break
            self._take()
            right = self._expression(precedence + 1)
            if right is None:
                return None
            left = ("binary", operator, left, right)
        if minimum_precedence == 0 and self._take("?") is not None:
            when_true = self._expression(0)
            if when_true is None or self._take(":") is None:
                return None
            when_false = self._expression(0)
            if when_false is None:
                return None
            left = ("ternary", left, when_true, when_false)
        return left

    def _unary(self) -> tuple | None:
        token = self._peek()
        if token is not None and token[1] in {"!", "+", "-"}:
            self._take()
            operand = self._unary()
            return None if operand is None else ("unary", token[1], operand)
        return self._primary()

    def _primary(self) -> tuple | None:
        token = self._take()
        if token is None:
            return None
        kind, value = token
        if kind == "number":
            try:
                return ("number", Decimal(value))
            except InvalidOperation:
                return None
        if value == "(":
            expression = self._expression(0)
            return expression if expression is not None and self._take(")") else None
        if kind != "identifier":
            return None
        name = value.lower()
        if self._take("(") is not None:
            arguments: list[tuple] = []
            if self._peek(")") is None:
                while True:
                    argument = self._expression(0)
                    if argument is None:
                        return None
                    arguments.append(argument)
                    if len(arguments) > 32:
                        return None
                    if self._take(",") is None:
                        break
            if self._take(")") is None:
                return None
            return ("call", name, tuple(arguments))
        if self._take("[") is not None:
            index = self._expression(0)
            if index is None or self._take("]") is None:
                return None
            return ("array", name, index)
        return ("identifier", name)


def _parse_mql_expression(value: str) -> tuple | None:
    tokens = _tokenize_mql_expression(value)
    return _MqlExpressionParser(tokens).parse() if tokens is not None else None


def _symbolic_value(
    *,
    constant_known: bool = False,
    constant: Decimal | None = None,
    market_sources: set[str] | None = None,
    prior_buffer: bool = False,
    proven: bool = True,
) -> dict:
    return {
        "constantKnown": constant_known,
        "constant": constant if constant_known else None,
        "marketSources": set(market_sources or set()),
        "priorBuffer": prior_buffer,
        "proven": proven,
    }


def _constant_value(value: Decimal) -> dict:
    return _symbolic_value(constant_known=True, constant=value)


def _combine_symbolic(left: dict, right: dict, *, proven: bool | None = None) -> dict:
    return _symbolic_value(
        market_sources=set(left["marketSources"]) | set(right["marketSources"]),
        prior_buffer=bool(left["priorBuffer"] or right["priorBuffer"]),
        proven=(left["proven"] and right["proven"]) if proven is None else proven,
    )


def _constant_binary(operator: str, left: Decimal, right: Decimal) -> Decimal | None:
    try:
        if operator == "+":
            return left + right
        if operator == "-":
            return left - right
        if operator == "*":
            return left * right
        if operator == "/" and right != 0:
            return left / right
        if operator == "%" and right != 0:
            return left % right
        if operator in {"==", "!=", "<", "<=", ">", ">="}:
            matched = {
                "==": left == right,
                "!=": left != right,
                "<": left < right,
                "<=": left <= right,
                ">": left > right,
                ">=": left >= right,
            }[operator]
            return Decimal(1 if matched else 0)
        if operator == "&&":
            return Decimal(1 if left != 0 and right != 0 else 0)
        if operator == "||":
            return Decimal(1 if left != 0 or right != 0 else 0)
    except (InvalidOperation, OverflowError, ZeroDivisionError):
        return None
    return None


def _mql_parameter_names(value: str) -> list[str] | None:
    if not value.strip():
        return []
    parts = [part.strip() for part in value.split(",")]
    if len(parts) > 32:
        return None
    result: list[str] = []
    for part in parts:
        declaration = part.split("=", 1)[0]
        identifiers = re.findall(r"[A-Za-z_]\w*", declaration)
        if not identifiers:
            return None
        name = identifiers[-1].lower()
        if name in result:
            return None
        result.append(name)
    return result


def _mql_alias_environment(
    code_prefix: str,
    *,
    initial: dict[str, dict] | None,
    helper_records: dict[str, dict],
    buffer_names: set[str],
    depth: int,
) -> dict[str, dict]:
    aliases = dict(initial or {})
    events = list(_MQL_ALIAS_EVENT.finditer(code_prefix))
    if len(events) > 256:
        return {}
    for event in events:
        name = event.group("name").lower()
        declared = event.group("type") is not None
        if not declared and name not in aliases:
            continue
        expression = _parse_mql_expression(event.group("value"))
        if expression is None:
            aliases[name] = _symbolic_value(proven=False)
            continue
        operator = event.group("operator")
        if operator != "=":
            expression = (
                "binary",
                operator[0],
                ("identifier", name),
                expression,
            )
        aliases[name] = _summarize_mql_node(
            expression,
            aliases=aliases,
            helper_records=helper_records,
            buffer_names=buffer_names,
            depth=depth,
        )
        if len(aliases) > 128:
            return {}
    return aliases


def _summarize_mql_node(
    node: tuple,
    *,
    aliases: dict[str, dict],
    helper_records: dict[str, dict],
    buffer_names: set[str],
    depth: int = 0,
) -> dict:
    if depth > 6 or not isinstance(node, tuple) or not node:
        return _symbolic_value(proven=False)
    kind = node[0]
    if kind == "number":
        return _constant_value(node[1])
    if kind == "identifier":
        name = str(node[1]).lower()
        if name in aliases:
            return copy.deepcopy(aliases[name])
        if name in {"true", "false", "null", "empty_value", "nan"}:
            return _constant_value(Decimal(1 if name == "true" else 0))
        if name in _MQL_MARKET_SCALARS:
            return _symbolic_value(market_sources={name})
        # Inputs/constants remain symbolic scalars.  They cannot prove a
        # market-derived output alone, but may safely scale a market series.
        return _symbolic_value()
    if kind == "array":
        name = str(node[1]).lower()
        index_summary = _summarize_mql_node(
            node[2],
            aliases=aliases,
            helper_records=helper_records,
            buffer_names=buffer_names,
            depth=depth + 1,
        )
        if name in {item.lower() for item in buffer_names}:
            return _symbolic_value(
                prior_buffer=True,
                proven=index_summary["proven"],
            )
        if name in _MQL_MARKET_ARRAYS:
            return _symbolic_value(
                market_sources={name},
                prior_buffer=index_summary["priorBuffer"],
                proven=index_summary["proven"],
            )
        return _symbolic_value(
            prior_buffer=index_summary["priorBuffer"],
            proven=False,
        )
    if kind == "unary":
        operand = _summarize_mql_node(
            node[2],
            aliases=aliases,
            helper_records=helper_records,
            buffer_names=buffer_names,
            depth=depth + 1,
        )
        if operand["constantKnown"]:
            value = operand["constant"]
            if node[1] == "-":
                value = -value
            elif node[1] == "!":
                value = Decimal(1 if value == 0 else 0)
            return _symbolic_value(
                constant_known=True,
                constant=value,
                prior_buffer=operand["priorBuffer"],
                proven=operand["proven"],
            )
        return operand
    if kind == "binary":
        operator, left_node, right_node = node[1], node[2], node[3]
        left = _summarize_mql_node(
            left_node,
            aliases=aliases,
            helper_records=helper_records,
            buffer_names=buffer_names,
            depth=depth + 1,
        )
        right = _summarize_mql_node(
            right_node,
            aliases=aliases,
            helper_records=helper_records,
            buffer_names=buffer_names,
            depth=depth + 1,
        )
        combined = _combine_symbolic(left, right)
        if left_node == right_node and operator in {"-", "%"}:
            return {**combined, "constantKnown": True, "constant": Decimal(0), "marketSources": set()}
        if left_node == right_node and operator == "/":
            return {**combined, "constantKnown": True, "constant": Decimal(1), "marketSources": set()}
        if left["constantKnown"] and right["constantKnown"]:
            result = _constant_binary(operator, left["constant"], right["constant"])
            if result is not None:
                return {**combined, "constantKnown": True, "constant": result, "marketSources": set()}
        if operator == "*" and (
            (left["constantKnown"] and left["constant"] == 0)
            or (right["constantKnown"] and right["constant"] == 0)
        ):
            return {**combined, "constantKnown": True, "constant": Decimal(0), "marketSources": set()}
        if operator == "/" and left["constantKnown"] and left["constant"] == 0:
            return {**combined, "constantKnown": True, "constant": Decimal(0), "marketSources": set()}
        if operator in {"+", "-"} and right["constantKnown"] and right["constant"] == 0:
            return {**left, "priorBuffer": combined["priorBuffer"], "proven": combined["proven"]}
        if operator == "+" and left["constantKnown"] and left["constant"] == 0:
            return {**right, "priorBuffer": combined["priorBuffer"], "proven": combined["proven"]}
        if operator in {"*", "/"} and right["constantKnown"] and right["constant"] == 1:
            return {**left, "priorBuffer": combined["priorBuffer"], "proven": combined["proven"]}
        if operator == "*" and left["constantKnown"] and left["constant"] == 1:
            return {**right, "priorBuffer": combined["priorBuffer"], "proven": combined["proven"]}
        return combined
    if kind == "ternary":
        condition_node, true_node, false_node = node[1], node[2], node[3]
        condition = _summarize_mql_node(
            condition_node,
            aliases=aliases,
            helper_records=helper_records,
            buffer_names=buffer_names,
            depth=depth + 1,
        )
        when_true = _summarize_mql_node(
            true_node,
            aliases=aliases,
            helper_records=helper_records,
            buffer_names=buffer_names,
            depth=depth + 1,
        )
        when_false = _summarize_mql_node(
            false_node,
            aliases=aliases,
            helper_records=helper_records,
            buffer_names=buffer_names,
            depth=depth + 1,
        )
        combined = _combine_symbolic(condition, _combine_symbolic(when_true, when_false))
        if condition["constantKnown"]:
            selected = when_true if condition["constant"] != 0 else when_false
            return {**selected, "priorBuffer": combined["priorBuffer"], "proven": combined["proven"]}
        if true_node == false_node or (
            when_true["constantKnown"]
            and when_false["constantKnown"]
            and when_true["constant"] == when_false["constant"]
        ):
            return {
                **when_true,
                "priorBuffer": combined["priorBuffer"],
                "proven": combined["proven"],
            }
        return combined
    if kind == "call":
        name = str(node[1]).lower()
        argument_nodes = list(node[2])
        arguments = [
            _summarize_mql_node(
                argument,
                aliases=aliases,
                helper_records=helper_records,
                buffer_names=buffer_names,
                depth=depth + 1,
            )
            for argument in argument_nodes
        ]
        prior_buffer = any(value["priorBuffer"] for value in arguments)
        proven_arguments = all(value["proven"] for value in arguments)
        argument_sources = set().union(
            *(value["marketSources"] for value in arguments),
        ) if arguments else set()
        if name in _MQL_VALUE_WRAPPERS and arguments:
            return {
                **arguments[0],
                "priorBuffer": prior_buffer,
                "proven": proven_arguments,
            }
        if name in {"mathsin", "mathcos"} and len(arguments) == 1:
            argument = arguments[0]
            if argument["constantKnown"]:
                numeric = float(argument["constant"])
                result = math.sin(numeric) if name == "mathsin" else math.cos(numeric)
                return _symbolic_value(
                    constant_known=True,
                    constant=Decimal(str(result)),
                    prior_buffer=prior_buffer,
                    proven=proven_arguments,
                )
            return _symbolic_value(
                market_sources=argument_sources,
                prior_buffer=prior_buffer,
                proven=proven_arguments,
            )
        if name in _MQL_MARKET_CALLS:
            return _symbolic_value(
                market_sources={f"call:{name}"} | argument_sources,
                prior_buffer=prior_buffer,
                proven=proven_arguments,
            )
        helper = helper_records.get(name)
        if helper is not None and depth < 6:
            parameters = _mql_parameter_names(str(helper.get("parameters") or ""))
            body = str(helper.get("body") or "")
            returns = list(
                re.finditer(r"\breturn\s+(?P<value>[^;\r\n]{1,800});", body, flags=re.IGNORECASE)
            )
            if parameters is None or len(parameters) != len(arguments) or len(returns) != 1:
                return _symbolic_value(prior_buffer=prior_buffer, proven=False)
            return_match = returns[0]
            helper_aliases = _mql_alias_environment(
                body[: return_match.start()],
                initial=dict(zip(parameters, arguments)),
                helper_records=helper_records,
                buffer_names=buffer_names,
                depth=depth + 1,
            )
            returned = _parse_mql_expression(return_match.group("value"))
            if returned is None:
                return _symbolic_value(prior_buffer=prior_buffer, proven=False)
            return _summarize_mql_node(
                returned,
                aliases=helper_aliases,
                helper_records=helper_records,
                buffer_names=buffer_names,
                depth=depth + 1,
            )
        return _symbolic_value(
            market_sources=argument_sources,
            prior_buffer=prior_buffer,
            proven=False,
        )
    return _symbolic_value(proven=False)


def _indicator_output_value_is_meaningful(
    value: str,
    target: str,
    *,
    analysis_code: str = "",
    assignment_position: int = 0,
    function_records: list[dict] | None = None,
    buffer_names: set[str] | None = None,
) -> bool:
    parsed = _parse_mql_expression(value)
    if parsed is None:
        return False
    normalized_buffers = {str(name).lower() for name in (buffer_names or set())}
    helpers = {
        str(record.get("normalizedName") or ""): record
        for record in (function_records or [])
        if isinstance(record, dict) and record.get("normalizedName")
    }
    aliases = _mql_alias_environment(
        analysis_code[: max(0, assignment_position)],
        initial=None,
        helper_records=helpers,
        buffer_names=normalized_buffers,
        depth=0,
    )
    summary = _summarize_mql_node(
        parsed,
        aliases=aliases,
        helper_records=helpers,
        buffer_names=normalized_buffers,
    )
    return bool(
        summary["proven"]
        and summary["marketSources"]
        and not summary["constantKnown"]
        and not summary["priorBuffer"]
        and re.sub(r"\s+", "", value).lower()
        != re.sub(r"\s+", "", target).lower()
    )


def _signal_buffer_assignment_records(
    body: str,
    buffer_names: set[str],
    *,
    require_reachable: bool = False,
    source_offset: int = 0,
    analysis_code: str | None = None,
    function_records: list[dict] | None = None,
) -> list[dict]:
    if not buffer_names:
        return []
    result: list[dict] = []
    pattern = re.compile(
        rf"\b(?P<name>{'|'.join(re.escape(name) for name in sorted(buffer_names))})"
        r"\s*\[(?P<index>[^\]\r\n]{1,160})\]\s*"
        r"(?P<operator>\+=|-=|\*=|/=|%=|(?<![=!<>])=(?!=))\s*"
        r"(?P<value>[^;\r\n]{1,800});",
        flags=re.IGNORECASE,
    )
    for match in pattern.finditer(body):
        target = (
            match.group("name").lower()
            + "["
            + re.sub(r"\s+", "", match.group("index")).lower()
            + "]"
        )
        if require_reachable and re.search(
            r"\b(?:return|continue|break)\b[^;]*;",
            body[: match.start()],
            flags=re.IGNORECASE,
        ):
            continue
        global_position = source_offset + match.start()
        operator = match.group("operator")
        meaningful = bool(
            operator == "="
            and _indicator_output_value_is_meaningful(
                match.group("value"),
                target,
                analysis_code=(analysis_code if analysis_code is not None else body),
                assignment_position=(global_position if analysis_code is not None else match.start()),
                function_records=function_records,
                buffer_names=buffer_names,
            )
        )
        result.append({
            "name": match.group("name"),
            "target": target,
            "operator": operator,
            "value": match.group("value").strip(),
            "meaningful": meaningful,
            "start": global_position,
            "end": source_offset + match.end(),
        })
    normalized_buffers = {name.lower(): name for name in buffer_names}
    bulk_calls = list(
        re.finditer(
            r"\b(?P<operator>ArrayInitialize|ArrayFill|ArrayCopy)\s*\(",
            body,
            flags=re.IGNORECASE,
        )
    )
    for match in bulk_calls:
        opening = body.find("(", match.start(), match.end())
        closing = _balanced_close(body, opening, "(", ")")
        if closing is None:
            continue
        arguments = _split_mql_arguments(body[opening + 1 : closing])
        if not arguments:
            continue
        destination = arguments[0].strip().lower()
        if destination not in normalized_buffers:
            continue
        if require_reachable and not _code_position_is_reachable(body, match.start()):
            continue
        operator = match.group("operator")
        result.append({
            "name": normalized_buffers[destination],
            "target": destination + "[*]",
            "operator": operator,
            "value": ", ".join(arguments[1:]),
            # These calls mutate the complete bound array or a range that the
            # bounded analysis cannot prove excludes the signal index.
            # ArraySetAsSeries is intentionally absent: it changes indexing
            # metadata, not the array's values.
            "meaningful": False,
            "start": source_offset + match.start(),
            "end": source_offset + closing + 1,
        })
    result.sort(key=lambda row: (int(row["start"]), int(row["end"])))
    return result


def _signal_buffer_assignments(
    body: str,
    buffer_names: set[str],
    *,
    require_reachable: bool = False,
    function_records: list[dict] | None = None,
) -> set[str]:
    return {
        str(record["name"])
        for record in _signal_buffer_assignment_records(
            body,
            buffer_names,
            require_reachable=require_reachable,
            analysis_code=body,
            function_records=function_records,
        )
        if record.get("meaningful") is True
    }


def _split_mql_arguments(value: str) -> list[str] | None:
    """Split one bounded MQL call without treating nested commas as separators."""

    result: list[str] = []
    start = 0
    stack: list[str] = []
    closing_for = {"(": ")", "[": "]", "{": "}"}
    for index, character in enumerate(value):
        if character in closing_for:
            stack.append(closing_for[character])
        elif character in ")]}" :
            if not stack or stack.pop() != character:
                return None
        elif character == "," and not stack:
            result.append(value[start:index].strip())
            start = index + 1
        if len(stack) > 32:
            return None
    if stack:
        return None
    result.append(value[start:].strip())
    if not all(result) or len(result) > 16:
        return None
    return result


def _set_index_buffer_records(
    code: str,
    *,
    source_offset: int = 0,
) -> tuple[list[dict], bool]:
    """Parse every binding call; fail closed when its identity is not static."""

    result: list[dict] = []
    valid = True
    matches = list(re.finditer(r"\bSetIndexBuffer\s*\(", code, flags=re.IGNORECASE))
    if len(matches) > 256:
        return [], False
    for match in matches:
        opening = code.find("(", match.start(), match.end())
        closing = _balanced_close(code, opening, "(", ")")
        if closing is None:
            valid = False
            continue
        arguments = _split_mql_arguments(code[opening + 1 : closing])
        if arguments is None or len(arguments) not in {2, 3}:
            valid = False
            continue
        index_match = re.fullmatch(r"(?:0|[1-9]\d{0,2})", arguments[0])
        name_match = re.fullmatch(r"[A-Za-z_]\w*", arguments[1])
        if index_match is None or name_match is None:
            # A computed index, aliased buffer, or other expression cannot
            # establish a unique immutable output-buffer identity.
            valid = False
            continue
        result.append({
            "index": int(index_match.group(0)),
            "name": name_match.group(0),
            "normalizedName": name_match.group(0).lower(),
            "start": source_offset + match.start(),
            "end": source_offset + closing + 1,
        })
    return result, valid


def _code_position_is_reachable(code: str, position: int) -> bool:
    return re.search(
        r"\b(?:return|continue|break)\b[^;]*;",
        code[:position],
        flags=re.IGNORECASE,
    ) is None


def _indicator_lifecycle_buffer_bindings(
    live_code: str,
    function_records: list[dict],
) -> tuple[set[str], bool]:
    """Resolve one immutable binding identity from the OnInit call graph."""

    functions = {
        str(record.get("normalizedName") or ""): record
        for record in function_records
        if isinstance(record, dict) and record.get("normalizedName")
    }
    if len(functions) != len(function_records) or "oninit" not in functions:
        return set(), False
    reachable = {"oninit"}
    queue = ["oninit"]
    while queue:
        current = queue.pop()
        body = str(functions[current].get("body") or "")
        for candidate in functions:
            if candidate in reachable:
                continue
            calls = list(
                re.finditer(
                    rf"\b{re.escape(candidate)}\s*\(",
                    body,
                    flags=re.IGNORECASE,
                )
            )
            if any(_code_position_is_reachable(body, call.start()) for call in calls):
                reachable.add(candidate)
                queue.append(candidate)

    reachable_bindings: list[dict] = []
    for name in reachable:
        record = functions[name]
        body = str(record.get("body") or "")
        body_start = int(record.get("bodyStart") or 0)
        conditional_regions = _mql_if_region_records(body)
        if conditional_regions is None:
            return set(), False
        conditional_spans = [
            (
                body_start + int(region.get("bodyStart") or 0),
                body_start + int(region.get("bodyEnd") or 0),
            )
            for region in conditional_regions
        ]
        bindings, bindings_valid = _set_index_buffer_records(
            body,
            source_offset=body_start,
        )
        if not bindings_valid:
            return set(), False
        for binding in bindings:
            local_position = int(binding["start"]) - body_start
            if (
                _code_position_is_reachable(body, local_position)
                and not _assignment_inside_span(binding, conditional_spans)
            ):
                reachable_bindings.append(binding)
    all_bindings, all_bindings_valid = _set_index_buffer_records(live_code)
    indices = [int(record["index"]) for record in reachable_bindings]
    names = [str(record["normalizedName"]) for record in reachable_bindings]
    stable = bool(
        reachable_bindings
        and all_bindings_valid
        # A binding in an uncalled helper or another lifecycle callback is not
        # initialization evidence and could later rebind the visible index.
        and len(all_bindings) == len(reachable_bindings)
        # Reject any repeated/rebound index or buffer identity.  One source
        # index must have exactly one final, stable data-buffer owner.
        and len(set(indices)) == len(indices)
        and len(set(names)) == len(names)
        and sorted(
            (row["index"], row["normalizedName"], row["start"])
            for row in all_bindings
        )
        == sorted(
            (row["index"], row["normalizedName"], row["start"])
            for row in reachable_bindings
        )
    )
    return ({str(record["name"]) for record in reachable_bindings} if stable else set()), stable


def _assignment_inside_span(record: dict, spans: list[tuple[int, int]]) -> bool:
    position = int(record.get("start") or 0)
    return any(start <= position < end for start, end in spans)


def _buffer_targets_overlap(left: object, right: object) -> bool:
    """Return true when two indexed or whole-buffer mutation targets overlap."""

    left_value = str(left or "").lower()
    right_value = str(right or "").lower()
    left_name = left_value.split("[", 1)[0]
    right_name = right_value.split("[", 1)[0]
    return bool(
        left_name
        and left_name == right_name
        and (
            left_value == right_value
            or left_value.endswith("[*]")
            or right_value.endswith("[*]")
        )
    )


def _rule_marker_controls_final_output(
    calculation_code: str,
    if_regions: list[dict],
    marker: str,
    all_rule_markers: set[str],
    buffer_names: set[str],
    function_records: list[dict] | None = None,
) -> bool:
    """Require a meaningful marker-controlled write that survives each path."""

    controlled_branch_finals: list[dict[str, dict]] = []
    for region in if_regions:
        condition = str(region.get("condition") or "")
        if not _condition_requires_rule_marker(
            condition,
            marker,
            all_rule_markers,
        ):
            continue
        body = str(region.get("body") or "")
        branch_assignments = _signal_buffer_assignment_records(
            body,
            buffer_names,
            require_reachable=True,
            source_offset=int(region.get("bodyStart") or 0),
            analysis_code=calculation_code,
            function_records=function_records,
        )
        nested_regions = _mql_if_region_records(body)
        if nested_regions is None:
            return False
        nested_spans = [
            (
                int(region.get("bodyStart") or 0) + int(nested.get("bodyStart") or 0),
                int(region.get("bodyStart") or 0) + int(nested.get("bodyEnd") or 0),
            )
            for nested in nested_regions
        ]
        # A nested condition means the assignment is not guaranteed when this
        # rule marker is true.  Keep only writes at the marker branch level.
        top_level_assignments = [
            record
            for record in branch_assignments
            if not _assignment_inside_span(record, nested_spans)
        ]
        final_by_target: dict[str, dict] = {}
        for assignment in top_level_assignments:
            final_by_target[str(assignment["target"])] = assignment
        # A top-level write guarantees a value when the marker is true, but a
        # later nested branch can still erase it on one path.  Mark that target
        # invalid unless every later conditional write remains meaningful.
        for target, final_assignment in list(final_by_target.items()):
            if any(
                _buffer_targets_overlap(later.get("target"), target)
                and int(later.get("start") or 0)
                > int(final_assignment.get("end") or 0)
                and later.get("meaningful") is not True
                for later in branch_assignments
            ):
                invalid_final = dict(final_assignment)
                invalid_final["meaningful"] = False
                final_by_target[target] = invalid_final
        if final_by_target:
            controlled_branch_finals.append(final_by_target)
    if not controlled_branch_finals:
        return False

    common_targets = set(controlled_branch_finals[0])
    for branch in controlled_branch_finals[1:]:
        common_targets.intersection_update(branch)
    if not common_targets:
        return False

    all_assignments = _signal_buffer_assignment_records(
        calculation_code,
        buffer_names,
        analysis_code=calculation_code,
        function_records=function_records,
    )
    if_body_spans = [
        (int(region.get("bodyStart") or 0), int(region.get("bodyEnd") or 0))
        for region in if_regions
    ]
    top_level_assignments = [
        record
        for record in all_assignments
        if not _assignment_inside_span(record, if_body_spans)
    ]
    for target in common_targets:
        branch_finals = [branch[target] for branch in controlled_branch_finals]
        if any(record.get("meaningful") is not True for record in branch_finals):
            continue
        # Any subsequent unconditional write wins on the marker-true path, so
        # the signal is no longer the final marker-controlled buffer value.
        if any(
            _buffer_targets_overlap(later.get("target"), target)
            and int(later.get("start") or 0) > int(branch_final.get("end") or 0)
            for branch_final in branch_finals
            for later in top_level_assignments
        ):
            continue
        if any(
            _buffer_targets_overlap(later.get("target"), target)
            and later.get("meaningful") is not True
            and int(later.get("start") or 0) > int(branch_final.get("end") or 0)
            for branch_final in branch_finals
            for later in all_assignments
        ):
            continue
        return True
    return False


def _normalize_rule_predicate_contracts(
    requirements: dict,
    expected_rule_ids: set[str],
) -> dict[str, dict]:
    rows = requirements.get("requiredRulePredicates")
    if not isinstance(rows, list) or len(rows) > 1000:
        raise ValueError("EA Factory Indicator rule predicates are malformed.")
    result: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "ruleId",
            "semanticBindingId",
            "predicate",
        }:
            raise ValueError("EA Factory Indicator rule predicate is malformed.")
        rule_id = str(row.get("ruleId") or "")
        binding_id = str(row.get("semanticBindingId") or "")
        predicate = row.get("predicate")
        if (
            not rule_id
            or rule_id in result
            or len(rule_id) > 160
            or not binding_id.startswith(f"rule_semantics:{rule_id}:")
            or len(binding_id) > 300
            or not isinstance(predicate, dict)
        ):
            raise ValueError("EA Factory Indicator rule predicate identity is invalid.")
        result[rule_id] = predicate
    if set(result) != expected_rule_ids:
        raise ValueError("EA Factory Indicator rule predicate coverage is incomplete.")
    return result


def analyze_indicator_source(
    requirements: object,
    source_text: str,
    *,
    target_platform: str,
) -> dict:
    """Statically bind each rule predicate to an actual Indicator buffer branch."""

    if (
        not isinstance(requirements, dict)
        or requirements.get("schemaVersion") != REQUIREMENTS_SCHEMA_VERSION
    ):
        raise ValueError("EA Factory Indicator coverage requirements are malformed.")
    unsigned = dict(requirements)
    claimed_digest = str(unsigned.pop("requirementsDigest", "")).lower()
    if (
        _SHA256_PATTERN.fullmatch(claimed_digest) is None
        or _payload_digest(REQUIREMENTS_SCHEMA_VERSION, unsigned) != claimed_digest
    ):
        raise ValueError("EA Factory Indicator requirements digest is invalid.")
    platform = str(target_platform or "").strip().lower()
    if platform not in _SUPPORTED_PLATFORMS:
        raise ValueError("EA Factory Indicator target platform is invalid.")
    marker_rows = requirements.get("requiredRuleMarkers")
    if not isinstance(marker_rows, list) or len(marker_rows) > 1000:
        raise ValueError("EA Factory Indicator rule markers are malformed.")
    normalized_markers: list[dict] = []
    seen_ids: set[str] = set()
    seen_markers: set[str] = set()
    for row in marker_rows:
        identifier = str(row.get("id") or "") if isinstance(row, dict) else ""
        marker = str(row.get("marker") or "") if isinstance(row, dict) else ""
        if (
            not identifier
            or len(identifier) > 160
            or _RULE_MARKER_PATTERN.fullmatch(marker) is None
            or identifier in seen_ids
            or marker in seen_markers
        ):
            raise ValueError("EA Factory Indicator rule marker identity is invalid.")
        seen_ids.add(identifier)
        seen_markers.add(marker)
        normalized_markers.append({"id": identifier, "marker": marker})
    predicate_contracts = _normalize_rule_predicate_contracts(
        requirements,
        seen_ids,
    )
    indicator_profile = requirements.get("indicatorSemanticProfile")
    indicator_marker_rows = requirements.get("requiredIndicatorSemanticMarkers")
    if (
        not isinstance(indicator_profile, dict)
        or not isinstance(indicator_marker_rows, list)
    ):
        raise ValueError("EA Factory Indicator operand contract is malformed.")
    indicator_bindings = indicator_profile.get("semanticBindings")
    if not isinstance(indicator_bindings, list):
        raise ValueError("EA Factory Indicator operand contract is malformed.")

    lexical = _mql_lexical_views(str(source_text or ""))
    failed_checks = {
        "lexicallyUnambiguous": False,
        "indicatorDeclaration": False,
        "onCalculate": False,
        "indicatorBufferBinding": False,
        "indicatorOutputAssignment": False,
        "indicatorOperandsBound": False,
        "ruleMarkersControlOutput": False,
        "tradingFunctionsAbsent": False,
    }
    if lexical is None:
        return {
            "checks": failed_checks,
            "ruleMarkerEvidence": [
                {
                    **row,
                    "presentInOnCalculate": False,
                    "semanticPredicate": False,
                    "controlsIndicatorOutput": False,
                }
                for row in normalized_markers
            ],
            "missingRuleMarkers": [row["id"] for row in normalized_markers],
            "forbiddenTradingFunctions": ["source_lexically_ambiguous"],
            "complete": False,
        }
    code, _descriptions = lexical
    live_code = strip_statically_dead_mql_regions(code)
    if not isinstance(live_code, str):
        live_code = ""
    # All output/control evidence must come from the statically live view.
    # Otherwise an ``if(false)`` decoy inside OnCalculate can satisfy the
    # marker and buffer checks even though MetaTrader can never execute it.
    function_records = _mql_function_records(live_code)
    if function_records is None:
        function_records = []
    on_calculate_records = [
        record
        for record in function_records
        if str(record.get("normalizedName") or "") == "oncalculate"
    ]
    calculation_code = (
        str(on_calculate_records[0].get("body") or "")
        if len(on_calculate_records) == 1
        else ""
    )
    calculation_code = strip_statically_dead_mql_regions(calculation_code)
    if not isinstance(calculation_code, str):
        calculation_code = ""
    if_regions = _mql_if_region_records(calculation_code)
    if if_regions is None:
        if_regions = []
    buffer_names, buffer_binding_stable = _indicator_lifecycle_buffer_bindings(
        live_code,
        function_records,
    )
    assigned_buffers = _signal_buffer_assignments(
        calculation_code,
        buffer_names,
        function_records=function_records,
    )
    operand_aliases = semantic_indicator_operand_aliases_for_source(
        str(source_text or ""),
        indicator_profile,
        indicator_marker_rows,
        target_platform=platform,
    )
    expected_operand_keys = {
        f"indicator:{str(row.get('identity') or '').strip().lower()}"
        for row in indicator_bindings
        if isinstance(row, dict) and row.get("kind") == "indicator"
    }
    indicator_operands_bound = (
        not expected_operand_keys
        or (
            set(operand_aliases) == expected_operand_keys
            and all(operand_aliases.get(key) for key in expected_operand_keys)
        )
    )
    forbidden_patterns = {
        "OnTick": r"\bOnTick\s*\(",
        "OrderSend": r"\bOrderSend\s*\(",
        "OrderSendAsync": r"\bOrderSendAsync\s*\(",
        "OrderCheck": r"\bOrderCheck\s*\(",
        "OrderClose": r"\bOrderClose\s*\(",
        "OrderModify": r"\bOrderModify\s*\(",
        "OrderDelete": r"\bOrderDelete\s*\(",
        "CTrade": r"\bCTrade\b",
        "trade operation": (
            r"\.[ \t]*(?:Buy|Sell|BuyLimit|SellLimit|BuyStop|SellStop|"
            r"PositionOpen|PositionClose|PositionModify|OrderOpen|OrderDelete|OrderModify)\s*\("
        ),
        "MqlTradeRequest": r"\bMqlTradeRequest\b",
        "TRADE_ACTION": r"\bTRADE_ACTION_[A-Z_]+\b",
        "PositionOpen": r"\bPositionOpen\s*\(",
        "PositionClose": r"\bPositionClose\s*\(",
        "WebRequest": r"\bWebRequest\s*\(",
        "FileOpen": r"\bFileOpen\s*\(",
        "Socket": r"\bSocket(?:Create|Connect|Send|Read|Close)\s*\(",
        "import directive": r"(?mi)^\s*#\s*import\b",
        "resource directive": r"(?mi)^\s*#\s*resource\b",
        "include directive": r"(?mi)^\s*#\s*include\b",
    }
    forbidden = [
        label
        for label, pattern in forbidden_patterns.items()
        if re.search(pattern, code, flags=re.IGNORECASE)
    ]
    expected_coverage_markers = {
        row["marker"] for row in normalized_markers
    } | {
        str(row.get("marker") or "")
        for row in indicator_marker_rows
        if isinstance(row, dict) and str(row.get("marker") or "")
    }
    if any(
        re.search(
            rf"(?mi)^\s*#\s*(?:define|undef)\s+{re.escape(marker)}\b",
            code,
        )
        for marker in expected_coverage_markers
    ):
        forbidden.append("coverage marker macro override")

    all_rule_markers = {row["marker"] for row in normalized_markers}
    marker_evidence: list[dict] = []
    for row in normalized_markers:
        marker = row["marker"]
        marker_word = rf"\b{re.escape(marker)}\b"
        definitions = re.findall(
            rf"\b(?:const\s+)?bool\s+{re.escape(marker)}\s*=\s*([^;]{{1,800}});",
            calculation_code,
            flags=re.IGNORECASE,
        )
        assignments = re.findall(
            rf"\b{re.escape(marker)}\b\s*(?:"
            r"(?<![=!<>])=(?!=)|\^=|\|=|&=)",
            calculation_code,
            flags=re.IGNORECASE,
        )
        semantic_predicate = bool(
            len(definitions) == 1
            and len(assignments) == 1
            and indicator_operands_bound
            and rule_predicate_expression_supported(
                definitions[0],
                predicate_contracts.get(row["id"]),
                operand_aliases=operand_aliases,
            )
        )
        controls_output = bool(
            semantic_predicate
            and _rule_marker_controls_final_output(
                calculation_code,
                if_regions,
                marker,
                all_rule_markers,
                buffer_names,
                function_records=function_records,
            )
        )
        marker_evidence.append({
            **row,
            "presentInOnCalculate": bool(re.search(marker_word, calculation_code)),
            "semanticPredicate": semantic_predicate,
            "controlsIndicatorOutput": controls_output,
        })
    missing = [
        row["id"]
        for row in marker_evidence
        if not (
            row["presentInOnCalculate"]
            and row["semanticPredicate"]
            and row["controlsIndicatorOutput"]
        )
    ]
    checks = {
        "lexicallyUnambiguous": True,
        "indicatorDeclaration": bool(
            re.search(
                r"(?mi)^\s*#property\s+indicator_(?:chart_window|separate_window)\b",
                code,
            )
            and re.search(r"(?mi)^\s*#property\s+indicator_buffers\s+[1-9]\d*\b", code)
        ),
        "onCalculate": len(on_calculate_records) == 1,
        "indicatorBufferBinding": bool(buffer_names and buffer_binding_stable),
        "indicatorOutputAssignment": bool(
            assigned_buffers
            and buffer_binding_stable
            and re.search(r"\bDRAW_NONE\b", live_code, flags=re.IGNORECASE) is None
        ),
        "indicatorOperandsBound": indicator_operands_bound,
        "ruleMarkersControlOutput": not missing,
        "tradingFunctionsAbsent": not forbidden,
    }
    return {
        "checks": checks,
        "ruleMarkerEvidence": marker_evidence,
        "missingRuleMarkers": missing,
        "forbiddenTradingFunctions": forbidden,
        "complete": all(checks.values()) and not missing and not forbidden,
    }


def build_indicator_coverage_manifest(
    requirements: object,
    source_text: str,
    *,
    strategy_spec_digest: str,
    source_digest: str,
    target_platform: str,
) -> dict:
    platform = str(target_platform or "").strip().lower()
    spec_digest = str(strategy_spec_digest or "").strip().lower()
    normalized_source_digest = str(source_digest or "").strip().lower()
    if (
        platform not in _SUPPORTED_PLATFORMS
        or _SHA256_PATTERN.fullmatch(spec_digest) is None
        or _SHA256_PATTERN.fullmatch(normalized_source_digest) is None
    ):
        raise ValueError("EA Factory Indicator coverage binding is invalid.")
    analysis = analyze_indicator_source(
        requirements,
        source_text,
        target_platform=platform,
    )
    manifest = {
        "schemaVersion": MANIFEST_SCHEMA_VERSION,
        "requirementsDigest": str(
            requirements.get("requirementsDigest")
            if isinstance(requirements, dict)
            else ""
        ).lower(),
        "eaBlueprintDigest": str(
            requirements.get("eaBlueprintDigest")
            if isinstance(requirements, dict)
            else ""
        ).lower(),
        "strategySpecDigest": spec_digest,
        "sourceDigest": normalized_source_digest,
        "targetPlatform": platform,
        **analysis,
    }
    manifest["manifestDigest"] = _payload_digest(MANIFEST_SCHEMA_VERSION, manifest)
    return manifest
