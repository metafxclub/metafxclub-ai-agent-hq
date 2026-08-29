"""Backend-only Google Sheets transport for the Metafxclub research hub.

The browser supplies only a spreadsheet id and may launch a one-time Google
authorization in the system browser. Credentials stay in the Local Runner and
are never returned to the frontend, reports, project runtime files, or audit
log. The module intentionally uses the standard library so the guarded runner
does not silently depend on an uninstalled Google SDK.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen

import google_oauth_store


SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"
GOOGLE_API_ROOT = "https://sheets.googleapis.com/v4/spreadsheets"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_OAUTH_CALLBACK_PATH = "/api/props/mission_strategy_table/research-sheet/auth/callback"
GOOGLE_OAUTH_FLOW_TTL_SECONDS = 10 * 60
GOOGLE_OAUTH_MAX_PENDING_FLOWS = 8
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_OAUTH_ERROR_RESPONSE_BYTES = 16 * 1024
MAX_OAUTH_CLIENT_JSON_BYTES = 64 * 1024
DEFAULT_TIMEOUT_SECONDS = 20
SAFE_SHEET_ID = re.compile(r"^[A-Za-z0-9_-]{20,128}$")
_OAUTH_FLOW_LOCK = threading.RLock()
_PENDING_OAUTH_FLOWS: dict[str, dict] = {}
_OAUTH_PROVIDER_ERROR_MAP = {
    "client_secret_required": (
        "oauth_client_secret_required",
        "Google requires the Client Secret for this OAuth client. Configure the matching Client Secret in Local Runner and reconnect.",
        503,
    ),
    "invalid_client": (
        "oauth_invalid_client",
        "Google rejected the OAuth client. Verify the Desktop OAuth Client ID and optional matching Client Secret, then restart Local Runner.",
        503,
    ),
    "unauthorized_client": (
        "oauth_invalid_client",
        "Google rejected the OAuth client. Verify the Desktop OAuth Client ID and optional matching Client Secret, then restart Local Runner.",
        503,
    ),
    "invalid_grant": (
        "oauth_code_invalid_or_expired",
        "The one-time Google authorization was invalid, expired, already used, or failed PKCE validation. Start a new connection.",
        400,
    ),
    "redirect_uri_mismatch": (
        "oauth_redirect_mismatch",
        "Google rejected the loopback callback address. Use a Desktop OAuth client and start the connection again.",
        400,
    ),
    "invalid_scope": (
        "oauth_scope_missing",
        "Google did not accept the required Google Sheets scope. Verify the OAuth consent configuration and reconnect.",
        403,
    ),
    "invalid_request": (
        "oauth_invalid_request",
        "Google rejected the OAuth token request. Verify the Desktop OAuth client configuration and reconnect.",
        400,
    ),
    "access_denied": (
        "oauth_authorization_denied",
        "Google Sheets access was not granted. Start the connection again and approve the requested access.",
        403,
    ),
    "rate_limit_exceeded": (
        "oauth_rate_limited",
        "Google OAuth is temporarily rate limiting requests. Wait briefly and reconnect.",
        429,
    ),
    "slow_down": (
        "oauth_rate_limited",
        "Google OAuth is temporarily rate limiting requests. Wait briefly and reconnect.",
        429,
    ),
    "temporarily_unavailable": (
        "oauth_unavailable",
        "Google OAuth is temporarily unavailable. Wait briefly and reconnect.",
        503,
    ),
}


@dataclass(frozen=True)
class GoogleSheetHubError(RuntimeError):
    code: str
    message: str
    status: int = 502
    write_unknown: bool = False

    def __str__(self) -> str:
        return self.message


def _environment_oauth_client(env: dict[str, str]) -> dict[str, str]:
    client_id = str(env.get("METAFX_GOOGLE_OAUTH_CLIENT_ID") or "").strip()
    client_secret = str(env.get("METAFX_GOOGLE_OAUTH_CLIENT_SECRET") or "").strip()
    return {
        "clientId": client_id,
        "clientSecret": client_secret,
        "source": "environment" if client_id else "not_configured",
    }


def oauth_client_configuration(environ: dict[str, str] | None = None) -> dict[str, str]:
    """Resolve a Desktop OAuth client without exposing it to the browser.

    An explicitly supplied environment mapping is an isolated/test contract and
    therefore never falls through to the current user's durable store.  Normal
    runtime calls use the DPAPI-protected client first, then the legacy
    environment configuration as a backwards-compatible fallback.
    """

    env = environ if isinstance(environ, dict) else os.environ
    if environ is None:
        try:
            stored = google_oauth_store.load_client_configuration()
        except google_oauth_store.SecureStoreError as error:
            raise GoogleSheetHubError(error.code, error.message, 503) from error
        if isinstance(stored, dict) and str(stored.get("clientId") or "").strip():
            return {
                "clientId": str(stored.get("clientId") or "").strip(),
                "clientSecret": str(stored.get("clientSecret") or "").strip(),
                "source": "secure_store",
            }
    return _environment_oauth_client(env)


def _safe_client_status(configuration: dict[str, str]) -> dict:
    client_id = str(configuration.get("clientId") or "").strip()
    return {
        "configured": bool(client_id),
        "source": str(configuration.get("source") or "not_configured"),
        "clientHint": google_oauth_store.client_id_hint(client_id),
    }


def parse_google_oauth_client_json(raw_json: str | bytes) -> dict[str, str]:
    """Parse one downloaded Google Desktop OAuth JSON file, fail closed."""

    if isinstance(raw_json, bytes):
        if len(raw_json) > MAX_OAUTH_CLIENT_JSON_BYTES:
            raise GoogleSheetHubError(
                "oauth_client_file_too_large",
                "The Google OAuth client file exceeds the allowed size.",
                413,
            )
        try:
            text = raw_json.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise GoogleSheetHubError(
                "invalid_oauth_client_file",
                "The selected file is not valid UTF-8 JSON.",
                422,
            ) from error
    else:
        text = str(raw_json or "")
        if len(text.encode("utf-8")) > MAX_OAUTH_CLIENT_JSON_BYTES:
            raise GoogleSheetHubError(
                "oauth_client_file_too_large",
                "The Google OAuth client file exceeds the allowed size.",
                413,
            )
    try:
        decoded = json.loads(text)
    except json.JSONDecodeError as error:
        raise GoogleSheetHubError(
            "invalid_oauth_client_file",
            "The selected file is not valid Google OAuth client JSON.",
            422,
        ) from error
    if not isinstance(decoded, dict) or not isinstance(decoded.get("installed"), dict):
        raise GoogleSheetHubError(
            "oauth_client_not_desktop",
            "Select an OAuth Client JSON created as a Google Desktop app.",
            422,
        )
    installed = decoded["installed"]
    client_id = installed.get("client_id")
    client_secret = installed.get("client_secret", "")
    if not isinstance(client_id, str) or not isinstance(client_secret, str):
        raise GoogleSheetHubError(
            "invalid_oauth_client_file",
            "The Google OAuth Desktop client file has an invalid credential shape.",
            422,
        )
    auth_uri = installed.get("auth_uri")
    token_uri = installed.get("token_uri")
    if auth_uri != "https://accounts.google.com/o/oauth2/auth" or token_uri != GOOGLE_TOKEN_URL:
        raise GoogleSheetHubError(
            "invalid_oauth_client_file",
            "The Google OAuth Desktop client endpoints are invalid.",
            422,
        )
    redirect_uris = installed.get("redirect_uris")
    if not isinstance(redirect_uris, list) or not redirect_uris:
        raise GoogleSheetHubError(
            "oauth_client_not_desktop",
            "The Google OAuth client does not allow a Desktop loopback callback.",
            422,
        )
    loopback_ready = False
    for value in redirect_uris:
        if not isinstance(value, str):
            continue
        parsed = urlsplit(value)
        if (
            parsed.scheme == "http"
            and parsed.hostname in {"localhost", "127.0.0.1"}
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
        ):
            loopback_ready = True
            break
    if not loopback_ready:
        raise GoogleSheetHubError(
            "oauth_client_not_desktop",
            "The Google OAuth client does not allow a Desktop loopback callback.",
            422,
        )
    try:
        # Reuse the store's strict field validation without writing anything.
        return google_oauth_store.validate_client_configuration(client_id, client_secret)
    except google_oauth_store.SecureStoreError as error:
        raise GoogleSheetHubError(error.code, error.message, 422) from error


def configure_google_oauth_client_json(
    raw_json: str | bytes,
    *,
    expected_client_id: str = "",
) -> dict:
    configuration = parse_google_oauth_client_json(raw_json)
    normalized_expected = str(expected_client_id or "").strip()
    if normalized_expected and not secrets.compare_digest(
        configuration["clientId"],
        normalized_expected,
    ):
        raise GoogleSheetHubError(
            "oauth_client_id_mismatch",
            "The OAuth JSON does not match the expected Desktop Client ID.",
            422,
        )
    try:
        previous = oauth_client_configuration()
    except GoogleSheetHubError:
        previous = {"clientId": "", "clientSecret": "", "source": "not_configured"}
    same_configuration = (
        secrets.compare_digest(
            str(previous.get("clientId") or ""),
            configuration["clientId"],
        )
        and secrets.compare_digest(
            str(previous.get("clientSecret") or ""),
            configuration.get("clientSecret", ""),
        )
    )
    try:
        # Delete the old refresh token before publishing a changed client.  If
        # secure deletion fails the old pair remains untouched; if the later
        # atomic client write fails, the safe outcome is merely reconnecting
        # the previous client instead of exposing a mismatched pair as ready.
        authorization_reset = (
            google_oauth_store.delete_refresh_token()
            if not same_configuration
            else False
        )
        google_oauth_store.save_client_configuration(
            configuration["clientId"],
            configuration.get("clientSecret", ""),
        )
    except google_oauth_store.SecureStoreError as error:
        raise GoogleSheetHubError(error.code, error.message, 503) from error
    with _OAUTH_FLOW_LOCK:
        _PENDING_OAUTH_FLOWS.clear()
    return {
        "ok": True,
        "kind": "google_oauth_client_configured",
        "configured": True,
        "clientHint": google_oauth_store.client_id_hint(configuration["clientId"]),
        "clientSource": "secure_store",
        "store": "windows_current_user_secure_store",
        "authorizationReset": authorization_reset,
    }


def remove_google_oauth_client_configuration(
    environ: dict[str, str] | None = None,
) -> dict:
    """Explicitly remove both durable OAuth artifacts for this Windows user."""

    env = environ if isinstance(environ, dict) else os.environ
    # Consume every in-flight callback before deleting either durable value so
    # a late browser redirect cannot recreate a refresh grant after removal.
    with _OAUTH_FLOW_LOCK:
        _PENDING_OAUTH_FLOWS.clear()
    try:
        refresh_removed = google_oauth_store.delete_refresh_token()
        client_removed = google_oauth_store.delete_client_configuration()
    except google_oauth_store.SecureStoreError as error:
        raise GoogleSheetHubError(error.code, error.message, 503) from error
    environment_fallback = bool(
        str(env.get("METAFX_GOOGLE_OAUTH_CLIENT_ID") or "").strip()
        or str(env.get("METAFX_GOOGLE_OAUTH_REFRESH_TOKEN") or "").strip()
        or str(env.get("METAFX_GOOGLE_SHEETS_ACCESS_TOKEN") or "").strip()
    )
    return {
        "ok": True,
        "kind": "google_oauth_client_removed",
        "configured": False,
        "clientHint": "",
        "store": "empty",
        "removed": bool(refresh_removed or client_removed),
        "clientRemoved": client_removed,
        "authorizationRemoved": refresh_removed,
        "environmentFallbackActive": environment_fallback,
    }


def credential_status(environ: dict[str, str] | None = None) -> dict:
    env = environ if isinstance(environ, dict) else os.environ
    direct = bool(str(env.get("METAFX_GOOGLE_SHEETS_ACCESS_TOKEN") or "").strip())
    environment_client_id = bool(str(env.get("METAFX_GOOGLE_OAUTH_CLIENT_ID") or "").strip())
    environment_client_secret = bool(str(env.get("METAFX_GOOGLE_OAUTH_CLIENT_SECRET") or "").strip())
    client_configuration_error = ""
    try:
        client = oauth_client_configuration(environ)
    except GoogleSheetHubError as error:
        client = {"clientId": "", "clientSecret": "", "source": "not_configured"}
        client_configuration_error = error.code
    client_id = bool(str(client.get("clientId") or "").strip())
    environment_refresh_token = bool(
        str(env.get("METAFX_GOOGLE_OAUTH_REFRESH_TOKEN") or "").strip()
    )
    environment_refresh = environment_client_id and environment_refresh_token
    store = google_oauth_store.status()
    stored_refresh = client_id and store.get("stored") is True
    partial_refresh = (
        any((client_id, environment_client_secret, environment_refresh_token))
        and not (environment_refresh or stored_refresh)
    )
    configured = direct or environment_refresh or stored_refresh
    if direct:
        mode = "access_token"
    elif environment_refresh:
        mode = "oauth_refresh"
    elif stored_refresh:
        mode = "oauth_refresh_stored"
    else:
        mode = "not_configured"
    return {
        "configured": configured,
        "mode": mode,
        "partialConfiguration": partial_refresh,
        "credentialsAcceptedByFrontend": False,
        "oauthClientConfigured": client_id,
        "oauthClientSource": str(client.get("source") or "not_configured"),
        "oauthClientHint": google_oauth_store.client_id_hint(
            str(client.get("clientId") or "")
        ),
        "storedRefreshToken": store.get("stored") is True,
        "oauthClientStoreStatus": (
            client_configuration_error
            or (
                "ready"
                if client.get("source") == "secure_store"
                else ("environment" if client_id else "empty")
            )
        ),
        "secureStoreStatus": str(store.get("status") or "unknown"),
        "environmentCredential": direct or environment_refresh,
    }


def google_oauth_status(environ: dict[str, str] | None = None) -> dict:
    credential = credential_status(environ)
    configured = credential.get("configured") is True
    client_configured = credential.get("oauthClientConfigured") is True
    if configured:
        status = "connected"
        message_th = "Google Sheets เชื่อมต่อกับ Local Runner แล้ว"
    elif not client_configured:
        client_store_status = str(
            credential.get("oauthClientStoreStatus") or "empty"
        )
        if client_store_status not in {"empty", "ready", "environment"}:
            status = client_store_status
            message_th = "ที่เก็บ OAuth Client ของ Windows ไม่พร้อมใช้งาน กรุณาตั้งค่าไฟล์ Desktop OAuth ใหม่"
        else:
            status = "oauth_client_not_configured"
            message_th = "Local Runner ยังไม่ได้ตั้งค่า Google OAuth Client ID"
    elif credential.get("secureStoreStatus") not in {"empty", "ready"}:
        status = str(credential.get("secureStoreStatus") or "secure_store_unavailable")
        message_th = "ที่เก็บสิทธิ์ Google ของ Windows ไม่พร้อมใช้งาน กรุณาตรวจ Local Runner"
    else:
        status = "authorization_required"
        message_th = "พร้อมเชื่อมต่อ Google กรุณากดเชื่อมต่อหนึ่งครั้ง"
    return {
        "configured": configured,
        "connected": configured,
        "status": status,
        "mode": str(credential.get("mode") or "not_configured"),
        "clientConfigured": client_configured,
        "clientSource": str(credential.get("oauthClientSource") or "not_configured"),
        "clientHint": str(credential.get("oauthClientHint") or ""),
        "messageTh": message_th,
        "credentialsAcceptedByFrontend": False,
        "storedCredential": credential.get("storedRefreshToken") is True,
        "environmentCredential": credential.get("environmentCredential") is True,
    }


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _validate_redirect_uri(redirect_uri: str) -> str:
    value = str(redirect_uri or "").strip()
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError as error:
        raise GoogleSheetHubError(
            "invalid_oauth_redirect",
            "Google OAuth callback address is invalid.",
            422,
        ) from error
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or port is None
        or not 1024 <= port <= 65535
        or parsed.path != GOOGLE_OAUTH_CALLBACK_PATH
        or parsed.query
        or parsed.fragment
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise GoogleSheetHubError(
            "invalid_oauth_redirect",
            "Google OAuth callback must use the exact Local Runner loopback address.",
            422,
        )
    return value


def _purge_pending_oauth_flows(now_monotonic: float) -> None:
    expired = [
        state
        for state, flow in _PENDING_OAUTH_FLOWS.items()
        if float(flow.get("expiresAtMonotonic") or 0) <= now_monotonic
    ]
    for state in expired:
        _PENDING_OAUTH_FLOWS.pop(state, None)


def start_google_oauth(
    redirect_uri: str,
    environ: dict[str, str] | None = None,
    *,
    now_monotonic: float | None = None,
) -> dict:
    client = oauth_client_configuration(environ)
    client_id = str(client.get("clientId") or "").strip()
    client_secret = str(client.get("clientSecret") or "").strip()
    if not client_id:
        raise GoogleSheetHubError(
            "oauth_client_not_configured",
            "Google OAuth Client ID is not configured in the Local Runner.",
            503,
        )
    callback = _validate_redirect_uri(redirect_uri)
    verifier = _base64url(secrets.token_bytes(64))
    if not 43 <= len(verifier) <= 128:
        raise GoogleSheetHubError(
            "oauth_pkce_generation_failed",
            "Local Runner could not create a secure Google authorization request.",
            500,
        )
    challenge = _base64url(hashlib.sha256(verifier.encode("ascii")).digest())
    state = _base64url(secrets.token_bytes(32))
    now = time.monotonic() if now_monotonic is None else float(now_monotonic)
    with _OAUTH_FLOW_LOCK:
        _purge_pending_oauth_flows(now)
        while len(_PENDING_OAUTH_FLOWS) >= GOOGLE_OAUTH_MAX_PENDING_FLOWS:
            oldest_state = min(
                _PENDING_OAUTH_FLOWS,
                key=lambda value: float(
                    _PENDING_OAUTH_FLOWS[value].get("createdAtMonotonic") or 0
                ),
            )
            _PENDING_OAUTH_FLOWS.pop(oldest_state, None)
        _PENDING_OAUTH_FLOWS[state] = {
            "verifier": verifier,
            "redirectUri": callback,
            "clientId": client_id,
            "clientSecret": client_secret,
            "createdAtMonotonic": now,
            "expiresAtMonotonic": now + GOOGLE_OAUTH_FLOW_TTL_SECONDS,
        }
    authorization_url = GOOGLE_AUTHORIZATION_URL + "?" + urlencode(
        {
            "client_id": client_id,
            "redirect_uri": callback,
            "response_type": "code",
            "scope": SHEETS_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    return {
        "ok": True,
        "kind": "google_oauth_authorization_started",
        "authorizationUrl": authorization_url,
        "expiresInSeconds": GOOGLE_OAUTH_FLOW_TTL_SECONDS,
        "auth": google_oauth_status(environ),
    }


def _single_query_value(query: dict[str, list[str]], name: str) -> str:
    values = query.get(name)
    if not isinstance(values, list) or len(values) != 1:
        return ""
    return str(values[0] or "").strip()


def _oauth_token_response(response) -> dict:
    try:
        return _read_json_response(response)
    except GoogleSheetHubError as error:
        raise GoogleSheetHubError(
            "oauth_invalid_response",
            "Google OAuth returned an invalid token response.",
            502,
        ) from error


def _allowlisted_provider_oauth_error(error: HTTPError) -> str | None:
    """Read only a bounded JSON provider error code; discard all other text."""

    try:
        payload = error.read(MAX_OAUTH_ERROR_RESPONSE_BYTES + 1)
    except (AttributeError, OSError, ValueError):
        return None
    if not isinstance(payload, bytes) or len(payload) > MAX_OAUTH_ERROR_RESPONSE_BYTES:
        return None
    try:
        decoded = json.loads(payload.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(decoded, dict):
        return None
    provider_error = decoded.get("error")
    if not isinstance(provider_error, str):
        return None
    normalized = provider_error.strip().lower()
    # Google Desktop/PKCE may currently require a client_secret for some
    # clients despite the native-app documentation marking it optional. Read
    # only this exact known description in memory and collapse it immediately
    # to a non-sensitive internal condition; never return or persist the text.
    description = decoded.get("error_description")
    if normalized == "invalid_request" and isinstance(description, str):
        normalized_description = " ".join(description.strip().lower().split())
        if (
            normalized_description in {
                "client_secret is missing",
                "client_secret is missing.",
            }
            or normalized_description.startswith("client_secret is missing. ")
        ):
            return "client_secret_required"
    return normalized if normalized in _OAUTH_PROVIDER_ERROR_MAP else None


def _classified_oauth_http_error(
    error: HTTPError,
    *,
    refresh_grant: bool = False,
) -> GoogleSheetHubError:
    status_code = int(getattr(error, "code", 0) or 0)
    try:
        provider_error = _allowlisted_provider_oauth_error(error)
    finally:
        # HTTPError owns the provider response stream.  Python 3.14 warns when
        # that stream is finalized implicitly, and the warning may include the
        # untrusted provider reason.  Close it deterministically after the one
        # bounded read so provider-controlled text cannot leak to stderr.
        try:
            error.close()
        except (AttributeError, OSError, ValueError):
            pass
    if status_code == 429:
        return GoogleSheetHubError(
            "oauth_rate_limited",
            "Google OAuth is temporarily rate limiting requests. Wait briefly and reconnect.",
            429,
        )
    if status_code >= 500:
        return GoogleSheetHubError(
            "oauth_unavailable",
            "Google OAuth is temporarily unavailable. Wait briefly and reconnect.",
            503,
        )
    if refresh_grant and provider_error == "invalid_grant":
        return GoogleSheetHubError(
            "auth_expired",
            "Google Sheets authorization is invalid or expired. Please reconnect Google Sheets.",
            401,
        )
    if provider_error:
        code, message, status = _OAUTH_PROVIDER_ERROR_MAP[provider_error]
        return GoogleSheetHubError(code, message, status)
    if refresh_grant and status_code in {400, 401}:
        return GoogleSheetHubError(
            "auth_expired",
            "Google Sheets authorization is invalid or expired. Please reconnect Google Sheets.",
            401,
        )
    return GoogleSheetHubError(
        "oauth_exchange_rejected",
        "Google OAuth did not accept the one-time authorization.",
        502,
    )


def complete_google_oauth(
    query: dict[str, list[str]],
    environ: dict[str, str] | None = None,
    *,
    open_url: Callable = urlopen,
    now_monotonic: float | None = None,
) -> dict:
    state = _single_query_value(query, "state")
    if not state or len(state) > 256:
        raise GoogleSheetHubError(
            "oauth_state_invalid",
            "Google authorization state is invalid or has already been used.",
            400,
        )
    now = time.monotonic() if now_monotonic is None else float(now_monotonic)
    with _OAUTH_FLOW_LOCK:
        flow = _PENDING_OAUTH_FLOWS.pop(state, None)
    if not isinstance(flow, dict):
        raise GoogleSheetHubError(
            "oauth_state_invalid",
            "Google authorization state is invalid or has already been used.",
            400,
        )
    if float(flow.get("expiresAtMonotonic") or 0) <= now:
        raise GoogleSheetHubError(
            "oauth_state_expired",
            "Google authorization expired. Please start the connection again.",
            400,
        )
    oauth_error = _single_query_value(query, "error")
    code = _single_query_value(query, "code")
    if oauth_error:
        raise GoogleSheetHubError(
            "oauth_authorization_denied",
            "Google authorization was not completed.",
            400,
        )
    if not code or len(code) > 4096 or any(ord(character) < 32 for character in code):
        raise GoogleSheetHubError(
            "oauth_code_invalid",
            "Google authorization did not return a valid one-time code.",
            400,
        )
    verifier = str(flow.get("verifier") or "")
    redirect_uri = str(flow.get("redirectUri") or "")
    client_id = str(flow.get("clientId") or "").strip()
    client_secret = str(flow.get("clientSecret") or "").strip()
    if not client_id:
        raise GoogleSheetHubError(
            "oauth_client_not_configured",
            "Google OAuth Client ID is not configured in the Local Runner.",
            503,
        )
    form = {
        "client_id": client_id,
        "code": code,
        "code_verifier": verifier,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    if client_secret:
        form["client_secret"] = client_secret
    request = Request(
        GOOGLE_TOKEN_URL,
        data=urlencode(form).encode("utf-8"),
        headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with open_url(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            result = _oauth_token_response(response)
    except HTTPError as error:
        raise _classified_oauth_http_error(error) from error
    except (URLError, TimeoutError, OSError) as error:
        raise GoogleSheetHubError(
            "oauth_unavailable",
            "Google OAuth token service is unavailable.",
            502,
        ) from error
    refresh_token = str(result.get("refresh_token") or "").strip()
    if not refresh_token:
        raise GoogleSheetHubError(
            "oauth_refresh_token_missing",
            "Google did not return an offline authorization. Please reconnect and grant access.",
            502,
        )
    granted_scopes = {
        value.strip()
        for value in str(result.get("scope") or "").split()
        if value.strip()
    }
    if SHEETS_SCOPE not in granted_scopes:
        raise GoogleSheetHubError(
            "oauth_scope_missing",
            "Google authorization did not grant the required Google Sheets scope.",
            403,
        )
    try:
        google_oauth_store.save_refresh_token(refresh_token)
    except google_oauth_store.SecureStoreError as error:
        raise GoogleSheetHubError(error.code, error.message, 503) from error
    return {
        "ok": True,
        "kind": "google_oauth_connected",
        "auth": google_oauth_status(environ),
        "messageTh": "เชื่อมต่อ Google Sheets สำเร็จแล้ว สามารถกลับไปยัง Agent HQ ได้",
    }


def disconnect_google_oauth(environ: dict[str, str] | None = None) -> dict:
    with _OAUTH_FLOW_LOCK:
        _PENDING_OAUTH_FLOWS.clear()
    try:
        removed = google_oauth_store.delete_refresh_token()
    except google_oauth_store.SecureStoreError as error:
        raise GoogleSheetHubError(error.code, error.message, 503) from error
    auth = google_oauth_status(environ)
    return {
        "ok": True,
        "kind": "google_oauth_disconnected",
        "storedCredentialRemoved": removed,
        "auth": auth,
        "messageTh": (
            "ลบสิทธิ์ Google ที่บันทึกในเครื่องแล้ว"
            if not auth.get("connected")
            else "ลบสิทธิ์ที่บันทึกแล้ว แต่ Local Runner ยังใช้สิทธิ์จาก Environment อยู่"
        ),
    }


def _read_json_response(response) -> dict:
    payload = response.read(MAX_RESPONSE_BYTES + 1)
    if len(payload) > MAX_RESPONSE_BYTES:
        raise GoogleSheetHubError("response_too_large", "Google Sheets response exceeded the size limit.", 502)
    try:
        decoded = json.loads(payload.decode("utf-8")) if payload else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GoogleSheetHubError("invalid_google_response", "Google Sheets returned an invalid response.", 502) from error
    if not isinstance(decoded, dict):
        raise GoogleSheetHubError("invalid_google_response", "Google Sheets returned an invalid response.", 502)
    return decoded


def _safe_http_error(error: HTTPError, *, write_started: bool = False) -> GoogleSheetHubError:
    if error.code == 401:
        return GoogleSheetHubError("auth_expired", "Google Sheets authorization is missing or expired.", 401)
    if error.code == 403:
        return GoogleSheetHubError("permission_denied", "Google Sheet permission or OAuth scope is insufficient.", 403)
    if error.code == 404:
        return GoogleSheetHubError("spreadsheet_not_found", "Google Sheet or requested tab was not found.", 404)
    if error.code == 429:
        return GoogleSheetHubError("rate_limited", "Google Sheets rate limit was reached.", 429, write_started)
    if write_started and error.code >= 500:
        return GoogleSheetHubError(
            "write_unknown",
            "Google Sheets did not return a conclusive write result.",
            502,
            True,
        )
    # Deterministic 4xx validation errors mean Google rejected the request;
    # they are not ambiguous writes and must not enter an infinite retry loop.
    return GoogleSheetHubError("google_api_error", "Google Sheets API request failed.", 502, False)


def access_token(
    environ: dict[str, str] | None = None,
    *,
    open_url: Callable = urlopen,
) -> str:
    env = environ if isinstance(environ, dict) else os.environ
    direct = str(env.get("METAFX_GOOGLE_SHEETS_ACCESS_TOKEN") or "").strip()
    if direct:
        return direct
    refresh_token = str(env.get("METAFX_GOOGLE_OAUTH_REFRESH_TOKEN") or "").strip()
    if refresh_token:
        # An explicit environment refresh token remains paired with its
        # explicit environment client for backwards compatibility.
        client = _environment_oauth_client(env)
    else:
        client = oauth_client_configuration(environ)
        try:
            refresh_token = str(google_oauth_store.load_refresh_token() or "").strip()
        except google_oauth_store.SecureStoreError as error:
            raise GoogleSheetHubError(error.code, error.message, 503) from error
    client_id = str(client.get("clientId") or "").strip()
    client_secret = str(client.get("clientSecret") or "").strip()
    if not (client_id and refresh_token):
        raise GoogleSheetHubError(
            "auth_required",
            "Google Sheets credential is not configured in the Local Runner.",
            503,
        )
    form = {
        "client_id": client_id,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    if client_secret:
        form["client_secret"] = client_secret
    body = urlencode(form).encode("utf-8")
    request = Request(
        GOOGLE_TOKEN_URL,
        data=body,
        headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with open_url(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            result = _read_json_response(response)
    except HTTPError as error:
        if error.code in {400, 401, 429} or error.code >= 500:
            raise _classified_oauth_http_error(error, refresh_grant=True) from error
        raise _safe_http_error(error) from error
    except (URLError, TimeoutError, OSError) as error:
        raise GoogleSheetHubError("auth_unavailable", "Google OAuth token service is unavailable.", 502) from error
    token = str(result.get("access_token") or "").strip()
    if not token:
        raise GoogleSheetHubError("auth_invalid_response", "Google OAuth did not return an access token.", 502)
    return token


def api_request(
    sheet_id: str,
    suffix: str = "",
    *,
    method: str = "GET",
    query: dict[str, object] | None = None,
    body: dict | None = None,
    environ: dict[str, str] | None = None,
    open_url: Callable = urlopen,
) -> dict:
    if not SAFE_SHEET_ID.fullmatch(str(sheet_id or "")):
        raise GoogleSheetHubError("invalid_sheet_id", "Google Sheet ID is invalid.", 422)
    token = access_token(environ, open_url=open_url)
    url = f"{GOOGLE_API_ROOT}/{quote(sheet_id, safe='')}" + str(suffix or "")
    if query:
        url += "?" + urlencode({key: value for key, value in query.items() if value is not None})
    payload = None
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    if body is not None:
        payload = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=payload, headers=headers, method=method)
    write_started = method.upper() not in {"GET", "HEAD"}
    try:
        with open_url(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            return _read_json_response(response)
    except HTTPError as error:
        raise _safe_http_error(error, write_started=write_started) from error
    except (URLError, TimeoutError, OSError) as error:
        raise GoogleSheetHubError(
            "write_unknown" if write_started else "google_api_unavailable",
            "Google Sheets request could not be completed.",
            502,
            write_started,
        ) from error


def canonical_header(value: object) -> str:
    return str(value or "").strip().split("/", 1)[0].strip()


def quoted_tab(tab_name: str) -> str:
    return "'" + str(tab_name).replace("'", "''") + "'"


def read_values(
    sheet_id: str,
    tab_name: str,
    cell_range: str,
    *,
    environ: dict[str, str] | None = None,
    open_url: Callable = urlopen,
) -> list[list[object]]:
    a1 = f"{quoted_tab(tab_name)}!{cell_range}"
    result = api_request(
        sheet_id,
        f"/values/{quote(a1, safe='')}",
        query={"majorDimension": "ROWS", "valueRenderOption": "FORMATTED_VALUE"},
        environ=environ,
        open_url=open_url,
    )
    rows = result.get("values")
    return rows if isinstance(rows, list) else []


def inspect_tabs(
    sheet_id: str,
    tab_contracts: dict[str, dict],
    *,
    environ: dict[str, str] | None = None,
    open_url: Callable = urlopen,
) -> dict:
    metadata = api_request(
        sheet_id,
        query={"fields": "spreadsheetId,properties.title,sheets.properties(sheetId,title,gridProperties)"},
        environ=environ,
        open_url=open_url,
    )
    available = {
        str(((item.get("properties") or {}).get("title")) or "")
        for item in (metadata.get("sheets") if isinstance(metadata.get("sheets"), list) else [])
        if isinstance(item, dict)
    }
    checks: dict[str, dict] = {}
    all_ready = True
    for consumer_id, contract in tab_contracts.items():
        tab_name = str(contract.get("tabName") or "")
        required = {str(value) for value in (contract.get("requiredHeaders") or []) if str(value)}
        exact_headers = [
            str(value) for value in (contract.get("exactHeaders") or []) if str(value)
        ]
        if tab_name not in available:
            checks[consumer_id] = {"tabName": tab_name, "status": "missing_tab", "readReady": False}
            all_ready = False
            continue
        rows = read_values(sheet_id, tab_name, "1:1", environ=environ, open_url=open_url)
        headers = [canonical_header(value) for value in (rows[0] if rows else [])]
        duplicate_headers = sorted(
            {header for header in headers if header and headers.count(header) > 1}
        )
        missing = sorted(required - set(headers))
        order_mismatch = bool(
            exact_headers
            and (
                len(headers) != len(exact_headers)
                or headers != exact_headers
            )
        )
        ready = bool(headers) and not missing and not duplicate_headers and not order_mismatch
        key_header = str(contract.get("keyHeader") or "")
        key_column = (
            _column_letter(headers.index(key_header) + 1)
            if ready and key_header in headers
            else None
        )
        checks[consumer_id] = {
            "tabName": tab_name,
            "status": "ready" if ready else "schema_mismatch",
            "readReady": ready,
            "columnCount": len(headers),
            "keyHeader": key_header or None,
            "keyColumn": key_column,
            "missingHeaders": missing,
            "duplicateHeaders": duplicate_headers,
            "headerOrderMismatch": order_mismatch,
        }
        all_ready = all_ready and ready
    return {
        "title": str(((metadata.get("properties") or {}).get("title")) or "")[:160] or None,
        "consumers": checks,
        "readReady": all_ready,
        "writeReady": all_ready,
    }


def probe_tabs(
    sheet_id: str,
    tab_contracts: dict[str, dict],
    *,
    max_rows: int = 10000,
    environ: dict[str, str] | None = None,
    open_url: Callable = urlopen,
) -> dict:
    """Verify schema and perform a bounded, read-only key-column probe per tab.

    The returned evidence contains counts and ranges only.  Cell values and all
    OAuth/service-account material stay inside the Backend process.
    """

    if max_rows < 2 or max_rows > 10000:
        raise GoogleSheetHubError(
            "invalid_probe_limit",
            "Google Sheet probe row limit is invalid.",
            422,
        )
    inspection = inspect_tabs(
        sheet_id,
        tab_contracts,
        environ=environ,
        open_url=open_url,
    )
    checks = (
        inspection.get("consumers")
        if isinstance(inspection.get("consumers"), dict)
        else {}
    )
    all_ready = bool(inspection.get("readReady"))
    for consumer_id, contract in tab_contracts.items():
        check = checks.get(consumer_id) if isinstance(checks.get(consumer_id), dict) else {}
        if check.get("readReady") is not True:
            check["probeReady"] = False
            check["rowCount"] = 0
            check["probeEvidence"] = {
                "kind": "key_column_read",
                "range": None,
                "confirmed": False,
            }
            checks[consumer_id] = check
            all_ready = False
            continue
        tab_name = str(contract.get("tabName") or "")
        key_column = str(check.get("keyColumn") or "")
        if not key_column:
            check.update({
                "status": "schema_mismatch",
                "readReady": False,
                "probeReady": False,
                "rowCount": 0,
                "probeEvidence": {
                    "kind": "key_column_read",
                    "range": None,
                    "confirmed": False,
                },
            })
            checks[consumer_id] = check
            all_ready = False
            continue
        probe_range = f"{key_column}2:{key_column}{max_rows}"
        try:
            key_rows = read_values(
                sheet_id,
                tab_name,
                probe_range,
                environ=environ,
                open_url=open_url,
            )
        except GoogleSheetHubError as error:
            check.update({
                "status": error.code,
                "readReady": False,
                "probeReady": False,
                "rowCount": 0,
                "probeEvidence": {
                    "kind": "key_column_read",
                    "range": probe_range,
                    "confirmed": False,
                    "errorCode": error.code,
                },
            })
            checks[consumer_id] = check
            all_ready = False
            continue
        keys = [
            str(row[0] or "").strip()
            for row in key_rows
            if isinstance(row, list) and row and str(row[0] or "").strip()
        ]
        duplicate_key_count = max(0, len(keys) - len(set(keys)))
        probe_ready = duplicate_key_count == 0
        check.update({
            "status": "ready" if probe_ready else "duplicate_key_conflict",
            "readReady": probe_ready,
            "probeReady": probe_ready,
            "rowCount": len(keys),
            "duplicateKeyCount": duplicate_key_count,
            "probeEvidence": {
                "kind": "key_column_read",
                "range": probe_range,
                "confirmed": probe_ready,
                "rowsScanned": len(key_rows),
                "nonEmptyKeys": len(keys),
                "duplicateKeyCount": duplicate_key_count,
            },
        })
        checks[consumer_id] = check
        all_ready = all_ready and probe_ready
    return {
        **inspection,
        "consumers": checks,
        "readReady": all_ready,
        "writeReady": all_ready,
        "probeReady": all_ready,
    }


def upsert_row(
    sheet_id: str,
    tab_name: str,
    key_header: str,
    key_value: str,
    row_by_header: dict[str, object],
    *,
    environ: dict[str, str] | None = None,
    open_url: Callable = urlopen,
    max_rows: int = 10000,
) -> dict:
    header_rows = read_values(
        sheet_id,
        tab_name,
        "1:1",
        environ=environ,
        open_url=open_url,
    )
    if not header_rows:
        raise GoogleSheetHubError("schema_mismatch", "Google Sheet tab has no header row.", 409)
    raw_headers = [str(value or "").strip() for value in header_rows[0]]
    headers = [canonical_header(value) for value in raw_headers]
    duplicate_headers = sorted({header for header in headers if header and headers.count(header) > 1})
    if duplicate_headers:
        raise GoogleSheetHubError("schema_mismatch", "Google Sheet has duplicate canonical column names.", 409)
    if key_header not in headers:
        raise GoogleSheetHubError("schema_mismatch", "Google Sheet key column is missing.", 409)
    unknown = sorted(set(row_by_header) - set(headers))
    if unknown:
        raise GoogleSheetHubError("schema_mismatch", "Google Sheet columns do not match the configured schema.", 409)
    key_index = headers.index(key_header)
    key_column = _column_letter(key_index + 1)
    key_rows = read_values(
        sheet_id,
        tab_name,
        f"{key_column}2:{key_column}{max_rows}",
        environ=environ,
        open_url=open_url,
    )
    matching_rows: list[int] = []
    for index, row in enumerate(key_rows, start=2):
        if row and str(row[0] or "").strip() == str(key_value):
            matching_rows.append(index)
    if len(matching_rows) > 1:
        raise GoogleSheetHubError("duplicate_key_conflict", "Google Sheet contains more than one row for the same record key.", 409)
    target_row = matching_rows[0] if matching_rows else len(key_rows) + 2
    if target_row > max_rows:
        raise GoogleSheetHubError("sheet_capacity_reached", "Google Sheet reached the configured row safety limit.", 409)
    end_column = _column_letter(len(headers))

    supplied_key = row_by_header.get(key_header)
    if supplied_key is not None and str(supplied_key) != str(key_value):
        raise GoogleSheetHubError("key_mismatch", "Google Sheet row key does not match the upsert key.", 409)

    # Only the fields present in row_by_header are owned by this adapter.  The
    # record key is always owned so a newly allocated row remains idempotent.
    # Updating a whole row from FORMATTED_VALUE read-back would replace formulas
    # with their displayed values and blank user-managed columns.
    owned_by_index = {
        headers.index(header): str(value if value is not None else "")
        for header, value in row_by_header.items()
    }
    owned_by_index[key_index] = str(key_value)
    owned_indexes = sorted(owned_by_index)

    # Coalesce adjacent owned cells into compact ValueRanges while leaving every
    # formula/manual column outside those ranges untouched.
    data: list[dict] = []
    range_start = owned_indexes[0]
    range_end = range_start
    for column_index in owned_indexes[1:] + [None]:
        if column_index is not None and column_index == range_end + 1:
            range_end = column_index
            continue
        start_column = _column_letter(range_start + 1)
        stop_column = _column_letter(range_end + 1)
        a1 = f"{quoted_tab(tab_name)}!{start_column}{target_row}:{stop_column}{target_row}"
        data.append(
            {
                "range": a1,
                "majorDimension": "ROWS",
                "values": [[owned_by_index[index] for index in range(range_start, range_end + 1)]],
            }
        )
        if column_index is not None:
            range_start = column_index
            range_end = column_index

    result = api_request(
        sheet_id,
        "/values:batchUpdate",
        method="POST",
        body={
            "valueInputOption": "RAW",
            "includeValuesInResponse": True,
            "data": data,
        },
        environ=environ,
        open_url=open_url,
    )
    responses = result.get("responses") if isinstance(result.get("responses"), list) else []
    confirmed = (
        len(responses) == len(data)
        and all(
            isinstance(response, dict) and int(response.get("updatedRows") or 0) == 1
            for response in responses
        )
    )
    if not confirmed:
        raise GoogleSheetHubError("write_verification_failed", "Google Sheets did not confirm exactly one updated row.", 502, True)
    try:
        readback = read_values(
            sheet_id,
            tab_name,
            f"A{target_row}:{end_column}{target_row}",
            environ=environ,
            open_url=open_url,
        )
    except GoogleSheetHubError as error:
        # The batchUpdate response already confirmed one updated row.  If the
        # independent read-back cannot complete, the adapter must not turn that
        # into a terminal read error: the external write may be durable and an
        # idempotent retry by the same record key is the only safe recovery.
        raise GoogleSheetHubError(
            "write_unknown",
            "Google Sheet write completed but read-back verification could not be completed.",
            502,
            True,
        ) from error
    observed = [str(value or "") for value in (readback[0] if readback else [])]
    observed.extend([""] * (len(headers) - len(observed)))
    if any(observed[index] != value for index, value in owned_by_index.items()):
        raise GoogleSheetHubError("write_verification_failed", "Google Sheet read-back did not match the submitted row.", 502, True)
    return {"rowNumber": target_row, "updatedRows": 1, "readBackVerified": True}


def _column_letter(number: int) -> str:
    if number < 1 or number > 702:
        raise GoogleSheetHubError("schema_too_wide", "Google Sheet schema exceeds the supported width.", 422)
    result = ""
    value = number
    while value:
        value, remainder = divmod(value - 1, 26)
        result = chr(65 + remainder) + result
    return result
