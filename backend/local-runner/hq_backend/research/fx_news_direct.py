from __future__ import annotations

"""Deterministic daily FX-news collection from official structured sources.

This module deliberately has no dependency on Missions, agents, Codex, AI, or
the dashboard runtime.  It accepts an injectable HTTP fetcher so the complete
collection and normalization path can be tested without network access.

Directional output is intentionally narrow.  A direction is emitted only when
an event has one unambiguous currency, comparable numeric ``actual`` and
``forecast`` values, and its title matches an explicit indicator rule.  Merely
publishing a central-bank release never creates a directional trading claim.
"""

import email.utils
import hashlib
import html
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


BANGKOK = ZoneInfo("Asia/Bangkok")
STORE_VERSION = "fx-daily-news-direct-store-v1"
PROVIDER_MODE = "official_structured_allowlist"
MAX_HISTORY = 64
MAX_EVENTS_PER_DAY = 120
MAX_BODY_BYTES = 1_000_000
# Stats NZ's official calendar has measured near eight seconds in production.
# Twelve seconds remains bounded while avoiding routine false source failures;
# four sources are collected concurrently and the service runs at most twice.
DEFAULT_TIMEOUT_SECONDS = 12
USER_AGENT = "Metafxclub-Daily-News/1.0 (+mailto:Metafxclub56@gmail.com)"

FX_PAIRS = (
    "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD", "CADCHF", "CADJPY",
    "CHFJPY", "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD",
    "EURUSD", "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
    "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
)

# Every network target is an HTTPS endpoint owned by the named public body.
# Forex Factory and FairEconomy are intentionally absent and are never scraped.
OFFICIAL_SOURCES = (
    {
        "sourceId": "bls_release_calendar",
        "label": "U.S. Bureau of Labor Statistics release calendar",
        "url": "https://www.bls.gov/schedule/news_release/bls.ics",
        "host": "www.bls.gov",
        "format": "ics",
        "currency": "USD",
        "timezone": "America/New_York",
    },
    {
        "sourceId": "ecb_statistical_press",
        "label": "European Central Bank statistical press releases",
        "url": "https://www.ecb.europa.eu/rss/statpress.html",
        "host": "www.ecb.europa.eu",
        "format": "rss",
        "currency": "EUR",
        "timezone": "Europe/Berlin",
    },
    {
        "sourceId": "boe_news",
        "label": "Bank of England news",
        "url": "https://www.bankofengland.co.uk/rss/news",
        "host": "www.bankofengland.co.uk",
        "format": "rss",
        "currency": "GBP",
        "timezone": "Europe/London",
    },
    {
        "sourceId": "boc_press_releases",
        "label": "Bank of Canada press releases",
        "url": "https://www.bankofcanada.ca/content_type/press-releases/feed/",
        "host": "www.bankofcanada.ca",
        "format": "rss",
        "currency": "CAD",
        "timezone": "America/Toronto",
    },
    {
        "sourceId": "rba_media_releases",
        "label": "Reserve Bank of Australia media releases",
        "url": "https://www.rba.gov.au/rss/rss-cb-media-releases.xml",
        "host": "www.rba.gov.au",
        "format": "rss",
        "currency": "AUD",
        "timezone": "Australia/Sydney",
    },
    {
        "sourceId": "stats_nz_release_calendar",
        "label": "Stats NZ release calendar",
        "url": "https://www.stats.govt.nz/release-calendar/calendar-export",
        "host": "www.stats.govt.nz",
        "format": "ics",
        "currency": "NZD",
        "timezone": "Pacific/Auckland",
    },
    {
        "sourceId": "boj_whats_new",
        "label": "Bank of Japan updates",
        "url": "https://www.boj.or.jp/en/rss/whatsnew.xml",
        "host": "www.boj.or.jp",
        "format": "rss",
        "currency": "JPY",
        "timezone": "Asia/Tokyo",
    },
    {
        "sourceId": "snb_press_releases",
        "label": "Swiss National Bank press releases",
        "url": "https://www.snb.ch/public/rss/en/pressrel",
        "host": "www.snb.ch",
        "format": "rss",
        "currency": "CHF",
        "timezone": "Europe/Zurich",
    },
)

