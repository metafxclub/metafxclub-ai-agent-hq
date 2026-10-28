"""Bridge-owned daily admission. No second calendar collector or trading API.

All dispatches use the existing guarded Mission worker. A durable per-day
reservation is committed before launch; an ambiguous crash never replays it.
"""
from __future__ import annotations

import json
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from . import sentiment_news_ai as contract

THAI = timezone(timedelta(hours=7))
TIMEOUT_SECONDS = 240
RESERVE_SECONDS = TIMEOUT_SECONDS + 90
ACTIVE = {"queued", "running", "waiting_approval", "waiting_quota"}
DAY_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


def context(mission):
    value = mission.get("sentimentNewsContext") if isinstance(mission, dict) else None
    if not isinstance(value, dict):
        return None
    day = value.get("dayThai", "")
    if (value.get("kind") != contract.ACTION_ID or not DAY_RE.fullmatch(day)
            or not contract.DIGEST.fullmatch(str(value.get("inputDigest", "")))
            or value.get("readOnly") is not True
            or mission.get("owner") != "codex_mcp_operator"
            or mission.get("toolId") != "codex_cli_task"
            or mission.get("requester") != "backend"
            or mission.get("idempotencyKey") != f"sentiment-news:{day}"):
        return None
    return value


class DailyNews:
    def __init__(self, host):
        self.host = host
        self.lock = threading.RLock()
        self.next_poll = 0.0

    @property
    def root(self):
        return self.host.MISSIONS_PATH.parent / "sentiment-news-ai"

    def read(self, path, default=None, limit=3 * 1024 * 1024):
        if not path.exists():
            return default
        if path.stat().st_size > limit:
            raise ValueError("news_ai_file_too_large")
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(value, dict):
            raise ValueError("news_ai_store_invalid")
        return value

    def ledger(self, day):
        return self.read(self.root / "days" / f"{day}.json", {})

    def save(self, state):
        state = {**state, "schemaVersion": 1, "updatedAt": self.host.utc_now()}
        self.host.write_json(self.root / "days" / f"{state['dayThai']}.json", state)
        self.host.write_json(self.root / "state.json", state)
        return state

    def news(self):
        mirror = self.host.PROJECT_ROOT / "frontend/public/sentiment-universe/market.json"
        value = self.read(mirror, {})
        stamp = self.host.parse_iso((value.get("mirror") or {}).get("publishedAt") or value.get("generatedAt"))
        if stamp is None or not -30 <= (datetime.now(timezone.utc) - stamp).total_seconds() <= 180:
            raise ValueError("calendar_stale")
        return value.get("news") or {}

    def council_gate(self, now=None):
        now = now or datetime.now(timezone.utc)
        host = self.host
        rows = host.load_missions(shared_snapshot=True)
        if any((r.get("analysisContext") or {}).get("kind") in
               {"ai_trade_council_parent", "ai_trade_council_vote"}
               and r.get("status") in ACTIVE for r in rows):
            return "council_busy"
        store = host.load_ai_trade_council_automation_store()
        if (store.get("config") or {}).get("enabled") is not True:
            return None
        state = store.get("state") or {}
        if state.get("pendingQueue") or state.get("pendingSnapshotId"):
            return "council_busy"
        seconds = {"M5": 300, "M15": 900, "M30": 1800, "H1": 3600,
                   "H4": 14400, "D1": 86400, "W1": 604800, "MN1": 86400}.get(state.get("timeframe"))
        if seconds is None:
            return "council_window"
        # Conservative UTC aligned boundary plus start buffer; runtime activity
        # is also checked continuously, including broker-offset daily bars.
        elapsed = now.timestamp() % seconds
        if elapsed < 30 or seconds - elapsed <= 105:
            return "council_window"
        return None

    def timeout(self):
        store = self.host.load_ai_trade_council_automation_store()
        if (store.get("config") or {}).get("enabled") is not True:
            return TIMEOUT_SECONDS
        seconds = {"M5": 300, "M15": 900, "M30": 1800, "H1": 3600,
                   "H4": 14400, "D1": 86400, "W1": 604800, "MN1": 86400}.get((store.get("state") or {}).get("timeframe"), 300)
        remaining = seconds - datetime.now(timezone.utc).timestamp() % seconds
        return max(30, min(TIMEOUT_SECONDS, int(remaining) - 45))

    def tick(self):
        if time.monotonic() < self.next_poll:
            return
        self.next_poll = time.monotonic() + 30
        with self.lock:
            now = datetime.now(THAI)
            day = now.date().isoformat()
            state = self.ledger(day)
            if state.get("attempted"):
                mission = self.host.find_mission(state.get("missionId")) or {}
                if state.get("status") == "running" and mission.get("status") != "running":
                    self.save({**state, "status": "interrupted", "reason": "interrupted_unknown"})
                return
            existing = self.host.find_mission_by_idempotency(f"sentiment-news:{day}")
            if existing:
                if existing.get("status") not in ACTIVE:
                    self.save({**state, "dayThai": day, "missionId": existing["id"],
                               "attempted": True, "status": "failed", "reason": "already_attempted"})
                return
            def blocked(reason):
                self.save({"dayThai": day, "status": "blocked", "reason": reason, "attempted": False})
            if now.hour == 0 and now.minute < 10:
                return blocked("waiting_calendar")
            if self.host.load_operator_mode_record().get("mode") != "auto_guarded":
                return blocked("operator_manual")
            gate = self.council_gate()
            if gate:
                return blocked(gate)
            try:
                news = self.news()
                if news.get("status") not in {"ready", "empty"} or news.get("dayThai") != day:
                    return blocked("waiting_calendar")
                if not news.get("events"):
                    self.save({"dayThai": day, "status": "empty", "reason": "empty_day", "attempted": False})
                    return
                assignment = contract.build_assignment(news, day)
            except (ValueError, OSError, TypeError):
                return blocked("calendar_stale")
            quota = self.host._collaboration_quota_gate({}, refresh=False, quota=self.host.codex_rate_limits())
            if quota.get("allowed") is not True or quota.get("billingSource") == "existing_credits":
                return blocked("quota_unavailable" if quota.get("remainingPercent") is None else "quota_below_reserve")
            self.host.write_json(self.root / f"assignment-{day}.json", assignment)
            marker = {"kind": contract.ACTION_ID, "dayThai": day,
                      "inputDigest": assignment["inputDigest"], "readOnly": True}
            mission = self.host.create_mission({
                "title": f"Sentiment Universe ข่าวประจำวัน {day}",
                "prompt": f"Explain the supplied public economic calendar for {day} in Thai. Read-only educational scenarios.",
                "agentId": "codex_mcp_operator", "requester": "backend",
                "toolId": "codex_cli_task", "targetId": "left_signal_cube",
                "reportType": "sentiment_news_daily_report", "risk": "low",
                "modelTier": "specialist_fast", "idempotencyKey": f"sentiment-news:{day}",
                "budget": {"timeoutSeconds": TIMEOUT_SECONDS, "maxRuns": 1}},
                allow_model_override=True, allow_budget_override=True,
                _trusted_sentiment_news=marker)
            self.save({"dayThai": day, "status": "queued", "reason": "waiting_dispatch",
                       "missionId": mission["id"], "inputDigest": assignment["inputDigest"], "attempted": False})
            self.host.append_audit({"type": "sentiment_news.daily_queued", "missionId": mission["id"],
                                    "dayThai": day, "eventCount": len(assignment["events"]), "readOnly": True})

    def assignment(self, mission):
        marker = context(mission)
        if not marker or marker["dayThai"] != datetime.now(THAI).date().isoformat():
            raise ValueError("day_expired")
        value = contract.validate_assignment(self.read(self.root / f"assignment-{marker['dayThai']}.json"), marker["dayThai"])
        if value["inputDigest"] != marker["inputDigest"]:
            raise ValueError("calendar_changed")
        return value

    def preflight(self, mission):
        try:
            assignment = self.assignment(mission)
            state = self.ledger(assignment["dayThai"])
            if state.get("attempted"):
                return "already_attempted"
            if contract.build_assignment(self.news(), assignment["dayThai"])["inputDigest"] != assignment["inputDigest"]:
                return "calendar_changed"
            return self.council_gate()
        except (ValueError, OSError, TypeError):
            return "day_expired" if (context(mission) or {}).get("dayThai") != datetime.now(THAI).date().isoformat() else "calendar_changed"

    def begin(self, mission):
        with self.lock:
            reason = self.preflight(mission)
            if reason:
                raise ValueError(reason)
            marker = context(mission)
            self.save({"dayThai": marker["dayThai"], "inputDigest": marker["inputDigest"],
                       "missionId": mission["id"], "status": "running", "reason": "dispatch_reserved",
                       "attempted": True, "reservedAt": self.host.utc_now()})

    def complete(self, mission, runner, result, final):
        marker = context(mission)
        if not marker:
            return
        with self.lock:
            state = self.ledger(marker["dayThai"])
            if (not state.get("attempted") or final is None
                    or state.get("missionId") != mission.get("id")
                    or state.get("inputDigest") != marker["inputDigest"]):
                return
            ready = (final or {}).get("status") == "completed" and runner.get("ok") is True and runner.get("processStarted") is True and result.get("ok") is True
            if ready:
                assignment = self.assignment(mission)
                validated = contract.validate_result(result.get("newsAnalysis"), assignment)
                self.host.write_json(self.root / "result.json", {
                    "schemaVersion": 1, "dayThai": marker["dayThai"], "inputDigest": marker["inputDigest"],
                    "missionId": mission["id"], "generatedAt": self.host.utc_now(),
                    "assignment": assignment, "result": validated})
            self.save({**state, "status": "ready" if ready else "failed",
                       "reason": "completed" if ready else "runner_failed",
                       "processStarted": bool(runner.get("processStarted"))})

    def run(self, mission, command, **kwargs):
        self.begin(mission)
        # Recalculate the bounded window at the process boundary. The existing
        # lease may be longer, but this process cannot outlive this shorter cap.
        command = list(command)
        timeout = self.timeout()
        command[command.index("--timeout") + 1] = str(timeout)
        kwargs["timeout"] = timeout + 30
        cancel = threading.Event()
        done = threading.Event()
        def monitor():
            while not done.wait(1):
                try:
                    stop = self.host.MISSION_WORKER_STOP.is_set() or self.council_gate() == "council_busy"
                except Exception:
                    stop = True
                if stop:
                    cancel.set()
                    return
        thread = threading.Thread(target=monitor, name="sentiment-news-council-priority", daemon=True)
        thread.start()
        try:
            kwargs["cancel_event"] = cancel
            return self.host.run_safe_command(command, **kwargs)
        finally:
            done.set()
            thread.join(timeout=2)
