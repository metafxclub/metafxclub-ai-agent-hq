from __future__ import annotations

import importlib.util
import math
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location("bridge_core20_test", BRIDGE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def synthetic_bars(count: int = 1000) -> list[dict]:
    bars = []
    for index in range(count):
        close = (
            2000.0
            + (index * 0.15)
            + (25.0 * math.sin(index / 12.0))
            + (7.0 * math.sin(index / 3.0))
        )
        open_price = close - (2.0 * math.sin(index))
        bars.append({
            "time": 1_700_000_000 + (index * 300),
            "open": open_price,
            "high": max(open_price, close) + 3.0 + (index % 3),
            "low": min(open_price, close) - 3.0 - (index % 2),
            "close": close,
            "volume": 100.0 + (index % 40),
        })
    return bars


class AiTradeCouncilBackendCore20Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        with self.bridge.AI_TRADE_COUNCIL_ANALYSIS_CACHE_LOCK:
            self.bridge.AI_TRADE_COUNCIL_ANALYSIS_CACHE.clear()

    def test_core20_is_split_between_technical_and_price_action(self) -> None:
        self.assertEqual(self.bridge.METATRADER_SNAPSHOT_MAX_BARS, 1000)
        self.assertEqual(
            self.bridge.AI_TRADE_COUNCIL_ALLOWED_ANALYSIS_BAR_COUNTS,
            (120, 180, 240, 300, 500, 1000),
        )
        bundle = self.bridge._ai_trade_council_analysis_feature_bundle(
            synthetic_bars()
        )
        technical = bundle["technicalIndicators"]
        price_action = bundle["priceActionFeatures"]
        self.assertEqual(technical["moduleCount"], 14)
        self.assertEqual(price_action["moduleCount"], 6)
        self.assertEqual(
            technical["formulaVersion"],
            "metafx-deterministic-core20-price-action-v3",
        )
        self.assertEqual(price_action["formulaVersion"], technical["formulaVersion"])
        self.assertTrue(technical["available"])
        self.assertTrue(price_action["available"])

    def test_all_standard_indicator_outputs_have_null_warmups(self) -> None:
        bars = synthetic_bars()
        technical = self.bridge._technical_indicator_snapshot(bars)
        self.assertEqual(len(technical["series"]), 1000)
        for field in (
            "sma20",
            "sma50",
            "sma200",
            "ema9",
            "ema20",
            "ema50",
            "ema200",
            "rsi14",
            "macdLine",
            "macdSignal",
            "macdHistogram",
            "stochasticK",
            "stochasticD",
            "atr14",
            "bollingerMiddle",
            "bollingerUpper",
            "bollingerLower",
            "adx14",
            "plusDI14",
            "minusDI14",
            "cci20",
            "williamsR14",
            "roc12",
            "momentum10",
            "obv",
            "mfi14",
            "volumeMA20",
        ):
            self.assertIn(field, technical)
            self.assertIsNotNone(technical[field], field)
        first = technical["series"][0]
        self.assertIsNone(first["sma20"])
        self.assertIsNone(first["ema9"])
        self.assertIsNone(first["rsi14"])
        self.assertIsNone(first["adx14"])
        self.assertEqual(first["obv"], 0.0)

    def test_flat_market_indicator_baseline_is_deterministic(self) -> None:
        bars = [
            {
                "time": 1_700_000_000 + (index * 300),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
                "volume": 10.0,
            }
            for index in range(240)
        ]
        technical = self.bridge._technical_indicator_snapshot(bars)
        self.assertEqual(technical["rsi14"], 50.0)
        self.assertEqual(technical["stochasticK"], 50.0)
        self.assertEqual(technical["stochasticD"], 50.0)
        self.assertEqual(technical["adx14"], 0.0)
        self.assertEqual(technical["cci20"], 0.0)
        self.assertEqual(technical["williamsR14"], -50.0)
        self.assertEqual(technical["roc12"], 0.0)
        self.assertEqual(technical["momentum10"], 100.0)
        self.assertEqual(technical["obv"], 0.0)
        self.assertEqual(technical["mfi14"], 50.0)

    def test_closed_bar_calculation_has_no_future_leakage(self) -> None:
        bars = synthetic_bars()
        prefix = self.bridge._technical_indicator_snapshot(bars[:500])
        full = self.bridge._technical_indicator_snapshot(bars)
        at_prefix_end = full["series"][499]
        for field in (
            "sma200",
            "ema200",
            "rsi14",
            "macdHistogram",
            "stochasticD",
            "atr14",
            "bollingerUpper",
            "adx14",
            "cci20",
            "williamsR14",
            "roc12",
            "momentum10",
            "obv",
            "mfi14",
            "volumeMA20",
        ):
            self.assertEqual(prefix[field], at_prefix_end[field], field)
        prefix_highs, prefix_lows = self.bridge._price_action_confirmed_pivots(
            bars[:500]
        )
        full_highs, full_lows = self.bridge._price_action_confirmed_pivots(bars)
        prefix_end_time = bars[499]["time"]
        self.assertEqual(
            prefix_highs,
            [item for item in full_highs if item["confirmedAtTime"] <= prefix_end_time],
        )
        self.assertEqual(
            prefix_lows,
            [item for item in full_lows if item["confirmedAtTime"] <= prefix_end_time],
        )
        self.assertTrue(
            all(item["confirmedAtTime"] > item["time"] for item in prefix_highs + prefix_lows)
        )

    def test_price_action_shape_and_regular_divergence_evidence(self) -> None:
        features = self.bridge._price_action_features_snapshot(synthetic_bars())
        self.assertTrue(features["pivotConfig"]["confirmedOnly"])
        self.assertEqual(len(features["fibonacci"]["levels"]), 7)
        self.assertIn(features["fibonacci"]["direction"], {"UP", "DOWN"})
        self.assertIn("support", features["trendlines"])
        self.assertIn("resistance", features["trendlines"])

        pivots = [
            {"index": 10, "time": 10, "confirmedAtTime": 13, "price": 100.0, "type": "LOW"},
            {"index": 20, "time": 20, "confirmedAtTime": 23, "price": 95.0, "type": "LOW"},
        ]
        oscillator = [None] * 21
        oscillator[10] = 30.0
        oscillator[20] = 40.0
        signal = self.bridge._price_action_regular_divergence(
            pivots,
            oscillator,
            oscillator="RSI14",
            bullish=True,
        )
        self.assertEqual(signal["kind"], "REGULAR_BULLISH")
        self.assertEqual(signal["detectedAtTime"], 23)
        self.assertEqual(signal["first"]["oscillatorValue"], 30.0)
        self.assertEqual(signal["second"]["oscillatorValue"], 40.0)

    def test_analysis_cache_is_bounded_and_returns_defensive_copies(self) -> None:
        first = self.bridge._ai_trade_council_analysis_feature_bundle(
            synthetic_bars(120)
        )
        first["technicalIndicators"]["rsi14"] = -999
        second = self.bridge._ai_trade_council_analysis_feature_bundle(
            synthetic_bars(120)
        )
        self.assertNotEqual(second["technicalIndicators"]["rsi14"], -999)
        for size in range(121, 131):
            self.bridge._ai_trade_council_analysis_feature_bundle(
                synthetic_bars(size)
            )
        self.assertLessEqual(
            len(self.bridge.AI_TRADE_COUNCIL_ANALYSIS_CACHE),
            self.bridge.AI_TRADE_COUNCIL_ANALYSIS_CACHE_MAX_ENTRIES,
        )

    def test_dashboard_keeps_1000_overlay_points_while_codex_window_stays_300(self) -> None:
        bars = synthetic_bars(1000)
        dashboard = self.bridge._ai_trade_council_dashboard_feature_state(
            bars,
            300,
        )
        display = dashboard["displayFeatures"]
        self.assertEqual(len(display["technicalIndicators"]["series"]), 1000)
        self.assertEqual(display["technicalIndicators"]["seriesBarCount"], 1000)
        self.assertEqual(display["technicalIndicators"]["scope"], "dashboard_source_window")
        self.assertEqual(display["priceActionFeatures"]["barCount"], 1000)
        self.assertEqual(dashboard["analysisWindow"]["usedBars"], 300)
        self.assertEqual(
            len(dashboard["analysisFeatures"]["technicalIndicators"]["series"]),
            300,
        )

        source = {
            "dailySummary": {"available": True},
            "chartSnapshot": {
                "available": True,
                "snapshotId": "a" * 64,
                "bars": bars,
                **display,
            },
        }
        windowed = self.bridge._ai_trade_council_windowed_snapshot(source, 300)
        chart = windowed["chartSnapshot"]
        self.assertEqual(len(chart["bars"]), 300)
        self.assertEqual(chart["bars"][0]["time"], bars[700]["time"])
        self.assertEqual(len(chart["technicalIndicators"]["series"]), 300)
        self.assertEqual(chart["technicalIndicators"]["scope"], "codex_analysis_window")
        self.assertEqual(chart["technicalIndicators"]["seriesBarCount"], 300)
        self.assertEqual(chart["priceActionFeatures"]["barCount"], 300)
        self.assertEqual(chart["priceActionFeatures"]["scope"], "codex_analysis_window")


if __name__ == "__main__":
    unittest.main()
