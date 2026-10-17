from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "backend" / "local-runner" / "hq_backend" / "ea" / "ea_factory_visible_terminal_mt5.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "metafx_mt5_native_report_row_color_test", MODULE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mt5 = load_module()


def native_report_payload(bgcolor: str) -> bytes:
    report = (
        "<html><head><title>Strategy Tester Report</title></head>"
        "<body><table>"
        f'<tr bgcolor="{bgcolor}" align="right">'
        "<td>Strategy Tester Report</td>"
        "</tr></table></body></html>"
    )
    # MT5's native HTML export is UTF-16LE with a BOM.  ``utf-16`` produces
    # that exact representation on supported Windows/Python runtimes.
    return report.encode("utf-16")


class Mt5NativeReportRowColorTests(unittest.TestCase):
    def test_native_f7f7f7_row_is_accepted_by_both_html_parsers(self) -> None:
        evidence = mt5._html_report_evidence_from_payload(
            native_report_payload("#F7F7F7")
        )

        self.assertIn("Strategy Tester Report", evidence["text"])
        self.assertEqual(evidence["rows"], [["Strategy Tester Report"]])
        self.assertEqual(evidence["tables"], [[["Strategy Tester Report"]]])

    def test_non_native_nearby_row_colors_remain_rejected(self) -> None:
        for bgcolor in ("#F7F7F8", "F7F7F7", "#F7F7F7FF"):
            with self.subTest(bgcolor=bgcolor):
                with self.assertRaisesRegex(
                    mt5.VisibleTerminalAdapterError,
                    "mt5_tester_report_html_invalid",
                ):
                    mt5._html_report_evidence_from_payload(
                        native_report_payload(bgcolor)
                    )


if __name__ == "__main__":
    unittest.main()
