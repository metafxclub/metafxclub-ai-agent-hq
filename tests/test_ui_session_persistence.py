from __future__ import annotations

import importlib.util
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


def load_bridge(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load bridge module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UiSessionPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bridge = load_bridge(
            f"metafx_bridge_ui_session_{id(self)}_{threading.get_ident()}"
        )
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.runtime = self.root / "runtime"
        self.bridge.RUNTIME_DIR = self.runtime
        self.bridge.RUNTIME_REPORTS_DIR = self.runtime / "reports"
        self.bridge.UI_SESSION_PATH = self.runtime / "ui-session.json"
        self.bridge.UI_SESSION_REPLACE_INITIAL_DELAY_SECONDS = 0.0

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def session(version: int) -> dict:
        return {
            "modal": {"signalDashboardVersion": version},
            "selectedAgentId": f"agent-{version}",
        }

    def read_store(self) -> dict:
        return json.loads(self.bridge.UI_SESSION_PATH.read_text(encoding="utf-8"))

    def test_concurrent_writes_are_serialized_and_keep_highest_version(self) -> None:
        original_replace = self.bridge._bounded_atomic_replace
        active = 0
        maximum_active = 0
        counter_lock = threading.Lock()

        def observed_replace(*args, **kwargs):
            nonlocal active, maximum_active
            with counter_lock:
                active += 1
                maximum_active = max(maximum_active, active)
            try:
                time.sleep(0.005)
                return original_replace(*args, **kwargs)
            finally:
                with counter_lock:
                    active -= 1

        with mock.patch.object(
            self.bridge,
            "_bounded_atomic_replace",
            side_effect=observed_replace,
        ):
            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(
                    lambda version: self.bridge.store_ui_session(self.session(version)),
                    range(1, 33),
                ))

        self.assertEqual(maximum_active, 1)
        self.assertEqual(
            self.read_store()["session"]["modal"]["signalDashboardVersion"],
            32,
        )
        self.assertTrue(all(result["ok"] for result in results))
        backup_version = json.loads(
            self.bridge.UI_SESSION_PATH.with_name("ui-session.json.bak").read_text(
                encoding="utf-8"
            )
        )["session"]["modal"]["signalDashboardVersion"]
        # Thread scheduling is intentionally nondeterministic. The backup must
        # be valid last-good state older than the final highest version; it is
        # not required to be the numerically adjacent submission.
        self.assertGreaterEqual(backup_version, 1)
        self.assertLess(backup_version, 32)

    def test_temporary_permission_error_retries_and_preserves_backup(self) -> None:
        self.bridge.store_ui_session(self.session(1))
        original_replace = self.bridge.os.replace
        attempts = 0

        def transient_replace(source, destination):
            nonlocal attempts
            if Path(destination) == self.bridge.UI_SESSION_PATH:
                attempts += 1
                if attempts < 3:
                    raise PermissionError(5, "temporary access denied")
            return original_replace(source, destination)

        with mock.patch.object(self.bridge.os, "replace", side_effect=transient_replace):
            result = self.bridge.store_ui_session(self.session(2))

        self.assertTrue(result["ok"])
        self.assertEqual(attempts, 3)
        self.assertEqual(
            self.read_store()["session"]["modal"]["signalDashboardVersion"],
            2,
        )
        backup = json.loads(
            self.bridge.UI_SESSION_PATH.with_name("ui-session.json.bak").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(backup["session"]["modal"]["signalDashboardVersion"], 1)

    def test_permanent_permission_error_is_bounded_and_last_good_stays_valid(self) -> None:
        self.bridge.store_ui_session(self.session(7))
        original = self.read_store()
        attempts = 0

        def denied_replace(source, destination):
            nonlocal attempts
            if Path(destination) == self.bridge.UI_SESSION_PATH:
                attempts += 1
                raise PermissionError(5, "persistent access denied")
            return self.bridge.os_replace_original(source, destination)

        self.bridge.os_replace_original = self.bridge.os.replace
        with mock.patch.object(self.bridge.os, "replace", side_effect=denied_replace):
            with self.assertRaises(PermissionError):
                self.bridge.store_ui_session(self.session(8))

        self.assertEqual(attempts, self.bridge.UI_SESSION_REPLACE_MAX_ATTEMPTS)
        self.assertEqual(self.read_store(), original)
        backup = json.loads(
            self.bridge.UI_SESSION_PATH.with_name("ui-session.json.bak").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(backup, original)
        self.assertEqual(list(self.runtime.glob(".ui-session.json.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
