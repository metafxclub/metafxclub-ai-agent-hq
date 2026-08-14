#!/usr/bin/env python3
"""Recover one source-backed Radar result after a validator-only rejection.

This is deliberately not a retry path.  It never starts Codex, Web Search,
MetaTrader, or a Sheet adapter.  The default mode is read-only.  ``--apply``
requires compare-and-swap hashes copied from a preceding dry run and refuses
to run while the local Bridge control file is present.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
import tempfile
from contextlib import contextmanager, nullcontext
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Callable, Iterator, Mapping


RECOVERY_SCHEMA = "radar-contract-result-recovery-v1"
VALIDATOR_VERSION = "radar-contract-enum-alias-revalidation-v1"
EXPECTED_FAILURE = "radar_output_contract_invalid"
EXPECTED_PHASE = "auto_guarded_radar_output_contract_invalid"
EXPECTED_PROP_ID = "left_audit_crystals"
EXPECTED_ACTION_ID = "discover_new_indicators"
EXPECTED_PROCEDURE_ID = "backend-readonly-indicator-scout"
EXPECTED_REPORT_TYPE = "indicator_scout_report"
EXPECTED_TOOL_ID = "codex_web_research"
EXPECTED_POLICY_VERSION = "backend-auto-safe-v1"
EXPECTED_RESULT_PROFILE = "radar_website_tool"
AUDIT_SEGMENT_MAX_BYTES = 5 * 1024 * 1024
SHA256_RE = re.compile(r"[0-9a-f]{64}")
SAFE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")

RESERVATION_KEYS = (
    "lastAttemptAt",
    "lastAttemptSlotKey",
    "lastRunAt",
    "lastMissionId",
    "lastSnapshotId",
    "lastSlotKey",
    "lastIdempotentReplay",
    "pendingSlotKey",
    "pendingScheduledAt",
    "dailyExecutionDate",
    "dailyExecutionCount",
    "dailyExecutionSlotKeys",
    "dailyExecutionLastReservedAt",
)
MUTABLE_HASH_NAMES = ("missions", "report", "settings", "audit")
ARTIFACT_HASH_NAMES = ("stdout", "final")
ALL_HASH_NAMES = MUTABLE_HASH_NAMES + ARTIFACT_HASH_NAMES


class RecoveryError(RuntimeError):
    """A fail-closed recovery precondition was not satisfied."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")


