from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge(name: str = "radar_retry_quarantine_bridge"):
    spec = importlib.util.spec_from_file_location(name, BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RadarRetryQuarantineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        self.bridge._invalidate_missions_read_cache()

    def runtime(self, temp_dir: str) -> ExitStack:
        root = Path(temp_dir)
        runtime = root / "data" / "runtime"
        stack = ExitStack()
        stack.enter_context(mock.patch.object(self.bridge, "PROJECT_ROOT", root))
        stack.enter_context(mock.patch.object(self.bridge, "RUNTIME_DIR", runtime))
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "MISSIONS_PATH",
                runtime / "missions.json",
            )
        )
        stack.enter_context(
            mock.patch.object(self.bridge, "AUDIT_PATH", runtime / "audit.jsonl")
        )
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "OPERATOR_MODE_PATH",
                runtime / "operator.json",
            )
        )
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "DASHBOARD_WORKFLOW_SETTINGS_PATH",
                runtime / "dashboard-workflow-settings.json",
            )
        )
        self.bridge._invalidate_missions_read_cache()
        return stack

    def scheduled_radar(self, slot_date: str) -> tuple[dict, str]:
        slot_key = f"indicatorScoutSchedule:{slot_date}:0900"
        response = self.bridge.run_dashboard_workflow_action(
            "left_audit_crystals",
            {
                "actionId": "discover_new_indicators",
                "form": {},
                "idempotencyKey": f"dashboard-schedule:{slot_key}",
            },
            trusted_trigger_source="schedule",
        )
        mission = response["mission"]
        self.bridge._dashboard_workflow_update_schedule_state(
            "indicatorScoutSchedule",
            {
                "requestedEnabled": True,
                "lastMissionId": mission["id"],
                "lastSlotKey": slot_key,
                "lastAttemptSlotKey": slot_key,
                "dailyExecutionDate": slot_date,
                "dailyExecutionCount": 1,
                "dailyExecutionSlotKeys": [slot_key],
            },
        )
        return mission, slot_key

    def apply_generic_retry(self, mission: dict, *, code: str) -> None:
        applied = self.bridge._apply_scheduled_public_research_completion_retry(
            mission,
            failure_code=code,
            failure_summary="Synthetic permanent public upstream failure.",
        )
        self.assertTrue(applied)

    def apply_batch_retry(self, temp_dir: str, mission: dict) -> None:
        artifact = (
            Path(temp_dir)
            / "data"
            / "runtime"
            / "codex-runs"
            / "permanent-radar-failure.final.md"
        )
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("permanent invalid Radar batch", encoding="utf-8")
        reference = artifact.relative_to(Path(temp_dir)).as_posix()
        applied = self.bridge._apply_scheduled_radar_batch_completion_repair(
            mission,
            {
                "artifactPath": reference,
                "artifactDigest": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "observedItemCount": 0,
                "failureReasonCode": "radar_batch_attempt_incomplete",
            },
            requeued_at=self.bridge.utc_now(),
        )
        self.assertTrue(applied)

    def test_generic_retry_attempt_ceiling_quarantines_and_releases_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            today = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
            mission, _slot_key = self.scheduled_radar(today)
            for _ in range(
                self.bridge.SCHEDULED_RADAR_COMPLETION_RETRY_MAX_ATTEMPTS
            ):
                self.apply_generic_retry(mission, code="runner_failed")
            self.bridge.replace_mission(mission)
            self.bridge._dashboard_workflow_update_schedule_state(
                "indicatorScoutSchedule",
                {
                    "carryForwardBlockDate": today,
                    "carryForwardMissionId": mission["id"],
                },
            )

            quarantined = self.bridge._expire_prior_day_radar_mission(mission)
            stored = self.bridge.find_mission(mission["id"])
            schedule = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]
            audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)

        self.assertTrue(quarantined)
        self.assertEqual(stored["status"], "blocked")
        self.assertEqual(stored["errorCode"], "radar_retry_quarantined")
        retry = stored["scheduledCompletionRetry"]
        self.assertEqual(retry["status"], "quarantined")
        self.assertEqual(retry["remainingAttempts"], 0)
        self.assertFalse(retry["automaticRetry"])
        self.assertEqual(
            retry["forensicFailure"]["failureSummary"],
            "Synthetic permanent public upstream failure.",
        )
        self.assertIsNone(schedule["carryForwardBlockDate"])
        self.assertIsNone(schedule["carryForwardMissionId"])
        event = next(
            row
            for row in audit
            if row.get("type") == "mission.radar_retry_quarantined"
        )
        self.assertEqual(event["quarantineReason"], "maximum_attempts_exhausted")
        self.assertTrue(event["carryForwardReleased"])
        self.assertTrue(event["forensicFailureRetained"])

    def test_batch_failure_carries_one_day_then_age_quarantines_with_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            base_day = datetime.now(self.bridge.THAILAND_TIMEZONE).date()
            slot_day = base_day - timedelta(days=1)
            mission, _slot_key = self.scheduled_radar(slot_day.isoformat())
            self.apply_batch_retry(temp_dir, mission)
            self.bridge.replace_mission(mission)

            first_day = datetime.combine(
                base_day,
                datetime.min.time(),
                tzinfo=self.bridge.THAILAND_TIMEZONE,
            ).replace(hour=9, minute=1)
            with mock.patch.object(
                self.bridge,
                "_dashboard_scheduler_local_now",
                return_value=first_day,
            ):
                carried = self.bridge._expire_prior_day_radar_mission(mission)
            carried_mission = self.bridge.find_mission(mission["id"])

            second_day = first_day + timedelta(days=1)
            with mock.patch.object(
                self.bridge,
                "_dashboard_scheduler_local_now",
                return_value=second_day,
            ):
                quarantined = self.bridge._expire_prior_day_radar_mission(
                    carried_mission
                )
            stored = self.bridge.find_mission(mission["id"])
            schedule = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]

        self.assertTrue(carried)
        self.assertTrue(carried_mission["radarBatchRepair"]["overdueCarryForward"])
        self.assertTrue(quarantined)
        self.assertEqual(stored["status"], "blocked")
        repair = stored["radarBatchRepair"]
        self.assertEqual(repair["status"], "quarantined")
        self.assertEqual(
            repair["quarantineReason"],
            "maximum_carry_forward_age_exhausted",
        )
        self.assertEqual(
            repair["latestFailureArtifact"],
            "data/runtime/codex-runs/permanent-radar-failure.final.md",
        )
        self.assertEqual(
            repair["forensicFailure"]["failureReasonCode"],
            "radar_batch_attempt_incomplete",
        )
        self.assertIsNone(schedule["carryForwardBlockDate"])
        self.assertIsNone(schedule["carryForwardMissionId"])

    def test_generic_upstream_failure_carries_one_day_then_releases_next_day(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            base_day = datetime.now(self.bridge.THAILAND_TIMEZONE).date()
            slot_day = base_day - timedelta(days=1)
            mission, _slot_key = self.scheduled_radar(slot_day.isoformat())
            self.apply_generic_retry(mission, code="runner_failed")
            self.bridge.replace_mission(mission)
            first_day = datetime.combine(
                base_day,
                datetime.min.time(),
                tzinfo=self.bridge.THAILAND_TIMEZONE,
            ).replace(hour=9, minute=1)
            with mock.patch.object(
                self.bridge,
                "_dashboard_scheduler_local_now",
                return_value=first_day,
            ):
                self.assertTrue(
                    self.bridge._expire_prior_day_radar_mission(mission)
                )
            carried = self.bridge.find_mission(mission["id"])
            with mock.patch.object(
                self.bridge,
                "_dashboard_scheduler_local_now",
                return_value=first_day + timedelta(days=1),
            ):
                self.assertTrue(
                    self.bridge._expire_prior_day_radar_mission(carried)
                )
            stored = self.bridge.find_mission(mission["id"])
            schedule = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]

        self.assertEqual(stored["status"], "blocked")
        self.assertEqual(
            stored["scheduledCompletionRetry"]["quarantineReason"],
            "maximum_carry_forward_age_exhausted",
        )
        self.assertEqual(
            stored["scheduledCompletionRetry"]["forensicFailure"][
                "failureCode"
            ],
            "runner_failed",
        )
        self.assertIsNone(schedule["carryForwardBlockDate"])
        self.assertIsNone(schedule["carryForwardMissionId"])


if __name__ == "__main__":
    unittest.main()
