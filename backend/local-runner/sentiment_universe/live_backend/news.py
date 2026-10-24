"""Local, read-only Forex Factory calendar snapshots. No AI or trading calls.

The public weekly export is the user's selected source for this local preview.
It is not a licence to redistribute the calendar commercially. JSON provides
offset-aware times, ICS supplies occurrence UIDs/time-zone evidence, and XML
supplies explicit All Day/Tentative markers where the publisher provides them.
Only the current-week export is published at the verified URLs. Cached earlier
weeks are retained; an uncovered Thai day is never called a verified quiet day.
"""
from __future__ import annotations

import copy
import base64
import hashlib
import json
import math
import os
import re
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BANGKOK = ZoneInfo('Asia/Bangkok')
NEW_YORK = ZoneInfo('America/New_York')
SOURCE = 'Forex Factory · Weekly Export'
SOURCE_URL = 'https://www.forexfactory.com/calendar'
URLS = {kind: f'https://nfs.faireconomy.media/ff_calendar_thisweek.{kind}' for kind in ('json', 'ics', 'xml')}
MAX_BYTES = 2_000_000
CACHE_VERSION = 2
RIGHTS_NOTE = 'ใช้ export ในเครื่องนี้; การเผยแพร่หรือแจกจ่ายข้อมูลต่อยังต้องตรวจสิทธิ์กับ Forex Factory'
# These are FF's ICS labels, NOT ISO country codes (CH=China, SZ=Switzerland).
COUNTRY_CURRENCY = {'US': 'USD', 'EU': 'EUR', 'EZ': 'EUR', 'GE': 'EUR', 'FR': 'EUR', 'BE': 'EUR', 'SP': 'EUR', 'IT': 'EUR', 'GB': 'GBP', 'UK': 'GBP', 'JP': 'JPY', 'JN': 'JPY', 'CA': 'CAD', 'AU': 'AUD', 'NZ': 'NZD', 'SZ': 'CHF', 'CH': 'CNY', 'CN': 'CNY', 'WW': 'All'}
ICS_TITLE_PREFIX = {'GE': 'German ', 'FR': 'French ', 'BE': 'Belgian ', 'SP': 'Spanish ', 'IT': 'Italian '}
IMPACTS = {'high': 'สูง', 'medium': 'ปานกลาง', 'low': 'ต่ำ', 'holiday': 'วันหยุด / เหตุการณ์ปฏิทิน', 'none': 'ไม่จัดระดับ', 'non-economic': 'ไม่ใช่ตัวเลขเศรษฐกิจ'}


class NewsSourceError(RuntimeError):
    def __init__(self, code, *, retry_after=None):
        super().__init__(code)
        self.retry_after = retry_after


def failure_delay(error: Exception, current: datetime, failures: int) -> float:
    delay = min(60 * 2 ** (failures - 1), 3600)
    if str(error) == 'http_429':
        delay = max(delay, 1800)
    retry_after = getattr(error, 'retry_after', None)
    if retry_after is not None:
        try:
            seconds = float(str(retry_after))
        except ValueError:
            try:
                until = parsedate_to_datetime(str(retry_after))
                seconds = (until.astimezone(timezone.utc) - current).total_seconds() if until.tzinfo else 0
            except (ValueError, TypeError, OverflowError):
                seconds = 0
        if math.isfinite(seconds):
            delay = max(delay, seconds)
    return delay


def utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def reference_time(value: datetime | None = None) -> datetime:
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError('now must include a timezone')
    return value.astimezone(timezone.utc)


def parse_time(value: object) -> datetime | None:
    try:
        dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except (TypeError, ValueError):
        return None


def text(value: object, limit: int = 1000) -> str:
    return re.sub(r'\s+', ' ', str(value or '')).strip()[:limit]


def raw_value(value: object) -> str | None:
    # Preserve zero; missing fields must never become numeric zero.
    if value is None:
        return None
    result = str(value).strip()
    return result if result else None


