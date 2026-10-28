"""Read-only offline-upgrade checks. Never import HQ or repair runtime state."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import stat
import time


class UpgradeBlocked(Exception):
    pass


def _safe_path(path: Path) -> None:
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise UpgradeBlocked("unsafe_runtime_path")


def _unique(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise UpgradeBlocked("runtime_duplicate_json_key")
        result[key] = value
    return result


def _read(path: Path, *, limit: int = 128 * 1024 * 1024) -> object | None:
    _safe_path(path)
    try:
        before = path.stat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= limit:
        raise UpgradeBlocked("runtime_file_invalid")
    raw = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise UpgradeBlocked("runtime_changed_during_check")
    try:
        result = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_unique,
                            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if result is None:
            raise UpgradeBlocked("runtime_shape_invalid")
        return result
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise UpgradeBlocked("runtime_json_invalid") from exc


def _dict(value: object) -> dict:
    if not isinstance(value, dict):
        raise UpgradeBlocked("runtime_shape_invalid")
    return value


def _list(value: object) -> list:
    if not isinstance(value, list):
        raise UpgradeBlocked("runtime_shape_invalid")
    return value


def _count(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise UpgradeBlocked("position_state_invalid")
    return float(value)


def _channel(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"mtc-[A-Za-z0-9_-]+", value):
        raise UpgradeBlocked("target_identity_invalid")
    return value


def check_upgrade_state(install_root: Path, common_files: Path, *, now: float | None = None) -> None:
    """The caller must hold the existing Bridge OS lease for this entire check."""
    now = time.time() if now is None else now
    _safe_path(install_root)
    runtime = install_root / "data" / "runtime"
    channels = set()
    missions = _read(runtime / "missions.json")
    if missions is not None:
        rows = missions if isinstance(missions, list) else _dict(missions).get("missions")
        for row in _list(rows):
            row = _dict(row)
            if row.get("status") not in {"completed", "failed", "blocked", "archived", "cancelled", "canceled"}:
                raise UpgradeBlocked("active_mission")
    council = _read(runtime / "ai-trade-council-automation.json")
    if council is not None:
        council = _dict(council)
        if not isinstance(_dict(council.get("config")).get("enabled"), bool):
            raise UpgradeBlocked("council_state_invalid")
        state = _dict(council.get("state"))
        if state.get("candidateId") is not None:
            channels.add(_channel(state["candidateId"]))
        if _list(state.get("pendingQueue", [])) or any(state.get(key) is not None for key in (
            "pendingClosedBarTime", "pendingSnapshotId", "pendingDetectedAt",
        )) or state.get("status") in {"running", "queued", "analyzing"}:
            raise UpgradeBlocked("council_pending")
    agents = _read(runtime / "full-agent-runtime" / "full-agent-runtime-v1.json")
    if agents is not None:
        for thread in _dict(_dict(agents).get("threads")).values():
            thread = _dict(thread)
            if thread.get("activeTurnId") is not None:
                raise UpgradeBlocked("active_agent_turn")
            for turn in _list(thread.get("turns", [])):
                if _dict(turn).get("status") not in {"completed", "failed", "cancelled"}:
                    raise UpgradeBlocked("active_agent_turn")
    daily_news = _read(runtime / "sentiment-news-ai" / "state.json")
    if daily_news is not None and _dict(daily_news).get("status") in {"queued", "running"}:
        raise UpgradeBlocked("daily_news_analysis_active")
    ledger = _read(runtime / "mt4-trade-gateway" / "mt4-trade-gateway-ledger.json")
    if ledger is not None:
        ledger = _dict(ledger)
        if ledger.get("activeCommandId") is not None:
            raise UpgradeBlocked("outstanding_trade_command")
        for entry in _dict(ledger.get("commands")).values():
            entry = _dict(entry)
            if entry.get("outstanding") is not False or "unknown" in str(entry.get("status", "")).lower():
                raise UpgradeBlocked("unresolved_trade_command")
            if entry.get("command") is not None:
                channels.add(_channel(_dict(entry["command"]).get("channelId")))
    targets = _read(runtime / "metatrader-targets.json")
    if targets is not None:
        targets = _dict(targets)
        candidates = _dict(targets.get("candidates"))
        for key in ("selections", "platformSelections"):
            for selected in _dict(targets.get(key, {})).values():
                if selected is None:
                    continue
                channel = _dict(selected).get("candidateId")
                if channel is None:
                    continue
                if _channel(channel) not in candidates:
                    raise UpgradeBlocked("target_identity_invalid")
                channels.add(channel)
    for channel in channels:
        folder = common_files / "MetafxHQ" / channel
        status = _read(folder / "trade-gateway" / "status.json", limit=1024 * 1024)
        if status is not None:
            status = _dict(status)
            if status.get("channelId") != channel:
                raise UpgradeBlocked("ea_identity_invalid")
            if _count(status.get("currentManagedPositions", 0)) > 0:
                raise UpgradeBlocked("open_positions")
            observed = status.get("observedAt")
            if isinstance(observed, bool) or not isinstance(observed, (int, float)) or not math.isfinite(observed):
                raise UpgradeBlocked("ea_status_time_invalid")
            if observed > now + 30 or now - observed <= 60:
                raise UpgradeBlocked("ea_connection_active")
        snapshot = _read(folder / "snapshot.json", limit=1024 * 1024)
        if snapshot is not None:
            snapshot = _dict(snapshot)
            if snapshot.get("channelId") != channel:
                raise UpgradeBlocked("ea_identity_invalid")
            summary = _dict(snapshot.get("positionsSummary"))
            if _count(summary.get("count")) > 0:
                raise UpgradeBlocked("open_positions")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install-root", required=True)
    parser.add_argument("--common-files", required=True)
    args = parser.parse_args()
    try:
        check_upgrade_state(Path(args.install_root), Path(args.common_files))
    except UpgradeBlocked as exc:
        print(json.dumps({"ok": False, "code": str(exc)}))
        return 3
    except (OSError, ValueError, TypeError):
        print(json.dumps({"ok": False, "code": "runtime_state_unavailable"}))
        return 3
    print(json.dumps({"ok": True, "code": "offline_state_ready"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
