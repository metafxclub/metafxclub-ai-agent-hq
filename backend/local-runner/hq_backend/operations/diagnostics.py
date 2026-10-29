"""Allowlisted support export. Pure data projection, never a runtime file bundle."""
from __future__ import annotations

import hashlib
import re

from .preflight import finite, instant


_STATUSES = frozenset("ready ready_guarded degraded unavailable not_checked unknown idle waiting running queued pending paused disabled blocked skipped analyzed complete completed partial failed error cancelled canceled timeout timed_out deadline_exceeded active recovered resolved open closed stale stopped stopping starting confirmed not_started complete_all attention none recorded observed superseded missing".split())
_REASONS = frozenset("""
unknown ready quota_ready quota_unavailable quota_stale quota_incomplete quota_below_reserve
quota_limit_reached quota_provider_hard_stop quota_time_unverified quota_blocked
codex_runner_not_ready codex_runner_unavailable runner_ready runner_status_stale runner_time_unverified full_access_required
automation_enabled automation_disabled automation_state_unknown terminal_locks_ready
global_metatrader_locks_incomplete terminal_lock_state_unknown snapshot_unavailable
snapshot_time_unverified snapshot_stale snapshot_ready snapshot_identity_invalid
analysis_snapshot_ready_before_start analysis_snapshot_expired_before_start
analysis_snapshot_time_invalid_before_start execution_age_limit_unavailable_before_start
guarded_mode_ready council_round_already_active no_active_round round_state_unknown
new_bar_only_wait_next_bar new_bar_only_restart_baseline new_bar_only_stream_change_baseline
new_bar_only_missed_trigger new_bar_only_trigger_window_expired new_bar_only_trigger_not_admitted
new_bar_only_backlog_cancelled restart_baseline stream_change_baseline first_observation_baseline
bar_time_regression_baseline snapshot_not_captured_during_gap snapshot_artifact_capture_failed
durable_snapshot_unavailable daily_cap_reached daily_round_limit_reached daily_limit_reached
mission_running gap_history_unavailable council_round_terminal council_round_partial
council_round_failed council_round_completed council_round_skipped council_round_started
heartbeat_gap heartbeat_stale heartbeat_missing monitoring_gap monitoring_started monitoring_resumed
bridge_started bridge_stopped bridge_shutdown bridge_graceful_shutdown_requested
bridge_restart bridge_restart_unknown bridge_shutdown_confirmed bridge_unobserved_interval
bridge_clean_shutdown bridge_stopped_interval observation_gap_unknown archive_history_unavailable
observation_gap lifecycle_started lifecycle_stopped lifecycle_gap unknown_gap
observer_unavailable observer_store_unavailable observer_write_failed observer_read_failed
data_integrity_error invalid_vote response_invalid timeout cancelled completed
""".split())
_SYMBOLS = frozenset("EURUSD EURGBP EURJPY EURCHF EURAUD EURCAD EURNZD GBPUSD GBPJPY GBPCHF GBPAUD GBPCAD GBPNZD AUDUSD AUDJPY AUDCHF AUDCAD AUDNZD NZDUSD NZDJPY NZDCHF NZDCAD USDJPY USDCHF USDCAD CADJPY CADCHF CHFJPY XAUUSD XAGUSD WTI BRENT".split())
_TIMEFRAMES = frozenset("M1 M2 M3 M4 M5 M6 M10 M12 M15 M20 M30 H1 H2 H3 H4 H6 H8 H12 D1 W1 MN1".split())
_EVENT_TYPES = frozenset("heartbeat lifecycle incident coverage round bar gap observation recovery readiness startup shutdown paused availability".split())
_SOURCES = frozenset("council_tick coverage mission lifecycle bridge_startup bridge_shutdown observer heartbeat cached_existing_runtime first_observation bridge_shutdown_receipt heartbeat_gap snapshot_history_bounds observed_bar_coverage".split())


def _enum(value, allowed, fallback="unknown"):
    return value if isinstance(value, str) and value in allowed else fallback


def _time(value):
    parsed = instant(value)
    return parsed.isoformat() if parsed else None


def _bool(value):
    return value if isinstance(value, bool) else None


