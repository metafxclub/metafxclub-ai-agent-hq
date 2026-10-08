from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MT4_SOURCE_PATH = (
    ROOT
    / "integrations"
    / "mt4-trade-gateway"
    / "MetafxHQTradeGateway.mq4"
)
MT5_SOURCE_PATH = (
    ROOT
    / "integrations"
    / "mt5-trade-gateway"
    / "MetafxHQTradeGateway.mq5"
)
BRIDGE_SOURCE_PATH = ROOT / "backend" / "local-runner" / "bridge_server.py"


def strip_mql_comments(source: str) -> str:
    without_blocks = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"//[^\r\n]*", "", without_blocks)


def function_body(source: str, name: str) -> str:
    """Return one MQL/Python-style braced function body without regex nesting bugs."""

    signature = re.search(rf"\b{name}\s*\([^)]*\)\s*\{{", source)
    if signature is None:
        raise AssertionError(f"function {name!r} not found")
    opening = source.find("{", signature.start())
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1 : index]
    raise AssertionError(f"function {name!r} has no closing brace")


def canonical_policy_fields(source: str) -> list[str]:
    body = function_body(source, "BuildPortfolioPolicyCanonical")
    fields = ["schema"]
    fields.extend(re.findall(r'canonical\s*\+=\s*"\|([^=\"]+)=', body))
    return fields


class TradeGatewayCrossPlatformContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mt4 = strip_mql_comments(MT4_SOURCE_PATH.read_text(encoding="utf-8"))
        cls.mt5 = strip_mql_comments(MT5_SOURCE_PATH.read_text(encoding="utf-8"))
        cls.bridge = BRIDGE_SOURCE_PATH.read_text(encoding="utf-8")

    def test_account_portfolio_policy_has_identical_cross_platform_semantics(self) -> None:
        expected = [
            "schema",
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
        ]
        self.assertEqual(canonical_policy_fields(self.mt4), expected)
        self.assertEqual(canonical_policy_fields(self.mt5), expected)
        for platform, source in (("MT4", self.mt4), ("MT5", self.mt5)):
            body = function_body(source, "BuildPortfolioPolicyCanonical")
            with self.subTest(platform=platform):
                self.assertIn("PositionSizingModeName()", body)
                self.assertIn("DoubleToString(EffectiveRiskPercent(), 8)", body)
                self.assertIn("RiskCapitalBaseName()", body)
                self.assertIn(
                    "DoubleToString(EffectiveEstimatedCommissionPerLot(), 8)",
                    body,
                )
                self.assertIn("CommissionFreeAccountConfirmed", body)

    def test_live_commission_and_symbol_policy_are_explicit_and_fail_closed(self) -> None:
        for platform, source, chart_symbol in (
            ("MT4", self.mt4, "Symbol()"),
            ("MT5", self.mt5, "_Symbol"),
        ):
            commission = function_body(source, "LiveCommissionPolicyConfirmed")
            exact_symbol = function_body(source, "LiveSymbolExactAllowlistConfirmed")
            configuration = function_body(
                source,
                "ValidateMoneyManagementConfiguration",
            )
            runtime = function_body(source, "ValidateRuntime")
            status = function_body(source, "BuildStatusJson")
            with self.subTest(platform=platform):
                self.assertIn(
                    "input bool CommissionFreeAccountConfirmed = false;",
                    source,
                )
                self.assertIn("NormalizeDouble(EstimatedCommissionPerLot, 8)", source)
                self.assertIn(
                    "EffectiveEstimatedCommissionPerLot() >= 0.00000001",
                    commission,
                )
                self.assertIn("CommissionFreeAccountConfirmed", commission)
                self.assertIn("GatewayMode == GATEWAY_LIVE", configuration)
                self.assertIn("!LiveCommissionPolicyConfirmed()", configuration)
                self.assertIn('"LIVE_COMMISSION_POLICY_UNCONFIRMED"', configuration)
                self.assertIn(f"CsvContains(AllowedSymbols, {chart_symbol})", exact_symbol)
                self.assertIn("GatewayMode == GATEWAY_LIVE", runtime)
                self.assertIn("CsvContains(AllowedSymbols, command.symbol)", runtime)
                self.assertIn('"LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST"', runtime)
                self.assertIn(r'\"commissionFreeAccountConfirmed\"', status)

    def test_backend_rechecks_live_policy_for_pre_hardening_status(self) -> None:
        """A readable older heartbeat must never recover Live execution authority."""

        self.assertIn(
            'MT4_TRADE_GATEWAY_STATUS_FIELDS - {"commissionFreeAccountConfirmed"}',
            self.bridge,
        )
        self.assertIn(
            'MT5_TRADE_GATEWAY_STATUS_FIELDS - {"commissionFreeAccountConfirmed"}',
            self.bridge,
        )
        read_model_start = self.bridge.index(
            "def mt4_trade_gateway_status_read_model("
        )
        read_model_end = self.bridge.index("\ndef ", read_model_start + 5)
        read_model = self.bridge[read_model_start:read_model_end]
        for token in (
            "commission_policy_ready = bool(",
            "float(estimated_commission_per_lot) >= 0.00000001",
            'ea_status.get("commissionFreeAccountConfirmed") is True',
            "exact_symbol_allowlist_ready = bool(",
            'str(ea_status.get("allowedSymbols") or "").split(",")',
            "live_local_policy_ready = bool(",
            "and live_local_policy_ready",
            '"LIVE_COMMISSION_POLICY_UNCONFIRMED"',
            '"LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST"',
            '"live_commission_policy_unconfirmed"',
            '"live_symbol_requires_exact_allowlist"',
        ):
            with self.subTest(token=token):
                self.assertIn(token, read_model)

    def test_pre_hardening_live_heartbeat_is_observable_but_cannot_bypass_gates(
        self,
    ) -> None:
        # Reuse the real bridge fixture without exporting its TestCase into this
        # module (which would make unittest discover the whole suite twice).
        from tests import test_mt4_trade_gateway_bridge as bridge_tests

        fixture_type = bridge_tests.Mt4TradeGatewayBridgeTests
        fixture_type.setUpClass()
        fixture = fixture_type(
            "test_snapshot_symbol_boundary_accepts_hash_but_not_plus_suffix"
        )
        fixture.setUp()
        try:
            common = {
                "mode": "live",
                "demoAccount": False,
                "accountMode": "live",
                "liveArmed": True,
                "autoTradingAllowed": True,
                "tradeAllowed": True,
                "positionSizingMode": "RISK_PERCENT",
                "riskPercent": 1.0,
                "riskCapitalBase": "EQUITY",
                "brokerVolumeMin": 0.01,
                "brokerVolumeMax": 100.0,
                "brokerVolumeStep": 0.01,
            }

            # The pre-hardening wire shape intentionally omits the new bool.
            fixture.write_ea_status(
                **common,
                estimatedCommissionPerLot=0.0,
            )
            with fixture.selected_candidate():
                zero_reserve = fixture.bridge.mt4_trade_gateway_status_read_model()
            self.assertTrue(zero_reserve["connected"])
            self.assertIsNone(zero_reserve["commissionFreeAccountConfirmed"])
            self.assertEqual(
                zero_reserve["executionGuardReason"],
                "LIVE_COMMISSION_POLICY_UNCONFIRMED",
            )
            self.assertEqual(
                zero_reserve["reasonCode"],
                "live_commission_policy_unconfirmed",
            )
            self.assertFalse(zero_reserve["liveOrderExecutionAvailable"])

            # A positive native-account-currency reserve is sufficient even for
            # an older sender that cannot publish the explicit free-account bool.
            fixture.write_ea_status(
                **common,
                estimatedCommissionPerLot=7.0,
            )
            with fixture.selected_candidate():
                positive_reserve = (
                    fixture.bridge.mt4_trade_gateway_status_read_model()
                )
            self.assertEqual(positive_reserve["status"], "live_ready")
            self.assertTrue(positive_reserve["liveOrderExecutionAvailable"])

            # Broker-affix compatibility is deliberately non-Live only.  An
            # older heartbeat cannot authorize a prefixed chart from XAUUSD.
            fixture.write_ea_status(
                **common,
                estimatedCommissionPerLot=7.0,
                symbol="MXAUUSD",
                allowedSymbols="XAUUSD",
            )
            with fixture.selected_candidate():
                affix_only = fixture.bridge.mt4_trade_gateway_status_read_model()
            self.assertEqual(
                affix_only["executionGuardReason"],
                "LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST",
            )
            self.assertEqual(
                affix_only["reasonCode"],
                "live_symbol_requires_exact_allowlist",
            )
            self.assertFalse(affix_only["liveOrderExecutionAvailable"])
        finally:
            fixture.tearDown()

    def test_account_execution_lock_uses_one_cross_platform_namespace(self) -> None:
        for platform, source in (("MT4", self.mt4), ("MT5", self.mt5)):
            identity = function_body(source, "AccountIdentityDigest")
            lock_path = function_body(source, "AccountExecutionLockPath")
            with self.subTest(platform=platform):
                self.assertIn('"MT4|"', identity)
                self.assertIn('"|" + server', identity)
                self.assertIn(
                    '"MetafxHQ\\\\locks\\\\account-execution-" + account_digest + ".lock"',
                    lock_path,
                )

    def test_broker_symbol_affixes_are_bounded_and_consistent(self) -> None:
        for platform, source in (("MT4", self.mt4), ("MT5", self.mt5)):
            prefix = function_body(source, "IsAllowedBrokerPrefix")
            matcher = function_body(source, "IsAllowedBrokerSymbol")
            with self.subTest(platform=platform):
                self.assertIn("prefix_length > 8", prefix)
                self.assertIn("prefix_length == 1", prefix)
                self.assertIn("IsBrokerNamespaceDelimiter(", prefix)
                self.assertIn("prefix_length - 1", prefix)
                self.assertIn("suffix_length > 8", matcher)
                self.assertIn("IsAllowedBrokerPrefix(", matcher)
                self.assertIn("IsBrokerSuffixCharacter(", matcher)
                self.assertTrue(
                    "canonical_matches != 1" in matcher
                    or "HasSingleBrokerBaseOccurrence(" in matcher,
                    f"{platform} must reject candidates containing the base twice",
                )

    def test_risk_sizing_uses_native_account_money_and_never_clamps_up(self) -> None:
        mt4_metadata = function_body(self.mt4, "ReadBrokerRiskMetadata")
        mt4_rounding = function_body(self.mt4, "NormalizeRiskVolumeDown")
        mt4_resolve = function_body(self.mt4, "ResolvePositionSize")
        self.assertIn("MODE_TICKVALUE", mt4_metadata)
        self.assertIn("MODE_TICKSIZE", mt4_metadata)
        self.assertIn("MODE_POINT", mt4_metadata)
        self.assertNotIn("AccountCurrency", mt4_metadata)
        self.assertIn("capped_lots < minimum", mt4_rounding)
        self.assertIn('reason = "RISK_VOLUME_BELOW_BROKER_MINIMUM"', mt4_rounding)
        self.assertIn("MathFloor(", mt4_rounding)
        self.assertIn("resolved_lots - step", mt4_resolve)

        mt5_resolve = function_body(self.mt5, "ResolveOrderVolume")
        self.assertGreaterEqual(mt5_resolve.count("OrderCalcProfit("), 2)
        self.assertIn("raw_volume + 0.00000001 < minimum", mt5_resolve)
        self.assertIn('reason = "RISK_VOLUME_BELOW_BROKER_MINIMUM"', mt5_resolve)
        self.assertIn("MathFloor(", mt5_resolve)
        self.assertIn("volume - step", mt5_resolve)
        self.assertIn("OrderCalcMargin(", mt5_resolve)

    def test_broker_variance_and_execution_fail_closed_guards_exist(self) -> None:
        mt4_required = (
            "MODE_MINLOT",
            "MODE_MAXLOT",
            "MODE_LOTSTEP",
            "MODE_STOPLEVEL",
            "MODE_TRADEALLOWED",
            "AccountFreeMarginCheck",
            '"SPREAD_LIMIT_EXCEEDED"',
            '"QUOTE_STALE"',
            '"BROKER_QUOTE_TIME_STALE"',
            '"EXECUTION_UNKNOWN"',
            '"DUPLICATE"',
        )
        mt5_required = (
            "SYMBOL_VOLUME_MIN",
            "SYMBOL_VOLUME_MAX",
            "SYMBOL_VOLUME_STEP",
            "SYMBOL_VOLUME_LIMIT",
            "SYMBOL_TRADE_STOPS_LEVEL",
            "SYMBOL_TRADE_FREEZE_LEVEL",
            "SYMBOL_TRADE_MODE",
            "OrderCheck(request, check_result)",
            '"SPREAD_LIMIT_EXCEEDED"',
            '"QUOTE_STALE_OR_FUTURE"',
            '"EXECUTION_UNKNOWN"',
            '"DUPLICATE"',
        )
        for platform, source, required in (
            ("MT4", self.mt4, mt4_required),
            ("MT5", self.mt5, mt5_required),
        ):
            for token in required:
                with self.subTest(platform=platform, token=token):
                    self.assertIn(token, source)

    def test_live_is_opt_in_and_backend_has_one_atomic_selected_authority(self) -> None:
        for platform, source in (("MT4", self.mt4), ("MT5", self.mt5)):
            with self.subTest(platform=platform):
                self.assertIn(
                    "input ENUM_GATEWAY_MODE GatewayMode = GATEWAY_SHADOW;",
                    source,
                )
                self.assertIn("input bool LiveArmed = false;", source)
                self.assertIn("LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT", source)
                self.assertIn("LIVE_SIGNING_KEY_PIN_REQUIRED", source)

        self.assertIn(
            "MT4_TRADE_GATEWAY_LOCK = METATRADER_TARGETS_LOCK",
            self.bridge,
        )
        publish_start = self.bridge.index("def _mt4_trade_gateway_publish_for_selection(")
        publish_end = self.bridge.index("\ndef ", publish_start + 5)
        publish = self.bridge[publish_start:publish_end]
        self.assertIn("with MT4_TRADE_GATEWAY_LOCK:", publish)
        self.assertIn('current_selection.get("candidateId")', publish)
        self.assertIn('current_selection.get("selectionRevision")', publish)
        self.assertIn("expected_selection_revision", publish)

        switch_start = self.bridge.index(
            "def _assert_ai_trade_council_target_switch_safe_unlocked("
        )
        switch_end = self.bridge.index("\ndef ", switch_start + 5)
        switch_guard = self.bridge[switch_start:switch_end]
        for token in (
            "quarantinedExecutionUnknown",
            "activeCommandId",
            "executionUnknown",
            "gateway_status_not_observed",
            "currentManagedPositions",
            "target_switch_managed_positions_open",
        ):
            with self.subTest(switch_token=token):
                self.assertIn(token, switch_guard)


if __name__ == "__main__":
    unittest.main()
