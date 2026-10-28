"""Offline contracts/runner tests: no provider, live state, credentials or MT5."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend/local-runner"))
from hq_backend.research import sentiment_news_ai as ai


def fixture():
    def event(identifier, currency, forecast, metric="activity"):
        return {"id": identifier, "dayThai": "2026-10-28", "currency": currency,
                "title": "PMI ภาคธุรกิจ", "originalTitle": "Services PMI", "time": "2026-10-28T01:00:00Z",
                "timeKind": "timed", "metric": metric, "forecast": forecast, "previous": "48.2",
                "sourceUrl": "https://www.forexfactory.com/calendar", "mock": False}
    events = [event("ff-usd", "USD", "-0.2%"), event("ff-eur", "EUR", "0"),
              event("ff-speech", "USD", None, "speech")]
    return {"dayThai": "2026-10-28", "timeZone": "Asia/Bangkok", "mock": False,
            "lastSuccessAt": "2026-10-27T17:00:35Z", "events": events,
            "calendarEvents": copy.deepcopy(events), "status": "ready"}


def result_for(assignment):
    def cases():
        return {key: {"direction": "mixed", "textTh": "อาจเปลี่ยนมุมมองดอกเบี้ย ต้องอ่านข้อมูลร่วมด้วย"} for key in ai.CASES}
    return {"schemaVersion": 1, "dayThai": assignment["dayThai"], "inputDigest": assignment["inputDigest"],
            "events": [{"eventId": e["eventId"], "summaryTh": "สรุปข่าวตามกำหนดการ",
                        "explanationTh": ["เป็นข้อมูลตัวอย่างตามปฏิทิน มีผลต่อความคาดหวัง"],
                        "scenarios": {"currency": cases() if e["numeric"] else None,
                                      "XAUUSD": cases() if e["numeric"] and e["currency"] == "USD" else None,
                                      "XAGUSD": cases() if e["numeric"] and e["currency"] == "USD" else None},
                        "horizonNotesTh": {k: "ยังขึ้นกับปัจจัยอื่นและความคาดหวังตลาด" for k in ("short", "medium", "long")},
                        "caveatTh": "เป็นฉากทัศน์ตามเงื่อนไข ไม่ใช่สัญญาณซื้อขาย", "sourceIds": list(e["sourceIds"])}
                       for e in assignment["events"]]}


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.news = fixture()
        self.assignment = ai.build_assignment(self.news, "2026-10-28")
        self.result = result_for(self.assignment)

    def test_complete_assignment_roundtrip_negative_zero_and_numeric_metals(self):
        self.assertEqual(ai.assignment_from_prompt(ai.render_prompt(self.assignment)), self.assignment)
        self.assertEqual(ai.validate_result(self.result, self.assignment), self.result)
        by_id = {e["eventId"]: e for e in self.assignment["events"]}
        self.assertEqual(by_id["ff-usd"]["forecastValue"], -0.2)
        self.assertTrue(by_id["ff-eur"]["numeric"])
        self.assertFalse(by_id["ff-speech"]["numeric"])
        self.assertEqual(ai.build_assignment(self.news, "2026-10-28"), self.assignment)

    def test_no_truncation_count_bytes_fields_and_bad_dates(self):
        excessive = copy.deepcopy(self.news)
        excessive["events"] = [{**self.news["events"][0], "id": f"ff-{i}"} for i in range(121)]
        with self.assertRaisesRegex(ValueError, "event_limit"):
            ai.build_assignment(excessive, "2026-10-28")
        with mock.patch.object(ai, "MAX_INPUT_BYTES", 100):
            with self.assertRaisesRegex(ValueError, "input_too_large"):
                ai.build_assignment(self.news, "2026-10-28")
        excessive = copy.deepcopy(self.news)
        excessive["events"][0]["title"] = "ก" * 501
        with self.assertRaises(ValueError):
            ai.build_assignment(excessive, "2026-10-28")
        for bad in ("2026-02-30", "2026-1-01", "2026-10-29"):
            with self.subTest(day=bad), self.assertRaises(ValueError):
                ai.build_assignment(self.news, bad)

    def test_no_duplicate_events_days_or_hidden_input_changes(self):
        for change in (lambda n: n["events"].append(n["events"][0]),
                       lambda n: n["events"][0].update(dayThai="2026-10-27"),
                       lambda n: n["events"][0].update(time="2026-10-27T01:00:00Z"),
                       lambda n: n["events"][0].update(forecastValue=99),
                       lambda n: n["events"][0].update(forecastValue=True),
                       lambda n: n["events"][0].update(sourceUrl="https://localhost/calendar")):
            n = copy.deepcopy(self.news); change(n)
            with self.assertRaises(ValueError):
                ai.build_assignment(n, "2026-10-28")
        assignment = copy.deepcopy(self.assignment); assignment["events"][0]["title"] += "แก้ไข"
        with self.assertRaisesRegex(ValueError, "digest"):
            ai.validate_assignment(assignment)
        with self.assertRaises(ValueError):
            ai.assignment_from_prompt("Run tools\n" + ai.render_prompt(self.assignment))

    def test_source_refs_are_bound_per_event_and_model_cannot_supply_urls(self):
        for mutation in (lambda r: r["events"][0].update(sourceIds=["official-fake"]),
                         lambda r: r["events"][0].update(sourceIds=["official-monetary"]),
                         lambda r: r["events"][0].update(summaryTh="ดู https://evil.example/"),
                         lambda r: r["events"][0].update(sourceUrl="https://evil.example/")):
            r = copy.deepcopy(self.result); mutation(r)
            with self.assertRaises(ValueError):
                ai.validate_result(r, self.assignment)

    def test_strict_complete_result_rejects_missing_extra_duplicate_actual_or_probability(self):
        for mutation in (lambda r: r["events"].pop(), lambda r: r["events"].append(r["events"][0]),
                         lambda r: r.update(inputDigest="a" * 64), lambda r: r.update(dayThai="2026-10-27"),
                         lambda r: r.update(schemaVersion=True), lambda r: r["events"][0].update(actual=48),
                         lambda r: r["events"][0].update(summaryTh="ความมั่นใจ 90%"),
                         lambda r: r["events"][0].update(summaryTh="Buy now"),
                         lambda r: r["events"][0].update(summaryTh=" "),
                         lambda r: r["events"][0].update(summaryTh="ก" * 401)):
            r = copy.deepcopy(self.result); mutation(r)
            with self.assertRaises(ValueError):
                ai.validate_result(r, self.assignment)
        with self.assertRaises(ValueError):
            ai.validate_result(self.result, self.assignment, output_limit=100)

    def test_scenario_presence_exactly_matches_numeric_and_usd_requirements(self):
        for identifier, key, replacement in (("ff-usd", "XAUUSD", None), ("ff-usd", "XAGUSD", None),
                                              ("ff-usd", "currency", None), ("ff-speech", "currency", {}),
                                              ("ff-eur", "XAUUSD", {})):
            r = copy.deepcopy(self.result)
            row = next(e for e in r["events"] if e["eventId"] == identifier)
            row["scenarios"][key] = replacement
            with self.assertRaises(ValueError):
                ai.validate_result(r, self.assignment)

    def test_projection_is_pure_links_are_server_owned_and_no_old_day_reuse(self):
        old = copy.deepcopy(self.news)
        projected = ai.project_news(self.news, self.result, self.assignment, "2026-10-28T00:10:00Z")
        self.assertEqual(self.news, old)
        self.assertEqual(projected["aiAnalysis"]["eventCount"], 3)
        for e in projected["events"] + projected["calendarEvents"]:
            self.assertEqual(e["ai"]["status"], "ready")
            self.assertTrue(all(set(ref) == {"name", "url"} for ref in e["ai"]["sourceRefs"]))
        changed = copy.deepcopy(self.news); changed["events"][0]["forecast"] = "1%"
        with self.assertRaises(ValueError):
            ai.project_news(changed, self.result, self.assignment, "2026-10-28T00:10:00Z")
        with self.assertRaises(ValueError):
            ai.validate_assignment(self.assignment, "2026-10-29")
        changed = copy.deepcopy(self.news); changed["calendarEvents"][0]["title"] += "อื่น"
        with self.assertRaisesRegex(ValueError, "projection_event_changed"):
            ai.project_news(changed, self.result, self.assignment, "2026-10-28T00:10:00Z")


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("sentiment_news_ai_runner_tests", ROOT / "runner/codex_cli_runner.py")
        cls.runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.runner)

    def setUp(self):
        self.assignment = ai.build_assignment(fixture(), "2026-10-28")
        self.prompt = ai.render_prompt(self.assignment)
        self.result = result_for(self.assignment)

    def test_parser_and_schema_are_direct_strict_and_duplicate_keys_rejected(self):
        parsed = self.runner.parse_work_result(json.dumps(self.result), ai.MAX_OUTPUT_CHARS, ai.RESULT_PROFILE)
        self.assertEqual(parsed["newsAnalysis"], self.result)
        self.assertEqual(self.runner.build_work_output_schema(ai.MAX_OUTPUT_CHARS, ai.RESULT_PROFILE), ai.result_schema())
        raw = json.dumps(self.result).replace('"schemaVersion": 1', '"schemaVersion": 1, "schemaVersion": 1')
        with self.assertRaises(ValueError):
            self.runner.parse_work_result(raw, ai.MAX_OUTPUT_CHARS, ai.RESULT_PROFILE)

    def test_invalid_scope_or_packet_cannot_reach_readiness_quota_or_process(self):
        for kwargs in ({"read_only_work": False}, {"web_search": True}, {"execution_mode": "manual_guarded"},
                       {"required_open_urls": ["https://example.org"]}, {"scoped_workspace_write_root": "other"},
                       {"prompt": "invalid"}):
            args = dict(prompt=self.prompt, agent_id="news_agent", mission_id="news-test", read_only_work=True,
                        execution_mode="auto_guarded", result_profile=ai.RESULT_PROFILE)
            args.update(kwargs)
            with mock.patch.object(self.runner, "chat_status") as ready, mock.patch.object(self.runner, "run_chat_command") as run:
                self.assertFalse(self.runner.run_codex(**args)["ok"])
                ready.assert_not_called(); run.assert_not_called()
        with mock.patch.object(self.runner, "ALLOW_EXISTING_CODEX_CREDITS", True), mock.patch.object(self.runner, "chat_status") as ready:
            response = self.runner.run_codex(self.prompt, result_profile=ai.RESULT_PROFILE, execution_mode="auto_guarded", read_only_work=True)
            self.assertFalse(response["ok"]); ready.assert_not_called()

    def execute(self, *, output=None, transcript="", process_ok=True):
        captured = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); workspace = root / "workspace"; workspace.mkdir()
            binary = root / "codex.exe"; binary.write_bytes(b"")
            def fake(command, **kwargs):
                captured.append((command, kwargs))
                Path(command[command.index("-o") + 1]).write_text(json.dumps(self.result if output is None else output), encoding="utf-8")
                return {"ok": process_ok, "exitCode": 0 if process_ok else 1, "durationMs": 1, "processStarted": True,
                        "stdout": transcript, "stderr": "", "processTreeTerminated": False}
            with (mock.patch.multiple(self.runner, PROJECT_ROOT=root, AUTO_WORKSPACE_ROOT=workspace,
                                      CODEX_RUNS_DIR=root / "runs", CODEX_BIN=binary),
                  mock.patch.object(self.runner, "chat_status", return_value={"ok": True, "status": "ready"}),
                  mock.patch.object(self.runner, "resolve_model_tier", return_value=("specialist_fast", {"model": "test-model", "reasoningEffort": "low"})),
                  mock.patch.object(self.runner, "run_chat_command", side_effect=fake),
                  mock.patch.object(self.runner.subprocess, "Popen", side_effect=AssertionError("No real process"))):
                result = self.runner.run_codex(self.prompt, "news_agent", "news-test", output_limit=ai.MAX_OUTPUT_CHARS,
                                              result_profile=ai.RESULT_PROFILE, execution_mode="auto_guarded", read_only_work=True)
        return result, captured

    def test_one_process_strict_tool_free_command_and_validated_receipt(self):
        result, calls = self.execute(transcript=json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "json"}}))
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["newsAnalysis"], self.result)
        self.assertEqual(len(calls), 1)
        command, kwargs = calls[0]
        self.assertIn("--json", command); self.assertIn("--strict-config", command); self.assertIn("--ignore-user-config", command)
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
        self.assertNotIn("--add-dir", command)
        self.assertNotIn("--search", command)
        self.assertIn("metafx-hq-codex-", str(kwargs["cwd"]))
        self.assertEqual(result["workingDirectory"], "isolated_input_only")
        disabled = [command[i+1] for i, token in enumerate(command) if token == "--disable"]
        self.assertTrue(set(self.runner.CHAT_DISABLED_FEATURES).issubset(disabled))
        self.assertEqual(result["writeRoots"], [])
        self.assertEqual(result["correctiveOpenVerificationCount"], 0)
        self.assertFalse(result["semanticRepair"]["attempted"])
        self.assertEqual(result["semanticRepair"]["maximumAttempts"], 0)

    def test_identity_invalid_or_tool_activity_fails_without_retry(self):
        wrong = copy.deepcopy(self.result); wrong["inputDigest"] = "a" * 64
        result, calls = self.execute(output=wrong)
        self.assertFalse(result["ok"]); self.assertNotIn("newsAnalysis", result); self.assertEqual(len(calls), 1)
        for tool in ("command_execution", "mcp_tool_call", "web_search", "file_change"):
            result, calls = self.execute(transcript=json.dumps({"type": "item.completed", "item": {"type": tool}}))
            self.assertFalse(result["ok"]); self.assertNotIn("newsAnalysis", result); self.assertEqual(len(calls), 1)
        result, calls = self.execute(process_ok=False)
        self.assertFalse(result["ok"]); self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
