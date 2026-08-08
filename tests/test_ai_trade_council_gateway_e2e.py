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
        "metafx_bridge_ai_trade_gateway_e2e_tests",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load bridge module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AiTradeCouncilGatewayE2ETests(unittest.TestCase):
    """Exercise the complete trade path without touching a real MT4 channel."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.original_runtime_dir = self.bridge.RUNTIME_DIR
        self.original_audit_path = self.bridge.AUDIT_PATH
        self.original_common_files = self.bridge.METATRADER_COMMON_FILES_DIR
        self.original_gateway_module = self.bridge.MT4_TRADE_GATEWAY_MODULE
        self.original_status_reader = (
            self.bridge.mt4_trade_gateway_status_read_model
        )
        self.bridge.RUNTIME_DIR = self.root / "runtime"
        self.bridge.AUDIT_PATH = self.bridge.RUNTIME_DIR / "bridge-audit.jsonl"
        self.bridge.METATRADER_COMMON_FILES_DIR = self.root / "common"
        self.bridge.MT4_TRADE_GATEWAY_MODULE = None

    def tearDown(self) -> None:
        self.bridge.RUNTIME_DIR = self.original_runtime_dir
        self.bridge.AUDIT_PATH = self.original_audit_path
        self.bridge.METATRADER_COMMON_FILES_DIR = self.original_common_files
        self.bridge.MT4_TRADE_GATEWAY_MODULE = self.original_gateway_module
        self.bridge.mt4_trade_gateway_status_read_model = (
            self.original_status_reader
        )
        self.temp.cleanup()

    def council_round(self) -> tuple[dict, list[dict]]:
        now = datetime.now(timezone.utc)
        valid_until = int((now + timedelta(hours=1)).timestamp())
        snapshot_id = "a" * 64
        # MT4 represents iTime in broker/server-clock epoch.  A UTC+3 broker
        # therefore appears to be ahead of snapshotObservedAt even though it is
        # the same latest closed M5 bar.  This reproduces the production fault
        # without contacting a terminal.
        broker_closed_bar = int(now.timestamp()) + (3 * 60 * 60) - (5 * 60)
        parent = {
            "id": "mission-safe-e2e-demo-simulation",
            "analysisContext": {
                "kind": "ai_trade_council_parent",
                "snapshotId": snapshot_id,
                "snapshotObservedAt": now.isoformat(),
                "referencePrice": 2400.0,
                "horizonBars": 1,
                "validUntilBarTime": valid_until,
                "requiredVotes": 1,
                "roundDeadlineAt": (now + timedelta(minutes=4)).isoformat(),
                "closedBarIdentity": {
                    "candidateId": "mtc-safe-e2e-test",
                    "streamKey": "b" * 64,
                    "symbol": "XAUUSD",
                    "timeframe": "M5",
                    "closedBarTime": broker_closed_bar,
                },
                "qualityGate": {
                    "passed": True,
                    "reasonCodes": [],
                    "confidenceFloorDefault": 70,
                    "confidenceFloorByRole": {
                        "technical": 70,
                        "price_action": 70,
                        "news": 70,
                    },
                    "minimumRewardRiskRatio": 1.0,
                    "technical": {"volatilityState": "NORMAL"},
                    "executionEligibility": {
                        "shadow": True,
                        "demo": True,
                        "live": True,
                    },
                },
            },
        }
        decisions = {
            "technical": "HOLD",
            "price_action": "BUY",
            "news": "HOLD",
        }
        children = []
        for agent_id, role_id in self.bridge.AI_TRADE_COUNCIL_AGENT_ROLES.items():
            decision = decisions[role_id]
            children.append({
                "owner": agent_id,
                "completedAt": now.isoformat(),
                "councilVote": {
                    "snapshotId": snapshot_id,
                    "agentId": agent_id,
                    "roleId": role_id,
                    "decision": decision,
                    "confidence": 80,
                    "horizonBars": 1,
                    "validUntilBarTime": valid_until,
                    "stopLossPrice": (
                        2380.0 if role_id == "price_action" else None
                    ),
                    "takeProfitPrice": (
                        2420.0 if role_id == "price_action" else None
                    ),
                    "indicatorValidation": (
                        "PASS" if role_id == "technical" else None
                    ),
                    "volatilityState": (
                        "NORMAL" if role_id == "technical" else None
                    ),
                    "eventRisk": "HOLD" if role_id == "news" else None,
                    "newsEvidence": None,
                },
            })
        return parent, children

    def executed_ack(self, command: dict) -> dict:
        observed_at = max(
            int(datetime.now(timezone.utc).timestamp()),
            int(command["issuedAt"]),
        ) + 1
        return {
            "schemaVersion": "metafx-hq-mt4-ack-v3",
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
            "status": "EXECUTED",
            "reasonCode": "ORDER_ACCEPTED",
            "mode": "demo",
            "action": command["action"],
            "symbol": command["symbol"],
            "timeframe": command["timeframe"],
            "fixedLot": 0.01,
            "observedAt": observed_at,
            "ticket": 987654,
            "filledPrice": command["referencePrice"],
            "filledSlippagePoints": 0.0,
            "actualStopLoss": command["stopLoss"],
            "actualTakeProfit": command["takeProfit"],
            "actualMagicNumber": 4186001,
            "actualComment": f"HQ:{command['commandId']}",
            "signatureVerificationStatus": "VERIFIED",
            "verificationStatus": "VERIFIED_OPEN",
            "executionState": "OPEN",
            "closedAt": None,
            "closedPnl": None,
            "errorCode": 0,
            "statePersisted": True,
        }

    def test_vote_to_signed_command_to_verified_ack_and_fill_simulation(self) -> None:
        parent, children = self.council_round()
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        self.assertTrue(consensus["ready"])
        self.assertTrue(consensus["qualityGate"]["passed"])
        self.assertEqual(consensus["decision"], "BUY")
        self.assertEqual(consensus["directionalVoteCount"], 1)
        self.assertEqual(consensus["requiredVotes"], 1)

        self.bridge.mt4_trade_gateway_status_read_model = lambda: {
            "connected": True,
            "selectedCandidateId": "mtc-safe-e2e-test",
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "mode": "demo",
            "fixedLot": 0.01,
            "liveArmed": False,
            "killSwitchActive": False,
            "executionGuardReady": True,
            "demoOrderExecutionAvailable": True,
            "liveOrderExecutionAvailable": False,
        }
        dispatched = self.bridge.dispatch_ai_trade_council_trade_plan(
            parent,
            consensus,
        )
        self.assertEqual(dispatched["status"], "queued")
        self.assertTrue(dispatched["commandPublished"])
        command_id = dispatched["commandId"]
        self.assertIsNotNone(command_id)

        gateway = self.bridge._mt4_trade_gateway_instance()
        command = gateway.read_command(command_id)["command"]
        self.assertEqual(command["action"], "BUY")
        self.assertEqual(command["barTime"], parent["analysisContext"]["closedBarIdentity"]["closedBarTime"])
        self.assertNotIn("fixedLot", command)
        self.assertNotIn("risk", command)

        command_path = (
            self.bridge.METATRADER_COMMON_FILES_DIR
            / "MetafxHQ"
            / command["channelId"]
            / "trade-gateway"
            / "command.json"
        )
        envelope = json.loads(command_path.read_text(encoding="ascii"))
        self.assertEqual(
            envelope["schemaVersion"],
            "metafx-hq-mt4-signed-envelope-v1",
        )
        self.assertEqual(envelope["algorithm"], "HMAC-SHA256")
        # This read verifies the HMAC before returning the inner command.
        self.assertEqual(gateway._read_command_slot(command["channelId"]), command)

        accepted_ack = gateway.ingest_ack(self.executed_ack(command))
        self.assertEqual(accepted_ack["status"], "ack_EXECUTED")
        self.assertTrue(accepted_ack["outstandingReleased"])
        self.assertEqual(accepted_ack["ack"]["ticket"], 987654)

        outcome = {
            "schemaVersion": "metafx-hq-mt4-outcome-v1",
            "channelId": command["channelId"],
            "commandId": command["commandId"],
            "executionState": "CLOSED",
            "observedAt": self.executed_ack(command)["observedAt"] + 60,
            "ticket": 987654,
            "symbol": command["symbol"],
            "action": command["action"],
            "openedAt": self.executed_ack(command)["observedAt"],
            "closedAt": self.executed_ack(command)["observedAt"] + 60,
            "openPrice": command["referencePrice"],
            "stopLoss": command["stopLoss"],
            "takeProfit": command["takeProfit"],
            "lots": 0.01,
            "magicNumber": 4186001,
            "comment": f"HQ:{command['commandId']}",
            "closedPnl": 4.25,
        }
        outcome_path = (
            self.bridge.METATRADER_COMMON_FILES_DIR
            / "MetafxHQ"
            / command["channelId"]
            / "trade-gateway"
            / "outcomes"
            / f"{command['commandId']}.json"
        )
        outcome_path.parent.mkdir(parents=True, exist_ok=True)
        outcome_path.write_text(json.dumps(outcome), encoding="ascii")
        observed = self.bridge.mt4_trade_gateway_outcome_read_model(command_id)
        self.assertTrue(observed["ok"])
        self.assertEqual(observed["outcome"]["executionState"], "CLOSED")
        self.assertEqual(observed["outcome"]["ticket"], 987654)
        self.assertEqual(observed["outcome"]["closedPnl"], 4.25)

        parent["tradeGateway"] = {"commandId": command_id}
        reconciled = self.bridge.dispatch_ai_trade_council_trade_plan(
            parent,
            consensus,
        )
        self.assertEqual(reconciled["status"], "ack_executed")
        self.assertTrue(reconciled["orderExecutionConfirmed"])


if __name__ == "__main__":
    unittest.main()
