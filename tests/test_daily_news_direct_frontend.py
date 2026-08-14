import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DailyNewsDirectFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main = (ROOT / "frontend" / "src" / "app" / "main.js").read_text(encoding="utf-8")

    def function_source(self, name: str) -> str:
        start = self.main.index(f"function {name}(")
        end = self.main.find("\nfunction ", start + 1)
        return self.main[start:] if end < 0 else self.main[start:end]

    def node_binary(self) -> str:
        candidates = [
            shutil.which("node"),
            str(Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "bin" / "node.exe"),
        ]
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                return candidate
        self.skipTest("Node.js is required for the frontend normalizer regression")

    def run_node(self, source: str) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "daily-news-direct-regression.js"
            script.write_text(source, encoding="utf-8")
            result = subprocess.run(
                [self.node_binary(), str(script)],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        return json.loads(result.stdout)

    def test_fx_rail_uses_only_dedicated_direct_endpoints_without_handoff_copy(self):
        fallback_start = self.main.index("  left_signal_cube: {", self.main.index("const WORKFLOW_DASHBOARD_FALLBACKS"))
        fallback_end = self.main.index("  terminal_workstation: {", fallback_start)
        fallback = self.main[fallback_start:fallback_end]
        self.assertNotIn("analyze_daily_market_news", fallback)
        self.assertNotIn("build_fx_pair_bias", fallback)
        self.assertIn("actions: []", fallback)

        schedule = self.function_source("saveFxNewsSchedule")
        refresh = self.function_source("refreshFxNewsDirect")
        rail = self.function_source("renderFxNewsSettingsRail")
        dashboard = self.function_source("renderWorkflowDashboard")
        self.assertIn("/news/schedule", schedule)
        self.assertIn("{\n      enabled,\n      times,\n    }", schedule)
        self.assertNotIn("/workflow/actions", schedule)
        self.assertNotIn("mergeBackendMission", schedule)
        self.assertIn("/news/refresh", refresh)
        self.assertIn("/news/refresh`, {}", refresh)
        self.assertIn("/^news_direct_refresh(?:_|$)/", refresh)
        self.assertLess(refresh.index("mergeFxNewsDirectResponse(response)"), refresh.index("const serviceStatus"))
        self.assertNotIn("/workflow/actions", refresh)
        self.assertNotIn("mergeBackendMission", refresh)
        for forbidden in ("Mission", "Agent", "อนุมัติ"):
            self.assertNotIn(forbidden, rail)
        self.assertIn("schedule.times.slice(0, 2)", rail)
        self.assertIn("service.sources", rail)
        self.assertIn("service.directRefreshAvailable === true", rail)
        self.assertIn("if (isFxNewsDashboard)", dashboard)
        self.assertIn("els.workflowAgentHandoffRail.hidden = true", dashboard)
        self.assertIn("if (!isFxNewsDashboard) renderWorkflowResults", dashboard)

    def test_schedule_defaults_and_requested_enabled_are_authoritative(self):
        source = "\n".join([
            self.function_source("workflowDomainArray"),
            self.function_source("normalizeFxNewsScheduleTime"),
            self.function_source("normalizeFxNewsSchedule"),
            "const safeDashboardDisplayText = (value, fallback = '') => String(value ?? '').trim() || fallback;",
            "const requestedOff = normalizeFxNewsSchedule({requestedEnabled:false,effectiveEnabled:true,enabled:true});",
            "const effectiveOn = normalizeFxNewsSchedule({effectiveEnabled:true});",
            "const supplied = normalizeFxNewsSchedule({requestedEnabled:true,times:['07:30','19:45','22:00']});",
            "process.stdout.write(JSON.stringify({requestedOff,effectiveOn,supplied}));",
        ])
        result = self.run_node(source)
        self.assertFalse(result["requestedOff"]["enabled"])
        self.assertEqual(result["requestedOff"]["times"], ["00:00", "12:00"])
        self.assertTrue(result["effectiveOn"]["enabled"])
        self.assertEqual(result["supplied"]["times"], ["07:30", "19:45"])
        self.assertEqual(result["supplied"]["timezone"], "Asia/Bangkok")

    def test_direct_history_day_preserves_clickable_verified_events_and_nullable_pair_counts(self):
        helpers = (
            "workflowDomainObject", "workflowDomainArray", "workflowSourceLinkRows",
            "isFxNewsReferenceOnlyUrl", "fxNewsVerifiedSourceLinks", "fxNewsVerifiedItemSources",
            "normalizeFxNewsImpact", "normalizeFxNewsMetric", "normalizeFxNewsPairImpactRows",
            "fxNewsCalendarRows", "normalizeFxNewsEvent", "normalizeFxBiasValue",
            "normalizeFxNewsHistoryItem",
        )
        source = "\n".join([
            "const FX_BIAS_PAIR_UNIVERSE = Object.freeze([]);",
            "const safeDashboardDisplayText = (value, fallback = '') => String(value ?? '').trim() || fallback;",
            "const getSafeExternalHttpUrl = (value) => { try { const url = new URL(String(value || '')); return ['http:', 'https:'].includes(url.protocol) ? url.href : ''; } catch { return ''; } };",
            *(self.function_source(name) for name in helpers),
            "const item = {marketDate:'2026-08-14',lastUpdatedAt:'2026-08-14T12:00:00Z',eventCount:2,events:[{eventId:'one',title:'Official release',publicationStatus:'published',actual:'3.1',forecast:'2.8',previous:'2.6',sourceLinks:[{id:'official-one',label:'Official source',url:'https://example.com/release'}]},{eventId:'two',title:'Upcoming release',publicationStatus:'scheduled',sourceLinks:[{id:'official-two',label:'Second source',url:'https://example.com/upcoming'}]}]};",
            "process.stdout.write(JSON.stringify(normalizeFxNewsHistoryItem(item)));",
        ])
        result = self.run_node(source)
        self.assertEqual(result["calendarDate"], "2026-08-14")
        self.assertEqual(result["updatedAt"], "2026-08-14T12:00:00Z")
        self.assertEqual(result["dataStatus"], "stored_history")
        self.assertEqual(result["eventCount"], 2)
        self.assertEqual(result["releasedCount"], 1)
        self.assertIsNone(result["assessedPairCount"])
        self.assertIsNone(result["directionalPairCount"])
        self.assertEqual([event["title"] for event in result["events"]], ["Official release", "Upcoming release"])
        self.assertEqual(result["events"][0]["actual"], "3.1")
        self.assertEqual(result["events"][0]["forecast"], "2.8")
        self.assertEqual(result["events"][0]["previous"], "2.6")
        self.assertEqual(result["events"][0]["sources"][0]["url"], "https://example.com/release")

        history_renderer = self.function_source("renderFxNewsHistory")
        event_card = self.function_source("createFxNewsEventCard")
        detail_modal = self.function_source("openFxNewsEventDetail")
        self.assertIn("createFxNewsEventCard(event)", history_renderer)
        self.assertIn("openFxNewsEventDetail(item, button)", event_card)
        for field in ("fxNewsActualDisplay(item)", "item.forecast", "item.previous", "item.sources"):
            self.assertIn(field, detail_modal)

    def test_partial_live_shape_keeps_informational_events_out_of_pair_relevance(self):
        pairs = "AUDCAD AUDCHF AUDJPY AUDNZD AUDUSD CADCHF CADJPY CHFJPY EURAUD EURCAD EURCHF EURGBP EURJPY EURNZD EURUSD GBPAUD GBPCAD GBPCHF GBPJPY GBPNZD GBPUSD NZDCAD NZDCHF NZDJPY NZDUSD USDCAD USDCHF USDJPY".split()
        helpers = (
            "workflowDomainObject", "workflowDomainArray", "workflowReportRows", "normalizeFxBiasValue",
            "fxBiasHorizonValue", "normalizeFxFreshness", "workflowSourceLinkRows", "workflowItemSourceUrl",
            "isFxNewsReferenceOnlyUrl", "fxNewsVerifiedSourceLinks", "fxNewsVerifiedItemSources",
            "normalizeFxNewsImpact", "normalizeFxNewsMetric", "normalizeFxNewsPairImpactRows",
            "fxNewsCalendarRows", "normalizeFxNewsEvent", "deriveFxOverallBias",
            "normalizeFxPairAssessmentEvent", "normalizeFxPairAssessmentStatus", "deriveFxPairAssessmentSummary",
            "normalizeFxNewsScheduleTime", "normalizeFxNewsSchedule", "normalizeFxNewsHistoryItem",
            "normalizeFxNewsHistory", "normalizeFxNewsBiasDomain",
        )
        fixture = {
            "marketNews": {
                "marketDate": "2026-08-14",
                "dataStatus": "degraded",
                "sourceStatus": "partial_success",
                "currentDataAvailable": True,
                "coverageCurrencies": ["AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "USD"],
                "failedCurrencies": ["NZD"],
                "sourceLinks": [
                    {"id": "official-aud", "url": "https://example.com/aud"},
                    {"id": "official-jpy", "url": "https://example.com/jpy"},
                ],
                "events": [
                    {
                        "eventId": "aud-publication",
                        "title": "RBA informational publication",
                        "currencies": ["AUD"],
                        "scheduledAt": "2026-08-14T02:00:00Z",
                        "marketDate": "2026-08-14",
                        "timeKind": "timed",
                        "impact": "low",
                        "eventCategory": "informational_publication",
                        "actionableMacro": False,
                        "publicationStatus": "published",
                        "actualStatus": "not_applicable",
                        "sourceRef": "official-aud",
                    },
                    {
                        "eventId": "jpy-publication",
                        "title": "BOJ informational publication",
                        "currencies": ["JPY"],
                        "scheduledAt": "2026-08-14T07:00:00Z",
                        "marketDate": "2026-08-14",
                        "timeKind": "timed",
                        "impact": "low",
                        "eventCategory": "informational_publication",
                        "actionableMacro": False,
                        "publicationStatus": "published",
                        "actualStatus": "not_applicable",
                        "sourceRef": "official-jpy",
                    },
                ],
            },
            "fxBias": {
                "marketDate": "2026-08-14",
                "dataStatus": "degraded",
                "sourceStatus": "partial_success",
                "currentDataAvailable": True,
                "coverageCurrencies": ["AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "USD"],
                "failedCurrencies": ["NZD"],
                "sourceLinks": [
                    {"id": "official-aud", "url": "https://example.com/aud"},
                    {"id": "official-jpy", "url": "https://example.com/jpy"},
                ],
                "pairBias": [{
                    "pair": pair,
                    "short": {"bias": "INSUFFICIENT_DATA", "sourceRefs": []},
                    "medium": {"bias": "INSUFFICIENT_DATA", "sourceRefs": []},
                    "long": {"bias": "INSUFFICIENT_DATA", "sourceRefs": []},
                    "verified": False,
                    "assessmentStatus": "unavailable" if "NZD" in pair else "no_direct_event",
                    "assessmentComplete": False if "NZD" in pair else True,
                    "relevantEventCount": 0,
                    "relevantEvents": [],
                } for pair in pairs],
            },
        }
        source = "\n".join([
            f"const FX_BIAS_PAIR_UNIVERSE = Object.freeze({json.dumps(pairs)});",
            "const safeDashboardDisplayText = (value, fallback = '') => String(value ?? '').trim() || fallback;",
            "const getSafeExternalHttpUrl = (value) => { try { const url = new URL(String(value || '')); return ['http:', 'https:'].includes(url.protocol) ? url.href : ''; } catch { return ''; } };",
            *(self.function_source(name) for name in helpers),
            f"const fixture = {json.dumps(fixture)};",
            "const domain = normalizeFxNewsBiasDomain(fixture, {});",
            "const failed = domain.pairBias.filter((row) => row.pair.includes('NZD'));",
            "const covered = domain.pairBias.filter((row) => !row.pair.includes('NZD'));",
            "process.stdout.write(JSON.stringify({calendar:domain.calendar,news:domain.news,summary:domain.pairAssessmentSummary,failed,covered,allBiases:domain.pairBias.map((row)=>row.bias)}));",
        ])
        result = self.run_node(source)
        self.assertEqual(result["calendar"]["date"], "2026-08-14")
        self.assertEqual(result["news"][0]["releaseState"], "released")
        self.assertEqual(result["summary"]["assessedPairCount"], 21)
        self.assertEqual(result["summary"]["unavailablePairCount"], 7)
        self.assertTrue(all(not row["assessmentComplete"] for row in result["failed"]))
        self.assertTrue(all(row["assessmentStatus"] == "unavailable" for row in result["failed"]))
        self.assertTrue(all(row["assessmentComplete"] for row in result["covered"]))
        self.assertTrue(all(row["assessmentStatus"] == "no_direct_event" for row in result["covered"]))
        self.assertTrue(all(row["relevantEventCount"] == 0 for row in result["covered"]))
        self.assertTrue(all(value == "unavailable" for value in result["allBiases"]))

    def test_history_prefers_one_canonical_row_per_market_date_over_legacy_reports(self):
        helpers = (
            "workflowDomainObject", "workflowDomainArray", "workflowSourceLinkRows",
            "isFxNewsReferenceOnlyUrl", "fxNewsVerifiedSourceLinks", "fxNewsVerifiedItemSources",
            "normalizeFxNewsImpact", "normalizeFxNewsMetric", "normalizeFxNewsPairImpactRows",
            "fxNewsCalendarRows", "normalizeFxNewsEvent", "normalizeFxBiasValue",
            "normalizeFxNewsHistoryItem", "normalizeFxNewsHistory",
        )
        canonical = [{
            "id": "canonical-day",
            "marketDate": "2026-08-14",
            "lastUpdatedAt": "2026-08-14T12:00:00Z",
            "events": [{
                "eventId": "canonical-event",
                "title": "Canonical official event",
                "publicationStatus": "published",
                "sourceLinks": [{
                    "id": "canonical-source",
                    "label": "Official source",
                    "url": "https://example.com/canonical",
                }],
            }],
        }]
        legacy = [{
            "id": f"legacy-{index}",
            "marketDate": "2026-08-14",
            "updatedAt": f"2026-08-14T{20 + index}:00:00Z",
            "events": [{
                "eventId": f"legacy-event-{index}",
                "title": f"Legacy event {index}",
                "publicationStatus": "published",
                "sourceLinks": [{
                    "id": f"legacy-source-{index}",
                    "label": "Legacy source",
                    "url": f"https://example.com/legacy-{index}",
                }],
            }],
        } for index in range(2)]
        source = "\n".join([
            "const FX_BIAS_PAIR_UNIVERSE = Object.freeze([]);",
            "const safeDashboardDisplayText = (value, fallback = '') => String(value ?? '').trim() || fallback;",
            "const getSafeExternalHttpUrl = (value) => { try { const url = new URL(String(value || '')); return ['http:', 'https:'].includes(url.protocol) ? url.href : ''; } catch { return ''; } };",
            *(self.function_source(name) for name in helpers),
            f"const canonical = {json.dumps(canonical)};",
            f"const legacy = {json.dumps(legacy)};",
            "process.stdout.write(JSON.stringify(normalizeFxNewsHistory(canonical, legacy)));",
        ])
        result = self.run_node(source)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["calendarDate"], "2026-08-14")
        self.assertEqual(result[0]["id"], "canonical-day")
        self.assertEqual([event["title"] for event in result[0]["events"]], ["Canonical official event"])

    def test_verified_empty_partial_and_failure_states_are_explicit(self):
        state_renderer = self.function_source("appendFxNewsBackendState")
        history_renderer = self.function_source("renderFxNewsHistory")
        for token in (
            "ตรวจสอบวันนี้แล้ว • ไม่มีข่าวตรง • ประเมินครบ 28/28",
            "ได้รับข้อมูลที่ยืนยันแล้วเพียงบางแหล่ง",
            "บริการข่าวหรือแหล่งข้อมูลยังไม่พร้อม",
            "กำลังดึงผลประเมิน 28 คู่เงิน",
        ):
            self.assertIn(token, state_renderer)
        self.assertIn("Backend ยังไม่มีประวัติอัปเดตรายวันให้แสดง", history_renderer)
        self.assertIn("historyDayCount", history_renderer)


if __name__ == "__main__":
    unittest.main()
