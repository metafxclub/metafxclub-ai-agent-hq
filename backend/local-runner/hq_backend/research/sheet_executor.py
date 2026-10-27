"""One isolated Sheet executor; the Bridge remains the durable-store writer.

Only JSON travels through anonymous owned pipes. No job, token, result, or
traceback is logged or persisted here. This module never starts the Bridge,
mission workers, Council, or a MetaTrader terminal.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from urllib.error import HTTPError
from urllib.request import urlopen


PROTOCOL_VERSION = 1
MAX_FRAME_BYTES = 8 * 1024 * 1024
MAX_TIMEOUT_SECONDS = 120.0
OPERATIONS = frozenset({
    "projection.report_items", "google.read_values", "google.inspect_tabs",
    "google.probe_tabs", "google.upsert_row", "google.start_google_oauth",
    "google.complete_google_oauth", "google.disconnect_google_oauth",
    "google.configure_google_oauth_client_json",
    "google.remove_google_oauth_client_configuration",
    "google.migrate_google_oauth_to_central_release",
})
NETWORK_OPERATIONS = frozenset({
    "google.read_values", "google.inspect_tabs", "google.probe_tabs",
    "google.upsert_row", "google.complete_google_oauth",
})
PROVIDER_ERROR_CODES = frozenset({
    "auth_expired", "auth_invalid_response", "auth_required", "auth_unavailable",
    "duplicate_key_conflict", "google_api_error", "google_api_unavailable",
    "invalid_google_response", "invalid_oauth_client", "invalid_oauth_client_file",
    "invalid_oauth_redirect", "invalid_probe_limit", "invalid_refresh_token",
    "invalid_sheet_id", "key_mismatch", "oauth_authorization_denied",
    "oauth_central_release_unavailable", "oauth_client_changed",
    "oauth_client_configuration_unreadable", "oauth_client_file_too_large",
    "oauth_client_id_mismatch", "oauth_client_not_configured", "oauth_client_not_desktop",
    "oauth_code_invalid", "oauth_credential_changed", "oauth_environment_override_active",
    "oauth_exchange_rejected", "oauth_invalid_response", "oauth_pkce_generation_failed",
    "oauth_rate_limited", "oauth_refresh_token_missing", "oauth_scope_missing",
    "oauth_state_expired", "oauth_state_invalid", "oauth_unavailable", "permission_denied",
    "rate_limited", "response_too_large", "schema_mismatch", "schema_too_wide",
    "secure_store_busy", "secure_store_client_mismatch", "secure_store_delete_failed",
    "secure_store_invalid", "secure_store_read_failed", "secure_store_rollback_failed",
    "secure_store_unavailable", "secure_store_write_failed", "sheet_capacity_reached",
    "spreadsheet_not_found", "write_unknown", "write_verification_failed",
    "background_budget_exhausted",
})
EXECUTOR_ERROR_CODES = frozenset({
    "sheet_worker_busy", "sheet_worker_closed", "sheet_worker_unavailable",
    "sheet_worker_start_failed", "sheet_worker_exited", "sheet_worker_timeout",
    "sheet_worker_protocol_error", "sheet_worker_operation_rejected",
    "sheet_worker_request_invalid", "sheet_worker_request_too_large",
    "sheet_worker_response_too_large", "sheet_worker_error",
    "sheet_projection_integrity_failed", "sheet_projection_side_effect_blocked",
})


class SheetExecutorError(RuntimeError):
    def __init__(self, code: str, write_unknown: bool = False, status: int = 503):
        self.code = code if code in PROVIDER_ERROR_CODES | EXECUTOR_ERROR_CODES else "sheet_worker_error"
        self.write_unknown = bool(write_unknown)
        self.status = status if type(status) is int and 400 <= status <= 599 else 503
        self.message = "The isolated Sheet operation could not be completed."
        super().__init__(self.message)


def _json_bytes(value: object) -> bytes:
    try:
        data = json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, RecursionError) as error:
        raise SheetExecutorError("sheet_worker_request_invalid", status=422) from error
    if len(data) + 1 > MAX_FRAME_BYTES:
        raise SheetExecutorError("sheet_worker_request_too_large", status=413)
    return data + b"\n"


def _reject_json_constant(_value):
    raise ValueError("Non-finite JSON is not supported.")


def _decode_frame(data: bytes) -> dict:
    if not data or len(data) > MAX_FRAME_BYTES or not data.endswith(b"\n"):
        raise SheetExecutorError("sheet_worker_protocol_error")
    try:
        value = json.loads(data.decode("utf-8"), parse_constant=_reject_json_constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise SheetExecutorError("sheet_worker_protocol_error") from error
    if not isinstance(value, dict):
        raise SheetExecutorError("sheet_worker_protocol_error")
    return value


class SheetExecutor:
    """Serialize bounded calls to one owned child, without waiting in status()."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve(strict=True)
        runner = self.project_root / "backend" / "local-runner"
        self._worker_path = (runner / "hq_backend" / "research" / "sheet_executor.py").resolve(strict=True)
        self._worker_path.relative_to(self.project_root)
        (runner / "bridge_server.py").resolve(strict=True).relative_to(self.project_root)
        self._call_lock = threading.Lock()
        self._stop_lock = threading.Lock()
        self._process = None
        self._responses = None
        self._protocol_bad = None
        self._unusable = False
        self._closing = False
        self._state = {"running": False, "busy": False, "closed": False,
                       "completedCalls": 0, "lastErrorCode": None}

    def _worker_command(self) -> list[str]:
        """Fixed production command; subclasses can supply a fixture in tests."""
        return [sys.executable, "-I", "-B", "-u", str(self._worker_path),
                "--worker", "--project-root", str(self.project_root)]

    def _update_state(self, **values):
        # Replace rather than mutate so status reads a coherent memory-only
        # snapshot without acquiring an operation/process lock.
        self._state = {**self._state, **values}

    def status(self) -> dict:
        return dict(self._state)

    @staticmethod
    def _reader(process, responses: queue.Queue, bad: threading.Event):
        try:
            while True:
                line = process.stdout.readline(MAX_FRAME_BYTES + 1)
                if not line:
                    item = ("error", "sheet_worker_exited")
                elif len(line) > MAX_FRAME_BYTES or not line.endswith(b"\n"):
                    bad.set()
                    item = ("error", "sheet_worker_protocol_error")
                else:
                    item = ("frame", line)
                try:
                    responses.put_nowait(item)
                except queue.Full:
                    # A final valid reply followed by EOF is not a second
                    # protocol message. Let the waiting caller consume it.
                    if item[0] == "frame":
                        bad.set()
                    return
                if item[0] == "error":
                    return
        except (OSError, ValueError, AttributeError):
            try:
                responses.put_nowait(("error", "sheet_worker_exited"))
            except queue.Full:
                bad.set()

    def _stop_owned(self, process) -> bool:
        """Only this exact Popen instance can be terminated/reaped."""
        if process is None:
            return True
        if not self._stop_lock.acquire(timeout=0.1):
            return False
        try:
            if process.poll() is None:
                try:
                    process.terminate()
                except OSError:
                    pass
                try:
                    process.wait(timeout=0.25)
                except subprocess.TimeoutExpired:
                    try:
                        process.kill()
                    except OSError:
                        pass
                    try:
                        process.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        return False
            if process.poll() is None:
                return False
            process.wait(timeout=0)
            # Popen uses bufsize=0, so these are raw FileIO pipes, without a
            # BufferedReader lock that could block close behind readline.
            # Close only after confirmed exit; EOF releases the daemon readers
            # and repeated restart does not leak pipe handles until GC.
            for name in ("stdin", "stdout", "stderr"):
                stream = getattr(process, name, None)
                if stream is not None:
                    try:
                        stream.close()
                    except (OSError, ValueError):
                        pass
            return True
        except (OSError, ValueError, subprocess.TimeoutExpired):
            return process.poll() is not None
        finally:
            self._stop_lock.release()

    def _discard(self, code: str):
        self._unusable = True
        old = self._process
        confirmed = self._stop_owned(old)
        if confirmed and self._process is old:
            self._process = None
            self._responses = None
            self._protocol_bad = None
        self._update_state(running=not confirmed, busy=False, lastErrorCode=code)

    def _ensure_process(self):
        if self._closing:
            raise SheetExecutorError("sheet_worker_closed")
        if self._process is not None:
            if self._process.poll() is not None:
                self._discard("sheet_worker_exited")
            elif self._unusable or (self._protocol_bad is not None and self._protocol_bad.is_set()):
                self._discard("sheet_worker_unavailable")
                if self._process is not None:
                    raise SheetExecutorError("sheet_worker_unavailable")
            else:
                return
        # Never replace a child whose exit was not confirmed.
        if self._process is not None or self._closing:
            raise SheetExecutorError("sheet_worker_unavailable")
        options = {"stdin": subprocess.PIPE, "stdout": subprocess.PIPE,
                   "stderr": subprocess.DEVNULL, "cwd": str(self.project_root),
                   "bufsize": 0, "close_fds": True}
        if os.name == "nt":
            options["creationflags"] = subprocess.CREATE_NO_WINDOW
        try:
            process = subprocess.Popen(self._worker_command(), **options)
        except (OSError, ValueError) as error:
            raise SheetExecutorError("sheet_worker_start_failed") from error
        self._process = process
        self._unusable = False
        self._responses = queue.Queue(maxsize=1)
        self._protocol_bad = threading.Event()
        threading.Thread(target=self._reader,
                         args=(process, self._responses, self._protocol_bad),
                         name="metafx-sheet-ipc-reader", daemon=True).start()
        self._update_state(running=True, lastErrorCode=None)
        if self._closing:
            self._discard("sheet_worker_closed")
            raise SheetExecutorError("sheet_worker_closed")

    def call(self, operation: str, args: list, kwargs: dict,
             timeout_seconds: float = 45) -> object:
        if not isinstance(operation, str) or operation not in OPERATIONS:
            raise SheetExecutorError("sheet_worker_operation_rejected", status=422)
        if not isinstance(args, list) or not isinstance(kwargs, dict):
            raise SheetExecutorError("sheet_worker_request_invalid", status=422)
        try:
            timeout = float(timeout_seconds)
        except (ValueError, TypeError) as error:
            raise SheetExecutorError("sheet_worker_request_invalid", status=422) from error
        if not math.isfinite(timeout) or timeout <= 0:
            raise SheetExecutorError("sheet_worker_timeout")
        deadline = time.monotonic() + min(timeout, MAX_TIMEOUT_SECONDS)
        request_id = uuid.uuid4().hex
        request = {"version": PROTOCOL_VERSION, "id": request_id, "operation": operation,
                   "args": args, "kwargs": kwargs, "timeoutSeconds": min(timeout, MAX_TIMEOUT_SECONDS)}
        _json_bytes(request)  # Reject invalid/unbounded input before locking/spawning.
        if not self._call_lock.acquire(timeout=max(0, deadline - time.monotonic())):
            raise SheetExecutorError("sheet_worker_busy")
        dispatched = False
        try:
            self._ensure_process()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise SheetExecutorError("sheet_worker_timeout")
            request["timeoutSeconds"] = remaining
            frame = _json_bytes(request)
            process = self._process
            responses = self._responses
            bad = self._protocol_bad
            written = threading.Event()

            def write_request():
                try:
                    view = memoryview(frame)
                    while view:
                        count = process.stdin.write(view)
                        if not count:
                            raise OSError("Closed worker pipe.")
                        view = view[count:]
                    process.stdin.flush()
                except (OSError, ValueError, AttributeError):
                    try:
                        responses.put_nowait(("error", "sheet_worker_exited"))
                    except queue.Full:
                        bad.set()
                finally:
                    written.set()

            self._update_state(busy=True)
            dispatched = True
            threading.Thread(target=write_request, name="metafx-sheet-ipc-writer", daemon=True).start()
            try:
                kind, value = responses.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty as error:
                raise SheetExecutorError("sheet_worker_timeout") from error
            if kind != "frame" or bad.is_set():
                raise SheetExecutorError(value if kind == "error" else "sheet_worker_protocol_error")
            response = _decode_frame(value)
            if (response.get("version") != PROTOCOL_VERSION or response.get("id") != request_id
                    or type(response.get("ok")) is not bool):
                raise SheetExecutorError("sheet_worker_protocol_error")
            if not written.wait(timeout=max(0, deadline - time.monotonic())):
                raise SheetExecutorError("sheet_worker_timeout")
            if not response["ok"]:
                error = response.get("error")
                if not isinstance(error, dict) or error.get("code") not in PROVIDER_ERROR_CODES | EXECUTOR_ERROR_CODES:
                    raise SheetExecutorError("sheet_worker_protocol_error")
                raise SheetExecutorError(error["code"], error.get("writeUnknown") is True,
                                         error.get("status", 503))
            self._update_state(busy=False, running=process.poll() is None,
                               completedCalls=self._state["completedCalls"] + 1, lastErrorCode=None)
            return response.get("result")
        except SheetExecutorError as error:
            fatal = error.code in {"sheet_worker_timeout", "sheet_worker_exited",
                                   "sheet_worker_protocol_error", "sheet_worker_unavailable"}
            if fatal:
                if dispatched and operation == "google.upsert_row":
                    error.write_unknown = True
                self._discard(error.code)
            else:
                self._update_state(busy=False, lastErrorCode=error.code)
            raise
        except Exception:
            self._discard("sheet_worker_error")
            raise SheetExecutorError("sheet_worker_error", dispatched and operation == "google.upsert_row") from None
        finally:
            self._call_lock.release()

    def close(self) -> None:
        self._closing = True
        self._discard("sheet_worker_closed")
        self._update_state(closed=True, busy=False)


