from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "backend" / "local-runner"
if str(RUNNER) not in sys.path:
    sys.path.insert(0, str(RUNNER))

import configure_google_oauth_client as cli  # noqa: E402
import google_oauth_store as store  # noqa: E402
import google_sheet_hub as hub  # noqa: E402


CLIENT_ID = (
    "149991890071-p57qibgugqvfa3k3p0cm94q74b9umajd"
    ".apps.googleusercontent.com"
)
OTHER_CLIENT_ID = (
    "149991890071-anotherdesktopclientidentifier1234567"
    ".apps.googleusercontent.com"
)
CLIENT_SECRET = "TEST_ONLY_DESKTOP_CLIENT_SECRET_MARKER"


def desktop_client_json(
    *,
    client_id: str = CLIENT_ID,
    client_secret: str = CLIENT_SECRET,
) -> str:
    return json.dumps(
        {
            "installed": {
                "client_id": client_id,
                "project_id": "test-project",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": hub.GOOGLE_TOKEN_URL,
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": ["http://localhost"],
            }
        }
    )


class GoogleOAuthClientStoreTests(unittest.TestCase):
    def test_client_configuration_is_only_persisted_inside_dpapi_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credentials" / "client.dpapi"
            with (
                mock.patch.object(
                    store,
                    "_protect_client_configuration",
                    side_effect=lambda value: b"cipher:" + value[::-1],
                ),
                mock.patch.object(
                    store,
                    "_unprotect_client_configuration",
                    side_effect=lambda value: value.removeprefix(b"cipher:")[::-1],
                ),
            ):
                store.save_client_configuration(CLIENT_ID, CLIENT_SECRET, path=path)
                persisted = path.read_bytes()
                self.assertTrue(persisted.startswith(store._CLIENT_STORE_MAGIC))
                self.assertNotIn(CLIENT_ID.encode("utf-8"), persisted)
                self.assertNotIn(CLIENT_SECRET.encode("utf-8"), persisted)
                self.assertEqual(
                    store.load_client_configuration(path=path),
                    {"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET},
                )
                status = store.client_configuration_status(path=path)
                self.assertTrue(status["stored"])
                self.assertNotIn(CLIENT_ID, json.dumps(status))
                self.assertNotIn(CLIENT_SECRET, json.dumps(status))

    def test_invalid_or_plaintext_client_store_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "client.dpapi"
            path.write_text(desktop_client_json(), encoding="utf-8")
            with self.assertRaises(store.SecureStoreError) as caught:
                store.load_client_configuration(path=path)
            self.assertEqual(caught.exception.code, "secure_store_invalid")


class GoogleOAuthClientParserTests(unittest.TestCase):
    def test_parser_accepts_only_installed_desktop_loopback_contract(self) -> None:
        parsed = hub.parse_google_oauth_client_json(desktop_client_json())
        self.assertEqual(parsed["clientId"], CLIENT_ID)
        self.assertEqual(parsed["clientSecret"], CLIENT_SECRET)

        web = json.loads(desktop_client_json())
        web["web"] = web.pop("installed")
        with self.assertRaises(hub.GoogleSheetHubError) as wrong_type:
            hub.parse_google_oauth_client_json(json.dumps(web))
        self.assertEqual(wrong_type.exception.code, "oauth_client_not_desktop")

        invalid_endpoint = json.loads(desktop_client_json())
        invalid_endpoint["installed"]["token_uri"] = "https://example.invalid/token"
        with self.assertRaises(hub.GoogleSheetHubError) as wrong_endpoint:
            hub.parse_google_oauth_client_json(json.dumps(invalid_endpoint))
        self.assertEqual(wrong_endpoint.exception.code, "invalid_oauth_client_file")

        invalid_redirect = json.loads(desktop_client_json())
        invalid_redirect["installed"]["redirect_uris"] = ["https://example.invalid/callback"]
        with self.assertRaises(hub.GoogleSheetHubError) as wrong_redirect:
            hub.parse_google_oauth_client_json(json.dumps(invalid_redirect))
        self.assertEqual(wrong_redirect.exception.code, "oauth_client_not_desktop")

    def test_parser_rejects_oversized_or_non_utf8_files_without_echoing_content(self) -> None:
        with self.assertRaises(hub.GoogleSheetHubError) as oversized:
            hub.parse_google_oauth_client_json(
                b"x" * (hub.MAX_OAUTH_CLIENT_JSON_BYTES + 1)
            )
        self.assertEqual(oversized.exception.code, "oauth_client_file_too_large")
        with self.assertRaises(hub.GoogleSheetHubError) as invalid_utf8:
            hub.parse_google_oauth_client_json(b"\xff\xfe")
        self.assertEqual(invalid_utf8.exception.code, "invalid_oauth_client_file")


class GoogleOAuthClientConfigurationTests(unittest.TestCase):
    def tearDown(self) -> None:
        with hub._OAUTH_FLOW_LOCK:
            hub._PENDING_OAUTH_FLOWS.clear()

    def test_reimport_same_client_is_idempotent_and_preserves_refresh(self) -> None:
        previous = {
            "clientId": CLIENT_ID,
            "clientSecret": CLIENT_SECRET,
            "source": "secure_store",
        }
        with (
            mock.patch.object(hub, "oauth_client_configuration", return_value=previous),
            mock.patch.object(store, "save_client_configuration") as save,
            mock.patch.object(store, "delete_refresh_token") as delete,
        ):
            result = hub.configure_google_oauth_client_json(desktop_client_json())
        save.assert_called_once_with(CLIENT_ID, CLIENT_SECRET)
        delete.assert_not_called()
        self.assertFalse(result["authorizationReset"])
        serialized = json.dumps(result)
        self.assertNotIn(CLIENT_ID, serialized)
        self.assertNotIn(CLIENT_SECRET, serialized)

    def test_expected_client_id_mismatch_fails_before_secure_store_mutation(self) -> None:
        with (
            mock.patch.object(hub, "oauth_client_configuration") as previous,
            mock.patch.object(store, "save_client_configuration") as save,
            mock.patch.object(store, "delete_refresh_token") as delete,
        ):
            with self.assertRaises(hub.GoogleSheetHubError) as caught:
                hub.configure_google_oauth_client_json(
                    desktop_client_json(),
                    expected_client_id=OTHER_CLIENT_ID,
                )
        self.assertEqual(caught.exception.code, "oauth_client_id_mismatch")
        previous.assert_not_called()
        save.assert_not_called()
        delete.assert_not_called()

    def test_changed_client_clears_refresh_and_pending_oauth_flow(self) -> None:
        calls: list[str] = []
        with hub._OAUTH_FLOW_LOCK:
            hub._PENDING_OAUTH_FLOWS["pending-state"] = {"verifier": "private"}
        previous = {
            "clientId": CLIENT_ID,
            "clientSecret": CLIENT_SECRET,
            "source": "secure_store",
        }
        with (
            mock.patch.object(hub, "oauth_client_configuration", return_value=previous),
            mock.patch.object(
                store,
                "save_client_configuration",
                side_effect=lambda *_args: calls.append("save"),
            ) as save,
            mock.patch.object(
                store,
                "delete_refresh_token",
                side_effect=lambda: calls.append("delete") or True,
            ) as delete,
        ):
            result = hub.configure_google_oauth_client_json(
                desktop_client_json(client_id=OTHER_CLIENT_ID)
            )
        save.assert_called_once_with(OTHER_CLIENT_ID, CLIENT_SECRET)
        delete.assert_called_once_with()
        self.assertEqual(calls, ["delete", "save"])
        self.assertTrue(result["authorizationReset"])
        with hub._OAUTH_FLOW_LOCK:
            self.assertEqual(hub._PENDING_OAUTH_FLOWS, {})

    def test_changed_client_never_publishes_new_config_if_refresh_delete_fails(self) -> None:
        previous = {
            "clientId": CLIENT_ID,
            "clientSecret": CLIENT_SECRET,
            "source": "secure_store",
        }
        failure = store.SecureStoreError(
            "secure_store_delete_failed",
            "safe generic delete failure",
        )
        with (
            mock.patch.object(hub, "oauth_client_configuration", return_value=previous),
            mock.patch.object(store, "delete_refresh_token", side_effect=failure) as delete,
            mock.patch.object(store, "save_client_configuration") as save,
        ):
            with self.assertRaises(hub.GoogleSheetHubError) as caught:
                hub.configure_google_oauth_client_json(
                    desktop_client_json(client_id=OTHER_CLIENT_ID)
                )
        self.assertEqual(caught.exception.code, "secure_store_delete_failed")
        delete.assert_called_once_with()
        save.assert_not_called()

    def test_explicit_remove_consumes_pending_flow_and_deletes_refresh_before_client(self) -> None:
        calls: list[str] = []
        with hub._OAUTH_FLOW_LOCK:
            hub._PENDING_OAUTH_FLOWS["pending-state"] = {"verifier": "private"}
        with (
            mock.patch.object(
                store,
                "delete_refresh_token",
                side_effect=lambda: calls.append("refresh") or True,
            ),
            mock.patch.object(
                store,
                "delete_client_configuration",
                side_effect=lambda: calls.append("client") or True,
            ),
        ):
            result = hub.remove_google_oauth_client_configuration({})
        self.assertEqual(calls, ["refresh", "client"])
        self.assertTrue(result["removed"])
        self.assertFalse(result["configured"])
        self.assertNotIn("clientId", result)
        with hub._OAUTH_FLOW_LOCK:
            self.assertEqual(hub._PENDING_OAUTH_FLOWS, {})

        failure = store.SecureStoreError(
            "secure_store_delete_failed",
            "safe generic delete failure",
        )
        with (
            mock.patch.object(store, "delete_refresh_token", side_effect=failure),
            mock.patch.object(store, "delete_client_configuration") as delete_client,
        ):
            with self.assertRaises(hub.GoogleSheetHubError):
                hub.remove_google_oauth_client_configuration({})
        delete_client.assert_not_called()

    def test_stored_client_drives_status_oauth_start_and_refresh_grant(self) -> None:
        stored_client = {"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET}
        captured = []

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _limit: int = -1) -> bytes:
                return b'{"access_token":"SHORT_LIVED_ACCESS"}'

        def open_url(request, timeout=0):
            captured.append((request, timeout))
            return Response()

        with (
            mock.patch.object(store, "load_client_configuration", return_value=stored_client),
            mock.patch.object(
                store,
                "status",
                return_value={"available": True, "stored": True, "status": "ready"},
            ),
            mock.patch.object(store, "load_refresh_token", return_value="STORED_REFRESH"),
        ):
            status = hub.google_oauth_status()
            started = hub.start_google_oauth(
                f"http://127.0.0.1:4191{hub.GOOGLE_OAUTH_CALLBACK_PATH}",
                now_monotonic=10,
            )
            token = hub.access_token(open_url=open_url)

        self.assertTrue(status["clientConfigured"])
        self.assertEqual(status["clientSource"], "secure_store")
        self.assertTrue(status["clientHint"])
        status_json = json.dumps(status)
        self.assertNotIn(CLIENT_ID, status_json)
        self.assertNotIn(CLIENT_SECRET, status_json)
        self.assertIn("client_id=", started["authorizationUrl"])
        self.assertEqual(token, "SHORT_LIVED_ACCESS")
        form = parse_qs(captured[0][0].data.decode("utf-8"))
        self.assertEqual(form["client_id"], [CLIENT_ID])
        self.assertEqual(form["client_secret"], [CLIENT_SECRET])
        self.assertEqual(form["refresh_token"], ["STORED_REFRESH"])

    def test_corrupt_client_store_returns_safe_status_instead_of_raising(self) -> None:
        failure = store.SecureStoreError(
            "secure_store_invalid",
            "PRIVATE_CORRUPT_STORE_DETAIL_MUST_NOT_RETURN",
        )
        with (
            mock.patch.object(store, "load_client_configuration", side_effect=failure),
            mock.patch.object(
                store,
                "status",
                return_value={"available": True, "stored": False, "status": "empty"},
            ),
        ):
            status = hub.google_oauth_status()
        self.assertEqual(status["status"], "secure_store_invalid")
        serialized = json.dumps(status)
        self.assertNotIn("PRIVATE_CORRUPT_STORE_DETAIL", serialized)
        self.assertNotIn("clientId", serialized)


class GoogleOAuthClientCliAndFrontendTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "win32", "Windows DPAPI integration")
    def test_setup_script_and_cli_share_one_isolated_dpapi_store(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected = root / "desktop-client.json"
            selected.write_text(desktop_client_json(), encoding="utf-8")
            local_app_data = root / "LocalAppData"
            environment = dict(os.environ)
            environment["LOCALAPPDATA"] = str(local_app_data)
            setup = subprocess.run(
                [
                    "powershell.exe",
                    "-NoLogo",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(ROOT / "scripts" / "setup-google-oauth.ps1"),
                    "-ClientJsonPath",
                    str(selected),
                    "-SkipBridgeEnsure",
                    "-SkipOpen",
                ],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
            )
            self.assertEqual(setup.returncode, 0, setup.stderr)
            status = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER / "configure_google_oauth_client.py"),
                    "--status",
                ],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
                check=False,
            )
            self.assertEqual(status.returncode, 0, status.stderr)
            safe_status = json.loads(status.stdout)
            self.assertEqual(
                set(safe_status),
                {"ok", "configured", "clientHint", "store"},
            )
            self.assertTrue(safe_status["configured"])
            protected = (
                local_app_data
                / "Metafxclub"
                / "AgentHQ"
                / "credentials"
                / "google-oauth-client.dpapi"
            )
            self.assertTrue(protected.is_file())
            persisted = protected.read_bytes()
            combined_output = setup.stdout + setup.stderr + status.stdout + status.stderr
            for marker in (
                CLIENT_ID,
                CLIENT_SECRET,
                str(selected),
            ):
                self.assertNotIn(marker.encode("utf-8"), persisted)
                self.assertNotIn(marker, combined_output)
            legacy_duplicate = (
                local_app_data
                / "Metafxclub"
                / "AI-Agent-HQ-Auth"
                / "google-oauth-client.dpapi"
            )
            self.assertFalse(legacy_duplicate.exists())

            with mock.patch.dict(os.environ, {"LOCALAPPDATA": str(local_app_data)}):
                store.save_refresh_token("TEST_ONLY_DURABLE_REFRESH_MARKER")
                refresh_path = store.credential_path()
            self.assertTrue(refresh_path.is_file())
            removed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER / "configure_google_oauth_client.py"),
                    "--remove",
                ],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
                check=False,
            )
            self.assertEqual(removed.returncode, 0, removed.stderr)
            remove_status = json.loads(removed.stdout)
            self.assertEqual(
                set(remove_status),
                {"ok", "configured", "clientHint", "store", "removed"},
            )
            self.assertTrue(remove_status["removed"])
            self.assertFalse(protected.exists())
            self.assertFalse(refresh_path.exists())
            self.assertNotIn(CLIENT_ID, removed.stdout + removed.stderr)
            self.assertNotIn(CLIENT_SECRET, removed.stdout + removed.stderr)

    def test_cli_file_and_status_output_only_safe_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            selected = Path(directory) / "downloaded-client.json"
            selected.write_text(desktop_client_json(), encoding="utf-8")
            output = io.StringIO()
            with (
                mock.patch.object(
                    cli.google_sheet_hub,
                    "configure_google_oauth_client_json",
                    return_value={"clientHint": "14999189…umajd"},
                ),
                redirect_stdout(output),
            ):
                exit_code = cli.main(["--file", str(selected)])
            self.assertEqual(exit_code, 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(
                set(payload),
                {"ok", "configured", "clientHint", "store"},
            )
            serialized = output.getvalue()
            self.assertNotIn(CLIENT_ID, serialized)
            self.assertNotIn(CLIENT_SECRET, serialized)
            self.assertNotIn(str(selected), serialized)

            output.seek(0)
            output.truncate(0)
            with (
                mock.patch.object(
                    cli.google_sheet_hub,
                    "configure_google_oauth_client_json",
                    return_value={"clientHint": "14999189…umajd"},
                ) as configure,
                redirect_stdout(output),
            ):
                exit_code = cli.main(
                    [
                        "--file",
                        str(selected),
                        "--expected-client-id",
                        CLIENT_ID,
                    ]
                )
            self.assertEqual(exit_code, 0)
            configure.assert_called_once()
            self.assertEqual(configure.call_args.kwargs["expected_client_id"], CLIENT_ID)
            self.assertNotIn(CLIENT_ID, output.getvalue())
            self.assertNotIn(CLIENT_SECRET, output.getvalue())

        output = io.StringIO()
        with (
            mock.patch.object(
                cli.google_sheet_hub,
                "oauth_client_configuration",
                return_value={"clientId": CLIENT_ID, "source": "secure_store"},
            ),
            redirect_stdout(output),
        ):
            self.assertEqual(cli.main(["--status"]), 0)
        status = json.loads(output.getvalue())
        self.assertTrue(status["configured"])
        self.assertNotIn(CLIENT_ID, output.getvalue())

    def test_frontend_receives_only_safe_client_status_and_connect_action(self) -> None:
        source = (ROOT / "frontend" / "src" / "app" / "main.js").read_text(
            encoding="utf-8"
        )
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        auth_start = html.index('id="researchSheetGoogleAuth"')
        auth_end = html.index("</section>", auth_start)
        auth_markup = html[auth_start:auth_end]
        self.assertIn("clientHint", source)
        self.assertIn("clientSource", source)
        self.assertIn("Credential ไม่ผ่าน Browser", source)
        self.assertNotIn('type="file"', auth_markup)
        self.assertNotIn("oauthClientJson", source)
        self.assertIn("researchSheetGoogleConnect", auth_markup)


if __name__ == "__main__":
    unittest.main()
