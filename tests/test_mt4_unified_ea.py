from __future__ import annotations

import hashlib
import math
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UNIFIED_EA_PATH = (
    PROJECT_ROOT
    / "artifacts"
    / "mt4-ai-council-ea-v2.18-enum-fail-closed-readiness"
    / "MetafxHQTradeGateway.mq4"
)
MT5_GATEWAY_PATH = (
    PROJECT_ROOT
    / "integrations"
    / "mt5-trade-gateway"
    / "MetafxHQTradeGateway.mq5"
)
STANDALONE_INDICATOR_PATH = (
    PROJECT_ROOT
    / "integrations"
    / "mt4-readonly"
    / "MetafxHQReadOnlySnapshot.mq4"
)


def strip_mql_comments(source: str) -> str:
    without_blocks = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"//[^\r\n]*", "", without_blocks)


def named_block(source: str, signature: str) -> str:
    match = re.search(signature, source)
    if match is None:
        return ""
    opening = source.find("{", match.end())
    if opening < 0:
        return ""
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1 : index]
    return ""


COMPACT_POLICY_LEASE_RE = re.compile(
    r"^policy-p-([0-9a-f]{16})-c-([0-9a-f]{16})\.lease$"
)
LEGACY_POLICY_LEASE_RE = re.compile(
    r"^policy-([0-9a-f]{64})-channel-([0-9a-f]{64})\.lease$"
)


def compact_policy_lease_name(policy_digest: str, channel_digest: str) -> str:
    return f"policy-p-{policy_digest[:16]}-c-{channel_digest[:16]}.lease"


def snapshot_channel_digest(channel: str) -> str:
    return hashlib.sha256(channel.encode("ascii")).hexdigest()


def risk_volume_model(
    *,
    capital: float,
    balance: float,
    risk_percent: float,
    hard_cap_percent: float,
    stop_distance: float,
    point: float,
    tick_size_points: float,
    tick_value: float,
    commission_per_lot: float,
    slippage_points: int,
    minimum: float,
    maximum: float,
    step: float,
    max_managed_lots: float,
    current_managed_lots: float,
) -> tuple[float, float] | None:
    tick_size_price = tick_size_points * point
    loss_per_lot = (
        (stop_distance + slippage_points * point)
        / tick_size_price
        * tick_value
        + commission_per_lot
    )
    budget = min(
        capital * risk_percent / 100.0,
        balance * hard_cap_percent / 100.0,
    )
    ceiling = min(maximum, max_managed_lots - current_managed_lots)
    raw_lots = budget / loss_per_lot
    capped = min(raw_lots, ceiling)
    if capped < minimum:
        return None
    step_count = math.floor((capped - minimum) / step + 1e-10)
    lots = minimum + max(0, step_count) * step
    while lots >= minimum and loss_per_lot * lots > budget:
        lots -= step
    if lots < minimum:
        return None
    return lots, loss_per_lot * lots


def broker_symbol_match_model(csv: str, candidate: str) -> bool:
    """Mirror the bounded MT4 canonical-symbol/affix policy for edge cases."""

    normalized_candidate = candidate.strip().upper()
    allowed_affix = re.compile(r"^[A-Z0-9._#-]*$")
    for raw_allowed in csv.split(","):
        allowed = raw_allowed.strip().upper()
        if allowed == normalized_candidate:
            return True
        if len(allowed) < 6 or len(normalized_candidate) <= len(allowed):
            continue
        if len(normalized_candidate) > len(allowed) + 16:
            continue
        matches = [
            start
            for start in range(len(normalized_candidate) - len(allowed) + 1)
            if normalized_candidate[start : start + len(allowed)] == allowed
        ]
        if len(matches) != 1:
            continue
        for prefix_length in range(9):
            suffix_length = len(normalized_candidate) - prefix_length - len(allowed)
            if suffix_length < 0 or suffix_length > 8:
                continue
            if normalized_candidate[
                prefix_length : prefix_length + len(allowed)
            ] != allowed:
                continue
            prefix = normalized_candidate[:prefix_length]
            suffix = normalized_candidate[prefix_length + len(allowed) :]
            if prefix and not (len(prefix) == 1 or prefix[-1] in "._#-"):
                continue
            if allowed_affix.fullmatch(prefix) and allowed_affix.fullmatch(suffix):
                return True
    return False


def _legacy_loss_latch_scan_pass_model(
    entries: list[tuple[str, bool, bool, bool]],
    *,
    cap: int = 256,
    enumeration_error: bool = False,
) -> tuple[bool, bool, bool, tuple[str, ...], str]:
    if enumeration_error:
        return (
            False,
            False,
            False,
            (),
            "LEGACY_LOSS_LATCH_ENUMERATION_FAILED",
        )
    if len(entries) > cap:
        return (
            False,
            False,
            False,
            (),
            "LEGACY_LOSS_LATCH_ENUMERATION_LIMIT_EXCEEDED",
        )
    daily_found = False
    weekly_found = False
    channels: list[str] = []
    for name, is_directory, has_daily, has_weekly in entries:
        if name in {"locks", "account-policies"}:
            continue
        if not re.fullmatch(r"mtc-[A-Za-z0-9_-]{1,116}", name):
            continue
        if not is_directory:
            return (
                False,
                False,
                False,
                (),
                "LEGACY_LOSS_LATCH_ENUMERATION_AMBIGUOUS",
            )
        channels.append(name)
        daily_found = daily_found or has_daily
        weekly_found = weekly_found or has_weekly
    return True, daily_found, weekly_found, tuple(sorted(channels)), ""


def legacy_loss_latch_scan_model(
    entries: list[tuple[str, bool, bool, bool]],
    *,
    cap: int = 256,
    enumeration_error: bool = False,
) -> tuple[bool, bool, bool, str]:
    ok, daily, weekly, _channels, reason = _legacy_loss_latch_scan_pass_model(
        entries,
        cap=cap,
        enumeration_error=enumeration_error,
    )
    return ok, daily, weekly, reason


def legacy_loss_latch_migration_model(
    first_entries: list[tuple[str, bool, bool, bool]],
    second_entries: list[tuple[str, bool, bool, bool]],
    *,
    first_enumeration_error: bool = False,
    second_enumeration_error: bool = False,
    captured_periods: tuple[int, int] = (1_700_000_000, 1_699_747_200),
    periods_before_activation: tuple[int, int] | None = None,
    periods_after_activation: tuple[int, int] | None = None,
    persistence_ok: bool = True,
) -> tuple[bool, bool, bool, str]:
    first = _legacy_loss_latch_scan_pass_model(
        first_entries,
        enumeration_error=first_enumeration_error,
    )
    if not first[0]:
        return False, False, False, first[4]
    second = _legacy_loss_latch_scan_pass_model(
        second_entries,
        enumeration_error=second_enumeration_error,
    )
    if not second[0]:
        return False, False, False, second[4]
    if first[3] != second[3]:
        return False, False, False, "LEGACY_LOSS_LATCH_CHANNEL_SET_CHANGED"
    before = periods_before_activation or captured_periods
    after = periods_after_activation or captured_periods
    if before != captured_periods or after != captured_periods:
        return False, False, False, "LEGACY_LOSS_LATCH_PERIOD_CHANGED"
    daily_found = first[1] or second[1]
    weekly_found = first[2] or second[2]
    if (daily_found or weekly_found) and not persistence_ok:
        return False, daily_found, weekly_found, "LOSS_LATCH_PERSISTENCE_FAILED"
    return True, daily_found, weekly_found, ""


def legacy_loss_latch_marker_probe_model(
    *,
    is_regular_file: bool,
    error_code: int,
) -> tuple[bool, bool]:
    if is_regular_file:
        return True, True
    if error_code in {0, 5020, 5023}:
        return True, False
    return False, False


def compact_policy_lease_payload(
    account_digest: str,
    policy_digest: str,
    channel: str,
    observed_at: int = 1_700_000_000,
) -> str:
    digest = snapshot_channel_digest(channel)
    return (
        "MetafxHQPortfolioPolicyV2|"
        f"{account_digest}|{policy_digest}|{digest}|{channel}|{observed_at}"
    )


def parse_policy_lease_model(
    file_name: str,
    raw: str,
    expected_account_digest: str,
) -> tuple[str, str]:
    compact = COMPACT_POLICY_LEASE_RE.fullmatch(file_name)
    legacy = LEGACY_POLICY_LEASE_RE.fullmatch(file_name)
    if (compact is None) == (legacy is None):
        raise ValueError("PORTFOLIO_POLICY_STATE_INVALID")
    parts = raw.strip().split("|")
    if compact is not None:
        if (
            len(parts) != 6
            or parts[0] != "MetafxHQPortfolioPolicyV2"
            or any(re.fullmatch(r"[0-9a-f]{64}", value) is None for value in parts[1:4])
            or parts[1] != expected_account_digest
            or parts[2][:16] != compact.group(1)
            or parts[3][:16] != compact.group(2)
            or re.fullmatch(r"mtc-[A-Za-z0-9_-]{1,116}", parts[4]) is None
            or snapshot_channel_digest(parts[4]) != parts[3]
            or not parts[5].isdigit()
            or int(parts[5]) < 946_684_800
        ):
            raise ValueError("PORTFOLIO_POLICY_STATE_INVALID")
        return parts[2], parts[3]
    assert legacy is not None
    if (
        len(parts) != 4
        or parts[0] != "MetafxHQPortfolioPolicy"
        or re.fullmatch(r"[0-9a-f]{64}", parts[1]) is None
        or not parts[2].startswith("mtc-")
        or not parts[3].isdigit()
        or int(parts[3]) < 946_684_800
        or parts[1] != legacy.group(1)
    ):
        raise ValueError("PORTFOLIO_POLICY_STATE_INVALID")
    legacy_channel_digest = hashlib.sha256(parts[2].encode("ascii")).hexdigest()
    if legacy_channel_digest != legacy.group(2):
        raise ValueError("PORTFOLIO_POLICY_STATE_INVALID")
    return parts[1], legacy_channel_digest


def inspect_policy_leases_model(
    records: list[dict[str, object]],
    expected_account_digest: str,
    expected_policy_digest: str,
    *,
    first_scan_error: bool = False,
    next_scan_error_at: int | None = None,
) -> tuple[str, int]:
    active_count = 0
    if first_scan_error:
        return "PORTFOLIO_POLICY_STATE_INVALID", active_count
    for index, record in enumerate(records):
        if not record.get("active", True):
            # The exclusive probe succeeds, so stale evidence is deleted
            # before any payload parsing is attempted.
            continue
        if not record.get("readable", True):
            return "PORTFOLIO_POLICY_STATE_INVALID", active_count
        try:
            policy_digest, _ = parse_policy_lease_model(
                str(record["name"]),
                str(record["payload"]),
                expected_account_digest,
            )
        except (KeyError, ValueError):
            return "PORTFOLIO_POLICY_STATE_INVALID", active_count
        active_count += 1
        if policy_digest != expected_policy_digest:
            return "PORTFOLIO_POLICY_MISMATCH", active_count
        if next_scan_error_at == index:
            return "PORTFOLIO_POLICY_STATE_INVALID", active_count
    return "READY", active_count


