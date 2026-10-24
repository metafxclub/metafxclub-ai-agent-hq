from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


class Mt5TicketBridgeProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / "backend/local-runner/bridge_server.py"
        spec = importlib.util.spec_from_file_location("mt5_ticket_projection_bridge", path)
        cls.bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.bridge)

    def test_ticket_display_preserves_actual_and_full_mt5_integer_precision(self):
        for ticket in (500029817749, 9007199254740993, 18446744073709551615):
            with self.subTest(ticket=ticket):
                result = self.bridge._mt4_trade_gateway_command_summary({
                    "command": {"commandId": "cmd-43988dc026e7d81bcfde6957"},
                    "ack": {"status": "EXECUTED", "ticket": ticket},
                })
                self.assertEqual(result["ack"]["ticket"], ticket)
                self.assertEqual(result["ack"]["ticketText"], str(ticket))

    def test_invalid_ticket_is_not_given_an_authoritative_display_identity(self):
        for ticket in (None, True, -1, 0, 500029817749.0, "500029817749"):
            with self.subTest(ticket=ticket):
                result = self.bridge._mt4_trade_gateway_command_summary({
                    "command": {}, "ack": {"status": "EXECUTED", "ticket": ticket},
                })
                self.assertIsNone(result["ack"]["ticketText"])

    def test_rejected_ack_has_exact_command_diagnostic_without_payload_acceptance(self):
        command_id = "cmd-43988dc026e7d81bcfde6957"
        result = self.bridge._mt4_trade_gateway_ack_event_read_model({
            "kind": "ack_rejected", "fileName": command_id + ".json",
            "code": "invalid_ack_ticket",
        })
        self.assertEqual(result["commandId"], command_id)
        self.assertEqual(result["code"], "invalid_ack_ticket")
        self.assertNotIn("fileName", result)
        self.assertNotIn("ticket", result)
        self.assertNotIn("orderExecutionConfirmed", result)

    def test_rejected_ack_never_extracts_command_from_arbitrary_path(self):
        name = "cmd-43988dc026e7d81bcfde6957.json"
        for bad in ("../" + name, "C:/private/" + name, name + ".bak", "cmd-bad.json"):
            with self.subTest(name=bad):
                result = self.bridge._mt4_trade_gateway_ack_event_read_model({
                    "kind": "ack_rejected", "fileName": bad,
                })
                self.assertIsNone(result["commandId"])
                self.assertNotIn("fileName", result)


if __name__ == "__main__":
    unittest.main()
