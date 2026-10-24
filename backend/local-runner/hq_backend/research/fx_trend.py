"""Pure, versioned FX28 closed-bar trend calculations and AI explanation contract.

No terminal, filesystem, network, account or order access belongs in this module.
Tick volume means broker quote activity; the score is not a probability of profit.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from datetime import datetime, timezone

from .fx_news_direct import FX_PAIRS

RESULT_PROFILE = "fx_trend_daily_v1"
PROCEDURE_ID = "backend.fx28-trend-daily-v1"
ACTION_ID = "analyze_fx28_trends"
REPORT_TYPE = "fx28_trend_report"
HORIZONS = {"short": ("M15", "H1"), "medium": ("H1", "H4", "D1"), "long": ("D1", "W1")}
SECONDS = {"M15": 900, "H1": 3600, "H4": 14400, "D1": 86400, "W1": 604800}
BEGIN = "FX28_LOCKED_ASSIGNMENT_BEGIN"
END = "FX28_LOCKED_ASSIGNMENT_END"
MAX_PROMPT_CHARS = 20000


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (ValueError, OverflowError):
        return None


def iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _ema(values, period):
    value = sum(values[:period]) / period
    for current in values[period:]:
        value += (current - value) * 2 / (period + 1)
    return value


def series_metrics(rows, timeframe, *, collected_at, clock_offset_seconds=0):
    if not isinstance(rows, list) or len(rows) < 60:
        raise ValueError("history_short")
    if len(rows) > 2000:
        raise ValueError("history_oversized")
    previous = None
    for row in rows:
        if not isinstance(row, dict) or not all(number(row.get(key)) for key in ("time", "open", "high", "low", "close", "tick_volume")):
            raise ValueError("invalid_ohlc")
        if row["time"] != int(row["time"]) or row["time"] <= 0 or (previous is not None and row["time"] <= previous):
            raise ValueError("non_monotonic_bars")
        if min(row["open"], row["close"], row["high"], row["low"]) <= 0 or row["tick_volume"] < 0 or not row["low"] <= min(row["open"], row["close"]) <= max(row["open"], row["close"]) <= row["high"]:
            raise ValueError("invalid_ohlc")
        previous = row["time"]
    closed_at = rows[-1]["time"] - clock_offset_seconds + SECONDS[timeframe]
    # Broker epochs can encode server wall time. The collector supplies a
    # verified offset; no heuristic per-bar shifting or fabricated candles.
    if closed_at > collected_at.timestamp() + 120:
        raise ValueError("unclosed_or_clock_mismatch")
    closes = [row["close"] for row in rows]
    ema20, ema50 = _ema(closes, 20), _ema(closes, 50)
    atr = sum(max(row["high"] - row["low"], abs(row["high"] - rows[index - 1]["close"]), abs(row["low"] - rows[index - 1]["close"])) for index, row in list(enumerate(rows))[-14:]) / 14
    slope = (ema20 - _ema(closes[:-5], 20)) / atr if atr > 0 else 0.0
    spread = (ema20 - ema50) / atr if atr > 0 else 0.0
    direction = 1 if closes[-1] > ema20 > ema50 and slope > 0.10 and spread > 0.10 else -1 if closes[-1] < ema20 < ema50 and slope < -0.10 and spread < -0.10 else 0
    prior_volume = sum(row["tick_volume"] for row in rows[-21:-1]) / 20
    return {"direction": direction, "close": closes[-1], "ema20": ema20, "ema50": ema50, "atr14": atr,
            "ema20SlopeAtr": slope, "emaSpreadAtr": spread,
            "return5Pct": (closes[-1] / closes[-6] - 1) * 100,
            "tickVolumeRatio20": rows[-1]["tick_volume"] / prior_volume if prior_volume else None,
            "barCount": len(rows), "lastClosedBarTime": int(rows[-1]["time"]),
            "dataAsOf": iso(datetime.fromtimestamp(closed_at, timezone.utc)), "historyDigest": digest(rows)}


def build_read_model(snapshot, *, now=None):
    now = now or datetime.now(timezone.utc)
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    collected = timestamp(snapshot.get("collectedAt"))
    source = snapshot.get("source") if isinstance(snapshot.get("source"), dict) else {}
    trusted = snapshot.get("schemaVersion") == "fx28-market-snapshot-v1" and source.get("kind") == "mt5_closed_bars" and collected is not None
    stale = not collected or (now - collected).total_seconds() > 1800 or (now - collected).total_seconds() < -120
    pairs = snapshot.get("pairs") if isinstance(snapshot.get("pairs"), list) else []
    by_pair = {}
    for row in pairs:
        if isinstance(row, dict) and row.get("pair") in FX_PAIRS:
            if row["pair"] in by_pair:
                trusted = False
            by_pair[row["pair"]] = row
    output = []
    error_th = {"history_short": "ประวัติน้อยกว่า 60 แท่ง", "invalid_ohlc": "ข้อมูลราคาไม่ผ่านการตรวจสอบ", "source_unavailable": "แหล่งข้อมูลยังไม่พร้อม", "non_monotonic_bars": "เวลาแท่งซ้ำหรือเรียงผิด", "unclosed_or_clock_mismatch": "แท่งยังไม่ปิดหรือเวลาไม่ตรง", "bars_stale": "แท่งล่าสุดเก่าเกินกรอบเวลา"}
    for pair in FX_PAIRS:
        current = by_pair.get(pair, {})
        series = current.get("series") if isinstance(current.get("series"), dict) else {}
        clock = current.get("clock") if isinstance(current.get("clock"), dict) else source.get("clock", {})
        offset = clock.get("serverOffsetSeconds", 0) if isinstance(clock, dict) else 0
        metrics, errors = {}, {}
        for frame in SECONDS:
            try:
                if not trusted or not number(offset) or abs(offset) > 86400:
                    raise ValueError("source_unavailable")
                item = series_metrics(series.get(frame), frame, collected_at=collected, clock_offset_seconds=offset)
                # A known weekend closure retains the last real bar. In an
                # open session an old bar is explicit stale, not forward-filled.
                age = collected.timestamp() - timestamp(item["dataAsOf"]).timestamp()
                weekend = collected.weekday() >= 5 or (collected.weekday() == 0 and collected.hour < 1)
                if age > max(SECONDS[frame] * 3, 3600) and not (weekend and age <= 259200 + SECONDS[frame]):
                    raise ValueError("bars_stale")
                metrics[frame] = item
            except (ValueError, TypeError, OverflowError) as error:
                errors[frame] = str(error)
        horizons = {}
        for name, frames in HORIZONS.items():
            available = all(frame in metrics for frame in frames)
            directions = [metrics[frame]["direction"] for frame in frames] if available else []
            bias = "BULLISH" if directions and all(value == 1 for value in directions) else "BEARISH" if directions and all(value == -1 for value in directions) else "SIDEWAY" if available else "INSUFFICIENT_DATA"
            status = "stale" if available and stale else "ready" if available else "insufficient_data"
            reason = "แท่งราคาปิดยืนยันแนวโน้มขาขึ้นตรงกัน" if bias == "BULLISH" else "แท่งราคาปิดยืนยันแนวโน้มขาลงตรงกัน" if bias == "BEARISH" else "ทิศทางแต่ละกรอบยังไม่สอดคล้อง หรือราคาอยู่ในช่วงแกว่ง" if available else "ข้อมูลแท่งปิดยังไม่ครบ: " + ", ".join(frame + " (" + error_th.get(errors.get(frame), "ยังไม่มีข้อมูล") + ")" for frame in frames if frame not in metrics)
            if stale and available:
                reason = "ข้อมูลรอบล่าสุดเก่าแล้ว: " + reason
            horizons[name] = {"bias": bias if status == "ready" else "INSUFFICIENT_DATA", "status": status, "reasonTh": reason,
                              "timeframes": list(frames), "dataAsOf": min((metrics[frame]["dataAsOf"] for frame in frames if frame in metrics), default=None),
                              "metrics": {frame: metrics[frame] for frame in frames if frame in metrics}}
        ready = sum(item["status"] == "ready" for item in horizons.values())
        refs = [{"id": f"price:{pair}:{frame}", "kind": "closed_bars", "pair": pair, "timeframe": frame, "dataAsOf": item["dataAsOf"]} for frame, item in metrics.items()]
        hourly = metrics.get("H1") or {}
        price_summary = (f"H1 ปิด {hourly['close']:.6g} · 5 แท่งล่าสุด {hourly['return5Pct']:+.2f}%" if hourly else "ยังไม่มีแท่ง H1 ที่ตรวจสอบได้")
        activity = hourly.get("tickVolumeRatio20")
        volume_summary = (f"H1 tick volume {activity:.2f} เท่าของค่าเฉลี่ย 20 แท่งก่อนหน้า · เป็นกิจกรรมราคาโบรกเกอร์" if number(activity) else "ยังไม่มี tick volume ที่ใช้เปรียบเทียบได้")
        output.append({"pair": pair, "brokerSymbol": str(current.get("brokerSymbol") or "")[:80] or None,
                       "status": "ready" if ready == 3 else "partial" if ready else "waiting", "horizons": horizons,
                       "priceSummaryTh": price_summary, "tickVolumeSummaryTh": volume_summary,
                       "newsSummaryTh": "บริบทข่าวแสดงแยกจากแนวโน้มราคา", "sourceRefs": refs})
    evaluated = sum(row["status"] == "ready" for row in output)
    some = any(row["status"] in {"ready", "partial"} for row in output)
    return {"schemaVersion": "fx28-trend-read-model-v1", "calculationVersion": "ema20-50-atr14-v1",
            "status": "ready" if evaluated == 28 else "partial" if some else "waiting", "snapshotId": "fx28-" + digest(snapshot)[:24] if trusted else None,
            "snapshotDigest": digest(snapshot) if trusted else None, "updatedAt": iso(collected) if collected else None,
            "dataAsOf": max((ref["dataAsOf"] for row in output for ref in row["sourceRefs"]), default=None),
            "stale": stale, "rows": output, "summary": {"evaluatedPairCount": evaluated, "totalPairCount": 28},
            "analysisOnly": True, "orderSubmissionAllowed": False}


def make_assignment(model, market_date, news_sources=()):
    if model.get("status") not in {"ready", "partial"} or model.get("stale") is not False:
        raise ValueError("price_snapshot_not_ready")
    refs = []
    rows = []
    for row in model["rows"]:
        refs.extend({"id": ref["id"], "kind": "closed_bars"} for ref in row["sourceRefs"])
        rows.append({"pair": row["pair"], "horizons": {name: {"bias": h["bias"], "status": h["status"], "timeframes": h["timeframes"],
                     "metrics": {frame: {key: round(value, 6) if isinstance(value, float) else value for key, value in metric.items() if key in {"close", "ema20", "ema50", "ema20SlopeAtr", "tickVolumeRatio20"}} for frame, metric in h["metrics"].items()}}
                    for name, h in row["horizons"].items()}})
        hourly = row["horizons"]["short"]["metrics"].get("H1") or {}
        rows[-1]["priceFeatures"] = {key: round(hourly[source], 4) if number(hourly.get(source)) else None
                                    for key, source in (("h1Change5Pct", "return5Pct"), ("h1TickVolumeRatio20", "tickVolumeRatio20"))}
    for source in list(news_sources)[:3]:
        if not isinstance(source, dict) or not re.fullmatch(r"https://[^\s]+", str(source.get("url") or "")):
            continue
        refs.append({"id": "news:" + digest(source["url"])[:16], "kind": "news", "url": source["url"], "title": str(source.get("title") or "Official news")[:120]})
    assignment = {"schemaVersion": "fx28-trend-assignment-v1", "snapshotId": model["snapshotId"], "snapshotDigest": model["snapshotDigest"], "marketDate": market_date,
                  "pairs": list(FX_PAIRS), "sourceRefs": refs, "rows": rows}
    # Keep 28x3 context under a fixed transport budget; metrics are optional
    # detail only. Snapshot identity, directions, missing states and refs remain.
    if len(canonical(assignment)) > 18000:
        for row in rows:
            for horizon in row["horizons"].values():
                horizon.pop("metrics", None)
                horizon.pop("timeframes", None)
    if len(canonical(assignment)) > 18500:
        raise ValueError("fx28_assignment_too_large")
    return assignment


def render_prompt(assignment):
    text = ("Explain the locked FX28 closed-bar trends in concise Thai. Prices, direction and source timestamps are immutable Backend facts; never output new prices, bias, confidence or trade instructions. "
            "Fixed horizons: short=M15+H1, medium=H1+H4+D1, long=D1+W1. Each horizon must cite every available price:PAIR:TF ID in that mapping. "
            "Explain each short/medium/long horizon using only the supplied source IDs. Missing prices must be described as insufficient data. Tick volume is broker quote activity, not exchange volume. "
            "Public news sources are optional independent context; open any cited exact URL individually in the main process before summarizing it. No orders, accounts, terminal controls, file writes or child agents. "
            "Return only the strict JSON object: snapshotId,snapshotDigest,marketDate,pairExplanations,summaryTh,newsContext,limitations. "
            "pairExplanations contains all 28 pairs; each has pair and short/medium/long {reasonTh (max120 chars),sourceRefs:[locked IDs]}. Summary max500; newsContext max3 {sourceRef,summaryTh}; limitations max5 strings.\n"
            + BEGIN + "\n" + canonical(assignment) + "\n" + END)
    if len(text) > MAX_PROMPT_CHARS:
        raise ValueError("fx28_prompt_too_large")
    return text


def prompt_assignment(prompt):
    if not isinstance(prompt, str) or len(prompt) > MAX_PROMPT_CHARS or prompt.count(BEGIN) != 1 or prompt.count(END) != 1:
        raise ValueError("fx28_assignment_missing")
    before, content = prompt.split(BEGIN)
    raw, trailing = content.split(END)
    if trailing.strip():
        raise ValueError("fx28_assignment_not_terminal")
    value = json.loads(raw)
    if not isinstance(value, dict) or set(value) != {"schemaVersion", "snapshotId", "snapshotDigest", "marketDate", "pairs", "sourceRefs", "rows"} or value.get("schemaVersion") != "fx28-trend-assignment-v1" or value.get("pairs") != list(FX_PAIRS):
        raise ValueError("fx28_assignment_invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", str(value.get("snapshotDigest") or "")) or value.get("snapshotId") != "fx28-" + value["snapshotDigest"][:24] or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value.get("marketDate") or "")):
        raise ValueError("fx28_assignment_identity_invalid")
    if not isinstance(value["sourceRefs"], list) or len(value["sourceRefs"]) > 143 or not isinstance(value["rows"], list) or [row.get("pair") for row in value["rows"]] != list(FX_PAIRS):
        raise ValueError("fx28_assignment_rows_invalid")
    ids = [row.get("id") for row in value["sourceRefs"] if isinstance(row, dict)]
    if len(ids) != len(value["sourceRefs"]) or len(set(ids)) != len(ids):
        raise ValueError("fx28_assignment_sources_invalid")
    for row in value["sourceRefs"]:
        if row.get("kind") == "closed_bars":
            parts = str(row.get("id") or "").split(":")
            if len(parts) != 3 or parts[0] != "price" or parts[1] not in FX_PAIRS or parts[2] not in SECONDS:
                raise ValueError("fx28_price_source_invalid")
        elif row.get("kind") == "news":
            if not re.fullmatch(r"https://[^\s]+", str(row.get("url") or "")) or row.get("id") != "news:" + digest(row["url"])[:16]:
                raise ValueError("fx28_news_source_invalid")
        else:
            raise ValueError("fx28_source_kind_invalid")
    for row in value["rows"]:
        if not isinstance(row.get("horizons"), dict) or set(row["horizons"]) != set(HORIZONS):
            raise ValueError("fx28_assignment_horizons_invalid")
        for name, horizon in row["horizons"].items():
            if not isinstance(horizon, dict) or horizon.get("bias") not in {"BULLISH", "BEARISH", "SIDEWAY", "INSUFFICIENT_DATA"} or horizon.get("status") not in {"ready", "insufficient_data", "stale", "error"}:
                raise ValueError("fx28_assignment_horizons_invalid")
    return value


def _text(value, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", value):
        raise ValueError("fx28_text_invalid")
    return value.strip()


def validate_explanations(payload, assignment):
    assignment = prompt_assignment(render_prompt(assignment))
    keys = {"snapshotId", "snapshotDigest", "marketDate", "pairExplanations", "summaryTh", "newsContext", "limitations"}
    if not isinstance(payload, dict) or set(payload) != keys or any(payload.get(key) != assignment[key] for key in ("snapshotId", "snapshotDigest", "marketDate")):
        raise ValueError("fx28_result_binding_invalid")
    rows = payload["pairExplanations"]
    if not isinstance(rows, list) or len(rows) != 28 or set(row.get("pair") for row in rows if isinstance(row, dict)) != set(FX_PAIRS):
        raise ValueError("fx28_result_pairs_invalid")
    sources = {item["id"]: item for item in assignment["sourceRefs"]}
    for row in rows:
        if set(row) != {"pair", "short", "medium", "long"}:
            raise ValueError("fx28_result_fields_invalid")
        for name, frames in HORIZONS.items():
            item = row[name]
            if not isinstance(item, dict) or set(item) != {"reasonTh", "sourceRefs"}:
                raise ValueError("fx28_horizon_fields_invalid")
            _text(item["reasonTh"], 120)
            refs = item["sourceRefs"]
            if not isinstance(refs, list) or len(refs) > 6 or len(set(refs)) != len(refs):
                raise ValueError("fx28_horizon_sources_invalid")
            for ref in refs:
                source = sources.get(ref)
                if not source or source["kind"] == "closed_bars" and ref not in {f"price:{row['pair']}:{frame}" for frame in frames}:
                    raise ValueError("fx28_horizon_source_mismatch")
            expected = [f"price:{row['pair']}:{frame}" for frame in frames if f"price:{row['pair']}:{frame}" in sources]
            if any(ref not in refs for ref in expected):
                raise ValueError("fx28_price_evidence_missing")
    _text(payload["summaryTh"], 500)
    news = payload["newsContext"]
    if not isinstance(news, list) or len(news) > 3:
        raise ValueError("fx28_news_invalid")
    for item in news:
        if not isinstance(item, dict) or set(item) != {"sourceRef", "summaryTh"} or sources.get(item.get("sourceRef"), {}).get("kind") != "news":
            raise ValueError("fx28_news_source_invalid")
        _text(item["summaryTh"], 300)
    used_news = {ref for row in rows for name in HORIZONS for ref in row[name]["sourceRefs"] if sources[ref]["kind"] == "news"}
    if not used_news.issubset({item["sourceRef"] for item in news}):
        raise ValueError("fx28_unverified_news_reference")
    if not isinstance(payload["limitations"], list) or len(payload["limitations"]) > 5:
        raise ValueError("fx28_limitations_invalid")
    for value in payload["limitations"]:
        _text(value, 200)
    return copy.deepcopy(payload)


def result_schema():
    text = lambda size: {"type": "string", "minLength": 1, "maxLength": size}
    def obj(fields):
        return {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}
    horizon = obj({"reasonTh": text(120), "sourceRefs": {"type": "array", "items": text(100), "maxItems": 6}})
    return obj({"snapshotId": text(40), "snapshotDigest": text(64), "marketDate": text(10),
                "pairExplanations": {"type": "array", "minItems": 28, "maxItems": 28, "items": obj({"pair": {"type": "string", "enum": list(FX_PAIRS)}, **{name: horizon for name in HORIZONS}})},
                "summaryTh": text(500), "newsContext": {"type": "array", "maxItems": 3, "items": obj({"sourceRef": text(100), "summaryTh": text(300)})},
                "limitations": {"type": "array", "maxItems": 5, "items": text(200)}})
