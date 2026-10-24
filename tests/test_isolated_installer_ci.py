"""The native installer smoke may run only on actual isolated CI runners."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from tests.release_secret_scan import scan_embedded_secrets

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/test-isolated-installer-ci.ps1'


class IsolatedInstallerCiTests(unittest.TestCase):
    def test_fixture_client_is_not_duplicated_in_the_distributed_generator(self):
        # A literal fixture client ID in this distributed script is correctly
        # rejected by release preflight after its client file is injected.
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            client = fixture / 'backend/local-runner/google_oauth_native_client.txt'
            client.parent.mkdir(parents=True)
            client_id = 'inert-smoke-fixture' + '.apps.googleusercontent.com'
            client.write_text('client_id=' + client_id + '\nclient_secret=' + 'GOC' + 'SPX-' + 'INERT_SMOKE_FIXTURE_' * 2 + '\n', encoding='utf-8')
            script = fixture / 'scripts/test-isolated-installer-ci.ps1'
            script.parent.mkdir(parents=True)
            script.write_bytes(SCRIPT.read_bytes())
            self.assertEqual(scan_embedded_secrets(fixture, allow_central_native_client=True), [])
        text = SCRIPT.read_text(encoding='utf-8-sig')
        self.assertIn("$ciDummyClientId = 'inert-smoke-' + [Guid]::NewGuid()", text)
        self.assertIn('client_id=$ciDummyClientId', text)

    def test_workflow_uses_read_only_ci_job_and_does_not_upload_fixture(self):
        workflow = (ROOT / '.github/workflows/verify.yml').read_text(encoding='utf-8-sig')
        job = workflow[workflow.index('  isolated-installer:'):]
        self.assertIn('runs-on: windows-latest', job)
        self.assertIn('contents: read', job)
        self.assertIn('./scripts/test-isolated-installer-ci.ps1', job)
        self.assertNotIn('secrets.', job)
        self.assertNotIn('upload-artifact', job)
        self.assertNotIn('gh release', job)

    def test_fixture_is_generated_under_runner_temp_and_preserves_safety_flags(self):
        script = SCRIPT.read_text(encoding='utf-8-sig')
        self.assertLess(script.index("$env:GITHUB_ACTIONS -cne 'true'"), script.index('New-Item'))
        self.assertIn('[IO.Path]::GetFullPath($env:RUNNER_TEMP)', script)
        self.assertIn('archive --format=zip --output=$ciArchive HEAD', script)
        self.assertIn('-SkipShortcuts -SkipAutostart -SkipGoogleSetup -PackageSmoke', script)
        self.assertIn("-ExtraArguments @('-SkipLaunch')", script)
        self.assertIn("'-PackageSmokeFailAfterPublish'", script)
        self.assertIn("'Rollback did not restore previous VERSION.'", script)
        self.assertIn("'Upgrade changed preserved user data.'", script)
        self.assertIn('http://127.0.0.1:$ciPort/api/health', script)
        self.assertIn('-File $ciLifecycle -Action Stop -Port $ciPort', script)
        for forbidden in ('Stop-Process', 'taskkill', 'Register-ScheduledTask', 'Unregister-ScheduledTask', '${{ secrets.'):
            self.assertNotIn(forbidden, script)

    @unittest.skipUnless(os.name == 'nt', 'Windows entry guard')
    def test_local_execution_rejects_before_any_installation(self):
        environment = os.environ.copy()
        environment.pop('GITHUB_ACTIONS', None)
        environment.pop('RUNNER_TEMP', None)
        result = subprocess.run(['powershell.exe', '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(SCRIPT)], cwd=ROOT, env=environment, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('requires actual GitHub Actions', result.stderr)


if __name__ == '__main__':
    unittest.main()
