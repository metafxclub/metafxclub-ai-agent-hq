from __future__ import annotations

import importlib.util
import http.client
import json
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "interactive_meeting_backend_bridge",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InteractiveMeetingBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.stack = ExitStack()
        for name, path in {
            "RUNTIME_DIR": root / "runtime",
            "MISSIONS_PATH": root / "runtime" / "missions.json",
            "AUDIT_PATH": root / "runtime" / "audit.jsonl",
            "OPERATOR_MODE_PATH": root / "runtime" / "operator-mode.json",
            "INTERACTIVE_MEETING_SESSIONS_PATH": root / "runtime" / "meeting-sessions.json",
            "MEMORY_DIR": root / "memory",
            "MEETING_TRANSCRIPTS_PATH": root / "memory" / "meetings.jsonl",
            "RUNTIME_REPORTS_DIR": root / "runtime" / "reports",
        }.items():
            self.stack.enter_context(mock.patch.object(self.bridge, name, path))
        self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "INTERACTIVE_MEETING_SESSIONS_LOCK",
                threading.RLock(),
            )
        )
        self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "INTERACTIVE_MEETING_ROUND_LOCK",
                threading.Lock(),
            )
        )
        self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "REAL_RUN_SEMAPHORE",
                threading.BoundedSemaphore(1),
            )
        )
        self.stack.enter_context(
            mock.patch.object(self.bridge, "INTERACTIVE_MEETING_THREADS", {})
        )
        self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "load_operator_mode_record",
                return_value={"mode": "auto_guarded"},
            )
        )
        self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "_collaboration_quota_gate",
                return_value={"allowed": True, "reason": "allowed"},
            )
        )
        self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "check_rate_limit",
                return_value=(True, 0),
            )
        )
        self.reserve_slots = self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "reserve_rate_limit_slots",
                side_effect=lambda key, limit, slot_count, *, consume: (
                    True,
                    0,
                    [float(index + 1) for index in range(slot_count)] if consume else [],
                ),
            )
        )
        self.safe_command = self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "run_safe_command",
                side_effect=self._collaboration_command,
            )
        )
        self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "_interactive_meeting_start_round_thread",
                side_effect=lambda session_id, round_id: self.bridge._run_interactive_meeting_round(
                    session_id,
                    round_id,
                ),
            )
        )
        self.bridge._invalidate_missions_read_cache()
        self.bridge.ensure_runtime_dir()
        self.bridge.ensure_memory_dir()
        self.bridge.ensure_interactive_meeting_sessions_store()

    def tearDown(self) -> None:
        if self.bridge.INTERACTIVE_MEETING_ROUND_LOCK.locked():
            self.bridge.INTERACTIVE_MEETING_ROUND_LOCK.release()
        self.bridge._invalidate_missions_read_cache()
        self.stack.close()
        self.temp.cleanup()

    def _contribution(self, agent_id: str) -> dict:
        is_manager = agent_id == "manager"
        return {
            "schemaVersion": "meeting-contribution-v1",
            "speaker": {
                "agentId": agent_id,
                "agentName": "Manager" if is_manager else "Specialist",
                "role": "manager" if is_manager else "specialist",
            },
            "proposal": (
                "Implement the selected bounded dashboard improvement"
                if is_manager
                else "Add one bounded dashboard status panel"
            ),
            "risks": ["Keep existing API behavior stable"],
            "acceptanceChecks": ["Focused tests pass", "No external side effect"],
            "managerDecision": {
                "status": "accepted" if is_manager else "not_applicable",
                "summary": "Approve the bounded dashboard status improvement" if is_manager else "",
            },
        }

    def _collaboration_command(self, command, **kwargs):
        command = [str(item) for item in command]
        agent_id = command[command.index("--agent-id") + 1]
        contribution = self._contribution(agent_id)
        payload = {
            "ok": True,
            "kind": "agent_collaboration_turn",
            "status": "completed",
            "finalMessage": contribution["proposal"],
            "meetingContribution": contribution,
            "taskCreationEnabled": False,
            "guardrails": {
                "toolsEnabled": False,
                "computerUseEnabled": False,
                "projectWorkspaceExposed": False,
                "taskCreationEnabled": False,
            },
            "durationMs": 5,
            "quotaConsumption": "recorded",
        }
        return {
            "ok": True,
            "exitCode": 0,
            "durationMs": 5,
            "output": json.dumps(payload),
            "processStarted": True,
            "processTreeTerminated": False,
        }

    def create_completed_first_round(self, key: str = "meeting-create-1") -> dict:
        result = self.bridge.create_interactive_meeting_session({
            "agenda": "Improve the shared AI meeting dashboard safely",
            "developmentGoal": "Deliver one verified shared-room product improvement",
            "participantAgentIds": ["ea_developer"],
            "aiTurnsPerRound": 2,
            "idempotencyKey": key,
        })
        self.assertTrue(result["ok"])
        return result

    def test_create_runs_bounded_round_manager_last_and_idempotently_replays(self) -> None:
        result = self.create_completed_first_round()
        session = self.bridge.interactive_meeting_session_read_model(
            result["session"]["id"]
        )["session"]
        self.assertEqual(session["status"], "awaiting_user")
        self.assertEqual(session["roundCount"], 1)
        self.assertEqual(len(session["turns"]), 2)
        self.assertEqual(session["turns"][-1]["speakerAgentId"], "manager")
        self.assertEqual(session["turns"][0]["speakerRole"], "MT4/MT5 EA Developer")
        self.assertEqual(session["turns"][-1]["speakerRole"], "Manager Agent")
        self.assertEqual(session["turns"][-1]["intent"], "decision")
        self.assertEqual(session["managerDecision"]["decision"]["status"], "accepted")
        self.assertEqual(session["progress"]["currentTurn"], 2)
        self.assertEqual(session["progress"]["totalTurns"], 2)
        self.assertEqual(session["aiTurnsPerRound"], 2)
        self.assertEqual(
            session["developmentGoal"],
            "Deliver one verified shared-room product improvement",
        )
        mission = self.bridge.find_mission(session["discussionMissionIds"][0])
        self.assertEqual(mission["status"], "completed")
        replay = self.bridge.create_interactive_meeting_session({
            "agenda": "Improve the shared AI meeting dashboard safely",
            "developmentGoal": "Deliver one verified shared-room product improvement",
            "participantAgentIds": ["ea_developer"],
            "aiTurnsPerRound": 2,
            "idempotencyKey": "meeting-create-1",
        })
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["session"]["id"], session["id"])
        self.assertEqual(len(self.bridge.interactive_meeting_sessions_read_model()["sessions"]), 1)

    def test_user_controls_exact_eight_turn_batches_with_rotating_specialists_and_manager_last(self) -> None:
        agenda = "Review the real shared AI chat flow"
        development_goal = "Make every selected Agent discuss one verifiable product improvement"
        created = self.bridge.create_interactive_meeting_session({
            "agenda": agenda,
            "developmentGoal": development_goal,
            "participantAgentIds": [
                "ea_developer",
                "backtest_analyst",
                "risk_guard",
            ],
            "aiTurnsPerRound": 8,
            "idempotencyKey": "exact-eight-round-one",
        })
        session_id = created["session"]["id"]
        first = self.bridge.interactive_meeting_session_read_model(session_id)["session"]
        first_turns = [item for item in first["turns"] if item.get("role") == "agent"]
        self.assertEqual(len(first_turns), 8)
        self.assertEqual(
            [item["speakerAgentId"] for item in first_turns],
            [
                "ea_developer",
                "backtest_analyst",
                "risk_guard",
                "ea_developer",
                "backtest_analyst",
                "risk_guard",
                "ea_developer",
                "manager",
            ],
        )
        self.assertEqual(first["progress"], {
            "currentRound": 1,
            "totalRounds": 3,
            "currentTurn": 8,
            "totalTurns": 8,
        })
        self.assertEqual(first["status"], "awaiting_user")

        self.bridge.append_interactive_meeting_user_message(session_id, {
            "message": "Please add a measurable acceptance criterion before concluding.",
            "idempotencyKey": "exact-eight-round-two",
        })
        second = self.bridge.interactive_meeting_session_read_model(session_id)["session"]
        second_turns = [
            item
            for item in second["turns"]
            if item.get("role") == "agent" and item.get("roundNumber") == 2
        ]
        self.assertEqual(len(second_turns), 8)
        self.assertEqual(
            [item["speakerAgentId"] for item in second_turns],
            [
                "backtest_analyst",
                "risk_guard",
                "ea_developer",
                "backtest_analyst",
                "risk_guard",
                "ea_developer",
                "backtest_analyst",
                "manager",
            ],
        )
        self.assertEqual(second_turns[-1]["intent"], "decision")
        round_two_requests = [
            json.loads(item.kwargs["input_text"])["message"]
            for item in self.safe_command.call_args_list[-8:]
        ]
        self.assertTrue(all("Review the real shared AI chat flow" in item for item in round_two_requests))
        self.assertTrue(all("Make every selected Agent" in item for item in round_two_requests))
        self.assertTrue(any("measurable acceptance criterion" in item for item in round_two_requests))

    def test_topic_goal_and_turn_count_are_required_and_strictly_bounded(self) -> None:
        base = {
            "agenda": "Discuss one bounded product improvement",
            "developmentGoal": "Deliver one verified product improvement",
            "participantAgentIds": ["ea_developer"],
            "aiTurnsPerRound": 2,
        }
        invalid_payloads = [
            ({key: value for key, value in base.items() if key != "developmentGoal"}, "developmentGoal"),
            ({key: value for key, value in base.items() if key != "aiTurnsPerRound"}, "aiTurnsPerRound"),
            ({**base, "aiTurnsPerRound": True}, "aiTurnsPerRound"),
            ({**base, "aiTurnsPerRound": 1}, "aiTurnsPerRound"),
            ({**base, "aiTurnsPerRound": 9}, "aiTurnsPerRound"),
            ({
                **base,
                "participantAgentIds": ["ea_developer", "backtest_analyst"],
                "aiTurnsPerRound": 2,
            }, "every selected Agent"),
        ]
        for index, (payload, expected_message) in enumerate(invalid_payloads):
            payload["idempotencyKey"] = f"invalid-user-control-{index}"
            with self.subTest(index=index):
                with self.assertRaises(self.bridge.RequestError) as error:
                    self.bridge.create_interactive_meeting_session(payload)
                self.assertEqual(error.exception.status, 422)
                self.assertIn(expected_message, str(error.exception))
        self.assertEqual(self.bridge.load_missions(), [])

    def test_whole_turn_batch_is_reserved_before_any_agent_runs(self) -> None:
        reservations = []

        def reserve(key, limit, slot_count, *, consume):
            reservations.append((key, limit, slot_count, consume))
            if consume:
                return False, 900, []
            return True, 0, []

        with mock.patch.object(
            self.bridge,
            "reserve_rate_limit_slots",
            side_effect=reserve,
        ):
            created = self.bridge.create_interactive_meeting_session({
                "agenda": "Check atomic AI turn reservation behavior",
                "developmentGoal": "Prevent a meeting batch from stopping halfway on hourly capacity",
                "participantAgentIds": ["ea_developer"],
                "aiTurnsPerRound": 6,
                "idempotencyKey": "atomic-turn-reservation",
            })
        session = self.bridge.interactive_meeting_session_read_model(
            created["session"]["id"]
        )["session"]
        self.assertEqual(session["status"], "blocked")
        self.assertEqual(session["failureReason"], "hourly_turn_batch_capacity")
        self.assertEqual(session["turns"], [])
        self.assertEqual(self.safe_command.call_count, 0)
        self.assertEqual([item[2:] for item in reservations], [(6, False), (6, True)])

    def test_early_runner_failure_releases_only_unattempted_turn_reservations(self) -> None:
        attempts = 0

        def command(command, **kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 2:
                return {
                    "ok": True,
                    "exitCode": 0,
                    "durationMs": 5,
                    "output": json.dumps({
                        "ok": False,
                        "kind": "agent_collaboration_turn",
                        "status": "provider_error",
                        "message": "Injected turn failure",
                        "guardrails": {
                            "toolsEnabled": False,
                            "computerUseEnabled": False,
                            "projectWorkspaceExposed": False,
                            "taskCreationEnabled": False,
                        },
                    }),
                    "processStarted": True,
                    "processTreeTerminated": False,
                }
            return self._collaboration_command(command, **kwargs)

        def reserve(key, limit, slot_count, *, consume):
            return True, 0, ([10.0, 11.0, 12.0, 13.0] if consume else [])

        with mock.patch.object(
            self.bridge,
            "reserve_rate_limit_slots",
            side_effect=reserve,
        ), mock.patch.object(
            self.bridge,
            "release_rate_limit_slots",
            return_value=2,
        ) as release, mock.patch.object(
            self.bridge,
            "run_safe_command",
            side_effect=command,
        ):
            created = self.bridge.create_interactive_meeting_session({
                "agenda": "Check failed meeting reservation cleanup",
                "developmentGoal": "Keep only attempted AI turn slots after a guarded failure",
                "participantAgentIds": ["ea_developer"],
                "aiTurnsPerRound": 4,
                "idempotencyKey": "release-unused-turns",
            })
        session = self.bridge.interactive_meeting_session_read_model(
            created["session"]["id"]
        )["session"]
        self.assertEqual(session["status"], "blocked")
        self.assertEqual(session["failureReason"], "provider_error")
        self.assertEqual(len(session["turns"]), 1)
        release.assert_called_once_with(
            "real:interactive-meeting-turn",
            [12.0, 13.0],
        )

    def test_collaboration_runner_payload_is_at_most_12000_and_contribution_is_propagated(self) -> None:
        very_long = "A" * 2400
        prior_proposal = "PRIOR_PROPOSAL_SENTINEL"
        prior_risk = "RISK_SENTINEL"
        prior_check = "CHECK_SENTINEL"
        result = self.bridge._run_collaboration_agent_turn(
            meeting_id="meeting-boundary",
            mission_id="mission-boundary",
            speaker_agent_id="manager",
            topic=very_long,
            context=very_long,
            prior_turns=[{
                "speakerAgentId": "ceo",
                "speakerName": "CEO",
                "speakerRole": "Strategic Reviewer",
                "message": very_long,
                "proposal": prior_proposal,
                "risks": [prior_risk],
                "acceptanceChecks": [prior_check],
            }],
            turn_number=2,
            final_turn=True,
            timeout_seconds=90,
            output_limit=1800,
        )
        self.assertTrue(result["ok"])
        request = json.loads(self.safe_command.call_args.kwargs["input_text"])
        self.assertLessEqual(
            len(request["message"]),
            self.bridge.INTERACTIVE_MEETING_COLLABORATION_MESSAGE_MAX_CHARS,
        )
        self.assertIn("คุณเป็น Manager Agent รอบสุดท้าย", request["message"])
        self.assertIn("โดยยังไม่สร้าง Task หรือเรียก Tool", request["message"])
        self.assertIn(prior_proposal, request["message"])
        self.assertIn(prior_risk, request["message"])
        self.assertIn(prior_check, request["message"])
        self.assertEqual(result["message"], "Approve the bounded dashboard status improvement")
        self.assertEqual(result["meetingContribution"]["acceptanceChecks"][0], "Focused tests pass")
        self.assertEqual(result["meetingContribution"]["speaker"]["agentName"], "HQ Manager")
        self.assertEqual(result["meetingContribution"]["speaker"]["role"], "Manager Agent")

    def test_round_context_uses_only_this_session_and_prioritizes_latest_user_direction(self) -> None:
        latest_direction = "LATEST_USER_DIRECTION_SENTINEL"
        older_direction = "OLDER_USER_DIRECTION_SENTINEL"
        prior_manager_decision = "PRIOR_MANAGER_DECISION_SENTINEL"
        session = {
            "turns": [
                {"role": "user", "message": older_direction},
                {
                    "role": "agent",
                    "speakerAgentId": "manager",
                    "intent": "decision",
                    "message": prior_manager_decision,
                },
                {"role": "user", "message": latest_direction},
            ],
        }
        with mock.patch.object(
            self.bridge,
            "_collaboration_report_context",
            side_effect=AssertionError("global report context must not enter an interactive session"),
        ):
            context = self.bridge._interactive_meeting_round_context(session)
        self.assertIn(latest_direction, context)
        self.assertIn(older_direction, context)
        self.assertIn(prior_manager_decision, context)
        self.assertLess(context.index(latest_direction), context.index(older_direction))

    def test_manager_prompt_preserves_all_seven_prior_agent_contributions(self) -> None:
        prior_turns = [
            {
                "speakerAgentId": f"specialist_{index}",
                "speakerName": f"Agent {index}",
                "proposal": f"IDEA_{index}_SENTINEL",
                "risks": [f"RISK_{index}"],
                "acceptanceChecks": [f"CHECK_{index}"],
            }
            for index in range(1, 8)
        ]
        latest_direction = "LATEST_CONTEXT_SENTINEL"
        result = self.bridge._run_collaboration_agent_turn(
            meeting_id="meeting-seven-prior-turns",
            mission_id="mission-seven-prior-turns",
            speaker_agent_id="manager",
            topic="Evaluate one bounded Agent Office improvement",
            context=latest_direction,
            prior_turns=prior_turns,
            turn_number=8,
            final_turn=True,
            timeout_seconds=90,
            output_limit=1800,
        )
        self.assertTrue(result["ok"])
        request = json.loads(self.safe_command.call_args.kwargs["input_text"])
        self.assertLessEqual(
            len(request["message"]),
            self.bridge.INTERACTIVE_MEETING_COLLABORATION_MESSAGE_MAX_CHARS,
        )
        for index in range(1, 8):
            self.assertIn(f"IDEA_{index}_SENTINEL", request["message"])
        self.assertIn(latest_direction, request["message"])

    def test_full_input_tails_reach_every_agent_turn_after_user_interjection(self) -> None:
        agenda_tail = "AGENDA_TAIL_SENTINEL"
        goal_tail = "GOAL_TAIL_SENTINEL"
        user_tail = "USER_INTERJECTION_TAIL_SENTINEL"
        agenda = ("A" * (2400 - len(agenda_tail))) + agenda_tail
        development_goal = ("G" * (2400 - len(goal_tail))) + goal_tail
        created = self.bridge.create_interactive_meeting_session({
            "agenda": agenda,
            "developmentGoal": development_goal,
            "participantAgentIds": ["ea_developer"],
            "aiTurnsPerRound": 2,
            "idempotencyKey": "full-input-tail-create",
        })
        session_id = created["session"]["id"]
        interjection = (
            "U" * (
                self.bridge.INTERACTIVE_MEETING_USER_MESSAGE_MAX_CHARS
                - len(user_tail)
            )
        ) + user_tail
        self.bridge.append_interactive_meeting_user_message(session_id, {
            "message": interjection,
            "idempotencyKey": "full-input-tail-round-two",
        })
        round_two_requests = [
            json.loads(item.kwargs["input_text"])["message"]
            for item in self.safe_command.call_args_list[-2:]
        ]
        self.assertEqual(len(round_two_requests), 2)
        for message in round_two_requests:
            self.assertLessEqual(
                len(message),
                self.bridge.INTERACTIVE_MEETING_COLLABORATION_MESSAGE_MAX_CHARS,
            )
            self.assertIn(agenda_tail, message)
            self.assertIn(goal_tail, message)
            self.assertIn(user_tail, message)

    def test_third_round_packet_keeps_all_interjection_and_manager_decision_tails(self) -> None:
        agenda_tail = "AGENDA_ROUND_THREE_TAIL"
        goal_tail = "GOAL_ROUND_THREE_TAIL"
        first_user_tail = "FIRST_USER_TAIL"
        second_user_tail = "SECOND_USER_TAIL"
        first_manager_tail = "FIRST_MANAGER_DECISION_TAIL"
        second_manager_tail = "SECOND_MANAGER_DECISION_TAIL"

        def bounded(prefix: str, tail: str, limit: int) -> str:
            return (prefix * (limit - len(tail)))[: limit - len(tail)] + tail

        session = {
            "agenda": bounded("A", agenda_tail, 2400),
            "developmentGoal": bounded("G", goal_tail, 2400),
            "turns": [
                {
                    "role": "agent",
                    "speakerAgentId": "manager",
                    "intent": "decision",
                    "roundNumber": 1,
                    "proposal": bounded("P", first_manager_tail, 700),
                    "managerDecision": {
                        "status": "accepted",
                        "summary": bounded("S", first_manager_tail, 360),
                    },
                },
                {
                    "role": "user",
                    "message": bounded("U", first_user_tail, 1600),
                },
                {
                    "role": "agent",
                    "speakerAgentId": "manager",
                    "intent": "decision",
                    "roundNumber": 2,
                    "proposal": bounded("Q", second_manager_tail, 700),
                    "managerDecision": {
                        "status": "accepted",
                        "summary": bounded("T", second_manager_tail, 360),
                    },
                },
                {
                    "role": "user",
                    "message": bounded("V", second_user_tail, 1600),
                },
            ],
        }
        message = self.bridge._compose_collaboration_turn_message(
            topic=self.bridge._interactive_meeting_agent_topic(session),
            context=self.bridge._interactive_meeting_round_context(session),
            prior_turns=[],
            turn_number=1,
            instruction="Discuss only this exact third-round packet without tools.",
        )
        self.assertLessEqual(
            len(message),
            self.bridge.INTERACTIVE_MEETING_COLLABORATION_MESSAGE_MAX_CHARS,
        )
        for tail in (
            agenda_tail,
            goal_tail,
            first_user_tail,
            second_user_tail,
            first_manager_tail,
            second_manager_tail,
        ):
            self.assertIn(tail, message)

    def test_collaboration_prompt_fails_closed_instead_of_clipping_tail(self) -> None:
        with self.assertRaises(self.bridge.DataIntegrityError) as error:
            self.bridge._compose_collaboration_turn_message(
                topic="T" * 7000,
                context="C" * 7000,
                prior_turns=[],
                turn_number=1,
                instruction="Discuss without tools.",
                maximum_chars=(
                    self.bridge.INTERACTIVE_MEETING_COLLABORATION_MESSAGE_MAX_CHARS
                ),
            )
        self.assertIn("without truncation", str(error.exception))

    def test_risky_words_in_discussion_agenda_do_not_create_approval_or_authority(self) -> None:
        agenda = (
            "ประชุมเพื่อยืนยันว่าห้าม Deploy ระบบ production และห้ามเทรดจริง "
            "ให้คุยเฉพาะ guardrail โดยไม่สร้างงาน implementation"
        )
        generic = self.bridge.create_mission({
            "title": "Generic high-impact request remains guarded",
            "prompt": agenda,
            "agentId": "manager",
            "requester": "human",
            "toolId": "agent_collaboration",
            "targetId": self.bridge.MISSION_STRATEGY_TABLE_PROP_ID,
            "risk": "low",
            "modelTier": "manager_quality",
            "reportType": "collaboration_report",
            "idempotencyKey": "generic-risky-keywords",
            "trustedDiscussionOnly": True,
        }, status="queued")
        self.assertEqual(generic["status"], "waiting_approval")
        self.assertEqual(generic["risk"], "high")
        self.assertTrue(generic["requiresHumanApproval"])
        self.assertNotIn("discussionOnly", generic)

        result = self.bridge.create_interactive_meeting_session({
            "agenda": agenda,
            "developmentGoal": "Confirm discussion guardrails without implementation authority",
            "participantAgentIds": ["ea_developer"],
            "aiTurnsPerRound": 2,
            "idempotencyKey": "risky-discussion-safe",
        })
        self.assertTrue(result["ok"])
        session = self.bridge.interactive_meeting_session_read_model(
            result["session"]["id"]
        )["session"]
        self.assertEqual(session["status"], "awaiting_user")
        self.assertIsNone(session["proposal"])
        self.assertIsNone(session["implementationMissionId"])
        discussion = self.bridge.find_mission(session["discussionMissionIds"][0])
        self.assertEqual(discussion["status"], "completed")
        self.assertEqual(discussion["risk"], "low")
        self.assertEqual(discussion["executionMode"], "discussion_only")
        self.assertFalse(discussion["autoEligible"])
        self.assertFalse(discussion["requiresHumanApproval"])
        self.assertEqual(discussion["approval"]["state"], "not_required")
        self.assertTrue(discussion["discussionOnly"])
        self.assertEqual(discussion["discussionGuardrails"], {
            "schemaVersion": "internal-discussion-only-v1",
            "toolsEnabled": False,
            "workspaceExposed": False,
            "taskCreationEnabled": False,
            "implementationAuthority": False,
        })
        implementation = [
            mission
            for mission in self.bridge.load_missions()
            if mission.get("toolId") == "codex_cli_task"
        ]
        self.assertEqual(implementation, [])

    def test_secret_unknown_agent_manager_only_and_local_auth_are_rejected(self) -> None:
        with self.assertRaises(self.bridge.RequestError) as secret:
            self.bridge.create_interactive_meeting_session({
                "agenda": "Use api_key=secret-value in this meeting",
                "developmentGoal": "Reject secret-bearing discussion input safely",
                "participantAgentIds": ["ea_developer"],
                "aiTurnsPerRound": 2,
                "idempotencyKey": "secret-meeting",
            })
        self.assertEqual(secret.exception.status, 422)
        with self.assertRaises(self.bridge.RequestError) as unknown:
            self.bridge.create_interactive_meeting_session({
                "agenda": "Discuss a bounded dashboard improvement",
                "developmentGoal": "Deliver one verified dashboard improvement",
                "participantAgentIds": ["unknown_agent"],
                "aiTurnsPerRound": 2,
                "idempotencyKey": "unknown-agent",
            })
        self.assertEqual(unknown.exception.status, 422)
        with self.assertRaises(self.bridge.RequestError):
            self.bridge.create_interactive_meeting_session({
                "agenda": "Discuss a bounded dashboard improvement",
                "developmentGoal": "Deliver one verified dashboard improvement",
                "participantAgentIds": ["manager"],
                "aiTurnsPerRound": 2,
                "idempotencyKey": "manager-only",
            })
        fake_handler = SimpleNamespace(
            headers={"Host": "example.com"},
            server=SimpleNamespace(server_port=4186),
        )
        with self.assertRaises(self.bridge.RequestError) as auth:
            self.bridge.BridgeHandler.validate_local_request(fake_handler)
        self.assertEqual(auth.exception.status, 403)

    def test_full_access_and_strict_fresh_quota_gate_before_creation(self) -> None:
        with mock.patch.object(
            self.bridge,
            "load_operator_mode_record",
            return_value={"mode": "confirm_first"},
        ):
            with self.assertRaises(self.bridge.RequestError) as mode:
                self.bridge.create_interactive_meeting_session({
                    "agenda": "Discuss one bounded product improvement",
                    "developmentGoal": "Deliver one verified product improvement",
                    "participantAgentIds": ["ea_developer"],
                    "aiTurnsPerRound": 2,
                    "idempotencyKey": "mode-block",
                })
        self.assertEqual(mode.exception.status, 409)
        self.assertFalse(self.bridge.INTERACTIVE_MEETING_ROUND_LOCK.locked())
        with mock.patch.object(
            self.bridge,
            "_collaboration_quota_gate",
            return_value={"allowed": False, "reason": "quota_below_reserve", "messageTh": "remaining 15"},
        ):
            with self.assertRaises(self.bridge.RequestError) as quota:
                self.bridge.create_interactive_meeting_session({
                    "agenda": "Discuss one bounded product improvement",
                    "developmentGoal": "Deliver one verified product improvement",
                    "participantAgentIds": ["ea_developer"],
                    "aiTurnsPerRound": 2,
                    "idempotencyKey": "quota-block",
                })
        self.assertEqual(quota.exception.status, 429)
        self.assertFalse(self.bridge.INTERACTIVE_MEETING_ROUND_LOCK.locked())
        self.assertEqual(self.bridge.load_missions(), [])

    def test_round_cap_and_message_secret_do_not_append_or_create_mission(self) -> None:
        result = self.create_completed_first_round()
        session_id = result["session"]["id"]
        self.bridge.append_interactive_meeting_user_message(session_id, {
            "message": "Please include a visible empty state",
            "idempotencyKey": "message-round-2",
        })
        session_after_message = self.bridge.interactive_meeting_session_read_model(session_id)["session"]
        user_turn = next(item for item in session_after_message["turns"] if item.get("role") == "user")
        self.assertEqual(user_turn["speakerRole"], "local_user")
        self.bridge.append_interactive_meeting_user_message(session_id, {
            "message": "Please include a focused regression test",
            "idempotencyKey": "message-round-3",
        })
        before = len(self.bridge.load_missions())
        with self.assertRaises(self.bridge.RequestError) as cap:
            self.bridge.append_interactive_meeting_user_message(session_id, {
                "message": "Try a fourth round",
                "idempotencyKey": "message-round-4",
            })
        self.assertEqual(cap.exception.status, 409)
        with self.assertRaises(self.bridge.RequestError) as secret:
            self.bridge.append_interactive_meeting_user_message(session_id, {
                "message": "password=should-not-persist",
                "idempotencyKey": "message-secret",
            })
        self.assertEqual(secret.exception.status, 422)
        self.assertEqual(len(self.bridge.load_missions()), before)

    def test_user_interjection_accepts_1600_chars_and_rejects_1601(self) -> None:
        result = self.create_completed_first_round("message-boundary-create")
        session_id = result["session"]["id"]
        with self.assertRaises(self.bridge.RequestError) as too_long:
            self.bridge.append_interactive_meeting_user_message(session_id, {
                "message": "x" * 1601,
                "idempotencyKey": "message-boundary-too-long",
            })
        self.assertEqual(too_long.exception.status, 422)
        self.assertIn("1-1600", str(too_long.exception))
        accepted = self.bridge.append_interactive_meeting_user_message(session_id, {
            "message": "x" * 1600,
            "idempotencyKey": "message-boundary-exact",
        })
        self.assertEqual(accepted["kind"], "interactive_meeting_message_accepted")
        session = self.bridge.interactive_meeting_session_read_model(session_id)["session"]
        user_turns = [item for item in session["turns"] if item.get("role") == "user"]
        self.assertEqual(len(user_turns), 1)
        self.assertEqual(len(user_turns[0]["message"]), 1600)

    def test_message_reservation_blocks_concurrent_proposal_and_rolls_back_cleanly(self) -> None:
        result = self.create_completed_first_round()
        session_id = result["session"]["id"]
        entered = threading.Event()
        release = threading.Event()

        def fail_after_reservation(**kwargs):
            entered.set()
            release.wait(5)
            raise RuntimeError("injected mission creation failure")

        with mock.patch.object(
            self.bridge,
            "_interactive_meeting_create_discussion_mission",
            side_effect=fail_after_reservation,
        ):
            with ThreadPoolExecutor(max_workers=2) as pool:
                future = pool.submit(
                    self.bridge.append_interactive_meeting_user_message,
                    session_id,
                    {"message": "Concurrent user interjection", "idempotencyKey": "race-message"},
                )
                self.assertTrue(entered.wait(5))
                with self.assertRaises(self.bridge.RequestError) as proposal:
                    self.bridge.freeze_interactive_meeting_proposal(
                        session_id,
                        {"idempotencyKey": "race-proposal"},
                    )
                self.assertEqual(proposal.exception.status, 409)
                release.set()
                with self.assertRaises(RuntimeError):
                    future.result(timeout=5)
        session = self.bridge.interactive_meeting_session_read_model(session_id)["session"]
        self.assertEqual(session["status"], "awaiting_user")
        self.assertEqual(session["roundCount"], 1)
        self.assertEqual(len(session["discussionMissionIds"]), 1)

    def test_proposal_freeze_creates_no_mission_and_reject_is_digest_bound(self) -> None:
        result = self.create_completed_first_round()
        session_id = result["session"]["id"]
        before = len(self.bridge.load_missions())
        frozen = self.bridge.freeze_interactive_meeting_proposal(
            session_id,
            {"idempotencyKey": "freeze-1"},
        )
        self.assertEqual(frozen["session"]["status"], "proposed")
        self.assertEqual(len(self.bridge.load_missions()), before)
        digest = frozen["session"]["proposal"]["digest"]
        rejected = self.bridge.reject_interactive_meeting_proposal(session_id, {
            "confirmMeetingId": session_id,
            "confirmProposalDigest": digest,
            "idempotencyKey": "reject-1",
        })
        self.assertEqual(rejected["session"]["status"], "rejected")
        self.assertIsNone(rejected["session"]["implementationMissionId"])

    def test_approve_reservation_allows_one_mission_for_different_keys(self) -> None:
        result = self.create_completed_first_round()
        session_id = result["session"]["id"]
        frozen = self.bridge.freeze_interactive_meeting_proposal(
            session_id,
            {"idempotencyKey": "freeze-approve-race"},
        )
        digest = frozen["session"]["proposal"]["digest"]
        original = self.bridge._interactive_meeting_create_implementation_mission
        entered = threading.Event()
        release = threading.Event()

        def delayed_create(session, approval_note):
            entered.set()
            release.wait(5)
            return original(session, approval_note)

        approval_note = "อนุมัติให้แก้เฉพาะโค้ด Agent Office ตามข้อเสนอและขอบเขตที่แสดงเท่านั้น"
        payload = {
            "confirmMeetingId": session_id,
            "confirmProposalDigest": digest,
            "idempotencyKey": "approve-race-a",
            "note": approval_note,
        }
        command_count_before_approval = self.safe_command.call_count
        with mock.patch.object(
            self.bridge,
            "_interactive_meeting_create_implementation_mission",
            side_effect=delayed_create,
        ):
            with ThreadPoolExecutor(max_workers=2) as pool:
                future = pool.submit(
                    self.bridge.approve_interactive_meeting_proposal,
                    session_id,
                    payload,
                )
                self.assertTrue(entered.wait(5))
                with self.assertRaises(self.bridge.RequestError) as second:
                    self.bridge.approve_interactive_meeting_proposal(session_id, {
                        **payload,
                        "idempotencyKey": "approve-race-b",
                    })
                self.assertEqual(second.exception.status, 409)
                release.set()
                approved = future.result(timeout=5)
        self.assertTrue(approved["readyToExecute"])
        self.assertFalse(approved["executed"])
        self.assertEqual(self.safe_command.call_count, command_count_before_approval)
        implementation = [
            item for item in self.bridge.load_missions()
            if item.get("toolId") == "codex_cli_task"
        ]
        self.assertEqual(len(implementation), 1)
        expected_structured_proposal = {
            "schemaVersion": "interactive-meeting-implementation-proposal-v1",
            "meetingId": session_id,
            "proposalDigest": digest,
            "proposalTurnId": frozen["session"]["proposal"]["managerTurnId"],
            "agenda": "Improve the shared AI meeting dashboard safely",
            "developmentGoal": "Deliver one verified shared-room product improvement",
            "proposal": "Implement the selected bounded dashboard improvement",
            "risks": ["Keep existing API behavior stable"],
            "acceptanceChecks": ["Focused tests pass", "No external side effect"],
            "managerDecision": {
                "status": "accepted",
                "summary": "Approve the bounded dashboard status improvement",
            },
            "approvalNote": approval_note,
        }
        self.assertEqual(
            implementation[0]["meetingImplementationProposal"],
            expected_structured_proposal,
        )
        self.assertEqual(
            implementation[0]["approval"]["payloadDigest"],
            self.bridge.mission_payload_digest(implementation[0]),
        )
        self.assertIn(
            "Deliver one verified shared-room product improvement",
            implementation[0]["detail"],
        )
        self.assertIn(approval_note, implementation[0]["detail"])
        self.assertIn(
            "Structured approved proposal:\nImplement the selected bounded dashboard improvement",
            implementation[0]["detail"],
        )
        self.assertIn(
            "Manager decision status:\naccepted",
            implementation[0]["detail"],
        )
        self.assertIn(
            "Manager decision summary:\nApprove the bounded dashboard status improvement",
            implementation[0]["detail"],
        )
        self.assertIn("- Keep existing API behavior stable", implementation[0]["detail"])
        self.assertIn("- Focused tests pass", implementation[0]["detail"])
        self.assertIn("- No external side effect", implementation[0]["detail"])
        self.assertLessEqual(
            len(implementation[0]["detail"]),
            self.bridge.INTERACTIVE_MEETING_IMPLEMENTATION_PROMPT_MAX_CHARS,
        )
        self.assertEqual(
            implementation[0]["meetingImplementationPrompt"]["promptChars"],
            len(implementation[0]["detail"]),
        )
        for allowed_root in (
            "workspace",
            "frontend",
            "backend",
            "runner",
            "contracts",
            "tests",
            "docs",
            "assets-source",
        ):
            self.assertIn(allowed_root, implementation[0]["detail"])
        for denied_surface in (
            "runtime data",
            "scripts",
            "installer surfaces",
            ".git",
            "MetaTrader",
            "trading actions",
            "external side effects",
        ):
            self.assertIn(denied_surface, implementation[0]["detail"])
        session = self.bridge.interactive_meeting_session_read_model(session_id)["session"]
        self.assertEqual(session["status"], "approved")
        self.assertTrue(session["readyToExecute"])
        self.assertEqual(session["approvalNote"], approval_note)
        self.assertEqual(session["implementationMission"]["approvalState"], "approved")
        human_decision = next(
            item
            for item in implementation[0]["approval"]["decisions"]
            if item.get("actorId") == "human"
        )
        self.assertEqual(human_decision["note"], approval_note)
        replay = self.bridge.approve_interactive_meeting_proposal(
            session_id,
            payload,
        )
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["implementationMissionId"], implementation[0]["id"])

    def test_structured_implementation_proposal_is_digest_bound_and_revalidated(self) -> None:
        result = self.create_completed_first_round()
        session_id = result["session"]["id"]
        frozen = self.bridge.freeze_interactive_meeting_proposal(
            session_id,
            {"idempotencyKey": "freeze-structured-binding"},
        )
        digest = frozen["session"]["proposal"]["digest"]
        approved = self.bridge.approve_interactive_meeting_proposal(session_id, {
            "confirmMeetingId": session_id,
            "confirmProposalDigest": digest,
            "idempotencyKey": "approve-structured-binding",
            "note": "Approve only the exact structured proposal and acceptance checks",
        })
        mission = approved["mission"]
        self.assertEqual(
            self.bridge._approved_interactive_meeting_workspace_binding(mission),
            {"meetingId": session_id, "proposalDigest": digest},
        )
        original_payload_digest = self.bridge.mission_payload_digest(mission)

        session_mismatch = json.loads(json.dumps(mission))
        session_mismatch["meetingImplementationProposal"]["managerDecision"][
            "summary"
        ] += " changed"
        self.assertNotEqual(
            self.bridge.mission_payload_digest(session_mismatch),
            original_payload_digest,
        )
        with self.assertRaises(self.bridge.RequestError):
            self.bridge._approved_interactive_meeting_workspace_binding(
                session_mismatch
            )

        broad_packet = json.loads(json.dumps(mission))
        broad_packet["meetingImplementationProposal"]["extraAuthority"] = True
        with self.assertRaises(self.bridge.RequestError):
            self.bridge._approved_interactive_meeting_workspace_binding(
                broad_packet
            )

        self.bridge.replace_mission(session_mismatch)
        command_count = self.safe_command.call_count
        executed = self.bridge.execute_mission(
            mission["id"],
            {"confirmMissionId": mission["id"]},
        )
        self.assertEqual(executed["kind"], "approval_digest_mismatch")
        self.assertEqual(self.safe_command.call_count, command_count)

    def test_generic_prompt_over_8000_fails_closed_without_persisting(self) -> None:
        mission_count = len(self.bridge.load_missions())
        with self.assertRaises(self.bridge.RequestError) as rejected:
            self.bridge.create_mission({
                "prompt": "G" * 8001,
                "agentId": "manager",
                "requester": "human",
                "toolId": "manager_mission",
                "targetId": self.bridge.MISSION_STRATEGY_TABLE_PROP_ID,
                "risk": "low",
                "reportType": "manager_plan",
                "idempotencyKey": "generic-prompt-over-limit",
            })
        self.assertEqual(rejected.exception.status, 422)
        self.assertIn("8000", str(rejected.exception))
        self.assertEqual(len(self.bridge.load_missions()), mission_count)

    def test_private_meeting_prompt_supports_12000_bound_without_broad_capability(self) -> None:
        long_prompt = "P" * 12000
        structured_proposal = {
            "schemaVersion": "interactive-meeting-implementation-proposal-v1",
            "meetingId": "meeting-private-prompt",
            "proposalDigest": "a" * 64,
            "proposalTurnId": "turn-private-manager",
            "agenda": "Verify the private prompt boundary",
            "developmentGoal": "Keep the implementation capability exact",
            "proposal": "Implement only the approved bounded change",
            "risks": ["Preserve existing behavior"],
            "acceptanceChecks": ["Focused tests pass"],
            "managerDecision": {
                "status": "accepted",
                "summary": "Approve only this bounded implementation",
            },
            "approvalNote": "Approved for this exact local scope",
        }
        payload = {
            "prompt": long_prompt,
            "agentId": "ea_developer",
            "requester": "human",
            "toolId": "codex_cli_task",
            "targetId": "terminal_workstation",
            "risk": "high",
            "modelTier": "manager_quality",
            "reportType": "code_change_report",
            "meetingImplementationProposal": structured_proposal,
            "idempotencyKey": "meeting-implementation:private-long-prompt",
        }
        mission = self.bridge.create_mission(
            payload,
            status="waiting_approval",
            _trusted_meeting_implementation_prompt=long_prompt,
        )
        self.assertEqual(len(mission["detail"]), 12000)
        self.assertTrue(mission["requiresHumanApproval"])
        self.assertFalse(mission["autoEligible"])
        self.assertEqual(
            mission["meetingImplementationProposal"],
            structured_proposal,
        )
        self.assertEqual(
            mission["meetingImplementationPrompt"]["maximumChars"],
            12000,
        )
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.bridge.create_mission(
                {**payload, "agentId": "manager", "idempotencyKey": "meeting-implementation:broad"},
                status="waiting_approval",
                _trusted_meeting_implementation_prompt=long_prompt,
            )
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.bridge.create_mission(
                {
                    **payload,
                    "modelTier": "specialist_fast",
                    "idempotencyKey": "meeting-implementation:wrong-tier",
                },
                status="waiting_approval",
                _trusted_meeting_implementation_prompt=long_prompt,
            )
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.bridge.create_mission(
                {**payload, "idempotencyKey": "meeting-implementation:mismatch"},
                status="waiting_approval",
                _trusted_meeting_implementation_prompt=long_prompt + "X",
            )
        over_limit_prompt = long_prompt + "X"
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.bridge.create_mission(
                {
                    **payload,
                    "prompt": over_limit_prompt,
                    "idempotencyKey": "meeting-implementation:over-limit",
                },
                status="waiting_approval",
                _trusted_meeting_implementation_prompt=over_limit_prompt,
            )

    def test_stale_proposal_digest_creates_no_implementation_mission(self) -> None:
        result = self.create_completed_first_round()
        session_id = result["session"]["id"]
        frozen = self.bridge.freeze_interactive_meeting_proposal(
            session_id,
            {"idempotencyKey": "freeze-stale"},
        )
        digest = frozen["session"]["proposal"]["digest"]
        with self.bridge.INTERACTIVE_MEETING_SESSIONS_LOCK:
            store = self.bridge._load_interactive_meeting_store_unlocked()
            session = self.bridge._interactive_meeting_find_unlocked(store, session_id)
            session["proposal"]["text"] = "tampered proposal text"
            self.bridge._save_interactive_meeting_store_unlocked(store)
        with self.assertRaises(self.bridge.RequestError) as stale:
            self.bridge.approve_interactive_meeting_proposal(session_id, {
                "confirmMeetingId": session_id,
                "confirmProposalDigest": digest,
                "idempotencyKey": "approve-stale",
            })
        self.assertEqual(stale.exception.status, 409)
        self.assertFalse(any(
            item.get("toolId") == "codex_cli_task"
            for item in self.bridge.load_missions()
        ))

    def test_structured_proposal_copy_must_match_digest_bound_manager_turn(self) -> None:
        result = self.create_completed_first_round()
        session_id = result["session"]["id"]
        frozen = self.bridge.freeze_interactive_meeting_proposal(
            session_id,
            {"idempotencyKey": "freeze-structured-tamper"},
        )
        digest = frozen["session"]["proposal"]["digest"]
        with self.bridge.INTERACTIVE_MEETING_SESSIONS_LOCK:
            store = self.bridge._load_interactive_meeting_store_unlocked()
            session = self.bridge._interactive_meeting_find_unlocked(store, session_id)
            session["proposal"]["proposal"] = "Tampered structured proposal copy"
            self.bridge._save_interactive_meeting_store_unlocked(store)
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.bridge.approve_interactive_meeting_proposal(session_id, {
                "confirmMeetingId": session_id,
                "confirmProposalDigest": digest,
                "idempotencyKey": "approve-structured-tamper",
                "note": "อนุมัติเฉพาะข้อเสนอที่ผูก digest และข้อมูล Manager เดิมเท่านั้น",
            })
        self.assertFalse(any(
            item.get("toolId") == "codex_cli_task"
            for item in self.bridge.load_missions()
        ))

    def test_proposal_digest_binds_user_owned_development_goal(self) -> None:
        result = self.create_completed_first_round()
        session_id = result["session"]["id"]
        frozen = self.bridge.freeze_interactive_meeting_proposal(
            session_id,
            {"idempotencyKey": "freeze-goal-binding"},
        )
        digest = frozen["session"]["proposal"]["digest"]
        self.assertEqual(
            frozen["session"]["proposal"]["digestVersion"],
            self.bridge.INTERACTIVE_MEETING_PROPOSAL_DIGEST_VERSION,
        )
        with self.bridge.INTERACTIVE_MEETING_SESSIONS_LOCK:
            store = self.bridge._load_interactive_meeting_store_unlocked()
            session = self.bridge._interactive_meeting_find_unlocked(store, session_id)
            session["developmentGoal"] = "Tampered development goal"
            self.bridge._save_interactive_meeting_store_unlocked(store)
        with self.assertRaises(self.bridge.RequestError) as stale:
            self.bridge.approve_interactive_meeting_proposal(session_id, {
                "confirmMeetingId": session_id,
                "confirmProposalDigest": digest,
                "idempotencyKey": "approve-tampered-goal",
            })
        self.assertEqual(stale.exception.status, 409)
        self.assertFalse(any(
            item.get("toolId") == "codex_cli_task"
            for item in self.bridge.load_missions()
        ))

    def test_runner_busy_blocks_discussion_mission_instead_of_leaving_queue(self) -> None:
        class BusySemaphore:
            def acquire(self, blocking=False):
                return False

            def release(self):
                raise AssertionError("busy semaphore was not acquired")

        with mock.patch.object(self.bridge, "REAL_RUN_SEMAPHORE", BusySemaphore()):
            result = self.bridge.create_interactive_meeting_session({
                "agenda": "Verify runner busy fail closed behavior",
                "developmentGoal": "Prove a busy Runner fails closed before an AI turn",
                "participantAgentIds": ["ea_developer"],
                "aiTurnsPerRound": 2,
                "idempotencyKey": "runner-busy",
            })
        session = self.bridge.interactive_meeting_session_read_model(
            result["session"]["id"]
        )["session"]
        self.assertEqual(session["status"], "blocked")
        mission = self.bridge.find_mission(session["discussionMissionIds"][0])
        self.assertEqual(mission["status"], "blocked")
        self.assertEqual(mission["errorCode"], "runner_busy")

    def test_approved_execute_uses_exact_bound_workspace_mode_and_echo(self) -> None:
        result = self.create_completed_first_round()
        session_id = result["session"]["id"]
        frozen = self.bridge.freeze_interactive_meeting_proposal(
            session_id,
            {"idempotencyKey": "freeze-execute"},
        )
        digest = frozen["session"]["proposal"]["digest"]
        approved = self.bridge.approve_interactive_meeting_proposal(session_id, {
            "confirmMeetingId": session_id,
            "confirmProposalDigest": digest,
            "idempotencyKey": "approve-execute",
        })
        mission_id = approved["implementationMissionId"]
        captured = {}

        def execute_command(command, **kwargs):
            captured["command"] = [str(item) for item in command]
            output = {
                "ok": True,
                "status": "completed",
                "workStatus": "completed",
                "finalMessage": "Bounded implementation completed",
                "approvalBinding": {
                    "meetingId": session_id,
                    "proposalDigest": digest,
                },
                "processStarted": True,
                "processTreeTerminated": False,
            }
            return {
                "ok": True,
                "exitCode": 0,
                "durationMs": 10,
                "output": json.dumps(output),
                "processStarted": True,
                "processTreeTerminated": False,
            }

        with mock.patch.object(
            self.bridge,
            "bridge_status",
            return_value={"codex": {"status": "ready_guarded"}},
        ), mock.patch.object(
            self.bridge,
            "codex_rate_limits",
            return_value={"ok": True, "limitReached": False},
        ), mock.patch.object(
            self.bridge,
            "run_safe_command",
            side_effect=execute_command,
        ):
            executed = self.bridge.execute_mission(
                mission_id,
                {"confirmMissionId": mission_id},
            )
        self.assertTrue(executed["ok"])
        command = captured["command"]
        self.assertEqual(command[command.index("--execution-mode") + 1], "approved_workspace")
        self.assertEqual(command[command.index("--approval-meeting-id") + 1], session_id)
        self.assertEqual(command[command.index("--approval-proposal-digest") + 1], digest)
        self.assertEqual(executed["mission"]["phase"], "approved_workspace_completed")

    def test_restart_recovery_blocks_running_round_and_persists(self) -> None:
        with mock.patch.object(
            self.bridge,
            "_interactive_meeting_start_round_thread",
            return_value=None,
        ):
            result = self.bridge.create_interactive_meeting_session({
                "agenda": "Recover one interrupted interactive meeting",
                "developmentGoal": "Prove restart recovery blocks an interrupted round",
                "participantAgentIds": ["ea_developer"],
                "aiTurnsPerRound": 2,
                "idempotencyKey": "restart-create",
            })
        if self.bridge.INTERACTIVE_MEETING_ROUND_LOCK.locked():
            self.bridge.INTERACTIVE_MEETING_ROUND_LOCK.release()
        session_id = result["session"]["id"]
        recovered = self.bridge.recover_interrupted_interactive_meeting_sessions()
        self.assertEqual(recovered, 1)
        session = self.bridge.interactive_meeting_session_read_model(session_id)["session"]
        self.assertEqual(session["status"], "blocked")
        self.assertEqual(session["failureReason"], "bridge_restart_during_round")
        mission = self.bridge.find_mission(session["discussionMissionIds"][0])
        self.assertEqual(mission["status"], "blocked")

    def test_store_prunes_idempotency_for_trimmed_session(self) -> None:
        store = self.bridge._interactive_meeting_default_store()
        for index in range(self.bridge.INTERACTIVE_MEETING_MAX_SESSIONS):
            store["sessions"].append({
                "id": f"meeting-{index}",
                "agenda": "bounded",
                "participantAgentIds": ["ea_developer", "manager"],
                "status": "idle",
                "roundCount": 0,
                "turns": [],
                "discussionMissionIds": [],
                "idempotency": {},
            })
        store["createIdempotency"] = {
            "kept": {"sessionId": "meeting-0"},
            "stale": {"sessionId": "meeting-trimmed"},
        }
        with self.bridge.INTERACTIVE_MEETING_SESSIONS_LOCK:
            saved = self.bridge._save_interactive_meeting_store_unlocked(store)
        self.assertIn("kept", saved["createIdempotency"])
        self.assertNotIn("stale", saved["createIdempotency"])
        self.assertEqual(saved["sessions"][0]["developmentGoal"], "bounded")
        self.assertEqual(saved["sessions"][0]["aiTurnsPerRound"], 2)

    def test_http_routes_are_present_and_legacy_meetings_remain(self) -> None:
        source = BRIDGE_PATH.read_text(encoding="utf-8")
        for route in (
            "/api/meetings/sessions",
            "messages|proposal|approve|reject",
            "/api/meetings",
            "/api/meetings/turn",
        ):
            self.assertIn(route, source)

    def test_http_create_list_and_detail_round_trip_on_loopback(self) -> None:
        server = self.bridge.BridgeHTTPServer(
            ("127.0.0.1", 0),
            self.bridge.BridgeHandler,
        )
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            connection = http.client.HTTPConnection(
                "127.0.0.1",
                server.server_port,
                timeout=5,
            )
            body = json.dumps({
                "agenda": "Build one bounded shared meeting read model",
                "developmentGoal": "Expose a verified user-controlled meeting batch",
                "participantAgentIds": ["ea_developer"],
                "aiTurnsPerRound": 2,
                "idempotencyKey": "http-create",
            })
            connection.request(
                "POST",
                "/api/meetings/sessions",
                body=body,
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            created = json.loads(response.read())
            self.assertEqual(response.status, 202)
            session_id = created["session"]["id"]
            connection.request("GET", "/api/meetings/sessions")
            response = connection.getresponse()
            listed = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertEqual(listed["sessions"][0]["id"], session_id)
            connection.request("GET", f"/api/meetings/sessions/{session_id}")
            response = connection.getresponse()
            detailed = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertEqual(detailed["session"]["status"], "awaiting_user")
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