def load_python_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RecoveryError(f"cannot_load_module:{path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_runtime_modules(project_root: Path) -> tuple[ModuleType, ModuleType]:
    bridge_path = project_root / "backend" / "local-runner" / "bridge_server.py"
    runner_path = project_root / "runner" / "codex_cli_runner.py"
    if not bridge_path.is_file() or not runner_path.is_file():
        raise RecoveryError("runtime_modules_missing")
    nonce = hashlib.sha256(str(project_root).encode("utf-8")).hexdigest()[:12]
    bridge = load_python_module(f"radar_recovery_bridge_{nonce}", bridge_path)
    runner = load_python_module(f"radar_recovery_runner_{nonce}", runner_path)
    return bridge, runner


def _read_bytes(path: Path, *, allow_missing: bool = False) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        if allow_missing:
            return b""
        raise RecoveryError(f"required_file_missing:{path.name}") from None
    except OSError as error:
        raise RecoveryError(f"cannot_read:{path.name}:{error.__class__.__name__}") from error


def _decode_json(raw: bytes, label: str) -> object:
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise RecoveryError(f"invalid_json:{label}") from error


def _assert_plain_regular_file(path: Path, root: Path, label: str) -> Path:
    root = root.resolve(strict=True)
    candidate = path if path.is_absolute() else root / path
    try:
        relative = candidate.relative_to(root)
    except ValueError as error:
        raise RecoveryError(f"path_outside_project:{label}") from error
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        try:
            if cursor.is_symlink():
                raise RecoveryError(f"symlink_not_allowed:{label}")
        except OSError as error:
            raise RecoveryError(f"cannot_inspect_path:{label}") from error
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
        mode = resolved.stat().st_mode
    except (FileNotFoundError, OSError, ValueError) as error:
        raise RecoveryError(f"invalid_file_path:{label}") from error
    if not stat.S_ISREG(mode):
        raise RecoveryError(f"not_regular_file:{label}")
    return resolved


def _ensure_local_directory(path: Path, root: Path, label: str) -> Path:
    root = root.resolve(strict=True)
    candidate = path if path.is_absolute() else root / path
    try:
        relative = candidate.relative_to(root)
    except ValueError as error:
        raise RecoveryError(f"directory_outside_project:{label}") from error
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise RecoveryError(f"directory_symlink_not_allowed:{label}")
    candidate.mkdir(parents=True, exist_ok=True)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as error:
        raise RecoveryError(f"invalid_directory:{label}") from error
    if not resolved.is_dir():
        raise RecoveryError(f"not_directory:{label}")
    return resolved


def _resolve_artifacts(project_root: Path, mission: Mapping[str, object]) -> tuple[Path, Path, str]:
    artifact_ref = str(mission.get("artifactPath") or "").strip().replace("\\", "/")
    if not artifact_ref or artifact_ref.startswith("/") or re.match(r"^[A-Za-z]:", artifact_ref):
        raise RecoveryError("invalid_final_artifact_reference")
    if not artifact_ref.startswith("data/runtime/codex-runs/"):
        raise RecoveryError("final_artifact_outside_codex_runs")
    relative = Path(*artifact_ref.split("/"))
    final_path = _assert_plain_regular_file(relative, project_root, "final_artifact")
    codex_runs = (project_root / "data" / "runtime" / "codex-runs").resolve(strict=True)
    try:
        final_path.relative_to(codex_runs)
    except ValueError as error:
        raise RecoveryError("final_artifact_outside_codex_runs") from error
    if not final_path.name.endswith(".final.md"):
        raise RecoveryError("unexpected_final_artifact_name")
    stdout_name = final_path.name[: -len(".final.md")] + ".stdout.log"
    stdout_path = _assert_plain_regular_file(
        final_path.with_name(stdout_name), project_root, "stdout_artifact"
    )
    try:
        stdout_path.relative_to(codex_runs)
    except ValueError as error:
        raise RecoveryError("stdout_artifact_outside_codex_runs") from error
    return final_path, stdout_path, artifact_ref


def _strict_jsonl_result(stdout_bytes: bytes) -> tuple[str, dict[str, object]]:
    try:
        stdout_text = stdout_bytes.decode("utf-8")
    except UnicodeError as error:
        raise RecoveryError("stdout_not_utf8") from error
    events: list[dict[str, object]] = []
    for index, raw_line in enumerate(stdout_text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError as error:
            raise RecoveryError(f"stdout_invalid_jsonl_line:{index}") from error
        if not isinstance(event, dict) or not str(event.get("type") or "").strip():
            raise RecoveryError(f"stdout_invalid_event:{index}")
        events.append(event)
    if not events or events[-1].get("type") != "turn.completed":
        raise RecoveryError("stdout_missing_terminal_turn_completed")
    if sum(event.get("type") == "turn.completed" for event in events) != 1:
        raise RecoveryError("stdout_turn_completed_count_invalid")
    completed_web_search = False
    last_agent_message: str | None = None
    for event in events:
        if event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, dict):
            raise RecoveryError("stdout_completed_item_invalid")
        if (
            item.get("type") == "web_search"
            and str(item.get("id") or "").strip()
            and str(item.get("query") or "").strip()
        ):
            completed_web_search = True
        if item.get("type") == "agent_message":
            text = item.get("text")
            if not isinstance(text, str) or not text.strip():
                raise RecoveryError("stdout_agent_message_invalid")
            last_agent_message = text
    if not completed_web_search:
        raise RecoveryError("stdout_native_completed_web_search_missing")
    if last_agent_message is None:
        raise RecoveryError("stdout_completed_agent_message_missing")
    terminal_event = events[-1]
    return last_agent_message, terminal_event


def _require_mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise RecoveryError(f"invalid_mapping:{label}")
    return value


def _validate_exact_prestate(
    mission: dict[str, object],
    report: dict[str, object],
    settings: dict[str, object],
    artifact_ref: str,
) -> tuple[dict[str, object], str]:
    if mission.get("status") != "blocked":
        raise RecoveryError("mission_not_blocked")
    if mission.get("phase") != EXPECTED_PHASE:
        raise RecoveryError("mission_phase_mismatch")
    if mission.get("errorCode") != EXPECTED_FAILURE or mission.get("workStatus") != EXPECTED_FAILURE:
        raise RecoveryError("mission_failure_mismatch")
    if mission.get("toolId") != EXPECTED_TOOL_ID:
        raise RecoveryError("mission_tool_mismatch")
    if not (
        mission.get("owner") == "codex_mcp_operator"
        and mission.get("targetId") == EXPECTED_PROP_ID
        and mission.get("reportType") == EXPECTED_REPORT_TYPE
    ):
        raise RecoveryError("mission_radar_binding_mismatch")
    if mission.get("webSearchUsed") is not True or mission.get("webSearchEvidenceVerified") is not True:
        raise RecoveryError("mission_web_search_evidence_unverified")

    approval = _require_mapping(mission.get("approval"), "approval")
    if not (
        approval.get("required") is False
        and approval.get("state") == "not_required"
        and approval.get("gateMode") == "not_required"
    ):
        raise RecoveryError("mission_approval_not_auto_safe")
    execution = _require_mapping(mission.get("execution"), "execution")
    if not (
        execution.get("schema") == "auto-guarded-execution-v1"
        and execution.get("authorizationSource") == "backend_auto_policy"
        and execution.get("authorizationDecision") == "allowed"
        and execution.get("authorizationPolicyVersion") == EXPECTED_POLICY_VERSION
        and execution.get("authorizationReason") == "routine_internal_or_read_only"
        and execution.get("dispatchState") == "blocked"
        and execution.get("processStarted") is True
        and execution.get("webSearchEnabled") is True
        and execution.get("webSearchMode") == "live"
        and execution.get("webSearchUsed") is True
        and execution.get("webSearchEvidenceVerified") is True
        and execution.get("controlPlaneWritable") is False
        and execution.get("writeRoots") == []
        and execution.get("automaticRetry") is False
    ):
        raise RecoveryError("mission_execution_not_exact_auto_safe_web_search")

    context = _require_mapping(mission.get("workflowContext"), "workflowContext")
    if context.get("propId") != EXPECTED_PROP_ID or context.get("actionId") != EXPECTED_ACTION_ID:
        raise RecoveryError("mission_radar_action_mismatch")
    procedure = _require_mapping(context.get("pluginProcedure"), "pluginProcedure")
    if not (
        procedure.get("pluginSkillId") == EXPECTED_PROCEDURE_ID
        and procedure.get("procedureKind") == "backend_procedure"
        and procedure.get("pluginInvocationMode") == "backend_owned_procedure"
        and procedure.get("automationMode") == "scheduled_read_only"
    ):
        raise RecoveryError("mission_radar_procedure_mismatch")
    reservation = _require_mapping(context.get("executionReservation"), "executionReservation")
    slot_key = str(reservation.get("slotKey") or "")
    if not (
        reservation.get("settingsKey") == "indicatorScoutSchedule"
        and reservation.get("maximumRunsPerDay") == 1
        and slot_key.startswith("indicatorScoutSchedule:")
    ):
        raise RecoveryError("mission_reservation_mismatch")

    report_ids = mission.get("reportIds")
    if not isinstance(report_ids, list) or len(report_ids) != 1 or report_ids[0] != report.get("id"):
        raise RecoveryError("mission_report_binding_mismatch")
    if not (
        report.get("linkedMissionId") == mission.get("id")
        and report.get("linkedPropId") == EXPECTED_PROP_ID
        and report.get("ownerAgentId") == mission.get("owner")
        and report.get("type") == EXPECTED_REPORT_TYPE
        and report.get("status") == "blocked"
        and report.get("artifacts") == [artifact_ref]
    ):
        raise RecoveryError("blocked_report_prestate_mismatch")
    report_context = _require_mapping(report.get("workflowContext"), "report.workflowContext")
    if report_context != context:
        raise RecoveryError("blocked_report_workflow_context_mismatch")
    metrics = _require_mapping(report.get("metrics"), "report.metrics")
    old_receipt = _require_mapping(metrics.get("workflowOutput"), "report.workflowOutput")
    mission_receipt = _require_mapping(
        mission.get("workflowOutputContract"), "mission.workflowOutputContract"
    )
    if not (
        old_receipt.get("valid") is False
        and old_receipt.get("failureCode") == EXPECTED_FAILURE
        and mission_receipt.get("valid") is False
        and mission_receipt.get("failureCode") == EXPECTED_FAILURE
        and mission_receipt == old_receipt
        and report.get("risks") == [EXPECTED_FAILURE]
    ):
        raise RecoveryError("blocked_report_reason_mismatch")

    schedule = _require_mapping(settings.get("indicatorScoutSchedule"), "indicatorScoutSchedule")
    slot_keys = schedule.get("dailyExecutionSlotKeys")
    if not (
        schedule.get("lastMissionId") == mission.get("id")
        and schedule.get("lastRunStatus") == "blocked"
        and schedule.get("lastError") == EXPECTED_FAILURE
        and schedule.get("lastSlotKey") == slot_key
        and schedule.get("lastAttemptSlotKey") == slot_key
        and schedule.get("dailyExecutionDate") == reservation.get("bangkokDate")
        and schedule.get("dailyExecutionCount") == 1
        and slot_keys == [slot_key]
        and schedule.get("pendingSlotKey") is None
    ):
        raise RecoveryError("daily_reservation_prestate_mismatch")
    return schedule, slot_key


def _normalization_allowlist(bridge: ModuleType) -> dict[str, dict[str, str]]:
    return {
        "platform": dict(getattr(bridge, "RADAR_PLATFORM_ALIASES", {})),
        "verificationStatus": dict(
            getattr(bridge, "RADAR_VERIFICATION_STATUS_ALIASES", {})
        ),
        "availability": dict(getattr(bridge, "RADAR_AVAILABILITY_STATUS_ALIASES", {})),
    }


def _validate_normalizations(receipt: dict[str, object], bridge: ModuleType) -> list[dict[str, object]]:
    rows = receipt.get("enumNormalizations")
    if not isinstance(rows, list) or not rows:
        raise RecoveryError("canonical_alias_normalizations_required")
    allowed = _normalization_allowlist(bridge)
    normalized_rows: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"entryIndex", "field", "from", "to"}:
            raise RecoveryError("normalization_receipt_shape_invalid")
        field = str(row.get("field") or "")
        source = str(row.get("from") or "")
        target = str(row.get("to") or "")
        index = row.get("entryIndex")
        if (
            not isinstance(index, int)
            or isinstance(index, bool)
            or index < 1
            or field not in allowed
            or allowed[field].get(source) != target
        ):
            raise RecoveryError("normalization_receipt_not_allowlisted")
        normalized_rows.append(copy.deepcopy(row))
    return normalized_rows


def _validate_backend_contract_excluding_bound_report(
    bridge: ModuleType,
    mission: dict[str, object],
    parsed: dict[str, object],
    report: dict[str, object],
) -> dict[str, object]:
    """Run the production validator without counting its own bound report.

    A committed Radar report is part of the global duplicate catalog.  On an
    idempotent revalidation it must not classify itself as a newly discovered
    duplicate.  Other reports remain in the catalog and the production
    validator itself is still the authority for every contract field.
    """

    reports_reader = getattr(bridge, "load_runtime_reports", None)
    report_reader = getattr(bridge, "_radar_report_entries", None)
    prop_matcher = getattr(bridge, "_workflow_record_matches_prop", None)
    validator = getattr(bridge, "validate_dashboard_workflow_output_contract", None)
    if not (
        callable(reports_reader)
        and callable(report_reader)
        and callable(prop_matcher)
        and callable(validator)
    ):
        raise RecoveryError("backend_radar_validator_unavailable")
    existing: set[str] = set()
    bound_report_id = str(report.get("id") or "")
    for candidate in reports_reader(limit=2000):
        if (
            not isinstance(candidate, dict)
            or str(candidate.get("id") or "") == bound_report_id
            or candidate.get("type") != EXPECTED_REPORT_TYPE
            or not prop_matcher(candidate, EXPECTED_PROP_ID)
        ):
            continue
        for row in report_reader(candidate):
            fingerprint = str(row.get("duplicateFingerprint") or "").strip().lower()
            if re.fullmatch(r"[0-9a-f]{24}", fingerprint):
                existing.add(fingerprint)
    original = bridge._radar_existing_catalog_fingerprints
    bridge._radar_existing_catalog_fingerprints = lambda: set(existing)
    try:
        result = validator(mission, parsed)
    finally:
        bridge._radar_existing_catalog_fingerprints = original
    if not isinstance(result, dict):
        raise RecoveryError("backend_radar_validator_result_invalid")
    return result


