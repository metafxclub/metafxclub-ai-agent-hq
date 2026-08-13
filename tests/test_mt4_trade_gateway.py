from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GATEWAY_PATH = PROJECT_ROOT / "backend" / "local-runner" / "mt4_trade_gateway.py"
EA_ROOT = PROJECT_ROOT / "integrations" / "mt4-trade-gateway"


def load_gateway_module():
    spec = importlib.util.spec_from_file_location(
        "metafx_mt4_trade_gateway_tests",
        GATEWAY_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load MT4 trade gateway module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_example(name: str) -> dict[str, object]:
    value = json.loads((EA_ROOT / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{name} must contain one JSON object")
    return value


class MutableClock:
    def __init__(self):
        self.current = datetime(2026, 7, 31, 3, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.current

    def advance(self, seconds: int) -> None:
        self.current += timedelta(seconds=seconds)


class MT4TradeGatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway_module = load_gateway_module()
        self.clock = MutableClock()
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.file_common = root / "Terminal" / "Common" / "Files"
        self.state_root = root / "runtime"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def gateway(self, **overrides):
        options = {
            "file_common_root": self.file_common,
            "state_root": self.state_root,
            "clock": self.clock,
        }
        options.update(overrides)
        return self.gateway_module.MT4TradeGateway(**options)

    def intent(self, **overrides) -> dict[str, object]:
        payload: dict[str, object] = {
            "channelId": "mtc-demo-01",
            "snapshotId": "a" * 64,
            "snapshotObservedAt": 1785466800,
            "barTime": 1785466800,
            "referencePrice": 3300.0,
            "missionId": "mission-20260731-0001",
            "councilDecisionId": "council-20260731-0001",
            "ownerAgentId": "manager",
            "action": "BUY",
            "symbol": "XAUUSD",
            "timeframe": "H4",
            "stopLoss": 3275.0,
            "takeProfit": 3350.0,
        }
        payload.update(overrides)
        if "streamKey" not in overrides:
            payload["streamKey"] = self.gateway_module._stream_key(
                str(payload["channelId"]),
                str(payload["symbol"]).upper(),
                str(payload["timeframe"]).upper(),
            )
        return payload

    def next_bar(self, **overrides) -> dict[str, object]:
        payload = self.intent(
            snapshotId="c" * 64,
            snapshotObservedAt=1785481200,
            barTime=1785481200,
        )
        payload.update(overrides)
        return payload

    def command_path(self, channel_id: str = "mtc-demo-01") -> Path:
        return (
            self.file_common
            / "MetafxHQ"
            / channel_id
            / "trade-gateway"
            / "command.json"
        )

    def heartbeat_path(self, channel_id: str = "mtc-demo-01") -> Path:
        return (
            self.file_common
            / "MetafxHQ"
            / channel_id
            / "trade-gateway"
            / "heartbeat.json"
        )

    def keys_path(self, channel_id: str = "mtc-demo-01") -> Path:
        return (
            self.file_common
            / "MetafxHQ"
            / channel_id
            / "trade-gateway"
            / "keys"
        )

    def read_envelope(self, path: Path) -> dict[str, object]:
        value = json.loads(path.read_text(encoding="ascii"))
        self.assertIsInstance(value, dict)
        return value

    def envelope_payload(self, path: Path) -> dict[str, object]:
        envelope = self.read_envelope(path)
        payload = json.loads(bytes.fromhex(str(envelope["payloadHex"])).decode("ascii"))
        self.assertIsInstance(payload, dict)
        return payload

    def ack_path(self, command: dict[str, object]) -> Path:
        return (
            self.file_common
            / "MetafxHQ"
            / str(command["channelId"])
            / "trade-gateway"
            / "acks"
            / f"{command['commandId']}.json"
        )

    def outcome_path(self, command: dict[str, object]) -> Path:
        return (
            self.file_common
            / "MetafxHQ"
            / str(command["channelId"])
            / "trade-gateway"
            / "outcomes"
            / f"{command['commandId']}.json"
        )

    def write_outcome(
        self,
        command: dict[str, object],
        *,
        wire_digits: int = 8,
        **overrides,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "schemaVersion": self.gateway_module.OUTCOME_SCHEMA_VERSION,
            "channelId": command["channelId"],
            "commandId": command["commandId"],
            "executionState": "OPEN",
            "observedAt": int(self.clock.current.timestamp()) + 2,
            "ticket": 123456,
            "symbol": command["symbol"],
            "action": command["action"],
            "openedAt": int(self.clock.current.timestamp()) + 1,
            "closedAt": None,
            "openPrice": command["referencePrice"],
            "stopLoss": command["stopLoss"],
            "takeProfit": command["takeProfit"],
            "lots": 0.01,
            "magicNumber": 4186001,
            "comment": f"HQ:{command['commandId']}",
            "closedPnl": None,
        }
        payload.update(overrides)
        path = self.outcome_path(command)
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(payload, separators=(",", ":"))
        for field in ("openPrice", "stopLoss", "takeProfit"):
            encoded = json.dumps(payload[field], separators=(",", ":"))
            raw = raw.replace(
                f'"{field}":{encoded}',
                f'"{field}":{float(payload[field]):.{wire_digits}f}',
                1,
            )
        path.write_text(raw, encoding="ascii")
        return payload

    def ack(self, command: dict[str, object], **overrides) -> dict[str, object]:
        payload: dict[str, object] = {
            "schemaVersion": self.gateway_module.ACK_SCHEMA_VERSION,
            "profile": "special",
            "commandId": command["commandId"],
            "idempotencyKey": command["idempotencyKey"],
            "channelId": command["channelId"],
            "missionId": command["missionId"],
            "councilDecisionId": command["councilDecisionId"],
            "ownerAgentId": command["ownerAgentId"],
            "snapshotId": command["snapshotId"],
            "snapshotObservedAt": command["snapshotObservedAt"],
            "barTime": command["barTime"],
            "referencePrice": command["referencePrice"],
            "eaClosedBarTime": command["barTime"],
            "status": "SHADOWED",
            "reasonCode": "VALIDATED_WITHOUT_ORDER_SEND",
            "mode": "shadow",
            "action": command["action"],
            "symbol": command["symbol"],
            "timeframe": command["timeframe"],
            "fixedLot": 0.01,
            "observedAt": int(self.clock.current.timestamp()) + 1,
            "ticket": None,
            "filledPrice": None,
            "filledSlippagePoints": None,
            "actualStopLoss": None,
            "actualTakeProfit": None,
            "actualMagicNumber": None,
            "actualComment": "",
            "signatureVerificationStatus": "VERIFIED",
            "verificationStatus": "NOT_APPLICABLE",
            "executionState": "NONE",
            "closedAt": None,
            "closedPnl": None,
            "errorCode": 0,
            "statePersisted": True,
        }
        payload.update(overrides)
        if payload["status"] == "EXECUTED":
            defaults = {
                "filledPrice": command["referencePrice"],
                "filledSlippagePoints": 0.0,
                "actualStopLoss": command["stopLoss"],
                "actualTakeProfit": command["takeProfit"],
                "actualMagicNumber": 4186001,
                "actualComment": f"HQ:{command['commandId']}",
                "verificationStatus": "VERIFIED_OPEN",
                "executionState": "OPEN",
            }
            for field, value in defaults.items():
                if field not in overrides:
                    payload[field] = value
        elif payload["status"] == "EXECUTION_UNKNOWN":
            if "verificationStatus" not in overrides:
                payload["verificationStatus"] = "SELECT_FAILED"
            if "executionState" not in overrides:
                payload["executionState"] = "UNKNOWN"
        return payload

    def release(self, gateway, command: dict[str, object]) -> dict[str, object]:
        return gateway.ingest_ack(self.ack(command))

    def test_wire_contract_matches_ea_examples_and_exact_paths(self) -> None:
        command_example = load_example("command.example.json")
        heartbeat_example = load_example("heartbeat.example.json")
        ack_example = load_example("ack.example.json")

        self.assertEqual(
            self.gateway_module.LEDGER_SCHEMA_VERSION,
            "metafx-mt4-trade-ledger-v3",
        )
        self.assertEqual(
            self.gateway_module.COMMAND_SCHEMA_VERSION,
            "metafx-hq-mt4-command-v2",
        )
        self.assertEqual(
            self.gateway_module.ACK_SCHEMA_VERSION,
            "metafx-hq-mt4-ack-v3",
        )

        self.assertEqual(
            list(self.gateway_module.COMMAND_FIELDS),
            list(command_example),
        )
        self.assertEqual(
            list(self.gateway_module.HEARTBEAT_FIELDS),
            list(heartbeat_example),
        )
        self.assertEqual(
            set(self.gateway_module.ACK_ALLOWED_FIELDS),
            set(ack_example),
        )

        gateway = self.gateway(command_ttl_seconds=60, heartbeat_ttl_seconds=60)
        result = gateway.queue_trade_intent(self.intent())
        command = result["command"]
        heartbeat = result["heartbeat"]

        self.assertEqual(result["kind"], "mt4_trade_command_published")
        self.assertFalse(result["idempotentReplay"])
        self.assertEqual(list(command), list(command_example))
        self.assertEqual(list(heartbeat), list(heartbeat_example))
        self.assertEqual(
            command["schemaVersion"],
            command_example["schemaVersion"],
        )
        self.assertEqual(
            heartbeat["schemaVersion"],
            heartbeat_example["schemaVersion"],
        )
        self.assertEqual(command["heartbeatId"], heartbeat["heartbeatId"])
        self.assertIsInstance(command["issuedAt"], int)
        self.assertIsInstance(command["expiresAt"], int)
        self.assertEqual(command["expiresAt"] - command["issuedAt"], 60)
        self.assertEqual(heartbeat["expiresAt"], command["expiresAt"])
        command_envelope = self.read_envelope(self.command_path())
        heartbeat_envelope = self.read_envelope(self.heartbeat_path())
        self.assertEqual(
            list(command_envelope),
            list(self.gateway_module.SIGNED_ENVELOPE_FIELDS),
        )
        self.assertEqual(
            list(heartbeat_envelope),
            list(self.gateway_module.SIGNED_ENVELOPE_FIELDS),
        )
        self.assertEqual(
            command_envelope["schemaVersion"],
            "metafx-hq-mt4-signed-envelope-v1",
        )
        self.assertEqual(command_envelope["algorithm"], "HMAC-SHA256")
        self.assertEqual(self.envelope_payload(self.command_path()), command)
        self.assertEqual(self.envelope_payload(self.heartbeat_path()), heartbeat)
        self.assertEqual(gateway.read_heartbeat("mtc-demo-01"), heartbeat)
        self.assertFalse(self.command_path().with_name("command.json.tmp").exists())
        self.assertFalse(self.heartbeat_path().with_name("heartbeat.json.tmp").exists())
        self.assertTrue(all(
            value is None or isinstance(value, (str, int, float, bool))
            for value in command.values()
        ))
        for evidence_field in (
            "snapshotId",
            "snapshotObservedAt",
            "barTime",
            "referencePrice",
        ):
            self.assertEqual(command[evidence_field], self.intent()[evidence_field])
        self.assertNotIn("streamKey", command)
        for forbidden in ("fixedLot", "lot", "volume", "risk", "riskPercent", "mode"):
            self.assertNotIn(forbidden, command)
        stored = gateway.read_command(str(command["commandId"]))
        self.assertEqual(stored["wireSchemaVersion"], command["schemaVersion"])
        status = gateway.status()
        self.assertEqual(status["ledgerSchemaVersion"], "metafx-mt4-trade-ledger-v3")
        self.assertEqual(status["commandSchemaVersion"], command["schemaVersion"])
        self.assertEqual(status["ackSchemaVersion"], "metafx-hq-mt4-ack-v3")
        self.assertEqual(
            status["signedEnvelopeSchemaVersion"],
            "metafx-hq-mt4-signed-envelope-v1",
        )
        self.assertEqual(status["signatureAlgorithm"], "HMAC-SHA256")
        self.assertTrue(status["signedCommandVerificationAvailable"])
        self.assertTrue(status["liveExecutionAvailable"])
        self.assertIsNone(status["liveBlockReason"])

    def test_wire_numbers_are_plain_decimal_and_precision_is_bounded(self) -> None:
        gateway = self.gateway()
        result = gateway.queue_trade_intent(self.intent(
            referencePrice=0.00000002,
            stopLoss=0.00000001,
            takeProfit=0.00000003,
        ))
        envelope = self.read_envelope(self.command_path())
        wire = bytes.fromhex(str(envelope["payloadHex"])).decode("ascii")

        self.assertIn('"referencePrice":0.00000002', wire)
        self.assertIn('"stopLoss":0.00000001', wire)
        self.assertIn('"takeProfit":0.00000003', wire)
        self.assertNotRegex(
            wire,
            r":-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?[eE][+-]?[0-9]+(?=[,}])",
        )
        self.assertEqual(
            gateway.read_command(str(result["command"]["commandId"]))["command"],
            result["command"],
        )

        with self.assertRaises(self.gateway_module.GatewayValidationError) as raised:
            gateway.queue_trade_intent(self.intent(
                referencePrice=0.000000002,
                stopLoss=0.000000001,
                takeProfit=0.000000003,
            ))
        self.assertEqual(
            raised.exception.code,
            "invalid_stop_loss_precision",
        )

    def test_executed_ack_must_match_the_command_stops(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]

        for field, value, expected_code in (
            ("actualStopLoss", command["stopLoss"] + 1, "ack_actualStopLoss_mismatch"),
            ("actualTakeProfit", command["takeProfit"] + 1, "ack_actualTakeProfit_mismatch"),
        ):
            with self.subTest(field=field):
                with self.assertRaises(self.gateway_module.AckValidationError) as raised:
                    gateway.ingest_ack(self.ack(
                        command,
                        status="EXECUTED",
                        reasonCode="ORDER_ACCEPTED",
                        mode="demo",
                        ticket=983283721,
                        **{field: value},
                    ))
                self.assertEqual(raised.exception.code, expected_code)
                self.assertTrue(
                    gateway.read_command(str(command["commandId"]))["outstanding"]
                )

    def test_broker_digit_normalized_ack_and_outcome_remain_bound(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent(
            referencePrice=3300.125,
            stopLoss=3275.005,
            takeProfit=3350.005,
        ))["command"]
        ticket = 983283721

        def write_ack_with_prices(stop_loss: str, *, inconsistent: bool = False) -> Path:
            ack = self.ack(
                command,
                status="EXECUTED",
                reasonCode="ORDER_ACCEPTED",
                mode="demo",
                ticket=ticket,
                filledPrice=3300.13,
                actualStopLoss=float(stop_loss),
                actualTakeProfit=3350.01,
            )
            raw = json.dumps(ack, separators=(",", ":"))
            rendered = {
                "filledPrice": "3300.13",
                "actualStopLoss": stop_loss,
                "actualTakeProfit": "3350.010" if inconsistent else "3350.01",
            }
            for field, wire_value in rendered.items():
                encoded = json.dumps(ack[field], separators=(",", ":"))
                before = f'"{field}":{encoded}'
                self.assertIn(before, raw)
                raw = raw.replace(before, f'"{field}":{wire_value}', 1)
            path = self.ack_path(command)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(raw, encoding="ascii")
            return path

        inconsistent_path = write_ack_with_prices("3275.01", inconsistent=True)
        with self.assertRaises(self.gateway_module.AckValidationError) as raised:
            gateway.ingest_ack_file(inconsistent_path)
        self.assertEqual(
            raised.exception.code,
            "invalid_ack_execution_price_precision",
        )

        mismatched_path = write_ack_with_prices("3275.02")
        with self.assertRaises(self.gateway_module.AckValidationError) as raised:
            gateway.ingest_ack_file(mismatched_path)
        self.assertEqual(raised.exception.code, "ack_actualStopLoss_mismatch")

        accepted = gateway.ingest_ack_file(write_ack_with_prices("3275.01"))
        self.assertTrue(accepted["outstandingReleased"])

        outcome = self.write_outcome(
            command,
            wire_digits=2,
            ticket=ticket,
            openPrice=3300.13,
            stopLoss=3275.01,
            takeProfit=3350.01,
        )
        self.assertEqual(
            gateway.read_outcome(str(command["commandId"])),
            outcome,
        )

    def test_duplicate_json_keys_fail_closed_at_durable_boundaries(self) -> None:
        with self.assertRaises(ValueError):
            self.gateway_module._strict_json_object('{"value":NaN}')

        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        ack = self.ack(command)
        raw_ack = json.dumps(ack, separators=(",", ":"))
        raw_ack = raw_ack.replace(
            '"status":"SHADOWED"',
            '"status":"EXECUTED","status":"SHADOWED"',
            1,
        )
        ack_path = self.ack_path(command)
        ack_path.parent.mkdir(parents=True, exist_ok=True)
        ack_path.write_text(raw_ack, encoding="ascii")

        with self.assertRaises(self.gateway_module.AckValidationError) as raised:
            gateway.ingest_ack_file(ack_path)
        self.assertEqual(raised.exception.code, "invalid_ack_json")

        ledger_path = self.state_root / "mt4-trade-gateway-ledger.json"
        raw_ledger = ledger_path.read_text(encoding="ascii")
        raw_ledger = raw_ledger.replace(
            '"revision":',
            '"revision":0,"revision":',
            1,
        )
        ledger_path.write_text(raw_ledger, encoding="ascii")
        with self.assertRaises(self.gateway_module.LedgerIntegrityError):
            gateway.status()

    def test_hmac_rfc4231_and_exact_signed_envelope_vector(self) -> None:
        self.assertEqual(
            self.gateway_module._hmac_sha256_hex(
                bytes.fromhex("0b" * 20),
                b"Hi There",
            ),
            "b0344c61d8db38535ca8afceaf0bf12b"
            "881dc200c9833da726e9376c2e32cff7",
        )

        envelope = self.gateway_module._build_signed_envelope(
            kind="command",
            channel_id="mtc-demo-01",
            payload=b'{"schemaVersion":"metafx-hq-mt4-command-v2"}',
            key=bytes(range(32)),
        )
        self.assertEqual(
            envelope,
            {
                "schemaVersion": "metafx-hq-mt4-signed-envelope-v1",
                "algorithm": "HMAC-SHA256",
                "keyId": (
                    "hk-630dcd2966c4336691125448bbb25b4f"
                    "f412a49c732db2c8abc1b8581bd710dd"
                ),
                "payloadHex": (
                    "7b22736368656d6156657273696f6e223a226d65746166782d68712d6d7434"
                    "2d636f6d6d616e642d7632227d"
                ),
                "signatureHex": (
                    "cb256044ef860dd92296c6018b97cead"
                    "345a0df428268da402624bb9e6eeb478"
                ),
            },
        )

    def test_signing_key_is_stable_private_and_never_returned(self) -> None:
        gateway = self.gateway()
        created = gateway.ensure_signing_key("mtc-demo-01")
        reused = gateway.ensure_signing_key("mtc-demo-01")

        self.assertEqual(
            set(created),
            {
                "ok",
                "channelId",
                "keyId",
                "algorithm",
                "envelopeSchemaVersion",
                "created",
            },
        )
        self.assertTrue(created["created"])
        self.assertFalse(reused["created"])
        self.assertEqual(created["keyId"], reused["keyId"])
        self.assertNotIn("key", {name.lower() for name in created if name != "keyId"})
        self.assertNotIn("path", {name.lower() for name in created})

        active_id = (self.keys_path() / "active-key.id").read_text("ascii")
        key_path = self.keys_path() / f"{active_id}.key"
        key = key_path.read_bytes()
        self.assertEqual(len(key), 32)
        self.assertEqual(active_id, self.gateway_module._signing_key_id(key))

        result = gateway.queue_trade_intent(self.intent())
        public_material = "\n".join((
            json.dumps(created, sort_keys=True),
            json.dumps(reused, sort_keys=True),
            json.dumps(result, sort_keys=True),
            json.dumps(gateway.status(), sort_keys=True),
            self.command_path().read_text("ascii"),
            self.heartbeat_path().read_text("ascii"),
            (self.state_root / "mt4-trade-gateway-ledger.json").read_text("ascii"),
        ))
        self.assertNotIn(key.hex(), public_material)

    def test_signed_command_and_heartbeat_tampering_fails_closed(self) -> None:
        gateway = self.gateway()
        gateway.queue_trade_intent(self.intent())

        command_envelope = self.read_envelope(self.command_path())
        command_envelope["payloadHex"] = (
            str(command_envelope["payloadHex"][:-1])
            + ("0" if str(command_envelope["payloadHex"])[-1] != "0" else "1")
        )
        self.command_path().write_text(
            json.dumps(command_envelope),
            encoding="ascii",
        )
        with self.assertRaises(self.gateway_module.OutstandingCommandError) as raised:
            gateway._read_command_slot("mtc-demo-01")
        self.assertEqual(raised.exception.code, "signed_envelope_signature_invalid")

        heartbeat_envelope = self.read_envelope(self.heartbeat_path())
        heartbeat_envelope["signatureHex"] = "0" * 64
        self.heartbeat_path().write_text(
            json.dumps(heartbeat_envelope),
            encoding="ascii",
        )
        with self.assertRaises(self.gateway_module.GatewayValidationError) as raised:
            gateway.read_heartbeat("mtc-demo-01")
        self.assertEqual(raised.exception.code, "signed_envelope_signature_invalid")

    def test_wrong_or_missing_key_never_falls_back_to_unsigned(self) -> None:
        wrong_root = self.file_common / "wrong-key"
        wrong_state = self.state_root / "wrong-key"
        wrong_gateway = self.gateway(
            file_common_root=wrong_root,
            state_root=wrong_state,
        )
        wrong_gateway.queue_trade_intent(self.intent())
        wrong_keys = (
            wrong_root
            / "MetafxHQ"
            / "mtc-demo-01"
            / "trade-gateway"
            / "keys"
        )
        key_id = (wrong_keys / "active-key.id").read_text("ascii")
        (wrong_keys / f"{key_id}.key").write_bytes(b"x" * 32)
        with self.assertRaises(self.gateway_module.OutstandingCommandError) as raised:
            wrong_gateway._read_command_slot("mtc-demo-01")
        self.assertEqual(raised.exception.code, "signing_key_id_mismatch")

        missing_root = self.file_common / "missing-key"
        missing_state = self.state_root / "missing-key"
        missing_gateway = self.gateway(
            file_common_root=missing_root,
            state_root=missing_state,
        )
        missing_gateway.queue_trade_intent(self.intent())
        missing_keys = (
            missing_root
            / "MetafxHQ"
            / "mtc-demo-01"
            / "trade-gateway"
            / "keys"
        )
        missing_id = (missing_keys / "active-key.id").read_text("ascii")
        (missing_keys / f"{missing_id}.key").unlink()
        with self.assertRaises(self.gateway_module.GatewaySafetyError) as raised:
            missing_gateway.refresh_heartbeat()
        self.assertEqual(raised.exception.code, "signing_key_missing")

        orphan_root = self.file_common / "orphan-key"
        orphan_keys = (
            orphan_root
            / "MetafxHQ"
            / "mtc-demo-01"
            / "trade-gateway"
            / "keys"
        )
        orphan_keys.mkdir(parents=True)
        (orphan_keys / "orphan.key").write_bytes(b"z" * 32)
        orphan_gateway = self.gateway(
            file_common_root=orphan_root,
            state_root=self.state_root / "orphan-key",
        )
        with self.assertRaises(self.gateway_module.GatewaySafetyError) as raised:
            orphan_gateway.ensure_signing_key("mtc-demo-01")
        self.assertEqual(raised.exception.code, "signing_key_state_incomplete")

    def test_snapshot_evidence_and_reference_price_are_required_and_validated(self) -> None:
        gateway = self.gateway()
        for field in (
            "snapshotId",
            "snapshotObservedAt",
            "barTime",
            "referencePrice",
        ):
            with self.subTest(missing=field):
                intent = self.intent()
                intent.pop(field)
                with self.assertRaises(self.gateway_module.GatewayValidationError) as raised:
                    gateway.queue_trade_intent(intent)
                self.assertEqual(raised.exception.code, "missing_trade_intent_field")

        invalid = (
            ({"snapshotObservedAt": True}, "invalid_snapshot_observed_at"),
            (
                {
                    "snapshotObservedAt": 1785466800,
                    "barTime": (
                        1785466800
                        + self.gateway_module.MAX_BROKER_CLOCK_LEAD_SECONDS
                        + 1
                    ),
                },
                "invalid_snapshot_bar_order",
            ),
            ({"referencePrice": 0}, "invalid_reference_price"),
            ({"referencePrice": 3275.0}, "invalid_sl_tp_direction"),
            ({"referencePrice": 3350.0}, "invalid_sl_tp_direction"),
        )
        for overrides, expected_code in invalid:
            with self.subTest(overrides=overrides):
                with self.assertRaises(self.gateway_module.GatewayValidationError) as raised:
                    gateway.queue_trade_intent(self.intent(**overrides))
                self.assertEqual(raised.exception.code, expected_code)

    def test_broker_clock_bar_time_lead_is_bounded_and_preserved_for_ea_binding(self) -> None:
        gateway = self.gateway()
        snapshot_observed_at = 1785466800
        # A UTC+3 broker's latest closed M5 bar can appear 2h55m ahead of UTC.
        broker_closed_bar_time = snapshot_observed_at + (2 * 60 * 60) + (55 * 60)

        published = gateway.queue_trade_intent(self.intent(
            snapshotObservedAt=snapshot_observed_at,
            barTime=broker_closed_bar_time,
            timeframe="M5",
        ))

        command = published["command"]
        self.assertEqual(command["snapshotObservedAt"], snapshot_observed_at)
        self.assertEqual(command["barTime"], broker_closed_bar_time)
        self.assertGreater(command["barTime"], command["snapshotObservedAt"])

        with self.assertRaises(self.gateway_module.AckValidationError) as raised:
            gateway.ingest_ack(self.ack(
                command,
                eaClosedBarTime=broker_closed_bar_time - 300,
            ))
        self.assertEqual(
            raised.exception.code,
            "ack_ea_closed_bar_time_mismatch",
        )
        accepted = gateway.ingest_ack(self.ack(command))
        self.assertTrue(accepted["outstandingReleased"])

    def test_schema_salt_and_snapshot_evidence_change_durable_identity(self) -> None:
        self.assertNotEqual(
            self.gateway_module._contract_digest("schema-a", {"value": 1}),
            self.gateway_module._contract_digest("schema-b", {"value": 1}),
        )
        first = self.gateway(
            file_common_root=self.file_common / "first",
            state_root=self.state_root / "first",
        ).queue_trade_intent(self.intent())["command"]
        second = self.gateway(
            file_common_root=self.file_common / "second",
            state_root=self.state_root / "second",
        ).queue_trade_intent(self.intent(
            snapshotObservedAt=1785466801,
            referencePrice=3301.0,
        ))["command"]
        self.assertNotEqual(first["commandId"], second["commandId"])
        self.assertNotEqual(first["idempotencyKey"], second["idempotencyKey"])

    def test_only_an_empty_v2_ledger_migrates_to_v3(self) -> None:
        ledger_path = self.state_root / "mt4-trade-gateway-ledger.json"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        old_empty = {
            "schemaVersion": "metafx-mt4-trade-ledger-v2",
            "revision": 7,
            "activeCommandId": None,
            "commands": {},
            "idempotency": {},
            "barClaims": {},
            "updatedAt": "2026-07-31T02:59:59.000Z",
        }
        ledger_path.write_text(json.dumps(old_empty), encoding="ascii")

        status = self.gateway().status()
        migrated = json.loads(ledger_path.read_text(encoding="ascii"))
        backup = json.loads(
            (self.state_root / "mt4-trade-gateway-ledger.json.bak").read_text(
                encoding="ascii"
            )
        )
        self.assertEqual(migrated["schemaVersion"], "metafx-mt4-trade-ledger-v3")
        self.assertEqual(migrated["revision"], 8)
        self.assertEqual(status["commandCount"], 0)
        self.assertEqual(backup, old_empty)

        old_nonempty = dict(old_empty)
        old_nonempty["commands"] = {"cmd-legacy": {}}
        ledger_path.write_text(json.dumps(old_nonempty), encoding="ascii")
        with self.assertRaises(self.gateway_module.LedgerIntegrityError):
            self.gateway().status()
        self.assertEqual(
            json.loads(ledger_path.read_text(encoding="ascii")),
            old_nonempty,
        )

    def test_backend_has_no_fixed_lot_or_risk_configuration_surface(self) -> None:
        with self.assertRaises(TypeError):
            self.gateway(fixed_lot=0.01)
        with self.assertRaises(TypeError):
            self.gateway(risk_percent=1)
        with self.assertRaises(TypeError):
            self.gateway(mode="shadow")

        gateway = self.gateway()
        policy_fields = (
            ("fixedLot", 0.01),
            ("lot", 0.01),
            ("lots", 0.01),
            ("volume", 0.01),
            ("risk", 1),
            ("riskPercent", 1),
            ("riskAmount", 10),
            ("mode", "live"),
            ("liveArmed", True),
            ("spread", 20),
            ("slippage", 3),
            ("magicNumber", 1234),
        )
        for field, value in policy_fields:
            with self.subTest(field=field):
                with self.assertRaises(self.gateway_module.GatewayValidationError):
                    gateway.queue_trade_intent(self.intent(**{field: value}))

        result = gateway.queue_trade_intent(self.intent())
        ledger_text = (
            self.state_root / "mt4-trade-gateway-ledger.json"
        ).read_text(encoding="ascii")
        command_text = self.command_path().read_text(encoding="ascii")
        self.assertNotIn('"fixedLot"', ledger_text)
        self.assertNotIn('"fixedLot"', command_text)
        self.assertNotIn('"risk"', ledger_text)
        self.assertNotIn('"riskPercent"', ledger_text)
        self.assertNotIn("fixedLot", result["command"])

    def test_m1_is_rejected_and_m5_is_supported(self) -> None:
        gateway = self.gateway()
        with self.assertRaises(self.gateway_module.GatewayValidationError) as raised:
            gateway.queue_trade_intent(self.intent(timeframe="M1"))
        self.assertEqual(raised.exception.code, "invalid_timeframe")

        result = gateway.queue_trade_intent(self.intent(timeframe="M5"))
        self.assertEqual(result["command"]["timeframe"], "M5")
        self.assertNotIn("M1", self.gateway_module.ALLOWED_TIMEFRAMES)

    def test_list_commands_is_newest_first_bounded_and_validates_limit(self) -> None:
        gateway = self.gateway()
        first = gateway.queue_trade_intent(self.intent())["command"]
        self.clock.advance(2)
        self.release(gateway, first)
        self.clock.advance(2)
        second = gateway.queue_trade_intent(
            self.next_bar(
                missionId="mission-20260731-0002",
                councilDecisionId="council-20260731-0002",
            )
        )["command"]

        records = gateway.list_commands(limit=2)
        self.assertEqual(
            [item["command"]["commandId"] for item in records],
            [second["commandId"], first["commandId"]],
        )
        self.assertEqual(
            gateway.list_commands(limit=1)[0]["command"]["commandId"],
            second["commandId"],
        )
        self.assertEqual(records[1]["status"], "ack_SHADOWED")
        self.assertIsNotNone(records[1]["ack"])

        for invalid_limit in (True, False, 0, 501, 1.5, "2", None):
            with self.subTest(limit=invalid_limit):
                with self.assertRaises(
                    self.gateway_module.GatewayValidationError
                ) as raised:
                    gateway.list_commands(limit=invalid_limit)
                self.assertEqual(
                    raised.exception.code,
                    "invalid_command_history_limit",
                )

    def test_exact_replay_survives_restart_and_repairs_missing_slot(self) -> None:
        first_gateway = self.gateway()
        first = first_gateway.queue_trade_intent(self.intent())
        first_command = first["command"]
        self.command_path().unlink()
        self.clock.advance(2)

        restarted = self.gateway()
        replay = restarted.queue_trade_intent(self.intent())
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["command"], first_command)
        self.assertTrue(self.command_path().is_file())
        self.assertEqual(
            self.envelope_payload(self.command_path()),
            first_command,
        )
        self.assertEqual(
            restarted.status()["activeCommandId"],
            first_command["commandId"],
        )

    def test_durable_command_history_can_be_paged_without_silent_truncation(self) -> None:
        gateway = self.gateway()
        commands = []
        for index, timeframe in enumerate(("M5", "M15", "M30"), start=1):
            command = gateway.queue_trade_intent(self.intent(
                snapshotId=f"{index}" * 64,
                snapshotObservedAt=1785466800 + index,
                barTime=1785466800,
                missionId=f"mission-page-{index}",
                timeframe=timeframe,
            ))["command"]
            commands.append(command)
            self.release(gateway, command)
            self.clock.advance(1)

        first = gateway.list_commands_page(limit=2)
        self.assertEqual(first["total"], 3)
        self.assertTrue(first["hasMore"])
        self.assertTrue(first["cursorFound"])
        self.assertEqual(len(first["records"]), 2)
        self.assertEqual(
            first["nextCursor"],
            first["records"][-1]["command"]["commandId"],
        )

        second = gateway.list_commands_page(
            limit=2,
            cursor=str(first["nextCursor"]),
        )
        self.assertEqual(second["total"], 3)
        self.assertFalse(second["hasMore"])
        self.assertTrue(second["cursorFound"])
        self.assertEqual(len(second["records"]), 1)
        seen = {
            record["command"]["commandId"]
            for record in (*first["records"], *second["records"])
        }
        self.assertEqual(seen, {command["commandId"] for command in commands})

        missing = gateway.list_commands_page(limit=2, cursor="cmd-" + "f" * 24)
        self.assertFalse(missing["cursorFound"])
        self.assertEqual(missing["records"], [])
        self.assertFalse(missing["hasMore"])

        selected = gateway.list_commands_page(
            limit=1,
            channel_id="mtc-demo-01",
        )
        self.assertEqual(selected["channelId"], "mtc-demo-01")
        self.assertEqual(selected["total"], 3)
        self.assertTrue(selected["hasMore"])
        self.assertTrue(all(
            record["command"]["channelId"] == "mtc-demo-01"
            for record in selected["records"]
        ))

        with self.assertRaises(self.gateway_module.GatewayValidationError) as raised:
            gateway.list_commands_page(channel_id="../../other")
        self.assertEqual(raised.exception.code, "invalid_command_history_channel")

    def test_single_outstanding_survives_ttl_until_persisted_terminal_ack(self) -> None:
        gateway = self.gateway(command_ttl_seconds=10)
        first = gateway.queue_trade_intent(self.intent())["command"]
        with self.assertRaises(self.gateway_module.OutstandingCommandError):
            gateway.queue_trade_intent(self.next_bar())

        self.clock.advance(10)
        expired = gateway.expire_pending()
        self.assertEqual(expired["expiredCount"], 1)
        self.assertFalse(expired["slotReleased"])
        with self.assertRaises(self.gateway_module.OutstandingCommandError):
            gateway.queue_trade_intent(self.next_bar())

        released = self.release(gateway, first)
        self.assertTrue(released["outstandingReleased"])
        second = gateway.queue_trade_intent(self.next_bar())["command"]
        self.assertNotEqual(second["commandId"], first["commandId"])
        self.assertEqual(
            self.envelope_payload(self.command_path())["commandId"],
            second["commandId"],
        )

    def test_one_bar_claim_is_durable_after_terminal_ack(self) -> None:
        gateway = self.gateway()
        first = gateway.queue_trade_intent(self.intent())["command"]
        self.release(gateway, first)

        changed_same_bar = self.intent(
            snapshotId="d" * 64,
            missionId="mission-20260731-0002",
            action="SELL",
            stopLoss=3350.0,
            takeProfit=3275.0,
        )
        with self.assertRaises(self.gateway_module.OneOrderPerBarError):
            gateway.queue_trade_intent(changed_same_bar)

        replay = gateway.queue_trade_intent(self.intent())
        self.assertTrue(replay["idempotentReplay"])
        self.assertFalse(replay["outstanding"])

    def test_bar_claim_is_exactly_once_per_channel_symbol_timeframe_stream(self) -> None:
        gateway = self.gateway()
        bar_time = 1785466800

        first = gateway.queue_trade_intent(self.intent(barTime=bar_time))["command"]
        first_entry = gateway.read_command(str(first["commandId"]))
        self.release(gateway, first)

        switched_timeframe = gateway.queue_trade_intent(self.intent(
            snapshotId="d" * 64,
            missionId="mission-stream-m5",
            timeframe="M5",
            barTime=bar_time,
        ))["command"]
        timeframe_entry = gateway.read_command(str(switched_timeframe["commandId"]))
        self.release(gateway, switched_timeframe)

        suffixed_symbol = gateway.queue_trade_intent(self.intent(
            snapshotId="e" * 64,
            missionId="mission-stream-suffix",
            symbol="XAUUSD.r",
            barTime=bar_time,
        ))["command"]
        suffix_entry = gateway.read_command(str(suffixed_symbol["commandId"]))
        self.release(gateway, suffixed_symbol)

        switched_channel = gateway.queue_trade_intent(self.intent(
            channelId="mtc-demo-02",
            snapshotId="f" * 64,
            missionId="mission-stream-channel",
            barTime=bar_time,
        ))["command"]
        channel_entry = gateway.read_command(str(switched_channel["commandId"]))
        self.release(gateway, switched_channel)

        entries = (
            first_entry,
            timeframe_entry,
            suffix_entry,
            channel_entry,
        )
        self.assertTrue(all(entry is not None for entry in entries))
        bar_keys = {
            entry["backendIdentity"]["barKey"]
            for entry in entries
            if entry is not None
        }
        self.assertEqual(len(bar_keys), 4)

        duplicate_suffix_bar = self.intent(
            snapshotId="1" * 64,
            missionId="mission-stream-suffix-duplicate",
            action="SELL",
            symbol="XAUUSD.r",
            barTime=bar_time,
            stopLoss=3350.0,
            takeProfit=3275.0,
        )
        with self.assertRaises(self.gateway_module.OneOrderPerBarError):
            gateway.queue_trade_intent(duplicate_suffix_bar)

    def test_stream_key_is_bound_to_selected_channel_symbol_and_timeframe(self) -> None:
        gateway = self.gateway()
        with self.assertRaises(self.gateway_module.GatewayValidationError) as raised:
            gateway.queue_trade_intent(self.intent(streamKey="b" * 64))
        self.assertEqual(raised.exception.code, "stream_key_mismatch")

        published = gateway.queue_trade_intent(self.intent(streamKey=""))
        entry = gateway.read_command(str(published["command"]["commandId"]))
        self.assertIsNotNone(entry)
        self.assertEqual(
            entry["backendIdentity"]["streamKey"],
            self.gateway_module._stream_key("mtc-demo-01", "XAUUSD", "H4"),
        )

    def test_hash_broker_suffix_is_supported_but_plus_remains_rejected(self) -> None:
        gateway = self.gateway()
        published = gateway.queue_trade_intent(self.intent(
            symbol="eurusd#",
            missionId="mission-hash-suffix",
        ))
        command = published["command"]
        self.assertEqual(command["symbol"], "EURUSD#")
        entry = gateway.read_command(str(command["commandId"]))
        self.assertIsNotNone(entry)
        self.assertEqual(
            entry["backendIdentity"]["streamKey"],
            self.gateway_module._stream_key("mtc-demo-01", "EURUSD#", "H4"),
        )

        with self.assertRaises(self.gateway_module.GatewayValidationError) as raised:
            gateway.queue_trade_intent(self.intent(
                channelId="mtc-plus-test",
                symbol="EURUSD+",
            ))
        self.assertEqual(raised.exception.code, "invalid_symbol")

    def test_existing_v3_ledger_with_mismatched_stream_identity_fails_closed(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        self.release(gateway, command)
        ledger_path = self.state_root / "mt4-trade-gateway-ledger.json"
        ledger = json.loads(ledger_path.read_text(encoding="ascii"))
        ledger["commands"][command["commandId"]]["backendIdentity"][
            "streamKey"
        ] = "b" * 64
        ledger_path.write_text(json.dumps(ledger), encoding="ascii")

        restarted = self.gateway()
        with self.assertRaises(self.gateway_module.LedgerIntegrityError):
            restarted.status()

    def test_unowned_or_tampered_command_slot_fails_closed(self) -> None:
        gateway = self.gateway()
        self.command_path().parent.mkdir(parents=True, exist_ok=True)
        self.command_path().write_text(
            json.dumps(load_example("command.example.json")),
            encoding="ascii",
        )
        with self.assertRaises(self.gateway_module.OutstandingCommandError):
            gateway.queue_trade_intent(self.intent())

        self.assertFalse(
            (self.state_root / "mt4-trade-gateway-ledger.json").exists()
        )

    def test_legacy_plain_slot_is_only_replaceable_after_terminal_resolution(self) -> None:
        outstanding_root = self.file_common / "legacy-outstanding"
        outstanding_gateway = self.gateway(
            file_common_root=outstanding_root,
            state_root=self.state_root / "legacy-outstanding",
        )
        outstanding = outstanding_gateway.queue_trade_intent(self.intent())["command"]
        outstanding_path = (
            outstanding_root
            / "MetafxHQ"
            / "mtc-demo-01"
            / "trade-gateway"
            / "command.json"
        )
        outstanding_path.write_text(json.dumps(outstanding), encoding="ascii")
        with self.assertRaises(self.gateway_module.OutstandingCommandError) as raised:
            outstanding_gateway.queue_trade_intent(self.intent())
        self.assertEqual(raised.exception.code, "signed_envelope_required")
        self.assertEqual(json.loads(outstanding_path.read_text("ascii")), outstanding)

        resolved_root = self.file_common / "legacy-resolved"
        resolved_gateway = self.gateway(
            file_common_root=resolved_root,
            state_root=self.state_root / "legacy-resolved",
        )
        resolved = resolved_gateway.queue_trade_intent(self.intent())["command"]
        resolved_gateway.ingest_ack(self.ack(resolved))
        resolved_path = (
            resolved_root
            / "MetafxHQ"
            / "mtc-demo-01"
            / "trade-gateway"
            / "command.json"
        )
        resolved_path.write_text(json.dumps(resolved), encoding="ascii")
        replacement = resolved_gateway.queue_trade_intent(self.next_bar())["command"]
        replacement_envelope = json.loads(resolved_path.read_text("ascii"))
        self.assertEqual(
            replacement_envelope["schemaVersion"],
            "metafx-hq-mt4-signed-envelope-v1",
        )
        replacement_inner = json.loads(
            bytes.fromhex(replacement_envelope["payloadHex"]).decode("ascii")
        )
        self.assertEqual(replacement_inner, replacement)

    def test_ack_is_bound_and_fixed_lot_is_sanitized_to_status_only(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]

        invalid_acks = (
            self.ack(command, commandId="cmd-" + "f" * 24),
            self.ack(command, idempotencyKey="idem-" + "f" * 32),
            self.ack(command, channelId="mtc-other-01"),
        )
        for ack in invalid_acks:
            with self.subTest(field=next(
                key
                for key in ("commandId", "idempotencyKey", "channelId")
                if ack[key] != command[key]
            )):
                with self.assertRaises(self.gateway_module.AckValidationError):
                    gateway.ingest_ack(ack)

        with self.assertRaises(self.gateway_module.AckValidationError) as signature_error:
            gateway.ingest_ack(
                self.ack(command, signatureVerificationStatus="NOT_VERIFIED")
            )
        self.assertEqual(
            signature_error.exception.code,
            "invalid_ack_signature_verification_status",
        )

        result = gateway.ingest_ack(self.ack(command, fixedLot=123.45))
        self.assertTrue(result["outstandingReleased"])
        self.assertEqual(result["eaSizingStatus"], "reported_read_only")
        self.assertNotIn("fixedLot", result["ack"])
        stored = gateway.read_command(str(command["commandId"]))
        self.assertEqual(stored["eaSizingStatus"], "reported_read_only")
        self.assertNotIn("fixedLot", stored["ack"])
        ledger_text = (
            self.state_root / "mt4-trade-gateway-ledger.json"
        ).read_text(encoding="ascii")
        self.assertNotIn('"fixedLot"', ledger_text)
        self.assertNotIn("123.45", ledger_text)

    def test_ack_must_echo_snapshot_and_match_the_ea_closed_bar(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        invalid = (
            ({"snapshotId": "f" * 64}, "ack_snapshotId_mismatch"),
            (
                {"snapshotObservedAt": command["snapshotObservedAt"] + 1},
                "ack_snapshotObservedAt_mismatch",
            ),
            ({"barTime": command["barTime"] - 300}, "ack_barTime_mismatch"),
            (
                {"referencePrice": command["referencePrice"] + 0.1},
                "ack_referencePrice_mismatch",
            ),
            (
                {"eaClosedBarTime": command["barTime"] - 300},
                "ack_ea_closed_bar_time_mismatch",
            ),
        )
        for overrides, expected_code in invalid:
            with self.subTest(overrides=overrides):
                with self.assertRaises(self.gateway_module.AckValidationError) as raised:
                    gateway.ingest_ack(self.ack(command, **overrides))
                self.assertEqual(raised.exception.code, expected_code)

        accepted = gateway.ingest_ack(self.ack(command))
        self.assertTrue(accepted["outstandingReleased"])
        for field in (
            "snapshotId",
            "snapshotObservedAt",
            "barTime",
            "referencePrice",
            "eaClosedBarTime",
        ):
            self.assertEqual(accepted["ack"][field], self.ack(command)[field])

    def test_legacy_rejected_ack_file_can_round_midpoint_but_executed_ack_cannot(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(
            self.intent(
                referencePrice=4347.895,
                stopLoss=4340.0,
                takeProfit=4360.0,
            )
        )["command"]
        rejected = self.ack(
            command,
            referencePrice=4347.9,
            status="REJECTED",
            reasonCode="SIGNAL_PRICE_DRIFT_EXCEEDED",
            mode="demo",
        )
        rejected_path = self.ack_path(command)
        rejected_path.parent.mkdir(parents=True, exist_ok=True)
        rejected_wire = json.dumps(rejected, separators=(",", ":"))
        rejected_wire = rejected_wire.replace(
            '"referencePrice":4347.9',
            '"referencePrice":4347.90',
        )
        rejected_path.write_text(rejected_wire, encoding="ascii")

        accepted = gateway.ingest_ack_file(rejected_path)
        self.assertTrue(accepted["outstandingReleased"])
        self.assertEqual(
            accepted["referencePriceBinding"],
            "legacy_rejected_wire_rounding",
        )

        next_command = gateway.queue_trade_intent(
            self.next_bar(
                referencePrice=4347.895,
                stopLoss=4340.0,
                takeProfit=4360.0,
            )
        )["command"]
        executed = self.ack(
            next_command,
            referencePrice=4347.9,
            status="EXECUTED",
            reasonCode="ORDER_SEND_VERIFIED",
            mode="demo",
            ticket=123456,
        )
        executed_path = self.ack_path(next_command)
        executed_wire = json.dumps(executed, separators=(",", ":"))
        executed_wire = executed_wire.replace(
            '"referencePrice":4347.9',
            '"referencePrice":4347.90',
        )
        executed_path.write_text(executed_wire, encoding="ascii")
        with self.assertRaises(self.gateway_module.AckValidationError) as raised:
            gateway.ingest_ack_file(executed_path)
        self.assertEqual(raised.exception.code, "ack_referencePrice_mismatch")

    def test_executing_and_unpersisted_terminal_ack_do_not_release_slot(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        executing = gateway.ingest_ack(self.ack(
            command,
            status="EXECUTING",
            reasonCode="ORDER_SEND_STARTED",
            statePersisted=True,
        ))
        self.assertFalse(executing["outstandingReleased"])
        with self.assertRaises(self.gateway_module.OutstandingCommandError):
            gateway.queue_trade_intent(self.next_bar())

        terminal_unpersisted = gateway.ingest_ack(self.ack(
            command,
            status="EXECUTED",
            reasonCode="ORDER_SEND_SUCCEEDED",
            mode="demo",
            ticket=123456,
            statePersisted=False,
        ))
        self.assertFalse(terminal_unpersisted["outstandingReleased"])
        with self.assertRaises(self.gateway_module.OutstandingCommandError):
            gateway.queue_trade_intent(self.next_bar())

        self.clock.advance(1)
        terminal_persisted = gateway.ingest_ack(self.ack(
            command,
            status="EXECUTED",
            reasonCode="ORDER_SEND_SUCCEEDED",
            mode="demo",
            ticket=123456,
            statePersisted=True,
            observedAt=int(self.clock.current.timestamp()),
        ))
        self.assertTrue(terminal_persisted["outstandingReleased"])
        self.assertIsNone(gateway.status()["activeCommandId"])

    def test_execution_unknown_after_executing_is_persisted_but_never_releases_slot(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        executing = gateway.ingest_ack(self.ack(
            command,
            status="EXECUTING",
            reasonCode="ORDER_SEND_STARTED",
            statePersisted=True,
        ))
        self.assertFalse(executing["outstandingReleased"])

        self.clock.advance(1)
        unknown_ack = self.ack(
            command,
            status="EXECUTION_UNKNOWN",
            reasonCode="ORDER_SEND_RESULT_UNKNOWN",
            mode="demo",
            statePersisted=True,
            observedAt=int(self.clock.current.timestamp()),
        )
        unknown = gateway.ingest_ack(unknown_ack)
        self.assertEqual(unknown["status"], "ack_EXECUTION_UNKNOWN")
        self.assertFalse(unknown["outstandingReleased"])
        self.assertEqual(
            gateway.status()["activeCommandId"],
            command["commandId"],
        )
        with self.assertRaises(self.gateway_module.OutstandingCommandError):
            gateway.queue_trade_intent(self.next_bar())

        replay = gateway.ingest_ack(unknown_ack)
        self.assertTrue(replay["idempotentReplay"])
        self.assertFalse(replay["outstandingReleased"])

        self.clock.advance(1)
        with self.assertRaises(self.gateway_module.AckConflictError):
            gateway.ingest_ack(self.ack(
                command,
                status="EXECUTED",
                reasonCode="ORDER_SEND_SUCCEEDED",
                mode="demo",
                ticket=123456,
                statePersisted=True,
                observedAt=int(self.clock.current.timestamp()),
            ))

    def test_expiry_preserves_unknown_and_repairs_legacy_overwrite(self) -> None:
        gateway = self.gateway(command_ttl_seconds=1)
        command = gateway.queue_trade_intent(self.intent())["command"]
        unknown_ack = self.ack(
            command,
            status="EXECUTION_UNKNOWN",
            reasonCode="ORDER_POST_SEND_VERIFICATION_MISMATCH",
            mode="demo",
            ticket=123456,
            filledPrice=3300.25,
            filledSlippagePoints=22.0,
            actualStopLoss=command["stopLoss"],
            actualTakeProfit=command["takeProfit"],
            actualMagicNumber=4186001,
            actualComment=f"HQ:{command['commandId']}",
            verificationStatus="MISMATCH",
            executionState="OPEN",
        )
        gateway.ingest_ack(unknown_ack)
        self.clock.advance(2)

        expired = gateway.expire_pending()
        self.assertEqual(expired["expiredCount"], 0)
        self.assertEqual(
            gateway.read_command(str(command["commandId"]))["status"],
            "ack_EXECUTION_UNKNOWN",
        )
        self.assertEqual(gateway.status()["activeCommandId"], command["commandId"])

        ledger_path = self.state_root / "mt4-trade-gateway-ledger.json"
        legacy = json.loads(ledger_path.read_text(encoding="ascii"))
        legacy["commands"][command["commandId"]]["status"] = "expired_waiting_ack"
        ledger_path.write_text(json.dumps(legacy), encoding="ascii")

        repaired = gateway.read_command(str(command["commandId"]))
        self.assertEqual(repaired["status"], "ack_EXECUTION_UNKNOWN")
        self.assertTrue(repaired["outstanding"])
        migrated = json.loads(ledger_path.read_text(encoding="ascii"))
        self.assertEqual(
            migrated["commands"][command["commandId"]]["statusMigration"]["reasonCode"],
            "RESTORE_DURABLE_EXECUTION_UNKNOWN",
        )

    def test_exact_unknown_outcome_reconciliation_releases_once_with_warning(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        unknown_ack = self.ack(
            command,
            status="EXECUTION_UNKNOWN",
            reasonCode="ORDER_POST_SEND_VERIFICATION_MISMATCH",
            mode="demo",
            ticket=983283721,
            filledPrice=3300.25,
            filledSlippagePoints=22.0,
            actualStopLoss=command["stopLoss"],
            actualTakeProfit=command["takeProfit"],
            actualMagicNumber=4186001,
            actualComment=f"HQ:{command['commandId']}",
            verificationStatus="MISMATCH",
            executionState="OPEN",
        )
        gateway.ingest_ack(unknown_ack)
        self.write_outcome(
            command,
            ticket=983283721,
            openPrice=3300.25,
        )

        reconciled = gateway.reconcile_execution_unknown(
            str(command["commandId"])
        )
        self.assertTrue(reconciled["outstandingReleased"])
        self.assertTrue(reconciled["barClaimRetained"])
        self.assertEqual(reconciled["executionQuality"], "warning")
        self.assertEqual(reconciled["status"], "ack_EXECUTED")
        self.assertEqual(
            reconciled["ack"]["reasonCode"],
            "EXECUTION_RECONCILED_WITH_WARNING",
        )
        self.assertEqual(
            reconciled["ack"]["observedAt"],
            unknown_ack["observedAt"],
        )
        persisted = json.loads(
            (self.state_root / "mt4-trade-gateway-ledger.json").read_text(
                encoding="ascii"
            )
        )["commands"][command["commandId"]]
        self.assertEqual(
            persisted["recovery"]["originalAckObservedAt"],
            unknown_ack["observedAt"],
        )
        self.assertIsNone(gateway.status()["activeCommandId"])

        replay = gateway.reconcile_execution_unknown(str(command["commandId"]))
        self.assertTrue(replay["idempotentReplay"])
        self.assertTrue(replay["outstandingReleased"])

        with self.assertRaises(self.gateway_module.OneOrderPerBarError):
            gateway.queue_trade_intent(self.intent(
                snapshotId="d" * 64,
                missionId="mission-20260731-retry",
            ))

    def test_unknown_reconciliation_rejects_mismatched_ticket_without_release(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        unknown_ack = self.ack(
            command,
            status="EXECUTION_UNKNOWN",
            reasonCode="ORDER_POST_SEND_VERIFICATION_MISMATCH",
            mode="demo",
            ticket=123456,
            filledPrice=3300.25,
            filledSlippagePoints=22.0,
            actualStopLoss=command["stopLoss"],
            actualTakeProfit=command["takeProfit"],
            actualMagicNumber=4186001,
            actualComment=f"HQ:{command['commandId']}",
            verificationStatus="MISMATCH",
            executionState="OPEN",
        )
        gateway.ingest_ack(unknown_ack)
        self.write_outcome(
            command,
            ticket=654321,
            openPrice=3300.25,
        )

        with self.assertRaises(self.gateway_module.GatewayValidationError):
            gateway.reconcile_execution_unknown(str(command["commandId"]))
        current = gateway.read_command(str(command["commandId"]))
        self.assertEqual(current["status"], "ack_EXECUTION_UNKNOWN")
        self.assertTrue(current["outstanding"])

    def test_pending_scan_auto_reconciles_existing_unknown_from_exact_outcome(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        unknown_ack = self.ack(
            command,
            status="EXECUTION_UNKNOWN",
            reasonCode="ORDER_POST_SEND_VERIFICATION_MISMATCH",
            mode="demo",
            ticket=983283721,
            filledPrice=3300.25,
            filledSlippagePoints=22.0,
            actualStopLoss=command["stopLoss"],
            actualTakeProfit=command["takeProfit"],
            actualMagicNumber=4186001,
            actualComment=f"HQ:{command['commandId']}",
            verificationStatus="MISMATCH",
            executionState="OPEN",
        )
        gateway.ingest_ack(unknown_ack)
        ack_path = self.ack_path(command)
        ack_path.parent.mkdir(parents=True, exist_ok=True)
        ack_path.write_text(json.dumps(unknown_ack), encoding="ascii")
        self.write_outcome(
            command,
            ticket=983283721,
            openPrice=3300.25,
        )

        events = gateway.ingest_pending_acks()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["kind"], "mt4_execution_unknown_reconciled")
        self.assertTrue(events[0]["outstandingReleased"])
        self.assertIsNone(gateway.status()["activeCommandId"])

    def test_unknown_can_upgrade_to_exact_closed_terminal_ack_with_tp_suffix(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        unknown_ack = self.ack(
            command,
            status="EXECUTION_UNKNOWN",
            reasonCode="ORDER_POST_SEND_VERIFICATION_MISMATCH",
            mode="demo",
            ticket=123456,
            filledPrice=3300.25,
            filledSlippagePoints=22.0,
            actualStopLoss=command["stopLoss"],
            actualTakeProfit=command["takeProfit"],
            actualMagicNumber=4186001,
            actualComment=f"HQ:{command['commandId']}",
            verificationStatus="MISMATCH",
            executionState="OPEN",
        )
        gateway.ingest_ack(unknown_ack)
        truncated = f"HQ:{command['commandId']}"[:-8] + "[tp]"
        upgraded = gateway.ingest_ack(self.ack(
            command,
            status="EXECUTED",
            reasonCode="RECOVERED_ORDER_FOUND",
            mode="demo",
            ticket=123456,
            filledPrice=3300.25,
            filledSlippagePoints=0.0,
            actualStopLoss=command["stopLoss"],
            actualTakeProfit=command["takeProfit"],
            actualMagicNumber=4186001,
            actualComment=truncated,
            verificationStatus="VERIFIED_CLOSED",
            executionState="CLOSED",
            closedAt=int(self.clock.current.timestamp()) + 60,
            closedPnl=7.58,
        ))
        self.assertTrue(upgraded["outstandingReleased"])
        self.assertEqual(upgraded["status"], "ack_EXECUTED")
        self.assertEqual(
            upgraded["ack"]["reasonCode"],
            "EXECUTION_RECONCILED_WITH_WARNING",
        )
        self.assertEqual(
            upgraded["ack"]["observedAt"],
            unknown_ack["observedAt"],
        )
        self.assertEqual(upgraded["ack"]["filledSlippagePoints"], 22.0)
        self.assertEqual(
            upgraded["ack"]["actualComment"],
            f"HQ:{command['commandId']}",
        )
        ledger = json.loads(
            (self.state_root / "mt4-trade-gateway-ledger.json").read_text(
                encoding="ascii"
            )
        )
        self.assertEqual(
            ledger["commands"][command["commandId"]]["recovery"]["action"],
            "reconcile_terminal_ack",
        )

    def test_durable_reconciliation_accepts_exact_later_closed_lifecycle_ack(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        unknown_ack = self.ack(
            command,
            status="EXECUTION_UNKNOWN",
            reasonCode="ORDER_POST_SEND_VERIFICATION_MISMATCH",
            mode="demo",
            ticket=983283721,
            filledPrice=3300.25,
            filledSlippagePoints=22.0,
            actualStopLoss=command["stopLoss"],
            actualTakeProfit=command["takeProfit"],
            actualMagicNumber=4186001,
            actualComment=f"HQ:{command['commandId']}",
            verificationStatus="MISMATCH",
            executionState="OPEN",
        )
        gateway.ingest_ack(unknown_ack)
        self.write_outcome(command, ticket=983283721, openPrice=3300.25)
        gateway.reconcile_execution_unknown(str(command["commandId"]))

        self.clock.advance(120)
        truncated = f"HQ:{command['commandId']}"[:-8] + "[tp]"
        closed = gateway.ingest_ack(self.ack(
            command,
            status="EXECUTED",
            reasonCode="RECOVERED_ORDER_FOUND",
            mode="demo",
            ticket=983283721,
            filledPrice=3300.25,
            filledSlippagePoints=0.0,
            actualStopLoss=command["stopLoss"],
            actualTakeProfit=command["takeProfit"],
            actualMagicNumber=4186001,
            actualComment=truncated,
            verificationStatus="VERIFIED_CLOSED",
            executionState="CLOSED",
            eaClosedBarTime=int(command["barTime"]) + 300,
            closedAt=int(self.clock.current.timestamp()) + 60,
            closedPnl=7.58,
        ))
        self.assertEqual(closed["ack"]["executionState"], "CLOSED")
        self.assertEqual(closed["ack"]["verificationStatus"], "VERIFIED_CLOSED")
        self.assertEqual(closed["ack"]["observedAt"], unknown_ack["observedAt"])
        self.assertEqual(closed["ack"]["filledSlippagePoints"], 22.0)
        self.assertEqual(
            closed["ack"]["actualComment"],
            f"HQ:{command['commandId']}",
        )
        ledger = json.loads(
            (self.state_root / "mt4-trade-gateway-ledger.json").read_text(
                encoding="ascii"
            )
        )["commands"][command["commandId"]]
        self.assertEqual(
            ledger["recovery"]["action"],
            "reconcile_terminal_lifecycle_ack",
        )
        self.assertFalse(ledger["outstanding"])
        self.assertEqual(
            closed["referencePriceBinding"],
            "recovered_order_lifecycle_current_closed_bar",
        )

    def test_pending_scan_reads_exact_inactive_recovery_lifecycle_ack_once(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        gateway.ingest_ack(self.ack(
            command,
            status="EXECUTION_UNKNOWN",
            reasonCode="ORDER_POST_SEND_VERIFICATION_MISMATCH",
            mode="demo",
            ticket=983283721,
            filledPrice=3300.25,
            filledSlippagePoints=22.0,
            actualStopLoss=command["stopLoss"],
            actualTakeProfit=command["takeProfit"],
            actualMagicNumber=4186001,
            actualComment=f"HQ:{command['commandId']}",
            verificationStatus="MISMATCH",
            executionState="OPEN",
        ))
        self.write_outcome(command, ticket=983283721, openPrice=3300.25)
        gateway.reconcile_execution_unknown(str(command["commandId"]))
        self.clock.advance(120)
        recovered_ack = self.ack(
            command,
            status="EXECUTED",
            reasonCode="RECOVERED_ORDER_FOUND",
            mode="demo",
            ticket=983283721,
            filledPrice=3300.25,
            filledSlippagePoints=0.0,
            actualStopLoss=command["stopLoss"],
            actualTakeProfit=command["takeProfit"],
            actualMagicNumber=4186001,
            actualComment=f"HQ:{command['commandId']}"[:-8] + "[tp]",
            verificationStatus="VERIFIED_CLOSED",
            executionState="CLOSED",
            eaClosedBarTime=int(command["barTime"]) + 300,
            closedAt=int(self.clock.current.timestamp()) + 60,
            closedPnl=7.58,
        )
        path = self.ack_path(command)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(recovered_ack), encoding="ascii")

        events = gateway.ingest_pending_acks()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["ack"]["executionState"], "CLOSED")
        self.assertEqual(
            events[0]["referencePriceBinding"],
            "recovered_order_lifecycle_current_closed_bar",
        )
        self.assertEqual(gateway.ingest_pending_acks(), [])

    def test_normal_executed_ack_still_rejects_wrong_closed_bar(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        with self.assertRaises(self.gateway_module.AckValidationError) as raised:
            gateway.ingest_ack(self.ack(
                command,
                status="EXECUTED",
                reasonCode="ORDER_ACCEPTED",
                mode="demo",
                ticket=123456,
                eaClosedBarTime=int(command["barTime"]) + 300,
            ))
        self.assertEqual(
            raised.exception.code,
            "ack_ea_closed_bar_time_mismatch",
        )

    def test_ack_file_path_and_pending_scan_match_ea_contract(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        path = self.ack_path(command)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.ack(command), ensure_ascii=True),
            encoding="ascii",
        )

        results = gateway.ingest_pending_acks()
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["outstandingReleased"])
        self.assertTrue(path.is_file())
        self.assertEqual(gateway.ingest_pending_acks(), [])

        wrong_path = path.parent.parent / path.name
        with self.assertRaises(self.gateway_module.AckValidationError):
            gateway.ingest_ack_file(wrong_path)

    def test_executed_ack_requires_verified_fill_and_outcome_is_readable(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        invalid = self.ack(
            command,
            status="EXECUTED",
            reasonCode="ORDER_ACCEPTED",
            mode="demo",
            ticket=123456,
            verificationStatus="NOT_APPLICABLE",
            executionState="NONE",
        )
        with self.assertRaises(self.gateway_module.AckValidationError) as raised:
            gateway.ingest_ack(invalid)
        self.assertEqual(raised.exception.code, "unverified_executed_ack")

        accepted = gateway.ingest_ack(self.ack(
            command,
            status="EXECUTED",
            reasonCode="ORDER_ACCEPTED",
            mode="demo",
            ticket=123456,
        ))
        self.assertTrue(accepted["outstandingReleased"])
        outcome = load_example("outcome.example.json")
        outcome.update({
            "channelId": command["channelId"],
            "commandId": command["commandId"],
            "ticket": 123456,
            "openPrice": command["referencePrice"],
            "comment": f"HQ:{command['commandId']}",
        })
        outcome_path = (
            self.file_common
            / "MetafxHQ"
            / str(command["channelId"])
            / "trade-gateway"
            / "outcomes"
            / f"{command['commandId']}.json"
        )
        outcome_path.parent.mkdir(parents=True, exist_ok=True)
        outcome_raw = json.dumps(outcome, separators=(",", ":"))
        for field in ("openPrice", "stopLoss", "takeProfit"):
            encoded = json.dumps(outcome[field], separators=(",", ":"))
            outcome_raw = outcome_raw.replace(
                f'"{field}":{encoded}',
                f'"{field}":{float(outcome[field]):.2f}',
                1,
            )
        outcome_path.write_text(outcome_raw, encoding="ascii")
        observed = gateway.read_outcome(str(command["commandId"]))
        self.assertEqual(observed["ticket"], 123456)
        self.assertEqual(observed["executionState"], "CLOSED")
        self.assertEqual(observed["closedPnl"], 4.25)

    def test_execution_unknown_can_only_be_quarantined_fail_closed(self) -> None:
        gateway = self.gateway()
        command = gateway.queue_trade_intent(self.intent())["command"]
        gateway.ingest_ack(self.ack(
            command,
            status="EXECUTING",
            reasonCode="EXECUTION_STARTED",
        ))
        gateway.ingest_ack(self.ack(
            command,
            status="EXECUTION_UNKNOWN",
            reasonCode="ORDER_POST_SEND_SELECT_FAILED",
            mode="demo",
            ticket=123456,
        ))
        revision = gateway.status()["ledgerRevision"]
        with self.assertRaises(self.gateway_module.GatewaySafetyError) as stale:
            gateway.quarantine_execution_unknown(
                str(command["commandId"]),
                expected_ledger_revision=revision - 1,
            )
        self.assertEqual(stale.exception.code, "stale_ledger_revision")

        result = gateway.quarantine_execution_unknown(
            str(command["commandId"]),
            expected_ledger_revision=revision,
        )
        self.assertTrue(result["killSwitchActive"])
        self.assertTrue(result["barClaimRetained"])
        self.assertTrue(result["slotReleased"])
        self.assertIsNone(gateway.status()["activeCommandId"])
        kill_switch = (
            self.file_common
            / "MetafxHQ"
            / str(command["channelId"])
            / "trade-gateway"
            / "kill.switch"
        )
        self.assertTrue(kill_switch.is_file())
        with self.assertRaises(self.gateway_module.GatewaySafetyError) as blocked:
            gateway.queue_trade_intent(self.next_bar())
        self.assertEqual(blocked.exception.code, "kill_switch_active")

    def test_heartbeat_is_capped_by_command_ttl_and_expiry_is_fail_closed(self) -> None:
        gateway = self.gateway(
            command_ttl_seconds=10,
            heartbeat_ttl_seconds=60,
        )
        queued = gateway.queue_trade_intent(self.intent())
        command = queued["command"]
        self.assertEqual(queued["heartbeat"]["expiresAt"], command["expiresAt"])

        self.clock.advance(5)
        refreshed = gateway.refresh_heartbeat()
        self.assertEqual(
            refreshed["heartbeat"]["expiresAt"],
            command["expiresAt"],
        )
        self.clock.advance(5)
        with self.assertRaises(self.gateway_module.GatewaySafetyError) as raised:
            gateway.refresh_heartbeat()
        self.assertEqual(raised.exception.code, "command_expired")
        self.assertEqual(gateway.status()["activeCommandId"], command["commandId"])

    def test_kill_switch_and_corrupt_ledger_both_fail_closed(self) -> None:
        kill_switch = (
            self.file_common
            / "MetafxHQ"
            / "mtc-demo-01"
            / "trade-gateway"
            / "kill.switch"
        )
        kill_switch.parent.mkdir(parents=True, exist_ok=True)
        kill_switch.write_text("locked", encoding="ascii")
        with self.assertRaises(self.gateway_module.GatewaySafetyError) as raised:
            self.gateway().queue_trade_intent(self.intent())
        self.assertEqual(raised.exception.code, "kill_switch_active")

        kill_switch.unlink()
        gateway = self.gateway()
        gateway.queue_trade_intent(self.intent())
        ledger_path = self.state_root / "mt4-trade-gateway-ledger.json"
        ledger_path.write_text("{broken", encoding="ascii")
        with self.assertRaises(self.gateway_module.LedgerIntegrityError):
            gateway.status()

    def test_import_helpers_are_thin_and_do_not_create_global_runtime_state(self) -> None:
        gateway = self.gateway()
        queued = self.gateway_module.queue_trade_intent(gateway, self.intent())
        ingested = self.gateway_module.ingest_trade_ack(
            gateway,
            self.ack(queued["command"]),
        )
        self.assertTrue(ingested["outstandingReleased"])
        self.assertFalse(hasattr(self.gateway_module, "_DEFAULT_GATEWAY"))


if __name__ == "__main__":
    unittest.main()
