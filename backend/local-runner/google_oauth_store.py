"""Current-user secure storage for the Google Sheets OAuth refresh token.

Only the encrypted DPAPI blob is persisted and it lives below LOCALAPPDATA,
outside the project checkout.  The browser, project runtime JSON, reports, and
audit log never receive the refresh token.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import secrets
import threading
import time
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path


_STORE_MAGIC = b"METAFX-GOOGLE-OAUTH-DPAPI\x00\x01"
_REFRESH_RECORD_MAGIC = b"METAFX-GOOGLE-OAUTH-REFRESH-RECORD\x00\x02"
_DPAPI_ENTROPY = b"Metafxclub.AgentHQ.GoogleSheets.RefreshToken.v1"
_CLIENT_STORE_MAGIC = b"METAFX-GOOGLE-OAUTH-CLIENT-DPAPI\x00\x01"
_CLIENT_DPAPI_ENTROPY = b"Metafxclub.AgentHQ.GoogleSheets.DesktopClient.v1"
_STORE_LOCK = threading.RLock()
_CRYPTPROTECT_UI_FORBIDDEN = 0x01
_CLIENT_GENERATION_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32,128}$")
_CLIENT_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{8,240}\.apps\.googleusercontent\.com$"
)


@dataclass(frozen=True)
class SecureStoreError(RuntimeError):
    code: str
    message: str

    def __str__(self) -> str:
        return self.message


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def credential_path() -> Path:
    local_app_data = str(os.environ.get("LOCALAPPDATA") or "").strip()
    base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return base / "Metafxclub" / "AgentHQ" / "credentials" / "google-sheets-refresh.dpapi"


def client_configuration_path() -> Path:
    local_app_data = str(os.environ.get("LOCALAPPDATA") or "").strip()
    base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return base / "Metafxclub" / "AgentHQ" / "credentials" / "google-oauth-client.dpapi"


def _transaction_lock_path() -> Path:
    return client_configuration_path().parent / ".google-oauth-store.lock"


class _OAuthStoreTransaction:
    def __init__(self, timeout_seconds: float) -> None:
        self.timeout_seconds = max(0.1, min(float(timeout_seconds), 30.0))
        self.handle = None
        self.msvcrt = None

    def __enter__(self):
        _STORE_LOCK.acquire()
        if os.name != "nt":
            # The durable store itself is Windows-only.  This branch keeps unit
            # tests deterministic without pretending to provide DPAPI elsewhere.
            return self
        try:
            import msvcrt

            path = _transaction_lock_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            self.handle = path.open("a+b")
            self.msvcrt = msvcrt
            if self.handle.seek(0, os.SEEK_END) == 0:
                self.handle.write(b"\x00")
                self.handle.flush()
                os.fsync(self.handle.fileno())
            deadline = time.monotonic() + self.timeout_seconds
            while True:
                self.handle.seek(0)
                try:
                    msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as error:
                    if time.monotonic() >= deadline:
                        self.handle.close()
                        self.handle = None
                        raise SecureStoreError(
                            "secure_store_busy",
                            "The Google authorization store is busy. Please try again.",
                        ) from error
                    time.sleep(0.05)
        except Exception:
            if self.handle is not None:
                self.handle.close()
                self.handle = None
            _STORE_LOCK.release()
            raise
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback) -> bool:
        try:
            if self.handle is not None and self.msvcrt is not None:
                try:
                    self.handle.seek(0)
                    self.msvcrt.locking(
                        self.handle.fileno(),
                        self.msvcrt.LK_UNLCK,
                        1,
                    )
                finally:
                    self.handle.close()
                    self.handle = None
        finally:
            _STORE_LOCK.release()
        return False


def oauth_store_transaction(*, timeout_seconds: float = 10.0):
    """Serialize short OAuth mutations across setup CLI and Bridge processes."""

    return _OAuthStoreTransaction(timeout_seconds)


def _blob(value: bytes) -> tuple[_DataBlob, ctypes.Array]:
    buffer = ctypes.create_string_buffer(value)
    return (
        _DataBlob(
            len(value),
            ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)),
        ),
        buffer,
    )


def _crypt32():
    if os.name != "nt":
        raise SecureStoreError(
            "secure_store_unavailable",
            "Windows current-user secure storage is unavailable on this system.",
        )
    try:
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
    except (AttributeError, OSError) as error:
        raise SecureStoreError(
            "secure_store_unavailable",
            "Windows current-user secure storage is unavailable.",
        ) from error
    return crypt32, kernel32


def _protect_with_entropy(cleartext: bytes, entropy: bytes) -> bytes:
    crypt32, kernel32 = _crypt32()
    input_blob, input_buffer = _blob(cleartext)
    entropy_blob, entropy_buffer = _blob(entropy)
    output_blob = _DataBlob()
    # Keep the input buffers alive for the duration of the native call.
    _ = (input_buffer, entropy_buffer)
    if not crypt32.CryptProtectData(
        ctypes.byref(input_blob),
        "Metafxclub Agent HQ Google Sheets",
        ctypes.byref(entropy_blob),
        None,
        None,
        _CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    ):
        raise SecureStoreError(
            "secure_store_write_failed",
            "Windows could not protect the Google authorization.",
        )
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        kernel32.LocalFree(output_blob.pbData)


def _unprotect_with_entropy(ciphertext: bytes, entropy: bytes) -> bytes:
    crypt32, kernel32 = _crypt32()
    input_blob, input_buffer = _blob(ciphertext)
    entropy_blob, entropy_buffer = _blob(entropy)
    output_blob = _DataBlob()
    _ = (input_buffer, entropy_buffer)
    if not crypt32.CryptUnprotectData(
        ctypes.byref(input_blob),
        None,
        ctypes.byref(entropy_blob),
        None,
        None,
        _CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    ):
        raise SecureStoreError(
            "secure_store_read_failed",
            "Windows could not unlock the saved Google authorization for this user.",
        )
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        kernel32.LocalFree(output_blob.pbData)


def _protect(cleartext: bytes) -> bytes:
    return _protect_with_entropy(cleartext, _DPAPI_ENTROPY)


def _unprotect(ciphertext: bytes) -> bytes:
    return _unprotect_with_entropy(ciphertext, _DPAPI_ENTROPY)


def _protect_client_configuration(cleartext: bytes) -> bytes:
    return _protect_with_entropy(cleartext, _CLIENT_DPAPI_ENTROPY)


def _unprotect_client_configuration(ciphertext: bytes) -> bytes:
    return _unprotect_with_entropy(ciphertext, _CLIENT_DPAPI_ENTROPY)


def _write_protected_payload(target: Path, payload: bytes) -> None:
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    with _STORE_LOCK:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with temporary.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, target)
        except OSError as error:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise SecureStoreError(
                "secure_store_write_failed",
                "The Google authorization configuration could not be saved securely for this Windows user.",
            ) from error


def _validate_client_generation(value: str) -> str:
    generation = str(value or "").strip()
    if not _CLIENT_GENERATION_PATTERN.fullmatch(generation):
        raise SecureStoreError(
            "invalid_oauth_client",
            "The Google OAuth Desktop client configuration is invalid.",
        )
    return generation


def save_refresh_token(
    refresh_token: str,
    *,
    client_generation: str = "",
    path: Path | None = None,
) -> None:
    token = str(refresh_token or "").strip()
    if not token or len(token) > 16384 or any(ord(character) < 32 for character in token):
        raise SecureStoreError(
            "invalid_refresh_token",
            "Google OAuth returned an invalid refresh credential.",
        )
    target = Path(path) if path is not None else credential_path()
    generation = str(client_generation or "").strip()
    if generation:
        generation = _validate_client_generation(generation)
        cleartext = _REFRESH_RECORD_MAGIC + json.dumps(
            {
                "schemaVersion": "google-oauth-refresh-v2",
                "clientGeneration": generation,
                "refreshToken": token,
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    else:
        # Read/write compatibility for the v1 store created by older releases.
        # Runtime OAuth callbacks always supply a generation and therefore use
        # the bound v2 record below; this legacy form is retained only for
        # in-place upgrades and direct compatibility callers.
        cleartext = token.encode("utf-8")
    ciphertext = _protect(cleartext)
    payload = _STORE_MAGIC + ciphertext
    _write_protected_payload(target, payload)


def load_refresh_token(
    *,
    expected_client_generation: str = "",
    path: Path | None = None,
) -> str | None:
    target = Path(path) if path is not None else credential_path()
    with _STORE_LOCK:
        try:
            payload = target.read_bytes()
        except FileNotFoundError:
            return None
        except OSError as error:
            raise SecureStoreError(
                "secure_store_read_failed",
                "The saved Google authorization could not be read.",
            ) from error
    if not payload.startswith(_STORE_MAGIC) or len(payload) <= len(_STORE_MAGIC):
        raise SecureStoreError(
            "secure_store_invalid",
            "The saved Google authorization is invalid and must be reconnected.",
        )
    try:
        cleartext = _unprotect(payload[len(_STORE_MAGIC) :])
        if cleartext.startswith(_REFRESH_RECORD_MAGIC):
            decoded = cleartext[len(_REFRESH_RECORD_MAGIC) :].decode(
                "utf-8",
                errors="strict",
            )
            record = json.loads(decoded)
            if (
                not isinstance(record, dict)
                or set(record) != {
                    "schemaVersion",
                    "clientGeneration",
                    "refreshToken",
                }
                or record.get("schemaVersion") != "google-oauth-refresh-v2"
                or not isinstance(record.get("clientGeneration"), str)
                or not isinstance(record.get("refreshToken"), str)
            ):
                raise ValueError("invalid refresh record")
            try:
                generation = _validate_client_generation(record["clientGeneration"])
            except SecureStoreError as error:
                raise ValueError("invalid refresh client generation") from error
            expected = str(expected_client_generation or "").strip()
            if expected:
                expected = _validate_client_generation(expected)
                if not secrets.compare_digest(generation, expected):
                    raise SecureStoreError(
                        "secure_store_client_mismatch",
                        "The saved Google authorization belongs to a different OAuth client and must be reconnected.",
                    )
            token = record["refreshToken"].strip()
        else:
            token = cleartext.decode("utf-8", errors="strict").strip()
    except SecureStoreError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise SecureStoreError(
            "secure_store_invalid",
            "The saved Google authorization is invalid and must be reconnected.",
        ) from error
    if not token or len(token) > 16384 or any(ord(character) < 32 for character in token):
        raise SecureStoreError(
            "secure_store_invalid",
            "The saved Google authorization is invalid and must be reconnected.",
        )
    return token


def delete_refresh_token(*, path: Path | None = None) -> bool:
    target = Path(path) if path is not None else credential_path()
    with _STORE_LOCK:
        try:
            target.unlink()
            return True
        except FileNotFoundError:
            return False
        except OSError as error:
            raise SecureStoreError(
                "secure_store_delete_failed",
                "The saved Google authorization could not be removed.",
            ) from error


def validate_client_configuration(client_id: str, client_secret: str = "") -> dict[str, str]:
    normalized_id = str(client_id or "").strip()
    normalized_secret = str(client_secret or "").strip()
    if not _CLIENT_ID_PATTERN.fullmatch(normalized_id):
        raise SecureStoreError(
            "invalid_oauth_client",
            "The Google OAuth Desktop client configuration is invalid.",
        )
    if (
        len(normalized_secret) > 2048
        or any(ord(character) < 32 for character in normalized_secret)
    ):
        raise SecureStoreError(
            "invalid_oauth_client",
            "The Google OAuth Desktop client configuration is invalid.",
        )
    return {"clientId": normalized_id, "clientSecret": normalized_secret}


def _legacy_client_generation(configuration: dict[str, str]) -> str:
    material = (
        "google-oauth-client-legacy-v1\x00"
        + configuration["clientId"]
        + "\x00"
        + configuration["clientSecret"]
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _new_client_generation() -> str:
    return secrets.token_urlsafe(32)


def save_client_configuration(
    client_id: str,
    client_secret: str = "",
    *,
    client_generation: str = "",
    path: Path | None = None,
) -> str:
    configuration = validate_client_configuration(client_id, client_secret)
    target = Path(path) if path is not None else client_configuration_path()
    generation = str(client_generation or "").strip()
    if generation:
        generation = _validate_client_generation(generation)
    else:
        # Idempotent re-import of the same client preserves the generation and
        # any in-flight authorization that was started for that exact client.
        try:
            previous = _load_client_configuration_record(path=target)
        except SecureStoreError:
            previous = None
        if (
            isinstance(previous, dict)
            and secrets.compare_digest(previous.get("clientId", ""), configuration["clientId"])
            and secrets.compare_digest(previous.get("clientSecret", ""), configuration["clientSecret"])
        ):
            generation = previous["clientGeneration"]
        else:
            generation = _new_client_generation()
    cleartext = json.dumps(
        {
            "schemaVersion": "google-oauth-desktop-client-v2",
            **configuration,
            "clientGeneration": generation,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    ciphertext = _protect_client_configuration(cleartext)
    _write_protected_payload(target, _CLIENT_STORE_MAGIC + ciphertext)
    return generation


def _load_client_configuration_record(*, path: Path | None = None) -> dict[str, str] | None:
    target = Path(path) if path is not None else client_configuration_path()
    with _STORE_LOCK:
        try:
            payload = target.read_bytes()
        except FileNotFoundError:
            return None
        except OSError as error:
            raise SecureStoreError(
                "secure_store_read_failed",
                "The saved Google OAuth client configuration could not be read.",
            ) from error
    if not payload.startswith(_CLIENT_STORE_MAGIC) or len(payload) <= len(_CLIENT_STORE_MAGIC):
        raise SecureStoreError(
            "secure_store_invalid",
            "The saved Google OAuth client configuration is invalid and must be replaced.",
        )
    try:
        decoded = _unprotect_client_configuration(payload[len(_CLIENT_STORE_MAGIC) :]).decode(
            "utf-8",
            errors="strict",
        )
        parsed = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SecureStoreError(
            "secure_store_invalid",
            "The saved Google OAuth client configuration is invalid and must be replaced.",
        ) from error
    if not isinstance(parsed, dict):
        raise SecureStoreError(
            "secure_store_invalid",
            "The saved Google OAuth client configuration is invalid and must be replaced.",
        )
    schema_version = parsed.get("schemaVersion")
    if schema_version == "google-oauth-desktop-client-v1" and set(parsed) == {
        "schemaVersion",
        "clientId",
        "clientSecret",
    }:
        configuration = validate_client_configuration(
            str(parsed.get("clientId") or ""),
            str(parsed.get("clientSecret") or ""),
        )
        return {
            **configuration,
            "clientGeneration": _legacy_client_generation(configuration),
        }
    if schema_version != "google-oauth-desktop-client-v2" or set(parsed) != {
        "schemaVersion",
        "clientId",
        "clientSecret",
        "clientGeneration",
    }:
        raise SecureStoreError(
            "secure_store_invalid",
            "The saved Google OAuth client configuration is invalid and must be replaced.",
        )
    configuration = validate_client_configuration(
        str(parsed.get("clientId") or ""),
        str(parsed.get("clientSecret") or ""),
    )
    try:
        generation = _validate_client_generation(str(parsed.get("clientGeneration") or ""))
    except SecureStoreError as error:
        raise SecureStoreError(
            "secure_store_invalid",
            "The saved Google OAuth client configuration is invalid and must be replaced.",
        ) from error
    return {**configuration, "clientGeneration": generation}


def load_client_configuration(*, path: Path | None = None) -> dict[str, str] | None:
    record = _load_client_configuration_record(path=path)
    if not record:
        return None
    return {
        "clientId": record["clientId"],
        "clientSecret": record["clientSecret"],
    }


def load_client_configuration_record(*, path: Path | None = None) -> dict[str, str] | None:
    """Return the private client generation for backend transaction binding."""

    return _load_client_configuration_record(path=path)


def delete_client_configuration(*, path: Path | None = None) -> bool:
    target = Path(path) if path is not None else client_configuration_path()
    with _STORE_LOCK:
        try:
            target.unlink()
            return True
        except FileNotFoundError:
            return False
        except OSError as error:
            raise SecureStoreError(
                "secure_store_delete_failed",
                "The saved Google OAuth client configuration could not be removed.",
            ) from error


def client_id_hint(client_id: str) -> str:
    normalized = str(client_id or "").strip()
    if not normalized:
        return ""
    suffix = ".apps.googleusercontent.com"
    core = normalized[: -len(suffix)] if normalized.endswith(suffix) else normalized
    if len(core) <= 12:
        return f"{core[:4]}…{core[-3:]}"
    return f"{core[:8]}…{core[-5:]}"


def client_configuration_status(*, path: Path | None = None) -> dict:
    try:
        configuration = load_client_configuration(path=path)
    except SecureStoreError as error:
        return {
            "available": os.name == "nt",
            "stored": False,
            "status": error.code,
            "clientHint": "",
            "secretStored": False,
        }
    return {
        "available": os.name == "nt",
        "stored": bool(configuration),
        "status": "ready" if configuration else "empty",
        "clientHint": client_id_hint((configuration or {}).get("clientId", "")),
        "secretStored": bool((configuration or {}).get("clientSecret")),
    }


def status(
    *,
    expected_client_generation: str = "",
    path: Path | None = None,
) -> dict:
    try:
        token = load_refresh_token(
            expected_client_generation=expected_client_generation,
            path=path,
        )
    except SecureStoreError as error:
        return {
            "available": os.name == "nt",
            "stored": False,
            "status": error.code,
        }
    return {
        "available": os.name == "nt",
        "stored": bool(token),
        "status": "ready" if token else "empty",
    }
