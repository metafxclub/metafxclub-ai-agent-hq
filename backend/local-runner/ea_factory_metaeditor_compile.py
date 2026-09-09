from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
import subprocess
import time
from pathlib import Path
from typing import Callable


MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_LOG_BYTES = 2 * 1024 * 1024
MAX_COMPILER_BYTES = 512 * 1024 * 1024
MAX_COMPILED_BYTES = 64 * 1024 * 1024
MAX_STANDARD_INCLUDE_FILES = 4096
MAX_STANDARD_INCLUDE_BYTES = 64 * 1024 * 1024
MAX_STANDARD_INCLUDE_FILE_BYTES = 8 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 90


class MetaEditorCompileError(RuntimeError):
    """One fail-closed compile adapter outcome with no sensitive path text."""

    def __init__(
        self,
        code: str,
        *,
        process_started: bool = False,
        exit_code: int | str | None = None,
        errors: int | None = None,
        warnings: int | None = None,
        duration_ms: int | None = None,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.process_started = bool(process_started)
        self.exit_code = exit_code
        self.errors = errors
        self.warnings = warnings
        self.duration_ms = duration_ms

    def public_details(self) -> dict:
        return {
            "reasonCode": self.code,
            "processStarted": self.process_started,
            "processExitCode": self.exit_code,
            "errorCount": self.errors,
            "warningCount": self.warnings,
            "durationMs": self.duration_ms,
        }


def _canonical_json_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _path_has_reparse_component(path: Path) -> bool:
    """Reject symlinks and Windows reparse points in the full lexical chain."""

    try:
        absolute = path.absolute()
    except (OSError, RuntimeError, ValueError):
        return True
    candidates = [absolute, *absolute.parents]
    for candidate in candidates:
        if candidate.parent == candidate:
            continue
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            continue
        except (OSError, RuntimeError, ValueError):
            return True
        if stat.S_ISLNK(metadata.st_mode):
            return True
        if int(getattr(metadata, "st_file_attributes", 0) or 0) & 0x400:
            return True
    return False


def _stable_file_digest(
    path: Path,
    *,
    maximum_bytes: int,
    minimum_bytes: int = 1,
) -> tuple[str, int, tuple[int | None, int | None, int, int, int]]:
    try:
        if _path_has_reparse_component(path) or not path.is_file():
            raise MetaEditorCompileError("compile_path_unsafe")
        before = path.stat(follow_symlinks=False)
        if before.st_size < minimum_bytes or before.st_size > maximum_bytes:
            raise MetaEditorCompileError("compile_file_size_invalid")
        digest = hashlib.sha256()
        observed = 0
        with path.open("rb") as handle:
            while True:
                block = handle.read(64 * 1024)
                if not block:
                    break
                observed += len(block)
                if observed > maximum_bytes:
                    raise MetaEditorCompileError("compile_file_size_invalid")
                digest.update(block)
        after = path.stat(follow_symlinks=False)
    except MetaEditorCompileError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise MetaEditorCompileError("compile_file_unavailable") from error
    if (
        observed != before.st_size
        or after.st_size != before.st_size
        or after.st_mtime_ns != before.st_mtime_ns
        or getattr(after, "st_ino", None) != getattr(before, "st_ino", None)
    ):
        raise MetaEditorCompileError("compile_file_changed_during_read")
    identity = (
        getattr(after, "st_dev", None),
        getattr(after, "st_ino", None),
        int(after.st_size),
        int(after.st_mtime_ns),
        int(after.st_ctime_ns),
    )
    return digest.hexdigest(), observed, identity


def _read_stable_bytes(path: Path, *, maximum_bytes: int) -> bytes:
    try:
        if _path_has_reparse_component(path) or not path.is_file():
            raise MetaEditorCompileError("compile_log_unsafe")
        before = path.stat(follow_symlinks=False)
        if before.st_size <= 0 or before.st_size > maximum_bytes:
            raise MetaEditorCompileError("compile_log_size_invalid")
        payload = path.read_bytes()
        after = path.stat(follow_symlinks=False)
    except MetaEditorCompileError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise MetaEditorCompileError("compile_log_unavailable") from error
    if (
        len(payload) != before.st_size
        or after.st_size != before.st_size
        or after.st_mtime_ns != before.st_mtime_ns
        or getattr(after, "st_ino", None) != getattr(before, "st_ino", None)
    ):
        raise MetaEditorCompileError("compile_log_changed_during_read")
    return payload


def _decode_metaeditor_log(payload: bytes) -> str:
    attempts: list[str] = []
    if payload.startswith((b"\xff\xfe", b"\xfe\xff")):
        attempts.append("utf-16")
    attempts.extend(["utf-8-sig", "utf-16-le"])
    for encoding in attempts:
        try:
            decoded = payload.decode(encoding, errors="strict")
        except UnicodeError:
            continue
        text = decoded.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
        if "\x00" not in text:
            return text
    raise MetaEditorCompileError("compile_log_encoding_invalid", process_started=True)


def _strip_c_style_comments(text: str) -> str:
    """Replace comments with spaces while preserving strings and line boundaries."""

    output: list[str] = []
    index = 0
    state = "code"
    quote = ""
    while index < len(text):
        character = text[index]
        following = text[index + 1] if index + 1 < len(text) else ""
        if state == "line_comment":
            if character == "\n":
                output.append(character)
                state = "code"
            else:
                output.append(" ")
            index += 1
            continue
        if state == "block_comment":
            if character == "*" and following == "/":
                output.extend((" ", " "))
                index += 2
                state = "code"
            else:
                output.append("\n" if character == "\n" else " ")
                index += 1
            continue
        if state == "string":
            output.append(character)
            if character == "\\" and following:
                output.append(following)
                index += 2
            else:
                if character == quote:
                    state = "code"
                index += 1
            continue
        if character == "/" and following == "/":
            output.extend((" ", " "))
            index += 2
            state = "line_comment"
        elif character == "/" and following == "*":
            output.extend((" ", " "))
            index += 2
            state = "block_comment"
        elif character in {'"', "'"}:
            output.append(character)
            quote = character
            index += 1
            state = "string"
        else:
            output.append(character)
            index += 1
    return "".join(output)


def _source_dependency_policy(payload: bytes, platform: str) -> tuple[bool, bool]:
    normalized_platform = str(platform or "").strip().lower()
    if normalized_platform not in {"mt4", "mt5"}:
        return False, False
    try:
        text = payload.decode("utf-8-sig", errors="strict")
    except UnicodeError:
        return False, False
    uses_standard_trade = False
    for line in _strip_c_style_comments(text).splitlines():
        directive = re.match(r"^\s*#\s*(include|import|resource|property)\b(.*)$", line, re.IGNORECASE)
        if not directive:
            continue
        name = directive.group(1).lower()
        tail = directive.group(2).strip()
        if name in {"import", "resource"}:
            return False, False
        if name == "property" and re.match(r"(?i)^icon\b", tail):
            return False, False
        if name != "include":
            continue
        match = re.fullmatch(r"<([A-Za-z0-9_./\\ -]{1,180})>", tail)
        if not match:
            return False, False
        reference = match.group(1).replace("\\", "/")
        if (
            reference.startswith("/")
            or ".." in reference.split("/")
            or ":" in reference
            or "//" in reference
        ):
            return False, False
        if normalized_platform != "mt5" or reference.casefold() != "trade/trade.mqh":
            return False, False
        uses_standard_trade = True
    return True, uses_standard_trade


def _source_directives_are_safe(payload: bytes, platform: str) -> bool:
    """Allow no external compile inputs beyond MT5's exact standard Trade API."""

    return _source_dependency_policy(payload, platform)[0]


def inspect_source_dependencies(payload: bytes, platform: str) -> dict:
    safe, uses_standard_trade = _source_dependency_policy(payload, platform)
    if not safe:
        raise MetaEditorCompileError("source_compile_directive_unsafe")
    return {"usesMt5StandardTrade": uses_standard_trade}


def snapshot_standard_include_tree(root: Path) -> dict:
    """Hash a bounded, link-free MT5 standard include tree deterministically."""

    include_root = Path(root)
    try:
        if _path_has_reparse_component(include_root) or not include_root.is_dir():
            raise MetaEditorCompileError("standard_include_tree_unsafe")
        exact_root = include_root.resolve(strict=True)
        pending = [exact_root]
        manifest: list[dict] = []
        seen_names: set[str] = set()
        total_bytes = 0
        visited_entries = 0
        while pending:
            directory = pending.pop()
            if _path_has_reparse_component(directory) or not directory.is_dir():
                raise MetaEditorCompileError("standard_include_tree_unsafe")
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda item: item.name.casefold())
            for entry in entries:
                visited_entries += 1
                if visited_entries > MAX_STANDARD_INCLUDE_FILES * 2:
                    raise MetaEditorCompileError("standard_include_tree_unbounded")
                path = Path(entry.path)
                if _path_has_reparse_component(path):
                    raise MetaEditorCompileError("standard_include_tree_unsafe")
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    raise MetaEditorCompileError("standard_include_tree_unsafe")
                relative_name = path.relative_to(exact_root).as_posix().casefold()
                if relative_name in seen_names:
                    raise MetaEditorCompileError("standard_include_tree_unsafe")
                seen_names.add(relative_name)
                digest, byte_size, _identity = _stable_file_digest(
                    path,
                    maximum_bytes=MAX_STANDARD_INCLUDE_FILE_BYTES,
                )
                total_bytes += byte_size
                if (
                    len(manifest) >= MAX_STANDARD_INCLUDE_FILES
                    or total_bytes > MAX_STANDARD_INCLUDE_BYTES
                ):
                    raise MetaEditorCompileError("standard_include_tree_unbounded")
                manifest.append({
                    "relativePath": relative_name,
                    "byteSize": byte_size,
                    "sha256": digest,
                })
        manifest.sort(key=lambda item: item["relativePath"])
        required = next(
            (
                item
                for item in manifest
                if item["relativePath"] == "trade/trade.mqh"
            ),
            None,
        )
        if required is None:
            raise MetaEditorCompileError("standard_include_tree_unavailable")
        return {
            "treeDigest": _canonical_json_digest(manifest),
            "fileCount": len(manifest),
            "byteSize": total_bytes,
        }
    except MetaEditorCompileError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise MetaEditorCompileError("standard_include_tree_unavailable") from error


