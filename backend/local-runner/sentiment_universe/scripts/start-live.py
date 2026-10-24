"""Current-user supervisor for the read-only market service; no trading calls."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import build_opener, ProxyHandler

ROOT = Path(__file__).resolve().parents[1]


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value), encoding='utf-8')
    os.replace(temporary, path)


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=4197)
    parser.add_argument('--state-dir', type=Path, default=Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'Metafxclub' / 'SentimentUniverse')
    parser.add_argument('--static-dir', type=Path, default=ROOT / 'dist' / 'client')
    parser.add_argument('--public-mirror', type=Path)
    result = parser.parse_args(argv)
    if not 1024 <= result.port <= 65535:
        parser.error('Port must be between1024 and65535')
    result.state_dir = result.state_dir.resolve()
    result.static_dir = result.static_dir.resolve()
    if result.public_mirror:
        result.public_mirror = result.public_mirror.resolve()
    if result.state_dir.is_relative_to(result.static_dir):
        parser.error('Private state must stay outside public assets')
    return result


def healthy(port, root=ROOT):
    try:
        with build_opener(ProxyHandler({})).open(f'http://127.0.0.1:{port}/api/health', timeout=3) as response:
            data = json.load(response)
        project = data.get('project') or data.get('packageRoot')
        return data.get('service') == 'sentiment-universe' and data.get('ok') is True and project and Path(project).resolve() == root.resolve()
    except Exception:
        return False


def child_command(options, executable=None):
    command = [executable or sys.executable, '-m', 'live_backend.server', '--port', str(options.port),
               '--state-dir', str(options.state_dir), '--static-dir', str(options.static_dir)]
    if options.public_mirror:
        command += ['--public-mirror', str(options.public_mirror)]
    return command


def mutex_name(options):
    # Shared state/port ownership also prevents two source checkouts collecting.
    identity = f'{str(options.state_dir).casefold()}|{options.port}'
    return 'Local\\MetafxclubSentimentUniverse-' + hashlib.sha256(identity.encode()).hexdigest()[:24]


def main(argv=None):
    options = arguments(argv)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.CreateMutexW.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.ReleaseMutex.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    mutex = kernel.CreateMutexW(None, False, mutex_name(options))
    if not mutex:
        return 1
    acquired = kernel.WaitForSingleObject(mutex, 0)
    if acquired not in (0, 0x80):  # WAIT_ABANDONED also grants ownership.
        kernel.CloseHandle(mutex)
        return 0
    record_path = options.state_dir / 'supervisor.json'
    child = None
    record = {'schemaVersion': 1, 'pid': os.getpid(), 'project': str(ROOT),
              'launcher': str(Path(__file__).resolve()), 'python': sys.executable,
              'port': options.port, 'stateDir': str(options.state_dir),
              'staticDir': str(options.static_dir), 'childPid': None}
    try:
        options.state_dir.mkdir(parents=True, exist_ok=True)
        atomic_json(record_path, record)
        while True:
            if healthy(options.port):
                time.sleep(30)
                continue
            # A foreign/unhealthy listener is not permission to terminate it.
            with socket.socket() as probe:
                if probe.connect_ex(('127.0.0.1', options.port)) == 0:
                    time.sleep(30)
                    continue
            log = options.state_dir / 'service.log'
            if log.exists() and log.stat().st_size > 1024 * 1024:
                os.replace(log, options.state_dir / 'service.previous.log')
            with log.open('ab') as output:
                child = subprocess.Popen(child_command(options), cwd=ROOT, stdin=subprocess.DEVNULL,
                                         stdout=output, stderr=output, creationflags=subprocess.CREATE_NO_WINDOW)
                record['childPid'] = child.pid
                atomic_json(record_path, record)
                child.wait()
                record['childPid'] = None
                atomic_json(record_path, record)
                child = None
            time.sleep(15)
    finally:
        if child is not None and child.poll() is None:
            child.terminate()  # This Popen owns the process handle; no PID scan.
        kernel.ReleaseMutex(mutex)
        kernel.CloseHandle(mutex)


if __name__ == '__main__':
    raise SystemExit(main())
