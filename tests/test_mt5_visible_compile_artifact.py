"""Native compile evidence. Only extracted installer validation functions run.

No installer entrypoint, compiler, terminal, profile or trading action is run.
The module name remains stable for existing release automation.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MT4_REL = Path('artifacts/mt4-ai-council-ea-v2.18-enum-fail-closed-readiness')
MT5_REL = Path('artifacts/mt5-trade-gateway-v1.07-isolated-compile-readiness')
ARTIFACT_DIR = ROOT / MT5_REL
SOURCE_REL = Path('integrations/mt5-trade-gateway/MetafxHQTradeGateway.mq5')
BINARY_REL = SOURCE_REL.with_suffix('.ex5')

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def rehash(folder: Path) -> None:
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.name != 'SHA256SUMS.txt')
    (folder / 'SHA256SUMS.txt').write_text(''.join(f'{sha256(p)}  {p.name}\n' for p in files), encoding='utf-8')

def stage_minimum(destination: Path) -> None:
    for rel in (MT4_REL, MT5_REL):
        shutil.copytree(ROOT / rel, destination / rel)
    for rel in (SOURCE_REL, BINARY_REL, Path('integrations/mt4-trade-gateway/MetafxHQTradeGateway.mq4')):
        (destination / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, destination / rel)

def run_gates(candidate: Path, platform: str = 'both') -> subprocess.CompletedProcess:
    installer = str(ROOT / 'installer/install.ps1').replace("'", "''")
    location = str(candidate).replace("'", "''")
    calls = []
    if platform in ('mt4', 'both'):
        calls.append(f"Assert-EaArtifactIntegrity -CandidateRoot '{location}'")
    if platform in ('mt5', 'both'):
        calls.append(f"Assert-Mt5CompileArtifactIntegrity -CandidateRoot '{location}'")
    code = """$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$tokens=$null; $parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('INSTALLER',[ref]$tokens,[ref]$parseErrors)
