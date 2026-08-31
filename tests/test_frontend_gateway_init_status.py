from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_MAIN_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "main.js"
FRONTEND_STYLES_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "styles.css"


class FrontendGatewayInitStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        self.styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")

    def test_runtime_maps_only_public_init_diagnostic_fields(self) -> None:
        start = self.main.index("function getSignalRuntimeTruth")
        end = self.main.index("function signalMarketModel", start)
        runtime = self.main[start:end]

        self.assertIn("const gatewayInit = gateway?.initStatus", runtime)
        self.assertIn("gatewayInitStatus: {", runtime)
        for field in (
            "available",
            "readStatus",
            "eaVersion",
            "severity",
            "stage",
            "reasonCode",
            "warningCode",
            "observedAt",
            "ageSeconds",
            "stale",
            "supersededByLiveStatus",
        ):
            self.assertIn(f"{field}:", runtime)
        self.assertNotIn("channelId: gatewayInit", runtime)
        self.assertNotIn("profile: gatewayInit", runtime)

    def test_thai_message_hides_superseded_error_and_labels_current_warning(self) -> None:
        start = self.main.index("function signalGatewayInitStatusMessage")
        end = self.main.index("function getSignalRuntimeTruth", start)
        helper = self.main[start:end]

        self.assertIn('severity === "error" && superseded', helper)
        self.assertIn("EA เริ่มทำงานไม่สำเร็จ", helper)
        self.assertIn("EA เริ่มทำงานแล้ว แต่มีคำเตือน", helper)
        self.assertIn("ข้อมูลนี้เก่าและใช้เพื่อช่วยวินิจฉัยเท่านั้น", helper)
        self.assertIn("SIGNING_KEY_FILE_MISSING", helper)
        self.assertIn("SIGNING_KEY_LENGTH_INVALID", helper)

    def test_daily_connection_panel_renders_diagnostic_with_text_content(self) -> None:
        start = self.main.index("function renderSignalDailyPanel")
        end = self.main.index("async function setAiTradeCouncilAutomation", start)
        daily = self.main[start:end]

        self.assertIn("data-signal-init-diagnostic", daily)
        self.assertIn("signalGatewayInitStatusMessage(runtime.gatewayInitStatus)", daily)
        self.assertIn("initDiagnosticNode.textContent = initDiagnostic.text", daily)
        self.assertIn(".signal-init-diagnostic", self.styles)
        self.assertIn('.signal-init-diagnostic[data-tone="error"]', self.styles)


if __name__ == "__main__":
    unittest.main()
