from __future__ import annotations

import json
import unittest
from unittest.mock import patch

import test_mt4_trade_gateway as fixtures


MT5_TICKET = 500_029_817_749
MT5_MAX_TICKET = (1 << 64) - 1


class MT5TicketRecoveryTests(unittest.TestCase):
    """Temporary signed channels only; never contact a terminal or broker."""

    setUp = fixtures.MT4TradeGatewayTests.setUp
    tearDown = fixtures.MT4TradeGatewayTests.tearDown
    gateway = fixtures.MT4TradeGatewayTests.gateway
    intent = fixtures.MT4TradeGatewayTests.intent
    ack = fixtures.MT4TradeGatewayTests.ack
    ack_path = fixtures.MT4TradeGatewayTests.ack_path
    command_path = fixtures.MT4TradeGatewayTests.command_path
    heartbeat_path = fixtures.MT4TradeGatewayTests.heartbeat_path
    outcome_path = fixtures.MT4TradeGatewayTests.outcome_path
    write_outcome = fixtures.MT4TradeGatewayTests.write_outcome

    def mt5(self):
        return self.gateway(wire_platform="mt5", wire_account_binding_id="a" * 64)

    def fill(self, command, **overrides):
        return self.ack(command, **{
            "status": "EXECUTED",
            "reasonCode": "ORDER_VERIFIED_OPEN_SLIPPAGE_RESERVE_AND_RISK_ESTIMATE_EXCEEDED",
            "mode": "demo",
            "ticket": MT5_TICKET,
            "filledSlippageKnown": True,
            "filledSlippagePoints": 4.0,
            **overrides,
        })

    def write_ack(self, command, payload):
        path = self.ack_path(command)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, separators=(",", ":")), encoding="ascii")
        return path

    def test_mt5_json_integer_boundaries_survive_ingestion_restart_and_replay(self):
        for index, ticket in enumerate((1, 2_147_483_647, 2_147_483_648,
                                         MT5_TICKET, (1 << 53) + 1, MT5_MAX_TICKET)):
            with self.subTest(ticket=ticket):
                gateway = self.mt5()
                command = gateway.queue_trade_intent(
                    self.intent(channelId=f"mtc-ticket-{index}")
                )["command"]
                wire = self.fill(command, ticket=ticket)
                path = self.write_ack(command, wire)
                result = gateway.ingest_ack_file(path)
                self.assertIs(type(result["ack"]["ticket"]), int)
                self.assertEqual(result["ack"]["ticket"], ticket)
                restarted = self.mt5()
                stored = restarted.read_command(command["commandId"])
                self.assertEqual(stored["ack"]["ticket"], ticket)
                self.assertEqual(json.loads(json.dumps(stored))["ack"]["ticket"], ticket)
                revision = restarted.status()["ledgerRevision"]
                replay = restarted.ingest_ack_file(path)
                self.assertTrue(replay["idempotentReplay"])
                self.assertEqual(restarted.status()["ledgerRevision"], revision)

    def test_mt5_rejects_non_integer_nonpositive_and_overflow_ticket_without_release(self):
        gateway = self.mt5()
        command = gateway.queue_trade_intent(self.intent())["command"]
        bad_tickets = (True, False, 0, -1, MT5_MAX_TICKET + 1,
                       float(MT5_TICKET), 1.5, "500029817749", "1e12", "", [], {})
        for ticket in bad_tickets:
            with self.subTest(ticket=ticket):
                with self.assertRaises(self.gateway_module.AckValidationError) as raised:
                    gateway.ingest_ack(self.fill(command, ticket=ticket))
                self.assertEqual(raised.exception.code, "invalid_ack_ticket")
                self.assertTrue(gateway.read_command(command["commandId"])["outstanding"])
                self.assertIsNone(gateway.read_command(command["commandId"])["ack"])

    def test_mt5_file_rejects_float_and_string_tokens_without_numeric_coercion(self):
        gateway = self.mt5()
        command = gateway.queue_trade_intent(self.intent())["command"]
        for ticket in (float(MT5_TICKET), str(MT5_TICKET), True):
            with self.subTest(ticket=ticket):
                path = self.write_ack(command, self.fill(command, ticket=ticket))
                with self.assertRaises(self.gateway_module.AckValidationError) as raised:
                    gateway.ingest_ack_file(path)
                self.assertEqual(raised.exception.code, "invalid_ack_ticket")

    def test_mt4_ticket_contract_remains_positive_int32(self):
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        for ticket in (1, 2_147_483_647):
            normalized, _ = gateway._normalize_ack(self.ack(
                command, status="EXECUTED", mode="demo", ticket=ticket,
            ))
            self.assertEqual(normalized["ticket"], ticket)
        for ticket in (True, 0, -1, 2_147_483_648, MT5_TICKET, MT5_MAX_TICKET):
            with self.subTest(ticket=ticket):
                with self.assertRaises(self.gateway_module.AckValidationError) as raised:
                    gateway.ingest_ack(self.ack(
                        command, status="EXECUTED", mode="demo", ticket=ticket,
                    ))
                self.assertEqual(raised.exception.code, "invalid_ack_ticket")

    def test_mt5_does_not_widen_timestamp_error_or_magic_fields(self):
        gateway = self.mt5()
        command = gateway.queue_trade_intent(self.intent())["command"]
        fields = {
            "snapshotObservedAt": "snapshot_observed_at",
            "barTime": "bar_time",
            "eaClosedBarTime": "ea_closed_bar_time",
            "observedAt": "observed_at",
            "closedAt": "closed_at",
            "errorCode": "error_code",
            "actualMagicNumber": "actual_magic_number",
        }
        for field, error_field in fields.items():
            for value in (2_147_483_648, True, 1.0, "1"):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(self.gateway_module.AckValidationError) as raised:
                        gateway._normalize_ack(self.fill(command, **{field: value}))
                    self.assertEqual(raised.exception.code, f"invalid_ack_{error_field}")

    def test_expired_pending_real_size_ticket_recovers_once_without_resending(self):
        gateway = self.mt5()
        intent = self.intent()
        command = gateway.queue_trade_intent(intent)["command"]
        original_command = self.command_path().read_bytes()
        original_heartbeat = self.heartbeat_path().read_bytes()
        wire = self.fill(command)
        self.write_ack(command, wire)
        self.clock.advance(120)
        gateway.expire_pending()
        pending = gateway.read_command(command["commandId"])
        self.assertEqual(pending["status"], "expired_waiting_ack")
        self.assertTrue(pending["outstanding"])
        with patch.object(gateway, "_write_command", side_effect=AssertionError("resend")), \
                patch.object(gateway, "_write_heartbeat", side_effect=AssertionError("heartbeat")):
            events = gateway.ingest_pending_acks()
            self.assertEqual(len(events), 1)
            self.assertTrue(events[0]["outstandingReleased"])
            self.assertEqual(events[0]["ack"]["ticket"], MT5_TICKET)
            self.assertEqual(events[0]["ack"]["reasonCode"], wire["reasonCode"])
            self.assertEqual(gateway.ingest_pending_acks(), [])
            self.assertTrue(gateway.ingest_ack(wire)["idempotentReplay"])
            self.assertTrue(gateway.queue_trade_intent(intent)["idempotentReplay"])
            with self.assertRaises(self.gateway_module.OneOrderPerBarError):
                gateway.queue_trade_intent(self.intent(
                    snapshotId="b" * 64, missionId="mission-second-attempt",
                ))
        self.assertEqual(self.command_path().read_bytes(), original_command)
        self.assertEqual(self.heartbeat_path().read_bytes(), original_heartbeat)
        self.assertEqual(len(gateway.list_commands(limit=10)), 1)
        self.assertIsNone(gateway.status()["activeCommandId"])
        stored = self.mt5().read_command(command["commandId"])
        self.assertEqual(stored["status"], "ack_EXECUTED")
        self.assertFalse(stored["outstanding"])

    def test_unpersisted_mt5_ack_does_not_release_until_same_persisted_ack(self):
        gateway = self.mt5()
        command = gateway.queue_trade_intent(self.intent())["command"]
        first = gateway.ingest_ack(self.fill(command, statePersisted=False))
        self.assertFalse(first["outstandingReleased"])
        second = gateway.ingest_ack(self.fill(command, statePersisted=True))
        self.assertTrue(second["outstandingReleased"])
        self.assertEqual(second["ack"]["ticket"], MT5_TICKET)

    def test_mt5_open_closed_outcome_preserves_full_ticket_and_fill_warning(self):
        for index, ticket in enumerate((MT5_TICKET, MT5_MAX_TICKET)):
            with self.subTest(ticket=ticket):
                gateway = self.mt5()
                command = gateway.queue_trade_intent(
                    self.intent(channelId=f"mtc-outcome-{index}")
                )["command"]
                gateway.ingest_ack(self.fill(command, ticket=ticket))
                self.write_outcome(command, ticket=ticket)
                opened = gateway.read_outcome(command["commandId"])
                self.assertEqual(opened["executionState"], "OPEN")
                self.assertEqual(opened["ticket"], ticket)
                self.write_outcome(command, ticket=ticket, executionState="CLOSED",
                                   closedAt=int(self.clock.current.timestamp()) + 60,
                                   closedPnl=16.54)
                closed = self.mt5().read_outcome(command["commandId"])
                self.assertEqual(closed["executionState"], "CLOSED")
                self.assertEqual(closed["ticket"], ticket)
                self.assertEqual(closed["closedPnl"], 16.54)
                # History uses a generic ledger reader across MT4/MT5 channels.
                self.assertEqual(self.gateway().read_outcome(command["commandId"]), closed)
                self.assertEqual(gateway.read_command(command["commandId"])["ack"]["reasonCode"],
                                 "ORDER_VERIFIED_OPEN_SLIPPAGE_RESERVE_AND_RISK_ESTIMATE_EXCEEDED")
                self.assertFalse(gateway.read_command(command["commandId"])["outstanding"])

    def test_outcome_rejects_malformed_overflow_or_different_exact_ticket(self):
        gateway = self.mt5()
        command = gateway.queue_trade_intent(self.intent())["command"]
        gateway.ingest_ack(self.fill(command, ticket=MT5_MAX_TICKET))
        for ticket in (True, 0, -1, float(MT5_TICKET), str(MT5_TICKET),
                       MT5_MAX_TICKET + 1, MT5_MAX_TICKET - 1):
            with self.subTest(ticket=ticket):
                self.write_outcome(command, ticket=ticket)
                with self.assertRaises(self.gateway_module.GatewayValidationError) as raised:
                    gateway.read_outcome(command["commandId"])
                self.assertEqual(raised.exception.code, "invalid_mt4_outcome")

    def test_generic_outcome_retains_existing_positive_integer_contract_with_uint64_cap(self):
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        for ticket in (2_147_483_647, 2_147_483_648, MT5_TICKET, MT5_MAX_TICKET):
            self.write_outcome(command, ticket=ticket)
            self.assertEqual(gateway.read_outcome(command["commandId"])["ticket"], ticket)
        self.write_outcome(command, ticket=MT5_MAX_TICKET + 1)
        with self.assertRaises(self.gateway_module.GatewayValidationError) as raised:
            gateway.read_outcome(command["commandId"])
        self.assertEqual(raised.exception.code, "invalid_mt4_outcome")

    def test_full_outcome_details_preserve_broker_costs_and_close_price(self):
        gateway = self.mt5()
        command = gateway.queue_trade_intent(self.intent())["command"]
        gateway.ingest_ack(self.fill(command))
        details = {field: None for field in self.gateway_module.OUTCOME_DETAIL_FIELDS}
        self.write_outcome(command, ticket=MT5_TICKET, **details)
        opened = self.gateway().read_outcome(command["commandId"])
        self.assertTrue(all(opened[field] is None for field in details))
        details.update(closePrice=3316.54, grossProfit=17.04,
                       commission=-0.3, swap=-0.1, fee=-0.1)
        self.write_outcome(command, ticket=MT5_TICKET, executionState="CLOSED",
                           closedAt=int(self.clock.current.timestamp()) + 60,
                           closedPnl=16.54, **details)
        closed = self.gateway().read_outcome(command["commandId"])
        self.assertEqual({field: closed[field] for field in details}, details)
        self.assertEqual(closed["closedPnl"], 16.54)

    def test_outcome_details_are_full_or_none_and_lifecycle_bound(self):
        gateway = self.mt5()
        command = gateway.queue_trade_intent(self.intent())["command"]
        gateway.ingest_ack(self.fill(command))
        details = {field: None for field in self.gateway_module.OUTCOME_DETAIL_FIELDS}
        for removed in details:
            with self.subTest(missing=removed):
                self.write_outcome(command, ticket=MT5_TICKET,
                                   **{key: value for key, value in details.items() if key != removed})
                with self.assertRaises(self.gateway_module.GatewayValidationError):
                    gateway.read_outcome(command["commandId"])
        for field in details:
            with self.subTest(open_field=field):
                self.write_outcome(command, ticket=MT5_TICKET, **{**details, field: 1})
                with self.assertRaises(self.gateway_module.GatewayValidationError):
                    gateway.read_outcome(command["commandId"])
        self.write_outcome(command, ticket=MT5_TICKET, unexpected="broker", **details)
        with self.assertRaises(self.gateway_module.GatewayValidationError):
            gateway.read_outcome(command["commandId"])

    def test_closed_details_reject_malformed_values_and_inconsistent_net(self):
        gateway = self.mt5()
        command = gateway.queue_trade_intent(self.intent())["command"]
        gateway.ingest_ack(self.fill(command))
        details = dict(closePrice=3316.54, grossProfit=16.54, commission=0, swap=0, fee=0)
        for field in details:
            for value in (None, True, "0", float("inf"), float("nan")):
                with self.subTest(field=field, value=value):
                    self.write_outcome(command, ticket=MT5_TICKET, executionState="CLOSED",
                                       closedAt=int(self.clock.current.timestamp()) + 60,
                                       closedPnl=16.54, **{**details, field: value})
                    with self.assertRaises(self.gateway_module.GatewayValidationError):
                        gateway.read_outcome(command["commandId"])
        for overrides in ({"closePrice": 0}, {"closePrice": -1}, {"grossProfit": 16.57}):
            with self.subTest(overrides=overrides):
                self.write_outcome(command, ticket=MT5_TICKET, executionState="CLOSED",
                                   closedAt=int(self.clock.current.timestamp()) + 60,
                                   closedPnl=16.54, **{**details, **overrides})
                with self.assertRaises(self.gateway_module.GatewayValidationError):
                    gateway.read_outcome(command["commandId"])
        self.write_outcome(command, ticket=MT5_TICKET, executionState="CLOSED",
                           closedAt=int(self.clock.current.timestamp()) + 60,
                           closedPnl=16.54, **{**details, "grossProfit": 16.56})
        self.assertEqual(gateway.read_outcome(command["commandId"])["grossProfit"], 16.56)

    def test_closed_ack_recovery_keeps_uint64_ticket_exact(self):
        gateway = self.mt5()
        command = gateway.queue_trade_intent(self.intent())["command"]
        gateway.ingest_ack(self.ack(command, status="EXECUTION_UNKNOWN",
                                    reasonCode="ORDER_SEND_API_UNCERTAIN", mode="demo"))
        wire = self.fill(command, ticket=MT5_MAX_TICKET, reasonCode="RECOVERED_ORDER_FOUND",
                         filledSlippageKnown=False, filledSlippagePoints=None,
                         executionState="CLOSED", verificationStatus="VERIFIED_CLOSED",
                         closedAt=int(self.clock.current.timestamp()) + 60, closedPnl=16.54)
        result = gateway.ingest_ack(wire)
        self.assertTrue(result["outstandingReleased"])
        self.assertEqual(result["ack"]["ticket"], MT5_MAX_TICKET)
        self.assertEqual(result["ack"]["executionState"], "CLOSED")
        self.assertTrue(self.mt5().ingest_ack(wire)["idempotentReplay"])


if __name__ == "__main__":
    unittest.main()
