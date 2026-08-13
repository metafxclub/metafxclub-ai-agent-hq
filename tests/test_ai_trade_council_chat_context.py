from __future__ import annotations

import importlib.util
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
RUNNER_PATH = PROJECT_ROOT / "runner" / "codex_cli_runner.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AiTradeCouncilChatContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module("metafx_bridge_council_chat_tests", BRIDGE_PATH)
        cls.runner = load_module("metafx_runner_council_chat_tests", RUNNER_PATH)

    @staticmethod
    def vote(
        agent_id: str,
        role_id: str,
        decision: str,
        *,
        marker: str,
    ) -> dict:
        directional = decision in {"BUY", "SELL"}
        return {
            "schemaVersion": "ai-trade-council-vote-v2",
            "snapshotId": "a" * 64,
            "agentId": agent_id,
            "roleId": role_id,
            "decision": decision,
            "confidence": 72,
            "stopLossPrice": 2300.0 if directional else None,
            "takeProfitPrice": 2500.0 if directional else None,
            "horizon": "M5",
            "observations": [
                f"{marker}: เหตุผลที่อนุญาต",
                "broker server=HiddenBroker",
                "C:\\Users\\META\\secret\\report.json",
            ],
            "invalidation": "ยกเลิกมุมมองเมื่อโครงสร้างเปลี่ยน",
            "evidence": [
                {
                    "label": f"{marker} public evidence",
                    "observedAt": datetime.now(timezone.utc).isoformat(),
                    "sourceUrl": "https://example.com/market-report",
                },
                {
                    "label": "private host",
                    "observedAt": datetime.now(timezone.utc).isoformat(),
                    "sourceUrl": "http://127.0.0.1/private",
                },
                {
                    "label": "secret query",
                    "observedAt": datetime.now(timezone.utc).isoformat(),
                    "sourceUrl": "https://example.com/data?token=not-for-chat",
                },
            ],
            "warnings": [],
            "readOnly": True,
        }

    def mission(
        self,
        agent_id: str,
        role_id: str,
        decision: str,
        marker: str,
        minutes_ago: int,
    ) -> dict:
        observed = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
        updated = observed + timedelta(seconds=20)
        return {
            "id": f"mission-{agent_id}-{minutes_ago}",
            "owner": agent_id,
            "status": "completed",
            "parentMissionId": None,
            "completedAt": updated.isoformat(),
            "updatedAt": updated.isoformat(),
            "analysisContext": {
                "kind": "ai_trade_council_vote",
                "snapshotId": "a" * 64,
                "agentId": agent_id,
                "roleId": role_id,
                "closedBarIdentity": {
                    "candidateId": "mtc-private-terminal-reference",
                    "streamKey": "b" * 64,
                    "symbol": "XAUUSD",
                    "timeframe": "M5",
                    "closedBarTime": int(observed.timestamp()),
                },
            },
            "councilVote": self.vote(
                agent_id,
                role_id,
                decision,
                marker=marker,
            ),
        }

    def test_backend_context_is_agent_isolated_and_secret_free(self) -> None:
        technical = self.mission(
            "optimization_agent",
            "technical",
            "BUY",
            "TECHNICAL_ONLY",
            2,
        )
        price_action = self.mission(
            "backtest_analyst",
            "price_action",
            "SELL",
            "PRICE_ACTION_ONLY",
            1,
        )
        news = self.mission(
            "codex_mcp_operator",
            "news",
            "HOLD",
            "NEWS_ONLY",
            3,
        )
        with (
            mock.patch.object(
                self.bridge,
                "load_missions",
                return_value=[technical, price_action, news],
            ),
            mock.patch.object(
                self.bridge,
                "load_runtime_reports",
                return_value=[],
            ),
        ):
            technical_context = (
                self.bridge.ai_trade_council_agent_chat_context(
                    "optimization_agent"
                )
            )
            price_context = (
                self.bridge.ai_trade_council_agent_chat_context(
                    "backtest_analyst"
                )
            )

        self.assertEqual(technical_context["status"], "available")
        self.assertEqual(technical_context["agentId"], "optimization_agent")
        self.assertEqual(technical_context["direction"], "BUY")
        self.assertEqual(
            technical_context["reasons"],
            ["TECHNICAL_ONLY: เหตุผลที่อนุญาต"],
        )
        self.assertEqual(len(technical_context["evidence"]), 1)
        self.assertEqual(
            technical_context["evidence"][0]["sourceUrl"],
            "https://example.com/market-report",
        )
        self.assertEqual(price_context["direction"], "SELL")
        self.assertEqual(
            price_context["reasons"],
            ["PRICE_ACTION_ONLY: เหตุผลที่อนุญาต"],
        )
        serialized = json.dumps(
            technical_context,
            ensure_ascii=False,
            sort_keys=True,
        )
        self.assertNotIn("PRICE_ACTION_ONLY", serialized)
        self.assertNotIn("NEWS_ONLY", serialized)
        self.assertNotIn("HiddenBroker", serialized)
        self.assertNotIn("127.0.0.1", serialized)
        self.assertNotIn("not-for-chat", serialized)
        self.assertNotIn("candidateId", serialized)
        self.assertNotIn("streamKey", serialized)
        self.assertNotIn("ticket", serialized.lower())
        self.assertLessEqual(
            len(serialized),
            self.bridge.AI_TRADE_COUNCIL_CHAT_CONTEXT_MAX_CHARS,
        )

    def test_chat_freshness_uses_utc_evidence_not_broker_bar_clock(self) -> None:
        observed = datetime.now(timezone.utc) - timedelta(minutes=2)
        expected_observed_at = observed.isoformat().replace("+00:00", "Z")

        for broker_offset_hours in (3, -5):
            with self.subTest(broker_offset_hours=broker_offset_hours):
                mission = self.mission(
                    "optimization_agent",
                    "technical",
                    "BUY",
                    "BROKER_CLOCK_TEST",
                    2,
                )
                mission["analysisContext"]["snapshotObservedAt"] = (
                    expected_observed_at
                )
                mission["analysisContext"]["closedBarIdentity"][
                    "closedBarTime"
                ] = (
                    int(observed.timestamp())
                    + broker_offset_hours * 60 * 60
                    - 5 * 60
                )

                with (
                    mock.patch.object(
                        self.bridge,
                        "load_missions",
                        return_value=[mission],
                    ),
                    mock.patch.object(
                        self.bridge,
                        "load_runtime_reports",
                        return_value=[],
                    ),
                ):
                    context = self.bridge.ai_trade_council_agent_chat_context(
                        "optimization_agent"
                    )

                self.assertEqual(context["observedAt"], expected_observed_at)
                self.assertEqual(context["freshness"], "fresh")
                self.assertLess(context["ageSeconds"], 600)

    def test_chat_context_falls_back_to_zoned_mission_time_only(self) -> None:
        mission = self.mission(
            "optimization_agent",
            "technical",
            "BUY",
            "MISSION_TIME_TEST",
            2,
        )
        mission["analysisContext"].pop("snapshotObservedAt", None)
        expected = mission["completedAt"]
        symbol, timeframe, observed_at, _ = (
            self.bridge._ai_trade_council_chat_source_context(
                mission,
                {mission["id"]: mission},
            )
        )
        self.assertEqual((symbol, timeframe), ("XAUUSD", "M5"))
        self.assertEqual(
            observed_at,
            self.bridge.parse_iso(expected)
            .astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        )

        mission["completedAt"] = "2026-08-13T03:00:00"
        mission["updatedAt"] = "2026-08-13T03:00:00"
        mission["createdAt"] = "2026-08-13T03:00:00"
        _, _, observed_at, observed_time = (
            self.bridge._ai_trade_council_chat_source_context(
                mission,
                {mission["id"]: mission},
            )
        )
        self.assertIsNone(observed_at)
        self.assertIsNone(observed_time)

    def test_runner_rejects_cross_agent_and_secret_context(self) -> None:
        technical = self.mission(
            "optimization_agent",
            "technical",
            "BUY",
            "TECHNICAL_ONLY",
            2,
        )
        with (
            mock.patch.object(
                self.bridge,
                "load_missions",
                return_value=[technical],
            ),
            mock.patch.object(
                self.bridge,
                "load_runtime_reports",
                return_value=[],
            ),
        ):
            context = self.bridge.ai_trade_council_agent_chat_context(
                "optimization_agent"
            )

        accepted = self.runner.sanitize_council_chat_context(
            context,
            "optimization_agent",
        )
        isolated = self.runner.sanitize_council_chat_context(
            context,
            "backtest_analyst",
        )
        unsafe = {
            **context,
            "rogue": "account=123456 broker=Hidden",
        }
        rejected = self.runner.sanitize_council_chat_context(
            unsafe,
            "optimization_agent",
        )
        self.assertEqual(accepted["status"], "available")
        self.assertEqual(isolated["status"], "unavailable")
        self.assertEqual(
            isolated["reasonCode"],
            "latest_vote_context_mismatch",
        )
        self.assertEqual(rejected["status"], "unavailable")
        self.assertEqual(
            rejected["reasonCode"],
            "latest_vote_context_rejected",
        )

    def test_chat_prompt_uses_only_backend_context_and_no_vote_is_explicit(self) -> None:
        technical = self.mission(
            "optimization_agent",
            "technical",
            "BUY",
            "TECHNICAL_ONLY",
            2,
        )
        with (
            mock.patch.object(
                self.bridge,
                "load_missions",
                return_value=[technical],
            ),
            mock.patch.object(
                self.bridge,
                "load_runtime_reports",
                return_value=[],
            ),
        ):
            runner_payload = self.bridge._agent_chat_runner_request_payload(
                "ทำไมวิเคราะห์แบบนี้",
                [],
                "optimization_agent",
            )

        persona = {
            "id": "optimization_agent",
            "name": "Optimization Agent",
            "role": "Technical specialist",
            "goal": "อธิบาย Technical",
            "blockedActions": [],
            "memoryScope": "",
            "chatGreeting": "",
            "chatAnswerScope": "",
            "chatStyle": "",
            "chatBoundary": "",
            "tradeCouncil": {
                "enabled": True,
                "displayTitle": "Technical Agent",
                "specialization": "Indicator only",
                "structuredReport": "vote",
                "forbidden": [],
            },
        }
        prompt = self.runner.build_chat_prompt(
            runner_payload["message"],
            persona,
            [],
            5000,
            runner_payload["councilContext"],
        )
        self.assertIn("TECHNICAL_ONLY", prompt)
        self.assertIn('"direction":"BUY"', prompt)
        self.assertIn("ห้ามอ้างข้อมูลของ Agent ตัวอื่น", prompt)
        self.assertIn("conversation ไม่ใช่คำสั่งสร้าง Task", prompt)

        with (
            mock.patch.object(
                self.bridge,
                "load_missions",
                return_value=[],
            ),
            mock.patch.object(
                self.bridge,
                "load_runtime_reports",
                return_value=[],
            ),
        ):
            no_vote = self.bridge._agent_chat_runner_request_payload(
                "ทำไมวิเคราะห์แบบนี้",
                [],
                "codex_mcp_operator",
            )
        self.assertEqual(
            no_vote["councilContext"]["status"],
            "unavailable",
        )

    def test_non_council_agent_receives_no_council_context(self) -> None:
        payload = self.bridge._agent_chat_runner_request_payload(
            "สวัสดี",
            [],
            "ceo",
        )
        self.assertEqual(
            payload,
            {"message": "สวัสดี", "history": []},
        )


if __name__ == "__main__":
    unittest.main()
