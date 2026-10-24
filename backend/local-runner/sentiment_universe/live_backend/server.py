"""Loopback-only dashboard. Worker threads fetch data; HTTP never sends trades."""
import argparse
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import secrets
import threading
import time
from urllib.parse import urlsplit, unquote

from .secure_store import SecretStore
from .public_snapshot import public_snapshot

ROOT = Path(__file__).resolve().parents[1]


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    os.replace(tmp, path)


class MarketService:
    def __init__(self, state_dir, public_mirror=None):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.secrets = SecretStore(self.state_dir / 'private')
        config_path = self.state_dir / 'config.json'
        self.config = json.loads(config_path.read_text('utf-8-sig')) if config_path.exists() else {}
        self.lock = threading.RLock()
        self.auth_lock = threading.RLock()
        self.public_mirror = Path(public_mirror) if public_mirror else None
        self.mirror_error = False
        self.mt5_setup = None
        self.selection_epoch = 0
        self.sentiment_provider = None
        self.stop = threading.Event()
        self.wake_sentiment = threading.Event()
        self.wake_correlation = threading.Event()
        self.snapshot = {'schemaVersion': 1, 'mode': 'live', 'generatedAt': utc_now(),
                         'sentiment': {'status': 'loading', 'source': 'Myfxbook', 'items': []},
                         'correlations': {'status': 'loading', 'source': 'MT5', 'items': []},
                         'news': {'status': 'loading', 'source': 'Forex Factory', 'events': []}}

    def update(self, key, value):
        with self.lock:
            self.snapshot[key] = value
            self.snapshot['generatedAt'] = utc_now()
            # Public market data only: provider responses must never contain auth.
            atomic_json(self.state_dir / 'snapshot.json', self.snapshot)
            self.publish_mirror()

    def publish_mirror(self):
        if self.public_mirror:
            with self.lock:
                try:
                    atomic_json(self.public_mirror, public_snapshot(self.snapshot, utc_now()))
                    self.mirror_error = False
                except (OSError, ValueError, TypeError):
                    # Preserve the last complete mirror. Its heartbeat will expire.
                    self.mirror_error = True

    def heartbeat(self):
        while not self.stop.is_set():
            self.publish_mirror()
            self.stop.wait(30)

    def read(self):
        with self.lock:
            return json.loads(json.dumps(self.snapshot, allow_nan=False))

    def save_credentials(self, email, password):
        # A prior login must finish before replacing its encrypted session.
        with self.auth_lock:
            self.secrets.save_credentials(email, password)
            if self.sentiment_provider:
                self.sentiment_provider.credentials_changed()
        self.wake_sentiment.set()

    def collect_sentiment(self):
        with self.auth_lock:
            return self.sentiment_provider.collect()

    def setup_helper(self):
        from .mt5_setup import MT5Setup
        with self.lock:
            if self.mt5_setup is None:
                self.mt5_setup = MT5Setup(self.state_dir)
            return self.mt5_setup

    def setup_status(self):
        with self.lock:
            config = dict(self.config.get('mt5', {}))
            correlation = dict(self.snapshot['correlations'])
        return {'mt5': self.setup_helper().status(config, correlation),
                'automaticUpdates': True, 'timeZone': 'Asia/Bangkok',
                'publicMirror': 'error' if self.mirror_error else 'enabled' if self.public_mirror else 'not_required'}

    def select_mt5(self, candidate_id, revision):
        selected = self.setup_helper().resolve_selection(candidate_id, revision)
        with self.lock:
            # Replace the dashboard's private binding only. No HQ/council selection.
            config = {**self.config, 'mt5': selected}
            atomic_json(self.state_dir / 'config.json', config)
            self.config = config
            self.selection_epoch += 1
            self.update('correlations', {'status': 'loading', 'source': 'MT5', 'items': [],
                                        'errorCode': 'verifying_selected_terminal'})
        self.wake_correlation.set()
        return {'saved': True, 'state': 'verifying', 'message': 'บันทึก MT5 ของหน้าดาวแล้ว กำลังตรวจข้อมูลและเวลาโบรกเกอร์'}

    def collect_correlation(self):
        from .correlation import collect_for_service
        with self.lock:
            config, epoch = dict(self.config.get('mt5', {})), self.selection_epoch
        try:
            result = collect_for_service(config, self.state_dir)
        except Exception:
            with self.lock:
                if epoch != self.selection_epoch:
                    return None
                result = dict(self.snapshot['correlations'])
                result.update(status='error', errorCode='collector_failed', lastAttemptAt=utc_now())
        with self.lock:
            # A result from the previous terminal must not appear after selection.
            if epoch != self.selection_epoch:
                return None
            self.update('correlations', result)
            return None  # Publication and selection check share the same lock.

    def worker(self, key, action, interval, wake=None):
        while not self.stop.is_set():
            try:
                value = action()
                if value is not None:
                    self.update(key, value)
            except Exception:
                # Exception text can contain provider URLs/credentials. Never log it.
                # Correlation handles failure with its own selection epoch; a
                # generic retry must never re-publish another terminal's data.
                if key == 'correlations':
                    if wake:
                        wake.wait(interval)
                        wake.clear()
                    else:
                        self.stop.wait(interval)
                    continue
                with self.lock:
                    prior = dict(self.snapshot[key])
                    prior.update(status='error', errorCode='collector_failed', lastAttemptAt=utc_now())
                    self.update(key, prior)
            if wake:
                wake.wait(interval)
                wake.clear()
            else:
                self.stop.wait(interval)

    def start(self):
        from .myfxbook import MyfxbookProvider
        from .news import NewsService
        # Upgrade a proven legacy binding before any worker starts. This only
        # rewrites this dashboard's private files, never HQ's terminal selection.
        migration = self.setup_helper().migrate_legacy(self.config)
        if migration.get('migrated'):
            self.config = json.loads((self.state_dir / 'config.json').read_text('utf-8-sig'))
        provider = MyfxbookProvider(self.config.get('myfxbook', {}), self.state_dir / 'myfxbook',
                                    read_credentials=self.secrets.credentials,
                                    read_session=self.secrets.session,
                                    save_session=self.secrets.save_session,
                                    clear_session=self.secrets.clear_session)
        self.sentiment_provider = provider
        news = NewsService(self.state_dir / 'news', provider=self.config.get('newsProvider', 'forexfactory'))
        tasks = [('sentiment', self.collect_sentiment, 60, self.wake_sentiment),
                 ('correlations', self.collect_correlation, 300, self.wake_correlation),
                 ('news', news.refresh_if_due, 60, None)]
        for key, action, interval, wake in tasks:
            threading.Thread(target=self.worker, args=(key, action, interval, wake),
                             daemon=True, name='universe-' + key).start()
        threading.Thread(target=self.heartbeat, daemon=True, name='universe-public-mirror').start()


