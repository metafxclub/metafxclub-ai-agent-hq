# Metafxclub AI Agent HQ Contracts

This folder is the shared agreement between the visual frontend, the local backend runner, future MCP/Codex tools, and durable memory.

- `agents/agents.json` defines the canonical visible agent roster.
- `agents/agent-spawn-contract.json` defines how Manager may request extra workers safely.
- `rooms/command-room.json` defines the current room, walkable mask, blockers, and props.
- `props/prop-interaction-contract.json` defines clickable prop/report behavior.
- `missions/mission-contract.json` defines task state and mission lifecycle.
- `meetings/meeting-contract.json` defines agent-to-agent transcript records.
- `reports/report-contract.json` defines output/report cards.
- `bridge/bridge-contract.json` defines backend/local-runner boundaries.
- `tools/tool-permission-contract.json` defines what can run and what needs approval.
- `orchestration/orchestration-contract.json` defines Manager delegation, model tiers, budgets, rate limits, report aggregation, and mission-bound approval.
- `workflows/equipment-plugin-map.json` binds each independent equipment action to its Backend-owned Custom Plugin procedure, safe defaults, automation mode, expected outputs, evidence, and Thai recovery guidance.
- `memory/memory-contract.json` defines durable non-secret memory storage.

Rule: frontend may display and submit intents, but real tool execution, Codex CLI, MCP, filesystem, VPS, MT4/MT5, Telegram, and approvals must remain behind the backend/local runner.
