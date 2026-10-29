"""Pure, cached readiness presentation. Never authorizes or starts Council work."""
from __future__ import annotations

from datetime import datetime, timezone
import math
import re


def instant(value):
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, OverflowError):
            return None
    else:
        return None
    # A broker's wall clock must never silently become a UTC instant.
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def finite(value, minimum=0, maximum=10**12):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) and minimum <= value <= maximum else None


def code(value, fallback="unknown"):
    return value if isinstance(value, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.:-]{0,119}", value) else fallback


def build_preflight(*, now, enabled=None, terminal_locks_ready=None, snapshot=None,
                    quota_gate=None, runner=None, operator_mode=None, active_round=None,
                    next_bar_at=None, quota_max_age_seconds=75):
    """Use supplied cached facts only; this function performs no I/O or refresh."""
    current = instant(now)
    if current is None:
        raise ValueError("Readiness requires an explicit timezone-aware observation time")
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    gate = quota_gate if isinstance(quota_gate, dict) else {}
    runner = runner if isinstance(runner, dict) else {}
    quota = gate.get("quota") if isinstance(gate.get("quota"), dict) else {}
    checks = []

    def add(identifier, label, state, reason, message, observed=None, age=None):
        stamp = instant(observed)
        checks.append({"id": identifier, "label": label, "status": state,
                       "reasonCode": code(reason), "messageTh": message,
                       "observedAt": stamp.isoformat() if stamp else None,
                       "ageSeconds": round(age, 1) if finite(age) is not None else None})

    add("automation", "การเปิดสภา", "ready" if enabled is True else "paused" if enabled is False else "unknown",
        "automation_enabled" if enabled is True else "automation_disabled" if enabled is False else "automation_state_unknown",
        "เปิดสภาอยู่" if enabled is True else "ผู้ใช้พักการวิเคราะห์อัตโนมัติ" if enabled is False else "ยังยืนยันการเปิดสภาไม่ได้")
    add("terminal", "การเลือก MT4/MT5", "ready" if terminal_locks_ready is True else "blocked" if terminal_locks_ready is False else "unknown",
        "terminal_locks_ready" if terminal_locks_ready is True else "global_metatrader_locks_incomplete" if terminal_locks_ready is False else "terminal_lock_state_unknown",
        "ยืนยัน Terminal ที่เลือกแล้ว" if terminal_locks_ready is True else "ยังยืนยัน Terminal ที่ต้องใช้ไม่ครบ")

    observed = instant(snapshot.get("observedAt"))
    age = (current - observed).total_seconds() if observed else None
    max_age = finite(snapshot.get("maximumAgeSeconds"), 1)
    if snapshot.get("status") not in {"ready", "ok"} or snapshot.get("identityReady") is not True:
        add("snapshot", "ข้อมูล MT5", "blocked" if snapshot.get("status") else "unknown",
            snapshot.get("reasonCode", "snapshot_unavailable"), "ข้อมูลหรืออัตลักษณ์กราฟยังไม่พร้อม", observed, age)
    elif age is None or age < -5 or max_age is None:
        add("snapshot", "ข้อมูล MT5", "unknown", "snapshot_time_unverified", "ยังยืนยันอายุข้อมูลหรือเกณฑ์ความสดไม่ได้", observed)
    elif age > max_age:
        add("snapshot", "ข้อมูล MT5", "blocked", "snapshot_stale", "ข้อมูล MT5 เก่าเกินเกณฑ์ ต้องรอข้อมูลใหม่", observed, age)
    else:
        add("snapshot", "ข้อมูล MT5", "ready", "snapshot_ready", "ข้อมูลล่าสุดอยู่ภายในเกณฑ์ความสด", observed, max(0, age))

    runner_observed = instant(runner.get("observedAt"))
    runner_stamp_age = (current - runner_observed).total_seconds() if runner_observed else None
    runner_cache_age = finite(runner.get("cacheAgeSeconds"))
    runner_ages = [age for age in (runner_stamp_age, runner_cache_age) if age is not None]
    runner_age = max(runner_ages) if runner_ages else None
    runner_ttl = finite(runner.get("maximumAgeSeconds", 30), 1)
    runner_ready = runner.get("status") in {"ready", "ready_guarded"}
    if runner_age is None or runner_ttl is None or (runner_stamp_age is not None and runner_stamp_age < -5):
        runner_state, runner_reason = "unknown", "runner_time_unverified"
    elif runner_age > runner_ttl:
        runner_state, runner_reason = "unknown", "runner_status_stale"
    else:
        runner_state = "ready" if runner_ready else "blocked" if runner.get("status") else "unknown"
        runner_reason = "runner_ready" if runner_ready else "codex_runner_not_ready"
    runner_messages = {"runner_ready": "Runner พร้อมตามสถานะล่าสุด",
                       "runner_time_unverified": "ยังยืนยันเวลาที่ตรวจ Runner ไม่ได้",
                       "runner_status_stale": "สถานะ Runner เก่า ต้องตรวจยืนยันใหม่ตอนเริ่มรอบ"}
    add("runner", "Codex Runner", runner_state, runner_reason,
        runner_messages.get(runner_reason, "Runner ยังไม่พร้อมหรือยังไม่มีข้อมูล"), runner_observed, runner_age)

    quota_observed = instant(quota.get("checkedAt") or quota.get("observedAt") or quota.get("fetchedAt"))
    stamp_age = (current - quota_observed).total_seconds() if quota_observed else None
    cache_age = finite(quota.get("cacheAgeSeconds"))
    quota_age = max(x for x in (stamp_age, cache_age) if x is not None) if stamp_age is not None or cache_age is not None else None
    ttl = finite(quota_max_age_seconds, 1)
    reason = code(gate.get("reason"), "quota_unavailable")
    explanations = {
        "quota_limit_reached": "โควต้าถึงขีดจำกัดตามผลตรวจล่าสุด",
        "quota_below_reserve": "โควต้าต่ำกว่าเกณฑ์สำรอง",
        "quota_provider_hard_stop": "ผู้ให้บริการระงับการใช้งานตามผลตรวจล่าสุด",
        "quota_incomplete": "ข้อมูลโควต้ายังไม่ครบ",
        "quota_unavailable": "ยังอ่านข้อมูลโควต้าไม่ได้ ไม่ได้แปลว่าโควต้าหมด",
        "quota_stale": "ข้อมูลโควต้าเก่า ต้องตรวจยืนยันใหม่ตอนเริ่มรอบ",
    }
    if quota.get("stale") is True or (quota_age is not None and ttl is not None and quota_age > ttl):
        quota_state, reason = "unknown", "quota_stale"
    elif gate.get("allowed") is not True and reason in {"quota_unavailable", "quota_incomplete"}:
        quota_state = "unknown"
    elif quota_age is None or ttl is None or (stamp_age is not None and stamp_age < -5):
        quota_state, reason = "unknown", "quota_time_unverified"
    elif gate.get("allowed") is True:
        quota_state, reason = "ready", "quota_ready"
    else:
        quota_state = "unknown" if reason in {"quota_unavailable", "quota_incomplete", "quota_stale"} else "blocked"
    add("quota", "โควต้า Codex", quota_state, reason,
        "โควต้าผ่านการตรวจครั้งล่าสุด" if reason == "quota_ready" else explanations.get(reason, "ยังยืนยันความพร้อมของโควต้าไม่ได้"),
        quota_observed, quota_age)

    add("mode", "โหมดอนุญาต", "ready" if operator_mode == "auto_guarded" else "blocked" if operator_mode else "unknown",
        "guarded_mode_ready" if operator_mode == "auto_guarded" else "full_access_required",
        "โหมดทำงานอัตโนมัติพร้อม Guard" if operator_mode == "auto_guarded" else "โหมดปัจจุบันยังไม่อนุญาตเริ่มสภาอัตโนมัติ")
    add("round", "รอบก่อนหน้า", "waiting" if active_round is True else "ready" if active_round is False else "unknown",
        "council_round_already_active" if active_round is True else "no_active_round" if active_round is False else "round_state_unknown",
        "รอบก่อนหน้ายังทำงาน" if active_round is True else "ไม่มีรอบก่อนหน้าค้าง" if active_round is False else "ยังยืนยันรอบที่ทำงานไม่ได้")
    statuses = {x["status"] for x in checks}
    status = "paused" if enabled is False else "attention" if statuses & {"blocked", "waiting"} else "unknown" if "unknown" in statuses else "ready"
    next_bar = instant(next_bar_at)
    return {"schemaVersion": "council-preflight-v1", "advisory": True, "canAuthorizeAnalysis": False,
            "checkedAt": current.isoformat(), "status": status, "source": "cached_existing_runtime",
            "nextBarAt": next_bar.isoformat() if next_bar and next_bar > current else None,
            "checks": checks,
            "limitations": ["เป็นการตรวจล่วงหน้าจากสถานะที่มีอยู่ ต้องตรวจเงื่อนไขจริงอีกครั้งตอนแท่งใหม่",
                            "ไม่เรียก AI ไม่รีเฟรชผู้ให้บริการ และไม่อนุญาตส่งคำสั่งหรือวิเคราะห์ย้อนหลัง"]}
