"""Loopback HTTP/auth boundaries with temporary data, never real provider calls."""
import http.client
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import threading
import unittest
from unittest.mock import patch

from live_backend import server as target
from live_backend.secure_store import SecretStore


class FakeMarket:
    def __init__(self, private):
        self.secrets = SimpleNamespace(path=private / 'myfxbook.dpapi')
        self.saved = []

    def read(self):
        return {'mode': 'live', 'sentiment': {'status': 'needs_configuration', 'items': []}}

    def save_credentials(self, email, password):
        self.saved.append((email, password))


class HandlerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.public = self.root / 'dist' / 'client'
        self.public.mkdir(parents=True)
        (self.public / 'index.html').write_text('<p>PUBLIC_TEST_PAGE</p>', encoding='utf-8')
        (self.public / 'assets').mkdir()
        (self.public / 'assets' / 'known.js').write_text('const publicAsset = true;', encoding='utf-8')
        (self.root / 'private').mkdir()
        (self.root / 'private' / 'myfxbook.dpapi').write_bytes(b'PRIVATE_TEST_CANARY')
        (self.root / 'state').mkdir()
        (self.root / 'state' / 'snapshot.json').write_text('PRIVATE_STATE_CANARY', encoding='utf-8')
        self.addCleanup(patch.stopall)
        patch.object(target, 'ROOT', self.root).start()
        self.market = FakeMarket(self.root / 'private')
        self.httpd = target.ThreadingHTTPServer(('127.0.0.1', 0), target.DashboardHandler)
        self.httpd.daemon_threads = True
        self.httpd.market = self.market
        self.httpd.csrf = 'test-csrf-only-not-a-real-token'
        self.port = self.httpd.server_port
        self.thread = threading.Thread(target=self.httpd.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)

    def close_server(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(2)

    def request(self, method, path, body=None, headers=None):
        client = http.client.HTTPConnection('127.0.0.1', self.port, timeout=3)
        try:
            client.request(method, path, body=body, headers=headers or {})
            response = client.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            client.close()

    def post(self, body=None, *, headers=None, path='/api/setup/myfxbook'):
        default = {'Origin': f'http://127.0.0.1:{self.port}', 'X-CSRF-Token': self.httpd.csrf,
                   'Content-Type': 'application/json'}
        if headers:
            for key, value in headers.items():
                if value is None:
                    default.pop(key, None)
                else:
                    default[key] = value
        if body is None:
            body = json.dumps({'email': 'test@example.invalid', 'password': 'TEST_PASSWORD_ONLY'})
        return self.request('POST', path, body, default)

    def test_health_and_market_are_public_read_only_and_uncached(self):
        status, headers, raw = self.request('GET', '/api/health')
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(raw)['readOnlyMarketData'])
        self.assertEqual(headers['Cache-Control'], 'no-store')
        status, headers, raw = self.request('GET', '/api/market')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw), self.market.read())
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(self.market.saved, [])
        self.assertNotIn('Access-Control-Allow-Origin', headers)

    def test_host_rebinding_and_wrong_ports_rejected_on_get_head_and_post(self):
        for host in ['attacker.example', f'127.0.0.1:{self.port + 1}', f'127.0.0.1.attacker.example:{self.port}', 'localhost', f'user@127.0.0.1:{self.port}']:
            for method in ('GET', 'HEAD'):
                with self.subTest(host=host, method=method):
                    self.assertEqual(self.request(method, '/api/health', headers={'Host': host})[0], 403)
            self.assertEqual(self.post(headers={'Host': host})[0], 403)
        self.assertEqual(self.market.saved, [])

    def test_localhost_host_alias_is_supported(self):
        self.assertEqual(self.request('GET', '/api/health', headers={'Host': f'localhost:{self.port}'})[0], 200)

    def test_origin_is_required_and_must_match_loopback_port(self):
        for origin in [None, 'null', 'https://attacker.example', f'https://127.0.0.1:{self.port}', f'http://127.0.0.1:{self.port + 1}', f'http://localhost:{self.port}/']:
            with self.subTest(origin=origin):
                status, _, raw = self.post(headers={'Origin': origin})
                self.assertEqual(status, 403)
                self.assertEqual(json.loads(raw)['error'], 'request_rejected')
        self.assertEqual(self.market.saved, [])

    def test_csrf_missing_empty_wrong_are_rejected_without_saving(self):
        for token in [None, '', 'wrong', self.httpd.csrf + '-suffix', 'invalid-\u00e1-token']:
            self.assertEqual(self.post(headers={'X-CSRF-Token': token})[0], 403)
        self.assertEqual(self.market.saved, [])

    def test_valid_setup_returns_status_without_echoing_test_secret(self):
        status, _, raw = self.request('GET', '/api/setup')
        setup = json.loads(raw)
        self.assertEqual(status, 200)
        self.assertEqual(setup['csrf'], self.httpd.csrf)
        self.assertTrue(setup['encryptedCredentialsPresent'])
        status, headers, raw = self.post(headers={'Origin': f'http://localhost:{self.port}'})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(raw)['saved'])
        self.assertEqual(self.market.saved, [('test@example.invalid', 'TEST_PASSWORD_ONLY')])
        self.assertNotIn(b'TEST_PASSWORD_ONLY', raw)
        self.assertNotIn(b'test@example.invalid', raw)
        self.assertEqual(headers['Cache-Control'], 'no-store')

    def test_invalid_json_body_types_and_credential_types_are_rejected(self):
        bodies = [b'{', b'\xff', 'null', '[]', '"text"', '23', 'true',
                  json.dumps({'email': 5, 'password': 'test'}),
                  json.dumps({'email': ['a@b'], 'password': 'test'}),
                  json.dumps({'email': 'a@b', 'password': []}),
                  json.dumps({'email': 'missing-at', 'password': 'test'}),
                  json.dumps({'email': 'a@b', 'password': ''}),
                  json.dumps({'email': 'a@b', 'password': 'p' * 2049}),
                  json.dumps({'email': 'x' * 253 + '@b', 'password': 'test'})]
        for body in bodies:
            with self.subTest(body_type=type(body).__name__, size=len(body)):
                self.assertEqual(self.post(body)[0], 400)
        self.assertEqual(self.market.saved, [])

    def test_large_empty_and_invalid_content_lengths_are_rejected(self):
        for length in ('0', '-1', '8193', 'not-a-number'):
            with self.subTest(length=length):
                self.assertEqual(self.post('', headers={'Content-Length': length})[0], 400)
        self.assertEqual(self.post('x' * 8193)[0], 400)
        self.assertEqual(self.market.saved, [])

    def test_exact_body_size_limit_accepts_valid_json(self):
        body = json.dumps({'email': 'test@example.invalid', 'password': 'TEST_BOUNDARY_ONLY'})
        body += ' ' * (8192 - len(body.encode('utf-8')))
        self.assertEqual(len(body.encode('utf-8')), 8192)
        self.assertEqual(self.post(body)[0], 200)
        self.assertEqual(len(self.market.saved), 1)

    def test_unknown_api_and_post_routes_do_not_fall_back_to_static(self):
        self.assertEqual(self.request('GET', '/api/private')[0], 404)
        self.assertEqual(self.post(path='/api/trade')[0], 404)
        self.assertEqual(self.post(path='/')[0], 404)
        self.assertEqual(self.market.saved, [])

    def test_static_pages_have_security_headers_and_no_directory_listing(self):
        status, headers, raw = self.request('GET', '/')
        self.assertEqual(status, 200)
        self.assertIn(b'PUBLIC_TEST_PAGE', raw)
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(headers['X-Frame-Options'], 'DENY')
        self.assertEqual(headers['Referrer-Policy'], 'no-referrer')
        self.assertIn("connect-src 'self'", headers['Content-Security-Policy'])
        status, _, raw = self.request('GET', '/assets/')
        self.assertEqual(status, 404)
        self.assertNotIn(b'known.js', raw)

    def test_private_state_sources_and_encoded_traversal_are_not_exposed(self):
        routes = ['/private/myfxbook.dpapi', '/state/snapshot.json', '/live_backend/secure_store.py',
                  '/../../private/myfxbook.dpapi', '/%2e%2e/%2e%2e/private/myfxbook.dpapi',
                  '/..%5c..%5cprivate%5cmyfxbook.dpapi', '/%2f..%2f..%2fprivate/myfxbook.dpapi',
                  '/api/../private/myfxbook.dpapi']
        for route in routes:
            with self.subTest(route=route):
                status, _, raw = self.request('GET', route)
                self.assertEqual(status, 404)
                self.assertNotIn(b'PRIVATE_TEST_CANARY', raw)
                self.assertNotIn(b'PRIVATE_STATE_CANARY', raw)

    def test_symlink_escape_is_rejected_when_os_supports_symlinks(self):
        try:
            os.symlink(self.root / 'private' / 'myfxbook.dpapi', self.public / 'escape.bin')
        except (OSError, NotImplementedError):
            self.skipTest('This Windows account cannot create symlinks')
        status, _, raw = self.request('GET', '/escape.bin')
        self.assertEqual(status, 404)
        self.assertNotIn(b'PRIVATE_TEST_CANARY', raw)


