from __future__ import annotations

import copy
import importlib.util
import math
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_RUNNER = PROJECT_ROOT / "backend" / "local-runner"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, LOCAL_RUNNER / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def closed_bars(count: int = 240) -> list[dict]:
    bars = []
    for index in range(count):
        close = 100.0 + index * 0.04 + math.sin(index / 4.0) * 3.0
        bars.append({
            "time": 1_700_000_000 + index * 300,
            "open": close - 0.2,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": 10.0 + index % 5,
        })
    return bars


class CouncilAnalysisModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Load the calculation module directly: no Bridge, runtime, or terminal.
        cls.analysis = load_module(
            "isolated_council_analysis_test", "hq_backend/trading/council_analysis.py"
        )

    def test_invalid_closed_bars_keep_both_feature_families_unavailable(self) -> None:
        invalid_rows = [
            None,
            {"open": None},
            {"time": True},
            {"time": 0},
            {"close": float("nan")},
            {"high": float("inf")},
            {"low": 0},
            {"volume": -1},
            {"high": 1},
            {"low": 1000},
        ]
        for override in invalid_rows:
            with self.subTest(override=override):
                bars = closed_bars()
                bars[-1] = None if override is None else {**bars[-1], **override}
                technical = self.analysis._technical_indicator_snapshot_uncached(bars)
                price_action = self.analysis._price_action_features_snapshot_uncached(
                    bars, technical
                )
                for features in (technical, price_action):
                    self.assertFalse(features["available"])
                    self.assertEqual(features["reasonCode"], "invalid_closed_bar_payload")
                    self.assertEqual(features["barCount"], len(bars))

    def test_empty_and_warmup_windows_preserve_unknown_values(self) -> None:
        empty = self.analysis._technical_indicator_snapshot_uncached([])
        self.assertFalse(empty["available"])
        self.assertEqual(empty["series"], [])

        warmup = self.analysis._technical_indicator_snapshot_uncached(closed_bars(12))
        self.assertEqual(len(warmup["series"]), 12)
        for field in ("sma200", "ema200", "rsi14", "atr14", "macdSignal"):
            self.assertIsNone(warmup[field], field)
        self.assertIsNotNone(warmup["ema9"])

    def test_future_bars_do_not_rewrite_existing_series_or_confirmed_pivots(self) -> None:
        bars = closed_bars()
        prefix = bars[:120]
        prefix_features = self.analysis._technical_indicator_snapshot_uncached(prefix)
        full_features = self.analysis._technical_indicator_snapshot_uncached(bars)
        self.assertEqual(prefix_features["series"], full_features["series"][:120])

        prefix_pivots = self.analysis._price_action_confirmed_pivots(prefix)
        full_pivots = self.analysis._price_action_confirmed_pivots(bars)
        for before, after in zip(prefix_pivots, full_pivots):
            self.assertTrue(before)
            self.assertEqual(before, [
                pivot for pivot in after
                if pivot["confirmedAtTime"] <= prefix[-1]["time"]
            ])

    def test_direct_calculation_does_not_mutate_input_or_retain_output_state(self) -> None:
        bars = closed_bars()
        original = copy.deepcopy(bars)
        technical = self.analysis._technical_indicator_snapshot_uncached(bars)
        price_action = self.analysis._price_action_features_snapshot_uncached(bars, technical)
        expected_technical = copy.deepcopy(technical)
        expected_price_action = copy.deepcopy(price_action)
        technical["series"][-1]["ema20"] = -999
        technical["modules"].clear()
        price_action["swings"]["highs"].clear()
        price_action["modules"].clear()

        fresh = self.analysis._technical_indicator_snapshot_uncached(bars)
        self.assertEqual(bars, original)
        self.assertEqual(fresh, expected_technical)
        self.assertEqual(
            self.analysis._price_action_features_snapshot_uncached(bars, fresh),
            expected_price_action,
        )


class CouncilAnalysisBridgeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module("bridge_council_analysis_module_test", "bridge_server.py")

    def setUp(self) -> None:
        with self.bridge.AI_TRADE_COUNCIL_ANALYSIS_CACHE_LOCK:
            self.bridge.AI_TRADE_COUNCIL_ANALYSIS_CACHE.clear()

    def tearDown(self) -> None:
        with self.bridge.AI_TRADE_COUNCIL_ANALYSIS_CACHE_LOCK:
            self.bridge.AI_TRADE_COUNCIL_ANALYSIS_CACHE.clear()

    def test_bridge_reexports_the_calculation_module_without_duplicate_formulas(self) -> None:
        from hq_backend.trading import council_analysis
        self.assertIs(
            self.bridge._technical_indicator_snapshot_uncached,
            council_analysis._technical_indicator_snapshot_uncached,
        )
        self.assertIs(
            self.bridge._price_action_features_snapshot_uncached,
            council_analysis._price_action_features_snapshot_uncached,
        )
        self.assertIs(
            self.bridge.AI_TRADE_COUNCIL_TECHNICAL_MODULES,
            council_analysis.AI_TRADE_COUNCIL_TECHNICAL_MODULES,
        )

    def test_bridge_cache_keeps_delegation_seams_and_defensive_copies(self) -> None:
        bars = closed_bars()
        with (
            mock.patch.object(
                self.bridge,
                "_technical_indicator_snapshot_uncached",
                wraps=self.bridge._technical_indicator_snapshot_uncached,
            ) as technical,
            mock.patch.object(
                self.bridge,
                "_price_action_features_snapshot_uncached",
                wraps=self.bridge._price_action_features_snapshot_uncached,
            ) as price_action,
        ):
            first = self.bridge._ai_trade_council_analysis_feature_bundle(bars)
            expected = copy.deepcopy(first)
            first["technicalIndicators"]["series"][-1]["ema20"] = -999
            first["priceActionFeatures"]["swings"]["highs"].clear()
            second = self.bridge._ai_trade_council_analysis_feature_bundle(copy.deepcopy(bars))
            self.assertEqual(second, expected)
            technical.assert_called_once_with(bars)
            price_action.assert_called_once()

            self.bridge._ai_trade_council_analysis_feature_bundle(closed_bars(241))
            self.assertEqual(technical.call_count, 2)
            self.assertEqual(price_action.call_count, 2)


if __name__ == "__main__":
    unittest.main()
