"""Council evidence journal owned by the existing Bridge, not another scheduler.

Only explicit observe/archive calls write. Reading a missing database never creates
it. Unknown intervals describe missing observations, not invented candles or proof
that Windows/the UI was closed. No provider, terminal or Mission dependencies.
"""
from __future__ import annotations

import hashlib
import base64
import binascii
import json
import math
from pathlib import Path
import re
import sqlite3
import threading
from datetime import datetime, timezone

SCHEMA = "council-operations-v1"
HEARTBEAT_SECONDS = 30
STALE_SECONDS = 90
ROLES = ("technical", "price_action", "news")
NORMAL_REASONS = frozenset({"ready", "waiting", "new_bar_only_wait_next_bar",
    "closed_bar_round_queued", "closed_bar_round_already_recorded", "snapshot_settling",
    "waiting_for_snapshot_settle", "council_round_terminal", "analysis_snapshot_ready_before_start"})
LIMITATIONS = [
    "ปิดหน้าเว็บไม่เท่ากับปิด Bridge; ช่วงไม่มีข้อมูลไม่ใช่หลักฐานว่าเครื่องหรือโปรแกรมปิด",
    "ประวัติเริ่มตั้งแต่เปิดการบันทึกนี้; เหตุการณ์ก่อนหน้านั้นยืนยันได้เฉพาะหลักฐานที่ยังเก็บอยู่",
    "เติมได้เฉพาะประวัติแท่งจริงที่อ่านได้ ไม่มีการเรียก AI วิเคราะห์ย้อนหลัง",
    "เมื่อเครื่องและตัวตรวจทั้งหมดหยุด จะบันทึกช่วงที่ขาดหลังกลับมาทำงาน ไม่สามารถแจ้งเตือนจากเครื่องที่ดับได้",
]


def _time(value):
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, str):
        try:
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    return result.astimezone(timezone.utc) if result.tzinfo else None


def _iso(value):
    parsed = _time(value)
    return parsed.isoformat() if parsed else None


def _code(value, default="unknown"):
    value = str(value or "")
    return value if re.fullmatch(r"[A-Za-z0-9_.:-]{1,120}", value) else default


def _symbol(value):
    value = str(value or "")
    return value if re.fullmatch(r"[A-Za-z0-9_.#-]{1,32}", value) else None


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True, allow_nan=False)


def _id(*parts):
    return hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:32]


def decode_cursor(cursor):
    if not isinstance(cursor, str) or not re.fullmatch(r"page-[A-Za-z0-9_-]{1,220}", cursor):
        raise ValueError("invalid_cursor")
    try:
        token = cursor[5:]
        value = json.loads(base64.urlsafe_b64decode(token + "=" * (-len(token) % 4)))
    except (ValueError, UnicodeError, binascii.Error) as error:
        raise ValueError("invalid_cursor") from error
    if (not isinstance(value, list) or len(value) != 2
            or not isinstance(value[0], str) or value[0] and _iso(value[0]) != value[0]
            or not isinstance(value[1], int) or isinstance(value[1], bool)
            or not 0 < value[1] < 9_223_372_036_854_775_807):
        raise ValueError("invalid_cursor")
    return tuple(value)


def _cursor(stamp, seq):
    return "page-" + base64.urlsafe_b64encode(_json([stamp, seq]).encode()).decode().rstrip("=")


def sanitize_evidence(value):
    """Intentionally omit free-form errors, paths, account IDs, tickets and secrets."""
    source = value if isinstance(value, dict) else {}
    result = {}
    for key in ("afterClosedBarTime", "beforeClosedBarTime", "closedBarTime", "availableBars",
                "processesStarted", "completedVotes", "requiredVotes", "cacheAgeSeconds",
                "durationMs", "remainingPercent", "maximumSnapshotAgeSeconds", "snapshotAgeSeconds"):
        v = source.get(key)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v):
            result[key] = v
    exit_code = source.get("exitCode")
    if isinstance(exit_code, int) and not isinstance(exit_code, bool):
        result["exitCode"] = exit_code
    elif exit_code in {"not_found", "timeout", "cancelled"}:
        result["exitCode"] = exit_code
    for key in ("ok", "stale", "servedStale", "limitReached", "snapshotCaptured",
                "identityReady", "sameSnapshot", "terminalActions", "aiRunAllowed"):
        if isinstance(source.get(key), bool):
            result[key] = source[key]
    for key in ("source", "status", "errorType", "errorCode", "reasonCode", "attemptStatus", "missionId"):
        if source.get(key) is not None:
            result[key] = _code(source[key])
    for key in ("checkedAt", "snapshotObservedAt", "previousSeenAt"):
        if _iso(source.get(key)):
            result[key] = _iso(source[key])
    return result