_DIRECTION_RULES = (
    (("unemployment", "jobless", "unemployment rate"), "lower_is_bullish"),
    (("employment", "nonfarm", "non-farm", "payroll", "job openings"), "higher_is_bullish"),
    (("gross domestic product", " gdp", "retail sales", "industrial production"), "higher_is_bullish"),
    (("consumer price", " cpi", "producer price", " ppi", "inflation"), "higher_is_bullish"),
)

_IMPACT_KEYWORDS = {
    "high": (
        "interest rate", "rate decision", "monetary policy", "nonfarm", "non-farm",
        "payroll", "consumer price", " cpi", "gross domestic product", " gdp",
        "unemployment rate", "employment situation",
    ),
    "medium": (
        "retail sales", "producer price", " ppi", "industrial production",
        "job openings", "minutes", "speech", "press conference", "financial stability",
    ),
}

_INFORMATIONAL_KEYWORDS = (
    "appointment", "appointed", "research paper", "working paper", "bulletin",
    "conference", "seminar", "podcast", "productivity", "wages research",
    "annual report", "financial statements", "operational notice", "procurement",
)
_MACRO_RELEASE_KEYWORDS = tuple(dict.fromkeys(
    keyword.strip()
    for values in _IMPACT_KEYWORDS.values()
    for keyword in values
)) + (
    "employment", "unemployment", "jobless", "inflation", "price index",
    "money stock", "monetary base", "trade balance", "balance of payments",
    "business survey", "consumer confidence", "purchasing managers", "pmi",
)

_MACRO_PRESS_CONFERENCE_MARKERS = (
    "monetary policy", "interest rate", "rate decision", "central bank",
    "federal reserve", "ecb", "bank of england", "bank of canada",
    "bank of japan", "reserve bank", "snb", "inflation report",
)


class SourceFetchError(RuntimeError):
    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(message or code)
        self.code = code


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_text(value: object, maximum: int) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:maximum]


def _plain_text(value: object, maximum: int) -> str:
    decoded = html.unescape(str(value or ""))
    without_markup = re.sub(r"<[^>]{0,500}>", " ", decoded)
    return _safe_text(without_markup, maximum)


def _official_event_url(value: object, source: dict) -> str:
    candidate = _safe_text(value, 1000)
    parsed = urlparse(candidate)
    if (
        parsed.scheme.lower() == "https"
        and (parsed.hostname or "").lower().rstrip(".") == source.get("host")
    ):
        return candidate
    return str(source["url"])


def _digest(*values: object, length: int = 24) -> str:
    raw = "\x1f".join(str(value or "") for value in values)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:length]


def _tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1].lower()


def _child_text(element: ET.Element, names: tuple[str, ...]) -> str:
    wanted = set(names)
    for child in list(element):
        if _tag(child) in wanted:
            return _safe_text("".join(child.itertext()), 2000)
    return ""


def _entry_link(element: ET.Element) -> str:
    for child in list(element):
        if _tag(child) != "link":
            continue
        href = _safe_text(child.attrib.get("href"), 1000)
        if href:
            return href
        text = _safe_text("".join(child.itertext()), 1000)
        if text:
            return text
    return ""


def _parse_feed_time(value: object, default_tz: ZoneInfo) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    parsed: datetime | None = None
    try:
        parsed = email.utils.parsedate_to_datetime(raw)
    except (TypeError, ValueError, OverflowError):
        parsed = None
    if parsed is None:
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=default_tz)
    return parsed.astimezone(timezone.utc)


def _unfold_ics(text: str) -> list[str]:
    rows: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw.startswith((" ", "\t")) and rows:
            rows[-1] += raw[1:]
        else:
            rows.append(raw)
    return rows


