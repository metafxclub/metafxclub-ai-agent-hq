from __future__ import annotations

import hashlib
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "mt4-ai-council-ea-v2.16-stream-transition-hardening"


class ReleaseInstallerHardeningTests(unittest.TestCase):
    def test_v216_curated_artifact_is_complete_and_not_ignored(self) -> None:
        required = {
            "MetafxHQTradeGateway.mq4",
            "MetafxHQTradeGateway.ex4",
            "README_TH.md",
            "AUDIT_TH.md",
            "SHA256SUMS.txt",
            "BUILD_LOG.txt",
        }
        self.assertEqual(required, {path.name for path in ARTIFACT.iterdir() if path.is_file()})

        for relative_path in (
            "scripts/run-bridge-watchdog-hidden.vbs",
            *(
                f"artifacts/mt4-ai-council-ea-v2.16-stream-transition-hardening/{filename}"
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
        self.assertIn("!artifacts/mt4-ai-council-ea-v2.16-stream-transition-hardening/", ignore_text)
        self.assertIn("!artifacts/mt4-ai-council-ea-v2.16-stream-transition-hardening/**", ignore_text)
        self.assertIn("artifacts/mt4-ai-council-ea-v2.16-stream-transition-hardening/*.log", ignore_text)
        self.assertIn("integrations/mt4-trade-gateway/*.ex4", ignore_text)

    def test_v216_manifest_and_build_evidence_match_curated_files(self) -> None:
        manifest_text = (ARTIFACT / "SHA256SUMS.txt").read_text(encoding="utf-8")
        manifest: dict[str, str] = {}
        for line in manifest_text.splitlines():
            if not line.strip():
                continue
            match = re.fullmatch(r"([A-Fa-f0-9]{64})\s+([^\\/]+)", line)
            self.assertIsNotNone(match, line)
            assert match is not None
            manifest[match.group(2)] = match.group(1).upper()

        for filename in ("MetafxHQTradeGateway.mq4", "MetafxHQTradeGateway.ex4"):
            digest = hashlib.sha256((ARTIFACT / filename).read_bytes()).hexdigest().upper()
            self.assertEqual(digest, manifest[filename])

        integration_digest = hashlib.sha256(
            (ROOT / "integrations" / "mt4-trade-gateway" / "MetafxHQTradeGateway.mq4").read_bytes()
        ).hexdigest().upper()
        self.assertEqual(integration_digest, manifest["MetafxHQTradeGateway.mq4"])

        build_log = (ARTIFACT / "BUILD_LOG.txt").read_text(encoding="utf-8")
        self.assertIn("Result: 0 errors, 0 warnings,", build_log)
        self.assertIn(f"SourceSHA256: {manifest['MetafxHQTradeGateway.mq4']}", build_log)
        self.assertIn(f"BinarySHA256: {manifest['MetafxHQTradeGateway.ex4']}", build_log)
        self.assertIsNone(re.search(r"(?i)(?:[A-Z]:\\|/Users/|/home/)", build_log))

    def test_installer_requires_and_verifies_all_v216_release_evidence(self) -> None:
        installer = (ROOT / "installer" / "install.ps1").read_text(encoding="utf-8-sig")
        for filename in (
            "MetafxHQTradeGateway.mq4",
            "MetafxHQTradeGateway.ex4",
            "README_TH.md",
            "AUDIT_TH.md",
            "SHA256SUMS.txt",
            "BUILD_LOG.txt",
        ):
            self.assertIn(
                f"artifacts\\mt4-ai-council-ea-v2.16-stream-transition-hardening\\{filename}",
                installer,
            )
        self.assertIn("Assert-EaArtifactIntegrity", installer)
        self.assertIn("Assert-NoEmbeddedHighConfidenceSecrets", installer)
        self.assertIn("Source EA ใน Integration ไม่ตรงกับ Source", installer)
        self.assertIn("หลักฐาน Compile ของ EA ไม่ตรงกับ Source/Binary", installer)
        self.assertIn('install_root = "%LOCALAPPDATA%\\Metafxclub\\AI-Agent-HQ"', installer)
        self.assertIn("install_scope = \"current_windows_user\"", installer)

    def test_installer_stages_before_mutation_and_restores_last_good_on_failure(self) -> None:
        installer = (ROOT / "installer" / "install.ps1").read_text(encoding="utf-8-sig")
        self.assertLess(installer.index("$stagingRoot = New-StagedApplication"), installer.index("$script:applicationMutationStarted = $true"))
        self.assertLess(installer.index("$stagingRoot = New-StagedApplication"), installer.index("$bridgeTaskWasEnabled = Suspend-BridgeScheduledTask"))
        normal_flow_start = installer.index("$previousHealthyEndpoint = Get-HealthySavedEndpoint")
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
        self.assertIn("$previousHealthyEndpoint = Get-HealthySavedEndpoint", installer)
        self.assertIn("Stop-CandidateBridgeAfterFailedStart", installer)
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
        staged = installer[installer.index("function New-StagedApplication"):installer.index("function Publish-StagedApplication")]
        self.assertIn("Resolve-SystemPython", staged)
        self.assertNotIn("if (Test-Path -LiteralPath $candidatePython -PathType Leaf)", staged)

        requirements = (ROOT / "requirements-runner.txt").read_text(encoding="utf-8")
        self.assertGreaterEqual(requirements.count("--hash=sha256:"), 11)
        requirement_blocks = [block for block in re.split(r"\n(?=[A-Za-z0-9_.-]+==)", requirements) if "==" in block]
        self.assertEqual(7, len(requirement_blocks))
        self.assertTrue(all("--hash=sha256:" in block for block in requirement_blocks))
        self.assertIn("[int]$details.minor -gt 14", installer)
        self.assertIn("[switch]$PackageSmoke", installer)
        smoke = installer[
            installer.index("if ($PackageSmoke) {"):
            installer.index("$previousHealthyEndpoint = Get-HealthySavedEndpoint")
        ]
        self.assertIn("Publish-StagedApplication", smoke)
        self.assertIn("Test-InstalledApplication", smoke)
        self.assertNotIn("Suspend-BridgeScheduledTask", smoke)
        self.assertNotIn("Stop-ExistingBridge", smoke)
        self.assertIn('$env:GITHUB_ACTIONS -cne "true"', smoke)
        self.assertIn("$localAppDataFull.StartsWith($runnerTempFull", smoke)
        self.assertIn("$script:rollbackIncomplete = $true", installer)
        finally_block = installer[installer.rindex("    finally {"):installer.index("    Write-Step \"ติดตั้งและตรวจสอบสำเร็จ")]
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
        publish_scope = installer[
            installer.index("function Publish-StagedApplication"):
            installer.index("function New-ApplicationRollbackSnapshot")
        ]
        self.assertIn('".github"', copy_scope)
        self.assertIn('".github"', publish_scope)

    def test_release_workflow_never_skips_current_archive_smoke(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "publish-release.yml").read_text(encoding="utf-8")
        verify_step = workflow[
            workflow.index("- name: Verify safe runtime"):
            workflow.index("- name: Build release package")
        ]
        self.assertIn("Python regression suite failed with exit code", verify_step)
        self.assertIn("Frontend syntax check failed with exit code", verify_step)
        self.assertGreaterEqual(verify_step.count("$LASTEXITCODE -ne 0"), 2)
        self.assertIn("Always build and smoke-test the exact current archive", workflow)
        self.assertIn("git archive --format=zip", workflow)
        self.assertIn("Release ZIP installation smoke test failed", workflow)
        self.assertIn("Bump VERSION instead of reusing the tag", workflow)
        self.assertIn("gh release upload $tag $archive $checksum", workflow)
        self.assertIn("--clobber", workflow)
        self.assertIn("gh api \"repos/$env:GITHUB_REPOSITORY/releases/tags/$tag\"", workflow)
        self.assertIn("Unable to determine whether Release $tag already exists", workflow)
        self.assertIn("Release $tag could not be created", workflow)
        self.assertIn("gh release download $tag", workflow)
        self.assertIn("remote assets do not match the verified local package", workflow)
        self.assertIn("Release $tag verified", workflow)
        self.assertIn("-PackageSmoke", workflow)
        for filename in (
            "scripts\\run-bridge-watchdog-hidden.vbs",
            "MetafxHQTradeGateway.mq4",
            "MetafxHQTradeGateway.ex4",
            "README_TH.md",
            "AUDIT_TH.md",
            "SHA256SUMS.txt",
            "BUILD_LOG.txt",
        ):
            self.assertIn(filename, workflow)

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
        self.assertIn("Remove-StagedApplication -StagingRoot $stagingRoot", installer)
        self.assertNotIn('.AI-Agent-HQ.staging.', installer)
        self.assertNotIn('.AI-Agent-HQ.rollback.', installer)


if __name__ == "__main__":
    unittest.main()
