from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_bridge_stream_switching_tests",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load bridge module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AiTradeCouncilStreamSwitchingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bridge = load_bridge()
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bridge.RUNTIME_DIR = self.root / "runtime"
        self.bridge.AUDIT_PATH = self.bridge.RUNTIME_DIR / "bridge-audit.jsonl"
        self.bridge.PROJECT_ROOT = self.root
        self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR = self.root / "workspace"
        self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR = (
            self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR
            / "ai-trade-council"
            / "snapshots"
        )
        self.bridge.evaluate_ai_trade_council_outcomes = (
            lambda: {"updated": 0, "pending": 0}
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _record(
        self,
        *,
        candidate: str,
        symbol: str,
        timeframe: str,
        bar_time: int,
        status: str = "pending",
    ) -> dict:
        return {
            "streamKey": self.bridge._ai_trade_council_stream_key(
                candidate,
                symbol,
                timeframe,
            ),
            "candidateId": candidate,
            "symbol": symbol,
            "timeframe": timeframe,
            "closedBarTime": bar_time,
            "snapshotId": "a" * 64,
            "detectedAt": "2026-08-12T00:00:00+00:00",
            "status": status,
            "reasonCode": "new_closed_bar_detected",
            "executionPolicy": "current_exact_snapshot",
        }

    def _snapshot(
        self,
        *,
        candidate: str,
        symbol: str,
        timeframe: str,
        bar_time: int,
        snapshot_id: str,
    ) -> dict:
        return {
            "selectedCandidateId": candidate,
            "adapter": {"ready": True},
            "dailySummary": {},
            "chartSnapshot": {
                "available": True,
                "snapshotId": snapshot_id,
                "observedAt": "2026-08-12T01:00:00+00:00",
                "symbol": symbol,
                "timeframe": timeframe,
                "bars": [{"time": bar_time}],
            },
        }

    def test_stream_change_terminalizes_previous_pending_and_baselines_new_chart(self) -> None:
        old = self._record(
            candidate="mtc-chart-one",
            symbol="XAUUSD",
            timeframe="M5",
            bar_time=1_786_470_000,
        )
        new_candidate = "mtc-chart-two"
        new_symbol = "EURUSD"
        new_timeframe = "H1"
        new_bar_time = 1_786_474_000
        new_stream = self.bridge._ai_trade_council_stream_key(
            new_candidate,
            new_symbol,
            new_timeframe,
        )
        store = self.bridge._ai_trade_council_automation_default_store()
        store["config"]["enabled"] = True
        store["state"].update({
            "startupId": self.bridge.SERVER_STARTED_AT,
            "candidateId": old["candidateId"],
            "streamKey": old["streamKey"],
            "symbol": old["symbol"],
            "timeframe": old["timeframe"],
            "lastObservedClosedBarTime": old["closedBarTime"],
            "coverageRecords": [old],
            "pendingQueue": [old],
        })
        self.bridge._save_ai_trade_council_automation_store(store)
        current_snapshot = self._snapshot(
            candidate=new_candidate,
            symbol=new_symbol,
            timeframe=new_timeframe,
            bar_time=new_bar_time,
            snapshot_id="b" * 64,
        )
        self.bridge.metatrader_snapshot_read_model = lambda _prop: current_snapshot

        # Keep this test focused on stream switching.  A real-time Bangkok day
        # rollover is covered separately and would otherwise expire this fixed
        # historical pending row when the suite runs after 2026-08-12.
        with mock.patch.object(
            self.bridge,
            "_automation_day_key",
            return_value="2026-08-12",
        ):
            result = self.bridge.ai_trade_council_automation_tick()

        self.assertEqual(result["kind"], "ai_trade_council_automation_baseline")
        self.assertEqual(result["reason"], "stream_change_baseline")
        saved = self.bridge.load_ai_trade_council_automation_store()["state"]
        self.assertEqual(saved["streamKey"], new_stream)
        self.assertEqual(saved["coverageCursorClosedBarTime"], new_bar_time)
        self.assertEqual(saved["pendingQueue"], [])
        old_saved = next(
            row for row in saved["coverageRecords"]
            if row["streamKey"] == old["streamKey"]
        )
        self.assertEqual(old_saved["status"], "skipped")
        self.assertEqual(
            old_saved["reasonCode"],
            "stream_changed_before_analysis",
        )
        self.assertEqual(
            old_saved["executionPolicy"],
            "audit_only_no_stale_dispatch",
        )
        transition = result["automation"]["state"]["transition"]
        self.assertTrue(transition["active"])
        self.assertEqual(transition["previous"]["symbol"], "XAUUSD")
        self.assertEqual(transition["current"]["symbol"], "EURUSD")
        self.assertEqual(transition["current"]["timeframe"], "H1")
        self.assertEqual(
            result["automation"]["state"]["activeStream"]["snapshotId"],
            "b" * 64,
        )

        # The baseline itself never enters the runnable FIFO. Only the next
        # exact H1 close is captured, and duplicate polling cannot enqueue it
        # twice.
        next_h1_close = new_bar_time + 3_600
        current_snapshot = self._snapshot(
            candidate=new_candidate,
            symbol=new_symbol,
            timeframe=new_timeframe,
            bar_time=next_h1_close,
            snapshot_id="c" * 64,
        )
        with mock.patch.object(
            self.bridge,
            "_automation_day_key",
            return_value="2026-08-12",
        ):
            first_close = self.bridge.ai_trade_council_automation_tick()
            second_poll = self.bridge.ai_trade_council_automation_tick()
        after_close = self.bridge.load_ai_trade_council_automation_store()["state"]
        self.assertEqual(first_close["kind"], "ai_trade_council_automation_settling")
        self.assertEqual(second_poll["kind"], "ai_trade_council_automation_settling")
        h1_pending = [
            row for row in after_close["pendingQueue"]
            if row["streamKey"] == new_stream
            and row["closedBarTime"] == next_h1_close
        ]
        self.assertEqual(len(h1_pending), 1)

    def test_restart_plus_stream_change_uses_stream_baseline_and_skips_old_pending(self) -> None:
        old = self._record(
            candidate="mtc-chart-one",
            symbol="XAUUSD",
            timeframe="M5",
            bar_time=1_786_470_000,
        )
        store = self.bridge._ai_trade_council_automation_default_store()
        store["config"]["enabled"] = True
        store["state"].update({
            "startupId": "previous-bridge-process",
            "candidateId": old["candidateId"],
            "streamKey": old["streamKey"],
            "symbol": old["symbol"],
            "timeframe": old["timeframe"],
            "lastObservedClosedBarTime": old["closedBarTime"],
            "coverageRecords": [old],
            "pendingQueue": [old],
        })
        self.bridge._save_ai_trade_council_automation_store(store)
        self.bridge.metatrader_snapshot_read_model = lambda _prop: self._snapshot(
            candidate="mtc-chart-two",
            symbol="EURUSD",
            timeframe="H1",
            bar_time=1_786_474_000,
            snapshot_id="b" * 64,
        )

        # Stream-transition semantics must not depend on the wall-clock date
        # on which this historical fixture is executed.
        with mock.patch.object(
            self.bridge,
            "_automation_day_key",
            return_value="2026-08-12",
        ):
            result = self.bridge.ai_trade_council_automation_tick()
        saved = self.bridge.load_ai_trade_council_automation_store()["state"]

        self.assertEqual(result["reason"], "stream_change_baseline")
        self.assertEqual(saved["pendingQueue"], [])
        old_saved = next(
            row for row in saved["coverageRecords"]
            if row["streamKey"] == old["streamKey"]
        )
        self.assertEqual(old_saved["status"], "skipped")
        self.assertEqual(old_saved["reasonCode"], "stream_changed_before_analysis")

    def test_missing_durable_fifo_head_terminalizes_before_transient_gates(self) -> None:
        candidate = "mtc-chart-one"
        symbol = "XAUUSD"
        timeframe = "M5"
        first = self._record(
            candidate=candidate,
            symbol=symbol,
            timeframe=timeframe,
            bar_time=1_786_470_000,
        )
        second = self._record(
            candidate=candidate,
            symbol=symbol,
            timeframe=timeframe,
            bar_time=1_786_470_300,
        )
        current_bar_time = 1_786_470_600
        store = self.bridge._ai_trade_council_automation_default_store()
        store["config"]["enabled"] = True
        store["state"].update({
            "startupId": self.bridge.SERVER_STARTED_AT,
            "dailyRunDate": "2026-08-12",
            "candidateId": candidate,
            "streamKey": first["streamKey"],
            "symbol": symbol,
            "timeframe": timeframe,
            "lastObservedClosedBarTime": current_bar_time,
            "coverageRecords": [first, second],
            "pendingQueue": [first, second],
        })
        self.bridge._save_ai_trade_council_automation_store(store)
        self.bridge.metatrader_snapshot_read_model = lambda _prop: self._snapshot(
            candidate=candidate,
            symbol=symbol,
            timeframe=timeframe,
            bar_time=current_bar_time,
            snapshot_id="c" * 64,
        )

        gate_must_not_run = AssertionError(
            "transient runtime gates must not precede intrinsic snapshot validation"
        )
        with (
            mock.patch.object(
                self.bridge,
                "_automation_day_key",
                return_value="2026-08-12",
            ),
            mock.patch.object(
                self.bridge,
                "_active_ai_trade_council_parent",
                side_effect=gate_must_not_run,
            ),
            mock.patch.object(
                self.bridge,
                "load_operator_mode_record",
                side_effect=gate_must_not_run,
            ),
            mock.patch.object(
                self.bridge,
                "bridge_status",
                side_effect=gate_must_not_run,
            ),
            mock.patch.object(
                self.bridge,
                "_collaboration_quota_gate",
                side_effect=gate_must_not_run,
            ),
        ):
            result = self.bridge.ai_trade_council_automation_tick()

        self.assertFalse(result["ok"])
        self.assertEqual(result["kind"], "ai_trade_council_automation_skipped")
        self.assertEqual(result["reason"], "durable_snapshot_unavailable")
        runtime_state = result["automation"]["state"]
        self.assertEqual(runtime_state["status"], "skipped")
        self.assertEqual(runtime_state["reasonCode"], "durable_snapshot_unavailable")
        self.assertEqual(runtime_state["pendingCount"], 1)
        self.assertEqual(runtime_state["pending"]["closedBarTime"], second["closedBarTime"])
        self.assertEqual(runtime_state["pending"]["queuePosition"], 1)
        self.assertEqual(runtime_state["pending"]["queueDepth"], 1)
        self.assertEqual(
            runtime_state["coverage"],
            {
                "expected": 2,
                "analyzed": 0,
                "skipped": 1,
                "pending": 1,
                "queued": 0,
                "reconciled": True,
            },
        )
        saved = self.bridge.load_ai_trade_council_automation_store()["state"]
        terminal = next(
            row for row in saved["coverageRecords"]
            if row["closedBarTime"] == first["closedBarTime"]
        )
        self.assertEqual(terminal["status"], "skipped")
        self.assertEqual(terminal["reasonCode"], "durable_snapshot_unavailable")
        self.assertEqual(
            [row["closedBarTime"] for row in saved["pendingQueue"]],
            [second["closedBarTime"]],
        )
        audit_rows = [
            json.loads(line)
            for line in self.bridge.AUDIT_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        event = next(
            row for row in audit_rows
            if row.get("type") == "ai_trade_council.automation_skipped"
            and row.get("reason") == "durable_snapshot_unavailable"
        )
        self.assertEqual(event["remainingPendingCount"], 1)
        self.assertFalse(event["tradeCommandAllowed"])
        self.assertFalse(event["terminalActions"])

    def test_old_terminal_round_cannot_overwrite_current_stream_cursors(self) -> None:
        old_stream = "a" * 64
        new_stream = "b" * 64
        store = self.bridge._ai_trade_council_automation_default_store()
        store["state"].update({
            "streamKey": new_stream,
            "lastAnalyzedClosedBarTime": 2_000,
            "lastAnalyzedSnapshotId": "c" * 64,
            "lastMissionId": "mission-new",
        })

        updates = self.bridge._ai_trade_council_terminal_cursor_updates(
            store,
            stream_key=old_stream,
            closed_bar_time=1_000,
            snapshot_id="d" * 64,
            mission_id="mission-old",
        )
        current_updates = self.bridge._ai_trade_council_terminal_cursor_updates(
            store,
            stream_key=new_stream,
            closed_bar_time=2_300,
            snapshot_id="e" * 64,
            mission_id="mission-current",
        )

        self.assertEqual(updates, {})
        self.assertEqual(current_updates["lastAnalyzedClosedBarTime"], 2_300)
        self.assertEqual(current_updates["lastMissionId"], "mission-current")

    def test_active_history_scope_filters_before_summary_and_pagination(self) -> None:
        active = self._record(
            candidate="mtc-active",
            symbol="EURUSD",
            timeframe="M15",
            bar_time=1_000,
            status="skipped",
        )
        old = self._record(
            candidate="mtc-old",
            symbol="XAUUSD",
            timeframe="M5",
            bar_time=2_000,
            status="skipped",
        )
        store = self.bridge._ai_trade_council_automation_default_store()
        store["state"].update({
            "candidateId": active["candidateId"],
            "streamKey": active["streamKey"],
            "symbol": active["symbol"],
            "timeframe": active["timeframe"],
            "coverageRecords": [old, active],
        })
        self.bridge._save_ai_trade_council_automation_store(store)
        scope = self.bridge._ai_trade_council_history_scope(
            "active",
            expected_candidate_id="mtc-active",
            expected_symbol="EURUSD",
            expected_timeframe="M15",
        )

        model = self.bridge._ai_trade_council_analysis_history_read_model(
            [],
            {"items": []},
            limit=1,
            scope=scope,
        )

        self.assertTrue(model["scope"]["authoritative"])
        self.assertEqual(model["scope"]["mode"], "active")
        self.assertEqual(model["summary"]["expected"], 1)
        self.assertEqual(model["page"]["total"], 1)
        self.assertEqual(len(model["items"]), 1)
        self.assertEqual(model["items"][0]["symbol"], "EURUSD")

        all_model = self.bridge._ai_trade_council_analysis_history_read_model(
            [],
            {"items": []},
            limit=10,
            scope=self.bridge._ai_trade_council_history_scope("all"),
        )
        self.assertEqual(all_model["summary"]["expected"], 2)
        self.assertEqual(all_model["page"]["total"], 2)

        with self.assertRaises(self.bridge.RequestError) as mismatch:
            self.bridge._ai_trade_council_history_scope(
                "active",
                expected_symbol="GBPJPY",
            )
        self.assertEqual(mismatch.exception.status, 409)

    def test_same_closed_bar_time_remains_partitioned_by_stream(self) -> None:
        shared_time = 1_786_474_000
        xau = self._record(
            candidate="mtc-xau",
            symbol="XAUUSD",
            timeframe="H1",
            bar_time=shared_time,
            status="skipped",
        )
        eur = self._record(
            candidate="mtc-eur",
            symbol="EURUSD",
            timeframe="H1",
            bar_time=shared_time,
            status="skipped",
        )
        store = self.bridge._ai_trade_council_automation_default_store()
        store["state"].update({
            "candidateId": eur["candidateId"],
            "streamKey": eur["streamKey"],
            "symbol": eur["symbol"],
            "timeframe": eur["timeframe"],
        })
        self.bridge._ai_trade_council_coverage_upsert(store, xau)
        self.bridge._ai_trade_council_coverage_upsert(store, eur)
        self.bridge._save_ai_trade_council_automation_store(store)

        all_model = self.bridge._ai_trade_council_analysis_history_read_model(
            [], {"items": []}, limit=10,
            scope=self.bridge._ai_trade_council_history_scope("all"),
        )
        active_model = self.bridge._ai_trade_council_analysis_history_read_model(
            [], {"items": []}, limit=10,
            scope=self.bridge._ai_trade_council_history_scope("active"),
        )

        self.assertEqual(all_model["page"]["total"], 2)
        self.assertEqual(active_model["page"]["total"], 1)
        self.assertEqual(active_model["items"][0]["streamKey"], eur["streamKey"])

    def test_lowercase_broker_suffix_uses_gateway_stream_identity_and_active_scope(self) -> None:
        candidate = "mtc-suffix-chart"
        snapshot = self._snapshot(
            candidate=candidate,
            symbol="EURUSD.m",
            timeframe="H1",
            bar_time=1_786_474_000,
            snapshot_id="d" * 64,
        )
        identity, reason = self.bridge._ai_trade_council_closed_bar_identity(snapshot)
        expected_stream = self.bridge.payload_digest(
            candidate,
            "EURUSD.M",
            "H1",
        )

        self.assertEqual(reason, "ready")
        self.assertEqual(identity["symbol"], "EURUSD.m")
        self.assertEqual(identity["streamKey"], expected_stream)

        store = self.bridge._ai_trade_council_automation_default_store()
        store["state"].update({
            "candidateId": candidate,
            "streamKey": expected_stream,
            "symbol": "EURUSD.m",
            "timeframe": "H1",
        })
        self.bridge._save_ai_trade_council_automation_store(store)
        scope = self.bridge._ai_trade_council_history_scope(
            "active",
            expected_candidate_id=candidate,
            expected_stream_key=expected_stream,
            expected_symbol="EURUSD.m",
            expected_timeframe="H1",
        )
        gateway_history_row = {
            "candidateId": candidate,
            "streamKey": expected_stream,
            "symbol": "EURUSD.M",
            "timeframe": "H1",
        }

        self.assertTrue(
            self.bridge._ai_trade_council_row_in_history_scope(
                gateway_history_row,
                scope,
            )
        )
        self.assertEqual(scope["symbol"], "EURUSD.m")

    def test_durable_artifact_must_match_record_symbol_timeframe_and_bar(self) -> None:
        snapshot = {
            "selectedCandidateId": "mtc-artifact",
            "dailySummary": {},
            "chartSnapshot": {
                "available": True,
                "snapshotId": "f" * 64,
                "symbol": "EURUSD",
                "timeframe": "M15",
                "bars": [{"time": 1_500}],
            },
        }
        reference = self.bridge._write_ai_trade_council_snapshot_artifact(snapshot)
        artifact_path = self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR / reference
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        record = {
            "candidateId": "mtc-artifact",
            "symbol": "GBPJPY",
            "timeframe": "M15",
            "closedBarTime": 1_500,
            "snapshotId": "f" * 64,
            "snapshotArtifact": reference,
            "snapshotArtifactDigest": artifact["artifactDigest"],
        }

        self.assertIsNone(
            self.bridge._ai_trade_council_snapshot_from_artifact(record)
        )

    def test_canonical_instrument_maps_only_known_fx_prefixes(self) -> None:
        eurusd = self.bridge._ai_trade_council_canonical_instrument("EURUSD")
        suffixed = self.bridge._ai_trade_council_canonical_instrument("eurusd.m")
        hash_suffixed = self.bridge._ai_trade_council_canonical_instrument("EURUSD#")
        gbpjpy = self.bridge._ai_trade_council_canonical_instrument("GBPJPY")
        unknown = self.bridge._ai_trade_council_canonical_instrument("ABCDEF")

        self.assertEqual(eurusd["canonicalSymbol"], "EURUSD")
        self.assertEqual(eurusd["assetClass"], "forex")
        self.assertEqual(eurusd["baseCurrency"], "EUR")
        self.assertEqual(eurusd["quoteCurrency"], "USD")
        self.assertEqual(suffixed["canonicalSymbol"], "EURUSD")
        self.assertEqual(suffixed["observedSymbol"], "EURUSD.M")
        self.assertEqual(hash_suffixed["canonicalSymbol"], "EURUSD")
        self.assertEqual(gbpjpy["canonicalSymbol"], "GBPJPY")
        self.assertEqual(unknown["mappingStatus"], "identity_only")
        self.assertEqual(unknown["assetClass"], "unknown")

    def test_max_order_history_reconciliation_ignores_another_chart_stream(self) -> None:
        candidate = "mtc-active"
        symbol = "EURUSD"
        timeframe = "M15"
        status = {
            "selectedCandidateId": candidate,
            "symbol": symbol,
            "timeframe": timeframe,
            "maxManagedPositions": 10,
            "currentManagedPositions": 0,
            "orderHistory": {
                "schemaVersion": "metafx-hq-mt4-order-history-v1",
                "available": True,
                "sourceScope": "durable_selected_channel_executed_ack_plus_identity_exact_execution_unknown",
                "items": [{
                    "candidateId": "mtc-old",
                    "streamKey": self.bridge._ai_trade_council_stream_key(
                        "mtc-old",
                        "XAUUSD",
                        "M5",
                    ),
                    "symbol": "XAUUSD",
                    "timeframe": "M5",
                    "ticket": 123456,
                    "executionState": "OPEN",
                }],
            },
        }

        model = self.bridge._ai_trade_council_managed_order_limit_model(status)

        self.assertEqual(model["currentManagedPositions"], 0)
        self.assertFalse(model["reached"])

    def test_order_history_scans_past_500_with_authoritative_gateway_pages(self) -> None:
        newest = []
        for index in range(500):
            command_id = f"cmd-{index:024x}"
            newest.append({
                "command": {
                    "commandId": command_id,
                    "channelId": "mtc-current",
                    "action": "BUY",
                    "symbol": "EURUSD",
                    "timeframe": "H1",
                },
                "ack": None,
                "createdAt": f"2026-08-12T01:{index % 60:02d}:00Z",
            })
        old_command_id = "cmd-ffffffffffffffffffffffff"
        old_executed = {
            "command": {
                "commandId": old_command_id,
                "channelId": "mtc-old-channel",
                "missionId": "mission-old-order",
                "snapshotId": "f" * 64,
                "councilDecisionId": "council-" + "f" * 24,
                "action": "SELL",
                "symbol": "XAUUSD",
                "timeframe": "M5",
            },
            "status": "ack_EXECUTED",
            "outstanding": False,
            "createdAt": "2026-08-11T01:00:00Z",
            "updatedAt": "2026-08-11T01:00:01Z",
            "ack": {
                "status": "EXECUTED",
                "reasonCode": "ORDER_ACCEPTED",
                "observedAt": 1_786_435_200,
                "ticket": 987654,
                "fixedLot": 0.01,
                "filledPrice": 4_380.0,
                "actualStopLoss": 4_390.0,
                "actualTakeProfit": 4_360.0,
                "actualMagicNumber": 4_186_001,
                "actualComment": f"HQ:{old_command_id}",
                "verificationStatus": "VERIFIED_OPEN",
                "statePersisted": True,
                "mode": "demo",
            },
        }

        class FakeGateway:
            def __init__(self) -> None:
                self.calls: list[tuple[int, str | None, str | None]] = []

            def list_commands_page(
                self,
                *,
                limit: int,
                cursor: str | None,
                channel_id: str | None,
            ) -> dict:
                self.calls.append((limit, cursor, channel_id))
                if cursor is None:
                    return {
                        "records": newest,
                        "total": 501,
                        "hasMore": True,
                        "nextCursor": newest[-1]["command"]["commandId"],
                        "cursorFound": True,
                        "channelId": channel_id,
                    }
                return {
                    "records": [old_executed],
                    "total": 501,
                    "hasMore": False,
                    "nextCursor": None,
                    "cursorFound": True,
                    "channelId": channel_id,
                }

            def read_outcome(self, _command_id: str) -> None:
                return None

        gateway = FakeGateway()
        history = self.bridge._mt4_trade_gateway_order_history(
            gateway,
            selected_candidate_id="mtc-current",
            limit=None,
            include_all_channels=True,
        )

        self.assertTrue(history["available"])
        self.assertEqual(history["totalExecuted"], 1)
        self.assertEqual(history["items"][0]["commandId"], old_command_id)
        self.assertEqual(history["items"][0]["candidateId"], "mtc-old-channel")
        self.assertEqual(history["historyWindow"]["scannedCommands"], 501)
        self.assertEqual(history["historyWindow"]["pageCount"], 2)
        self.assertTrue(history["historyWindow"]["complete"])
        self.assertEqual(gateway.calls[0], (500, None, None))
        self.assertEqual(gateway.calls[1][2], None)

    def test_all_order_history_uses_global_ledger_without_selected_terminal(self) -> None:
        command_id = "cmd-" + "d" * 24
        record = {
            "command": {
                "commandId": command_id,
                "channelId": "mtc-historical-channel",
                "action": "BUY",
                "symbol": "EURUSD",
                "timeframe": "H1",
            },
            "status": "ack_EXECUTED",
            "outstanding": False,
            "createdAt": "2026-08-11T01:00:00Z",
            "updatedAt": "2026-08-11T01:00:01Z",
            "ack": {
                "status": "EXECUTED",
                "reasonCode": "ORDER_ACCEPTED",
                "observedAt": 1_786_435_200,
                "ticket": 987654,
                "fixedLot": 0.01,
                "filledPrice": 1.15,
                "actualStopLoss": 1.14,
                "actualTakeProfit": 1.17,
                "actualMagicNumber": 4_186_001,
                "actualComment": f"HQ:{command_id}",
                "verificationStatus": "VERIFIED_OPEN",
                "statePersisted": True,
                "mode": "demo",
            },
        }

        class FakeGateway:
            def __init__(self) -> None:
                self.channels: list[str | None] = []

            def list_commands_page(
                self,
                *,
                limit: int,
                cursor: str | None,
                channel_id: str | None,
            ) -> dict:
                self.channels.append(channel_id)
                return {
                    "records": [record],
                    "total": 1,
                    "hasMore": False,
                    "nextCursor": None,
                    "cursorFound": True,
                    "channelId": channel_id,
                }

            def read_outcome(self, _command_id: str) -> None:
                return None

        gateway = FakeGateway()
        with mock.patch.object(
            self.bridge,
            "_selected_metatrader_candidate_record",
            return_value=None,
        ), mock.patch.object(
            self.bridge,
            "_mt4_trade_gateway_instance",
            return_value=gateway,
        ), mock.patch.object(
            self.bridge,
            "load_missions",
            return_value=[],
        ):
            model = self.bridge.ai_trade_council_order_history_page_read_model(
                scope=self.bridge._ai_trade_council_history_scope("all"),
            )

        self.assertTrue(model["available"])
        self.assertEqual(model["scope"]["mode"], "all")
        self.assertTrue(model["scope"]["authoritative"])
        self.assertEqual(model["summary"]["total"], 1)
        self.assertEqual(model["items"][0]["candidateId"], "mtc-historical-channel")
        self.assertEqual(gateway.channels, [None])

    def test_active_order_history_still_requires_selected_mt4_terminal(self) -> None:
        scope = {
            "mode": "active",
            "authoritative": True,
            "candidateId": "mtc-active",
            "channelId": "mtc-active",
            "streamKey": self.bridge._ai_trade_council_stream_key(
                "mtc-active",
                "EURUSD",
                "H1",
            ),
            "symbol": "EURUSD",
            "timeframe": "H1",
        }
        with mock.patch.object(
            self.bridge,
            "_selected_metatrader_candidate_record",
            return_value=None,
        ):
            model = self.bridge.ai_trade_council_order_history_page_read_model(
                scope=scope,
            )

        self.assertFalse(model["available"])
        self.assertEqual(model["reasonCode"], "selected_mt4_channel_missing")

    def test_active_order_history_fails_closed_when_selection_changes_mid_read(self) -> None:
        scope = {
            "mode": "active",
            "authoritative": True,
            "candidateId": "mtc-active-before-switch",
            "channelId": "mtc-active-before-switch",
            "streamKey": self.bridge._ai_trade_council_stream_key(
                "mtc-active-before-switch",
                "EURUSD",
                "H1",
            ),
            "symbol": "EURUSD",
            "timeframe": "H1",
        }
        gateway_must_not_run = AssertionError(
            "mismatched active selection must fail before reading the ledger"
        )
        with (
            mock.patch.object(
                self.bridge,
                "_selected_metatrader_candidate_record",
                return_value={"candidateId": "mtc-active-after-switch"},
            ),
            mock.patch.object(
                self.bridge,
                "_public_metatrader_candidate",
                return_value={
                    "candidateId": "mtc-active-after-switch",
                    "platform": "mt4",
                },
            ),
            mock.patch.object(
                self.bridge,
                "_mt4_trade_gateway_instance",
                side_effect=gateway_must_not_run,
            ),
        ):
            model = self.bridge.ai_trade_council_order_history_page_read_model(
                scope=scope,
            )

        self.assertFalse(model["available"])
        self.assertEqual(model["items"], [])
        self.assertEqual(model["reasonCode"], "selected_mt4_channel_changed")

    def test_consensus_stream_identity_fails_closed_on_provenance_mismatch(self) -> None:
        snapshot_id = "a" * 64
        context_identity = {
            "candidateId": "mtc-context-chart",
            "streamKey": self.bridge._ai_trade_council_stream_key(
                "mtc-context-chart",
                "EURUSD.m",
                "H1",
            ),
            "symbol": "EURUSD.m",
            "timeframe": "H1",
            "closedBarTime": 1_786_474_000,
        }
        provenance_identity = {
            "candidateId": "mtc-other-chart",
            "streamKey": self.bridge._ai_trade_council_stream_key(
                "mtc-other-chart",
                "XAUUSD",
                "M5",
            ),
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "closedBarTime": 1_786_474_000,
        }
        projection = self.bridge._ai_trade_council_consensus_stream_identity(
            {
                "analysisContext": {
                    "snapshotId": snapshot_id,
                    "closedBarIdentity": context_identity,
                },
            },
            {
                "snapshotId": snapshot_id,
                "decisionProvenance": {
                    "snapshotId": snapshot_id,
                    "closedBarIdentity": provenance_identity,
                },
            },
        )

        self.assertFalse(projection["identityValid"])
        self.assertEqual(
            projection["identityReasonCode"],
            "consensus_stream_identity_mismatch",
        )
        for field in (
            "candidateId",
            "channelId",
            "streamKey",
            "symbol",
            "timeframe",
            "snapshotId",
            "closedBarIdentity",
            "streamIdentity",
        ):
            self.assertIsNone(projection[field])

    def test_bangkok_day_rollover_expires_prior_day_pending_without_replay(self) -> None:
        pending = self._record(
            candidate="mtc-rollover",
            symbol="EURUSD",
            timeframe="H1",
            bar_time=1_786_435_200,
        )
        pending["detectedAt"] = "2026-08-11T16:55:00+00:00"
        store = self.bridge._ai_trade_council_automation_default_store()
        store["config"].update({
            "dailyRoundLimitMode": "limited",
            "maxDailyRounds": 1,
        })
        store["state"].update({
            "dailyRunDate": "2026-08-11",
            "dailyRunCount": 1,
            "candidateId": pending["candidateId"],
            "streamKey": pending["streamKey"],
            "symbol": pending["symbol"],
            "timeframe": pending["timeframe"],
            "coverageRecords": [pending],
            "pendingQueue": [pending],
            "pendingClosedBarTime": pending["closedBarTime"],
            "pendingSnapshotId": pending["snapshotId"],
            "pendingDetectedAt": pending["detectedAt"],
        })

        rolled, changed = self.bridge._rollover_ai_trade_council_automation_day(
            store,
            datetime(2026, 8, 12, 0, 5, tzinfo=self.bridge.THAILAND_TIMEZONE),
        )

        self.assertTrue(changed)
        self.assertEqual(rolled["state"]["dailyRunDate"], "2026-08-12")
        self.assertEqual(rolled["state"]["dailyRunCount"], 0)
        self.assertEqual(rolled["state"]["pendingQueue"], [])
        self.assertEqual(rolled["state"]["status"], "skipped")
        self.assertEqual(
            rolled["state"]["reason"],
            "pending_expired_at_bangkok_day_boundary",
        )
        self.assertIsNone(rolled["state"]["pendingClosedBarTime"])
        expired = rolled["state"]["coverageRecords"][0]
        self.assertEqual(expired["status"], "skipped")
        self.assertEqual(
            expired["reasonCode"],
            "pending_expired_at_bangkok_day_boundary",
        )
        self.assertEqual(
            expired["executionPolicy"],
            "audit_only_no_stale_dispatch",
        )

    def test_legacy_selection_revision_migrates_and_next_generation_increments(self) -> None:
        candidate = "mtc-legacy-selection"
        self.bridge.RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        legacy_store = {
            "schemaVersion": 1,
            "candidates": {},
            "selections": {
                self.bridge.AI_TRADE_COUNCIL_PROP_ID: {
                    "candidateId": candidate,
                    "selectedAt": "2026-08-11T00:00:00Z",
                },
            },
            "updatedAt": None,
        }
        self.bridge._metatrader_target_store_path().write_text(
            json.dumps(legacy_store),
            encoding="utf-8",
        )

        token = self.bridge._metatrader_selection_token(
            self.bridge.AI_TRADE_COUNCIL_PROP_ID
        )
        saved = self.bridge._load_metatrader_target_store_unlocked()

        self.assertEqual(token["selectionRevision"], 1)
        self.assertEqual(
            saved["schemaVersion"],
            self.bridge.METATRADER_TARGET_STORE_SCHEMA_VERSION,
        )
        self.assertEqual(
            saved["selections"][self.bridge.AI_TRADE_COUNCIL_PROP_ID][
                "selectionRevision"
            ],
            1,
        )
        self.assertEqual(
            self.bridge._metatrader_next_selection_revision(
                saved["selections"][self.bridge.AI_TRADE_COUNCIL_PROP_ID]
            ),
            2,
        )

    def test_selection_change_between_status_and_publish_blocks_without_queue(self) -> None:
        queued = []

        class FakeGateway:
            def queue_trade_intent(self, intent: dict) -> dict:
                queued.append(intent)
                return {"command": {"commandId": "cmd-" + "a" * 24}}

            def read_command(self, _command_id: str) -> dict:
                return {}

        tokens = [{
            "candidateId": "mtc-chart-a",
            "selectionRevision": 2,
        }]
        self.bridge._metatrader_selection_token = lambda _prop: tokens[0]
        self.bridge._mt4_trade_gateway_instance = lambda: FakeGateway()

        result = self.bridge._mt4_trade_gateway_publish_for_selection(
            {"channelId": "mtc-chart-a"},
            expected_candidate_id="mtc-chart-a",
            expected_selection_revision=1,
            expected_closed_bar_identity={
                "candidateId": "mtc-chart-a",
                "streamKey": self.bridge._ai_trade_council_stream_key(
                    "mtc-chart-a", "XAUUSD", "M5"
                ),
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "closedBarTime": 1_786_470_000,
            },
            analysis_context={},
            maximum_signal_drift_points=100,
            minimum_reward_risk_ratio=1.0,
            maximum_snapshot_age_seconds=300,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(
            result["reasonCode"],
            "terminal_selection_changed_before_publish",
        )
        self.assertEqual(queued, [])


if __name__ == "__main__":
    unittest.main()
