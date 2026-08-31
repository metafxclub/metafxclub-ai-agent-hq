import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ResearchSheetHubFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        cls.main = (ROOT / "frontend" / "src" / "app" / "main.js").read_text(encoding="utf-8")
        cls.styles = (ROOT / "frontend" / "src" / "app" / "styles.css").read_text(encoding="utf-8")

    def block(self, start, end):
        start_index = self.main.index(start)
        return self.main[start_index:self.main.index(end, start_index)]

    def test_global_topbar_has_inspect_then_activate_controls(self):
        self.assertEqual(self.html.count('id="researchSheetHub"'), 1)
        self.assertEqual(self.html.count('id="researchSheetHubReference"'), 1)
        for element_id in (
            "researchSheetHubDetailsToggle",
            "researchSheetHubPopover",
            "researchSheetHubActive",
            "researchSheetHubLifecycle",
            "researchSheetHubLinkedSystems",
            "researchSheetHubInspection",
            "researchSheetHubInspectionTabs",
            "researchSheetHubActivate",
            "researchSheetHubCancel",
            "researchSheetHubProgress",
            "researchSheetHubConsumers",
            "researchSheetHubRetryFailed",
        ):
            self.assertIn(f'id="{element_id}"', self.html)
        self.assertIn("ตรวจสอบ Google Sheet", self.html)
        self.assertIn("ใช้ Google Sheet นี้", self.html)
        self.assertIn("GOOGLE SHEET STATUS", self.html)
        self.assertEqual(self.html.count('data-phase="inspecting"'), 1)
        self.assertEqual(self.html.count('data-phase="verifying"'), 1)
        self.assertEqual(self.html.count('data-phase="activating"'), 1)
        self.assertIn('for="researchSheetHubReference"', self.html)
        self.assertIn('aria-live="polite"', self.html)
        self.assertIn('aria-busy="false"', self.html)

    def test_google_oauth_is_one_time_backend_flow_without_frontend_secrets(self):
        for element_id in (
            "researchSheetGoogleAuth",
            "researchSheetGoogleAuthStatus",
            "researchSheetGoogleAuthTitle",
            "researchSheetGoogleAuthDetail",
            "researchSheetGoogleConnect",
            "researchSheetGoogleDisconnect",
        ):
            self.assertEqual(self.html.count(f'id="{element_id}"'), 1)
            self.assertEqual(
                self.main.count(f'document.getElementById("{element_id}")'),
                1,
            )
        self.assertIn("เชื่อมบัญชี Google ครั้งเดียว", self.html)
        auth_start = self.html.index('id="researchSheetGoogleAuth"')
        auth_end = self.html.index('id="researchSheetHubActive"', auth_start)
        auth_markup = self.html[auth_start:auth_end]
        self.assertNotRegex(auth_markup, r'<input[^>]+(?:token|secret|credential)')
        self.assertIn("ไม่รับ Token, Client Secret หรือ Credential", auth_markup)

    def test_google_oauth_uses_canonical_endpoints_and_safe_synchronous_popup(self):
        constants = self.block("const RESEARCH_SHEET_HUB_ENDPOINT", "const RESEARCH_SHEET_CONSUMERS")
        start = self.block("async function startResearchSheetGoogleAuth", "async function disconnectResearchSheetGoogleAuth")
        disconnect = self.block("async function disconnectResearchSheetGoogleAuth", "async function inspectResearchSheetHub")
        self.assertIn('${RESEARCH_SHEET_HUB_ENDPOINT}/auth', constants)
        self.assertIn('${RESEARCH_SHEET_GOOGLE_AUTH_ENDPOINT}/start', constants)
        self.assertIn('${RESEARCH_SHEET_GOOGLE_AUTH_ENDPOINT}/disconnect', constants)
        self.assertIn('window.open(\n    "about:blank"', start)
        self.assertLess(start.index("window.open("), start.index("await postJson("))
        self.assertIn("normalizeResearchSheetAuthorizationUrl", start)
        self.assertIn("accounts.google.com", self.main)
        self.assertIn("if (!popup.closed) popup.close()", start)
        self.assertIn("postJson(RESEARCH_SHEET_GOOGLE_AUTH_START_ENDPOINT, {})", start)
        self.assertIn("postJson(RESEARCH_SHEET_GOOGLE_AUTH_DISCONNECT_ENDPOINT, {})", disconnect)
        self.assertNotIn("token:", start.lower())
        self.assertNotIn("clientSecret", start)

    def test_google_oauth_poll_is_bounded_and_stops_on_success_error_and_unmount(self):
        polling = self.block("function stopResearchSheetGoogleAuthPolling", "async function startResearchSheetGoogleAuth")
        self.assertIn("RESEARCH_SHEET_GOOGLE_AUTH_POLL_TIMEOUT_MS = 120_000", self.main)
        self.assertIn("window.setTimeout", polling)
        self.assertIn("data?.connected === true", polling)
        self.assertIn('auth.status === "error"', polling)
        self.assertIn("researchSheetGoogleAuthIsTerminalStatus", polling)
        self.assertIn("stopResearchSheetGoogleAuthPolling({ closePopup: true })", polling)
        self.assertIn('window.addEventListener("pagehide"', self.main)
        pagehide_start = self.main.index('window.addEventListener("pagehide"')
        pagehide = self.main[pagehide_start:self.main.index("});", pagehide_start) + 3]
        self.assertIn("stopResearchSheetGoogleAuthPolling({ closePopup: true })", pagehide)

    def test_google_oauth_missing_backend_client_is_explicit_and_fail_closed(self):
        normalize = self.block("function normalizeResearchSheetGoogleAuth", "function normalizeResearchSheetAuthorizationUrl")
        presentation = self.block("function researchSheetGoogleAuthPresentation", "function renderResearchSheetGoogleAuth")
        render = self.block("function renderResearchSheetGoogleAuth", "function researchSheetHubSummaryPresentation")
        self.assertIn("requiresAdminSetup", normalize)
        self.assertIn("client_not_configured", normalize)
        self.assertIn("oauth_client_not_configured", normalize)
        self.assertIn("Backend ยังไม่ได้ตั้ง Google OAuth Client", presentation)
        self.assertIn("ไม่ต้องใส่ Token หรือ Client Secret ที่หน้านี้", presentation)
        self.assertIn("!presentation.startAvailable", render)
        self.assertIn("!googleAuth.connected", self.block("function renderResearchSheetHub()", "function refreshOpenResearchSheetConsumer"))
        self.assertNotIn('"configured", "ready"', normalize)

    def test_google_oauth_access_denied_explains_testing_audience(self):
        reason = self.block(
            "function researchSheetGoogleAuthFailureReason",
            "function researchSheetGoogleAuthIsTerminalStatus",
        )
        self.assertIn("Audience > Test users", reason)
        self.assertIn("กรณีแอปยังเป็น Testing", reason)

    def test_google_disconnect_keeps_sheet_id_and_normal_sheet_flow_stays_confirmed(self):
        disconnect = self.block("async function disconnectResearchSheetGoogleAuth", "async function inspectResearchSheetHub")
        inspect = self.block("async function inspectResearchSheetHub", "async function activateResearchSheetHub")
        activate = self.block("async function activateResearchSheetHub", "function normalizeOperatorModePayload")
        self.assertIn("Sheet ID จะยังอยู่", disconnect)
        self.assertNotIn('researchSheetHubReference.value = ""', disconnect)
        self.assertIn("postJson(RESEARCH_SHEET_HUB_INSPECT_ENDPOINT", inspect)
        self.assertIn("readyForConfirmation", inspect)
        self.assertIn("postJson(RESEARCH_SHEET_HUB_ACTIVATE_ENDPOINT", activate)
        self.assertIn("confirmActivate: true", activate)

    def test_hub_is_a_global_topbar_control_before_actions_not_inside_the_mission_modal(self):
        topbar_index = self.html.index('<header class="topbar">')
        brand_index = self.html.index('class="topbar-brand"', topbar_index)
        hub_index = self.html.index('id="researchSheetHub"', topbar_index)
        actions_index = self.html.index('class="topbar-actions"', topbar_index)
        topbar_close = self.html.index("</header>", actions_index)
        modal_index = self.html.index('id="gameModal"')
        self.assertLess(topbar_index, brand_index)
        self.assertLess(brand_index, hub_index)
        self.assertLess(hub_index, actions_index)
        self.assertLess(actions_index, topbar_close)
        self.assertLess(topbar_close, modal_index)

        hub_tag_start = self.html.rfind("<section", topbar_index, hub_index)
        hub_open_tag = self.html[hub_tag_start:self.html.index(">", hub_index) + 1]
        self.assertIn("topbar-research-sheet-hub", hub_open_tag)
        self.assertNotIn(" hidden", hub_open_tag)

        modal_controls_start = self.html.index('<div class="modal-controls-stack">')
        modal_panels_start = self.html.index('<div class="modal-tab-panel', modal_controls_start)
        modal_controls = self.html[modal_controls_start:modal_panels_start]
        self.assertNotIn('id="researchSheetHub"', modal_controls)
        self.assertNotIn('id="researchSheetHubForm"', modal_controls)

    def test_topbar_details_toggle_and_popover_are_unique_and_accessible(self):
        self.assertEqual(self.html.count('id="researchSheetHubDetailsToggle"'), 1)
        self.assertEqual(self.html.count('id="researchSheetHubPopover"'), 1)
        toggle_index = self.html.index('id="researchSheetHubDetailsToggle"')
        toggle_tag_start = self.html.rfind("<button", 0, toggle_index)
        toggle_tag = self.html[toggle_tag_start:self.html.index(">", toggle_index) + 1]
        self.assertIn('type="button"', toggle_tag)
        self.assertIn('aria-expanded="false"', toggle_tag)
        self.assertIn('aria-controls="researchSheetHubPopover"', toggle_tag)

        popover_index = self.html.index('id="researchSheetHubPopover"')
        popover_tag_start = self.html.rfind("<div", 0, popover_index)
        popover_tag = self.html[popover_tag_start:self.html.index(">", popover_index) + 1]
        self.assertIn("research-sheet-hub-popover", popover_tag)
        self.assertIn(" hidden", popover_tag)

        for element_id in ("researchSheetHubDetailsToggle", "researchSheetHubPopover"):
            self.assertEqual(
                self.main.count(f'document.getElementById("{element_id}")'),
                1,
            )

    def test_exact_three_tabs_and_four_linked_systems_are_fixed(self):
        consumers = self.block("const RESEARCH_SHEET_CONSUMERS", "const RESEARCH_SHEET_LINKED_SYSTEMS")
        linked = self.block("const RESEARCH_SHEET_LINKED_SYSTEMS", "const RESEARCH_SHEET_CONSUMER_PROP_IDS")
        self.assertEqual(
            re.findall(r'propId: "([a-z0-9_]+)"', consumers),
            ["codex_mcp_portal", "left_server_racks", "left_audit_crystals"],
        )
        self.assertEqual(
            re.findall(r'tabKey: "([A-Za-z0-9_]+)"', consumers),
            ["worldSystem", "deepResearch", "indicatorEaTool"],
        )
        self.assertEqual(
            re.findall(r'systemId: "([A-Za-z0-9_]+)"', linked),
            ["worldRadar", "deepResearch", "eaFactory", "radarWebsiteTool"],
        )
        self.assertIn('systemId: "eaFactory", propId: EA_FACTORY_PROP_ID, sourcePropId: "left_server_racks"', linked)
        self.assertNotIn("right_tool_console", consumers)
        self.assertNotIn("terminal_workstation", consumers)

    def test_get_inspect_and_activate_use_canonical_endpoints(self):
        constants = self.block("const RESEARCH_SHEET_HUB_ENDPOINT", "const RESEARCH_SHEET_HUB_MAX_AGE_MS")
        load = self.block("async function loadResearchSheetHub", "async function inspectResearchSheetHub")
        inspect = self.block("async function inspectResearchSheetHub", "async function activateResearchSheetHub")
        activate = self.block("async function activateResearchSheetHub", "function normalizeOperatorModePayload")
        self.assertIn('const RESEARCH_SHEET_HUB_ENDPOINT = "/api/props/mission_strategy_table/research-sheet";', constants)
        self.assertIn('${RESEARCH_SHEET_HUB_ENDPOINT}/inspect', constants)
        self.assertIn('${RESEARCH_SHEET_HUB_ENDPOINT}/activate', constants)
        self.assertIn('${RESEARCH_SHEET_HUB_ENDPOINT}/flush', constants)
        self.assertIn("fetchJson(RESEARCH_SHEET_HUB_ENDPOINT", load)
        self.assertIn("postJson(RESEARCH_SHEET_HUB_INSPECT_ENDPOINT", inspect)
        self.assertIn("googleSheetUrlOrId: sheetId", inspect)
        self.assertNotIn("postJson(RESEARCH_SHEET_HUB_ENDPOINT", inspect)
        self.assertIn("postJson(RESEARCH_SHEET_HUB_ACTIVATE_ENDPOINT", activate)
        self.assertIn("verificationToken: preview.verificationToken", activate)
        self.assertIn("confirmActivate: true", activate)
        self.assertIn("expectedConfigRevision: preview.baseConfigRevision", activate)
        self.assertIn("idempotencyKey: createWorkflowIdempotencyKey()", activate)
        self.assertNotIn("googleSheetUrlOrId", activate)

    def test_inspection_is_non_mutating_and_preserves_active_sheet_on_failure(self):
        inspect = self.block("async function inspectResearchSheetHub", "async function activateResearchSheetHub")
        self.assertIn("hub.preview = normalizeResearchSheetInspection(payload)", inspect)
        self.assertIn("if (payload?.researchSheet) hub.data = normalizeResearchSheetHub(payload)", inspect)
        self.assertIn("Sheet ที่ใช้งานอยู่เดิมไม่ถูกเปลี่ยน", inspect)
        self.assertIn("ค่าที่ใช้งานอยู่เดิมไม่ถูกเปลี่ยน", inspect)
        self.assertNotIn("hub.data = null", inspect)
        self.assertNotIn('input.value = ""', inspect)
        self.assertNotIn("hub.submittedReference = sheetId", inspect)

    def test_preview_requires_real_three_tab_evidence_before_confirmation(self):
        normalize = self.block("function normalizeResearchSheetInspection", "function researchSheetHubConfiguredReference")
        render = self.block("function renderResearchSheetHubInspection", "function researchSheetHubSummaryPresentation")
        header_normalizer = self.block("function normalizeResearchSheetHeaderList", "function normalizeResearchSheetHub")
        header_summary = self.block("function researchSheetHeaderIssueSummary", "function renderResearchSheetHubInspection")
        self.assertIn("verificationToken", normalize)
        self.assertIn("/^[A-Za-z0-9_-]{32,128}$/", normalize)
        self.assertIn("baseConfigRevision", normalize)
        self.assertIn("rowCount", normalize)
        self.assertIn("cachedRowCount", normalize)
        self.assertIn("observedAt", normalize)
        self.assertIn("probeEvidence", normalize)
        self.assertIn("missingHeaders: normalizeResearchSheetHeaderList(item?.missingHeaders)", normalize)
        self.assertIn("duplicateHeaders: normalizeResearchSheetHeaderList(item?.duplicateHeaders)", normalize)
        self.assertIn(".slice(0, 100)", header_normalizer)
        self.assertIn(".slice(0, 120)", header_normalizer)
        self.assertIn("consumer.readReady === true && consumer.probeEvidence.confirmed === true", normalize)
        self.assertIn("verifiedConsumerCount === consumers.length", normalize)
        self.assertIn("root.readyForConfirmation === true", normalize)
        self.assertIn("els.researchSheetHubActivate.hidden = !ready", render)
        self.assertIn("consumer.rowCount", render)
        self.assertIn("แท็บว่างใช้งานได้และพร้อมรับข้อมูลแรก", render)
        self.assertIn("researchSheetObservedLabel(consumer.observedAt)", render)
        self.assertIn("researchSheetHeaderIssueSummary(consumer)", render)
        self.assertIn('summarize("ขาด", consumer.missingHeaders)', header_summary)
        self.assertIn('summarize("ซ้ำ", consumer.duplicateHeaders)', header_summary)
        self.assertIn("หลักฐาน", render)

    def test_read_only_column_query_is_bounded_and_shows_backend_columns(self):
        for element_id in (
            "researchSheetHubQuery",
            "researchSheetHubQueryFields",
            "researchSheetHubQueryTab",
            "researchSheetHubQueryColumn",
            "researchSheetHubQueryContains",
            "researchSheetHubQueryLimit",
            "researchSheetHubQuerySubmit",
            "researchSheetHubQueryStatus",
            "researchSheetHubQueryResults",
        ):
            self.assertEqual(self.html.count(f'id="{element_id}"'), 1)
            self.assertEqual(
                self.main.count(f'document.getElementById("{element_id}")'),
                1,
            )
        query_markup_start = self.html.index('id="researchSheetHubQuery"')
        query_markup_end = self.html.index('id="researchSheetHubInspection"', query_markup_start)
        query_markup = self.html[query_markup_start:query_markup_end]
        for tab_name in ("World_System", "Deep_Research", "Indicator_EA_Tool"):
            self.assertIn(f'value="{tab_name}"', query_markup)
        self.assertIn('<option value="">ทุกแท็บ</option>', query_markup)
        self.assertIn('maxlength="120"', query_markup)
        self.assertIn('maxlength="200"', query_markup)
        self.assertIn('min="1" max="100"', query_markup)
        self.assertIn("ไม่รับ A1 Range", query_markup)

        constants = self.block("const RESEARCH_SHEET_HUB_ENDPOINT", "const RESEARCH_SHEET_CONSUMERS")
        normalize = self.block("function normalizeResearchSheetQueryResult", "function normalizeResearchSheetHub")
        can_run = self.block("function researchSheetHubQueryCanRun", "function researchSheetHubQueryIsBusy")
        render = self.block("function renderResearchSheetHubQuery", "function researchSheetHeaderIssueSummary")
        request = self.block("async function queryResearchSheetHub", "async function loadResearchSheetGoogleAuth")
        self.assertIn('${RESEARCH_SHEET_HUB_ENDPOINT}/query', constants)
        self.assertIn('new Set(["", "World_System", "Deep_Research", "Indicator_EA_Tool"])', constants)
        self.assertIn("rawMatches.slice(0, RESEARCH_SHEET_QUERY_MAX_MATCHES)", normalize)
        self.assertIn("normalizeResearchSheetQueryText(item?.value, 1_000)", normalize)
        self.assertIn("rawSearchedTabs.slice(0, RESEARCH_SHEET_CONSUMERS.length)", normalize)
        self.assertIn("normalizeResearchSheetHeaderList(item?.availableColumns)", normalize)
        self.assertIn("Array.isArray(root.availableColumns)", normalize)
        self.assertIn('data?.operational === true', can_run)
        self.assertIn('data?.readReady === true', can_run)
        self.assertIn("data.activeConfigRevision === data.configRevision", can_run)
        self.assertIn("postJson(RESEARCH_SHEET_HUB_QUERY_ENDPOINT, {", request)
        for field in ("tabName,", "columnName,", "contains,", "limit,"):
            self.assertIn(field, request)
        self.assertIn('errorResult.kind === "research_sheet_column_not_found"', request)
        self.assertIn("result.searchedTabs.forEach", render)
        self.assertIn("tab.availableColumns.forEach", render)
        self.assertIn("result.matches.forEach", render)
        self.assertIn("value.textContent = match.value", render)
        self.assertIn("els.researchSheetHubQueryResults.replaceChildren()", render)
        self.assertNotIn("innerHTML", render)
        self.assertIn(".research-sheet-hub-query-fields", self.styles)
        self.assertIn(".research-sheet-hub-query-match-list", self.styles)
        self.assertIn(".research-sheet-hub-query-columns", self.styles)

    def test_activation_is_fail_closed_and_keeps_the_id_visible(self):
        activate = self.block("async function activateResearchSheetHub", "function normalizeOperatorModePayload")
        self.assertIn("!preview?.readyForConfirmation", activate)
        self.assertIn("!preview.verificationToken", activate)
        self.assertIn("payload?.activation?.active !== true", activate)
        self.assertIn("activeData.active = payload.activation.active === true", activate)
        self.assertNotIn("const summary = researchSheetHubSummaryPresentation()", activate)
        self.assertIn("const activePresentation = researchSheetActivePresentation(activeData)", activate)
        self.assertIn('if (activePresentation.tone === "ready")', activate)
        self.assertIn('else if (activePresentation.tone === "warning")', activate)
        self.assertIn("เปิดใช้ Google Sheet สำเร็จ", activate)
        self.assertIn("activeData.consumers.every", activate)
        self.assertIn("ชีตยังไม่มีข้อมูลและพร้อมรับข้อมูลแรก", activate)
        self.assertIn("การเชื่อมต่อ Revision ปัจจุบันยังขัดข้อง", activate)
        self.assertIn("els.researchSheetHubReference.value = hub.submittedReference", activate)
        self.assertIn("hub.preview = null", activate)
        self.assertNotIn('els.researchSheetHubReference.value = ""', activate)

    def test_empty_active_sheet_is_presented_as_connected_without_claiming_write_proof(self):
        consumer = self.block(
            "function researchSheetConsumerPresentation",
            "function researchSheetHardError",
        )
        linked = self.block(
            "function renderResearchSheetHubLinkedSystems",
            "function resetResearchSheetHubQuery",
        )
        self.assertIn("activeReadConnection", consumer)
        self.assertIn("consumer.configurationApplied === true", consumer)
        self.assertIn("consumer.writeReady !== true", consumer)
        self.assertIn('label: empty ? "เชื่อมแล้ว • พร้อมรับข้อมูลแรก"', consumer)
        self.assertIn("ยังไม่มีหลักฐานเขียนและอ่านกลับ", consumer)
        self.assertIn("writeVerified: false", consumer)
        self.assertIn("verifiedReady: true", consumer)
        self.assertIn("ยังไม่มีข้อมูลและพร้อมรับข้อมูลแรก", linked)

    def test_outbox_pending_and_failure_presentations_are_truthful_and_isolated(self):
        normalize = self.block(
            "function normalizeResearchSheetOutbox",
            "function normalizeResearchSheetInspection",
        )
        counter = self.block(
            "function researchSheetOutboxCount",
            "function researchSheetConsumerPresentation",
        )
        consumer = self.block(
            "function researchSheetConsumerPresentation",
            "function researchSheetHardError",
        )
        active = self.block(
            "function researchSheetActivePresentation",
            "function researchSheetObservedLabel",
        )
        linked = self.block(
            "function renderResearchSheetHubLinkedSystems",
            "function resetResearchSheetHubQuery",
        )
        self.assertIn("outbox: normalizeResearchSheetOutbox(item?.outbox)", normalize)
        self.assertIn("outbox: normalizeResearchSheetOutbox(supplied.outbox)", normalize)
        self.assertIn("outbox: normalizeResearchSheetOutbox(supplied.outbox || source.outbox)", normalize)
        self.assertIn("deferred: boundedResearchSheetCount(source.deferred)", normalize)
        self.assertIn("Number(value?.outbox?.[name])", counter)
        self.assertIn("Number.isInteger(count) && count > 0", counter)

        consumer_failure_start = consumer.index("if (failedOutboxCount > 0)")
        consumer_failure_end = consumer.index("if (waitingOutboxCount > 0 && activeReadConnection)", consumer_failure_start)
        consumer_failure = consumer[consumer_failure_start:consumer_failure_end]
        self.assertIn('tone: "error"', consumer_failure)
        self.assertIn("ซิงก์ Sheet ไม่สำเร็จ", consumer_failure)
        self.assertIn("verifiedReady: false", consumer_failure)
        self.assertIn('researchSheetOutboxCount(consumer, "failed")', consumer)
        self.assertIn('researchSheetOutboxCount(consumer, "pending")', consumer)
        self.assertIn('researchSheetOutboxCount(consumer, "deferred")', consumer)
        self.assertIn("effectiveRequiresWrite", consumer)
        self.assertIn('["read_ready", "read_ready_write_unverified"].includes(consumer.status)', consumer)
        self.assertLess(consumer_failure_start, consumer.index("if (verifiedReady)"))
        consumer_pending_start = consumer.index("if (waitingOutboxCount > 0 && activeReadConnection)")
        consumer_pending_end = consumer.index("const statusIsReady", consumer_pending_start)
        consumer_pending = consumer[consumer_pending_start:consumer_pending_end]
        self.assertIn('tone: "warning"', consumer_pending)
        self.assertIn("เชื่อมอ่านแล้ว • รอซิงก์", consumer_pending)
        self.assertIn("verifiedReady: false", consumer_pending)

        active_failure_start = active.index("if (failedOutboxCount > 0)")
        active_failure_end = active.index("if (!currentRevisionVerified", active_failure_start)
        active_failure = active[active_failure_start:active_failure_end]
        self.assertIn('tone: "error"', active_failure)
        self.assertIn("Google Sheet มีรายการซิงก์ไม่สำเร็จ", active_failure)
        self.assertIn("verifiedReady: false", active_failure)
        self.assertLess(active_failure_start, active.index('tone: "ready"'))
        self.assertIn("deferredOutboxCount", active)
        self.assertIn("if (waitingOutboxCount > 0)", active)
        self.assertIn('tone: "warning"', active)
        self.assertIn("เชื่อมอ่านแล้ว • รอซิงก์", active)
        active_waiting_start = active.index("if (waitingOutboxCount > 0)")
        active_waiting_end = active.index("return {", active_waiting_start + 10)
        active_waiting_end = active.index("};", active_waiting_end) + 2
        self.assertIn(
            "verifiedReady: false",
            active[active_waiting_start:active_waiting_end],
        )
        self.assertIn('const requiresWrite = system.mode !== "read"', linked)
        self.assertIn('researchSheetOutboxCount(system, "pending")', linked)
        self.assertIn('researchSheetOutboxCount(system, "deferred")', linked)
        self.assertIn('researchSheetOutboxCount(system, "failed")', linked)
        self.assertNotIn("researchSheetActivePresentation(data)", linked)

    def test_failed_outbox_has_real_bounded_retry_action(self):
        self.assertEqual(
            self.html.count('id="researchSheetHubRetryFailed"'),
            1,
        )
        self.assertEqual(
            self.main.count(
                'document.getElementById("researchSheetHubRetryFailed")'
            ),
            1,
        )
        retry = self.block(
            "async function retryFailedResearchSheetOutbox",
            "async function queryResearchSheetHub",
        )
        self.assertIn("RESEARCH_SHEET_HUB_FLUSH_ENDPOINT", retry)
        self.assertIn("retryFailed: true", retry)
        self.assertIn("boundedResearchSheetCount(payload?.retry?.requeued, 50)", retry)
        self.assertIn("researchSheetFailedOutboxCount(hub.data)", retry)
        self.assertIn("กดซ้ำได้หลังตรวจสิทธิ์ Google แล้ว", retry)
        render = self.block(
            "function renderResearchSheetHub()",
            "function refreshOpenResearchSheetConsumer",
        )
        self.assertIn("els.researchSheetHubRetryFailed.hidden = failedCount === 0", render)
        self.assertIn('hub.operation === "retry_failed"', render)
        listeners = self.main[
            self.main.index('els.researchSheetHubRetryFailed?.addEventListener("click"'):
            self.main.index('els.researchSheetHubQuerySubmit?.addEventListener("click"')
        ]
        self.assertIn("retryFailedResearchSheetOutbox()", listeners)

    def test_active_banner_is_green_only_for_active_current_verified_revision(self):
        presentation = self.block("function researchSheetActivePresentation", "function researchSheetObservedLabel")
        summary = self.block("function researchSheetHubSummaryPresentation", "function renderResearchSheetHub")
        self.assertIn("data.active !== true", presentation)
        self.assertIn("data.connected === true", presentation)
        self.assertIn("data.readReady === true", presentation)
        self.assertIn("data.operational === true", presentation)
        self.assertIn("data.activeConfigRevision === data.configRevision", presentation)
        self.assertIn("consumer.configRevision === data.configRevision", presentation)
        self.assertIn("data.allConsumersApplied === true", presentation)
        self.assertIn("data.allConsumersVerified === true", presentation)
        self.assertIn("verified === total", presentation)
        self.assertIn("บันทึก ID แล้ว แต่ยังไม่เปิดใช้", presentation)
        self.assertIn("กำหนดให้ใช้ Sheet นี้ แต่การเชื่อมต่อขัดข้อง", presentation)
        self.assertIn("กำลังใช้ Google Sheet นี้อยู่", presentation)
        self.assertIn("data.active === true", summary)
        self.assertIn("data.allConsumersApplied === true", summary)
        self.assertIn("data.allConsumersVerified === true", summary)
        self.assertIn("readyCount === totalTabs", summary)
        self.assertIn("activePresentation.verifiedReady === true", summary)

    def test_auth_and_schema_errors_are_honest_and_do_not_claim_service_account(self):
        failure = self.block("function researchSheetHubFailureReason", "function clearResearchSheetHubPhaseTimers")
        self.assertIn("auth_required", failure)
        self.assertIn("schema_mismatch", failure)
        self.assertIn("Backend ยังไม่มี Google OAuth สำหรับเปิด Sheet นี้", failure)
        self.assertIn("หัวคอลัมน์", failure)
        self.assertNotIn("Service Account", failure)

    def test_dirty_edit_resets_preview_but_not_active_data(self):
        listeners = self.main[
            self.main.index('els.researchSheetHubReference?.addEventListener("input"'):
            self.main.index('els.researchSheetHubCancel?.addEventListener("click"')
        ]
        render = self.block("function renderResearchSheetHub()", "function refreshOpenResearchSheetConsumer")
        self.assertIn("hub.preview = null", listeners)
        self.assertIn("hub.dirty = configuredReference", listeners)
        self.assertIn("Sheet ID ถูกแก้ไขแล้ว", listeners)
        self.assertIn("ค่าที่กำลังใช้งานอยู่จะยังไม่เปลี่ยน", listeners)
        self.assertNotIn("hub.data = null", listeners)
        self.assertIn("!hub.dirty", render)
        self.assertIn("!hub.preview", render)
        self.assertIn("!hub.inFlight", render)
        self.assertIn("els.researchSheetHubReference.value = configuredSheetId", render)
        self.assertIn("hub.submittedReference = configuredSheetId", render)

    def test_active_read_model_is_fail_closed_and_includes_linked_truth(self):
        normalize = self.block("function normalizeResearchSheetHub", "function normalizeResearchSheetInspection")
        self.assertIn("root.rawSheetIdExposed === true", normalize)
        self.assertIn("rawSheetIdExposed: Boolean(rawSheetIdAllowed && sheetId)", normalize)
        self.assertIn("active: root.active === true", normalize)
        self.assertIn("operational: root.operational === true", normalize)
        self.assertIn("activeConfigRevision", normalize)
        self.assertIn("activationConfirmedAt: normalizeResearchSheetTimestamp(root.activationConfirmedAt)", normalize)
        self.assertIn("Array.isArray(root.linkedSystems)", normalize)
        self.assertIn("RESEARCH_SHEET_LINKED_SYSTEMS.map", normalize)
        self.assertIn("rowCount", normalize)
        self.assertIn("observedAt", normalize)
        self.assertIn("configRevision", normalize)

    def test_all_linked_system_cards_share_full_id_revision_and_actual_rows(self):
        identity = self.block("function researchSheetHubConfiguredReference", "function researchSheetHubFailureReason")
        linked = self.block("function renderResearchSheetHubLinkedSystems", "function renderResearchSheetHubInspection")
        factory = self.block("function renderEaFactoryGoogleSheetSync", "function renderEaFactorySourceStage")
        world = self.block("function renderWorkflowCatalog", "function getWorkflowDashboardEntries")
        radar = self.block("function createRadarRailTruthCard", "function createBackendOwnedDailyScheduleCard")
        card = self.block("function createResearchSheetConsumerCard", "function createWorkflowUseGuideCard")
        self.assertIn("data.sheetId || data.sheetReferenceMasked", identity)
        self.assertIn("configRevision", identity)
        self.assertIn("Config r", identity)
        self.assertIn("data?.linkedSystems", linked)
        self.assertIn("system.rowCount", linked)
        self.assertIn("researchSheetObservedLabel(system.observedAt)", linked)
        for renderer in (factory, world, radar, card):
            self.assertIn("researchSheetHubConfiguredReference", renderer)

    def test_factory_uses_deep_research_without_duplicate_sheet_input(self):
        renderer = self.block("function renderEaFactoryGoogleSheetSync", "function renderEaFactorySourceStage")
        schema_renderer = self.block("function renderEaFactorySheetSchema", "function renderEaFactoryGoogleSheetSync")
        sync = self.block("async function syncEaFactoryGoogleSheet", "async function createEaFactoryBuild")
        self.assertIn("researchSheetConsumerPresentation(TRADING_RESEARCH_LAB_PROP_ID, { requiresWrite: false })", renderer)
        self.assertIn("Deep_Research", self.main)
        self.assertNotIn('createElement("input")', renderer)
        self.assertNotIn('name = "googleSheetUrlOrId"', renderer)
        self.assertIn("{ idempotencyKey }", sync)
        self.assertNotIn("googleSheetUrlOrId", sync)
        self.assertIn("sheetSchema.sourceRequiredHeaders", schema_renderer)
        self.assertIn("sheetSchema.sheetTabDefault", schema_renderer)
        self.assertIn("eaFactorySpreadsheetColumnName(sourceHeaders.length)", schema_renderer)
        self.assertIn("${sourceHeaders.length} headers", schema_renderer)
        self.assertIn("ไม่ใช่ช่วงคอลัมน์ Google Sheet", schema_renderer)
        self.assertNotIn("Schema Google Sheets A-W", schema_renderer)

    def test_progress_and_layout_are_accessible_and_responsive(self):
        progress = self.block("function renderResearchSheetHubProgress", "function researchSheetConsumer")
        self.assertIn('["inspecting", "verifying", "activating"]', progress)
        self.assertIn('step.setAttribute("aria-current", "step")', progress)
        self.assertIn("awaiting_confirmation", progress)
        self.assertIn(".research-sheet-hub-active", self.styles)
        self.assertIn(".research-sheet-hub-linked-systems", self.styles)
        self.assertIn(".research-sheet-hub-inspection-tabs", self.styles)
        self.assertIn("@keyframes research-sheet-spin", self.styles)
        self.assertIn("@media (max-width: 900px)", self.styles)
        self.assertIn("@media (max-width: 640px)", self.styles)

    def test_topbar_hub_has_explicit_responsive_breakpoints(self):
        for width in (1300, 900, 640):
            with self.subTest(width=width):
                media_starts = [
                    match.start()
                    for match in re.finditer(rf"@media \(max-width: {width}px\)\s*\{{", self.styles)
                ]
                media_blocks = [
                    self.styles[start:self.styles.find("@media", start + 1)]
                    if self.styles.find("@media", start + 1) >= 0
                    else self.styles[start:]
                    for start in media_starts
                ]
                self.assertTrue(
                    any(
                        selector in block
                        for block in media_blocks
                        for selector in (
                            ".topbar-research-sheet-hub",
                            ".research-sheet-hub-toolbar",
                            ".research-sheet-hub-popover",
                        )
                    ),
                    f"Topbar Research Sheet Hub must have a {width}px responsive rule",
                )

    def test_global_render_is_not_tied_to_mission_table_visibility(self):
        render = self.block("function renderResearchSheetHub()", "function refreshOpenResearchSheetConsumer")
        self.assertNotIn('state.modal.id === "mission_strategy_table"', render)
        self.assertNotIn('state.modal.id !== "mission_strategy_table"', render)
        self.assertIn("els.researchSheetHub.hidden = false", render)

    def test_global_status_loads_on_initial_read_refresh_burst_and_periodic_poll(self):
        burst = self.block("function runAutomaticPollingBurst()", "function runInitialPollingRead()")
        initial = self.block("function runInitialPollingRead()", "function stopAutomaticPolling()")
        periodic = self.block("function startMissionPolling()", "async function loadMemoryStatus")
        self.assertIn("loadResearchSheetHub({ signal })", burst)
        self.assertIn("loadResearchSheetHub()", initial)
        self.assertIn("loadResearchSheetHub({ signal })", periodic)
        self.assertIn("loadResearchSheetGoogleAuth({ signal })", burst)
        self.assertIn("loadResearchSheetGoogleAuth()", initial)
        self.assertIn("loadResearchSheetGoogleAuth({ signal })", periodic)

    def test_popover_auto_opens_for_inspection_and_preview_and_escape_closes_first(self):
        render = self.block("function renderResearchSheetHub()", "function refreshOpenResearchSheetConsumer")
        inspect = self.block("async function inspectResearchSheetHub", "async function activateResearchSheetHub")
        activate = self.block("async function activateResearchSheetHub", "function normalizeOperatorModePayload")
        self.assertIn("hub.panelOpen = true", inspect)
        self.assertIn("hub.panelOpen = true", activate)
        self.assertIn("hub.panelOpen || hub.inFlight || Boolean(hub.preview)", render)
        self.assertIn("els.researchSheetHubPopover.hidden = !popoverOpen", render)
        self.assertIn('setAttribute("aria-expanded", String(popoverOpen))', render)

        toggle_start = self.main.index('els.researchSheetHubDetailsToggle?.addEventListener("click"')
        toggle_listener = self.main[
            toggle_start:self.main.index('document.addEventListener("click"', toggle_start)
        ]
        self.assertIn("setResearchSheetHubPanelOpen", toggle_listener)

        keydown_start = self.main.rindex('document.addEventListener("keydown", (event) => {')
        keydown_end = self.main.index('els.stage.addEventListener("click"', keydown_start)
        keydown = self.main[keydown_start:keydown_end]
        self.assertIn("closeResearchSheetHubPopover()", keydown)
        self.assertLess(
            keydown.index("closeResearchSheetHubPopover()"),
            keydown.index("if (state.modal.open) closeGameModal()"),
        )

    def test_world_and_radar_show_central_backend_status(self):
        world = self.block("function renderWorkflowCatalog", "function getWorkflowDashboardEntries")
        radar = self.block("function createRadarRailTruthCard", "function createBackendOwnedDailyScheduleCard")
        self.assertIn('researchSheetConsumerPresentation("codex_mcp_portal")', world)
        self.assertNotIn("Coming Soon", world)
        self.assertIn("Google Sheet กลาง", radar)
        self.assertIn("researchSheetHubConfiguredReference", radar)
        self.assertNotIn("(ตัวเลือก)", radar)


if __name__ == "__main__":
    unittest.main()
