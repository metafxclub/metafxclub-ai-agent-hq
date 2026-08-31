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
