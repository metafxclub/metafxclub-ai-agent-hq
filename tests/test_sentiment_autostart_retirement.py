"""Exercise legacy-shortcut retirement only; never register tasks or start services."""
from __future__ import annotations

import json
import ctypes
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "scripts/register-sentiment-autostart.ps1"
POWERSHELL = shutil.which("powershell.exe")

HARNESS = r"""
param([string]$CasePath)
$ErrorActionPreference = 'Stop'
$case = Get-Content -LiteralPath $CasePath -Raw -Encoding UTF8 | ConvertFrom-Json
$tokens = $null; $errors = $null
$tree = [Management.Automation.Language.Parser]::ParseFile($case.source,[ref]$tokens,[ref]$errors)
if ($errors.Count -ne 0) { throw 'Source parse failed.' }
$helper = $tree.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq 'Remove-VerifiedLegacyShortcut'},$false)
if (@($helper).Count -ne 1) { throw 'Expected one migration helper.' }
# Only the helper definition is loaded: no top-level task/health/launch code.
Invoke-Expression $helper[0].Extent.Text
$hqRoot = $case.hqRoot
$LegacyLauncherPath = $case.explicitLauncher
$LegacyPythonPath = $case.explicitPython
$shortcutPath = Join-Path $case.startup 'Metafxclub Sentiment Universe.lnk'
if ($case.createShortcut) {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $case.target
    $shortcut.Arguments = $case.arguments
    $shortcut.Save()
}
$before = if (Test-Path -LiteralPath $shortcutPath) { [Convert]::ToBase64String([IO.File]::ReadAllBytes($shortcutPath)) } else { $null }
$failure = $null
$global:sentimentMigrationTestCalls = @()
if ($case.runSetup) {
    # Intercept every child invocation. Only the read-only migration helper
    # above runs; Ensure and registration are counted without executing them.
    function powershell.exe {
        if ($args -contains '-ValidateMigrationOnly') {
            $global:sentimentMigrationTestCalls += 'preflight'
            try { Remove-VerifiedLegacyShortcut -ValidateOnly -StartupDirectory $case.startup; $global:LASTEXITCODE = 0 }
            catch { $global:LASTEXITCODE = 9 }
        } elseif ($args -contains 'Ensure') {
            $global:sentimentMigrationTestCalls += 'ensure'; $global:LASTEXITCODE = 0
        } else {
            $global:sentimentMigrationTestCalls += 'register'; $global:LASTEXITCODE = 0
        }
    }
    function Start-Process { throw 'Unexpected process start in isolated setup test.' }
    try { & $case.setup } catch { $failure = $_.Exception.Message }
} else {
    try { Remove-VerifiedLegacyShortcut -ValidateOnly:([bool]$case.validateOnly) -StartupDirectory $case.startup }
    catch { $failure = $_.Exception.Message }
}
$exists = Test-Path -LiteralPath $shortcutPath
$after = if ($exists) { [Convert]::ToBase64String([IO.File]::ReadAllBytes($shortcutPath)) } else { $null }
@{ failed=($null -ne $failure); exists=$exists; preserved=($exists -and $before -ceq $after); message=$failure; calls=@($global:sentimentMigrationTestCalls) } | ConvertTo-Json -Compress
"""


