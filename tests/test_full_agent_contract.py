from __future__ import annotations

import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FULL_AGENT_CONTRACT_PATH = (
    PROJECT_ROOT / "contracts" / "agents" / "full-agent-runtime-contract.json"
)
BRIDGE_CONTRACT_PATH = PROJECT_ROOT / "contracts" / "bridge" / "bridge-contract.json"


class FullAgentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(FULL_AGENT_CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.bridge_contract = json.loads(BRIDGE_CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_private_transport_and_secret_boundary_are_explicit(self) -> None:
        transport = self.contract["transport"]
        self.assertEqual(transport["bridgeToCodex"], "Codex app-server over private stdio")
        self.assertFalse(transport["publicNetworkListenerAllowed"])
        self.assertFalse(transport["frontendCredentialsAllowed"])
        self.assertEqual(transport["mutationContentType"], "application/json")
        self.assertTrue(transport["mutationOriginRequired"])
        self.assertTrue(transport["mutationOriginMustMatchRequestAuthority"])
        self.assertFalse(transport["localProcessAuthenticationClaimed"])

    def test_sdk_auto_approval_and_danger_full_access_are_forbidden(self) -> None:
        policy = self.contract["approvalPolicy"]
        self.assertFalse(policy["sdkDefaultApprovalHandlerAllowed"])
        self.assertEqual(policy["commandExecutionDefaultDecision"], "decline")
        self.assertEqual(policy["fileChangeDefaultDecision"], "decline")
        self.assertEqual(policy["permissionEscalationDefault"], "grant_nothing")
        self.assertFalse(policy["dangerFullAccessAllowed"])
        self.assertNotEqual(self.contract["modes"]["workspace"]["sandbox"], "danger-full-access")

    def test_tool_modes_fail_closed_until_approval_adapter_exists(self) -> None:
        for mode in ("workspace", "computer", "full"):
            with self.subTest(mode=mode):
                self.assertFalse(self.contract["modes"][mode]["defaultReady"])
                self.assertTrue(self.contract["modes"][mode]["approvalRequired"])
                if mode != "workspace":
                    self.assertFalse(self.contract["modes"][mode]["silentApprovalAllowed"])

    def test_every_real_turn_requires_operational_lineage(self) -> None:
        evidence = self.contract["executionEvidence"]
        self.assertTrue(evidence["missionRequired"])
        self.assertTrue(evidence["ownerAgentRequired"])
        self.assertTrue(evidence["auditRequired"])
        self.assertTrue(evidence["reportRequired"])
        self.assertEqual(
            evidence["successTerminalProof"],
            "turn/completed notification OR authoritative thread/read reconciliation",
        )
        self.assertNotIn("successRequiresTurnCompletedNotification", evidence)
        self.assertTrue(evidence["successRequiresTurnTerminalProof"])
        self.assertFalse(evidence["interruptAcknowledgementCountsAsTermination"])
        self.assertTrue(evidence["unconfirmedTimeoutRequiresGatewayQuarantine"])
        self.assertFalse(evidence["timeoutMayMasqueradeAsSuccess"])

    def test_bridge_contract_publishes_the_same_endpoint_set(self) -> None:
        bridge_endpoints = self.bridge_contract["endpoints"]
        for endpoint in self.contract["endpoints"]:
            with self.subTest(endpoint=endpoint):
                self.assertIn(endpoint, bridge_endpoints)

    def test_thread_mutations_bind_revision_and_archive_is_reversible(self) -> None:
        policy = self.contract["threadMutationPolicy"]
        self.assertTrue(policy["settingsExpectedRevisionRequired"])
        self.assertTrue(policy["archiveExpectedRevisionRequired"])
        self.assertTrue(policy["archiveIsReversible"])
        self.assertTrue(policy["archivedHistoryListableWithIncludeArchived"])

        endpoints = self.contract["endpoints"]
        settings = endpoints["POST /api/agent-runtime/threads/{threadId}/settings"]
        archive = endpoints["POST /api/agent-runtime/threads/{threadId}/archive"]
        listing = endpoints["GET /api/agent-runtime/threads?agentId={agentId}"]
        self.assertIn("expectedRevision", settings)
        self.assertIn("expectedRevision", archive)
        self.assertIn("archived true or false", archive)
        self.assertIn("includeArchived=true", listing)

    def test_http_projection_preserves_runtime_bounded_content(self) -> None:
        projection = self.contract["httpProjection"]
        self.assertEqual(projection["maximumStringCharacters"], 32768)
        self.assertEqual(projection["assistantReplyMaximumCharacters"], 32000)
        self.assertFalse(
            projection["validRuntimeContentMayBeSilentlyClippedAtGenericDashboardLimit"]
        )
        self.assertTrue(projection["fullAgentSerializerIsEndpointSpecific"])

    def test_failed_live_sentinel_keeps_workspace_fail_closed(self) -> None:
        activation = self.contract["workspaceActivation"]
        self.assertFalse(activation["ready"])
        self.assertEqual(
            activation["liveSentinelStatus"],
            "failed_unapproved_write",
        )
        self.assertFalse(activation["failedSentinelMayBeOverriddenByFrontend"])
        self.assertFalse(activation["wholeWorkspacePreTurnGrantSupported"])


if __name__ == "__main__":
    unittest.main()