class _WorkerGuard:
    """Permanent child-only audit guard; never install this in the Bridge."""

    def __init__(self, credential_root: Path):
        self.credential_root = credential_root.resolve(strict=False)
        self.mode = "idle"

    def _credential_path(self, value) -> bool:
        if not isinstance(value, (str, bytes, os.PathLike)):
            return False
        try:
            Path(os.fsdecode(value)).resolve(strict=False).relative_to(self.credential_root)
            return self.mode == "google"
        except (OSError, ValueError, TypeError):
            return False

    def _credential_parent_mkdir(self, value) -> bool:
        if self.mode != "google" or not isinstance(value, (str, bytes, os.PathLike)):
            return False
        try:
            path = Path(os.fsdecode(value)).resolve(strict=False)
            return path == self.credential_root or path in self.credential_root.parents
        except (OSError, ValueError, TypeError):
            return False

    def __call__(self, event: str, args: tuple):
        if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "os.fork", "os.exec", "os.spawn"}:
            raise PermissionError("Sheet executor cannot start processes.")
        if self.mode != "google" and event.startswith("socket."):
            raise PermissionError("Sheet projection cannot use the network.")
        if event == "open":
            path, mode, flags = (list(args) + [None, None, 0])[:3]
            writing = (isinstance(mode, str) and any(mark in mode for mark in "wax+")) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            )
            if writing and not self._credential_path(path):
                raise PermissionError("Sheet executor cannot write shared runtime files.")
        elif event in {"os.rename", "os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.chown", "os.truncate", "os.utime", "os.link", "os.symlink"}:
            # On a fresh Windows profile Path.mkdir(parents=True) creates the
            # exact missing ancestors of the credential directory. This does
            # not authorize opening/removing/renaming files in those parents.
            if event == "os.mkdir" and args and self._credential_parent_mkdir(args[0]):
                return
            paths = args[:2] if event in {"os.rename", "os.link", "os.symlink"} else args[:1]
            if not paths or not all(self._credential_path(value) for value in paths):
                raise PermissionError("Sheet executor cannot mutate shared runtime files.")


