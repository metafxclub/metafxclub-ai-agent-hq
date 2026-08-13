from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]

WORKFLOW_PROP_IDS = (
    "codex_mcp_portal",
    "left_server_racks",
    "right_server_racks",
    "right_tool_console",
    "left_audit_crystals",
    "left_signal_cube",
    "terminal_workstation",
    "right_status_crystals",
)


class DashboardWorkflowFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        cls.main = (ROOT / "frontend" / "src" / "app" / "main.js").read_text(encoding="utf-8")
        cls.styles = (ROOT / "frontend" / "src" / "app" / "styles.css").read_text(encoding="utf-8")
        cls.role_map = json.loads(
            (ROOT / "contracts" / "props" / "property-role-map.json").read_text(encoding="utf-8")
        )["properties"]

    def test_one_reusable_workspace_serves_all_eight_independent_dashboard_props(self):
        self.assertEqual(self.index.count('id="modalWorkflowDashboardWorkspace"'), 1)
        self.assertNotIn('id="workflowDashboardPipeline"', self.index)
        self.assertNotIn('id="workflowDashboardIdentityMark"', self.index)
        self.assertNotIn('id="workflowDashboardIdentityLabel"', self.index)
        self.assertNotIn('id="workflowDashboardStage"', self.index)
        self.assertNotIn('id="workflowDashboardTitle"', self.index)
        self.assertNotIn('id="workflowDashboardSummary"', self.index)
        self.assertIn('id="workflowSettingsRail"', self.index)
        self.assertIn('id="workflowSettingsRailContent"', self.index)
        self.assertIn('id="workflowAgentHandoffRail"', self.index)
        self.assertIn('id="workflowHandoffReport"', self.index)
        self.assertIn('id="workflowHandoffTarget"', self.index)
        self.assertIn('id="workflowHandoffAction"', self.index)
        self.assertIn('id="workflowHandoffButton"', self.index)
        self.assertIn('id="workflowDashboardTabs"', self.index)
        self.assertIn('id="workflowDashboardContent"', self.index)
        self.assertIn('id="workflowResultsPanel"', self.index)
        for prop_id in WORKFLOW_PROP_IDS:
            self.assertIn(prop_id, self.main)
        self.assertIn("WORKFLOW_DASHBOARD_PROP_IDS", self.main)
        self.assertIn("WORKFLOW_DASHBOARD_IDENTITIES", self.main)
        self.assertIn("isWorkflowDashboardPropId(subject.id)", self.main)

    def test_settings_and_agent_handoff_live_in_left_rail_not_the_main_workspace(self):
        left_rail_start = self.index.index('id="modalPortraitPanel"')
        left_rail_end = self.index.index('<div class="modal-content-panel">', left_rail_start)
        left_rail = self.index[left_rail_start:left_rail_end]
        workspace_start = self.index.index('id="modalWorkflowDashboardWorkspace"')
        workspace_end = self.index.index('id="modalKanbanPanel"', workspace_start)
        workspace = self.index[workspace_start:workspace_end]

        for control_id in (
            "workflowSettingsRail",
            "workflowSettingsRailContent",
            "workflowAgentHandoffRail",
            "workflowHandoffReport",
            "workflowHandoffTarget",
            "workflowHandoffAction",
            "workflowHandoffButton",
            "workflowHandoffStatus",
        ):
            self.assertIn(f'id="{control_id}"', left_rail)
            self.assertNotIn(f'id="{control_id}"', workspace)

        self.assertRegex(
            left_rail,
            re.compile(r'id="workflowSettingsRail"[^>]*\bhidden\b'),
        )
        self.assertRegex(
            left_rail,
            re.compile(r'id="workflowAgentHandoffRail"[^>]*\bhidden\b'),
        )

    def test_workflow_actions_use_the_guarded_prop_endpoint_and_minimal_payload(self):
        self.assertIn("`/api/props/${encodeURIComponent(propId)}/workflow/actions`", self.main)
        self.assertRegex(
            self.main,
            re.compile(
                r"postJson\(`/api/props/\$\{encodeURIComponent\(propId\)\}/workflow/actions`,\s*\{\s*actionId,\s*form:\s*actionForm,\s*idempotencyKey,?\s*\}\)",
                re.S,
            ),
        )
        self.assertNotIn("/api/dashboard-workflows/action", self.main)
        self.assertNotIn('type = "password"', self.main)
        self.assertIn("WORKFLOW_FIELD_DENY_PATTERN", self.main)

    def test_canonical_tabs_and_actions_are_present(self):
        expected = {
            "systems": "discover_trading_systems",
            "ea_updates": "discover_ea_updates",
            "schedule": "save_discovery_schedule",
            "research_queue": "deep_research_system",
            "builder": "build_strategy_code",
            "code_review": "review_source_code",
            "backtest": "prepare_backtest_plan",
            "optimization": "prepare_optimization_plan",
            "ea_discovery": "prepare_ea_discovery_plan",
        }
        for tab_id, action_id in expected.items():
            self.assertIn(f'id: "{tab_id}"', self.main)
            self.assertIn(f'id: "{action_id}"', self.main)
        self.assertIn('id: "verified_archive"', self.main)
        self.assertIn('id: "outputs"', self.main)

    def test_each_workflow_device_opens_on_main_work_and_only_history_devices_end_with_reports(self):
        expected_last_ids = {
            "codex_mcp_portal": "catalog",
            "left_server_racks": "evidence",
            "right_server_racks": "outputs",
            "right_tool_console": "history",
            "left_audit_crystals": "archive",
            "terminal_workstation": "outputs",
        }
        no_history_props = {"left_signal_cube", "right_status_crystals"}
        single_view_props = {"right_status_crystals": "connections"}
        for prop_id in WORKFLOW_PROP_IDS:
            role = self.role_map[prop_id]
            tabs = role["localTabs"]
            ux = role["dashboardUx"]
            with self.subTest(prop_id=prop_id):
                if prop_id in single_view_props:
                    self.assertEqual(len(tabs), 1)
                    self.assertEqual(tabs[0]["id"], single_view_props[prop_id])
                else:
                    self.assertGreaterEqual(len(tabs), 2)
                self.assertEqual(role["defaultTab"], tabs[0]["id"])
                self.assertEqual(ux["mainWorkTabId"], tabs[0]["id"])
                if prop_id in no_history_props:
                    self.assertIsNone(ux["historyReportTabId"])
                    self.assertIsNone(ux["historyReportTabPosition"])
                    self.assertNotIn(tabs[-1]["id"], {"schedule_history", "activity_history"})
                    continue
                self.assertEqual(ux["historyReportTabId"], expected_last_ids[prop_id])
                self.assertEqual(tabs[-1]["id"], expected_last_ids[prop_id])
                self.assertEqual(tabs[-1]["labelTh"], "ประวัติและรายงาน")
                self.assertEqual(ux["historyReportTabPosition"], "last")

        self.assertIn("const WORKFLOW_DASHBOARD_PRIMARY_TABS", self.main)
        self.assertIn("const WORKFLOW_DASHBOARD_SETTING_TAB_IDS", self.main)
        self.assertIn("const WORKFLOW_DASHBOARD_HISTORY_TAB_IDS", self.main)
        self.assertIn(
            "const visibleTabs = normalizedTabs.filter((tab) => !WORKFLOW_DASHBOARD_SETTING_TAB_IDS.has(tab.id));",
            self.main,
        )
        self.assertIn('id: "history",\n      labelTh: "ประวัติและรายงาน"', self.main)
        self.assertIn(
            'const isPortalCatalog = subject?.id === "codex_mcp_portal" && tab.id === "catalog";',
            self.main,
        )
        self.assertIn('isPortalCatalog ? "คลังและแบบฟอร์มข้อมูล"', self.main)
        self.assertIn("return tabs.find((tab) => tab.id === requested) || tabs[0] || null;", self.main)
        self.assertIn('isHistory ? "ประวัติและรายงาน"', self.main)

    def test_portal_catalog_label_does_not_duplicate_the_final_history_tab(self):
        start = self.main.index("const visibleTabs = normalizedTabs.filter")
        end = self.main.index("const deliveredSourceRows", start)
        normalization = self.main[start:end]
        catalog_label = re.search(r'isPortalCatalog \? "([^"]+)"', normalization)
        history_label = re.search(r'isHistory \? "([^"]+)"', normalization)

        self.assertIsNotNone(catalog_label)
        self.assertIsNotNone(history_label)
        self.assertEqual(catalog_label.group(1), "คลังและแบบฟอร์มข้อมูล")
        self.assertEqual(history_label.group(1), "ประวัติและรายงาน")
        self.assertNotEqual(catalog_label.group(1), history_label.group(1))
        self.assertIn('visibleTabs.push({\n      id: "history"', normalization)

    def test_view_only_tabs_are_truthful_and_survive_backend_schema_merging(self):
        self.assertIn("Google Sheets Connector: Coming Soon", self.main)
        self.assertIn("MetaEditor/Compiler Adapter: Coming Soon", self.main)
        self.assertIn("Compile (Coming Soon)", self.main)
        self.assertNotIn("ตรวจโค้ดและ Compile", self.main)
        self.assertNotIn("ผล Compile จากไฟล์ที่สร้างแล้ว", self.main)
        self.assertIn("const suppliedTabMap = new Map", self.main)
        self.assertIn("(fallback.tabs || []).length", self.main)
        self.assertIn("selectedTab?.emptyMessageTh ||", self.main)

    def test_device_identity_is_used_for_theming_without_duplicate_main_header(self):
        identity_start = self.main.index("const WORKFLOW_DASHBOARD_IDENTITIES")
        identity_end = self.main.index("\n});", identity_start)
        identity_block = self.main[identity_start:identity_end]
        for identity in (
            "world-radar",
            "research-vault",
            "ea-factory",
            "experiment-lab",
            "indicator-scout",
            "market-news-bias",
            "ea-dev-desk",
            "hq-vps-settings",
        ):
            self.assertIn(f'id: "{identity}"', identity_block)
        self.assertNotIn("WORKFLOW_PIPELINE", self.main)
        self.assertNotIn("WORKFLOW_OPERATIONS_PIPELINE", self.main)
        self.assertNotIn("renderWorkflowPipeline", self.main)
        self.assertNotIn("data-workflow-prop", self.main)
        self.assertNotIn("workflow-pipeline", self.styles)
        self.assertNotIn("workflowDashboardIdentityMark", self.main)
        self.assertNotIn("workflowDashboardIdentityLabel", self.main)
        self.assertNotIn("workflowDashboardStage", self.main)
        self.assertNotIn("workflowDashboardTitle", self.main)
        self.assertNotIn("workflowDashboardSummary", self.main)

        tabs_start = self.main.index("function renderWorkflowTabs")
        tabs_end = self.main.index("function workflowAvailabilityCopy", tabs_start)
        tabs_block = self.main[tabs_start:tabs_end]
        self.assertNotIn("index + 1", tabs_block)
        self.assertNotIn('createElement("span")', tabs_block)
        self.assertIn("button.textContent = tab.labelTh", tabs_block)

    def test_catalog_renders_42_field_template_and_deduplication_truth(self):
        start = self.main.index("const WORKFLOW_DISCOVERY_SHEET_COLUMNS")
        end = self.main.index("\n]);", start)
        columns = re.findall(r'^\s*"([a-z][a-z0-9_]*)",?$', self.main[start:end], re.M)
        self.assertEqual(len(columns), 42)
        self.assertEqual(columns[0], "discovery_id")
        self.assertEqual(columns[-1], "notes")
        self.assertIn("template.columns.length", self.main)
        self.assertIn("Google Sheets: Coming Soon", self.main)
        self.assertIn("ยังไม่รวมข้อมูลจาก Google Sheets", self.main)
        self.assertIn("พร้อมตรวจรายการซ้ำกับ Report ในเครื่อง", self.main)
        self.assertIn("Frontend ไม่รับ Token, Credential หรือ Secret", self.main)
        self.assertIn("credentialsAcceptedByFrontend: false", self.main)

    def test_workflow_actions_wait_for_authoritative_read_model_without_false_connection_error(self):
        normalize_start = self.main.index("function normalizeWorkflowDashboard")
        normalize_end = self.main.index("function getWorkflowSelectedTab", normalize_start)
        normalize = self.main[normalize_start:normalize_end]
        availability_start = self.main.index("function workflowAvailabilityCopy")
        availability_end = self.main.index("function createWorkflowSourceSelect", availability_start)
        availability = self.main[availability_start:availability_end]
        card_start = self.main.index("function createWorkflowActionCard")
        card_end = self.main.index("function renderWorkflowAutomationSummary", card_start)
        card = self.main[card_start:card_end]
        open_start = self.main.index("async function openPropDialog")
        open_end = self.main.index("function setConnectionActionState", open_start)
        open_dialog = self.main[open_start:open_end]

        self.assertIn("const hasAuthoritativeReadModel = Array.isArray(backend.actions)", normalize)
        self.assertIn("workflowReadModel,", normalize)
        self.assertIn("workflowReadModel.authoritative !== true", availability)
        self.assertIn('label: "กำลังตรวจสอบสถานะ..."', availability)
        self.assertIn('label: "โหลดสถานะไม่สำเร็จ"', availability)
        self.assertIn("ปิดและเปิดอุปกรณ์นี้ใหม่เพื่อลองอีกครั้ง", availability)
        self.assertIn("dashboard.workflowReadModel?.authoritative === true", card)
        self.assertIn("submit.disabled = !canSubmit || inFlight", card)
        self.assertLess(open_dialog.index("const reportRequest = loadPropReport(propId)"), open_dialog.index("openGameModal("))
        self.assertIn("await reportRequest", open_dialog)
        self.assertIn("state.modal.id === propId", open_dialog)

    def test_workflow_submit_has_opaque_retry_safe_idempotency(self):
        self.assertIn("function createWorkflowIdempotencyKey", self.main)
        self.assertIn("globalThis.crypto?.randomUUID?.()", self.main)
        self.assertIn("function workflowActionFormSignature", self.main)
        self.assertIn('previousAction.tone === "error"', self.main)
        self.assertIn("previousAction.formSignature === formSignature", self.main)
        self.assertIn("idempotencyKey,", self.main)
        request = re.search(
            r"postJson\(`/api/props/\$\{encodeURIComponent\(propId\)\}/workflow/actions`,\s*\{(?P<body>.*?)\}\);",
            self.main,
            re.S,
        )
        self.assertIsNotNone(request)
        self.assertNotRegex(request.group("body"), re.compile(r"\b(?:token|password|secret|cookie)\b", re.I))

    def test_workflow_source_selection_and_clickable_result_details_are_wired(self):
        self.assertIn('id: "sourceReportId"', self.main)
        self.assertIn("createWorkflowSourceSelect", self.main)
        self.assertIn("backend.agentDeliveredSources", self.main)
        self.assertNotIn("backend.upstreamSources", self.main)
        self.assertIn("dashboard.agentDeliveredSources", self.main)
        self.assertNotIn("dashboard.upstreamSources", self.main)
        self.assertIn("Report ที่ Agent ส่งเข้ามาผ่าน Mission", self.main)
        self.assertIn("openDashboardResultDetail(source, card)", self.main)
        self.assertIn("findWorkflowCurrentPropReportProjection", self.main)
        self.assertIn("renderDashboardWorkColumn(els.workflowRunningList", self.main)
        self.assertIn("renderDashboardWorkColumn(els.workflowCompletedList", self.main)
        self.assertIn("renderDashboardWorkColumn(els.workflowBlockedList", self.main)

    def test_report_handoff_is_explicit_agent_mission_flow_without_direct_navigation(self):
        left_rail_start = self.index.index('id="modalPortraitPanel"')
        left_rail_end = self.index.index('<div class="modal-content-panel">', left_rail_start)
        left_rail = self.index[left_rail_start:left_rail_end]
        self.assertIn("Backend จะบันทึก Mission และเส้นทางของ Report ก่อนส่งต่อ", left_rail)
        self.assertIn("ให้ Agent ส่งต่อ Report", left_rail)
        handoff_start = self.main.index("async function submitWorkflowAgentHandoff")
        handoff_end = self.main.index("function renderWorkflowDashboard", handoff_start)
        handoff = self.main[handoff_start:handoff_end]
        self.assertRegex(
            handoff,
            re.compile(
                r"postJson\(`/api/props/\$\{encodeURIComponent\(targetPropId\)\}/workflow/transfers`,\s*\{\s*actionId,\s*sourceReportId:\s*reportId,\s*idempotencyKey,?\s*\}\)",
                re.S,
            ),
        )
        self.assertNotIn("assignTask(", handoff)
        self.assertIn('result?.kind !== "agent_report_transfer_recorded"', handoff)
        self.assertIn("mergeBackendMission(mission)", handoff)
        self.assertIn("loadPropReport(subject.id)", handoff)
        self.assertIn("loadPropReport(targetPropId)", handoff)
        self.assertIn("routeAgentToTargetId(transferAgentId, targetPropId", handoff)
        self.assertIn("ยังไม่ได้เริ่มงานปลายทาง", handoff)
        self.assertNotIn("openPropDialog", handoff)
        self.assertNotIn("openGameModal", handoff)

    def test_agent_handoff_and_settings_are_context_aware(self):
        settings_start = self.main.index("function renderWorkflowSettingsRail")
        settings_end = self.main.index("function getWorkflowHandoffReports", settings_start)
        settings = self.main[settings_start:settings_end]
        handoff_start = self.main.index("function renderWorkflowAgentHandoff")
        handoff_end = self.main.index("function workflowHandoffErrorMessage", handoff_start)
        handoff = self.main[handoff_start:handoff_end]

        self.assertIn("function workflowRailActions", self.main)
        self.assertIn("WORKFLOW_DASHBOARD_SETTING_ACTION_IDS.has(left.id)", self.main)
        self.assertIn("els.workflowSettingsRail.hidden = false", settings)
        self.assertIn("createWorkflowUseGuideCard(subject)", settings)
        self.assertIn("els.workflowSettingsRailContent.innerHTML = \"\"", settings)
        self.assertIn("els.workflowAgentHandoffRail.hidden = !selectedRoute", handoff)
        self.assertIn("getWorkflowReportTransferRoutes(subject.id, selectedReport)", handoff)
        self.assertIn("els.workflowHandoffButton.disabled = !selectedRoute", handoff)

    def test_main_tab_is_friendly_and_reports_only_render_on_the_last_tab(self):
        overview_start = self.main.index("function renderWorkflowPrimaryOverview")
        overview_end = self.main.index("function findWorkflowCurrentPropReportProjection", overview_start)
        overview = self.main[overview_start:overview_end]
        render_start = self.main.index("function renderWorkflowDashboard")
        render_end = self.main.index("function setWorkflowDashboardTab", render_start)
        render = self.main[render_start:render_end]

        self.assertIn("const isPrimaryTab = selectedTab?.id === dashboard.tabs[0]?.id", render)
        self.assertIn("const isHistoryTab = WORKFLOW_DASHBOARD_HISTORY_TAB_IDS.has(selectedTab?.id)", render)
        self.assertIn("els.workflowResultsPanel.hidden = !isHistoryTab", render)
        self.assertIn('els.workflowResultsTitle.textContent = "ประวัติและรายงาน"', render)
        self.assertIn("if (!isPrimaryTab && !isHistoryTab)", render)
        self.assertIn('note.className = "workflow-empty-message"', render)
        self.assertIn(
            '"ยังไม่มีข้อมูลในส่วนนี้ เมื่อ Local Runner ส่งผลกลับมาระบบจะแสดงที่นี่"',
            render,
        )
        self.assertLess(
            render.index("renderWorkflowDomainPanel("),
            render.index("renderWorkflowPrimaryOverview("),
        )
        self.assertLess(
            render.index("renderWorkflowPrimaryOverview("),
            render.index("if (actions.length)"),
        )
        self.assertIn('copy.textContent = "ยังไม่มีผลล่าสุดจาก Local Runner"', overview)
        self.assertIn("const primaryAction = actions[0] || null", overview)
        self.assertEqual(overview.count('className = "modal-action primary workflow-primary-empty-cta"'), 1)
        self.assertIn("findWorkflowCurrentPropReportProjection", overview)

    def test_report_handoff_allow_list_is_fail_closed_and_matches_backend_routes(self):
        route_start = self.main.index("const WORKFLOW_REPORT_TRANSFER_ROUTES")
        route_end = self.main.index("\n]);", route_start)
        route_block = self.main[route_start:route_end]
        for action_id in (
            "deep_research_system",
            "build_strategy_code",
            "review_source_code",
            "prepare_backtest_plan",
            "prepare_optimization_plan",
            "prepare_ea_discovery_plan",
            "build_fx_pair_bias",
            "inspect_ea_source",
            "develop_ea_source",
            "propose_ea_performance_improvements",
        ):
            self.assertIn(f'actionId: "{action_id}"', route_block)
        self.assertIn("WORKFLOW_REPORT_TRANSFER_READY_STATUSES", self.main)
        self.assertIn("getWorkflowReportTransferRoutes", self.main)
        self.assertIn("Report นี้ไม่มีเส้นทางปลายทางที่ Backend อนุญาต", self.main)
        self.assertIn("workflowHandoffFormSignature", self.main)
        self.assertIn('previousHandoff.tone === "error"', self.main)

    def test_backend_field_aliases_are_supported(self):
        self.assertIn('source_report: "source"', self.main)
        self.assertIn('boolean: "checkbox"', self.main)
        self.assertIn('time_list: "list"', self.main)
        self.assertIn('integer: "number"', self.main)
        self.assertIn('"settings_only"', self.main)

    def test_task_routing_matches_the_new_equipment_roles(self):
        expected_routes = (
            'taskKeywords.deepResearch)) return "left_server_racks"',
            'taskKeywords.eaDiscovery)) return "right_tool_console"',
            'taskKeywords.backtest)) return "right_tool_console"',
            'taskKeywords.optimization)) return "right_tool_console"',
            'taskKeywords.globalDiscovery)) return "codex_mcp_portal"',
            'taskKeywords.eaBuild)) return "right_server_racks"',
        )
        for route in expected_routes:
            self.assertIn(route, self.main)

    def test_workspace_has_responsive_no_overlap_layout_and_accessible_tabs(self):
        self.assertIn(".workflow-dashboard-workspace", self.styles)
        self.assertIn(".workflow-settings-rail", self.styles)
        self.assertIn(".workflow-settings-rail[hidden]", self.styles)
        self.assertIn(".workflow-agent-handoff", self.styles)
        self.assertIn(".workflow-agent-handoff[hidden]", self.styles)
        self.assertIn(".workflow-results[hidden]", self.styles)
        self.assertIn(".workflow-primary-overview", self.styles)
        self.assertIn(".workflow-primary-empty", self.styles)
        self.assertIn(".workflow-command-deck", self.styles)
        self.assertIn(".workflow-dashboard-scroll", self.styles)
        self.assertIn("overflow-y: auto", self.styles)
        self.assertIn("@media (max-width: 900px)", self.styles)
        self.assertIn(".workflow-result-columns", self.styles)
        self.assertIn('role="tablist"', self.index)
        self.assertIn('aria-live="polite"', self.index)
        self.assertIn('setAttribute("aria-selected", active ? "true" : "false")', self.main)
        self.assertIn('event.key === "ArrowRight"', self.main)

    def test_custom_plugin_profile_and_automatic_schedule_truth_are_visible(self):
        self.assertIn("rawPluginProfile", self.main)
        self.assertIn('pluginSkillId: safeDashboardDisplayText', self.main)
        self.assertIn('automationMode', self.main)
        self.assertIn('className = "workflow-plugin-profile"', self.main)
        self.assertIn('className = "workflow-automation-summary"', self.main)
        self.assertIn("renderWorkflowAutomationSummary", self.main)
        self.assertIn("schedule?.automaticRunsImplemented === true", self.main)
        self.assertIn("schedule.requestedEnabled ?? schedule.enabled", self.main)
        self.assertIn("schedule.nextRunAt", self.main)
        self.assertIn("schedule.lastRunAt", self.main)
        self.assertIn(".workflow-plugin-profile", self.styles)
        self.assertIn(".workflow-automation-summary", self.styles)

    def test_custom_plugin_wording_does_not_claim_direct_dispatch(self):
        self.assertIn("function workflowProcedurePresentation", self.main)
        self.assertIn('title: "Codex ใช้ขั้นตอนจาก Custom Plugin"', self.main)
        self.assertIn('"ขั้นตอน Backend ที่ปรับจาก Custom Plugin"', self.main)
        self.assertIn('"ขั้นตอน Backend"', self.main)
        self.assertIn("Backend นำความต้องการจาก Custom Plugin มาทำเป็นขั้นตอนคลิกเดียว", self.main)
        self.assertIn("ไม่ใช่การเรียก Plugin โดยตรงจากหน้าเว็บ", self.main)
        self.assertIn("ยังไม่พบ Custom Plugin นี้ใน Codex ของผู้ใช้", self.main)
        self.assertIn("Version ไม่ตรงกัน", self.main)
        self.assertIn("Workflow ต้องการ", self.main)
        self.assertNotIn(" / Plugin → Local Runner", self.main)

    def test_platform_selection_updates_the_visible_backend_and_reference_profile(self):
        self.assertIn("function workflowPluginProfileForSelection", self.main)
        self.assertIn("pluginSelectionField", self.main)
        self.assertIn("pluginCandidates", self.main)
        self.assertIn("renderSelectedPluginProfile", self.main)
        self.assertIn("workflowPluginProfileForSelection(action.pluginProfile, selectionControl.value)", self.main)
        self.assertIn('platformControl.dispatchEvent(new Event("change"))', self.main)

    def test_plugin_profile_never_expands_frontend_execution_authority(self):
        action_start = self.main.index("function createWorkflowActionCard")
        action_end = self.main.index("function renderWorkflowAutomationSummary", action_start)
        action_block = self.main[action_start:action_end]
        self.assertNotIn("fetch(", action_block)
        self.assertNotIn("WebSocket", action_block)
        self.assertNotIn("localStorage.setItem", action_block)
        self.assertNotIn('type = "password"', action_block)
        self.assertIn("action.pluginProfile", action_block)

    def test_plugin_flow_labels_do_not_reference_an_out_of_scope_agent_name(self):
        self.assertNotIn(
            'displayAgentName(action.ownerAgentId || "manager", agentName)',
            self.main,
        )
        self.assertNotIn(
            'displayAgentName(primaryAction.ownerAgentId || "manager", agentName)',
            self.main,
        )
        self.assertIn(
            'displayAgentName(action.ownerAgentId || "manager", "Agent ผู้รับงาน")',
            self.main,
        )


if __name__ == "__main__":
    unittest.main()
