from __future__ import annotations

import base64
import http.client
import importlib.util
import json
import threading
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location("metafx_ohlc_bridge", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OhlcBridgeEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def request(self, payload: dict) -> tuple[int, dict]:
        server = self.bridge.BridgeHTTPServer(("127.0.0.1", 0), self.bridge.BridgeHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            body = json.dumps(payload).encode("utf-8")
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            connection.request(
                "POST",
                "/api/props/left_server_racks/ohlc/import",
                body=body,
                headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
            )
            response = connection.getresponse()
            decoded = json.loads(response.read().decode("utf-8"))
            connection.close()
            return response.status, decoded
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_valid_csv_is_returned_in_memory_without_network_persistence_or_mt(self) -> None:
        csv_bytes = (
            b"DateTime,Open,High,Low,Close\n"
            b"2025-01-01 00:00:00,100,102,99,101\n"
            b"2025-01-01 01:00:00,101,103,100,102\n"
        )
        audit_events: list[dict] = []
        with mock.patch.object(self.bridge, "append_audit", side_effect=audit_events.append):
            status, body = self.request({
                "fileName": "prices.csv",
                "contentBase64": base64.b64encode(csv_bytes).decode("ascii"),
                "timeframe": "H1",
            })

        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["kind"], "ohlc_import_ready")
        self.assertEqual(body["rowCount"], 2)
        self.assertEqual(len(body["bars"]), 2)
        self.assertEqual(
            body["privacy"],
            {
                "localOnly": True,
                "networkUpload": False,
                "filePersisted": False,
                "metaTraderActions": False,
            },
        )
        self.assertEqual(len(audit_events), 1)
        self.assertEqual(audit_events[0]["type"], "research.ohlc_imported")
        self.assertFalse(audit_events[0]["filePersisted"])
        self.assertFalse(audit_events[0]["networkUpload"])
        self.assertFalse(audit_events[0]["metaTraderActions"])

    def test_invalid_ohlc_is_rejected_with_stable_code_and_no_audit_success(self) -> None:
        invalid = b"DateTime,Open,High,Low,Close\n2025-01-01,100,99,98,101\n"
        audit_events: list[dict] = []
        with mock.patch.object(self.bridge, "append_audit", side_effect=audit_events.append):
            status, body = self.request({
                "fileName": "invalid.csv",
                "contentBase64": base64.b64encode(invalid).decode("ascii"),
                "timeframe": "H1",
            })

        self.assertEqual(status, 422)
        self.assertFalse(body["ok"])
        self.assertEqual(body["kind"], "ohlc_import_rejected")
        self.assertEqual(body["code"], "invalid_ohlc_range")
        self.assertEqual(audit_events, [])


if __name__ == "__main__":
    unittest.main()
