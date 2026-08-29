"""Trusted equipment-to-Custom-Plugin workflow profiles for the local bridge.

The browser never supplies these values.  They are loaded from the checked-in
contract so a dashboard intent can be enriched with a Backend-owned procedure,
default inputs, expected outputs, and evidence requirements.
"""

from __future__ import annotations

import copy
import json
import re
import threading
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_MAP_PATH = PROJECT_ROOT / "contracts" / "workflows" / "equipment-plugin-map.json"
AUTOMATION_MODES = {
    "scheduled_read_only",
    "mission_on_demand",
    "mission_interactive",
    "local_read_only",
    "settings_only",
}
PROCEDURE_KINDS = {"custom_plugin_skill", "backend_procedure"}
REVIEWED_EVIDENCE_KINDS = {
    "28_pair_rows",
    "acceptance_criteria",
    "adapter_status_truth",
    "at_least_two_source_urls",
    "backend_observed_at",
    "backtest_plan",
    "baseline_reference",
    "change_summary",
    "checked_at",
    "compile_status_truth",
    "discovery_blueprint",
    "ea_readiness",
    "frontend_safe_candidate_registry",
    "inspection_scope",
    "limitations",
    "local_health_snapshot",
    "local_settings_record",
    "local_terminal_selection_record",
    "no_unverified_profit_claim",
    "overfit_guard",
    "parameter_plan",
    "project_relative_source_path",
    "public_availability_status",
    "published_or_event_time",
    "quoted_fact_summary",
    "rejection_criteria",
    "review_scope",
    "scheduler_state",
    "source_digest",
    "source_reference",
    "source_title",
    "source_url",
    "source_url_per_supported_bias",
    "uncompiled_status",
    "unknown_when_unverified",
    "updated_at",
}
REVIEWED_COMPLETION_EVIDENCE_KINDS = {
    "binary_file",
    "html_report",
    "optimization_settings",
    "report",
    "result_report",
    "screenshots",
    "set_files",
    "terminal_identity",
    "tester_log",
    "tester_settings",
    "version_history",
    "visual_backtest",
    "visual_result_screenshot",
    "zero_compile_errors",
}
EVIDENCE_OUTPUT_ANY = {
    "28_pair_rows": {"pairBias"},
    "acceptance_criteria": {"acceptanceCriteria"},
    "backend_observed_at": {"checkedAt", "backendObservedAt"},
    "backtest_plan": {"testModel", "dateRange", "artifactPlan"},
    "change_summary": {"changeSummary"},
    "checked_at": {"checkedAt", "entries", "systems"},
    "compile_status_truth": {"compileStatus"},
    "discovery_blueprint": {"blueprint", "versionPlan"},
    "ea_readiness": {"eaReadiness", "entries"},
    "frontend_safe_candidate_registry": {"candidates", "candidateCount", "privacy"},
    "inspection_scope": {"strategySummary", "codeRisks", "tradeLifecycle", "moneyManagement"},
    "limitations": {"limitations", "knownRisks", "riskNotes", "conflictingEvidence", "systems"},
    "local_health_snapshot": {"bridgeStatus", "missionWorkerStatus", "schedulerStatus", "codexStatus"},
    "local_settings_record": {"savedAt", "times", "language", "requestedEnabled"},
    "local_terminal_selection_record": {"selectedCandidate", "selectedAt"},
    "no_unverified_profit_claim": {"expectedTradeoffs", "validationPlan", "rejectionCriteria"},
    "overfit_guard": {"overfitGuards", "validationSplit"},
    "parameter_plan": {"parameterRanges", "startStepStop", "nextRanges"},
    "project_relative_source_path": {"sourceFiles", "changedFiles", "sourcePath", "downloadArtifacts"},
    "public_availability_status": {"availability", "entries"},
    "published_or_event_time": {"publishedAt", "eventAt", "events", "sourceLinks"},
    "quoted_fact_summary": {"entryRules", "exitRules", "strategySummary", "featureSummary", "systems"},
    "rejection_criteria": {"rejectionCriteria"},
    "review_scope": {"issues", "lineReferences", "reviewScope"},
    "scheduler_state": {"effectiveEnabled", "nextRunAt", "lastRunStatus"},
    "source_digest": {"sourceDigest"},
    "source_title": {"sourceTitle", "entries", "systems"},
    "source_url_per_supported_bias": {"pairBias"},
    "uncompiled_status": {"compileChecklist", "compileStatus", "nextValidationStep"},
    "unknown_when_unverified": {"pairBias"},
    "updated_at": {"updatedAt"},
}
EVIDENCE_OUTPUT_ALL = {
    "frontend_safe_candidate_registry": {"candidates", "candidateCount", "privacy"},
    "local_health_snapshot": {
        "bridgeStatus",
        "missionWorkerStatus",
        "schedulerStatus",
        "codexStatus",
    },
    "local_terminal_selection_record": {"selectedCandidate", "selectedAt"},
}

