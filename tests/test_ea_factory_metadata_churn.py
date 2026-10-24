from __future__ import annotations

import copy
import importlib.util
import json
import os
import tempfile
import unittest
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


class FactoryMetadataChurnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "factory_metadata_churn_bridge", ROOT / "backend/local-runner/bridge_server.py"
        )
        cls.bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.bridge)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings_path = self.root / "settings.json"
        self.outbox_path = self.root / "outbox.json"
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for name, value in {
            "PROJECT_ROOT": self.root,
            "RUNTIME_DIR": self.root,
            "DASHBOARD_WORKFLOW_SETTINGS_PATH": self.settings_path,
            "RESEARCH_SHEET_OUTBOX_PATH": self.outbox_path,
            "ensure_runtime_dir": lambda: None,
        }.items():
            self.stack.enter_context(mock.patch.object(self.bridge, name, value))
        self.settings = self.bridge._default_dashboard_workflow_settings()
        self.save_settings(self.settings)
        self.bridge.EA_FACTORY_READ_MODEL_CACHE.update(
            signature=None, value=None, refreshing=False, generation=0
        )

    def save_settings(self, settings):
        self.settings_path.write_text(json.dumps(settings), encoding="utf-8")

    def signature(self):
        with ExitStack() as stack:
            for name, value in {
                "_ea_factory_mission_projection_signature": ("missions",),
                "_ea_factory_report_store_signature": ("reports",),
                "_ea_factory_cache_file_signature": ("other-files",),
                "_ea_factory_workspace_signature": ("workspace",),
                "_existing_credit_grants": [],
            }.items():
                stack.enter_context(mock.patch.object(self.bridge, name, return_value=value))
            return self.bridge._ea_factory_read_model_signature({}, {}, {}, (), False, missions=[])

    def outbox(self):
        value = self.bridge._research_sheet_outbox_default()
        value["items"] = [{
            "id": "delivery-one", "status": "pending", "configRevision": 1,
            "payloadDigest": "a" * 64, "row": {"record_id": "one", "content": "original"},
            "updatedAt": "2026-10-19T01:00:00Z",
        }]
        return value

    def test_radar_bookkeeping_and_byte_identical_rewrite_do_not_invalidate_factory(self):
        baseline = self.signature()
        for schedule in ("discoverySchedule", "indicatorScoutSchedule"):
            changed = copy.deepcopy(self.settings)
            changed[schedule].update(lastAttemptAt="2026-10-19T02:00:00Z", lastErrorAt="2026-10-19T02:00:00Z")
            self.save_settings(changed)
            self.assertEqual(self.signature(), baseline)
        stat = self.settings_path.stat()
        os.utime(self.settings_path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))
        self.assertEqual(self.signature(), baseline)
        reordered = dict(reversed(list(changed.items())))
        self.settings_path.write_text(json.dumps(reordered, indent=4), "utf-8")
        self.assertEqual(self.signature(), baseline)

    def test_settings_file_removal_and_json_types_remain_distinct(self):
        baseline = self.signature()
        self.settings_path.unlink()
        self.assertNotEqual(self.signature(), baseline)
        values = []
        for value in (True, 1, 1.0):
            changed = copy.deepcopy(self.settings)
            changed["unknownControl"] = value
            self.save_settings(changed)
            values.append(self.signature())
        self.assertEqual(len(set(values)), 3)

    def test_every_control_error_configuration_and_unknown_field_remains_a_dependency(self):
        baseline = self.signature()
        mutations = [
            ("discoverySchedule", "lastRunStatus", "running"),
            ("discoverySchedule", "lastError", "quota_blocked"),
            ("discoverySchedule", "requestedEnabled", False),
            ("indicatorScoutSchedule", "lastResultKind", "different-result"),
            ("indicatorScoutSchedule", "times", ["10:00"]),
            ("researchSheetHub", "configRevision", 45),
            ("researchSheetHub", "active", True),
            ("existingCreditPolicy", "grants", [{"buildId": "another", "allowExistingCredits": True}]),
            ("unknownSettings", "lastAttemptAt", "must-not-be-ignored"),
            ("newsBiasSchedule", "lastErrorAt", "2026-10-19T02:00:00Z"),
        ]
        for section, field, value in mutations:
            with self.subTest(section=section, field=field):
                changed = copy.deepcopy(self.settings)
                changed.setdefault(section, {})[field] = value
                self.save_settings(changed)
                self.assertNotEqual(self.signature(), baseline)

    def test_corrupt_settings_never_fall_back_to_old_signature_or_backup(self):
        for raw in ("{broken", "[]", "null", '{"unknownControl":NaN}'):
            with self.subTest(raw=raw):
                self.settings_path.with_suffix(".json.bak").write_text(json.dumps(self.settings), "utf-8")
                self.settings_path.write_text(raw, "utf-8")
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.signature()
                self.assertEqual(self.settings_path.read_text("utf-8"), raw)

    def test_cold_factory_read_converges_during_unrelated_scheduler_updates(self):
        for name, value in {
            "peek_metatrader_status": {}, "_metatrader_selection_read_model": {},
            "_ea_factory_terminal_gate": {}, "research_sheet_hub_read_model": {},
            "_ea_factory_front_office_supported_platforms": (), "load_missions": [],
        }.items():
            self.stack.enter_context(mock.patch.object(self.bridge, name, return_value=value))
        self.stack.enter_context(mock.patch.object(
            self.bridge, "_ea_factory_read_model_signature", side_effect=lambda *a, **kw:
            self.bridge._ea_factory_settings_projection_signature()
        ))
        model = {"schemaVersion": "ea-factory-v1", "builds": [], "snapshotStale": False}

        def assemble(**kwargs):
            changed = copy.deepcopy(self.settings)
            changed["discoverySchedule"]["lastAttemptAt"] = "2026-10-19T02:00:00Z"
            changed["indicatorScoutSchedule"]["lastErrorAt"] = "2026-10-19T02:00:00Z"
            self.save_settings(changed)
            return model

        with mock.patch.object(self.bridge, "_ea_factory_read_model_uncached", side_effect=assemble) as build:
            self.assertEqual(self.bridge.ea_factory_read_model(http_read=True), model)
            self.assertEqual(self.bridge.ea_factory_read_model(http_read=True), model)
            self.assertEqual(build.call_count, 1)

    def test_outbox_noop_preserves_durable_timestamp_mtime_and_backup(self):
        self.bridge._save_research_sheet_outbox_unlocked(self.outbox())
        backup = self.outbox_path.with_suffix(".json.bak")
        backup.write_bytes(b'{"previous":"preserved"}')
        before = (self.outbox_path.read_bytes(), self.outbox_path.stat().st_mtime_ns, backup.read_bytes())
        value = self.bridge._load_research_sheet_outbox_unlocked()
        value["updatedAt"] = "2026-10-20T00:00:00Z"
        with mock.patch.object(self.bridge, "write_json", wraps=self.bridge.write_json) as write:
            self.bridge._save_research_sheet_outbox_unlocked(value)
            write.assert_not_called()
        after = (self.outbox_path.read_bytes(), self.outbox_path.stat().st_mtime_ns, backup.read_bytes())
        self.assertEqual(after, before)

    def test_nested_outbox_metadata_status_payload_and_revision_still_persist(self):
        self.bridge._save_research_sheet_outbox_unlocked(self.outbox())
        for field, value in (
            ("updatedAt", "2026-10-19T02:00:00Z"), ("status", "write_unknown"),
            ("payloadDigest", "b" * 64), ("configRevision", 2),
            ("row", {"record_id": "one", "content": "changed"}),
        ):
            with self.subTest(field=field):
                before = self.outbox_path.read_bytes()
                store = self.bridge._load_research_sheet_outbox_unlocked()
                store["items"][0][field] = value
                self.bridge._save_research_sheet_outbox_unlocked(store)
                self.assertNotEqual(self.outbox_path.read_bytes(), before)
                self.assertEqual(self.outbox_path.with_suffix(".json.bak").read_bytes(), before)
                self.assertEqual(json.loads(self.outbox_path.read_bytes())["items"][0][field], value)

    def test_outbox_numeric_and_boolean_values_do_not_compare_equal(self):
        self.bridge._save_research_sheet_outbox_unlocked(self.outbox())
        seen = []
        for value in (True, 1, 1.0):
            store = self.bridge._load_research_sheet_outbox_unlocked()
            store["items"][0]["row"]["typedControl"] = value
            with mock.patch.object(self.bridge, "write_json", wraps=self.bridge.write_json) as write:
                self.bridge._save_research_sheet_outbox_unlocked(store)
                write.assert_called_once()
            seen.append(self.outbox_path.read_bytes())
        self.assertEqual(len(set(seen)), 3)

    def test_invalid_outbox_primary_cannot_be_hidden_by_noop_or_overwrite_backup(self):
        candidate = self.outbox()
        for raw in (b"{broken", b"[]", b"null", b"\xff", b'{"unknownControl":NaN}'):
            with self.subTest(raw=raw):
                backup = self.outbox_path.with_suffix(".json.bak")
                backup.write_bytes(json.dumps(candidate).encode())
                old_backup = backup.read_bytes()
                self.outbox_path.write_bytes(raw)
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._save_research_sheet_outbox_unlocked(candidate)
                self.assertEqual(self.outbox_path.read_bytes(), raw)
                self.assertEqual(backup.read_bytes(), old_backup)

    def blocked_pending_fixture(self, mission_status="completed"):
        settings = copy.deepcopy(self.settings)
        schedule = settings["discoverySchedule"]
        schedule.update(
            lastMissionId="mission-previous-day", lastRunStatus="completed",
            lastRunAt="2026-10-18T02:00:00Z", lastSlotKey="discoverySchedule:2026-10-18:0900",
            pendingSlotKey="discoverySchedule:2026-10-19:0900", pendingScheduledAt="2026-10-19T02:00:00Z",
            dailyExecutionDate="2026-10-19", dailyExecutionCount=1,
            dailyExecutionSlotKeys=["discoverySchedule:2026-10-19:0900"],
        )
        self.save_settings(self.bridge._dashboard_workflow_settings_shape(settings))
        with mock.patch.object(self.bridge, "utc_now", return_value="2026-10-19T02:01:00Z"), \
             mock.patch.object(self.bridge, "append_audit"):
            self.bridge._dashboard_workflow_record_scheduler_error({
                "settingsKey": "discoverySchedule", "slotKey": "discoverySchedule:2026-10-19:0900",
            }, "codex_limit_reached", message="Official quota is currently exhausted")
        mission = {
            "id": "mission-previous-day", "status": mission_status,
            "completedAt": "2026-10-18T02:02:00Z", "updatedAt": "2026-10-18T02:02:00Z",
            "errorCode": "previous-day-failure",
        }
        return json.loads(self.settings_path.read_bytes()), mission

    def test_previous_terminal_mission_cannot_erase_newer_blocked_pending_attempt(self):
        for status in ("completed", "failed", "blocked", "cancelled"):
            with self.subTest(status=status):
                settings, mission = self.blocked_pending_fixture(status)
                before = self.settings_path.read_bytes()
                before_signature = self.signature()
                with mock.patch.object(self.bridge, "load_missions", return_value=[mission]):
                    for _ in range(3):
                        self.assertEqual(self.bridge._dashboard_workflow_reconcile_schedule_states(), 0)
                self.assertEqual(self.settings_path.read_bytes(), before)
                self.assertEqual(self.signature(), before_signature)
                after = json.loads(before)["discoverySchedule"]
                self.assertEqual(after["lastError"], settings["discoverySchedule"]["lastError"])
                self.assertFalse(self.bridge._dashboard_workflow_retry_ready(
                    after, datetime(2026, 10, 19, 2, 2, tzinfo=timezone.utc)
                ))
                self.assertTrue(self.bridge._dashboard_workflow_retry_ready(
                    after, datetime(2026, 10, 19, 2, 6, tzinfo=timezone.utc)
                ))

    def test_current_slot_or_active_or_newer_mission_still_reconciles(self):
        cases = ("same-slot", "active-mission", "newer-terminal", "missing-pending", "wrong-attempt-slot", "invalid-attempt-time")
        for case in cases:
            with self.subTest(case=case):
                settings, mission = self.blocked_pending_fixture()
                schedule = settings["discoverySchedule"]
                if case == "same-slot":
                    schedule["lastSlotKey"] = schedule["pendingSlotKey"]
                elif case == "active-mission":
                    mission["status"] = "running"
                elif case == "newer-terminal":
                    mission["completedAt"] = "2026-10-19T02:02:00Z"
                elif case == "missing-pending":
                    schedule["pendingSlotKey"] = None
                elif case == "wrong-attempt-slot":
                    schedule["lastAttemptSlotKey"] = "different-slot"
                else:
                    schedule["lastAttemptAt"] = "not-a-time"
                self.save_settings(settings)
                with mock.patch.object(self.bridge, "load_missions", return_value=[mission]):
                    self.assertEqual(self.bridge._dashboard_workflow_reconcile_schedule_states(), 1)
                after = json.loads(self.settings_path.read_bytes())["discoverySchedule"]
                self.assertEqual(after["lastRunStatus"], mission["status"])
                for key in ("dailyExecutionDate", "dailyExecutionCount", "dailyExecutionSlotKeys", "lastMissionId", "pendingSlotKey"):
                    self.assertEqual(after[key], schedule[key])

    def test_a_newly_dispatched_mission_replaces_blocked_attempt_normally(self):
        settings, previous_mission = self.blocked_pending_fixture()
        schedule = settings["discoverySchedule"]
        schedule.update(lastMissionId="mission-new-day", lastRunStatus="queued",
                        lastRunAt="2026-10-19T02:06:00Z", lastSlotKey=schedule["pendingSlotKey"],
                        pendingSlotKey=None, lastError=None, lastErrorAt=None)
        self.save_settings(settings)
        current = {"id": "mission-new-day", "status": "completed", "completedAt": "2026-10-19T02:08:00Z"}
        with mock.patch.object(self.bridge, "load_missions", return_value=[previous_mission, current]):
            self.assertEqual(self.bridge._dashboard_workflow_reconcile_schedule_states(), 1)
        after = json.loads(self.settings_path.read_bytes())["discoverySchedule"]
        self.assertEqual(after["lastRunStatus"], "completed")
        self.assertIsNone(after["lastError"])
        self.assertEqual(after["lastMissionId"], "mission-new-day")
        self.assertEqual(after["dailyExecutionCount"], 1)


if __name__ == "__main__":
    unittest.main()