class _WorkerDispatcher:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve(strict=True)
        runner = self.project_root / "backend" / "local-runner"
        if str(runner) not in sys.path:
            sys.path.insert(0, str(runner))
        from hq_backend.google import google_sheet_hub, google_oauth_store
        self.google = google_sheet_hub
        self.guard = _WorkerGuard(google_oauth_store.credential_path().parent)
        self.projection = None

    def _projection_module(self):
        if self.projection is None:
            path = self.project_root / "backend" / "local-runner" / "bridge_server.py"
            name = "_metafx_sheet_readonly_projection"
            spec = importlib.util.spec_from_file_location(name, path)
            if spec is None or spec.loader is None:
                raise SheetExecutorError("sheet_worker_unavailable")
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            # Loading/shaping settings is otherwise a lazy migration writer.
            module.load_dashboard_workflow_settings = module._load_dashboard_workflow_settings_read_only
            module.RESEARCH_SHEET_AUTO_SYNC_ENABLED = True  # include read-only catalog cache
            def forbidden(*_args, **_kwargs):
                raise PermissionError("Projection mutation is forbidden.")
            for attr in ("write_json", "append_audit", "append_audit_once", "_mutate_dashboard_workflow_settings"):
                setattr(module, attr, forbidden)
            module.ensure_runtime_dir = lambda: None
            self.projection = module
        return self.projection

    def _opener(self, deadline: float):
        write_attempted = False
        def bounded(request, *, timeout=20):
            nonlocal write_attempted
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise self.google.GoogleSheetHubError("background_budget_exhausted", "Sheet operation yielded.", 503, write_attempted)
            address = str(getattr(request, "full_url", request))
            method = request.get_method() if hasattr(request, "get_method") else "GET"
            if address.startswith(self.google.GOOGLE_API_ROOT + "/") and method not in {"GET", "HEAD"}:
                write_attempted = True
            try:
                return urlopen(request, timeout=min(float(timeout), remaining))
            except HTTPError:
                raise
            except (TimeoutError, OSError) as error:
                if time.monotonic() >= deadline:
                    raise self.google.GoogleSheetHubError("background_budget_exhausted", "Sheet operation yielded.", 503, write_attempted) from error
                raise
        return bounded

    def dispatch(self, operation: str, args: list, kwargs: dict, timeout_seconds: float):
        if not isinstance(operation, str) or operation not in OPERATIONS:
            raise SheetExecutorError("sheet_worker_operation_rejected", status=422)
        if not isinstance(args, list) or not isinstance(kwargs, dict) or any(key in kwargs for key in ("open_url", "environ")):
            raise SheetExecutorError("sheet_worker_request_invalid", status=422)
        deadline = time.monotonic() + min(float(timeout_seconds), MAX_TIMEOUT_SECONDS)
        options = dict(kwargs)
        self.guard.mode = "projection" if operation == "projection.report_items" else "google"
        try:
            if operation == "projection.report_items":
                return self._projection_module()._research_sheet_report_items(*args, **options)
            binding = options.get("expected_credential_binding")
            if binding is not None:
                if (operation != "google.read_values" or not isinstance(binding, dict)
                        or set(binding) != {"fingerprint"}
                        or not re.fullmatch(r"[0-9a-f]{64}", str(binding.get("fingerprint") or ""))):
                    raise SheetExecutorError("sheet_worker_request_invalid", status=422)
                options["expected_credential_binding"] = self.google._CredentialBindingSnapshot(binding["fingerprint"])
            if operation in NETWORK_OPERATIONS:
                options["open_url"] = self._opener(deadline)
            return getattr(self.google, operation.removeprefix("google."))(*args, **options)
        except self.google.GoogleSheetHubError as error:
            code = error.code if error.code in PROVIDER_ERROR_CODES else "sheet_worker_error"
            if time.monotonic() >= deadline and code in {"auth_unavailable", "google_api_unavailable"}:
                code = "background_budget_exhausted"
            raise SheetExecutorError(code, error.write_unknown, error.status) from None
        except PermissionError:
            raise SheetExecutorError("sheet_projection_side_effect_blocked", operation == "google.upsert_row") from None
        except SheetExecutorError:
            raise
        except Exception as error:
            code = "sheet_projection_integrity_failed" if type(error).__name__ == "DataIntegrityError" else "sheet_worker_error"
            raise SheetExecutorError(code, operation == "google.upsert_row") from None
        finally:
            self.guard.mode = "idle"