def _parse_ics_datetime(
    raw: str,
    parameters: dict[str, str],
    default_tz: ZoneInfo,
) -> tuple[datetime | None, str, str | None]:
    value = raw.strip()
    is_date = parameters.get("VALUE", "").upper() == "DATE" or bool(re.fullmatch(r"\d{8}", value))
    if is_date:
        try:
            event_date = datetime.strptime(value[:8], "%Y%m%d").date().isoformat()
        except ValueError:
            return None, "all_day", None
        return None, "all_day", event_date
    event_tz = default_tz
    tzid = parameters.get("TZID")
    if tzid:
        try:
            event_tz = ZoneInfo(tzid)
        except Exception:
            return None, "timed", None
    fmt = "%Y%m%dT%H%M%S" if len(value.rstrip("Z")) >= 15 else "%Y%m%dT%H%M"
    try:
        parsed = datetime.strptime(value.rstrip("Z"), fmt)
    except ValueError:
        return None, "timed", None
    parsed = parsed.replace(tzinfo=timezone.utc if value.endswith("Z") else event_tz)
    return parsed.astimezone(timezone.utc), "timed", None


def impact_for_title(title: object) -> str:
    normalized = f" {str(title or '').strip().lower()}"
    if (
        "press conference" in normalized
        and any(marker in normalized for marker in _MACRO_PRESS_CONFERENCE_MARKERS)
    ):
        return "medium"
    if any(keyword in normalized for keyword in _INFORMATIONAL_KEYWORDS):
        return "low"
    for impact in ("high", "medium"):
        if any(keyword in normalized for keyword in _IMPACT_KEYWORDS[impact]):
            return impact
    return "low"


def event_taxonomy(title: object) -> tuple[str, bool]:
    normalized = f" {str(title or '').strip().lower()}"
    if (
        "press conference" in normalized
        and any(marker in normalized for marker in _MACRO_PRESS_CONFERENCE_MARKERS)
    ):
        return "economic_release", True
    if any(keyword in normalized for keyword in _INFORMATIONAL_KEYWORDS):
        return "informational_publication", False
    if any(keyword in normalized for keyword in _MACRO_RELEASE_KEYWORDS):
        return "economic_release", True
    return "informational_publication", False


def parse_ics(
    body: bytes,
    source: dict,
    market_date: str,
) -> list[dict]:
    try:
        text = body.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise SourceFetchError("invalid_encoding", str(error)) from error
    try:
        default_tz = ZoneInfo(str(source.get("timezone") or "UTC"))
    except Exception as error:
        raise SourceFetchError("invalid_source_timezone", str(error)) from error
    records: list[dict] = []
    current: dict[str, tuple[str, dict[str, str]]] | None = None
    for line in _unfold_ics(text):
        upper = line.strip().upper()
        if upper == "BEGIN:VEVENT":
            current = {}
            continue
        if upper == "END:VEVENT":
            if current is not None:
                raw_start, parameters = current.get("DTSTART", ("", {}))
                scheduled, time_kind, all_day_date = _parse_ics_datetime(raw_start, parameters, default_tz)
                event_market_date = (
                    scheduled.astimezone(BANGKOK).date().isoformat()
                    if scheduled is not None
                    else all_day_date
                )
                title = _safe_text(current.get("SUMMARY", ("", {}))[0], 300)
                if title and event_market_date == market_date:
                    uid = _safe_text(current.get("UID", ("", {}))[0], 300)
                    description = _plain_text(current.get("DESCRIPTION", ("", {}))[0], 1200)
                    link = _official_event_url(current.get("URL", ("", {}))[0], source)
                    records.append({
                        "sourceEventId": uid or _digest(source["sourceId"], title, scheduled or event_market_date),
                        "title": title,
                        "summary": description or title,
                        "detail": description or title,
                        "scheduledAt": _iso_utc(scheduled) if scheduled is not None else None,
                        "marketDate": event_market_date,
                        "timeKind": time_kind,
                        "publishedAt": None,
                        "url": link,
                        "publicationStatus": "scheduled",
                    })
            current = None
            continue
        if current is None or ":" not in line:
            continue
        lhs, value = line.split(":", 1)
        pieces = lhs.split(";")
        key = pieces[0].upper()
        parameters = {}
        for item in pieces[1:]:
            if "=" in item:
                param_key, param_value = item.split("=", 1)
                parameters[param_key.upper()] = param_value
        if key in {"UID", "SUMMARY", "DESCRIPTION", "URL", "DTSTART"}:
            current[key] = (value.replace("\\n", "\n").replace("\\,", ","), parameters)
    return records


