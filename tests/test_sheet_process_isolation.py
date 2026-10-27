from __future__ import annotations

import copy
import importlib.util
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import venv
from contextlib import ExitStack
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "backend" / "local-runner" / "bridge_server.py"
EXECUTOR_PATH = ROOT / "backend" / "local-runner" / "hq_backend" / "research" / "sheet_executor.py"


class SheetExecutorProcessTests(unittest.TestCase):
    """Real owned pipes/processes with a stdlib fixture, never the production worker."""

    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("sheet_executor_process_test", EXECUTOR_PATH)
        assert spec is not None and spec.loader is not None
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="sheet-child-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.fixture = Path(self.temp.name) / "fixture.py"
        self.fixture.write_text("""import json, os, sys, time
count = 0
for line in sys.stdin.buffer:
    request = json.loads(line)
    count += 1
    args = request['args']
    mode = args[0] if args else 'echo'
    if mode == 'stall': time.sleep(30)
    if mode == 'exit': os._exit(3)
    response = {'version': 1, 'id': request['id'], 'ok': True,
                'result': {'pid': os.getpid(), 'count': count, 'args': args}}
    if mode == 'wrong_id': response['id'] = '0' * 32
    if mode == 'error':
        response = {'version': 1, 'id': request['id'], 'ok': False,
                    'error': {'code': args[1], 'writeUnknown': args[2], 'status': args[3],
                              'message': 'fixture-secret-must-not-leak'}}
    print(json.dumps(response), flush=True)
""", encoding="utf-8")
        fixture = self.fixture

        class FixtureExecutor(self.module.SheetExecutor):
            def _worker_command(self):
                return [sys.executable, "-I", "-B", "-u", str(fixture)]

        self.executor = FixtureExecutor(ROOT)
        self.addCleanup(self.executor.close)

    def call(self, mode="echo", *, operation="google.read_values", timeout=3):
        return self.executor.call(operation, [mode], {}, timeout_seconds=timeout)

    def test_reuses_exact_owned_child_for_sequential_requests(self) -> None:
        first = self.call()
        second = self.call()
        self.assertEqual(first["pid"], second["pid"])
        self.assertEqual((first["count"], second["count"]), (1, 2))
        self.assertEqual(self.executor.status()["completedCalls"], 2)
        self.assertFalse(self.executor.status()["busy"])

    def test_timeout_is_bounded_and_only_dispatched_write_is_ambiguous(self) -> None:
        for operation in ("google.read_values", "google.upsert_row", "projection.report_items"):
            with self.subTest(operation=operation):
                started = time.monotonic()
                with self.assertRaises(self.module.SheetExecutorError) as caught:
                    self.call("stall", operation=operation, timeout=0.3)
                self.assertLess(time.monotonic() - started, 2.5)
                self.assertEqual(caught.exception.code, "sheet_worker_timeout")
                self.assertEqual(caught.exception.write_unknown, operation == "google.upsert_row")
                self.assertFalse(self.executor.status()["running"])

    def test_status_remains_nonblocking_and_timeout_does_not_automatically_replay(self) -> None:
        failures = []

        def blocked():
            try:
                self.call("stall", timeout=1)
            except self.module.SheetExecutorError as error:
                failures.append(error)

        thread = threading.Thread(target=blocked)
        thread.start()
        self.addCleanup(thread.join, 3)
        deadline = time.monotonic() + 2
        while not self.executor.status()["busy"] and time.monotonic() < deadline:
            time.sleep(0.01)
        owned = self.executor._process
        started = time.monotonic()
        self.assertTrue(self.executor.status()["busy"])
        self.assertLess(time.monotonic() - started, 0.15)
        with self.assertRaises(self.module.SheetExecutorError) as caught:
            self.call(timeout=0.1)
        self.assertEqual(caught.exception.code, "sheet_worker_busy")
        self.assertIs(self.executor._process, owned)
        thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual([error.code for error in failures], ["sheet_worker_timeout"])
        self.assertEqual(self.executor.status()["completedCalls"], 0)
        resumed = self.call()
        self.assertEqual(resumed["count"], 1)
        self.assertNotEqual(resumed["pid"], owned.pid)

    def test_no_replacement_until_previous_child_exit_is_confirmed(self) -> None:
        self.call()
        owned = self.executor._process
        with mock.patch.object(self.executor, "_stop_owned", return_value=False):
            with self.assertRaises(self.module.SheetExecutorError):
                self.call("stall", timeout=0.2)
            with self.assertRaises(self.module.SheetExecutorError) as caught:
                self.call(timeout=0.3)
            self.assertEqual(caught.exception.code, "sheet_worker_unavailable")
            self.assertIs(self.executor._process, owned)
            self.assertIsNone(owned.poll())

    def test_child_death_and_wrong_response_id_poison_session_without_replay(self) -> None:
        for mode, expected in (("exit", "sheet_worker_exited"), ("wrong_id", "sheet_worker_protocol_error")):
            with self.subTest(mode=mode):
                with self.assertRaises(self.module.SheetExecutorError) as caught:
                    self.call(mode, operation="google.upsert_row")
                self.assertEqual(caught.exception.code, expected)
                self.assertTrue(caught.exception.write_unknown)
                self.assertFalse(self.executor.status()["running"])
                self.assertEqual(self.call()["count"], 1)

    def test_provider_error_preserves_ambiguity_and_redacts_untrusted_message(self) -> None:
        first = self.call()
        for code, ambiguous, status in (("write_unknown", True, 502), ("permission_denied", False, 403), ("rate_limited", False, 429)):
            with self.subTest(code=code):
                with self.assertRaises(self.module.SheetExecutorError) as caught:
                    self.executor.call("google.upsert_row", ["error", code, ambiguous, status], {}, timeout_seconds=3)
                self.assertEqual((caught.exception.code, caught.exception.write_unknown, caught.exception.status), (code, ambiguous, status))
                self.assertNotIn("fixture-secret", str(caught.exception))
                self.assertEqual(self.executor._process.pid, first["pid"])

    def test_invalid_or_oversized_request_never_starts_child(self) -> None:
        cases = [("arbitrary.exec", [], {}), ("google.read_values", [float("nan")], {}),
                 ("google.read_values", ["x" * self.module.MAX_FRAME_BYTES], {})]
        with mock.patch.object(self.module.subprocess, "Popen", side_effect=AssertionError("Invalid request launched child")):
            for operation, args, kwargs in cases:
                with self.subTest(operation=operation, size=len(args)):
                    with self.assertRaises(self.module.SheetExecutorError):
                        self.executor.call(operation, args, kwargs)
        self.assertFalse(self.executor.status()["running"])

    def test_close_prevents_restart(self) -> None:
        self.call()
        child = self.executor._process
        self.executor.close()
        self.assertIsNotNone(child.poll())
        with self.assertRaises(self.module.SheetExecutorError) as caught:
            self.call()
        self.assertEqual(caught.exception.code, "sheet_worker_closed")
        self.assertTrue(self.executor.status()["closed"])

    @unittest.skipUnless(os.name == "nt", "Windows venv redirector contract")
    def test_windows_venv_launch_uses_base_interpreter_and_child_only_environment(self) -> None:
        base = str(Path(sys._base_executable).resolve())
        virtual = str(Path(self.temp.name) / "venv" / "Scripts" / "python.exe")
        command = [virtual, "-I", "-B", "-u", "fixture-worker.py"]
        with (
            mock.patch.object(self.module.sys, "executable", virtual),
            mock.patch.object(self.module.sys, "_base_executable", base),
            mock.patch.dict(os.environ, {"__PYVENV_LAUNCHER__": "fixture-parent-value", "SHEET_FIXTURE_INHERITED": "preserved"}),
        ):
            selected, environment = self.module._direct_worker_launch(command)
            self.assertEqual(selected, [base, *command[1:]])
            self.assertEqual(command[0], virtual, "Do not mutate the caller's command")
            self.assertEqual(environment["__PYVENV_LAUNCHER__"], virtual)
            self.assertEqual(environment["SHEET_FIXTURE_INHERITED"], "preserved")
            self.assertEqual(os.environ["__PYVENV_LAUNCHER__"], "fixture-parent-value")
            environment["SHEET_FIXTURE_INHERITED"] = "child-only"
            self.assertEqual(os.environ["SHEET_FIXTURE_INHERITED"], "preserved")

    @unittest.skipUnless(os.name == "nt", "Windows venv redirector contract")
    def test_base_interpreter_and_explicit_fixture_executable_keep_original_launch(self) -> None:
        base = str(Path(sys._base_executable).resolve())
        with mock.patch.object(self.module.sys, "executable", base), mock.patch.object(self.module.sys, "_base_executable", base):
            command = [base, "-I", "fixture.py"]
            self.assertEqual(self.module._direct_worker_launch(command), (command, None))
        virtual = str(Path(self.temp.name) / "venv" / "Scripts" / "python.exe")
        with mock.patch.object(self.module.sys, "executable", virtual), mock.patch.object(self.module.sys, "_base_executable", base):
            command = [base, "-I", "explicit-fixture.py"]
            self.assertEqual(self.module._direct_worker_launch(command), (command, None))

    @unittest.skipUnless(os.name == "nt", "Windows venv redirector contract")
    def test_invalid_base_interpreter_never_falls_back_to_venv_launcher(self) -> None:
        virtual = str(Path(self.temp.name) / "venv" / "Scripts" / "python.exe")
        for invalid in (None, "", str(Path(self.temp.name) / "missing-python.exe"), self.temp.name):
            with (
                self.subTest(base=invalid),
                mock.patch.object(self.module.sys, "executable", virtual),
                mock.patch.object(self.module.sys, "_base_executable", invalid),
                mock.patch.object(self.module.subprocess, "Popen", side_effect=AssertionError("Unsafe launcher fallback")) as launch,
            ):
                with self.assertRaises(self.module.SheetExecutorError) as caught:
                    self.call()
                self.assertEqual(caught.exception.code, "sheet_worker_start_failed")
                launch.assert_not_called()

    @unittest.skipUnless(os.name == "nt", "Exercises the actual Windows venv redirector")
    def test_windows_venv_worker_is_direct_child_and_exits_during_projection_on_owner_death(self) -> None:
        import ctypes
        from ctypes import wintypes

        project = Path(self.temp.name) / "venv-owner-checkout"
        runner = project / "backend" / "local-runner"
        runner.mkdir(parents=True)
        source_package = ROOT / "backend" / "local-runner" / "hq_backend"
        for source in source_package.rglob("*.py"):
            target = runner / "hq_backend" / source.relative_to(source_package)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        (runner / "bridge_server.py").write_text("""import ctypes, os, sys, time
from ctypes import wintypes
def _load_dashboard_workflow_settings_read_only(): return {}
def _research_sheet_report_items(report, revision, **kwargs):
    if report.get('stallEvent'):
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenEventW.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR)
        kernel.OpenEventW.restype = wintypes.HANDLE
        kernel.SetEvent.argtypes = (wintypes.HANDLE,)
        kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
        event = kernel.OpenEventW(2, False, report['stallEvent'])
        if not event: raise RuntimeError('fixture event unavailable')
        kernel.SetEvent(event)
        kernel.CloseHandle(event)
        time.sleep(10)
    return [{'pid': os.getpid(), 'parentPid': os.getppid(),
             'executable': sys.executable, 'prefix': sys.prefix}]
""", encoding="utf-8")
        virtual_root = project / "fixture-venv"
        venv.EnvBuilder(with_pip=False).create(virtual_root)
        virtual = str(virtual_root / "Scripts" / "python.exe")
        base = str(Path(sys._base_executable).resolve())
        parent_script = project / "fixture_bridge.py"
        parent_script.write_text("""import importlib.util, json, os, pathlib, sys, threading
root = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location('fixture_sheet_executor', root / 'backend/local-runner/hq_backend/research/sheet_executor.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
executor = module.SheetExecutor(root)
result = executor.call('projection.report_items', [{}, 3], {}, timeout_seconds=10)[0]
print(json.dumps({'ownerPid': os.getpid(), 'ownedPid': executor._process.pid,
                  'ownerExecutable': sys.executable, 'ownerPrefix': sys.prefix, 'worker': result}), flush=True)
sys.stdin.readline()
def stall():
    executor.call('projection.report_items', [{'stallEvent': sys.argv[2]}, 3], {}, timeout_seconds=15)
threading.Thread(target=stall, daemon=True).start()
sys.stdin.readline()
executor.close()
""", encoding="utf-8")
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateEventW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR)
        kernel.CreateEventW.restype = wintypes.HANDLE
        kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.TerminateProcess.argtypes = (wintypes.HANDLE, wintypes.UINT)
        kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
        event_name = "Local\\MetafxSheetFixture-" + Path(self.temp.name).name
        event = kernel.CreateEventW(None, True, False, event_name)
        self.assertTrue(event)
        self.addCleanup(kernel.CloseHandle, event)
        environment = os.environ.copy()
        environment.update({"__PYVENV_LAUNCHER__": virtual,
                            "LOCALAPPDATA": str(project / "fixture-local-appdata"),
                            "APPDATA": str(project / "fixture-roaming-appdata"),
                            "CODEX_HOME": str(project / "fixture-codex")})
        for name in list(environment):
            if name.startswith("METAFX_GOOGLE_"):
                del environment[name]
        parent = subprocess.Popen([base, "-I", "-B", "-u", str(parent_script), str(project), event_name],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  text=True, env=environment, creationflags=subprocess.CREATE_NO_WINDOW)
        owned_handles = {}
        lines = queue.Queue()
        reader = threading.Thread(target=lambda: lines.put(parent.stdout.readline()), daemon=True)
        reader.start()
        try:
            line = lines.get(timeout=15)
            self.assertTrue(line, "Fixture Bridge exited before the worker responded")
            facts = json.loads(line)
            self.assertEqual(facts["ownerPid"], parent.pid)
            for pid in {facts["ownedPid"], facts["worker"]["pid"]}:
                handle = kernel.OpenProcess(0x00100000 | 0x0001, False, pid)
                self.assertTrue(handle, "Fixture worker must still be alive")
                owned_handles[pid] = handle
            self.assertEqual(Path(facts["ownerExecutable"]), Path(virtual))
            self.assertEqual(Path(facts["ownerPrefix"]), virtual_root)
            self.assertEqual(Path(facts["worker"]["executable"]), Path(virtual))
            self.assertEqual(Path(facts["worker"]["prefix"]), virtual_root)
            parent.stdin.write("stall\n")
            parent.stdin.flush()
            self.assertEqual(kernel.WaitForSingleObject(event, 5000), 0, "The actual worker must enter its slow projection")
            parent.kill()  # Only the owned temporary Bridge fixture.
            parent.wait(timeout=3)
            worker_exit = kernel.WaitForSingleObject(owned_handles[facts["worker"]["pid"]], 4000)
            self.assertEqual(worker_exit, 0, "Worker survived owner death inside a 10-second projection")
            self.assertEqual(facts["ownedPid"], facts["worker"]["pid"], "Popen must own the real worker, not a venv redirector")
            self.assertEqual(facts["worker"]["parentPid"], parent.pid, "Worker must monitor the Bridge directly")
        finally:
            if parent.poll() is None:
                parent.kill()
                parent.wait(timeout=3)
            for handle in owned_handles.values():
                if kernel.WaitForSingleObject(handle, 0) == 258:
                    kernel.TerminateProcess(handle, 1)
                self.assertEqual(kernel.WaitForSingleObject(handle, 3000), 0, "Temporary fixture process cleanup failed")
                kernel.CloseHandle(handle)
            parent.stdin.close()
            parent.stdout.close()
            reader.join(timeout=1)

    def test_worker_guard_blocks_shared_mutations_network_and_processes_for_projection(self) -> None:
        guard = self.module._WorkerGuard(Path(self.temp.name) / "credential-store")
        guard.mode = "projection"
        for event, args in (
            ("open", (str(Path(self.temp.name) / "outbox.json"), "w", os.O_WRONLY)),
            ("os.rename", (str(Path(self.temp.name) / "outbox.json"), str(Path(self.temp.name) / "cache.json"), -1, -1)),
            ("socket.connect", (object(), ("127.0.0.1", 12345))),
            ("subprocess.Popen", ("terminal64.exe", [], None, None)),
        ):
            with self.subTest(event=event), self.assertRaises(PermissionError):
                guard(event, args)
        guard("open", (str(Path(self.temp.name) / "report.json"), "r", os.O_RDONLY))
        guard.mode = "google"
        guard("open", (str(Path(self.temp.name) / "credential-store" / "token.json"), "w", os.O_WRONLY))
        with self.assertRaises(PermissionError):
            guard("open", (str(Path(self.temp.name) / "outbox.json"), "w", os.O_WRONLY))

    def test_process_lease_excludes_second_owner_and_releases_after_owned_child_death(self) -> None:
        lease_root = Path(self.temp.name) / "lease-checkout"
        lease_root.mkdir()
        script = Path(self.temp.name) / "lease_holder.py"
        script.write_text("""import importlib.util, pathlib, sys
spec = importlib.util.spec_from_file_location('fixture_lease_module', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
lease = module._acquire_worker_lease(pathlib.Path(sys.argv[2]))
print('owned' if lease else 'blocked', flush=True)
sys.stdin.readline()
module._release_worker_lease(lease)
""", encoding="utf-8")
        options = {"stdin": subprocess.PIPE, "stdout": subprocess.PIPE, "stderr": subprocess.DEVNULL, "text": True}
        if os.name == "nt":
            options["creationflags"] = subprocess.CREATE_NO_WINDOW
        child = subprocess.Popen([sys.executable, "-I", "-B", "-u", str(script), str(EXECUTOR_PATH), str(lease_root)], **options)
        try:
            self.assertEqual(child.stdout.readline().strip(), "owned")
            self.assertIsNone(self.module._acquire_worker_lease(lease_root))
            child.kill()
            child.wait(timeout=3)
            lease = self.module._acquire_worker_lease(lease_root)
            self.assertIsNotNone(lease)
            self.module._release_worker_lease(lease)
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=3)
            child.stdin.close()
            child.stdout.close()

    def test_parent_monitor_observes_current_parent_and_closes_without_exit(self) -> None:
        with mock.patch.object(self.module.os, "_exit", side_effect=AssertionError("Live fixture parent must not trigger exit")) as exit_process:
            monitor = self.module._ParentDeathMonitor()
            self.assertTrue(monitor.start())
            self.assertEqual(monitor.parent_pid, os.getppid())
            monitor.close()
            self.assertFalse(monitor.thread.is_alive())
            exit_process.assert_not_called()

    def test_parent_death_exits_only_the_fixture_worker_and_releases_its_pipe(self) -> None:
        child_script = Path(self.temp.name) / "monitored_child.py"
        child_script.write_text("""import importlib.util, sys, time
spec = importlib.util.spec_from_file_location('fixture_monitor_module', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
monitor = module._ParentDeathMonitor()
if not monitor.start(): raise SystemExit(3)
print('monitor-ready', flush=True)
time.sleep(8)
monitor.close()
""", encoding="utf-8")
        parent_script = Path(self.temp.name) / "fixture_parent.py"
        parent_script.write_text("""import os, subprocess, sys
options = {'stdin': subprocess.DEVNULL, 'stdout': sys.stdout, 'stderr': subprocess.DEVNULL}
if os.name == 'nt': options['creationflags'] = subprocess.CREATE_NO_WINDOW
child = subprocess.Popen([sys.executable, '-I', '-B', '-u', sys.argv[1], sys.argv[2]], **options)
sys.stdin.readline()
os._exit(0)
""", encoding="utf-8")
        options = {"stdin": subprocess.PIPE, "stdout": subprocess.PIPE, "stderr": subprocess.DEVNULL, "text": True}
        if os.name == "nt":
            options["creationflags"] = subprocess.CREATE_NO_WINDOW
        parent = subprocess.Popen([sys.executable, "-I", "-B", "-u", str(parent_script), str(child_script), str(EXECUTOR_PATH)], **options)
        try:
            self.assertEqual(parent.stdout.readline().strip(), "monitor-ready")
            # The grandchild inherits this pipe. EOF proves that the orphan
            # monitor exited it, rather than merely letting its parent exit.
            parent.communicate(input="exit\n", timeout=4)
            self.assertEqual(parent.returncode, 0)
        finally:
            if parent.poll() is None:
                parent.kill()
                parent.wait(timeout=3)
            if parent.stdin:
                parent.stdin.close()
            if parent.stdout:
                parent.stdout.close()

    def test_real_projection_child_imports_without_mutating_runtime_or_using_credentials(self) -> None:
        project = Path(self.temp.name) / "projection-checkout"
        runner = project / "backend" / "local-runner"
        runner.mkdir(parents=True)
        shutil.copyfile(BRIDGE_PATH, runner / "bridge_server.py")
        source_package = ROOT / "backend" / "local-runner" / "hq_backend"
        for source in source_package.rglob("*.py"):
            target = runner / "hq_backend" / source.relative_to(source_package)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        runtime = project / "data" / "runtime"
        runtime.mkdir(parents=True)
        marker = runtime / "fixture-preserve.json"
        marker.write_text('{"unchanged":true}', encoding="utf-8")
        before = {str(p.relative_to(runtime)): p.read_bytes() for p in runtime.rglob("*") if p.is_file()}
        bootstrap = project / "guarded_worker.py"
        bootstrap.write_text("""import os, pathlib, runpy, sys
root = pathlib.Path(sys.argv[1])
os.environ['LOCALAPPDATA'] = str(root / 'fixture-local-appdata')
os.environ['APPDATA'] = str(root / 'fixture-roaming-appdata')
os.environ['CODEX_HOME'] = str(root / 'fixture-codex')
for name in list(os.environ):
    if name.startswith('METAFX_GOOGLE_'): del os.environ[name]
def guard(event, args):
    if event.startswith('socket.') or event == 'subprocess.Popen':
        raise PermissionError('Fixture forbids network and child launches')
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.fsdecode(args[0]).replace('\\\\', '/').lower()
        if path.endswith('.dpapi') or path.endswith('/auth.json') or path.endswith('google_oauth_native_client.txt'):
            raise PermissionError('Fixture forbids credential reads')
sys.addaudithook(guard)
script = root / 'backend/local-runner/hq_backend/research/sheet_executor.py'
sys.argv = [str(script), '--worker', '--project-root', str(root)]
runpy.run_path(str(script), run_name='__main__')
""", encoding="utf-8")

        class ProductionFixtureExecutor(self.module.SheetExecutor):
            def _worker_command(self):
                return [sys.executable, "-I", "-B", "-u", str(bootstrap), str(project)]

        executor = ProductionFixtureExecutor(project)
        try:
            empty = executor.call("projection.report_items", [{"id": "fixture-noneligible", "type": "prop_report"}, 3], {}, timeout_seconds=30)
            self.assertEqual(empty, [])
            systems = [{
                "recordId": f"world-{index}", "systemName": f"Verified fixture {index}",
                "sourceTitle": "Fixture source", "sourceUrl": f"https://www.tradingview.com/scripts/system-{index}",
                "corroboratingUrls": [f"https://github.com/metafxclub/system-{index}"],
                "checkedAt": "2026-10-01T00:00:00Z", "verificationStatus": "verified",
                "duplicateStatus": "unique", "duplicateFingerprint": f"fixture-fp-{index}",
                "strategyFamily": "trend_following", "symbols": ["EURUSD"], "timeframes": ["H1"],
                "entrySteps": ["EMA cross"], "exitSteps": ["ATR target"],
                "riskManagement": {"maxRiskPerTrade": "1%", "sourceUrl": f"https://www.tradingview.com/scripts/system-{index}"},
            } for index in range(1, 4)]
            report = {"id": "fixture-world-report", "type": "trading_system_discovery_report", "status": "ready",
                      "linkedPropId": "codex_mcp_portal", "linkedMissionId": "fixture-mission",
                      "createdAt": "2026-10-01T00:00:00Z", "updatedAt": "2026-10-01T00:00:00Z",
                      "metrics": {"workflowOutput": {"applicable": True, "valid": True}, "systems": systems}}
            rows = executor.call("projection.report_items", [report, 3], {}, timeout_seconds=30)
            self.assertEqual(len(rows), 3)
            self.assertTrue(all(row["reportId"] == report["id"] and row["configRevision"] == 3 for row in rows))
            self.assertEqual(executor.status()["completedCalls"], 2)
        finally:
            executor.close()
        after = {str(p.relative_to(runtime)): p.read_bytes() for p in runtime.rglob("*") if p.is_file()}
        self.assertEqual(after, before)


