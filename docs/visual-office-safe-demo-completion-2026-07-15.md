# Visual Office Safe-Demo Completion — 2026-07-15

## Completion boundary

This release completes the local Visual Office control surface for guarded demo/read-only operation. It does not claim that every future external adapter is implemented.

- Characters are the conversational and taskable Agent surfaces.
- Props are dashboard/report surfaces only; they do not own a chat composer.
- The Mission Strategy Table is the global mission queue and status board.
- Every other prop shows only missions, structured reports, capability status, and local evidence routed to that prop.
- Frontend requests are intents. Permission, model tier, budget, approval, execution, report persistence, and audit remain backend-owned.

## Runtime flow

1. The user talks to an Agent or gives Manager/CEO a goal.
2. Manager creates a guarded parent mission and deterministic specialist subtasks.
3. Each subtask receives an Agent owner, target prop, report type, model tier, timeout, output limit, risk, and mission-bound approval record.
4. The frontend moves the assigned Agent to the target workstation and keeps active workers out of visual-autonomy patrols.
5. Mission state is refreshed from the Bridge while the page is visible.
6. Real Codex execution remains a separate, explicit step after approval and exact Mission ID confirmation.
7. Structured reports route back to the specialist prop; Manager synthesis routes to `mission_strategy_table`.

Agent chat is an audited local intent/transcript surface. It does not silently spend Codex quota. Use **Create Task** for a specialist mission or **Delegate Queue** for a Manager plan; any real Codex response still follows the approval and explicit-execute flow.

## Safety invariants

- Approval is bound to the complete execution packet, including owner, tool, target, prompt, model tier, budget, risk, and report type.
- Approval and execution are separate HTTP actions. Approval never starts a real tool automatically.
- Backend Risk Guard decisions are generated only by backend policy; the frontend cannot impersonate `risk_guard`.
- Disabled or unimplemented high-risk capabilities are rejected fail-closed.
- Codex rate-limit telemetry is read-only and cannot reset or bypass account limits.
- Official `limitReached=true` blocks a new Codex run; unavailable or stale telemetry is never presented as fake zero usage.
- Secrets, auth material, cookies, broker credentials, account identity, and raw local paths are excluded from frontend read models.
- Interrupted or duplicate real runs are never retried automatically.
- Bridge startup reconciles expired or legacy-inconsistent `waiting_approval` records to `blocked` with an audit event; it never executes them.

## Dashboard routing

| Work type | Agent | Dashboard prop |
| --- | --- | --- |
| Backtest analysis | `backtest_analyst` | `left_analytics_console` |
| Optimization | `optimization_agent` | `left_analytics_console` |
| EA / MT4 / MT5 build intent | `ea_developer` | `terminal_workstation` |
| VPS / terminal health | `vps_watch` | `right_server_racks` |
| Auto-trading status | `vps_watch` | `left_signal_cube` |
| Telegram draft / automation | `telegram_ops` | `right_tool_console` |
| Codex / MCP / plugin status | `codex_mcp_operator` | `codex_mcp_portal` |
| Risk / approval | `risk_guard` | `left_audit_crystals` |
| Memory / archive | `mission_archivist` | `left_server_racks` |
| Manager plan / executive summary | `manager` | `mission_strategy_table` |

## Capability truth

`GET /api/capabilities` and each prop report expose a sanitized, contract-owned capability read model. The visible state distinguishes:

- local queue/read-only capability ready;
- guarded Codex capability ready but approval required;
- configuration detected but adapter not implemented;
- deliberately disabled high-risk capability.

`MCP config_present` means that a local configuration file was detected. It does not claim that an MCP server handshake or tool call succeeded.

## Deliberately not enabled

- Live trading or live order placement
- Public/customer Telegram send
- MT4/MT5 terminal mutation
- VPS restart, firewall change, or deployment
- File deletion or public publishing
- MCP mutation or arbitrary plugin execution

These remain future backend adapters. Enabling one requires its own allowlists, structured input/output contract, timeout/output budget, audit trail, Risk Guard policy, explicit human approval, and—in the case of live trading—account allowlists, risk limits, and a kill switch.

## Operating the office

Use `Open Metafx Agent HQ.cmd` or `scripts/open-agent-hq.cmd`. The lifecycle controller verifies the exact Bridge process and `GET /api/health` before opening `http://127.0.0.1:4186/`.

The completed local Bridge runtime for this pass is `0.6.1`.

If the page is unavailable, run `scripts/status-local-bridge.cmd`, then `scripts/restart-local-bridge.cmd`. The controller never kills an unrelated process that happens to use port 4186.

## Verification record

- Python and JavaScript syntax checks passed.
- Runtime regression suite: 30/30 passed.
- Frontend runtime smoke rendered the exact new build with 10/10 Agent nodes.
- Live Bridge health: ready, canonical Agent roster 10/10, room/navigation/Agent/prop assets valid.
- Live capability and all 10 prop-report routes returned only matching capability records.
- Static backend/runtime files remained unpublished; bad Host, cross-origin, and wrong Content-Type requests were rejected.
- Codex runner status and official quota telemetry were ready without running a quota-consuming mission.
- The Codex in-app Browser refused the loopback URL under its own URL policy, so interactive in-app-browser clicking was not used as evidence and no policy workaround was attempted.