def parse_feed(
    body: bytes,
    source: dict,
    market_date: str,
) -> list[dict]:
    try:
        root = ET.fromstring(body)
    except ET.ParseError as error:
        raise SourceFetchError("invalid_xml", str(error)) from error
    try:
        default_tz = ZoneInfo(str(source.get("timezone") or "UTC"))
    except Exception as error:
        raise SourceFetchError("invalid_source_timezone", str(error)) from error
    entries = [element for element in root.iter() if _tag(element) in {"item", "entry"}]
    records: list[dict] = []
    for entry in entries[:200]:
        title = _child_text(entry, ("title",))
        if not title:
            continue
        date_text = _child_text(entry, ("pubdate", "published", "updated", "date"))
        published = _parse_feed_time(date_text, default_tz)
        if published is None or published.astimezone(BANGKOK).date().isoformat() != market_date:
            continue
        link = _official_event_url(_entry_link(entry), source)
        entry_id = _child_text(entry, ("guid", "id")) or link
        summary = _plain_text(
            _child_text(entry, ("description", "summary", "content")) or title,
            1200,
        )
        records.append({
            "sourceEventId": _safe_text(entry_id, 500) or _digest(source["sourceId"], title, date_text),
            "title": title,
            "summary": summary,
            "detail": summary,
            "scheduledAt": _iso_utc(published),
            "marketDate": market_date,
            "timeKind": "timed",
            "publishedAt": _iso_utc(published),
            "url": link,
            "publicationStatus": "published",
        })
    return records


def default_http_fetch(
    source: dict,
    conditional: dict | None = None,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    max_body_bytes: int = MAX_BODY_BYTES,
) -> dict:
    url = str(source.get("url") or "")
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https" or (parsed.hostname or "").lower() != source.get("host"):
        raise SourceFetchError("source_not_allowlisted")
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, text/calendar;q=0.9",
    }
    cached = conditional if isinstance(conditional, dict) else {}
    if cached.get("etag"):
        headers["If-None-Match"] = str(cached["etag"])
    if cached.get("lastModified"):
        headers["If-Modified-Since"] = str(cached["lastModified"])
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=max(1, int(timeout_seconds))) as response:
            status = int(getattr(response, "status", 200) or 200)
            final = urlparse(str(response.geturl() or url))
            if final.scheme.lower() != "https" or (final.hostname or "").lower() != source.get("host"):
                raise SourceFetchError("redirect_not_allowlisted")
            body = response.read(max_body_bytes + 1)
            if len(body) > max_body_bytes:
                raise SourceFetchError("body_too_large")
            return {
                "status": status,
                "body": body,
                "etag": response.headers.get("ETag"),
                "lastModified": response.headers.get("Last-Modified"),
            }
    except SourceFetchError:
        raise
    except Exception as error:
        code = "http_error"
        if getattr(error, "code", None) == 304:
            return {"status": 304, "body": b"", "etag": cached.get("etag"), "lastModified": cached.get("lastModified")}
        if isinstance(error, TimeoutError):
            code = "timeout"
        raise SourceFetchError(code, type(error).__name__) from error


def _numeric_scalar(value: object) -> tuple[float, str] | None:
    if isinstance(value, bool) or value is None:
        return None
    raw = str(value).strip().lower().replace(",", "")
    match = re.fullmatch(r"([-+]?\d+(?:\.\d+)?)\s*(%|k|m|b)?", raw)
    if not match:
        return None
    try:
        number = float(match.group(1))
    except ValueError:
        return None
    unit = match.group(2) or "number"
    return number, unit


