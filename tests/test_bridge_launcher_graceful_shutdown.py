from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_PATH = PROJECT_ROOT / "scripts" / "start-local-bridge.ps1"


class BridgeLauncherGracefulShutdownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.launcher = LAUNCHER_PATH.read_text(encoding="utf-8-sig")

    def _function_body(self, name: str, next_name: str) -> str:
        start = self.launcher.index(f"function {name}")
        end = self.launcher.index(f"function {next_name}", start)
        return self.launcher[start:end]

    def test_control_record_is_bound_to_exact_project_process_and_port(self) -> None:
        block = self._function_body(
            "Get-BridgeControlRecord",
            "Wait-ForBridgeProcessExit",
        )
        self.assertIn('$controlPath = Join-Path $runtimePath "bridge-control.json"', self.launcher)
        self.assertIn('[string]$control.schemaVersion -cne "1.0.0"', block)
        self.assertIn("$control.projectRoot", block)
        self.assertIn("[int]$control.processId -ne $ProcessId", block)
        self.assertIn("[int]$control.port -ne $Port", block)
        self.assertIn("$control.shutdownToken", block)

    def test_authenticated_loopback_post_waits_before_force_fallback(self) -> None:
        request = self._function_body(
            "Request-BridgeGracefulShutdown",
            "Stop-VerifiedProcess",
        )
        stop = self._function_body("Stop-VerifiedProcess", "Start-Bridge")
        self.assertIn(
            '$shutdownUrl = "http://127.0.0.1:$Port/api/admin/shutdown"',
            request,
        )
        self.assertIn('"X-Metafx-Bridge-Control"', request)
        self.assertIn("Invoke-WebRequest", request)
        self.assertIn("Wait-ForBridgeProcessExit", request)
        self.assertLess(
            stop.index("Request-BridgeGracefulShutdown"),
            stop.index("Stop-Process -Id $ProcessId -Force"),
        )
        self.assertIn('Outcome "graceful_fallback_force"', stop)

    def test_stop_restart_and_watchdog_replacement_request_graceful_shutdown(self) -> None:
        self.assertIn(
            "Stop-VerifiedProcess -ProcessId $existingId -GracefulFirst",
            self.launcher,
        )
        self.assertIn(
            "Stop-VerifiedProcess -ProcessId $processId -GracefulFirst",
            self.launcher,
        )
        restart = self._function_body("Stop-Bridge", "Get-BridgeStatus")
        self.assertIn("-GracefulFirst", restart)
        self.assertIsNone(
            re.search(
                r"Write-(?:Host|Output|Verbose|Debug)[^\r\n]*ShutdownToken",
                self.launcher,
                flags=re.IGNORECASE,
            )
        )


if __name__ == "__main__":
    unittest.main()
