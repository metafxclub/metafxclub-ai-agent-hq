from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge(name: str = "backend_auto_safe_radar_bridge"):
    spec = importlib.util.spec_from_file_location(name, BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BackendAutoSafeRadarPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        self.bridge.DASHBOARD_WORKFLOW_SCHEDULER_STOP.clear()
        self.bridge.DASHBOARD_WORKFLOW_SCHEDULER_WAKE.clear()
        with self.bridge.RATE_LIMIT_LOCK:
            self.bridge.RATE_LIMIT_STATE.clear()
        self.bridge._invalidate_missions_read_cache()

    def runtime(self, temp_dir: str) -> ExitStack:
        root = Path(temp_dir)
        stack = ExitStack()
        stack.enter_context(mock.patch.object(self.bridge, "MISSIONS_PATH", root / "missions.json"))
        stack.enter_context(mock.patch.object(self.bridge, "AUDIT_PATH", root / "audit.jsonl"))
        stack.enter_context(mock.patch.object(self.bridge, "OPERATOR_MODE_PATH", root / "operator.json"))
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "DASHBOARD_WORKFLOW_SETTINGS_PATH",
                root / "dashboard-workflow-settings.json",
            )
        )
        self.bridge._invalidate_missions_read_cache()
        return stack

    def radar_context(
        self,
        *,
        query: str = "trend indicator",
        trigger_source: str = "schedule",
    ) -> tuple[dict, str, dict]:
        action = self.bridge.DASHBOARD_WORKFLOW_ACTIONS["discover_new_indicators"]
        form = self.bridge._sanitize_dashboard_workflow_form(
            action,
            {
                "query": query,
                "platform": "mt4",
                "category": "trend",
                "maxItems": 6,
            },
        )
        profile = self.bridge._trusted_workflow_plugin_profile(
            "left_audit_crystals",
            "discover_new_indicators",
            form,
        )
        context = self.bridge._dashboard_workflow_lineage(
            "left_audit_crystals",
            "discover_new_indicators",
            form,
            None,
            trigger_source=trigger_source,
            plugin_profile=profile,
        )
        prompt = self.bridge._workflow_prompt(
            "discover_new_indicators",
            form,
            None,
            profile,
        )
        return context, prompt, action

    def create_safe_radar(self, *, idempotency_key: str = "radar-safe-1") -> dict:
        context, prompt, action = self.radar_context()
        bangkok_date = self.bridge._dashboard_scheduler_local_now().strftime("%Y-%m-%d")
        scheduled_idempotency_key = (
            idempotency_key
            if idempotency_key.startswith("dashboard-schedule:")
            else f"dashboard-schedule:{idempotency_key}"
        )
        context["executionReservation"] = {
            "settingsKey": "indicatorScoutSchedule",
            "bangkokDate": bangkok_date,
            "slotKey": f"indicatorScoutSchedule:{bangkok_date}:0900",
            "maximumRunsPerDay": 1,
            "source": "schedule",
        }
        preferences = self.bridge._dashboard_workflow_execution_preferences(
            "discover_new_indicators",
            self.bridge.load_dashboard_workflow_settings(),
        )
        result = self.bridge.run_bridge_task(
            {
                "toolId": action["toolId"],
                "agentId": action["ownerAgentId"],
                "requester": action["ownerAgentId"],
                "targetId": "left_audit_crystals",
                "reportType": action["reportType"],
                "prompt": prompt,
                "idempotencyKey": scheduled_idempotency_key,
            },
            trusted_workflow_context=context,
            trusted_execution_preferences=preferences,
        )
        self.assertTrue(result["ok"], result)
        return result["mission"]

    def trading_system_evidence_artifact(self) -> tuple[dict, list[str]]:
        urls = [
            "https://alpha.example.com/system-one",
            "https://bravo.example.org/system-one",
            "https://charlie.example.net/system-two",
            "https://delta.example.com/system-two",
            "https://echo.example.org/system-three",
            "https://foxtrot.example.net/system-three",
        ]
        return (
            {
                "status": "completed",
                "summary": "sanitized test artifact",
                "evidence": [
                    {
                        "label": f"source-{index}",
                        "url": url,
                        "note": "public evidence",
                    }
                    for index, url in enumerate(urls, start=1)
                ],
                "systems": [{}, {}, {}],
            },
            urls,
        )

    def prepare_v6_portal_evidence_failure(
        self,
        project_root: Path,
    ) -> tuple[dict, list[str], str]:
        """Persist the exact bounded shape eligible for the one-time v7 repair."""

        today = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
        slot_key = f"discoverySchedule:{today}:0900"
        result = self.bridge.run_dashboard_workflow_action(
            "codex_mcp_portal",
            {
                "actionId": "discover_trading_systems",
                "form": {},
                "idempotencyKey": f"dashboard-schedule:{slot_key}",
            },
            trusted_trigger_source="schedule",
        )
        mission = result["mission"]
        previous_payload, previous_urls = self.trading_system_evidence_artifact()
        latest_urls = [
            "https://golf.example.com/system-one",
            "https://hotel.example.org/system-one",
            "https://india.example.net/system-two",
            "https://juliet.example.com/system-two",
            "https://kilo.example.org/system-three",
            "https://lima.example.net/system-three",
        ]
        latest_payload = copy.deepcopy(previous_payload)
        for row, url in zip(latest_payload["evidence"], latest_urls):
            row["url"] = url
        previous_reference = "data/runtime/codex-runs/v6-source.final.md"
        latest_reference = "data/runtime/codex-runs/v6-failed.final.md"
        for reference, payload in (
            (previous_reference, previous_payload),
            (latest_reference, latest_payload),
        ):
            path = project_root / reference
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )
        block = self.bridge._trading_system_evidence_candidate_block(
            previous_urls
        )
        self.assertIsNotNone(block)
        expected_evidence = [
            "source_url",
            "at_least_two_source_urls",
            "checked_at",
            "source_title",
            "quoted_fact_summary",
            "limitations",
        ]
        mission.update({
            "detail": f"{mission['detail'].rstrip()}\n\n{block}",
            "status": "failed",
            "phase": "auto_guarded_invalid_output",
            "workStatus": "invalid_output",
            "errorCode": "invalid_output",
            "completedAt": self.bridge.utc_now(),
            "attemptCount": 1,
            "reportIds": ["v6-evidence-open-report"],
            "artifactPath": latest_reference,
            "structuredOutputError": self.bridge.TRADING_SYSTEM_EVIDENCE_OPEN_ERROR,
            "webSearchUsed": True,
            "webSearchEvidenceVerified": False,
            "workflowOutputContract": {
                "applicable": True,
                "valid": False,
                "failureCode": "trading_system_output_contract_invalid",
                "procedureId": self.bridge.TRADING_SYSTEM_WORKFLOW_PROCEDURE_ID,
                "expectedFields": ["systems"],
                "providedFields": [],
                "missingFields": ["systems"],
                "expectedEvidenceKinds": expected_evidence,
                "providedEvidenceKinds": [],
                "missingEvidenceKinds": expected_evidence,
                "entryErrors": ["systems_not_array"],
                "oversizedFields": [],
                "contractValueChars": 0,
                "sourceUrlCount": 0,
            },
            "outputContractRepair": {
                "version": 6,
                "kind": "trading_system_evidence_open_corrective_retry",
                "previous": {
                    "priorRepair": {
                        "version": 5,
                        "kind": "trading_system_structured_empty_arrays",
                    },
                },
            },
            "correctiveRetry": {
                "schemaVersion": "scheduled-corrective-retry-v1",
                "version": 1,
                "kind": self.bridge.TRADING_SYSTEM_EVIDENCE_CORRECTIVE_RETRY_KIND,
                "attemptCount": 1,
                "maximumAttempts": 1,
                "sourceArtifact": previous_reference,
                "candidateUrlCount": 6,
                "candidateUrlDigest": self.bridge.payload_digest(previous_urls),
                "automaticRetry": True,
                "scheduleSlotPreserved": True,
                "newDailyReservation": False,
                "newReport": False,
            },
        })
        mission["execution"].update({
            "dispatchState": "failed",
            "processStarted": True,
            "workingDirectory": "workspace",
            "writeRoots": [],
            "controlPlaneWritable": False,
            "webSearchEnabled": True,
            "webSearchMode": "live",
            "webSearchUsed": True,
            "webSearchEvidenceVerified": False,
            "automaticRetry": False,
        })
        self.bridge.replace_mission(mission)
        self.bridge._dashboard_workflow_update_schedule_state(
            "discoverySchedule",
            {
                "requestedEnabled": True,
                "lastMissionId": mission["id"],
                "lastAttemptSlotKey": slot_key,
                "lastSlotKey": slot_key,
                "dailyExecutionDate": today,
                "dailyExecutionCount": 1,
                "dailyExecutionSlotKeys": [slot_key],
            },
        )
        return mission, latest_urls, slot_key

    def queue_required_open_mission(
        self,
        project_root: Path,
        repair_level: str,
    ) -> tuple[dict, list[str], str]:
        """Build a runnable corrective-only v6 or trusted-prompt v7 Mission."""

        mission, urls, slot_key = self.prepare_v6_portal_evidence_failure(
            project_root
        )
        if repair_level == "v7":
            self.assertEqual(
                self.bridge.reconcile_current_day_public_research_output_repairs(),
                1,
            )
            return self.bridge.find_mission(mission["id"]), urls, slot_key
        self.assertEqual(repair_level, "v6")
        queued = self.bridge.find_mission(mission["id"])
        now_text = self.bridge.utc_now()
        queued.update({
            "status": "queued",
            "phase": "auto_guarded_corrective_retry_queued",
            "workStatus": "queued",
            "errorCode": None,
            "runnerStatus": None,
            "result": "",
            "startedAt": None,
            "completedAt": None,
            "updatedAt": now_text,
            "heartbeatAt": now_text,
            "attemptCount": 0,
            "reportIds": [],
            "autoQueuedAt": now_text,
            "execution": {},
        })
        queued["approval"] = self.bridge._not_required_approval_record()
        queued["requiresHumanApproval"] = False
        self.bridge._issue_backend_auto_safe_authorization(
            queued,
            issued_at=now_text,
        )
        queued["execution"].update({
            "automaticRetry": True,
            "correctiveRetryKind": (
                self.bridge.TRADING_SYSTEM_EVIDENCE_CORRECTIVE_RETRY_KIND
            ),
        })
        self.bridge.replace_mission(queued)
        self.assertEqual(
            self.bridge._trading_system_required_open_urls_for_mission(queued),
            (urls, None),
        )
        return queued, urls, slot_key

    def trading_system_evidence_open_failure_receipt(self) -> dict:
        expected_evidence = [
            "source_url",
            "at_least_two_source_urls",
            "checked_at",
            "source_title",
            "quoted_fact_summary",
            "limitations",
        ]
        return {
            "applicable": True,
            "valid": False,
            "failureCode": "trading_system_output_contract_invalid",
            "procedureId": self.bridge.TRADING_SYSTEM_WORKFLOW_PROCEDURE_ID,
            "expectedFields": ["systems"],
            "providedFields": [],
            "missingFields": ["systems"],
            "expectedEvidenceKinds": expected_evidence,
            "providedEvidenceKinds": [],
            "missingEvidenceKinds": expected_evidence,
            "entryErrors": ["systems_not_array"],
            "oversizedFields": [],
            "contractValueChars": 0,
            "sourceUrlCount": 0,
        }

    def persist_evidence_open_failure(
        self,
        mission: dict,
        *,
        report_id: str,
        artifact_reference: str = "data/runtime/codex-runs/v6-failed.final.md",
    ) -> dict:
        failed = copy.deepcopy(mission)
        failed.update({
            "status": "failed",
            "phase": "auto_guarded_invalid_output",
            "workStatus": "invalid_output",
            "errorCode": "invalid_output",
            "attemptCount": 1,
            "reportIds": [report_id],
            "artifactPath": artifact_reference,
            "structuredOutputError": self.bridge.TRADING_SYSTEM_EVIDENCE_OPEN_ERROR,
            "workflowOutputContract": (
                self.trading_system_evidence_open_failure_receipt()
            ),
            "webSearchUsed": True,
            "webSearchEvidenceVerified": False,
        })
        failed["execution"].update({
            "dispatchState": "failed",
            "processStarted": True,
            "workingDirectory": "workspace",
            "writeRoots": [],
            "controlPlaneWritable": False,
            "webSearchEnabled": True,
            "webSearchMode": "live",
            "webSearchUsed": True,
            "webSearchEvidenceVerified": False,
            "automaticRetry": False,
        })
        self.bridge.replace_mission(failed)
        return failed

    def requeue_v6_for_dispatch(self, mission: dict) -> dict:
        """Restore the exact queued v6 shape used before the v7 startup repair."""

        queued = copy.deepcopy(mission)
        queued_at = self.bridge.utc_now()
        queued.update({
            "status": "queued",
            "phase": "auto_guarded_corrective_retry_queued",
            "workStatus": "queued",
            "errorCode": None,
            "runnerStatus": None,
            "result": "",
            "blockedCapability": "",
            "startedAt": None,
            "completedAt": None,
            "updatedAt": queued_at,
            "heartbeatAt": queued_at,
            "attemptCount": 0,
            "reportIds": [],
            "evidence": [],
            "workflowOutputContract": None,
            "artifactPath": None,
            "structuredOutputError": None,
            "webSearchUsed": False,
            "webSearchEvidenceVerified": False,
            "modelTier": "manager_quality",
            "approval": self.bridge._not_required_approval_record(),
            "requiresHumanApproval": False,
            "autoQueuedAt": queued_at,
            "execution": {},
        })
        budget = copy.deepcopy(queued.get("budget") or {})
        budget.update({
            "rateReservePercent": self.bridge.AUTOMATION_MIN_REMAINING_PERCENT,
            "timeoutSeconds": 300,
            "outputLimitChars": 20000,
        })
        queued["budget"] = budget
        self.bridge._issue_backend_auto_safe_authorization(
            queued,
            issued_at=queued_at,
        )
        queued["execution"].update({
            "automaticRetry": True,
            "correctiveRetryKind": (
                self.bridge.TRADING_SYSTEM_EVIDENCE_CORRECTIVE_RETRY_KIND
            ),
        })
        self.bridge.replace_mission(queued)
        return queued

    def test_trusted_radar_is_backend_auto_safe_without_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission = self.create_safe_radar()
            public = self.bridge.mission_read_model_item(mission)

        self.assertEqual(mission["status"], "queued")
        self.assertFalse(mission["requiresHumanApproval"])
        self.assertEqual(mission["approval"]["state"], "not_required")
        self.assertFalse(mission["approval"]["required"])
        self.assertEqual(mission["budget"]["outputLimitChars"], 20000)
        self.assertEqual(mission["budget"]["timeoutSeconds"], 600)
        self.assertEqual(mission["budget"]["rateReservePercent"], 15)
        self.assertEqual(public["automaticPolicy"], {
            "mode": "backend_auto_safe",
            "decision": "allowed",
            "reason": "routine_internal_or_read_only",
            "version": "backend-auto-safe-v1",
            "humanApprovalRequired": False,
        })
        self.assertIsNone(
            self.bridge.auto_execution_authorization_error(
                mission,
                require_operator_mode=False,
            )
        )

    def test_public_research_frontend_runs_are_blocked_before_mission_creation(self) -> None:
        cases = (
            ("codex_mcp_portal", "discover_trading_systems"),
            ("left_audit_crystals", "discover_new_indicators"),
        )
        for prop_id, action_id in cases:
            with self.subTest(action_id=action_id), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                with self.assertRaises(self.bridge.RequestError) as blocked:
                    self.bridge.run_dashboard_workflow_action(
                        prop_id,
                        {
                            "actionId": action_id,
                            "form": {},
                            "idempotencyKey": f"frontend-{action_id}",
                        },
                        trusted_trigger_source="frontend",
                    )
                self.assertEqual(blocked.exception.status, 403)
                self.assertEqual(str(blocked.exception), "backend_owned_schedule_only")
                self.assertEqual(self.bridge.load_missions(), [])

    def test_safe_scheduled_portal_submission_remains_no_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            result = self.bridge.run_dashboard_workflow_action(
                "codex_mcp_portal",
                {
                    "actionId": "discover_trading_systems",
                    "form": {},
                    "idempotencyKey": "dashboard-schedule:portal-safe-no-approval",
                },
                trusted_trigger_source="schedule",
            )
            mission = result["mission"]

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["kind"], "mission_auto_queued")
        self.assertEqual(mission["status"], "queued")
        self.assertTrue(mission["autoEligible"])
        self.assertFalse(mission["requiresHumanApproval"])
        self.assertFalse(mission["approval"]["required"])
        self.assertEqual(mission["approval"]["state"], "not_required")
        self.assertIn("role ใช้ได้เฉพาะ trader/author/developer", mission["detail"])
        self.assertIn("ถ้าหาชื่อพร้อมหลักฐานไม่ได้ให้ข้ามระบบนั้น", mission["detail"])
        self.assertNotIn("name=null", mission["detail"])

    def test_backend_only_preset_tampering_fails_trusted_intent_guard(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            result = self.bridge.run_dashboard_workflow_action(
                "codex_mcp_portal",
                {
                    "actionId": "discover_trading_systems",
                    "form": {},
                    "idempotencyKey": "dashboard-schedule:portal-preset-tamper",
                },
                trusted_trigger_source="schedule",
            )
            mission = result["mission"]
            tampered = copy.deepcopy(mission)
            inputs = tampered["workflowContext"]["inputs"]
            inputs["sourcePolicy"] = "external_write"
            tampered["workflowContext"]["inputDigest"] = self.bridge.payload_digest(
                "dashboard-workflow-input-v1",
                "codex_mcp_portal",
                "discover_trading_systems",
                json.dumps(inputs, ensure_ascii=False, sort_keys=True),
            )

        self.assertEqual(json.loads(self.bridge._trusted_workflow_guard_intent(mission)), {})
        self.assertIsNone(self.bridge._trusted_workflow_guard_intent(tampered))
        self.assertFalse(
            self.bridge.auto_guarded_eligibility(
                tampered,
                require_operator_mode=False,
            )["eligible"]
        )

    def test_portal_user_high_impact_override_is_rejected_without_mission(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            with self.assertRaises(self.bridge.RequestError) as raised:
                self.bridge.run_dashboard_workflow_action(
                    "codex_mcp_portal",
                    {
                        "actionId": "discover_trading_systems",
                        "form": {"query": "deploy production and send token"},
                        "idempotencyKey": "dashboard-schedule:portal-high-impact-user-intent",
                    },
                    trusted_trigger_source="schedule",
                )
            missions = self.bridge.load_missions()

        self.assertEqual(raised.exception.status, 422)
        self.assertIn("read-only searches of public web pages", str(raised.exception))
        self.assertIn("no Mission was created", str(raised.exception))
        self.assertEqual(missions, [])

    def test_portal_out_of_scope_workspace_mutation_is_rejected_without_mission(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            with self.assertRaises(self.bridge.RequestError) as raised:
                self.bridge.run_dashboard_workflow_action(
                    "codex_mcp_portal",
                    {
                        "actionId": "discover_trading_systems",
                        "form": {"query": "edit the local source code file"},
                        "idempotencyKey": "dashboard-schedule:portal-out-of-scope-user-intent",
                    },
                    trusted_trigger_source="schedule",
                )
            missions = self.bridge.load_missions()

        self.assertEqual(raised.exception.status, 422)
        self.assertIn("read-only searches of public web pages", str(raised.exception))
        self.assertEqual(missions, [])

    def test_radar_high_impact_intent_is_rejected_before_daily_reservation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            with self.assertRaises(self.bridge.RequestError) as raised:
                self.bridge.run_dashboard_workflow_action(
                    "left_audit_crystals",
                    {
                        "actionId": "discover_new_indicators",
                        "form": {
                            "query": "deploy production and send token",
                            "platform": "any",
                            "category": "any",
                            "maxItems": 2,
                        },
                        "idempotencyKey": "dashboard-schedule:radar-malicious-1",
                    },
                    trusted_trigger_source="schedule",
                )
            settings = self.bridge.load_dashboard_workflow_settings()
            missions = self.bridge.load_missions()

        self.assertEqual(raised.exception.status, 422)
        self.assertIn("no Mission was created", str(raised.exception))
        self.assertEqual(missions, [])
        self.assertEqual(
            settings["indicatorScoutSchedule"]["dailyExecutionCount"],
            0,
        )

    def test_new_trusted_radar_cannot_auto_run_without_daily_reservation(self) -> None:
        context, prompt, action = self.radar_context()
        preferences = self.bridge._dashboard_workflow_execution_preferences(
            "discover_new_indicators",
            self.bridge._default_dashboard_workflow_settings(),
        )
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            result = self.bridge.run_bridge_task(
                {
                    "toolId": action["toolId"],
                    "agentId": action["ownerAgentId"],
                    "requester": "human",
                    "targetId": "left_audit_crystals",
                    "reportType": action["reportType"],
                    "prompt": prompt,
                    "idempotencyKey": "radar-missing-reservation",
                },
                trusted_workflow_context=context,
                trusted_execution_preferences=preferences,
            )
            missions = self.bridge.load_missions()

        self.assertFalse(result["ok"])
        self.assertEqual(result["kind"], "radar_execution_reservation_missing")
        self.assertEqual(result["_httpStatus"], 409)
        self.assertEqual(missions, [])

    def test_reservation_slot_shape_is_bound_to_trigger_source(self) -> None:
        scheduled, _prompt, _action = self.radar_context(trigger_source="schedule")
        scheduled["executionReservation"] = {
            "settingsKey": "indicatorScoutSchedule",
            "bangkokDate": "2026-08-14",
            "slotKey": "indicatorScoutSchedule:2026-08-14:0900",
            "maximumRunsPerDay": 1,
            "source": "schedule",
        }
        self.assertIsNotNone(self.bridge._workflow_context_storage(scheduled))

        schedule_with_manual_slot = copy.deepcopy(scheduled)
        schedule_with_manual_slot["executionReservation"]["slotKey"] = (
            "indicatorScoutSchedule:2026-08-14:manual-0000000000000000"
        )
        self.assertIsNone(
            self.bridge._workflow_context_storage(schedule_with_manual_slot)
        )

        manual_with_schedule_slot = copy.deepcopy(scheduled)
        manual_with_schedule_slot["triggerSource"] = "frontend"
        manual_with_schedule_slot["executionReservation"]["source"] = (
            "manual_or_backend"
        )
        self.assertIsNone(
            self.bridge._workflow_context_storage(manual_with_schedule_slot)
        )

    def test_automatic_policy_read_model_requires_coherent_digest_bound_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission = self.create_safe_radar(idempotency_key="radar-policy-shape")
            valid = self.bridge.mission_read_model_item(mission)

            manual = copy.deepcopy(mission)
            manual["executionMode"] = "manual_guarded"
            manual_policy = self.bridge.mission_read_model_item(manual)["automaticPolicy"]

            malformed = copy.deepcopy(mission)
            malformed["execution"]["schema"] = "other"
            malformed_policy = self.bridge.mission_read_model_item(malformed)["automaticPolicy"]

            tampered = copy.deepcopy(mission)
            tampered["detail"] += " tampered"
            tampered_policy = self.bridge.mission_read_model_item(tampered)["automaticPolicy"]

            contradictory = copy.deepcopy(mission)
            contradictory["requiresHumanApproval"] = False
            contradictory["approval"]["required"] = True
            contradictory["approval"]["state"] = "pending"
            contradictory_public = self.bridge.mission_read_model_item(contradictory)

        self.assertEqual(valid["automaticPolicy"]["mode"], "backend_auto_safe")
        self.assertEqual(manual_policy["mode"], "manual_guarded")
        self.assertEqual(malformed_policy["mode"], "manual_guarded")
        self.assertEqual(tampered_policy["mode"], "manual_guarded")
        self.assertTrue(contradictory_public["requiresHumanApproval"])
        self.assertEqual(contradictory_public["automaticPolicy"]["mode"], "human_review")

    def test_authorization_binds_workflow_and_idempotency_and_is_single_use(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission = self.create_safe_radar()
            persisted = self.bridge.find_mission(mission["id"])
            self.assertIsNone(
                self.bridge.auto_execution_authorization_error(
                    persisted,
                    require_operator_mode=False,
                )
            )
            changed_context = copy.deepcopy(persisted)
            changed_context["workflowContext"]["inputs"]["query"] = "other"
            self.assertEqual(
                self.bridge.auto_execution_authorization_error(
                    changed_context,
                    require_operator_mode=False,
                ),
                "auto_policy_digest_mismatch",
            )
            changed_key = copy.deepcopy(persisted)
            changed_key["idempotencyKey"] = "radar-safe-mutated"
            self.assertEqual(
                self.bridge.auto_execution_authorization_error(
                    changed_key,
                    require_operator_mode=False,
                ),
                "auto_policy_digest_mismatch",
            )
            changed_reservation_date = copy.deepcopy(persisted)
            changed_reservation_date["workflowContext"]["executionReservation"][
                "bangkokDate"
            ] = "2026-08-13"
            self.assertEqual(
                self.bridge.auto_execution_authorization_error(
                    changed_reservation_date,
                    require_operator_mode=False,
                ),
                "auto_policy_digest_mismatch",
            )
            changed_reservation_slot = copy.deepcopy(persisted)
            reservation_date = changed_reservation_slot["workflowContext"][
                "executionReservation"
            ]["bangkokDate"]
            changed_reservation_slot["workflowContext"]["executionReservation"][
                "slotKey"
            ] = f"indicatorScoutSchedule:{reservation_date}:manual-0000000000000000"
            self.assertEqual(
                self.bridge.auto_execution_authorization_error(
                    changed_reservation_slot,
                    require_operator_mode=False,
                ),
                "auto_policy_digest_mismatch",
            )
            changed_reservation_source = copy.deepcopy(persisted)
            changed_reservation_source["workflowContext"]["executionReservation"][
                "source"
            ] = "manual_or_backend"
            self.assertEqual(
                self.bridge.auto_execution_authorization_error(
                    changed_reservation_source,
                    require_operator_mode=False,
                ),
                "auto_policy_digest_mismatch",
            )
            invalid_calendar_date = copy.deepcopy(persisted)
            invalid_calendar_date["workflowContext"]["executionReservation"].update({
                "bangkokDate": "2026-99-99",
                "slotKey": "indicatorScoutSchedule:2026-99-99:manual-0000000000000000",
            })
            self.assertEqual(
                self.bridge.auto_execution_authorization_error(
                    invalid_calendar_date,
                    require_operator_mode=False,
                ),
                "auto_policy_digest_mismatch",
            )
            claimed = self.bridge.claim_auto_mission(mission["id"], "worker-one")
            second_claim = self.bridge.claim_auto_mission(mission["id"], "worker-two")

        self.assertIsNotNone(claimed)
        self.assertIsNotNone(claimed["execution"]["authorizationConsumedAt"])
        self.assertEqual(
            claimed["execution"]["authorizationConsumedLeaseId"],
            claimed["execution"]["leaseId"],
        )
        self.assertIsNone(second_claim)

    def test_frontend_run_is_denied_and_scheduler_owns_one_daily_slot_per_device(self) -> None:
        scheduler_now = datetime(
            2026,
            8,
            14,
            9,
            0,
            tzinfo=self.bridge.THAILAND_TIMEZONE,
        )
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            self.bridge.save_direct_daily_fx_news_schedule(
                {"enabled": False, "times": ["00:00", "12:00"]}
            )
            with self.assertRaises(self.bridge.RequestError) as blocked:
                self.bridge.run_dashboard_workflow_action(
                    "left_audit_crystals",
                    {
                        "actionId": "discover_new_indicators",
                        "form": {},
                        "idempotencyKey": "frontend-radar-denied",
                    },
                    trusted_trigger_source="frontend",
                )
            self.assertEqual(self.bridge.load_missions(), [])
            runner = mock.Mock(side_effect=lambda prop_id, payload, **_kwargs: {
                "ok": True,
                "kind": "mission_auto_queued",
                "mission": {
                    "id": f"scheduled-{prop_id}",
                    "status": "queued",
                    "requiresHumanApproval": False,
                },
                "idempotentReplay": False,
            })
            with mock.patch.object(
                self.bridge,
                "load_operator_mode_record",
                return_value={"mode": "auto_guarded"},
            ), mock.patch.object(
                self.bridge,
                "bridge_status",
                return_value={"codex": {"status": "ready"}},
            ), mock.patch.object(
                self.bridge,
                "mission_worker_read_model",
                return_value={"operational": True},
            ), mock.patch.object(
                self.bridge,
                "peek_codex_rate_limits",
                return_value=self.quota(16),
            ), mock.patch.object(
                self.bridge,
                "_dashboard_workflow_retry_ready",
                return_value=True,
            ), mock.patch.object(
                self.bridge,
                "run_dashboard_workflow_action",
                runner,
            ):
                first = self.bridge.dashboard_workflow_scheduler_tick(
                    scheduler_now,
                    refresh_quota=False,
                )
                second = self.bridge.dashboard_workflow_scheduler_tick(
                    scheduler_now.replace(minute=1),
                    refresh_quota=False,
                )
                duplicate = self.bridge.dashboard_workflow_scheduler_tick(
                    scheduler_now.replace(minute=2),
                    refresh_quota=False,
                )
            settings = self.bridge.load_dashboard_workflow_settings()

        self.assertEqual(blocked.exception.status, 403)
        self.assertEqual(str(blocked.exception), "backend_owned_schedule_only")
        self.assertTrue(first["dispatched"])
        self.assertTrue(second["dispatched"])
        self.assertFalse(duplicate["dispatched"])
        self.assertEqual(runner.call_count, 2)
        self.assertEqual(
            {call.args[0] for call in runner.call_args_list},
            {"codex_mcp_portal", "left_audit_crystals"},
        )
        for call in runner.call_args_list:
            self.assertEqual(call.kwargs["trusted_trigger_source"], "schedule")
            self.assertTrue(
                call.args[1]["idempotencyKey"].startswith("dashboard-schedule:")
            )
        for settings_key in ("discoverySchedule", "indicatorScoutSchedule"):
            schedule = settings[settings_key]
            self.assertEqual(schedule["dailyExecutionDate"], "2026-08-14")
            self.assertEqual(schedule["dailyExecutionCount"], 1)
            self.assertEqual(len(schedule["dailyExecutionSlotKeys"]), 1)

    def test_scheduled_definite_no_mission_releases_reservations(self) -> None:
        scheduler_now = datetime(
            2026,
            8,
            14,
            9,
            0,
            tzinfo=self.bridge.THAILAND_TIMEZONE,
        )
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            self.bridge.save_direct_daily_fx_news_schedule(
                {"enabled": False, "times": ["00:00", "12:00"]}
            )
            runner = mock.Mock(return_value={
                "ok": False,
                "kind": "guarded",
                "message": "no mission",
            })
            with mock.patch.object(
                self.bridge,
                "load_operator_mode_record",
                return_value={"mode": "auto_guarded"},
            ), mock.patch.object(
                self.bridge,
                "bridge_status",
                return_value={"codex": {"status": "ready"}},
            ), mock.patch.object(
                self.bridge,
                "mission_worker_read_model",
                return_value={"operational": True},
            ), mock.patch.object(
                self.bridge,
                "peek_codex_rate_limits",
                return_value=self.quota(16),
            ), mock.patch.object(
                self.bridge,
                "_dashboard_workflow_retry_ready",
                return_value=True,
            ), mock.patch.object(
                self.bridge,
                "run_dashboard_workflow_action",
                runner,
            ):
                result = self.bridge.dashboard_workflow_scheduler_tick(
                    scheduler_now,
                    refresh_quota=False,
                )
            settings = self.bridge.load_dashboard_workflow_settings()

        self.assertFalse(result["dispatched"])
        self.assertEqual(runner.call_count, 2)
        for settings_key in ("discoverySchedule", "indicatorScoutSchedule"):
            self.assertEqual(settings[settings_key]["dailyExecutionCount"], 0)
            self.assertEqual(settings[settings_key]["dailyExecutionSlotKeys"], [])

    def test_schedule_migration_enforces_backend_owned_enabled_nine_am(self) -> None:
        untouched = self.bridge._dashboard_workflow_settings_shape({})
        explicit = self.bridge._dashboard_workflow_settings_shape({
            "indicatorScoutSchedule": {
                "requestedEnabled": False,
                "times": ["07:00", "12:00"],
                "savedAt": "2026-08-13T10:00:00Z",
                "dailyExecutionCount": 1,
            }
        })

        self.assertTrue(untouched["indicatorScoutSchedule"]["requestedEnabled"])
        self.assertEqual(untouched["indicatorScoutSchedule"]["times"], ["09:00"])
        self.assertTrue(explicit["indicatorScoutSchedule"]["requestedEnabled"])
        self.assertEqual(explicit["indicatorScoutSchedule"]["times"], ["09:00"])
        self.assertEqual(
            explicit["indicatorScoutSchedule"]["timezone"],
            "Asia/Bangkok",
        )
        self.assertEqual(
            explicit["indicatorScoutSchedule"]["automaticDailyRadarVersion"],
            2,
        )
        self.assertEqual(
            explicit["indicatorScoutSchedule"]["savedAt"],
            "2026-08-13T10:00:00Z",
        )
        self.assertEqual(explicit["indicatorScoutSchedule"]["dailyExecutionCount"], 0)
        for saver in (
            self.bridge.save_dashboard_discovery_schedule,
            lambda form: self.bridge._save_dashboard_schedule_preference(
                "indicatorScoutSchedule",
                form,
            ),
        ):
            with self.assertRaises(self.bridge.RequestError) as disabled:
                saver({"enabled": False, "times": ["09:00"]})
            self.assertEqual(disabled.exception.status, 409)
            self.assertEqual(
                str(disabled.exception),
                "backend_owned_schedule_must_remain_enabled",
            )

    @staticmethod
    def quota(remaining: float, *, stale: bool = False, limit: bool = False) -> dict:
        return {
            "ok": True,
            "status": "ready",
            "primary": {"remainingPercent": remaining},
            "secondary": {"remainingPercent": remaining},
            "limitReached": limit,
            "stale": stale,
        }

    def test_all_scheduler_quota_gates_require_more_than_fifteen_percent(self) -> None:
        common = {
            "refresh_quota": False,
            "operator_mode": {"mode": "auto_guarded"},
            "bridge": {"codex": {"status": "ready"}},
            "mission_worker": {"operational": True},
            "settings": self.bridge._default_dashboard_workflow_settings(),
        }
        blocked = {
            settings_key: self.bridge._dashboard_workflow_scheduler_gate(
                **common,
                settings_key=settings_key,
                quota=self.quota(15),
            )
            for settings_key in ("indicatorScoutSchedule", "discoverySchedule")
        }
        allowed = {
            settings_key: self.bridge._dashboard_workflow_scheduler_gate(
                **common,
                settings_key=settings_key,
                quota=self.quota(16),
            )
            for settings_key in ("indicatorScoutSchedule", "discoverySchedule")
        }
        stale = self.bridge._dashboard_workflow_scheduler_gate(
            **common,
            settings_key="indicatorScoutSchedule",
            quota=self.quota(16, stale=True),
        )
        limited = self.bridge._dashboard_workflow_scheduler_gate(
            **common,
            settings_key="indicatorScoutSchedule",
            quota=self.quota(16, limit=True),
        )

        self.assertTrue(all(not result["allowed"] for result in blocked.values()))
        self.assertTrue(all(result["allowed"] for result in allowed.values()))
        self.assertEqual(
            {result["rateReservePercent"] for result in (*blocked.values(), *allowed.values())},
            {15},
        )
        self.assertFalse(stale["allowed"])
        self.assertFalse(limited["allowed"])

    def test_collaboration_quota_gate_ignores_stale_caller_thresholds(self) -> None:
        for stale_threshold in (40, 80):
            with self.subTest(stale_threshold=stale_threshold):
                config = {"minRemainingPercent": stale_threshold}
                allowed = self.bridge._collaboration_quota_gate(
                    config,
                    refresh=False,
                    quota=self.quota(16),
                )
                blocked = self.bridge._collaboration_quota_gate(
                    config,
                    refresh=False,
                    quota=self.quota(15),
                )

                self.assertTrue(allowed["allowed"], allowed)
                self.assertEqual(allowed["reason"], "ready")
                self.assertEqual(allowed["remainingPercent"], 16)
                self.assertFalse(blocked["allowed"], blocked)
                self.assertEqual(blocked["reason"], "quota_below_reserve")
                self.assertEqual(blocked["remainingPercent"], 15)
                self.assertIn("มากกว่า 15%", blocked["messageTh"])

    def test_quota_pause_does_not_burn_slots_and_recovery_dispatches_each_device_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            self.bridge.save_direct_daily_fx_news_schedule(
                {"enabled": False, "times": ["00:00", "12:00"]}
            )
            quota = {"value": self.quota(5)}
            runner = mock.Mock(side_effect=lambda prop_id, _payload, **_kwargs: {
                "ok": True,
                "kind": "mission_auto_queued",
                "mission": {
                    "id": f"quota-recovered-{prop_id}",
                    "status": "queued",
                },
                "idempotentReplay": False,
            })
            patches = (
                mock.patch.object(self.bridge, "load_missions", return_value=[]),
                mock.patch.object(self.bridge, "load_operator_mode_record", return_value={"mode": "auto_guarded"}),
                mock.patch.object(self.bridge, "bridge_status", return_value={"codex": {"status": "ready"}}),
                mock.patch.object(self.bridge, "mission_worker_read_model", return_value={"operational": True}),
                mock.patch.object(self.bridge, "peek_codex_rate_limits", side_effect=lambda: quota["value"]),
                mock.patch.object(self.bridge, "run_dashboard_workflow_action", runner),
                mock.patch.object(self.bridge, "_dashboard_workflow_retry_ready", return_value=True),
            )
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
                paused = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 14, 9, 0, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                before = self.bridge.load_dashboard_workflow_settings()
                quota["value"] = self.quota(26)
                portal = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 14, 9, 6, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                radar = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 14, 9, 7, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                duplicate = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 14, 9, 8, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                after = self.bridge.load_dashboard_workflow_settings()

        self.assertFalse(paused["dispatched"])
        for settings_key in ("discoverySchedule", "indicatorScoutSchedule"):
            self.assertEqual(before[settings_key]["dailyExecutionCount"], 0)
            self.assertEqual(before[settings_key]["dailyExecutionSlotKeys"], [])
        self.assertTrue(portal["dispatched"])
        self.assertTrue(radar["dispatched"])
        self.assertFalse(duplicate["dispatched"])
        self.assertEqual(runner.call_count, 2)
        self.assertEqual(
            {call.args[0] for call in runner.call_args_list},
            {"codex_mcp_portal", "left_audit_crystals"},
        )
        for settings_key in ("discoverySchedule", "indicatorScoutSchedule"):
            self.assertEqual(after[settings_key]["dailyExecutionCount"], 1)
            self.assertEqual(len(after[settings_key]["dailyExecutionSlotKeys"]), 1)

    def test_prior_day_scheduled_radar_is_terminal_before_any_runtime_probe(self) -> None:
        context, prompt, action = self.radar_context(trigger_source="schedule")
        context["executionReservation"] = {
            "settingsKey": "indicatorScoutSchedule",
            "bangkokDate": "2026-08-13",
            "slotKey": "indicatorScoutSchedule:2026-08-13:0900",
            "maximumRunsPerDay": 1,
            "source": "schedule",
        }
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            preferences = self.bridge._dashboard_workflow_execution_preferences(
                "discover_new_indicators",
                self.bridge.load_dashboard_workflow_settings(),
            )
            result = self.bridge.run_bridge_task(
                {
                    "toolId": action["toolId"],
                    "agentId": action["ownerAgentId"],
                    "requester": action["ownerAgentId"],
                    "targetId": "left_audit_crystals",
                    "reportType": action["reportType"],
                    "prompt": prompt,
                    "idempotencyKey": (
                        "dashboard-schedule:indicatorScoutSchedule:2026-08-13:0900"
                    ),
                },
                trusted_workflow_context=context,
                trusted_execution_preferences=preferences,
            )
            mission = result["mission"]
            runtime_probe = mock.Mock()
            with mock.patch.object(
                self.bridge,
                "_dashboard_scheduler_local_now",
                return_value=datetime(
                    2026,
                    8,
                    14,
                    0,
                    1,
                    tzinfo=self.bridge.THAILAND_TIMEZONE,
                ),
            ), mock.patch.object(self.bridge, "bridge_status", runtime_probe):
                self.bridge.process_auto_mission("worker-midnight", mission)
            finished = self.bridge.find_mission(mission["id"])

        runtime_probe.assert_not_called()
        self.assertEqual(finished["status"], "blocked")
        self.assertEqual(finished["errorCode"], "scheduled_radar_slot_expired")
        self.assertFalse(finished["execution"]["processStarted"])
        self.assertFalse(finished["execution"]["automaticRetry"])

    def test_scheduled_radar_worker_rechecks_fifteen_percent_reserve_before_process_start(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission = self.create_safe_radar(idempotency_key="radar-quota-race")
            runner = mock.Mock()
            with mock.patch.object(
                self.bridge,
                "bridge_status",
                return_value={"codex": {"status": "ready"}},
            ), mock.patch.object(
                self.bridge,
                "codex_rate_limits",
                return_value=self.quota(15),
            ), mock.patch.object(
                self.bridge,
                "_collaboration_quota_gate",
                return_value={"allowed": False, "reason": "quota_reserve"},
            ), mock.patch.object(self.bridge, "run_safe_command", runner):
                self.bridge.process_auto_mission("worker-scheduled-quota", mission)
            stored = self.bridge.find_mission(mission["id"])

        runner.assert_not_called()
        self.assertEqual(stored["status"], "queued")
        self.assertFalse(stored["execution"]["processStarted"])
        self.assertEqual(stored["execution"]["lastDeferredReason"], "quota_reserve")
        self.assertEqual(
            stored["workflowContext"]["executionReservation"]["maximumRunsPerDay"],
            1,
        )

    def test_prior_day_scheduled_radar_expiry_does_not_consume_next_day_slots(self) -> None:
        day_one = datetime(
            2026,
            8,
            13,
            8,
            0,
            tzinfo=self.bridge.THAILAND_TIMEZONE,
        )
        day_two = datetime(
            2026,
            8,
            14,
            9,
            0,
            tzinfo=self.bridge.THAILAND_TIMEZONE,
        )
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            self.bridge.save_direct_daily_fx_news_schedule(
                {"enabled": False, "times": ["00:00", "12:00"]}
            )
            with mock.patch.object(
                self.bridge,
                "_dashboard_scheduler_local_now",
                return_value=day_one,
            ):
                mission = self.create_safe_radar(
                    idempotency_key=(
                        "dashboard-schedule:"
                        "indicatorScoutSchedule:2026-08-13:0900"
                    )
                )
            runtime_probe = mock.Mock()
            with mock.patch.object(
                self.bridge,
                "_dashboard_scheduler_local_now",
                return_value=day_two,
            ), mock.patch.object(self.bridge, "bridge_status", runtime_probe):
                self.bridge.process_auto_mission("worker-scheduled-midnight", mission)
            expired = self.bridge.find_mission(mission["id"])

            scheduler_runner = mock.Mock(side_effect=lambda prop_id, _payload, **_kwargs: {
                "ok": True,
                "kind": "mission_auto_queued",
                "mission": {
                    "id": f"next-day-{prop_id}",
                    "status": "queued",
                },
                "idempotentReplay": False,
            })
            with mock.patch.object(
                self.bridge,
                "load_operator_mode_record",
                return_value={"mode": "auto_guarded"},
            ), mock.patch.object(
                self.bridge,
                "bridge_status",
                return_value={"codex": {"status": "ready"}},
            ), mock.patch.object(
                self.bridge,
                "mission_worker_read_model",
                return_value={"operational": True},
            ), mock.patch.object(
                self.bridge,
                "peek_codex_rate_limits",
                return_value=self.quota(26),
            ), mock.patch.object(
                self.bridge,
                "_dashboard_workflow_retry_ready",
                return_value=True,
            ), mock.patch.object(
                self.bridge,
                "run_dashboard_workflow_action",
                scheduler_runner,
            ):
                first = self.bridge.dashboard_workflow_scheduler_tick(
                    day_two,
                    refresh_quota=False,
                )
                second = self.bridge.dashboard_workflow_scheduler_tick(
                    day_two.replace(minute=1),
                    refresh_quota=False,
                )
                duplicate = self.bridge.dashboard_workflow_scheduler_tick(
                    day_two.replace(minute=2),
                    refresh_quota=False,
                )
            settings = self.bridge.load_dashboard_workflow_settings()

        runtime_probe.assert_not_called()
        self.assertEqual(expired["status"], "blocked")
        self.assertEqual(expired["errorCode"], "scheduled_radar_slot_expired")
        self.assertFalse(expired["execution"]["processStarted"])
        self.assertTrue(first["dispatched"])
        self.assertTrue(second["dispatched"])
        self.assertFalse(duplicate["dispatched"])
        self.assertEqual(scheduler_runner.call_count, 2)
        for settings_key in ("discoverySchedule", "indicatorScoutSchedule"):
            schedule = settings[settings_key]
            self.assertEqual(schedule["dailyExecutionDate"], "2026-08-14")
            self.assertEqual(schedule["dailyExecutionCount"], 1)

    def test_public_research_worker_commands_enforce_action_quality_and_read_only_boundaries(self) -> None:
        captured: list[list[str]] = []

        def fake_runner(command, **_kwargs):
            captured.append([str(item) for item in command])
            return {
                "ok": False,
                "exitCode": 1,
                "processStarted": False,
                "output": json.dumps({"ok": False, "status": "failed"}),
            }

        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            general_preferences = self.bridge._save_dashboard_agent_preferences({
                "modelTier": "risk_quality",
            })
            portal_result = self.bridge.run_dashboard_workflow_action(
                "codex_mcp_portal",
                {
                    "actionId": "discover_trading_systems",
                    "form": {},
                    "idempotencyKey": "dashboard-schedule:portal-sandbox",
                },
                trusted_trigger_source="schedule",
            )
            portal = portal_result["mission"]
            radar_date = self.bridge._dashboard_scheduler_local_now().strftime(
                "%Y-%m-%d"
            )
            radar = self.create_safe_radar(
                idempotency_key=(
                    f"indicatorScoutSchedule:{radar_date}:0900"
                )
            )
            ordinary = self.bridge.create_mission({
                "title": "Internal workspace review",
                "prompt": "Review the internal project notes and prepare a bounded report.",
                "agentId": "manager",
                "requester": "human",
                "toolId": "codex_cli_task",
                "targetId": "mission_strategy_table",
                "reportType": "mission_plan",
                "idempotencyKey": "ordinary-sandbox",
            })
            patches = (
                mock.patch.object(self.bridge, "bridge_status", return_value={"codex": {"status": "ready"}}),
                mock.patch.object(self.bridge, "codex_rate_limits", return_value=self.quota(80)),
                mock.patch.object(self.bridge, "_collaboration_quota_gate", return_value={"allowed": True, "reason": "ready"}),
                mock.patch.object(self.bridge, "check_rate_limit", return_value=(True, 0)),
                mock.patch.object(self.bridge, "run_safe_command", side_effect=fake_runner),
                mock.patch.object(self.bridge, "finish_auto_mission"),
                mock.patch.object(self.bridge, "heartbeat_auto_mission"),
                mock.patch.object(self.bridge, "update_mission_worker_state"),
                mock.patch.object(self.bridge, "invalidate_codex_rate_limit_cache"),
            )
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8]:
                self.bridge.process_auto_mission("worker-portal", portal)
                self.bridge.process_auto_mission("worker-radar", radar)
                self.bridge.process_auto_mission("worker-ordinary", ordinary)

        self.assertEqual(len(captured), 3)
        portal_command, radar_command, ordinary_command = captured
        self.assertEqual(general_preferences["modelTier"], "risk_quality")
        self.assertEqual(portal["modelTier"], "manager_quality")
        self.assertEqual(radar["modelTier"], "specialist_balanced")
        self.assertEqual(
            portal_command[portal_command.index("--model-tier") + 1],
            "manager_quality",
        )
        self.assertEqual(
            radar_command[radar_command.index("--model-tier") + 1],
            "specialist_balanced",
        )
        model_tiers = self.bridge.load_orchestration_contract()["modelTiers"]
        self.assertEqual(model_tiers["manager_quality"]["reasoningEffort"], "high")
        self.assertEqual(
            model_tiers["specialist_balanced"]["reasoningEffort"],
            "medium",
        )
        self.assertIn("--read-only-work", portal_command)
        self.assertEqual(
            portal_command[portal_command.index("--result-profile") + 1],
            "trading_system_discovery",
        )
        self.assertIn("--read-only-work", radar_command)
        self.assertEqual(
            radar_command[radar_command.index("--result-profile") + 1],
            "radar_website_tool",
        )
        self.assertNotIn("--read-only-work", ordinary_command)
        self.assertNotIn("--result-profile", ordinary_command)

    def test_current_day_exact_output_contract_bugs_requeue_once_without_new_reservation(self) -> None:
        today = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
        cases = (
            {
                "propId": "codex_mcp_portal",
                "actionId": "discover_trading_systems",
                "settingsKey": "discoverySchedule",
                "status": "failed",
                "errorCode": "trading_system_output_contract_invalid",
                "receipt": {
                    "valid": False,
                    "failureCode": "trading_system_output_contract_invalid",
                    "procedureId": self.bridge.TRADING_SYSTEM_WORKFLOW_PROCEDURE_ID,
                    "providedFields": [],
                    "missingFields": ["systems"],
                    "providedEvidenceKinds": [
                        "source_url",
                        "at_least_two_source_urls",
                        "checked_at",
                        "source_title",
                        "quoted_fact_summary",
                        "limitations",
                    ],
                    "missingEvidenceKinds": [
                        "checked_at",
                        "source_title",
                        "quoted_fact_summary",
                        "limitations",
                    ],
                    "entryErrors": ["systems_not_array"],
                    "oversizedFields": [],
                    "contractValueChars": 12000,
                    "sourceUrlCount": 9,
                },
            },
            {
                "propId": "left_audit_crystals",
                "actionId": "discover_new_indicators",
                "settingsKey": "indicatorScoutSchedule",
                "status": "blocked",
                "errorCode": "radar_output_contract_invalid",
                "receipt": {
                    "valid": False,
                    "failureCode": "radar_output_contract_invalid",
                    "procedureId": self.bridge.RADAR_WORKFLOW_PROCEDURE_ID,
                    "providedFields": ["entries"],
                    "missingFields": [],
                    "expectedEvidenceKinds": [
                        "source_url",
                        "source_title",
                        "checked_at",
                        "ea_readiness",
                        "public_availability_status",
                    ],
                    "providedEvidenceKinds": [],
                    "missingEvidenceKinds": [
                        "source_url",
                        "source_title",
                        "checked_at",
                        "ea_readiness",
                        "public_availability_status",
                    ],
                    "entryErrors": [],
                    "oversizedFields": [],
                    "contractValueChars": 4782,
                    "sourceUrlCount": 6,
                },
            },
        )
        for case in cases:
            with self.subTest(action=case["actionId"]), tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
                slot_key = f"{case['settingsKey']}:{today}:0900"
                result = self.bridge.run_dashboard_workflow_action(
                    case["propId"],
                    {
                        "actionId": case["actionId"],
                        "form": {},
                        "idempotencyKey": f"dashboard-schedule:{slot_key}",
                    },
                    trusted_trigger_source="schedule",
                )
                mission = result["mission"]
                mission["status"] = case["status"]
                mission["phase"] = f"auto_guarded_{case['errorCode']}"
                mission["workStatus"] = case["errorCode"]
                mission["errorCode"] = case["errorCode"]
                mission["completedAt"] = self.bridge.utc_now()
                mission["attemptCount"] = 1
                mission["reportIds"] = ["old-blocked-report"]
                mission["artifactPath"] = "data/runtime/codex-runs/old.final.md"
                mission["workflowOutputContract"] = copy.deepcopy(case["receipt"])
                mission["execution"].update({
                    "dispatchState": case["status"],
                    "processStarted": True,
                    "writeRoots": [],
                    "controlPlaneWritable": False,
                    "webSearchEnabled": True,
                    "webSearchUsed": True,
                    "webSearchEvidenceVerified": True,
                    "automaticRetry": False,
                })
                self.bridge.replace_mission(mission)
                self.bridge._dashboard_workflow_update_schedule_state(
                    case["settingsKey"],
                    {
                        "requestedEnabled": True,
                        "lastMissionId": mission["id"],
                        "lastAttemptSlotKey": slot_key,
                        "lastSlotKey": slot_key,
                        "lastRunStatus": case["status"],
                        "lastResultKind": "approval_required",
                        "dailyExecutionDate": today,
                        "dailyExecutionCount": 1,
                        "dailyExecutionSlotKeys": [slot_key],
                    },
                )

                self.assertEqual(
                    self.bridge.reconcile_current_day_public_research_output_repairs(),
                    1,
                )
                repaired = self.bridge.find_mission(mission["id"])
                schedule = self.bridge.load_dashboard_workflow_settings()[case["settingsKey"]]

                self.assertEqual(repaired["status"], "queued")
                self.assertEqual(repaired["approval"]["state"], "not_required")
                self.assertEqual(repaired["attemptCount"], 0)
                self.assertEqual(repaired["reportIds"], [])
                self.assertEqual(
                    repaired["outputContractRepair"]["version"],
                    self.bridge.PUBLIC_RESEARCH_OUTPUT_REPAIR_VERSION,
                )
                self.assertTrue(repaired["outputContractRepair"]["scheduleSlotPreserved"])
                self.assertFalse(repaired["outputContractRepair"]["newDailyReservation"])
                self.assertEqual(schedule["dailyExecutionCount"], 1)
                self.assertEqual(schedule["dailyExecutionSlotKeys"], [slot_key])
                self.assertEqual(schedule["lastResultKind"], "output_contract_repair_requeued")
                self.assertIsNone(
                    self.bridge.auto_execution_authorization_error(
                        repaired,
                        require_operator_mode=False,
                    )
                )
                self.assertEqual(
                    self.bridge.reconcile_current_day_public_research_output_repairs(),
                    0,
                )

    def test_scheduled_terminal_state_replaces_stale_dispatch_result_kind(self) -> None:
        today = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
        slot_key = f"indicatorScoutSchedule:{today}:0900"
        mission_id = "mission-schedule-terminal-sync"
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            context, _prompt, _action = self.radar_context(trigger_source="schedule")
            self.bridge._dashboard_workflow_update_schedule_state(
                "indicatorScoutSchedule",
                {
                    "requestedEnabled": True,
                    "lastMissionId": mission_id,
                    "lastAttemptSlotKey": slot_key,
                    "lastSlotKey": slot_key,
                    "lastRunStatus": "queued",
                    "lastResultKind": "approval_required",
                },
            )
            self.bridge._sync_scheduled_workflow_terminal_state({
                "id": mission_id,
                "status": "completed",
                "workStatus": "completed",
                "errorCode": None,
                "idempotencyKey": f"dashboard-schedule:{slot_key}",
                "workflowContext": context,
            })
            schedule = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]

        self.assertEqual(schedule["lastRunStatus"], "completed")
        self.assertEqual(schedule["lastResultKind"], "mission_completed")
        self.assertIsNone(schedule["lastError"])

    def test_v1_repair_schema_rejection_is_requeued_once_by_current_repair(self) -> None:
        today = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
        slot_key = f"discoverySchedule:{today}:0900"
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            result = self.bridge.run_dashboard_workflow_action(
                "codex_mcp_portal",
                {
                    "actionId": "discover_trading_systems",
                    "form": {},
                    "idempotencyKey": f"dashboard-schedule:{slot_key}",
                },
                trusted_trigger_source="schedule",
            )
            mission = result["mission"]
            mission.update({
                "status": "failed",
                "phase": "auto_guarded_invalid_runner_output",
                "workStatus": "invalid_runner_output",
                "errorCode": None,
                "completedAt": self.bridge.utc_now(),
                "attemptCount": 1,
                "reportIds": ["schema-rejected-report"],
                "artifactPath": None,
                "workflowOutputContract": {
                    "valid": False,
                    "providedFields": [],
                    "contractValueChars": 0,
                    "sourceUrlCount": 0,
                },
                "outputContractRepair": {
                    "version": 1,
                    "kind": "trading_system_truncated_nested_json",
                },
            })
            mission["execution"].update({
                "dispatchState": "failed",
                "processStarted": True,
                "writeRoots": [],
                "controlPlaneWritable": False,
                "webSearchEnabled": True,
                "webSearchUsed": False,
                "webSearchEvidenceVerified": False,
            })
            self.bridge.replace_mission(mission)
            self.bridge._dashboard_workflow_update_schedule_state(
                "discoverySchedule",
                {
                    "requestedEnabled": True,
                    "lastMissionId": mission["id"],
                    "lastAttemptSlotKey": slot_key,
                    "lastSlotKey": slot_key,
                },
            )

            self.assertEqual(
                self.bridge.reconcile_current_day_public_research_output_repairs(),
                1,
            )
            repaired = self.bridge.find_mission(mission["id"])

        self.assertEqual(repaired["status"], "queued")
        self.assertEqual(
            repaired["outputContractRepair"]["version"],
            self.bridge.PUBLIC_RESEARCH_OUTPUT_REPAIR_VERSION,
        )
        self.assertEqual(
            repaired["outputContractRepair"]["kind"],
            "structured_schema_keyword_unsupported",
        )
        self.assertEqual(
            repaired["outputContractRepair"]["previous"]["priorRepair"]["version"],
            1,
        )

    def test_v2_portal_transport_truncation_requeues_once_by_current_repair(self) -> None:
        today = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
        slot_key = f"discoverySchedule:{today}:0900"
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            result = self.bridge.run_dashboard_workflow_action(
                "codex_mcp_portal",
                {
                    "actionId": "discover_trading_systems",
                    "form": {},
                    "idempotencyKey": f"dashboard-schedule:{slot_key}",
                },
                trusted_trigger_source="schedule",
            )
            mission = result["mission"]
            mission.update({
                "status": "failed",
                "phase": "auto_guarded_invalid_runner_output",
                "workStatus": "invalid_runner_output",
                "errorCode": "invalid_runner_output",
                "completedAt": self.bridge.utc_now(),
                "attemptCount": 1,
                "reportIds": ["transport-truncated-report"],
                "artifactPath": None,
                "workflowOutputContract": {
                    "valid": False,
                    "providedFields": [],
                    "contractValueChars": 0,
                    "sourceUrlCount": 0,
                },
                "outputContractRepair": {
                    "version": 2,
                    "kind": "structured_schema_keyword_unsupported",
                    "previous": {
                        "priorRepair": {
                            "version": 1,
                            "kind": "trading_system_truncated_nested_json",
                        },
                    },
                },
            })
            mission["execution"].update({
                "dispatchState": "failed",
                "processStarted": True,
                "writeRoots": [],
                "controlPlaneWritable": False,
                "webSearchEnabled": True,
                "webSearchUsed": False,
                "webSearchEvidenceVerified": False,
            })
            self.bridge.replace_mission(mission)
            self.bridge._dashboard_workflow_update_schedule_state(
                "discoverySchedule",
                {
                    "requestedEnabled": True,
                    "lastMissionId": mission["id"],
                    "lastAttemptSlotKey": slot_key,
                    "lastSlotKey": slot_key,
                    "dailyExecutionDate": today,
                    "dailyExecutionCount": 1,
                    "dailyExecutionSlotKeys": [slot_key],
                },
            )

            self.assertEqual(
                self.bridge.reconcile_current_day_public_research_output_repairs(),
                1,
            )
            repaired = self.bridge.find_mission(mission["id"])
            schedule = self.bridge.load_dashboard_workflow_settings()[
                "discoverySchedule"
            ]
            second = self.bridge.reconcile_current_day_public_research_output_repairs()

        self.assertEqual(repaired["id"], mission["id"])
        self.assertEqual(repaired["status"], "queued")
        self.assertEqual(repaired["approval"]["state"], "not_required")
        self.assertEqual(
            repaired["outputContractRepair"]["version"],
            self.bridge.PUBLIC_RESEARCH_OUTPUT_REPAIR_VERSION,
        )
        self.assertEqual(
            repaired["outputContractRepair"]["kind"],
            "runner_response_duplicate_payload_truncated",
        )
        self.assertEqual(repaired["budget"]["rateReservePercent"], 15)
        self.assertEqual(repaired["budget"]["timeoutSeconds"], 600)
        self.assertEqual(repaired["budget"]["outputLimitChars"], 20000)
        self.assertEqual(schedule["lastMissionId"], mission["id"])
        self.assertEqual(schedule["dailyExecutionCount"], 1)
        self.assertEqual(schedule["dailyExecutionSlotKeys"], [slot_key])
        self.assertFalse(repaired["outputContractRepair"]["newDailyReservation"])
        self.assertEqual(second, 0)

    def test_v3_nested_system_string_truncation_requeues_once_by_current_same_slot(self) -> None:
        today = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
        slot_key = f"discoverySchedule:{today}:0900"
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            result = self.bridge.run_dashboard_workflow_action(
                "codex_mcp_portal",
                {
                    "actionId": "discover_trading_systems",
                    "form": {},
                    "idempotencyKey": f"dashboard-schedule:{slot_key}",
                },
                trusted_trigger_source="schedule",
            )
            mission = result["mission"]
            mission.update({
                "status": "blocked",
                "phase": "auto_guarded_trading_system_output_contract_invalid",
                "workStatus": "trading_system_output_contract_invalid",
                "errorCode": "trading_system_output_contract_invalid",
                "completedAt": self.bridge.utc_now(),
                "attemptCount": 1,
                "reportIds": ["nested-string-truncated-report"],
                "artifactPath": "data/runtime/codex-runs/nested-string-truncated.final.md",
                "workflowOutputContract": {
                    "valid": False,
                    "failureCode": "trading_system_output_contract_invalid",
                    "procedureId": self.bridge.TRADING_SYSTEM_WORKFLOW_PROCEDURE_ID,
                    "providedFields": [],
                    "missingFields": ["systems"],
                    "entryErrors": ["systems_not_array"],
                    "contractValueChars": 11999,
                    "sourceUrlCount": 2,
                },
                "outputContractRepair": {
                    "version": 3,
                    "kind": "runner_response_duplicate_payload_truncated",
                    "previous": {
                        "priorRepair": {
                            "version": 2,
                            "kind": "structured_schema_keyword_unsupported",
                        },
                    },
                },
            })
            mission["execution"].update({
                "dispatchState": "blocked",
                "processStarted": True,
                "writeRoots": [],
                "controlPlaneWritable": False,
                "webSearchEnabled": True,
                "webSearchUsed": True,
                "webSearchEvidenceVerified": True,
            })
            self.bridge.replace_mission(mission)
            self.bridge._dashboard_workflow_update_schedule_state(
                "discoverySchedule",
                {
                    "requestedEnabled": True,
                    "lastMissionId": mission["id"],
                    "lastAttemptSlotKey": slot_key,
                    "lastSlotKey": slot_key,
                    "dailyExecutionDate": today,
                    "dailyExecutionCount": 1,
                    "dailyExecutionSlotKeys": [slot_key],
                },
            )

            self.assertEqual(
                self.bridge.reconcile_current_day_public_research_output_repairs(),
                1,
            )
            repaired = self.bridge.find_mission(mission["id"])
            schedule = self.bridge.load_dashboard_workflow_settings()[
                "discoverySchedule"
            ]
            second = self.bridge.reconcile_current_day_public_research_output_repairs()

        self.assertEqual(repaired["id"], mission["id"])
        self.assertEqual(repaired["status"], "queued")
        self.assertEqual(
            repaired["outputContractRepair"]["version"],
            self.bridge.PUBLIC_RESEARCH_OUTPUT_REPAIR_VERSION,
        )
        self.assertEqual(
            repaired["outputContractRepair"]["kind"],
            "trading_system_nested_string_truncated",
        )
        self.assertEqual(schedule["dailyExecutionCount"], 1)
        self.assertEqual(schedule["dailyExecutionSlotKeys"], [slot_key])
        self.assertFalse(repaired["outputContractRepair"]["newDailyReservation"])
        self.assertEqual(second, 0)

    def test_v4_structured_empty_arrays_requeues_once_by_current_same_slot(self) -> None:
        today = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
        slot_key = f"discoverySchedule:{today}:0900"
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            result = self.bridge.run_dashboard_workflow_action(
                "codex_mcp_portal",
                {
                    "actionId": "discover_trading_systems",
                    "form": {},
                    "idempotencyKey": f"dashboard-schedule:{slot_key}",
                },
                trusted_trigger_source="schedule",
            )
            mission = result["mission"]
            mission.update({
                "status": "failed",
                "phase": "auto_guarded_invalid_output",
                "workStatus": "invalid_output",
                "errorCode": "invalid_output",
                "completedAt": self.bridge.utc_now(),
                "attemptCount": 1,
                "reportIds": ["structured-empty-arrays-report"],
                "artifactPath": "data/runtime/codex-runs/structured-empty-arrays.final.md",
                "workflowOutputContract": {
                    "valid": False,
                    "failureCode": "trading_system_output_contract_invalid",
                    "procedureId": self.bridge.TRADING_SYSTEM_WORKFLOW_PROCEDURE_ID,
                    "providedFields": [],
                    "missingFields": ["systems"],
                    "entryErrors": ["systems_not_array"],
                    "contractValueChars": 0,
                    "sourceUrlCount": 0,
                },
                "outputContractRepair": {
                    "version": 4,
                    "kind": "trading_system_nested_string_truncated",
                },
                # Model the currently persisted v4 Mission, which predates the
                # action-specific manager-quality Portal policy.
                "modelTier": "specialist_balanced",
            })
            mission["execution"].update({
                "dispatchState": "failed",
                "processStarted": True,
                "workingDirectory": "workspace",
                "writeRoots": [],
                "controlPlaneWritable": False,
                "webSearchEnabled": True,
                "webSearchUsed": True,
                "webSearchEvidenceVerified": False,
            })
            self.bridge.replace_mission(mission)
            self.bridge._dashboard_workflow_update_schedule_state(
                "discoverySchedule",
                {
                    "requestedEnabled": True,
                    "lastMissionId": mission["id"],
                    "lastAttemptSlotKey": slot_key,
                    "lastSlotKey": slot_key,
                    "dailyExecutionDate": today,
                    "dailyExecutionCount": 1,
                    "dailyExecutionSlotKeys": [slot_key],
                },
            )
            self.bridge.MISSION_WORKER_WAKE.clear()

            first = self.bridge.reconcile_current_day_public_research_output_repairs()
            repaired = self.bridge.find_mission(mission["id"])
            schedule = self.bridge.load_dashboard_workflow_settings()[
                "discoverySchedule"
            ]
            worker_woke = self.bridge.MISSION_WORKER_WAKE.is_set()
            second = self.bridge.reconcile_current_day_public_research_output_repairs()

        self.assertEqual(first, 1)
        self.assertEqual(repaired["id"], mission["id"])
        self.assertEqual(repaired["status"], "queued")
        self.assertEqual(repaired["approval"]["state"], "not_required")
        self.assertEqual(repaired["modelTier"], "manager_quality")
        self.assertEqual(
            repaired["outputContractRepair"]["version"],
            self.bridge.PUBLIC_RESEARCH_OUTPUT_REPAIR_VERSION,
        )
        self.assertEqual(
            repaired["outputContractRepair"]["kind"],
            "trading_system_structured_empty_arrays",
        )
        self.assertEqual(
            repaired["outputContractRepair"]["previous"]["priorRepair"]["version"],
            4,
        )
        self.assertEqual(schedule["lastMissionId"], mission["id"])
        self.assertEqual(schedule["dailyExecutionCount"], 1)
        self.assertEqual(schedule["dailyExecutionSlotKeys"], [slot_key])
        self.assertFalse(repaired["outputContractRepair"]["newDailyReservation"])
        self.assertTrue(worker_woke)
        self.assertEqual(second, 0)

    def test_v5_evidence_open_failure_requeues_same_slot_by_current_repair_with_candidate_block(self) -> None:
        today = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
        slot_key = f"discoverySchedule:{today}:0900"
        artifact_payload, urls = self.trading_system_evidence_artifact()
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            result = self.bridge.run_dashboard_workflow_action(
                "codex_mcp_portal",
                {
                    "actionId": "discover_trading_systems",
                    "form": {},
                    "idempotencyKey": f"dashboard-schedule:{slot_key}",
                },
                trusted_trigger_source="schedule",
            )
            mission = result["mission"]
            original_mission_id = mission["id"]
            original_authorization_id = mission["execution"]["authorizationId"]
            project_root = Path(temp_dir) / "project"
            runtime_root = project_root / "data" / "runtime"
            artifact_reference = (
                "data/runtime/codex-runs/v5-evidence-open.final.md"
            )
            artifact_path = project_root / artifact_reference
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(
                json.dumps(artifact_payload, ensure_ascii=False),
                encoding="utf-8",
            )
            mission.update({
                "status": "failed",
                "phase": "auto_guarded_invalid_output",
                "workStatus": "invalid_output",
                "errorCode": "invalid_output",
                "completedAt": self.bridge.utc_now(),
                "attemptCount": 1,
                "reportIds": ["v5-evidence-open-report"],
                "artifactPath": artifact_reference,
                "structuredOutputError": (
                    self.bridge.TRADING_SYSTEM_EVIDENCE_OPEN_ERROR
                ),
                "webSearchUsed": True,
                "webSearchEvidenceVerified": False,
                "workflowOutputContract": {
                    "applicable": True,
                    "valid": False,
                    "failureCode": "trading_system_output_contract_invalid",
                    "procedureId": (
                        self.bridge.TRADING_SYSTEM_WORKFLOW_PROCEDURE_ID
                    ),
                    "providedFields": [],
                    "missingFields": ["systems"],
                    "entryErrors": ["systems_not_array"],
                    "contractValueChars": 0,
                    "sourceUrlCount": 0,
                },
                "outputContractRepair": {
                    "version": 5,
                    "kind": "trading_system_structured_empty_arrays",
                    "previous": {
                        "priorRepair": {
                            "version": 4,
                            "kind": "trading_system_nested_string_truncated",
                        },
                    },
                },
            })
            mission["execution"].update({
                "dispatchState": "failed",
                "processStarted": True,
                "workingDirectory": "workspace",
                "writeRoots": [],
                "controlPlaneWritable": False,
                "webSearchEnabled": True,
                "webSearchUsed": True,
                "webSearchEvidenceVerified": False,
                "automaticRetry": False,
            })
            self.bridge.replace_mission(mission)
            self.bridge._dashboard_workflow_update_schedule_state(
                "discoverySchedule",
                {
                    "requestedEnabled": True,
                    "lastMissionId": mission["id"],
                    "lastAttemptSlotKey": slot_key,
                    "lastSlotKey": slot_key,
                    "dailyExecutionDate": today,
                    "dailyExecutionCount": 1,
                    "dailyExecutionSlotKeys": [slot_key],
                },
            )
            self.bridge.MISSION_WORKER_WAKE.clear()
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_root),
                mock.patch.object(self.bridge, "create_report") as create_report,
            ):
                first = (
                    self.bridge.reconcile_current_day_public_research_output_repairs()
                )
                repaired = self.bridge.find_mission(mission["id"])
                schedule = self.bridge.load_dashboard_workflow_settings()[
                    "discoverySchedule"
                ]
                worker_woke = self.bridge.MISSION_WORKER_WAKE.is_set()
                second = (
                    self.bridge.reconcile_current_day_public_research_output_repairs()
                )

            create_report.assert_not_called()

        self.assertEqual(first, 1)
        self.assertEqual(second, 0)
        self.assertEqual(repaired["id"], original_mission_id)
        self.assertEqual(repaired["status"], "queued")
        self.assertEqual(
            repaired["phase"],
            "auto_guarded_corrective_retry_queued",
        )
        self.assertEqual(repaired["approval"]["state"], "not_required")
        self.assertFalse(repaired["requiresHumanApproval"])
        self.assertNotEqual(
            repaired["execution"]["authorizationId"],
            original_authorization_id,
        )
        self.assertTrue(repaired["execution"]["automaticRetry"])
        self.assertEqual(repaired["budget"]["rateReservePercent"], 15)
        self.assertEqual(repaired["budget"]["timeoutSeconds"], 600)
        self.assertEqual(repaired["budget"]["outputLimitChars"], 20000)
        self.assertEqual(repaired["reportIds"], [])
        self.assertIsNone(repaired["artifactPath"])
        self.assertEqual(
            repaired["outputContractRepair"]["version"],
            self.bridge.PUBLIC_RESEARCH_OUTPUT_REPAIR_VERSION,
        )
        self.assertEqual(
            repaired["outputContractRepair"]["kind"],
            "trading_system_evidence_open_corrective_retry",
        )
        self.assertEqual(repaired["correctiveRetry"]["attemptCount"], 1)
        self.assertEqual(repaired["correctiveRetry"]["maximumAttempts"], 1)
        self.assertTrue(repaired["correctiveRetry"]["automaticRetry"])
        self.assertFalse(repaired["correctiveRetry"]["newDailyReservation"])
        self.assertFalse(repaired["correctiveRetry"]["newReport"])
        self.assertEqual(
            repaired["detail"].count(
                self.bridge.TRADING_SYSTEM_EVIDENCE_CANDIDATE_BLOCK_START
            ),
            1,
        )
        for url in urls:
            self.assertIn(url, repaired["detail"])
        self.assertEqual(schedule["lastMissionId"], original_mission_id)
        self.assertEqual(schedule["lastSlotKey"], slot_key)
        self.assertEqual(schedule["dailyExecutionCount"], 1)
        self.assertEqual(schedule["dailyExecutionSlotKeys"], [slot_key])
        self.assertEqual(
            schedule["lastResultKind"],
            "evidence_open_corrective_retry_requeued",
        )
        self.assertTrue(worker_woke)
        self.assertIsNone(
            self.bridge.auto_execution_authorization_error(
                repaired,
                require_operator_mode=False,
            )
        )

    def test_v6_evidence_open_failure_requeues_once_by_v7(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            project_root = Path(temp_dir) / "project"
            runtime_root = project_root / "data" / "runtime"
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_root),
                mock.patch.object(self.bridge, "create_report") as create_report,
            ):
                mission, latest_urls, slot_key = (
                    self.prepare_v6_portal_evidence_failure(project_root)
                )
                mission_id = mission["id"]
                first = self.bridge.reconcile_current_day_public_research_output_repairs()
                repaired = self.bridge.find_mission(mission_id)
                immediate_repeat = (
                    self.bridge.reconcile_current_day_public_research_output_repairs()
                )
                schedule = self.bridge.load_dashboard_workflow_settings()[
                    "discoverySchedule"
                ]

            create_report.assert_not_called()

        self.assertEqual(first, 1)
        self.assertEqual(immediate_repeat, 0)
        self.assertEqual(repaired["id"], mission_id)
        self.assertEqual(repaired["status"], "queued")
        self.assertEqual(
            repaired["phase"],
            "auto_guarded_trusted_prompt_repair_queued",
        )
        self.assertEqual(repaired["outputContractRepair"]["version"], 7)
        self.assertEqual(
            repaired["outputContractRepair"]["kind"],
            "trading_system_evidence_open_trusted_prompt_repair",
        )
        self.assertEqual(repaired["correctiveRetry"]["attemptCount"], 1)
        self.assertEqual(repaired["correctiveRetry"]["maximumAttempts"], 1)
        self.assertEqual(repaired["trustedPromptRepair"]["attemptCount"], 1)
        self.assertEqual(repaired["trustedPromptRepair"]["maximumAttempts"], 1)
        self.assertTrue(repaired["trustedPromptRepair"]["candidateBlockReplaced"])
        self.assertEqual(
            repaired["correctiveRetry"]["candidateUrlDigest"],
            self.bridge.payload_digest(latest_urls),
        )
        self.assertEqual(
            repaired["trustedPromptRepair"]["candidateUrlDigest"],
            self.bridge.payload_digest(latest_urls),
        )
        self.assertEqual(
            repaired["detail"].count(
                self.bridge.TRADING_SYSTEM_EVIDENCE_CANDIDATE_BLOCK_START
            ),
            1,
        )
        self.assertTrue(
            repaired["detail"].rstrip().endswith(
                self.bridge.TRADING_SYSTEM_EVIDENCE_CANDIDATE_BLOCK_END
            )
        )
        for url in latest_urls:
            self.assertIn(url, repaired["detail"])
        self.assertNotIn("https://alpha.example.com/system-one", repaired["detail"])
        self.assertEqual(repaired["modelTier"], "manager_quality")
        self.assertEqual(repaired["budget"]["rateReservePercent"], 15)
        self.assertFalse(repaired["approval"]["required"])
        self.assertEqual(repaired["reportIds"], [])
        self.assertEqual(schedule["lastMissionId"], mission_id)
        self.assertEqual(schedule["lastSlotKey"], slot_key)
        self.assertEqual(schedule["dailyExecutionCount"], 1)
        self.assertEqual(schedule["dailyExecutionSlotKeys"], [slot_key])
        self.assertEqual(schedule["lastResultKind"], "trusted_prompt_repair_requeued")
        self.assertIsNone(
            self.bridge.auto_execution_authorization_error(
                repaired,
                require_operator_mode=False,
            )
        )

    def test_v7_worker_passes_exact_six_digest_bound_required_open_urls(self) -> None:
        captured: list[str] = []
        single_slot_rate_check = mock.Mock(return_value=(True, 0))

        def fake_runner(command, **_kwargs):
            captured.extend(str(item) for item in command)
            return {
                "ok": False,
                "exitCode": 1,
                "processStarted": False,
                "output": json.dumps({"ok": False, "status": "failed"}),
            }

        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            project_root = Path(temp_dir) / "project"
            runtime_root = project_root / "data" / "runtime"
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_root),
            ):
                mission, latest_urls, _slot_key = (
                    self.prepare_v6_portal_evidence_failure(project_root)
                )
                self.assertEqual(
                    self.bridge.reconcile_current_day_public_research_output_repairs(),
                    1,
                )
                repaired = self.bridge.find_mission(mission["id"])
                rate_key = (
                    f"real:{repaired['owner']}:{repaired['toolId']}:"
                    f"{repaired['modelTier']}"
                )
                patches = (
                    mock.patch.object(self.bridge, "bridge_status", return_value={"codex": {"status": "ready"}}),
                    mock.patch.object(self.bridge, "codex_rate_limits", return_value=self.quota(80)),
                    mock.patch.object(self.bridge, "_collaboration_quota_gate", return_value={"allowed": True, "reason": "ready"}),
                    mock.patch.object(
                        self.bridge,
                        "check_rate_limit",
                        single_slot_rate_check,
                    ),
                    mock.patch.object(self.bridge, "run_safe_command", side_effect=fake_runner),
                    mock.patch.object(self.bridge, "finish_auto_mission"),
                    mock.patch.object(self.bridge, "heartbeat_auto_mission"),
                    mock.patch.object(self.bridge, "update_mission_worker_state"),
                    mock.patch.object(self.bridge, "invalidate_codex_rate_limit_cache"),
                )
                with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8]:
                    self.bridge.process_auto_mission("worker-v7-bound", repaired)
                stored = self.bridge.find_mission(mission["id"])
                with self.bridge.RATE_LIMIT_LOCK:
                    rate_rows = self.bridge._load_persisted_rate_limits_unlocked()[
                        rate_key
                    ]

        required_indexes = [
            index
            for index, value in enumerate(captured)
            if value == "--required-open-url"
        ]
        self.assertEqual(len(required_indexes), 6)
        self.assertEqual(
            [captured[index + 1] for index in required_indexes],
            latest_urls,
        )
        single_slot_rate_check.assert_not_called()
        reservation = stored["execution"]["correctiveOpenHourlyReservation"]
        self.assertEqual(reservation["state"], "reserved")
        self.assertEqual(reservation["reservedRunCount"], 6)
        self.assertEqual(reservation["mainRunCount"], 1)
        self.assertEqual(reservation["maximumChildRunCount"], 5)
        self.assertEqual(
            reservation["candidateUrlDigest"],
            self.bridge.payload_digest(latest_urls),
        )
        self.assertEqual(len(rate_rows), 6)

    def test_v6_and_v7_required_url_repairs_defer_when_only_one_hourly_slot_remains(self) -> None:
        for repair_version in ("v6", "v7"):
            with (
                self.subTest(repair_version=repair_version),
                tempfile.TemporaryDirectory() as temp_dir,
                self.runtime(temp_dir),
            ):
                with self.bridge.RATE_LIMIT_LOCK:
                    self.bridge.RATE_LIMIT_STATE.clear()
                project_root = Path(temp_dir) / "project"
                runtime_root = project_root / "data" / "runtime"
                with (
                    mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                    mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_root),
                ):
                    mission, _latest_urls, _slot_key = (
                        self.prepare_v6_portal_evidence_failure(project_root)
                    )
                    if repair_version == "v7":
                        self.assertEqual(
                            self.bridge.reconcile_current_day_public_research_output_repairs(),
                            1,
                        )
                        queued = self.bridge.find_mission(mission["id"])
                    else:
                        queued = self.requeue_v6_for_dispatch(
                            self.bridge.find_mission(mission["id"])
                        )
                    required_urls, required_error = (
                        self.bridge._trading_system_required_open_urls_for_mission(
                            queued
                        )
                    )
                    self.assertIsNone(required_error)
                    self.assertEqual(len(required_urls), 6)
                    rate_key = (
                        f"real:{queued['owner']}:{queued['toolId']}:"
                        f"{queued['modelTier']}"
                    )
                    reserved, _retry, existing_stamps = (
                        self.bridge.reserve_rate_limit_slots(
                            rate_key,
                            6,
                            5,
                            consume=True,
                        )
                    )
                    self.assertTrue(reserved)
                    self.assertEqual(len(existing_stamps), 5)
                    runner = mock.Mock()
                    finish = mock.Mock()
                    single_slot_rate_check = mock.Mock(return_value=(True, 0))
                    with (
                        mock.patch.object(
                            self.bridge,
                            "bridge_status",
                            return_value={"codex": {"status": "ready"}},
                        ),
                        mock.patch.object(
                            self.bridge,
                            "codex_rate_limits",
                            return_value=self.quota(80),
                        ),
                        mock.patch.object(
                            self.bridge,
                            "_collaboration_quota_gate",
                            return_value={"allowed": True, "reason": "ready"},
                        ),
                        mock.patch.object(
                            self.bridge,
                            "check_rate_limit",
                            single_slot_rate_check,
                        ),
                        mock.patch.object(
                            self.bridge,
                            "run_safe_command",
                            runner,
                        ),
                        mock.patch.object(
                            self.bridge,
                            "finish_auto_mission",
                            finish,
                        ),
                    ):
                        self.bridge.process_auto_mission(
                            f"worker-{repair_version}-hourly-capacity",
                            queued,
                        )
                    stored = self.bridge.find_mission(mission["id"])
                    with self.bridge.RATE_LIMIT_LOCK:
                        rate_rows = (
                            self.bridge._load_persisted_rate_limits_unlocked()[
                                rate_key
                            ]
                        )

                runner.assert_not_called()
                finish.assert_not_called()
                single_slot_rate_check.assert_not_called()
                self.assertEqual(stored["status"], "queued")
                self.assertEqual(stored["phase"], "auto_guarded_deferred")
                self.assertEqual(stored["attemptCount"], 0)
                self.assertEqual(
                    stored["execution"]["lastDeferredReason"],
                    "corrective_open_hourly_capacity_insufficient",
                )
                self.assertEqual(len(rate_rows), 5)

    def test_queued_empty_to_claimed_six_urls_fails_before_reservation_or_runner(self) -> None:
        """A claim-time corrective packet cannot bypass the queued six-slot gate."""

        runner = mock.Mock()
        finish = mock.Mock()
        bulk_reserve = mock.Mock()
        rate_check = mock.Mock(return_value=(True, 0))
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            project_root = Path(temp_dir) / "project"
            runtime_root = project_root / "data" / "runtime"
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_root),
            ):
                claimed, _urls, _slot_key = self.queue_required_open_mission(
                    project_root,
                    "v7",
                )
                queued_without_urls = copy.deepcopy(claimed)
                queued_without_urls["detail"] = queued_without_urls[
                    "detail"
                ].split(
                    self.bridge.TRADING_SYSTEM_EVIDENCE_CANDIDATE_BLOCK_START,
                    1,
                )[0].rstrip()
                for key in (
                    "correctiveRetry",
                    "trustedPromptRepair",
                    "deterministicOpenRepair",
                ):
                    queued_without_urls.pop(key, None)
                self.assertEqual(
                    self.bridge._trading_system_required_open_urls_for_mission(
                        queued_without_urls
                    ),
                    ([], None),
                )
                self.assertEqual(
                    len(
                        self.bridge._trading_system_required_open_urls_for_mission(
                            claimed
                        )[0]
                    ),
                    6,
                )
                with (
                    mock.patch.object(
                        self.bridge,
                        "bridge_status",
                        return_value={"codex": {"status": "ready"}},
                    ),
                    mock.patch.object(
                        self.bridge,
                        "codex_rate_limits",
                        return_value=self.quota(80),
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_collaboration_quota_gate",
                        return_value={"allowed": True, "reason": "ready"},
                    ),
                    mock.patch.object(
                        self.bridge,
                        "check_rate_limit",
                        rate_check,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "reserve_rate_limit_slots",
                        bulk_reserve,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "claim_auto_mission",
                        return_value=claimed,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "run_safe_command",
                        runner,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "finish_auto_mission",
                        finish,
                    ),
                    mock.patch.object(self.bridge, "update_mission_worker_state"),
                    mock.patch.object(
                        self.bridge,
                        "invalidate_codex_rate_limit_cache",
                    ),
                ):
                    self.bridge.process_auto_mission(
                        "worker-required-url-claim-race",
                        queued_without_urls,
                    )

        runner.assert_not_called()
        bulk_reserve.assert_not_called()
        self.assertEqual(len(rate_check.call_args_list), 1)
        self.assertFalse(rate_check.call_args.kwargs["consume"])
        finish.assert_called_once()
        process_receipt = finish.call_args.args[2]
        result = finish.call_args.args[3]
        self.assertFalse(process_receipt["processStarted"])
        self.assertEqual(
            process_receipt["exitCode"],
            "trading_system_required_open_urls_changed",
        )
        self.assertEqual(
            result["status"],
            "trading_system_required_open_urls_changed",
        )

    def test_empty_required_open_path_uses_single_normal_hourly_slot(self) -> None:
        """An ordinary scheduled Portal run retains the one-model-call path."""

        captured_command: list[str] = []

        def fake_runner(command, **_kwargs):
            captured_command.extend(str(item) for item in command)
            return {
                "ok": False,
                "exitCode": 1,
                "processStarted": False,
                "output": json.dumps({"ok": False, "status": "failed"}),
            }

        rate_check = mock.Mock(return_value=(True, 0))
        bulk_reserve = mock.Mock()
        finish = mock.Mock()
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            result = self.bridge.run_dashboard_workflow_action(
                "codex_mcp_portal",
                {
                    "actionId": "discover_trading_systems",
                    "form": {},
                    "idempotencyKey": "dashboard-schedule:empty-required-open",
                },
                trusted_trigger_source="schedule",
            )
            mission = result["mission"]
            self.assertEqual(
                self.bridge._trading_system_required_open_urls_for_mission(
                    mission
                ),
                ([], None),
            )
            with (
                mock.patch.object(
                    self.bridge,
                    "bridge_status",
                    return_value={"codex": {"status": "ready"}},
                ),
                mock.patch.object(
                    self.bridge,
                    "codex_rate_limits",
                    return_value=self.quota(80),
                ),
                mock.patch.object(
                    self.bridge,
                    "_collaboration_quota_gate",
                    return_value={"allowed": True, "reason": "ready"},
                ),
                mock.patch.object(
                    self.bridge,
                    "check_rate_limit",
                    rate_check,
                ),
                mock.patch.object(
                    self.bridge,
                    "reserve_rate_limit_slots",
                    bulk_reserve,
                ),
                mock.patch.object(
                    self.bridge,
                    "run_safe_command",
                    side_effect=fake_runner,
                ),
                mock.patch.object(
                    self.bridge,
                    "finish_auto_mission",
                    finish,
                ),
                mock.patch.object(self.bridge, "heartbeat_auto_mission"),
                mock.patch.object(self.bridge, "update_mission_worker_state"),
                mock.patch.object(
                    self.bridge,
                    "invalidate_codex_rate_limit_cache",
                ),
            ):
                self.bridge.process_auto_mission(
                    "worker-empty-required-open",
                    mission,
                )

        bulk_reserve.assert_not_called()
        self.assertEqual(
            [call.kwargs["consume"] for call in rate_check.call_args_list],
            [False, True],
        )
        self.assertNotIn("--required-open-url", captured_command)
        finish.assert_called_once()

    def test_v7_failure_concurrently_requeues_once_by_v8_and_v8_is_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            project_root = Path(temp_dir) / "project"
            runtime_root = project_root / "data" / "runtime"
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_root),
                mock.patch.object(self.bridge, "create_report") as create_report,
            ):
                mission, latest_urls, slot_key = (
                    self.prepare_v6_portal_evidence_failure(project_root)
                )
                self.assertEqual(
                    self.bridge.reconcile_current_day_public_research_output_repairs(),
                    1,
                )
                v7 = self.bridge.find_mission(mission["id"])
                v7_detail = v7["detail"]
                self.persist_evidence_open_failure(
                    v7,
                    report_id="v7-deterministic-open-failure",
                )
                with ThreadPoolExecutor(max_workers=2) as executor:
                    concurrent_results = list(executor.map(
                        lambda _index: (
                            self.bridge.reconcile_current_day_public_research_output_repairs()
                        ),
                        range(2),
                    ))
                v8 = self.bridge.find_mission(mission["id"])
                repeated = (
                    self.bridge.reconcile_current_day_public_research_output_repairs()
                )
                schedule = self.bridge.load_dashboard_workflow_settings()[
                    "discoverySchedule"
                ]
                required_urls, required_urls_error = (
                    self.bridge._trading_system_required_open_urls_for_mission(v8)
                )

                self.persist_evidence_open_failure(
                    v8,
                    report_id="v8-terminal-report",
                )
                terminal_retry = (
                    self.bridge.reconcile_current_day_public_research_output_repairs()
                )
                terminal = self.bridge.find_mission(mission["id"])

            create_report.assert_not_called()

        self.assertEqual(sorted(concurrent_results), [0, 1])
        self.assertEqual(repeated, 0)
        self.assertEqual(terminal_retry, 0)
        self.assertEqual(v8["id"], mission["id"])
        self.assertEqual(v8["status"], "queued")
        self.assertEqual(
            v8["phase"],
            "auto_guarded_deterministic_open_repair_queued",
        )
        self.assertEqual(v8["detail"], v7_detail)
        self.assertEqual(v8["outputContractRepair"]["version"], 8)
        self.assertEqual(
            v8["outputContractRepair"]["kind"],
            "trading_system_evidence_open_deterministic_verification_repair",
        )
        self.assertEqual(v8["correctiveRetry"]["attemptCount"], 1)
        self.assertEqual(v8["correctiveRetry"]["maximumAttempts"], 1)
        self.assertEqual(v8["trustedPromptRepair"]["attemptCount"], 1)
        self.assertEqual(v8["trustedPromptRepair"]["maximumAttempts"], 1)
        deterministic = v8["deterministicOpenRepair"]
        self.assertEqual(deterministic["attemptCount"], 1)
        self.assertEqual(deterministic["maximumAttempts"], 1)
        self.assertTrue(deterministic["automaticRetry"])
        self.assertTrue(deterministic["requiredUrlBlockPreserved"])
        self.assertFalse(deterministic["newDailyReservation"])
        self.assertFalse(deterministic["newReport"])
        self.assertEqual(
            deterministic["candidateUrlDigest"],
            self.bridge.payload_digest(latest_urls),
        )
        self.assertIsNone(required_urls_error)
        self.assertEqual(required_urls, latest_urls)
        self.assertEqual(v8["reportIds"], [])
        self.assertFalse(v8["approval"]["required"])
        self.assertEqual(v8["approval"]["state"], "not_required")
        self.assertEqual(v8["modelTier"], "manager_quality")
        self.assertEqual(v8["budget"]["rateReservePercent"], 15)
        self.assertEqual(schedule["lastMissionId"], mission["id"])
        self.assertEqual(schedule["lastSlotKey"], slot_key)
        self.assertEqual(schedule["dailyExecutionCount"], 1)
        self.assertEqual(schedule["dailyExecutionSlotKeys"], [slot_key])
        self.assertEqual(
            schedule["lastResultKind"],
            "deterministic_open_repair_requeued",
        )
        self.assertIsNone(
            self.bridge.auto_execution_authorization_error(
                v8,
                require_operator_mode=False,
            )
        )
        self.assertEqual(terminal["status"], "failed")
        self.assertEqual(terminal["reportIds"], ["v8-terminal-report"])

    def test_v8_worker_passes_exact_six_urls_and_persists_bounded_open_receipt(self) -> None:
        captured_command: list[str] = []

        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            project_root = Path(temp_dir) / "project"
            runtime_root = project_root / "data" / "runtime"
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_root),
                mock.patch.object(self.bridge, "create_report") as create_report,
            ):
                mission, latest_urls, _slot_key = (
                    self.prepare_v6_portal_evidence_failure(project_root)
                )
                self.assertEqual(
                    self.bridge.reconcile_current_day_public_research_output_repairs(),
                    1,
                )
                v7 = self.bridge.find_mission(mission["id"])
                self.persist_evidence_open_failure(
                    v7,
                    report_id="v7-before-v8-command",
                )
                self.assertEqual(
                    self.bridge.reconcile_current_day_public_research_output_repairs(),
                    1,
                )
                v8 = self.bridge.find_mission(mission["id"])
                malformed_receipt = (
                    self.bridge._bounded_corrective_open_verification_receipt(
                        v8,
                        {
                            "correctiveOpenVerificationCount": 1,
                            "correctiveOpenVerifications": [{
                                "url": "http://127.1/private",
                                "durationMs": 1,
                                "verificationSource": (
                                    "isolated_codex_exec_jsonl_direct_url"
                                ),
                            }],
                        },
                    )
                )
                verification_rows = [
                    {
                        "url": url,
                        "durationMs": index * 100,
                        "exitCode": 0,
                        "completedEventId": f"event-v8-{index}",
                        "completedEventDigest": self.bridge.payload_digest(
                            "completed-event",
                            url,
                        ),
                        "source": "posthoc_open_verification",
                    }
                    for index, url in enumerate(latest_urls[1:], start=1)
                ]
                manifest = {
                    "schemaVersion": (
                        "metafx-corrective-url-open-verification-v1"
                    ),
                    "verificationType": "posthoc_open_verification",
                    "runId": "run-v8-receipt",
                    "requiredUrlCount": 6,
                    "mainRequiredOpenCount": 1,
                    "mainRequiredOpenIndexes": [0],
                    "posthocVerificationCount": 5,
                    "rows": verification_rows,
                }
                manifest_text = json.dumps(
                    manifest,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                manifest_reference = (
                    "data/runtime/codex-runs/"
                    "run-v8-receipt.url-open-verification.json"
                )
                manifest_path = project_root / manifest_reference
                manifest_path.parent.mkdir(parents=True, exist_ok=True)
                manifest_path.write_text(manifest_text, encoding="utf-8")
                manifest_digest = self.bridge.hashlib.sha256(
                    manifest_text.encode("utf-8")
                ).hexdigest()
                runner_result = {
                    "ok": True,
                    "status": "completed",
                    "workStatus": "completed",
                    "finalMessage": "bounded deterministic verifier test",
                    "processStarted": True,
                    "workingDirectory": "workspace",
                    "writeRoots": [],
                    "controlPlaneWritable": False,
                    "webSearchEnabled": True,
                    "webSearchMode": "live",
                    "webSearchUsed": True,
                    "webSearchEvidenceVerified": True,
                    "correctiveOpenVerificationCount": 5,
                    "correctiveOpenVerifications": verification_rows,
                    "correctiveOpenVerificationArtifact": manifest_reference,
                    "correctiveOpenVerificationDigest": manifest_digest,
                    "artifacts": {},
                }
                valid_contract = {
                    "applicable": True,
                    "valid": True,
                    "failureCode": None,
                    "providedFields": ["systems"],
                    "missingFields": [],
                    "expectedEvidenceKinds": [],
                    "providedEvidenceKinds": [],
                    "missingEvidenceKinds": [],
                    "entryErrors": [],
                    "oversizedFields": [],
                }

                def fake_runner(command, **_kwargs):
                    captured_command.extend(str(item) for item in command)
                    return {
                        "ok": True,
                        "exitCode": 0,
                        "processStarted": True,
                        "output": json.dumps(runner_result),
                    }

                patches = (
                    mock.patch.object(self.bridge, "bridge_status", return_value={"codex": {"status": "ready"}}),
                    mock.patch.object(self.bridge, "codex_rate_limits", return_value=self.quota(80)),
                    mock.patch.object(self.bridge, "_collaboration_quota_gate", return_value={"allowed": True, "reason": "ready"}),
                    mock.patch.object(self.bridge, "check_rate_limit", return_value=(True, 0)),
                    mock.patch.object(self.bridge, "run_safe_command", side_effect=fake_runner),
                    mock.patch.object(self.bridge, "heartbeat_auto_mission"),
                    mock.patch.object(self.bridge, "update_mission_worker_state"),
                    mock.patch.object(self.bridge, "invalidate_codex_rate_limit_cache"),
                    mock.patch.object(self.bridge, "validate_dashboard_workflow_output_contract", return_value=valid_contract),
                )
                with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8]:
                    self.bridge.process_auto_mission("worker-v8-receipt", v8)
                stored = self.bridge.find_mission(mission["id"])
                rate_key = (
                    f"real:{stored['owner']}:{stored['toolId']}:"
                    f"{stored['modelTier']}"
                )
                with self.bridge.RATE_LIMIT_LOCK:
                    rate_rows = self.bridge._load_persisted_rate_limits_unlocked()[
                        rate_key
                    ]

            create_report.assert_called_once()

        required_indexes = [
            index
            for index, value in enumerate(captured_command)
            if value == "--required-open-url"
        ]
        self.assertEqual(len(required_indexes), 6)
        self.assertEqual(
            [captured_command[index + 1] for index in required_indexes],
            latest_urls,
        )
        self.assertFalse(malformed_receipt["valid"])
        self.assertEqual(malformed_receipt["missingUrlVerificationCount"], 0)
        self.assertEqual(malformed_receipt["verifications"], [])
        receipt = stored["correctiveOpenVerificationReceipt"]
        self.assertEqual(stored["status"], "completed")
        self.assertTrue(receipt["valid"])
        self.assertEqual(receipt["requiredUrlCount"], 6)
        self.assertEqual(receipt["missingUrlVerificationCount"], 5)
        self.assertEqual(receipt["modelOpenedUrlCount"], 1)
        self.assertEqual(receipt["modelOpenedUrlIndexes"], [0])
        self.assertEqual(
            receipt["requiredUrlDigest"],
            self.bridge.payload_digest(latest_urls),
        )
        self.assertTrue(receipt["requiredUrlCoverageVerified"])
        self.assertTrue(receipt["manifestVerified"])
        self.assertEqual(receipt["manifestArtifact"], manifest_reference)
        self.assertEqual(receipt["manifestDigest"], manifest_digest)
        self.assertEqual(
            [row["requiredUrlIndex"] for row in receipt["verifications"]],
            list(range(1, 6)),
        )
        self.assertTrue(
            all("url" not in row for row in receipt["verifications"])
        )
        self.assertEqual(
            stored["execution"]["correctiveOpenVerificationReceipt"],
            receipt,
        )
        hourly = stored["execution"]["correctiveOpenHourlyReservation"]
        self.assertEqual(hourly["state"], "reconciled")
        self.assertEqual(hourly["reservedRunCount"], 6)
        self.assertEqual(hourly["actualChildRunCount"], 5)
        self.assertEqual(hourly["releasedUnusedChildRunCount"], 0)
        self.assertEqual(len(rate_rows), 6)

    def test_v8_worker_defers_before_claim_when_six_hourly_slots_are_unavailable(self) -> None:
        runner = mock.Mock()
        finish = mock.Mock()
        rate_check = mock.Mock(return_value=(True, 0))

        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            project_root = Path(temp_dir) / "project"
            runtime_root = project_root / "data" / "runtime"
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_root),
            ):
                mission, _latest_urls, slot_key = (
                    self.prepare_v6_portal_evidence_failure(project_root)
                )
                self.assertEqual(
                    self.bridge.reconcile_current_day_public_research_output_repairs(),
                    1,
                )
                v7 = self.bridge.find_mission(mission["id"])
                self.persist_evidence_open_failure(
                    v7,
                    report_id="v7-before-hourly-capacity-deferral",
                )
                self.assertEqual(
                    self.bridge.reconcile_current_day_public_research_output_repairs(),
                    1,
                )
                v8 = self.bridge.find_mission(mission["id"])
                rate_key = (
                    f"real:{v8['owner']}:{v8['toolId']}:{v8['modelTier']}"
                )
                reserved, _retry, existing_stamps = (
                    self.bridge.reserve_rate_limit_slots(
                        rate_key,
                        6,
                        2,
                        consume=True,
                    )
                )
                self.assertTrue(reserved)
                self.assertEqual(len(existing_stamps), 2)
                patches = (
                    mock.patch.object(self.bridge, "bridge_status", return_value={"codex": {"status": "ready"}}),
                    mock.patch.object(self.bridge, "codex_rate_limits", return_value=self.quota(80)),
                    mock.patch.object(self.bridge, "_collaboration_quota_gate", return_value={"allowed": True, "reason": "ready"}),
                    mock.patch.object(self.bridge, "check_rate_limit", rate_check),
                    mock.patch.object(self.bridge, "run_safe_command", runner),
                    mock.patch.object(self.bridge, "finish_auto_mission", finish),
                )
                with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                    self.bridge.process_auto_mission(
                        "worker-v8-hourly-capacity",
                        v8,
                    )
                stored = self.bridge.find_mission(mission["id"])
                settings = self.bridge.load_dashboard_workflow_settings()
                with self.bridge.RATE_LIMIT_LOCK:
                    rate_rows = self.bridge._load_persisted_rate_limits_unlocked()[
                        rate_key
                    ]

        runner.assert_not_called()
        finish.assert_not_called()
        rate_check.assert_not_called()
        self.assertEqual(stored["status"], "queued")
        self.assertEqual(stored["phase"], "auto_guarded_deferred")
        self.assertEqual(stored["attemptCount"], 0)
        self.assertEqual(
            stored["execution"]["lastDeferredReason"],
            "corrective_open_hourly_capacity_insufficient",
        )
        self.assertEqual(stored["execution"]["dispatchState"], "deferred")
        self.assertIsNotNone(stored["execution"]["nextAttemptAt"])
        self.assertFalse(stored["execution"]["processStarted"])
        self.assertEqual(len(rate_rows), 2)
        schedule = settings["discoverySchedule"]
        self.assertEqual(schedule["lastMissionId"], mission["id"])
        self.assertEqual(schedule["lastSlotKey"], slot_key)
        self.assertEqual(schedule["dailyExecutionCount"], 1)
        self.assertEqual(schedule["dailyExecutionSlotKeys"], [slot_key])

    def test_bulk_hourly_reservation_is_atomic_and_rejects_count_above_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            rate_key = "real:news_consultant:codex_web_research:manager_quality"
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(
                    lambda _index: self.bridge.reserve_rate_limit_slots(
                        rate_key,
                        6,
                        6,
                        consume=True,
                    ),
                    range(2),
                ))
            tiny_key = "real:news_consultant:codex_web_research:tiny"
            tiny_result = self.bridge.reserve_rate_limit_slots(
                tiny_key,
                5,
                6,
                consume=True,
            )
            with self.bridge.RATE_LIMIT_LOCK:
                buckets = self.bridge._load_persisted_rate_limits_unlocked()

        self.assertEqual(sorted(result[0] for result in results), [False, True])
        self.assertEqual(sorted(len(result[2]) for result in results), [0, 6])
        self.assertEqual(len(buckets[rate_key]), 6)
        self.assertEqual(tiny_result, (False, 3600, []))
        self.assertNotIn(tiny_key, buckets)

    def test_v8_open_manifest_rejects_invalid_main_required_open_indexes(self) -> None:
        cases = {
            "overlap": {
                "mainIndexes": [1],
                "childIndexes": [1, 2, 3, 4, 5],
            },
            "missing": {
                "mainIndexes": [0],
                "childIndexes": [1, 2, 3, 4],
            },
            "extra": {
                "mainIndexes": [6],
                "childIndexes": [1, 2, 3, 4, 5],
            },
            "tampered": {
                "mainIndexes": [1, 0],
                "childIndexes": [2, 3, 4, 5],
            },
        }
        for case_name, case in cases.items():
            with (
                self.subTest(case_name=case_name),
                tempfile.TemporaryDirectory() as temp_dir,
                self.runtime(temp_dir),
            ):
                project_root = Path(temp_dir) / "project"
                runtime_root = project_root / "data" / "runtime"
                with (
                    mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                    mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_root),
                ):
                    mission, latest_urls, _slot_key = (
                        self.prepare_v6_portal_evidence_failure(project_root)
                    )
                    self.assertEqual(
                        self.bridge.reconcile_current_day_public_research_output_repairs(),
                        1,
                    )
                    v7 = self.bridge.find_mission(mission["id"])
                    self.persist_evidence_open_failure(
                        v7,
                        report_id=f"v7-before-index-{case_name}",
                    )
                    self.assertEqual(
                        self.bridge.reconcile_current_day_public_research_output_repairs(),
                        1,
                    )
                    v8 = self.bridge.find_mission(mission["id"])
                    child_indexes = case["childIndexes"]
                    rows = [
                        {
                            "url": latest_urls[index],
                            "durationMs": (position + 1) * 10,
                            "exitCode": 0,
                            "completedEventId": (
                                f"event-index-{case_name}-{position}"
                            ),
                            "completedEventDigest": self.bridge.payload_digest(
                                "completed-event",
                                latest_urls[index],
                            ),
                            "source": "posthoc_open_verification",
                        }
                        for position, index in enumerate(child_indexes)
                    ]
                    manifest = {
                        "schemaVersion": (
                            "metafx-corrective-url-open-verification-v1"
                        ),
                        "verificationType": "posthoc_open_verification",
                        "runId": f"run-v8-index-{case_name}",
                        "requiredUrlCount": 6,
                        "mainRequiredOpenCount": len(case["mainIndexes"]),
                        "mainRequiredOpenIndexes": case["mainIndexes"],
                        "posthocVerificationCount": len(rows),
                        "rows": rows,
                    }
                    manifest_text = json.dumps(
                        manifest,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    reference = (
                        "data/runtime/codex-runs/"
                        f"run-v8-index-{case_name}.url-open-verification.json"
                    )
                    path = project_root / reference
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(manifest_text, encoding="utf-8")
                    result = {
                        "webSearchUsed": True,
                        "webSearchEvidenceVerified": True,
                        "correctiveOpenVerificationCount": len(rows),
                        "correctiveOpenVerifications": rows,
                        "correctiveOpenVerificationArtifact": reference,
                        "correctiveOpenVerificationDigest": (
                            self.bridge.hashlib.sha256(
                                manifest_text.encode("utf-8")
                            ).hexdigest()
                        ),
                    }
                    receipt = (
                        self.bridge._bounded_corrective_open_verification_receipt(
                            v8,
                            result,
                        )
                    )

            self.assertFalse(receipt["valid"])
            self.assertFalse(receipt["requiredUrlCoverageVerified"])
            self.assertEqual(receipt["modelOpenedUrlIndexes"], [])
            self.assertEqual(
                receipt["failureCode"],
                "corrective_open_verification_invalid",
            )

    def test_v8_valid_zero_child_receipt_releases_exactly_five_reserved_slots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            project_root = Path(temp_dir) / "project"
            runtime_root = project_root / "data" / "runtime"
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_root),
            ):
                mission, latest_urls, _slot_key = (
                    self.prepare_v6_portal_evidence_failure(project_root)
                )
                self.assertEqual(
                    self.bridge.reconcile_current_day_public_research_output_repairs(),
                    1,
                )
                v7 = self.bridge.find_mission(mission["id"])
                self.persist_evidence_open_failure(
                    v7,
                    report_id="v7-before-zero-child-receipt",
                )
                self.assertEqual(
                    self.bridge.reconcile_current_day_public_research_output_repairs(),
                    1,
                )
                running = self.bridge.find_mission(mission["id"])
                lease_id = "lease-v8-zero-child"
                rate_key = (
                    f"real:{running['owner']}:{running['toolId']}:"
                    f"{running['modelTier']}"
                )
                reserved, _retry, stamps = self.bridge.reserve_rate_limit_slots(
                    rate_key,
                    6,
                    6,
                    consume=True,
                )
                self.assertTrue(reserved)
                reservation = (
                    self.bridge._corrective_open_hourly_reservation_record(
                        rate_key,
                        running["modelTier"],
                        6,
                        running["id"],
                        lease_id,
                        running["deterministicOpenRepair"][
                            "candidateUrlDigest"
                        ],
                        stamps,
                    )
                )
                self.assertIsNotNone(reservation)
                running.update({
                    "status": "running",
                    "phase": "auto_guarded_running",
                    "attemptCount": 1,
                })
                running["execution"].update({
                    "dispatchState": "running",
                    "leaseId": lease_id,
                    "workerId": "worker-v8-zero-child",
                    "processStarted": False,
                    "correctiveOpenHourlyReservation": reservation,
                })
                self.bridge.replace_mission(running)
                manifest = {
                    "schemaVersion": (
                        "metafx-corrective-url-open-verification-v1"
                    ),
                    "verificationType": "posthoc_open_verification",
                    "runId": "run-v8-zero-child",
                    "requiredUrlCount": 6,
                    "mainRequiredOpenCount": 6,
                    "mainRequiredOpenIndexes": [0, 1, 2, 3, 4, 5],
                    "posthocVerificationCount": 0,
                    "rows": [],
                }
                manifest_text = json.dumps(
                    manifest,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                reference = (
                    "data/runtime/codex-runs/"
                    "run-v8-zero-child.url-open-verification.json"
                )
                path = project_root / reference
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(manifest_text, encoding="utf-8")
                result = {
                    "ok": True,
                    "status": "completed",
                    "workStatus": "completed",
                    "finalMessage": "all six URLs opened by the main run",
                    "processStarted": True,
                    "workingDirectory": "workspace",
                    "writeRoots": [],
                    "controlPlaneWritable": False,
                    "webSearchEnabled": True,
                    "webSearchMode": "live",
                    "webSearchUsed": True,
                    "webSearchEvidenceVerified": True,
                    "correctiveOpenVerificationCount": 0,
                    "correctiveOpenVerifications": [],
                    "correctiveOpenVerificationArtifact": reference,
                    "correctiveOpenVerificationDigest": (
                        self.bridge.hashlib.sha256(
                            manifest_text.encode("utf-8")
                        ).hexdigest()
                    ),
                    "artifacts": {},
                }
                valid_contract = {
                    "applicable": True,
                    "valid": True,
                    "failureCode": None,
                    "providedFields": ["systems"],
                    "missingFields": [],
                    "expectedEvidenceKinds": [],
                    "providedEvidenceKinds": [],
                    "missingEvidenceKinds": [],
                    "entryErrors": [],
                    "oversizedFields": [],
                }
                with mock.patch.object(
                    self.bridge,
                    "validate_dashboard_workflow_output_contract",
                    return_value=valid_contract,
                ), mock.patch.object(self.bridge, "create_report"):
                    finished = self.bridge.finish_auto_mission(
                        mission["id"],
                        lease_id,
                        {"processStarted": True, "exitCode": 0},
                        result,
                    )
                with self.bridge.RATE_LIMIT_LOCK:
                    rate_rows = self.bridge._load_persisted_rate_limits_unlocked()[
                        rate_key
                    ]

        self.assertEqual(finished["status"], "completed")
        receipt = finished["correctiveOpenVerificationReceipt"]
        self.assertTrue(receipt["valid"])
        self.assertEqual(receipt["modelOpenedUrlIndexes"], list(range(6)))
        self.assertEqual(receipt["requiredUrlDigest"], self.bridge.payload_digest(latest_urls))
        hourly = finished["execution"]["correctiveOpenHourlyReservation"]
        self.assertEqual(hourly["state"], "reconciled")
        self.assertEqual(hourly["actualChildRunCount"], 0)
        self.assertEqual(hourly["releasedUnusedChildRunCount"], 5)
        self.assertEqual(len(rate_rows), 1)

    def test_v8_completed_result_with_missing_or_tampered_open_receipt_fails_closed(self) -> None:
        for receipt_kind in ("missing", "tampered"):
            with (
                self.subTest(receipt_kind=receipt_kind),
                tempfile.TemporaryDirectory() as temp_dir,
                self.runtime(temp_dir),
            ):
                with self.bridge.RATE_LIMIT_LOCK:
                    self.bridge.RATE_LIMIT_STATE.clear()
                project_root = Path(temp_dir) / "project"
                runtime_root = project_root / "data" / "runtime"
                with (
                    mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                    mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_root),
                ):
                    mission, _latest_urls, _slot_key = (
                        self.prepare_v6_portal_evidence_failure(project_root)
                    )
                    self.assertEqual(
                        self.bridge.reconcile_current_day_public_research_output_repairs(),
                        1,
                    )
                    v7 = self.bridge.find_mission(mission["id"])
                    self.persist_evidence_open_failure(
                        v7,
                        report_id=f"v7-before-{receipt_kind}",
                    )
                    self.assertEqual(
                        self.bridge.reconcile_current_day_public_research_output_repairs(),
                        1,
                    )
                    running = self.bridge.find_mission(mission["id"])
                    lease_id = f"lease-{receipt_kind}"
                    rate_key = (
                        f"real:{running['owner']}:{running['toolId']}:"
                        f"{running['modelTier']}"
                    )
                    reserved, _retry, stamps = (
                        self.bridge.reserve_rate_limit_slots(
                            rate_key,
                            6,
                            6,
                            consume=True,
                        )
                    )
                    self.assertTrue(reserved)
                    reservation = (
                        self.bridge._corrective_open_hourly_reservation_record(
                            rate_key,
                            running["modelTier"],
                            6,
                            running["id"],
                            lease_id,
                            running["deterministicOpenRepair"][
                                "candidateUrlDigest"
                            ],
                            stamps,
                        )
                    )
                    self.assertIsNotNone(reservation)
                    running.update({
                        "status": "running",
                        "phase": "auto_guarded_running",
                        "attemptCount": 1,
                    })
                    running["execution"].update({
                        "dispatchState": "running",
                        "leaseId": lease_id,
                        "workerId": "worker-v8-completion-gate",
                        "processStarted": True,
                        "correctiveOpenHourlyReservation": reservation,
                    })
                    self.bridge.replace_mission(running)
                    result = {
                        "ok": True,
                        "status": "completed",
                        "workStatus": "completed",
                        "finalMessage": "must not be accepted",
                        "processStarted": True,
                        "workingDirectory": "workspace",
                        "writeRoots": [],
                        "controlPlaneWritable": False,
                        "webSearchEnabled": True,
                        "webSearchMode": "live",
                        "webSearchUsed": True,
                        "webSearchEvidenceVerified": True,
                        "artifacts": {},
                    }
                    if receipt_kind == "tampered":
                        result.update({
                            "correctiveOpenVerificationCount": 1,
                            "correctiveOpenVerifications": [{
                                "url": "http://127.1/private",
                                "durationMs": 1,
                                "verificationSource": (
                                    "isolated_codex_exec_jsonl_direct_url"
                                ),
                            }],
                        })
                    valid_contract = {
                        "applicable": True,
                        "valid": True,
                        "failureCode": None,
                        "providedFields": ["systems"],
                        "missingFields": [],
                        "expectedEvidenceKinds": [],
                        "providedEvidenceKinds": [],
                        "missingEvidenceKinds": [],
                        "entryErrors": [],
                        "oversizedFields": [],
                    }
                    with mock.patch.object(
                        self.bridge,
                        "validate_dashboard_workflow_output_contract",
                        return_value=valid_contract,
                    ), mock.patch.object(self.bridge, "create_report"):
                        finished = self.bridge.finish_auto_mission(
                            mission["id"],
                            lease_id,
                            {"processStarted": True},
                            result,
                        )
                    with self.bridge.RATE_LIMIT_LOCK:
                        rate_rows = (
                            self.bridge._load_persisted_rate_limits_unlocked()[
                                rate_key
                            ]
                        )

            self.assertEqual(finished["status"], "failed")
            self.assertEqual(
                finished["errorCode"],
                "trading_system_deterministic_open_verification_invalid",
            )
            self.assertFalse(
                finished["correctiveOpenVerificationReceipt"]["valid"]
            )
            hourly = finished["execution"][
                "correctiveOpenHourlyReservation"
            ]
            self.assertEqual(hourly["state"], "reserved")
            self.assertIsNone(hourly["actualChildRunCount"])
            self.assertEqual(hourly["releasedUnusedChildRunCount"], 0)
            self.assertEqual(len(rate_rows), 6)

    def test_v7_deterministic_open_repair_rejects_tampered_lineage_or_block(self) -> None:
        for tamper_kind in ("digest", "metadata", "block"):
            with (
                self.subTest(tamper_kind=tamper_kind),
                tempfile.TemporaryDirectory() as temp_dir,
                self.runtime(temp_dir),
            ):
                project_root = Path(temp_dir) / "project"
                runtime_root = project_root / "data" / "runtime"
                with (
                    mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                    mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_root),
                    mock.patch.object(self.bridge, "create_report") as create_report,
                ):
                    mission, latest_urls, _slot_key = (
                        self.prepare_v6_portal_evidence_failure(project_root)
                    )
                    self.assertEqual(
                        self.bridge.reconcile_current_day_public_research_output_repairs(),
                        1,
                    )
                    v7 = self.bridge.find_mission(mission["id"])
                    failed = self.persist_evidence_open_failure(
                        v7,
                        report_id=f"v7-tampered-{tamper_kind}",
                    )
                    if tamper_kind == "digest":
                        failed["trustedPromptRepair"]["candidateUrlDigest"] = "0" * 64
                    elif tamper_kind == "metadata":
                        failed["trustedPromptRepair"]["attemptCount"] = 2
                    else:
                        failed["detail"] = failed["detail"].replace(
                            latest_urls[0],
                            "http://127.1/private",
                        )
                    self.bridge.replace_mission(failed)
                    repaired_count = (
                        self.bridge.reconcile_current_day_public_research_output_repairs()
                    )
                    stored = self.bridge.find_mission(mission["id"])

                create_report.assert_not_called()

            self.assertEqual(repaired_count, 0)
            self.assertEqual(stored["status"], "failed")
            self.assertNotIn("deterministicOpenRepair", stored)

    def test_tampered_or_obfuscated_corrective_urls_fail_before_runner_process(self) -> None:
        rejected = (
            "http://127.1/admin",
            "http://0177.0.0.1/admin",
            "http://0x7f.0.0.1/admin",
            "http://router.lan/admin",
        )
        for url in rejected:
            with self.subTest(url=url):
                self.assertIsNone(
                    self.bridge._normalized_trading_system_retry_url(url)
                )

        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            project_root = Path(temp_dir) / "project"
            runtime_root = project_root / "data" / "runtime"
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_root),
            ):
                mission, latest_urls, _slot_key = (
                    self.prepare_v6_portal_evidence_failure(project_root)
                )
                self.assertEqual(
                    self.bridge.reconcile_current_day_public_research_output_repairs(),
                    1,
                )
                repaired = self.bridge.find_mission(mission["id"])
                digest_tampered = copy.deepcopy(repaired)
                digest_tampered["correctiveRetry"]["candidateUrlDigest"] = "0" * 64
                self.assertEqual(
                    self.bridge._trading_system_required_open_urls_for_mission(
                        digest_tampered
                    )[1],
                    "trading_system_required_open_urls_invalid",
                )

                obfuscated = copy.deepcopy(repaired)
                obfuscated_url = "http://127.1/private"
                obfuscated["detail"] = obfuscated["detail"].replace(
                    latest_urls[0],
                    obfuscated_url,
                )
                tampered_urls = [obfuscated_url, *latest_urls[1:]]
                tampered_digest = self.bridge.payload_digest(tampered_urls)
                obfuscated["correctiveRetry"]["candidateUrlDigest"] = tampered_digest
                obfuscated["trustedPromptRepair"]["candidateUrlDigest"] = tampered_digest
                self.bridge._issue_backend_auto_safe_authorization(obfuscated)
                self.bridge.replace_mission(obfuscated)
                runner = mock.Mock()
                rate_check = mock.Mock(return_value=(True, 0))
                bulk_reserve = mock.Mock()
                finished = mock.Mock()
                patches = (
                    mock.patch.object(self.bridge, "bridge_status", return_value={"codex": {"status": "ready"}}),
                    mock.patch.object(self.bridge, "codex_rate_limits", return_value=self.quota(80)),
                    mock.patch.object(self.bridge, "_collaboration_quota_gate", return_value={"allowed": True, "reason": "ready"}),
                    mock.patch.object(self.bridge, "check_rate_limit", rate_check),
                    mock.patch.object(
                        self.bridge,
                        "reserve_rate_limit_slots",
                        bulk_reserve,
                    ),
                    mock.patch.object(self.bridge, "run_safe_command", runner),
                    mock.patch.object(self.bridge, "finish_auto_mission", finished),
                    mock.patch.object(self.bridge, "update_mission_worker_state"),
                    mock.patch.object(self.bridge, "invalidate_codex_rate_limit_cache"),
                )
                with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8]:
                    self.bridge.process_auto_mission(
                        "worker-v7-tampered",
                        obfuscated,
                    )

        runner.assert_not_called()
        bulk_reserve.assert_not_called()
        self.assertTrue(rate_check.called)
        self.assertTrue(
            all(call.kwargs.get("consume") is False for call in rate_check.call_args_list)
        )
        finished.assert_called_once()
        failure_result = finished.call_args.args[3]
        self.assertEqual(
            failure_result["status"],
            "trading_system_required_open_urls_invalid",
        )

    def test_finish_public_research_requires_verified_web_evidence_and_image_fault_is_nonfatal(self) -> None:
        valid_contract = {
            "applicable": True,
            "valid": True,
            "failureCode": None,
            "procedureId": self.bridge.RADAR_WORKFLOW_PROCEDURE_ID,
            "providedFields": ["entries"],
            "missingFields": [],
            "expectedEvidenceKinds": [],
            "providedEvidenceKinds": [],
            "missingEvidenceKinds": [],
            "entryErrors": [],
            "oversizedFields": [],
            "values": {"entries": "[]"},
        }
        for verified, expected_status in ((False, "blocked"), (True, "completed")):
            with (
                self.subTest(verified=verified),
                tempfile.TemporaryDirectory() as temp_dir,
                self.runtime(temp_dir),
            ):
                mission = self.create_safe_radar(
                    idempotency_key=f"finish-public-evidence-{verified}"
                )
                lease_id = f"lease-public-evidence-{verified}"
                mission.update({
                    "status": "running",
                    "phase": "auto_guarded_running",
                    "attemptCount": 1,
                })
                mission["execution"].update({
                    "dispatchState": "running",
                    "leaseId": lease_id,
                    "workerId": "worker-public-evidence",
                    "processStarted": True,
                })
                self.bridge.replace_mission(mission)
                runner_result = {
                    "ok": True,
                    "status": "completed",
                    "workStatus": "completed",
                    "finalMessage": "verified public research",
                    "processStarted": True,
                    "workingDirectory": "workspace",
                    "writeRoots": [],
                    "controlPlaneWritable": False,
                    "webSearchEnabled": True,
                    "webSearchMode": "live",
                    "webSearchUsed": True,
                    "webSearchEvidenceVerified": verified,
                    "evidence": [],
                    "artifacts": {},
                }
                with (
                    mock.patch.object(
                        self.bridge,
                        "validate_dashboard_workflow_output_contract",
                        return_value=valid_contract,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_radar_complete_daily_batch_required",
                        return_value=False,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "create_report",
                        side_effect=lambda payload: payload,
                    ) as create_report,
                    mock.patch.object(
                        self.bridge,
                        "queue_radar_publisher_image_enrichment",
                        side_effect=(RuntimeError("optional queue fault") if verified else False),
                    ) as queue_image,
                ):
                    finished = self.bridge.finish_auto_mission(
                        mission["id"],
                        lease_id,
                        {"processStarted": True},
                        runner_result,
                    )

                self.assertEqual(finished["status"], expected_status)
                create_report.assert_called_once()
                queue_image.assert_called_once()
                report_payload = create_report.call_args.args[0]
                self.assertEqual(report_payload["status"], "ready" if verified else "blocked")
                if verified:
                    self.assertIsNone(finished["errorCode"])
                else:
                    self.assertEqual(
                        finished["errorCode"],
                        "public_web_evidence_unverified",
                    )

    def test_scheduled_report_persist_failure_requeues_same_mission_and_slot(
        self,
    ) -> None:
        valid_contract = {
            "applicable": True,
            "valid": True,
            "failureCode": None,
            "procedureId": self.bridge.RADAR_WORKFLOW_PROCEDURE_ID,
            "providedFields": ["entries"],
            "missingFields": [],
            "expectedEvidenceKinds": [],
            "providedEvidenceKinds": [],
            "missingEvidenceKinds": [],
            "entryErrors": [],
            "oversizedFields": [],
            "values": {"entries": "[]"},
        }
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission = self.create_safe_radar(
                idempotency_key="report-persist-retry"
            )
            mission_id = mission["id"]
            slot_key = mission["idempotencyKey"].removeprefix(
                "dashboard-schedule:"
            )
            today = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
            self.bridge._dashboard_workflow_update_schedule_state(
                "indicatorScoutSchedule",
                {
                    "requestedEnabled": True,
                    "lastMissionId": mission_id,
                    "lastSlotKey": slot_key,
                    "lastAttemptSlotKey": slot_key,
                    "dailyExecutionDate": today,
                    "dailyExecutionCount": 1,
                    "dailyExecutionSlotKeys": [slot_key],
                },
            )
            lease_id = "lease-report-persist-retry"
            mission.update({
                "status": "running",
                "phase": "auto_guarded_running",
                "attemptCount": 1,
            })
            mission["execution"].update({
                "dispatchState": "running",
                "leaseId": lease_id,
                "workerId": "worker-report-persist-retry",
                "processStarted": True,
            })
            self.bridge.replace_mission(mission)
            runner_result = {
                "ok": True,
                "status": "completed",
                "workStatus": "completed",
                "finalMessage": "verified public research",
                "processStarted": True,
                "workingDirectory": "workspace",
                "writeRoots": [],
                "controlPlaneWritable": False,
                "webSearchEnabled": True,
                "webSearchMode": "live",
                "webSearchUsed": True,
                "webSearchEvidenceVerified": True,
                "evidence": [],
                "artifacts": {},
            }
            with (
                mock.patch.object(
                    self.bridge,
                    "validate_dashboard_workflow_output_contract",
                    return_value=valid_contract,
                ),
                mock.patch.object(
                    self.bridge,
                    "_radar_complete_daily_batch_required",
                    return_value=False,
                ),
                mock.patch.object(
                    self.bridge,
                    "create_report",
                    side_effect=OSError("disk unavailable"),
                ) as create_report,
                mock.patch.object(
                    self.bridge,
                    "queue_radar_publisher_image_enrichment",
                ) as queue_image,
            ):
                deferred = self.bridge.finish_auto_mission(
                    mission_id,
                    lease_id,
                    {"processStarted": True},
                    runner_result,
                )
            stored = self.bridge.find_mission(mission_id)
            schedule = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]

        create_report.assert_called_once()
        queue_image.assert_not_called()
        self.assertEqual(deferred["id"], mission_id)
        self.assertEqual(stored["id"], mission_id)
        self.assertEqual(stored["status"], "queued")
        self.assertEqual(
            stored["phase"],
            "auto_guarded_scheduled_completion_retry_deferred",
        )
        self.assertEqual(stored["reportIds"], [])
        retry = stored["scheduledCompletionRetry"]
        self.assertEqual(retry["lastFailureCode"], "report_persist_failed")
        self.assertTrue(retry["sameMission"])
        self.assertTrue(retry["sameDailyReservation"])
        self.assertFalse(retry["newDailyReservation"])
        self.assertEqual(schedule["lastMissionId"], mission_id)
        self.assertEqual(schedule["lastSlotKey"], slot_key)
        self.assertEqual(schedule["dailyExecutionCount"], 1)
        self.assertEqual(schedule["dailyExecutionSlotKeys"], [slot_key])
        self.assertEqual(schedule["lastRunStatus"], "deferred")
        self.assertEqual(
            schedule["lastResultKind"],
            "report_persist_retry_deferred",
        )

    def test_finish_exact_evidence_open_failure_retries_once_without_report_or_new_slot(self) -> None:
        today = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
        slot_key = f"discoverySchedule:{today}:0900"
        artifact_payload, urls = self.trading_system_evidence_artifact()
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            result = self.bridge.run_dashboard_workflow_action(
                "codex_mcp_portal",
                {
                    "actionId": "discover_trading_systems",
                    "form": {},
                    "idempotencyKey": f"dashboard-schedule:{slot_key}",
                },
                trusted_trigger_source="schedule",
            )
            mission = result["mission"]
            mission_id = mission["id"]
            project_root = Path(temp_dir) / "project"
            runtime_root = project_root / "data" / "runtime"
            artifact_reference = (
                "data/runtime/codex-runs/live-evidence-open.final.md"
            )
            artifact_path = project_root / artifact_reference
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(
                json.dumps(artifact_payload, ensure_ascii=False),
                encoding="utf-8",
            )
            mission.update({
                "status": "running",
                "phase": "auto_guarded_running",
                "workStatus": None,
                "errorCode": None,
                "attemptCount": 1,
            })
            mission["execution"].update({
                "dispatchState": "running",
                "workerId": "worker-live-corrective",
                "leaseId": "lease-live-corrective-1",
                "processStarted": True,
            })
            self.bridge.replace_mission(mission)
            self.bridge._dashboard_workflow_update_schedule_state(
                "discoverySchedule",
                {
                    "requestedEnabled": True,
                    "lastMissionId": mission_id,
                    "lastAttemptSlotKey": slot_key,
                    "lastSlotKey": slot_key,
                    "dailyExecutionDate": today,
                    "dailyExecutionCount": 1,
                    "dailyExecutionSlotKeys": [slot_key],
                },
            )
            runner_result = {
                "ok": False,
                "status": "invalid_output",
                "workStatus": "invalid_output",
                "finalMessage": "invalid structured result",
                "structuredOutputError": (
                    self.bridge.TRADING_SYSTEM_EVIDENCE_OPEN_ERROR
                ),
                "artifacts": {"final": artifact_reference},
                "evidence": [],
                "contractFields": [],
                "processStarted": True,
                "workingDirectory": "workspace",
                "writeRoots": [],
                "controlPlaneWritable": False,
                "webSearchEnabled": True,
                "webSearchMode": "live",
                "webSearchUsed": True,
                "webSearchEvidenceVerified": False,
            }
            self.bridge.MISSION_WORKER_WAKE.clear()
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_root),
                mock.patch.object(self.bridge, "create_report") as create_report,
            ):
                first = self.bridge.finish_auto_mission(
                    mission_id,
                    "lease-live-corrective-1",
                    {"processStarted": True},
                    runner_result,
                )
                schedule_after_first = (
                    self.bridge.load_dashboard_workflow_settings()[
                        "discoverySchedule"
                    ]
                )
                create_report.assert_not_called()

                second_run = copy.deepcopy(first)
                second_run.update({
                    "status": "running",
                    "phase": "auto_guarded_running",
                    "workStatus": None,
                    "errorCode": None,
                    "attemptCount": 1,
                })
                second_run["execution"].update({
                    "dispatchState": "running",
                    "workerId": "worker-live-corrective",
                    "leaseId": "lease-live-corrective-2",
                    "processStarted": True,
                })
                self.bridge.replace_mission(second_run)
                create_report.reset_mock()
                second = self.bridge.finish_auto_mission(
                    mission_id,
                    "lease-live-corrective-2",
                    {"processStarted": True},
                    runner_result,
                )
                schedule_after_second = (
                    self.bridge.load_dashboard_workflow_settings()[
                        "discoverySchedule"
                    ]
                )
                create_report.assert_not_called()

        self.assertEqual(first["id"], mission_id)
        self.assertEqual(first["status"], "queued")
        self.assertEqual(first["reportIds"], [])
        self.assertTrue(first["execution"]["automaticRetry"])
        self.assertEqual(first["correctiveRetry"]["attemptCount"], 1)
        self.assertEqual(first["correctiveRetry"]["maximumAttempts"], 1)
        self.assertEqual(
            first["detail"].count(
                self.bridge.TRADING_SYSTEM_EVIDENCE_CANDIDATE_BLOCK_START
            ),
            1,
        )
        for url in urls:
            self.assertIn(url, first["detail"])
        self.assertEqual(schedule_after_first["lastMissionId"], mission_id)
        self.assertEqual(schedule_after_first["lastSlotKey"], slot_key)
        self.assertEqual(schedule_after_first["dailyExecutionCount"], 1)
        self.assertEqual(schedule_after_first["dailyExecutionSlotKeys"], [slot_key])
        self.assertEqual(second["id"], mission_id)
        self.assertEqual(second["status"], "queued")
        self.assertEqual(
            second["phase"],
            "auto_guarded_scheduled_completion_retry_deferred",
        )
        self.assertTrue(second["execution"]["automaticRetry"])
        self.assertEqual(second["execution"]["dispatchState"], "deferred")
        self.assertTrue(second["execution"]["sameMission"])
        self.assertTrue(second["execution"]["sameDailyReservation"])
        self.assertEqual(second["scheduledCompletionRetry"]["attemptCount"], 1)
        self.assertTrue(second["scheduledCompletionRetry"]["sameMission"])
        self.assertTrue(
            second["scheduledCompletionRetry"]["sameDailyReservation"]
        )
        self.assertFalse(
            second["scheduledCompletionRetry"]["newDailyReservation"]
        )
        self.assertEqual(second["reportIds"], [])
        self.assertEqual(second["correctiveRetry"]["attemptCount"], 1)
        self.assertEqual(schedule_after_second["lastRunStatus"], "deferred")
        self.assertEqual(
            schedule_after_second["lastResultKind"],
            "scheduled_completion_retry_deferred",
        )
        self.assertEqual(schedule_after_second["dailyExecutionCount"], 1)
        self.assertEqual(schedule_after_second["dailyExecutionSlotKeys"], [slot_key])

    def test_current_day_reserved_scheduled_legacy_radar_is_requeued_in_place(self) -> None:
        today_bangkok = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
        slot_key = f"indicatorScoutSchedule:{today_bangkok}:0900"
        context, prompt, action = self.radar_context(trigger_source="schedule")
        context["executionReservation"] = {
            "settingsKey": "indicatorScoutSchedule",
            "bangkokDate": today_bangkok,
            "slotKey": slot_key,
            "maximumRunsPerDay": 1,
            "source": "schedule",
        }
        legacy = {
            "id": "mission-current-day-legacy-radar",
            "title": "Legacy scheduled Radar",
            "detail": prompt,
            "owner": action["ownerAgentId"],
            "toolId": action["toolId"],
            "targetId": "left_audit_crystals",
            "reportType": action["reportType"],
            "risk": "high",
            "status": "waiting_approval",
            "phase": "waiting_approval",
            "approval": {
                "required": True,
                "id": "approval-current-day-legacy-radar",
                "state": "approved",
                "gateMode": "human_and_risk_guard",
                "requiredActors": ["human", "risk_guard"],
                "decisions": [],
                "expiresAt": "2020-01-01T00:00:00Z",
                "consumedAt": None,
                "payloadDigest": "a" * 64,
            },
            "workflowContext": context,
            "executionMode": "manual_guarded",
            "autoEligible": False,
            "requiresHumanApproval": True,
            "budget": {
                "tokenBudget": 2048,
                "timeoutSeconds": 120,
                "outputLimitChars": 7000,
                "rateReservePercent": 30,
            },
            "execution": {},
        }

        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            self.bridge._dashboard_workflow_update_schedule_state(
                "indicatorScoutSchedule",
                {
                    "dailyExecutionDate": today_bangkok,
                    "dailyExecutionCount": 1,
                    "dailyExecutionSlotKeys": [slot_key],
                    "dailyExecutionLastReservedAt": self.bridge.utc_now(),
                },
            )
            before_schedule = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]
            self.bridge.save_missions([legacy])
            wake = mock.Mock()
            with mock.patch.object(self.bridge, "MISSION_WORKER_WAKE", wake):
                count = self.bridge.reconcile_stale_approval_missions()
            migrated = self.bridge.find_mission(legacy["id"])
            after_schedule = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]

        self.assertEqual(before_schedule["dailyExecutionCount"], 1)
        self.assertEqual(before_schedule["dailyExecutionSlotKeys"], [slot_key])
        self.assertEqual(count, 1)
        self.assertIsNotNone(migrated)
        self.assertEqual(migrated["id"], legacy["id"])
        self.assertEqual(migrated["status"], "queued")
        self.assertEqual(migrated["phase"], "auto_guarded_queued")
        self.assertEqual(migrated["approval"]["state"], "not_required")
        self.assertFalse(migrated["approval"]["required"])
        self.assertFalse(migrated["requiresHumanApproval"])
        self.assertTrue(migrated["autoEligible"])
        self.assertEqual(migrated["executionMode"], "auto_guarded")
        self.assertEqual(
            migrated["execution"]["authorizationSource"],
            "backend_auto_policy",
        )
        self.assertEqual(migrated["execution"]["authorizationDecision"], "allowed")
        self.assertEqual(migrated["budget"]["rateReservePercent"], 15)
        self.assertEqual(migrated["budget"]["timeoutSeconds"], 300)
        self.assertEqual(migrated["budget"]["outputLimitChars"], 20000)
        self.assertEqual(
            migrated["approvalMigration"]["action"],
            "requeued_current_schedule",
        )
        self.assertEqual(after_schedule["dailyExecutionCount"], 1)
        self.assertEqual(after_schedule["dailyExecutionSlotKeys"], [slot_key])
        wake.set.assert_called_once_with()

    def test_current_day_scheduled_legacy_portal_is_requeued_only_for_exact_scheduler_identity(self) -> None:
        today_bangkok = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
        slot_key = f"discoverySchedule:{today_bangkok}:0900"
        idempotency_key = f"dashboard-schedule:{slot_key}"

        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            created = self.bridge.run_dashboard_workflow_action(
                "codex_mcp_portal",
                {
                    "actionId": "discover_trading_systems",
                    "form": {},
                    "idempotencyKey": idempotency_key,
                },
                trusted_trigger_source="schedule",
            )
            legacy = copy.deepcopy(created["mission"])
            legacy.update({
                "risk": "high",
                "status": "blocked",
                "phase": "approval_reconciled",
                "errorCode": "approval_expired_during_startup_reconciliation",
                "executionMode": "manual_guarded",
                "autoEligible": False,
                "requiresHumanApproval": True,
                "completedAt": self.bridge.utc_now(),
                "execution": {},
                "approval": {
                    "required": True,
                    "id": "approval-current-day-legacy-portal",
                    "state": "expired",
                    "gateMode": "human_review",
                    "requiredActors": ["human", "risk_guard"],
                    "decisions": [],
                    "expiresAt": "2020-01-01T00:00:00Z",
                    "consumedAt": None,
                    "payloadDigest": "b" * 64,
                },
            })
            legacy["budget"] = {
                "tokenBudget": 2048,
                "timeoutSeconds": 120,
                "outputLimitChars": 7000,
                "rateReservePercent": 30,
            }
            self.bridge.save_missions([legacy])
            self.bridge._dashboard_workflow_update_schedule_state(
                "discoverySchedule",
                {
                    "lastAttemptAt": self.bridge.utc_now(),
                    "lastAttemptSlotKey": slot_key,
                    "lastRunAt": self.bridge.utc_now(),
                    "lastMissionId": legacy["id"],
                    "lastSlotKey": slot_key,
                    "lastRunStatus": "blocked",
                    "lastResultKind": "approval_required",
                },
            )
            settings = self.bridge.load_dashboard_workflow_settings()
            context = legacy["workflowContext"]
            self.assertTrue(
                self.bridge._current_day_scheduled_workflow_recovery_matches(
                    legacy,
                    context,
                    settings,
                    today_bangkok,
                )
            )
            mismatched = copy.deepcopy(legacy)
            mismatched["id"] = "mission-not-the-scheduler-record"
            self.assertFalse(
                self.bridge._current_day_scheduled_workflow_recovery_matches(
                    mismatched,
                    context,
                    settings,
                    today_bangkok,
                )
            )

            wake = mock.Mock()
            with mock.patch.object(self.bridge, "MISSION_WORKER_WAKE", wake):
                count = self.bridge.reconcile_stale_approval_missions()
            migrated = self.bridge.find_mission(legacy["id"])

        self.assertEqual(count, 1)
        self.assertIsNotNone(migrated)
        self.assertEqual(migrated["status"], "queued")
        self.assertEqual(migrated["phase"], "auto_guarded_queued")
        self.assertEqual(migrated["approval"]["state"], "not_required")
        self.assertFalse(migrated["requiresHumanApproval"])
        self.assertTrue(migrated["autoEligible"])
        self.assertEqual(migrated["executionMode"], "auto_guarded")
        self.assertEqual(
            migrated["execution"]["authorizationSource"],
            "backend_auto_policy",
        )
        self.assertEqual(migrated["budget"]["rateReservePercent"], 15)
        self.assertEqual(migrated["budget"]["timeoutSeconds"], 300)
        self.assertEqual(migrated["budget"]["outputLimitChars"], 20000)
        self.assertEqual(
            migrated["approvalMigration"]["action"],
            "requeued_current_schedule",
        )
        wake.set.assert_called_once_with()

    def test_legacy_false_positive_approval_is_archived_with_full_evidence(self) -> None:
        context, prompt, action = self.radar_context(trigger_source="schedule")
        prior_approval = {
            "required": True,
            "id": "approval-legacy-radar",
            "state": "approved",
            "gateMode": "human_and_risk_guard",
            "requiredActors": ["human", "risk_guard"],
            "decisions": [
                {
                    "actorId": "human",
                    "decision": "approved",
                    "at": "2026-08-13T01:00:00Z",
                    "payloadDigest": "a" * 64,
                }
            ],
            "expiresAt": "2026-08-13T02:00:00Z",
            "consumedAt": None,
            "payloadDigest": "a" * 64,
        }
        legacy = {
            "id": "mission-legacy-radar",
            "title": "Legacy Radar",
            "detail": prompt,
            "owner": action["ownerAgentId"],
            "toolId": action["toolId"],
            "targetId": "left_audit_crystals",
            "reportType": action["reportType"],
            "risk": "high",
            "status": "waiting_approval",
            "phase": "waiting_approval",
            "approval": prior_approval,
            "workflowContext": context,
            "executionMode": "manual_guarded",
            "autoEligible": False,
            "execution": {},
        }
        failed = {**copy.deepcopy(legacy), "id": "mission-radar-failed", "status": "failed"}
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            self.bridge.save_missions([legacy, failed])
            count = self.bridge.reconcile_stale_approval_missions()
            rows = {item["id"]: item for item in self.bridge.load_missions()}

        self.assertEqual(count, 1)
        migrated = rows["mission-legacy-radar"]
        self.assertEqual(migrated["status"], "archived")
        self.assertFalse(migrated["approvalMigration"]["realToolExecuted"])
        self.assertEqual(
            migrated["approvalMigration"]["previousApproval"]["id"],
            "approval-legacy-radar",
        )
        self.assertEqual(
            migrated["approvalMigration"]["previousApproval"]["decisions"][0]["actorId"],
            "human",
        )
        self.assertEqual(rows["mission-radar-failed"]["status"], "failed")

    def service_schedule(self, *, remaining: int = 1, error: str | None = None) -> dict:
        return {
            "lastRunStatus": "failed" if error else "never",
            "lastResultKind": "worker_failed" if error else None,
            "lastAttemptAt": "2020-01-01T00:00:00Z" if error else None,
            "lastRunAt": None,
            "lastError": error,
            "gateAllowed": True,
            "remainingRunsToday": remaining,
        }

    def test_service_health_is_backend_truth_and_never_offers_manual_retry(self) -> None:
        now_local = datetime(2026, 8, 14, 12, 0, tzinfo=self.bridge.THAILAND_TIMEZONE)
        ready_bridge = {"codex": {"status": "ready"}, "time": "2026-08-14T05:00:00Z"}
        unavailable = self.bridge._radar_website_tool_read_model(
            [],
            settings={},
            now_local=now_local,
            bridge={"codex": {"status": "not_ready"}},
            missions=[],
            schedule=self.service_schedule(),
        )["serviceHealth"]
        no_report = self.bridge._radar_website_tool_read_model(
            [],
            settings={},
            now_local=now_local,
            bridge=ready_bridge,
            missions=[],
            schedule=self.service_schedule(),
        )["serviceHealth"]
        active = self.bridge._radar_website_tool_read_model(
            [],
            settings={},
            now_local=now_local,
            bridge=ready_bridge,
            missions=[{
                "id": "radar-running",
                "status": "running",
                "targetId": "left_audit_crystals",
                "reportType": "indicator_scout_report",
                "workflowContext": {
                    "propId": "left_audit_crystals",
                    "actionId": "discover_new_indicators",
                },
            }],
            schedule=self.service_schedule(),
        )["serviceHealth"]
        healthy = self.bridge._radar_website_tool_read_model(
            [{
                "id": "report-radar-success",
                "type": "indicator_scout_report",
                "linkedPropId": "left_audit_crystals",
                "createdAt": "2026-08-14T04:00:00Z",
                "metrics": {"entries": []},
                "workflowContext": {
                    "propId": "left_audit_crystals",
                    "actionId": "discover_new_indicators",
                },
            }],
            settings={},
            now_local=now_local,
            bridge=ready_bridge,
            missions=[],
            schedule=self.service_schedule(),
        )["serviceHealth"]
        failed_with_capacity = self.bridge._radar_website_tool_read_model(
            [],
            settings={
                "indicatorScoutSchedule": {
                    "lastError": "worker_failed",
                    "lastAttemptAt": "2020-01-01T00:00:00Z",
                },
                "indicatorScoutSheet": {
                    "sheetId": "configured-sheet-id-1234",
                    "canonicalUrl": "https://docs.google.com/spreadsheets/d/configured-sheet-id-1234",
                    "savedAt": "2026-08-13T01:00:00Z",
                },
            },
            now_local=now_local,
            bridge=ready_bridge,
            missions=[],
            schedule=self.service_schedule(error="worker_failed"),
        )["serviceHealth"]
        failed_without_capacity = self.bridge._radar_website_tool_read_model(
            [],
            settings={
                "indicatorScoutSchedule": {
                    "lastError": "worker_failed",
                    "lastAttemptAt": "2020-01-01T00:00:00Z",
                }
            },
            now_local=now_local,
            bridge=ready_bridge,
            missions=[],
            schedule=self.service_schedule(remaining=0, error="worker_failed"),
        )["serviceHealth"]

        self.assertEqual(unavailable["status"], "configuration_required")
        self.assertFalse(unavailable["retryAvailable"])
        self.assertFalse(no_report["retryAvailable"])
        self.assertEqual(active["status"], "running")
        self.assertFalse(active["retryAvailable"])
        self.assertFalse(healthy["retryAvailable"])
        self.assertFalse(failed_with_capacity["retryAvailable"])
        self.assertFalse(failed_without_capacity["retryAvailable"])
        for health in (
            unavailable,
            no_report,
            active,
            healthy,
            failed_with_capacity,
            failed_without_capacity,
        ):
            self.assertFalse(health["manualRunAllowed"])
            self.assertTrue(health["automaticExecution"])
            self.assertFalse(health["humanApprovalRequired"])
            self.assertIsNone(health["retryEndpoint"])
            self.assertIsNone(health["retryActionId"])
        sheet = next(
            item
            for item in failed_with_capacity["sourceHealth"]
            if item["sourceId"] == "google_sheet"
        )
        self.assertEqual(sheet["status"], "auth_required")
        self.assertIsNone(sheet["lastSuccessAt"])

    def test_scheduled_terminal_reconcile_clears_stale_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            self.bridge._dashboard_workflow_update_schedule_state(
                "indicatorScoutSchedule",
                {
                    "lastAttemptAt": "2026-08-13T01:00:00Z",
                    "lastRunStatus": "failed",
                    "lastResultKind": "worker_failed",
                    "lastError": "old_worker_error",
                    "lastErrorAt": "2026-08-13T01:00:00Z",
                },
            )
            bangkok_date = self.bridge._dashboard_scheduler_local_now().date().isoformat()
            slot_key = f"indicatorScoutSchedule:{bangkok_date}:0900"
            mission = self.create_safe_radar(
                idempotency_key=f"dashboard-schedule:{slot_key}"
            )
            queued_at = mission["createdAt"]
            self.bridge._dashboard_workflow_update_schedule_state(
                "indicatorScoutSchedule",
                {
                    "lastAttemptAt": queued_at,
                    "lastAttemptSlotKey": slot_key,
                    "lastRunAt": queued_at,
                    "lastMissionId": mission["id"],
                    "lastSlotKey": slot_key,
                    "lastRunStatus": "queued",
                    "lastResultKind": "mission_auto_queued",
                    "lastIdempotentReplay": False,
                    "lastError": None,
                    "lastErrorAt": None,
                    "pendingSlotKey": None,
                    "pendingScheduledAt": None,
                    "dailyExecutionDate": bangkok_date,
                    "dailyExecutionCount": 1,
                    "dailyExecutionSlotKeys": [slot_key],
                },
            )
            queued_schedule = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]
            completed = copy.deepcopy(mission)
            completed["status"] = "completed"
            completed["phase"] = "auto_guarded_completed"
            completed["completedAt"] = self.bridge.utc_now()
            completed["updatedAt"] = completed["completedAt"]
            self.bridge.replace_mission(completed)
            self.bridge._dashboard_workflow_reconcile_schedule_states()
            settings = self.bridge.load_dashboard_workflow_settings()
            terminal_schedule = settings["indicatorScoutSchedule"]
            schedule_model = self.bridge._dashboard_saved_schedule_read_model(
                "indicatorScoutSchedule",
                default_times=["09:00"],
                settings=settings,
                max_times=1,
            )
            health = self.bridge._radar_website_tool_read_model(
                [],
                settings=settings,
                now_local=self.bridge._dashboard_scheduler_local_now(),
                bridge={"codex": {"status": "ready"}},
                missions=[completed],
                schedule=schedule_model,
            )["serviceHealth"]

        self.assertEqual(queued_schedule["lastMissionId"], mission["id"])
        self.assertEqual(queued_schedule["lastRunStatus"], "queued")
        self.assertEqual(queued_schedule["lastResultKind"], "mission_auto_queued")
        self.assertIsNone(queued_schedule["lastError"])
        self.assertIsNone(queued_schedule["pendingSlotKey"])
        self.assertEqual(queued_schedule["dailyExecutionCount"], 1)
        self.assertEqual(terminal_schedule["lastMissionId"], mission["id"])
        self.assertEqual(terminal_schedule["lastRunStatus"], "completed")
        self.assertIsNone(terminal_schedule["lastError"])
        self.assertEqual(terminal_schedule["dailyExecutionCount"], 1)
        self.assertEqual(health["lastRunStatus"], "completed")
        self.assertIsNone(health["lastError"])
        self.assertFalse(health["retryAvailable"])

    def test_radar_schedule_read_model_never_claims_external_actions(self) -> None:
        schedule = self.bridge._dashboard_schedule_read_model(
            "indicatorScoutSchedule",
            default_times=["09:00"],
            settings=self.bridge._default_dashboard_workflow_settings(),
            now_local=datetime(2026, 8, 14, 8, 0, tzinfo=self.bridge.THAILAND_TIMEZONE),
            max_times=1,
            scheduler={"alive": True, "operational": True},
            gate={
                "allowed": True,
                "reason": "ready",
                "settingsKey": "indicatorScoutSchedule",
            },
        )

        self.assertTrue(schedule["automaticReadOnlyResearch"])
        self.assertFalse(schedule["automaticExternalActions"])
        self.assertFalse(schedule["automaticExternalWrites"])
        self.assertFalse(schedule["automaticMetaTraderActions"])
        self.assertEqual(schedule["maximumRunsPerDay"], 1)

    def test_corrupt_over_cap_daily_count_normalizes_fail_closed_to_one(self) -> None:
        settings = self.bridge._default_dashboard_workflow_settings()
        settings["indicatorScoutSchedule"].update({
            "dailyExecutionDate": "2026-08-14",
            "dailyExecutionCount": 42,
            "dailyExecutionSlotKeys": [],
        })
        schedule = self.bridge._dashboard_schedule_read_model(
            "indicatorScoutSchedule",
            default_times=["09:00"],
            settings=settings,
            now_local=datetime(2026, 8, 14, 8, 0, tzinfo=self.bridge.THAILAND_TIMEZONE),
            max_times=1,
            scheduler={"alive": True, "operational": True},
            gate={
                "allowed": True,
                "reason": "ready",
                "settingsKey": "indicatorScoutSchedule",
            },
        )

        self.assertEqual(schedule["runsReservedToday"], 1)
        self.assertEqual(schedule["remainingRunsToday"], 0)
        self.assertTrue(schedule["effectiveEnabled"])
        self.assertEqual(schedule["status"], "daily_limit_reached")
        self.assertEqual(schedule["nextRunAt"], "2026-08-15T02:00:00Z")

    def test_radar_contracts_freeze_once_daily_enabled_nine_am_default(self) -> None:
        connection = json.loads(
            (PROJECT_ROOT / "contracts" / "connections" / "dashboard-connection-contract.json").read_text(
                encoding="utf-8"
            )
        )
        reports = json.loads(
            (PROJECT_ROOT / "contracts" / "reports" / "report-contract.json").read_text(
                encoding="utf-8"
            )
        )
        orchestration = json.loads(
            (PROJECT_ROOT / "contracts" / "orchestration" / "orchestration-contract.json").read_text(
                encoding="utf-8"
            )
        )
        properties = json.loads(
            (PROJECT_ROOT / "contracts" / "props" / "property-role-map.json").read_text(
                encoding="utf-8"
            )
        )
        radar_connection = connection["profiles"]["left_audit_crystals"]
        radar_report = reports["typed_report_schemas"]["indicator_scout_report"]

        operation = radar_connection["operation"]
        self.assertTrue(operation["scheduleDefaultEnabled"])
        self.assertEqual(operation["scheduleDefaultTimes"], ["09:00"])
        self.assertEqual(operation["schedulePreferenceMaxRunsPerDay"], 1)
        self.assertEqual(operation["scheduleHardMaximumRunsPerDay"], 1)
        scheduler_label = next(
            adapter["labelTh"]
            for adapter in radar_connection["connections"]
            if adapter["id"] == "backend_scheduler"
        )
        self.assertNotIn("1-2", scheduler_label)

        preference = radar_report["schedulePreference"]
        self.assertTrue(preference["defaultEnabled"])
        self.assertEqual(preference["defaultTimes"], ["09:00"])
        self.assertEqual(preference["times"], ["09:00"])
        self.assertEqual(preference["maximumRunsPerDay"], 1)
        self.assertTrue(preference["configurationSaved"])
        radar_workflow = properties["properties"]["left_audit_crystals"]["workflow"]
        self.assertTrue(radar_workflow["schedule"]["defaultEnabled"])
        self.assertEqual(radar_workflow["schedule"]["defaultTimes"], ["09:00"])
        self.assertEqual(radar_workflow["schedule"]["maximumRunsPerDay"], 1)
        schedule_section = next(
            section
            for section in properties["properties"]["left_audit_crystals"]["dashboardUx"]["leftRailSections"]
            if section["id"] == "schedule"
        )
        self.assertNotIn("2 รอบ", schedule_section["purpose"])
        digest_fields = orchestration["approvalGate"]["missionDigestFields"]
        for field in (
            "workflowContext.executionReservation",
            "workflowContext.executionReservation.bangkokDate",
            "workflowContext.executionReservation.slotKey",
            "workflowContext.executionReservation.maximumRunsPerDay",
            "workflowContext.executionReservation.source",
        ):
            self.assertIn(field, digest_fields)


if __name__ == "__main__":
    unittest.main()