RADAR_ACTION_ID = "discover_new_indicators"
TRADING_SYSTEM_DISCOVERY_ACTION_ID = "discover_trading_systems"
RADAR_ENTRY_WORKER_REQUIRED_FIELDS = {
    "toolName",
    "toolKind",
    "platform",
    "category",
    "version",
    "summaryTh",
    "sourceTitle",
    "sourceUrl",
    "publishedAt",
    "checkedAt",
    "verificationStatus",
    "availability",
    "eaReadiness",
    "missingRules",
    "sourceLimitations",
    "screenshot",
}
RADAR_ENTRY_BACKEND_COMPUTED_FIELDS = {
    "recordId",
    "duplicateFingerprint",
    "duplicateStatus",
    "duplicateScope",
}
TRADING_SYSTEM_WORKER_REQUIRED_FIELDS = {
    "recordType",
    "systemName",
    "strategyFamily",
    "creatorOrTrader",
    "publicUsers",
    "market",
    "symbols",
    "timeframes",
    "sessions",
    "indicatorSettings",
    "setupConditions",
    "entrySteps",
    "exitSteps",
    "riskManagement",
    "tradeManagementSteps",
    "sourceTitle",
    "sourceUrl",
    "corroboratingUrls",
    "checkedAt",
    "verificationStatus",
    "suitableFor",
    "risksAndLimitations",
    "unknowns",
}
TRADING_SYSTEM_BACKEND_COMPUTED_FIELDS = {
    "recordId",
    "duplicateFingerprint",
    "duplicateStatus",
    "duplicateScope",
}
NON_OUTPUT_EVIDENCE_KINDS = {
    "source_url",
    "at_least_two_source_urls",
    "source_reference",
    "baseline_reference",
    "adapter_status_truth",
}
_OUTPUT_FIELD_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,79}")
_EVIDENCE_KIND_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}")

_CACHE_LOCK = threading.RLock()
_CACHE_MTIME_NS: int | None = None
_CACHE_PAYLOAD: dict[str, Any] | None = None
_SKILL_INSTALL_CACHE: dict[str, dict[str, Any]] = {}


class EquipmentWorkflowContractError(RuntimeError):
    """Raised when the Backend-owned workflow contract is missing or unsafe."""


