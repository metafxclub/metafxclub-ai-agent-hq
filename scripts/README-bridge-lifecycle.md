# Local Bridge lifecycle

Use these launchers from this folder:

- `open-agent-hq.cmd` starts or reuses a healthy Bridge, waits for the side-effect-free `/api/health` check, then opens the HQ.
- `start-local-bridge.cmd` starts the Bridge in a hidden background process.
- `status-local-bridge.cmd` reports healthy, stopped, unhealthy, or port conflict.
- `stop-local-bridge.cmd` stops only a process whose exact Python command targets this project's `bridge_server.py` on `127.0.0.1:4186`.
- `restart-local-bridge.cmd` safely stops the verified Bridge and starts a healthy replacement.
- `bridge-control.cmd Start|Status|Stop|Restart` provides the same actions from one entrypoint.

Runtime files are intentionally kept outside the frontend:

- State: `data/runtime/bridge-lifecycle-state.json`
- Output: `data/runtime/logs/bridge-stdout.log`
- Errors: `data/runtime/logs/bridge-stderr.log`
- Lifecycle audit: `data/runtime/logs/bridge-lifecycle-audit.jsonl`

Logs rotate to at most three prior generations. A running Bridge is never stopped merely because a PID file exists: the controller re-reads the Windows process and verifies its executable, exact server path, host, and port before stopping it. An unrelated process on port 4186 is reported and left untouched.
