import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SimplifiedEquipmentHubsFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main = (ROOT / "frontend" / "src" / "app" / "main.js").read_text(encoding="utf-8")
        cls.styles = (ROOT / "frontend" / "src" / "app" / "styles.css").read_text(encoding="utf-8")

    def function_block(self, name: str, next_name: str) -> str:
        start = self.main.index(f"function {name}(")
        end = self.main.index(f"function {next_name}(", start)
        return self.main[start:end]

    def function_source(self, name: str) -> str:
        start = self.main.index(f"function {name}(")
        end = self.main.find("\nfunction ", start + 1)
        return self.main[start:] if end < 0 else self.main[start:end]

    def style_block(self, selector: str) -> str:
        start = self.styles.index(selector)
        end = self.styles.index("}", start)
        return self.styles[start:end]

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
        self.skipTest("Node.js is required for the frontend normalizer regression")

    def run_node_script(self, script: str) -> subprocess.CompletedProcess[str]:
        # Windows limits command-line length; execute generated regression scripts from a temp file.
        with tempfile.TemporaryDirectory() as directory:
            script_path = Path(directory) / "frontend-regression.js"
            script_path.write_text(script, encoding="utf-8")
            return subprocess.run(
                [self.node_binary(), str(script_path)],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

    def test_fx_default_presentation_has_assessments_news_and_backend_history(self):
        self.assertIn('left_signal_cube: "ศูนย์แนวโน้ม 28 คู่เงินและข่าว Forex"', self.main)
        self.assertIn(
            'const FX_NEWS_BIAS_PRESENTATION_TAB_IDS = Object.freeze(["pair_bias", "today", "history"]);',
            self.main,
        )
        normalize = self.main[
            self.main.index("function normalizeWorkflowDashboard("):
            self.main.index("function getWorkflowSelectedTab(")
        ]
        self.assertIn("FX_NEWS_BIAS_PRESENTATION_TAB_IDS", normalize)
        self.assertIn('pair_bias: "ผลประเมิน 28 คู่เงิน"', normalize)
        self.assertIn('history: "ประวัติอัปเดต"', normalize)
        self.assertIn("actionIds: []", normalize)
        self.assertIn('id: "history"', normalize[normalize.index("subject?.id === FX_NEWS_BIAS_PROP_ID"):])

        domain = self.function_block("normalizeFxNewsBiasDomain", "normalizeConnectionCenterDevice")
        self.assertIn("FX_BIAS_PAIR_UNIVERSE.map", domain)
        self.assertIn('summary: "รอข้อมูลจริงจาก Backend"', domain)
        panel = self.function_block("renderFxNewsBiasPanel", "renderTerminalOutputPanel")
        self.assertIn("renderFxBiasGrid(section, domain.pairBias, domain.pairAssessmentSummary)", panel)
        self.assertIn("renderFxNewsHistory(section, domain)", panel)
        self.assertNotIn("renderWorkflowSourceCards", panel)

    def test_history_is_explicit_so_fx_news_and_status_tabs_never_become_history_by_position(self):
        render = self.function_block("renderWorkflowDashboard", "setWorkflowDashboardTab")
        self.assertIn(
            "const isHistoryTab = WORKFLOW_DASHBOARD_HISTORY_TAB_IDS.has(selectedTab?.id);",
            render,
        )
        self.assertNotIn("selectedTab?.id === dashboard.tabs.at(-1)?.id", render)
        self.assertIn("[INDICATOR_SCOUT_PROP_ID, FX_NEWS_BIAS_PROP_ID]", render)
        self.assertIn("els.workflowResultsPanel.hidden = isFxNewsDashboard", render)

    def test_connection_hub_uses_backend_connection_center_as_authority_without_fanout(self):
        self.assertIn('right_status_crystals: "ศูนย์การเชื่อมต่ออุปกรณ์ HQ"', self.main)
        normalize = self.function_block("normalizeVpsHqDomain", "normalizeWorkflowDomainData")
        for token in (
            "backend.connectionCenter",
            "connectionCenterRoot.devices",
            "connectionCenterRoot.summary",
            "connectionCenterRoot.services",
            "authoritative: Object.keys(connectionCenterRoot).length > 0",
        ):
            self.assertIn(token, normalize)

        entries = self.function_block("workflowConnectionHubEntries", "renderConnectionHubServices")
        self.assertIn("connectionCenter.authoritative === true", entries)
        self.assertIn("state.propReports[propId]", entries)
        self.assertNotIn("loadPropReport(", entries)
        panel = self.function_block("renderConnectionHubPanel", "renderVpsHqPanel")
        self.assertIn("HQ_CONNECTION_HUB_FILTER_IDS", panel)
        self.assertIn("workflow-connection-remedy", panel)
        self.assertIn("สรุปจาก Snapshot กลางของ Backend เท่านั้น", panel)
        self.assertNotIn("สรุปจากผลตรวจที่ Frontend ได้รับแล้วเท่านั้น", panel)
        self.assertIn("data", panel)
        self.assertNotIn("loadPropReport(", panel)

    def test_generic_connection_rail_is_hidden_for_all_dashboards(self):
        modal = self.function_block("renderGameModal", "openGameModal")
        self.assertIn("els.modalDashboardConnectionRail.hidden = true", modal)
        self.assertNotIn('modalDashboardConnectionRail.hidden = surface !== "dashboard"', modal)
        self.assertIn('signal-consensus-modal", surface === "dashboard" && subject.id === AI_TRADE_COUNCIL_PROP_ID', modal)

    def test_daily_news_uses_a_direct_backend_only_left_rail(self):
        rail_actions = self.function_block("workflowRailActions", "createWorkflowUseGuideCard")
        self.assertIn("INDICATOR_SCOUT_RAIL_ACTION_IDS", rail_actions)
        self.assertIn("if (subject?.id === FX_NEWS_BIAS_PROP_ID) return [];", rail_actions)
        self.assertIn("return [...actions]", rail_actions)
        direct_rail = self.function_block("renderFxNewsSettingsRail", "renderWorkflowSettingsRail")
        self.assertIn('checkbox.dataset.fxNewsScheduleEnabled = "true"', direct_rail)
        self.assertIn("schedule.times.slice(0, 2)", direct_rail)
        self.assertIn('timezone.textContent = "เวลาไทย • Asia/Bangkok • สูงสุด 2 รอบต่อวัน"', direct_rail)
        self.assertIn("service.sources", direct_rail)
        self.assertIn("service.directRefreshAvailable === true", direct_rail)
        settings = self.function_block("renderWorkflowSettingsRail", "getWorkflowHandoffReports")
        self.assertIn("renderFxNewsSettingsRail(dashboard, identity)", settings)
        self.assertIn("return;", settings)
        self.assertIn("workflowRailActions(subject, dashboard)", settings)
        self.assertIn("createWorkflowUseGuideCard(subject)", settings)
        self.assertIn("els.workflowSettingsRail.hidden = false", settings)

    def test_connection_guidance_points_to_the_central_hub_and_news_schedule_caps_two_times(self):
        self.assertNotIn("ตรวจการเชื่อมต่อด้านซ้าย", self.main)
        self.assertIn("เปิดศูนย์การเชื่อมต่ออุปกรณ์ HQ จากปุ่มด้านซ้าย", self.main)
        self.assertIn('const FX_NEWS_BIAS_DEFAULT_TIMES = Object.freeze(["00:00", "12:00"]);', self.main)
        self.assertIn("schedule.times.slice(0, 2)", self.main)

    def test_grid_hub_and_compact_rail_have_responsive_styles(self):
        for selector in (
            ".workflow-fx-bias-grid",
            ".workflow-fx-bias-card",
            ".workflow-fx-horizons",
            ".workflow-connection-hub-grid",
            ".workflow-connection-hub-card",
            ".workflow-connection-hub-filters",
            ".workflow-connection-remedy",
            ".workflow-use-guide",
        ):
            self.assertIn(selector, self.styles)
        self.assertIn("@media (max-width: 520px)", self.styles)

    def test_fx_grid_and_connection_hub_critical_text_meets_readability_floor(self):
        expected_sizes = {
            ".workflow-bias-badge {": "font-size: 11px",
            ".workflow-fx-bias-summary p,": "font-size: 12px",
            ".workflow-fx-horizons span {": "font-size: 10px",
            ".workflow-fx-horizons strong {": "font-size: 11px",
            ".workflow-fx-bias-card > p {": "font-size: 12px",
            ".workflow-fx-bias-card > footer small {": "font-size: 10px",
            ".workflow-connection-filter,": "font-size: 11px",
            ".workflow-connection-services span {": "font-size: 10px",
            ".workflow-connection-services strong {": "font-size: 11px",
            ".workflow-connection-hub-card .connection-badge {": "font-size: 11px",
            ".workflow-connection-hub-card > p {": "font-size: 10px",
            ".workflow-connection-remedy strong {": "font-size: 11px",
            ".workflow-connection-remedy p {": "font-size: 12px",
            ".workflow-connection-hub-card > footer small {": "font-size: 10px",
            ".workflow-news-grid article > span,": "font-size: 10px",
            ".workflow-news-grid p,": "font-size: 12px",
            ".workflow-external-link,": "font-size: 11px",
            ".workflow-settings-rail .workflow-availability {": "font-size: 11px",
            '.workflow-settings-rail .workflow-field input:not([type="checkbox"]),': "font-size: 12px",
            ".workflow-settings-rail .workflow-field > span,": "font-size: 10px",
            ".workflow-settings-rail .workflow-action-footer p {": "font-size: 12px",
            ".workflow-use-guide ol {": "font-size: 12px",
            ".workflow-freshness-banner > strong {": "font-size: 13px",
            ".workflow-freshness-banner > p {": "font-size: 12px",
        }
        for selector, declaration in expected_sizes.items():
            with self.subTest(selector=selector):
                self.assertIn(declaration, self.style_block(selector))

        self.assertIn(
            ".workflow-fx-bias-grid {\n    grid-template-columns: repeat(2, minmax(0, 1fr));",
            self.styles,
        )
        self.assertIn(
            ".workflow-fx-bias-grid {\n    grid-template-columns: minmax(0, 1fr);",
            self.styles,
        )

    def test_fx_sibling_read_models_populate_news_danger_and_all_28_pairs(self):
        fixture = {
            "marketNews": {
                "asOf": "2026-08-12T08:00:00+07:00",
                "currentBangkokDate": "2026-08-12",
                "reportBangkokDate": "2026-08-12",
                "stale": False,
                "currentDataAvailable": True,
                "dataStatus": "current",
                "sources": [{"id": "source-cpi", "url": "https://example.com/cpi"}, {"id": "source-window", "url": "https://example.com/cpi-window"}],
                "events": [
                    {
                        "eventId": "event-cpi",
                        "titleTh": "ตัวเลข CPI สหรัฐ",
                        "summaryTh": "เงินเฟ้ออาจเพิ่มความผันผวนให้ USD",
                        "scheduledAt": "2026-08-12T12:30:00Z",
                        "currencies": ["USD"],
                        "impact": "high",
                        "sourceLinks": [{"url": "https://example.com/cpi"}],
                    }
                ],
                "dangerWindows": [
                    {
                        "windowId": "danger-cpi",
                        "startsAt": "2026-08-12T12:15:00Z",
                        "endsAt": "2026-08-12T12:45:00Z",
                        "reasonTh": "หลีกเลี่ยงช่วงประกาศ CPI",
                        "currencies": ["USD"],
                        "sourceLinks": [{"url": "https://example.com/cpi-window"}],
                    }
                ],
            },
            "fxBias": {
                "asOf": "2026-08-12T08:00:00+07:00",
                "currentBangkokDate": "2026-08-12",
                "reportBangkokDate": "2026-08-12",
                "stale": False,
                "currentDataAvailable": True,
                "dataStatus": "current",
                "sources": [{"id": "bias-eurusd", "url": "https://example.com/eurusd"}],
                "pairs": [
                    {
                        "pair": "EURUSD",
                        "status": "source_backed",
                        "horizons": {
                            "short": {"bias": "bullish", "reasonTh": "โมเมนตัมสั้นเป็นบวก"},
                            "medium": {"bias": "bullish", "reasonTh": "แนวโน้มกลางเป็นบวก"},
                            "long": {"bias": "sideway", "reasonTh": "ภาพยาวยังพักตัว"},
                        },
                        "sourceLinks": [{"url": "https://example.com/eurusd"}],
                    },
                    {
                        "pair": "GBPUSD",
                        "status": "insufficient_data",
                        "shortBias": "bullish",
                        "mediumBias": "bullish",
                        "longBias": "bullish",
                    },
                ]
            },
        }
        pair_universe = [
            "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD",
            "CADCHF", "CADJPY", "CHFJPY",
            "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
            "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
            "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD",
            "USDCAD", "USDCHF", "USDJPY",
        ]
        function_names = (
            "workflowDomainObject",
            "workflowDomainArray",
            "workflowReportRows",
            "normalizeFxBiasValue",
            "fxBiasHorizonValue",
            "normalizeFxFreshness",
            "workflowSourceLinkRows",
            "workflowItemSourceUrl",
            "isFxNewsReferenceOnlyUrl",
            "fxNewsVerifiedSourceLinks",
            "fxNewsVerifiedItemSources",
            "normalizeFxNewsImpact",
            "normalizeFxNewsMetric",
            "normalizeFxNewsPairImpactRows",
            "fxNewsCalendarRows",
            "normalizeFxNewsEvent",
            "deriveFxOverallBias",
            "normalizeFxPairAssessmentEvent",
            "normalizeFxPairAssessmentStatus",
            "deriveFxPairAssessmentSummary",
            "normalizeFxNewsScheduleTime",
            "normalizeFxNewsSchedule",
            "normalizeFxNewsHistoryItem",
            "normalizeFxNewsHistory",
            "normalizeFxNewsBiasDomain",
        )
        script = "\n".join(
            [
                f"const FX_BIAS_PAIR_UNIVERSE = Object.freeze({json.dumps(pair_universe)});",
                "const safeDashboardDisplayText = (value, fallback = '') => String(value ?? '').trim() || fallback;",
                "const getSafeExternalHttpUrl = (value) => { try { const url = new URL(String(value || '')); return ['http:', 'https:'].includes(url.protocol) ? url.href : ''; } catch { return ''; } };",
                *(self.function_source(name) for name in function_names),
                f"const fixture = {json.dumps(fixture, ensure_ascii=False)};",
                "const domain = normalizeFxNewsBiasDomain(fixture, {});",
                "const eurusd = domain.pairBias.find((row) => row.pair === 'EURUSD');",
                "const gbpusd = domain.pairBias.find((row) => row.pair === 'GBPUSD');",
                "const placeholder = domain.pairBias.find((row) => row.pair === 'AUDCAD');",
                "process.stdout.write(JSON.stringify({news: domain.news, dangerWindows: domain.dangerWindows, freshness: domain.freshness, pairCount: domain.pairBias.length, eurusd, gbpusd, placeholder}));",
            ]
        )
        result = self.run_node_script(script)
        payload = json.loads(result.stdout)

        self.assertEqual(payload["news"][0]["id"], "event-cpi")
        self.assertEqual(payload["news"][0]["title"], "ตัวเลข CPI สหรัฐ")
        self.assertEqual(payload["news"][0]["currencies"], ["USD"])
        self.assertEqual(payload["news"][0]["sourceUrl"], "https://example.com/cpi")
        self.assertEqual(payload["dangerWindows"][0]["id"], "danger-cpi")
        self.assertEqual(payload["dangerWindows"][0]["reason"], "หลีกเลี่ยงช่วงประกาศ CPI")
        self.assertEqual(payload["dangerWindows"][0]["sourceUrl"], "https://example.com/cpi-window")
        self.assertEqual(payload["pairCount"], 28)
        self.assertEqual(payload["eurusd"]["short"], "bullish")
        self.assertEqual(payload["eurusd"]["medium"], "bullish")
        self.assertEqual(payload["eurusd"]["long"], "sideway")
        self.assertEqual(payload["eurusd"]["bias"], "unavailable")
        self.assertEqual(payload["eurusd"]["sourceUrl"], "https://example.com/eurusd")
        self.assertEqual(payload["gbpusd"]["bias"], "unavailable")
        self.assertEqual(payload["gbpusd"]["short"], "unavailable")
        self.assertEqual(payload["placeholder"]["bias"], "unavailable")
        self.assertEqual(payload["freshness"]["marketNews"]["dataStatus"], "current")
        self.assertTrue(payload["freshness"]["marketNews"]["currentDataAvailable"])
        self.assertEqual(payload["freshness"]["fxBias"]["reportBangkokDate"], "2026-08-12")

        panel = self.function_block("renderFxNewsBiasPanel", "renderTerminalOutputPanel")
        self.assertIn("domain.dangerWindows", panel)
        self.assertIn("domain.news", panel)
        self.assertIn("renderFxBiasGrid(section, domain.pairBias, domain.pairAssessmentSummary)", panel)

    def test_pair_news_assessment_renders_complete_coverage_without_inventing_direction(self):
        pair_universe = [
            "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD",
            "CADCHF", "CADJPY", "CHFJPY",
            "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
            "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
            "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD",
            "USDCAD", "USDCHF", "USDJPY",
        ]
        usd_event = {
            "eventId": "retail-usd", "titleTh": "ยอดค้าปลีกสหรัฐ", "currencies": ["USD"],
            "impact": "high", "timeKind": "timed", "scheduledAtUtc": "2026-08-14T12:30:00Z",
            "scheduledAtBangkok": "2026-08-14T19:30:00+07:00", "timingState": "future",
            "actualStatus": "pending", "releaseState": "scheduled", "analysisStatus": "pending_release",
            "forecast": "0.4%", "previous": "0.2%", "sourceRefs": ["official-usd"],
        }
        cad_event = {
            "eventId": "factory-cad", "titleTh": "ยอดขายภาคการผลิตแคนาดา", "currencies": ["CAD"],
            "impact": "medium", "timeKind": "timed", "scheduledAtUtc": "2026-08-14T12:30:00Z",
            "scheduledAtBangkok": "2026-08-14T19:30:00+07:00", "timingState": "past",
            "actualStatus": "released", "releaseState": "released", "analysisStatus": "insufficient_data",
            "actual": "-0.8%", "forecast": "-0.5%", "previous": "0.3%", "sourceRefs": ["official-cad"],
        }
        pair_rows = []
        for pair in pair_universe:
            if "USD" in pair:
                assessment_status, events = "upcoming_event", [usd_event]
            elif "CAD" in pair:
                assessment_status, events = "released_no_direction", [cad_event]
            else:
                assessment_status, events = "no_direct_event", []
            pair_rows.append({
                "pair": pair,
                "status": "insufficient_data",
                "horizons": {
                    "short": {"bias": "INSUFFICIENT_DATA"},
                    "medium": {"bias": "INSUFFICIENT_DATA"},
                    "long": {"bias": "INSUFFICIENT_DATA"},
                },
                "assessmentStatus": assessment_status,
                "assessmentComplete": True,
                "relevantEventCount": len(events),
                "relevantEvents": [
                    {**event, "titleTh": "ข้อความ row ที่ห้ามใช้แทนข่าวที่ตรวจแหล่งแล้ว"}
                    for event in events
                ],
                "nextEvent": (
                    {**events[0], "titleTh": "ข้อความ nextEvent ที่ห้ามใช้แทนข่าวที่ตรวจแหล่งแล้ว"}
                    if events else None
                ),
            })
        fixture = {
            "marketNews": {
                "calendarDate": "2026-08-14", "currentBangkokDate": "2026-08-14",
                "reportBangkokDate": "2026-08-14", "dataStatus": "verified",
                "currentDataAvailable": True, "stale": False,
                "sources": [
                    {"id": "official-usd", "url": "https://example.com/usd"},
                    {"id": "official-cad", "url": "https://example.com/cad"},
                ],
                "events": [usd_event, cad_event],
            },
            "fxBias": {
                "dataStatus": "verified", "currentDataAvailable": True, "stale": False,
                "assessmentComplete": True,
                "assessedPairCount": 28, "directionalPairCount": 0,
                "upcomingEventPairCount": 7, "awaitingActualPairCount": 0,
                "awaitingEventPairCount": 7, "releasedNoDirectionPairCount": 6,
                "noDirectEventPairCount": 15, "unavailablePairCount": 0,
                "pairs": pair_rows,
            },
        }
        function_names = (
            "workflowDomainObject", "workflowDomainArray", "workflowReportRows", "normalizeFxBiasValue",
            "fxBiasHorizonValue", "normalizeFxFreshness", "workflowSourceLinkRows", "workflowItemSourceUrl",
            "isFxNewsReferenceOnlyUrl", "fxNewsVerifiedSourceLinks", "fxNewsVerifiedItemSources",
            "normalizeFxNewsImpact", "normalizeFxNewsMetric", "normalizeFxNewsPairImpactRows",
            "fxNewsCalendarRows", "normalizeFxNewsEvent", "deriveFxOverallBias",
            "normalizeFxPairAssessmentEvent", "normalizeFxPairAssessmentStatus",
            "deriveFxPairAssessmentSummary", "normalizeFxNewsScheduleTime", "normalizeFxNewsSchedule",
            "normalizeFxNewsHistoryItem", "normalizeFxNewsHistory", "normalizeFxNewsBiasDomain",
        )
        script = "\n".join([
            f"const FX_BIAS_PAIR_UNIVERSE = Object.freeze({json.dumps(pair_universe)});",
            "const safeDashboardDisplayText = (value, fallback = '') => String(value ?? '').trim() || fallback;",
            "const getSafeExternalHttpUrl = (value) => { try { const url = new URL(String(value || '')); return ['http:', 'https:'].includes(url.protocol) ? url.href : ''; } catch { return ''; } };",
            *(self.function_source(name) for name in function_names),
            f"const fixture = {json.dumps(fixture, ensure_ascii=False)};",
            "const domain = normalizeFxNewsBiasDomain(fixture, {});",
            "const byPair = Object.fromEntries(domain.pairBias.map((row) => [row.pair, row]));",
            "const incompleteFixture = JSON.parse(JSON.stringify(fixture));",
            "incompleteFixture.fxBias.pairs.find((row) => row.pair === 'EURUSD').assessmentComplete = false;",
            "const incomplete = normalizeFxNewsBiasDomain(incompleteFixture, {});",
            "const staleFixture = JSON.parse(JSON.stringify(fixture));",
            "Object.assign(staleFixture.fxBias, {stale:true,currentDataAvailable:false,dataStatus:'stale'});",
            "const stale = normalizeFxNewsBiasDomain(staleFixture, {});",
            "const partialFixture = JSON.parse(JSON.stringify(fixture));",
            "partialFixture.fxBias.sources = [{id:'official-usd',url:'https://example.com/usd'}];",
            "const partialRow = partialFixture.fxBias.pairs.find((row) => row.pair === 'AUDNZD');",
            "Object.assign(partialRow, {status:'source_backed',assessmentStatus:'directional_ready',sourceLinks:[{url:'https://example.com/usd'}]});",
            "partialRow.horizons.short.bias = 'BULLISH';",
            "const partial = normalizeFxNewsBiasDomain(partialFixture, {});",
            "const partialAudnzd = partial.pairBias.find((row) => row.pair === 'AUDNZD');",
            "process.stdout.write(JSON.stringify({summary:domain.pairAssessmentSummary,eurusd:byPair.EURUSD,audcad:byPair.AUDCAD,audnzd:byPair.AUDNZD,freshness:domain.freshness.fxBias,incompleteSummary:incomplete.pairAssessmentSummary,incompleteEurusd:incomplete.pairBias.find((row)=>row.pair==='EURUSD'),staleSummary:stale.pairAssessmentSummary,partialSummary:partial.pairAssessmentSummary,partialAudnzd}));",
        ])
        result = self.run_node_script(script)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"], {
            "assessedPairCount": 28,
            "directionalPairCount": 0,
            "awaitingEventPairCount": 7,
            "upcomingEventPairCount": 7,
            "awaitingActualPairCount": 0,
            "releasedNoDirectionPairCount": 6,
            "noDirectEventPairCount": 15,
            "unavailablePairCount": 0,
            "assessmentComplete": True,
        })
        self.assertTrue(payload["freshness"]["currentDataAvailable"])
        self.assertEqual(payload["eurusd"]["assessmentStatus"], "upcoming_event")
        self.assertTrue(payload["eurusd"]["assessmentComplete"])
        self.assertEqual(payload["eurusd"]["nextEvent"]["title"], "ยอดค้าปลีกสหรัฐ")
        self.assertTrue(all(payload["eurusd"][key] == "unavailable" for key in ("bias", "short", "medium", "long")))
        self.assertEqual(payload["audcad"]["assessmentStatus"], "released_no_direction")
        self.assertEqual(payload["audnzd"]["assessmentStatus"], "no_direct_event")
        self.assertEqual(payload["audnzd"]["relevantEventCount"], 0)
        self.assertEqual(payload["incompleteEurusd"]["assessmentStatus"], "unavailable")
        self.assertFalse(payload["incompleteEurusd"]["assessmentComplete"])
        self.assertEqual(payload["incompleteSummary"]["assessedPairCount"], 27)
        self.assertEqual(payload["incompleteSummary"]["unavailablePairCount"], 1)
        self.assertEqual(payload["staleSummary"]["assessedPairCount"], 0)
        self.assertEqual(payload["staleSummary"]["unavailablePairCount"], 28)
        self.assertEqual(payload["partialAudnzd"]["assessmentStatus"], "directional_ready")
        self.assertEqual(payload["partialAudnzd"]["short"], "bullish")
        self.assertEqual(payload["partialAudnzd"]["medium"], "unavailable")
        self.assertEqual(payload["partialAudnzd"]["bias"], "unavailable")
        self.assertEqual(payload["partialSummary"]["directionalPairCount"], 1)

        grid = self.function_source("renderFxBiasGrid")
        self.assertIn("คู่ประเมินข่าวแล้ว", grid)
        self.assertIn("คู่มี Bias ยืนยัน", grid)
        self.assertIn("fxPairHorizonLabel(item, bias)", grid)
        self.assertNotIn("คู่มีข้อมูล", grid)
        self.assertIn("ไม่พบข่าวตรงของคู่เงินนี้ในปฏิทินรอบปัจจุบัน", self.main)
        self.assertIn("ข่าวออกแล้วแต่ยังไม่มี Bias ยืนยัน", self.main)
        self.assertIn("รอ Actual ข่าว", self.main)
        self.assertIn("มี Bias ยืนยัน", self.main)
        self.assertIn("วันหยุดวันนี้", self.main)
        self.assertIn("เหตุการณ์ตลอดวัน", self.main)

        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        self.assertIn("20260814-daily-news-direct-v060", html)
        self.assertNotIn("20260814-pair-news-assessment-v055", html)
        self.assertNotIn("20260814-runtime-truth-v054", html)
        self.assertNotIn("20260808-workflow-friendly-v053", html)

    def test_directional_pair_summary_keeps_verified_next_event_caution(self):
        script = "\n".join([
            "const fxNewsEventTimeLabel = () => '19:30';",
            self.function_source("fxPairAssessmentSummaryText"),
            "process.stdout.write(fxPairAssessmentSummaryText({assessmentStatus:'directional_ready',bias:'unavailable',summary:'ยืนยัน Bias ระยะสั้น',nextEvent:{title:'ยอดค้าปลีกสหรัฐ',currencies:['USD'],timeKind:'timed',eventAt:'2026-08-14T12:30:00Z'}}));",
        ])
        result = self.run_node_script(script)
        self.assertEqual(
            result.stdout,
            "ยืนยัน Bias ระยะสั้น • ข่าวถัดไป USD: ยอดค้าปลีกสหรัฐ • 19:30 • โปรดระวังความผันผวน",
        )

    def test_fx_stale_rollover_preserves_freshness_and_suppresses_old_truth(self):
        fixture = {
            "marketNews": {
                "asOf": "2026-08-12T01:00:00+07:00",
                "currentBangkokDate": "2026-08-12",
                "reportBangkokDate": "2026-08-11",
                "stale": True,
                "currentDataAvailable": False,
                "dataStatus": "stale",
                "events": [{"eventId": "old-news", "titleTh": "old", "scheduledAt": "2026-08-11T12:00:00Z"}],
                "dangerWindows": [{"windowId": "old-window", "reasonTh": "old"}],
            },
            "fxBias": {
                "asOf": "2026-08-12T01:00:00+07:00",
                "currentBangkokDate": "2026-08-12",
                "reportBangkokDate": "2026-08-11",
                "stale": True,
                "currentDataAvailable": False,
                "dataStatus": "stale",
                "pairs": [{
                    "pair": "EURUSD",
                    "status": "source_backed",
                    "shortBias": "bullish",
                    "mediumBias": "bullish",
                    "longBias": "bullish",
                    "sourceLinks": [{"url": "https://example.com/stale-eurusd"}],
                }],
            },
        }
        pair_universe = [
            "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD",
            "CADCHF", "CADJPY", "CHFJPY",
            "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
            "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
            "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD",
            "USDCAD", "USDCHF", "USDJPY",
        ]
        function_names = (
            "workflowDomainObject",
            "workflowDomainArray",
            "workflowReportRows",
            "normalizeFxBiasValue",
            "fxBiasHorizonValue",
            "normalizeFxFreshness",
            "workflowSourceLinkRows",
            "workflowItemSourceUrl",
            "isFxNewsReferenceOnlyUrl",
            "fxNewsVerifiedSourceLinks",
            "fxNewsVerifiedItemSources",
            "normalizeFxNewsImpact",
            "normalizeFxNewsMetric",
            "normalizeFxNewsPairImpactRows",
            "fxNewsCalendarRows",
            "normalizeFxNewsEvent",
            "deriveFxOverallBias",
            "normalizeFxPairAssessmentEvent",
            "normalizeFxPairAssessmentStatus",
            "deriveFxPairAssessmentSummary",
            "normalizeFxNewsScheduleTime",
            "normalizeFxNewsSchedule",
            "normalizeFxNewsHistoryItem",
            "normalizeFxNewsHistory",
            "normalizeFxNewsBiasDomain",
        )
        script = "\n".join(
            [
                f"const FX_BIAS_PAIR_UNIVERSE = Object.freeze({json.dumps(pair_universe)});",
                "const safeDashboardDisplayText = (value, fallback = '') => String(value ?? '').trim() || fallback;",
                "const getSafeExternalHttpUrl = (value) => { try { const url = new URL(String(value || '')); return ['http:', 'https:'].includes(url.protocol) ? url.href : ''; } catch { return ''; } };",
                *(self.function_source(name) for name in function_names),
                f"const fixture = {json.dumps(fixture, ensure_ascii=False)};",
                "const domain = normalizeFxNewsBiasDomain(fixture, {});",
                "process.stdout.write(JSON.stringify(domain));",
            ]
        )
        result = self.run_node_script(script)
        domain = json.loads(result.stdout)

        self.assertEqual(domain["freshness"]["marketNews"], {
            "asOf": "2026-08-12T01:00:00+07:00",
            "currentBangkokDate": "2026-08-12",
            "reportBangkokDate": "2026-08-11",
            "stale": True,
            "currentDataAvailable": False,
            "dataStatus": "stale",
            "evidenceStatus": "unknown",
            "failClosed": False,
            "verifiedEmpty": False,
            "reasonCode": "",
        })
        self.assertEqual(domain["freshness"]["fxBias"], domain["freshness"]["marketNews"])
        self.assertEqual(domain["news"], [])
        self.assertEqual(domain["dangerWindows"], [])
        self.assertEqual(len(domain["pairBias"]), 28)
        self.assertTrue(all(
            all(row[key] == "unavailable" for key in ("bias", "short", "medium", "long"))
            for row in domain["pairBias"]
        ))
        self.assertFalse(any(row["sourceUrl"] for row in domain["pairBias"]))

        banner = self.function_source("createFxFreshnessBanner")
        panel = self.function_block("renderFxNewsBiasPanel", "renderTerminalOutputPanel")
        backend_state = self.function_source("appendFxNewsBackendState")
        self.assertIn("ยังไม่มีข้อมูลของวันนี้", banner)
        self.assertIn("freshness?.stale !== true", banner)
        self.assertIn("calendar?.verifiedEmpty", backend_state)
        self.assertIn('"source_failure"', backend_state)
        self.assertIn('"no_verified_data"', backend_state)
        self.assertIn("domain?.freshness?.marketNews", panel)
        self.assertIn("domain?.freshness?.fxBias", panel)

    def test_daily_news_calendar_normalizes_canonical_truth_without_client_time_inference(self):
        fixture = {
            "marketNews": {
                "schemaVersion": "fx-market-news-read-model-v2",
                "calendarDate": "2026-08-14",
                "currentBangkokDate": "2026-08-14",
                "reportBangkokDate": "2026-08-14",
                "dataStatus": "verified",
                "stale": False,
                "currentDataAvailable": True,
                "sources": [{"id": "official-cpi", "title": "Official CPI", "url": "https://example.com/official-cpi"}],
                "events": [
                    {
                        "eventId": "cpi-us",
                        "titleTh": "US CPI",
                        "summaryTh": "ผลเงินเฟ้อสหรัฐ",
                        "detailTh": "ตรวจผลจากแหล่งข้อมูลทางการ",
                        "scheduledAtUtc": "2026-08-14T12:30:00Z",
                        "timeKind": "timed",
                        "timingState": "past",
                        "releaseState": "released",
                        "actualStatus": "released",
                        "analysisStatus": "analyzed",
                        "currencies": ["USD"],
                        "impact": "high",
                        "actual": 0,
                        "forecast": "0.2%",
                        "previous": "0.1%",
                        "outcomeTh": "USD อ่อนกว่าคาด",
                        "sourceLinks": [{"id": "official-cpi", "url": "https://example.com/official-cpi"}],
                        "pairImpactComplete": True,
                        "pairImpactSnapshot": [
                            {"pair": pair, "impact": "bearish" if pair.endswith("USD") else "insufficient_data", "confidence": 0 if pair == "EURUSD" else None}
                            for pair in [
                                "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD",
                                "CADCHF", "CADJPY", "CHFJPY",
                                "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
                                "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
                                "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
                            ]
                        ],
                    },
                    {
                        "eventId": "jobs-us-awaiting",
                        "titleTh": "US Jobless Claims",
                        "summaryTh": "ผ่านเวลาประกาศแล้วแต่ Actual ยังไม่ยืนยัน",
                        "detailTh": "รอผลจากแหล่งข้อมูลทางการ",
                        "scheduledAtUtc": "2026-08-14T11:30:00Z",
                        "timeKind": "timed",
                        "timingState": "past",
                        "releaseState": "unconfirmed",
                        "actualStatus": "pending",
                        "analysisStatus": "awaiting_actual",
                        "currencies": ["USD"],
                        "impact": "medium",
                        "forecast": "230K",
                        "previous": "228K",
                        "sourceLinks": [{"id": "official-cpi", "url": "https://example.com/official-cpi"}],
                    },
                    {
                        "eventId": "holiday-jp",
                        "titleTh": "Japan Holiday",
                        "summaryTh": "วันหยุดตลาดญี่ปุ่น",
                        "timeKind": "holiday",
                        "timingState": "future",
                        "releaseState": "scheduled",
                        "actualStatus": "not_applicable",
                        "analysisStatus": "pending_release",
                        "currencies": ["JPY"],
                        "impact": "non_economic",
                        "sourceLinks": [{"id": "official-cpi", "url": "https://example.com/official-cpi"}],
                    },
                    {  # Stable duplicate identity must not render twice.
                        "eventId": "holiday-jp",
                        "titleTh": "Japan Holiday duplicate",
                        "timeKind": "holiday",
                        "timingState": "future",
                        "releaseState": "scheduled",
                    },
                ],
            }
        }
        pair_universe = [
            "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD", "CADCHF", "CADJPY", "CHFJPY",
            "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
            "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
            "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
        ]
        function_names = (
            "workflowDomainObject", "workflowDomainArray", "workflowReportRows", "normalizeFxBiasValue",
            "fxBiasHorizonValue", "normalizeFxFreshness", "workflowSourceLinkRows", "workflowItemSourceUrl",
            "isFxNewsReferenceOnlyUrl", "fxNewsVerifiedSourceLinks", "fxNewsVerifiedItemSources",
            "normalizeFxNewsImpact", "normalizeFxNewsMetric", "normalizeFxNewsPairImpactRows",
            "fxNewsCalendarRows", "normalizeFxNewsEvent", "deriveFxOverallBias",
            "normalizeFxPairAssessmentEvent", "normalizeFxPairAssessmentStatus",
            "deriveFxPairAssessmentSummary", "normalizeFxNewsScheduleTime", "normalizeFxNewsSchedule",
            "normalizeFxNewsHistoryItem", "normalizeFxNewsHistory", "normalizeFxNewsBiasDomain",
        )
        script = "\n".join([
            f"const FX_BIAS_PAIR_UNIVERSE = Object.freeze({json.dumps(pair_universe)});",
            "const safeDashboardDisplayText = (value, fallback = '') => String(value ?? '').trim() || fallback;",
            "const getSafeExternalHttpUrl = (value) => { try { const url = new URL(String(value || '')); return ['http:', 'https:'].includes(url.protocol) ? url.href : ''; } catch { return ''; } };",
            *(self.function_source(name) for name in function_names),
            self.function_source("fxNewsActualDisplay"),
            f"const fixture = {json.dumps(fixture, ensure_ascii=False)};",
            "const domain = normalizeFxNewsBiasDomain(fixture, {});",
            "const released = domain.releasedNews[0]; const upcoming = domain.upcomingNews[0];",
            "const unconfirmed = domain.unconfirmedNews[0];",
            "const pairAssessmentEvent = normalizeFxPairAssessmentEvent(fixture.marketNews.events[1]);",
            "const unavailableActual = {...unconfirmed,analysisStatus:'insufficient_data',actualStatus:'unavailable'};",
            "process.stdout.write(JSON.stringify({count: domain.news.length, released, upcoming, unconfirmed, pairAssessmentEvent, awaitingActualDisplay:fxNewsActualDisplay(unconfirmed), unavailableActualDisplay:fxNewsActualDisplay(unavailableActual), upcomingIds:domain.upcomingNews.map((item)=>item.id), unconfirmedIds:domain.unconfirmedNews.map((item)=>item.id)}));",
        ])
        result = self.run_node_script(script)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["count"], 3)
        self.assertEqual(payload["released"]["actual"], "0")
        self.assertEqual(payload["released"]["actualStatus"], "released")
        self.assertEqual(payload["released"]["eventAt"], "2026-08-14T12:30:00Z")
        self.assertFalse(payload["released"]["pairImpactComplete"])
        self.assertEqual(payload["released"]["pairImpactRows"][14]["confidence"], 0)
        self.assertIsNone(payload["released"]["pairImpactRows"][0]["confidence"])
        self.assertEqual(payload["upcoming"]["timeKind"], "holiday")
        self.assertEqual(payload["unconfirmed"]["id"], "jobs-us-awaiting")
        self.assertEqual(payload["unconfirmed"]["analysisStatus"], "awaiting_actual")
        self.assertEqual(payload["unconfirmed"]["releaseState"], "unconfirmed")
        self.assertEqual(payload["pairAssessmentEvent"]["analysisStatus"], "awaiting_actual")
        self.assertEqual(payload["awaitingActualDisplay"], "รอ Actual")
        self.assertEqual(payload["unavailableActualDisplay"], "ยังไม่ยืนยัน")
        self.assertNotIn("jobs-us-awaiting", payload["upcomingIds"])
        self.assertIn("jobs-us-awaiting", payload["unconfirmedIds"])
        self.assertIn('if (item.analysisStatus === "awaiting_actual") return "ผ่านเวลาแล้ว • รอ Actual";', self.main)
        self.assertIn("เวลาประกาศผ่านแล้ว แต่ยังไม่มีค่า Actual ที่ยืนยันจากแหล่งข้อมูล", self.main)

    def test_daily_news_dialog_and_original_calendar_ui_are_accessible(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="newsEventDialog" aria-labelledby="newsEventDetailTitle" aria-describedby="newsEventDetailIntro"', html)
        self.assertIn('id="newsEventDetailClose" type="button" aria-label="ปิดรายละเอียดข่าว"', html)
        self.assertIn('button.setAttribute("aria-haspopup", "dialog")', self.main)
        self.assertIn('els.newsEventDialog?.addEventListener("cancel"', self.main)
        self.assertIn('if (event.target === els.newsEventDialog) closeFxNewsEventDetail()', self.main)
        self.assertIn('if (newsEventShouldRestoreFocus) newsEventReturnFocus?.focus?.()', self.main)
        self.assertIn('els.dashboardResultDialog?.open || els.newsEventDialog?.open', self.main)
        self.assertIn("ปฏิทินข่าวเศรษฐกิจ", self.main)
        self.assertNotIn("Forex Factory feed", self.main)
        self.assertIn(".workflow-news-event-button:focus-visible", self.styles)
        self.assertIn(".news-event-dialog", self.styles)

    def test_daily_news_preserves_zoned_instants_and_rejects_naive_source_time(self):
        pair_universe = [
            "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD", "CADCHF", "CADJPY", "CHFJPY",
            "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
            "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
            "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
        ]
        function_names = (
            "workflowDomainArray", "normalizeFxBiasValue", "workflowSourceLinkRows", "workflowItemSourceUrl",
            "isFxNewsReferenceOnlyUrl", "fxNewsVerifiedSourceLinks", "fxNewsVerifiedItemSources",
            "normalizeFxNewsImpact", "normalizeFxNewsMetric", "normalizeFxNewsPairImpactRows", "normalizeFxNewsEvent",
        )
        events = [
            {"eventId": "ny-standard", "scheduledAtUtc": "2026-03-08T01:30:00-05:00"},
            {"eventId": "ny-daylight", "scheduledAtUtc": "2026-03-08T03:30:00-04:00"},
            {"eventId": "utc-plus-three", "scheduledAtUtc": "2026-08-14T22:00:00+03:00"},
            {"eventId": "naive", "scheduledAt": "2026-08-14T12:00:00"},
        ]
        for event in events:
            event.update({
                "titleTh": event["eventId"], "summaryTh": "verified", "currencies": ["USD"],
                "timeKind": "timed", "timingState": "future", "releaseState": "scheduled",
                "actualStatus": "pending", "analysisStatus": "pending_release",
                "sourceLinks": [{"id": "source", "url": "https://example.com/source"}],
            })
        script = "\n".join([
            f"const FX_BIAS_PAIR_UNIVERSE = Object.freeze({json.dumps(pair_universe)});",
            "const safeDashboardDisplayText = (value, fallback = '') => String(value ?? '').trim() || fallback;",
            "const getSafeExternalHttpUrl = (value) => { try { const url = new URL(String(value || '')); return ['http:', 'https:'].includes(url.protocol) ? url.href : ''; } catch { return ''; } };",
            *(self.function_source(name) for name in function_names),
            f"const events = {json.dumps(events, ensure_ascii=False)};",
            "const sources = [{id:'source',url:'https://example.com/source'}];",
            "const rows = events.map((event, index) => normalizeFxNewsEvent(event, index, sources));",
            "const parts = Object.fromEntries(new Intl.DateTimeFormat('en-US',{timeZone:'Asia/Bangkok',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(rows[2].eventAt)).map((part) => [part.type, part.value]));",
            "process.stdout.write(JSON.stringify({rows,bangkokDate:`${parts.year}-${parts.month}-${parts.day}`}));",
        ])
        result = self.run_node_script(script)
        payload = json.loads(result.stdout)
        rows = payload["rows"]
        self.assertEqual(rows[0]["eventAt"], "2026-03-08T01:30:00-05:00")
        self.assertEqual(rows[1]["eventAt"], "2026-03-08T03:30:00-04:00")
        self.assertEqual(rows[2]["eventAt"], "2026-08-14T22:00:00+03:00")
        self.assertEqual(payload["bangkokDate"], "2026-08-15")
        self.assertIsNone(rows[3]["eventAt"])
        self.assertTrue(all(row["releaseState"] == "scheduled" for row in rows))

    def test_daily_news_bangkok_formatter_is_independent_of_browser_timezone(self):
        formatter = self.function_source("fxNewsBangkokDateTimeLabel")
        self.assertIn('timeZone: "Asia/Bangkok"', formatter)
        script = "\n".join([
            formatter,
            "process.stdout.write(JSON.stringify([",
            "  fxNewsBangkokDateTimeLabel('2026-03-08T01:30:00-05:00'),",
            "  fxNewsBangkokDateTimeLabel('2026-08-14T22:00:00+03:00'),",
            "]));",
        ])
        outputs = []
        for timezone in ("UTC", "America/New_York"):
            result = subprocess.run(
                [self.node_binary(), "-e", script],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**__import__("os").environ, "TZ": timezone},
            )
            outputs.append(json.loads(result.stdout))
        self.assertEqual(outputs[0], outputs[1])
        self.assertNotEqual(outputs[0][0], outputs[0][1])

    def test_reference_only_or_legacy_news_cannot_authorize_events_or_pair_direction(self):
        fixture = {
            "marketNews": {
                "dataStatus": "verified",
                "currentDataAvailable": True,
                "stale": False,
                "sources": [{"id": "official", "url": "https://example.com/official-release"}],
                "events": [
                    {
                        "eventId": "unlinked", "titleTh": "Unlinked row", "summaryTh": "must be rejected",
                        "currencies": ["USD"], "releaseState": "released", "timingState": "past",
                        "sourceLinks": [{"id": "other", "url": "https://example.net/unverified"}],
                    },
                    {
                        "eventId": "official-row", "titleTh": "Verified row", "summaryTh": "kept",
                        "currencies": ["USD"], "releaseState": "released", "timingState": "past",
                        "sourceRefs": ["official"],
                    },
                ],
                "dangerWindows": [{
                    "windowId": "ff-danger", "reasonTh": "reference only must not authorize",
                    "currencies": ["USD"], "startsAt": "2026-08-14T12:00:00Z", "endsAt": "2026-08-14T13:00:00Z",
                    "sourceLinks": [{"id": "ff", "url": "https://nfs.faireconomy.media/ff_calendar_thisweek.json"}],
                }],
            },
            "fxBias": {
                "dataStatus": "verified",
                "currentDataAvailable": True,
                "stale": False,
                "sources": [{"id": "ff", "url": "https://www.forexfactory.com/calendar"}],
                "pairs": [{
                    "pair": "EURUSD", "status": "source_backed", "shortBias": "bullish",
                    "mediumBias": "bullish", "longBias": "bullish",
                    "sourceLinks": [{"id": "ff", "url": "https://www.forexfactory.com/calendar"}],
                }],
            },
        }
        verified_empty_fixture = {
            "marketNews": {
                "calendarDate": "2026-08-15",
                "currentBangkokDate": "2026-08-15",
                "reportBangkokDate": "2026-08-15",
                "dataStatus": "verified_empty",
                "verifiedEmpty": True,
                "emptyReasonTh": "verified holiday with no qualifying events",
                "currentDataAvailable": True,
                "stale": False,
                "sources": [{"id": "official", "url": "https://example.com/official-release"}],
                "events": [],
                "dangerWindows": [],
            }
        }
        pair_universe = [
            "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD", "CADCHF", "CADJPY", "CHFJPY",
            "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
            "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
            "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
        ]
        function_names = (
            "workflowDomainObject", "workflowDomainArray", "workflowReportRows", "normalizeFxBiasValue",
            "fxBiasHorizonValue", "normalizeFxFreshness", "workflowSourceLinkRows", "workflowItemSourceUrl",
            "isFxNewsReferenceOnlyUrl", "fxNewsVerifiedSourceLinks", "fxNewsVerifiedItemSources", "normalizeFxNewsImpact",
            "normalizeFxNewsMetric", "normalizeFxNewsPairImpactRows", "fxNewsCalendarRows",
            "normalizeFxNewsEvent", "deriveFxOverallBias", "normalizeFxPairAssessmentEvent",
            "normalizeFxPairAssessmentStatus", "deriveFxPairAssessmentSummary", "normalizeFxNewsScheduleTime",
            "normalizeFxNewsSchedule", "normalizeFxNewsHistoryItem", "normalizeFxNewsHistory", "normalizeFxNewsBiasDomain",
        )
        script = "\n".join([
            f"const FX_BIAS_PAIR_UNIVERSE = Object.freeze({json.dumps(pair_universe)});",
            "const safeDashboardDisplayText = (value, fallback = '') => String(value ?? '').trim() || fallback;",
            "const getSafeExternalHttpUrl = (value) => { try { const url = new URL(String(value || '')); return ['http:', 'https:'].includes(url.protocol) ? url.href : ''; } catch { return ''; } };",
            *(self.function_source(name) for name in function_names),
            f"const fixture = {json.dumps(fixture, ensure_ascii=False)};",
            f"const verifiedEmptyFixture = {json.dumps(verified_empty_fixture, ensure_ascii=False)};",
            "const domain = normalizeFxNewsBiasDomain(fixture, {});",
            "const emptyDomain = normalizeFxNewsBiasDomain(verifiedEmptyFixture, {});",
            "process.stdout.write(JSON.stringify({news:domain.news,dangerWindows:domain.dangerWindows,eurusd:domain.pairBias.find((row)=>row.pair==='EURUSD'),verifiedEmpty:emptyDomain.calendar.verifiedEmpty,emptyReason:emptyDomain.calendar.emptyReason,emptyNews:emptyDomain.news}));",
        ])
        result = self.run_node_script(script)
        payload = json.loads(result.stdout)
        self.assertEqual([row["id"] for row in payload["news"]], ["official-row"])
        self.assertEqual(payload["dangerWindows"], [])
        self.assertEqual(payload["eurusd"]["bias"], "unavailable")
        self.assertEqual(payload["eurusd"]["sourceUrl"], "")
        self.assertTrue(payload["verifiedEmpty"])
        self.assertEqual(payload["emptyReason"], "verified holiday with no qualifying events")
        self.assertEqual(payload["emptyNews"], [])

        listener = self.main[self.main.index('document.addEventListener("keydown"'):]
        self.assertLess(listener.index("els.newsEventDialog?.open"), listener.index("els.dashboardResultDialog?.open"))


if __name__ == "__main__":
    unittest.main()
