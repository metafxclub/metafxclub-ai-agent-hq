from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HUB_PATH = PROJECT_ROOT / "backend" / "local-runner" / "hq_backend" / "google" / "google_sheet_hub.py"
LOCAL_RUNNER = PROJECT_ROOT / "backend" / "local-runner"


def load_hub():
    spec = importlib.util.spec_from_file_location(
        "metafx_google_sheet_credential_binding_tests",
        HUB_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {HUB_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
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

    def __exit__(self, _exc_type, _exc, _traceback):
        return False

    def read(self, _limit: int = -1) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class GoogleSheetCredentialBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.hub = load_hub()

    def test_direct_access_token_binding_is_exact_opaque_and_not_json_serializable(self) -> None:
        first = self.hub.credential_binding_snapshot(
            {"METAFX_GOOGLE_SHEETS_ACCESS_TOKEN": "ya29.account-a-token"}
        )
        same = self.hub.credential_binding_snapshot(
            {"METAFX_GOOGLE_SHEETS_ACCESS_TOKEN": "ya29.account-a-token"}
        )
        changed = self.hub.credential_binding_snapshot(
            {"METAFX_GOOGLE_SHEETS_ACCESS_TOKEN": "ya29.account-b-token"}
        )

        self.assertEqual(first, same)
        self.assertNotEqual(first, changed)
        self.assertEqual(repr(first), "<google-credential-binding-redacted>")
        self.assertNotIn("account-a", repr(first))
        with self.assertRaises(TypeError):
            json.dumps(first)

    def test_direct_access_token_takes_precedence_over_unrelated_oauth_values(self) -> None:
        first = self.hub.credential_binding_snapshot(
            {
                "METAFX_GOOGLE_SHEETS_ACCESS_TOKEN": "same-direct-token",
                "METAFX_GOOGLE_OAUTH_CLIENT_ID": "old.apps.googleusercontent.com",
                "METAFX_GOOGLE_OAUTH_CLIENT_SECRET": "old-secret",
                "METAFX_GOOGLE_OAUTH_REFRESH_TOKEN": "old-refresh",
            }
        )
        second = self.hub.credential_binding_snapshot(
            {
                "METAFX_GOOGLE_SHEETS_ACCESS_TOKEN": "same-direct-token",
                "METAFX_GOOGLE_OAUTH_CLIENT_ID": "new.apps.googleusercontent.com",
                "METAFX_GOOGLE_OAUTH_CLIENT_SECRET": "new-secret",
                "METAFX_GOOGLE_OAUTH_REFRESH_TOKEN": "new-refresh",
            }
        )
        self.assertEqual(first, second)

    def test_environment_refresh_binding_changes_with_client_or_grant(self) -> None:
        base = {
            "METAFX_GOOGLE_OAUTH_CLIENT_ID": "client.apps.googleusercontent.com",
            "METAFX_GOOGLE_OAUTH_CLIENT_SECRET": "client-secret-a",
            "METAFX_GOOGLE_OAUTH_REFRESH_TOKEN": "refresh-account-a",
        }
        same = dict(base)
        changed_secret = {**base, "METAFX_GOOGLE_OAUTH_CLIENT_SECRET": "client-secret-b"}
        changed_refresh = {**base, "METAFX_GOOGLE_OAUTH_REFRESH_TOKEN": "refresh-account-b"}

        snapshot = self.hub.credential_binding_snapshot(base)
        self.assertEqual(snapshot, self.hub.credential_binding_snapshot(same))
        self.assertNotEqual(
            snapshot,
            self.hub.credential_binding_snapshot(changed_secret),
        )
        self.assertNotEqual(
            snapshot,
            self.hub.credential_binding_snapshot(changed_refresh),
        )

    def test_explicit_environment_never_falls_through_to_durable_store(self) -> None:
        with mock.patch.object(
            self.hub.google_oauth_store,
            "load_refresh_token",
        ) as load_refresh:
            with self.assertRaises(self.hub.GoogleSheetHubError) as caught:
                self.hub.credential_binding_snapshot(
                    {
                        "METAFX_GOOGLE_OAUTH_CLIENT_ID": (
                            "client.apps.googleusercontent.com"
                        )
                    }
                )

        self.assertEqual(caught.exception.code, "auth_required")
        load_refresh.assert_not_called()

    def test_stored_refresh_binding_samples_client_and_token_in_one_transaction(self) -> None:
        client = {
            "clientId": "client.apps.googleusercontent.com",
            "clientSecret": "not-exposed",
            "clientGeneration": "a" * 64,
            "source": "central_release",
        }
        transaction = mock.Mock(side_effect=lambda **_kwargs: nullcontext())
        with mock.patch.object(
            self.hub.google_oauth_store,
            "oauth_store_transaction",
            transaction,
        ), mock.patch.object(
            self.hub,
            "_runtime_oauth_environment",
            return_value={},
        ), mock.patch.object(
            self.hub,
            "oauth_client_configuration",
            return_value=client,
        ), mock.patch.object(
            self.hub.google_oauth_store,
            "load_refresh_token",
            side_effect=["refresh-a", "refresh-a", "refresh-b"],
        ) as load_refresh:
            first = self.hub.credential_binding_snapshot()
            same = self.hub.credential_binding_snapshot()
            changed = self.hub.credential_binding_snapshot()

        self.assertEqual(first, same)
        self.assertNotEqual(first, changed)
        self.assertEqual(transaction.call_count, 3)
        self.assertEqual(load_refresh.call_count, 3)
        for call in load_refresh.call_args_list:
            self.assertEqual(
                call.kwargs["expected_client_generation"],
                "a" * 64,
            )

    def test_secure_store_errors_are_classified_without_secret_text(self) -> None:
        store_error = self.hub.google_oauth_store.SecureStoreError(
            "secure_store_busy",
            "Credential store is busy.",
        )
        with mock.patch.object(
            self.hub.google_oauth_store,
            "oauth_store_transaction",
            side_effect=store_error,
        ):
            with self.assertRaises(self.hub.GoogleSheetHubError) as caught:
                self.hub.credential_binding_snapshot()

        self.assertEqual(caught.exception.code, "secure_store_busy")
        self.assertEqual(caught.exception.status, 503)

    def test_expected_binding_blocks_mismatched_direct_token_before_http(self) -> None:
        expected = self.hub.credential_binding_snapshot(
            {"METAFX_GOOGLE_SHEETS_ACCESS_TOKEN": "access-account-a"}
        )
        opener = mock.Mock(
            side_effect=AssertionError("mismatched credential reached HTTP")
        )

        with self.assertRaises(self.hub.GoogleSheetHubError) as caught:
            self.hub.api_request(
                "A" * 24,
                environ={
                    "METAFX_GOOGLE_SHEETS_ACCESS_TOKEN": "access-account-b"
                },
                open_url=opener,
                expected_credential_binding=expected,
            )

        self.assertEqual(caught.exception.code, "oauth_credential_changed")
        self.assertEqual(caught.exception.status, 409)
        self.assertNotIn("account-a", str(caught.exception))
        self.assertNotIn("account-b", str(caught.exception))
        opener.assert_not_called()

    def test_read_values_enforces_expected_binding_on_every_aba_request(self) -> None:
        account_a = {
            "METAFX_GOOGLE_SHEETS_ACCESS_TOKEN": "access-account-a"
        }
        account_b = {
            "METAFX_GOOGLE_SHEETS_ACCESS_TOKEN": "access-account-b"
        }
        expected = self.hub.credential_binding_snapshot(account_a)
        authorizations: list[str] = []

        def open_url(request, timeout: int):
            authorizations.append(str(request.headers.get("Authorization") or ""))
            return FakeJsonResponse({"values": [["system_name"], ["Alpha"]]})

        first = self.hub.read_values(
            "B" * 24,
            "Deep_Research",
            "B:B",
            environ=account_a,
            open_url=open_url,
            expected_credential_binding=expected,
        )
        with self.assertRaises(self.hub.GoogleSheetHubError) as caught:
            self.hub.read_values(
                "B" * 24,
                "Deep_Research",
                "B:B",
                environ=account_b,
                open_url=open_url,
                expected_credential_binding=expected,
            )
        third = self.hub.read_values(
            "B" * 24,
            "Deep_Research",
            "B:B",
            environ=account_a,
            open_url=open_url,
            expected_credential_binding=expected,
        )

        self.assertEqual(caught.exception.code, "oauth_credential_changed")
        self.assertEqual(first, [["system_name"], ["Alpha"]])
        self.assertEqual(third, first)
        self.assertEqual(
            authorizations,
            ["Bearer access-account-a", "Bearer access-account-a"],
        )

    def test_environment_refresh_mismatch_stops_before_sheets_http(self) -> None:
        account_a = {
            "METAFX_GOOGLE_OAUTH_CLIENT_ID": (
                "client.apps.googleusercontent.com"
            ),
            "METAFX_GOOGLE_OAUTH_CLIENT_SECRET": "client-secret",
            "METAFX_GOOGLE_OAUTH_REFRESH_TOKEN": "refresh-account-a",
        }
        account_b = {
            **account_a,
            "METAFX_GOOGLE_OAUTH_REFRESH_TOKEN": "refresh-account-b",
        }
        expected = self.hub.credential_binding_snapshot(account_a)
        requested_urls: list[str] = []

        def open_url(request, timeout: int):
            requested_urls.append(request.full_url)
            if request.full_url == self.hub.GOOGLE_TOKEN_URL:
                return FakeJsonResponse({"access_token": "access-account-b"})
            raise AssertionError("mismatched refresh grant reached Sheets HTTP")

        with self.assertRaises(self.hub.GoogleSheetHubError) as caught:
            self.hub.api_request(
                "C" * 24,
                environ=account_b,
                open_url=open_url,
                expected_credential_binding=expected,
            )

        self.assertEqual(caught.exception.code, "oauth_credential_changed")
        self.assertEqual(requested_urls, [self.hub.GOOGLE_TOKEN_URL])


if __name__ == "__main__":
    unittest.main()
