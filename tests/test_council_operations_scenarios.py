"""Operational evidence fault scenarios; no live Bridge, provider or terminal.

Only temporary SQLite files and explicit aware fixture clocks are used. Public
readers must not manufacture successful analysis, repair stores or refresh data.
"""
from __future__ import annotations

import copy
import ast
import importlib.util
import json
import sys
import tempfile
import threading
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
OPERATIONS = ROOT / "backend" / "local-runner" / "hq_backend" / "operations"
NOW = datetime(2026, 10, 29, 2, 0, tzinfo=timezone.utc)


def load_operation(name):
    spec = importlib.util.spec_from_file_location(
        "hq_backend.operations._scenario_" + name, OPERATIONS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.path.insert(0, str(OPERATIONS.parents[1]))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def fixture_round():
    parent = {
        "id": "mission-fixture-parent", "status": "completed",
        "analysisContext": {"snapshotId": "a" * 64,
                            "snapshotArtifactDigest": "b" * 64},
    }
    children = [{
        "id": "mission-fixture-" + role, "parentMissionId": parent["id"],
        "status": "completed", "execution": {"processStarted": True},
        "analysisContext": {**parent["analysisContext"], "roleId": role},
        "councilVote": {"roleId": role, "snapshotId": "a" * 64,
                        "decision": "HOLD", "confidence": 81},
    } for role in ("technical", "price_action", "news")]
    return parent, children


def fixture_coverage(bar, **changes):
    return {"streamKey": "c" * 64, "closedBarTime": bar, "symbol": "XAUUSD",
            "timeframe": "H1", "status": "analyzed", "reasonCode": "council_round_terminal",
            "missionId": "mission-fixture-parent", "detectedAt": NOW.isoformat(),
            "completedAt": (NOW + timedelta(seconds=100)).isoformat(),
            "snapshotId": "a" * 64, "snapshotArtifactDigest": "b" * 64, **changes}


class CouncilOperationsJournalScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_operation("council_observability")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.journal = self.module.CouncilJournal(self.root / "new-runtime" / "operations.sqlite3")

    def events(self, now=NOW, **kwargs):
        return self.journal.read(now=now, **kwargs)["events"]

    def test_missing_reader_never_creates_runtime_or_observer_store(self):
        before = list(self.root.rglob("*"))
        for _ in range(3):
            model = self.journal.read(now=NOW)
            self.assertFalse(model["available"])
            self.assertEqual(model["reasonCode"], "observability_not_recorded")
        self.assertEqual(list(self.root.rglob("*")), before)

    def test_old_startup_gap_is_unknown_and_never_invents_candles(self):
        self.assertTrue(self.journal.observe(now=NOW, startup_id="startup-first"))
        restarted = self.module.CouncilJournal(self.journal.path)
        later = NOW + timedelta(days=10)
        self.assertTrue(restarted.observe(now=later, startup_id="startup-next"))
        self.assertTrue(restarted.gap(now=later, after_bar=1_700_000_000,
            before_bar=1_700_864_000, available_bars=120, symbol="XAUUSD", timeframe="H1"))
        model = restarted.read(now=later)
        self.assertEqual(model["heartbeat"]["status"], "observed")
        gaps = [event for event in model["events"] if event["type"] == "gap"]
        self.assertEqual({row["reasonCode"] for row in gaps},
                         {"observation_gap_unknown", "gap_history_unavailable"})
        self.assertTrue(all(row["certainty"] == "unknown" for row in gaps))
        self.assertTrue(all(row["evidence"]["aiRunAllowed"] is False for row in gaps))
        self.assertFalse(any(row["type"] == "bar" for row in model["events"]))
        self.assertFalse(any("missedBarCount" in row["evidence"] for row in gaps))

    def test_clean_shutdown_is_confirmed_but_does_not_claim_machine_was_off(self):
        self.journal.observe(now=NOW, startup_id="startup-first")
        self.journal.stopped(now=NOW + timedelta(seconds=15), startup_id="startup-first")
        stopped = self.journal.read(now=NOW + timedelta(seconds=16))
        self.assertEqual(stopped["heartbeat"]["status"], "stopped")
        self.journal.observe(now=NOW + timedelta(minutes=3), startup_id="startup-next")
        gaps = [row for row in self.events(NOW + timedelta(minutes=3)) if row["type"] == "gap"]
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["reasonCode"], "bridge_stopped_interval")
        self.assertEqual(gaps[0]["certainty"], "confirmed")
        self.assertEqual(gaps[0]["evidence"]["source"], "bridge_shutdown_receipt")
        self.assertNotIn("machineOff", gaps[0])

    def test_repeated_incident_is_coalesced_and_recovery_keeps_its_identity(self):
        for second in (0, 31, 62):
            self.journal.observe(now=NOW + timedelta(seconds=second), startup_id="startup-first",
                reason="quota_unavailable", blocked=True, evidence={"remainingPercent": None})
        before = self.journal.read(now=NOW + timedelta(seconds=63))
        active = before["incidents"]["active"]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["occurrences"], 3)
        self.journal.observe(now=NOW + timedelta(seconds=64), startup_id="startup-first")
        after = self.journal.read(now=NOW + timedelta(seconds=64))
        self.assertEqual(after["incidents"]["active"], [])
        self.assertEqual(len(after["incidents"]["recovered"]), 1)
        self.assertEqual(after["incidents"]["recovered"][0]["id"], active[0]["id"])
        self.assertEqual(after["incidents"]["recovered"][0]["status"], "recovered")

    def test_archive_preserves_more_than_hot_snapshot_and_pages_without_duplicates(self):
        records = [fixture_coverage(1_700_000_000 + index * 3600) for index in range(365)]
        self.assertTrue(self.journal.archive(records))
        self.assertTrue(self.journal.archive(copy.deepcopy(records)))
        found, cursor = [], None
        while True:
            model = self.journal.read(now=NOW, limit=37, cursor=cursor)
            found.extend(model["events"])
            if not model["hasMore"]:
                break
            cursor = model["nextCursor"]
            self.assertIsNotNone(cursor)
        self.assertEqual(len(found), len(records))
        self.assertEqual(len({row["id"] for row in found}), len(records))
        self.assertEqual({row["evidence"]["closedBarTime"] for row in found},
                         {row["closedBarTime"] for row in records})
        # Legacy status=analyzed does not prove that three processes completed.
        self.assertTrue(all(row["attemptStatus"] == "unknown" for row in found))

    def test_reobserved_pending_bar_cannot_downgrade_completed_execution_evidence(self):
        parent, children = fixture_round()
        summary = self.module.summarize_round(parent, children)
        row = fixture_coverage(1_700_000_000)
        self.assertTrue(self.journal.archive([row], round_summary=summary))
        self.assertTrue(self.journal.archive([{**row, "status": "pending", "completedAt": None}]))
        result = self.events()[0]
        self.assertEqual(result["status"], "analyzed")
        self.assertEqual(result["attemptStatus"], "complete_all")
        self.assertEqual(result["evidence"]["completedVotes"], 3)

    def test_write_failure_is_reported_and_same_record_can_be_persisted_after_recovery(self):
        with mock.patch.object(self.journal, "_connect", side_effect=OSError("fixture disk failure")):
            self.assertFalse(self.journal.observe(now=NOW, startup_id="startup-first"))
            self.assertFalse(self.journal.archive([fixture_coverage(1_700_000_000)]))
        model = self.journal.read(now=NOW)
        self.assertEqual(model["observerErrorCode"], "observability_OSError")
        self.assertNotIn("fixture disk failure", json.dumps(model))
        self.assertTrue(self.journal.archive([fixture_coverage(1_700_000_000)]))
        self.assertEqual(len(self.events()), 1)
        self.assertNotIn("observerErrorCode", self.journal.read(now=NOW))

    def test_corrupt_store_and_invalid_cursor_are_read_only_failures(self):
        self.journal.path.parent.mkdir(parents=True)
        self.journal.path.write_bytes(b"fixture corrupt database with private content")
        before = self.journal.path.read_bytes()
        model = self.journal.read(now=NOW)
        self.assertFalse(model["available"])
        self.assertEqual(self.journal.path.read_bytes(), before)
        self.assertNotIn("private content", json.dumps(model))
        self.journal.path.unlink()
        self.journal.observe(now=NOW, startup_id="startup-first")
        before = self.journal.path.read_bytes()
        files = sorted(path.name for path in self.journal.path.parent.iterdir())
        model = self.journal.read(now=NOW, cursor="before-1; DROP TABLE events")
        self.assertFalse(model["available"])
        self.assertEqual(self.journal.path.read_bytes(), before)
        self.assertEqual(sorted(path.name for path in self.journal.path.parent.iterdir()), files)

    def test_reader_does_not_renew_last_seen_or_mutate_existing_store(self):
        self.journal.observe(now=NOW, startup_id="startup-first")
        before = self.journal.path.read_bytes()
        stat_before = self.journal.path.stat().st_mtime_ns
        model = self.journal.read(now=NOW + timedelta(minutes=4))
        self.assertEqual(model["heartbeat"]["status"], "stale")
        self.assertEqual(model["lastSeenAt"], NOW.isoformat())
        self.assertEqual(model["unobservedInterval"]["certainty"], "unknown")
        self.assertEqual(self.journal.path.read_bytes(), before)
        self.assertEqual(self.journal.path.stat().st_mtime_ns, stat_before)

    def test_backfilled_old_bar_receipts_do_not_hide_newest_startup_event(self):
        self.journal.observe(now=NOW, startup_id="startup-first")
        yesterday = (NOW - timedelta(days=1)).isoformat()
        records = [fixture_coverage(1_700_000_000 + index * 3600,
                    detectedAt=yesterday, completedAt=yesterday) for index in range(250)]
        self.journal.archive(records)
        first = self.journal.read(now=NOW, limit=100)
        self.assertTrue(first["hasMore"])
        self.assertTrue(any(row["reasonCode"] == "bridge_started" for row in first["events"][:2]))
        found, cursor = list(first["events"]), first["nextCursor"]
        while cursor:
            page = self.journal.read(now=NOW, limit=100, cursor=cursor)
            found.extend(page["events"])
            cursor = page["nextCursor"]
        self.assertEqual(len(found), 252)
        self.assertEqual(len({row["id"] for row in found}), 252)


class CouncilOperationsVoteScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_operation("council_observability")

    def test_three_completed_hold_votes_are_analysis_success_not_trade_authorization(self):
        parent, children = fixture_round()
        before = copy.deepcopy((parent, children))
        result = self.module.summarize_round(parent, children)
        self.assertEqual(result["attemptStatus"], "complete_all")
        self.assertEqual(result["completedVotes"], 3)
        self.assertEqual((parent, children), before)
        self.assertNotIn("tradeCommandAllowed", result)
        self.assertNotIn("decision", result)

    def test_partial_three_roles_require_started_valid_vote_and_exact_snapshot(self):
        variants = {
            "not_started": lambda row: row["execution"].update(processStarted=False),
            "wrong_digest": lambda row: row["analysisContext"].update(snapshotArtifactDigest="f" * 64),
            "wrong_vote_snapshot": lambda row: row["councilVote"].update(snapshotId="f" * 64),
            "wrong_parent": lambda row: row.update(parentMissionId="mission-other"),
            "wrong_role": lambda row: row["councilVote"].update(roleId="technical"),
            "failed": lambda row: row.update(status="failed"),
            "invalid_decision": lambda row: row["councilVote"].update(decision="ASSUME_BUY"),
            "nan": lambda row: row["councilVote"].update(confidence=float("nan")),
            "bool_confidence": lambda row: row["councilVote"].update(confidence=True),
        }
        for name, modify in variants.items():
            with self.subTest(name=name):
                parent, children = fixture_round()
                modify(children[2])
                result = self.module.summarize_round(parent, children)
                self.assertEqual(result["attemptStatus"], "partial")
                self.assertEqual(result["completedVotes"], 2)
                self.assertFalse(result["roles"][2]["validVote"])

    def test_duplicate_role_is_ambiguous_and_not_counted_twice(self):
        parent, children = fixture_round()
        children.append(copy.deepcopy(children[0]))
        result = self.module.summarize_round(parent, children)
        self.assertEqual(result["completedVotes"], 2)
        self.assertEqual(result["attemptStatus"], "partial")

    def test_parent_completion_without_process_evidence_is_not_analysis_success(self):
        parent, children = fixture_round()
        for child in children:
            child["execution"] = {}
        result = self.module.summarize_round(parent, children)
        self.assertEqual(result["completedVotes"], 0)
        self.assertEqual(result["processesStarted"], 0)
        self.assertEqual(result["attemptStatus"], "not_started")

    def test_malformed_nested_legacy_evidence_never_proves_three_roles_complete(self):
        for field in ("analysisContext", "execution", "councilVote"):
            for invalid in ([], "legacy-invalid", True):
                with self.subTest(field=field, invalid=invalid):
                    parent, children = fixture_round()
                    children[2][field] = invalid
                    result = self.module.summarize_round(parent, children)
                    self.assertLess(result["completedVotes"], 3)
                    self.assertNotEqual(result["attemptStatus"], "complete_all")
        parent, children = fixture_round()
        parent["analysisContext"] = ["legacy-invalid"]
        result = self.module.summarize_round(parent, children)
        self.assertEqual(result["completedVotes"], 0)


class CouncilOperationsPreflightScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_operation("preflight")

    def ready(self):
        return {"now": NOW, "enabled": True, "terminal_locks_ready": True,
                "snapshot": {"status": "ready", "observedAt": NOW.isoformat(),
                             "maximumAgeSeconds": 300, "identityReady": True},
                "quota_gate": {"allowed": True, "reason": "ready", "remainingPercent": 80,
                               "quota": {"observedAt": NOW.isoformat(), "stale": False}},
                "runner": {"status": "ready_guarded", "observedAt": NOW.isoformat()},
                "operator_mode": "auto_guarded", "active_round": False}

    def test_disabled_terminal_lock_stale_data_and_existing_round_never_authorize(self):
        cases = [("automation", {"enabled": False}, "paused"),
                 ("terminal", {"terminal_locks_ready": False}, "blocked"),
                 ("snapshot", {"snapshot": {"status": "ready", "identityReady": True,
                     "observedAt": (NOW - timedelta(seconds=301)).isoformat(),
                     "maximumAgeSeconds": 300}}, "blocked"),
                 ("round", {"active_round": True}, "waiting")]
        for check_id, override, expected in cases:
            with self.subTest(check_id=check_id):
                values = {**self.ready(), **override}
                before = copy.deepcopy(values)
                result = self.module.build_preflight(**values)
                check = next(row for row in result["checks"] if row["id"] == check_id)
                self.assertEqual(check["status"], expected)
                self.assertFalse(result["canAuthorizeAnalysis"])
                self.assertTrue(result["advisory"])
                self.assertEqual(values, before)

    def test_fresh_exhaustion_is_distinct_from_missing_or_stale_quota(self):
        cases = [("quota_limit_reached", False, "blocked"),
                 ("quota_unavailable", False, "unknown"),
                 ("quota_stale", True, "unknown")]
        for reason, stale, expected in cases:
            with self.subTest(reason=reason):
                values = self.ready()
                values["quota_gate"] = {"allowed": False, "reason": reason,
                    "remainingPercent": 0 if reason == "quota_limit_reached" else None,
                    "quota": {"observedAt": NOW.isoformat(), "stale": stale}}
                result = self.module.build_preflight(**values)
                quota = next(row for row in result["checks"] if row["id"] == "quota")
                self.assertEqual(quota["status"], expected)
                self.assertEqual(quota["reasonCode"], reason)

    def test_all_ready_is_still_advisory_and_does_not_renew_cached_facts(self):
        values = self.ready()
        stamp = (NOW - timedelta(seconds=70)).isoformat()
        values["quota_gate"]["quota"]["observedAt"] = stamp
        values["snapshot"]["observedAt"] = stamp
        before = copy.deepcopy(values)
        result = self.module.build_preflight(**values)
        self.assertEqual(result["status"], "ready")
        self.assertFalse(result["canAuthorizeAnalysis"])
        for identifier in ("snapshot", "quota"):
            check = next(row for row in result["checks"] if row["id"] == identifier)
            self.assertEqual(check["observedAt"], stamp)
            self.assertEqual(check["ageSeconds"], 70)
        self.assertEqual(values, before)


class CouncilOperationsDiagnosticsScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_operation("diagnostics")
        cls.journal_module = load_operation("council_observability")

    def test_hostile_fields_and_known_text_fields_are_redacted_without_mutating_inputs(self):
        private = "fixture_private_token C:\\private\\auth.json account=123456"
        event = {"id": private, "type": private, "status": private, "severity": private,
                 "reasonCode": private, "symbol": private, "timeframe": private,
                 "messageTh": private, "prompt": private, "token": private,
                 "evidence": {"source": private, "error": private, "password": private}}
        operations = {"available": True, "events": [event], "accountId": private,
            "incidents": {"active": [event], "recovered": [event]},
            "readiness": {"checks": [{"id": private, "status": private,
                                      "reasonCode": private, "messageTh": private}]}}
        health = {"ok": True, "status": "ready", "logs": private, "accountId": private}
        council = {"config": {"enabled": True, "apiKey": private},
                   "state": {"reason": private, "symbol": private, "timeframe": private}}
        rounds = [{"missionId": private, "reasonCode": private, "prompt": private,
                   "roles": [{"roleId": "news", "status": "completed", "reason": private,
                              "stderr": private, "credentials": private}]}]
        before = copy.deepcopy((health, operations, council, rounds))
        result = self.module.build_diagnostics(now=NOW, version="0.9.27", health=health,
            operations=operations, council=council, rounds=rounds)
        rendered = json.dumps(result, ensure_ascii=False)
        for fragment in (private, "fixture_private_token", "auth.json", "123456"):
            self.assertNotIn(fragment, rendered)
        self.assertEqual((health, operations, council, rounds), before)
        self.assertTrue(result["readOnly"])
        self.assertTrue(result["redacted"])
        self.assertFalse(result["canAuthorizeAnalysis"])
        self.assertEqual(result["operations"]["events"][0]["reasonCode"], "unknown")
        self.assertIsNotNone(result["operations"]["events"][0]["unrecognizedReasonDigest"])

    def test_journal_partial_analysis_export_retains_observed_role_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            journal = self.journal_module.CouncilJournal(Path(temporary) / "operations.sqlite3")
            parent, children = fixture_round()
            children[2]["status"] = "failed"
            summary = self.journal_module.summarize_round(parent, children)
            journal.archive([fixture_coverage(1_700_000_000)], round_summary=summary)
            result = self.module.build_diagnostics(now=NOW, version="0.9.27", health={},
                operations=journal.read(now=NOW))
        event = result["operations"]["events"][0]
        self.assertEqual(event["type"], "bar")
        self.assertEqual(event["attemptStatus"], "partial")
        self.assertEqual(event["evidence"]["completedVotes"], 2)
        self.assertEqual(event["evidence"]["processesStarted"], 3)
        self.assertEqual(event["evidence"]["source"], "observed_bar_coverage")
        self.assertEqual(len(event["roles"]), 3)

    def test_export_is_bounded_even_with_large_history_and_malformed_optional_values(self):
        events = [{"type": "incident", "reasonCode": "quota_unavailable"}] * 1000
        result = self.module.build_diagnostics(now=NOW, version="0.9.27", health=[],
            operations={"events": events, "incidents": {"active": events, "recovered": "invalid"},
                        "readiness": {"checks": [None, True, "invalid"]}},
            council="invalid", rounds=[None] * 1000)
        self.assertEqual(len(result["operations"]["events"]), 200)
        self.assertTrue(result["operations"]["hasMore"])
        self.assertEqual(len(result["operations"]["incidents"]["active"]), 100)
        self.assertEqual(result["operations"]["incidents"]["recovered"], [])
        self.assertEqual(result["operations"]["readiness"]["checks"], [])
        self.assertEqual(len(result["rounds"]), 50)