def _validated_payload(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict) or raw.get("version") != "equipment-plugin-map-v1":
        raise EquipmentWorkflowContractError("unsupported_equipment_plugin_map")
    security = raw.get("security")
    if not isinstance(security, dict):
        raise EquipmentWorkflowContractError("missing_equipment_plugin_security")
    required_security = {
        "frontendIntentOnly": True,
        "backendOwnsExecution": True,
        "credentialsAcceptedFromFrontend": False,
        "externalWritesDefault": False,
        "liveTradingAllowed": False,
    }
    if any(security.get(key) is not value for key, value in required_security.items()):
        raise EquipmentWorkflowContractError("unsafe_equipment_plugin_security")
    input_contract = raw.get("inputContract")
    if not isinstance(input_contract, dict):
        raise EquipmentWorkflowContractError("missing_equipment_input_contract")
    if (
        input_contract.get("acceptedFieldsSource")
        != "backend/local-runner/bridge_server.py:DASHBOARD_WORKFLOW_ACTIONS.formFields"
        or input_contract.get("integrationAcceptedFieldsSource")
        != "backend/local-runner/bridge_server.py:/api/integrations/metatrader/discover|select"
        or input_contract.get("inputPresetRole") != "trusted_defaults_only"
        or input_contract.get("frontendMaySubmitUnknownFields") is not False
    ):
        raise EquipmentWorkflowContractError("unsafe_equipment_input_contract")
    equipment = raw.get("equipment")
    if not isinstance(equipment, dict) or not equipment:
        raise EquipmentWorkflowContractError("missing_equipment_plugin_profiles")
    for prop_id, equipment_profile in equipment.items():
        if not isinstance(prop_id, str) or not prop_id or not isinstance(equipment_profile, dict):
            raise EquipmentWorkflowContractError("invalid_equipment_plugin_profile")
        actions = equipment_profile.get("actions")
        if not isinstance(actions, dict) or not actions:
            raise EquipmentWorkflowContractError(f"missing_equipment_actions:{prop_id}")
        for action_id, action_profile in actions.items():
            if not isinstance(action_id, str) or not isinstance(action_profile, dict):
                raise EquipmentWorkflowContractError(f"invalid_equipment_action:{prop_id}")
            if not str(action_profile.get("pluginSkillId") or "").strip():
                raise EquipmentWorkflowContractError(f"missing_plugin_skill:{prop_id}:{action_id}")
            if "|" in str(action_profile.get("pluginSkillId") or ""):
                raise EquipmentWorkflowContractError(f"compound_plugin_skill:{prop_id}:{action_id}")
            reference_skill_id = str(action_profile.get("referencePluginSkillId") or "").strip()
            reference_skill_version = str(action_profile.get("referencePluginVersion") or "").strip()
            if "|" in reference_skill_id:
                raise EquipmentWorkflowContractError(f"compound_reference_plugin_skill:{prop_id}:{action_id}")
            if bool(reference_skill_id) != bool(reference_skill_version):
                raise EquipmentWorkflowContractError(f"incomplete_reference_plugin:{prop_id}:{action_id}")
            procedure_kind = str(action_profile.get("procedureKind") or "custom_plugin_skill")
            if procedure_kind not in PROCEDURE_KINDS:
                raise EquipmentWorkflowContractError(f"invalid_procedure_kind:{prop_id}:{action_id}")
            candidates = action_profile.get("pluginCandidates", [])
            if not isinstance(candidates, list):
                raise EquipmentWorkflowContractError(f"invalid_plugin_candidates:{prop_id}:{action_id}")
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    raise EquipmentWorkflowContractError(f"invalid_plugin_candidate:{prop_id}:{action_id}")
                candidate_id = str(candidate.get("pluginSkillId") or "").strip()
                candidate_version = str(candidate.get("pluginVersion") or "").strip()
                candidate_procedure_kind = str(candidate.get("procedureKind") or "").strip()
                values = candidate.get("values")
                if not candidate_id or "|" in candidate_id or not isinstance(values, list) or not values:
                    raise EquipmentWorkflowContractError(f"invalid_plugin_candidate:{prop_id}:{action_id}")
                if not candidate_version:
                    raise EquipmentWorkflowContractError(
                        f"missing_candidate_plugin_version:{prop_id}:{action_id}"
                    )
                if candidate_procedure_kind not in PROCEDURE_KINDS:
                    raise EquipmentWorkflowContractError(
                        f"invalid_candidate_procedure_kind:{prop_id}:{action_id}"
                    )
                candidate_reference_id = str(candidate.get("referencePluginSkillId") or "").strip()
                candidate_reference_version = str(candidate.get("referencePluginVersion") or "").strip()
                if "|" in candidate_reference_id:
                    raise EquipmentWorkflowContractError(f"compound_candidate_reference_plugin:{prop_id}:{action_id}")
                if bool(candidate_reference_id) != bool(candidate_reference_version):
                    raise EquipmentWorkflowContractError(f"incomplete_candidate_reference_plugin:{prop_id}:{action_id}")
            if action_profile.get("automationMode") not in AUTOMATION_MODES:
                raise EquipmentWorkflowContractError(f"invalid_automation_mode:{prop_id}:{action_id}")
            action_kind = str(action_profile.get("actionKind") or "mission_action").strip()
            if action_kind not in {"mission_action", "integration_action"}:
                raise EquipmentWorkflowContractError(f"invalid_action_kind:{prop_id}:{action_id}")
            required_inputs = action_profile.get("requiredInputs", [])
            required_inputs_any = action_profile.get("requiredInputsAnyOf", [])
            for input_key, values in (
                ("requiredInputs", required_inputs),
                ("requiredInputsAnyOf", required_inputs_any),
            ):
                if not isinstance(values, list) or any(
                    _OUTPUT_FIELD_PATTERN.fullmatch(str(item or "").strip()) is None
                    for item in values
                ):
                    raise EquipmentWorkflowContractError(
                        f"invalid_{input_key}:{prop_id}:{action_id}"
                    )
            if action_kind == "integration_action":
                expected_integration_inputs = {
                    "discover_metatrader": [],
                    "select_metatrader_target": ["candidateId"],
                }.get(action_id)
                if expected_integration_inputs is None or required_inputs != expected_integration_inputs:
                    raise EquipmentWorkflowContractError(
                        f"invalid_integration_action_contract:{prop_id}:{action_id}"
                    )
            for key in ("inputPreset", "outputFields", "evidenceRequired"):
                expected = dict if key == "inputPreset" else list
                if not isinstance(action_profile.get(key), expected):
                    raise EquipmentWorkflowContractError(f"invalid_{key}:{prop_id}:{action_id}")
            output_fields = [str(item or "").strip() for item in action_profile["outputFields"]]
            evidence_kinds = [str(item or "").strip() for item in action_profile["evidenceRequired"]]
            if any(_OUTPUT_FIELD_PATTERN.fullmatch(item) is None for item in output_fields):
                raise EquipmentWorkflowContractError(f"invalid_output_field:{prop_id}:{action_id}")
            if len(set(output_fields)) != len(output_fields):
                raise EquipmentWorkflowContractError(f"duplicate_output_field:{prop_id}:{action_id}")
            if any(_EVIDENCE_KIND_PATTERN.fullmatch(item) is None for item in evidence_kinds):
                raise EquipmentWorkflowContractError(f"invalid_evidence_kind:{prop_id}:{action_id}")
            if len(set(evidence_kinds)) != len(evidence_kinds):
                raise EquipmentWorkflowContractError(f"duplicate_evidence_kind:{prop_id}:{action_id}")
            unsupported = set(evidence_kinds) - REVIEWED_EVIDENCE_KINDS
            if unsupported:
                raise EquipmentWorkflowContractError(
                    f"unsupported_evidence_kind:{prop_id}:{action_id}:{sorted(unsupported)[0]}"
                )
            output_field_set = set(output_fields)
            if action_id == RADAR_ACTION_ID:
                entry_contract = action_profile.get("entryContract")
                if output_fields != ["entries"] or not isinstance(entry_contract, dict):
                    raise EquipmentWorkflowContractError(
                        f"invalid_radar_entry_container:{prop_id}:{action_id}"
                    )
                if (
                    entry_contract.get("containerField") != "entries"
                    or entry_contract.get("minimumItemsPerRun") != 1
                    or not isinstance(entry_contract.get("maximumItemsPerRun"), int)
                    or not 1 <= entry_contract["maximumItemsPerRun"] <= 6
                    or set(entry_contract.get("workerRequiredFields") or [])
                    != RADAR_ENTRY_WORKER_REQUIRED_FIELDS
                    or set(entry_contract.get("backendComputedFields") or [])
                    != RADAR_ENTRY_BACKEND_COMPUTED_FIELDS
                ):
                    raise EquipmentWorkflowContractError(
                        f"invalid_radar_entry_contract:{prop_id}:{action_id}"
                    )
            if action_id == TRADING_SYSTEM_DISCOVERY_ACTION_ID:
                entry_contract = action_profile.get("entryContract")
                if output_fields != ["systems"] or not isinstance(entry_contract, dict):
                    raise EquipmentWorkflowContractError(
                        f"invalid_trading_system_container:{prop_id}:{action_id}"
                    )
                if (
                    entry_contract.get("containerField") != "systems"
                    or entry_contract.get("minimumItemsPerRun") != 3
                    or entry_contract.get("maximumItemsPerRun") != 3
                    or set(entry_contract.get("workerRequiredFields") or [])
                    != TRADING_SYSTEM_WORKER_REQUIRED_FIELDS
                    or set(entry_contract.get("backendComputedFields") or [])
                    != TRADING_SYSTEM_BACKEND_COMPUTED_FIELDS
                ):
                    raise EquipmentWorkflowContractError(
                        f"invalid_trading_system_entry_contract:{prop_id}:{action_id}"
                    )
            for evidence_kind in evidence_kinds:
                required_any = EVIDENCE_OUTPUT_ANY.get(evidence_kind)
                if required_any is not None and not output_field_set.intersection(required_any):
                    raise EquipmentWorkflowContractError(
                        f"missing_evidence_prerequisite:{prop_id}:{action_id}:{evidence_kind}"
                    )
                required_all = EVIDENCE_OUTPUT_ALL.get(evidence_kind)
                if required_all is not None and not required_all.issubset(output_field_set):
                    raise EquipmentWorkflowContractError(
                        f"missing_evidence_prerequisite:{prop_id}:{action_id}:{evidence_kind}"
                    )
            completion_evidence = action_profile.get("completionEvidenceRequired", [])
            if not isinstance(completion_evidence, list):
                raise EquipmentWorkflowContractError(
                    f"invalid_completion_evidence:{prop_id}:{action_id}"
                )
            normalized_completion = [str(item or "").strip() for item in completion_evidence]
            if (
                any(_EVIDENCE_KIND_PATTERN.fullmatch(item) is None for item in normalized_completion)
                or len(set(normalized_completion)) != len(normalized_completion)
            ):
                raise EquipmentWorkflowContractError(
                    f"invalid_completion_evidence:{prop_id}:{action_id}"
                )
            unsupported_completion = (
                set(normalized_completion) - REVIEWED_COMPLETION_EVIDENCE_KINDS
            )
            if unsupported_completion:
                raise EquipmentWorkflowContractError(
                    f"unsupported_completion_evidence:{prop_id}:{action_id}:"
                    f"{sorted(unsupported_completion)[0]}"
                )
            if "adapter_status_truth" in evidence_kinds and not (
                str(action_profile.get("adapterStatus") or "").strip()
                or "adapterStatus" in output_field_set
            ):
                raise EquipmentWorkflowContractError(
                    f"missing_adapter_status_source:{prop_id}:{action_id}"
                )
            reference_evidence = {"source_reference", "baseline_reference"}.intersection(evidence_kinds)
            if reference_evidence:
                if action_profile.get("automationMode") == "scheduled_read_only":
                    raise EquipmentWorkflowContractError(
                        f"scheduled_action_requires_runtime_source:{prop_id}:{action_id}"
                    )
                declared_inputs = set(str(key) for key in action_profile["inputPreset"])
                for key in ("requiredInputs", "requiredInputsAnyOf"):
                    values = action_profile.get(key)
                    if isinstance(values, list):
                        declared_inputs.update(str(item) for item in values)
                if not any(
                    any(token in key.lower() for token in ("source", "report", "artifact", "path"))
                    for key in declared_inputs
                ):
                    raise EquipmentWorkflowContractError(
                        f"missing_runtime_source_input:{prop_id}:{action_id}"
                    )
        schedule = equipment_profile.get("schedule")
        if not isinstance(schedule, dict) or not isinstance(schedule.get("supported"), bool):
            raise EquipmentWorkflowContractError(f"invalid_equipment_schedule:{prop_id}")
        if schedule["supported"]:
            if schedule.get("timezone") != "Asia/Bangkok":
                raise EquipmentWorkflowContractError(f"invalid_schedule_timezone:{prop_id}")
            default_times = schedule.get("defaultTimes")
            schedule_actions = schedule.get("actions")
            manual_actions = schedule.get("manualOrAgentHandoffActions", [])
            direct_backend_handler = str(
                schedule.get("directBackendHandler") or ""
            ).strip()
            if (
                not isinstance(default_times, list)
                or not default_times
                or len(set(default_times)) != len(default_times)
                or any(
                    re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", str(item or "")) is None
                    for item in default_times
                )
            ):
                raise EquipmentWorkflowContractError(f"invalid_schedule_times:{prop_id}")
            if (
                not isinstance(schedule_actions, list)
                or not isinstance(manual_actions, list)
                or len(set(schedule_actions)) != len(schedule_actions)
                or len(set(manual_actions)) != len(manual_actions)
                or set(schedule_actions).intersection(manual_actions)
                or (
                    not schedule_actions
                    and not direct_backend_handler
                )
                or (
                    direct_backend_handler
                    and (schedule_actions or manual_actions)
                )
            ):
                raise EquipmentWorkflowContractError(f"invalid_schedule_actions:{prop_id}")
            if direct_backend_handler:
                direct_endpoints = equipment_profile.get("directEndpoints")
                if (
                    equipment_profile.get("serviceMode")
                    != "deterministic_backend_direct"
                    or equipment_profile.get("ownerAgentId") is not None
                    or equipment_profile.get("allowedActionIds") != []
                    or not isinstance(direct_endpoints, dict)
                    or not all(
                        str(direct_endpoints.get(key) or "").startswith(
                            "/api/props/"
                        )
                        for key in ("refresh", "schedule")
                    )
                ):
                    raise EquipmentWorkflowContractError(
                        f"invalid_direct_schedule_contract:{prop_id}"
                    )
            for scheduled_action_id in schedule_actions:
                scheduled_action = actions.get(str(scheduled_action_id or ""))
                if (
                    not isinstance(scheduled_action, dict)
                    or scheduled_action.get("automationMode") != "scheduled_read_only"
                ):
                    raise EquipmentWorkflowContractError(
                        f"invalid_scheduled_action:{prop_id}:{scheduled_action_id}"
                    )
            for manual_action_id in manual_actions:
                manual_action = actions.get(str(manual_action_id or ""))
                if (
                    not isinstance(manual_action, dict)
                    or manual_action.get("automationMode") == "scheduled_read_only"
                ):
                    raise EquipmentWorkflowContractError(
                        f"invalid_manual_schedule_action:{prop_id}:{manual_action_id}"
                    )
        elif not str(schedule.get("reasonTh") or "").strip():
            raise EquipmentWorkflowContractError(f"missing_schedule_reason:{prop_id}")
    return raw


