"""One-time, local-only Google Desktop OAuth client setup.

The selected file is read by this Python process and passed directly to the
canonical backend parser.  Raw client JSON, client id, client secret, and file
path are never printed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import google_oauth_store
import google_sheet_hub


def _safe_status() -> dict:
    configuration = google_sheet_hub.oauth_client_configuration()
    client_id = str(configuration.get("clientId") or "").strip()
    source = str(configuration.get("source") or "not_configured")
    return {
        "ok": True,
        "configured": bool(client_id),
        "clientHint": google_oauth_store.client_id_hint(client_id),
        "store": (
            "windows_current_user_secure_store"
            if source == "secure_store"
            else source
        ),
    }


def _read_selected_file(path_value: str) -> bytes:
    candidate = Path(str(path_value or ""))
    if candidate.suffix.lower() != ".json":
        raise google_sheet_hub.GoogleSheetHubError(
            "invalid_oauth_client_file",
            "Select the downloaded Google OAuth client JSON file.",
            422,
        )
    try:
        with candidate.open("rb") as handle:
            payload = handle.read(google_sheet_hub.MAX_OAUTH_CLIENT_JSON_BYTES + 1)
    except OSError as error:
        raise google_sheet_hub.GoogleSheetHubError(
            "oauth_client_file_unreadable",
            "The selected Google OAuth client file could not be read.",
            422,
        ) from error
    if len(payload) > google_sheet_hub.MAX_OAUTH_CLIENT_JSON_BYTES:
        raise google_sheet_hub.GoogleSheetHubError(
            "oauth_client_file_too_large",
            "The Google OAuth client file exceeds the allowed size.",
            413,
        )
    return payload


def _emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments in (["--help"], ["-h"]):
        print(
            "usage: configure_google_oauth_client.py --status | "
            "--file <desktop-client.json> [--expected-client-id <id>] | --remove"
        )
        return 0
    try:
        if arguments == ["--status"]:
            result = _safe_status()
        elif arguments == ["--remove"]:
            removed = google_sheet_hub.remove_google_oauth_client_configuration()
            result = {
                "ok": True,
                "configured": False,
                "clientHint": "",
                "store": "empty",
                "removed": removed.get("removed") is True,
            }
        elif (
            len(arguments) in {2, 4}
            and arguments[0] == "--file"
            and (len(arguments) == 2 or arguments[2] == "--expected-client-id")
        ):
            expected_client_id = arguments[3] if len(arguments) == 4 else ""
            configured = google_sheet_hub.configure_google_oauth_client_json(
                _read_selected_file(arguments[1]),
                expected_client_id=expected_client_id,
            )
            result = {
                "ok": True,
                "configured": True,
                "clientHint": str(configured.get("clientHint") or ""),
                "store": "windows_current_user_secure_store",
            }
        else:
            _emit(
                {
                    "ok": False,
                    "configured": False,
                    "kind": "invalid_arguments",
                    "message": "Use --status, --file with one Desktop OAuth JSON file and optional expected Client ID, or --remove.",
                }
            )
            return 1
    except google_sheet_hub.GoogleSheetHubError as error:
        _emit(
            {
                "ok": False,
                "configured": False,
                "kind": error.code,
                "message": error.message,
            }
        )
        return 1
    except Exception:
        _emit(
            {
                "ok": False,
                "configured": False,
                "kind": "oauth_client_setup_failed",
                "message": "The local Google OAuth client setup could not be completed.",
            }
        )
        return 1
    _emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
