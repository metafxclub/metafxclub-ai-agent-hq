# Permanent Runtime Hardening — 2026-07-14

## Incident addressed

The recurring symptom was that opening the Bridge page sometimes showed no AI Agents. Two independent failures could produce the same visible result:

1. Port 4186 had no durable background Bridge because the old launcher was tied to a foreground terminal.
2. Frontend boot was all-or-nothing. A missing or slow optional navigation mask could throw before Agent rendering, so all 10 Agents disappeared even when their contracts and PNG files were valid.

Codex CLI iConfig/model selection was not in the Agent render path and was not the cause of this incident.

## Permanent changes

### Bridge lifecycle

- Added verified Start, Status, Stop, and Restart control with a process mutex.
- Bridge runs hidden in the background and duplicate Start reuses the healthy verified PID.
- Process identity includes executable, `bridge_server.py` path, host, and port.
- An unknown process on port 4186 is reported as a conflict and is never killed.
- Startup waits for `GET /api/health` rather than a Codex-dependent endpoint.
- Lifecycle state, stdout/stderr, and JSONL audit have bounded local rotation.

### Frontend boot resilience

- Room and Agent contracts load independently with `Promise.allSettled`.
- Embedded room/10-Agent fallbacks preserve a usable office during a contract fetch failure.
- Agents render before optional animation and navigation resources.
- Navigation mask loading has a timeout and degrades to safe fallback movement instead of aborting boot.
- Missing Agent images display an initials fallback.
- A diagnostic overlay identifies the failed resource, checks Bridge health, and offers Retry.
- A watchdog verifies that exactly 10 `.agent-unit` elements were rendered.
- Asset cache versioning is stable per build rather than changing on every page load.

### Health and static boundary

- `/api/health` is fast and side-effect-free: it never probes Codex, MCP, or external services.
- Readiness requires the exact canonical 10-Agent IDs, room image, walkable mask, all 10 Agent sprites, all registered prop images, critical frontend files, and valid durable JSON stores.
- Static serving remains limited to the root redirect, `frontend/`, and `contracts/`; resolved paths must remain inside an allowed root to prevent junction/symlink escape.

### Mission safety and completion

- Manager delegation creates approval-gated `codex_cli_task` specialist missions and never auto-runs them.
- Parent missions aggregate child status and produce one executive summary at `mission_strategy_table` after all children reach terminal states.
- The mission read model exposes backend-derived `readyToExecute` but never approval digests.
- Approval and execution are separate. The UI requires typing the exact Mission ID, and the backend independently enforces the same confirmation.
- Approval is mission-bound, digest-bound, expiring, and single-use.
- A consumed real run found after Bridge restart fails closed as `bridge_restart_interrupted`; no automatic retry occurs.
- Adapters other than guarded Codex CLI remain blocked/not implemented.

### Data and secret safety

- Existing corrupt JSON fails closed with an audited HTTP 503; it is never replaced with an empty list.
- Mission and memory writes are atomic and preserve the previous valid `.bak` file.
- Large audit, Agent-event, and meeting JSONL files roll into timestamped archive segments without deletion.
- Raw Codex `-o` output is written outside the project/OneDrive tree, sanitized, and only then atomically published to `data/runtime/codex-runs/`.
- Frontend contains no token, API key, auth cookie, broker password, or direct real-tool adapter.

### Codex account quota telemetry

- `GET /api/codex/rate-limits` is a read-only, loopback-only telemetry endpoint and is intentionally separate from `/api/health`.
- The project runner reads the stable `account/rateLimits/read` method from the authenticated local Codex app-server with `experimentalApi: false`.
- Runner and Bridge each apply an explicit allowlist. No account identity, plan, credits, balance, auth material, local path, or raw protocol error can reach the frontend.
- Percent remaining is derived from Codex `usedPercent`; missing or malformed data fails closed as unavailable rather than displaying a fake zero.
- A 75-second in-memory cache coalesces polling. A failed refresh may use a marked stale snapshot for at most 15 minutes; `auth_required` clears the snapshot immediately.
- Real refreshes use the fixed telemetry mission `system-codex-rate-monitor`, owned by `codex_mcp_operator`, and write a sanitized audit event. Cache hits are not audited.
- Completing a real Codex mission invalidates the cache so the next widget read observes updated usage.

## Contract cleanup

- Props are dashboard/report surfaces (`showsChat: false`); chat belongs to Agent characters.
- Agent `allowed_surfaces` describes visual routing only.
- Backend tool authorization is defined exclusively by `contracts/tools/tool-permission-contract.json`.
- Manager/specialist model tiers stay on GPT-5.5 with bounded timeout, output, and hourly run limits.

## Deliberately not enabled

- No Windows logon scheduled task was silently installed. `Open Metafx Agent HQ.cmd` is the explicit canonical launcher after reboot.
- No live trading, public Telegram send, VPS mutation, deployment, delete-files, or paid external API adapter was enabled.
- High-risk approval remains fail-closed until a durable backend Risk Guard issuer exists.

## Next structural migration

The current frontend and Bridge are still large compatibility files. The safest next migration is incremental: keep the current HTTP endpoints as a facade, split UI/API/security/storage/adapters into modules, then migrate runtime state to SQLite WAL with backup, read-only JSON import, row-count/hash verification, and rollback. Do not combine that migration with live-trading enablement.
