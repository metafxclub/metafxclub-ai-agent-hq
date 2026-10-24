import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / 'live_backend' / 'news.py'
SPEC = importlib.util.spec_from_file_location('live_news_test_target', MODULE)
news = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(news)


def instant(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def exports(rows):
    """Deterministic fixtures, never fetched by tests."""
    country_codes = {'USD': 'US', 'EUR': 'EZ', 'JPY': 'JN', 'NZD': 'NZ', 'GBP': 'UK', 'CHF': 'SZ', 'CNY': 'CH'}
    calendar = ['BEGIN:VCALENDAR']
    xml = ['<weeklyevents>']
    for index, row in enumerate(rows):
        dt = instant(row['date'])
        start = dt.astimezone(news.NEW_YORK).strftime('%Y%m%dT%H%M%S')
        currency = country_codes.get(row['country'], 'WW')
        calendar += ['BEGIN:VEVENT', f"UID:{row.get('uid', index + 1)}", f"SUMMARY:⁎ {currency} {row['title']}", f'DTSTART;TZID=America/New_York:{start}', 'URL:https://www.forexfactory.com/calendar/123-test', 'END:VEVENT']
        xml += [f"<event><title>{row['title']}</title><country>{row['country']}</country><time>{row.get('precision', '8:30am')}</time></event>"]
    calendar.append('END:VCALENDAR')
    xml.append('</weeklyevents>')
    return {'json': json.dumps(rows).encode(), 'ics': '\n'.join(calendar).encode(), 'xml': ''.join(xml).encode()}


def row(title='CPI m/m', dt='2026-10-23T08:30:00-04:00', currency='USD', uid=10, **extra):
    return {'title': title, 'date': dt, 'country': currency, 'impact': 'High', 'forecast': '0.3%', 'previous': '0.2%', 'uid': uid, **extra}


class FakeFetcher:
    def __init__(self, rows):
        self.payload = exports(rows)
        self.calls = []
        self.fail = False

    def __call__(self, url):
        self.calls.append(url)
        if self.fail:
            raise news.NewsSourceError('http_503')
        return self.payload[url.rsplit('.', 1)[-1]]


class NormalizationTests(unittest.TestCase):
    def normalize(self, rows):
        payload = exports(rows)
        return news.normalize_exports(payload['json'], payload['ics'], payload['xml'])

    def test_all_same_time_events_and_all_impacts_survive(self):
        rows = [row('CPI m/m', uid=1), row('Core CPI m/m', uid=2, impact='Low'), row('GDP q/q', uid=3, impact='Medium'), row('Bank Holiday', uid=4, impact='Holiday', precision='All Day')]
        events, coverage = self.normalize(rows)
        self.assertEqual(len(events), 4)
        self.assertEqual(len({event['id'] for event in events}), 4)
        self.assertEqual({event['impact'] for event in events}, {'high', 'low', 'medium', 'holiday'})
        self.assertEqual(coverage['sourceCount'], 4)

    def test_exact_offset_converts_cross_midnight_to_thai_day(self):
        events, _ = self.normalize([row(dt='2026-10-23T19:30:00-04:00')])
        self.assertEqual(events[0]['time'], '2026-10-23T23:30:00Z')
        self.assertEqual(events[0]['dayThai'], '2026-10-24')
        self.assertEqual(events[0]['timeLabel'], '06:30')
        self.assertEqual(events[0]['sourceTimeZone'], 'America/New_York')
        self.assertEqual(events[0]['timePrecision'], 'minute')

    def test_dst_offsets_are_not_fixed_to_four_hours(self):
        events, _ = self.normalize([row(dt='2026-11-03T08:30:00-05:00')])
        self.assertEqual(events[0]['timeLabel'], '20:30')
        self.assertEqual(events[0]['time'], '2026-11-03T13:30:00Z')

    def test_publisher_ics_country_codes_are_not_iso_codes(self):
        events, _ = self.normalize([row('CPI y/y', currency='CNY', uid=1), row('CPI y/y', currency='CHF', uid=2), row('CPI y/y', currency='JPY', uid=3)])
        self.assertEqual([event['currency'] for event in events], ['CNY', 'CHF', 'JPY'])
        self.assertTrue(all(event['idStability'] == 'source_uid' for event in events))

    def test_ics_country_prefix_reconciles_german_event_name(self):
        payload = exports([row('German ZEW Economic Sentiment', currency='EUR')])
        payload['ics'] = payload['ics'].replace(b'EZ German ZEW', b'GE ZEW')
        events, _ = news.normalize_exports(payload['json'], payload['ics'], payload['xml'])
        self.assertEqual(events[0]['idStability'], 'source_uid')
        self.assertEqual(events[0]['timeKind'], 'timed')

    def test_tentative_and_all_day_do_not_invent_times(self):
        events, _ = self.normalize([row('Bond Auction', uid=1, precision='Tentative'), row('Bank Holiday', uid=2, precision='All Day')])
        self.assertEqual([event['time'] for event in events], [None, None])
        self.assertEqual([event['timeKind'] for event in events], ['tentative', 'all_day'])
        self.assertEqual([event['timePrecision'] for event in events], ['tentative', 'all_day'])
        self.assertTrue(all(event['dayThaiEstimated'] for event in events))

    def test_repeated_titles_keep_precision_and_uids(self):
        events, _ = self.normalize([row('Bond Auction', uid=1, precision='Tentative'), row('Bond Auction', dt='2026-10-24T08:30:00-04:00', uid=2)])
        self.assertEqual(events[0]['timeKind'], 'tentative')
        self.assertEqual(events[1]['timeKind'], 'timed')
        self.assertNotEqual(events[0]['id'], events[1]['id'])

    def test_uid_is_stable_when_time_changes(self):
        first, _ = self.normalize([row(uid=300)])
        second, _ = self.normalize([row(uid=300, dt='2026-10-23T09:15:00-04:00')])
        self.assertEqual(first[0]['id'], second[0]['id'])
        self.assertNotEqual(first[0]['time'], second[0]['time'])

    def test_actual_is_explicitly_unsupported_even_if_unexpected_field_arrives(self):
        events, _ = self.normalize([row(actual='0.4%')])
        self.assertIsNone(events[0]['actual'])
        self.assertIsNone(events[0]['actualValue'])
        self.assertFalse(events[0]['supportsActual'])
        self.assertEqual(events[0]['actualStatus'], 'unsupported')
        self.assertFalse(events[0]['mock'])
        self.assertEqual(events[0]['aiStatus'], 'not_run')

    def test_missing_or_unknown_consensus_does_not_create_scenario(self):
        events, _ = self.normalize([row(forecast='', previous='0%'), row('Bond Auction', uid=20, forecast='3.58|1.2')])
        self.assertIsNone(events[0]['forecastValue'])
        self.assertEqual(events[0]['previousValue'], 0)
        self.assertEqual(events[0]['kind'], 'informational')
        self.assertEqual(events[1]['kind'], 'informational')
        self.assertIsNone(events[1]['forecastValue'])

    def test_numeric_parser_requires_one_unambiguous_value(self):
        for raw, expected in [('0%', 0), ('-775M', -775000000), ('1.39M', 1390000), ('23.8B', 23800000000), ('1,200', 1200), ('', None), ('3.58|1.2', None), ('high rate 3.9%', None)]:
            self.assertEqual(news.numeric_value(raw), expected)

    def test_unknown_time_when_precision_metadata_is_unavailable(self):
        payload = exports([row()])
        events, coverage = news.normalize_exports(payload['json'])
        self.assertIsNone(events[0]['time'])
        self.assertEqual(events[0]['timeKind'], 'unknown')
        self.assertEqual(coverage['ambiguousTimeCount'], 1)

    def test_naive_time_invalid_payload_and_xml_entities_rejected(self):
        for payload in [b'{}', b'[]', json.dumps([row(dt='2026-10-23T08:30:00')]).encode()]:
            with self.assertRaises(news.NewsSourceError):
                news.normalize_exports(payload)
        with self.assertRaises(news.NewsSourceError):
            news.parse_xml_metadata(b'<!DOCTYPE test [<!ENTITY x "test">]><weeklyevents/>')


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.fetch = FakeFetcher([row()])
        self.service = news.NewsService(self.folder.name, fetcher=self.fetch)

    def test_snapshot_is_read_only_and_daily_success_survives_restart(self):
        friday = instant('2026-10-23T10:00:00Z')
        self.assertEqual(self.service.snapshot(friday)['status'], 'unavailable')
        self.assertEqual(self.fetch.calls, [])
        first = self.service.refresh_if_due(friday)
        self.assertEqual(first['status'], 'ready')
        self.assertEqual(len(self.fetch.calls), 3)
        self.assertEqual(first['coverage']['sourceCount'], first['coverage']['normalizedCount'])
        self.service.refresh_if_due(instant('2026-10-23T12:00:00Z'))
        restarted = news.NewsService(self.folder.name, fetcher=self.fetch)
        restarted.refresh_if_due(instant('2026-10-23T13:00:00Z'))
        self.assertEqual(len(self.fetch.calls), 3)

    def test_thai_midnight_starts_one_new_round(self):
        self.service.refresh_if_due(instant('2026-10-23T16:59:00Z'))
        result = self.service.refresh_if_due(instant('2026-10-23T17:00:00Z'))
        self.assertEqual(len(self.fetch.calls), 6)
        self.assertEqual(result['dayThai'], '2026-10-24')
        self.assertEqual(result['status'], 'empty')
        self.assertTrue(result['coverage']['thaiDayFullyCovered'])
        self.assertIn({'dayThai': '2026-10-24', 'count': 0, 'fullyCovered': True}, result['availableDays'])

    def test_failure_keeps_last_good_and_backs_off(self):
        self.service.refresh_if_due(instant('2026-10-23T10:00:00Z'))
        self.fetch.fail = True
        result = self.service.refresh_if_due(instant('2026-10-23T17:00:00Z'))
        self.assertEqual(result['status'], 'stale')
        self.assertEqual(len(result['calendarEvents']), 1)
        self.assertEqual(result['error'], 'http_503')
        self.service.refresh_if_due(instant('2026-10-23T17:00:30Z'))
        self.assertEqual(len(self.fetch.calls), 4)
        self.service.refresh_if_due(instant('2026-10-23T17:01:00Z'))
        self.assertEqual(len(self.fetch.calls), 5)

    def test_sunday_rollover_is_partial_then_combines_cached_weeks(self):
        self.service.refresh_if_due(instant('2026-10-24T10:00:00Z'))
        sunday_early = self.service.refresh_if_due(instant('2026-10-24T17:00:00Z'))
        self.assertEqual(sunday_early['status'], 'partial')
        self.assertFalse(sunday_early['coverage']['thaiDayFullyCovered'])
        self.assertEqual(sunday_early['nextAttemptAt'], '2026-10-24T17:30:00Z')
        self.fetch.payload = exports([row(dt='2026-10-26T08:30:00-04:00')])
        sunday_late = self.service.refresh_if_due(instant('2026-10-25T04:01:00Z'))
        self.assertEqual(sunday_late['coverage']['cachedWeekCount'], 2)
        self.assertTrue(sunday_late['coverage']['thaiDayFullyCovered'])
        self.assertEqual(sunday_late['status'], 'empty')

    def test_first_start_after_week_rollover_reports_missing_prior_hours(self):
        self.fetch.payload = exports([row(dt='2026-10-26T08:30:00-04:00')])
        result = self.service.refresh_if_due(instant('2026-10-25T05:00:00Z'))
        self.assertFalse(result['coverage']['thaiDayFullyCovered'])
        self.assertEqual(result['status'], 'partial')

    def test_changed_uid_time_replaces_same_occurrence(self):
        self.service.refresh_if_due(instant('2026-10-23T10:00:00Z'))
        self.fetch.payload = exports([row(dt='2026-10-23T19:30:00-04:00')])
        result = self.service.refresh_if_due(instant('2026-10-23T17:00:00Z'))
        self.assertEqual(len(result['calendarEvents']), 1)
        self.assertEqual(len(result['events']), 1)
        self.assertEqual(result['events'][0]['timeLabel'], '06:30')

    def test_no_silent_provider_switch(self):
        with self.assertRaises(ValueError):
            news.NewsService(self.folder.name, provider='financecalendar')

    def test_old_parser_cache_reparses_saved_raw_without_refetch_or_new_timestamp(self):
        original = self.service.refresh_if_due(instant('2026-10-23T10:00:00Z'))
        old = json.loads(self.service.cache_path.read_text(encoding='utf-8'))
        old['version'] = news.CACHE_VERSION - 1
        old['weeks']['2026-10-18']['events'][0]['time'] = None
        self.service.cache_path.write_text(json.dumps(old), encoding='utf-8')
        restarted = news.NewsService(self.folder.name, fetcher=self.fetch)
        result = restarted.refresh_if_due(instant('2026-10-23T11:00:00Z'))
        self.assertEqual(len(self.fetch.calls), 3)
        self.assertEqual(result['events'][0]['time'], original['events'][0]['time'])
        self.assertEqual(result['lastSuccessAt'], original['lastSuccessAt'])
        self.assertNotIn('rawExportsB64', json.dumps(result))

    def test_legacy_normalized_only_cache_keeps_last_good_rows_as_stale_across_restarts(self):
        original = self.service.refresh_if_due(instant('2026-10-23T10:00:00Z'))
        old = json.loads(self.service.cache_path.read_text(encoding='utf-8'))
        old['version'] = 1
        old['weeks']['2026-10-18'].pop('rawExportsB64')
        self.service.cache_path.write_text(json.dumps(old), encoding='utf-8')
        for _ in range(2):
            restarted = news.NewsService(self.folder.name, fetcher=self.fetch)
            result = restarted.refresh_if_due(instant('2026-10-23T11:00:00Z'))
            self.assertEqual(result['status'], 'stale')
            self.assertTrue(result['migrationPending'])
            self.assertEqual(result['events'], original['events'])
            self.assertEqual(result['lastSuccessAt'], original['lastSuccessAt'])
        self.assertEqual(len(self.fetch.calls), 3)

    def test_429_preserves_cache_and_waits_at_least_30_minutes_across_restart(self):
        self.service.refresh_if_due(instant('2026-10-23T10:00:00Z'))
        calls = []

        def limited(url):
            calls.append(url)
            raise news.NewsSourceError('http_429')

        self.service.fetcher = limited
        result = self.service.refresh_if_due(instant('2026-10-23T17:00:00Z'))
        self.assertEqual(result['status'], 'stale')
        self.assertEqual(len(result['calendarEvents']), 1)
        self.assertEqual(result['nextAttemptAt'], '2026-10-23T17:30:00Z')
        restarted = news.NewsService(self.folder.name, fetcher=limited)
        restarted.refresh_if_due(instant('2026-10-23T17:29:59Z'))
        self.assertEqual(len(calls), 1)

    def test_429_retry_after_seconds_and_http_date_are_honored(self):
        now = instant('2026-10-23T17:00:00Z')
        for header, expected in [('3600', 3600), ('Fri, 23 Oct 2026 19:00:00 GMT', 7200), ('10', 1800), ('invalid', 1800)]:
            error = news.NewsSourceError('http_429', retry_after=header)
            self.assertEqual(news.failure_delay(error, now, 1), expected)

    def test_http_transport_carries_retry_after_without_network(self):
        error = news.urllib.error.HTTPError(news.URLS['json'], 429, 'test', {'Retry-After': '7200'}, None)
        with patch.object(news.urllib.request, 'urlopen', side_effect=error):
            with self.assertRaises(news.NewsSourceError) as caught:
                news.fetch_public_export(news.URLS['json'])
        self.assertEqual(str(caught.exception), 'http_429')
        self.assertEqual(caught.exception.retry_after, '7200')

    def test_metadata_429_stops_before_next_export_and_keeps_last_good(self):
        original = self.service.refresh_if_due(instant('2026-10-23T10:00:00Z'))
        calls = []

        def limited_ics(url):
            calls.append(url)
            if url.endswith('.ics'):
                raise news.NewsSourceError('http_429', retry_after='3600')
            return self.fetch.payload['json']

        self.service.fetcher = limited_ics
        result = self.service.refresh_if_due(instant('2026-10-23T17:00:00Z'))
        self.assertEqual(calls, [news.URLS['json'], news.URLS['ics']])
        self.assertEqual(result['calendarEvents'], original['calendarEvents'])
        self.assertEqual(result['nextAttemptAt'], '2026-10-23T18:00:00Z')

    def test_recovery_uses_original_bytes_and_timestamp_preserves_429_and_no_network(self):
        self.service._state.update(error='http_429', failures=2, lastAttemptAt='2026-10-23T17:00:00Z', nextAttemptAt='2026-10-23T17:02:00Z')
        self.service._save()
        restarted = news.NewsService(self.folder.name, fetcher=self.fetch)
        restored = restarted.recover_cached_exports(self.fetch.payload, fetched_at=instant('2026-10-23T10:00:00Z'), now=instant('2026-10-23T17:05:00Z'))
        self.assertEqual(self.fetch.calls, [])
        self.assertEqual(restored['status'], 'stale')
        self.assertEqual(restored['error'], 'http_429')
        self.assertEqual(restored['lastSuccessAt'], '2026-10-23T10:00:00Z')
        self.assertEqual(restored['nextAttemptAt'], '2026-10-23T17:30:00Z')
        self.assertEqual(len(restored['calendarEvents']), 1)
        after_restart = news.NewsService(self.folder.name, fetcher=self.fetch)
        result = after_restart.refresh_if_due(instant('2026-10-23T17:29:00Z'))
        self.assertEqual(self.fetch.calls, [])
        self.assertEqual(result['calendarEvents'], restored['calendarEvents'])
        self.assertEqual(result['lastSuccessAt'], restored['lastSuccessAt'])
        self.assertTrue(result['recoveredFromSavedExport'])

    def test_rescheduled_uid_across_weeks_does_not_leave_old_day_occurrence(self):
        self.service.refresh_if_due(instant('2026-10-23T10:00:00Z'))
        self.fetch.payload = exports([row(dt='2026-10-26T08:30:00-04:00')])
        self.service.refresh_if_due(instant('2026-10-25T05:00:00Z'))
        prior_day = self.service.snapshot(instant('2026-10-23T10:00:00Z'))
        self.assertEqual(prior_day['events'], [])
        self.assertEqual(len(prior_day['calendarEvents']), 1)
        self.assertEqual(prior_day['calendarEvents'][0]['dayThai'], '2026-10-26')


if __name__ == '__main__':
    unittest.main()
