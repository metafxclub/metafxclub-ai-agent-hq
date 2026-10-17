from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "frontend" / "src" / "app" / "main.js"
CONTRACT_PATH = ROOT / "contracts" / "workflows" / "ea-factory-contract.json"


class EaFactorySheetDropdownFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main = MAIN_PATH.read_text(encoding="utf-8")
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def block(self, start: str, end: str) -> str:
        start_index = self.main.index(start)
        return self.main[start_index:self.main.index(end, start_index)]

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
            if candidate and Path(candidate).exists():
                return candidate
        self.fail("Node.js runtime is required")

    def test_catalog_helpers_preserve_exact_identity_and_invalidate_stale_imports(self) -> None:
        helpers = self.block(
            "function eaFactoryGoogleSheetCatalogRecords",
            "function stopEaFactoryGoogleSheetCatalogAutoRefresh",
        )
        harness = f"""
const EA_FACTORY_GOOGLE_SHEET_CATALOG_SCHEMA_VERSION = "ea-factory-deep-research-catalog-v1";
const EA_FACTORY_GOOGLE_SHEET_CATALOG_REFRESH_MS = 75000;
{helpers}
const sha = (character) => character.repeat(64);
const system = (recordId, systemName, sourceRecordId, digest, displayLabel = "") => ({{
  value: recordId,
  recordId,
  systemName,
  displayLabel,
  sourceRecordId,
  recordDigest: digest,
  buildReady: true,
}});
const catalog = {{
  schemaVersion: EA_FACTORY_GOOGLE_SHEET_CATALOG_SCHEMA_VERSION,
  status: "ready",
  inFlight: false,
  configRevision: 7,
  tabName: "Deep_Research",
  catalogDigest: sha("c"),
  snapshotDigest: sha("d"),
  totalCount: 3,
  systems: [
    system("deep-a", "Shared Name", "ea-source-a", sha("a")),
    system("deep-b", "Shared Name", "ea-source-b", sha("b")),
    system("deep-c", "Unique Name", "ea-source-c", sha("e")),
  ],
}};
const records = eaFactoryGoogleSheetCatalogRecords(catalog);
const importedFactory = {{
  sheetRecordId: "deep-a",
  selectedSourceId: "ea-source-a",
  importedSourceId: "ea-source-a",
  importedRecordDigest: sha("a"),
  importedCatalogDigest: sha("c"),
  importedSnapshotDigest: sha("d"),
}};
const keptFactory = {{ ...importedFactory }};
const kept = reconcileEaFactoryGoogleSheetSelection(catalog, keptFactory, [{{
  sourceRecordId: "ea-source-a",
  recordDigest: sha("a"),
}}]);
const refreshingCatalog = {{
  ...catalog,
  status: "refreshing",
  inFlight: true,
}};
const pendingFactory = {{ ...importedFactory }};
const pending = reconcileEaFactoryGoogleSheetSelection(
  refreshingCatalog,
  pendingFactory,
  [{{ sourceRecordId: "ea-source-a", recordDigest: sha("a") }}],
);
const unchangedAfterPending = reconcileEaFactoryGoogleSheetSelection(
  catalog,
  pendingFactory,
  [{{ sourceRecordId: "ea-source-a", recordDigest: sha("a") }}],
);
const changedCatalog = JSON.parse(JSON.stringify(catalog));
changedCatalog.systems[0].recordDigest = sha("f");
changedCatalog.catalogDigest = sha("1");
changedCatalog.snapshotDigest = sha("2");
const staleFactory = {{ ...importedFactory }};
const stale = reconcileEaFactoryGoogleSheetSelection(changedCatalog, staleFactory, [{{
  sourceRecordId: "ea-source-a",
  recordDigest: sha("f"),
}}]);
const removedCatalog = JSON.parse(JSON.stringify(catalog));
removedCatalog.systems = removedCatalog.systems.slice(1);
removedCatalog.totalCount = 2;
removedCatalog.catalogDigest = sha("3");
removedCatalog.snapshotDigest = sha("4");
const removedFactory = {{ ...importedFactory }};
const removed = reconcileEaFactoryGoogleSheetSelection(removedCatalog, removedFactory, []);
const blankNameCatalog = {{ ...catalog, totalCount: 1, systems: [
  system("deep-blank", "   ", "ea-source-blank", sha("6")),
] }};
const duplicateIdCatalog = {{ ...catalog, totalCount: 2, systems: [
  system("deep-dup", "First", "ea-source-first", sha("7")),
  system("DEEP-DUP", "Second", "ea-source-second", sha("8")),
] }};
const maxIdCatalog = {{ ...catalog, totalCount: 1, systems: [
  system("r".repeat(160), "Thai ID", "ea-source-max", sha("9")),
] }};
const overlongIdCatalog = {{ ...catalog, totalCount: 1, systems: [
  system("r".repeat(161), "Overlong ID", "ea-source-overlong", sha("5")),
] }};
const longNameCatalog = {{ ...catalog, totalCount: 1, systems: [
  system("deep-long-name", "ช".repeat(600), "ea-source-long-name", sha("4")),
] }};
const maxNameCatalog = {{ ...catalog, totalCount: 1, systems: [
  system("deep-max-name", "n".repeat(8000), "ea-source-max-name", sha("2")),
] }};
const overlongNameCatalog = {{ ...catalog, totalCount: 1, systems: [
  system("deep-overlong-name", "n".repeat(8001), "ea-source-overlong-name", sha("1")),
] }};
const controlIdCatalog = {{ ...catalog, totalCount: 1, systems: [
  system("deep-\u0085-bad", "Control ID", "ea-source-control", sha("0")),
] }};
const renamedCatalog = JSON.parse(JSON.stringify(catalog));
renamedCatalog.systems[2].systemName = "Renamed System";
console.log(JSON.stringify({{
  values: records.map((record) => record.value),
  labels: records.map((record) => record.label),
  kept,
  keptFactory,
  pending,
  pendingFactory,
  unchangedAfterPending,
  stale,
  staleFactory,
  removed,
  removedFactory,
  blankCount: eaFactoryGoogleSheetCatalogRecords(blankNameCatalog).length,
  duplicateCount: eaFactoryGoogleSheetCatalogRecords(duplicateIdCatalog).length,
  maxIdCount: eaFactoryGoogleSheetCatalogRecords(maxIdCatalog).length,
  overlongIdCount: eaFactoryGoogleSheetCatalogRecords(overlongIdCatalog).length,
  longNameLength: eaFactoryGoogleSheetCatalogRecords(longNameCatalog)[0]?.systemName.length || 0,
  maxNameLength: eaFactoryGoogleSheetCatalogRecords(maxNameCatalog)[0]?.systemName.length || 0,
  overlongNameCount: eaFactoryGoogleSheetCatalogRecords(overlongNameCatalog).length,
  controlIdCount: eaFactoryGoogleSheetCatalogRecords(controlIdCatalog).length,
  keyChangesOnRename: eaFactoryGoogleSheetCatalogKey(catalog) !== eaFactoryGoogleSheetCatalogKey(renamedCatalog),
}}));
"""
        completed = subprocess.run(
            [self.node_binary(), "-e", harness],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        result = json.loads(completed.stdout)

        self.assertEqual(result["values"], ["deep-a", "deep-b", "deep-c"])
        self.assertEqual(
            result["labels"],
            ["Shared Name — deep-a", "Shared Name — deep-b", "Unique Name"],
        )
        self.assertTrue(result["kept"]["imported"])
        self.assertEqual(result["keptFactory"]["importedSourceId"], "ea-source-a")
        self.assertTrue(result["pending"]["pending"])
        self.assertTrue(result["pending"]["imported"])
        self.assertEqual(result["pendingFactory"]["sheetRecordId"], "deep-a")
        self.assertEqual(result["pendingFactory"]["selectedSourceId"], "ea-source-a")
        self.assertEqual(result["pendingFactory"]["importedSourceId"], "ea-source-a")
        self.assertTrue(result["unchangedAfterPending"]["imported"])
        self.assertFalse(result["unchangedAfterPending"]["invalidated"])
        self.assertTrue(result["stale"]["invalidated"])
        self.assertFalse(result["stale"]["imported"])
        self.assertEqual(result["staleFactory"]["sheetRecordId"], "deep-a")
        self.assertEqual(result["staleFactory"]["selectedSourceId"], "")
        self.assertTrue(result["removed"]["selectionRemoved"])
        self.assertEqual(result["removedFactory"]["sheetRecordId"], "")
        self.assertEqual(result["blankCount"], 0)
        self.assertEqual(result["duplicateCount"], 0)
        self.assertEqual(result["maxIdCount"], 1)
        self.assertEqual(result["overlongIdCount"], 0)
        self.assertEqual(result["longNameLength"], 600)
        self.assertEqual(result["maxNameLength"], 8000)
        self.assertEqual(result["overlongNameCount"], 0)
        self.assertEqual(result["controlIdCount"], 0)
        self.assertTrue(result["keyChangesOnRename"])

        start_controls = self.block(
            "function renderEaFactoryStartControls",
            "function renderEaFactoryDiscoveryPreview",
        )
        self.assertIn("eaFactoryGoogleSheetCatalogIsFresh", start_controls)
        self.assertIn('reason: "start"', start_controls)
        self.assertIn("await ensureEaFactoryGoogleSheetCatalog", start_controls)
        self.assertIn("&& importBindingReady", start_controls)
        self.assertIn("submit.disabled = !canStart", start_controls)

    def test_catalog_scheduler_keeps_deadline_and_freshness_expires_before_start(self) -> None:
        helpers = self.block(
            "function stopEaFactoryGoogleSheetCatalogAutoRefresh",
            "function renderEaFactorySourceStage",
        )
        harness = f"""
const EA_FACTORY_GOOGLE_SHEET_CATALOG_REFRESH_MS = 75000;
const EA_FACTORY_GOOGLE_SHEET_CATALOG_INTERACTION_GRACE_MS = 5000;
const EA_FACTORY_GOOGLE_SHEET_CATALOG_SCHEMA_VERSION = "ea-factory-deep-research-catalog-v1";
const EA_FACTORY_PROP_ID = "right_server_racks";
let now = 1000;
Date.now = () => now;
let nextTimerId = 0;
const timers = new Map();
const window = {{
  setTimeout(callback, delay) {{
    const id = ++nextTimerId;
    timers.set(id, {{ callback, delay }});
    return id;
  }},
  clearTimeout(id) {{ timers.delete(id); }},
}};
const state = {{ modal: {{
  open: true,
  type: "prop",
  id: EA_FACTORY_PROP_ID,
  eaFactory: {{
    sourceMode: "google_sheet",
    inFlight: false,
    googleSheetCatalog: {{ status: "ready", inFlight: false, lastInteractionAt: 0 }},
  }},
}}, propReports: {{}} }};
const document = {{ activeElement: null }};
const els = {{ workflowDashboardContent: {{ contains() {{ return false; }} }} }};
let ensureCalls = 0;
async function ensureEaFactoryGoogleSheetCatalog() {{ ensureCalls += 1; }}
let eaFactoryGoogleSheetCatalogRefreshTimer = null;
let eaFactoryGoogleSheetCatalogRefreshDueAt = 0;
{helpers}
scheduleEaFactoryGoogleSheetCatalogAutoRefresh();
const firstTimerId = eaFactoryGoogleSheetCatalogRefreshTimer;
const firstDueAt = eaFactoryGoogleSheetCatalogRefreshDueAt;
now = 31000;
scheduleEaFactoryGoogleSheetCatalogAutoRefresh();
const timerAfterThirtySeconds = eaFactoryGoogleSheetCatalogRefreshTimer;
now = 61000;
scheduleEaFactoryGoogleSheetCatalogAutoRefresh();
const timerAfterSixtySeconds = eaFactoryGoogleSheetCatalogRefreshTimer;
const freshCatalog = {{
  schemaVersion: EA_FACTORY_GOOGLE_SHEET_CATALOG_SCHEMA_VERSION,
  status: "ready",
  inFlight: false,
  lastLoadedAt: 1000,
}};
const freshAt74999 = eaFactoryGoogleSheetCatalogIsFresh(freshCatalog, 75999);
const freshAt75000 = eaFactoryGoogleSheetCatalogIsFresh(freshCatalog, 76000);
now = firstDueAt;
timers.get(firstTimerId).callback();
console.log(JSON.stringify({{
  firstTimerId,
  timerAfterThirtySeconds,
  timerAfterSixtySeconds,
  firstDueAt,
  ensureCalls,
  dueAtAfterFire: eaFactoryGoogleSheetCatalogRefreshDueAt,
  freshAt74999,
  freshAt75000,
}}));
"""
        completed = subprocess.run(
            [self.node_binary(), "-e", harness],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["firstDueAt"], 76000)
        self.assertEqual(result["timerAfterThirtySeconds"], result["firstTimerId"])
        self.assertEqual(result["timerAfterSixtySeconds"], result["firstTimerId"])
        self.assertEqual(result["ensureCalls"], 1)
        self.assertEqual(result["dueAtAfterFire"], 0)
        self.assertTrue(result["freshAt74999"])
        self.assertFalse(result["freshAt75000"])

    def test_strategy_brief_preserves_6000_character_b_to_j_fields(self) -> None:
        sanitizer = self.block(
            "function safeDashboardDisplayText",
            "function safeAgentChatReplyText",
        )
        fields = self.block(
            "const TRADING_RESEARCH_STRATEGY_BRIEF_FIELDS",
            "const TRADING_RESEARCH_BLUEPRINT_SCHEMA_VERSION",
        )
        helpers = self.block(
            "function tradingResearchBlueprintObject",
            "function projectLegacyTradingResearchBlueprint",
        )
        harness = f"""
{sanitizer}
{fields}
{helpers}
const input = {{ record_id: "r".repeat(160) }};
TRADING_RESEARCH_STRATEGY_BRIEF_FIELDS.slice(1).forEach((field, index) => {{
  input[field.key] = String(index + 1).repeat(6000);
}});
const normalized = normalizeTradingResearchStrategyBrief(input);
console.log(JSON.stringify(Object.fromEntries(
  TRADING_RESEARCH_STRATEGY_BRIEF_FIELDS.map((field) => [field.key, normalized[field.key].length]),
)));
"""
        completed = subprocess.run(
            [self.node_binary(), "-e", harness],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        lengths = json.loads(completed.stdout)
        self.assertEqual(lengths["record_id"], 160)
        for field in (
            "system_name",
            "system_overview",
            "entry_rules",
            "recovery_rules",
            "exit_rules",
            "money_management",
            "order_execution",
            "display_requirements",
            "additional_notes",
        ):
            self.assertEqual(lengths[field], 6000, field)

    def test_dropdown_a11y_focus_reopen_and_invalidation_are_explicit(self) -> None:
        renderer = self.block(
            "function renderEaFactoryRecordImport",
            "function renderEaFactoryImportedSummary",
        )
        focus_helper = self.block(
            "function rerenderEaFactoryDashboardPreservingFocus",
            "function eaFactoryGoogleSheetCatalogUserIsEditing",
        )
        invalidation = self.block(
            "function surfaceEaFactoryGoogleSheetInvalidation",
            "function stopEaFactoryGoogleSheetCatalogAutoRefresh",
        )
        opener = self.block(
            "async function openPropDialog",
            "function setConnectionActionState",
        )
        merge = self.block(
            "function mergeEaFactoryReadModel",
            "function mergeEaFactoryResponseReport",
        )
        self.assertIn('label.htmlFor = "ea-factory-google-sheet-record"', renderer)
        self.assertIn('select.id = "ea-factory-google-sheet-record"', renderer)
        self.assertIn("form.append(label, row, help)", renderer)
        self.assertNotIn("label.appendChild(row)", renderer)
        self.assertIn('status.setAttribute("role", "status")', renderer)
        self.assertIn('status.setAttribute("aria-live", "polite")', renderer)
        self.assertIn('status.setAttribute("aria-atomic", "true")', renderer)
        self.assertIn("aria-describedby", renderer)
        self.assertIn("eaFactoryFocusKey", renderer)
        self.assertIn("document.activeElement?.dataset?.eaFactoryFocusKey", focus_helper)
        self.assertIn("nextControl?.focus?", focus_helper)
        self.assertIn("factory.message = message", invalidation)
        self.assertIn('factory.tone = "warning"', invalidation)
        self.assertIn("google_sheet_selection_removed", invalidation)
        self.assertIn("google_sheet_changed_after_import", invalidation)
        self.assertIn("google_sheet_selection_removed", merge)
        self.assertIn("google_sheet_changed_after_import", merge)
        self.assertIn('ensureEaFactoryGoogleSheetCatalog({ force: true, reason: "open" })', opener)

    def test_contract_declares_explicit_record_id_dropdown_and_refresh_semantics(self) -> None:
        google_sheet = self.contract["sourceContract"]["googleSheets"]
        self.assertEqual(google_sheet["tabName"], "Deep_Research")
        self.assertEqual(google_sheet["selectionMode"], "explicit_dropdown_record_id")
        self.assertEqual(google_sheet["optionLabelField"], "displayLabel")
        self.assertEqual(google_sheet["optionLabelFallbackField"], "system_name")
        self.assertEqual(google_sheet["optionValueField"], "record_id")
        self.assertFalse(google_sheet["automaticFirstSelectionAllowed"])
        self.assertTrue(google_sheet["refreshOnFactoryOpen"])
        self.assertTrue(google_sheet["manualRefreshAllowed"])
        self.assertTrue(google_sheet["automaticRefreshWhileOpen"])
        self.assertTrue(google_sheet["pauseAutomaticRefreshWhileUserEditing"])
        self.assertFalse(google_sheet["overlappingCatalogRequestsAllowed"])
        self.assertTrue(google_sheet["refreshAfterExternalSheetUpdate"])
        self.assertTrue(google_sheet["refreshImmediatelyAfterCentralSheetActivation"])
        self.assertTrue(google_sheet["cancelSupersededCatalogRequestOnActivation"])
        self.assertTrue(google_sheet["clearStaleSelectionOnCatalogChange"])
        self.assertEqual(
            google_sheet["catalogCacheBindingFields"],
            [
                "sheetId",
                "sheetDigest",
                "configRevision",
                "activationConfirmedAt",
                "tabName",
                "authBinding",
            ],
        )
        self.assertEqual(
            google_sheet["reconcileBindingFields"],
            [
                "recordId",
                "sourceRecordId",
                "recordDigest",
                "catalogDigest",
                "snapshotDigest",
                "configRevision",
            ],
        )
        self.assertEqual(
            google_sheet["createBuildBindingFields"],
            google_sheet["reconcileBindingFields"],
        )
        self.assertTrue(google_sheet["createBuildBindingAtomic"])
        self.assertEqual(google_sheet["staleCreateStatus"], 409)
        self.assertEqual(google_sheet["postImportView"], "strategy_brief_summary")
        self.assertEqual(google_sheet["frontendRequiredIntentFields"], ["configRevision"])
        self.assertEqual(google_sheet["frontendOptionalIntentFields"], ["idempotencyKey"])
        self.assertEqual(
            google_sheet["summaryFields"],
            [
                "record_id",
                "system_name",
                "system_overview",
                "entry_rules",
                "recovery_rules",
                "exit_rules",
                "money_management",
                "order_execution",
                "display_requirements",
                "additional_notes",
            ],
        )
        self.assertEqual(google_sheet["failureMode"], "fail_closed_empty_catalog")

    def test_dropdown_uses_system_name_labels_and_exact_record_id_values(self) -> None:
        renderer = self.block(
            "function renderEaFactoryRecordImport",
            "function renderEaFactoryImportedSummary",
        )
        self.assertIn('document.createElement("select")', renderer)
        self.assertNotIn('document.createElement("input")', renderer)
        self.assertIn("recordId", renderer)
        self.assertIn("sourceRecordId", renderer)
        self.assertRegex(renderer, r"option\.value\s*=\s*(?:item|record|entry|source)\.recordId")
        self.assertRegex(renderer, r"option\.textContent\s*=\s*(?:item|record|entry|source)\.(?:label|systemName)")
        self.assertIn("Import ข้อมูล", renderer)
        self.assertIn("Deep_Research", renderer)

    def test_catalog_helpers_are_bound_to_verified_sheet_records_and_catalog_revision(self) -> None:
        catalog = self.block(
            "function eaFactoryGoogleSheetCatalogRecords",
            "function eaFactoryGoogleSheetCatalogKey",
        )
        key = self.block(
            "function eaFactoryGoogleSheetCatalogKey",
            "function reconcileEaFactoryGoogleSheetSelection",
        )
        self.assertIn("verified_deep_research_sheet", catalog)
        self.assertIn("sourceRecordId", catalog)
        self.assertIn("recordId", catalog)
        self.assertIn("systemName", catalog)
        self.assertIn("briefDigest", key)
        self.assertIn("systemName", key)
        self.assertIn("recordId", key)
        self.assertIn("sourceRecordId", key)

    def test_refresh_reconciles_missing_or_changed_selection_without_using_first_row(self) -> None:
        reconcile = self.block(
            "function reconcileEaFactoryGoogleSheetSelection",
            "function renderEaFactorySourceStage",
        )
        merge = self.block(
            "function mergeEaFactoryReadModel",
            "function mergeEaFactoryResponseReport",
        )
        self.assertIn("sheetRecordId", reconcile)
        self.assertIn("selectedSourceId", reconcile)
        self.assertIn("importedSourceId", reconcile)
        self.assertIn("importedRecordDigest", reconcile)
        self.assertIn("importedCatalogDigest", reconcile)
        self.assertIn("importedSnapshotDigest", reconcile)
        self.assertIn('= ""', reconcile)
        self.assertNotRegex(reconcile, r"records\s*\[\s*0\s*\]")
        self.assertIn("reconcileEaFactoryGoogleSheetSelection", merge)

    def test_import_switches_to_summary_and_renders_every_deep_research_field(self) -> None:
        importer = self.block(
            "async function importEaFactorySourceRecord",
            "async function createEaFactoryBuild",
        )
        summary = self.block(
            "function renderEaFactoryImportedSummary",
            "function renderEaFactoryStartControls",
        )
        self.assertIn("selectedSourceId = source.sourceRecordId", importer)
        self.assertIn("importedSourceId = source.sourceRecordId", importer)
        self.assertIn(
            "await syncEaFactoryGoogleSheet(currentCatalog.configRevision)",
            importer,
        )
        self.assertIn("await ensureEaFactoryGoogleSheetCatalog", importer)
        self.assertIn("importedRecordDigest = refreshedCatalogRecord.recordDigest", importer)
        self.assertIn("renderEaFactoryImportedSummary", self.block(
            "function renderEaFactoryRecordImport",
            "function renderEaFactoryStartControls",
        ))
        for field in (
            "record_id",
            "system_name",
            "system_overview",
            "entry_rules",
            "recovery_rules",
            "exit_rules",
            "money_management",
            "order_execution",
            "display_requirements",
            "additional_notes",
        ):
            self.assertIn(field, summary)
        self.assertLess(
            summary.index("createTradingResearchStrategyBrief"),
            summary.index("renderEaFactoryStartControls"),
        )
        brief_renderer = self.block(
            "function createTradingResearchStrategyBrief",
            "function createTradingResearchSourceSnapshot",
        )
        self.assertIn('field.key === "record_id" ? 160 : 8000', brief_renderer)
        self.assertIn("กลับไปเลือกระบบ", summary)

    def test_create_build_posts_the_complete_imported_sheet_precondition(self) -> None:
        helpers = self.block(
            "function eaFactoryGoogleSheetCatalogRecords",
            "function rerenderEaFactoryDashboardPreservingFocus",
        )
        harness = f"""
const EA_FACTORY_GOOGLE_SHEET_CATALOG_SCHEMA_VERSION = "ea-factory-deep-research-catalog-v1";
const EA_FACTORY_GOOGLE_SHEET_CATALOG_REFRESH_MS = 75000;
{helpers}
const sha = (character) => character.repeat(64);
const catalog = {{
  schemaVersion: EA_FACTORY_GOOGLE_SHEET_CATALOG_SCHEMA_VERSION,
  status: "ready",
  inFlight: false,
  lastLoadedAt: Date.now(),
  configRevision: 7,
  tabName: "Deep_Research",
  catalogDigest: sha("c"),
  snapshotDigest: sha("d"),
  totalCount: 1,
  systems: [{{
    value: "deep-a",
    recordId: "deep-a",
    systemName: "System A",
    displayLabel: "System A",
    sourceRecordId: "ea-source-a",
    recordDigest: sha("a"),
    buildReady: true,
  }}],
}};
const factory = {{
  importedSourceId: "ea-source-a",
  importedRecordDigest: sha("a"),
  importedCatalogDigest: sha("c"),
  importedSnapshotDigest: sha("d"),
}};
const sheetSource = {{
  sourceKind: "verified_deep_research_sheet",
  recordId: "deep-a",
  sourceRecordId: "ea-source-a",
  recordDigest: sha("a"),
}};
const nonSheetSource = {{
  ...sheetSource,
  sourceKind: "verified_deep_research",
}};
const staleFactory = {{ ...factory, importedRecordDigest: sha("e") }};
console.log(JSON.stringify({{
  sheet: eaFactoryCreateSourceBinding(sheetSource, catalog, factory),
  staleSheet: eaFactoryCreateSourceBinding(sheetSource, catalog, staleFactory),
  nonSheet: eaFactoryCreateSourceBinding(nonSheetSource, {{}}, {{}}),
}}));
"""
        completed = subprocess.run(
            [self.node_binary(), "-e", harness],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        binding = json.loads(completed.stdout)
        self.assertTrue(binding["sheet"]["required"])
        self.assertTrue(binding["sheet"]["ready"])
        self.assertEqual(
            binding["sheet"]["fields"],
            {
                "recordId": "deep-a",
                "recordDigest": "a" * 64,
                "catalogDigest": "c" * 64,
                "snapshotDigest": "d" * 64,
                "configRevision": 7,
            },
        )
        self.assertTrue(binding["staleSheet"]["required"])
        self.assertFalse(binding["staleSheet"]["ready"])
        self.assertEqual(binding["staleSheet"]["fields"], {})
        self.assertFalse(binding["nonSheet"]["required"])
        self.assertTrue(binding["nonSheet"]["ready"])
        self.assertEqual(binding["nonSheet"]["fields"], {})

        create = self.block(
            "async function createEaFactoryBuild",
            "function eaFactoryOneClickRequestKey",
        )
        one_click = self.block(
            "async function createAndRunEaFactoryBuild",
            "async function advanceEaFactoryStage",
        )
        self.assertIn("eaFactoryCreateSourceBinding", create)
        self.assertIn("|| !sourceBinding.ready", create)
        self.assertIn("...(sourceBinding.required ? sourceBinding.fields : {})", create)
        self.assertIn("postEaFactoryJson", create)
        self.assertIn("requestPayload", create)
        self.assertIn("const created = await createEaFactoryBuild", one_click)

        expected_binding = [
            "recordId",
            "sourceRecordId",
            "recordDigest",
            "catalogDigest",
            "snapshotDigest",
            "configRevision",
        ]
        self.assertEqual(
            self.contract["sourceContract"]["googleSheets"]["createBuildBindingFields"],
            expected_binding,
        )
        for field in expected_binding:
            self.assertIn(field, self.contract["api"]["createBuildFields"])

    def test_create_build_reuses_key_after_lost_response_and_rotates_safely(self) -> None:
        helpers = self.block(
            "function eaFactoryCreateBuildFormSignature",
            "async function createEaFactoryBuild",
        )
        harness = f"""
const state = {{ modal: {{ eaFactory: {{
  createIdempotencyKey: "",
  createFormSignature: "",
}} }} }};
let keyCount = 0;
function createWorkflowIdempotencyKey() {{
  keyCount += 1;
  return `workflow-create-key-${{keyCount}}`;
}}
{helpers}
const sha = (character) => character.repeat(64);
const request = {{
  sourceRecordId: "ea-source-a",
  artifactKind: "expert_advisor",
  platform: "mt5",
  brief: "keep   risk\\nfixed",
  recordId: "deep-a",
  recordDigest: sha("a"),
  catalogDigest: sha("b"),
  snapshotDigest: sha("c"),
  configRevision: 7,
}};
const first = eaFactoryCreateBuildRequestIdentity(request);
// A timeout/lost response leaves the identity untouched. Retrying the same
// backend-normalized form, including whitespace-only changes, must reuse it.
const retry = eaFactoryCreateBuildRequestIdentity({{
  ...request,
  brief: "  keep risk fixed  ",
}});
completeEaFactoryCreateBuildRequest(first);
const afterSuccess = eaFactoryCreateBuildRequestIdentity(request);
const changedBinding = eaFactoryCreateBuildRequestIdentity({{
  ...request,
  recordDigest: sha("d"),
}});
completeEaFactoryCreateBuildRequest(afterSuccess);
console.log(JSON.stringify({{
  first,
  retry,
  afterSuccess,
  changedBinding,
  retainedAfterStaleCompletion: state.modal.eaFactory.createIdempotencyKey,
  keyCount,
}}));
"""
        completed = subprocess.run(
            [self.node_binary(), "-e", harness],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        result = json.loads(completed.stdout)
        self.assertEqual(
            result["first"]["idempotencyKey"],
            result["retry"]["idempotencyKey"],
        )
        self.assertEqual(result["first"]["formSignature"], result["retry"]["formSignature"])
        self.assertNotEqual(
            result["afterSuccess"]["idempotencyKey"],
            result["first"]["idempotencyKey"],
        )
        self.assertNotEqual(
            result["changedBinding"]["idempotencyKey"],
            result["afterSuccess"]["idempotencyKey"],
        )
        self.assertEqual(
            result["retainedAfterStaleCompletion"],
            result["changedBinding"]["idempotencyKey"],
        )
        self.assertEqual(result["keyCount"], 3)

        create = self.block(
            "async function createEaFactoryBuild",
            "function eaFactoryOneClickRequestKey",
        )
        self.assertIn("eaFactoryCreateBuildRequestIdentity(requestPayload)", create)
        self.assertIn("requestPayload.idempotencyKey = createIdentity.idempotencyKey", create)
        self.assertIn("completeEaFactoryCreateBuildRequest(createIdentity)", create)

    def test_sheet_sync_posts_the_selected_catalog_revision(self) -> None:
        sync = self.block(
            "async function syncEaFactoryGoogleSheet",
            "function normalizeEaFactoryGoogleSheetCatalog",
        )
        importer = self.block(
            "async function importEaFactorySourceRecord",
            "function eaFactoryCreateBuildFormSignature",
        )
        legacy_sync = self.block(
            "function renderEaFactoryGoogleSheetSync",
            "function renderEaFactoryResearchGate",
        )
        self.assertIn("Number.isInteger(normalizedConfigRevision)", sync)
        self.assertIn("configRevision: normalizedConfigRevision", sync)
        self.assertIn(
            "syncEaFactoryGoogleSheet(currentCatalog.configRevision)",
            importer,
        )
        self.assertIn("syncEaFactoryGoogleSheet(hub?.configRevision)", legacy_sync)

    def test_activation_supersedes_inflight_catalog_and_forces_open_factory_refresh(self) -> None:
        activate = self.block(
            "async function activateResearchSheetHub",
            "function normalizeOperatorModePayload",
        )
        invalidate = self.block(
            "function invalidateEaFactoryGoogleSheetCatalogAfterActivation",
            "function eaFactoryGoogleSheetCatalogIsFresh",
        )
        ensure = self.block(
            "async function ensureEaFactoryGoogleSheetCatalog",
            "async function importEaFactorySourceRecord",
        )
        self.assertIn(
            "void invalidateEaFactoryGoogleSheetCatalogAfterActivation()",
            activate,
        )
        self.assertIn("eaFactoryGoogleSheetCatalogAbortController.abort()", invalidate)
        self.assertIn("eaFactoryGoogleSheetCatalogInFlight = null", invalidate)
        self.assertIn('sheetRecordId = ""', invalidate)
        self.assertIn('importedSourceId = ""', invalidate)
        self.assertIn('systems: []', invalidate)
        self.assertIn(
            'ensureEaFactoryGoogleSheetCatalog({ force: true, reason: "activation" })',
            invalidate,
        )
        self.assertIn("signal: abortController.signal", ensure)

        harness = f"""
const EA_FACTORY_PROP_ID = "right_server_racks";
const EA_FACTORY_GOOGLE_SHEET_CATALOG_ENDPOINT = "/catalog";
const EA_FACTORY_ACTION_TIMEOUT_MS = 45000;
const EA_FACTORY_GOOGLE_SHEET_CATALOG_SCHEMA_VERSION = "ea-factory-deep-research-catalog-v1";
let eaFactoryGoogleSheetCatalogInFlight = null;
let eaFactoryGoogleSheetCatalogAbortController = null;
let eaFactoryGoogleSheetCatalogRefreshTimer = null;
let eaFactoryGoogleSheetCatalogRefreshDueAt = 0;
const oldSystem = {{ recordId: "old-record" }};
const state = {{
  modal: {{
    open: true,
    type: "prop",
    id: EA_FACTORY_PROP_ID,
    eaFactory: {{
      sourceMode: "google_sheet",
      sheetRecordId: "old-record",
      selectedSourceId: "old-source",
      importedSourceId: "old-source",
      importedRecordDigest: "old-record-digest",
      importedCatalogDigest: "old-catalog-digest",
      importedSnapshotDigest: "old-snapshot-digest",
      inFlight: false,
      googleSheetCatalog: {{
        schemaVersion: EA_FACTORY_GOOGLE_SHEET_CATALOG_SCHEMA_VERSION,
        status: "ready",
        configRevision: 1,
        systems: [oldSystem],
        totalCount: 1,
        inFlight: false,
        requestId: 9,
        lastLoadedAt: 1,
        lastInteractionAt: 2,
      }},
    }},
  }},
  propReports: {{}},
}};
const deferred = [];
function fetchJson(path, options) {{
  let resolve;
  const promise = new Promise((done) => {{ resolve = done; }});
  deferred.push({{ path, options, resolve }});
  return promise;
}}
function stopEaFactoryGoogleSheetCatalogAutoRefresh() {{
  eaFactoryGoogleSheetCatalogRefreshTimer = null;
  eaFactoryGoogleSheetCatalogRefreshDueAt = 0;
}}
function eaFactoryGoogleSheetCatalogIsFresh() {{ return false; }}
function rerenderEaFactoryGoogleSheetCatalog() {{}}
function scheduleEaFactoryGoogleSheetCatalogAutoRefresh() {{}}
function normalizeEaFactoryGoogleSheetCatalog(payload) {{ return payload.catalog; }}
function normalizeWorkflowDashboard() {{
  return {{ domainData: {{ eaFactory: {{ sourceCatalog: {{ records: [] }} }} }} }};
}}
function getModalSubject() {{ return {{}}; }}
function getPropertyRole() {{ return {{}}; }}
function reconcileEaFactoryGoogleSheetSelection() {{ return {{}}; }}
function surfaceEaFactoryGoogleSheetInvalidation() {{}}
function safeDashboardDisplayText(value, fallback) {{ return String(value || fallback || ""); }}
{invalidate}
{ensure}
const catalog = (configRevision, recordId) => ({{
  schemaVersion: EA_FACTORY_GOOGLE_SHEET_CATALOG_SCHEMA_VERSION,
  status: "ready",
  configRevision,
  tabName: "Deep_Research",
  catalogDigest: `${{configRevision}}`.repeat(64).slice(0, 64),
  snapshotDigest: `${{configRevision + 1}}`.repeat(64).slice(0, 64),
  observedAt: null,
  totalCount: 1,
  systems: [{{ recordId }}],
  selectedRecord: null,
  reasonCode: "",
  message: "ready",
}});
(async () => {{
  const staleRequest = ensureEaFactoryGoogleSheetCatalog({{ force: true, reason: "auto" }});
  const staleSignal = deferred[0].options.signal;
  const activatedRequest = invalidateEaFactoryGoogleSheetCatalogAfterActivation();
  const immediate = {{
    fetchCount: deferred.length,
    staleSignalAborted: staleSignal.aborted,
    catalog: {{ ...state.modal.eaFactory.googleSheetCatalog }},
    sheetRecordId: state.modal.eaFactory.sheetRecordId,
    selectedSourceId: state.modal.eaFactory.selectedSourceId,
    importedSourceId: state.modal.eaFactory.importedSourceId,
    importedRecordDigest: state.modal.eaFactory.importedRecordDigest,
    importedCatalogDigest: state.modal.eaFactory.importedCatalogDigest,
    importedSnapshotDigest: state.modal.eaFactory.importedSnapshotDigest,
  }};
  deferred[1].resolve({{ ok: true, catalog: catalog(22, "new-record") }});
  await activatedRequest;
  const afterFresh = JSON.parse(JSON.stringify(state.modal.eaFactory.googleSheetCatalog));
  // The transport intentionally ignores AbortSignal so this proves the
  // requestId generation guard also rejects a late stale success.
  deferred[0].resolve({{ ok: true, catalog: catalog(1, "old-record") }});
  const staleResult = await staleRequest;
  const afterStale = JSON.parse(JSON.stringify(state.modal.eaFactory.googleSheetCatalog));
  state.modal.open = false;
  state.modal.eaFactory.sourceMode = "discovery";
  state.modal.eaFactory.selectedSourceId = "discovery-source";
  const closedResult = invalidateEaFactoryGoogleSheetCatalogAfterActivation();
  console.log(JSON.stringify({{
    immediate,
    afterFresh,
    afterStale,
    staleResult,
    closedResult,
    finalFetchCount: deferred.length,
    nonSheetSelection: state.modal.eaFactory.selectedSourceId,
    inFlightCleared: eaFactoryGoogleSheetCatalogInFlight === null,
    abortControllerCleared: eaFactoryGoogleSheetCatalogAbortController === null,
  }}));
}})().catch((error) => {{
  console.error(error);
  process.exitCode = 1;
}});
"""
        completed = subprocess.run(
            [self.node_binary(), "-e", harness],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        result = json.loads(completed.stdout)
        immediate = result["immediate"]
        self.assertEqual(immediate["fetchCount"], 2)
        self.assertTrue(immediate["staleSignalAborted"])
        self.assertEqual(immediate["catalog"]["status"], "loading")
        self.assertTrue(immediate["catalog"]["inFlight"])
        self.assertEqual(immediate["catalog"]["systems"], [])
        self.assertEqual(immediate["catalog"]["requestId"], 12)
        for field in (
            "sheetRecordId",
            "selectedSourceId",
            "importedSourceId",
            "importedRecordDigest",
            "importedCatalogDigest",
            "importedSnapshotDigest",
        ):
            self.assertEqual(immediate[field], "", field)
        self.assertEqual(result["afterFresh"]["configRevision"], 22)
        self.assertEqual(result["afterFresh"]["systems"], [{"recordId": "new-record"}])
        self.assertEqual(result["afterStale"], result["afterFresh"])
        self.assertIsNone(result["staleResult"])
        self.assertIsNone(result["closedResult"])
        self.assertEqual(result["finalFetchCount"], 2)
        self.assertEqual(result["nonSheetSelection"], "discovery-source")
        self.assertTrue(result["inFlightCleared"])
        self.assertTrue(result["abortControllerCleared"])

    def test_auth_schema_and_unready_sheet_states_disable_catalog_fail_closed(self) -> None:
        normalizer = self.block(
            "function normalizeEaFactoryGoogleSheetCatalog",
            "function rerenderEaFactoryGoogleSheetCatalog",
        )
        ensure = self.block(
            "async function ensureEaFactoryGoogleSheetCatalog",
            "async function importEaFactorySourceRecord",
        )
        renderer = self.block(
            "function renderEaFactoryRecordImport",
            "function renderEaFactoryImportedSummary",
        )
        self.assertIn("EA_FACTORY_GOOGLE_SHEET_CATALOG_SCHEMA_VERSION", normalizer)
        self.assertIn('raw.tabName === "Deep_Research"', normalizer)
        self.assertIn("raw.selectedRecord === null", normalizer)
        self.assertIn("totalCount === systems.length", normalizer)
        self.assertIn("auth_required", ensure)
        self.assertIn("permission_denied", ensure)
        self.assertIn("schema_mismatch", ensure)
        self.assertIn("systems: []", ensure)
        self.assertIn("selectedRecord: null", ensure)
        self.assertIn("reconcileEaFactoryGoogleSheetSelection", ensure)
        self.assertIn("fetchJson(EA_FACTORY_GOOGLE_SHEET_CATALOG_ENDPOINT", ensure)
        self.assertNotIn("?recordId", ensure)
        self.assertIn("disabled", renderer)
        self.assertNotRegex(renderer, r"records\s*\[\s*0\s*\]")


if __name__ == "__main__":
    unittest.main()
