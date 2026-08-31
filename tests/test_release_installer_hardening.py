from __future__ import annotations

import hashlib
import fnmatch
import json
import re
import subprocess
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

        integration_digest = hashlib.sha256(
            (ROOT / "integrations" / "mt4-trade-gateway" / "MetafxHQTradeGateway.mq4").read_bytes()
        ).hexdigest().upper()
        self.assertEqual(integration_digest, manifest["MetafxHQTradeGateway.mq4"])

        artifact_manifest = json.loads((ARTIFACT / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual("metafx-hq-mt4-ea-artifact-v1", artifact_manifest["schemaVersion"])
        self.assertEqual("2.18", artifact_manifest["packageVersion"])
        self.assertEqual("ready_visible_metaeditor_compiled", artifact_manifest["candidateStatus"])
        self.assertEqual(integration_digest, artifact_manifest["sourceSha256"])
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
        self.assertIn("Source EA ใน Integration ไม่ตรงกับ Source", installer)
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
        smoke = installer[
            installer.index("if ($PackageSmoke) {"):
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
        self.assertIn('"tests\\release_secret_scan.py"', installer)
        self.assertIn('"tests\\test_release_candidate_preflight.py"', installer)

        exclude_match = re.search(r'"/XF",(?P<filters>.*?)\r?\n\s*"/XD"', sync_scope, re.DOTALL)
        self.assertIsNotNone(exclude_match)
        exclude_patterns = re.findall(r'"([^"]+)"', exclude_match.group("filters"))
        for safe_source_name in (
            "release_secret_scan.py",
            "test_release_secret_hygiene.py",
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
        verify_step = workflow[
            workflow.index("- name: Verify safe runtime"):
            workflow.index("- name: Build release package")
        ]
        self.assertIn("Python regression suite failed with exit code", verify_step)
        self.assertIn("Frontend syntax check failed with exit code", verify_step)
        self.assertIn("python -m venv runner/.venv", verify_step)
        self.assertIn("--require-hashes --requirement requirements-runner.txt", verify_step)
        self.assertIn(r".\runner\.venv\Scripts\python.exe -m unittest", verify_step)
        self.assertGreaterEqual(verify_step.count("$LASTEXITCODE -ne 0"), 2)
        self.assertIn("Always build and smoke-test the exact current archive", workflow)
        self.assertIn("git archive --format=zip", workflow)
        self.assertIn("legacy-listener upgrade smoke failed", workflow)
        self.assertIn("Bump VERSION instead of reusing the tag", workflow)
        self.assertIn("gh release upload $tag $archive $checksum", workflow)
        self.assertIn("--clobber", workflow)
        self.assertIn("gh api \"repos/$env:GITHUB_REPOSITORY/releases/tags/$tag\"", workflow)
        self.assertIn("Unable to determine whether Release $tag already exists", workflow)
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
        self.assertIn("https://github.com/metafxclub/metafxclub-ai-agent-hq.git", workflow)
        self.assertIn("git -C $verifiedClone fetch --depth 1 origin $env:GITHUB_SHA", workflow)
        self.assertIn("git -C $verifiedClone checkout --detach $env:GITHUB_SHA", workflow)
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
        self.assertIn("actions/checkout@11d5960a326750d5838078e36cf38b85af677262", workflow)
        self.assertIn("actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065", workflow)
        self.assertIn("Python 3.10-3.14", workflow)
        for filename in (
            "requirements-runner.txt",
            "scripts\\start-local-bridge.ps1",
            "google_oauth_store.py",
            "google_sheet_hub.py",
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
        self.assertIn("actions/checkout@11d5960a326750d5838078e36cf38b85af677262", verify_workflow)
        self.assertIn("actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065", verify_workflow)
        self.assertIn('python-version: ["3.10", "3.11", "3.12", "3.13", "3.14"]', verify_workflow)
        self.assertIn('python-version: ${{ matrix.python-version }}', verify_workflow)
        self.assertIn('python-version: "3.11"', workflow)
        self.assertIn("needs: compatibility", workflow)
        self.assertIn('python-version: ["3.10", "3.11", "3.12", "3.13", "3.14"]', workflow)
        self.assertIn("Regression suite failed on Python ${{ matrix.python-version }}", workflow)

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

    def test_temporary_installer_paths_are_short_for_deep_windows_assets(self) -> None:
        installer = (ROOT / "installer" / "install.ps1").read_text(encoding="utf-8-sig")
        staged = installer[
            installer.index("function New-StagedApplication"):
            installer.index("function Publish-StagedApplication")
        ]
        self.assertIn("Get-InstallerTemporaryParent", staged)
        self.assertNotIn("Split-Path -Parent $installRoot", staged)
        self.assertIn('("mfxhq-stage-{0}"', staged)
        self.assertIn("$file.FullName.Length -ge 260", staged)
        self.assertIn("$installedPath.Length -ge 260", staged)
        self.assertIn("Copy-ApplicationFiles -DestinationRoot $stagingRoot", staged)
        self.assertLess(staged.index("Copy-ApplicationFiles"), staged.index("Assert-NoEmbeddedHighConfidenceSecrets"))
        self.assertIn('("mfxhq-rollback-{0}"', installer)
        self.assertIn("Assert-InstallerTemporaryDirectory", installer)
        self.assertIn("Remove-InstallerTemporaryDirectoryWithRetry", installer)
        self.assertIn("$delaysMilliseconds = @(0, 100, 250, 500, 1000, 2000)", installer)
        self.assertIn("-BestEffort", installer)
        self.assertIn("Remove-StagedApplication -StagingRoot $stagingRoot", installer)
        self.assertNotIn('.AI-Agent-HQ.staging.', installer)
        self.assertNotIn('.AI-Agent-HQ.rollback.', installer)


if __name__ == "__main__":
    unittest.main()
