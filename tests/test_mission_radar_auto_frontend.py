from pathlib import Path
import json
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "frontend" / "src" / "app" / "main.js"
STYLES_PATH = ROOT / "frontend" / "src" / "app" / "styles.css"
INDEX_PATH = ROOT / "frontend" / "index.html"


class MissionRadarAutoFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main = MAIN_PATH.read_text(encoding="utf-8")
        cls.styles = STYLES_PATH.read_text(encoding="utf-8")
        cls.index = INDEX_PATH.read_text(encoding="utf-8")

    def block(self, start: str, end: str) -> str:
        start_index = self.main.index(start)
        return self.main[start_index:self.main.index(end, start_index)]

    def function_source(self, name: str) -> str:
        start = self.main.index(f"function {name}(")
        end = self.main.find("\nfunction ", start + 1)
        return self.main[start:] if end < 0 else self.main[start:end]

    def node_binary(self) -> str:
        candidates = [
            shutil.which("node"),
            str(
                Path.home()
                / ".cache"
                / "codex-runtimes"
                / "codex-primary-runtime"
                / "dependencies"
                / "node"
                / "bin"
                / "node.exe"
            ),
        ]
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                return candidate
        self.skipTest("Node.js is required for frontend behavior regressions")

    def run_node(self, script: str) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            script_path = Path(directory) / "mission-radar-regression.js"
            script_path.write_text(script, encoding="utf-8")
            result = subprocess.run(
                [self.node_binary(), str(script_path)],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        return json.loads(result.stdout)

    def test_mission_center_has_only_four_operational_columns(self) -> None:
        block = self.block("const MISSION_KANBAN_COLUMNS", "function getModalSurface")
        self.assertEqual(
            re.findall(r'\{ id: "([a-z_]+)", label:', block),
            ["running", "blocked", "completed", "failed"],
        )
        self.assertNotIn('id: "queued"', block)
        self.assertNotIn('id: "waiting_approval"', block)
        self.assertNotIn('label: "รออนุมัติ"', block)

    def test_waiting_approval_is_presented_as_blocked_not_a_sixth_column(self) -> None:
        self.assertIn('waiting_approval: "ติดขัด"', self.main)
        block = self.block("function getMissionPresentationStatus", "function isBackendAutoEligibleMission")
        self.assertIn('status === "waiting_approval" ? "blocked" : status', block)
        self.assertIn('if (count("waiting_approval") > 0) return "blocked";', block)
        self.assertNotIn('return "waiting_approval";', block)

    def test_mission_status_and_approval_predicate_execute_exactly(self) -> None:
        script = "\n".join([
            self.function_source("normalizeMissionStatus"),
            self.function_source("missionRequiresExplicitHumanApproval"),
            self.function_source("getMissionAutomaticPolicy"),
            self.function_source("isBackendAutoSafeMission"),
            self.function_source("getMissionPresentationStatus"),
            "process.stdout.write(JSON.stringify({",
            "safeWaiting:getMissionPresentationStatus({status:'waiting_approval',requiresHumanApproval:false,approval:{required:false}}),",
            "riskyWaiting:getMissionPresentationStatus({status:'waiting_approval',requiresHumanApproval:true,approval:{required:true}}),",
            "delegatedWaiting:getMissionPresentationStatus({status:'queued',subtaskIds:['a'],delegation:{subtaskCount:1,subtaskStatusCounts:{waiting_approval:1}}}),",
            "bothTrue:missionRequiresExplicitHumanApproval({requiresHumanApproval:true,approval:{required:true}}),",
            "onlyMissionFlag:missionRequiresExplicitHumanApproval({requiresHumanApproval:true,approval:{required:false}}),",
            "onlyApprovalFlag:missionRequiresExplicitHumanApproval({requiresHumanApproval:false,approval:{required:true}}),",
            "safePolicy:isBackendAutoSafeMission({requiresHumanApproval:false,approval:{required:false},automaticPolicy:{mode:'backend_auto_safe',decision:'allowed',humanApprovalRequired:false}}),",
            "missingPolicyFlag:isBackendAutoSafeMission({requiresHumanApproval:false,approval:{required:false},automaticPolicy:{mode:'backend_auto_safe',decision:'allowed'}}),",
            "contradictorySafePolicy:isBackendAutoSafeMission({requiresHumanApproval:true,approval:{required:false},automaticPolicy:{mode:'backend_auto_safe',decision:'allowed',humanApprovalRequired:false}})",
            "}));",
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["safeWaiting"], "blocked")
        self.assertEqual(payload["riskyWaiting"], "blocked")
        self.assertEqual(payload["delegatedWaiting"], "blocked")
        self.assertTrue(payload["bothTrue"])
        self.assertFalse(payload["onlyMissionFlag"])
        self.assertFalse(payload["onlyApprovalFlag"])
        self.assertTrue(payload["safePolicy"])
        self.assertFalse(payload["missingPolicyFlag"])
        self.assertFalse(payload["contradictorySafePolicy"])

    def test_explicit_approval_ui_requires_both_backend_flags(self) -> None:
        predicate = self.block(
            "function missionRequiresExplicitHumanApproval",
            "function getMissionAutomaticPolicy",
        )
        self.assertIn("mission?.requiresHumanApproval === true", predicate)
        self.assertIn("mission?.approval?.required === true", predicate)

        readiness = self.block(
            "function isMissionReadyForExplicitExecution",
            "function setMissionExecuteStatus",
        )
        self.assertIn("!missionRequiresExplicitHumanApproval(mission)", readiness)

        detail = self.block("function renderMissionDetail", "function openTaskDetail")
        self.assertIn("const explicitHumanApproval = missionRequiresExplicitHumanApproval(mission)", detail)
        self.assertIn("if (explicitHumanApproval)", detail)
        self.assertIn("&& missionRequiresExplicitHumanApproval(mission)", detail)
        self.assertIn('els.modalKanbanApprove.hidden = !canRecordApproval', detail)
        self.assertIn('els.modalKanbanReject.hidden = !canRecordApproval', detail)

        decision = self.block(
            "async function recordKanbanApprovalDecision",
            "async function executeApprovedKanbanMission",
        )
        self.assertIn("!missionRequiresExplicitHumanApproval(mission)", decision)

    def test_safe_mission_detail_uses_automatic_policy_without_approval_copy(self) -> None:
        policy = self.block("function getMissionAutomaticPolicy", "function getMissionPresentationStatus")
        for marker in (
            'policy.mode === "backend_auto_safe"',
            'policy.decision === "allowed"',
            "policy.humanApprovalRequired === false",
            'return "ทำงานอัตโนมัติ • งานภายในหรืออ่านอย่างเดียว"',
        ):
            self.assertIn(marker, policy)
        detail = self.block("function renderMissionDetail", "function openTaskDetail")
        self.assertIn('appendMissionDetailRow(facts, "นโยบายการทำงาน", missionAutomaticPolicyLabel(mission))', detail)
        self.assertNotIn('"การอนุมัติ", autoEligible', detail)
        self.assertIn("Frontend จะแสดงเฉพาะสถานะและผลลัพธ์", detail)

    def test_mission_center_summary_lists_blocked_completed_and_failed_separately(self) -> None:
        block = self.block("function renderGameModal", "function gameModalFocusableElements")
        self.assertIn('["ติดขัด", String(counts.blocked || 0)]', block)
        self.assertIn('["เสร็จแล้ว", String(counts.completed || 0)]', block)
        self.assertIn('["ไม่สำเร็จ", String(counts.failed || 0)]', block)
        self.assertNotIn('["รออนุมัติ",', block)
        self.assertIn(
            "งานเสี่ยงสูงที่ต้องยืนยันจะแสดงในคอลัมน์ติดขัด",
            self.main,
        )
        self.assertNotIn(
            "กดโต๊ะเพื่อดูงานที่รอเริ่ม กำลังทำ รออนุมัติ",
            self.main,
        )

    def test_radar_normalizes_immutable_once_daily_bangkok_schedule(self) -> None:
        block = self.block("function normalizeRadarSchedule", "function normalizeRadarServiceHealth")
        self.assertIn('const INDICATOR_SCOUT_DEFAULT_TIME = "09:00";', self.main)
        self.assertIn('const INDICATOR_SCOUT_TIMEZONE = "Asia/Bangkok";', self.main)
        self.assertIn("const requestedEnabled = true", block)
        self.assertIn("const configuredTime = INDICATOR_SCOUT_DEFAULT_TIME", block)
        self.assertIn("times: [configuredTime]", block)
        self.assertIn("maximumRunsPerDay: 1", block)
        self.assertIn("timezone: INDICATOR_SCOUT_TIMEZONE", block)
        self.assertIn("Number.isInteger(numeric)", block)
        self.assertNotIn("schedule.requestedEnabled", block)
        self.assertNotIn("schedule.times", block)
        self.assertNotIn("times.slice(0, 2)", block)

    def test_radar_schedule_and_service_normalizers_execute_fail_closed(self) -> None:
        script = "\n".join([
            'const INDICATOR_SCOUT_DEFAULT_TIME = "09:00";',
            'const INDICATOR_SCOUT_TIMEZONE = "Asia/Bangkok";',
            "function safeDashboardDisplayText(value, fallback='') { const text=String(value ?? '').trim(); return text || fallback; }",
            self.function_source("normalizeRadarSchedule"),
            self.function_source("normalizeRadarServiceHealth"),
            "const schedule=normalizeRadarSchedule({requestedEnabled:false,effectiveEnabled:true,times:['7:05','12:00'],maximumRunsPerDay:2,runsReservedToday:1,remainingRunsToday:1});",
            "const unavailable=normalizeRadarSchedule({requestedEnabled:false,effectiveEnabled:false,times:['23:59']});",
            "const fractional=normalizeRadarSchedule({requestedEnabled:true,effectiveEnabled:true,runsReservedToday:0.5,remainingRunsToday:0.5});",
            "const healthy=normalizeRadarServiceHealth({status:'ready',adapterStatus:'ready',sourceStatus:'ready',retryAvailable:true,retryEndpoint:'/api/props/left_audit_crystals/workflow/actions',retryActionId:'discover_new_indicators',automaticCorrectiveRetry:{supported:true,status:'deferred',attempted:2,remaining:0,totalAttemptsQueued:2,nextAttemptAt:'2026-08-23T04:00:00Z',sameMission:true,sameDailyReservation:true,newDailyReservation:false},sourceHealth:[{sourceId:'codex_web_search',label:'Web',status:'ready'}]});",
            "const tampered=normalizeRadarServiceHealth({retryAvailable:true,retryEndpoint:'/api/evil',retryActionId:'discover_new_indicators'});",
            "process.stdout.write(JSON.stringify({schedule,unavailable,fractional,healthy,tampered}));",
        ])
        payload = self.run_node(script)
        self.assertTrue(payload["schedule"]["requestedEnabled"])
        self.assertTrue(payload["schedule"]["effectiveEnabled"])
        self.assertEqual(payload["schedule"]["times"], ["09:00"])
        self.assertEqual(payload["schedule"]["maximumRunsPerDay"], 1)
        self.assertEqual(payload["schedule"]["timezone"], "Asia/Bangkok")
        self.assertEqual(payload["schedule"]["runsReservedToday"], 1)
        self.assertEqual(payload["schedule"]["remainingRunsToday"], 0)
        self.assertTrue(payload["unavailable"]["requestedEnabled"])
        self.assertFalse(payload["unavailable"]["effectiveEnabled"])
        self.assertEqual(payload["unavailable"]["times"], ["09:00"])
        self.assertIsNone(payload["fractional"]["runsReservedToday"])
        self.assertIsNone(payload["fractional"]["remainingRunsToday"])
        self.assertFalse(payload["healthy"]["retryAvailable"])
        self.assertEqual(payload["healthy"]["retryEndpoint"], "")
        self.assertEqual(payload["healthy"]["retryActionId"], "")
        self.assertEqual(payload["healthy"]["sourceHealth"][0]["sourceId"], "codex_web_search")
        self.assertTrue(payload["healthy"]["automaticCorrectiveRetry"]["supported"])
        self.assertEqual(payload["healthy"]["automaticCorrectiveRetry"]["status"], "deferred")
        self.assertEqual(payload["healthy"]["automaticCorrectiveRetry"]["attempted"], 2)
        self.assertEqual(
            payload["healthy"]["automaticCorrectiveRetry"]["nextAttemptAt"],
            "2026-08-23T04:00:00Z",
        )
        self.assertFalse(payload["healthy"]["automaticCorrectiveRetry"]["newDailyReservation"])
        self.assertFalse(payload["tampered"]["retryAvailable"])
        self.assertEqual(payload["tampered"]["retryEndpoint"], "")

    def test_radar_today_run_truth_distinguishes_schedule_running_failure_and_verified_empty(self) -> None:
        script = "\n".join([
            'const INDICATOR_SCOUT_DEFAULT_TIME = "09:00";',
            'const INDICATOR_SCOUT_TIMEZONE = "Asia/Bangkok";',
            "const INDICATOR_SCOUT_EXPECTED_BATCH_SIZE = 6;",
            self.function_source("safeDashboardDisplayText"),
            self.function_source("indicatorScoutBangkokDateKey"),
            self.function_source("normalizeRadarSchedule"),
            self.function_source("normalizeRadarServiceHealth"),
            self.function_source("normalizeRadarRunStatus"),
            self.function_source("radarBangkokMinuteOfDay"),
            self.function_source("getRadarTodayRunState"),
            "const beforeNine='2026-08-23T01:30:00Z';",
            "const afterNine='2026-08-23T03:00:00Z';",
            "const runAt='2026-08-23T09:01:00+07:00';",
            "const retryAt='2026-08-23T04:00:00Z';",
            "const awaiting=getRadarTodayRunState({todayEntries:[],schedule:{effectiveEnabled:true,nextRunAt:'2026-08-23T02:00:00Z'}},beforeNine);",
            "const running=getRadarTodayRunState({todayEntries:[],schedule:{lastRunAt:runAt},serviceHealth:{status:'running',activeMissionId:'mission-safe'}},afterNine);",
            "const correcting=getRadarTodayRunState({todayEntries:[],schedule:{lastRunAt:runAt},serviceHealth:{status:'corrective-running'}},afterNine);",
            "const repairQueued=getRadarTodayRunState({todayEntries:[],schedule:{lastRunAt:runAt,lastRunStatus:'failed',lastResultKind:'invalid_output',runsReservedToday:1,nextRunAt:'2026-08-24T02:00:00Z'},serviceHealth:{status:'degraded',automaticCorrectiveRetry:{supported:true,status:'queued',attempted:1,remaining:1,totalAttemptsQueued:1,nextAttemptAt:retryAt,sameMission:true,sameDailyReservation:true,newDailyReservation:false}}},afterNine);",
            "const repairDeferred=getRadarTodayRunState({todayEntries:[],schedule:{lastRunAt:runAt,lastRunStatus:'deferred',lastResultKind:'radar_batch_completion_repair_requeued',runsReservedToday:1},serviceHealth:{status:'degraded',automaticCorrectiveRetry:{supported:true,status:'deferred',attempted:2,remaining:0,totalAttemptsQueued:2,nextAttemptAt:retryAt,sameMission:true,sameDailyReservation:true,newDailyReservation:false}}},afterNine);",
            "const untrustedRepair=getRadarTodayRunState({todayEntries:[],schedule:{lastRunAt:runAt,lastRunStatus:'failed',lastResultKind:'invalid_output',runsReservedToday:1},serviceHealth:{automaticCorrectiveRetry:{supported:true,status:'queued',nextAttemptAt:retryAt,sameMission:true,sameDailyReservation:true,newDailyReservation:true}}},afterNine);",
            "const failed=getRadarTodayRunState({todayEntries:[],schedule:{lastRunAt:runAt,lastRunStatus:'failed',lastResultKind:'invalid_output',runsReservedToday:1}},afterNine);",
            "const degraded=getRadarTodayRunState({todayEntries:[],schedule:{lastRunAt:runAt,runsReservedToday:1},serviceHealth:{status:'degraded'}},afterNine);",
            "const verifiedEmpty=getRadarTodayRunState({todayEntries:[],schedule:{lastRunAt:runAt,lastRunStatus:'completed'}},afterNine);",
            "const delayed=getRadarTodayRunState({todayEntries:[],schedule:{effectiveEnabled:true}},afterNine);",
            "const complete=getRadarTodayRunState({expectedBatchSize:6,todayEntries:Array.from({length:6},(_,id)=>({id}))},afterNine);",
            "const partial=getRadarTodayRunState({expectedBatchSize:6,todayEntries:[{id:1},{id:2}]},afterNine);",
            "process.stdout.write(JSON.stringify({awaiting,running,correcting,repairQueued,repairDeferred,untrustedRepair,failed,degraded,verifiedEmpty,delayed,complete,partial}));",
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["awaiting"]["state"], "awaiting_schedule")
        self.assertEqual(payload["running"]["state"], "running")
        self.assertEqual(payload["correcting"]["state"], "corrective_running")
        self.assertEqual(payload["repairQueued"]["state"], "corrective_running")
        self.assertEqual(payload["repairQueued"]["tone"], "running")
        self.assertEqual(payload["repairQueued"]["title"], "กำลังหาให้ครบ 6 รายการ")
        self.assertEqual(payload["repairQueued"]["nextAttemptAt"], "2026-08-23T04:00:00Z")
        self.assertEqual(payload["repairQueued"]["nextRunAt"], "2026-08-23T04:00:00Z")
        self.assertEqual(payload["repairDeferred"]["state"], "corrective_running")
        self.assertIn("พักตามขีดจำกัดชั่วคราว", payload["repairDeferred"]["detail"])
        self.assertEqual(payload["repairDeferred"]["nextAttemptAt"], "2026-08-23T04:00:00Z")
        self.assertEqual(payload["untrustedRepair"]["state"], "corrective_failed")
        self.assertEqual(payload["failed"]["state"], "corrective_failed")
        self.assertEqual(payload["failed"]["tone"], "error")
        self.assertEqual(payload["failed"]["error"], "invalid_output")
        self.assertEqual(payload["degraded"]["state"], "degraded")
        self.assertEqual(payload["degraded"]["tone"], "warning")
        self.assertEqual(payload["verifiedEmpty"]["state"], "verified_empty")
        self.assertEqual(payload["delayed"]["state"], "delayed")
        self.assertEqual(payload["complete"]["state"], "verified_results")
        self.assertIn("6/6", payload["complete"]["title"])
        self.assertEqual(payload["partial"]["state"], "delayed")
        self.assertNotIn("2/6", payload["partial"]["title"])

    def test_radar_today_panel_shows_backend_run_truth_and_six_item_progress_without_controls(self) -> None:
        normalizer = self.block("function normalizeIndicatorScoutDomain", "function normalizeTradingSystemPortalDomain")
        renderer = self.block("function renderIndicatorScoutPanel", "function renderFxBiasTable")
        notice = self.block("function createRadarTodayRunNotice", "function workflowBiasLabel")
        self.assertIn("expectedBatchSize", normalizer)
        self.assertIn("INDICATOR_SCOUT_EXPECTED_BATCH_SIZE", normalizer)
        self.assertIn(
            "projectedTodayEntries.length === expectedBatchSize",
            normalizer,
        )
        self.assertIn("createRadarTodayRunNotice(domain)", renderer)
        self.assertIn("`${entries.length}/${expectedBatchSize} รายการ`", renderer)
        self.assertNotIn("วันนี้ยังไม่มีรายการใหม่จาก Backend", renderer)
        self.assertIn('notice.className = "workflow-radar-run-state"', notice)
        self.assertIn('notice.dataset.state = runState.state', notice)
        self.assertIn('notice.setAttribute("role", runState.tone === "error" ? "alert" : "status")', notice)
        self.assertIn('progress.textContent = `${todayCount}/${expectedBatchSize}`', notice)
        self.assertIn('runState.nextAttemptAt ? "ลองหาให้ครบอีกครั้ง" : "รอบถัดไป"', notice)
        self.assertNotIn("button", notice.lower())
        self.assertNotIn("approval", notice.lower())
        for selector in (
            '.workflow-radar-run-state[data-tone="ready"]',
            '.workflow-radar-run-state[data-tone="running"]',
            '.workflow-radar-run-state[data-tone="error"]',
            ".workflow-radar-run-state-heading",
        ):
            self.assertIn(selector, self.styles)

    def test_radar_health_is_read_only_and_retry_is_hard_disabled(self) -> None:
        normalizer = self.block("function normalizeRadarServiceHealth", "function normalizeIndicatorScoutDomain")
        for marker in (
            "service.sourceHealth",
            "service.sourceStatus",
            "service.adapterStatus",
            "retryAvailable: false",
            'retryEndpoint: ""',
            'retryActionId: ""',
        ):
            self.assertIn(marker, normalizer)

        card = self.block("function createRadarRailTruthCard", "function createBackendOwnedDailyScheduleCard")
        self.assertIn("service.sourceHealth.forEach", card)
        self.assertIn("service.lastError || schedule.lastError", card)
        self.assertIn('not_connected_optional: "Backend ยังไม่ยืนยันการเชื่อมต่อ"', card)
        self.assertIn('configured_not_connected: "บันทึกการตั้งค่าแล้ว • ยังไม่เชื่อมต่อ"', card)
        self.assertNotIn("configured_read_only", card)
        self.assertNotIn("retryAvailable", card)
        self.assertNotIn("ลองค้นหาใหม่", card)
        self.assertNotIn("data-radar-retry", card)
        self.assertNotIn("approval", card.lower())
        self.assertNotIn("อนุมัติ", card)

    def test_radar_has_no_manual_save_retry_or_run_now_api_path(self) -> None:
        for forbidden in (
            "INDICATOR_SCOUT_WORKFLOW_ENDPOINT",
            "function createRadarScheduleCard",
            "function radarRetryQuotaAvailable",
            "async function saveRadarSchedule",
            "async function retryRadarDiscovery",
            "ลองค้นหาใหม่",
        ):
            self.assertNotIn(forbidden, self.main)

        radar_start = self.main.index("  left_audit_crystals: {", self.main.index("const WORKFLOW_DASHBOARD_FALLBACKS"))
        radar_end = self.main.index("  left_signal_cube: {", radar_start)
        radar_fallback = self.main[radar_start:radar_end]
        self.assertIn("actions: []", radar_fallback)
        self.assertNotIn('id: "discover_new_indicators"', radar_fallback)
        self.assertNotIn('id: "save_indicator_scout_schedule"', radar_fallback)

        submit = self.block("async function submitWorkflowDashboardAction", "function renderPropDashboard")
        guard = "if (BACKEND_OWNED_DAILY_ACTION_IDS.has(actionId)) return;"
        self.assertIn(guard, submit)
        self.assertLess(submit.index(guard), submit.index("postJson("))

    def test_cache_version_includes_radar_truth_in_latest_build(self) -> None:
        self.assertIn("20260827-google-auth-v074", self.index)
        self.assertNotIn("20260824-ea-optimization-lab-v072", self.index)
        self.assertNotIn("20260822-ai-meeting-chat-first-v068", self.index)
        self.assertNotIn("20260814-ai-meeting-preview-v063", self.index)
        self.assertNotIn("20260814-radar-contract-v062", self.index)
        self.assertNotIn("20260814-daily-news-direct-v060", self.index)

    def test_radar_uses_custom_rail_not_generic_mission_action_cards(self) -> None:
        settings = self.block("function renderWorkflowSettingsRail", "function getWorkflowHandoffReports")
        radar_branch = settings[
            settings.index("if (subject?.id === INDICATOR_SCOUT_PROP_ID)"):
            settings.index("const actions = workflowRailActions", settings.index("if (subject?.id === INDICATOR_SCOUT_PROP_ID)"))
        ]
        self.assertIn("renderRadarSettingsRail(dashboard, identity)", radar_branch)
        self.assertIn("return;", radar_branch)
        custom_rail = self.block("function renderRadarSettingsRail", "function workflowRailActions")
        self.assertIn('createBackendOwnedDailyScheduleCard(dashboard, "Radar ทำงานอัตโนมัติวันละครั้ง")', custom_rail)
        self.assertIn("createRadarRailTruthCard(dashboard)", custom_rail)
        self.assertNotIn("createWorkflowActionCard", custom_rail)
        self.assertNotIn("document.createElement(\"form\")", custom_rail)
        self.assertNotIn("document.createElement(\"button\")", custom_rail)
        self.assertNotIn("อนุมัติ", custom_rail)

    def test_radar_styles_cover_read_only_schedule_health_and_error_states(self) -> None:
        for selector in (
            ".workflow-radar-schedule",
            ".workflow-radar-source-health",
            ".workflow-radar-service-error",
            ".workflow-radar-action-status",
        ):
            self.assertIn(selector, self.styles)


if __name__ == "__main__":
    unittest.main()
