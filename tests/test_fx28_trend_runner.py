"""Strict FX28 Runner boundaries; all processes and web events are fixtures."""
import copy
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_runner(name="fx28_test_runner"):
    spec = importlib.util.spec_from_file_location(name, ROOT / "runner/codex_cli_runner.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def market_snapshot(engine, *, pair_count=28):
    now = datetime(2026, 10, 23, 4, tzinfo=timezone.utc)
    pairs = []
    for pair in engine.FX_PAIRS[:pair_count]:
        series = {}
        for frame, seconds in engine.SECONDS.items():
            end = int(now.timestamp()) // seconds * seconds
            series[frame] = [{"time": end - (60 - index) * seconds,
                              "open": 1 + index / 1000, "high": 1.002 + index / 1000,
                              "low": 0.998 + index / 1000, "close": 1.001 + index / 1000,
                              "tick_volume": 100 + index} for index in range(60)]
        pairs.append({"pair": pair, "brokerSymbol": pair + ".m", "series": series})
    return {"schemaVersion": "fx28-market-snapshot-v1", "collectedAt": engine.iso(now),
            "source": {"kind": "mt5_closed_bars", "clock": {"serverOffsetSeconds": 0}}, "pairs": pairs}, now


def assignment_fixture(engine, *, news=False, pair_count=28):
    snapshot, now = market_snapshot(engine, pair_count=pair_count)
    model = engine.build_read_model(snapshot, now=now)
    sources = [{"url": "https://www.ecb.europa.eu/press/pr/date/2026/html/index.en.html", "title": "ECB statement"}] if news else []
    return engine.make_assignment(model, "2026-10-23", sources)


def explanation_fixture(engine, assignment, *, news=False):
    ids = {row["id"] for row in assignment["sourceRefs"]}
    return {**{key: assignment[key] for key in ("snapshotId", "snapshotDigest", "marketDate")},
            "summaryTh": "สรุปจากแท่งปิดที่ตรวจสอบได้ โดยไม่ส่งคำสั่งซื้อขาย",
            "pairExplanations": [{"pair": pair, **{
                name: {"reasonTh": "อธิบายจากข้อมูลแท่งราคาปิดที่ให้มา" if any(f"price:{pair}:{frame}" in ids for frame in frames) else "ข้อมูลแท่งปิดไม่ครบ จึงยังสรุปทิศทางไม่ได้",
                       "sourceRefs": [f"price:{pair}:{frame}" for frame in frames if f"price:{pair}:{frame}" in ids]}
                for name, frames in engine.HORIZONS.items()}} for pair in engine.FX_PAIRS],
            "newsContext": [{"sourceRef": row["id"], "summaryTh": "ข้อมูลประกอบจากประกาศของธนาคารกลาง"}
                            for row in assignment["sourceRefs"] if news and row["kind"] == "news"],
            "limitations": ["Tick volume เป็นกิจกรรมราคาเฉพาะโบรกเกอร์ ไม่ใช่ปริมาณซื้อขายทั้งตลาด"]}


class Fx28TrendRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_runner()
        cls.engine = cls.runner.fx_trend

    def run_fixture(self, assignment, payload, stdout="", *, web_search=True, **overrides):
        calls = []
        def fake_chat(command, **kwargs):
            calls.append((command, kwargs))
            Path(command[command.index("-o") + 1]).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return {"ok": True, "exitCode": 0, "durationMs": 1, "processStarted": True,
                    "processTreeTerminated": False, "stdout": stdout, "stderr": ""}
        params = dict(execution_mode="auto_guarded", read_only_work=True, web_search=web_search,
                      result_profile=self.runner.FX_TREND_RESULT_PROFILE, output_limit=20000)
        params.update(overrides)
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(self.runner, "CODEX_RUNS_DIR", Path(folder)), \
             mock.patch.object(self.runner, "chat_status", return_value={"ok": True, "status": "ready"}), \
             mock.patch.object(self.runner, "run_chat_command", side_effect=fake_chat), \
             mock.patch.object(self.runner, "complete_radar_evidence_open_urls", side_effect=AssertionError("No children")), \
             mock.patch.object(self.runner, "complete_trading_system_research_required_open_urls", side_effect=AssertionError("No children")):
            result = self.runner.run_codex(self.engine.render_prompt(assignment), "codex_mcp_operator", "mission-fx28-fixture", **params)
        return result, calls

    def test_full_28_pair_assignment_and_response_fit_without_omission(self):
        assignment = assignment_fixture(self.engine, news=True)
        payload = explanation_fixture(self.engine, assignment)
        prompt = self.engine.render_prompt(assignment)
        self.assertLessEqual(len(prompt), 20000)
        self.assertIn("short=M15+H1, medium=H1+H4+D1, long=D1+W1", prompt)
        self.assertEqual(self.runner.bound_mission_prompt(prompt, self.runner.FX_TREND_RESULT_PROFILE), prompt)
        self.assertEqual(len(assignment["rows"]), 28)
        self.assertEqual(len(assignment["sourceRefs"]), 141)
        parsed = self.runner.parse_work_result(json.dumps(payload, ensure_ascii=False), 20000, self.runner.FX_TREND_RESULT_PROFILE)
        self.assertEqual(json.loads(parsed["contractFields"][0]["value"]), payload)

    def test_one_read_only_run_can_complete_price_explanations_without_web_news(self):
        assignment = assignment_fixture(self.engine)
        payload = explanation_fixture(self.engine, assignment)
        before = copy.deepcopy(payload)
        for web_search in (False, True):
            with self.subTest(web_search=web_search):
                result, calls = self.run_fixture(assignment, payload, web_search=web_search)
                self.assertTrue(result["ok"], result)
                self.assertEqual(len(calls), 1)
                command = calls[0][0]
                self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
                self.assertIn("shell_tool", command)
                self.assertEqual(result["correctiveOpenVerificationCount"], 0)
                self.assertEqual(result["evidence"], [])
                self.assertFalse(result["webSearchEvidenceVerified"])
                self.assertEqual(json.loads(result["contractFields"][0]["value"]), payload)
                self.assertNotIn("fxTrendAnalysis", result, "Do not duplicate the transport payload")
        self.assertEqual(payload, before)

    def test_news_requires_completed_exact_main_open_and_never_child_fallback(self):
        assignment = assignment_fixture(self.engine, news=True)
        payload = explanation_fixture(self.engine, assignment, news=True)
        url = next(row["url"] for row in assignment["sourceRefs"] if row["kind"] == "news")
        for event_type, opened_url, expected in (("item.completed", url, True), ("item.started", url, False),
                                                 ("item.completed", "https://example.org/unrelated", False)):
            with self.subTest(event_type=event_type, opened_url=opened_url):
                event = json.dumps({"type": event_type, "item": {"id": "fx-open", "type": "web_search",
                                  "action": {"type": "open_page", "url": opened_url}}})
                result, calls = self.run_fixture(assignment, payload, event)
                self.assertEqual(result["ok"], expected, result)
                self.assertEqual(len(calls), 1)
                if expected:
                    self.assertTrue(result["webSearchEvidenceVerified"])
                    self.assertEqual(result["evidence"][0]["url"], url)
        result, _ = self.run_fixture(assignment, payload, web_search=False)
        self.assertFalse(result["ok"])

    def test_scope_and_unbound_prompt_fail_before_spawn(self):
        assignment = assignment_fixture(self.engine)
        payload = explanation_fixture(self.engine, assignment)
        for changed in ({"read_only_work": False}, {"execution_mode": "manual_guarded"},
                        {"required_open_urls": ["https://example.org/source"]}, {"council_snapshot_id": "council-other"}):
            with self.subTest(changed=changed):
                result, calls = self.run_fixture(assignment, payload, **changed)
                self.assertFalse(result["ok"])
                self.assertFalse(calls)
                self.assertFalse(result["processStarted"])
        with mock.patch.object(self.runner, "run_chat_command") as run:
            result = self.runner.run_codex("unbound request", "codex_mcp_operator", "mission-fx28-invalid",
                     execution_mode="auto_guarded", read_only_work=True, result_profile=self.runner.FX_TREND_RESULT_PROFILE)
        self.assertFalse(result["ok"])
        run.assert_not_called()

    def test_binding_pair_source_and_price_override_tampering_fail_closed(self):
        assignment = assignment_fixture(self.engine)
        base = explanation_fixture(self.engine, assignment)
        for tamper in ("digest", "date", "duplicate_pair", "missing_pair", "foreign_source", "missing_source", "bias", "price", "confidence"):
            with self.subTest(tamper=tamper):
                payload = copy.deepcopy(base)
                if tamper == "digest": payload["snapshotDigest"] = "0" * 64
                elif tamper == "date": payload["marketDate"] = "2026-10-22"
                elif tamper == "duplicate_pair": payload["pairExplanations"][1] = copy.deepcopy(payload["pairExplanations"][0])
                elif tamper == "missing_pair": payload["pairExplanations"].pop()
                elif tamper == "foreign_source": payload["pairExplanations"][0]["short"]["sourceRefs"][0] = "price:USDJPY:M15"
                elif tamper == "missing_source": payload["pairExplanations"][0]["short"]["sourceRefs"] = []
                else: payload["pairExplanations"][0]["short"][tamper] = 42
                result, calls = self.run_fixture(assignment, payload)
                self.assertFalse(result["ok"], result)
                self.assertEqual(len(calls), 1)

    def test_missing_pair_prices_keep_28_explanations_and_no_fabricated_refs(self):
        assignment = assignment_fixture(self.engine, pair_count=1)
        payload = explanation_fixture(self.engine, assignment)
        result, _ = self.run_fixture(assignment, payload)
        self.assertTrue(result["ok"], result)
        self.assertEqual(len(payload["pairExplanations"]), 28)
        self.assertEqual(payload["pairExplanations"][1]["short"]["sourceRefs"], [])

    def test_duplicate_json_keys_and_oversized_results_are_rejected(self):
        assignment = assignment_fixture(self.engine)
        payload = explanation_fixture(self.engine, assignment)
        raw = json.dumps(payload, ensure_ascii=False)
        duplicate = raw[:-1] + ',"summaryTh":"duplicate"}'
        with self.assertRaises(ValueError):
            self.runner.parse_work_result(duplicate, 20000, self.runner.FX_TREND_RESULT_PROFILE)
        payload["pairExplanations"][0]["short"]["reasonTh"] = "ก" * 121
        with self.assertRaises(ValueError):
            self.runner.parse_work_result(json.dumps(payload, ensure_ascii=False), 20000, self.runner.FX_TREND_RESULT_PROFILE)

    def test_hidden_news_reference_cannot_bypass_native_open_verification(self):
        assignment = assignment_fixture(self.engine, news=True)
        payload = explanation_fixture(self.engine, assignment)
        news_id = next(row["id"] for row in assignment["sourceRefs"] if row["kind"] == "news")
        payload["pairExplanations"][0]["short"]["sourceRefs"].append(news_id)
        result, calls = self.run_fixture(assignment, payload)
        self.assertFalse(result["ok"], result)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
