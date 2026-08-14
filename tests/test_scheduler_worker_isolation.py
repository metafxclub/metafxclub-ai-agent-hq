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
        "metafx_scheduler_worker_isolation_bridge",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SchedulerWorkerIsolationTests(unittest.TestCase):
    """Release requirements for truthful worker health and per-device queues."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        self.bridge.DASHBOARD_WORKFLOW_SCHEDULER_STOP.clear()
        self.bridge.DASHBOARD_WORKFLOW_SCHEDULER_WAKE.clear()

    def _healthy_scheduler(self) -> dict:
        now = self.bridge.utc_now()
        return {
            "status": "running",
            "alive": True,
            "operational": True,
            "operationalReason": None,
            "heartbeatStale": False,
            "heartbeatAgeSeconds": 0.0,
            "lastHeartbeatAt": now,
            "lastSuccessAt": now,
        }

    def _worker_model(
        self,
        *,
        status: str = "idle",
        alive: bool = True,
        heartbeat: str | None = None,
        watchdog_alive: bool = True,
        operational: bool | None = None,
        reason: str | None = None,
    ) -> dict:
        if heartbeat is None and alive:
            heartbeat = self.bridge.utc_now()
        if operational is None:
            operational = bool(
                alive
                and watchdog_alive
                and status in {"starting", "idle", "running"}
                and heartbeat
            )
        return {
            "status": status,
            "alive": alive,
            "operational": operational,
            "operationalReason": reason,
            "heartbeatAt": heartbeat,
            "heartbeatStale": reason == "heartbeat_stale",
            "heartbeatAgeSeconds": 0.0 if heartbeat and reason != "heartbeat_stale" else None,
            "watchdogAlive": watchdog_alive,
            "workerId": "mission-worker-test" if alive else None,
            "currentMissionId": None,
            "queued": 0,
            "lastError": None if operational else reason,
        }

    def _scheduled_context(self, prop_id: str, action_id: str) -> dict:
        return {
            "schemaVersion": "dashboard-workflow-lineage-v1",
            "propId": prop_id,
            "actionId": action_id,
            "inputs": {},
            "inputDigest": "0" * 64,
            "submittedAt": "2026-08-10T02:00:00Z",
            "triggerSource": "schedule",
        }

    def _active_scheduled_mission(self, prop_id: str, action_id: str) -> dict:
        return {
            "id": f"mission-active-{prop_id}",
            "status": "running",
            "workflowContext": self._scheduled_context(prop_id, action_id),
        }

    def test_runtime_health_fails_closed_when_mission_worker_is_not_operational(self) -> None:
        """A healthy scheduler cannot mask a dead or unsafe execution worker."""

        healthy_worker = self._worker_model()
        with (
            mock.patch.object(
                self.bridge,
                "dashboard_workflow_scheduler_read_model",
                return_value=self._healthy_scheduler(),
            ),
            mock.patch.object(
                self.bridge,
                "mission_worker_read_model",
                return_value=healthy_worker,
            ),
        ):
            baseline = self.bridge.runtime_health()
        self.assertTrue(baseline["ok"], "The project fixture must be healthy first")

        cases = {
            "stopped": self._worker_model(
                status="stopped",
                alive=False,
                heartbeat=None,
                operational=False,
                reason="worker_thread_not_alive",
            ),
            "degraded": self._worker_model(
                status="degraded",
                operational=False,
                reason="runtime_degraded",
            ),
            "stale": self._worker_model(
                heartbeat="2000-01-01T00:00:00Z",
                operational=False,
                reason="heartbeat_stale",
            ),
            "watchdog_dead": self._worker_model(
                watchdog_alive=False,
                operational=False,
                reason="watchdog_not_alive",
            ),
        }
        for label, worker in cases.items():
            with (
                self.subTest(label=label),
                mock.patch.object(
                    self.bridge,
                    "dashboard_workflow_scheduler_read_model",
                    return_value=self._healthy_scheduler(),
                ),
                mock.patch.object(
                    self.bridge,
                    "mission_worker_read_model",
                    return_value=worker,
                ),
            ):
                health = self.bridge.runtime_health()

            self.assertFalse(health["ok"])
            self.assertEqual(health["status"], "degraded")
            self.assertIn("missionWorker", health)
            self.assertFalse(health["missionWorker"]["operational"])

    def test_scheduler_gate_rejects_non_operational_mission_worker(self) -> None:
        """The scheduler must not enqueue work that no healthy worker can execute."""

        cases = {
            "stopped": self._worker_model(
                status="stopped",
                alive=False,
                heartbeat=None,
                operational=False,
                reason="worker_thread_not_alive",
            ),
            "degraded": self._worker_model(
                status="degraded",
                operational=False,
                reason="runtime_degraded",
            ),
            "stale": self._worker_model(
                heartbeat="2000-01-01T00:00:00Z",
                operational=False,
                reason="heartbeat_stale",
            ),
            "watchdog_dead": self._worker_model(
                watchdog_alive=False,
                operational=False,
                reason="watchdog_not_alive",
            ),
        }
        for label, worker in cases.items():
            with (
                self.subTest(label=label),
                mock.patch.object(
                    self.bridge,
                    "load_operator_mode_record",
                    return_value={"mode": "auto_guarded"},
                ),
                mock.patch.object(
                    self.bridge,
                    "bridge_status",
                    return_value={"codex": {"status": "ready_guarded"}},
                ),
                mock.patch.object(
                    self.bridge,
                    "mission_worker_read_model",
                    return_value=worker,
                ),
                mock.patch.object(
                    self.bridge,
                    "_collaboration_quota_gate",
                    return_value={"allowed": True, "reason": "ready"},
                ) as quota_gate,
            ):
                gate = self.bridge._dashboard_workflow_scheduler_gate(
                    refresh_quota=False
                )

            self.assertFalse(gate["allowed"])
            self.assertEqual(gate["reason"], "mission_worker_not_operational")
            quota_gate.assert_not_called()

    def test_active_prop_a_schedule_does_not_block_due_prop_b(self) -> None:
        """A busy device stays serialized while another independent device proceeds."""

        due_at = datetime(
            2026,
            8,
            10,
            9,
            0,
            tzinfo=self.bridge.THAILAND_TIMEZONE,
        )
        active = self._active_scheduled_mission(
            "codex_mcp_portal",
            "discover_trading_systems",
        )
        dispatched: list[tuple[str, dict, str]] = []

        def fake_action(prop_id: str, payload: dict, *, trusted_trigger_source: str) -> dict:
            dispatched.append((prop_id, payload, trusted_trigger_source))
            return {
                "ok": True,
                "kind": "mission_auto_queued",
                "mission": {"id": "mission-prop-b", "status": "queued"},
                "idempotentReplay": False,
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "dashboard-workflow-settings.json"
            with (
                mock.patch.object(
                    self.bridge,
                    "DASHBOARD_WORKFLOW_SETTINGS_PATH",
                    settings_path,
                ),
                mock.patch.object(self.bridge, "load_missions", return_value=[active]),
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
                self.bridge._save_dashboard_schedule_preference(
                    "newsBiasSchedule",
                    {"enabled": False, "times": ["00:00", "12:00"]},
                )
                self.bridge._save_dashboard_schedule_preference(
                    "indicatorScoutSchedule",
                    {"enabled": False, "times": ["09:00"]},
                )
                self.bridge.save_dashboard_discovery_schedule(
                    {"enabled": True, "times": ["09:00"]}
                )
                self.bridge._save_dashboard_schedule_preference(
                    "indicatorScoutSchedule",
                    {"enabled": True, "times": ["09:00"]},
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

    def test_active_schedule_still_serializes_the_same_prop(self) -> None:
        """A second scheduled mission must not overlap work on the same device."""

        due_at = datetime(
            2026,
            8,
            10,
            9,
            0,
            tzinfo=self.bridge.THAILAND_TIMEZONE,
        )
        active = self._active_scheduled_mission(
            "codex_mcp_portal",
            "discover_trading_systems",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "dashboard-workflow-settings.json"
            with (
                mock.patch.object(
                    self.bridge,
                    "DASHBOARD_WORKFLOW_SETTINGS_PATH",
                    settings_path,
                ),
                mock.patch.object(self.bridge, "load_missions", return_value=[active]),
                mock.patch.object(self.bridge, "append_audit"),
                mock.patch.object(
                    self.bridge,
                    "_dashboard_workflow_scheduler_gate",
                    return_value={"allowed": True, "reason": "ready"},
                ),
                mock.patch.object(
                    self.bridge,
                    "run_dashboard_workflow_action",
                ) as runner,
            ):
                self.bridge._save_dashboard_schedule_preference(
                    "newsBiasSchedule",
                    {"enabled": False, "times": ["00:00", "12:00"]},
                )
                self.bridge._save_dashboard_schedule_preference(
                    "indicatorScoutSchedule",
                    {"enabled": False, "times": ["09:00"]},
                )
                self.bridge.save_dashboard_discovery_schedule(
                    {"enabled": True, "times": ["09:00"]}
                )
                result = self.bridge.dashboard_workflow_scheduler_tick(
                    due_at,
                    refresh_quota=False,
                )
                stored = self.bridge.load_dashboard_workflow_settings()

        self.assertFalse(result["dispatched"])
        runner.assert_not_called()
        self.assertIsNotNone(stored["discoverySchedule"]["pendingSlotKey"])


if __name__ == "__main__":
    unittest.main()
