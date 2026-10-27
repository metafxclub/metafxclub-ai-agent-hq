from __future__ import annotations

import copy
import importlib.util
import json
import os
import tempfile
import threading
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock
from urllib.request import Request


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "backend" / "local-runner" / "bridge_server.py"


class ResearchSheetBackgroundBatchTests(unittest.TestCase):
    """Small-batch scheduling over synthetic local reports; no external work."""

    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("sheet_background_batch_bridge", BRIDGE_PATH)
        assert spec is not None and spec.loader is not None
        cls.bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.bridge)

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.runtime = self.root / "runtime"
        self.reports = self.runtime / "reports"
        self.reports.mkdir(parents=True)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.clock = 100.0
        self.stop = threading.Event()
        self.state = {}
        self.internal = {
            "sheetId": "1SyntheticBackgroundFixtureNoExternalAccount",
            "configRevision": 3,
            "activeConfigRevision": 3,
            "active": True,
        }
        replacements = {
            "RUNTIME_DIR": self.runtime,
            "RUNTIME_REPORTS_DIR": self.reports,
            "DASHBOARD_WORKFLOW_SETTINGS_PATH": self.runtime / "settings.json",
            "RESEARCH_SHEET_OUTBOX_PATH": self.runtime / "outbox.json",
            "RESEARCH_SHEET_CACHE_PATH": self.runtime / "cache.json",
            "DEEP_RESEARCH_CONFIRMATIONS_PATH": self.runtime / "confirmations.json",
            "MISSIONS_PATH": self.runtime / "missions.json",
            "AUDIT_PATH": self.runtime / "audit.jsonl",
            "DASHBOARD_WORKFLOW_SCHEDULER_STOP": self.stop,
        }
        for name, value in replacements.items():
            self.stack.enter_context(mock.patch.object(self.bridge, name, value))
        self.stack.enter_context(mock.patch.object(self.bridge.time, "monotonic", side_effect=lambda: self.clock))
        self.stack.enter_context(mock.patch.object(self.bridge, "_research_sheet_hub_internal", side_effect=lambda *_, **__: copy.deepcopy(self.internal)))
        self.stack.enter_context(mock.patch.object(self.bridge, "append_audit"))
        self.stack.enter_context(mock.patch.object(self.bridge, "urlopen", side_effect=AssertionError("Network is forbidden in batch tests")))
        self.stack.enter_context(mock.patch("socket.socket.connect", side_effect=AssertionError("Network is forbidden in batch tests")))
        self.stack.enter_context(mock.patch.object(self.bridge.subprocess, "Popen", side_effect=AssertionError("Processes are forbidden in batch tests")))
        self.flush = self.stack.enter_context(mock.patch.object(self.bridge, "_flush_research_sheet_outbox", return_value={"processed": 0, "synced": 0}))
        self.real_drain = self.bridge._research_sheet_drain_deferred_reports
        self.drain = self.stack.enter_context(mock.patch.object(self.bridge, "_research_sheet_drain_deferred_reports", return_value={"queued": 0, "eligibleDeferred": 0}))
        self.real_queue = self.bridge._research_sheet_queue_report
        self.queue = self.stack.enter_context(mock.patch.object(self.bridge, "_research_sheet_queue_report", return_value={"queued": 1}))
        self.build_index = self.stack.enter_context(mock.patch.object(self.bridge, "_research_sheet_runtime_deep_version_index", side_effect=AssertionError("Compact projection must not scan complete history")))
        original_read = self.bridge.read_json

        def isolated_read(path, fallback):
            candidate = Path(path).resolve()
            self.assertTrue(candidate.is_relative_to(self.root.resolve()), f"Unexpected read outside synthetic fixture: {candidate}")
            return original_read(path, fallback)

        self.stack.enter_context(mock.patch.object(self.bridge, "read_json", side_effect=isolated_read))

    def write_report(self, ordinal: int, *, version: int = 1, kind: str = "trading_system_research_report") -> dict:
        report = {
            "id": f"report-{ordinal:03d}",
            "type": kind,
            "version": version,
            "createdAt": f"2026-10-01T00:{ordinal % 60:02d}:00Z",
            "updatedAt": f"2026-10-01T00:{ordinal % 60:02d}:{version:02d}Z",
        }
        path = self.reports / f"{report['id']}.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        # Deterministic ordering and an observable fingerprint when updated.
        timestamp = 1_790_000_000 + ordinal * 10 + version
        os.utime(path, (timestamp, timestamp))
        return report

    def step(self, **kwargs) -> dict:
        return self.bridge._research_sheet_backfill_background_step(self.state, **kwargs)

    def queued_ids(self) -> list[str]:
        return [call.args[0]["id"] for call in self.queue.call_args_list]

    def test_bounded_batches_resume_oldest_first_and_complete_without_restarting(self) -> None:
        for ordinal in range(5):
            self.write_report(ordinal)
        first = self.step(max_reports=2)
        self.assertEqual(self.queued_ids(), ["report-000", "report-001"])
        self.assertTrue(first["more"])
        second = self.step(max_reports=2)
        self.assertEqual(self.queued_ids(), [f"report-{i:03d}" for i in range(4)])
        self.assertTrue(second["more"])
        third = self.step(max_reports=2)
        self.assertEqual(self.queued_ids(), [f"report-{i:03d}" for i in range(5)])
        self.assertFalse(third["more"])
        self.assertLessEqual(first["processedReports"], 2)
        self.assertLessEqual(second["processedReports"], 2)
        self.assertEqual(third["processedReports"], 1)

    def test_projection_cap_ignores_unrelated_council_reports_without_queueing_them(self) -> None:
        for ordinal in range(12):
            self.write_report(ordinal, kind="ai_trade_council_vote" if ordinal % 3 else "trading_system_research_report")
        result = self.step(max_reports=2)
        self.assertEqual(self.queued_ids(), ["report-000", "report-003"])
        self.assertEqual(result["processedReports"], 2)
        self.assertTrue(result["more"])

    def test_monotonic_budget_yields_after_current_report_then_resumes_next(self) -> None:
        for ordinal in range(6):
            self.write_report(ordinal)

        def slow_projection(report, **kwargs):
            self.clock += 5.0
            return {"queued": 1}

        self.queue.side_effect = slow_projection
        first = self.step(max_reports=6, budget_seconds=8.0)
        self.assertEqual(self.queued_ids(), ["report-000", "report-001"])
        self.assertTrue(first["more"])
        self.step(max_reports=6, budget_seconds=8.0)
        self.assertEqual(self.queued_ids(), [f"report-{i:03d}" for i in range(4)])

    def test_one_slow_atomic_projection_does_not_start_a_second_after_budget(self) -> None:
        for ordinal in range(3):
            self.write_report(ordinal)

        def slow_projection(report, **kwargs):
            self.clock += 90.0
            return {"queued": 1}

        self.queue.side_effect = slow_projection
        result = self.step(max_reports=3, budget_seconds=8.0)
        self.assertEqual(self.queued_ids(), ["report-000"])
        self.assertTrue(result["more"])
        self.flush.assert_not_called()
        self.drain.assert_not_called()

    def test_stop_before_batch_does_not_queue_or_flush_anything(self) -> None:
        self.write_report(0)
        self.stop.set()
        self.step()
        self.queue.assert_not_called()
        self.flush.assert_not_called()
        self.drain.assert_not_called()

    def test_stop_between_reports_preserves_the_unprocessed_tail(self) -> None:
        for ordinal in range(3):
            self.write_report(ordinal)

        def request_stop(report, **kwargs):
            self.stop.set()
            return {"queued": 1}

        self.queue.side_effect = request_stop
        first = self.step(max_reports=3)
        self.assertEqual(self.queued_ids(), ["report-000"])
        self.assertTrue(first["more"])
        self.stop.clear()
        self.queue.side_effect = None
        self.step(max_reports=3)
        self.assertEqual(self.queued_ids(), [f"report-{i:03d}" for i in range(3)])

    def test_unprocessed_file_is_reread_after_edit(self) -> None:
        for ordinal in range(3):
            self.write_report(ordinal)
        self.step(max_reports=1)
        self.write_report(1, version=2)
        self.step(max_reports=1)
        self.assertEqual(self.queue.call_args.args[0]["id"], "report-001")
        self.assertEqual(self.queue.call_args.args[0]["version"], 2)

    def test_edited_report_behind_cursor_is_eventually_revisited_without_starvation(self) -> None:
        for ordinal in range(5):
            self.write_report(ordinal)
        self.step(max_reports=2)
        self.write_report(0, version=2)
        for _ in range(5):
            self.step(max_reports=2)
        seen = [(call.args[0]["id"], call.args[0]["version"]) for call in self.queue.call_args_list]
        self.assertIn(("report-000", 2), seen)
        for ordinal in range(1, 5):
            self.assertIn((f"report-{ordinal:03d}", 1), seen)
        self.assertEqual(seen.count(("report-000", 1)), 1)

    def test_new_report_arriving_mid_sweep_is_eventually_processed(self) -> None:
        for ordinal in range(4):
            self.write_report(ordinal)
        self.step(max_reports=2)
        self.write_report(4)
        for _ in range(4):
            self.step(max_reports=2)
        self.assertIn("report-004", self.queued_ids())
        self.assertEqual(set(self.queued_ids()), {f"report-{i:03d}" for i in range(5)})

    def test_config_revision_change_restarts_projection_for_new_binding(self) -> None:
        for ordinal in range(4):
            self.write_report(ordinal)
        revisions = []

        def queue_with_revision(report, **kwargs):
            revisions.append((report["id"], self.internal["configRevision"]))
            return {"queued": 1}

        self.queue.side_effect = queue_with_revision
        self.step(max_reports=2)
        self.internal.update(configRevision=4, activeConfigRevision=4)
        result = self.step(max_reports=2)
        self.assertEqual(revisions, [("report-000", 3), ("report-001", 3), ("report-000", 4), ("report-001", 4)])
        self.assertEqual(result["configRevision"], 4)

    def test_inactive_binding_does_not_consume_reports(self) -> None:
        self.write_report(0)
        self.internal.update(active=False, activeConfigRevision=None)
        self.step()
        self.queue.assert_not_called()
        self.internal.update(active=True, activeConfigRevision=3)
        self.step()
        self.assertEqual(self.queued_ids(), ["report-000"])

    def test_deleted_file_does_not_prevent_later_reports(self) -> None:
        for ordinal in range(4):
            self.write_report(ordinal)
        self.step(max_reports=1)
        (self.reports / "report-001.json").unlink()
        for _ in range(3):
            self.step(max_reports=2)
        self.assertNotIn("report-001", self.queued_ids())
        self.assertIn("report-003", self.queued_ids())

    def test_transient_queue_failure_retains_report_for_retry_without_losing_tail(self) -> None:
        self.write_report(0)
        self.write_report(1)
        self.queue.side_effect = OSError("synthetic outbox sharing conflict")
        with self.assertRaises(OSError):
            self.step(max_reports=2)
        self.queue.side_effect = None
        self.step(max_reports=2)
        self.assertEqual(self.queued_ids(), ["report-000", "report-000", "report-001"])

    def test_malformed_report_does_not_permanently_starve_valid_report_after_it(self) -> None:
        self.write_report(0)
        self.write_report(1)
        (self.reports / "report-000.json").write_text("{broken-json", encoding="utf-8")
        os.utime(self.reports / "report-000.json", (1_790_000_001, 1_790_000_001))
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.step(max_reports=2)
        self.step(max_reports=2)
        self.assertEqual(self.queued_ids(), ["report-001"])

    def test_projection_integrity_error_is_quarantined_without_starving_valid_report(self) -> None:
        self.write_report(0)
        self.write_report(1)

        def project(report, **kwargs):
            if report["id"] == "report-000":
                raise self.bridge.DataIntegrityError("synthetic malformed report")
            return {"queued": 1}

        self.queue.side_effect = project
        result = self.step(max_reports=2)
        self.assertEqual(self.queued_ids(), ["report-000", "report-001"])
        self.assertEqual(result["quarantinedReports"], 1)
        store = json.loads((self.runtime / "outbox.json").read_text(encoding="utf-8-sig"))
        quarantined = store["quarantinedReports"]
        self.assertEqual([r["reportId"] for r in quarantined], ["report-000"])
        self.assertEqual(quarantined[0]["configRevision"], 3)

    def test_background_projection_never_flushes_or_drains_and_keeps_queue_contract(self) -> None:
        self.write_report(0)
        self.step()
        self.queue.assert_called_once()
        self.assertFalse(self.queue.call_args.kwargs["flush"])
        self.assertIsNone(self.queue.call_args.kwargs.get("deep_version_index"))
        self.flush.assert_not_called()
        self.drain.assert_not_called()
        self.build_index.assert_not_called()

    def test_manual_full_backfill_keeps_all_reports_and_existing_flush_limits(self) -> None:
        for ordinal in range(7):
            self.write_report(ordinal)
        result = self.bridge._research_sheet_backfill_recent_reports()
        self.assertEqual(self.queued_ids(), [f"report-{i:03d}" for i in range(7)])
        self.assertEqual(result["recentQueued"], 7)
        self.flush.assert_called_once_with(max_items=50)
        self.drain.assert_called_once_with(
            max_reports=self.bridge.RESEARCH_SHEET_DEFERRED_REPORT_DRAIN_BATCH_LIMIT,
            allowed_consumer_ids=None,
        )

    def install_synthetic_row_projection(self) -> None:
        def rows(report, revision, **kwargs):
            return [{
                "id": f"sheet-sync-{report['id']}", "status": "pending",
                "consumerId": "deepResearch", "producerPropId": "left_server_racks",
                "tabName": "Deep_Research", "keyHeader": "record_id",
                "recordKey": report["id"], "row": {"record_id": report["id"], "system_name": f"Version {report['version']}"},
                "payloadDigest": f"synthetic-{report['id']}-v{report['version']}",
                "configRevision": revision, "reportId": report["id"],
                "missionId": "mission-fixture", "attemptCount": 0,
                "createdAt": "2026-10-01T00:00:00Z", "updatedAt": "2026-10-01T00:00:00Z",
            }]

        self.stack.enter_context(mock.patch.object(self.bridge, "_research_sheet_report_items", side_effect=rows))
        self.queue.side_effect = self.real_queue

    def test_restart_rebuilds_scan_without_duplicating_outbox_or_resetting_retry(self) -> None:
        self.write_report(0)
        self.install_synthetic_row_projection()
        self.assertEqual(self.step()["queued"], 1)
        stored = self.bridge._load_research_sheet_outbox_unlocked()
        stored["items"][0].update(status="retry_pending", attemptCount=2, nextAttemptAt="2099-01-01T00:00:00Z")
        self.bridge._save_research_sheet_outbox_unlocked(stored)
        self.state.clear()  # A newly started scheduler has no in-memory cursor.
        self.assertEqual(self.step()["queued"], 0)
        after = self.bridge._load_research_sheet_outbox_unlocked()
        self.assertEqual(len(after["items"]), 1)
        self.assertEqual(after["items"][0]["status"], "retry_pending")
        self.assertEqual(after["items"][0]["attemptCount"], 2)
        self.assertEqual(after["items"][0]["nextAttemptAt"], "2099-01-01T00:00:00Z")
        self.flush.assert_not_called()

    def test_restarted_scan_does_not_requeue_a_durable_synced_receipt(self) -> None:
        self.write_report(0)
        self.install_synthetic_row_projection()
        self.step()
        stored = self.bridge._load_research_sheet_outbox_unlocked()
        item = stored["items"][0]
        stored["items"] = []
        stored["syncedLedger"] = [{
            "id": item["id"], "payloadDigest": item["payloadDigest"],
            "configRevision": 3, "syncedAt": "2026-10-01T00:01:00Z",
        }]
        self.bridge._save_research_sheet_outbox_unlocked(stored)
        self.state.clear()
        self.assertEqual(self.step()["queued"], 0)
        after = self.bridge._load_research_sheet_outbox_unlocked()
        self.assertEqual(after["items"], [])
        self.assertEqual(len(after["syncedLedger"]), 1)

    def test_changed_payload_replaces_one_outbox_row_instead_of_adding_duplicate(self) -> None:
        self.write_report(0)
        self.install_synthetic_row_projection()
        self.step()
        self.write_report(0, version=2)
        self.assertEqual(self.step()["queued"], 1)
        after = self.bridge._load_research_sheet_outbox_unlocked()
        self.assertEqual(len(after["items"]), 1)
        self.assertEqual(after["items"][0]["row"]["system_name"], "Version 2")
        self.assertEqual(after["items"][0]["payloadDigest"], "synthetic-report-000-v2")

    def seed_deferred(self, count: int) -> None:
        store = self.bridge._research_sheet_outbox_default()
        store["deferredReports"] = []
        for ordinal in range(count):
            report = self.write_report(ordinal)
            store["deferredReports"].append({
                "reportId": report["id"], "reportType": report["type"],
                "consumerId": "deepResearch", "configRevision": 3,
                "deferredAt": f"2026-10-01T00:{ordinal:02d}:00Z",
                "recoveryAttemptCount": 0,
            })
        (self.runtime / "outbox.json").write_text(json.dumps(store), encoding="utf-8")

    def test_deferred_scan_limit_and_failure_rotation_prevent_large_missing_file_scan(self) -> None:
        self.seed_deferred(3)
        (self.reports / "report-000.json").unlink()
        first = self.real_drain(max_reports=1, max_scanned=1, deadline_monotonic=self.clock + 8)
        self.assertEqual(first["scanned"], 1)
        self.assertEqual(first["recoveryDeferred"], 1)
        self.queue.assert_not_called()
        second = self.real_drain(max_reports=1, max_scanned=1, deadline_monotonic=self.clock + 8)
        self.assertEqual(second["scanned"], 1)
        self.assertEqual(second["drained"], 1)
        self.assertEqual(self.queued_ids(), ["report-001"])
        self.build_index.assert_not_called()

    def test_deferred_budget_does_not_start_next_projection_after_expiry(self) -> None:
        self.seed_deferred(3)

        def slow_projection(report, **kwargs):
            self.clock += 20.0
            return {"queued": 1}

        self.queue.side_effect = slow_projection
        result = self.real_drain(max_reports=3, max_scanned=3, deadline_monotonic=self.clock + 8)
        self.assertEqual(result["drained"], 1)
        self.assertEqual(self.queued_ids(), ["report-000"])
        self.flush.assert_not_called()
        self.build_index.assert_not_called()

    def test_deferred_background_stop_does_not_consume_marker(self) -> None:
        self.seed_deferred(1)
        self.stop.set()
        result = self.real_drain(max_reports=1, max_scanned=1, deadline_monotonic=self.clock + 8)
        self.assertEqual(result["scanned"], 0)
        self.queue.assert_not_called()
        stored = json.loads((self.runtime / "outbox.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(len(stored["deferredReports"]), 1)

    def test_manual_deferred_drain_retains_default_scan_and_no_unused_history_build(self) -> None:
        self.seed_deferred(3)
        result = self.real_drain(max_reports=3)
        self.assertEqual(result["drained"], 3)
        self.assertEqual(self.queued_ids(), [f"report-{i:03d}" for i in range(3)])
        self.build_index.assert_not_called()

    def seed_pending_row(self) -> None:
        self.write_report(0)
        self.install_synthetic_row_projection()
        self.step()
        self.stack.enter_context(mock.patch.object(self.bridge.google_sheet_hub, "credential_status", return_value={"configured": True}))
        self.stack.enter_context(mock.patch.object(self.bridge, "_research_sheet_mark_write_verified"))
        self.stack.enter_context(mock.patch.object(self.bridge, "_research_sheet_tab_contracts", return_value={"deepResearch": {"tabName": "Deep_Research", "keyHeader": "record_id"}}))

    def pending_row(self) -> dict:
        return self.bridge._load_research_sheet_outbox_unlocked()["items"][0]

    def test_network_budget_caps_every_request_and_rejects_exhausted_oauth_without_write_unknown(self) -> None:
        hub = self.bridge.google_sheet_hub
        opener = self.bridge._research_sheet_background_opener(self.clock + 8)
        with mock.patch.object(self.bridge, "urlopen") as opened:
            opener(Request(hub.GOOGLE_TOKEN_URL, data=b"fixture", method="POST"), timeout=20)
            self.assertEqual(opened.call_args.kwargs["timeout"], 8)
            self.clock += 6
            opener(Request(hub.GOOGLE_API_ROOT + "/fixture"), timeout=20)
            self.assertEqual(opened.call_args.kwargs["timeout"], 2)
            self.clock += 2
            with self.assertRaises(hub.GoogleSheetHubError) as caught:
                opener(Request(hub.GOOGLE_API_ROOT + "/fixture"))
            self.assertEqual(caught.exception.code, "background_budget_exhausted")
            self.assertFalse(caught.exception.write_unknown)
            self.assertEqual(opened.call_count, 2)

    def test_network_budget_after_sheets_write_preserves_ambiguous_write(self) -> None:
        hub = self.bridge.google_sheet_hub
        opener = self.bridge._research_sheet_background_opener(self.clock + 8)
        with mock.patch.object(self.bridge, "urlopen") as opened:
            opener(Request(hub.GOOGLE_API_ROOT + "/fixture/values:batchUpdate", data=b"{}", method="POST"))
            self.clock += 8
            with self.assertRaises(hub.GoogleSheetHubError) as caught:
                opener(Request(hub.GOOGLE_API_ROOT + "/fixture"))
            self.assertTrue(caught.exception.write_unknown)
            self.assertEqual(caught.exception.code, "background_budget_exhausted")
            self.assertEqual(opened.call_count, 1)

    def test_network_stop_prevents_new_request_without_contacting_provider(self) -> None:
        self.stop.set()
        with mock.patch.object(self.bridge, "urlopen") as opened:
            with self.assertRaises(self.bridge.google_sheet_hub.GoogleSheetHubError) as caught:
                self.bridge._research_sheet_background_opener(self.clock + 8)(Request("https://sheets.googleapis.com/v4/spreadsheets/fixture"))
            self.assertEqual(caught.exception.code, "background_budget_exhausted")
            opened.assert_not_called()

    def test_empty_background_outbox_does_not_inspect_authorization(self) -> None:
        with mock.patch.object(self.bridge.google_sheet_hub, "credential_status", side_effect=AssertionError("Idle queue must not read credentials")):
            result = self.bridge._flush_research_sheet_outbox_locked(max_items=1, background=True)
        self.assertEqual(result["processed"], 0)

    def test_background_flush_skips_full_cache_and_manual_flush_retains_refresh(self) -> None:
        self.seed_pending_row()
        receipt = {"rowNumber": 2, "updatedRows": 1, "readBackVerified": True}
        with (
            mock.patch.object(self.bridge.google_sheet_hub, "upsert_row", return_value=receipt) as upsert,
            mock.patch.object(self.bridge, "_refresh_research_sheet_cache") as refresh,
        ):
            result = self.bridge._flush_research_sheet_outbox_locked(max_items=1, background=True)
            self.assertEqual(result["synced"], 1)
            self.assertEqual(result["syncedConsumerIds"], ["deepResearch"])
            self.assertTrue(callable(upsert.call_args.kwargs["open_url"]))
            refresh.assert_not_called()
            self.write_report(0, version=2)
            self.step()
            result = self.bridge._flush_research_sheet_outbox_locked(max_items=1)
            self.assertEqual(result["synced"], 1)
            self.assertNotIn("open_url", upsert.call_args.kwargs)
            refresh.assert_called_once_with(self.internal["sheetId"], 3)

    def test_budget_expiry_during_oauth_response_read_remains_retryable(self) -> None:
        self.seed_pending_row()
        hub = self.bridge.google_sheet_hub
        real_upsert = hub.upsert_row
        response = mock.MagicMock()
        response.__enter__.return_value = response

        def expire_read(*args):
            self.clock += self.bridge.RESEARCH_SHEET_BACKGROUND_IO_BUDGET_SECONDS + 1
            raise TimeoutError("synthetic OAuth response timeout")

        response.read.side_effect = expire_read
        synthetic_env = {"METAFX_GOOGLE_OAUTH_CLIENT_ID": "fixture-client", "METAFX_GOOGLE_OAUTH_REFRESH_TOKEN": "fixture-refresh-not-a-secret"}
        with (
            mock.patch.object(self.bridge, "urlopen", return_value=response) as opened,
            mock.patch.object(hub, "upsert_row", side_effect=lambda *args, **kwargs: real_upsert(*args, **kwargs, environ=synthetic_env)),
        ):
            result = self.bridge._flush_research_sheet_outbox_locked(max_items=1, background=True)
        self.assertEqual(result["synced"], 0)
        self.assertEqual(opened.call_count, 1)
        self.assertEqual(opened.call_args.args[0].full_url, hub.GOOGLE_TOKEN_URL)
        self.assertEqual(self.pending_row()["status"], "retry_pending")
        self.assertEqual(self.pending_row()["lastErrorCode"], "background_budget_exhausted")

    def test_budget_expiry_during_write_response_or_readback_keeps_write_unknown(self) -> None:
        for timeout_request in (3, 4):
            with self.subTest(timeout_request=timeout_request):
                self.clock = 100.0
                self.write_report(0, version=timeout_request)
                if timeout_request == 3:
                    self.install_synthetic_row_projection()
                    self.stack.enter_context(mock.patch.object(self.bridge.google_sheet_hub, "credential_status", return_value={"configured": True}))
                    self.stack.enter_context(mock.patch.object(self.bridge, "_research_sheet_tab_contracts", return_value={"deepResearch": {}}))
                self.step()
                hub = self.bridge.google_sheet_hub
                real_upsert = hub.upsert_row
                calls = []

                def open_fixture(request, *, timeout):
                    calls.append(request.get_method())
                    response = mock.MagicMock()
                    response.__enter__.return_value = response
                    if len(calls) == timeout_request:
                        def expire_read(*args):
                            self.clock += self.bridge.RESEARCH_SHEET_BACKGROUND_IO_BUDGET_SECONDS + 1
                            raise TimeoutError("synthetic post-write response timeout")
                        response.read.side_effect = expire_read
                    else:
                        payload = ({"values": [["record_id", "system_name"]]} if len(calls) == 1
                                   else {"values": []} if len(calls) == 2
                                   else {"responses": [{"updatedRows": 1}]})
                        response.read.return_value = json.dumps(payload).encode()
                    return response

                with (
                    mock.patch.object(self.bridge, "urlopen", side_effect=open_fixture),
                    mock.patch.object(hub, "upsert_row", side_effect=lambda *args, **kwargs: real_upsert(*args, **kwargs, environ={"METAFX_GOOGLE_SHEETS_ACCESS_TOKEN": "fixture-direct-token-not-a-secret"})),
                ):
                    self.bridge._flush_research_sheet_outbox_locked(max_items=1, background=True)
                self.assertEqual(calls, ["GET", "GET", "POST"] + (["GET"] if timeout_request == 4 else []))
                self.assertEqual(self.pending_row()["status"], "write_unknown")
                self.assertEqual(self.pending_row()["lastErrorCode"], "write_unknown")
                self.assertIsNotNone(self.pending_row()["nextAttemptAt"])

    def seed_cache(self) -> dict:
        old = {
            "schemaVersion": "research-sheet-cache-v1",
            "sheetDigest": self.bridge.payload_digest("research-sheet-id-v1", self.internal["sheetId"]),
            "configRevision": 3,
            "updatedAt": "2026-10-01T00:00:00Z",
            "consumers": {
                "deepResearch": {"observedAt": "2026-10-01T00:00:00Z", "rows": [{"record_id": "old"}]},
                "worldSystem": {"observedAt": "2026-10-01T00:00:00Z", "rows": [{"record_id": "must-stay-stale"}]},
            },
        }
        (self.runtime / "cache.json").write_text(json.dumps(old), encoding="utf-8")
        self.stack.enter_context(mock.patch.object(self.bridge, "utc_now", return_value="2026-10-02T00:00:00Z"))
        self.stack.enter_context(mock.patch.object(self.bridge, "_research_sheet_tab_contracts", return_value={
            "deepResearch": {"tabName": "Deep_Research", "keyHeader": "record_id"},
            "worldSystem": {"tabName": "World_System", "keyHeader": "record_id"},
        }))
        return old

    def test_partial_cache_merge_preserves_other_consumers_age_and_global_ttl(self) -> None:
        previous = self.seed_cache()
        opener = object()
        with mock.patch.object(self.bridge.google_sheet_hub, "read_values", side_effect=[[["record_id"]], [["fresh"]], [["fresh"]]]) as read:
            result = self.bridge._refresh_research_sheet_cache(self.internal["sheetId"], 3,
                allowed_consumer_ids={"deepResearch"}, merge_existing=True, open_url=opener)
        self.assertEqual(result["consumers"]["worldSystem"], previous["consumers"]["worldSystem"])
        self.assertEqual(result["consumers"]["deepResearch"]["observedAt"], "2026-10-02T00:00:00Z")
        self.assertEqual(result["updatedAt"], previous["updatedAt"])
        self.assertEqual([c.args[1] for c in read.call_args_list], ["Deep_Research"] * 3)
        self.assertTrue(all(c.kwargs["open_url"] is opener for c in read.call_args_list))

    def test_partial_cache_cannot_publish_after_configuration_changes(self) -> None:
        previous = self.seed_cache()

        def reconfigured_read(*args, **kwargs):
            self.internal.update(configRevision=4, activeConfigRevision=4)
            return [["record_id"]] if args[2] == "1:1" else []

        with mock.patch.object(self.bridge.google_sheet_hub, "read_values", side_effect=reconfigured_read):
            self.bridge._refresh_research_sheet_cache(self.internal["sheetId"], 3,
                allowed_consumer_ids={"deepResearch"}, merge_existing=True)
        self.assertEqual(json.loads((self.runtime / "cache.json").read_text(encoding="utf-8-sig")), previous)

    def test_manual_cache_refresh_still_refreshes_all_consumers(self) -> None:
        self.seed_cache()
        with mock.patch.object(self.bridge.google_sheet_hub, "read_values", side_effect=lambda *args, **kwargs: [["record_id"]] if args[2] == "1:1" else []) as read:
            result = self.bridge._refresh_research_sheet_cache(self.internal["sheetId"], 3)
        self.assertEqual({c.args[1] for c in read.call_args_list}, {"Deep_Research", "World_System"})
        self.assertEqual(result["updatedAt"], "2026-10-02T00:00:00Z")
        self.assertTrue(all(not c.kwargs for c in read.call_args_list))

    def test_partial_cache_merge_preserves_newer_concurrent_refresh(self) -> None:
        previous = self.seed_cache()
        concurrent = copy.deepcopy(previous)
        concurrent["consumers"]["deepResearch"] = {"observedAt": "2026-10-03T00:00:00Z", "rows": [{"record_id": "newer-concurrent"}]}

        def read_and_publish_newer(*args, **kwargs):
            (self.runtime / "cache.json").write_text(json.dumps(concurrent), encoding="utf-8")
            return [["record_id"]] if args[2] == "1:1" else []

        with mock.patch.object(self.bridge.google_sheet_hub, "read_values", side_effect=read_and_publish_newer):
            result = self.bridge._refresh_research_sheet_cache(self.internal["sheetId"], 3,
                allowed_consumer_ids={"deepResearch"}, merge_existing=True)
        self.assertEqual(result["consumers"], concurrent["consumers"])
        self.assertEqual(result["updatedAt"], previous["updatedAt"])

    def test_background_cache_rotates_after_failed_consumer_and_rebuilds_from_delivery_receipts(self) -> None:
        self.seed_cache()
        self.internal["consumerChecks"] = {name: {"readReady": True, "configRevision": 3} for name in ("deepResearch", "worldSystem")}
        store = self.bridge._research_sheet_outbox_default()
        store["syncedLedger"] = [{"id": "receipt-fixture", "payloadDigest": "synthetic-delivery-digest", "configRevision": 3, "syncedAt": "2026-10-02T00:00:00Z"}]
        self.bridge._save_research_sheet_outbox_unlocked(store)
        cursor = {}
        with mock.patch.object(self.bridge, "_refresh_research_sheet_cache", side_effect=[RuntimeError("fixture consumer unavailable"), {}]) as refresh:
            with self.assertRaisesRegex(RuntimeError, "fixture consumer unavailable"):
                self.bridge._research_sheet_background_cache_step(cursor)
            result = self.bridge._research_sheet_background_cache_step(cursor)
            self.assertEqual(result["consumerId"], "worldSystem")
            self.assertEqual([c.kwargs["allowed_consumer_ids"] for c in refresh.call_args_list], [{"deepResearch"}, {"worldSystem"}])
            self.assertTrue(all(c.kwargs["merge_existing"] is True for c in refresh.call_args_list))
            self.assertTrue(all(callable(c.kwargs["open_url"]) for c in refresh.call_args_list))
        # Restart loses only the disposable cursor, not pending refresh work.
        with mock.patch.object(self.bridge, "_refresh_research_sheet_cache") as refresh:
            result = self.bridge._research_sheet_background_cache_step({})
        self.assertEqual(result["consumerId"], "deepResearch")
        refresh.assert_called_once()

    def test_slow_report_read_rechecks_deadline_before_projection_and_retains_cursor(self) -> None:
        self.write_report(0)
        isolated_read = self.bridge.read_json.side_effect

        def slow_read(path, fallback):
            value = isolated_read(path, fallback)
            if Path(path).parent == self.reports:
                self.clock += 9
            return value

        with mock.patch.object(self.bridge, "read_json", side_effect=slow_read):
            result = self.step(budget_seconds=8)
        self.assertEqual(result["reason"], "budget_exhausted")
        self.assertEqual(result["processedReports"], 0)
        self.assertTrue(result["more"])
        self.queue.assert_not_called()
        self.assertEqual(self.step()["processedReports"], 1)
        self.assertEqual(self.queued_ids(), ["report-000"])


if __name__ == "__main__":
    unittest.main()
