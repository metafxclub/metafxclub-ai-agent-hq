from __future__ import annotations

import http.client
import importlib.util
import re
import threading
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "backend" / "local-runner" / "bridge_server.py"
MT5_SOURCE_RELATIVE = "integrations/mt5-trade-gateway/MetafxHQTradeGateway.mq5"
MT5_README_RELATIVE = "integrations/mt5-trade-gateway/README_TH.md"


def load_bridge(name: str):
    spec = importlib.util.spec_from_file_location(name, BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MetaTraderGatewaySourceDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge("metafx_gateway_source_delivery")
        cls.audit_patch = mock.patch.object(cls.bridge, "append_audit")
        cls.audit_patch.start()
        cls.server = cls.bridge.BridgeHTTPServer(
            ("127.0.0.1", 0),
            cls.bridge.BridgeHandler,
        )
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        cls.audit_patch.stop()

    def request(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            int(self.server.server_port),
            timeout=3,
        )
        connection.request("GET", path, headers=headers or {})
        response = connection.getresponse()
        payload = response.read()
        headers = {key.lower(): value for key, value in response.getheaders()}
        status = response.status
        connection.close()
        return status, headers, payload

    def test_exact_allowlisted_mt4_and_mt5_sources_download_as_attachments(self) -> None:
        expected = {
            "mt4": self.bridge.METATRADER_UNIFIED_EA_SOURCE_PATH,
            "mt5": self.bridge.METATRADER_MT5_UNIFIED_EA_SOURCE_PATH,
        }
        for platform, source_path in expected.items():
            with self.subTest(platform=platform):
                status, headers, payload = self.request(
                    f"/api/integrations/metatrader/gateway-source/{platform}"
                )
                self.assertEqual(status, 200)
                self.assertEqual(payload, source_path.read_bytes())
                self.assertEqual(headers["content-type"], "text/plain; charset=utf-8")
                self.assertEqual(headers["cache-control"], "no-store")
                self.assertEqual(headers["x-content-type-options"], "nosniff")
                self.assertEqual(
                    headers["content-disposition"],
                    f'attachment; filename="{source_path.name}"',
                )

    def test_gateway_download_rejects_unknown_or_path_shaped_values(self) -> None:
        for path in (
            "/api/integrations/metatrader/gateway-source/windows",
            "/api/integrations/metatrader/gateway-source/mt5%2F..%2F..%2Fbackend%2Flocal-runner%2Fbridge_server.py",
            "/integrations/mt5-trade-gateway/MetafxHQTradeGateway.mq5",
        ):
            with self.subTest(path=path):
                status, _, payload = self.request(path)
                self.assertEqual(status, 404)
                self.assertNotIn(b"bridge_server.py", payload)

        self.assertIsNone(self.bridge.resolve_metatrader_gateway_source("../mt5"))
        self.assertIsNone(
            self.bridge.resolve_metatrader_gateway_source(
                "C:/Windows/System32/drivers/etc/hosts"
            )
        )

    def test_gateway_download_keeps_the_shared_loopback_host_guard(self) -> None:
        status, _, payload = self.request(
            "/api/integrations/metatrader/gateway-source/mt5",
            headers={"Host": "example.invalid"},
        )
        self.assertEqual(status, 403)
        self.assertIn(b"loopback", payload.lower())

    def test_council_ui_downloads_only_the_platform_selected_gateway(self) -> None:
        read_model = self.bridge._empty_metatrader_snapshot_read_model(
            "mission_strategy_table",
            "waiting_snapshot",
            "snapshot_missing",
            selected_candidate={"candidateId": "mtc-test-mt5", "platform": "mt5"},
        )
        self.assertEqual(
            read_model["installPreparation"]["sourceDownloadUrl"],
            "/api/integrations/metatrader/gateway-source/mt5",
        )
        self.assertTrue(read_model["installPreparation"]["sourceReady"])
        main = (ROOT / "frontend" / "src" / "app" / "main.js").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            '"/api/integrations/metatrader/gateway-source/mt5"',
            main,
        )
        self.assertIn(
            '"/api/integrations/metatrader/gateway-source/mt4"',
            main,
        )
        self.assertIn("data-signal-download-gateway-source", main)
        self.assertIn('download="${gatewaySource}"', main)
        self.assertIn("เลือก MT4 หรือ MT5 ก่อนดาวน์โหลด EA", main)

    def test_release_and_installer_fail_closed_when_mt5_sources_are_missing(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "publish-release.yml").read_text(
            encoding="utf-8"
        )
        installer = (ROOT / "installer" / "install.ps1").read_text(
            encoding="utf-8-sig"
        )
        preflight = (ROOT / "tests" / "test_release_candidate_preflight.py").read_text(
            encoding="utf-8"
        )
        for relative_path in (MT5_SOURCE_RELATIVE, MT5_README_RELATIVE):
            self.assertIn(relative_path.replace("/", "\\"), workflow)
            self.assertIn(relative_path.replace("/", "\\"), installer)
            self.assertIn(f'"{relative_path}"', preflight)
        self.assertIn('".mq4", ".mq5", ".ps1"', installer)

    def test_source_only_policy_ignores_uncurated_ex5_and_docs_are_portable(self) -> None:
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        readme = (ROOT / MT5_README_RELATIVE).read_text(encoding="utf-8")
        self.assertIn("integrations/mt5-trade-gateway/*.ex5", ignore)
        self.assertEqual(
            list((ROOT / "integrations" / "mt5-trade-gateway").rglob("*.ex5")),
            [],
        )
        self.assertIsNone(re.search(r"(?i)(?:[A-Z]:\\|/Users/|/home/)", readme))
        self.assertNotIn("MetafxHQTradeGateway.ex5", readme)


if __name__ == "__main__":
    unittest.main()