class SheetBridgeIsolationTests(unittest.TestCase):
    """Synthetic stores only; no provider, protected credentials or terminal access."""

    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("sheet_process_isolation_bridge", BRIDGE_PATH)
        assert spec is not None and spec.loader is not None
        cls.bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.bridge)

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="sheet-isolation-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.reports = self.root / "reports"
        self.intents = self.root / "research-sheet-intents"
        self.reports.mkdir()
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.internal = {
            "sheetId": "1SyntheticIsolationSheetNoExternalAccount",
            "configRevision": 3, "activeConfigRevision": 3, "active": True,
        }
        for name, value in {
            "RUNTIME_DIR": self.root,
            "RUNTIME_REPORTS_DIR": self.reports,
            "RESEARCH_SHEET_INTENTS_DIR": self.intents,
            "RESEARCH_SHEET_OUTBOX_PATH": self.root / "outbox.json",
            "RESEARCH_SHEET_CACHE_PATH": self.root / "cache.json",
            "DASHBOARD_WORKFLOW_SETTINGS_PATH": self.root / "settings.json",
            "DEEP_RESEARCH_CONFIRMATIONS_PATH": self.root / "confirmations.json",
            "MISSIONS_PATH": self.root / "missions.json",
            "MEMORY_INDEX_PATH": self.root / "memory.json",
            "AUDIT_PATH": self.root / "audit.jsonl",
            "RESEARCH_SHEET_ISOLATION_ENABLED": True,
            "RESEARCH_SHEET_SERVICE_STOP": threading.Event(),
            "RESEARCH_SHEET_SERVICE_WAKE": threading.Event(),
            "RESEARCH_SHEET_INTENT_RETRY_AT": {},
        }.items():
            self.stack.enter_context(mock.patch.object(self.bridge, name, value))
        self.stack.enter_context(mock.patch.object(self.bridge, "_research_sheet_hub_internal", side_effect=lambda *args, **kwargs: copy.deepcopy(self.internal)))
        self.stack.enter_context(mock.patch.object(self.bridge, "append_audit"))
        self.stack.enter_context(mock.patch.object(self.bridge, "urlopen", side_effect=AssertionError("Bridge must not contact providers")))
        self.stack.enter_context(mock.patch("socket.socket.connect", side_effect=AssertionError("No network in Bridge fixture")))
        self.stack.enter_context(mock.patch.object(self.bridge.subprocess, "Popen", side_effect=AssertionError("Bridge fixture may not start processes")))
        self.stack.enter_context(mock.patch.object(self.bridge.google_sheet_hub, "credential_status", side_effect=AssertionError("No credential reads in Bridge fixture")))
        self.real_queue = self.bridge._research_sheet_queue_report
        self.queue = self.stack.enter_context(mock.patch.object(self.bridge, "_research_sheet_queue_report", return_value={"queued": 1, "reason": None}))
        self.flush = self.stack.enter_context(mock.patch.object(self.bridge, "_flush_research_sheet_outbox", side_effect=AssertionError("Intent handling must not deliver")))

    def report(self, ordinal: int, *, version: int = 1) -> dict:
        report = {
            "id": f"report-isolation-{ordinal:04d}",
            "type": "trading_system_research_report", "status": "ready",
            "linkedPropId": "left_server_racks", "linkedMissionId": "synthetic-mission",
            "createdAt": "2026-10-01T00:00:00Z",
            "updatedAt": f"2026-10-01T00:00:{version:02d}Z",
            "metrics": {"fixtureVersion": version},
        }
        (self.reports / f"{report['id']}.json").write_text(json.dumps(report), encoding="utf-8")
        return report

    def test_sheet_failure_is_diagnostic_and_cannot_degrade_healthy_core(self) -> None:
        healthy = {"status": "running", "alive": True, "operational": True}
        for status in ("stalled", "stopped", "timeout", "degraded"):
            with (
                self.subTest(status=status),
                mock.patch.object(self.bridge, "dashboard_workflow_scheduler_read_model", return_value=healthy),
                mock.patch.object(self.bridge, "mission_worker_read_model", return_value=healthy),
                mock.patch.object(self.bridge, "research_sheet_service_read_model", return_value={
                    "status": status, "phase": "sheet_flush", "lastHeartbeatAt": "2000-01-01T00:00:00Z",
                    "affectsCoreHealth": False, "executor": {"alive": False},
                }),
            ):
                health = self.bridge.runtime_health()
            self.assertTrue(health["ok"])
            self.assertEqual(health["status"], "ready")
            self.assertEqual(health["researchSheetService"]["status"], status)
            self.assertFalse(health["researchSheetService"]["affectsCoreHealth"])

    def test_healthy_sheet_worker_cannot_mask_stale_core_scheduler(self) -> None:
        with (
            mock.patch.object(self.bridge, "dashboard_workflow_scheduler_read_model", return_value={"alive": True, "operational": False, "heartbeatStale": True}),
            mock.patch.object(self.bridge, "mission_worker_read_model", return_value={"alive": True, "operational": True}),
            mock.patch.object(self.bridge, "research_sheet_service_read_model", return_value={"status": "ready", "affectsCoreHealth": False}),
        ):
            health = self.bridge.runtime_health()
        self.assertFalse(health["ok"])
        self.assertEqual(health["status"], "degraded")

    def test_report_intents_survive_beyond_legacy_240_report_scan_window(self) -> None:
        expected_ids = set()
        for ordinal in range(241):
            report = self.report(ordinal)
            expected_ids.add(report["id"])
            self.bridge._enqueue_research_sheet_report_intent(report)
        self.queue.assert_not_called()
        self.assertEqual(len(list(self.intents.glob("*.json"))), 241)
        with mock.patch.object(self.bridge, "load_runtime_reports", side_effect=AssertionError("Intent recovery must not use a truncated history scan")):
            for _ in range(121):
                previous = self.queue.call_count
                self.bridge._drain_research_sheet_report_intents(max_reports=2)
                self.assertLessEqual(self.queue.call_count - previous, 2)
        self.assertEqual({c.args[0]["id"] for c in self.queue.call_args_list}, expected_ids)
        self.assertEqual(self.queue.call_count, 241)
        self.assertEqual(list(self.intents.glob("*.json")), [])
        self.assertTrue(all(c.kwargs.get("flush") is False for c in self.queue.call_args_list))
        self.flush.assert_not_called()

    def test_intent_contains_identity_without_full_report_or_credentials(self) -> None:
        report = self.report(0)
        report["metrics"]["privateLongText"] = "synthetic-projection-body-not-for-intent"
        self.bridge._enqueue_research_sheet_report_intent(report)
        paths = list(self.intents.glob("*.json"))
        self.assertEqual(len(paths), 1)
        payload = json.loads(paths[0].read_text(encoding="utf-8-sig"))
        self.assertEqual(payload["reportId"], report["id"])
        self.assertNotIn("synthetic-projection-body-not-for-intent", paths[0].read_text(encoding="utf-8-sig"))
        self.assertNotIn("metrics", payload)
        self.assertNotIn("credentials", payload)
        self.queue.assert_not_called()

    def test_newer_intent_is_not_acknowledged_by_an_older_projection(self) -> None:
        first = self.report(0)
        self.bridge._enqueue_research_sheet_report_intent(first)

        def project_and_replace(report, **kwargs):
            self.bridge._enqueue_research_sheet_report_intent(self.report(0, version=2))
            return {"queued": 1, "reason": None}

        self.queue.side_effect = project_and_replace
        self.bridge._drain_research_sheet_report_intents(max_reports=1)
        self.assertEqual(len(list(self.intents.glob("*.json"))), 1)
        self.queue.side_effect = None
        self.bridge._drain_research_sheet_report_intents(max_reports=1)
        self.assertEqual(self.queue.call_args.args[0]["metrics"]["fixtureVersion"], 2)
        self.assertEqual(list(self.intents.glob("*.json")), [])

    def test_failed_intent_remains_durable_without_starving_next_report(self) -> None:
        for ordinal in range(2):
            self.bridge._enqueue_research_sheet_report_intent(self.report(ordinal))

        def project(report, **kwargs):
            if report["id"].endswith("0000"):
                raise OSError("fixture store unavailable")
            return {"queued": 1, "reason": None}

        self.queue.side_effect = project
        self.bridge._drain_research_sheet_report_intents(max_reports=2)
        self.assertEqual(self.queue.call_count, 2)
        remaining = list(self.intents.glob("*.json"))
        self.assertEqual(len(remaining), 1)
        self.assertEqual(json.loads(remaining[0].read_text(encoding="utf-8-sig"))["reportId"], "report-isolation-0000")
        self.bridge._drain_research_sheet_report_intents(max_reports=2)
        self.assertEqual(self.queue.call_count, 2, "Backoff prevents a hot retry loop")

    def test_intent_retained_until_capacity_has_durable_recovery_marker(self) -> None:
        self.bridge._enqueue_research_sheet_report_intent(self.report(0))
        self.queue.return_value = {"queued": 0, "reason": "outbox_capacity_reached", "deferredStored": False}
        self.bridge._drain_research_sheet_report_intents(max_reports=1)
        self.assertEqual(len(list(self.intents.glob("*.json"))), 1)
        self.bridge.RESEARCH_SHEET_INTENT_RETRY_AT.clear()
        self.queue.return_value = {"queued": 0, "reason": "outbox_capacity_reached", "deferredStored": True}
        self.bridge._drain_research_sheet_report_intents(max_reports=1)
        self.assertEqual(list(self.intents.glob("*.json")), [])

    def test_sheet_service_cycles_fairly_and_failure_does_not_enter_core_loop(self) -> None:
        clock = [100.0]
        seen = []
        waits = []
        wake = mock.Mock()

        def operation(phase):
            self.assertEqual(self.bridge.RESEARCH_SHEET_SERVICE_RUNTIME["phase"], phase)
            seen.append(phase)
            if phase == "sheet_flush":
                raise RuntimeError("fixture isolated provider timeout")
            return {"more": True, "eligibleDeferred": 1}

        def wait(timeout):
            self.assertEqual(self.bridge.RESEARCH_SHEET_SERVICE_RUNTIME["phase"], "waiting")
            waits.append(timeout)
            clock[0] += timeout
            if len(waits) == 10:
                self.bridge.RESEARCH_SHEET_SERVICE_STOP.set()

        wake.wait.side_effect = wait
        with (
            mock.patch.object(self.bridge.time, "monotonic", side_effect=lambda: clock[0]),
            mock.patch.object(self.bridge, "RESEARCH_SHEET_SERVICE_WAKE", wake),
            mock.patch.object(self.bridge, "RESEARCH_SHEET_AUTO_SYNC_ENABLED", True),
            mock.patch.object(self.bridge, "_drain_research_sheet_report_intents", side_effect=lambda **_: operation("sheet_intents")),
            mock.patch.object(self.bridge, "_flush_research_sheet_outbox", side_effect=lambda **_: operation("sheet_flush")),
            mock.patch.object(self.bridge, "_research_sheet_backfill_background_step", side_effect=lambda *_: operation("sheet_backfill")),
            mock.patch.object(self.bridge, "_research_sheet_drain_deferred_reports", side_effect=lambda **_: operation("sheet_deferred")),
            mock.patch.object(self.bridge, "_research_sheet_background_cache_step", side_effect=lambda *_: operation("sheet_cache")),
            mock.patch.object(self.bridge, "dashboard_workflow_scheduler_tick", side_effect=AssertionError("Sheet service cannot run Council/dashboard work")) as tick,
        ):
            self.bridge.research_sheet_service_loop()
        self.assertEqual(seen, ["sheet_intents", "sheet_flush", "sheet_backfill", "sheet_deferred", "sheet_cache"] * 2)
        self.assertEqual(self.bridge.RESEARCH_SHEET_SERVICE_RUNTIME["phase"], "stopped")
        tick.assert_not_called()

    def test_write_ahead_state_survives_interruption_before_provider_result(self) -> None:
        store = self.bridge._research_sheet_outbox_default()
        store["items"] = [{
            "id": "sheet-isolation-item", "status": "pending", "configRevision": 3,
            "payloadDigest": "synthetic-payload-digest", "consumerId": "deepResearch",
            "tabName": "Deep_Research", "keyHeader": "record_id", "recordKey": "fixture-record",
            "row": {"record_id": "fixture-record"}, "attemptCount": 0,
        }]
        self.bridge._save_research_sheet_outbox_unlocked(store)

        def interrupted(*args, **kwargs):
            saved = self.bridge._load_research_sheet_outbox_unlocked()["items"][0]
            self.assertEqual(saved["status"], "write_unknown")
            self.assertEqual(saved["lastErrorCode"], "sheet_worker_inflight")
            self.assertEqual(saved["attemptCount"], 0)
            self.assertIsNotNone(saved["nextAttemptAt"])
            raise KeyboardInterrupt("synthetic crash before response")

        with (
            mock.patch.object(self.bridge.google_sheet_hub, "credential_status", return_value={"configured": True}),
            mock.patch.object(self.bridge.google_sheet_hub, "upsert_row", side_effect=interrupted),
        ):
            with self.assertRaises(KeyboardInterrupt):
                self.bridge._flush_research_sheet_outbox_locked(max_items=1)
        remaining = self.bridge._load_research_sheet_outbox_unlocked()["items"]
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["status"], "write_unknown")

    def test_projection_errors_preserve_integrity_vs_transient_failure(self) -> None:
        from hq_backend.research.sheet_executor import SheetExecutorError
        report = self.report(0)
        for code, expected in (("sheet_projection_integrity_failed", self.bridge.DataIntegrityError),
                               ("sheet_worker_timeout", self.bridge.RequestError)):
            with self.subTest(code=code), mock.patch.object(self.bridge, "RESEARCH_SHEET_EXECUTOR") as executor:
                executor.call.side_effect = SheetExecutorError(code)
                with self.assertRaises(expected):
                    self.bridge._research_sheet_report_items(report, 3)

    def test_projection_reply_must_match_report_and_configuration(self) -> None:
        report = self.report(0)
        for reply in ([{"reportId": "foreign-report", "configRevision": 3}],
                      [{"reportId": report["id"], "configRevision": 2}], {"not": "a list"}):
            with self.subTest(reply=reply), mock.patch.object(self.bridge, "RESEARCH_SHEET_EXECUTOR") as executor:
                executor.call.return_value = reply
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._research_sheet_report_items(report, 3)

    def test_failed_executor_initialization_never_falls_back_to_inline_google_io(self) -> None:
        from hq_backend.research import sheet_executor
        names = ("read_values", "inspect_tabs", "probe_tabs", "upsert_row", "start_google_oauth", "complete_google_oauth", "disconnect_google_oauth")
        with ExitStack() as patches:
            for operation in sheet_executor.OPERATIONS:
                if operation.startswith("google."):
                    name = operation.removeprefix("google.")
                    patches.callback(setattr, self.bridge.google_sheet_hub, name, getattr(self.bridge.google_sheet_hub, name))
            originals = {name: patches.enter_context(mock.patch.object(self.bridge.google_sheet_hub, name, side_effect=AssertionError("Inline Google fallback forbidden"))) for name in names}
            patches.enter_context(mock.patch.object(self.bridge, "RESEARCH_SHEET_ISOLATION_ENABLED", False))
            patches.enter_context(mock.patch.object(self.bridge, "RESEARCH_SHEET_EXECUTOR", None))
            patches.enter_context(mock.patch.dict(self.bridge.RESEARCH_SHEET_PROXY_ORIGINALS, {}, clear=True))
            patches.enter_context(mock.patch.object(sheet_executor, "SheetExecutor", side_effect=OSError("fixture missing runtime")))
            self.bridge.initialize_research_sheet_process_isolation()
            self.assertTrue(self.bridge.RESEARCH_SHEET_ISOLATION_ENABLED)
            for name in names:
                with self.subTest(operation=name), self.assertRaises(self.bridge.google_sheet_hub.GoogleSheetHubError) as caught:
                    getattr(self.bridge.google_sheet_hub, name)()
                self.assertEqual(caught.exception.code, "sheet_worker_unavailable")
                originals[name].assert_not_called()

    def test_report_commit_only_persists_intent_and_never_waits_for_projection_or_delivery(self) -> None:
        payload = {"id": "report-save-isolated", "type": "indicator_scout_report", "status": "ready",
                   "linkedPropId": "left_audit_crystals", "summary": "Synthetic durable report", "metrics": {}}
        with (
            mock.patch.object(self.bridge, "ensure_runtime_dir"),
            mock.patch.object(self.bridge, "RESEARCH_SHEET_AUTO_SYNC_ENABLED", True),
            mock.patch.object(self.bridge, "_research_sheet_report_items", side_effect=AssertionError("Report commit waited for projection")) as projection,
        ):
            result = self.bridge.create_report(payload)
        stored = json.loads((self.reports / f"{result['id']}.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(stored["summary"], payload["summary"])
        self.assertEqual(len(list(self.intents.glob("*.json"))), 1)
        self.queue.assert_not_called()
        self.flush.assert_not_called()
        projection.assert_not_called()

    def test_stale_projection_cannot_prune_or_append_to_new_configuration_outbox(self) -> None:
        report = self.report(0)
        saved_bytes = []
        outbox = self.root / "outbox.json"

        def reconfigure_during_projection(*args, **kwargs):
            self.internal.update(configRevision=4, activeConfigRevision=4)
            store = self.bridge._research_sheet_outbox_default()
            store["items"] = [{"id": "new-revision-item", "status": "pending", "configRevision": 4,
                               "payloadDigest": "new-current-payload", "attemptCount": 2}]
            self.bridge._save_research_sheet_outbox_unlocked(store)
            saved_bytes.append(outbox.read_bytes())
            return [{"id": "stale-projection", "reportId": report["id"], "configRevision": 3,
                     "consumerId": "deepResearch", "payloadDigest": "old-payload", "status": "pending"}]

        with mock.patch.object(self.bridge, "_research_sheet_report_items", side_effect=reconfigure_during_projection):
            result = self.real_queue(report, flush=False)
        self.assertEqual(result["reason"], "sheet_configuration_changed")
        self.assertEqual(outbox.read_bytes(), saved_bytes[0])

    def test_report_edited_during_projection_cannot_queue_stale_payload(self) -> None:
        report = self.report(0)
        self.bridge._save_research_sheet_outbox_unlocked(self.bridge._research_sheet_outbox_default())
        outbox = self.root / "outbox.json"
        previous = outbox.read_bytes()

        def edit_during_projection(*args, **kwargs):
            self.report(0, version=2)
            return [{"id": "stale-projection", "reportId": report["id"], "configRevision": 3,
                     "consumerId": "deepResearch", "payloadDigest": "old-payload", "status": "pending"}]

        with mock.patch.object(self.bridge, "_research_sheet_report_items", side_effect=edit_during_projection):
            result = self.real_queue(report, flush=False)
        self.assertEqual(result["reason"], "report_changed")
        self.assertEqual(outbox.read_bytes(), previous)
        self.bridge._enqueue_research_sheet_report_intent(report)
        self.queue.return_value = {"queued": 0, "reason": "report_changed"}
        self.bridge._drain_research_sheet_report_intents(max_reports=1)
        self.assertEqual(len(list(self.intents.glob("*.json"))), 1)

    def _seed_pruned_retry_failure(self) -> dict:
        report = self.report(0)
        report["type"] = "indicator_scout_report"
        (self.reports / f"{report['id']}.json").write_text(json.dumps(report), encoding="utf-8")
        item = {
            "id": "sheet-sync-isolated-retry", "reportId": report["id"],
            "configRevision": 3, "consumerId": "indicatorScout",
            "payloadDigest": "fixture-old-payload", "status": "pending",
            "recordKey": "fixture-retry-key", "row": ["fixture-value"],
            "requeueCount": 0,
        }
        store = self.bridge._research_sheet_outbox_default()
        store["failedLedger"] = [{
            key: item[key] for key in ("id", "reportId", "configRevision", "consumerId", "payloadDigest", "requeueCount")
        }]
        store["failedLedger"][0].update(lastErrorCode="permission_denied", failedAt="2026-10-01T00:00:00Z")
        self.bridge._save_research_sheet_outbox_unlocked(store)
        return item

    def test_manual_retry_projection_releases_all_core_shared_store_locks(self) -> None:
        item = self._seed_pruned_retry_failure()
        acquired = {}

        def project(*args, **kwargs):
            def probe_locks():
                for name in ("RESEARCH_SHEET_OUTBOX_LOCK", "DASHBOARD_WORKFLOW_SETTINGS_LOCK", "REPORTS_LOCK"):
                    lock = getattr(self.bridge, name)
                    acquired[name] = lock.acquire(timeout=0.2)
                    if acquired[name]:
                        lock.release()
            probe = threading.Thread(target=probe_locks, daemon=True)
            probe.start()
            probe.join(2)
            self.assertFalse(probe.is_alive(), "A Sheet projection blocked the core lock probe")
            self.assertEqual(acquired, {
                "RESEARCH_SHEET_OUTBOX_LOCK": True,
                "DASHBOARD_WORKFLOW_SETTINGS_LOCK": True,
                "REPORTS_LOCK": True,
            })
            return [copy.deepcopy(item)]

        with mock.patch.object(self.bridge, "_research_sheet_report_items", side_effect=project) as projection:
            result = self.bridge._research_sheet_requeue_failed_current_revision(reason="explicit_retry", max_items=1)
        projection.assert_called_once()
        self.assertEqual(result["requeued"], 1)
        after = self.bridge._load_research_sheet_outbox_unlocked()
        self.assertEqual(after["items"][0]["status"], "pending")
        self.assertEqual(after["items"][0]["requeueCount"], 1)
        self.assertEqual(after["failedLedger"], [])
        self.flush.assert_not_called()

    def test_manual_retry_stale_projection_preserves_concurrent_failed_payload(self) -> None:
        item = self._seed_pruned_retry_failure()
        saved_bytes = []

        def project(*args, **kwargs):
            with self.bridge.RESEARCH_SHEET_OUTBOX_LOCK:
                store = self.bridge._load_research_sheet_outbox_unlocked()
                store["failedLedger"][0].update(payloadDigest="fixture-new-payload", requeueCount=2)
                self.bridge._save_research_sheet_outbox_unlocked(store)
                saved_bytes.append(self.bridge.RESEARCH_SHEET_OUTBOX_PATH.read_bytes())
            return [copy.deepcopy(item)]

        with mock.patch.object(self.bridge, "_research_sheet_report_items", side_effect=project) as projection:
            result = self.bridge._research_sheet_requeue_failed_current_revision(reason="explicit_retry", max_items=1)
        projection.assert_called_once()
        self.assertEqual(result["requeued"], 0)
        self.assertEqual(self.bridge.RESEARCH_SHEET_OUTBOX_PATH.read_bytes(), saved_bytes[0])
        self.flush.assert_not_called()

    def test_manual_retry_stale_projection_preserves_new_sheet_revision(self) -> None:
        item = self._seed_pruned_retry_failure()
        saved_bytes = []

        def project(*args, **kwargs):
            with self.bridge.DASHBOARD_WORKFLOW_SETTINGS_LOCK, self.bridge.RESEARCH_SHEET_OUTBOX_LOCK:
                self.internal.update(configRevision=4, activeConfigRevision=4)
                store = self.bridge._research_sheet_outbox_default()
                store["items"] = [{**item, "payloadDigest": "fixture-revision-four", "configRevision": 4}]
                self.bridge._save_research_sheet_outbox_unlocked(store)
                saved_bytes.append(self.bridge.RESEARCH_SHEET_OUTBOX_PATH.read_bytes())
            return [copy.deepcopy(item)]

        with mock.patch.object(self.bridge, "_research_sheet_report_items", side_effect=project) as projection:
            result = self.bridge._research_sheet_requeue_failed_current_revision(reason="explicit_retry", max_items=1)
        projection.assert_called_once()
        self.assertEqual(result["requeued"], 0)
        self.assertEqual(self.bridge.RESEARCH_SHEET_OUTBOX_PATH.read_bytes(), saved_bytes[0])
        self.flush.assert_not_called()


if __name__ == "__main__":
    unittest.main()
