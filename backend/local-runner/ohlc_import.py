"""Bounded, dependency-free OHLC CSV/XLSX importer for the local HQ bridge.

The parser is deliberately data-only: it never persists the uploaded file,
opens a spreadsheet application, calls MetaTrader, or performs network I/O.
"""

from __future__ import annotations

import base64
import binascii
import csv
import hashlib
import io
import math
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable
from xml.etree import ElementTree as ET


MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 256
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 32 * 1024 * 1024
MAX_ARCHIVE_COMPRESSION_RATIO = 200
MIN_RATIO_CHECK_BYTES = 1024 * 1024
MAX_ROWS = 50_000
MAX_COLUMNS = 32
MAX_YEARS = 10
MAX_CELL_TEXT_CHARS = 4_000
MAX_DATETIME_TEXT_CHARS = 128
ALLOWED_TIMEFRAMES = frozenset({"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"})

_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_DECIMAL_NUMBER = re.compile(r"^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$")


class OhlcImportError(ValueError):
    def __init__(self, code: str, message: str, status: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


@dataclass(frozen=True)
class _Table:
    rows: list[list[object]]
    sheet_name: str
    date_1904: bool = False


def _safe_file_name(value: object) -> str:
    name = Path(str(value or "").replace("\\", "/")).name
    name = re.sub(r"[^A-Za-z0-9._ -]+", "_", name).strip(" .")
    return name[:120] or "ohlc-data"


def _decode_payload(content_base64: object) -> bytes:
    if not isinstance(content_base64, str) or not content_base64:
        raise OhlcImportError("missing_file_data", "ไม่พบข้อมูลไฟล์ OHLC")
    if len(content_base64) > ((MAX_FILE_BYTES + 2) // 3 * 4) + 8:
        raise OhlcImportError("file_too_large", "ไฟล์ OHLC มีขนาดเกิน 5 MB", 413)
    try:
        data = base64.b64decode(content_base64, validate=True)
    except (binascii.Error, ValueError) as error:
        raise OhlcImportError("invalid_base64", "ข้อมูลไฟล์ OHLC ไม่ใช่ Base64 ที่ถูกต้อง") from error
    if not data:
        raise OhlcImportError("empty_file", "ไฟล์ OHLC ว่างเปล่า")
    if len(data) > MAX_FILE_BYTES:
        raise OhlcImportError("file_too_large", "ไฟล์ OHLC มีขนาดเกิน 5 MB", 413)
    return data


def _normalized_header(value: object) -> str:
    raw = str(value or "").strip().lower()
    thai = {
        "วันที่": "date",
        "วันเวลา": "datetime",
        "เวลา": "time",
        "เปิด": "open",
        "สูง": "high",
        "ต่ำ": "low",
        "ปิด": "close",
    }
    if raw in thai:
        return thai[raw]
    return re.sub(r"[^a-z0-9]+", "", raw)


_HEADER_ALIASES = {
    "datetime": {"datetime", "dateandtime", "timestamp", "opentime", "bartime"},
    "date": {"date", "day", "tradingdate"},
    "time": {"time", "timeofday"},
    "open": {"open", "o", "openprice"},
    "high": {"high", "h", "highprice"},
    "low": {"low", "l", "lowprice"},
    "close": {"close", "c", "closeprice", "last"},
}


def _header_map(header: Iterable[object]) -> dict[str, int]:
    result: dict[str, int] = {}
    for index, value in enumerate(list(header)[:MAX_COLUMNS]):
        normalized = _normalized_header(value)
        for canonical, aliases in _HEADER_ALIASES.items():
            if normalized in aliases and canonical in result:
                raise OhlcImportError(
                    "duplicate_ohlc_column",
                    f"พบคอลัมน์ {canonical} ซ้ำมากกว่าหนึ่งคอลัมน์",
                )
            if normalized in aliases:
                result[canonical] = index
                break
    if "datetime" not in result and "date" not in result:
        raise OhlcImportError("missing_datetime_column", "ไฟล์ต้องมีคอลัมน์ Date, DateTime หรือ Timestamp")
    missing = [field for field in ("open", "high", "low", "close") if field not in result]
    if missing:
        raise OhlcImportError("missing_ohlc_columns", "ไฟล์ต้องมีคอลัมน์ Open, High, Low และ Close ให้ครบ")
    return result


def _csv_table(data: bytes) -> _Table:
    try:
        text = data.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as error:
        raise OhlcImportError("csv_not_utf8", "ไฟล์ CSV ต้องเป็น UTF-8") from error
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(io.StringIO(text, newline=""), dialect)
    rows: list[list[object]] = []
    try:
        for row in reader:
            if not any(str(value).strip() for value in row):
                continue
            if len(row) > MAX_COLUMNS:
                raise OhlcImportError("too_many_columns", f"ไฟล์มีคอลัมน์เกิน {MAX_COLUMNS} คอลัมน์")
            rows.append(list(row))
            if len(rows) > MAX_ROWS + 1:
                raise OhlcImportError("too_many_rows", f"ไฟล์มีข้อมูลเกิน {MAX_ROWS:,} แถว", 413)
    except csv.Error as error:
        raise OhlcImportError("invalid_csv", "โครงสร้าง CSV ไม่ถูกต้อง") from error
    return _Table(rows=rows, sheet_name="CSV")


def _zip_member_bytes(archive: zipfile.ZipFile, name: str, *, maximum: int = 8 * 1024 * 1024) -> bytes:
    try:
        info = archive.getinfo(name)
    except KeyError as error:
        raise OhlcImportError("xlsx_structure_missing", f"ไฟล์ XLSX ไม่มีส่วนประกอบ {name}") from error
    if info.file_size > maximum:
        raise OhlcImportError("xlsx_part_too_large", "ส่วนประกอบภายใน XLSX มีขนาดเกินกำหนด", 413)
    try:
        with archive.open(info, "r") as handle:
            data = handle.read(maximum + 1)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError, EOFError) as error:
        raise OhlcImportError("invalid_xlsx", "ข้อมูลบีบอัดภายใน XLSX เสียหาย") from error
    if len(data) > maximum:
        raise OhlcImportError("xlsx_part_too_large", "ส่วนประกอบภายใน XLSX มีขนาดเกินกำหนด", 413)
    if len(data) != info.file_size:
        raise OhlcImportError("invalid_xlsx", "ขนาดส่วนประกอบภายใน XLSX ไม่ตรงกับสารบัญ")
    return data


def _xlsx_archive(data: bytes) -> zipfile.ZipFile:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data), "r")
    except (zipfile.BadZipFile, OSError) as error:
        raise OhlcImportError("invalid_xlsx", "ไฟล์ XLSX เปิดไม่ได้หรือโครงสร้างเสียหาย") from error
    infos = archive.infolist()
    if not infos or len(infos) > MAX_ARCHIVE_ENTRIES:
        archive.close()
        raise OhlcImportError("xlsx_entry_limit", "จำนวนไฟล์ย่อยใน XLSX เกินกำหนด", 413)
    total = 0
    member_names: set[str] = set()
    for info in infos:
        raw_name = info.filename
        if not raw_name or "\x00" in raw_name or "\\" in raw_name:
            archive.close()
            raise OhlcImportError("unsafe_xlsx_archive", "XLSX มีชื่อไฟล์ย่อยที่ไม่อนุญาต")
        path = PurePosixPath(raw_name)
        normalized_name = path.as_posix()
        folded_name = normalized_name.casefold()
        unix_mode = (info.external_attr >> 16) & 0xF000
        if (
            path.is_absolute()
            or ".." in path.parts
            or any(":" in part for part in path.parts)
            or info.flag_bits & 0x1
            or unix_mode == 0xA000
            or info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
            or folded_name in member_names
        ):
            archive.close()
            raise OhlcImportError("unsafe_xlsx_archive", "XLSX มี path หรือการเข้ารหัสที่ไม่อนุญาต")
        member_names.add(folded_name)
        if (
            info.file_size >= MIN_RATIO_CHECK_BYTES
            and info.file_size > max(1, info.compress_size) * MAX_ARCHIVE_COMPRESSION_RATIO
        ):
            archive.close()
            raise OhlcImportError("xlsx_compression_ratio", "XLSX มีอัตราการขยายข้อมูลผิดปกติ", 413)
        total += max(0, int(info.file_size))
        if total > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
            archive.close()
            raise OhlcImportError("xlsx_expansion_limit", "XLSX ขยายข้อมูลเกิน 32 MB", 413)
    return archive


