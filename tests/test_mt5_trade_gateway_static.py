from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = (
    ROOT
    / "integrations"
    / "mt5-trade-gateway"
    / "MetafxHQTradeGateway.mq5"
)


def strip_mql_comments(source: str) -> str:
    without_blocks = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"//[^\r\n]*", "", without_blocks)


class Mt5TradeGatewayStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SOURCE_PATH.read_text(encoding="utf-8")
        cls.code = strip_mql_comments(cls.source)

    def test_safe_defaults_and_hedging_only_gate(self) -> None:
        self.assertIn("input ENUM_GATEWAY_MODE GatewayMode = GATEWAY_SHADOW;", self.code)
        self.assertIn("input bool LiveArmed = false;", self.code)
        self.assertIn("input bool SingleHostLiveAcknowledged = false;", self.code)
        self.assertIn("ACCOUNT_MARGIN_MODE_RETAIL_HEDGING", self.code)
        self.assertIn('"MT5_HEDGING_ACCOUNT_REQUIRED"', self.code)
        self.assertRegex(
            self.code,
            r"(?s)int\s+OnInit\s*\(\s*\).*?if\s*\(\s*!IsHedgingAccount\s*\(\s*\)\s*\).*?return\s+INIT_FAILED",
        )

    def test_legacy_schema_names_are_preserved_but_mt5_signature_is_bound(self) -> None:
        for token in (
            "metafx-hq-mt4-command-v2",
            "metafx-hq-mt4-heartbeat-v1",
            "metafx-hq-mt4-signed-envelope-v1",
            "metafx-hq-mt4-ack-v3",
            "metafx-hq-mt4-status-v5",
            "metafx-hq-mt4-snapshot-v1",
            "FILE_COMMON",
        ):
            self.assertIn(token, self.code)
        self.assertIn('"METAFXHQ|MT5|" + normalized_kind', self.code)
        self.assertIn("ProtocolAccountBindingId(account_binding_id)", self.code)
        self.assertIn(r'\"terminalPlatform\":\"mt5\"', self.code)
        self.assertIn(r'\"accountBindingId\":', self.code)
        self.assertNotIn("METAFXHQ|MT4|COMMAND", self.code)

    def test_no_mql4_trade_or_market_compatibility_api(self) -> None:
        forbidden = (
            "MarketInfo",
            "OrdersHistoryTotal",
            "OrderSelect",
            "OrderType",
            "OrderLots",
            "OrderMagicNumber",
            "OrderClose",
            "AccountFreeMarginCheck",
            "RefreshRates",
            "OP_BUY",
            "OP_SELL",
            "IsTradeContextBusy",
        )
        for token in forbidden:
            self.assertNotRegex(self.code, rf"\b{token}\b")

    def test_native_mql5_execution_requires_check_and_exact_evidence(self) -> None:
        for token in (
            "MqlTradeRequest",
            "MqlTradeCheckResult",
            "OrderCheck(request, check_result)",
            "MqlTradeResult",
            "OrderSend(request, result)",
            "HistoryDealSelect(result.deal)",
            "DEAL_POSITION_ID",
            "POSITION_IDENTIFIER",
            "PositionGetTicket",
            "VERIFIED_OPEN",
            "EXECUTION_UNKNOWN",
        ):
            self.assertIn(token, self.code)
        self.assertIn("IsDefinitiveRejectTradeRetcode", self.code)
        self.assertIn("IsAmbiguousTradeRetcode(result.retcode)", self.code)
        self.assertRegex(
            self.code,
            r"(?s)OrderCheck\s*\(\s*request\s*,\s*check_result\s*\).*?check_result\.retcode\s*!=\s*0",
        )
        self.assertNotIn(
            "check_result.retcode != TRADE_RETCODE_DONE",
            self.code,
        )

    def test_order_check_margin_telemetry_is_finite_and_fail_closed(self) -> None:
        helper = re.search(
            r"(?s)bool\s+CheckTradeRequest\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nbool\s+ValidateCurrentRiskState",
            self.code,
        )
        self.assertIsNotNone(helper)
        body = helper.group(1)
        for token in (
            "!MathIsValidNumber(projected_level)",
            "!MathIsValidNumber(projected_margin)",
            "projected_margin <= 0.0",
            "!MathIsValidNumber(account_equity)",
            "!MathIsValidNumber(projected_profit)",
            "!MathIsValidNumber(projected_equity)",
            'reason = "BROKER_MARGIN_TELEMETRY_INVALID"',
        ):
            self.assertIn(token, body)
        self.assertNotIn(": 999999.0", body)

    def test_ambiguous_transport_retcodes_fail_unknown_without_resend(self) -> None:
        definitive = re.search(
            r"(?s)bool\s+IsDefinitiveRejectTradeRetcode\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        ambiguous = re.search(
            r"(?s)bool\s+IsAmbiguousTradeRetcode\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(definitive)
        self.assertIsNotNone(ambiguous)
        self.assertIn("retcode != TRADE_RETCODE_DONE", ambiguous.group(1))
        self.assertIn(
            "!IsDefinitiveRejectTradeRetcode(retcode)",
            ambiguous.group(1),
        )
        # These accepted/indeterminate outcomes must never enter the positive
        # definitive-reject allowlist. Unknown future values therefore also
        # take the conservative EXECUTION_UNKNOWN branch.
        for token in (
            "TRADE_RETCODE_PLACED",
            "TRADE_RETCODE_DONE_PARTIAL",
            "TRADE_RETCODE_ERROR",
            "TRADE_RETCODE_TIMEOUT",
            "TRADE_RETCODE_CONNECTION",
            "TRADE_RETCODE_LOCKED",
            "TRADE_RETCODE_ORDER_CHANGED",
        ):
            self.assertNotIn(token, definitive.group(1))
        send_path = re.search(
            r"(?s)bool\s+sent\s*=\s*OrderSend\(request, result\);(.*?)ulong\s+position_ticket",
            self.code,
        )
        self.assertIsNotNone(send_path)
        self.assertGreaterEqual(
            send_path.group(1).count("IsAmbiguousTradeRetcode(result.retcode)"),
            2,
        )
        self.assertGreaterEqual(send_path.group(1).count('"EXECUTION_UNKNOWN"'), 2)

    def test_execution_attempt_is_durable_before_the_only_order_send(self) -> None:
        execute = re.search(
            r"(?s)void\s+ExecuteCommand\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nvoid\s+ProcessCommandFile",
            self.code,
        )
        self.assertIsNotNone(execute)
        body = execute.group(1)
        attempt_index = body.find('WriteExecutionAttempt(')
        markers_index = body.find('WriteExecutionMarkers(command, executing_payload)')
        send_index = body.find('OrderSend(request, result)')
        self.assertGreaterEqual(attempt_index, 0)
        self.assertGreater(markers_index, attempt_index)
        self.assertGreater(send_index, markers_index)
        self.assertIn('"EXECUTING"', body[:send_index])
        self.assertIn('"ORDER_SEND_RETURNED"', body[send_index:])
        self.assertIn('"IDEMPOTENCY_STATE_WRITE_FAILED"', body[:send_index])
        self.assertIn('"ORDER_SEND_RESULT_PERSIST_FAILED"', body[send_index:])

    def test_execution_attempt_persists_exact_private_identity_and_result(self) -> None:
        for token in (
            '"metafx-hq-mt5-execution-attempt-v1"',
            '"accountBindingId"',
            '"streamKey"',
            '"signedCommandDigest"',
            '"brokerComment"',
            '"expectedVolume"',
            '"positionSizingMode"',
            '"riskPercent"',
            '"riskCapitalBase"',
            '"estimatedCommissionPerLot"',
            '"riskCapitalAmount"',
            '"estimatedRiskMoney"',
            '"expectedStopLoss"',
            '"expectedTakeProfit"',
            '"orderId"',
            '"dealId"',
            '"requestId"',
            '"retcodeExternal"',
            "result.order",
            "result.deal",
            "result.request_id",
            "result.retcode_external",
        ):
            self.assertIn(token, self.code)
        read_attempt = re.search(
            r"(?s)bool\s+ReadExecutionAttempt\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(read_attempt)
        for token in (
            "ProtocolAccountBindingId(current_account_binding_id)",
            "ProtocolStreamKey(command, expected_stream_key)",
            "SignedCommandDigest(signed_raw, expected_signed_digest)",
            "attempt.account_binding_id != current_account_binding_id",
            "attempt.stream_key != expected_stream_key",
            "attempt.signed_command_digest != expected_signed_digest",
        ):
            self.assertIn(token, read_attempt.group(1))

    def test_restart_routes_all_unresolved_attempts_to_exact_reconciliation(self) -> None:
        process = re.search(
            r"(?s)void\s+ProcessCommandFile\s*\(\s*\)\s*\{(.*?)\n\}\n\n\nvoid\s+UpdateChartStatus",
            self.code,
        )
        self.assertIsNotNone(process)
        body = process.group(1)
        self.assertIn('processed_status == "EXECUTING"', body)
        self.assertIn('processed_status == "EXECUTION_UNKNOWN"', body)
        self.assertGreaterEqual(body.count("ReconcileExecutingCommand(command, signed_raw)"), 3)
        self.assertLess(
            body.find("ReconcileExecutingCommand(command, signed_raw)"),
            body.find("ResolveOrderVolume("),
        )
        self.assertLess(
            body.find("ResolveOrderVolume("),
            body.find("ExecuteCommand("),
        )

        reconcile = re.search(
            r"(?s)void\s+ReconcileExecutingCommand\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nvoid\s+ExecuteCommand",
            self.code,
        )
        self.assertIsNotNone(reconcile)
        for token in (
            "ReadExecutionAttempt(command, signed_raw, attempt, reason)",
            "FindRecoveryOpenPosition",
            "FindRecoveryCurrentOrders",
            "FindRecoveryHistory",
            '"MULTIPLE_OR_MISMATCHED_RECOVERY_EVIDENCE"',
            '"RECOVERED_ORDER_FOUND"',
            '"RESTART_RECONCILIATION_REQUIRED"',
        ):
            self.assertIn(token, reconcile.group(1))
        self.assertNotIn('"RECOVERED_POSITION_FOUND"', reconcile.group(1))
        self.assertNotIn('"RECOVERED_HISTORY_FOUND"', reconcile.group(1))

    def test_recovery_matches_comment_magic_symbol_action_volume_and_stops(self) -> None:
        for token in (
            'string expected_comment = "HQ:" + command.command_id;',
            "magic != (long)MagicNumber",
            "Uppercase(symbol) != command.symbol",
            "command.action == \"BUY\"",
            "MathAbs(volume - expected_volume) > volume_tolerance",
            "MathAbs(stop_loss - NormalizeSymbolPrice(command.stop_loss))",
            "MathAbs(take_profit - NormalizeSymbolPrice(command.take_profit))",
            "DEAL_POSITION_ID",
            "DEAL_ORDER",
        ):
            self.assertIn(token, self.code)

    def test_tickets_are_64_bit_and_no_automatic_resend_loop_exists(self) -> None:
        self.assertRegex(self.code, r"ulong\s+position_ticket\s*=\s*0")
        self.assertRegex(self.code, r"const\s+ulong\s+ticket")
        self.assertEqual(self.code.count("OrderSend(request, result)"), 1)
        self.assertNotRegex(
            self.code,
            r"(?s)for\s*\([^)]*\)\s*\{[^{}]*OrderSend\s*\(",
        )

    def test_cross_platform_account_lock_namespace_stays_shared(self) -> None:
        self.assertIn('"MT4|" + StringFormat("%I64d", account_login)', self.code)
        self.assertIn('"MetafxHQ\\\\locks\\\\account-execution-"', self.code)

    def test_broker_symbol_matching_accepts_bounded_prefix_and_suffix_only(self) -> None:
        matcher = re.search(
            r"(?s)bool\s+IsAllowedBrokerSymbol\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nbool\s+IsManagedMagic",
            self.code,
        )
        self.assertIsNotNone(matcher)
        body = matcher.group(1)
        for token in (
            "prefix_length <= 8",
            "suffix_length > 8",
            "IsAllowedBrokerPrefix(",
            "HasSingleBrokerBaseOccurrence(normalized_candidate, allowed)",
            "prefix_length + base_length",
            "IsBrokerSuffixCharacter(",
        ):
            self.assertIn(token, body)

        prefix = re.search(
            r"(?s)bool\s+IsAllowedBrokerPrefix\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(prefix)
        self.assertIn("prefix_length == 1", prefix.group(1))
        self.assertIn("IsBrokerNamespaceDelimiter(", prefix.group(1))
        self.assertIn("prefix_length - 1", prefix.group(1))

        uniqueness = re.search(
            r"(?s)bool\s+HasSingleBrokerBaseOccurrence\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(uniqueness)
        self.assertIn("StringFind(candidate, allowed)", uniqueness.group(1))
        self.assertIn("StringFind(candidate, allowed, first + 1) < 0", uniqueness.group(1))

        runtime = re.search(
            r"(?s)bool\s+ValidateRuntime\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nbool\s+UpdateRiskTelemetry",
            self.code,
        )
        self.assertIsNotNone(runtime)
        self.assertIn("IsAllowedBrokerSymbol(AllowedSymbols, command.symbol)", runtime.group(1))
        self.assertIn("Uppercase(_Symbol) != command.symbol", runtime.group(1))

    def test_broker_symbol_matching_rejects_repeated_canonical_base(self) -> None:
        uniqueness = re.search(
            r"(?s)bool\s+HasSingleBrokerBaseOccurrence\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(uniqueness)
        self.assertIn("XAUUSDXAUUSD", self.source)
        self.assertIn("int first = StringFind(candidate, allowed)", uniqueness.group(1))
        self.assertIn("StringFind(candidate, allowed, first + 1) < 0", uniqueness.group(1))

        matcher = re.search(
            r"(?s)bool\s+IsAllowedBrokerSymbol\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nbool\s+IsManagedMagic",
            self.code,
        )
        self.assertIsNotNone(matcher)
        body = matcher.group(1)
        uniqueness_gate = body.find(
            "!HasSingleBrokerBaseOccurrence(normalized_candidate, allowed)"
        )
        affix_loop = body.find("for(int prefix_length = 0; prefix_length <= 8; prefix_length++)")
        self.assertGreaterEqual(uniqueness_gate, 0)
        self.assertGreater(affix_loop, uniqueness_gate)

    def test_snapshot_uses_closed_copy_rates_and_deal_history(self) -> None:
        self.assertIn("CopyRates(_Symbol, _Period, 1, requested, rates)", self.code)
        self.assertIn(
            "bool tick_available = SymbolInfoTick(_Symbol, tick);",
            self.code,
        )
        self.assertIn(
            "SnapshotMarketOpen(tick, tick_available)",
            self.code,
        )
        self.assertNotIn("SnapshotMarketOpen()", self.code)
        self.assertIn("HistoryDealsTotal()", self.code)
        self.assertIn("PositionsTotal()", self.code)
        self.assertIn("DEAL_PROFIT", self.code)
        self.assertIn("DEAL_COMMISSION", self.code)
        self.assertIn("DEAL_FEE", self.code)

    def test_history_and_position_telemetry_fail_closed(self) -> None:
        for signature in (
            "bool ReadSnapshotDailySummary(",
            "bool ReadSnapshotPositionSummary(",
            "bool ReadManagedOpenState(",
            "bool CountManagedTradesSince(",
            "bool ManagedPnlSince(",
            "bool ReadManagedLossStreak(",
            "bool UpdateRiskTelemetry(",
        ):
            self.assertIn(signature, self.code)
        self.assertIn('reason = "HISTORY_TELEMETRY_UNAVAILABLE";', self.code)
        self.assertIn('reason = "POSITION_TELEMETRY_UNAVAILABLE";', self.code)
        self.assertRegex(
            self.code,
            r"(?s)bool\s+BuildSnapshotJson\s*\([^)]*\).*?if\s*\(\s*!UpdateRiskTelemetry\(false\)\s*\)\s*return\s+false",
        )
        self.assertRegex(
            self.code,
            r"(?s)bool\s+ReadManagedOpenState\s*\([^)]*\).*?PositionGetTicket\(index\).*?if\s*\(\s*ticket\s*==\s*0\s*\)\s*return\s+false",
        )

    def test_history_risk_includes_linked_and_unattributed_broker_costs(self) -> None:
        pnl = re.search(
            r"(?s)bool\s+ManagedPnlSince\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nbool\s+ManagedDailyPnl",
            self.code,
        )
        self.assertIsNotNone(pnl)
        for token in (
            "DEAL_POSITION_ID",
            "DEAL_ORDER",
            "managed_positions",
            "managed_orders",
            "linked_to_managed_lifecycle",
            "profit + swap + commission + fee",
            "result < 0.0",
            "IsBrokerCostDealType(type)",
        ):
            self.assertIn(token, pnl.group(1))
        for token in (
            "DEAL_TYPE_CHARGE",
            "DEAL_TYPE_CORRECTION",
            "DEAL_TYPE_COMMISSION",
            "DEAL_TYPE_COMMISSION_DAILY",
            "DEAL_TYPE_COMMISSION_MONTHLY",
            "DEAL_TYPE_COMMISSION_AGENT_DAILY",
            "DEAL_TYPE_COMMISSION_AGENT_MONTHLY",
            "DEAL_TYPE_INTEREST",
            "DEAL_TYPE_BUY_CANCELED",
            "DEAL_TYPE_SELL_CANCELED",
        ):
            self.assertIn(token, self.code)
        loss_streak = re.search(
            r"(?s)bool\s+ReadManagedLossStreak\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nbool\s+CurrentAccountDrawdownPercent",
            self.code,
        )
        self.assertIsNotNone(loss_streak)
        self.assertIn("ManagedPositionLifecyclePnl", loss_streak.group(1))
        self.assertIn("HistoryPositionIsManaged", loss_streak.group(1))
        self.assertIn("loss_count++", loss_streak.group(1))
        self.assertIn("HistorySelect(0, now)", loss_streak.group(1))
        self.assertNotIn("BrokerWeekStart()", loss_streak.group(1))
        self.assertIn(
            "loss_count >= MaxConsecutiveManagedLosses",
            loss_streak.group(1),
        )

        lifecycle = re.search(
            r"(?s)bool\s+ManagedPositionLifecyclePnl\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(lifecycle)
        self.assertIn("bool saw_entry = false", lifecycle.group(1))
        self.assertIn("entry == DEAL_ENTRY_IN", lifecycle.group(1))
        self.assertIn("return saw_entry && latest_exit_time > 0", lifecycle.group(1))

    def test_loss_caps_include_open_managed_losses_without_profit_offset(self) -> None:
        helper = re.search(
            r"(?s)bool\s+ManagedRiskPnlIncludingFloatingLoss\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(helper)
        self.assertIn("MathMin(0.0, floating_pnl)", helper.group(1))
        self.assertIn("MathIsValidNumber(realized_pnl)", helper.group(1))
        self.assertIn("MathIsValidNumber(floating_pnl)", helper.group(1))

        current_risk = re.search(
            r"(?s)bool\s+ValidateCurrentRiskState\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nbool\s+ValidateRiskEnvelope",
            self.code,
        )
        self.assertIsNotNone(current_risk)
        self.assertEqual(
            current_risk.group(1).count("ManagedRiskPnlIncludingFloatingLoss("),
            2,
        )
        self.assertIn("daily_risk_pnl", current_risk.group(1))
        self.assertIn("weekly_risk_pnl", current_risk.group(1))
        self.assertIn("!MathIsValidNumber(balance)", current_risk.group(1))
        self.assertIn("datetime broker_now = TimeCurrent()", current_risk.group(1))
        self.assertIn("(int)broker_now < cooldown_until", current_risk.group(1))
        self.assertNotIn("NowUtc() < cooldown_until", current_risk.group(1))
        self.assertIn(
            "CurrentAccountDrawdownPercent(account_drawdown_percent)",
            current_risk.group(1),
        )

    def test_position_and_account_risk_telemetry_reject_non_finite_values(self) -> None:
        managed = re.search(
            r"(?s)bool\s+ReadManagedOpenState\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nbool\s+CountManagedTradesSince",
            self.code,
        )
        self.assertIsNotNone(managed)
        for token in (
            "!MathIsValidNumber(volume)",
            "volume <= 0.0",
            "!MathIsValidNumber(profit)",
            "!MathIsValidNumber(swap)",
            "!MathIsValidNumber(lots)",
            "!MathIsValidNumber(floating_pnl)",
        ):
            self.assertIn(token, managed.group(1))

        drawdown = re.search(
            r"(?s)bool\s+CurrentAccountDrawdownPercent\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(drawdown)
        for token in (
            "!MathIsValidNumber(balance)",
            "!MathIsValidNumber(equity)",
            "MathIsValidNumber(drawdown_percent)",
        ):
            self.assertIn(token, drawdown.group(1))

        telemetry = re.search(
            r"(?s)bool\s+UpdateRiskTelemetry\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nstring\s+BrokerRetcodeReason",
            self.code,
        )
        self.assertIsNotNone(telemetry)
        self.assertEqual(
            telemetry.group(1).count("ManagedRiskPnlIncludingFloatingLoss("),
            2,
        )
        self.assertIn(
            "g_cached_managed_daily_pnl = daily_risk_pnl;",
            telemetry.group(1),
        )
        self.assertIn(
            "g_cached_managed_weekly_pnl = weekly_risk_pnl;",
            telemetry.group(1),
        )

    def test_trade_session_lookup_fails_closed(self) -> None:
        session_guard = re.search(
            r"(?s)bool\s+IsTradeSessionOpen\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nbool\s+SelectFillingMode",
            self.code,
        )
        self.assertIsNotNone(session_guard)
        body = session_guard.group(1)
        self.assertIn("SymbolInfoSessionTrade(", body)
        self.assertIn('reason = "BROKER_TRADE_SESSION_UNAVAILABLE";', body)
        self.assertIn('reason = "BROKER_TRADE_SESSION_INVALID";', body)
        self.assertRegex(
            body,
            r"if\s*\(\s*!observed_session\s*\)\s*\{\s*reason\s*=\s*\"BROKER_TRADE_SESSION_UNAVAILABLE\";\s*return\s+false;",
        )
        self.assertNotRegex(
            body,
            r"if\s*\(\s*observed_session\s*&&\s*!inside_session\s*\)",
        )

    def test_execution_tolerance_inputs_have_finite_upper_bounds(self) -> None:
        for token in (
            "const int MAX_SAFE_SPREAD_POINTS = 10000;",
            "const int MAX_SAFE_SLIPPAGE_POINTS = 1000;",
            "const int MAX_SAFE_SIGNAL_DRIFT_POINTS = 10000;",
            "MaxSpreadPoints > MAX_SAFE_SPREAD_POINTS",
            "SlippagePoints > MAX_SAFE_SLIPPAGE_POINTS",
            "MaxSignalDriftPoints > MAX_SAFE_SIGNAL_DRIFT_POINTS",
        ):
            self.assertIn(token, self.code)

    def test_money_management_modes_are_local_inputs_and_risk_is_hard_capped(self) -> None:
        for token in (
            "enum ENUM_MONEY_MANAGEMENT_MODE",
            "MONEY_MANAGEMENT_FIXED_LOT",
            "MONEY_MANAGEMENT_RISK_PERCENT",
            "enum ENUM_RISK_CAPITAL_BASE",
            "RISK_CAPITAL_BALANCE",
            "RISK_CAPITAL_EQUITY",
            "input ENUM_MONEY_MANAGEMENT_MODE MoneyManagementMode = MONEY_MANAGEMENT_FIXED_LOT;",
            "input double RiskPercent = 1.0;",
            "input ENUM_RISK_CAPITAL_BASE RiskCapitalBase = RISK_CAPITAL_EQUITY;",
            "input double EstimatedCommissionPerLot = 0.0;",
            "input bool CommissionFreeAccountConfirmed = false;",
            "effective_risk_percent > MaxLossPerTradePercent",
        ):
            self.assertIn(token, self.code)
        for forbidden_key in (
            'normalized == "LOT"',
            'normalized == "LOTS"',
            'normalized == "FIXEDLOT"',
            'normalized == "RISKPERCENT"',
            'normalized == "POSITION_SIZING"',
            'normalized == "POSITIONSIZING"',
            'normalized == "MONEY_MANAGEMENT"',
            'normalized == "MONEYMANAGEMENT"',
            'normalized == "RISK_CAPITAL_BASE"',
            'normalized == "VOLUME"',
        ):
            self.assertIn(forbidden_key, self.code)

        validation = re.search(
            r"(?s)bool\s+ValidateMoneyManagementConfiguration\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nbool\s+ResolveReadinessProbeVolume",
            self.code,
        )
        self.assertIsNotNone(validation)
        body = validation.group(1)
        for token in (
            "!MathIsValidNumber(FixedLot)",
            "FixedLot < 0.0",
            "FixedLot > 1000.0",
            "!MathIsValidNumber(RiskPercent)",
            "RiskPercent < 0.0",
            "RiskPercent > 100.0",
            "effective_risk_percent = EffectiveRiskPercent()",
            "MoneyManagementMode == MONEY_MANAGEMENT_RISK_PERCENT",
            "effective_risk_percent < 0.00000001",
            "effective_risk_percent > MaxLossPerTradePercent",
            "MoneyManagementMode == MONEY_MANAGEMENT_FIXED_LOT",
            "!ValidateFixedLot(reason)",
            "GatewayMode == GATEWAY_LIVE && !LiveCommissionPolicyConfirmed()",
            'reason = "LIVE_COMMISSION_POLICY_UNCONFIRMED"',
        ):
            self.assertIn(token, body)

    def test_live_requires_explicit_commission_policy_and_exact_symbol_token(self) -> None:
        effective_commission = re.search(
            r"(?s)double\s+EffectiveEstimatedCommissionPerLot\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(effective_commission)
        for token in (
            "MathIsValidNumber(EstimatedCommissionPerLot)",
            "NormalizeDouble(EstimatedCommissionPerLot, 8)",
        ):
            self.assertIn(token, effective_commission.group(1))

        commission_policy = re.search(
            r"(?s)bool\s+LiveCommissionPolicyConfirmed\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(commission_policy)
        for token in (
            "EstimatedCommissionPerLot >= 0.0",
            "EstimatedCommissionPerLot <= 1000000.0",
            "EffectiveEstimatedCommissionPerLot() >= 0.00000001",
            "CommissionFreeAccountConfirmed",
        ):
            self.assertIn(token, commission_policy.group(1))
        self.assertNotIn("EstimatedCommissionPerLot > 0.0", commission_policy.group(1))

        exact_symbol = re.search(
            r"(?s)bool\s+LiveSymbolExactAllowlistConfirmed\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(exact_symbol)
        self.assertIn("CsvContains(AllowedSymbols, _Symbol)", exact_symbol.group(1))
        self.assertNotIn("IsAllowedBrokerSymbol", exact_symbol.group(1))

        canonical = re.search(
            r"(?s)bool\s+BuildPortfolioPolicyCanonical\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(canonical)
        canonical_body = canonical.group(1)
        commission_index = canonical_body.find('"|estimatedCommissionPerLot="')
        confirmation_index = canonical_body.find('"|commissionFreeAccountConfirmed="')
        position_cap_index = canonical_body.find('"|maxManagedOpenPositions="')
        self.assertGreaterEqual(commission_index, 0)
        self.assertGreater(confirmation_index, commission_index)
        self.assertGreater(position_cap_index, confirmation_index)
        self.assertIn("DoubleToString(EffectiveEstimatedCommissionPerLot(), 8)", canonical_body)

        capabilities = re.search(
            r"(?s)string\s+BuildCapabilitiesJson\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(capabilities)
        for token in (
            "LiveCommissionPolicyConfirmed()",
            "LiveSymbolExactAllowlistConfirmed()",
            "LIVE_COMMISSION_POLICY_UNCONFIRMED",
            "LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST",
        ):
            self.assertIn(token, capabilities.group(1))

        status = re.search(
            r"(?s)string\s+BuildStatusJson\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(status)
        self.assertIn(r'\"commissionFreeAccountConfirmed\":', status.group(1))
        self.assertIn("JsonBoolean(CommissionFreeAccountConfirmed)", status.group(1))
        self.assertIn("JsonNumber(EffectiveEstimatedCommissionPerLot(), 8)", status.group(1))

        runtime = re.search(
            r"(?s)bool\s+ValidateRuntime\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nbool\s+UpdateRiskTelemetry",
            self.code,
        )
        self.assertIsNotNone(runtime)
        for token in (
            "GatewayMode == GATEWAY_LIVE",
            "!CsvContains(AllowedSymbols, command.symbol)",
            'reason = "LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST"',
            "GatewayMode != GATEWAY_LIVE",
            "!IsAllowedBrokerSymbol(AllowedSymbols, command.symbol)",
            "Uppercase(_Symbol) != command.symbol",
        ):
            self.assertIn(token, runtime.group(1))

        on_init = re.search(r"(?s)int\s+OnInit\s*\(\s*\)\s*\{(.*)\Z", self.code)
        self.assertIsNotNone(on_init)
        on_init_body = on_init.group(1)
        self.assertIn("!LiveSymbolExactAllowlistConfirmed()", on_init_body)
        self.assertIn("LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST", on_init_body)
        exact_gate_index = on_init_body.find("!LiveSymbolExactAllowlistConfirmed()")
        broker_match_index = on_init_body.find(
            "!IsAllowedBrokerSymbol(AllowedSymbols, _Symbol)"
        )
        self.assertGreaterEqual(exact_gate_index, 0)
        self.assertGreater(broker_match_index, exact_gate_index)

    def test_risk_sizing_uses_broker_units_floors_volume_and_reserves_fees(self) -> None:
        sizing = re.search(
            r"(?s)bool\s+ResolveOrderVolume\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nbool\s+ValidateClosedBarBinding",
            self.code,
        )
        self.assertIsNotNone(sizing)
        body = sizing.group(1)
        for token in (
            "SYMBOL_VOLUME_LIMIT",
            "ReadDirectionalSymbolVolume(type, directional_volume, reason)",
            "ReadManagedOpenState(",
            "remaining_managed_lots = MaxManagedTotalLots - managed_lots",
            "MathMax(0.0, remaining_managed_lots)",
            "symbol_volume_limit - directional_volume",
            "entry + (double)SlippagePoints * point",
            "entry - (double)SlippagePoints * point",
            "OrderCalcProfit(",
            "requested_risk_budget",
            "risk_capital_amount * EffectiveRiskPercent() / 100.0",
            "balance_risk_cap",
            "MathMin(requested_risk_budget, balance_risk_cap)",
            "risk_budget < 0.00000001",
            "risk_budget / loss_per_lot",
            "EffectiveEstimatedCommissionPerLot() * volume",
            "estimated_risk_money < 0.00000001",
            'reason = "RISK_ESTIMATE_BELOW_WIRE_MINIMUM"',
            "MathFloor(",
            "(capped_volume - minimum) / step",
            "minimum + MathMax(0.0, step_count) * step",
            'reason = "RISK_VOLUME_BELOW_BROKER_MINIMUM";',
            "volume = NormalizeDouble(volume - step, LotDigits())",
            "OrderCalcMargin(",
        ):
            self.assertIn(token, body)
        for token in (
            "SYMBOL_VOLUME_MIN",
            "SYMBOL_VOLUME_MAX",
            "SYMBOL_VOLUME_STEP",
        ):
            self.assertIn(token, self.code)
        for redundant_metadata in (
            "SYMBOL_TRADE_TICK_SIZE",
            "SYMBOL_TRADE_TICK_VALUE",
            "SYMBOL_TRADE_TICK_VALUE_LOSS",
            "SYMBOL_TRADE_CONTRACT_SIZE",
        ):
            self.assertNotIn(redundant_metadata, body)
        self.assertNotIn("ACCOUNT_COMPANY", body)
        self.assertNotIn('"CENT"', body.upper())
        self.assertNotIn(
            "MathMax(0.00000001, risk_budget * 0.000000001)",
            body,
        )
        self.assertRegex(
            body,
            r"if\s*\(\s*!MathIsValidNumber\(estimated_risk_money\)\s*\|\|\s*estimated_risk_money\s*<\s*0\.00000001\s*\)",
        )

    def test_lot_precision_covers_nonzero_grid_origin_and_step(self) -> None:
        digits = re.search(
            r"(?s)int\s+LotDigits\s*\(\s*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(digits)
        for token in (
            "SYMBOL_VOLUME_MIN",
            "SYMBOL_VOLUME_STEP",
            "VolumeDigitsForValue(minimum)",
            "VolumeDigitsForValue(step)",
            "minimum_digits > step_digits",
        ):
            self.assertIn(token, digits.group(1))
        self.assertIn(
            "minimum + MathMax(0.0, step_count) * step",
            self.code,
        )

    def test_risk_percent_is_normalized_to_one_eight_decimal_semantic_value(self) -> None:
        helper = re.search(
            r"(?s)double\s+EffectiveRiskPercent\s*\(\s*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(helper)
        self.assertIn("NormalizeDouble(RiskPercent, 8)", helper.group(1))

        # Raw input is allowed only at the declaration, normalization helper,
        # and finite/range validation boundary. Values with more than 8dp are
        # accepted but all behavior uses the one normalized semantic value.
        raw_uses = [
            line.strip()
            for line in self.code.splitlines()
            if "RiskPercent" in line and "EffectiveRiskPercent" not in line
        ]
        permitted_fragments = (
            "input double RiskPercent =",
            "NormalizeDouble(RiskPercent, 8)",
            "!MathIsValidNumber(RiskPercent)",
            "RiskPercent < 0.0 || RiskPercent > 100.0",
            "MathAbs(RiskPercent - effective_risk_percent)",
        )
        self.assertTrue(raw_uses)
        for line in raw_uses:
            self.assertTrue(
                any(fragment in line for fragment in permitted_fragments),
                f"raw RiskPercent bypasses the 8dp semantic boundary: {line}",
            )
        self.assertNotIn(
            "RISK_PERCENT_PRECISION_EXCEEDS_8_DECIMALS",
            self.code,
        )

        for token in (
            "DoubleToString(EffectiveRiskPercent(), 8)",
            "JsonNumber(EffectiveRiskPercent(), 8)",
            "risk_capital_amount * EffectiveRiskPercent() / 100.0",
            "risk_capital * EffectiveRiskPercent() / 100.0",
        ):
            self.assertIn(token, self.code)
        self.assertGreaterEqual(
            self.code.count("EffectiveRiskPercent(),"),
            2,
        )

    def test_quote_freshness_uses_broker_server_clock_domain(self) -> None:
        helper = re.search(
            r"(?s)bool\s+ReadFreshTick\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(helper)
        body = helper.group(1)
        self.assertIn("datetime server_now = TimeCurrent()", body)
        self.assertIn("server_now < tick.time", body)
        self.assertIn("server_now - tick.time > MaxQuoteAgeSeconds", body)
        self.assertNotIn("NowUtc()", body)

        snapshot_market = re.search(
            r"(?s)bool\s+SnapshotMarketOpen\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(snapshot_market)
        snapshot_body = snapshot_market.group(1)
        self.assertIn("datetime server_now = TimeCurrent()", snapshot_body)
        self.assertIn("server_now >= tick.time", snapshot_body)
        self.assertIn(
            "server_now - tick.time <= MaxQuoteAgeSeconds",
            snapshot_body,
        )
        self.assertNotIn("NowUtc()", snapshot_body)

    def test_final_risk_envelope_uses_adverse_entry_from_the_request_tick(self) -> None:
        envelope = re.search(
            r"(?s)bool\s+ValidateRiskEnvelope\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nbool\s+ValidateHeartbeat",
            self.code,
        )
        self.assertIsNotNone(envelope)
        body = envelope.group(1)
        for token in (
            "command.action == \"BUY\" ? tick.ask : tick.bid",
            "entry + (double)SlippagePoints * point",
            "entry - (double)SlippagePoints * point",
            "order_volume,\n         risk_entry,\n         stop_loss",
            "order_volume,\n         risk_entry,\n         take_profit",
            "risk_budget < 0.00000001",
            "double tolerance = risk_budget * 0.000000001",
            "final_estimated_risk_money = loss_money",
            "persisted_risk_budget =",
            "g_ack_risk_capital_amount * g_ack_risk_percent / 100.0",
            "MathMin(\n         live_risk_budget,\n         persisted_risk_budget",
        ):
            self.assertIn(token, body)

        execute = re.search(
            r"(?s)void\s+ExecuteCommand\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nvoid\s+ProcessCommandFile",
            self.code,
        )
        self.assertIsNotNone(execute)
        flow = execute.group(1)
        risk_index = flow.find("ValidateRiskEnvelope(\n             command,\n             tick,")
        request_index = flow.find("BuildTradeRequest(\n             command,\n             tick,")
        send_index = flow.find("OrderSend(request, result)")
        self.assertGreaterEqual(risk_index, 0)
        self.assertGreater(request_index, risk_index)
        self.assertGreater(send_index, request_index)
        self.assertEqual(flow[:send_index].count("ReadFreshTick(tick, reason)"), 1)
        final_risk_index = flow.find(
            "g_ack_estimated_risk_money = final_estimated_risk_money"
        )
        final_persist_index = flow.find("WriteExecutionAttempt(", final_risk_index)
        self.assertGreater(final_risk_index, request_index)
        self.assertGreater(final_persist_index, final_risk_index)
        self.assertLess(final_persist_index, send_index)
        self.assertIn(
            '"FINAL_RISK_STATE_WRITE_FAILED"',
            flow[final_persist_index:send_index],
        )

    def test_recovery_history_uses_broker_clock_with_utc_age_conversion(self) -> None:
        helper = re.search(
            r"(?s)bool\s+FindRecoveryHistory\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nvoid\s+MarkRecoveryUnknown",
            self.code,
        )
        self.assertIsNotNone(helper)
        body = helper.group(1)
        for token in (
            "datetime now = TimeCurrent()",
            "datetime utc_now = TimeGMT()",
            "(long)utc_now - (long)command.issued_at",
            "command_age_seconds + 86400",
            "datetime since = now - (datetime)lookback_seconds",
            "HistorySelect(since, now)",
        ):
            self.assertIn(token, body)
        self.assertNotIn("command.issued_at - 300", body)

    def test_post_fill_risk_truth_is_reported_without_expanding_ack_vocabulary(self) -> None:
        helper = re.search(
            r"(?s)string\s+FilledRiskAssessmentCode\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(helper)
        for token in (
            "OrderCalcProfit(",
            "estimated_commission_per_lot * volume",
            "pre_send_estimated_risk * 0.000000001",
            '"SLIPPAGE_RESERVE_AND_RISK_ESTIMATE_EXCEEDED"',
            ': "RISK_ESTIMATE_EXCEEDED"',
            "SlippagePoints",
            'return "SLIPPAGE_RESERVE_EXCEEDED"',
        ):
            self.assertIn(token, helper.group(1))

        capture = re.search(
            r"(?s)bool\s+CaptureExecutionEvidence\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nvoid\s+WriteDuplicateAck",
            self.code,
        )
        self.assertIsNotNone(capture)
        body = capture.group(1)
        for token in (
            "FilledRiskAssessmentCode(",
            'g_ack_verification_status = "VERIFIED_OPEN"',
            '"ORDER_VERIFIED_OPEN_SLIPPAGE_RESERVE_AND_RISK_ESTIMATE_EXCEEDED"',
            'reason = "ORDER_VERIFIED_OPEN_RISK_ESTIMATE_EXCEEDED"',
            'reason = "ORDER_VERIFIED_OPEN_SLIPPAGE_RESERVE_EXCEEDED"',
            'reason = "ORDER_VERIFIED_OPEN_RISK_UNAVAILABLE"',
        ):
            self.assertIn(token, body)
        self.assertNotIn(
            'g_ack_verification_status = "VERIFIED_OPEN_RISK_ESTIMATE_EXCEEDED"',
            body,
        )
        self.assertNotIn(
            'g_ack_verification_status = "VERIFIED_OPEN_SLIPPAGE_RESERVE_EXCEEDED"',
            body,
        )

    def test_safety_double_inputs_reject_nan_and_infinity(self) -> None:
        on_init = re.search(
            r"(?s)int\s+OnInit\s*\(\s*\)\s*\{(.*?)\n\}\n\n\nvoid\s+OnDeinit",
            self.code,
        )
        self.assertIsNotNone(on_init)
        body = on_init.group(1)
        for name in (
            "MaxManagedTotalLots",
            "MaxLossPerTradePercent",
            "MaxDailyLossPercent",
            "MaxManagedWeeklyLossPercent",
            "MaxAccountEquityDrawdownPercent",
            "MinRewardRiskRatio",
            "MinProjectedMarginLevelPercent",
        ):
            self.assertIn(f"!MathIsValidNumber({name})", body)

    def test_selected_volume_flows_through_caps_checks_request_and_ack(self) -> None:
        for token in (
            "const double proposed_volume",
            "lots + proposed_volume >",
            "MaxManagedTotalLots + 0.00000001",
            "request.volume = order_volume;",
            "ValidateRiskEnvelope(\n   const CommandPayload &command,\n   const MqlTick &tick,\n   const double order_volume",
            "OrderCalcProfit(\n         type,\n         _Symbol,\n         order_volume",
            'payload += "\\\"fixedLot\\\":" +',
            "DoubleToString(reported_volume, LotDigits())",
            "MathAbs(volume - request.volume) > volume_tolerance",
            "MathAbs(volume - expected_volume) > volume_tolerance",
        ):
            self.assertIn(token, self.code)
        self.assertNotRegex(self.code, r"MathAbs\([^\r\n]*FixedLot")
        self.assertEqual(self.code.count("OrderSend(request, result)"), 1)

    def test_exact_sized_volume_is_persisted_before_send_and_reused_after_restart(self) -> None:
        execute = re.search(
            r"(?s)void\s+ExecuteCommand\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nvoid\s+ProcessCommandFile",
            self.code,
        )
        self.assertIsNotNone(execute)
        body = execute.group(1)
        persist_index = body.find("WriteExecutionAttempt(")
        send_index = body.find("OrderSend(request, result)")
        self.assertGreaterEqual(persist_index, 0)
        self.assertGreater(send_index, persist_index)
        self.assertIn("order_volume", body[persist_index:send_index])

        reconcile = re.search(
            r"(?s)void\s+ReconcileExecutingCommand\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nvoid\s+ExecuteCommand",
            self.code,
        )
        self.assertIsNotNone(reconcile)
        for token in (
            "attempt.expected_volume",
            "attempt.position_sizing_mode",
            "attempt.risk_percent",
            "attempt.risk_capital_base",
            "attempt.estimated_commission_per_lot",
            "attempt.risk_capital_amount",
            "attempt.estimated_risk_money",
        ):
            self.assertIn(token, reconcile.group(1))
        self.assertNotIn("ResolveOrderVolume(", reconcile.group(1))

        read_attempt = re.search(
            r"(?s)bool\s+ReadExecutionAttempt\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nvoid\s+FinalizeCommand",
            self.code,
        )
        self.assertIsNotNone(read_attempt)
        self.assertIn("!MathIsValidNumber(expected_volume)", read_attempt.group(1))
        self.assertIn(
            "estimated_risk_money < 0.00000001",
            read_attempt.group(1),
        )
        self.assertNotIn(
            'attempt.position_sizing_mode == "RISK_PERCENT" &&\n        estimated_risk_money < 0.00000001',
            read_attempt.group(1),
        )
        self.assertNotIn("expected_volume > MaxManagedTotalLots", read_attempt.group(1))
        self.assertGreaterEqual(
            self.code.count("const double volume_tolerance = 0.00000001;"),
            6,
        )

        persist = re.search(
            r"(?s)bool\s+BuildExecutionAttemptJson\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nbool\s+WriteExecutionAttempt",
            self.code,
        )
        self.assertIsNotNone(persist)
        for token in (
            "DoubleToString(expected_volume, 8)",
            "JsonNumber(g_ack_risk_percent, 8)",
            "JsonNumber(g_ack_estimated_commission_per_lot, 8)",
            "JsonNumber(g_ack_risk_capital_amount, 8)",
            "JsonNumber(g_ack_estimated_risk_money, 8)",
        ):
            self.assertIn(token, persist.group(1))

    def test_position_sizing_telemetry_is_backward_compatible(self) -> None:
        for field in (
            r'\"positionSizingMode\":',
            r'\"riskPercent\":',
            r'\"riskCapitalBase\":',
            r'\"brokerVolumeMin\":',
            r'\"brokerVolumeMax\":',
            r'\"brokerVolumeStep\":',
            r'\"riskCapitalAmount\":',
            r'\"estimatedRiskMoney\":',
            r'\"estimatedCommissionPerLot\":',
            r'\"commissionFreeAccountConfirmed\":',
        ):
            self.assertIn(field, self.code)
        ack = re.search(
            r"(?s)string\s+BuildAckJson\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nbool\s+IsExecutionAttemptKey",
            self.code,
        )
        self.assertIsNotNone(ack)
        body = ack.group(1)
        for token in (
            "double reported_volume = g_ack_has_sizing_evidence",
            "? g_ack_reported_volume",
            ": 0.0",
            "JsonNumber(g_ack_risk_capital_amount, 8)",
            "JsonNumber(g_ack_estimated_risk_money, 8)",
            '"riskCapitalAmount\\\":null',
            '"estimatedRiskMoney\\\":null',
            "? g_ack_risk_percent\n         : EffectiveRiskPercent(),\n      8",
        ):
            self.assertIn(token, body)
        self.assertIn(
            "JsonNumber(EffectiveRiskPercent(), 8)",
            self.code,
        )

    def test_unsized_rejections_and_duplicates_publish_zero_and_null_evidence(self) -> None:
        reset = re.search(
            r"(?s)void\s+ResetAckExecutionEvidence\s*\(\s*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(reset)
        for token in (
            "g_ack_has_sizing_evidence = false",
            "g_ack_reported_volume = 0.0",
            "g_ack_risk_capital_amount = 0.0",
            "g_ack_estimated_risk_money = 0.0",
        ):
            self.assertIn(token, reset.group(1))

        duplicate = re.search(
            r"(?s)void\s+WriteDuplicateAck\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(duplicate)
        self.assertIn("ResetAckExecutionEvidence();", duplicate.group(1))

        process = re.search(
            r"(?s)void\s+ProcessCommandFile\s*\(\s*\)\s*\{(.*?)\n\}\n\n\nvoid\s+UpdateChartStatus",
            self.code,
        )
        self.assertIsNotNone(process)
        body = process.group(1)
        reset_index = body.find("ResetAckExecutionEvidence();")
        parse_index = body.find("ParseCommand(signed_raw, command, reason)")
        sizing_index = body.find("SetAckSizingEvidence(")
        shadow_index = body.find('"SHADOWED"')
        self.assertGreaterEqual(reset_index, 0)
        self.assertGreater(parse_index, reset_index)
        self.assertGreater(sizing_index, parse_index)
        self.assertGreater(shadow_index, sizing_index)

    def test_readiness_probe_matches_active_sizing_mode(self) -> None:
        probe = re.search(
            r"(?s)bool\s+ResolveReadinessProbeVolume\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nbool\s+SelectedRiskCapital",
            self.code,
        )
        self.assertIsNotNone(probe)
        body = probe.group(1)
        self.assertIn("probe_volume = FixedLot", body)
        self.assertIn(
            "MoneyManagementMode == MONEY_MANAGEMENT_RISK_PERCENT",
            body,
        )
        self.assertIn("ReadBrokerVolumeLimits(minimum, maximum, step, reason)", body)
        self.assertIn("probe_volume = minimum", body)

        telemetry = re.search(
            r"(?s)bool\s+UpdateRiskTelemetry\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nstring\s+BrokerRetcodeReason",
            self.code,
        )
        self.assertIsNotNone(telemetry)
        flow = telemetry.group(1)
        probe_index = flow.find("ResolveReadinessProbeVolume(readiness_probe_volume, reason)")
        risk_index = flow.find("ValidateCurrentRiskState(readiness_probe_volume, reason)")
        self.assertGreaterEqual(probe_index, 0)
        self.assertGreater(risk_index, probe_index)
        self.assertNotIn("ValidateCurrentRiskState(0.0, reason)", flow)

    def test_mt5_live_requires_explicit_single_host_fences(self) -> None:
        self.assertNotIn('"DISTRIBUTED_ACCOUNT_LEASE_REQUIRED"', self.code)
        self.assertIn('#property version   "1.03"', self.code)
        self.assertIn('string EA_VERSION = "1.03";', self.code)
        for token in (
            "LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT",
            "LIVE_NOT_ARMED",
            "SINGLE_HOST_LIVE_ACK_REQUIRED",
            "LIVE_SIGNING_KEY_PIN_REQUIRED",
            "LIVE_SIGNING_KEY_PIN_MISMATCH",
            "LIVE_ACCOUNT_OWNER_LOCK_UNAVAILABLE",
            "LIVE_ACCOUNT_BINDING_CHANGED",
            '"MetafxHQ\\\\locks\\\\account-live-owner-"',
            "AcquireLiveAccountOwnerLock(live_owner_reason)",
            "ReleaseLiveAccountOwnerLock()",
        ):
            self.assertIn(token, self.code)
        on_init = re.search(
            r"(?s)int\s+OnInit\s*\(\s*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(on_init)
        for token in (
            "GatewayMode == GATEWAY_LIVE && IsDemo()",
            "AcquireChannelLock()",
            "AcquireLiveAccountOwnerLock(live_owner_reason)",
        ):
            self.assertIn(token, on_init.group(1))
        self.assertNotIn('"LIVE_NOT_ARMED"', on_init.group(1))
        self.assertNotIn('"SINGLE_HOST_LIVE_ACK_REQUIRED"', on_init.group(1))
        self.assertRegex(
            on_init.group(1),
            r"GatewayMode\s*==\s*GATEWAY_LIVE\s*&&\s*LiveArmed\s*&&\s*SingleHostLiveAcknowledged\s*&&\s*!signing_ready",
        )
        self.assertLess(
            on_init.group(1).find("AcquireChannelLock()"),
            on_init.group(1).find("AcquireLiveAccountOwnerLock(live_owner_reason)"),
        )

    def test_major_mt5_init_failures_publish_specific_diagnostics(self) -> None:
        on_init = re.search(
            r"(?s)int\s+OnInit\s*\(\s*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(on_init)
        body = on_init.group(1)
        for token in (
            '"account_mode",\n         "MT5_HEDGING_ACCOUNT_REQUIRED"',
            '"account_mode",\n         "LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT"',
            '"live_account_owner_lock"',
            '"account_execution_lock"',
            '"INITIAL_SNAPSHOT_WRITE_FAILED"',
            '"INITIAL_CAPABILITIES_WRITE_FAILED"',
            '"INITIAL_STATUS_WRITE_FAILED"',
            'RecordInitDiagnostic("info", "ready", "INIT_SUCCEEDED", INIT_SUCCEEDED)',
        ):
            self.assertIn(token, body)
        self.assertNotIn('"INITIAL_PUBLICATION_FAILED"', body)
        acquire_owner = re.search(
            r"(?s)bool\s+AcquireLiveAccountOwnerLock\s*\([^)]*\)\s*\{(.*?)\n\}",
            self.code,
        )
        self.assertIsNotNone(acquire_owner)
        self.assertIn("FILE_READ | FILE_WRITE", acquire_owner.group(1))
        self.assertIn("FILE_COMMON", acquire_owner.group(1))
        self.assertIn("FILE_SHARE_READ", acquire_owner.group(1))
        self.assertNotIn("FILE_SHARE_WRITE", acquire_owner.group(1))
        self.assertRegex(
            self.code,
            r"(?s)bool\s+ValidateCurrentRiskState\s*\([^)]*\).*?HISTORY_TELEMETRY_UNAVAILABLE",
        )
        self.assertEqual(
            self.code.count(r'\"singleHostLiveAcknowledged\":'),
            2,
        )
        self.assertEqual(
            self.code.count(
                r'\"liveSafetyScope\":\"single_windows_user_file_common_only\"'
            ),
            2,
        )
        self.assertIn(
            r'\"concurrencyBoundary\":\"same_windows_user_file_common\"',
            self.code,
        )
        self.assertIn(r'\"crossVpsDistributedLock\":false', self.code)

    def test_live_owner_and_account_binding_are_rechecked_before_order_send(self) -> None:
        execute = re.search(
            r"(?s)void\s+ExecuteCommand\s*\([^)]*\)\s*\{(.*?)\n\}\n\n\nvoid\s+ProcessCommandFile",
            self.code,
        )
        self.assertIsNotNone(execute)
        body = execute.group(1)
        send_index = body.find("OrderSend(request, result)")
        owner_index = body.rfind("LiveAccountOwnerLockReady(reason)", 0, send_index)
        envelope_index = body.rfind("ReverifyCommandEnvelope", 0, send_index)
        self.assertGreater(send_index, 0)
        self.assertGreater(owner_index, envelope_index)
        self.assertLess(owner_index, send_index)
        self.assertIn("AcquireAccountExecutionLock()", body[:send_index])
        self.assertIn("WriteExecutionMarkers(command, executing_payload)", body[:send_index])


if __name__ == "__main__":
    unittest.main()