class DashboardHandler(SimpleHTTPRequestHandler):
    server_version = 'MetafxUniverse/1'

    def __init__(self, request, client_address, server, **kwargs):
        self.public_dir = Path(getattr(server, 'static_dir', ROOT / 'dist' / 'client')).resolve()
        super().__init__(request, client_address, server, directory=str(self.public_dir), **kwargs)

    def log_message(self, fmt, *args):
        pass  # No request bodies, query strings, secrets or remote errors in logs.

    def list_directory(self, path):
        self.send_error(404)
        return None

    def translate_path(self, path):
        resolved = Path(super().translate_path(path)).resolve()
        public = self.public_dir
        if not resolved.is_relative_to(public):
            return str(public / '__not_found__')
        return str(resolved)

    def do_HEAD(self):
        if not self.valid_host():
            self.send_error(403)
            return
        if not self.valid_path():
            self.send_error(404)
            return
        super().do_HEAD()

    def valid_path(self):
        path = unquote(urlsplit(self.path).path)
        return '\\' not in path and '..' not in path.split('/')

    def valid_host(self):
        return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}')

    def send_json(self, value, status=200):
        raw = json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(raw)

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        super().end_headers()

    def do_GET(self):
        if not self.valid_host():
            return self.send_json({'error': 'invalid_host'}, 403)
        if not self.valid_path():
            return self.send_json({'error': 'not_found'}, 404)
        route = urlsplit(self.path).path
        if route == '/api/health':
            return self.send_json({'ok': True, 'service': 'sentiment-universe', 'readOnlyMarketData': True,
                                   'pid': os.getpid(), 'project': str(ROOT.resolve())})
        if route == '/api/market':
            return self.send_json(self.server.market.read())
        if route == '/api/setup':
            return self.send_json({'csrf': self.server.csrf, 'encryptedCredentialsPresent': self.server.market.secrets.path.exists(),
                                   **(self.server.market.setup_status() if hasattr(self.server.market, 'setup_status') else {})})
        if route == '/api/setup/mt5/candidates':
            try:
                return self.send_json(self.server.market.setup_helper().discover())
            except Exception:
                return self.send_json({'error': 'terminal_discovery_failed', 'candidates': []}, 503)
        if route in ('/connect', '/connect.js'):
            name = 'connect.html' if route == '/connect' else 'connect.js'
            raw = (ROOT / 'live_backend' / name).read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8' if name.endswith('html') else 'text/javascript; charset=utf-8')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(raw)
            return
        if route.startswith('/api/'):
            return self.send_json({'error': 'not_found'}, 404)
        super().do_GET()

    def do_POST(self):
        origin = self.headers.get('Origin')
        allowed = {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}
        token = self.headers.get('X-CSRF-Token', '')
        if not self.valid_host() or origin not in allowed or not token.isascii() or not secrets.compare_digest(token, self.server.csrf):
            return self.send_json({'error': 'request_rejected'}, 403)
        route = urlsplit(self.path).path
        if route not in ('/api/setup/myfxbook', '/api/setup/mt5/select'):
            return self.send_json({'error': 'not_found'}, 404)
        try:
            if self.headers.get('Transfer-Encoding') or self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
                return self.send_json({'error': 'invalid_request'}, 400)
            size = int(self.headers.get('Content-Length', '0'))
            if not 1 <= size <= 8192:
                return self.send_json({'error': 'invalid_request'}, 400)
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                return self.send_json({'error': 'invalid_request'}, 400)
            if route == '/api/setup/mt5/select':
                candidate_id, revision = data.get('candidateId'), data.get('discoveryRevision')
                if (set(data) != {'candidateId', 'discoveryRevision'} or not isinstance(candidate_id, str)
                        or not isinstance(revision, str) or not 1 <= len(candidate_id) <= 200 or not 1 <= len(revision) <= 200):
                    return self.send_json({'error': 'invalid_selection'}, 400)
                try:
                    return self.send_json(self.server.market.select_mt5(candidate_id, revision))
                except Exception as error:
                    from .mt5_setup import MT5SetupError
                    code = error.code if isinstance(error, MT5SetupError) else 'selection_not_saved'
                    return self.send_json({'error': code}, 409)
            email, password = data.get('email', ''), data.get('password', '')
            if not isinstance(email, str) or not isinstance(password, str) or '@' not in email or not 1 <= len(password) <= 2048 or len(email) > 254:
                return self.send_json({'error': 'invalid_credentials'}, 400)
            self.server.market.save_credentials(email.strip(), password)
            return self.send_json({'saved': True, 'message': 'บันทึกแบบเข้ารหัสแล้ว กำลังตรวจการเชื่อมต่อ Myfxbook'})
        except Exception:
            return self.send_json({'error': 'credentials_not_saved'}, 400)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=4197)
    parser.add_argument('--state-dir', default=str(Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'Metafxclub' / 'SentimentUniverse'))
    parser.add_argument('--static-dir', default=str(ROOT / 'dist' / 'client'))
    parser.add_argument('--public-mirror')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('Port must be between 1024 and 65535')
    static_dir, state_dir = Path(args.static_dir).resolve(), Path(args.state_dir).resolve()
    if state_dir.is_relative_to(static_dir) or static_dir.is_relative_to(state_dir):
        parser.error('Private state must stay outside the public directory')
    if args.public_mirror and (Path(args.public_mirror).resolve().parent != static_dir or Path(args.public_mirror).name != 'market.json'):
        parser.error('Public mirror must be market.json directly inside the public directory')
    market = MarketService(state_dir, args.public_mirror)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), DashboardHandler)
    server.daemon_threads = True
    server.static_dir = static_dir
    server.market, server.csrf = market, secrets.token_urlsafe(32)
    atomic_json(Path(args.state_dir) / 'service.json', {'pid': os.getpid(), 'port': args.port, 'startedAt': utc_now(), 'project': str(ROOT)})
    market.start()
    try:
        server.serve_forever()
    finally:
        market.stop.set()
        server.server_close()


if __name__ == '__main__':
    main()
