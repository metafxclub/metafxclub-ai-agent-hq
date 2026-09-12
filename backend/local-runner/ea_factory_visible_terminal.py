from __future__ import annotations

"""Fail-closed visible MetaEditor and MT4 Strategy Tester adapter.

The bridge owns terminal selection and injects a ``target_resolver``.  This
module never accepts an install/data path from a browser request, never sends a
trade, never attaches an EA to a chart, never changes AutoTrading, and never
closes a terminal.  PowerShell is used only for visible Windows UI Automation;
all path, digest, idempotency and evidence checks stay in this Python boundary.
"""

import copy
import hashlib
import html as html_lib
import json
import os
import re
import secrets
import stat
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Mapping


REQUEST_SCHEMA = "ea-factory-visible-front-office-request-v1"
PROCESS_BINDING_SCHEMA = "ea-factory-front-office-process-binding-v1"
RECEIPT_SCHEMA = "ea-factory-visible-front-office-receipt-v1"
ACTION_INTENT_SCHEMA = "ea-factory-visible-front-office-action-intent-v1"
BACKTEST_ACTION_REQUEST_SCHEMA = "ea-factory-visible-backtest-action-request-v1"
START_BOUNDARY_SCHEMA = "ea-factory-tester-start-boundary-v1"
RESOLVED_TESTER_SCHEMA = "ea-factory-resolved-tester-settings-v1"
TESTER_SETTINGS_SCHEMA = "ea-factory-tester-settings-v1"
TESTER_INPUT_PRESET_SCHEMA = "ea-factory-tester-input-preset-v1"
RESOLVED_TESTER_INPUT_PRESET_SCHEMA = (
    "ea-factory-resolved-tester-input-preset-v1"
)
EVIDENCE_MODE = "visible_front_office_v1"
POWERSHELL_RESULT_SCHEMA = "ea-factory-visible-powershell-result-v1"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_BINARY_BYTES = 64 * 1024 * 1024
MAX_EVIDENCE_BYTES = 32 * 1024 * 1024
MAX_SET_BYTES = 1024 * 1024
DEFAULT_UI_TIMEOUT_SECONDS = 120
DEFAULT_BACKTEST_TIMEOUT_SECONDS = 2 * 60 * 60
POWERSHELL_COMPLETION_MARGIN_SECONDS = 90
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
SAFE_OPERATION_ID = re.compile(r"ea-visible-[a-f0-9]{24}\Z")
SAFE_SYMBOL = re.compile(r"[A-Za-z0-9._#-]{1,40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
CAN_SLIM_CERTIFIED_INPUT_LAYOUT = (
    ("InpStopLossPercent", "double"),
    ("RewardRiskRatio", "double"),
    ("RiskPercent", "double"),
    ("ExecutionBufferPoints", "int"),
    ("SlippagePoints", "int"),
    ("MaxOpenPositionsPerSymbolMagic", "int"),
    ("MagicNumber", "int"),
    ("DailyMAPeriod", "int"),
    ("WeeklyMAPeriod", "int"),
    ("FiftyTwoWeekLookback", "int"),
    ("FundamentalCriteriaConfirmed", "bool"),
    ("ExternalBenchmarkUptrendConfirmed", "bool"),
    ("MaxSpreadPoints", "int"),
)
CAN_SLIM_SIMULATION_INPUT_NAMES = (
    "FundamentalCriteriaConfirmed",
    "ExternalBenchmarkUptrendConfirmed",
)
CAN_SLIM_FIXED_SOURCE_DEFAULTS = {
    "ExecutionBufferPoints": 2,
    "SlippagePoints": 3,
    "MagicNumber": 4186001,
    "DailyMAPeriod": 50,
    "WeeklyMAPeriod": 50,
    "FiftyTwoWeekLookback": 52,
    "FundamentalCriteriaConfirmed": False,
    "ExternalBenchmarkUptrendConfirmed": False,
    "MaxSpreadPoints": 30,
}
MT4_TESTER_INPUT_TYPES = frozenset({"bool", "int", "double"})
MT4_TESTER_INPUT_MAX_COUNT = 64
MT4_TESTER_SIMULATION_NAME_PATTERN = re.compile(
    r"(?:Fundamental|External|Eligibility|Screen|Criteria)",
    re.IGNORECASE,
)
MT4_TESTER_SIMULATION_FORBIDDEN_NAME_PATTERN = re.compile(
    r"(?:EnableTrading|TradingEnabled|AllowTrading|LiveTrading|AutoTrading|Safety)",
    re.IGNORECASE,
)
ALLOWED_PERIODS = frozenset(
    {
        "M1",
        "M5",
        "M15",
        "M30",
        "H1",
        "H4",
        "D1",
        "W1",
        "MN1",
    }
)
ALLOWED_MODELS = frozenset({"every_tick", "control_points", "open_prices"})
ARTIFACT_KINDS = {
    "compiled_binary": "compile_evidence",
    "visible_window": "screenshot_evidence",
    "compile_log": "compile_evidence",
    "tester_settings": "screenshot_evidence",
    "tester_input_preset": "screenshot_evidence",
    "tester_input_preset_set": "set_file",
    "tester_input_readback_set": "set_file",
    "tester_result": "screenshot_evidence",
    "tester_report_proof": "screenshot_evidence",
    "tester_report": "backtest_evidence",
    # Bridge registers the receipt under the stage evidence class.
    "adapter_receipt": "compile_evidence",
}


class VisibleTerminalAdapterError(RuntimeError):
    """One public, path-free adapter failure code."""

    def __init__(self, code: str, *, retryable: bool = False) -> None:
        super().__init__(code)
        self.code = str(code)
        self.retryable = bool(retryable)

    def public_details(self) -> dict:
        return {"reasonCode": self.code, "retryable": self.retryable}


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_text(value: object) -> str:
    return _sha256_bytes(str(value or "").encode("utf-8", errors="replace"))


def _path_has_reparse_component(path: Path) -> bool:
    try:
        absolute = path.absolute()
    except (OSError, RuntimeError, ValueError):
        return True
    for candidate in (absolute, *absolute.parents):
        if candidate.parent == candidate:
            continue
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            continue
        except (OSError, RuntimeError, ValueError):
            return True
        if stat.S_ISLNK(metadata.st_mode):
            return True
        if int(getattr(metadata, "st_file_attributes", 0) or 0) & 0x400:
            return True
    return False


def _resolved_directory(path: object, code: str) -> Path:
    candidate = Path(str(path or ""))
    try:
        if (
            not candidate.is_absolute()
            or _path_has_reparse_component(candidate)
            or not candidate.is_dir()
        ):
            raise VisibleTerminalAdapterError(code)
        return candidate.resolve(strict=True)
    except VisibleTerminalAdapterError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError(code) from error


def _resolved_file(path: object, code: str, *, maximum_bytes: int) -> Path:
    candidate = Path(str(path or ""))
    try:
        if (
            not candidate.is_absolute()
            or _path_has_reparse_component(candidate)
            or not candidate.is_file()
        ):
            raise VisibleTerminalAdapterError(code)
        resolved = candidate.resolve(strict=True)
        size = resolved.stat(follow_symlinks=False).st_size
        if size <= 0 or size > maximum_bytes:
            raise VisibleTerminalAdapterError(code)
        return resolved
    except VisibleTerminalAdapterError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError(code) from error


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _managed_path(root: Path, relative: object, code: str) -> Path:
    raw = str(relative or "").replace("\\", "/")
    if (
        not raw
        or len(raw) > 260
        or raw.startswith("/")
        or ":" in raw
        or any(part in {"", ".", ".."} for part in raw.split("/"))
    ):
        raise VisibleTerminalAdapterError(code)
    candidate = root.joinpath(*raw.split("/"))
    try:
        parent = candidate.parent.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError(code) from error
    if _path_has_reparse_component(parent) or not _is_relative_to(parent, root):
        raise VisibleTerminalAdapterError(code)
    return parent / candidate.name


def _stable_digest(path: Path, *, maximum_bytes: int) -> tuple[str, int]:
    try:
        if _path_has_reparse_component(path) or not path.is_file():
            raise VisibleTerminalAdapterError("evidence_file_unavailable")
        before = path.stat(follow_symlinks=False)
        if before.st_size <= 0 or before.st_size > maximum_bytes:
            raise VisibleTerminalAdapterError("evidence_file_size_invalid")
        digest = hashlib.sha256()
        observed = 0
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(64 * 1024), b""):
                observed += len(block)
                if observed > maximum_bytes:
                    raise VisibleTerminalAdapterError("evidence_file_size_invalid")
                digest.update(block)
        after = path.stat(follow_symlinks=False)
    except VisibleTerminalAdapterError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError("evidence_file_unavailable") from error
    if (
        observed != before.st_size
        or after.st_size != before.st_size
        or after.st_mtime_ns != before.st_mtime_ns
        or getattr(after, "st_ino", None) != getattr(before, "st_ino", None)
    ):
        raise VisibleTerminalAdapterError("evidence_file_changed_during_read")
    return digest.hexdigest(), observed


def _write_exclusive(path: Path, payload: bytes, code: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as error:
        raise VisibleTerminalAdapterError(code) from error
    except (OSError, ValueError) as error:
        raise VisibleTerminalAdapterError(code) from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _copy_exclusive_or_verify(source: Path, destination: Path) -> tuple[str, int, bool]:
    source_digest, source_size = _stable_digest(source, maximum_bytes=MAX_BINARY_BYTES)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if _path_has_reparse_component(destination.parent):
        raise VisibleTerminalAdapterError("expert_deployment_path_unsafe")
    if destination.exists():
        destination_digest, destination_size = _stable_digest(
            destination,
            maximum_bytes=MAX_BINARY_BYTES,
        )
        if (
            destination_size != source_size
            or not secrets.compare_digest(destination_digest, source_digest)
        ):
            raise VisibleTerminalAdapterError("expert_deployment_collision")
        return source_digest, source_size, True
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    descriptor: int | None = None
    try:
        descriptor = os.open(destination, flags, 0o600)
        with source.open("rb") as input_handle, os.fdopen(descriptor, "wb") as output_handle:
            descriptor = None
            for block in iter(lambda: input_handle.read(64 * 1024), b""):
                output_handle.write(block)
            output_handle.flush()
            os.fsync(output_handle.fileno())
    except FileExistsError:
        return _copy_exclusive_or_verify(source, destination)
    except (OSError, ValueError) as error:
        raise VisibleTerminalAdapterError("expert_deployment_failed") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
    copied_digest, copied_size = _stable_digest(destination, maximum_bytes=MAX_BINARY_BYTES)
    if copied_size != source_size or not secrets.compare_digest(copied_digest, source_digest):
        raise VisibleTerminalAdapterError("expert_deployment_digest_mismatch")
    return copied_digest, copied_size, False


def _process_binding_digest(value: Mapping[str, object]) -> str:
    # Keep byte compatibility with bridge_server.payload_digest(prefix, dict).
    ordered = {
        key: value.get(key)
        for key in sorted(value)
        if key != "processBindingDigest"
    }
    joined = "ea-factory-front-office-process-binding-v1\n" + str(ordered)
    return hashlib.sha256(joined.encode("utf-8", errors="replace")).hexdigest()


def _parse_utc(value: object) -> datetime:
    text = str(value or "")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise VisibleTerminalAdapterError("process_observation_time_invalid") from error
    if parsed.tzinfo is None:
        raise VisibleTerminalAdapterError("process_observation_time_invalid")
    return parsed.astimezone(timezone.utc)


def _fresh_raw_binding(
    raw: object,
    *,
    target: dict,
    stage_id: str,
    maximum_age_seconds: int = 30,
    observed_against: datetime | None = None,
) -> dict:
    if not isinstance(raw, dict):
        raise VisibleTerminalAdapterError("process_binding_missing")
    expected = {
        "observedAt",
        "terminalProcessId",
        "terminalExecutablePath",
        "terminalWindowHandle",
        "terminalWindowOwnerProcessId",
        "terminalWindowTitle",
        "terminalWindowClass",
        "frontOfficeKind",
        "frontOfficeProcessId",
        "frontOfficeExecutablePath",
        "frontOfficeWindowHandle",
        "frontOfficeWindowOwnerProcessId",
        "frontOfficeWindowTitle",
        "frontOfficeWindowClass",
        "autoTradingState",
    }
    if set(raw) != expected:
        raise VisibleTerminalAdapterError("process_binding_shape_invalid")
    if (
        isinstance(maximum_age_seconds, bool)
        or not isinstance(maximum_age_seconds, int)
        or maximum_age_seconds < 1
        or maximum_age_seconds > DEFAULT_BACKTEST_TIMEOUT_SECONDS + 60
    ):
        raise VisibleTerminalAdapterError("process_binding_freshness_policy_invalid")
    observed = _parse_utc(raw.get("observedAt"))
    reference = observed_against or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        raise VisibleTerminalAdapterError("process_binding_freshness_policy_invalid")
    reference = reference.astimezone(timezone.utc)
    age = (reference - observed).total_seconds()
    if age < -2 or age > maximum_age_seconds:
        raise VisibleTerminalAdapterError("process_binding_stale")
    integer_fields = (
        "terminalProcessId",
        "terminalWindowHandle",
        "terminalWindowOwnerProcessId",
        "frontOfficeProcessId",
        "frontOfficeWindowHandle",
        "frontOfficeWindowOwnerProcessId",
    )
    if any(
        isinstance(raw.get(field), bool)
        or not isinstance(raw.get(field), int)
        or int(raw.get(field)) <= 0
        for field in integer_fields
    ):
        raise VisibleTerminalAdapterError("process_binding_identity_invalid")
    if (
        raw["terminalProcessId"] != raw["terminalWindowOwnerProcessId"]
        or raw["frontOfficeProcessId"] != raw["frontOfficeWindowOwnerProcessId"]
        or not isinstance(raw.get("autoTradingState"), bool)
    ):
        raise VisibleTerminalAdapterError("process_binding_owner_mismatch")
    terminal_path = _resolved_file(
        raw.get("terminalExecutablePath"),
        "terminal_process_image_invalid",
        maximum_bytes=1024 * 1024 * 1024,
    )
    expected_terminal = Path(target["terminalPath"])
    front_path = _resolved_file(
        raw.get("frontOfficeExecutablePath"),
        "front_office_process_image_invalid",
        maximum_bytes=1024 * 1024 * 1024,
    )
    expected_front = (
        Path(target["compilerPath"])
        if stage_id == "compile_validate"
        else expected_terminal
    )
    if (
        os.path.normcase(str(terminal_path)) != os.path.normcase(str(expected_terminal))
        or os.path.normcase(str(front_path)) != os.path.normcase(str(expected_front))
        or raw.get("frontOfficeKind")
        != ("metaeditor" if stage_id == "compile_validate" else "strategy_tester")
        or not str(raw.get("terminalWindowTitle") or "").strip()
        or not str(raw.get("terminalWindowClass") or "").strip()
        or not str(raw.get("frontOfficeWindowTitle") or "").strip()
        or not str(raw.get("frontOfficeWindowClass") or "").strip()
    ):
        raise VisibleTerminalAdapterError("process_binding_target_mismatch")
    terminal_digest, _ = _stable_digest(terminal_path, maximum_bytes=1024 * 1024 * 1024)
    front_digest, _ = _stable_digest(front_path, maximum_bytes=1024 * 1024 * 1024)
    binding = {
        "schemaVersion": PROCESS_BINDING_SCHEMA,
        "observedAt": observed.isoformat(),
        "stageId": stage_id,
        "terminalCandidateId": target["candidateId"],
        "terminalSelectionRevision": target["selectionRevision"],
        "terminalBindingDigest": target["bindingDigest"],
        "terminalProcessId": raw["terminalProcessId"],
        "terminalExecutableSha256": terminal_digest,
        "terminalWindowHandle": raw["terminalWindowHandle"],
        "terminalWindowOwnerProcessId": raw["terminalWindowOwnerProcessId"],
        "terminalWindowTitleSha256": _sha256_text(raw["terminalWindowTitle"]),
        "terminalWindowClassSha256": _sha256_text(raw["terminalWindowClass"]),
        "frontOfficeKind": raw["frontOfficeKind"],
        "frontOfficeProcessId": raw["frontOfficeProcessId"],
        "frontOfficeExecutableSha256": front_digest,
        "frontOfficeWindowHandle": raw["frontOfficeWindowHandle"],
        "frontOfficeWindowOwnerProcessId": raw["frontOfficeWindowOwnerProcessId"],
        "frontOfficeWindowTitleSha256": _sha256_text(raw["frontOfficeWindowTitle"]),
        "frontOfficeWindowClassSha256": _sha256_text(raw["frontOfficeWindowClass"]),
    }
    binding["processBindingDigest"] = _process_binding_digest(binding)
    return binding


def _validate_target(raw: object, terminal_binding: dict, platform: str) -> dict:
    if not isinstance(raw, dict):
        raise VisibleTerminalAdapterError("terminal_target_missing")
    required = {
        "candidateId",
        "selectionRevision",
        "bindingDigest",
        "platform",
        "installPath",
        "dataPath",
        "terminalPath",
        "compilerPath",
    }
    if not required.issubset(raw):
        raise VisibleTerminalAdapterError("terminal_target_incomplete")
    if platform != "mt4":
        raise VisibleTerminalAdapterError("mt5_visible_adapter_not_verified")
    if (
        raw.get("platform") != platform
        or raw.get("candidateId") != terminal_binding.get("candidateId")
        or raw.get("selectionRevision") != terminal_binding.get("selectionRevision")
        or raw.get("bindingDigest") != terminal_binding.get("bindingDigest")
        or re.fullmatch(r"mtc-[A-Za-z0-9._-]{1,115}", str(raw.get("candidateId") or ""))
        is None
        or isinstance(raw.get("selectionRevision"), bool)
        or not isinstance(raw.get("selectionRevision"), int)
        or raw.get("selectionRevision") < 1
        or SHA256.fullmatch(str(raw.get("bindingDigest") or "")) is None
    ):
        raise VisibleTerminalAdapterError("terminal_binding_mismatch")
    install = _resolved_directory(raw.get("installPath"), "terminal_install_path_invalid")
    data = _resolved_directory(raw.get("dataPath"), "terminal_data_path_invalid")
    terminal = _resolved_file(
        raw.get("terminalPath"),
        "terminal_executable_invalid",
        maximum_bytes=1024 * 1024 * 1024,
    )
    compiler = _resolved_file(
        raw.get("compilerPath"),
        "metaeditor_executable_invalid",
        maximum_bytes=1024 * 1024 * 1024,
    )
    if (
        terminal.name.casefold() != "terminal.exe"
        or compiler.name.casefold() != "metaeditor.exe"
        or terminal.parent != install
        or compiler.parent != install
        or not (data / "MQL4").is_dir()
        or _path_has_reparse_component(data / "MQL4")
    ):
        raise VisibleTerminalAdapterError("terminal_target_origin_invalid")
    return {
        "candidateId": raw["candidateId"],
        "selectionRevision": raw["selectionRevision"],
        "bindingDigest": raw["bindingDigest"],
        "platform": platform,
        "installPath": install,
        "dataPath": data,
        "terminalPath": terminal,
        "compilerPath": compiler,
    }


def _validate_request(raw: object, expected_stage: str) -> dict:
    if not isinstance(raw, dict):
        raise VisibleTerminalAdapterError("visible_request_invalid")
    required = {
        "schemaVersion",
        "buildId",
        "stageId",
        "platform",
        "artifactKind",
        "workspaceRoot",
        "versions",
        "terminalBinding",
        "visibleOperation",
        "missionId",
        "reportId",
        "safety",
    }
    allowed = required | {
        "processBinding",
        "terminalTarget",
        "resolvedTarget",
        "testerSettings",
        "capabilityCheckedAt",
    }
    if not required.issubset(raw) or not set(raw).issubset(allowed):
        raise VisibleTerminalAdapterError("visible_request_shape_invalid")
    platform = str(raw.get("platform") or "").lower()
    if (
        raw.get("schemaVersion") != REQUEST_SCHEMA
        or raw.get("stageId") != expected_stage
        or platform not in {"mt4", "mt5"}
        or raw.get("artifactKind") != "expert_advisor"
        or not SAFE_ID.fullmatch(str(raw.get("buildId") or ""))
        or not SAFE_ID.fullmatch(str(raw.get("missionId") or ""))
        or not SAFE_ID.fullmatch(str(raw.get("reportId") or ""))
    ):
        raise VisibleTerminalAdapterError("visible_request_contract_invalid")
    binding = raw.get("terminalBinding")
    operation = raw.get("visibleOperation")
    safety = raw.get("safety")
    if (
        not isinstance(binding, dict)
        or binding.get("platform") != platform
        or not isinstance(operation, dict)
        or not SAFE_OPERATION_ID.fullmatch(str(operation.get("operationId") or ""))
        or operation.get("stageId") != expected_stage
        or operation.get("state") != "reserved"
        or operation.get("requiresExplicitResume") is not False
        or not isinstance(safety, dict)
        or safety.get("liveTradingAllowed") is not False
        or safety.get("autoTradingMayBeToggled") is not False
        or safety.get("chartAttachmentAllowed") is not False
        or safety.get("terminalShutdownAllowed") is not False
        or safety.get("optimizationAllowed") is not False
        or safety.get("visualModeRequired") is not (expected_stage == "backtest_recheck")
    ):
        raise VisibleTerminalAdapterError("visible_request_safety_invalid")
    workspace = _resolved_directory(raw.get("workspaceRoot"), "workspace_root_invalid")
    versions = raw.get("versions")
    if not isinstance(versions, list) or not versions or len(versions) > 20:
        raise VisibleTerminalAdapterError("source_version_missing")
    candidates: list[dict] = []
    suffix = ".mq4" if platform == "mt4" else ".mq5"
    for item in versions:
        if not isinstance(item, dict):
            raise VisibleTerminalAdapterError("source_version_invalid")
        relative = item.get("versionFile") or item.get("sourceFile")
        source = _managed_path(workspace, relative, "source_path_invalid")
        source = _resolved_file(source, "source_file_invalid", maximum_bytes=MAX_SOURCE_BYTES)
        digest, _ = _stable_digest(source, maximum_bytes=MAX_SOURCE_BYTES)
        if (
            source.suffix.casefold() != suffix
            or SHA256.fullmatch(str(item.get("sourceDigest") or "")) is None
            or not secrets.compare_digest(digest, str(item.get("sourceDigest")))
        ):
            raise VisibleTerminalAdapterError("source_digest_mismatch")
        candidates.append({"row": copy.deepcopy(item), "path": source, "digest": digest})
    source = candidates[-1]
    return {
        "raw": copy.deepcopy(raw),
        "platform": platform,
        "stageId": expected_stage,
        "workspace": workspace,
        "source": source,
        "terminalBinding": copy.deepcopy(binding),
        "operation": copy.deepcopy(operation),
    }


def _validate_tester_input_preset(
    raw: object,
    *,
    source: Path,
    source_digest: str,
) -> dict | None:
    """Validate a full, exact-source MT4 Strategy Tester Input snapshot."""

    try:
        source_text = source.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeDecodeError) as error:
        raise VisibleTerminalAdapterError("tester_input_preset_source_unreadable") from error
    expected_assumptions = _mt4_source_input_snapshot(source_text)
    source_has_inputs = bool(expected_assumptions)
    if raw is None:
        if source_has_inputs:
            raise VisibleTerminalAdapterError("tester_input_preset_required")
        return None
    if not source_has_inputs:
        raise VisibleTerminalAdapterError("tester_input_preset_source_profile_mismatch")
    expected_keys = {
        "schemaVersion",
        "mode",
        "scope",
        "sourceDigest",
        "assumptions",
        "liveSourceDefaultsPreserved",
        "visibleExpertPropertiesRequired",
        "readbackRequired",
        "liveTradingAllowed",
        "fullCertifiedInputSnapshot",
        "simulationInputNames",
        "presetDigest",
    }
    if not isinstance(raw, dict) or set(raw) != expected_keys:
        raise VisibleTerminalAdapterError("tester_input_preset_shape_invalid")
    unsigned = copy.deepcopy(raw)
    claimed_digest = str(unsigned.pop("presetDigest", "") or "").strip().lower()
    if (
        raw.get("schemaVersion") != TESTER_INPUT_PRESET_SCHEMA
        or raw.get("mode")
        != "full_certified_input_snapshot_with_explicit_simulation_assumptions"
        or raw.get("scope") != "mt4_strategy_tester_only"
        or raw.get("sourceDigest") != source_digest
        or raw.get("assumptions") != expected_assumptions
        or raw.get("liveSourceDefaultsPreserved") is not True
        or raw.get("visibleExpertPropertiesRequired") is not True
        or raw.get("readbackRequired") is not True
        or raw.get("liveTradingAllowed") is not False
        or raw.get("fullCertifiedInputSnapshot") is not True
        or raw.get("simulationInputNames")
        != _tester_simulation_input_names(expected_assumptions)
        or SHA256.fullmatch(claimed_digest) is None
        or not secrets.compare_digest(claimed_digest, _sha256_bytes(_canonical_json(unsigned)))
    ):
        raise VisibleTerminalAdapterError("tester_input_preset_invalid")
    return copy.deepcopy(raw)


