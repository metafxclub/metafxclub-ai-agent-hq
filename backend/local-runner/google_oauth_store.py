"""Current-user secure storage for the Google Sheets OAuth refresh token.

Only the encrypted DPAPI blob is persisted and it lives below LOCALAPPDATA,
outside the project checkout.  The browser, project runtime JSON, reports, and
audit log never receive the refresh token.
"""

from __future__ import annotations

import ctypes
import json
import os
import re
import threading
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path


_STORE_MAGIC = b"METAFX-GOOGLE-OAUTH-DPAPI\x00\x01"
_DPAPI_ENTROPY = b"Metafxclub.AgentHQ.GoogleSheets.RefreshToken.v1"
_CLIENT_STORE_MAGIC = b"METAFX-GOOGLE-OAUTH-CLIENT-DPAPI\x00\x01"
_CLIENT_DPAPI_ENTROPY = b"Metafxclub.AgentHQ.GoogleSheets.DesktopClient.v1"
_STORE_LOCK = threading.RLock()
_CRYPTPROTECT_UI_FORBIDDEN = 0x01
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


def save_refresh_token(refresh_token: str, *, path: Path | None = None) -> None:
    token = str(refresh_token or "").strip()
    if not token or len(token) > 16384 or any(ord(character) < 32 for character in token):
        raise SecureStoreError(
            "invalid_refresh_token",
            "Google OAuth returned an invalid refresh credential.",
        )
    target = Path(path) if path is not None else credential_path()
    ciphertext = _protect(token.encode("utf-8"))
    payload = _STORE_MAGIC + ciphertext
    _write_protected_payload(target, payload)


def load_refresh_token(*, path: Path | None = None) -> str | None:
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
        token = _unprotect(payload[len(_STORE_MAGIC) :]).decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as error:
        raise SecureStoreError(
            "secure_store_invalid",
            "The saved Google authorization is invalid and must be reconnected.",
        ) from error
    if not token:
        raise SecureStoreError(
            "secure_store_invalid",
            "The saved Google authorization is empty and must be reconnected.",
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


def save_client_configuration(
    client_id: str,
    client_secret: str = "",
    *,
    path: Path | None = None,
) -> None:
    configuration = validate_client_configuration(client_id, client_secret)
    cleartext = json.dumps(
        {
            "schemaVersion": "google-oauth-desktop-client-v1",
            **configuration,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    target = Path(path) if path is not None else client_configuration_path()
    ciphertext = _protect_client_configuration(cleartext)
    _write_protected_payload(target, _CLIENT_STORE_MAGIC + ciphertext)


def load_client_configuration(*, path: Path | None = None) -> dict[str, str] | None:
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
    if (
        not isinstance(parsed, dict)
        or parsed.get("schemaVersion") != "google-oauth-desktop-client-v1"
        or set(parsed) != {"schemaVersion", "clientId", "clientSecret"}
    ):
        raise SecureStoreError(
            "secure_store_invalid",
            "The saved Google OAuth client configuration is invalid and must be replaced.",
        )
    return validate_client_configuration(
        str(parsed.get("clientId") or ""),
        str(parsed.get("clientSecret") or ""),
    )


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


def status(*, path: Path | None = None) -> dict:
    try:
        token = load_refresh_token(path=path)
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