def _reservation_projection(schedule: Mapping[str, object]) -> dict[str, object]:
    return {key: copy.deepcopy(schedule.get(key)) for key in RESERVATION_KEYS}


def _report_path(project_root: Path, report_id: object) -> Path:
    value = str(report_id or "").strip()
    if not SAFE_ID_RE.fullmatch(value):
        raise RecoveryError("unsafe_report_id")
    reports_root = project_root / "data" / "runtime" / "reports"
    return _assert_plain_regular_file(reports_root / f"{value}.json", project_root, "report")


def _mission_from_store(store: object, mission_id: str) -> tuple[dict[str, object], list[object]]:
    if not isinstance(store, dict) or not isinstance(store.get("missions"), list):
        raise RecoveryError("missions_store_shape_invalid")
    matches = [row for row in store["missions"] if isinstance(row, dict) and row.get("id") == mission_id]
    if len(matches) != 1:
        raise RecoveryError("mission_match_count_invalid")
    return matches[0], store["missions"]


def _recovery_id(mission_id: str, stdout_sha: str, final_sha: str) -> str:
    basis = "\x1f".join((mission_id, stdout_sha, final_sha, VALIDATOR_VERSION))
    return "radar-recovery-" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:32]


def _has_recovery_marker(
    mission: Mapping[str, object],
    report: Mapping[str, object],
    settings: Mapping[str, object],
    recovery_id: str,
) -> bool:
    mission_recovery = mission.get("recovery")
    report_recovery = report.get("recovery")
    schedule = settings.get("indicatorScoutSchedule")
    return bool(
        isinstance(mission_recovery, dict)
        and mission_recovery.get("recoveryId") == recovery_id
        and isinstance(report_recovery, dict)
        and report_recovery.get("recoveryId") == recovery_id
        and isinstance(schedule, dict)
        and schedule.get("lastRecoveryId") == recovery_id
    )


def _receipt_semantics(receipt: object) -> dict[str, object]:
    source = receipt if isinstance(receipt, dict) else {}
    keys = (
        "applicable",
        "valid",
        "failureCode",
        "procedureId",
        "procedureKind",
        "expectedFields",
        "providedFields",
        "values",
        "missingFields",
        "expectedEvidenceKinds",
        "providedEvidenceKinds",
        "missingEvidenceKinds",
        "entryErrors",
        "enumNormalizations",
        "oversizedFields",
        "contractValueChars",
        "contractValueLimitChars",
        "resultEnvelopeChars",
        "resultEnvelopeLimitChars",
        "runnerStructuredResultChars",
        "sourceUrlCount",
    )
    return {key: copy.deepcopy(source.get(key)) for key in keys}


def _validate_enum_only_blocked_receipt(
    old_receipt: object,
    current_receipt: Mapping[str, object],
    normalizations: list[dict[str, object]],
    entry_count: int,
) -> None:
    """Authorize recovery only for the historical enum-only Radar rejection.

    The older validator rejected the complete ``entries`` field when any
    entry used a documented alias.  Its receipt therefore recorded the
    entries field as missing while retaining the source/evidence counters.
    Every rejected entry must now have at least one allowlisted
    normalization; unrelated schema, evidence, URL, or size failures are not
    recoverable through this tool.
    """

    old = _require_mapping(old_receipt, "blocked.workflowOutput")
    if entry_count < 1:
        raise RecoveryError("blocked_enum_receipt_entry_count_invalid")
    expected_errors = [
        f"entry_{index}_invalid_enum" for index in range(1, entry_count + 1)
    ]
    normalized_indices = sorted({
        row.get("entryIndex")
        for row in normalizations
        if isinstance(row.get("entryIndex"), int)
    })
    scalar_match_keys = (
        "expectedFields",
        "expectedEvidenceKinds",
        "providedEvidenceKinds",
        "contractValueChars",
        "contractValueLimitChars",
        "resultEnvelopeChars",
        "resultEnvelopeLimitChars",
        "runnerStructuredResultChars",
        "sourceUrlCount",
    )
    if not (
        old.get("applicable") is True
        and old.get("valid") is False
        and old.get("failureCode") == EXPECTED_FAILURE
        and old.get("procedureId") == EXPECTED_PROCEDURE_ID
        and old.get("procedureKind") == "backend_procedure"
        and old.get("providedFields") == []
        and old.get("values") == {}
        and old.get("missingFields") == ["entries"]
        and old.get("missingEvidenceKinds")
        == [
            kind
            for kind in (current_receipt.get("expectedEvidenceKinds") or [])
            if kind != "source_url"
        ]
        and old.get("entryErrors") == expected_errors
        and old.get("enumNormalizations") in (None, [])
        and old.get("oversizedFields") == []
        and normalized_indices == list(range(1, entry_count + 1))
        and all(old.get(key) == current_receipt.get(key) for key in scalar_match_keys)
    ):
        raise RecoveryError("blocked_receipt_not_enum_only")


def _validate_backend_workflow_binding(
    bridge: ModuleType,
    mission: Mapping[str, object],
    report: Mapping[str, object],
) -> None:
    """Require the persisted lineage to remain canonical and guard-trusted."""

    storage = getattr(bridge, "_workflow_context_storage", None)
    trusted_intent = getattr(bridge, "_trusted_workflow_guard_intent", None)
    coherent_marker = getattr(
        bridge, "_mission_backend_auto_safe_marker_is_coherent", None
    )
    if not callable(storage) or not callable(trusted_intent) or not callable(coherent_marker):
        raise RecoveryError("backend_workflow_binding_helpers_unavailable")
    context = _require_mapping(mission.get("workflowContext"), "workflowContext")
    report_context = _require_mapping(
        report.get("workflowContext"), "report.workflowContext"
    )
    try:
        stored_context = storage(context)
        intent = trusted_intent(mission)
        marker_is_coherent = coherent_marker(dict(mission))
    except Exception as error:
        raise RecoveryError(
            f"backend_workflow_binding_validation_failed:{error.__class__.__name__}"
        ) from error
    if (
        stored_context != context
        or report_context != context
        or not isinstance(intent, str)
        or marker_is_coherent is not True
    ):
        raise RecoveryError("backend_workflow_binding_invalid")


