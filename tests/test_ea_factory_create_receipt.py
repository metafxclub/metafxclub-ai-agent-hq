"""Verify durable Create receipts through the actual sanitized HTTP response."""
from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


class EaFactoryCreateReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location(
            "ea_factory_create_receipt_bridge",
            ROOT / "backend/local-runner/bridge_server.py",
        )
        cls.bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.bridge)

    def setUp(self) -> None:
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.state = self.bridge._empty_ea_factory_state()
        self.record = self.bridge._ea_factory_normalize_record(
            {
                "record_id": "receipt-system-001",
                "system_name": "Receipt Verified System",
                "system_overview": "Closed-bar EMA trend system for a selected liquid market and timeframe.",
                "entry_rules": "Buy on a confirmed fast EMA cross above slow; sell on the inverse closed-bar cross.",
                "recovery_rules": "No recovery, grid, martingale, averaging, or hedging.",
                "exit_rules": "Close on the opposite signal with bounded stop loss and take profit.",
                "money_management": "Use a positive fixed lot and at most one managed position.",
                "order_execution": "Use market buy and sell orders on a new confirmed bar.",
                "display_requirements": "Display system name, signal, Balance, Equity, and Spread.",
                "additional_notes": "Compile and backtest separately before use.",
            },
            source_kind="verified_deep_research_sheet",
            source_key="sheet-create-receipt",
        )
        self.assertTrue(self.record["buildReady"])
        self.binding = {
            "recordId": self.record["recordId"],
            "sourceRecordId": self.record["sourceRecordId"],
            "recordDigest": self.record["recordDigest"],
            "catalogDigest": "c" * 64,
            "snapshotDigest": "d" * 64,
            "configRevision": 7,
        }
        self.payload = {
            **self.binding,
            "platform": "mt5",
            "artifactKind": "expert_advisor",
            "brief": "Compile and test only after independent stage admission.",
            "idempotencyKey": "create-durable-receipt",
        }
        self.build_id = "ea-build-durable-receipt"
        self.mission = {
            "id": "mission-create-receipt", "status": "completed",
            "owner": "mission_archivist", "targetId": "right_server_racks",
            "toolId": "ea_factory_strategy_spec", "reportIds": ["report-create-receipt"],
        }
        self.report = {"id": "report-create-receipt", "status": "ready"}
        self.workspace = {
            "storageScope": "repo_managed_workspace",
            "workspaceId": "ea-workspace-create-receipt",
            "folderNames": list(self.bridge.EA_FACTORY_BUILD_FOLDER_NAMES),
            "strategySpecFile": "Source/strategy-spec-v01.json",
            "strategySpecDigest": "e" * 64,
            "rawFilesystemPathExposed": False,
        }
        replacements = {
            "_ea_factory_require_top_header_locks": {"return_value": {}},
            "_load_ea_factory_state_unlocked": {"side_effect": self.load_state},
            "_write_ea_factory_state_unlocked": {"side_effect": self.write_state},
            "load_missions": {"return_value": []},
            "load_runtime_reports": {"return_value": []},
            "_ea_factory_source_catalog": {"return_value": [self.record]},
            "_ea_factory_verify_live_sheet_create_binding": {"return_value": {}},
            "safe_id": {"return_value": self.build_id},
            "_ea_factory_create_build_workspace": {"return_value": self.workspace},
            "_ea_factory_source_report": {"return_value": (self.mission, self.report)},
            "_ea_factory_register_artifacts": {"return_value": []},
            "append_audit": {},
            "ea_factory_read_model": {"side_effect": AssertionError("Create acknowledgement must not load Factory projection")},
            "_ea_factory_build_read_model": {"side_effect": AssertionError("Receipt must not grant projected Build authority")},
        }
        self.mocks = {
            name: self.stack.enter_context(mock.patch.object(self.bridge, name, **options))
            for name, options in replacements.items()
        }

    def load_state(self):
        self.assertTrue(self.bridge._ea_factory_lock_owned_by_current_thread())
        state = copy.deepcopy(self.state)
        # The real loader derives this field after validating the durable source.
        for build in state["builds"]:
            build["coverageStatus"] = "compact_current"
        return state

    def write_state(self, state):
        self.assertTrue(self.bridge._ea_factory_lock_owned_by_current_thread())
        self.state = copy.deepcopy(state)

    def post(self, payload=None):
        handler = object.__new__(self.bridge.BridgeHandler)
        handler.path = "/api/props/right_server_racks/ea-factory/builds"
        handler.validate_local_request = mock.Mock()
        handler.validate_full_agent_mutation_request = mock.Mock()
        handler.read_payload = mock.Mock(return_value=copy.deepcopy(self.payload if payload is None else payload))
        handler.send_preencoded_json = mock.Mock()
        handler.do_POST()
        handler.send_preencoded_json.assert_called_once()
        call = handler.send_preencoded_json.call_args
        body = json.loads(call.args[0])
        return call.kwargs.get("status", 200), body

    def assert_receipt(self, body, *, replayed=False, key=None):
        persisted = self.state["builds"][0]
        self.assertTrue(body["ok"])
        self.assertEqual(body["kind"], "ea_factory_build_replayed" if replayed else "ea_factory_build_created")
        self.assertEqual(body["idempotentReplay"], replayed)
        self.assertEqual(body["requestIdempotencyKey"], key or self.payload["idempotencyKey"])
        self.assertEqual(body["createRequestDigest"], persisted["createRequestDigest"])
        self.assertRegex(body["createRequestDigest"], r"^[0-9a-f]{64}$")
        self.assertNotIn("eaFactory", body)
        self.assertEqual(body["eaFactoryReadResult"], {
            "kind": "ea_factory_refresh_deferred", "status": "deferred",
            "refreshEndpoint": "/api/props/right_server_racks/ea-factory",
            "readinessConfirmed": False,
        })
        build = body["build"]
        for field in ("id", "sourceRecordId", "sourceRecordDigest", "platform", "artifactKind",
                      "brief", "createRequestDigest", "createdAt", "updatedAt"):
            self.assertEqual(build[field], persisted[field], field)
        self.assertEqual(build["createSheetBinding"], self.binding)
        for forbidden in ("canRun", "status", "oneClickRun", "oneClick", "workspace", "stages", "files", "canAdvance"):
            self.assertNotIn(forbidden, build)
        self.mocks["ea_factory_read_model"].assert_not_called()
        self.mocks["_ea_factory_build_read_model"].assert_not_called()

    def test_fresh_and_replayed_http_receipts_preserve_exact_identity_without_projection(self):
        status, first = self.post()
        self.assertEqual(status, 200)
        self.assert_receipt(first)
        self.assertEqual(first["mission"]["id"], self.mission["id"])
        self.mocks["_ea_factory_verify_live_sheet_create_binding"].assert_called_once_with(self.binding, self.record)
        writes = self.mocks["_write_ea_factory_state_unlocked"].call_count
        status, replay = self.post()
        self.assertEqual(status, 200)
        self.assert_receipt(replay, replayed=True)
        self.assertIsNone(replay["mission"])
        self.assertEqual(replay["build"]["id"], first["build"]["id"])
        self.assertEqual(len(self.state["builds"]), 1)
        self.assertEqual(self.mocks["_write_ea_factory_state_unlocked"].call_count, writes)
        self.mocks["_ea_factory_create_build_workspace"].assert_called_once()
        self.mocks["_ea_factory_source_report"].assert_called_once()

    def test_exact_persisted_alias_returns_the_alias_without_another_build(self):
        self.post()
        alias = "create-recovered-alias"
        self.state["builds"][0]["createIdempotencyKeys"].append(alias)
        status, receipt = self.post({**self.payload, "idempotencyKey": alias})
        self.assertEqual(status, 200)
        self.assert_receipt(receipt, replayed=True, key=alias)
        self.assertEqual(len(self.state["builds"]), 1)
        self.mocks["_ea_factory_create_build_workspace"].assert_called_once()

    def test_same_key_changed_intent_is_rejected_without_new_side_effects(self):
        self.post()
        writes = self.mocks["_write_ea_factory_state_unlocked"].call_count
        for changed in ({"brief": "Different requested system"}, {"catalogDigest": "a" * 64}, {"platform": "mt4"}):
            with self.subTest(changed=changed):
                status, result = self.post({**self.payload, **changed})
                self.assertEqual(status, 409)
                self.assertFalse(result["ok"])
                self.assertEqual(result["code"], "ea_factory_create_key_conflict")
                self.assertNotIn("build", result)
        self.assertEqual(self.mocks["_write_ea_factory_state_unlocked"].call_count, writes)
        self.mocks["_ea_factory_create_build_workspace"].assert_called_once()
        self.mocks["ea_factory_read_model"].assert_not_called()

    def test_header_integrity_and_live_binding_rejections_remain_fail_closed(self):
        failures = (
            ("_ea_factory_require_top_header_locks", self.bridge.RequestError("Header locks unavailable", 409), 409),
            ("_load_ea_factory_state_unlocked", self.bridge.DataIntegrityError("Invalid existing Factory evidence"), 503),
            ("_ea_factory_verify_live_sheet_create_binding", self.bridge.RequestError("Sheet binding changed", 409), 409),
        )
        for name, error, expected_status in failures:
            with self.subTest(guard=name), mock.patch.object(self.bridge, name, side_effect=error):
                status, result = self.post()
                self.assertEqual(status, expected_status)
                self.assertFalse(result["ok"])
                self.assertNotIn("build", result)
        self.assertEqual(self.state["builds"], [])
        self.mocks["_write_ea_factory_state_unlocked"].assert_not_called()
        self.mocks["_ea_factory_create_build_workspace"].assert_not_called()
        self.mocks["_ea_factory_source_report"].assert_not_called()
        self.mocks["ea_factory_read_model"].assert_not_called()

    def test_receipt_helper_rejects_an_unrecorded_key(self):
        self.post()
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.bridge._ea_factory_create_commit_receipt(
                self.state["builds"][0], "unrelated-request-key", replayed=True,
            )


if __name__ == "__main__":
    unittest.main()
