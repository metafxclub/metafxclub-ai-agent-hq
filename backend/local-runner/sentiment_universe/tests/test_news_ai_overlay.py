"""Offline artifact projection; no AI, providers, credentials or terminal calls."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from live_backend import news_ai_overlay as target
from live_backend.public_snapshot import public_snapshot
from live_backend.server import MarketService


NOW = datetime(2026, 10, 27, 14, 0, tzinfo=timezone.utc)


def fixture_news(count=3):
    events = [{'id': f'ff-fixture-{index}', 'dayThai': '2026-10-27', 'currency': 'USD' if index % 3 == 0 else 'EUR',
               'title': 'ข่าวเศรษฐกิจ', 'originalTitle': 'Services PMI', 'time': '2026-10-27T13:30:00Z',
               'timeKind': 'timed', 'forecast': None if index % 3 == 2 else '-0.2%', 'previous': '0.1%',
               'sourceUrl': 'https://www.forexfactory.com/calendar', 'mock': False} for index in range(count)]
    yesterday = {**events[0], 'id': 'ff-yesterday', 'dayThai': '2026-10-26', 'ai': {'status': 'ready', 'summaryTh': 'STALE_PRIVATE'}} if events else None
    return {'status': 'ready', 'dayThai': '2026-10-27', 'timeZone': 'Asia/Bangkok', 'mock': False,
            'lastSuccessAt': '2026-10-26T17:01:00Z', 'events': events,
            'calendarEvents': [*copy.deepcopy(events), *([yesterday] if yesterday else [])]}


def fixture_result(assignment):
    def cases():
        return {key: {'direction': 'mixed', 'textTh': 'อาจส่งผลต่อความคาดหวัง ต้องพิจารณาปัจจัยอื่น'} for key in ('below', 'inline', 'above')}
    return {'schemaVersion': 1, 'dayThai': assignment['dayThai'], 'inputDigest': assignment['inputDigest'],
            'events': [{'eventId': row['eventId'], 'summaryTh': 'สรุปข่าวตามปฏิทิน', 'explanationTh': ['เป็นข้อมูลที่สะท้อนกิจกรรมทางเศรษฐกิจ'],
                        'scenarios': {'currency': cases() if row['numeric'] else None,
                                      'XAUUSD': cases() if row['numeric'] and row['currency'] == 'USD' else None,
                                      'XAGUSD': cases() if row['numeric'] and row['currency'] == 'USD' else None},
                        'horizonNotesTh': {key: 'ขึ้นกับความคาดหวังและปัจจัยร่วม' for key in ('short', 'medium', 'long')},
                        'caveatTh': 'เป็นฉากทัศน์ ไม่ใช่คำสั่งซื้อขาย', 'sourceIds': row['sourceIds']} for row in assignment['events']]}


class NewsAIOverlayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / 'artifacts'
        self.directory.mkdir()
        self.news = fixture_news()
        self.rules = target.contract()
        self.assignment = self.rules.build_assignment(self.news, '2026-10-27')
        self.saved = {'schemaVersion': 1, 'dayThai': '2026-10-27', 'inputDigest': self.assignment['inputDigest'],
                      'missionId': 'mission-fixture-news', 'generatedAt': '2026-10-27T01:00:00Z',
                      'assignment': self.assignment, 'result': fixture_result(self.assignment)}
        self.addCleanup(patch.stopall)
        patch('socket.socket.connect', side_effect=AssertionError('No network in overlay')).start()
        patch('subprocess.Popen', side_effect=AssertionError('No execution in overlay')).start()
        patch('live_backend.secure_store.SecretStore._read', side_effect=AssertionError('No credentials in overlay')).start()

    def save(self, saved=None):
        (self.directory / 'result.json').write_text(json.dumps(self.saved if saved is None else saved), encoding='utf-8')

    def project(self, news=None, now=NOW):
        return target.overlay_news(self.news if news is None else news, self.directory, now=now)

    def assert_not_ready(self, projected):
        self.assertNotEqual(projected['aiAnalysis']['status'], 'ready')
        self.assertTrue(all('ai' not in row for key in ('events', 'calendarEvents') for row in projected.get(key, [])))

    def test_ready_batch_covers_all_today_events_metals_and_clears_prior_day_analysis(self):
        self.save()
        before = copy.deepcopy(self.news)
        projected = self.project()
        self.assertEqual(projected['aiAnalysis']['status'], 'ready')
        self.assertEqual(projected['aiAnalysis']['eventCount'], 3)
        self.assertEqual(projected['aiAnalysis']['inputDigest'], self.assignment['inputDigest'])
        self.assertEqual(projected['aiAnalysis']['generatedAt'], self.saved['generatedAt'])
        for event in projected['events']:
            self.assertEqual(event['ai']['eventId'], event['id'])
            self.assertEqual(event['ai']['dayThai'], event['dayThai'])
            self.assertEqual(event['ai']['inputDigest'], projected['aiAnalysis']['inputDigest'])
            for metal in ('XAUUSD', 'XAGUSD'):
                self.assertEqual(event['ai']['scenarios'][metal] is not None, event['currency'] == 'USD' and event['forecast'] is not None)
        self.assertNotIn('ai', projected['calendarEvents'][-1])
        self.assertEqual(self.news, before)

    def test_absent_result_clears_previous_ai_in_both_event_lists(self):
        self.news['events'][0]['ai'] = {'status': 'ready', 'summaryTh': 'OLD_PRIVATE'}
        projected = self.project()
        self.assert_not_ready(projected)
        self.assertEqual(projected['aiAnalysis']['status'], 'pending')
        self.assertNotIn('OLD_PRIVATE', json.dumps(projected))
        self.assertNotIn('STALE_PRIVATE', json.dumps(projected))

    def test_state_is_only_safe_status_and_cannot_mark_missing_result_ready(self):
        for status in ('pending', 'queued', 'running', 'failed', 'blocked', 'interrupted', 'ready'):
            with self.subTest(status=status):
                state = {'schemaVersion': 1, 'dayThai': '2026-10-27', 'status': status, 'reason': 'quota_unavailable',
                         'missionId': 'mission-fixture-news', 'attempted': True, 'updatedAt': NOW.isoformat(),
                         'inputDigest': self.assignment['inputDigest'], 'private': 'PRIVATE_CANARY'}
                (self.directory / 'state.json').write_text(json.dumps(state), encoding='utf-8')
                projected = self.project()
                self.assert_not_ready(projected)
                self.assertEqual(projected['aiAnalysis']['status'], 'pending' if status == 'ready' else status)
                self.assertNotIn('PRIVATE_CANARY', json.dumps(projected))
        state.update(reason='PRIVATE PATH / SECRET', missionId='invalid / PRIVATE', updatedAt='PRIVATE')
        (self.directory / 'state.json').write_text(json.dumps(state), encoding='utf-8')
        self.assertNotIn('PRIVATE', json.dumps(self.project()))

    def test_valid_result_is_authoritative_during_result_before_state_ready_window(self):
        self.save()
        (self.directory / 'state.json').write_text(json.dumps({'schemaVersion': 1, 'dayThai': '2026-10-27', 'status': 'running',
            'missionId': self.saved['missionId'], 'inputDigest': self.saved['inputDigest']}), encoding='utf-8')
        self.assertEqual(self.project()['aiAnalysis']['status'], 'ready')

    def test_malformed_status_value_cannot_break_snapshot_when_result_is_missing(self):
        for status in ([], {}, 1, True, None):
            with self.subTest(status=status):
                (self.directory / 'state.json').write_text(json.dumps({'schemaVersion': 1,
                    'dayThai': '2026-10-27', 'status': status}), encoding='utf-8')
                projected = self.project()
                self.assert_not_ready(projected)
                self.assertEqual(projected['aiAnalysis']['status'], 'pending')

    def test_today_queued_state_is_visible_while_yesterday_artifact_remains(self):
        self.save({**self.saved, 'dayThai': '2026-10-26'})
        (self.directory / 'state.json').write_text(json.dumps({'schemaVersion': 1, 'dayThai': '2026-10-27', 'status': 'queued',
            'missionId': 'mission-today', 'inputDigest': self.assignment['inputDigest']}), encoding='utf-8')
        projected = self.project()
        self.assert_not_ready(projected)
        self.assertEqual(projected['aiAnalysis']['status'], 'queued')
        self.assertEqual(projected['aiAnalysis']['missionId'], 'mission-today')

    def test_prior_day_and_changed_calendar_digest_never_show_ready(self):
        self.save()
        self.assert_not_ready(self.project(now=datetime(2026, 10, 27, 17, 1, tzinfo=timezone.utc)))
        saved = copy.deepcopy(self.saved)
        saved['dayThai'] = '2026-10-26'
        self.save(saved)
        self.assertEqual(self.project()['aiAnalysis']['reason'], 'day_expired')
        self.save()
        for field, value in (('forecast', '1.5%'), ('title', 'Changed event'), ('time', '2026-10-27T12:00:00Z')):
            changed = copy.deepcopy(self.news)
            for key in ('events', 'calendarEvents'):
                changed[key][0][field] = value
            self.assertEqual(self.project(changed)['aiAnalysis']['reason'], 'calendar_changed')
        changed = copy.deepcopy(self.news)
        changed['lastSuccessAt'] = '2026-10-27T00:00:00Z'
        self.assert_not_ready(self.project(changed))

    def test_calendar_event_with_same_id_but_different_input_cannot_inherit_analysis(self):
        self.save()
        changed = copy.deepcopy(self.news)
        changed['calendarEvents'][0]['forecast'] = '5%'
        self.assertEqual(self.project(changed)['aiAnalysis']['reason'], 'calendar_changed')

    def test_missing_duplicate_and_foreign_result_events_reject_entire_batch(self):
        for mutation in (lambda r:r['events'].pop(),
                         lambda r:r['events'].append(copy.deepcopy(r['events'][0])),
                         lambda r:r['events'][0].update(eventId='ff-foreign')):
            saved = copy.deepcopy(self.saved)
            mutation(saved['result'])
            self.save(saved)
            self.assert_not_ready(self.project())

    def test_foreign_fields_and_invented_sources_never_enter_public_artifact(self):
        for mutate in (lambda s:s.update(private='PRIVATE_CANARY'),
                       lambda s:s['result']['events'][0].update(actual='PRIVATE_CANARY'),
                       lambda s:s['result']['events'][0].update(sourceIds=['official-foreign']),
                       lambda s:s['assignment']['sourceRefs'][0].update(url='https://evil.invalid/')):
            saved = copy.deepcopy(self.saved)
            mutate(saved)
            self.save(saved)
            projected = self.project()
            self.assert_not_ready(projected)
            self.assertNotIn('PRIVATE_CANARY', json.dumps(projected))
            self.assertNotIn('evil.invalid', json.dumps(projected))

    def test_invalid_versions_timestamps_and_state_identity_fail_closed(self):
        for mutation in (lambda s:s.update(schemaVersion=True), lambda s:s.update(generatedAt='not-a-time'),
                         lambda s:s.update(generatedAt='2026-10-27T16:00:00Z'), lambda s:s.update(missionId='../private')):
            saved = copy.deepcopy(self.saved)
            mutation(saved)
            self.save(saved)
            self.assert_not_ready(self.project())
        self.save()
        for changed in ({'missionId': 'mission-new'}, {'inputDigest': 'f' * 64}):
            state = {'schemaVersion': 1, 'dayThai': '2026-10-27', **changed}
            (self.directory / 'state.json').write_text(json.dumps(state), encoding='utf-8')
            self.assertEqual(self.project()['aiAnalysis']['reason'], 'calendar_changed')

    def test_partial_duplicate_nonfinite_and_oversized_json_are_not_accepted(self):
        for raw in ('{"schemaVersion":', '{"schemaVersion":1,"schemaVersion":1}', '{"x":NaN}'):
            (self.directory / 'result.json').write_text(raw, encoding='utf-8')
            self.assert_not_ready(self.project())
        self.save()
        with patch.object(target, 'MAX_ARTIFACT_BYTES', 100), patch.object(Path, 'open', side_effect=AssertionError('Oversized file must be rejected before read')):
            self.assert_not_ready(self.project())

    def test_atomic_replacement_during_read_is_rejected_then_recovers_next_cycle(self):
        self.save()
        with patch.object(target, '_identity', side_effect=[(1, 1, 10, 1), (1, 2, 10, 2)]):
            self.assert_not_ready(self.project())
        self.assertEqual(self.project()['aiAnalysis']['status'], 'ready')

    def test_complete_large_day_is_not_silently_truncated(self):
        news = fixture_news(45)
        assignment = self.rules.build_assignment(news, '2026-10-27')
        saved = {**self.saved, 'assignment': assignment, 'inputDigest': assignment['inputDigest'], 'result': fixture_result(assignment)}
        self.save(saved)
        projected = self.project(news)
        self.assertEqual(projected['aiAnalysis']['eventCount'], 45)
        self.assertEqual(sum('ai' in row for row in projected['events']), 45)

    def test_empty_day_never_needs_an_artifact_or_claims_ready(self):
        projected = self.project(fixture_news(0))
        self.assertEqual(projected['aiAnalysis']['status'], 'empty')
        self.assertEqual(projected['aiAnalysis']['reason'], 'empty_day')

    def test_public_snapshot_projects_only_known_nested_ai_fields(self):
        self.save()
        projected = self.project()
        analysis = projected['events'][0]['ai']
        analysis['private'] = 'PRIVATE_CANARY'
        analysis['scenarios']['currency']['below']['private'] = 'PRIVATE_CANARY'
        analysis['scenarios']['unapprovedAsset'] = 'PRIVATE_CANARY'
        analysis['sourceRefs'][0]['secret'] = 'PRIVATE_CANARY'
        projected['aiAnalysis']['private'] = 'PRIVATE_CANARY'
        public = public_snapshot({'news': projected}, NOW.isoformat())['news']
        self.assertNotIn('PRIVATE_CANARY', json.dumps(public))
        self.assertEqual(public['aiAnalysis']['inputDigest'], self.assignment['inputDigest'])
        self.assertEqual(public['events'][0]['ai']['scenarios']['XAUUSD'], projected['events'][0]['ai']['scenarios']['XAUUSD'])

    def test_market_read_and_mirror_pick_up_result_without_calendar_refetch(self):
        mirror = Path(self.temp.name) / 'public' / 'market.json'
        market = MarketService(Path(self.temp.name) / 'market-private', mirror, news_ai_dir=self.directory)
        with patch('live_backend.news_ai_overlay.datetime', wraps=datetime) as clock:
            clock.now.return_value = NOW
            market.update('news', copy.deepcopy(self.news))
            original_generated_at = market.snapshot['generatedAt']
            self.assertEqual(market.read()['news']['aiAnalysis']['status'], 'pending')
            self.save()
            market.publish_mirror()
            published = json.loads(mirror.read_text(encoding='utf-8'))
            self.assertEqual(published['news']['aiAnalysis']['status'], 'ready')
            self.assertEqual(market.read()['news']['aiAnalysis']['status'], 'ready')
            self.assertEqual(market.snapshot['news'], self.news)
            self.assertEqual(published['generatedAt'], original_generated_at)
            self.assertEqual(published['news']['lastSuccessAt'], self.news['lastSuccessAt'])
            (self.directory / 'result.json').unlink()
            market.publish_mirror()
            self.assertNotEqual(json.loads(mirror.read_text(encoding='utf-8'))['news']['aiAnalysis']['status'], 'ready')


if __name__ == '__main__':
    unittest.main()
