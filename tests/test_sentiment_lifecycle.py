"""Isolated lifecycle checks. Never load a provider, a terminal, or user state."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'backend/local-runner/sentiment_universe'

FAKE_SERVER = '''import argparse,json,os
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
p=argparse.ArgumentParser()
p.add_argument('--port',type=int);p.add_argument('--state-dir',type=Path)
p.add_argument('--static-dir');p.add_argument('--public-mirror')
a=p.parse_args(); root=Path(__file__).resolve().parents[1]
a.state_dir.mkdir(parents=True,exist_ok=True)
record={'pid':os.getpid(),'project':str(root),'service':'sentiment-universe','ok':True}
(a.state_dir/'service.json').write_text(json.dumps(record))
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  body=json.dumps(record).encode();self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def log_message(self,*args):pass
HTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
'''


@unittest.skipUnless(os.name == 'nt', 'Windows lifecycle')
class SentimentLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sentiment-lifecycle-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'fake hq'
        self.package = self.root / 'backend/local-runner/sentiment_universe'
        self.state = Path(self.temp.name) / 'private state'
        self.state.mkdir(parents=True)
        (self.state / 'credentials.dpapi').write_bytes(b'private canary')
        (self.state / 'limits.json').write_text('{"sentinel":42}')
        (self.root / 'scripts').mkdir(parents=True)
        (self.package / 'scripts').mkdir(parents=True)
        (self.package / 'live_backend').mkdir()
        static = self.root / 'frontend/public/sentiment-universe'
        static.mkdir(parents=True)
        (static / 'index.html').write_text('isolated fixture')
        shutil.copy2(ROOT / 'scripts/sentiment-universe.ps1', self.root / 'scripts')
        shutil.copy2(PACKAGE / 'scripts/start-live.py', self.package / 'scripts')
        (self.package / 'live_backend/__init__.py').touch()
        (self.package / 'live_backend/server.py').write_text(FAKE_SERVER)
        self.pythonw = Path(sys.executable).with_name('pythonw.exe')
        self.assertTrue(self.pythonw.is_file())
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            self.port = sock.getsockname()[1]
        self.owned_pids = set()
        self.addCleanup(self.cleanup_processes)

    def invoke(self, action):
        result = subprocess.run(['powershell.exe', '-NoLogo', '-NoProfile', '-NonInteractive',
            '-ExecutionPolicy', 'Bypass', '-File', str(self.root / 'scripts/sentiment-universe.ps1'),
            '-Action', action, '-Port', str(self.port), '-StateDirectory', str(self.state),
            '-PythonPath', str(self.pythonw)], capture_output=True, text=True, timeout=75)
        if result.returncode == 0:
            value = json.loads(result.stdout.strip().splitlines()[-1])
            for name in ('supervisorPid', 'workerPid'):
                if value.get(name): self.owned_pids.add(value[name])
        return result

    def cleanup_processes(self):
        # Only exact fixture process IDs whose command lines contain this temp root.
        for pid in self.owned_pids:
            cmd = "$p=Get-CimInstance Win32_Process -Filter 'ProcessId=%d'; if($p -and $p.CommandLine.Contains('%s')){Stop-Process -Id %d -Force}" % (pid, self.temp.name.replace("'", "''"), pid)
            subprocess.run(['powershell.exe','-NoProfile','-Command',cmd],capture_output=True)

    def assert_private_state(self):
        self.assertEqual((self.state / 'credentials.dpapi').read_bytes(), b'private canary')
        self.assertEqual(json.loads((self.state / 'limits.json').read_text()), {'sentinel':42})

    def test_ensure_is_idempotent_and_stop_ends_both_processes(self):
        first = self.invoke('Ensure')
        self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
        one = json.loads(first.stdout)
        second = self.invoke('Ensure')
        self.assertEqual(second.returncode, 0, second.stderr)
        two = json.loads(second.stdout)
        self.assertEqual((one['workerPid'],one['supervisorPid']), (two['workerPid'],two['supervisorPid']))
        stopped = self.invoke('Stop')
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(json.loads(stopped.stdout)['stoppedCount'], 2)
        time.sleep(1)
        state = self.invoke('Status')
        self.assertEqual(json.loads(state.stdout)['status'], 'stopped')
        for pid in (one['workerPid'], one['supervisorPid']):
            check = subprocess.run(['powershell.exe','-NoProfile','-Command',f'if(Get-Process -Id {pid} -ErrorAction SilentlyContinue){{exit 5}}'],capture_output=True)
            self.assertEqual(check.returncode, 0, 'owned child or supervisor still alive')
        self.assert_private_state()

    def test_foreign_port_is_preserved(self):
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',self.port)); listener.listen()
            result = self.invoke('Ensure')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('no process was stopped', result.stderr)
            self.assertFalse((self.state/'supervisor.json').exists())
            self.assertEqual(listener.getsockname()[1],self.port)
        self.assert_private_state()

    def test_stale_record_cannot_kill_foreign_process(self):
        process = subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])
        def cleanup_foreign():
            if process.poll() is None: process.terminate()
            process.wait(timeout=5)
        self.addCleanup(cleanup_foreign)
        (self.state/'supervisor.json').write_text(json.dumps({'pid':process.pid}))
        result = self.invoke('Stop')
        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(process.poll())
        self.assertIn('identity is unverified',result.stderr)
        self.assert_private_state()

    def test_mutex_rejects_second_supervisor_and_worker_crash_recovers(self):
        result = self.invoke('Ensure')
        self.assertEqual(result.returncode, 0, result.stderr)
        initial = json.loads(result.stdout)
        command = [str(self.pythonw),str(self.package/'scripts/start-live.py'),
                   '--port',str(self.port),'--state-dir',str(self.state),
                   '--static-dir',str(self.root/'frontend/public/sentiment-universe'),
                   '--public-mirror',str(self.root/'frontend/public/sentiment-universe/market.json')]
        duplicate = subprocess.run(command,cwd=self.package,timeout=5)
        self.assertEqual(duplicate.returncode,0)
        self.assertEqual(json.loads((self.state/'supervisor.json').read_text())['pid'],initial['supervisorPid'])
        # Kill only the child created by this isolated fixture, then verify the
        # same supervisor creates exactly one replacement without data loss.
        subprocess.run(['powershell.exe','-NoProfile','-Command',f"Stop-Process -Id {initial['workerPid']} -Force"],check=True)
        deadline=time.monotonic()+25
        recovered=None
        while time.monotonic()<deadline:
            time.sleep(1)
            record=json.loads((self.state/'service.json').read_text())
            if record['pid']!=initial['workerPid']:
                recovered=record['pid'];self.owned_pids.add(recovered);break
        self.assertIsNotNone(recovered,'supervisor did not restart its fixture worker')
        status=self.invoke('Status')
        value=json.loads(status.stdout)
        self.assertEqual(value['supervisorPid'],initial['supervisorPid'])
        self.assertEqual(value['workerPid'],recovered)
        self.assertEqual(self.invoke('Stop').returncode,0)
        self.assert_private_state()

    def test_stop_recovers_owned_child_before_metadata_publication(self):
        started=self.invoke('Ensure')
        self.assertEqual(started.returncode,0,started.stderr)
        status=json.loads(started.stdout)
        path=self.state/'supervisor.json'
        record=json.loads(path.read_text());record['childPid']=None;path.write_text(json.dumps(record))
        (self.state/'service.json').unlink()
        stopped=self.invoke('Stop')
        self.assertEqual(stopped.returncode,0,stopped.stderr)
        self.assertEqual(json.loads(stopped.stdout)['stoppedCount'],2)
        time.sleep(.3)
        check=subprocess.run(['powershell.exe','-NoProfile','-Command',f"if(Get-Process -Id {status['workerPid']} -ErrorAction SilentlyContinue){{exit 9}}"],capture_output=True)
        self.assertEqual(check.returncode,0,'worker escaped before metadata publication')


class SentimentSupervisorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('sentiment_supervisor',PACKAGE/'scripts/start-live.py')
        cls.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.module)

    def test_installed_cli_forwards_paths_without_shell(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            options=self.module.arguments(['--port','45231','--state-dir',str(root/'state'),'--static-dir',str(root/'web'),'--public-mirror',str(root/'web/market.json')])
            command=self.module.child_command(options,'pythonw.exe')
            self.assertEqual(command[:5],['pythonw.exe','-m','live_backend.server','--port','45231'])
            self.assertEqual(command[-2:],['--public-mirror',str(root/'web/market.json')])
            self.assertEqual(self.module.mutex_name(options),self.module.mutex_name(options))

    def test_private_state_cannot_be_under_webroot(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(SystemExit):
                self.module.arguments(['--state-dir',str(Path(folder)/'web/state'),'--static-dir',str(Path(folder)/'web')])


if __name__ == '__main__':
    unittest.main()