def summarize_round(parent, children):
    """Evidence of execution, not a new voting/consensus policy."""
    parent = parent if isinstance(parent, dict) else {}
    context = parent.get("analysisContext") if isinstance(parent.get("analysisContext"), dict) else {}
    children = children if isinstance(children, list) else []
    snapshot = context.get("snapshotId")
    digest = context.get("snapshotArtifactDigest")
    identity_valid = bool(re.fullmatch(r"[0-9a-f]{64}", str(snapshot or ""))
                          and re.fullmatch(r"[0-9a-f]{64}", str(digest or "")))
    roles = []
    for role in ROLES:
        matches = [c for c in children if isinstance(c, dict)
                   and isinstance(c.get("analysisContext"), dict)
                   and c["analysisContext"].get("roleId") == role
                   and c.get("parentMissionId") == parent.get("id")]
        child = matches[0] if len(matches) == 1 else {}
        ctx = child.get("analysisContext") if isinstance(child.get("analysisContext"), dict) else {}
        vote = child.get("councilVote") or {}
        if not isinstance(vote, dict):
            vote = {}
        execution = child.get("execution") if isinstance(child.get("execution"), dict) else {}
        started = execution.get("processStarted") is True
        same = bool(identity_valid and ctx.get("snapshotId") == snapshot
                    and ctx.get("snapshotArtifactDigest") == digest)
        confidence = vote.get("confidence")
        valid = bool(started and same and child.get("status") == "completed"
                     and vote.get("decision") in {"BUY", "SELL", "HOLD", "NO_DATA"}
                     and isinstance(confidence, (int, float)) and not isinstance(confidence, bool)
                     and math.isfinite(confidence) and 0 <= confidence <= 100
                     and vote.get("snapshotId") == snapshot
                     and vote.get("roleId") == role)
        roles.append({"roleId": role, "status": _code(child.get("status"), "missing"),
                      "processStarted": started, "sameSnapshot": same, "validVote": valid,
                      "decision": vote.get("decision") if valid else None,
                      "confidence": confidence if valid else None,
                      "startedAt": _iso(child.get("startedAt")), "completedAt": _iso(child.get("completedAt"))})
    count = sum(r["validVote"] for r in roles)
    started = sum(r["processStarted"] for r in roles)
    terminal = parent.get("status") in {"completed", "blocked", "failed", "archived"}
    status = ("complete_all" if count == 3 else ("running" if started else "queued") if not terminal
              else "partial" if count else "failed" if started else "not_started")
    decision = parent.get("councilDecision") if isinstance(parent.get("councilDecision"), dict) else {}
    direction = decision.get("decision")
    return {"attemptStatus": status, "processesStarted": started, "completedVotes": count,
            "requiredVotes": 3, "sameSnapshot": all(r["sameSnapshot"] for r in roles), "roles": roles,
            "finalDecision": direction if direction in {"BUY", "SELL", "HOLD", "NO_TRADE", "NO_DATA"} else None}


def _message(reason):
    return {
        "monitoring_started": "เริ่มเก็บประวัติการตรวจ; ไม่ยืนยันช่วงเวลาก่อนหน้านี้",
        "bridge_started": "เริ่ม Bridge รอบใหม่",
        "bridge_clean_shutdown": "Bridge บันทึกการปิดตามขั้นตอนแล้ว",
        "bridge_stopped_interval": "ช่วงหลัง Bridge บันทึกการปิดจนเริ่มใหม่",
        "observation_gap_unknown": "ขาดการตรวจช่วงนี้; ยังยืนยันสาเหตุไม่ได้",
        "gap_history_unavailable": "ประวัติแท่งไม่ครอบคลุมช่วงที่ขาด จึงยังยืนยันจำนวนแท่งไม่ได้",
        "automation_disabled": "ปิดการวิเคราะห์อัตโนมัติอยู่",
        "global_metatrader_locks_incomplete": "การเลือกและล็อก MT4/MT5 ยังไม่พร้อม",
        "scheduler_loop_error": "ตัวตรวจพบข้อผิดพลาด; ดูรหัสสาเหตุที่บันทึก",
    }.get(reason, "บันทึกสถานะจากสภา AI; ดูรหัสสาเหตุและหลักฐานประกอบ")