def _xml_root(data: bytes) -> ET.Element:
    lowered = data.lower()
    if b"\x00" in data:
        raise OhlcImportError("unsafe_xlsx_xml", "XML ภายใน XLSX ต้องใช้ UTF-8 และห้ามมี Null Byte")
    if b"<!doctype" in lowered or b"<!entity" in lowered:
        raise OhlcImportError("unsafe_xlsx_xml", "XML ภายใน XLSX มี DTD หรือ Entity ที่ไม่อนุญาต")
    try:
        return ET.fromstring(data)
    except ET.ParseError as error:
        raise OhlcImportError("invalid_xlsx_xml", "XML ภายใน XLSX เสียหาย") from error


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = _xml_root(_zip_member_bytes(archive, "xl/sharedStrings.xml", maximum=12 * 1024 * 1024))
    values: list[str] = []
    for item in root.findall(f"{{{_MAIN_NS}}}si"):
        text = "".join(node.text or "" for node in item.iter(f"{{{_MAIN_NS}}}t"))
        if len(text) > MAX_CELL_TEXT_CHARS:
            raise OhlcImportError("xlsx_cell_text_limit", "ข้อความในเซลล์ XLSX ยาวเกินกำหนด", 413)
        values.append(text)
        if len(values) > MAX_ROWS * 4:
            raise OhlcImportError("xlsx_shared_string_limit", "Shared Strings ใน XLSX มากเกินกำหนด", 413)
    return values


