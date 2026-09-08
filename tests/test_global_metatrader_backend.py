from __future__ import annotations

import importlib.util
import json
import tempfile
import threading
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
CONNECTION_CONTRACT_PATH = (
    PROJECT_ROOT / "contracts" / "connections" / "dashboard-connection-contract.json"
)
BRIDGE_CONTRACT_PATH = PROJECT_ROOT / "contracts" / "bridge" / "bridge-contract.json"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "global_metatrader_backend_test_bridge",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GlobalMetatraderBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir(parents=True)
        self.mt4_path = self.root / "terminal-mt4"
        self.mt5_path = self.root / "terminal-mt5"
        (self.mt4_path / "MQL4").mkdir(parents=True)
        (self.mt5_path / "MQL5").mkdir(parents=True)
        self.mt4_id = "mtc-" + ("m" * 26)
        self.mt5_id = "mtc-" + ("n" * 26)
        self.original_cache = dict(self.bridge.METATRADER_CACHE)
        self.bridge.RUNTIME_DIR = self.runtime
        self._write_store()
        terminal_model = self.bridge.metatrader_status_read_model(
            {"mt4": 1, "mt5": 1},
            {"supported": True, "mt4": 0, "mt5": 0},
            [
                self.bridge._public_metatrader_candidate(
                    self._candidate_record("mt4", self.mt4_id, self.mt4_path, 1)
                ),
                self.bridge._public_metatrader_candidate(
                    self._candidate_record("mt5", self.mt5_id, self.mt5_path, 1)
                ),
            ],
        )
        self.bridge.METATRADER_CACHE.clear()
        self.bridge.METATRADER_CACHE.update({
            "payload": terminal_model,
            "fetchedMonotonic": 0.0,
        })

    def tearDown(self) -> None:
        self.bridge.METATRADER_CACHE.clear()
        self.bridge.METATRADER_CACHE.update(self.original_cache)
        self.temp.cleanup()

    def _candidate_record(
        self,
        platform: str,
        candidate_id: str,
        path: Path,
        ordinal: int,
    ) -> dict:
        local_path = self.bridge._canonical_metatrader_location(path)
        return {
            "candidateId": candidate_id,
            "identityKey": self.bridge._metatrader_identity_key(platform, local_path),
            "platform": platform,
            "ordinal": ordinal,
            "localPath": local_path,
            "installPath": None,
            "dataPath": local_path,
            "firstSeenAt": "2026-09-07T00:00:00Z",
            "lastSeenAt": "2026-09-07T00:00:00Z",
            "available": True,
            "runningState": "not_running_detected",
        }

    def _write_store(self, selections: dict | None = None) -> None:
        store = {
            "schemaVersion": self.bridge.METATRADER_TARGET_STORE_SCHEMA_VERSION,
            "candidates": {
                self.mt4_id: self._candidate_record(
                    "mt4", self.mt4_id, self.mt4_path, 1
                ),
                self.mt5_id: self._candidate_record(
                    "mt5", self.mt5_id, self.mt5_path, 1
                ),
            },
            "selections": selections or {},
            "updatedAt": "2026-09-07T00:00:00Z",
        }
        self.bridge.write_json(
            self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME,
            store,
        )

    def _add_second_mt4_candidate(
        self,
        *,
        first_running: bool = False,
        second_running: bool = False,
    ) -> str:
        second_path = self.root / "terminal-mt4-second"
        (second_path / "MQL4").mkdir(parents=True)
        second_id = "mtc-" + ("p" * 26)
        store_path = self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME
        store = json.loads(store_path.read_text(encoding="utf-8"))
        store["candidates"][self.mt4_id]["runningState"] = (
            "platform_running_detected"
            if first_running
            else "not_running_detected"
        )
        second = self._candidate_record("mt4", second_id, second_path, 2)
        second["runningState"] = (
            "platform_running_detected"
            if second_running
            else "not_running_detected"
        )
        store["candidates"][second_id] = second
        self.bridge.write_json(store_path, store)
        return second_id

    def _action_patches(self) -> ExitStack:
        stack = ExitStack()
        stack.enter_context(mock.patch.object(
            self.bridge,
            "check_rate_limit",
            return_value=(True, 0),
        ))
        stack.enter_context(mock.patch.object(
            self.bridge,
            "create_mission",
            return_value={
                "id": "mission-global-metatrader",
                "owner": "manager",
                "targetId": self.bridge.GLOBAL_METATRADER_DISCOVERY_PROP_ID,
            },
        ))
        stack.enter_context(mock.patch.object(
            self.bridge,
            "create_report",
            side_effect=lambda payload: {"id": "report-global-metatrader", **payload},
        ))
        stack.enter_context(mock.patch.object(
            self.bridge,
            "report_read_model_item",
            side_effect=lambda report: report,
        ))
        stack.enter_context(mock.patch.object(
            self.bridge,
            "_complete_diagnostic_mission",
            side_effect=lambda mission, report, result: mission,
        ))
        stack.enter_context(mock.patch.object(
            self.bridge,
            "_fail_diagnostic_mission",
            side_effect=lambda mission, audit_type, error_code: mission,
        ))
        stack.enter_context(mock.patch.object(self.bridge, "append_audit"))
        return stack

    def test_mt4_selection_is_one_atomic_write_for_all_three_consumers(self) -> None:
        self._write_store({
            "right_server_racks": {
                "candidateId": self.mt5_id,
                "selectedAt": "2026-09-07T00:00:00Z",
                "selectionRevision": 4,
            }
        })
        original_write = self.bridge._write_metatrader_target_store_unlocked
        with self._action_patches(), mock.patch.object(
            self.bridge,
            "_write_metatrader_target_store_unlocked",
            wraps=original_write,
        ) as write_store:
            result = self.bridge.select_global_metatrader_target(
                "MT4",
                self.mt4_id,
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["atomic"])
        self.assertEqual(result["configuredTargetCount"], 3)
        self.assertEqual(
            result["targetPropIds"],
            [
                "left_analytics_console",
                "right_server_racks",
                "right_tool_console",
            ],
        )
        self.assertEqual(write_store.call_count, 1)
        stored = json.loads(
            (self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            {
                stored["selections"][prop_id]["candidateId"]
                for prop_id in result["targetPropIds"]
            },
            {self.mt4_id},
        )
        self.assertEqual(
            result["globalMetatraderHub"]["platforms"]["mt4"]["configurationStatus"],
            "configured",
        )
        self.assertEqual(result["globalMetatraderHub"]["status"], "configured")
        self.assertEqual(result["globalMetatraderHub"]["selectedPlatform"], "mt4")

    def test_multiple_mt4_candidates_with_none_running_are_rejected(self) -> None:
        self._add_second_mt4_candidate()
        with mock.patch.object(
            self.bridge,
            "check_rate_limit",
            return_value=(True, 0),
        ), mock.patch.object(
            self.bridge,
            "_metatrader_process_locations",
            return_value={
                "supported": True,
                "mt4": [],
                "mt5": [],
                "pathAccessLimited": {"mt4": 0, "mt5": 0},
            },
        ), mock.patch.object(self.bridge, "create_mission") as create_mission:
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.select_global_metatrader_target("mt4", self.mt4_id)
        self.assertEqual(caught.exception.status, 409)
        create_mission.assert_not_called()

    def test_multiple_mt4_candidates_with_two_running_are_rejected(self) -> None:
        self._add_second_mt4_candidate(first_running=True, second_running=True)
        with mock.patch.object(
            self.bridge,
            "check_rate_limit",
            return_value=(True, 0),
        ), mock.patch.object(
            self.bridge,
            "_metatrader_process_locations",
            return_value={
                "supported": True,
                "mt4": [
                    self.bridge._canonical_metatrader_location(self.mt4_path),
                    self.bridge._canonical_metatrader_location(
                        self.root / "terminal-mt4-second"
                    ),
                ],
                "mt5": [],
                "pathAccessLimited": {"mt4": 0, "mt5": 0},
            },
        ), mock.patch.object(self.bridge, "create_mission") as create_mission:
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.select_global_metatrader_target("mt4", self.mt4_id)
        self.assertEqual(caught.exception.status, 409)
        create_mission.assert_not_called()

    def test_multiple_mt4_candidates_allow_only_the_unique_running_terminal(self) -> None:
        second_id = self._add_second_mt4_candidate(second_running=True)
        fresh_process_locations = {
            "supported": True,
            "mt4": [
                self.bridge._canonical_metatrader_location(
                    self.root / "terminal-mt4-second"
                )
            ],
            "mt5": [],
            "pathAccessLimited": {"mt4": 0, "mt5": 0},
        }
        with mock.patch.object(
            self.bridge,
            "_metatrader_process_locations",
            return_value=fresh_process_locations,
        ):
            with mock.patch.object(
                self.bridge,
                "check_rate_limit",
                return_value=(True, 0),
            ), mock.patch.object(self.bridge, "create_mission") as create_mission:
                with self.assertRaises(self.bridge.RequestError):
                    self.bridge.select_global_metatrader_target("mt4", self.mt4_id)
            create_mission.assert_not_called()
            with self._action_patches():
                result = self.bridge.select_global_metatrader_target("mt4", second_id)
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["globalMetatraderHub"]["platforms"]["mt4"]["selectedCandidate"]["candidateId"],
            second_id,
        )

    def test_fresh_process_probe_rejects_stale_running_candidate_without_store_write(self) -> None:
        existing_selections = {
            prop_id: {
                "candidateId": self.mt4_id,
                "selectedAt": "2026-09-07T00:00:00Z",
                "selectionRevision": 7,
            }
            for prop_id in self.bridge.GLOBAL_METATRADER_SELECTION_TARGETS["mt4"]
        }
        store_path = self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME
        store = json.loads(store_path.read_text(encoding="utf-8"))
        store["candidates"][self.mt4_id]["runningState"] = "platform_running_detected"
        store["selections"] = existing_selections
        self.bridge.write_json(store_path, store)
        before = store_path.read_bytes()

        fresh_process_locations = {
            "supported": True,
            "mt4": [
                self.bridge._canonical_metatrader_location(
                    self.root / "terminal-mt4-replacement-not-in-stale-scan"
                )
            ],
            "mt5": [],
            "pathAccessLimited": {"mt4": 0, "mt5": 0},
        }
        with self._action_patches(), mock.patch.object(
            self.bridge,
            "_metatrader_process_locations",
            return_value=fresh_process_locations,
        ) as process_probe, mock.patch.object(
            self.bridge,
            "_write_metatrader_target_store_unlocked",
        ) as write_store:
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.select_global_metatrader_target("mt4", self.mt4_id)

        self.assertEqual(caught.exception.status, 409)
        self.assertIn("ปิด MT4 อื่น", str(caught.exception))
        process_probe.assert_called_once_with()
        write_store.assert_not_called()
        self.assertEqual(store_path.read_bytes(), before)

    def test_registry_generation_change_between_probe_and_transaction_is_rejected(self) -> None:
        existing_selections = {
            prop_id: {
                "candidateId": self.mt4_id,
                "selectedAt": "2026-09-07T00:00:00Z",
                "selectionRevision": 7,
            }
            for prop_id in self.bridge.GLOBAL_METATRADER_SELECTION_TARGETS["mt4"]
        }
        self._write_store(existing_selections)
        second_id = self._add_second_mt4_candidate(first_running=True)
        store_path = self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME
        probe_started = threading.Event()
        permit_probe_return = threading.Event()
        outcome: dict[str, object] = {}

        def blocking_probe() -> dict:
            probe_started.set()
            if not permit_probe_return.wait(timeout=2):
                raise AssertionError("test did not release process probe")
            return {
                "supported": True,
                "mt4": [self.bridge._canonical_metatrader_location(self.mt4_path)],
                "mt5": [],
                "pathAccessLimited": {"mt4": 0, "mt5": 0},
            }

        def apply_selection() -> None:
            try:
                self.bridge.select_global_metatrader_target("mt4", self.mt4_id)
            except Exception as error:  # Captured for assertion in the test thread.
                outcome["error"] = error

        with self._action_patches(), mock.patch.object(
            self.bridge,
            "_metatrader_process_locations",
            side_effect=blocking_probe,
        ), mock.patch.object(
            self.bridge,
            "_write_metatrader_target_store_unlocked",
        ) as write_store:
            worker = threading.Thread(target=apply_selection)
            worker.start()
            self.assertTrue(probe_started.wait(timeout=2))
            changed_store = json.loads(store_path.read_text(encoding="utf-8"))
            changed_store["candidates"][self.mt4_id]["runningState"] = (
                "not_running_detected"
            )
            changed_store["candidates"][second_id]["runningState"] = (
                "platform_running_detected"
            )
            changed_store["updatedAt"] = "2026-09-07T00:00:01Z"
            self.bridge.write_json(store_path, changed_store)
            permit_probe_return.set()
            worker.join(timeout=2)

        self.assertFalse(worker.is_alive())
        error = outcome.get("error")
        self.assertIsInstance(error, self.bridge.RequestError)
        self.assertEqual(error.status, 409)
        write_store.assert_not_called()
        stored = json.loads(store_path.read_text(encoding="utf-8"))
        self.assertEqual(stored["selections"], existing_selections)
        self.assertEqual(
            stored["candidates"][second_id]["runningState"],
            "platform_running_detected",
        )

    def test_multi_install_apply_fails_closed_when_process_path_access_is_limited(self) -> None:
        self._add_second_mt4_candidate(first_running=True)
        with self._action_patches(), mock.patch.object(
            self.bridge,
            "_metatrader_process_locations",
            return_value={
                "supported": True,
                "mt4": [self.bridge._canonical_metatrader_location(self.mt4_path)],
                "mt5": [],
                "pathAccessLimited": {"mt4": 1, "mt5": 0},
            },
        ), mock.patch.object(
            self.bridge,
            "_write_metatrader_target_store_unlocked",
        ) as write_store:
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.select_global_metatrader_target("mt4", self.mt4_id)

        self.assertEqual(caught.exception.status, 409)
        write_store.assert_not_called()

    def test_multi_install_apply_fails_closed_when_process_probe_is_unsupported(self) -> None:
        self._add_second_mt4_candidate(first_running=True)
        with self._action_patches(), mock.patch.object(
            self.bridge,
            "_metatrader_process_locations",
            return_value={
                "supported": False,
                "mt4": [],
                "mt5": [],
                "pathAccessLimited": {"mt4": 0, "mt5": 0},
            },
        ), mock.patch.object(
            self.bridge,
            "_write_metatrader_target_store_unlocked",
        ) as write_store:
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.select_global_metatrader_target("mt4", self.mt4_id)

        self.assertEqual(caught.exception.status, 409)
        write_store.assert_not_called()

    def test_mt5_selection_targets_only_factory_and_lab(self) -> None:
        with self._action_patches():
            result = self.bridge.select_global_metatrader_target(
                "mt5",
                self.mt5_id,
            )

        self.assertEqual(
            result["targetPropIds"],
            ["right_server_racks", "right_tool_console"],
        )
        stored = json.loads(
            (self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME).read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn("left_analytics_console", stored["selections"])
        self.assertEqual(
            stored["selections"]["right_server_racks"]["candidateId"],
            self.mt5_id,
        )
        self.assertEqual(
            stored["selections"]["right_tool_console"]["candidateId"],
            self.mt5_id,
        )
        self.assertEqual(result["globalMetatraderHub"]["status"], "configured")
        self.assertEqual(result["globalMetatraderHub"]["selectedPlatform"], "mt5")
        self.assertEqual(
            result["globalMetatraderHub"]["platforms"]["mt4"]["configurationStatus"],
            "not_configured",
        )

    def test_legacy_selection_endpoint_alias_cannot_create_per_dashboard_drift(self) -> None:
        with self._action_patches():
            result = self.bridge.select_metatrader_target_compatibility_alias(
                "right_server_racks",
                self.mt4_id,
            )

        self.assertTrue(result["atomic"])
        self.assertEqual(result["compatibilityMode"], "central_atomic_alias")
        self.assertEqual(result["legacyRequestPropId"], "right_server_racks")
        self.assertEqual(result["selection"]["propId"], "right_server_racks")
        self.assertEqual(result["selection"]["status"], "configured")
        stored = json.loads(
            (self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            {
                stored["selections"][prop_id]["candidateId"]
                for prop_id in self.bridge.GLOBAL_METATRADER_SELECTION_TARGETS["mt4"]
            },
            {self.mt4_id},
        )

    def test_legacy_selection_alias_rejects_incompatible_consumer_before_write(self) -> None:
        store_path = self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME
        before = store_path.read_bytes()
        with mock.patch.object(self.bridge, "create_mission") as create_mission:
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.select_metatrader_target_compatibility_alias(
                    "left_analytics_console",
                    self.mt5_id,
                )
        self.assertEqual(caught.exception.status, 422)
        create_mission.assert_not_called()
        self.assertEqual(store_path.read_bytes(), before)

    def test_switching_from_mt4_to_mt5_keeps_global_status_configured(self) -> None:
        self._write_store({
            prop_id: {
                "candidateId": self.mt4_id,
                "selectedAt": "2026-09-07T00:00:00Z",
                "selectionRevision": 2,
            }
            for prop_id in self.bridge.GLOBAL_METATRADER_SELECTION_TARGETS["mt4"]
        })
        with self._action_patches():
            result = self.bridge.select_global_metatrader_target("mt5", self.mt5_id)

        hub = result["globalMetatraderHub"]
        self.assertEqual(hub["status"], "configured")
        self.assertEqual(hub["selectedPlatform"], "mt5")
        self.assertEqual(hub["platforms"]["mt5"]["configurationStatus"], "configured")
        self.assertEqual(hub["platforms"]["mt4"]["configurationStatus"], "partial")

    def test_write_failure_leaves_every_consumer_on_previous_selection(self) -> None:
        initial = {
            "left_analytics_console": {
                "candidateId": self.mt4_id,
                "selectedAt": "2026-09-07T00:00:00Z",
                "selectionRevision": 2,
            },
            "right_server_racks": {
                "candidateId": self.mt5_id,
                "selectedAt": "2026-09-07T00:00:00Z",
                "selectionRevision": 7,
            },
            "right_tool_console": {
                "candidateId": self.mt5_id,
                "selectedAt": "2026-09-07T00:00:00Z",
                "selectionRevision": 9,
            },
        }
        self._write_store(initial)
        store_path = self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME
        before = store_path.read_bytes()
        with self._action_patches(), mock.patch.object(
            self.bridge,
            "_write_metatrader_target_store_unlocked",
            side_effect=OSError("forced write failure"),
        ):
            with self.assertRaises(OSError):
                self.bridge.select_global_metatrader_target("mt4", self.mt4_id)
        self.assertEqual(store_path.read_bytes(), before)

    def test_readback_failure_rolls_back_every_consumer_before_reporting_failure(self) -> None:
        initial = {
            "right_server_racks": {
                "candidateId": self.mt5_id,
                "selectedAt": "2026-09-07T00:00:00Z",
                "selectionRevision": 7,
            }
        }
        self._write_store(initial)
        with self._action_patches(), mock.patch.object(
            self.bridge,
            "global_metatrader_hub_read_model",
            return_value={
                "status": "not_configured",
                "platforms": {
                    "mt4": {
                        "configurationStatus": "not_configured",
                        "selectedCandidate": None,
                    }
                },
            },
        ), mock.patch.object(
            self.bridge,
            "_fail_diagnostic_mission",
        ) as fail_mission:
            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge.select_global_metatrader_target("mt4", self.mt4_id)

        stored = json.loads(
            (self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(stored["selections"], initial)
        fail_mission.assert_not_called()

    def test_post_commit_observability_failures_do_not_reverse_or_fail_selection(self) -> None:
        failure_cases = (
            ("create_report", "report_write_failed"),
            ("_complete_diagnostic_mission", "mission_completion_failed"),
            ("append_audit", "audit_write_failed"),
        )
        for function_name, expected_warning in failure_cases:
            with self.subTest(function_name=function_name):
                self._write_store()
                with self._action_patches(), mock.patch.object(
                    self.bridge,
                    function_name,
                    side_effect=OSError(f"forced {function_name} failure"),
                ), mock.patch.object(
                    self.bridge,
                    "replace_mission",
                ) as replace_mission, mock.patch.object(
                    self.bridge,
                    "_fail_diagnostic_mission",
                ) as fail_mission:
                    result = self.bridge.select_global_metatrader_target(
                        "mt4",
                        self.mt4_id,
                    )

                self.assertTrue(result["ok"])
                self.assertTrue(result["atomic"])
                self.assertEqual(result["observabilityStatus"], "degraded")
                self.assertIn(expected_warning, result["observabilityWarnings"])
                fail_mission.assert_not_called()
                if function_name in {"create_report", "_complete_diagnostic_mission"}:
                    replace_mission.assert_called_once()
                stored = json.loads(
                    (
                        self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME
                    ).read_text(encoding="utf-8")
                )
                self.assertEqual(
                    {
                        stored["selections"][prop_id]["candidateId"]
                        for prop_id in self.bridge.GLOBAL_METATRADER_SELECTION_TARGETS["mt4"]
                    },
                    {self.mt4_id},
                )
                self.assertEqual(
                    result["globalMetatraderHub"]["platforms"]["mt4"]["configurationStatus"],
                    "configured",
                )

    def test_selection_mission_write_failure_does_not_block_atomic_commit(self) -> None:
        with self._action_patches(), mock.patch.object(
            self.bridge,
            "create_mission",
            side_effect=OSError("forced mission write failure"),
        ), mock.patch.object(
            self.bridge,
            "_write_metatrader_target_store_unlocked",
            wraps=self.bridge._write_metatrader_target_store_unlocked,
        ) as write_store:
            result = self.bridge.select_global_metatrader_target(
                "mt4",
                self.mt4_id,
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["atomic"])
        self.assertIsNone(result["missionId"])
        self.assertEqual(result["observabilityStatus"], "degraded")
        self.assertIn("mission_write_failed", result["observabilityWarnings"])
        self.assertNotIn("report_write_invalid", result["observabilityWarnings"])
        self.assertEqual(write_store.call_count, 1)
        stored = json.loads(
            (self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            {
                stored["selections"][prop_id]["candidateId"]
                for prop_id in self.bridge.GLOBAL_METATRADER_SELECTION_TARGETS["mt4"]
            },
            {self.mt4_id},
        )

    def test_discovery_observability_failure_keeps_the_sanitized_scan_successful(self) -> None:
        terminal_state = self.bridge.peek_metatrader_status()
        with self._action_patches(), mock.patch.object(
            self.bridge,
            "metatrader_status",
            return_value=terminal_state,
        ), mock.patch.object(
            self.bridge,
            "dashboard_connection_checklist",
            return_value={"overallStatus": "detected", "items": []},
        ), mock.patch.object(
            self.bridge,
            "create_report",
            side_effect=OSError("forced report failure"),
        ), mock.patch.object(
            self.bridge,
            "replace_mission",
        ), mock.patch.object(
            self.bridge,
            "_fail_diagnostic_mission",
        ) as fail_mission:
            result = self.bridge.run_global_metatrader_discovery()

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["observabilityStatus"], "degraded")
        self.assertIn("report_write_failed", result["observabilityWarnings"])
        self.assertIsNone(result["report"])
        self.assertIn("platforms", result["globalMetatraderHub"])
        fail_mission.assert_not_called()

    def test_discovery_mission_write_failure_does_not_block_safe_scan(self) -> None:
        terminal_state = self.bridge.peek_metatrader_status()
        with self._action_patches(), mock.patch.object(
            self.bridge,
            "create_mission",
            side_effect=OSError("forced mission write failure"),
        ), mock.patch.object(
            self.bridge,
            "metatrader_status",
            return_value=terminal_state,
        ) as scan, mock.patch.object(
            self.bridge,
            "dashboard_connection_checklist",
            return_value={"overallStatus": "detected", "items": []},
        ):
            result = self.bridge.run_global_metatrader_discovery()

        scan.assert_called_once_with(force=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "completed")
        self.assertIsNone(result["missionId"])
        self.assertEqual(result["observabilityStatus"], "degraded")
        self.assertIn("mission_write_failed", result["observabilityWarnings"])
        self.assertNotIn("report_write_invalid", result["observabilityWarnings"])
        self.assertIsInstance(result["report"], dict)
        self.assertIsNone(result["report"].get("linkedMissionId"))

    def test_global_discovery_uses_factory_capability_but_central_activity_identity(self) -> None:
        terminal_state = self.bridge.peek_metatrader_status()
        mission_payloads = []
        report_payloads = []

        def create_mission(payload, status="queued"):
            mission_payloads.append(payload)
            return {
                "id": "mission-global-discovery",
                "owner": payload["agentId"],
                "targetId": payload["targetId"],
                "status": status,
            }

        def create_report(payload):
            report_payloads.append(payload)
            return {"id": "report-global-discovery", **payload}

        with (
            mock.patch.object(self.bridge, "check_rate_limit", return_value=(True, 0)),
            mock.patch.object(
                self.bridge,
                "metatrader_status",
                return_value=terminal_state,
            ),
            mock.patch.object(
                self.bridge,
                "dashboard_connection_checklist",
                return_value={"overallStatus": "detected", "items": []},
            ) as checklist,
            mock.patch.object(
                self.bridge,
                "create_mission",
                side_effect=create_mission,
            ),
            mock.patch.object(
                self.bridge,
                "create_report",
                side_effect=create_report,
            ),
            mock.patch.object(
                self.bridge,
                "report_read_model_item",
                side_effect=lambda report: report,
            ),
            mock.patch.object(self.bridge, "_complete_diagnostic_mission"),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            result = self.bridge.run_global_metatrader_discovery()

        self.assertTrue(result["ok"])
        self.assertEqual(
            self.bridge.GLOBAL_METATRADER_DISCOVERY_PROP_ID,
            "mission_strategy_table",
        )
        self.assertEqual(
            self.bridge.GLOBAL_METATRADER_DISCOVERY_PROFILE_PROP_ID,
            "right_server_racks",
        )
        self.assertEqual(mission_payloads[0]["targetId"], "mission_strategy_table")
        self.assertEqual(report_payloads[0]["linkedPropId"], "mission_strategy_table")
        checklist.assert_called_once_with(
            "right_server_racks",
            terminals=terminal_state,
        )

        report_contract = json.loads(
            (
                PROJECT_ROOT
                / "contracts"
                / "reports"
                / "report-contract.json"
            ).read_text(encoding="utf-8")
        )
        self.assertIn(
            "mission_strategy_table",
            report_contract["report_targets"]["terminal_discovery_report"],
        )

    def test_concurrent_scan_and_global_apply_follow_one_lock_order_without_deadlock(self) -> None:
        sync_entered = threading.Event()
        allow_sync = threading.Event()
        peek_entered = threading.Event()
        results = {}
        errors = []
        original_sync = self.bridge._sync_metatrader_candidate_registry
        original_peek = self.bridge.peek_metatrader_status

        def paused_sync(discovered, running):
            sync_entered.set()
            if not allow_sync.wait(2):
                raise TimeoutError("test did not release candidate registry sync")
            return original_sync(discovered, running)

        def marked_peek():
            peek_entered.set()
            return original_peek()

        def scan_worker() -> None:
            try:
                results["scan"] = self.bridge.metatrader_status(
                    force=True,
                    roots=[self.mt4_path, self.mt5_path],
                    process_rows=[],
                )
            except Exception as error:  # pragma: no cover - surfaced below
                errors.append(error)

        def select_worker() -> None:
            try:
                results["select"] = self.bridge.select_global_metatrader_target(
                    "mt4",
                    self.mt4_id,
                )
            except Exception as error:  # pragma: no cover - surfaced below
                errors.append(error)

        with self._action_patches(), mock.patch.object(
            self.bridge,
            "_sync_metatrader_candidate_registry",
            side_effect=paused_sync,
        ), mock.patch.object(
            self.bridge,
            "peek_metatrader_status",
            side_effect=marked_peek,
        ):
            scan_thread = threading.Thread(target=scan_worker, daemon=True)
            select_thread = threading.Thread(target=select_worker, daemon=True)
            scan_thread.start()
            self.assertTrue(sync_entered.wait(1), "scan did not reach registry sync")
            select_thread.start()
            self.assertTrue(peek_entered.wait(1), "Apply did not request its cache snapshot")
            allow_sync.set()
            scan_thread.join(2)
            select_thread.join(2)

        self.assertFalse(scan_thread.is_alive(), "scan deadlocked with Apply")
        self.assertFalse(select_thread.is_alive(), "Apply deadlocked with scan")
        if errors:
            raise errors[0]
        self.assertTrue(results["select"]["ok"])
        self.assertEqual(
            results["select"]["globalMetatraderHub"]["platforms"]["mt4"]["configurationStatus"],
            "configured",
        )

    def test_idempotent_apply_does_not_rewrite_or_advance_revisions(self) -> None:
        selections = {
            prop_id: {
                "candidateId": self.mt4_id,
                "selectedAt": "2026-09-07T00:00:00Z",
                "selectionRevision": index,
            }
            for index, prop_id in enumerate(
                self.bridge.GLOBAL_METATRADER_SELECTION_TARGETS["mt4"],
                start=3,
            )
        }
        self._write_store(selections)
        with self._action_patches(), mock.patch.object(
            self.bridge,
            "_write_metatrader_target_store_unlocked",
        ) as write_store:
            result = self.bridge.select_global_metatrader_target("mt4", self.mt4_id)
        write_store.assert_not_called()
        self.assertEqual(result["changedTargetIds"], [])
        self.assertEqual(
            result["unchangedTargetIds"],
            list(self.bridge.GLOBAL_METATRADER_SELECTION_TARGETS["mt4"]),
        )
        self.assertEqual(
            result["selectionRevisions"],
            {prop_id: row["selectionRevision"] for prop_id, row in selections.items()},
        )

    def test_read_model_reports_legacy_per_prop_drift_as_partial(self) -> None:
        self._write_store({
            "left_analytics_console": {
                "candidateId": self.mt4_id,
                "selectedAt": "2026-09-07T00:00:00Z",
                "selectionRevision": 2,
            }
        })
        self.bridge.METATRADER_CACHE["payload"]["candidates"][0].update({
            "localPath": "C:\\private\\terminal",
            "installPath": "C:\\private\\install",
            "dataPath": "C:\\private\\data",
            "processId": 1234,
        })
        model = self.bridge.global_metatrader_hub_read_model()
        self.assertEqual(model["status"], "partial")
        self.assertEqual(
            model["platforms"]["mt4"]["configurationStatus"],
            "partial",
        )
        self.assertEqual(model["platforms"]["mt4"]["configuredTargetCount"], 1)
        self.assertTrue(model["safety"]["atomicFanOut"])
        self.assertFalse(model["safety"]["launchesTerminal"])
        self.assertFalse(model["safety"]["terminalPathsExposed"])
        self.assertFalse(model["safety"]["processIdsExposed"])
        self.assertFalse(model["safety"]["tradingDataAccessed"])
        allowed_candidate_fields = {
            "candidateId",
            "platform",
            "labelTh",
            "detected",
            "runningState",
        }
        for candidate in model["candidates"]:
            self.assertLessEqual(set(candidate), allowed_candidate_fields)
        for platform in model["platforms"].values():
            for candidate in platform["candidates"]:
                self.assertLessEqual(set(candidate), allowed_candidate_fields)
        observed_keys = set()

        def collect_keys(value) -> None:
            if isinstance(value, dict):
                observed_keys.update(value)
                for item in value.values():
                    collect_keys(item)
            elif isinstance(value, list):
                for item in value:
                    collect_keys(item)

        collect_keys(model)
        self.assertTrue({
            "localPath",
            "installPath",
            "dataPath",
            "processId",
        }.isdisjoint(observed_keys))

    def test_platform_mismatch_is_rejected_before_any_state_change(self) -> None:
        store_path = self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME
        before = store_path.read_bytes()
        with mock.patch.object(self.bridge, "create_mission") as create_mission:
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.select_global_metatrader_target("mt5", self.mt4_id)
        self.assertEqual(caught.exception.status, 422)
        create_mission.assert_not_called()
        self.assertEqual(store_path.read_bytes(), before)

    def test_running_mt5_outside_standard_roots_can_join_safe_candidate_scan(self) -> None:
        install = self.root / "custom-mt5-install"
        install.mkdir()
        (install / "terminal64.exe").write_bytes(b"")
        combined = self.bridge._include_verified_running_metatrader_candidate_locations(
            [],
            {
                "supported": True,
                "_processInstallPaths": {"mt4": [], "mt5": [str(install)]},
            },
        )
        self.assertEqual(len(combined), 1)
        self.assertEqual(combined[0]["platform"], "mt5")
        self.assertEqual(combined[0]["dataPath"], None)

    def test_custom_process_proven_terminal_survives_close_and_reboot_revalidation(self) -> None:
        custom_install = self.root / "custom-terminal-install"
        custom_install.mkdir()
        executable = custom_install / "terminal64.exe"
        executable.write_bytes(b"")
        empty_scan_root = self.root / "empty-standard-root"
        empty_scan_root.mkdir()
        running = self.bridge.discover_running_metatrader(
            process_locations={"mt4": [], "mt5": [str(custom_install)]}
        )
        stopped = self.bridge.discover_running_metatrader(
            process_locations={"mt4": [], "mt5": []}
        )

        with mock.patch.object(
            self.bridge,
            "discover_running_metatrader",
            side_effect=[running, stopped],
        ):
            first = self.bridge.metatrader_status(
                force=True,
                roots=[empty_scan_root],
                process_rows=[],
            )
            custom = next(
                item for item in first["candidates"] if item["platform"] == "mt5"
            )
            with self._action_patches(), mock.patch.object(
                self.bridge,
                "_metatrader_process_locations",
                return_value={
                    "supported": True,
                    "mt4": [],
                    "mt5": [
                        self.bridge._canonical_metatrader_location(custom_install)
                    ],
                    "pathAccessLimited": {"mt4": 0, "mt5": 0},
                },
            ):
                selected = self.bridge.select_global_metatrader_target(
                    "mt5",
                    custom["candidateId"],
                )
            self.bridge.METATRADER_CACHE.update(
                {"payload": None, "fetchedMonotonic": 0.0}
            )
            second = self.bridge.metatrader_status(
                force=True,
                roots=[empty_scan_root],
                process_rows=[],
            )

        self.assertEqual(second["candidateCount"], 1)
        self.assertEqual(second["candidates"][0]["candidateId"], custom["candidateId"])
        self.assertEqual(second["candidates"][0]["runningState"], "not_running_detected")
        hub = self.bridge.global_metatrader_hub_read_model(second)
        self.assertEqual(hub["platforms"]["mt5"]["configurationStatus"], "configured")
        self.assertEqual(
            hub["platforms"]["mt5"]["selectedCandidate"]["candidateId"],
            custom["candidateId"],
        )
        observed_keys = set()

        def collect_keys(value) -> None:
            if isinstance(value, dict):
                observed_keys.update(value)
                for item in value.values():
                    collect_keys(item)
            elif isinstance(value, list):
                for item in value:
                    collect_keys(item)

        collect_keys({"scan": second, "selection": selected, "hub": hub})
        self.assertTrue(
            {"localPath", "installPath", "dataPath", "processId", "pid"}.isdisjoint(
                observed_keys
            )
        )

    def test_custom_persisted_terminal_is_rejected_when_executable_or_identity_is_invalid(self) -> None:
        custom_install = self.root / "invalidated-custom-terminal"
        custom_install.mkdir()
        executable = custom_install / "terminal64.exe"
        executable.write_bytes(b"")
        canonical = self.bridge._canonical_metatrader_location(custom_install)
        record = self._candidate_record("mt5", self.mt5_id, custom_install, 1)
        record.update({
            "localPath": canonical,
            "installPath": canonical,
            "dataPath": None,
        })
        self.bridge.write_json(
            self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME,
            {
                "schemaVersion": self.bridge.METATRADER_TARGET_STORE_SCHEMA_VERSION,
                "candidates": {self.mt5_id: record},
                "selections": {},
                "updatedAt": "2026-09-07T00:00:00Z",
            },
        )
        self.assertEqual(
            len(self.bridge._include_verified_persisted_metatrader_install_roots([])),
            1,
        )

        executable.unlink()
        self.assertEqual(
            self.bridge._include_verified_persisted_metatrader_install_roots([]),
            [],
        )
        executable.write_bytes(b"")
        record["identityKey"] = "0" * 64
        self.bridge.write_json(
            self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME,
            {
                "schemaVersion": self.bridge.METATRADER_TARGET_STORE_SCHEMA_VERSION,
                "candidates": {self.mt5_id: record},
                "selections": {},
                "updatedAt": "2026-09-07T00:00:00Z",
            },
        )
        self.assertEqual(
            self.bridge._include_verified_persisted_metatrader_install_roots([]),
            [],
        )

    def test_selected_persisted_terminal_survives_more_than_recovery_limit_stale_candidates(self) -> None:
        custom_install = self.root / "selected-custom-terminal"
        custom_install.mkdir()
        (custom_install / "terminal64.exe").write_bytes(b"")
        selected_path = self.bridge._canonical_metatrader_location(custom_install)
        selected_record = self._candidate_record(
            "mt5",
            self.mt5_id,
            custom_install,
            1,
        )
        selected_record.update({
            "localPath": selected_path,
            "installPath": selected_path,
            "dataPath": None,
        })
        candidates = {}
        stale_count = self.bridge.METATRADER_PERSISTED_RECOVERY_RECENT_LIMIT + 76
        for index in range(stale_count):
            candidate_id = f"mtc-stale-{index:04d}"
            stale_path = self.bridge._canonical_metatrader_location(
                self.root / f"removed-terminal-{index:04d}"
            )
            candidates[candidate_id] = {
                "candidateId": candidate_id,
                "identityKey": self.bridge._metatrader_identity_key(
                    "mt5",
                    stale_path,
                ),
                "platform": "mt5",
                "ordinal": index + 2,
                "localPath": stale_path,
                "installPath": stale_path,
                "dataPath": None,
                "firstSeenAt": "2026-01-01T00:00:00Z",
                "lastSeenAt": "2026-01-01T00:00:00Z",
                "available": False,
                "runningState": "not_running_detected",
            }
        # Deliberately insert the selected record after more than 1,024 stale
        # entries to catch arbitrary insertion-order recovery limits.
        candidates[self.mt5_id] = selected_record
        self.bridge.write_json(
            self.runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME,
            {
                "schemaVersion": self.bridge.METATRADER_TARGET_STORE_SCHEMA_VERSION,
                "candidates": candidates,
                "selections": {
                    "right_server_racks": {
                        "candidateId": self.mt5_id,
                        "selectedAt": "2026-09-07T00:00:00Z",
                        "selectionRevision": 3,
                    },
                },
                "updatedAt": "2026-09-07T00:00:00Z",
            },
        )

        recovered = self.bridge._include_verified_persisted_metatrader_install_roots([])
        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0]["localPath"], selected_path)
        competing_discovered = [
            {
                "platform": "mt5",
                "localPath": self.bridge._canonical_metatrader_location(
                    self.root / f"0000-competing-terminal-{index:04d}"
                ),
                "installPath": None,
                "dataPath": None,
            }
            for index in range(
                self.bridge.METATRADER_PERSISTED_RECOVERY_RECENT_LIMIT
            )
        ]
        self.bridge._sync_metatrader_candidate_registry(
            [*competing_discovered, *recovered],
            {
                "supported": True,
                "_processInstallPaths": {"mt4": [], "mt5": []},
            },
        )
        with self.bridge.METATRADER_TARGETS_LOCK:
            stored = self.bridge._load_metatrader_target_store_unlocked()
        self.assertIn(self.mt5_id, stored["candidates"])
        self.assertTrue(stored["candidates"][self.mt5_id]["available"])
        self.assertEqual(
            stored["selections"]["right_server_racks"]["candidateId"],
            self.mt5_id,
        )
        self.assertLessEqual(
            len(stored["candidates"]),
            self.bridge.METATRADER_STALE_CANDIDATE_RETENTION_LIMIT
            + self.bridge.METATRADER_PERSISTED_RECOVERY_RECENT_LIMIT,
        )

    def test_bounded_children_stops_advancing_after_the_limit(self) -> None:
        class CountingPath:
            def __init__(self) -> None:
                self.advanced = 0

            def iterdir(self):
                for index in range(10_000):
                    self.advanced += 1
                    yield Path(f"child-{index}")

        path = CountingPath()
        children = self.bridge._bounded_children(path, limit=7)
        self.assertEqual(len(children), 7)
        self.assertEqual(path.advanced, 7)

    def test_selected_candidate_context_migrates_and_returns_one_matching_generation(self) -> None:
        self._write_store({
            "right_server_racks": {
                "candidateId": self.mt4_id,
                "selectedAt": "2026-09-07T00:00:00Z",
            }
        })
        original_write = self.bridge._write_metatrader_target_store_unlocked
        with mock.patch.object(
            self.bridge,
            "_write_metatrader_target_store_unlocked",
            wraps=original_write,
        ) as write_store:
            first = self.bridge._selected_metatrader_candidate_context(
                "right_server_racks"
            )
            second = self.bridge._selected_metatrader_candidate_context(
                "right_server_racks"
            )
            gate = self.bridge._ea_factory_terminal_gate("mt4")

        self.assertEqual(write_store.call_count, 1)
        self.assertEqual(first, second)
        self.assertEqual(first["record"]["candidateId"], self.mt4_id)
        self.assertEqual(first["token"], {
            "candidateId": self.mt4_id,
            "selectionRevision": 1,
        })
        self.assertEqual(gate["candidateId"], self.mt4_id)
        self.assertEqual(gate["selectionRevision"], 1)

    def test_gateway_status_fails_closed_if_selection_changes_before_reconciliation(self) -> None:
        record_a = self._candidate_record("mt4", self.mt4_id, self.mt4_path, 1)
        context_a = {
            "record": record_a,
            "token": {"candidateId": self.mt4_id, "selectionRevision": 1},
        }
        context_b = {
            "record": self._candidate_record("mt4", "mtc-" + ("z" * 26), self.mt4_path, 2),
            "token": {"candidateId": "mtc-" + ("z" * 26), "selectionRevision": 2},
        }
        with mock.patch.object(
            self.bridge,
            "_selected_metatrader_candidate_context",
            side_effect=[context_a, context_b],
        ), mock.patch.object(
            self.bridge,
            "_mt4_trade_gateway_instance",
        ) as gateway:
            status = self.bridge.mt4_trade_gateway_status_read_model()

        gateway.assert_not_called()
        self.assertFalse(status["connected"])
        self.assertEqual(status["status"], "selection_changed")
        self.assertEqual(
            status["reasonCode"],
            "terminal_selection_changed_during_status_read",
        )

    def test_connection_contract_declares_backend_atomic_global_endpoints(self) -> None:
        contract = json.loads(CONNECTION_CONTRACT_PATH.read_text(encoding="utf-8"))
        hub = contract["terminalTargetSelection"]["centralHeaderControl"]
        self.assertEqual(
            hub["statusEndpoint"],
            "GET /api/integrations/metatrader/global",
        )
        self.assertEqual(
            hub["discoveryEndpoint"],
            "POST /api/integrations/metatrader/global/discover",
        )
        self.assertEqual(
            hub["selectionEndpoint"],
            "POST /api/integrations/metatrader/global/select",
        )
        self.assertEqual(hub["selectionRequestFields"], ["platform", "candidateId"])
        self.assertTrue(hub["backendAtomicFanOut"])
        self.assertTrue(hub["frontendFanOutForbidden"])
        self.assertTrue(hub["discoveryPostScanObservabilityBestEffort"])
        self.assertTrue(hub["frontendReconcileIndeterminateDiscoveryResponse"])
        self.assertFalse(hub["frontendAutomaticDiscoveryRetryAllowed"])
        self.assertTrue(hub["postCommitObservabilityBestEffort"])
        self.assertTrue(hub["frontendReconcileIndeterminateResponse"])
        self.assertFalse(hub["frontendAutomaticMutationRetryAllowed"])
        self.assertEqual(hub["interactiveSelectionSurface"], "central_header_only")
        self.assertFalse(hub["deviceDashboardSelectionControlsAllowed"])
        self.assertTrue(hub["deviceDashboardSelectionStatusReadOnly"])
        self.assertEqual(
            hub["legacyPerDashboardEndpointBehavior"],
            "backend_alias_to_platform_atomic_fanout",
        )
        self.assertFalse(hub["legacyPerDashboardEndpointMayWriteSingleConsumer"])

        bridge_contract = json.loads(BRIDGE_CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(bridge_contract["version"], "bridge-contract-v020")
        endpoints = bridge_contract["endpoints"]
        for endpoint in (
            "GET /api/integrations/metatrader/global",
            "POST /api/integrations/metatrader/global/discover",
            "POST /api/integrations/metatrader/global/select",
        ):
            self.assertIn(endpoint, endpoints)
        self.assertIn(
            "same atomic all-compatible-consumer transaction",
            endpoints["POST /api/integrations/metatrader/select"],
        )


if __name__ == "__main__":
    unittest.main()
