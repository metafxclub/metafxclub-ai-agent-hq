from __future__ import annotations

import importlib.util
import math
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_bridge_vote_threshold_tests", BRIDGE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load bridge module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AiTradeCouncilVoteThresholdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def council_round(self, required_votes: int, decisions_by_role: dict[str, str]):
        now = datetime.now(timezone.utc)
        valid_until = int((now + timedelta(hours=1)).timestamp())
        snapshot_id = "a" * 64
        parent = {
            "analysisContext": {
                "kind": "ai_trade_council_parent",
                "snapshotId": snapshot_id,
                "referencePrice": 2400.0,
                "horizonBars": 1,
                "validUntilBarTime": valid_until,
                "requiredVotes": required_votes,
                "roundDeadlineAt": (now + timedelta(minutes=4)).isoformat(),
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
            }
        }
        children = []
        for agent_id, role_id in self.bridge.AI_TRADE_COUNCIL_AGENT_ROLES.items():
            decision = decisions_by_role[role_id]
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
                        2380.0
                        if role_id == "price_action" and decision == "BUY"
                        else 2420.0
                        if role_id == "price_action" and decision == "SELL"
                        else None
                    ),
                    "takeProfitPrice": (
                        2420.0
                        if role_id == "price_action" and decision == "BUY"
                        else 2380.0
                        if role_id == "price_action" and decision == "SELL"
                        else None
                    ),
                    "indicatorValidation": (
                        "PASS" if role_id == "technical" else None
                    ),
                    "volatilityState": (
                        "NORMAL" if role_id == "technical" else None
                    ),
                    "eventRisk": (
                        (
                            "ALLOW"
                            if decision in {"BUY", "SELL"}
                            else "HOLD"
                        )
                        if role_id == "news"
                        else None
                    ),
                    "newsEvidence": (
                        {
                            "fresh": True,
                            "distinctDomains": 2,
                            "requiredDistinctDomains": 2,
                        }
                        if role_id == "news"
                        else None
                    ),
                },
            })
        return parent, children

    def install_snapshot_artifact(self, root: Path, parent: dict) -> Path:
        context = parent["analysisContext"]
        snapshot_id = context["snapshotId"]
        bars = []
        start_time = 1_786_000_000
        for index in range(120):
            center = 2400.0 + math.sin(index / 4.0) * 8.0 + index * 0.02
            open_price = center - math.sin(index / 3.0) * 0.8
            close_price = center + math.cos(index / 5.0) * 0.8
            bars.append({
                "time": start_time + index * 300,
                "open": round(open_price, 5),
                "high": round(max(open_price, close_price) + 1.5, 5),
                "low": round(min(open_price, close_price) - 1.5, 5),
                "close": round(close_price, 5),
                "volume": 1000.0 + index,
            })
        context.update({
            "usedAnalysisBarCount": len(bars),
            "snapshotObservedAt": datetime.now(timezone.utc).isoformat(),
            "indicatorFormulaVersion": (
                self.bridge.AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION
            ),
            "closedBarIdentity": {
                "candidateId": "mtc-deterministic-fallback-test",
                "streamKey": "b" * 64,
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "closedBarTime": bars[-1]["time"],
            },
        })
        snapshot_dir = root / "ai-trade-council" / "snapshots"
        self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR = snapshot_dir
        artifact = {
            "schemaVersion": "ai-trade-council-input-v1",
            "snapshotId": snapshot_id,
            "createdAt": self.bridge.utc_now(),
            "sourceMode": "mt4_read_only_snapshot",
            "dailySummary": None,
            "chartSnapshot": {
                "available": True,
                "snapshotId": snapshot_id,
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "bid": 2399.9,
                "ask": 2400.1,
                "bars": bars,
                "analysisWindow": {
                    "requestedBars": len(bars),
                    "usedBars": len(bars),
                    "closedBarsOnly": True,
                },
            },
            "policy": {
                "readOnly": True,
                "sameSnapshotRequired": True,
                "terminalActionsAllowed": False,
            },
        }
        artifact_digest = (
            self.bridge._ai_trade_council_snapshot_artifact_digest(artifact)
        )
        artifact["artifactDigest"] = artifact_digest
        artifact_path = snapshot_dir / f"{artifact_digest}.json"
        context.update({
            "snapshotArtifact": (
                f"ai-trade-council/snapshots/{artifact_path.name}"
            ),
            "snapshotArtifactDigest": artifact_digest,
        })
        self.bridge.write_json(artifact_path, artifact)
        return artifact_path

    def test_one_of_three_allows_direction_when_other_votes_hold(self) -> None:
        parent, children = self.council_round(1, {
            "technical": "HOLD",
            "price_action": "BUY",
            "news": "HOLD",
        })
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        self.assertTrue(consensus["ready"])
        self.assertTrue(consensus["consensusReached"])
        self.assertFalse(consensus["unanimous"])
        self.assertEqual(consensus["selectedDirection"], "BUY")
        self.assertEqual(consensus["decision"], "BUY")
        self.assertEqual(consensus["requiredVotes"], 1)
        self.assertEqual(consensus["directionalVoteCount"], 1)
        self.assertEqual(
            consensus["directionCounts"],
            {"BUY": 1, "HOLD": 2, "SELL": 0, "NO_DATA": 0},
        )
        self.assertTrue(consensus["qualityGate"]["passed"])
        self.assertTrue(consensus["tradePlan"]["available"])

    def test_completed_round_keeps_original_deadline_result_during_later_reconciliation(self) -> None:
        parent, children = self.council_round(1, {
            "technical": "SELL",
            "price_action": "SELL",
            "news": "HOLD",
        })
        now = datetime.now(timezone.utc)
        deadline = now - timedelta(minutes=20)
        completed_at = deadline - timedelta(seconds=5)
        parent["analysisContext"]["roundDeadlineAt"] = deadline.isoformat()
        parent["analysisContext"]["validUntilBarTime"] = int(
            (now + timedelta(hours=1)).timestamp()
        )
        for child in children:
            child["completedAt"] = completed_at.isoformat()
            child["councilVote"]["validUntilBarTime"] = parent[
                "analysisContext"
            ]["validUntilBarTime"]

        consensus = self.bridge.ai_trade_council_consensus(parent, children)

        self.assertEqual(consensus["decision"], "SELL")
        self.assertTrue(consensus["qualityGate"]["passed"])
        self.assertFalse(consensus["qualityGate"]["roundExpired"])
        self.assertNotIn(
            "round_deadline_expired",
            consensus["qualityGate"]["reasonCodes"],
        )
        self.assertEqual(
            consensus["decisionProvenance"]["createdAt"],
            completed_at.isoformat().replace("+00:00", "Z"),
        )

    def test_broker_clock_horizon_is_never_compared_with_utc(self) -> None:
        now = datetime.now(timezone.utc)
        for broker_offset_hours in (3, -5):
            with self.subTest(broker_offset_hours=broker_offset_hours):
                parent, children = self.council_round(1, {
                    "technical": "SELL",
                    "price_action": "SELL",
                    "news": "HOLD",
                })
                raw_closed_bar = (
                    int(now.timestamp())
                    + broker_offset_hours * 60 * 60
                    - 5 * 60
                )
                broker_clock_horizon = raw_closed_bar + 2 * 5 * 60
                parent["analysisContext"]["validUntilBarTime"] = (
                    broker_clock_horizon
                )
                for child in children:
                    child["councilVote"]["validUntilBarTime"] = (
                        broker_clock_horizon
                    )

                consensus = self.bridge.ai_trade_council_consensus(
                    parent,
                    children,
                )

                self.assertTrue(consensus["qualityGate"]["passed"])
                self.assertFalse(consensus["qualityGate"]["roundExpired"])
                self.assertFalse(consensus["qualityGate"]["horizonExpired"])
                self.assertEqual(
                    consensus["qualityGate"]["validUntilBarTimeDomain"],
                    "mt4_broker_clock",
                )
                self.assertEqual(
                    consensus["qualityGate"]["decisionExpirySource"],
                    "round_deadline_at_utc",
                )

    def test_expired_round_never_dispatches_historical_trade_plan(self) -> None:
        parent, children = self.council_round(1, {
            "technical": "SELL",
            "price_action": "SELL",
            "news": "HOLD",
        })
        now = datetime.now(timezone.utc)
        deadline = now - timedelta(minutes=20)
        completed_at = deadline - timedelta(seconds=5)
        parent["id"] = "mission-historical-dispatch-block-test"
        parent["analysisContext"].update({
            "roundDeadlineAt": deadline.isoformat(),
            # Deliberately future-dated like a broker-time-derived epoch. The
            # UTC dispatch deadline must remain authoritative for publication.
            "validUntilBarTime": int((now + timedelta(hours=3)).timestamp()),
            "snapshotObservedAt": completed_at.isoformat(),
            "closedBarIdentity": {
                "candidateId": "mtc-historical-dispatch-test",
                "streamKey": "b" * 64,
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "closedBarTime": int(completed_at.timestamp()) - 300,
            },
        })
        for child in children:
            child["completedAt"] = completed_at.isoformat()
            child["councilVote"]["validUntilBarTime"] = parent[
                "analysisContext"
            ]["validUntilBarTime"]

        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        self.assertEqual(consensus["decision"], "SELL")
        self.assertTrue(consensus["qualityGate"]["passed"])

        gateway_status_calls = []
        queue_calls = []

        def ready_gateway_status():
            gateway_status_calls.append(True)
            return {
                "connected": True,
                "selectedCandidateId": "mtc-historical-dispatch-test",
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "mode": "demo",
                "executionGuardReady": True,
                "demoOrderExecutionAvailable": True,
            }

        class ReadyGateway:
            def queue_trade_intent(self, intent):
                queue_calls.append(intent)
                raise AssertionError("expired decision must never be queued")

        original_status = self.bridge.mt4_trade_gateway_status_read_model
        original_gateway = self.bridge._mt4_trade_gateway_instance
        try:
            self.bridge.mt4_trade_gateway_status_read_model = ready_gateway_status
            self.bridge._mt4_trade_gateway_instance = lambda: ReadyGateway()
            result = self.bridge.dispatch_ai_trade_council_trade_plan(
                parent,
                consensus,
            )
        finally:
            self.bridge.mt4_trade_gateway_status_read_model = original_status
            self.bridge._mt4_trade_gateway_instance = original_gateway

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(
            result["reasonCode"],
            "decision_dispatch_window_expired",
        )
        self.assertFalse(result["commandPublished"])
        self.assertEqual(gateway_status_calls, [])
        self.assertEqual(queue_calls, [])

    def test_expired_round_still_tracks_previously_published_command_ack(self) -> None:
        parent = {
            "analysisContext": {
                "roundDeadlineAt": (
                    datetime.now(timezone.utc) - timedelta(minutes=20)
                ).isoformat(),
            },
            "tradeGateway": {"commandId": "cmd-existing-ack-test"},
        }
        consensus = {}
        original_read_command = self.bridge._mt4_trade_gateway_command_read_model
        original_status = self.bridge.mt4_trade_gateway_status_read_model
        try:
            self.bridge._mt4_trade_gateway_command_read_model = lambda command_id: {
                "commandId": command_id,
                "status": "acknowledged",
                "ack": {
                    "status": "EXECUTED",
                    "reasonCode": "order_executed",
                },
            }
            self.bridge.mt4_trade_gateway_status_read_model = lambda: {
                "connected": True,
                "mode": "demo",
            }
            result = self.bridge.dispatch_ai_trade_council_trade_plan(
                parent,
                consensus,
            )
        finally:
            self.bridge._mt4_trade_gateway_command_read_model = original_read_command
            self.bridge.mt4_trade_gateway_status_read_model = original_status

        self.assertEqual(result["status"], "ack_executed")
        self.assertEqual(result["reasonCode"], "order_executed")
        self.assertTrue(result["commandPublished"])
        self.assertTrue(result["orderExecutionConfirmed"])

    def test_news_hold_is_an_abstention_and_allows_threshold_trade(self) -> None:
        parent, children = self.council_round(1, {
            "technical": "SELL",
            "price_action": "SELL",
            "news": "HOLD",
        })
        news_agent_id = next(
            agent_id
            for agent_id, role_id in self.bridge.AI_TRADE_COUNCIL_AGENT_ROLES.items()
            if role_id == "news"
        )
        news_child = next(item for item in children if item["owner"] == news_agent_id)
        news_child["councilVote"]["eventRisk"] = "HOLD"
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        self.assertTrue(consensus["consensusReached"])
        self.assertEqual(consensus["selectedDirection"], "SELL")
        self.assertEqual(consensus["directionalVoteCount"], 2)
        self.assertEqual(consensus["decision"], "SELL")
        self.assertTrue(consensus["qualityGate"]["passed"])
        self.assertTrue(consensus["qualityGate"]["newsEvidencePassed"])
        self.assertFalse(consensus["qualityGate"]["newsEvidenceRequired"])
        self.assertTrue(consensus["qualityGate"]["newsAbstained"])
        self.assertFalse(consensus["qualityGate"]["newsVeto"])
        self.assertTrue(consensus["tradePlan"]["available"])

    def test_news_event_risk_veto_hard_blocks_threshold_trade(self) -> None:
        parent, children = self.council_round(1, {
            "technical": "HOLD",
            "price_action": "SELL",
            "news": "HOLD",
        })
        news_agent_id = next(
            agent_id
            for agent_id, role_id in self.bridge.AI_TRADE_COUNCIL_AGENT_ROLES.items()
            if role_id == "news"
        )
        news_child = next(item for item in children if item["owner"] == news_agent_id)
        news_child["councilVote"]["eventRisk"] = "VETO"
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        self.assertTrue(consensus["consensusReached"])
        self.assertEqual(consensus["selectedDirection"], "SELL")
        self.assertEqual(consensus["decision"], "NO_TRADE")
        self.assertFalse(consensus["qualityGate"]["passed"])
        self.assertFalse(consensus["qualityGate"]["newsEvidencePassed"])
        self.assertFalse(consensus["qualityGate"]["newsEvidenceRequired"])
        self.assertFalse(consensus["qualityGate"]["newsAbstained"])
        self.assertTrue(consensus["qualityGate"]["newsVeto"])
        self.assertIn("news_event_veto", consensus["qualityGate"]["reasonCodes"])
        self.assertFalse(consensus["tradePlan"]["available"])

    def test_directional_news_vote_still_requires_fresh_distinct_evidence(self) -> None:
        parent, children = self.council_round(1, {
            "technical": "HOLD",
            "price_action": "BUY",
            "news": "BUY",
        })
        news_agent_id = next(
            agent_id
            for agent_id, role_id in self.bridge.AI_TRADE_COUNCIL_AGENT_ROLES.items()
            if role_id == "news"
        )
        news_child = next(item for item in children if item["owner"] == news_agent_id)
        news_child["councilVote"]["newsEvidence"] = {
            "fresh": False,
            "distinctDomains": 1,
            "requiredDistinctDomains": 2,
        }
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        self.assertTrue(consensus["consensusReached"])
        self.assertEqual(consensus["selectedDirection"], "BUY")
        self.assertEqual(consensus["decision"], "NO_TRADE")
        self.assertFalse(consensus["qualityGate"]["passed"])
        self.assertTrue(consensus["qualityGate"]["newsEvidenceRequired"])
        self.assertFalse(consensus["qualityGate"]["newsEvidencePassed"])
        self.assertFalse(consensus["qualityGate"]["newsAbstained"])
        self.assertFalse(consensus["qualityGate"]["newsVeto"])
        self.assertIn(
            "news_evidence_gate_failed",
            consensus["qualityGate"]["reasonCodes"],
        )
        self.assertFalse(consensus["tradePlan"]["available"])

    def test_buy_and_sell_conflict_is_no_trade_for_every_threshold(self) -> None:
        for required_votes in (1, 2, 3):
            with self.subTest(requiredVotes=required_votes):
                parent, children = self.council_round(required_votes, {
                    "technical": "BUY",
                    "price_action": "SELL",
                    "news": "HOLD",
                })
                consensus = self.bridge.ai_trade_council_consensus(parent, children)
                self.assertTrue(consensus["directionConflict"])
                self.assertFalse(consensus["consensusReached"])
                self.assertEqual(consensus["decision"], "NO_TRADE")
                self.assertFalse(consensus["tradePlan"]["available"])
                self.assertIn(
                    "direction_conflict_buy_sell",
                    consensus["qualityGate"]["reasonCodes"],
                )

    def test_dispatch_accepts_threshold_consensus_but_does_not_bypass_gateway(self) -> None:
        parent, children = self.council_round(1, {
            "technical": "HOLD",
            "price_action": "SELL",
            "news": "HOLD",
        })
        now = datetime.now(timezone.utc)
        parent["id"] = "mission-threshold-dispatch-test"
        parent["analysisContext"].update({
            "snapshotObservedAt": now.isoformat(),
            "closedBarIdentity": {
                "candidateId": "mtc-threshold-test",
                "streamKey": "b" * 64,
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "closedBarTime": int(now.timestamp()) - 300,
            },
        })
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        original_status = self.bridge.mt4_trade_gateway_status_read_model
        try:
            self.bridge.mt4_trade_gateway_status_read_model = lambda: {
                "connected": False,
                "reasonCode": "test_gateway_disconnected",
            }
            result = self.bridge.dispatch_ai_trade_council_trade_plan(
                parent, consensus
            )
        finally:
            self.bridge.mt4_trade_gateway_status_read_model = original_status
        self.assertEqual(result["status"], "waiting_gateway")
        self.assertEqual(result["reasonCode"], "test_gateway_disconnected")
        self.assertFalse(result["commandPublished"])

    def test_conflict_never_reaches_gateway_dispatch(self) -> None:
        parent, children = self.council_round(1, {
            "technical": "BUY",
            "price_action": "SELL",
            "news": "HOLD",
        })
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        parent["analysisContext"].pop("roundDeadlineAt")
        original_status = self.bridge.mt4_trade_gateway_status_read_model
        try:
            self.bridge.mt4_trade_gateway_status_read_model = lambda: (
                (_ for _ in ()).throw(AssertionError("gateway must not be queried"))
            )
            result = self.bridge.dispatch_ai_trade_council_trade_plan(
                parent, consensus
            )
        finally:
            self.bridge.mt4_trade_gateway_status_read_model = original_status
        self.assertEqual(result["status"], "no_trade")
        self.assertEqual(result["reasonCode"], "consensus_threshold_not_met")
        self.assertFalse(result["commandPublished"])

    def test_two_and_three_vote_thresholds_are_enforced(self) -> None:
        parent, children = self.council_round(2, {
            "technical": "BUY",
            "price_action": "BUY",
            "news": "HOLD",
        })
        two_of_three = self.bridge.ai_trade_council_consensus(parent, children)
        self.assertEqual(two_of_three["decision"], "BUY")
        self.assertEqual(two_of_three["directionalVoteCount"], 2)

        parent["analysisContext"]["requiredVotes"] = 3
        three_required = self.bridge.ai_trade_council_consensus(parent, children)
        self.assertFalse(three_required["consensusReached"])
        self.assertEqual(three_required["decision"], "NO_TRADE")
        self.assertIn(
            "directional_votes_below_threshold",
            three_required["qualityGate"]["reasonCodes"],
        )

    def test_price_action_plan_is_still_required(self) -> None:
        parent, children = self.council_round(1, {
            "technical": "BUY",
            "price_action": "HOLD",
            "news": "HOLD",
        })
        consensus = self.bridge.ai_trade_council_consensus(parent, children)
        self.assertTrue(consensus["consensusReached"])
        self.assertEqual(consensus["selectedDirection"], "BUY")
        self.assertEqual(consensus["decision"], "NO_TRADE")
        self.assertFalse(consensus["tradePlan"]["available"])
        self.assertIn(
            "price_action_protective_plan_failed",
            consensus["qualityGate"]["reasonCodes"],
        )
        self.assertIn(
            "fallback_snapshot_digest_missing",
            consensus["qualityGate"]["reasonCodes"],
        )
        self.assertTrue(
            consensus["qualityGate"]["protectivePlanFallbackAttempted"]
        )
        self.assertFalse(
            consensus["qualityGate"]["protectivePlanFallbackUsed"]
        )

    def test_price_action_hold_uses_closed_bar_fallback_for_passed_thresholds(self) -> None:
        cases = (
            (
                1,
                "BUY",
                {"technical": "BUY", "price_action": "HOLD", "news": "HOLD"},
            ),
            (
                2,
                "SELL",
                {"technical": "SELL", "price_action": "HOLD", "news": "SELL"},
            ),
        )
        original_snapshot_dir = self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR
        try:
            for required_votes, direction, votes in cases:
                with self.subTest(requiredVotes=required_votes, direction=direction):
                    with tempfile.TemporaryDirectory() as directory:
                        parent, children = self.council_round(required_votes, votes)
                        self.install_snapshot_artifact(Path(directory), parent)

                        consensus = self.bridge.ai_trade_council_consensus(
                            parent,
                            children,
                        )

                        self.assertEqual(consensus["decision"], direction)
                        self.assertTrue(consensus["qualityGate"]["passed"])
                        self.assertTrue(consensus["tradePlan"]["available"])
                        self.assertEqual(
                            consensus["tradePlan"]["protectivePlanSource"],
                            "backend_deterministic_fallback",
                        )
                        self.assertEqual(
                            consensus["tradePlan"]["protectivePlanReasonCode"],
                            "price_action_hold_consensus_fallback",
                        )
                        self.assertEqual(
                            consensus["tradePlan"]["protectivePriceOwnerRole"],
                            "backend_deterministic_guard",
                        )
                        self.assertTrue(
                            consensus["tradePlan"]["protectivePlanFallbackUsed"]
                        )
                        self.assertGreaterEqual(
                            consensus["tradePlan"]["rewardRiskRatio"],
                            1.0,
                        )
                        if direction == "BUY":
                            self.assertLess(
                                consensus["tradePlan"]["stopLossPrice"],
                                2400.0,
                            )
                            self.assertGreater(
                                consensus["tradePlan"]["takeProfitPrice"],
                                2400.0,
                            )
                        else:
                            self.assertGreater(
                                consensus["tradePlan"]["stopLossPrice"],
                                2400.0,
                            )
                            self.assertLess(
                                consensus["tradePlan"]["takeProfitPrice"],
                                2400.0,
                            )
                        provenance = consensus["tradePlan"][
                            "protectivePlanProvenance"
                        ]
                        self.assertEqual(provenance["snapshotId"], "a" * 64)
                        self.assertEqual(provenance["analysisBarCount"], 120)
                        self.assertTrue(provenance["closedBarsOnly"])
                        self.assertNotIn(
                            "price_action_protective_plan_failed",
                            consensus["qualityGate"]["reasonCodes"],
                        )
        finally:
            self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR = original_snapshot_dir

    def test_three_required_votes_cannot_be_bypassed_when_price_action_holds(self) -> None:
        original_snapshot_dir = self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR
        try:
            with tempfile.TemporaryDirectory() as directory:
                parent, children = self.council_round(3, {
                    "technical": "BUY",
                    "price_action": "HOLD",
                    "news": "BUY",
                })
                self.install_snapshot_artifact(Path(directory), parent)

                consensus = self.bridge.ai_trade_council_consensus(parent, children)

                self.assertFalse(consensus["consensusReached"])
                self.assertEqual(consensus["decision"], "NO_TRADE")
                self.assertFalse(consensus["tradePlan"]["available"])
                self.assertFalse(
                    consensus["qualityGate"]["protectivePlanFallbackAttempted"]
                )
                self.assertIn(
                    "directional_votes_below_threshold",
                    consensus["qualityGate"]["reasonCodes"],
                )
        finally:
            self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR = original_snapshot_dir

    def test_technical_no_data_cannot_unlock_directional_news_fallback(self) -> None:
        original_snapshot_dir = self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR
        try:
            with tempfile.TemporaryDirectory() as directory:
                parent, children = self.council_round(1, {
                    "technical": "NO_DATA",
                    "price_action": "HOLD",
                    "news": "BUY",
                })
                # Defense in depth: even a previously stored malformed vote
                # that says NO_DATA + PASS must fail at consensus time.
                technical = next(
                    child for child in children
                    if child["councilVote"]["roleId"] == "technical"
                )
                technical["councilVote"]["indicatorValidation"] = "PASS"
                self.install_snapshot_artifact(Path(directory), parent)

                consensus = self.bridge.ai_trade_council_consensus(
                    parent,
                    children,
                )

                self.assertTrue(consensus["consensusReached"])
                self.assertEqual(consensus["selectedDirection"], "BUY")
                self.assertEqual(consensus["decision"], "NO_TRADE")
                self.assertFalse(consensus["qualityGate"]["passed"])
                self.assertIn(
                    "technical_deterministic_validation_failed",
                    consensus["qualityGate"]["reasonCodes"],
                )
                self.assertFalse(
                    consensus["qualityGate"][
                        "protectivePlanFallbackAttempted"
                    ]
                )
        finally:
            self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR = original_snapshot_dir

    def test_mutated_snapshot_artifact_fails_digest_binding(self) -> None:
        original_snapshot_dir = self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR
        try:
            with tempfile.TemporaryDirectory() as directory:
                parent, children = self.council_round(1, {
                    "technical": "BUY",
                    "price_action": "HOLD",
                    "news": "HOLD",
                })
                artifact_path = self.install_snapshot_artifact(
                    Path(directory),
                    parent,
                )
                artifact = self.bridge.read_json(artifact_path, {})
                artifact["chartSnapshot"]["bars"][10]["low"] -= 100.0
                # Deliberately retain the old stored digest: the parent-held
                # expected digest must detect this historical-bar mutation.
                self.bridge.write_json(artifact_path, artifact)

                consensus = self.bridge.ai_trade_council_consensus(
                    parent,
                    children,
                )

                self.assertEqual(consensus["decision"], "NO_TRADE")
                self.assertFalse(consensus["tradePlan"]["available"])
                self.assertTrue(
                    consensus["qualityGate"][
                        "protectivePlanFallbackAttempted"
                    ]
                )
                self.assertIn(
                    "fallback_snapshot_digest_mismatch",
                    consensus["qualityGate"]["reasonCodes"],
                )
        finally:
            self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR = original_snapshot_dir

    def test_deterministic_fallback_still_requires_gateway_readiness(self) -> None:
        original_snapshot_dir = self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR
        original_status = self.bridge.mt4_trade_gateway_status_read_model
        original_runtime = self.bridge.RUNTIME_DIR
        original_audit = self.bridge.AUDIT_PATH
        try:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.bridge.RUNTIME_DIR = root / "runtime"
                self.bridge.AUDIT_PATH = self.bridge.RUNTIME_DIR / "bridge-audit.jsonl"
                parent, children = self.council_round(1, {
                    "technical": "BUY",
                    "price_action": "HOLD",
                    "news": "HOLD",
                })
                parent["id"] = "mission-deterministic-fallback-gateway-test"
                self.install_snapshot_artifact(root, parent)
                consensus = self.bridge.ai_trade_council_consensus(parent, children)
                self.assertEqual(consensus["decision"], "BUY")
                self.assertTrue(
                    consensus["tradePlan"]["protectivePlanFallbackUsed"]
                )

                self.bridge.mt4_trade_gateway_status_read_model = lambda: {
                    "connected": False,
                    "reasonCode": "test_gateway_disconnected",
                }
                result = self.bridge.dispatch_ai_trade_council_trade_plan(
                    parent,
                    consensus,
                )

                self.assertEqual(result["status"], "waiting_gateway")
                self.assertEqual(result["reasonCode"], "test_gateway_disconnected")
                self.assertFalse(result["commandPublished"])
        finally:
            self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR = original_snapshot_dir
            self.bridge.mt4_trade_gateway_status_read_model = original_status
            self.bridge.RUNTIME_DIR = original_runtime
            self.bridge.AUDIT_PATH = original_audit

    def test_required_votes_persist_with_default_three_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime"
            original_runtime = self.bridge.RUNTIME_DIR
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.RUNTIME_DIR = runtime
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                default_model = self.bridge.ai_trade_council_automation_read_model()
                self.assertEqual(default_model["config"]["requiredVotes"], 3)
                updated = self.bridge.set_ai_trade_council_automation({
                    "requiredVotes": 1
                })
                self.assertTrue(updated["ok"])
                self.assertEqual(updated["automation"]["config"]["requiredVotes"], 1)
                self.assertEqual(
                    self.bridge.load_ai_trade_council_automation_store()["config"][
                        "requiredVotes"
                    ],
                    1,
                )
                audit_text = self.bridge.AUDIT_PATH.read_text(encoding="utf-8")
                self.assertIn('"requiredVotes": 1', audit_text)
                rejected = self.bridge.set_ai_trade_council_automation({
                    "requiredVotes": 0
                })
                self.assertFalse(rejected["ok"])
                self.assertEqual(rejected["kind"], "invalid_requiredVotes")
            finally:
                self.bridge.RUNTIME_DIR = original_runtime
                self.bridge.AUDIT_PATH = original_audit

    def test_max_managed_orders_defaults_persists_and_rejects_non_allowlisted_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime"
            original_runtime = self.bridge.RUNTIME_DIR
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.RUNTIME_DIR = runtime
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"

                default_model = self.bridge.ai_trade_council_automation_read_model()
                self.assertEqual(default_model["config"]["maxManagedOrders"], 1)
                self.assertEqual(
                    default_model["config"]["allowedMaxManagedOrders"],
                    [1, 3, 5, 10],
                )

                for allowed_value in (3, 5, 10, 1):
                    with self.subTest(allowed=allowed_value):
                        updated = self.bridge.set_ai_trade_council_automation({
                            "maxManagedOrders": allowed_value,
                        })
                        self.assertTrue(updated["ok"])
                        self.assertEqual(
                            updated["automation"]["config"]["maxManagedOrders"],
                            allowed_value,
                        )
                        self.assertEqual(
                            self.bridge.load_ai_trade_council_automation_store()[
                                "config"
                            ]["maxManagedOrders"],
                            allowed_value,
                        )

                for rejected_value in (2, 4, 11, True, "3"):
                    with self.subTest(rejected=rejected_value):
                        rejected = self.bridge.set_ai_trade_council_automation({
                            "maxManagedOrders": rejected_value,
                        })
                        self.assertFalse(rejected["ok"])
                        self.assertEqual(rejected["kind"], "invalid_maxManagedOrders")
                        self.assertEqual(
                            rejected["allowedMaxManagedOrders"],
                            [1, 3, 5, 10],
                        )
                        self.assertEqual(
                            self.bridge.load_ai_trade_council_automation_store()[
                                "config"
                            ]["maxManagedOrders"],
                            1,
                        )

                audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)
                accepted = [
                    event
                    for event in audit
                    if event.get("type") == "ai_trade_council.automation_changed"
                    and "maxManagedOrders" in event
                ]
                rejected_events = [
                    event
                    for event in audit
                    if event.get("type")
                    == "ai_trade_council.automation_change_rejected"
                    and event.get("reason") == "invalid_max_managed_orders"
                ]
                self.assertEqual(
                    [event["maxManagedOrders"] for event in accepted],
                    [3, 5, 10, 1],
                )
                self.assertEqual(len(rejected_events), 5)
                self.assertTrue(
                    all(event.get("terminalActions") is False for event in rejected_events)
                )
            finally:
                self.bridge.RUNTIME_DIR = original_runtime
                self.bridge.AUDIT_PATH = original_audit


if __name__ == "__main__":
    unittest.main()
