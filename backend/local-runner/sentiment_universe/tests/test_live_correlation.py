import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "live_backend" / "correlation.py"
spec = importlib.util.spec_from_file_location("live_correlation", MODULE)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
sys.path.insert(0, str(MODULE.parents[1]))
from live_backend import mt5_reader as reader
NOW = 1792774800  # Friday UTC, deliberately away from weekend-specific logic.


def bars(returns, *, start=NOW - 400 * 3600, initial=1.0):
    output = [{"time": start, "close": initial}]
    value = initial
    for index, change in enumerate(returns, 1):
        value *= math.exp(change)
        output.append({"time": start + index * 3600, "close": value})
    return output


def fixture(a=None, b=None, now=NOW):
    changes = [math.sin(i * .4) * .001 + math.cos(i * .13) * .002 for i in range(200)]
    start = now - 202 * 3600
    return {"collectedAt": c.iso(now), "source": {"kind": "mt5_closed_bars", "closedBarsOnly": True,
            "clock": {"basis": "broker_server_normalized", "offsetSeconds": 10800}},
            "pairs": [{"pair": "EURUSD", "brokerSymbol": "EURUSD", "series": {"H1": a or bars(changes, start=start)}},
                      {"pair": "GBPUSD", "brokerSymbol": "GBPUSD", "series": {"H1": b or bars([-x for x in changes], start=start)}}]}


def model(snapshot, **kwargs):
    return c.build(snapshot, now=NOW, instruments=("EURUSD", "GBPUSD"), **kwargs)