def _validate_exact_recovered_state(
    project_root: Path,
    mission: dict[str, object],
    report: dict[str, object],
    settings: dict[str, object],
    recovery_id: str,
    hashes: Mapping[str, str],
    receipt: dict[str, object],
    report_metrics: dict[str, object],
    parsed: dict[str, object],
    normalizations: list[dict[str, object]],
    final_text: str,
) -> None:
    if not (
        mission.get("status") == "completed"
        and mission.get("phase") == "auto_guarded_completed_recovered_contract_revalidation"
        and mission.get("workStatus") == "completed"
        and mission.get("errorCode") is None
        and mission.get("result") == final_text
        and mission.get("recoveryId") == recovery_id
        and mission.get("blockedCapability") == ""
    ):
        raise RecoveryError("recovered_mission_state_invalid")
    mission_recovery = _require_mapping(mission.get("recovery"), "mission.recovery")
    approval = _require_mapping(mission.get("approval"), "approval")
    approval_prestate = _require_mapping(
        mission_recovery.get("approvalPrestate"), "recovery.approvalPrestate"
    )
    if not (
        approval.get("required") is False
        and approval.get("state") == "not_required"
        and approval.get("gateMode") == "not_required"
        and approval == approval_prestate
    ):
        raise RecoveryError("recovered_approval_state_invalid")
    execution = _require_mapping(mission.get("execution"), "execution")
    execution_prestate = _require_mapping(
        mission_recovery.get("executionPrestate"), "recovery.executionPrestate"
    )
    expected_execution = copy.deepcopy(execution_prestate)
    expected_execution["dispatchState"] = "completed"
    if not (
        execution.get("dispatchState") == "completed"
        and execution.get("schema") == "auto-guarded-execution-v1"
        and execution.get("authorizationSource") == "backend_auto_policy"
        and execution.get("authorizationDecision") == "allowed"
        and execution.get("authorizationPolicyVersion") == EXPECTED_POLICY_VERSION
        and execution.get("authorizationReason") == "routine_internal_or_read_only"
        and execution.get("processStarted") is True
        and execution.get("webSearchEnabled") is True
        and execution.get("webSearchMode") == "live"
        and execution.get("webSearchUsed") is True
        and execution.get("webSearchEvidenceVerified") is True
        and execution.get("controlPlaneWritable") is False
        and execution.get("writeRoots") == []
        and execution.get("automaticRetry") is False
        and execution == expected_execution
    ):
        raise RecoveryError("recovered_execution_state_invalid")
    context = _require_mapping(mission.get("workflowContext"), "workflowContext")
    preserved_context = _require_mapping(
        mission_recovery.get("workflowContext"), "recovery.workflowContext"
    )
    reservation = _require_mapping(context.get("executionReservation"), "executionReservation")
    procedure = _require_mapping(context.get("pluginProcedure"), "pluginProcedure")
    slot_key = str(reservation.get("slotKey") or "")
    if not (
        context == preserved_context
        and context.get("propId") == EXPECTED_PROP_ID
        and context.get("actionId") == EXPECTED_ACTION_ID
        and mission.get("owner") == "codex_mcp_operator"
        and mission.get("targetId") == EXPECTED_PROP_ID
        and mission.get("reportType") == EXPECTED_REPORT_TYPE
        and reservation.get("settingsKey") == "indicatorScoutSchedule"
        and reservation.get("maximumRunsPerDay") == 1
        and slot_key.startswith("indicatorScoutSchedule:")
        and procedure.get("pluginSkillId") == EXPECTED_PROCEDURE_ID
        and procedure.get("procedureKind") == "backend_procedure"
        and procedure.get("pluginInvocationMode") == "backend_owned_procedure"
        and procedure.get("automationMode") == "scheduled_read_only"
    ):
        raise RecoveryError("recovered_mission_binding_invalid")
    report_ids = mission.get("reportIds")
    if report_ids != [report.get("id")]:
        raise RecoveryError("recovered_report_binding_invalid")
    if not (
        report.get("status") == "ready"
        and report.get("type") == EXPECTED_REPORT_TYPE
        and report.get("linkedMissionId") == mission.get("id")
        and report.get("linkedPropId") == EXPECTED_PROP_ID
        and report.get("ownerAgentId") == mission.get("owner")
        and report.get("summary") == final_text
        and report.get("findings") == (parsed.get("findings") or [])
        and report.get("nextActions") == (parsed.get("nextSteps") or [])
        and report.get("evidence") == (parsed.get("evidence") or [])
        and mission.get("evidence") == (parsed.get("evidence") or [])
        and report.get("risks") == []
        and mission.get("artifactPath") == mission_recovery.get("artifactRef")
        and report.get("artifacts") == [mission_recovery.get("artifactRef")]
        and report.get("recoveryId") == recovery_id
        and report.get("recoveredAt") == mission.get("recoveredAt")
    ):
        raise RecoveryError("recovered_report_state_invalid")
    report_context = _require_mapping(report.get("workflowContext"), "report.workflowContext")
    if report_context != context:
        raise RecoveryError("recovered_report_workflow_context_invalid")
    mission_receipt = mission.get("workflowOutputContract")
    stored_metrics = _require_mapping(report.get("metrics"), "report.metrics")
    report_receipt = stored_metrics.get("workflowOutput")
    expected_receipt = _receipt_semantics(receipt)
    non_receipt_metric_keys = set(report_metrics) - {"workflowOutput"}
    if (
        mission_receipt != report_receipt
        or _receipt_semantics(mission_receipt) != expected_receipt
        or _receipt_semantics(report_receipt) != expected_receipt
        or set(stored_metrics) != set(report_metrics)
        or any(
            stored_metrics.get(key) != report_metrics.get(key)
            for key in non_receipt_metric_keys
        )
        or stored_metrics.get("entries") != report_metrics.get("entries")
        or not isinstance(stored_metrics.get("entries"), list)
        or len(stored_metrics["entries"]) != len(report_metrics.get("entries") or [])
    ):
        raise RecoveryError("recovered_contract_receipt_invalid")
    report_recovery = _require_mapping(report.get("recovery"), "report.recovery")
    if mission_recovery != report_recovery:
        raise RecoveryError("recovered_provenance_mismatch")
    artifact_hashes = mission_recovery.get("artifactHashes")
    previous = mission_recovery.get("previousBlockedState")
    if not (
        mission_recovery.get("schemaVersion") == RECOVERY_SCHEMA
        and mission_recovery.get("recoveryId") == recovery_id
        and mission_recovery.get("recoveredAt") == mission.get("recoveredAt")
        and mission_recovery.get("validatorVersion") == VALIDATOR_VERSION
        and mission_recovery.get("enumNormalizations") == normalizations
        and isinstance(artifact_hashes, dict)
        and artifact_hashes.get("stdoutSha256") == hashes.get("stdout")
        and artifact_hashes.get("finalSha256") == hashes.get("final")
        and isinstance(previous, dict)
        and previous.get("missionStatus") == "blocked"
        and previous.get("missionPhase") == EXPECTED_PHASE
        and previous.get("missionWorkStatus") == EXPECTED_FAILURE
        and previous.get("missionErrorCode") == EXPECTED_FAILURE
        and previous.get("reportStatus") == "blocked"
        and isinstance(previous.get("reportSummary"), str)
        and bool(str(previous.get("reportSummary") or "").strip())
        and previous.get("reportRisks") == [EXPECTED_FAILURE]
        and previous.get("reportFailureCode") == EXPECTED_FAILURE
        and mission_recovery.get("reservationPreserved") is True
        and mission_recovery.get("runnerInvoked") is False
        and mission_recovery.get("webSearchInvoked") is False
        and mission_recovery.get("mt4Actions") is False
        and mission_recovery.get("googleSheetWrites") is False
        and mission_recovery.get("externalWrites") is False
    ):
        raise RecoveryError("recovered_provenance_invalid")
    schedule = _require_mapping(settings.get("indicatorScoutSchedule"), "indicatorScoutSchedule")
    if not (
        schedule.get("lastMissionId") == mission.get("id")
        and schedule.get("lastRunStatus") == "completed"
        and schedule.get("lastResultKind") == "recovered_contract_revalidation"
        and schedule.get("lastError") is None
        and schedule.get("lastErrorAt") is None
        and schedule.get("lastRecoveryId") == recovery_id
        and schedule.get("lastRecoveryAt") == mission_recovery.get("recoveredAt")
        and schedule.get("lastSlotKey") == slot_key
        and schedule.get("lastAttemptSlotKey") == slot_key
        and schedule.get("dailyExecutionDate") == reservation.get("bangkokDate")
        and schedule.get("dailyExecutionCount") == 1
        and schedule.get("dailyExecutionSlotKeys") == [slot_key]
        and schedule.get("pendingSlotKey") is None
    ):
        raise RecoveryError("recovered_daily_reservation_invalid")
    journal_path = (
        project_root / "data" / "runtime" / "recoveries" / f"{recovery_id}.journal.json"
    )
    journal = _decode_json(_read_bytes(journal_path), "recovery_journal")
    if not (
        isinstance(journal, dict)
        and journal.get("recoveryId") == recovery_id
        and journal.get("status") == "committed"
        and journal.get("missionId") == mission.get("id")
        and journal.get("reportId") == report.get("id")
        and journal.get("recoveryProvenance") == mission_recovery
    ):
        raise RecoveryError("recovered_journal_invalid")
    reservation_projection = _reservation_projection(schedule)
    if not (
        mission_recovery.get("reservationProjection") == reservation_projection
        and journal.get("reservationProjection") == reservation_projection
    ):
        raise RecoveryError("recovered_reservation_projection_invalid")
    after_hashes = journal.get("afterHashes")
    intended_hashes = journal.get("intendedHashes")
    if (
        not isinstance(after_hashes, dict)
        or not isinstance(intended_hashes, dict)
        or any(not SHA256_RE.fullmatch(str(after_hashes.get(name) or "")) for name in ALL_HASH_NAMES)
        or intended_hashes != after_hashes
        or any(after_hashes.get(name) != hashes.get(name) for name in ARTIFACT_HASH_NAMES)
    ):
        raise RecoveryError("recovered_journal_post_hashes_invalid")
    recovery_events: list[dict[str, object]] = []
    runtime_dir = project_root / "data" / "runtime"
    audit_paths = [runtime_dir / "bridge-audit.jsonl"]
    audit_paths.extend(
        sorted((runtime_dir / "archive" / "bridge-audit").glob("*.jsonl"))
        if (runtime_dir / "archive" / "bridge-audit").exists()
        else []
    )
    for audit_path in audit_paths:
        if not audit_path.exists():
            continue
        try:
            safe_audit_path = _assert_plain_regular_file(
                audit_path, project_root, "recovery_audit_segment"
            )
            audit_text = _read_bytes(safe_audit_path).decode("utf-8")
        except UnicodeError as error:
            raise RecoveryError("recovered_audit_not_utf8") from error
        for index, raw_line in enumerate(audit_text.splitlines(), start=1):
            if not raw_line.strip():
                continue
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError as error:
                raise RecoveryError(
                    f"recovered_audit_jsonl_invalid:{safe_audit_path.name}:{index}"
                ) from error
            if (
                isinstance(event, dict)
                and event.get("type") == "radar.contract_result_recovered"
                and event.get("recoveryId") == recovery_id
            ):
                recovery_events.append(event)
    if len(recovery_events) != 1:
        raise RecoveryError("recovered_audit_event_count_invalid")
    audit_event = recovery_events[0]
    if not (
        audit_event.get("time") == mission_recovery.get("recoveredAt")
        and audit_event.get("missionId") == mission.get("id")
        and audit_event.get("reportId") == report.get("id")
        and audit_event.get("preState")
        == {"mission": "blocked", "report": "blocked", "reason": EXPECTED_FAILURE}
        and audit_event.get("postState")
        == {"mission": "completed", "report": "ready"}
        and audit_event.get("stdoutSha256") == hashes.get("stdout")
        and audit_event.get("finalSha256") == hashes.get("final")
        and audit_event.get("validatorVersion") == VALIDATOR_VERSION
        and audit_event.get("enumNormalizations") == normalizations
        and audit_event.get("reservationPreserved") is True
        and audit_event.get("runnerInvoked") is False
        and audit_event.get("webSearchInvoked") is False
        and audit_event.get("mt4Actions") is False
        and audit_event.get("googleSheetWrites") is False
        and audit_event.get("externalWrites") is False
    ):
        raise RecoveryError("recovered_audit_event_invalid")


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            except OSError:
                pass
            finally:
                os.close(directory_fd)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def _atomic_write_json(path: Path, payload: object) -> None:
    _atomic_write_bytes(path, canonical_json_bytes(payload))


