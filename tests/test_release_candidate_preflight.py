from __future__ import annotations

import json
import os
import re
import subprocess
import unittest
from pathlib import Path

from tests.release_secret_scan import find_sensitive_filenames, scan_embedded_secrets


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CENTRAL_NATIVE_CLIENT_RELATIVE_PATH = (
    Path("backend") / "local-runner" / "google_oauth_native_client.txt"
)
CENTRAL_NATIVE_CLIENT_PATH = PROJECT_ROOT / CENTRAL_NATIVE_CLIENT_RELATIVE_PATH


def _is_source_checkout() -> bool:
    return (PROJECT_ROOT / ".git").exists()


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
            "backend/local-runner/ea_factory_blueprint_coverage.py",
            "backend/local-runner/ea_factory_visible_terminal.py",
            "backend/local-runner/ea_factory_visible_terminal.ps1",
            "backend/local-runner/ea_research_blueprint.py",
            "backend/local-runner/ea_strategy_brief.py",
            "backend/local-runner/configure_google_oauth_client.py",
            "backend/local-runner/google_oauth_store.py",
            "backend/local-runner/google_sheet_hub.py",
            "frontend/index.html",
            "frontend/src/app/main.js",
            "runner/codex_cli_runner.py",
            "scripts/start-local-bridge.ps1",
            "scripts/setup-google-oauth.ps1",
            "docs/research-sheet-hub-setup-th.md",
            "contracts/research/ea-implementation-blueprint-v2.schema.json",
            "contracts/workflows/ea-factory-contract.json",
        )
        if not _is_source_checkout():
            required += (CENTRAL_NATIVE_CLIENT_RELATIVE_PATH.as_posix(),)
        missing = [path for path in required if not (PROJECT_ROOT / path).is_file()]
        self.assertEqual(missing, [])

    def test_central_google_oauth_native_client_is_release_only_and_exact(self) -> None:
        if _is_source_checkout():
            self.assertFalse(
                CENTRAL_NATIVE_CLIENT_PATH.exists(),
                "real central OAuth material may be injected only after source checkout",
            )
            ignored = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8-sig")
            self.assertRegex(
                ignored,
                r"(?m)^/?backend/local-runner/google_oauth_native_client\.txt$",
            )
            tracked = subprocess.run(
                [
                    "git",
                    "-c",
                    f"safe.directory={PROJECT_ROOT.as_posix()}",
                    "ls-files",
                    "--",
                    CENTRAL_NATIVE_CLIENT_RELATIVE_PATH.as_posix(),
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=20,
                check=False,
            )
            self.assertEqual(tracked.returncode, 0, tracked.stderr)
            self.assertEqual(tracked.stdout.strip(), "")
            return

        raw = CENTRAL_NATIVE_CLIENT_PATH.read_text(encoding="utf-8")
        lines = raw.splitlines()

        self.assertLessEqual(len(raw.encode("utf-8")), 4096)
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("client_id="))
        self.assertTrue(lines[1].startswith("client_secret="))
        client_id = lines[0].removeprefix("client_id=")
        client_secret = lines[1].removeprefix("client_secret=")
        self.assertRegex(
            client_id,
            r"^[A-Za-z0-9][A-Za-z0-9._-]{8,240}\.apps\.googleusercontent\.com$",
        )
        self.assertRegex(client_secret, r"^GOCSPX-[A-Za-z0-9_-]{16,}$")
        for prohibited in ("access_token", "refresh_token", "1//", "ya29.", "{", "}"):
            with self.subTest(prohibited=prohibited):
                self.assertNotIn(prohibited, raw)

    def test_release_tree_contains_no_secret_material_or_credential_files(self) -> None:
        # Findings intentionally contain only a relative path and a rule name;
        # never echo matching content into installer or GitHub Actions logs.
        self.assertEqual(find_sensitive_filenames(PROJECT_ROOT), [])
        self.assertEqual(
            scan_embedded_secrets(
                PROJECT_ROOT,
                allow_central_native_client=not _is_source_checkout(),
            ),
            [],
        )

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

    def test_codex_sdk_and_cli_use_the_verified_matching_release(self) -> None:
        requirements = (PROJECT_ROOT / "requirements-runner.txt").read_text(
            encoding="utf-8-sig"
        )

        def pinned_version(package: str) -> str:
            match = re.search(
                rf"(?m)^{re.escape(package)}==([^\s\\]+)\s*\\$",
                requirements,
            )
            self.assertIsNotNone(match, f"missing exact {package} pin")
            return match.group(1)

        sdk_version = pinned_version("openai-codex")
        cli_version = pinned_version("openai-codex-cli-bin")
        self.assertEqual(
            sdk_version,
            cli_version,
            "Codex Python SDK and bundled CLI must use the same app-server protocol release",
        )
        numeric = tuple(int(part) for part in sdk_version.split("."))
        self.assertGreaterEqual(
            numeric,
            (0, 147, 0),
            "older Codex runtimes cannot parse the current model catalog",
        )

    def test_ea_research_schema_local_references_resolve(self) -> None:
        path = (
            PROJECT_ROOT
            / "contracts"
            / "research"
            / "ea-implementation-blueprint-v2.schema.json"
        )
        schema = json.loads(path.read_text(encoding="utf-8-sig"))
        references: list[str] = []

        def collect(value: object) -> None:
            if isinstance(value, dict):
                reference = value.get("$ref")
                if isinstance(reference, str):
                    references.append(reference)
                for item in value.values():
                    collect(item)
            elif isinstance(value, list):
                for item in value:
                    collect(item)

        collect(schema)
        self.assertGreater(len(references), 100)
        for reference in references:
            with self.subTest(reference=reference):
                self.assertTrue(reference.startswith("#/"))
                current: object = schema
                for raw_token in reference[2:].split("/"):
                    token = raw_token.replace("~1", "/").replace("~0", "~")
                    self.assertIsInstance(current, dict)
                    current = current[token]

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
