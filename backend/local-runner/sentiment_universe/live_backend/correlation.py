"""Read-only H1 correlation model. This module never imports a trading API.

Public output contains market-data metadata only, never terminal paths, accounts,
positions, orders, authentication data or the original snapshot object.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from itertools import combinations
import json
import hashlib
import math
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

INSTRUMENTS = (
    "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD", "CADCHF", "CADJPY",
    "CHFJPY", "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
    "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD", "NZDCAD",
    "NZDCHF", "NZDJPY", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
    "XAUUSD", "XAGUSD", "WTI", "BRENT",
)
METHOD = "pearson_aligned_consecutive_h1_log_returns"
MAX_SNAPSHOT_BYTES = 16 * 1024 * 1024
SERVICE_LOCK = threading.Lock()


def stamp(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value) if math.isfinite(value) else None
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.timestamp() if parsed.tzinfo else None
        except (ValueError, OverflowError):
            pass
    return None


def iso(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z") if value is not None else None


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _symbol(value):
    # Broker suffixes are data, not selectors or executable input.
    return value if isinstance(value, str) and 0 < len(value) <= 40 and all(c.isalnum() or c in "._-#" for c in value) else None


def _closed_weekend(last_end, now):
    current = datetime.fromtimestamp(now, timezone.utc)
    previous = datetime.fromtimestamp(last_end, timezone.utc)
    # A stale Thursday bar is not relabelled as a normal weekend closure.
    closed = current.weekday() == 5 or (current.weekday() == 6 and current.hour < 21)
    return closed and previous.weekday() == 4 and 0 <= now - last_end <= 72 * 3600


def _weekend_retry_at(now):
    current = datetime.fromtimestamp(now, timezone.utc)
    if current.weekday() == 5 or (current.weekday() == 6 and current.hour < 21):
        opening = (current + timedelta(days=6-current.weekday())).replace(hour=21, minute=0, second=0, microsecond=0)
        return opening.timestamp()
    return None


def _stale_return_end(last_end, now, max_age):
    # Freshness belongs to an actual observation used in the statistic. A lone
    # current bar after a gap does not create a new consecutive H1 return.
    return last_end is None or (now - last_end > max_age and not _closed_weekend(last_end, now))


def _returns(bars, now):
    points = {}
    invalid = 0
    for bar in bars if isinstance(bars, list) else []:
        if not isinstance(bar, dict):
            invalid += 1
            continue
        at, close = bar.get("time"), bar.get("close")
        if not (_number(at) and at > 0 and int(at) == at and _number(close) and close > 0):
            invalid += 1
            continue
        at = int(at)
        if at + 3600 > now:
            # The newest bar can be incomplete even when a producer labels it closed.
            continue
        if at in points and points[at] != close:
            return {}, None, invalid + 1, "conflicting_duplicate_bar"
        points[at] = float(close)
    ordered = sorted(points.items())
    result = {}
    for (previous_at, previous_close), (at, close) in zip(ordered, ordered[1:]):
        if at - previous_at != 3600:
            continue
        # These are CLOSE timestamps, so both start and end must match across assets.
        result[(previous_at + 3600, at + 3600)] = math.log(close) - math.log(previous_close)
    return result, ordered[-1][0] + 3600 if ordered else None, invalid, None


def pearson(xs, ys):
    """Stable centered Pearson; undefined for constant returns, never coerce to 0."""
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    x_mean, y_mean = math.fsum(xs) / len(xs), math.fsum(ys) / len(ys)
    dx, dy = [x - x_mean for x in xs], [y - y_mean for y in ys]
    xx, yy = math.fsum(x * x for x in dx), math.fsum(y * y for y in dy)
    if xx <= 1e-24 or yy <= 1e-24:
        return None
    return max(-1.0, min(1.0, math.fsum(x * y for x, y in zip(dx, dy)) / math.sqrt(xx * yy)))


def build(snapshot, *, now=None, lookback=200, min_samples=100, max_bar_age_seconds=10800,
          max_collection_age_seconds=1800, instruments=INSTRUMENTS):
    now = time.time() if now is None else float(now)
    if not 2 <= min_samples <= lookback <= 1000:
        raise ValueError("invalid_correlation_window")
    if len(set(instruments)) != len(instruments) or any(x not in INSTRUMENTS for x in instruments):
        raise ValueError("invalid_instrument_set")
    collected = stamp(snapshot.get("collectedAt")) if isinstance(snapshot, dict) else None
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    source = snapshot.get("source") if isinstance(snapshot.get("source"), dict) else {}
    trusted = source.get("kind") in ("mt5_closed_bars", "mt5_guarded_closed_bars") and source.get("closedBarsOnly") is True
    clock = source.get("clock") if isinstance(source.get("clock"), dict) else {}
    # Snapshot times must already be normalized. Do not guess a broker's UTC offset.
    trusted = trusted and clock.get("basis") == "broker_server_normalized" and _number(clock.get("offsetSeconds"))
    collection_stale = collected is None or collected > now + 30 or now - collected > max_collection_age_seconds
    raw_rows = snapshot.get("pairs") if isinstance(snapshot.get("pairs"), list) else []
    rows = {row.get("pair"): row for row in raw_rows if isinstance(row, dict) and row.get("pair") in instruments}
    series, public = {}, []
    for instrument in instruments:
        row = rows.get(instrument, {})
        frames = row.get("series") if isinstance(row.get("series"), dict) else {}
        returns, last_end, invalid, error = _returns(frames.get("H1", []), now) if trusted else ({}, None, 0, "unverified_source")
        recent = dict(sorted(returns.items())[-lookback:])
        last_return_end = max((interval[1] for interval in recent), default=None)
        status = "ready"
        if error:
            status = "invalid"
        elif not recent:
            status = "missing"
        elif ((collection_stale and not (_closed_weekend(last_return_end, now) and collected is not None and last_return_end <= collected <= now))
              or _stale_return_end(last_return_end, now, max_bar_age_seconds)):
            status = "stale"
        elif len(recent) < min_samples:
            status = "insufficient"
        elif pearson(list(recent.values()), list(recent.values())) is None:
            status = "flat"
        elif _closed_weekend(last_return_end, now):
            status = "market_closed"
        # Align the full fetched window first, then take the latest shared 200.
        # Truncating each instrument first would unnecessarily lose observations
        # around differing trading-session gaps.
        series[instrument] = (returns, status)
        row_errors = row.get("errors") if isinstance(row.get("errors"), list) else []
        producer_error = next((entry.get("code") for entry in row_errors if isinstance(entry, dict)
                               and isinstance(entry.get("code"), str) and len(entry["code"]) < 80
                               and entry["code"].replace("_", "").isalnum()), None)
        public.append({"symbol": instrument, "brokerSymbol": _symbol(row.get("brokerSymbol")),
                       "status": status, "samplesAvailable": len(recent), "lastBarClosedAt": iso(last_end),
                       "lastReturnEndAt": iso(last_return_end),
                       "invalidBars": invalid, "errorCode": error or producer_error})
    edges = []
    for left, right in combinations(instruments, 2):
        a, sa = series[left]
        b, sb = series[right]
        aligned = sorted(a.keys() & b.keys())[-lookback:]
        status = next((s for s in ("invalid", "missing", "stale", "insufficient", "flat") if s in (sa, sb)), "ready")
        # Individually fresh series may have no recent matching intervals. Never
        # publish an old shared window as current merely because each has newer
        # observations at different times.
        if status == "ready" and aligned and _stale_return_end(aligned[-1][1], now, max_bar_age_seconds):
            status = "stale"
        if status == "ready" and len(aligned) < min_samples:
            status = "insufficient_overlap"
        value = pearson([a[k] for k in aligned], [b[k] for k in aligned]) if status == "ready" else None
        if status == "ready" and value is None:
            status = "flat"
        edges.append({"source": left, "target": right, "value": round(value, 6) if value is not None else None,
                      "status": status, "samples": len(aligned), "startAt": iso(aligned[0][0]) if aligned else None,
                      "endAt": iso(aligned[-1][1]) if aligned else None})
    available = [row for row in public if row["status"] in ("ready", "market_closed")]
    status = "ready" if len(available) == len(instruments) and all(edge["status"] == "ready" for edge in edges) else "partial" if available else "unavailable"
    if available and all(row["status"] == "market_closed" for row in available):
        market_status = "market_closed"
    else:
        market_status = "open_or_unknown"
    return {"status": status, "source": "MT5", "sourceMode": "guarded_terminal" if source.get("kind") == "mt5_guarded_closed_bars" else "hq_cache",
            "timeframe": "H1", "method": METHOD, "lookback": lookback, "minSamples": min_samples,
            "lastSuccessAt": iso(collected) if available else None, "checkedAt": iso(now),
            "asOf": min((edge["endAt"] for edge in edges if edge["value"] is not None), default=None), "marketStatus": market_status,
            "items": edges, "instruments": public, "coverage": {"available": len(available), "total": len(instruments)},
            "clock": {"basis": clock.get("basis") if trusted else "unverified", "historicalClockApproximation": clock.get("historicalClockApproximation") is True,
                      "status": clock.get("status") if trusted else "unverified", "method": clock.get("method") if trusted else None,
                      "verifiedAt": clock.get("verifiedAt") if trusted else None, "offsetSeconds": clock.get("offsetSeconds") if trusted else None},
            "noteTh": "Correlation คือความสัมพันธ์ของผลตอบแทนย้อนหลัง ไม่ใช่การคาดการณ์ทิศทาง; เทียบเฉพาะช่วง H1 ที่ตรงกัน ไม่มีการเติมแท่งที่ขาด"}


def read_snapshot(path):
    """Bounded local-only read; malformed/in-progress producer writes fail closed."""
    target = Path(path)
    if not target.is_absolute():
        raise ValueError("snapshot_path_must_be_absolute")
    if target.stat().st_size > MAX_SNAPSHOT_BYTES:
        raise ValueError("snapshot_too_large")
    with target.open("rb") as stream:
        raw = stream.read(MAX_SNAPSHOT_BYTES + 1)
    if len(raw) > MAX_SNAPSHOT_BYTES:
        raise ValueError("snapshot_too_large")
    value = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("snapshot_invalid")
    return value


def collect(config):
    """Config: snapshotPath, now, lookback, minSamples, max*AgeSeconds.

    No automatic discovery, login, terminal launch or arbitrary URL fetching.
    A guarded collector may supply its own snapshotPath through this same API.
    """
    error = None
    try:
        snapshot = read_snapshot(config["snapshotPath"])
    except (OSError, ValueError, KeyError, TypeError):
        snapshot, error = {}, "snapshot_unavailable"
    result = build(snapshot, now=config.get("now"), lookback=config.get("lookback", 200),
                   min_samples=config.get("minSamples", 100), max_bar_age_seconds=config.get("maxBarAgeSeconds", 10800),
                   max_collection_age_seconds=config.get("maxCollectionAgeSeconds", 1800))
    if error:
        result["errorCode"] = error
    return result


def _read_optional(path):
    try:
        return read_snapshot(path)
    except (OSError, ValueError, TypeError):
        return {}


def _atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=True, allow_nan=False), encoding="utf-8")
    os.replace(temporary, path)


def _terminal_child(config):
    args = [config.get("pythonPath") or sys.executable, str(Path(__file__).with_name("mt5_reader.py")), "--stdin"]
    completed = subprocess.run(args, input=json.dumps(config, ensure_ascii=True), capture_output=True,
                               text=True, encoding="utf-8", timeout=90, shell=False,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if len(completed.stdout.encode("utf-8")) > MAX_SNAPSHOT_BYTES:
        return {"status": "unavailable", "errorCode": "collector_output_too_large"}
    try:
        result = json.loads(completed.stdout)
    except (ValueError, TypeError):
        return {"status": "unavailable", "errorCode": "collector_invalid_response"}
    return result if isinstance(result, dict) else {"status": "unavailable", "errorCode": "collector_invalid_response"}


def collect_for_service(config, state_dir, *, terminal_collector=None):
    """Read cache per request, refresh closed H1 at most once per hour.

    config: enabled, optional inputCachePath (HQ read-only), terminalPath, dataPath,
    optional candidateId, symbolMap, pythonPath, lookback, minSamples.
    All output files live in caller-owned state_dir; never modify inputCachePath.
    Missing native dependency/terminal/data fails over to the existing HQ cache.
    A stale direct cache does not mask a fresher HQ cache.
    """
    now = time.time()
    state = Path(state_dir).resolve()
    input_path = Path(config["inputCachePath"]).resolve() if config.get("inputCachePath") else None
    if input_path and (state == input_path.parent or input_path.parent in state.parents):
        return dict(build({}, now=now), errorCode="isolated_state_directory_required")
    path, metadata_path = state / "mt5-h1-snapshot.json", state / "mt5-h1-collector-state.json"
    binding = hashlib.sha256(json.dumps({key: config.get(key) for key in ("terminalPath", "dataPath", "selectionId", "candidateId", "symbolMap")}, sort_keys=True).encode()).hexdigest()
    with SERVICE_LOCK:
        upstream, cached, metadata = _read_optional(input_path) if input_path else {}, _read_optional(path), _read_optional(metadata_path)
        upstream_matches = bool(config.get("candidateId") and (upstream.get("source") or {}).get("terminalCandidateId") == config["candidateId"])
        # The pre-setup release used the same binding without selectionId. A
        # missing new field must not discard a still-valid commodity cache on
        # the weekend. Only migrate an exact old binding while HQ still proves
        # the legacy candidate; never carry data across a new UI selection.
        legacy_binding = hashlib.sha256(json.dumps({key: config.get(key) for key in ("terminalPath", "dataPath", "candidateId", "symbolMap")}, sort_keys=True).encode()).hexdigest()
        if (not config.get("selectionId") and upstream_matches and metadata.get("binding") == legacy_binding
                and cached.get("schemaVersion") == "sentiment-mt5-h1-snapshot-v1"):
            from live_backend.mt5_reader import terminal_binding
            clock = (cached.get("source") or {}).get("clock")
            if isinstance(clock, dict):
                clock["bindingId"] = terminal_binding(config)
            metadata["binding"] = binding
            _atomic_json(path, cached)
            _atomic_json(metadata_path, metadata)
        if metadata.get("binding") != binding:
            cached, metadata = {}, {}
        collected = stamp(cached.get("collectedAt"))
        last_attempt = stamp(metadata.get("lastAttemptAt"))
        retry_at = stamp(metadata.get("nextAttemptAt"))
        hour = int(now // 3600)
        dt = datetime.fromtimestamp(now, timezone.utc)
        weekend = dt.weekday() == 5 or (dt.weekday() == 6 and dt.hour < 21)
        cached_weekend = False
        if cached and collected is not None and now - collected < 72 * 3600 and weekend:
            cached_weekend = build(cached, now=now, max_collection_age_seconds=7200)["marketStatus"] == "market_closed"
        due = not cached or collected is None or int(collected // 3600) < hour
        due = due and not cached_weekend and (last_attempt is None or now - last_attempt >= 300) and (retry_at is None or retry_at <= now)
        error = metadata.get("errorCode")
        # New standalone selections are independent of HQ's trading selection.
        # Legacy HQ-bound configurations retain their original change guard.
        selected = bool(config.get("selectionId")) or not config.get("candidateId") or upstream_matches
        if config.get("selectionId") or (config.get("candidateId") and not upstream_matches):
            upstream = {}
        if config.get("enabled") is True and due and selected:
            try:
                from .mt5_reader import terminal_binding
            except ImportError:
                from live_backend.mt5_reader import terminal_binding
            request = {key: config[key] for key in ("terminalPath", "dataPath", "selectionId", "terminalPid", "symbolMap", "pythonPath") if key in config}
            clock = (cached.get("source") or {}).get("clock", {})
            if not clock and upstream_matches and not config.get("selectionId"):
                # Migration only: the legacy HQ candidate explicitly proves the
                # clock belongs to this configured terminal, never a guessed one.
                clock = dict((upstream.get("source") or {}).get("clock", {}))
                clock["bindingId"] = terminal_binding(request)
            request.update(enabled=True, clock=clock)
            metadata = {"binding": binding, "lastAttemptAt": iso(now)}
            try:
                received = (terminal_collector or _terminal_child)(request)
                if received.get("schemaVersion") != "sentiment-mt5-h1-snapshot-v1" or not received.get("collectedAt") or not isinstance(received.get("pairs"), list):
                    supplied = received.get("errorCode", "collector_unavailable")
                    error = supplied if isinstance(supplied, str) and supplied.replace("_", "").isalnum() and len(supplied) < 80 else "collector_unavailable"
                else:
                    cached, error = received, None
                    _atomic_json(path, cached)
            except (OSError, ValueError, TypeError, subprocess.TimeoutExpired):
                error = "collector_unavailable"
            metadata["errorCode"] = error
            retry_at = (_weekend_retry_at(now) if error == "broker_clock_waiting_for_ticks" else None) or (now+300 if error else (hour+1)*3600)
            metadata["nextAttemptAt"] = iso(retry_at)
            _atomic_json(metadata_path, metadata)
        elif config.get("enabled") is True and not selected:
            error = "selected_terminal_changed"
        # Include the latest HQ rows when a commodity-capable direct read is old.
        chosen = cached or upstream
        upstream_time, cache_time = stamp(upstream.get("collectedAt")), stamp(cached.get("collectedAt"))
        if cached and upstream and upstream_time is not None and (cache_time is None or upstream_time > cache_time + 3600):
            rows = {row.get("pair"): row for row in cached.get("pairs", []) if isinstance(row, dict)}
            for row in upstream.get("pairs", []):
                if isinstance(row, dict) and row.get("pair") in INSTRUMENTS:
                    rows[row["pair"]] = row
            chosen = dict(upstream, pairs=list(rows.values()))
        result = build(chosen, now=now, lookback=config.get("lookback", 200), min_samples=config.get("minSamples", 100),
                       max_collection_age_seconds=7200)
        result["refreshIntervalSeconds"] = 3600
        result["lastAttemptAt"] = metadata.get("lastAttemptAt")
        result["nextAttemptAt"] = iso(_weekend_retry_at(now) if cached_weekend else retry_at or ((hour+1)*3600)) if config.get("enabled") else None
        if error:
            result["refreshErrorCode"] = error
        if not config.get("enabled") and not upstream:
            result.update(status="needs_configuration", errorCode="mt5_selection_required")
        return result
