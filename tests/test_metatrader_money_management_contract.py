from __future__ import annotations

import math
import json
import re
import unittest
from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MT4_SOURCE_PATH = (
    ROOT
    / "artifacts"
    / "mt4-ai-council-ea-v2.18-enum-fail-closed-readiness"
    / "MetafxHQTradeGateway.mq4"
)
MT5_SOURCE_PATH = (
    ROOT
    / "integrations"
    / "mt5-trade-gateway"
    / "MetafxHQTradeGateway.mq5"
)


class SizingRejected(ValueError):
    """The requested volume cannot be represented without increasing risk."""


WIRE_MONEY_MINIMUM = Decimal("0.00000001")
RISK_PERCENT_QUANTUM = Decimal("0.00000001")


def decimal_value(value: object, name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive type boundary
        raise SizingRejected(f"{name}_INVALID") from exc
    if not result.is_finite():
        raise SizingRejected(f"{name}_INVALID")
    return result


def is_on_broker_grid(
    volume: Decimal,
    minimum: Decimal,
    step: Decimal,
) -> bool:
    if volume < minimum:
        return False
    return (volume - minimum) % step == 0


@dataclass(frozen=True)
class SizingResult:
    volume: Decimal
    risk_budget: Decimal | None
    projected_loss: Decimal


def conservative_volume(
    *,
    mode: str,
    fixed_lot: object = "0.01",
    risk_percent: object = "1",
    balance: object = "0",
    equity: object = "0",
    risk_capital_base: str = "EQUITY",
    loss_per_lot: object,
    minimum: object,
    maximum: object,
    step: object,
    managed_cap: object | None = None,
) -> SizingResult:
    """Reference model for the fail-closed MT4/MT5 sizing contract.

    All monetary inputs use the account's native deposit unit.  That makes the
    result invariant when a cent account scales both capital and P/L by 100.
    Risk-percent volume is always rounded down on the broker grid; it is never
    raised to the minimum lot when doing so would exceed the risk budget.
    """

    minimum_d = decimal_value(minimum, "MINIMUM")
    maximum_d = decimal_value(maximum, "MAXIMUM")
    step_d = decimal_value(step, "STEP")
    loss_d = decimal_value(loss_per_lot, "LOSS_PER_LOT")
    if minimum_d <= 0 or maximum_d < minimum_d or step_d <= 0:
        raise SizingRejected("BROKER_VOLUME_LIMITS_INVALID")
    if loss_d <= 0:
        raise SizingRejected("LOSS_PER_LOT_INVALID")

    effective_maximum = maximum_d
    if managed_cap is not None:
        managed_cap_d = decimal_value(managed_cap, "MANAGED_CAP")
        if managed_cap_d <= 0:
            raise SizingRejected("MANAGED_CAP_INVALID")
        effective_maximum = min(effective_maximum, managed_cap_d)
    if effective_maximum < minimum_d:
        raise SizingRejected("CAP_BELOW_BROKER_MINIMUM")

    normalized_mode = mode.strip().upper()
    if normalized_mode == "FIXED_LOT":
        fixed_d = decimal_value(fixed_lot, "FIXED_LOT")
        if (
            fixed_d < minimum_d
            or fixed_d > effective_maximum
            or not is_on_broker_grid(fixed_d, minimum_d, step_d)
        ):
            raise SizingRejected("FIXED_LOT_INVALID")
        projected_loss = fixed_d * loss_d
        if projected_loss < WIRE_MONEY_MINIMUM:
            raise SizingRejected("RISK_ESTIMATE_BELOW_WIRE_MINIMUM")
        return SizingResult(
            volume=fixed_d,
            risk_budget=None,
            projected_loss=projected_loss,
        )
    if normalized_mode != "RISK_PERCENT":
        raise SizingRejected("MONEY_MANAGEMENT_MODE_INVALID")

    percent_d = decimal_value(risk_percent, "RISK_PERCENT").quantize(
        RISK_PERCENT_QUANTUM
    )
    if percent_d <= 0 or percent_d > 100:
        raise SizingRejected("RISK_PERCENT_INVALID")
    balance_d = decimal_value(balance, "BALANCE")
    equity_d = decimal_value(equity, "EQUITY")
    normalized_base = risk_capital_base.strip().upper()
    if normalized_base == "BALANCE":
        capital = balance_d
    elif normalized_base == "EQUITY":
        capital = equity_d
    else:
        raise SizingRejected("RISK_CAPITAL_BASE_INVALID")
    if capital <= 0:
        raise SizingRejected("RISK_CAPITAL_UNAVAILABLE")

    budget = capital * percent_d / Decimal("100")
    if budget < WIRE_MONEY_MINIMUM:
        raise SizingRejected("RISK_BUDGET_INVALID")
    raw_volume = budget / loss_d
    if raw_volume < minimum_d:
        raise SizingRejected("RISK_VOLUME_BELOW_BROKER_MINIMUM")

    capped_volume = min(raw_volume, effective_maximum)
    step_count = ((capped_volume - minimum_d) / step_d).to_integral_value(
        rounding=ROUND_FLOOR
    )
    volume = minimum_d + step_count * step_d
    while volume > capped_volume and volume >= minimum_d:
        volume -= step_d
    while volume >= minimum_d and volume * loss_d > budget:
        volume -= step_d
    if volume < minimum_d:
        raise SizingRejected("RISK_VOLUME_BELOW_BROKER_MINIMUM")
    if not is_on_broker_grid(volume, minimum_d, step_d):
        raise AssertionError("reference model produced an off-grid volume")
    projected_loss = volume * loss_d
    if projected_loss < WIRE_MONEY_MINIMUM:
        raise SizingRejected("RISK_ESTIMATE_BELOW_WIRE_MINIMUM")
    return SizingResult(
        volume=volume,
        risk_budget=budget,
        projected_loss=projected_loss,
    )


def linear_tick_loss_per_lot(
    *,
    entry_price: object,
    stop_price: object,
    tick_size_price: object,
    tick_value: object,
) -> Decimal:
    entry = decimal_value(entry_price, "ENTRY_PRICE")
    stop = decimal_value(stop_price, "STOP_PRICE")
    tick_size = decimal_value(tick_size_price, "TICK_SIZE")
    value = decimal_value(tick_value, "TICK_VALUE")
    if entry <= 0 or stop <= 0 or entry == stop:
        raise SizingRejected("STOP_DISTANCE_INVALID")
    if tick_size <= 0 or value <= 0:
        raise SizingRejected("BROKER_RISK_METADATA_INVALID")
    return abs(entry - stop) / tick_size * value


def strip_mql_comments(source: str) -> str:
    without_blocks = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"//[^\r\n]*", "", without_blocks)


