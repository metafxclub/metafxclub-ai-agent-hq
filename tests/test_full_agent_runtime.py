from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = (
    PROJECT_ROOT / "backend" / "local-runner" / "full_agent_runtime.py"
)


def load_runtime_module():
    spec = importlib.util.spec_from_file_location(
        "metafx_full_agent_runtime_tests", RUNTIME_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Full Agent runtime module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FullAgentRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_runtime_module()

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name).resolve() / "runtime"
        self.runtime = self.module.FullAgentRuntime(
            self.root,
            allowed_agents={"technical_consultant", "ea_developer"},
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def create_thread(self, **overrides):
        request = {
            "agent_id": "technical_consultant",
            "title": "Technical review",
            "idempotency_key": "create-thread-0001",
        }
        request.update(overrides)
        return self.runtime.create_thread(**request)

    def assert_error(self, code: str, callable_):
        with self.assertRaises(self.module.FullAgentRuntimeError) as caught:
            callable_()
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def test_status_is_truthful_and_exposes_only_allowlisted_options(self) -> None:
        status = self.runtime.runtime_status("technical_consultant")

        self.assertTrue(status["available"])
        self.assertFalse(status["executionEnabled"])
        self.assertEqual(status["toolExecutionState"], "not_connected")
        self.assertEqual(status["storageKind"], "local_secret_free_atomic_json")
        self.assertFalse(status["secretStorageAllowed"])
        self.assertFalse(status["encryptionAtRest"])
        self.assertIn("gpt-6-sol", status["modelOptions"])
        self.assertEqual(
            [item["id"] for item in status["capabilityModes"]],
            ["chat", "workspace", "computer", "full"],
        )
        self.assertTrue(
            all(not item["toolExecutionEnabled"] for item in status["capabilityModes"])
        )

    def approval_request(self, **overrides):
        request = {
            "requestId": "approval-request-0001",
            "method": "item/commandExecution/requestApproval",
            "actionType": "command",
            "threadId": "thread-approval-0001",
            "turnId": "turn-approval-0001",
            "itemId": "item-approval-0001",
            "requestDigest": "a" * 64,
            "decisionNonce": "0123456789abcdef0123456789abcdef",
            "createdAt": "2026-09-27T00:00:00.000Z",
            "expiresAt": "2026-09-27T00:02:00.000Z",
            "commandSummary": "rg bounded_target .",
            "cwdLabel": "Workspace",
            "reason": "Codex requests one command execution approval.",
        }
        request.update(overrides)
        return request

    def test_approval_journal_hashes_secrets_and_replays_committed_tombstone(self) -> None:
        clock = [100.0]
        journal = self.module.FullAgentApprovalJournal(
            self.root,
            now_epoch=lambda: clock[0],
        )
        request = self.approval_request()
        journal.register_pending(request, expires_epoch=200.0)
        claimed = journal.claim_decision(
            request["requestId"],
            decision="accept_once",
            idempotency_key="approval-idempotency-0001",
            thread_id=request["threadId"],
            turn_id=request["turnId"],
            item_id=request["itemId"],
            payload_hash=request["requestDigest"],
            decision_nonce=request["decisionNonce"],
        )
        self.assertFalse(claimed["idempotentReplay"])
        committed = journal.commit_resolution(
            request["requestId"],
            requested_decision="accept_once",
            effective_decision="accept_once",
            outcome_success=True,
            terminal_reason="user_approved_once",
        )
        self.assertEqual(committed["state"], "committed")

        raw = (self.root / self.module.APPROVAL_JOURNAL_FILENAME).read_text(
            encoding="utf-8"
        )
        self.assertNotIn(request["decisionNonce"], raw)
        self.assertNotIn("approval-idempotency-0001", raw)
        self.assertNotIn(request["commandSummary"], raw)
        self.assertNotIn("C:\\", raw)

        restarted = self.module.FullAgentApprovalJournal(
            self.root,
            now_epoch=lambda: clock[0],
        )
        replay = restarted.claim_decision(
            request["requestId"],
            decision="accept_once",
            idempotency_key="approval-idempotency-0001",
            thread_id=request["threadId"],
            turn_id=request["turnId"],
            item_id=request["itemId"],
            payload_hash=request["requestDigest"],
            decision_nonce=request["decisionNonce"],
        )
        self.assertTrue(replay["idempotentReplay"])
        self.assertTrue(replay["committed"])
        self.assertTrue(replay["outcomeSuccess"])
        self.assert_error(
            "approval_decision_conflict",
            lambda: restarted.claim_decision(
                request["requestId"],
                decision="decline",
                idempotency_key="approval-idempotency-0001",
                thread_id=request["threadId"],
                turn_id=request["turnId"],
                item_id=request["itemId"],
                payload_hash=request["requestDigest"],
                decision_nonce=request["decisionNonce"],
            ),
        )

    def test_approval_journal_restart_aborts_unfinished_request(self) -> None:
        clock = [100.0]
        first = self.module.FullAgentApprovalJournal(
            self.root,
            now_epoch=lambda: clock[0],
        )
        request = self.approval_request(requestId="approval-restart-0001")
        first.register_pending(request, expires_epoch=200.0)

        restarted = self.module.FullAgentApprovalJournal(
            self.root,
            now_epoch=lambda: clock[0],
        )
        record = restarted.get_record(request["requestId"])
        self.assertEqual(record["state"], "aborted")
        self.assertEqual(record["effectiveDecision"], "decline")
        self.assertFalse(record["outcomeSuccess"])
        self.assertEqual(record["terminalReason"], "broker_restarted")
        replay = restarted.claim_decision(
            request["requestId"],
            decision="accept_once",
            idempotency_key="approval-restart-key-0001",
            thread_id=request["threadId"],
            turn_id=request["turnId"],
            item_id=request["itemId"],
            payload_hash=request["requestDigest"],
            decision_nonce=request["decisionNonce"],
        )
        self.assertEqual(replay["state"], "aborted")
        self.assertFalse(replay["committed"])

    def test_approval_journal_expiry_and_concurrent_first_decision_fail_closed(self) -> None:
        clock = [100.0]
        journal = self.module.FullAgentApprovalJournal(
            self.root,
            now_epoch=lambda: clock[0],
        )
        expired = self.approval_request(requestId="approval-expired-0001")
        journal.register_pending(expired, expires_epoch=101.0)
        clock[0] = 102.0
        self.assert_error(
            "approval_expired",
            lambda: journal.claim_decision(
                expired["requestId"],
                decision="accept_once",
                idempotency_key="approval-expired-key-0001",
                thread_id=expired["threadId"],
                turn_id=expired["turnId"],
                item_id=expired["itemId"],
                payload_hash=expired["requestDigest"],
                decision_nonce=expired["decisionNonce"],
            ),
        )
        self.assertEqual(journal.get_record(expired["requestId"])["state"], "aborted")

        clock[0] = 200.0
        request = self.approval_request(requestId="approval-race-0001")
        journal.register_pending(request, expires_epoch=300.0)
        outcomes: list[str] = []
        barrier = threading.Barrier(3)

        def decide(decision: str, key: str) -> None:
            barrier.wait()
            try:
                journal.claim_decision(
                    request["requestId"],
                    decision=decision,
                    idempotency_key=key,
                    thread_id=request["threadId"],
                    turn_id=request["turnId"],
                    item_id=request["itemId"],
                    payload_hash=request["requestDigest"],
                    decision_nonce=request["decisionNonce"],
                )
                outcomes.append(decision)
            except self.module.FullAgentRuntimeError as error:
                outcomes.append(error.code)

        workers = [
            threading.Thread(target=decide, args=("accept_once", "approval-race-accept")),
            threading.Thread(target=decide, args=("decline", "approval-race-decline")),
        ]
        for worker in workers:
            worker.start()
        barrier.wait()
        for worker in workers:
            worker.join(2)
        self.assertEqual(len(outcomes), 2)
        self.assertEqual(outcomes.count("approval_decision_conflict"), 1)
        self.assertEqual(
            len([value for value in outcomes if value in {"accept_once", "decline"}]),
            1,
        )

    def test_approval_journal_retains_terminal_replay_for_full_window(self) -> None:
        clock = [100.0]

        def now() -> str:
            return datetime.fromtimestamp(clock[0], timezone.utc).isoformat(
                timespec="milliseconds"
            ).replace("+00:00", "Z")

        journal = self.module.FullAgentApprovalJournal(
            self.root,
            now=now,
            now_epoch=lambda: clock[0],
        )
        request = self.approval_request(requestId="approval-retention-0001")
        journal.register_pending(request, expires_epoch=200.0)
        journal.claim_decision(
            request["requestId"],
            decision="accept_once",
            idempotency_key="approval-retention-key-0001",
            thread_id=request["threadId"],
            turn_id=request["turnId"],
            item_id=request["itemId"],
            payload_hash=request["requestDigest"],
            decision_nonce=request["decisionNonce"],
        )
        journal.commit_resolution(
            request["requestId"],
            requested_decision="accept_once",
            effective_decision="accept_once",
            outcome_success=True,
            terminal_reason="user_approved_once",
        )

        clock[0] += self.module.APPROVAL_REPLAY_RETENTION_SECONDS
        restarted = self.module.FullAgentApprovalJournal(
            self.root,
            now=now,
            now_epoch=lambda: clock[0],
        )
        replay = restarted.claim_decision(
            request["requestId"],
            decision="accept_once",
            idempotency_key="approval-retention-key-0001",
            thread_id=request["threadId"],
            turn_id=request["turnId"],
            item_id=request["itemId"],
            payload_hash=request["requestDigest"],
            decision_nonce=request["decisionNonce"],
        )
        self.assertTrue(replay["idempotentReplay"])
        self.assertTrue(replay["committed"])

        clock[0] += 1.0
        compacted = self.module.FullAgentApprovalJournal(
            self.root,
            now=now,
            now_epoch=lambda: clock[0],
        )
        self.assertIsNone(compacted.get_record(request["requestId"]))

    def test_approval_capacity_compacts_only_expired_terminal_records(self) -> None:
        clock = [100.0]

        def now() -> str:
            return datetime.fromtimestamp(clock[0], timezone.utc).isoformat(
                timespec="milliseconds"
            ).replace("+00:00", "Z")

        with mock.patch.object(self.module, "MAX_APPROVAL_RECORDS", 3):
            journal = self.module.FullAgentApprovalJournal(
                self.root,
                now=now,
                now_epoch=lambda: clock[0],
            )
            terminal = self.approval_request(requestId="approval-terminal-old-0001")
            decision_recorded = self.approval_request(
                requestId="approval-decision-inflight-0001"
            )
            pending = self.approval_request(requestId="approval-pending-inflight-0001")
            for request in (terminal, decision_recorded, pending):
                journal.register_pending(request, expires_epoch=200000.0)

            journal.claim_decision(
                terminal["requestId"],
                decision="decline",
                idempotency_key="approval-terminal-key-0001",
                thread_id=terminal["threadId"],
                turn_id=terminal["turnId"],
                item_id=terminal["itemId"],
                payload_hash=terminal["requestDigest"],
                decision_nonce=terminal["decisionNonce"],
            )
            journal.commit_resolution(
                terminal["requestId"],
                requested_decision="decline",
                effective_decision="decline",
                outcome_success=True,
                terminal_reason="user_declined",
            )
            journal.claim_decision(
                decision_recorded["requestId"],
                decision="accept_once",
                idempotency_key="approval-inflight-key-0001",
                thread_id=decision_recorded["threadId"],
                turn_id=decision_recorded["turnId"],
                item_id=decision_recorded["itemId"],
                payload_hash=decision_recorded["requestDigest"],
                decision_nonce=decision_recorded["decisionNonce"],
            )

            clock[0] += self.module.APPROVAL_REPLAY_RETENTION_SECONDS + 1.0
            replacement = self.approval_request(requestId="approval-replacement-0001")
            journal.register_pending(replacement, expires_epoch=clock[0] + 1000.0)

            self.assertIsNone(journal.get_record(terminal["requestId"]))
            self.assertEqual(
                journal.get_record(decision_recorded["requestId"])["state"],
                "decision_recorded",
            )
            self.assertEqual(journal.get_record(pending["requestId"])["state"], "pending")
            self.assertEqual(
                journal.get_record(replacement["requestId"])["state"], "pending"
            )
            overflow = self.approval_request(requestId="approval-overflow-0001")
            self.assert_error(
                "approval_store_full",
                lambda: journal.register_pending(
                    overflow, expires_epoch=clock[0] + 1000.0
                ),
            )

    def test_create_get_list_update_archive_and_unarchive_persist(self) -> None:
        created = self.create_thread()["thread"]
        self.assertEqual(created["agentId"], "technical_consultant")
        self.assertEqual(created["model"], "gpt-6-sol")
        self.assertEqual(created["reasoning"], "medium")
        self.assertEqual(created["mode"], "chat")
        self.assertEqual(created["status"], "idle")
        self.assertFalse(created["archived"])
        self.assertEqual(created["events"], [])
        self.assertFalse(created["canInterrupt"])
        self.assertFalse(created["canContinue"])
        self.assertTrue(created["canArchive"])
        self.assertTrue(created["canUpdateSettings"])

        updated = self.runtime.update_settings(
            created["id"],
            title="Workspace review",
            model="gpt-6-astra",
            reasoning="high",
            mode="workspace",
            expected_revision=created["revision"],
        )
        self.assertEqual(updated["title"], "Workspace review")
        self.assertEqual(updated["model"], "gpt-6-astra")
        self.assertEqual(updated["reasoning"], "high")
        self.assertEqual(updated["mode"], "workspace")
        self.assertIn("shell", updated["capabilities"])

        archived = self.runtime.archive_thread(
            created["id"], expected_revision=updated["revision"]
        )
        self.assertTrue(archived["archived"])
        self.assertEqual(archived["status"], "archived")
        self.assertEqual(self.runtime.list_threads(), [])
        self.assertEqual(len(self.runtime.list_threads(include_archived=True)), 1)

        restored = self.runtime.archive_thread(created["id"], archived=False)
        self.assertFalse(restored["archived"])
        reloaded = self.module.FullAgentRuntime(
            self.root,
            allowed_agents={"technical_consultant", "ea_developer"},
        ).get_thread(created["id"])
        self.assertEqual(reloaded["title"], "Workspace review")
        self.assertFalse(reloaded["archived"])

    def test_create_is_idempotent_and_does_not_store_raw_key(self) -> None:
        first = self.create_thread()
        replay = self.create_thread()

        self.assertFalse(first["idempotentReplay"])
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(first["thread"]["id"], replay["thread"]["id"])
        raw = (self.root / self.module.STORE_FILENAME).read_text(encoding="utf-8")
        self.assertNotIn("create-thread-0001", raw)

    def test_create_idempotency_conflict_is_rejected(self) -> None:
        self.create_thread()
        self.assert_error(
            "idempotency_conflict",
            lambda: self.create_thread(title="Different request"),
        )

    def test_unknown_agent_and_non_allowlisted_settings_are_rejected(self) -> None:
        self.assert_error(
            "unknown_agent", lambda: self.runtime.create_thread("intruder_agent")
        )
        self.assert_error(
            "model_not_allowed",
            lambda: self.runtime.create_thread(
                "technical_consultant", model="untrusted-model"
            ),
        )
        self.assert_error(
            "reasoning_not_allowed",
            lambda: self.runtime.create_thread(
                "technical_consultant", reasoning="infinite"
            ),
        )
        self.assert_error(
            "mode_not_allowed",
            lambda: self.runtime.create_thread(
                "technical_consultant", mode="danger-full-access"
            ),
        )

    def test_update_uses_optimistic_revision_guard(self) -> None:
        thread = self.create_thread()["thread"]
        changed = self.runtime.update_settings(thread["id"], title="Changed")

        self.assert_error(
            "revision_conflict",
            lambda: self.runtime.update_settings(
                thread["id"], title="Stale", expected_revision=thread["revision"]
            ),
        )
        self.assertEqual(
            self.runtime.get_thread(thread["id"])["revision"], changed["revision"]
        )

    def test_append_event_sanitizes_controls_and_is_idempotent(self) -> None:
        thread = self.create_thread()["thread"]
        first = self.runtime.append_event(
            thread["id"],
            role="assistant",
            content="Result\x00 ready\u202e",
            metadata={"source": "local_runner", "count": 2},
            idempotency_key="event-answer-0001",
        )
        replay = self.runtime.append_event(
            thread["id"],
            role="assistant",
            content="Result\x00 ready\u202e",
            metadata={"source": "local_runner", "count": 2},
            idempotency_key="event-answer-0001",
        )

        self.assertEqual(first["event"]["content"], "Result ready")
        self.assertEqual(first["event"]["contentFormat"], "plain_text")
        self.assertFalse(first["idempotentReplay"])
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(first["event"]["id"], replay["event"]["id"])
        self.assertEqual(self.runtime.get_thread(thread["id"])["eventCount"], 1)

    def test_event_idempotency_conflict_is_rejected(self) -> None:
        thread = self.create_thread()["thread"]
        self.runtime.append_event(
            thread["id"],
            role="assistant",
            content="First",
            idempotency_key="event-conflict-0001",
        )
        self.assert_error(
            "idempotency_conflict",
            lambda: self.runtime.append_event(
                thread["id"],
                role="assistant",
                content="Changed",
                idempotency_key="event-conflict-0001",
            ),
        )

    def test_tool_event_requires_tool_name_and_has_frontend_safe_shape(self) -> None:
        thread = self.create_thread()["thread"]
        self.assert_error(
            "invalid_request",
            lambda: self.runtime.append_event(
                thread["id"], role="tool", event_type="tool_result", content="ok"
            ),
        )
        event = self.runtime.append_event(
            thread["id"],
            role="tool",
            event_type="tool_result",
            content="read-only result",
            tool_name="workspace.read",
            tool_call_id="call_001",
        )["event"]
        self.assertEqual(event["toolName"], "workspace.read")
        self.assertEqual(event["toolCallId"], "call_001")
        self.assertNotIn("idempotencyKey", event)
        self.assertNotIn("requestDigest", event)

    def test_secret_patterns_and_sensitive_metadata_are_rejected_without_persistence(self) -> None:
        thread = self.create_thread()["thread"]
        secret_attempts = (
            "Authorization: Bearer abcdefghijklmnopqrstuvwxyz",
            "api_" + "key=abcdefghijklmnop123456",
            "refresh_token: abcdefghijklmnop123456",
            "-----BEGIN PRIVATE " + "KEY-----",
            "ghp" + "_abcdefghijklmnopqrstuvwxyz123456",
            "GOC" + "SPX-" + ("A" * 28),
            str(123456789) + ":" + ("A" * 35),
        )
        for index, content in enumerate(secret_attempts):
            with self.subTest(index=index):
                self.assert_error(
                    "secret_rejected",
                    lambda content=content: self.runtime.append_event(
                        thread["id"], role="user", content=content
                    ),
                )
        self.assert_error(
            "secret_rejected",
            lambda: self.runtime.append_event(
                thread["id"],
                role="user",
                content="safe prompt",
                metadata={"clientSecret": "do-not-store-this"},
            ),
        )
        self.assertEqual(self.runtime.get_thread(thread["id"])["eventCount"], 0)

    def test_documented_placeholders_are_allowed(self) -> None:
        thread = self.create_thread()["thread"]
        event = self.runtime.append_event(
            thread["id"],
            role="user",
            content="Set api_key=YOUR_API_KEY placeholder in the example only.",
        )["event"]
        self.assertIn("YOUR_API_KEY", event["content"])

    def test_request_turn_is_atomic_idempotent_and_blocks_second_active_turn(self) -> None:
        thread = self.create_thread()["thread"]
        first = self.runtime.request_turn(
            thread["id"], content="Inspect this project", idempotency_key="turn-request-0001"
        )
        replay = self.runtime.request_turn(
            thread["id"], content="Inspect this project", idempotency_key="turn-request-0001"
        )

        self.assertEqual(first["turn"]["status"], "queued")
        self.assertEqual(first["thread"]["status"], "queued")
        self.assertEqual(first["thread"]["eventCount"], 1)
        self.assertTrue(first["thread"]["canInterrupt"])
        self.assertFalse(first["thread"]["canArchive"])
        self.assertFalse(first["thread"]["canUpdateSettings"])
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(first["turn"]["id"], replay["turn"]["id"])
        self.assert_error(
            "thread_busy",
            lambda: self.runtime.request_turn(
                thread["id"], content="Second", idempotency_key="turn-request-0002"
            ),
        )
        self.assert_error(
            "thread_busy",
            lambda: self.runtime.update_settings(thread["id"], model="gpt-6-astra"),
        )

    def test_request_turn_reserves_user_start_and_terminal_event_headroom(self) -> None:
        with mock.patch.object(self.module, "MAX_EVENTS_PER_THREAD", 4):
            admitted = self.runtime.create_thread(
                "technical_consultant",
                title="Headroom admitted",
                idempotency_key="create-headroom-admitted-0001",
            )["thread"]
            self.runtime.append_event(
                admitted["id"], role="system", content="Earlier history"
            )
            requested = self.runtime.request_turn(
                admitted["id"],
                content="Use the final three event slots safely",
                idempotency_key="turn-headroom-admitted-0001",
            )
            turn_id = requested["turn"]["id"]
            self.runtime.update_turn_state(admitted["id"], turn_id, status="running")
            self.runtime.append_event(
                admitted["id"],
                role="system",
                event_type="system_notice",
                content="Turn started",
                metadata={"turnId": turn_id},
            )
            self.runtime.append_event(
                admitted["id"],
                role="assistant",
                content="Turn completed",
                metadata={"turnId": turn_id},
            )
            self.runtime.update_turn_state(admitted["id"], turn_id, status="completed")
            self.assertEqual(
                self.runtime.get_thread(admitted["id"], event_limit=4)["eventCount"], 4
            )

            replay = self.runtime.request_turn(
                admitted["id"],
                content="Use the final three event slots safely",
                idempotency_key="turn-headroom-admitted-0001",
            )
            self.assertTrue(replay["idempotentReplay"])

            rejected = self.runtime.create_thread(
                "technical_consultant",
                title="Headroom rejected",
                idempotency_key="create-headroom-rejected-0001",
            )["thread"]
            for index in range(2):
                self.runtime.append_event(
                    rejected["id"], role="system", content=f"Earlier history {index}"
                )
            self.assert_error(
                "history_limit_reached",
                lambda: self.runtime.request_turn(
                    rejected["id"],
                    content="This turn must not be partially admitted",
                    idempotency_key="turn-headroom-rejected-0001",
                ),
            )
            unchanged = self.runtime.get_thread(rejected["id"], event_limit=4)
            self.assertEqual(unchanged["eventCount"], 2)
            self.assertEqual(unchanged["turnCount"], 0)
            self.assertEqual(unchanged["status"], "idle")

    def test_turn_lifecycle_and_interrupt_marker_persist(self) -> None:
        thread = self.create_thread()["thread"]
        requested = self.runtime.request_turn(
            thread["id"], content="Run a long task", idempotency_key="turn-long-0001"
        )
        turn_id = requested["turn"]["id"]
        running = self.runtime.update_turn_state(
            thread["id"], turn_id, status="running"
        )
        self.assertEqual(running["thread"]["status"], "running")
        self.assertIsNotNone(running["turn"]["startedAt"])

        interrupted = self.runtime.request_interrupt(
            thread["id"],
            turn_id=turn_id,
            idempotency_key="interrupt-turn-0001",
        )
        replay = self.runtime.request_interrupt(
            thread["id"],
            turn_id=turn_id,
            idempotency_key="interrupt-turn-0001",
        )
        self.assertTrue(interrupted["turn"]["interruptRequested"])
        self.assertEqual(interrupted["thread"]["status"], "interrupt_requested")
        self.assertFalse(interrupted["thread"]["canInterrupt"])
        self.assertTrue(replay["idempotentReplay"])

        finished = self.runtime.update_turn_state(
            thread["id"], turn_id, status="cancelled"
        )
        self.assertEqual(finished["thread"]["status"], "idle")
        self.assertIsNone(finished["thread"]["activeTurn"])
        self.assertTrue(finished["thread"]["canArchive"])
        persisted = self.module.FullAgentRuntime(
            self.root,
            allowed_agents={"technical_consultant", "ea_developer"},
        ).get_thread(thread["id"])
        self.assertEqual(persisted["status"], "idle")

    def test_invalid_turn_transitions_and_failed_state_contract_are_rejected(self) -> None:
        thread = self.create_thread()["thread"]
        turn = self.runtime.request_turn(
            thread["id"], content="Task", idempotency_key="turn-state-0001"
        )["turn"]
        self.assert_error(
            "invalid_turn_transition",
            lambda: self.runtime.update_turn_state(
                thread["id"], turn["id"], status="completed"
            ),
        )
        self.assert_error(
            "invalid_request",
            lambda: self.runtime.update_turn_state(
                thread["id"], turn["id"], status="failed"
            ),
        )
        failed = self.runtime.update_turn_state(
            thread["id"], turn["id"], status="failed", error_code="runner_timeout"
        )
        self.assertEqual(failed["turn"]["errorCode"], "runner_timeout")

    def test_active_thread_cannot_be_archived_and_archived_thread_is_read_only(self) -> None:
        thread = self.create_thread()["thread"]
        active = self.runtime.request_turn(
            thread["id"], content="Task", idempotency_key="turn-archive-0001"
        )["turn"]
        self.assert_error(
            "thread_busy", lambda: self.runtime.archive_thread(thread["id"])
        )
        self.runtime.update_turn_state(
            thread["id"], active["id"], status="cancelled"
        )
        self.runtime.archive_thread(thread["id"])
        self.assert_error(
            "thread_archived",
            lambda: self.runtime.append_event(
                thread["id"], role="user", content="Cannot append"
            ),
        )

    def test_classification_requires_approval_for_external_destructive_and_computer_actions(self) -> None:
        external = self.runtime.classify_action(
            {
                "capability": "external_action",
                "operation": "publish release",
                "externalSideEffect": True,
            },
            mode="full",
        )
        destructive = self.runtime.classify_action(
            {
                "capability": "workspace_write",
                "operation": "delete workspace file",
                "destructive": True,
            },
            mode="workspace",
        )
        computer = self.runtime.classify_action(
            {"capability": "computer_use", "operation": "click confirmation"},
            mode="computer",
        )
        safe_read = self.runtime.classify_action(
            {"capability": "workspace_read", "operation": "inspect source"},
            mode="workspace",
        )

        self.assertTrue(external["approvalRequired"])
        self.assertEqual(external["riskLevel"], "high")
        self.assertTrue(destructive["approvalRequired"])
        self.assertTrue(computer["approvalRequired"])
        self.assertFalse(safe_read["approvalRequired"])
        self.assertFalse(safe_read["executionEnabled"])
        self.assertFalse(safe_read["executionAllowed"])

    def test_credential_and_live_trade_classification_is_critical(self) -> None:
        credentials = self.runtime.classify_action(
            {
                "capability": "external_action",
                "operation": "read password",
                "credentialAccess": True,
            },
            mode="full",
        )
        live_trade = self.runtime.classify_action(
            {
                "capability": "external_action",
                "operation": "place live trade order",
                "financialOrLiveTrade": True,
            },
            mode="full",
        )

        self.assertTrue(credentials["policyBlocked"])
        self.assertEqual(credentials["riskLevel"], "critical")
        self.assertTrue(live_trade["approvalRequired"])
        self.assertEqual(live_trade["riskLevel"], "critical")
        self.assertFalse(live_trade["executionAllowed"])

    def test_mode_capability_boundary_is_reported_without_executing(self) -> None:
        result = self.runtime.classify_action(
            {"capability": "computer_use", "operation": "view"}, mode="chat"
        )
        self.assertFalse(result["modeAllowsCapability"])
        self.assertFalse(result["executionAllowed"])
        self.assert_error(
            "tool_execution_unavailable", lambda: self.runtime.execute_tool("anything")
        )

    def test_workspace_classification_inspects_a_full_bounded_prompt(self) -> None:
        harmless_prefix = "Inspect the documented project structure. " * 20
        result = self.runtime.classify_action(
            {
                "capability": "workspace_write",
                "operation": harmless_prefix + "Do not delete files; report only.",
                "externalSideEffect": False,
                "destructive": False,
                "credentialAccess": False,
                "financialOrLiveTrade": False,
            },
            mode="workspace",
        )
        self.assertIn("destructive_action", result["reasonCodes"])

    def test_frontend_read_model_does_not_expose_storage_or_internal_digests(self) -> None:
        thread = self.create_thread()["thread"]
        self.runtime.append_event(
            thread["id"],
            role="assistant",
            content="Safe response",
            idempotency_key="event-private-0001",
        )
        model = self.runtime.get_thread(thread["id"])
        encoded = json.dumps(model, sort_keys=True)
        self.assertNotIn(str(self.root), encoded)
        self.assertNotIn("eventIdempotency", encoded)
        self.assertNotIn("turnIdempotency", encoded)
        self.assertNotIn("requestDigest", encoded)
        self.assertNotIn("event-private-0001", encoded)

    def test_backend_thread_binding_persists_but_is_never_frontend_visible(self) -> None:
        thread = self.create_thread()["thread"]
        backend_id = "019f8f3d-1234-7abc-9def-1234567890ab"

        bound = self.runtime.set_backend_thread_id(thread["id"], backend_id)
        self.assertEqual(
            self.runtime.get_backend_thread_id(thread["id"]), backend_id
        )
        self.assertNotIn("backendThreadId", bound)
        self.assertNotIn(
            backend_id, json.dumps(self.runtime.get_thread(thread["id"]), sort_keys=True)
        )

        reloaded = self.module.FullAgentRuntime(
            self.root,
            allowed_agents={"technical_consultant", "ea_developer"},
        )
        self.assertEqual(reloaded.get_backend_thread_id(thread["id"]), backend_id)
        archived = reloaded.archive_thread(thread["id"])
        self.assertTrue(archived["archived"])
        self.assertEqual(reloaded.get_backend_thread_id(thread["id"]), backend_id)

    def test_backend_thread_binding_rejects_rebind_paths_and_secrets(self) -> None:
        thread = self.create_thread()["thread"]
        self.runtime.set_backend_thread_id(
            thread["id"], "019f8f3d-1234-7abc-9def-1234567890ab"
        )
        self.assert_error(
            "backend_thread_conflict",
            lambda: self.runtime.set_backend_thread_id(
                thread["id"], "019f8f3d-ffff-7abc-9def-1234567890ab"
            ),
        )
        for unsafe in (
            "../outside/session",
            r"C:\\Users\\META\\session",
            "".join(("sk", "-", "abcdefghijklmnopqrstuvwxyz123456")),
        ):
            with self.subTest(unsafe=unsafe):
                error = self.assert_error(
                    "invalid_request"
                    if not unsafe.startswith("sk-")
                    else "secret_rejected",
                    lambda unsafe=unsafe: self.runtime.set_backend_thread_id(
                        thread["id"], unsafe
                    ),
                )
                self.assertIsNotNone(error)

    def test_quarantine_compare_and_clear_detaches_only_the_expected_backend_thread(self) -> None:
        thread = self.create_thread()["thread"]
        self.runtime.set_backend_thread_id(thread["id"], "backend-thread-safe-001")

        cleared = self.runtime.clear_backend_thread_id(
            thread["id"],
            expected_backend_thread_id="backend-thread-safe-001",
        )
        self.assertNotIn("backendThreadId", cleared)
        self.assertIsNone(self.runtime.get_backend_thread_id(thread["id"]))

        self.runtime.set_backend_thread_id(thread["id"], "backend-thread-safe-002")
        self.assert_error(
            "backend_thread_conflict",
            lambda: self.runtime.clear_backend_thread_id(
                thread["id"],
                expected_backend_thread_id="backend-thread-stale-001",
            ),
        )
        self.assertEqual(
            self.runtime.get_backend_thread_id(thread["id"]),
            "backend-thread-safe-002",
        )

    def test_store_write_is_atomic_and_leaves_no_temporary_files(self) -> None:
        self.create_thread()
        files = {path.name for path in self.root.iterdir()}
        self.assertIn(self.module.STORE_FILENAME, files)
        self.assertIn(self.module.LOCK_FILENAME, files)
        self.assertFalse(any(name.endswith(".tmp") for name in files))
        parsed = json.loads(
            (self.root / self.module.STORE_FILENAME).read_text(encoding="utf-8")
        )
        self.assertEqual(parsed["schemaVersion"], 1)

    def test_relative_storage_path_and_path_escape_are_rejected(self) -> None:
        self.assert_error(
            "unsafe_storage_path",
            lambda: self.module.FullAgentRuntime(Path("relative/runtime")),
        )
        escaped = self.root.parent / "child" / ".." / "escape"
        self.assert_error(
            "unsafe_storage_path", lambda: self.module.FullAgentRuntime(escaped)
        )

    def test_storage_symlink_is_rejected_when_platform_supports_it(self) -> None:
        target = Path(self.temporary_directory.name).resolve() / "target"
        target.mkdir()
        link = Path(self.temporary_directory.name).resolve() / "linked-runtime"
        try:
            link.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"Directory symlinks are unavailable: {error}")
        self.assert_error(
            "unsafe_storage_path", lambda: self.module.FullAgentRuntime(link)
        )

    def test_corrupt_store_fails_closed_without_overwrite(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        store = self.root / self.module.STORE_FILENAME
        store.write_text("not-json", encoding="utf-8")
        original = store.read_bytes()

        self.assert_error("store_corrupt", lambda: self.runtime.list_threads())
        self.assertEqual(store.read_bytes(), original)

    def test_parallel_appends_are_serialized_without_lost_events(self) -> None:
        thread = self.create_thread()["thread"]
        errors: list[BaseException] = []

        def append(index: int) -> None:
            try:
                self.runtime.append_event(
                    thread["id"],
                    role="assistant",
                    content=f"event {index}",
                    idempotency_key=f"parallel-event-{index:04d}",
                )
            except BaseException as error:  # captured for assertion on the main thread
                errors.append(error)

        workers = [threading.Thread(target=append, args=(index,)) for index in range(24)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=10)

        self.assertEqual(errors, [])
        model = self.runtime.get_thread(thread["id"])
        self.assertEqual(model["eventCount"], 24)
        self.assertEqual(len({event["id"] for event in model["events"]}), 24)

    def test_missing_thread_and_event_bounds_fail_with_stable_errors(self) -> None:
        self.assert_error(
            "thread_not_found", lambda: self.runtime.get_thread("fat_missing")
        )
        thread = self.create_thread()["thread"]
        self.assert_error(
            "request_too_large",
            lambda: self.runtime.append_event(
                thread["id"],
                role="user",
                content="x" * (self.module.MAX_CONTENT_CHARS + 1),
            ),
        )
        self.assert_error(
            "invalid_event_role",
            lambda: self.runtime.append_event(
                thread["id"], role="developer", content="not allowed"
            ),
        )


if __name__ == "__main__":
    unittest.main()