def _xlsx_sheet_target(archive: zipfile.ZipFile) -> tuple[str, str, bool]:
    workbook = _xml_root(_zip_member_bytes(archive, "xl/workbook.xml"))
    workbook_pr = workbook.find(f"{{{_MAIN_NS}}}workbookPr")
    date_1904 = bool(workbook_pr is not None and workbook_pr.attrib.get("date1904") in {"1", "true", "True"})
    selected = None
    sheets = workbook.find(f"{{{_MAIN_NS}}}sheets")
    for sheet in list(sheets) if sheets is not None else []:
        if sheet.attrib.get("state", "visible") == "visible":
            selected = sheet
            break
    if selected is None:
        raise OhlcImportError("xlsx_no_visible_sheet", "XLSX ไม่มี Worksheet ที่มองเห็นได้")
    relationship_id = selected.attrib.get(f"{{{_REL_NS}}}id")
    if not relationship_id:
        raise OhlcImportError("xlsx_sheet_relationship_missing", "XLSX ไม่มีความสัมพันธ์ของ Worksheet")
    relationships = _xml_root(_zip_member_bytes(archive, "xl/_rels/workbook.xml.rels"))
    target = ""
    matching_relationships = 0
    for relation in relationships.findall(f"{{{_PKG_REL_NS}}}Relationship"):
        if relation.attrib.get("Id") == relationship_id:
            matching_relationships += 1
            if relation.attrib.get("TargetMode", "Internal") != "Internal":
                raise OhlcImportError("unsafe_xlsx_target", "Worksheet target ภายนอกไม่ได้รับอนุญาต")
            relation_type = relation.attrib.get("Type", "")
            if relation_type and not relation_type.endswith("/worksheet"):
                raise OhlcImportError("unsafe_xlsx_target", "ความสัมพันธ์ Worksheet มีชนิดไม่ถูกต้อง")
            target = relation.attrib.get("Target", "")
    if matching_relationships != 1 or not target:
        raise OhlcImportError("xlsx_sheet_relationship_missing", "XLSX ไม่มีความสัมพันธ์ Worksheet ที่ชัดเจน")
    normalized_target = str(PurePosixPath("xl") / PurePosixPath(target)).replace("\\", "/")
    parts: list[str] = []
    for part in normalized_target.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                raise OhlcImportError("unsafe_xlsx_target", "Worksheet target อยู่นอกโครงสร้าง XLSX")
            parts.pop()
        else:
            parts.append(part)
    sheet_path = "/".join(parts)
    if not sheet_path.startswith("xl/worksheets/"):
        raise OhlcImportError("unsafe_xlsx_target", "Worksheet target ไม่อยู่ในโฟลเดอร์ที่อนุญาต")
    return sheet_path, str(selected.attrib.get("name") or "Sheet1")[:80], date_1904