def _acquire_worker_lease(project_root: Path):
    """One provider owner per checkout, even across Bridge crashes/restarts."""
    identity = str(Path(project_root).resolve(strict=True)).casefold()
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        create = kernel32.CreateMutexW
        create.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
        create.restype = wintypes.HANDLE
        close = kernel32.CloseHandle
        close.argtypes = (wintypes.HANDLE,)
        close.restype = wintypes.BOOL
        handle = create(None, False, f"Local\\MetafxAgentHQSheet-{digest}")
        if not handle:
            raise OSError("Sheet worker lease unavailable.")
        if ctypes.get_last_error() == 183:
            close(handle)
            return None
        return {"kind": "windows_mutex", "handle": handle, "close": close}
    import fcntl
    path = Path(tempfile.gettempdir()) / f"metafx-sheet-{os.getuid()}-{digest}.lock"
    handle = path.open("a+b")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        return None
    return {"kind": "posix_flock", "handle": handle}


def _release_worker_lease(lease) -> None:
    if not isinstance(lease, dict):
        return
    handle = lease.pop("handle", None)
    if handle is None:
        return
    if lease.get("kind") == "windows_mutex":
        lease["close"](handle)
    else:
        import fcntl
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


class _ParentDeathMonitor:
    """Observe our real parent; terminate only this child if that parent dies."""
    def __init__(self):
        self.parent_pid = os.getppid()
        self.stop_event = threading.Event()
        self.thread = None
        self.handle = None
        self.close_handle = None

    def start(self) -> bool:
        if self.parent_pid <= 1:
            return False
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            open_process = kernel32.OpenProcess
            open_process.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
            open_process.restype = wintypes.HANDLE
            wait = kernel32.WaitForSingleObject
            wait.argtypes = (wintypes.HANDLE, wintypes.DWORD)
            wait.restype = wintypes.DWORD
            close = kernel32.CloseHandle
            close.argtypes = (wintypes.HANDLE,)
            close.restype = wintypes.BOOL
            get_times = kernel32.GetProcessTimes
            pointer = ctypes.POINTER(wintypes.FILETIME)
            get_times.argtypes = (wintypes.HANDLE, pointer, pointer, pointer, pointer)
            get_times.restype = wintypes.BOOL
            current_process = kernel32.GetCurrentProcess
            current_process.restype = wintypes.HANDLE
            # Synchronize observes the captured process object, not a numeric
            # PID that could later identify an unrelated replacement process.
            handle = open_process(0x00100000 | 0x1000, False, self.parent_pid)
            if not handle:
                return False
            self.handle, self.close_handle = handle, close
            def created_at(process_handle):
                times = [wintypes.FILETIME() for _ in range(4)]
                if not get_times(process_handle, *(ctypes.byref(item) for item in times)):
                    return None
                return (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
            parent_created = created_at(handle)
            child_created = created_at(current_process())
            if (parent_created is None or child_created is None
                    or parent_created > child_created or wait(handle, 0) != 258):
                close(handle)
                self.handle = None
                return False
            def watch():
                while not self.stop_event.is_set():
                    result = wait(handle, 250)
                    if result != 258:  # signaled parent or invalid monitor
                        os._exit(0)  # never targets another PID
        else:
            def watch():
                while not self.stop_event.wait(0.25):
                    if os.getppid() != self.parent_pid:
                        os._exit(0)
        self.thread = threading.Thread(target=watch, name="metafx-sheet-parent-watch", daemon=True)
        self.thread.start()
        return True

    def close(self):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=0.5)
        if self.handle is not None and (self.thread is None or not self.thread.is_alive()):
            self.close_handle(self.handle)
            self.handle = None


