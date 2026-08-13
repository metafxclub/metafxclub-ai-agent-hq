from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UNIFIED_EA_PATH = (
    PROJECT_ROOT
    / "integrations"
    / "mt4-trade-gateway"
    / "MetafxHQTradeGateway.mq4"
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
            r"\binput\s+double\s+FixedLot\s*=\s*[0-9.]+\s*;",
        )
        command_fields = named_block(self.code, r"\bstruct\s+CommandPayload\b")
        self.assertTrue(command_fields, "CommandPayload must be present")
        self.assertIsNone(
            re.search(r"(?i)\b(?:lot|volume|risk_percent|risk_pct|risk_amount)\b", command_fields),
            "AI command payload must not own lot or risk sizing",
        )
        self.assertRegex(
            self.code,
            r"OrderSend\s*\([^;]*?\bFixedLot\b[^;]*?\)",
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
        self.assertIn("AccountFreeMarginCheck", self.code)
        self.assertIn("MODE_MARGINREQUIRED", self.code)

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
        process = named_block(self.code, r"\bvoid\s+ProcessCommandFile\s*\([^)]*\)")
        self.assertIn("OrderMagicNumber", finder)
        self.assertIn("IsManagedMagic(OrderMagicNumber())", finder)
        self.assertNotIn("OrderMagicNumber() == MagicNumber", finder)
        self.assertIn("OrderComment", finder)
        self.assertIn("CurrentChannelOwnsCommandId(command.command_id)", finder)
        self.assertIn("RECOVERED_ORDER_FOUND", reconcile)
        self.assertIn("EXECUTION_UNKNOWN", reconcile)
        self.assertIn("RESTART_RECONCILIATION_REQUIRED", reconcile)
        self.assertIn('processed_status == "EXECUTING"', process)
        self.assertNotIn("OrderSend", reconcile)

    def test_portfolio_guards_cover_managed_magic_numbers_account_wide(self) -> None:
        self.assertRegex(
            self.code,
            r'input\s+string\s+ManagedMagicNumbers\s*=\s*"4186001"\s*;',
        )
        managed = named_block(self.code, r"\bvoid\s+ReadManagedOpenState\s*\([^)]*\)")
        daily = named_block(self.code, r"\bdouble\s+ManagedDailyPnl\s*\([^)]*\)")
        weekly = named_block(self.code, r"\bdouble\s+ManagedWeeklyPnl\s*\([^)]*\)")
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

    def test_broker_order_time_arithmetic_stays_in_the_broker_clock_domain(self) -> None:
        loss_streak = named_block(
            self.code,
            r"\bvoid\s+ReadManagedLossStreak\s*\([^)]*\)",
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
        self.assertIn("LIFECYCLE_SLTP_ONLY", lifecycle)
        self.assertIn("LifecycleAttemptPath", lifecycle)
        self.assertIn("automaticRetry", lifecycle)
        self.assertIn("LiveArmed", lifecycle)

    def test_order_send_is_verified_and_outcomes_are_refreshed(self) -> None:
        execute = named_block(self.code, r"\bvoid\s+ExecuteCommand\s*\([^)]*\)")
        verify = named_block(self.code, r"\bbool\s+CaptureSelectedOrderEvidence\s*\([^)]*\)")
        ack = named_block(self.code, r"\bstring\s+BuildAckJson\s*\([^)]*\)")
        self.assertGreater(execute.find("CaptureSelectedOrderEvidence"), execute.find("OrderSend"))
        self.assertIn("OrderSelect", verify)
        for token in (
            "OrderOpenPrice",
            "SlippagePoints",
            "slippage_within_limit",
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
        self.assertIn("ORDER_ACCEPTED_WITH_SLIPPAGE_WARNING", verify)
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
        self.assertIn("!demo_account && signed_ready && explicit_live_pin && LiveArmed", capabilities)

    def test_optional_demo_pin_is_normalized_but_live_remains_fail_closed(self) -> None:
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
        self.assertEqual(malformed_pin.count("InitFailure"), 1)
        self.assertIn("LIVE_SIGNING_KEY_PIN_INVALID", malformed_pin)
        self.assertIn('g_trusted_signing_key_id = ""', malformed_pin)
        self.assertIn("OPTIONAL_SIGNING_KEY_PIN_INVALID_IGNORED", malformed_pin)
        self.assertIn("OPTIONAL_SIGNING_KEY_PIN_MISMATCH_IGNORED", on_init)
        self.assertIn("GatewayMode != GATEWAY_LIVE", on_init)

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
        self.assertIn("IsDemo()", account_mode)
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
            r"live_ready\s*=\s*GatewayMode\s*==\s*GATEWAY_LIVE\s*&&\s*!demo_account\s*&&\s*signed_ready\s*&&\s*explicit_live_pin\s*&&\s*LiveArmed",
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
        self.assertIn("ExecuteCommand(command, raw)", process)

    def test_demo_and_live_share_signed_ordersend_path_and_ack_v3(self) -> None:
        execute = named_block(self.code, r"\bvoid\s+ExecuteCommand\s*\([^)]*\)")
        self.assertGreaterEqual(execute.count("ReverifyCommandEnvelope"), 2)
        self.assertEqual(execute.count("OrderSend"), 1)
        self.assertNotRegex(execute, r"GATEWAY_DEMO[^}]*OrderSend")
        ack = named_block(self.code, r"\bstring\s+BuildAckJson\s*\([^)]*\)")
        self.assertIn("signatureVerificationStatus", ack)
        self.assertIn("metafx-hq-mt4-ack-v3", self.code)
        self.assertIn('version   "2.16"', self.code)
        self.assertIn('EA_VERSION = "2.16"', self.code)
        self.assertIn("JsonNumber(command.reference_price, 8)", ack)

    def test_risk_estimate_normalizes_broker_tick_size_without_point_double_count(self) -> None:
        estimate = named_block(self.code, r"\bbool\s+EstimateStopLossMoney\s*\([^)]*\)")
        self.assertIn("tick_size_raw < 1.0", estimate)
        self.assertIn("tick_size_raw * point", estimate)
        self.assertNotIn("tick_size_points * point", estimate)
        self.assertIn("risk_distance / tick_size_price * tick_value * FixedLot", estimate)

    def test_broker_suffix_allowlist_still_requires_exact_attached_command_symbol(self) -> None:
        matcher = named_block(
            self.code,
            r"\bbool\s+IsAllowedBrokerSymbol\s*\([^)]*\)",
        )
        self.assertIn("base_length < 6", matcher)
        self.assertIn("suffix_length > 8", matcher)
        self.assertIn("IsBrokerSuffixCharacter", matcher)
        suffix_character = named_block(
            self.code,
            r"\bbool\s+IsBrokerSuffixCharacter\s*\([^)]*\)",
        )
        self.assertIn("code == '#'", suffix_character)
        self.assertNotIn("code == '+'", suffix_character)
        runtime = named_block(self.code, r"\bbool\s+ValidateRuntime\s*\([^)]*\)")
        self.assertIn("IsAllowedBrokerSymbol(AllowedSymbols, command.symbol)", runtime)
        self.assertIn("Uppercase(Symbol()) != command.symbol", runtime)
        execute = named_block(self.code, r"\bvoid\s+ExecuteCommand\s*\([^)]*\)")
        self.assertRegex(execute, r"OrderSend\s*\(\s*Symbol\s*\(\s*\)")
        on_init = named_block(self.code, r"\bint\s+OnInit\s*\([^)]*\)")
        self.assertIn("IsAllowedBrokerSymbol(AllowedSymbols, Symbol())", on_init)

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
            "maxManagedOpenPositions",
            "maxManagedTotalLots",
            "maxTradesPerBrokerDay",
            "maxDailyLossPercent",
            "maxManagedWeeklyLossPercent",
            "maxConsecutiveManagedLosses",
            "consecutiveLossCooldownMinutes",
            "maxAccountEquityDrawdownPercent",
        ):
            self.assertIn(field, policy)
        self.assertIn("Sha256TextHex", policy)
        self.assertIn("AccountIdentityDigest", directory)
        self.assertNotIn("SnapshotChannel", directory)
        self.assertIn("FileFindFirst", acquire)
        self.assertIn("PORTFOLIO_POLICY_MISMATCH", acquire)
        self.assertIn("active_digest != expected_digest", acquire)
        self.assertIn("active_lease_count > 0", acquire)
        self.assertIn("WriteCommonTextAtomic(policy_path, canonical)", acquire)
        self.assertIn("FILE_SHARE_READ", acquire)
        self.assertNotIn("FILE_SHARE_WRITE", acquire)
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
