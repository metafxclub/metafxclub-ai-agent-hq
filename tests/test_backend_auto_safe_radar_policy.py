from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
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
        trigger_source: str = "backend",
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
        context["executionReservation"] = {
            "settingsKey": "indicatorScoutSchedule",
            "bangkokDate": bangkok_date,
            "slotKey": (
                f"indicatorScoutSchedule:{bangkok_date}:manual-"
                f"{self.bridge.payload_digest(idempotency_key)[:16]}"
            ),
            "maximumRunsPerDay": 1,
            "source": "manual_or_backend",
        }
        preferences = self.bridge._dashboard_workflow_execution_preferences(
            "discover_new_indicators",
            self.bridge.load_dashboard_workflow_settings(),
        )
        result = self.bridge.run_bridge_task(
            {
                "toolId": action["toolId"],
                "agentId": action["ownerAgentId"],
                "requester": "human",
                "targetId": "left_audit_crystals",
                "reportType": action["reportType"],
                "prompt": prompt,
                "idempotencyKey": idempotency_key,
            },
            trusted_workflow_context=context,
            trusted_execution_preferences=preferences,
        )
        self.assertTrue(result["ok"], result)
        return result["mission"]

    def test_trusted_radar_is_backend_auto_safe_without_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission = self.create_safe_radar()
            public = self.bridge.mission_read_model_item(mission)

        self.assertEqual(mission["status"], "queued")
        self.assertFalse(mission["requiresHumanApproval"])
        self.assertEqual(mission["approval"]["state"], "not_required")
        self.assertFalse(mission["approval"]["required"])
        self.assertEqual(mission["budget"]["outputLimitChars"], 20000)
        self.assertEqual(mission["budget"]["rateReservePercent"], 10)
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

    def test_trusted_classifier_does_not_hide_malicious_user_intent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            result = self.bridge.run_dashboard_workflow_action(
                "left_audit_crystals",
                {
                    "actionId": "discover_new_indicators",
                    "form": {
                        "query": "deploy production and send token",
                        "platform": "any",
                        "category": "any",
                        "maxItems": 2,
                    },
                    "idempotencyKey": "radar-malicious-1",
                },
                trusted_trigger_source="frontend",
            )
            settings = self.bridge.load_dashboard_workflow_settings()

        self.assertFalse(result["ok"])
        self.assertEqual(result.get("kind"), "approval_required")
        self.assertEqual(result["mission"]["status"], "waiting_approval")
        self.assertTrue(result["mission"]["approval"]["required"])
        self.assertTrue(result["mission"]["requiresHumanApproval"])
        self.assertEqual(
            settings["indicatorScoutSchedule"]["dailyExecutionCount"],
            1,
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
            wrong_manual_shape = copy.deepcopy(persisted)
            reservation_date = wrong_manual_shape["workflowContext"][
                "executionReservation"
            ]["bangkokDate"]
            wrong_manual_shape["workflowContext"]["executionReservation"][
                "slotKey"
            ] = f"indicatorScoutSchedule:{reservation_date}:0900"
            self.assertEqual(
                self.bridge.auto_execution_authorization_error(
                    wrong_manual_shape,
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

    def test_manual_and_scheduler_share_one_atomic_daily_reservation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            self.bridge.save_direct_daily_fx_news_schedule(
                {"enabled": False, "times": ["00:00", "12:00"]}
            )
            first = self.bridge.run_dashboard_workflow_action(
                "left_audit_crystals",
                {
                    "actionId": "discover_new_indicators",
                    "form": {"query": "first", "maxItems": 1},
                    "idempotencyKey": "manual-radar-first",
                },
                trusted_trigger_source="frontend",
            )
            replay = self.bridge.run_dashboard_workflow_action(
                "left_audit_crystals",
                {
                    "actionId": "discover_new_indicators",
                    "form": {"query": "first", "maxItems": 1},
                    "idempotencyKey": "manual-radar-first",
                },
                trusted_trigger_source="frontend",
            )
            with self.assertRaises(self.bridge.RequestError) as blocked:
                self.bridge.run_dashboard_workflow_action(
                    "left_audit_crystals",
                    {
                        "actionId": "discover_new_indicators",
                        "form": {"query": "retry", "maxItems": 1},
                        "idempotencyKey": "manual-radar-second",
                    },
                    trusted_trigger_source="frontend",
                )
            runner = mock.Mock()
            with mock.patch.object(
                self.bridge,
                "run_dashboard_workflow_action",
                runner,
            ):
                scheduled = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 14, 9, 0, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
            stored = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]

        self.assertTrue(first["ok"])
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(blocked.exception.status, 409)
        self.assertFalse(scheduled["dispatched"])
        runner.assert_not_called()
        self.assertEqual(stored["dailyExecutionCount"], 1)
        self.assertEqual(len(stored["dailyExecutionSlotKeys"]), 1)

    def test_definite_no_mission_releases_manual_reservation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            with mock.patch.object(
                self.bridge,
                "run_bridge_task",
                return_value={"ok": False, "kind": "guarded", "message": "no mission"},
            ):
                result = self.bridge.run_dashboard_workflow_action(
                    "left_audit_crystals",
                    {
                        "actionId": "discover_new_indicators",
                        "form": {"query": "safe", "maxItems": 1},
                        "idempotencyKey": "manual-no-mission",
                    },
                    trusted_trigger_source="frontend",
                )
            stored = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]

        self.assertFalse(result["ok"])
        self.assertEqual(stored["dailyExecutionCount"], 0)
        self.assertEqual(stored["dailyExecutionSlotKeys"], [])

    def test_schedule_migration_preserves_explicit_operator_choice(self) -> None:
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
        self.assertFalse(explicit["indicatorScoutSchedule"]["requestedEnabled"])
        self.assertEqual(explicit["indicatorScoutSchedule"]["times"], ["07:00"])
        self.assertEqual(
            explicit["indicatorScoutSchedule"]["savedAt"],
            "2026-08-13T10:00:00Z",
        )
        self.assertEqual(explicit["indicatorScoutSchedule"]["dailyExecutionCount"], 0)

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

    def test_radar_quota_reserve_is_ten_percent_at_scheduler_gate(self) -> None:
        common = {
            "refresh_quota": False,
            "operator_mode": {"mode": "auto_guarded"},
            "bridge": {"codex": {"status": "ready"}},
            "mission_worker": {"operational": True},
            "settings": self.bridge._default_dashboard_workflow_settings(),
        }
        radar = self.bridge._dashboard_workflow_scheduler_gate(
            **common,
            settings_key="indicatorScoutSchedule",
            quota=self.quota(26),
        )
        ordinary = self.bridge._dashboard_workflow_scheduler_gate(
            **common,
            settings_key="discoverySchedule",
            quota=self.quota(26),
        )
        stale = self.bridge._dashboard_workflow_scheduler_gate(
            **common,
            settings_key="indicatorScoutSchedule",
            quota=self.quota(26, stale=True),
        )
        limited = self.bridge._dashboard_workflow_scheduler_gate(
            **common,
            settings_key="indicatorScoutSchedule",
            quota=self.quota(26, limit=True),
        )

        self.assertTrue(radar["allowed"])
        self.assertEqual(radar["rateReservePercent"], 10)
        self.assertFalse(ordinary["allowed"])
        self.assertFalse(stale["allowed"])
        self.assertFalse(limited["allowed"])

    def test_quota_pause_does_not_burn_slot_and_recovery_dispatches_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            self.bridge.save_direct_daily_fx_news_schedule(
                {"enabled": False, "times": ["00:00", "12:00"]}
            )
            self.bridge._save_dashboard_schedule_preference(
                "indicatorScoutSchedule",
                {"enabled": True, "times": ["09:00"]},
            )
            quota = {"value": self.quota(5)}
            runner = mock.Mock(return_value={
                "ok": True,
                "kind": "mission_auto_queued",
                "mission": {"id": "radar-quota-recovered", "status": "queued"},
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
                before = self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]
                quota["value"] = self.quota(26)
                recovered = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 14, 9, 6, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                duplicate = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 14, 9, 7, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                after = self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]

        self.assertFalse(paused["dispatched"])
        self.assertEqual(before["dailyExecutionCount"], 0)
        self.assertTrue(recovered["dispatched"])
        self.assertFalse(duplicate["dispatched"])
        self.assertEqual(runner.call_count, 1)
        self.assertEqual(after["dailyExecutionCount"], 1)

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

    def test_manual_radar_worker_rechecks_ten_percent_reserve_before_process_start(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            result = self.bridge.run_dashboard_workflow_action(
                "left_audit_crystals",
                {
                    "actionId": "discover_new_indicators",
                    "form": {"query": "manual reserve race", "maxItems": 1},
                    "idempotencyKey": "manual-radar-quota-race",
                },
                trusted_trigger_source="frontend",
            )
            mission = result["mission"]
            runner = mock.Mock()
            with mock.patch.object(
                self.bridge,
                "bridge_status",
                return_value={"codex": {"status": "ready"}},
            ), mock.patch.object(
                self.bridge,
                "codex_rate_limits",
                return_value=self.quota(8),
            ), mock.patch.object(
                self.bridge,
                "_collaboration_quota_gate",
                return_value={"allowed": False, "reason": "quota_reserve"},
            ), mock.patch.object(self.bridge, "run_safe_command", runner):
                self.bridge.process_auto_mission("worker-manual-quota", mission)
            stored = self.bridge.find_mission(mission["id"])

        runner.assert_not_called()
        self.assertEqual(stored["status"], "queued")
        self.assertFalse(stored["execution"]["processStarted"])
        self.assertEqual(stored["execution"]["lastDeferredReason"], "quota_reserve")
        self.assertEqual(
            stored["workflowContext"]["executionReservation"]["maximumRunsPerDay"],
            1,
        )

    def test_prior_day_manual_radar_expires_then_next_day_scheduler_runs_once(self) -> None:
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
            ), mock.patch.object(
                self.bridge,
                "utc_now",
                return_value="2026-08-13T01:00:00Z",
            ):
                result = self.bridge.run_dashboard_workflow_action(
                    "left_audit_crystals",
                    {
                        "actionId": "discover_new_indicators",
                        "form": {"query": "manual prior day", "maxItems": 1},
                        "idempotencyKey": "manual-radar-prior-day",
                    },
                    trusted_trigger_source="frontend",
                )
            mission = result["mission"]
            runtime_probe = mock.Mock()
            with mock.patch.object(
                self.bridge,
                "_dashboard_scheduler_local_now",
                return_value=day_two,
            ), mock.patch.object(self.bridge, "bridge_status", runtime_probe):
                self.bridge.process_auto_mission("worker-manual-midnight", mission)
            expired = self.bridge.find_mission(mission["id"])

            scheduler_runner = mock.Mock(return_value={
                "ok": True,
                "kind": "mission_auto_queued",
                "mission": {"id": "radar-next-day", "status": "queued"},
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
                scheduled = self.bridge.dashboard_workflow_scheduler_tick(
                    day_two,
                    refresh_quota=False,
                )
            schedule = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]

        runtime_probe.assert_not_called()
        self.assertEqual(expired["status"], "blocked")
        self.assertEqual(expired["errorCode"], "radar_daily_reservation_expired")
        self.assertFalse(expired["execution"]["processStarted"])
        self.assertTrue(scheduled["dispatched"])
        self.assertEqual(scheduler_runner.call_count, 1)
        self.assertEqual(schedule["dailyExecutionDate"], "2026-08-14")
        self.assertEqual(schedule["dailyExecutionCount"], 1)

    def test_radar_worker_command_is_read_only_while_ordinary_safe_work_can_write_workspace(self) -> None:
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
            radar = self.create_safe_radar(idempotency_key="radar-sandbox")
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
                self.bridge.process_auto_mission("worker-radar", radar)
                self.bridge.process_auto_mission("worker-ordinary", ordinary)

        self.assertEqual(len(captured), 2)
        radar_command, ordinary_command = captured
        self.assertIn("--read-only-work", radar_command)
        self.assertEqual(
            radar_command[radar_command.index("--result-profile") + 1],
            "radar_website_tool",
        )
        self.assertNotIn("--read-only-work", ordinary_command)
        self.assertNotIn("--result-profile", ordinary_command)

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

    def test_service_health_is_backend_truth_and_retry_is_fail_closed(self) -> None:
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
        self.assertTrue(no_report["retryAvailable"])
        self.assertEqual(active["status"], "running")
        self.assertFalse(active["retryAvailable"])
        self.assertFalse(healthy["retryAvailable"])
        self.assertTrue(failed_with_capacity["retryAvailable"])
        self.assertFalse(failed_without_capacity["retryAvailable"])
        self.assertEqual(
            failed_with_capacity["retryEndpoint"],
            "/api/props/left_audit_crystals/workflow/actions",
        )
        self.assertEqual(
            failed_with_capacity["retryActionId"],
            "discover_new_indicators",
        )
        sheet = next(
            item
            for item in failed_with_capacity["sourceHealth"]
            if item["sourceId"] == "google_sheet"
        )
        self.assertEqual(sheet["status"], "configured_not_connected")
        self.assertIsNone(sheet["lastSuccessAt"])

    def test_manual_retry_links_schedule_and_terminal_reconcile_clears_stale_error(self) -> None:
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
            result = self.bridge.run_dashboard_workflow_action(
                "left_audit_crystals",
                {
                    "actionId": "discover_new_indicators",
                    "form": {"query": "retry after prior failure", "maxItems": 1},
                    "idempotencyKey": "manual-radar-linked-retry",
                },
                trusted_trigger_source="frontend",
            )
            mission = result["mission"]
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
        self.assertEqual(queued_schedule["lastResultKind"], result["kind"])
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
        self.assertFalse(schedule["effectiveEnabled"])

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
