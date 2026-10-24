"""Check the independent service survives release and installed-package boundaries."""
from pathlib import Path
import json
import os
import re
import subprocess
import unittest
from tests.test_release_candidate_preflight import REQUIRED_SENTIMENT_PACKAGE_FILES

ROOT=Path(__file__).resolve().parents[1]


class SentimentPackageTests(unittest.TestCase):
    def test_inventory_covers_every_backend_module_at_all_boundaries(self):
        package=ROOT/'backend/local-runner/sentiment_universe'
        actual={p.relative_to(ROOT).as_posix() for p in package.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.js','.html','.css'}}
        required={p for p in REQUIRED_SENTIMENT_PACKAGE_FILES if p.startswith('backend/')}
        self.assertEqual(actual,required)
        for path in REQUIRED_SENTIMENT_PACKAGE_FILES:
            self.assertTrue((ROOT/path).is_file(),path)
        installer=(ROOT/'installer/install.ps1').read_text(encoding='utf-8-sig')
        workflow=(ROOT/'.github/workflows/publish-release.yml').read_text(encoding='utf-8-sig')
        boundaries={'source':installer[installer.index('$requiredFiles = @('):installer.index('foreach ($relativePath in $requiredFiles)')]}
        for marker in ('foreach ($requiredFile in @(', 'foreach ($requiredInstalledFile in @(', 'foreach ($verifiedRuntimeFile in @('):
            start=workflow.index(marker);boundaries[marker]=workflow[start:workflow.index(')) {',start)]
        for name,body in boundaries.items():
            for path in REQUIRED_SENTIMENT_PACKAGE_FILES:
                with self.subTest(boundary=name,path=path):
                    self.assertIn('"'+path.replace('/','\\')+'"',body)

    def test_browser_assets_exist_and_private_state_is_not_shipped(self):
        public=ROOT/'frontend/public/sentiment-universe'
        html=(public/'index.html').read_text(encoding='utf-8')
        refs=re.findall(r'(?:src|href)=["\']([^"\']+)["\']',html)
        self.assertTrue(refs)
        for ref in refs:
            if ref.startswith(('http:','https:','data:','#')):continue
            relative=ref.lstrip('/').removeprefix('sentiment-universe/')
            self.assertTrue((public/relative.split('?')[0]).is_file(),ref)
        forbidden={'market.json','service.json','supervisor.json','news-calendar-cache.json','myfxbook-cache.json','credentials.dpapi'}
        for scope in (public,ROOT/'backend/local-runner/sentiment_universe'):
            for file in scope.rglob('*'):
                self.assertNotIn(file.name,forbidden,str(file))
                self.assertNotIn(file.suffix,{'.dpapi','.log'},str(file))

    def test_customer_setup_does_not_route_through_trading_lifecycle(self):
        setup=(ROOT/'scripts/setup-sentiment-universe.ps1').read_text(encoding='utf-8-sig')
        lifecycle=(ROOT/'scripts/sentiment-universe.ps1').read_text(encoding='utf-8-sig')
        for text in (setup,lifecycle):
            self.assertNotIn('start-local-bridge',text)
            self.assertNotIn('terminal64.exe',text)
            self.assertNotIn('order_send',text)
        self.assertIn('-WindowStyle Hidden',lifecycle)
        registration=(ROOT/'scripts/register-sentiment-autostart.ps1').read_text(encoding='utf-8-sig')
        self.assertIn('-LogonType Interactive -RunLevel Limited',registration)
        self.assertIn('Test-OwnedTask $previous',registration)
        self.assertIn('$targetMatches -and $argsMatch',registration)

    def test_package_smoke_skips_provider_setup(self):
        installer=(ROOT/'installer/install.ps1').read_text(encoding='utf-8-sig')
        self.assertIn("if ($PackageSmoke) {\n            $script:sentimentStatus = 'skipped_package_smoke'",installer)
        self.assertIn("elseif ($SkipLaunch) {\n            $script:sentimentStatus = 'skipped_no_launch'",installer)
        self.assertIn('Suspend-SentimentForUpdate\n        $bridgeTaskWasEnabled',installer)
        start=installer.index("if ($PackageSmoke) {\n            $script:sentimentStatus = 'skipped_package_smoke'")
        end=installer.index('Invoke-GoogleOAuthFirstRunSetup',start)
        onboarding=installer[start:end]
        self.assertIn("'-OpenSetupIfNeeded'",onboarding)
        self.assertLess(onboarding.index('elseif ($SkipLaunch)'),onboarding.index("'-OpenSetupIfNeeded'"))

    @unittest.skipUnless(os.name=='nt','PowerShell onboarding predicate')
    def test_fresh_setup_opens_but_saved_account_and_terminal_are_reused(self):
        path=str(ROOT/'scripts/setup-sentiment-universe.ps1').replace("'","''")
        # Extract just the pure predicate. Do not execute lifecycle, browser,
        # provider requests, Scheduled Tasks, or read this user's credentials.
        script="""$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('%s',[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Parse failure'}
$fn=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Test-SentimentSetupRequired'},$true)
Invoke-Expression $fn.Extent.Text
$cases=@(
 [pscustomobject]@{encryptedCredentialsPresent=$false;mt5=[pscustomobject]@{configured=$false}},
 [pscustomobject]@{encryptedCredentialsPresent=$true;mt5=[pscustomobject]@{configured=$false}},
 [pscustomobject]@{encryptedCredentialsPresent=$false;mt5=[pscustomobject]@{configured=$true}},
 [pscustomobject]@{encryptedCredentialsPresent=$true;mt5=[pscustomobject]@{configured=$true;status='waiting_for_live_ticks'}},
 [pscustomobject]@{encryptedCredentialsPresent=$true;mt5=[pscustomobject]@{configured=$true;status='terminal_closed'}},
 [pscustomobject]@{}
)
@($cases | ForEach-Object { Test-SentimentSetupRequired $_ }) | ConvertTo-Json -Compress
""" % path
        result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout),[True,True,True,False,False,True])


if __name__=='__main__':unittest.main()