@unittest.skipUnless(os.name == 'nt', 'Windows DPAPI contract')
class DpapiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = SecretStore(Path(self.temp.name) / 'private')

    def test_real_dpapi_roundtrip_and_reopen_do_not_persist_plaintext(self):
        self.assertIsNone(self.store.credentials())
        email, password = 'dpapi-test@example.invalid', 'TEST_ONLY_รหัส_7391'
        session = {'session': 'TEST_SESSION_ONLY_5299', 'createdAt': 123}
        self.store.save_credentials(email, password)
        self.store.save_session(session)
        encrypted = self.store.path.read_bytes()
        for marker in (email, password, session['session'], 'credentials'):
            self.assertNotIn(marker.encode('utf-8'), encrypted)
        reopened = SecretStore(self.store.path.parent)
        self.assertEqual(reopened.credentials(), {'email': email, 'password': password})
        self.assertEqual(reopened.session(), session)
        self.assertFalse(self.store.path.with_suffix('.tmp').exists())

    def test_credential_replacement_and_session_clear_preserve_only_current_auth(self):
        self.store.save_credentials('old@example.invalid', 'TEST_OLD')
        self.store.save_session({'session': 'TEST_OLD_SESSION'})
        self.store.save_credentials('new@example.invalid', 'TEST_NEW')
        self.assertIsNone(self.store.session())
        self.assertEqual(self.store.credentials()['email'], 'new@example.invalid')
        self.store.save_session({'session': 'TEST_NEW_SESSION'})
        self.store.clear_session()
        self.assertIsNone(self.store.session())
        self.assertEqual(self.store.credentials()['password'], 'TEST_NEW')

    def test_invalid_ciphertext_fails_closed(self):
        self.store.path.parent.mkdir(parents=True)
        self.store.path.write_bytes(b'INVALID_TEST_CIPHERTEXT')
        with self.assertRaises(RuntimeError):
            self.store.credentials()


