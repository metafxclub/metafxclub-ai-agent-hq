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

    def test_mission_center_has_only_five_operational_columns(self) -> None:
        block = self.block("const MISSION_KANBAN_COLUMNS", "function getModalSurface")
        self.assertEqual(
            re.findall(r'\{ id: "([a-z_]+)", label:', block),
            ["queued", "running", "blocked", "completed", "failed"],
        )
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

    def test_radar_normalizes_once_daily_bangkok_schedule(self) -> None:
        block = self.block("function normalizeRadarSchedule", "function normalizeRadarServiceHealth")
        self.assertIn('const INDICATOR_SCOUT_DEFAULT_TIME = "09:00";', self.main)
        self.assertIn('const INDICATOR_SCOUT_TIMEZONE = "Asia/Bangkok";', self.main)
        self.assertIn("typeof schedule.requestedEnabled === \"boolean\"", block)
        self.assertIn("times: [configuredTime]", block)
        self.assertIn("maximumRunsPerDay: 1", block)
        self.assertIn("timezone: INDICATOR_SCOUT_TIMEZONE", block)
        self.assertIn("Number.isInteger(numeric)", block)
        self.assertNotIn("times.slice(0, 2)", block)

    def test_radar_schedule_and_retry_normalizers_execute_fail_closed(self) -> None:
        script = "\n".join([
            'const INDICATOR_SCOUT_DEFAULT_TIME = "09:00";',
            'const INDICATOR_SCOUT_TIMEZONE = "Asia/Bangkok";',
            'const INDICATOR_SCOUT_WORKFLOW_ENDPOINT = "/api/props/left_audit_crystals/workflow/actions";',
            "function workflowDomainArray(...values) { return values.find((value) => Array.isArray(value)) || []; }",
            "function safeDashboardDisplayText(value, fallback='') { const text=String(value ?? '').trim(); return text || fallback; }",
            self.function_source("normalizeRadarSchedule"),
            self.function_source("normalizeRadarServiceHealth"),
            "const schedule=normalizeRadarSchedule({requestedEnabled:false,effectiveEnabled:true,times:['7:05','12:00'],maximumRunsPerDay:2,runsReservedToday:1,remainingRunsToday:1});",
            "const requestedOnly=normalizeRadarSchedule({requestedEnabled:true,times:['09:00']});",
            "const fractional=normalizeRadarSchedule({requestedEnabled:true,effectiveEnabled:true,runsReservedToday:0.5,remainingRunsToday:0.5});",
            "const healthy=normalizeRadarServiceHealth({status:'ready',adapterStatus:'ready',sourceStatus:'ready',retryAvailable:true,retryEndpoint:INDICATOR_SCOUT_WORKFLOW_ENDPOINT,retryActionId:'discover_new_indicators',sourceHealth:[{sourceId:'codex_web_search',label:'Web',status:'ready'}]});",
            "const tampered=normalizeRadarServiceHealth({retryAvailable:true,retryEndpoint:'/api/evil',retryActionId:'discover_new_indicators'});",
            "const missingFlag=normalizeRadarServiceHealth({retryEndpoint:INDICATOR_SCOUT_WORKFLOW_ENDPOINT,retryActionId:'discover_new_indicators'});",
            "process.stdout.write(JSON.stringify({schedule,requestedOnly,fractional,healthy,tampered,missingFlag}));",
        ])
        payload = self.run_node(script)
        self.assertFalse(payload["schedule"]["requestedEnabled"])
        self.assertFalse(payload["schedule"]["effectiveEnabled"])
        self.assertEqual(payload["schedule"]["times"], ["07:05"])
        self.assertEqual(payload["schedule"]["maximumRunsPerDay"], 1)
        self.assertEqual(payload["schedule"]["timezone"], "Asia/Bangkok")
        self.assertEqual(payload["schedule"]["runsReservedToday"], 1)
        self.assertEqual(payload["schedule"]["remainingRunsToday"], 0)
        self.assertTrue(payload["requestedOnly"]["requestedEnabled"])
        self.assertFalse(payload["requestedOnly"]["effectiveEnabled"])
        self.assertIsNone(payload["fractional"]["runsReservedToday"])
        self.assertIsNone(payload["fractional"]["remainingRunsToday"])
        self.assertTrue(payload["healthy"]["retryAvailable"])
        self.assertEqual(payload["healthy"]["sourceHealth"][0]["sourceId"], "codex_web_search")
        self.assertFalse(payload["tampered"]["retryAvailable"])
        self.assertEqual(payload["tampered"]["retryEndpoint"], "")
        self.assertFalse(payload["missingFlag"]["retryAvailable"])

    def test_radar_health_and_retry_are_backend_authoritative_and_fail_closed(self) -> None:
        normalizer = self.block("function normalizeRadarServiceHealth", "function normalizeIndicatorScoutDomain")
        for marker in (
            "service.sourceHealth",
            "service.sourceStatus",
            "service.adapterStatus",
            'retryEndpoint === INDICATOR_SCOUT_WORKFLOW_ENDPOINT',
            'retryActionId === "discover_new_indicators"',
            "service.retryAvailable === true && retryContractValid",
        ):
            self.assertIn(marker, normalizer)

        card = self.block("function createRadarRailTruthCard", "function createRadarScheduleCard")
        self.assertIn("service.sourceHealth.forEach", card)
        self.assertIn("service.lastError || schedule.lastError", card)
        self.assertIn('not_connected_optional: "ยังไม่เชื่อม • ตัวเลือก"', card)
        self.assertIn('configured_not_connected: "บันทึกการตั้งค่าแล้ว • ยังไม่เชื่อมต่อ"', card)
        self.assertNotIn("configured_read_only", card)
        self.assertIn("service.retryAvailable === true && radarRetryQuotaAvailable(schedule)", card)
        self.assertIn('retry.textContent = inFlight ? "กำลังลองใหม่..." : "ลองค้นหาใหม่"', card)
        self.assertNotIn("approval", card.lower())
        self.assertNotIn("อนุมัติ", card)

    def test_radar_schedule_and_retry_use_exact_endpoint_and_bounded_payloads(self) -> None:
        self.assertIn(
            'const INDICATOR_SCOUT_WORKFLOW_ENDPOINT = "/api/props/left_audit_crystals/workflow/actions";',
            self.main,
        )
        schedule = self.block("async function saveRadarSchedule", "async function retryRadarDiscovery")
        self.assertIn("const idempotencyKey = createWorkflowIdempotencyKey()", schedule)
        self.assertIn("postJson(INDICATOR_SCOUT_WORKFLOW_ENDPOINT", schedule)
        self.assertIn('actionId: "save_indicator_scout_schedule"', schedule)
        self.assertIn("form: { enabled: enabledControl.checked === true, times: [rawTime] }", schedule)
        self.assertNotIn("timezone:", schedule)

        retry = self.block("async function retryRadarDiscovery", "function workflowRailActions")
        self.assertIn("const schedule = normalizeRadarSchedule(", retry)
        self.assertIn("service.retryAvailable !== true", retry)
        self.assertIn("service.retryEndpoint !== INDICATOR_SCOUT_WORKFLOW_ENDPOINT", retry)
        self.assertIn('service.retryActionId !== "discover_new_indicators"', retry)
        self.assertIn("!radarRetryQuotaAvailable(schedule)", retry)
        self.assertIn("form: {}", retry)
        self.assertIn("const idempotencyKey = createWorkflowIdempotencyKey()", retry)
        self.assertNotIn("อนุมัติ", retry)

    def test_radar_retry_quota_rejects_zero_unknown_and_fractional_values(self) -> None:
        script = "\n".join([
            self.function_source("radarRetryQuotaAvailable"),
            "process.stdout.write(JSON.stringify({",
            "one:radarRetryQuotaAvailable({remainingRunsToday:1}),",
            "zero:radarRetryQuotaAvailable({remainingRunsToday:0}),",
            "unknown:radarRetryQuotaAvailable({remainingRunsToday:null}),",
            "fractional:radarRetryQuotaAvailable({remainingRunsToday:0.5}),",
            "stringValue:radarRetryQuotaAvailable({remainingRunsToday:'1'})",
            "}));",
        ])
        payload = self.run_node(script)
        self.assertTrue(payload["one"])
        self.assertFalse(payload["zero"])
        self.assertFalse(payload["unknown"])
        self.assertFalse(payload["fractional"])
        self.assertFalse(payload["stringValue"])

    def test_cache_version_is_mission_radar_v061(self) -> None:
        self.assertIn("20260814-radar-contract-v062", self.index)
        self.assertNotIn("20260814-daily-news-direct-v060", self.index)

    def test_radar_uses_custom_rail_not_generic_mission_action_cards(self) -> None:
        settings = self.block("function renderWorkflowSettingsRail", "function getWorkflowHandoffReports")
        radar_branch = settings[
            settings.index("if (subject?.id === INDICATOR_SCOUT_PROP_ID)"):
            settings.index("const actions = workflowRailActions", settings.index("if (subject?.id === INDICATOR_SCOUT_PROP_ID)"))
        ]
        self.assertIn("renderRadarSettingsRail(dashboard, identity)", radar_branch)
        self.assertIn("return;", radar_branch)
        custom_rail = self.block("function renderRadarSettingsRail", "async function saveRadarSchedule")
        self.assertIn("createRadarScheduleCard(dashboard)", custom_rail)
        self.assertIn("createRadarRailTruthCard(dashboard)", custom_rail)
        self.assertNotIn("createWorkflowActionCard", custom_rail)
        self.assertNotIn("อนุมัติ", custom_rail)

    def test_radar_styles_cover_schedule_health_error_and_retry_states(self) -> None:
        for selector in (
            ".workflow-radar-schedule",
            ".workflow-radar-source-health",
            ".workflow-radar-service-error",
            ".workflow-radar-retry",
            ".workflow-radar-action-status",
        ):
            self.assertIn(selector, self.styles)


if __name__ == "__main__":
    unittest.main()
