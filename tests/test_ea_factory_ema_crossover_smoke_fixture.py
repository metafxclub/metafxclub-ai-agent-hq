from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "ea-smoke" / "MetafxEmaCrossoverSmokeEA.mq5"


class EmaCrossoverSmokeFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = FIXTURE.read_text(encoding="utf-8")

    def test_has_only_requested_sl_and_tp_inputs(self) -> None:
        inputs = re.findall(r"(?m)^\s*input\s+\w+\s+(\w+)\s*=", self.source)
        self.assertEqual(inputs, ["StopLossPips", "TakeProfitPips"])
        self.assertRegex(self.source, r"input\s+double\s+StopLossPips\s*=\s*[1-9]")
        self.assertRegex(self.source, r"input\s+double\s+TakeProfitPips\s*=\s*[1-9]")

    def test_uses_closed_bar_ema_10_60_crossovers(self) -> None:
        self.assertIn("const int   EMA_FAST_PERIOD = 10;", self.source)
        self.assertIn("const int   EMA_SLOW_PERIOD = 60;", self.source)
        self.assertEqual(self.source.count("MODE_EMA, PRICE_CLOSE"), 2)
        self.assertRegex(
            self.source,
            r"CopyBuffer\(gFastEmaHandle,\s*0,\s*2,\s*1,\s*fastPrevious\)",
        )
        self.assertRegex(
            self.source,
            r"CopyBuffer\(gFastEmaHandle,\s*0,\s*1,\s*1,\s*fastClosed\)",
        )
        self.assertRegex(
            self.source,
            r"CopyBuffer\(gSlowEmaHandle,\s*0,\s*2,\s*1,\s*slowPrevious\)",
        )
        self.assertRegex(
            self.source,
            r"CopyBuffer\(gSlowEmaHandle,\s*0,\s*1,\s*1,\s*slowClosed\)",
        )
        self.assertNotRegex(self.source, r"CopyBuffer\([^,\n]+,\s*0,\s*0,")
        self.assertIn(
            "fastPreviousValue <= slowPreviousValue && fastClosedValue > slowClosedValue",
            self.source,
        )
        self.assertIn(
            "fastPreviousValue >= slowPreviousValue && fastClosedValue < slowClosedValue",
            self.source,
        )

    def test_signal_sentinel_and_trade_api_are_unambiguous(self) -> None:
        self.assertRegex(self.source, r"(?m)^#define SIGNAL_NONE -1$")
        self.assertNotRegex(self.source, r"SIGNAL_NONE\s+(?:=\s*)?0\b")
        self.assertIn("#include <Trade/Trade.mqh>", self.source)
        self.assertRegex(self.source, r"\bCTrade\s+trade\s*;")
        self.assertIn("trade.Buy(", self.source)
        self.assertIn("trade.Sell(", self.source)
        self.assertIn("trade.PositionClose(ticket)", self.source)

    def test_is_hard_guarded_to_strategy_tester(self) -> None:
        self.assertRegex(
            self.source,
            r"if\s*\(\s*MQLInfoInteger\(MQL_TESTER\)\s*==\s*0\s*\)",
        )
        self.assertIn("return(INIT_FAILED);", self.source)
        forbidden = (
            "WebRequest(",
            "FileOpen(",
            "SocketCreate(",
            "SendNotification(",
            "ShellExecute",
            "TerminalClose(",
            "ExpertRemove(",
            "#import",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, self.source)

    def test_fixed_smoke_lot_is_broker_normalized(self) -> None:
        self.assertIn("const double SMOKE_LOT      = 0.01;", self.source)
        for token in (
            "SYMBOL_VOLUME_MIN",
            "SYMBOL_VOLUME_MAX",
            "SYMBOL_VOLUME_STEP",
            "MathRound(SMOKE_LOT / step)",
            "MathAbs(aligned - SMOKE_LOT)",
            "NormalizeDouble(aligned, VolumeDigits(step))",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.source)

    def test_pips_prices_and_broker_stop_level_are_normalized(self) -> None:
        self.assertIn("digits == 3 || digits == 5", self.source)
        self.assertIn("point * 10.0", self.source)
        self.assertIn("SYMBOL_TRADE_STOPS_LEVEL", self.source)
        self.assertIn("SYMBOL_TRADE_FREEZE_LEVEL", self.source)
        self.assertIn("SYMBOL_TRADE_TICK_SIZE", self.source)
        self.assertIn("MathCeil(ticks - 1e-9)", self.source)
        self.assertIn("MathFloor(ticks + 1e-9)", self.source)
        self.assertIn(
            "const double entryPrice = signal == SIGNAL_BUY ? tick.ask : tick.bid;",
            self.source,
        )
        self.assertIn(
            "MathMin(entryPrice - requestedSLDistance, tick.bid - brokerMinimum)",
            self.source,
        )
        self.assertIn(
            "MathMax(entryPrice + requestedTPDistance, tick.ask + brokerMinimum)",
            self.source,
        )
        self.assertIn(
            "MathMax(entryPrice + requestedSLDistance, tick.ask + brokerMinimum)",
            self.source,
        )
        self.assertIn(
            "MathMin(entryPrice - requestedTPDistance, tick.bid - brokerMinimum)",
            self.source,
        )
        self.assertIn(
            "stopLoss <= entryPrice - requestedSLDistance + 1e-9",
            self.source,
        )
        self.assertIn(
            "takeProfit >= entryPrice + requestedTPDistance - 1e-9",
            self.source,
        )
        self.assertIn(
            "stopLoss >= entryPrice + requestedSLDistance - 1e-9",
            self.source,
        )
        self.assertIn(
            "takeProfit <= entryPrice - requestedTPDistance + 1e-9",
            self.source,
        )

    def test_filling_mode_supports_valid_return_execution_symbols(self) -> None:
        self.assertNotIn("SetTypeFillingBySymbol", self.source)
        for token in (
            "SYMBOL_FILLING_MODE",
            "SYMBOL_TRADE_EXEMODE",
            "SYMBOL_FILLING_FOK",
            "SYMBOL_FILLING_IOC",
            "ORDER_FILLING_FOK",
            "ORDER_FILLING_IOC",
            "ORDER_FILLING_RETURN",
            "execution != SYMBOL_TRADE_EXECUTION_MARKET",
            "trade.SetTypeFilling(filling);",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.source)
        resolver = self.source[
            self.source.index("bool ResolveSmokeFillingMode(") : self.source.index(
                "bool OpenSignal("
            )
        ]
        self.assertLess(
            resolver.index("SYMBOL_FILLING_FOK"),
            resolver.index("SYMBOL_FILLING_IOC"),
        )
        self.assertLess(
            resolver.index("SYMBOL_FILLING_IOC"),
            resolver.index("ORDER_FILLING_RETURN"),
        )

    def test_enforces_one_position_per_symbol_and_magic_before_reverse(self) -> None:
        self.assertIn("PositionGetString(POSITION_SYMBOL) != _Symbol", self.source)
        self.assertIn("PositionGetInteger(POSITION_MAGIC) != SMOKE_MAGIC", self.source)
        self.assertIn("managedCount == 1 && currentDirection == signal", self.source)
        close_call = self.source.index("if(!CloseManagedPositions())")
        empty_check = self.source.index("CountManagedPositions(remainingDirection) != 0")
        open_call = self.source.index(
            "OpenSignal(signal, signalSeq, closedBarTime);"
        )
        self.assertLess(close_call, empty_check)
        self.assertLess(empty_check, open_call)

    def test_releases_both_indicator_handles(self) -> None:
        self.assertIn("IndicatorRelease(gFastEmaHandle);", self.source)
        self.assertIn("IndicatorRelease(gSlowEmaHandle);", self.source)
        self.assertRegex(
            self.source,
            r"gFastEmaHandle\s*==\s*INVALID_HANDLE\s*\|\|\s*"
            r"gSlowEmaHandle\s*==\s*INVALID_HANDLE",
        )

    def test_exposes_expected_and_executed_directional_proof(self) -> None:
        for token in (
            "gBuySignals",
            "gSellSignals",
            "gBuyEntries",
            "gSellEntries",
            "SMOKE_SIGNAL %s expected",
            'EMA_SMOKE_V1 {\\"event\\":\\"signal\\"',
            'EMA_SMOKE_V1 {\\"event\\":\\"entry\\"',
            'EMA_SMOKE_AUDIT_V1 {\\"event\\":\\"entry_fill\\"',
            'EMA_SMOKE_AUDIT_V1 {\\"event\\":\\"entry_fill_late\\"',
            'EMA_SMOKE_AUDIT_V1 {\\"event\\":\\"entry_complete\\"',
            'EMA_SMOKE_AUDIT_V1 {\\"event\\":\\"accepted\\"',
            'EMA_SMOKE_V1 {\\"event\\":\\"orphan_entry\\"',
            'EMA_SMOKE_AUDIT_V1 {\\"event\\":\\"order_finalized\\"',
            'EMA_SMOKE_AUDIT_V1 {\\"event\\":\\"entry_identity\\"',
            'EMA_SMOKE_V1 {\\"event\\":\\"final\\"',
            "Expected BUY signals",
            "Executed BUY entries",
            "Expected SELL signals",
            "Executed SELL entries",
            "OnTradeTransaction(",
            "TRADE_TRANSACTION_DEAL_ADD",
            "TRADE_TRANSACTION_REQUEST",
            "TRADE_TRANSACTION_ORDER_DELETE",
            "TRADE_TRANSACTION_HISTORY_ADD",
            "DEAL_ENTRY_IN",
            "DEAL_ENTRY_INOUT",
            "DEAL_ORDER",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.source)

    def test_transient_copybuffer_failure_retries_same_bar(self) -> None:
        self.assertIn("#define SIGNAL_DATA_UNAVAILABLE -2", self.source)
        self.assertIn('gLastOutcome = "data_unavailable";', self.source)
        self.assertIn('gLastOutcome = "no_signal";', self.source)
        on_tick = self.source[
            self.source.index("void OnTick()") : self.source.index(
                "void OnTradeTransaction("
            )
        ]
        read = on_tick.index("const int signal = ReadClosedBarSignal(")
        unavailable = on_tick.index("signal == SIGNAL_DATA_UNAVAILABLE")
        commit = on_tick.index("gLastBarOpenTime = currentBarOpenTime;")
        process = on_tick.index("ProcessSignal(")
        self.assertLess(read, unavailable)
        self.assertLess(unavailable, commit)
        self.assertLess(commit, process)

    def test_structured_telemetry_correlates_signal_pending_and_entry(self) -> None:
        signal_format = (
            'EMA_SMOKE_V1 {\\"event\\":\\"signal\\",\\"seq\\":%I64u,'
            '\\"direction\\":\\"%s\\",\\"closed_bar_time\\":%I64d,'
            '\\"fast_period\\":%d,\\"slow_period\\":%d,'
            '\\"previous_shift\\":2,\\"current_shift\\":1,'
            '\\"fast_2\\":%.10f,\\"fast_1\\":%.10f,'
            '\\"slow_2\\":%.10f,\\"slow_1\\":%.10f}'
        )
        self.assertIn(signal_format, self.source)
        for token in (
            "const ulong signalSeq = ++gSignalSequence;",
            "SetPendingSignal(signalSeq, signal, closedBarTime);",
            "gPendingSignalSeq = seq;",
            "gPendingDirection = direction;",
            "gPendingClosedBarTime = closedBarTime;",
            "gPendingRequestId = requestId;",
            "gPendingRequestIdentityBound = true;",
            "gPendingOrderTicket = orderTicket;",
            "gPendingAcceptedDealTicket = dealTicket;",
            "gPendingSignalSeq == 0 || !gPendingRequestIdentityBound",
            "gPendingDirection != direction || dealOrder == 0",
            "acceptedDealMatches",
            "acceptedOrderMatches",
            "MatchCompletedOrder(",
            "const ulong matchedSeq = gPendingSignalSeq;",
            "const datetime matchedClosedBarTime = gPendingClosedBarTime;",
            "++gOrphanEntries;",
            "++gPendingFillCount;",
            "if(!gPendingEntryCounted)",
            "gPendingEntryCounted = true;",
            "ClearPendingSignal();",
            'RejectSignal(seq, direction, closedBarTime, "pending_timeout");',
            'RejectSignal(seq, direction, closedBarTime, "deinit_pending");',
            '\\"signal\\":%d',
            '\\"entry\\":%d',
            '\\"rejected\\":%d',
            '\\"orphan\\":%d',
            '\\"pending\\":%d',
            '\\"data_unavailable\\":%d',
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.source)

        bind = self.source[
            self.source.index("bool BindPendingRequest(") : self.source.index(
                "void RememberCompletedOrder("
            )
        ]
        self.assertNotIn("requestId == 0", bind)
        self.assertIn("orderTicket == 0 && dealTicket == 0", bind)
        self.assertLess(
            bind.index("gPendingAcceptedDealTicket = dealTicket;"),
            bind.index("gPendingRequestIdentityBound = true;"),
        )
        transaction = self.source[
            self.source.index("void OnTradeTransaction(") : self.source.index(
                "double OnTester()"
            )
        ]
        self.assertIn(
            "gPendingSignalSeq != 0 && gPendingRequestIdentityBound &&",
            transaction,
        )

        process = self.source[
            self.source.index("void ProcessSignal(") : self.source.index(
                "int OnInit()"
            )
        ]
        self.assertIn(
            "EmitSignalEvent(\n"
            "      signalSeq,\n"
            "      signal,\n"
            "      closedBarTime,\n"
            "      fast2,\n"
            "      fast1,\n"
            "      slow2,\n"
            "      slow1\n"
            "   );",
            process,
        )
        open_signal = self.source[
            self.source.index("bool OpenSignal(") : self.source.index(
                "void ProcessSignal("
            )
        ]
        self.assertLess(
            open_signal.index("SetPendingSignal(signalSeq, signal, closedBarTime);"),
            min(open_signal.index("trade.Buy("), open_signal.index("trade.Sell(")),
        )
        self.assertLess(
            max(open_signal.index("trade.Buy("), open_signal.index("trade.Sell(")),
            open_signal.index("trade.Result(acceptedResult);"),
        )
        self.assertLess(
            open_signal.index("trade.Result(acceptedResult);"),
            open_signal.index("BindPendingRequest("),
        )

    def test_one_signal_is_one_logical_entry_across_split_fills(self) -> None:
        transaction = self.source[
            self.source.index("void OnTradeTransaction(") : self.source.index(
                "double OnTester()"
            )
        ]
        guard = transaction.index("if(!gPendingEntryCounted)")
        buy_count = transaction.index("++gBuyEntries;")
        sell_count = transaction.index("++gSellEntries;")
        first_entry = transaction.index(
            'EMA_SMOKE_V1 {\\"event\\":\\"entry\\"'
        )
        split_fill = transaction.index(
            'EMA_SMOKE_AUDIT_V1 {\\"event\\":\\"entry_fill\\"',
            first_entry,
        )
        self.assertLess(guard, buy_count)
        self.assertLess(guard, sell_count)
        self.assertLess(buy_count, first_entry)
        self.assertLess(sell_count, first_entry)
        self.assertGreater(split_fill, first_entry)
        self.assertEqual(transaction.count("++gBuyEntries;"), 1)
        self.assertEqual(transaction.count("++gSellEntries;"), 1)
        self.assertIn("transaction.deal == gPendingAcceptedDealTicket", transaction)
        self.assertIn("dealOrder == gPendingOrderTicket", transaction)

    def test_primary_execution_proof_stream_keeps_parser_exact_event_shapes(self) -> None:
        event_names = re.findall(
            r'EMA_SMOKE_V1 \{\\"event\\":\\"([^"\\]+)\\"',
            self.source,
        )
        self.assertEqual(
            sorted(set(event_names)),
            ["entry", "final", "orphan_entry", "pending", "rejected", "signal"],
        )
        self.assertIn(
            'EMA_SMOKE_V1 {\\"event\\":\\"entry\\",\\"seq\\":%I64u,'
            '\\"direction\\":\\"%s\\",\\"closed_bar_time\\":%I64d,'
            '\\"deal\\":%I64u}',
            self.source,
        )
        for audit_event in (
            "accepted",
            "order_finalized",
            "entry_fill",
            "entry_fill_late",
            "entry_complete",
            "entry_identity",
        ):
            with self.subTest(audit_event=audit_event):
                self.assertNotIn(
                    f'EMA_SMOKE_V1 {{\\"event\\":\\"{audit_event}\\"',
                    self.source,
                )
                self.assertIn(
                    f'EMA_SMOKE_AUDIT_V1 {{\\"event\\":\\"{audit_event}\\"',
                    self.source,
                )

    def test_position_cap_counts_positions_and_orders(self) -> None:
        for token in (
            "PositionsTotal()",
            "OrdersTotal()",
            "PositionGetString(POSITION_SYMBOL) != _Symbol",
            "OrderGetString(ORDER_SYMBOL) != _Symbol",
            "PositionGetInteger(POSITION_MAGIC) != SMOKE_MAGIC",
            "OrderGetInteger(ORDER_MAGIC) != SMOKE_MAGIC",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.source)


if __name__ == "__main__":
    unittest.main()
