"""Local MT5 selection for market-data reads, independent of HQ's trading slots.

Discovery reads process image paths and bounded origin.txt files only. It never
loads MetaTrader5, attaches to a terminal, or reads account/configuration files.
Only opaque candidate ids and generic installation labels leave this module.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import secrets
import threading
import time

from .correlation import MAX_SNAPSHOT_BYTES, SERVICE_LOCK, iso, stamp


class MT5SetupError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _canonical(path):
    return os.path.normcase(str(Path(path).resolve()))


def _identity(terminal, data_path):
    return hashlib.sha256((_canonical(terminal) + "\0" + _canonical(data_path)).encode("utf-8")).hexdigest()


def _limited_json(path, limit):
    if path.stat().st_size > limit:
        raise ValueError("migration_input_too_large")
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("migration_input_invalid")
    return raw, value


def _replace_bytes(path, raw):
    """One private file at a time; no shared temporary filename."""
    temporary = path.with_name(path.name + ".migration-" + secrets.token_hex(8) + ".tmp")
    try:
        with temporary.open("wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _json_bytes(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False).encode("utf-8")


def _origin(data_path):
    try:
        source = data_path / "origin.txt"
        if source.stat().st_size > 4096:
            return None
        raw = source.read_bytes()
    except OSError:
        return None
    for encoding in ("utf-16", "utf-8-sig", "utf-8"):
        try:
            value = raw.decode(encoding).strip("\x00\r\n ")
        except UnicodeError:
            continue
        if value and "\x00" not in value:
            candidate = Path(value)
            if candidate.is_absolute():
                executable = candidate / "terminal64.exe"
                if executable.is_file():
                    return _canonical(executable)
    return None


def running_terminals():
    """Return private process bindings without command lines, titles or accounts."""
    if os.name != "nt":
        raise MT5SetupError("mt5_windows_required")
    kernel, psapi = ctypes.WinDLL("kernel32", use_last_error=True), ctypes.WinDLL("psapi", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    psapi.EnumProcesses.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    processes, size = (wintypes.DWORD * 8192)(), wintypes.DWORD()
    if not psapi.EnumProcesses(processes, ctypes.sizeof(processes), ctypes.byref(size)) or size.value >= ctypes.sizeof(processes):
        raise MT5SetupError("terminal_process_probe_unavailable")
    result = []
    for pid in processes[:size.value // ctypes.sizeof(wintypes.DWORD)]:
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            continue
        try:
            buf, length = ctypes.create_unicode_buffer(32768), wintypes.DWORD(32768)
            if kernel.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(length)):
                path = Path(buf.value)
                if path.name.lower() == "terminal64.exe" and path.is_file():
                    result.append({"terminalPath": _canonical(path), "pid": int(pid)})
        finally:
            kernel.CloseHandle(handle)
    return result


def discover_bindings(*, processes=None, data_root=None):
    """Private candidates; no native MT5 IPC, and no recursive filesystem scan."""
    processes = running_terminals() if processes is None else processes
    root = Path(data_root) if data_root else Path(os.environ.get("APPDATA", "")) / "MetaQuotes" / "Terminal"
    data_by_terminal = {}
    try:
        entries = sorted(root.iterdir(), key=lambda item: item.name)[:256]
    except OSError:
        entries = []
    for data in entries:
        if data.is_dir() and (data / "MQL5").is_dir():
            terminal = _origin(data)
            if terminal:
                data_by_terminal.setdefault(terminal, set()).add(_canonical(data))
    by_terminal = {}
    for process in processes[:8192]:
        terminal = _canonical(process["terminalPath"])
        if Path(terminal).name.lower() == "terminal64.exe":
            by_terminal.setdefault(terminal, set()).add(process["pid"])
    result = []
    for terminal, pids in sorted(by_terminal.items()):
        installation = Path(terminal).parent
        directories = set(data_by_terminal.get(terminal, set()))
        if (installation / "MQL5").is_dir():
            directories.add(_canonical(installation))
        if not directories:
            result.append({"terminalPath": terminal, "dataPath": None, "runningCount": len(pids), "reasonCode": "terminal_data_path_unavailable"})
        for data in sorted(directories):
            result.append({"terminalPath": terminal, "dataPath": data, "runningCount": len(pids),
                           "reasonCode": None if len(pids) == 1 else "selected_terminal_ambiguous"})
    return result


class MT5Setup:
    def __init__(self, state_dir, *, discoverer=None):
        self.path = Path(state_dir) / "mt5-candidates.json"
        self.discoverer = discoverer or discover_bindings
        self.lock = threading.RLock()

    def _read(self):
        try:
            if self.path.stat().st_size > 262144:
                return {}
            value = json.loads(self.path.read_text("utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, ValueError):
            return {}

    def _save(self, value):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=True), encoding="utf-8")
        os.replace(temporary, self.path)

    @staticmethod
    def _public(row):
        return {key: row.get(key) for key in ("candidateId", "label", "running", "selectable", "reasonCode")}

    def discover(self):
        with self.lock:
            previous = self._read()
            known = {row.get("identity"): row for row in previous.get("candidates", []) if isinstance(row, dict)}
            rows = []
            for index, binding in enumerate(self.discoverer()[:256], 1):
                terminal, data = binding["terminalPath"], binding.get("dataPath")
                identity = _identity(terminal, data or Path(terminal).parent)
                record = known.get(identity, {})
                selectable = bool(data and binding.get("runningCount") == 1 and not binding.get("reasonCode"))
                rows.append({"identity": identity, "candidateId": record.get("candidateId") or "mt5-" + secrets.token_hex(16),
                             "label": f"MT5 · {Path(terminal).parent.name[:64]} · โปรไฟล์ {index}",
                             "running": binding.get("runningCount", 0) > 0, "selectable": selectable,
                             "reasonCode": binding.get("reasonCode"), "terminalPath": terminal, "dataPath": data})
            value = {"schemaVersion": "sentiment-mt5-selection-v1", "discoveryRevision": secrets.token_urlsafe(24),
                     "checkedAt": iso(time.time()), "candidates": rows}
            self._save(value)
            return {**{key: value[key] for key in ("schemaVersion", "discoveryRevision", "checkedAt")},
                    "candidates": [self._public(row) for row in rows]}

    def resolve_selection(self, candidate_id, discovery_revision):
        """Return a private config fragment for the caller to merge and persist."""
        with self.lock:
            state = self._read()
            checked = stamp(state.get("checkedAt"))
            if (not isinstance(discovery_revision, str) or discovery_revision != state.get("discoveryRevision")
                    or checked is None or not 0 <= time.time() - checked <= 600):
                raise MT5SetupError("mt5_discovery_expired")
            row = next((item for item in state.get("candidates", []) if item.get("candidateId") == candidate_id), None)
            if not row or not row.get("selectable"):
                raise MT5SetupError("mt5_candidate_unavailable")
            current = [item for item in self.discoverer() if item.get("dataPath")
                       and _identity(item["terminalPath"], item["dataPath"]) == row["identity"]]
            if len(current) != 1 or current[0].get("runningCount") != 1 or current[0].get("reasonCode"):
                raise MT5SetupError("mt5_candidate_changed")
            fragment = {"enabled": True, "terminalPath": _canonical(row["terminalPath"]), "dataPath": _canonical(row["dataPath"]),
                        "selectionId": candidate_id, "selectedAt": iso(time.time())}
            # Runtime location is not terminal identity. Keep the installer-owned
            # interpreter when the server replaces only this config section.
            try:
                config_path = self.path.parent / "config.json"
                existing = json.loads(config_path.read_text("utf-8-sig")).get("mt5", {}) if config_path.stat().st_size < 262144 else {}
                python = existing.get("pythonPath")
                if isinstance(python, str) and Path(python).is_absolute() and Path(python).is_file():
                    fragment["pythonPath"] = python
            except (OSError, ValueError, AttributeError, TypeError):
                pass
            return fragment

    def migrate_legacy(self, full_config):
        """Return sanitized migration outcome; never expose filesystem errors."""
        try:
            return self._migrate_legacy(full_config)
        except Exception:
            return {"migrated": False, "reason": "legacy_migration_unavailable"}

    def _migrate_legacy(self, full_config):
        """Before workers start, detach a proven legacy cache from HQ selection.

        The argument is the complete, already-loaded service configuration. No
        MetaTrader5 module/IPC is used. Exact current discovery, the matching HQ
        candidate, and a valid own-cache binding must all agree. Config is saved
        last; an ordinary write failure restores already-written private files.
        Caller reloads config.json only when migrated is true. Never call this
        concurrently with HTTP selection or another service instance.
        """
        def outcome(reason, migrated=False):
            return {"migrated": migrated, "reason": reason}
        if not isinstance(full_config, dict) or not isinstance(full_config.get("mt5"), dict):
            return outcome("legacy_configuration_missing")
        old = full_config["mt5"]
        if old.get("selectionId"):
            return outcome("already_independent")
        if old.get("enabled") is not True or not old.get("candidateId") or not old.get("inputCachePath"):
            return outcome("legacy_configuration_missing")
        with self.lock, SERVICE_LOCK:
            state = self.path.parent.resolve()
            config_path = state / "config.json"
            cache_path = state / "mt5-h1-snapshot.json"
            metadata_path = state / "mt5-h1-collector-state.json"
            registry_path = state / self.path.name
            owned = (cache_path, metadata_path, registry_path, config_path)
            try:
                if any(path.resolve().parent != state for path in owned):
                    return outcome("private_state_path_invalid")
                original_config, persisted = _limited_json(config_path, 262144)
                if persisted != full_config:
                    return outcome("configuration_changed")
                terminal, data = old.get("terminalPath"), old.get("dataPath")
                if not isinstance(terminal, str) or not isinstance(data, str) or not Path(terminal).is_absolute() or not Path(data).is_absolute():
                    return outcome("legacy_binding_invalid")
                identity = _identity(terminal, data)
                bindings = [row for row in self.discoverer() if _canonical(row["terminalPath"]) == _canonical(terminal)]
                if (len(bindings) != 1 or not bindings[0].get("dataPath")
                        or _identity(bindings[0]["terminalPath"], bindings[0]["dataPath"]) != identity
                        or bindings[0].get("runningCount") != 1 or bindings[0].get("reasonCode")):
                    return outcome("legacy_terminal_not_uniquely_proven")
                _, upstream = _limited_json(Path(old["inputCachePath"]), MAX_SNAPSHOT_BYTES)
                if (upstream.get("source") or {}).get("terminalCandidateId") != old["candidateId"]:
                    return outcome("legacy_candidate_mismatch")
                original_cache, cache = _limited_json(cache_path, MAX_SNAPSHOT_BYTES)
                original_metadata, metadata = _limited_json(metadata_path, 262144)
                hashes = {hashlib.sha256(json.dumps({key: old.get(key) for key in names}, sort_keys=True).encode()).hexdigest()
                          for names in (("terminalPath", "dataPath", "candidateId", "symbolMap"),
                                        ("terminalPath", "dataPath", "selectionId", "candidateId", "symbolMap"))}
                if metadata.get("binding") not in hashes:
                    return outcome("legacy_cache_binding_mismatch")
                source = cache.get("source") or {}
                if (cache.get("schemaVersion") != "sentiment-mt5-h1-snapshot-v1"
                        or source.get("kind") != "mt5_guarded_closed_bars" or source.get("closedBarsOnly") is not True
                        or not isinstance(cache.get("pairs"), list) or stamp(cache.get("collectedAt")) is None):
                    return outcome("legacy_cache_invalid")
                from .mt5_reader import terminal_binding
                clock = source.get("clock") or {}
                upstream_clock = (upstream.get("source") or {}).get("clock") or {}
                now = time.time()
                def valid_clock(value):
                    offset, verified = value.get("offsetSeconds"), stamp(value.get("verifiedAt"))
                    return (value.get("basis") == "broker_server_normalized" and type(offset) is int
                            and abs(offset) <= 14*3600 and offset % 900 == 0 and verified is not None
                            and 0 <= now-verified <= 72*3600)
                if (not valid_clock(clock) or not valid_clock(upstream_clock)
                        or clock["offsetSeconds"] != upstream_clock["offsetSeconds"]
                        or clock.get("bindingId") not in (None, terminal_binding(old))):
                    return outcome("legacy_clock_not_proven")
                original_registry, registry = _limited_json(registry_path, 262144) if registry_path.exists() else (None, {})
                known = next((row for row in registry.get("candidates", []) if isinstance(row, dict) and row.get("identity") == identity), {})
                selection_id = known.get("candidateId") or "mt5-" + secrets.token_hex(16)
                updated = dict(old)
                for key in ("candidateId", "inputCachePath", "terminalPid", "clock"):
                    updated.pop(key, None)
                updated.update(terminalPath=_canonical(terminal), dataPath=_canonical(data), selectionId=selection_id, selectedAt=iso(now))
                next_config = {**full_config, "mt5": updated}
                # Preserve source bars, verifiedAt and collection timestamps.
                clock["bindingId"] = terminal_binding(updated)
                metadata["binding"] = hashlib.sha256(json.dumps({key: updated.get(key) for key in
                    ("terminalPath", "dataPath", "selectionId", "candidateId", "symbolMap")}, sort_keys=True).encode()).hexdigest()
                selected_row = {"identity": identity, "candidateId": selection_id,
                                "label": f"MT5 · {Path(terminal).parent.name[:64]} · โปรไฟล์ที่บันทึกไว้",
                                "running": True, "selectable": True, "reasonCode": None,
                                "terminalPath": updated["terminalPath"], "dataPath": updated["dataPath"]}
                registry = {"schemaVersion": "sentiment-mt5-selection-v1", "discoveryRevision": secrets.token_urlsafe(24),
                            "checkedAt": iso(now), "candidates": [selected_row]}
                originals = {cache_path: original_cache, metadata_path: original_metadata, config_path: original_config,
                             registry_path: original_registry}
                writes = ((cache_path, cache), (metadata_path, metadata), (registry_path, registry), (config_path, next_config))
            except Exception:
                return outcome("legacy_migration_evidence_unavailable")
            committed = []
            try:
                for path, value in writes:
                    if path == config_path and config_path.read_bytes() != original_config:
                        raise ValueError("configuration_changed")
                    _replace_bytes(path, _json_bytes(value))
                    committed.append(path)
            except Exception:
                restored = True
                for path in reversed(committed):
                    try:
                        if originals[path] is None:
                            path.unlink(missing_ok=True)
                        else:
                            _replace_bytes(path, originals[path])
                    except Exception:
                        restored = False
                return outcome("legacy_migration_write_failed" if restored else "legacy_migration_restore_failed")
            return outcome("independent_binding_migrated", True)

    def status(self, config, correlation_snapshot=None):
        snapshot = correlation_snapshot if isinstance(correlation_snapshot, dict) else {}
        configured = config.get("enabled") is True and bool(config.get("terminalPath") and config.get("dataPath"))
        rows = self._read().get("candidates", [])
        selected = next((self._public(row) for row in rows if row.get("candidateId") == config.get("selectionId")), None)
        if configured and selected is None:
            selected = {"candidateId": config.get("selectionId"), "label": "MT5 ที่บันทึกไว้", "running": None}
        return {"configured": configured, "selected": selected,
                "status": snapshot.get("status", "verifying" if configured else "needs_configuration"),
                "reasonCode": snapshot.get("refreshErrorCode") or snapshot.get("errorCode"),
                "clock": snapshot.get("clock"), "coverage": snapshot.get("coverage"),
                "lastSuccessAt": snapshot.get("lastSuccessAt"), "lastAttemptAt": snapshot.get("lastAttemptAt"),
                "nextAttemptAt": snapshot.get("nextAttemptAt"), "readOnlyMarketData": True}