def _worker_main(project_root: Path) -> int:
    sys.dont_write_bytecode = True
    root = project_root.resolve(strict=True)
    expected = (root / "backend" / "local-runner" / "hq_backend" / "research" / "sheet_executor.py").resolve(strict=True)
    if expected != Path(__file__).resolve(strict=True):
        return 2
    monitor = _ParentDeathMonitor()
    if not monitor.start():
        return 3
    lease = None
    try:
        lease = _acquire_worker_lease(root)
        if lease is None:
            return 3
        return _worker_serve(root)
    finally:
        _release_worker_lease(lease)
        monitor.close()


def _worker_serve(root: Path) -> int:
    dispatcher = _WorkerDispatcher(root)
    sys.addaudithook(dispatcher.guard)
    input_pipe, output_pipe = sys.stdin.buffer, sys.stdout.buffer
    # Imported legacy helpers cannot corrupt the IPC or leak diagnostics.
    class _SilentText:
        encoding = "utf-8"
        def write(self, _value): return 0
        def flush(self): return None
        def isatty(self): return False
    sys.stdout = _SilentText()
    sys.stderr = _SilentText()
    while True:
        frame = input_pipe.readline(MAX_FRAME_BYTES + 1)
        if not frame:
            return 0
        request_id = None
        operation = None
        try:
            request = _decode_frame(frame)
            request_id = request.get("id")
            operation = request.get("operation")
            budget = request.get("timeoutSeconds")
            if (request.get("version") != PROTOCOL_VERSION
                    or not re.fullmatch(r"[0-9a-f]{32}", str(request_id or ""))
                    or not isinstance(budget, (float, int)) or isinstance(budget, bool)
                    or not math.isfinite(budget) or not 0 < budget <= MAX_TIMEOUT_SECONDS):
                return 2
            result = dispatcher.dispatch(operation, request.get("args"), request.get("kwargs"), budget)
            response = {"version": PROTOCOL_VERSION, "id": request_id, "ok": True, "result": result}
            try:
                encoded = _json_bytes(response)
            except SheetExecutorError:
                raise SheetExecutorError("sheet_worker_response_too_large", operation == "google.upsert_row") from None
        except SheetExecutorError as error:
            if request_id is None:
                return 2
            encoded = _json_bytes({"version": PROTOCOL_VERSION, "id": request_id, "ok": False,
                                   "error": {"code": error.code, "status": error.status,
                                             "writeUnknown": error.write_unknown}})
        output_pipe.write(encoded)
        output_pipe.flush()


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--worker", action="store_true", required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    options = parser.parse_args()
    try:
        return _worker_main(options.project_root)
    except Exception:
        return 2  # stderr is intentionally empty; parent reports a safe code.


if __name__ == "__main__":
    raise SystemExit(main())