def deterministic_currency_direction(event: dict) -> str | None:
    if event.get("actionableMacro") is not True:
        return None
    currencies = [str(value or "").upper() for value in (event.get("currencies") or [])]
    if len(set(currencies)) != 1:
        return None
    actual = _numeric_scalar(event.get("actual"))
    forecast = _numeric_scalar(event.get("forecast"))
    if actual is None or forecast is None or actual[1] != forecast[1]:
        return None
    title = f" {str(event.get('title') or event.get('titleTh') or '').lower()}"
    rule = next(
        (direction for keywords, direction in _DIRECTION_RULES if any(keyword in title for keyword in keywords)),
        None,
    )
    if rule is None:
        return None
    if actual[0] == forecast[0]:
        return "sideway"
    higher = actual[0] > forecast[0]
    bullish = higher if rule == "higher_is_bullish" else not higher
    return "bullish" if bullish else "bearish"


def _pair_impacts(event: dict) -> dict[str, dict]:
    direction = deterministic_currency_direction(event)
    currencies = list(dict.fromkeys(str(value or "").upper() for value in (event.get("currencies") or [])))
    if direction is None or len(currencies) != 1:
        return {}
    currency = currencies[0]
    source_ref = str(event.get("sourceRef") or "")
    impacts: dict[str, dict] = {}
    for pair in FX_PAIRS:
        if currency not in {pair[:3], pair[3:]}:
            continue
        if direction == "sideway":
            pair_direction = "SIDEWAY"
        elif currency == pair[:3]:
            pair_direction = direction.upper()
        else:
            pair_direction = ("bearish" if direction == "bullish" else "bullish").upper()
        impacts[pair] = {
            "impact": pair_direction,
            "confidence": 70,
            "sourceRefs": [source_ref] if source_ref else [],
            "reasonTh": "กฎ deterministic จาก Actual เทียบ Forecast ของแหล่งทางการ",
        }
    return impacts


def normalize_event(record: dict, source: dict, checked_at: str) -> dict:
    source_event_id = _safe_text(record.get("sourceEventId"), 500)
    event_id = f"fxevent-{_digest(source['sourceId'], source_event_id)}"
    publication_status = str(record.get("publicationStatus") or "scheduled")
    title = _plain_text(record.get("title"), 300)
    actual_present = "actual" in record and record.get("actual") is not None
    actual_status = str(record.get("actualStatus") or ("released" if actual_present else "not_applicable" if publication_status == "published" else "pending"))
    event_category, actionable_macro = event_taxonomy(title)
    event = {
        "eventId": event_id,
        "sourceEventId": source_event_id,
        "titleTh": title,
        "title": title,
        "summaryTh": _plain_text(record.get("summary") or title, 1200),
        "detailTh": _plain_text(record.get("detail") or record.get("summary") or title, 1600),
        "currencies": [source["currency"]],
        "scheduledAt": record.get("scheduledAt"),
        "marketDate": record.get("marketDate"),
        "timeKind": str(record.get("timeKind") or "timed"),
        "impact": str(record.get("impact") or impact_for_title(title)),
        "eventCategory": event_category,
        "actionableMacro": actionable_macro,
        "actual": record.get("actual") if actual_present else None,
        "actualStatus": actual_status,
        "forecast": record.get("forecast"),
        "previous": record.get("previous"),
        "publicationStatus": publication_status,
        "publishedAt": record.get("publishedAt"),
        "sourceRef": source["sourceId"],
        "sourceRefs": [source["sourceId"]],
        "sourceUrl": _official_event_url(record.get("url"), source),
        "checkedAt": checked_at,
    }
    event["pairImpacts"] = _pair_impacts(event)
    return event


