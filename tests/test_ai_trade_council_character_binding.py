import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

COUNCIL_BINDINGS = {
    "optimization_agent": {
        "role_id": "technical",
        "image": "05-optimization-agent-male-static-v001.png",
        "public_name": "Technical Consultant",
        "legacy_name": "Optimization Agent",
    },
    "backtest_analyst": {
        "role_id": "price_action",
        "image": "03-backtest-analyst-male-static-v001.png",
        "public_name": "Price Action Consultant",
        "legacy_name": "Backtest Analyst",
    },
    "codex_mcp_operator": {
        "role_id": "news",
        "image": "07-codex-mcp-operator-male-static-v001.png",
        "public_name": "News Consultant",
        "legacy_name": "Codex MCP Operator",
    },
}


def load_json(relative_path: str):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


class AiTradeCouncilCharacterBindingTests(unittest.TestCase):
    def test_agent_roster_binds_each_council_role_to_an_existing_character(self):
        roster = load_json("contracts/agents/agents.json")
        agents = {agent["id"]: agent for agent in roster["agents"]}

        for agent_id, expected in COUNCIL_BINDINGS.items():
            agent = agents[agent_id]
            self.assertEqual(expected["public_name"], agent["name"])
            self.assertEqual(expected["legacy_name"], agent["legacy_name"])
            self.assertTrue(agent["ai_trade_council"]["enabled"])
            self.assertEqual(expected["role_id"], agent["ai_trade_council"]["role_id"])
            self.assertTrue(agent["chat_profile"]["greeting_th"])
            self.assertTrue(agent["chat_profile"]["answer_scope_th"])

            asset_path = agent["visual"]["static_image"].removeprefix("./")
            self.assertEqual(expected["image"], Path(asset_path).name)
            self.assertTrue((ROOT / asset_path).is_file(), asset_path)

    def test_prompt_order_and_roles_match_the_three_dashboard_characters(self):
        prompts = load_json("contracts/orchestration/ai-trade-council-prompts.json")
        bindings = [
            (agent["agentId"], agent["roleId"])
            for agent in prompts["agents"]
        ]
        self.assertEqual(
            [
                ("optimization_agent", "technical"),
                ("backtest_analyst", "price_action"),
                ("codex_mcp_operator", "news"),
            ],
            bindings,
        )
        for agent in prompts["agents"]:
            expected = COUNCIL_BINDINGS[agent["agentId"]]
            self.assertEqual(expected["public_name"], agent["publicName"])
            self.assertIn(expected["public_name"].split(" (")[0], agent["promptTemplate"])
            self.assertTrue(agent["personaTh"])
            self.assertTrue(agent["chatGreetingTh"])
            self.assertTrue(agent["chatAnswerScopeTh"])

    def test_asset_registry_exposes_dashboard_click_and_status_binding(self):
        registry = load_json(
            "frontend/public/assets/agents/"
            "male-roster-set-a-core-command-operators-v001/registry/asset-registry.json"
        )
        entries = {asset["agent_id"]: asset for asset in registry["assets"]}

        for agent_id, expected in COUNCIL_BINDINGS.items():
            self.assertEqual(expected["public_name"], entries[agent_id]["name"])
            self.assertEqual(expected["legacy_name"], entries[agent_id]["legacy_name"])
            assignment = entries[agent_id]["ai_trade_council_assignment"]
            self.assertEqual(expected["role_id"], assignment["role_id"])
            self.assertEqual("left_analytics_console", assignment["dashboard_surface"])
            self.assertEqual("open_agent_chat", assignment["click_action"])
            self.assertEqual("backend_council_mission", assignment["status_source"])

    def test_frontend_uses_real_agent_dialog_and_backend_work_state(self):
        source = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        styles = (ROOT / "frontend/src/app/styles.css").read_text(encoding="utf-8")

        for agent_id in COUNCIL_BINDINGS:
            self.assertIn(f'"{agent_id}"', source)
        for expected in COUNCIL_BINDINGS.values():
            self.assertIn(expected["public_name"], source)
            self.assertNotIn(f'name: "{expected["legacy_name"]}"', source)
        self.assertIn("AI_TRADE_COUNCIL_PUBLIC_NAMES", source)
        self.assertIn("AI_TRADE_COUNCIL_LEGACY_NAMES", source)
        self.assertIn("agent.legacyName?.toLowerCase() === ownerText", source)
        self.assertIn("function createSignalAgentSprite", source)
        self.assertIn("function signalAgentWorkStatus", source)
        self.assertIn("openAgentDialog(view.agentId)", source)
        self.assertIn("คุยและถามเหตุผล", source)
        self.assertIn(".signal-agent-sprite-image", styles)
        self.assertIn('[data-work-state="working"]', styles)
        self.assertIn("@media (max-width: 900px)", styles)
        self.assertIn("max-width: 190px", styles)
        self.assertIn("overflow-wrap: anywhere", styles)


if __name__ == "__main__":
    unittest.main()
