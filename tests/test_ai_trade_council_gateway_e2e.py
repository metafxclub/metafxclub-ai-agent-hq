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
        self.original_selection_token_reader = (
            self.bridge._metatrader_selection_token
        )
        self.original_snapshot_reader = self.bridge.metatrader_snapshot_read_model
        self.original_snapshot_dir = self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR
        self.bridge.RUNTIME_DIR = self.root / "runtime"
        self.bridge.AUDIT_PATH = self.bridge.RUNTIME_DIR / "bridge-audit.jsonl"
        self.bridge.METATRADER_COMMON_FILES_DIR = self.root / "common"
        self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR = (
            self.root / "ai-trade-council" / "snapshots"
        )
        self.bridge.MT4_TRADE_GATEWAY_MODULE = None
        self.bridge._metatrader_selection_token = lambda _prop_id: {
            "candidateId": "mtc-safe-e2e-test",
            "selectionRevision": 1,
        }
        self.current_broker_closed_bar = 1_785_466_800
        self.bridge.metatrader_snapshot_read_model = self.current_snapshot

    def tearDown(self) -> None:
        self.bridge.RUNTIME_DIR = self.original_runtime_dir
        self.bridge.AUDIT_PATH = self.original_audit_path
        self.bridge.METATRADER_COMMON_FILES_DIR = self.original_common_files
        self.bridge.MT4_TRADE_GATEWAY_MODULE = self.original_gateway_module
        self.bridge.mt4_trade_gateway_status_read_model = (
            self.original_status_reader
        )
        self.bridge._metatrader_selection_token = (
            self.original_selection_token_reader
        )
        self.bridge.metatrader_snapshot_read_model = self.original_snapshot_reader
        self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR = self.original_snapshot_dir
        self.temp.cleanup()

    def current_snapshot(self, _prop_id: str) -> dict:
        return {
            "selectedCandidateId": "mtc-safe-e2e-test",
            "adapter": {"ready": True, "status": "ready"},
            "chartSnapshot": {
                "available": True,
                "snapshotId": "f" * 64,
                "observedAt": datetime.now(timezone.utc).isoformat(),
                "ageSeconds": 0,
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "bid": 2399.9,
                "ask": 2400.1,
                "spreadPoints": 20.0,
                "marketOpen": True,
                "bars": [{"time": self.current_broker_closed_bar}],
            },
        }

    def council_round(
        self,
        *,
        broker_offset_hours: int = 3,
    ) -> tuple[dict, list[dict]]:
        now = datetime.now(timezone.utc)
        snapshot_id = "a" * 64
        # MT4 represents iTime in broker/server-clock epoch.  Keep both the
        # closed-bar and horizon identity in that domain; only roundDeadlineAt
        # is eligible for UTC expiry comparisons.
        broker_closed_bar = (
            int(now.timestamp())
            + (broker_offset_hours * 60 * 60)
            - (5 * 60)
        )
        self.current_broker_closed_bar = broker_closed_bar
        valid_until = broker_closed_bar + 2 * 5 * 60
        parent = {
            "id": "mission-safe-e2e-demo-simulation",
            "analysisContext": {
                "kind": "ai_trade_council_parent",
                "snapshotId": snapshot_id,
                "snapshotObservedAt": now.isoformat(),
                "referencePrice": 2400.0,
                "analysisQuote": {
                    "schemaVersion": "ai-trade-council-analysis-quote-v1",
                    "snapshotId": snapshot_id,
                    "bid": 2399.9,
                    "ask": 2400.1,
                    "spreadPoints": 20.0,
                    "derivedPoint": 0.01,
                    "digits": 2,
                    "directionalReferencePolicy": (
                        "ask_for_buy_bid_for_sell"
                    ),
                },
                "horizonBars": 1,
                "validUntilBarTime": valid_until,
                "requiredVotes": 1,
                "roundDeadlineAt": (now + timedelta(minutes=4)).isoformat(),
                "closedBarIdentity": {
                    "candidateId": "mtc-safe-e2e-test",
                    "streamKey": self.bridge.payload_digest(
                        "mtc-safe-e2e-test",
                        "XAUUSD",
                        "M5",
                    ),
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
                        2421.0 if role_id == "price_action" else None
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
        self.install_analysis_artifact(parent)
        return parent, children

    def install_analysis_artifact(self, parent: dict) -> Path:
        context = parent["analysisContext"]
        bar_time = context["closedBarIdentity"]["closedBarTime"]
        artifact = {
            "schemaVersion": "ai-trade-council-input-v1",
            "snapshotId": context["snapshotId"],
            "createdAt": self.bridge.utc_now(),
            "sourceMode": "mt4_read_only_snapshot",
            "dailySummary": None,
            "chartSnapshot": {
                "available": True,
                "snapshotId": context["snapshotId"],
                "observedAt": context["snapshotObservedAt"],
                "symbol": context["closedBarIdentity"]["symbol"],
                "timeframe": context["closedBarIdentity"]["timeframe"],
                "bid": 2399.9,
                "ask": 2400.1,
                "spreadPoints": 20.0,
                "bars": [{
                    "time": bar_time,
                    "open": 2400.0,
                    "high": 2401.0,
                    "low": 2399.0,
                    "close": 2400.0,
                    "volume": 1.0,
                }],
            },
            "policy": {
                "readOnly": True,
                "sameSnapshotRequired": True,
                "terminalActionsAllowed": False,
            },
            "selectedCandidateId": "mtc-safe-e2e-test",
        }
        digest = self.bridge._ai_trade_council_snapshot_artifact_digest(
            artifact
        )
        artifact["artifactDigest"] = digest
        path = self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR / f"{digest}.json"
        self.bridge.write_json(path, artifact)
        context.update({
            "snapshotArtifact": (
                f"ai-trade-council/snapshots/{digest}.json"
            ),
            "snapshotArtifactDigest": digest,
        })
        return path

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

    def gateway_status(
        self,
        *,
        ea_max_managed_positions: int = 1,
        current_managed_positions: int = 0,
    ) -> dict:
        return {
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
            "maxManagedPositions": ea_max_managed_positions,
            "currentManagedPositions": current_managed_positions,
            "minRewardRiskRatio": 1.0,
            "maxSignalDriftPoints": 100,
            "maxSnapshotAgeSeconds": 300,
        }

    def configure_max_managed_orders(self, value: int) -> None:
        updated = self.bridge.set_ai_trade_council_automation({
            "maxManagedOrders": value,
        })
        self.assertTrue(updated["ok"])
        self.assertEqual(
            updated["automation"]["config"]["maxManagedOrders"],
            value,
        )

    def assert_ea_proven_history_blocks_at_ai_cap(
        self,
        execution_state: str,
    ) -> None:
        self.configure_max_managed_orders(1)
        parent, children = self.council_round()
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        status = self.gateway_status(
            ea_max_managed_positions=10,
            current_managed_positions=0,
        )
        status["orderHistory"] = {
            "schemaVersion": "metafx-hq-mt4-order-history-v1",
            "available": True,
            # Gateway history is already filtered to selectedCandidateId. An
            # EA-proven EXECUTED ACK is an order even when lifecycle telemetry
            # is missing/stale and therefore CONFIRMED_UNKNOWN.
            "items": [{
                "commandId": f"cmd-history-{execution_state.lower()}",
                "ticket": 987650,
                "side": "BUY",
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "executionState": execution_state,
                "verificationStatus": "VERIFIED_OPEN",
                "provenByEa": True,
            }],
            "totalExecuted": 1,
            "hasMore": False,
            "reasonCode": "ready",
            "sourceScope": "durable_gateway_ledger_executed_ack_only",
        }
        self.bridge.mt4_trade_gateway_status_read_model = lambda: dict(status)

        blocked = self.bridge.dispatch_ai_trade_council_trade_plan(
            parent,
            consensus,
        )

        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["reasonCode"], "max_managed_orders_reached")
        self.assertFalse(blocked["commandPublished"])
        self.assertEqual(
            blocked["managedOrderLimit"]["configuredMaxManagedOrders"],
            1,
        )
        self.assertEqual(
            blocked["managedOrderLimit"]["eaMaxManagedPositions"],
            10,
        )
        self.assertEqual(
            blocked["managedOrderLimit"]["effectiveMaxManagedOrders"],
            1,
        )
        self.assertGreaterEqual(
            blocked["managedOrderLimit"]["currentManagedPositions"],
            1,
        )
        self.assertTrue(blocked["managedOrderLimit"]["reached"])
        self.assertEqual(
            self.bridge._mt4_trade_gateway_instance().list_commands(limit=10),
            [],
        )

    def test_vote_to_signed_command_to_verified_ack_and_fill_simulation(self) -> None:
        parent, children = self.council_round()
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        self.assertTrue(consensus["ready"])
        self.assertTrue(consensus["qualityGate"]["passed"])
        self.assertEqual(consensus["decision"], "BUY")
        self.assertEqual(consensus["directionalVoteCount"], 1)
        self.assertEqual(consensus["requiredVotes"], 1)

        self.bridge.mt4_trade_gateway_status_read_model = self.gateway_status
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
        self.assertEqual(command["referencePrice"], 2400.1)
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
            "openPrice": float(command["referencePrice"]),
            "stopLoss": float(command["stopLoss"]),
            "takeProfit": float(command["takeProfit"]),
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
        self.assertTrue(observed["ok"], observed)
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

    def test_utc_minus_five_broker_horizon_uses_utc_dispatch_deadline(self) -> None:
        parent, children = self.council_round(broker_offset_hours=-5)
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        self.assertTrue(consensus["qualityGate"]["passed"])
        self.assertLess(
            consensus["validUntilBarTime"],
            int(datetime.now(timezone.utc).timestamp()),
        )
        self.bridge.mt4_trade_gateway_status_read_model = self.gateway_status

        dispatched = self.bridge.dispatch_ai_trade_council_trade_plan(
            parent,
            consensus,
        )

        self.assertEqual(dispatched["status"], "queued")
        self.assertTrue(dispatched["commandPublished"])

    def test_dispatch_uses_lower_ai_limit_when_ea_limit_is_higher(self) -> None:
        self.configure_max_managed_orders(3)
        parent, children = self.council_round()
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        self.bridge.mt4_trade_gateway_status_read_model = lambda: self.gateway_status(
            ea_max_managed_positions=10,
            current_managed_positions=2,
        )

        dispatched = self.bridge.dispatch_ai_trade_council_trade_plan(
            parent,
            consensus,
        )

        self.assertEqual(dispatched["status"], "queued")
        self.assertTrue(dispatched["commandPublished"])
        self.assertEqual(dispatched["managedOrderLimit"], {
            "configuredMaxManagedOrders": 3,
            "eaMaxManagedPositions": 10,
            "effectiveMaxManagedOrders": 3,
            "currentManagedPositions": 2,
            "reached": False,
            "source": "backend_dispatch_cap",
            "eaInputUnchanged": True,
        })

    def test_dispatch_uses_lower_ea_limit_when_ai_limit_is_higher(self) -> None:
        self.configure_max_managed_orders(10)
        parent, children = self.council_round()
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        self.bridge.mt4_trade_gateway_status_read_model = lambda: self.gateway_status(
            ea_max_managed_positions=3,
            current_managed_positions=2,
        )

        dispatched = self.bridge.dispatch_ai_trade_council_trade_plan(
            parent,
            consensus,
        )

        self.assertEqual(dispatched["status"], "queued")
        self.assertTrue(dispatched["commandPublished"])
        self.assertEqual(dispatched["managedOrderLimit"], {
            "configuredMaxManagedOrders": 10,
            "eaMaxManagedPositions": 3,
            "effectiveMaxManagedOrders": 3,
            "currentManagedPositions": 2,
            "reached": False,
            "source": "backend_dispatch_cap",
            "eaInputUnchanged": True,
        })

    def test_dispatch_blocks_when_current_positions_reach_effective_limit(self) -> None:
        parent, children = self.council_round()
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        scenarios = (
            (3, 5, 3, 3),
            (10, 3, 4, 3),
        )
        for configured, ea_limit, current, effective in scenarios:
            with self.subTest(
                configured=configured,
                ea_limit=ea_limit,
                current=current,
            ):
                self.configure_max_managed_orders(configured)
                self.bridge.mt4_trade_gateway_status_read_model = (
                    lambda ea_limit=ea_limit, current=current: self.gateway_status(
                        ea_max_managed_positions=ea_limit,
                        current_managed_positions=current,
                    )
                )
                blocked = self.bridge.dispatch_ai_trade_council_trade_plan(
                    parent,
                    consensus,
                )

                self.assertEqual(blocked["status"], "blocked")
                self.assertEqual(
                    blocked["reasonCode"],
                    "max_managed_orders_reached",
                )
                self.assertFalse(blocked["commandPublished"])
                self.assertEqual(blocked["managedOrderLimit"], {
                    "configuredMaxManagedOrders": configured,
                    "eaMaxManagedPositions": ea_limit,
                    "effectiveMaxManagedOrders": effective,
                    "currentManagedPositions": current,
                    "reached": True,
                    "source": "backend_dispatch_cap",
                    "eaInputUnchanged": True,
                })

    def test_dispatch_fails_closed_when_managed_position_telemetry_is_missing(self) -> None:
        self.configure_max_managed_orders(5)
        parent, children = self.council_round()
        consensus = self.bridge.ai_trade_council_consensus(parent, children)

        for missing_field in ("maxManagedPositions", "currentManagedPositions"):
            with self.subTest(missing=missing_field):
                status = self.gateway_status(
                    ea_max_managed_positions=10,
                    current_managed_positions=0,
                )
                status.pop(missing_field)
                self.bridge.mt4_trade_gateway_status_read_model = (
                    lambda status=status: dict(status)
                )

                blocked = self.bridge.dispatch_ai_trade_council_trade_plan(
                    parent,
                    consensus,
                )

                self.assertEqual(blocked["status"], "blocked")
                self.assertEqual(
                    blocked["reasonCode"],
                    "managed_position_telemetry_unavailable",
                )
                self.assertFalse(blocked["commandPublished"])
                self.assertEqual(
                    blocked["managedOrderLimit"]["configuredMaxManagedOrders"],
                    5,
                )
                self.assertIsNone(
                    blocked["managedOrderLimit"][
                        "eaMaxManagedPositions"
                        if missing_field == "maxManagedPositions"
                        else "currentManagedPositions"
                    ]
                )
                self.assertEqual(
                    blocked["managedOrderLimit"]["source"],
                    "backend_dispatch_cap",
                )
                self.assertTrue(
                    blocked["managedOrderLimit"]["eaInputUnchanged"]
                )

    def test_dispatch_counts_ea_proven_open_history_when_status_count_is_zero(self) -> None:
        self.assert_ea_proven_history_blocks_at_ai_cap("OPEN")

    def test_dispatch_counts_ea_proven_unknown_history_when_status_count_is_zero(self) -> None:
        self.assert_ea_proven_history_blocks_at_ai_cap("CONFIRMED_UNKNOWN")


if __name__ == "__main__":
    unittest.main()
