"""V2 native research accepts 0..3, never a fabricated/failed empty success."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


class RadarV2RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / "runner/codex_cli_runner.py"
        spec = importlib.util.spec_from_file_location("radar_v2_test_runner", path)
        cls.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.runner)

    def payload(self, count=0):
        urls = [f"https://github.com/example/public-tool-{index}" for index in range(count)]
        return {
            "status": "completed", "summary": "Checked public sources; actual new items only",
            "findings": [], "nextSteps": [], "blockedCapability": "",
            "evidence": [{"label": f"Source {index}", "url": url, "note": "Opened source"}
                         for index, url in enumerate(urls)],
            "contractFields": [{"field": "entries", "value": json.dumps(
                [{"sourceUrl": url} for url in urls])}],
            "evidenceKinds": list(self.runner.PROFILE_CONTRACT_REQUIREMENTS[
                self.runner.RADAR_V2_RESULT_PROFILE]["evidenceKinds"]),
        }

    @staticmethod
    def native_events(urls=(), *, search=True, search_type="item.completed", error=None):
        events = []
        if search:
            item = {"id": "query-native-1", "type": "web_search", "query": "public EA indicator technology",
                    "action": {"type": "search", "query": "public EA indicator technology"}}
            if error:
                item["error"] = error
            events.append({"type": search_type, "item": item})
        events.extend({"type": "item.completed", "item": {
            "id": f"open-native-{index}", "type": "web_search", "query": url,
            "action": {"type": "open_page", "url": url}}} for index, url in enumerate(urls))
        return "\n".join(json.dumps(item) for item in events)

    def run_payload(self, payload, stdout):
        calls = []
        def fake_chat(command, **kwargs):
            calls.append(command)
            Path(command[command.index("-o") + 1]).write_text(json.dumps(payload), encoding="utf-8")
            return {"ok": True, "exitCode": 0, "durationMs": 1, "processStarted": True,
                    "processTreeTerminated": False, "stdout": stdout, "stderr": ""}
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(
            self.runner, "CODEX_RUNS_DIR", Path(folder)
        ), mock.patch.object(self.runner, "chat_status", return_value={"ok": True, "status": "ready"}), \
                mock.patch.object(self.runner, "run_chat_command", side_effect=fake_chat), \
                mock.patch.object(self.runner, "complete_radar_evidence_open_urls",
                                  side_effect=AssertionError("v2 must never start legacy child verifiers")):
            result = self.runner.run_codex(
                'เงื่อนไขจากผู้ใช้: {"maxItems":3,"radarPublicationVersion":2}',
                "codex_mcp_operator", "mission-radar-v2-test", output_limit=20000,
                execution_mode="auto_guarded", web_search=True, read_only_work=True,
                result_profile=self.runner.RADAR_V2_RESULT_PROFILE,
            )
            manifests = list(Path(folder).glob("*.url-open-verification.json"))
            manifest = json.loads(manifests[0].read_text(encoding="utf-8")) if manifests else None
            if manifest:
                self.assertEqual(hashlib.sha256(manifests[0].read_bytes()).hexdigest(),
                                 result["correctiveOpenVerificationDigest"])
        self.assertEqual(len(calls), 1, "One admitted main process only")
        return result, manifest

    def test_zero_one_two_three_all_complete_with_real_native_evidence(self):
        for count in range(4):
            with self.subTest(count=count):
                payload = self.payload(count)
                result, manifest = self.run_payload(payload, self.native_events(
                    [row["url"] for row in payload["evidence"]]))
                self.assertTrue(result["ok"], result)
                self.assertTrue(result["webSearchEvidenceVerified"])
                self.assertEqual(manifest["requiredUrlCount"], count)
                self.assertEqual(manifest["completedSearchCount"], 1)
                self.assertEqual(manifest["mainRequiredOpenIndexes"], list(range(count)))
                self.assertEqual(result["correctiveOpenVerificationCount"], 0)
                self.assertEqual(manifest["schemaVersion"], "metafx-radar-url-open-verification-v2")

    def test_empty_without_search_is_not_success(self):
        result, manifest = self.run_payload(self.payload(), "")
        self.assertFalse(result["ok"])
        self.assertIsNone(manifest)

    def test_started_only_search_is_not_empty_success(self):
        result, _ = self.run_payload(self.payload(), self.native_events(search_type="item.started"))
        self.assertFalse(result["ok"])

    def test_failed_search_is_not_empty_success(self):
        result, _ = self.run_payload(self.payload(), self.native_events(error="upstream unavailable"))
        self.assertFalse(result["ok"])

    def test_open_only_without_discovery_query_is_not_success(self):
        p = self.payload(1)
        result, _ = self.run_payload(p, self.native_events([p["evidence"][0]["url"]], search=False))
        self.assertFalse(result["ok"])

    def test_unopened_item_is_rejected_without_child_process(self):
        result, _ = self.run_payload(self.payload(1), self.native_events())
        self.assertFalse(result["ok"])

    def test_four_items_rejected_not_silently_truncated(self):
        p = self.payload(4)
        result, _ = self.run_payload(p, self.native_events([r["url"] for r in p["evidence"]]))
        self.assertFalse(result["ok"])
        self.assertIn("three-item", result["structuredOutputError"])

    def test_failed_open_is_not_accepted_as_source_proof(self):
        p = self.payload(1)
        events = [json.loads(line) for line in self.native_events([p["evidence"][0]["url"]]).splitlines()]
        events[-1]["item"]["error"] = "page unavailable"
        result, _ = self.run_payload(p, "\n".join(json.dumps(event) for event in events))
        self.assertFalse(result["ok"])

    def test_declared_technical_failure_stays_failure(self):
        p = self.payload()
        p["status"] = "failed"
        result, manifest = self.run_payload(p, self.native_events())
        self.assertFalse(result["ok"])
        self.assertEqual(result["workStatus"], "failed")
        self.assertIsNone(manifest)

    def test_bad_evidence_row_is_not_silently_dropped_to_zero(self):
        p = self.payload(1)
        p["evidence"][0]["url"] = "http://127.0.0.1/private"
        result, _ = self.run_payload(p, self.native_events())
        self.assertFalse(result["ok"])

    def test_mismatched_entries_rejected(self):
        p = self.payload(1)
        p["contractFields"][0]["value"] = "[]"
        result, _ = self.run_payload(p, self.native_events())
        self.assertFalse(result["ok"])

    def test_duplicate_contract_field_rejected(self):
        p = self.payload()
        p["contractFields"] *= 2
        result, _ = self.run_payload(p, self.native_events())
        self.assertFalse(result["ok"])

    def test_duplicate_kinds_rejected(self):
        p = self.payload()
        p["evidenceKinds"].append(p["evidenceKinds"][0])
        result, _ = self.run_payload(p, self.native_events())
        self.assertFalse(result["ok"])

    def test_time_lookup_is_not_search_proof(self):
        event = {"type": "item.completed", "item": {"id": "native-time", "type": "web_search",
                 "action": {"type": "search", "query": 'time: {"utc_offset":"+07:00"}'},
                 "query": 'time: {"utc_offset":"+07:00"}'}}
        self.assertEqual(self.runner.radar_v2_completed_search_events(json.dumps(event)), [])

    def test_duplicate_search_ids_not_double_counted(self):
        events = self.native_events()
        self.assertEqual(len(self.runner.radar_v2_completed_search_events(events + "\n" + events)), 1)

    def test_schema_accepts_zero_to_three_and_preserves_failure_status(self):
        schema = self.runner.build_work_output_schema(20000, self.runner.RADAR_V2_RESULT_PROFILE)
        self.assertEqual(schema["properties"]["evidence"]["minItems"], 0)
        self.assertEqual(schema["properties"]["evidence"]["maxItems"], 3)
        self.assertIn("failed", schema["properties"]["status"]["enum"])
        old = self.runner.build_work_output_schema(20000, "radar_website_tool", 6)
        self.assertEqual(old["properties"]["evidence"]["minItems"], 6)
        self.assertEqual(old["properties"]["evidence"]["maxItems"], 6)

    def test_scope_blocks_non_readonly_or_no_search_before_process(self):
        for options in ({"read_only_work": False}, {"web_search": False}, {"execution_mode": "manual_guarded"}):
            params = dict(execution_mode="auto_guarded", web_search=True, read_only_work=True)
            params.update(options)
            result = self.runner.run_codex("Search", result_profile=self.runner.RADAR_V2_RESULT_PROFILE, **params)
            self.assertEqual(result["status"], "radar_v2_scope_invalid")
            self.assertFalse(result["processStarted"])

    def test_prompt_has_maximum_not_fixed_count_and_category_choice(self):
        prompt = self.runner.build_prompt("Search", "codex_mcp_operator", "mission-v2", "specialist_balanced",
                    20000, execution_mode="auto_guarded", web_search=True, read_only_work=True,
                    result_profile=self.runner.RADAR_V2_RESULT_PROFILE)
        self.assertIn("at most three", prompt)
        self.assertIn("0, 1, 2 and 3", prompt)
        self.assertIn("any mix of EA, Indicator", prompt)
        self.assertNotIn("exactly six", prompt)