class CorrelationTests(unittest.TestCase):
    def test_inverse_log_returns_are_minus_one(self):
        result = model(fixture())
        self.assertEqual(result["items"][0]["value"], -1)
        self.assertEqual(result["items"][0]["samples"], 200)
        self.assertEqual(result["status"], "ready")

    def test_prices_not_levels_and_scaled_prices_equal(self):
        data = fixture()
        data["pairs"][1]["series"]["H1"] = [{"time": x["time"], "close": x["close"] * 1000} for x in data["pairs"][0]["series"]["H1"]]
        self.assertEqual(model(data)["items"][0]["value"], 1)

    def test_extreme_finite_prices_do_not_overflow_or_crash(self):
        data = fixture()
        data["pairs"][0]["series"]["H1"][50]["close"] = 1e-308
        data["pairs"][0]["series"]["H1"][51]["close"] = 1e308
        edge = model(data)["items"][0]
        self.assertTrue(math.isfinite(edge["value"]))

    def test_aligns_before_window_limit(self):
        changes = [math.sin(i * .2) * .001 for i in range(260)]
        start = NOW - 262 * 3600
        data = fixture(bars(changes, start=start), bars([-x for x in changes], start=start))
        del data["pairs"][1]["series"]["H1"][-50]
        edge = model(data)["items"][0]
        self.assertEqual(edge["samples"], 200)
        self.assertEqual(edge["value"], -1)

    def test_missing_bar_drops_both_spanning_intervals_no_forward_fill(self):
        data = fixture()
        del data["pairs"][1]["series"]["H1"][70]
        edge = model(data)["items"][0]
        self.assertEqual(edge["samples"], 198)
        self.assertEqual(edge["value"], -1)

    def test_consecutive_intervals_require_same_start_and_end(self):
        data = fixture()
        for row in data["pairs"][1]["series"]["H1"]:
            row["time"] += 1800
        result = model(data)
        self.assertEqual(result["items"][0]["samples"], 0)
        self.assertEqual(result["items"][0]["status"], "insufficient_overlap")
        self.assertIsNone(result["items"][0]["value"])

    def test_incomplete_bar_excluded(self):
        data = fixture()
        for row in data["pairs"]:
            row["series"]["H1"].append({"time": NOW, "close": 9000})
        self.assertEqual(model(data)["items"][0]["samples"], 200)

    def test_minimum_threshold_not_fabricated(self):
        data = fixture()
        for row in data["pairs"]:
            row["series"]["H1"] = row["series"]["H1"][-100:]
        edge = model(data)["items"][0]
        self.assertEqual(edge["samples"], 99)
        self.assertEqual(edge["status"], "insufficient")
        self.assertIsNone(edge["value"])

    def test_flat_is_undefined_not_zero(self):
        data = fixture()
        for bar in data["pairs"][1]["series"]["H1"]:
            bar["close"] = 1
        self.assertEqual(model(data)["items"][0]["status"], "flat")
        self.assertIsNone(model(data)["items"][0]["value"])

    def test_old_collection_is_stale(self):
        data = fixture()
        data["collectedAt"] = c.iso(NOW - 3601)
        self.assertEqual(model(data)["items"][0]["status"], "stale")
        self.assertIsNone(model(data)["items"][0]["value"])

    def test_old_market_bars_stale_even_when_collection_fresh(self):
        data = fixture()
        for row in data["pairs"]:
            for bar in row["series"]["H1"]:
                bar["time"] -= 86400
        self.assertEqual(model(data)["items"][0]["status"], "stale")

    def test_isolated_fresh_bar_cannot_revive_old_consecutive_returns(self):
        changes = [math.sin(i * .2) * .001 for i in range(200)]
        old = bars(changes, start=NOW - 800 * 3600)
        data = fixture(copy.deepcopy(old), copy.deepcopy(old))
        for row in data["pairs"]:
            row["series"]["H1"].append({"time": NOW - 3600, "close": 1.1})
        result = model(data)
        for row in result["instruments"]:
            self.assertEqual(row["lastBarClosedAt"], c.iso(NOW))
            self.assertEqual(row["lastReturnEndAt"], c.iso(NOW - 599 * 3600))
            self.assertEqual(row["status"], "stale")
        edge = result["items"][0]
        self.assertEqual(edge["samples"], 200)
        self.assertEqual(edge["status"], "stale")
        self.assertIsNone(edge["value"])
        self.assertIsNone(result["asOf"])

    def test_fresh_series_with_only_old_shared_intervals_produces_no_edge(self):
        changes = [math.sin(i * .2) * .001 for i in range(200)]
        old = bars(changes, start=NOW - 800 * 3600)
        a = copy.deepcopy(old) + bars([.002], start=NOW - 3 * 3600)
        b = copy.deepcopy(old) + bars([-.003], start=NOW - 2 * 3600)
        result = model(fixture(a, b))
        self.assertTrue(all(row["status"] == "ready" for row in result["instruments"]))
        edge = result["items"][0]
        self.assertEqual(edge["samples"], 200)
        self.assertEqual(edge["endAt"], c.iso(NOW - 599 * 3600))
        self.assertEqual(edge["status"], "stale")
        self.assertIsNone(edge["value"])
        self.assertEqual(result["status"], "partial")
        self.assertIsNone(result["asOf"])

    def test_fresh_shared_return_restores_valid_edge_after_gap(self):
        changes = [math.sin(i * .2) * .001 for i in range(200)]
        old = bars(changes, start=NOW - 800 * 3600)
        a = copy.deepcopy(old) + bars([.002], start=NOW - 2 * 3600)
        result = model(fixture(a, copy.deepcopy(a)))
        self.assertEqual(result["items"][0]["status"], "ready")
        self.assertEqual(result["items"][0]["value"], 1)
        self.assertEqual(result["asOf"], c.iso(NOW))

    def test_duplicate_conflict_invalidates_instrument(self):
        data = fixture()
        duplicate = dict(data["pairs"][0]["series"]["H1"][100], close=8)
        data["pairs"][0]["series"]["H1"].append(duplicate)
        self.assertEqual(model(data)["items"][0]["status"], "invalid")

    def test_missing_instrument_distinct_from_flat(self):
        data = fixture()
        data["pairs"].pop()
        result = model(data)
        self.assertEqual(result["instruments"][1]["status"], "missing")
        self.assertEqual(result["items"][0]["status"], "missing")

    def test_source_must_explicitly_prove_closed_normalized_bars(self):
        data = fixture()
        data["source"]["closedBarsOnly"] = False
        self.assertEqual(model(data)["items"][0]["status"], "invalid")
        self.assertIsNone(model(data)["lastSuccessAt"])

    def test_never_exports_account_or_path_fields(self):
        data = fixture()
        data["account"] = {"login": "PRIVATE", "balance": "PRIVATE"}
        data["source"]["terminalPath"] = "PRIVATE"
        encoded = json.dumps(model(data))
        self.assertNotIn("PRIVATE", encoded)

    def test_full_output_has_496_unique_edges_even_when_missing(self):
        result = c.build(fixture(), now=NOW)
        self.assertEqual(len(result["items"]), 496)
        self.assertEqual(result["coverage"], {"available": 2, "total": 32})
        self.assertEqual(len({(x["source"], x["target"]) for x in result["items"]}), 496)

    def test_weekend_preserves_friday_data_but_labels_market_closed(self):
        saturday = 1792843200
        data = fixture(now=saturday)
        for row in data["pairs"]:
            for bar in row["series"]["H1"]:
                bar["time"] -= 14 * 3600
        result = c.build(data, now=saturday, instruments=("EURUSD", "GBPUSD"))
        self.assertEqual(result["marketStatus"], "market_closed")
        self.assertEqual(result["items"][0]["value"], -1)

    def test_weekend_isolated_friday_bar_does_not_preserve_thursday_returns(self):
        saturday = 1792843200
        data = fixture(now=saturday)
        for row in data["pairs"]:
            for bar in row["series"]["H1"]:
                bar["time"] -= 38 * 3600
            row["series"]["H1"].append({"time": saturday - 15 * 3600, "close": 1.1})
        result = c.build(data, now=saturday, instruments=("EURUSD", "GBPUSD"))
        self.assertTrue(all(row["status"] == "stale" for row in result["instruments"]))
        self.assertIsNone(result["items"][0]["value"])

    def test_sunday_reopening_does_not_keep_friday_data_market_closed(self):
        saturday=1792843200
        sunday_night=saturday+34*3600
        data=fixture(now=saturday)
        for row in data["pairs"]:
            for bar in row["series"]["H1"]:
                bar["time"]-=14*3600
        data["collectedAt"]=c.iso(sunday_night)
        result=c.build(data,now=sunday_night,instruments=("EURUSD","GBPUSD"))
        self.assertEqual(result["items"][0]["status"],"stale")
        self.assertIsNone(result["items"][0]["value"])
        self.assertEqual(result["marketStatus"],"open_or_unknown")

    def test_weekend_keeps_shared_friday_interval_even_when_newer_intervals_differ(self):
        saturday = 1792843200
        data = fixture(now=saturday)
        for row in data["pairs"]:
            for bar in row["series"]["H1"]:
                bar["time"] -= 20 * 3600
        shared_end = data["pairs"][0]["series"]["H1"][-1]["time"] + 3600
        data["pairs"][0]["series"]["H1"] += bars([.002], start=saturday - 18 * 3600)
        data["pairs"][1]["series"]["H1"] += bars([-.003], start=saturday - 17 * 3600)
        result = c.build(data, now=saturday, instruments=("EURUSD", "GBPUSD"))
        self.assertEqual(result["items"][0]["status"], "ready")
        self.assertEqual(result["items"][0]["endAt"], c.iso(shared_end))
        self.assertEqual(result["items"][0]["value"], -1)

    def test_unreadable_cache_returns_sanitized_error(self):
        result = c.collect({"snapshotPath": str(MODULE.parent / "nonexistent.json"), "now": NOW})
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["errorCode"], "snapshot_unavailable")
        self.assertNotIn(str(MODULE.parent), json.dumps(result))

    def test_service_reuses_same_hour_without_second_terminal_call(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "hq" / "snapshot.json"
            source.parent.mkdir()
            source.write_text(json.dumps(fixture()), encoding="utf-8")
            calls = []

            def fake(config):
                calls.append(config)
                result = fixture()
                result["schemaVersion"] = "sentiment-mt5-h1-snapshot-v1"
                result["source"]["kind"] = "mt5_guarded_closed_bars"
                return result

            config = {"inputCachePath": str(source), "enabled": True, "terminalPath": "selected-terminal", "dataPath": "selected-data"}
            with patch.object(c.time, "time", return_value=NOW):
                a = c.collect_for_service(config, root / "isolated", terminal_collector=fake)
            with patch.object(c.time, "time", return_value=NOW + 600):
                b = c.collect_for_service(config, root / "isolated", terminal_collector=fake)
            self.assertEqual(len(calls), 1)
            self.assertEqual(a["items"], b["items"])

    def test_service_candidate_change_never_attaches_to_previous_terminal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "hq" / "snapshot.json"
            source.parent.mkdir()
            data = fixture()
            data["source"]["terminalCandidateId"] = "new-selection"
            source.write_text(json.dumps(data), encoding="utf-8")
            config = {"inputCachePath": str(source), "enabled": True, "candidateId": "old-selection"}
            with patch.object(c.time, "time", return_value=NOW):
                result = c.collect_for_service(config, root / "isolated", terminal_collector=lambda _: self.fail("must not initialize"))
            self.assertEqual(result["refreshErrorCode"], "selected_terminal_changed")

    def test_service_never_writes_into_hq_input_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            result = c.collect_for_service({"inputCachePath": str(root / "snapshot.json"), "enabled": True}, root)
            self.assertEqual(result["errorCode"], "isolated_state_directory_required")
            self.assertEqual(list(root.iterdir()), [])


class GuardedReaderTests(unittest.TestCase):
    def symbol(self, name="EURUSD", base="EUR", profit="USD", visible=True, custom=False):
        return SimpleNamespace(name=name, currency_base=base, currency_profit=profit, visible=visible, custom=custom, trade_calc_mode=0)

    def test_catalog_respects_suffix_and_excludes_custom(self):
        self.assertEqual(reader.choose_symbol("EURUSD", [self.symbol("EURUSD.a")]), ("EURUSD.a", None))
        self.assertEqual(reader.choose_symbol("XAUUSD", [self.symbol("XAUUSD_TEST", "XAU", custom=True)]), (None, "symbol_unavailable"))
        self.assertEqual(reader.choose_symbol("WTI", [self.symbol("USOIL.a", "")]), ("USOIL.a", None))
        self.assertEqual(reader.choose_symbol("WTI", [self.symbol("WTI_DEC26", "")]), (None, "symbol_unavailable"))

    def test_ambiguous_mapping_fails_closed(self):
        choices = [self.symbol("EURUSD.a"), self.symbol("EURUSD.b")]
        self.assertEqual(reader.choose_symbol("EURUSD", choices), (None, "symbol_ambiguous"))

    def test_reader_only_uses_allowed_read_methods(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            calls = []
            class FakeAPI:
                TIMEFRAME_H1 = 16385
                tick_calls = 0
                def initialize(self, path, **kwargs):
                    calls.append(("initialize", path, kwargs))
                    return True
                def terminal_info(self):
                    return SimpleNamespace(path=str(root), data_path=str(root), connected=True)
                def symbols_get(self):
                    return [SimpleNamespace(name=symbol, currency_base=symbol[:3], currency_profit=symbol[3:], custom=False, visible=True, trade_calc_mode=0) for symbol in ("EURUSD", "GBPUSD", "USDJPY")]
                def symbol_info_tick(self, symbol):
                    self.tick_calls += 1
                    calls.append(("tick", symbol))
                    return SimpleNamespace(time=NOW - 1 + (self.tick_calls - 1) // 3)
                def copy_rates_from_pos(self, symbol, frame, start, count):
                    calls.append(("read", symbol, frame, start, count))
                    return bars([.001, -.001], start=NOW - 5 * 3600)
                def shutdown(self):
                    calls.append(("shutdown",))
                def __getattr__(self, name):
                    raise AssertionError("Forbidden API method: " + name)
            config = {"enabled": True, "terminalPath": str(root / "terminal64.exe"), "dataPath": str(root), "terminalPid": 123}
            def guard(pid, path):
                self.assertEqual(pid, 123)
                return lambda: calls.append(("guard",)), lambda: calls.append(("release",))
            with patch.object(reader.time, "time", return_value=NOW):
                result = reader.collect_snapshot(config, api=FakeAPI(), guard_factory=guard, pause=lambda _: None)
            self.assertEqual(calls[0], ("guard",))
            self.assertEqual(calls[1][0], "initialize")
            self.assertEqual(calls[1][2], {"timeout": 10000})
            self.assertEqual(calls[-2:], [("shutdown",), ("release",)])
            self.assertEqual(result["source"]["closedBarsOnly"], True)
            self.assertEqual(result["source"]["clock"]["method"], "live_tick_consensus")
            self.assertEqual(result["source"]["clock"]["offsetSeconds"], 0)
            self.assertEqual([x for x in calls if x[0] == "read"][0][-2:], (1, 350))

    def test_disabled_reader_rejects_before_loading_api(self):
        with self.assertRaisesRegex(reader.ReadUnavailable, "terminal_reader_disabled"):
            reader.collect_snapshot({"enabled": False}, api=object())

    def test_saved_selection_resolves_new_pid_after_terminal_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            guarded=[]
            class FakeAPI:
                TIMEFRAME_H1=16385
                ticks=0
                def initialize(self,path,**kwargs):
                    self.ticks=0
                    return True
                def terminal_info(self):
                    return SimpleNamespace(path=str(root),data_path=str(root),connected=True)
                def symbols_get(self):
                    return [SimpleNamespace(name=s,currency_base=s[:3],currency_profit=s[3:],custom=False,visible=True,trade_calc_mode=0) for s in ("EURUSD","GBPUSD","USDJPY")]
                def symbol_info_tick(self,symbol):
                    self.ticks+=1
                    return SimpleNamespace(time=NOW-1+(self.ticks-1)//3)
                def copy_rates_from_pos(self,*args):
                    return bars([.001,-.001],start=NOW-5*3600)
                def shutdown(self):
                    pass
                def __getattr__(self,name):
                    raise AssertionError("Forbidden API method: "+name)
            config={"enabled":True,"terminalPath":str(root/"terminal64.exe"),"dataPath":str(root),"selectionId":"saved-selection"}
            def guard(pid,path):
                guarded.append(pid)
                return lambda:None,lambda:None
            with patch.object(reader,"find_running_pid",side_effect=[123,456]),patch.object(reader.time,"time",return_value=NOW):
                for _ in range(2):
                    result=reader.collect_snapshot(config,api=FakeAPI(),guard_factory=guard,pause=lambda _:None)
                    self.assertEqual(result["source"]["clock"]["status"],"verified")
            self.assertEqual(guarded,[123,456])


class ClockRenewalTests(unittest.TestCase):
    def previous(self, *, now=NOW, offset=10800, binding="selected", age=3600):
        return {"basis": "broker_server_normalized", "offsetSeconds": offset, "verifiedAt": c.iso(now-age), "bindingId": binding}

    def quotes(self, now=NOW, offset=10800, advancing=True):
        return ({symbol: now+offset-1 for symbol in ("EURUSD", "GBPUSD", "USDJPY")},
                {symbol: now+offset-(0 if advancing else 1) for symbol in ("EURUSD", "GBPUSD", "USDJPY")})

    def test_expired_clock_is_renewed_without_hq_or_manual_setup(self):
        first, second = self.quotes()
        result = reader.verified_clock(first, second, NOW, previous=self.previous(age=9*86400), binding="selected")
        self.assertEqual(result["verifiedAt"], c.iso(NOW))
        self.assertEqual(result["offsetSeconds"], 10800)
        self.assertEqual(result["status"], "verified")

    def test_utc_api_requires_no_broker_shift(self):
        first, second = self.quotes(offset=0)
        self.assertEqual(reader.verified_clock(first, second, NOW, binding="selected")["offsetSeconds"], 0)

    def test_weekend_first_setup_waits_without_guessing_offset(self):
        first, second = self.quotes(advancing=False)
        with self.assertRaisesRegex(reader.ReadUnavailable, "waiting_for_ticks"):
            reader.verified_clock(first, second, 1792843200, binding="selected")

    def test_weekend_fallback_is_terminal_bound_and_does_not_renew_verified_at(self):
        saturday = 1792843200
        first, second = self.quotes(advancing=False)
        previous = self.previous(age=0)
        result = reader.verified_clock(first, second, saturday, previous=previous, binding="selected")
        self.assertEqual(result["verifiedAt"], previous["verifiedAt"])
        self.assertEqual(result["status"], "held_market_closed")
        with self.assertRaisesRegex(reader.ReadUnavailable, "waiting_for_ticks"):
            reader.verified_clock(first, second, saturday, previous=previous, binding="different-terminal")

    def test_stale_fallback_and_ambiguous_advancing_quotes_are_rejected(self):
        first, second = self.quotes(advancing=False)
        with self.assertRaises(reader.ReadUnavailable):
            reader.verified_clock(first, second, NOW, previous=self.previous(age=9*86400), binding="selected")
        first, second = self.quotes()
        second["USDJPY"] += 3600
        with self.assertRaisesRegex(reader.ReadUnavailable, "unverified"):
            reader.verified_clock(first, second, NOW, previous=self.previous(age=1), binding="selected")

    def test_dst_moves_both_directions_and_excludes_uncertain_transition_bars(self):
        for old_offset, new_offset in ((10800,7200),(7200,10800)):
            with self.subTest(old=old_offset,new=new_offset):
                first, second = self.quotes(offset=new_offset)
                result = reader.verified_clock(first, second, NOW,
                    previous=self.previous(offset=old_offset,age=2*3600), binding="selected")
                self.assertEqual(result["offsetSeconds"], new_offset)
                self.assertEqual(len(result["transitions"]), 1)
                self.assertEqual(reader.normalized_bar_time(NOW-6*3600+old_offset,result), NOW-6*3600)
                self.assertIsNone(reader.normalized_bar_time(NOW-3600+new_offset,result))
                self.assertEqual(reader.normalized_bar_time(NOW+2*3600+new_offset,result),NOW+2*3600)
                self.assertTrue(result["historicalClockApproximation"])

    def test_service_works_without_any_hq_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            seen = []
            def collector(config):
                seen.append(config)
                data=fixture()
                data["schemaVersion"]="sentiment-mt5-h1-snapshot-v1"
                data["source"]["kind"]="mt5_guarded_closed_bars"
                return data
            config={"enabled":True,"terminalPath":"selected-terminal","dataPath":"selected-data","selectionId":"chosen"}
            with patch.object(c.time,"time",return_value=NOW):
                result=c.collect_for_service(config,Path(folder)/"independent",terminal_collector=collector)
            self.assertEqual(len(seen),1)
            self.assertEqual(seen[0]["clock"],{})
            self.assertEqual(result["coverage"]["available"],2)
            self.assertEqual(result["items"][next(i for i,e in enumerate(result["items"]) if {e["source"],e["target"]}=={"EURUSD","GBPUSD"})]["value"],-1)

    def test_first_weekend_setup_defers_native_retry_until_earliest_reopening(self):
        with tempfile.TemporaryDirectory() as folder:
            saturday=1792843200
            sunday_open=saturday+33*3600
            calls=[]
            def waiting(_):
                calls.append(1)
                return {"status":"unavailable","errorCode":"broker_clock_waiting_for_ticks"}
            config={"enabled":True,"terminalPath":"selected-terminal","dataPath":"selected-data","selectionId":"chosen"}
            for moment in (saturday,saturday+300,saturday+3600):
                with patch.object(c.time,"time",return_value=moment):
                    result=c.collect_for_service(config,folder,terminal_collector=waiting)
                    self.assertEqual(result["nextAttemptAt"],c.iso(sunday_open))
            self.assertEqual(len(calls),1)
            with patch.object(c.time,"time",return_value=sunday_open):
                result=c.collect_for_service(config,folder,terminal_collector=waiting)
            self.assertEqual(len(calls),2)
            self.assertEqual(result["nextAttemptAt"],c.iso(sunday_open+300))

    def test_closed_terminal_retries_are_bounded_and_deadline_does_not_slide(self):
        with tempfile.TemporaryDirectory() as folder:
            calls=[]
            def closed(_):
                calls.append(1)
                return {"status":"unavailable","errorCode":"selected_terminal_not_running"}
            config={"enabled":True,"terminalPath":"selected-terminal","dataPath":"selected-data","selectionId":"chosen"}
            with patch.object(c.time,"time",return_value=NOW):
                first=c.collect_for_service(config,folder,terminal_collector=closed)
            with patch.object(c.time,"time",return_value=NOW+60):
                second=c.collect_for_service(config,folder,terminal_collector=closed)
            self.assertEqual(len(calls),1)
            self.assertEqual(first["nextAttemptAt"],second["nextAttemptAt"])
            with patch.object(c.time,"time",return_value=NOW+300):
                c.collect_for_service(config,folder,terminal_collector=closed)
            self.assertEqual(len(calls),2)

    def test_legacy_binding_upgrade_retains_weekend_cache_without_native_attach(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            state=root/"independent"
            state.mkdir()
            upstream=root/"hq"/"snapshot.json"
            upstream.parent.mkdir()
            config={"enabled":True,"terminalPath":"same-terminal","dataPath":"same-data",
                    "candidateId":"same-candidate","inputCachePath":str(upstream)}
            data=fixture()
            data["schemaVersion"]="sentiment-mt5-h1-snapshot-v1"
            data["source"]["kind"]="mt5_guarded_closed_bars"
            data["source"]["clock"]["verifiedAt"]=c.iso(NOW)
            (state/"mt5-h1-snapshot.json").write_text(json.dumps(data))
            old_binding=hashlib.sha256(json.dumps({key:config.get(key) for key in
                ("terminalPath","dataPath","candidateId","symbolMap")},sort_keys=True).encode()).hexdigest()
            (state/"mt5-h1-collector-state.json").write_text(json.dumps({"binding":old_binding,"lastAttemptAt":c.iso(NOW)}))
            hq=copy.deepcopy(data)
            hq["source"]["terminalCandidateId"]="same-candidate"
            hq["pairs"]=hq["pairs"][:1]
            upstream.write_text(json.dumps(hq))
            with patch.object(c.time,"time",return_value=1792843200):
                result=c.collect_for_service(config,state,terminal_collector=lambda _:self.fail("Weekend upgrade must not attach"))
            self.assertEqual(result["coverage"]["available"],2)
            self.assertEqual(result["marketStatus"],"market_closed")
            saved=json.loads((state/"mt5-h1-snapshot.json").read_text())
            self.assertEqual(saved["source"]["clock"]["bindingId"],reader.terminal_binding(config))
            self.assertNotEqual(json.loads((state/"mt5-h1-collector-state.json").read_text())["binding"],old_binding)


if __name__ == "__main__":
    unittest.main()