class ServiceConcurrencyTests(unittest.TestCase):
    def test_credential_replacement_waits_for_inflight_collector_then_invalidates_session(self):
        with tempfile.TemporaryDirectory() as temporary:
            market = target.MarketService(temporary)  # Constructor only; never start workers.
            entered, release, replacing, replaced = (threading.Event() for _ in range(4))
            sequence, errors = [], []

            class FakeSecrets:
                credentials_value = {'email': 'old@example.invalid', 'password': 'TEST_OLD'}
                session_value = None

                def save_credentials(self, email, password):
                    sequence.append('credentials_saved')
                    self.credentials_value = {'email': email, 'password': password}
                    self.session_value = None

            store = FakeSecrets()
            market.secrets = store

            class FakeProvider:
                def collect(self):
                    sequence.append('collect_started')
                    captured_email = store.credentials_value['email']
                    entered.set()
                    if not release.wait(3):
                        raise AssertionError('Test release was not signalled')
                    store.session_value = 'TEST_OLD_SESSION'
                    sequence.append('collect_finished')
                    return {'status': 'ready', 'capturedEmail': captured_email}

                def credentials_changed(self):
                    sequence.append('credentials_changed')

            market.sentiment_provider = FakeProvider()

            def collect():
                try:
                    market.collect_sentiment()
                except Exception as error:
                    errors.append(error)

            def replace():
                replacing.set()
                try:
                    market.save_credentials('new@example.invalid', 'TEST_NEW')
                except Exception as error:
                    errors.append(error)
                finally:
                    replaced.set()

            collector = threading.Thread(target=collect)
            writer = threading.Thread(target=replace)
            collector.start()
            try:
                self.assertTrue(entered.wait(2))
                writer.start()
                self.assertTrue(replacing.wait(2))
                self.assertFalse(replaced.wait(0.08), 'Credential replacement bypassed the in-flight auth lock')
                self.assertEqual(store.credentials_value['email'], 'old@example.invalid')
            finally:
                release.set()
                collector.join(3)
                if writer.ident is not None:
                    writer.join(3)
            self.assertFalse(collector.is_alive())
            self.assertFalse(writer.is_alive())
            self.assertEqual(errors, [])
            self.assertEqual(sequence, ['collect_started', 'collect_finished', 'credentials_saved', 'credentials_changed'])
            self.assertIsNone(store.session_value)
            self.assertEqual(store.credentials_value['email'], 'new@example.invalid')
            self.assertTrue(market.wake_sentiment.is_set())

    def test_public_snapshot_is_deep_copy_and_worker_errors_do_not_expose_exception(self):
        with tempfile.TemporaryDirectory() as temporary:
            market = target.MarketService(temporary)
            copied = market.read()
            copied['sentiment']['status'] = 'tampered'
            self.assertEqual(market.read()['sentiment']['status'], 'loading')

            def failing_action():
                market.stop.set()
                raise RuntimeError('TEST_SECRET_IN_PROVIDER_URL?password=TEST_PRIVATE')

            market.worker('sentiment', failing_action, 0)
            stored = (Path(temporary) / 'snapshot.json').read_text(encoding='utf-8')
            self.assertNotIn('TEST_SECRET', stored)
            self.assertNotIn('TEST_PRIVATE', stored)
            self.assertEqual(market.read()['sentiment']['errorCode'], 'collector_failed')


if __name__ == '__main__':
    unittest.main()