def _number(value, maximum=10**9):
    return finite(value, 0, maximum)


def _reason(value):
    # Unknown provider text may contain tokens, paths or account identifiers.
    # Export a digest for correlation, never the unrecognized string itself.
    reason = _enum(value, _REASONS)
    return {"reasonCode": reason, "unrecognizedReasonDigest":
            hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
            if reason == "unknown" and isinstance(value, str) and value else None}


def _reference(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16] if isinstance(value, str) and value else None


def _roles(raw):
    if isinstance(raw, dict):
        raw = [{"roleId": key, **value} for key, value in raw.items() if isinstance(value, dict)]
    if not isinstance(raw, list):
        return []
    result = []
    for role in raw[:3]:
        if not isinstance(role, dict):
            continue
        result.append({"roleId": _enum(role.get("roleId"), {"technical", "price_action", "news"}),
                       "status": _enum(role.get("status"), _STATUSES),
                       "processStarted": _bool(role.get("processStarted")),
                       "validVote": _bool(role.get("validVote")),
                       "sameSnapshot": _bool(role.get("sameSnapshot"))})
    return result


def _event(raw):
    value = raw if isinstance(raw, dict) else {}
    evidence = value.get("evidence") if isinstance(value.get("evidence"), dict) else {}
    return {"reference": _reference(value.get("id")), "type": _enum(value.get("type"), _EVENT_TYPES),
            "status": _enum(value.get("status"), _STATUSES),
            "severity": _enum(value.get("severity"), {"info", "warning", "error", "critical", "success"}),
            "certainty": _enum(value.get("certainty"), {"confirmed", "observed", "unknown", "inferred"}),
            **_reason(value.get("reasonCode")),
            **{key: _time(value.get(key)) for key in ("startedAt", "endedAt", "lastSeenAt")},
            "occurrences": _number(value.get("occurrences")),
            "symbol": _enum(value.get("symbol"), _SYMBOLS, None),
            "timeframe": _enum(value.get("timeframe"), _TIMEFRAMES, None),
            "attemptStatus": _enum(value.get("attemptStatus"), _STATUSES),
            "roles": _roles(value.get("roles")),
            "evidence": {"source": _enum(evidence.get("source"), _SOURCES),
                         "processStarted": _bool(evidence.get("processStarted")),
                         "completeRoleCount": _number(evidence.get("completeRoleCount"), 3),
                         "snapshotDigestMatched": _bool(evidence.get("snapshotDigestMatched")),
                         "processesStarted": _number(evidence.get("processesStarted"), 3),
                         "completedVotes": _number(evidence.get("completedVotes"), 3),
                         "requiredVotes": _number(evidence.get("requiredVotes"), 3),
                         "sameSnapshot": _bool(evidence.get("sameSnapshot")),
                         "aiRunAllowed": _bool(evidence.get("aiRunAllowed")),
                         "terminalActions": _bool(evidence.get("terminalActions"))}}


def _readiness(raw):
    value = raw if isinstance(raw, dict) else {}
    checks = value.get("checks") if isinstance(value.get("checks"), list) else []
    return {"advisory": True, "canAuthorizeAnalysis": False,
            "status": _enum(value.get("status"), _STATUSES),
            "checkedAt": _time(value.get("checkedAt")), "nextBarAt": _time(value.get("nextBarAt")),
            "checks": [{"id": _enum(c.get("id"), {"automation", "terminal", "snapshot", "runner", "quota", "mode", "round"}),
                        "status": _enum(c.get("status"), _STATUSES), **_reason(c.get("reasonCode")),
                        "observedAt": _time(c.get("observedAt")), "ageSeconds": _number(c.get("ageSeconds"))}
                       for c in checks[:20] if isinstance(c, dict)]}


