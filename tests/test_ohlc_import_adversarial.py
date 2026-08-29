from __future__ import annotations

import base64
import importlib.util
import io
import sys
import unittest
import warnings
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "backend" / "local-runner" / "ohlc_import.py"
SPEC = importlib.util.spec_from_file_location("ohlc_import_adversarial", MODULE_PATH)
ohlc = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = ohlc
SPEC.loader.exec_module(ohlc)


def encoded(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def xlsx_package(
    sheet_xml: str,
    *,
    shared_xml: str | None = None,
    workbook_xml: str | None = None,
    relationships_xml: str | None = None,
    compression: int = zipfile.ZIP_DEFLATED,
    extra_members: list[tuple[str, bytes | str]] | None = None,
) -> bytes:
    workbook = workbook_xml or (
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="OHLC" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    relationships = relationships_xml or (
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/></Relationships>'
    )
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=compression) as archive:
        archive.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", relationships)
        if shared_xml is not None:
            archive.writestr("xl/sharedStrings.xml", shared_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        for name, value in extra_members or []:
            archive.writestr(name, value)
    return output.getvalue()


SHARED_VALUES = ("Date", "Open", "High", "Low", "Close", "2026-01-01")
SHARED_XML = (
    '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    + "".join(f"<si><t>{value}</t></si>" for value in SHARED_VALUES)
    + "</sst>"
)


def worksheet_with_price_cell(price_cell: str, *, date_cell: str = '<c r="A2" t="s"><v>5</v></c>') -> str:
    return (
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
        '<row r="1">'
        '<c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c>'
        '<c r="C1" t="s"><v>2</v></c><c r="D1" t="s"><v>3</v></c>'
        '<c r="E1" t="s"><v>4</v></c></row>'
        f'<row r="2">{date_cell}{price_cell}'
        '<c r="C2"><v>105</v></c><c r="D2"><v>99</v></c><c r="E2"><v>104</v></c>'
        "</row></sheetData></worksheet>"
    )


def parse_xlsx(data: bytes):
    return ohlc.parse_ohlc_upload(
        {"fileName": "bars.xlsx", "contentBase64": encoded(data), "timeframe": "D1"}
    )


class OhlcImportAdversarialTests(unittest.TestCase):
    def assert_code(self, expected: str, callback) -> None:
        with self.assertRaises(ohlc.OhlcImportError) as captured:
            callback()
        self.assertEqual(expected, captured.exception.code)

    def test_cached_xlsx_formula_and_boolean_price_are_rejected(self) -> None:
        formula = worksheet_with_price_cell('<c r="B2"><f>50+50</f><v>100</v></c>')
        self.assert_code(
            "xlsx_formula_rejected",
            lambda: parse_xlsx(xlsx_package(formula, shared_xml=SHARED_XML)),
        )

        boolean = worksheet_with_price_cell('<c r="B2" t="b"><v>1</v></c>')
        self.assert_code(
            "invalid_price",
            lambda: parse_xlsx(xlsx_package(boolean, shared_xml=SHARED_XML)),
        )

        namespace_evasion = worksheet_with_price_cell(
            '<c r="B2"><f xmlns="">50+50</f><v>100</v></c>'
        )
        self.assert_code(
            "xlsx_formula_rejected",
            lambda: parse_xlsx(xlsx_package(namespace_evasion, shared_xml=SHARED_XML)),
        )

    def test_negative_shared_string_index_and_duplicate_cell_are_rejected(self) -> None:
        negative_index = worksheet_with_price_cell(
            '<c r="B2"><v>100</v></c>',
            date_cell='<c r="A2" t="s"><v>-1</v></c>',
        )
        self.assert_code(
            "xlsx_shared_string_invalid",
            lambda: parse_xlsx(xlsx_package(negative_index, shared_xml=SHARED_XML)),
        )

        negative_zero_index = negative_index.replace("<v>-1</v>", "<v>-0</v>")
        self.assert_code(
            "xlsx_shared_string_invalid",
            lambda: parse_xlsx(xlsx_package(negative_zero_index, shared_xml=SHARED_XML)),
        )

        duplicate = worksheet_with_price_cell(
            '<c r="B2"><v>100</v></c><c r="B2"><v>101</v></c>'
        )
        self.assert_code(
            "xlsx_duplicate_cell",
            lambda: parse_xlsx(xlsx_package(duplicate, shared_xml=SHARED_XML)),
        )

        malformed_reference = duplicate.replace('r="B2"', 'r="Bevil"', 1)
        self.assert_code(
            "xlsx_cell_reference_invalid",
            lambda: parse_xlsx(xlsx_package(malformed_reference, shared_xml=SHARED_XML)),
        )

    def test_invalid_clock_values_fail_with_stable_codes(self) -> None:
        for time_value in ("24:00", "12:60", "12:30:60"):
            with self.subTest(time=time_value):
                csv_bytes = (
                    "Date,Time,Open,High,Low,Close\n"
                    f"2026-01-01,{time_value},100,105,99,104\n"
                ).encode("utf-8")
                self.assert_code(
                    "invalid_time",
                    lambda data=csv_bytes: ohlc.parse_ohlc_upload(
                        {"fileName": "bars.csv", "contentBase64": encoded(data), "timeframe": "D1"}
                    ),
                )

        self.assert_code(
            "invalid_time",
            lambda: ohlc._parse_datetime(45_000.0, date_1904=False, time_value=-0.5),
        )

    def test_timezone_equivalent_duplicates_are_detected_and_unordered_input_is_sorted(self) -> None:
        duplicate = (
            b"DateTime,Open,High,Low,Close\n"
            b"2026-01-01T07:00:00+07:00,100,105,99,104\n"
            b"2026-01-01T00:00:00Z,104,108,101,102\n"
        )
        self.assert_code(
            "duplicate_timestamp",
            lambda: ohlc.parse_ohlc_upload(
                {"fileName": "bars.csv", "contentBase64": encoded(duplicate), "timeframe": "H1"}
            ),
        )

        unordered = (
            b"DateTime,Open,High,Low,Close\n"
            b"2026-01-02,104,108,101,102\n"
            b"2026-01-01,100,105,99,104\n"
        )
        parsed = ohlc.parse_ohlc_upload(
            {"fileName": "bars.csv", "contentBase64": encoded(unordered), "timeframe": "D1"}
        )
        self.assertEqual(
            ["2026-01-01T00:00:00", "2026-01-02T00:00:00"],
            [bar["time"] for bar in parsed["bars"]],
        )

        subsecond = (
            b"DateTime,Open,High,Low,Close\n"
            b"2026-01-01T00:00:00.100000,100,105,99,104\n"
        )
        self.assert_code(
            "subsecond_timestamp_rejected",
            lambda: ohlc.parse_ohlc_upload(
                {"fileName": "bars.csv", "contentBase64": encoded(subsecond), "timeframe": "H1"}
            ),
        )

    def test_nan_infinity_and_duplicate_headers_are_rejected(self) -> None:
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                data = (
                    "Date,Open,High,Low,Close\n"
                    f"2026-01-01,{value},105,99,104\n"
                ).encode("utf-8")
                self.assert_code(
                    "invalid_price",
                    lambda payload=data: ohlc.parse_ohlc_upload(
                        {"fileName": "bars.csv", "contentBase64": encoded(payload), "timeframe": "D1"}
                    ),
                )
        duplicate_header = b"Date,Open,O,High,Low,Close\n2026-01-01,100,100,105,99,104\n"
        self.assert_code(
            "duplicate_ohlc_column",
            lambda: ohlc.parse_ohlc_upload(
                {"fileName": "bars.csv", "contentBase64": encoded(duplicate_header), "timeframe": "D1"}
            ),
        )

    def test_excel_1900_serial_discontinuity_is_interpreted_deterministically(self) -> None:
        self.assertEqual("1900-01-01", ohlc._excel_datetime(1.0, False).date().isoformat())
        self.assertEqual("1900-02-28", ohlc._excel_datetime(59.0, False).date().isoformat())
        self.assertEqual("1900-02-28", ohlc._excel_datetime(60.0, False).date().isoformat())
        self.assertEqual("1900-03-01", ohlc._excel_datetime(61.0, False).date().isoformat())
        self.assert_code("invalid_datetime", lambda: ohlc._excel_datetime(1e20, False))

    def test_xlsx_duplicate_members_unsupported_compression_and_zip_bomb_are_rejected(self) -> None:
        output = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("xl/workbook.xml", "one")
                archive.writestr("xl/workbook.xml", "two")
        self.assert_code("unsafe_xlsx_archive", lambda: ohlc._xlsx_archive(output.getvalue()))

        bzip_data = xlsx_package(
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData/></worksheet>',
            compression=zipfile.ZIP_BZIP2,
        )
        self.assert_code("unsafe_xlsx_archive", lambda: ohlc._xlsx_archive(bzip_data))

        bomb = io.BytesIO()
        with zipfile.ZipFile(bomb, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("xl/bomb.bin", b"A" * (2 * 1024 * 1024))
        self.assertLess(len(bomb.getvalue()), 100_000)
        self.assert_code("xlsx_compression_ratio", lambda: ohlc._xlsx_archive(bomb.getvalue()))

    def test_dtd_external_relationship_and_formula_like_xml_never_execute(self) -> None:
        dtd_workbook = (
            '<!DOCTYPE workbook [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="&xxe;" sheetId="1" r:id="rId1"/></sheets></workbook>'
        )
        empty_sheet = '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData/></worksheet>'
        self.assert_code(
            "unsafe_xlsx_xml",
            lambda: parse_xlsx(xlsx_package(empty_sheet, workbook_xml=dtd_workbook)),
        )

        utf16_workbook = dtd_workbook.encode("utf-16")
        self.assert_code(
            "unsafe_xlsx_xml",
            lambda: parse_xlsx(xlsx_package(empty_sheet, workbook_xml=utf16_workbook)),
        )

        external_relationship = (
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" TargetMode="External" Target="https://example.com/sheet.xml"/>'
            "</Relationships>"
        )
        self.assert_code(
            "unsafe_xlsx_target",
            lambda: parse_xlsx(xlsx_package(empty_sheet, relationships_xml=external_relationship)),
        )

    def test_row_file_and_ten_year_limits_hold_at_both_boundaries(self) -> None:
        at_limit = b"h\n" + (b"x\n" * ohlc.MAX_ROWS)
        self.assertEqual(ohlc.MAX_ROWS + 1, len(ohlc._csv_table(at_limit).rows))
        over_limit = at_limit + b"x\n"
        self.assert_code("too_many_rows", lambda: ohlc._csv_table(over_limit))

        exact_size = b"x" * ohlc.MAX_FILE_BYTES
        self.assertEqual(ohlc.MAX_FILE_BYTES, len(ohlc._decode_payload(encoded(exact_size))))
        self.assert_code(
            "file_too_large",
            lambda: ohlc._decode_payload(encoded(exact_size + b"x")),
        )

        leap_boundary = (
            b"Date,Open,High,Low,Close\n"
            b"2016-02-29,100,105,99,104\n"
            b"2026-02-28,104,108,101,102\n"
        )
        accepted = ohlc.parse_ohlc_upload(
            {"fileName": "bars.csv", "contentBase64": encoded(leap_boundary), "timeframe": "D1"}
        )
        self.assertEqual(2, accepted["rowCount"])
        over_ten = leap_boundary.replace(b"2026-02-28", b"2026-03-01")
        self.assert_code(
            "date_range_over_10_years",
            lambda: ohlc.parse_ohlc_upload(
                {"fileName": "bars.csv", "contentBase64": encoded(over_ten), "timeframe": "D1"}
            ),
        )

    def test_fuzz_like_malformed_csv_fields_return_domain_errors_not_parser_exceptions(self) -> None:
        cases = (
            b"Date,Open,High,Low,Close\n\x00,100,105,99,104\n",
            b"Date,Open,High,Low,Close\n2026-01-01,1e999999,105,99,104\n",
            b"Date,Open,High,Low,Close\n2026-01-01,@SUM(1),105,99,104\n",
            b"Date,Open,High,Low,Close\n2026-01-01,=1+1,105,99,104\n",
            b"Date,Open,High,Low,Close\n2026-01-01,1_000,1005,999,1004\n",
            b"Date,Open,High,Low,Close\n2026-01-01," + (b"1" * 200_000) + b",105,99,104\n",
        )
        for index, data in enumerate(cases):
            with self.subTest(index=index):
                with self.assertRaises(ohlc.OhlcImportError):
                    ohlc.parse_ohlc_upload(
                        {"fileName": "bars.csv", "contentBase64": encoded(data), "timeframe": "D1"}
                    )


if __name__ == "__main__":
    unittest.main()