@contextmanager
def _exclusive_recovery_lock(runtime_dir: Path) -> Iterator[None]:
    recovery_dir = _ensure_local_directory(
        runtime_dir / "recoveries", runtime_dir.parents[1], "recoveries"
    )
    lock_path = recovery_dir / ".radar-contract-recovery.lock"
    try:
        handle = lock_path.open("a+b")
    except OSError as error:
        raise RecoveryError("recovery_lock_already_held") from error
    locked = False
    try:
        if os.name == "nt":
            import msvcrt

            try:
                handle.seek(0)
                if handle.read(1) == b"":
                    handle.seek(0)
                    handle.write(b"0")
                    handle.flush()
            except OSError as error:
                raise RecoveryError("recovery_lock_already_held") from error
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise RecoveryError("recovery_lock_already_held") from error
        else:
            import fcntl

            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (BlockingIOError, OSError) as error:
                raise RecoveryError("recovery_lock_already_held") from error
        locked = True
        handle.seek(0)
        handle.truncate()
        handle.write(
            json.dumps(
                {"pid": os.getpid(), "acquiredAt": utc_now()},
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("ascii")
        )
        handle.flush()
        os.fsync(handle.fileno())
        yield
    finally:
        if locked:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
            else:
                import fcntl

                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass
        handle.close()


def _assert_expected_hashes(actual: Mapping[str, str], expected: Mapping[str, str] | None) -> None:
    if expected is None or set(expected) != set(ALL_HASH_NAMES):
        raise RecoveryError("apply_requires_all_expected_hashes")
    for name in ALL_HASH_NAMES:
        wanted = str(expected.get(name) or "").lower()
        if not SHA256_RE.fullmatch(wanted):
            raise RecoveryError(f"expected_hash_invalid:{name}")
        if actual.get(name) != wanted:
            raise RecoveryError(f"compare_and_swap_mismatch:{name}")


def _audit_event_line(event: Mapping[str, object], event_time: str) -> bytes:
    line = json.dumps(
        {"time": event_time, **event},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return (line + "\n").encode("utf-8")


def _bridge_not_running(project_root: Path) -> None:
    if (project_root / "data" / "runtime" / "bridge-control.json").exists():
        raise RecoveryError("bridge_control_present_stop_bridge_before_apply")


def _archive_rolled_back_journal(
    project_root: Path,
    journal_path: Path,
    journal: Mapping[str, object],
) -> Path:
    recovery_id = str(journal.get("recoveryId") or "")
    if not recovery_id.startswith("radar-recovery-"):
        raise RecoveryError("rolled_back_journal_recovery_id_invalid")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    archive_dir = project_root / "data" / "runtime" / "recoveries" / "rolled-back"
    archive_dir = _ensure_local_directory(
        archive_dir, project_root, "rolled_back_recoveries"
    )
    archive_path = archive_dir / f"{recovery_id}-{stamp}-{os.getpid()}.journal.json"
    if archive_path.exists():
        raise RecoveryError("rolled_back_journal_archive_collision")
    _atomic_write_json(archive_path, dict(journal))
    journal_path.unlink()
    return archive_path


def _rollback_prepared_recovery_journal(project_root: Path, mission_id: str) -> bool:
    """Restore an interrupted prepared transaction before reading live state.

    The recovery lock and the Bridge process guard must already be held.  Only
    backups whose hashes exactly match the journal's original CAS snapshot are
    accepted; an ambiguous or malformed journal is a hard stop.
    """

    runtime_dir = project_root / "data" / "runtime"
    recovery_dir = runtime_dir / "recoveries"
    if not recovery_dir.exists():
        return False
    candidates: list[tuple[Path, dict[str, object]]] = []
    for raw_path in sorted(recovery_dir.glob("*.journal.json")):
        path = _assert_plain_regular_file(raw_path, project_root, "recovery_journal")
        journal = _decode_json(_read_bytes(path), "recovery_journal")
        if not isinstance(journal, dict):
            raise RecoveryError("recovery_journal_shape_invalid")
        journal_mission_id = str(journal.get("missionId") or "")
        journal_recovery_id = str(journal.get("recoveryId") or "")
        if not (
            SAFE_ID_RE.fullmatch(journal_mission_id)
            and re.fullmatch(r"radar-recovery-[0-9a-f]{32}", journal_recovery_id)
        ):
            raise RecoveryError("recovery_journal_identity_invalid")
        status_name = str(journal.get("status") or "")
        if status_name in {"prepared", "rollback_incomplete"}:
            if journal_mission_id != mission_id:
                raise RecoveryError(
                    f"foreign_incomplete_recovery_journal:{journal_mission_id}"
                )
            candidates.append((path, journal))
        elif status_name not in {"committed", "rolled_back"}:
            raise RecoveryError("recovery_journal_status_invalid")
    if not candidates:
        return False
    if len(candidates) != 1:
        raise RecoveryError("multiple_incomplete_recovery_journals")
    journal_path, journal = candidates[0]
    before_hashes = journal.get("beforeHashes")
    intended_hashes = journal.get("intendedHashes")
    backup_refs = journal.get("backupPaths")
    if not (
        isinstance(before_hashes, dict)
        and isinstance(intended_hashes, dict)
        and isinstance(backup_refs, dict)
        and all(
            SHA256_RE.fullmatch(str(before_hashes.get(name) or ""))
            and SHA256_RE.fullmatch(str(intended_hashes.get(name) or ""))
            for name in ALL_HASH_NAMES
        )
    ):
        raise RecoveryError("prepared_recovery_journal_shape_invalid")
    report_id = str(journal.get("reportId") or "")
    if not SAFE_ID_RE.fullmatch(report_id):
        raise RecoveryError("prepared_recovery_report_id_invalid")
    targets = {
        "missions": runtime_dir / "missions.json",
        "report": runtime_dir / "reports" / f"{report_id}.json",
        "settings": runtime_dir / "dashboard-workflow-settings.json",
        "audit": runtime_dir / "bridge-audit.jsonl",
    }
    backup_root = (runtime_dir / "backups").resolve(strict=True)
    backup_payloads: dict[str, bytes] = {}
    for name in MUTABLE_HASH_NAMES:
        reference = str(backup_refs.get(name) or "").replace("\\", "/")
        if not reference or reference.startswith("/") or re.match(r"^[A-Za-z]:", reference):
            raise RecoveryError(f"prepared_recovery_backup_reference_invalid:{name}")
        backup_path = _assert_plain_regular_file(
            Path(*reference.split("/")), project_root, f"recovery_backup_{name}"
        )
        try:
            backup_path.relative_to(backup_root)
        except ValueError as error:
            raise RecoveryError(f"prepared_recovery_backup_outside_root:{name}") from error
        payload = _read_bytes(backup_path)
        if sha256_bytes(payload) != before_hashes.get(name):
            raise RecoveryError(f"prepared_recovery_backup_hash_mismatch:{name}")
        backup_payloads[name] = payload
    backup_missions_store = _decode_json(backup_payloads["missions"], "backup_missions")
    backup_mission, _rows = _mission_from_store(backup_missions_store, mission_id)
    backup_final_path, backup_stdout_path, _artifact_ref = _resolve_artifacts(
        project_root, backup_mission
    )
    artifact_current = {
        "stdout": sha256_bytes(_read_bytes(backup_stdout_path)),
        "final": sha256_bytes(_read_bytes(backup_final_path)),
    }
    if any(
        artifact_current[name] != before_hashes.get(name)
        or artifact_current[name] != intended_hashes.get(name)
        for name in ARTIFACT_HASH_NAMES
    ):
        raise RecoveryError("prepared_recovery_artifact_hash_mismatch")
    current_payloads = {
        "missions": _read_bytes(targets["missions"]),
        "report": _read_bytes(targets["report"]),
        "settings": _read_bytes(targets["settings"]),
        "audit": _read_bytes(targets["audit"], allow_missing=True),
    }
    current_hashes = {
        name: sha256_bytes(payload) for name, payload in current_payloads.items()
    }
    divergent = [
        name
        for name in MUTABLE_HASH_NAMES
        if current_hashes[name]
        not in {before_hashes.get(name), intended_hashes.get(name)}
    ]
    if divergent:
        raise RecoveryError(
            "prepared_recovery_external_divergence:" + ",".join(divergent)
        )
    if journal.get("auditExisted") not in {True, False}:
        raise RecoveryError("prepared_recovery_audit_prestate_invalid")
    for name in ("missions", "report", "settings"):
        if current_hashes[name] == intended_hashes.get(name):
            _atomic_write_bytes(targets[name], backup_payloads[name])
    if current_hashes["audit"] == intended_hashes.get("audit"):
        if journal.get("auditExisted") is True:
            _atomic_write_bytes(targets["audit"], backup_payloads["audit"])
        elif not backup_payloads["audit"]:
            targets["audit"].unlink(missing_ok=True)
        else:
            raise RecoveryError("prepared_recovery_audit_prestate_invalid")
    for name, target in targets.items():
        restored = _read_bytes(target, allow_missing=name == "audit")
        if sha256_bytes(restored) != before_hashes.get(name):
            raise RecoveryError(f"prepared_recovery_restore_hash_mismatch:{name}")
    journal.update({
        "status": "rolled_back",
        "rolledBackAt": utc_now(),
        "rollbackReason": "startup_prepared_journal_recovery",
        "rollbackErrors": [],
    })
    _atomic_write_json(journal_path, journal)
    _archive_rolled_back_journal(project_root, journal_path, journal)
    return True


@contextmanager
def _exclusive_bridge_process_guard(project_root: Path, bridge: ModuleType) -> Iterator[None]:
    """Hold the Bridge's own project-wide process mutex during live apply.

    Unit tests intentionally point the recovery code at a temporary project
    root while importing the production validator module.  Only acquire the
    module's mutex when it represents the same checkout.
    """

    bridge_root = Path(str(getattr(bridge, "PROJECT_ROOT", ""))).resolve()
    if bridge_root != project_root:
        yield
        return
    acquire = getattr(bridge, "acquire_bridge_process_guard", None)
    release = getattr(bridge, "release_bridge_process_guard", None)
    if not callable(acquire) or not callable(release):
        raise RecoveryError("bridge_process_guard_unavailable")
    if acquire() is not True:
        raise RecoveryError("bridge_process_guard_busy_stop_bridge_before_apply")
    try:
        yield
    finally:
        release()


def recover_radar_contract_result(
    project_root: Path,
    mission_id: str,
    *,
    apply: bool = False,
    expected_hashes: Mapping[str, str] | None = None,
    bridge: ModuleType | None = None,
    runner: ModuleType | None = None,
    fault_injector: Callable[[str], None] | None = None,
    _lock_held: bool = False,
) -> dict[str, object]:
    """Validate and optionally recover one exact immutable Radar result."""

    project_root = Path(project_root).resolve(strict=True)
    if not SAFE_ID_RE.fullmatch(str(mission_id or "")):
        raise RecoveryError("unsafe_mission_id")
    if bridge is None or runner is None:
        loaded_bridge, loaded_runner = load_runtime_modules(project_root)
        bridge = bridge or loaded_bridge
        runner = runner or loaded_runner
    runtime_dir = project_root / "data" / "runtime"
    if apply and not _lock_held:
        _bridge_not_running(project_root)
        with _exclusive_bridge_process_guard(project_root, bridge), _exclusive_recovery_lock(runtime_dir):
            _bridge_not_running(project_root)
            rolled_back = _rollback_prepared_recovery_journal(
                project_root, mission_id
            )
            result = recover_radar_contract_result(
                project_root,
                mission_id,
                apply=True,
                expected_hashes=expected_hashes,
                bridge=bridge,
                runner=runner,
                fault_injector=fault_injector,
                _lock_held=True,
            )
            if rolled_back:
                result["preparedJournalRolledBack"] = True
            return result
    missions_path = _assert_plain_regular_file(runtime_dir / "missions.json", project_root, "missions")
    settings_path = _assert_plain_regular_file(
        runtime_dir / "dashboard-workflow-settings.json", project_root, "settings"
    )
    audit_path = runtime_dir / "bridge-audit.jsonl"
    if audit_path.exists():
        audit_path = _assert_plain_regular_file(audit_path, project_root, "audit")

    missions_bytes = _read_bytes(missions_path)
    settings_bytes = _read_bytes(settings_path)
    missions_store = _decode_json(missions_bytes, "missions")
    settings = _decode_json(settings_bytes, "settings")
    if not isinstance(settings, dict):
        raise RecoveryError("settings_store_shape_invalid")
    mission, missions = _mission_from_store(missions_store, mission_id)
    report_ids = mission.get("reportIds")
    if not isinstance(report_ids, list) or len(report_ids) != 1:
        raise RecoveryError("mission_report_binding_mismatch")
    report_path = _report_path(project_root, report_ids[0])
    report_bytes = _read_bytes(report_path)
    report = _decode_json(report_bytes, "report")
    if not isinstance(report, dict):
        raise RecoveryError("report_store_shape_invalid")

    final_path, stdout_path, artifact_ref = _resolve_artifacts(project_root, mission)
    final_bytes = _read_bytes(final_path)
    stdout_bytes = _read_bytes(stdout_path)
    audit_bytes = _read_bytes(audit_path, allow_missing=True)
    hashes = {
        "missions": sha256_bytes(missions_bytes),
        "report": sha256_bytes(report_bytes),
        "settings": sha256_bytes(settings_bytes),
        "audit": sha256_bytes(audit_bytes),
        "stdout": sha256_bytes(stdout_bytes),
        "final": sha256_bytes(final_bytes),
    }
    recovery_id = _recovery_id(mission_id, hashes["stdout"], hashes["final"])
    recovered_marker = _has_recovery_marker(mission, report, settings, recovery_id)
    if recovered_marker:
        schedule = _require_mapping(
            settings.get("indicatorScoutSchedule"), "indicatorScoutSchedule"
        )
        recovered_context = _require_mapping(
            mission.get("workflowContext"), "workflowContext"
        )
        recovered_reservation = _require_mapping(
            recovered_context.get("executionReservation"), "executionReservation"
        )
        slot_key = str(recovered_reservation.get("slotKey") or "")
    else:
        schedule, slot_key = _validate_exact_prestate(
            mission, report, settings, artifact_ref
        )
    _validate_backend_workflow_binding(bridge, mission, report)
    last_agent_message, terminal_event = _strict_jsonl_result(stdout_bytes)
    output_limit = int((_require_mapping(mission.get("budget"), "budget").get("outputLimitChars") or 0))
    if output_limit < 1000 or output_limit > 20000:
        raise RecoveryError("mission_output_limit_invalid")
    try:
        parsed = runner.parse_work_result(last_agent_message, output_limit, EXPECTED_RESULT_PROFILE)
    except Exception as error:
        raise RecoveryError(f"runner_parse_failed:{error.__class__.__name__}") from error
    if parsed.get("workStatus") != "completed":
        raise RecoveryError("runner_result_not_completed")
    try:
        receipt = _validate_backend_contract_excluding_bound_report(
            bridge, mission, parsed, report
        )
    except Exception as error:
        raise RecoveryError(f"backend_validation_failed:{error.__class__.__name__}") from error
    if not isinstance(receipt, dict) or not receipt.get("valid"):
        raise RecoveryError("backend_contract_still_invalid")
    if receipt.get("failureCode") not in (None, ""):
        raise RecoveryError("backend_contract_failure_code_present")
    if receipt.get("missingFields") or receipt.get("missingEvidenceKinds") or receipt.get("entryErrors"):
        raise RecoveryError("backend_contract_receipt_incomplete")
    if "entries" not in (receipt.get("providedFields") or []):
        raise RecoveryError("backend_contract_entries_missing")
    normalizations = _validate_normalizations(receipt, bridge)
    try:
        final_text = final_bytes.decode("utf-8")
    except UnicodeError as error:
        raise RecoveryError("final_artifact_not_utf8") from error
    formatted = runner.format_work_report(parsed, output_limit)
    if formatted != final_text:
        raise RecoveryError("formatted_final_artifact_mismatch")

    try:
        report_metrics = bridge.dashboard_workflow_output_metrics(receipt)
    except Exception as error:
        raise RecoveryError(f"backend_metrics_projection_failed:{error.__class__.__name__}") from error
    if not recovered_marker:
        metrics = _require_mapping(report.get("metrics"), "report.metrics")
        entries = report_metrics.get("entries")
        if not isinstance(entries, list):
            raise RecoveryError("backend_metrics_entries_invalid")
        _validate_enum_only_blocked_receipt(
            metrics.get("workflowOutput"),
            receipt,
            normalizations,
            len(entries),
        )
    if recovered_marker:
        _validate_exact_recovered_state(
            project_root,
            mission,
            report,
            settings,
            recovery_id,
            hashes,
            receipt,
            report_metrics,
            parsed,
            normalizations,
            final_text,
        )
        return {
            "ok": True,
            "status": "already_recovered",
            "applied": False,
            "idempotentReplay": True,
            "missionId": mission_id,
            "reportId": report.get("id"),
            "recoveryId": recovery_id,
            "expectedHashes": hashes,
            "entriesCount": len(report_metrics.get("entries") or []),
            "enumNormalizations": normalizations,
        }

    reservation_before = _reservation_projection(schedule)
    recovered_at = utc_now()
    previous_blocked_state = {
        "missionStatus": mission.get("status"),
        "missionPhase": mission.get("phase"),
        "missionWorkStatus": mission.get("workStatus"),
        "missionErrorCode": mission.get("errorCode"),
        "reportStatus": report.get("status"),
        "reportSummary": report.get("summary"),
        "reportRisks": copy.deepcopy(report.get("risks")),
        "reportFailureCode": (
            report.get("metrics", {}).get("workflowOutput", {}).get("failureCode")
            if isinstance(report.get("metrics"), dict)
            and isinstance(report["metrics"].get("workflowOutput"), dict)
            else None
        ),
    }
    recovery_common = {
        "schemaVersion": RECOVERY_SCHEMA,
        "recoveryId": recovery_id,
        "recoveredAt": recovered_at,
        "validatorVersion": VALIDATOR_VERSION,
        "artifactHashes": {
            "stdoutSha256": hashes["stdout"],
            "finalSha256": hashes["final"],
        },
        "enumNormalizations": copy.deepcopy(normalizations),
        "previousBlockedState": previous_blocked_state,
        "approvalPrestate": copy.deepcopy(mission.get("approval")),
        "executionPrestate": copy.deepcopy(mission.get("execution")),
        "workflowContext": copy.deepcopy(mission.get("workflowContext")),
        "artifactRef": artifact_ref,
        "reservationProjection": copy.deepcopy(reservation_before),
        "reservationPreserved": True,
        "runnerInvoked": False,
        "webSearchInvoked": False,
        "mt4Actions": False,
        "googleSheetWrites": False,
        "externalWrites": False,
    }

    updated_mission = copy.deepcopy(mission)
    updated_mission.update({
        "status": "completed",
        "phase": "auto_guarded_completed_recovered_contract_revalidation",
        "workStatus": "completed",
        "errorCode": None,
        "result": final_text,
        "evidence": copy.deepcopy(parsed.get("evidence") or []),
        "workflowOutputContract": copy.deepcopy(receipt),
        "blockedCapability": "",
        "recoveredAt": recovered_at,
        "recoveryId": recovery_id,
        "recovery": copy.deepcopy(recovery_common),
    })
    updated_execution = copy.deepcopy(_require_mapping(updated_mission.get("execution"), "execution"))
    updated_execution["dispatchState"] = "completed"
    updated_mission["execution"] = updated_execution

    updated_report = copy.deepcopy(report)
    updated_report.update({
        "summary": final_text,
        "status": "ready",
        "findings": copy.deepcopy(parsed.get("findings") or []),
        "metrics": copy.deepcopy(report_metrics),
        "risks": [],
        "nextActions": copy.deepcopy(parsed.get("nextSteps") or []),
        "evidence": copy.deepcopy(parsed.get("evidence") or []),
        "recoveredAt": recovered_at,
        "recoveryId": recovery_id,
        "recovery": copy.deepcopy(recovery_common),
    })

    updated_settings = copy.deepcopy(settings)
    updated_schedule = _require_mapping(
        updated_settings.get("indicatorScoutSchedule"), "indicatorScoutSchedule"
    )
    updated_schedule.update({
        "lastRunStatus": "completed",
        "lastResultKind": "recovered_contract_revalidation",
        "lastError": None,
        "lastErrorAt": None,
        "lastRecoveryAt": recovered_at,
        "lastRecoveryId": recovery_id,
    })
    updated_settings["indicatorScoutSchedule"] = updated_schedule
    if _reservation_projection(updated_schedule) != reservation_before:
        raise RecoveryError("daily_reservation_would_change")

    replacement_count = 0
    for index, row in enumerate(missions):
        if isinstance(row, dict) and row.get("id") == mission_id:
            missions[index] = updated_mission
            replacement_count += 1
    if replacement_count != 1:
        raise RecoveryError("mission_replace_count_invalid")

    plan = {
        "ok": True,
        "status": "ready_to_apply" if not apply else "validated",
        "applied": False,
        "idempotentReplay": False,
        "missionId": mission_id,
        "reportId": report.get("id"),
        "recoveryId": recovery_id,
        "validatorVersion": VALIDATOR_VERSION,
        "artifactPath": artifact_ref,
        "stdoutPath": stdout_path.relative_to(project_root).as_posix(),
        "expectedHashes": hashes,
        "entriesCount": len(report_metrics.get("entries") or []),
        "enumNormalizations": normalizations,
        "reservation": {
            "slotKey": slot_key,
            "preserved": True,
            "projection": reservation_before,
        },
        "sideEffects": {
            "runnerInvoked": False,
            "webSearchInvoked": False,
            "mt4Actions": False,
            "googleSheetWrites": False,
            "externalWrites": False,
        },
        "terminalTurnCompleted": terminal_event.get("type") == "turn.completed",
    }
    if not apply:
        return plan

    _bridge_not_running(project_root)
    _assert_expected_hashes(hashes, expected_hashes)
    if fault_injector is None:
        fault_injector = lambda _stage: None
    recovery_dir = runtime_dir / "recoveries"
    journal_path = recovery_dir / f"{recovery_id}.journal.json"
    backup_attempt = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_dir = runtime_dir / "backups" / f"{recovery_id}-{backup_attempt}-{os.getpid()}"

    guard_context = nullcontext() if _lock_held else _exclusive_bridge_process_guard(project_root, bridge)
    recovery_lock_context = nullcontext() if _lock_held else _exclusive_recovery_lock(runtime_dir)
    with guard_context, recovery_lock_context:
        _bridge_not_running(project_root)
        current_bytes = {
            "missions": _read_bytes(missions_path),
            "report": _read_bytes(report_path),
            "settings": _read_bytes(settings_path),
            "audit": _read_bytes(audit_path, allow_missing=True),
            "stdout": _read_bytes(stdout_path),
            "final": _read_bytes(final_path),
        }
        current_hashes = {name: sha256_bytes(value) for name, value in current_bytes.items()}
        _assert_expected_hashes(current_hashes, expected_hashes)
        if journal_path.exists():
            existing_journal = _decode_json(_read_bytes(journal_path), "recovery_journal")
            if isinstance(existing_journal, dict) and existing_journal.get("status") == "committed":
                raise RecoveryError("committed_journal_exists_but_state_not_idempotent")
            if not isinstance(existing_journal, dict) or existing_journal.get("status") != "rolled_back":
                raise RecoveryError("incomplete_recovery_journal_exists")

        audit_event = {
            "type": "radar.contract_result_recovered",
            "recoveryId": recovery_id,
            "missionId": mission_id,
            "reportId": report.get("id"),
            "preState": {
                "mission": "blocked",
                "report": "blocked",
                "reason": EXPECTED_FAILURE,
            },
            "postState": {"mission": "completed", "report": "ready"},
            "stdoutSha256": hashes["stdout"],
            "finalSha256": hashes["final"],
            "validatorVersion": VALIDATOR_VERSION,
            "enumNormalizations": normalizations,
            "reservationPreserved": True,
            "runnerInvoked": False,
            "webSearchInvoked": False,
            "mt4Actions": False,
            "googleSheetWrites": False,
            "externalWrites": False,
        }
        audit_line = _audit_event_line(audit_event, recovered_at)
        if len(current_bytes["audit"]) + len(audit_line) >= AUDIT_SEGMENT_MAX_BYTES:
            raise RecoveryError("audit_segment_rotation_required")
        intended_payloads = {
            "missions": canonical_json_bytes(missions_store),
            "report": canonical_json_bytes(updated_report),
            "settings": canonical_json_bytes(updated_settings),
            "audit": current_bytes["audit"] + audit_line,
            "stdout": current_bytes["stdout"],
            "final": current_bytes["final"],
        }
        intended_hashes = {
            name: sha256_bytes(payload) for name, payload in intended_payloads.items()
        }

        backup_root = _ensure_local_directory(
            runtime_dir / "backups", project_root, "recovery_backups"
        )
        if backup_dir.parent.resolve() != backup_root:
            raise RecoveryError("recovery_backup_directory_invalid")
        backup_dir.mkdir(parents=False, exist_ok=False)
        backup_paths = {
            "missions": backup_dir / "missions.json",
            "report": backup_dir / f"{report.get('id')}.json",
            "settings": backup_dir / "dashboard-workflow-settings.json",
            "audit": backup_dir / "bridge-audit.jsonl",
        }
        for name, path in backup_paths.items():
            _atomic_write_bytes(path, current_bytes[name])
        journal = {
            "schemaVersion": RECOVERY_SCHEMA,
            "recoveryId": recovery_id,
            "status": "prepared",
            "preparedAt": utc_now(),
            "missionId": mission_id,
            "reportId": report.get("id"),
            "beforeHashes": current_hashes,
            "intendedHashes": intended_hashes,
            "auditExisted": audit_path.exists(),
            "backupPaths": {
                name: path.relative_to(project_root).as_posix()
                for name, path in backup_paths.items()
            },
            "reservationProjection": reservation_before,
            "recoveryProvenance": copy.deepcopy(recovery_common),
        }
        _atomic_write_json(journal_path, journal)
        try:
            fault_injector("prepared")
            _atomic_write_bytes(missions_path, intended_payloads["missions"])
            fault_injector("missions_written")
            _atomic_write_bytes(report_path, intended_payloads["report"])
            fault_injector("report_written")
            _atomic_write_bytes(settings_path, intended_payloads["settings"])
            fault_injector("settings_written")
            if sha256_bytes(_read_bytes(audit_path, allow_missing=True)) != current_hashes["audit"]:
                raise RecoveryError("audit_compare_and_swap_mismatch")
            _atomic_write_bytes(audit_path, intended_payloads["audit"])
            fault_injector("audit_appended")
            after_payloads = {
                "missions": _read_bytes(missions_path),
                "report": _read_bytes(report_path),
                "settings": _read_bytes(settings_path),
                "audit": _read_bytes(audit_path),
                "stdout": _read_bytes(stdout_path),
                "final": _read_bytes(final_path),
            }
            observed_after_hashes = {
                name: sha256_bytes(payload) for name, payload in after_payloads.items()
            }
            if observed_after_hashes != intended_hashes:
                raise RecoveryError("transaction_intended_hash_mismatch")
            journal.update({
                "status": "committed",
                "committedAt": utc_now(),
                "afterHashes": observed_after_hashes,
            })
            _atomic_write_json(journal_path, journal)
        except Exception as error:
            rollback_errors: list[str] = []
            try:
                rollback_payloads = {
                    "missions": _read_bytes(missions_path),
                    "report": _read_bytes(report_path),
                    "settings": _read_bytes(settings_path),
                    "audit": _read_bytes(audit_path, allow_missing=True),
                }
                rollback_hashes = {
                    name: sha256_bytes(payload)
                    for name, payload in rollback_payloads.items()
                }
                divergent = [
                    name
                    for name in MUTABLE_HASH_NAMES
                    if rollback_hashes[name]
                    not in {current_hashes[name], intended_hashes[name]}
                ]
                if divergent:
                    rollback_errors.append(
                        "external_divergence:" + ",".join(divergent)
                    )
                else:
                    for name, path in (
                        ("missions", missions_path),
                        ("report", report_path),
                        ("settings", settings_path),
                    ):
                        if rollback_hashes[name] == intended_hashes[name]:
                            _atomic_write_bytes(path, current_bytes[name])
                    if rollback_hashes["audit"] == intended_hashes["audit"]:
                        if current_bytes["audit"]:
                            _atomic_write_bytes(audit_path, current_bytes["audit"])
                        else:
                            audit_path.unlink(missing_ok=True)
                    rollback_targets = {
                        "missions": missions_path,
                        "report": report_path,
                        "settings": settings_path,
                        "audit": audit_path,
                    }
                    for name, path in rollback_targets.items():
                        restored = _read_bytes(path, allow_missing=name == "audit")
                        if sha256_bytes(restored) != current_hashes[name]:
                            rollback_errors.append(f"{name}:restore_hash_mismatch")
            except Exception as rollback_error:  # pragma: no cover - catastrophic disk failure
                rollback_errors.append(
                    f"rollback_inspection:{rollback_error.__class__.__name__}"
                )
            journal.update({
                "status": "rolled_back" if not rollback_errors else "rollback_incomplete",
                "rolledBackAt": utc_now(),
                "failure": error.__class__.__name__,
                "rollbackErrors": rollback_errors,
            })
            try:
                _atomic_write_json(journal_path, journal)
                if not rollback_errors:
                    _archive_rolled_back_journal(
                        project_root, journal_path, journal
                    )
            except Exception:  # pragma: no cover - original and rollback errors are more useful
                pass
            if rollback_errors:
                raise RecoveryError("recovery_failed_rollback_incomplete") from error
            if isinstance(error, RecoveryError):
                raise
            raise RecoveryError(f"recovery_transaction_rolled_back:{error.__class__.__name__}") from error

    plan.update({
        "status": "recovered",
        "applied": True,
        "journalPath": journal_path.relative_to(project_root).as_posix(),
        "backupDirectory": backup_dir.relative_to(project_root).as_posix(),
    })
    return plan


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--mission-id", required=True)
    parser.add_argument("--apply", action="store_true")
    for name in ALL_HASH_NAMES:
        parser.add_argument(f"--expected-{name}-sha256")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    expected = {
        name: getattr(args, f"expected_{name}_sha256")
        for name in ALL_HASH_NAMES
    }
    try:
        result = recover_radar_contract_result(
            args.project_root,
            args.mission_id,
            apply=args.apply,
            expected_hashes=expected if args.apply else None,
        )
    except RecoveryError as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