def _column_index(cell_reference: str) -> int:
    match = re.fullmatch(r"([A-Z]{1,3})[1-9][0-9]*", cell_reference.upper())
    if not match:
        return -1
    index = 0
    for character in match.group(1):
        index = index * 26 + (ord(character) - 64)
    return index - 1


def _cell_value(cell: ET.Element, shared: list[str]) -> object:
    if any(str(node.tag).rsplit("}", 1)[-1] == "f" for node in cell.iter() if node is not cell):
        raise OhlcImportError("xlsx_formula_rejected", "ไม่อนุญาต Formula ในข้อมูล OHLC")
    kind = cell.attrib.get("t", "")
    if kind == "inlineStr":
        text = "".join(node.text or "" for node in cell.iter(f"{{{_MAIN_NS}}}t"))
        if len(text) > MAX_CELL_TEXT_CHARS:
            raise OhlcImportError("xlsx_cell_text_limit", "ข้อความในเซลล์ XLSX ยาวเกินกำหนด", 413)
        return text
    value_node = cell.find(f"{{{_MAIN_NS}}}v")
    value = value_node.text if value_node is not None else ""
    if kind == "s":
        try:
            if re.fullmatch(r"0|[1-9][0-9]*", str(value)) is None:
                raise ValueError
            index = int(value)
            if index < 0 or index >= len(shared):
                raise ValueError
            return shared[index]
        except (TypeError, ValueError, IndexError):
            raise OhlcImportError("xlsx_shared_string_invalid", "XLSX อ้าง Shared String ที่ไม่ถูกต้อง")
    if kind == "e":
        raise OhlcImportError("xlsx_error_cell_rejected", "ไม่อนุญาต Error Cell ในข้อมูล OHLC")
    if kind in {"str", "d"}:
        if len(str(value)) > MAX_CELL_TEXT_CHARS:
            raise OhlcImportError("xlsx_cell_text_limit", "ข้อความในเซลล์ XLSX ยาวเกินกำหนด", 413)
        return value
    if kind == "b":
        if value not in {"0", "1"}:
            raise OhlcImportError("xlsx_boolean_invalid", "ค่า Boolean ภายใน XLSX ไม่ถูกต้อง")
        return value == "1"
    if kind not in {"", "n"}:
        raise OhlcImportError("xlsx_cell_type_rejected", "ชนิดเซลล์ XLSX ไม่ได้รับอนุญาต")
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def _xlsx_table(data: bytes) -> _Table:
    archive = _xlsx_archive(data)
    try:
        shared = _shared_strings(archive)
        sheet_path, sheet_name, date_1904 = _xlsx_sheet_target(archive)
        root = _xml_root(_zip_member_bytes(archive, sheet_path, maximum=24 * 1024 * 1024))
    finally:
        archive.close()
    rows: list[list[object]] = []
    sheet_data = root.find(f"{{{_MAIN_NS}}}sheetData")
    for row_node in list(sheet_data) if sheet_data is not None else []:
        row: list[object] = []
        used_columns: set[int] = set()
        for cell in row_node.findall(f"{{{_MAIN_NS}}}c"):
            index = _column_index(cell.attrib.get("r", ""))
            if index < 0:
                raise OhlcImportError("xlsx_cell_reference_invalid", "XLSX มี Cell Reference ที่ไม่ถูกต้อง")
            if index >= MAX_COLUMNS:
                raise OhlcImportError("too_many_columns", f"ไฟล์มีคอลัมน์เกิน {MAX_COLUMNS} คอลัมน์")
            if index in used_columns:
                raise OhlcImportError("xlsx_duplicate_cell", "XLSX มี Cell Reference ซ้ำภายในแถวเดียวกัน")
            used_columns.add(index)
            if len(row) <= index:
                row.extend([""] * (index + 1 - len(row)))
            row[index] = _cell_value(cell, shared)
        if any(str(value).strip() for value in row):
            rows.append(row)
        if len(rows) > MAX_ROWS + 1:
            raise OhlcImportError("too_many_rows", f"ไฟล์มีข้อมูลเกิน {MAX_ROWS:,} แถว", 413)
    return _Table(rows=rows, sheet_name=sheet_name, date_1904=date_1904)


