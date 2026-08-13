from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
MAIN_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "main.js"
STYLES_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "styles.css"
COUNCIL_PROMPTS_PATH = (
    PROJECT_ROOT / "contracts" / "orchestration" / "ai-trade-council-prompts.json"
)


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_bridge_ai_trade_agent_blocker_tests",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load bridge module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def function_block(source: str, signature: str) -> str:
    start = source.index(signature)
    end = source.find("\nfunction ", start + len(signature))
    return source[start : end if end >= 0 else len(source)]


class AiTradeCouncilAgentBlockerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()
        cls.main = MAIN_PATH.read_text(encoding="utf-8")
        cls.styles = STYLES_PATH.read_text(encoding="utf-8")

    def rate_limited_mission(self) -> dict:
        return {
            "id": "mission-rate-limited-technical",
            "title": "วิเคราะห์ Technical จาก Indicator",
            "owner": "optimization_agent",
            "toolId": "codex_workspace_analysis",
            "status": "blocked",
            "workStatus": "blocked",
            "phase": "council_round_expired",
            "errorCode": "council_round_deadline_expired",
            "runnerStatus": "local_rate_limited",
            "execution": {
                "lastDeferredReason": "local_rate_limited",
                "deferralCount": 3,
                "processStarted": False,
                "nextAttemptAt": "2026-08-07T21:18:53Z",
            },
            "analysisContext": {
                "kind": "ai_trade_council_vote",
                "roleId": "technical",
                "snapshotId": "a" * 64,
                "roundDeadlineAt": "2026-08-07T20:54:24Z",
                "snapshotArtifact": "private-path-must-not-leak",
            },
            "createdAt": "2026-08-07T20:50:24Z",
            "completedAt": "2026-08-07T21:18:53Z",
        }

    def test_backend_explains_rate_limit_deadline_in_plain_thai(self) -> None:
        blocker = self.bridge._mission_blocker_read_model(
            self.rate_limited_mission()
        )
        self.assertIsNotNone(blocker)
        self.assertEqual(blocker["rootCauseCode"], "local_rate_limited")
        self.assertIn("คิวงาน", blocker["titleTh"])
        self.assertIn("ยังไม่ได้เปิด Codex", blocker["causeTh"])
        self.assertEqual(blocker["deferralCount"], 3)
        self.assertFalse(blocker["processStarted"])
        self.assertTrue(blocker["terminalActionBlocked"])
        self.assertGreaterEqual(len(blocker["resolutionStepsTh"]), 2)

    def test_terminal_timeout_is_not_masked_by_previous_quota_deferral(self) -> None:
        mission = self.rate_limited_mission()
        mission.update(
            {
                "status": "failed",
                "workStatus": "timeout",
                "phase": "auto_guarded_timeout",
                "errorCode": "timeout",
                "runnerStatus": "timeout",
            }
        )
        mission["execution"].update(
            {
                "lastDeferredReason": "quota_unavailable_or_stale",
                "processStarted": True,
            }
        )

        blocker = self.bridge._mission_blocker_read_model(mission)

        self.assertIsNotNone(blocker)
        self.assertEqual(blocker["reasonCode"], "timeout")
        self.assertEqual(blocker["rootCauseCode"], "timeout")
        self.assertTrue(blocker["processStarted"])

    def test_news_consultant_has_bounded_ninety_second_timeout(self) -> None:
        contract = json.loads(COUNCIL_PROMPTS_PATH.read_text(encoding="utf-8"))
        agents = {
            item["roleId"]: item
            for item in contract["agents"]
        }

        self.assertEqual(contract["sharedPolicy"]["qualityGate"]["roundDeadlineSeconds"], 240)
        self.assertEqual(agents["technical"]["timeoutSeconds"], 60)
        self.assertEqual(agents["price_action"]["timeoutSeconds"], 60)
        self.assertEqual(agents["news"]["timeoutSeconds"], 90)

    def test_safe_mission_read_model_contains_blocker_without_private_context(self) -> None:
        item = self.bridge.mission_read_model_item(self.rate_limited_mission())
        self.assertEqual(item["reasonCode"], "council_round_deadline_expired")
        self.assertEqual(item["blocker"]["source"], "backend_mission_truth")
        self.assertNotIn("analysisContext", item)
        self.assertNotIn("snapshotArtifact", str(item))

    def test_completed_mission_has_no_blocker(self) -> None:
        mission = self.rate_limited_mission()
        mission.update({"status": "completed", "workStatus": "completed", "phase": "completed"})
        mission.pop("errorCode", None)
        self.assertIsNone(self.bridge._mission_blocker_read_model(mission))

    def test_council_rate_preflight_checks_all_agents_without_consuming(self) -> None:
        contract = {
            "agents": [
                {
                    "agentId": "optimization_agent",
                    "toolId": "codex_workspace_analysis",
                    "modelTier": "specialist_balanced",
                    "roleId": "technical",
                    "titleTh": "วิเคราะห์ Technical จาก Indicator",
                },
                {
                    "agentId": "backtest_analyst",
                    "toolId": "codex_workspace_analysis",
                    "modelTier": "specialist_balanced",
                    "roleId": "price_action",
                    "titleTh": "วิเคราะห์กราฟเปล่าและ Price Action",
                },
                {
                    "agentId": "codex_mcp_operator",
                    "toolId": "codex_web_research",
                    "modelTier": "specialist_fast",
                    "roleId": "news",
                    "titleTh": "วิเคราะห์ข่าวและสถานการณ์ปัจจุบัน",
                },
            ]
        }

        def fake_check(key, _max_per_hour, cooldown_seconds=0, consume=True):
            self.assertFalse(consume)
            self.assertEqual(cooldown_seconds, 0)
            return (False, 180) if "optimization_agent" in key else (True, 0)

        with mock.patch.object(self.bridge, "check_rate_limit", side_effect=fake_check):
            blockers = self.bridge._ai_trade_council_rate_preflight(contract)

        self.assertEqual(len(blockers), 1)
        self.assertEqual(blockers[0]["agentId"], "optimization_agent")
        self.assertEqual(blockers[0]["retryAfterSeconds"], 180)

    def test_frontend_prioritizes_current_mission_and_real_completion_time(self) -> None:
        views = function_block(self.main, "function signalAgentViews(")
        self.assertIn("signalCurrentConsensusSource(report, run)", views)
        self.assertNotIn("runtime.ensembleAvailable", views)
        self.assertNotIn("live.observedAt", views)
        self.assertIn("mission?.completedAt || mission?.updatedAt", views)
        self.assertIn('const missionWins = ["blocked", "running"].includes(missionState)', views)

    def test_frontend_blocker_has_plain_thai_recovery_and_collapsed_system_details(self) -> None:
        panel = function_block(self.main, "function createSignalAgentBlockerPanel(")
        self.assertIn('issueLabel.textContent = "ติดอะไร"', panel)
        self.assertIn('causeLabel.textContent = "สาเหตุ"', panel)
        self.assertIn('stepsLabel.textContent = "วิธีแก้"', panel)
        self.assertIn('summary.textContent = "ดูรายละเอียดระบบ"', panel)
        self.assertIn("await loadPropReport(AI_TRADE_COUNCIL_PROP_ID)", panel)
        self.assertNotIn("postJson(", panel)

    def test_consensus_source_requires_current_parent_and_snapshot(self) -> None:
        selector = function_block(self.main, "function signalCurrentConsensusSource(")
        self.assertIn("sourceMissionId === parentId", selector)
        self.assertIn("sourceSnapshotId === runSnapshotId", selector)
        self.assertNotIn("!sourceMissionId", selector)

    def test_blocked_agent_card_expands_and_keeps_recovery_content_inside(self) -> None:
        self.assertIn(".signal-council-agent-card.blocked {", self.styles)
        self.assertIn("min-height: max-content;", self.styles)
        self.assertIn("height: max-content;", self.styles)
        self.assertIn(".signal-agent-blocker-row {", self.styles)
        self.assertIn("grid-template-columns: minmax(0, 1fr);", self.styles)


if __name__ == "__main__":
    unittest.main()
