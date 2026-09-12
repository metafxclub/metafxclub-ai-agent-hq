from __future__ import annotations

import copy
import importlib.util
import inspect
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_ea_factory_backend_admission_and_cache",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EaFactoryBackendAdmissionAndCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        self.bridge.EA_FACTORY_ONE_CLICK_THREADS.clear()
        self.bridge.EA_FACTORY_WORLD_SHEET_CACHE.update({
            "signature": None,
            "value": None,
        })
        self.bridge._invalidate_ea_factory_read_model_cache()

    def tearDown(self) -> None:
        self.bridge.EA_FACTORY_ONE_CLICK_THREADS.clear()

    def state(self, *builds: dict) -> dict:
        return {
            "schemaVersion": self.bridge.EA_FACTORY_STATE_SCHEMA_VERSION,
            "sourceSnapshots": [],
            "builds": list(builds),
            "createReservations": [],
            "updatedAt": None,
        }

    @staticmethod
    def stage(stage_id: str, mission_id: str | None, status: str) -> dict:
        return {
            "id": stage_id,
            "status": status,
            "missionId": mission_id,
            "reportId": None,
            "blockedReasonCode": None,
            "evidenceVerified": False,
            "requestIdempotencyKey": None,
            "requestDigest": None,
            "startedAt": None,
            "missionIdempotencyKey": None,
            "manualRetryCount": 0,
            "manualRetryHistory": [],
            "artifacts": [],
            "updatedAt": "2026-09-12T00:00:00Z",
        }

    def build(self, build_id: str, stages: list[dict]) -> dict:
        return {
            "schemaVersion": "ea-factory-build-v1",
            "id": build_id,
            "sourceRecordId": f"source-{build_id}",
            "sourceDisplayName": f"Build {build_id}",
            "sourceRecordDigest": "a" * 64,
            "createRequestDigest": "b" * 64,
            "coverageStatus": "compact_current",
            "coverageUpgradeRequired": False,
            "platform": "mt4",
            "artifactKind": "expert_advisor",
            "brief": "",
            "status": "ready",
            "workspace": {"folderNames": []},
            "stages": stages,
            "versions": [],
            "createdAt": "2026-09-12T00:00:00Z",
            "updatedAt": "2026-09-12T00:00:00Z",
        }

    def volatile_patches(self):
        return (
            mock.patch.object(self.bridge, "peek_metatrader_status", return_value={}),
            mock.patch.object(
                self.bridge,
                "_metatrader_selection_read_model",
                return_value={"candidates": [], "selectedCandidate": None},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_terminal_gate",
                side_effect=lambda platform: {"platform": platform, "ready": False},
            ),
            mock.patch.object(self.bridge, "research_sheet_hub_read_model", return_value={}),
            mock.patch.object(
                self.bridge,
                "_ea_factory_front_office_supported_platforms",
                return_value=set(),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_read_model_signature",
                return_value=("stable-signature",),
            ),
        )

    def test_active_guard_uses_mission_truth_and_ignores_stale_stage_copy(self) -> None:
        build = self.build(
            "ea-build-stale-stage",
            [self.stage("generate_source", "mission-stage", "running")],
        )
        state = self.state(build)
        for terminal_status in (
            "completed",
            "failed",
            "blocked",
            "pending",
            "waiting_approval",
            "awaiting_visible_terminal",
        ):
            with self.subTest(status=terminal_status):
                self.assertIsNone(
                    self.bridge._ea_factory_active_worker_payload(
                        state,
                        [{"id": "mission-stage", "status": terminal_status}],
                    )
                )

        busy = self.bridge._ea_factory_active_worker_payload(
            state,
            [{"id": "mission-stage", "status": "queued"}],
        )
        self.assertEqual(busy["buildId"], build["id"])
        self.assertEqual(busy["stageId"], "generate_source")
        self.assertEqual(busy["missionStatus"], "queued")
        self.assertEqual(busy["activeOperation"], "generate_source")

    def test_active_guard_binds_mission_by_reserved_key_during_dispatch_crash_window(self) -> None:
        stage = self.stage("generate_source", None, "pending")
        stage["missionIdempotencyKey"] = "ea-factory:stage:crash-window"
        build = self.build("ea-build-crash-window", [stage])
        mission = {
            "id": "mission-crash-window",
            "status": "queued",
            "idempotencyKey": stage["missionIdempotencyKey"],
            "targetId": "right_server_racks",
            "requester": "human",
            "owner": "ea_developer",
            "toolId": "codex_cli_task",
            "reportType": "ea_build_report",
        }
        with mock.patch.object(
            self.bridge,
            "_trusted_backend_ea_factory_worker_sandbox",
            return_value={"buildId": build["id"], "stageId": "generate_source"},
        ):
            busy = self.bridge._ea_factory_active_worker_payload(
                self.state(build),
                [mission],
            )
            self.assertEqual(busy["missionId"], mission["id"])
            self.assertEqual(busy["buildId"], build["id"])
            self.assertEqual(busy["stageId"], "generate_source")

            unrelated = {**mission, "targetId": "terminal_workstation"}
            self.assertIsNone(
                self.bridge._ea_factory_active_worker_payload(
                    self.state(build),
                    [unrelated],
                )
            )

    def test_request_error_response_keeps_structured_busy_contract(self) -> None:
        with self.assertRaises(self.bridge.RequestError) as raised:
            self.bridge._raise_ea_factory_busy({
                "buildId": "ea-build-busy",
                "displayName": "Busy build",
                "stageId": "generate_source",
                "status": "running",
                "missionId": "mission-busy",
                "missionStatus": "running",
                "activeOperation": "generate_source",
            })
        error = raised.exception
        response = self.bridge.request_error_response(error)
        self.assertEqual(error.status, 409)
        self.assertEqual(response["kind"], "ea_factory_busy")
        self.assertEqual(response["code"], "ea_factory_single_active_build")
        self.assertEqual(response["busy"]["buildId"], "ea-build-busy")
        self.assertIn("กำลังทำงาน", response["messageTh"])
        self.assertIn(
            "request_error_response(error)",
            inspect.getsource(self.bridge.BridgeHandler.do_POST),
        )

    def test_world_sheet_projection_cache_is_signature_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            cache_path = Path(temporary) / "research-sheet-cache.json"
            cache_path.write_text("{}", encoding="utf-8")
            value = ([{"sourceRecordId": "record-1"}], {"acceptedRowCount": 1})
            with (
                mock.patch.object(self.bridge, "RESEARCH_SHEET_CACHE_PATH", cache_path),
                mock.patch.object(
                    self.bridge,
                    "_world_sheet_catalog_projection_uncached",
                    return_value=value,
                ) as project,
            ):
                first = self.bridge._world_sheet_catalog_projection()
                second = self.bridge._world_sheet_catalog_projection()
                self.assertEqual(first, second)
                self.assertEqual(project.call_count, 1)
                first[0][0]["sourceRecordId"] = "mutated"
                self.assertEqual(
                    self.bridge._world_sheet_catalog_projection()[0][0]["sourceRecordId"],
                    "record-1",
                )
                cache_path.write_text('{"revision":2}', encoding="utf-8")
                self.bridge._world_sheet_catalog_projection()
                self.assertEqual(project.call_count, 2)

    def test_read_model_cache_coalesces_concurrent_cold_reads(self) -> None:
        entered = threading.Event()
        release = threading.Event()
        calls = []
        results = []
        errors = []

        def build_model(**_kwargs):
            calls.append(threading.get_ident())
            entered.set()
            if not release.wait(2):
                raise AssertionError("test did not release cache builder")
            return {"schemaVersion": "ea-factory-v1", "builds": []}

        patches = self.volatile_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], mock.patch.object(
            self.bridge,
            "_ea_factory_read_model_uncached",
            side_effect=build_model,
        ):
            def reader():
                try:
                    results.append(self.bridge.ea_factory_read_model())
                except Exception as error:  # pragma: no cover - asserted below
                    errors.append(error)

            first = threading.Thread(target=reader)
            second = threading.Thread(target=reader)
            first.start()
            self.assertTrue(entered.wait(1))
            second.start()
            time.sleep(0.05)
            release.set()
            first.join(2)
            second.join(2)

        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        self.assertEqual(len(calls), 1)
        results[0]["builds"].append({"id": "mutated"})
        self.assertEqual(results[1]["builds"], [])

    def test_read_model_rebuilds_after_inflight_invalidation(self) -> None:
        calls = []

        def build_model(**_kwargs):
            revision = len(calls) + 1
            calls.append(revision)
            if revision == 1:
                self.bridge._invalidate_ea_factory_read_model_cache()
            return {"schemaVersion": "ea-factory-v1", "revision": revision}

        patches = self.volatile_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], mock.patch.object(
            self.bridge,
            "_ea_factory_read_model_uncached",
            side_effect=build_model,
        ):
            result = self.bridge.ea_factory_read_model()

        self.assertEqual(calls, [1, 2])
        self.assertEqual(result["revision"], 2)
        self.assertEqual(self.bridge.EA_FACTORY_READ_MODEL_CACHE["value"]["revision"], 2)

    def test_thread_registry_invalidates_cached_busy_on_register_and_removal(self) -> None:
        build_id = "ea-build-thread-cache"
        fake_worker = mock.Mock()
        with self.bridge.EA_FACTORY_READ_MODEL_CACHE_CONDITION:
            self.bridge.EA_FACTORY_READ_MODEL_CACHE.update({
                "signature": ("cached-idle",),
                "value": {"busy": None},
            })
        with mock.patch.object(self.bridge.threading, "Thread", return_value=fake_worker):
            self.assertTrue(self.bridge._start_ea_factory_one_click_thread(build_id))
        fake_worker.start.assert_called_once_with()
        self.assertIsNone(self.bridge.EA_FACTORY_READ_MODEL_CACHE["value"])

        self.bridge.EA_FACTORY_ONE_CLICK_THREADS.clear()
        self.bridge.EA_FACTORY_ONE_CLICK_THREADS[build_id] = threading.current_thread()
        with self.bridge.EA_FACTORY_READ_MODEL_CACHE_CONDITION:
            self.bridge.EA_FACTORY_READ_MODEL_CACHE.update({
                "signature": ("cached-busy",),
                "value": {"busy": {"buildId": build_id}},
            })
        with mock.patch.object(
            self.bridge,
            "_ea_factory_one_click_next_action",
            return_value={"kind": "stop"},
        ):
            self.bridge._ea_factory_one_click_worker(build_id)
        self.assertNotIn(build_id, self.bridge.EA_FACTORY_ONE_CLICK_THREADS)
        self.assertIsNone(self.bridge.EA_FACTORY_READ_MODEL_CACHE["value"])

    def test_cache_refresh_does_not_deadlock_nested_replay_holding_factory_lock(self) -> None:
        refresh_entered = threading.Event()
        outer_result = []
        errors = []

        def lock_bound_model(**_kwargs):
            refresh_entered.set()
            with self.bridge.EA_FACTORY_LOCK:
                return {"schemaVersion": "ea-factory-v1", "builds": []}

        patches = self.volatile_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], mock.patch.object(
            self.bridge,
            "_ea_factory_read_model_uncached",
            side_effect=lock_bound_model,
        ):
            with self.bridge.EA_FACTORY_LOCK:
                def reader():
                    try:
                        outer_result.append(self.bridge.ea_factory_read_model())
                    except Exception as error:  # pragma: no cover - asserted below
                        errors.append(error)

                thread = threading.Thread(target=reader)
                thread.start()
                self.assertTrue(refresh_entered.wait(1))
                nested = self.bridge.ea_factory_read_model()
                self.assertEqual(nested["schemaVersion"], "ea-factory-v1")
            thread.join(2)

        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(len(outer_result), 1)

    def test_generic_right_rack_report_does_not_build_factory_projection(self) -> None:
        role = {
            "displayTitle": "Factory",
            "purpose": "Factory workflow",
            "allowedDashboardActions": [],
            "localTabs": [],
            "workflow": {},
            "workflowDashboard": {},
        }
        with (
            mock.patch.object(self.bridge, "find_property_role", return_value=role),
            mock.patch.object(self.bridge, "_workflow_transfer_sources", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_workflow_agent_transfer_destinations",
                return_value=[],
            ),
            mock.patch.object(
                self.bridge,
                "research_sheet_hub_read_model",
                return_value={"consumers": []},
            ),
            mock.patch.object(
                self.bridge,
                "ea_factory_read_model",
                side_effect=AssertionError("generic report must not calculate Factory"),
            ) as factory,
        ):
            model = self.bridge.workflow_dashboard_read_model(
                "right_server_racks",
                reports=[],
                missions=[],
                bridge={"time": "2026-09-12T00:00:00Z"},
            )
        self.assertNotIn("eaFactory", model)
        factory.assert_not_called()

    def test_dedicated_factory_model_exposes_same_bounded_busy_projection(self) -> None:
        build = self.build(
            "ea-build-model-busy",
            [self.stage("generate_source", "mission-model-busy", "running")],
        )
        missions = [{"id": "mission-model-busy", "status": "running"}]
        with (
            mock.patch.object(self.bridge, "load_missions", return_value=missions),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=self.state(build),
            ),
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status"),
            mock.patch.object(self.bridge, "_ea_factory_source_catalog", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_ea_factory_build_read_model",
                side_effect=lambda row: copy.deepcopy(row),
            ),
            mock.patch.object(self.bridge, "_ea_factory_sheet_schema_read_model", return_value={}),
        ):
            model = self.bridge._ea_factory_read_model_uncached(
                selection={},
                terminal_gates={
                    "mt4": {},
                    "mt5": {},
                    "tradingview": {},
                },
                research_sheet_hub_model={},
                front_office_supported_platforms=(),
                front_office_handlers_connected=False,
            )
        self.assertEqual(model["busy"]["buildId"], build["id"])
        self.assertEqual(model["busy"]["missionStatus"], "running")
        self.assertNotIn("detail", model["busy"])

    def test_create_busy_rejection_precedes_report_catalog_load(self) -> None:
        active = self.build(
            "ea-build-active",
            [self.stage("generate_source", "mission-active", "running")],
        )
        with (
            mock.patch.object(
                self.bridge,
                "load_missions",
                return_value=[{"id": "mission-active", "status": "running"}],
            ),
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=self.state(active),
            ),
            mock.patch.object(self.bridge, "load_runtime_reports") as reports,
            mock.patch.object(self.bridge, "_ea_factory_source_catalog") as catalog,
        ):
            started = time.monotonic()
            with self.assertRaises(self.bridge.RequestError) as raised:
                self.bridge.create_ea_factory_build({
                    "sourceRecordId": "source-new",
                    "platform": "mt4",
                    "artifactKind": "expert_advisor",
                    "idempotencyKey": "create-busy-123",
                })
            elapsed = time.monotonic() - started
        self.assertEqual(raised.exception.status, 409)
        self.assertEqual(raised.exception.code, "ea_factory_single_active_build")
        self.assertLess(elapsed, 0.5)
        reports.assert_not_called()
        catalog.assert_not_called()

    def test_run_replay_never_starts_stale_build_beside_live_other_build(self) -> None:
        stale = self.build(
            "ea-build-stale-replay",
            [self.stage("generate_source", None, "pending")],
        )
        stale["oneClickRun"] = {
            "idempotencyKey": "one-click-stale-123",
            "requestDigest": self.bridge._ea_factory_one_click_request_digest(stale),
            "status": "queued",
        }
        live = self.build(
            "ea-build-live-other",
            [self.stage("generate_source", None, "pending")],
        )
        self.bridge.EA_FACTORY_ONE_CLICK_THREADS[live["id"]] = mock.Mock(
            is_alive=mock.Mock(return_value=True)
        )
        with (
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=self.state(stale, live),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_read_model",
                return_value={"status": "queued"},
            ),
            mock.patch.object(self.bridge, "_start_ea_factory_one_click_thread") as start,
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write,
            mock.patch.object(self.bridge, "append_audit") as audit,
        ):
            result = self.bridge.run_ea_factory_build_one_click(
                stale["id"],
                {"idempotencyKey": "one-click-stale-123"},
            )
        self.assertTrue(result["idempotentReplay"])
        self.assertFalse(result["workerStarted"])
        start.assert_not_called()
        write.assert_not_called()
        audit.assert_not_called()

    def test_advance_and_retry_reject_different_active_build_before_reconcile(self) -> None:
        target_stage = self.stage("generate_source", "mission-failed", "failed")
        target_stage["blockedReasonCode"] = "invalid_output"
        target = self.build("ea-build-target", [target_stage])
        active = self.build(
            "ea-build-other-active",
            [self.stage("generate_source", "mission-active", "running")],
        )
        missions = [
            {"id": "mission-failed", "status": "failed", "errorCode": "invalid_output"},
            {"id": "mission-active", "status": "queued"},
        ]
        with (
            mock.patch.object(self.bridge, "load_missions", return_value=missions),
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=self.state(target, active),
            ),
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status") as reconcile,
        ):
            with self.assertRaises(self.bridge.RequestError) as advance_error:
                self.bridge.advance_ea_factory_build(
                    target["id"],
                    {"stageId": "generate_source", "idempotencyKey": "advance-busy-123"},
                )
            with self.assertRaises(self.bridge.RequestError) as retry_error:
                self.bridge.retry_ea_factory_build_stage(
                    target["id"],
                    {
                        "stageId": "generate_source",
                        "failedMissionId": "mission-failed",
                        "idempotencyKey": "retry-busy-123",
                    },
                )
        self.assertEqual(advance_error.exception.status, 409)
        self.assertEqual(retry_error.exception.status, 409)
        reconcile.assert_not_called()

    def test_worker_thread_exemption_never_applies_to_another_active_build(self) -> None:
        target_stage = self.stage("generate_source", "mission-failed", "failed")
        target_stage["blockedReasonCode"] = "invalid_output"
        target = self.build("ea-build-worker-target", [target_stage])
        active = self.build(
            "ea-build-worker-other",
            [self.stage("generate_source", "mission-worker-other", "running")],
        )
        missions = [
            {"id": "mission-worker-other", "status": "running"},
            {"id": "mission-failed", "status": "failed", "errorCode": "invalid_output"},
        ]
        self.bridge.EA_FACTORY_ONE_CLICK_THREADS[target["id"]] = threading.current_thread()
        with (
            mock.patch.object(self.bridge, "load_missions", return_value=missions),
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=self.state(active, target),
            ),
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status") as reconcile,
        ):
            with self.assertRaises(self.bridge.RequestError) as advance_error:
                self.bridge.advance_ea_factory_build(
                    target["id"],
                    {"stageId": "generate_source", "idempotencyKey": "advance-worker-other"},
                )
            with self.assertRaises(self.bridge.RequestError) as retry_error:
                self.bridge.retry_ea_factory_build_stage(
                    target["id"],
                    {
                        "stageId": "generate_source",
                        "failedMissionId": "mission-failed",
                        "idempotencyKey": "retry-worker-other",
                    },
                )
        self.assertEqual(advance_error.exception.code, "ea_factory_single_active_build")
        self.assertEqual(retry_error.exception.code, "ea_factory_single_active_build")
        reconcile.assert_not_called()

    def test_retry_receipt_without_downstream_advance_returns_busy_not_sent(self) -> None:
        retry_key = "retry-receipt-only"
        advance_key = "ea-factory:source-retry:receipt-only"
        target_stage = self.stage("generate_source", None, "pending")
        target_stage["manualRetryCount"] = 1
        target_stage["manualRetryHistory"] = [{
            "attempt": 1,
            "idempotencyKey": retry_key,
            "advanceIdempotencyKey": advance_key,
            "failedMissionId": "mission-old-failed",
        }]
        target = self.build("ea-build-retry-receipt", [target_stage])
        active = self.build(
            "ea-build-retry-active-other",
            [self.stage("generate_source", "mission-retry-active", "running")],
        )
        with (
            mock.patch.object(
                self.bridge,
                "load_missions",
                return_value=[{"id": "mission-retry-active", "status": "queued"}],
            ),
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=self.state(target, active),
            ),
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status") as reconcile,
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write,
            mock.patch.object(self.bridge, "advance_ea_factory_build") as advance,
        ):
            with self.assertRaises(self.bridge.RequestError) as raised:
                self.bridge.retry_ea_factory_build_stage(
                    target["id"],
                    {
                        "stageId": "generate_source",
                        "failedMissionId": "mission-old-failed",
                        "idempotencyKey": retry_key,
                    },
                )
        self.assertEqual(raised.exception.code, "ea_factory_single_active_build")
        self.assertNotIn("ส่ง", str(raised.exception))
        reconcile.assert_not_called()
        write.assert_not_called()
        advance.assert_not_called()

    def test_restart_resumes_only_oldest_candidate_and_quarantines_extra(self) -> None:
        older = self.build(
            "ea-build-restart-older",
            [self.stage("generate_source", None, "pending")],
        )
        newer = self.build(
            "ea-build-restart-newer",
            [self.stage("generate_source", None, "pending")],
        )
        older["oneClickRun"] = {
            "status": "queued",
            "currentStageId": "generate_source",
            "startedAt": "2026-09-12T00:00:01Z",
        }
        newer["oneClickRun"] = {
            "status": "running",
            "currentStageId": "generate_source",
            "startedAt": "2026-09-12T00:00:02Z",
        }
        state = self.state(newer, older)
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_one_click_thread",
                return_value=True,
            ) as start,
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write,
            mock.patch.object(self.bridge, "append_audit") as audit,
        ):
            resumed = self.bridge.resume_interrupted_ea_factory_one_click_runs()
        self.assertEqual(resumed, 1)
        start.assert_called_once_with(older["id"])
        self.assertEqual(older["oneClickRun"]["status"], "queued")
        self.assertEqual(newer["oneClickRun"]["status"], "blocked")
        self.assertEqual(
            newer["oneClickRun"]["failureCode"],
            "restart_single_active_conflict",
        )
        write.assert_called_once_with(state)
        self.assertEqual(
            audit.call_args.args[0]["quarantinedConflictCount"],
            1,
        )

    def test_restart_with_multiple_active_missions_starts_no_coordinator(self) -> None:
        first = self.build(
            "ea-build-restart-active-first",
            [self.stage("generate_source", "mission-restart-first", "running")],
        )
        second = self.build(
            "ea-build-restart-active-second",
            [self.stage("generate_source", "mission-restart-second", "queued")],
        )
        for index, build in enumerate((first, second), start=1):
            build["oneClickRun"] = {
                "status": "waiting_ai",
                "currentStageId": "generate_source",
                "startedAt": f"2026-09-12T00:00:0{index}Z",
            }
        state = self.state(second, first)
        missions = [
            {"id": "mission-restart-first", "status": "running"},
            {"id": "mission-restart-second", "status": "queued"},
        ]
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "load_missions", return_value=missions),
            mock.patch.object(self.bridge, "_start_ea_factory_one_click_thread") as start,
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write,
            mock.patch.object(self.bridge, "append_audit") as audit,
        ):
            resumed = self.bridge.resume_interrupted_ea_factory_one_click_runs()
        self.assertEqual(resumed, 0)
        start.assert_not_called()
        self.assertEqual(first["oneClickRun"]["status"], "blocked")
        self.assertEqual(second["oneClickRun"]["status"], "blocked")
        write.assert_called_once_with(state)
        self.assertEqual(audit.call_args.args[0]["quarantinedConflictCount"], 2)
        self.assertIsNone(audit.call_args.args[0]["selectedBuildId"])

    def test_generic_factory_actions_require_dedicated_backend_entrypoint(self) -> None:
        with (
            mock.patch.object(self.bridge, "find_room_prop", return_value={"id": "right_server_racks"}),
            mock.patch.object(self.bridge, "run_bridge_task") as run,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            with self.assertRaises(self.bridge.RequestError) as raised:
                self.bridge.run_dashboard_workflow_action(
                    "right_server_racks",
                    {
                        "actionId": "build_strategy_code",
                        "form": {},
                        "idempotencyKey": "legacy-factory-direct",
                    },
                )
        self.assertEqual(raised.exception.status, 409)
        response = self.bridge.request_error_response(raised.exception)
        self.assertEqual(response["code"], "ea_factory_dedicated_endpoint_required")
        self.assertIn("EA Factory", response["messageTh"])
        run.assert_not_called()

    def test_manual_execute_rejects_legacy_factory_mission_before_runner(self) -> None:
        mission = {
            "id": "mission-legacy-factory",
            "status": "waiting_approval",
            "targetId": "right_server_racks",
            "workflowContext": {
                "propId": "right_server_racks",
                "actionId": "review_source_code",
            },
        }
        with (
            mock.patch.object(self.bridge, "find_mission", return_value=mission),
            mock.patch.object(self.bridge, "run_safe_command") as runner,
            mock.patch.object(self.bridge, "bridge_status") as bridge_status,
            mock.patch.object(self.bridge, "append_audit") as audit,
        ):
            result = self.bridge.execute_mission(
                mission["id"],
                {"confirmMissionId": mission["id"]},
            )
        self.assertFalse(result["ok"])
        self.assertEqual(result["_httpStatus"], 409)
        self.assertEqual(result["code"], "ea_factory_dedicated_endpoint_required")
        runner.assert_not_called()
        bridge_status.assert_not_called()
        self.assertFalse(audit.call_args.args[0]["manualRunnerStarted"])

    def test_advance_exact_replay_is_pure_while_other_build_is_active(self) -> None:
        stage = self.stage("generate_source", "mission-old", "queued")
        target = self.build("ea-build-replay-target", [stage])
        stage.update({
            "requestIdempotencyKey": "advance-original-123",
            "requestDigest": self.bridge._ea_factory_advance_request_digest(
                target,
                "generate_source",
            ),
            "startedAt": "2026-09-12T00:00:01Z",
            "missionIdempotencyKey": "ea-factory:stage:original",
        })
        active = self.build(
            "ea-build-replay-other",
            [self.stage("generate_source", "mission-active", "running")],
        )
        missions = [
            {"id": "mission-old", "status": "completed"},
            {"id": "mission-active", "status": "running"},
        ]
        with (
            mock.patch.object(self.bridge, "load_missions", return_value=missions),
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=self.state(target, active),
            ),
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status") as reconcile,
            mock.patch.object(
                self.bridge,
                "_ea_factory_build_read_model",
                return_value={"id": target["id"]},
            ),
            mock.patch.object(
                self.bridge,
                "mission_read_model_item",
                side_effect=lambda row: copy.deepcopy(row),
            ),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write,
            mock.patch.object(self.bridge, "run_dashboard_workflow_action") as dispatch,
        ):
            result = self.bridge.advance_ea_factory_build(
                target["id"],
                {"stageId": "generate_source", "idempotencyKey": "new-browser-key-123"},
            )
        self.assertEqual(result["kind"], "ea_factory_stage_replayed")
        self.assertTrue(result["idempotentReplay"])
        reconcile.assert_not_called()
        write.assert_not_called()
        dispatch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
