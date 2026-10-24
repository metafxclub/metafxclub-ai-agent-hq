from __future__ import annotations

import copy
import importlib.util
import json
import threading
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


class EaFactorySyncTransactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location(
            "ea_factory_sync_transaction_bridge",
            ROOT / "backend/local-runner/bridge_server.py",
        )
        cls.bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.bridge)

    def setUp(self) -> None:
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.events = []
        self.missions = {}
        self.reports = []
        self.state = self.bridge._empty_ea_factory_state()
        self.hub = {"sheetId": "1FactorySyncTransactionSyntheticSheet0123456789", "configRevision": 7}
        self.request = {"configRevision": 7, "idempotencyKey": "factory-sync-transaction"}
        replacements = {
            "_research_sheet_hub_internal": {"return_value": self.hub},
            "find_mission_by_idempotency": {"side_effect": lambda key: copy.deepcopy(self.missions.get(key))},
            "create_mission": {"side_effect": self.create_mission},
            "replace_mission": {"side_effect": lambda row: self.missions.update({row["idempotencyKey"]: copy.deepcopy(row)})},
            "create_report": {"side_effect": self.create_report},
            "append_audit": {},
            "_load_ea_factory_state_unlocked": {"side_effect": self.load_state},
            "_write_ea_factory_state_unlocked": {"side_effect": self.write_state},
            "_ea_factory_read_deep_research_values": {"return_value": [["header"], ["row"]]},
            "_ea_factory_parse_deep_research_values": {"return_value": [{
                "sourceRecordId": "ea-source-transaction", "recordDigest": "a" * 64,
            }]},
        }
        self.mocks = {name: self.stack.enter_context(mock.patch.object(self.bridge, name, **options)) for name, options in replacements.items()}
        self.stack.enter_context(mock.patch.object(self.bridge.google_sheet_hub, "credential_status", return_value={"configured": True}))

    def create_mission(self, payload, *, status):
        key = payload["idempotencyKey"]
        if key not in self.missions:
            self.missions[key] = {
                **copy.deepcopy(payload), "id": "mission-sync-transaction", "status": status,
                "owner": "mission_archivist", "createdAt": "2026-10-18T05:00:00Z",
                "updatedAt": "2026-10-18T05:00:00Z", "reportIds": [],
            }
        return copy.deepcopy(self.missions[key])

    def create_report(self, payload):
        if payload["status"] == "ready":
            self.assertTrue(self.bridge._ea_factory_lock_owned_by_current_thread())
        self.events.append("report:" + payload["status"])
        row = {**copy.deepcopy(payload), "id": f"report-sync-transaction-{len(self.reports) + 1}"}
        self.reports.append(row)
        return row

    def load_state(self):
        self.assertTrue(self.bridge._ea_factory_lock_owned_by_current_thread())
        self.events.append("validate")
        return copy.deepcopy(self.state)

    def write_state(self, payload):
        self.assertTrue(self.bridge._ea_factory_lock_owned_by_current_thread())
        self.events.append("persist")
        self.state = copy.deepcopy(payload)

    def wire_result(self, payload):
        handler = object.__new__(self.bridge.BridgeHandler)
        handler.send_preencoded_json = mock.Mock()
        handler.send_result(payload)
        return json.loads(handler.send_preencoded_json.call_args.args[0])

    def test_validation_precedes_own_report_and_receipt_survives_wire_projection(self):
        result = self.bridge.sync_ea_factory_google_sheet(self.request)
        self.assertEqual(self.events, ["validate", "report:ready", "persist"])
        wire = self.wire_result(result)
        self.assertNotIn("idempotencyKey", wire["mission"])
        self.assertEqual(wire["requestIdempotencyKey"], self.request["idempotencyKey"])
        self.assertEqual(wire["configRevision"], 7)
        self.assertEqual(wire["mission"]["status"], "completed")
        self.assertEqual(
            wire["report"]["metrics"]["eaFactorySource"]["snapshotDigest"],
            self.state["sourceSnapshots"][0]["snapshotDigest"],
        )
        self.assertEqual(wire["sourceSnapshot"]["reportId"], wire["report"]["id"])

    def test_invalid_existing_state_creates_only_a_linked_failure_report(self):
        self.mocks["_load_ea_factory_state_unlocked"].side_effect = self.bridge.DataIntegrityError("invalid historical evidence")
        with self.assertRaises(self.bridge.RequestError):
            self.bridge.sync_ea_factory_google_sheet(self.request)
        self.mocks["_write_ea_factory_state_unlocked"].assert_not_called()
        self.assertEqual([row["status"] for row in self.reports], ["failed"])
        mission = self.missions[self.request["idempotencyKey"]]
        self.assertEqual(mission["status"], "failed")
        self.assertEqual(mission["reportIds"], [self.reports[0]["id"]])
        self.assertEqual(self.reports[0]["linkedMissionId"], mission["id"])

    def test_replay_reuses_exact_receipt_without_second_read_or_report(self):
        first = self.bridge.sync_ea_factory_google_sheet(self.request)
        second = self.bridge.sync_ea_factory_google_sheet(self.request)
        self.assertTrue(second["idempotentReplay"])
        self.assertEqual(first["sourceSnapshot"], second["sourceSnapshot"])
        self.assertEqual(len(self.reports), 1)
        self.mocks["_ea_factory_read_deep_research_values"].assert_called_once()
        wire = self.wire_result(second)
        self.assertNotIn("idempotencyKey", wire["mission"])
        self.assertEqual(wire["requestIdempotencyKey"], self.request["idempotencyKey"])
        self.assertEqual(wire["configRevision"], 7)
        # An old retry cannot relabel its request as a newer central revision.
        self.hub["configRevision"] = 8
        with self.assertRaises(self.bridge.RequestError) as error:
            self.bridge.sync_ea_factory_google_sheet(self.request)
        self.assertEqual(error.exception.status, 409)
        self.assertEqual(len(self.reports), 1)
        self.mocks["_ea_factory_read_deep_research_values"].assert_called_once()

    def test_waiting_sync_preserves_state_committed_before_it_gets_lock(self):
        sheet_read = threading.Event()
        self.mocks["_ea_factory_read_deep_research_values"].side_effect = lambda *args: sheet_read.set() or [["header"], ["row"]]
        results, errors = [], []

        def run():
            try:
                results.append(self.bridge.sync_ea_factory_google_sheet(self.request))
            except Exception as error:
                errors.append(error)

        thread = threading.Thread(target=run)
        with self.bridge.EA_FACTORY_LOCK:
            thread.start()
            reached_read = sheet_read.wait(3)
            self.state["customSources"] = [{"concurrentlyCommittedSource": True}]
            self.state["sourceSnapshots"] = [{"sourceKey": "sheet-other-transaction"}]
        thread.join(5)
        self.assertTrue(reached_read)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 1)
        self.assertEqual(self.state["customSources"], [{"concurrentlyCommittedSource": True}])
        self.assertIn("sheet-other-transaction", [row["sourceKey"] for row in self.state["sourceSnapshots"]])
        self.assertEqual(self.events, ["validate", "report:ready", "persist"])


if __name__ == "__main__":
    unittest.main()