def collect_official_sources(
    market_date: str,
    *,
    now_utc: datetime | None = None,
    fetcher=None,
    previous_cache: dict | None = None,
    sources: tuple[dict, ...] = OFFICIAL_SOURCES,
) -> dict:
    reference = now_utc or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    else:
        reference = reference.astimezone(timezone.utc)
    checked_at = _iso_utc(reference)
    fetch = fetcher or default_http_fetch
    cached_by_source = previous_cache if isinstance(previous_cache, dict) else {}

    def one(source: dict) -> dict:
        raw_cached = cached_by_source.get(source["sourceId"])
        raw_cached = raw_cached if isinstance(raw_cached, dict) else {}
        same_market_date = raw_cached.get("marketDate") == market_date
        cached = raw_cached if same_market_date else {}
        try:
            response = fetch(source, cached)
            if not isinstance(response, dict):
                raise SourceFetchError("invalid_fetch_response")
            status = int(response.get("status") or 200)
            if status == 304:
                if not same_market_date:
                    raise SourceFetchError("unexpected_not_modified_new_market_date")
                cached_events = cached.get("events") if isinstance(cached.get("events"), list) else []
                return {
                    "source": source,
                    "events": cached_events,
                    "status": "success" if cached_events else "quiet_day",
                    "notModified": True,
                    "etag": cached.get("etag"),
                    "lastModified": cached.get("lastModified"),
                }
            if status < 200 or status >= 300:
                raise SourceFetchError(f"http_{status}")
            body = response.get("body")
            if not isinstance(body, (bytes, bytearray)):
                raise SourceFetchError("invalid_body")
            records = (
                parse_ics(bytes(body), source, market_date)
                if source.get("format") == "ics"
                else parse_feed(bytes(body), source, market_date)
            )
            events = [normalize_event(record, source, checked_at) for record in records]
            return {
                "source": source,
                "events": events,
                "status": "success" if events else "quiet_day",
                "notModified": False,
                "etag": response.get("etag"),
                "lastModified": response.get("lastModified"),
            }
        except SourceFetchError as error:
            return {"source": source, "events": [], "status": "source_failure", "errorCode": error.code}
        except Exception as error:
            return {"source": source, "events": [], "status": "source_failure", "errorCode": f"unexpected_{type(error).__name__.lower()}"}

    results: list[dict] = []
    workers = min(4, max(1, len(sources)))
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="fx-news-source") as pool:
        future_map = {pool.submit(one, source): source for source in sources}
        for future in as_completed(future_map):
            results.append(future.result())
    results.sort(key=lambda item: next(index for index, source in enumerate(sources) if source["sourceId"] == item["source"]["sourceId"]))

    all_events: dict[str, dict] = {}
    source_health: list[dict] = []
    source_cache: dict[str, dict] = {}
    coverage_currencies: set[str] = set()
    failed_currencies: set[str] = set()
    successes = 0
    failures = 0
    for result in results:
        source = result["source"]
        events = result.get("events") if isinstance(result.get("events"), list) else []
        prior_cache = cached_by_source.get(source["sourceId"])
        prior_cache = prior_cache if isinstance(prior_cache, dict) else {}
        same_day_cache = prior_cache if prior_cache.get("marketDate") == market_date else {}
        if result["status"] == "source_failure":
            failures += 1
            failed_currencies.add(str(source["currency"]))
        else:
            successes += 1
            coverage_currencies.add(str(source["currency"]))
        for event in events:
            key = str(event.get("eventId") or _digest(source["sourceId"], event))
            all_events[key] = event
        source_health.append({
            "sourceId": source["sourceId"],
            "label": source["label"],
            "url": source["url"],
            "currency": source["currency"],
            "status": result["status"],
            "lastCheckedAt": checked_at,
            "lastSuccessAt": checked_at if result["status"] != "source_failure" else prior_cache.get("lastSuccessAt"),
            "eventCount": len(events),
            "errorCode": result.get("errorCode"),
            "notModified": bool(result.get("notModified")),
        })
        source_cache[source["sourceId"]] = {
            "marketDate": market_date,
            "etag": result.get("etag"),
            "lastModified": result.get("lastModified"),
            "lastSuccessAt": checked_at if result["status"] != "source_failure" else prior_cache.get("lastSuccessAt"),
            "events": events if result["status"] != "source_failure" else same_day_cache.get("events", []),
        }
    events = sorted(
        all_events.values(),
        key=lambda row: (str(row.get("scheduledAt") or "9999"), str(row.get("eventId") or "")),
    )[:MAX_EVENTS_PER_DAY]
    if failures == 0 and not events:
        source_status = "quiet_day"
        data_status = "verified_empty"
        current_available = True
        fail_closed = False
    elif failures == 0:
        source_status = "verified"
        data_status = "verified"
        current_available = True
        fail_closed = False
    elif successes > 0:
        source_status = "partial_success"
        data_status = "degraded"
        current_available = True
        fail_closed = False
    else:
        source_status = "source_failure"
        data_status = "source_failure"
        current_available = False
        fail_closed = True
    return {
        "checkedAt": checked_at,
        "marketDate": market_date,
        "events": events,
        "sourceHealth": source_health,
        "sourceCache": source_cache,
        "sourceStatus": source_status,
        "dataStatus": data_status,
        "quietDay": bool(failures == 0 and not events),
        "partialQuietDay": bool(failures > 0 and successes > 0 and not events),
        "currentDataAvailable": current_available,
        "failClosed": fail_closed,
        "coverageCurrencies": sorted(coverage_currencies),
        "failedCurrencies": sorted(failed_currencies - coverage_currencies),
        "successfulSourceCount": successes,
        "failedSourceCount": failures,
    }


