from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("isolated_upgrade_guard", ROOT / "installer" / "upgrade_guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class OfflineUpgradeStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "hq"
        self.common = Path(self.temp.name) / "common"
        self.runtime = self.root / "data" / "runtime"
        self.runtime.mkdir(parents=True)

    def write(self, relative, value):
        path = self.runtime / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def check(self):
        guard.check_upgrade_state(self.root, self.common, now=1000)

    def blocked(self, reason):
        with self.assertRaisesRegex(guard.UpgradeBlocked, reason):
            self.check()

    def channel(self):
        self.write("metatrader-targets.json", {
            "candidates": {"mtc-test": {"platform": "mt5"}},
            "selections": {"council": {"candidateId": "mtc-test"}},
            "platformSelections": {"mt5": {"candidateId": "mtc-test"}},
        })
        folder = self.common / "MetafxHQ" / "mtc-test"
        (folder / "trade-gateway").mkdir(parents=True)
        return folder

    def test_fresh_install_has_no_runtime_to_rewrite(self):
        self.check()
        self.assertEqual([], list(self.runtime.iterdir()))

    def test_enabled_but_quiescent_settings_and_daily_ledger_are_preserved(self):
        self.write("ai-trade-council-automation.json", {"config": {"enabled": True}, "state": {"status": "idle", "pendingQueue": []}})
        self.write("sentiment-news-ai/state.json", {"status": "ready", "attempted": True})
        self.write("sentiment-news-ai/days/2026-10-27.json", {"attempted": True, "status": "ready"})
        self.write("private-config-fixture.json", {"myfxbook": "UNCHANGED", "mt5": "SAVED"})
        before = {p: p.read_bytes() for p in self.runtime.rglob("*.json")}
        self.check()
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_mission_shapes_allow_terminal_history_but_block_active_or_unknown(self):
        for wrapped in (False, True):
            for status in ("completed", "failed", "blocked", "archived", "cancelled"):
                rows = [{"status": status}]
                self.write("missions.json", {"missions": rows} if wrapped else rows)
                self.check()
            for status in ("queued", "running", "waiting_approval", "waiting_quota", "unexpected"):
                rows = [{"status": status}]
                self.write("missions.json", {"missions": rows} if wrapped else rows)
                self.blocked("active_mission")

    def test_council_pending_capture_or_queue_is_not_discarded(self):
        for state in ({"pendingQueue": [{"snapshot": "retained"}]}, {"pendingClosedBarTime": 123}, {"status": "running"}):
            path = self.write("ai-trade-council-automation.json", {"config": {"enabled": False}, "state": state})
            before = path.read_bytes()
            self.blocked("council_pending")
            self.assertEqual(before, path.read_bytes())

    def test_active_agent_turn_and_stale_pointer_block(self):
        for thread in ({"activeTurnId": "t", "turns": []}, {"activeTurnId": None, "turns": [{"status": "running"}]}):
            self.write("full-agent-runtime/full-agent-runtime-v1.json", {"threads": {"x": thread}})
            self.blocked("active_agent_turn")
        self.write("full-agent-runtime/full-agent-runtime-v1.json", {"threads": {"x": {"activeTurnId": None, "turns": [{"status": "cancelled"}]}}})
        self.check()

    def test_daily_news_reservation_blocks_without_retrying_it(self):
        path = self.write("sentiment-news-ai/state.json", {"status": "running", "attempted": True})
        before = path.read_bytes()
        self.blocked("daily_news_analysis_active")
        self.assertEqual(before, path.read_bytes())

    def test_gateway_outstanding_or_execution_unknown_blocks(self):
        for state in (
            {"activeCommandId": "c", "commands": {}},
            {"activeCommandId": None, "commands": {"c": {"outstanding": True, "status": "published"}}},
            {"activeCommandId": None, "commands": {"c": {"outstanding": False, "status": "quarantined_execution_unknown"}}},
        ):
            self.write("mt4-trade-gateway/mt4-trade-gateway-ledger.json", state)
            self.blocked("trade_command")

    def test_settled_gateway_history_is_preserved(self):
        self.write("mt4-trade-gateway/mt4-trade-gateway-ledger.json", {"activeCommandId": None, "commands": {"c": {"outstanding": False, "status": "acknowledged"}}})
        self.check()

    def test_fresh_ea_status_and_future_clock_fail_closed(self):
        folder = self.channel()
        for observed in (999, 1031):
            (folder / "trade-gateway/status.json").write_text(json.dumps({"channelId": "mtc-test", "observedAt": observed, "currentManagedPositions": 0}))
            self.blocked("ea_connection_active")

    def test_stale_ea_status_with_open_positions_still_blocks(self):
        folder = self.channel()
        (folder / "trade-gateway/status.json").write_text(json.dumps({"channelId": "mtc-test", "observedAt": 1, "currentManagedPositions": 1}))
        self.blocked("open_positions")

    def test_unmanaged_open_snapshot_position_also_blocks(self):
        folder = self.channel()
        (folder / "snapshot.json").write_text(json.dumps({"channelId": "mtc-test", "positionsSummary": {"count": 1}}))
        self.blocked("open_positions")

    def test_prior_owned_channel_is_checked_even_without_current_selection(self):
        folder = self.channel()
        (self.runtime / "metatrader-targets.json").unlink()
        (folder / "trade-gateway/status.json").write_text(json.dumps({"channelId": "mtc-test", "observedAt": 999, "currentManagedPositions": 0}))
        self.write("ai-trade-council-automation.json", {"config": {"enabled": True}, "state": {"candidateId": "mtc-test"}})
        self.blocked("ea_connection_active")
        (self.runtime / "ai-trade-council-automation.json").unlink()
        self.write("mt4-trade-gateway/mt4-trade-gateway-ledger.json", {"activeCommandId": None, "commands": {"c": {"outstanding": False, "status": "acknowledged", "command": {"channelId": "mtc-test"}}}})
        self.blocked("ea_connection_active")

    def test_stale_flat_status_and_empty_unselected_targets_are_allowed(self):
        folder = self.channel()
        (folder / "trade-gateway/status.json").write_text(json.dumps({"channelId": "mtc-test", "observedAt": 1, "currentManagedPositions": 0}))
        self.check()
        self.write("metatrader-targets.json", {"candidates": {}, "selections": {"council": None}, "platformSelections": {}})
        self.check()

    def test_channel_traversal_and_mismatched_identity_are_rejected(self):
        folder = self.channel()
        (folder / "snapshot.json").write_text(json.dumps({"channelId": "mtc-other", "positionsSummary": {"count": 0}}))
        self.blocked("ea_identity_invalid")
        self.write("metatrader-targets.json", {"candidates": {}, "selections": {"council": {"candidateId": "mtc-../../other"}}})
        self.blocked("target_identity_invalid")

    def test_corrupt_duplicate_null_and_nonfinite_json_fail_closed(self):
        path = self.runtime / "missions.json"
        for raw in ('{', 'null', '{"missions":[],"missions":[]}', '{"missions":[],"number":NaN}'):
            path.write_text(raw)
            with self.assertRaises(guard.UpgradeBlocked):
                self.check()
            self.assertEqual(raw, path.read_text())

    def test_cli_errors_contain_only_safe_reason(self):
        self.write("missions.json", {"missions": [{"status": "running", "secret": "NEVER_EMIT_THIS"}]})
        import sys
        result = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "installer/upgrade_guard.py"), "--install-root", str(self.root), "--common-files", str(self.common)], capture_output=True, text=True, timeout=10)
        self.assertEqual(3, result.returncode)
        self.assertEqual({"ok": False, "code": "active_mission"}, json.loads(result.stdout))
        self.assertEqual("", result.stderr)