class ConservativeMoneyManagementModelTests(unittest.TestCase):
    def test_fixed_and_percent_modes_are_distinct(self) -> None:
        fixed = conservative_volume(
            mode="fixed_lot",
            fixed_lot="0.25",
            # Risk inputs are deliberately unusable: fixed mode must not turn
            # them into hidden position-sizing authority.
            risk_percent="0",
            balance="0",
            equity="0",
            loss_per_lot="800",
            minimum="0.01",
            maximum="10",
            step="0.01",
        )
        percent = conservative_volume(
            mode="risk_percent",
            risk_percent="1",
            balance="10000",
            equity="10000",
            loss_per_lot="800",
            minimum="0.01",
            maximum="10",
            step="0.01",
        )
        self.assertEqual(fixed.volume, Decimal("0.25"))
        self.assertIsNone(fixed.risk_budget)
        self.assertEqual(percent.volume, Decimal("0.12"))
        self.assertEqual(percent.risk_budget, Decimal("100"))
        self.assertLessEqual(percent.projected_loss, percent.risk_budget)

    def test_risk_percent_uses_one_normalized_eight_decimal_value(self) -> None:
        result = conservative_volume(
            mode="risk_percent",
            risk_percent="1.123456789",
            balance="10000",
            equity="10000",
            loss_per_lot="100",
            minimum="0.00000001",
            maximum="10",
            step="0.00000001",
        )
        self.assertEqual(result.risk_budget, Decimal("112.3456790000"))
        self.assertEqual(result.volume, Decimal("1.12345679"))
        self.assertLessEqual(result.projected_loss, result.risk_budget)

    def test_risk_estimate_below_wire_minimum_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            SizingRejected,
            "RISK_ESTIMATE_BELOW_WIRE_MINIMUM",
        ):
            conservative_volume(
                mode="risk_percent",
                risk_percent="1.123456789",
                balance="10000",
                equity="10000",
                loss_per_lot="0.0000004",
                minimum="0.01",
                maximum="0.01",
                step="0.01",
            )

        with self.assertRaisesRegex(
            SizingRejected,
            "RISK_ESTIMATE_BELOW_WIRE_MINIMUM",
        ):
            conservative_volume(
                mode="fixed_lot",
                fixed_lot="0.01",
                risk_percent="0",
                loss_per_lot="0.0000004",
                minimum="0.01",
                maximum="10",
                step="0.01",
            )

    def test_standard_and_cent_account_scaling_produce_the_same_lot(self) -> None:
        standard = conservative_volume(
            mode="risk_percent",
            risk_percent="1",
            balance="1000",
            equity="1000",
            loss_per_lot="100",
            minimum="0.0001",
            maximum="100",
            step="0.0001",
        )
        cent = conservative_volume(
            mode="risk_percent",
            risk_percent="1",
            balance="100000",
            equity="100000",
            loss_per_lot="10000",
            minimum="0.0001",
            maximum="100",
            step="0.0001",
        )
        self.assertEqual(standard.volume, Decimal("0.1"))
        self.assertEqual(cent.volume, standard.volume)

    def test_standard_and_cent_commission_scaling_preserves_lot_and_wrong_units_overrisk(self) -> None:
        """Commission must use the same native account-money unit as P/L."""

        standard_gross_stop_loss = Decimal("930")
        standard_round_trip_commission = Decimal("7")
        cent_scale = Decimal("100")
        common = {
            "mode": "risk_percent",
            "risk_percent": "1",
            "minimum": "0.001",
            "maximum": "100",
            "step": "0.001",
        }

        standard = conservative_volume(
            **common,
            balance="10000",
            equity="10000",
            loss_per_lot=(
                standard_gross_stop_loss + standard_round_trip_commission
            ),
        )
        cent = conservative_volume(
            **common,
            balance="1000000",
            equity="1000000",
            loss_per_lot=(
                standard_gross_stop_loss * cent_scale
                + standard_round_trip_commission * cent_scale
            ),
        )

        self.assertEqual(standard.volume, Decimal("0.106"))
        self.assertEqual(cent.volume, standard.volume)
        self.assertEqual(cent.risk_budget, standard.risk_budget * cent_scale)
        self.assertEqual(
            cent.projected_loss,
            standard.projected_loss * cent_scale,
        )

        # Supplying `7` to an account whose terminal reports money in cents
        # means seven cents, not USD 7.  It produces a larger lot.  Revalue that
        # lot with the actual 700-cent round-trip cost to demonstrate the risk
        # budget overrun caused by the unit mistake.
        cent_with_wrong_unscaled_commission = conservative_volume(
            **common,
            balance="1000000",
            equity="1000000",
            loss_per_lot=(
                standard_gross_stop_loss * cent_scale
                + standard_round_trip_commission
            ),
        )
        self.assertGreater(
            cent_with_wrong_unscaled_commission.volume,
            cent.volume,
        )
        actual_cent_loss = cent_with_wrong_unscaled_commission.volume * (
            standard_gross_stop_loss * cent_scale
            + standard_round_trip_commission * cent_scale
        )
        self.assertGreater(
            actual_cent_loss,
            cent_with_wrong_unscaled_commission.risk_budget,
        )

    def test_supported_volume_steps_always_round_down(self) -> None:
        expected = {
            "0.1": "1.2",
            "0.01": "1.23",
            "0.001": "1.234",
            "0.0001": "1.2345",
            "0.25": "1.00",
        }
        for step, expected_volume in expected.items():
            with self.subTest(step=step):
                result = conservative_volume(
                    mode="risk_percent",
                    risk_percent="1",
                    balance="12345",
                    equity="12345",
                    loss_per_lot="100",
                    minimum=step,
                    maximum="100",
                    step=step,
                )
                self.assertEqual(result.volume, Decimal(expected_volume))
                self.assertLessEqual(result.projected_loss, result.risk_budget)
                self.assertTrue(
                    is_on_broker_grid(
                        result.volume,
                        Decimal(step),
                        Decimal(step),
                    )
                )

    def test_nonzero_broker_grid_origin_is_respected(self) -> None:
        result = conservative_volume(
            mode="risk_percent",
            risk_percent="1",
            balance="10200",
            equity="10200",
            loss_per_lot="100",
            minimum="0.10",
            maximum="10",
            step="0.25",
        )

        # Broker volumes are min + n*step, not necessarily n*step.
        self.assertEqual(result.volume, Decimal("0.85"))
        self.assertTrue(
            is_on_broker_grid(
                result.volume,
                Decimal("0.10"),
                Decimal("0.25"),
            )
        )
        self.assertLessEqual(result.projected_loss, result.risk_budget)

    def test_grid_origin_can_have_more_precision_than_the_step(self) -> None:
        result = conservative_volume(
            mode="risk_percent",
            risk_percent="1",
            balance="3.9",
            equity="3.9",
            loss_per_lot="1",
            minimum="0.005",
            maximum="1",
            step="0.01",
        )

        self.assertEqual(result.volume, Decimal("0.035"))
        self.assertTrue(
            is_on_broker_grid(
                result.volume,
                Decimal("0.005"),
                Decimal("0.01"),
            )
        )
        self.assertLessEqual(result.projected_loss, result.risk_budget)

    def test_commission_or_slippage_reserve_can_only_reduce_volume(self) -> None:
        baseline = conservative_volume(
            mode="risk_percent",
            risk_percent="1",
            balance="10000",
            equity="10000",
            loss_per_lot="800",
            minimum="0.01",
            maximum="10",
            step="0.01",
        )
        reserved = conservative_volume(
            mode="risk_percent",
            risk_percent="1",
            balance="10000",
            equity="10000",
            loss_per_lot="850",
            minimum="0.01",
            maximum="10",
            step="0.01",
        )

        self.assertEqual(baseline.volume, Decimal("0.12"))
        self.assertEqual(reserved.volume, Decimal("0.11"))
        self.assertLess(reserved.volume, baseline.volume)
        self.assertLessEqual(reserved.projected_loss, reserved.risk_budget)

    def test_below_minimum_is_rejected_instead_of_rounded_up(self) -> None:
        with self.assertRaisesRegex(
            SizingRejected,
            "RISK_VOLUME_BELOW_BROKER_MINIMUM",
        ):
            conservative_volume(
                mode="risk_percent",
                risk_percent="1",
                balance="100",
                equity="100",
                loss_per_lot="1000",
                minimum="0.01",
                maximum="100",
                step="0.01",
            )

    def test_symbol_and_managed_maximum_caps_are_honored(self) -> None:
        symbol_cap = conservative_volume(
            mode="risk_percent",
            risk_percent="10",
            balance="100000",
            equity="100000",
            loss_per_lot="10",
            minimum="0.01",
            maximum="0.50",
            step="0.01",
        )
        managed_cap = conservative_volume(
            mode="risk_percent",
            risk_percent="10",
            balance="100000",
            equity="100000",
            loss_per_lot="10",
            minimum="0.01",
            maximum="10",
            step="0.01",
            managed_cap="0.37",
        )
        self.assertEqual(symbol_cap.volume, Decimal("0.50"))
        self.assertEqual(managed_cap.volume, Decimal("0.37"))

    def test_balance_and_equity_bases_are_explicit(self) -> None:
        from_balance = conservative_volume(
            mode="risk_percent",
            risk_percent="1",
            balance="10000",
            equity="8000",
            risk_capital_base="BALANCE",
            loss_per_lot="1000",
            minimum="0.01",
            maximum="10",
            step="0.01",
        )
        from_equity = conservative_volume(
            mode="risk_percent",
            risk_percent="1",
            balance="10000",
            equity="8000",
            risk_capital_base="EQUITY",
            loss_per_lot="1000",
            minimum="0.01",
            maximum="10",
            step="0.01",
        )
        self.assertEqual(from_balance.volume, Decimal("0.10"))
        self.assertEqual(from_equity.volume, Decimal("0.08"))

    def test_buy_and_sell_stop_distances_are_symmetric(self) -> None:
        buy_loss = linear_tick_loss_per_lot(
            entry_price="1.10500",
            stop_price="1.10000",
            tick_size_price="0.00001",
            tick_value="1",
        )
        sell_loss = linear_tick_loss_per_lot(
            entry_price="1.10000",
            stop_price="1.10500",
            tick_size_price="0.00001",
            tick_value="1",
        )
        self.assertEqual(buy_loss, Decimal("500"))
        self.assertEqual(sell_loss, buy_loss)

    def test_invalid_and_zero_inputs_fail_closed(self) -> None:
        base = {
            "mode": "risk_percent",
            "risk_percent": "1",
            "balance": "10000",
            "equity": "10000",
            "loss_per_lot": "100",
            "minimum": "0.01",
            "maximum": "100",
            "step": "0.01",
        }
        mutations = (
            {"mode": "unknown"},
            {"risk_percent": "0"},
            {"risk_percent": "101"},
            {"risk_percent": math.nan},
            {"equity": "0"},
            {"loss_per_lot": "0"},
            {"loss_per_lot": math.inf},
            {"minimum": "0"},
            {"maximum": "0.001"},
            {"step": "0"},
            {"managed_cap": "0"},
            {"risk_capital_base": "FREE_MARGIN"},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                values = dict(base)
                values.update(mutation)
                with self.assertRaises(SizingRejected):
                    conservative_volume(**values)

    def test_dense_rounding_matrix_never_exceeds_the_budget(self) -> None:
        for step in ("0.1", "0.01", "0.001", "0.0001", "0.25"):
            minimum = Decimal(step)
            for raw_text in (
                "0.0001",
                "0.0011",
                "0.01001",
                "0.09999",
                "0.10001",
                "0.24999",
                "0.25001",
                "1.234567",
                "19.999999",
            ):
                raw = Decimal(raw_text)
                with self.subTest(step=step, raw=raw_text):
                    if raw < minimum:
                        with self.assertRaises(SizingRejected):
                            conservative_volume(
                                mode="risk_percent",
                                risk_percent="1",
                                balance=raw * Decimal("100"),
                                equity=raw * Decimal("100"),
                                loss_per_lot="1",
                                minimum=minimum,
                                maximum="100",
                                step=step,
                            )
                        continue
                    result = conservative_volume(
                        mode="risk_percent",
                        risk_percent="1",
                        balance=raw * Decimal("100"),
                        equity=raw * Decimal("100"),
                        loss_per_lot="1",
                        minimum=minimum,
                        maximum="100",
                        step=step,
                    )
                    self.assertLessEqual(result.volume, raw)
                    self.assertLessEqual(result.projected_loss, result.risk_budget)
                    self.assertTrue(
                        is_on_broker_grid(result.volume, minimum, Decimal(step))
                    )


class MetaTraderMoneyManagementStaticContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mt4 = strip_mql_comments(MT4_SOURCE_PATH.read_text(encoding="utf-8"))
        cls.mt5 = strip_mql_comments(MT5_SOURCE_PATH.read_text(encoding="utf-8"))
        cls.bridge_contract = json.loads(
            (ROOT / "contracts" / "bridge" / "bridge-contract.json").read_text(
                encoding="utf-8"
            )
        )
        cls.orchestration_contract = json.loads(
            (
                ROOT
                / "contracts"
                / "orchestration"
                / "orchestration-contract.json"
            ).read_text(encoding="utf-8")
        )

    def test_mt4_and_mt5_expose_the_same_money_management_inputs(self) -> None:
        required = (
            "enum ENUM_MONEY_MANAGEMENT_MODE",
            "MONEY_MANAGEMENT_FIXED_LOT = 0",
            "MONEY_MANAGEMENT_RISK_PERCENT = 1",
            "enum ENUM_RISK_CAPITAL_BASE",
            "RISK_CAPITAL_BALANCE = 0",
            "RISK_CAPITAL_EQUITY = 1",
            "input ENUM_MONEY_MANAGEMENT_MODE MoneyManagementMode = MONEY_MANAGEMENT_FIXED_LOT;",
            "input double FixedLot = 0.01;",
            "input double RiskPercent = 1.0;",
            "input ENUM_RISK_CAPITAL_BASE RiskCapitalBase = RISK_CAPITAL_EQUITY;",
        )
        for platform, source in (("MT4", self.mt4), ("MT5", self.mt5)):
            for token in required:
                with self.subTest(platform=platform, token=token):
                    self.assertTrue(
                        token in source,
                        f"{platform} missing money-management input {token!r}",
                    )

    def test_mt4_and_mt5_publish_the_same_sizing_telemetry_names(self) -> None:
        telemetry_fields = (
            "positionSizingMode",
            "riskPercent",
            "riskCapitalBase",
            "riskCapitalAmount",
            "estimatedRiskMoney",
            "brokerVolumeMin",
            "brokerVolumeMax",
            "brokerVolumeStep",
        )
        for platform, source in (("MT4", self.mt4), ("MT5", self.mt5)):
            for field in telemetry_fields:
                with self.subTest(platform=platform, field=field):
                    self.assertTrue(
                        f'\\"{field}\\"' in source,
                        f"{platform} missing sizing telemetry field {field!r}",
                    )

    def test_ai_contracts_explicitly_forbid_all_ea_owned_sizing_inputs(self) -> None:
        bridge_policy = self.bridge_contract["runner_mode"]["mt4_trade_gateway"]
        ea_owned_sizing = {
            "moneyManagementMode",
            "fixedLot",
            "riskPercent",
            "riskCapitalBase",
            "estimatedCommissionPerLot",
        }
        self.assertTrue(
            ea_owned_sizing.issubset(set(bridge_policy["eaOwnedInputs"]))
        )
        self.assertTrue(
            ea_owned_sizing.issubset(set(bridge_policy["forbiddenAiSignalFields"]))
        )
        self.assertIn("mode", bridge_policy["forbiddenAiSignalFields"])
        orchestration_policy = self.orchestration_contract[
            "aiTradeCouncilAutoAnalysis"
        ]["consensusPolicy"]
        self.assertTrue(
            ea_owned_sizing.issubset(set(orchestration_policy["forbiddenAiFields"]))
        )
        self.assertIn("mode", orchestration_policy["forbiddenAiFields"])

    def test_platform_specific_risk_valuation_and_margin_guards_exist(self) -> None:
        for token in (
            "MODE_TICKVALUE",
            "MODE_TICKSIZE",
            "MODE_MINLOT",
            "MODE_MAXLOT",
            "MODE_LOTSTEP",
            "AccountFreeMarginCheck",
        ):
            with self.subTest(platform="MT4", token=token):
                self.assertTrue(
                    token in self.mt4,
                    f"MT4 missing broker sizing guard {token!r}",
                )
        for token in (
            "OrderCalcProfit",
            "SYMBOL_VOLUME_MIN",
            "SYMBOL_VOLUME_MAX",
            "SYMBOL_VOLUME_STEP",
            "OrderCalcMargin",
            "OrderCheck",
        ):
            with self.subTest(platform="MT5", token=token):
                self.assertTrue(
                    token in self.mt5,
                    f"MT5 missing broker sizing guard {token!r}",
                )

    def test_both_platforms_fail_closed_on_unrepresentable_risk(self) -> None:
        reasons = (
            "RISK_PERCENT_INVALID_OR_ABOVE_HARD_CAP",
            "RISK_STOP_LOSS_CALCULATION_FAILED",
            "RISK_VOLUME_BELOW_BROKER_MINIMUM",
            "RISK_ESTIMATE_BELOW_WIRE_MINIMUM",
            "ORDER_VOLUME_NOT_ON_BROKER_STEP",
        )
        for platform, source in (("MT4", self.mt4), ("MT5", self.mt5)):
            for reason in reasons:
                with self.subTest(platform=platform, reason=reason):
                    self.assertTrue(
                        reason in source,
                        f"{platform} missing fail-closed reason {reason!r}",
                    )


if __name__ == "__main__":
    unittest.main()
