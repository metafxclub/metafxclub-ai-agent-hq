# Local Bridge lifecycle

Use these launchers from this folder:

- `open-agent-hq.cmd` starts or reuses a healthy Bridge, waits for the side-effect-free `/api/health` check, then opens the HQ.
- `start-local-bridge.cmd` starts the Bridge in a hidden background process.
- `status-local-bridge.cmd` reports healthy, stopped, unhealthy, or port conflict.
- `stop-local-bridge.cmd` stops only a process whose exact Python command targets this project's `bridge_server.py` on the confirmed `127.0.0.1` endpoint.
- `restart-local-bridge.cmd` safely stops the verified Bridge and starts a healthy replacement.
- `bridge-control.cmd Start|Status|Stop|Restart` provides the same actions from one entrypoint.
- `register-bridge-autostart.cmd` registers the current-user Windows Scheduled Task used automatically by the normal installer. It starts only the hidden Local Bridge after sign-in, reuses the confirmed loopback endpoint, retries startup failures three times, and checks the Bridge every fifteen minutes by default through `wscript.exe` plus `run-bridge-watchdog-hidden.vbs`, so Windows Terminal is not opened. It does not open a browser or MT4/MT5.
- `unregister-bridge-autostart.cmd` removes that exact Scheduled Task and also cleans up the legacy Startup shortcut if present.

Runtime files are intentionally kept outside the frontend:

- State: `data/runtime/bridge-lifecycle-state.json`
- Confirmed endpoint: `data/runtime/bridge-endpoint.json`
- Output: `data/runtime/logs/bridge-stdout.log`
- Errors: `data/runtime/logs/bridge-stderr.log`
- Lifecycle audit: `data/runtime/logs/bridge-lifecycle-audit.jsonl`

Logs rotate to at most three prior generations. A running Bridge is never stopped merely because a PID file exists: the controller re-reads the Windows process and verifies its executable, exact server path, host, and port before stopping it.

For a new installation, `installer/install.ps1 -ListAvailableEndpoints` proposes three loopback URLs before any installation change. The user confirms one URL, and the installer starts the Bridge with that exact Port. If the confirmed Port becomes unavailable, the controller stops safely and asks for a new selection instead of silently changing the URL. Normal Open/Status/Stop operations continue to use the endpoint that passed Health and was saved in `data/runtime/bridge-endpoint.json`.

`scripts/check-codex-readiness.cmd` reads only the sanitized Bridge status and Codex Rate Limit endpoints. It reports the current Windows user's Codex readiness without reading or copying auth files.

The normal installer registers automatic startup only after the exact loopback endpoint passes Health and the frontend responds. The Scheduled Task runs as the current interactive Windows user because Codex login and Rate Limit belong to that user, but its action uses the windowless Windows Script Host wrapper rather than launching PowerShell directly. Advanced or isolated installs can opt out with `-SkipAutostart`; the current state is recorded in `data/runtime/bridge-autostart.json`.
