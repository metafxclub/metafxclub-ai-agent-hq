from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MARKET_WATCH_PATH = (
    PROJECT_ROOT / "backend" / "local-runner" / "hq_backend" / "trading" / "mt4_market_watch.py"
)
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def symbols_sel_payload(*symbols: str, version: int = 400) -> bytes:
    payload = bytearray(version.to_bytes(4, "little"))
    for symbol in symbols:
        encoded = symbol.encode("ascii")
        if len(encoded) > 12:
            raise ValueError("test symbol exceeds the MT4 symbols.sel field")
        payload.extend(encoded.ljust(12, b"\0"))
        payload.extend(b"\0" * (128 - 12))
    return bytes(payload)


class Mt4MarketWatchParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.market_watch = load_module(
            "metafx_mt4_market_watch_tests",
            MARKET_WATCH_PATH,
        )

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_profile(self, name: str, *symbols: str) -> Path:
        profile = self.root / "history" / name
        profile.mkdir(parents=True, exist_ok=True)
        source = profile / "symbols.sel"
        source.write_bytes(symbols_sel_payload(*symbols))
        return source

    def test_parser_accepts_header_400_and_preserves_exact_broker_suffixes(self) -> None:
        symbols = self.market_watch.parse_symbols_sel_bytes(
            symbols_sel_payload("XAUUSD.pro", "EURUSD#", "USDJPY-m")
        )

        self.assertEqual(symbols, ("XAUUSD.pro", "EURUSD#", "USDJPY-m"))

    def test_parser_rejects_unsupported_header(self) -> None:
        with self.assertRaises(self.market_watch.MarketWatchReadError) as caught:
            self.market_watch.parse_symbols_sel_bytes(
                symbols_sel_payload("EURUSD", version=401)
            )

        self.assertEqual(caught.exception.code, "unsupported_symbols_file_version")

    def test_parser_rejects_non_record_aligned_layout(self) -> None:
        raw = (400).to_bytes(4, "little") + (b"\0" * 127)

        with self.assertRaises(self.market_watch.MarketWatchReadError) as caught:
            self.market_watch.parse_symbols_sel_bytes(raw)

        self.assertEqual(caught.exception.code, "invalid_symbols_file")

    def test_parser_rejects_case_insensitive_duplicates(self) -> None:
        with self.assertRaises(self.market_watch.MarketWatchReadError) as caught:
            self.market_watch.parse_symbols_sel_bytes(
                symbols_sel_payload("EURUSD", "eurusd")
            )

        self.assertEqual(caught.exception.code, "duplicate_symbol_name")

    def test_parser_rejects_non_ascii_symbol(self) -> None:
        raw = bytearray(symbols_sel_payload("EURUSD"))
        raw[4] = 0xFF

        with self.assertRaises(self.market_watch.MarketWatchReadError) as caught:
            self.market_watch.parse_symbols_sel_bytes(bytes(raw))

        self.assertEqual(caught.exception.code, "invalid_symbol_name")

    def test_resolver_returns_only_unique_visible_row_count_match(self) -> None:
        self._write_profile("default", "EURUSD")
        self._write_profile("demo", "XAUUSD.pro", "EURUSD#")
        self._write_profile("live", "USDJPY", "GBPUSD", "AUDUSD")

        result = self.market_watch.resolve_market_watch_symbols(self.root, 2)

        self.assertEqual(result.symbols, ("XAUUSD.pro", "EURUSD#"))
        self.assertEqual(result.inspected_profile_count, 3)
        self.assertGreater(result.source_mtime_ns, 0)

    def test_resolver_fails_closed_when_no_profile_count_matches(self) -> None:
        self._write_profile("default", "EURUSD")
        self._write_profile("demo", "EURUSD", "GBPUSD")

        with self.assertRaises(self.market_watch.MarketWatchReadError) as caught:
            self.market_watch.resolve_market_watch_symbols(self.root, 3)

        self.assertEqual(caught.exception.code, "market_watch_profile_not_matched")

    def test_resolver_fails_closed_when_profile_count_match_is_ambiguous(self) -> None:
        self._write_profile("demo", "EURUSD", "GBPUSD")
        self._write_profile("live", "XAUUSD.pro", "USDJPY")

        with self.assertRaises(self.market_watch.MarketWatchReadError) as caught:
            self.market_watch.resolve_market_watch_symbols(self.root, 2)

        self.assertEqual(caught.exception.code, "market_watch_profile_ambiguous")

    def test_parser_detects_file_changed_during_read(self) -> None:
        source = self._write_profile("demo", "EURUSD", "GBPUSD")
        original_read_bytes = Path.read_bytes

        def read_then_change(path: Path) -> bytes:
            raw = original_read_bytes(path)
            with path.open("ab") as handle:
                handle.write(b"\0")
            return raw

        with mock.patch.object(Path, "read_bytes", new=read_then_change):
            with self.assertRaises(self.market_watch.MarketWatchReadError) as caught:
                self.market_watch.parse_symbols_sel(source)

        self.assertEqual(caught.exception.code, "symbols_file_changed_during_read")

    def test_parser_rejects_symbol_file_symlink_when_supported(self) -> None:
        target = self.root / "target.sel"
        target.write_bytes(symbols_sel_payload("EURUSD"))
        link = self.root / "linked.sel"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"symlinks unavailable: {error}")

        with self.assertRaises(self.market_watch.MarketWatchReadError) as caught:
            self.market_watch.parse_symbols_sel(link)

        self.assertEqual(caught.exception.code, "symbols_file_link_rejected")

    def test_resolver_rejects_invalid_visible_row_count(self) -> None:
        self._write_profile("demo", "EURUSD")

        for invalid in (True, 0, 513, "1"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(self.market_watch.MarketWatchReadError) as caught:
                    self.market_watch.resolve_market_watch_symbols(self.root, invalid)
                self.assertEqual(caught.exception.code, "market_watch_row_count_invalid")


class Mt4MarketWatchBridgeReadModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module(
            "metafx_mt4_market_watch_bridge_tests",
            BRIDGE_PATH,
        )

    @staticmethod
    def _context(platform: str = "mt4", revision: int = 7) -> dict:
        return {
            "record": {
                "candidateId": "mtc-market-watch-test",
                "platform": platform,
                "installPath": r"C:\private\broker-install",
                "dataPath": r"C:\private\broker-data",
                "runningState": "platform_running_detected",
                "accountNumber": "12345678",
                "brokerServer": "PrivateBroker-Live",
            },
            "token": {
                "candidateId": "mtc-market-watch-test",
                "selectionRevision": revision,
            },
        }

    @staticmethod
    def _catalog() -> SimpleNamespace:
        return SimpleNamespace(
            symbols=("XAUUSD.pro", "EURUSD#"),
            source_mtime_ns=1_789_000_000_000_000_000,
            inspected_profile_count=3,
        )

    def test_selected_mt4_catalog_is_bound_to_candidate_revision_and_private(self) -> None:
        context = self._context()
        token = context["token"]
        with mock.patch.object(
            self.bridge,
            "_global_metatrader_platform_context",
            return_value=context,
        ), mock.patch.object(
            self.bridge,
            "_mt4_market_watch_visible_row_count",
            side_effect=[
                {"ok": True, "rowCount": 2},
                {"ok": True, "rowCount": 2},
            ],
        ), mock.patch.object(
            self.bridge,
            "resolve_market_watch_symbols",
            return_value=self._catalog(),
        ) as resolver, mock.patch.object(
            self.bridge,
            "_global_metatrader_platform_token",
            return_value=token,
        ):
            model = self.bridge.mt4_market_watch_read_model("right_server_racks")

        resolver.assert_called_once_with(Path(context["record"]["dataPath"]), 2)
        self.assertEqual(model["status"], "ready")
        self.assertEqual(model["candidateId"], token["candidateId"])
        self.assertEqual(model["selectionRevision"], token["selectionRevision"])
        self.assertEqual(model["symbols"], ["XAUUSD.pro", "EURUSD#"])
        self.assertEqual(model["symbolCount"], 2)
        self.assertEqual(model["verification"]["visibleRowCount"], 2)
        self.assertEqual(model["privacy"], {
            "pathsExposed": False,
            "processIdsExposed": False,
            "accountDataExposed": False,
            "quotesOrTradesExposed": False,
        })
        serialized = json.dumps(model, ensure_ascii=False)
        for forbidden in (
            "broker-install",
            "broker-data",
            "12345678",
            "PrivateBroker-Live",
            "source_mtime_ns",
        ):
            self.assertNotIn(forbidden, serialized)
        observed_keys: set[str] = set()

        def collect_keys(value: object) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    observed_keys.add(str(key))
                    collect_keys(child)
            elif isinstance(value, list):
                for child in value:
                    collect_keys(child)

        collect_keys(model)
        self.assertTrue(
            {"processId", "windowHandle", "dataPath", "installPath"}.isdisjoint(
                observed_keys
            )
        )

    def test_selection_revision_change_discards_catalog(self) -> None:
        context = self._context(revision=7)
        with mock.patch.object(
            self.bridge,
            "_global_metatrader_platform_context",
            return_value=context,
        ), mock.patch.object(
            self.bridge,
            "_mt4_market_watch_visible_row_count",
            side_effect=[
                {"ok": True, "rowCount": 2},
                {"ok": True, "rowCount": 2},
            ],
        ), mock.patch.object(
            self.bridge,
            "resolve_market_watch_symbols",
            return_value=self._catalog(),
        ), mock.patch.object(
            self.bridge,
            "_global_metatrader_platform_token",
            return_value={
                "candidateId": context["token"]["candidateId"],
                "selectionRevision": 8,
            },
        ):
            model = self.bridge.mt4_market_watch_read_model("right_server_racks")

        self.assertEqual(model["status"], "stale_selection")
        self.assertEqual(
            model["reasonCode"],
            "terminal_selection_changed_during_read",
        )
        self.assertEqual(model["symbols"], [])
        self.assertEqual(model["symbolCount"], 0)
        self.assertIsNone(model["candidateId"])
        self.assertIsNone(model["selectionRevision"])

    def test_selected_mt5_fails_closed_without_probe_or_file_read(self) -> None:
        context = self._context(platform="mt5")
        with mock.patch.object(
            self.bridge,
            "_global_metatrader_platform_context",
            return_value=context,
        ), mock.patch.object(
            self.bridge,
            "_mt4_market_watch_visible_row_count",
        ) as probe, mock.patch.object(
            self.bridge,
            "resolve_market_watch_symbols",
        ) as resolver:
            model = self.bridge.mt4_market_watch_read_model("right_server_racks")

        probe.assert_not_called()
        resolver.assert_not_called()
        self.assertEqual(model["status"], "unsupported_platform")
        self.assertEqual(model["reasonCode"], "selected_terminal_not_mt4")
        self.assertEqual(model["symbols"], [])
        self.assertEqual(model["symbolCount"], 0)

    def test_missing_selected_terminal_fails_closed(self) -> None:
        with mock.patch.object(
            self.bridge,
            "_global_metatrader_platform_context",
            return_value=None,
        ), mock.patch.object(
            self.bridge,
            "_mt4_market_watch_visible_row_count",
        ) as probe, mock.patch.object(
            self.bridge,
            "resolve_market_watch_symbols",
        ) as resolver:
            model = self.bridge.mt4_market_watch_read_model("right_server_racks")

        probe.assert_not_called()
        resolver.assert_not_called()
        self.assertEqual(model["status"], "terminal_not_selected")
        self.assertEqual(model["reasonCode"], "selected_terminal_missing")
        self.assertEqual(model["symbols"], [])

    def test_visible_row_count_change_discards_catalog(self) -> None:
        context = self._context()
        with mock.patch.object(
            self.bridge,
            "_global_metatrader_platform_context",
            return_value=context,
        ), mock.patch.object(
            self.bridge,
            "_mt4_market_watch_visible_row_count",
            side_effect=[
                {"ok": True, "rowCount": 2},
                {"ok": True, "rowCount": 3},
            ],
        ), mock.patch.object(
            self.bridge,
            "resolve_market_watch_symbols",
            return_value=self._catalog(),
        ), mock.patch.object(
            self.bridge,
            "_global_metatrader_platform_token",
            return_value=context["token"],
        ):
            model = self.bridge.mt4_market_watch_read_model("right_server_racks")

        self.assertEqual(model["status"], "stale_market_watch")
        self.assertEqual(model["reasonCode"], "market_watch_changed_during_read")
        self.assertEqual(model["symbols"], [])


if __name__ == "__main__":
    unittest.main()