def validate_equipment_workflow_contract() -> dict[str, Any]:
    """Run a fresh fail-closed preflight before the bridge opens a socket."""

    return load_equipment_plugin_map(force_reload=True)


def _installed_skill(skill_id: str) -> dict[str, Any]:
    """Resolve an installed Codex skill without exposing its local path."""

    normalized = str(skill_id or "").strip()
    if not normalized:
        return {"installed": False, "version": None}
    with _CACHE_LOCK:
        cached = _SKILL_INSTALL_CACHE.get(normalized)
        if cached is not None:
            return copy.deepcopy(cached)
    codex_home = Path.home() / ".codex"
    discovered: list[tuple[str, Path]] = []
    personal = codex_home / "skills" / normalized / "SKILL.md"
    if personal.is_file():
        discovered.append(("personal", personal))
    cache_root = codex_home / "plugins" / "cache"
    if cache_root.is_dir():
        try:
            plugin_roots = list(cache_root.iterdir())
        except OSError:
            plugin_roots = []
        for plugin_root in plugin_roots:
            skill_root = plugin_root / normalized
            if not skill_root.is_dir():
                continue
            try:
                version_dirs = list(skill_root.iterdir())
            except OSError:
                continue
            for version_dir in version_dirs:
                skill_file = version_dir / "skills" / normalized / "SKILL.md"
                if skill_file.is_file():
                    discovered.append((version_dir.name, skill_file))
    result = {
        "installed": bool(discovered),
        "version": sorted((version for version, _ in discovered), reverse=True)[0] if discovered else None,
    }
    with _CACHE_LOCK:
        _SKILL_INSTALL_CACHE[normalized] = copy.deepcopy(result)
    return result


