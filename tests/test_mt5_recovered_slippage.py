from __future__ import annotations

import json
import unittest

import test_mt4_trade_gateway as fixtures


class MT5RecoveredSlippageTests(unittest.TestCase):
    """Real durable gateway, temporary signed channels; no terminal or broker."""

    setUp = fixtures.MT4TradeGatewayTests.setUp
    tearDown = fixtures.MT4TradeGatewayTests.tearDown
    gateway = fixtures.MT4TradeGatewayTests.gateway
    intent = fixtures.MT4TradeGatewayTests.intent
    ack = fixtures.MT4TradeGatewayTests.ack

    def mt5(self):
        return self.gateway(wire_platform="mt5", wire_account_binding_id="a" * 64)

    def fill(self, command, **overrides):
        return self.ack(command, **{
            "status": "EXECUTED", "reasonCode": "RECOVERED_ORDER_FOUND",
            "mode": "demo", "ticket": 123456, "filledPrice": 3300.25,
            "filledSlippagePoints": None, "filledSlippageKnown": False,
            "actualStopLoss": command["stopLoss"],
            "actualTakeProfit": command["takeProfit"],
            "actualMagicNumber": 4186001,
            "actualComment": f"HQ:{command['commandId']}",
            "verificationStatus": "VERIFIED_OPEN", "executionState": "OPEN",
            **overrides,
        })

    def test_recovered_unknown_slippage_is_null_and_idempotent_across_restart(self):
        gateway = self.mt5()
        command = gateway.queue_trade_intent(self.intent())["command"]
        wire = self.fill(command)
        result = gateway.ingest_ack(wire)
        self.assertTrue(result["outstandingReleased"])
        self.assertIsNone(result["ack"]["filledSlippagePoints"])
        self.assertIs(result["ack"]["filledSlippageKnown"], False)
        restarted = self.mt5()
        before = restarted.status()["ledgerRevision"]
        replay = restarted.ingest_ack(wire)
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(restarted.status()["ledgerRevision"], before)
        self.assertEqual(len(restarted.list_commands(limit=10)), 1)
        # Generic read-only ledger readers also retain the MT5 evidence.
        self.assertIsNone(self.gateway().read_command(command["commandId"])["ack"]["filledSlippagePoints"])
        with self.assertRaises(self.gateway_module.OneOrderPerBarError):
            restarted.queue_trade_intent(self.intent(snapshotId="b" * 64, missionId="mission-other"))

    def test_unknown_submission_can_recover_closed_fill_without_inventing_slippage(self):
        gateway = self.mt5()
        command = gateway.queue_trade_intent(self.intent())["command"]
        gateway.ingest_ack(self.ack(command, status="EXECUTION_UNKNOWN",
                                    reasonCode="ORDER_SEND_API_UNCERTAIN", mode="demo"))
        wire = self.fill(command, executionState="CLOSED", verificationStatus="VERIFIED_CLOSED",
                         closedAt=int(self.clock.current.timestamp()) + 60, closedPnl=-3.25)
        result = gateway.ingest_ack(wire)
        self.assertTrue(result["outstandingReleased"])
        self.assertEqual(result["ack"]["reasonCode"], "EXECUTION_RECONCILED_WITH_WARNING")
        record = self.mt5().read_command(command["commandId"])
        self.assertIs(record["ack"]["filledSlippageKnown"], False)
        self.assertIsNone(record["ack"]["filledSlippagePoints"])
        self.assertEqual(record["ack"]["closedPnl"], -3.25)
        durable = json.loads((self.state_root / "mt4-trade-gateway-ledger.json").read_text(encoding="ascii"))
        recovery = durable["commands"][command["commandId"]]["recovery"]
        self.assertTrue(recovery["barClaimRetained"])
        self.assertEqual(recovery["provenance"], "mt5_account_bound_command_envelope")

    def test_prior_measured_slippage_survives_unknown_recovery(self):
        gateway = self.mt5()
        command = gateway.queue_trade_intent(self.intent())["command"]
        gateway.ingest_ack(self.fill(command, status="EXECUTION_UNKNOWN",
                                    reasonCode="ORDER_POST_SEND_VERIFICATION_MISMATCH",
                                    verificationStatus="MISMATCH",
                                    filledSlippageKnown=True, filledSlippagePoints=22.0))
        result = gateway.ingest_ack(self.fill(command))
        self.assertEqual(result["ack"]["filledSlippagePoints"], 22.0)
        self.assertIs(result["ack"]["filledSlippageKnown"], True)
        self.assertEqual(result["ack"]["reasonCode"], "EXECUTION_RECONCILED_WITH_WARNING")
        self.assertEqual(self.mt5().read_command(command["commandId"])["ack"]["filledSlippagePoints"], 22.0)

    def test_unmeasurable_direct_fill_recovers_only_the_previously_matched_ticket(self):
        gateway = self.mt5()
        command = gateway.queue_trade_intent(self.intent())["command"]
        gateway.ingest_ack(self.ack(
            command, status="EXECUTION_UNKNOWN", mode="demo", ticket=123456,
            reasonCode="EXECUTION_SLIPPAGE_EVIDENCE_UNAVAILABLE",
            verificationStatus="MISMATCH", executionState="UNKNOWN",
        ))
        with self.assertRaises(self.gateway_module.AckConflictError):
            gateway.ingest_ack(self.fill(command, ticket=654321))
        self.assertTrue(gateway.read_command(command["commandId"])["outstanding"])
        result = gateway.ingest_ack(self.fill(command))
        self.assertTrue(result["outstandingReleased"])
        self.assertEqual(result["ack"]["ticket"], 123456)
        self.assertIs(result["ack"]["filledSlippageKnown"], False)
        self.assertIsNone(result["ack"]["filledSlippagePoints"])
        self.assertEqual(len(self.mt5().list_commands(limit=10)), 1)

    def test_direct_observed_fill_marker_and_legacy_numeric_ack_remain_valid(self):
        gateway = self.mt5()
        command = gateway.queue_trade_intent(self.intent())["command"]
        direct = self.fill(command, reasonCode="ORDER_VERIFIED_OPEN",
                           filledSlippageKnown=True, filledSlippagePoints=2.5)
        normalized, _ = gateway._normalize_ack(direct)
        self.assertIs(normalized["filledSlippageKnown"], True)
        legacy = {k: v for k, v in direct.items() if k != "filledSlippageKnown"}
        self.assertNotIn("filledSlippageKnown", gateway._normalize_ack(legacy)[0])
        legacy["filledSlippagePoints"] = None
        with self.assertRaises(self.gateway_module.AckValidationError):
            gateway.ingest_ack(legacy)

    def test_unknown_extension_rejects_forged_or_partial_evidence_before_release(self):
        gateway = self.mt5()
        command = gateway.queue_trade_intent(self.intent())["command"]
        invalid = [
            {"filledSlippageKnown": None}, {"filledSlippageKnown": 0},
            {"filledSlippageKnown": "false"}, {"filledSlippageKnown": True},
            {"filledSlippagePoints": 0}, {"filledSlippagePoints": "0"},
            {"reasonCode": "ORDER_VERIFIED_OPEN"},
            {"reasonCode": "EXECUTION_RECONCILED_WITH_WARNING"},
            {"statePersisted": False}, {"verificationStatus": "MISMATCH"},
            {"verificationStatus": "VERIFIED_CLOSED"}, {"executionState": "UNKNOWN"},
            {"status": "EXECUTION_UNKNOWN"}, {"status": "SHADOWED"},
            {"ticket": None}, {"filledPrice": None}, {"actualStopLoss": None},
            {"actualTakeProfit": None}, {"actualMagicNumber": None},
            {"actualComment": "unrelated"}, {"signatureVerificationStatus": "FAILED"},
            {"snapshotId": "b" * 64}, {"actualStopLoss": 3200},
        ]
        for change in invalid:
            with self.subTest(change=change):
                with self.assertRaises(self.gateway_module.TradeGatewayError):
                    gateway.ingest_ack(self.fill(command, **change))
                self.assertTrue(gateway.read_command(command["commandId"])["outstanding"])
                self.assertEqual(len(gateway.list_commands(limit=10)), 1)
        for marker, points in ((False, None), (True, 0.0)):
            with self.subTest(mt4_marker=marker):
                with self.assertRaises(self.gateway_module.AckValidationError):
                    self.gateway().ingest_ack(self.fill(command, filledSlippageKnown=marker,
                                                        filledSlippagePoints=points))

    def test_corrupted_durable_marker_fails_closed_without_resend(self):
        gateway = self.mt5()
        command = gateway.queue_trade_intent(self.intent())["command"]
        gateway.ingest_ack(self.fill(command))
        ledger_path = self.state_root / "mt4-trade-gateway-ledger.json"
        pristine = json.loads(ledger_path.read_text(encoding="ascii"))
        for change in ({"filledSlippagePoints": 0}, {"filledSlippageKnown": True},
                       {"filledSlippageKnown": "false"}, {"reasonCode": "ORDER_VERIFIED_OPEN"}):
            with self.subTest(change=change):
                ledger = json.loads(json.dumps(pristine))
                ledger["commands"][command["commandId"]]["ack"].update(change)
                ledger_path.write_text(json.dumps(ledger), encoding="ascii")
                with self.assertRaises(self.gateway_module.LedgerIntegrityError):
                    self.mt5().status()
        ledger_path.write_text(json.dumps(pristine), encoding="ascii")


if __name__ == "__main__":
    unittest.main()