class CouncilOperationsReadSurfaceScenarios(unittest.TestCase):
    """Run actual Bridge reader functions without importing or starting Bridge."""
    @classmethod
    def setUpClass(cls):
        source = (ROOT / "backend" / "local-runner" / "bridge_server.py").read_text(encoding="utf-8-sig")
        tree = ast.parse(source)
        names = {"_council_operations_context", "_council_operations_readiness",
                 "ai_trade_council_operations_read_model", "ai_trade_council_diagnostics_read_model",
                 "_council_operations_observe", "_council_operations_enqueue", "_council_operations_flush"}
        selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
        if {node.name for node in selected} != names:
            raise AssertionError("Bridge operations reader seam missing")
        cls.reader_code = compile(ast.Module(body=selected, type_ignores=[]), "bridge_operations_readers", "exec")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = {"settings": {"preserveFixture": True, "riskPercent": 0.5},
                         "privateFixture": "fixture-private-operator-setting"}
        self.config = {"config": {"enabled": True, "maxManagedOrders": 3},
                       "state": {"status": "idle"}}
        payloads = {"council.json": self.config,
                    "dashboard-workflow-settings.json": self.settings,
                    "operator-mode.json": {"mode": "auto_guarded"}}
        for filename, value in payloads.items():
            (self.root / filename).write_text(json.dumps(value), encoding="utf-8")
        self.quota = {"checkedAt": NOW.isoformat(), "cacheAgeSeconds": 3, "stale": False}
        self.reads, self.gates = [], []

        def read_json(path, default):
            path = Path(path)
            self.assertEqual(path.parent.resolve(), self.root.resolve())
            self.reads.append(path.name)
            return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default

        def quota_gate(config, *, refresh, quota, settings):
            self.assertFalse(refresh, "GET must use cached quota and never refresh provider")
            self.assertEqual(settings, self.settings)
            self.assertEqual(config, self.config["config"])
            self.gates.append(copy.deepcopy(quota))
            return {"allowed": True, "reason": "ready", "quota": quota}

        deny = mock.Mock(side_effect=AssertionError("read surface attempted external work or mutation"))
        self.ns = {
            "copy": copy, "threading": threading, "RUNTIME_DIR": self.root,
            "time": SimpleNamespace(monotonic=lambda: 1000.0),
            "COUNCIL_OPERATIONS_LOCK": threading.RLock(), "COUNCIL_OPERATIONS_CONTEXTS": {},
            "council_observability": load_operation("council_observability"),
            "CODEX_RATE_LIMIT_CACHE_LOCK": threading.RLock(), "CODEX_RATE_LIMIT_LAST_PROBE": {},
            "CODEX_RATE_LIMIT_CACHE": {"payload": copy.deepcopy(self.quota), "fetchedMonotonic": 997.0},
            "CODEX_STATUS_CACHE_LOCK": threading.RLock(),
            "CODEX_STATUS_CACHE": {"payload": {"status": "ready_guarded", "checkedAt": NOW.isoformat()},
                                   "fetchedMonotonic": 1000.0},
            "CODEX_STATUS_CACHE_STALE_MAX_SECONDS": 300,
            "MISSIONS_READ_CACHE_LOCK": threading.RLock(), "MISSIONS_PATH": self.root / "missions.json",
            "MISSIONS_READ_CACHE": {"path": str(self.root / "missions.json"), "missions": []},
            "utc_now": lambda: NOW.isoformat(), "read_json": read_json,
            "_ai_trade_council_automation_store_path": lambda: self.root / "council.json",
            "_collaboration_quota_gate": quota_gate,
            "build_council_preflight": load_operation("preflight").build_preflight,
            "build_council_diagnostics": load_operation("diagnostics").build_diagnostics,
            "VERSION": "0.9.27", "BRIDGE_RUNTIME_VERSION": "0.9.27",
            "SERVER_STARTED_AT": NOW.isoformat(),
        }
        for name in ("bridge_status", "codex_status", "codex_rate_limits", "peek_codex_rate_limits", "write_json",
                     "ensure_runtime_dir", "create_mission", "run_safe_command", "urlopen",
                     "metatrader_snapshot_read_model", "dispatch_ai_trade_council_trade_plan",
                     "start_local_runner", "publish_mt5_command"):
            self.ns[name] = deny
        self.deny = deny
        exec(self.reader_code, self.ns)
        context = self.ns["_council_operations_context"]()
        context["facts"] = {"terminalLocksReady": True, "activeRound": False,
            "snapshot": {"status": "ready", "identityReady": True,
                         "observedAt": NOW.isoformat(), "maximumAgeSeconds": 300}}

    def snapshot_files(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file()}

    def test_operations_readiness_and_export_never_dispatch_probe_or_write_settings(self):
        before = self.snapshot_files()
        model = self.ns["ai_trade_council_operations_read_model"]()
        self.assertEqual(model["readiness"]["status"], "ready")
        self.assertFalse(model["available"])
        self.assertFalse(model["readiness"]["canAuthorizeAnalysis"])
        exported = self.ns["ai_trade_council_diagnostics_read_model"]()
        self.assertTrue(exported["readOnly"])
        self.assertEqual(len(self.gates), 2)
        self.assertEqual(self.gates[0], self.quota)
        self.assertEqual(self.snapshot_files(), before)
        self.assertNotIn("fixture-private-operator-setting", json.dumps(exported))
        self.deny.assert_not_called()

    def test_latest_failed_quota_probe_is_not_hidden_by_older_ready_cache(self):
        failed = {"checkedAt": NOW.isoformat(), "status": "unavailable", "stale": False}
        self.ns["CODEX_RATE_LIMIT_LAST_PROBE"] = {"ok": False, "quota": failed}
        before = self.snapshot_files()
        self.ns["ai_trade_council_operations_read_model"]()
        self.assertEqual(self.gates[-1]["status"], "unavailable")
        self.assertEqual(self.gates[-1]["checkedAt"], failed["checkedAt"])
        self.assertEqual(self.snapshot_files(), before)
        self.deny.assert_not_called()

    def test_malformed_cached_setting_failure_is_unknown_without_repair_or_provider_fallback(self):
        path = self.root / "dashboard-workflow-settings.json"
        path.write_text("{fixture corrupt settings", encoding="utf-8")
        before = self.snapshot_files()
        result = self.ns["ai_trade_council_operations_read_model"]()
        self.assertEqual(result["readinessErrorCode"], "cached_state_unavailable")
        self.assertEqual(result["readiness"]["status"], "unknown")
        self.assertFalse(result["readiness"]["canAuthorizeAnalysis"])
        self.assertEqual(self.snapshot_files(), before)
        self.deny.assert_not_called()

    def test_busy_provider_status_or_mission_cache_lock_never_waits_or_refreshes(self):
        case = self

        class BusyLock:
            def acquire(self, blocking=True, **kwargs):
                case.assertFalse(blocking, "passive reader attempted to wait behind active work")
                return False

            def release(self):
                raise AssertionError("unowned cache lock was released")

        for name in ("CODEX_RATE_LIMIT_CACHE_LOCK", "CODEX_STATUS_CACHE_LOCK", "MISSIONS_READ_CACHE_LOCK"):
            with self.subTest(lock=name):
                before = self.snapshot_files()
                old = self.ns[name]
                self.ns[name] = BusyLock()
                try:
                    model = self.ns["ai_trade_council_operations_read_model"]()
                finally:
                    self.ns[name] = old
                self.assertEqual(model["readiness"]["status"], "unknown")
                self.assertFalse(model["readiness"]["canAuthorizeAnalysis"])
                self.assertEqual(self.snapshot_files(), before)
                self.deny.assert_not_called()

    def test_unreadable_quota_does_not_falsely_recover_a_blocked_incident(self):
        journal = self.ns["_council_operations_context"]()["journal"]
        clock = [NOW]
        self.ns["utc_now"] = lambda: clock[0].isoformat()
        model = {"checks": [{"id": "quota", "status": "blocked", "reasonCode": "quota_below_reserve"}]}
        self.ns["_council_operations_readiness"] = lambda now: copy.deepcopy(model)
        self.ns["_council_operations_observe"]()
        active = journal.read(now=clock[0])["incidents"]["active"]
        self.assertEqual(len(active), 1)
        first_id = active[0]["id"]
        clock[0] += timedelta(seconds=31)
        model["checks"][0].update(status="unknown", reasonCode="quota_unavailable")
        self.ns["_council_operations_observe"]()
        unknown = journal.read(now=clock[0])
        self.assertTrue(unknown["incidents"]["active"])
        self.assertFalse(any(event["id"] == first_id and event["status"] == "recovered"
                             for event in unknown["events"]))
        clock[0] += timedelta(seconds=31)
        model["checks"][0].update(status="ready", reasonCode="quota_ready")
        self.ns["_council_operations_observe"]()
        recovered = journal.read(now=clock[0])
        self.assertEqual(recovered["incidents"]["active"], [])
        self.assertTrue(any(event["status"] == "recovered" for event in recovered["events"]))
        self.deny.assert_not_called()


