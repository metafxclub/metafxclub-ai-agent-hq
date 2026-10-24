"""Optional bounded reader of ONE explicitly configured, already-running MT5.

No discovery by account, login, symbol selection, trade APIs, settings, chart
changes, terminal lifecycle commands or writes to HQ/MT5. initialize() itself
has no connect-only flag; a process-handle guard constrains its use to a live
matching executable and verifies the same process and data directory afterward.
"""
from __future__ import annotations

import ctypes
from collections import Counter
from ctypes import wintypes
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import time
import sys

try:
    from .correlation import INSTRUMENTS, iso, stamp
except ImportError:
    from correlation import INSTRUMENTS, iso, stamp


class ReadUnavailable(RuntimeError):
    pass


def process_guard(pid, executable):
    executable = Path(executable)
    if os.name != "nt" or type(pid) is not int or pid <= 0 or not executable.is_absolute() or executable.name.lower() != "terminal64.exe" or not executable.is_file():
        raise ReadUnavailable("selected_terminal_unavailable")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        raise ReadUnavailable("selected_terminal_not_running")

    def verify():
        buf, size, code = ctypes.create_unicode_buffer(32768), wintypes.DWORD(32768), wintypes.DWORD()
        if (not kernel.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size))
                or Path(buf.value).resolve() != executable.resolve()
                or not kernel.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value != 259):
            raise ReadUnavailable("selected_terminal_process_changed")
    try:
        verify()
    except Exception:
        kernel.CloseHandle(handle)
        raise
    return verify, lambda: kernel.CloseHandle(handle)


