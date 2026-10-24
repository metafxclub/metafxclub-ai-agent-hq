"""Bounded market-data reader for one already-running, explicitly selected MT5.

No login, chart changes, symbol selection, order API, account reads or terminal
launch command. Run as an isolated child so the parent can enforce a timeout.
"""
from __future__ import annotations

import argparse
from collections import Counter
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import sys
import time

PAIRS = ("AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD", "CADCHF", "CADJPY",
         "CHFJPY", "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
         "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD", "NZDCAD",
         "NZDCHF", "NZDJPY", "NZDUSD", "USDCAD", "USDCHF", "USDJPY")
TIMEFRAMES = ("M15", "H1", "H4", "D1", "W1")
SCHEMA = "fx28-market-snapshot-v1"


class DataUnavailable(RuntimeError):
    pass


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def choose_symbol(pair: str, symbols: list) -> tuple[str | None, str | None]:
    matches = [s for s in symbols if getattr(s, "currency_base", "") == pair[:3]
               and getattr(s, "currency_profit", "") == pair[3:]
               and getattr(s, "trade_calc_mode", None) in (0, 5)
               and not getattr(s, "custom", False)]
    exact = [s for s in matches if s.name.upper() == pair]
    visible = [s for s in matches if getattr(s, "visible", False)]
    choices = exact or visible or matches
    if len(choices) == 1:
        return str(choices[0].name), None
    return None, "symbol_ambiguous" if choices else "symbol_unavailable"


def verified_clock(first: dict, second: dict, now: float, previous: dict | None = None) -> dict:
    candidates = []
    for pair, stamp in second.items():
        if not isinstance(stamp, (int, float)) or not math.isfinite(stamp) or stamp <= 0:
            continue
        offset = round((stamp - now) / 900) * 900
        if abs(offset) <= 14 * 3600 and -5 <= now - (stamp - offset) <= 90:
            candidates.append((pair, stamp, offset))
    counts = Counter(row[2] for row in candidates)
    if counts:
        offset, count = counts.most_common(1)[0]
        advancing = any(stamp > first.get(pair, stamp) for pair, stamp, shift in candidates if shift == offset)
        if count >= 3 and count > len(candidates) / 2 and advancing:
            return {"basis": "broker_server_normalized", "offsetSeconds": offset,
                    "method": "live_tick_progress", "verifiedAt": iso_now(),
                    "agreeingPairCount": count, "rawTickTime": max(s for _,s,o in candidates if o == offset)}
    if previous:
        offset, checked = previous.get("offsetSeconds"), previous.get("verifiedAt")
        try:
            checked_at = datetime.fromisoformat(str(checked).replace("Z", "+00:00"))
            age = now - checked_at.timestamp() if checked_at.tzinfo else -1
        except (ValueError, TypeError):
            age = -1
        if (type(offset) is int and abs(offset) <= 14 * 3600 and offset % 900 == 0
                and 0 <= age <= 8 * 86400):
            if any(isinstance(stamp, (int, float)) and math.isfinite(stamp)
                   and stamp - offset > now + 5 for stamp in second.values()):
                raise DataUnavailable("broker_clock_unverified")
            return {"basis": "broker_server_normalized", "offsetSeconds": offset,
                    "method": "previous_verified_live_ticks", "verifiedAt": checked,
                    "historicalClockApproximation": True}
    raise DataUnavailable("broker_clock_unverified")


def process_guard(pid: int, executable: Path):
    if os.name != "nt" or pid <= 0 or executable.name.lower() != "terminal64.exe" or not executable.is_file():
        raise DataUnavailable("selected_terminal_unavailable")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        raise DataUnavailable("selected_terminal_not_running")

    def verify():
        buf = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(buf))
        code = wintypes.DWORD()
        if (not kernel.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size))
                or Path(buf.value).resolve() != executable.resolve()
                or not kernel.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value != 259):
            raise DataUnavailable("selected_terminal_process_changed")
    try:
        verify()
    except Exception:
        kernel.CloseHandle(handle)
        raise
    return verify, lambda: kernel.CloseHandle(handle)


