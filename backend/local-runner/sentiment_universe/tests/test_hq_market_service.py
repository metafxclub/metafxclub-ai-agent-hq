"""HQ integration boundaries. Temporary state and fake providers only."""
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from live_backend.public_snapshot import public_snapshot
from live_backend.server import MarketService
from tests.test_live_server import HandlerTests


class MirrorTests(unittest.TestCase):
    def test_allowlisted_public_mirror_omits_config_and_unknown_nested_fields(self):
        raw = {'generatedAt':'2026-10-24T10:00:00Z', 'config':{'password':'PRIVATE'},
               'sentiment':{'status':'ready','session':'PRIVATE','items':[{'symbol':'EURUSD','long':80,'short':20,'available':True,'password':'PRIVATE','positions':{'long':2,'short':1,'total':3,'account':'PRIVATE'}}]},
               'correlations':{'status':'partial','terminalPath':'PRIVATE','items':[{'source':'EURUSD','target':'GBPUSD','value':.8,'status':'ready','dataPath':'PRIVATE'}]},
               'news':{'status':'ready','rawExportsB64':'PRIVATE','events':[{'id':'event1','time':'2026-10-24T10:00:00Z','title':'PMI','account':'PRIVATE'}], 'coverage':{'dayCount':1,'raw':'PRIVATE'}}}
        output = public_snapshot(raw, '2026-10-24T10:00:30Z')
        self.assertNotIn('PRIVATE', json.dumps(output))
        self.assertEqual(output['sentiment']['items'][0]['long'], 80)
        self.assertEqual(output['correlations']['items'][0]['value'], .8)
        self.assertEqual(output['generatedAt'], raw['generatedAt'])
        self.assertEqual(output['mirror']['publishedAt'], '2026-10-24T10:00:30Z')

    def test_heartbeat_does_not_change_provider_freshness_or_source_generated_at(self):
        with tempfile.TemporaryDirectory() as folder:
            mirror = Path(folder)/'public'/'market.json'
            market = MarketService(Path(folder)/'private', mirror)
            market.update('sentiment', {'status':'ready','lastSuccessAt':'2026-10-24T09:00:00Z','items':[]})
            before = market.read()
            with patch('live_backend.server.utc_now', return_value='2026-10-24T10:01:00Z'):
                market.publish_mirror()
            output = json.loads(mirror.read_text('utf-8'))
            self.assertEqual(output['sentiment']['lastSuccessAt'], before['sentiment']['lastSuccessAt'])
            self.assertEqual(output['generatedAt'], before['generatedAt'])
            self.assertEqual(output['mirror']['publishedAt'], '2026-10-24T10:01:00Z')
            self.assertEqual(list(mirror.parent.glob('*.tmp')), [])

    def test_failed_mirror_write_retains_last_complete_document(self):
        with tempfile.TemporaryDirectory() as folder:
            mirror = Path(folder)/'public'/'market.json'
            market = MarketService(Path(folder)/'private', mirror)
            market.publish_mirror()
            before = mirror.read_bytes()
            with patch('live_backend.server.atomic_json', side_effect=OSError('TEST_PRIVATE_PATH')):
                market.publish_mirror()
            self.assertTrue(market.mirror_error)
            self.assertEqual(mirror.read_bytes(), before)


class SelectionConcurrencyTests(unittest.TestCase):
    def test_selection_change_discards_inflight_old_terminal_result(self):
        with tempfile.TemporaryDirectory() as folder:
            market = MarketService(folder)
            market.config = {'mt5':{'selectionId':'old'}}
            entered, release = threading.Event(), threading.Event()
            def collect(config, _):
                self.assertEqual(config['selectionId'], 'old')
                entered.set()
                self.assertTrue(release.wait(3))
                return {'status':'ready','source':'OLD_TERMINAL','items':[]}
            with patch('live_backend.correlation.collect_for_service', side_effect=collect):
                worker = threading.Thread(target=market.collect_correlation)
                worker.start()
                try:
                    self.assertTrue(entered.wait(2))
                    with market.lock:
                        market.selection_epoch += 1
                        market.config['mt5'] = {'selectionId':'new'}
                        market.update('correlations', {'status':'loading','source':'MT5','items':[]})
                finally:
                    release.set(); worker.join(3)
            self.assertEqual(market.read()['correlations']['source'], 'MT5')
            self.assertEqual(market.read()['correlations']['status'], 'loading')

    def test_selection_saves_only_own_config_and_preserves_other_provider_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            market = MarketService(folder)
            market.config = {'myfxbook':{'intervalSeconds':1200},'newsProvider':'forexfactory'}
            class Setup:
                def resolve_selection(self, candidate, revision):
                    return {'enabled':True,'selectionId':candidate,'terminalPath':'TEST_PATH','dataPath':'TEST_DATA'}
            market.mt5_setup = Setup()
            market.select_mt5('opaque-test', 'revision-test')
            saved = json.loads((Path(folder)/'config.json').read_text('utf-8'))
            self.assertEqual(saved['myfxbook'], {'intervalSeconds':1200})
            self.assertEqual(saved['newsProvider'], 'forexfactory')
            self.assertEqual(saved['mt5']['selectionId'], 'opaque-test')
            self.assertTrue(market.wake_correlation.is_set())
            self.assertNotIn('TEST_PATH', json.dumps(market.read()))


class SetupHTTPTests(HandlerTests):
    def test_mt5_selection_rejects_injected_paths_and_requires_csrf(self):
        calls = []
        self.market.select_mt5 = lambda candidate, revision: calls.append((candidate, revision)) or {'saved':True}
        valid = json.dumps({'candidateId':'opaque-test','discoveryRevision':'revision-test'})
        endpoint = '/api/setup/mt5/select'
        self.assertEqual(self.post(valid, path=endpoint, headers={'X-CSRF-Token':None})[0], 403)
        extra = json.dumps({'candidateId':'opaque-test','discoveryRevision':'revision-test','terminalPath':'INJECTED'})
        self.assertEqual(self.post(extra, path=endpoint)[0], 400)
        self.assertEqual(calls, [])
        self.assertEqual(self.post(valid, path=endpoint)[0], 200)
        self.assertEqual(calls, [('opaque-test','revision-test')])

    def test_custom_static_root_keeps_private_paths_unservable(self):
        custom = self.root/'hq-public'
        custom.mkdir()
        (custom/'index.html').write_text('CUSTOM_STATIC_PUBLIC', encoding='utf-8')
        self.httpd.static_dir = custom
        self.assertIn(b'CUSTOM_STATIC_PUBLIC', self.request('GET','/')[2])
        self.assertEqual(self.request('GET','/../private/myfxbook.dpapi')[0],404)


if __name__ == '__main__':
    unittest.main()