def _excel_datetime(value: float, date_1904: bool) -> datetime:
    origin = datetime(1904, 1, 1) if date_1904 else datetime(1899, 12, 30)
    adjusted = value
    # Excel's Windows date system contains the fictional 1900-02-29.  Preserve
    # Excel's serial interpretation on both sides of that discontinuity.
    if not date_1904 and 0 < adjusted < 60:
        adjusted += 1
    try:
        return origin + timedelta(days=adjusted)
    except (OverflowError, ValueError) as error:
        raise OhlcImportError("invalid_datetime", "Excel Date/Time อยู่นอกช่วงที่รองรับ") from error


def _parse_datetime(value: object, *, date_1904: bool, time_value: object = None) -> datetime:
    if isinstance(value, bool):
        raise OhlcImportError("invalid_datetime", "พบ Date/Time ที่ไม่ถูกต้อง")
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        parsed = _excel_datetime(float(value), date_1904)
    else:
        text = str(value or "").strip()
        if not text:
            raise OhlcImportError("invalid_datetime", "พบ Date/Time ว่างเปล่า")
        if len(text) > MAX_DATETIME_TEXT_CHARS:
            raise OhlcImportError("invalid_datetime", "ข้อความ Date/Time ยาวเกินกำหนด")
        normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
        parsed = None
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            for pattern in (
                "%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y.%m.%d",
                "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
            ):
                try:
                    parsed = datetime.strptime(text, pattern)
                    break
                except ValueError:
                    continue
        if parsed is None:
            raise OhlcImportError("invalid_datetime", f"อ่าน Date/Time ไม่ได้: {text[:60]}")
    if parsed.tzinfo is not None and parsed.utcoffset() is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    if time_value not in (None, ""):
        if parsed.hour != 0 or parsed.minute != 0 or parsed.second != 0 or parsed.microsecond != 0:
            raise OhlcImportError("conflicting_time_columns", "คอลัมน์ Date มีเวลาอยู่แล้วแต่ยังมีคอลัมน์ Time ซ้ำ")
        if isinstance(time_value, bool):
            raise OhlcImportError("invalid_time", "พบเวลาที่ไม่ถูกต้อง")
        if isinstance(time_value, (int, float)) and math.isfinite(float(time_value)):
            fraction = float(time_value)
            if fraction < 0 or fraction >= 1:
                raise OhlcImportError("invalid_time", "ค่าเวลาแบบ Excel ต้องอยู่ระหว่าง 0 ถึงน้อยกว่า 1")
            seconds = int(fraction * 86400)
            parsed = parsed.replace(hour=seconds // 3600, minute=(seconds % 3600) // 60, second=seconds % 60)
        else:
            time_text = str(time_value).strip()
            if len(time_text) > 32:
                raise OhlcImportError("invalid_time", "ข้อความ Time ยาวเกินกำหนด")
            match = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", time_text)
            if not match:
                raise OhlcImportError("invalid_time", f"อ่านเวลาไม่ได้: {str(time_value)[:40]}")
            hour, minute, second = int(match[1]), int(match[2]), int(match[3] or 0)
            if hour > 23 or minute > 59 or second > 59:
                raise OhlcImportError("invalid_time", "เวลาอยู่นอกช่วง 00:00:00 ถึง 23:59:59")
            parsed = parsed.replace(hour=hour, minute=minute, second=second)
    if parsed.microsecond != 0:
        raise OhlcImportError("subsecond_timestamp_rejected", "ข้อมูล OHLC รองรับ Date/Time ละเอียดถึงระดับวินาที")
    return parsed.replace(tzinfo=None)


def _numeric(value: object, field: str, row_number: int) -> float:
    if isinstance(value, bool):
        raise OhlcImportError("invalid_price", f"แถว {row_number}: {field} ต้องไม่ใช่ Boolean")
    if isinstance(value, str):
        text = value.strip()
        if len(text) > 128:
            raise OhlcImportError("invalid_price", f"แถว {row_number}: {field} ยาวเกินกำหนด")
        if _DECIMAL_NUMBER.fullmatch(text) is None:
            raise OhlcImportError("invalid_price", f"แถว {row_number}: {field} ไม่ใช่เลขฐานสิบที่ถูกต้อง")
    try:
        number = float(str(value).strip()) if not isinstance(value, (int, float)) else float(value)
    except (TypeError, ValueError) as error:
        raise OhlcImportError("invalid_price", f"แถว {row_number}: {field} ไม่ใช่ตัวเลข") from error
    if not math.isfinite(number) or number <= 0:
        raise OhlcImportError("invalid_price", f"แถว {row_number}: {field} ต้องเป็นตัวเลขบวก")
    return number


def _value(row: list[object], index: int) -> object:
    return row[index] if 0 <= index < len(row) else ""


def _ten_year_limit(start: datetime) -> datetime:
    if start.year > datetime.max.year - MAX_YEARS:
        return datetime.max
    try:
        return start.replace(year=start.year + MAX_YEARS)
    except ValueError:
        return start.replace(month=2, day=28, year=start.year + MAX_YEARS)


def _normalize_rows(table: _Table) -> list[dict]:
    if len(table.rows) < 2:
        raise OhlcImportError("no_ohlc_rows", "ไฟล์ไม่มีแถวข้อมูล OHLC")
    columns = _header_map(table.rows[0])
    bars: list[tuple[datetime, dict]] = []
    seen: set[datetime] = set()
    for row_number, row in enumerate(table.rows[1:], start=2):
        date_index = columns.get("datetime", columns.get("date", -1))
        timestamp = _parse_datetime(
            _value(row, date_index),
            date_1904=table.date_1904,
            time_value=_value(row, columns["time"]) if "time" in columns else None,
        )
        if timestamp in seen:
            raise OhlcImportError("duplicate_timestamp", f"แถว {row_number}: Date/Time ซ้ำกับแถวก่อนหน้า")
        open_price = _numeric(_value(row, columns["open"]), "Open", row_number)
        high_price = _numeric(_value(row, columns["high"]), "High", row_number)
        low_price = _numeric(_value(row, columns["low"]), "Low", row_number)
        close_price = _numeric(_value(row, columns["close"]), "Close", row_number)
        if low_price > min(open_price, close_price) or high_price < max(open_price, close_price) or low_price > high_price:
            raise OhlcImportError("invalid_ohlc_range", f"แถว {row_number}: High/Low ไม่ครอบ Open และ Close")
        seen.add(timestamp)
        bars.append((timestamp, {
            "time": timestamp.isoformat(timespec="seconds"),
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
        }))
    if not bars:
        raise OhlcImportError("no_ohlc_rows", "ไฟล์ไม่มีแถวข้อมูล OHLC")
    bars.sort(key=lambda item: item[0])
    if bars[-1][0] > _ten_year_limit(bars[0][0]):
        raise OhlcImportError("date_range_over_10_years", "ช่วงข้อมูล OHLC ต้องไม่เกิน 10 ปี")
    return [item[1] for item in bars]


def parse_ohlc_upload(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise OhlcImportError("invalid_request", "คำขอนำเข้า OHLC ต้องเป็น JSON Object")
    allowed = {"fileName", "contentBase64", "timeframe"}
    if set(payload) - allowed:
        raise OhlcImportError("unexpected_fields", "คำขอนำเข้า OHLC มีฟิลด์ที่ไม่อนุญาต")
    file_name = _safe_file_name(payload.get("fileName"))
    extension = Path(file_name).suffix.lower()
    if extension not in {".csv", ".xlsx"}:
        raise OhlcImportError("unsupported_file_type", "รองรับเฉพาะไฟล์ .csv และ .xlsx")
    timeframe = str(payload.get("timeframe") or "").strip().upper()
    if timeframe not in ALLOWED_TIMEFRAMES:
        raise OhlcImportError("invalid_timeframe", "Timeframe ไม่อยู่ในรายการที่ระบบรองรับ")
    data = _decode_payload(payload.get("contentBase64"))
    table = _csv_table(data) if extension == ".csv" else _xlsx_table(data)
    bars = _normalize_rows(table)
    digest = hashlib.sha256(data).hexdigest()
    return {
        "ok": True,
        "kind": "ohlc_import_ready",
        "schemaVersion": "ohlc-import-v1",
        "file": {
            "name": file_name,
            "extension": extension,
            "byteSize": len(data),
            "sha256": digest,
            "persisted": False,
        },
        "sheetName": table.sheet_name,
        "timeframe": timeframe,
        "rowCount": len(bars),
        "range": {"start": bars[0]["time"], "end": bars[-1]["time"], "maximumYears": MAX_YEARS},
        "bars": bars,
        "privacy": {
            "localOnly": True,
            "networkUpload": False,
            "filePersisted": False,
            "metaTraderActions": False,
        },
    }