def _mask_mql_comments_and_strings(source_text: str) -> str:
    """Blank comments/strings while preserving offsets and line boundaries."""

    output = list(source_text)
    state = "code"
    index = 0
    while index < len(source_text):
        current = source_text[index]
        following = source_text[index + 1] if index + 1 < len(source_text) else ""
        if state == "code":
            if current == "/" and following == "/":
                output[index] = output[index + 1] = " "
                index += 2
                state = "line_comment"
                continue
            if current == "/" and following == "*":
                output[index] = output[index + 1] = " "
                index += 2
                state = "block_comment"
                continue
            if current == '"':
                output[index] = " "
                index += 1
                state = "string"
                continue
        elif state == "line_comment":
            if current in "\r\n":
                state = "code"
            else:
                output[index] = " "
            index += 1
            continue
        elif state == "block_comment":
            if current == "*" and following == "/":
                output[index] = output[index + 1] = " "
                index += 2
                state = "code"
                continue
            if current not in "\r\n":
                output[index] = " "
            index += 1
            continue
        elif state == "string":
            output[index] = current if current in "\r\n" else " "
            if current == "\\" and index + 1 < len(source_text):
                if source_text[index + 1] not in "\r\n":
                    output[index + 1] = " "
                index += 2
                continue
            if current == '"':
                state = "code"
            elif current in "\r\n":
                raise VisibleTerminalAdapterError(
                    "tester_input_source_contract_unsupported"
                )
            index += 1
            continue
        index += 1
    if state not in {"code", "line_comment"}:
        raise VisibleTerminalAdapterError("tester_input_source_contract_unsupported")
    return "".join(output)


def _brace_depth_at(code: str, position: int) -> int:
    depth = 0
    for character in code[:position]:
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth < 0:
                return -1
    return depth


def _guarded_tester_simulation(code: str, input_name: str) -> bool:
    if (
        MT4_TESTER_SIMULATION_NAME_PATTERN.search(input_name) is None
        or MT4_TESTER_SIMULATION_FORBIDDEN_NAME_PATTERN.search(input_name) is not None
    ):
        return False
    name = re.escape(input_name)
    return re.search(
        rf"(?mi)^[ \t]*if[ \t]*\([ \t]*(?:![ \t]*{name}\b|"
        rf"{name}\b[ \t]*==[ \t]*false\b|false\b[ \t]*==[ \t]*{name}\b)"
        r"[ \t]*\)[ \t]*(?:\{[ \t]*)?return[ \t]*;",
        code,
    ) is not None


def _tester_simulation_input_names(assumptions: list[dict]) -> list[str]:
    return [
        str(item["inputName"])
        for item in assumptions
        if item.get("testerValue") != item.get("sourceDefault")
    ]


def _mt4_source_input_snapshot(source_text: str) -> list[dict]:
    """Return every supported MT4 Input default or fail before visible UI."""

    if not isinstance(source_text, str) or not source_text.strip():
        raise VisibleTerminalAdapterError("tester_input_source_contract_unsupported")
    code = _mask_mql_comments_and_strings(source_text)
    input_tokens = list(re.finditer(r"(?i)\b(?:input|extern|sinput)\b", code))
    if len(input_tokens) > MT4_TESTER_INPUT_MAX_COUNT:
        raise VisibleTerminalAdapterError("tester_input_source_contract_unsupported")
    declarations: list[tuple[str, str, str]] = []
    seen_lines: set[int] = set()
    for token_match in input_tokens:
        line_start = code.rfind("\n", 0, token_match.start()) + 1
        line_end = code.find("\n", token_match.end())
        if line_end < 0:
            line_end = len(code)
        if line_start in seen_lines:
            raise VisibleTerminalAdapterError("tester_input_source_contract_unsupported")
        seen_lines.add(line_start)
        line = code[line_start:line_end].rstrip("\r")
        declaration = re.fullmatch(
            r"[ \t]*(input|extern)[ \t]+([A-Za-z_][A-Za-z0-9_]*)"
            r"[ \t]+([A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*"
            r"([^;\r\n]+?)[ \t]*;[ \t]*",
            line,
            flags=re.IGNORECASE,
        )
        if declaration is None or _brace_depth_at(code, line_start) != 0:
            raise VisibleTerminalAdapterError("tester_input_source_contract_unsupported")
        kind = declaration.group(2).lower()
        name = declaration.group(3)
        literal = declaration.group(4).strip()
        if kind not in MT4_TESTER_INPUT_TYPES:
            raise VisibleTerminalAdapterError("tester_input_source_contract_unsupported")
        declarations.append((kind, name, literal))
    folded_names = [name.casefold() for _kind, name, _literal in declarations]
    if len(folded_names) != len(set(folded_names)):
        raise VisibleTerminalAdapterError("tester_input_source_contract_unsupported")
    snapshot: list[dict] = []
    for kind, name, literal in declarations:
        try:
            source_default = _parse_tester_input_token(literal, kind)
        except VisibleTerminalAdapterError as error:
            raise VisibleTerminalAdapterError(
                "tester_input_source_contract_unsupported"
            ) from error
        simulation = bool(
            kind == "bool"
            and source_default is False
            and _guarded_tester_simulation(code, name)
        )
        snapshot.append({
            "inputName": name,
            "inputType": kind,
            "sourceDefault": source_default,
            "testerValue": True if simulation else source_default,
            "reasonCode": (
                "simulate_external_fundamental_confirmation_for_historical_test_only"
                if name == "FundamentalCriteriaConfirmed"
                else "simulate_external_benchmark_uptrend_for_historical_test_only"
                if name == "ExternalBenchmarkUptrendConfirmed"
                else "simulate_external_manual_confirmation_for_historical_test_only"
                if simulation
                else "reset_to_certified_source_default_to_prevent_stale_tester_state"
            ),
        })
    return snapshot


def _can_slim_certified_input_snapshot(source_text: str) -> list[dict] | None:
    """Compatibility attestation for the existing certified CAN SLIM profile."""

    if re.search(
        r'(?m)^\s*const\s+string\s+CERTIFIED_PROFILE_VERSION\s*=\s*'
        r'"can-slim-mt4-certified-v3"\s*;\s*$',
        source_text,
    ) is None:
        return None
    try:
        snapshot = _mt4_source_input_snapshot(source_text)
    except VisibleTerminalAdapterError:
        return None
    if [(item["inputName"], item["inputType"]) for item in snapshot] != list(
        CAN_SLIM_CERTIFIED_INPUT_LAYOUT
    ):
        return None
    if any(
        item["sourceDefault"] != CAN_SLIM_FIXED_SOURCE_DEFAULTS[item["inputName"]]
        for item in snapshot
        if item["inputName"] in CAN_SLIM_FIXED_SOURCE_DEFAULTS
    ):
        return None
    if _tester_simulation_input_names(snapshot) != list(CAN_SLIM_SIMULATION_INPUT_NAMES):
        return None
    return snapshot


def _validate_tester_policy(
    raw: object,
    binary_name: str,
    *,
    source: Path,
    source_digest: str,
) -> dict:
    if not isinstance(raw, dict):
        raise VisibleTerminalAdapterError("tester_settings_missing")
    required_keys = {
        "schemaVersion",
        "expertFileName",
        "symbolPolicy",
        "period",
        "model",
        "spreadPolicy",
        "useDate",
        "fromDate",
        "toDate",
        "depositPolicy",
        "visualMode",
        "optimizationEnabled",
        "shutdownTerminalAfterTest",
        "liveTradingAllowed",
    }
    allowed_keys = required_keys | {"testerInputPreset"}
    if (
        not required_keys.issubset(raw)
        or not set(raw).issubset(allowed_keys)
        or raw.get("schemaVersion") != TESTER_SETTINGS_SCHEMA
        or raw.get("expertFileName") != binary_name
        or raw.get("symbolPolicy") != "current_tester_selection_required"
        or raw.get("period") not in ALLOWED_PERIODS
        or raw.get("model") not in ALLOWED_MODELS
        or raw.get("spreadPolicy") != "current"
        or raw.get("useDate") is not False
        or raw.get("fromDate") is not None
        or raw.get("toDate") is not None
        or raw.get("depositPolicy") != "current_tester_deposit"
        or raw.get("visualMode") is not True
        or raw.get("optimizationEnabled") is not False
        or raw.get("shutdownTerminalAfterTest") is not False
        or raw.get("liveTradingAllowed") is not False
    ):
        raise VisibleTerminalAdapterError("tester_settings_policy_invalid")
    normalized = copy.deepcopy(raw)
    preset = _validate_tester_input_preset(
        raw.get("testerInputPreset"),
        source=source,
        source_digest=source_digest,
    )
    if preset is None:
        normalized.pop("testerInputPreset", None)
    else:
        normalized["testerInputPreset"] = preset
    return normalized


