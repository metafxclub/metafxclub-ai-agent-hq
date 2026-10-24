"""Closed-bar arithmetic and truthful missing/stale projections; no I/O."""
import copy
import sys
import unittest
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "local-runner"))
from hq_backend.research import fx_trend as engine
from test_fx28_trend_runner import market_snapshot


class Fx28TrendEngineTests(unittest.TestCase):
    def test_rising_prices_confirm_all_horizons_with_actual_activity(self):
        raw, now = market_snapshot(engine)
        model = engine.build_read_model(raw, now=now)
        self.assertEqual(model["summary"], {"evaluatedPairCount": 28, "totalPairCount": 28})
        self.assertEqual(model["status"], "ready")
        self.assertEqual(len(model["rows"]), 28)
        for row in model["rows"]:
            self.assertEqual({value["bias"] for value in row["horizons"].values()}, {"BULLISH"})
            hourly = row["horizons"]["short"]["metrics"]["H1"]
            self.assertAlmostEqual(hourly["tickVolumeRatio20"], 159 / 148.5)
            self.assertIn("1.06", row["priceSummaryTh"])
            self.assertIn("1.07", row["tickVolumeSummaryTh"])

    def test_declining_prices_and_flat_prices_are_distinct(self):
        raw, now = market_snapshot(engine, pair_count=1)
        for descending, expected in ((True, "BEARISH"), (False, "SIDEWAY")):
            candidate = copy.deepcopy(raw)
            for rows in candidate["pairs"][0]["series"].values():
                for index, row in enumerate(rows):
                    level = 2 - index / 1000 if descending else 2
                    row.update(open=level, close=level, high=level + .002, low=level - .002)
            model = engine.build_read_model(candidate, now=now)
            self.assertEqual({h["bias"] for h in model["rows"][0]["horizons"].values()}, {expected})

    def test_conflicting_timeframes_do_not_create_false_confirmation(self):
        raw, now = market_snapshot(engine, pair_count=1)
        for index, row in enumerate(raw["pairs"][0]["series"]["M15"]):
            row.update(open=2-index/1000, close=2-index/1000, high=2.002-index/1000, low=1.998-index/1000)
        model = engine.build_read_model(raw, now=now)
        self.assertEqual(model["rows"][0]["horizons"]["short"]["bias"], "SIDEWAY")
        self.assertEqual(model["rows"][0]["horizons"]["medium"]["bias"], "BULLISH")

    def test_missing_weekly_history_does_not_hide_short_medium(self):
        raw, now = market_snapshot(engine, pair_count=1)
        raw["pairs"][0]["series"]["W1"] = []
        model = engine.build_read_model(raw, now=now)
        row = model["rows"][0]
        self.assertEqual(row["status"], "partial")
        self.assertEqual(row["horizons"]["long"]["bias"], "INSUFFICIENT_DATA")
        self.assertEqual(row["horizons"]["short"]["status"], "ready")
        self.assertEqual(model["rows"][1]["status"], "waiting")

    def test_bad_prices_duplicate_times_and_current_bar_fail_closed(self):
        raw, now = market_snapshot(engine, pair_count=1)
        for kind in ("nan", "negative", "ohlc", "duplicate", "current"):
            with self.subTest(kind=kind):
                candidate = copy.deepcopy(raw)
                rows = candidate["pairs"][0]["series"]["M15"]
                if kind == "nan": rows[-1]["close"] = float("nan")
                elif kind == "negative": rows[-1]["tick_volume"] = -1
                elif kind == "ohlc": rows[-1]["high"] = rows[-1]["low"] - .1
                elif kind == "duplicate": rows[-1]["time"] = rows[-2]["time"]
                else: rows[-1]["time"] = int(now.timestamp())
                # Invalid numbers are rejected by the canonical digest as well
                # as the per-series validator; neither can become a signal.
                try:
                    model = engine.build_read_model(candidate, now=now)
                except ValueError:
                    self.assertEqual(kind, "nan")
                else:
                    self.assertEqual(model["rows"][0]["horizons"]["short"]["bias"], "INSUFFICIENT_DATA")

    def test_stale_collection_never_presents_direction_as_current(self):
        raw, now = market_snapshot(engine)
        model = engine.build_read_model(raw, now=now + timedelta(minutes=31))
        self.assertTrue(model["stale"])
        self.assertEqual(model["summary"]["evaluatedPairCount"], 0)
        self.assertEqual({h["bias"] for row in model["rows"] for h in row["horizons"].values()}, {"INSUFFICIENT_DATA"})

    def test_normalized_broker_timestamps_are_not_shifted_twice(self):
        raw, now = market_snapshot(engine)
        raw["source"]["clock"] = {"basis": "broker_server_normalized", "offsetSeconds": 10800}
        for pair in raw["pairs"]:
            for rows in pair["series"].values():
                for row in rows:
                    row["brokerTime"] = row["time"] + 10800
        model = engine.build_read_model(raw, now=now)
        self.assertEqual(model["summary"]["evaluatedPairCount"], 28)
        self.assertEqual(model["dataAsOf"], engine.iso(now))

    def test_weekend_retains_real_last_bars_without_fabricating_slots(self):
        raw, friday = market_snapshot(engine, pair_count=1)
        sunday = friday + timedelta(days=2)
        raw["collectedAt"] = engine.iso(sunday)
        before = copy.deepcopy(raw)
        model = engine.build_read_model(raw, now=sunday)
        self.assertEqual(model["rows"][0]["status"], "ready")
        self.assertEqual(raw, before)
        self.assertEqual(model["rows"][0]["horizons"]["short"]["metrics"]["M15"]["barCount"], 60)

    def test_assignment_is_bounded_all_pairs_and_all_available_source_ids(self):
        raw, now = market_snapshot(engine)
        model = engine.build_read_model(raw, now=now)
        assignment = engine.make_assignment(model, "2026-10-23", [{"url": "https://www.ecb.europa.eu/press/", "title": "ECB"}])
        prompt = engine.render_prompt(assignment)
        self.assertLessEqual(len(prompt), 20000)
        self.assertEqual(len(engine.prompt_assignment(prompt)["sourceRefs"]), 141)
        changed = copy.deepcopy(assignment)
        changed["rows"][0]["horizons"] = {}
        with self.assertRaises(ValueError):
            engine.prompt_assignment(engine.render_prompt(changed))

    def test_zero_tick_volume_is_unknown_activity_not_infinite(self):
        raw, now = market_snapshot(engine, pair_count=1)
        for row in raw["pairs"][0]["series"]["H1"]:
            row["tick_volume"] = 0
        model = engine.build_read_model(raw, now=now)
        self.assertIsNone(model["rows"][0]["horizons"]["short"]["metrics"]["H1"]["tickVolumeRatio20"])
        self.assertIn("ยังไม่มี", model["rows"][0]["tickVolumeSummaryTh"])


if __name__ == "__main__":
    unittest.main()
