import importlib.util
import json
import re
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPATIBILITY_PATH = ROOT / "contracts" / "research" / "radar-website-tool-compatibility-v1.json"
ROLE_MAP_PATH = ROOT / "contracts" / "props" / "property-role-map.json"
PLUGIN_MAP_PATH = ROOT / "contracts" / "workflows" / "equipment-plugin-map.json"
REPORT_CONTRACT_PATH = ROOT / "contracts" / "reports" / "report-contract.json"
BRIDGE_PATH = ROOT / "backend" / "local-runner" / "bridge_server.py"
FRONTEND_PATH = ROOT / "frontend" / "src" / "app" / "main.js"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_bridge_module():
    spec = importlib.util.spec_from_file_location("radar_website_tool_bridge_test", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("bridge module unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RadarWebsiteToolCompatibilitySnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compatibility = load_json(COMPATIBILITY_PATH)

    def test_snapshot_identifies_exact_prop_plugin_and_two_main_tabs(self) -> None:
        contract = self.compatibility
        self.assertEqual(contract["schemaVersion"], "radar-website-tool-compatibility-v1")
        self.assertEqual(contract["propId"], "left_audit_crystals")
        self.assertEqual(contract["canonicalName"], "Radar Website Tool")
        self.assertEqual(contract["referencePlugin"]["skillId"], "metafx-online-system-scout")
        self.assertEqual(contract["referencePlugin"]["version"], "0.1.2")
        self.assertEqual(
            [tab["id"] for tab in contract["presentation"]["tabs"]],
            ["today", "seven_days"],
        )
        self.assertEqual(contract["presentation"]["historyIncludedInTabId"], "seven_days")
        self.assertEqual(
            contract["presentation"]["leftRailSections"][0]["fieldIds"],
            ["googleSheetUrlOrId", "enabled", "times"],
        )

    def test_snapshot_requires_indicator_ea_and_tool_rows_with_plugin_readiness_truth(self) -> None:
        entries = self.compatibility["entryContract"]
        self.assertEqual(entries["containerField"], "entries")
        self.assertEqual(entries["toolKinds"], ["indicator", "ea", "tool"])
        self.assertEqual(
            entries["eaReadinessStatuses"],
            ["ready", "needs_clarification", "not_ea_ready"],
        )
        self.assertTrue({
            "sourceTitle",
            "sourceUrl",
            "checkedAt",
            "eaReadiness",
            "missingRules",
            "sourceLimitations",
            "duplicateFingerprint",
            "duplicateStatus",
            "screenshot",
        }.issubset(entries["requiredFields"]))
        self.assertFalse(self.compatibility["sourceEvidence"]["inventedRulesAllowed"])
        self.assertTrue(self.compatibility["readinessTruth"]["backendAuthorityRequired"])

    def test_snapshot_keeps_deduplication_backend_owned_and_canonical(self) -> None:
        dedupe = self.compatibility["deduplicationTruth"]
        self.assertTrue(dedupe["backendAuthorityRequired"])
        self.assertEqual(dedupe["defaultStatus"], "unique")
        self.assertEqual(dedupe["statuses"], ["unique", "duplicate"])
        self.assertEqual(
            dedupe["fingerprintFields"],
            ["sourceUrl", "toolName", "platform", "version"],
        )
        self.assertTrue(dedupe["positiveStatusRequiresBackendFingerprint"])
        self.assertTrue(dedupe["frontendMayNotUpgradeStatus"])

    def test_snapshot_limits_schedule_to_two_and_google_sheet_url_is_not_a_credential(self) -> None:
        settings = self.compatibility["settings"]
        schedule = settings["schedule"]
        sheet = settings["googleSheetUrl"]
        self.assertEqual(schedule["maximumRunsPerDay"], 2)
        self.assertEqual(schedule["allowedRunsPerDayWhenEnabled"], [1, 2])
        self.assertEqual(schedule["timezone"], "Asia/Bangkok")
        self.assertEqual(sheet["fieldId"], "googleSheetUrlOrId")
        self.assertEqual(sheet["allowedHost"], "docs.google.com")
        self.assertEqual(sheet["requiredPathPrefix"], "/spreadsheets/d/")
        self.assertFalse(sheet["frontendCredentialsAccepted"])
        self.assertFalse(sheet["externalWriteDefault"])

    def test_snapshot_filters_only_checked_rows_and_never_invents_screenshots(self) -> None:
        filters = self.compatibility["filters"]
        screenshot = self.compatibility["screenshotEvidence"]
        self.assertEqual(filters["timestampField"], "checkedAt")
        self.assertEqual(filters["timezone"], "Asia/Bangkok")
        self.assertEqual(filters["sevenDays"]["days"], 7)
        self.assertFalse(filters["undatedEntriesVisibleInFilteredTabs"])
        self.assertFalse(filters["futureEntriesVisible"])
        self.assertTrue(screenshot["backendAttachmentOnly"])
        self.assertTrue(screenshot["sameOriginOnly"])
        self.assertFalse(screenshot["externalImageUrlsAllowed"])
        self.assertFalse(screenshot["fabricatedPlaceholderAllowed"])
        self.assertEqual(
            screenshot["unavailableShape"],
            {
                "available": False,
                "status": "not_available",
                "attachmentId": None,
                "artifactRef": None,
            },
        )
        self.assertTrue(screenshot["entryIdentityRequired"])
        self.assertFalse(screenshot["firstReportImageFallbackAllowed"])
        self.assertEqual(screenshot["workerAvailableTrueRequiresFields"], ["artifactRef"])
        self.assertEqual(screenshot["backendReadModelAvailableTrueRequiresFields"], ["attachmentId"])

    def test_snapshot_contains_no_secret_values_or_frontend_credential_fields(self) -> None:
        security = self.compatibility["security"]
        self.assertEqual(security["frontendAcceptedCredentialFields"], [])
        self.assertTrue(security["frontendIntentOnly"])
        self.assertTrue(security["backendOwnsResearchAndPersistence"])
        serialized = json.dumps(self.compatibility, ensure_ascii=False)
        for marker in ("Bearer ", "sk-", "sessionid=", "api_key=", "password="):
            self.assertNotIn(marker, serialized)


class RadarWebsiteToolProductionCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compatibility = load_json(COMPATIBILITY_PATH)
        cls.roles = load_json(ROLE_MAP_PATH)["properties"]
        cls.plugin_map = load_json(PLUGIN_MAP_PATH)
        cls.report_contract = load_json(REPORT_CONTRACT_PATH)["typed_report_schemas"]
        cls.frontend = FRONTEND_PATH.read_text(encoding="utf-8")
        cls.bridge = load_bridge_module()

    def test_prop_and_frontend_use_radar_name_and_target_tabs(self) -> None:
        role = self.roles["left_audit_crystals"]
        presentation_tabs = self.compatibility["presentation"]["tabs"]
        expected_backend_tabs = [tab["backendCanonicalId"] for tab in presentation_tabs]
        self.assertEqual(role["functionName"], "Radar Website Tool")
        self.assertEqual(role["displayTitle"], "Radar Website Tool")
        self.assertTrue({"discover_new_indicators", "save_indicator_scout_schedule"}.issubset(role["allowedDashboardActions"]))
        self.assertTrue(self.compatibility["migrationCompatibility"]["backendTabIdsMayRemainCanonical"])
        fallback_start = self.frontend.index("  left_audit_crystals: {", self.frontend.index("const WORKFLOW_DASHBOARD_FALLBACKS"))
        fallback_end = self.frontend.index("  left_signal_cube: {", fallback_start)
        fallback = self.frontend[fallback_start:fallback_end]
        self.assertIn('titleTh: "Radar Website Tool"', fallback)
        self.assertIn('id: "save_indicator_scout_schedule"', fallback)
        self.assertIn(
            f'const INDICATOR_SCOUT_PRESENTATION_TAB_IDS = Object.freeze({json.dumps(expected_backend_tabs)});',
            self.frontend,
        )
        normalize_start = self.frontend.index("function normalizeWorkflowDashboard")
        normalize_end = self.frontend.index("function renderWorkflowAction", normalize_start)
        normalize_block = self.frontend[normalize_start:normalize_end]
        # The variable must remain explicit, but the frontend may legitimately
        # reassign it for prop-specific projections, so do not couple this
        # compatibility test to const versus let.
        self.assertRegex(normalize_block, r"\b(?:const|let) presentationTabs\b")
        self.assertIn("INDICATOR_SCOUT_PRESENTATION_TAB_IDS.includes(tab.id)", normalize_block)
        self.assertIn('labelTh: tab.id === "discoveries"', normalize_block)
        self.assertIn("tabs: presentationTabs.length ? presentationTabs", normalize_block)

    def test_plugin_and_report_contract_expose_structured_truth_fields(self) -> None:
        required = set(self.compatibility["entryContract"]["requiredFields"])
        worker_required = set(self.compatibility["entryContract"]["workerRequiredFields"])
        backend_fields = set(self.compatibility["entryContract"]["backendComputedFields"])
        action = self.plugin_map["equipment"]["left_audit_crystals"]["actions"]["discover_new_indicators"]
        self.assertEqual(action["referencePluginSkillId"], "metafx-online-system-scout")
        self.assertEqual(action["referencePluginVersion"], "0.1.2")
        with self.subTest(contract="plugin_output_fields"):
            self.assertEqual(action["outputFields"], ["entries"])
            self.assertEqual(set(action["entryContract"]["workerRequiredFields"]), worker_required)
            self.assertEqual(set(action["entryContract"]["backendComputedFields"]), backend_fields)
            self.assertEqual(required, worker_required | backend_fields)
        with self.subTest(contract="plugin_evidence_required"):
            self.assertTrue({
                "source_url",
                "source_title",
                "checked_at",
                "ea_readiness",
                "public_availability_status",
            }.issubset(set(action["evidenceRequired"])))
        report = self.report_contract["indicator_scout_report"]
        envelope = report["workerOutputEnvelope"]
        self.assertEqual(envelope["contractFields"][0]["field"], "entries")
        self.assertEqual(set(envelope["workerRequiredFields"]), worker_required)
        self.assertEqual(set(envelope["backendComputedFields"]), backend_fields)
        self.assertIn("entries", report)
        exemplar = report["entries"][0]
        with self.subTest(contract="report_fields"):
            self.assertTrue(required.issubset(set(exemplar)))
        with self.subTest(contract="tool_kind_enum"):
            self.assertEqual(exemplar["toolKind"], "indicator|ea|tool")
        with self.subTest(contract="ea_readiness_enum"):
            self.assertEqual(exemplar["eaReadiness"], "ready|needs_clarification|not_ea_ready")
        with self.subTest(contract="report_truth_arrays"):
            self.assertIsInstance(exemplar["missingRules"], list)
            self.assertIsInstance(exemplar["sourceLimitations"], list)

    def test_backend_accepts_only_safe_public_source_urls(self) -> None:
        normalize = self.bridge._normalized_contract_public_url
        self.assertEqual(
            normalize("https://docs.google.com/spreadsheets/d/abc123/edit#gid=0"),
            "https://docs.google.com/spreadsheets/d/abc123/edit",
        )
        for unsafe in (
            "https://user:password@example.com/tool",
            "http://127.0.0.1/internal",
            "http://10.0.0.8/internal",
            "https://example.com/tool?token=secret",
            "file:///C:/secret.png",
        ):
            with self.subTest(unsafe=unsafe):
                self.assertIsNone(normalize(unsafe))

    def test_backend_schedule_settings_include_google_sheet_url_and_cap_times_at_two(self) -> None:
        action = self.bridge.DASHBOARD_WORKFLOW_ACTIONS["save_indicator_scout_schedule"]
        field_ids = {field["id"] for field in action["formFields"]}
        self.assertTrue({"enabled", "times", "googleSheetUrlOrId"}.issubset(field_ids))
        self.assertEqual(
            self.bridge._dashboard_schedule_times(
                {"times": ["06:00", "12:00", "18:00"]},
                ["09:00"],
                max_times=2,
            ),
            ["06:00", "12:00"],
        )
        defaults = self.bridge._default_dashboard_workflow_settings()
        self.assertEqual(defaults["indicatorScoutSchedule"]["timezone"], "Asia/Bangkok")
        sheet = self.bridge._dashboard_indicator_sheet_read_model(defaults)
        self.assertFalse(sheet["configured"])
        self.assertFalse(sheet["credentialsAcceptedByFrontend"])
        self.assertFalse(sheet["rawSheetIdExposed"])
        self.assertFalse(sheet["externalWriteEnabled"])

    def test_disconnected_sheet_and_screenshot_adapters_are_not_reported_ready(self) -> None:
        freshness = {
            name: self.bridge._connection_probe_freshness({})
            for name in ("bridge", "codexQuota", "metatrader")
        }
        cases = (
            ("google_sheets_config", "configuration_only_adapter_not_connected"),
            ("screenshot_adapter", "not_connected"),
        )
        for item_id, adapter_status in cases:
            with self.subTest(item_id=item_id):
                item = self.bridge._connection_item_status(
                    {
                        "id": item_id,
                        "labelTh": item_id,
                        "required": False,
                        "adapterStatus": adapter_status,
                    },
                    {},
                    {},
                    {},
                    False,
                    freshness,
                    {},
                )
                self.assertEqual(item["status"], "not_connected")
                self.assertEqual(item["adapterStatus"], adapter_status)
                self.assertNotIn("พร้อมใช้งานผ่าน Local Runner", item["detailTh"])

    def test_backend_filters_today_and_seven_days_without_undated_future_or_stale_rows(self) -> None:
        thai_tz = timezone(timedelta(hours=7))
        now = datetime(2026, 8, 12, 12, 0, tzinfo=thai_tz)

        def report(report_id: str, checked_at: str | None) -> dict:
            metrics = {
                "entries": [{
                    "toolName": f"Radar item {report_id}",
                    "toolKind": "indicator",
                    "platform": "mt5",
                    "version": "1.0",
                    "category": "trend",
                    "sourceUrl": f"https://example.com/{report_id}",
                    "checkedAt": checked_at,
                }],
            }
            if checked_at is not None:
                metrics["checkedAt"] = checked_at
            return {
                "id": report_id,
                "type": "indicator_scout_report",
                "linkedPropId": "left_audit_crystals",
                "workflowContext": {
                    "propId": "left_audit_crystals",
                    "actionId": "discover_new_indicators",
                },
                "metrics": metrics,
            }

        payload = self.bridge._radar_website_tool_read_model(
            [
                report("today", "2026-08-12T02:00:00Z"),
                report("six-days", "2026-08-06T02:00:00Z"),
                report("eight-days", "2026-08-04T02:00:00Z"),
                report("future", "2026-08-13T02:00:00Z"),
                report("undated", None),
            ],
            settings=self.bridge._default_dashboard_workflow_settings(),
            now_local=now,
        )
        self.assertEqual([item["reportId"] for item in payload["todayEntries"]], ["today"])
        self.assertEqual(
            {item["reportId"] for item in payload["sevenDayEntries"]},
            {"today", "six-days"},
        )
        self.assertEqual(payload["historyWindowDays"], 7)

    def test_backend_buckets_each_entry_by_its_checked_at_not_report_date(self) -> None:
        thai_tz = timezone(timedelta(hours=7))
        now = datetime(2026, 8, 12, 12, 0, tzinfo=thai_tz)
        report = {
            "id": "mixed-entry-dates",
            "type": "indicator_scout_report",
            "linkedPropId": "left_audit_crystals",
            "workflowContext": {
                "propId": "left_audit_crystals",
                "actionId": "discover_new_indicators",
            },
            "createdAt": "2026-08-12T02:00:00Z",
            "updatedAt": "2026-08-12T02:01:00Z",
            "metrics": {
                "entries": [
                    {
                        "toolName": label,
                        "toolKind": "indicator",
                        "platform": "mt5",
                        "version": "1.0",
                        "category": "trend",
                        "sourceUrl": f"https://example.com/{slug}",
                        "checkedAt": checked_at,
                    }
                    for label, slug, checked_at in (
                        ("Today item", "today-item", "2026-08-12T02:00:00Z"),
                        ("Yesterday item", "yesterday-item", "2026-08-11T02:00:00Z"),
                        ("Future item", "future-item", "2026-08-13T02:00:00Z"),
                    )
                ]
            },
        }
        payload = self.bridge._radar_website_tool_read_model(
            [report],
            settings=self.bridge._default_dashboard_workflow_settings(),
            now_local=now,
        )
        self.assertEqual(
            [item["toolName"] for item in payload["todayEntries"]],
            ["Today item"],
        )
        self.assertEqual(
            {item["toolName"] for item in payload["sevenDayEntries"]},
            {"Today item", "Yesterday item"},
        )
        self.assertEqual(payload["history7Days"][0]["runCount"], 1)

    def test_sheet_reference_and_tab_name_reject_secret_like_values(self) -> None:
        secret = "sk-" + ("a" * 40)
        with self.assertRaises(self.bridge.RequestError):
            self.bridge._normalize_google_sheet_reference(secret)

        action = self.bridge.DASHBOARD_WORKFLOW_ACTIONS["save_indicator_scout_schedule"]
        with self.assertRaises(self.bridge.RequestError):
            self.bridge._sanitize_dashboard_workflow_form(
                action,
                {
                    "enabled": False,
                    "times": ["09:00"],
                    "googleSheetTabName": f"api_key={secret}",
                },
            )

        sheet_id = "1AbCdEfGhIjKlMnOpQrStUvWxYz_987654321"
        read_model = self.bridge._dashboard_indicator_sheet_read_model({
            "indicatorScoutSheet": {
                "sheetId": sheet_id,
                "tabName": f"api_key={secret}",
            }
        })
        self.assertTrue(read_model["configured"])
        self.assertIsNone(read_model["tabName"])
        self.assertNotIn(secret, json.dumps(read_model, ensure_ascii=False))

    def test_backend_read_model_preserves_truth_fields_and_canonical_dedupe_status(self) -> None:
        thai_tz = timezone(timedelta(hours=7))
        now = datetime(2026, 8, 12, 12, 0, tzinfo=thai_tz)
        shared_entry = {
            "toolName": "Verified Trend Tool",
            "toolKind": "tool",
            "platform": "tradingview",
            "category": "trend",
            "version": "2.1",
            "summaryTh": "สรุปจากหน้าต้นทาง",
            "sourceTitle": "Public documentation",
            "sourceUrl": "https://example.com/tools/verified-trend",
            "publishedAt": "2026-08-10T00:00:00Z",
            "checkedAt": "2026-08-12T02:00:00Z",
            "verificationStatus": "partially_verified",
            "availability": "public",
            "eaReadiness": "needs_clarification",
            "missingRules": ["exit_rule"],
            "sourceLimitations": ["No tested performance evidence"],
        }
        reports = [
            {
                "id": report_id,
                "type": "indicator_scout_report",
                "linkedPropId": "left_audit_crystals",
                "workflowContext": {
                    "propId": "left_audit_crystals",
                    "actionId": "discover_new_indicators",
                },
                "updatedAt": updated_at,
                "metrics": {"checkedAt": checked_at, "entries": [dict(shared_entry, checkedAt=checked_at)]},
            }
            for report_id, checked_at, updated_at in (
                ("radar-first", "2026-08-11T02:00:00Z", "2026-08-11T02:01:00Z"),
                ("radar-second", "2026-08-12T02:00:00Z", "2026-08-12T02:01:00Z"),
            )
        ]
        payload = self.bridge._radar_website_tool_read_model(
            reports,
            settings=self.bridge._default_dashboard_workflow_settings(),
            now_local=now,
        )
        entries = payload["sevenDayEntries"]
        self.assertEqual(len(entries), 2)
        by_report = {entry["reportId"]: entry for entry in entries}
        first = by_report["radar-first"]
        second = by_report["radar-second"]
        for field in (
            "toolName",
            "toolKind",
            "sourceTitle",
            "sourceUrl",
            "checkedAt",
            "verificationStatus",
            "eaReadiness",
            "missingRules",
            "sourceLimitations",
            "duplicateFingerprint",
            "duplicateStatus",
        ):
            with self.subTest(field=field):
                self.assertIn(field, first)
        with self.subTest(field="duplicateStatus:first"):
            self.assertEqual(first["duplicateStatus"], "unique")
        with self.subTest(field="duplicateStatus:second"):
            self.assertEqual(second["duplicateStatus"], "duplicate")
        self.assertEqual(first["duplicateFingerprint"], second["duplicateFingerprint"])
        with self.subTest(field="missingRules:type"):
            self.assertIsInstance(first["missingRules"], list)
        with self.subTest(field="sourceLimitations:type"):
            self.assertIsInstance(first["sourceLimitations"], list)
        self.assertFalse(first["screenshotClaimAllowed"])
        self.assertEqual(first["screenshotStatus"], "not_available")

    def test_frontend_returns_today_and_seven_day_rows_from_checked_at(self) -> None:
        start = self.frontend.index("function indicatorScoutTimestamp")
        end = self.frontend.index("function normalizeFxBiasValue", start)
        block = self.frontend[start:end]
        for marker in (
            "item.checkedAt",
            'timeZone: "Asia/Bangkok"',
            "function filterIndicatorScoutToday",
            "function filterIndicatorScoutRollingSevenDays",
            "backend.radarWebsiteTool",
            "hasCanonicalTruth",
            "projectCanonicalRows(canonicalTodayRows)",
            "projectCanonicalRows(canonicalSevenDayRows)",
            "todayEntries",
            "sevenDayEntries",
        ):
            self.assertIn(marker, block)
        renderer_start = self.frontend.index("function renderIndicatorScoutPanel")
        renderer_end = self.frontend.index("function renderFxBiasTable", renderer_start)
        renderer = self.frontend[renderer_start:renderer_end]
        self.assertIn('const isToday = tabId === "discoveries"', renderer)
        self.assertIn("domain.todayEntries", renderer)
        self.assertIn("domain.sevenDayEntries", renderer)

    def test_frontend_screenshot_requires_same_origin_backend_attachment_and_no_placeholder(self) -> None:
        safe_start = self.frontend.index("function getSafeReportImageUrl")
        safe_end = self.frontend.index("function getSafeReportArtifactUrl", safe_start)
        safe_block = self.frontend[safe_start:safe_end]
        self.assertIn("parsed.origin !== window.location.origin", safe_block)
        self.assertIn("/api\\/reports\\/", safe_block)
        scout_start = self.frontend.index("function indicatorScoutSafeScreenshotUrl")
        scout_end = self.frontend.index("function indicatorScoutTimestamp", scout_start)
        scout_block = self.frontend[scout_start:scout_end]
        self.assertIn("screenshot.available === true", scout_block)
        self.assertIn("attachmentId", scout_block)
        self.assertIn("getSafeReportImageUrl", scout_block)
        self.assertNotIn("placehold.co", scout_block)
        self.assertNotIn("data:image", scout_block)

    def test_radar_frontend_action_fields_never_accept_credentials(self) -> None:
        forbidden = tuple(
            value.lower() for value in self.compatibility["security"]["forbiddenFieldNameFragments"]
        )
        action_ids = self.compatibility["migrationCompatibility"]["retainedActionIds"]
        for action_id in action_ids:
            action = self.bridge.DASHBOARD_WORKFLOW_ACTIONS[action_id]
            for field in action["formFields"]:
                normalized = re.sub(r"[^a-z0-9]", "", field["id"].lower())
                with self.subTest(action_id=action_id, field=field["id"]):
                    self.assertFalse(any(re.sub(r"[^a-z0-9]", "", token) in normalized for token in forbidden))


if __name__ == "__main__":
    unittest.main()