def find_running_pid(executable):
    if os.name != "nt":
        raise ReadUnavailable("selected_terminal_unavailable")
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.EnumProcesses.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    processes, size = (wintypes.DWORD * 8192)(), wintypes.DWORD()
    if not psapi.EnumProcesses(processes, ctypes.sizeof(processes), ctypes.byref(size)) or size.value >= ctypes.sizeof(processes):
        raise ReadUnavailable("terminal_process_probe_unavailable")
    matches = []
    for pid in processes[:size.value // ctypes.sizeof(wintypes.DWORD)]:
        try:
            _, release = process_guard(pid, executable)
        except ReadUnavailable:
            continue
        release()
        matches.append(pid)
    if len(matches) != 1:
        raise ReadUnavailable("selected_terminal_not_running" if not matches else "selected_terminal_ambiguous")
    return matches[0]


def choose_symbol(instrument, symbols, explicit=None):
    available = [s for s in symbols if not getattr(s, "custom", False)]
    if explicit:
        exact = [s for s in available if s.name == explicit]
        return (exact[0].name, None) if len(exact) == 1 else (None, "symbol_override_unavailable")
    if instrument in ("WTI", "BRENT"):
        available = [s for s in available if not getattr(s, "expiration_time", 0)
                     and not re.search(r"(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\d{0,4}$", str(s.name), re.I)
                     and not re.search(r"FUTUR", str(getattr(s, "description", "")), re.I)]
        aliases = ("WTI", "USOIL", "XTIUSD") if instrument == "WTI" else ("BRENT", "UKOIL", "XBRUSD")
        exact = [s for s in available if s.name.upper() in aliases]
        candidates = exact or [s for s in available if any(re.fullmatch(re.escape(alias) + r"(?:[._#-][A-Z]{1,6}|[._#-])", s.name.upper()) for alias in aliases)]
    else:
        candidates = [s for s in available if getattr(s, "currency_base", "").upper() == instrument[:3]
                      and getattr(s, "currency_profit", "").upper() == instrument[3:]
                      and (instrument.startswith(("XAU", "XAG")) or getattr(s, "trade_calc_mode", None) in (0, 5))]
        exact = [s for s in candidates if s.name.upper() == instrument]
        candidates = exact or candidates
    visible = [s for s in candidates if getattr(s, "visible", False)]
    choices = visible or candidates
    return (str(choices[0].name), None) if len(choices) == 1 else (None, "symbol_ambiguous" if choices else "symbol_unavailable")


def terminal_binding(config):
    # Internal-only identity: never publish local paths or process ids.
    parts = [os.path.normcase(str(Path(config.get(key, "")).resolve())) for key in ("terminalPath", "dataPath")]
    parts.append(str(config.get("selectionId") or ""))
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()


def _previous_clock(previous, binding, now):
    if not isinstance(previous, dict) or previous.get("bindingId") != binding or previous.get("basis") != "broker_server_normalized":
        return None
    offset, verified = previous.get("offsetSeconds"), stamp(previous.get("verifiedAt"))
    if type(offset) is not int or abs(offset) > 14 * 3600 or offset % 900 or verified is None or verified > now + 5:
        return None
    return previous


def _clock_transitions(previous):
    result = []
    transitions = (previous or {}).get("transitions", [])
    for item in transitions[-16:] if isinstance(transitions, list) else []:
        if not isinstance(item, dict):
            continue
        before, after = stamp(item.get("beforeUtc")), stamp(item.get("afterUtc"))
        old, new = item.get("fromOffset"), item.get("toOffset")
        if (before is not None and after is not None and 0 <= before <= after
                and type(old) is int and type(new) is int and max(abs(old), abs(new)) <= 14 * 3600
                and old % 900 == 0 and new % 900 == 0):
            result.append({"beforeUtc": iso(before), "afterUtc": iso(after), "fromOffset": old, "toOffset": new})
    return sorted(result, key=lambda item: item["afterUtc"])


def verified_clock(first, second, now, *, previous=None, binding):
    """Verify the current offset from multiple actually advancing quote clocks.

    No assumption that every API uses server wall time: UTC produces offset 0.
    Prior clocks are considered only for this binding, never as a prerequisite.
    """
    previous = _previous_clock(previous, binding, now)
    candidates = []
    for symbol, observed in second.items():
        if type(observed) not in (int, float) or not math.isfinite(observed) or observed <= 0:
            continue
        offset = round((observed - now) / 900) * 900
        earlier = first.get(symbol)
        advancing = type(earlier) in (int, float) and math.isfinite(earlier) and observed > earlier
        if abs(offset) <= 14 * 3600 and -5 <= now - (observed - offset) <= 90:
            candidates.append((symbol, observed, offset, advancing))
    counts = Counter(item[2] for item in candidates)
    if counts:
        offset, count = counts.most_common(1)[0]
        advancing = sum(item[3] for item in candidates if item[2] == offset)
        if count >= 3 and count > len(candidates) / 2 and advancing >= 2:
            transitions = _clock_transitions(previous)
            if previous and previous["offsetSeconds"] != offset:
                transitions.append({"beforeUtc": previous["verifiedAt"], "afterUtc": iso(now),
                                    "fromOffset": previous["offsetSeconds"], "toOffset": offset})
            return {"basis": "broker_server_normalized", "offsetSeconds": offset, "bindingId": binding,
                    "method": "live_tick_consensus", "status": "verified", "verifiedAt": iso(now),
                    "checkedAt": iso(now), "agreeingPairCount": count, "advancingPairCount": advancing,
                    "transitions": transitions[-16:], "historicalClockApproximation": True}
    # A previous clock never overrides contradictory advancing quotes (DST,
    # server switch, local clock mismatch). Wait for sufficient new evidence.
    any_advancing = any(type(value) in (int, float) and math.isfinite(value)
                        and type(first.get(symbol)) in (int, float) and value > first[symbol]
                        for symbol, value in second.items())
    if previous and not any_advancing:
        from datetime import datetime, timezone
        checked, offset = stamp(previous["verifiedAt"]), previous["offsetSeconds"]
        age = now - checked
        current = datetime.fromtimestamp(now, timezone.utc)
        weekend = current.weekday() == 5 or (current.weekday() == 6 and current.hour < 21)
        observations = [value - offset for value in second.values()
                        if type(value) in (int, float) and math.isfinite(value) and value > 0]
        no_future = observations and max(observations) <= now + 5
        closed = no_future and weekend and 0 <= age <= 72 * 3600 and now - max(observations) <= 72 * 3600
        brief_pause = no_future and 0 <= age <= 900 and now - max(observations) <= 90
        if closed or brief_pause:
            return {**previous, "method": "previous_verified_live_ticks", "status": "held_market_closed" if closed else "held_brief_pause",
                    "checkedAt": iso(now), "historicalClockApproximation": True}
    raise ReadUnavailable("broker_clock_unverified" if any_advancing else "broker_clock_waiting_for_ticks")


def normalized_bar_time(raw_time, clock):
    """Exclude uncertain offset-change windows instead of inventing DST history.

    Older unobserved history still has an explicit approximation marker. Once
    an offset change is observed, both old and new interpretations must lie on
    the same side of the uncertainty window before a bar can be used.
    """
    offset = clock["offsetSeconds"]
    for transition in reversed(_clock_transitions(clock)):
        old, new = transition["fromOffset"], transition["toOffset"]
        before, after = stamp(transition["beforeUtc"]), stamp(transition["afterUtc"])
        candidates = (raw_time - old, raw_time - new)
        if max(candidates) + 3600 <= before:
            offset = old
        elif min(candidates) >= after:
            offset = new
            break
        else:
            return None
    return raw_time - offset


def collect_snapshot(config, *, api=None, guard_factory=process_guard, pause=time.sleep):
    """Config paths/PID injected by local trusted configuration, never from UI.

    Required terminalPath and dataPath. terminalPid is optional; without it
    enumerate already-running processes matching terminalPath, never launch.
    Current quote clocks are verified here; no HQ setup or prior clock required.
    Call in a bounded child process so a stuck native IPC cannot hang the server.
    """
    if config.get("enabled") is not True:
        raise ReadUnavailable("terminal_reader_disabled")
    terminal, data_path = Path(config.get("terminalPath", "")), Path(config.get("dataPath", ""))
    if not terminal.is_absolute() or not data_path.is_absolute() or not data_path.is_dir():
        raise ReadUnavailable("selected_terminal_paths_invalid")
    pid = config.get("terminalPid") or find_running_pid(terminal)
    verify, release = guard_factory(pid, terminal)
    initialized = False
    started = time.monotonic()
    try:
        try:
            mt5 = api if api is not None else importlib.import_module("MetaTrader5")
        except ModuleNotFoundError:
            raise ReadUnavailable("mt5_python_dependency_unavailable") from None
        verify()
        if not mt5.initialize(str(terminal), timeout=10000):
            raise ReadUnavailable("mt5_connection_unavailable")
        initialized = True
        verify()
        info = mt5.terminal_info()
        if info is None or Path(info.path).resolve() != terminal.parent.resolve() or Path(info.data_path).resolve() != data_path.resolve():
            raise ReadUnavailable("selected_terminal_binding_mismatch")
        if not info.connected:
            raise ReadUnavailable("broker_disconnected")
        symbols = mt5.symbols_get()
        if symbols is None:
            raise ReadUnavailable("symbol_catalog_unavailable")
        overrides = config.get("symbolMap") if isinstance(config.get("symbolMap"), dict) else {}
        choices = {instrument: choose_symbol(instrument, symbols, overrides.get(instrument)) for instrument in INSTRUMENTS}
        def ticks():
            observed = {}
            for instrument in INSTRUMENTS[:28]:
                symbol, _ = choices[instrument]
                tick = mt5.symbol_info_tick(symbol) if symbol else None
                if tick is not None:
                    value = getattr(tick, "time_msc", 0)
                    value = value / 1000 if type(value) in (int, float) and value > 0 else getattr(tick, "time", 0)
                    if type(value) in (int, float) and math.isfinite(value) and value > 0:
                        observed[instrument] = value
            return observed
        first, first_wall, first_mono = ticks(), time.time(), time.monotonic()
        previous = config.get("clock")
        binding = terminal_binding(config)
        for attempt in range(3):
            pause(.8 if attempt == 0 else 1.2)
            verify()
            second, now = ticks(), time.time()
            if abs((now - first_wall) - (time.monotonic() - first_mono)) > 5:
                raise ReadUnavailable("local_clock_changed_during_verification")
            try:
                clock = verified_clock(first, second, now, previous=previous, binding=binding)
                break
            except ReadUnavailable:
                if attempt == 2:
                    raise
        pairs = []
        for instrument in INSTRUMENTS:
            verify()
            symbol, error = choices[instrument]
            row = {"pair": instrument, "brokerSymbol": symbol, "series": {}, "errors": []}
            if error:
                row["errors"].append({"code": error})
            elif time.monotonic() - started > 70:
                row["errors"].append({"code": "collection_time_budget_reached"})
            else:
                raw = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 1, 350)
                if raw is None or not len(raw):
                    row["errors"].append({"code": "price_history_unavailable"})
                else:
                    bars, excluded = [], 0
                    for rate in raw:
                        raw_time, close = int(rate["time"]), float(rate["close"])
                        at = normalized_bar_time(raw_time, clock)
                        if at is None:
                            excluded += 1
                        elif math.isfinite(close) and close > 0 and at + 3600 <= time.time():
                            bars.append({"time": at, "brokerTime": raw_time, "close": close})
                    row["series"]["H1"] = bars
                    if excluded:
                        row["errors"].append({"code": "clock_transition_bars_excluded", "count": excluded})
            pairs.append(row)
        verify()
        # A second binding check detects operator changes to the data directory.
        final = mt5.terminal_info()
        if final is None or Path(final.path).resolve() != terminal.parent.resolve() or Path(final.data_path).resolve() != data_path.resolve() or not final.connected:
            raise ReadUnavailable("terminal_binding_changed")
        result = {"schemaVersion": "sentiment-mt5-h1-snapshot-v1", "collectedAt": iso(time.time()),
                "source": {"kind": "mt5_guarded_closed_bars", "closedBarsOnly": True, "requestedBars": 350,
                           "clock": clock},
                "pairs": pairs}
        if config.get("includeCatalog") is True:
            # Restricted research diagnostic only: no account/server/ticket fields.
            result["catalog"] = [{"name": str(s.name), "description": str(getattr(s, "description", "")),
                                  "base": str(getattr(s, "currency_base", "")), "profit": str(getattr(s, "currency_profit", "")),
                                  "visible": bool(getattr(s, "visible", False)), "custom": bool(getattr(s, "custom", False))}
                                 for s in symbols if re.search(r"OIL|BRENT|WTI|XBR|XTI|XAG|XAU|CRUDE", str(s.name) + " " + str(getattr(s, "description", "")), re.I)]
        return result
    finally:
        if initialized:
            mt5.shutdown()  # disconnect THIS Python client's IPC, never the terminal process
        release()


def main():
    if sys.argv[1:] != ["--stdin"]:
        return 2
    try:
        raw = sys.stdin.read(65537)
        if len(raw) > 65536:
            raise ReadUnavailable("collector_config_too_large")
        config = json.loads(raw)
        if not isinstance(config, dict):
            raise ReadUnavailable("collector_config_invalid")
        result = collect_snapshot(config)
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
        return 0
    except ReadUnavailable as error:
        print(json.dumps({"status": "unavailable", "errorCode": str(error)}))
        return 2
    except Exception:
        print(json.dumps({"status": "unavailable", "errorCode": "market_data_read_failed"}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
