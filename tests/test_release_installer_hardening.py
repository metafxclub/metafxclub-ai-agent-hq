from __future__ import annotations

import hashlib
import fnmatch
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "mt4-ai-council-ea-v2.18-enum-fail-closed-readiness"


class ReleaseInstallerHardeningTests(unittest.TestCase):
    def test_v218_curated_artifact_is_complete_and_not_ignored(self) -> None:
        required = {
            "MetafxHQTradeGateway.mq4",
            "MetafxHQTradeGateway.ex4",
            "README_TH.md",
            "AUDIT_TH.md",
            "SHA256SUMS.txt",
            "BUILD_LOG.txt",
            "MANIFEST.json",
            "COMPILE_PROOF.png",
        }
        self.assertEqual(required, {path.name for path in ARTIFACT.iterdir() if path.is_file()})

        for relative_path in (
            "scripts/run-bridge-watchdog-hidden.vbs",
            *(
                f"artifacts/mt4-ai-council-ea-v2.18-enum-fail-closed-readiness/{filename}"
                for filename in required
            ),
        ):
            completed = subprocess.run(
                [
                    "git",
                    "-c",
                    f"safe.directory={ROOT.as_posix()}",
                    "check-ignore",
                    "--quiet",
                    "--",
                    relative_path,
                ],
                cwd=ROOT,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertNotIn("dubious ownership", completed.stderr.lower())
            self.assertNotEqual(0, completed.returncode, f"release file remains ignored: {relative_path}")

        ignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("!artifacts/mt4-ai-council-ea-v2.18-enum-fail-closed-readiness/", ignore_text)
        self.assertIn("!artifacts/mt4-ai-council-ea-v2.18-enum-fail-closed-readiness/**", ignore_text)
        self.assertIn("artifacts/mt4-ai-council-ea-v2.18-enum-fail-closed-readiness/*.log", ignore_text)
        self.assertIn("integrations/mt4-trade-gateway/*.ex4", ignore_text)

    def test_v218_manifest_and_build_evidence_match_curated_files(self) -> None:
        manifest_text = (ARTIFACT / "SHA256SUMS.txt").read_text(encoding="utf-8")
        manifest: dict[str, str] = {}
        for line in manifest_text.splitlines():
            if not line.strip():
                continue
            match = re.fullmatch(r"([A-Fa-f0-9]{64})\s+([^\\/]+)", line)
            self.assertIsNotNone(match, line)
            assert match is not None
            manifest[match.group(2)] = match.group(1).upper()

        hashed_files = {
            "AUDIT_TH.md",
            "BUILD_LOG.txt",
            "COMPILE_PROOF.png",
            "MANIFEST.json",
            "MetafxHQTradeGateway.ex4",
            "MetafxHQTradeGateway.mq4",
            "README_TH.md",
        }
        self.assertEqual(hashed_files, set(manifest))
        for filename in hashed_files:
            digest = hashlib.sha256((ARTIFACT / filename).read_bytes()).hexdigest().upper()
            self.assertEqual(digest, manifest[filename])

        source_digest = hashlib.sha256(
            (ARTIFACT / "MetafxHQTradeGateway.mq4").read_bytes()
        ).hexdigest().upper()
        self.assertEqual(source_digest, manifest["MetafxHQTradeGateway.mq4"])

        artifact_manifest = json.loads((ARTIFACT / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual("metafx-hq-mt4-ea-artifact-v1", artifact_manifest["schemaVersion"])
        self.assertEqual("2.18", artifact_manifest["packageVersion"])
        self.assertEqual("ready_visible_metaeditor_compiled", artifact_manifest["candidateStatus"])
        self.assertEqual(source_digest, artifact_manifest["sourceSha256"])
        self.assertEqual(manifest["MetafxHQTradeGateway.ex4"], artifact_manifest["binarySha256"])
        self.assertEqual(
            (ARTIFACT / "MetafxHQTradeGateway.ex4").stat().st_size,
            artifact_manifest["binaryBytes"],
        )
        self.assertTrue(artifact_manifest["ex4Included"])
        compile_evidence = artifact_manifest["compileEvidence"]
        self.assertEqual("passed", compile_evidence["status"])
        self.assertEqual("visible_metaeditor_front_office", compile_evidence["mode"])
        self.assertEqual(0, compile_evidence["errors"])
        self.assertEqual(0, compile_evidence["warnings"])
        self.assertEqual("COMPILE_PROOF.png", compile_evidence["screenshot"])
        self.assertEqual(manifest["COMPILE_PROOF.png"], compile_evidence["screenshotSha256"])
        release_compile = compile_evidence["releaseCompile"]
        self.assertEqual("visible_metaeditor_exact_source", release_compile["mode"])
        self.assertEqual(0, release_compile["errors"])
        self.assertEqual(0, release_compile["warnings"])
        self.assertEqual(manifest["MetafxHQTradeGateway.mq4"], release_compile["sourceSha256"])
        self.assertEqual(manifest["MetafxHQTradeGateway.ex4"], release_compile["binarySha256"])
        self.assertEqual(b"\x89PNG\r\n\x1a\n", (ARTIFACT / "COMPILE_PROOF.png").read_bytes()[:8])

        build_log = (ARTIFACT / "BUILD_LOG.txt").read_text(encoding="utf-8")
        self.assertIn("PackageVersion: 2.18", build_log)
        self.assertIn("CompileResult: PASS", build_log)
        self.assertIn("CompileErrors: 0", build_log)
        self.assertIn("CompileWarnings: 0", build_log)
        self.assertIn("ReleaseCompileResult: PASS", build_log)
        self.assertIn("ReleaseCompileErrors: 0", build_log)
        self.assertIn("ReleaseCompileWarnings: 0", build_log)
        self.assertIn(f"SourceSHA256: {manifest['MetafxHQTradeGateway.mq4']}", build_log)
        self.assertIn(f"BinarySHA256: {manifest['MetafxHQTradeGateway.ex4']}", build_log)
        self.assertIn(f"CompileProofSHA256: {manifest['COMPILE_PROOF.png']}", build_log)
        self.assertIsNone(re.search(r"(?i)(?:[A-Z]:\\|/Users/|/home/)", build_log))

    def test_installer_requires_and_verifies_all_v218_release_evidence(self) -> None:
        installer = (ROOT / "installer" / "install.ps1").read_text(encoding="utf-8-sig")
        for filename in (
            "MetafxHQTradeGateway.mq4",
            "MetafxHQTradeGateway.ex4",
            "README_TH.md",
            "AUDIT_TH.md",
            "SHA256SUMS.txt",
            "BUILD_LOG.txt",
            "MANIFEST.json",
            "COMPILE_PROOF.png",
        ):
            self.assertIn(
                f"artifacts\\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness\\{filename}",
                installer,
            )
        self.assertIn("Assert-EaArtifactIntegrity", installer)
        self.assertIn("Assert-NoEmbeddedHighConfidenceSecrets", installer)
        self.assertIn("function Get-Sha256Hex", installer)
        self.assertIsNone(re.search(r"(?m)^[^#\r\n]*\bGet-FileHash\b", installer))
        self.assertIn("$artifactSourceHash = Get-Sha256Hex -LiteralPath $artifactSource", installer)
        self.assertIn("หลักฐาน Compile ของ EA ไม่ตรงกับ Source/Binary", installer)
        self.assertIn("MANIFEST/Compile proof ของ EA v2.18", installer)
        self.assertIn('install_root = "%LOCALAPPDATA%\\Metafxclub\\AI-Agent-HQ"', installer)
        self.assertIn("install_scope = \"current_windows_user\"", installer)

    def test_prompt_clone_mode_is_enforced_again_by_installer(self) -> None:
        installer = (ROOT / "installer" / "install.ps1").read_text(encoding="utf-8-sig")
        for parameter in (
            "ExpectedGitRepository",
            "ExpectedGitTag",
            "ExpectedSourceVersion",
            "ExpectedGitCommit",
        ):
            self.assertIn(f"[string]${parameter}", installer)
        self.assertIn("[switch]$RequireVerifiedGitSource", installer)
        self.assertIn("function Assert-ExpectedGitSource", installer)
        self.assertIn("https://github.com/metafxclub/metafxclub-ai-agent-hq.git", installer)
        provenance = installer[
            installer.index("function Assert-ExpectedGitSource"):
            installer.index("function Assert-SafeSource")
        ]
        self.assertIn('Test-Path -LiteralPath $gitDirectory', provenance)
        self.assertIn('@("remote", "get-url", "origin")', provenance)
        self.assertIn('"refs/tags/$($ExpectedGitTag.Trim())^{commit}"', provenance)
        self.assertIn('@("rev-parse", "--verify", "HEAD^{commit}")', provenance)
        self.assertIn('@("branch", "--show-current")', provenance)
        self.assertIn('@("status", "--porcelain", "--untracked-files=all")', provenance)
        self.assertIn('"ls-remote", "--exit-code", "--tags", $officialRepository', provenance)
        self.assertIn("Git HEAD ไม่ตรงกับ Tag ที่เผยแพร่บน GitHub ทางการ", provenance)
        self.assertIn('@("ls-files", "-v")', provenance)
        self.assertIn("--absolute-git-dir", provenance)
        self.assertIn("--no-replace-objects", installer)
        self.assertIn("Source ต้อง Checkout จาก Tag แบบ detached", provenance)
        self.assertIn("Source มีไฟล์แก้ไขหรือไฟล์ใหม่ที่ไม่อยู่ใน Tag", provenance)
        self.assertIn("VERSION ใน Source ไม่ตรงกับ Version ที่ล็อกไว้", provenance)
        self.assertIn("$script:validatedSourceCommit", provenance)
        self.assertIn("if ($PrePublishVerification)", provenance)
        self.assertIn("Git HEAD ไม่ตรงกับ Commit ของ Workflow", provenance)
        safe_source = installer[
            installer.index("function Assert-SafeSource"):
            installer.index("function Assert-EaArtifactIntegrity")
        ]
        self.assertIn("Assert-ExpectedGitSource", safe_source)
        self.assertIn(
            '"backend\\local-runner\\ea_factory_indicator_coverage.py"',
            safe_source,
        )
        self.assertIn(
            '"backend\\local-runner\\ea_factory_metaeditor_compile.py"',
            safe_source,
        )
        self.assertIn(
            '"backend\\local-runner\\ea_factory_visible_terminal.py"',
            safe_source,
        )
        self.assertIn(
            '"backend\\local-runner\\ea_factory_visible_terminal.ps1"',
            safe_source,
        )
        self.assertIn(
            '"backend\\local-runner\\ea_strategy_brief.py"',
            safe_source,
        )
        self.assertIn("function Export-VerifiedGitSource", installer)
        self.assertIn('"archive", "--format=zip"', installer)
        self.assertIn("Export-VerifiedGitSource -DestinationRoot $stagingRoot", installer)
        self.assertIn('"verified_official_commit_pre_release"', installer)
        self.assertIn('"verified_remote_git_tag"', installer)
        self.assertIn('"unverified_archive_or_local_source"', installer)

    def test_installer_stages_before_mutation_and_restores_last_good_on_failure(self) -> None:
        installer = (ROOT / "installer" / "install.ps1").read_text(encoding="utf-8-sig")
        self.assertLess(installer.index("$stagingRoot = New-StagedApplication"), installer.index("$script:applicationMutationStarted = $true"))
        self.assertLess(installer.index("$stagingRoot = New-StagedApplication"), installer.index("$bridgeTaskWasEnabled = Suspend-BridgeScheduledTask"))
        normal_flow_start = installer.index("$previousBridgeEndpointState = Get-SavedBridgeEndpointState")
        self.assertLess(
            installer.index("$script:applicationRollbackState = New-ApplicationRollbackSnapshot", normal_flow_start),
            installer.index("Publish-StagedApplication -StagingRoot $stagingRoot", normal_flow_start),
        )
        self.assertIn("Restore-ApplicationRollbackSnapshot -RollbackState", installer)
        self.assertIn("Remove-ApplicationRollbackSnapshot -RollbackState", installer)
        self.assertIn("if ($rollbackRestored)", installer)
        self.assertIn("เก็บ Last-good ไว้ที่ $recoveryPath", installer)
        self.assertIn("Start-PreviousBridgeAfterRollback", installer)
        self.assertIn("if ($bridgeEndpoint)", installer)
        self.assertIn("$rollbackRestored -and $previousBridgeWasRunning", installer)
        self.assertIn("$script:previousBridgeWasStopped -and $previousBridgeWasRunning", installer)
        self.assertIn("$previousBridgeEndpointState = Get-SavedBridgeEndpointState", installer)
        self.assertIn("$previousBridgeWasHealthy = [bool]$previousBridgeEndpointState.Healthy", installer)
        self.assertIn("Start-PreviousDegradedBridgeAfterRollback", installer)
        self.assertIn("Get-InstalledBridgeListenerIdentity", installer)
        self.assertIn("Stop-CandidateBridgeAfterFailedStart", installer)
        self.assertIn('$health.server -ceq "Metafx Local Bridge"', installer)
        self.assertIn("$health.version -ceq $installedVersion", installer)
        self.assertIn("<title>Metafxclub AI Agent HQ", installer)
        self.assertIn("frontend/index\\.html", installer)
        self.assertIn('$frontendAppUrl = "{0}frontend/index.html"', installer)
        self.assertIn("<title>Metafxclub AI Pixel HQ", installer)
        self.assertIn("frontend/src/app/main\\.js", installer)
        self.assertIn('$mainJsUrl = "{0}frontend/src/app/main.js"', installer)
        self.assertIn("window\\.MetafxHqBoot", installer)
        self.assertIn("init\\(\\)\\.catch", installer)
        self.assertIn("struct.calcsize('P')*8", installer)
        self.assertIn("[int]$details.bits -ne 64", installer)
        candidate_stop = installer[
            installer.index("function Stop-CandidateBridgeAfterFailedStart"):
            installer.index("function Start-PreviousBridgeAfterRollback")
        ]
        self.assertIn("Get-NetTCPConnection", candidate_stop)
        self.assertIn("ไม่เขียนทับไฟล์ระหว่าง Rollback", candidate_stop)
        self.assertLess(
            installer.index("elseif (-not (Get-ComparablePath -Path $sourceRoot).Equals"),
            installer.index("$bridgeTaskWasEnabled = Suspend-BridgeScheduledTask"),
        )
        suspend = installer[
            installer.index("function Suspend-BridgeScheduledTask"):
            installer.index("function Restore-BridgeScheduledTask")
        ]
        self.assertIn("$taskWasDisabled = $true", suspend)
        self.assertIn("Enable-ScheduledTask -TaskName $bridgeTaskName", suspend)
        self.assertIn("Test-InstalledApplication -PythonPath", installer)
        self.assertIn('"--require-hashes"', installer)
        dependency_setup = installer[
            installer.index("function Initialize-PythonEnvironment"):
            installer.index("function Test-InstalledApplication")
        ]
        self.assertIn("Assert-PipBootstrapWheel -CandidateRoot $installRoot", dependency_setup)
        self.assertIn('"--no-index", "--no-deps", "--upgrade", $pipBootstrapWheel', dependency_setup)
        self.assertIn('"--only-binary=:all:"', dependency_setup)
        self.assertIn('"https://pypi.org/simple"', dependency_setup)
        self.assertIn('print(pip.__version__)', dependency_setup)
        self.assertIn("Windows certificate store", dependency_setup)
        clean_pip = installer[
            installer.index("function Invoke-PipWithCleanConfiguration"):
            installer.index("function Get-Sha256Hex")
        ]
        self.assertIn('$_.Name -like "PIP_*"', clean_pip)
        self.assertIn('$env:PIP_CONFIG_FILE = "nul"', clean_pip)
        self.assertIn('Remove-Item -LiteralPath $environmentPath -Force', clean_pip)
        for certificate_override in (
            "REQUESTS_CA_BUNDLE",
            "CURL_CA_BUNDLE",
            "SSL_CERT_FILE",
            "SSL_CERT_DIR",
        ):
            self.assertIn(certificate_override, clean_pip)
        self.assertLess(
            dependency_setup.index('"--no-index"'),
            dependency_setup.index('"https://pypi.org/simple"'),
        )
        for unsafe_option in ("--trusted-host", "legacy-certs", "PIP_TRUSTED_HOST"):
            self.assertNotIn(unsafe_option, dependency_setup)
        installed_check = installer[
            installer.index("function Test-InstalledApplication"):
            installer.index("function Test-GoogleOAuthDeploymentConfigured")
        ]
        self.assertIn('"tests.test_release_candidate_preflight"', installed_check)
        self.assertIn('"backend\\local-runner\\bridge_server.py", "--help"', installed_check)
        self.assertIn('"runner\\codex_cli_runner.py", "--help"', installed_check)
        self.assertNotIn('"discover"', installed_check)
        staged = installer[installer.index("function New-StagedApplication"):installer.index("function Publish-StagedApplication")]
        self.assertIn("Resolve-SystemPython", staged)
        self.assertIn('"tests.test_release_candidate_preflight"', staged)
        self.assertNotIn('"discover"', staged)
        self.assertNotIn(r'runner\.venv\Scripts\python.exe', staged)

        requirements = (ROOT / "requirements-runner.txt").read_text(encoding="utf-8")
        self.assertGreaterEqual(requirements.count("--hash=sha256:"), 11)
        requirement_blocks = [block for block in re.split(r"\n(?=[A-Za-z0-9_.-]+==)", requirements) if "==" in block]
        self.assertEqual(8, len(requirement_blocks))
        self.assertTrue(all("--hash=sha256:" in block for block in requirement_blocks))
        self.assertIn("[int]$details.minor -gt 14", installer)
        for selector in ("-3.14", "-3.13", "-3.12", "-3.11", "-3.10"):
            self.assertIn(f'"{selector}"', installer)
        self.assertLess(installer.index('"-3.14"'), installer.index('"-3.10"'))
        self.assertIn("[switch]$PackageSmoke", installer)
        main_entry = installer.index("try {\n    # Validate explicit classroom onboarding inputs")
        smoke = installer[
            installer.index("if ($PackageSmoke) {", main_entry):
            installer.index("$previousBridgeEndpointState = Get-SavedBridgeEndpointState")
        ]
        self.assertIn("Publish-StagedApplication", smoke)
        self.assertIn("Test-InstalledApplication", smoke)
        self.assertIn("Test-IsolatedInstalledBridge", smoke)
        self.assertNotIn("Suspend-BridgeScheduledTask", smoke)
        self.assertNotIn("Stop-ExistingBridge", smoke)
        self.assertIn('$env:GITHUB_ACTIONS -cne "true"', smoke)
        self.assertIn("$localAppDataFull.StartsWith($runnerTempFull", smoke)
        isolated_smoke = installer[
            installer.index("function Test-IsolatedInstalledBridge"):
            installer.index("function New-HqShortcut")
        ]
        self.assertIn("Start-And-TestBridge", isolated_smoke)
        self.assertIn("Invoke-WebRequest", isolated_smoke)
        self.assertIn("Invoke-BridgeLifecycleProcess -Action Stop", isolated_smoke)
        lifecycle_process = installer[
            installer.index("function Invoke-BridgeLifecycleProcess"):
            installer.index("function Test-IsolatedInstalledBridge")
        ]
        self.assertIn("Start-Process", lifecycle_process)
        self.assertIn("-WindowStyle Hidden", lifecycle_process)
        self.assertIn("-PassThru", lifecycle_process)
        self.assertIn("$process.WaitForExit(60000)", lifecycle_process)
        self.assertNotIn("-Wait `", lifecycle_process)
        self.assertNotIn("| Out-Host", lifecycle_process)
        self.assertIn("$script:rollbackIncomplete = $true", installer)
        finally_block = installer[
            installer.rindex("    finally {"):
            installer.index("    Write-Step \"ติดตั้ง Runtime และตรวจ Health สำเร็จ")
        ]
        self.assertIn("if ($script:rollbackIncomplete)", finally_block)
        self.assertIn("คง Watchdog ไว้ในสถานะปิด", finally_block)

    def test_installer_scans_the_exact_staged_text_boundary(self) -> None:
        installer = (ROOT / "installer" / "install.ps1").read_text(encoding="utf-8-sig")
        secret_gate = installer[
            installer.index("function Assert-NoEmbeddedHighConfidenceSecrets"):
            installer.index("function Suspend-BridgeScheduledTask")
        ]
        self.assertIn('param([string]$CandidateRoot = $sourceRoot)', secret_gate)
        self.assertIn('".github"', secret_gate)
        self.assertIn('"tests"', secret_gate)
        for filename in (
            "index.html",
            "Open Metafx Agent HQ.cmd",
            "1-INSTALL-HQ.bat",
            "2-SETUP-GOOGLE-HQ.bat",
            "UPDATE-HQ.bat",
            "REPAIR-HQ.bat",
            "UNINSTALL-HQ.bat",
            "LICENSE",
            "LICENSE.md",
            "$requirementsName",
        ):
            self.assertIn(filename, secret_gate)
        staged = installer[
            installer.index("function New-StagedApplication"):
            installer.index("function Publish-StagedApplication")
        ]
        self.assertIn("Assert-NoEmbeddedHighConfidenceSecrets -CandidateRoot $stagingRoot", staged)

        verified_export = installer[
            installer.index("function Export-VerifiedGitSource") :
            installer.index("function Get-InstallerTemporaryParent")
        ]
        self.assertIn(
            "Assert-CentralGoogleOAuthPublicClient -CandidateRoot $sourceRoot",
            verified_export,
        )
        self.assertIn(
            "$centralClientSource = Join-Path $sourceRoot $centralGoogleOAuthClientRelativePath",
            verified_export,
        )
        self.assertIn(
            "$centralClientDestination = Join-Path $DestinationRoot $centralGoogleOAuthClientRelativePath",
            verified_export,
        )
        self.assertEqual(
            verified_export.count("Copy-Item"),
            1,
            "verified staging may copy only the separately validated central client outside git archive",
        )
        self.assertLess(
            verified_export.index("Assert-CentralGoogleOAuthPublicClient -CandidateRoot $sourceRoot"),
            verified_export.index("Copy-Item"),
        )
        self.assertLess(
            verified_export.index("Copy-Item"),
            verified_export.index("Assert-CentralGoogleOAuthPublicClient -CandidateRoot $DestinationRoot"),
        )

        copy_scope = installer[
            installer.index("function Copy-ApplicationFiles"):
            installer.index("function Stop-CandidateBridgeAfterFailedStart")
        ]
        sync_scope = installer[
            installer.index("function Sync-Directory"):
            installer.index("function Copy-ApplicationFiles")
        ]
        publish_scope = installer[
            installer.index("function Publish-StagedApplication"):
            installer.index("function New-ApplicationRollbackSnapshot")
        ]
        self.assertIn('".github"', copy_scope)
        self.assertIn('".github"', publish_scope)
        self.assertNotIn('"*secret*"', sync_scope)
        self.assertIn('"*secret*.json"', sync_scope)
        self.assertIn('"*.dpapi"', sync_scope)
        self.assertIn('"2-SETUP-GOOGLE-HQ.bat"', copy_scope)
        self.assertIn('"scripts\\setup-google-oauth.ps1"', installer)
        self.assertIn('"backend\\local-runner\\google_oauth_native_client.txt"', installer)
        self.assertIn('"tests\\release_secret_scan.py"', installer)
        self.assertIn('"tests\\test_release_candidate_preflight.py"', installer)
        for google_secret_pattern in ("GOCSPX-", "1//", "ya29"):
            with self.subTest(google_secret_pattern=google_secret_pattern):
                self.assertIn(google_secret_pattern, secret_gate)
        central_validator = installer[
            installer.index("function Assert-CentralGoogleOAuthPublicClient") :
            installer.index("function Assert-GoogleOAuthOneRunInputs")
        ]
        self.assertIn("$centralGoogleOAuthClientRelativePath", central_validator)
        self.assertIn("client_id=", central_validator)
        self.assertIn("client_secret=", central_validator)
        self.assertIn("GOCSPX-", central_validator)
        self.assertIn("$lines.Count -ne 2", central_validator)
        self.assertIn("New-Object Text.UTF8Encoding($false, $true)", central_validator)

        exclude_match = re.search(r'"/XF",(?P<filters>.*?)\r?\n\s*"/XD"', sync_scope, re.DOTALL)
        self.assertIsNotNone(exclude_match)
        exclude_patterns = re.findall(r'"([^"]+)"', exclude_match.group("filters"))
        for safe_source_name in (
            "release_secret_scan.py",
            "test_release_secret_hygiene.py",
            "google_oauth_native_client.txt",
            "google_oauth_store.py",
        ):
            with self.subTest(safe_source_name=safe_source_name):
                self.assertFalse(
                    any(
                        fnmatch.fnmatchcase(safe_source_name.lower(), pattern.lower())
                        for pattern in exclude_patterns
                    )
                )
        for credential_name in (
            "client_secret_download.json",
            "google-oauth-client.json",
            "service_account.json",
            "auth.json",
            "refresh_token.json",
            "private.pem",
            "oauth-cache.dpapi",
        ):
            with self.subTest(credential_name=credential_name):
                self.assertTrue(
                    any(
                        fnmatch.fnmatchcase(credential_name.lower(), pattern.lower())
                        for pattern in exclude_patterns
                    )
                )

    def test_watchdog_is_verified_and_reports_partial_without_runtime_rollback(self) -> None:
        installer = (ROOT / "installer" / "install.ps1").read_text(encoding="utf-8-sig")
        verifier = installer[
            installer.index("function Assert-BridgeScheduledTaskReady"):
            installer.index("function Rebind-BridgeScheduledTask")
        ]
        self.assertIn('MSFT_TaskLogonTrigger', verifier)
        self.assertIn('MSFT_TaskTimeTrigger', verifier)
        self.assertIn('Repetition.Interval', verifier)
        self.assertIn('System32\\wscript.exe', verifier)
        self.assertIn('run-bridge-watchdog-hidden.vbs', verifier)
        self.assertIn("$expectedArguments", verifier)
        self.assertIn("WorkingDirectory", verifier)
        self.assertIn("bridge-autostart.json", verifier)
        self.assertIn("$state.confirmed_port -ne $ConfirmedPort", verifier)

        onboarding = installer[
            installer.index("# Watchdog and Google setup are non-transactional onboarding"):
            installer.index("if (-not $SkipShortcuts)", installer.index("# Watchdog and Google setup are non-transactional onboarding"))
        ]
        self.assertIn('$watchdogStatus = "repair_required"', onboarding)
        self.assertIn('$watchdogFailure = $true', onboarding)
        self.assertIn("$postInstallFailures.Add", onboarding)
        self.assertIn("Assert-BridgeScheduledTaskReady", installer)
        self.assertLess(
            installer.index("$script:applicationRollbackState = $null"),
            installer.index('$watchdogStatus = "repair_required"'),
        )

        result_writer = installer[
            installer.index("function Write-InstallResult"):
            installer.index("try {", installer.index("function Write-InstallResult"))
        ]
        self.assertIn("post_install", result_writer)
        self.assertIn("repair_command", result_writer)
        self.assertIn("PostInstallExitCode", result_writer)
        self.assertIn('status = $WatchdogStatus', result_writer)
        self.assertIn('2=Google, 3=Watchdog, 4=ทั้งสองส่วน', installer)
        self.assertIn('exit $postInstallExitCode', installer)
        restore_finally = installer[
            installer.rindex("    finally {"):
            installer.index('$postInstallExitCode = if ($watchdogFailure', installer.rindex("    finally {"))
        ]
        self.assertIn("Restore-BridgeScheduledTask", restore_finally)
        self.assertIn("if ($bridgeEndpoint -and -not $script:applicationMutationStarted)", restore_finally)
        self.assertIn('$watchdogStatus = "repair_required"', restore_finally)
        self.assertLess(
            installer.rindex("    finally {"),
            installer.index("Write-InstallResult", installer.rindex("    finally {")),
        )

        prompt = (ROOT / "docs" / "prompts" / "install-github-google-auto-th.md").read_text(encoding="utf-8")
        self.assertIn("2=Google OAuth", prompt)
        self.assertIn("3=Watchdog", prompt)
        self.assertIn("4=ทั้ง Google OAuth กับ Watchdog", prompt)
        self.assertIn("-RepairOnly -Port <PORT> -EndpointConfirmed -SkipGoogleSetup -SkipShortcuts", prompt)
        self.assertIn('post_install.watchdog.status="ready"', prompt)

    def test_release_workflow_never_skips_current_archive_smoke(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "publish-release.yml").read_text(encoding="utf-8")
        regression_runner = (ROOT / "scripts" / "run-regression-suite.ps1").read_text(
            encoding="utf-8"
        )
        verify_step = workflow[
            workflow.index("- name: Verify safe runtime"):
            workflow.index("- name: Build release package")
        ]
        self.assertIn("Python regression suite failed with exit code", verify_step)
        self.assertIn("Frontend syntax check failed with exit code", verify_step)
        self.assertIn("python -m venv runner/.venv", verify_step)
        self.assertIn("--no-index --no-deps --upgrade $pipWheel", verify_step)
        self.assertIn("Expected verified pip 26.2.1", verify_step)
        self.assertIn("--index-url https://pypi.org/simple --require-hashes --only-binary=:all: --requirement requirements-runner.txt", verify_step)
        self.assertIn("$env:PIP_CONFIG_FILE = \"nul\"", verify_step)
        self.assertIn("-m pip check", verify_step)
        self.assertIn(r".\scripts\run-regression-suite.ps1", verify_step)
        self.assertIn(
            '& $resolvedPython -m unittest discover -s tests -p "test_*.py" -v',
            regression_runner,
        )
        self.assertIn('$previousErrorActionPreference = $ErrorActionPreference', regression_runner)
        self.assertIn('$ErrorActionPreference = "Continue"', regression_runner)
        self.assertIn('$ErrorActionPreference = $previousErrorActionPreference', regression_runner)
        self.assertIn("Regression suite failed::", regression_runner)
        self.assertIn("FAIL|ERROR", regression_runner)
        self.assertGreaterEqual(verify_step.count("$LASTEXITCODE -ne 0"), 2)
        self.assertIn("Always build and smoke-test the exact current archive", workflow)
        self.assertIn("git archive --format=zip", workflow)
        self.assertIn(
            "METAFX_GOOGLE_OAUTH_DESKTOP_CLIENT_ID: ${{ secrets.METAFX_GOOGLE_OAUTH_DESKTOP_CLIENT_ID }}",
            workflow,
        )
        self.assertIn(
            "METAFX_GOOGLE_OAUTH_DESKTOP_CLIENT_SECRET: ${{ secrets.METAFX_GOOGLE_OAUTH_DESKTOP_CLIENT_SECRET }}",
            workflow,
        )
        injection = workflow[
            workflow.index("$sourceArchive =") :
            workflow.index("# Test the exact ZIP layout")
        ]
        self.assertIn("--output=$sourceArchive HEAD", injection)
        self.assertIn("Expand-Archive -LiteralPath $sourceArchive", injection)
        self.assertIn(r"backend\local-runner\google_oauth_native_client.txt", injection)
        self.assertIn("client_id=$($env:METAFX_GOOGLE_OAUTH_DESKTOP_CLIENT_ID)", injection)
        self.assertIn("client_secret=$($env:METAFX_GOOGLE_OAUTH_DESKTOP_CLIENT_SECRET)", injection)
        self.assertIn("New-Object Text.UTF8Encoding($false)", injection)
        self.assertIn("[IO.File]::WriteAllText($injectedClientPath", injection)
        self.assertIn("Compress-Archive -LiteralPath $injectedPackageRoot", injection)
        self.assertLess(injection.index("git archive --format=zip"), injection.index("client_id=$($env:"))
        self.assertLess(injection.index("client_id=$($env:"), injection.index("Get-FileHash -LiteralPath $archive"))
        self.assertNotIn("--output=$archive HEAD", injection)
        self.assertGreaterEqual(
            workflow.count('"backend\\local-runner\\ea_strategy_brief.py"'),
            2,
        )
        self.assertIn("legacy-listener upgrade smoke failed", workflow)
        self.assertIn('runner\\.venv\\Scripts\\python.exe', workflow)
        self.assertIn("print(sys._base_executable)", workflow)
        self.assertIn("$fixturePythonProbe.Count -ne 1", workflow)
        self.assertIn("-PythonPath $fixturePythonPath", workflow)
        self.assertIn("-FilePath $PythonPath", workflow)
        self.assertNotIn("Get-Command python.exe -CommandType Application", workflow)
        self.assertNotIn("function Test-ProcessDescendsFrom", workflow)
        self.assertIn("[int]$listenerIds[0] -eq [int]$process.Id", workflow)
        self.assertIn("function Stop-DegradedFixture", workflow)
        self.assertIn("$FixtureProcess.Kill()", workflow)
        self.assertIn("if (-not $FixtureProcess.WaitForExit(10000))", workflow)
        self.assertIn("FIXTURE_CLEANUP_UNCONFIRMED", workflow)
        self.assertGreaterEqual(
            workflow.count(
                '$_.Exception.Message -ceq "FIXTURE_CLEANUP_UNCONFIRMED"'
            ),
            2,
        )
        self.assertGreaterEqual(
            workflow.count("Stop-DegradedFixture -FixtureProcess $foreignProcess"), 2
        )
        self.assertIn("$foreignAttempt -le 5", workflow)
        self.assertIn("$legacyAttempt -le 5", workflow)
        self.assertIn("$legacyProcess = $null", workflow)
        self.assertIn("Stop-DegradedFixture -FixtureProcess $legacyProcess", workflow)
        self.assertIn("$cleanupFailures.Add(\"foreign-fixture\")", workflow)
        self.assertIn("$cleanupFailures.Add(\"legacy-fixture\")", workflow)
        self.assertIn("$env:LOCALAPPDATA = $originalLocalAppData", workflow)
        self.assertIn("Release fixture cleanup was not confirmed", workflow)
        self.assertIn("Bump VERSION instead of reusing the tag", workflow)
        self.assertIn(
            '"backend\\local-runner\\ea_factory_indicator_coverage.py"',
            workflow,
        )
        self.assertIn(
            '"backend\\local-runner\\ea_factory_metaeditor_compile.py"',
            workflow,
        )
        self.assertGreaterEqual(
            workflow.count(
                '"backend\\local-runner\\ea_factory_visible_terminal.py"'
            ),
            2,
        )
        self.assertGreaterEqual(
            workflow.count(
                '"backend\\local-runner\\ea_factory_visible_terminal.ps1"'
            ),
            2,
        )
        self.assertIn("gh release upload $tag $archive $checksum", workflow)
        self.assertIn("--clobber", workflow)
        self.assertIn("gh api \"repos/$env:GITHUB_REPOSITORY/releases/tags/$tag\"", workflow)
        self.assertIn("gh api --paginate", workflow)
        self.assertIn('releases?per_page=100', workflow)
        self.assertIn("--jq '.[].tag_name'", workflow)
        self.assertIn("$releaseListExit = $LASTEXITCODE", workflow)
        self.assertIn("$releaseListExit -ne 0", workflow)
        self.assertIn("[string]$_ -ceq $tag", workflow)
        self.assertIn("$matchingReleaseTags.Count -gt 1", workflow)
        self.assertIn("$matchingReleaseTags.Count -eq 1", workflow)
        self.assertIn("Unable to list existing GitHub Releases", workflow)
        self.assertIn("was listed but its exact API record could not be read", workflow)
        self.assertNotIn("Get-GitHubApiHttpStatus", workflow)
        self.assertIn("::error title=Build release package failed::", workflow)
        self.assertLess(
            workflow.index("gh api --paginate"),
            workflow.index('gh api "repos/$env:GITHUB_REPOSITORY/releases/tags/$tag"'),
        )
        self.assertIn("$releaseCreationAmbiguous = $true", workflow)
        self.assertIn("$createdReleaseProbeAttempt -le 5", workflow)
        self.assertIn("$createdReleasePayload.tag_name -ceq $tag", workflow)
        self.assertIn("could not be created or confirmed through the GitHub API; preserving its tag", workflow)
        ambiguous_failure = workflow[
            workflow.index("if (-not $createdReleaseFound)"):
            workflow.index("gh release upload $tag $archive $checksum", workflow.index("if (-not $createdReleaseFound)"))
        ]
        self.assertNotIn("$releaseCreationAmbiguous = $false", ambiguous_failure)
        self.assertIn("was created after an ambiguous CLI response", workflow)
        self.assertIn("gh release download $tag", workflow)
        self.assertIn("$releaseDownloadAttempt -le 8", workflow)
        self.assertIn("Release assets are not readable with the expected checksum yet", workflow)
        self.assertIn("Start-Sleep -Seconds 5", workflow)
        self.assertIn("if (-not $releaseDownloadReady)", workflow)
        download_loop = workflow[
            workflow.index("for ($releaseDownloadAttempt = 1;"):
            workflow.index("if (-not $releaseDownloadReady)")
        ]
        self.assertIn("Remove-Item -LiteralPath $remoteArchive", download_loop)
        self.assertIn("Remove-Item -LiteralPath $remoteChecksum", download_loop)
        self.assertIn("$releaseDownloadExitCode = $LASTEXITCODE", download_loop)
        self.assertIn("$releaseDownloadExitCode -eq 0", download_loop)
        self.assertIn("Get-FileHash -LiteralPath $remoteArchive", download_loop)
        self.assertIn("Get-Content -LiteralPath $remoteChecksum", download_loop)
        self.assertIn("-ErrorAction Stop", download_loop)
        self.assertIn("Release asset read failed during verification attempt", download_loop)
        self.assertIn("$remoteHash -ceq $hash", download_loop)
        self.assertIn('$remoteChecksumLine -ceq "$hash  $archive"', download_loop)
        self.assertIn("could not be downloaded with the verified local package checksum", workflow)
        self.assertIn("Release $tag verified", workflow)
        self.assertIn("-PackageSmoke", workflow)
        self.assertIn("Verified Git Runtime central OAuth status probe failed", workflow)
        build_step = workflow[
            workflow.index("      - name: Build release package") :
        ]
        self.assertEqual(build_step.count("\n        env:\n"), 1)
        self.assertIn("          GH_TOKEN: ${{ github.token }}", build_step)
        self.assertNotIn("\nimport json\n", workflow)
        self.assertIn(
            "\n          import json\n"
            "          import os\n"
            "          import sys\n"
            '          sys.path.insert(0, os.environ["METAFX_VERIFIED_RUNNER_PATH"])\n'
            "          import google_sheet_hub\n"
            "          print(json.dumps(google_sheet_hub.google_oauth_status(), sort_keys=True))\n"
            "          '@ 2>$null) | Select-Object -Last 1\n",
            workflow,
        )
        self.assertIn("$verifiedAuth.clientConfigured -ne $true", workflow)
        self.assertIn("$verifiedAuth.connected -ne $false", workflow)
        self.assertIn('[string]$verifiedAuth.status -cne "authorization_required"', workflow)
        self.assertIn('[string]$verifiedAuth.clientSource -cne "central_release"', workflow)
        self.assertIn("Verified Git Runtime central OAuth clean-profile contract failed", workflow)
        self.assertIn("https://github.com/metafxclub/metafxclub-ai-agent-hq.git", workflow)
        self.assertIn("git -C $verifiedClone fetch --depth 1 origin $env:GITHUB_SHA", workflow)
        self.assertIn("git -C $verifiedClone checkout --detach $env:GITHUB_SHA", workflow)
        verified_clone_setup = workflow[
            workflow.index("$verifiedCentralClient = Join-Path $verifiedClone") :
            workflow.index("$verifiedListener =", workflow.index("$verifiedCentralClient = Join-Path $verifiedClone"))
        ]
        self.assertIn(
            r'Join-Path $packageRoot "backend\local-runner\google_oauth_native_client.txt"',
            verified_clone_setup,
        )
        self.assertIn("Copy-Item", verified_clone_setup)
        self.assertIn(
            'git -C $verifiedClone check-ignore --quiet -- "backend/local-runner/google_oauth_native_client.txt"',
            verified_clone_setup,
        )
        self.assertIn("-PrePublishVerification", workflow)
        self.assertIn("-ExpectedGitCommit $env:GITHUB_SHA", workflow)
        self.assertLess(
            workflow.index("Verified official-commit installation smoke failed"),
            workflow.index('git push origin "refs/tags/$tag`:refs/tags/$tag"'),
        )
        self.assertIn("-RequireVerifiedGitSource", workflow)
        self.assertIn("-ExpectedGitRepository $officialRepository", workflow)
        self.assertIn("-ExpectedGitTag $tag", workflow)
        self.assertIn("-ExpectedSourceVersion $version", workflow)
        self.assertIn("ci-ignored-source-sentinel.txt", workflow)
        self.assertIn("Verified official-commit installation smoke failed", workflow)
        self.assertIn("Installer accepted a foreign HTTP 503 listener", workflow)
        self.assertIn("PackageSmokeFailAfterPublish", workflow)
        self.assertIn("Last-good VERSION was not restored", workflow)
        self.assertIn("Assert-DegradedFixture -Port $smokePort", workflow)
        self.assertIn("gh release delete $tag", workflow)
        cleanup = workflow[workflow.index("          catch {") :]
        self.assertNotIn("--cleanup-tag", cleanup)
        self.assertIn("if ($releaseCreatedByThisRun)", cleanup)
        self.assertIn("$releaseRemovedOrNeverCreated = -not $releaseCreatedByThisRun", cleanup)
        self.assertIn("if ($LASTEXITCODE -eq 0)", cleanup)
        self.assertIn("cleanup failed; preserving its Git tag", cleanup)
        self.assertIn("if ($tagCreatedByThisRun -and $releaseRemovedOrNeverCreated)", cleanup)
        self.assertIn("-not $releaseCreationAmbiguous", cleanup)
        self.assertLess(
            cleanup.index("gh release delete $tag"),
            cleanup.index('git push origin ":refs/tags/$tag"'),
        )
        self.assertIn("context=metafxclub/release", workflow)
        trigger = workflow[: workflow.index("permissions:")]
        self.assertNotIn("paths:", trigger)
        ref_guard = workflow[
            workflow.index("  release_ref_guard:"):
            workflow.index("  compatibility:")
        ]
        self.assertIn('if ($env:GITHUB_REF -cne "refs/heads/main")', ref_guard)
        self.assertIn("Release publishing is allowed only from refs/heads/main", ref_guard)
        compatibility_header = workflow[
            workflow.index("  compatibility:"):
            workflow.index("    strategy:", workflow.index("  compatibility:"))
        ]
        self.assertIn("needs: release_ref_guard", compatibility_header)
        self.assertIn("timeout-minutes: 30", compatibility_header)
        self.assertLess(
            workflow.index("  release_ref_guard:"),
            workflow.index("  compatibility:"),
        )
        self.assertLess(
            workflow.index("  compatibility:"),
            workflow.index("  publish:"),
        )
        self.assertIn("$existingReleaseNeedsPublish", workflow)
        self.assertIn("$releasePayload.draft -eq $true", workflow)
        self.assertIn("$releasePayload.published_at", workflow)
        self.assertIn("gh release edit $tag", workflow)
        self.assertIn("--draft=false", workflow)
        self.assertIn("$publishedRelease.draft -ne $false", workflow)
        self.assertIn("$publishedRelease.published_at", workflow)
        self.assertIn("$publishedArchiveAssets.Count -ne 1", workflow)
        self.assertIn("$publishedChecksumAssets.Count -ne 1", workflow)
        self.assertLess(
            workflow.index("Release $tag is not a published, non-draft Release"),
            workflow.index("context=metafxclub/release"),
        )
        self.assertIn("node --check (Join-Path $verifiedInstalledRoot", workflow)
        self.assertIn("actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd", workflow)
        self.assertIn("actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405", workflow)
        self.assertIn("Python 3.10-3.14", workflow)
        for filename in (
            "requirements-runner.txt",
            "installer\\bootstrap\\pip-26.2.1-py3-none-any.whl",
            "installer\\bootstrap\\README.md",
            "scripts\\start-local-bridge.ps1",
            "google_oauth_store.py",
            "google_sheet_hub.py",
            "google_oauth_native_client.txt",
            "ea-factory-contract.json",
            "research-sheet-hub-setup-th.md",
            "test_release_candidate_preflight.py",
            "legacy_degraded_bridge.py",
            "scripts\\run-bridge-watchdog-hidden.vbs",
            "MetafxHQTradeGateway.mq4",
            "MetafxHQTradeGateway.ex4",
            "README_TH.md",
            "AUDIT_TH.md",
            "SHA256SUMS.txt",
            "BUILD_LOG.txt",
        ):
            self.assertIn(filename, workflow)

        verify_workflow = (ROOT / ".github" / "workflows" / "verify.yml").read_text(encoding="utf-8")
        self.assertIn("actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd", verify_workflow)
        self.assertIn("actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405", verify_workflow)
        self.assertIn('python-version: ["3.10", "3.11", "3.12", "3.13", "3.14"]', verify_workflow)
        self.assertIn('python-version: ${{ matrix.python-version }}', verify_workflow)
        self.assertIn("timeout-minutes: 30", verify_workflow)
        self.assertIn('python-version: "3.11"', workflow)
        self.assertIn("needs: compatibility", workflow)
        self.assertIn('python-version: ["3.10", "3.11", "3.12", "3.13", "3.14"]', workflow)
        self.assertIn("Regression suite failed on Python ${{ matrix.python-version }}", workflow)
        self.assertGreaterEqual(workflow.count("Offline pip bootstrap SHA-256 mismatch"), 2)
        self.assertGreaterEqual(workflow.count("--no-index --no-deps --upgrade $pipWheel"), 2)
        self.assertGreaterEqual(workflow.count("--only-binary=:all:"), 2)
        self.assertGreaterEqual(workflow.count('$env:PIP_CONFIG_FILE = "nul"'), 2)
        self.assertGreaterEqual(workflow.count("-m pip check"), 2)
        self.assertIn("Offline pip bootstrap SHA-256 mismatch", verify_workflow)
        self.assertIn("--no-index --no-deps --upgrade $pipWheel", verify_workflow)
        self.assertIn("--only-binary=:all:", verify_workflow)
        self.assertIn('$env:PIP_CONFIG_FILE = "nul"', verify_workflow)
        self.assertIn("-m pip check", verify_workflow)
        for unsafe_option in ("--trusted-host", "legacy-certs", "PIP_TRUSTED_HOST"):
            self.assertNotIn(unsafe_option, workflow)
            self.assertNotIn(unsafe_option, verify_workflow)

    def test_degraded_endpoint_upgrade_is_exact_owned_and_foreign_fail_closed(self) -> None:
        installer = (ROOT / "installer" / "install.ps1").read_text(encoding="utf-8-sig")
        identity = installer[
            installer.index("function Get-InstalledBridgeListenerIdentity"):
            installer.index("function Get-SavedBridgeEndpointState")
        ]
        self.assertIn("Get-NetTCPConnection -LocalPort $CandidatePort -State Listen", identity)
        self.assertIn("$listenerIds.Count -ne 1", identity)
        self.assertIn("Get-CimInstance Win32_Process", identity)
        self.assertIn('Join-Path $installRoot "backend\\local-runner\\bridge_server.py"', identity)
        self.assertIn('$tokens[3] -cne "127.0.0.1"', identity)
        self.assertIn("$parsedPort -ne $CandidatePort", identity)

        endpoint_state = installer[
            installer.index("function Get-SavedBridgeEndpointState"):
            installer.index("function Get-HealthySavedEndpoint")
        ]
        self.assertLess(
            endpoint_state.index("Get-InstalledBridgeListenerIdentity"),
            endpoint_state.index("Invoke-RestMethod"),
        )
        self.assertIn("A 503 response is not sufficient proof of ownership", endpoint_state)
        self.assertIn("Health ยัง degraded", endpoint_state)
        self.assertIn("Running = $true", endpoint_state)

        requested = installer[
            installer.index("function Test-RequestedEndpointUsable"):
            installer.index("function Confirm-BridgeEndpoint")
        ]
        self.assertIn("Get-SavedBridgeEndpointState", requested)
        self.assertIn("Test-LoopbackPortAvailable", requested)

        task_suspend = installer[
            installer.index("function Suspend-BridgeScheduledTask") :
            installer.index("function Restore-BridgeScheduledTask")
        ]
        self.assertIn("if ($PackageSmoke)", task_suspend)
        self.assertIn("$taskTargetsIsolatedInstall", task_suspend)
        self.assertIn("$actionIdentity.IndexOf($installRoot", task_suspend)
        self.assertLess(
            task_suspend.index("if (-not $taskTargetsIsolatedInstall)"),
            task_suspend.index("$script:bridgeTaskExisted = $true"),
        )

        rollback = installer[
            installer.index("function Start-PreviousDegradedBridgeAfterRollback"):
            installer.index("function New-StagedApplication")
        ]
        self.assertIn("Get-InstalledBridgeListenerIdentity", rollback)
        self.assertIn("$previousBridgeWasHealthy", rollback)
        self.assertIn("Start-Process", rollback)
        self.assertIn("คงสถานะ degraded เดิม", rollback)

    def test_student_prompt_requires_release_assets_checksum_and_success_gate(self) -> None:
        prompt = (ROOT / "docs" / "prompts" / "install-github-google-auto-th.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("/releases/tags/<GITHUB_TAG>", prompt)
        self.assertIn("draft=false", prompt)
        self.assertIn(".sha256", prompt)
        self.assertIn("SHA-256 64", prompt)
        self.assertIn("/commits/<REMOTE_TAG_COMMIT>/status", prompt)
        self.assertIn("context=metafxclub/release", prompt)
        self.assertIn("state=success", prompt)
        self.assertIn("ห้ามเชื่อเพียงว่า Tag มีอยู่", prompt)
        self.assertIn("objects.githubusercontent.com", prompt)
        self.assertIn("release-assets.githubusercontent.com", prompt)
        self.assertIn(
            "Metafxclub-AI-Agent-HQ-<GITHUB_TAG>/backend/local-runner/google_oauth_native_client.txt",
            prompt,
        )
        self.assertIn("อ่าน bytes ของ entry นี้แล้วเขียนแบบ atomic ไปที่", prompt)
        self.assertIn("ตัดเฉพาะชื่อ root ของ Archive ออก", prompt)

    def test_student_prompt_bootstrap_is_locked_per_user_and_precedes_clone(self) -> None:
        prompt = (ROOT / "docs" / "prompts" / "install-github-google-auto-th.md").read_text(
            encoding="utf-8"
        )
        bootstrap = prompt[prompt.index("1. ตรวจว่าเป็น Windows") : prompt.index("2. ใช้เฉพาะ")]
        install_lines = [line for line in bootstrap.splitlines() if "`winget install " in line]

        self.assertEqual(2, len(install_lines))
        self.assertTrue(any("--id Git.Git" in line for line in install_lines))
        self.assertTrue(any("--id Python.Python.3.13" in line for line in install_lines))
        for line in install_lines:
            for required in (
                "--exact",
                "--source winget",
                "--scope user",
                "--architecture x64",
                "--silent",
                "--no-upgrade",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--disable-interactivity",
            ):
                self.assertIn(required, line)
            for forbidden in ("--scope machine", "--force", "--override", "winget upgrade"):
                self.assertNotIn(forbidden, line)

        self.assertIn("ใช้ของเดิมทันที", bootstrap)
        self.assertIn("ห้ามติดตั้งซ้ำ", bootstrap)
        self.assertIn("Merge Process PATH เดิมกับ Machine PATH และ User PATH", bootstrap)
        self.assertIn("ไม่ใช้ `setx`", bootstrap)
        self.assertIn('`-3.10` และ `-3` เป็นทางเลือกสุดท้าย', bootstrap)
        self.assertIn("git version --build-options", bootstrap)
        self.assertIn("cpu: x86_64", bootstrap)
        self.assertIn("sizeof-size_t: 8", bootstrap)
        self.assertIn("https://cdn.winget.microsoft.com/cache", bootstrap)
        self.assertIn("Microsoft.PreIndexed.Package", bootstrap)
        self.assertIn("winget source list --name winget", bootstrap)
        self.assertIn("Deadline รายการละ 15 นาที", bootstrap)
        self.assertIn("ห้ามเริ่ม Process ที่สอง", bootstrap)
        self.assertIn("ห้าม Reset/เพิ่ม Source เอง", bootstrap)
        self.assertIn("ห้ามใช้ `winget upgrade`", bootstrap)
        self.assertIn("ห้ามเปลี่ยนไปใช้ Package/Source อื่น", bootstrap)
        self.assertLess(prompt.index("1. ตรวจว่าเป็น Windows"), prompt.index("/releases/tags/<GITHUB_TAG>"))
        self.assertLess(prompt.index("/releases/tags/<GITHUB_TAG>"), prompt.index("git clone --depth 1"))

    def test_central_default_is_noninteractive_and_advanced_inputs_validate_before_mutation(self) -> None:
        installer = (ROOT / "installer" / "install.ps1").read_text(encoding="utf-8-sig")
        validator = installer[
            installer.index("function Assert-GoogleOAuthOneRunInputs") :
            installer.index("function Test-PythonCommand")
        ]
        for required_fragment in (
            'Test-Path -LiteralPath $fullPath -PathType Leaf',
            "[IO.FileAttributes]::ReparsePoint",
            '$file.Extension -ine ".json"',
            "$file.Length -gt 64KB",
            "New-Object Text.UTF8Encoding($false, $true)",
            '$document.PSObject.Properties["installed"]',
            '$installed.PSObject.Properties["client_id"]',
            '$installed.PSObject.Properties["client_secret"]',
            '"https://accounts.google.com/o/oauth2/auth"',
            '"https://oauth2.googleapis.com/token"',
            '@("localhost", "127.0.0.1")',
            "$ExpectedGoogleClientId.Trim()",
            "$script:validatedGoogleClientJsonPath = $fullPath",
        ):
            self.assertIn(required_fragment, validator)

        normal_main = installer[
            installer.index("try {\n    # Validate explicit classroom onboarding inputs") :
        ]
        self.assertLess(
            normal_main.index("Assert-GoogleOAuthOneRunInputs"),
            normal_main.index("Assert-SafeSource"),
        )
        self.assertLess(
            normal_main.index("Assert-GoogleOAuthOneRunInputs"),
            normal_main.index("$selectedBridgePort = Confirm-BridgeEndpoint"),
        )
        self.assertLess(
            normal_main.index("$selectedBridgePort = Confirm-BridgeEndpoint"),
            normal_main.index("$stagingRoot = New-StagedApplication"),
        )

        first_run = installer[
            installer.index("function Invoke-GoogleOAuthFirstRunSetup") :
            installer.index("function Invoke-BridgeLifecycleProcess")
        ]
        self.assertIn("Get-GoogleOAuthDeploymentStatus -CandidateRoot", first_run)
        self.assertIn('"central_release"', first_run)
        self.assertIn('$script:googleSetupStatus = "ready_central"', first_run)
        self.assertIn('$script:googleSetupStatus = "ready_existing_override"', first_run)
        self.assertIn("if (-not $explicitClientSetup)", first_run)
        self.assertNotIn("Read-Host", first_run)
        self.assertIn('$setupArguments += "-NonInteractive"', first_run)
        self.assertIn('"-ClientJsonPath", $validatedGoogleClientJsonPath', first_run)
        self.assertIn('"-ExpectedClientId", $ExpectedGoogleClientId', first_run)
        self.assertIn('$script:googleSetupStatus = "ready_imported"', first_run)
        self.assertLess(
            first_run.index("if ($SkipGoogleSetup -and -not $explicitClientSetup)"),
            first_run.index("$deploymentStatus = Get-GoogleOAuthDeploymentStatus"),
        )

        completion = installer[
            installer.index("$postInstallExitCode = if ($watchdogFailure") :
            installer.rindex("catch {")
        ]
        self.assertLess(completion.index("Write-InstallResult"), completion.index("exit 0"))
        self.assertLess(completion.index("if ($postInstallFailures.Count -gt 0)"), completion.index("exit 0"))
        self.assertIn("exit $postInstallExitCode", completion)
        result_writer = installer[
            installer.index("function Write-InstallResult") :
            installer.index("try {\n    # Validate explicit classroom onboarding inputs")
        ]
        self.assertIn("google_oauth_client", result_writer)
        self.assertIn("requested = -not ($SkipGoogleSetup -or $SkipLaunch)", result_writer)
        self.assertIn('status = $(if ($googleSetupFailure) { "repair_required" } else { $googleSetupStatus })', result_writer)
        self.assertIn("source = $googleSetupSource", result_writer)
        for forbidden_field in (
            "client_id =",
            "client_secret =",
            "access_token =",
            "refresh_token =",
            "json_path =",
        ):
            with self.subTest(forbidden_field=forbidden_field):
                self.assertNotIn(forbidden_field, result_writer.lower())

        for batch_name in ("1-INSTALL-HQ.bat", "UPDATE-HQ.bat"):
            batch = (ROOT / batch_name).read_text(encoding="utf-8-sig")
            self.assertIn("-NonInteractive", batch)
            self.assertIn('if "%~1"=="" pause', batch)
        install_batch = (ROOT / "1-INSTALL-HQ.bat").read_text(encoding="utf-8-sig")
        default_install_branch = install_batch[
            install_batch.index('if "%~1"=="" (') : install_batch.index(") else (")
        ]
        argument_install_branch = install_batch[
            install_batch.index(") else (") : install_batch.index("set \"INSTALL_EXIT")
        ]
        self.assertNotIn("-NonInteractive", default_install_branch)
        self.assertIn("-NonInteractive", argument_install_branch)

    def test_watchdog_registration_is_current_user_and_never_requests_admin(self) -> None:
        registration = (ROOT / "scripts" / "register-bridge-autostart.ps1").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("[Security.Principal.WindowsIdentity]::GetCurrent().Name", registration)
        self.assertIn("New-ScheduledTaskPrincipal", registration)
        self.assertIn("-LogonType Interactive", registration)
        self.assertIn("-RunLevel Limited", registration)
        self.assertNotIn("RunLevel Highest", registration)
        self.assertNotIn("Start-Process -Verb RunAs", registration)
        self.assertIn("Register-ScheduledTask", registration)
        self.assertIn("Unregister-ScheduledTask", registration)

    @unittest.skipUnless(os.name == "nt", "Windows PowerShell installer preflight")
    def test_explicit_google_inputs_validate_noninteractively_before_endpoint_listing(self) -> None:
        client_id = "123456789012-installer-preflight.apps.googleusercontent.com"
        client_secret = "UNIT_TEST_ONLY_VALUE"
        document = {
            "installed": {
                "client_id": client_id,
                "project_id": "installer-preflight",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": ["http://localhost"],
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            oauth_path = temporary_root / "desktop-client.json"
            oauth_path.write_text(json.dumps(document), encoding="utf-8")
            isolated_local_app_data = temporary_root / "localappdata"
            isolated_temp = temporary_root / "temp"
            isolated_local_app_data.mkdir()
            isolated_temp.mkdir()
            environment = os.environ.copy()
            environment["LOCALAPPDATA"] = str(isolated_local_app_data)
            environment["TEMP"] = str(isolated_temp)
            environment["TMP"] = str(isolated_temp)
            base_command = [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(ROOT / "installer" / "install.ps1"),
                "-ListAvailableEndpoints",
                "-GoogleClientJsonPath",
                str(oauth_path),
                "-ExpectedGoogleClientId",
            ]
            valid = subprocess.run(
                [*base_command, client_id],
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            self.assertEqual(0, valid.returncode, valid.stderr)
            self.assertRegex(valid.stdout, r'"ok"\s*:\s*true')
            self.assertNotIn(client_secret, valid.stdout + valid.stderr)
            self.assertFalse((isolated_local_app_data / "Metafxclub" / "AI-Agent-HQ").exists())

            mismatch = subprocess.run(
                [*base_command, "999999999999-wrong-client.apps.googleusercontent.com"],
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            self.assertEqual(1, mismatch.returncode)
            self.assertIn("Client ID", mismatch.stderr)
            self.assertNotIn(client_secret, mismatch.stdout + mismatch.stderr)
            self.assertFalse((isolated_local_app_data / "Metafxclub" / "AI-Agent-HQ").exists())

    def test_temporary_installer_paths_are_short_for_deep_windows_assets(self) -> None:
        installer = (ROOT / "installer" / "install.ps1").read_text(encoding="utf-8-sig")
        staged = installer[
            installer.index("function New-StagedApplication"):
            installer.index("function Publish-StagedApplication")
        ]
        self.assertIn("Get-InstallerTemporaryParent", staged)
        self.assertNotIn("Split-Path -Parent $installRoot", staged)
        self.assertIn('("mhs-{0}"', staged)
        self.assertIn("$file.FullName.Length -ge 260", staged)
        self.assertIn("$installedPath.Length -ge 260", staged)
        self.assertIn("Copy-ApplicationFiles -DestinationRoot $stagingRoot", staged)
        self.assertLess(staged.index("Copy-ApplicationFiles"), staged.index("Assert-NoEmbeddedHighConfidenceSecrets"))
        self.assertIn('("mhr-{0}"', installer)
        self.assertIn("mfxhq-stage", installer)
        self.assertIn("mfxhq-rollback", installer)
        self.assertIn("Assert-InstallerTemporaryDirectory", installer)
        self.assertIn("Remove-InstallerTemporaryDirectoryWithRetry", installer)
        self.assertIn("[IO.Directory]::Delete($extendedPath, $true)", installer)
        self.assertIn("$delaysMilliseconds = @(0, 100, 250, 500, 1000, 2000)", installer)
        self.assertIn("-BestEffort", installer)
        self.assertIn("Remove-StagedApplication -StagingRoot $stagingRoot", installer)
        self.assertNotIn('.AI-Agent-HQ.staging.', installer)
        self.assertNotIn('.AI-Agent-HQ.rollback.', installer)

        # Regression for a real classroom/CI TEMP parent whose canonical path
        # is 85 characters: the old 128-bit directory name placed this exact
        # shipped asset at Win32 length 260, while the shortened 128-bit name
        # keeps it below the installer's fail-closed boundary.
        deepest_release_asset = (
            "frontend\\public\\assets\\agents\\"
            "male-roster-set-a-core-command-operators-v001\\characters\\"
            "05-optimization-agent-male-static-v001.png"
        )
        parent_length = 85
        old_full_length = parent_length + 1 + len("mfxhq-stage-" + ("a" * 32)) + 1 + len(deepest_release_asset)
        new_full_length = parent_length + 1 + len("mhs-" + ("a" * 32)) + 1 + len(deepest_release_asset)
        self.assertEqual(260, old_full_length)
        self.assertLess(new_full_length, 260)

    def test_install_and_venv_cleanup_are_exact_path_bounded_retries(self) -> None:
        installer = (ROOT / "installer" / "install.ps1").read_text(encoding="utf-8-sig")
        managed_cleanup = installer[
            installer.index("function Assert-InstallerManagedDirectoryRemoval") :
            installer.index("function Stop-CandidateBridgeAfterFailedStart")
        ]
        self.assertIn('ValidateSet("installation", "venv")', managed_cleanup)
        self.assertIn('Join-Path $env:LOCALAPPDATA "Metafxclub\\AI-Agent-HQ"', managed_cleanup)
        self.assertIn("[IO.FileAttributes]::ReparsePoint", managed_cleanup)
        self.assertIn("-Attributes ReparsePoint", managed_cleanup)
        self.assertIn("$delaysMilliseconds = @(0, 100, 250, 500, 1000, 2000)", managed_cleanup)
        self.assertIn("[IO.Directory]::Delete($extendedPath, $true)", managed_cleanup)

        rollback = installer[
            installer.index("function Restore-ApplicationRollbackSnapshot") :
            installer.index("function Remove-ApplicationRollbackSnapshot")
        ]
        self.assertIn(
            "Remove-InstallerManagedDirectoryWithRetry -Path $installRoot -Kind installation",
            rollback,
        )
        self.assertNotIn("Remove-Item -LiteralPath $installRoot -Recurse", rollback)

        venv = installer[
            installer.index("function Initialize-PythonEnvironment") :
            installer.index("function Test-InstalledApplication")
        ]
        self.assertIn(
            "Remove-InstallerManagedDirectoryWithRetry -Path $venvRoot -Kind venv",
            venv,
        )
        self.assertNotIn("Remove-Item -LiteralPath $venvRoot -Recurse", venv)

    @unittest.skipUnless(os.name == "nt", "Windows directory-lock retry semantics")
    def test_managed_cleanup_survives_transient_lock_and_rejects_sibling(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local_app_data = Path(directory) / "LocalAppData"
            local_app_data.mkdir()
            installer_path = str(ROOT / "installer" / "install.ps1").replace("'", "''")
            local_app_data_path = str(local_app_data).replace("'", "''")
            script = rf"""
$ErrorActionPreference = 'Stop'
$installerPath = '{installer_path}'
$tokens = $null
$parseErrors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile(
    $installerPath,
    [ref]$tokens,
    [ref]$parseErrors
)
if ($parseErrors.Count -ne 0) {{ throw 'Installer parse failed' }}
foreach ($name in @(
    'Assert-InstallerManagedDirectoryRemoval',
    'Remove-InstallerManagedDirectoryWithRetry'
)) {{
    $node = $ast.Find({{
        param($candidate)
        $candidate -is [Management.Automation.Language.FunctionDefinitionAst] -and
            $candidate.Name -ceq $name
    }}, $true)
    if (-not $node) {{ throw "Function missing: $name" }}
    Invoke-Expression $node.Extent.Text
}}
$env:LOCALAPPDATA = '{local_app_data_path}'
$installRoot = Join-Path $env:LOCALAPPDATA 'Metafxclub\AI-Agent-HQ'
$venvRoot = Join-Path $installRoot 'runner\.venv'
New-Item -ItemType Directory -Path $venvRoot -Force | Out-Null
$lockedFile = Join-Path $venvRoot 'transient-lock.bin'
[IO.File]::WriteAllBytes($lockedFile, [byte[]](1, 2, 3))
$job = Start-Job -ScriptBlock {{
    param($path)
    $stream = [IO.File]::Open(
        $path,
        [IO.FileMode]::Open,
        [IO.FileAccess]::ReadWrite,
        [IO.FileShare]::None
    )
    try {{
        Write-Output 'LOCKED'
        Start-Sleep -Milliseconds 700
    }}
    finally {{
        $stream.Dispose()
    }}
}} -ArgumentList $lockedFile
try {{
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    do {{
        $jobOutput = @(Receive-Job -Job $job -Keep)
        if ($jobOutput -contains 'LOCKED') {{ break }}
        Start-Sleep -Milliseconds 50
    }} while ([DateTime]::UtcNow -lt $deadline)
    if ($jobOutput -notcontains 'LOCKED') {{ throw 'Lock fixture did not start' }}
    Remove-InstallerManagedDirectoryWithRetry -Path $venvRoot -Kind venv
    if (Test-Path -LiteralPath $venvRoot) {{ throw 'Venv remained after bounded retry' }}
}}
finally {{
    Stop-Job -Job $job -ErrorAction SilentlyContinue
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
}}
$outside = Join-Path $env:LOCALAPPDATA 'outside'
New-Item -ItemType Directory -Path $outside -Force | Out-Null
$rejected = $false
try {{
    Remove-InstallerManagedDirectoryWithRetry -Path $outside -Kind installation
}}
catch {{
    $rejected = $true
}}
if (-not $rejected) {{ throw 'Sibling deletion was not rejected' }}
if (-not (Test-Path -LiteralPath $outside -PathType Container)) {{
    throw 'Rejected sibling was mutated'
}}
Write-Output 'MANAGED_CLEANUP_OK'
"""
            completed = subprocess.run(
                [
                    "powershell.exe",
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    script,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=45,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertIn("MANAGED_CLEANUP_OK", completed.stdout)

    @unittest.skipUnless(os.name == "nt", "Windows PowerShell installer behavior")
    def test_skip_google_setup_does_not_probe_current_user_oauth_store(self) -> None:
        installer_path = str(ROOT / "installer" / "install.ps1").replace("'", "''")
        script = rf"""
$ErrorActionPreference = 'Stop'
$tokens = $null
$parseErrors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile(
    '{installer_path}',
    [ref]$tokens,
    [ref]$parseErrors
)
if ($parseErrors.Count -ne 0) {{ throw 'Installer parse failed' }}
$name = 'Invoke-GoogleOAuthFirstRunSetup'
$node = $ast.Find({{
    param($candidate)
    $candidate -is [Management.Automation.Language.FunctionDefinitionAst] -and
        $candidate.Name -ceq $name
}}, $true)
if (-not $node) {{ throw 'First-run function missing' }}
Invoke-Expression $node.Extent.Text
function Test-GoogleOAuthDeploymentConfigured {{ throw 'OAUTH_STORE_PROBED' }}
$GoogleClientJsonPath = ''
$SkipGoogleSetup = $true
$SkipLaunch = $false
$script:googleSetupStatus = ''
Invoke-GoogleOAuthFirstRunSetup -CandidateRoot 'unused'
if ($script:googleSetupStatus -cne 'skipped_by_request') {{
    throw "Unexpected skip status: $($script:googleSetupStatus)"
}}
$SkipGoogleSetup = $false
$SkipLaunch = $true
$script:googleSetupStatus = ''
Invoke-GoogleOAuthFirstRunSetup -CandidateRoot 'unused'
if ($script:googleSetupStatus -cne 'skipped_no_launch') {{
    throw "Unexpected no-launch status: $($script:googleSetupStatus)"
}}
Write-Output 'OAUTH_SKIP_ISOLATED_OK'
"""
        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("OAUTH_SKIP_ISOLATED_OK", completed.stdout)


if __name__ == "__main__":
    unittest.main()
