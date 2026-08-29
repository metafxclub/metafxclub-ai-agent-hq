from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

from tests.release_secret_scan import find_sensitive_filenames, scan_embedded_secrets


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ReleaseCandidatePreflightTests(unittest.TestCase):
    """Dependency-free checks that are safe before the installed venv exists."""

    def test_required_student_release_files_are_present(self) -> None:
        required = (
            ".gitattributes",
            ".gitignore",
            "VERSION",
            "README.md",
            "STUDENT-QUICKSTART-TH.md",
            "installer/install.ps1",
            "2-SETUP-GOOGLE-HQ.bat",
            "docs/prompts/install-github-google-auto-th.md",
            "backend/local-runner/bridge_server.py",
            "backend/local-runner/configure_google_oauth_client.py",
            "backend/local-runner/google_oauth_store.py",
            "backend/local-runner/google_sheet_hub.py",
            "frontend/index.html",
            "frontend/src/app/main.js",
            "runner/codex_cli_runner.py",
            "scripts/start-local-bridge.ps1",
            "scripts/setup-google-oauth.ps1",
            "docs/research-sheet-hub-setup-th.md",
            "contracts/workflows/ea-factory-contract.json",
        )
        missing = [path for path in required if not (PROJECT_ROOT / path).is_file()]
        self.assertEqual(missing, [])

    def test_release_tree_contains_no_secret_material_or_credential_files(self) -> None:
        # Findings intentionally contain only a relative path and a rule name;
        # never echo matching content into installer or GitHub Actions logs.
        self.assertEqual(find_sensitive_filenames(PROJECT_ROOT), [])
        self.assertEqual(scan_embedded_secrets(PROJECT_ROOT), [])

    def test_all_distributed_python_sources_compile_without_importing(self) -> None:
        paths = [
            path
            for root in ("backend", "runner", "tests")
            for path in (PROJECT_ROOT / root).rglob("*.py")
            if not {".venv", "__pycache__"}.intersection(path.parts)
        ]
        self.assertGreater(len(paths), 20)
        for path in paths:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                source = path.read_text(encoding="utf-8-sig")
                compile(source, str(path), "exec", dont_inherit=True)

    def test_all_distributed_json_contracts_parse(self) -> None:
        paths = sorted((PROJECT_ROOT / "contracts").rglob("*.json"))
        self.assertGreater(len(paths), 10)
        for path in paths:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                json.loads(path.read_text(encoding="utf-8-sig"))

    def test_all_distributed_powershell_scripts_parse(self) -> None:
        scripts = sorted(
            path
            for root in ("installer", "scripts")
            for path in (PROJECT_ROOT / root).rglob("*.ps1")
        )
        self.assertGreater(len(scripts), 2)
        parser = (
            "$tokens=$null; $errors=$null; "
            "[void][Management.Automation.Language.Parser]::ParseFile("
            "$env:METAFX_PS_PARSE_PATH,[ref]$tokens,[ref]$errors); "
            "if($errors.Count -gt 0){$errors | ForEach-Object {Write-Error $_.Message}; exit 1}"
        )
        for path in scripts:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                environment = os.environ.copy()
                environment["METAFX_PS_PARSE_PATH"] = str(path)
                result = subprocess.run(
                    [
                        "powershell.exe",
                        "-NoLogo",
                        "-NoProfile",
                        "-NonInteractive",
                        "-Command",
                        parser,
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=20,
                    check=False,
                    env=environment,
                )
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
