from __future__ import annotations

import json
import os
import shutil
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
        self.assertIn("ADVANCED/RECOVERY สำหรับผู้ดูแลระบบเท่านั้น", batch)
        self.assertIn("นี่ไม่ใช่ขั้นตอนปกติของนักเรียน", batch)
        self.assertIn("ใช้ Client กลางจาก Release", batch)

    def test_main_install_bat_is_one_click_on_fixed_classroom_endpoint(self) -> None:
        batch = INSTALL_BAT.read_text(encoding="utf-8-sig")
        self.assertIn('if "%~1"==""', batch)
        self.assertIn("-Port 4186 -EndpointConfirmed", batch)
        self.assertIn('installer\\install.ps1" %*', batch)
        for exit_code, component in ((2, "Google OAuth"), (3, "Watchdog"), (4, "Google OAuth และ Watchdog")):
            with self.subTest(exit_code=exit_code):
                self.assertIn(f'if "%INSTALL_EXIT%"=="{exit_code}"', batch)
                self.assertIn(f"{component} ยังต้องซ่อม", batch)
        self.assertIn("Runtime และ Health พร้อมใช้งานแล้ว", batch)
        self.assertIn("ไม่ต้องติดตั้ง Source ซ้ำ", batch)

    @unittest.skipUnless(os.name == "nt", "Windows DPAPI integration")
    def test_clean_profile_uses_central_client_then_requires_user_authorization(self) -> None:
        source_runner = ROOT / "backend" / "local-runner"
        central_client_id = "123456789012-release.apps.googleusercontent.com"
        central_client_secret = "GOC" + "SPX-" + ("C" * 24)
        with tempfile.TemporaryDirectory(prefix="mfxhq-google-central-") as temporary:
            temporary_root = Path(temporary)
            staged_root = temporary_root / "staged-release"
            runner = staged_root / "backend" / "local-runner"
            shutil.copytree(
                source_runner,
                runner,
                ignore=shutil.ignore_patterns(
                    "__pycache__",
                    "google_oauth_native_client.txt",
                ),
            )
            (runner / "google_oauth_native_client.txt").write_text(
                f"client_id={central_client_id}\n"
                f"client_secret={central_client_secret}\n",
                encoding="utf-8",
            )
            isolated_local_app_data = temporary_root / "LocalAppData"
            isolated_local_app_data.mkdir()
            environment = os.environ.copy()
            environment["LOCALAPPDATA"] = str(isolated_local_app_data)
            for name in (
                "METAFX_GOOGLE_OAUTH_CLIENT_ID",
                "METAFX_GOOGLE_OAUTH_CLIENT_SECRET",
                "METAFX_GOOGLE_OAUTH_REFRESH_TOKEN",
                "METAFX_GOOGLE_SHEETS_ACCESS_TOKEN",
            ):
                environment.pop(name, None)

            client_status = subprocess.run(
                [
                    sys.executable,
                    str(runner / "configure_google_oauth_client.py"),
                    "--status",
                ],
                cwd=staged_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=20,
                check=False,
                env=environment,
            )
            self.assertEqual(client_status.returncode, 0, client_status.stderr)
            safe_client_status = json.loads(client_status.stdout)
            self.assertTrue(safe_client_status["ok"])
            self.assertTrue(safe_client_status["configured"])
            self.assertEqual(safe_client_status["store"], "central_release")

            runtime_status = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import json,sys;"
                        f"sys.path.insert(0,{str(runner)!r});"
                        "import google_sheet_hub as h;"
                        "print(json.dumps(h.google_oauth_status(),sort_keys=True))"
                    ),
                ],
                cwd=staged_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=20,
                check=False,
                env=environment,
            )
            self.assertEqual(runtime_status.returncode, 0, runtime_status.stderr)
            public_status = json.loads(runtime_status.stdout)
            self.assertTrue(public_status["clientConfigured"])
            self.assertFalse(public_status["connected"])
            self.assertFalse(public_status["configured"])
            self.assertEqual(public_status["status"], "authorization_required")
            self.assertEqual(public_status["clientSource"], "central_release")
            self.assertFalse(public_status["storedCredential"])

            visible_output = "\n".join(
                (
                    client_status.stdout,
                    client_status.stderr,
                    runtime_status.stdout,
                    runtime_status.stderr,
                )
            )
            self.assertFalse(
                central_client_id in visible_output
                or central_client_secret in visible_output,
                "central native client values leaked through status output",
            )
            self.assertEqual(list(isolated_local_app_data.rglob("*.dpapi")), [])
            self.assertEqual(list(isolated_local_app_data.rglob("*.json")), [])

    @unittest.skipUnless(os.name == "nt", "Windows DPAPI integration")
    def test_powershell_import_round_trips_through_canonical_backend_store(self) -> None:
        client_id = "123456789012-testdesktopclient.apps.googleusercontent.com"
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

    @unittest.skipUnless(os.name == "nt", "Windows DPAPI integration")
    def test_client_and_refresh_grant_survive_fresh_runtime_processes(self) -> None:
        """Model a Bridge restart without ever printing the stored credentials."""

        client_id = "123456789012-restartdesktopclient.apps.googleusercontent.com"
        client_secret = "TEST_RESTART_CLIENT_SECRET_MUST_NOT_BE_PRINTED"
        refresh_token = "TEST_RESTART_REFRESH_TOKEN_MUST_NOT_BE_PRINTED"
        document = {
            "installed": {
                "client_id": client_id,
                "project_id": "metafxclub-agent-hq-restart-test",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_secret": client_secret,
                "redirect_uris": ["http://localhost"],
            }
        }
        runner = ROOT / "backend" / "local-runner"
        with tempfile.TemporaryDirectory(prefix="mfxhq-google-restart-") as temporary:
            temporary_root = Path(temporary)
            source_json = temporary_root / "desktop-client.json"
            source_json.write_text(json.dumps(document), encoding="utf-8")
            environment = os.environ.copy()
            environment["LOCALAPPDATA"] = str(temporary_root / "LocalAppData")
            environment["METAFX_TEST_REFRESH"] = refresh_token

            imported = subprocess.run(
                [
                    sys.executable,
                    str(runner / "configure_google_oauth_client.py"),
                    "--file",
                    str(source_json),
                    "--expected-client-id",
                    client_id,
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
            self.assertEqual(imported.returncode, 0, imported.stderr)

            saved = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import os,sys;"
                        f"sys.path.insert(0,{str(runner)!r});"
                        "import google_oauth_store as s;"
                        "s.save_refresh_token(os.environ['METAFX_TEST_REFRESH'])"
                    ),
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
            self.assertEqual(saved.returncode, 0, saved.stderr)

            # A third process represents the newly started Bridge after a
            # logout/reboot. It returns only the public auth read model.
            restarted = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import json,sys;"
                        f"sys.path.insert(0,{str(runner)!r});"
                        "import google_sheet_hub as h;"
                        "print(json.dumps(h.google_oauth_status(),sort_keys=True))"
                    ),
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
            self.assertEqual(restarted.returncode, 0, restarted.stderr)
            public_status = json.loads(restarted.stdout)
            self.assertTrue(public_status["connected"])
            self.assertEqual(public_status["mode"], "oauth_refresh_stored")
            self.assertTrue(public_status["clientConfigured"])
            visible_output = "\n".join(
                (
                    imported.stdout,
                    imported.stderr,
                    saved.stdout,
                    saved.stderr,
                    restarted.stdout,
                    restarted.stderr,
                )
            )
            self.assertNotIn(client_id, visible_output)
            self.assertNotIn(client_secret, visible_output)
            self.assertNotIn(refresh_token, visible_output)

    def test_installer_uses_central_default_and_keeps_advanced_json_override(self) -> None:
        installer = INSTALLER.read_text(encoding="utf-8-sig")
        self.assertIn("[switch]$SkipGoogleSetup", installer)
        self.assertIn("function Invoke-GoogleOAuthFirstRunSetup", installer)
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
        self.assertIn("Get-GoogleOAuthDeploymentStatus -CandidateRoot", first_run_function)
        self.assertIn('"central_release"', first_run_function)
        self.assertIn('$script:googleSetupStatus = "ready_central"', first_run_function)
        self.assertIn('$script:googleSetupStatus = "ready_existing_override"', first_run_function)
        self.assertNotIn("Read-Host", first_run_function)

        # Explicit JSON import remains an advanced/recovery override and must
        # still go through the canonical backend-only setup script.
        self.assertIn("scripts\\setup-google-oauth.ps1", first_run_function)
        self.assertIn('"-ClientJsonPath", $validatedGoogleClientJsonPath', first_run_function)
        self.assertIn("-ExpectedClientId", first_run_function)
        self.assertIn("-SkipBridgeEnsure", first_run_function)
        self.assertIn("-SkipOpen", first_run_function)
        self.assertIn('$script:googleSetupStatus = "ready_imported"', first_run_function)
        post_commit = installer[installer.index("Remove-ApplicationRollbackSnapshot -RollbackState") :]
        self.assertLess(
            post_commit.index("Register-NewBridgeScheduledTask"),
            post_commit.index("Invoke-GoogleOAuthFirstRunSetup"),
        )
        self.assertIn("Google OAuth Client กลางไม่พร้อม", post_commit)
        self.assertIn("Google OAuth Client แบบ Advanced", post_commit)
        self.assertIn("$googleSetupFailure = $true", post_commit)
        self.assertIn("exit $postInstallExitCode", post_commit)
        self.assertIn("Runtime ยังเปิดใช้ได้และไม่ถูก Rollback", post_commit)

    def test_student_docs_use_central_client_without_per_student_oauth_setup(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        quickstart = (ROOT / "STUDENT-QUICKSTART-TH.md").read_text(encoding="utf-8")
        setup_doc = (ROOT / "docs" / "research-sheet-hub-setup-th.md").read_text(encoding="utf-8")
        for text in (readme, quickstart):
            self.assertIn("Client กลาง", text)
            self.assertRegex(
                text,
                r"ไม่ต้อง(?:\*{0,2}\s*)?สร้าง Google Cloud Project/OAuth Client",
            )
            self.assertIn("ไม่ต้องดาวน์โหลด", text)
            self.assertIn("เชื่อมบัญชี Google", text)
            self.assertIn("Release secrets", text)
            self.assertIn("public Git", text)
        for text in (readme, quickstart, setup_doc):
            self.assertIn("DPAPI", text)
        self.assertIn("ไม่ต้อง Restart Bridge", setup_doc)

        # Advanced custom JSON remains documented as recovery/admin-only, but
        # the classroom path may never instruct each student to provide it.
        self.assertIn("Advanced/Recovery custom override", readme)
        self.assertIn("Advanced/Recovery custom override", quickstart)
        for old_student_instruction in (
            "เปิด Google Auth Platform ของ Project ตนเอง",
            "นักเรียนแก้เฉพาะ 2 บรรทัดสุดท้ายคือ Client ID",
            "เพิ่ม Gmail ที่นักเรียนจะใช้เชื่อมไว้ที่ Google Auth Platform",
        ):
            with self.subTest(old_student_instruction=old_student_instruction):
                self.assertNotIn(old_student_instruction, readme)
                self.assertNotIn(old_student_instruction, quickstart)

    def test_student_docs_distinguish_prompt_bootstrap_from_manual_prerequisites(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        quickstart = (ROOT / "STUDENT-QUICKSTART-TH.md").read_text(encoding="utf-8")

        for text in (readme, quickstart):
            self.assertIn("ไม่ต้องติดตั้ง Git หรือ Python", text)
            self.assertIn("WinGet", text)
            self.assertIn("current-user", text)
            self.assertIn("ไม่ติดตั้งซ้ำ", text)

        readme_manual = readme[readme.index("## ติดตั้งด้วยตนเอง") : readme.index("## Clone Source")]
        quickstart_manual = quickstart[
            quickstart.index("## วิธีติดตั้งเองเมื่อไม่ได้ใช้ Codex") :
            quickstart.index("## ถ้าต้องการเก็บ Source")
        ]
        for manual in (readme_manual, quickstart_manual):
            self.assertIn("Python 3.10-3.14 แบบ 64-bit", manual)

        readme_clone = readme[readme.index("## Clone Source") : readme.index("## วิธีตรวจว่าพร้อมใช้งาน")]
        quickstart_clone = quickstart[
            quickstart.index("## ถ้าต้องการเก็บ Source") :
            quickstart.index("## เปิด Bridge อัตโนมัติ")
        ]
        for clone_section in (readme_clone, quickstart_clone):
            self.assertIn("Plain clone", clone_section)
            self.assertIn("Prompt หลัก", clone_section)
            self.assertIn("Release Asset", clone_section)
            self.assertNotIn(".\\1-INSTALL-HQ.bat", clone_section)
        self.assertIn("ไม่ใช่ตัวอัปเดตสำหรับชุดห้องเรียน", readme_clone)
        self.assertIn("ไม่ต้อง Pull `main`", quickstart_clone)

    def test_automatic_install_prompt_uses_verified_noninteractive_contract(self) -> None:
        prompt = AUTO_INSTALL_PROMPT.read_text(encoding="utf-8-sig")
        version = (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip()
        for placeholder in (
            "GITHUB_REPOSITORY",
            "GITHUB_TAG",
            "EXPECTED_VERSION",
        ):
            self.assertIn(placeholder, prompt)
        for prohibited in (
            "EXPECTED_GOOGLE_CLIENT_ID",
            "GOOGLE_DESKTOP_OAUTH_JSON",
            "-GoogleClientJsonPath",
            "-ExpectedGoogleClientId",
            "-ClientJsonPath",
            "เพิ่ม Gmail ที่นักเรียนจะใช้เชื่อมไว้ที่ Google Auth Platform",
            "ตรวจ GOOGLE_DESKTOP_OAUTH_JSON",
        ):
            with self.subTest(prohibited=prohibited):
                self.assertNotIn(prohibited, prompt)
        self.assertIn('GITHUB_REPOSITORY = "https://github.com/metafxclub/metafxclub-ai-agent-hq.git"', prompt)
        self.assertIn(f'GITHUB_TAG = "v{version}"', prompt)
        self.assertIn(f'EXPECTED_VERSION = "{version}"', prompt)
        self.assertIn("git ls-remote --exit-code --tags", prompt)
        self.assertIn('"refs/tags/<GITHUB_TAG>^{}"', prompt)
        self.assertIn("REMOTE_TAG_COMMIT", prompt)
        self.assertIn("git clone --depth 1 --single-branch --branch", prompt)
        self.assertIn("git status --porcelain", prompt)
        self.assertIn("ดาวน์โหลด Release ZIP กับ `.sha256`", prompt)
        self.assertIn("Get-FileHash -Algorithm SHA256", prompt)
        self.assertIn("git check-ignore -q -- backend/local-runner/google_oauth_native_client.txt", prompt)
        self.assertIn("ไม่มีอยู่ใน Git index", prompt)
        self.assertIn("อ่าน bytes ของ entry นี้แล้วเขียนแบบ atomic ไปที่", prompt)
        for unsafe_archive_entry in ("absolute path", "`..`", "duplicate", "symlink", "ReparsePoint"):
            with self.subTest(unsafe_archive_entry=unsafe_archive_entry):
                self.assertIn(unsafe_archive_entry, prompt)
        self.assertIn("refs/tags/GITHUB_TAG^{commit}", prompt)
        self.assertNotIn("GITHUB_RELEASE_URL", prompt)
        self.assertIn("URL `latest`", prompt)
        self.assertIn("-ListAvailableEndpoints", prompt)
        self.assertIn("available=true", prompt)
        self.assertIn("-Port 4186 -EndpointConfirmed", prompt)
        self.assertIn("-ExpectedGitRepository", prompt)
        self.assertIn("-ExpectedGitTag", prompt)
        self.assertIn("-ExpectedSourceVersion", prompt)
        self.assertGreaterEqual(prompt.count("-RequireVerifiedGitSource"), 2)
        primary_install = prompt[
            prompt.index("9. เรียก Installer") :
            prompt.index("10. ")
        ]
        self.assertNotIn("-EndpointConfirmed -SkipGoogleSetup", primary_install)
        self.assertIn("ห้ามใช้ `-SkipLaunch`", prompt)
        self.assertNotIn("-SkipGoogleSetup -SkipLaunch", prompt)
        self.assertIn("Client กลาง", prompt)
        self.assertIn("GitHub Actions inject จาก Release secrets", prompt)
        self.assertIn("ห้าม commit ค่าจริงลง public Source", prompt)
        self.assertIn("authorization_required", prompt)
        self.assertIn('source.provenance="verified_remote_git_tag"', prompt)
        self.assertIn("post_install.google_oauth_client.requested=true", prompt)
        self.assertIn('post_install.google_oauth_client.status="ready_central"', prompt)
        self.assertIn('post_install.google_oauth_client.source="central_release"', prompt)
        self.assertIn("ready_existing_override", prompt)
        self.assertIn("2=Google OAuth", prompt)
        self.assertIn("3=Watchdog", prompt)
        self.assertIn("partial", prompt)
        self.assertIn("ห้ามกดปุ่มเชื่อม Google", prompt)
        self.assertIn("Client Secret", prompt)
        self.assertIn("Git.Git", prompt)
        self.assertIn("Python.Python.3.13", prompt)
        self.assertIn("The Git Development Community", prompt)
        self.assertIn("Python Software Foundation", prompt)
        self.assertIn("ใช้ของเดิมทันที", prompt)
        self.assertIn("Refresh เฉพาะ Process PATH", prompt)
        self.assertIn("Merge Process PATH เดิมกับ Machine PATH และ User PATH", prompt)
        self.assertIn('`-3.10` และ `-3` เป็นทางเลือกสุดท้าย', prompt)
        self.assertIn("git version --build-options", prompt)
        self.assertIn("cpu: x86_64", prompt)
        self.assertIn("sizeof-size_t: 8", prompt)
        self.assertIn("https://cdn.winget.microsoft.com/cache", prompt)
        self.assertIn("Microsoft.PreIndexed.Package", prompt)
        self.assertIn("Deadline รายการละ 15 นาที", prompt)
        self.assertIn("ห้ามเริ่ม Process ที่สอง", prompt)
        self.assertIn("existing", prompt)
        self.assertIn("installed_this_run", prompt)
        for command in (
            "winget install --id Git.Git --exact --source winget --scope user --architecture x64 --silent --no-upgrade",
            "winget install --id Python.Python.3.13 --exact --source winget --scope user --architecture x64 --silent --no-upgrade",
        ):
            self.assertIn(command, prompt)
        for prohibited in (
            "ห้ามใช้ `winget upgrade`",
            "`winget uninstall`",
            "`--force`",
            "`--override`",
            "`Start-Process -Verb RunAs`",
            "ห้ามแก้ Machine/User PATH แบบถาวร",
        ):
            self.assertIn(prohibited, prompt)
        self.assertNotIn("หากไม่มี Git ให้หยุดและแจ้งวิธีติดตั้ง Git for Windows", prompt)
        self.assertNotIn("ห้ามติดตั้ง Python, ปิด Antivirus", prompt)
        self.assertLess(prompt.index("Git.Git"), prompt.index("git ls-remote --exit-code --tags"))
        self.assertLess(prompt.index("Python.Python.3.13"), prompt.index("9. เรียก Installer"))
        quickstart = (ROOT / "STUDENT-QUICKSTART-TH.md").read_text(encoding="utf-8")
        self.assertIn("UAC หรือขอสิทธิ์ Administrator", quickstart)
        self.assertIn("กด **No/Cancel**", quickstart)
        self.assertIn("ห้ามกดยอมรับแทน", quickstart)

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
        self.assertIn("google-oauth-client.dpapi", removal)
        self.assertIn("google-sheets-refresh.dpapi", removal)
        self.assertIn("Test-Path -LiteralPath", removal)
        call = uninstaller.index("    Remove-GoogleOAuthUserConfiguration")
        delete_application = uninstaller.index('foreach ($directoryName in @(')
        self.assertLess(call, delete_application)
        self.assertIn("หากติดตั้งใหม่จะใช้ต่อได้", uninstaller)

    def test_full_data_uninstall_accepts_central_client_only_after_dpapi_cleanup(self) -> None:
        uninstaller = UNINSTALLER.read_text(encoding="utf-8-sig")
        removal = uninstaller[
            uninstaller.index("function Remove-GoogleOAuthUserConfiguration") :
            uninstaller.index("$unregisterAutostart")
        ]

        # The packaged central client remains resolvable until the application
        # directory is deleted, so configured=true is a valid post-remove state.
        self.assertIn(
            '$result.configured -eq $true -and $fallbackStore -in @("central_release", "environment")',
            removal,
        )
        self.assertNotIn('$result.configured -ne $false', removal)

        # The safe fallback must not be confused with a surviving per-user
        # override: both canonical DPAPI artifacts are checked independently.
        self.assertIn('"Metafxclub\\AgentHQ\\credentials"', removal)
        self.assertIn(
            '@("google-oauth-client.dpapi", "google-sheets-refresh.dpapi")',
            removal,
        )
        self.assertIn("Where-Object { Test-Path -LiteralPath $_ }", removal)
        self.assertIn("$remainingOAuthArtifacts.Count -gt 0", removal)
        self.assertIn('"not_configured", "empty"', removal)

    @unittest.skipUnless(os.name == "nt", "Windows PowerShell integration")
    def test_remove_user_data_runtime_accepts_central_fallback_but_rejects_partial_cleanup(self) -> None:
        uninstaller = UNINSTALLER.read_text(encoding="utf-8-sig")
        removal = uninstaller[
            uninstaller.index("function Remove-GoogleOAuthUserConfiguration") :
            uninstaller.index("$unregisterAutostart")
        ]
        cli_invocation = '    $output = @(& $pythonPath $configureCli --remove 2>$null)'
        self.assertEqual(removal.count(cli_invocation), 1)

        def run_case(*, leave_client_override: bool) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
            temporary = tempfile.TemporaryDirectory(prefix="mfxhq-uninstall-oauth-")
            self.addCleanup(temporary.cleanup)
            local_app_data = Path(temporary.name) / "LocalAppData"
            install_root = local_app_data / "Metafxclub" / "AI-Agent-HQ"
            python_path = install_root / "runner" / ".venv" / "Scripts" / "python.exe"
            configure_cli = install_root / "backend" / "local-runner" / "configure_google_oauth_client.py"
            python_path.parent.mkdir(parents=True)
            configure_cli.parent.mkdir(parents=True)
            python_path.write_bytes(b"test stub")
            configure_cli.write_text("# test stub\n", encoding="utf-8")

            credential_root = local_app_data / "Metafxclub" / "AgentHQ" / "credentials"
            credential_root.mkdir(parents=True)
            client_override = credential_root / "google-oauth-client.dpapi"
            refresh_token = credential_root / "google-sheets-refresh.dpapi"
            client_override.write_bytes(b"encrypted client override")
            refresh_token.write_bytes(b"encrypted refresh token")

            simulated_cli = [
                '    Remove-Item -LiteralPath (Join-Path $googleOAuthCredentialRoot "google-sheets-refresh.dpapi") -Force',
            ]
            if not leave_client_override:
                simulated_cli.append(
                    '    Remove-Item -LiteralPath (Join-Path $googleOAuthCredentialRoot "google-oauth-client.dpapi") -Force'
                )
            simulated_cli.extend(
                (
                    '    $output = @(\'{"configured":true,"ok":true,"removed":true,"store":"central_release"}\')',
                    "    $LASTEXITCODE = 0",
                )
            )
            function_under_test = removal.replace(cli_invocation, "\n".join(simulated_cli))
            harness = "\n".join(
                (
                    "Set-StrictMode -Version Latest",
                    '$ErrorActionPreference = "Stop"',
                    '$installRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA "Metafxclub\\AI-Agent-HQ")).TrimEnd("\\")',
                    function_under_test,
                    "Remove-GoogleOAuthUserConfiguration",
                )
            )
            harness_path = Path(temporary.name) / "invoke-remove-google-oauth.ps1"
            harness_path.write_text(harness, encoding="utf-8-sig")
            environment = os.environ.copy()
            environment["LOCALAPPDATA"] = str(local_app_data)
            completed = subprocess.run(
                [
                    "powershell.exe",
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(harness_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=20,
                check=False,
                env=environment,
            )
            return completed, client_override, refresh_token

        completed, client_override, refresh_token = run_case(leave_client_override=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(client_override.exists())
        self.assertFalse(refresh_token.exists())

        partial, client_override, refresh_token = run_case(leave_client_override=True)
        self.assertNotEqual(partial.returncode, 0)
        self.assertTrue(client_override.exists())
        self.assertFalse(refresh_token.exists())
        self.assertIn("DPAPI", partial.stdout + partial.stderr)


if __name__ == "__main__":
    unittest.main()
