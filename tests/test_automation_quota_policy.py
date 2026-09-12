from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
RUNNER_PATH = PROJECT_ROOT / "runner" / "codex_cli_runner.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AutomationQuotaPolicyBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module("automation_quota_policy_bridge", BRIDGE_PATH)

    @contextmanager
    def isolated_settings(self):
        with tempfile.TemporaryDirectory() as temp_dir, ExitStack() as stack:
            root = Path(temp_dir)
            settings_path = root / "dashboard-workflow-settings.json"
            stack.enter_context(
                mock.patch.object(
                    self.bridge,
                    "DASHBOARD_WORKFLOW_SETTINGS_PATH",
                    settings_path,
                )
            )
            stack.enter_context(
                mock.patch.object(self.bridge, "AUDIT_PATH", root / "bridge-audit.jsonl")
            )
            stack.enter_context(mock.patch.object(self.bridge, "append_audit"))
            stack.enter_context(
                mock.patch.object(self.bridge, "_wake_ai_quota_policy_consumers")
            )
            yield settings_path

    @staticmethod
    def quota(
        primary: float,
        secondary: float | None = None,
        *,
        stale: bool = False,
        limit_reached: bool = False,
    ) -> dict:
        result = {
            "ok": True,
            "status": "ready",
            "stale": stale,
            "limitReached": limit_reached,
            "primary": {"remainingPercent": primary},
        }
        if secondary is not None:
            result["secondary"] = {"remainingPercent": secondary}
        return result

    def test_boundary_values_persist_without_overwriting_other_preferences(self) -> None:
        with self.isolated_settings() as settings_path:
            initial = self.bridge._default_dashboard_workflow_settings()
            initial["agentPreferences"].update(
                {
                    "language": "en",
                    "modelTier": "manager_quality",
                    "tokenBudget": 54321,
                    "timeoutSeconds": 321,
                    "outputLimitChars": 12345,
                    "rateReservePercent": 37,
                    "savedAt": "2026-09-11T00:00:00+00:00",
                }
            )
            initial["operatorOwnedSentinel"] = {"preserve": True}
            self.bridge.write_json(settings_path, initial)

            for boundary in (0, 100):
                with self.subTest(boundary=boundary):
                    result = self.bridge.save_automation_quota_policy(
                        {"rateReservePercent": boundary}
                    )
                    stored = self.bridge.load_dashboard_workflow_settings()
                    preferences = stored["agentPreferences"]

                    self.assertTrue(result["ok"])
                    self.assertEqual(result["rateReservePercent"], boundary)
                    self.assertEqual(result["minRemainingPercent"], boundary)
                    self.assertEqual(preferences["rateReservePercent"], boundary)
                    self.assertEqual(preferences["language"], "en")
                    self.assertEqual(preferences["modelTier"], "manager_quality")
                    self.assertEqual(preferences["tokenBudget"], 54321)
                    self.assertEqual(preferences["timeoutSeconds"], 321)
                    self.assertEqual(preferences["outputLimitChars"], 12345)
                    self.assertEqual(stored["operatorOwnedSentinel"], {"preserve": True})
                    self.assertEqual(
                        result["comparison"],
                        "remaining_greater_than_or_equal_to_threshold",
                    )
                    self.assertEqual(result["blocksWhen"], "remaining_below_threshold")

    def test_invalid_policy_requests_fail_closed_without_changing_persisted_value(self) -> None:
        invalid_requests = (
            None,
            [],
            {},
            {"rateReservePercent": True},
            {"rateReservePercent": False},
            {"rateReservePercent": 1.0},
            {"rateReservePercent": 15.5},
            {"rateReservePercent": "15"},
            {"rateReservePercent": None},
            {"rateReservePercent": -1},
            {"rateReservePercent": 101},
            {"rateReservePercent": 15, "extra": "not-accepted"},
        )
        with self.isolated_settings():
            self.bridge.save_automation_quota_policy({"rateReservePercent": 37})
            before = copy.deepcopy(self.bridge.load_dashboard_workflow_settings())

            for request in invalid_requests:
                with self.subTest(request=request), self.assertRaises(
                    self.bridge.RequestError
                ) as raised:
                    self.bridge.save_automation_quota_policy(request)
                self.assertEqual(raised.exception.status, 422)
                after = self.bridge.load_dashboard_workflow_settings()
                self.assertEqual(after, before)
                self.assertEqual(
                    after["agentPreferences"]["rateReservePercent"],
                    37,
                )

    def test_malformed_persisted_thresholds_normalize_to_safe_default(self) -> None:
        malformed_values = (True, False, 12.5, "12", -1, 101, None)
        for malformed in malformed_values:
            with self.subTest(malformed=malformed), self.isolated_settings() as settings_path:
                payload = self.bridge._default_dashboard_workflow_settings()
                payload["agentPreferences"]["rateReservePercent"] = malformed
                self.bridge.write_json(settings_path, payload)

                stored = self.bridge.load_dashboard_workflow_settings()

                self.assertEqual(
                    stored["agentPreferences"]["rateReservePercent"],
                    self.bridge.AUTOMATION_MIN_REMAINING_PERCENT,
                )

    def test_gate_uses_lower_of_primary_and_secondary_and_allows_exact_threshold(self) -> None:
        with self.isolated_settings():
            self.bridge.save_automation_quota_policy({"rateReservePercent": 30})

            secondary_lower = self.bridge._collaboration_quota_gate(
                {"minRemainingPercent": 99},
                refresh=False,
                quota=self.quota(85, 29),
            )
            primary_lower = self.bridge._collaboration_quota_gate(
                {"minRemainingPercent": 0},
                refresh=False,
                quota=self.quota(25, 80),
            )
            exact_threshold = self.bridge._collaboration_quota_gate(
                {"minRemainingPercent": 99},
                refresh=False,
                quota=self.quota(30, 75),
            )

            self.assertFalse(secondary_lower["allowed"])
            self.assertEqual(secondary_lower["remainingPercent"], 29)
            self.assertEqual(secondary_lower["rateReservePercent"], 30)
            self.assertEqual(secondary_lower["reason"], "quota_below_reserve")
            self.assertFalse(primary_lower["allowed"])
            self.assertEqual(primary_lower["remainingPercent"], 25)
            self.assertTrue(exact_threshold["allowed"], exact_threshold)
            self.assertEqual(exact_threshold["remainingPercent"], 30)
            self.assertEqual(exact_threshold["reason"], "ready")

    def test_zero_allows_zero_but_never_overrides_provider_limit_reached(self) -> None:
        with self.isolated_settings():
            self.bridge.save_automation_quota_policy({"rateReservePercent": 0})

            available_zero = self.bridge._collaboration_quota_gate(
                {},
                refresh=False,
                quota=self.quota(0, 0),
            )
            provider_exhausted = self.bridge._collaboration_quota_gate(
                {},
                refresh=False,
                quota=self.quota(0, 0, limit_reached=True),
            )

            self.assertTrue(available_zero["allowed"], available_zero)
            self.assertEqual(available_zero["remainingPercent"], 0)
            self.assertEqual(available_zero["rateReservePercent"], 0)
            self.assertFalse(provider_exhausted["allowed"])
            self.assertEqual(provider_exhausted["reason"], "quota_limit_reached")

    def test_hundred_allows_only_a_full_remaining_window(self) -> None:
        with self.isolated_settings():
            self.bridge.save_automation_quota_policy({"rateReservePercent": 100})

            full = self.bridge._collaboration_quota_gate(
                {},
                refresh=False,
                quota=self.quota(100, 100),
            )
            below = self.bridge._collaboration_quota_gate(
                {},
                refresh=False,
                quota=self.quota(100, 99.99),
            )

            self.assertTrue(full["allowed"], full)
            self.assertFalse(below["allowed"], below)
            self.assertEqual(below["reason"], "quota_below_reserve")
            self.assertEqual(below["remainingPercent"], 99.99)

    def test_stale_and_unavailable_snapshots_are_blocked_at_every_threshold(self) -> None:
        with self.isolated_settings():
            for threshold in (0, 50, 100):
                self.bridge.save_automation_quota_policy(
                    {"rateReservePercent": threshold}
                )
                stale = self.bridge._collaboration_quota_gate(
                    {},
                    refresh=False,
                    quota=self.quota(100, stale=True),
                )
                unavailable = self.bridge._collaboration_quota_gate(
                    {},
                    refresh=False,
                    quota={"ok": False, "stale": False, "limitReached": False},
                )

                with self.subTest(threshold=threshold, kind="stale"):
                    self.assertFalse(stale["allowed"])
                    self.assertEqual(stale["reason"], "quota_stale")
                with self.subTest(threshold=threshold, kind="unavailable"):
                    self.assertFalse(unavailable["allowed"])
                    self.assertEqual(unavailable["reason"], "quota_unavailable")

    def test_malformed_quota_windows_fail_closed_even_when_threshold_is_zero(self) -> None:
        malformed_snapshots = {
            "missing_primary": {
                "ok": True,
                "stale": False,
                "limitReached": False,
            },
            "primary_bool": self.quota(True),
            "primary_nan": self.quota(float("nan")),
            "primary_inf": self.quota(float("inf")),
            "primary_negative": self.quota(-0.01),
            "primary_over_100": self.quota(100.01),
            "secondary_bool": {
                **self.quota(100),
                "secondary": {"remainingPercent": True},
            },
            "secondary_malformed": {
                **self.quota(100),
                "secondary": {"remainingPercent": "unknown"},
            },
        }
        with self.isolated_settings():
            self.bridge.save_automation_quota_policy({"rateReservePercent": 0})
            for case_name, snapshot in malformed_snapshots.items():
                with self.subTest(case=case_name):
                    result = self.bridge._collaboration_quota_gate(
                        {},
                        refresh=False,
                        quota=snapshot,
                    )
                    self.assertFalse(result["allowed"], result)
                    self.assertEqual(result["reason"], "quota_incomplete")
                    self.assertEqual(result["rateReservePercent"], 0)

    def test_existing_gate_object_picks_up_central_policy_changes_immediately(self) -> None:
        with self.isolated_settings():
            stale_embedded_config = {"minRemainingPercent": 15}
            quota = self.quota(50, 80)

            self.bridge.save_automation_quota_policy({"rateReservePercent": 70})
            before_change = self.bridge._collaboration_quota_gate(
                stale_embedded_config,
                refresh=False,
                quota=quota,
            )
            self.bridge.save_automation_quota_policy({"rateReservePercent": 20})
            after_change = self.bridge._collaboration_quota_gate(
                stale_embedded_config,
                refresh=False,
                quota=quota,
            )

            self.assertFalse(before_change["allowed"])
            self.assertEqual(before_change["rateReservePercent"], 70)
            self.assertTrue(after_change["allowed"], after_change)
            self.assertEqual(after_change["rateReservePercent"], 20)

    def test_policy_change_reschedules_only_quota_deferred_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, ExitStack() as stack:
            root = Path(temp_dir)
            settings_path = root / "dashboard-workflow-settings.json"
            missions_path = root / "missions.json"
            stack.enter_context(
                mock.patch.object(
                    self.bridge,
                    "DASHBOARD_WORKFLOW_SETTINGS_PATH",
                    settings_path,
                )
            )
            stack.enter_context(
                mock.patch.object(self.bridge, "MISSIONS_PATH", missions_path)
            )
            settings = self.bridge._default_dashboard_workflow_settings()
            settings["discoverySchedule"].update(
                {
                    "lastRunStatus": "blocked",
                    "lastResultKind": "quota_below_reserve",
                    "lastError": "waiting for quota",
                    "lastErrorAt": "2026-09-11T00:00:00+00:00",
                }
            )
            settings["indicatorScoutSchedule"].update(
                {
                    "lastRunStatus": "blocked",
                    "lastResultKind": "safety_contract_failed",
                    "lastError": "keep this failure",
                }
            )
            self.bridge.write_json(settings_path, settings)
            self.bridge.write_json(
                missions_path,
                {
                    "missions": [
                        {
                            "id": "quota-deferred",
                            "status": "queued",
                            "autoEligible": True,
                            "executionMode": "auto_guarded",
                            "execution": {
                                "dispatchState": "deferred",
                                "lastDeferredReason": "quota_below_reserve",
                                "nextAttemptAt": "2099-01-01T00:00:00+00:00",
                            },
                        },
                        {
                            "id": "safety-deferred",
                            "status": "queued",
                            "autoEligible": True,
                            "executionMode": "auto_guarded",
                            "execution": {
                                "dispatchState": "deferred",
                                "lastDeferredReason": "safety_contract_failed",
                                "nextAttemptAt": "2099-01-01T00:00:00+00:00",
                            },
                        },
                    ]
                },
            )
            self.bridge._invalidate_missions_read_cache()

            result = self.bridge._reschedule_quota_deferred_work()

            self.assertEqual(result["quotaDeferredMissionsRescheduled"], 1)
            self.assertEqual(result["quotaDeferredSchedulesRescheduled"], 1)
            missions = {
                item["id"]: item for item in self.bridge.load_missions()
            }
            self.assertIsNone(
                missions["quota-deferred"]["execution"]["nextAttemptAt"]
            )
            self.assertEqual(
                missions["safety-deferred"]["execution"]["nextAttemptAt"],
                "2099-01-01T00:00:00+00:00",
            )
            stored = self.bridge.load_dashboard_workflow_settings()
            self.assertEqual(
                stored["discoverySchedule"]["lastRunStatus"],
                "pending",
            )
            self.assertIsNone(
                stored["discoverySchedule"]["lastResultKind"]
            )
            self.assertEqual(
                stored["indicatorScoutSchedule"]["lastResultKind"],
                "safety_contract_failed",
            )

    def test_endpoint_wakes_consumers_only_when_threshold_changes(self) -> None:
        with self.isolated_settings():
            wake = self.bridge._wake_ai_quota_policy_consumers
            wake.return_value = {
                "quotaDeferredMissionsRescheduled": 0,
                "quotaDeferredSchedulesRescheduled": 0,
            }

            unchanged = self.bridge.save_automation_quota_policy(
                {"rateReservePercent": 15}
            )
            self.assertFalse(unchanged["queuedWorkersWoken"])
            wake.assert_not_called()

            changed = self.bridge.save_automation_quota_policy(
                {"rateReservePercent": 0}
            )
            self.assertTrue(changed["queuedWorkersWoken"])
            self.assertEqual(changed["quotaDeferredMissionsRescheduled"], 0)
            self.assertEqual(changed["quotaDeferredSchedulesRescheduled"], 0)
            wake.assert_called_once_with()

    def test_post_commit_audit_failure_does_not_turn_successful_save_into_error(self) -> None:
        with self.isolated_settings(), mock.patch.object(
            self.bridge,
            "append_audit",
            side_effect=OSError("simulated audit failure"),
        ):
            result = self.bridge.save_automation_quota_policy(
                {"rateReservePercent": 7}
            )
            stored = self.bridge.load_dashboard_workflow_settings()

        self.assertTrue(result["ok"])
        self.assertFalse(result["auditRecorded"])
        self.assertEqual(stored["agentPreferences"]["rateReservePercent"], 7)

    def test_post_commit_wake_failure_signals_consumers_and_returns_degraded_success(self) -> None:
        events = (
            self.bridge.MISSION_WORKER_WAKE,
            self.bridge.AI_TRADE_COUNCIL_AUTOMATION_WAKE,
            self.bridge.DASHBOARD_WORKFLOW_SCHEDULER_WAKE,
            self.bridge.COLLABORATION_SCHEDULER_WAKE,
        )
        for event in events:
            event.clear()
        with self.isolated_settings(), mock.patch.object(
            self.bridge,
            "_wake_ai_quota_policy_consumers",
            side_effect=OSError("simulated wake failure"),
        ):
            result = self.bridge.save_automation_quota_policy(
                {"rateReservePercent": 0}
            )
            stored = self.bridge.load_dashboard_workflow_settings()

        self.assertTrue(result["ok"])
        self.assertTrue(result["queuedWorkersWoken"])
        self.assertTrue(result["quotaRescheduleDegraded"])
        self.assertFalse(result["quotaRescheduleCountsReliable"])
        self.assertIsNone(result["quotaDeferredMissionsRescheduled"])
        self.assertIsNone(result["quotaDeferredSchedulesRescheduled"])
        self.assertEqual(result["quotaRescheduleErrorType"], "OSError")
        self.assertEqual(stored["agentPreferences"]["rateReservePercent"], 0)
        self.assertTrue(all(event.is_set() for event in events))

    def test_wake_retries_transient_reschedule_failure_before_signaling(self) -> None:
        events = (
            self.bridge.MISSION_WORKER_WAKE,
            self.bridge.AI_TRADE_COUNCIL_AUTOMATION_WAKE,
            self.bridge.DASHBOARD_WORKFLOW_SCHEDULER_WAKE,
            self.bridge.COLLABORATION_SCHEDULER_WAKE,
        )
        for event in events:
            event.clear()
        with mock.patch.object(
            self.bridge,
            "_reschedule_quota_deferred_work",
            side_effect=[
                OSError("transient replace failure"),
                {
                    "quotaDeferredMissionsRescheduled": 2,
                    "quotaDeferredSchedulesRescheduled": 1,
                },
            ],
        ) as reschedule:
            result = self.bridge._wake_ai_quota_policy_consumers()

        self.assertEqual(reschedule.call_count, 2)
        self.assertEqual(result["quotaDeferredMissionsRescheduled"], 2)
        self.assertEqual(result["quotaDeferredSchedulesRescheduled"], 1)
        self.assertFalse(result["quotaRescheduleDegraded"])
        self.assertTrue(result["quotaRescheduleCountsReliable"])
        self.assertTrue(result["quotaConsumersSignaled"])
        self.assertTrue(all(event.is_set() for event in events))


class AutomationQuotaPolicyRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_module("automation_quota_policy_runner", RUNNER_PATH)

    @staticmethod
    def quota(primary: float, secondary: float | None = None, **overrides) -> dict:
        snapshot = {
            "ok": True,
            "stale": False,
            "limitReached": False,
            "primary": {"remainingPercent": primary},
        }
        if secondary is not None:
            snapshot["secondary"] = {"remainingPercent": secondary}
        snapshot.update(overrides)
        return snapshot

    def test_corrective_verifier_uses_configured_threshold_and_exact_boundary(self) -> None:
        snapshot = self.quota(50, 80)

        with (
            mock.patch.object(
                self.runner,
                "TRADING_SYSTEM_CORRECTIVE_MIN_REMAINING_PERCENT",
                70,
            ),
            mock.patch.object(self.runner, "read_rate_limits", return_value=snapshot),
            self.assertRaisesRegex(ValueError, "at or above 70 percent"),
        ):
            self.runner.require_fresh_corrective_verifier_quota()

        full = self.quota(100, 100)
        with (
            mock.patch.object(
                self.runner,
                "TRADING_SYSTEM_CORRECTIVE_MIN_REMAINING_PERCENT",
                100,
            ),
            mock.patch.object(self.runner, "read_rate_limits", return_value=full),
        ):
            self.assertIs(self.runner.require_fresh_corrective_verifier_quota(), full)

        secondary_below = self.quota(100, 99.99)
        with (
            mock.patch.object(
                self.runner,
                "TRADING_SYSTEM_CORRECTIVE_MIN_REMAINING_PERCENT",
                100,
            ),
            mock.patch.object(
                self.runner,
                "read_rate_limits",
                return_value=secondary_below,
            ),
            self.assertRaisesRegex(ValueError, "at or above 100 percent"),
        ):
            self.runner.require_fresh_corrective_verifier_quota()

        with (
            mock.patch.object(
                self.runner,
                "TRADING_SYSTEM_CORRECTIVE_MIN_REMAINING_PERCENT",
                50,
            ),
            mock.patch.object(self.runner, "read_rate_limits", return_value=snapshot),
        ):
            self.assertIs(
                self.runner.require_fresh_corrective_verifier_quota(),
                snapshot,
            )

    def test_corrective_verifier_zero_and_hundred_boundaries_follow_central_semantics(self) -> None:
        zero = self.quota(0, 0)
        with (
            mock.patch.object(
                self.runner,
                "TRADING_SYSTEM_CORRECTIVE_MIN_REMAINING_PERCENT",
                0,
            ),
            mock.patch.object(self.runner, "read_rate_limits", return_value=zero),
        ):
            self.assertIs(self.runner.require_fresh_corrective_verifier_quota(), zero)

        limited_zero = self.quota(0, 0, limitReached=True)
        with (
            mock.patch.object(
                self.runner,
                "TRADING_SYSTEM_CORRECTIVE_MIN_REMAINING_PERCENT",
                0,
            ),
            mock.patch.object(
                self.runner,
                "read_rate_limits",
                return_value=limited_zero,
            ),
            self.assertRaises(ValueError),
        ):
            self.runner.require_fresh_corrective_verifier_quota()

    def test_semantic_repair_child_is_not_started_when_fresh_gate_blocks(self) -> None:
        with (
            mock.patch.object(
                self.runner,
                "require_fresh_corrective_verifier_quota",
                side_effect=ValueError("quota is below the central threshold"),
            ),
            mock.patch.object(self.runner, "run_chat_command") as child,
        ):
            result = self.runner.run_quota_guarded_semantic_repair(
                ["codex", "exec"],
                timeout=30,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "quota_guard_blocked")
        self.assertFalse(result["processStarted"])
        self.assertTrue(result["quotaGuarded"])
        child.assert_not_called()

    def test_semantic_repair_child_runs_at_the_exact_allowed_boundary(self) -> None:
        child_result = {
            "ok": True,
            "status": "completed",
            "processStarted": True,
        }
        with (
            mock.patch.object(
                self.runner,
                "require_fresh_corrective_verifier_quota",
                return_value=self.quota(15, 15),
            ),
            mock.patch.object(
                self.runner,
                "run_chat_command",
                return_value=child_result,
            ) as child,
        ):
            result = self.runner.run_quota_guarded_semantic_repair(
                ["codex", "exec"],
                timeout=30,
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["quotaGuarded"])
        child.assert_called_once()

    def test_each_corrective_child_rechecks_quota_before_process_start(self) -> None:
        urls = [
            "https://public-source1.example/system-1",
            "https://public-source2.example/system-1",
            "https://public-source3.example/system-2",
        ]
        allowed_at_boundary = self.quota(15, 15)

        def run_first_child(command, **_kwargs):
            final_path = Path(command[command.index("-o") + 1])
            final_path.write_text('{"status":"completed"}', encoding="utf-8")
            completed_item = {
                "id": "first-corrective-open",
                "type": "web_search",
                "query": urls[1],
                "action": {"type": "other"},
            }
            started_item = {**completed_item, "query": ""}
            return {
                "ok": True,
                "exitCode": 0,
                "durationMs": 1,
                "processStarted": True,
                "processTreeTerminated": False,
                "stdout": "\n".join((
                    json.dumps({"type": "item.started", "item": started_item}),
                    json.dumps({"type": "item.completed", "item": completed_item}),
                )),
                "stderr": "",
            }

        with (
            mock.patch.object(
                self.runner,
                "require_fresh_corrective_verifier_quota",
                side_effect=(
                    allowed_at_boundary,
                    ValueError("quota is below the central threshold"),
                ),
            ) as gate,
            mock.patch.object(
                self.runner,
                "run_chat_command",
                side_effect=run_first_child,
            ) as child,
            self.assertRaisesRegex(ValueError, "below the central threshold"),
        ):
            self.runner._complete_corrective_public_open_urls(
                urls,
                [urls[0]],
                model_name=None,
                working_directory=PROJECT_ROOT,
                deadline_monotonic=10**12,
                maximum_children=2,
                main_open_error="main open required",
                child_limit_error="too many children",
                completion_error="incomplete",
            )

        self.assertEqual(gate.call_count, 2)
        child.assert_called_once()


if __name__ == "__main__":
    unittest.main()
