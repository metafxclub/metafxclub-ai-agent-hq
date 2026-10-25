"""Exercise maintenance stop logic using mock PowerShell functions only."""
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SHELL = shutil.which("pwsh") or shutil.which("powershell")


@unittest.skipUnless(SHELL, "PowerShell is required")
class GracefulOnlyMaintenanceTests(unittest.TestCase):
    def run_case(self, mode, *, graceful_only=True, first=True):
        source = (ROOT / "scripts/start-local-bridge.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("[switch]$GracefulOnly", source)
        start = source.index("function Stop-VerifiedProcess {")
        stop = source.index("function Start-Bridge {", start)
        body = source[start:stop]
        script = r'''
$ErrorActionPreference = 'Stop'
$GracefulOnly = __ONLY__
$bridgePort = 4186
$forceShutdownWaitSeconds = 1
$script:forced = 0
$script:recordReads = 0
$script:requested = 0
function Get-ProcessRecord {
    param($ProcessId)
    $script:recordReads++
    if ('__MODE__' -eq 'late_exit' -and $script:recordReads -gt 1) { return $null }
    return @{ ProcessId = 12345 }
}
function Test-BridgeProcess { param($ProcessRecord,$ExpectedPort) return ('__MODE__' -ne 'wrong_identity') }
function Request-BridgeGracefulShutdown {
    param($ProcessId,$Port)
    $script:requested++
    return ('__MODE__' -eq 'success')
}
function Remove-MatchingBridgeControlFile { param($ProcessId,$Port) }
function Write-AuditEvent { param($Operation,$Outcome,$ProcessId,$Message) }
function Wait-ForBridgeProcessExit { param($ProcessId,$TimeoutSeconds) return $true }
function Stop-Process { param($Id,[switch]$Force,$ErrorAction) $script:forced++ }
__BODY__
$failed = $false
$stopped = $false
try { $stopped = Stop-VerifiedProcess -ProcessId 12345 -GracefulFirst:__FIRST__ } catch { $failed = $true }
@{ failed=$failed; stopped=$stopped; forced=$script:forced; requested=$script:requested } | ConvertTo-Json -Compress
'''
        script = script.replace("__MODE__", mode).replace("__ONLY__", "$true" if graceful_only else "$false")
        script = script.replace("__FIRST__", "$true" if first else "$false").replace("__BODY__", body)
        encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
        result = subprocess.run([SHELL, "-NoLogo", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                                capture_output=True, text=True, timeout=25,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout.strip())

    def test_timeout_does_not_force_stop(self):
        self.assertEqual(self.run_case("timeout"), {"failed": True, "stopped": False, "forced": 0, "requested": 1})

    def test_success_stops_without_force(self):
        self.assertEqual(self.run_case("success"), {"failed": False, "stopped": True, "forced": 0, "requested": 1})

    def test_late_clean_exit_is_accepted(self):
        self.assertEqual(self.run_case("late_exit"), {"failed": False, "stopped": True, "forced": 0, "requested": 1})

    def test_startup_cleanup_is_not_forced(self):
        self.assertEqual(self.run_case("timeout", first=False), {"failed": True, "stopped": False, "forced": 0, "requested": 0})

    def test_wrong_process_identity_is_untouched(self):
        self.assertEqual(self.run_case("wrong_identity"), {"failed": True, "stopped": False, "forced": 0, "requested": 0})

    def test_existing_force_fallback_is_unchanged_without_opt_in(self):
        self.assertEqual(self.run_case("timeout", graceful_only=False), {"failed": False, "stopped": True, "forced": 1, "requested": 1})


if __name__ == "__main__":
    unittest.main()
