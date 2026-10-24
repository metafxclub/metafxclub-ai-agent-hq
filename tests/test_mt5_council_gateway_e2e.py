from __future__ import annotations

import hashlib
import json
import unittest
from datetime import datetime, timedelta, timezone

import test_ai_trade_council_gateway_e2e as council_fixtures
import test_mt4_trade_gateway_bridge as status_fixtures


class MT5CouncilGatewayE2ETests(unittest.TestCase):
    """Offline MT5 domain: real consensus, preflight, HMAC, ledger and ACK parsing.

    Quotes, EA status and broker fill are fixtures in TemporaryDirectory. This
    does not prove native execution or submit any real broker order.
    """

    tearDown = council_fixtures.AiTradeCouncilGatewayE2ETests.tearDown
    install_analysis_artifact = council_fixtures.AiTradeCouncilGatewayE2ETests.install_analysis_artifact
    executed_ack = council_fixtures.AiTradeCouncilGatewayE2ETests.executed_ack
    status_path = status_fixtures.Mt4TradeGatewayBridgeTests.status_path
    signing_key_id = status_fixtures.Mt4TradeGatewayBridgeTests.signing_key_id
    write_ea_status = status_fixtures.Mt4TradeGatewayBridgeTests.write_ea_status
    confirmed_live_policy_status = staticmethod(status_fixtures.Mt4TradeGatewayBridgeTests.confirmed_live_policy_status)
    write_mt5_price_risk_status = status_fixtures.Mt4TradeGatewayBridgeTests.write_mt5_price_risk_status

    @classmethod
    def setUpClass(cls):
        cls.bridge = council_fixtures.load_bridge()

    def setUp(self):
        council_fixtures.AiTradeCouncilGatewayE2ETests.setUp(self)
        self.candidate = {
            "candidateId": "mtc-safe-e2e-test", "platform": "mt5",
            "available": True, "ordinal": 1, "runningState": "platform_running_detected",
        }
        self.selection_revision = 1
        self.binding = "b" * 64
        self.quote_age = 0
        self.bid, self.ask = 2400.0, 2400.2  # A new tick, within the 100-point gate.
        self.bridge._active_global_metatrader_context = lambda **_kwargs: {
            "record": dict(self.candidate),
            "token": {"candidateId": self.candidate["candidateId"],
                      "selectionRevision": self.selection_revision, "platform": "mt5"},
            "selectedAt": "2026-10-16T00:00:00+00:00",
        }
        self.write_mt5_price_risk_status(mode="demo", demoAccount=True, accountMode="demo",
                                         liveArmed=False, eaVersion="1.06")
        self.bridge.mt4_trade_gateway_status_read_model = self.original_status_reader
        self.write_snapshot()

    def write_snapshot(self):
        payload = {
            "schemaVersion": self.bridge.METATRADER_SNAPSHOT_SCHEMA_VERSION,
            "adapterId": self.candidate["candidateId"], "mode": "read_only",
            "terminalPlatform": "mt5", "accountBindingId": self.binding,
            "observedAt": datetime.now(timezone.utc).isoformat(),
            "bid": self.bid, "ask": self.ask,
        }
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        path = self.bridge._metatrader_snapshot_file(self.candidate["candidateId"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        self.current_snapshot_id = hashlib.sha256(raw).hexdigest()

    def current_snapshot(self, prop_id):
        snapshot = council_fixtures.AiTradeCouncilGatewayE2ETests.current_snapshot(self, prop_id)
        snapshot["chartSnapshot"].update({
            "snapshotId": self.current_snapshot_id,
            "bid": self.bid, "ask": self.ask,
            "ageSeconds": self.quote_age,
            "observedAt": (datetime.now(timezone.utc) - timedelta(seconds=self.quote_age)).isoformat(),
        })
        return snapshot

    def round(self, *, analysis_age=80):
        parent, children = council_fixtures.AiTradeCouncilGatewayE2ETests.council_round(self)
        parent["analysisContext"]["requiredVotes"] = 2
        parent["analysisContext"]["snapshotObservedAt"] = (
            datetime.now(timezone.utc) - timedelta(seconds=analysis_age)
        ).isoformat()
        for child in children:
            if child["councilVote"]["roleId"] == "technical":
                child["councilVote"].update(decision="BUY", stopLossPrice=2380.0, takeProfitPrice=2421.0)
        self.install_analysis_artifact(parent)
        self.write_snapshot()
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        self.assertTrue(consensus["ready"])
        self.assertEqual(consensus["voteCount"], 3)
        self.assertEqual(consensus["directionalVoteCount"], 2)
        self.assertTrue(consensus["qualityGate"]["passed"])
        return parent, consensus

    def gateway(self, binding=None):
        return self.bridge._mt4_trade_gateway_instance(mt5_account_binding_id=binding or "b" * 64)

    def assert_no_command(self, result):
        self.assertFalse(result["commandPublished"])
        self.assertEqual(self.gateway().list_commands(limit=10), [])
        self.assertFalse(self.status_path().with_name("command.json").exists())

    def test_three_votes_new_tick_to_mt5_signed_command_verified_fill_and_no_resend(self):
        parent, consensus = self.round()
        self.assertNotEqual(self.current_snapshot_id, consensus["snapshotId"])
        result = self.bridge.dispatch_ai_trade_council_trade_plan(parent, consensus)
        self.assertEqual(result["status"], "queued", result)
        gateway = self.gateway()
        command_id = result["commandId"]
        command = gateway.read_command(command_id)["command"]
        self.assertEqual(command["snapshotId"], parent["analysisContext"]["snapshotId"])
        self.assertEqual(command["referencePrice"], 2400.1)
        self.assertGreaterEqual(result["executionPricePreflight"]["analysisSnapshotAgeSeconds"], 80)
        self.assertEqual(result["executionPricePreflight"]["status"], "passed")
        self.assertNotIn("fixedLot", command)
        self.assertNotIn("riskCostBasis", command)
        # Real HMAC verification must bind both MT5 and this account.
        self.assertEqual(gateway._read_command_slot(command["channelId"]), command)
        for wrong_gateway in (self.gateway("c" * 64), self.bridge._mt4_trade_gateway_instance()):
            with self.assertRaises(self.bridge.MT4_TRADE_GATEWAY_MODULE.TradeGatewayError):
                wrong_gateway._read_command_slot(command["channelId"])
        path = self.status_path().with_name("command.json")
        original = path.read_bytes()
        damaged = json.loads(original)
        damaged["signatureHex"] = "0" * 64
        path.write_text(json.dumps(damaged), encoding="ascii")
        with self.assertRaises(self.bridge.MT4_TRADE_GATEWAY_MODULE.TradeGatewayError):
            gateway._read_command_slot(command["channelId"])
        path.write_bytes(original)
        ack = self.executed_ack(command)
        ack.update(reasonCode="ORDER_VERIFIED_OPEN", filledSlippageKnown=True,
                   filledPrice=2400.2, filledSlippagePoints=10.0)
        accepted = gateway.ingest_ack(ack)
        self.assertTrue(accepted["outstandingReleased"])
        summary = self.bridge._mt4_trade_gateway_command_summary(gateway.read_command(command_id))
        self.assertIs(summary["ack"]["filledSlippageKnown"], True)
        self.assertEqual(summary["ack"]["filledSlippagePoints"], 10.0)
        legacy_record = gateway.read_command(command_id)
        legacy_record["ack"].pop("filledSlippageKnown")
        legacy_summary = self.bridge._mt4_trade_gateway_command_summary(legacy_record)
        self.assertNotIn("filledSlippageKnown", legacy_summary["ack"])
        self.assertEqual(legacy_summary["ack"]["filledSlippagePoints"], 10.0)
        self.assertTrue(gateway.ingest_ack(ack)["idempotentReplay"])
        parent["tradeGateway"] = {"commandId": command_id}
        repeated = self.bridge.dispatch_ai_trade_council_trade_plan(parent, consensus)
        self.assertEqual(repeated["status"], "ack_executed")
        self.assertTrue(repeated["orderExecutionConfirmed"])
        self.assertEqual(len(gateway.list_commands(limit=10)), 1)
        self.assertEqual(path.read_bytes(), original)

    def test_mt5_recovered_unknown_slippage_summary_stays_null(self):
        parent, consensus = self.round()
        result = self.bridge.dispatch_ai_trade_council_trade_plan(parent, consensus)
        self.assertEqual(result["status"], "queued", result)
        gateway = self.gateway()
        command = gateway.read_command(result["commandId"])["command"]
        ack = self.executed_ack(command)
        ack.update(reasonCode="RECOVERED_ORDER_FOUND", filledSlippageKnown=False, filledSlippagePoints=None)
        gateway.ingest_ack(ack)
        summary = self.bridge._mt4_trade_gateway_command_summary(gateway.read_command(command["commandId"]))
        self.assertIs(summary["ack"]["filledSlippageKnown"], False)
        self.assertIsNone(summary["ack"]["filledSlippagePoints"])

    def test_same_bar_excessive_drift_is_rejected_without_repricing(self):
        parent, consensus = self.round()
        self.bid, self.ask = 2401.0, 2401.2
        self.write_snapshot()
        result = self.bridge.dispatch_ai_trade_council_trade_plan(parent, consensus)
        self.assertEqual(result["reasonCode"], "signal_price_drift_exceeded_before_publish", result)
        self.assert_no_command(result)

    def test_same_bar_stale_quote_is_rejected(self):
        parent, consensus = self.round()
        self.quote_age = self.bridge.METATRADER_SNAPSHOT_FRESH_SECONDS + 1
        result = self.bridge.dispatch_ai_trade_council_trade_plan(parent, consensus)
        self.assertEqual(result["reasonCode"], "execution_quote_stale_before_publish", result)
        self.assert_no_command(result)

    def test_closed_bar_advance_is_rejected_even_with_fresh_tick(self):
        parent, consensus = self.round()
        self.current_broker_closed_bar += 300
        self.write_snapshot()
        result = self.bridge.dispatch_ai_trade_council_trade_plan(parent, consensus)
        self.assertEqual(result["reasonCode"], "closed_bar_advanced_during_analysis", result)
        self.assert_no_command(result)

    def test_stale_analysis_and_changed_account_fail_closed(self):
        parent, consensus = self.round(analysis_age=301)
        result = self.bridge.dispatch_ai_trade_council_trade_plan(parent, consensus)
        self.assertEqual(result["reasonCode"], "analysis_snapshot_stale_before_publish", result)
        self.assert_no_command(result)
        parent, consensus = self.round()
        self.binding = "c" * 64
        self.write_snapshot()
        result = self.bridge.dispatch_ai_trade_council_trade_plan(parent, consensus)
        self.assertEqual(result["reasonCode"], "gateway_account_binding_mismatch", result)
        self.assert_no_command(result)

    def test_mt5_manual_three_vote_round_remains_analysis_only(self):
        parent, consensus = self.round()
        parent["analysisContext"].pop("automation")
        result = self.bridge.dispatch_ai_trade_council_trade_plan(parent, consensus)
        self.assertEqual(result["reasonCode"], "manual_analysis_only")
        self.assert_no_command(result)


if __name__ == "__main__":
    unittest.main()
