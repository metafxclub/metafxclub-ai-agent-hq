"""Official Myfxbook community snapshot adapter, with no browser credentials.

MyfxbookProvider(config, state_dir, read_credentials=None, read_session=None,
                save_session=None, clear_session=None, transport=None, clock=None)
    .collect(credentials=None) -> public JSON-compatible dict.

Credential callback returns {email, password}; session callbacks read/write
{session, createdAt, expiresAt} (epoch seconds). The caller must protect that
store, e.g. Windows DPAPI. This module never persists authentication itself.
The optional transport(endpoint, params) returns (HTTP status, JSON object).
Use a persistent state_dir outside the served web directory. Do not log params.
Source contract: https://www.myfxbook.com/api (v1.38).
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4


DEFAULT_SYMBOLS = (
    "AUDCAD AUDCHF AUDJPY AUDNZD AUDUSD CADCHF CADJPY CHFJPY "
    "EURAUD EURCAD EURCHF EURGBP EURJPY EURNZD EURUSD "
    "GBPAUD GBPCAD GBPCHF GBPJPY GBPNZD GBPUSD NZDCAD NZDCHF NZDJPY NZDUSD "
    "USDCAD USDCHF USDJPY XAUUSD XAGUSD WTI BRENT"
).split()
MIN_INTERVAL = 20 * 60
WINDOW = 24 * 60 * 60
MAX_CALLS = 100
SESSION_TTL = 28 * WINDOW  # Renew before the provider's one-month maximum.
MAX_BODY = 4 * 1024 * 1024


def _iso(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace("+00:00", "Z") if timestamp is not None else None


def _number(value, *, minimum=0, maximum=None, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    if not math.isfinite(result) or result < minimum or (maximum is not None and result > maximum):
        return None
    if integer:
        return int(result) if result.is_integer() else None
    return result


def _symbol(value):
    if not isinstance(value, str):
        return None
    value = value.upper().replace("/", "").replace(" ", "")
    return value if re.fullmatch(r"[A-Z0-9_.-]{2,32}", value) else None


def _error_code(response):
    # Provider message is inspected only here; never expose its text to clients.
    message = response.get("message", "") if isinstance(response, dict) else ""
    if not isinstance(message, str):
        return "provider_unavailable"
    if re.search(r"limit|too many", message, re.I):
        return "rate_limited"
    if re.search(r"invalid.*(?:session|email|password)|(?:session|email|password).*(?:invalid|expired)|wrong.*(?:email|password)", message, re.I):
        return "auth_error"
    return "provider_unavailable"


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward credentials or session to a redirect target.


def _transport(endpoint, params):
    if endpoint not in ("login.json", "get-community-outlook.json"):
        raise ValueError("unsupported_endpoint")
    request = Request(
        "https://www.myfxbook.com/api/" + endpoint + "?" + urlencode(params),
        headers={"Accept": "application/json", "User-Agent": "Metafxclub-Sentiment/1.0"},
    )
    opener = build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=15) as response:
            body = response.read(MAX_BODY + 1)
            if len(body) > MAX_BODY:
                raise ValueError("response_too_large")
            return response.status, json.loads(body)
    except HTTPError as error:
        # Do not retain exception URL/body: both can contain secret parameters.
        status = error.code
        error.close()
        return status, None


def _write_json(path, value):
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, allow_nan=False, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


class _BudgetExceeded(Exception):
    pass


class MyfxbookProvider:
    def __init__(self, config, state_dir, *, read_credentials=None, read_session=None,
                 save_session=None, clear_session=None, transport=None, clock=None):
        self.config = config or {}
        self.directory = Path(state_dir)
        self.state_path = self.directory / "myfxbook-state.json"
        self.cache_path = self.directory / "myfxbook-public-cache.json"
        self.lock_path = self.directory / "myfxbook-collection.lock"
        self.read_credentials = read_credentials
        self.read_session = read_session
        self.save_session = save_session
        self.clear_session = clear_session
        self.transport = transport or _transport
        self.clock = clock or time.time
        self.session = None
        self.interval = max(MIN_INTERVAL, _number(self.config.get("intervalSeconds")) or MIN_INTERVAL)
        self.limit = min(MAX_CALLS, _number(self.config.get("maxRequestsPerDay"), minimum=1, integer=True) or MAX_CALLS)
        self.stale_after = max(self.interval, _number(self.config.get("staleAfterSeconds")) or self.interval * 2)
        self.symbols = list(dict.fromkeys(filter(None, (_symbol(s) for s in self.config.get("symbols", DEFAULT_SYMBOLS)))))
        self.symbol_map = {_symbol(k): _symbol(v) for k, v in self.config.get("symbolMap", {}).items()}

    @contextmanager
    def _lock(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        # OS locks are released on crash/restart; a stale lock filename cannot
        # permanently stop tomorrow's collection, and competing workers share it.
        with self.lock_path.open("a+b") as handle:
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                yield False
                return
            try:
                yield True
            finally:
                handle.seek(0)
                if os.name == "nt":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _load_state(self):
        if not self.state_path.exists():
            return {"attempts": [], "nextAttemptAt": None, "lastSuccessAt": None, "failures": 0, "reason": None}
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        if not isinstance(state, dict) or not isinstance(state.get("attempts"), list):
            raise ValueError("invalid_state")
        if any(_number(t) is None for t in state["attempts"]):
            raise ValueError("invalid_state")
        for key in ("nextAttemptAt", "lastSuccessAt"):
            if state.get(key) is not None and _number(state[key]) is None:
                raise ValueError("invalid_state")
        if _number(state.get("failures", 0), integer=True) is None:
            raise ValueError("invalid_state")
        return state

    def _cached(self):
        try:
            cache = json.loads(self.cache_path.read_text(encoding="utf-8"))
            # Revalidate persisted data; never return arbitrary fields from disk.
            if not isinstance(cache, dict) or _number(cache.get("asOf")) is None:
                return None
            items = self._normalize(cache.get("symbols"), cache["asOf"])
            return {"items": items, "asOf": cache["asOf"]} if items is not None else None
        except (OSError, ValueError, TypeError):
            return None

    def _empty(self):
        return [{"symbol": s, "sourceSymbol": self.symbol_map.get(s) or s,
                 "long": None, "short": None, "avgLong": None, "avgShort": None,
                 "available": False, "asOf": None, "reason": "no_data"} for s in self.symbols]

    def _result(self, status, state=None, cache=None, reason=None):
        state = state or {}
        return {"status": status, "source": "Myfxbook", "lastSuccessAt": _iso(cache["asOf"]) if cache else None,
                "nextAttemptAt": _iso(state.get("nextAttemptAt")), "reason": reason,
                "items": cache["items"] if cache else self._empty(),
                "timestampBasis": "retrieved_at", "intervalSeconds": self.interval,
                "requestsInLast24Hours": len(state.get("attempts", [])), "requestLimit": self.limit}

    def _normalize(self, rows, as_of):
        if not isinstance(rows, list) or not rows:
            return None
        indexed = {}
        duplicate = set()
        for row in rows:
            if not isinstance(row, dict) or not (name := _symbol(row.get("name"))):
                continue
            if name in indexed:
                duplicate.add(name)
            indexed[name] = row
        if not indexed:
            return None
        items = self._empty()
        for item in items:
            name = item["sourceSymbol"]
            row = indexed.get(name)
            if not row or name in duplicate:
                item["reason"] = "duplicate_symbol" if name in duplicate else "not_supplied"
                continue
            long = _number(row.get("longPercentage"), maximum=100)
            short = _number(row.get("shortPercentage"), maximum=100)
            # Myfxbook's own example totals 99 due to percentage rounding.
            if long is None or short is None or not 98 <= long + short <= 102:
                item["reason"] = "invalid_percentages"
                continue
            item.update(long=long, short=short, available=True, asOf=_iso(as_of), reason=None,
                        avgLong=_number(row.get("avgLongPrice"), minimum=1e-15),
                        avgShort=_number(row.get("avgShortPrice"), minimum=1e-15))
            positions = {"long": _number(row.get("longPositions"), integer=True),
                         "short": _number(row.get("shortPositions"), integer=True),
                         "total": _number(row.get("totalPositions"), integer=True)}
            if all(positions[k] is not None for k in positions) and positions["total"] != positions["long"] + positions["short"]:
                positions["total"] = None
            item["positions"] = positions
            item["volumes"] = {"long": _number(row.get("longVolume")), "short": _number(row.get("shortVolume"))}
        return items

    def _invalidate_session(self):
        self.session = None
        if self.clear_session:
            try:
                self.clear_session()
            except Exception:
                pass

    def credentials_changed(self):
        """Invalidate auth after the caller securely replaces credentials.

        The caller must serialize credential-store replacement, this method and
        collect() with the same application lock, so an in-flight login cannot
        save an old account's session after the replacement. A manual correction
        may shorten auth-only backoff, but never the minimum request interval,
        the rolling budget, provider-rate-limit backoff or a successful schedule.
        """
        with self._lock() as locked:
            if not locked:
                raise RuntimeError("collector_busy")
            self._invalidate_session()
            state = self._load_state()
            if state.get("reason") not in ("auth_error", "credentials_required", "needs_configuration"):
                return
            now = self.clock()
            attempts = state["attempts"]
            earliest = max(now, max(attempts) + self.interval) if attempts else now
            active = [stamp for stamp in attempts if stamp > now - WINDOW]
            reason = None
            if len(active) >= self.limit:
                earliest = max(earliest, min(active) + WINDOW + 1)
                reason = "rate_limited"
            state.update(nextAttemptAt=earliest, failures=0, reason=reason)
            _write_json(self.state_path, state)

    def _read_auth(self, now):
        session = self.session
        if session is None and self.read_session:
            session = self.read_session()
        if not isinstance(session, dict) or not isinstance(session.get("session"), str) or not session["session"]:
            return None
        created = _number(session.get("createdAt"))
        expires = _number(session.get("expiresAt"))
        if created is None or expires is None or now >= min(expires, created + SESSION_TTL):
            self._invalidate_session()
            return None
        self.session = session
        return session["session"]

    def _request(self, endpoint, params, state, now):
        state["attempts"] = [stamp for stamp in state["attempts"] if stamp > now - WINDOW]
        if len(state["attempts"]) >= self.limit:
            state["nextAttemptAt"] = max(state.get("nextAttemptAt") or now, min(state["attempts"]) + WINDOW + 1)
            _write_json(self.state_path, state)
            raise _BudgetExceeded()
        # Reserve before I/O; failed calls, login and process crashes count too.
        state["attempts"].append(now)
        _write_json(self.state_path, state)
        return self.transport(endpoint, params)

    def _fail(self, code, state, cache, now):
        state["failures"] = min(10, state.get("failures", 0) + 1)
        state["reason"] = code
        delay = min(6 * 3600, self.interval * 2 ** (state["failures"] - 1))
        state["nextAttemptAt"] = max(state.get("nextAttemptAt") or now, now + delay)
        _write_json(self.state_path, state)
        return self._result("stale" if cache else code, state, cache, code)

    def collect(self, credentials=None):
        """Collect one due snapshot. Cached reads never contact Myfxbook."""
        try:
            with self._lock() as locked:
                if not locked:
                    return self._result("busy", cache=self._cached(), reason="collector_busy")
                return self._collect_locked(credentials)
        except (OSError, ValueError, TypeError, OverflowError):
            return self._result("state_error", cache=self._cached(), reason="local_state_unavailable")

    def _collect_locked(self, credentials):
        now = self.clock()
        state = self._load_state()
        state["attempts"] = [stamp for stamp in state["attempts"] if stamp > now - WINDOW]
        cache = self._cached()
        if state.get("nextAttemptAt") and now < state["nextAttemptAt"]:
            status = "ready" if cache and not state.get("reason") and now - cache["asOf"] <= self.stale_after else "stale" if cache else state.get("reason") or "waiting"
            return self._result(status, state, cache, state.get("reason"))
        try:
            session = self._read_auth(now)
            if not session:
                credentials = credentials or (self.read_credentials() if self.read_credentials else None)
                if not isinstance(credentials, dict) or not all(isinstance(credentials.get(k), str) and credentials[k] for k in ("email", "password")):
                    return self._result("needs_configuration", state, cache, "credentials_required")
            state["nextAttemptAt"] = now + self.interval
            _write_json(self.state_path, state)
            if not session:
                status, response = self._request("login.json", {"email": credentials["email"], "password": credentials["password"]}, state, now)
                if status == 429:
                    return self._fail("rate_limited", state, cache, now)
                if status == 401:
                    self._invalidate_session()
                    return self._fail("auth_error", state, cache, now)
                if isinstance(response, dict) and response.get("error") is True:
                    code = _error_code(response)
                    if code == "auth_error":
                        self._invalidate_session()
                    return self._fail(code, state, cache, now)
                if status != 200 or not isinstance(response, dict) or response.get("error") is not False or not isinstance(response.get("session"), str) or not response["session"]:
                    return self._fail("provider_unavailable", state, cache, now)
                session = response["session"]
                self.session = {"session": session, "createdAt": now, "expiresAt": now + SESSION_TTL}
                if self.save_session:
                    self.save_session(self.session.copy())
            status, response = self._request("get-community-outlook.json", {"session": session}, state, now)
            if status == 429:
                return self._fail("rate_limited", state, cache, now)
            if status == 401:
                self._invalidate_session()
                return self._fail("auth_error", state, cache, now)
            if status != 200 or not isinstance(response, dict):
                return self._fail("provider_unavailable", state, cache, now)
            if response.get("error") is True:
                code = _error_code(response)
                if code == "auth_error":
                    self._invalidate_session()
                return self._fail(code, state, cache, now)
            items = self._normalize(response.get("symbols"), now) if response.get("error") is False else None
            if items is None:
                return self._fail("invalid_response", state, cache, now)
            # Persist an allowlisted public payload, never raw response/session/message.
            rows = [{"name": item["sourceSymbol"], "longPercentage": item["long"], "shortPercentage": item["short"],
                     "avgLongPrice": item["avgLong"], "avgShortPrice": item["avgShort"],
                     "longPositions": item.get("positions", {}).get("long"), "shortPositions": item.get("positions", {}).get("short"),
                     "totalPositions": item.get("positions", {}).get("total"), "longVolume": item.get("volumes", {}).get("long"),
                     "shortVolume": item.get("volumes", {}).get("short")} for item in items if item["available"]]
            if not rows:
                return self._fail("invalid_response", state, cache, now)
            _write_json(self.cache_path, {"asOf": now, "symbols": rows})
            state.update(lastSuccessAt=now, failures=0, reason=None)
            _write_json(self.state_path, state)
            return self._result("ready", state, {"items": items, "asOf": now})
        except _BudgetExceeded:
            return self._fail("rate_limited", state, cache, now)
        except Exception:
            # Redaction by construction: never emit str(exception), request URLs,
            # credentials, provider body or secret-bearing callback exceptions.
            return self._fail("provider_unavailable", state, cache, now)


def collect(config, state_dir, credentials=None, **kwargs):
    return MyfxbookProvider(config, state_dir, **kwargs).collect(credentials)
