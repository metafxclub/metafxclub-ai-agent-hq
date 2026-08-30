from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import threading
import unittest
from contextlib import ExitStack, redirect_stderr
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
LOCAL_RUNNER = ROOT / "backend" / "local-runner"
HUB_PATH = LOCAL_RUNNER / "google_sheet_hub.py"
BRIDGE_PATH = LOCAL_RUNNER / "bridge_server.py"
CONTRACT_PATH = ROOT / "contracts" / "bridge" / "bridge-contract.json"
SETUP_DOC_PATH = ROOT / "docs" / "research-sheet-hub-setup-th.md"
CLIENT_ENV = {"METAFX_GOOGLE_OAUTH_CLIENT_ID": "desktop-client-id.apps.googleusercontent.com"}
CALLBACK_PATH = "/api/props/mission_strategy_table/research-sheet/auth/callback"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    runner = str(LOCAL_RUNNER)
    added = runner not in sys.path
    if added:
        sys.path.insert(0, runner)
    try:
        spec.loader.exec_module(module)
    finally:
        if added:
            sys.path.remove(runner)
    return module


class FakeJsonResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, _limit: int = -1) -> bytes:
        return json.dumps(self.payload, separators=(",", ":")).encode("utf-8")


class RecordingReadBody(io.BytesIO):
    def __init__(self, payload: bytes):
        super().__init__(payload)
        self.read_sizes: list[int] = []

    def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        if size < 0:
            raise AssertionError("OAuth provider error bodies must never be read without a bound")
        return super().read(size)


class FakeSecureStore:
    def __init__(self) -> None:
        self.refresh_token: str | None = None
        self.saved: list[str] = []
        self.delete_calls = 0

    def save_refresh_token(self, refresh_token: str, **_kwargs) -> None:
        self.refresh_token = refresh_token
        self.saved.append(refresh_token)

    def load_refresh_token(self, **_kwargs) -> str | None:
        return self.refresh_token

    def delete_refresh_token(self, **_kwargs) -> bool:
        self.delete_calls += 1
        removed = self.refresh_token is not None
        self.refresh_token = None
        return removed

    def status(self, **_kwargs) -> dict:
        return {
            "available": True,
            "stored": self.refresh_token is not None,
            "status": "ready" if self.refresh_token is not None else "empty",
        }


def authorization_query(result: dict) -> dict[str, list[str]]:
    return parse_qs(urlsplit(result["authorizationUrl"]).query, keep_blank_values=True)


def oauth_http_error(
    status: int,
    provider_error: str,
    description: str,
    *,
    extra: dict | None = None,
) -> HTTPError:
    payload = {
        "error": provider_error,
        "error_description": description,
        "error_uri": "https://provider.invalid/help?token=PROVIDER_URI_TOKEN_MARKER",
        "code": "PROVIDER_BODY_CODE_MARKER",
        "state": "PROVIDER_BODY_STATE_MARKER",
        "access_token": "PROVIDER_BODY_ACCESS_TOKEN_MARKER",
        "refresh_token": "PROVIDER_BODY_REFRESH_TOKEN_MARKER",
    }
    if isinstance(extra, dict):
        payload.update(extra)
    return HTTPError(
        "https://oauth2.googleapis.com/token",
        status,
        "PROVIDER_HTTP_REASON_MARKER",
        {"X-Provider-Debug": "PROVIDER_HEADER_SECRET_MARKER"},
        io.BytesIO(json.dumps(payload).encode("utf-8")),
    )


def assert_no_secret_fields(test: unittest.TestCase, payload: object) -> None:
    forbidden = {
        "accesstoken",
        "access_token",
        "authorizationcode",
        "clientsecret",
        "client_secret",
        "codeverifier",
        "code_verifier",
        "pkceverifier",
        "refreshtoken",
        "refresh_token",
        "securestorepayload",
    }

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                test.assertNotIn(str(key).replace("-", "").lower(), forbidden)
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)


class GoogleOAuthModuleSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.hub = load_module(HUB_PATH, "google_oauth_security_hub")

    def setUp(self) -> None:
        self.hub._PENDING_OAUTH_FLOWS.clear()
        self.store = FakeSecureStore()
        self.stack = ExitStack()
        for name in ("save_refresh_token", "load_refresh_token", "delete_refresh_token", "status"):
            self.stack.enter_context(
                patch.object(self.hub.google_oauth_store, name, getattr(self.store, name))
            )
        self.redirect_uri = f"http://127.0.0.1:43191{CALLBACK_PATH}"

    def tearDown(self) -> None:
        self.hub._PENDING_OAUTH_FLOWS.clear()
        self.stack.close()

    def start(self, *, now: float = 100.0, hub=None) -> tuple[dict, dict[str, list[str]]]:
        module = hub or self.hub
        result = module.start_google_oauth(
            self.redirect_uri,
            CLIENT_ENV,
            now_monotonic=now,
        )
        return result, authorization_query(result)

    def test_start_uses_exact_loopback_pkce_s256_and_offline_consent(self) -> None:
        result, query = self.start()
        parsed = urlsplit(result["authorizationUrl"])
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.hostname, "accounts.google.com")
        self.assertEqual(query["redirect_uri"], [self.redirect_uri])
        self.assertEqual(query["response_type"], ["code"])
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertEqual(query["access_type"], ["offline"])
        self.assertEqual(query["prompt"], ["consent"])
        self.assertEqual(len(query["state"]), 1)
        state = query["state"][0]
        flow = self.hub._PENDING_OAUTH_FLOWS[state]
        verifier = flow["verifier"]
        self.assertGreaterEqual(len(verifier), 43)
        self.assertLessEqual(len(verifier), 128)
        expected_challenge = self.hub._base64url(
            hashlib.sha256(verifier.encode("ascii")).digest()
        )
        self.assertEqual(query["code_challenge"], [expected_challenge])
        self.assertNotIn(verifier, json.dumps(result, sort_keys=True))
        self.assertNotIn("codeVerifier", result)
        assert_no_secret_fields(self, result)

    def test_redirect_must_be_exact_127_loopback_callback(self) -> None:
        invalid = (
            f"http://localhost:43191{CALLBACK_PATH}",
            f"http://127.0.0.1:43191{CALLBACK_PATH}/extra",
            f"https://127.0.0.1:43191{CALLBACK_PATH}",
            f"http://127.0.0.1:43191{CALLBACK_PATH}?next=1",
        )
        for redirect_uri in invalid:
            with self.subTest(redirect_uri=redirect_uri):
                with self.assertRaises(self.hub.GoogleSheetHubError) as raised:
                    self.hub.start_google_oauth(redirect_uri, CLIENT_ENV)
                self.assertEqual(raised.exception.code, "invalid_oauth_redirect")

    def test_state_is_consumed_before_failed_token_exchange(self) -> None:
        _result, query = self.start()
        callback = {"state": query["state"], "code": ["ONE_TIME_CODE_MARKER"]}
        opener = Mock(side_effect=URLError("offline"))
        with self.assertRaises(self.hub.GoogleSheetHubError) as first:
            self.hub.complete_google_oauth(
                callback,
                CLIENT_ENV,
                open_url=opener,
                now_monotonic=101.0,
            )
        self.assertEqual(first.exception.code, "oauth_unavailable")
        with self.assertRaises(self.hub.GoogleSheetHubError) as replay:
            self.hub.complete_google_oauth(callback, CLIENT_ENV, open_url=opener)
        self.assertEqual(replay.exception.code, "oauth_state_invalid")
        opener.assert_called_once()

    def test_denied_state_is_also_one_use(self) -> None:
        _result, query = self.start()
        callback = {"state": query["state"], "error": ["access_denied"]}
        with self.assertRaises(self.hub.GoogleSheetHubError) as denied:
            self.hub.complete_google_oauth(callback, CLIENT_ENV, now_monotonic=101.0)
        self.assertEqual(denied.exception.code, "oauth_authorization_denied")
        with self.assertRaises(self.hub.GoogleSheetHubError) as replay:
            self.hub.complete_google_oauth(callback, CLIENT_ENV)
        self.assertEqual(replay.exception.code, "oauth_state_invalid")

    def test_expired_state_is_consumed_without_network_exchange(self) -> None:
        _result, query = self.start(now=10.0)
        callback = {"state": query["state"], "code": ["EXPIRED_CODE_MARKER"]}
        opener = Mock()
        expired_at = 10.0 + self.hub.GOOGLE_OAUTH_FLOW_TTL_SECONDS + 0.001
        with self.assertRaises(self.hub.GoogleSheetHubError) as expired:
            self.hub.complete_google_oauth(
                callback,
                CLIENT_ENV,
                open_url=opener,
                now_monotonic=expired_at,
            )
        self.assertEqual(expired.exception.code, "oauth_state_expired")
        opener.assert_not_called()
        with self.assertRaises(self.hub.GoogleSheetHubError) as replay:
            self.hub.complete_google_oauth(callback, CLIENT_ENV, open_url=opener)
        self.assertEqual(replay.exception.code, "oauth_state_invalid")

    def test_exact_expiry_boundary_is_rejected(self) -> None:
        _result, query = self.start(now=25.0)
        callback = {"state": query["state"], "code": ["BOUNDARY_CODE_MARKER"]}
        opener = Mock()
        with self.assertRaises(self.hub.GoogleSheetHubError) as expired:
            self.hub.complete_google_oauth(
                callback,
                CLIENT_ENV,
                open_url=opener,
                now_monotonic=25.0 + self.hub.GOOGLE_OAUTH_FLOW_TTL_SECONDS,
            )
        self.assertEqual(expired.exception.code, "oauth_state_expired")
        opener.assert_not_called()

    def test_token_exchange_binds_pkce_and_never_returns_secrets(self) -> None:
        _result, query = self.start()
        state = query["state"][0]
        verifier = self.hub._PENDING_OAUTH_FLOWS[state]["verifier"]
        code = "AUTHORIZATION_CODE_MARKER"
        refresh_token = "REFRESH_TOKEN_MARKER"
        captured: dict[str, object] = {}

        def open_token(request: Request, timeout: int):
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            captured["form"] = parse_qs(request.data.decode("utf-8"))
            return FakeJsonResponse(
                {
                    "access_token": "ACCESS_TOKEN_MARKER",
                    "refresh_token": refresh_token,
                    "scope": self.hub.SHEETS_SCOPE,
                }
            )

        response = self.hub.complete_google_oauth(
            {"state": [state], "code": [code]},
            CLIENT_ENV,
            open_url=open_token,
            now_monotonic=101.0,
        )
        form = captured["form"]
        self.assertEqual(form["code"], [code])
        self.assertEqual(form["code_verifier"], [verifier])
        self.assertEqual(form["redirect_uri"], [self.redirect_uri])
        self.assertEqual(form["grant_type"], ["authorization_code"])
        self.assertNotIn("client_secret", form)
        self.assertEqual(self.store.saved, [refresh_token])
        serialized = json.dumps(response, sort_keys=True)
        for secret in (code, verifier, refresh_token, "ACCESS_TOKEN_MARKER"):
            self.assertNotIn(secret, serialized)
        assert_no_secret_fields(self, response)

    def test_http_error_classification_is_allowlisted_and_provider_details_never_escape(self) -> None:
        allowlisted = {
            "oauth_invalid_client",
            "oauth_client_secret_required",
            "oauth_code_invalid_or_expired",
            "oauth_redirect_mismatch",
            "oauth_scope_missing",
            "oauth_invalid_request",
            "oauth_authorization_denied",
            "oauth_rate_limited",
            "oauth_unavailable",
            "oauth_exchange_rejected",
        }
        generic_description = "PROVIDER_DESCRIPTION_SECRET_MARKER"
        cases = (
            (401, "invalid_client", generic_description, "oauth_invalid_client"),
            (400, "unauthorized_client", generic_description, "oauth_invalid_client"),
            (400, "invalid_grant", generic_description, "oauth_code_invalid_or_expired"),
            (400, "redirect_uri_mismatch", generic_description, "oauth_redirect_mismatch"),
            (400, "invalid_scope", generic_description, "oauth_scope_missing"),
            (400, "invalid_request", generic_description, "oauth_invalid_request"),
            (
                400,
                "invalid_request",
                "client_secret is missing. PROVIDER_CLIENT_SECRET_DESCRIPTION_MARKER",
                "oauth_client_secret_required",
            ),
            (400, "access_denied", generic_description, "oauth_authorization_denied"),
            (400, "rate_limit_exceeded", generic_description, "oauth_rate_limited"),
            (400, "slow_down", generic_description, "oauth_rate_limited"),
            (429, "invalid_grant", generic_description, "oauth_rate_limited"),
            (500, "invalid_client", generic_description, "oauth_unavailable"),
            (503, "invalid_grant", generic_description, "oauth_unavailable"),
            (418, "PROVIDER_CONTROLLED_KIND_MARKER", generic_description, "oauth_exchange_rejected"),
        )
        provider_markers = (
            "PROVIDER_CONTROLLED_KIND_MARKER",
            "PROVIDER_DESCRIPTION_SECRET_MARKER",
            "PROVIDER_CLIENT_SECRET_DESCRIPTION_MARKER",
            "PROVIDER_URI_TOKEN_MARKER",
            "PROVIDER_BODY_CODE_MARKER",
            "PROVIDER_BODY_STATE_MARKER",
            "PROVIDER_BODY_ACCESS_TOKEN_MARKER",
            "PROVIDER_BODY_REFRESH_TOKEN_MARKER",
            "PROVIDER_HTTP_REASON_MARKER",
            "PROVIDER_HEADER_SECRET_MARKER",
        )
        for index, (http_status, provider_error, description, expected_kind) in enumerate(cases):
            with self.subTest(
                http_status=http_status,
                provider_error=provider_error,
                expected_kind=expected_kind,
            ):
                started_at = 1000.0 + (index * 20.0)
                _result, query = self.start(now=started_at)
                callback = {
                    "state": query["state"],
                    "code": [f"CALLBACK_CODE_SECRET_MARKER_{index}"],
                }
                opener = Mock(
                    side_effect=oauth_http_error(
                        http_status,
                        provider_error,
                        description,
                    )
                )
                provider_response = opener.side_effect
                with self.assertRaises(self.hub.GoogleSheetHubError) as rejected:
                    self.hub.complete_google_oauth(
                        callback,
                        CLIENT_ENV,
                        open_url=opener,
                        now_monotonic=started_at + 1.0,
                    )
                self.assertEqual(rejected.exception.code, expected_kind)
                self.assertIn(rejected.exception.code, allowlisted)
                self.assertTrue(provider_response.fp.closed)
                safe_exception = f"{rejected.exception.code}\n{rejected.exception}"
                for marker in provider_markers + (callback["code"][0],):
                    self.assertNotIn(marker, safe_exception)
                self.assertEqual(self.store.saved, [])
                with self.assertRaises(self.hub.GoogleSheetHubError) as replay:
                    self.hub.complete_google_oauth(
                        callback,
                        CLIENT_ENV,
                        open_url=opener,
                    )
                self.assertEqual(replay.exception.code, "oauth_state_invalid")
                opener.assert_called_once()

    def test_malformed_and_oversized_oauth_error_bodies_fail_to_generic_kind(self) -> None:
        error_bodies = (
            b"not-json PROVIDER_MALFORMED_DESCRIPTION_MARKER",
            b'["invalid_client", "PROVIDER_LIST_DESCRIPTION_MARKER"]',
            b"\xff\xfePROVIDER_INVALID_UTF8_MARKER",
            (
                b'{"error":"invalid_client","error_description":"'
                + b"X" * (self.hub.MAX_OAUTH_ERROR_RESPONSE_BYTES + 1024)
                + b'PROVIDER_OVERSIZE_SECRET_MARKER"}'
            ),
        )
        for index, body in enumerate(error_bodies):
            with self.subTest(index=index, byte_count=len(body)):
                started_at = 2000.0 + (index * 20.0)
                _result, query = self.start(now=started_at)
                callback_code = f"MALFORMED_CALLBACK_CODE_MARKER_{index}"
                error = HTTPError(
                    self.hub.GOOGLE_TOKEN_URL,
                    400,
                    "PROVIDER_MALFORMED_REASON_MARKER",
                    {},
                    io.BytesIO(body),
                )
                with self.assertRaises(self.hub.GoogleSheetHubError) as rejected:
                    self.hub.complete_google_oauth(
                        {"state": query["state"], "code": [callback_code]},
                        CLIENT_ENV,
                        open_url=Mock(side_effect=error),
                        now_monotonic=started_at + 1.0,
                    )
                self.assertEqual(rejected.exception.code, "oauth_exchange_rejected")
                safe_exception = f"{rejected.exception.code}\n{rejected.exception}"
                for marker in (
                    callback_code,
                    "PROVIDER_MALFORMED_DESCRIPTION_MARKER",
                    "PROVIDER_LIST_DESCRIPTION_MARKER",
                    "PROVIDER_INVALID_UTF8_MARKER",
                    "PROVIDER_OVERSIZE_SECRET_MARKER",
                    "PROVIDER_MALFORMED_REASON_MARKER",
                ):
                    self.assertNotIn(marker, safe_exception)
                self.assertEqual(self.store.saved, [])

    def test_oauth_http_error_parser_reads_only_one_bounded_envelope(self) -> None:
        body = RecordingReadBody(
            json.dumps(
                {
                    "error": "invalid_client",
                    "error_description": "BOUNDED_READ_DESCRIPTION_MARKER",
                }
            ).encode("utf-8")
        )
        error = HTTPError(
            self.hub.GOOGLE_TOKEN_URL,
            401,
            "BOUNDED_READ_REASON_MARKER",
            {},
            body,
        )
        try:
            self.assertEqual(
                self.hub._allowlisted_provider_oauth_error(error),
                "invalid_client",
            )
            self.assertEqual(
                body.read_sizes,
                [self.hub.MAX_OAUTH_ERROR_RESPONSE_BYTES + 1],
            )
        finally:
            error.close()

    def test_missing_sheets_scope_never_persists_refresh_token_and_consumes_state(self) -> None:
        _result, query = self.start()
        callback = {"state": query["state"], "code": ["WRONG_SCOPE_CODE_MARKER"]}
        opener = Mock(
            return_value=FakeJsonResponse(
                {
                    "access_token": "WRONG_SCOPE_ACCESS_MARKER",
                    "refresh_token": "WRONG_SCOPE_REFRESH_MARKER",
                    "scope": "openid email",
                }
            )
        )
        with self.assertRaises(self.hub.GoogleSheetHubError) as missing_scope:
            self.hub.complete_google_oauth(
                callback,
                CLIENT_ENV,
                open_url=opener,
                now_monotonic=101.0,
            )
        self.assertEqual(missing_scope.exception.code, "oauth_scope_missing")
        self.assertEqual(self.store.saved, [])
        with self.assertRaises(self.hub.GoogleSheetHubError) as replay:
            self.hub.complete_google_oauth(callback, CLIENT_ENV, open_url=opener)
        self.assertEqual(replay.exception.code, "oauth_state_invalid")
        opener.assert_called_once()

    def test_fake_secure_store_survives_fresh_module_instance(self) -> None:
        _result, query = self.start()
        self.hub.complete_google_oauth(
            {"state": query["state"], "code": ["RESTART_CODE_MARKER"]},
            CLIENT_ENV,
            open_url=lambda *_args, **_kwargs: FakeJsonResponse(
                {
                    "access_token": "SHORT_ACCESS",
                    "refresh_token": "DURABLE_REFRESH_MARKER",
                    "scope": self.hub.SHEETS_SCOPE,
                }
            ),
            now_monotonic=101.0,
        )
        restarted = load_module(HUB_PATH, "google_oauth_security_hub_restarted")
        status = restarted.credential_status(CLIENT_ENV)
        self.assertTrue(status["configured"])
        self.assertEqual(status["mode"], "oauth_refresh_stored")
        captured: dict[str, dict[str, list[str]]] = {}

        def open_refresh(request: Request, timeout: int):
            captured["form"] = parse_qs(request.data.decode("utf-8"))
            return FakeJsonResponse({"access_token": "RESTARTED_ACCESS_MARKER"})

        access = restarted.access_token(CLIENT_ENV, open_url=open_refresh)
        self.assertEqual(access, "RESTARTED_ACCESS_MARKER")
        self.assertEqual(captured["form"]["refresh_token"], ["DURABLE_REFRESH_MARKER"])

    def test_disconnect_clears_store_and_pending_flows_but_preserves_env_fallback(self) -> None:
        self.store.refresh_token = "STORED_REFRESH_MARKER"
        self.start()
        env = dict(CLIENT_ENV)
        env["METAFX_GOOGLE_SHEETS_ACCESS_TOKEN"] = "ENV_ACCESS_MARKER"
        response = self.hub.disconnect_google_oauth(env)
        self.assertIsNone(self.store.refresh_token)
        self.assertEqual(self.store.delete_calls, 1)
        self.assertEqual(self.hub._PENDING_OAUTH_FLOWS, {})
        self.assertTrue(response["auth"]["connected"])
        self.assertTrue(response["auth"]["environmentCredential"])
        self.assertEqual(response["auth"]["mode"], "access_token")
        self.assertNotIn("ENV_ACCESS_MARKER", json.dumps(response, sort_keys=True))
        assert_no_secret_fields(self, response)

    def test_environment_credentials_take_precedence_over_stored_refresh(self) -> None:
        self.store.refresh_token = "STORED_REFRESH_MARKER"
        direct_env = dict(CLIENT_ENV)
        direct_env["METAFX_GOOGLE_SHEETS_ACCESS_TOKEN"] = "DIRECT_ENV_ACCESS_MARKER"
        opener = Mock(side_effect=AssertionError("direct token must not call network"))
        self.assertEqual(
            self.hub.access_token(direct_env, open_url=opener),
            "DIRECT_ENV_ACCESS_MARKER",
        )
        opener.assert_not_called()

        refresh_env = dict(CLIENT_ENV)
        refresh_env["METAFX_GOOGLE_OAUTH_REFRESH_TOKEN"] = "ENV_REFRESH_MARKER"
        captured: dict[str, dict[str, list[str]]] = {}

        def open_refresh(request: Request, timeout: int):
            captured["form"] = parse_qs(request.data.decode("utf-8"))
            return FakeJsonResponse({"access_token": "ENV_REFRESH_ACCESS"})

        self.hub.access_token(refresh_env, open_url=open_refresh)
        self.assertEqual(captured["form"]["refresh_token"], ["ENV_REFRESH_MARKER"])


class GoogleOAuthSecureStoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.store_module = load_module(
            LOCAL_RUNNER / "google_oauth_store.py",
            "google_oauth_security_store",
        )

    def test_persisted_file_contains_only_protected_blob_and_can_reload(self) -> None:
        token = "PLAINTEXT_REFRESH_TOKEN_MARKER"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credentials" / "google.dpapi"
            with (
                patch.object(self.store_module, "_protect", return_value=b"fake-dpapi-ciphertext"),
                patch.object(self.store_module, "_unprotect", return_value=token.encode("utf-8")),
            ):
                self.store_module.save_refresh_token(token, path=path)
                persisted = path.read_bytes()
                self.assertTrue(persisted.startswith(self.store_module._STORE_MAGIC))
                self.assertNotIn(token.encode("utf-8"), persisted)
                self.assertEqual(self.store_module.load_refresh_token(path=path), token)
                self.assertTrue(self.store_module.delete_refresh_token(path=path))
                self.assertFalse(path.exists())


class GoogleOAuthBridgeSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module(BRIDGE_PATH, "google_oauth_security_bridge")

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp.name)
        self.stack = ExitStack()
        self.stack.enter_context(
            patch.object(self.bridge, "AUDIT_PATH", self.temp_path / "bridge-audit.jsonl")
        )
        self.stack.enter_context(
            patch.object(
                self.bridge,
                "DASHBOARD_WORKFLOW_SETTINGS_PATH",
                self.temp_path / "dashboard-workflow-settings.json",
            )
        )
        class JoinableBridgeHTTPServer(self.bridge.BridgeHTTPServer):
            # Production request threads are intentionally daemonized so a
            # broken browser tab cannot keep HQ alive during shutdown. Tests
            # must instead join every handler before deleting their temporary
            # audit/settings directory on Windows.
            daemon_threads = False
            block_on_close = True

        self.server = JoinableBridgeHTTPServer(
            ("127.0.0.1", 0),
            self.bridge.BridgeHandler,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        thread_stopped = False
        try:
            self.server.shutdown()
            self.thread.join(timeout=5)
            thread_stopped = not self.thread.is_alive()
        finally:
            try:
                # ThreadingMixIn.server_close waits for non-daemon request
                # handlers when block_on_close is true, so no request can
                # recreate a file while TemporaryDirectory is being removed.
                self.server.server_close()
            finally:
                self.stack.close()
                self.temp.cleanup()
        self.assertTrue(thread_stopped, "OAuth test server did not stop")

    def read_url(self, path: str) -> tuple[int, bytes]:
        try:
            with urlopen(self.base_url + path, timeout=3) as response:
                return response.status, response.read()
        except HTTPError as error:
            try:
                return error.code, error.read()
            finally:
                error.close()

    def test_callback_query_and_provider_exception_are_not_logged_or_echoed(self) -> None:
        code = "CALLBACK_CODE_SECRET_MARKER"
        state = "CALLBACK_STATE_MARKER"
        provider_secret = "PROVIDER_EXCEPTION_SECRET_MARKER"
        failure = self.bridge.google_sheet_hub.GoogleSheetHubError(
            "oauth_exchange_rejected",
            provider_secret,
            502,
        )
        log = io.StringIO()
        with (
            patch.object(
                self.bridge.google_sheet_hub,
                "complete_google_oauth",
                side_effect=failure,
            ),
            redirect_stderr(log),
        ):
            status, body = self.read_url(f"{CALLBACK_PATH}?code={code}&state={state}")
        self.assertEqual(status, 502)
        combined = log.getvalue() + body.decode("utf-8", errors="replace")
        for secret in (code, state, provider_secret):
            self.assertNotIn(secret, combined)
        for path in (
            self.temp_path / "bridge-audit.jsonl",
            self.temp_path / "dashboard-workflow-settings.json",
        ):
            if path.exists():
                persisted = path.read_text(encoding="utf-8")
                for secret in (code, state, provider_secret):
                    self.assertNotIn(secret, persisted)

    def test_unexpected_callback_exception_message_is_never_persisted(self) -> None:
        code = "UNEXPECTED_CALLBACK_CODE_MARKER"
        state = "UNEXPECTED_CALLBACK_STATE_MARKER"
        exception_marker = "PROVIDER_RAW_VALUE_Q7Z9"
        log = io.StringIO()
        with (
            patch.object(
                self.bridge.google_sheet_hub,
                "complete_google_oauth",
                side_effect=RuntimeError(exception_marker),
            ),
            redirect_stderr(log),
        ):
            status, body = self.read_url(f"{CALLBACK_PATH}?code={code}&state={state}")
        self.assertEqual(status, 500)
        persisted = ""
        audit_path = self.temp_path / "bridge-audit.jsonl"
        if audit_path.exists():
            persisted = audit_path.read_text(encoding="utf-8")
        combined = log.getvalue() + body.decode("utf-8", errors="replace") + persisted
        for secret in (code, state, exception_marker):
            self.assertNotIn(secret, combined)
        if persisted:
            events = [json.loads(line) for line in persisted.splitlines() if line.strip()]
            callback_failures = [
                event
                for event in events
                if event.get("path") == CALLBACK_PATH
                or event.get("type") == "research_sheet.google_oauth_callback_failed"
            ]
            self.assertTrue(callback_failures)
            for event in callback_failures:
                self.assertNotIn("errorMessage", event)

    def test_classified_http_errors_audit_only_allowlisted_kind_and_generic_guidance(self) -> None:
        allowlisted = {
            "oauth_invalid_client",
            "oauth_client_secret_required",
            "oauth_code_invalid_or_expired",
            "oauth_redirect_mismatch",
            "oauth_scope_missing",
            "oauth_invalid_request",
            "oauth_authorization_denied",
            "oauth_rate_limited",
            "oauth_unavailable",
            "oauth_exchange_rejected",
        }
        cases = (
            (401, "invalid_client", "ROUTE_PROVIDER_DESCRIPTION_MARKER_0", "oauth_invalid_client"),
            (400, "invalid_grant", "ROUTE_PROVIDER_DESCRIPTION_MARKER_1", "oauth_code_invalid_or_expired"),
            (
                400,
                "invalid_request",
                "client_secret is missing. ROUTE_CLIENT_SECRET_DESCRIPTION_MARKER",
                "oauth_client_secret_required",
            ),
            (400, "PROVIDER_ARBITRARY_KIND_MARKER", "ROUTE_PROVIDER_DESCRIPTION_MARKER_3", "oauth_exchange_rejected"),
        )
        original_complete = self.bridge.google_sheet_hub.complete_google_oauth
        audit_path = self.temp_path / "bridge-audit.jsonl"
        for index, (http_status, provider_error, description, expected_kind) in enumerate(cases):
            with self.subTest(provider_error=provider_error):
                environment = {
                    "METAFX_GOOGLE_OAUTH_CLIENT_ID": "desktop-client-id.apps.googleusercontent.com"
                }
                callback_uri = f"{self.base_url}{CALLBACK_PATH}"
                with patch.object(
                    self.bridge.google_sheet_hub.google_oauth_store,
                    "status",
                    return_value={"available": True, "stored": False, "status": "empty"},
                ):
                    started = self.bridge.google_sheet_hub.start_google_oauth(
                        callback_uri,
                        environment,
                    )
                state = authorization_query(started)["state"][0]
                callback_code = f"ROUTE_CALLBACK_CODE_MARKER_{index}"
                provider_error_response = oauth_http_error(
                    http_status,
                    provider_error,
                    description,
                )

                def complete_with_http_error(query, *, _error=provider_error_response):
                    return original_complete(
                        query,
                        environment,
                        open_url=Mock(side_effect=_error),
                    )

                log = io.StringIO()
                with (
                    patch.object(
                        self.bridge.google_sheet_hub,
                        "complete_google_oauth",
                        side_effect=complete_with_http_error,
                    ),
                    redirect_stderr(log),
                ):
                    status, body = self.read_url(
                        f"{CALLBACK_PATH}?code={callback_code}&state={state}"
                    )
                self.assertGreaterEqual(status, 400)
                events = [
                    json.loads(line)
                    for line in audit_path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                callback_event = next(
                    event
                    for event in reversed(events)
                    if event.get("type") == "research_sheet.google_oauth_callback_failed"
                )
                self.assertEqual(callback_event["errorKind"], expected_kind)
                self.assertIn(callback_event["errorKind"], allowlisted)
                self.assertEqual(callback_event.get("sensitiveQueryPersisted"), False)
                self.assertNotIn("errorMessage", callback_event)
                persisted = audit_path.read_text(encoding="utf-8")
                combined = log.getvalue() + body.decode("utf-8", errors="replace") + persisted
                for marker in (
                    callback_code,
                    state,
                    provider_error,
                    description,
                    "PROVIDER_URI_TOKEN_MARKER",
                    "PROVIDER_BODY_CODE_MARKER",
                    "PROVIDER_BODY_STATE_MARKER",
                    "PROVIDER_BODY_ACCESS_TOKEN_MARKER",
                    "PROVIDER_BODY_REFRESH_TOKEN_MARKER",
                    "PROVIDER_HTTP_REASON_MARKER",
                    "PROVIDER_HEADER_SECRET_MARKER",
                ):
                    # Allowlisted provider identifiers such as invalid_client may
                    # be represented only by the internal oauth_* kind, never as
                    # their raw provider field value.
                    if marker == provider_error and provider_error in {
                        "invalid_client",
                        "invalid_grant",
                    }:
                        self.assertNotIn(f'"error": "{marker}"', combined)
                    else:
                        self.assertNotIn(marker, combined)
                settings_path = self.temp_path / "dashboard-workflow-settings.json"
                if settings_path.exists():
                    settings = settings_path.read_text(encoding="utf-8")
                    for marker in (callback_code, state, description):
                        self.assertNotIn(marker, settings)

    def test_auth_mutations_reject_and_do_not_echo_frontend_credentials(self) -> None:
        for route in ("auth/start", "auth/disconnect"):
            marker = f"FRONTEND_{route.replace('/', '_').upper()}_SECRET_MARKER"
            request = Request(
                f"{self.base_url}/api/props/mission_strategy_table/research-sheet/{route}",
                data=json.dumps({"clientSecret": marker}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.subTest(route=route):
                try:
                    with urlopen(request, timeout=3) as response:
                        status, body = response.status, response.read()
                except HTTPError as error:
                    try:
                        status, body = error.code, error.read()
                    finally:
                        error.close()
                self.assertEqual(status, 422)
                self.assertNotIn(marker.encode("utf-8"), body)
        for path in (
            self.temp_path / "bridge-audit.jsonl",
            self.temp_path / "dashboard-workflow-settings.json",
        ):
            if path.exists():
                self.assertNotIn("SECRET_MARKER", path.read_text(encoding="utf-8"))


class GoogleOAuthContractTests(unittest.TestCase):
    def test_contract_and_setup_doc_define_one_time_secure_oauth(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        endpoints = contract["endpoints"]
        for endpoint in (
            "GET /api/props/mission_strategy_table/research-sheet/auth",
            "POST /api/props/mission_strategy_table/research-sheet/auth/start",
            "GET /api/props/mission_strategy_table/research-sheet/auth/callback?code={code}&state={state}",
            "POST /api/props/mission_strategy_table/research-sheet/auth/disconnect",
        ):
            self.assertIn(endpoint, endpoints)
        oauth = contract["research_sheet_hub"]["oauthBootstrap"]
        self.assertEqual(oauth["pkceMethod"], "S256")
        self.assertEqual(oauth["pkceVerifierLength"], {"minimum": 43, "maximum": 128})
        self.assertTrue(oauth["stateAndVerifierAreShortLivedAndOneTime"])
        self.assertFalse(oauth["callbackQueryMayBeLogged"])
        self.assertEqual(
            oauth["durableRefreshTokenStore"],
            "windows_current_user_dpapi_outside_project",
        )
        self.assertEqual(
            oauth["authReadModelFields"],
            [
                "configured",
                "connected",
                "status",
                "mode",
                "clientConfigured",
                "messageTh",
                "credentialsAcceptedByFrontend",
                "storedCredential",
                "environmentCredential",
            ],
        )
        self.assertEqual(
            oauth["authorizationUrlAllowedOrigin"],
            "https://accounts.google.com",
        )
        classification = oauth["httpErrorClassification"]
        self.assertEqual(classification["maximumProviderBodyBytes"], 16 * 1024)
        self.assertEqual(
            set(classification["allowlistedInternalKinds"]),
            {
                "oauth_invalid_client",
                "oauth_client_secret_required",
                "oauth_code_invalid_or_expired",
                "oauth_redirect_mismatch",
                "oauth_scope_missing",
                "oauth_invalid_request",
                "oauth_authorization_denied",
                "oauth_rate_limited",
                "oauth_unavailable",
                "oauth_exchange_rejected",
            },
        )
        self.assertFalse(classification["providerValuesMayBeReturned"])
        self.assertFalse(classification["providerValuesMayBeAudited"])
        self.assertEqual(
            classification["callbackAuditFields"],
            ["type", "errorKind", "sensitiveQueryPersisted"],
        )
        boundary = contract["research_sheet_hub"]["credentialBoundary"]
        self.assertFalse(boundary["frontendMayReadOrWriteCredentials"])
        self.assertFalse(boundary["reportsMayContainCredentials"])
        self.assertFalse(boundary["auditMayContainCredentials"])
        self.assertFalse(boundary["settingsMayContainCredentials"])

        setup = SETUP_DOC_PATH.read_text(encoding="utf-8")
        for required in (
            CALLBACK_PATH,
            "PKCE `S256`",
            "Windows current-user DPAPI",
            "METAFX_GOOGLE_OAUTH_CLIENT_ID",
            "METAFX_GOOGLE_OAUTH_REFRESH_TOKEN",
            "oauth_client_secret_required",
            "16 KiB",
        ):
            self.assertIn(required, setup)


if __name__ == "__main__":
    unittest.main()