def _danger_windows(events: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for event in events:
        if (
            event.get("actionableMacro") is not True
            or event.get("impact") not in {"medium", "high"}
            or event.get("timeKind") != "timed"
        ):
            continue
        try:
            scheduled = datetime.fromisoformat(str(event.get("scheduledAt") or "").replace("Z", "+00:00"))
        except ValueError:
            continue
        rows.append({
            "windowId": f"fxwindow-{_digest(event.get('eventId'))}",
            "currencies": list(event.get("currencies") or []),
            "startsAt": _iso_utc(scheduled - timedelta(minutes=30)),
            "endsAt": _iso_utc(scheduled + timedelta(minutes=30)),
            "reasonTh": f"ช่วงเฝ้าระวังข่าว {event.get('titleTh')}",
            "sourceRefs": list(event.get("sourceRefs") or []),
        })
    return rows[:3]


def pair_bias_rows(events: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for pair in FX_PAIRS:
        directional = []
        refs: list[str] = []
        for event in events:
            impact = (event.get("pairImpacts") or {}).get(pair) if isinstance(event.get("pairImpacts"), dict) else None
            if not isinstance(impact, dict):
                continue
            direction = str(impact.get("impact") or "").upper()
            if direction in {"BULLISH", "BEARISH", "SIDEWAY"}:
                directional.append(direction)
                refs.extend(str(value) for value in (impact.get("sourceRefs") or []) if value)
        unique = set(directional)
        short = directional[-1] if len(unique) == 1 and directional else "INSUFFICIENT_DATA"
        rows.append({
            "pair": pair,
            "short": {
                "bias": short,
                "confidence": 70 if short != "INSUFFICIENT_DATA" else None,
                "sourceRefs": list(dict.fromkeys(refs)) if short != "INSUFFICIENT_DATA" else [],
            },
            "medium": {"bias": "INSUFFICIENT_DATA", "confidence": None, "sourceRefs": []},
            "long": {"bias": "INSUFFICIENT_DATA", "confidence": None, "sourceRefs": []},
            "confidence": 70 if short != "INSUFFICIENT_DATA" else None,
            "verified": short != "INSUFFICIENT_DATA",
        })
    return rows


def build_snapshot(
    collection: dict,
    *,
    trigger_source: str,
    idempotency_digest: str | None,
) -> dict:
    checked_at = str(collection.get("checkedAt") or "")
    market_date = str(collection.get("marketDate") or "")
    events = list(collection.get("events") or [])
    source_links = [
        {
            "id": row["sourceId"],
            "title": row["label"],
            "url": row["url"],
            "checkedAt": row["lastCheckedAt"],
        }
        for row in (collection.get("sourceHealth") or [])
        if row.get("status") != "source_failure"
    ]
    return {
        "snapshotId": f"fxnews-{market_date}-{_digest(checked_at, trigger_source)}",
        "marketDate": market_date,
        "createdAt": checked_at,
        "updatedAt": checked_at,
        "triggerSource": trigger_source,
        "idempotencyKeyDigest": idempotency_digest,
        "providerMode": PROVIDER_MODE,
        "sourceStatus": collection.get("sourceStatus"),
        "dataStatus": collection.get("dataStatus"),
        "quietDay": bool(collection.get("quietDay")),
        "partialQuietDay": bool(collection.get("partialQuietDay")),
        "currentDataAvailable": bool(collection.get("currentDataAvailable")),
        "failClosed": bool(collection.get("failClosed")),
        "coverageCurrencies": list(collection.get("coverageCurrencies") or []),
        "failedCurrencies": list(collection.get("failedCurrencies") or []),
        "successfulSourceCount": int(collection.get("successfulSourceCount") or 0),
        "failedSourceCount": int(collection.get("failedSourceCount") or 0),
        "sourceHealth": list(collection.get("sourceHealth") or []),
        "sourceLinks": source_links,
        "events": events,
        "dangerWindows": _danger_windows(events),
        "pairBias": pair_bias_rows(events),
    }


def empty_store() -> dict:
    return {
        "storeVersion": STORE_VERSION,
        "providerMode": PROVIDER_MODE,
        "updatedAt": None,
        "lastAttemptAt": None,
        "lastSuccessAt": None,
        "latestSnapshotId": None,
        "latestSuccessfulSnapshotId": None,
        "sourceCache": {},
        "history": [],
    }


def normalize_store(value: object) -> dict:
    source = value if isinstance(value, dict) else {}
    history = [row for row in (source.get("history") or []) if isinstance(row, dict)][-MAX_HISTORY:]
    result = empty_store()
    result.update({
        "updatedAt": source.get("updatedAt"),
        "lastAttemptAt": source.get("lastAttemptAt"),
        "lastSuccessAt": source.get("lastSuccessAt"),
        "latestSnapshotId": source.get("latestSnapshotId"),
        "latestSuccessfulSnapshotId": source.get("latestSuccessfulSnapshotId"),
        "sourceCache": source.get("sourceCache") if isinstance(source.get("sourceCache"), dict) else {},
        "history": history,
    })
    return result


def append_snapshot(store: object, snapshot: dict, source_cache: dict) -> dict:
    result = normalize_store(store)
    snapshot_id = str(snapshot.get("snapshotId") or "")
    history = [row for row in result["history"] if row.get("snapshotId") != snapshot_id]
    history.append(snapshot)
    result.update({
        "updatedAt": snapshot.get("updatedAt"),
        "lastAttemptAt": snapshot.get("updatedAt"),
        "latestSnapshotId": snapshot_id,
        "sourceCache": source_cache,
        "history": history[-MAX_HISTORY:],
    })
    if snapshot.get("currentDataAvailable") is True:
        result["lastSuccessAt"] = snapshot.get("updatedAt")
        result["latestSuccessfulSnapshotId"] = snapshot_id
    return result


def latest_snapshot(store: object) -> dict | None:
    normalized = normalize_store(store)
    snapshot_id = normalized.get("latestSnapshotId")
    return next((row for row in reversed(normalized["history"]) if row.get("snapshotId") == snapshot_id), None)


def latest_successful_snapshot(store: object) -> dict | None:
    normalized = normalize_store(store)
    snapshot_id = normalized.get("latestSuccessfulSnapshotId")
    return next((row for row in reversed(normalized["history"]) if row.get("snapshotId") == snapshot_id), None)


def history_days(store: object, *, limit: int = 14) -> list[dict]:
    normalized = normalize_store(store)
    days: dict[str, dict] = {}
    for snapshot in normalized["history"]:
        market_date = str(snapshot.get("marketDate") or "")
        if not market_date:
            continue
        row = days.setdefault(market_date, {"marketDate": market_date, "events": {}, "lastUpdatedAt": None})
        for event in snapshot.get("events") or []:
            if isinstance(event, dict) and event.get("eventId"):
                row["events"][event["eventId"]] = event
        row["lastUpdatedAt"] = snapshot.get("updatedAt") or row["lastUpdatedAt"]
    return [
        {"marketDate": row["marketDate"], "events": list(row["events"].values()), "eventCount": len(row["events"]), "lastUpdatedAt": row["lastUpdatedAt"]}
        for _, row in sorted(days.items(), reverse=True)[: max(1, min(int(limit), 31))]
    ]
