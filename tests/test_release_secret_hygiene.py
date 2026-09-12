from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.release_secret_scan import find_sensitive_filenames, scan_embedded_secrets


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ReleaseSecretHygieneTests(unittest.TestCase):
    def test_distributed_tree_has_no_embedded_high_confidence_secrets(self) -> None:
        self.assertEqual(scan_embedded_secrets(PROJECT_ROOT), [])

    def test_distributed_tree_has_no_sensitive_credential_files(self) -> None:
        self.assertEqual(find_sensitive_filenames(PROJECT_ROOT), [])

    def test_google_oauth_json_and_dpapi_names_are_ignored(self) -> None:
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8-sig")
        for rule in (
            "**/client_secret*.json",
            "**/*secret*.json",
            "**/*oauth*client*.json",
            "**/*google*oauth*.json",
            "**/service-account*.json",
            "**/service_account*.json",
            "*.dpapi",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, gitignore)

    def test_scanner_reports_rule_and_path_without_secret_value(self) -> None:
        synthetic_secret = "GOC" + "SPX-" + ("A" * 24)
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "backend" / "example.py"
            target.parent.mkdir(parents=True)
            target.write_text("value = " + repr(synthetic_secret), encoding="utf-8")
            findings = scan_embedded_secrets(root)

        self.assertEqual(findings, [("backend/example.py", "google_oauth_client_secret")])
        self.assertNotIn(synthetic_secret, repr(findings))

    def test_scanner_detects_google_access_token_without_echoing_it(self) -> None:
        synthetic_token = "ya" + "29." + ("A" * 32)
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "frontend" / "leaked-token.js"
            target.parent.mkdir(parents=True)
            target.write_text("const value = " + repr(synthetic_token), encoding="utf-8")
            findings = scan_embedded_secrets(root)

        self.assertEqual(findings, [("frontend/leaked-token.js", "google_access_token")])
        self.assertNotIn(synthetic_token, repr(findings))

    def test_central_native_client_exception_requires_explicit_staged_release_mode(self) -> None:
        synthetic_secret = "GOC" + "SPX-" + ("C" * 24)
        payload = (
            "client_id=123456789012-central.apps.googleusercontent.com\n"
            f"client_secret={synthetic_secret}\n"
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "backend" / "local-runner" / "google_oauth_native_client.txt"
            target.parent.mkdir(parents=True)
            target.write_text(payload, encoding="utf-8")

            self.assertEqual(find_sensitive_filenames(root), [])
            self.assertEqual(
                scan_embedded_secrets(root),
                [
                    (
                        "backend/local-runner/google_oauth_native_client.txt",
                        "google_oauth_client_secret",
                    )
                ],
            )
            self.assertEqual(
                scan_embedded_secrets(
                    root,
                    allow_central_native_client=True,
                ),
                [],
            )

            copied = root / "frontend" / "native-client.txt"
            copied.parent.mkdir(parents=True)
            copied.write_text(payload, encoding="utf-8")
            findings = scan_embedded_secrets(
                root,
                allow_central_native_client=True,
            )

        self.assertEqual(
            findings,
            [
                ("frontend/native-client.txt", "central_google_oauth_client_id_copy"),
                ("frontend/native-client.txt", "google_oauth_client_secret"),
            ],
        )
        self.assertNotIn(synthetic_secret, repr(findings))

    def test_scanner_rejects_full_central_client_id_copied_to_frontend(self) -> None:
        synthetic_secret = "GOC" + "SPX-" + ("E" * 24)
        client_id = "123456789012-central.apps.googleusercontent.com"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            central = root / "backend" / "local-runner" / "google_oauth_native_client.txt"
            central.parent.mkdir(parents=True)
            central.write_text(
                f"client_id={client_id}\nclient_secret={synthetic_secret}\n",
                encoding="utf-8",
            )
            frontend = root / "frontend" / "app.js"
            frontend.parent.mkdir(parents=True)
            frontend.write_text("const client = " + repr(client_id), encoding="utf-8")
            findings = scan_embedded_secrets(
                root,
                allow_central_native_client=True,
            )

        self.assertEqual(
            findings,
            [("frontend/app.js", "central_google_oauth_client_id_copy")],
        )
        self.assertFalse(
            client_id in repr(findings) or synthetic_secret in repr(findings),
            "scanner findings echoed central native client values",
        )

    def test_malformed_central_native_client_file_is_rejected_without_echoing_it(self) -> None:
        synthetic_secret = "GOC" + "SPX-" + ("D" * 24)
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "backend" / "local-runner" / "google_oauth_native_client.txt"
            target.parent.mkdir(parents=True)
            target.write_text(
                "client_id=123456789012-central.apps.googleusercontent.com\n"
                f"client_secret={synthetic_secret}\n"
                "unexpected=extra-line\n",
                encoding="utf-8",
            )
            findings = scan_embedded_secrets(
                root,
                allow_central_native_client=True,
            )

        self.assertEqual(
            findings,
            [
                (
                    "backend/local-runner/google_oauth_native_client.txt",
                    "google_oauth_client_secret",
                ),
                (
                    "backend/local-runner/google_oauth_native_client.txt",
                    "invalid_central_google_oauth_native_client",
                ),
            ],
        )
        self.assertNotIn(synthetic_secret, repr(findings))

    def test_staged_release_exception_never_allows_user_tokens(self) -> None:
        synthetic_secret = "GOC" + "SPX-" + ("F" * 24)
        refresh_token = "1" + "//" + ("R" * 32)
        access_token = "ya" + "29." + ("A" * 32)
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            central = root / "backend" / "local-runner" / "google_oauth_native_client.txt"
            central.parent.mkdir(parents=True)
            central.write_text(
                "client_id=123456789012-central.apps.googleusercontent.com\n"
                f"client_secret={synthetic_secret}\n",
                encoding="utf-8",
            )
            runtime = root / "backend" / "runtime.txt"
            runtime.write_text(
                f"refresh={refresh_token}\naccess={access_token}\n",
                encoding="utf-8",
            )
            findings = scan_embedded_secrets(
                root,
                allow_central_native_client=True,
            )

        self.assertEqual(
            findings,
            [
                ("backend/runtime.txt", "google_access_token"),
                ("backend/runtime.txt", "google_refresh_token"),
            ],
        )
        self.assertNotIn(refresh_token, repr(findings))
        self.assertNotIn(access_token, repr(findings))

    def test_scanner_includes_curated_release_artifacts(self) -> None:
        synthetic_secret = "GOC" + "SPX-" + ("B" * 24)
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "artifacts" / "example-release" / "BUILD_LOG.txt"
            target.parent.mkdir(parents=True)
            target.write_text("credential=" + synthetic_secret, encoding="utf-8")
            findings = scan_embedded_secrets(root)

        self.assertEqual(
            findings,
            [("artifacts/example-release/BUILD_LOG.txt", "google_oauth_client_secret")],
        )
        self.assertNotIn(synthetic_secret, repr(findings))

    def test_scanner_rejects_oauth_json_filename_without_reading_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "backend" / "client_secret_download.json"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"not-json-and-must-not-be-read-as-a-credential")
            findings = find_sensitive_filenames(root)

        self.assertEqual(findings, [("backend/client_secret_download.json", "oauth_client_json")])

    def test_scanner_allows_security_source_names_but_rejects_secret_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            tests = root / "tests"
            tests.mkdir(parents=True)
            (tests / "release_secret_scan.py").write_text("# scanner", encoding="utf-8")
            (tests / "test_release_secret_hygiene.py").write_text("# tests", encoding="utf-8")
            self.assertEqual(find_sensitive_filenames(root), [])

            credential = root / "backend" / "student-secret-backup.json"
            credential.parent.mkdir(parents=True)
            credential.write_text("{}", encoding="utf-8")
            findings = find_sensitive_filenames(root)

        self.assertEqual(findings, [("backend/student-secret-backup.json", "sensitive_json")])

    def test_scanner_detects_renamed_google_oauth_json_by_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "backend" / "settings.json"
            target.parent.mkdir(parents=True)
            target.write_text(
                json.dumps(
                    {
                        "installed": {
                            "client_id": "public-client.apps.googleusercontent.com",
                            "client_secret": "legacy-format-value",
                        }
                    }
                ),
                encoding="utf-8",
            )
            findings = scan_embedded_secrets(root)

        self.assertEqual(findings, [("backend/settings.json", "google_oauth_client_json")])


if __name__ == "__main__":
    unittest.main()
