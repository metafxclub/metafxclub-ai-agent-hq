from __future__ import annotations

import importlib.util
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_scheduler_lifecycle_regression_bridge",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SchedulerLifecycleRegressionTests(unittest.TestCase):
    """Release requirements for truthful, independent dashboard automation."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        self.bridge.DASHBOARD_WORKFLOW_SCHEDULER_STOP.clear()
        self.bridge.DASHBOARD_WORKFLOW_SCHEDULER_WAKE.clear()

    def _scheduler_model(
        self,
        *,
        status: str,
        alive: bool,
        heartbeat: str | None,
    ) -> dict:
        return {
            "status": status,
            "alive": alive,
            "startedAt": "2026-08-09T00:00:00Z",
            "lastHeartbeatAt": heartbeat,
            "lastSuccessAt": heartbeat,
            "lastError": None if status == "running" else "scheduler_not_operational",
            "lastErrorAt": None if status == "running" else heartbeat,
            "timezone": "Asia/Bangkok",
            "pollSeconds": self.bridge.DASHBOARD_WORKFLOW_SCHEDULER_POLL_SECONDS,
        }

    def test_runtime_health_fails_closed_for_stopped_degraded_or_stale_scheduler(self) -> None:
        """HTTP health must make the watchdog restart a non-operational scheduler."""

        operational = self._scheduler_model(
            status="running",
            alive=True,
            heartbeat=self.bridge.utc_now(),
        )
        healthy_worker = {
            "status": "idle",
            "alive": True,
            "operational": True,
            "operationalReason": None,
            "watchdogAlive": True,
            "heartbeatAt": self.bridge.utc_now(),
            "heartbeatStale": False,
        }
        with (
            mock.patch.object(
                self.bridge,
                "dashboard_workflow_scheduler_read_model",
                return_value=operational,
            ),
            mock.patch.object(
                self.bridge,
                "mission_worker_read_model",
                return_value=healthy_worker,
            ),
        ):
            baseline = self.bridge.runtime_health()
        self.assertTrue(baseline["ok"], "The fixture must start from a healthy project state")

        cases = {
            "stopped": self._scheduler_model(
                status="stopped",
                alive=False,
                heartbeat=None,
            ),
            "degraded": self._scheduler_model(
                status="degraded",
                alive=True,
                heartbeat=self.bridge.utc_now(),
            ),
            "stale": self._scheduler_model(
                status="running",
                alive=True,
                heartbeat="2000-01-01T00:00:00Z",
            ),
        }
        for label, scheduler in cases.items():
            with (
                self.subTest(label=label),
                mock.patch.object(
                    self.bridge,
                    "dashboard_workflow_scheduler_read_model",
                    return_value=scheduler,
                ),
                mock.patch.object(
                    self.bridge,
                    "mission_worker_read_model",
                    return_value=healthy_worker,
                ),
            ):
                health = self.bridge.runtime_health()
                self.assertFalse(health["ok"])
                self.assertEqual(health["status"], "degraded")

    def test_schedule_effective_enabled_requires_operational_scheduler(self) -> None:
        """A saved schedule is not effectively enabled while its scheduler is unhealthy."""

        settings = self.bridge._default_dashboard_workflow_settings()
        settings["discoverySchedule"]["requestedEnabled"] = True
        settings["discoverySchedule"]["times"] = ["09:00"]
        cases = {
            "stopped": (False, "stopped", None),
            "degraded": (True, "degraded", self.bridge.utc_now()),
            "stale": (True, "running", "2000-01-01T00:00:00Z"),
        }
        for label, (thread_alive, status, heartbeat) in cases.items():
            scheduler = self._scheduler_model(
                status=status,
                alive=thread_alive,
                heartbeat=heartbeat,
            )
            runtime = dict(self.bridge.DASHBOARD_WORKFLOW_SCHEDULER_RUNTIME)
            runtime.update(
                status=status,
                lastHeartbeatAt=heartbeat,
                lastError=scheduler["lastError"],
                lastErrorAt=scheduler["lastErrorAt"],
            )
            thread = mock.Mock()
            thread.is_alive.return_value = thread_alive
            with (
                self.subTest(label=label),
                mock.patch.object(
                    self.bridge,
                    "DASHBOARD_WORKFLOW_SCHEDULER_THREAD",
                    thread,
                ),
                mock.patch.dict(
                    self.bridge.DASHBOARD_WORKFLOW_SCHEDULER_RUNTIME,
                    runtime,
                    clear=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "dashboard_workflow_scheduler_read_model",
                    return_value=scheduler,
                ),
            ):
                model = self.bridge._dashboard_schedule_read_model(
                    "discoverySchedule",
                    default_times=["09:00"],
                    settings=settings,
                )
                self.assertTrue(model["requestedEnabled"])
                self.assertFalse(model["effectiveEnabled"])
                self.assertFalse(model["automaticExternalActions"])

    def test_gate_blocked_tick_is_not_counted_as_scheduler_success(self) -> None:
        """A handled gate failure is still a failed tick, not a healthy heartbeat success."""

        class StopAfterFirstWait:
            def __init__(self) -> None:
                self.stopped = False

            def is_set(self) -> bool:
                return self.stopped

        class WakeOnce:
            def __init__(self, stop: StopAfterFirstWait) -> None:
                self.stop = stop

            def wait(self, _timeout: float) -> bool:
                self.stop.stopped = True
                return True

            def clear(self) -> None:
                return None

        stop = StopAfterFirstWait()
        wake = WakeOnce(stop)
        updates: list[dict] = []

        with (
            mock.patch.object(self.bridge, "DASHBOARD_WORKFLOW_SCHEDULER_STOP", stop),
            mock.patch.object(self.bridge, "DASHBOARD_WORKFLOW_SCHEDULER_WAKE", wake),
            mock.patch.object(
                self.bridge,
                "dashboard_workflow_scheduler_tick",
                return_value={
                    "ok": False,
                    "kind": "quota_below_reserve",
                    "dispatched": False,
                },
            ),
            mock.patch.object(
                self.bridge,
                "_dashboard_workflow_scheduler_runtime_update",
                side_effect=lambda **values: updates.append(values),
            ),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            self.bridge.dashboard_workflow_scheduler_loop()

        self.assertFalse(
            any(update.get("lastSuccessAt") for update in updates),
            "A gate-blocked tick must not advance scheduler lastSuccessAt",
        )

    def test_retry_blocked_first_device_does_not_starve_other_due_device(self) -> None:
        """Independent devices must continue when the oldest due job is cooling down."""

        dispatched: list[tuple[str, dict, str]] = []

        def fake_action(prop_id: str, payload: dict, *, trusted_trigger_source: str) -> dict:
            dispatched.append((prop_id, payload, trusted_trigger_source))
            return {
                "ok": True,
                "kind": "mission_auto_queued",
                "mission": {
                    "id": "mission-indicator-not-starved",
                    "status": "queued",
                },
                "idempotentReplay": False,
            }

        due_at = datetime(
            2026,
            8,
            9,
            9,
            0,
            tzinfo=self.bridge.THAILAND_TIMEZONE,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "dashboard-workflow-settings.json"
            with (
                mock.patch.object(
                    self.bridge,
                    "DASHBOARD_WORKFLOW_SETTINGS_PATH",
                    settings_path,
                ),
                mock.patch.object(self.bridge, "load_missions", return_value=[]),
                mock.patch.object(self.bridge, "append_audit"),
                mock.patch.object(
                    self.bridge,
                    "_dashboard_workflow_scheduler_gate",
                    return_value={"allowed": True, "reason": "ready"},
                ),
                mock.patch.object(
                    self.bridge,
                    "run_dashboard_workflow_action",
                    side_effect=fake_action,
                ),
            ):
                self.bridge.save_dashboard_discovery_schedule(
                    {"enabled": True, "times": ["09:00"]}
                )
                self.bridge._save_dashboard_schedule_preference(
                    "indicatorScoutSchedule",
                    {"enabled": True, "times": ["09:00"]},
                )
                captured = self.bridge._dashboard_workflow_capture_due_slots(due_at)
                self.assertEqual(len(captured), 2)
                self.bridge._dashboard_workflow_update_schedule_state(
                    "discoverySchedule",
                    {
                        "lastAttemptAt": self.bridge.utc_now(),
                        "lastRunStatus": "blocked",
                        "lastError": "discovery_retry_cooldown",
                        "lastErrorAt": self.bridge.utc_now(),
                    },
                )

                result = self.bridge.dashboard_workflow_scheduler_tick(
                    due_at,
                    refresh_quota=False,
                )
                stored = self.bridge.load_dashboard_workflow_settings()

        self.assertTrue(result["dispatched"])
        self.assertEqual(len(dispatched), 1)
        self.assertEqual(dispatched[0][0], "left_audit_crystals")
        self.assertEqual(dispatched[0][1]["actionId"], "discover_new_indicators")
        self.assertEqual(dispatched[0][2], "schedule")
        self.assertIsNotNone(stored["discoverySchedule"]["pendingSlotKey"])
        self.assertIsNone(stored["indicatorScoutSchedule"]["pendingSlotKey"])

    def test_generic_bridge_run_rejects_reserved_scheduler_idempotency_prefix(self) -> None:
        """Only the trusted dashboard scheduler may mint dashboard-schedule keys."""

        mission = {
            "id": "mission-generic-prefix-poison",
            "owner": "manager",
            "toolId": "manager_mission",
            "targetId": "mission_strategy_table",
            "status": "queued",
            "approval": {"required": False},
        }
        with (
            mock.patch.object(
                self.bridge,
                "evaluate_tool_permission",
                return_value={
                    "allowed": True,
                    "policy": {"risk": "low", "adapterStatus": "runtime_detected"},
                },
            ),
            mock.patch.object(
                self.bridge,
                "tool_execution_capability_unavailable",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "find_room_prop",
                return_value={"id": "mission_strategy_table"},
            ),
            mock.patch.object(
                self.bridge,
                "load_agent_contracts",
                return_value=[{"id": "manager"}],
            ),
            mock.patch.object(
                self.bridge,
                "load_report_contract",
                return_value={"report_targets": {"prop_report": {}}},
            ),
            mock.patch.object(
                self.bridge,
                "find_mission_by_idempotency",
                return_value=None,
            ),
            mock.patch.object(
                self.bridge,
                "create_mission",
                return_value=mission,
            ) as create_mission,
            mock.patch.object(
                self.bridge,
                "bridge_status",
                return_value={"codex": {"status": "ready_guarded"}},
            ),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            result = self.bridge.run_bridge_task(
                {
                    "toolId": "manager_mission",
                    "agentId": "manager",
                    "requester": "manager",
                    "targetId": "mission_strategy_table",
                    "reportType": "prop_report",
                    "prompt": "Prepare a safe local summary.",
                    "idempotencyKey": (
                        "dashboard-schedule:discoverySchedule:2026-08-10:0900"
                    ),
                }
            )

        self.assertFalse(result["ok"])
        self.assertIn(result.get("_httpStatus"), {403, 422})
        create_mission.assert_not_called()


if __name__ == "__main__":
    unittest.main()
