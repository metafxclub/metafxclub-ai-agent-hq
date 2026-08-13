from __future__ import annotations

import importlib.util
import http.client
import json
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_bridge_read_stability_tests",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BridgeReadStabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        with self.bridge.RUNTIME_HEALTH_JSON_CACHE_LOCK:
            self.bridge.RUNTIME_HEALTH_JSON_CACHE.clear()
        self.bridge._invalidate_missions_read_cache()
        with self.bridge.EQUIPMENT_CONNECTION_CENTER_CACHE_CONDITION:
            self.bridge.EQUIPMENT_CONNECTION_CENTER_CACHE.update({
                "storedAtMonotonic": 0.0,
                "value": None,
                "refreshing": False,
                "generation": 0,
                "missionSignature": None,
            })
        with self.bridge.CODEX_STATUS_CACHE_CONDITION:
            self.bridge.CODEX_STATUS_CACHE.update({
                "payload": None,
                "fetchedMonotonic": 0.0,
                "refreshing": False,
            })
        with self.bridge.BRIDGE_STATUS_CACHE_CONDITION:
            self.bridge.BRIDGE_STATUS_CACHE.update({
                "payload": None,
                "fetchedMonotonic": 0.0,
                "refreshing": False,
            })

    def test_large_health_document_is_parsed_once_per_stat_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "missions.json"
            path.write_text(
                json.dumps({"missions": [{"id": f"m-{index}"} for index in range(4000)]}),
                encoding="utf-8",
            )
            validator = mock.Mock(
                side_effect=lambda value: isinstance(value, dict)
                and isinstance(value.get("missions"), list)
            )
            original_loads = self.bridge.json.loads
            with mock.patch.object(
                self.bridge.json,
                "loads",
                wraps=original_loads,
            ) as loads:
                value, first = self.bridge._runtime_health_json_document(
                    "missionStoreTest",
                    path,
                    False,
                    validator,
                    retain_value=False,
                )
                self.assertEqual(value, {})
                self.assertTrue(first["validJson"])
                self.assertTrue(first["schemaValid"])
                self.assertEqual(loads.call_count, 1)
                self.assertEqual(validator.call_count, 1)

                backup_path = path.with_name(f"{path.name}.bak")
                backup_path.write_text("{}", encoding="utf-8")
                cached_value, cached = self.bridge._runtime_health_json_document(
                    "missionStoreTest",
                    path,
                    False,
                    validator,
                    retain_value=False,
                )
                self.assertEqual(cached_value, {})
                self.assertTrue(cached["backupAvailable"])
                self.assertEqual(loads.call_count, 1)
                self.assertEqual(validator.call_count, 1)

                cache_key = f"missionStoreTest:{path.resolve(strict=False)}"
                self.assertIsNone(
                    self.bridge.RUNTIME_HEALTH_JSON_CACHE[cache_key]["value"]
                )

                path.write_text('{"missions": [', encoding="utf-8")
                _value, corrupt = self.bridge._runtime_health_json_document(
                    "missionStoreTest",
                    path,
                    False,
                    validator,
                    retain_value=False,
                )
                self.assertFalse(corrupt["validJson"])
                self.assertFalse(corrupt["schemaValid"])
                self.assertEqual(loads.call_count, 2)

                path.write_text('{"missions": []}', encoding="utf-8")
                _value, repaired = self.bridge._runtime_health_json_document(
                    "missionStoreTest",
                    path,
                    False,
                    validator,
                    retain_value=False,
                )
                self.assertTrue(repaired["validJson"])
                self.assertTrue(repaired["schemaValid"])
                self.assertEqual(loads.call_count, 3)
                self.assertEqual(validator.call_count, 2)

    def test_small_health_contract_retains_parsed_value(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "room.json"
            expected = {"props": [], "layers": []}
            path.write_text(json.dumps(expected), encoding="utf-8")
            validator = mock.Mock(return_value=True)

            first, first_integrity = self.bridge._runtime_health_json_document(
                "roomContractTest",
                path,
                True,
                validator,
                retain_value=True,
            )
            second, second_integrity = self.bridge._runtime_health_json_document(
                "roomContractTest",
                path,
                True,
                validator,
                retain_value=True,
            )

            self.assertEqual(first, expected)
            self.assertEqual(second, expected)
            self.assertEqual(first_integrity, second_integrity)
            self.assertEqual(validator.call_count, 1)

    def test_health_stat_error_and_non_file_path_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "missions.json"
            path.write_text('{"missions": []}', encoding="utf-8")
            cache_key = f"missionStoreStatTest:{path.resolve(strict=False)}"

            with mock.patch.object(Path, "stat", side_effect=OSError("sharing violation")):
                _value, stat_error = self.bridge._runtime_health_json_document(
                    "missionStoreStatTest",
                    path,
                    False,
                    lambda value: isinstance(value, dict),
                    retain_value=False,
                )
            self.assertFalse(stat_error["validJson"])
            self.assertFalse(stat_error["schemaValid"])
            self.assertNotIn(cache_key, self.bridge.RUNTIME_HEALTH_JSON_CACHE)

            path.unlink()
            path.mkdir()
            _value, wrong_type = self.bridge._runtime_health_json_document(
                "missionStoreStatTest",
                path,
                False,
                lambda value: isinstance(value, dict),
                retain_value=False,
            )
            self.assertFalse(wrong_type["validJson"])
            self.assertFalse(wrong_type["schemaValid"])

    def test_runtime_mission_window_keeps_attention_items_and_bounds_history(self) -> None:
        missions = [
            {"id": "run", "status": "running", "title": "Running"},
            {"id": "done-1", "status": "completed", "title": "Newest done"},
            {"id": "block", "status": "blocked", "title": "Needs attention"},
            {"id": "fail", "status": "failed", "title": "Failed"},
            {"id": "queue", "status": "queued", "title": "Queued"},
            {"id": "done-2", "status": "completed", "title": "Second done"},
            {"id": "archive", "status": "archived", "title": "Archived"},
            {"id": "done-1", "status": "completed", "title": "Duplicate old copy"},
            {"id": "done-3", "status": "completed", "title": "Old done"},
        ]

        selected, metadata = self.bridge.mission_runtime_window(
            missions,
            terminal_limit=2,
        )

        self.assertEqual(
            [mission["id"] for mission in selected],
            ["run", "done-1", "block", "fail", "queue", "done-2"],
        )
        self.assertEqual(metadata["terminalLimit"], 2)
        self.assertEqual(
            metadata["maximumReturned"],
            self.bridge.MISSIONS_RUNTIME_MAX_RETURNED,
        )
        self.assertEqual(metadata["returnedCount"], 6)
        self.assertEqual(metadata["actionableCount"], 4)
        self.assertEqual(metadata["actionableReturned"], 4)
        self.assertEqual(metadata["actionableOmitted"], 0)
        self.assertEqual(metadata["routineTerminalReturned"], 2)
        self.assertEqual(metadata["uniqueCount"], 8)
        self.assertTrue(metadata["truncated"])

    def test_runtime_mission_window_hard_bounds_large_attention_backlog(self) -> None:
        maximum = self.bridge.MISSIONS_RUNTIME_MAX_RETURNED
        missions = [
            {
                "id": f"blocked-{index}",
                "status": "blocked",
                "title": f"Blocked {index}",
            }
            for index in range(maximum + 275)
        ] + [
            {
                "id": f"completed-{index}",
                "status": "completed",
                "title": f"Completed {index}",
            }
            for index in range(200)
        ]

        selected, metadata = self.bridge.mission_runtime_window(
            missions,
            terminal_limit=100,
        )

        self.assertEqual(len(selected), maximum)
        self.assertEqual(metadata["returnedCount"], maximum)
        self.assertEqual(metadata["actionableCount"], maximum + 275)
        self.assertEqual(metadata["actionableReturned"], maximum)
        self.assertEqual(metadata["actionableOmitted"], 275)
        self.assertEqual(metadata["routineTerminalReturned"], 0)
        self.assertEqual(metadata["uniqueCount"], maximum + 475)
        self.assertTrue(metadata["truncated"])

    def test_runtime_endpoint_projection_is_coalesced_per_store_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "missions.json"
            path.write_text(
                json.dumps({
                    "missions": [
                        {"id": f"m-{index}", "status": "completed"}
                        for index in range(1500)
                    ]
                }),
                encoding="utf-8",
            )
            original_window = self.bridge.mission_runtime_window
            with (
                mock.patch.object(self.bridge, "MISSIONS_PATH", path),
                mock.patch.object(
                    self.bridge,
                    "mission_runtime_window",
                    wraps=original_window,
                ) as window,
            ):
                self.bridge._invalidate_missions_read_cache()
                missions = self.bridge.load_missions(shared_snapshot=True)
                with ThreadPoolExecutor(max_workers=12) as pool:
                    snapshots = list(pool.map(
                        lambda _: self.bridge.mission_runtime_endpoint_snapshot(
                            missions,
                            100,
                        ),
                        range(12),
                    ))
                self.assertEqual(window.call_count, 1)
                self.assertEqual({item["totalCount"] for item in snapshots}, {1500})
                self.assertEqual({len(item["missions"]) for item in snapshots}, {100})
                self.assertEqual(sum(bool(item["runtimeWindow"]["cacheHit"]) for item in snapshots), 11)

                path.write_text(
                    json.dumps({
                        "missions": [
                            {"id": "revision-2", "status": "running"}
                        ]
                    }),
                    encoding="utf-8",
                )
                revised_missions = self.bridge.load_missions(shared_snapshot=True)
                revised = self.bridge.mission_runtime_endpoint_snapshot(
                    revised_missions,
                    100,
                )

            self.assertEqual(window.call_count, 2)
            self.assertEqual(revised["totalCount"], 1)
            self.assertEqual(revised["missions"][0]["id"], "revision-2")
            self.assertFalse(revised["runtimeWindow"]["cacheHit"])

    def test_default_runtime_response_reuses_preencoded_bytes_per_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "missions.json"
            path.write_text(
                json.dumps({
                    "missions": [
                        {
                            "id": f"running-{index}",
                            "status": "running",
                            "detail": "x" * 1800,
                        }
                        for index in range(700)
                    ]
                }),
                encoding="utf-8",
            )
            with mock.patch.object(self.bridge, "MISSIONS_PATH", path):
                self.bridge._invalidate_missions_read_cache()
                missions = self.bridge.load_missions(shared_snapshot=True)
                snapshot = self.bridge.mission_runtime_endpoint_snapshot(missions, 100)
                runtime_window = dict(snapshot["runtimeWindow"])
                runtime_window.pop("cacheHit", None)
                payload = {
                    "missions": snapshot["missions"],
                    "counts": snapshot["counts"],
                    "readModel": "mission_list_v1",
                    "scope": "runtime",
                    "requestedScope": None,
                    "defaultScopeApplied": True,
                    "fullArchiveRequiresExplicitScope": True,
                    "countsScope": "all",
                    "totalCount": snapshot["totalCount"],
                    "returnedCount": len(snapshot["missions"]),
                    "truncated": True,
                    "runtimeWindow": runtime_window,
                    "updatedAt": "2026-08-12T00:00:00Z",
                }
                first, first_hit = self.bridge.mission_runtime_preencoded_response(
                    payload,
                    terminal_limit=100,
                    expected_signature=snapshot["_storeSignature"],
                )
                second, second_hit = self.bridge.mission_runtime_preencoded_response(
                    payload,
                    terminal_limit=100,
                    expected_signature=snapshot["_storeSignature"],
                )
                for terminal_limit in range(101, 108):
                    self.bridge.mission_runtime_preencoded_response(
                        payload,
                        terminal_limit=terminal_limit,
                        expected_signature=snapshot["_storeSignature"],
                    )
                serialized_cache_size = len(
                    self.bridge.MISSIONS_READ_CACHE["serializedRuntimeResponses"]
                )

            self.assertFalse(first_hit)
            self.assertTrue(second_hit)
            self.assertIs(first, second)
            decoded = json.loads(first.decode("utf-8"))
            self.assertEqual(decoded["returnedCount"], 500)
            self.assertEqual(decoded["totalCount"], 700)
            self.assertNotIn(b"\n  ", first)
            self.assertLessEqual(
                serialized_cache_size,
                self.bridge.MISSIONS_SERIALIZED_RUNTIME_CACHE_MAX_ENTRIES,
            )

    def test_cached_legacy_mission_http_stress_does_not_starve_health(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "missions.json"
            path.write_text(
                json.dumps({
                    "missions": [
                        {
                            "id": f"running-{index}",
                            "status": "running",
                            "title": f"Running {index}",
                            "detail": "stress-payload-" + ("x" * 1800),
                        }
                        for index in range(700)
                    ]
                }),
                encoding="utf-8",
            )

            def health() -> dict:
                return {
                    "ok": True,
                    "status": "ready",
                    "checkedAt": self.bridge.utc_now(),
                }

            with (
                mock.patch.object(self.bridge, "MISSIONS_PATH", path),
                mock.patch.object(self.bridge, "runtime_health", side_effect=health),
            ):
                self.bridge._invalidate_missions_read_cache()
                server = self.bridge.BridgeHTTPServer(
                    ("127.0.0.1", 0),
                    self.bridge.BridgeHandler,
                )
                worker = threading.Thread(target=server.serve_forever, daemon=True)
                worker.start()

                def request(path_value: str, barrier=None) -> tuple[float, int, int, str | None]:
                    if barrier is not None:
                        barrier.wait(timeout=5)
                    started = time.perf_counter()
                    connection = http.client.HTTPConnection(
                        "127.0.0.1",
                        server.server_port,
                        timeout=5,
                    )
                    try:
                        connection.request("GET", path_value)
                        response = connection.getresponse()
                        body = response.read()
                        return (
                            time.perf_counter() - started,
                            response.status,
                            len(body),
                            response.getheader("X-Metafx-Projection-Cache"),
                        )
                    finally:
                        connection.close()

                try:
                    warm = request("/api/missions")
                    self.assertEqual(warm[1], 200)
                    self.assertGreater(warm[2], 750_000)
                    self.assertEqual(warm[3], "miss")

                    barrier = threading.Barrier(12)
                    paths = ["/api/missions"] * 8 + ["/api/health"] * 4
                    with ThreadPoolExecutor(max_workers=12) as pool:
                        futures = [
                            pool.submit(request, path_value, barrier)
                            for path_value in paths
                        ]
                        results = [future.result(timeout=8) for future in futures]
                finally:
                    server.shutdown()
                    server.server_close()
                    worker.join(timeout=5)

            mission_results = results[:8]
            health_results = results[8:]
            self.assertTrue(all(item[1] == 200 for item in results))
            self.assertTrue(all(item[3] == "hit" for item in mission_results))
            self.assertTrue(all(item[2] > 750_000 for item in mission_results))
            self.assertLess(max(item[0] for item in health_results), 0.25)

    def test_runtime_health_does_not_reload_full_mission_store_for_queue_depth(self) -> None:
        scheduler = {
            "status": "running",
            "alive": True,
            "operational": True,
            "lastHeartbeatAt": self.bridge.utc_now(),
        }
        with (
            mock.patch.object(
                self.bridge,
                "dashboard_workflow_scheduler_read_model",
                return_value=scheduler,
            ),
            mock.patch.object(self.bridge, "load_missions") as load_missions,
        ):
            health = self.bridge.runtime_health()

        load_missions.assert_not_called()
        self.assertIsNone(health["missionWorker"]["queued"])
        self.assertFalse(health["missionWorker"]["queueCountAvailable"])

    def test_missions_endpoint_defaults_bounded_and_explicit_admin_is_full(self) -> None:
        missions = [
            {"id": "run", "status": "running", "title": "Running"},
            {"id": "done-1", "status": "completed", "title": "Done 1"},
            {"id": "block", "status": "blocked", "title": "Blocked"},
            {"id": "done-2", "status": "completed", "title": "Done 2"},
            {"id": "done-3", "status": "completed", "title": "Done 3"},
        ]

        def request(path: str) -> dict:
            handler = object.__new__(self.bridge.BridgeHandler)
            handler.path = path
            handler.validate_local_request = mock.Mock(return_value=None)
            response: dict = {}
            handler.send_json = lambda payload, status=200: response.update(
                {"payload": payload, "status": status}
            )
            with mock.patch.object(self.bridge, "load_missions", return_value=missions):
                handler._do_GET_guarded()
            return response["payload"]

        bounded_default = request("/api/missions?limit=1")
        self.assertEqual(
            [item["id"] for item in bounded_default["missions"]],
            ["run", "done-1", "block"],
        )
        self.assertEqual(bounded_default["scope"], "runtime")
        self.assertTrue(bounded_default["defaultScopeApplied"])
        self.assertEqual(bounded_default["countsScope"], "all")
        self.assertEqual(bounded_default["totalCount"], 5)
        self.assertEqual(bounded_default["returnedCount"], 3)
        self.assertTrue(bounded_default["truncated"])

        for explicit_scope in ("all", "admin", "full"):
            with self.subTest(scope=explicit_scope):
                full = request(f"/api/missions?scope={explicit_scope}")
                self.assertEqual(
                    [item["id"] for item in full["missions"]],
                    [item["id"] for item in missions],
                )
                self.assertEqual(full["scope"], "full")
                self.assertEqual(full["requestedScope"], explicit_scope)
                self.assertFalse(full["defaultScopeApplied"])
                self.assertEqual(full["totalCount"], 5)
                self.assertEqual(full["returnedCount"], 5)
                self.assertFalse(full["truncated"])
                self.assertIsNone(full["runtimeWindow"])

        runtime = request("/api/missions?scope=runtime&limit=1")
        self.assertEqual(
            [item["id"] for item in runtime["missions"]],
            ["run", "done-1", "block"],
        )
        self.assertEqual(runtime["scope"], "runtime")
        self.assertEqual(runtime["totalCount"], 5)
        self.assertEqual(runtime["returnedCount"], 3)
        self.assertEqual(runtime["counts"], {"running": 1, "completed": 3, "blocked": 1})
        self.assertTrue(runtime["truncated"])

    def test_concurrent_mission_reads_parse_once_and_revision_invalidates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "missions.json"
            path.write_text(
                json.dumps({
                    "missions": [
                        {"id": f"mission-{index}", "status": "completed"}
                        for index in range(2000)
                    ]
                }),
                encoding="utf-8",
            )
            self.bridge._invalidate_missions_read_cache()
            original_read_json = self.bridge.read_json
            parse_count = 0
            count_lock = threading.Lock()

            def counted_read_json(*args, **kwargs):
                nonlocal parse_count
                with count_lock:
                    parse_count += 1
                time.sleep(0.02)
                return original_read_json(*args, **kwargs)

            with (
                mock.patch.object(self.bridge, "MISSIONS_PATH", path),
                mock.patch.object(self.bridge, "read_json", side_effect=counted_read_json),
            ):
                with ThreadPoolExecutor(max_workers=12) as pool:
                    rows = list(
                        pool.map(
                            lambda _: self.bridge.load_missions(shared_snapshot=True),
                            range(12),
                        )
                    )
                self.assertEqual(parse_count, 1)
                self.assertEqual({len(items) for items in rows}, {2000})
                self.assertEqual(len({id(items) for items in rows}), 1)

                path.write_text(
                    json.dumps({"missions": [{"id": "revision-2", "status": "queued"}]}),
                    encoding="utf-8",
                )
                revised = self.bridge.load_missions(shared_snapshot=True)

            self.assertEqual(parse_count, 2)
            self.assertEqual([item["id"] for item in revised], ["revision-2"])

    def test_connection_center_cold_miss_is_single_flight_under_load(self) -> None:
        call_count = 0
        count_lock = threading.Lock()
        value = {
            "schemaVersion": "hq-equipment-connection-center-v1",
            "checkedAt": "2026-08-12T00:00:00Z",
            "summary": {"deviceCount": 9},
            "devices": [{"propId": f"p-{index}"} for index in range(9)],
            "services": {},
            "privacy": {},
        }

        def slow_builder(*args, **kwargs):
            nonlocal call_count
            with count_lock:
                call_count += 1
            time.sleep(0.08)
            return value

        with mock.patch.object(
            self.bridge,
            "_build_equipment_connection_center_read_model",
            side_effect=slow_builder,
        ):
            started = time.perf_counter()
            with ThreadPoolExecutor(max_workers=16) as pool:
                results = list(
                    pool.map(
                        lambda _: self.bridge._equipment_connection_center_read_model(),
                        range(16),
                    )
                )
            elapsed = time.perf_counter() - started

        self.assertEqual(call_count, 1)
        self.assertLess(elapsed, 0.5)
        self.assertTrue(all(item["summary"]["deviceCount"] == 9 for item in results))
        self.assertTrue(all(item["cache"]["refreshInProgress"] is False for item in results))

    def test_connection_center_returns_labeled_stale_last_good_during_refresh(self) -> None:
        cached = {
            "schemaVersion": "hq-equipment-connection-center-v1",
            "checkedAt": "2026-08-12T00:00:00Z",
            "summary": {"deviceCount": 9},
            "devices": [],
            "services": {},
            "privacy": {},
        }
        with self.bridge.EQUIPMENT_CONNECTION_CENTER_CACHE_CONDITION:
            self.bridge.EQUIPMENT_CONNECTION_CENTER_CACHE.update({
                "storedAtMonotonic": time.monotonic()
                - self.bridge.EQUIPMENT_CONNECTION_CENTER_CACHE_TTL_SECONDS
                - 1,
                "value": cached,
                "refreshing": True,
                "missionSignature": self.bridge._mission_store_signature(),
            })

        started = time.perf_counter()
        result = self.bridge._equipment_connection_center_read_model()
        elapsed = time.perf_counter() - started

        self.assertLess(elapsed, 0.1)
        self.assertEqual(result["summary"]["deviceCount"], 9)
        self.assertTrue(result["cache"]["hit"])
        self.assertTrue(result["cache"]["stale"])
        self.assertTrue(result["cache"]["refreshInProgress"])
        self.assertFalse(result["snapshotFresh"])

    def test_codex_and_bridge_status_probes_are_single_flight(self) -> None:
        codex_calls = 0
        bridge_calls = 0
        count_lock = threading.Lock()

        def slow_codex():
            nonlocal codex_calls
            with count_lock:
                codex_calls += 1
            time.sleep(0.05)
            return {"status": "ready", "path": "project_runner", "version": "test"}

        def slow_bridge():
            nonlocal bridge_calls
            with count_lock:
                bridge_calls += 1
            time.sleep(0.05)
            return {
                "ok": True,
                "mode": "Codex Runner Ready",
                "status": "guarded",
                "server": "Metafx Local Bridge",
                "root": "local_project",
                "codex": {"status": "ready"},
                "mcp": {"status": "config_present", "configPresent": True},
                "policy": {},
                "time": self.bridge.utc_now(),
            }

        with mock.patch.object(self.bridge, "_detect_codex_uncached", side_effect=slow_codex):
            with ThreadPoolExecutor(max_workers=10) as pool:
                codex_results = list(pool.map(lambda _: self.bridge.detect_codex(), range(10)))
        with mock.patch.object(self.bridge, "_bridge_status_uncached", side_effect=slow_bridge):
            with ThreadPoolExecutor(max_workers=10) as pool:
                bridge_results = list(pool.map(lambda _: self.bridge.bridge_status(), range(10)))

        self.assertEqual(codex_calls, 1)
        self.assertEqual(bridge_calls, 1)
        self.assertTrue(any(item["status"] == "ready" for item in codex_results))
        self.assertTrue(any(item["codex"]["status"] == "ready" for item in bridge_results))
        self.assertTrue(all(item.get("refreshInProgress") is not None for item in codex_results))
        self.assertTrue(all(item.get("refreshInProgress") is not None for item in bridge_results))

    def test_prop_report_passes_one_mission_snapshot_to_nested_read_models(self) -> None:
        shared = [{"id": "mission-shared", "status": "running"}]
        checklist_calls: list[dict] = []
        workflow_calls: list[dict] = []

        def checklist(_prop_id, **kwargs):
            checklist_calls.append(kwargs)
            return {}

        def workflow(_prop_id, **kwargs):
            workflow_calls.append(kwargs)
            return {}

        bridge = {
            "status": "guarded",
            "time": "2026-08-12T00:00:00Z",
            "codex": {"status": "ready_guarded"},
            "mcp": {"status": "config_present", "configPresent": True},
        }
        with (
            mock.patch.object(self.bridge, "load_missions", return_value=shared) as loader,
            mock.patch.object(self.bridge, "load_agent_events", return_value=[]),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
            mock.patch.object(self.bridge, "load_meeting_records", return_value=[]),
            mock.patch.object(self.bridge, "load_memory_index", return_value={"items": []}),
            mock.patch.object(self.bridge, "bridge_status", return_value=bridge),
            mock.patch.object(
                self.bridge,
                "capability_registry",
                return_value={"capabilities": [], "bridge": {}},
            ),
            mock.patch.object(
                self.bridge,
                "dashboard_connection_checklist",
                side_effect=checklist,
            ),
            mock.patch.object(
                self.bridge,
                "workflow_dashboard_read_model",
                side_effect=workflow,
            ),
        ):
            result = self.bridge.prop_report("right_status_crystals")

        loader.assert_called_once_with(shared_snapshot=True)
        self.assertIs(checklist_calls[0]["missions"], shared)
        self.assertIs(workflow_calls[0]["missions"], shared)
        self.assertEqual(result["connectionSourcePropId"], "right_status_crystals")

    def test_get_and_post_disconnects_are_not_audited_or_replied_twice(self) -> None:
        for method_name, disconnect in (
            ("do_GET", BrokenPipeError("client left")),
            ("do_POST", ConnectionResetError("client reset")),
        ):
            with self.subTest(method=method_name):
                handler = object.__new__(self.bridge.BridgeHandler)
                handler.path = "/api/missions"
                handler.send_json_disconnect_safe = mock.Mock()
                if method_name == "do_GET":
                    handler._do_GET_guarded = mock.Mock(side_effect=disconnect)
                else:
                    handler.validate_local_request = mock.Mock(side_effect=disconnect)
                with mock.patch.object(self.bridge, "append_audit") as append_audit:
                    getattr(handler, method_name)()
                append_audit.assert_not_called()
                handler.send_json_disconnect_safe.assert_not_called()

    def test_error_response_swallows_disconnect(self) -> None:
        handler = object.__new__(self.bridge.BridgeHandler)
        handler.send_json = mock.Mock(side_effect=ConnectionAbortedError("closed"))
        self.assertFalse(handler.send_json_disconnect_safe({"ok": False}, status=500))


if __name__ == "__main__":
    unittest.main()