def _powershell_executable(platform: str) -> Path:
    system_root = Path(os.environ.get("WINDIR") or r"C:\Windows")
    candidates = (
        [system_root / "SysWOW64" / "WindowsPowerShell" / "v1.0" / "powershell.exe"]
        if platform == "mt4"
        else []
    ) + [system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"]
    for candidate in candidates:
        if candidate.is_file() and not _path_has_reparse_component(candidate):
            return candidate.resolve(strict=True)
    raise VisibleTerminalAdapterError("powershell_runtime_unavailable")


def _default_powershell_runner(
    payload: dict,
    *,
    response_path: Path,
    timeout_seconds: int,
) -> dict:
    try:
        script = Path(__file__).with_suffix(".ps1").resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError("visible_ui_script_missing") from error
    request_path = response_path.with_name(response_path.stem + "-request.json")
    _write_exclusive(request_path, _canonical_json(payload), "ui_request_exists")
    command = [
        str(_powershell_executable(str(payload.get("platform") or ""))),
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        "-RequestPath",
        str(request_path),
        "-ResponsePath",
        str(response_path),
    ]
    started = time.perf_counter()
    bounded_timeout = max(10, min(int(timeout_seconds), DEFAULT_BACKTEST_TIMEOUT_SECONDS))
    process_timeout = (
        bounded_timeout + POWERSHELL_COMPLETION_MARGIN_SECONDS
        if bounded_timeout == DEFAULT_BACKTEST_TIMEOUT_SECONDS
        else bounded_timeout
    )
    try:
        result = subprocess.run(
            command,
            cwd=str(script.parent),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            timeout=process_timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise VisibleTerminalAdapterError("visible_ui_timeout", retryable=True) from error
    except (OSError, ValueError) as error:
        raise VisibleTerminalAdapterError("visible_ui_process_failed", retryable=True) from error
    finally:
        try:
            request_path.unlink(missing_ok=True)
        except OSError:
            pass
    if len(result.stdout or b"") + len(result.stderr or b"") > 64 * 1024:
        raise VisibleTerminalAdapterError("visible_ui_output_exceeded")
    if not response_path.is_file():
        raise VisibleTerminalAdapterError("visible_ui_response_missing", retryable=True)
    try:
        raw = json.loads(response_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise VisibleTerminalAdapterError("visible_ui_response_invalid") from error
    finally:
        try:
            response_path.unlink(missing_ok=True)
        except OSError:
            pass
    if result.returncode != 0 or not isinstance(raw, dict) or raw.get("ok") is not True:
        code = str(raw.get("reasonCode") or "visible_ui_action_failed") if isinstance(raw, dict) else "visible_ui_action_failed"
        if not re.fullmatch(r"[a-z0-9_]{3,80}", code):
            code = "visible_ui_action_failed"
        raise VisibleTerminalAdapterError(code, retryable=code.endswith(("_timeout", "_not_ready")))
    raw["pythonObservedDurationMs"] = round((time.perf_counter() - started) * 1000)
    return raw


def _validate_png(path: Path) -> tuple[str, int]:
    digest, size = _stable_digest(path, maximum_bytes=MAX_EVIDENCE_BYTES)
    try:
        header = path.read_bytes()[:8]
    except OSError as error:
        raise VisibleTerminalAdapterError("screenshot_unreadable") from error
    if header != b"\x89PNG\r\n\x1a\n" or size < 1024:
        raise VisibleTerminalAdapterError("screenshot_invalid")
    return digest, size


def _relative_path(path: Path, workspace: Path) -> str:
    resolved = path.resolve(strict=True)
    if not _is_relative_to(resolved, workspace):
        raise VisibleTerminalAdapterError("artifact_outside_workspace")
    return resolved.relative_to(workspace).as_posix()


def _artifact(
    alias: str,
    path: Path,
    workspace: Path,
    *,
    artifact_kind: str | None = None,
) -> dict:
    return {
        "alias": alias,
        "relativePath": _relative_path(path, workspace),
        "artifactKind": artifact_kind or ARTIFACT_KINDS[alias],
    }


def _bridge_payload_digest(prefix: str, value: object) -> str:
    return hashlib.sha256(
        f"{prefix}\n{value}".encode("utf-8", errors="replace")
    ).hexdigest()


def _normalized_compile_log(
    result_line: str,
    source_name: str,
    source_digest: str,
    binary_name: str,
    binary_digest: str,
) -> bytes:
    if re.fullmatch(r"Result:\s*0\s+errors?,\s*0\s+warnings?", result_line.strip(), re.I) is None:
        raise VisibleTerminalAdapterError("compile_result_line_unverified")
    return (
        "MetaEditor verified compile result\n"
        f"Source: {source_name}\n"
        f"sourceDigest: {source_digest}\n"
        f"Compiled binary: {binary_name}\n"
        f"compiledBinarySha256: {binary_digest}\n"
        f"{result_line.strip()}\n"
    ).encode("utf-8")


def _read_json_object(path: Path, code: str, *, maximum_bytes: int = 256 * 1024) -> dict:
    try:
        _digest, size = _stable_digest(path, maximum_bytes=maximum_bytes)
        if size > maximum_bytes:
            raise VisibleTerminalAdapterError(code)
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except VisibleTerminalAdapterError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise VisibleTerminalAdapterError(code) from error
    if not isinstance(value, dict):
        raise VisibleTerminalAdapterError(code)
    return value


def _next_recovery_receipt_path(
    workspace: Path,
    operation_id: str,
    stage_token: str,
) -> Path:
    parent = workspace / "Summaries"
    for attempt in range(1, 65):
        candidate = parent / (
            f"{operation_id}-{stage_token}-receipt-recovery-{attempt:02d}.json"
        )
        if not candidate.exists():
            return candidate
    raise VisibleTerminalAdapterError("visible_recovery_receipt_limit")


def _action_intent_payload(context: dict, target: dict) -> dict:
    return {
        "schemaVersion": ACTION_INTENT_SCHEMA,
        "operationId": context["operation"]["operationId"],
        "stageId": context["stageId"],
        "terminalCandidateId": target["candidateId"],
        "terminalSelectionRevision": target["selectionRevision"],
        "terminalBindingDigest": target["bindingDigest"],
        "sourceDigest": context["source"]["digest"],
    }


def _require_exact_action_intent(path: Path, expected: dict) -> None:
    observed = _read_json_object(
        path,
        "visible_action_intent_missing_or_invalid",
        maximum_bytes=16 * 1024,
    )
    if observed != expected:
        raise VisibleTerminalAdapterError("visible_action_intent_mismatch")


def _require_exact_json_object(path: Path, expected: dict, code: str) -> None:
    observed = _read_json_object(path, code, maximum_bytes=32 * 1024)
    if observed != expected:
        raise VisibleTerminalAdapterError(code)


def _backtest_action_request_payload(
    context: dict,
    target: dict,
    *,
    policy: dict,
    binary_digest: str,
    binary_name: str,
    expert_ui_path: str,
) -> tuple[dict, str]:
    raw = context["raw"]
    unsigned = {
        "schemaVersion": BACKTEST_ACTION_REQUEST_SCHEMA,
        "protocolVersion": "durable-start-boundary-v1",
        "operationId": context["operation"]["operationId"],
        "stageId": context["stageId"],
        "buildId": raw["buildId"],
        "missionId": raw["missionId"],
        "reportId": raw["reportId"],
        "terminalCandidateId": target["candidateId"],
        "terminalSelectionRevision": target["selectionRevision"],
        "terminalBindingDigest": target["bindingDigest"],
        "sourceDigest": context["source"]["digest"],
        "compiledBinarySha256": binary_digest,
        "expertFileName": binary_name,
        "expertUiPathDigest": _sha256_text(expert_ui_path),
        "testerSettingsDigest": _sha256_bytes(_canonical_json(policy)),
        "testerInputPresetDigest": (
            (policy.get("testerInputPreset") or {}).get("presetDigest")
            if policy.get("testerInputPreset") is not None
            else None
        ),
        "safetyPolicyDigest": _sha256_bytes(_canonical_json(raw["safety"])),
    }
    digest = _sha256_bytes(_canonical_json(unsigned))
    return {**unsigned, "actionRequestDigest": digest}, digest


def _tester_start_boundary_payload(operation_id: str, action_request_digest: str) -> dict:
    return {
        "schemaVersion": START_BOUNDARY_SCHEMA,
        "operationId": operation_id,
        "stageId": "backtest_recheck",
        "actionRequestDigest": action_request_digest,
    }


def _binding_pair(
    ui: dict,
    *,
    target: dict,
    stage_id: str,
    maximum_operation_seconds: int,
) -> tuple[dict, dict]:
    if (
        isinstance(maximum_operation_seconds, bool)
        or not isinstance(maximum_operation_seconds, int)
        or maximum_operation_seconds < 1
        or maximum_operation_seconds > DEFAULT_BACKTEST_TIMEOUT_SECONDS
    ):
        raise VisibleTerminalAdapterError("process_binding_freshness_policy_invalid")
    validated_at = datetime.now(timezone.utc)
    process_binding = _fresh_raw_binding(
        ui.get("processBinding"),
        target=target,
        stage_id=stage_id,
        maximum_age_seconds=maximum_operation_seconds + 30,
        observed_against=validated_at,
    )
    post_binding = _fresh_raw_binding(
        ui.get("postProcessBinding"),
        target=target,
        stage_id=stage_id,
        maximum_age_seconds=30,
        observed_against=validated_at,
    )
    process_observed = _parse_utc(process_binding.get("observedAt"))
    post_observed = _parse_utc(post_binding.get("observedAt"))
    if (
        process_observed > post_observed
        or (post_observed - process_observed).total_seconds()
        > maximum_operation_seconds + 10
        or process_binding["terminalProcessId"]
        != post_binding["terminalProcessId"]
        or process_binding["frontOfficeProcessId"]
        != post_binding["frontOfficeProcessId"]
        or process_binding["terminalWindowHandle"]
        != post_binding["terminalWindowHandle"]
        or process_binding["frontOfficeWindowHandle"]
        != post_binding["frontOfficeWindowHandle"]
        or process_binding["terminalExecutableSha256"]
        != post_binding["terminalExecutableSha256"]
        or process_binding["frontOfficeExecutableSha256"]
        != post_binding["frontOfficeExecutableSha256"]
        or process_binding["terminalWindowTitleSha256"]
        != post_binding["terminalWindowTitleSha256"]
        or process_binding["terminalWindowClassSha256"]
        != post_binding["terminalWindowClassSha256"]
        or process_binding["frontOfficeWindowTitleSha256"]
        != post_binding["frontOfficeWindowTitleSha256"]
        or process_binding["frontOfficeWindowClassSha256"]
        != post_binding["frontOfficeWindowClassSha256"]
        or process_binding["frontOfficeKind"]
        != post_binding["frontOfficeKind"]
        or not isinstance(ui.get("processBinding"), dict)
        or not isinstance(ui.get("postProcessBinding"), dict)
        or ui["processBinding"].get("autoTradingState")
        is not ui["postProcessBinding"].get("autoTradingState")
    ):
        raise VisibleTerminalAdapterError("process_binding_drift")
    return process_binding, post_binding


def _assert_preflight_continuity(binding: dict, probe: dict) -> None:
    if (
        binding.get("terminalProcessId") != probe.get("processId")
        or binding.get("terminalWindowHandle") != probe.get("windowHandle")
        or binding.get("terminalExecutableSha256") != probe.get("executableSha256")
    ):
        raise VisibleTerminalAdapterError("terminal_process_changed_after_capability_probe")


def _normalize_resolved_tester_settings(
    raw: object,
    *,
    binary_name: str,
    policy: dict,
    verified_deposit: object,
    verified_spread: object = None,
) -> dict:
    expected_keys = {
        "schemaVersion",
        "expertFileName",
        "symbol",
        "period",
        "model",
        "spread",
        "useDate",
        "fromDate",
        "toDate",
        "deposit",
        "visualMode",
        "optimizationEnabled",
        "shutdownTerminalAfterTest",
    }
    if (
        not isinstance(raw, dict)
        or set(raw) != expected_keys
        or raw.get("schemaVersion") != RESOLVED_TESTER_SCHEMA
        or raw.get("expertFileName") != binary_name
        or SAFE_SYMBOL.fullmatch(str(raw.get("symbol") or "")) is None
        or raw.get("period") != policy["period"]
        or raw.get("model") != policy["model"]
        or raw.get("useDate") is not False
        or raw.get("fromDate") is not None
        or raw.get("toDate") is not None
        or raw.get("visualMode") is not True
        or raw.get("optimizationEnabled") is not False
        or raw.get("shutdownTerminalAfterTest") is not False
    ):
        raise VisibleTerminalAdapterError("tester_settings_readback_invalid")
    # Fix insertion order because bridge ``payload_digest`` hashes ``str(dict)``.
    # The same normalized object is returned in metrics and stored in receipts.
    resolved = {
        "schemaVersion": raw.get("schemaVersion"),
        "expertFileName": raw.get("expertFileName"),
        "symbol": raw.get("symbol"),
        "period": raw.get("period"),
        "model": raw.get("model"),
        "spread": raw.get("spread"),
        "useDate": raw.get("useDate"),
        "fromDate": raw.get("fromDate"),
        "toDate": raw.get("toDate"),
        "deposit": raw.get("deposit"),
        "visualMode": raw.get("visualMode"),
        "optimizationEnabled": raw.get("optimizationEnabled"),
        "shutdownTerminalAfterTest": raw.get("shutdownTerminalAfterTest"),
    }
    spread = verified_spread if verified_spread is not None else resolved.get("spread")
    if isinstance(spread, str):
        spread = spread.strip()
        if spread.isdecimal():
            spread = int(spread)
        elif spread.casefold() == "current":
            spread = "current"
    if not (
        spread == "current"
        or (
            isinstance(spread, int)
            and not isinstance(spread, bool)
            and 0 <= spread <= 100000
        )
    ):
        raise VisibleTerminalAdapterError("tester_spread_readback_invalid")
    resolved["spread"] = spread
    deposit = verified_deposit
    if (
        isinstance(deposit, bool)
        or not isinstance(deposit, (int, float))
        or not (0 < float(deposit) <= 1_000_000_000)
    ):
        raise VisibleTerminalAdapterError("tester_deposit_unverified")
    resolved["deposit"] = deposit
    return resolved


def _normalize_resolved_tester_input_preset(
    raw: object,
    *,
    policy: dict,
) -> dict | None:
    preset = policy.get("testerInputPreset")
    if preset is None:
        if raw is not None:
            raise VisibleTerminalAdapterError("tester_input_preset_unexpected_readback")
        return None
    expected_keys = {
        "schemaVersion",
        "presetDigest",
        "sourceDigest",
        "mode",
        "scope",
        "readback",
        "visibleExpertProperties",
        "inputsTabSelected",
        "sourceDefaultsPreserved",
        "appliedOnlyToStrategyTester",
        "notAppliedToLiveChart",
        "readbackVerified",
    }
    # Keep both the outer object and every readback row in one deterministic
    # insertion order.  Bridge payload digests intentionally hash ``str(dict)``;
    # JSON receipts are written with sorted keys, so returning the deserialized
    # object directly would produce a different digest during recovery even
    # when all values are identical.
    expected_readback = [
        {
            "inputName": item["inputName"],
            "inputType": item["inputType"],
            "sourceDefault": item["sourceDefault"],
            "testerValue": item["testerValue"],
            "reasonCode": item["reasonCode"],
            "observedValue": item["testerValue"],
        }
        for item in preset["assumptions"]
    ]
    raw_readback = raw.get("readback") if isinstance(raw, dict) else None
    readback_matches = bool(
        isinstance(raw_readback, list)
        and len(raw_readback) == len(expected_readback)
        and all(
            isinstance(observed, dict)
            and set(observed) == set(expected)
            and all(
                _tester_input_values_equal(
                    observed.get(key),
                    expected.get(key),
                    str(expected.get("inputType") or ""),
                )
                if key in {"sourceDefault", "testerValue", "observedValue"}
                else observed.get(key) == expected.get(key)
                for key in expected
            )
            for observed, expected in zip(raw_readback, expected_readback)
        )
    )
    if (
        not isinstance(raw, dict)
        or set(raw) != expected_keys
        or raw.get("schemaVersion") != RESOLVED_TESTER_INPUT_PRESET_SCHEMA
        or raw.get("presetDigest") != preset["presetDigest"]
        or raw.get("sourceDigest") != preset["sourceDigest"]
        or raw.get("mode") != preset["mode"]
        or raw.get("scope") != preset["scope"]
        or not readback_matches
        or raw.get("visibleExpertProperties") is not True
        or raw.get("inputsTabSelected") is not True
        or raw.get("sourceDefaultsPreserved") is not True
        or raw.get("appliedOnlyToStrategyTester") is not True
        or raw.get("notAppliedToLiveChart") is not True
        or raw.get("readbackVerified") is not True
    ):
        raise VisibleTerminalAdapterError("tester_input_preset_readback_invalid")
    return {
        "schemaVersion": raw["schemaVersion"],
        "presetDigest": raw["presetDigest"],
        "sourceDigest": raw["sourceDigest"],
        "mode": raw["mode"],
        "scope": raw["scope"],
        "readback": expected_readback,
        "visibleExpertProperties": True,
        "inputsTabSelected": True,
        "sourceDefaultsPreserved": True,
        "appliedOnlyToStrategyTester": True,
        "notAppliedToLiveChart": True,
        "readbackVerified": True,
    }


def _tester_input_preset_set_bytes(preset: dict) -> bytes:
    lines = [
        f"{item['inputName']}={_tester_input_value_token(item['testerValue'], item['inputType'])}"
        for item in preset["assumptions"]
    ]
    return ("\r\n".join(lines) + "\r\n").encode("ascii", errors="strict")


def _tester_input_value_token(value: object, input_type: str) -> str:
    if input_type == "bool" and isinstance(value, bool):
        return "true" if value else "false"
    if input_type == "int" and isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if input_type == "double" and isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        if float("-inf") < number < float("inf"):
            return format(number, ".15g")
    raise VisibleTerminalAdapterError("tester_input_preset_value_invalid")


def _parse_tester_input_token(token: str, input_type: str) -> bool | int | float:
    normalized = token.strip()
    if input_type == "bool":
        folded = normalized.casefold()
        if folded in {"true", "1"}:
            return True
        if folded in {"false", "0"}:
            return False
    elif input_type == "int" and re.fullmatch(r"[+-]?\d+", normalized):
        value = int(normalized)
        if -2_147_483_648 <= value <= 2_147_483_647:
            return value
    elif input_type == "double" and re.fullmatch(
        r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",
        normalized,
    ):
        value = float(normalized)
        if float("-inf") < value < float("inf"):
            return value
    raise VisibleTerminalAdapterError("tester_input_readback_value_invalid")


def _tester_input_values_equal(
    observed: object,
    expected: object,
    input_type: str,
) -> bool:
    if input_type in {"bool", "int"}:
        return type(observed) is type(expected) and observed == expected
    if (
        input_type == "double"
        and isinstance(observed, (int, float))
        and not isinstance(observed, bool)
        and isinstance(expected, (int, float))
        and not isinstance(expected, bool)
    ):
        left = float(observed)
        right = float(expected)
        return bool(
            float("-inf") < left < float("inf")
            and float("-inf") < right < float("inf")
            and abs(left - right) <= 1e-12 * max(1.0, abs(right))
        )
    return False


def _decode_tester_set(payload: bytes) -> str:
    try:
        if payload.startswith((b"\xff\xfe", b"\xfe\xff")):
            return payload.decode("utf-16", errors="strict")
        if payload.startswith(b"\xef\xbb\xbf"):
            return payload.decode("utf-8-sig", errors="strict")
        if payload[:512].count(b"\x00") > 40:
            return payload.decode("utf-16-le", errors="strict")
        return payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise VisibleTerminalAdapterError("tester_input_readback_encoding_invalid") from error


def _resolved_tester_input_preset_from_set(
    path: Path,
    *,
    policy: dict,
) -> dict | None:
    preset = policy.get("testerInputPreset")
    if preset is None:
        if path.exists():
            raise VisibleTerminalAdapterError("tester_input_readback_unexpected")
        return None
    resolved = _resolved_file(
        path,
        "tester_input_readback_missing",
        maximum_bytes=MAX_SET_BYTES,
    )
    try:
        text = _decode_tester_set(resolved.read_bytes())
    except OSError as error:
        raise VisibleTerminalAdapterError("tester_input_readback_unreadable") from error
    assumptions = preset["assumptions"]
    expected_by_name = {item["inputName"]: item for item in assumptions}
    observed: dict[str, bool | int | float] = {}
    optimization_metadata_seen: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith((";", "#")) or "=" not in line:
            continue
        name, raw_value = line.split("=", 1)
        name = name.strip()
        if name not in expected_by_name:
            metadata = re.fullmatch(r"(.+),(F|1|2|3)", name)
            if (
                metadata is not None
                and metadata.group(1) in expected_by_name
                and name not in optimization_metadata_seen
            ):
                optimization_metadata_seen.add(name)
                continue
            raise VisibleTerminalAdapterError("tester_input_readback_unexpected_input")
        if name in observed:
            raise VisibleTerminalAdapterError("tester_input_readback_duplicate")
        # MT4 may append optimization fields after ``||``.  Only the first
        # saved current-value token is authoritative for this Strategy Tester
        # readback; MT4 may retain Tester Inputs after the run has completed.
        token = raw_value.split("||", 1)[0].strip()
        observed[name] = _parse_tester_input_token(
            token,
            expected_by_name[name]["inputType"],
        )
    if set(observed) != set(expected_by_name) or any(
        not _tester_input_values_equal(
            observed[item["inputName"]],
            item["testerValue"],
            item["inputType"],
        )
        for item in assumptions
    ):
        raise VisibleTerminalAdapterError("tester_input_preset_readback_mismatch")
    raw = {
        "schemaVersion": RESOLVED_TESTER_INPUT_PRESET_SCHEMA,
        "presetDigest": preset["presetDigest"],
        "sourceDigest": preset["sourceDigest"],
        "mode": preset["mode"],
        "scope": preset["scope"],
        "readback": [
            {**copy.deepcopy(item), "observedValue": observed[item["inputName"]]}
            for item in assumptions
        ],
        "visibleExpertProperties": True,
        "inputsTabSelected": True,
        "sourceDefaultsPreserved": True,
        "appliedOnlyToStrategyTester": True,
        "notAppliedToLiveChart": True,
        "readbackVerified": True,
    }
    return _normalize_resolved_tester_input_preset(raw, policy=policy)


def _validate_receipt_common(
    receipt: object,
    *,
    operation_id: str,
    stage_id: str,
    target: dict,
    source_digest: str,
    binary_digest: str,
) -> dict:
    required = {
        "schemaVersion",
        "operationId",
        "stageId",
        "terminalCandidateId",
        "status",
        "processBindingDigest",
        "postProcessBindingDigest",
        "sourceDigest",
        "compiledBinarySha256",
    }
    if (
        not isinstance(receipt, dict)
        or not required.issubset(receipt)
        or receipt.get("schemaVersion") != RECEIPT_SCHEMA
        or receipt.get("operationId") != operation_id
        or receipt.get("stageId") != stage_id
        or receipt.get("terminalCandidateId") != target["candidateId"]
        or receipt.get("status") != "verified"
        or receipt.get("sourceDigest") != source_digest
        or receipt.get("compiledBinarySha256") != binary_digest
        or any(
            SHA256.fullmatch(str(receipt.get(field) or "")) is None
            for field in (
                "processBindingDigest",
                "postProcessBindingDigest",
                "sourceDigest",
                "compiledBinarySha256",
            )
        )
    ):
        raise VisibleTerminalAdapterError("visible_receipt_invalid")
    return copy.deepcopy(receipt)


class _TesterTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.casefold()
        if lowered == "tr":
            self._row = []
        elif lowered in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.casefold()
        if lowered in {"td", "th"} and self._cell is not None:
            if self._row is not None:
                self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif lowered == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None
            self._cell = None


def _normalized_report_label(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def _unique_report_metadata_value(
    rows: list[list[str]],
    labels: set[str],
    code: str,
) -> str:
    normalized_labels = {_normalized_report_label(label) for label in labels}
    matches: list[str] = []
    for row in rows:
        if len(row) < 2 or _normalized_report_label(row[0]) not in normalized_labels:
            continue
        values = [str(cell).strip() for cell in row[1:] if str(cell).strip()]
        if len(values) != 1:
            raise VisibleTerminalAdapterError(code)
        matches.append(values[0])
    if len(matches) != 1:
        raise VisibleTerminalAdapterError(code)
    return matches[0]


def _report_expert_value(decoded: str, rows: list[list[str]]) -> str:
    """Return the EA identity from either supported MT4 report layout.

    Some MT4 builds emit an ``Expert`` metadata row, while build 1470 places
    the exact EA name only in ``<title>Strategy Tester: ...</title>``.  Prefer
    the row whenever it exists so a contradictory row can never be hidden by a
    valid-looking title.  The title fallback is accepted only when the row is
    absent and exactly one bounded title identifies the strategy tester.
    """

    normalized_labels = {
        _normalized_report_label(label) for label in {"expert", "expert advisor"}
    }
    row_matches: list[str] = []
    for row in rows:
        if len(row) < 2 or _normalized_report_label(row[0]) not in normalized_labels:
            continue
        values = [str(cell).strip() for cell in row[1:] if str(cell).strip()]
        if len(values) != 1:
            raise VisibleTerminalAdapterError("tester_report_settings_mismatch")
        row_matches.append(values[0])
    if len(row_matches) > 1:
        raise VisibleTerminalAdapterError("tester_report_settings_mismatch")
    if len(row_matches) == 1:
        return row_matches[0]

    title_matches = re.findall(
        r"<title\b[^>]{0,512}>\s*Strategy\s+Tester\s*:\s*([^<]{1,260}?)\s*</title>",
        decoded,
        re.IGNORECASE | re.DOTALL,
    )
    normalized_titles = [
        " ".join(html_lib.unescape(value).split()) for value in title_matches
    ]
    if len(normalized_titles) != 1 or not normalized_titles[0]:
        raise VisibleTerminalAdapterError("tester_report_settings_mismatch")
    return normalized_titles[0]


def _report_symbol_matches(value: str, expected: str) -> bool:
    normalized = " ".join(str(value or "").split())
    expected = str(expected or "").strip()
    return bool(
        expected
        and re.fullmatch(
            rf"{re.escape(expected)}(?:\s*\([^\r\n]*\))?",
            normalized,
            re.IGNORECASE,
        )
    )


def _report_period_matches(value: str, expected: str) -> bool:
    normalized = " ".join(str(value or "").split())
    expected = str(expected or "").strip()
    if not expected:
        return False
    if normalized.casefold() == expected.casefold():
        return True
    return bool(
        re.search(
            rf"(?<![A-Za-z0-9])\({re.escape(expected)}\)(?![A-Za-z0-9])",
            normalized,
            re.IGNORECASE,
        )
    )


def _report_model_matches(value: str, expected: str) -> bool:
    expected_label = {
        "every_tick": "every tick",
        "control_points": "control points",
        "open_prices": "open prices",
    }.get(str(expected or ""))
    normalized = " ".join(str(value or "").split()).casefold()
    return bool(
        expected_label
        and re.fullmatch(
            rf"{re.escape(expected_label)}(?:\s*\([^\r\n]*\))?",
            normalized,
        )
    )


def _report_mismatched_chart_errors(rows: list[list[str]]) -> int:
    token = _unique_report_metadata_value(
        rows,
        {"mismatched chart errors", "mismatched charts errors"},
        "tester_mismatched_chart_errors_unverified",
    )
    if re.fullmatch(r"[0-9][0-9 ,]*", token) is None:
        raise VisibleTerminalAdapterError("tester_mismatched_chart_errors_unverified")
    try:
        value = int(token.replace(" ", "").replace(",", ""))
    except ValueError as error:
        raise VisibleTerminalAdapterError(
            "tester_mismatched_chart_errors_unverified"
        ) from error
    if not (0 <= value <= 1_000_000_000):
        raise VisibleTerminalAdapterError("tester_mismatched_chart_errors_unverified")
    return value


def _backtest_attention_fields(zero_trade: bool, mismatched_chart_errors: int) -> dict:
    history_quality_issue = mismatched_chart_errors > 0
    if zero_trade and history_quality_issue:
        reason = "backtest_zero_trades_and_history_quality_errors"
        outcome = "completed_zero_trades_with_history_quality_errors"
    elif zero_trade:
        reason = "backtest_zero_trades"
        outcome = "completed_zero_trades"
    elif history_quality_issue:
        reason = "backtest_history_quality_errors"
        outcome = "completed_with_trades_history_quality_errors"
    else:
        reason = None
        outcome = "completed_with_trades"
    attention_required = bool(zero_trade or history_quality_issue)
    return {
        "mismatchedChartErrors": mismatched_chart_errors,
        "historyQualityIssue": history_quality_issue,
        "historyQualityVerified": not history_quality_issue,
        "attentionRequired": attention_required,
        "attentionReasonCode": reason,
        "performanceEvaluationAvailable": not attention_required,
        "executionOutcome": outcome,
    }


def _decode_tester_report(payload: bytes) -> str:
    encodings: list[str] = []
    if payload.startswith((b"\xff\xfe", b"\xfe\xff")):
        encodings.append("utf-16")
    elif payload[:512].count(b"\x00") > 40:
        encodings.append("utf-16-le")
    encodings.extend(("utf-8-sig", "cp1252"))
    for encoding in encodings:
        try:
            return payload.decode(encoding, errors="strict")
        except (UnicodeDecodeError, LookupError):
            continue
    raise VisibleTerminalAdapterError("tester_report_encoding_invalid")


def _report_number(text: str, label_pattern: str, code: str) -> float:
    match = re.search(
        rf"{label_pattern}\s*:?\s*([0-9][0-9 ,.]*[0-9]|[0-9])",
        text,
        re.IGNORECASE,
    )
    if match is None:
        raise VisibleTerminalAdapterError(code)
    normalized = match.group(1).replace(" ", "").replace(",", "")
    try:
        value = float(normalized)
    except ValueError as error:
        raise VisibleTerminalAdapterError(code) from error
    if not (0 <= value <= 1_000_000_000):
        raise VisibleTerminalAdapterError(code)
    return value


def _report_spread(text: str) -> int:
    match = re.search(
        r"(?:spread|สเปรด)\s*:?\s*(?:current\s*\(\s*(\d+)\s*\)|(\d+))",
        text,
        re.IGNORECASE,
    )
    if match is None:
        raise VisibleTerminalAdapterError("tester_spread_report_unverified")
    value = int(match.group(1) or match.group(2))
    if not (0 <= value <= 100000):
        raise VisibleTerminalAdapterError("tester_spread_report_unverified")
    return value


def _verify_tester_report_input_preset(plain: str, preset: object) -> bool:
    if not isinstance(preset, dict) or not isinstance(preset.get("assumptions"), list):
        raise VisibleTerminalAdapterError("tester_report_input_preset_invalid")
    assumptions = preset["assumptions"]
    names = [
        str(item.get("inputName") or "")
        for item in assumptions
        if isinstance(item, dict)
    ]
    if (
        not (1 <= len(assumptions) <= MT4_TESTER_INPUT_MAX_COUNT)
        or len(names) != len(assumptions)
        or any(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is None for name in names)
        or len({name.casefold() for name in names}) != len(names)
    ):
        raise VisibleTerminalAdapterError("tester_report_input_preset_invalid")
    marker = re.search(
        r"(?:^|\s)(?:parameters|inputs|พารามิเตอร์)\s*:?\s*",
        plain,
        re.IGNORECASE,
    )
    if marker is None:
        raise VisibleTerminalAdapterError("tester_report_parameters_missing")
    parameters = plain[marker.end() :]
    observed: dict[str, bool | int | float] = {}
    for item in assumptions:
        name = str(item.get("inputName") or "")
        matches = re.findall(
            rf"(?<![A-Za-z0-9_]){re.escape(name)}\s*=\s*([^\s;,<]+)",
            parameters,
        )
        if len(matches) != 1:
            raise VisibleTerminalAdapterError("tester_report_parameter_ambiguous")
        observed[name] = _parse_tester_input_token(
            matches[0],
            str(item.get("inputType") or ""),
        )
        if not _tester_input_values_equal(
            observed[name],
            item.get("testerValue"),
            str(item.get("inputType") or ""),
        ):
            raise VisibleTerminalAdapterError("tester_report_parameter_mismatch")
    if len(observed) != len(assumptions):
        raise VisibleTerminalAdapterError("tester_report_parameter_coverage_invalid")
    return True


def verify_visible_metaeditor_compile(context: dict) -> dict:
    """Read-only post-action verifier; it never invokes a compiler."""

    if not isinstance(context, dict):
        raise VisibleTerminalAdapterError("compile_verifier_context_invalid")
    source = _resolved_file(
        context.get("sourcePath"),
        "compile_verifier_source_missing",
        maximum_bytes=MAX_SOURCE_BYTES,
    )
    binary = _resolved_file(
        context.get("binaryPath"),
        "compile_verifier_binary_missing",
        maximum_bytes=MAX_BINARY_BYTES,
    )
    source_digest, _ = _stable_digest(source, maximum_bytes=MAX_SOURCE_BYTES)
    binary_digest, _ = _stable_digest(binary, maximum_bytes=MAX_BINARY_BYTES)
    ui = context.get("visibleUiResult")
    result_line = str(
        ui.get("compileResultLine") if isinstance(ui, dict) else ""
    ).strip()
    if (
        source_digest != context.get("sourceDigest")
        or re.fullmatch(
            r"Result:\s*0\s+errors?,\s*0\s+warnings?",
            result_line,
            re.IGNORECASE,
        )
        is None
    ):
        raise VisibleTerminalAdapterError("compile_visible_result_unverified")
    return {
        "compileVerified": True,
        "errorCount": 0,
        "warningCount": 0,
        "sourceDigest": source_digest,
        "compiledDigest": binary_digest,
        "resultLine": result_line,
    }


def verify_mt4_tester_report(context: dict) -> dict:
    """Parse the exact saved MT4 Tester report; it never starts a test."""

    if not isinstance(context, dict):
        raise VisibleTerminalAdapterError("backtest_verifier_context_invalid")
    report = _resolved_file(
        context.get("testerReportPath"),
        "tester_report_missing",
        maximum_bytes=MAX_EVIDENCE_BYTES,
    )
    deployed = _resolved_file(
        context.get("deployedExpertPath"),
        "deployed_expert_missing",
        maximum_bytes=MAX_BINARY_BYTES,
    )
    compiled_digest, _ = _stable_digest(deployed, maximum_bytes=MAX_BINARY_BYTES)
    if compiled_digest != context.get("compiledDigest"):
        raise VisibleTerminalAdapterError("deployed_expert_digest_mismatch")
    try:
        raw = report.read_bytes()
    except OSError as error:
        raise VisibleTerminalAdapterError("tester_report_unreadable") from error
    decoded = _decode_tester_report(raw)
    parser = _TesterTableParser()
    try:
        parser.feed(decoded)
    except Exception as error:
        raise VisibleTerminalAdapterError("tester_report_html_invalid") from error
    plain = re.sub(r"<[^>]{1,1000}>", " ", decoded)
    plain = " ".join(html_lib.unescape(plain).split())
    settings = context.get("resolvedTesterSettings")
    if not isinstance(settings, dict):
        raise VisibleTerminalAdapterError("tester_settings_readback_invalid")
    expert_file_name = Path(str(settings.get("expertFileName") or "")).name
    expert_stem = Path(expert_file_name).stem
    symbol = str(settings.get("symbol") or "")
    period = str(settings.get("period") or "")
    model = str(settings.get("model") or "")
    folded = plain.casefold()
    expert_report_value = _report_expert_value(decoded, parser.rows).replace("\\", "/")
    symbol_report_value = _unique_report_metadata_value(
        parser.rows,
        {"symbol"},
        "tester_report_settings_mismatch",
    )
    period_report_value = _unique_report_metadata_value(
        parser.rows,
        {"period"},
        "tester_report_settings_mismatch",
    )
    model_report_value = _unique_report_metadata_value(
        parser.rows,
        {"model"},
        "tester_report_settings_mismatch",
    )
    expert_report_name = Path(expert_report_value).name
    expert_report_stem = Path(expert_report_name).stem
    if (
        not expert_stem
        or expert_report_stem.casefold() != expert_stem.casefold()
        or expert_report_name.casefold()
        not in {expert_stem.casefold(), expert_file_name.casefold()}
        or not _report_symbol_matches(symbol_report_value, symbol)
        or not _report_period_matches(period_report_value, period)
        or not _report_model_matches(model_report_value, model)
        or "spread" not in folded
    ):
        raise VisibleTerminalAdapterError("tester_report_settings_mismatch")
    deposit = _report_number(
        plain,
        r"(?:initial\s+deposit|deposit|เงินฝากเริ่มต้น)",
        "tester_deposit_unverified",
    )
    report_spread = _report_spread(plain)
    expected_spread = settings.get("spread")
    if isinstance(expected_spread, str):
        expected_spread = expected_spread.strip()
        if expected_spread.isdecimal():
            expected_spread = int(expected_spread)
        elif expected_spread.casefold() == "current":
            expected_spread = "current"
    if (
        isinstance(expected_spread, bool)
        or (
            expected_spread != "current"
            and (
                not isinstance(expected_spread, int)
                or expected_spread != report_spread
            )
        )
    ):
        raise VisibleTerminalAdapterError("tester_spread_report_mismatch")
    total = int(
        _report_number(
            plain,
            r"(?:total\s+(?:trades|deals)|จำนวน(?:การ)?ซื้อขายทั้งหมด)",
            "tester_total_trades_unverified",
        )
    )
    sell_count = int(
        _report_number(
            plain,
            r"(?:short\s+positions(?:\s*\([^)]*\))?|sell\s+trades)",
            "tester_short_trades_unverified",
        )
    )
    buy_count = int(
        _report_number(
            plain,
            r"(?:long\s+positions(?:\s*\([^)]*\))?|buy\s+trades)",
            "tester_long_trades_unverified",
        )
    )
    row_sides: list[str] = []
    for row in parser.rows:
        exact_sides = [
            cell.casefold()
            for cell in row
            if cell.casefold() in {"buy", "sell"}
        ]
        if len(exact_sides) == 1:
            row_sides.append(exact_sides[0])
    if (
        total < 0
        or buy_count < 0
        or sell_count < 0
        or buy_count + sell_count != total
        or len(row_sides) != total
        or row_sides.count("buy") != buy_count
        or row_sides.count("sell") != sell_count
    ):
        raise VisibleTerminalAdapterError("tester_trade_rows_unverified")
    zero_trade = total == 0
    attention = _backtest_attention_fields(
        zero_trade,
        _report_mismatched_chart_errors(parser.rows),
    )
    tester_input_preset = context.get("testerInputPreset")
    tester_input_preset_report_verified = (
        _verify_tester_report_input_preset(plain, tester_input_preset)
        if tester_input_preset is not None
        else False
    )
    return {
        "backtestVerified": True,
        "testerTradeRowsVerified": True,
        "tradeCount": total,
        "tradeRowCount": len(row_sides),
        "buyTradeCount": buy_count,
        "sellTradeCount": sell_count,
        "zeroTrade": zero_trade,
        **attention,
        "deposit": deposit,
        "spread": report_spread,
        "testerInputPresetReportVerified": tester_input_preset_report_verified,
    }


def _validated_terminal_probe(raw: object, target: dict) -> dict:
    if not isinstance(raw, dict):
        raise VisibleTerminalAdapterError("terminal_process_probe_missing")
    expected = {
        "observedAt",
        "processId",
        "executablePath",
        "windowHandle",
        "windowOwnerProcessId",
        "windowTitle",
        "windowClass",
    }
    if set(raw) != expected:
        raise VisibleTerminalAdapterError("terminal_process_probe_invalid")
    observed = _parse_utc(raw.get("observedAt"))
    age = (datetime.now(timezone.utc) - observed).total_seconds()
    if age < -2 or age > 30:
        raise VisibleTerminalAdapterError("terminal_process_probe_stale")
    process_id = raw.get("processId")
    handle = raw.get("windowHandle")
    owner = raw.get("windowOwnerProcessId")
    if (
        isinstance(process_id, bool)
        or not isinstance(process_id, int)
        or process_id <= 0
        or isinstance(handle, bool)
        or not isinstance(handle, int)
        or handle <= 0
        or owner != process_id
        or str(raw.get("windowClass") or "") != "MetaQuotes::MetaTrader::4.00"
        or not str(raw.get("windowTitle") or "").strip()
    ):
        raise VisibleTerminalAdapterError("terminal_process_probe_identity_invalid")
    executable = _resolved_file(
        raw.get("executablePath"),
        "terminal_process_probe_image_invalid",
        maximum_bytes=1024 * 1024 * 1024,
    )
    if os.path.normcase(str(executable)) != os.path.normcase(str(target["terminalPath"])):
        raise VisibleTerminalAdapterError("terminal_process_probe_image_mismatch")
    return {
        "observedAt": observed.isoformat(),
        "processId": process_id,
        "windowHandle": handle,
        "executableSha256": _stable_digest(
            executable,
            maximum_bytes=1024 * 1024 * 1024,
        )[0],
        "windowTitleSha256": _sha256_text(raw["windowTitle"]),
        "windowClassSha256": _sha256_text(raw["windowClass"]),
    }


class VisibleFrontOfficeAdapter:
    """Bridge-callable MT4 visible adapter with durable operation receipts."""

    # Read-model metadata: MT5 intentionally stays disconnected until its own
    # controls and stable AutomationIds have been exercised and pinned.
    supported_platforms = frozenset({"mt4"})

    def __init__(
        self,
        *,
        target_resolver: Callable[..., dict],
        compile_verifier: Callable[[dict], dict] | None,
        backtest_verifier: Callable[[dict], dict] | None = None,
        powershell_runner: Callable[..., dict] | None = None,
    ) -> None:
        if not callable(target_resolver):
            raise TypeError("target_resolver must be callable")
        self._target_resolver = target_resolver
        self._compile_verifier = compile_verifier
        self._backtest_verifier = backtest_verifier
        self._powershell_runner = powershell_runner or _default_powershell_runner
        self._probe_lock = threading.Lock()
        self._operation_probes: dict[tuple[str, str], dict] = {}

    def _target(self, request: dict, context: dict) -> dict:
        supplied = request.get("resolvedTarget") or request.get("terminalTarget")
        if supplied is None:
            try:
                supplied = self._target_resolver(
                    platform=context["platform"],
                    terminal_binding=copy.deepcopy(context["terminalBinding"]),
                )
            except VisibleTerminalAdapterError:
                raise
            except Exception as error:
                raise VisibleTerminalAdapterError("terminal_target_resolution_failed") from error
        merged = dict(supplied)
        merged.update({
            "candidateId": context["terminalBinding"].get("candidateId"),
            "selectionRevision": context["terminalBinding"].get("selectionRevision"),
            "bindingDigest": context["terminalBinding"].get("bindingDigest"),
            "platform": context["platform"],
        })
        return _validate_target(
            merged,
            context["terminalBinding"],
            context["platform"],
        )

    def capability_provider(
        self,
        *,
        platform: str,
        stage_id: str,
        terminal_binding: dict,
        visible_operation: dict,
        resolved_target: dict | None = None,
        tester_settings: dict | None = None,
    ) -> dict:
        """Read-only capability check; it never opens or foregrounds a window."""

        common = {
            "ready": False,
            "reasonCode": None,
            "freshProcessProbe": False,
            "foregroundInteraction": True,
            "visibleEvidenceCapture": True,
            "terminalSelectionBound": True,
            "liveTradingAllowed": False,
            "terminalProcessMayRemainOpen": True,
            "processAndWindowBinding": True,
            "idempotentOperationBinding": True,
            "durableReceiptRecovery": True,
            "terminalShutdownAllowed": False,
            "autoTradingMayBeToggled": False,
            "chartAttachmentAllowed": False,
            "visibleMetaEditorCompile": stage_id == "compile_validate",
            "visibleStrategyTester": stage_id == "backtest_recheck",
            "visualModeRequired": stage_id == "backtest_recheck",
            "testerTradeRowsEvidence": stage_id == "backtest_recheck",
            "terminalOnlyPreflight": True,
        }
        try:
            if platform != "mt4":
                raise VisibleTerminalAdapterError("mt5_visible_adapter_not_verified")
            if stage_id not in {"compile_validate", "backtest_recheck"}:
                raise VisibleTerminalAdapterError("visible_stage_unsupported")
            if not isinstance(visible_operation, dict):
                raise VisibleTerminalAdapterError("visible_operation_missing")
            target = resolved_target
            if not isinstance(target, dict) or not target:
                target = self._target_resolver(
                    platform=platform,
                    terminal_binding=copy.deepcopy(terminal_binding),
                )
            merged_target = dict(target)
            merged_target.update({
                "candidateId": terminal_binding.get("candidateId"),
                "selectionRevision": terminal_binding.get("selectionRevision"),
                "bindingDigest": terminal_binding.get("bindingDigest"),
                "platform": platform,
            })
            target = _validate_target(merged_target, terminal_binding, platform)
            _powershell_executable(platform)
            if stage_id == "compile_validate" and not callable(self._compile_verifier):
                raise VisibleTerminalAdapterError("compile_verifier_not_connected")
            if stage_id == "backtest_recheck" and not callable(self._backtest_verifier):
                raise VisibleTerminalAdapterError("backtest_verifier_not_connected")
            operation_id = str((visible_operation or {}).get("operationId") or "")
            if not SAFE_OPERATION_ID.fullmatch(operation_id):
                raise VisibleTerminalAdapterError("visible_operation_invalid")
            with tempfile.TemporaryDirectory(prefix="metafx-visible-probe-") as temporary:
                response_path = Path(temporary) / "probe-response.json"
                probe = self._powershell_runner(
                    {
                        "schemaVersion": "ea-factory-visible-powershell-request-v1",
                        "action": "probe",
                        "platform": platform,
                        "operationId": operation_id,
                        "terminalPath": str(target["terminalPath"]),
                        "compilerPath": str(target["compilerPath"]),
                        "dataPath": str(target["dataPath"]),
                    },
                    response_path=response_path,
                    timeout_seconds=20,
                )
            if (
                not isinstance(probe, dict)
                or probe.get("schemaVersion") != POWERSHELL_RESULT_SCHEMA
                or probe.get("action") != "probe"
                or probe.get("operationId") != operation_id
            ):
                raise VisibleTerminalAdapterError("terminal_process_probe_invalid")
            common["terminalProcessProbe"] = _validated_terminal_probe(
                probe.get("terminalProbe"),
                target,
            )
        except VisibleTerminalAdapterError as error:
            common["reasonCode"] = error.code
            return common
        common["freshProcessProbe"] = True
        common["ready"] = True
        with self._probe_lock:
            self._operation_probes[(operation_id, stage_id)] = {
                "terminalCandidateId": target["candidateId"],
                "terminalSelectionRevision": target["selectionRevision"],
                "terminalBindingDigest": target["bindingDigest"],
                "probe": copy.deepcopy(common["terminalProcessProbe"]),
            }
        return common

    def _operation_probe(self, context: dict, target: dict) -> dict:
        operation_id = context["operation"]["operationId"]
        key = (operation_id, context["stageId"])
        with self._probe_lock:
            stored = copy.deepcopy(self._operation_probes.get(key))
        if (
            not isinstance(stored, dict)
            or stored.get("terminalCandidateId") != target["candidateId"]
            or stored.get("terminalSelectionRevision") != target["selectionRevision"]
            or stored.get("terminalBindingDigest") != target["bindingDigest"]
            or not isinstance(stored.get("probe"), dict)
        ):
            raise VisibleTerminalAdapterError("capability_process_probe_missing")
        observed = _parse_utc(stored["probe"].get("observedAt"))
        if (datetime.now(timezone.utc) - observed).total_seconds() > 60:
            raise VisibleTerminalAdapterError("capability_process_probe_stale")
        return stored["probe"]

    def _recover_compile(
        self,
        *,
        context: dict,
        target: dict,
        source: Path,
        source_digest: str,
        binary: Path,
        screenshot: Path,
        compile_log: Path,
        base_receipt_path: Path,
        preflight_probe: dict,
    ) -> dict:
        operation_id = context["operation"]["operationId"]
        workspace = context["workspace"]
        expected_binary = _resolved_file(
            binary,
            "compiled_binary_missing",
            maximum_bytes=MAX_BINARY_BYTES,
        )
        binary_digest, _ = _stable_digest(
            expected_binary,
            maximum_bytes=MAX_BINARY_BYTES,
        )
        receipt = _validate_receipt_common(
            _read_json_object(base_receipt_path, "visible_receipt_invalid"),
            operation_id=operation_id,
            stage_id="compile_validate",
            target=target,
            source_digest=source_digest,
            binary_digest=binary_digest,
        )
        screenshot_digest, _ = _validate_png(screenshot)
        compile_log_digest, _ = _stable_digest(
            compile_log,
            maximum_bytes=MAX_EVIDENCE_BYTES,
        )
        result_line = str(receipt.get("resultLine") or "").strip()
        if (
            receipt.get("zeroErrors") is not True
            or receipt.get("zeroWarnings") is not True
            or receipt.get("liveTradingExecuted") is not False
            or receipt.get("visibleWindowSha256") != screenshot_digest
            or receipt.get("compileLogSha256") != compile_log_digest
            or re.fullmatch(
                r"Result:\s*0\s+errors?,\s*0\s+warnings?",
                result_line,
                re.IGNORECASE,
            )
            is None
        ):
            raise VisibleTerminalAdapterError("visible_receipt_evidence_mismatch")
        try:
            log_text = compile_log.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise VisibleTerminalAdapterError("compile_log_unreadable") from error
        if (
            result_line not in log_text
            or source_digest not in log_text
            or binary_digest not in log_text
        ):
            raise VisibleTerminalAdapterError("compile_log_receipt_mismatch")

        recovery_receipt = _next_recovery_receipt_path(
            workspace,
            operation_id,
            "compile",
        )
        response_path = recovery_receipt.with_name(
            recovery_receipt.stem + "-ui.json"
        )
        ui = self._powershell_runner(
            {
                "schemaVersion": "ea-factory-visible-powershell-request-v1",
                "action": "recover_compile",
                "platform": "mt4",
                "operationId": operation_id,
                "terminalPath": str(target["terminalPath"]),
                "compilerPath": str(target["compilerPath"]),
                "dataPath": str(target["dataPath"]),
                "sourcePath": str(source),
                "binaryPath": str(expected_binary),
                "expectedSourceDigest": source_digest,
                "expectedBinaryDigest": binary_digest,
                "expectedTerminalProcessId": preflight_probe["processId"],
                "expectedTerminalWindowHandle": preflight_probe["windowHandle"],
            },
            response_path=response_path,
            timeout_seconds=30,
        )
        if (
            not isinstance(ui, dict)
            or ui.get("schemaVersion") != POWERSHELL_RESULT_SCHEMA
            or ui.get("action") != "recover_compile"
            or ui.get("operationId") != operation_id
            or ui.get("recoveredWithoutAction") is not True
            or ui.get("exactSourceWindowVerified") is not True
            or str(ui.get("compileResultLine") or "").strip() != result_line
        ):
            raise VisibleTerminalAdapterError("visible_compile_recovery_invalid")
        process_binding, post_binding = _binding_pair(
            ui,
            target=target,
            stage_id="compile_validate",
            maximum_operation_seconds=30,
        )
        _assert_preflight_continuity(process_binding, preflight_probe)
        current_source_digest, _ = _stable_digest(
            source,
            maximum_bytes=MAX_SOURCE_BYTES,
        )
        if not secrets.compare_digest(current_source_digest, source_digest):
            raise VisibleTerminalAdapterError("source_changed_before_visible_recovery")
        recovered_receipt = copy.deepcopy(receipt)
        recovered_receipt.update(
            {
                "processBindingDigest": process_binding["processBindingDigest"],
                "postProcessBindingDigest": post_binding["processBindingDigest"],
                "recoveredExistingReceipt": True,
                "recoveredFromReceiptSha256": _stable_digest(
                    base_receipt_path,
                    maximum_bytes=256 * 1024,
                )[0],
            }
        )
        _write_exclusive(
            recovery_receipt,
            _canonical_json(recovered_receipt),
            "visible_recovery_receipt_exists",
        )
        metrics = {
            "evidenceMode": EVIDENCE_MODE,
            "operationId": operation_id,
            "eaFactoryStage": "compile_validate",
            "platform": "mt4",
            "terminalCandidateId": target["candidateId"],
            "terminalSelectionRevision": target["selectionRevision"],
            "terminalBindingDigest": target["bindingDigest"],
            "processBinding": process_binding,
            "processBindingDigest": process_binding["processBindingDigest"],
            "postProcessBinding": post_binding,
            "postProcessBindingDigest": post_binding["processBindingDigest"],
            "processId": process_binding["frontOfficeProcessId"],
            "windowHandle": process_binding["frontOfficeWindowHandle"],
            "liveTradingExecuted": False,
            "autoTradingToggled": False,
            "autoTradingStateBefore": ui["processBinding"]["autoTradingState"],
            "autoTradingStateAfter": ui["postProcessBinding"]["autoTradingState"],
            "chartAttached": False,
            "terminalClosedByAdapter": False,
            "terminalStillRunning": True,
            "terminalStillOpen": True,
            "sourceDigest": source_digest,
            "compiledBinaryArtifactAlias": "compiled_binary",
            "compiledBinarySha256": binary_digest,
            "visibleWindowEvidenceArtifactAlias": "visible_window",
            "visibleWindowEvidenceSha256": screenshot_digest,
            "compileLogArtifactAlias": "compile_log",
            "compileLogSha256": compile_log_digest,
            "adapterReceiptArtifactAlias": "adapter_receipt",
            "visibleMetaEditor": True,
            "compileVerified": True,
            "compileExecuted": False,
            "recoveredExistingReceipt": True,
            "zeroErrors": True,
            "zeroWarnings": True,
            "backtestExecuted": False,
            "resultLine": result_line,
        }
        return {
            "schemaVersion": "ea-factory-visible-front-office-result-v1",
            "operationId": operation_id,
            "metrics": metrics,
            "artifactSpecifications": [
                _artifact("compiled_binary", expected_binary, workspace),
                _artifact("visible_window", screenshot, workspace),
                _artifact("compile_log", compile_log, workspace),
                _artifact("adapter_receipt", recovery_receipt, workspace),
            ],
        }

    def compile_handler(self, *, request: dict) -> dict:
        context = _validate_request(request, "compile_validate")
        target = self._target(request, context)
        preflight_probe = self._operation_probe(context, target)
        if not callable(self._compile_verifier):
            raise VisibleTerminalAdapterError("compile_verifier_not_connected")
        workspace = context["workspace"]
        source = context["source"]["path"]
        source_digest = context["source"]["digest"]
        binary = source.with_suffix(".ex4")
        operation_id = context["operation"]["operationId"]
        screenshot = workspace / "Screenshots" / f"{operation_id}-metaeditor.png"
        compile_log = workspace / "Reports" / f"{operation_id}-compile.txt"
        receipt_path = workspace / "Summaries" / f"{operation_id}-compile-receipt.json"
        intent_path = workspace / "Summaries" / f"{operation_id}-compile-intent.json"
        response_path = workspace / "Summaries" / f"{operation_id}-compile-ui.json"
        for parent in {screenshot.parent, compile_log.parent, receipt_path.parent}:
            parent.mkdir(parents=True, exist_ok=True)
            if _path_has_reparse_component(parent):
                raise VisibleTerminalAdapterError("evidence_directory_unsafe")
        expected_intent = _action_intent_payload(context, target)
        if receipt_path.exists():
            _require_exact_action_intent(intent_path, expected_intent)
            return self._recover_compile(
                context=context,
                target=target,
                source=source,
                source_digest=source_digest,
                binary=binary,
                screenshot=screenshot,
                compile_log=compile_log,
                base_receipt_path=receipt_path,
                preflight_probe=preflight_probe,
            )
        if intent_path.exists() or screenshot.exists() or compile_log.exists():
            # A visible action may already have happened.  Never issue a second
            # Compile click without a complete verified operation receipt.
            raise VisibleTerminalAdapterError("visible_action_state_uncertain")
        payload = {
            "schemaVersion": "ea-factory-visible-powershell-request-v1",
            "action": "compile",
            "platform": "mt4",
            "operationId": operation_id,
            "terminalPath": str(target["terminalPath"]),
            "compilerPath": str(target["compilerPath"]),
            "dataPath": str(target["dataPath"]),
            "sourcePath": str(source),
            "expectedSourceDigest": source_digest,
            "binaryPath": str(binary),
            "screenshotPath": str(screenshot),
            "timeoutSeconds": DEFAULT_UI_TIMEOUT_SECONDS,
            "expectedTerminalProcessId": preflight_probe["processId"],
            "expectedTerminalWindowHandle": preflight_probe["windowHandle"],
        }
        _write_exclusive(
            intent_path,
            _canonical_json(expected_intent),
            "visible_action_intent_exists",
        )
        ui = self._powershell_runner(
            payload,
            response_path=response_path,
            timeout_seconds=DEFAULT_UI_TIMEOUT_SECONDS,
        )
        if (
            not isinstance(ui, dict)
            or ui.get("schemaVersion") != POWERSHELL_RESULT_SCHEMA
            or ui.get("action") != "compile"
            or ui.get("operationId") != operation_id
            or ui.get("compileInvoked") is not True
            or ui.get("exactSourceWindowVerified") is not True
        ):
            raise VisibleTerminalAdapterError("visible_compile_result_invalid")
        process_binding, post_binding = _binding_pair(
            ui,
            target=target,
            stage_id="compile_validate",
            maximum_operation_seconds=DEFAULT_UI_TIMEOUT_SECONDS,
        )
        _assert_preflight_continuity(process_binding, preflight_probe)
        current_source_digest, _ = _stable_digest(source, maximum_bytes=MAX_SOURCE_BYTES)
        if not secrets.compare_digest(current_source_digest, source_digest):
            raise VisibleTerminalAdapterError("source_changed_during_visible_compile")
        verifier_context = {
            "platform": "mt4",
            "operationId": operation_id,
            "sourcePath": source,
            "binaryPath": binary,
            "sourceDigest": source_digest,
            "terminalTarget": copy.deepcopy(target),
            "visibleUiResult": copy.deepcopy(ui),
        }
        try:
            verified = self._compile_verifier(verifier_context)
        except VisibleTerminalAdapterError:
            raise
        except Exception as error:
            raise VisibleTerminalAdapterError("compile_verifier_failed") from error
        if not isinstance(verified, dict):
            raise VisibleTerminalAdapterError("compile_verifier_result_invalid")
        result_line = str(verified.get("resultLine") or "").strip()
        visible_result_line = str(ui.get("compileResultLine") or "").strip()
        expected_binary = _resolved_file(
            binary,
            "compiled_binary_missing",
            maximum_bytes=MAX_BINARY_BYTES,
        )
        binary_digest, _ = _stable_digest(expected_binary, maximum_bytes=MAX_BINARY_BYTES)
        if (
            verified.get("compileVerified") is not True
            or verified.get("errorCount") != 0
            or verified.get("warningCount") != 0
            or verified.get("sourceDigest") != source_digest
            or verified.get("compiledDigest") != binary_digest
            or result_line != visible_result_line
        ):
            raise VisibleTerminalAdapterError("compile_verification_failed")
        _write_exclusive(
            compile_log,
            _normalized_compile_log(
                result_line,
                source.name,
                source_digest,
                expected_binary.name,
                binary_digest,
            ),
            "compile_log_already_exists",
        )
        screenshot_digest, _ = _validate_png(screenshot)
        compile_log_digest, _ = _stable_digest(compile_log, maximum_bytes=MAX_EVIDENCE_BYTES)
        receipt = {
            "schemaVersion": RECEIPT_SCHEMA,
            "operationId": operation_id,
            "stageId": "compile_validate",
            "terminalCandidateId": target["candidateId"],
            "status": "verified",
            "processBindingDigest": process_binding["processBindingDigest"],
            "postProcessBindingDigest": post_binding["processBindingDigest"],
            "sourceDigest": source_digest,
            "compiledBinarySha256": binary_digest,
            "compileLogSha256": compile_log_digest,
            "visibleWindowSha256": screenshot_digest,
            "resultLine": result_line,
            "resolvedTesterSettingsDigest": None,
            "zeroErrors": True,
            "zeroWarnings": True,
            "liveTradingExecuted": False,
        }
        _write_exclusive(
            receipt_path,
            _canonical_json(receipt),
            "visible_receipt_already_exists",
        )
        metrics = {
            "evidenceMode": EVIDENCE_MODE,
            "operationId": operation_id,
            "eaFactoryStage": "compile_validate",
            "platform": "mt4",
            "terminalCandidateId": target["candidateId"],
            "terminalSelectionRevision": target["selectionRevision"],
            "terminalBindingDigest": target["bindingDigest"],
            "processBinding": process_binding,
            "processBindingDigest": process_binding["processBindingDigest"],
            "postProcessBinding": post_binding,
            "postProcessBindingDigest": post_binding["processBindingDigest"],
            "processId": process_binding["frontOfficeProcessId"],
            "windowHandle": process_binding["frontOfficeWindowHandle"],
            "liveTradingExecuted": False,
            "autoTradingToggled": False,
            "autoTradingStateBefore": ui["processBinding"]["autoTradingState"],
            "autoTradingStateAfter": ui["postProcessBinding"]["autoTradingState"],
            "chartAttached": False,
            "terminalClosedByAdapter": False,
            "terminalStillRunning": True,
            "terminalStillOpen": True,
            "sourceDigest": source_digest,
            "compiledBinaryArtifactAlias": "compiled_binary",
            "compiledBinarySha256": binary_digest,
            "visibleWindowEvidenceArtifactAlias": "visible_window",
            "visibleWindowEvidenceSha256": screenshot_digest,
            "compileLogArtifactAlias": "compile_log",
            "compileLogSha256": compile_log_digest,
            "adapterReceiptArtifactAlias": "adapter_receipt",
            "visibleMetaEditor": True,
            "compileVerified": True,
            "compileExecuted": True,
            "recoveredExistingReceipt": False,
            "zeroErrors": True,
            "zeroWarnings": True,
            "backtestExecuted": False,
            "resultLine": result_line,
        }
        return {
            "schemaVersion": "ea-factory-visible-front-office-result-v1",
            "operationId": operation_id,
            "metrics": metrics,
            "artifactSpecifications": [
                _artifact("compiled_binary", expected_binary, workspace),
                _artifact("visible_window", screenshot, workspace),
                _artifact("compile_log", compile_log, workspace),
                _artifact("adapter_receipt", receipt_path, workspace),
            ],
        }

    def _recover_backtest(
        self,
        *,
        context: dict,
        target: dict,
        policy: dict,
        source_digest: str,
        binary: Path,
        binary_digest: str,
        deployed: Path,
        expert_ui_path: str,
        settings_screenshot: Path,
        input_preset_screenshot: Path | None,
        input_preset_set: Path | None,
        input_readback_set: Path | None,
        result_screenshot: Path,
        report_screenshot: Path,
        tester_report: Path,
        base_receipt_path: Path,
        preflight_probe: dict,
        action_request_digest: str,
        start_boundary_digest: str,
    ) -> dict:
        operation_id = context["operation"]["operationId"]
        workspace = context["workspace"]
        receipt = _validate_receipt_common(
            _read_json_object(base_receipt_path, "visible_receipt_invalid"),
            operation_id=operation_id,
            stage_id="backtest_recheck",
            target=target,
            source_digest=source_digest,
            binary_digest=binary_digest,
        )
        settings_digest, _ = _validate_png(settings_screenshot)
        input_preset_digest = (
            _validate_png(input_preset_screenshot)[0]
            if input_preset_screenshot is not None
            else None
        )
        input_preset_set_digest = (
            _stable_digest(input_preset_set, maximum_bytes=MAX_SET_BYTES)[0]
            if input_preset_set is not None
            else None
        )
        input_readback_set_digest = (
            _stable_digest(input_readback_set, maximum_bytes=MAX_SET_BYTES)[0]
            if input_readback_set is not None
            else None
        )
        result_digest, _ = _validate_png(result_screenshot)
        report_screenshot_digest, _ = _validate_png(report_screenshot)
        report_digest, _ = _stable_digest(
            tester_report,
            maximum_bytes=MAX_EVIDENCE_BYTES,
        )
        stored_resolved = receipt.get("resolvedTesterSettings")
        stored_resolved_preset = receipt.get("resolvedTesterInputPreset")
        resolved_preset = _normalize_resolved_tester_input_preset(
            stored_resolved_preset,
            policy=policy,
        )
        readback_resolved_preset = (
            _resolved_tester_input_preset_from_set(
                input_readback_set,
                policy=policy,
            )
            if input_readback_set is not None
            else None
        )
        if readback_resolved_preset != resolved_preset:
            raise VisibleTerminalAdapterError("tester_input_preset_receipt_mismatch")
        if input_preset_set is not None:
            expected_preset_bytes = _tester_input_preset_set_bytes(
                policy["testerInputPreset"]
            )
            if input_preset_set.read_bytes() != expected_preset_bytes:
                raise VisibleTerminalAdapterError("tester_input_preset_set_mismatch")
        resolved_preset_digest = (
            _bridge_payload_digest(
                RESOLVED_TESTER_INPUT_PRESET_SCHEMA,
                resolved_preset,
            )
            if resolved_preset is not None
            else None
        )
        stored_counts = {
            "tradeCount": receipt.get("tradeCount"),
            "buyTradeCount": receipt.get("buyTradeCount"),
            "sellTradeCount": receipt.get("sellTradeCount"),
            "tradeRowCount": receipt.get("tradeRowCount"),
        }
        if (
            receipt.get("visualMode") is not True
            or receipt.get("optimizationEnabled") is not False
            or receipt.get("shutdownTerminalAfterTest") is not False
            or receipt.get("liveTradingExecuted") is not False
            or receipt.get("testerSettingsSha256") != settings_digest
            or receipt.get("testerInputPresetScreenshotSha256")
            != input_preset_digest
            or receipt.get("testerInputPresetSetSha256")
            != input_preset_set_digest
            or receipt.get("testerInputReadbackSetSha256")
            != input_readback_set_digest
            or receipt.get("testerInputPresetDigest")
            != (
                (policy.get("testerInputPreset") or {}).get("presetDigest")
                if policy.get("testerInputPreset") is not None
                else None
            )
            or receipt.get("resolvedTesterInputPresetDigest")
            != resolved_preset_digest
            or receipt.get("testerInputPresetReportVerified")
            != (resolved_preset is not None)
            or receipt.get("testerResultSha256") != result_digest
            or receipt.get("testerReportScreenshotSha256")
            != report_screenshot_digest
            or receipt.get("testerReportSha256") != report_digest
            or receipt.get("expertUiPathDigest") != _sha256_text(expert_ui_path)
            or receipt.get("actionRequestDigest") != action_request_digest
            or receipt.get("startBoundarySha256") != start_boundary_digest
            or not isinstance(stored_resolved, dict)
            or any(
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 0
                for key, value in stored_counts.items()
            )
            or stored_counts["buyTradeCount"] + stored_counts["sellTradeCount"]
            != stored_counts["tradeCount"]
            or stored_counts["tradeRowCount"] != stored_counts["tradeCount"]
            or receipt.get("zeroTrade") is not (stored_counts["tradeCount"] == 0)
        ):
            raise VisibleTerminalAdapterError("visible_receipt_evidence_mismatch")

        stored_mismatched_chart_errors = receipt.get("mismatchedChartErrors")
        if (
            isinstance(stored_mismatched_chart_errors, bool)
            or not isinstance(stored_mismatched_chart_errors, int)
            or stored_mismatched_chart_errors < 0
        ):
            raise VisibleTerminalAdapterError("visible_receipt_evidence_mismatch")
        stored_attention = _backtest_attention_fields(
            stored_counts["tradeCount"] == 0,
            stored_mismatched_chart_errors,
        )
        if any(receipt.get(key) != value for key, value in stored_attention.items()):
            raise VisibleTerminalAdapterError("visible_receipt_evidence_mismatch")

        recovery_receipt = _next_recovery_receipt_path(
            workspace,
            operation_id,
            "backtest",
        )
        response_path = recovery_receipt.with_name(
            recovery_receipt.stem + "-ui.json"
        )
        ui = self._powershell_runner(
            {
                "schemaVersion": "ea-factory-visible-powershell-request-v1",
                "action": "recover_backtest",
                "platform": "mt4",
                "operationId": operation_id,
                "terminalPath": str(target["terminalPath"]),
                "compilerPath": str(target["compilerPath"]),
                "dataPath": str(target["dataPath"]),
                "deployedExpertPath": str(deployed),
                "expectedDeployedExpertSha256": binary_digest,
                "expertFileName": binary.name,
                "expertUiPath": expert_ui_path,
                "testerSettings": policy,
                "expectedResolvedTesterSettings": copy.deepcopy(stored_resolved),
                "expectedTerminalProcessId": preflight_probe["processId"],
                "expectedTerminalWindowHandle": preflight_probe["windowHandle"],
            },
            response_path=response_path,
            timeout_seconds=30,
        )
        recovered_selected_expert = str(
            ui.get("selectedExpertReadback") if isinstance(ui, dict) else ""
        ).strip().replace("/", "\\").lstrip("\\").casefold()
        recovered_expected_experts = {
            expert_ui_path.replace("/", "\\").lstrip("\\").casefold(),
            (expert_ui_path + ".ex4").replace("/", "\\").lstrip("\\").casefold(),
        }
        if (
            not isinstance(ui, dict)
            or ui.get("schemaVersion") != POWERSHELL_RESULT_SCHEMA
            or ui.get("action") != "recover_backtest"
            or ui.get("operationId") != operation_id
            or ui.get("recoveredWithoutAction") is not True
            or ui.get("exactExpertVerified") is not True
            or recovered_selected_expert not in recovered_expected_experts
            or recovered_selected_expert == binary.name.casefold()
            or ui.get("deployedExpertSha256") != binary_digest
            or ui.get("settingsStillVerified") is not True
        ):
            raise VisibleTerminalAdapterError("visible_backtest_recovery_invalid")
        process_binding, post_binding = _binding_pair(
            ui,
            target=target,
            stage_id="backtest_recheck",
            maximum_operation_seconds=30,
        )
        _assert_preflight_continuity(process_binding, preflight_probe)
        verifier_context = {
            "platform": "mt4",
            "operationId": operation_id,
            "sourceDigest": source_digest,
            "compiledDigest": binary_digest,
            "deployedExpertPath": deployed,
            "resolvedTesterSettings": copy.deepcopy(stored_resolved),
            "testerReportPath": tester_report,
            "settingsScreenshotPath": settings_screenshot,
            "inputPresetScreenshotPath": input_preset_screenshot,
            "resultScreenshotPath": result_screenshot,
            "testerInputPreset": copy.deepcopy(policy.get("testerInputPreset")),
            "visibleUiResult": copy.deepcopy(ui),
            "recoveryOnly": True,
        }
        try:
            verified = self._backtest_verifier(verifier_context)
        except VisibleTerminalAdapterError:
            raise
        except Exception as error:
            raise VisibleTerminalAdapterError("backtest_verifier_failed") from error
        if not isinstance(verified, dict):
            raise VisibleTerminalAdapterError("backtest_verifier_result_invalid")
        verified_counts = {
            key: verified.get(key)
            for key in stored_counts
        }
        if (
            verified.get("backtestVerified") is not True
            or verified.get("testerTradeRowsVerified") is not True
            or verified_counts != stored_counts
            or verified.get("zeroTrade") is not (stored_counts["tradeCount"] == 0)
            or verified.get("mismatchedChartErrors")
            != stored_mismatched_chart_errors
            or any(
                verified.get(key) != value
                for key, value in stored_attention.items()
            )
            or verified.get("testerInputPresetReportVerified")
            != (resolved_preset is not None)
        ):
            raise VisibleTerminalAdapterError("backtest_recovery_evidence_mismatch")
        resolved = _normalize_resolved_tester_settings(
            stored_resolved,
            binary_name=binary.name,
            policy=policy,
            verified_deposit=verified.get("deposit"),
            verified_spread=verified.get("spread"),
        )
        resolved_digest = _bridge_payload_digest(
            "ea-factory-resolved-tester-settings-v1",
            resolved,
        )
        if receipt.get("resolvedTesterSettingsDigest") != resolved_digest:
            raise VisibleTerminalAdapterError("tester_settings_receipt_mismatch")
        recovered_receipt = copy.deepcopy(receipt)
        recovered_receipt.update(
            {
                "processBindingDigest": process_binding["processBindingDigest"],
                "postProcessBindingDigest": post_binding["processBindingDigest"],
                "recoveredExistingReceipt": True,
                "recoveredFromReceiptSha256": _stable_digest(
                    base_receipt_path,
                    maximum_bytes=256 * 1024,
                )[0],
                "zeroTrade": stored_counts["tradeCount"] == 0,
                **stored_attention,
            }
        )
        _write_exclusive(
            recovery_receipt,
            _canonical_json(recovered_receipt),
            "visible_recovery_receipt_exists",
        )
        metrics = {
            "evidenceMode": EVIDENCE_MODE,
            "operationId": operation_id,
            "eaFactoryStage": "backtest_recheck",
            "platform": "mt4",
            "terminalCandidateId": target["candidateId"],
            "terminalSelectionRevision": target["selectionRevision"],
            "terminalBindingDigest": target["bindingDigest"],
            "processBinding": process_binding,
            "processBindingDigest": process_binding["processBindingDigest"],
            "postProcessBinding": post_binding,
            "postProcessBindingDigest": post_binding["processBindingDigest"],
            "processId": process_binding["frontOfficeProcessId"],
            "windowHandle": process_binding["frontOfficeWindowHandle"],
            "liveTradingExecuted": False,
            "autoTradingToggled": False,
            "autoTradingStateBefore": ui["processBinding"]["autoTradingState"],
            "autoTradingStateAfter": ui["postProcessBinding"]["autoTradingState"],
            "chartAttached": False,
            "terminalClosedByAdapter": False,
            "terminalStillRunning": True,
            "terminalStillOpen": True,
            "sourceDigest": source_digest,
            "compiledBinaryArtifactAlias": "compiled_binary",
            "compiledBinarySha256": binary_digest,
            "expertFileName": binary.name,
            "expertUiPathDigest": _sha256_text(expert_ui_path),
            "actionRequestDigest": action_request_digest,
            "startBoundarySha256": start_boundary_digest,
            "resolvedTesterSettings": copy.deepcopy(resolved),
            "resolvedTesterSettingsDigest": resolved_digest,
            "settingsScreenshotArtifactAlias": "tester_settings",
            "settingsScreenshotSha256": settings_digest,
            "resultScreenshotArtifactAlias": "tester_result",
            "resultScreenshotSha256": result_digest,
            "visibleWindowEvidenceArtifactAlias": "tester_result",
            "visibleWindowEvidenceSha256": result_digest,
            "reportScreenshotArtifactAlias": "tester_report_proof",
            "reportScreenshotSha256": report_screenshot_digest,
            "testerReportArtifactAlias": "tester_report",
            "testerReportSha256": report_digest,
            "adapterReceiptArtifactAlias": "adapter_receipt",
            "visibleStrategyTester": True,
            "visualMode": True,
            "optimizationEnabled": False,
            "backtestVerified": True,
            "backtestExecuted": False,
            "recoveredExistingReceipt": True,
            "testerTradeRowsVerified": True,
            "fullDynamicSixGroupVerified": False,
            "zeroTrade": stored_counts["tradeCount"] == 0,
            **stored_attention,
            **stored_counts,
            "deploymentReusedExactBytes": True,
        }
        artifacts = [
            _artifact("tester_settings", settings_screenshot, workspace),
            _artifact("tester_result", result_screenshot, workspace),
            _artifact("tester_report_proof", report_screenshot, workspace),
            _artifact("tester_report", tester_report, workspace),
            _artifact(
                "adapter_receipt",
                recovery_receipt,
                workspace,
                artifact_kind="backtest_evidence",
            ),
        ]
        if resolved_preset is not None and input_preset_screenshot is not None:
            metrics.update({
                "testerInputPresetApplied": True,
                "testerInputPresetReadbackVerified": True,
                "testerInputPresetReportVerified": True,
                "testerInputPresetDigest": policy["testerInputPreset"]["presetDigest"],
                "resolvedTesterInputPreset": copy.deepcopy(resolved_preset),
                "resolvedTesterInputPresetDigest": resolved_preset_digest,
                "inputPresetScreenshotArtifactAlias": "tester_input_preset",
                "inputPresetScreenshotSha256": input_preset_digest,
                "inputPresetSetArtifactAlias": "tester_input_preset_set",
                "inputPresetSetSha256": input_preset_set_digest,
                "inputReadbackSetArtifactAlias": "tester_input_readback_set",
                "inputReadbackSetSha256": input_readback_set_digest,
                "simulationAssumptionsExplicit": True,
            })
            artifacts[1:1] = [
                _artifact("tester_input_preset", input_preset_screenshot, workspace),
                _artifact("tester_input_preset_set", input_preset_set, workspace),
                _artifact("tester_input_readback_set", input_readback_set, workspace),
            ]
        return {
            "schemaVersion": "ea-factory-visible-front-office-result-v1",
            "operationId": operation_id,
            "metrics": metrics,
            "artifactSpecifications": artifacts,
        }

    def backtest_handler(self, *, request: dict) -> dict:
        context = _validate_request(request, "backtest_recheck")
        target = self._target(request, context)
        preflight_probe = self._operation_probe(context, target)
        if not callable(self._backtest_verifier):
            raise VisibleTerminalAdapterError("backtest_verifier_not_connected")
        workspace = context["workspace"]
        source = context["source"]["path"]
        source_digest = context["source"]["digest"]
        binary = _resolved_file(
            source.with_suffix(".ex4"),
            "compiled_binary_missing",
            maximum_bytes=MAX_BINARY_BYTES,
        )
        policy = _validate_tester_policy(
            request.get("testerSettings"),
            binary.name,
            source=source,
            source_digest=source_digest,
        )
        operation_id = context["operation"]["operationId"]
        receipt_path = workspace / "Summaries" / f"{operation_id}-backtest-receipt.json"
        intent_path = workspace / "Summaries" / f"{operation_id}-backtest-intent.json"
        action_request_path = (
            workspace / "Summaries" / f"{operation_id}-backtest-action-request.json"
        )
        start_boundary_path = (
            workspace / "Summaries" / f"{operation_id}-backtest-start-boundary.json"
        )
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        if _path_has_reparse_component(receipt_path.parent):
            raise VisibleTerminalAdapterError("evidence_directory_unsafe")
        deploy_root = target["dataPath"] / "MQL4" / "Experts" / "Metafxclub" / "AgentHQ" / operation_id
        settings_screenshot = workspace / "Screenshots" / f"{operation_id}-tester-settings.png"
        input_preset_screenshot = (
            workspace / "Screenshots" / f"{operation_id}-tester-input-preset.png"
            if policy.get("testerInputPreset") is not None
            else None
        )
        input_preset_set = (
            workspace / "Sets" / f"{operation_id}-tester-input-preset.set"
            if policy.get("testerInputPreset") is not None
            else None
        )
        input_readback_set = (
            workspace / "Sets" / f"{operation_id}-tester-input-readback.set"
            if policy.get("testerInputPreset") is not None
            else None
        )
        result_screenshot = workspace / "Screenshots" / f"{operation_id}-tester-result.png"
        report_screenshot = workspace / "Screenshots" / f"{operation_id}-tester-report.png"
        tester_report = workspace / "Reports" / f"{operation_id}-tester.htm"
        response_path = workspace / "Summaries" / f"{operation_id}-backtest-ui.json"
        expert_ui_path = f"Metafxclub\\AgentHQ\\{operation_id}\\{binary.stem}"
        source_binary_digest, _ = _stable_digest(binary, maximum_bytes=MAX_BINARY_BYTES)
        expected_intent = _action_intent_payload(context, target)
        expected_action_request, action_request_digest = _backtest_action_request_payload(
            context,
            target,
            policy=policy,
            binary_digest=source_binary_digest,
            binary_name=binary.name,
            expert_ui_path=expert_ui_path,
        )
        expected_start_boundary = _tester_start_boundary_payload(
            operation_id,
            action_request_digest,
        )
        expected_start_boundary_bytes = _canonical_json(expected_start_boundary)
        expected_start_boundary_digest = _sha256_bytes(expected_start_boundary_bytes)
        if receipt_path.exists():
            _require_exact_action_intent(intent_path, expected_intent)
            _require_exact_json_object(
                action_request_path,
                expected_action_request,
                "backtest_action_request_mismatch",
            )
            _require_exact_json_object(
                start_boundary_path,
                expected_start_boundary,
                "tester_start_boundary_mismatch",
            )
            observed_start_boundary_digest, _ = _stable_digest(
                start_boundary_path,
                maximum_bytes=32 * 1024,
            )
            if not secrets.compare_digest(
                observed_start_boundary_digest,
                expected_start_boundary_digest,
            ):
                raise VisibleTerminalAdapterError("tester_start_boundary_mismatch")
            try:
                resolved_deploy_root = deploy_root.resolve(strict=True)
            except (OSError, RuntimeError, ValueError) as error:
                raise VisibleTerminalAdapterError("expert_recovery_deployment_missing") from error
            expected_experts_root = (target["dataPath"] / "MQL4" / "Experts").resolve(strict=True)
            if (
                _path_has_reparse_component(resolved_deploy_root)
                or not _is_relative_to(resolved_deploy_root, expected_experts_root)
            ):
                raise VisibleTerminalAdapterError("expert_deployment_path_unsafe")
            deployed = _resolved_file(
                resolved_deploy_root / binary.name,
                "expert_recovery_deployment_missing",
                maximum_bytes=MAX_BINARY_BYTES,
            )
            deployed_digest, _ = _stable_digest(deployed, maximum_bytes=MAX_BINARY_BYTES)
            if not secrets.compare_digest(deployed_digest, source_binary_digest):
                raise VisibleTerminalAdapterError("expert_recovery_deployment_mismatch")
            return self._recover_backtest(
                context=context,
                target=target,
                policy=policy,
                source_digest=source_digest,
                binary=binary,
                binary_digest=source_binary_digest,
                deployed=deployed,
                expert_ui_path=expert_ui_path,
                settings_screenshot=settings_screenshot,
                input_preset_screenshot=input_preset_screenshot,
                input_preset_set=input_preset_set,
                input_readback_set=input_readback_set,
                result_screenshot=result_screenshot,
                report_screenshot=report_screenshot,
                tester_report=tester_report,
                base_receipt_path=receipt_path,
                preflight_probe=preflight_probe,
                action_request_digest=action_request_digest,
                start_boundary_digest=expected_start_boundary_digest,
            )
        intent_reused_before_start = False
        action_request_reused_before_start = False
        recovering_inflight_backtest = False
        recovering_completed_backtest = False
        recovering_collected_backtest = False
        legacy_tester_report = (
            workspace / "Reports" / f"{operation_id}-tester.html"
        )
        pre_start_generated_paths = tuple(
            path
            for path in (
                settings_screenshot,
                input_preset_screenshot,
                input_readback_set,
            )
            if path is not None
        )
        if start_boundary_path.exists():
            _require_exact_action_intent(intent_path, expected_intent)
            _require_exact_json_object(
                action_request_path,
                expected_action_request,
                "backtest_action_request_mismatch",
            )
            _require_exact_json_object(
                start_boundary_path,
                expected_start_boundary,
                "tester_start_boundary_mismatch",
            )
            observed_boundary_digest, _ = _stable_digest(
                start_boundary_path,
                maximum_bytes=32 * 1024,
            )
            if not secrets.compare_digest(
                observed_boundary_digest,
                expected_start_boundary_digest,
            ):
                raise VisibleTerminalAdapterError("tester_start_boundary_mismatch")
            if legacy_tester_report.exists():
                raise VisibleTerminalAdapterError("visible_action_state_uncertain")
            if tester_report.exists():
                if result_screenshot.exists() and report_screenshot.exists():
                    recovering_collected_backtest = True
                else:
                    raise VisibleTerminalAdapterError("visible_action_state_uncertain")
            elif result_screenshot.exists():
                recovering_completed_backtest = True
            elif report_screenshot.exists():
                raise VisibleTerminalAdapterError("visible_action_state_uncertain")
            else:
                recovering_inflight_backtest = True
        elif (
            result_screenshot.exists()
            or report_screenshot.exists()
            or tester_report.exists()
            or legacy_tester_report.exists()
        ):
            raise VisibleTerminalAdapterError("visible_action_state_uncertain")
        recovering_existing_backtest = bool(
            recovering_inflight_backtest
            or recovering_completed_backtest
            or recovering_collected_backtest
        )
        if recovering_existing_backtest:
            # Recovery below can only observe an already-running Stop state and
            # collect the original operation after Stop -> Start, or validate a
            # completed result checkpoint and collect its missing report, or
            # validate a completed result/report pair already collected by the
            # original operation. All recovery modes forbid calling Start again.
            pass
        elif intent_path.exists():
            _require_exact_action_intent(intent_path, expected_intent)
            intent_reused_before_start = True
            if action_request_path.exists():
                _require_exact_json_object(
                    action_request_path,
                    expected_action_request,
                    "backtest_action_request_mismatch",
                )
                action_request_reused_before_start = True
            elif any(path.exists() for path in pre_start_generated_paths):
                # A legacy v1 intent has no crash-safe Start marker. Upgrade it
                # only when no legacy pre-Start boundary evidence was emitted.
                raise VisibleTerminalAdapterError("visible_action_state_uncertain")
        elif action_request_path.exists() or any(
            path.exists() for path in pre_start_generated_paths
        ):
            raise VisibleTerminalAdapterError("visible_action_state_uncertain")
        if action_request_reused_before_start and not recovering_existing_backtest:
            # Under the durable marker protocol these are all pre-Start
            # checkpoints. If no marker exists they can be recreated safely.
            for path in pre_start_generated_paths:
                if not path.exists():
                    continue
                try:
                    if _path_has_reparse_component(path) or not path.is_file():
                        raise VisibleTerminalAdapterError("prestart_artifact_unsafe")
                    path.unlink()
                except VisibleTerminalAdapterError:
                    raise
                except OSError as error:
                    raise VisibleTerminalAdapterError(
                        "prestart_artifact_cleanup_failed"
                    ) from error
        try:
            if recovering_existing_backtest:
                if not deploy_root.is_dir():
                    raise OSError("recovery deployment directory missing")
            else:
                deploy_root.mkdir(parents=True, exist_ok=True)
            resolved_deploy_root = deploy_root.resolve(strict=True)
        except (OSError, RuntimeError, ValueError) as error:
            raise VisibleTerminalAdapterError("expert_deployment_path_invalid") from error
        expected_experts_root = (target["dataPath"] / "MQL4" / "Experts").resolve(strict=True)
        if (
            _path_has_reparse_component(resolved_deploy_root)
            or not _is_relative_to(resolved_deploy_root, expected_experts_root)
        ):
            raise VisibleTerminalAdapterError("expert_deployment_path_unsafe")
        deployed = resolved_deploy_root / binary.name
        if recovering_existing_backtest and not deployed.is_file():
            raise VisibleTerminalAdapterError(
                "expert_recovery_deployment_missing"
            )
        binary_digest, _binary_size, reused_deployment = _copy_exclusive_or_verify(binary, deployed)
        for parent in {
            settings_screenshot.parent,
            result_screenshot.parent,
            report_screenshot.parent,
            tester_report.parent,
            response_path.parent,
            *(
                {input_preset_screenshot.parent}
                if input_preset_screenshot is not None
                else set()
            ),
            *(
                {input_preset_set.parent, input_readback_set.parent}
                if input_preset_set is not None and input_readback_set is not None
                else set()
            ),
        }:
            if recovering_existing_backtest:
                if not parent.is_dir():
                    raise VisibleTerminalAdapterError(
                        "tester_inflight_recovery_checkpoint_invalid"
                    )
            else:
                parent.mkdir(parents=True, exist_ok=True)
            if _path_has_reparse_component(parent):
                raise VisibleTerminalAdapterError("evidence_directory_unsafe")
        if input_preset_set is not None:
            preset_bytes = _tester_input_preset_set_bytes(policy["testerInputPreset"])
            if input_preset_set.exists():
                preset_digest, preset_size = _stable_digest(
                    input_preset_set,
                    maximum_bytes=MAX_SET_BYTES,
                )
                if (
                    preset_size != len(preset_bytes)
                    or not secrets.compare_digest(
                        preset_digest,
                        _sha256_bytes(preset_bytes),
                    )
                ):
                    raise VisibleTerminalAdapterError("tester_input_preset_set_collision")
            elif recovering_existing_backtest:
                raise VisibleTerminalAdapterError(
                    "tester_inflight_recovery_preset_invalid"
                )
            else:
                _write_exclusive(
                    input_preset_set,
                    preset_bytes,
                    "tester_input_preset_set_exists",
                )
        if recovering_existing_backtest:
            _validate_png(settings_screenshot)
            if recovering_completed_backtest or recovering_collected_backtest:
                _validate_png(result_screenshot)
                if report_screenshot.exists():
                    _validate_png(report_screenshot)
            if recovering_collected_backtest:
                _stable_digest(tester_report, maximum_bytes=MAX_EVIDENCE_BYTES)
            if input_preset_set is not None:
                if input_preset_screenshot is None or input_readback_set is None:
                    raise VisibleTerminalAdapterError(
                        "tester_inflight_recovery_preset_invalid"
                    )
                _validate_png(input_preset_screenshot)
                _resolved_tester_input_preset_from_set(
                    input_readback_set,
                    policy=policy,
                )
        payload = {
            "schemaVersion": "ea-factory-visible-powershell-request-v1",
            "action": (
                "recover_collected_backtest"
                if recovering_collected_backtest
                else (
                    "recover_completed_backtest"
                    if recovering_completed_backtest
                    else (
                        "recover_inflight_backtest"
                        if recovering_inflight_backtest
                        else "backtest"
                    )
                )
            ),
            "platform": "mt4",
            "operationId": operation_id,
            "terminalPath": str(target["terminalPath"]),
            "compilerPath": str(target["compilerPath"]),
            "dataPath": str(target["dataPath"]),
            "deployedExpertPath": str(deployed),
            "expectedDeployedExpertSha256": binary_digest,
            "expertFileName": binary.name,
            "expertUiPath": expert_ui_path,
            "testerSettings": policy,
            "settingsScreenshotPath": str(settings_screenshot),
            "inputPresetScreenshotPath": (
                str(input_preset_screenshot)
                if input_preset_screenshot is not None
                else None
            ),
            "inputPresetSetPath": (
                str(input_preset_set) if input_preset_set is not None else None
            ),
            "inputReadbackSetPath": (
                str(input_readback_set) if input_readback_set is not None else None
            ),
            "resultScreenshotPath": str(result_screenshot),
            "reportScreenshotPath": str(report_screenshot),
            "testerReportPath": str(tester_report),
            "startBoundaryPath": str(start_boundary_path),
            "startBoundaryJson": expected_start_boundary_bytes.decode("utf-8"),
            "startBoundarySha256": expected_start_boundary_digest,
            "actionRequestDigest": action_request_digest,
            "timeoutSeconds": DEFAULT_BACKTEST_TIMEOUT_SECONDS,
            "maxExpertSelectionSteps": 512,
            "expectedTerminalProcessId": preflight_probe["processId"],
            "expectedTerminalWindowHandle": preflight_probe["windowHandle"],
        }
        if not recovering_existing_backtest and not intent_reused_before_start:
            _write_exclusive(
                intent_path,
                _canonical_json(expected_intent),
                "visible_action_intent_exists",
            )
        if not recovering_existing_backtest and not action_request_reused_before_start:
            _write_exclusive(
                action_request_path,
                _canonical_json(expected_action_request),
                "backtest_action_request_exists",
            )
        ui_response_path = (
            response_path.with_name(response_path.stem + "-collected-recovery.json")
            if recovering_collected_backtest
            else (
                response_path.with_name(response_path.stem + "-completed-recovery.json")
                if recovering_completed_backtest
                else (
                    response_path.with_name(response_path.stem + "-inflight-recovery.json")
                    if recovering_inflight_backtest
                    else response_path
                )
            )
        )
        ui = self._powershell_runner(
            payload,
            response_path=ui_response_path,
            timeout_seconds=DEFAULT_BACKTEST_TIMEOUT_SECONDS,
        )
        selected_expert_readback = str(
            ui.get("selectedExpertReadback") if isinstance(ui, dict) else ""
        ).strip().replace("/", "\\").lstrip("\\").casefold()
        expected_expert_values = {
            expert_ui_path.replace("/", "\\").lstrip("\\").casefold(),
            (expert_ui_path + ".ex4").replace("/", "\\").lstrip("\\").casefold(),
        }
        if recovering_collected_backtest:
            execution_contract_valid = bool(
                isinstance(ui, dict)
                and ui.get("action") == "recover_collected_backtest"
                and ui.get("recoveredWithoutStart") is True
                and ui.get("startInvoked") is False
                and ui.get("executionObservedRunning") is False
                and ui.get("completedResultCheckpointReused") is True
                and ui.get("completedReportCheckpointReused") is True
                and ui.get("testerCompletionObservation")
                == "recovery_collected_checkpoint_observed"
                and ui.get("fastCompletionTesterLogAdvanced") is False
            )
        elif recovering_completed_backtest:
            execution_contract_valid = bool(
                isinstance(ui, dict)
                and ui.get("action") == "recover_completed_backtest"
                and ui.get("recoveredWithoutStart") is True
                and ui.get("startInvoked") is False
                and ui.get("executionObservedRunning") is False
                and ui.get("completedResultCheckpointReused") is True
                and ui.get("testerCompletionObservation")
                == "recovery_completed_checkpoint_observed"
                and ui.get("fastCompletionTesterLogAdvanced") is False
            )
        elif recovering_inflight_backtest:
            execution_contract_valid = bool(
                isinstance(ui, dict)
                and ui.get("action") == "recover_inflight_backtest"
                and ui.get("recoveredWithoutStart") is True
                and ui.get("startInvoked") is False
                and ui.get("executionObservedRunning") is True
                and ui.get("testerCompletionObservation")
                == "recovery_stop_transition_observed"
                and ui.get("fastCompletionTesterLogAdvanced") is False
            )
        else:
            execution_contract_valid = bool(
                isinstance(ui, dict)
                and ui.get("action") == "backtest"
                and ui.get("startInvoked") is True
                and ui.get("testerCompletionObservation")
                in {"stop_transition_observed", "fast_idle_evidence_required"}
                and isinstance(ui.get("fastCompletionTesterLogAdvanced"), bool)
                and (
                    ui.get("testerCompletionObservation")
                    != "fast_idle_evidence_required"
                    or ui.get("fastCompletionTesterLogAdvanced") is True
                )
                and isinstance(ui.get("visualSpeedBefore"), int)
                and not isinstance(ui.get("visualSpeedBefore"), bool)
                and isinstance(ui.get("visualSpeedAfter"), int)
                and not isinstance(ui.get("visualSpeedAfter"), bool)
                and isinstance(ui.get("visualSpeedMaximum"), int)
                and not isinstance(ui.get("visualSpeedMaximum"), bool)
                and 0 <= ui.get("visualSpeedBefore") <= ui.get("visualSpeedMaximum") <= 100
                and ui.get("visualSpeedAfter") == ui.get("visualSpeedMaximum")
            )
        if (
            not isinstance(ui, dict)
            or ui.get("schemaVersion") != POWERSHELL_RESULT_SCHEMA
            or not execution_contract_valid
            or ui.get("operationId") != operation_id
            or ui.get("testerCompleted") is not True
            or ui.get("freshResultEvidenceCaptured") is not True
            or ui.get("exactExpertVerified") is not True
            or selected_expert_readback not in expected_expert_values
            or selected_expert_readback == binary.name.casefold()
            or ui.get("deployedExpertSha256") != binary_digest
            or ui.get("startBoundaryCommitted") is not True
            or ui.get("startBoundarySha256") != expected_start_boundary_digest
            or ui.get("actionRequestDigest") != action_request_digest
        ):
            raise VisibleTerminalAdapterError("visible_backtest_result_invalid")
        _require_exact_json_object(
            start_boundary_path,
            expected_start_boundary,
            "tester_start_boundary_mismatch",
        )
        observed_start_boundary_digest, _ = _stable_digest(
            start_boundary_path,
            maximum_bytes=32 * 1024,
        )
        if not secrets.compare_digest(
            observed_start_boundary_digest,
            expected_start_boundary_digest,
        ):
            raise VisibleTerminalAdapterError("tester_start_boundary_mismatch")
        resolved_preset = _resolved_tester_input_preset_from_set(
            input_readback_set,
            policy=policy,
        ) if input_readback_set is not None else None
        if (
            resolved_preset is not None
            and (
                ui.get("testerInputPresetApplied") is not True
                or ui.get("testerInputPresetReadbackVerified") is not True
                or ui.get("inputPresetReadbackSaved") is not True
            )
        ) or (
            resolved_preset is None
            and (
                ui.get("testerInputPresetApplied") not in {None, False}
                or ui.get("testerInputPresetReadbackVerified") not in {None, False}
                or ui.get("inputPresetReadbackSaved") not in {None, False}
            )
        ):
            raise VisibleTerminalAdapterError("tester_input_preset_execution_invalid")
        process_binding, post_binding = _binding_pair(
            ui,
            target=target,
            stage_id="backtest_recheck",
            maximum_operation_seconds=DEFAULT_BACKTEST_TIMEOUT_SECONDS,
        )
        _assert_preflight_continuity(process_binding, preflight_probe)
        resolved = ui.get("resolvedTesterSettings")
        expected_resolved_keys = {
            "schemaVersion",
            "expertFileName",
            "symbol",
            "period",
            "model",
            "spread",
            "useDate",
            "fromDate",
            "toDate",
            "deposit",
            "visualMode",
            "optimizationEnabled",
            "shutdownTerminalAfterTest",
        }
        if (
            not isinstance(resolved, dict)
            or set(resolved) != expected_resolved_keys
            or resolved.get("schemaVersion") != RESOLVED_TESTER_SCHEMA
            or resolved.get("expertFileName") != binary.name
            or SAFE_SYMBOL.fullmatch(str(resolved.get("symbol") or "")) is None
            or resolved.get("period") != policy["period"]
            or resolved.get("model") != policy["model"]
            or not str(resolved.get("spread") or "").strip()
            or resolved.get("useDate") is not False
            or resolved.get("fromDate") is not None
            or resolved.get("toDate") is not None
            or resolved.get("visualMode") is not True
            or resolved.get("optimizationEnabled") is not False
            or resolved.get("shutdownTerminalAfterTest") is not False
        ):
            raise VisibleTerminalAdapterError("tester_settings_readback_invalid")
        settings_digest, _ = _validate_png(settings_screenshot)
        input_preset_screenshot_digest = (
            _validate_png(input_preset_screenshot)[0]
            if input_preset_screenshot is not None
            else None
        )
        if input_preset_set is not None and input_preset_set.read_bytes() != (
            _tester_input_preset_set_bytes(policy["testerInputPreset"])
        ):
            raise VisibleTerminalAdapterError("tester_input_preset_set_mismatch")
        input_preset_set_digest = (
            _stable_digest(input_preset_set, maximum_bytes=MAX_SET_BYTES)[0]
            if input_preset_set is not None
            else None
        )
        input_readback_set_digest = (
            _stable_digest(input_readback_set, maximum_bytes=MAX_SET_BYTES)[0]
            if input_readback_set is not None
            else None
        )
        result_digest, _ = _validate_png(result_screenshot)
        report_screenshot_digest, _ = _validate_png(report_screenshot)
        report_digest, _ = _stable_digest(tester_report, maximum_bytes=MAX_EVIDENCE_BYTES)
        verifier_context = {
            "platform": "mt4",
            "operationId": operation_id,
            "sourceDigest": source_digest,
            "compiledDigest": binary_digest,
            "deployedExpertPath": deployed,
            "resolvedTesterSettings": copy.deepcopy(resolved),
            "testerReportPath": tester_report,
            "settingsScreenshotPath": settings_screenshot,
            "inputPresetScreenshotPath": input_preset_screenshot,
            "resultScreenshotPath": result_screenshot,
            "testerInputPreset": copy.deepcopy(policy.get("testerInputPreset")),
            "visibleUiResult": copy.deepcopy(ui),
        }
        try:
            verified = self._backtest_verifier(verifier_context)
        except VisibleTerminalAdapterError:
            raise
        except Exception as error:
            raise VisibleTerminalAdapterError("backtest_verifier_failed") from error
        if not isinstance(verified, dict):
            raise VisibleTerminalAdapterError("backtest_verifier_result_invalid")
        trade_count = verified.get("tradeCount")
        trade_row_count = verified.get("tradeRowCount")
        buy_count = verified.get("buyTradeCount")
        sell_count = verified.get("sellTradeCount")
        mismatched_chart_errors = verified.get("mismatchedChartErrors")
        expected_attention = (
            _backtest_attention_fields(trade_count == 0, mismatched_chart_errors)
            if isinstance(trade_count, int)
            and not isinstance(trade_count, bool)
            and isinstance(mismatched_chart_errors, int)
            and not isinstance(mismatched_chart_errors, bool)
            and mismatched_chart_errors >= 0
            else None
        )
        if (
            verified.get("backtestVerified") is not True
            or verified.get("testerTradeRowsVerified") is not True
            or isinstance(trade_count, bool)
            or not isinstance(trade_count, int)
            or trade_count < 0
            or isinstance(trade_row_count, bool)
            or not isinstance(trade_row_count, int)
            or trade_row_count < 0
            or isinstance(buy_count, bool)
            or not isinstance(buy_count, int)
            or buy_count < 0
            or isinstance(sell_count, bool)
            or not isinstance(sell_count, int)
            or sell_count < 0
            or buy_count + sell_count != trade_count
            or trade_row_count != trade_count
            or verified.get("zeroTrade") is not (trade_count == 0)
            or expected_attention is None
            or any(
                verified.get(key) != value
                for key, value in expected_attention.items()
            )
            or verified.get("testerInputPresetReportVerified")
            != (resolved_preset is not None)
        ):
            raise VisibleTerminalAdapterError("tester_trade_rows_unverified")
        zero_trade = trade_count == 0
        resolved = _normalize_resolved_tester_settings(
            resolved,
            binary_name=binary.name,
            policy=policy,
            verified_deposit=verified.get("deposit"),
            verified_spread=verified.get("spread"),
        )
        resolved_digest = _bridge_payload_digest(
            "ea-factory-resolved-tester-settings-v1",
            resolved,
        )
        resolved_preset_digest = (
            _bridge_payload_digest(
                RESOLVED_TESTER_INPUT_PRESET_SCHEMA,
                resolved_preset,
            )
            if resolved_preset is not None
            else None
        )
        receipt = {
            "schemaVersion": RECEIPT_SCHEMA,
            "operationId": operation_id,
            "stageId": "backtest_recheck",
            "terminalCandidateId": target["candidateId"],
            "status": "verified",
            "processBindingDigest": process_binding["processBindingDigest"],
            "postProcessBindingDigest": post_binding["processBindingDigest"],
            "sourceDigest": source_digest,
            "compiledBinarySha256": binary_digest,
            "testerSettingsSha256": settings_digest,
            "testerInputPresetScreenshotSha256": input_preset_screenshot_digest,
            "testerInputPresetSetSha256": input_preset_set_digest,
            "testerInputReadbackSetSha256": input_readback_set_digest,
            "testerInputPresetDigest": (
                policy["testerInputPreset"]["presetDigest"]
                if resolved_preset is not None
                else None
            ),
            "testerResultSha256": result_digest,
            "testerReportScreenshotSha256": report_screenshot_digest,
            "testerReportSha256": report_digest,
            "resolvedTesterSettingsDigest": resolved_digest,
            "resolvedTesterSettings": copy.deepcopy(resolved),
            "resolvedTesterInputPreset": copy.deepcopy(resolved_preset),
            "resolvedTesterInputPresetDigest": resolved_preset_digest,
            "testerInputPresetReportVerified": resolved_preset is not None,
            "expertUiPathDigest": _sha256_text(expert_ui_path),
            "actionRequestDigest": action_request_digest,
            "startBoundarySha256": expected_start_boundary_digest,
            "tradeCount": trade_count,
            "tradeRowCount": trade_row_count,
            "buyTradeCount": buy_count,
            "sellTradeCount": sell_count,
            "zeroTrade": zero_trade,
            **expected_attention,
            "visualMode": True,
            "optimizationEnabled": False,
            "shutdownTerminalAfterTest": False,
            "liveTradingExecuted": False,
            "recoveredInflightBacktest": recovering_inflight_backtest,
            "recoveredCompletedBacktest": recovering_completed_backtest,
            "recoveredCollectedBacktest": recovering_collected_backtest,
            "completedReportCheckpointReused": recovering_collected_backtest,
            "recoveryIssuedStart": False,
        }
        _write_exclusive(
            receipt_path,
            _canonical_json(receipt),
            "visible_receipt_already_exists",
        )
        metrics = {
            "evidenceMode": EVIDENCE_MODE,
            "operationId": operation_id,
            "eaFactoryStage": "backtest_recheck",
            "platform": "mt4",
            "terminalCandidateId": target["candidateId"],
            "terminalSelectionRevision": target["selectionRevision"],
            "terminalBindingDigest": target["bindingDigest"],
            "processBinding": process_binding,
            "processBindingDigest": process_binding["processBindingDigest"],
            "postProcessBinding": post_binding,
            "postProcessBindingDigest": post_binding["processBindingDigest"],
            "processId": process_binding["frontOfficeProcessId"],
            "windowHandle": process_binding["frontOfficeWindowHandle"],
            "liveTradingExecuted": False,
            "autoTradingToggled": False,
            "autoTradingStateBefore": ui["processBinding"]["autoTradingState"],
            "autoTradingStateAfter": ui["postProcessBinding"]["autoTradingState"],
            "chartAttached": False,
            "terminalClosedByAdapter": False,
            "terminalStillRunning": True,
            "terminalStillOpen": True,
            "sourceDigest": source_digest,
            "compiledBinaryArtifactAlias": "compiled_binary",
            "compiledBinarySha256": binary_digest,
            "expertFileName": binary.name,
            "expertUiPathDigest": _sha256_text(expert_ui_path),
            "actionRequestDigest": action_request_digest,
            "startBoundarySha256": expected_start_boundary_digest,
            "resolvedTesterSettings": copy.deepcopy(resolved),
            "resolvedTesterSettingsDigest": resolved_digest,
            "settingsScreenshotArtifactAlias": "tester_settings",
            "settingsScreenshotSha256": settings_digest,
            "resultScreenshotArtifactAlias": "tester_result",
            "resultScreenshotSha256": result_digest,
            "visibleWindowEvidenceArtifactAlias": "tester_result",
            "visibleWindowEvidenceSha256": result_digest,
            "reportScreenshotArtifactAlias": "tester_report_proof",
            "reportScreenshotSha256": report_screenshot_digest,
            "testerReportArtifactAlias": "tester_report",
            "testerReportSha256": report_digest,
            "adapterReceiptArtifactAlias": "adapter_receipt",
            "visibleStrategyTester": True,
            "visualMode": True,
            "optimizationEnabled": False,
            "backtestVerified": True,
            "backtestExecuted": True,
            "testerCompletionObservation": ui["testerCompletionObservation"],
            "fastCompletionFallbackUsed": (
                ui["testerCompletionObservation"] == "fast_idle_evidence_required"
            ),
            "recoveredExistingReceipt": False,
            "recoveredInflightBacktest": recovering_inflight_backtest,
            "recoveredCompletedBacktest": recovering_completed_backtest,
            "recoveredCollectedBacktest": recovering_collected_backtest,
            "completedReportCheckpointReused": recovering_collected_backtest,
            "recoveryIssuedStart": False,
            "reusedPreStartIntent": intent_reused_before_start,
            "testerTradeRowsVerified": True,
            "fullDynamicSixGroupVerified": False,
            "zeroTrade": zero_trade,
            **expected_attention,
            "tradeCount": trade_count,
            "tradeRowCount": trade_row_count,
            "buyTradeCount": buy_count,
            "sellTradeCount": sell_count,
            "deploymentReusedExactBytes": reused_deployment,
        }
        artifacts = [
            _artifact("tester_settings", settings_screenshot, workspace),
            _artifact("tester_result", result_screenshot, workspace),
            _artifact("tester_report_proof", report_screenshot, workspace),
            _artifact("tester_report", tester_report, workspace),
            _artifact(
                "adapter_receipt",
                receipt_path,
                workspace,
                artifact_kind="backtest_evidence",
            ),
        ]
        if resolved_preset is not None and input_preset_screenshot is not None:
            metrics.update({
                "testerInputPresetApplied": True,
                "testerInputPresetReadbackVerified": True,
                "testerInputPresetReportVerified": True,
                "testerInputPresetDigest": policy["testerInputPreset"]["presetDigest"],
                "resolvedTesterInputPreset": copy.deepcopy(resolved_preset),
                "resolvedTesterInputPresetDigest": resolved_preset_digest,
                "inputPresetScreenshotArtifactAlias": "tester_input_preset",
                "inputPresetScreenshotSha256": input_preset_screenshot_digest,
                "inputPresetSetArtifactAlias": "tester_input_preset_set",
                "inputPresetSetSha256": input_preset_set_digest,
                "inputReadbackSetArtifactAlias": "tester_input_readback_set",
                "inputReadbackSetSha256": input_readback_set_digest,
                "simulationAssumptionsExplicit": True,
            })
            artifacts[1:1] = [
                _artifact("tester_input_preset", input_preset_screenshot, workspace),
                _artifact("tester_input_preset_set", input_preset_set, workspace),
                _artifact("tester_input_readback_set", input_readback_set, workspace),
            ]
        return {
            "schemaVersion": "ea-factory-visible-front-office-result-v1",
            "operationId": operation_id,
            "metrics": metrics,
            "artifactSpecifications": artifacts,
        }


def create_visible_front_office_adapter(
    *,
    target_resolver: Callable[..., dict],
    compile_verifier: Callable[[dict], dict] | None,
    backtest_verifier: Callable[[dict], dict] | None = None,
    powershell_runner: Callable[..., dict] | None = None,
) -> VisibleFrontOfficeAdapter:
    return VisibleFrontOfficeAdapter(
        target_resolver=target_resolver,
        compile_verifier=compile_verifier,
        backtest_verifier=backtest_verifier,
        powershell_runner=powershell_runner,
    )


def create_production_visible_front_office_adapter(
    *,
    target_resolver: Callable[..., dict],
    powershell_runner: Callable[..., dict] | None = None,
) -> VisibleFrontOfficeAdapter:
    """Create the MT4 adapter with read-only post-action verifiers."""

    return create_visible_front_office_adapter(
        target_resolver=target_resolver,
        compile_verifier=verify_visible_metaeditor_compile,
        backtest_verifier=verify_mt4_tester_report,
        powershell_runner=powershell_runner,
    )


__all__ = [
    "VisibleFrontOfficeAdapter",
    "VisibleTerminalAdapterError",
    "create_production_visible_front_office_adapter",
    "create_visible_front_office_adapter",
    "verify_mt4_tester_report",
    "verify_visible_metaeditor_compile",
]
