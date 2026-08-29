from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETUP_SCRIPT = ROOT / "scripts" / "setup-google-oauth.ps1"
SETUP_BAT = ROOT / "2-SETUP-GOOGLE-HQ.bat"
INSTALL_BAT = ROOT / "1-INSTALL-HQ.bat"
INSTALLER = ROOT / "installer" / "install.ps1"
UNINSTALLER = ROOT / "scripts" / "uninstall-hq.ps1"
AUTO_INSTALL_PROMPT = ROOT / "docs" / "prompts" / "install-github-google-auto-th.md"


class GoogleOAuthFirstRunSetupTests(unittest.TestCase):
    def test_setup_script_parses_in_windows_powershell(self) -> None:
        parser = (
            "$tokens=$null;$errors=$null;"
            "[void][Management.Automation.Language.Parser]::ParseFile("
            "$env:METAFX_PS_PARSE_PATH,[ref]$tokens,[ref]$errors);"
            "if($errors.Count){$errors|%{Write-Error $_.Message};exit 1}"
        )
        environment = __import__("os").environ.copy()
        environment["METAFX_PS_PARSE_PATH"] = str(SETUP_SCRIPT)
        completed = subprocess.run(
            ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", parser],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
            env=environment,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_secret_boundary_is_backend_cli_only(self) -> None:
        script = SETUP_SCRIPT.read_text(encoding="utf-8-sig")
        self.assertIn("configure_google_oauth_client.py", script)
        self.assertIn('@($configureCli, "--file", $Path)', script)
        self.assertIn("Get-SafeClientJsonPath", script)
        self.assertIn("ReparsePoint", script)
        self.assertIn("64KB", script)
        self.assertIn('"--expected-client-id"', script)
        self.assertNotIn("function Assert-ExpectedClientId", script)
        self.assertNotIn("Get-Content -LiteralPath $Path", script)
        self.assertNotIn("ProtectedData", script)
        self.assertNotIn("SetEnvironmentVariable", script)
        self.assertNotIn("Get-Content -LiteralPath $fullPath", script)
        self.assertNotIn("-Action Restart", script)
        self.assertIn("-Action Ensure", script)

    def test_root_bat_supports_double_click_and_drag_drop(self) -> None:
        batch = SETUP_BAT.read_text(encoding="utf-8-sig")
        self.assertIn('if "%~1"==""', batch)
        self.assertIn('-ClientJsonPath "%~1"', batch)
        self.assertIn("setup-google-oauth.ps1", batch)

    def test_main_install_bat_is_one_click_on_fixed_classroom_endpoint(self) -> None:
        batch = INSTALL_BAT.read_text(encoding="utf-8-sig")
        self.assertIn('if "%~1"==""', batch)
        self.assertIn("-Port 4186 -EndpointConfirmed", batch)
        self.assertIn('installer\\install.ps1" %*', batch)

    @unittest.skipUnless(os.name == "nt", "Windows DPAPI integration")
    def test_powershell_import_round_trips_through_canonical_backend_store(self) -> None:
        client_id = "149991890071-testdesktopclient.apps.googleusercontent.com"
        client_secret = "TEST_CLIENT_SECRET_MUST_NOT_BE_PRINTED"
        document = {
            "installed": {
                "client_id": client_id,
                "project_id": "metafxclub-agent-hq-test",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_secret": client_secret,
                "redirect_uris": ["http://localhost"],
            }
        }
        with tempfile.TemporaryDirectory(prefix="mfxhq-google-first-run-") as temporary:
            temporary_root = Path(temporary)
            source_json = temporary_root / "desktop-client.json"
            source_json.write_text(json.dumps(document), encoding="utf-8")
            isolated_local_app_data = temporary_root / "LocalAppData"
            environment = os.environ.copy()
            environment["LOCALAPPDATA"] = str(isolated_local_app_data)

            completed = subprocess.run(
                [
                    "powershell.exe",
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(SETUP_SCRIPT),
                    "-ClientJsonPath",
                    str(source_json),
                    "-ExpectedClientId",
                    client_id,
                    "-SkipBridgeEnsure",
                    "-SkipOpen",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
                env=environment,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            visible_output = f"{completed.stdout}\n{completed.stderr}"
            self.assertNotIn(client_id, visible_output)
            self.assertNotIn(client_secret, visible_output)

            status = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "backend" / "local-runner" / "configure_google_oauth_client.py"),
                    "--status",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=20,
                check=False,
                env=environment,
            )
            self.assertEqual(status.returncode, 0, status.stderr)
            safe_status = json.loads(status.stdout)
            self.assertTrue(safe_status["ok"])
            self.assertTrue(safe_status["configured"])
            self.assertNotEqual(safe_status["clientHint"], client_id)
            self.assertNotIn(client_secret, status.stdout)
            self.assertTrue(
                (isolated_local_app_data / "Metafxclub" / "AgentHQ" / "credentials" / "google-oauth-client.dpapi").is_file()
            )
            self.assertEqual(list(isolated_local_app_data.rglob("*.json")), [])

    def test_installer_offers_optional_setup_without_ci_dialog(self) -> None:
        installer = INSTALLER.read_text(encoding="utf-8-sig")
        self.assertIn("[switch]$SkipGoogleSetup", installer)
        self.assertIn("function Invoke-GoogleOAuthFirstRunSetup", installer)
        self.assertIn("2-SETUP-GOOGLE-HQ.bat", installer)
        self.assertIn("scripts\\setup-google-oauth.ps1", installer)
        self.assertIn("-SkipBridgeEnsure -SkipOpen", installer)
        package_exit = installer.index('Write-Step "Package Smoke')
        first_run = installer.index("Invoke-GoogleOAuthFirstRunSetup -CandidateRoot")
        self.assertLess(package_exit, first_run)
        self.assertLess(installer.index("Test-InstalledApplication -PythonPath", package_exit), first_run)
        self.assertLess(installer.index("Start-And-TestBridge -ConfirmedPort", package_exit), first_run)
        self.assertLess(installer.index("Remove-ApplicationRollbackSnapshot -RollbackState", package_exit), first_run)
        self.assertIn("Invoke-GoogleOAuthFirstRunSetup -CandidateRoot $installRoot", installer)
        first_run_function = installer[
            installer.index("function Invoke-GoogleOAuthFirstRunSetup") :
            installer.index("function Invoke-BridgeLifecycleProcess")
        ]
        self.assertIn("$explicitClientSetup", first_run_function)
        self.assertIn("$SkipGoogleSetup -and -not $explicitClientSetup", first_run_function)
        self.assertIn("-ExpectedClientId", first_run_function)
        post_commit = installer[installer.index("Remove-ApplicationRollbackSnapshot -RollbackState") :]
        self.assertLess(
            post_commit.index("Register-NewBridgeScheduledTask"),
            post_commit.index("Invoke-GoogleOAuthFirstRunSetup"),
        )
        self.assertIn("ติดตั้ง Agent HQ สำเร็จ แต่ยังตั้งค่า Google ไม่ได้", post_commit)
        self.assertIn('$postInstallFailure = "Agent HQ ติดตั้งและเปิดใช้งานแล้ว', post_commit)
        self.assertIn("exit 2", post_commit)
        self.assertIn("ตัวโปรแกรมไม่ถูก Rollback", post_commit)

    def test_student_docs_keep_json_out_of_browser_and_project(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        quickstart = (ROOT / "STUDENT-QUICKSTART-TH.md").read_text(encoding="utf-8")
        setup_doc = (ROOT / "docs" / "research-sheet-hub-setup-th.md").read_text(encoding="utf-8")
        for text in (readme, quickstart, setup_doc):
            self.assertIn("2-SETUP-GOOGLE-HQ.bat", text)
            self.assertIn("DPAPI", text)
            self.assertIn("Browser", text)
        self.assertIn("ไม่ต้อง Restart Bridge", setup_doc)

    def test_automatic_install_prompt_uses_verified_noninteractive_contract(self) -> None:
        prompt = AUTO_INSTALL_PROMPT.read_text(encoding="utf-8-sig")
        for placeholder in (
            "GITHUB_RELEASE_URL",
            "EXPECTED_GOOGLE_CLIENT_ID",
            "GOOGLE_DESKTOP_OAUTH_JSON",
        ):
            self.assertIn(placeholder, prompt)
        self.assertIn("-ListAvailableEndpoints", prompt)
        self.assertIn("available=true", prompt)
        self.assertIn("-Port 4186 -EndpointConfirmed", prompt)
        self.assertIn("-GoogleClientJsonPath", prompt)
        self.assertIn("-ExpectedGoogleClientId", prompt)
        self.assertNotIn("-EndpointConfirmed -SkipGoogleSetup", prompt)
        self.assertIn("ห้ามใช้ -SkipLaunch", prompt)
        self.assertNotIn("-SkipGoogleSetup -SkipLaunch", prompt)
        self.assertIn(
            "$env:LOCALAPPDATA\\Metafxclub\\AI-Agent-HQ\\scripts\\setup-google-oauth.ps1",
            prompt,
        )
        self.assertIn("-ClientJsonPath", prompt)
        self.assertIn("-SkipOpen", prompt)
        self.assertIn("authorization_required", prompt)
        self.assertIn("Exit code 2", prompt)
        self.assertIn("partial success", prompt)
        self.assertIn("ห้ามกดปุ่มเชื่อม Google", prompt)
        self.assertIn("Client Secret", prompt)

    def test_uninstall_removes_setup_launcher_and_requires_explicit_data_removal(self) -> None:
        uninstaller = UNINSTALLER.read_text(encoding="utf-8-sig")
        self.assertIn('"2-SETUP-GOOGLE-HQ.bat"', uninstaller)
        self.assertIn('$ConfirmUserDataRemoval -cne "DELETE-METAFX-DATA"', uninstaller)
        self.assertIn("Remove-GoogleOAuthUserConfiguration", uninstaller)
        removal = uninstaller[
            uninstaller.index("function Remove-GoogleOAuthUserConfiguration") :
            uninstaller.index("$unregisterAutostart")
        ]
        self.assertIn("configure_google_oauth_client.py", removal)
        self.assertIn("--remove", removal)
        self.assertNotIn("google-oauth-client.dpapi", removal)
        self.assertNotIn("google-sheets-refresh.dpapi", removal)
        call = uninstaller.index("    Remove-GoogleOAuthUserConfiguration")
        delete_application = uninstaller.index('foreach ($directoryName in @(')
        self.assertLess(call, delete_application)
        self.assertIn("หากติดตั้งใหม่จะใช้ต่อได้", uninstaller)


if __name__ == "__main__":
    unittest.main()