def _read_origin_install(data_path: Path, platform: str) -> Path | None:
    origin = data_path / "origin.txt"
    try:
        if _path_has_reparse_component(origin) or not origin.is_file() or origin.stat().st_size > 4096:
            return None
        raw = origin.read_bytes()
    except (OSError, RuntimeError, ValueError):
        return None
    for encoding in ("utf-16", "utf-8-sig", "utf-8"):
        try:
            value = raw.decode(encoding, errors="strict").strip("\x00\r\n ")
        except UnicodeError:
            continue
        if not value or "\x00" in value:
            continue
        candidate = Path(value)
        if candidate.is_absolute():
            return candidate
    return None


def resolve_compile_target(record: object, token: object, platform: str) -> dict:
    """Resolve only the Backend-selected install; never accept a request path."""

    normalized_platform = str(platform or "").strip().lower()
    if normalized_platform not in {"mt4", "mt5"}:
        raise MetaEditorCompileError("compile_platform_unsupported")
    if not isinstance(record, dict) or not isinstance(token, dict):
        raise MetaEditorCompileError("terminal_not_selected")
    candidate_id = str(record.get("candidateId") or "")
    selection_candidate = str(token.get("candidateId") or "")
    revision = token.get("selectionRevision")
    if (
        not re.fullmatch(r"mtc-[A-Za-z0-9._-]{1,115}", candidate_id)
        or not secrets.compare_digest(candidate_id, selection_candidate)
        or isinstance(revision, bool)
        or not isinstance(revision, int)
        or revision < 1
    ):
        raise MetaEditorCompileError("terminal_selection_invalid")
    if str(record.get("platform") or "").strip().lower() != normalized_platform:
        raise MetaEditorCompileError("terminal_platform_mismatch")
    if record.get("available") is not True:
        raise MetaEditorCompileError("terminal_selection_stale")

    raw_local = str(record.get("localPath") or "").strip()
    raw_install = str(record.get("installPath") or "").strip()
    raw_data = str(record.get("dataPath") or "").strip()
    identity = str(record.get("identityKey") or "")
    expected_identity = hashlib.sha256(
        f"{normalized_platform}\0{os.path.normcase(raw_local)}".encode(
            "utf-8", errors="replace"
        )
    ).hexdigest()
    if (
        not raw_local
        or not raw_install
        or not re.fullmatch(r"[0-9a-f]{64}", identity)
        or not secrets.compare_digest(identity, expected_identity)
    ):
        raise MetaEditorCompileError("terminal_identity_invalid")
    local_path = Path(raw_local)
    install_path = Path(raw_install)
    if (
        not local_path.is_absolute()
        or not install_path.is_absolute()
        or _path_has_reparse_component(local_path)
        or _path_has_reparse_component(install_path)
    ):
        raise MetaEditorCompileError("terminal_path_unsafe")
    try:
        if not local_path.is_dir() or not install_path.is_dir():
            raise MetaEditorCompileError("terminal_path_unavailable")
        canonical_local = os.path.normcase(str(local_path.resolve(strict=True)))
        canonical_install = os.path.normcase(str(install_path.resolve(strict=True)))
    except (OSError, RuntimeError, ValueError) as error:
        raise MetaEditorCompileError("terminal_path_unavailable") from error

    terminal_name = "terminal.exe" if normalized_platform == "mt4" else "terminal64.exe"
    editor_name = "metaeditor.exe" if normalized_platform == "mt4" else "metaeditor64.exe"
    mql_name = "MQL4" if normalized_platform == "mt4" else "MQL5"
    terminal = install_path / terminal_name
    compiler = install_path / editor_name
    if (
        _path_has_reparse_component(terminal)
        or _path_has_reparse_component(compiler)
        or not terminal.is_file()
        or not compiler.is_file()
        or compiler.name.lower() != editor_name
        or terminal.name.lower() != terminal_name
    ):
        raise MetaEditorCompileError("metaeditor_not_available")

    verified_data_path: Path | None = None
    if canonical_local != canonical_install:
        if not raw_data:
            raise MetaEditorCompileError("terminal_origin_unverified")
        data_path = Path(raw_data)
        try:
            canonical_data = os.path.normcase(str(data_path.resolve(strict=True)))
        except (OSError, RuntimeError, ValueError) as error:
            raise MetaEditorCompileError("terminal_origin_unverified") from error
        origin_install = _read_origin_install(data_path, normalized_platform)
        try:
            canonical_origin = (
                os.path.normcase(str(origin_install.resolve(strict=True)))
                if origin_install is not None
                else ""
            )
        except (OSError, RuntimeError, ValueError):
            canonical_origin = ""
        if (
            _path_has_reparse_component(data_path)
            or canonical_data != canonical_local
            or not (data_path / mql_name).is_dir()
            or canonical_origin != canonical_install
        ):
            raise MetaEditorCompileError("terminal_origin_unverified")
        verified_data_path = data_path.resolve(strict=True)
    elif raw_data:
        data_path = Path(raw_data)
        try:
            resolved_data_path = data_path.resolve(strict=True)
            if (
                _path_has_reparse_component(data_path)
                or os.path.normcase(str(resolved_data_path)) != canonical_local
                or not (resolved_data_path / mql_name).is_dir()
            ):
                raise MetaEditorCompileError("terminal_origin_unverified")
        except (OSError, RuntimeError, ValueError) as error:
            raise MetaEditorCompileError("terminal_origin_unverified") from error
        verified_data_path = resolved_data_path

    standard_include_root: Path | None = None
    if normalized_platform == "mt5" and verified_data_path is not None:
        candidate_include_root = verified_data_path / "MQL5" / "Include"
        trade_header = candidate_include_root / "Trade" / "Trade.mqh"
        try:
            if (
                not _path_has_reparse_component(candidate_include_root)
                and not _path_has_reparse_component(trade_header)
                and candidate_include_root.is_dir()
                and trade_header.is_file()
            ):
                standard_include_root = candidate_include_root.resolve(strict=True)
        except (OSError, RuntimeError, ValueError):
            standard_include_root = None

    binding = {
        "candidateId": candidate_id,
        "selectionRevision": revision,
        "platform": normalized_platform,
        "identityKey": identity,
        "localPath": canonical_local,
        "installPath": canonical_install,
        "dataPath": (
            os.path.normcase(str(Path(raw_data).resolve(strict=True)))
            if raw_data
            else None
        ),
    }
    return {
        "candidateId": candidate_id,
        "selectionRevision": revision,
        "platform": normalized_platform,
        "compilerPath": compiler.resolve(strict=True),
        "installPath": install_path.resolve(strict=True),
        "standardIncludeRoot": standard_include_root,
        "bindingDigest": _canonical_json_digest(binding),
    }