if ($parseErrors.Count -ne 0) { throw 'Installer parse failed' }
foreach ($name in @('Get-Sha256Hex','Assert-NativeCompileArtifactIntegrity','Assert-EaArtifactIntegrity','Assert-Mt5CompileArtifactIntegrity')) {
    $node=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true)
    if (-not $node) { throw 'Missing gate function' }
    Invoke-Expression $node.Extent.Text
}
""".replace('INSTALLER', installer) + '\n'.join(calls)
    return subprocess.run(['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-Command',code], cwd=ROOT, capture_output=True, encoding='utf-8', errors='replace', timeout=30, check=False)

class Mt5NativeCompileArtifactTests(unittest.TestCase):
    def test_source_binary_and_native_log_are_exact_reviewed_bytes(self) -> None:
        manifest = json.loads((ARTIFACT_DIR / 'MANIFEST.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['schemaVersion'], 'metafx-hq-mt5-ea-compile-proof-v2')
        self.assertEqual(manifest['packageVersion'], '1.07')
        self.assertEqual(manifest['releasePolicy'], 'source_and_verified_binary')
        self.assertIs(manifest['compiledBinaryIncluded'], True)
        self.assertIs(manifest['compiledBinaryEligibleForDistribution'], True)
        for field, rel in (('source', SOURCE_REL), ('binary', BINARY_REL)):
            self.assertEqual(manifest[field + 'File'], rel.as_posix())
            self.assertEqual(manifest[field + 'Sha256'], sha256(ROOT / rel))
            self.assertEqual(manifest[field + 'Bytes'], (ROOT / rel).stat().st_size)
        evidence = manifest['compileEvidence']
        self.assertEqual(evidence['mode'], 'isolated_portable_metaeditor64_cli_exact_source')
        self.assertEqual((evidence['errors'], evidence['warnings']), (0, 0))
        self.assertEqual(evidence['compiledSourceSha256'], manifest['sourceSha256'])
        self.assertEqual(evidence['logSha256'], sha256(ARTIFACT_DIR / 'COMPILE_LOG.log'))
        self.assertNotIn('screenshot', evidence)
        for key in ('eaAttachedToChart','algoTradingChanged','orderOrTradeCommandSent','demoExecutionValidated','liveExecutionValidated','nativeAttachmentValidated'):
            self.assertIs(manifest['safety'][key], False)

    def test_checksums_complete_unique_and_public_logs_are_portable(self) -> None:
        for relative in (MT4_REL, MT5_REL):
            folder = ROOT / relative
            entries = {}
            for line in (folder / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
                match = re.fullmatch(r'([0-9A-F]{64})  ([^\\/]+)', line)
                self.assertIsNotNone(match)
                digest, name = match.groups()
                self.assertNotIn(name, entries)
                entries[name] = digest
                self.assertEqual(sha256(folder / name), digest)
            self.assertEqual(set(entries), {p.name for p in folder.iterdir() if p.name != 'SHA256SUMS.txt'})
            for name in ('COMPILE_LOG.log','BUILD_LOG.txt','MANIFEST.json'):
                self.assertNotRegex((folder / name).read_text(encoding='utf-8'), r'(?i)(?<![A-Za-z])(?:[A-Z]:[\\/]|/Users/|/home/)')

    def test_all_package_boundaries_require_complete_current_evidence(self) -> None:
        installer = (ROOT / 'installer/install.ps1').read_text(encoding='utf-8-sig')
        workflow = (ROOT / '.github/workflows/publish-release.yml').read_text(encoding='utf-8-sig')
        boundaries = [installer[installer.index('$requiredFiles = @('):installer.index('foreach ($relativePath in $requiredFiles)')]]
        for marker in ('foreach ($requiredFile in @(', 'foreach ($requiredInstalledFile in @(', 'foreach ($verifiedRuntimeFile in @('):
            start = workflow.index(marker)
            boundaries.append(workflow[start:workflow.index(')) {', start)])
        for rel in (MT4_REL, MT5_REL):
            for file in (ROOT / rel).iterdir():
                for boundary in boundaries:
                    self.assertIn(str(file.relative_to(ROOT)).replace('/', '\\'), boundary)
        for boundary in boundaries:
            self.assertIn(str(BINARY_REL).replace('/', '\\'), boundary)

    @unittest.skipUnless(os.name == 'nt', 'Windows PowerShell validation only')
    def test_real_current_proofs_pass_strict_mode_without_running_installer(self) -> None:
        result = run_gates(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(os.name == 'nt', 'Windows pure copy and validation functions')
    def test_actual_allowlisted_copy_and_publish_preserve_only_curated_compile_logs(self) -> None:
        # Exercise the real robocopy /XF policy, not shutil as a stand-in for
        # installer staging. All source, staged and installed paths are owned
        # temporary fixtures; the installer entrypoint is never invoked.
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary)
            source, staged, installed = (sandbox / name for name in ('source', 'stage', 'installed'))
            stage_minimum(source)
            for rel in ('backend/local-runner/private.log', 'backend/local-runner/COMPILE_LOG.log',
                        'integrations/mt5-trade-gateway/private.log', 'integrations/mt5-trade-gateway/COMPILE_LOG.log',
                        'data/runtime/never-copy.txt', 'workspace/never-copy.txt'):
                file = source / rel
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text('synthetic excluded fixture', encoding='utf-8')
            (source / 'backend/local-runner/keep.py').write_text('value = 1\n', encoding='utf-8')
            def quoted(path):
                return str(path.resolve()).replace("'", "''")
            script = """$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('INSTALLER',[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw 'Installer parse failed' }
foreach ($name in @('Get-ComparablePath','Get-Sha256Hex','Sync-Directory','Copy-ApplicationFiles','Publish-StagedApplication','Assert-NativeCompileArtifactIntegrity','Assert-EaArtifactIntegrity','Assert-Mt5CompileArtifactIntegrity')) {
    $node=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true)
    if (-not $node) { throw 'Missing pure copy/validation function' }
    Invoke-Expression $node.Extent.Text
}
function Write-Step { param([string]$Message) }
$sourceRoot='SOURCE'
$installRoot='INSTALLED'
$requirementsName='requirements-runner.txt'
Copy-ApplicationFiles -DestinationRoot 'STAGED'
Assert-EaArtifactIntegrity -CandidateRoot 'STAGED'
Assert-Mt5CompileArtifactIntegrity -CandidateRoot 'STAGED'
Publish-StagedApplication -StagingRoot 'STAGED'
Assert-EaArtifactIntegrity -CandidateRoot 'INSTALLED'
Assert-Mt5CompileArtifactIntegrity -CandidateRoot 'INSTALLED'
""".replace('INSTALLER', quoted(ROOT / 'installer/install.ps1')).replace('SOURCE', quoted(source)).replace('STAGED', quoted(staged)).replace('INSTALLED', quoted(installed))
            result = subprocess.run(['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-Command',script], cwd=ROOT, capture_output=True, encoding='utf-8', errors='replace', timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            expected_logs = {str(rel / 'COMPILE_LOG.log') for rel in (MT4_REL, MT5_REL)}
            for destination in (staged, installed):
                self.assertEqual({str(p.relative_to(destination)) for p in destination.rglob('*.log')}, expected_logs)
                self.assertTrue((destination / 'backend/local-runner/keep.py').is_file())
                self.assertFalse((destination / 'data').exists())
                self.assertFalse((destination / 'workspace').exists())
                for rel in (MT4_REL, MT5_REL):
                    self.assertEqual(sha256(destination / rel / 'COMPILE_LOG.log'), sha256(ROOT / rel / 'COMPILE_LOG.log'))

    @unittest.skipUnless(os.name == 'nt', 'Windows PowerShell validation only')
    def test_recomputed_checksums_do_not_approve_stale_forged_or_unreviewed_proof(self) -> None:
        # Rehash each corrupted local bundle. Merely self-consistent metadata
        # cannot replace the reviewed binaries or truthful native compile proof.
        mutations = ('source_changed', 'binary_changed', 'stale_compile_source', 'boolean_string', 'nonzero_warning', 'screenshot_claim', 'live_claim', 'missing_log', 'duplicate_checksum', 'path_escape', 'log_failure')
        for platform, rel in (('mt4', MT4_REL), ('mt5', MT5_REL)):
            for mutation in mutations:
                with self.subTest(platform=platform, mutation=mutation), tempfile.TemporaryDirectory() as temp:
                    candidate = Path(temp)
                    stage_minimum(candidate)
                    folder = candidate / rel
                    path = folder / 'MANIFEST.json'
                    manifest = json.loads(path.read_text(encoding='utf-8'))
                    source = folder / manifest['sourceFile'] if platform == 'mt4' else candidate / manifest['sourceFile']
                    binary = folder / manifest['binaryFile'] if platform == 'mt4' else candidate / manifest['binaryFile']
                    if mutation in ('source_changed', 'binary_changed'):
                        target = source if mutation == 'source_changed' else binary
                        target.write_bytes(target.read_bytes() + b'changed')
                        field = 'source' if mutation == 'source_changed' else 'binary'
                        manifest[field + 'Sha256'] = sha256(target)
                        manifest[field + 'Bytes'] = target.stat().st_size
                    elif mutation == 'stale_compile_source': manifest['compileEvidence']['compiledSourceSha256'] = '0' * 64
                    elif mutation == 'boolean_string': manifest['compileEvidence']['currentSourceMatchesCompiledSource'] = 'true'
                    elif mutation == 'nonzero_warning': manifest['compileEvidence']['warnings'] = 1
                    elif mutation == 'screenshot_claim': manifest['compileEvidence']['screenshot'] = 'synthetic.png'
                    elif mutation == 'live_claim': manifest['safety']['liveExecutionValidated'] = True
                    elif mutation == 'missing_log': (folder / 'COMPILE_LOG.log').unlink()
                    elif mutation == 'path_escape': manifest['sourceFile'] = '../outside.mq5'
                    elif mutation == 'log_failure':
                        log = folder / 'COMPILE_LOG.log'
                        old_hash = sha256(log)
                        log.write_text('Result: 1 errors, 0 warnings, 1 ms elapsed\n', encoding='utf-8')
                        manifest['compileEvidence']['logSha256'] = sha256(log)
                        build = folder / 'BUILD_LOG.txt'
                        build.write_text(build.read_text(encoding='utf-8').replace(old_hash, sha256(log)), encoding='utf-8')
                    path.write_text(json.dumps(manifest), encoding='utf-8')
                    rehash(folder)
                    if mutation == 'duplicate_checksum':
                        sums = folder / 'SHA256SUMS.txt'
                        sums.write_text(sums.read_text(encoding='utf-8') + sums.read_text(encoding='utf-8').splitlines()[0] + '\n', encoding='utf-8')
                    result = run_gates(candidate, platform)
                    self.assertNotEqual(result.returncode, 0, 'Tampered candidate was accepted')
                    self.assertIn('Native compile', result.stderr, result.stdout + result.stderr)

if __name__ == '__main__':
    unittest.main()
