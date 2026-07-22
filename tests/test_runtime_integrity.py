from __future__ import annotations

import importlib.util
import json
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
RUNNER_PATH = PROJECT_ROOT / "runner" / "codex_cli_runner.py"
FRONTEND_INDEX_PATH = PROJECT_ROOT / "frontend" / "index.html"
FRONTEND_MAIN_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "main.js"
FRONTEND_STYLES_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "styles.css"
LIFECYCLE_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "start-local-bridge.ps1"
INSTALLER_SCRIPT_PATH = PROJECT_ROOT / "installer" / "install.ps1"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module("metafx_bridge_server", BRIDGE_PATH)
        cls.runner = load_module("metafx_codex_runner", RUNNER_PATH)

    def test_all_contracts_are_valid_json(self) -> None:
        contract_paths = sorted((PROJECT_ROOT / "contracts").rglob("*.json"))
        self.assertGreater(len(contract_paths), 0)
        for path in contract_paths:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                json.loads(path.read_text(encoding="utf-8"))

    def test_canonical_agent_roster_has_ten_unique_agents(self) -> None:
        payload = json.loads(
            (PROJECT_ROOT / "contracts" / "agents" / "agents.json").read_text(encoding="utf-8")
        )
        agent_ids = [str(agent.get("id")) for agent in payload.get("agents", [])]
        self.assertEqual(len(agent_ids), 10)
        self.assertEqual(len(set(agent_ids)), 10)
        self.assertIn("manager", agent_ids)
        self.assertIn("risk_guard", agent_ids)

    def test_cross_contract_agent_prop_tool_and_report_routes_are_consistent(self) -> None:
        contracts = PROJECT_ROOT / "contracts"
        agents_payload = json.loads((contracts / "agents" / "agents.json").read_text(encoding="utf-8"))
        room_payload = json.loads((contracts / "rooms" / "command-room.json").read_text(encoding="utf-8"))
        role_payload = json.loads((contracts / "props" / "property-role-map.json").read_text(encoding="utf-8"))
        tool_payload = json.loads((contracts / "tools" / "tool-permission-contract.json").read_text(encoding="utf-8"))
        report_payload = json.loads((contracts / "reports" / "report-contract.json").read_text(encoding="utf-8"))
        orchestration_payload = json.loads((contracts / "orchestration" / "orchestration-contract.json").read_text(encoding="utf-8"))

        agent_ids = {str(item["id"]) for item in agents_payload["agents"]}
        prop_ids = {str(item["id"]) for item in room_payload["props"]}
        role_map = role_payload.get("properties") or {}
        report_types = set((report_payload.get("report_targets") or {}).keys())

        self.assertEqual(set(role_map.keys()), prop_ids)
        for agent in agents_payload["agents"]:
            with self.subTest(agent=agent["id"]):
                self.assertIn(agent["visual"]["default_target"], prop_ids)

        for prop_id, role in role_map.items():
            with self.subTest(prop=prop_id):
                actor_fields = (
                    "primaryOwnerAgentId",
                    "contributorAgentIds",
                    "reviewerAgentIds",
                    "approverAgentIds",
                    "ownerAgents",
                )
                referenced_agents = set()
                for field in actor_fields:
                    value = role.get(field)
                    referenced_agents.update(value if isinstance(value, list) else ([value] if value else []))
                self.assertTrue(referenced_agents.issubset(agent_ids))
                self.assertTrue(set(role.get("acceptedReportTypes") or []).issubset(report_types))

        for tool in tool_payload["tools"]:
            with self.subTest(tool=tool["id"]):
                self.assertTrue(set(tool.get("allowedAgents") or []).issubset(agent_ids))
                self.assertTrue(set(tool.get("linkedPropIds") or []).issubset(prop_ids))

        for report_type, targets in report_payload["report_targets"].items():
            with self.subTest(report=report_type):
                self.assertTrue(set(targets).issubset(agent_ids | prop_ids))

        manager_rules = orchestration_payload["managerAutoDelegation"]
        for rule in [*(manager_rules.get("specialistRules") or []), manager_rules.get("fallback") or {}]:
            with self.subTest(rule=rule.get("id", "fallback")):
                self.assertIn(rule["agentId"], agent_ids)
                self.assertIn(rule["targetPropId"], prop_ids)
                self.assertIn(rule["reportType"], report_types)

    def test_frontend_execution_requires_a_separate_exact_mission_confirmation(self) -> None:
        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        self.assertIn('id="modalKanbanExecuteMissionId"', html)
        self.assertIn('id="modalKanbanExecute"', html)

        readiness_start = main.index("function isMissionReadyForExplicitExecution(mission)")
        readiness_end = main.index("\nfunction setMissionExecuteStatus", readiness_start)
        readiness_block = main[readiness_start:readiness_end]
        self.assertIn("return mission.readyToExecute === true;", readiness_block)
        self.assertNotIn('getMissionApprovalState(mission) === "approved"', readiness_block)

        execute_start = main.index("async function executeApprovedKanbanMission()")
        execute_end = main.index("\nfunction setModalTab", execute_start)
        execute_block = main[execute_start:execute_end]
        confirmation_check = execute_block.index("confirmation !== mission.id")
        guarded_post = execute_block.index("postJson(`/api/missions/${encodeURIComponent(mission.id)}/execute`")
        self.assertLess(confirmation_check, guarded_post)
        self.assertIn("confirmMissionId: mission.id", execute_block)
        self.assertIn("No automatic retry", execute_block)

        approval_start = main.index("async function recordKanbanApprovalDecision(decision)")
        approval_end = main.index("async function executeApprovedKanbanMission()", approval_start)
        self.assertNotIn("/execute", main[approval_start:approval_end])

    def test_frontend_prefers_allowed_surfaces_with_legacy_tool_fallback(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        preferred = main.index("Array.isArray(contract.allowed_surfaces)")
        legacy = main.index("Array.isArray(contract.allowed_tools)", preferred)
        assignment = main.index("allowedSurfaces,", legacy)
        self.assertLess(preferred, legacy)
        self.assertLess(legacy, assignment)

    def test_codex_rate_widget_is_backend_only_nonblocking_and_not_persisted(self) -> None:
        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        for element_id in (
            "codexRateWidget",
            "codexRateSummary",
            "codexRateProgress",
            "codexRateReset",
            "codexRateFreshness",
            "codexRateRefreshButton",
        ):
            self.assertIn(f'id="{element_id}"', html)
        self.assertIn('const CODEX_RATE_LIMIT_ENDPOINT = "/api/codex/rate-limits";', main)
        self.assertIn("const CODEX_RATE_LIMIT_POLL_MS = 60000;", main)
        self.assertIn('document.visibilityState === "visible"', main)
        self.assertIn("window.setTimeout(startCodexRateLimitPolling, 0);", main)
        self.assertIn('state.codexRate.inFlight', main)
        self.assertIn('["auth_required", "config_error", "missing"]', main)
        save_start = main.index("function saveSessionSnapshot()")
        save_end = main.index("\nfunction clearSessionSnapshot()", save_start)
        self.assertNotIn("codexRate", main[save_start:save_end])

    def test_visual_office_polls_missions_preserves_active_workers_and_renders_report_truth(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")

        self.assertIn("const MISSION_POLL_MS = 12000;", main)
        self.assertIn("window.setTimeout(startMissionPolling, 0);", main)
        self.assertIn("function reconcileAgentMissionState()", main)
        self.assertIn("&& !agent.activeMissionId", main)
        self.assertIn("structuredReportItems", main)
        self.assertIn("capabilityDashboardItems", main)
        self.assertIn("report?.meetings", main)
        self.assertIn("report?.bridge", main)
        for status in ("queued", "running", "waiting_approval", "blocked", "completed", "failed", "archived"):
            self.assertIn(f".kanban-column.status-{status}", styles)

    def test_modal_layers_fill_the_usable_viewport_and_keep_actions_visible(self) -> None:
        styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")

        modal_start = styles.index(".game-modal {")
        modal_end = styles.index("\n.game-modal.open", modal_start)
        modal_rule = styles[modal_start:modal_end]
        self.assertIn("top: 104px;", modal_rule)
        self.assertIn("bottom: 14px;", modal_rule)
        self.assertIn("max-height: none;", modal_rule)

        body_start = styles.index(".game-modal-body {")
        body_end = styles.index("\n.modal-portrait-panel", body_start)
        body_rule = styles[body_start:body_end]
        self.assertIn("height: 100%;", body_rule)
        self.assertIn("min-height: 0;", body_rule)

        self.assertIn(".game-modal.dashboard-modal #modalDashboardPanel.active", styles)
        self.assertIn("grid-template-rows: auto minmax(0, 1fr) auto;", styles)
        self.assertIn(".game-modal.kanban-modal #modalKanbanPanel.active", styles)
        self.assertIn(".kanban-detail-body", styles)
        self.assertIn("height: 100%;\n  max-height: none;\n  overflow: auto;", styles)

    def test_task_detail_dialog_uses_task_only_renderers_without_raw_payload_dump(self) -> None:
        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")

        self.assertIn('id="taskDetailDialog"', html)
        self.assertIn('class="task-detail-dialog"', html)
        self.assertIn("taskDetailMissionId: null", main)
        self.assertIn('taskDetailDialog: document.getElementById("taskDetailDialog")', main)
        self.assertIn("function createTaskCard(", main)
        self.assertIn("function renderTaskList(", main)

        def function_block(name: str) -> str:
            start = main.index(f"function {name}(")
            next_function = main.find("\nfunction ", start + 1)
            next_async_function = main.find("\nasync function ", start + 1)
            candidates = [value for value in (next_function, next_async_function) if value >= 0]
            return main[start:min(candidates) if candidates else len(main)]

        task_card_block = function_block("createTaskCard")
        self.assertIn('document.createElement("button")', task_card_block)
        self.assertTrue(
            'type = "button"' in task_card_block or 'setAttribute("type", "button")' in task_card_block,
        )
        self.assertIn("aria-haspopup", task_card_block)
        self.assertIn('"dialog"', task_card_block)
        self.assertTrue(
            'addEventListener("click"' in task_card_block or ".onclick" in task_card_block,
        )

        modal_block = function_block("renderGameModal")
        prop_dashboard_block = function_block("renderPropDashboard")
        kanban_block = function_block("renderMissionKanban")
        self.assertIn("renderTaskList(els.modalTaskBoard", modal_block)
        self.assertIn("renderTaskList(els.modalDashboardWork", prop_dashboard_block)
        self.assertTrue(
            "renderTaskList(" in kanban_block or "createTaskCard(" in kanban_block,
            "Kanban must use the same task-card renderer as the Agent and Current Work surfaces.",
        )
        self.assertNotIn("renderTaskList(els.modalDashboardReports", main)
        self.assertNotIn("renderTaskList(els.modalDashboardStatus", main)
        self.assertIn("renderCardList(els.modalDashboardReports", prop_dashboard_block)
        self.assertIn("renderCardList(els.modalDashboardStatus", prop_dashboard_block)

        detail_block = function_block("renderMissionDetail")
        has_details_disclosure = '<details' in html.lower() or 'createElement("details")' in detail_block
        self.assertTrue(has_details_disclosure)
        self.assertIn('const facts = document.createElement("div")', detail_block)
        self.assertIn("ดูข้อมูลระบบ", f"{html}\n{detail_block}")
        self.assertIn("textContent", detail_block)
        self.assertNotIn("payloadDigest", detail_block)
        self.assertNotIn("JSON.stringify(mission", detail_block)
        self.assertNotIn("JSON.stringify(item", detail_block)
        self.assertIn("function restoreTaskDetailReturnFocus()", main)
        self.assertIn("taskDetailReturnMissionId", main)
        self.assertIn("taskDetailInUse", main)
        self.assertIn("!userIsEditing && !taskDetailInUse", main)

    def test_thai_localization_keeps_machine_statuses_and_utf8_integrity(self) -> None:
        frontend_paths = (FRONTEND_INDEX_PATH, FRONTEND_MAIN_PATH, FRONTEND_STYLES_PATH)
        for path in frontend_paths:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                decoded = path.read_bytes().decode("utf-8")
                self.assertNotIn("\ufffd", decoded)

        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        self.assertIn('<html lang="th">', html)
        self.assertIn('<meta charset="utf-8"', html)

        normalize_start = main.index('function normalizeMissionStatus(status = "queued")')
        normalize_end = main.index("\nfunction getAgentIdFromOwner", normalize_start)
        normalize_block = main[normalize_start:normalize_end]
        for status in ("queued", "running", "waiting_approval", "blocked", "completed", "failed", "archived"):
            self.assertIn(f'"{status}"', normalize_block)

        # Localization is presentation-only: these backend protocol values and
        # exact-ID execution guards must remain machine-readable and unchanged.
        self.assertIn('actorId: "human"', main)
        self.assertIn('recordKanbanApprovalDecision("approved")', main)
        self.assertIn('recordKanbanApprovalDecision("rejected")', main)
        self.assertIn("confirmation !== mission.id", main)
        self.assertIn("confirmMissionId: mission.id", main)

    def test_agent_chat_is_audited_intent_not_a_fake_model_response(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        start = main.index("async function handleModalSend()")
        end = main.index("async function handleModalAssignTask()", start)
        block = main[start:end]
        self.assertIn("persistAgentIntent", block)
        self.assertIn("submitManagerCommand", block)
        self.assertIn("No tool was run", block)
        self.assertNotIn("runBridgeTask", block)

    def test_health_check_is_fast_and_side_effect_free(self) -> None:
        health = self.bridge.runtime_health()
        self.assertTrue(health["ok"])
        self.assertEqual(health["status"], "ready")
        self.assertEqual(health["agentCount"], 10)
        self.assertEqual(health["expectedAgentCount"], 10)
        self.assertTrue(health["agentRosterComplete"])
        self.assertTrue(all(health["criticalFiles"].values()))
        self.assertTrue(health["assetIntegrity"]["roomImage"])
        self.assertTrue(health["assetIntegrity"]["walkableMask"])
        self.assertTrue(all(health["assetIntegrity"]["agentImages"].values()))
        self.assertTrue(all(health["assetIntegrity"]["propImages"].values()))
        self.assertFalse(health["policy"]["frontendSecrets"])
        self.assertEqual(health["policy"]["realExecution"], "guarded")

    def test_http_server_is_restart_friendly(self) -> None:
        self.assertTrue(self.bridge.BridgeHTTPServer.allow_reuse_address)
        self.assertTrue(self.bridge.BridgeHTTPServer.daemon_threads)

    def test_windows_venv_launcher_does_not_break_bridge_lifecycle_identity(self) -> None:
        lifecycle = LIFECYCLE_SCRIPT_PATH.read_text(encoding="utf-8-sig")
        installer = INSTALLER_SCRIPT_PATH.read_text(encoding="utf-8-sig")

        self.assertIn("sys._base_executable", lifecycle)
        self.assertIn("$candidates = @(Get-BridgeProcesses)", lifecycle)
        self.assertIn("$healthyProcessId = Wait-ForBridgeHealth", lifecycle)
        self.assertIn('Write-LifecycleState -Status "running" -ProcessId $healthyProcessId', lifecycle)
        self.assertIn("& $FilePath @Arguments | Out-Host", installer)
        self.assertIn("$nativeExitCode = $LASTEXITCODE", installer)

    def test_durable_json_write_keeps_last_valid_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missions.json"
            self.bridge.write_json(path, {"missions": [{"id": "first"}]}, keep_backup=True)
            self.bridge.write_json(path, {"missions": [{"id": "second"}]}, keep_backup=True)
            backup = path.with_name("missions.json.bak")
            self.assertTrue(backup.is_file())
            self.assertEqual(json.loads(backup.read_text(encoding="utf-8"))["missions"][0]["id"], "first")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["missions"][0]["id"], "second")

    def test_corrupt_json_fails_closed_instead_of_returning_empty_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missions.json"
            path.write_text("{not valid json", encoding="utf-8")
            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge.read_json(path, {"missions": []})
            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge.write_json(path, {"missions": []}, keep_backup=True)
            self.assertEqual(path.read_text(encoding="utf-8"), "{not valid json")

    def test_append_only_log_rotation_archives_without_deleting_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original_runtime = self.bridge.RUNTIME_DIR
            try:
                self.bridge.RUNTIME_DIR = Path(directory) / "runtime"
                path = self.bridge.RUNTIME_DIR / "agent-events.jsonl"
                path.parent.mkdir(parents=True, exist_ok=True)
                original = '{"kind":"historic","detail":"preserve me"}\n'
                path.write_text(original, encoding="utf-8")
                archived = self.bridge.rotate_jsonl_segment(path, max_bytes=1)
                self.assertIsNotNone(archived)
                self.assertFalse(path.exists())
                self.assertEqual(archived.read_text(encoding="utf-8"), original)
                self.assertTrue(str(archived).startswith(str(self.bridge.RUNTIME_DIR / "archive")))
            finally:
                self.bridge.RUNTIME_DIR = original_runtime

    def test_codex_raw_output_is_sanitized_before_project_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_directory = Path(directory) / "codex-runs"
            raw_output_paths = []
            original_runs_dir = self.runner.CODEX_RUNS_DIR
            original_status = self.runner.status
            original_run_command = self.runner.run_command

            def fake_run_command(command, timeout=30, stdin=None):
                raw_path = Path(command[command.index("-o") + 1])
                raw_output_paths.append(raw_path)
                self.assertNotEqual(raw_path.parent.resolve(), run_directory.resolve())
                raw_path.write_text("token=supersecretvalue\nSafe report body", encoding="utf-8")
                return {
                    "ok": True,
                    "exitCode": 0,
                    "stdout": "token=supersecretvalue",
                    "stderr": "",
                    "durationMs": 1,
                }

            try:
                self.runner.CODEX_RUNS_DIR = run_directory
                self.runner.status = lambda: {"status": "ready"}
                self.runner.run_command = fake_run_command
                result = self.runner.run_codex("Review this report", "manager", "mission-test")
            finally:
                self.runner.CODEX_RUNS_DIR = original_runs_dir
                self.runner.status = original_status
                self.runner.run_command = original_run_command

            self.assertTrue(result["ok"])
            self.assertTrue(result["usage"]["secretRedacted"])
            for path in run_directory.glob("*"):
                content = path.read_text(encoding="utf-8")
                self.assertNotIn("supersecretvalue", content)
            self.assertTrue(raw_output_paths)
            self.assertFalse(raw_output_paths[0].exists())

    def test_codex_rate_limit_runner_drops_account_and_secret_fields(self) -> None:
        payload = self.runner.sanitize_rate_limits_response({
            "rateLimits": {"primary": {"usedPercent": 8, "windowDurationMins": 60, "resetsAt": 1780000000}},
            "rateLimitsByLimitId": {
                "codex": {
                    "planType": "private-plan",
                    "credits": {"balance": "private-credit"},
                    "account": {"email": "private@example.test", "token": "secret-token-value"},
                    "primary": {"usedPercent": 123, "windowDurationMins": 10080, "resetsAt": 1784531255},
                    "secondary": {"usedPercent": -5, "windowDurationMins": 300, "resetsAt": 1784530000},
                    "rateLimitReachedType": None,
                },
            },
            "codexHome": "C:/private/path",
        })
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["primary"]["usedPercent"], 100)
        self.assertEqual(payload["primary"]["remainingPercent"], 0)
        self.assertEqual(payload["secondary"]["usedPercent"], 0)
        serialized = json.dumps(payload).lower()
        for forbidden in ("plan", "credit", "balance", "email", "token", "codexhome", "private"):
            self.assertNotIn(forbidden, serialized)

    def test_bridge_rate_limit_cache_stale_fallback_and_auth_invalidation(self) -> None:
        good = {
            "ok": True,
            "status": "ready",
            "source": "codex_app_server",
            "meter": {"id": "codex", "name": "Codex", "planType": "must-drop"},
            "primary": {
                "usedPercent": 37,
                "remainingPercent": 999,
                "windowDurationMinutes": 10080,
                "resetsAt": "2026-07-20T07:07:35Z",
                "token": "must-drop",
            },
            "secondary": None,
            "limitReached": False,
            "checkedAt": "2026-07-14T16:00:00Z",
            "credits": {"balance": "must-drop"},
        }
        calls = []
        responses = [good, {"ok": False, "status": "timeout"}, {"ok": False, "status": "auth_required"}]
        original_command = self.bridge.run_safe_command
        original_audit = self.bridge.AUDIT_PATH
        original_runner_python = self.bridge.CODEX_RUNNER_PYTHON
        original_cache = dict(self.bridge.CODEX_RATE_LIMIT_CACHE)

        def fake_command(command, timeout=8, output_limit=1200, input_text=None):
            calls.append(command)
            payload = responses.pop(0)
            return {"ok": True, "exitCode": 0, "output": json.dumps(payload), "durationMs": 1}

        with tempfile.TemporaryDirectory() as directory:
            try:
                self.bridge.run_safe_command = fake_command
                self.bridge.AUDIT_PATH = Path(directory) / "bridge-audit.jsonl"
                # The clean repository intentionally excludes runner/.venv.
                # Point the mocked runner gate at an existing local file so
                # this unit test remains independent from installation state.
                self.bridge.CODEX_RUNNER_PYTHON = Path(__file__)
                self.bridge.CODEX_RATE_LIMIT_CACHE.update({"payload": None, "fetchedMonotonic": 0.0, "invalidated": False})

                fresh = self.bridge.codex_rate_limits(force=True)
                audit_after_refresh = self.bridge.AUDIT_PATH.read_text(encoding="utf-8").count("\n")
                cached = self.bridge.codex_rate_limits()
                self.assertEqual(len(calls), 1)
                self.assertEqual(self.bridge.AUDIT_PATH.read_text(encoding="utf-8").count("\n"), audit_after_refresh)
                self.assertEqual(fresh["primary"]["remainingPercent"], 63)
                self.assertTrue(cached["cacheHit"])
                serialized = json.dumps(fresh).lower()
                for forbidden in ("plantype", "credits", "balance", "token", "must-drop"):
                    self.assertNotIn(forbidden, serialized)

                self.bridge.CODEX_RATE_LIMIT_CACHE["fetchedMonotonic"] = time.monotonic() - 80
                stale = self.bridge.codex_rate_limits()
                self.assertTrue(stale["stale"])
                self.assertEqual(len(calls), 2)

                auth = self.bridge.codex_rate_limits(force=True)
                self.assertFalse(auth["ok"])
                self.assertEqual(auth["status"], "auth_required")
                self.assertIsNone(self.bridge.CODEX_RATE_LIMIT_CACHE["payload"])
                self.assertEqual(len(calls), 3)

                audit_text = self.bridge.AUDIT_PATH.read_text(encoding="utf-8").lower()
                self.assertIn("system-codex-rate-monitor", audit_text)
                self.assertIn("codex_mcp_operator", audit_text)
                self.assertNotIn("must-drop", audit_text)
            finally:
                self.bridge.run_safe_command = original_command
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.CODEX_RUNNER_PYTHON = original_runner_python
                self.bridge.CODEX_RATE_LIMIT_CACHE.clear()
                self.bridge.CODEX_RATE_LIMIT_CACHE.update(original_cache)

    def test_concurrent_codex_rate_limit_reads_use_one_runner_refresh(self) -> None:
        good = {
            "ok": True,
            "status": "ready",
            "primary": {
                "usedPercent": 42,
                "windowDurationMinutes": 10080,
                "resetsAt": "2026-07-20T07:07:35Z",
            },
            "secondary": None,
            "checkedAt": "2026-07-14T16:00:00Z",
        }
        call_count = 0
        count_lock = threading.Lock()
        original_command = self.bridge.run_safe_command
        original_audit = self.bridge.AUDIT_PATH
        original_runner_python = self.bridge.CODEX_RUNNER_PYTHON
        original_cache = dict(self.bridge.CODEX_RATE_LIMIT_CACHE)

        def fake_command(command, timeout=8, output_limit=1200, input_text=None):
            nonlocal call_count
            with count_lock:
                call_count += 1
            time.sleep(0.05)
            return {"ok": True, "exitCode": 0, "output": json.dumps(good), "durationMs": 50}

        with tempfile.TemporaryDirectory() as directory:
            try:
                self.bridge.run_safe_command = fake_command
                self.bridge.AUDIT_PATH = Path(directory) / "bridge-audit.jsonl"
                self.bridge.CODEX_RUNNER_PYTHON = Path(__file__)
                self.bridge.CODEX_RATE_LIMIT_CACHE.update({"payload": None, "fetchedMonotonic": 0.0, "invalidated": False})
                with ThreadPoolExecutor(max_workers=10) as pool:
                    results = list(pool.map(lambda _: self.bridge.codex_rate_limits(), range(10)))
                self.assertEqual(call_count, 1)
                self.assertTrue(all(item["ok"] for item in results))
                self.assertEqual({item["primary"]["remainingPercent"] for item in results}, {58})
            finally:
                self.bridge.run_safe_command = original_command
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.CODEX_RUNNER_PYTHON = original_runner_python
                self.bridge.CODEX_RATE_LIMIT_CACHE.clear()
                self.bridge.CODEX_RATE_LIMIT_CACHE.update(original_cache)

    def test_manager_delegation_creates_approval_gated_specialist_missions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_missions = self.bridge.MISSIONS_PATH
            original_reports = self.bridge.RUNTIME_REPORTS_DIR
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.RATE_LIMIT_STATE.clear()
                result = self.bridge.manager_delegate({
                    "agentId": "manager",
                    "goal": "Analyze this backtest drawdown and optimize the parameter range",
                    "idempotencyKey": "delegation-regression-test",
                })
                self.assertTrue(result["ok"])
                self.assertEqual(result["parent"]["status"], "running")
                self.assertGreaterEqual(len(result["subtasks"]), 2)
                for subtask in result["subtasks"]:
                    self.assertEqual(subtask["toolId"], "codex_cli_task")
                    self.assertEqual(subtask["status"], "waiting_approval")
                    self.assertTrue(subtask["approval"]["required"])
                    self.assertEqual(subtask["approval"]["state"], "pending")

                for subtask in result["subtasks"]:
                    subtask["status"] = "completed"
                    subtask["result"] = f"Structured result from {subtask['owner']}"
                    subtask["completedAt"] = self.bridge.utc_now()
                    self.bridge.replace_mission(subtask)
                refreshed = self.bridge.refresh_parent_mission(result["parent"]["id"])
                self.assertEqual(refreshed["status"], "completed")
                self.assertEqual(refreshed["phase"], "synthesized")
                self.assertTrue(refreshed["delegation"]["finalReportId"])
            finally:
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.RUNTIME_REPORTS_DIR = original_reports
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.RATE_LIMIT_STATE.clear()

    def test_approval_digest_binds_every_execution_relevant_field(self) -> None:
        mission = {
            "owner": "backtest_analyst",
            "toolId": "codex_cli_task",
            "targetId": "left_analytics_console",
            "detail": "Analyze this bounded report",
            "modelTier": "specialist_balanced",
            "budget": {"timeoutSeconds": 120, "outputLimitChars": 7000, "maxRuns": 1},
            "risk": "medium",
            "reportType": "backtest_report",
        }
        digest = self.bridge.mission_payload_digest(mission)
        for field, changed in {
            "owner": "manager",
            "toolId": "mcp_tool_run",
            "targetId": "codex_mcp_portal",
            "detail": "Changed detail",
            "modelTier": "manager_quality",
            "budget": {"timeoutSeconds": 121, "outputLimitChars": 7000, "maxRuns": 1},
            "risk": "high",
            "reportType": "risk_review",
        }.items():
            with self.subTest(field=field):
                changed_mission = {**mission, field: changed}
                self.assertNotEqual(self.bridge.mission_payload_digest(changed_mission), digest)
        reordered_budget = {
            **mission,
            "budget": {"maxRuns": 1, "outputLimitChars": 7000, "timeoutSeconds": 120},
        }
        self.assertEqual(self.bridge.mission_payload_digest(reordered_budget), digest)

    def test_manager_idempotent_replay_does_not_consume_rate_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_missions = self.bridge.MISSIONS_PATH
            original_reports = self.bridge.RUNTIME_REPORTS_DIR
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.RATE_LIMIT_STATE.clear()
                payload = {
                    "agentId": "manager",
                    "goal": "Analyze this backtest report",
                    "idempotencyKey": "replay-before-rate-limit",
                }
                first = self.bridge.manager_delegate(payload)
                rate_rows_after_first = list(self.bridge.RATE_LIMIT_STATE.get("delegate:manager", []))
                replay = self.bridge.manager_delegate(payload)
                self.assertTrue(first["ok"])
                self.assertTrue(replay["ok"])
                self.assertTrue(replay["idempotentReplay"])
                self.assertEqual(self.bridge.RATE_LIMIT_STATE.get("delegate:manager", []), rate_rows_after_first)
            finally:
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.RUNTIME_REPORTS_DIR = original_reports
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.RATE_LIMIT_STATE.clear()

    def test_archived_child_preserves_outcome_and_parent_report_is_updated_in_place(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_missions = self.bridge.MISSIONS_PATH
            original_reports = self.bridge.RUNTIME_REPORTS_DIR
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                parent = {"id": "parent-archive", "title": "Parent", "status": "running", "owner": "manager", "reportIds": [], "delegation": {}}
                children = [
                    {"id": "child-success", "parentMissionId": parent["id"], "owner": "backtest_analyst", "status": "completed", "result": "ok"},
                    {"id": "child-later-fails", "parentMissionId": parent["id"], "owner": "optimization_agent", "status": "completed", "result": "ok"},
                ]
                self.bridge.save_missions([parent, *children])
                completed = self.bridge.refresh_parent_mission(parent["id"])
                report_id = completed["delegation"]["finalReportId"]
                self.assertEqual(completed["status"], "completed")

                archived_success = self.bridge.archive_mission("child-success")
                self.assertEqual(archived_success["mission"]["archivedFromStatus"], "completed")
                self.assertTrue(archived_success["mission"]["archivedSuccessful"])
                after_success_archive = self.bridge.find_mission(parent["id"])
                self.assertEqual(after_success_archive["status"], "completed")
                self.assertEqual(after_success_archive["delegation"]["finalReportId"], report_id)

                failed_child = self.bridge.find_mission("child-later-fails")
                failed_child["status"] = "failed"
                failed_child["result"] = "failed safely"
                self.bridge.replace_mission(failed_child)
                archived_failure = self.bridge.archive_mission("child-later-fails")
                self.assertFalse(archived_failure["mission"]["archivedSuccessful"])
                blocked_parent = self.bridge.find_mission(parent["id"])
                self.assertEqual(blocked_parent["status"], "blocked")
                self.assertEqual(blocked_parent["delegation"]["finalReportId"], report_id)
                final_report = json.loads((self.bridge.RUNTIME_REPORTS_DIR / f"{report_id}.json").read_text(encoding="utf-8"))
                self.assertEqual(final_report["status"], "blocked")
                self.assertEqual(final_report["metrics"]["outcomes"]["notSucceeded"], 1)
            finally:
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.RUNTIME_REPORTS_DIR = original_reports
                self.bridge.AUDIT_PATH = original_audit

    def test_backend_risk_guard_rejects_disabled_high_risk_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_missions = self.bridge.MISSIONS_PATH
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                mission = self.bridge.create_mission({
                    "title": "Telegram external send",
                    "prompt": "send telegram summary",
                    "agentId": "telegram_ops",
                    "toolId": "send_telegram",
                    "targetId": "right_tool_console",
                    "risk": "low",
                    "reportType": "telegram_tool_report",
                })
                self.assertEqual(mission["risk"], "high")
                self.assertEqual(set(mission["approval"]["requiredActors"]), {"human", "risk_guard"})
                result = self.bridge.approve_mission(mission["id"], {
                    "actorId": "human",
                    "decision": "approved",
                    "confirmMissionId": mission["id"],
                    "note": "I explicitly approve this exact bounded mission packet.",
                })
                reviewed = self.bridge.find_mission(mission["id"])
                self.assertTrue(result["ok"])
                self.assertEqual(reviewed["status"], "blocked")
                self.assertEqual(reviewed["approval"]["state"], "rejected")
                risk_decision = next(item for item in reviewed["approval"]["decisions"] if item["actorId"] == "risk_guard")
                self.assertEqual(risk_decision["decision"], "rejected")
                self.assertEqual(risk_decision["actorProvenance"], "backend_deterministic_policy")
                self.assertEqual(risk_decision["payloadDigest"], reviewed["approval"]["payloadDigest"])
                audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)
                self.assertTrue(any(item.get("type") == "mission.risk_guard_review" for item in audit))
            finally:
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.AUDIT_PATH = original_audit

    def test_capability_registry_is_contract_owned_sanitized_and_prop_filtered(self) -> None:
        fake_status = {
            "mode": "Codex Runner Ready",
            "status": "guarded",
            "codex": {"status": "ready", "version": "codex-cli 1", "runner": "project_sdk"},
            "mcp": {"status": "config_present", "configPresent": True},
            "time": "2026-07-15T00:00:00+00:00",
        }
        registry = self.bridge.capability_registry(fake_status)
        self.assertEqual(registry["contractVersion"], "tool-permission-contract-v003")
        self.assertFalse(registry["policy"]["frontendSecrets"])
        self.assertTrue(registry["policy"]["disabledToolsFailClosed"])
        telegram = next(item for item in registry["capabilities"] if item["id"] == "send_telegram")
        self.assertFalse(telegram["realExecutionAvailable"])
        self.assertFalse(telegram["autoRunnable"])
        serialized = json.dumps(registry).lower()
        for forbidden in ("api_key", "authorization", "cookie", "password"):
            self.assertNotIn(forbidden, serialized)

        originals = {
            "bridge_status": self.bridge.bridge_status,
            "load_missions": self.bridge.load_missions,
            "load_agent_events": self.bridge.load_agent_events,
            "load_runtime_reports": self.bridge.load_runtime_reports,
            "load_meeting_records": self.bridge.load_meeting_records,
            "search_memory_items": self.bridge.search_memory_items,
        }
        try:
            self.bridge.bridge_status = lambda: fake_status
            self.bridge.load_missions = lambda: []
            self.bridge.load_agent_events = lambda limit=120: []
            self.bridge.load_runtime_reports = lambda limit=120: []
            self.bridge.load_meeting_records = lambda limit=120: [{"id": "meeting-1", "linkedPropId": "codex_mcp_portal", "participants": ["codex_mcp_operator"]}]
            self.bridge.search_memory_items = lambda query="", limit=12: []
            prop = self.bridge.prop_report("codex_mcp_portal")
            self.assertEqual(prop["bridge"]["runtimeVersion"], self.bridge.BRIDGE_RUNTIME_VERSION)
            self.assertTrue(prop["meetings"])
            self.assertTrue(prop["capabilities"])
            self.assertTrue(all("codex_mcp_portal" in item["linkedPropIds"] for item in prop["capabilities"]))
        finally:
            for name, value in originals.items():
                setattr(self.bridge, name, value)

        source = BRIDGE_PATH.read_text(encoding="utf-8")
        self.assertIn('if path == "/api/capabilities":', source)

    def test_frontend_read_model_exposes_only_server_derived_execute_readiness(self) -> None:
        mission = {
            "id": "mission-ready",
            "title": "Approved read-only analysis",
            "status": "waiting_approval",
            "approval": {
                "required": True,
                "state": "approved",
                "payloadDigest": "must-not-leak",
            },
        }
        read_model = self.bridge.mission_read_model_item(mission)
        self.assertTrue(read_model["readyToExecute"])
        self.assertNotIn("payloadDigest", read_model["approval"])
        mission["approval"]["state"] = "pending"
        self.assertFalse(self.bridge.mission_read_model_item(mission)["readyToExecute"])

    def test_execute_requires_exact_mission_confirmation_before_lookup(self) -> None:
        result = self.bridge.execute_mission("mission-confirm", {})
        self.assertFalse(result["ok"])
        self.assertEqual(result["kind"], "mission_confirmation_required")
        self.assertEqual(result["_httpStatus"], 422)

    def test_runner_busy_does_not_consume_hourly_rate_counter(self) -> None:
        class BusySemaphore:
            def acquire(self, blocking=False):
                return False

            def release(self):
                raise AssertionError("A semaphore that was not acquired must not be released")

        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_missions = self.bridge.MISSIONS_PATH
            original_audit = self.bridge.AUDIT_PATH
            original_bridge_status = self.bridge.bridge_status
            original_quota = self.bridge.codex_rate_limits
            original_semaphore = self.bridge.REAL_RUN_SEMAPHORE
            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.bridge_status = lambda: {"codex": {"status": "ready"}}
                self.bridge.codex_rate_limits = lambda force=False: {"ok": False, "status": "unavailable", "stale": False}
                self.bridge.REAL_RUN_SEMAPHORE = BusySemaphore()
                self.bridge.RATE_LIMIT_STATE.clear()
                mission = {
                    "id": "mission-runner-busy",
                    "title": "Bounded analysis",
                    "detail": "Analyze a local report only",
                    "owner": "backtest_analyst",
                    "requester": "human",
                    "toolId": "codex_cli_task",
                    "targetId": "left_analytics_console",
                    "status": "waiting_approval",
                    "risk": "medium",
                    "modelTier": "specialist_balanced",
                    "reportType": "backtest_report",
                    "budget": {"timeoutSeconds": 120, "outputLimitChars": 7000, "maxRuns": 1},
                }
                mission["approval"] = {"required": True, "state": "approved", "payloadDigest": self.bridge.mission_payload_digest(mission)}
                self.bridge.save_missions([mission])
                result = self.bridge.execute_mission(mission["id"], {"confirmMissionId": mission["id"]})
                self.assertEqual(result["kind"], "runner_busy")
                self.assertEqual(self.bridge.RATE_LIMIT_STATE, {})
            finally:
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.bridge_status = original_bridge_status
                self.bridge.codex_rate_limits = original_quota
                self.bridge.REAL_RUN_SEMAPHORE = original_semaphore
                self.bridge.RATE_LIMIT_STATE.clear()

    def test_official_codex_limit_reached_blocks_before_runner_without_guessing_unavailable(self) -> None:
        class UntouchedSemaphore:
            def acquire(self, blocking=False):
                raise AssertionError("Runner semaphore must not be touched after an official limit block")

            def release(self):
                raise AssertionError("Runner semaphore must not be touched after an official limit block")

        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_missions = self.bridge.MISSIONS_PATH
            original_audit = self.bridge.AUDIT_PATH
            original_bridge_status = self.bridge.bridge_status
            original_quota = self.bridge.codex_rate_limits
            original_semaphore = self.bridge.REAL_RUN_SEMAPHORE
            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.bridge_status = lambda: {"codex": {"status": "ready"}}
                self.bridge.codex_rate_limits = lambda force=False: {"ok": True, "status": "ready", "limitReached": True, "stale": False}
                self.bridge.REAL_RUN_SEMAPHORE = UntouchedSemaphore()
                self.bridge.RATE_LIMIT_STATE.clear()
                mission = {
                    "id": "mission-official-limit",
                    "title": "Bounded analysis",
                    "detail": "Analyze a local report only",
                    "owner": "backtest_analyst",
                    "requester": "human",
                    "toolId": "codex_cli_task",
                    "targetId": "left_analytics_console",
                    "status": "waiting_approval",
                    "risk": "medium",
                    "modelTier": "specialist_balanced",
                    "reportType": "backtest_report",
                    "budget": {"timeoutSeconds": 120, "outputLimitChars": 7000, "maxRuns": 1},
                }
                mission["approval"] = {"required": True, "state": "approved", "payloadDigest": self.bridge.mission_payload_digest(mission)}
                self.bridge.save_missions([mission])
                result = self.bridge.execute_mission(mission["id"], {"confirmMissionId": mission["id"]})
                self.assertEqual(result["kind"], "codex_limit_reached")
                self.assertEqual(self.bridge.RATE_LIMIT_STATE, {})
                audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)
                self.assertTrue(any(item.get("type") == "guard.codex_limit_reached" for item in audit))
            finally:
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.bridge_status = original_bridge_status
                self.bridge.codex_rate_limits = original_quota
                self.bridge.REAL_RUN_SEMAPHORE = original_semaphore
                self.bridge.RATE_LIMIT_STATE.clear()

    def test_interrupted_consumed_run_is_failed_closed_without_retry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime"
            original_runtime = self.bridge.RUNTIME_DIR
            original_missions = self.bridge.MISSIONS_PATH
            original_reports = self.bridge.RUNTIME_REPORTS_DIR
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.RUNTIME_DIR = runtime
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                mission = {
                    "id": "mission-interrupted",
                    "title": "Interrupted task",
                    "owner": "backtest_analyst",
                    "toolId": "codex_cli_task",
                    "status": "running",
                    "approval": {"required": True, "state": "consumed"},
                    "attemptCount": 1,
                }
                self.bridge.save_missions([mission])
                recovered = self.bridge.recover_interrupted_missions()
                stored = self.bridge.find_mission("mission-interrupted")
                self.assertEqual(recovered, 1)
                self.assertEqual(stored["status"], "failed")
                self.assertEqual(stored["phase"], "interrupted")
                self.assertEqual(stored["errorCode"], "bridge_restart_interrupted")
                self.assertEqual(stored["approval"]["state"], "consumed")
                self.assertIn("no automatic retry", stored["result"])
                audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)
                self.assertEqual(audit[-1]["type"], "mission.interrupted_recovered")
                self.assertFalse(audit[-1]["automaticRetry"])
            finally:
                self.bridge.RUNTIME_DIR = original_runtime
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.RUNTIME_REPORTS_DIR = original_reports
                self.bridge.AUDIT_PATH = original_audit

    def test_startup_reconciles_expired_and_legacy_waiting_approval_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime"
            original_missions = self.bridge.MISSIONS_PATH
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.save_missions([
                    {
                        "id": "mission-expired-startup",
                        "owner": "backtest_analyst",
                        "toolId": "codex_cli_task",
                        "status": "waiting_approval",
                        "approval": {
                            "required": True,
                            "state": "pending",
                            "expiresAt": "2000-01-01T00:00:00+00:00",
                        },
                    },
                    {
                        "id": "mission-legacy-waiting",
                        "owner": "manager",
                        "toolId": "manager_mission",
                        "status": "waiting_approval",
                        "approval": {"required": False, "state": "not_required"},
                    },
                ])
                count = self.bridge.reconcile_stale_approval_missions()
                self.assertEqual(count, 2)
                expired = self.bridge.find_mission("mission-expired-startup")
                legacy = self.bridge.find_mission("mission-legacy-waiting")
                self.assertEqual(expired["status"], "blocked")
                self.assertEqual(expired["approval"]["state"], "expired")
                self.assertEqual(legacy["status"], "blocked")
                self.assertEqual(legacy["errorCode"], "legacy_waiting_without_required_approval")
                audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)
                self.assertEqual(sum(item.get("type") == "mission.approval_reconciled" for item in audit), 2)
                self.assertTrue(all(item.get("realToolExecuted") is False for item in audit))
            finally:
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.AUDIT_PATH = original_audit

    def test_static_publish_boundary_stays_closed(self) -> None:
        allowed = self.bridge.BridgeHandler.static_path_allowed
        self.assertTrue(allowed(None, "/"))
        self.assertTrue(allowed(None, "/frontend/index.html"))
        self.assertTrue(allowed(None, "/contracts/agents/agents.json"))
        self.assertFalse(allowed(None, "/backend/local-runner/bridge_server.py"))
        self.assertFalse(allowed(None, "/runner/codex_cli_runner.py"))
        self.assertFalse(allowed(None, "/data/runtime/bridge-audit.jsonl"))
        self.assertFalse(allowed(None, "/.gitignore"))


if __name__ == "__main__":
    unittest.main()
