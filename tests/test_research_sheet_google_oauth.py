from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from datetime import timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "backend" / "local-runner"
BRIDGE_PATH = RUNNER / "bridge_server.py"
if str(RUNNER) not in sys.path:
    sys.path.insert(0, str(RUNNER))

import google_oauth_store as store  # noqa: E402
import google_sheet_hub as hub  # noqa: E402

REAL_STORE_SAVE = store.save_refresh_token
REAL_STORE_LOAD = store.load_refresh_token
REAL_STORE_DELETE = store.delete_refresh_token


class FakeJsonResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, _limit: int = -1) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def load_bridge():
    spec = importlib.util.spec_from_file_location("google_oauth_route_test_bridge", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    # Keep this focused route test independent of an optional tzdata wheel on
    # minimal Windows Python installations used by local development.
    with mock.patch("zoneinfo.ZoneInfo", return_value=timezone(timedelta(hours=7))):
        spec.loader.exec_module(module)
    return module


class ResearchSheetGoogleOAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.saved: dict[str, str] = {}
        self.store_patches = (
            mock.patch.object(
                store,
                "status",
                side_effect=lambda: {
                    "available": True,
                    "stored": bool(self.saved.get("refresh")),
                    "status": "ready" if self.saved.get("refresh") else "empty",
                },
            ),
            mock.patch.object(
                store,
                "save_refresh_token",
                side_effect=lambda value: self.saved.__setitem__("refresh", value),
            ),
            mock.patch.object(
                store,
                "load_refresh_token",
                side_effect=lambda: self.saved.get("refresh"),
            ),
            mock.patch.object(
                store,
                "delete_refresh_token",
                side_effect=lambda: self.saved.pop("refresh", None) is not None,
            ),
        )
        for patcher in self.store_patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        with hub._OAUTH_FLOW_LOCK:
            hub._PENDING_OAUTH_FLOWS.clear()
        self.addCleanup(self._clear_flows)

    def _clear_flows(self) -> None:
        with hub._OAUTH_FLOW_LOCK:
            hub._PENDING_OAUTH_FLOWS.clear()

    def test_start_requires_client_id_and_returns_pkce_url_without_secrets(self) -> None:
        with self.assertRaises(hub.GoogleSheetHubError) as caught:
            hub.start_google_oauth(
                f"http://127.0.0.1:4191{hub.GOOGLE_OAUTH_CALLBACK_PATH}",
                {},
            )
        self.assertEqual(caught.exception.code, "oauth_client_not_configured")

        environment = {
            "METAFX_GOOGLE_OAUTH_CLIENT_ID": "desktop-client.apps.googleusercontent.com",
            "METAFX_GOOGLE_OAUTH_CLIENT_SECRET": "never-return-this-secret",
        }
        result = hub.start_google_oauth(
            f"http://127.0.0.1:4191{hub.GOOGLE_OAUTH_CALLBACK_PATH}",
            environment,
            now_monotonic=100,
        )
        parsed = urlsplit(result["authorizationUrl"])
        query = parse_qs(parsed.query)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertEqual(query["access_type"], ["offline"])
        self.assertEqual(query["prompt"], ["consent"])
        self.assertEqual(query["scope"], [hub.SHEETS_SCOPE])
        self.assertEqual(query["redirect_uri"], [f"http://127.0.0.1:4191{hub.GOOGLE_OAUTH_CALLBACK_PATH}"])
        state = query["state"][0]
        with hub._OAUTH_FLOW_LOCK:
            verifier = hub._PENDING_OAUTH_FLOWS[state]["verifier"]
        serialized = json.dumps(result)
        self.assertNotIn(verifier, serialized)
        self.assertNotIn(environment["METAFX_GOOGLE_OAUTH_CLIENT_SECRET"], serialized)

    def test_callback_is_one_use_exchanges_pkce_and_persists_only_refresh_token(self) -> None:
        environment = {"METAFX_GOOGLE_OAUTH_CLIENT_ID": "desktop-client"}
        started = hub.start_google_oauth(
            f"http://127.0.0.1:4191{hub.GOOGLE_OAUTH_CALLBACK_PATH}",
            environment,
            now_monotonic=10,
        )
        state = parse_qs(urlsplit(started["authorizationUrl"]).query)["state"][0]
        requests = []

        def open_url(request, timeout=0):
            requests.append((request, timeout))
            return FakeJsonResponse(
                {
                    "access_token": "access-must-not-return",
                    "refresh_token": "refresh-must-not-return",
                    "scope": hub.SHEETS_SCOPE,
                }
            )

        result = hub.complete_google_oauth(
            {"state": [state], "code": ["one-time-code-must-not-return"]},
            environment,
            open_url=open_url,
            now_monotonic=11,
        )
        self.assertEqual(self.saved["refresh"], "refresh-must-not-return")
        self.assertEqual(len(requests), 1)
        form = parse_qs(requests[0][0].data.decode("utf-8"))
        self.assertEqual(form["grant_type"], ["authorization_code"])
        self.assertEqual(form["code"], ["one-time-code-must-not-return"])
        self.assertEqual(len(form["code_verifier"][0]) >= 43, True)
        self.assertNotIn("client_secret", form)
        serialized = json.dumps(result)
        self.assertNotIn("one-time-code-must-not-return", serialized)
        self.assertNotIn("access-must-not-return", serialized)
        self.assertNotIn("refresh-must-not-return", serialized)
        with self.assertRaises(hub.GoogleSheetHubError) as replay:
            hub.complete_google_oauth(
                {"state": [state], "code": ["another-code"]},
                environment,
                open_url=open_url,
                now_monotonic=12,
            )
        self.assertEqual(replay.exception.code, "oauth_state_invalid")
        self.assertEqual(len(requests), 1)

    def test_callback_rejects_missing_sheets_scope_before_secure_store_write(self) -> None:
        environment = {"METAFX_GOOGLE_OAUTH_CLIENT_ID": "desktop-client"}
        started = hub.start_google_oauth(
            f"http://127.0.0.1:4191{hub.GOOGLE_OAUTH_CALLBACK_PATH}",
            environment,
            now_monotonic=10,
        )
        state = parse_qs(urlsplit(started["authorizationUrl"]).query)["state"][0]
        with self.assertRaises(hub.GoogleSheetHubError) as missing_scope:
            hub.complete_google_oauth(
                {"state": [state], "code": ["one-time-code"]},
                environment,
                open_url=lambda *_args, **_kwargs: FakeJsonResponse(
                    {"access_token": "access", "refresh_token": "refresh", "scope": "openid"}
                ),
                now_monotonic=11,
            )
        self.assertEqual(missing_scope.exception.code, "oauth_scope_missing")
        self.assertNotIn("refresh", self.saved)

    def test_provider_http_errors_are_allowlisted_and_never_expose_description(self) -> None:
        environment = {"METAFX_GOOGLE_OAUTH_CLIENT_ID": "desktop-client"}
        cases = (
            ("invalid_client", 400, "oauth_invalid_client"),
            ("unauthorized_client", 401, "oauth_invalid_client"),
            ("invalid_grant", 400, "oauth_code_invalid_or_expired"),
            ("redirect_uri_mismatch", 400, "oauth_redirect_mismatch"),
            ("invalid_scope", 400, "oauth_scope_missing"),
            ("invalid_request", 400, "oauth_invalid_request"),
            ("access_denied", 403, "oauth_authorization_denied"),
            ("rate_limit_exceeded", 400, "oauth_rate_limited"),
            ("slow_down", 400, "oauth_rate_limited"),
            ("temporarily_unavailable", 400, "oauth_unavailable"),
        )
        for index, (provider_error, http_status, expected_kind) in enumerate(cases):
            with self.subTest(provider_error=provider_error):
                started = hub.start_google_oauth(
                    f"http://127.0.0.1:4191{hub.GOOGLE_OAUTH_CALLBACK_PATH}",
                    environment,
                    now_monotonic=100 + index,
                )
                state = parse_qs(urlsplit(started["authorizationUrl"]).query)["state"][0]
                description_marker = f"provider-secret-description-{index}"

                def rejected(*_args, **_kwargs):
                    body = json.dumps(
                        {
                            "error": provider_error,
                            "error_description": description_marker,
                            "access_token": "must-not-be-read-or-returned",
                        }
                    ).encode("utf-8")
                    raise HTTPError(
                        hub.GOOGLE_TOKEN_URL,
                        http_status,
                        "provider reason must not be returned",
                        {},
                        io.BytesIO(body),
                    )

                with self.assertRaises(hub.GoogleSheetHubError) as caught:
                    hub.complete_google_oauth(
                        {"state": [state], "code": [f"one-time-code-{index}"]},
                        environment,
                        open_url=rejected,
                        now_monotonic=101 + index,
                    )
                self.assertEqual(caught.exception.code, expected_kind)
                self.assertNotIn(description_marker, str(caught.exception))
                self.assertNotIn("must-not-be-read-or-returned", str(caught.exception))
                self.assertNotIn("refresh", self.saved)

    def test_unknown_oversize_429_and_5xx_oauth_errors_fail_safely(self) -> None:
        environment = {"METAFX_GOOGLE_OAUTH_CLIENT_ID": "desktop-client"}
        cases = (
            (
                400,
                {"error": "future_provider_code", "error_description": "unknown-secret"},
                "oauth_exchange_rejected",
            ),
            (429, {"error": "future_provider_code"}, "oauth_rate_limited"),
            (503, {"error": "invalid_client"}, "oauth_unavailable"),
        )
        for index, (http_status, payload, expected_kind) in enumerate(cases):
            with self.subTest(http_status=http_status):
                started = hub.start_google_oauth(
                    f"http://127.0.0.1:4191{hub.GOOGLE_OAUTH_CALLBACK_PATH}",
                    environment,
                    now_monotonic=200 + index,
                )
                state = parse_qs(urlsplit(started["authorizationUrl"]).query)["state"][0]

                def rejected(*_args, **_kwargs):
                    raise HTTPError(
                        hub.GOOGLE_TOKEN_URL,
                        http_status,
                        "unsafe reason marker",
                        {},
                        io.BytesIO(json.dumps(payload).encode("utf-8")),
                    )

                with self.assertRaises(hub.GoogleSheetHubError) as caught:
                    hub.complete_google_oauth(
                        {"state": [state], "code": [f"code-{index}"]},
                        environment,
                        open_url=rejected,
                        now_monotonic=201 + index,
                    )
                self.assertEqual(caught.exception.code, expected_kind)
                self.assertNotIn("unknown-secret", str(caught.exception))
                self.assertNotIn("unsafe reason marker", str(caught.exception))

        started = hub.start_google_oauth(
            f"http://127.0.0.1:4191{hub.GOOGLE_OAUTH_CALLBACK_PATH}",
            environment,
            now_monotonic=300,
        )
        state = parse_qs(urlsplit(started["authorizationUrl"]).query)["state"][0]
        oversized_marker = "oversized-provider-secret"
        oversized = json.dumps(
            {
                "error": "invalid_client",
                "error_description": oversized_marker
                + ("x" * hub.MAX_OAUTH_ERROR_RESPONSE_BYTES),
            }
        ).encode("utf-8")

        def oversized_rejection(*_args, **_kwargs):
            raise HTTPError(
                hub.GOOGLE_TOKEN_URL,
                400,
                "unsafe reason marker",
                {},
                io.BytesIO(oversized),
            )

        with self.assertRaises(hub.GoogleSheetHubError) as caught:
            hub.complete_google_oauth(
                {"state": [state], "code": ["oversized-code"]},
                environment,
                open_url=oversized_rejection,
                now_monotonic=301,
            )
        self.assertEqual(caught.exception.code, "oauth_exchange_rejected")
        self.assertNotIn(oversized_marker, str(caught.exception))

    def test_exact_client_secret_missing_condition_is_actionable_without_description_leak(self) -> None:
        environment = {"METAFX_GOOGLE_OAUTH_CLIENT_ID": "desktop-client"}
        cases = (
            ("client_secret is missing.", "oauth_client_secret_required"),
            (
                "client_secret is missing; debug=provider-private-value",
                "oauth_invalid_request",
            ),
        )
        for index, (description, expected_kind) in enumerate(cases):
            with self.subTest(description=description):
                started = hub.start_google_oauth(
                    f"http://127.0.0.1:4191{hub.GOOGLE_OAUTH_CALLBACK_PATH}",
                    environment,
                    now_monotonic=400 + index,
                )
                state = parse_qs(urlsplit(started["authorizationUrl"]).query)["state"][0]

                def rejected(*_args, **_kwargs):
                    raise HTTPError(
                        hub.GOOGLE_TOKEN_URL,
                        400,
                        "unsafe provider reason",
                        {},
                        io.BytesIO(
                            json.dumps(
                                {
                                    "error": "invalid_request",
                                    "error_description": description,
                                }
                            ).encode("utf-8")
                        ),
                    )

                with self.assertRaises(hub.GoogleSheetHubError) as caught:
                    hub.complete_google_oauth(
                        {"state": [state], "code": [f"code-{index}"]},
                        environment,
                        open_url=rejected,
                        now_monotonic=401 + index,
                    )
                self.assertEqual(caught.exception.code, expected_kind)
                self.assertNotIn(description, str(caught.exception))
                self.assertNotIn("provider-private-value", str(caught.exception))

    def test_callback_state_expires_and_disconnect_does_not_disable_environment_fallback(self) -> None:
        environment = {
            "METAFX_GOOGLE_OAUTH_CLIENT_ID": "desktop-client",
            "METAFX_GOOGLE_OAUTH_REFRESH_TOKEN": "environment-refresh",
        }
        started = hub.start_google_oauth(
            f"http://127.0.0.1:4191{hub.GOOGLE_OAUTH_CALLBACK_PATH}",
            environment,
            now_monotonic=20,
        )
        state = parse_qs(urlsplit(started["authorizationUrl"]).query)["state"][0]
        with self.assertRaises(hub.GoogleSheetHubError) as expired:
            hub.complete_google_oauth(
                {"state": [state], "code": ["expired-code"]},
                environment,
                now_monotonic=20 + hub.GOOGLE_OAUTH_FLOW_TTL_SECONDS + 1,
            )
        self.assertEqual(expired.exception.code, "oauth_state_expired")

        self.saved["refresh"] = "stored-refresh"
        result = hub.disconnect_google_oauth(environment)
        self.assertTrue(result["storedCredentialRemoved"])
        self.assertTrue(result["auth"]["connected"])
        self.assertEqual(result["auth"]["mode"], "oauth_refresh")
        self.assertNotIn("environment-refresh", json.dumps(result))

    def test_exact_ttl_boundary_is_expired_and_client_id_only_is_partial(self) -> None:
        environment = {"METAFX_GOOGLE_OAUTH_CLIENT_ID": "desktop-client"}
        status = hub.credential_status(environment)
        self.assertFalse(status["configured"])
        self.assertTrue(status["partialConfiguration"])
        started = hub.start_google_oauth(
            f"http://127.0.0.1:4191{hub.GOOGLE_OAUTH_CALLBACK_PATH}",
            environment,
            now_monotonic=50,
        )
        state = parse_qs(urlsplit(started["authorizationUrl"]).query)["state"][0]
        with self.assertRaises(hub.GoogleSheetHubError) as expired:
            hub.complete_google_oauth(
                {"state": [state], "code": ["boundary-code"]},
                environment,
                now_monotonic=50 + hub.GOOGLE_OAUTH_FLOW_TTL_SECONDS,
            )
        self.assertEqual(expired.exception.code, "oauth_state_expired")

    def test_access_token_uses_saved_refresh_with_optional_client_secret(self) -> None:
        self.saved["refresh"] = "saved-refresh"
        captured = []

        def open_url(request, timeout=0):
            captured.append(request)
            return FakeJsonResponse({"access_token": "short-lived-access"})

        token = hub.access_token(
            {"METAFX_GOOGLE_OAUTH_CLIENT_ID": "desktop-client"},
            open_url=open_url,
        )
        self.assertEqual(token, "short-lived-access")
        form = parse_qs(captured[0].data.decode("utf-8"))
        self.assertEqual(form["refresh_token"], ["saved-refresh"])
        self.assertNotIn("client_secret", form)

    def test_refresh_invalid_grant_maps_to_reconnect_required(self) -> None:
        self.saved["refresh"] = "saved-refresh"

        def rejected(*_args, **_kwargs):
            raise HTTPError(hub.GOOGLE_TOKEN_URL, 400, "Bad Request", {}, None)

        with self.assertRaises(hub.GoogleSheetHubError) as caught:
            hub.access_token(
                {"METAFX_GOOGLE_OAUTH_CLIENT_ID": "desktop-client"},
                open_url=rejected,
            )
        self.assertEqual(caught.exception.code, "auth_expired")
        self.assertEqual(caught.exception.status, 401)

    def test_dpapi_store_file_contains_only_ciphertext_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credential.dpapi"
            with (
                mock.patch.object(store, "_protect", side_effect=lambda value: b"cipher:" + value[::-1]),
                mock.patch.object(store, "_unprotect", side_effect=lambda value: value.removeprefix(b"cipher:")[::-1]),
            ):
                REAL_STORE_SAVE("a-sensitive-refresh-token", path=path)
                raw = path.read_bytes()
                self.assertNotIn(b"a-sensitive-refresh-token", raw)
                self.assertEqual(REAL_STORE_LOAD(path=path), "a-sensitive-refresh-token")
                self.assertTrue(REAL_STORE_DELETE(path=path))
                self.assertFalse(path.exists())


class ResearchSheetGoogleOAuthRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def handler(self, path: str):
        handler = object.__new__(self.bridge.BridgeHandler)
        handler.path = path
        handler.headers = {
            "Host": "127.0.0.1:4191",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
        }
        handler.server = SimpleNamespace(server_port=4191)
        handler.send_json = mock.Mock()
        handler.send_google_oauth_callback_page = mock.Mock()
        return handler

    def test_exact_cross_site_top_level_callback_is_allowed(self) -> None:
        path = f"{hub.GOOGLE_OAUTH_CALLBACK_PATH}?state=safe-state&code=secret-code"
        handler = self.handler(path)
        with mock.patch.object(
            self.bridge.google_sheet_hub,
            "complete_google_oauth",
            return_value={"messageTh": "connected"},
        ) as complete, mock.patch.object(self.bridge, "append_audit") as audit:
            handler._do_GET_guarded()
        complete.assert_called_once_with({"state": ["safe-state"], "code": ["secret-code"]})
        handler.send_google_oauth_callback_page.assert_called_once_with(
            connected=True,
            message_th="connected",
        )
        persisted = audit.call_args.args[0]
        self.assertNotIn("state", persisted)
        self.assertNotIn("code", persisted)
        self.assertNotIn("authorizationUrl", persisted)

    def test_classified_callback_uses_static_actionable_thai_not_provider_text(self) -> None:
        path = f"{hub.GOOGLE_OAUTH_CALLBACK_PATH}?state=safe-state&code=secret-code"
        handler = self.handler(path)
        provider_marker = "provider-error-description-must-not-render"
        failure = self.bridge.google_sheet_hub.GoogleSheetHubError(
            "oauth_invalid_client",
            provider_marker,
            503,
        )
        with (
            mock.patch.object(
                self.bridge.google_sheet_hub,
                "complete_google_oauth",
                side_effect=failure,
            ),
            mock.patch.object(self.bridge, "append_audit") as audit,
        ):
            handler._do_GET_guarded()
        callback = handler.send_google_oauth_callback_page.call_args.kwargs
        self.assertFalse(callback["connected"])
        self.assertIn("Desktop OAuth Client ID", callback["message_th"])
        self.assertNotIn(provider_marker, callback["message_th"])
        self.assertEqual(audit.call_args.args[0]["errorKind"], "oauth_invalid_client")

    def test_callback_rejects_non_navigation_and_log_skips_query(self) -> None:
        handler = self.handler(f"{hub.GOOGLE_OAUTH_CALLBACK_PATH}?code=must-not-log")
        handler.headers["Sec-Fetch-Mode"] = "cors"
        with self.assertRaises(self.bridge.RequestError):
            handler.validate_google_oauth_callback_request()

    def test_unexpected_callback_failure_never_audits_raw_exception_or_query(self) -> None:
        secret_marker = "oauth-code-and-token-must-never-be-audited"
        handler = self.handler(
            f"{hub.GOOGLE_OAUTH_CALLBACK_PATH}?code={secret_marker}"
        )
        handler._do_GET_guarded = mock.Mock(side_effect=RuntimeError(secret_marker))
        with mock.patch.object(self.bridge, "append_audit") as audit:
            handler.do_GET()
        event = audit.call_args.args[0]
        serialized = json.dumps(event)
        self.assertNotIn(secret_marker, serialized)
        self.assertNotIn("errorMessage", event)
        self.assertFalse(event["sensitiveErrorPersisted"])
        with mock.patch("http.server.BaseHTTPRequestHandler.log_message") as parent_log:
            handler.log_message(
                '%s %s',
                "GET",
                f"{hub.GOOGLE_OAUTH_CALLBACK_PATH}?code=must-not-log",
            )
        parent_log.assert_not_called()

        handler.headers["Sec-Fetch-Mode"] = "navigate"
        handler.headers["Host"] = "127.0.0.1:4999"
        with self.assertRaises(self.bridge.RequestError):
            handler.validate_google_oauth_callback_request()

    def test_status_route_returns_safe_auth_contract(self) -> None:
        handler = self.handler("/api/props/mission_strategy_table/research-sheet/auth")
        handler.headers = {"Host": "127.0.0.1:4191"}
        expected = {
            "configured": False,
            "connected": False,
            "status": "authorization_required",
            "mode": "not_configured",
            "clientConfigured": True,
        }
        with mock.patch.object(
            self.bridge.google_sheet_hub,
            "google_oauth_status",
            return_value=expected,
        ):
            handler._do_GET_guarded()
        handler.send_json.assert_called_once_with({"ok": True, "auth": expected})

    def test_start_route_reports_missing_client_id_without_accepting_credentials(self) -> None:
        handler = self.handler(
            "/api/props/mission_strategy_table/research-sheet/auth/start"
        )
        handler.headers = {"Host": "127.0.0.1:4191"}
        handler.read_payload = mock.Mock(return_value={})
        failure = self.bridge.google_sheet_hub.GoogleSheetHubError(
            "oauth_client_not_configured",
            "client id missing",
            503,
        )
        with (
            mock.patch.object(
                self.bridge.google_sheet_hub,
                "start_google_oauth",
                side_effect=failure,
            ),
            mock.patch.object(self.bridge, "append_audit") as audit,
        ):
            handler.do_POST()
        response, = [
            call.args[0]
            for call in handler.send_json.call_args_list
            if isinstance(call.args[0], dict)
        ]
        self.assertFalse(response["ok"])
        self.assertEqual(response["kind"], "oauth_client_not_configured")
        self.assertNotIn("code", response)
        self.assertEqual(handler.send_json.call_args.kwargs["status"], 503)
        self.assertEqual(
            audit.call_args.args[0]["type"],
            "research_sheet.google_oauth_start_failed",
        )


if __name__ == "__main__":
    unittest.main()
