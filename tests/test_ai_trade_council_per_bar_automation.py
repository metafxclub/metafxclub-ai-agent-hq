from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_bridge_per_bar_automation_tests",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load bridge module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AiTradeCouncilPerBarAutomationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bridge = load_bridge()
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.bridge.RUNTIME_DIR = root / "runtime"
        self.bridge.AUDIT_PATH = self.bridge.RUNTIME_DIR / "bridge-audit.jsonl"
        # Snapshot artifacts are part of automation state. Keep them inside
        # the same isolated fixture so an installed-package test never writes
        # into the source checkout or reuses artifacts from another test run.
        self.bridge.PROJECT_ROOT = root
        self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR = root / "workspace"
        self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR = (
            self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR
            / "ai-trade-council"
            / "snapshots"
        )
        self.bridge.AI_TRADE_COUNCIL_DEEP_ANALYSIS_DIR = (
            self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR
            / "ai-trade-council"
            / "deep-analysis"
        )
        self.candidate_id = "mtc-per-bar-regression"
        self.symbol = "XAUUSD"
        self.timeframe = "M5"
        self.closed_bar_time = 1_786_470_000
        self.snapshot_id = "a" * 64
        self.calls: list[dict] = []

        self.bridge.evaluate_ai_trade_council_outcomes = (
            lambda: {"updated": 0, "pending": 0}
        )
        self.bridge._active_ai_trade_council_parent = lambda: None
        self.bridge.load_operator_mode_record = lambda: {"mode": "auto_guarded"}
        self.bridge.bridge_status = lambda: {
            "codex": {"status": "ready_guarded"}
        }
        self.bridge._collaboration_quota_gate = (
            lambda config, refresh: {
                "allowed": True,
                "reason": "ready",
                "remainingPercent": 80,
            }
        )
        self.bridge.metatrader_snapshot_read_model = lambda _prop_id: self._snapshot()

        def fake_council(request, *, automation_context=None, _snapshot_model=None):
            self.calls.append({
                "request": request,
                "automationContext": automation_context,
                "snapshotModel": _snapshot_model,
            })
            return {
                "ok": True,
                "kind": "ai_trade_council_queued",
                "parent": {"id": f"mission-per-bar-{len(self.calls)}"},
            }

        self.bridge.run_ai_trade_council_analysis = fake_council

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def _snapshot(self) -> dict:
        return {
            "selectedCandidateId": self.candidate_id,
            "adapter": {"ready": True},
            "chartSnapshot": {
                "available": True,
                "snapshotId": self.snapshot_id,
                "symbol": self.symbol,
                "timeframe": self.timeframe,
                "bars": [{"time": self.closed_bar_time}],
            },
        }

    def _save_observed_store(
        self,
        *,
        daily_run_count: int = 0,
        startup_id: str | None = None,
    ) -> None:
        store = self.bridge._ai_trade_council_automation_default_store()
        store["config"].update({
            "enabled": True,
            "dailyRoundLimitMode": "unlimited",
        })
        store["state"].update({
            "status": "idle",
            "reason": "waiting_for_new_closed_bar",
            "startupId": startup_id or self.bridge.SERVER_STARTED_AT,
            "dailyRunDate": self.bridge._automation_day_key(),
            "dailyRunCount": daily_run_count,
            "candidateId": self.candidate_id,
            "streamKey": self.bridge.payload_digest(
                self.candidate_id,
                self.symbol,
                self.timeframe,
            ),
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "lastObservedClosedBarTime": self.closed_bar_time,
        })
        self.bridge._save_ai_trade_council_automation_store(store)

    def _finish_settle(self) -> dict:
        pending = self.bridge.load_ai_trade_council_automation_store()
        pending["state"]["pendingDetectedAt"] = (
            datetime.now(timezone.utc) - timedelta(seconds=20)
        ).isoformat()
        self.bridge._save_ai_trade_council_automation_store(pending)
        return self.bridge.ai_trade_council_automation_tick()

    def _advance_bar(self) -> None:
        self.closed_bar_time += 300
        next_digest_character = chr(ord("a") + (self.closed_bar_time // 300) % 6)
        self.snapshot_id = next_digest_character * 64

    def test_same_bar_is_idle_and_each_new_bar_queues_exactly_once_without_daily_cap(self) -> None:
        self._save_observed_store(daily_run_count=24)

        same_bar = self.bridge.ai_trade_council_automation_tick()
        self.assertEqual(same_bar["kind"], "ai_trade_council_automation_idle")
        self.assertEqual(self.calls, [])

        self._advance_bar()
        detected = self.bridge.ai_trade_council_automation_tick()
        self.assertEqual(
            detected["kind"],
            "ai_trade_council_automation_settling",
        )
        queued = self._finish_settle()
        self.assertEqual(queued["kind"], "ai_trade_council_queued")
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(
            self.calls[0]["automationContext"]["closedBarTime"],
            self.closed_bar_time,
        )

        replay = self.bridge.ai_trade_council_automation_tick()
        self.assertEqual(replay["kind"], "ai_trade_council_automation_idle")
        self.assertEqual(len(self.calls), 1)

        self._advance_bar()
        self.assertEqual(
            self.bridge.ai_trade_council_automation_tick()["kind"],
            "ai_trade_council_automation_settling",
        )
        second = self._finish_settle()
        self.assertEqual(second["kind"], "ai_trade_council_queued")
        self.assertEqual(len(self.calls), 2)
        automation = second["automation"]
        self.assertEqual(automation["state"]["dailyRunCount"], 26)
        self.assertEqual(
            automation["config"]["dailyRoundLimitMode"],
            "unlimited",
        )
        self.assertFalse(automation["config"]["dailyRoundLimitEnabled"])
        self.assertIsNone(automation["config"]["effectiveMaxDailyRounds"])

    def test_same_closed_bar_survives_mutable_tick_snapshot_id_change(self) -> None:
        self._save_observed_store()
        self._advance_bar()
        captured_snapshot_id = self.snapshot_id
        detected = self.bridge.ai_trade_council_automation_tick()
        self.assertEqual(detected["kind"], "ai_trade_council_automation_settling")

        # The EA republishes a different full snapshot as quotes/risk telemetry
        # move, while the immutable stream and most recent closed bar stay the
        # same. This must not demote a current bar to audit-only.
        self.snapshot_id = "f" * 64
        queued = self._finish_settle()

        self.assertEqual(queued["kind"], "ai_trade_council_queued")
        self.assertEqual(len(self.calls), 1)
        call = self.calls[0]
        self.assertEqual(call["request"]["snapshotId"], captured_snapshot_id)
        self.assertEqual(
            call["snapshotModel"]["chartSnapshot"]["snapshotId"],
            captured_snapshot_id,
        )
        self.assertEqual(
            call["automationContext"]["executionPolicy"],
            "current_exact_snapshot",
        )
        self.assertTrue(call["automationContext"]["tradeCommandAllowed"])

    def test_closed_bar_identity_match_ignores_only_snapshot_id(self) -> None:
        stream_key = self.bridge._ai_trade_council_stream_key(
            self.candidate_id,
            self.symbol,
            self.timeframe,
        )
        pending = {
            "candidateId": self.candidate_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "streamKey": stream_key,
            "closedBarTime": self.closed_bar_time,
            "snapshotId": "a" * 64,
        }
        current = {
            "candidateId": self.candidate_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "streamKey": stream_key,
            "lastClosedBarTime": self.closed_bar_time,
            "snapshotId": "f" * 64,
        }
        self.assertTrue(
            self.bridge._ai_trade_council_pending_matches_current_closed_bar(
                pending,
                current,
            )
        )
        mutations = {
            "candidateId": "mtc-other-candidate",
            "symbol": "EURUSD",
            "timeframe": "H1",
            "streamKey": "0" * 64,
            "lastClosedBarTime": self.closed_bar_time + 300,
        }
        for field, value in mutations.items():
            changed = dict(current)
            changed[field] = value
            with self.subTest(field=field):
                self.assertFalse(
                    self.bridge._ai_trade_council_pending_matches_current_closed_bar(
                        pending,
                        changed,
                    )
                )

    def test_restart_establishes_baseline_without_catching_up(self) -> None:
        self._save_observed_store(
            daily_run_count=87,
            startup_id="previous-process",
        )
        self._advance_bar()

        result = self.bridge.ai_trade_council_automation_tick()

        self.assertEqual(result["kind"], "ai_trade_council_automation_baseline")
        self.assertEqual(result["reason"], "restart_baseline")
        self.assertEqual(self.calls, [])
        state = result["automation"]["state"]
        self.assertEqual(state["lastObservedClosedBarTime"], self.closed_bar_time)
        self.assertIsNone(
            self.bridge.load_ai_trade_council_automation_store()["state"][
                "pendingClosedBarTime"
            ]
        )

    def test_quota_gate_fails_closed_and_retains_pending_bar_for_retry(self) -> None:
        self._save_observed_store(daily_run_count=999)
        self._advance_bar()
        self.assertEqual(
            self.bridge.ai_trade_council_automation_tick()["kind"],
            "ai_trade_council_automation_settling",
        )
        pending = self.bridge.load_ai_trade_council_automation_store()
        pending["state"]["pendingDetectedAt"] = (
            datetime.now(timezone.utc) - timedelta(seconds=20)
        ).isoformat()
        self.bridge._save_ai_trade_council_automation_store(pending)
        self.bridge._collaboration_quota_gate = (
            lambda config, refresh: {
                "allowed": False,
                "reason": "quota_reserve_reached",
                "remainingPercent": 10,
            }
        )

        blocked = self.bridge.ai_trade_council_automation_tick()

        self.assertEqual(
            blocked["kind"],
            "ai_trade_council_automation_waiting_gate",
        )
        self.assertEqual(blocked["reason"], "quota_reserve_reached")
        self.assertEqual(self.calls, [])
        state = self.bridge.load_ai_trade_council_automation_store()["state"]
        self.assertEqual(state["pendingClosedBarTime"], self.closed_bar_time)

        self.bridge._collaboration_quota_gate = (
            lambda config, refresh: {
                "allowed": True,
                "reason": "ready",
                "remainingPercent": 80,
            }
        )
        queued = self.bridge.ai_trade_council_automation_tick()
        self.assertEqual(queued["kind"], "ai_trade_council_queued")
        self.assertEqual(len(self.calls), 1)

    def test_explicit_limited_mode_still_blocks_at_the_configured_cap(self) -> None:
        self._save_observed_store(daily_run_count=24)
        store = self.bridge.load_ai_trade_council_automation_store()
        store["config"].update({
            "dailyRoundLimitMode": "limited",
            "maxDailyRounds": 24,
        })
        self.bridge._save_ai_trade_council_automation_store(store)
        self._advance_bar()

        detected = self.bridge.ai_trade_council_automation_tick()
        self.assertEqual(
            detected["kind"],
            "ai_trade_council_automation_settling",
        )
        blocked = self._finish_settle()

        self.assertEqual(
            blocked["kind"],
            "ai_trade_council_automation_daily_cap",
        )
        self.assertEqual(self.calls, [])
        automation = blocked["automation"]
        self.assertTrue(automation["config"]["dailyRoundLimitEnabled"])
        self.assertEqual(automation["config"]["effectiveMaxDailyRounds"], 24)

    def test_active_round_retains_fifo_and_backlog_is_audit_only(self) -> None:
        self._save_observed_store()
        self._advance_bar()
        first_pending_bar = self.closed_bar_time
        self.assertEqual(
            self.bridge.ai_trade_council_automation_tick()["kind"],
            "ai_trade_council_automation_settling",
        )
        pending = self.bridge.load_ai_trade_council_automation_store()
        pending["state"]["pendingDetectedAt"] = (
            datetime.now(timezone.utc) - timedelta(seconds=20)
        ).isoformat()
        self.bridge._save_ai_trade_council_automation_store(pending)
        self.bridge._active_ai_trade_council_parent = lambda: {
            "id": "mission-still-running",
        }

        waiting = self.bridge.ai_trade_council_automation_tick()
        self.assertEqual(
            waiting["kind"],
            "ai_trade_council_automation_waiting_gate",
        )
        self.assertEqual(waiting["reason"], "council_round_already_active")
        self.assertEqual(self.calls, [])

        # A second candle is retained. The oldest exact captured Snapshot is
        # analyzed first, but it can no longer publish a trade command.
        self._advance_bar()
        latest_pending_bar = self.closed_bar_time
        self.assertNotEqual(latest_pending_bar, first_pending_bar)
        self.assertEqual(
            self.bridge.ai_trade_council_automation_tick()["kind"],
            "ai_trade_council_automation_settling",
        )
        pending = self.bridge.load_ai_trade_council_automation_store()
        self.assertEqual(
            pending["state"]["pendingClosedBarTime"],
            first_pending_bar,
        )
        pending["state"]["pendingDetectedAt"] = (
            datetime.now(timezone.utc) - timedelta(seconds=20)
        ).isoformat()
        self.bridge._save_ai_trade_council_automation_store(pending)

        self.bridge._active_ai_trade_council_parent = lambda: None
        queued = self.bridge.ai_trade_council_automation_tick()

        self.assertEqual(queued["kind"], "ai_trade_council_queued")
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(
            self.calls[0]["automationContext"]["closedBarTime"],
            first_pending_bar,
        )
        self.assertEqual(
            self.calls[0]["automationContext"]["executionPolicy"],
            "audit_only_no_stale_dispatch",
        )
        self.assertFalse(
            self.calls[0]["automationContext"]["tradeCommandAllowed"]
        )
        state = self.bridge.load_ai_trade_council_automation_store()["state"]
        self.assertEqual(state["pendingQueue"][0]["closedBarTime"], latest_pending_bar)

    def test_legacy_store_migrates_to_unlimited_but_legacy_api_can_opt_into_limit(self) -> None:
        legacy_store = self.bridge._ai_trade_council_automation_default_store()
        legacy_store["config"].pop("dailyRoundLimitMode", None)
        legacy_store["config"]["maxDailyRounds"] = 24
        shaped = self.bridge._ai_trade_council_automation_store_shape(legacy_store)
        self.assertEqual(shaped["config"]["dailyRoundLimitMode"], "unlimited")

        updated = self.bridge.set_ai_trade_council_automation({
            "maxDailyRounds": 12,
        })
        config = updated["automation"]["config"]
        self.assertEqual(config["dailyRoundLimitMode"], "limited")
        self.assertTrue(config["dailyRoundLimitEnabled"])
        self.assertEqual(config["effectiveMaxDailyRounds"], 12)

    def test_contracts_describe_unlimited_fifo_coverage_compatibility(self) -> None:
        contracts = PROJECT_ROOT / "contracts"
        orchestration = json.loads(
            (contracts / "orchestration" / "orchestration-contract.json").read_text(
                encoding="utf-8"
            )
        )
        reports = json.loads(
            (contracts / "reports" / "report-contract.json").read_text(
                encoding="utf-8"
            )
        )
        connections = json.loads(
            (
                contracts
                / "connections"
                / "dashboard-connection-contract.json"
            ).read_text(encoding="utf-8")
        )
        bridge = json.loads(
            (contracts / "bridge" / "bridge-contract.json").read_text(
                encoding="utf-8"
            )
        )

        automation = orchestration["aiTradeCouncilAutoAnalysis"]
        cost_guard = orchestration["costRateGuard"]
        report_config = reports["typed_report_schemas"]["prop_report"]["properties"][
            "aiTradeCouncil"
        ]["autoAnalysis"]["config"]
        connection_config = connections["profiles"]["left_analytics_console"][
            "operation"
        ]
        post_contract = bridge["endpoints"]["POST /api/ai-trade-council/automation"]

        fifo_policy = "durable_fifo_exact_snapshot_audit_only_when_stale"
        self.assertEqual(automation["backlogPolicy"], fifo_policy)
        self.assertEqual(report_config["backlogPolicy"], fifo_policy)
        self.assertEqual(connection_config["backlogPolicy"], fifo_policy)
        self.assertEqual(cost_guard["aiTradeCouncilAutoDailyRoundLimitMode"], "unlimited")
        self.assertFalse(cost_guard["aiTradeCouncilAutoDailyRoundLimitEnabled"])
        self.assertIsNone(cost_guard["aiTradeCouncilAutoMaxDailyRounds"])
        self.assertEqual(cost_guard["aiTradeCouncilAutoLegacyMaxDailyRounds"], 24)
        self.assertIn("dailyRoundLimitMode", post_contract)
        self.assertIn("effectiveMaxDailyRounds null", post_contract)
        self.assertIn("durable FIFO", post_contract)
        self.assertIn("stale snapshot is analysis-only", post_contract)


if __name__ == "__main__":
    unittest.main()
