from __future__ import annotations

import copy
import http.client
import importlib.util
import json
import tempfile
import threading
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "backend" / "local-runner" / "bridge_server.py"
BLUEPRINT_FIXTURE_PATH = ROOT / "tests" / "test_ea_research_blueprint_v2.py"
SHEET_ID = "1MfxHQConfirmationGateSyntheticSheet0123456789"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "deep_research_confirmation_gate_bridge",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ready_blueprint() -> dict:
    spec = importlib.util.spec_from_file_location(
        "deep_research_confirmation_gate_fixture",
        BLUEPRINT_FIXTURE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BLUEPRINT_FIXTURE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ready_blueprint()


def ready_brief() -> dict:
    return {
        "schemaVersion": "ea-strategy-brief/1.0.0",
        "systemName": "Confirmation Gate EMA Cross",
        "systemOverview": "ระบบตามแนวโน้ม Forex; timeframe เป็น input ที่ผู้ใช้เลือก",
        "entryRules": "Buy เมื่อ EMA 10 ตัดขึ้น EMA 60 บนแท่งปิด; Sell ใช้เงื่อนไขกลับกัน",
        "recoveryRules": "ไม่มีการแก้ไม้ ห้าม Grid, Martingale, Averaging และ Hedging",
        "exitRules": "ปิดด้วย SL, TP, trailing stop หรือสัญญาณตัดกลับตาม input",
        "moneyManagement": "รองรับ fixed lot และ risk percent พร้อมจำกัดหนึ่ง position",
        "orderExecution": "ส่ง Buy/Sell แบบ market order หลังแท่งสัญญาณปิด",
        "displayRequirements": "แสดงชื่อระบบ สถานะสัญญาณ Balance, Equity และ Spread",
        "additionalNotes": "ค่า period, SL, TP และ trailing ต้องปรับได้จาก EA inputs",
        "sourceLinks": [
            "https://tradingfinder.com/education/ema-cross",
            "https://forex-station.com/ema-cross-confirmation",
        ],
        "checkedAt": "2026-09-09T01:00:00+00:00",
        "limitations": ["เป็นข้อกำหนดสร้าง Source EA ไม่ใช่ผล Backtest"],
    }


class DeepResearchConfirmationGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.runtime = Path(self.temp.name) / "runtime"
        self.reports = self.runtime / "reports"
        self.reports.mkdir(parents=True)
        self.stack = ExitStack()
        replacements = {
            "RUNTIME_DIR": self.runtime,
            "RUNTIME_REPORTS_DIR": self.reports,
            "MISSIONS_PATH": self.runtime / "missions.json",
            "DASHBOARD_WORKFLOW_SETTINGS_PATH": self.runtime / "dashboard-workflow-settings.json",
            "RESEARCH_SHEET_OUTBOX_PATH": self.runtime / "research-sheet-outbox.json",
            "RESEARCH_SHEET_CACHE_PATH": self.runtime / "research-sheet-cache.json",
            "DEEP_RESEARCH_CONFIRMATIONS_PATH": self.runtime / "deep-research-confirmations.json",
            "EA_FACTORY_STATE_PATH": self.runtime / "ea-factory-state.json",
            "AUDIT_PATH": self.runtime / "bridge-audit.jsonl",
        }
        for name, value in replacements.items():
            self.stack.enter_context(mock.patch.object(self.bridge, name, value))
        self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "_ea_factory_build_root",
                return_value=self.runtime / "ea-factory-workspaces",
            )
        )
        self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "_deep_research_required_open_urls_for_mission",
                return_value=(
                    [
                        "https://tradingfinder.com/education/ema-cross",
                        "https://forex-station.com/ema-cross-confirmation",
                    ],
                    None,
                ),
            )
        )

    def tearDown(self) -> None:
        self.stack.close()
        self.temp.cleanup()

    def deep_report(self) -> dict:
        blueprint = ready_blueprint()
        blueprint["strategyId"] = "confirmation-gate-ema-cross"
        blueprint["scope"]["systemName"] = "Confirmation Gate EMA Cross"
        projection = self.bridge.ea_research_report_projection(blueprint)
        strategy_brief = ready_brief()
        brief_digest = self.bridge.compute_strategy_brief_digest(strategy_brief)
        source_report_id = "report-world-confirm-001"
        source_record_id = "world-system-confirm-001"
        return {
            "id": "report-deep-confirm-001",
            "type": "trading_system_research_report",
            "title": "Deep research confirmation contract",
            "summary": "Canonical EA-ready research awaiting explicit operator confirmation.",
            "status": "ready",
            "linkedPropId": "left_server_racks",
            "linkedMissionId": "mission-deep-confirm-001",
            "ownerAgentId": "mission_archivist",
            "createdAt": "2026-09-09T01:00:00Z",
            "updatedAt": "2026-09-09T01:05:00Z",
            "workflowContext": {
                "schemaVersion": "dashboard-workflow-lineage-v1",
                "propId": "left_server_racks",
                "actionId": "deep_research_system",
                "coordinationMode": self.bridge.DASHBOARD_WORKFLOW_COORDINATION_MODE,
                "source": {
                    "kind": "verified_catalog_record",
                    "propId": "codex_mcp_portal",
                    "recordId": source_record_id,
                    "reportId": source_report_id,
                    "missionId": "mission-world-confirm-001",
                },
                "inputs": {
                    "sourceReportId": source_report_id,
                    "sourceRecordId": source_record_id,
                },
                "inputDigest": self.bridge.payload_digest(
                    "deep-research-confirmation-gate-fixture",
                    source_report_id,
                    source_record_id,
                ),
                "submittedAt": "2026-09-09T00:59:00Z",
                "triggerSource": "frontend",
            },
            "metrics": {
                "workflowOutput": {"applicable": True, "valid": True},
                "eaBlueprint": copy.deepcopy(blueprint),
                **projection,
                "strategyBrief": strategy_brief,
                "briefDigest": brief_digest,
                "sourceDigest": brief_digest,
            },
        }

    def mission(self, report: dict) -> dict:
        return {
            "id": report["linkedMissionId"],
            "status": "completed",
            "targetId": "left_server_racks",
            "owner": "mission_archivist",
            "reportIds": [report["id"]],
            "workflowContext": copy.deepcopy(report["workflowContext"]),
            "workflowOutputContract": copy.deepcopy(
                report["metrics"]["workflowOutput"]
            ),
        }

    def persist_report_and_mission(self, report: dict) -> None:
        self.bridge.write_json(self.reports / f"{report['id']}.json", report)
        self.bridge.save_missions([self.mission(report)])

    def configure_active_sheet(self) -> None:
        settings = self.bridge._default_dashboard_workflow_settings()
        settings["researchSheetHub"].update(
            {
                "sheetId": SHEET_ID,
                "canonicalUrl": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}",
                "configRevision": 1,
                "active": True,
                "activeConfigRevision": 1,
                "activationConfirmedAt": "2026-09-09T01:10:00Z",
                "savedAt": "2026-09-09T01:09:00Z",
                "lastVerifiedAt": "2026-09-09T01:10:00Z",
                "lastVerificationStatus": "read_ready_write_unverified",
                "consumerChecks": {
                    contract["consumerId"]: {
                        "tabName": contract["tabName"],
                        "status": "ready",
                        "readReady": True,
                        "configRevision": 1,
                    }
                    for contract in self.bridge.RESEARCH_SHEET_HUB_PROP_TABS.values()
                },
            }
        )
        self.bridge.write_json(self.bridge.DASHBOARD_WORKFLOW_SETTINGS_PATH, settings)

    def digest_for(self, report: dict) -> str:
        metrics = report["metrics"]
        brief = self.bridge.normalize_strategy_brief(metrics["strategyBrief"])
        return self.bridge.compute_strategy_brief_digest(brief)

    def write_confirmation(
        self,
        report: dict,
        *,
        digest: str | None = None,
        save_to_sheet: bool = True,
    ) -> None:
        record = {
            "schemaVersion": self.bridge.DEEP_RESEARCH_CONFIRMATION_SCHEMA_VERSION,
            "researchReportId": report["id"],
            "confirmedBriefDigest": digest or self.digest_for(report),
            "confirmedAssumptionIds": [],
            "confirmedAt": "2026-09-09T01:15:00Z",
            "saveToGoogleSheet": save_to_sheet,
            "status": "confirmed",
            "sourceMissionId": report["linkedMissionId"],
            "sheetBinding": self.bridge._deep_research_active_sheet_binding(),
        }
        self.bridge.write_json(
            self.bridge.DEEP_RESEARCH_CONFIRMATIONS_PATH,
            {
                "schemaVersion": self.bridge.DEEP_RESEARCH_CONFIRMATION_STORE_VERSION,
                "records": [record],
                "updatedAt": "2026-09-09T01:15:00Z",
            },
        )

    def replace_blueprint(self, report: dict, blueprint: dict) -> dict:
        projection = self.bridge.ea_research_report_projection(blueprint)
        # The compact contract must be authored explicitly; a legacy Blueprint
        # is never converted into build authorization by the Backend.
        strategy_brief = copy.deepcopy(report["metrics"]["strategyBrief"])
        strategy_brief["systemName"] = blueprint["scope"]["systemName"]
        brief_digest = self.bridge.compute_strategy_brief_digest(strategy_brief)
        report["metrics"] = {
            "workflowOutput": {"applicable": True, "valid": True},
            "eaBlueprint": copy.deepcopy(blueprint),
            **projection,
            "strategyBrief": strategy_brief,
            "briefDigest": brief_digest,
            "sourceDigest": brief_digest,
        }
        return report

    def confirmed_deep_rows(self, report: dict) -> list[dict]:
        self.write_confirmation(report)
        rows, _legacy_factory_rows = self.bridge._research_sheet_deep_rows(report)
        return rows

    def cache_deep_rows(self, rows: list[dict]) -> None:
        self.bridge.write_json(
            self.bridge.RESEARCH_SHEET_CACHE_PATH,
            {
                "schemaVersion": "research-sheet-cache-v1",
                "sheetDigest": self.bridge.payload_digest(
                    "research-sheet-id-v1",
                    SHEET_ID,
                ),
                "configRevision": 1,
                "consumers": {
                    "deepResearch": {
                        "rows": copy.deepcopy(rows),
                        "rowCount": len(rows),
                        "updatedAt": self.bridge.utc_now(),
                    }
                },
                "updatedAt": self.bridge.utc_now(),
            },
        )

    def persist_pending_delivery(self, report: dict) -> list[dict]:
        items = self.bridge._research_sheet_report_items(report, 1)
        outbox = self.bridge._research_sheet_outbox_default()
        outbox["items"] = copy.deepcopy(items)
        self.bridge.write_json(self.bridge.RESEARCH_SHEET_OUTBOX_PATH, outbox)
        return items

    @staticmethod
    def request(port: int, payload: dict) -> tuple[int, dict]:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        body = json.dumps(payload).encode("utf-8")
        connection.request(
            "POST",
            "/api/props/left_server_racks/deep-research/confirm",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        decoded = json.loads(response.read().decode("utf-8"))
        status = response.status
        connection.close()
        return status, decoded

    def test_deep_research_workflow_is_exactly_two_steps(self) -> None:
        tabs = self.bridge.DASHBOARD_WORKFLOW_TABS["left_server_racks"]
        self.assertEqual([tab["id"] for tab in tabs], ["select", "analysis"])
        self.assertEqual(tabs[0]["actionIds"], ["deep_research_system"])
        self.assertEqual(tabs[1]["actionIds"], [])
        action = self.bridge.DASHBOARD_WORKFLOW_ACTIONS["deep_research_system"]
        self.assertEqual(action["propId"], "left_server_racks")
        self.assertEqual(action["tabId"], "select")
        self.assertTrue(action["analysisOnly"])

    def test_archived_unsuccessful_or_detached_mission_cannot_confirm(self) -> None:
        report = self.deep_report()
        mission = self.mission(report)
        mission["status"] = "archived"
        mission["archivedSuccessful"] = False
        _row, error = self.bridge._deep_research_report_lineage(report, mission)
        self.assertEqual(error, "research_mission_lineage_invalid")

        mission = self.mission(report)
        mission["workflowContext"]["source"]["recordId"] = "detached-record"
        _row, error = self.bridge._deep_research_report_lineage(report, mission)
        self.assertEqual(error, "research_output_contract_invalid")

        mission = self.mission(report)
        with mock.patch.object(
            self.bridge,
            "_deep_research_required_open_urls_for_mission",
            return_value=([], "trading_system_research_source_binding_detached"),
        ):
            _row, error = self.bridge._deep_research_report_lineage(
                report,
                mission,
            )
        self.assertEqual(
            error,
            "trading_system_research_source_binding_detached",
        )

    def test_second_research_revision_checks_only_its_compact_ten_column_row(self) -> None:
        older = self.deep_report()
        older["id"] = "report-deep-confirm-older"
        older["createdAt"] = "2026-09-08T01:00:00Z"
        older["updatedAt"] = "2026-09-08T01:05:00Z"
        newer = self.deep_report()
        self.bridge.write_json(self.reports / f"{older['id']}.json", older)
        self.bridge.write_json(self.reports / f"{newer['id']}.json", newer)

        rows, _factory = self.bridge._research_sheet_deep_rows(newer)
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]), 10)
        self.assertEqual(set(rows[0]), set(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS))
        completeness = self.bridge._deep_research_projected_column_completeness(
            newer
        )
        self.assertEqual(completeness["requiredColumnCount"], 10)
        self.assertEqual(completeness["populatedColumnCount"], 10)
        self.assertEqual(completeness["missingColumns"], [])

    def test_compact_sheet_row_is_treated_as_already_confirmed_delivery(self) -> None:
        report = self.deep_report()
        self.configure_active_sheet()
        rows, _factory = self.bridge._research_sheet_deep_rows(report)
        self.assertEqual(len(rows), 1)
        self.assertEqual(set(rows[0]), set(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS))
        records = self.bridge._ea_factory_deep_research_records(
            rows,
            source_key="confirmed-before-sheet-delivery",
            strict=True,
        )
        self.assertEqual(len(records), 1)
        self.assertTrue(records[0]["buildReady"])

    def test_report_compare_and_swap_does_not_overwrite_newer_revision(self) -> None:
        report = self.deep_report()
        self.bridge.write_json(self.reports / f"{report['id']}.json", report)
        expected = self.bridge._report_snapshot_digest(report)
        newer = copy.deepcopy(report)
        newer["summary"] = "NEWER CONCURRENT REVISION"
        newer["updatedAt"] = "2026-09-09T01:06:00Z"
        self.bridge.write_json(self.reports / f"{report['id']}.json", newer)

        with self.assertRaises(self.bridge.RequestError) as raised:
            self.bridge.create_report(
                report,
                queue_research_sheet=False,
                expected_existing_digest=expected,
            )
        self.assertEqual(raised.exception.status, 409)
        stored = self.bridge.read_json(self.reports / f"{report['id']}.json", {})
        self.assertEqual(stored["summary"], "NEWER CONCURRENT REVISION")

    def test_confirmation_flush_is_scoped_to_exact_report_items(self) -> None:
        self.configure_active_sheet()
        outbox = self.bridge._research_sheet_outbox_default()
        now = "2026-09-09T01:20:00Z"

        def item(item_id: str, record_key: str) -> dict:
            return {
                "id": item_id,
                "status": "pending",
                "consumerId": "deepResearch",
                "producerPropId": "left_server_racks",
                "tabName": "Deep_Research",
                "keyHeader": "research_id",
                "recordKey": record_key,
                "row": {"research_id": record_key},
                "payloadDigest": self.bridge.payload_digest(record_key),
                "configRevision": 1,
                "reportId": f"report-{record_key}",
                "missionId": f"mission-{record_key}",
                "attemptCount": 0,
                "requeueCount": 0,
                "lastAttemptAt": None,
                "nextAttemptAt": None,
                "lastErrorCode": None,
                "receipt": None,
                "createdAt": now,
                "updatedAt": now,
            }

        outbox["items"] = [item("item-a", "A"), item("item-b", "B")]
        self.bridge.write_json(self.bridge.RESEARCH_SHEET_OUTBOX_PATH, outbox)
        with (
            mock.patch.object(
                self.bridge.google_sheet_hub,
                "credential_status",
                return_value={"configured": True},
            ),
            mock.patch.object(
                self.bridge.google_sheet_hub,
                "upsert_row",
                return_value={"verified": True},
            ) as upsert,
            mock.patch.object(self.bridge, "_research_sheet_mark_write_verified"),
            mock.patch.object(self.bridge, "_refresh_research_sheet_cache"),
        ):
            result = self.bridge._flush_research_sheet_outbox(
                max_items=50,
                allowed_item_ids={"item-a"},
            )
        self.assertEqual(result["processed"], 1)
        self.assertEqual(upsert.call_count, 1)
        stored = self.bridge.read_json(self.bridge.RESEARCH_SHEET_OUTBOX_PATH, {})
        status_by_id = {row["id"]: row["status"] for row in stored["items"]}
        self.assertEqual(status_by_id, {"item-a": "synced", "item-b": "pending"})

    def test_queue_rejects_a_sheet_changed_after_confirmation_preflight(self) -> None:
        self.configure_active_sheet()
        binding = self.bridge._deep_research_active_sheet_binding()
        settings = self.bridge.read_json(
            self.bridge.DASHBOARD_WORKFLOW_SETTINGS_PATH,
            {},
        )
        settings["researchSheetHub"].update(
            {
                "sheetId": "1DifferentSyntheticSheetForRace0123456789",
                "configRevision": 2,
                "active": True,
                "activeConfigRevision": 2,
            }
        )
        self.bridge.write_json(
            self.bridge.DASHBOARD_WORKFLOW_SETTINGS_PATH,
            settings,
        )
        result = self.bridge._research_sheet_queue_report(
            self.deep_report(),
            flush=False,
            expected_sheet_binding=binding,
        )
        self.assertEqual(result["queued"], 0)
        self.assertEqual(result["reason"], "sheet_configuration_changed")
        self.assertFalse(self.bridge.RESEARCH_SHEET_OUTBOX_PATH.exists())

    def test_unconfirmed_report_is_complete_but_cannot_queue_or_reach_factory(self) -> None:
        report = self.deep_report()
        mission = self.mission(report)
        self.persist_report_and_mission(report)
        self.configure_active_sheet()

        rows, _factory_rows = self.bridge._research_sheet_deep_rows(report)
        self.assertEqual(len(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS), 10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(set(rows[0]), set(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS))
        completeness = self.bridge._deep_research_projected_column_completeness(report)
        self.assertEqual(completeness["requiredColumnCount"], 10)
        self.assertEqual(completeness["populatedColumnCount"], 10)
        self.assertEqual(completeness["missingColumns"], [])
        self.assertEqual(len(completeness["columnStatuses"]), 10)
        self.assertTrue(all(item["present"] for item in completeness["columnStatuses"]))

        with mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_status",
            return_value={"configured": True, "mode": "access_token"},
        ):
            model = self.bridge.report_read_model_item(report)["eaResearch"]["confirmation"]
        self.assertTrue(model["required"])
        self.assertFalse(model["confirmed"])
        self.assertTrue(model["canConfirm"])
        # This is an advertised destination contract, not a claim that the
        # unconfirmed report has already been written to Sheets.
        self.assertTrue(model["saveToGoogleSheet"])
        self.assertEqual(model["briefDigest"], self.digest_for(report))

        self.assertEqual(self.bridge._research_sheet_report_items(report, 1), [])
        self.assertEqual(
            self.bridge._ea_factory_research_source_records([report], [mission]),
            [],
        )

    def test_only_exact_digest_and_true_sheet_consent_unlock_downstream_consumers(self) -> None:
        report = self.deep_report()
        mission = self.mission(report)
        self.configure_active_sheet()

        self.write_confirmation(report, digest="0" * 64)
        self.assertFalse(self.bridge._deep_research_report_is_human_confirmed(report))
        self.assertEqual(self.bridge._research_sheet_report_items(report, 1), [])
        self.assertEqual(self.bridge._ea_factory_research_source_records([report], [mission]), [])

        self.write_confirmation(report, save_to_sheet=False)
        self.assertFalse(self.bridge._deep_research_report_is_human_confirmed(report))
        self.assertEqual(self.bridge._research_sheet_report_items(report, 1), [])
        self.assertEqual(self.bridge._ea_factory_research_source_records([report], [mission]), [])

        self.write_confirmation(report)
        self.assertTrue(self.bridge._deep_research_report_is_human_confirmed(report))
        sheet_items = self.bridge._research_sheet_report_items(report, 1)
        self.assertEqual(len(sheet_items), 1)
        self.assertEqual(sheet_items[0]["consumerId"], "deepResearch")
        # Confirmation permits queueing but does not claim that Google accepted
        # the row.  EA Factory must stay closed until the exact item digest has
        # a durable synced receipt.
        self.assertEqual(self.bridge._ea_factory_research_source_records([report], [mission]), [])
        outbox = self.bridge._research_sheet_outbox_default()
        outbox["syncedLedger"] = [
            {
                "id": sheet_items[0]["id"],
                "payloadDigest": sheet_items[0]["payloadDigest"],
                "configRevision": 1,
                "syncedAt": "2026-09-09T01:16:00Z",
            }
        ]
        self.bridge.write_json(self.bridge.RESEARCH_SHEET_OUTBOX_PATH, outbox)
        factory_records = self.bridge._ea_factory_research_source_records([report], [mission])
        self.assertEqual(len(factory_records), 1)
        self.assertTrue(factory_records[0]["buildReady"])
        self.assertEqual(factory_records[0]["strategyBriefDigest"], self.digest_for(report))

    def test_legacy_blueprint_is_diagnostic_only_and_requires_research_rerun(self) -> None:
        report = self.deep_report()
        legacy_digest = report["metrics"]["blueprintDigest"]
        report["metrics"].pop("strategyBrief")
        report["metrics"].pop("briefDigest")
        report["metrics"].pop("sourceDigest")
        self.persist_report_and_mission(report)
        self.configure_active_sheet()

        # Even a historical v3-shaped receipt that has only the old Blueprint
        # digest cannot authenticate a compact handoff.
        self.bridge.write_json(
            self.bridge.DEEP_RESEARCH_CONFIRMATIONS_PATH,
            {
                "schemaVersion": self.bridge.DEEP_RESEARCH_CONFIRMATION_STORE_VERSION,
                "records": [
                    {
                        "schemaVersion": self.bridge.DEEP_RESEARCH_CONFIRMATION_SCHEMA_VERSION,
                        "status": "confirmed",
                        "researchReportId": report["id"],
                        "sourceMissionId": report["linkedMissionId"],
                        "confirmedBlueprintDigest": legacy_digest,
                        "confirmedAssumptionIds": [],
                        "confirmedAt": "2026-09-09T01:15:00Z",
                        "saveToGoogleSheet": True,
                        "sheetBinding": self.bridge._deep_research_active_sheet_binding(),
                    }
                ],
            },
        )

        model = self.bridge.report_read_model_item(report)["eaResearch"]
        self.assertEqual(model["validationStatus"], "legacy_blueprint_read_only")
        self.assertFalse(model["validated"])
        self.assertFalse(model["ready"])
        self.assertFalse(model["eaHandoffAllowed"])
        self.assertTrue(model["requiresResearchRerun"])
        self.assertIsNone(model["blueprint"])
        self.assertIsInstance(model["legacyBlueprintDiagnostic"], dict)
        self.assertFalse(model["confirmation"]["canConfirm"])
        self.assertFalse(self.bridge._deep_research_report_is_human_confirmed(report))
        self.assertFalse(self.bridge._deep_research_report_is_handoff_ready(report))
        self.assertEqual(self.bridge._research_sheet_deep_rows(report), ([], []))
        self.assertEqual(
            self.bridge._ea_factory_research_source_records(
                [report],
                [self.mission(report)],
            ),
            [],
        )

        with self.assertRaises(self.bridge.RequestError) as caught:
            self.bridge.confirm_deep_research_for_ea(
                {
                    "researchReportId": report["id"],
                    "confirmBlueprintDigest": legacy_digest,
                    "confirmAssumptions": True,
                    "confirmSaveToGoogleSheet": True,
                }
            )
        self.assertEqual(caught.exception.status, 422)
        self.assertIn("Strategy Brief A-J", str(caught.exception))

    def test_http_confirmation_rejects_bad_requests_then_is_idempotent(self) -> None:
        report = self.deep_report()
        self.persist_report_and_mission(report)
        self.configure_active_sheet()
        digest = self.digest_for(report)
        queue_result = {
            "queued": 1,
            "synced": 0,
            "pending": 1,
            "reason": None,
        }
        factory_model = {
            "schemaVersion": "ea-factory-v1",
            "sourceCatalog": {"records": []},
        }
        with (
            mock.patch.object(
                self.bridge,
                "_research_sheet_queue_report",
                return_value=queue_result,
            ) as queue_report,
            mock.patch.object(
                self.bridge,
                "ea_factory_read_model",
                return_value=factory_model,
            ),
            mock.patch.object(
                self.bridge.google_sheet_hub,
                "credential_status",
                return_value={"configured": True, "mode": "access_token"},
            ),
        ):
            server = self.bridge.BridgeHTTPServer(("127.0.0.1", 0), self.bridge.BridgeHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                rejected = (
                    {
                        "researchReportId": report["id"],
                        "confirmBriefDigest": "f" * 64,
                        "confirmAssumptions": True,
                        "confirmSaveToGoogleSheet": True,
                    },
                    {
                        "researchReportId": report["id"],
                        "confirmBriefDigest": digest,
                        "confirmAssumptions": False,
                        "confirmSaveToGoogleSheet": True,
                    },
                    {
                        "researchReportId": report["id"],
                        "confirmBriefDigest": digest,
                        "confirmAssumptions": True,
                        "confirmSaveToGoogleSheet": False,
                    },
                    {
                        "researchReportId": report["id"],
                        "confirmBriefDigest": digest,
                        "confirmAssumptions": True,
                        "confirmSaveToGoogleSheet": True,
                        "unexpected": "must fail closed",
                    },
                    {
                        "researchReportId": "unknown-report",
                        "confirmBriefDigest": digest,
                        "confirmAssumptions": True,
                        "confirmSaveToGoogleSheet": True,
                    },
                )
                for payload in rejected:
                    with self.subTest(payload=payload):
                        status, body = self.request(server.server_port, payload)
                        self.assertIn(status, {400, 404, 409, 422})
                        self.assertFalse(body.get("ok", False))
                self.assertFalse(self.bridge.DEEP_RESEARCH_CONFIRMATIONS_PATH.exists())
                queue_report.assert_not_called()

                valid = {
                    "researchReportId": report["id"],
                    "confirmBriefDigest": digest,
                    "confirmSaveToGoogleSheet": True,
                }
                first_status, first = self.request(server.server_port, valid)
                second_status, second = self.request(server.server_port, valid)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

        self.assertEqual(first_status, 200)
        self.assertTrue(first["ok"])
        self.assertFalse(first["idempotentReplay"])
        self.assertEqual(first["confirmation"]["briefDigest"], digest)
        self.assertEqual(first["confirmation"]["confirmedBriefDigest"], digest)
        self.assertTrue(first["confirmation"]["saveToGoogleSheet"])
        self.assertEqual(second_status, 200)
        self.assertTrue(second["ok"])
        self.assertTrue(second["idempotentReplay"])
        self.assertEqual(queue_report.call_count, 2)
        store = self.bridge.read_json(self.bridge.DEEP_RESEARCH_CONFIRMATIONS_PATH, {})
        self.assertEqual(len(store["records"]), 1)
        self.assertTrue(self.bridge._deep_research_report_is_human_confirmed(report))

    def test_ready_ten_columns_round_trip_to_build_payload_for_mt4_and_mt5(self) -> None:
        report = self.deep_report()
        self.configure_active_sheet()
        rows = self.confirmed_deep_rows(report)

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(
            set(row),
            set(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS),
        )
        self.assertEqual(len(row), 10)
        self.assertTrue(
            all(
                self.bridge._research_sheet_cell_is_present(row.get(header))
                for header in self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS
            )
        )

        records = self.bridge._ea_factory_deep_research_records(
            rows,
            source_key="deep-research-ten-column-round-trip",
            strict=True,
        )
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertTrue(record["buildReady"])
        self.assertEqual(record["missingCoreFields"], [])
        self.assertEqual(record["readinessIssues"], [])
        self.assertEqual(
            record["core"]["strategy_family"],
            report["metrics"]["strategyBrief"]["systemOverview"],
        )
        self.assertEqual(
            record["strategyBriefDigest"],
            self.bridge._ea_factory_sheet_strategy_brief_digest(
                row["record_id"],
                {
                    name: row[name]
                    for name in self.bridge.EA_STRATEGY_BRIEF_SHEET_TO_CAMEL
                },
            ),
        )

        with (
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_ea_factory_source_catalog",
                return_value=[record],
            ),
            mock.patch.object(self.bridge, "peek_metatrader_status", return_value={}),
            mock.patch.object(
                self.bridge.google_sheet_hub,
                "credential_status",
                return_value={"configured": True, "mode": "access_token"},
            ),
        ):
            for platform in ("mt4", "mt5"):
                with self.subTest(platform=platform):
                    created = self.bridge.create_ea_factory_build(
                        {
                            "sourceRecordId": record["sourceRecordId"],
                            "platform": platform,
                            "artifactKind": "expert_advisor",
                            "brief": "สร้างตาม Strategy Brief โดยไม่เดากฎเพิ่ม",
                            "idempotencyKey": f"handoff-round-trip-{platform}",
                        }
                    )
                    self.assertTrue(created["ok"])
                    self.assertEqual(created["build"]["platform"], platform)
                    build_dir = self.bridge._ea_factory_build_directory(
                        created["build"]["id"]
                    )
                    spec = self.bridge.read_json(
                        build_dir / "Source" / "strategy-spec-v01.json",
                        {},
                    )
                    self.assertEqual(spec["targetPlatform"], platform)
                    self.assertEqual(spec["coreRange"], "A-J")
                    self.assertEqual(
                        spec["downstreamRange"],
                        "Backend report and confirmation ledger",
                    )
                    self.assertEqual(spec["core"], record["core"])
                    self.assertEqual(spec["strategyBrief"], record["strategyBrief"])
                    self.assertEqual(
                        spec["strategyBriefDigest"],
                        record["strategyBriefDigest"],
                    )

    def test_current_revision_projects_one_compact_upsert_row_for_factory(self) -> None:
        self.configure_active_sheet()
        older = self.deep_report()
        older.update(
            {
                "id": "report-deep-revision-old",
                "linkedMissionId": "mission-deep-revision-old",
                "createdAt": "2026-09-08T01:00:00Z",
                "updatedAt": "2026-09-08T01:05:00Z",
            }
        )
        newer = self.deep_report()
        newer.update(
            {
                "id": "report-deep-revision-new",
                "linkedMissionId": "mission-deep-revision-new",
                "createdAt": "2026-09-09T01:00:00Z",
                "updatedAt": "2026-09-09T01:05:00Z",
            }
        )
        newer["metrics"]["strategyBrief"]["entryRules"] = "New revision: enter after confirmed closed-bar cross"
        newer["metrics"]["briefDigest"] = self.bridge.compute_strategy_brief_digest(
            newer["metrics"]["strategyBrief"]
        )
        newer["metrics"]["sourceDigest"] = newer["metrics"]["briefDigest"]
        self.bridge.write_json(self.reports / f"{older['id']}.json", older)
        self.bridge.write_json(self.reports / f"{newer['id']}.json", newer)
        self.write_confirmation(newer)

        rows, _legacy = self.bridge._research_sheet_deep_rows(newer)
        self.assertEqual(len(rows), 1)
        current = rows[0]
        self.assertEqual(len(current), 10)
        self.assertIn("New revision", current["entry_rules"])

        records = self.bridge._ea_factory_deep_research_records(
            [current],
            source_key="revision-current-wins",
            strict=True,
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["recordId"], current["record_id"])
        self.assertTrue(records[0]["buildReady"])

    def test_new_pending_revision_revokes_old_cached_build_source(self) -> None:
        self.configure_active_sheet()
        older = self.deep_report()
        older.update(
            {
                "id": "report-deep-cache-old",
                "linkedMissionId": "mission-deep-cache-old",
                "createdAt": "2026-09-07T01:00:00Z",
                "updatedAt": "2026-09-07T01:05:00Z",
            }
        )
        self.persist_report_and_mission(older)
        old_rows = self.confirmed_deep_rows(older)
        self.assertEqual(set(old_rows[0]), set(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS))
        self.cache_deep_rows(old_rows)

        newer = self.deep_report()
        newer.update(
            {
                "id": "report-deep-cache-new-pending",
                "linkedMissionId": "mission-deep-cache-new-pending",
                "createdAt": "2026-09-09T01:00:00Z",
                "updatedAt": "2026-09-09T01:05:00Z",
            }
        )
        newer["metrics"]["strategyBrief"]["entryRules"] += (
            "; revision ใหม่เพิ่มตัวกรอง spread ก่อนส่งคำสั่ง"
        )
        newer["metrics"]["briefDigest"] = self.bridge.compute_strategy_brief_digest(
            newer["metrics"]["strategyBrief"]
        )
        newer["metrics"]["sourceDigest"] = newer["metrics"]["briefDigest"]
        self.persist_report_and_mission(newer)
        self.write_confirmation(newer)
        pending = self.persist_pending_delivery(newer)
        self.assertEqual(len(pending), 1)
        self.assertFalse(self.bridge._deep_research_report_is_handoff_ready(newer))

        with mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_status",
            return_value={"configured": True, "mode": "access_token"},
        ):
            catalog = self.bridge._ea_factory_source_catalog(
                state=self.bridge._empty_ea_factory_state(),
                reports=[newer, older],
                missions=[self.mission(newer), self.mission(older)],
            )
        self.assertFalse(
            any(
                row.get("recordId") == old_rows[0]["record_id"]
                and row.get("buildReady") is True
                for row in catalog
            ),
            "A pending newer revision must revoke the older cached build source.",
        )

    def test_new_blocked_revision_revokes_old_cached_build_source(self) -> None:
        self.configure_active_sheet()
        older = self.deep_report()
        older.update(
            {
                "id": "report-deep-cache-ready-old",
                "linkedMissionId": "mission-deep-cache-ready-old",
                "createdAt": "2026-09-07T01:00:00Z",
                "updatedAt": "2026-09-07T01:05:00Z",
            }
        )
        self.persist_report_and_mission(older)
        old_rows = self.confirmed_deep_rows(older)
        self.cache_deep_rows(old_rows)

        newer = self.deep_report()
        newer.update(
            {
                "id": "report-deep-cache-new-blocked",
                "linkedMissionId": "mission-deep-cache-new-blocked",
                "createdAt": "2026-09-09T01:00:00Z",
                "updatedAt": "2026-09-09T01:05:00Z",
            }
        )
        blocked_blueprint = ready_blueprint()
        blocked_rule = blocked_blueprint["entry"]["buy"]["rules"][0]
        blocked_rule.update(
            {
                "sourceStatus": "unknown",
                "sourceRefs": [],
                "expression": {"op": "unknown"},
            }
        )
        blocked_blueprint["unknowns"] = [
            {
                "unknownId": "U_ENTRY_BUY",
                "path": "$.entry.buy.rules[0]",
                "description": "ยังไม่ทราบนิยามจุดเข้า Buy ที่ตรวจสอบซ้ำได้",
                "blocksExecution": True,
            }
        ]
        blocked_blueprint["conflicts"] = [
            {
                "conflictId": "C_ENTRY_BUY",
                "paths": ["$.entry.buy.rules[0]"],
                "description": "หลักฐานสองแหล่งให้นิยามจุดเข้าไม่ตรงกัน",
                "resolutionStatus": "unresolved",
                "sourceRefs": ["S1", "S2"],
            }
        ]
        blocked_blueprint["completeness"].update(
            {
                "status": "needs_clarification",
                "score": 60,
                "eaHandoffAllowed": False,
                "deterministicBacktestAllowed": False,
                "blockingIssues": [
                    {
                        "code": "ENTRY_UNKNOWN_CONFLICT",
                        "path": "$.entry.buy.rules[0]",
                        "messageTh": "กฎเข้า Buy ยังไม่ชัดเจน",
                        "questionTh": "ยืนยันนิยามกฎเข้า Buy ที่ถูกต้อง",
                    }
                ],
                "unknownPaths": ["$.entry.buy.rules[0]"],
                "conflictPaths": ["$.entry.buy.rules[0]"],
            }
        )
        self.replace_blueprint(newer, blocked_blueprint)
        self.persist_report_and_mission(newer)

        with mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_status",
            return_value={"configured": True, "mode": "access_token"},
        ):
            catalog = self.bridge._ea_factory_source_catalog(
                state=self.bridge._empty_ea_factory_state(),
                reports=[newer, older],
                missions=[self.mission(newer), self.mission(older)],
            )
        self.assertFalse(
            any(
                row.get("recordId") == old_rows[0]["record_id"]
                and row.get("buildReady") is True
                for row in catalog
            ),
            "A newer needs-clarification revision must revoke an older cached ready source.",
        )

    def test_missing_compact_cell_fails_closed_before_build(self) -> None:
        self.configure_active_sheet()
        report = self.deep_report()
        rows = self.confirmed_deep_rows(report)
        missing_cell = copy.deepcopy(rows[0])
        missing_cell["exit_rules"] = ""
        with self.assertRaisesRegex(
            self.bridge.RequestError,
            "incomplete Strategy Brief row",
        ):
            self.bridge._ea_factory_deep_research_records(
                [missing_cell],
                source_key="missing-cell",
                strict=True,
            )

    def test_compact_brief_allows_user_to_choose_mt4_or_mt5_at_build_time(self) -> None:
        self.configure_active_sheet()
        report = self.deep_report()
        rows = self.confirmed_deep_rows(report)
        record = self.bridge._ea_factory_deep_research_records(
            rows,
            source_key="compact-user-platform-choice",
            strict=True,
        )[0]
        self.assertTrue(record["buildReady"])

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
                return_value=[record],
            ),
        ):
            created = self.bridge.create_ea_factory_build(
                {
                    "sourceRecordId": record["sourceRecordId"],
                    "platform": "mt5",
                    "idempotencyKey": "compact-brief-mt5-choice",
                }
            )
        self.assertTrue(created["ok"])
        self.assertEqual(created["build"]["platform"], "mt5")

    def test_legacy_predicate_shape_does_not_block_compact_prose_handoff(self) -> None:
        self.configure_active_sheet()
        report = self.deep_report()
        blueprint = ready_blueprint()
        blueprint["entry"]["buy"]["rules"][0]["expression"] = {
            "op": "break_above",
            "left": {"kind": "indicator", "ref": "ema_fast", "shift": 1},
            "right": {"kind": "indicator", "ref": "ema_slow", "shift": 1},
        }
        self.replace_blueprint(report, blueprint)
        self.persist_report_and_mission(report)

        with mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_status",
            return_value={"configured": True, "mode": "access_token"},
        ):
            confirmation = self.bridge.report_read_model_item(report)["eaResearch"][
                "confirmation"
            ]
        self.assertTrue(confirmation["canConfirm"])
        self.assertTrue(confirmation["factoryCompatibility"]["ready"])
        self.assertEqual(
            confirmation["factoryCompatibility"]["contract"],
            self.bridge.EA_STRATEGY_BRIEF_SCHEMA_VERSION,
        )

        rows, _legacy = self.bridge._research_sheet_deep_rows(report)
        records = self.bridge._ea_factory_deep_research_records(
            rows,
            source_key="compact-prose-not-typed-predicate",
            strict=True,
        )
        self.assertEqual(len(records), 1)
        self.assertTrue(records[0]["buildReady"])

    def test_factory_http_read_model_preserves_long_compact_entry_rules_and_digest(self) -> None:
        """The public JSON must preserve digest-bound Strategy Brief prose losslessly."""
        self.configure_active_sheet()
        report = self.deep_report()
        prefix = "BUY เมื่อแท่งปิดยืนยัน EMA cross; SELL ใช้เงื่อนไขกลับกัน; "
        long_entry_rules = (
            prefix + ("ตรวจ spread และไม่เปิดซ้ำในแท่งเดียว; " * 150)
        ).strip()
        self.assertGreater(len(long_entry_rules), 5000)
        self.assertLessEqual(len(long_entry_rules), 8000)
        report["metrics"]["strategyBrief"]["entryRules"] = long_entry_rules
        report["metrics"]["briefDigest"] = self.bridge.compute_strategy_brief_digest(
            report["metrics"]["strategyBrief"]
        )
        report["metrics"]["sourceDigest"] = report["metrics"]["briefDigest"]
        rows = self.confirmed_deep_rows(report)
        record = self.bridge._ea_factory_deep_research_records(
            rows,
            source_key="long-entry-rules-http-round-trip",
            strict=True,
        )[0]
        expected_brief = copy.deepcopy(record["strategyBrief"])
        expected_digest = record["strategyBriefDigest"]
        expected_content = {
            sheet_name: expected_brief[camel_name]
            for sheet_name, camel_name
            in self.bridge.EA_STRATEGY_BRIEF_SHEET_TO_CAMEL.items()
        }
        self.assertEqual(
            self.bridge._ea_factory_sheet_strategy_brief_digest(
                record["recordId"],
                expected_content,
            ),
            expected_digest,
        )

        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=self.bridge._empty_ea_factory_state(),
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_ea_factory_source_catalog",
                return_value=[record],
            ),
            mock.patch.object(
                self.bridge,
                "research_sheet_hub_read_model",
                return_value={"configured": False, "consumers": []},
            ),
            mock.patch.object(
                self.bridge,
                "peek_metatrader_status",
                return_value={"status": "not_checked", "candidates": []},
            ),
            mock.patch.object(
                self.bridge,
                "_metatrader_selection_read_model",
                return_value={
                    "candidates": [],
                    "selectedCandidate": None,
                    "adapterReady": False,
                },
            ),
        ):
            server = self.bridge.BridgeHTTPServer(
                ("127.0.0.1", 0),
                self.bridge.BridgeHandler,
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                connection = http.client.HTTPConnection(
                    "127.0.0.1",
                    server.server_port,
                    timeout=5,
                )
                connection.request(
                    "GET",
                    "/api/props/right_server_racks/ea-factory",
                )
                response = connection.getresponse()
                body = json.loads(response.read().decode("utf-8"))
                connection.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

        self.assertEqual(response.status, 200)
        public_record = body["eaFactory"]["sourceCatalog"]["records"][0]
        public_research = public_record["eaResearch"]
        returned_brief = public_research["strategyBrief"]
        self.assertEqual(
            returned_brief["entryRules"].encode("utf-8"),
            long_entry_rules.encode("utf-8"),
        )
        self.assertEqual(returned_brief, expected_brief)
        self.assertIsNone(public_research.get("blueprint"))
        self.assertEqual(public_research["briefDigest"], expected_digest)
        self.assertEqual(
            self.bridge._ea_factory_sheet_strategy_brief_digest(
                public_record["recordId"],
                {
                    sheet_name: returned_brief[camel_name]
                    for sheet_name, camel_name
                    in self.bridge.EA_STRATEGY_BRIEF_SHEET_TO_CAMEL.items()
                },
            ),
            expected_digest,
        )
        self.assertTrue(public_research["digestMatched"])
        self.assertTrue(public_record["buildReady"])

    def test_public_http_evidence_stays_in_backend_not_compact_sheet_columns(self) -> None:
        """Evidence stays in the report ledger while learner-facing A-J stays compact."""
        self.configure_active_sheet()
        report = self.deep_report()
        http_urls = [
            "http://www.investopedia.com/terms/m/movingaverage.asp",
            "http://www.tradingview.com/support/solutions/43000592270-moving-average/",
        ]
        report["metrics"]["strategyBrief"]["sourceLinks"] = http_urls
        report["metrics"]["briefDigest"] = self.bridge.compute_strategy_brief_digest(
            report["metrics"]["strategyBrief"]
        )
        report["metrics"]["sourceDigest"] = report["metrics"]["briefDigest"]
        backend_research = self.bridge.report_read_model_item(report)["eaResearch"]
        self.assertEqual(
            backend_research["strategyBrief"]["sourceLinks"],
            http_urls,
        )

        rows = self.confirmed_deep_rows(report)
        self.assertEqual(len(rows), 1)
        self.assertEqual(set(rows[0]), set(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS))
        records = self.bridge._ea_factory_deep_research_records(
            rows,
            source_key="public-http-evidence-round-trip",
            strict=True,
        )
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["sourceUrls"], [])
        self.assertEqual(record["downstream"]["source_urls"], "")
        self.assertNotIn("source_urls", record["missingCoreFields"])
        self.assertNotIn("missing_source_urls", record["readinessIssues"])
        self.assertTrue(record["buildReady"])


if __name__ == "__main__":
    unittest.main()