def numeric_value(value: object) -> float | None:
    raw = raw_value(value)
    if raw is None:
        return None
    match = re.fullmatch(r'([+-]?(?:\d[\d,]*(?:\.\d*)?|\.\d+))\s*([KMBT])?\s*(%)?', raw, re.I)
    if not match:
        return None  # Auctions such as 3.58|1.2 are not a single observation.
    number = float(match[1].replace(',', '')) * {'': 1, 'K': 1e3, 'M': 1e6, 'B': 1e9, 'T': 1e12}[(match[2] or '').upper()]
    return number if math.isfinite(number) else None


TRANSLATIONS = (
    ('Core CPI', 'Core CPI เงินเฟ้อพื้นฐาน'), ('Trimmed Mean CPI', 'เงินเฟ้อ CPI แบบตัดค่าผิดปกติ'),
    ('Consumer Price Index', 'ดัชนีราคาผู้บริโภค'), ('CPI', 'CPI เงินเฟ้อผู้บริโภค'),
    ('Core PCE Price Index', 'ดัชนีราคา Core PCE'), ('PCE Price Index', 'ดัชนีราคา PCE'),
    ('Non-Farm Employment Change', 'การเปลี่ยนแปลงการจ้างงานนอกภาคเกษตร'),
    ('Unemployment Rate', 'อัตราการว่างงาน'), ('Unemployment Claims', 'จำนวนผู้ขอรับสวัสดิการว่างงาน'),
    ('Employment Change', 'การเปลี่ยนแปลงการจ้างงาน'), ('Average Hourly Earnings', 'รายได้เฉลี่ยต่อชั่วโมง'),
    ('Core Retail Sales', 'ยอดค้าปลีกพื้นฐาน'), ('Retail Sales', 'ยอดค้าปลีก'),
    ('Manufacturing PMI', 'PMI ภาคการผลิต'), ('Services PMI', 'PMI ภาคบริการ'),
    ('Consumer Confidence', 'ความเชื่อมั่นผู้บริโภค'), ('Consumer Sentiment', 'ความเชื่อมั่นผู้บริโภค'),
    ('Business Confidence', 'ความเชื่อมั่นภาคธุรกิจ'), ('Business Climate', 'ดัชนีบรรยากาศธุรกิจ'),
    ('Trade Balance', 'ดุลการค้า'), ('Current Account', 'ดุลบัญชีเดินสะพัด'),
    ('Gross Domestic Product', 'ผลิตภัณฑ์มวลรวมในประเทศ'), ('GDP', 'GDP ผลิตภัณฑ์มวลรวมในประเทศ'),
    ('Crude Oil Inventories', 'ปริมาณน้ำมันดิบคงคลัง'), ('Natural Gas Storage', 'ปริมาณก๊าซธรรมชาติคงคลัง'),
    ('Industrial Production', 'ผลผลิตภาคอุตสาหกรรม'), ('Building Permits', 'ใบอนุญาตก่อสร้าง'),
    ('Housing Starts', 'การเริ่มก่อสร้างที่อยู่อาศัย'), ('New Home Sales', 'ยอดขายบ้านใหม่'),
    ('Existing Home Sales', 'ยอดขายบ้านมือสอง'), ('Official Cash Rate', 'อัตราดอกเบี้ยนโยบาย'),
    ('Interest Rate Decision', 'มติอัตราดอกเบี้ยนโยบาย'), ('Rate Statement', 'แถลงการณ์นโยบายดอกเบี้ย'),
    ('Press Conference', 'การแถลงข่าว'), ('Bank Holiday', 'วันหยุดธนาคาร'),
    ('Daylight Saving Time Shift', 'การเปลี่ยนเวลาออมแสง'), ('IMF Meetings', 'การประชุม IMF'),
    ('Speaks', 'กล่าวถ้อยแถลง'), ('m/m', 'เทียบเดือนก่อน'), ('q/q', 'เทียบไตรมาสก่อน'), ('y/y', 'เทียบปีก่อน'),
)


