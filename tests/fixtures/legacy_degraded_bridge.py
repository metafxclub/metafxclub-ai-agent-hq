"""CI fixture that emulates the owned v0.9.2 Bridge in degraded Health.

The release workflow copies this file to the installed bridge path inside an
isolated RUNNER_TEMP tree.  Its command line and listener therefore exercise
the installer's real Windows ownership checks without touching a user Bridge.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    args = parser.parse_args()
    if args.host != "127.0.0.1" or not 1024 <= args.port <= 65535:
        return 2

    project_root = Path(__file__).resolve().parents[2]
    runtime_root = project_root / "data" / "runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)
    control_path = runtime_root / "bridge-control.json"
    shutdown_token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

        def _json(self, status: int, payload: dict[str, object]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            if self.path != "/api/health":
                self._json(404, {"ok": False})
                return
            self._json(
                503,
                {
                    "ok": False,
                    "status": "degraded",
                    "server": "Metafx Local Bridge",
                    "version": "0.9.2",
                    "endpoint": {"host": args.host, "port": args.port},
                },
            )

        def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            if (
                self.path != "/api/admin/shutdown"
                or self.headers.get("X-Metafx-Bridge-Control") != shutdown_token
            ):
                self._json(403, {"ok": False})
                return
            self._json(202, {"ok": True})
            threading.Thread(target=server.shutdown, daemon=True).start()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    control = {
        "schemaVersion": "1.0.0",
        "projectRoot": str(project_root),
        "processId": os.getpid(),
        "port": args.port,
        "startedAt": utc_now(),
        "shutdownToken": shutdown_token,
    }
    control_path.write_text(json.dumps(control) + "\n", encoding="utf-8")
    try:
        server.serve_forever()
    finally:
        server.server_close()
        try:
            current = json.loads(control_path.read_text(encoding="utf-8"))
            if int(current.get("processId", -1)) == os.getpid():
                control_path.unlink(missing_ok=True)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
