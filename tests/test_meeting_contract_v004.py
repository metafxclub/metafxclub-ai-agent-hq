from __future__ import annotations

import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEETING_PATH = PROJECT_ROOT / "contracts" / "meetings" / "meeting-contract.json"
BRIDGE_PATH = PROJECT_ROOT / "contracts" / "bridge" / "bridge-contract.json"
ORCHESTRATION_PATH = (
    PROJECT_ROOT / "contracts" / "orchestration" / "orchestration-contract.json"
)

MEETING_ENDPOINTS = {
    "GET /api/meetings/sessions",
    "GET /api/meetings/sessions/{id}",
    "POST /api/meetings/sessions",
    "POST /api/meetings/sessions/{id}/messages",
    "POST /api/meetings/sessions/{id}/proposal",
    "POST /api/meetings/sessions/{id}/approve",
    "POST /api/meetings/sessions/{id}/reject",
}


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain an object")
    return value


class MeetingContractV004Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.meeting = load_json(MEETING_PATH)
        cls.bridge = load_json(BRIDGE_PATH)
        cls.orchestration = load_json(ORCHESTRATION_PATH)

    def test_v004_exposes_exact_session_endpoints_across_contracts(self) -> None:
        self.assertEqual(self.meeting["version"], "meeting-contract-v004")
        self.assertEqual(set(self.meeting["endpoints"]), MEETING_ENDPOINTS)
        bridge_meeting_endpoints = {
            key
            for key in self.bridge["endpoints"]
            if "/api/meetings/" in key
        }
        self.assertEqual(bridge_meeting_endpoints, MEETING_ENDPOINTS)
        self.assertEqual(
            set(self.orchestration["interactiveMeetings"]["endpoints"]),
            MEETING_ENDPOINTS,
        )
        self.assertEqual(
            self.orchestration["interactiveMeetings"]["contractVersion"],
            "meeting-contract-v004",
        )

    def test_discussion_is_autonomous_but_tool_workspace_and_task_free(self) -> None:
        guard = self.meeting["discussion_guardrails"]
        self.assertTrue(guard["autonomousAgentDiscussion"])
        for key in (
            "toolsEnabled",
            "shellEnabled",
            "browserEnabled",
            "computerUseEnabled",
            "externalAppsEnabled",
            "projectWorkspaceExposed",
            "workspaceReadEnabled",
            "workspaceWriteEnabled",
            "taskCreationEnabled",
            "crossAgentToolHandoffEnabled",
            "productImplementationEnabled",
            "approvalClaimsFromTranscriptTrusted",
        ):
            self.assertFalse(guard[key], key)
        self.assertEqual(guard["discussionMissionExecutionMode"], "discussion_only")
        self.assertTrue(guard["discussionMissionBackendConstructorOnly"])
        self.assertFalse(guard["agendaRiskWordsGrantImplementationAuthority"])
        collaboration = self.bridge["runner_mode"]["agent_collaboration"]
        self.assertFalse(collaboration["toolsEnabled"])
        self.assertFalse(collaboration["shellEnabled"])
        self.assertFalse(collaboration["projectWorkspaceExposed"])
        self.assertFalse(collaboration["workspaceReadEnabled"])
        self.assertFalse(collaboration["taskCreationEnabled"])
        self.assertFalse(collaboration["productImplementationEnabled"])

    def test_contribution_schema_has_role_proposal_risk_checks_and_manager_decision(self) -> None:
        contribution = self.meeting["contribution_schema"]
        self.assertEqual(
            set(contribution),
            {
                "schemaVersion",
                "speaker",
                "proposal",
                "risks",
                "acceptanceChecks",
                "managerDecision",
            },
        )
        self.assertEqual(
            set(contribution["speaker"]),
            {"agentId", "agentName", "role"},
        )
        self.assertIn("accepted", contribution["managerDecision"]["status"])
        limits = self.meeting["limits"]
        self.assertEqual(limits["messageMaxChars"], 1600)
        self.assertEqual(limits["agentTurnTimeoutSeconds"], 90)
        self.assertEqual(limits["agentTurnOutputMaxChars"], 1800)
        self.assertEqual(limits["riskMaxItems"], 3)
        self.assertEqual(limits["acceptanceCheckMaxItems"], 4)

        turn = self.meeting["turn_schema"]
        self.assertIn("speakerRole", turn)
        self.assertIn("proposal", turn)
        self.assertIn("risks", turn)
        self.assertIn("acceptanceChecks", turn)
        self.assertIn("managerDecision", turn)

    def test_session_and_requests_match_backend_read_model_names(self) -> None:
        session = self.meeting["session_read_model"]
        self.assertEqual(
            set(session["status"].split("|")),
            {
                "idle",
                "running",
                "awaiting_user",
                "proposed",
                "approved",
                "rejected",
                "blocked",
                "failed",
            },
        )
        self.assertIn("discussionMissionIds", session)
        self.assertIn("developmentGoal", session)
        self.assertIn("aiTurnsPerRound", session)
        self.assertEqual(session["maxTurnsPerRound"], 8)
        self.assertEqual(session["maxParticipantAgents"], 4)
        self.assertIn("implementationMissionId", session)
        self.assertIn("readyToExecute", session)
        self.assertEqual(
            set(self.meeting["approval_request_schema"]),
            {"confirmMeetingId", "confirmProposalDigest", "note", "idempotencyKey"},
        )

        interactive = self.orchestration["interactiveMeetings"]
        self.assertEqual(interactive["discussionMissionToolId"], "agent_collaboration")
        self.assertEqual(interactive["discussionMissionExecutionMode"], "discussion_only")
        self.assertTrue(interactive["discussionMissionBackendConstructorOnly"])
        self.assertFalse(interactive["discussionMissionMayImplementProduct"])
        self.assertEqual(
            interactive["approvalRequestFields"],
            ["confirmMeetingId", "confirmProposalDigest", "note", "idempotencyKey"],
        )

    def test_chat_first_create_requires_goal_and_exact_bounded_ai_turn_count(self) -> None:
        request = self.meeting["create_session_request_schema"]
        self.assertEqual(
            request["requiredFields"],
            ["agenda", "developmentGoal", "aiTurnsPerRound", "idempotencyKey"],
        )
        self.assertFalse(request["agenda"]["emptyAllowed"])
        self.assertEqual(
            (request["agenda"]["minChars"], request["agenda"]["maxChars"]),
            (8, 2400),
        )
        self.assertFalse(request["developmentGoal"]["emptyAllowed"])
        self.assertEqual(
            (
                request["developmentGoal"]["minChars"],
                request["developmentGoal"]["maxChars"],
            ),
            (8, 2400),
        )
        self.assertEqual(
            (
                request["aiTurnsPerRound"]["minimum"],
                request["aiTurnsPerRound"]["maximum"],
            ),
            (2, 8),
        )
        self.assertTrue(request["aiTurnsPerRound"]["includesManagerFinalTurn"])
        self.assertTrue(
            request["aiTurnsPerRound"][
                "minimumMustCoverEverySelectedParticipantIncludingManager"
            ]
        )
        self.assertEqual(request["participantAgentIds"]["specialistMaximum"], 3)
        self.assertTrue(request["participantAgentIds"]["managerAppendedByBackend"])
        self.assertTrue(request["currentUiMustSendEveryRequiredField"])

    def test_user_interjection_starts_one_exact_next_ai_batch_with_manager_final(self) -> None:
        workflow = self.meeting["chat_first_workflow"]
        self.assertTrue(workflow["userLeadsEveryBatch"])
        self.assertTrue(workflow["userInterjectionStartsNextBatch"])
        self.assertFalse(workflow["userInterjectionMayJoinRunningBatch"])
        self.assertFalse(workflow["userInterjectionCountsAsAiTurn"])
        self.assertFalse(workflow["automaticContinuousAiLoop"])
        self.assertTrue(workflow["singleBatchInflightPerSession"])
        self.assertTrue(workflow["newSessionAllowedWhileAnotherSessionAwaitsUser"])
        self.assertEqual(workflow["maxBatchesPerSession"], 3)
        self.assertEqual(workflow["completedBatchReturnsToStatus"], "awaiting_user")

        message = self.meeting["message_request_schema"]
        self.assertEqual(message["requiredFields"], ["message", "idempotencyKey"])
        self.assertEqual(message["message"]["maxChars"], 1600)
        self.assertFalse(message["aiTurnsPerRoundOverrideAllowed"])
        self.assertEqual(message["batchCountSource"], "session.aiTurnsPerRound")

        batch = self.meeting["ai_turn_batch_schema"]
        self.assertEqual((batch["minimumAiTurns"], batch["maximumAiTurns"]), (2, 8))
        self.assertTrue(batch["selectedAiTurnCountIsExact"])
        self.assertTrue(batch["completedBatchAiTurnCountMustEqualConfiguredCount"])
        self.assertFalse(batch["partialBatchMayReportCompleted"])
        self.assertEqual(batch["participantPool"]["specialistMaximum"], 3)
        self.assertEqual(batch["participantPool"]["maximumDistinctAgents"], 4)
        self.assertEqual(batch["managerTurnCount"], 1)
        self.assertEqual(batch["managerTurnPosition"], "final")
        self.assertTrue(batch["managerFinalRequired"])
        self.assertFalse(batch["managerMaySpeakBeforeFinalSlot"])
        self.assertTrue(batch["userTurnExcludedFromAiCount"])
        self.assertIn("cycling deterministically", batch["specialistSelectionRule"])

    def test_chat_first_legacy_defaults_are_bounded_and_never_grant_authority(self) -> None:
        legacy = self.meeting["chat_first_legacy_compatibility"]
        self.assertIn("pre-chat-first stored sessions", legacy["scope"])
        self.assertIn("current UI must send explicit fields", legacy["scope"])
        self.assertIn("agenda", legacy["missingDevelopmentGoalDefault"])
        self.assertIn("two through four", legacy["missingAiTurnsPerRoundDefault"])
        self.assertTrue(legacy["normalizedReadModelAlwaysEmitsDevelopmentGoal"])
        self.assertTrue(legacy["normalizedReadModelAlwaysEmitsAiTurnsPerRound"])
        self.assertFalse(legacy["explicitValidValuesMayBeOverriddenByDefaults"])
        self.assertFalse(legacy["legacyDefaultMayGrantImplementationAuthority"])

    def test_chat_first_rate_limit_dependency_is_explicit_and_atomic(self) -> None:
        rate = self.meeting["rate_limit_integration"]
        self.assertEqual(rate["freshQuotaRemainingPercentMustBeStrictlyGreaterThan"], 15)
        self.assertTrue(rate["oneAiTurnConsumesOneModelInvocation"])
        self.assertTrue(rate["batchAdmissionMustReserveExactAiTurnCapacityBeforeFirstTurn"])
        self.assertFalse(rate["partialRateLimitAdmissionAllowed"])
        self.assertEqual(
            rate["currentSharedLimitField"],
            "costRateGuard.collaborationTurnsPerHour",
        )
        self.assertEqual(
            rate["dedicatedInteractiveLimitField"],
            "costRateGuard.interactiveMeetingTurnsPerHour",
        )
        self.assertEqual(
            self.orchestration["costRateGuard"]["interactiveMeetingTurnsPerHour"],
            24,
        )
        self.assertIn("configured_to_24", rate["dedicatedInteractiveLimitFieldStatus"])
        self.assertFalse(rate["sharedLimitFallbackMayClaimDedicatedCapacity"])

    def test_proposal_does_not_create_mission_and_approval_creates_separate_unexecuted_mission(self) -> None:
        invariant = self.meeting["approval_invariants"]
        self.assertTrue(invariant["explicitFreshUserEventRequired"])
        self.assertTrue(invariant["meetingIdMustMatchPath"])
        self.assertTrue(invariant["proposalDigestMustMatchCurrentProposal"])
        self.assertFalse(invariant["proposalCreatesMission"])
        self.assertTrue(invariant["approvalCreatesSeparateMission"])
        self.assertFalse(invariant["approvalExecutesMission"])
        self.assertFalse(invariant["rejectCreatesMission"])
        self.assertFalse(invariant["automaticApproval"])
        self.assertFalse(invariant["agentMayApprove"])

        orchestration = self.orchestration["interactiveMeetings"]
        self.assertFalse(orchestration["proposalCreatesMission"])
        self.assertTrue(orchestration["approvalCreatesSeparateMission"])
        self.assertFalse(orchestration["approvalExecutesMission"])
        self.assertEqual(
            orchestration["implementationMissionStateAfterApprove"],
            "waiting_approval with approval.state=approved and readyToExecute=true",
        )
        self.assertEqual(
            orchestration["implementationExecutionEndpoint"],
            "POST /api/missions/:id/execute",
        )
        self.assertFalse(orchestration["automaticWorkerExecution"])

    def test_digest_and_approval_are_exact_current_single_use_and_mutation_invalidates(self) -> None:
        digest = self.meeting["proposal_digest"]
        self.assertEqual(digest["algorithm"], "sha256")
        self.assertEqual(digest["encoding"], "lowercase hexadecimal")
        self.assertIn("meetingId", digest["binds"])
        self.assertIn("managerTurnId", digest["binds"])
        self.assertIn("text", digest["binds"])
        self.assertIn("structuredDecision.acceptanceChecks", digest["binds"])
        self.assertIn("structuredDecision.managerDecision", digest["binds"])
        self.assertIn("agenda", digest["binds"])
        self.assertIn("developmentGoal", digest["binds"])
        self.assertIn("aiTurnsPerRound", digest["binds"])
        self.assertIn("interactive-meeting-proposal-v2", digest["canonicalization"])
        self.assertIn("invalidates", digest["mutationRule"])
        self.assertIn("never reusable", digest["reuseRule"])

        invariant = self.meeting["approval_invariants"]
        self.assertTrue(invariant["approvalSingleUse"])
        self.assertTrue(invariant["approvalInvalidAfterProposalChange"])
        self.assertFalse(invariant["frontendBooleanAloneTrusted"])

    def test_implementation_binding_and_mission_digest_use_meeting_id_consistently(self) -> None:
        binding = self.meeting["implementation_mission_binding"]
        self.assertEqual(
            binding["schemaVersion"],
            "interactive-meeting-approval-binding-v1",
        )
        self.assertEqual(
            binding["requiredFields"],
            [
                "schemaVersion",
                "meetingId",
                "proposalDigest",
                "proposalTurnId",
            ],
        )
        self.assertNotIn("sessionId", binding["requiredFields"])
        self.assertEqual(binding["executionMode"], "approved_workspace")
        self.assertEqual(
            binding["runnerRequiredArguments"],
            ["--approval-meeting-id", "--approval-proposal-digest"],
        )
        self.assertEqual(
            binding["executionTrigger"].split(" body", 1)[0],
            "A fresh explicit POST /api/missions/:id/execute",
        )

        digest_fields = set(self.orchestration["approvalGate"]["missionDigestFields"])
        required_digest_fields = {
            "meetingApprovalBinding.schemaVersion",
            "meetingApprovalBinding.meetingId",
            "meetingApprovalBinding.proposalDigest",
            "meetingApprovalBinding.proposalTurnId",
            "meetingImplementationProposal",
        }
        self.assertTrue(required_digest_fields.issubset(digest_fields))
        self.assertNotIn("meetingApprovalBinding.sessionId", digest_fields)
        required_approved_workspace_markers = {
            *required_digest_fields,
            "meetingImplementationPrompt",
        }
        self.assertTrue(
            required_approved_workspace_markers.issubset(
                set(self.orchestration["missionWorker"]["requiredApprovedWorkspaceMarkers"])
            )
        )

    def test_approved_workspace_is_bounded_and_forbids_external_effects(self) -> None:
        guard = self.meeting["implementation_guardrails"]
        self.assertEqual(
            guard["writeRoots"],
            [
                "workspace",
                "frontend",
                "backend",
                "runner",
                "contracts",
                "tests",
                "docs",
                "assets-source",
            ],
        )
        self.assertEqual(
            guard["deniedRuntimeAndRepositoryRoots"],
            [
                "data/runtime",
                "scripts",
                "installer",
                ".git",
            ],
        )
        self.assertTrue(guard["projectCodeWritable"])
        self.assertTrue(guard["controlPlaneWritable"])
        self.assertFalse(guard["runtimeStateWritable"])
        self.assertIn("digest-bound", guard["writeBoundaryEnforcement"])
        self.assertIn("not represented as a separate OS read ACL", guard["readBoundaryEnforcement"])
        self.assertIn("not a separate filesystem delete ACL", guard["deleteRenameEnforcement"])
        self.assertFalse(guard["automaticDeploy"])
        self.assertFalse(guard["automaticExternalMessaging"])
        self.assertFalse(guard["automaticLiveTrading"])
        forbidden = " ".join(guard["forbidden"]).lower()
        for phrase in ("web search", "external messaging", "live trading", "mt4/mt5", "secret"):
            self.assertIn(phrase, forbidden)

        approved = self.bridge["runner_mode"]["codex_cli"]["approvedWorkspace"]
        self.assertEqual(approved["executionMode"], "approved_workspace")
        self.assertEqual(
            approved["writeRoots"],
            [f"./{label}/" for label in guard["writeRoots"]],
        )
        self.assertEqual(
            approved["deniedRoots"],
            [f"./{label}/" for label in guard["deniedRuntimeAndRepositoryRoots"]],
        )
        self.assertTrue(approved["projectCodeWritable"])
        self.assertTrue(approved["controlPlaneWritable"])
        self.assertFalse(approved["runtimeStateWritable"])
        self.assertFalse(approved["webSearchEnabled"])
        self.assertFalse(approved["approvalInlineExecution"])
        self.assertEqual(
            approved["bindingSchemaVersion"],
            "interactive-meeting-approval-binding-v1",
        )
        self.assertEqual(
            approved["executionEndpoint"],
            "POST /api/missions/:id/execute",
        )
        self.assertFalse(approved["automaticWorkerExecution"])
        self.assertEqual(approved["writeBoundaryEnforcement"], "OS workspace-write sandbox")
        self.assertIn("no separate OS read ACL", approved["readBoundaryEnforcement"])
        self.assertEqual(
            approved["requiredCliBindings"],
            ["--approval-meeting-id", "--approval-proposal-digest"],
        )
        worker = self.orchestration["missionWorker"]
        self.assertEqual(worker["approvedWorkspaceWritableRoots"], guard["writeRoots"])
        self.assertEqual(
            worker["approvedWorkspaceDeniedRoots"],
            guard["deniedRuntimeAndRepositoryRoots"],
        )
        self.assertTrue(worker["approvedWorkspaceProjectCodeWritable"])
        self.assertTrue(worker["approvedWorkspaceControlPlaneWritable"])
        self.assertFalse(worker["approvedWorkspaceRuntimeStateWritable"])


if __name__ == "__main__":
    unittest.main()