def describe_event(title: str) -> dict:
    lower = title.lower()
    translated = title
    # Use a single longest measurement phrase, then add period translation.
    changed = False
    for original, thai in TRANSLATIONS:
        if original in {'m/m', 'q/q', 'y/y'}:
            continue
        if original.lower() in lower:
            translated = re.sub(re.escape(original), lambda _: thai, translated, count=1, flags=re.I)
            changed = True
            break
    for original, thai in TRANSLATIONS[-3:]:
        translated = translated.replace(original, thai)
    metric, summary = 'unknown', 'อ่านชื่อ หน่วย ช่วงเวลาที่รายงาน และแหล่งต้นทาง; ข่าวเดียวไม่ยืนยันทิศทางราคา'
    if re.search(r'\b(core\s+)?cpi\b|consumer price', lower):
        metric, summary = 'inflation', 'ติดตามการเปลี่ยนแปลงราคาผู้บริโภค; ผลต่อค่าเงินขึ้นกับการปรับคาดการณ์ดอกเบี้ยและข่าวอื่น'
    elif 'unemployment rate' in lower:
        metric, summary = 'unemployment', 'สัดส่วนผู้ว่างงานในกำลังแรงงาน; อ่านร่วมกับค่าจ้างและการมีส่วนร่วมแรงงาน'
    elif 'employment change' in lower or 'payroll' in lower:
        metric, summary = 'employment', 'การเปลี่ยนแปลงการจ้างงาน; ควรแยกจำนวนที่เพิ่มขึ้นออกจากอัตราการว่างงาน'
    elif any(part in lower for part in ('consumer confidence', 'consumer sentiment', 'business confidence')):
        metric, summary = 'confidence', 'แบบสำรวจความเชื่อมั่น; หน่วยและความหมายแตกต่างกันตามผู้จัดทำ'
    elif any(part in lower for part in ('pmi', 'gdp', 'gross domestic product', 'retail sales')):
        metric, summary = 'activity', 'ข้อมูลกิจกรรมเศรษฐกิจ; เปรียบเทียบผลจริงกับคาดการณ์เมื่อมีข้อมูลครบ'
    elif 'speaks' in lower or 'speech' in lower:
        metric, summary = 'speech', 'ถ้อยแถลงไม่มีผลตัวเลขเทียบคาดโดยตรง; ต้องอ่านเนื้อหาจริงก่อนตีความ'
    return {'title': translated, 'titleLanguage': 'th_partial' if changed else 'original', 'metric': metric, 'summary': summary, 'summaryOrigin': 'local_dictionary'}


def fetch_public_export(url: str) -> dict:
    if url not in URLS.values():
        raise NewsSourceError('source_not_allowlisted')
    request = urllib.request.Request(url, headers={'User-Agent': 'Metafxclub-Local-Calendar/1.0', 'Accept': 'application/json,text/calendar,application/xml,text/xml'})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            if not str(response.geturl()).startswith('https://nfs.faireconomy.media/'):
                raise NewsSourceError('unexpected_source_redirect')
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise NewsSourceError('source_body_too_large')
            return {'body': body, 'status': response.status, 'lastModified': response.headers.get('Last-Modified'), 'etag': response.headers.get('ETag')}
    except urllib.error.HTTPError as exc:
        raise NewsSourceError(f'http_{exc.code}', retry_after=exc.headers.get('Retry-After') if exc.headers else None) from exc
    except (OSError, ValueError) as exc:
        raise NewsSourceError(type(exc).__name__) from exc


def response_body(response: object) -> bytes:
    if isinstance(response, bytes):
        return response
    if isinstance(response, str):
        return response.encode('utf-8')
    if isinstance(response, dict) and isinstance(response.get('body'), bytes):
        return response['body']
    raise NewsSourceError('invalid_fetch_response')