def load_equipment_plugin_map(*, force_reload: bool = False) -> dict[str, Any]:
    """Load and validate the trusted contract, reloading when the file changes."""

    global _CACHE_MTIME_NS, _CACHE_PAYLOAD
    try:
        stat = PLUGIN_MAP_PATH.stat()
    except OSError as exc:
        raise EquipmentWorkflowContractError("equipment_plugin_map_unavailable") from exc
    with _CACHE_LOCK:
        if (
            not force_reload
            and _CACHE_PAYLOAD is not None
            and _CACHE_MTIME_NS == stat.st_mtime_ns
        ):
            return copy.deepcopy(_CACHE_PAYLOAD)
        try:
            raw = json.loads(PLUGIN_MAP_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise EquipmentWorkflowContractError("equipment_plugin_map_unreadable") from exc
        payload = _validated_payload(raw)
        _CACHE_PAYLOAD = copy.deepcopy(payload)
        _CACHE_MTIME_NS = stat.st_mtime_ns
        return copy.deepcopy(payload)


def equipment_profile(prop_id: str) -> dict[str, Any] | None:
    payload = load_equipment_plugin_map()
    profile = payload.get("equipment", {}).get(str(prop_id or "").strip())
    return copy.deepcopy(profile) if isinstance(profile, dict) else None


def equipment_action_profile(
    prop_id: str,
    action_id: str,
    selectors: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    profile = equipment_profile(prop_id)
    if not profile:
        return None
    action = profile.get("actions", {}).get(str(action_id or "").strip())
    if not isinstance(action, dict):
        return None
    result = copy.deepcopy(action)
    selection_field = str(result.get("pluginSelectionField") or "platform").strip()
    selection_value = str(
        (selectors or {}).get(selection_field)
        or (result.get("inputPreset") or {}).get(selection_field)
        or ""
    ).strip().lower()
    selected_candidate = None
    for candidate in result.get("pluginCandidates", []):
        values = {str(value or "").strip().lower() for value in candidate.get("values", [])}
        if selection_value and selection_value in values:
            selected_candidate = candidate
            break
    if selected_candidate:
        result["pluginSkillId"] = selected_candidate["pluginSkillId"]
        result["pluginVersion"] = selected_candidate.get("pluginVersion", result.get("pluginVersion"))
        result["procedureKind"] = selected_candidate.get("procedureKind", result.get("procedureKind", "custom_plugin_skill"))
        if "referencePluginSkillId" in selected_candidate:
            result["referencePluginSkillId"] = selected_candidate.get("referencePluginSkillId")
            result["referencePluginVersion"] = selected_candidate.get("referencePluginVersion")
        result["selectedBy"] = selection_field
        result["selectedValue"] = selection_value
    for candidate in result.get("pluginCandidates", []):
        candidate_reference_id = str(candidate.get("referencePluginSkillId") or "").strip()
        if not candidate_reference_id:
            continue
        candidate_reference = _installed_skill(candidate_reference_id)
        requested_candidate_reference_version = str(candidate.get("referencePluginVersion") or "").strip()
        candidate["referenceSkillInstalled"] = bool(candidate_reference.get("installed"))
        candidate["referenceInstalledVersion"] = candidate_reference.get("version")
        candidate["referenceVersionMatch"] = bool(
            candidate_reference.get("installed")
            and (
                not requested_candidate_reference_version
                or requested_candidate_reference_version == "installed"
                or requested_candidate_reference_version == candidate_reference.get("version")
            )
        )
    result["ownerAgentId"] = str(result.get("ownerAgentId") or profile.get("ownerAgentId") or "manager")
    result["equipmentTitleTh"] = str(profile.get("titleTh") or prop_id)
    result["contractVersion"] = "equipment-plugin-map-v1"
    procedure_kind = str(result.get("procedureKind") or "custom_plugin_skill")
    result["procedureKind"] = procedure_kind
    result["pluginInvocationMode"] = (
        "codex_skill_guided" if procedure_kind == "custom_plugin_skill" else "backend_owned_procedure"
    )
    if procedure_kind == "custom_plugin_skill":
        installed = _installed_skill(str(result.get("pluginSkillId") or ""))
        result["skillInstalled"] = bool(installed.get("installed"))
        result["installedVersion"] = installed.get("version")
        requested_version = str(result.get("pluginVersion") or "").strip()
        result["versionMatch"] = bool(
            installed.get("installed")
            and (
                not requested_version
                or requested_version == "installed"
                or requested_version == installed.get("version")
            )
        )
    else:
        result["skillInstalled"] = None
        result["installedVersion"] = None
        result["versionMatch"] = True
    reference_skill_id = str(result.get("referencePluginSkillId") or "").strip()
    if reference_skill_id:
        reference = _installed_skill(reference_skill_id)
        requested_reference_version = str(result.get("referencePluginVersion") or "").strip()
        result["referenceSkillInstalled"] = bool(reference.get("installed"))
        result["referenceInstalledVersion"] = reference.get("version")
        result["referenceVersionMatch"] = bool(
            reference.get("installed")
            and (
                not requested_reference_version
                or requested_reference_version == "installed"
                or requested_reference_version == reference.get("version")
            )
        )
    return result
