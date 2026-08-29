import base64
import importlib.util
import io
import sys
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "backend" / "local-runner" / "ohlc_import.py"
SPEC = importlib.util.spec_from_file_location("ohlc_import_under_test", MODULE_PATH)
ohlc = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = ohlc
SPEC.loader.exec_module(ohlc)


def encoded(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def minimal_xlsx(rows):
    shared = []
    shared_index = {}

    def string_id(value):
        if value not in shared_index:
            shared_index[value] = len(shared)
            shared.append(value)
        return shared_index[value]

    row_xml = []
    for row_number, row in enumerate(rows, start=1):
        cells = []
        for column, value in enumerate(row):
            reference = f"{chr(65 + column)}{row_number}"
            if isinstance(value, str):
                cells.append(f'<c r="{reference}" t="s"><v>{string_id(value)}</v></c>')
            else:
                cells.append(f'<c r="{reference}"><v>{value}</v></c>')
        row_xml.append(f'<row r="{row_number}">{"".join(cells)}</row>')
    shared_xml = "".join(f"<si><t>{value}</t></si>" for value in shared)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"/>")
        archive.writestr("xl/workbook.xml", """<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="OHLC" sheetId="1" r:id="rId1"/></sheets></workbook>""")
        archive.writestr("xl/_rels/workbook.xml.rels", """<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>""")
        archive.writestr("xl/sharedStrings.xml", f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">{shared_xml}</sst>')
        archive.writestr("xl/worksheets/sheet1.xml", f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(row_xml)}</sheetData></worksheet>')
    return output.getvalue()


class OhlcImportTests(unittest.TestCase):
    def test_csv_is_normalized_without_persisting_or_network(self):
        data = b"Date,Open,High,Low,Close\n2026-01-01,100,105,99,104\n2026-01-02,104,108,101,102\n"
        result = ohlc.parse_ohlc_upload({"fileName": "bars.csv", "contentBase64": encoded(data), "timeframe": "D1"})
        self.assertEqual(result["rowCount"], 2)
        self.assertEqual(result["bars"][0]["close"], 104.0)
        self.assertFalse(result["file"]["persisted"])
        self.assertTrue(result["privacy"]["localOnly"])
        self.assertFalse(result["privacy"]["metaTraderActions"])

    def test_csv_rejects_invalid_high_low_relationship(self):
        data = b"Date,Open,High,Low,Close\n2026-01-01,100,101,99,104\n"
        with self.assertRaisesRegex(ohlc.OhlcImportError, "High/Low"):
            ohlc.parse_ohlc_upload({"fileName": "bars.csv", "contentBase64": encoded(data), "timeframe": "D1"})

    def test_csv_rejects_more_than_ten_years(self):
        data = b"Date,Open,High,Low,Close\n2015-01-01,100,105,99,104\n2026-01-02,104,108,101,102\n"
        with self.assertRaisesRegex(ohlc.OhlcImportError, "10"):
            ohlc.parse_ohlc_upload({"fileName": "bars.csv", "contentBase64": encoded(data), "timeframe": "D1"})

    def test_xlsx_shared_strings_and_numeric_prices_are_supported(self):
        data = minimal_xlsx([
            ["Date", "Open", "High", "Low", "Close"],
            ["2026-01-01", 100, 105, 99, 104],
            ["2026-01-02", 104, 108, 101, 102],
        ])
        result = ohlc.parse_ohlc_upload({"fileName": "bars.xlsx", "contentBase64": encoded(data), "timeframe": "H1"})
        self.assertEqual(result["sheetName"], "OHLC")
        self.assertEqual(result["rowCount"], 2)
        self.assertEqual(result["timeframe"], "H1")

    def test_rejects_invalid_base64_and_file_type(self):
        with self.assertRaises(ohlc.OhlcImportError):
            ohlc.parse_ohlc_upload({"fileName": "bars.csv", "contentBase64": "***", "timeframe": "D1"})
        with self.assertRaises(ohlc.OhlcImportError):
            ohlc.parse_ohlc_upload({"fileName": "bars.xls", "contentBase64": encoded(b"x"), "timeframe": "D1"})

    def test_rejects_duplicate_timestamp(self):
        data = b"Date,Open,High,Low,Close\n2026-01-01,100,105,99,104\n2026-01-01,104,108,101,102\n"
        with self.assertRaisesRegex(ohlc.OhlcImportError, "ซ้ำ"):
            ohlc.parse_ohlc_upload({"fileName": "bars.csv", "contentBase64": encoded(data), "timeframe": "D1"})


if __name__ == "__main__":
    unittest.main()