def parse_ics_metadata(body: bytes) -> list[dict]:
    unfolded = re.sub(r'\r?\n[ \t]', '', body.decode('utf-8-sig', errors='replace'))
    events, current = [], None
    for line in unfolded.splitlines():
        if line == 'BEGIN:VEVENT':
            current = {}
        elif line == 'END:VEVENT' and current is not None:
            summary = current.get('SUMMARY', '')
            match = re.match(r'^[^A-Za-z0-9]*([A-Z]{2})\s+(.+)$', summary)
            if match:
                current['currency'] = COUNTRY_CURRENCY.get(match[1], match[1])
                current['title'] = match[2].replace('\\,', ',').replace('\\;', ';')
                prefix = ICS_TITLE_PREFIX.get(match[1], '')
                if prefix and not current['title'].startswith(prefix):
                    current['title'] = prefix + current['title']
            raw = current.get('DTSTART', '')
            parameters = current.get('DTSTART_PARAMS', '')
            current['timeKind'] = 'all_day' if 'VALUE=DATE' in parameters or re.fullmatch(r'\d{8}', raw) else 'timed'
            current['time'] = None
            try:
                if current['timeKind'] == 'all_day':
                    current['sourceDate'] = datetime.strptime(raw[:8], '%Y%m%d').date().isoformat()
                elif raw.endswith('Z'):
                    current['time'] = utc_iso(datetime.strptime(raw, '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc))
                else:
                    tz_match = re.search(r'TZID=([^;]+)', parameters)
                    if tz_match:
                        current['time'] = utc_iso(datetime.strptime(raw, '%Y%m%dT%H%M%S').replace(tzinfo=ZoneInfo(tz_match[1])))
                        current['sourceTimeZone'] = tz_match[1]
            except (ValueError, KeyError):
                current['timeKind'] = 'unknown'
            events.append(current)
            current = None
        elif current is not None and ':' in line:
            key, value = line.split(':', 1)
            name = key.split(';', 1)[0]
            if name in {'UID', 'SUMMARY', 'DTSTART', 'URL', 'DTSTAMP'}:
                current[name] = value
                if name == 'DTSTART':
                    current['DTSTART_PARAMS'] = key
    return events


def parse_xml_metadata(body: bytes) -> list[dict]:
    if b'<!DOCTYPE' in body.upper() or b'<!ENTITY' in body.upper():
        raise NewsSourceError('unsupported_xml_declaration')
    return [{child.tag: child.text or '' for child in event} for event in ET.fromstring(body).findall('event')]


def normalize_exports(json_body: bytes, ics_body: bytes | None = None, xml_body: bytes | None = None) -> tuple[list[dict], dict]:
    rows = json.loads(json_body)
    if not isinstance(rows, list) or len(rows) > 10000:
        raise NewsSourceError('invalid_calendar_payload')
    ics = parse_ics_metadata(ics_body) if ics_body else []
    xml = parse_xml_metadata(xml_body) if xml_body else []
    ics_by_key, xml_by_key = defaultdict(list), defaultdict(list)
    for item in ics:
        ics_by_key[(text(item.get('title')), item.get('currency'))].append(item)
    for item in xml:
        xml_by_key[(text(item.get('title')), item.get('country'))].append(item)
    json_key_counts, key_positions = defaultdict(int), defaultdict(int)
    for row in rows:
        if isinstance(row, dict):
            json_key_counts[(text(row.get('title'), 300), text(row.get('country'), 10))] += 1
    events, missing_time, used_ids, weeks = [], 0, set(), defaultdict(int)
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise NewsSourceError('invalid_calendar_row')
        title, currency = text(row.get('title'), 300), text(row.get('country'), 10)
        if not title or not currency:
            raise NewsSourceError('missing_event_identity')
        dt = parse_time(row.get('date'))
        if dt is None:
            raise NewsSourceError('calendar_timestamp_missing_offset')
        source_day = dt.astimezone(NEW_YORK).date()
        week_start = source_day - timedelta(days=(source_day.weekday() + 1) % 7)
        weeks[week_start.isoformat()] += 1
        key = (title, currency)
        key_position = key_positions[key]
        key_positions[key] += 1
        candidates = ics_by_key.get(key, [])
        exact = [item for item in candidates if item.get('time') == utc_iso(dt)]
        meta = exact[0] if len(exact) == 1 else candidates[key_position] if len(candidates) == json_key_counts[key] else {}
        xm = xml_by_key.get(key, [])
        precision = xm[key_position] if len(xm) == json_key_counts[key] else {}
        kind = meta.get('timeKind', 'unknown')
        if not precision:
            kind = 'unknown'  # Cannot rule out a JSON placeholder for Tentative.
        precision_label = str(precision.get('time', '')).strip().lower()
        if 'tentative' in precision_label:
            kind = 'tentative'
        elif 'all day' in precision_label:
            kind = 'all_day'
        elif kind == 'unknown':
            missing_time += 1
        # Never advertise the JSON placeholder as an exact time for untimed news.
        iso = utc_iso(dt) if kind == 'timed' else None
        thai_day = dt.astimezone(BANGKOK).date().isoformat()
        label = dt.astimezone(BANGKOK).strftime('%H:%M') if iso else {'all_day': 'ตลอดวัน', 'tentative': 'รอยืนยันเวลา', 'unknown': 'เวลาในแหล่งข้อมูลยังไม่ยืนยัน'}.get(kind, 'ไม่ระบุเวลา')
        # A source date-only event has no unique instant; keep its source date.
        if kind in {'all_day', 'tentative'}:
            thai_day = meta.get('sourceDate') or source_day.isoformat()
        uid = text(meta.get('UID'), 150)
        identity = uid or hashlib.sha256(f'{currency}|{title}|{source_day}|{key_position}'.encode()).hexdigest()[:24]
        event_id = f'ff-{identity}'
        if event_id in used_ids:
            # Distinct payload rows are retained even if the source duplicates UID.
            event_id = f'{event_id}-{index}'
        used_ids.add(event_id)
        forecast, previous = raw_value(row.get('forecast')), raw_value(row.get('previous'))
        forecast_number, previous_number = numeric_value(forecast), numeric_value(previous)
        descriptions = describe_event(title)
        recognized = descriptions['metric'] in {'inflation', 'employment', 'unemployment', 'activity', 'confidence'}
        numeric = forecast_number is not None or previous_number is not None
        event_kind = 'numeric' if recognized and forecast_number is not None else 'informational'
        if descriptions['metric'] == 'speech':
            # A translated heading alone does not establish hawkish/dovish content.
            event_kind = 'informational'
        impact = text(row.get('impact')).lower() or 'none'
        source_link = meta.get('URL') or precision.get('url') or SOURCE_URL
        if not str(source_link).startswith('https://www.forexfactory.com/'):
            source_link = SOURCE_URL
        events.append({
            'id': event_id, 'sourceEventId': uid or None, 'idStability': 'source_uid' if uid else 'fallback_snapshot',
            'currency': currency, 'time': iso, 'dayThai': thai_day, 'timeLabel': label, 'timeKind': kind,
            'timePrecision': 'minute' if kind == 'timed' else kind,
            'sourceTime': row.get('date'), 'sourceTimeZone': meta.get('sourceTimeZone') or 'offset_in_payload',
            'sourceDate': source_day.isoformat(), 'originalTitle': title, **descriptions,
            'impact': impact, 'impactLabel': IMPACTS.get(impact, impact), 'kind': event_kind, 'numeric': numeric,
            'forecast': forecast, 'previous': previous, 'actual': None,
            'forecastValue': forecast_number, 'previousValue': previous_number, 'actualValue': None,
            'unit': '%' if '%' in str(forecast or previous or '') else '',
            'actualLabel': 'แหล่ง Weekly Export ไม่ส่งผลจริง', 'actualStatus': 'unsupported', 'supportsActual': False,
            'sourceName': SOURCE, 'sourceUrl': source_link, 'mock': False, 'aiStatus': 'not_run',
            'datePrecisionNote': 'วันที่ต้นทาง; ไม่มีเวลาแน่นอนให้แปลงเป็นวันไทย' if kind in {'all_day', 'tentative'} else None,
            'dayThaiEstimated': kind in {'all_day', 'tentative', 'unknown'},
        })
    if not weeks:
        # An empty export cannot establish which week was actually provided.
        raise NewsSourceError('empty_export_without_coverage')
    first = date.fromisoformat(max(weeks, key=weeks.get))
    start = datetime.combine(first, time.min, NEW_YORK)
    end = datetime.combine(first + timedelta(days=7), time.min, NEW_YORK)
    return events, {'from': utc_iso(start), 'to': utc_iso(end), 'weekStart': first.isoformat(), 'sourceCount': len(rows), 'metadataIcsCount': len(ics), 'metadataXmlCount': len(xml), 'ambiguousTimeCount': missing_time, 'scope': 'all_events_in_provider_weekly_export', 'completeWorldCalendar': False}


def day_bounds(day: date) -> tuple[datetime, datetime]:
    return datetime.combine(day, time.min, BANGKOK).astimezone(timezone.utc), datetime.combine(day + timedelta(days=1), time.min, BANGKOK).astimezone(timezone.utc)


def covers(intervals: list[tuple[datetime, datetime]], start: datetime, end: datetime) -> bool:
    cursor = start
    for left, right in sorted(intervals):
        if right <= cursor:
            continue
        if left > cursor:
            return False
        cursor = max(cursor, right)
        if cursor >= end:
            return True
    return False


class NewsService:
    def __init__(self, cache_dir: str | Path, *, provider: str = 'forexfactory', fetcher=None):
        if provider != 'forexfactory':
            raise ValueError('Only the explicitly selected forexfactory provider is enabled')
        self.cache_dir = Path(cache_dir)
        self.cache_path = self.cache_dir / 'news-calendar-cache.json'
        self.fetcher = fetcher or fetch_public_export
        self._lock = threading.RLock()
        self._refreshing = False
        self._state = {'version': CACHE_VERSION, 'provider': provider, 'weeks': {}, 'lastSuccessAt': None, 'lastAttemptAt': None, 'nextAttemptAt': None, 'successDayThai': None, 'failures': 0, 'error': None, 'migrationPending': False, 'recoveredFromSavedExport': False}
        try:
            loaded = json.loads(self.cache_path.read_text(encoding='utf-8'))
            if loaded.get('version') in (1, CACHE_VERSION) and loaded.get('provider') == provider and isinstance(loaded.get('weeks'), dict):
                self._state.update(loaded)
                if loaded.get('version') != CACHE_VERSION:
                    self._state['migrationPending'] = False
                    for week in self._state['weeks'].values():
                        try:
                            raw = week.get('rawExportsB64', {})
                            if not raw.get('json'):
                                raise ValueError('legacy_snapshot_has_no_raw_export')
                            decoded = {kind: base64.b64decode(body, validate=True) if body else None for kind, body in raw.items()}
                            events, coverage = normalize_exports(decoded['json'], decoded.get('ics'), decoded.get('xml'))
                            week.update(events=events, coverage=coverage)
                        except (ValueError, TypeError, KeyError, ET.ParseError, NewsSourceError):
                            # Keep the last good normalized rows when raw bytes are
                            # absent or corrupt; never replace them with an empty cache.
                            self._state['migrationPending'] = True
                            for event in week.get('events', []):
                                event.setdefault('timePrecision', 'minute' if event.get('timeKind') == 'timed' else event.get('timeKind', 'unknown'))
                    self._state['version'] = CACHE_VERSION
                # Also upgrade previously persisted short 429 retries without
                # making a request or changing original freshness timestamps.
                if self._state.get('error') == 'http_429':
                    attempted = parse_time(self._state.get('lastAttemptAt'))
                    due = parse_time(self._state.get('nextAttemptAt'))
                    if attempted:
                        self._state['nextAttemptAt'] = utc_iso(max(due or attempted, attempted + timedelta(minutes=30)))
        except (OSError, ValueError, TypeError, AttributeError):
            pass

    def recover_cached_exports(self, exports: dict[str, bytes], *, fetched_at: datetime, source_fetched_at: dict | None = None, now: datetime | None = None) -> dict:
        """Reparse verified, previously fetched bytes; no network and no new freshness.

        This explicit local recovery hook is never exposed as an HTTP endpoint.
        The caller supplies the original fetch timestamp, not the recovery time.
        """
        original = reference_time(fetched_at)
        events, coverage = normalize_exports(exports['json'], exports.get('ics'), exports.get('xml'))
        with self._lock:
            self._state['weeks'][coverage['weekStart']] = {
                'events': events, 'coverage': coverage, 'fetchedAt': utc_iso(original),
                'rawExportsB64': {kind: base64.b64encode(body).decode('ascii') for kind, body in exports.items() if body is not None},
                'sourceFetchedAt': source_fetched_at or {}, 'recoveredFromSavedExport': True,
            }
            previous_success = parse_time(self._state.get('lastSuccessAt'))
            if previous_success is None or original > previous_success:
                self._state['lastSuccessAt'] = utc_iso(original)
                self._state['successDayThai'] = original.astimezone(BANGKOK).date().isoformat()
            self._state.update(version=CACHE_VERSION, migrationPending=False, recoveredFromSavedExport=True)
            self._save()
        return self.snapshot(now)

    def _save(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        temporary = self.cache_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self._state, ensure_ascii=False), encoding='utf-8')
        os.replace(temporary, self.cache_path)

    def snapshot(self, now: datetime | None = None, *, refresh: bool = False) -> dict:
        if refresh:
            return self.refresh_if_due(now)
        current = reference_time(now)
        thai_day = current.astimezone(BANGKOK).date()
        start, end = day_bounds(thai_day)
        with self._lock:
            state = copy.deepcopy(self._state)
            refreshing = self._refreshing
        weeks = list(state['weeks'].values())
        all_by_id = {}
        intervals = []
        for week in sorted(weeks, key=lambda w: str(w.get('fetchedAt', ''))):
            cov = week.get('coverage', {})
            left, right = parse_time(cov.get('from')), parse_time(cov.get('to'))
            if left and right:
                intervals.append((left, right))
            for event in week.get('events', []):
                if isinstance(event, dict):
                    all_by_id[event['id']] = event
        # Deduplicate before filtering the day: a rescheduled UID in a newer
        # week must also remove its old occurrence from the former day.
        events = sorted((event for event in all_by_id.values() if event.get('dayThai') == thai_day.isoformat()), key=lambda e: (e.get('time') or f"{e['dayThai']}T99", e['currency'], e['id']))
        calendar_events = sorted(all_by_id.values(), key=lambda e: (e.get('dayThai', ''), e.get('time') or '99', e.get('currency', ''), e['id']))
        day_counts = defaultdict(int)
        for event in calendar_events:
            day_counts[event['dayThai']] += 1
        days = set(day_counts)
        for left, right in intervals:
            cursor = left.astimezone(BANGKOK).date()
            final = (right - timedelta(microseconds=1)).astimezone(BANGKOK).date()
            while cursor <= final:
                days.add(cursor.isoformat())
                cursor += timedelta(days=1)
        available_days = [{'dayThai': day, 'count': day_counts[day], 'fullyCovered': covers(intervals, *day_bounds(date.fromisoformat(day)))} for day in sorted(days)]
        fully_covered = covers(intervals, start, end)
        fresh = state.get('successDayThai') == thai_day.isoformat()
        status = 'refreshing' if refreshing and not weeks else 'ready' if fully_covered and fresh and events else 'empty' if fully_covered and fresh else 'partial' if fresh else 'stale' if weeks else 'unavailable'
        if state.get('error') and not weeks:
            status = 'error'
        elif state.get('error'):
            status = 'stale'
        elif state.get('migrationPending') or state.get('recoveredFromSavedExport'):
            status = 'stale'
        latest = max(weeks, key=lambda w: str(w.get('fetchedAt', '')), default={})
        cov = latest.get('coverage', {})
        return {
            'status': status, 'source': SOURCE, 'sourceUrl': SOURCE_URL, 'provider': 'forexfactory',
            'dayThai': thai_day.isoformat(), 'timeZone': 'Asia/Bangkok', 'mock': False,
            'lastSuccessAt': state.get('lastSuccessAt'), 'lastAttemptAt': state.get('lastAttemptAt'), 'nextAttemptAt': state.get('nextAttemptAt'),
            'supportsActual': False, 'snapshotOnly': True, 'updatePolicy': 'daily_thai_midnight_with_failure_and_rollover_backoff',
            'actualNotice': 'Weekly Export มีคาดการณ์และครั้งก่อน แต่ไม่มีผลจริง',
            'aiStatus': 'not_run', 'summaryOrigin': 'local_dictionary',
            'migrationPending': bool(state.get('migrationPending')), 'recoveredFromSavedExport': bool(state.get('recoveredFromSavedExport')),
            'coverage': {**cov, 'dayFrom': utc_iso(start), 'dayTo': utc_iso(end), 'dayCount': len(events), 'normalizedCount': len(latest.get('events', [])), 'thaiDayFullyCovered': fully_covered, 'cachedWeekCount': len(weeks), 'cachedSourceCount': sum(w.get('coverage', {}).get('sourceCount', 0) for w in weeks), 'fromThai': min((a.astimezone(BANGKOK).isoformat() for a, _ in intervals), default=None), 'toThai': max((b.astimezone(BANGKOK).isoformat() for _, b in intervals), default=None), 'intervals': [{'from': utc_iso(a), 'to': utc_iso(b)} for a, b in sorted(intervals)], 'allImpacts': True},
            'warning': 'ยังครอบคลุมวันไทยนี้ไม่ครบจาก export ที่มี; ไม่ตีความว่าไม่มีข่าว' if not fully_covered else 'ข้อมูลกำหนดการหนึ่งรอบต่อวัน; การเลื่อนเวลาภายหลังยังไม่รวมในรอบนี้',
            'error': state.get('error'), 'events': events, 'calendarEvents': calendar_events, 'availableDays': available_days, 'attribution': {'text': 'Calendar: Forex Factory', 'url': SOURCE_URL},
            'rightsNote': RIGHTS_NOTE,
        }

    def refresh_if_due(self, now: datetime | None = None) -> dict:
        current = reference_time(now)
        with self._lock:
            due = parse_time(self._state.get('nextAttemptAt'))
            if self._refreshing or (due and current < due):
                return self.snapshot(current)
            self._refreshing = True
            self._state['lastAttemptAt'] = utc_iso(current)
        try:
            json_response = self.fetcher(URLS['json'])
            json_body = response_body(json_response)
            metadata, metadata_errors = {}, []
            for kind in ('ics', 'xml'):
                try:
                    metadata[kind] = response_body(self.fetcher(URLS[kind]))
                except Exception as exc:
                    if isinstance(exc, NewsSourceError) and str(exc) == 'http_429':
                        raise  # Stop this round immediately; no next export request.
                    metadata[kind] = None
                    metadata_errors.append(f'{kind}:{type(exc).__name__}')
            events, coverage = normalize_exports(json_body, metadata['ics'], metadata['xml'])
            with self._lock:
                coverage['metadataErrors'] = metadata_errors
                raw_exports = {'json': json_body, **metadata}
                self._state['weeks'][coverage['weekStart']] = {'events': events, 'coverage': coverage, 'fetchedAt': utc_iso(current), 'rawExportsB64': {kind: base64.b64encode(body).decode('ascii') for kind, body in raw_exports.items() if body is not None}, 'sourceFetchedAt': {kind: utc_iso(current) for kind, body in raw_exports.items() if body is not None}}
                # Preserve previous/current week over the Sunday Thai/NY boundary.
                self._state['weeks'] = dict(sorted(self._state['weeks'].items())[-3:])
                day = current.astimezone(BANGKOK).date()
                _, day_end = day_bounds(day)
                coverage_end = parse_time(coverage['to'])
                retry_rollover = coverage_end is not None and coverage_end < day_end
                next_attempt = current + timedelta(minutes=30) if retry_rollover else day_end
                self._state.update(lastSuccessAt=utc_iso(current), successDayThai=day.isoformat(), failures=0, error=None, nextAttemptAt=utc_iso(next_attempt), migrationPending=False, recoveredFromSavedExport=False)
                self._save()
        except Exception as exc:
            with self._lock:
                failures = min(int(self._state.get('failures', 0)) + 1, 10)
                delay = failure_delay(exc, current, failures)
                code = str(exc) if isinstance(exc, NewsSourceError) else type(exc).__name__
                self._state.update(failures=failures, error=code[:160], nextAttemptAt=utc_iso(current + timedelta(seconds=delay)))
                try:
                    self._save()
                except OSError:
                    pass
        finally:
            with self._lock:
                self._refreshing = False
        return self.snapshot(current)