@unittest.skipUnless(os.name == "nt" and POWERSHELL, "Windows shortcut migration")
class SentimentAutostartRetirementTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="sentiment-autostart-retire-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.hq = self.root / "isolated hq"
        self.startup = self.root / "isolated Startup"
        self.startup.mkdir()
        self.launcher = self.hq / "backend/local-runner/sentiment_universe/scripts/start-live.py"
        self.python = self.hq / "runner/.venv/Scripts/pythonw.exe"
        for file in (self.launcher, self.python):
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(b"never executed fixture")
        self.harness = self.root / "helper-only.ps1"
        self.harness.write_text(HARNESS, encoding="utf-8-sig")

    def invoke(self, **overrides):
        case = {
            "source": str(REGISTER), "hqRoot": str(self.hq), "startup": str(self.startup),
            "explicitLauncher": "", "explicitPython": "",
            "target": str(self.python), "arguments": '"' + str(self.launcher) + '"',
            "createShortcut": True, "validateOnly": False, "runSetup": False,
            "setup": str(ROOT / "scripts/setup-sentiment-universe.ps1"),
        }
        case.update(overrides)
        case_path = self.root / "case.json"
        case_path.write_text(json.dumps(case), encoding="utf-8-sig")
        result = subprocess.run(
            [POWERSHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-File", str(self.harness), "-CasePath", str(case_path)],
            text=True, capture_output=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout.strip().splitlines()[-1])

    def test_default_installed_shortcut_is_retired(self):
        result = self.invoke()
        self.assertFalse(result["failed"], result)
        self.assertFalse(result["exists"], result)

    def test_preflight_validates_without_removing_shortcut(self):
        result = self.invoke(validateOnly=True)
        self.assertFalse(result["failed"], result)
        self.assertTrue(result["preserved"], result)

    def short_path(self, path):
        buffer = ctypes.create_unicode_buffer(32768)
        length = ctypes.windll.kernel32.GetShortPathNameW(str(path), buffer, len(buffer))
        self.assertGreater(length, 0, "Could not read the isolated fixture's short path")
        self.assertLess(length, len(buffer))
        if buffer.value == str(path):
            self.skipTest("The fixture filesystem does not provide an 8.3 alias")
        return Path(buffer.value)

    def test_short_temp_alias_argument_matches_exact_long_launcher(self):
        # GitHub's TEMP may contain RUNNER~1. WScript preserves that alias in
        # Arguments while GetFullPath expands the expected script path.
        short_root = self.short_path(self.root)
        short_launcher = short_root / self.launcher.relative_to(self.root)
        result = self.invoke(arguments='"' + str(short_launcher) + '"')
        self.assertFalse(result["failed"], result)
        self.assertFalse(result["exists"], result)

    def test_short_temp_alias_default_and_preflight_still_match(self):
        short_root = self.short_path(self.root)
        short_hq = short_root / self.hq.relative_to(self.root)
        short_python = short_root / self.python.relative_to(self.root)
        short_launcher = short_root / self.launcher.relative_to(self.root)
        result = self.invoke(hqRoot=str(short_hq), target=str(short_python),
                             arguments='"' + str(short_launcher) + '"', validateOnly=True)
        self.assertFalse(result["failed"], result)
        self.assertTrue(result["preserved"], result)

    def test_exact_launcher_with_case_variation_matches_windows_identity(self):
        result = self.invoke(arguments='"' + str(self.launcher).swapcase() + '"')
        self.assertFalse(result["failed"], result)
        self.assertFalse(result["exists"], result)

    def test_absent_shortcut_is_noop(self):
        result = self.invoke(createShortcut=False)
        self.assertFalse(result["failed"], result)
        self.assertFalse(result["exists"], result)

    def test_unknown_python_target_is_preserved_and_fails(self):
        other = self.root / "other/pythonw.exe"
        other.parent.mkdir()
        other.write_bytes(b"foreign fixture")
        result = self.invoke(target=str(other))
        self.assertTrue(result["failed"], result)
        self.assertTrue(result["preserved"], result)

    def test_external_prototype_requires_explicit_matching_paths(self):
        launcher = self.root / "old prototype/start-live.py"
        python = self.root / "old runtime/pythonw.exe"
        for file in (launcher, python):
            file.parent.mkdir(parents=True)
            file.write_bytes(b"external fixture")
        unknown = self.invoke(target=str(python), arguments='"' + str(launcher) + '"')
        self.assertTrue(unknown["failed"], unknown)
        self.assertTrue(unknown["preserved"], unknown)
        known = self.invoke(target=str(python), arguments='"' + str(launcher) + '"',
                            explicitLauncher=str(launcher), explicitPython=str(python))
        self.assertFalse(known["failed"], known)
        self.assertFalse(known["exists"], known)

    def test_extra_arguments_are_not_treated_as_owned(self):
        result = self.invoke(arguments='"' + str(self.launcher) + '" --port 4999')
        self.assertTrue(result["failed"], result)
        self.assertTrue(result["preserved"], result)

    def test_unquoted_path_with_spaces_is_not_a_single_launcher_argument(self):
        result = self.invoke(arguments=str(self.launcher))
        self.assertTrue(result["failed"], result)
        self.assertTrue(result["preserved"], result)

    def test_drive_relative_launcher_is_preserved(self):
        relative = self.launcher.drive + str(self.launcher)[len(self.launcher.drive) + 1:]
        result = self.invoke(arguments='"' + relative + '"')
        self.assertTrue(result["failed"], result)
        self.assertTrue(result["preserved"], result)

    def test_current_drive_root_relative_launcher_is_preserved(self):
        relative = str(self.launcher)[len(self.launcher.drive):]
        result = self.invoke(arguments='"' + relative + '"')
        self.assertTrue(result["failed"], result)
        self.assertTrue(result["preserved"], result)

    def test_trailing_newline_is_not_an_exact_single_argument(self):
        result = self.invoke(arguments='"' + str(self.launcher) + '"\n')
        self.assertTrue(result["failed"], result)
        self.assertTrue(result["preserved"], result)

    def test_short_path_with_extra_argument_is_preserved(self):
        short_launcher = self.short_path(self.launcher)
        result = self.invoke(arguments='"' + str(short_launcher) + '" --port 4999')
        self.assertTrue(result["failed"], result)
        self.assertTrue(result["preserved"], result)

    def test_different_existing_launcher_is_preserved(self):
        other = self.root / "foreign launcher/start-live.py"
        other.parent.mkdir()
        other.write_bytes(b"foreign fixture")
        result = self.invoke(arguments='"' + str(other) + '"')
        self.assertTrue(result["failed"], result)
        self.assertTrue(result["preserved"], result)

    def test_partial_explicit_identity_is_rejected_without_removal(self):
        result = self.invoke(explicitLauncher=str(self.launcher))
        self.assertTrue(result["failed"], result)
        self.assertTrue(result["preserved"], result)

    def test_unknown_shortcut_is_rejected_in_preflight(self):
        result = self.invoke(arguments='"' + str(self.launcher) + '" --extra', validateOnly=True)
        self.assertTrue(result["failed"], result)
        self.assertTrue(result["preserved"], result)

    def test_setup_rejects_unknown_shortcut_before_ensure(self):
        result = self.invoke(arguments='"' + str(self.launcher) + '" --port 4999', runSetup=True)
        self.assertTrue(result["failed"], result)
        self.assertTrue(result["preserved"], result)
        self.assertEqual(result["calls"], ["preflight"], result)

    def test_setup_validates_then_ensures_then_registers(self):
        result = self.invoke(runSetup=True)
        self.assertFalse(result["failed"], result)
        self.assertTrue(result["preserved"], result)  # Registration is mocked.
        self.assertEqual(result["calls"], ["preflight", "ensure", "register"], result)


class SentimentAutostartOrderingTests(unittest.TestCase):
    def test_setup_rejects_partial_migration_before_starting_service(self):
        source = (ROOT / "scripts/setup-sentiment-universe.ps1").read_text(encoding="utf-8-sig")
        self.assertLess(source.index("if ([bool]$LegacyLauncherPath -xor [bool]$LegacyPythonPath)"),
                        source.index("-File $lifecycle -Action Ensure"))

    def test_preflight_precedes_task_registration_and_removal_follows_verification(self):
        source = REGISTER.read_text(encoding="utf-8-sig")
        readonly = source[source.index("if ($ValidateMigrationOnly) {"):source.index("$previous = Get-ScheduledTask")]
        self.assertIn("Remove-VerifiedLegacyShortcut -ValidateOnly", readonly)
        self.assertIn("exit 0", readonly)
        self.assertLess(source.index("if (-not $Remove) { Remove-VerifiedLegacyShortcut -ValidateOnly }"),
                        source.index("$previous = Get-ScheduledTask"))
        self.assertLess(source.index("if (-not (Test-OwnedTask $installed))"),
                        source.rindex("\nRemove-VerifiedLegacyShortcut"))
        self.assertIn("docs/system-replacement-policy-th.md", (ROOT / "AGENTS.md").read_text(encoding="utf-8-sig"))


if __name__ == "__main__":
    unittest.main()
