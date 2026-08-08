from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import inspect
import io
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "bridge_deep_analysis_test",
        BRIDGE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def synthetic_bars(count: int = 500) -> list[dict]:
    bars = []
    for index in range(count):
        close = (
            2000.0
            + (index * 0.17)
            + (23.0 * math.sin(index / 11.0))
            + (6.0 * math.sin(index / 3.0))
        )
        open_price = close - (2.1 * math.sin(index / 2.0))
        bars.append({
            "time": 1_700_000_000 + (index * 300),
            "open": open_price,
            "high": max(open_price, close) + 2.5 + (index % 4),
            "low": min(open_price, close) - 2.5 - (index % 3),
            "close": close,
            "volume": 100.0 + (index % 41),
        })
    return bars


def snapshot_model(
    *,
    count: int = 500,
    status: str = "ready",
    snapshot_id: str = "a" * 64,
) -> dict:
    fresh = status == "ready"
    return {
        "status": status,
        "reasonCode": "ready" if fresh else "snapshot_stale",
        "dailySummary": {
            "available": True,
            "status": "ready",
            "reasonCode": "ready",
            "currency": "USD",
            "netPnl": 12.5,
            "balance": 1000.0,
            "equity": 1012.5,
            "accountLogin": 123456,
        },
        "chartSnapshot": {
            "available": fresh,
            "status": status,
            "reasonCode": "ready" if fresh else "snapshot_stale",
            "snapshotId": snapshot_id,
            "observedAt": "2026-08-01T10:00:00+00:00",
            "ageSeconds": 1.0 if fresh else 600.0,
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "bid": 2400.1,
            "ask": 2400.3,
            "spreadPoints": 20.0,
            "marketOpen": True,
            "marketSession": "London",
            "bars": synthetic_bars(count),
            "terminalPath": "C:\\private\\terminal.exe",
        },
    }


def news_mission(snapshot_id: str) -> dict:
    return {
        "id": "mission-news-1",
        "owner": "codex_mcp_operator",
        "status": "completed",
        "completedAt": "2026-08-01T09:59:00+00:00",
        "analysisContext": {
            "kind": "ai_trade_council_vote",
            "roleId": "news",
        },
        "councilVote": {
            "schemaVersion": "ai-trade-council-vote-v3",
            "readOnly": True,
            "snapshotId": snapshot_id,
            "agentId": "codex_mcp_operator",
            "roleId": "news",
            "decision": "HOLD",
            "confidence": 72,
            "eventRisk": "HOLD",
            "horizonBars": 2,
            "validUntilBarTime": 1_700_200_000,
            "observations": ["ข่าวสำคัญใกล้ประกาศ"],
            "warnings": ["รอความผันผวนลดลง"],
            "evidence": [{
                "label": "ข่าวเศรษฐกิจ",
                "sourceUrl": "https://www.reuters.com/markets/",
                "observedAt": "2026-08-01T09:58:00+00:00",
            }],
            "newsEvidence": {
                "fresh": True,
                "distinctDomains": 2,
                "requiredDistinctDomains": 2,
                "reasonCodes": [],
            },
        },
    }


class AiTradeCouncilDeepAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        with self.bridge.AI_TRADE_COUNCIL_ANALYSIS_CACHE_LOCK:
            self.bridge.AI_TRADE_COUNCIL_ANALYSIS_CACHE.clear()

    def build(self, model: dict) -> dict:
        snapshot_id = model["chartSnapshot"]["snapshotId"]
        with mock.patch.object(
            self.bridge,
            "load_missions",
            return_value=[news_mission(snapshot_id)],
        ):
            return self.bridge._ai_trade_council_deep_analysis_from_snapshot(
                model
            )

    def test_ready_snapshot_is_warmed_on_500_and_sliced_to_300(self) -> None:
        model = snapshot_model()
        result = self.build(model)
        bars = model["chartSnapshot"]["bars"]
        full_technical = self.bridge._technical_indicator_snapshot_uncached(bars)

        self.assertTrue(result["available"])
        self.assertEqual(result["status"], "ready")
        self.assertTrue(result["fresh"])
        self.assertTrue(result["decisionEligible"])
        self.assertEqual(result["sourceBarCount"], 500)
        self.assertEqual(result["analysisBarCount"], 300)
        self.assertEqual(result["warmupBarsUsed"], 200)
        self.assertEqual(len(result["bars"]), 300)
        self.assertEqual(len(result["technicalIndicators"]["series"]), 300)
        first = result["technicalIndicators"]["series"][0]
        self.assertEqual(first["time"], bars[200]["time"])
        self.assertEqual(first["sma200"], full_technical["series"][200]["sma200"])
        self.assertEqual(first["ema200"], full_technical["series"][200]["ema200"])
        self.assertIsNotNone(first["sma200"])
        self.assertIsNotNone(first["ema200"])
        self.assertEqual(
            tuple(first),
            self.bridge.AI_TRADE_COUNCIL_TECHNICAL_SERIES_FIELDS,
        )
        price_action = result["priceActionFeatures"]
        self.assertEqual(price_action["barCount"], 300)
        self.assertIn("trendlines", price_action)
        self.assertIn("fibonacci", price_action)
        self.assertIn("rsi", price_action["divergences"])
        self.assertIn("macd", price_action["divergences"])
        self.assertTrue(result["news"]["usableForCurrentSnapshot"])

        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("terminalPath", serialized)
        self.assertNotIn("accountLogin", serialized)
        self.assertNotIn("C:\\private", serialized)

    def test_insufficient_source_bars_fails_closed(self) -> None:
        result = self.build(snapshot_model(count=499))
        self.assertFalse(result["available"])
        self.assertFalse(result["fresh"])
        self.assertFalse(result["decisionEligible"])
        self.assertEqual(result["status"], "insufficient_closed_bars")
        self.assertEqual(
            result["reasonCode"],
            "minimum_500_closed_bars_required",
        )
        self.assertEqual(result["sourceBarCount"], 499)
        self.assertEqual(result["analysisBarCount"], 0)
        self.assertEqual(result["bars"], [])

    def test_stale_snapshot_remains_inspectable_but_not_decision_eligible(self) -> None:
        model = snapshot_model(status="stale")
        result = self.build(model)
        self.assertTrue(result["available"])
        self.assertEqual(result["status"], "stale")
        self.assertEqual(result["reasonCode"], "snapshot_stale")
        self.assertFalse(result["fresh"])
        self.assertFalse(result["decisionEligible"])
        self.assertFalse(result["snapshot"]["sourceAvailable"])
        self.assertEqual(result["snapshot"]["sourceStatus"], "stale")
        self.assertEqual(
            result["snapshot"]["sourceReasonCode"],
            "snapshot_stale",
        )
        self.assertEqual(len(result["bars"]), 300)

    def test_latest_news_is_visible_but_snapshot_mismatch_is_explicit(self) -> None:
        model = snapshot_model(snapshot_id="b" * 64)
        with mock.patch.object(
            self.bridge,
            "load_missions",
            return_value=[news_mission("c" * 64)],
        ):
            result = self.bridge._ai_trade_council_deep_analysis_from_snapshot(
                model
            )
        self.assertTrue(result["news"]["available"])
        self.assertFalse(result["news"]["usableForCurrentSnapshot"])
        self.assertEqual(result["news"]["reasonCode"], "snapshot_mismatch")

    def test_package_is_immutable_relative_hashed_and_reusable(self) -> None:
        deep = self.build(snapshot_model(status="stale"))
        with tempfile.TemporaryDirectory() as temporary:
            temp_root = Path(temporary)
            workspace = temp_root / "workspace"
            package_root = workspace / "ai-trade-council" / "deep-analysis"
            runtime = temp_root / "runtime"
            reports = runtime / "reports"
            audit = runtime / "bridge-audit.jsonl"
            patches = (
                mock.patch.object(
                    self.bridge,
                    "AI_TRADE_COUNCIL_WORKSPACE_DIR",
                    workspace,
                ),
                mock.patch.object(
                    self.bridge,
                    "AI_TRADE_COUNCIL_DEEP_ANALYSIS_DIR",
                    package_root,
                ),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime),
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", reports),
                mock.patch.object(self.bridge, "AUDIT_PATH", audit),
                mock.patch.object(
                    self.bridge,
                    "ai_trade_council_deep_analysis_read_model",
                    side_effect=lambda: copy.deepcopy(deep),
                ),
            )
            for patcher in patches:
                patcher.start()
            self.addCleanup(lambda: [patcher.stop() for patcher in reversed(patches)])

            first = self.bridge.create_ai_trade_council_deep_analysis_package({
                "snapshotId": deep["snapshot"]["snapshotId"],
            })
            second = self.bridge.create_ai_trade_council_deep_analysis_package({
                "snapshotId": deep["snapshot"]["snapshotId"],
            })

            self.assertTrue(first["ok"])
            self.assertTrue(first["package"]["created"])
            self.assertFalse(second["package"]["created"])
            self.assertFalse(first["package"]["fresh"])
            self.assertFalse(first["package"]["decisionEligible"])
            self.assertEqual(first["package"]["sourceStatus"], "stale")
            self.assertEqual(len(first["package"]["files"]), 5)
            expected_names = {
                "manifest.json",
                "bars-300.csv",
                "technical-300.csv",
                "price-action.json",
                "local-summary.json",
            }
            self.assertEqual(
                {item["name"] for item in first["package"]["files"]},
                expected_names,
            )
            package_dir = workspace / first["package"]["workspaceRelativeDirectory"]
            for record in first["package"]["files"]:
                self.assertFalse(Path(record["path"]).is_absolute())
                content = (package_dir / record["name"]).read_bytes()
                self.assertEqual(hashlib.sha256(content).hexdigest(), record["sha256"])
                self.assertEqual(len(content), record["bytes"])

            bars_csv = list(csv.reader(io.StringIO(
                (package_dir / "bars-300.csv").read_text(encoding="utf-8")
            )))
            technical_csv = list(csv.reader(io.StringIO(
                (package_dir / "technical-300.csv").read_text(encoding="utf-8")
            )))
            self.assertEqual(len(bars_csv), 301)
            self.assertEqual(len(technical_csv), 301)
            self.assertEqual(
                tuple(technical_csv[0]),
                self.bridge.AI_TRADE_COUNCIL_TECHNICAL_SERIES_FIELDS,
            )
            manifest = json.loads(
                (package_dir / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertTrue(manifest["immutable"])
            self.assertFalse(manifest["fresh"])
            self.assertFalse(manifest["decisionEligible"])
            self.assertTrue(audit.is_file())
            audit_events = [
                json.loads(line)
                for line in audit.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(len(audit_events), 2)
            self.assertEqual(
                audit_events[0]["type"],
                "ai_trade_council.deep_analysis_package_created",
            )
            self.assertEqual(
                audit_events[1]["type"],
                "ai_trade_council.deep_analysis_package_reused",
            )

            tampered_path = package_dir / "bars-300.csv"
            tampered_path.write_bytes(tampered_path.read_bytes() + b"tampered\n")
            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge.create_ai_trade_council_deep_analysis_package({
                    "snapshotId": deep["snapshot"]["snapshotId"],
                })

    def test_routes_are_dedicated_and_not_part_of_status_poll(self) -> None:
        get_source = inspect.getsource(self.bridge.BridgeHandler._do_GET_guarded)
        post_source = inspect.getsource(self.bridge.BridgeHandler.do_POST)
        status_source = inspect.getsource(
            self.bridge.ai_trade_council_status_read_model
        )
        self.assertIn('path == "/api/ai-trade-council/deep-analysis"', get_source)
        self.assertIn(
            'path == "/api/ai-trade-council/deep-analysis/package"',
            post_source,
        )
        self.assertNotIn("deep_analysis", status_source)


if __name__ == "__main__":
    unittest.main()
