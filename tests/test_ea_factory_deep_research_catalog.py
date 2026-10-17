from __future__ import annotations

import copy
import http.client
import importlib.util
import json
import threading
import unittest
from pathlib import Path
from urllib.parse import quote
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_ea_factory_deep_research_catalog_tests",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EaFactoryDeepResearchCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        self.global_platform_context = mock.patch.object(
            self.bridge,
            "_ea_factory_require_top_header_locks",
            side_effect=self._dual_locked_platform_context,
        )
        self.global_platform_context.start()
        self.addCleanup(self.global_platform_context.stop)
        with self.bridge.EA_FACTORY_DEEP_RESEARCH_CATALOG_CACHE_CONDITION:
            self.bridge.EA_FACTORY_DEEP_RESEARCH_CATALOG_CACHE.clear()
            self.bridge.EA_FACTORY_DEEP_RESEARCH_CATALOG_INFLIGHT.clear()
        self._credential_binding = object()
        self._credential_binding_patcher = mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_binding_snapshot",
            return_value=self._credential_binding,
        )
        self._credential_binding_patcher.start()
        self.addCleanup(self._credential_binding_patcher.stop)

    @staticmethod
    def _dual_locked_platform_context(
        platform: object,
        *,
        require_all_platforms: bool = True,
    ) -> dict | None:
        normalized = str(platform or "").strip().lower()
        if normalized not in {"mt4", "mt5"}:
            return None
        candidate_id = f"mtc-catalog-{normalized}"
        return {
            "record": {
                "candidateId": candidate_id,
                "platform": normalized,
                "available": True,
                "runningState": "platform_running_detected",
            },
            "token": {
                "candidateId": candidate_id,
                "platform": normalized,
                "selectionRevision": 7,
            },
        }

    @classmethod
    def rows(cls) -> list[list[str]]:
        headers = list(cls.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS)
        return [
            headers,
            [
                "deep-system-001",
                "Donchian Trend",
                "Donchian 5/20; Forex; D1",
                "Buy after the closed bar breaks the upper channel.\nSell symmetrically.",
                "No recovery, grid, martingale, or averaging.",
                "Exit on opposite channel or stop loss.",
                "RiskPercent=1; FixedLot=0.01.",
                "One decision per new closed bar.",
                "Show signal, balance, equity, and spread.",
                "Periods and risk remain inputs.",
            ],
            [
                "deep-system-002",
                "Donchian Trend",
                "Donchian 10/40; Forex; H4",
                "Buy after the closed bar breaks the upper channel.",
                "No recovery.",
                "Exit on opposite channel.",
                "RiskPercent=0.5.",
                "One position per symbol and magic.",
                "Show current channel.",
                "Longer-period variant.",
            ],
        ]

    @staticmethod
    def hub(
        revision: int = 7,
        *,
        read_ready: bool = True,
        activation_confirmed_at: str = "2026-10-14T10:00:00+00:00",
    ) -> dict:
        return {
            "sheetId": "1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
            "active": True,
            "configRevision": revision,
            "activeConfigRevision": revision,
            "activationConfirmedAt": activation_confirmed_at,
            "lastVerificationStatus": "ready",
            "consumerChecks": {
                "deepResearch": {
                    "readReady": read_ready,
                    "status": "ready" if read_ready else "schema_mismatch",
                    "configRevision": revision,
                }
            },
        }

    def ready_patches(self, rows: list[list[str]] | None = None):
        stable_rows = rows or self.rows()
        return (
            mock.patch.object(
                self.bridge,
                "_research_sheet_hub_internal",
                return_value=self.hub(),
            ),
            mock.patch.object(
                self.bridge.google_sheet_hub,
                "credential_status",
                return_value={"configured": True, "mode": "oauth"},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_read_deep_research_values",
                side_effect=[copy.deepcopy(stable_rows), copy.deepcopy(stable_rows)],
            ),
        )

    def test_live_catalog_uses_record_id_value_and_disambiguates_duplicate_names(self) -> None:
        patches = self.ready_patches()
        with patches[0], patches[1], patches[2]:
            result = self.bridge.ea_factory_deep_research_catalog_read_model(
                "deep-system-001"
            )

        self.assertEqual(
            result["schemaVersion"],
            "ea-factory-deep-research-catalog-v1",
        )
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["configRevision"], 7)
        self.assertEqual(result["tabName"], "Deep_Research")
        self.assertEqual(result["totalCount"], 2)
        self.assertRegex(result["catalogDigest"], r"^[0-9a-f]{64}$")
        self.assertRegex(result["snapshotDigest"], r"^[0-9a-f]{64}$")
        self.assertTrue(result["observedAt"])
        systems = {row["recordId"]: row for row in result["systems"]}
        self.assertEqual(systems["deep-system-001"]["value"], "deep-system-001")
        self.assertEqual(
            systems["deep-system-001"]["systemName"],
            "Donchian Trend",
        )
        self.assertEqual(
            systems["deep-system-001"]["displayLabel"],
            "Donchian Trend — deep-system-001",
        )
        self.assertRegex(
            systems["deep-system-001"]["sourceRecordId"],
            r"^ea-source-[0-9a-f]{24}$",
        )

        selected = result["selectedRecord"]
        self.assertEqual(selected["recordId"], "deep-system-001")
        self.assertEqual(
            list(selected["fields"]),
            list(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS),
        )
        # The catalog exposes the same whitespace-normalized prose covered by
        # the source-record digest; preserve both clauses without requiring a
        # raw Sheet line break in the rendered summary.
        self.assertIn(
            "Buy after the closed bar breaks the upper channel.",
            selected["fields"]["entry_rules"],
        )
        self.assertIn(
            "Sell symmetrically.",
            selected["fields"]["entry_rules"],
        )
        self.assertEqual(
            [row["column"] for row in selected["orderedFields"]],
            list("ABCDEFGHIJ"),
        )
        self.assertEqual(
            [row["field"] for row in selected["orderedFields"]],
            list(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS),
        )

    def test_catalog_without_selection_returns_options_only(self) -> None:
        patches = self.ready_patches()
        with patches[0], patches[1], patches[2]:
            result = self.bridge.ea_factory_deep_research_catalog_read_model()

        self.assertEqual(result["totalCount"], 2)
        self.assertIsNone(result["selectedRecord"])
        self.assertEqual(result["selectionField"], "record_id")
        self.assertEqual(result["displayField"], "system_name")
        self.assertFalse(result["externalWrites"])
        self.assertFalse(result["credentialsExposed"])
        self.assertNotIn("authBinding", json.dumps(result, ensure_ascii=False))
        self.assertNotIn("credential-binding", json.dumps(result, ensure_ascii=False))

    def test_success_cache_is_short_lived_and_avoids_duplicate_double_read(self) -> None:
        rows = self.rows()
        reader = mock.Mock(
            side_effect=[copy.deepcopy(rows), copy.deepcopy(rows)]
        )
        with mock.patch.object(
            self.bridge,
            "_research_sheet_hub_internal",
            return_value=self.hub(),
        ), mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_status",
            return_value={"configured": True},
        ), mock.patch.object(
            self.bridge,
            "_ea_factory_read_deep_research_values",
            reader,
        ):
            first = self.bridge.ea_factory_deep_research_catalog_read_model()
            second = self.bridge.ea_factory_deep_research_catalog_read_model()

        self.assertEqual(first, second)
        self.assertEqual(reader.call_count, 2)
        self.assertIsNot(first, second)

    def test_reactivating_same_revision_invalidates_catalog_cache(self) -> None:
        rows = self.rows()
        reader = mock.Mock(
            side_effect=[copy.deepcopy(rows) for _ in range(4)]
        )
        first_activation = self.hub(
            activation_confirmed_at="2026-10-14T10:00:00+00:00"
        )
        second_activation = self.hub(
            activation_confirmed_at="2026-10-14T10:00:01+00:00"
        )
        with mock.patch.object(
            self.bridge,
            "_research_sheet_hub_internal",
            side_effect=[
                first_activation,
                first_activation,
                first_activation,
                second_activation,
                second_activation,
                second_activation,
            ],
        ), mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_status",
            return_value={"configured": True},
        ), mock.patch.object(
            self.bridge,
            "_ea_factory_read_deep_research_values",
            reader,
        ):
            first = self.bridge.ea_factory_deep_research_catalog_read_model()
            second = self.bridge.ea_factory_deep_research_catalog_read_model()

        self.assertEqual(reader.call_count, 4)
        self.assertNotEqual(first["catalogDigest"], second["catalogDigest"])

    def test_all_record_selections_share_one_verified_base_catalog(self) -> None:
        rows = self.rows()
        reader = mock.Mock(
            side_effect=[copy.deepcopy(rows), copy.deepcopy(rows)]
        )
        with mock.patch.object(
            self.bridge,
            "_research_sheet_hub_internal",
            return_value=self.hub(),
        ), mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_status",
            return_value={"configured": True},
        ), mock.patch.object(
            self.bridge,
            "_ea_factory_read_deep_research_values",
            reader,
        ):
            first = self.bridge.ea_factory_deep_research_catalog_read_model(
                "deep-system-001"
            )
            second = self.bridge.ea_factory_deep_research_catalog_read_model(
                "deep-system-002"
            )
            with self.assertRaises(self.bridge.RequestError) as missing:
                self.bridge.ea_factory_deep_research_catalog_read_model(
                    "deep-system-missing"
                )

        self.assertEqual(first["selectedRecord"]["recordId"], "deep-system-001")
        self.assertEqual(second["selectedRecord"]["recordId"], "deep-system-002")
        self.assertEqual(missing.exception.status, 404)
        self.assertEqual(reader.call_count, 2)

    def test_concurrent_catalog_requests_share_one_stable_double_read(self) -> None:
        rows = self.rows()
        first_read_started = threading.Event()
        release_first_read = threading.Event()
        second_binding_seen = threading.Event()
        binding_calls = 0
        binding_calls_lock = threading.Lock()
        read_calls = 0
        read_calls_lock = threading.Lock()

        def credential_binding():
            nonlocal binding_calls
            with binding_calls_lock:
                binding_calls += 1
                if binding_calls >= 2:
                    second_binding_seen.set()
            return self._credential_binding

        def read_values(*_args, **_kwargs):
            nonlocal read_calls
            with read_calls_lock:
                read_calls += 1
                call_number = read_calls
            if call_number == 1:
                first_read_started.set()
                if not release_first_read.wait(timeout=3):
                    raise AssertionError("Timed out waiting to release first read")
            return copy.deepcopy(rows)

        results: list[dict] = []
        errors: list[BaseException] = []

        def target() -> None:
            try:
                results.append(
                    self.bridge.ea_factory_deep_research_catalog_read_model()
                )
            except BaseException as error:  # pragma: no cover - asserted below
                errors.append(error)

        with mock.patch.object(
            self.bridge,
            "_research_sheet_hub_internal",
            return_value=self.hub(),
        ), mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_status",
            return_value={"configured": True},
        ), mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_binding_snapshot",
            side_effect=credential_binding,
        ), mock.patch.object(
            self.bridge,
            "_ea_factory_read_deep_research_values",
            side_effect=read_values,
        ):
            first_thread = threading.Thread(target=target)
            second_thread = threading.Thread(target=target)
            first_thread.start()
            self.assertTrue(first_read_started.wait(timeout=3))
            second_thread.start()
            self.assertTrue(second_binding_seen.wait(timeout=3))
            release_first_read.set()
            first_thread.join(timeout=5)
            second_thread.join(timeout=5)

        self.assertFalse(first_thread.is_alive())
        self.assertFalse(second_thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], results[1])
        self.assertEqual(read_calls, 2)

    def test_catalog_fails_closed_if_sheet_changes_between_reads(self) -> None:
        first = self.rows()
        second = copy.deepcopy(first)
        second[1][2] = "Changed while reading"
        with mock.patch.object(
            self.bridge,
            "_research_sheet_hub_internal",
            return_value=self.hub(),
        ), mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_status",
            return_value={"configured": True},
        ), mock.patch.object(
            self.bridge,
            "_ea_factory_read_deep_research_values",
            side_effect=[first, second],
        ):
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.ea_factory_deep_research_catalog_read_model()

        self.assertEqual(caught.exception.status, 409)
        self.assertEqual(
            caught.exception.response_payload["code"],
            "deep_research_changed_during_read",
        )

    def test_catalog_fails_closed_if_active_revision_changes_after_read(self) -> None:
        rows = self.rows()
        with mock.patch.object(
            self.bridge,
            "_research_sheet_hub_internal",
            side_effect=[self.hub(7), self.hub(8)],
        ), mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_status",
            return_value={"configured": True},
        ), mock.patch.object(
            self.bridge,
            "_ea_factory_read_deep_research_values",
            side_effect=[copy.deepcopy(rows), copy.deepcopy(rows)],
        ):
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.ea_factory_deep_research_catalog_read_model()

        self.assertEqual(
            caught.exception.response_payload["code"],
            "research_sheet_binding_changed",
        )

    def test_catalog_fails_closed_if_activation_changes_after_read(self) -> None:
        rows = self.rows()
        with mock.patch.object(
            self.bridge,
            "_research_sheet_hub_internal",
            side_effect=[
                self.hub(
                    activation_confirmed_at="2026-10-14T10:00:00+00:00"
                ),
                self.hub(
                    activation_confirmed_at="2026-10-14T10:00:01+00:00"
                ),
            ],
        ), mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_status",
            return_value={"configured": True},
        ), mock.patch.object(
            self.bridge,
            "_ea_factory_read_deep_research_values",
            side_effect=[copy.deepcopy(rows), copy.deepcopy(rows)],
        ):
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.ea_factory_deep_research_catalog_read_model()

        self.assertEqual(caught.exception.status, 409)
        self.assertEqual(
            caught.exception.response_payload["code"],
            "research_sheet_binding_changed",
        )

    def test_catalog_fails_closed_if_google_authorization_changes_after_read(self) -> None:
        rows = self.rows()
        with mock.patch.object(
            self.bridge,
            "_research_sheet_hub_internal",
            side_effect=[self.hub(), self.hub()],
        ), mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_status",
            return_value={"configured": True},
        ), mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_binding_snapshot",
            side_effect=[object(), object()],
        ), mock.patch.object(
            self.bridge,
            "_ea_factory_read_deep_research_values",
            side_effect=[copy.deepcopy(rows), copy.deepcopy(rows)],
        ):
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.ea_factory_deep_research_catalog_read_model()

        self.assertEqual(caught.exception.status, 409)
        self.assertEqual(
            caught.exception.response_payload["code"],
            "research_sheet_binding_changed",
        )

    def test_catalog_blocks_aba_account_switch_before_second_sheets_http(self) -> None:
        rows = self.rows()
        binding_a = self.bridge.google_sheet_hub._direct_credential_binding(
            "access-account-a"
        )
        binding_b = self.bridge.google_sheet_hub._direct_credential_binding(
            "access-account-b"
        )
        context_a = self.bridge.google_sheet_hub._AccessTokenContext(
            token="access-account-a",
            credential_binding=binding_a,
        )
        context_b = self.bridge.google_sheet_hub._AccessTokenContext(
            token="access-account-b",
            credential_binding=binding_b,
        )
        with mock.patch.object(
            self.bridge,
            "_research_sheet_hub_internal",
            return_value=self.hub(),
        ), mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_status",
            return_value={"configured": True},
        ), mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_binding_snapshot",
            return_value=binding_a,
        ), mock.patch.object(
            self.bridge.google_sheet_hub,
            "_resolve_access_token_context",
            side_effect=[context_a, context_b],
        ) as resolver, mock.patch.object(
            self.bridge.google_sheet_hub,
            "_perform_google_sheets_request",
            return_value={"values": copy.deepcopy(rows)},
        ) as sheets_http:
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.ea_factory_deep_research_catalog_read_model()

        self.assertEqual(caught.exception.status, 409)
        self.assertEqual(
            caught.exception.response_payload["code"],
            "oauth_credential_changed",
        )
        self.assertEqual(resolver.call_count, 2)
        # The second read resolves account B, but expected binding A rejects it
        # before any Sheets HTTP can occur.  A final A snapshot could otherwise
        # hide this A -> B -> A sequence from a before/after-only check.
        sheets_http.assert_called_once()

    def test_catalog_requires_current_read_proof_and_google_auth(self) -> None:
        with mock.patch.object(
            self.bridge,
            "_research_sheet_hub_internal",
            return_value=self.hub(read_ready=False),
        ), mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_status",
            return_value={"configured": True},
        ):
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.ea_factory_deep_research_catalog_read_model()
        self.assertEqual(caught.exception.response_payload["code"], "schema_mismatch")

        with mock.patch.object(
            self.bridge,
            "_research_sheet_hub_internal",
            return_value=self.hub(),
        ), mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_status",
            return_value={"configured": False},
        ):
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.ea_factory_deep_research_catalog_read_model()
        self.assertEqual(caught.exception.response_payload["code"], "auth_required")

    def test_catalog_rejects_duplicate_record_id_and_missing_selection(self) -> None:
        duplicate = self.rows()
        duplicate[2][0] = duplicate[1][0].upper()
        patches = self.ready_patches(duplicate)
        with patches[0], patches[1], patches[2]:
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.ea_factory_deep_research_catalog_read_model()
        self.assertEqual(
            caught.exception.response_payload["code"],
            "deep_research_schema_mismatch",
        )

        patches = self.ready_patches()
        with patches[0], patches[1], patches[2]:
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.ea_factory_deep_research_catalog_read_model(
                    "deep-system-missing"
                )
        self.assertEqual(caught.exception.status, 404)
        self.assertEqual(
            caught.exception.response_payload["code"],
            "deep_research_record_not_found",
        )

    def test_catalog_rejects_noncanonical_header_and_incomplete_row(self) -> None:
        invalid_cases = []
        wrong_header = self.rows()
        wrong_header[0][0] = "record_id / note"
        invalid_cases.append(wrong_header)
        padded_header = self.rows()
        padded_header[0][0] = " record_id "
        invalid_cases.append(padded_header)
        short_row = self.rows()
        short_row[1] = short_row[1][:-1]
        invalid_cases.append(short_row)
        blank_cell = self.rows()
        blank_cell[1][8] = ""
        invalid_cases.append(blank_cell)

        for rows in invalid_cases:
            with self.subTest(rows=rows[0:2]):
                patches = self.ready_patches(rows)
                with patches[0], patches[1], patches[2]:
                    with self.assertRaises(self.bridge.RequestError) as caught:
                        self.bridge.ea_factory_deep_research_catalog_read_model()
                self.assertEqual(caught.exception.status, 422)
                self.assertEqual(
                    caught.exception.response_payload["code"],
                    "deep_research_schema_mismatch",
                )

    def test_catalog_rejects_raw_tokens_keys_and_private_key_material(self) -> None:
        newly_redacted_secrets = (
            "sk" + "_live_" + ("A" * 24),
            "glpat" + "-" + ("a" * 20),
            "AKIA" + ("A" * 16),
            "https://" + "alice:" + "s3cr3t-pass" + "@example.com/path",
        )
        secrets_to_reject = (
            "ya" + "29." + "A0ARrdaM-example-access-token-value",
            "1" + "//" + "0g-example-refresh-token-value",
            "AIza" + ("A" * 35),
            *newly_redacted_secrets,
            (
                '{"private_key":"-----BEGIN ' + "PRIVATE KEY-----\\n"
                "DUMMYKEYBODYTHATMUSTNEVERBEPUBLISHED\\n"
                "-----END " + 'PRIVATE KEY-----"}'
            ),
        )
        for secret_value in secrets_to_reject:
            with self.subTest(secret_kind=secret_value[:12]):
                self.assertTrue(
                    self.bridge._ea_factory_deep_research_cell_contains_secret(
                        secret_value
                    )
                )
                rows = self.rows()
                rows[1][9] = secret_value
                patches = self.ready_patches(rows)
                with patches[0], patches[1], patches[2]:
                    with self.assertRaises(self.bridge.RequestError) as caught:
                        self.bridge.ea_factory_deep_research_catalog_read_model()
                self.assertEqual(caught.exception.status, 422)
                self.assertEqual(
                    caught.exception.response_payload["code"],
                    "deep_research_schema_mismatch",
                )
                self.assertNotIn(
                    "DUMMYKEYBODYTHATMUSTNEVERBEPUBLISHED",
                    json.dumps(caught.exception.response_payload),
                )
        for secret_value in newly_redacted_secrets:
            with self.subTest(redaction_kind=secret_value[:12]):
                self.assertNotIn(
                    secret_value,
                    self.bridge.redact_text(secret_value),
                )

    def test_catalog_secret_guard_avoids_obvious_prefix_and_port_false_positives(self) -> None:
        safe_values = (
            "Use sk_live mode only after operator review.",
            "The GitLab documentation calls this the glpat prefix.",
            "Document the AKIA prefix without embedding an access key.",
            "Read the public guide at https://example.com:8443/path.",
        )
        for value in safe_values:
            with self.subTest(value=value):
                self.assertFalse(
                    self.bridge._ea_factory_deep_research_cell_contains_secret(value)
                )
                self.assertEqual(self.bridge.redact_text(value), value)

    def test_catalog_unicode_record_id_is_selectable_and_control_id_is_rejected(self) -> None:
        unicode_rows = self.rows()
        unicode_rows[1][0] = "ระบบ-๑"
        patches = self.ready_patches(unicode_rows)
        with patches[0], patches[1], patches[2]:
            result = self.bridge.ea_factory_deep_research_catalog_read_model(
                "ระบบ-๑"
            )
        self.assertEqual(result["selectedRecord"]["recordId"], "ระบบ-๑")

        control_rows = self.rows()
        control_rows[1][0] = "deep\x07system"
        patches = self.ready_patches(control_rows)
        with patches[0], patches[1], patches[2]:
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.ea_factory_deep_research_catalog_read_model()
        self.assertEqual(caught.exception.status, 422)
        self.assertEqual(
            caught.exception.response_payload["code"],
            "deep_research_schema_mismatch",
        )

        patches = self.ready_patches()
        with patches[0], patches[1], patches[2]:
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.ea_factory_deep_research_catalog_read_model(
                    "deep\x07system"
                )
        self.assertEqual(caught.exception.status, 422)
        self.assertEqual(caught.exception.response_payload["code"], "invalid_record_id")

    def test_catalog_rejects_record_ids_that_would_change_identity(self) -> None:
        invalid_ids = (
            " deep-system-001 ",
            "deep  system",
            r"C:\Users\Alice\secret",
            "pid=1234",
        )
        for invalid_id in invalid_ids:
            with self.subTest(record_id=invalid_id):
                rows = self.rows()
                rows[1][0] = invalid_id
                patches = self.ready_patches(rows)
                with patches[0], patches[1], patches[2]:
                    with self.assertRaises(self.bridge.RequestError) as caught:
                        self.bridge.ea_factory_deep_research_catalog_read_model()
                self.assertEqual(caught.exception.status, 422)
                self.assertEqual(
                    caught.exception.response_payload["code"],
                    "deep_research_schema_mismatch",
                )

    def test_catalog_record_id_length_boundary_is_shared_by_ingestion_and_selection(self) -> None:
        self.assertEqual(
            self.bridge.EA_FACTORY_DEEP_RESEARCH_RECORD_ID_MAX_CHARS,
            160,
        )
        accepted_id = "r" * self.bridge.EA_FACTORY_DEEP_RESEARCH_RECORD_ID_MAX_CHARS
        accepted_rows = self.rows()
        accepted_rows[1][0] = accepted_id
        patches = self.ready_patches(accepted_rows)
        with patches[0], patches[1], patches[2]:
            result = self.bridge.ea_factory_deep_research_catalog_read_model(
                accepted_id
            )
        self.assertEqual(result["selectedRecord"]["recordId"], accepted_id)

        rejected_id = accepted_id + "x"
        rejected_rows = self.rows()
        rejected_rows[1][0] = rejected_id
        # These rows are a new fixture snapshot.  Do not let the preceding
        # accepted snapshot satisfy this read if an ephemeral mock reuses an
        # adapter id that is still covered by the five-second catalog cache.
        with self.bridge.EA_FACTORY_DEEP_RESEARCH_CATALOG_CACHE_CONDITION:
            self.bridge.EA_FACTORY_DEEP_RESEARCH_CATALOG_CACHE.clear()
        patches = self.ready_patches(rejected_rows)
        with patches[0], patches[1], patches[2]:
            with self.assertRaises(self.bridge.RequestError) as ingestion_error:
                self.bridge.ea_factory_deep_research_catalog_read_model()
        self.assertEqual(ingestion_error.exception.status, 422)
        self.assertEqual(
            ingestion_error.exception.response_payload["code"],
            "deep_research_schema_mismatch",
        )

        with self.assertRaises(self.bridge.RequestError) as selection_error:
            self.bridge.ea_factory_deep_research_catalog_read_model(rejected_id)
        self.assertEqual(selection_error.exception.status, 422)
        self.assertEqual(
            selection_error.exception.response_payload["code"],
            "invalid_record_id",
        )

    def test_catalog_system_name_preserves_1600_to_8000_character_sheet_values(self) -> None:
        accepted: dict[int, dict] = {}
        for length in (1600, 1601, 8000):
            with self.subTest(length=length):
                with self.bridge.EA_FACTORY_DEEP_RESEARCH_CATALOG_CACHE_CONDITION:
                    self.bridge.EA_FACTORY_DEEP_RESEARCH_CATALOG_CACHE.clear()
                rows = self.rows()
                rows[1][1] = "N" * length
                patches = self.ready_patches(rows)
                with patches[0], patches[1], patches[2]:
                    result = self.bridge.ea_factory_deep_research_catalog_read_model(
                        rows[1][0]
                    )
                option = next(
                    item
                    for item in result["systems"]
                    if item["recordId"] == rows[1][0]
                )
                selected = result["selectedRecord"]
                self.assertEqual(option["systemName"], rows[1][1])
                self.assertEqual(option["displayLabel"], rows[1][1])
                self.assertEqual(selected["systemName"], rows[1][1])
                self.assertEqual(option["recordDigest"], selected["recordDigest"])
                self.assertEqual(
                    option["sourceRecordId"],
                    selected["sourceRecordId"],
                )
                accepted[length] = option

        # A change immediately beyond the old 1,600-character display cap must
        # still create a distinct immutable source identity.
        self.assertNotEqual(
            accepted[1600]["sourceRecordId"],
            accepted[1601]["sourceRecordId"],
        )
        self.assertNotEqual(
            accepted[1600]["recordDigest"],
            accepted[1601]["recordDigest"],
        )

        with self.bridge.EA_FACTORY_DEEP_RESEARCH_CATALOG_CACHE_CONDITION:
            self.bridge.EA_FACTORY_DEEP_RESEARCH_CATALOG_CACHE.clear()
        rejected_rows = self.rows()
        rejected_rows[1][1] = "N" * 8001
        patches = self.ready_patches(rejected_rows)
        with patches[0], patches[1], patches[2]:
            with self.assertRaises(self.bridge.RequestError) as oversized:
                self.bridge.ea_factory_deep_research_catalog_read_model()
        self.assertEqual(oversized.exception.status, 422)
        self.assertEqual(
            oversized.exception.response_payload["code"],
            "deep_research_schema_mismatch",
        )

    def test_create_rejects_sheet_mutation_before_any_build_side_effect(self) -> None:
        original_rows = self.rows()
        patches = self.ready_patches(original_rows)
        with patches[0], patches[1], patches[2]:
            imported = self.bridge.ea_factory_deep_research_catalog_read_model(
                original_rows[1][0]
            )
        option = next(
            item
            for item in imported["systems"]
            if item["recordId"] == original_rows[1][0]
        )
        source_key = self.bridge._ea_factory_deep_research_source_key(
            self.hub()["sheetId"],
            "Deep_Research",
        )
        source = next(
            item
            for item in self.bridge._ea_factory_parse_deep_research_values(
                original_rows,
                source_key,
            )
            if item["recordId"] == option["recordId"]
        )
        request = {
            "recordId": option["recordId"],
            "sourceRecordId": option["sourceRecordId"],
            "recordDigest": option["recordDigest"],
            "catalogDigest": imported["catalogDigest"],
            "snapshotDigest": imported["snapshotDigest"],
            "configRevision": imported["configRevision"],
            "artifactKind": "expert_advisor",
            "platform": "mt4",
            "idempotencyKey": "sheet-mutation-before-create",
        }
        mutated_rows = copy.deepcopy(original_rows)
        mutated_rows[1][3] += " Changed after import."
        live_reader = mock.Mock(
            side_effect=[copy.deepcopy(mutated_rows), copy.deepcopy(mutated_rows)]
        )
        empty_state = self.bridge._empty_ea_factory_state()

        with mock.patch.object(
            self.bridge,
            "_research_sheet_hub_internal",
            return_value=self.hub(),
        ), mock.patch.object(
            self.bridge.google_sheet_hub,
            "credential_status",
            return_value={"configured": True, "mode": "oauth"},
        ), mock.patch.object(
            self.bridge,
            "_ea_factory_read_deep_research_values",
            live_reader,
        ), mock.patch.object(
            self.bridge,
            "_load_ea_factory_state_unlocked",
            return_value=empty_state,
        ), mock.patch.object(
            self.bridge,
            "load_missions",
            return_value=[],
        ), mock.patch.object(
            self.bridge,
            "load_runtime_reports",
            return_value=[],
        ), mock.patch.object(
            self.bridge,
            "_ea_factory_source_catalog",
            return_value=[source],
        ), mock.patch.object(
            self.bridge,
            "_write_ea_factory_state_unlocked",
        ) as write_state, mock.patch.object(
            self.bridge,
            "_ea_factory_create_build_workspace",
        ) as create_workspace, mock.patch.object(
            self.bridge,
            "_ea_factory_source_report",
        ) as create_source_report, mock.patch.object(
            self.bridge,
            "create_mission",
        ) as create_mission, mock.patch.object(
            self.bridge,
            "create_report",
        ) as create_report, mock.patch.object(
            self.bridge,
            "append_audit",
        ) as append_audit:
            with self.assertRaises(self.bridge.RequestError) as stale:
                self.bridge.create_ea_factory_build(request)

        self.assertEqual(stale.exception.status, 409)
        self.assertEqual(stale.exception.code, "ea_factory_sheet_binding_stale")
        self.assertEqual(live_reader.call_count, 2)
        write_state.assert_not_called()
        create_workspace.assert_not_called()
        create_source_report.assert_not_called()
        create_mission.assert_not_called()
        create_report.assert_not_called()
        append_audit.assert_not_called()

    def test_create_sheet_binding_is_atomic_but_legacy_omission_remains_valid(self) -> None:
        source_record_id = "ea-source-binding-test"
        self.assertIsNone(
            self.bridge._ea_factory_create_sheet_binding(
                {"sourceRecordId": source_record_id},
                source_record_id,
            )
        )
        with self.assertRaises(self.bridge.RequestError) as partial:
            self.bridge._ea_factory_create_sheet_binding(
                {
                    "sourceRecordId": source_record_id,
                    "recordId": "deep-binding-test",
                },
                source_record_id,
            )
        self.assertEqual(partial.exception.status, 422)
        self.assertEqual(
            partial.exception.code,
            "ea_factory_sheet_binding_incomplete",
        )

        complete = self.bridge._ea_factory_create_sheet_binding(
            {
                "recordId": "deep-binding-test",
                "sourceRecordId": source_record_id,
                "recordDigest": "a" * 64,
                "catalogDigest": "b" * 64,
                "snapshotDigest": "c" * 64,
                "configRevision": 7,
            },
            source_record_id,
        )
        self.assertEqual(
            list(complete),
            list(self.bridge.EA_FACTORY_SHEET_CREATE_BINDING_FIELDS),
        )

    def test_full_sheet_read_keeps_sparse_records_and_rejects_cells_outside_a_to_j(self) -> None:
        headers = list(self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS)
        sheet_rows = [headers, self.rows()[1], *([[]] * 997), self.rows()[2]]
        with mock.patch.object(
            self.bridge.google_sheet_hub,
            "read_values",
            return_value=sheet_rows,
        ) as reader:
            result = self.bridge._ea_factory_read_deep_research_values(
                "1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
                "Deep_Research",
            )

        self.assertEqual(result, [headers, self.rows()[1], self.rows()[2]])
        reader.assert_called_once_with(
            "1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
            "Deep_Research",
            "A:ZZZ",
        )

        for out_of_contract_rows in (
            [[*headers, "unexpected_header"], self.rows()[1]],
            [headers, [*self.rows()[1], "unexpected_data"]],
        ):
            with self.subTest(out_of_contract_rows=out_of_contract_rows), mock.patch.object(
                self.bridge.google_sheet_hub,
                "read_values",
                return_value=out_of_contract_rows,
            ) as reader:
                with self.assertRaises(self.bridge.RequestError):
                    self.bridge._ea_factory_read_deep_research_values(
                        "1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
                        "Deep_Research",
                    )
            reader.assert_called_once_with(
                "1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
                "Deep_Research",
                "A:ZZZ",
            )

        trailing_blank_id = [headers, self.rows()[1], ["", *("poison" for _ in range(9))]]
        with mock.patch.object(
            self.bridge.google_sheet_hub,
            "read_values",
            return_value=trailing_blank_id,
        ):
            with self.assertRaises(self.bridge.RequestError):
                self.bridge._ea_factory_read_deep_research_values(
                    "1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
                    "Deep_Research",
                )

        overflow = [headers, *([[]] * self.bridge.RESEARCH_SHEET_CACHE_SCAN_MAX_ROW)]
        with mock.patch.object(
            self.bridge.google_sheet_hub,
            "read_values",
            return_value=overflow,
        ):
            with self.assertRaises(self.bridge.RequestError):
                self.bridge._ea_factory_read_deep_research_values(
                    "1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
                    "Deep_Research",
                )

        too_many = [headers]
        for index in range(self.bridge.EA_FACTORY_SOURCE_ROW_LIMIT + 1):
            row = copy.deepcopy(self.rows()[1])
            row[0] = f"deep-system-{index:03d}"
            row[1] = f"System {index:03d}"
            too_many.append(row)
        with mock.patch.object(
            self.bridge.google_sheet_hub,
            "read_values",
            return_value=too_many,
        ):
            with self.assertRaises(self.bridge.RequestError):
                self.bridge._ea_factory_read_deep_research_values(
                    "1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
                    "Deep_Research",
                )

    def test_a_to_j_read_threads_expected_google_binding_to_transport(self) -> None:
        binding = self.bridge.google_sheet_hub._direct_credential_binding(
            "access-account-a"
        )
        with mock.patch.object(
            self.bridge.google_sheet_hub,
            "read_values",
            return_value=self.rows(),
        ) as reader:
            result = self.bridge._ea_factory_read_deep_research_values(
                "1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
                "Deep_Research",
                expected_auth_binding=binding,
            )

        self.assertEqual(result, self.rows())
        reader.assert_called_once_with(
            "1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
            "Deep_Research",
            "A:ZZZ",
            expected_credential_binding=binding,
        )


class EaFactoryDeepResearchCatalogRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    @staticmethod
    def request(port: int, path: str) -> tuple[int, dict]:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        connection.request("GET", path)
        response = connection.getresponse()
        body = json.loads(response.read().decode("utf-8"))
        status = response.status
        connection.close()
        return status, body

    def test_catalog_get_route_passes_selected_record_id(self) -> None:
        model = {
            "schemaVersion": "ea-factory-deep-research-catalog-v1",
            "status": "ready",
            "systems": [],
            "selectedRecord": None,
        }
        with mock.patch.object(
            self.bridge,
            "ea_factory_deep_research_catalog_read_model",
            return_value=model,
        ) as reader:
            server = self.bridge.BridgeHTTPServer(
                ("127.0.0.1", 0),
                self.bridge.BridgeHandler,
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                status, body = self.request(
                    server.server_port,
                    "/api/props/right_server_racks/ea-factory/"
                    f"sources/google-sheet/catalog?recordId={quote('deep-system-001')}",
                )
                self.assertEqual(status, 200)
                self.assertEqual(body, {"ok": True, "catalog": model})
                reader.assert_called_once_with("deep-system-001")

                status, body = self.request(
                    server.server_port,
                    "/api/props/right_server_racks/ea-factory/"
                    "sources/google-sheet/catalog?tabName=Deep_Research",
                )
                self.assertEqual(status, 422)
                self.assertFalse(body["ok"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_catalog_get_route_preserves_fail_closed_status_and_public_code(self) -> None:
        failures = (
            (401, "auth_required"),
            (403, "permission_denied"),
            (422, "deep_research_schema_mismatch"),
            (409, "research_sheet_binding_changed"),
        )
        for status_code, error_code in failures:
            with self.subTest(error_code=error_code), mock.patch.object(
                self.bridge,
                "ea_factory_deep_research_catalog_read_model",
                side_effect=self.bridge.RequestError(
                    "Catalog blocked.",
                    status_code,
                    response_payload={
                        "kind": "ea_factory_deep_research_catalog_blocked",
                        "code": error_code,
                        "messageTh": "ยังไม่สามารถโหลดรายการ Deep_Research ได้",
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
                    status, body = self.request(
                        server.server_port,
                        "/api/props/right_server_racks/ea-factory/"
                        "sources/google-sheet/catalog",
                    )
                    self.assertEqual(status, status_code)
                    self.assertFalse(body["ok"])
                    self.assertEqual(
                        body["kind"],
                        "ea_factory_deep_research_catalog_blocked",
                    )
                    self.assertEqual(body["code"], error_code)
                    self.assertNotIn("systems", body)
                    self.assertNotIn("selectedRecord", body)
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=3)

    def test_catalog_route_supports_unicode_record_id_and_does_not_log_query(self) -> None:
        model = {
            "schemaVersion": "ea-factory-deep-research-catalog-v1",
            "status": "ready",
            "systems": [],
            "selectedRecord": None,
        }
        with mock.patch.object(
            self.bridge,
            "ea_factory_deep_research_catalog_read_model",
            return_value=model,
        ) as reader, mock.patch.object(
            self.bridge.SimpleHTTPRequestHandler,
            "log_message",
        ) as parent_log:
            server = self.bridge.BridgeHTTPServer(
                ("127.0.0.1", 0),
                self.bridge.BridgeHandler,
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                status, body = self.request(
                    server.server_port,
                    "/api/props/right_server_racks/ea-factory/"
                    "sources/google-sheet/catalog?recordId="
                    + quote("ระบบ-๑", safe=""),
                )
                self.assertEqual(status, 200)
                self.assertTrue(body["ok"])
                reader.assert_called_once_with("ระบบ-๑")
                parent_log.assert_not_called()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
