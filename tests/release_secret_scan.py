"""Dependency-free secret hygiene checks for the student release tree.

The scanner intentionally returns only a relative path and a rule name. It
must never include matching text because this module is used by installer
preflight and GitHub Actions, where output can become a public log.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


DISTRIBUTED_ROOTS = (
    ".github",
    "artifacts",
    "backend",
    "contracts",
    "docs",
    "frontend",
    "installer",
    "integrations",
    "runner",
    "scripts",
    "tests",
)
ROOT_TEXT_FILES = (
    ".env.example",
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "SECURITY.md",
    "STUDENT-QUICKSTART-TH.md",
    "requirements-runner.txt",
)
SKIPPED_DIRECTORIES = {
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}
TEXT_SUFFIXES = {
    ".bat",
    ".cmd",
    ".css",
    ".csv",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mq4",
    ".mq5",
    ".mqh",
    ".ps1",
    ".py",
    ".txt",
    ".vbs",
    ".yaml",
    ".yml",
}
MAX_TEXT_BYTES = 8 * 1024 * 1024
CENTRAL_GOOGLE_OAUTH_NATIVE_CLIENT_PATH = (
    "backend/local-runner/google_oauth_native_client.txt"
)
CENTRAL_GOOGLE_OAUTH_CLIENT_ID_PATTERN = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._-]{8,240}\.apps\.googleusercontent\.com"
)
CENTRAL_GOOGLE_OAUTH_CLIENT_SECRET_PATTERN = re.compile(
    r"GOCSPX-[A-Za-z0-9_-]{16,}"
)


HIGH_CONFIDENCE_PATTERNS = (
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("google_oauth_client_secret", re.compile(r"(?<![A-Za-z0-9])GOCSPX-[A-Za-z0-9_-]{16,}")),
    ("google_refresh_token", re.compile(r"(?<![A-Za-z0-9])1//[A-Za-z0-9_-]{20,}")),
    ("google_access_token", re.compile(r"(?<![A-Za-z0-9])ya29\.[A-Za-z0-9._~-]{20,}")),
    ("google_api_key", re.compile(r"(?<![A-Za-z0-9])AIza[0-9A-Za-z_-]{30,}")),
    ("github_token", re.compile(r"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{30,}")),
    ("github_fine_grained_token", re.compile(r"(?<![A-Za-z0-9])github_pat_[A-Za-z0-9_]{20,}")),
    ("openai_style_key", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{32,}")),
    ("slack_token", re.compile(r"(?<![A-Za-z0-9])xox[baprs]-[A-Za-z0-9-]{20,}")),
    ("aws_access_key", re.compile(r"(?<![A-Z0-9])AKIA[A-Z0-9]{16}(?![A-Z0-9])")),
    ("telegram_bot_token", re.compile(r"(?<![0-9])\d{8,10}:[A-Za-z0-9_-]{35}(?![A-Za-z0-9_-])")),
    ("jwt", re.compile(r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("npm_token", re.compile(r"(?<![A-Za-z0-9])npm_[A-Za-z0-9]{20,}")),
)


SENSITIVE_FILENAMES = (
    ("oauth_client_json", re.compile(r"(?i)(?:^|[._-])client[._-]?secret.*\.json$")),
    ("oauth_client_json", re.compile(r"(?i).*oauth.*client.*\.json$")),
    ("oauth_client_json", re.compile(r"(?i).*google.*oauth.*\.json$")),
    ("service_account_json", re.compile(r"(?i)service[._-]?account.*\.json$")),
    ("credential_json", re.compile(r"(?i)(?:credentials?|application_default_credentials)\.json$")),
    ("auth_json", re.compile(r"(?i)(?:auth|tokens?|cookies)\.json$")),
    ("sensitive_json", re.compile(r"(?i).*(?:token|credential|cookie|secret).*\.json$")),
    ("environment_file", re.compile(r"(?i)\.env(?:\..+)?$")),
    ("dpapi_credential", re.compile(r"(?i).*\.dpapi$")),
    ("private_key_file", re.compile(r"(?i).*(?:\.key|\.pem|\.p12|\.pfx)$")),
)


def _valid_central_google_oauth_native_client(content: str) -> bool:
    """Allow one installed-app credential file, and no broader exception.

    Google Desktop/native clients are public installed applications.  Their
    client secret is shipped application configuration rather than a user
    confidentiality boundary, but it is still confined to this exact file so
    it cannot drift into frontend code, docs, logs, or arbitrary artifacts.
    """

    if len(content.encode("utf-8")) > 4096:
        return False
    lines = content.splitlines()
    if len(lines) != 2:
        return False
    if not lines[0].startswith("client_id=") or not lines[1].startswith(
        "client_secret="
    ):
        return False
    client_id = lines[0].removeprefix("client_id=")
    client_secret = lines[1].removeprefix("client_secret=")
    return bool(
        CENTRAL_GOOGLE_OAUTH_CLIENT_ID_PATTERN.fullmatch(client_id)
        and CENTRAL_GOOGLE_OAUTH_CLIENT_SECRET_PATTERN.fullmatch(client_secret)
    )


def _central_google_oauth_client_id(root: Path) -> str:
    path = root / CENTRAL_GOOGLE_OAUTH_NATIVE_CLIENT_PATH
    try:
        if path.stat().st_size > 4096:
            return ""
        content = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return ""
    if not _valid_central_google_oauth_native_client(content):
        return ""
    return content.splitlines()[0].removeprefix("client_id=")


def _distributed_files(root: Path):
    seen: set[Path] = set()
    for relative_root in DISTRIBUTED_ROOTS:
        base = root / relative_root
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or SKIPPED_DIRECTORIES.intersection(path.parts):
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield path
    for relative_path in ROOT_TEXT_FILES:
        path = root / relative_path
        if path.is_file() and path.resolve() not in seen:
            yield path


def find_sensitive_filenames(root: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for path in _distributed_files(root):
        if path.name.lower() == ".env.example":
            continue
        for rule, pattern in SENSITIVE_FILENAMES:
            if pattern.fullmatch(path.name):
                findings.append((path.relative_to(root).as_posix(), rule))
                break
    return sorted(set(findings))


def scan_embedded_secrets(
    root: Path,
    *,
    allow_central_native_client: bool = False,
) -> list[tuple[str, str]]:
    """Scan distributed text without returning any matched secret value.

    Source scans are strict by default: even the canonical native-client path
    may not contain a real Google client secret in a Git checkout.  Release
    packaging may opt into the narrowly scoped exception only after injecting
    the validated two-line native-client file into an extracted/staged tree.
    """

    findings: list[tuple[str, str]] = []
    central_client_id = _central_google_oauth_client_id(root)
    for path in _distributed_files(root):
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in ROOT_TEXT_FILES:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            findings.append((path.relative_to(root).as_posix(), "unreadable_release_file"))
            continue
        if size > MAX_TEXT_BYTES:
            findings.append((path.relative_to(root).as_posix(), "oversized_text_file"))
            continue
        try:
            content = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            findings.append((path.relative_to(root).as_posix(), "unreadable_release_text"))
            continue
        relative_path = path.relative_to(root).as_posix()
        valid_central_native_client_schema = (
            relative_path == CENTRAL_GOOGLE_OAUTH_NATIVE_CLIENT_PATH
            and _valid_central_google_oauth_native_client(content)
        )
        allowed_central_native_client = (
            allow_central_native_client and valid_central_native_client_schema
        )
        if (
            relative_path == CENTRAL_GOOGLE_OAUTH_NATIVE_CLIENT_PATH
            and not valid_central_native_client_schema
        ):
            findings.append(
                (relative_path, "invalid_central_google_oauth_native_client")
            )
        if (
            central_client_id
            and relative_path != CENTRAL_GOOGLE_OAUTH_NATIVE_CLIENT_PATH
            and central_client_id in content
        ):
            findings.append((relative_path, "central_google_oauth_client_id_copy"))
        if path.suffix.lower() == ".json":
            try:
                document = json.loads(content)
            except json.JSONDecodeError:
                document = None
            if isinstance(document, dict):
                oauth_section = document.get("installed") or document.get("web")
                if (
                    isinstance(oauth_section, dict)
                    and isinstance(oauth_section.get("client_id"), str)
                    and "client_secret" in oauth_section
                ):
                    findings.append(
                        (path.relative_to(root).as_posix(), "google_oauth_client_json")
                    )
        for rule, pattern in HIGH_CONFIDENCE_PATTERNS:
            if pattern.search(content):
                if rule == "google_oauth_client_secret" and allowed_central_native_client:
                    continue
                findings.append((relative_path, rule))
    return sorted(set(findings))
