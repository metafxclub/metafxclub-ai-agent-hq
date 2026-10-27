"""Check the independent service survives release and installed-package boundaries."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from tests.test_release_candidate_preflight import REQUIRED_SENTIMENT_PACKAGE_FILES

ROOT=Path(__file__).resolve().parents[1]


class SentimentPackageTests(unittest.TestCase):
    def test_inventory_covers_every_backend_module_at_all_boundaries(self):
        package=ROOT/'backend/local-runner/sentiment_universe'
        actual={p.relative_to(ROOT).as_posix() for p in package.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.js','.html','.css'}}
        required={p for p in REQUIRED_SENTIMENT_PACKAGE_FILES if p.startswith('backend/local-runner/sentiment_universe/')}
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

    def test_isolated_universe_package_requires_its_shared_pure_news_contract(self):
        overlay='backend/local-runner/sentiment_universe/live_backend/news_ai_overlay.py'
        contract='backend/local-runner/hq_backend/research/sentiment_news_ai.py'
        for path in (overlay,contract):
            self.assertIn(path,REQUIRED_SENTIMENT_PACKAGE_FILES)
        probe=r'''
import importlib.util,json,os,sys
from pathlib import Path
def guard(event,args):
    if event.startswith(('socket.','subprocess.')) or event in ('os.system','os.mkdir','os.remove','os.rename'):
        raise AssertionError('unexpected side effect: '+event)
    if event=='open':
        mode=args[1] if len(args)>1 else None
        flags=args[2] if len(args)>2 else 0
        if (isinstance(mode,str) and any(char in mode for char in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
            raise AssertionError('unexpected write')
sys.addaudithook(guard)
path=Path(sys.argv[1])
spec=importlib.util.spec_from_file_location('isolated_universe_overlay',path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
try:
    shared=module.contract()
    result={'ready':True,'profile':shared.RESULT_PROFILE,'bridgeLoaded':any('bridge_server' in name for name in sys.modules)}
except FileNotFoundError:
    result={'ready':False,'reason':'shared_contract_missing'}
print(json.dumps(result))
'''
        with tempfile.TemporaryDirectory(prefix='sentiment-contract-package-') as temporary:
            root=Path(temporary)
            for relative in (overlay,contract):
                destination=root/relative
                destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/relative,destination)
            def check():
                run=subprocess.run([sys.executable,'-I','-B','-c',probe,str(root/overlay)],capture_output=True,text=True,timeout=15)
                self.assertEqual(run.returncode,0,run.stderr)
                return json.loads(run.stdout)
            self.assertEqual(check(),{'ready':True,'profile':'sentiment_news_daily_v1','bridgeLoaded':False})
            (root/contract).unlink()
            self.assertEqual(check(),{'ready':False,'reason':'shared_contract_missing'})

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
