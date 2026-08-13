from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DashboardEquipmentFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main = (ROOT / "frontend" / "src" / "app" / "main.js").read_text(encoding="utf-8")
        cls.styles = (ROOT / "frontend" / "src" / "app" / "styles.css").read_text(encoding="utf-8")

    def fallback_prop_block(self, prop_id: str, next_prop_id: str | None = None) -> str:
        start = self.main.index(f"  {prop_id}: {{", self.main.index("const WORKFLOW_DASHBOARD_FALLBACKS"))
        if next_prop_id:
            end = self.main.index(f"  {next_prop_id}: {{", start)
        else:
            end = self.main.index("\n});", start)
        return self.main[start:end]

    def test_boot_contract_urls_resolve_from_bridge_root_not_frontend_directory(self):
        self.assertIn('const ROOM_CONTRACT_PATH = "/contracts/rooms/command-room.json?v=32";', self.main)
        self.assertIn('const AGENT_CONTRACT_PATH = "/contracts/agents/agents.json?v=10";', self.main)
        self.assertNotIn('"./contracts/rooms/command-room.json', self.main)
        self.assertNotIn('"./contracts/agents/agents.json', self.main)

    def test_heavy_local_assets_and_prop_reports_have_explicit_startup_timeouts(self):
        self.assertIn("const BOOT_CONTRACT_FETCH_TIMEOUT_MS = 20000;", self.main)
        self.assertIn("const UI_SESSION_FETCH_TIMEOUT_MS = 5000;", self.main)
        self.assertIn("const PROP_REPORT_FETCH_TIMEOUT_MS = 20000;", self.main)
        self.assertIn("const NAVIGATION_MASK_LOAD_TIMEOUT_MS = 20000;", self.main)
        self.assertIn("{ timeoutMs: UI_SESSION_FETCH_TIMEOUT_MS }", self.main)
        self.assertIn("{ timeoutMs: PROP_REPORT_FETCH_TIMEOUT_MS, signal }", self.main)
        self.assertIn("}, NAVIGATION_MASK_LOAD_TIMEOUT_MS);", self.main)
        self.assertEqual(
            self.main.count("{ timeoutMs: BOOT_CONTRACT_FETCH_TIMEOUT_MS }"),
            2,
        )
        self.assertNotIn("reportBootResourceFailure(UI_SESSION_ENDPOINT", self.main)
        self.assertIn("UI session unavailable; using the local session snapshot.", self.main)

    def test_four_new_devices_have_exact_canonical_tabs(self):
        expected = {
            "left_audit_crystals": ["discoveries", "evidence", "schedule", "archive"],
            "left_signal_cube": ["today", "pair_bias", "horizons", "schedule_history"],
            "terminal_workstation": ["source", "development_brief", "performance_goals", "outputs"],
            "right_status_crystals": ["vps", "hq_bridge", "agent_settings", "activity_history"],
        }
        prop_ids = list(expected)
        for index, prop_id in enumerate(prop_ids):
            block = self.fallback_prop_block(prop_id, prop_ids[index + 1] if index + 1 < len(prop_ids) else None)
            tabs = block[block.index("tabs: ["):block.index("\n    actions:")]
            self.assertEqual(re.findall(r'\bid:\s*"([^"]+)"', tabs), expected[prop_id])

    def test_canonical_action_ids_are_wired(self):
        for action_id in (
            "discover_new_indicators",
            "save_indicator_scout_schedule",
            "analyze_daily_market_news",
            "build_fx_pair_bias",
            "save_news_bias_schedule",
            "inspect_ea_source",
            "develop_ea_source",
            "propose_ea_performance_improvements",
            "refresh_vps_hq_status",
            "save_agent_preferences",
        ):
            self.assertIn(f'id: "{action_id}"', self.main)

    def test_fx_bias_uses_exact_28_pair_universe_without_mock_values(self):
        start = self.main.index("const FX_BIAS_PAIR_UNIVERSE")
        end = self.main.index("\n]);", start)
        pairs = re.findall(r'"([A-Z]{6})"', self.main[start:end])
        self.assertEqual(len(pairs), 28)
        self.assertEqual(len(set(pairs)), 28)
        self.assertEqual(
            pairs,
            "AUDCAD AUDCHF AUDJPY AUDNZD AUDUSD CADCHF CADJPY CHFJPY EURAUD EURCAD EURCHF EURGBP EURJPY EURNZD EURUSD GBPAUD GBPCAD GBPCHF GBPJPY GBPNZD GBPUSD NZDCAD NZDCHF NZDJPY NZDUSD USDCAD USDCHF USDJPY".split(),
        )
        self.assertIn('short: "unavailable"', self.main)
        self.assertIn('medium: "unavailable"', self.main)
        self.assertIn('long: "unavailable"', self.main)
        self.assertIn('summary: "รอข้อมูลจริงจาก Backend"', self.main)
        normalizer_start = self.main.index("function normalizeFxNewsBiasDomain", start)
        normalizer_end = self.main.index("function normalizeVpsHqDomain", normalizer_start)
        self.assertNotIn("Math.random()", self.main[normalizer_start:normalizer_end])

    def test_fx_bias_consumes_current_backend_read_model_and_shared_sources(self):
        start = self.main.index("function normalizeFxNewsBiasDomain")
        end = self.main.index("function normalizeVpsHqDomain", start)
        block = self.main[start:end]
        self.assertIn("backend.fxBias", block)
        self.assertIn("item?.shortBias", block)
        self.assertIn("item?.mediumBias", block)
        self.assertIn("item?.longBias", block)
        self.assertIn("deriveFxOverallBias", block)
        self.assertIn("workflowItemSourceUrl(item, sharedSourceLinks)", block)
        source_helper = self.main[
            self.main.index("function workflowSourceLinkRows"):start
        ]
        self.assertIn("item.sourceLinks", source_helper)
        self.assertIn("item.sourceRefs", source_helper)
        self.assertIn("link.sourceId", source_helper)

    def test_indicator_scout_projects_direct_output_contract_fields(self):
        start = self.main.index("function normalizeIndicatorScoutDomain")
        end = self.main.index("function normalizeFxBiasValue", start)
        block = self.main[start:end]
        for field in (
            "indicatorName",
            "sourceUrl",
            "publishedAt",
            "checkedAt",
            "featureSummary",
            "availability",
            "limitations",
            "duplicateFingerprint",
            "platform",
            "category",
        ):
            self.assertIn(field, block)
        self.assertIn("ตรวจ Fingerprint แล้ว", block)

    def test_structured_report_metrics_are_bounded_and_human_readable(self):
        formatter = self.main[
            self.main.index("function formatDashboardValue"):
            self.main.index("function safeDashboardDisplayText")
        ]
        self.assertNotIn('value.join(", ")', formatter)
        self.assertIn("formatDashboardValue(item, depth + 1)", formatter)
        self.assertIn("dashboardFieldLabel(name)", formatter)
        renderer = self.main[
            self.main.index("const DASHBOARD_STRUCTURED_VALUE_LIMITS"):
            self.main.index("function getSafeReportImageUrl")
        ]
        self.assertIn("maxDepth: 3", renderer)
        self.assertIn("maxArrayItems: 20", renderer)
        self.assertIn("maxObjectFields: 20", renderer)
        self.assertIn("maxNodesPerMetricSection: 360", renderer)
        self.assertIn('document.createElement("details")', renderer)
        self.assertIn("appendDashboardStructuredValue", renderer)
        self.assertIn("แสดงบางส่วน", renderer)

    def test_verified_reports_are_grouped_as_completed(self):
        start = self.main.index("function getDashboardWorkState")
        end = self.main.index("function getDashboardItemTime", start)
        block = self.main[start:end]
        self.assertIn('"verified"', block)
        self.assertIn('return "completed"', block)

    def test_portal_schedule_copy_excludes_ea_discovery(self):
        self.assertIn('labelTh: "ตั้งเวลาค้นหาระบบเทรดรายวัน"', self.main)
        self.assertIn("งานค้นหา EA เป็น Mission แยก", self.main)
        self.assertIn('labelTh: "เวลาค้นหาระบบเทรด"', self.main)
        self.assertIn("ตารางเวลานี้ใช้กับการค้นหาระบบเทรดเท่านั้น", self.main)

    def test_indicator_scout_shows_source_date_dedup_and_truthful_adapter(self):
        self.assertIn("sourceUrl", self.main)
        self.assertIn("discoveredAt", self.main)
        self.assertIn("dedupStatus", self.main)
        self.assertIn('status: "coming_soon"', self.main)
        self.assertIn('labelTh: "Screenshot Adapter: Coming Soon"', self.main)
        self.assertIn("ไม่มีภาพจำลอง", self.main)

    def test_radar_website_tool_keeps_canonical_tabs_but_presents_only_today_and_seven_days(self):
        fallback = self.fallback_prop_block("left_audit_crystals", "left_signal_cube")
        tabs = fallback[fallback.index("tabs: ["):fallback.index("\n    actions:")]
        self.assertEqual(
            re.findall(r'\bid:\s*"([^"]+)"', tabs),
            ["discoveries", "evidence", "schedule", "archive"],
        )
        self.assertIn('left_audit_crystals: "Radar Website Tool"', self.main)
        self.assertIn('labelTh: "RADAR WEBSITE TOOL"', self.main)
        normalization = self.main[
            self.main.index("const tabs = visibleTabs.map"):
            self.main.index("const deliveredSourceRows", self.main.index("const tabs = visibleTabs.map"))
        ]
        self.assertIn("INDICATOR_SCOUT_PRESENTATION_TAB_IDS", normalization)
        self.assertIn('tab.id === "discoveries" ? "วันนี้" : "ย้อนหลัง 7 วัน"', normalization)

    def test_radar_actions_live_only_in_left_settings_rail(self):
        rail = self.main[
            self.main.index("function workflowRailActions"):
            self.main.index("function getWorkflowHandoffReports", self.main.index("function workflowRailActions"))
        ]
        dashboard = self.main[
            self.main.index("function renderWorkflowDashboard("):
            self.main.index("function setWorkflowDashboardTab", self.main.index("function renderWorkflowDashboard("))
        ]
        self.assertIn("INDICATOR_SCOUT_RAIL_ACTION_IDS", rail)
        self.assertIn('"discover_new_indicators"', self.main)
        self.assertIn('"save_indicator_scout_schedule"', self.main)
        self.assertIn("centralActionIds", dashboard)
        self.assertIn("!centralActionIds.has(action.id)", dashboard)
        self.assertIn("usesDomainHistory", dashboard)

    def test_radar_left_rail_shows_masked_sheet_and_hard_daily_cap_truth(self):
        rail = self.main[
            self.main.index("function createRadarRailTruthCard"):
            self.main.index("function getWorkflowHandoffReports", self.main.index("function createRadarRailTruthCard"))
        ]
        self.assertIn("sheetReferenceMasked", rail)
        self.assertIn("runsReservedToday", rail)
        self.assertIn("remainingRunsToday", rail)
        self.assertIn("ยังไม่เชื่อม Adapter", rail)
        self.assertNotIn("sheetId", rail)
        self.assertIn('field.id === "googleSheetUrlOrId"', self.main)
        self.assertIn("googleSheetTabName: radarSheet?.tabName", self.main)
        self.assertIn(".workflow-radar-rail-truth", self.styles)

    def test_radar_normalizes_contract_entries_categories_and_safe_report_images(self):
        start = self.main.index("function normalizeIndicatorScoutDomain")
        end = self.main.index("function normalizeFxBiasValue", start)
        block = self.main[start:end]
        for field in (
            "root.entries",
            "metrics.entries",
            "toolName",
            "toolKind",
            "sourceTitle",
            "checkedAt",
            "duplicateStatus",
            "verificationStatus",
            "screenshot",
        ):
            self.assertIn(field, block)
        self.assertIn('indicator: "Indicator", ea: "EA", tool: "Tool"', self.main)
        screenshot_helper = self.main[
            self.main.index("function indicatorScoutSafeScreenshotUrl"):
            self.main.index("function indicatorScoutTimestamp")
        ]
        self.assertIn("getSafeReportImageUrl", screenshot_helper)
        self.assertIn("screenshot.available === true", screenshot_helper)
        self.assertIn("/api/reports/${reportId}/attachments/${attachmentId}", screenshot_helper)
        self.assertNotIn("http://", screenshot_helper)
        image_guard = self.main[
            self.main.index("function getSafeReportImageUrl"):
            self.main.index("function getSafeReportArtifactUrl")
        ]
        self.assertIn("parsed.origin !== window.location.origin", image_guard)
        self.assertIn("parsed.username || parsed.password", image_guard)
        self.assertIn("parsed.search || parsed.hash", image_guard)

    def test_radar_filters_by_bangkok_today_and_rolling_seven_days(self):
        date_helpers = self.main[
            self.main.index("function indicatorScoutBangkokDateKey"):
            self.main.index("function normalizeIndicatorScoutDomain")
        ]
        self.assertIn('timeZone: "Asia/Bangkok"', date_helpers)
        self.assertIn("formatToParts", date_helpers)
        self.assertIn("7 * 24 * 60 * 60 * 1000", date_helpers)
        renderer = self.main[
            self.main.index("function renderIndicatorScoutPanel"):
            self.main.index("function renderFxBiasTable", self.main.index("function renderIndicatorScoutPanel"))
        ]
        self.assertIn("filterIndicatorScoutToday", renderer)
        self.assertIn("filterIndicatorScoutRollingSevenDays", renderer)
        self.assertIn("domain?.todayEntries", renderer)
        self.assertIn("domain?.sevenDayEntries", renderer)
        self.assertIn("same-origin Report attachment", renderer)

        normalizer = self.main[
            self.main.index("function normalizeIndicatorScoutDomain"):
            self.main.index("function normalizeFxBiasValue")
        ]
        self.assertIn("backend.radarWebsiteTool", normalizer)
        self.assertIn("const hasCanonicalTruth", normalizer)
        self.assertIn("projectCanonicalRows(canonicalTodayRows)", normalizer)
        self.assertIn("projectCanonicalRows(canonicalSevenDayRows)", normalizer)
        self.assertIn("filterIndicatorScoutToday(discoveries)", normalizer)
        self.assertIn("filterIndicatorScoutRollingSevenDays(discoveries)", normalizer)
        self.assertIn("todayEntries,", normalizer)
        self.assertIn("sevenDayEntries,", normalizer)
        self.assertIn("if (!hasCanonicalTruth) reports.forEach", normalizer)
        self.assertIn('`${reportId}\\u001f${recordId}\\u001f${checkedAt}`', normalizer)

    def test_radar_cards_are_responsive_and_have_honest_image_source_detail_states(self):
        for selector in (
            ".workflow-radar-website-tool",
            ".workflow-radar-card-media",
            ".workflow-radar-card-actions",
            ".workflow-radar-history-day",
            '.workflow-settings-rail[data-dashboard-identity="indicator-scout"]',
        ):
            self.assertIn(selector, self.styles)
        self.assertIn("aspect-ratio: 16 / 8", self.styles)
        self.assertIn("object-fit: cover", self.styles)
        self.assertIn("grid-template-columns: minmax(0, 1fr)", self.styles)
        self.assertIn("ยังไม่มี URL ที่ผ่านการตรวจ", self.main)
        self.assertIn("ดูรายละเอียด", self.main)

    def test_web_speech_dictation_handles_unsupported_and_permission_states(self):
        self.assertIn("window.SpeechRecognition || window.webkitSpeechRecognition", self.main)
        self.assertIn('recognition.lang = "th-TH"', self.main)
        self.assertIn("เบราว์เซอร์นี้ไม่รองรับการพิมพ์ด้วยเสียง", self.main)
        self.assertIn('"not-allowed", "service-not-allowed"', self.main)
        self.assertIn("ไมโครโฟนยังไม่ได้รับอนุญาต", self.main)
        self.assertIn("stopWorkflowVoiceDictation", self.main)
        self.assertIn("voiceDictation: field?.voiceDictation === true", self.main)

    def test_safe_artifact_download_is_backend_gated_and_same_origin(self):
        start = self.main.index("function getSafeReportArtifactUrl")
        end = self.main.index("function appendDashboardVisualEvidence", start)
        block = self.main[start:end]
        self.assertIn("parsed.origin !== window.location.origin", block)
        self.assertIn("(?:attachments|artifacts|downloads)", block)
        self.assertIn("item.available !== true", block)
        self.assertIn("kind:", block)
        self.assertIn("fileName:", block)
        self.assertIn("item.mediaType", block)
        self.assertIn("contentType:", block)
        self.assertIn("ยังไม่มีไฟล์ที่ Backend อนุญาตให้ดาวน์โหลด", self.main)
        self.assertNotIn("file://", block)

    def test_external_evidence_urls_block_private_hosts_credentials_and_sensitive_queries(self):
        start = self.main.index("const EXTERNAL_URL_BLOCKED_HOST_SUFFIXES")
        end = self.main.index("function workflowDomainObject", start)
        block = self.main[start:end]
        self.assertIn('[".localhost", ".local", ".internal"]', block)
        self.assertIn("parsed.username || parsed.password", block)
        self.assertIn("isBlockedExternalIpv4Literal", block)
        self.assertIn("first === 10", block)
        self.assertIn("first === 127", block)
        self.assertIn("first === 172 && second >= 16 && second <= 31", block)
        self.assertIn("first === 192 && second === 168", block)
        self.assertIn("isBlockedExternalIpv6Literal", block)
        self.assertIn("(first & 0xfe00) === 0xfc00", block)
        self.assertIn("(first & 0xffc0) === 0xfe80", block)
        self.assertIn("groups[5] === 0xffff", block)
        self.assertIn("EXTERNAL_URL_SENSITIVE_QUERY_NAME_PATTERN", block)
        self.assertIn("hasSensitiveExternalQueryName(parsed.searchParams)", block)

    def test_all_generic_external_evidence_renderers_use_the_hardened_url_guard(self):
        renderers = (
            ("function appendDashboardSourceLinks", "function openDashboardResultDetail"),
            ("function appendSignalDeepEvidenceList", "function renderSignalNewsHorizonCard"),
            ("function appendTaskEvidenceSection", "function getMissionNextStep"),
        )
        for start_marker, end_marker in renderers:
            block = self.main[self.main.index(start_marker):self.main.index(end_marker, self.main.index(start_marker))]
            self.assertIn("getSafeExternalHttpUrl", block)
            self.assertNotIn('link.href = parsed.href', block)

    def test_ea_factory_outputs_tab_renders_verified_backend_downloads(self):
        output_start = self.main.index("function renderTerminalOutputPanel")
        output_end = self.main.index("function renderTerminalSourceCatalogPanel", output_start)
        output_block = self.main[output_start:output_end]
        self.assertIn('"ea_build_report"', output_block)
        self.assertIn("item.downloads", output_block)
        self.assertIn("appendDashboardArtifactLinks(section, artifacts)", output_block)

        router_start = self.main.index("function renderWorkflowDomainPanel")
        router_end = self.main.index("function renderWorkflowCatalog", router_start)
        router_block = self.main[router_start:router_end]
        self.assertIn('["terminal_workstation", "right_server_racks"].includes(subject.id)', router_block)
        self.assertIn('selectedTab.id === "outputs"', router_block)
        self.assertIn("renderTerminalOutputPanel(container, report)", router_block)

    def test_ea_source_uses_only_backend_catalog_without_file_or_path_input(self):
        self.assertIn("function normalizeWorkflowSourceCatalog", self.main)
        self.assertIn("backend.workspaceSources", self.main)
        self.assertIn('"workspaceSourceId"', self.main)
        self.assertIn('rawType === "workspace_source"', self.main)
        self.assertIn('field.sourceKind === "workspace_source"', self.main)
        self.assertIn('data-workflow-field="workspaceSourceId"', self.main)
        self.assertIn("validateWorkflowSourceChoice", self.main)
        self.assertIn("เลือกได้เพียงอย่างเดียว", self.main)
        self.assertIn("Approved Workspace Source Catalog", self.main)
        self.assertIn("นำ Source เข้า Workspace ผ่าน Backend ก่อน", self.main)
        self.assertIn("Direct Import จากหน้าเว็บ: Coming Soon", self.main)
        self.assertIn("หน้าเว็บไม่รับการวาง Path", self.main)
        self.assertNotIn('type: "file"', self.fallback_prop_block("terminal_workstation", "right_status_crystals"))

    def test_vps_and_hq_panels_only_render_backend_values(self):
        self.assertIn("function normalizeVpsHqDomain", self.main)
        self.assertIn("function renderVpsHqPanel", self.main)
        self.assertIn("ยังไม่มีค่าตรวจ VPS จริงจาก Backend", self.main)
        self.assertIn("ยังไม่มีสถานะ HQ/Bridge ที่ Backend เปิดเผย", self.main)
        self.assertIn("Uptime", self.main)
        self.assertIn("Latency", self.main)
        self.assertIn("CPU", self.main)
        self.assertIn("RAM", self.main)

    def test_agent_settings_match_backend_safe_preferences_and_bounds(self):
        block = self.fallback_prop_block("right_status_crystals")
        action_start = block.index('id: "save_agent_preferences"')
        fields_start = block.index("formFields: [", action_start)
        fields_end = block.index("\n        ],", fields_start)
        fields = block[fields_start:fields_end]
        ids = re.findall(r'\{\s*id:\s*"([^"]+)"[^\n]*type:', fields)
        self.assertEqual(ids, [
            "language",
            "modelTier",
            "tokenBudget",
            "timeoutSeconds",
            "outputLimitChars",
            "rateReservePercent",
        ])
        self.assertNotIn("agentId", fields)
        self.assertNotIn("responseStyle", fields)
        self.assertNotIn("notificationLevel", fields)
        self.assertNotIn('type: "password"', block)
        self.assertNotIn('type: "file"', block)
        self.assertIn("tokenBudget: { min: 256, max: 100000, step: 1 }", self.main)
        self.assertIn("timeoutSeconds: { min: 15, max: 600, step: 1 }", self.main)
        self.assertIn("outputLimitChars: { min: 1000, max: 20000, step: 1 }", self.main)
        self.assertIn("rateReservePercent: { min: 10, max: 80, step: 1 }", self.main)
        self.assertIn('field.integer ? Math.trunc(numeric) : numeric', self.main)

    def test_field_guard_allows_canonical_budget_and_tier_but_denies_privileged_ids(self):
        guard_line = next(line for line in self.main.splitlines() if line.startswith("const WORKFLOW_FIELD_DENY_PATTERN"))
        self.assertIn("token(?!budget)", guard_line)
        self.assertIn("model[_-]?id", guard_line)
        self.assertNotIn("|budget|model|", guard_line)
        self.assertIn("provider", guard_line)
        self.assertIn("tool", guard_line)

    def test_agent_equipment_targets_follow_repurposed_props(self):
        start = self.main.index("const officeAgentDefinitions")
        end = self.main.index("const meetingSeats", start)
        roster = self.main[start:end]

        def agent_block(agent_id: str, next_agent_id: str) -> str:
            agent_start = roster.index(f'id: "{agent_id}"')
            return roster[agent_start:roster.index(f'id: "{next_agent_id}"', agent_start)]

        vps = agent_block("vps_watch", "telegram_ops")
        telegram = agent_block("telegram_ops", "risk_guard")
        risk = agent_block("risk_guard", "codex_mcp_operator")
        codex = agent_block("codex_mcp_operator", "mission_archivist")
        archivist = roster[roster.index('id: "mission_archivist"'):]
        self.assertIn('tools: ["right_status_crystals"]', vps)
        self.assertNotIn("left_signal_cube", vps)
        self.assertNotIn("right_server_racks", vps)
        self.assertIn('defaultTarget: "mission_strategy_table"', telegram)
        self.assertIn('homeTarget: "mission_strategy_table"', telegram)
        self.assertIn('tools: ["mission_strategy_table"]', telegram)
        self.assertNotIn("right_tool_console", telegram)
        self.assertNotIn("right_status_crystals", telegram)
        self.assertNotIn("left_audit_crystals", telegram)
        self.assertIn('defaultTarget: "mission_strategy_table"', risk)
        self.assertIn('homeTarget: "mission_strategy_table"', risk)
        self.assertNotIn("left_audit_crystals", risk)
        self.assertIn("left_audit_crystals", codex)
        self.assertIn("left_signal_cube", codex)
        self.assertIn("left_audit_crystals", archivist)

    def test_task_routing_for_new_devices_precedes_legacy_routes(self):
        pick_target = self.main[self.main.index("function pickTargetForTask"):self.main.index("function pickAgentForTask")]
        positions = {
            name: pick_target.index(f"taskKeywords.{name}")
            for name in ("indicatorScout", "fxNewsBias", "eaDevelopment", "vpsAgentSettings")
        }
        legacy = min(pick_target.index("taskKeywords.risk"), pick_target.index("taskKeywords.autoTradeCouncil"))
        self.assertTrue(all(position < legacy for position in positions.values()))
        self.assertIn('return "left_audit_crystals"', pick_target)
        self.assertIn('return "left_signal_cube"', pick_target)
        self.assertIn('return "terminal_workstation"', pick_target)
        self.assertIn('return "right_status_crystals"', pick_target)
        self.assertIn('taskKeywords.autoTradingStatus)) return AI_TRADE_COUNCIL_PROP_ID', pick_target)
        self.assertIn('taskKeywords.risk)) return "mission_strategy_table"', pick_target)
        self.assertNotIn('taskKeywords.autoTradingStatus)) return "left_signal_cube"', pick_target)
        self.assertNotIn('taskKeywords.risk)) return "left_audit_crystals"', pick_target)
        self.assertIn('const AI_TRADE_COUNCIL_PROP_ID = "left_analytics_console"', self.main)
        self.assertIn('return "mission_strategy_table";', pick_target)

    def test_responsive_domain_layout_prevents_horizontal_page_overlap(self):
        for selector in (
            ".workflow-domain-panel",
            ".workflow-table-scroll",
            ".workflow-domain-table",
            ".workflow-indicator-grid",
            ".workflow-news-grid",
            ".workflow-vps-grid",
            ".workflow-voice-toolbar",
        ):
            self.assertIn(selector, self.styles)
        self.assertIn("overflow-x: auto", self.styles)
        self.assertIn("@media (max-width: 900px)", self.styles)
        self.assertIn("@media (max-width: 520px)", self.styles)
        self.assertIn("grid-template-columns: minmax(0, 1fr)", self.styles)


if __name__ == "__main__":
    unittest.main()
