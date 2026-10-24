"""Provider contracts exercised with deterministic mock HTTP, never real login."""
import json
from pathlib import Path
import tempfile
import unittest

from live_backend.myfxbook import MyfxbookProvider, MIN_INTERVAL, SESSION_TTL, WINDOW


class Clock:
    def __init__(self):
        self.now = 1_800_000_000.0

    def __call__(self):
        return self.now


def response_row(**overrides):
    return {"name": "EURUSD", "longPercentage": 44, "shortPercentage": 55,
            "avgLongPrice": 1.4097, "avgShortPrice": 1.3808,
            "longVolume": 905.47, "shortVolume": 1142.58,
            "longPositions": 2932, "shortPositions": 3888, "totalPositions": 6820,
            **overrides}


def snapshot(*rows):
    return 200, {"error": False, "symbols": list(rows or [response_row()])}


class Transport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, endpoint, params):
        self.calls.append((endpoint, params.copy()))
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class MyfxbookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.clock = Clock()
        self.auth = {"session": "TEST_SESSION_SECRET", "createdAt": self.clock.now, "expiresAt": self.clock.now + SESSION_TTL}

    def provider(self, transport, config=None, **kwargs):
        kwargs.setdefault("read_session", lambda: self.auth)
        return MyfxbookProvider(config or {"symbols": ["EURUSD", "WTI"]}, self.directory,
                                clock=self.clock, transport=transport, **kwargs)

    def state(self):
        return json.loads((self.directory / "myfxbook-state.json").read_text())

    def test_no_configuration_never_calls_network_or_fabricates(self):
        transport = Transport()
        result = self.provider(transport, read_session=None).collect()
        self.assertEqual("needs_configuration", result["status"])
        self.assertEqual([], transport.calls)
        self.assertIsNone(result["lastSuccessAt"])
        self.assertTrue(all(not row["available"] and row["long"] is None for row in result["items"]))

    def test_official_fields_preserve_percent_rounding_and_unknown_oil(self):
        result = self.provider(Transport(snapshot())).collect()
        self.assertEqual("ready", result["status"])
        eur, oil = result["items"]
        self.assertEqual((44, 55), (eur["long"], eur["short"]))
        self.assertEqual((1.4097, 1.3808), (eur["avgLong"], eur["avgShort"]))
        self.assertEqual(6820, eur["positions"]["total"])
        self.assertEqual("retrieved_at", result["timestampBasis"])
        self.assertFalse(oil["available"])
        self.assertIsNone(oil["long"])
        self.assertEqual("not_supplied", oil["reason"])
        self.assertNotIn("currentPrice", eur)
        self.assertNotIn("popularity", eur)

    def test_multiple_clicks_and_restart_respect_persisted_interval(self):
        transport = Transport(snapshot(), snapshot(response_row(longPercentage=50, shortPercentage=50)))
        first = self.provider(transport).collect()
        for _ in range(5):
            self.assertEqual(first["lastSuccessAt"], self.provider(transport).collect()["lastSuccessAt"])
        self.assertEqual(1, len(transport.calls))
        self.clock.now += MIN_INTERVAL
        self.assertEqual(50, self.provider(transport).collect()["items"][0]["long"])
        self.assertEqual(2, len(transport.calls))

    def test_interval_cannot_be_lowered_below_twenty_minutes(self):
        result = self.provider(Transport(snapshot()), {"symbols": ["EURUSD"], "intervalSeconds": 1}).collect()
        self.assertEqual(MIN_INTERVAL, result["intervalSeconds"])
        self.assertEqual(self.clock.now + MIN_INTERVAL, self.state()["nextAttemptAt"])

    def test_login_session_is_callback_only_and_budget_counts_both_calls(self):
        saved = []
        transport = Transport((200, {"error": False, "session": "NEW_TEST_SECRET"}), snapshot())
        provider = self.provider(transport, read_session=None, save_session=saved.append,
                                 read_credentials=lambda: {"email": "fixture@example.invalid", "password": "PASSWORD_TEST_SECRET"})
        result = provider.collect()
        self.assertEqual("ready", result["status"])
        self.assertEqual(["login.json", "get-community-outlook.json"], [x[0] for x in transport.calls])
        self.assertEqual("NEW_TEST_SECRET", saved[0]["session"])
        self.assertEqual(2, result["requestsInLast24Hours"])
        files = "".join(p.read_text() for p in self.directory.glob("*.json"))
        self.assertNotIn("NEW_TEST_SECRET", files)
        self.assertNotIn("PASSWORD_TEST_SECRET", files)
        self.assertNotIn("fixture@example.invalid", files)
        self.assertNotIn("SECRET", json.dumps(result))

    def test_provider_message_and_extra_payload_fields_never_leak(self):
        row = response_row(password="LEAKME", session="LEAKME", popularity=12, currentPrice=1.1)
        result = self.provider(Transport((200, {"error": False, "symbols": [row], "session": "LEAKME"}))).collect()
        everything = json.dumps(result) + "".join(p.read_text() for p in self.directory.glob("*.json"))
        self.assertNotIn("LEAKME", everything)
        self.assertNotIn("currentPrice", everything)
        self.assertNotIn("popularity", everything)

    def test_exception_redaction_and_failure_counts_persist_across_restart(self):
        transport = Transport(RuntimeError("https://secret.invalid/?password=LEAKME"))
        result = self.provider(transport).collect()
        self.assertEqual("provider_unavailable", result["status"])
        self.assertEqual(1, len(self.state()["attempts"]))
        self.assertNotIn("LEAKME", json.dumps(result) + (self.directory / "myfxbook-state.json").read_text())
        result2 = self.provider(transport).collect()
        self.assertEqual(1, len(transport.calls))
        self.assertEqual(result["nextAttemptAt"], result2["nextAttemptAt"])

    def test_invalid_session_cleared_without_immediate_retry(self):
        cleared = []
        transport = Transport((200, {"error": True, "message": "Invalid session. LEAKME"}))
        provider = self.provider(transport, clear_session=lambda: cleared.append(True))
        result = provider.collect()
        self.assertEqual("auth_error", result["status"])
        self.assertEqual([True], cleared)
        self.assertIsNone(provider.session)
        self.assertEqual(1, len(transport.calls))
        provider.collect()
        self.assertEqual(1, len(transport.calls))
        self.assertNotIn("LEAKME", json.dumps(result))

    def test_http_401_invalidates_auth(self):
        cleared = []
        result = self.provider(Transport((401, None)), clear_session=lambda: cleared.append(True)).collect()
        self.assertEqual("auth_error", result["status"])
        self.assertEqual([True], cleared)

    def test_credential_replacement_drops_old_account_session_and_keeps_success_interval(self):
        secure = {"session": self.auth.copy(), "credentials": {"email": "old@example.invalid", "password": "OLD"}}
        transport = Transport(snapshot(), (200, {"error": False, "session": "NEW_ACCOUNT_SESSION"}), snapshot())
        provider = self.provider(transport, read_session=lambda: secure.get("session"),
                                 read_credentials=lambda: secure["credentials"],
                                 save_session=lambda value: secure.update(session=value),
                                 clear_session=lambda: secure.pop("session", None))
        provider.collect()
        original = self.state()
        secure.clear()
        secure["credentials"] = {"email": "new@example.invalid", "password": "NEW"}
        provider.credentials_changed()
        self.assertIsNone(provider.session)
        self.assertEqual(original, self.state())
        provider.collect()
        self.assertEqual(1, len(transport.calls))
        self.clock.now += MIN_INTERVAL
        result = provider.collect()
        self.assertEqual("ready", result["status"])
        self.assertEqual("new@example.invalid", transport.calls[1][1]["email"])
        self.assertEqual("NEW_ACCOUNT_SESSION", transport.calls[2][1]["session"])
        self.assertEqual(3, result["requestsInLast24Hours"])

    def test_auth_correction_shortens_only_auth_backoff_and_keeps_twenty_minute_floor(self):
        transport = Transport((401, None), (401, None))
        provider = self.provider(transport, read_session=None)
        credentials = {"email": "fixture@example.invalid", "password": "EXAMPLE"}
        provider.collect(credentials)
        self.clock.now += MIN_INTERVAL
        provider.collect(credentials)
        original = self.state()
        self.assertEqual(self.clock.now + 2 * MIN_INTERVAL, original["nextAttemptAt"])
        self.clock.now += 10
        provider.credentials_changed()
        changed = self.state()
        self.assertEqual(original["attempts"], changed["attempts"])
        self.assertEqual(original["attempts"][-1] + MIN_INTERVAL, changed["nextAttemptAt"])
        self.assertIsNone(changed["reason"])
        provider.collect(credentials)
        self.assertEqual(2, len(transport.calls))

    def test_auth_correction_cannot_bypass_full_rolling_budget(self):
        attempts = [self.clock.now - 100] * 100
        (self.directory / "myfxbook-state.json").write_text(json.dumps({
            "attempts": attempts, "nextAttemptAt": self.clock.now + 3600,
            "lastSuccessAt": None, "failures": 3, "reason": "auth_error"}))
        transport = Transport()
        provider = self.provider(transport)
        provider.credentials_changed()
        self.assertEqual(attempts, self.state()["attempts"])
        self.assertEqual(attempts[0] + WINDOW + 1, self.state()["nextAttemptAt"])
        self.assertEqual("rate_limited", provider.collect()["status"])
        self.assertEqual([], transport.calls)

    def test_credential_change_preserves_provider_rate_limit_and_other_failure_backoff(self):
        for reason in ("rate_limited", "provider_unavailable"):
            with self.subTest(reason=reason):
                state = {"attempts": [self.clock.now], "nextAttemptAt": self.clock.now + 7200,
                         "lastSuccessAt": None, "failures": 3, "reason": reason}
                (self.directory / "myfxbook-state.json").write_text(json.dumps(state))
                provider = self.provider(Transport())
                provider.session = self.auth.copy()
                provider.credentials_changed()
                self.assertIsNone(provider.session)
                self.assertEqual(state, self.state())

    def test_login_rate_limit_not_misreported_as_bad_password(self):
        transport = Transport((200, {"error": True, "message": "Too many requests. LEAKME"}))
        result = self.provider(transport, read_session=None).collect({"email": "fixture@example.invalid", "password": "EXAMPLE"})
        self.assertEqual("rate_limited", result["status"])
        self.assertEqual(1, len(transport.calls))
        self.assertNotIn("LEAKME", json.dumps(result))

    def test_wrong_password_json_is_auth_error_without_retry(self):
        transport = Transport((200, {"error": True, "message": "Invalid password"}))
        result = self.provider(transport, read_session=None).collect({"email": "fixture@example.invalid", "password": "EXAMPLE"})
        self.assertEqual("auth_error", result["status"])
        self.assertEqual(1, len(transport.calls))

    def test_403_or_html_is_unavailable_not_claimed_wrong_credentials(self):
        for status, body in [(403, None), (200, "<html>Cloudflare LEAKME</html>")]:
            with self.subTest(status=status):
                self.clock.now += 10 * WINDOW
                self.auth.update(createdAt=self.clock.now, expiresAt=self.clock.now + SESSION_TTL)
                cleared = []
                result = self.provider(Transport((status, body)), clear_session=lambda: cleared.append(True)).collect()
                self.assertEqual("provider_unavailable", result["status"])
                self.assertEqual([], cleared)
                self.assertNotIn("LEAKME", json.dumps(result))

    def test_expired_session_reauthenticates_with_local_credentials(self):
        self.auth["expiresAt"] = self.clock.now - 1
        transport = Transport((200, {"error": False, "session": "RENEWED"}), snapshot())
        result = self.provider(transport).collect({"email": "fixture@example.invalid", "password": "EXAMPLE"})
        self.assertEqual("ready", result["status"])
        self.assertEqual("login.json", transport.calls[0][0])

    def test_budget_stops_at_100_and_survives_restart(self):
        self.directory.mkdir(exist_ok=True)
        (self.directory / "myfxbook-state.json").write_text(json.dumps({
            "attempts": [self.clock.now - 100] * 100, "nextAttemptAt": None,
            "lastSuccessAt": None, "failures": 0, "reason": None}))
        transport = Transport()
        result = self.provider(transport).collect()
        self.assertEqual("rate_limited", result["status"])
        self.assertEqual([], transport.calls)
        self.assertEqual(100, result["requestLimit"])
        self.assertGreater(self.state()["nextAttemptAt"], self.clock.now)
        self.assertEqual("rate_limited", self.provider(transport).collect()["status"])

    def test_only_expired_rolling_window_budget_is_released(self):
        (self.directory / "myfxbook-state.json").write_text(json.dumps({
            "attempts": [self.clock.now - WINDOW - 1] * 99 + [self.clock.now - 10],
            "nextAttemptAt": None, "failures": 0, "reason": None}))
        result = self.provider(Transport(snapshot())).collect()
        self.assertEqual("ready", result["status"])
        self.assertEqual(2, result["requestsInLast24Hours"])

    def test_login_does_not_allow_budget_overrun_between_two_calls(self):
        (self.directory / "myfxbook-state.json").write_text(json.dumps({
            "attempts": [self.clock.now - 100] * 99, "nextAttemptAt": None, "failures": 0, "reason": None}))
        transport = Transport((200, {"error": False, "session": "NEW"}))
        result = self.provider(transport, read_session=None).collect({"email": "fixture@example.invalid", "password": "EXAMPLE"})
        self.assertEqual("rate_limited", result["status"])
        self.assertEqual(1, len(transport.calls))
        self.assertEqual(100, len(self.state()["attempts"]))

    def test_rate_limit_responses_are_backed_off_not_retried(self):
        transport = Transport((429, None), (429, None))
        provider = self.provider(transport)
        self.assertEqual("rate_limited", provider.collect()["status"])
        self.clock.now += MIN_INTERVAL
        provider.collect()
        self.assertEqual(self.clock.now + 2 * MIN_INTERVAL, self.state()["nextAttemptAt"])
        for _ in range(3):
            provider.collect()
        self.assertEqual(2, len(transport.calls))

    def test_last_good_cache_is_preserved_with_stale_status_on_failure(self):
        transport = Transport(snapshot(), TimeoutError("LEAKME"))
        first = self.provider(transport).collect()
        self.clock.now += MIN_INTERVAL
        stale = self.provider(transport).collect()
        self.assertEqual("stale", stale["status"])
        self.assertEqual(first["lastSuccessAt"], stale["lastSuccessAt"])
        self.assertEqual(44, stale["items"][0]["long"])
        self.assertEqual("provider_unavailable", stale["reason"])

    def test_corrupt_budget_fails_closed_without_network(self):
        (self.directory / "myfxbook-state.json").write_text('{"attempts":"broken"}')
        transport = Transport()
        self.assertEqual("state_error", self.provider(transport).collect()["status"])
        self.assertEqual([], transport.calls)

    def test_two_collectors_do_not_duplicate_request(self):
        blocked = []
        second_transport = Transport()
        def collect_with_competition(endpoint, params):
            blocked.append(self.provider(second_transport).collect())
            return snapshot()
        result = self.provider(collect_with_competition).collect()
        self.assertEqual("ready", result["status"])
        self.assertEqual("busy", blocked[0]["status"])
        self.assertEqual([], second_transport.calls)
        # The file remains but the OS lock is released, allowing later rounds.
        self.clock.now += MIN_INTERVAL
        self.assertEqual("ready", self.provider(Transport(snapshot())).collect()["status"])

    def test_bad_values_and_duplicate_symbols_are_unavailable(self):
        rows = [response_row(), response_row(name="XAUUSD", longPercentage="NaN"),
                response_row(name="WTI"), response_row(name="WTI")]
        result = self.provider(Transport(snapshot(*rows)), {"symbols": ["EURUSD", "XAUUSD", "WTI"]}).collect()
        self.assertEqual([True, False, False], [r["available"] for r in result["items"]])
        self.assertEqual("invalid_percentages", result["items"][1]["reason"])
        self.assertEqual("duplicate_symbol", result["items"][2]["reason"])

    def test_invalid_optional_fields_remain_null_and_count_mismatch_is_not_invented(self):
        result = self.provider(Transport(snapshot(response_row(avgLongPrice=0, avgShortPrice="Infinity", totalPositions=2048, longVolume=-1)))).collect()
        row = result["items"][0]
        self.assertTrue(row["available"])
        self.assertIsNone(row["avgLong"])
        self.assertIsNone(row["avgShort"])
        self.assertIsNone(row["positions"]["total"])
        self.assertIsNone(row["volumes"]["long"])

    def test_explicit_symbol_mapping_only(self):
        result = self.provider(Transport(snapshot(response_row(name="EUR/USD"), response_row(name="USOIL"))),
                               {"symbols": ["EURUSD", "WTI", "BRENT"], "symbolMap": {"WTI": "USOIL"}}).collect()
        self.assertEqual([True, True, False], [r["available"] for r in result["items"]])
        self.assertEqual("USOIL", result["items"][1]["sourceSymbol"])

    def test_empty_payload_does_not_overwrite_last_success(self):
        transport = Transport(snapshot(), (200, {"error": False, "symbols": []}))
        initial = self.provider(transport).collect()
        self.clock.now += MIN_INTERVAL
        result = self.provider(transport).collect()
        self.assertEqual("stale", result["status"])
        self.assertEqual("invalid_response", result["reason"])
        self.assertEqual(initial["lastSuccessAt"], result["lastSuccessAt"])


if __name__ == "__main__":
    unittest.main()