class CouncilOperationsTickIsolationScenarios(unittest.TestCase):
    """Real admission tick, inert Council runner and exclusively temporary files."""
    def setUp(self):
        import test_ai_trade_council_per_bar_automation as fixtures
        self.f = fixtures.AiTradeCouncilPerBarAutomationTests()
        self.f.setUp()
        self.addCleanup(self.f.tearDown)
        self.b = self.f.bridge
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.clock = NOW
        test_case = self

        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return test_case.clock.astimezone(tz) if tz else test_case.clock.replace(tzinfo=None)

        self.stack.enter_context(mock.patch.object(self.b, "datetime", FixedDateTime))
        self.stack.enter_context(mock.patch.object(fixtures, "datetime", FixedDateTime))
        self.stack.enter_context(mock.patch.object(self.b, "utc_now", side_effect=lambda: self.clock.isoformat()))
        self.b.MISSIONS_PATH = self.b.RUNTIME_DIR / "missions.json"
        self.b._collaboration_quota_gate = lambda config, refresh, **kwargs: {
            "allowed": True, "reason": "ready", "remainingPercent": 80,
            "quota": {"checkedAt": self.clock.isoformat(), "cacheAgeSeconds": 0}}
        self.b.peek_codex_rate_limits = lambda: {"checkedAt": self.clock.isoformat(), "cacheAgeSeconds": 0}
        self.denied = []
        for name in ("codex_rate_limits", "run_safe_command", "dispatch_ai_trade_council_trade_plan",
                     "create_mission", "urlopen"):
            denied = self.stack.enter_context(mock.patch.object(self.b, name,
                side_effect=AssertionError("fixture attempted real operation: " + name)))
            self.denied.append(denied)
        self.f._save_observed_store()
        self.config = copy.deepcopy(self.b.load_ai_trade_council_automation_store()["config"])
        self.setting = self.b.RUNTIME_DIR / "dashboard-workflow-settings.json"
        self.setting.write_text('{"preserveFixtureRisk":0.5}', encoding="utf-8")
        self.journal = self.b._council_operations_context()["journal"]

    def assert_preserved(self):
        self.assertEqual(self.b.load_ai_trade_council_automation_store()["config"], self.config)
        self.assertEqual(self.setting.read_text(encoding="utf-8"), '{"preserveFixtureRisk":0.5}')
        self.assertTrue(self.b.AI_TRADE_COUNCIL_AUTOMATION_RUN_LOCK.acquire(blocking=False))
        self.b.AI_TRADE_COUNCIL_AUTOMATION_RUN_LOCK.release()
        for denied in self.denied:
            denied.assert_not_called()

    def test_observer_disk_failure_keeps_admission_and_same_bar_dedup_unchanged(self):
        self.f._advance_bar()
        with mock.patch.object(self.journal, "_connect", side_effect=OSError("fixture disk full")) as failed:
            first = self.b.ai_trade_council_automation_tick()
            self.assertEqual(first["kind"], "ai_trade_council_automation_settling")
            queued = self.f._finish_settle()
            self.assertEqual(queued["kind"], "ai_trade_council_queued")
            replay = self.b.ai_trade_council_automation_tick()
            self.assertEqual(replay["kind"], "ai_trade_council_automation_idle")
        self.assertGreater(failed.call_count, 0, "disk-failure seam was actually exercised")
        self.assertEqual(len(self.f.calls), 1)
        self.assertTrue(self.b._council_operations_context()["pending"])
        self.assert_preserved()

    def test_unexpected_observer_exception_cannot_replace_successful_tick_result(self):
        self.f._advance_bar()
        with mock.patch.object(self.b, "_council_operations_observe", side_effect=RuntimeError("fixture observer bug")):
            self.assertEqual(self.b.ai_trade_council_automation_tick()["kind"], "ai_trade_council_automation_settling")
            self.assertEqual(self.f._finish_settle()["kind"], "ai_trade_council_queued")
        self.assertEqual(len(self.f.calls), 1)
        self.assert_preserved()

    def test_sqlite_archive_runs_after_all_trading_locks_are_released(self):
        observed = []
        original = self.journal.archive

        def archive(records, **kwargs):
            acquired = []

            def other_thread():
                for name in ("AI_TRADE_COUNCIL_AUTOMATION_RUN_LOCK", "AI_TRADE_COUNCIL_AUTOMATION_LOCK", "MISSIONS_LOCK"):
                    lock = getattr(self.b, name)
                    ok = lock.acquire(blocking=False)
                    acquired.append((name, ok))
                    if ok:
                        lock.release()

            thread = threading.Thread(target=other_thread)
            thread.start()
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
            self.assertEqual(len(acquired), 3)
            self.assertTrue(all(ok for _, ok in acquired), acquired)
            observed.append(True)
            return original(records, **kwargs)

        self.f._advance_bar()
        with mock.patch.object(self.journal, "archive", side_effect=archive):
            self.assertEqual(self.b.ai_trade_council_automation_tick()["kind"], "ai_trade_council_automation_settling")
        self.assertTrue(observed)
        self.assert_preserved()

    def test_failed_terminal_archive_batch_has_one_attempt_and_keeps_all_pending(self):
        parent, children = fixture_round()
        summary = self.b.council_observability.summarize_round(parent, children)
        records = [fixture_coverage(1_700_000_000 + index * 3600) for index in range(300)]
        self.b._council_operations_enqueue(records, round_summary=summary)
        with mock.patch.object(self.journal, "archive", return_value=False) as archive:
            self.b._council_operations_flush()
        archive.assert_called_once()
        self.assertEqual(len(archive.call_args.args[0]), 256)
        self.assertEqual(len(archive.call_args.kwargs["round_summaries"]), 256)
        self.assertEqual(len(self.b._council_operations_context()["pending"]), 300)
        # The next tick persists a single bounded batch; no work is dispatched.
        self.b._council_operations_flush()
        self.assertEqual(len(self.b._council_operations_context()["pending"]), 44)
        self.b._council_operations_flush()
        self.assertEqual(self.b._council_operations_context()["pending"], {})
        self.assertEqual(len(self.f.calls), 0)
        self.assert_preserved()

if __name__ == "__main__":
    unittest.main()