class MT4UnifiedEATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = UNIFIED_EA_PATH.read_text(encoding="utf-8")
        cls.code = strip_mql_comments(cls.source)

    def test_unified_ea_and_legacy_readonly_indicator_are_both_shipped(self) -> None:
        self.assertTrue(UNIFIED_EA_PATH.is_file())
        self.assertTrue(STANDALONE_INDICATOR_PATH.is_file())
        standalone = STANDALONE_INDICATOR_PATH.read_text(encoding="utf-8")
        self.assertIn("metafx-hq-mt4-snapshot-v1", standalone)
        self.assertIn("snapshot.json", standalone)
        self.assertRegex(standalone, r"\bvoid\s+OnTimer\s*\(")

    def test_snapshot_bar_inputs_support_20_through_1000_closed_bars(self) -> None:
        standalone = strip_mql_comments(
            STANDALONE_INDICATOR_PATH.read_text(encoding="utf-8")
        )
        self.assertRegex(
            standalone,
            r"MathMin\s*\(\s*SnapshotBars\s*,\s*1000\s*\)",
        )
        self.assertRegex(
            standalone,
            r"SnapshotBars\s*<\s*20\s*\|\|\s*SnapshotBars\s*>\s*1000",
        )
        self.assertRegex(
            self.code,
            r"MathMin\s*\(\s*SnapshotBars\s*,\s*1000\s*\)",
        )
        self.assertRegex(
            self.code,
            r"SnapshotBars\s*<\s*20\s*\|\|\s*SnapshotBars\s*>\s*1000",
        )

    def test_gateway_ea_publishes_the_snapshot_contract_atomically_in_file_common(self) -> None:
        self.assertIn("metafx-hq-mt4-snapshot-v1", self.code)
        self.assertIn("snapshot.tmp", self.code)
        self.assertIn("snapshot.json", self.code)
        self.assertIn("FILE_COMMON", self.code)
        self.assertRegex(
            self.code,
            r"(?i)string\s+temporary_[a-z_]*\s*=\s*[^;]*snapshot\.tmp",
        )
        snapshot_path_body = named_block(self.code, r"\bstring\s+SnapshotPath\s*\([^)]*\)")
        self.assertIn("snapshot.json", snapshot_path_body)
        self.assertRegex(
            self.code,
            r"(?s)FileMove\s*\(\s*temporary_[a-z_]*\s*,\s*FILE_COMMON\s*,\s*(?:final_[a-z_]*|SnapshotPath\s*\(\s*\))\s*,\s*FILE_COMMON\s*\|\s*FILE_REWRITE\s*\)",
        )
        self.assertRegex(
            self.code,
            r"(?s)FileOpen\s*\(\s*temporary_[a-z_]*\s*,[^;]*?FILE_COMMON",
        )

    def test_one_timer_handles_separate_snapshot_and_command_poll_intervals(self) -> None:
        self.assertRegex(
            self.code,
            r"\binput\s+int\s+SnapshotIntervalSeconds\s*=\s*5\s*;",
        )
        self.assertRegex(
            self.code,
            r"\binput\s+int\s+PollIntervalSeconds\s*=\s*1\s*;",
        )
        self.assertGreaterEqual(self.code.count("SnapshotIntervalSeconds"), 2)
        self.assertGreaterEqual(self.code.count("PollIntervalSeconds"), 2)
        self.assertEqual(len(re.findall(r"\bvoid\s+OnTimer\s*\(", self.code)), 1)
        timer_body = named_block(self.code, r"\bvoid\s+OnTimer\s*\([^)]*\)")
        self.assertTrue(timer_body, "OnTimer body must be present")
        self.assertIn("ProcessCommandFile", timer_body)
        self.assertRegex(timer_body, r"(?i)snapshot")

    def test_execution_authority_and_position_size_remain_local_ea_inputs(self) -> None:
        self.assertRegex(
            self.code,
            r"\binput\s+ENUM_GATEWAY_MODE\s+GatewayMode\s*=\s*GATEWAY_SHADOW\s*;",
        )
        self.assertRegex(
            self.code,
            r"\binput\s+bool\s+LiveArmed\s*=\s*false\s*;",
        )
        self.assertRegex(
            self.code,
            r"\binput\s+ENUM_MONEY_MANAGEMENT_MODE\s+MoneyManagementMode\s*=\s*MONEY_MANAGEMENT_FIXED_LOT\s*;",
        )
        self.assertRegex(
            self.code,
            r"\binput\s+double\s+FixedLot\s*=\s*[0-9.]+\s*;",
        )
        self.assertRegex(
            self.code,
            r"\binput\s+double\s+RiskPercent\s*=\s*[0-9.]+\s*;",
        )
        command_fields = named_block(self.code, r"\bstruct\s+CommandPayload\b")
        self.assertTrue(command_fields, "CommandPayload must be present")
        self.assertIsNone(
            re.search(
                r"(?i)\b(?:lot|volume|risk_percent|risk_pct|risk_amount|money_management)\b",
                command_fields,
            ),
            "AI command payload must not own lot or risk sizing",
        )
        self.assertRegex(
            self.code,
            r"OrderSend\s*\([^;]*?\bexpected_lots\b[^;]*?\)",
        )
        self.assertEqual(len(re.findall(r"\bOrderSend\s*\(", self.code)), 1)

    def test_trade_path_keeps_all_required_fail_closed_guards_and_ack(self) -> None:
        guard_evidence = {
            "command TTL": ("MaxCommandTtlSeconds", "expires_at"),
            "heartbeat": ("RequireHeartbeat", "ValidateHeartbeat", "HEARTBEAT_SCHEMA"),
            "spread": ("MaxSpreadPoints", "MODE_SPREAD"),
            "SL and TP": ("ValidateStops", "stop_loss", "take_profit"),
            "one order per bar": ("LastOrderBarPath", "ReadLastOrderBar", "WriteLastOrderBar"),
            "idempotency": ("IdempotencyLedgerPath", "idempotency_key"),
            "kill switch": ("KillMarkerPath", "kill.switch"),
            "ACK": ("ACK_SCHEMA", "AckPath"),
        }
        for guard, tokens in guard_evidence.items():
            with self.subTest(guard=guard):
                for token in tokens:
                    self.assertIn(token, self.code)

    def test_v2_command_and_v3_ack_bind_snapshot_latest_closed_bar_and_price(self) -> None:
        self.assertIn('metafx-hq-mt4-command-v2', self.code)
        self.assertIn('metafx-hq-mt4-ack-v3', self.code)
        command_fields = named_block(self.code, r"\bstruct\s+CommandPayload\b")
        for token in (
            "snapshot_id",
            "snapshot_observed_at",
            "bar_time",
            "reference_price",
        ):
            self.assertIn(token, command_fields)
        binding = named_block(self.code, r"\bbool\s+ValidateClosedBarBinding\s*\([^)]*\)")
        self.assertIn("IsSha256Hex", binding)
        self.assertIn("MaxSnapshotAgeSeconds", binding)
        self.assertRegex(binding, r"iTime\s*\(\s*Symbol\s*\(\s*\)\s*,\s*Period\s*\(\s*\)\s*,\s*1\s*\)")
        self.assertIn("MaxSignalDriftPoints", binding)
        ack = named_block(self.code, r"\bstring\s+BuildAckJson\s*\([^)]*\)")
        for wire_field in (
            "snapshotId",
            "snapshotObservedAt",
            "barTime",
            "referencePrice",
            "eaClosedBarTime",
        ):
            self.assertIn(wire_field, ack)

    def test_local_risk_envelope_and_margin_preflight_are_not_ai_fields(self) -> None:
        for declaration in (
            r"input\s+int\s+MaxManagedOpenPositions\s*=\s*1\s*;",
            r"input\s+double\s+MaxManagedTotalLots\s*=\s*0\.10\s*;",
            r"input\s+int\s+MaxTradesPerBrokerDay\s*=\s*6\s*;",
            r"input\s+double\s+MaxLossPerTradePercent\s*=\s*1\.0\s*;",
            r"input\s+double\s+MaxDailyLossPercent\s*=\s*3\.0\s*;",
            r"input\s+double\s+MinRewardRiskRatio\s*=\s*1\.0\s*;",
            r"input\s+double\s+MinProjectedMarginLevelPercent\s*=\s*300\.0\s*;",
        ):
            self.assertRegex(self.code, declaration)
        command_fields = named_block(self.code, r"\bstruct\s+CommandPayload\b")
        for forbidden in (
            "max_managed",
            "max_loss",
            "max_daily",
            "reward_risk",
            "margin_level",
        ):
            self.assertNotIn(forbidden, command_fields.lower())
        runtime = named_block(self.code, r"\bbool\s+ValidateRuntime\s*\([^)]*\)")
        for guard in (
            "ValidateRiskEnvelope",
            "ValidateMarginPreflight",
            "ValidateQuoteFreshness",
            "ValidateClosedBarBinding",
        ):
            self.assertIn(guard, runtime)
        margin = named_block(
            self.code,
            r"\bbool\s+ValidateMarginPreflight\s*\([^)]*\)",
        )
        self.assertIn("AccountFreeMarginCheck", margin)
        self.assertIn("current_free_margin = AccountFreeMargin()", margin)
        self.assertIn("current_free_margin - free_after", margin)
        self.assertIn("AccountMargin()", margin)
        self.assertIn("current_margin + incremental_margin", margin)
        self.assertNotIn("MODE_MARGINREQUIRED", margin)

    def test_shadow_runs_common_guards_and_never_calls_ordersend(self) -> None:
        runtime = named_block(self.code, r"\bbool\s+ValidateRuntime\s*\([^)]*\)")
        shadow_return = runtime.find("GatewayMode == GATEWAY_SHADOW")
        self.assertGreater(shadow_return, 0)
        for guard in (
            "ValidateClosedBarBinding",
            "ValidateRiskEnvelope",
            "ValidateMarginPreflight",
            "ReadLastOrderBar",
        ):
            self.assertGreaterEqual(runtime.find(guard), 0)
            self.assertLess(runtime.find(guard), shadow_return)
        process = named_block(self.code, r"\bvoid\s+ProcessCommandFile\s*\([^)]*\)")
        self.assertRegex(process, r"GatewayMode\s*==\s*GATEWAY_SHADOW")
        self.assertNotIn("OrderSend", process)

    def test_final_execution_boundary_rechecks_guards_before_ordersend(self) -> None:
        execute = named_block(self.code, r"\bvoid\s+ExecuteCommand\s*\([^)]*\)")
        order_send = execute.find("OrderSend")
        self.assertGreater(order_send, 0)
        for token in (
            "KillMarkerPath",
            "ValidateHeartbeat",
            "ValidateQuoteFreshness",
            "ValidateClosedBarBinding",
            "ValidateRiskEnvelope",
            "ValidateMarginPreflight",
            "WriteLastOrderBar(command.bar_time)",
            "ReverifyCommandEnvelope",
        ):
            self.assertGreaterEqual(execute.find(token), 0)
            self.assertLess(execute.find(token), order_send)
        self.assertIn("BrokerSendFailureReason", execute)
        failure_reason = named_block(
            self.code,
            r"\bstring\s+BrokerSendFailureReason\s*\([^)]*\)",
        )
        self.assertIn("ORDER_SEND_FAILED_NO_AUTOMATIC_RETRY", failure_reason)

    def test_channel_lock_init_io_and_ack_repair_are_fail_closed(self) -> None:
        on_init = named_block(self.code, r"\bint\s+OnInit\s*\([^)]*\)")
        on_deinit = named_block(self.code, r"\bvoid\s+OnDeinit\s*\([^)]*\)")
        process = named_block(self.code, r"\bvoid\s+ProcessCommandFile\s*\([^)]*\)")
        self.assertIn("AcquireChannelLock", on_init)
        self.assertIn("EventSetTimer", on_init)
        self.assertIn("INIT_FAILED", on_init)
        self.assertIn("ReleaseChannelLock", on_deinit)
        self.assertIn("RepairAckFromLedger", process)
        self.assertNotIn("g_last_command_raw", self.code)

    def test_restart_reconciliation_never_guesses_or_resends_an_order(self) -> None:
        reconcile = named_block(self.code, r"\bvoid\s+ReconcileExecutingCommand\s*\([^)]*\)")
        finder = named_block(self.code, r"\bint\s+FindManagedCommandTicket\s*\([^)]*\)")
        unknown = named_block(self.code, r"\bvoid\s+MarkRecoveryUnknown\s*\([^)]*\)")
        process = named_block(self.code, r"\bvoid\s+ProcessCommandFile\s*\([^)]*\)")
        self.assertIn("OrderMagicNumber", finder)
        self.assertIn("IsManagedMagic(OrderMagicNumber())", finder)
        self.assertNotIn("OrderMagicNumber() == MagicNumber", finder)
        self.assertIn("OrderComment", finder)
        self.assertIn("CurrentChannelOwnsCommandId(command.command_id)", finder)
        self.assertGreaterEqual(finder.count("match_count = -1"), 2)
        self.assertIn("RECOVERY_TELEMETRY_UNAVAILABLE", reconcile)
        self.assertIn("RECOVERED_ORDER_FOUND", reconcile)
        self.assertIn("EXECUTION_UNKNOWN", reconcile)
        self.assertIn("RESTART_RECONCILIATION_REQUIRED", reconcile)
        self.assertGreaterEqual(reconcile.count("MarkRecoveryUnknown("), 3)
        self.assertIn('g_ack_verification_status = "SELECT_FAILED"', unknown)
        self.assertIn('g_ack_execution_state = "UNKNOWN"', unknown)
        self.assertIn("ResetAckExecutionEvidence", unknown)
        self.assertIn('processed_status == "EXECUTING"', process)
        self.assertNotIn("OrderSend", reconcile)

    def test_portfolio_guards_cover_managed_magic_numbers_account_wide(self) -> None:
        self.assertRegex(
            self.code,
            r'input\s+string\s+ManagedMagicNumbers\s*=\s*"4186001"\s*;',
        )
        managed = named_block(self.code, r"\bbool\s+ReadManagedOpenState\s*\([^)]*\)")
        daily = named_block(self.code, r"\bbool\s+ManagedDailyPnl\s*\([^)]*\)")
        weekly = named_block(self.code, r"\bbool\s+ManagedWeeklyPnl\s*\([^)]*\)")
        self.assertIn("IsManagedMarketOrderSelected", managed)
        self.assertNotIn("OrderSymbol", managed)
        self.assertIn("IsManagedMarketOrderSelected", daily)
        self.assertIn("BrokerWeekStart", weekly)
        self.assertIn("MaxManagedWeeklyLossPercent", self.code)
        self.assertIn("ReadManagedLossStreak", self.code)
        self.assertIn("CONSECUTIVE_LOSS_COOLDOWN_ACTIVE", self.code)
        current_risk = named_block(
            self.code,
            r"\bbool\s+ValidateCurrentRiskState\s*\([^)]*\)",
        )
        self.assertIn("ReadManagedOpenState", current_risk)
        self.assertIn("MaxManagedOpenPositions", current_risk)
        self.assertNotIn("SnapshotChannel", current_risk)
        self.assertNotIn("CommandLedgerPath", current_risk)
        account_lock = named_block(
            self.code,
            r"\bbool\s+AccountExecutionLockPath\s*\([^)]*\)",
        )
        self.assertNotIn("SnapshotChannel", account_lock)

    def test_managed_telemetry_failures_are_fail_closed_at_the_order_gate(self) -> None:
        readers = {
            "open": (
                named_block(
                    self.code,
                    r"\bbool\s+ReadManagedOpenState\s*\([^)]*\)",
                ),
                1,
            ),
            "trade_count": (
                named_block(
                    self.code,
                    r"\bbool\s+CountManagedTradesToday\s*\([^)]*\)",
                ),
                2,
            ),
            "daily_pnl": (
                named_block(
                    self.code,
                    r"\bbool\s+ManagedDailyPnl\s*\([^)]*\)",
                ),
                1,
            ),
            "weekly_pnl": (
                named_block(
                    self.code,
                    r"\bbool\s+ManagedWeeklyPnl\s*\([^)]*\)",
                ),
                1,
            ),
            "loss_streak": (
                named_block(
                    self.code,
                    r"\bbool\s+ReadManagedLossStreak\s*\([^)]*\)",
                ),
                1,
            ),
        }
        for name, (block, expected_selects) in readers.items():
            with self.subTest(reader=name):
                self.assertTrue(block)
                self.assertEqual(block.count("if(!OrderSelect"), expected_selects)
                self.assertRegex(
                    block,
                    r"if\s*\(\s*!OrderSelect\([^)]*\)\s*\)\s*return\s+false\s*;",
                )

        for name in ("open", "daily_pnl", "weekly_pnl", "loss_streak"):
            with self.subTest(finite_reader=name):
                self.assertIn("MathIsValidNumber", readers[name][0])

        current_risk = named_block(
            self.code,
            r"\bbool\s+ValidateCurrentRiskState\s*\([^)]*\)",
        )
        resolver = named_block(
            self.code,
            r"\bbool\s+ResolvePositionSize\s*\([^)]*\)",
        )
        telemetry = named_block(
            self.code,
            r"\bvoid\s+UpdateRiskTelemetry\s*\([^)]*\)",
        )
        self.assertIn('reason = "POSITION_TELEMETRY_UNAVAILABLE";', current_risk)
        self.assertGreaterEqual(
            current_risk.count('reason = "HISTORY_TELEMETRY_UNAVAILABLE";'),
            4,
        )
        self.assertIn('reason = "POSITION_TELEMETRY_UNAVAILABLE";', resolver)
        self.assertIn('reason = "POSITION_TELEMETRY_UNAVAILABLE";', telemetry)
        self.assertIn('reason = "HISTORY_TELEMETRY_UNAVAILABLE";', telemetry)

    def test_open_profit_cannot_offset_realized_daily_or_weekly_losses(self) -> None:
        daily = named_block(self.code, r"\bbool\s+ManagedDailyPnl\s*\([^)]*\)")
        weekly = named_block(self.code, r"\bbool\s+ManagedWeeklyPnl\s*\([^)]*\)")
        adjusted = named_block(
            self.code,
            r"\bbool\s+ManagedRiskPnlIncludingFloatingLoss\s*\([^)]*\)",
        )
        current_risk = named_block(
            self.code,
            r"\bbool\s+ValidateCurrentRiskState\s*\([^)]*\)",
        )
        self.assertNotIn("MODE_TRADES", daily)
        self.assertNotIn("MODE_TRADES", weekly)
        self.assertIn("MathMin(0.0, floating_pnl)", adjusted)
        self.assertIn("daily_risk_pnl", current_risk)
        self.assertIn("weekly_risk_pnl", current_risk)
        self.assertNotIn("daily_pnl <= -daily_loss_limit", current_risk)
        self.assertNotIn("weekly_pnl <= -weekly_loss_limit", current_risk)

    def test_loss_latches_are_account_wide_durable_and_fail_closed(self) -> None:
        directory = named_block(
            self.code,
            r"\bbool\s+AccountLossLatchDirectoryPath\s*\([^)]*\)",
        )
        daily_path = named_block(
            self.code,
            r"\bbool\s+DailyLossLockPath\s*\([^)]*\)",
        )
        weekly_path = named_block(
            self.code,
            r"\bbool\s+WeeklyLossLockPath\s*\([^)]*\)",
        )
        self.assertIn("AccountPortfolioPolicyDirectoryPath", directory)
        self.assertIn('"\\\\risk-latches"', directory)
        for block in (directory, daily_path, weekly_path):
            self.assertNotIn("BasePath()", block)
            self.assertNotIn("SnapshotChannel", block)
        self.assertIn("LegacyDailyLossLockPath", self.code)
        self.assertIn("LegacyWeeklyLossLockPath", self.code)

        daily_activate = named_block(
            self.code,
            r"\bbool\s+ActivateDailyLossLatch\s*\([^)]*\)",
        )
        weekly_activate = named_block(
            self.code,
            r"\bbool\s+ActivateWeeklyLossLatch\s*\([^)]*\)",
        )
        daily_persist = named_block(
            self.code,
            r"\bbool\s+PersistDailyLossLatchContext\s*\([^)]*\)",
        )
        weekly_persist = named_block(
            self.code,
            r"\bbool\s+PersistWeeklyLossLatchContext\s*\([^)]*\)",
        )
        for name, activate, persist in (
            ("DAILY", daily_activate, daily_persist),
            ("WEEKLY", weekly_activate, weekly_persist),
        ):
            with self.subTest(period=name):
                memory_assignment = persist.find("latched_in_memory = true")
                context_validation = persist.find("period_start <= 0")
                durable_write = persist.find("WriteCommonTextAtomic")
                self.assertGreaterEqual(memory_assignment, 0)
                self.assertGreater(context_validation, memory_assignment)
                self.assertGreater(durable_write, context_validation)
                self.assertIn("GlobalVariableSet", persist)
                self.assertIn("GlobalVariablesFlush", persist)
                self.assertIn(f"{name}_LOSS_LATCH_PATH_UNAVAILABLE", persist)
                self.assertIn(f"{name}_LOSS_LATCH_PERSISTENCE_FAILED", persist)
                self.assertIn(
                    f"{name}_LOSS_LATCH_ACCOUNT_PERSISTENCE_FAILED",
                    persist,
                )
                self.assertIn(f"{name.title()}LossLatchContext", activate)
                self.assertIn(f"Persist{name.title()}LossLatchContext", activate)

        daily_gate = named_block(
            self.code,
            r"\bbool\s+DailyLossLatchAllowsTrading\s*\([^)]*\)",
        )
        weekly_gate = named_block(
            self.code,
            r"\bbool\s+WeeklyLossLatchAllowsTrading\s*\([^)]*\)",
        )
        for name, block in (("DAILY", daily_gate), ("WEEKLY", weekly_gate)):
            with self.subTest(gate=name):
                self.assertIn("GlobalVariableCheck", block)
                self.assertIn("Legacy", block)
                self.assertIn("latched_in_memory", block)
                self.assertIn("MIGRATION_FAILED", block)
                self.assertIn("LIMIT_LATCHED", block)
                self.assertIn("Activate", block)

        combined_gate = named_block(
            self.code,
            r"\bbool\s+LossLatchesAllowTrading\s*\([^)]*\)",
        )
        self.assertIn("DailyLossLatchAllowsTrading", combined_gate)
        self.assertIn("WeeklyLossLatchAllowsTrading", combined_gate)
        self.assertLess(
            combined_gate.find("DailyLossLatchAllowsTrading"),
            combined_gate.find("if(!daily_allows)"),
        )
        self.assertLess(
            combined_gate.find("WeeklyLossLatchAllowsTrading"),
            combined_gate.find("if(!daily_allows)"),
        )
        self.assertIn("GlobalVariablesFlush", daily_persist)
        self.assertIn("GlobalVariablesFlush", weekly_persist)

        current_risk = named_block(
            self.code,
            r"\bbool\s+ValidateCurrentRiskState\s*\([^)]*\)",
        )
        self.assertIn("if(!LossLatchesAllowTrading(reason))", current_risk)
        self.assertLess(
            current_risk.find("LossLatchesAllowTrading"),
            current_risk.find("ReadManagedOpenState"),
        )
        self.assertRegex(
            current_risk,
            r"if\s*\(\s*!ActivateDailyLossLatch\(reason\)\s*\)\s*return\s+false",
        )
        self.assertRegex(
            current_risk,
            r"if\s*\(\s*!ActivateWeeklyLossLatch\(reason\)\s*\)\s*return\s+false",
        )

    def test_legacy_loss_latch_upgrade_barrier_scans_every_channel_fail_closed(self) -> None:
        migration = named_block(
            self.code,
            r"\bbool\s+MigrateLegacyLossLatchesAcrossChannels\s*\([^)]*\)",
        )
        scanner = named_block(
            self.code,
            r"\bbool\s+ScanLegacyLossLatchesAcrossChannels\s*\([^)]*\)",
        )
        anchor = named_block(
            self.code,
            r"\bbool\s+EnsureLegacyLossLatchScanAnchor\s*\([^)]*\)",
        )
        classifier = named_block(
            self.code,
            r"\bbool\s+ClassifyLegacyLossLatchRootEntry\s*\([^)]*\)",
        )
        probe = named_block(
            self.code,
            r"\bbool\s+ProbeLegacyLossLatchMarker\s*\([^)]*\)",
        )
        self.assertIn("g_account_execution_lock_handle == INVALID_HANDLE", migration)
        self.assertIn('FileFindFirst(\n      "MetafxHQ\\\\*"', scanner)
        self.assertIn("FileFindNext", scanner)
        self.assertIn("ResetLastError", scanner)
        self.assertIn("LEGACY_LOSS_LATCH_SCAN_MAX_ENTRIES", scanner)
        self.assertIn("LEGACY_LOSS_LATCH_ENUMERATION_LIMIT_EXCEEDED", scanner)
        self.assertIn("LEGACY_LOSS_LATCH_ENUMERATION_FAILED", scanner)
        self.assertGreaterEqual(scanner.count("FileFindClose(search_handle)"), 4)
        self.assertIn("ClassifyLegacyLossLatchRootEntry", scanner)
        self.assertIn('"MetafxHQ\\\\" + entry_name', scanner)
        self.assertIn(
            'entry_name != "legacy-loss-latch-scan-anchor-v1.txt"',
            scanner,
        )
        self.assertIn("EnsureLegacyLossLatchScanAnchor", migration)
        self.assertIn("WriteCommonTextAtomic", anchor)
        self.assertIn("ReadCommonText", anchor)
        self.assertIn("LegacyDailyLossLockFileNameForPeriod", migration)
        self.assertIn("LegacyWeeklyLossLockFileNameForPeriod", migration)
        self.assertNotIn("BasePath()", migration)
        self.assertNotIn("SnapshotChannel", migration)
        self.assertEqual(
            migration.count("ScanLegacyLossLatchesAcrossChannels"),
            2,
        )
        self.assertIn("SameStringArrays", migration)
        self.assertIn("LEGACY_LOSS_LATCH_CHANNEL_SET_CHANGED", migration)
        self.assertIn("first_daily_found || second_daily_found", migration)
        self.assertIn("first_weekly_found || second_weekly_found", migration)
        self.assertIn("PersistDailyLossLatchContext", migration)
        self.assertIn("PersistWeeklyLossLatchContext", migration)
        self.assertGreaterEqual(
            migration.count("LEGACY_LOSS_LATCH_PERIOD_CHANGED"),
            2,
        )
        self.assertGreaterEqual(migration.count("BrokerDayStart()"), 3)
        self.assertGreaterEqual(
            migration.count("BrokerWeekStartForDay"),
            3,
        )
        self.assertIn("g_legacy_loss_latch_migration_ready = true", migration)
        self.assertIn('entry_name == "locks"', classifier)
        self.assertIn('entry_name == "account-policies"', classifier)
        self.assertIn("IsSafeChannel(entry_name)", classifier)
        self.assertIn("FILE_ERROR_IS_DIRECTORY", classifier)
        self.assertIn("LEGACY_LOSS_LATCH_ENUMERATION_AMBIGUOUS", classifier)
        self.assertIn("FILE_ERROR_NOT_EXIST", probe)
        self.assertIn("FILE_ERROR_DIRECTORY_NOT_EXIST", probe)
        self.assertIn("LEGACY_LOSS_LATCH_MARKER_PROBE_FAILED", probe)
        self.assertNotRegex(migration + scanner, r"File(?:Delete|Move)\s*\(")

        on_init = named_block(self.code, r"\bint\s+OnInit\s*\([^)]*\)")
        channel_lock = on_init.find("AcquireChannelLock")
        account_lock = on_init.find("AcquireAccountExecutionLock")
        policy_lease = on_init.find("AcquirePortfolioPolicyLease")
        migrate = on_init.find("MigrateLegacyLossLatchesAcrossChannels")
        release_lock = on_init.find("ReleaseAccountExecutionLock")
        timer = on_init.find("EventSetTimer")
        self.assertGreater(account_lock, channel_lock)
        self.assertGreater(policy_lease, account_lock)
        self.assertGreater(migrate, policy_lease)
        self.assertGreater(migrate, account_lock)
        self.assertGreater(release_lock, migrate)
        self.assertGreater(timer, release_lock)
        self.assertIn('"loss_latch_migration"', on_init)
        self.assertIn("legacy_loss_latch_migration_reason", on_init)
        migration_failure = on_init[on_init.find('"loss_latch_migration"') : timer]
        self.assertIn("ReleasePortfolioPolicyLease", migration_failure)
        self.assertIn("ReleaseChannelLock", migration_failure)

        combined_gate = named_block(
            self.code,
            r"\bbool\s+LossLatchesAllowTrading\s*\([^)]*\)",
        )
        self.assertIn("g_legacy_loss_latch_migration_ready", combined_gate)
        self.assertIn("LEGACY_LOSS_LATCH_MIGRATION_NOT_READY", combined_gate)

        # Channel A is offline, but its legacy marker is still discovered when
        # Channel B is the first v2.19 instance started after an upgrade.
        first_entries = [
            ("legacy-loss-latch-scan-anchor-v1.txt", False, False, False),
            ("locks", True, True, True),
            ("account-policies", True, True, True),
            ("mtc-channel-a", True, True, False),
            ("mtc-channel-b", True, False, False),
        ]
        migrated, daily, weekly, reason = legacy_loss_latch_migration_model(
            first_entries,
            list(reversed(first_entries)),
        )
        self.assertTrue(migrated)
        self.assertTrue(daily)
        self.assertFalse(weekly)
        self.assertEqual(reason, "")

        clean_entries = [
            ("legacy-loss-latch-scan-anchor-v1.txt", False, False, False),
            ("mtc-channel-b", True, False, False),
        ]
        clean = legacy_loss_latch_migration_model(clean_entries, clean_entries)
        self.assertEqual(clean, (True, False, False, ""))
        failed_first = legacy_loss_latch_migration_model(
            clean_entries,
            clean_entries,
            first_enumeration_error=True,
        )
        self.assertEqual(
            failed_first[3],
            "LEGACY_LOSS_LATCH_ENUMERATION_FAILED",
        )
        failed_next = legacy_loss_latch_migration_model(
            clean_entries,
            clean_entries,
            second_enumeration_error=True,
        )
        self.assertEqual(
            failed_next[3],
            "LEGACY_LOSS_LATCH_ENUMERATION_FAILED",
        )

        exactly_at_cap = legacy_loss_latch_scan_model(
            [(f"junk-{index}", False, False, False) for index in range(256)]
        )
        self.assertEqual(exactly_at_cap, (True, False, False, ""))
        overflow = legacy_loss_latch_scan_model(
            [(f"junk-{index}", False, False, False) for index in range(257)]
        )
        self.assertEqual(
            overflow[3],
            "LEGACY_LOSS_LATCH_ENUMERATION_LIMIT_EXCEEDED",
        )
        ambiguous = legacy_loss_latch_scan_model(
            [("mtc-channel-file", False, False, False)]
        )
        self.assertEqual(
            ambiguous[3],
            "LEGACY_LOSS_LATCH_ENUMERATION_AMBIGUOUS",
        )

        for absent_error in (0, 5020, 5023):
            with self.subTest(absent_error=absent_error):
                self.assertEqual(
                    legacy_loss_latch_marker_probe_model(
                        is_regular_file=False,
                        error_code=absent_error,
                    ),
                    (True, False),
                )
        for unsafe_error in (5019, 5004, 5016):
            with self.subTest(marker_probe_error=unsafe_error):
                self.assertEqual(
                    legacy_loss_latch_marker_probe_model(
                        is_regular_file=False,
                        error_code=unsafe_error,
                    ),
                    (False, False),
                )

        added_channel = legacy_loss_latch_migration_model(
            clean_entries,
            clean_entries + [("mtc-channel-c", True, False, False)],
        )
        self.assertEqual(
            added_channel[3],
            "LEGACY_LOSS_LATCH_CHANNEL_SET_CHANGED",
        )
        removed_channel = legacy_loss_latch_migration_model(
            [
                ("mtc-channel-a", True, False, False),
                ("mtc-channel-b", True, False, False),
            ],
            [("mtc-channel-a", True, False, False)],
        )
        self.assertEqual(
            removed_channel[3],
            "LEGACY_LOSS_LATCH_CHANNEL_SET_CHANGED",
        )
        appeared_marker = legacy_loss_latch_migration_model(
            [("mtc-channel-a", True, False, False)],
            [("mtc-channel-a", True, True, False)],
        )
        self.assertEqual(appeared_marker, (True, True, False, ""))
        disappeared_marker = legacy_loss_latch_migration_model(
            [("mtc-channel-a", True, False, True)],
            [("mtc-channel-a", True, False, False)],
        )
        self.assertEqual(disappeared_marker, (True, False, True, ""))

        rollover = legacy_loss_latch_migration_model(
            clean_entries,
            clean_entries,
            periods_before_activation=(1_700_086_400, 1_699_747_200),
        )
        self.assertEqual(
            rollover[3],
            "LEGACY_LOSS_LATCH_PERIOD_CHANGED",
        )
        monday_rollover = legacy_loss_latch_migration_model(
            clean_entries,
            clean_entries,
            periods_after_activation=(1_700_000_000, 1_700_352_000),
        )
        self.assertEqual(
            monday_rollover[3],
            "LEGACY_LOSS_LATCH_PERIOD_CHANGED",
        )
        persistence_failure = legacy_loss_latch_migration_model(
            [("mtc-channel-a", True, True, True)],
            [("mtc-channel-a", True, True, True)],
            persistence_ok=False,
        )
        self.assertEqual(persistence_failure[3], "LOSS_LATCH_PERSISTENCE_FAILED")

    def test_broker_order_time_arithmetic_stays_in_the_broker_clock_domain(self) -> None:
        loss_streak = named_block(
            self.code,
            r"\bbool\s+ReadManagedLossStreak\s*\([^)]*\)",
        )
        current_risk = named_block(
            self.code,
            r"\bbool\s+ValidateCurrentRiskState\s*\([^)]*\)",
        )
        lifecycle = named_block(
            self.code,
            r"\bvoid\s+ApplyOptionalPositionLifecycle\s*\([^)]*\)",
        )

        self.assertIn("OrderCloseTime", loss_streak)
        self.assertRegex(
            loss_streak,
            r"cooldown_until\s*=\s*\(int\)newest_time\s*\+\s*ConsecutiveLossCooldownMinutes\s*\*\s*60",
        )
        self.assertIn("int broker_now = (int)TimeCurrent();", current_risk)
        self.assertRegex(current_risk, r"broker_now\s*<\s*cooldown_until")
        self.assertNotRegex(current_risk, r"NowUtc\s*\(\s*\)\s*<\s*cooldown_until")
        self.assertIn("datetime broker_now = TimeCurrent();", lifecycle)
        self.assertRegex(
            lifecycle,
            r"broker_now\s*>=\s*OrderOpenTime\s*\(\s*\)\s*\+\s*MaxHoldingMinutes\s*\*\s*60",
        )
        self.assertNotRegex(
            lifecycle,
            r"NowUtc\s*\(\s*\)\s*>=\s*[^;]*OrderOpenTime",
        )
        self.assertIn('"observedAt\\\":" + IntegerToString(NowUtc())', lifecycle)

        utc_now = 1_800_000_000
        offsets = (3 * 60 * 60, -5 * 60 * 60)

        cooldown_results = []
        old_mixed_cooldown_results = []
        holding_results = []
        old_mixed_holding_results = []
        for broker_offset in offsets:
            broker_now = utc_now + broker_offset
            broker_close_time = broker_now - 30 * 60
            cooldown_until = broker_close_time + 4 * 60 * 60
            broker_open_time = broker_now - 90 * 60
            holding_deadline = broker_open_time + 60 * 60

            cooldown_results.append(broker_now < cooldown_until)
            old_mixed_cooldown_results.append(utc_now < cooldown_until)
            holding_results.append(broker_now >= holding_deadline)
            old_mixed_holding_results.append(utc_now >= holding_deadline)

        self.assertEqual(cooldown_results, [True, True])
        self.assertEqual(holding_results, [True, True])
        self.assertEqual(old_mixed_cooldown_results, [True, False])
        self.assertEqual(old_mixed_holding_results, [False, True])

    def test_position_lifecycle_is_explicit_and_safe_by_default(self) -> None:
        self.assertRegex(
            self.code,
            r"input\s+ENUM_POSITION_LIFECYCLE_MODE\s+PositionLifecycleMode\s*=\s*LIFECYCLE_SLTP_ONLY\s*;",
        )
        self.assertRegex(self.code, r"input\s+int\s+MaxHoldingMinutes\s*=\s*0\s*;")
        self.assertRegex(
            self.code,
            r"input\s+bool\s+EnableRolloverEntryBlock\s*=\s*false\s*;",
        )
        lifecycle = named_block(self.code, r"\bvoid\s+ApplyOptionalPositionLifecycle\s*\([^)]*\)")
        close_guard = named_block(
            self.code,
            r"\bbool\s+LifecycleCloseGuard\s*\([^)]*\)",
        )
        self.assertIn("LIFECYCLE_SLTP_ONLY", close_guard)
        self.assertIn("LifecycleAttemptPath", lifecycle)
        self.assertIn("automaticRetry", lifecycle)
        self.assertIn("LiveArmed", close_guard)
        self.assertIn(
            "GatewayMode == GATEWAY_DEMO && !IsNonRealAccount()",
            close_guard,
        )
        self.assertRegex(
            close_guard,
            r"GatewayMode\s*==\s*GATEWAY_LIVE[\s\S]*?IsNonRealAccount\s*\(\s*\)[\s\S]*?!LiveArmed",
        )
        self.assertIn("LifecycleCloseGuard", lifecycle)

    def test_position_lifecycle_rechecks_signed_close_guard_at_boundary(self) -> None:
        close_guard = named_block(
            self.code,
            r"\bbool\s+LifecycleCloseGuard\s*\([^)]*\)",
        )
        lifecycle = named_block(
            self.code,
            r"\bvoid\s+ApplyOptionalPositionLifecycle\s*\([^)]*\)",
        )

        for token in (
            "ValidateConfiguredModes",
            "GATEWAY_SHADOW",
            "IsTesting()",
            "IsOptimization()",
            "GatewayMode == GATEWAY_DEMO && !IsNonRealAccount()",
            "GatewayMode == GATEWAY_LIVE",
            "IsNonRealAccount()",
            "LiveArmed",
            "SignedCommandVerificationAvailable",
        ):
            self.assertIn(token, close_guard)
        self.assertRegex(
            close_guard,
            r"}\s*if\(!SignedCommandVerificationAvailable\(\)\)",
        )
        self.assertGreaterEqual(lifecycle.count("LifecycleCloseGuard"), 2)
        order_close = lifecycle.find("OrderClose")
        boundary_guard = lifecycle.rfind("LifecycleCloseGuard", 0, order_close)
        lifecycle_marker = lifecycle.find("WriteCommonTextAtomic", boundary_guard)
        self.assertGreaterEqual(boundary_guard, 0)
        self.assertLess(boundary_guard, lifecycle_marker)
        self.assertLess(lifecycle_marker, order_close)

    def test_position_lifecycle_serializes_close_with_account_lock(self) -> None:
        lifecycle = named_block(
            self.code,
            r"\bvoid\s+ApplyOptionalPositionLifecycle\s*\([^)]*\)",
        )

        candidate_probe = lifecycle.find("LifecycleCloseCandidateExists")
        acquire = lifecycle.find("AcquireAccountExecutionLock")
        locked_scope = lifecycle.find("do", acquire)
        locked_guard = lifecycle.find("LifecycleCloseGuard", locked_scope)
        locked_loop = lifecycle.find("for(", locked_guard)
        order_close = lifecycle.find("OrderClose", locked_loop)
        release = lifecycle.find("ReleaseAccountExecutionLock", order_close)

        self.assertGreaterEqual(candidate_probe, 0)
        self.assertLess(candidate_probe, acquire)
        self.assertLess(acquire, locked_scope)
        self.assertLess(locked_scope, locked_guard)
        self.assertLess(locked_guard, locked_loop)
        self.assertLess(locked_loop, order_close)
        self.assertLess(order_close, release)
        self.assertEqual(lifecycle.count("AcquireAccountExecutionLock"), 1)
        self.assertEqual(lifecycle.count("ReleaseAccountExecutionLock"), 1)
        self.assertNotRegex(lifecycle[locked_scope:release], r"\breturn\b")

        boundary_guard = lifecycle.rfind("LifecycleCloseGuard", 0, order_close)
        marker = lifecycle.find("WriteCommonTextAtomic", boundary_guard)
        self.assertGreater(boundary_guard, acquire)
        self.assertLess(boundary_guard, marker)
        self.assertLess(marker, order_close)

    def test_invalid_enum_modes_stop_before_ordersend_and_orderclose(self) -> None:
        gateway_mode = named_block(
            self.code,
            r"\bbool\s+GatewayModeIsValid\s*\([^)]*\)",
        )
        lifecycle_mode = named_block(
            self.code,
            r"\bbool\s+PositionLifecycleModeIsValid\s*\([^)]*\)",
        )
        configured_modes = named_block(
            self.code,
            r"\bbool\s+ValidateConfiguredModes\s*\([^)]*\)",
        )
        mode_name = named_block(self.code, r"\bstring\s+ModeName\s*\([^)]*\)")
        lifecycle_name = named_block(
            self.code,
            r"\bstring\s+LifecycleModeName\s*\([^)]*\)",
        )
        on_init = named_block(self.code, r"\bint\s+OnInit\s*\([^)]*\)")
        execution_guard = named_block(
            self.code,
            r"\bbool\s+EvaluateExecutionGuard\s*\([^)]*\)",
        )
        runtime_guard = named_block(
            self.code,
            r"\bbool\s+ValidateRuntime\s*\([^)]*\)",
        )
        execute = named_block(self.code, r"\bvoid\s+ExecuteCommand\s*\([^)]*\)")
        lifecycle = named_block(
            self.code,
            r"\bvoid\s+ApplyOptionalPositionLifecycle\s*\([^)]*\)",
        )

        for token in ("GATEWAY_SHADOW", "GATEWAY_DEMO", "GATEWAY_LIVE"):
            self.assertIn(token, gateway_mode)
        for token in (
            "LIFECYCLE_SLTP_ONLY",
            "LIFECYCLE_MAX_HOLDING",
            "LIFECYCLE_SESSION_CLOSE",
            "LIFECYCLE_MAX_HOLDING_AND_SESSION_CLOSE",
        ):
            self.assertIn(token, lifecycle_mode)
        self.assertIn('reason = "GATEWAY_MODE_INVALID"', configured_modes)
        self.assertIn(
            'reason = "POSITION_LIFECYCLE_MODE_INVALID"',
            configured_modes,
        )
        self.assertRegex(mode_name, r'return\s+"invalid"\s*;\s*$')
        self.assertRegex(lifecycle_name, r'return\s+"INVALID"\s*;\s*$')

        for block in (on_init, execution_guard, runtime_guard):
            self.assertIn("ValidateConfiguredModes", block)
        self.assertLess(
            on_init.find("ValidateConfiguredModes"),
            on_init.find("CryptoSelfTest"),
        )
        self.assertLess(
            execution_guard.find("ValidateConfiguredModes"),
            execution_guard.find("FileIsExist"),
        )
        self.assertLess(
            runtime_guard.find("ValidateConfiguredModes"),
            runtime_guard.find("command.schema_version"),
        )

        order_send = execute.find("OrderSend")
        self.assertGreaterEqual(order_send, 0)
        send_boundary = execute.rfind("ValidateConfiguredModes", 0, order_send)
        self.assertGreaterEqual(send_boundary, 0)
        self.assertRegex(
            execute[send_boundary:order_send],
            r"ValidateConfiguredModes\s*\([^)]*\)[\s\S]*?FinalizeCommand[\s\S]*?break\s*;",
        )

        order_close = lifecycle.find("OrderClose")
        self.assertGreaterEqual(order_close, 0)
        close_boundary = lifecycle.rfind("ValidateConfiguredModes", 0, order_close)
        lifecycle_marker = lifecycle.find("WriteCommonTextAtomic", close_boundary)
        self.assertGreaterEqual(close_boundary, 0)
        self.assertRegex(
            lifecycle[close_boundary:lifecycle_marker],
            r"ValidateConfiguredModes\s*\([^)]*\)[\s\S]*?break\s*;",
        )
        self.assertLess(close_boundary, lifecycle_marker)
        self.assertLess(lifecycle_marker, order_close)

    def test_order_send_is_verified_and_outcomes_are_refreshed(self) -> None:
        execute = named_block(self.code, r"\bvoid\s+ExecuteCommand\s*\([^)]*\)")
        verify = named_block(self.code, r"\bbool\s+CaptureSelectedOrderEvidence\s*\([^)]*\)")
        filled_risk = named_block(
            self.code,
            r"\bstring\s+FilledRiskAssessmentCode\s*\([^)]*\)",
        )
        ack = named_block(self.code, r"\bstring\s+BuildAckJson\s*\([^)]*\)")
        self.assertGreater(execute.find("CaptureSelectedOrderEvidence"), execute.find("OrderSend"))
        self.assertIn("OrderSelect", verify)
        for token in (
            "OrderOpenPrice",
            "FilledRiskAssessmentCode",
            "identity_matches",
            "OrderStopLoss",
            "OrderTakeProfit",
            "OrderMagicNumber",
            "OrderComment",
            "ORDER_POST_SEND_VERIFICATION_MISMATCH",
        ):
            self.assertIn(token, verify)
        identity_start = verify.find("bool identity_matches")
        identity_end = verify.find("if(!identity_matches)")
        self.assertGreaterEqual(identity_start, 0)
        self.assertGreater(identity_end, identity_start)
        self.assertNotIn(
            "slippage_within_limit",
            verify[identity_start:identity_end],
        )
        for token in (
            "SlippagePoints",
            "ReadBrokerRiskMetadata",
            "actual_risk",
            "SLIPPAGE_RESERVE_AND_RISK_ESTIMATE_EXCEEDED",
            "RISK_ESTIMATE_EXCEEDED",
            "SLIPPAGE_RESERVE_EXCEEDED",
            "RISK_UNAVAILABLE",
        ):
            self.assertIn(token, filled_risk)
        for token in (
            "ORDER_VERIFIED_OPEN",
            "ORDER_VERIFIED_CLOSED",
            "_SLIPPAGE_RESERVE_AND_RISK_ESTIMATE_EXCEEDED",
            "_RISK_ESTIMATE_EXCEEDED",
            "_SLIPPAGE_RESERVE_EXCEEDED",
            "_RISK_UNAVAILABLE",
        ):
            self.assertIn(token, verify)
        for field in (
            "filledPrice",
            "filledSlippagePoints",
            "actualStopLoss",
            "actualTakeProfit",
            "actualMagicNumber",
            "actualComment",
            "verificationStatus",
            "executionState",
            "closedPnl",
            "positionSizingMode",
            "riskPercent",
            "riskCapitalBase",
            "riskCapitalAmount",
            "estimatedRiskMoney",
        ):
            self.assertIn(field, ack)
        timer = named_block(self.code, r"\bvoid\s+OnTimer\s*\([^)]*\)")
        self.assertIn("RefreshManagedOutcomeFiles", timer)

    def test_ticket_mapping_survives_broker_tp_sl_comment_rewrite(self) -> None:
        ensure = named_block(self.code, r"\bvoid\s+EnsureFolders\s*\([^)]*\)")
        writer = named_block(self.code, r"\bbool\s+WriteTicketCommandMap\s*\([^)]*\)")
        reader = named_block(self.code, r"\bbool\s+ReadSelectedOrderTicketMap\s*\([^)]*\)")
        outcome = named_block(self.code, r"\bbool\s+WriteSelectedOrderOutcome\s*\([^)]*\)")
        refresh = named_block(self.code, r"\bvoid\s+RefreshManagedOutcomeFiles\s*\([^)]*\)")
        reconcile = named_block(self.code, r"\bvoid\s+ReconcileExecutingCommand\s*\([^)]*\)")
        process = named_block(self.code, r"\bvoid\s+ProcessCommandFile\s*\([^)]*\)")
        self.assertIn('"\\\\tickets"', ensure)
        self.assertIn("metafx-hq-mt4-ticket-map-v1", writer)
        self.assertIn("OrderTicket", reader)
        self.assertIn("OrderMagicNumber", reader)
        self.assertIn("IsBrokerClosedGatewayComment", reader)
        self.assertIn("[tp]", self.code)
        self.assertIn("[sl]", self.code)
        self.assertIn('JsonString("HQ:" + command_id)', outcome)
        self.assertIn("ResolveSelectedOrderCommandId", refresh)
        self.assertIn("WriteTicketCommandMap", reconcile)
        self.assertIn('processed_status == "EXECUTION_UNKNOWN"', process)

    def test_startup_backfill_is_bounded_exact_idempotent_and_never_resends(self) -> None:
        backfill = named_block(
            self.code,
            r"\bvoid\s+BackfillLegacyExecutionMapsAndOutcomes\s*\([^)]*\)",
        )
        parser = named_block(
            self.code,
            r"\bbool\s+ParseLegacyExecutedAck\s*\([^)]*\)",
        )
        matcher = named_block(
            self.code,
            r"\bbool\s+SelectedOrderMatchesLegacyExecutedAck\s*\([^)]*\)",
        )
        on_init = named_block(self.code, r"\bint\s+OnInit\s*\([^)]*\)")
        self.assertTrue(backfill)
        self.assertIn("LEGACY_BACKFILL_MAX_ACKS", backfill)
        self.assertIn("FileFindFirst", backfill)
        self.assertIn("processed\\\\commands\\\\*.json", backfill)
        self.assertIn("LegacyBackfillTicketIsAmbiguous", backfill)
        self.assertIn("ReadSelectedOrderTicketMap", backfill)
        self.assertIn("WriteSelectedOrderLegacyTicketMap", backfill)
        self.assertIn("WriteSelectedOrderOutcome", backfill)
        self.assertIn("automaticRetry", backfill)
        self.assertNotIn("OrderSend", backfill)
        self.assertIn("BackfillLegacyExecutionMapsAndOutcomes", on_init)
        for token in (
            "EXECUTED",
            "statePersisted",
            "signatureVerificationStatus",
            "ticket",
            "actualMagicNumber",
            "fixedLot",
            "filledPrice",
            "filledSlippagePoints",
            "actualStopLoss",
            "actualTakeProfit",
            "actualComment",
        ):
            self.assertIn(token, parser)
        for token in (
            "OrderTicket",
            "OrderMagicNumber",
            "OrderSymbol",
            "OrderType",
            "OrderLots",
            "OrderOpenPrice",
            "OrderStopLoss",
            "OrderTakeProfit",
            "IsBrokerClosedGatewayComment",
        ):
            self.assertIn(token, matcher)

    def test_atomic_writer_retries_with_backoff_and_failure_telemetry(self) -> None:
        attempt = named_block(
            self.code,
            r"\bbool\s+TryWriteCommonTextAtomic\s*\([^)]*\)",
        )
        retry = named_block(
            self.code,
            r"\bbool\s+WriteCommonTextAtomicWithTemporary\s*\([^)]*\)",
        )
        snapshot = named_block(self.code, r"\bbool\s+WriteSnapshot\s*\([^)]*\)")
        chart = named_block(self.code, r"\bvoid\s+UpdateChartStatus\s*\([^)]*\)")
        self.assertIn("FileWriteString", attempt)
        self.assertIn("FileMove", attempt)
        self.assertGreaterEqual(attempt.count("GetLastError"), 2)
        self.assertIn("ATOMIC_WRITE_MAX_ATTEMPTS", retry)
        self.assertIn("TryWriteCommonTextAtomic", retry)
        self.assertIn("Sleep", retry)
        self.assertIn("g_consecutive_atomic_write_failures++", retry)
        self.assertIn("g_last_atomic_write_error", retry)
        self.assertIn("WriteCommonTextAtomicWithTemporary", snapshot)
        self.assertIn("g_consecutive_atomic_write_failures", chart)
        self.assertIn("g_last_atomic_write_error", chart)

    def test_closed_outcome_payload_is_stable_and_not_rewritten(self) -> None:
        outcome = named_block(
            self.code,
            r"\bbool\s+WriteSelectedOrderOutcome\s*\([^)]*\)",
        )
        self.assertIn("outcome_observed_at", outcome)
        self.assertIn("OrderCloseTime", outcome)
        self.assertIn("existing_payload", outcome)
        self.assertRegex(
            outcome,
            r"Trimmed\s*\(\s*existing_payload\s*\)\s*==\s*payload",
        )
        compare_at = outcome.find("existing_payload")
        write_at = outcome.rfind("WriteCommonTextAtomic")
        self.assertGreater(write_at, compare_at)

    def test_signed_command_verifier_is_dynamic_and_snapshot_reports_market_state(self) -> None:
        signed = named_block(self.code, r"\bbool\s+SignedCommandVerificationAvailable\s*\([^)]*\)")
        self.assertIn("RefreshSigningReadiness", signed)
        self.assertNotIn("return false", signed)
        snapshot = named_block(self.code, r"\bstring\s+BuildSnapshotJson\s*\([^)]*\)")
        for field in (
            "marketOpen",
            "marketSession",
            "ACCOUNT_WIDE",
            "managedSummary",
            "MANAGED_MAGIC_NUMBERS_ACCOUNT_WIDE",
        ):
            self.assertIn(field, snapshot)
        capabilities = named_block(self.code, r"\bstring\s+BuildCapabilitiesJson\s*\([^)]*\)")
        self.assertIn("signedCommandVerification", capabilities)
        self.assertIn("liveExecutionAvailable", capabilities)
        self.assertIn("MT4_LOADED_ACCOUNT_HISTORY", capabilities)

    def test_status_v5_exposes_account_policy_and_protection_telemetry(self) -> None:
        self.assertIn('metafx-hq-mt4-status-v5', self.code)
        self.assertNotIn('metafx-hq-mt4-status-v4', self.code)
        self.assertNotIn('metafx-hq-mt4-status-v3', self.code)
        status = named_block(self.code, r"\bstring\s+BuildStatusJson\s*\([^)]*\)")
        for field in (
            "eaVersion",
            "demoAccount",
            "accountMode",
            "commandSchemaVersion",
            "ackSchemaVersion",
            "executionGuardReady",
            "executionGuardReason",
            "portfolioPolicyStatus",
            "portfolioPolicyDigest",
            "portfolioGuardScope",
            "managedMagicNumbers",
            "allowedSymbols",
            "allowedTimeframes",
            "same_windows_user_file_common",
            "crossVpsDistributedLock",
            "maxManagedPositions",
            "currentManagedPositions",
            "maxManagedLots",
            "currentManagedLots",
            "positionSizingMode",
            "riskPercent",
            "riskCapitalBase",
            "estimatedCommissionPerLot",
            "commissionFreeAccountConfirmed",
            "brokerVolumeMin",
            "brokerVolumeMax",
            "brokerVolumeStep",
            "maxTradesToday",
            "currentTradesToday",
            "maxLossPerTradePercent",
            "maxDailyLossPercent",
            "managedDailyPnl",
            "maxAccountEquityDrawdownPercent",
            "currentAccountEquityDrawdownPercent",
            "minRewardRiskRatio",
            "minProjectedMarginLevelPercent",
            "currentMarginLevelPercent",
            "maxSnapshotAgeSeconds",
            "maxSignalDriftPoints",
            "maxQuoteAgeSeconds",
            "signedCommandVerificationAvailable",
            "activeSigningKeyId",
            "signingKeyPinned",
            "signatureAlgorithm",
            "lastSignatureVerificationStatus",
        ):
            self.assertIn(field, status)
        for forbidden in ("AccountNumber", "password", "token", "cookie", "secret"):
            self.assertNotIn(forbidden, status)

    def test_signed_envelope_contract_and_hmac_preimage_match_backend(self) -> None:
        self.assertIn('metafx-hq-mt4-signed-envelope-v1', self.code)
        self.assertIn('HMAC-SHA256', self.code)
        verifier = named_block(self.code, r"\bbool\s+VerifySignedEnvelope\s*\([^)]*\)")
        self.assertTrue(verifier)
        for field in (
            "schemaVersion",
            "algorithm",
            "keyId",
            "payloadHex",
            "signatureHex",
        ):
            self.assertIn(field, verifier)
        self.assertIn("ArraySize(keys) != 5", verifier)
        for fragment in (
            "METAFXHQ|MT4|",
            "|HMAC-SHA256|V1\\n",
            "SnapshotChannel",
            "payload_hex",
        ):
            self.assertIn(fragment, verifier)
        self.assertIn("ConstantTimeHexEquals", verifier)
        self.assertIn("LoadActiveSigningKey", verifier)

    def test_signing_keys_are_backend_owned_binary_file_common_material(self) -> None:
        self.assertRegex(
            self.code,
            r'input\s+string\s+TrustedSigningKeyId\s*=\s*""\s*;',
        )
        self.assertIn('active-key.id', self.code)
        self.assertIn('"\\\\" + key_id + ".key"', self.code)
        loader = named_block(self.code, r"\bbool\s+ReadSigningKey\s*\([^)]*\)")
        self.assertIn("FILE_COMMON", loader)
        self.assertIn("FILE_BIN", loader)
        self.assertIn("size != 32", loader)
        self.assertIn('"hk-" + BytesToHex', loader)
        active = named_block(self.code, r"\bbool\s+LoadActiveSigningKey\s*\([^)]*\)")
        self.assertIn("GATEWAY_LIVE", active)
        self.assertIn("g_trusted_signing_key_id", active)
        self.assertNotIn("TrustedSigningKeyId", active)
        self.assertIn("LIVE_SIGNING_KEY_PIN_REQUIRED", active)
        self.assertIn("LIVE_SIGNING_KEY_PIN_MISMATCH", active)
        self.assertIn("g_signing_key_pinned = explicit_pin_matches", active)
        self.assertNotIn("GatewayMode == GATEWAY_DEMO && !explicit_pin_matches", active)
        capabilities = named_block(self.code, r"\bstring\s+BuildCapabilitiesJson\s*\([^)]*\)")
        self.assertIn("explicit_live_pin", capabilities)
        self.assertIn("g_trusted_signing_key_id", capabilities)
        self.assertNotIn("TrustedSigningKeyId", capabilities)
        self.assertIn("GatewayMode == GATEWAY_LIVE", capabilities)
        for live_guard in (
            "!demo_account",
            "signed_ready",
            "explicit_live_pin",
            "live_commission_policy_confirmed",
            "live_symbol_exact_allowlist_confirmed",
            "LiveArmed",
        ):
            self.assertIn(live_guard, capabilities)

    def test_optional_pin_is_normalized_and_only_armed_live_fails_closed(self) -> None:
        lowercase = named_block(self.code, r"\bstring\s+Lowercase\s*\([^)]*\)")
        self.assertIn("StringToLower", lowercase)
        normalize = named_block(
            self.code,
            r"\bstring\s+NormalizeSigningKeyId\s*\([^)]*\)",
        )
        self.assertIn("Lowercase(Trimmed(value))", normalize)

        on_init = named_block(self.code, r"\bint\s+OnInit\s*\([^)]*\)")
        self.assertIn(
            "g_trusted_signing_key_id = NormalizeSigningKeyId(TrustedSigningKeyId)",
            on_init,
        )
        malformed_pin = named_block(
            on_init,
            r"if\s*\(\s*StringLen\(supplied_signing_key_id\)[\s\S]*?"
            r"!IsSigningKeyId\(g_trusted_signing_key_id\)\s*\)",
        )
        self.assertIn("GatewayMode == GATEWAY_LIVE", malformed_pin)
        self.assertIn("LiveArmed", malformed_pin)
        self.assertEqual(malformed_pin.count("InitFailure"), 1)
        self.assertIn("LIVE_SIGNING_KEY_PIN_INVALID", malformed_pin)
        self.assertIn('g_trusted_signing_key_id = ""', malformed_pin)
        self.assertIn("NON_EXECUTING_SIGNING_KEY_PIN_INVALID_IGNORED", malformed_pin)
        self.assertIn("OPTIONAL_SIGNING_KEY_PIN_INVALID_IGNORED", malformed_pin)
        self.assertIn("if(GatewayMode == GATEWAY_LIVE)", malformed_pin)
        self.assertIn("OPTIONAL_SIGNING_KEY_PIN_MISMATCH_IGNORED", on_init)
        self.assertIn("GatewayMode != GATEWAY_LIVE", on_init)
        self.assertIn(
            "GatewayMode == GATEWAY_LIVE && LiveArmed && !signing_ready",
            on_init,
        )
        self.assertIn("LIVE_DISARMED_SIGNING_NOT_READY_", on_init)
        self.assertIn("StringLen(g_init_warning_code) == 0", on_init)

    def test_live_disarmed_stays_attached_and_execution_guards_remain_closed(self) -> None:
        on_init = named_block(self.code, r"\bint\s+OnInit\s*\([^)]*\)")
        execution_guard = named_block(
            self.code,
            r"\bbool\s+EvaluateExecutionGuard\s*\([^)]*\)",
        )
        command_guard = named_block(
            self.code,
            r"\bbool\s+ValidateRuntime\s*\([^)]*\)",
        )

        self.assertNotIn(
            "GatewayMode == GATEWAY_LIVE && !signing_ready",
            on_init,
        )
        self.assertIn(
            "GatewayMode == GATEWAY_LIVE && LiveArmed && !signing_ready",
            on_init,
        )
        self.assertIn('"LIVE_NOT_ARMED"', execution_guard)
        self.assertIn('"LIVE_NOT_ARMED"', command_guard)
        self.assertLess(
            execution_guard.find('reason = "LIVE_NOT_ARMED"'),
            execution_guard.find("SignedCommandVerificationAvailable"),
        )
        self.assertLess(
            command_guard.find('reason = "LIVE_NOT_ARMED"'),
            command_guard.find("SignedCommandVerificationAvailable"),
        )

    def test_init_failures_write_structured_status_and_append_audit(self) -> None:
        path = named_block(self.code, r"\bstring\s+InitStatusPath\s*\([^)]*\)")
        self.assertIn("init-status.json", path)
        diagnostic = named_block(
            self.code,
            r"\bbool\s+RecordInitDiagnostic\s*\([^)]*\)",
        )
        for field in (
            "metafx-hq-mt4-init-status-v1",
            "eaVersion",
            "channelId",
            "gatewayMode",
            "severity",
            "stage",
            "reasonCode",
            "warningCode",
            "returnCode",
            "observedAt",
        ):
            self.assertIn(field, diagnostic)
        self.assertIn("WriteCommonTextAtomic(InitStatusPath(), payload)", diagnostic)
        self.assertIn("AppendAudit(payload)", diagnostic)

        failure = named_block(self.code, r"\bint\s+InitFailure\s*\([^)]*\)")
        self.assertLess(
            failure.find("RecordInitDiagnostic"),
            failure.find("return return_code"),
        )
        on_init = named_block(self.code, r"\bint\s+OnInit\s*\([^)]*\)")
        self.assertGreaterEqual(on_init.count("InitFailure"), 10)
        self.assertIn(
            'RecordInitDiagnostic("info", "ready", "INIT_SUCCEEDED", INIT_SUCCEEDED)',
            on_init,
        )

    def test_capabilities_report_demo_and_live_readiness_from_actual_account(self) -> None:
        account_mode = named_block(self.code, r"\bstring\s+AccountModeName\s*\([^)]*\)")
        self.assertIn("IsNonRealAccount()", account_mode)
        non_real = named_block(
            self.code,
            r"\bbool\s+IsNonRealAccount\s*\([^)]*\)",
        )
        self.assertIn("AccountInfoInteger(ACCOUNT_TRADE_MODE)", non_real)
        self.assertIn("mode != ACCOUNT_TRADE_MODE_REAL", non_real)
        self.assertNotIn("IsDemo()", non_real)
        self.assertIn('return "demo"', account_mode)
        self.assertIn('return "live"', account_mode)

        capabilities = named_block(self.code, r"\bstring\s+BuildCapabilitiesJson\s*\([^)]*\)")
        for field in (
            "gatewayMode",
            "demoAccount",
            "accountMode",
            "demoExecutionAvailable",
            "liveExecutionAvailable",
            "liveBlockReason",
        ):
            self.assertIn(field, capabilities)
        self.assertRegex(
            capabilities,
            r"demo_ready\s*=\s*GatewayMode\s*==\s*GATEWAY_DEMO\s*&&\s*demo_account\s*&&\s*signed_ready",
        )
        self.assertRegex(
            capabilities,
            r"live_ready\s*=\s*GatewayMode\s*==\s*GATEWAY_LIVE[\s\S]*?!demo_account[\s\S]*?signed_ready[\s\S]*?explicit_live_pin[\s\S]*?live_commission_policy_confirmed[\s\S]*?live_symbol_exact_allowlist_confirmed[\s\S]*?LiveArmed",
        )
        self.assertIn("LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT", capabilities)
        self.assertLess(
            capabilities.find("if(demo_account)"),
            capabilities.find("if(!signed_ready)"),
        )
        self.assertIn("JsonBoolean(demo_ready)", capabilities)
        self.assertIn("JsonBoolean(live_ready)", capabilities)

    def test_manual_hmac_self_test_uses_python_compatible_vector(self) -> None:
        hmac_body = named_block(self.code, r"\bbool\s+HmacSha256\s*\([^)]*\)")
        self.assertGreaterEqual(hmac_body.count("Sha256Bytes"), 2)
        self.assertIn("0x36", hmac_body)
        self.assertIn("0x5c", hmac_body)
        self.assertIn("CRYPT_HASH_SHA256", self.code)
        self_test = named_block(self.code, r"\bbool\s+CryptoSelfTest\s*\([^)]*\)")
        for literal in (
            "hk-630dcd2966c4336691125448bbb25b4ff412a49c732db2c8abc1b8581bd710dd",
            "7b22736368656d6156657273696f6e223a226d65746166782d68712d6d74342d636f6d6d616e642d7632227d",
            "cb256044ef860dd92296c6018b97cead345a0df428268da402624bb9e6eeb478",
            "mtc-demo-01",
        ):
            self.assertIn(literal, self_test)
        on_init = named_block(self.code, r"\bint\s+OnInit\s*\([^)]*\)")
        self.assertIn("CryptoSelfTest", on_init)
        self.assertIn("INIT_FAILED", on_init)

    def test_command_and_heartbeat_are_verified_before_inner_json_is_used(self) -> None:
        parse_command = named_block(self.code, r"\bbool\s+ParseCommand\s*\([^)]*\)")
        self.assertLess(
            parse_command.find("VerifySignedEnvelope"),
            parse_command.find("ParseCommandPayload"),
        )
        heartbeat = named_block(self.code, r"\bbool\s+ValidateHeartbeat\s*\([^)]*\)")
        self.assertLess(
            heartbeat.find("VerifySignedEnvelope"),
            heartbeat.find("ParseFlatJson"),
        )
        process = named_block(self.code, r"\bvoid\s+ProcessCommandFile\s*\([^)]*\)")
        self.assertIn("ParseCommand(raw", process)
        self.assertIn("ExecuteCommand(command, raw, resolved_lots)", process)

    def test_demo_and_live_share_signed_ordersend_path_and_ack_v3(self) -> None:
        execute = named_block(self.code, r"\bvoid\s+ExecuteCommand\s*\([^)]*\)")
        self.assertGreaterEqual(execute.count("ReverifyCommandEnvelope"), 2)
        self.assertEqual(execute.count("OrderSend"), 1)
        self.assertNotRegex(execute, r"GATEWAY_DEMO[^}]*OrderSend")
        ack = named_block(self.code, r"\bstring\s+BuildAckJson\s*\([^)]*\)")
        self.assertIn("signatureVerificationStatus", ack)
        self.assertIn("metafx-hq-mt4-ack-v3", self.code)
        self.assertIn('version   "2.19"', self.code)
        self.assertIn('EA_VERSION = "2.19"', self.code)
        self.assertIn("JsonNumber(command.reference_price, 8)", ack)

    def test_risk_estimate_uses_documented_mt4_tick_size_points_and_local_fees(self) -> None:
        estimate = named_block(
            self.code,
            r"\bbool\s+EstimateStopLossMoneyAtEntry\s*\([^)]*\)",
        )
        metadata = named_block(self.code, r"\bbool\s+ReadBrokerRiskMetadata\s*\([^)]*\)")
        self.assertIn("MODE_TICKSIZE", metadata)
        self.assertIn("tick_size_points * point", metadata)
        self.assertNotIn("tick_size_points < 1.0", metadata)
        self.assertIn("risk_distance / tick_size_price * tick_value", estimate)
        self.assertIn("EffectiveEstimatedCommissionPerLot", estimate)
        self.assertIn("SlippagePoints * point", estimate)
        self.assertIn("gross_reward_per_lot - effective_commission", estimate)
        self.assertIn("net_reward_per_lot / loss_per_lot", estimate)
        self.assertNotRegex(self.code, r"(?i)AccountName\s*\(")
        self.assertNotRegex(self.code, r"(?i)(?:cent|pro.?cent)[^\r\n;]*\*\s*100")

    def test_risk_percent_sizing_rounds_down_and_never_forces_broker_minimum(self) -> None:
        normalize = named_block(
            self.code,
            r"\bbool\s+NormalizeRiskVolumeDown\s*\([^)]*\)",
        )
        resolve = named_block(self.code, r"\bbool\s+ResolvePositionSize\s*\([^)]*\)")
        self.assertIn("MathFloor", normalize)
        self.assertNotIn("MathRound", normalize)
        self.assertIn("(capped_lots - minimum) / step", normalize)
        broker_grid = named_block(
            self.code,
            r"\bbool\s+VolumeIsOnBrokerStep\s*\([^)]*\)",
        )
        lot_digits = named_block(self.code, r"\bint\s+LotDigits\s*\([^)]*\)")
        self.assertIn("(lots - minimum) / step", broker_grid)
        self.assertIn("MODE_LOTSTEP", lot_digits)
        self.assertIn("MODE_MINLOT", lot_digits)
        self.assertIn("MathMax", lot_digits)
        self.assertIn("RISK_VOLUME_BELOW_BROKER_MINIMUM", normalize)
        self.assertNotRegex(normalize, r"normalized_lots\s*=\s*minimum")
        self.assertIn("while(estimated_risk_money > risk_budget)", resolve)
        self.assertIn("resolved_lots - step", resolve)
        self.assertIn("MaxManagedTotalLots - managed_lots", resolve)
        self.assertIn("RISK_STOP_LOSS_CALCULATION_FAILED", resolve)
        self.assertGreaterEqual(
            resolve.count("RISK_ESTIMATE_BELOW_WIRE_MINIMUM"),
            2,
        )
        self.assertGreaterEqual(
            resolve.count("estimated_risk_money < 0.00000001"),
            2,
        )
        self.assertIn("effective_risk_percent > MaxLossPerTradePercent", self.code)

        on_init = named_block(self.code, r"\bint\s+OnInit\s*\([^)]*\)")
        for input_name in (
            "FixedLot",
            "RiskPercent",
            "EstimatedCommissionPerLot",
            "MaxManagedTotalLots",
            "MaxLossPerTradePercent",
            "MaxDailyLossPercent",
            "MaxManagedWeeklyLossPercent",
            "MaxAccountEquityDrawdownPercent",
            "MinRewardRiskRatio",
            "MinProjectedMarginLevelPercent",
        ):
            with self.subTest(input_name=input_name):
                self.assertIn(f"MathIsValidNumber({input_name})", on_init)

        rounded = risk_volume_model(
            capital=10_000.0,
            balance=10_000.0,
            risk_percent=1.0,
            hard_cap_percent=1.0,
            stop_distance=3.32,
            point=0.01,
            tick_size_points=1.0,
            tick_value=1.0,
            commission_per_lot=0.0,
            slippage_points=1,
            minimum=0.01,
            maximum=100.0,
            step=0.01,
            max_managed_lots=100.0,
            current_managed_lots=0.0,
        )
        self.assertIsNotNone(rounded)
        assert rounded is not None
        self.assertAlmostEqual(rounded[0], 0.30)
        self.assertLessEqual(rounded[1], 100.0)

        arbitrary_grid = risk_volume_model(
            capital=6_100.0,
            balance=6_100.0,
            risk_percent=1.0,
            hard_cap_percent=1.0,
            stop_distance=1.0,
            point=0.01,
            tick_size_points=1.0,
            tick_value=1.0,
            commission_per_lot=0.0,
            slippage_points=0,
            minimum=0.10,
            maximum=100.0,
            step=0.25,
            max_managed_lots=100.0,
            current_managed_lots=0.0,
        )
        self.assertIsNotNone(arbitrary_grid)
        assert arbitrary_grid is not None
        self.assertAlmostEqual(arbitrary_grid[0], 0.60)
        self.assertAlmostEqual((arbitrary_grid[0] - 0.10) / 0.25, 2.0)

        below_minimum = risk_volume_model(
            capital=100.0,
            balance=100.0,
            risk_percent=1.0,
            hard_cap_percent=1.0,
            stop_distance=5.0,
            point=0.01,
            tick_size_points=1.0,
            tick_value=1.0,
            commission_per_lot=0.0,
            slippage_points=0,
            minimum=0.01,
            maximum=100.0,
            step=0.01,
            max_managed_lots=100.0,
            current_managed_lots=0.0,
        )
        self.assertIsNone(below_minimum)

    def test_standard_and_cent_account_units_produce_the_same_risk_volume(self) -> None:
        common = dict(
            risk_percent=1.0,
            hard_cap_percent=1.0,
            stop_distance=1.0,
            point=0.01,
            tick_size_points=1.0,
            commission_per_lot=0.0,
            slippage_points=3,
            minimum=0.01,
            maximum=100.0,
            step=0.01,
            max_managed_lots=100.0,
            current_managed_lots=0.0,
        )
        standard = risk_volume_model(
            capital=10_000.0,
            balance=10_000.0,
            tick_value=1.0,
            **common,
        )
        cent = risk_volume_model(
            capital=1_000_000.0,
            balance=1_000_000.0,
            tick_value=100.0,
            **common,
        )
        self.assertIsNotNone(standard)
        self.assertIsNotNone(cent)
        assert standard is not None and cent is not None
        self.assertEqual(standard[0], cent[0])
        self.assertAlmostEqual(standard[1] / 10_000.0, cent[1] / 1_000_000.0)

    def test_sizing_is_persisted_once_and_reused_for_restart_reconciliation(self) -> None:
        process = named_block(self.code, r"\bvoid\s+ProcessCommandFile\s*\([^)]*\)")
        execute = named_block(self.code, r"\bvoid\s+ExecuteCommand\s*\([^)]*\)")
        reconcile = named_block(
            self.code,
            r"\bvoid\s+ReconcileExecutingCommand\s*\([^)]*\)",
        )
        persisted = named_block(
            self.code,
            r"\bbool\s+ReadPersistedSizingState\s*\([^)]*\)",
        )
        ack = named_block(self.code, r"\bstring\s+BuildAckJson\s*\([^)]*\)")
        self.assertEqual(process.count("ResolvePositionSize"), 1)
        self.assertNotIn("ResolvePositionSize", execute)
        self.assertNotIn("ResolvePositionSize", reconcile)
        self.assertLess(process.find("SetAckSizingEvidence"), process.find("ExecuteCommand"))
        self.assertLess(execute.find("WriteExecutionMarkers"), execute.find("OrderSend"))
        self.assertIn("ReadPersistedSizingState", reconcile)
        self.assertIn("expected_lots", reconcile)
        for field in (
            "fixedLot",
            "positionSizingMode",
            "riskPercent",
            "riskCapitalBase",
            "estimatedCommissionPerLot",
            "riskCapitalAmount",
            "estimatedRiskMoney",
        ):
            self.assertIn(field, persisted)
            self.assertIn(field, ack)
        self.assertIn("expected_lots", execute)
        self.assertNotIn("FixedLot", execute)

    def test_fixed_mode_ignores_unused_risk_percent_and_ack_stays_schema_valid(self) -> None:
        validate = named_block(
            self.code,
            r"\bbool\s+ValidateMoneyManagementConfiguration\s*\([^)]*\)",
        )
        self.assertRegex(
            validate,
            r"MoneyManagementMode\s*==\s*MONEY_MANAGEMENT_RISK_PERCENT[\s\S]*effective_risk_percent\s*<\s*0\.00000001",
        )
        ack = named_block(self.code, r"\bstring\s+BuildAckJson\s*\([^)]*\)")
        self.assertIn("g_ack_has_sizing_evidence ? g_ack_requested_lots : 0.0", ack)
        self.assertRegex(
            ack,
            r"g_ack_has_sizing_evidence\s*\?\s*g_ack_risk_percent\s*:\s*EffectiveRiskPercent\(\),\s*8",
        )
        self.assertIn("estimatedCommissionPerLot", ack)
        self.assertIn("g_ack_estimated_commission_per_lot", ack)
        self.assertIn("JsonNumber(g_ack_risk_capital_amount, 8)", ack)
        self.assertIn("JsonNumber(g_ack_estimated_risk_money, 8)", ack)

    def test_live_commission_policy_is_explicit_and_precision_safe(self) -> None:
        self.assertIn("input bool CommissionFreeAccountConfirmed = false;", self.code)
        self.assertIn(
            "Conservative round-trip commission for 1.0 lot in native account currency.",
            UNIFIED_EA_PATH.read_text(encoding="utf-8"),
        )
        effective = named_block(
            self.code,
            r"\bdouble\s+EffectiveEstimatedCommissionPerLot\s*\([^)]*\)",
        )
        self.assertIn("NormalizeDouble(EstimatedCommissionPerLot, 8)", effective)
        policy = named_block(
            self.code,
            r"\bbool\s+LiveCommissionPolicyConfirmed\s*\([^)]*\)",
        )
        self.assertIn("EffectiveEstimatedCommissionPerLot() >= 0.00000001", policy)
        self.assertIn("CommissionFreeAccountConfirmed", policy)
        validate = named_block(
            self.code,
            r"\bbool\s+ValidateMoneyManagementConfiguration\s*\([^)]*\)",
        )
        self.assertIn("GatewayMode == GATEWAY_LIVE", validate)
        self.assertIn("LIVE_COMMISSION_POLICY_UNCONFIRMED", validate)
        capabilities = named_block(
            self.code,
            r"\bstring\s+BuildCapabilitiesJson\s*\([^)]*\)",
        )
        self.assertIn("LiveCommissionPolicyConfirmed", capabilities)
        self.assertIn("LIVE_COMMISSION_POLICY_UNCONFIRMED", capabilities)
        estimate = named_block(
            self.code,
            r"\bbool\s+EstimateStopLossMoneyAtEntry\s*\([^)]*\)",
        )
        self.assertIn("EffectiveEstimatedCommissionPerLot()", estimate)

    def test_effective_risk_percent_is_identical_for_sizing_persistence_and_ack(self) -> None:
        effective = named_block(
            self.code,
            r"\bdouble\s+EffectiveRiskPercent\s*\([^)]*\)",
        )
        resolve = named_block(
            self.code,
            r"\bbool\s+ResolvePositionSize\s*\([^)]*\)",
        )
        final_guard = named_block(
            self.code,
            r"\bbool\s+ValidateRiskEnvelopeAtEntry\s*\([^)]*\)",
        )
        process = named_block(
            self.code,
            r"\bvoid\s+ProcessCommandFile\s*\([^)]*\)",
        )
        self.assertIn("NormalizeDouble(RiskPercent, 8)", effective)
        self.assertIn("EffectiveRiskPercent()", resolve)
        self.assertIn("EffectiveRiskPercent()", final_guard)
        self.assertIn("EffectiveRiskPercent()", process)

    def test_final_risk_guard_uses_current_risk_budget_and_exact_submitted_quote(self) -> None:
        guard = named_block(
            self.code,
            r"\bbool\s+ValidateRiskEnvelopeAtEntry\s*\([^)]*\)",
        )
        self.assertIn("EstimateStopLossMoneyAtEntry", guard)
        self.assertIn("risk_capital * EffectiveRiskPercent() / 100.0", guard)
        self.assertIn("persisted_risk_budget", guard)
        self.assertIn("MathMin(risk_budget, persisted_risk_budget)", guard)
        self.assertIn("final_estimated_risk_money = loss_money", guard)
        self.assertIn("RISK_PERCENT_BUDGET_EXCEEDED", guard)
        execute = named_block(self.code, r"\bvoid\s+ExecuteCommand\s*\([^)]*\)")
        capture = "price = order_type == OP_BUY ? Ask : Bid"
        validate = "ValidateRiskEnvelopeAtEntry"
        send = "OrderSend"
        self.assertLess(execute.find(capture), execute.find(validate))
        self.assertLess(execute.find(validate), execute.find(send))
        between_capture_and_send = execute[
            execute.find(capture) : execute.find(send)
        ]
        self.assertEqual(between_capture_and_send.count("RefreshRates"), 0)

        final_assignment = execute.find(
            "g_ack_estimated_risk_money = final_estimated_risk_money"
        )
        final_payload = execute.find('"FINAL_RISK_VALIDATED"')
        final_marker = execute.find(
            "WriteExecutionMarkers(command, final_executing_payload)"
        )
        bar_claim = execute.find("WriteLastOrderBar(command.bar_time)")
        self.assertGreater(final_assignment, execute.find(validate))
        self.assertGreater(final_payload, final_assignment)
        self.assertGreater(final_marker, final_payload)
        self.assertGreater(bar_claim, final_marker)
        self.assertGreater(execute.find(send), bar_claim)
        self.assertIn("FINAL_RISK_STATE_WRITE_FAILED", execute)

    def test_restart_order_identity_requires_exact_persisted_volume(self) -> None:
        evidence = named_block(
            self.code,
            r"\bbool\s+CaptureSelectedOrderEvidence\s*\([^)]*\)",
        )
        self.assertIn("double lot_tolerance = 0.00000001", evidence)
        self.assertNotIn("MODE_LOTSTEP) / 2.0", evidence)

    def test_broker_affix_allowlist_still_requires_exact_attached_command_symbol(self) -> None:
        matcher = named_block(
            self.code,
            r"\bbool\s+IsAllowedBrokerSymbol\s*\([^)]*\)",
        )
        self.assertIn("base_length < 6", matcher)
        self.assertIn("HasSingleBrokerBaseOccurrence", matcher)
        self.assertIn("prefix_length <= 8", matcher)
        self.assertIn("suffix_length > 8", matcher)
        self.assertIn("IsBrokerSuffixCharacter", matcher)
        self.assertIn("IsAllowedBrokerPrefix", matcher)
        suffix_character = named_block(
            self.code,
            r"\bbool\s+IsBrokerSuffixCharacter\s*\([^)]*\)",
        )
        self.assertIn("code == '#'", suffix_character)
        self.assertNotIn("code == '+'", suffix_character)
        namespace_delimiter = named_block(
            self.code,
            r"\bbool\s+IsBrokerNamespaceDelimiter\s*\([^)]*\)",
        )
        self.assertIn("code == '.'", namespace_delimiter)
        prefix_policy = named_block(
            self.code,
            r"\bbool\s+IsAllowedBrokerPrefix\s*\([^)]*\)",
        )
        self.assertIn("prefix_length == 1", prefix_policy)
        self.assertIn("IsBrokerNamespaceDelimiter", prefix_policy)
        single_occurrence = named_block(
            self.code,
            r"\bbool\s+HasSingleBrokerBaseOccurrence\s*\([^)]*\)",
        )
        self.assertIn("StringFind(candidate, allowed)", single_occurrence)
        self.assertIn("StringFind(candidate, allowed, first + 1)", single_occurrence)
        runtime = named_block(self.code, r"\bbool\s+ValidateRuntime\s*\([^)]*\)")
        self.assertIn("IsAllowedBrokerSymbol(AllowedSymbols, command.symbol)", runtime)
        self.assertIn("CsvContains(AllowedSymbols, command.symbol)", runtime)
        self.assertIn("LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST", runtime)
        self.assertIn("Uppercase(Symbol()) != command.symbol", runtime)
        execute = named_block(self.code, r"\bvoid\s+ExecuteCommand\s*\([^)]*\)")
        self.assertRegex(execute, r"OrderSend\s*\(\s*Symbol\s*\(\s*\)")
        on_init = named_block(self.code, r"\bint\s+OnInit\s*\([^)]*\)")
        self.assertIn("IsAllowedBrokerSymbol(AllowedSymbols, Symbol())", on_init)
        self.assertIn("LiveSymbolExactAllowlistConfirmed()", on_init)
        self.assertIn("LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST", on_init)
        exact_live = named_block(
            self.code,
            r"\bbool\s+LiveSymbolExactAllowlistConfirmed\s*\([^)]*\)",
        )
        self.assertIn("CsvContains(AllowedSymbols, Symbol())", exact_live)

        accepted = (
            "XAUUSD",
            "XAUUSD.m",
            "XAUUSD#",
            "XAUUSDpro",
            "mXAUUSD",
            "GOLD.XAUUSD",
            "mXAUUSD.pro",
        )
        rejected = (
            "XAUUSD+",
            "123456789XAUUSD",
            "XAUUSD123456789",
            "XAUUSDXAUUSD",
            "mXAUUSDXAUUSD.pro",
            "FOOXAUUSD",
            "GOLDXAUUSD",
            "EURUSD",
        )
        for symbol in accepted:
            with self.subTest(accepted=symbol):
                self.assertTrue(broker_symbol_match_model("XAUUSD", symbol))
        for symbol in rejected:
            with self.subTest(rejected=symbol):
                self.assertFalse(broker_symbol_match_model("XAUUSD", symbol))

    def test_command_identity_matches_backend_comment_and_replay_contract(self) -> None:
        runtime = named_block(self.code, r"\bbool\s+ValidateRuntime\s*\([^)]*\)")
        for validator in (
            "IsCommandIdentifier",
            "IsIdempotencyIdentifier",
            "IsHeartbeatIdentifier",
        ):
            self.assertIn(validator, runtime)
        command_id = named_block(
            self.code,
            r"\bbool\s+IsCommandIdentifier\s*\([^)]*\)",
        )
        self.assertIn('StringSubstr(value, 0, 4) == "cmd-"', command_id)
        self.assertIn("IsLowerHexIdentifierPart(value, 4, 24)", command_id)

    def test_stop_validation_uses_normalized_exit_side_prices(self) -> None:
        stops = named_block(self.code, r"\bbool\s+ValidateStops\s*\([^)]*\)")
        self.assertIn("NormalizeSymbolPrice(command.stop_loss)", stops)
        self.assertIn("NormalizeSymbolPrice(command.take_profit)", stops)
        self.assertRegex(stops, r"stop_loss\s*>=\s*Bid\s*\|\|\s*take_profit\s*<=\s*Ask")
        self.assertRegex(stops, r"stop_loss\s*<=\s*Ask\s*\|\|\s*take_profit\s*>=\s*Bid")
        self.assertIn("MODE_STOPLEVEL", stops)

    def test_bar_claim_happens_after_final_mutable_guards_but_before_ordersend(self) -> None:
        execute = named_block(self.code, r"\bvoid\s+ExecuteCommand\s*\([^)]*\)")
        claim = execute.rfind("WriteLastOrderBar(command.bar_time)")
        order_send = execute.find("OrderSend")
        self.assertGreater(claim, execute.rfind("ValidateMarginPreflight"))
        self.assertGreater(claim, execute.rfind("ReverifyCommandEnvelope"))
        self.assertLess(claim, order_send)

    def test_bar_claim_state_is_scoped_to_exact_channel_symbol_and_timeframe(self) -> None:
        path = named_block(self.code, r"\bstring\s+LastOrderBarPath\s*\([^)]*\)")
        read = named_block(self.code, r"\bbool\s+ReadLastOrderBar\s*\([^)]*\)")
        write = named_block(self.code, r"\bbool\s+WriteLastOrderBar\s*\([^)]*\)")
        migrate = named_block(
            self.code,
            r"\bbool\s+MigrateLegacyLastOrderBarState\s*\([^)]*\)",
        )
        self.assertIn("BasePath", path)
        self.assertIn("Uppercase(Symbol())", path)
        self.assertIn("CurrentTimeframeName", path)
        for token in ("SnapshotChannel", "Uppercase(Symbol())", "CurrentTimeframeName"):
            self.assertIn(token, read)
            self.assertIn(token, write)
        self.assertIn("FileIsExist", read)
        self.assertLess(migrate.find("WriteLastOrderBar"), migrate.find("FileDelete"))

    def test_account_execution_lock_wraps_mutable_guards_claim_and_ordersend(self) -> None:
        path = named_block(
            self.code,
            r"\bbool\s+AccountExecutionLockPath\s*\([^)]*\)",
        )
        identity = named_block(
            self.code,
            r"\bbool\s+AccountIdentityDigest\s*\([^)]*\)",
        )
        acquire = named_block(
            self.code,
            r"\bbool\s+AcquireAccountExecutionLock\s*\([^)]*\)",
        )
        execute = named_block(self.code, r"\bvoid\s+ExecuteCommand\s*\([^)]*\)")
        self.assertIn("AccountIdentityDigest", path)
        self.assertIn("AccountNumber", identity)
        self.assertIn("AccountServer", identity)
        self.assertIn("Uppercase(Trimmed(AccountServer()))", identity)
        self.assertIn("Sha256Bytes", identity)
        self.assertIn("FILE_SHARE_READ", acquire)
        self.assertNotIn("FILE_SHARE_WRITE", acquire)
        lock = execute.find("AcquireAccountExecutionLock")
        self.assertGreater(lock, 0)
        self.assertLess(lock, execute.rfind("ValidateRuntime"))
        self.assertLess(lock, execute.rfind("WriteLastOrderBar"))
        self.assertLess(lock, execute.find("OrderSend"))
        self.assertGreater(execute.find("ReleaseAccountExecutionLock"), execute.find("OrderSend"))

    def test_account_portfolio_policy_is_normalized_leased_and_fail_closed(self) -> None:
        normalize = named_block(
            self.code,
            r"\bbool\s+NormalizedManagedMagicNumbers\s*\([^)]*\)",
        )
        policy = named_block(
            self.code,
            r"\bbool\s+BuildPortfolioPolicyCanonical\s*\([^)]*\)",
        )
        acquire = named_block(
            self.code,
            r"\bbool\s+AcquirePortfolioPolicyLease\s*\([^)]*\)",
        )
        inspect = named_block(
            self.code,
            r"\bbool\s+InspectPortfolioPolicyLeases\s*\([^)]*\)",
        )
        parse = named_block(
            self.code,
            r"\bbool\s+ParsePortfolioPolicyLeaseEvidence\s*\([^)]*\)",
        )
        release = named_block(
            self.code,
            r"\bvoid\s+ReleasePortfolioPolicyLease\s*\([^)]*\)",
        )
        directory = named_block(
            self.code,
            r"\bbool\s+AccountPortfolioPolicyDirectoryPath\s*\([^)]*\)",
        )
        self.assertIn("values[right] < values[left]", normalize)
        self.assertIn("values[sorted_index] == values[sorted_index - 1]", normalize)
        for field in (
            "managedMagicNumbers",
            "positionSizingMode",
            "riskPercent",
            "riskCapitalBase",
            "commissionFreeAccountConfirmed",
            "maxManagedOpenPositions",
            "maxManagedTotalLots",
            "estimatedCommissionPerLot",
            "maxTradesPerBrokerDay",
            "maxDailyLossPercent",
            "maxManagedWeeklyLossPercent",
            "maxConsecutiveManagedLosses",
            "consecutiveLossCooldownMinutes",
            "maxAccountEquityDrawdownPercent",
        ):
            self.assertIn(field, policy)
        mt5_policy = named_block(
            MT5_GATEWAY_PATH.read_text(encoding="utf-8"),
            r"\bbool\s+BuildPortfolioPolicyCanonical\s*\([^)]*\)",
        )
        policy_fields = re.findall(r'canonical\s*\+=\s*"\|([^=]+)=', policy)
        mt5_policy_fields = re.findall(
            r'canonical\s*\+=\s*"\|([^=]+)=', mt5_policy
        )
        self.assertEqual(
            policy_fields,
            [
                "managedMagicNumbers",
                "positionSizingMode",
                "riskPercent",
                "riskCapitalBase",
                "estimatedCommissionPerLot",
                "commissionFreeAccountConfirmed",
                "maxManagedOpenPositions",
                "maxManagedTotalLots",
                "maxTradesPerBrokerDay",
                "maxDailyLossPercent",
                "maxManagedWeeklyLossPercent",
                "maxConsecutiveManagedLosses",
                "consecutiveLossCooldownMinutes",
                "maxAccountEquityDrawdownPercent",
            ],
        )
        self.assertEqual(policy_fields, mt5_policy_fields)
        self.assertIn("Sha256TextHex", policy)
        self.assertIn("AccountIdentityDigest", directory)
        self.assertNotIn("SnapshotChannel", directory)
        self.assertIn("InspectPortfolioPolicyLeases", acquire)
        self.assertIn("FileFindFirst", inspect)
        self.assertIn('directory + "\\\\*"', inspect)
        self.assertIn("find_next_error != 0", inspect)
        self.assertIn("g_portfolio_policy_lease_scan_error", inspect)
        self.assertIn("PORTFOLIO_POLICY_MISMATCH", inspect)
        self.assertIn("active_policy_digest != expected_policy_digest", inspect)
        self.assertIn("active_lease_count > 0", acquire)
        self.assertIn("scan-anchor-v1.txt", acquire)
        self.assertLess(
            inspect.find("int stale_handle = FileOpen"),
            inspect.find("ReadCommonText(lease_path, 512, raw)"),
        )
        self.assertIn("WriteCommonTextAtomic(policy_path, canonical)", acquire)
        self.assertIn("FILE_SHARE_READ", acquire)
        self.assertNotIn("FILE_SHARE_WRITE", acquire)
        self.assertIn("ReadCommonText(lease_path, 512, raw)", inspect)
        self.assertIn("ParsePortfolioPolicyLeaseEvidence", inspect)
        self.assertIn("MetafxHQPortfolioPolicyV2", parse)
        self.assertIn("expected_account_digest", parse)
        self.assertIn("legacy_policy_digest", parse)
        self.assertIn("legacy_channel_digest", parse)
        self.assertIn("PORTFOLIO_POLICY_STATE_INVALID", inspect)
        self.assertIn("FileClose(g_portfolio_policy_lease_handle)", release)
        self.assertIn("FileDelete(lease_path, FILE_COMMON)", release)

        on_init = named_block(self.code, r"\bint\s+OnInit\s*\([^)]*\)")
        account_lock = on_init.find("AcquireAccountExecutionLock")
        policy_lease = on_init.find("AcquirePortfolioPolicyLease")
        account_unlock = on_init.find("ReleaseAccountExecutionLock", policy_lease)
        self.assertLess(account_lock, policy_lease)
        self.assertLess(policy_lease, account_unlock)
        self.assertIn('"portfolio_policy"', on_init)
        self.assertIn("ReleasePortfolioPolicyLease", on_init)
        on_deinit = named_block(self.code, r"\bvoid\s+OnDeinit\s*\([^)]*\)")
        self.assertIn("ReleasePortfolioPolicyLease", on_deinit)

    def test_portfolio_policy_lease_path_is_bounded_and_payload_authoritative(self) -> None:
        path = named_block(
            self.code,
            r"\bbool\s+AccountPortfolioPolicyLeasePath\s*\([^)]*\)",
        )
        expanded = named_block(
            self.code,
            r"\bint\s+CommonFilesExpandedPathLength\s*\([^)]*\)",
        )
        parse = named_block(
            self.code,
            r"\bbool\s+ParsePortfolioPolicyLeaseEvidence\s*\([^)]*\)",
        )
        acquire = named_block(
            self.code,
            r"\bbool\s+AcquirePortfolioPolicyLease\s*\([^)]*\)",
        )
        diagnostic = named_block(
            self.code,
            r"\bbool\s+RecordInitDiagnostic\s*\([^)]*\)",
        )

        self.assertIn('"\\\\policy-p-"', path)
        self.assertIn('"-c-"', path)
        self.assertIn("PORTFOLIO_POLICY_PREFIX_HEX_LENGTH", path)
        self.assertNotIn('"-channel-"', path)
        self.assertIn("TERMINAL_COMMONDATA_PATH", expanded)
        self.assertIn('StringLen("\\\\Files\\\\")', expanded)
        self.assertIn("PORTFOLIO_POLICY_MAX_EXPANDED_PATH_LENGTH", acquire)
        self.assertIn("MetafxHQPortfolioPolicyV2", acquire)
        self.assertIn("account_digest", acquire)
        self.assertIn("expected_digest", acquire)
        self.assertIn("channel_digest", acquire)
        self.assertIn("SnapshotChannel", acquire)
        self.assertIn("GetLastError", acquire)
        self.assertIn("portfolioPolicyLeaseOpenErrorCode", diagnostic)
        self.assertIn("portfolioPolicyLeaseScanErrorCode", diagnostic)
        self.assertIn("portfolioPolicyLeaseExpandedPathLength", diagnostic)
        self.assertIn("portfolioPolicyLeaseMaxPathLength", diagnostic)

        # The prefixes select only a slot. Full account/policy/channel SHA-256
        # values in the bounded V2 payload are the evidence that is validated.
        self.assertIn("parts[1] != expected_account_digest", parse)
        self.assertIn("parts[2]", parse)
        self.assertIn("parts[3]", parse)
        self.assertIn("IsSafeChannel(parts[4])", parse)
        self.assertIn("Sha256TextHex(parts[4], observed_channel_digest)", parse)
        self.assertIn("observed_channel_digest != parts[3]", parse)
        self.assertIn("policy_digest = parts[2]", parse)
        self.assertIn("channel_digest = observed_channel_digest", parse)

        common_files_prefix = (
            "C:\\Users\\META\\AppData\\Roaming\\MetaQuotes\\Terminal\\Common\\Files\\"
        )
        account_directory = "MetafxHQ\\account-policies\\" + "a" * 64
        compact_name = "policy-p-" + "b" * 16 + "-c-" + "c" * 16 + ".lease"
        legacy_name = "policy-" + "b" * 64 + "-channel-" + "c" * 64 + ".lease"
        compact_expanded_length = len(
            common_files_prefix + account_directory + "\\" + compact_name
        )
        legacy_expanded_length = len(
            common_files_prefix + account_directory + "\\" + legacy_name
        )
        self.assertEqual(len(compact_name), 50)
        self.assertEqual(compact_expanded_length, 204)
        self.assertLessEqual(compact_expanded_length, 259)
        self.assertGreater(legacy_expanded_length, 259)

        compact_pattern = re.compile(
            r"^policy-p-([0-9a-f]{16})-c-([0-9a-f]{16})\.lease$"
        )
        legacy_pattern = re.compile(
            r"^policy-([0-9a-f]{64})-channel-([0-9a-f]{64})\.lease$"
        )
        self.assertIsNotNone(compact_pattern.fullmatch(compact_name))
        self.assertIsNotNone(legacy_pattern.fullmatch(legacy_name))
        self.assertIsNone(compact_pattern.fullmatch("policy-p-bad-c-bad.lease"))
        self.assertIsNone(legacy_pattern.fullmatch(compact_name))

    def test_compact_lease_full_digest_mismatch_fails_closed_despite_same_prefix(self) -> None:
        account_digest = "a" * 64
        expected_policy = "b" * 64
        conflicting_policy = "b" * 16 + "d" * 48
        channel = "mtc-model-prefix-collision"
        digest = snapshot_channel_digest(channel)
        self.assertEqual(
            compact_policy_lease_name(expected_policy, digest),
            compact_policy_lease_name(conflicting_policy, digest),
        )
        reason, active_count = inspect_policy_leases_model(
            [
                {
                    "name": compact_policy_lease_name(
                        conflicting_policy, digest
                    ),
                    "payload": compact_policy_lease_payload(
                        account_digest, conflicting_policy, channel
                    ),
                    "active": True,
                }
            ],
            account_digest,
            expected_policy,
        )
        self.assertEqual(reason, "PORTFOLIO_POLICY_MISMATCH")
        self.assertEqual(active_count, 1)

    def test_corrupt_or_unreadable_active_compact_lease_is_state_invalid(self) -> None:
        account_digest = "a" * 64
        policy_digest = "b" * 64
        channel = "mtc-model-corrupt"
        digest = snapshot_channel_digest(channel)
        name = compact_policy_lease_name(policy_digest, digest)
        corrupt_reason, _ = inspect_policy_leases_model(
            [{"name": name, "payload": "corrupt", "active": True}],
            account_digest,
            policy_digest,
        )
        unreadable_reason, _ = inspect_policy_leases_model(
            [
                {
                    "name": name,
                    "payload": compact_policy_lease_payload(
                        account_digest, policy_digest, channel
                    ),
                    "active": True,
                    "readable": False,
                }
            ],
            account_digest,
            policy_digest,
        )
        self.assertEqual(corrupt_reason, "PORTFOLIO_POLICY_STATE_INVALID")
        self.assertEqual(unreadable_reason, "PORTFOLIO_POLICY_STATE_INVALID")

    def test_empty_or_partial_stale_compact_lease_is_cleaned_before_parse(self) -> None:
        account_digest = "a" * 64
        policy_digest = "b" * 64
        channel = "mtc-model-stale-crash"
        name = compact_policy_lease_name(
            policy_digest, snapshot_channel_digest(channel)
        )
        reason, active_count = inspect_policy_leases_model(
            [
                {"name": name, "payload": "", "active": False},
                {"name": name, "payload": "MetafxHQPortfolio", "active": False},
            ],
            account_digest,
            policy_digest,
        )
        self.assertEqual(reason, "READY")
        self.assertEqual(active_count, 0)

    def test_compact_lease_rejects_channel_digest_tail_only_corruption(self) -> None:
        account_digest = "a" * 64
        policy_digest = "b" * 64
        channel = "mtc-model-tail-corruption"
        digest = snapshot_channel_digest(channel)
        name = compact_policy_lease_name(policy_digest, digest)
        payload_parts = compact_policy_lease_payload(
            account_digest, policy_digest, channel
        ).split("|")
        payload_parts[3] = payload_parts[3][:16] + (
            "0" if payload_parts[3][16] != "0" else "1"
        ) + payload_parts[3][17:]
        self.assertEqual(payload_parts[3][:16], digest[:16])
        self.assertNotEqual(payload_parts[3], digest)

        reason, active_count = inspect_policy_leases_model(
            [{"name": name, "payload": "|".join(payload_parts), "active": True}],
            account_digest,
            policy_digest,
        )
        self.assertEqual(reason, "PORTFOLIO_POLICY_STATE_INVALID")
        self.assertEqual(active_count, 0)

    def test_compact_lease_enumeration_errors_fail_closed(self) -> None:
        account_digest = "a" * 64
        policy_digest = "b" * 64
        channel = "mtc-model-enumeration"
        digest = snapshot_channel_digest(channel)
        record = {
            "name": compact_policy_lease_name(policy_digest, digest),
            "payload": compact_policy_lease_payload(
                account_digest, policy_digest, channel
            ),
            "active": True,
        }
        first_reason, first_count = inspect_policy_leases_model(
            [],
            account_digest,
            policy_digest,
            first_scan_error=True,
        )
        next_reason, next_count = inspect_policy_leases_model(
            [record],
            account_digest,
            policy_digest,
            next_scan_error_at=0,
        )
        self.assertEqual(first_reason, "PORTFOLIO_POLICY_STATE_INVALID")
        self.assertEqual(first_count, 0)
        self.assertEqual(next_reason, "PORTFOLIO_POLICY_STATE_INVALID")
        self.assertEqual(next_count, 1)

    def test_two_channels_with_same_full_policy_coexist_and_current_path_is_bounded(self) -> None:
        account_digest = "a" * 64
        policy_digest = "b" * 64
        channel_one = "mtc-model-channel-one"
        channel_two = "mtc-model-channel-two"
        records = [
            {
                "name": compact_policy_lease_name(
                    policy_digest, snapshot_channel_digest(channel)
                ),
                "payload": compact_policy_lease_payload(
                    account_digest, policy_digest, channel
                ),
                "active": True,
            }
            for channel in (channel_one, channel_two)
        ]
        self.assertNotEqual(records[0]["name"], records[1]["name"])
        reason, active_count = inspect_policy_leases_model(
            records, account_digest, policy_digest
        )
        self.assertEqual(reason, "READY")
        self.assertEqual(active_count, 2)

        current_common_files = (
            "C:\\Users\\META\\AppData\\Roaming\\MetaQuotes\\Terminal\\Common\\Files"
        )
        current_relative_path = (
            "MetafxHQ\\account-policies\\"
            + account_digest
            + "\\"
            + str(records[0]["name"])
        )
        current_expanded_path = current_common_files + "\\" + current_relative_path
        self.assertEqual(len(current_expanded_path), 204)
        self.assertLess(len(current_expanded_path), 260)

    def test_outcome_and_history_recovery_are_isolated_to_exact_channel(self) -> None:
        resolve = named_block(
            self.code,
            r"\bbool\s+ResolveSelectedOrderCommandId\s*\([^)]*\)",
        )
        outcome = named_block(
            self.code,
            r"\bbool\s+WriteSelectedOrderOutcome\s*\([^)]*\)",
        )
        refresh = named_block(
            self.code,
            r"\bvoid\s+RefreshManagedOutcomeFiles\s*\([^)]*\)",
        )
        legacy = named_block(
            self.code,
            r"\bbool\s+ParseLegacyExecutedAck\s*\([^)]*\)",
        )
        self.assertGreaterEqual(resolve.count("CurrentChannelOwnsCommandId"), 2)
        self.assertIn("CurrentChannelOwnsCommandId", outcome)
        self.assertIn("IsManagedMarketOrderSelected", refresh)
        self.assertNotIn("OrderMagicNumber() != MagicNumber", refresh)
        self.assertIn("IsManagedMagic(ack.magic_number)", legacy)

    def test_chart_transition_invalidates_old_runtime_before_unlocking_channel(self) -> None:
        on_init = named_block(self.code, r"\bint\s+OnInit\s*\([^)]*\)")
        on_deinit = named_block(self.code, r"\bvoid\s+OnDeinit\s*\([^)]*\)")
        invalidate = named_block(
            self.code,
            r"\bvoid\s+InvalidatePublishedRuntimeState\s*\([^)]*\)",
        )
        for token in ("StatusPath", "CapabilitiesPath", "SnapshotPath"):
            self.assertIn(token, invalidate)
        self.assertGreater(on_init.find("InvalidatePublishedRuntimeState"), on_init.find("AcquireChannelLock"))
        self.assertLess(on_deinit.find("InvalidatePublishedRuntimeState"), on_deinit.find("ReleaseChannelLock"))

    def test_duplicate_command_does_not_overwrite_original_idempotency_ledger(self) -> None:
        duplicate = named_block(self.code, r"\bvoid\s+WriteDuplicateAck\s*\([^)]*\)")
        self.assertIn("CommandLedgerPath(command.command_id)", duplicate)
        self.assertNotIn("IdempotencyLedgerPath", duplicate)
        self.assertNotIn("WriteExecutionMarkers", duplicate)

    def test_quote_market_and_deinit_diagnostics_are_fail_closed(self) -> None:
        quote = named_block(self.code, r"\bbool\s+ValidateQuoteFreshness\s*\([^)]*\)")
        self.assertIn("MODE_TIME", quote)
        self.assertIn("BROKER_QUOTE_TIME_STALE", quote)
        margin = named_block(self.code, r"\bbool\s+ValidateMarginPreflight\s*\([^)]*\)")
        self.assertIn("IsTradeAllowed(Symbol(), broker_time)", margin)
        self.assertIn("BROKER_SESSION_OR_SYMBOL_CLOSED", margin)
        deinit = named_block(self.code, r"\bvoid\s+OnDeinit\s*\([^)]*\)")
        self.assertIn("RecordInitDiagnostic", deinit)
        self.assertIn("GATEWAY_STOPPED_", deinit)


if __name__ == "__main__":
    unittest.main()