def find_running_pid(executable: Path) -> int:
    """Find one existing executable without launching a shell or a Terminal."""
    if os.name != "nt":
        raise DataUnavailable("selected_terminal_unavailable")
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.EnumProcesses.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    processes = (wintypes.DWORD * 8192)()
    size = wintypes.DWORD()
    if not psapi.EnumProcesses(processes, ctypes.sizeof(processes), ctypes.byref(size)) or size.value >= ctypes.sizeof(processes):
        raise DataUnavailable("terminal_process_probe_unavailable")
    matches = []
    for pid in processes[:size.value // ctypes.sizeof(wintypes.DWORD)]:
        try:
            _, release = process_guard(pid, executable)
        except DataUnavailable:
            continue
        release()
        matches.append(pid)
    if len(matches) != 1:
        raise DataUnavailable("selected_terminal_not_running" if not matches else "selected_terminal_process_ambiguous")
    return matches[0]


def collect(mt5, terminal: Path, data_path: Path, candidate_id: str, verify_process,
            *, previous_clock: dict | None = None, pause=time.sleep, progress=None) -> dict:
    deadline = time.monotonic() + 90
    verify_process()
    if not mt5.initialize(str(terminal), timeout=10000):
        raise DataUnavailable("mt5_connection_unavailable")
    try:
        verify_process()
        info = mt5.terminal_info()
        if (info is None or Path(info.path).resolve() != terminal.parent.resolve()
                or Path(info.data_path).resolve() != data_path.resolve()):
            raise DataUnavailable("selected_terminal_binding_mismatch")
        if not info.connected:
            raise DataUnavailable("broker_disconnected")
        symbols = mt5.symbols_get()
        if symbols is None:
            raise DataUnavailable("symbol_catalog_unavailable")
        choices = {pair: choose_symbol(pair, list(symbols)) for pair in PAIRS}

        def ticks():
            output = {}
            for pair, (symbol, _) in choices.items():
                tick = mt5.symbol_info_tick(symbol) if symbol else None
                if tick is not None:
                    output[pair] = int(tick.time)
            return output

        first = ticks()
        pause(0.8)
        second = ticks()
        try:
            clock = verified_clock(first, second, time.time(), previous_clock)
        except DataUnavailable:
            pause(1.2)
            second = ticks()
            clock = verified_clock(first, second, time.time(), previous_clock)
        offset = clock["offsetSeconds"]
        pairs = []
        for pair, (symbol, error) in choices.items():
            row = {"pair": pair, "brokerSymbol": symbol, "series": {}, "errors": [],
                   "tickObservedAt": second.get(pair, 0) - offset if pair in second else None}
            if error:
                row["errors"].append({"code": error})
            else:
                for frame in TIMEFRAMES:
                    if time.monotonic() >= deadline:
                        row["errors"].append({"timeframe": frame, "code": "collection_time_budget_reached"})
                        continue
                    if progress:
                        progress(pair, frame, "start")
                    rates = mt5.copy_rates_from_pos(symbol, getattr(mt5, "TIMEFRAME_" + frame), 1, 200)
                    if progress:
                        progress(pair, frame, "done")
                    if rates is None or not len(rates):
                        row["errors"].append({"timeframe": frame, "code": "price_history_unavailable"})
                        continue
                    bars = []
                    for rate in rates:
                        bar = {key: float(rate[key]) for key in ("open", "high", "low", "close")}
                        if not all(math.isfinite(value) for value in bar.values()):
                            bars = []
                            row["errors"].append({"timeframe": frame, "code": "price_history_invalid"})
                            break
                        raw_time = int(rate["time"])
                        bar.update(time=raw_time-offset, brokerTime=raw_time,
                                   tick_volume=int(rate["tick_volume"]), real_volume=int(rate["real_volume"]),
                                   spread=int(rate["spread"]))
                        bars.append(bar)
                    if bars:
                        row["series"][frame] = bars
            pairs.append(row)
        verify_process()
        return {"schemaVersion": SCHEMA, "collectedAt": iso_now(),
                "source": {"kind": "mt5_closed_bars", "terminalCandidateId": candidate_id,
                           "closedBarsOnly": True, "requestedBars": 200, "clock": clock,
                           "timeNoteTh": "เวลาแท่งปรับจากเวลาของโบรกเกอร์ด้วยส่วนต่างนาฬิกาที่ตรวจได้; แท่งเก่าช่วง DST อาจคลาดหนึ่งชั่วโมง"},
                "pairs": pairs}
    finally:
        mt5.shutdown()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--terminal-path", required=True)
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--terminal-pid", type=int, default=0)
    parser.add_argument("--clock-offset-seconds", type=int)
    parser.add_argument("--clock-verified-at")
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args()
    release = None
    try:
        if not re.fullmatch(r"mtc-[a-z0-9-]{8,100}", args.candidate_id):
            raise DataUnavailable("selected_terminal_identity_invalid")
        terminal, data_path = Path(args.terminal_path), Path(args.data_path)
        if not terminal.is_absolute() or not data_path.is_absolute() or not data_path.is_dir():
            raise DataUnavailable("selected_terminal_paths_invalid")
        selected_pid = args.terminal_pid or find_running_pid(terminal)
        verify, release = process_guard(selected_pid, terminal)
        try:
            import MetaTrader5 as mt5
        except ImportError:
            raise DataUnavailable("mt5_python_dependency_missing") from None
        previous = {"offsetSeconds": args.clock_offset_seconds, "verifiedAt": args.clock_verified_at}
        progress = (lambda pair, frame, state: print(pair, frame, state, file=sys.stderr, flush=True)) if args.progress else None
        result = collect(mt5, terminal, data_path, args.candidate_id, verify, previous_clock=previous, progress=progress)
        # Service-launched Windows Python may use cp1252 rather than UTF-8.
        # ASCII JSON transports Thai metadata losslessly in either encoding.
        print(json.dumps(result, ensure_ascii=True, allow_nan=False, separators=(",", ":")))
        return 0
    except DataUnavailable as error:
        print(json.dumps({"schemaVersion": SCHEMA, "status": "unavailable", "errorCode": str(error), "collectedAt": iso_now()}))
        return 2
    except Exception:
        print(json.dumps({"schemaVersion": SCHEMA, "status": "error", "errorCode": "market_data_read_failed", "collectedAt": iso_now()}))
        return 3
    finally:
        if release:
            release()


if __name__ == "__main__":
    raise SystemExit(main())