def _default_process_runner(command: list[str], cwd: Path, timeout_seconds: int) -> dict:
    started = time.perf_counter()
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 0x00000001)
        startupinfo.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
        creationflags = (
            getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        )
    process = None
    kill_job = None
    try:
        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
        kill_job = _windows_kill_on_close_job(process)
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired as error:
            _kill_process_tree(process, kill_job=kill_job)
            kill_job = None
            raise MetaEditorCompileError(
                "metaeditor_compile_timeout",
                process_started=True,
                exit_code="timeout",
                duration_ms=round((time.perf_counter() - started) * 1000),
            ) from error
    except MetaEditorCompileError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise MetaEditorCompileError(
            "metaeditor_process_start_failed",
            process_started=process is not None,
            duration_ms=round((time.perf_counter() - started) * 1000),
        ) from error
    finally:
        if kill_job is not None:
            _close_windows_handle(kill_job)
    if len(stdout or b"") + len(stderr or b"") > 64 * 1024:
        raise MetaEditorCompileError(
            "metaeditor_process_output_exceeded",
            process_started=True,
            exit_code=process.returncode,
            duration_ms=round((time.perf_counter() - started) * 1000),
        )
    return {
        "exitCode": int(process.returncode),
        "durationMs": round((time.perf_counter() - started) * 1000),
        "processStarted": True,
    }


