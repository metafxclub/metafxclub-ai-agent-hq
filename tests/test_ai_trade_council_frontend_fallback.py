import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "frontend" / "src" / "app" / "main.js"


def function_block(source: str, signature: str) -> str:
    start = source.index(signature)
    end = source.find("\nfunction ", start + len(signature))
    return source[start : end if end >= 0 else len(source)]


class AiTradeCouncilFrontendFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main = MAIN_PATH.read_text(encoding="utf-8")

    def test_live_snapshot_fallback_preserves_real_chart_and_indicator_data(self) -> None:
        fallback = function_block(
            self.main,
            "function signalDeepLiveSnapshotFallback(",
        )
        self.assertIn("chartSnapshot.available !== true || !bars.length", fallback)
        self.assertIn("technicalIndicators", fallback)
        self.assertIn("priceActionFeatures", fallback)
        self.assertIn('displaySource: "live_chart_snapshot"', fallback)
        self.assertIn("decisionEligible: false", fallback)

    def test_deep_data_wins_and_live_snapshot_is_only_a_display_fallback(self) -> None:
        context = function_block(self.main, "function signalDeepDisplayContext(")
        shell = function_block(self.main, "function renderSignalDeepShell(")

        self.assertLess(
            context.index("deepData?.available === true"),
            context.index("signalDeepLiveSnapshotFallback(report)"),
        )
        self.assertIn("const canPreparePackage = deepData?.available === true", shell)
        self.assertIn("const canAnalyze = canPreparePackage && deepData?.decisionEligible === true", shell)
        self.assertIn('fallback ? "Snapshot ปัจจุบัน (ยังไม่ใช่ Deep 500)"', shell)

    def test_price_action_and_technical_panels_use_display_context(self) -> None:
        price_action = function_block(
            self.main,
            "function renderSignalPriceActionDeepPanel()",
        )
        technical = function_block(
            self.main,
            "function renderSignalTechnicalDeepPanel(",
        )

        self.assertIn("const { body, data, fallback } = shell;", price_action)
        self.assertIn("ยังไม่ใช่ Deep Analysis 500 แท่ง", price_action)
        self.assertIn("const { body, data, fallback } = shell;", technical)
        self.assertIn("Snapshot ปัจจุบัน: OHLC", technical)
        self.assertIn(
            "function signalDeepTechnicalSeries(data = signalDeepDisplayContext().data)",
            self.main,
        )

    def test_minimum_bar_error_is_translated_for_the_dashboard(self) -> None:
        reason = function_block(
            self.main,
            "function signalDeepUnavailableReasonLabel(",
        )
        status = function_block(
            self.main,
            "function signalDeepDataStatusMessage(",
        )

        self.assertIn('reasonCode === "minimum_500_closed_bars_required"', reason)
        self.assertIn("ข้อมูลเชิงลึกต้องใช้แท่งปิดอย่างน้อย 500 แท่ง", reason)
        self.assertIn("ยังไม่ถือเป็น Deep Analysis 500 แท่ง", status)


if __name__ == "__main__":
    unittest.main()