def _round(raw):
    value = raw if isinstance(raw, dict) else {}
    roles = value.get("roles", value.get("votes", {}))
    if isinstance(roles, list):
        roles = {r.get("roleId", r.get("role")): r for r in roles if isinstance(r, dict)}
    if not isinstance(roles, dict):
        roles = {}
    result = {"reference": _reference(value.get("id", value.get("missionId"))),
              "status": _enum(value.get("status"), _STATUSES),
              "classification": _enum(value.get("classification"), _STATUSES),
              "symbol": _enum(value.get("symbol"), _SYMBOLS, None),
              "timeframe": _enum(value.get("timeframe"), _TIMEFRAMES, None),
              "finalDecision": _enum(value.get("finalDecision"), {"BUY", "SELL", "HOLD", "NO_TRADE", "NO_DATA"}, "NO_DATA"),
              "terminalActions": _bool(value.get("terminalActions")),
              "completeRoleCount": _number(value.get("completeRoleCount"), 3),
              **{k: _time(value.get(k)) for k in ("startedAt", "completedAt")},
              **_reason(value.get("reasonCode")), "roles": {}}
    for name in ("technical", "price_action", "news"):
        role = roles.get(name)
        if not isinstance(role, dict):
            continue
        result["roles"][name] = {"status": _enum(role.get("status"), _STATUSES),
                                 "processStarted": _bool(role.get("processStarted")),
                                 "validVote": _bool(role.get("validVote")),
                                 "decision": _enum(role.get("decision"), {"BUY", "SELL", "HOLD", "NO_DATA"}, "NO_DATA"),
                                 "confidence": _number(role.get("confidence"), 100),
                                 **{k: _time(role.get(k)) for k in ("startedAt", "completedAt")}}
    return result


def build_diagnostics(*, now, version, health, operations, council=None, rounds=None):
    """Export only bounded operational facts, never raw logs/state/configuration."""
    current = instant(now)
    if current is None:
        raise ValueError("Diagnostics require an explicit timezone-aware timestamp")
    health = health if isinstance(health, dict) else {}
    ops = operations if isinstance(operations, dict) else {}
    council = council if isinstance(council, dict) else {}
    cfg = council.get("config") if isinstance(council.get("config"), dict) else council
    state = council.get("state") if isinstance(council.get("state"), dict) else council
    incidents = ops.get("incidents") if isinstance(ops.get("incidents"), dict) else {}
    events = ops.get("events") if isinstance(ops.get("events"), list) else []
    rounds = rounds if isinstance(rounds, list) else []
    result = {"schemaVersion": "council-diagnostics-v1", "redacted": True,
              "generatedAt": current.isoformat(), "timezone": "Asia/Bangkok",
              "version": version if isinstance(version, str) and re.fullmatch(r"\d{1,4}\.\d{1,4}\.\d{1,4}", version) else "unknown",
              "readOnly": True, "canAuthorizeAnalysis": False,
              "health": {"ok": _bool(health.get("ok")), "status": _enum(health.get("status"), _STATUSES),
                         "startedAt": _time(health.get("startedAt")), "agentRosterComplete": _bool(health.get("agentRosterComplete"))},
              "council": {"enabled": _bool(cfg.get("enabled")), "status": _enum(state.get("status"), _STATUSES),
                          "symbol": _enum(state.get("symbol"), _SYMBOLS, None),
                          "timeframe": _enum(state.get("timeframe"), _TIMEFRAMES, None), **_reason(state.get("reason"))},
              "operations": {"available": _bool(ops.get("available")),
                             "observedAt": _time(ops.get("observedAt")), "lastSeenAt": _time(ops.get("lastSeenAt")),
                             "events": [_event(e) for e in events[:200]],
                             "hasMore": bool(ops.get("hasMore") or len(events) > 200),
                             "incidents": {key: [_event(e) for e in (incidents.get(key) or [])[:100]]
                                           if isinstance(incidents.get(key), list) else [] for key in ("active", "recovered")},
                             "readiness": _readiness(ops.get("readiness"))},
              "rounds": [_round(r) for r in rounds[:50]],
              "limitations": ["เป็นข้อมูลสรุป ณ เวลาส่งออก ไม่ใช่ผลทดสอบส่งออเดอร์จริง",
                              "ไม่รวมบัญชี รหัสผ่าน Token เส้นทางเครื่อง Prompt หรือข้อความ log ดิบ",
                              "รหัสเหตุที่ไม่รู้จักถูกแทนด้วย unknown และ digest เพื่อป้องกันข้อมูลส่วนตัวหลุด"]}
    # Do not expand a source-level report into an unbounded browser download.
    return result
