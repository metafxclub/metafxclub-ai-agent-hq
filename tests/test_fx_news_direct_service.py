from __future__ import annotations

import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIRECT_PATH = PROJECT_ROOT / "backend" / "local-runner" / "fx_news_direct.py"
MARKET_DATE = "2026-08-14"
CHECKED_AT = "2026-08-14T04:00:00Z"
NOW_UTC = datetime(2026, 8, 14, 4, 0, tzinfo=timezone.utc)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FxNewsDirectServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.direct = load_module("metafx_fx_news_direct", DIRECT_PATH)

    def source(
        self,
        source_id: str,
        currency: str,
        *,
        feed_format: str = "rss",
        timezone_name: str = "UTC",
        host: str | None = None,
    ) -> dict:
        source_host = host or f"{source_id}.example.com"
        return {
            "sourceId": source_id,
            "label": f"Official {currency} source",
            "url": f"https://{source_host}/feed",
            "host": source_host,
            "format": feed_format,
            "currency": currency,
            "timezone": timezone_name,
        }

    @staticmethod
    def empty_rss() -> bytes:
        return b"<?xml version='1.0'?><rss version='2.0'><channel></channel></rss>"

    class FakeHttpResponse:
        def __init__(self, url: str, body: bytes, *, status: int = 200, headers: dict | None = None) -> None:
            self.url = url
            self.body = body
            self.status = status
            self.headers = headers or {}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback) -> bool:
            return False

        def geturl(self) -> str:
            return self.url

        def read(self, _maximum: int) -> bytes:
            return self.body

    def test_all_configured_sources_have_valid_timezone_and_https_allowlist(self) -> None:
        self.assertEqual(
            {row["currency"] for row in self.direct.OFFICIAL_SOURCES},
            {"AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "USD"},
        )
        for source in self.direct.OFFICIAL_SOURCES:
            with self.subTest(source=source["sourceId"]):
                self.assertIsNotNone(ZoneInfo(source["timezone"]))
                self.assertTrue(source["url"].startswith("https://"))
                self.assertIn(source["host"], source["url"])
                self.assertNotIn("forexfactory", source["url"].lower())
                self.assertNotIn("faireconomy", source["url"].lower())

    def test_ics_filters_by_bangkok_day_not_iso_or_publisher_day(self) -> None:
        source = self.source(
            "ny_calendar",
            "USD",
            feed_format="ics",
            timezone_name="America/New_York",
        )
        body = b"""BEGIN:VCALENDAR
BEGIN:VEVENT
UID:crosses-bangkok-midnight
DTSTART;TZID=America/New_York:20260813T233000
SUMMARY:Consumer Price Index
DESCRIPTION:Official scheduled release
END:VEVENT
BEGIN:VEVENT
UID:publisher-day-only
DTSTART;TZID=America/New_York:20260813T070000
SUMMARY:Employment Situation
DESCRIPTION:Previous Bangkok day
END:VEVENT
END:VCALENDAR
"""
        records = self.direct.parse_ics(body, source, MARKET_DATE)
        self.assertEqual([row["sourceEventId"] for row in records], ["crosses-bangkok-midnight"])
        self.assertEqual(records[0]["scheduledAt"], "2026-08-14T03:30:00Z")
        self.assertEqual(records[0]["marketDate"], MARKET_DATE)

    def test_actual_numeric_zero_is_preserved_and_can_drive_deterministic_direction(self) -> None:
        source = self.source("official_us", "USD")
        event = self.direct.normalize_event(
            {
                "sourceEventId": "cpi-zero",
                "title": "Consumer Price Index",
                "summary": "Official release",
                "scheduledAt": "2026-08-14T12:00:00Z",
                "marketDate": MARKET_DATE,
                "timeKind": "timed",
                "publicationStatus": "published",
                "actualStatus": "released",
                "actual": "0",
                "forecast": "0.1",
                "previous": "0.2",
                "url": source["url"],
            },
            source,
            CHECKED_AT,
        )
        self.assertEqual(event["actual"], "0")
        self.assertTrue(event["actionableMacro"])
        self.assertEqual(self.direct.deterministic_currency_direction(event), "bearish")
        self.assertEqual(event["pairImpacts"]["EURUSD"]["impact"], "BULLISH")

    def test_duplicate_source_identity_collapses_to_one_event(self) -> None:
        source = self.source("official_calendar", "USD", feed_format="ics")
        body = b"""BEGIN:VCALENDAR
BEGIN:VEVENT
UID:same-official-id
DTSTART:20260814T120000Z
SUMMARY:Employment Situation
END:VEVENT
BEGIN:VEVENT
UID:same-official-id
DTSTART:20260814T120000Z
SUMMARY:Employment Situation revised title
END:VEVENT
END:VCALENDAR
"""

        def fetcher(_source: dict, _cached: dict) -> dict:
            return {"status": 200, "body": body, "etag": "v1"}

        result = self.direct.collect_official_sources(
            MARKET_DATE,
            now_utc=NOW_UTC,
            fetcher=fetcher,
            sources=(source,),
        )
        self.assertEqual(len(result["events"]), 1)
        self.assertEqual(result["events"][0]["sourceEventId"], "same-official-id")

    def test_all_success_with_no_events_is_verified_quiet_day(self) -> None:
        sources = (
            self.source("official_us", "USD"),
            self.source("official_eu", "EUR"),
        )

        def fetcher(_source: dict, _cached: dict) -> dict:
            return {"status": 200, "body": self.empty_rss()}

        result = self.direct.collect_official_sources(
            MARKET_DATE,
            now_utc=NOW_UTC,
            fetcher=fetcher,
            sources=sources,
        )
        self.assertEqual(result["sourceStatus"], "quiet_day")
        self.assertEqual(result["dataStatus"], "verified_empty")
        self.assertTrue(result["quietDay"])
        self.assertTrue(result["currentDataAvailable"])
        self.assertFalse(result["failClosed"])
        self.assertEqual(result["coverageCurrencies"], ["EUR", "USD"])

    def test_partial_zero_event_day_preserves_currency_coverage(self) -> None:
        sources = (
            self.source("official_us", "USD"),
            self.source("official_eu", "EUR"),
            self.source("official_gb", "GBP"),
        )

        def fetcher(source: dict, _cached: dict) -> dict:
            if source["currency"] == "USD":
                return {"status": 200, "body": self.empty_rss()}
            raise self.direct.SourceFetchError("timeout")

        result = self.direct.collect_official_sources(
            MARKET_DATE,
            now_utc=NOW_UTC,
            fetcher=fetcher,
            sources=sources,
        )
        self.assertEqual(result["sourceStatus"], "partial_success")
        self.assertEqual(result["dataStatus"], "degraded")
        self.assertTrue(result["partialQuietDay"])
        self.assertTrue(result["currentDataAvailable"])
        self.assertFalse(result["failClosed"])
        self.assertEqual(result["coverageCurrencies"], ["USD"])
        self.assertEqual(result["failedCurrencies"], ["EUR", "GBP"])

    def test_all_sources_failed_is_fail_closed(self) -> None:
        sources = (
            self.source("official_us", "USD"),
            self.source("official_eu", "EUR"),
        )

        def fetcher(_source: dict, _cached: dict) -> dict:
            raise self.direct.SourceFetchError("http_503")

        result = self.direct.collect_official_sources(
            MARKET_DATE,
            now_utc=NOW_UTC,
            fetcher=fetcher,
            sources=sources,
        )
        self.assertEqual(result["sourceStatus"], "source_failure")
        self.assertEqual(result["dataStatus"], "source_failure")
        self.assertFalse(result["currentDataAvailable"])
        self.assertTrue(result["failClosed"])
        self.assertEqual(result["events"], [])

    def test_new_market_date_does_not_send_or_reuse_previous_day_etag_cache(self) -> None:
        source = self.source("official_us", "USD")
        yesterday_event = {
            "eventId": "fxevent-yesterday",
            "marketDate": "2026-08-13",
            "titleTh": "Yesterday event",
        }
        previous_cache = {
            source["sourceId"]: {
                "marketDate": "2026-08-13",
                "etag": "old-etag",
                "lastModified": "Thu, 13 Aug 2026 00:00:00 GMT",
                "events": [yesterday_event],
            }
        }
        received_conditionals: list[dict] = []

        def fetcher(_source: dict, cached: dict) -> dict:
            received_conditionals.append(dict(cached))
            return {"status": 304, "body": b""}

        result = self.direct.collect_official_sources(
            MARKET_DATE,
            now_utc=NOW_UTC,
            fetcher=fetcher,
            previous_cache=previous_cache,
            sources=(source,),
        )
        self.assertEqual(received_conditionals, [{}])
        self.assertEqual(result["events"], [])
        self.assertEqual(result["sourceStatus"], "source_failure")
        self.assertEqual(result["sourceHealth"][0]["errorCode"], "unexpected_not_modified_new_market_date")
        self.assertEqual(result["sourceCache"][source["sourceId"]]["events"], [])

    def test_same_day_not_modified_reuses_only_same_day_normalized_events(self) -> None:
        source = self.source("official_us", "USD")
        event = {
            "eventId": "fxevent-today",
            "marketDate": MARKET_DATE,
            "titleTh": "Current event",
        }
        previous_cache = {
            source["sourceId"]: {
                "marketDate": MARKET_DATE,
                "etag": "same-day-etag",
                "events": [event],
            }
        }

        def fetcher(_source: dict, cached: dict) -> dict:
            self.assertEqual(cached["etag"], "same-day-etag")
            return {"status": 304, "body": b""}

        result = self.direct.collect_official_sources(
            MARKET_DATE,
            now_utc=NOW_UTC,
            fetcher=fetcher,
            previous_cache=previous_cache,
            sources=(source,),
        )
        self.assertEqual(result["events"], [event])
        self.assertTrue(result["sourceHealth"][0]["notModified"])

    def test_feed_markup_is_stripped_and_cross_host_link_falls_back_to_source(self) -> None:
        source = self.source("official_us", "USD")
        body = b"""<?xml version='1.0'?>
<rss version='2.0'><channel><item>
<guid>official-guid</guid>
<title>Consumer Price Index</title>
<pubDate>Fri, 14 Aug 2026 04:00:00 GMT</pubDate>
<link>https://attacker.example.net/copied</link>
<description>&lt;b&gt;Official&lt;/b&gt; &amp;amp; verified</description>
</item></channel></rss>"""
        rows = self.direct.parse_feed(body, source, MARKET_DATE)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], source["url"])
        self.assertNotIn("<", rows[0]["summary"])
        self.assertIn("Official", rows[0]["summary"])
        self.assertIn("verified", rows[0]["summary"])

    def test_same_host_event_link_is_retained(self) -> None:
        source = self.source("official_us", "USD")
        expected = f"https://{source['host']}/release/cpi"
        self.assertEqual(self.direct._official_event_url(expected, source), expected)
        self.assertEqual(
            self.direct._official_event_url(f"https://{source['host']}.evil.example/release", source),
            source["url"],
        )

    def test_http_fetch_enforces_source_host_redirect_and_body_bounds(self) -> None:
        source = self.source("official_us", "USD")
        invalid_source = {**source, "host": "different.example.com"}
        with self.assertRaises(self.direct.SourceFetchError) as invalid:
            self.direct.default_http_fetch(invalid_source)
        self.assertEqual(invalid.exception.code, "source_not_allowlisted")

        redirected = self.FakeHttpResponse(
            "https://attacker.example.net/feed",
            self.empty_rss(),
        )
        with mock.patch.object(self.direct, "urlopen", return_value=redirected):
            with self.assertRaises(self.direct.SourceFetchError) as redirect:
                self.direct.default_http_fetch(source)
        self.assertEqual(redirect.exception.code, "redirect_not_allowlisted")

        oversized = self.FakeHttpResponse(source["url"], b"12345")
        with mock.patch.object(self.direct, "urlopen", return_value=oversized):
            with self.assertRaises(self.direct.SourceFetchError) as body:
                self.direct.default_http_fetch(source, max_body_bytes=4)
        self.assertEqual(body.exception.code, "body_too_large")

    def test_http_fetch_sends_contact_user_agent_and_same_day_conditionals(self) -> None:
        source = self.source("official_us", "USD")
        captured = {}
        response = self.FakeHttpResponse(
            source["url"],
            self.empty_rss(),
            headers={"ETag": "next-etag", "Last-Modified": "Fri, 14 Aug 2026 04:00:00 GMT"},
        )

        def fake_urlopen(request, *, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return response

        with mock.patch.object(self.direct, "urlopen", side_effect=fake_urlopen):
            result = self.direct.default_http_fetch(
                source,
                {"etag": "prior-etag", "lastModified": "Thu, 13 Aug 2026 04:00:00 GMT"},
                timeout_seconds=7,
            )
        headers = {key.lower(): value for key, value in captured["request"].header_items()}
        self.assertIn("metafxclub56@gmail.com", headers["user-agent"].lower())
        self.assertEqual(headers["if-none-match"], "prior-etag")
        self.assertEqual(headers["if-modified-since"], "Thu, 13 Aug 2026 04:00:00 GMT")
        self.assertEqual(captured["timeout"], 7)
        self.assertEqual(result["etag"], "next-etag")

    def test_http_fetch_timeout_is_fail_closed_with_bounded_code(self) -> None:
        source = self.source("official_us", "USD")
        with mock.patch.object(self.direct, "urlopen", side_effect=TimeoutError("slow")):
            with self.assertRaises(self.direct.SourceFetchError) as timeout:
                self.direct.default_http_fetch(source, timeout_seconds=1)
        self.assertEqual(timeout.exception.code, "timeout")

    def test_appointments_and_research_are_low_informational_without_trade_claims(self) -> None:
        source = self.source("official_au", "AUD")
        for index, title in enumerate((
            "Appointment to the Monetary Policy Board",
            "Research paper on productivity and wages",
        )):
            with self.subTest(title=title):
                event = self.direct.normalize_event(
                    {
                        "sourceEventId": f"info-{index}",
                        "title": title,
                        "scheduledAt": "2026-08-14T04:00:00Z",
                        "marketDate": MARKET_DATE,
                        "timeKind": "timed",
                        "publicationStatus": "published",
                        "url": source["url"],
                    },
                    source,
                    CHECKED_AT,
                )
                self.assertEqual(event["impact"], "low")
                self.assertEqual(event["eventCategory"], "informational_publication")
                self.assertFalse(event["actionableMacro"])
                self.assertEqual(event["pairImpacts"], {})
                self.assertEqual(self.direct._danger_windows([event]), [])

    def test_actionable_macro_can_create_a_bounded_caution_window_without_direction(self) -> None:
        source = self.source("official_us", "USD")
        event = self.direct.normalize_event(
            {
                "sourceEventId": "future-cpi",
                "title": "Consumer Price Index",
                "scheduledAt": "2026-08-14T12:00:00Z",
                "marketDate": MARKET_DATE,
                "timeKind": "timed",
                "publicationStatus": "scheduled",
                "url": source["url"],
            },
            source,
            CHECKED_AT,
        )
        self.assertTrue(event["actionableMacro"])
        self.assertEqual(event["pairImpacts"], {})
        windows = self.direct._danger_windows([event])
        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0]["startsAt"], "2026-08-14T11:30:00Z")
        self.assertEqual(windows[0]["endsAt"], "2026-08-14T12:30:00Z")


if __name__ == "__main__":
    unittest.main()
