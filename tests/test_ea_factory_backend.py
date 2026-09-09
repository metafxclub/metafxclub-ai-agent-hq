from __future__ import annotations

import csv
import copy
import hashlib
import http.client
import importlib.util
import io
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
BLUEPRINT_FIXTURE_PATH = PROJECT_ROOT / "tests" / "test_ea_research_blueprint_v2.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location("metafx_ea_factory_backend", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ready_ea_research_blueprint() -> dict:
    spec = importlib.util.spec_from_file_location(
        "ea_factory_ready_blueprint_fixture",
        BLUEPRINT_FIXTURE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BLUEPRINT_FIXTURE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ready_blueprint()


class DummyCsvResponse:
    def __init__(self, body: bytes, content_type: str = "text/csv") -> None:
        self.body = body
        self.status = 200
        self.headers = {
            "Content-Type": content_type,
            "Content-Length": str(len(body)),
        }

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def geturl(self):
        return "https://docs.google.com/spreadsheets/d/example/gviz/tq?tqx=out:csv"

    def read(self, maximum: int):
        return self.body[:maximum]


class DummyOpener:
    def __init__(self, response: DummyCsvResponse) -> None:
        self.response = response

    def open(self, *_args, **_kwargs):
        return self.response


class EaFactoryBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    @staticmethod
    def exact_indicator_source(requirements: dict) -> str:
        semantic_markers = {
            row["id"]: row["marker"]
            for row in requirements["requiredIndicatorSemanticMarkers"]
        }
        indicator_bindings = {
            row["identity"]: row["id"]
            for row in requirements["indicatorSemanticProfile"]["semanticBindings"]
        }
        rule_markers = {
            row["id"]: row["marker"]
            for row in requirements["requiredRuleMarkers"]
        }
        fast_marker = semantic_markers[indicator_bindings["ema_fast"]]
        slow_marker = semantic_markers[indicator_bindings["ema_slow"]]
        entry_marker = rule_markers["ENTRY_BUY_001"]
        exit_marker = rule_markers["EXIT_BUY_001"]
        return f"""
#property strict
#property indicator_chart_window
#property indicator_buffers 1
double SignalBuffer[];
const bool {fast_marker} = true;
const bool {slow_marker} = true;
double FastValue(int shift) {{
  if(!{fast_marker}) return 0.0;
  return iMA(Symbol(), Period(), 10, 0, MODE_EMA, PRICE_CLOSE, shift);
}}
double SlowValue(int shift) {{
  if(!{slow_marker}) return 0.0;
  return iMA(Symbol(), Period(), 60, 0, MODE_EMA, PRICE_CLOSE, shift);
}}
int OnInit() {{ SetIndexBuffer(0, SignalBuffer); return(INIT_SUCCEEDED); }}
int OnCalculate(const int rates_total, const int prev_calculated,
                const datetime &time[], const double &open[],
                const double &high[], const double &low[],
                const double &close[], const long &tick_volume[],
                const long &volume[], const int &spread[]) {{
  if(rates_total < 3) return(0);
  SignalBuffer[1] = EMPTY_VALUE;
  bool {entry_marker} = FastValue(2) <= SlowValue(2)
                       && FastValue(1) > SlowValue(1);
  if({entry_marker}) SignalBuffer[1] = low[1];
  bool {exit_marker} = FastValue(2) >= SlowValue(2)
                      && FastValue(1) < SlowValue(1);
  if({exit_marker}) SignalBuffer[1] = high[1];
  return(rates_total);
}}
"""

    def valid_values(self, *, verification_status: str = "verified") -> dict:
        return {
            "record_id": "system-001",
            "system_name": "Verified Trend System",
            "strategy_family": "trend_following",
            "symbols_market": "EURUSD / Forex",
            "timeframe": "H1",
            "entry_rules": "Buy on confirmed trend rule",
            "exit_rules": "Exit on opposite confirmed rule",
            "stop_loss": "none",
            "take_profit": "none",
            "recovery": "none",
            "lot_risk": "1 percent fixed fractional",
            "indicators": "none",
            "special_conditions": "none",
            "source_urls": "https://example.org/public-system",
            "verification_status": verification_status,
            "backtest_status": "not_run",
            "backtest_report": "",
            "optimization_status": "not_run",
            "optimization_report": "",
            "issues": "none",
            "next_action": "build",
            "target_platform": "mt4",
            "updated_at": "2026-08-24T09:00:00+07:00",
        }

    def csv_payload(self, values: dict, *, thai_suffix: bool = True) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output)
        header = (
            list(self.bridge.EA_FACTORY_SHEET_TEMPLATE_HEADERS)
            if thai_suffix
            else [field for _column, field, _label, _group in self.bridge.EA_FACTORY_SHEET_COLUMNS]
        )
        writer.writerow(header)
        writer.writerow(
            [values.get(field, "") for _column, field, _label, _group in self.bridge.EA_FACTORY_SHEET_COLUMNS]
        )
        return output.getvalue().encode("utf-8")

    def test_sheet_header_is_exact_a_w_and_thai_suffix_is_allowed(self) -> None:
        records = self.bridge._ea_factory_parse_sheet_rows(
            self.csv_payload(self.valid_values()),
            "sheet-safe-test",
        )
        self.assertEqual(len(records), 1)
        self.assertTrue(records[0]["buildReady"])
        self.assertEqual(records[0]["missingCoreFields"], [])

        reordered = self.csv_payload(self.valid_values()).decode("utf-8").splitlines()
        cells = next(csv.reader([reordered[0]]))
        cells[5], cells[6] = cells[6], cells[5]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(cells)
        writer.writerow(next(csv.reader([reordered[1]])))
        with self.assertRaises(self.bridge.RequestError):
            self.bridge._ea_factory_parse_sheet_rows(output.getvalue().encode(), "sheet-bad-header")

        headerless = io.StringIO()
        writer = csv.writer(headerless)
        writer.writerow(list(self.valid_values().values()))
        with self.assertRaises(self.bridge.RequestError):
            self.bridge._ea_factory_parse_sheet_rows(headerless.getvalue().encode(), "sheet-no-header")

    def test_build_readiness_requires_all_a_m_public_n_and_verified_o(self) -> None:
        verified = self.bridge._ea_factory_normalize_record(
            self.valid_values(),
            source_kind="google_sheet_public_csv",
            source_key="sheet-ready",
        )
        self.assertTrue(verified["buildReady"])

        pending = self.bridge._ea_factory_normalize_record(
            self.valid_values(verification_status="pending"),
            source_kind="google_sheet_public_csv",
            source_key="sheet-pending",
        )
        self.assertFalse(pending["buildReady"])
        self.assertIn("verification_status", pending["missingCoreFields"])

        incomplete_values = self.valid_values()
        incomplete_values["stop_loss"] = ""
        incomplete_values["source_urls"] = "http://private.invalid/system"
        incomplete = self.bridge._ea_factory_normalize_record(
            incomplete_values,
            source_kind="google_sheet_public_csv",
            source_key="sheet-incomplete",
        )
        self.assertFalse(incomplete["buildReady"])
        self.assertIn("stop_loss", incomplete["missingCoreFields"])
        self.assertIn("source_urls", incomplete["missingCoreFields"])

    def test_source_read_model_fails_closed_unless_blueprint_digest_revalidates(self) -> None:
        values = self.valid_values()
        values["eaImplementationBlueprint"] = ready_ea_research_blueprint()
        record = self.bridge._ea_factory_normalize_record(
            values,
            source_kind="verified_deep_research",
            source_key="research-report-canonical-v2",
            source_report_id="research-report-canonical-v2",
        )
        self.assertIsNotNone(record)
        self.assertTrue(record["buildReady"])

        read_model = self.bridge._ea_factory_source_record_read_model(record)
        research = read_model["eaResearch"]
        self.assertTrue(read_model["buildReady"])
        self.assertEqual(read_model["sourceReportId"], "research-report-canonical-v2")
        self.assertTrue(research["validated"])
        self.assertTrue(research["digestMatched"])
        self.assertTrue(research["ready"])
        self.assertEqual(research["validationStatus"], "canonical_validated")
        self.assertEqual(research["blueprintDigest"], record["eaBlueprintDigest"])
        self.assertEqual(research["blueprint"], record["eaImplementationBlueprint"])

        tampered_record = dict(record)
        tampered_record["eaBlueprintDigest"] = "0" * 64
        tampered = self.bridge._ea_factory_source_record_read_model(tampered_record)
        self.assertFalse(tampered["buildReady"])
        self.assertFalse(tampered["eaResearch"]["validated"])
        self.assertFalse(tampered["eaResearch"]["digestMatched"])
        self.assertFalse(tampered["eaResearch"]["ready"])
        self.assertEqual(
            tampered["eaResearch"]["validationStatus"],
            "blueprint_digest_mismatch",
        )
        self.assertIsNone(tampered["eaResearch"]["blueprint"])
        self.assertIn("blueprint_digest_mismatch", tampered["readinessIssues"])

        legacy = dict(record)
        legacy["eaImplementationBlueprint"] = None
        legacy["eaBlueprintDigest"] = None
        legacy_model = self.bridge._ea_factory_source_record_read_model(legacy)
        self.assertFalse(legacy_model["buildReady"])
        self.assertEqual(
            legacy_model["eaResearch"]["validationStatus"],
            "legacy_ea_blueprint_missing",
        )

    def test_create_build_explains_non_ready_blueprint_without_missing_core_fields(self) -> None:
        source_record_id = "ea-source-needs-clarification"
        blocked_source = {
            "sourceRecordId": source_record_id,
            "recordDigest": "a" * 64,
            "buildReady": False,
            "missingCoreFields": [],
            "readinessIssues": [
                "ea_blueprint_needs_clarification",
                "ENTRY_UNKNOWN:$.entry.buy.rules[0]",
            ],
        }
        with (
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=self.bridge._empty_ea_factory_state(),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_source_catalog",
                return_value=[blocked_source],
            ),
        ):
            with self.assertRaises(self.bridge.RequestError) as raised:
                self.bridge.create_ea_factory_build({
                    "sourceRecordId": source_record_id,
                    "platform": "mt4",
                })

        self.assertEqual(raised.exception.status, 422)
        message = str(raised.exception)
        self.assertIn("ea_blueprint_needs_clarification", message)
        self.assertIn("ENTRY_UNKNOWN:$.entry.buy.rules[0]", message)
        self.assertFalse(message.endswith(": "))

    def test_create_build_rejects_unprovable_predicates_before_any_side_effect(self) -> None:
        def wrapped_and(original: dict) -> dict:
            return {"op": "and", "items": [copy.deepcopy(original)]}

        def once_per_bar(original: dict) -> dict:
            return {
                "op": "once_per_bar",
                "barShift": 1,
                "item": copy.deepcopy(original),
            }

        scenarios = {
            "and": wrapped_and,
            "once_per_bar": once_per_bar,
            "rising": lambda _original: {
                "op": "rising",
                "value": {"kind": "indicator", "ref": "ema_fast", "shift": 1},
                "bars": 2,
            },
            "within": lambda _original: {
                "op": "within",
                "value": {"kind": "indicator", "ref": "ema_fast", "shift": 1},
                "lower": {"kind": "constant", "value": 0},
                "upper": {"kind": "constant", "value": 100},
            },
            "break_above": lambda _original: {
                "op": "break_above",
                "left": {"kind": "indicator", "ref": "ema_fast", "shift": 1},
                "right": {"kind": "indicator", "ref": "ema_slow", "shift": 1},
            },
        }
        for operator, make_expression in scenarios.items():
            with self.subTest(operator=operator):
                blueprint = ready_ea_research_blueprint()
                original = blueprint["entry"]["buy"]["rules"][0]["expression"]
                blueprint["entry"]["buy"]["rules"][0]["expression"] = (
                    make_expression(original)
                )
                # These are valid Research expressions.  Rejection belongs to
                # the narrower source-verification capability boundary.
                normalized = self.bridge.normalize_ea_research_blueprint(
                    blueprint,
                    require_ready=True,
                )
                self.assertEqual(
                    normalized["entry"]["buy"]["rules"][0]["expression"]["op"],
                    operator,
                )
                values = self.valid_values()
                values["eaImplementationBlueprint"] = blueprint
                source_record = self.bridge._ea_factory_normalize_record(
                    values,
                    source_kind="verified_deep_research",
                    source_key=f"research-capability-{operator}",
                    source_report_id=f"report-capability-{operator}",
                )
                self.assertIsNotNone(source_record)
                self.assertTrue(source_record["buildReady"])
                empty_state = self.bridge._empty_ea_factory_state()
                with (
                    mock.patch.object(self.bridge, "load_missions", return_value=[]),
                    mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
                    mock.patch.object(
                        self.bridge,
                        "_load_ea_factory_state_unlocked",
                        return_value=empty_state,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_source_catalog",
                        return_value=[source_record],
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_write_ea_factory_state_unlocked",
                    ) as write_state,
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_create_build_workspace",
                    ) as create_workspace,
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_source_report",
                    ) as create_source_report,
                    mock.patch.object(self.bridge, "create_mission") as create_mission,
                    mock.patch.object(self.bridge, "create_report") as create_report,
                ):
                    with self.assertRaises(self.bridge.RequestError) as raised:
                        self.bridge.create_ea_factory_build(
                            {
                                "sourceRecordId": source_record["sourceRecordId"],
                                "platform": "mt4",
                                "idempotencyKey": f"capability-{operator}",
                            }
                        )

                self.assertEqual(raised.exception.status, 422)
                message = str(raised.exception)
                self.assertIn(
                    self.bridge.EA_FACTORY_UNSUPPORTED_RULE_PREDICATE_CODE,
                    message,
                )
                self.assertIn(f"ENTRY_BUY_001({operator})", message)
                write_state.assert_not_called()
                create_workspace.assert_not_called()
                create_source_report.assert_not_called()
                create_mission.assert_not_called()
                create_report.assert_not_called()
                self.assertEqual(empty_state, self.bridge._empty_ea_factory_state())

    def test_rule_predicate_capability_preflight_preserves_comparison_and_cross(self) -> None:
        cross_blueprint = ready_ea_research_blueprint()
        self.assertEqual(
            self.bridge._ea_factory_rule_predicate_capability_issues(cross_blueprint),
            [],
        )

        comparison_blueprint = ready_ea_research_blueprint()
        comparison_blueprint["entry"]["buy"]["rules"][0]["expression"] = {
            "op": ">",
            "left": {"kind": "indicator", "ref": "ema_fast", "shift": 1},
            "right": {"kind": "indicator", "ref": "ema_slow", "shift": 1},
        }
        self.assertEqual(
            self.bridge._ea_factory_rule_predicate_capability_issues(
                comparison_blueprint
            ),
            [],
        )

        class WorkspaceReached(RuntimeError):
            pass

        for label, blueprint in (
            ("cross", cross_blueprint),
            ("comparison", comparison_blueprint),
        ):
            with self.subTest(create_path=label):
                values = self.valid_values()
                values["eaImplementationBlueprint"] = blueprint
                source_record = self.bridge._ea_factory_normalize_record(
                    values,
                    source_kind="verified_deep_research",
                    source_key=f"research-supported-{label}",
                    source_report_id=f"report-supported-{label}",
                )
                self.assertTrue(source_record["buildReady"])
                with (
                    mock.patch.object(self.bridge, "load_missions", return_value=[]),
                    mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
                    mock.patch.object(
                        self.bridge,
                        "_load_ea_factory_state_unlocked",
                        return_value=self.bridge._empty_ea_factory_state(),
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_source_catalog",
                        return_value=[source_record],
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_write_ea_factory_state_unlocked",
                    ) as write_state,
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_create_build_workspace",
                        side_effect=WorkspaceReached,
                    ) as create_workspace,
                ):
                    with self.assertRaises(WorkspaceReached):
                        self.bridge.create_ea_factory_build(
                            {
                                "sourceRecordId": source_record["sourceRecordId"],
                                "platform": "mt4",
                                "idempotencyKey": f"supported-{label}",
                            }
                        )
                write_state.assert_called_once()
                create_workspace.assert_called_once()

    def test_deep_research_nested_facts_project_to_clear_a_w_fields(self) -> None:
        report_id = "auto-report-deep-research-nested"
        mission_id = "mission-deep-research-nested"
        report = {
            "id": report_id,
            "type": "trading_system_research_report",
            "status": "ready",
            "linkedMissionId": mission_id,
            "linkedPropId": "left_server_racks",
            "ownerAgentId": "mission_archivist",
            "title": "Do not use this fallback title",
            "workflowContext": {
                "propId": "left_server_racks",
                "actionId": "deep_research_system",
                "source": {"recordId": "research-system-nested"},
            },
            "metrics": {
                "workflowOutput": {"applicable": True, "valid": True},
                "systemIdentity": {
                    "facts": {
                        "systemName": "CANSLIM Method",
                        "strategyFamily": "growth momentum",
                    }
                },
                "suitableMarket": "US growth equities",
                "suitableTimeframe": "Daily / Weekly",
                "entrySteps": ["Breakout with confirmed volume"],
                "exitSteps": ["Exit at invalidation"],
                "riskModel": {
                    "facts": {
                        "stopLoss": "7-8% below entry",
                        "takeProfit": "partial at 20-25%",
                        "positionSizing": "fixed fractional",
                    }
                },
                "recoveryAndAveragingRules": "never average down",
                "indicatorSettings": "relative strength and volume",
                "specialConditions": "positive market direction",
                "tradeManagementSteps": "pyramid winners only",
                "implementationNotes": "preserve confirmed-bar logic",
                "sourceLinks": ["https://example.org/canslim"],
            },
            "updatedAt": "2026-08-24T09:00:00+07:00",
        }
        mission = {
            "id": mission_id,
            "status": "completed",
            "targetId": "left_server_racks",
            "owner": "mission_archivist",
            "reportIds": [report_id],
        }

        records = self.bridge._ea_factory_research_source_records([report], [mission])

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["displayName"], "CANSLIM Method")
        self.assertEqual(record["core"]["strategy_family"], "growth momentum")
        self.assertEqual(record["core"]["stop_loss"], "7-8% below entry")
        self.assertEqual(record["core"]["take_profit"], "partial at 20-25%")
        self.assertEqual(record["core"]["lot_risk"], "fixed fractional")
        self.assertFalse(record["buildReady"])
        self.assertIsNone(record["eaImplementationBlueprint"])
        self.assertIsNone(record["eaBlueprintDigest"])
        self.assertIn(
            "legacy_or_invalid_ea_blueprint",
            record["readinessIssues"],
        )

    def test_source_catalog_prefers_current_sheet_record_over_legacy_report_duplicate(self) -> None:
        values = self.valid_values()
        current_sheet = self.bridge._ea_factory_normalize_record(
            values,
            source_kind="verified_deep_research_sheet",
            source_key="central-sheet-current",
        )
        legacy_report = self.bridge._ea_factory_normalize_record(
            values,
            source_kind="verified_deep_research",
            source_key="legacy-runtime-report",
        )
        self.assertNotEqual(
            current_sheet["sourceRecordId"],
            legacy_report["sourceRecordId"],
        )

        with (
            mock.patch.object(
                self.bridge,
                "_research_sheet_hub_internal",
                return_value={"sheetId": "central-sheet-id"},
            ),
            mock.patch.object(
                self.bridge,
                "_research_sheet_cached_rows",
                return_value=[],
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_deep_research_records",
                return_value=[current_sheet],
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_google_sheet_records",
                return_value=[],
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_research_source_records",
                return_value=[legacy_report],
            ),
        ):
            catalog = self.bridge._ea_factory_source_catalog(state={})

        self.assertEqual(len(catalog), 1)
        self.assertEqual(catalog[0]["sourceRecordId"], current_sheet["sourceRecordId"])
        self.assertEqual(catalog[0]["sourceKind"], "verified_deep_research_sheet")

    def test_public_sheet_fetch_rejects_html_and_non_csv(self) -> None:
        with mock.patch.object(
            self.bridge,
            "build_opener",
            return_value=DummyOpener(DummyCsvResponse(b"<html><title>Sign in</title></html>", "text/csv")),
        ):
            with self.assertRaises(self.bridge.RequestError):
                self.bridge._ea_factory_fetch_public_sheet_csv("A" * 24, "EA_Full_Cycle")

        with mock.patch.object(
            self.bridge,
            "build_opener",
            return_value=DummyOpener(DummyCsvResponse(b"record_id", "text/html")),
        ):
            with self.assertRaises(self.bridge.RequestError):
                self.bridge._ea_factory_fetch_public_sheet_csv("A" * 24, "EA_Full_Cycle")

    def test_workspace_is_per_build_and_generated_source_must_originate_in_source_folder(self) -> None:
        record = self.bridge._ea_factory_normalize_record(
            self.valid_values(),
            source_kind="google_sheet_public_csv",
            source_key="sheet-workspace",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                workspace = self.bridge._ea_factory_create_build_workspace(
                    "ea-build-workspace-test",
                    record,
                    "mt4",
                )
                build_dir = root / "workspace" / "ea-factory" / "ea-build-workspace-test"
                self.assertEqual(
                    set(path.name for path in build_dir.iterdir() if path.is_dir()),
                    set(self.bridge.EA_FACTORY_BUILD_FOLDER_NAMES),
                )
                self.assertFalse(workspace["rawFilesystemPathExposed"])
                source_path = build_dir / "Source" / "TrendEA.mq4"
                source_path.write_text("#property strict\nint OnInit(){return(INIT_SUCCEEDED);}\n", encoding="utf-8")
                digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
                report = self.generation_report("ea-build-workspace-test", digest)
                build = {
                    "id": "ea-build-workspace-test",
                    "platform": "mt4",
                    "versions": [],
                }
                versions = self.bridge._ea_factory_copy_generated_sources(build, report)
                self.assertEqual(len(versions), 1)
                self.assertEqual(versions[0]["sourceDigest"], digest)
                self.assertTrue((build_dir / versions[0]["versionFile"]).is_file())
                self.assertEqual(
                    (build_dir / versions[0]["versionFile"]).read_bytes(),
                    source_path.read_bytes(),
                )

    def generation_report(self, build_id: str, digest: str) -> dict:
        relative = f"workspace/ea-factory/{build_id}/Source/TrendEA.mq4"
        return {
            "id": "report-generation-proof",
            "type": "ea_build_report",
            "status": "ready",
            "linkedPropId": "right_server_racks",
            "workflowContext": {
                "propId": "right_server_racks",
                "actionId": "build_strategy_code",
                "inputs": {"brief": f"[EA_FACTORY_BUILD_ID:{build_id}]"},
                "source": {"reportId": "report-strategy-spec"},
            },
            "metrics": {
                "workflowOutput": {
                    "applicable": True,
                    "valid": True,
                    "expectedFields": ["sourceFiles", "sourceDigest"],
                    "providedFields": ["sourceFiles", "sourceDigest"],
                    "missingFields": [],
                    "expectedEvidenceKinds": ["project_relative_source_path"],
                    "providedEvidenceKinds": ["project_relative_source_path"],
                    "missingEvidenceKinds": [],
                    "values": {
                        "sourceFiles": json.dumps([relative]),
                        "sourceDigest": digest,
                    },
                }
            },
        }

    def test_outside_build_source_is_never_ingested(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root / "workspace" / "OtherEA.mq4"
            outside.parent.mkdir(parents=True)
            outside.write_text("#property strict", encoding="utf-8")
            digest = hashlib.sha256(outside.read_bytes()).hexdigest()
            report = self.generation_report("ea-build-boundary-test", digest)
            report["metrics"]["workflowOutput"]["values"]["sourceFiles"] = json.dumps(
                ["workspace/OtherEA.mq4"]
            )
            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                self.bridge._ea_factory_create_build_workspace(
                    "ea-build-boundary-test",
                    self.bridge._ea_factory_normalize_record(
                        self.valid_values(),
                        source_kind="google_sheet_public_csv",
                        source_key="sheet-boundary",
                    ),
                    "mt4",
                )
                build = {"id": "ea-build-boundary-test", "platform": "mt4", "versions": []}
                self.assertEqual(self.bridge._ea_factory_copy_generated_sources(build, report), [])

    def test_maximum_user_requirements_survive_generation_dispatch_exactly(self) -> None:
        requirements = ("require confirmed closed bar and fixed risk only " * 30)[:900].strip()
        build = {
            "id": "ea-build-long-requirements",
            "sourceReportId": "report-strategy-spec",
            "sourceRecordId": "ea-source-long-requirements",
            "sourceRecordDigest": "a" * 64,
            "platform": "mt4",
            "brief": requirements,
            "workspace": {"strategySpecDigest": "b" * 64},
        }
        generation_brief = self.bridge._ea_factory_generation_brief(build)
        self.assertLessEqual(len(generation_brief), 2400)
        self.assertIn(
            f"[USER_BUILD_REQUIREMENTS]{requirements}[/USER_BUILD_REQUIREMENTS]",
            generation_brief,
        )
        self.assertIn("Risk sizing must fail closed", generation_brief)
        self.assertIn("worst-case loss", generation_brief)
        self.assertIn("no min-lot uplift", generation_brief)
        self.assertIn("tick alignment", generation_brief)
        self.assertIn("prime first available and return", generation_brief)

        action = self.bridge.DASHBOARD_WORKFLOW_ACTIONS["build_strategy_code"]
        form = self.bridge._sanitize_dashboard_workflow_form(
            action,
            {
                "sourceReportId": build["sourceReportId"],
                "platform": "mt4",
                "brief": generation_brief,
            },
        )
        self.assertEqual(form["brief"], generation_brief)
        prompt = self.bridge._workflow_prompt(
            "build_strategy_code",
            form,
            {"structuredPayload": {"largeUntrustedContext": "x" * 10000}},
        )
        self.assertIn(generation_brief, prompt)

    def test_custom_indicator_contract_is_no_trade_and_backtest_not_applicable(self) -> None:
        blueprint = self.bridge.normalize_ea_research_blueprint(
            ready_ea_research_blueprint(),
            require_ready=True,
        )
        blueprint_digest = self.bridge.ea_research_blueprint_digest(blueprint)
        requirements = self.bridge._ea_factory_indicator_coverage_requirements(
            blueprint,
            blueprint_digest,
        )
        source = self.exact_indicator_source(requirements)
        source_digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        manifest = self.bridge._ea_factory_indicator_coverage_manifest(
            requirements,
            source,
            strategy_spec_digest="a" * 64,
            source_digest=source_digest,
            target_platform="mt4",
        )
        self.assertTrue(manifest["complete"])
        self.assertEqual(manifest["missingRuleMarkers"], [])
        self.assertEqual(manifest["forbiddenTradingFunctions"], [])
        self.assertTrue(manifest["checks"]["onCalculate"])
        self.assertTrue(manifest["checks"]["indicatorOutputAssignment"])
        self.assertTrue(manifest["checks"]["ruleMarkersControlOutput"])
        self.assertTrue(all(
            row["semanticPredicate"] and row["controlsIndicatorOutput"]
            for row in manifest["ruleMarkerEvidence"]
        ))

        values = self.valid_values()
        values["eaImplementationBlueprint"] = blueprint
        source_record = self.bridge._ea_factory_normalize_record(
            values,
            source_kind="verified_deep_research",
            source_key="report-indicator-source",
            source_report_id="report-indicator-source",
        )
        self.assertTrue(source_record["buildReady"])
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            self.bridge,
            "PROJECT_ROOT",
            Path(temporary),
        ):
            workspace = self.bridge._ea_factory_create_build_workspace(
                "ea-build-indicator-contract",
                source_record,
                "mt4",
                "custom_indicator",
            )
            spec = json.loads(
                (
                    Path(temporary)
                    / "workspace"
                    / "ea-factory"
                    / "ea-build-indicator-contract"
                    / workspace["strategySpecFile"]
                ).read_text(encoding="utf-8")
            )
        self.assertEqual(spec["artifactKind"], "custom_indicator")
        self.assertNotIn("blueprintCoverageRequirements", spec)
        self.assertEqual(
            spec["indicatorCoverageRequirements"],
            requirements,
        )
        self.assertEqual(spec["buildGuardrails"]["backtestStage"], "not_applicable")
        self.assertTrue(spec["buildGuardrails"]["tradingFunctionsForbidden"])

        unsafe = source + "\nvoid OnTick(){ OrderSend(Symbol(),OP_BUY,0.1,Ask,3,0,0); }\n"
        rejected = self.bridge._ea_factory_indicator_coverage_manifest(
            requirements,
            unsafe,
            strategy_spec_digest="a" * 64,
            source_digest=hashlib.sha256(unsafe.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(rejected["complete"])
        self.assertIn("OnTick", rejected["forbiddenTradingFunctions"])
        self.assertIn("OrderSend", rejected["forbiddenTradingFunctions"])

        stages = self.bridge._ea_factory_initial_stages(
            "mt4",
            {"id": "mission-spec-indicator"},
            {"id": "report-spec-indicator"},
            "custom_indicator",
        )
        backtest = self.bridge._ea_factory_stage_row(
            {"stages": stages},
            "backtest_recheck",
        )
        self.assertEqual(backtest["status"], "not_applicable")
        self.assertTrue(backtest["evidenceVerified"])

    def test_custom_indicator_rejects_rule_marker_sink_unrelated_to_buffer_output(self) -> None:
        blueprint = self.bridge.normalize_ea_research_blueprint(
            ready_ea_research_blueprint(),
            require_ready=True,
        )
        blueprint_digest = self.bridge.ea_research_blueprint_digest(blueprint)
        requirements = self.bridge._ea_factory_indicator_coverage_requirements(
            blueprint,
            blueprint_digest,
        )
        source = self.exact_indicator_source(requirements)
        source = source.replace(
            "SignalBuffer[1] = EMPTY_VALUE;",
            "SignalBuffer[1] = EMPTY_VALUE; int markerSink = 0;",
        )
        for row in requirements["requiredRuleMarkers"]:
            source = source.replace(
                f"if({row['marker']}) SignalBuffer[1]",
                f"if({row['marker']}) markerSink",
            )
        manifest = self.bridge._ea_factory_indicator_coverage_manifest(
            requirements,
            source,
            strategy_spec_digest="a" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(manifest["complete"])
        self.assertFalse(manifest["checks"]["ruleMarkersControlOutput"])
        self.assertEqual(
            manifest["missingRuleMarkers"],
            [row["id"] for row in requirements["requiredRuleMarkers"]],
        )
        self.assertTrue(all(
            row["presentInOnCalculate"]
            and row["semanticPredicate"]
            and not row["controlsIndicatorOutput"]
            for row in manifest["ruleMarkerEvidence"]
        ))

    def test_custom_indicator_rejects_semantic_and_no_output_decoys(self) -> None:
        blueprint = self.bridge.normalize_ea_research_blueprint(
            ready_ea_research_blueprint(),
            require_ready=True,
        )
        blueprint_digest = self.bridge.ea_research_blueprint_digest(blueprint)
        requirements = self.bridge._ea_factory_indicator_coverage_requirements(
            blueprint,
            blueprint_digest,
        )
        source = self.exact_indicator_source(requirements)
        rule_markers = {
            row["id"]: row["marker"] for row in requirements["requiredRuleMarkers"]
        }
        entry_marker = rule_markers["ENTRY_BUY_001"]
        exit_marker = rule_markers["EXIT_BUY_001"]
        fast_call = (
            "return iMA(Symbol(), Period(), 10, 0, MODE_EMA, "
            "PRICE_CLOSE, shift);"
        )
        slow_call = (
            "return iMA(Symbol(), Period(), 60, 0, MODE_EMA, "
            "PRICE_CLOSE, shift);"
        )
        swapped_parameters = source.replace(fast_call, "__FAST_CALL__").replace(
            slow_call,
            fast_call,
        ).replace("__FAST_CALL__", slow_call)
        cases = {
            "swapped-indicator-parameters": swapped_parameters,
            "wrong-indicator-family": source.replace(
                fast_call,
                "return iRSI(Symbol(), Period(), 14, PRICE_CLOSE, shift);",
            ).replace(
                slow_call,
                "return iRSI(Symbol(), Period(), 7, PRICE_CLOSE, shift);",
            ),
            "rule-or-true": source.replace(
                "&& FastValue(1) > SlowValue(1);",
                "&& FastValue(1) > SlowValue(1) || true;",
            ).replace(
                "&& FastValue(1) < SlowValue(1);",
                "&& FastValue(1) < SlowValue(1) || true;",
            ),
            "rule-negated": source.replace(
                f"bool {entry_marker} = FastValue(2) <= SlowValue(2)\n"
                "                       && FastValue(1) > SlowValue(1);",
                f"bool {entry_marker} = !(FastValue(2) <= SlowValue(2)\n"
                "                       && FastValue(1) > SlowValue(1));",
            ),
            "rule-statically-false-conjunct": source.replace(
                "&& FastValue(1) > SlowValue(1);",
                "&& FastValue(1) > SlowValue(1) && (1 + 1 == 3);",
                1,
            ),
            "marker-reassigned": source.replace(
                f"  if({entry_marker})",
                f"  {entry_marker} = false;\n  if({entry_marker})",
            ),
            "zero-is-configured-empty": source.replace(
                "SetIndexBuffer(0, SignalBuffer);",
                "SetIndexBuffer(0, SignalBuffer); SetIndexEmptyValue(0, 0.0);",
            ).replace(
                "SignalBuffer[1] = low[1];",
                "SignalBuffer[1] = 0.0;",
            ).replace(
                "SignalBuffer[1] = high[1];",
                "SignalBuffer[1] = 0.0;",
            ),
            "constant-sentinel-output": source.replace(
                "SignalBuffer[1] = low[1];",
                "SignalBuffer[1] = 123456789;",
            ).replace(
                "SignalBuffer[1] = high[1];",
                "SignalBuffer[1] = -123456789;",
            ),
            "draw-none": source.replace(
                "SetIndexBuffer(0, SignalBuffer);",
                "SetIndexBuffer(0, SignalBuffer); SetIndexStyle(0, DRAW_NONE);",
            ),
            "dead-buffer-binding": source.replace(
                "SetIndexBuffer(0, SignalBuffer);",
                "if(false) SetIndexBuffer(0, SignalBuffer);",
            ),
            "assignment-after-return": source.replace(
                f"if({entry_marker}) SignalBuffer[1] = low[1];",
                f"if({entry_marker}) {{ return(rates_total); "
                "SignalBuffer[1] = low[1]; }",
            ).replace(
                f"if({exit_marker}) SignalBuffer[1] = high[1];",
                f"if({exit_marker}) {{ return(rates_total); "
                "SignalBuffer[1] = high[1]; }",
            ),
            "dead-rule-output-branches": source.replace(
                f"if({entry_marker}) SignalBuffer[1] = low[1];",
                f"if(false) {{ if({entry_marker}) SignalBuffer[1] = low[1]; }}",
            ).replace(
                f"if({exit_marker}) SignalBuffer[1] = high[1];",
                f"if(false) {{ if({exit_marker}) SignalBuffer[1] = high[1]; }}",
            ),
            "self-assignment-no-op": source.replace(
                "SignalBuffer[1] = low[1];",
                "SignalBuffer[1] = SignalBuffer[1];",
            ).replace(
                "SignalBuffer[1] = high[1];",
                "SignalBuffer[1] = SignalBuffer[1] + 0.0;",
            ),
            "rule-marker-macro-override": source.replace(
                "int OnCalculate(",
                f"#undef {entry_marker}\n#define {entry_marker} false\n"
                "int OnCalculate(",
                1,
            ),
            "include-hidden-logic": "#include <HiddenLogic.mqh>\n" + source,
        }
        for label, candidate in cases.items():
            with self.subTest(label=label):
                self.assertNotEqual(candidate, source)
                manifest = self.bridge._ea_factory_indicator_coverage_manifest(
                    requirements,
                    candidate,
                    strategy_spec_digest="a" * 64,
                    source_digest=hashlib.sha256(candidate.encode("utf-8")).hexdigest(),
                    target_platform="mt4",
                )
                self.assertFalse(manifest["complete"], manifest)

        lexical_include_decoys = (
            "// #include <CommentOnly.mqh>\n"
            'string IncludeDescription = "#include <StringOnly.mqh>";\n'
            + source
        )
        lexical_manifest = self.bridge._ea_factory_indicator_coverage_manifest(
            requirements,
            lexical_include_decoys,
            strategy_spec_digest="a" * 64,
            source_digest=hashlib.sha256(
                lexical_include_decoys.encode("utf-8")
            ).hexdigest(),
            target_platform="mt4",
        )
        self.assertTrue(lexical_manifest["complete"], lexical_manifest)

    def test_custom_indicator_rejects_final_write_and_binding_lifecycle_bypasses(self) -> None:
        blueprint = self.bridge.normalize_ea_research_blueprint(
            ready_ea_research_blueprint(),
            require_ready=True,
        )
        blueprint_digest = self.bridge.ea_research_blueprint_digest(blueprint)
        requirements = self.bridge._ea_factory_indicator_coverage_requirements(
            blueprint,
            blueprint_digest,
        )
        source = self.exact_indicator_source(requirements)
        rule_markers = {
            row["id"]: row["marker"] for row in requirements["requiredRuleMarkers"]
        }
        entry_marker = rule_markers["ENTRY_BUY_001"]
        exit_marker = rule_markers["EXIT_BUY_001"]
        cases = {
            "same-series-subtraction-is-zero": (
                source.replace(
                    "SignalBuffer[1] = low[1];",
                    "SignalBuffer[1] = low[1] - low[1];",
                ).replace(
                    "SignalBuffer[1] = high[1];",
                    "SignalBuffer[1] = high[1] - high[1];",
                ),
                "indicatorOutputAssignment",
            ),
            "constant-math-functions": (
                source.replace(
                    "SignalBuffer[1] = low[1];",
                    "SignalBuffer[1] = MathSin(0);",
                ).replace(
                    "SignalBuffer[1] = high[1];",
                    "SignalBuffer[1] = MathCos(0);",
                ),
                "indicatorOutputAssignment",
            ),
            "marker-branch-final-empty": (
                source.replace(
                    f"if({entry_marker}) SignalBuffer[1] = low[1];",
                    f"if({entry_marker}) {{ SignalBuffer[1] = low[1]; "
                    "SignalBuffer[1] = EMPTY_VALUE; }",
                ).replace(
                    f"if({exit_marker}) SignalBuffer[1] = high[1];",
                    f"if({exit_marker}) {{ SignalBuffer[1] = high[1]; "
                    "SignalBuffer[1] = EMPTY_VALUE; }",
                ),
                "ruleMarkersControlOutput",
            ),
            "unconditional-final-empty": (
                source.replace(
                    "  return(rates_total);\n}",
                    "  SignalBuffer[1] = EMPTY_VALUE;\n  return(rates_total);\n}",
                    1,
                ),
                "ruleMarkersControlOutput",
            ),
            "nested-path-erases-final-output": (
                source.replace(
                    f"if({entry_marker}) SignalBuffer[1] = low[1];",
                    f"if({entry_marker}) {{ SignalBuffer[1] = low[1]; "
                    "if(rates_total > 100) SignalBuffer[1] = EMPTY_VALUE; }",
                ).replace(
                    f"if({exit_marker}) SignalBuffer[1] = high[1];",
                    f"if({exit_marker}) {{ SignalBuffer[1] = high[1]; "
                    "if(rates_total > 100) SignalBuffer[1] = EMPTY_VALUE; }",
                ),
                "ruleMarkersControlOutput",
            ),
            "binding-only-in-never-called-helper": (
                source.replace(
                    "int OnInit() { SetIndexBuffer(0, SignalBuffer); "
                    "return(INIT_SUCCEEDED); }",
                    "void BindSignalBuffer() { SetIndexBuffer(0, SignalBuffer); }\n"
                    "int OnInit() { return(INIT_SUCCEEDED); }",
                ),
                "indicatorBufferBinding",
            ),
            "same-index-rebound-to-another-buffer": (
                source.replace(
                    "double SignalBuffer[];",
                    "double SignalBuffer[];\ndouble OtherBuffer[];",
                ).replace(
                    "SetIndexBuffer(0, SignalBuffer);",
                    "SetIndexBuffer(0, SignalBuffer); "
                    "SetIndexBuffer(0, OtherBuffer);",
                ),
                "indicatorBufferBinding",
            ),
        }
        for label, (candidate, failed_check) in cases.items():
            with self.subTest(label=label):
                self.assertNotEqual(candidate, source)
                manifest = self.bridge._ea_factory_indicator_coverage_manifest(
                    requirements,
                    candidate,
                    strategy_spec_digest="a" * 64,
                    source_digest=hashlib.sha256(candidate.encode("utf-8")).hexdigest(),
                    target_platform="mt4",
                )
                self.assertFalse(manifest["complete"], manifest)
                self.assertFalse(manifest["checks"][failed_check], manifest)

        called_helper = source.replace(
            "int OnInit() { SetIndexBuffer(0, SignalBuffer); "
            "return(INIT_SUCCEEDED); }",
            "void BindSignalBuffer() { SetIndexBuffer(0, SignalBuffer); }\n"
            "int OnInit() { BindSignalBuffer(); return(INIT_SUCCEEDED); }",
        )
        called_helper_manifest = self.bridge._ea_factory_indicator_coverage_manifest(
            requirements,
            called_helper,
            strategy_spec_digest="a" * 64,
            source_digest=hashlib.sha256(called_helper.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertTrue(called_helper_manifest["complete"], called_helper_manifest)

    def test_custom_indicator_rejects_symbolic_output_and_rebind_bypass_matrix(self) -> None:
        blueprint = self.bridge.normalize_ea_research_blueprint(
            ready_ea_research_blueprint(),
            require_ready=True,
        )
        blueprint_digest = self.bridge.ea_research_blueprint_digest(blueprint)
        requirements = self.bridge._ea_factory_indicator_coverage_requirements(
            blueprint,
            blueprint_digest,
        )
        source = self.exact_indicator_source(requirements)
        rule_markers = {
            row["id"]: row["marker"] for row in requirements["requiredRuleMarkers"]
        }
        entry_marker = rule_markers["ENTRY_BUY_001"]
        exit_marker = rule_markers["EXIT_BUY_001"]

        def replace_outputs(entry_value: str, exit_value: str) -> str:
            return source.replace(
                "SignalBuffer[1] = low[1];",
                f"SignalBuffer[1] = {entry_value};",
            ).replace(
                "SignalBuffer[1] = high[1];",
                f"SignalBuffer[1] = {exit_value};",
            )

        alias_source = source.replace(
            "  SignalBuffer[1] = EMPTY_VALUE;",
            "  SignalBuffer[1] = EMPTY_VALUE;\n"
            "  double EntryAlias = low[1];\n"
            "  double EntryAliasAgain = EntryAlias;\n"
            "  double ExitAlias = high[1];\n"
            "  double ExitAliasAgain = ExitAlias;",
        ).replace(
            "SignalBuffer[1] = low[1];",
            "SignalBuffer[1] = EntryAliasAgain * 0;",
        ).replace(
            "SignalBuffer[1] = high[1];",
            "SignalBuffer[1] = ExitAliasAgain * 0;",
        )
        helper_zero_source = replace_outputs(
            "ZeroSignal(low[1])",
            "ZeroSignal(high[1])",
        ).replace(
            "int OnCalculate(",
            "double ZeroSignal(double value) { return value * 0; }\n"
            "int OnCalculate(",
            1,
        )
        compound_source = source.replace(
            f"if({entry_marker}) SignalBuffer[1] = low[1];",
            f"if({entry_marker}) {{ SignalBuffer[1] = low[1]; "
            "SignalBuffer[1] *= 0; }",
        ).replace(
            f"if({exit_marker}) SignalBuffer[1] = high[1];",
            f"if({exit_marker}) {{ SignalBuffer[1] = high[1]; "
            "SignalBuffer[1] *= 0; }",
        )
        array_initialize_source = source.replace(
            "  return(rates_total);\n}",
            "  ArrayInitialize(SignalBuffer, EMPTY_VALUE);\n"
            "  return(rates_total);\n}",
            1,
        )
        array_fill_source = source.replace(
            "  return(rates_total);\n}",
            "  ArrayFill(SignalBuffer, 0, ArraySize(SignalBuffer), EMPTY_VALUE);\n"
            "  return(rates_total);\n}",
            1,
        )
        array_copy_source = source.replace(
            "double SignalBuffer[];",
            "double SignalBuffer[];\ndouble OtherBuffer[];",
        ).replace(
            "  return(rates_total);\n}",
            "  ArrayCopy(SignalBuffer, OtherBuffer, 0, 0, WHOLE_ARRAY);\n"
            "  return(rates_total);\n}",
            1,
        )
        dynamic_rebind_source = source.replace(
            "double SignalBuffer[];",
            "double SignalBuffer[];\ndouble OtherBuffer[];",
        ).replace(
            "SetIndexBuffer(0, SignalBuffer);",
            "SetIndexBuffer(0, SignalBuffer); int dynamicIndex = 0; "
            "SetIndexBuffer(dynamicIndex, OtherBuffer);",
        )
        helper_rebind_source = source.replace(
            "double SignalBuffer[];",
            "double SignalBuffer[];\ndouble OtherBuffer[];",
        ).replace(
            "int OnInit() { SetIndexBuffer(0, SignalBuffer); "
            "return(INIT_SUCCEEDED); }",
            "void RebindOutput() { SetIndexBuffer(0, OtherBuffer); }\n"
            "int OnInit() { SetIndexBuffer(0, SignalBuffer); RebindOutput(); "
            "return(INIT_SUCCEEDED); }",
        )
        cases = {
            "market-series-times-zero": (
                replace_outputs("low[1] * 0", "high[1] * 0"),
                "indicatorOutputAssignment",
            ),
            "market-series-divided-by-itself": (
                replace_outputs("low[1] / low[1]", "high[1] / high[1]"),
                "indicatorOutputAssignment",
            ),
            "wrapped-market-series-times-zero": (
                replace_outputs(
                    "NormalizeDouble(low[1] * 0, 5)",
                    "NormalizeDouble(high[1] * 0, 5)",
                ),
                "indicatorOutputAssignment",
            ),
            "equal-constant-ternary": (
                replace_outputs(
                    "(low[1] > high[1]) ? 7.0 : 7.0",
                    "(high[1] > low[1]) ? -7.0 : -7.0",
                ),
                "indicatorOutputAssignment",
            ),
            "prior-buffer-plus-cancelled-series": (
                replace_outputs(
                    "SignalBuffer[1] + low[1] - low[1]",
                    "SignalBuffer[1] + high[1] - high[1]",
                ),
                "indicatorOutputAssignment",
            ),
            "two-hop-alias-times-zero": (
                alias_source,
                "indicatorOutputAssignment",
            ),
            "helper-return-times-zero": (
                helper_zero_source,
                "indicatorOutputAssignment",
            ),
            "compound-zero-after-marker-write": (
                compound_source,
                "ruleMarkersControlOutput",
            ),
            "whole-buffer-empty-after-marker-write": (
                array_initialize_source,
                "ruleMarkersControlOutput",
            ),
            "array-fill-empty-after-marker-write": (
                array_fill_source,
                "ruleMarkersControlOutput",
            ),
            "array-copy-to-bound-output-after-marker-write": (
                array_copy_source,
                "ruleMarkersControlOutput",
            ),
            "dynamic-index-rebind": (
                dynamic_rebind_source,
                "indicatorBufferBinding",
            ),
            "called-helper-rebind": (
                helper_rebind_source,
                "indicatorBufferBinding",
            ),
        }
        for label, (candidate, failed_check) in cases.items():
            with self.subTest(label=label):
                self.assertNotEqual(candidate, source)
                manifest = self.bridge._ea_factory_indicator_coverage_manifest(
                    requirements,
                    candidate,
                    strategy_spec_digest="a" * 64,
                    source_digest=hashlib.sha256(candidate.encode("utf-8")).hexdigest(),
                    target_platform="mt4",
                )
                self.assertFalse(manifest["complete"], manifest)
                self.assertFalse(manifest["checks"][failed_check], manifest)

        value_helper = replace_outputs(
            "IdentitySignal(low[1])",
            "IdentitySignal(high[1])",
        ).replace(
            "int OnCalculate(",
            "double IdentitySignal(double value) { return value; }\n"
            "int OnCalculate(",
            1,
        )
        value_helper_manifest = self.bridge._ea_factory_indicator_coverage_manifest(
            requirements,
            value_helper,
            strategy_spec_digest="a" * 64,
            source_digest=hashlib.sha256(value_helper.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertTrue(value_helper_manifest["complete"], value_helper_manifest)

        metadata_only = source.replace(
            "SetIndexBuffer(0, SignalBuffer);",
            "SetIndexBuffer(0, SignalBuffer); "
            "ArraySetAsSeries(SignalBuffer, true);",
        )
        metadata_only_manifest = self.bridge._ea_factory_indicator_coverage_manifest(
            requirements,
            metadata_only,
            strategy_spec_digest="a" * 64,
            source_digest=hashlib.sha256(metadata_only.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertTrue(metadata_only_manifest["complete"], metadata_only_manifest)

    def test_custom_indicator_briefs_are_specific_and_tradingview_is_rejected(self) -> None:
        build = {
            "id": "ea-build-indicator-brief",
            "sourceReportId": "report-strategy-spec",
            "sourceRecordId": "ea-source-indicator-brief",
            "sourceRecordDigest": "a" * 64,
            "artifactKind": "custom_indicator",
            "platform": "mt5",
            "brief": "use closed bars and one arrow buffer",
            "workspace": {"strategySpecDigest": "b" * 64},
        }
        generation = self.bridge._ea_factory_generation_brief(build)
        self.assertIn("[EA_FACTORY_ARTIFACT_KIND:custom_indicator]", generation)
        self.assertIn("Generate one MQL Custom Indicator", generation)
        self.assertIn("No OnTick, CTrade, OrderSend", generation)
        self.assertIn("do not open MetaEditor/MT4/MT5, compile, backtest", generation)
        self.assertLessEqual(len(generation), 2400)

        build["stages"] = [
            {
                "id": "generate_source",
                "reportId": "report-indicator-generation",
            }
        ]
        build["versions"] = [{"sourceDigest": "c" * 64}]
        review = self.bridge._ea_factory_review_brief(build)
        self.assertIn("MQL Custom Indicator", review)
        self.assertIn("indicator_buffers", review)
        self.assertIn("trading side effect", review)
        self.assertLessEqual(len(review), 2400)

        with self.assertRaises(self.bridge.RequestError) as caught:
            self.bridge.create_ea_factory_build({
                "sourceRecordId": "ea-source-indicator-brief",
                "artifactKind": "custom_indicator",
                "platform": "tradingview",
            })
        self.assertEqual(caught.exception.status, 422)

    def test_expert_advisor_default_preserves_legacy_request_identity(self) -> None:
        expected = self.bridge.payload_digest(
            "ea-factory-create-build-v1",
            "ea-source-legacy",
            "mt4",
            "",
        )
        self.assertEqual(
            self.bridge._ea_factory_create_request_digest(
                "ea-source-legacy",
                "mt4",
                "",
            ),
            expected,
        )
        self.assertEqual(
            self.bridge._ea_factory_create_request_digest(
                "ea-source-legacy",
                "mt4",
                "",
                "expert_advisor",
            ),
            expected,
        )

    def test_runtime_runner_contract_preserves_factory_integrity_fields(self) -> None:
        binding_fields = {"sourceRecordDigest", "strategySpecDigest", "platform"}
        generation = self.bridge._trusted_workflow_plugin_profile(
            "right_server_racks",
            "build_strategy_code",
            {"platform": "mt4"},
        )
        review = self.bridge._trusted_workflow_plugin_profile(
            "right_server_racks",
            "review_source_code",
            {"platform": "mt4"},
        )
        self.assertTrue(binding_fields.issubset(set(generation["outputFields"])))
        self.assertTrue(binding_fields.issubset(set(review["outputFields"])))
        self.assertIn("strategyCoverage", review["outputFields"])

        stored_generation = self.bridge._plugin_procedure_storage(generation)
        stored_review = self.bridge._plugin_procedure_storage(review)
        self.assertTrue(binding_fields.issubset(set(stored_generation["outputFields"])))
        self.assertTrue(binding_fields.issubset(set(stored_review["outputFields"])))
        self.assertIn("strategyCoverage", stored_review["outputFields"])

    def test_stage_gates_are_manual_and_pine_skips_backtest(self) -> None:
        stages = self.bridge._ea_factory_initial_stages(
            "tradingview",
            {"id": "mission-spec"},
            {"id": "report-spec"},
        )
        build = {"stages": stages}
        self.assertTrue(self.bridge._ea_factory_stage_can_advance(build, "generate_source"))
        self.assertFalse(self.bridge._ea_factory_stage_can_advance(build, "source_review"))
        self.assertEqual(
            self.bridge._ea_factory_stage_row(build, "backtest_recheck")["status"],
            "not_applicable",
        )
        self.assertFalse(
            any(
                job.get("propId") == "right_server_racks"
                for job in self.bridge.DASHBOARD_WORKFLOW_SCHEDULE_JOBS
            )
        )

    def test_compile_and_strategy_tester_connections_fail_closed(self) -> None:
        freshness = {
            "bridge": self.bridge._connection_probe_freshness({}),
            "codexQuota": self.bridge._connection_probe_freshness({}),
            "metatrader": self.bridge._connection_probe_freshness({}),
        }
        for item_id in ("metaeditor_compile_adapter", "strategy_tester_adapter"):
            item = self.bridge._connection_item_status(
                {
                    "id": item_id,
                    "labelTh": item_id,
                    "required": False,
                    "adapterStatus": "guarded_requires_selected_matching_terminal_and_proof",
                },
                {},
                {},
                {},
                False,
                freshness,
                {"status": "selected", "configurationStatus": "configured", "selectedCandidate": {"candidateId": "mtc-safe", "platform": "mt4"}},
            )
            self.assertEqual(item["status"], "not_connected")
            self.assertFalse(item["adapterReady"])

    def test_read_model_has_exact_manual_frontend_safe_shape(self) -> None:
        empty_state = self.bridge._empty_ea_factory_state()
        sheet_id = "1MfxHQSyntheticSheetId0123456789ABCDEabcde"
        hub_model = {
            "configured": True,
            "sheetId": sheet_id,
            "canonicalUrl": f"https://docs.google.com/spreadsheets/d/{sheet_id}",
            "sheetDisplayValue": sheet_id,
            "sheetReferenceMasked": "1MfxHQ…bcde",
            "configRevision": 7,
            "applyPhase": "completed",
            "applyStatus": "ready",
            "verificationStatus": "read_ready_write_unverified",
            "consumers": [{
                "consumerId": "deepResearch",
                "tabName": "Deep_Research",
                "status": "read_ready",
                "readReady": True,
                "writeReady": False,
            }],
        }
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=empty_state),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
            mock.patch.object(self.bridge, "research_sheet_hub_read_model", return_value=hub_model),
            mock.patch.object(self.bridge, "peek_metatrader_status", return_value={"status": "not_checked", "candidates": []}),
            mock.patch.object(
                self.bridge,
                "_metatrader_selection_read_model",
                return_value={"candidates": [], "selectedCandidate": None, "adapterReady": False},
            ),
        ):
            model = self.bridge.ea_factory_read_model()
        self.assertEqual(model["mode"], "manual_stage_by_stage")
        self.assertFalse(model["scheduled"])
        self.assertFalse(model["schedulerEnabled"])
        self.assertEqual(set(model["sourceCatalog"]), {"sheetSchema", "records", "googleSheets"})
        self.assertEqual(model["sourceCatalog"]["googleSheets"]["sheetId"], sheet_id)
        self.assertEqual(model["sourceCatalog"]["googleSheets"]["configRevision"], 7)
        self.assertTrue(model["safety"]["rawSheetIdExposed"])
        self.assertFalse(model["safety"]["sheetIdIsCredential"])
        serialized = json.dumps(model)
        for forbidden in ("accessToken", "refreshToken", "serviceAccountKey", "clientSecret"):
            self.assertNotIn(forbidden, serialized)
        self.assertFalse(model["terminalSelection"]["adapterReady"])
        self.assertFalse(model["safety"]["syntheticCompileOrBacktestSuccessAllowed"])
        self.assertEqual(
            model["endpoints"]["downloadArtifactTemplate"],
            "/api/props/right_server_racks/ea-factory/builds/{buildId}/files/{fileId}",
        )

    def test_dedicated_get_create_and_advance_routes_dispatch(self) -> None:
        factory_model = {
            "schemaVersion": "ea-factory-v1",
            "mode": "manual_stage_by_stage",
            "scheduled": False,
        }
        create_result = {
            "ok": True,
            "kind": "ea_factory_build_created",
            "mission": None,
            "build": {"id": "ea-build-route"},
            "eaFactory": factory_model,
            "idempotentReplay": False,
        }
        advance_result = {
            **create_result,
            "kind": "ea_factory_stage_dispatched",
            "report": None,
        }
        with (
            mock.patch.object(self.bridge, "ea_factory_read_model", return_value=factory_model),
            mock.patch.object(self.bridge, "create_ea_factory_build", return_value=create_result) as create,
            mock.patch.object(self.bridge, "advance_ea_factory_build", return_value=advance_result) as advance,
        ):
            server = self.bridge.BridgeHTTPServer(("127.0.0.1", 0), self.bridge.BridgeHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                status, body = self.request(server.server_port, "GET", "/api/props/right_server_racks/ea-factory")
                self.assertEqual(status, 200)
                self.assertEqual(body, {"ok": True, "eaFactory": factory_model})
                status, body = self.request(
                    server.server_port,
                    "POST",
                    "/api/props/right_server_racks/ea-factory/builds",
                    {"sourceRecordId": "ea-source-route", "platform": "mt4"},
                )
                self.assertEqual(status, 200)
                self.assertEqual(body["kind"], "ea_factory_build_created")
                status, body = self.request(
                    server.server_port,
                    "POST",
                    "/api/props/right_server_racks/ea-factory/builds/ea-build-route/advance",
                    {"stageId": "generate_source"},
                )
                self.assertEqual(status, 200)
                self.assertEqual(body["kind"], "ea_factory_stage_dispatched")
                create.assert_called_once()
                advance.assert_called_once_with("ea-build-route", {"stageId": "generate_source"})
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def request(self, port: int, method: str, path: str, payload: dict | None = None):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {"Content-Type": "application/json"} if body is not None else {}
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        decoded = json.loads(response.read().decode("utf-8"))
        status = response.status
        connection.close()
        return status, decoded


if __name__ == "__main__":
    unittest.main()
