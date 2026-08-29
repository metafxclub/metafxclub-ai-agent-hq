from __future__ import annotations

import http.client
import importlib.util
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
START_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "start-local-bridge.ps1"


def load_bridge(name: str):
    spec = importlib.util.spec_from_file_location(name, BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BridgeProcessLifecycleTests(unittest.TestCase):
    def test_restart_loads_only_allowlisted_google_client_config_from_user_scope(self) -> None:
        script = START_SCRIPT_PATH.read_text(encoding="utf-8-sig")
        helper_start = script.index("function Start-BridgeChildProcess")
        helper_end = script.index("function Get-ComparablePath", helper_start)
        helper = script[helper_start:helper_end]

        self.assertIn("METAFX_GOOGLE_OAUTH_CLIENT_ID", helper)
        self.assertIn("METAFX_GOOGLE_OAUTH_CLIENT_SECRET", helper)
        self.assertIn("[EnvironmentVariableTarget]::User", helper)
        self.assertIn("[EnvironmentVariableTarget]::Process", helper)
        self.assertIn("[string]::IsNullOrWhiteSpace($processValue)", helper)
        self.assertIn("finally", helper)
        self.assertNotIn("Write-Host", helper)
        self.assertNotIn("Write-AuditEvent", helper)
        self.assertIn("$startedProcess = Start-BridgeChildProcess", script)

    def test_base_interpreter_preserves_the_pinned_project_venv(self) -> None:
        script = START_SCRIPT_PATH.read_text(encoding="utf-8-sig")
        helper_start = script.index("function Start-BridgeChildProcess")
        helper_end = script.index("function Get-ComparablePath", helper_start)
        helper = script[helper_start:helper_end]

        self.assertIn("__PYVENV_LAUNCHER__", helper)
        self.assertIn("$VenvLauncherPath", helper)
        self.assertIn("$originalVenvLauncher", helper)
        self.assertIn("[EnvironmentVariableTarget]::Process", helper)
        self.assertIn("$script:projectVenvLauncher", script)
        self.assertIn("-VenvLauncherPath $projectVenvLauncher", script)

    def test_os_guard_rejects_second_bridge_for_same_checkout(self) -> None:
        first = load_bridge("metafx_process_guard_first")
        second = load_bridge("metafx_process_guard_second")
        # A real bridge may be serving this checkout while the suite runs.
        # Isolate the mutex namespace while keeping both test modules on the
        # same synthetic checkout identity.
        isolated_digest = first.secrets.token_hex(16)
        first.BRIDGE_PROCESS_GUARD_STATE["nameDigest"] = isolated_digest
        second.BRIDGE_PROCESS_GUARD_STATE["nameDigest"] = isolated_digest
        try:
            self.assertTrue(first.acquire_bridge_process_guard())
            self.assertFalse(second.acquire_bridge_process_guard())
        finally:
            second.release_bridge_process_guard()
            first.release_bridge_process_guard()

    def test_control_file_contains_backend_only_lifecycle_identity(self) -> None:
        bridge = load_bridge("metafx_process_control_file")
        self.assertFalse(
            bridge.BridgeHandler.static_path_allowed(
                None,
                "/data/runtime/bridge-control.json",
            )
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            control_path = Path(temp_dir) / "bridge-control.json"
            with mock.patch.object(bridge, "BRIDGE_CONTROL_PATH", control_path):
                bridge.write_bridge_control_file("127.0.0.1", 4191)
                payload = json.loads(control_path.read_text(encoding="utf-8"))
                self.assertEqual(payload["schemaVersion"], "1.0.0")
                self.assertEqual(payload["projectRoot"], str(bridge.PROJECT_ROOT))
                self.assertEqual(payload["processId"], bridge.os.getpid())
                self.assertEqual(payload["port"], 4191)
                self.assertEqual(payload["shutdownToken"], bridge.BRIDGE_SHUTDOWN_TOKEN)
                bridge.remove_bridge_control_file()
                self.assertFalse(control_path.exists())

    def test_shutdown_endpoint_rejects_wrong_token_then_stops_gracefully(self) -> None:
        bridge = load_bridge("metafx_graceful_shutdown_endpoint")
        server = bridge.BridgeHTTPServer(("127.0.0.1", 0), bridge.BridgeHandler)
        port = int(server.server_port)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with mock.patch.object(bridge, "append_audit"):
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
                connection.request(
                    "POST",
                    "/api/admin/shutdown",
                    body="{}",
                    headers={
                        "Content-Type": "application/json",
                        "X-Metafx-Bridge-Control": "wrong-token",
                    },
                )
                rejected = connection.getresponse()
                rejected.read()
                connection.close()
                self.assertEqual(rejected.status, 403)
                self.assertTrue(thread.is_alive())

                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
                connection.request(
                    "POST",
                    "/api/admin/shutdown",
                    body="{}",
                    headers={
                        "Content-Type": "application/json",
                        "X-Metafx-Bridge-Control": bridge.BRIDGE_SHUTDOWN_TOKEN,
                    },
                )
                accepted = connection.getresponse()
                payload = json.loads(accepted.read().decode("utf-8"))
                connection.close()
                self.assertEqual(accepted.status, 202)
                self.assertEqual(payload["kind"], "graceful_shutdown_accepted")
                thread.join(timeout=3)
                self.assertFalse(thread.is_alive())
        finally:
            server.server_close()


if __name__ == "__main__":
    unittest.main()
