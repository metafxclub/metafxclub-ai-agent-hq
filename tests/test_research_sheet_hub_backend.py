from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "backend" / "local-runner" / "bridge_server.py"
SHEET_ID = "193dlWvLqVzsstF5qStjBOT4h-8wiQMhnXXKkydPRp5A"
OTHER_SHEET_ID = "1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "research_sheet_hub_backend_test_bridge",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeJsonResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, _limit: int = -1) -> bytes:
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")


class StopAfterEaFactoryValidation(RuntimeError):
    pass


class ResearchSheetHubBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()
        cls.hub = cls.bridge.google_sheet_hub

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp.name)
        self.runtime = self.temp_path / "runtime"
        self.reports = self.runtime / "reports"
        self.reports.mkdir(parents=True)
        self.stack = ExitStack()
        replacements = {
            "RUNTIME_DIR": self.runtime,
            "RUNTIME_REPORTS_DIR": self.reports,
            "DASHBOARD_WORKFLOW_SETTINGS_PATH": self.runtime / "dashboard-workflow-settings.json",
            "RESEARCH_SHEET_OUTBOX_PATH": self.runtime / "research-sheet-outbox.json",
            "RESEARCH_SHEET_CACHE_PATH": self.runtime / "research-sheet-cache.json",
            "AUDIT_PATH": self.runtime / "bridge-audit.jsonl",
        }
        for name, value in replacements.items():
            self.stack.enter_context(patch.object(self.bridge, name, value))

    def tearDown(self) -> None:
        self.stack.close()
        self.temp.cleanup()

    def write_settings(self, payload: dict) -> None:
        self.bridge.write_json(self.bridge.DASHBOARD_WORKFLOW_SETTINGS_PATH, payload)

    def configure_hub(
        self,
        *,
        revision: int = 3,
        status: str = "read_ready_write_unverified",
        active: bool = True,
    ) -> None:
        settings = self.bridge._default_dashboard_workflow_settings()
        settings["researchSheetHub"].update(
            {
                "sheetId": SHEET_ID,
                "canonicalUrl": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}",
                "configRevision": revision,
                "active": active,
                "activeConfigRevision": revision if active else None,
                "activationConfirmedAt": (
                    "2026-08-27T00:01:00Z" if active else None
                ),
                "savedAt": "2026-08-27T00:00:00Z",
                "lastVerifiedAt": "2026-08-27T00:01:00Z",
                "lastVerificationStatus": status,
                "consumerChecks": {
                    contract["consumerId"]: {
                        "tabName": contract["tabName"],
                        "status": "ready",
                        "readReady": True,
                        "configRevision": revision,
                    }
                    for contract in self.bridge.RESEARCH_SHEET_HUB_PROP_TABS.values()
                },
            }
        )
        self.write_settings(settings)

    def ready_probe(self, *, title: str = "Metafxclub System Research Hub") -> dict:
        consumers = {}
        for consumer_id, contract in self.bridge._research_sheet_tab_contracts().items():
            consumers[consumer_id] = {
                "tabName": contract["tabName"],
                "status": "ready",
                "readReady": True,
                "probeReady": True,
                "columnCount": len(contract["requiredHeaders"]),
                "missingHeaders": [],
                "duplicateHeaders": [],
                "rowCount": 1,
                "probeEvidence": {
                    "kind": "key_column_read",
                    "range": "A2:A10000",
                    "confirmed": True,
                    "rowsScanned": 1,
                    "nonEmptyKeys": 1,
                    "duplicateKeyCount": 0,
                },
            }
        return {
            "title": title,
            "consumers": consumers,
            "readReady": True,
            "writeReady": True,
            "probeReady": True,
        }

    def candidate_cache(self, sheet_id: str, revision: int) -> dict:
        # Keep cache fixtures fresh relative to the test run.  A fixed calendar
        # date eventually crosses RESEARCH_SHEET_CACHE_MAX_AGE_SECONDS and makes
        # otherwise valid re-verification tests fail only because time passed.
        observed_at = self.bridge.utc_now()
        return {
            "schemaVersion": "research-sheet-cache-v1",
            "sheetDigest": self.bridge.payload_digest(
                "research-sheet-id-v1", sheet_id
            ),
            "configRevision": revision,
            "consumers": {
                consumer_id: {
                    "tabName": contract["tabName"],
                    "rowCount": 1,
                    "cachedRowCount": 1,
                    "rows": [],
                    "observedAt": observed_at,
                }
                for consumer_id, contract in self.bridge._research_sheet_tab_contracts().items()
            },
            "updatedAt": observed_at,
        }

    def inspect_and_activate(
        self,
        sheet_id: str,
        *,
        idempotency_key: str,
    ) -> tuple[dict, dict]:
        preview = self.bridge.inspect_research_sheet_hub_candidate(
            {"googleSheetUrlOrId": sheet_id}
        )
        verification = preview["verificationPreview"]
        activated = self.bridge.activate_research_sheet_hub(
            {
                "verificationToken": verification["verificationToken"],
                "confirmActivate": True,
                "expectedConfigRevision": verification["baseConfigRevision"],
                "idempotencyKey": idempotency_key,
            }
        )
        return preview, activated

    def test_reference_normalization_is_canonical_and_rejects_secret_or_wrong_origin(self) -> None:
        normalize = self.bridge._normalize_google_sheet_reference
        expected = {
            "sheetId": SHEET_ID,
            "canonicalUrl": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}",
        }
        self.assertEqual(normalize(SHEET_ID), expected)
        self.assertEqual(
            normalize(
                f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?gid=123#gid=123"
            ),
            expected,
        )
        rejected = [
            f"http://docs.google.com/spreadsheets/d/{SHEET_ID}/edit",
            f"https://evil.example/spreadsheets/d/{SHEET_ID}/edit",
            f"https://user:pass@docs.google.com/spreadsheets/d/{SHEET_ID}/edit",
            f"https://docs.google.com:444/spreadsheets/d/{SHEET_ID}/edit",
            f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?access_token=secret",
            "short-id",
        ]
        for value in rejected:
            with self.subTest(value=value), self.assertRaises(self.bridge.RequestError) as caught:
                normalize(value)
            self.assertEqual(caught.exception.status, 422)

    def test_inspection_frontend_result_restores_only_ready_verification_capability(self) -> None:
        token = "A" * 43
        payload = {
            "ok": True,
            "kind": "research_sheet_hub_inspected",
            "verificationPreview": {
                "readyForConfirmation": True,
                "verificationToken": token,
                "totalConsumerCount": 3,
                "verifiedConsumerCount": 3,
            },
            "accessToken": "must-not-leak",
            "refreshToken": "must-not-leak",
            "clientSecret": "must-not-leak",
            "nested": {"verificationToken": "must-not-leak"},
        }

        result = self.bridge.research_sheet_inspection_frontend_result(payload)

        self.assertEqual(result["verificationPreview"]["verificationToken"], token)
        self.assertEqual(result["accessToken"], "[REDACTED_SECRET]")
        self.assertEqual(result["refreshToken"], "[REDACTED_SECRET]")
        self.assertEqual(result["clientSecret"], "[REDACTED_SECRET]")
        self.assertEqual(
            result["nested"]["verificationToken"],
            "[REDACTED_SECRET]",
        )

        unready = copy.deepcopy(payload)
        unready["verificationPreview"]["readyForConfirmation"] = False
        rejected = self.bridge.research_sheet_inspection_frontend_result(unready)
        self.assertFalse(rejected["verificationPreview"]["readyForConfirmation"])
        self.assertIsNone(rejected["verificationPreview"]["verificationToken"])

        malformed = copy.deepcopy(payload)
        malformed["verificationPreview"]["verificationToken"] = "too-short"
        rejected = self.bridge.research_sheet_inspection_frontend_result(malformed)
        self.assertFalse(rejected["verificationPreview"]["readyForConfirmation"])
        self.assertIsNone(rejected["verificationPreview"]["verificationToken"])

        self.assertEqual(
            self.bridge.sanitize_json_value({"verificationToken": token})[
                "verificationToken"
            ],
            "[REDACTED_SECRET]",
        )

    def test_legacy_radar_setting_migrates_to_persistent_safe_central_reference(self) -> None:
        self.write_settings(
            {
                "version": "dashboard-workflow-settings-v2",
                "indicatorScoutSheet": {
                    "sheetId": SHEET_ID,
                    "canonicalUrl": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit",
                    "tabName": "old-custom-tab",
                    "savedAt": "2026-08-26T10:00:00Z",
                },
            }
        )
        with patch.object(
            self.hub,
            "credential_status",
            return_value={
                "configured": False,
                "mode": "not_configured",
                "partialConfiguration": False,
                "credentialsAcceptedByFrontend": False,
            },
        ):
            settings = self.bridge.load_dashboard_workflow_settings()
            model = self.bridge.research_sheet_hub_read_model(settings)

        self.assertEqual(settings["researchSheetHub"]["sheetId"], SHEET_ID)
        self.assertEqual(settings["researchSheetHub"]["configRevision"], 1)
        self.assertEqual(
            settings["indicatorScoutSheet"]["tabName"],
            "Indicator_EA_Tool",
        )
        self.assertEqual(model["sheetReferenceMasked"], "193dlW…Rp5A")
        self.assertEqual(model["sheetId"], SHEET_ID)
        self.assertEqual(
            model["canonicalUrl"],
            f"https://docs.google.com/spreadsheets/d/{SHEET_ID}",
        )
        self.assertEqual(model["sheetDisplayValue"], SHEET_ID)
        self.assertEqual(model["adapterStatus"], "activation_required")
        self.assertEqual(model["applyPhase"], "awaiting_confirmation")
        self.assertEqual(model["applyStatus"], "activation_required")
        self.assertFalse(model["active"])
        self.assertFalse(model["allConsumersApplied"])
        self.assertEqual(model["appliedConsumerCount"], 0)
        self.assertFalse(model["credentialsAcceptedByFrontend"])
        self.assertTrue(model["rawSheetIdExposed"])
        self.assertFalse(model["sheetIdIsCredential"])
        self.assertFalse(model["oauthSecretsExposed"])
        for consumer in model["consumers"]:
            self.assertEqual(consumer["sheetId"], SHEET_ID)
            self.assertEqual(consumer["configRevision"], 1)
            self.assertFalse(consumer["configurationApplied"])

    def test_exact_three_consumers_and_two_explicit_exclusions(self) -> None:
        expected = {
            "codex_mcp_portal": ("worldSystem", "World_System", "read_write"),
            "left_server_racks": ("deepResearch", "Deep_Research", "read_write"),
            "left_audit_crystals": ("indicatorEaTool", "Indicator_EA_Tool", "read_write"),
        }
        observed = {
            prop_id: (
                contract["consumerId"],
                contract["tabName"],
                contract["mode"],
            )
            for prop_id, contract in self.bridge.RESEARCH_SHEET_HUB_PROP_TABS.items()
        }
        self.assertEqual(observed, expected)
        self.assertEqual(
            self.bridge.RESEARCH_SHEET_HUB_EXCLUDED_PROP_IDS,
            ("right_tool_console", "terminal_workstation"),
        )
        for excluded in self.bridge.RESEARCH_SHEET_HUB_EXCLUDED_PROP_IDS:
            self.assertNotIn(excluded, self.bridge.RESEARCH_SHEET_HUB_PROP_TABS)

    def test_activation_is_idempotent_persists_id_and_never_accepts_frontend_credentials(self) -> None:
        inspection = self.ready_probe()
        credential = {
            "configured": True,
            "mode": "access_token",
            "partialConfiguration": False,
            "credentialsAcceptedByFrontend": False,
        }
        with (
            patch.object(self.hub, "credential_status", return_value=credential),
            patch.object(self.hub, "probe_tabs", return_value=inspection) as probe,
            patch.object(
                self.bridge,
                "_refresh_research_sheet_cache",
                side_effect=lambda sheet_id, revision, _checks, **_kwargs: self.candidate_cache(
                    sheet_id, revision
                ),
            ),
            patch.object(
                self.bridge,
                "_research_sheet_backfill_recent_reports",
                return_value={"queued": 0, "flush": {"processed": 0, "synced": 0}},
            ),
        ):
            preview, first = self.inspect_and_activate(
                SHEET_ID,
                idempotency_key="hub-activate-001",
            )
            activation_payload = {
                "verificationToken": preview["verificationPreview"]["verificationToken"],
                "confirmActivate": True,
                "expectedConfigRevision": 0,
                "idempotencyKey": "hub-activate-001",
            }
            replay = self.bridge.activate_research_sheet_hub(activation_payload)
            other_preview = self.bridge.inspect_research_sheet_hub_candidate(
                {"googleSheetUrlOrId": OTHER_SHEET_ID}
            )
            with self.assertRaises(self.bridge.RequestError) as conflict:
                self.bridge.activate_research_sheet_hub({
                    "verificationToken": other_preview["verificationPreview"]["verificationToken"],
                    "confirmActivate": True,
                    "expectedConfigRevision": 1,
                    "idempotencyKey": "hub-activate-001",
                })

        self.assertEqual(probe.call_count, 3)
        self.assertEqual(first["kind"], "research_sheet_hub_activated")
        self.assertFalse(first["idempotentReplay"])
        self.assertEqual(replay["kind"], "research_sheet_hub_activation_replayed")
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(first["researchSheet"]["configRevision"], 1)
        self.assertEqual(replay["researchSheet"]["configRevision"], 1)
        self.assertEqual(first["researchSheet"]["sheetId"], SHEET_ID)
        self.assertEqual(replay["researchSheet"]["sheetId"], SHEET_ID)
        self.assertEqual(first["researchSheet"]["applyPhase"], "completed")
        self.assertEqual(first["researchSheet"]["applyStatus"], "ready")
        self.assertEqual(
            first["researchSheet"]["verificationStatus"],
            "read_ready_write_unverified",
        )
        self.assertTrue(first["researchSheet"]["allConsumersVerified"])
        self.assertTrue(first["researchSheet"]["active"])
        self.assertEqual(first["researchSheet"]["activeConfigRevision"], 1)
        self.assertEqual(len(first["researchSheet"]["linkedSystems"]), 4)
        reloaded = self.bridge.research_sheet_hub_read_model()
        self.assertEqual(reloaded["sheetId"], SHEET_ID)
        self.assertEqual(reloaded["sheetDisplayValue"], SHEET_ID)
        self.assertEqual(conflict.exception.status, 409)

        audit = self.bridge.AUDIT_PATH.read_text(encoding="utf-8")
        self.assertNotIn(SHEET_ID, audit)
        self.assertNotIn("access_token", audit.lower())
        for forbidden in ("accessToken", "credential", "clientSecret", "refreshToken"):
            with self.subTest(forbidden=forbidden), self.assertRaises(
                self.bridge.RequestError
            ) as rejected:
                self.bridge.inspect_research_sheet_hub_candidate(
                    {"googleSheetUrlOrId": SHEET_ID, forbidden: "secret"}
                )
            self.assertEqual(rejected.exception.status, 422)

    def test_auth_required_stops_before_any_network_write(self) -> None:
        network = Mock()
        with self.assertRaises(self.hub.GoogleSheetHubError) as caught:
            self.hub.upsert_row(
                SHEET_ID,
                "World_System",
                "discovery_id",
                "D-1",
                {"discovery_id": "D-1"},
                environ={},
                open_url=network,
            )
        self.assertEqual(caught.exception.code, "auth_required")
        network.assert_not_called()

        self.configure_hub()
        self.bridge._save_research_sheet_outbox_unlocked(
            {
                "items": [
                    {
                        "id": "sheet-sync-auth-test",
                        "status": "pending",
                        "configRevision": 3,
                    }
                ]
            }
        )
        with (
            patch.object(
                self.hub,
                "credential_status",
                return_value={"configured": False, "mode": "not_configured"},
            ),
            patch.object(self.hub, "upsert_row") as upsert,
        ):
            result = self.bridge._flush_research_sheet_outbox(max_items=20)
        self.assertEqual(
            result,
            {"processed": 0, "synced": 0, "reason": "auth_required"},
        )
        upsert.assert_not_called()

    def test_inspect_is_non_mutating_then_explicit_activation_becomes_ready(self) -> None:
        inspection = self.ready_probe()
        credential = {"configured": True, "mode": "access_token"}
        with (
            patch.object(self.hub, "credential_status", return_value=credential),
            patch.object(self.hub, "probe_tabs", return_value=inspection),
            patch.object(
                self.bridge,
                "_refresh_research_sheet_cache",
                side_effect=lambda sheet_id, revision, _checks, **_kwargs: self.candidate_cache(
                    sheet_id, revision
                ),
            ),
            patch.object(
                self.bridge,
                "_research_sheet_backfill_recent_reports",
                return_value={"queued": 0, "flush": {"processed": 0, "synced": 0}},
            ),
        ):
            preview = self.bridge.inspect_research_sheet_hub_candidate(
                {"googleSheetUrlOrId": SHEET_ID}
            )
            self.assertFalse(self.bridge.DASHBOARD_WORKFLOW_SETTINGS_PATH.exists())
            self.assertFalse(self.bridge.RESEARCH_SHEET_CACHE_PATH.exists())
            self.assertIsNone(preview["researchSheet"]["sheetId"])
            verification = preview["verificationPreview"]
            self.assertEqual(verification["status"], "ready")
            self.assertTrue(verification["readyForConfirmation"])
            self.assertEqual(verification["verifiedConsumerCount"], 3)
            self.assertTrue(verification["verificationToken"])
            result = self.bridge.activate_research_sheet_hub({
                "verificationToken": verification["verificationToken"],
                "confirmActivate": True,
                "expectedConfigRevision": verification["baseConfigRevision"],
                "idempotencyKey": "phase-check-001",
            })

        applied = result["researchSheet"]
        self.assertEqual(applied["applyPhase"], "completed")
        self.assertEqual(applied["applyStatus"], "ready")
        self.assertEqual(applied["verifiedConsumerCount"], 3)
        self.assertTrue(applied["allConsumersVerified"])
        self.assertIsNotNone(applied["verificationStartedAt"])
        self.assertIsNotNone(applied["verificationCompletedAt"])

    def test_failed_inspect_reports_auth_or_schema_without_touching_active_sheet(self) -> None:
        self.configure_hub(revision=4)
        original_settings = self.bridge.DASHBOARD_WORKFLOW_SETTINGS_PATH.read_bytes()
        auth_error = self.hub.GoogleSheetHubError(
            "auth_required",
            "Backend Google OAuth is required.",
            401,
        )
        with (
            patch.object(
                self.hub,
                "credential_status",
                return_value={"configured": False, "mode": "not_configured"},
            ),
            patch.object(self.hub, "probe_tabs", side_effect=auth_error),
        ):
            auth_result = self.bridge.inspect_research_sheet_hub_candidate(
                {"googleSheetUrlOrId": OTHER_SHEET_ID}
            )
        self.assertEqual(auth_result["verificationPreview"]["status"], "auth_required")
        self.assertFalse(auth_result["verificationPreview"]["readyForConfirmation"])
        self.assertIsNone(auth_result["verificationPreview"]["verificationToken"])
        self.assertEqual(auth_result["researchSheet"]["sheetId"], SHEET_ID)
        self.assertTrue(auth_result["researchSheet"]["active"])
        self.assertEqual(
            self.bridge.DASHBOARD_WORKFLOW_SETTINGS_PATH.read_bytes(),
            original_settings,
        )

        mismatch_checks = {
            consumer_id: {
                "tabName": contract["tabName"],
                "status": "schema_mismatch",
                "readReady": False,
                "probeReady": False,
                "missingHeaders": [contract["requiredHeaders"][0]],
            }
            for consumer_id, contract in self.bridge._research_sheet_tab_contracts().items()
        }
        with (
            patch.object(
                self.hub,
                "credential_status",
                return_value={"configured": True, "mode": "access_token"},
            ),
            patch.object(
                self.hub,
                "probe_tabs",
                return_value={
                    "title": "Wrong schema",
                    "consumers": mismatch_checks,
                    "readReady": False,
                    "probeReady": False,
                },
            ),
        ):
            mismatch_result = self.bridge.inspect_research_sheet_hub_candidate(
                {"googleSheetUrlOrId": OTHER_SHEET_ID}
            )
        self.assertEqual(mismatch_result["verificationPreview"]["status"], "schema_mismatch")
        self.assertEqual(mismatch_result["verificationPreview"]["verifiedConsumerCount"], 0)
        self.assertEqual(mismatch_result["researchSheet"]["sheetId"], SHEET_ID)
        self.assertEqual(
            self.bridge.DASHBOARD_WORKFLOW_SETTINGS_PATH.read_bytes(),
            original_settings,
        )

    def test_changing_sheet_invalidates_cache_outbox_and_all_consumers(self) -> None:
        self.configure_hub(revision=4)
        self.bridge.write_json(
            self.bridge.RESEARCH_SHEET_CACHE_PATH,
            {
                "schemaVersion": "research-sheet-cache-v1",
                "sheetDigest": self.bridge.payload_digest(
                    "research-sheet-id-v1", SHEET_ID
                ),
                "configRevision": 4,
                "consumers": {
                    "worldSystem": {"rows": [{"discovery_id": "old-row"}]}
                },
                "updatedAt": "2026-08-27T00:00:00Z",
            },
        )
        self.bridge._save_research_sheet_outbox_unlocked(
            {
                "items": [
                    {
                        "id": "old-sheet-work",
                        "consumerId": "worldSystem",
                        "configRevision": 4,
                        "status": "pending",
                    }
                ]
            }
        )
        inspection = self.ready_probe(title="Replacement research hub")
        with (
            patch.object(
                self.hub,
                "credential_status",
                return_value={"configured": True, "mode": "access_token"},
            ),
            patch.object(self.hub, "probe_tabs", return_value=inspection),
            patch.object(
                self.bridge,
                "_refresh_research_sheet_cache",
                side_effect=lambda sheet_id, revision, _checks, **_kwargs: self.candidate_cache(
                    sheet_id, revision
                ),
            ),
            patch.object(
                self.bridge,
                "_research_sheet_backfill_recent_reports",
                return_value={"queued": 0, "flush": {"processed": 0, "synced": 0}},
            ),
        ):
            _preview, activation = self.inspect_and_activate(
                OTHER_SHEET_ID,
                idempotency_key="change-sheet-001",
            )
            changed = activation["researchSheet"]

        self.assertEqual(changed["sheetId"], OTHER_SHEET_ID)
        self.assertEqual(changed["configRevision"], 5)
        self.assertEqual(changed["appliedConsumerCount"], 3)
        self.assertTrue(changed["allConsumersApplied"])
        for consumer in changed["consumers"]:
            self.assertEqual(consumer["sheetId"], OTHER_SHEET_ID)
            self.assertEqual(consumer["configRevision"], 5)
        cache = self.bridge._load_research_sheet_cache_unlocked()
        self.assertEqual(
            cache["sheetDigest"],
            self.bridge.payload_digest("research-sheet-id-v1", OTHER_SHEET_ID),
        )
        self.assertEqual(cache["configRevision"], 5)
        self.assertEqual(set(cache["consumers"]), {"worldSystem", "deepResearch", "indicatorEaTool"})
        self.assertEqual(
            self.bridge._load_research_sheet_outbox_unlocked()["items"], []
        )

    def test_authenticated_inspect_checks_all_three_fixed_tabs_without_leaking_token(self) -> None:
        contracts = self.bridge._research_sheet_tab_contracts()
        response_payloads = [
            {
                "spreadsheetId": SHEET_ID,
                "properties": {"title": "Metafxclub System Research Hub"},
                "sheets": [
                    {"properties": {"title": contract["tabName"]}}
                    for contract in contracts.values()
                ],
            },
            *[
                {"values": [contract["requiredHeaders"]]}
                for contract in contracts.values()
            ],
        ]
        calls = []

        def open_url(request, timeout):
            calls.append(
                {
                    "url": request.full_url,
                    "method": request.get_method(),
                    "authorization": request.get_header("Authorization"),
                    "timeout": timeout,
                }
            )
            return FakeJsonResponse(response_payloads[len(calls) - 1])

        token = "test-token-that-must-not-be-returned"
        result = self.hub.inspect_tabs(
            SHEET_ID,
            contracts,
            environ={"METAFX_GOOGLE_SHEETS_ACCESS_TOKEN": token},
            open_url=open_url,
        )
        self.assertEqual(len(calls), 4)
        self.assertTrue(all(call["method"] == "GET" for call in calls))
        self.assertTrue(
            all(call["authorization"] == f"Bearer {token}" for call in calls)
        )
        self.assertEqual(result["title"], "Metafxclub System Research Hub")
        self.assertTrue(result["readReady"])
        self.assertTrue(result["writeReady"])
        self.assertEqual(set(result["consumers"]), set(contracts))
        self.assertNotIn(token, json.dumps(result, ensure_ascii=False))

    def test_google_sheet_upsert_reads_back_and_updates_same_key_without_duplicate(self) -> None:
        state = {"rows": [["record_id", "manual_note", "system_name", "formula_total"]]}
        requests = []

        def open_url(request, timeout):
            method = request.get_method()
            decoded_url = unquote(request.full_url)
            requests.append((method, decoded_url))
            if method == "GET" and "!1:1" in decoded_url:
                return FakeJsonResponse({"values": [state["rows"][0]]})
            if method == "GET" and "!A2:A10000" in decoded_url:
                return FakeJsonResponse(
                    {"values": [[row[0]] for row in state["rows"][1:] if row]}
                )
            if method == "POST" and decoded_url.endswith("/values:batchUpdate"):
                body = json.loads(request.data.decode("utf-8"))
                self.assertEqual(body["valueInputOption"], "RAW")
                self.assertTrue(body["includeValuesInResponse"])
                responses = []
                for value_range in body["data"]:
                    match = re.search(
                        r"!([A-Z]+)(\d+):([A-Z]+)(\d+)$",
                        value_range["range"],
                    )
                    self.assertIsNotNone(match)
                    start_column, row_text, end_column, end_row_text = match.groups()
                    self.assertEqual(row_text, end_row_text)
                    row_number = int(row_text)
                    while len(state["rows"]) < row_number:
                        state["rows"].append([""] * len(state["rows"][0]))
                    start_index = ord(start_column) - ord("A")
                    end_index = ord(end_column) - ord("A")
                    values = value_range["values"][0]
                    self.assertEqual(len(values), end_index - start_index + 1)
                    state["rows"][row_number - 1][start_index : end_index + 1] = values
                    responses.append({"updatedRows": 1})
                return FakeJsonResponse(
                    {"responses": responses}
                )
            if method == "GET" and "!A2:D2" in decoded_url:
                return FakeJsonResponse({"values": [state["rows"][1]]})
            raise AssertionError(f"Unexpected Google API request: {method} {decoded_url}")

        env = {"METAFX_GOOGLE_SHEETS_ACCESS_TOKEN": "backend-only-test-token"}
        first = self.hub.upsert_row(
            SHEET_ID,
            "Test_Tab",
            "record_id",
            "REC-1",
            {"record_id": "REC-1", "system_name": "First"},
            environ=env,
            open_url=open_url,
        )
        state["rows"][1][1] = "manual value must survive"
        state["rows"][1][3] = "=LEN(A2)"
        second = self.hub.upsert_row(
            SHEET_ID,
            "Test_Tab",
            "record_id",
            "REC-1",
            {"record_id": "REC-1", "system_name": "Updated"},
            environ=env,
            open_url=open_url,
        )
        self.assertEqual(first["rowNumber"], 2)
        self.assertTrue(first["readBackVerified"])
        self.assertEqual(second["rowNumber"], 2)
        self.assertTrue(second["readBackVerified"])
        self.assertEqual(
            state["rows"],
            [
                ["record_id", "manual_note", "system_name", "formula_total"],
                ["REC-1", "manual value must survive", "Updated", "=LEN(A2)"],
            ],
        )
        self.assertEqual([method for method, _url in requests].count("POST"), 2)
        self.assertEqual([method for method, _url in requests].count("PUT"), 0)
        batch_requests = [
            url for method, url in requests
            if method == "POST" and url.endswith("/values:batchUpdate")
        ]
        self.assertEqual(len(batch_requests), 2)

    def test_google_sheet_upsert_rejects_existing_duplicate_keys_before_write(self) -> None:
        calls = []

        def open_url(request, timeout):
            calls.append(request.get_method())
            decoded_url = unquote(request.full_url)
            if "!1:1" in decoded_url:
                return FakeJsonResponse({"values": [["record_id", "system_name"]]})
            if "!A2:A10000" in decoded_url:
                return FakeJsonResponse({"values": [["REC-DUP"], ["REC-DUP"]]})
            raise AssertionError(f"Unexpected Google API request: {decoded_url}")

        with self.assertRaises(self.hub.GoogleSheetHubError) as caught:
            self.hub.upsert_row(
                SHEET_ID,
                "Test_Tab",
                "record_id",
                "REC-DUP",
                {"record_id": "REC-DUP", "system_name": "Updated"},
                environ={"METAFX_GOOGLE_SHEETS_ACCESS_TOKEN": "backend-test-token"},
                open_url=open_url,
            )
        self.assertEqual(caught.exception.code, "duplicate_key_conflict")
        self.assertEqual(calls, ["GET", "GET"])

    def test_verified_reports_queue_only_three_physical_sheet_tabs(self) -> None:
        self.configure_hub(revision=7)
        world = self._world_report()
        deep = self._deep_report()
        radar = self._radar_report()

        self.assertEqual(
            self.bridge._research_sheet_queue_report(world, flush=False)["queued"],
            3,
        )
        self.assertEqual(
            self.bridge._research_sheet_queue_report(deep, flush=False)["queued"],
            1,
        )
        self.assertEqual(
            self.bridge._research_sheet_queue_report(radar, flush=False)["queued"],
            6,
        )
        store = self.bridge._load_research_sheet_outbox_unlocked()
        items = store["items"]
        counts = {}
        contracts = self.bridge._research_sheet_tab_contracts()
        for item in items:
            counts[item["consumerId"]] = counts.get(item["consumerId"], 0) + 1
            self.assertEqual(item["configRevision"], 7)
            self.assertEqual(item["status"], "pending")
            self.assertTrue(item["recordKey"])
            self.assertLessEqual(
                set(item["row"]),
                set(contracts[item["consumerId"]]["requiredHeaders"]),
            )
        self.assertEqual(
            counts,
            {
                "worldSystem": 3,
                "deepResearch": 1,
                "indicatorEaTool": 6,
            },
        )
        self.assertEqual(len({item["id"] for item in items}), 10)

        # A retry replaces the same deterministic outbox identities instead of
        # creating duplicate rows.
        for report in (world, deep, radar):
            self.bridge._research_sheet_queue_report(report, flush=False)
        retried = self.bridge._load_research_sheet_outbox_unlocked()["items"]
        self.assertEqual(len(retried), 10)
        self.assertEqual(len({item["id"] for item in retried}), 10)

    def test_outbox_capacity_rejects_a_six_row_report_atomically_at_599(self) -> None:
        """A Radar batch must never become a misleading one-of-six archive."""

        self.configure_hub(revision=11)
        existing = [
            self._outbox_item(
                item_id=f"sheet-sync-existing-{index:03d}",
                record_key=f"existing-{index:03d}",
                revision=11,
            )
            for index in range(599)
        ]
        self.bridge._save_research_sheet_outbox_unlocked({"items": existing})
        radar = self._radar_report()
        expected_new_ids = {
            item["id"]
            for item in self.bridge._research_sheet_report_items(radar, 11)
        }
        self.assertEqual(len(expected_new_ids), 6)

        result = self.bridge._research_sheet_queue_report(radar, flush=False)
        stored = self.bridge._load_research_sheet_outbox_unlocked()["items"]

        self.assertEqual(
            result,
            {
                "queued": 0,
                "reason": "outbox_capacity_reached",
                "rejected": 6,
            },
        )
        self.assertEqual(len(stored), 599)
        self.assertTrue(expected_new_ids.isdisjoint({item["id"] for item in stored}))

    def test_flush_does_not_mark_a_replaced_payload_synced_with_stale_receipt(self) -> None:
        """A write receipt may acknowledge only the payload snapshot it wrote."""

        self.configure_hub(revision=12)
        original = self._world_report()
        self.bridge._research_sheet_queue_report(original, flush=False)
        before = self.bridge._load_research_sheet_outbox_unlocked()["items"]
        # Healthy candidates retain FIFO order within the least-attempted
        # generation, so this is the one max_items=1 will put in flight.
        target = before[0]
        # Isolate the in-flight row from scheduler ordering. The replacement
        # report may enqueue its two sibling rows only after this snapshot has
        # already been selected by flush.
        isolated_store = self.bridge._load_research_sheet_outbox_unlocked()
        isolated_store["items"] = [target]
        self.bridge._save_research_sheet_outbox_unlocked(isolated_store)
        replacement = copy.deepcopy(original)
        target_record_id = target["row"]["source_record_id"]
        replacement_system = next(
            system
            for system in replacement["metrics"]["systems"]
            if system["recordId"] == target_record_id
        )
        replacement_system["systemName"] += " - corrected while flush was in flight"
        replacement_items = self.bridge._research_sheet_report_items(replacement, 12)
        expected = next(item for item in replacement_items if item["id"] == target["id"])

        def upsert_then_replace(*_args, **_kwargs):
            queued = self.bridge._research_sheet_queue_report(
                replacement,
                flush=False,
            )
            self.assertGreaterEqual(queued["queued"], 1)
            return {
                "rowNumber": 2,
                "operation": "updated",
                "readBackVerified": True,
                "payloadDigest": target["payloadDigest"],
            }

        with (
            patch.object(
                self.hub,
                "credential_status",
                return_value={"configured": True, "mode": "access_token"},
            ),
            patch.object(self.hub, "upsert_row", side_effect=upsert_then_replace),
            patch.object(self.bridge, "_refresh_research_sheet_cache"),
        ):
            result = self.bridge._flush_research_sheet_outbox(max_items=1)

        stored = self.bridge._load_research_sheet_outbox_unlocked()["items"]
        current = next(item for item in stored if item["id"] == target["id"])
        self.assertEqual(result["synced"], 0)
        self.assertEqual(current["payloadDigest"], expected["payloadDigest"])
        self.assertEqual(current["row"], expected["row"])
        self.assertEqual(current["status"], "pending")
        self.assertEqual(current["attemptCount"], 0)
        self.assertIsNone(current["receipt"])
        settings = self.bridge.load_dashboard_workflow_settings()
        self.assertNotIn(
            "worldSystem",
            settings["researchSheetHub"].get("consumerWriteChecks") or {},
        )

    def test_retry_exhausted_poison_item_does_not_starve_fresh_pending_work(self) -> None:
        """A permanently failing head item must have a ceiling and fair queueing."""

        self.configure_hub(revision=13)
        attempt_ceiling = 5
        poison = self._outbox_item(
            item_id="sheet-sync-poison-item",
            record_key="poison-record",
            revision=13,
            status="retry_pending",
            attempt_count=attempt_ceiling,
            error_code="rate_limited",
        )
        healthy = self._outbox_item(
            item_id="sheet-sync-healthy-item",
            record_key="healthy-record",
            revision=13,
        )
        self.bridge._save_research_sheet_outbox_unlocked(
            {"items": [poison, healthy]}
        )
        written_keys = []

        def upsert(_sheet_id, _tab, _key_header, record_key, _row):
            written_keys.append(record_key)
            if record_key == "poison-record":
                raise self.hub.GoogleSheetHubError(
                    "rate_limited",
                    "synthetic permanent poison item",
                    429,
                )
            return {
                "rowNumber": 3,
                "operation": "updated",
                "readBackVerified": True,
            }

        with (
            patch.object(
                self.hub,
                "credential_status",
                return_value={"configured": True, "mode": "access_token"},
            ),
            patch.object(self.hub, "upsert_row", side_effect=upsert),
            patch.object(self.bridge, "_refresh_research_sheet_cache"),
        ):
            self.bridge._flush_research_sheet_outbox(max_items=1)

        stored = {
            item["id"]: item
            for item in self.bridge._load_research_sheet_outbox_unlocked()["items"]
        }
        self.assertEqual(written_keys, ["healthy-record"])
        self.assertEqual(stored["sheet-sync-healthy-item"]["status"], "synced")
        self.assertEqual(stored["sheet-sync-poison-item"]["status"], "failed")
        self.assertEqual(
            stored["sheet-sync-poison-item"]["lastErrorCode"],
            "retry_attempts_exhausted",
        )
        self.assertEqual(
            stored["sheet-sync-poison-item"]["attemptCount"],
            attempt_ceiling,
        )

    def test_verify_discards_stale_result_after_same_sheet_aba_revision_change(self) -> None:
        """Sheet A -> B -> A must not let A/rev3 verify overwrite A/rev5."""

        self.configure_hub(revision=3, status="verification_required")
        inspection = self.ready_probe(title="stale rev3 title")

        def change_config(sheet_id: str, revision: int) -> None:
            def mutate(settings: dict) -> dict:
                hub = settings["researchSheetHub"]
                hub.update(
                    {
                        "sheetId": sheet_id,
                        "canonicalUrl": (
                            f"https://docs.google.com/spreadsheets/d/{sheet_id}"
                        ),
                        "configRevision": revision,
                        "active": True,
                        "activeConfigRevision": revision,
                        "activationConfirmedAt": "2026-08-27T00:01:00Z",
                        "lastVerifiedAt": None,
                        "lastVerificationStatus": "verification_required",
                        "lastErrorCode": None,
                        "sheetTitle": None,
                        "consumerChecks": {},
                        "consumerWriteChecks": {},
                    }
                )
                settings["researchSheetHub"] = hub
                return settings

            self.bridge._mutate_dashboard_workflow_settings(mutate)

        def inspect_with_aba(sheet_id, _contracts, **_kwargs):
            self.assertEqual(sheet_id, SHEET_ID)
            change_config(OTHER_SHEET_ID, 4)
            change_config(SHEET_ID, 5)
            return inspection

        with (
            patch.object(
                self.hub,
                "credential_status",
                return_value={"configured": True, "mode": "access_token"},
            ),
            patch.object(self.hub, "probe_tabs", side_effect=inspect_with_aba),
            patch.object(
                self.bridge,
                "_refresh_research_sheet_cache",
                side_effect=lambda sheet_id, revision, _checks, **_kwargs: self.candidate_cache(
                    sheet_id, revision
                ),
            ),
        ):
            model = self.bridge._verify_research_sheet_hub()

        settings = self.bridge.load_dashboard_workflow_settings()
        hub = settings["researchSheetHub"]
        self.assertEqual(hub["sheetId"], SHEET_ID)
        self.assertEqual(hub["configRevision"], 5)
        self.assertEqual(hub["lastVerificationStatus"], "verification_required")
        self.assertIsNone(hub["lastVerifiedAt"])
        self.assertIsNone(hub["sheetTitle"])
        self.assertEqual(hub["consumerChecks"], {})
        self.assertEqual(model["configRevision"], 5)
        self.assertEqual(model["adapterStatus"], "verification_required")
        self.assertFalse(model["readReady"])

    def test_consumer_read_and_write_readiness_are_truthful_per_tab(self) -> None:
        self.configure_hub(revision=9)
        settings = self.bridge.load_dashboard_workflow_settings()
        settings["researchSheetHub"]["consumerWriteChecks"] = {
            "worldSystem": {
                "configRevision": 9,
                "verifiedAt": "2026-08-27T01:00:00Z",
            }
        }
        # A broken Radar schema must not hide the two independently readable
        # tabs, and one World write must not claim all writers are verified.
        settings["researchSheetHub"]["consumerChecks"]["indicatorEaTool"].update(
            {"status": "schema_mismatch", "readReady": False}
        )
        self.write_settings(settings)
        with patch.object(
            self.hub,
            "credential_status",
            return_value={"configured": True, "mode": "access_token"},
        ):
            model = self.bridge.research_sheet_hub_read_model()

        by_consumer = {item["consumerId"]: item for item in model["consumers"]}
        self.assertFalse(model["connected"])
        self.assertFalse(model["readReady"])
        self.assertFalse(model["writeReady"])
        self.assertTrue(by_consumer["worldSystem"]["readReady"])
        self.assertTrue(by_consumer["worldSystem"]["writeReady"])
        self.assertTrue(by_consumer["deepResearch"]["readReady"])
        self.assertFalse(by_consumer["deepResearch"]["writeReady"])
        self.assertFalse(by_consumer["indicatorEaTool"]["readReady"])
        self.assertNotIn("eaFactory", by_consumer)

    def test_writer_stays_unready_until_its_current_revision_outbox_is_complete(self) -> None:
        self.configure_hub(revision=10)
        settings = self.bridge.load_dashboard_workflow_settings()
        settings["researchSheetHub"]["consumerWriteChecks"] = {
            "worldSystem": {
                "configRevision": 10,
                "verifiedAt": "2026-08-27T01:00:00Z",
            }
        }
        self.write_settings(settings)
        pending = self._outbox_item(
            item_id="sheet-sync-world-pending",
            record_key="world-pending",
            revision=10,
        )
        self.bridge._save_research_sheet_outbox_unlocked({"items": [pending]})
        credential = {"configured": True, "mode": "access_token"}
        with patch.object(self.hub, "credential_status", return_value=credential):
            model = self.bridge.research_sheet_hub_read_model()
        world = next(row for row in model["consumers"] if row["consumerId"] == "worldSystem")
        self.assertFalse(world["writeReady"])
        self.assertEqual(world["outbox"]["pending"], 1)

        pending["status"] = "synced"
        self.bridge._save_research_sheet_outbox_unlocked({"items": [pending]})
        with patch.object(self.hub, "credential_status", return_value=credential):
            complete = self.bridge.research_sheet_hub_read_model()
        world_complete = next(
            row for row in complete["consumers"] if row["consumerId"] == "worldSystem"
        )
        self.assertTrue(world_complete["writeReady"])
        self.assertEqual(world_complete["outbox"]["pending"], 0)

    def test_unverified_or_incomplete_reports_never_enter_the_sheet_queue(self) -> None:
        world = self._world_report()
        world["metrics"]["systems"][1]["verificationStatus"] = "unverified"
        self.assertEqual(self.bridge._research_sheet_report_items(world, 1), [])

        deep = self._deep_report()
        deep["metrics"]["workflowOutput"]["valid"] = False
        self.assertEqual(self.bridge._research_sheet_report_items(deep, 1), [])

        factory_spec = self._deep_report()
        factory_spec["id"] = "report-eaf-spec-feedback-loop"
        factory_spec["metrics"]["eaFactoryStrategySpec"] = {
            "sourceRecordId": "world-1",
            "targetPlatform": "mt4",
        }
        self.assertEqual(
            self.bridge._research_sheet_report_items(factory_spec, 1),
            [],
        )

        radar = self._radar_report()
        radar["metrics"]["workflowOutput"]["entryErrors"] = ["invalid entry"]
        self.assertEqual(self.bridge._research_sheet_report_items(radar, 1), [])

    def test_ea_factory_uses_central_id_and_fixed_tab_only(self) -> None:
        self.configure_hub(revision=9)
        with self.assertRaises(self.bridge.RequestError) as wrong_sheet:
            self.bridge._sync_ea_factory_google_sheet_serial(
                {"googleSheetUrlOrId": OTHER_SHEET_ID}
            )
        self.assertEqual(wrong_sheet.exception.status, 409)

        with self.assertRaises(self.bridge.RequestError) as wrong_tab:
            self.bridge._sync_ea_factory_google_sheet_serial({"tabName": "Custom_Tab"})
        self.assertEqual(wrong_tab.exception.status, 422)

        with self.assertRaises(self.bridge.RequestError) as stale_revision:
            self.bridge._sync_ea_factory_google_sheet_serial({"configRevision": 8})
        self.assertEqual(stale_revision.exception.status, 409)

        with patch.object(
            self.bridge,
            "create_mission",
            side_effect=StopAfterEaFactoryValidation("validated"),
        ) as create_mission:
            with self.assertRaises(StopAfterEaFactoryValidation):
                self.bridge._sync_ea_factory_google_sheet_serial({})
        intent = create_mission.call_args.args[0]
        self.assertEqual(intent["targetId"], "right_server_racks")
        self.assertEqual(intent["toolId"], "ea_factory_google_sheet_read")
        self.assertIn("tab=Deep_Research", intent["prompt"])
        self.assertIn("required schema=Deep_Research", intent["prompt"])
        self.assertNotIn("EA_Full_Cycle", intent["prompt"])
        self.assertNotIn("range=A-W", intent["prompt"])
        self.assertNotIn(SHEET_ID, intent["prompt"])

    def test_deep_research_tab_maps_to_internal_factory_fields_without_a_fourth_tab(self) -> None:
        deep_row = self.bridge._research_sheet_deep_rows(self._deep_report())[0][0]
        deep_row.update(
            {
                "recovery_averaging_rules_json": json.dumps(["never average down"]),
                "special_conditions_json": json.dumps(["one position at a time"]),
                "position_sizing_rules_json": json.dumps(
                    {"maxRiskPerTrade": "1 percent fixed fractional"}
                ),
            }
        )
        headers = [
            *self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS,
            "manual_note",
        ]
        values = [
            headers,
            [deep_row.get(header, "") for header in headers],
        ]

        records = self.bridge._ea_factory_parse_deep_research_values(
            values,
            "sheet-deep-research-test",
        )

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["sourceKind"], "verified_deep_research_sheet")
        self.assertEqual(record["displayName"], "Verified System 1")
        self.assertEqual(record["core"]["entry_rules"], '["Enter on candle close"]')
        self.assertEqual(record["core"]["stop_loss"], "1 ATR")
        self.assertEqual(record["sourceUrls"], ["https://example.com/system-1"])
        self.assertTrue(record["buildReady"])
        schema = self.bridge._ea_factory_sheet_schema_read_model()
        self.assertEqual(schema["sheetTabDefault"], "Deep_Research")
        self.assertEqual(schema["sourceRequiredHeaders"], list(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS))
        self.assertNotIn("EA_Full_Cycle", json.dumps(schema, ensure_ascii=False))

        snapshot = {
            "schemaVersion": "ea-factory-sheet-snapshot-v1",
            "sourceSchemaVersion": "deep-research-sheet-v1",
            "sourceKind": "verified_deep_research_sheet",
            "sourceKey": "sheet-deep-research-test",
            "sheetReferenceMasked": "193dlW…Rp5A",
            "tabName": "Deep_Research",
            "status": "ready",
            "recordCount": 1,
            "rejectedRowCount": 0,
            "headerExact": True,
            "headerDigest": self.bridge.payload_digest(
                "ea-factory-deep-research-header-v1",
                list(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS),
            ),
            "records": records,
            "syncedAt": self.bridge.utc_now(),
            "missionId": "mission-deep-sheet-001",
            "reportId": "report-deep-sheet-001",
            "lastErrorCode": None,
        }
        snapshot["snapshotDigest"] = self.bridge._ea_factory_snapshot_digest(
            snapshot["sourceKey"], snapshot["tabName"], records
        )
        validated = self.bridge._ea_factory_revalidated_snapshot(snapshot)
        self.assertEqual(validated["sourceKind"], "verified_deep_research_sheet")
        tampered = copy.deepcopy(snapshot)
        tampered["tabName"] = "EA_Full_Cycle"
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.bridge._ea_factory_revalidated_snapshot(tampered)

    def test_verified_deep_research_cache_feeds_factory_automatically(self) -> None:
        self.configure_hub(revision=14)
        deep_row = self.bridge._research_sheet_deep_rows(self._deep_report())[0][0]
        deep_row.update(
            {
                "recovery_averaging_rules_json": json.dumps(["none"]),
                "special_conditions_json": json.dumps(["confirmed bar only"]),
                "position_sizing_rules_json": json.dumps({"maxRiskPerTrade": "1%"}),
            }
        )
        self.bridge.write_json(
            self.bridge.RESEARCH_SHEET_CACHE_PATH,
            {
                "schemaVersion": "research-sheet-cache-v1",
                "sheetDigest": self.bridge.payload_digest("research-sheet-id-v1", SHEET_ID),
                "configRevision": 14,
                "consumers": {
                    "deepResearch": {
                        "tabName": "Deep_Research",
                        "rowCount": 1,
                        "cachedRowCount": 1,
                        "rows": [deep_row],
                        "observedAt": self.bridge.utc_now(),
                    }
                },
                "updatedAt": self.bridge.utc_now(),
            },
        )
        with patch.object(
            self.hub,
            "credential_status",
            return_value={"configured": True, "mode": "access_token"},
        ):
            records = self.bridge._ea_factory_source_catalog(
                state=self.bridge._empty_ea_factory_state(),
                reports=[],
                missions=[],
            )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["sourceKind"], "verified_deep_research_sheet")
        self.assertTrue(records[0]["buildReady"])

    def test_lab_and_dev_read_models_receive_no_sheet_consumer(self) -> None:
        self.configure_hub()
        with patch.object(
            self.hub,
            "credential_status",
            return_value={"configured": False, "mode": "not_configured"},
        ):
            model = self.bridge.research_sheet_hub_read_model()
        consumer_props = {row["propId"] for row in model["consumers"]}
        self.assertNotIn("right_tool_console", consumer_props)
        self.assertNotIn("terminal_workstation", consumer_props)
        self.assertEqual(
            set(model["excludedPropIds"]),
            {"right_tool_console", "terminal_workstation"},
        )

    def test_world_sheet_cache_feeds_deep_research_and_selection_without_local_report(self) -> None:
        self.configure_hub(revision=5)
        observed_at = self.bridge.utc_now()
        world_row = {
            "discovery_id": "sheet-discovery-001",
            "source_record_id": "sheet-record-001",
            "system_name": "Verified Sheet Trend",
            "strategy_family": "trend_following",
            "record_type": "trading_system",
            "trader_or_author": "Public Author",
            "source_title": "Primary rules",
            "source_url": "https://example.com/primary-rules",
            "corroborating_url": "https://example.org/corroborating-rules",
            "evidence_urls_json": json.dumps(
                [
                    "https://example.com/primary-rules",
                    "https://example.org/corroborating-rules",
                ]
            ),
            "last_verified_at": "2026-08-27T06:00:00Z",
            "market": "forex",
            "symbols": json.dumps(["EURUSD"]),
            "timeframes_json": json.dumps(["H1"]),
            "sessions_json": json.dumps(["London"]),
            "indicator_settings_json": json.dumps([{"name": "EMA", "period": 20}]),
            "setup_conditions_json": json.dumps(["trend confirmed"]),
            "entry_steps_json": json.dumps(["enter on close"]),
            "exit_steps_json": json.dumps(["exit at two ATR"]),
            "trade_management_steps_json": json.dumps(["trail after one ATR"]),
            "max_risk_per_trade": "1%",
            "recovery_rules_json": json.dumps([]),
            "verification_status": "verified",
            "evidence_status": "verified",
            "duplicate_fingerprint": "a" * 24,
            "duplicate_status": "unique",
            "duplicate_scope": "none",
            "row_updated_at": "2026-08-27T06:05:00Z",
        }
        self.bridge.write_json(
            self.bridge.RESEARCH_SHEET_CACHE_PATH,
            {
                "schemaVersion": "research-sheet-cache-v1",
                "sheetDigest": self.bridge.payload_digest(
                    "research-sheet-id-v1", SHEET_ID
                ),
                "configRevision": 5,
                "consumers": {
                    "worldSystem": {
                        "tabName": "World_System",
                        "rowCount": 1,
                        "headerCount": len(world_row),
                        "rows": [world_row],
                        "observedAt": observed_at,
                    }
                },
                "updatedAt": observed_at,
            },
        )
        credential = {"configured": True, "mode": "access_token"}
        with patch.object(self.hub, "credential_status", return_value=credential):
            catalog = self.bridge._deep_research_catalog_read_model(
                reports=[], missions=[], delivered_sources=[]
            )
            selected = self.bridge._workflow_selected_source(
                "left_server_racks",
                "deep_research_system",
                {
                    "sourceReportId": "sheet-world-"
                    + self.bridge.payload_digest(
                        "world-system-sheet-row-v1", "sheet-discovery-001"
                    )[:24],
                    "sourceRecordId": "sheet-record-001",
                },
            )

        self.assertTrue(catalog["googleSheetCompared"])
        self.assertEqual(catalog["googleSheetVerifiedSystemCount"], 1)
        self.assertEqual(catalog["verifiedSystemCount"], 1)
        self.assertEqual(catalog["systems"][0]["sourceKind"], "verified_sheet_record")
        self.assertEqual(selected["sourceKind"], "verified_sheet_record")
        self.assertEqual(selected["structuredPayload"]["system"]["systemName"], "Verified Sheet Trend")
        self.assertFalse(selected["structuredPayload"]["embeddedInstructionsAllowed"])

    def test_cache_refresh_scans_keys_and_keeps_latest_250_rows(self) -> None:
        checks = {
            contract["consumerId"]: {
                "readReady": contract["consumerId"] == "worldSystem"
            }
            for contract in self.bridge.RESEARCH_SHEET_HUB_PROP_TABS.values()
        }
        ranges = []

        def read_values(_sheet_id, tab_name, cell_range):
            self.assertEqual(tab_name, "World_System")
            ranges.append(cell_range)
            if cell_range == "1:1":
                return [["discovery_id", "system_name"]]
            if cell_range == "A2:A10000":
                return [[f"D-{index:03d}"] for index in range(1, 301)]
            if cell_range == "A52:B301":
                return [
                    [f"D-{index:03d}", f"System {index:03d}"]
                    for index in range(51, 301)
                ]
            raise AssertionError(cell_range)

        with patch.object(self.hub, "read_values", side_effect=read_values):
            cache = self.bridge._refresh_research_sheet_cache(
                SHEET_ID,
                14,
                checks,
            )
        world = cache["consumers"]["worldSystem"]
        self.assertEqual(ranges, ["1:1", "A2:A10000", "A52:B301"])
        self.assertEqual(world["rowCount"], 300)
        self.assertEqual(world["cachedRowCount"], 250)
        self.assertEqual(world["windowStartRow"], 52)
        self.assertEqual(world["windowEndRow"], 301)
        self.assertEqual(world["rows"][0]["discovery_id"], "D-051")
        self.assertEqual(world["rows"][-1]["discovery_id"], "D-300")

    def test_deep_research_sheet_cache_is_exposed_as_verified_history(self) -> None:
        self.configure_hub(revision=15)
        row = {
            "research_id": "DR-sheet-history-001",
            "research_report_id": "report-deep-history-001",
            "source_report_id": "report-world-history-001",
            "source_record_id": "world-history-001",
            "system_name": "Sheet Deep Trend",
            "strategy_family": "trend_following",
            "verification_status": "verified_deep_research",
            "feasibility_status": "research_ready",
            "backtest_status": "not_run",
            "ea_build_status": "not_started",
            "symbols_json": json.dumps(["EURUSD"]),
            "suitable_timeframes_json": json.dumps(["H1"]),
            "candidate_platforms_json": json.dumps(["MT4", "MT5"]),
            "source_links_json": json.dumps(["https://example.com/deep-source"]),
            "updated_at": self.bridge.utc_now(),
        }
        now = self.bridge.utc_now()
        self.bridge.write_json(
            self.bridge.RESEARCH_SHEET_CACHE_PATH,
            {
                "schemaVersion": "research-sheet-cache-v1",
                "sheetDigest": self.bridge.payload_digest("research-sheet-id-v1", SHEET_ID),
                "configRevision": 15,
                "consumers": {
                    "deepResearch": {
                        "tabName": "Deep_Research",
                        "rowCount": 1,
                        "cachedRowCount": 1,
                        "rows": [row],
                        "observedAt": now,
                    }
                },
                "updatedAt": now,
            },
        )
        with patch.object(
            self.hub,
            "credential_status",
            return_value={"configured": True, "mode": "access_token"},
        ):
            catalog = self.bridge._deep_research_catalog_read_model(
                reports=[], missions=[], delivered_sources=[]
            )
        self.assertTrue(catalog["googleSheetResearchHistoryCompared"])
        self.assertEqual(catalog["googleSheetResearchHistoryCount"], 1)
        history = catalog["googleSheetResearchHistory"][0]
        self.assertEqual(history["researchId"], "DR-sheet-history-001")
        self.assertEqual(history["sourceKind"], "verified_deep_research_sheet_record")

    def test_radar_read_model_compares_verified_sheet_cache_and_revoked_auth_fails_closed(self) -> None:
        self.configure_hub(revision=6)
        fingerprint = "b" * 24
        observed_at = self.bridge.utc_now()
        self.bridge.write_json(
            self.bridge.RESEARCH_SHEET_CACHE_PATH,
            {
                "schemaVersion": "research-sheet-cache-v1",
                "sheetDigest": self.bridge.payload_digest(
                    "research-sheet-id-v1", SHEET_ID
                ),
                "configRevision": 6,
                "consumers": {
                    "indicatorEaTool": {
                        "tabName": "Indicator_EA_Tool",
                        "rowCount": 1,
                        "headerCount": 2,
                        "rows": [{"radar_record_id": "radar-cache-1", "duplicate_fingerprint": fingerprint}],
                        "observedAt": observed_at,
                    }
                },
                "updatedAt": observed_at,
            },
        )
        with patch.object(
            self.hub,
            "credential_status",
            return_value={"configured": True, "mode": "access_token"},
        ):
            radar = self.bridge._radar_website_tool_read_model(
                [],
                bridge={"codex": {"status": "ready"}, "time": "2026-08-27T07:00:00Z"},
                missions=[],
                schedule={"lastRunStatus": "never", "lastError": None},
            )
        self.assertTrue(radar["deduplication"]["googleSheetCompared"])
        self.assertEqual(radar["deduplication"]["googleSheetFingerprintCount"], 1)
        sheet_health = next(
            row for row in radar["serviceHealth"]["sourceHealth"]
            if row["sourceId"] == "google_sheet"
        )
        self.assertEqual(sheet_health["status"], "ready")

        with patch.object(
            self.hub,
            "credential_status",
            return_value={"configured": False, "mode": "not_configured"},
        ):
            revoked = self.bridge.research_sheet_hub_read_model()
            revoked_radar = self.bridge._radar_website_tool_read_model(
                [],
                bridge={"codex": {"status": "ready"}, "time": "2026-08-27T07:10:00Z"},
                missions=[],
                schedule={"lastRunStatus": "never", "lastError": None},
            )
        self.assertFalse(revoked["connected"])
        self.assertFalse(revoked["readReady"])
        self.assertEqual(revoked["adapterStatus"], "auth_required")
        self.assertTrue(
            all(row["status"] == "auth_required" for row in revoked["consumers"])
        )
        self.assertFalse(revoked_radar["deduplication"]["googleSheetCompared"])
        self.assertEqual(
            revoked_radar["deduplication"]["googleSheetFingerprintCount"],
            0,
        )

    def test_legacy_verified_hub_migrates_active_but_failed_legacy_stays_inactive(self) -> None:
        verified = self.bridge._default_dashboard_workflow_settings()
        verified_hub = verified["researchSheetHub"]
        verified_hub.update({
            "sheetId": SHEET_ID,
            "canonicalUrl": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}",
            "configRevision": 8,
            "savedAt": "2026-08-26T23:59:00Z",
            "lastVerifiedAt": "2026-08-27T00:00:00Z",
            "lastVerificationStatus": "read_ready_write_unverified",
            "consumerChecks": {
                contract["consumerId"]: {
                    "tabName": contract["tabName"],
                    "status": "ready",
                    "readReady": True,
                }
                for contract in self.bridge.RESEARCH_SHEET_HUB_PROP_TABS.values()
            },
        })
        for field in ("active", "activeConfigRevision", "activationConfirmedAt"):
            verified_hub.pop(field, None)
        self.write_settings(verified)
        with patch.object(
            self.hub,
            "credential_status",
            return_value={"configured": True, "mode": "access_token"},
        ):
            migrated = self.bridge.load_dashboard_workflow_settings()
            model = self.bridge.research_sheet_hub_read_model(migrated)
        self.assertTrue(migrated["researchSheetHub"]["active"])
        self.assertEqual(migrated["researchSheetHub"]["activeConfigRevision"], 8)
        self.assertTrue(model["active"])
        self.assertTrue(model["readReady"])
        self.assertTrue(all(
            check.get("configRevision") == 8
            for check in migrated["researchSheetHub"]["consumerChecks"].values()
        ))

        failed = self.bridge._default_dashboard_workflow_settings()
        failed_hub = failed["researchSheetHub"]
        failed_hub.update({
            "sheetId": OTHER_SHEET_ID,
            "canonicalUrl": f"https://docs.google.com/spreadsheets/d/{OTHER_SHEET_ID}",
            "configRevision": 9,
            "lastVerificationStatus": "auth_required",
            "consumerChecks": {},
        })
        for field in ("active", "activeConfigRevision", "activationConfirmedAt"):
            failed_hub.pop(field, None)
        self.write_settings(failed)
        shaped = self.bridge.load_dashboard_workflow_settings()
        self.assertFalse(shaped["researchSheetHub"]["active"])
        self.assertIsNone(shaped["researchSheetHub"]["activeConfigRevision"])

    def test_inactive_or_revision_mismatched_hub_never_reads_queues_flushes_or_marks(self) -> None:
        self.configure_hub(revision=21, active=False)
        now = self.bridge.utc_now()
        self.bridge.write_json(
            self.bridge.RESEARCH_SHEET_CACHE_PATH,
            {
                "schemaVersion": "research-sheet-cache-v1",
                "sheetDigest": self.bridge.payload_digest(
                    "research-sheet-id-v1", SHEET_ID
                ),
                "configRevision": 21,
                "consumers": {
                    "worldSystem": {
                        "tabName": "World_System",
                        "rowCount": 1,
                        "cachedRowCount": 1,
                        "rows": [{"discovery_id": "must-not-leak"}],
                        "observedAt": now,
                    }
                },
                "updatedAt": now,
            },
        )
        self.bridge._save_research_sheet_outbox_unlocked({
            "items": [self._outbox_item(
                item_id="sheet-sync-inactive",
                record_key="inactive",
                revision=21,
            )]
        })
        credential = {"configured": True, "mode": "access_token"}
        with (
            patch.object(self.hub, "credential_status", return_value=credential),
            patch.object(self.hub, "upsert_row") as upsert,
        ):
            self.assertEqual(
                self.bridge._research_sheet_cached_rows("worldSystem"),
                [],
            )
            self.assertEqual(
                self.bridge._research_sheet_queue_report(
                    self._world_report(), flush=False
                ),
                {"queued": 0, "reason": "activation_required"},
            )
            self.assertEqual(
                self.bridge._flush_research_sheet_outbox(max_items=20),
                {"processed": 0, "synced": 0, "reason": "activation_required"},
            )
            self.bridge._research_sheet_mark_write_verified(21, "worldSystem")
        upsert.assert_not_called()
        settings = self.bridge.load_dashboard_workflow_settings()
        self.assertEqual(
            settings["researchSheetHub"].get("consumerWriteChecks") or {},
            {},
        )

        settings["researchSheetHub"].update({
            "active": True,
            "activeConfigRevision": 20,
            "activationConfirmedAt": "2026-08-27T00:00:00Z",
        })
        self.write_settings(settings)
        with patch.object(self.hub, "credential_status", return_value=credential):
            model = self.bridge.research_sheet_hub_read_model()
        self.assertFalse(model["active"])
        self.assertFalse(model["operational"])
        self.assertFalse(any(system["ready"] for system in model["linkedSystems"]))

    def test_active_sheet_keeps_safe_title_when_backend_auth_expires(self) -> None:
        self.configure_hub(revision=22)
        settings = self.bridge.load_dashboard_workflow_settings()
        settings["researchSheetHub"]["sheetTitle"] = "Metafxclub Research Hub"
        self.write_settings(settings)
        with patch.object(
            self.hub,
            "credential_status",
            return_value={"configured": False, "mode": "not_configured"},
        ):
            model = self.bridge.research_sheet_hub_read_model()
        self.assertTrue(model["active"])
        self.assertFalse(model["operational"])
        self.assertEqual(model["adapterStatus"], "auth_required")
        self.assertEqual(model["sheetTitle"], "Metafxclub Research Hub")
        self.assertEqual(model["sheetDisplayValue"], SHEET_ID)

    def test_expired_stale_or_unconfirmed_activation_is_rejected_fail_closed(self) -> None:
        inspection = self.ready_probe()
        credential = {"configured": True, "mode": "access_token"}
        with (
            patch.object(self.hub, "credential_status", return_value=credential),
            patch.object(self.hub, "probe_tabs", return_value=inspection),
            patch.object(
                self.bridge,
                "_refresh_research_sheet_cache",
                side_effect=lambda sheet_id, revision, _checks, **_kwargs: self.candidate_cache(
                    sheet_id, revision
                ),
            ),
        ):
            inspected = self.bridge.inspect_research_sheet_hub_candidate(
                {"googleSheetUrlOrId": SHEET_ID}
            )["verificationPreview"]
            with self.assertRaises(self.bridge.RequestError) as unconfirmed:
                self.bridge.activate_research_sheet_hub({
                    "verificationToken": inspected["verificationToken"],
                    "confirmActivate": False,
                    "expectedConfigRevision": 0,
                    "idempotencyKey": "activation-unconfirmed",
                })
            self.assertEqual(unconfirmed.exception.status, 422)
            with self.bridge.RESEARCH_SHEET_PREVIEW_LOCK:
                self.bridge.RESEARCH_SHEET_VERIFICATION_PREVIEWS[
                    inspected["verificationToken"]
                ]["expiresAt"] = "2000-01-01T00:00:00+00:00"
            with self.assertRaises(self.bridge.RequestError) as expired:
                self.bridge.activate_research_sheet_hub({
                    "verificationToken": inspected["verificationToken"],
                    "confirmActivate": True,
                    "expectedConfigRevision": 0,
                    "idempotencyKey": "activation-expired",
                })
            self.assertEqual(expired.exception.status, 409)
        self.assertFalse(self.bridge.DASHBOARD_WORKFLOW_SETTINGS_PATH.exists())
        self.assertFalse(self.bridge.RESEARCH_SHEET_CACHE_PATH.exists())

    def test_active_reverify_persists_current_revision_probe_counts_and_cache(self) -> None:
        self.configure_hub(revision=23)
        inspection = self.ready_probe(title="Reverified Research Hub")
        credential = {"configured": True, "mode": "access_token"}
        with (
            patch.object(self.hub, "credential_status", return_value=credential),
            patch.object(self.hub, "probe_tabs", return_value=inspection),
            patch.object(
                self.bridge,
                "_refresh_research_sheet_cache",
                side_effect=lambda sheet_id, revision, _checks, **_kwargs: self.candidate_cache(
                    sheet_id, revision
                ),
            ),
        ):
            model = self.bridge._verify_research_sheet_hub()
        self.assertTrue(model["active"])
        self.assertTrue(model["operational"])
        self.assertEqual(model["sheetTitle"], "Reverified Research Hub")
        self.assertTrue(all(
            consumer["configRevision"] == 23 and consumer["rowCount"] == 1
            for consumer in model["consumers"]
        ))
        settings = self.bridge.load_dashboard_workflow_settings()
        for check in settings["researchSheetHub"]["consumerChecks"].values():
            self.assertEqual(check["configRevision"], 23)
            self.assertEqual(check["rowCount"], 1)
            self.assertTrue(check["probeEvidence"]["confirmed"])

    def test_probe_tabs_reports_real_row_counts_without_returning_cell_values(self) -> None:
        contracts = self.bridge._research_sheet_tab_contracts()
        headers_by_tab = {
            contract["tabName"]: contract["requiredHeaders"]
            for contract in contracts.values()
        }
        keys_by_tab = {
            "World_System": [["world-1"], ["world-2"]],
            "Deep_Research": [["deep-1"]],
            "Indicator_EA_Tool": [["radar-1"], ["radar-2"], ["radar-3"]],
        }

        def open_url(request, timeout=0):
            self.assertGreater(timeout, 0)
            decoded = unquote(request.full_url)
            if "fields=spreadsheetId" in decoded:
                return FakeJsonResponse({
                    "spreadsheetId": SHEET_ID,
                    "properties": {"title": "Probe Test Hub"},
                    "sheets": [
                        {"properties": {"title": tab_name}}
                        for tab_name in headers_by_tab
                    ],
                })
            for tab_name, headers in headers_by_tab.items():
                if f"'{tab_name}'!1:1" in decoded:
                    return FakeJsonResponse({"values": [headers]})
                if f"'{tab_name}'!A2:A10000" in decoded:
                    return FakeJsonResponse({"values": keys_by_tab[tab_name]})
            raise AssertionError(f"Unexpected Google API request: {decoded}")

        result = self.hub.probe_tabs(
            SHEET_ID,
            contracts,
            environ={"METAFX_GOOGLE_SHEETS_ACCESS_TOKEN": "backend-only-token"},
            open_url=open_url,
        )
        self.assertTrue(result["probeReady"])
        counts = {
            check["tabName"]: check["rowCount"]
            for check in result["consumers"].values()
        }
        self.assertEqual(counts, {
            "World_System": 2,
            "Deep_Research": 1,
            "Indicator_EA_Tool": 3,
        })
        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("backend-only-token", serialized)
        self.assertNotIn("world-1", serialized)
        self.assertTrue(all(
            check["probeEvidence"]["confirmed"]
            for check in result["consumers"].values()
        ))

    @staticmethod
    def _outbox_item(
        *,
        item_id: str,
        record_key: str,
        revision: int,
        status: str = "pending",
        attempt_count: int = 0,
        error_code: str | None = None,
    ) -> dict:
        row = {"discovery_id": record_key, "system_name": record_key}
        return {
            "id": item_id,
            "status": status,
            "consumerId": "worldSystem",
            "producerPropId": "codex_mcp_portal",
            "tabName": "World_System",
            "keyHeader": "discovery_id",
            "recordKey": record_key,
            "row": row,
            "payloadDigest": "synthetic-" + record_key,
            "configRevision": revision,
            "reportId": "report-" + record_key,
            "missionId": "mission-" + record_key,
            "attemptCount": attempt_count,
            "lastAttemptAt": None,
            "lastErrorCode": error_code,
            "receipt": None,
            "createdAt": "2026-08-27T00:00:00Z",
            "updatedAt": "2026-08-27T00:00:00Z",
        }

    @staticmethod
    def _world_report() -> dict:
        systems = []
        for index in range(1, 4):
            systems.append(
                {
                    "recordId": f"world-{index}",
                    "systemName": f"Verified System {index}",
                    "sourceTitle": f"Source {index}",
                    "sourceUrl": f"https://example.com/system-{index}",
                    "checkedAt": "2026-08-27T02:00:00Z",
                    "verificationStatus": "verified",
                    "duplicateStatus": "unique",
                    "duplicateFingerprint": f"fp-{index}",
                    "strategyFamily": "trend_following",
                    "symbols": ["EURUSD"],
                    "timeframes": ["H1"],
                    "entrySteps": ["EMA cross"],
                    "exitSteps": ["ATR target"],
                    "riskManagement": {"maxRiskPerTrade": "1%"},
                }
            )
        return {
            "id": "report-world-sheet-001",
            "type": "trading_system_discovery_report",
            "status": "ready",
            "linkedPropId": "codex_mcp_portal",
            "linkedMissionId": "mission-world-sheet-001",
            "ownerAgentId": "news_consultant",
            "createdAt": "2026-08-27T02:00:00Z",
            "updatedAt": "2026-08-27T02:05:00Z",
            "metrics": {
                "workflowOutput": {"applicable": True, "valid": True},
                "systems": systems,
            },
        }

    @staticmethod
    def _deep_report() -> dict:
        return {
            "id": "report-deep-sheet-001",
            "type": "trading_system_research_report",
            "title": "Deep research: verified trend system",
            "status": "ready",
            "linkedPropId": "left_server_racks",
            "linkedMissionId": "mission-deep-sheet-001",
            "ownerAgentId": "technical_consultant",
            "createdAt": "2026-08-27T03:00:00Z",
            "updatedAt": "2026-08-27T03:05:00Z",
            "workflowContext": {
                "source": {
                    "recordId": "world-1",
                    "systemId": "TS-world-1",
                    "reportId": "report-world-sheet-001",
                    "missionId": "mission-world-sheet-001",
                }
            },
            "metrics": {
                "workflowOutput": {"applicable": True, "valid": True},
                "systemIdentity": {
                    "systemName": "Verified System 1",
                    "strategyFamily": "trend_following",
                },
                "verifiedRules": ["EMA 20 crosses EMA 50"],
                "entrySteps": ["Enter on candle close"],
                "exitSteps": ["Exit at two ATR"],
                "riskModel": {"stopLoss": "1 ATR", "takeProfit": "2 ATR"},
                "indicatorSettings": {"EMA": [20, 50]},
                "suitableMarket": ["EURUSD"],
                "suitableTimeframe": ["H1"],
                "sourceLinks": ["https://example.com/system-1"],
                "targetPlatforms": ["MT4", "MT5"],
            },
        }

    def _radar_report(self) -> dict:
        entries = []
        for index in range(1, 7):
            entries.append(
                {
                    "recordId": f"radar-{index}",
                    "toolName": f"Radar Tool {index}",
                    "toolKind": ("indicator", "ea", "tool")[(index - 1) % 3],
                    "category": "analysis",
                    "platform": "tradingview" if index % 2 else "mt5",
                    "version": "1.0",
                    "sourceTitle": f"Publisher {index}",
                    "sourceUrl": f"https://example.org/tool-{index}",
                    "checkedAt": "2026-08-27T04:00:00Z",
                    "verificationStatus": "verified",
                    "availability": "public",
                    "eaReadiness": "ready" if index % 3 == 2 else "not_ea_ready",
                    "missingRules": [],
                    "sourceLimitations": [],
                    "duplicateStatus": "unique",
                    "duplicateScope": "none",
                }
            )
        return {
            "id": "report-radar-sheet-001",
            "type": "indicator_scout_report",
            "status": "ready",
            "linkedPropId": "left_audit_crystals",
            "linkedMissionId": "mission-radar-sheet-001",
            "ownerAgentId": "news_consultant",
            "createdAt": "2026-08-27T04:00:00Z",
            "updatedAt": "2026-08-27T04:05:00Z",
            "metrics": {
                "workflowOutput": {
                    "applicable": True,
                    "valid": True,
                    "failureCode": None,
                    "procedureId": self.bridge.RADAR_WORKFLOW_PROCEDURE_ID,
                    "providedFields": ["entries"],
                    "missingFields": [],
                    "missingEvidenceKinds": [],
                    "entryErrors": [],
                    "oversizedFields": [],
                },
                "entries": entries,
            },
            "evidence": [
                {"kind": "public_web", "url": entry["sourceUrl"]}
                for entry in entries
            ],
        }


if __name__ == "__main__":
    unittest.main()
