from __future__ import annotations

import csv
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


def load_bridge():
    spec = importlib.util.spec_from_file_location("metafx_ea_factory_backend", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        self.assertTrue(record["buildReady"])

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
        sheet_id = "193dlWvLqVzsstF5qStjBOT4h-8wiQMhnXXKkydPRp5A"
        hub_model = {
            "configured": True,
            "sheetId": sheet_id,
            "canonicalUrl": f"https://docs.google.com/spreadsheets/d/{sheet_id}",
            "sheetDisplayValue": sheet_id,
            "sheetReferenceMasked": "193dlW…Rp5A",
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