class CouncilJournal:
    def __init__(self, path):
        self.path = Path(path)
        self._lock = threading.RLock()
        self._last_sample = None
        self._last_fingerprint = None
        self._coverage_hashes = {}
        self.last_error = None

    def _connect(self, *, write):
        # The configured runtime directory is the boundary, including read-only
        # requests. Never follow a journal symlink to another application/file.
        if self.path.is_symlink() or self.path.resolve().parent != self.path.parent.resolve():
            raise OSError("journal_path_outside_runtime")
        if write:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(str(self.path), timeout=0.05)
            # DELETE avoids a nominally read-only GET creating WAL/SHM sidecars.
            try:
                connection.execute("PRAGMA journal_mode=DELETE")
                connection.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                connection.execute("CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, payload TEXT NOT NULL)")
                connection.execute("CREATE TABLE IF NOT EXISTS coverage (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
                connection.execute("CREATE INDEX IF NOT EXISTS events_time ON events(COALESCE(json_extract(payload,'$.startedAt'),''),seq)")
                connection.execute("CREATE INDEX IF NOT EXISTS events_kind ON events(json_extract(payload,'$.type'),seq)")
            except BaseException:
                connection.close()
                raise
        else:
            connection = sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True, timeout=0.05)
            connection.execute("PRAGMA query_only=ON")
        return connection

    def _write(self, operation):
        if not self._lock.acquire(blocking=False):
            self.last_error = "observability_writer_busy"
            return False
        connection = None
        try:
            connection = self._connect(write=True)
            with connection:
                operation(connection)
            self.last_error = None
            return True
        except (OSError, sqlite3.Error, ValueError, TypeError) as error:
            self.last_error = "observability_" + type(error).__name__
            return False
        finally:
            if connection is not None:
                connection.close()
            self._lock.release()

    @staticmethod
    def _meta(connection):
        row = connection.execute("SELECT value FROM meta WHERE key='state'").fetchone()
        state = json.loads(row[0]) if row else {}
        if not isinstance(state, dict):
            raise ValueError("invalid_observability_state")
        return state

    @staticmethod
    def _save_meta(connection, state):
        connection.execute("INSERT INTO meta(key,value) VALUES('state',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (_json(state),))

    @staticmethod
    def _event(connection, event):
        connection.execute("INSERT INTO events(id,payload) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload", (event["id"], _json(event)))

    @staticmethod
    def _new_event(kind, reason, now, *, started=None, ended=None, certainty="confirmed", status="recorded", evidence=None, symbol=None, timeframe=None, key=None):
        return {"id": _id(kind, reason, key or now), "type": kind, "status": status,
                "severity": "warning" if kind in {"gap", "incident"} else "info",
                "startedAt": started or now, "endedAt": ended, "lastSeenAt": now,
                "reasonCode": _code(reason), "messageTh": _message(reason), "occurrences": 1,
                "symbol": _symbol(symbol), "timeframe": _symbol(timeframe), "certainty": certainty,
                "evidence": sanitize_evidence(evidence)}

    def observe(self, *, now, startup_id, reason="ready", symbol=None, timeframe=None, evidence=None, blocked=False):
        now = _iso(now)
        if not now or not startup_id:
            return False
        fingerprint = (startup_id, _code(reason), _symbol(symbol), _symbol(timeframe), bool(blocked))
        if (fingerprint == self._last_fingerprint and self._last_sample
                and 0 <= (_time(now) - _time(self._last_sample)).total_seconds() < HEARTBEAT_SECONDS):
            return True

        def write(connection):
            state = self._meta(connection)
            previous = state.get("lastSeenAt")
            changed_start = bool(state and state.get("startupId") != startup_id)
            elapsed = (_time(now) - _time(previous)).total_seconds() if _time(previous) else None
            if not state:
                self._event(connection, self._new_event("lifecycle", "monitoring_started", now,
                            certainty="unknown", evidence={"source": "first_observation"}))
            if changed_start or not state:
                self._event(connection, self._new_event("lifecycle", "bridge_started", now, key=startup_id))
            if previous and (changed_start or elapsed is not None and elapsed > STALE_SECONDS):
                clean = bool(changed_start and state.get("cleanStoppedAt"))
                self._event(connection, self._new_event("gap", "bridge_stopped_interval" if clean else "observation_gap_unknown",
                    now, started=state.get("cleanStoppedAt") if clean else previous, ended=now,
                    certainty="confirmed" if clean else "unknown", key=(state.get("startupId"), previous, startup_id),
                    evidence={"source": "bridge_shutdown_receipt" if clean else "heartbeat_gap", "aiRunAllowed": False}))
            active = state.get("incident")
            incident_key = (_code(reason), _symbol(symbol), _symbol(timeframe))
            previous_key = (active.get("reasonCode"), active.get("symbol"), active.get("timeframe")) if active else None
            if active and (not blocked or incident_key != previous_key or changed_start):
                active.update(status="recovered" if not blocked else "superseded", endedAt=now, lastSeenAt=now)
                self._event(connection, active)
                active = None
            if blocked:
                if active:
                    active.update(lastSeenAt=now, occurrences=active["occurrences"] + 1, evidence=sanitize_evidence(evidence))
                else:
                    active = self._new_event("incident", reason, now, status="active", evidence=evidence, symbol=symbol, timeframe=timeframe)
                self._event(connection, active)
            state.update(startupId=startup_id, lastSeenAt=now, cleanStoppedAt=None, incident=active,
                         symbol=_symbol(symbol), timeframe=_symbol(timeframe), reasonCode=_code(reason))
            self._save_meta(connection, state)

        ok = self._write(write)
        if ok:
            self._last_sample, self._last_fingerprint = now, fingerprint
        return ok

    def stopped(self, *, now, startup_id):
        now = _iso(now)
        if not now:
            return False
        def write(connection):
            state = self._meta(connection)
            if state.get("startupId") != startup_id:
                return
            self._event(connection, self._new_event("lifecycle", "bridge_clean_shutdown", now,
                        key=startup_id, evidence={"source": "bridge_shutdown_receipt"}))
            state.update(cleanStoppedAt=now, lastSeenAt=now)
            self._save_meta(connection, state)
        return self._write(write)

    def gap(self, *, now, after_bar=None, before_bar=None, symbol=None, timeframe=None, available_bars=0, key=None, reason="gap_history_unavailable"):
        now = _iso(now)
        if not now:
            return False
        event = self._new_event("gap", _code(reason), now, ended=now, certainty="unknown",
            symbol=symbol, timeframe=timeframe, key=key or (symbol, timeframe, after_bar, before_bar),
            evidence={"afterClosedBarTime": after_bar, "beforeClosedBarTime": before_bar,
                      "availableBars": available_bars, "aiRunAllowed": False, "source": "snapshot_history_bounds"})
        return self._write(lambda connection: self._event(connection, event))

    def archive(self, records, *, round_summary=None, round_summaries=None):
        """Archive only observed coverage; never infer bars or use it as a work queue."""
        rows = []
        hashes = {}
        for record in records:
            if not isinstance(record, dict):
                continue
            stream, bar = record.get("streamKey"), record.get("closedBarTime")
            if not re.fullmatch(r"[0-9a-f]{64}", str(stream or "")) or not isinstance(bar, int) or isinstance(bar, bool) or bar < 0:
                continue
            key = _id(stream, bar)
            safe = {k: record.get(k) for k in ("streamKey", "closedBarTime", "symbol", "timeframe", "status", "reasonCode", "missionId", "detectedAt", "completedAt", "snapshotId", "snapshotArtifactDigest")}
            safe["reasonCode"] = _code(safe.get("reasonCode"))
            safe["missionId"] = _code(safe.get("missionId"), "") or None
            safe["symbol"], safe["timeframe"] = _symbol(safe.get("symbol")), _symbol(safe.get("timeframe"))
            summary = round_summary or (round_summaries or {}).get((stream, bar))
            if summary:
                safe["round"] = summary
            digest = _id(_json(safe))
            if self._coverage_hashes.get(key) != digest:
                rows.append((key, safe))
                hashes[key] = digest
        if not rows:
            return True

        def write(connection):
            for key, safe in rows:
                existing = connection.execute("SELECT payload FROM coverage WHERE id=?", (key,)).fetchone()
                previous = json.loads(existing[0]) if existing else {}
                if previous.get("round") and not safe.get("round"):
                    safe["round"] = previous["round"]
                # Old bootstrap/cache evidence must not downgrade terminal evidence.
                if previous.get("status") in {"analyzed", "skipped"} and safe.get("status") in {"pending", "queued"}:
                    continue
                connection.execute("INSERT INTO coverage(id,payload) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload", (key, _json(safe)))
                status = safe.get("status")
                summary = safe.get("round") or {}
                attempt = summary.get("attemptStatus") or ("not_started" if status == "skipped" else "queued" if status in {"pending", "queued"} else "unknown")
                now = _iso(safe.get("completedAt")) or _iso(safe.get("detectedAt"))
                event = self._new_event("bar", safe["reasonCode"], now, key=key,
                    started=_iso(safe.get("detectedAt")), ended=_iso(safe.get("completedAt")), status=status or "unknown",
                    symbol=safe.get("symbol"), timeframe=safe.get("timeframe"),
                    evidence={**summary, "closedBarTime": safe["closedBarTime"], "missionId": safe.get("missionId"),
                              "source": "observed_bar_coverage", "attemptStatus": attempt})
                event["id"] = "bar-" + key
                event["attemptStatus"] = attempt
                event["roles"] = summary.get("roles", [])
                event["finalDecision"] = summary.get("finalDecision")
                self._event(connection, event)
        ok = self._write(write)
        if ok:
            self._coverage_hashes.update(hashes)
            # This is only a skip-unchanged optimization; SQL is authoritative.
            if len(self._coverage_hashes) > 8192:
                self._coverage_hashes = dict(list(self._coverage_hashes.items())[-4096:])
        return ok

    def read(self, *, now, limit=100, cursor=None):
        now = _iso(now)
        result = {"schemaVersion": SCHEMA, "available": False, "observedAt": now, "lastSeenAt": None,
                  "heartbeat": {"status": "unknown", "lastSeenAt": None, "staleAfterSeconds": STALE_SECONDS, "ageSeconds": None},
                  "events": [], "incidents": {"active": [], "recovered": []}, "readiness": None,
                  "nextCursor": None, "hasMore": False, "limitations": list(LIMITATIONS), "archiveAvailable": False}
        if self.last_error:
            result["observerErrorCode"] = self.last_error
        if not self.path.is_file():
            result["reasonCode"] = "observability_not_recorded"
            return result
        connection = None
        try:
            limit = max(1, min(200, int(limit)))
            before, sequence = decode_cursor(cursor) if cursor else ("9999", 9_223_372_036_854_775_807)
            connection = self._connect(write=False)
            state = self._meta(connection)
            # Ingestion order is not chronology: a cold bootstrap can append
            # old coverage after this startup. The cursor binds both ordering
            # fields, including equal timestamps, without inventing event time.
            rows = connection.execute("""WITH timeline AS (
                SELECT seq,payload,COALESCE(json_extract(payload,'$.startedAt'),'') AS stamp FROM events)
                SELECT seq,payload,stamp FROM timeline
                WHERE stamp < ? OR (stamp = ? AND seq < ?)
                ORDER BY stamp DESC,seq DESC LIMIT ?""", (before, before, sequence, limit + 1)).fetchall()
            result["events"] = [json.loads(row[1]) for row in rows[:limit]]
            result["hasMore"] = len(rows) > limit
            result["nextCursor"] = _cursor(rows[limit - 1][2], rows[limit - 1][0]) if len(rows) > limit else None
            # Incidents are independently bounded; history remains pageable.
            incidents = connection.execute("SELECT payload FROM events WHERE json_extract(payload,'$.type')='incident' ORDER BY seq DESC LIMIT 100").fetchall()
            for row in incidents:
                event = json.loads(row[0])
                result["incidents"]["active" if event["status"] == "active" else "recovered"].append(event)
            previous = _time(state.get("lastSeenAt"))
            age = (_time(now) - previous).total_seconds() if previous and _time(now) else None
            result.update(available=True, archiveAvailable=True, lastSeenAt=state.get("lastSeenAt"))
            status = "stopped" if state.get("cleanStoppedAt") else "unknown" if age is None or age < 0 else "stale" if age > STALE_SECONDS else "observed"
            result["heartbeat"].update(status=status, ageSeconds=round(age, 3) if age is not None else None, lastSeenAt=state.get("lastSeenAt"))
            if status == "stale":
                result["unobservedInterval"] = {"startedAt": state.get("lastSeenAt"), "endedAt": None, "certainty": "unknown", "reasonCode": "observation_gap_unknown"}
        except (OSError, sqlite3.Error, ValueError, TypeError) as error:
            result.update(available=False, reasonCode="observability_read_" + type(error).__name__)
        finally:
            if connection is not None:
                connection.close()
        return result