def _close_windows_handle(handle: int | None) -> bool:
    if os.name != "nt" or not handle:
        return False
    try:
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_int
        return bool(kernel32.CloseHandle(ctypes.c_void_p(handle)))
    except (AttributeError, OSError, TypeError, ValueError):
        return False


def _windows_kill_on_close_job(process: subprocess.Popen) -> int | None:
    """Bind MetaEditor and descendants to a kill-on-close Windows Job."""

    if os.name != "nt":
        return None
    try:
        import ctypes

        class _IoCounters(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_uint64),
                ("WriteOperationCount", ctypes.c_uint64),
                ("OtherOperationCount", ctypes.c_uint64),
                ("ReadTransferCount", ctypes.c_uint64),
                ("WriteTransferCount", ctypes.c_uint64),
                ("OtherTransferCount", ctypes.c_uint64),
            ]

        class _BasicLimitInformation(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", ctypes.c_uint32),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", ctypes.c_uint32),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", ctypes.c_uint32),
                ("SchedulingClass", ctypes.c_uint32),
            ]

        class _ExtendedLimitInformation(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", _BasicLimitInformation),
                ("IoInfo", _IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
        kernel32.CreateJobObjectW.restype = ctypes.c_void_p
        kernel32.SetInformationJobObject.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_uint32,
        ]
        kernel32.SetInformationJobObject.restype = ctypes.c_int
        kernel32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        kernel32.AssignProcessToJobObject.restype = ctypes.c_int
        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            return None
        information = _ExtendedLimitInformation()
        information.BasicLimitInformation.LimitFlags = 0x00002000
        configured = kernel32.SetInformationJobObject(
            job,
            9,
            ctypes.byref(information),
            ctypes.sizeof(information),
        )
        process_handle = ctypes.c_void_p(int(getattr(process, "_handle")))
        assigned = bool(configured) and bool(
            kernel32.AssignProcessToJobObject(job, process_handle)
        )
        if not assigned:
            _close_windows_handle(int(job))
            return None
        return int(job)
    except (AttributeError, OSError, TypeError, ValueError):
        return None


def _kill_process_tree(
    process: subprocess.Popen,
    *,
    kill_job: int | None,
) -> None:
    """Terminate the full compiler tree, then wait for handle completion."""

    job_closed = _close_windows_handle(kill_job) if kill_job is not None else False
    if job_closed and process.poll() is None:
        try:
            process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            pass
    if os.name == "nt" and process.poll() is None:
        system_root = Path(os.environ.get("SystemRoot") or r"C:\Windows")
        taskkill = system_root / "System32" / "taskkill.exe"
        try:
            if (
                taskkill.is_file()
                and not _path_has_reparse_component(taskkill)
                and taskkill.name.lower() == "taskkill.exe"
            ):
                subprocess.run(
                    [str(taskkill), "/PID", str(int(process.pid)), "/T", "/F"],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=False,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),
                    check=False,
                )
        except (OSError, subprocess.TimeoutExpired, TypeError, ValueError):
            pass
    if process.poll() is None:
        try:
            process.kill()
        except OSError:
            pass
    try:
        process.wait(timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        pass


def _remove_owned_file(path: Path, root: Path) -> None:
    try:
        resolved_root = root.resolve(strict=True)
        lexical = path.absolute()
        if lexical.parent.resolve(strict=True) != resolved_root:
            raise MetaEditorCompileError("compile_output_path_unsafe")
        if not os.path.lexists(path):
            return
        if _path_has_reparse_component(path) or not path.is_file():
            raise MetaEditorCompileError("compile_output_path_unsafe")
        path.unlink()
    except MetaEditorCompileError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise MetaEditorCompileError("compile_output_cleanup_failed") from error


def compile_source(
    target: dict,
    source_path: Path,
    expected_source_digest: str,
    versions_root: Path,
    raw_log_path: Path,
    reports_root: Path,
    *,
    selection_is_current: Callable[[], bool],
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    process_runner: Callable[[list[str], Path, int], dict] | None = None,
) -> dict:
    """Compile one immutable source and accept only exact zero/zero evidence."""

    platform = str(target.get("platform") or "")
    expected_source_suffix = ".mq4" if platform == "mt4" else ".mq5" if platform == "mt5" else ""
    output_suffix = ".ex4" if platform == "mt4" else ".ex5" if platform == "mt5" else ""
    compiler = target.get("compilerPath")
    if not expected_source_suffix or not isinstance(compiler, Path):
        raise MetaEditorCompileError("compile_target_invalid")
    source_path = Path(source_path)
    versions_root = Path(versions_root)
    raw_log_path = Path(raw_log_path)
    reports_root = Path(reports_root)
    try:
        exact_versions_root = versions_root.resolve(strict=True)
        exact_reports_root = reports_root.resolve(strict=True)
        exact_source = source_path.resolve(strict=True)
        if (
            _path_has_reparse_component(versions_root)
            or _path_has_reparse_component(reports_root)
            or _path_has_reparse_component(source_path)
            or exact_source.parent != exact_versions_root
            or raw_log_path.parent.resolve(strict=True) != exact_reports_root
            or source_path.suffix.lower() != expected_source_suffix
            or raw_log_path.name != Path(raw_log_path.name).name
            or not raw_log_path.name.endswith(".raw.log")
        ):
            raise MetaEditorCompileError("compile_workspace_path_unsafe")
    except MetaEditorCompileError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise MetaEditorCompileError("compile_workspace_path_unsafe") from error
    if not re.fullmatch(r"[0-9a-f]{64}", str(expected_source_digest or "")):
        raise MetaEditorCompileError("source_digest_invalid")
    timeout = max(5, min(int(timeout_seconds), 180))
    source_digest_before, source_size, source_identity_before = _stable_file_digest(
        source_path,
        maximum_bytes=MAX_SOURCE_BYTES,
    )
    if not secrets.compare_digest(source_digest_before, expected_source_digest):
        raise MetaEditorCompileError("source_digest_mismatch")
    try:
        source_bytes = source_path.read_bytes()
    except OSError as error:
        raise MetaEditorCompileError("source_unavailable") from error
    source_dependencies = inspect_source_dependencies(source_bytes, platform)
    standard_include_before: dict | None = None
    if source_dependencies["usesMt5StandardTrade"]:
        standard_include_root = target.get("standardIncludeRoot")
        if not isinstance(standard_include_root, Path):
            raise MetaEditorCompileError("standard_include_tree_unavailable")
        standard_include_before = snapshot_standard_include_tree(
            standard_include_root
        )
    compiler_digest_before, compiler_size, compiler_identity_before = _stable_file_digest(
        compiler,
        maximum_bytes=MAX_COMPILER_BYTES,
    )
    if not selection_is_current():
        raise MetaEditorCompileError("terminal_selection_changed")

    output_path = source_path.with_suffix(output_suffix)
    _remove_owned_file(raw_log_path, exact_reports_root)
    # A deterministic binary left from a prior receipt is immutable evidence.
    # Never delete or overwrite it on retry.  A valid receipt is reused by the
    # caller; an orphan/spoofed binary fails closed for operator inspection.
    if os.path.lexists(output_path):
        raise MetaEditorCompileError("compile_output_preexisting_untrusted")
    command = [
        str(compiler),
        f"/compile:{source_path}",
        f"/log:{raw_log_path}",
    ]
    runner = process_runner or _default_process_runner
    process_result: dict | None = None
    accepted = False
    try:
        process_result = runner(command, Path(target["installPath"]), timeout)
        if not isinstance(process_result, dict):
            raise MetaEditorCompileError(
                "metaeditor_process_result_invalid",
                process_started=True,
            )
        duration_ms = int(process_result.get("durationMs") or 0)
        exit_code = process_result.get("exitCode")
        if (
            process_result.get("processStarted") is not True
            or isinstance(exit_code, bool)
            or not isinstance(exit_code, int)
            or duration_ms < 0
        ):
            raise MetaEditorCompileError(
                "metaeditor_process_result_invalid",
                process_started=process_result.get("processStarted") is True,
                exit_code=exit_code,
                duration_ms=max(0, duration_ms),
            )
        if not selection_is_current():
            raise MetaEditorCompileError(
                "terminal_selection_changed",
                process_started=True,
                exit_code=exit_code,
                duration_ms=duration_ms,
            )
        source_digest_after, _, source_identity_after = _stable_file_digest(
            source_path,
            maximum_bytes=MAX_SOURCE_BYTES,
        )
        if (
            not secrets.compare_digest(source_digest_before, source_digest_after)
            or source_identity_before != source_identity_after
        ):
            raise MetaEditorCompileError(
                "source_changed_during_compile",
                process_started=True,
                exit_code=exit_code,
                duration_ms=duration_ms,
            )
        compiler_digest_after, _, compiler_identity_after = _stable_file_digest(
            compiler,
            maximum_bytes=MAX_COMPILER_BYTES,
        )
        if (
            not secrets.compare_digest(compiler_digest_before, compiler_digest_after)
            or compiler_identity_before != compiler_identity_after
        ):
            raise MetaEditorCompileError(
                "compiler_changed_during_compile",
                process_started=True,
                exit_code=exit_code,
                duration_ms=duration_ms,
            )
        if standard_include_before is not None:
            try:
                standard_include_after = snapshot_standard_include_tree(
                    target["standardIncludeRoot"]
                )
            except MetaEditorCompileError as error:
                raise MetaEditorCompileError(
                    "standard_include_tree_changed",
                    process_started=True,
                    exit_code=exit_code,
                    duration_ms=duration_ms,
                ) from error
            if standard_include_after != standard_include_before:
                raise MetaEditorCompileError(
                    "standard_include_tree_changed",
                    process_started=True,
                    exit_code=exit_code,
                    duration_ms=duration_ms,
                )
        raw_log = _read_stable_bytes(raw_log_path, maximum_bytes=MAX_LOG_BYTES)
        log_text = _decode_metaeditor_log(raw_log)
        result_matches = list(re.finditer(
            r"(?im)^\s*Result:\s*(\d+)\s+errors?,\s*(\d+)\s+warnings?"
            r"(?:,\s*[^\r\n]{0,200})?\s*$",
            log_text,
        ))
        if len(result_matches) != 1:
            raise MetaEditorCompileError(
                "metaeditor_result_line_invalid",
                process_started=True,
                exit_code=exit_code,
                duration_ms=duration_ms,
            )
        errors = int(result_matches[0].group(1))
        warnings = int(result_matches[0].group(2))
        compile_mentions_source = bool(
            re.search(r"(?i)\bcompil(?:e|ing)\b", log_text)
            and source_path.name.lower() in log_text.lower()
        )
        if not compile_mentions_source:
            raise MetaEditorCompileError(
                "metaeditor_log_source_mismatch",
                process_started=True,
                exit_code=exit_code,
                errors=errors,
                warnings=warnings,
                duration_ms=duration_ms,
            )
        # MetaEditor builds in the field use both 0 and 1 for a completed
        # command-line compile.  The exit code is therefore supporting
        # evidence only; the fresh exact Result line and stable binary are the
        # authoritative pass gate.  Every other exit value still fails closed.
        if exit_code not in {0, 1} or errors != 0 or warnings != 0:
            raise MetaEditorCompileError(
                "metaeditor_compile_failed",
                process_started=True,
                exit_code=exit_code,
                errors=errors,
                warnings=warnings,
                duration_ms=duration_ms,
            )
        output_digest, output_size, _output_identity = _stable_file_digest(
            output_path,
            maximum_bytes=MAX_COMPILED_BYTES,
        )
        if not selection_is_current():
            raise MetaEditorCompileError(
                "terminal_selection_changed",
                process_started=True,
                exit_code=exit_code,
                errors=errors,
                warnings=warnings,
                duration_ms=duration_ms,
            )
        accepted = True
        return {
            "sourceFileName": source_path.name,
            "sourceDigest": source_digest_after,
            "sourceByteSize": source_size,
            "compiledFileName": output_path.name,
            "compiledDigest": output_digest,
            "compiledByteSize": output_size,
            "compilerDigest": compiler_digest_after,
            "compilerByteSize": compiler_size,
            "standardIncludeTreeDigest": (
                standard_include_before["treeDigest"]
                if standard_include_before is not None
                else None
            ),
            "standardIncludeFileCount": (
                standard_include_before["fileCount"]
                if standard_include_before is not None
                else 0
            ),
            "standardIncludeByteSize": (
                standard_include_before["byteSize"]
                if standard_include_before is not None
                else 0
            ),
            "processExitCode": exit_code,
            "errorCount": errors,
            "warningCount": warnings,
            "durationMs": duration_ms,
            "resultLine": "Result: 0 errors, 0 warnings",
        }
    except MetaEditorCompileError:
        raise
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        raise MetaEditorCompileError(
            "metaeditor_compile_evidence_invalid",
            process_started=bool((process_result or {}).get("processStarted")),
            exit_code=(process_result or {}).get("exitCode"),
            duration_ms=(process_result or {}).get("durationMs"),
        ) from error
    finally:
        try:
            _remove_owned_file(raw_log_path, exact_reports_root)
        except MetaEditorCompileError:
            pass
        if not accepted:
            try:
                _remove_owned_file(output_path, exact_versions_root)
            except MetaEditorCompileError:
                pass


__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "MAX_COMPILED_BYTES",
    "MetaEditorCompileError",
    "compile_source",
    "inspect_source_dependencies",
    "resolve_compile_target",
    "snapshot_standard_include_tree",
]