@unittest.skipUnless(os.name == "nt", "Windows maintenance lease")
class OfflineUpgradeLeaseTests(unittest.TestCase):
    def run_fixture(self, body, *, short_parent=False):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            if short_parent:
                # GitHub's Windows TEMP can contain RUNNER~1. Force the same
                # 8.3 alias case locally; no production directory is touched.
                import ctypes
                from ctypes import wintypes
                parent = parent / "Maintenance Lease Long Parent"
                parent.mkdir()
                get_short = ctypes.WinDLL("kernel32", use_last_error=True).GetShortPathNameW
                get_short.argtypes = (wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD)
                get_short.restype = wintypes.DWORD
                buffer = ctypes.create_unicode_buffer(32768)
                result = get_short(str(parent), buffer, len(buffer))
                if not result or result >= len(buffer):
                    self.fail("Unable to obtain the isolated Windows 8.3 fixture path")
                if buffer.value.lower() == str(parent).lower():
                    self.skipTest("The fixture volume has 8.3 names disabled")
                parent = Path(buffer.value)
            root = parent / "isolated-hq"
            # Independent production Bridge derivation: PROJECT_ROOT is a
            # pathlib-resolved path, not the raw possibly-short TEMP spelling.
            bridge_digest = hashlib.sha256(str(root.resolve()).lower().encode("utf-8")).hexdigest()[:16]
            script = f"""
$ErrorActionPreference='Stop'
$installRoot='{str(root).replace("'", "''")}'
$bridgeDigest='{bridge_digest}'
$upgradeMaintenanceLease=$null
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('{str(ROOT / 'installer/install.ps1').replace("'", "''")}',[ref]$tokens,[ref]$errors)
if ($errors.Count) {{ throw 'Installer syntax error' }}
foreach ($name in @('Assert-NoInstalledBridgeProcess','Enter-UpgradeMaintenanceLease','Exit-UpgradeMaintenanceLease')) {{
 $function=$ast.Find({{param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name}},$true)
 Invoke-Expression $function.Extent.Text
}}
function Get-CimInstance {{ @() }}
{body}
"""
            command = base64.b64encode(script.encode("utf-16le")).decode("ascii")
            result = subprocess.run(["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-EncodedCommand", command], capture_output=True, text=True, timeout=20)
            self.assertEqual(0, result.returncode, result.stderr)

    def assert_bridge_namespace_held(self, *, short_parent=False):
        self.run_fixture(r"""
Enter-UpgradeMaintenanceLease
try {
 $digest=$bridgeDigest; $created=$false
 $competitor=[Threading.Mutex]::new($false,('Local\MetafxAgentHQBridge-'+$digest),[ref]$created)
 if ($created) { throw ('Bridge could enter during upgrade: raw=' + $installRoot + '; canonical=' + [IO.Path]::GetFullPath($installRoot) + '; expected=' + $bridgeDigest) }
 $competitor.Dispose()
} finally { Exit-UpgradeMaintenanceLease }
$created=$false
$next=[Threading.Mutex]::new($false,('Local\MetafxAgentHQBridge-'+$digest),[ref]$created)
if (-not $created) { throw 'Maintenance lease leaked' }; $next.Dispose()
""", short_parent=short_parent)

    def test_same_bridge_namespace_is_held_and_released(self):
        self.assert_bridge_namespace_held()

    def test_short_temp_alias_uses_the_actual_bridge_canonical_namespace(self):
        self.assert_bridge_namespace_held(short_parent=True)

    def test_existing_owner_refuses_without_releasing_its_lease(self):
        self.run_fixture(r"""
Enter-UpgradeMaintenanceLease
$owner=$script:upgradeMaintenanceLease; $script:upgradeMaintenanceLease=$null
try {
 $rejected=$false
 try { Enter-UpgradeMaintenanceLease } catch { $rejected=$true }
 if (-not $rejected) { throw 'Existing owner accepted' }
 if ($script:upgradeMaintenanceLease) { throw 'Refusal retained another lease' }
} finally { $owner.Dispose() }
Enter-UpgradeMaintenanceLease; Exit-UpgradeMaintenanceLease
""")

    def test_legacy_running_or_unknown_identity_rejects_and_releases(self):
        self.run_fixture(r"""
function Get-CimInstance { @([pscustomobject]@{Name='python.exe'; CommandLine=('python "'+$installRoot+'\backend\local-runner\bridge_server.py" --host 127.0.0.1 --port 4186'); ExecutablePath='C:\fixture\python.exe'}) }
$rejected=$false
try { Enter-UpgradeMaintenanceLease } catch { $rejected=$true }
if (-not $rejected -or $script:upgradeMaintenanceLease) { throw 'Legacy process refusal failed' }
function Get-CimInstance { throw 'CIM unavailable' }
$rejected=$false
try { Enter-UpgradeMaintenanceLease } catch { $rejected=$true }
if (-not $rejected -or $script:upgradeMaintenanceLease) { throw 'Unknown process state accepted' }
function Get-CimInstance { @() }
Enter-UpgradeMaintenanceLease; Exit-UpgradeMaintenanceLease
""")

    def test_guard_precedes_service_mutations_and_copy_is_covered(self):
        source = (ROOT / "installer/install.ps1").read_text(encoding="utf-8-sig")
        start = source.index("$bridgeTaskWasEnabled = $false\n    try {")
        main = source[start:]
        self.assertLess(main.index("Enter-UpgradeMaintenanceLease"), main.index("Suspend-SentimentForUpdate"))
        self.assertLess(main.index("Assert-OfflineUpgradeReady"), main.index("Suspend-SentimentForUpdate"))
        self.assertNotIn("Stop-ExistingBridge", main)
        self.assertLess(main.index("Publish-StagedApplication"), main.index("Exit-UpgradeMaintenanceLease"))
        self.assertLess(main.index("Exit-UpgradeMaintenanceLease"), main.index("$bridgeEndpoint = Start-And-TestBridge"))
        suspend = source[source.index("function Suspend-BridgeScheduledTask"):source.index("function Restore-BridgeScheduledTask")]
        self.assertNotIn("Stop-ScheduledTask", suspend)
        self.assertIn("finally {\n        Exit-UpgradeMaintenanceLease", main)

    def test_owner_stopping_after_old_probe_remains_offline_after_rollback(self):
        self.run_fixture(r"""
$source=$ast.Extent.Text
$mainStart=$source.IndexOf('$bridgeTaskWasEnabled = $false')
$preludeStart=$source.IndexOf('Enter-UpgradeMaintenanceLease', $mainStart)
$preludeEnd=$source.IndexOf('Suspend-SentimentForUpdate', $preludeStart)
$prelude=$source.Substring($preludeStart,$preludeEnd-$preludeStart)
$recoveryStart=$source.IndexOf('if ($rollbackRestored -and $previousBridgeWasRunning)', $preludeEnd)
$recoveryEnd=$source.IndexOf('}', $recoveryStart)+1
$recovery=$source.Substring($recoveryStart,$recoveryEnd-$recoveryStart)
$previousBridgeWasRunning=$true
$script:previousBridgeWasStopped=$true
$script:restarts=0
function Assert-OfflineUpgradeReady { }
function Start-PreviousBridgeAfterRollback {
 if ($script:upgradeMaintenanceLease) { throw 'Recovery tried to start under its own maintenance lease' }
 $script:restarts++; return $true
}
try {
 Invoke-Expression $prelude
 if ($previousBridgeWasRunning -or $script:previousBridgeWasStopped) { throw 'Old probe was not superseded by the stopped baseline' }
 $rollbackRestored=$true
 Invoke-Expression $recovery
 if ($script:restarts -ne 0) { throw 'Rollback revived an intentionally stopped HQ' }
 if (-not $script:upgradeMaintenanceLease) { throw 'Offline rollback lost its publication lease too early' }
} finally { Exit-UpgradeMaintenanceLease }
""")

    def test_any_legacy_recovery_start_releases_the_maintenance_lease_first(self):
        self.run_fixture(r"""
$source=$ast.Extent.Text
$mainStart=$source.IndexOf('$bridgeTaskWasEnabled = $false')
$first=$source.IndexOf('if ($rollbackRestored -and $previousBridgeWasRunning)', $mainStart)
$second=$source.IndexOf('elseif ($script:previousBridgeWasStopped -and $previousBridgeWasRunning)', $first)
$script:restarts=0
function Start-PreviousBridgeAfterRollback {
 if ($script:upgradeMaintenanceLease) { throw 'Start still holds the maintenance lease' }
 $script:restarts++; return $true
}
foreach ($offset in @($first,$second)) {
 $begin=$source.IndexOf('{',$offset)+1
 $end=$source.IndexOf('}',$begin)
 Enter-UpgradeMaintenanceLease
 try { Invoke-Expression $source.Substring($begin,$end-$begin) }
 finally { Exit-UpgradeMaintenanceLease }
}
if ($script:restarts -ne 2) { throw 'Recovery fixture did not exercise both branches' }
""")


if __name__ == "__main__":
    unittest.main()
