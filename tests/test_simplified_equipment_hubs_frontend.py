import json
from pathlib import Path
import shutil
import subprocess
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

    def test_fx_default_presentation_is_28_pair_grid_without_history(self):
        self.assertIn('left_signal_cube: "ศูนย์แนวโน้ม 28 คู่เงินและข่าว Forex"', self.main)
        self.assertIn(
            'const FX_NEWS_BIAS_PRESENTATION_TAB_IDS = Object.freeze(["pair_bias", "today"]);',
            self.main,
        )
        normalize = self.main[
            self.main.index("function normalizeWorkflowDashboard("):
            self.main.index("function getWorkflowSelectedTab(")
        ]
        self.assertIn("FX_NEWS_BIAS_PRESENTATION_TAB_IDS", normalize)
        self.assertIn('labelTh: tab.id === "pair_bias" ? "แนวโน้ม 28 คู่เงิน" : "ข่าวและผลกระทบ"', normalize)
        self.assertIn("actionIds: []", normalize)
        self.assertNotIn('id: "history"', normalize[normalize.index("subject?.id === FX_NEWS_BIAS_PROP_ID"):])

        domain = self.function_block("normalizeFxNewsBiasDomain", "normalizeConnectionCenterDevice")
        self.assertIn("FX_BIAS_PAIR_UNIVERSE.map", domain)
        self.assertIn('summary: "รอข้อมูลจริงจาก Backend"', domain)
        panel = self.function_block("renderFxNewsBiasPanel", "renderTerminalOutputPanel")
        self.assertIn("renderFxBiasGrid(section, domain.pairBias)", panel)
        self.assertNotIn("renderWorkflowSourceCards", panel)

    def test_history_is_explicit_so_fx_news_and_status_tabs_never_become_history_by_position(self):
        render = self.function_block("renderWorkflowDashboard", "setWorkflowDashboardTab")
        self.assertIn(
            "const isHistoryTab = WORKFLOW_DASHBOARD_HISTORY_TAB_IDS.has(selectedTab?.id);",
            render,
        )
        self.assertNotIn("selectedTab?.id === dashboard.tabs.at(-1)?.id", render)
        self.assertIn("els.workflowResultsPanel.hidden = !isHistoryTab", render)

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

    def test_how_to_and_device_actions_live_in_left_rail(self):
        rail_actions = self.function_block("workflowRailActions", "createWorkflowUseGuideCard")
        self.assertIn("INDICATOR_SCOUT_RAIL_ACTION_IDS", rail_actions)
        self.assertIn("FX_NEWS_BIAS_RAIL_ACTION_IDS", rail_actions)
        self.assertIn("return [...actions]", rail_actions)
        guide = self.function_block("createWorkflowUseGuideCard", "renderWorkflowSettingsRail")
        self.assertIn('title.textContent = "ใช้งานอย่างไร"', guide)
        self.assertIn("สั่งวิเคราะห์หรือตั้งเวลาอัปเดตจากแถบด้านซ้ายนี้", guide)
        self.assertNotIn("สั่งวิเคราะห์หรือตั้งเวลาอัปเดตจากด้านล่าง", guide)
        self.assertIn("data", guide)
        settings = self.function_block("renderWorkflowSettingsRail", "getWorkflowHandoffReports")
        self.assertIn("workflowRailActions(subject, dashboard)", settings)
        self.assertIn("createWorkflowUseGuideCard(subject)", settings)
        self.assertIn("els.workflowSettingsRail.hidden = false", settings)

    def test_connection_guidance_points_to_the_central_hub_and_news_schedule_caps_two_times(self):
        self.assertNotIn("ตรวจการเชื่อมต่อด้านซ้าย", self.main)
        self.assertIn("เปิดศูนย์การเชื่อมต่ออุปกรณ์ HQ จากปุ่มด้านซ้าย", self.main)
        self.assertIn("เวลาที่ต้องการ สูงสุด 2 เวลา เช่น 07:00, 18:00", self.main)
        self.assertNotIn("เวลาที่ต้องการ เช่น 07:00, 13:00, 19:00", self.main)

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
            "deriveFxOverallBias",
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
        result = subprocess.run(
            [self.node_binary(), "-e", script],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
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
        self.assertEqual(payload["eurusd"]["bias"], "bullish")
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
        self.assertIn("renderFxBiasGrid(section, domain.pairBias)", panel)

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
            "deriveFxOverallBias",
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
        result = subprocess.run(
            [self.node_binary(), "-e", script],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        domain = json.loads(result.stdout)

        self.assertEqual(domain["freshness"]["marketNews"], {
            "asOf": "2026-08-12T01:00:00+07:00",
            "currentBangkokDate": "2026-08-12",
            "reportBangkokDate": "2026-08-11",
            "stale": True,
            "currentDataAvailable": False,
            "dataStatus": "stale",
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
        self.assertIn("ยังไม่มีข้อมูลของวันนี้", banner)
        self.assertIn("freshness?.stale !== true", banner)
        self.assertIn("freshness?.currentDataAvailable !== false", banner)
        self.assertIn("domain?.freshness?.marketNews", panel)
        self.assertIn("domain?.freshness?.fxBias", panel)


if __name__ == "__main__":
    unittest.main()
