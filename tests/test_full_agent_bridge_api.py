from __future__ import annotations

import contextlib
import importlib.util
import json
import re
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load bridge module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeGateway:
    """In-memory Codex App Server double. It never starts a real process."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self._lock = threading.Lock()
        self._thread_counter = 0
        self._turn_counter = 0
        self._turns: dict[str, dict] = {}
        self.block_waits = False
        self.wait_entered = threading.Event()
        self.wait_gate = threading.Event()
        self.interrupted = threading.Event()
        self.chat_items: list[dict] = []
        self.chat_items_truncated = False
        self.reply_text: str | None = None
        self.workspace_root: Path | None = None
        self.generated_output: tuple[str, bytes] | None = None

    def _record(self, method: str, **values: object) -> None:
        with self._lock:
            self.calls.append({"method": method, **values})

    def calls_for(self, method: str) -> list[dict]:
        with self._lock:
            return [dict(row) for row in self.calls if row.get("method") == method]

    def status(self) -> dict:
        self._record("status")
        return {
            "ok": True,
            "status": "ready",
            "process": {"status": "ready"},
            "authentication": {
                "authenticated": True,
                "requiresOpenaiAuth": True,
                "accountType": "chatgpt",
            },
        }

    def models(self) -> dict:
        self._record("models")
        return {
            "ok": True,
            "models": [
                {
                    "model": "gpt-6-sol",
                    "displayName": "GPT-6 Sol",
                    "isDefault": True,
                    "defaultReasoningEffort": "low",
                    "supportedReasoningEfforts": [
                        "low",
                        "medium",
                        "high",
                        "ultra",
                    ],
                    "inputModalities": ["text", "image"],
                },
                {
                    "model": "gpt-6-astra",
                    "displayName": "GPT-6 Astra",
                    "isDefault": False,
                    "defaultReasoningEffort": "xhigh",
                    "supportedReasoningEfforts": ["medium", "xhigh"],
                    "inputModalities": ["text", "image"],
                },
                {
                    "model": "untrusted-model",
                    "displayName": "Must be filtered",
                    "isDefault": False,
                    "supportedReasoningEfforts": ["medium"],
                },
            ],
        }

    def thread_start(self, policy_value: dict) -> dict:
        with self._lock:
            self._thread_counter += 1
            thread_id = f"gateway-thread-{self._thread_counter:04d}"
        self._record("thread_start", policy=dict(policy_value), threadId=thread_id)
        return {"ok": True, "thread": {"id": thread_id}}

    def thread_resume(self, thread_id: str, policy_value: dict) -> dict:
        self._record(
            "thread_resume",
            threadId=thread_id,
            policy=dict(policy_value),
        )
        return {"ok": True, "thread": {"id": thread_id}}

    def turn_start(
        self,
        thread_id: str,
        prompt: str,
        *,
        policy_value: dict,
        wait: bool,
        input_items: list[dict] | None = None,
    ) -> dict:
        copied_input_items = [dict(item) for item in (input_items or [])]
        with self._lock:
            self._turn_counter += 1
            turn_id = f"gateway-turn-{self._turn_counter:04d}"
            self._turns[turn_id] = {
                "threadId": thread_id,
                "prompt": prompt,
                "policy": dict(policy_value),
                "inputItems": copied_input_items,
            }
        self._record(
            "turn_start",
            threadId=thread_id,
            turnId=turn_id,
            prompt=prompt,
            policy=dict(policy_value),
            wait=wait,
            inputItems=copied_input_items,
        )
        return {"ok": True, "turn": {"id": turn_id, "status": "running"}}

    def turn_wait(self, turn_id: str, *, thread_id: str | None = None) -> dict:
        self._record("turn_wait", threadId=thread_id, turnId=turn_id)
        self.wait_entered.set()
        if self.block_waits:
            self.wait_gate.wait(5)
        turn = self._turns[turn_id]
        if self.interrupted.is_set():
            return {
                "ok": True,
                "status": "cancelled",
                "turn": {
                    "id": turn_id,
                    "status": "cancelled",
                    "assistantText": "",
                    "items": [],
                },
            }
        mode = str((turn.get("policy") or {}).get("mode") or "chat")
        if mode == "workspace" and self.workspace_root and self.generated_output:
            match = re.search(r"below `([^`]+)`", str(turn.get("prompt") or ""))
            if match:
                output_root = self.workspace_root.joinpath(*Path(match.group(1)).parts)
                output_root.mkdir(parents=True, exist_ok=True)
                output_root.joinpath(self.generated_output[0]).write_bytes(
                    self.generated_output[1]
                )
        items = (
            [{"type": "commandExecution", "status": "completed"}]
            if mode == "workspace"
            else [dict(item) for item in self.chat_items]
        )
        return {
            "ok": True,
            "status": "completed",
            "turn": {
                "id": turn_id,
                "status": "completed",
                "assistantText": self.reply_text or f"fake {mode} reply",
                "items": items,
                "itemsTruncated": self.chat_items_truncated,
            },
        }

    def turn_interrupt(self, thread_id: str, turn_id: str) -> dict:
        self._record("turn_interrupt", threadId=thread_id, turnId=turn_id)
        self.interrupted.set()
        self.wait_gate.set()
        return {"ok": True, "status": "interrupt_requested"}

    def close(self) -> None:
        self._record("close")
        self.wait_gate.set()


class UnconfirmedCloseGateway(FakeGateway):
    """Timeout double whose app-server process cannot be proven stopped."""

    def __init__(self) -> None:
        super().__init__()
        self.process_state = SimpleNamespace(
            status=SimpleNamespace(value="ready")
        )

    def turn_interrupt(self, thread_id: str, turn_id: str) -> dict:
        self._record("turn_interrupt", threadId=thread_id, turnId=turn_id)
        self.interrupted.set()
        # Intentionally leave the waiter blocked: interrupt_requested is only
        # an acknowledgement, not terminal evidence from the app-server.
        return {"ok": True, "status": "interrupt_requested"}

    def close(self) -> None:
        self._record("close")
        # Simulate a close request whose process is still reported as ready.
        # tearDown releases wait_gate after all fail-closed assertions finish.


class ApprovalOrderGateway(FakeGateway):
    """Records decline-before-interrupt ordering without an SDK process."""

    def approval_resolve(self, request_id: str, decision: str, **values: object) -> dict:
        self._record(
            "approval_resolve",
            requestId=request_id,
            decision=decision,
            **values,
        )
        return {
            "ok": True,
            "status": "resolution_accepted",
            "committed": True,
            "requestId": request_id,
        }


class PendingApprovalOrderGateway(ApprovalOrderGateway):
    """Simulates a decline callback that has not durably committed yet."""

    def approval_resolve(self, request_id: str, decision: str, **values: object) -> dict:
        self._record(
            "approval_resolve",
            requestId=request_id,
            decision=decision,
            **values,
        )
        return {
            "ok": True,
            "status": "resolution_pending",
            "committed": False,
            "requestId": request_id,
        }


class FullAgentBridgeApiTests(unittest.TestCase):
    THREAD_FIELDS_WITH_EVENTS = {
        "id",
        "agentId",
        "title",
        "model",
        "reasoning",
        "mode",
        "status",
        "lifecycle",
        "archived",
        "createdAt",
        "updatedAt",
        "revision",
        "eventCount",
        "turnCount",
        "activeTurn",
        "capabilities",
        "toolExecutionEnabled",
        "canInterrupt",
        "canContinue",
        "canArchive",
        "canUpdateSettings",
        "events",
        "eventOffset",
        "hasEarlierEvents",
    }
    THREAD_FIELDS_WITHOUT_EVENTS = THREAD_FIELDS_WITH_EVENTS - {
        "events",
        "eventOffset",
        "hasEarlierEvents",
    }

    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge("metafx_full_agent_bridge_api_tests")

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name).resolve()
        self.runtime_dir = self.root / "runtime"
        self.workspace_dir = self.root / "workspace"
        self.workspace_dir.mkdir(parents=True)
        self.gateway = FakeGateway()
        self.gateway.workspace_root = self.workspace_dir
        self.stack = contextlib.ExitStack()
        path_values = {
            "RUNTIME_DIR": self.runtime_dir,
            "MISSIONS_PATH": self.runtime_dir / "missions.json",
            "AUDIT_PATH": self.runtime_dir / "bridge-audit.jsonl",
            "RUNTIME_REPORTS_DIR": self.runtime_dir / "reports",
            "FULL_AGENT_RUNTIME_DIR": self.runtime_dir / "full-agent-runtime",
            "FULL_AGENT_ARTIFACTS_DIR": self.runtime_dir / "full-agent-media",
        }
        for name, value in path_values.items():
            self.stack.enter_context(mock.patch.object(self.bridge, name, value))
        self.stack.enter_context(
            mock.patch.object(self.bridge, "FULL_AGENT_RUNTIME_INSTANCE", None)
        )
        self.stack.enter_context(
            mock.patch.object(self.bridge, "FULL_AGENT_RUNTIME_RECONCILED", False)
        )
        self.stack.enter_context(
            mock.patch.object(self.bridge, "FULL_AGENT_ARTIFACT_STORE_INSTANCE", None)
        )
        self.stack.enter_context(
            mock.patch.object(self.bridge, "FULL_AGENT_GATEWAY_INSTANCE", self.gateway)
        )
        self.stack.enter_context(
            mock.patch.object(self.bridge, "FULL_AGENT_GATEWAY_QUARANTINED", False)
        )
        self.stack.enter_context(
            mock.patch.object(self.bridge, "FULL_AGENT_ACTIVE_TURNS", {})
        )
        self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_RUN_SEMAPHORE",
                threading.BoundedSemaphore(value=1),
            )
        )
        self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "REAL_RUN_SEMAPHORE",
                threading.BoundedSemaphore(value=1),
            )
        )
        self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "MISSIONS_READ_CACHE",
                {
                    "path": None,
                    "signature": None,
                    "missions": None,
                    "runtimeViews": {},
                    "serializedRuntimeResponses": {},
                },
            )
        )
        self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "codex_rate_limits",
                mock.Mock(return_value={"available": True, "windows": []}),
            )
        )
        self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "_collaboration_quota_gate",
                mock.Mock(return_value={"allowed": True}),
            )
        )
        self.stack.enter_context(
            mock.patch.object(
                self.bridge,
                "invalidate_codex_rate_limit_cache",
                mock.Mock(return_value=None),
            )
        )

    def tearDown(self) -> None:
        self.gateway.wait_gate.set()
        self._wait_for(
            lambda: not self.bridge.FULL_AGENT_ACTIVE_TURNS,
            timeout=2,
            fail=False,
        )
        self.stack.close()
        self.temporary_directory.cleanup()

    def _wait_for(self, predicate, *, timeout: float = 5, fail: bool = True) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return True
            time.sleep(0.01)
        if fail:
            self.fail("Timed out waiting for asynchronous Full Agent state")
        return False

    def _create_thread(
        self,
        *,
        agent_id: str = "manager",
        mode: str = "chat",
        title: str = "Bridge integration",
        model: str = "gpt-6-sol",
        reasoning: str = "medium",
    ) -> dict:
        return self.bridge.full_agent_create_thread(
            {
                "agentId": agent_id,
                "title": title,
                "model": model,
                "reasoning": reasoning,
                "mode": mode,
            }
        )["thread"]

    def _request_and_wait(
        self,
        thread_id: str,
        *,
        message: str,
        key: str,
        timeout: float = 5,
    ) -> tuple[dict, dict]:
        response = self.bridge.full_agent_request_turn(
            thread_id,
            {"message": message, "idempotencyKey": key},
        )
        self.assertEqual(response["status"], "queued")
        self._wait_for(
            lambda: self.bridge.full_agent_get_thread(thread_id)["thread"][
                "activeTurn"
            ]
            is None,
            timeout=timeout,
        )
        return response, self.bridge.full_agent_get_thread(thread_id)["thread"]

    def _audit_rows(self) -> list[dict]:
        if not self.bridge.AUDIT_PATH.exists():
            return []
        return [
            json.loads(line)
            for line in self.bridge.AUDIT_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def _seed_workspace_approval_state(
        self,
        *,
        suffix: str,
        cancel_requested: bool = False,
    ) -> tuple[object, dict, str, dict, dict]:
        runtime = self.bridge._full_agent_runtime()
        thread = runtime.create_thread(
            "ea_developer",
            title=f"workspace approval {suffix}",
            model="gpt-6-sol",
            reasoning="medium",
            mode="workspace",
        )["thread"]
        requested = runtime.request_turn(
            thread["id"],
            content="Exercise isolated approval callback only",
            idempotency_key=f"workspace-approval-{suffix}",
        )
        local_turn_id = requested["turn"]["id"]
        runtime.update_turn_state(thread["id"], local_turn_id, status="running")
        request = {
            "requestId": f"request-{suffix}",
            "requestDigest": "a" * 64,
            "decisionNonce": "b" * 32,
            "method": "item/commandExecution/requestApproval",
            "actionType": "command",
            "threadId": f"gateway-thread-{suffix}",
            "turnId": f"gateway-turn-{suffix}",
            "itemId": f"item-{suffix}",
        }
        mission_id = f"mission-{suffix}"
        generation = f"fgw-{suffix}"
        pending = {
            **request,
            "localThreadId": thread["id"],
            "localTurnId": local_turn_id,
            "missionId": mission_id,
            "gatewayGeneration": generation,
        }
        self.bridge.FULL_AGENT_ACTIVE_TURNS[local_turn_id] = {
            "threadId": thread["id"],
            "missionId": mission_id,
            "mode": "workspace",
            "gatewayGeneration": generation,
            "gatewayThreadId": request["threadId"],
            "gatewayTurnId": request["turnId"],
            "pendingApproval": pending,
            "approvalPreparing": None,
            "approvalDecisionCount": 0,
            "cancelRequested": cancel_requested,
        }
        return runtime, thread, local_turn_id, request, pending

    def _seed_interrupted_full_agent_turn(
        self,
        *,
        agent_id: str,
        tool_id: str,
        key: str,
    ) -> tuple[object, dict, dict, dict, str]:
        runtime = self.bridge._full_agent_runtime()
        message = f"Persist {agent_id} Full Agent turn before restart"
        thread = runtime.create_thread(
            agent_id,
            title=f"interrupted {agent_id} turn",
            model="gpt-6-sol",
            reasoning="medium",
            mode="chat",
        )["thread"]
        requested = runtime.request_turn(
            thread["id"],
            content=message,
            idempotency_key=key,
        )
        turn_id = requested["turn"]["id"]
        mission = self.bridge.create_mission(
            {
                "title": f"Full Agent Turn • {thread['title']}",
                "prompt": (
                    "Run one persistent read-only HQ chat turn with no tools. "
                    f"Prompt digest {self.bridge.payload_digest(message)}; "
                    f"prompt characters {len(message)}."
                ),
                "agentId": agent_id,
                "requester": "human",
                "toolId": tool_id,
                "targetId": self.bridge.role_default_target_id(agent_id),
                "risk": "low",
                "reportType": "prop_report",
                "idempotencyKey": f"full-agent-turn:{turn_id}",
            },
            status="running",
        )
        runtime.update_turn_state(thread["id"], turn_id, status="running")
        return runtime, thread, requested, mission, message

    def test_status_and_models_project_only_truthful_allowlisted_options(self) -> None:
        status = self.bridge.full_agent_runtime_status()
        self.assertEqual(set(status), {"ok", "runtime"})
        self.assertTrue(status["ok"])
        runtime = status["runtime"]
        modes = runtime["capabilityModes"]
        self.assertEqual(
            [item["id"] for item in modes],
            ["chat", "workspace", "computer", "full"],
        )
        projected = {item["id"]: item for item in modes}
        self.assertTrue(projected["chat"]["ready"])
        self.assertFalse(projected["workspace"]["ready"])
        self.assertFalse(projected["workspace"]["toolExecutionEnabled"])
        self.assertFalse(projected["computer"]["ready"])
        self.assertFalse(projected["full"]["ready"])
        self.assertFalse(runtime["approvalBrokerReady"])
        self.assertFalse(runtime["automaticExternalEffects"])
        self.assertTrue(runtime["chatReady"])
        self.assertFalse(runtime["fullAgentReady"])
        self.assertFalse(runtime["toolExecutionEnabled"])
        self.assertEqual(runtime["toolExecutionState"], "unavailable")
        self.assertIn("Chat พร้อมใช้งานแบบไม่เรียก Tool", runtime["messageTh"])
        self.assertIn("Workspace, Computer Use และ Full Access", runtime["messageTh"])
        self.assertIn("ถูกล็อกโดย Backend", runtime["messageTh"])
        self.assertEqual(runtime["workspaceSentinelStatus"], "failed_unapproved_write")
        self.assertFalse(runtime["workspaceSentinelVerified"])
        self.assertEqual(runtime["responseStringLimitChars"], 32768)
        self.assertIn(
            "live_write_sentinel_failed_unapproved_write",
            runtime["workspaceActivationBlockers"],
        )
        self.assertFalse(runtime["capabilities"]["computerUse"]["ready"])
        self.assertFalse(runtime["capabilities"]["mcp"]["ready"])
        self.assertFalse(runtime["capabilities"]["plugins"]["ready"])
        self.assertEqual(runtime["gatewayProcessStatus"], "ready")
        self.assertEqual(runtime["modelOptions"], ["gpt-6-sol", "gpt-6-astra"])
        self.assertEqual(
            runtime["reasoningOptions"], ["low", "medium", "high", "xhigh"]
        )

        catalog = self.bridge.full_agent_runtime_models()
        self.assertEqual(set(catalog), {"ok", "models", "reasoningOptions"})
        self.assertEqual(
            [row["id"] for row in catalog["models"]],
            ["gpt-6-sol", "gpt-6-astra"],
        )
        self.assertEqual(
            [row["id"] for row in catalog["reasoningOptions"]],
            ["low", "medium", "high", "xhigh"],
        )
        self.assertEqual(catalog["models"][0]["defaultReasoningEffort"], "low")
        self.assertEqual(catalog["models"][1]["defaultReasoningEffort"], "xhigh")
        self.assertEqual(
            [row["id"] for row in catalog["reasoningOptions"] if row["isDefault"]],
            ["low"],
        )
        self.assertNotIn(
            "ultra",
            {
                effort
                for model in catalog["models"]
                for effort in model["supportedReasoningEfforts"]
            },
        )
        self.assertEqual(len(self.gateway.calls_for("status")), 1)
        self.assertEqual(len(self.gateway.calls_for("models")), 2)

    def test_status_requires_safe_auth_and_create_resolves_the_live_default_model(self) -> None:
        unauthenticated = {
            "ok": True,
            "status": "ready",
            "process": {"status": "ready"},
            "authentication": {
                "authenticated": False,
                "requiresOpenaiAuth": True,
                "accountType": None,
            },
        }
        with mock.patch.object(self.gateway, "status", return_value=unauthenticated):
            runtime = self.bridge.full_agent_runtime_status()["runtime"]
        self.assertFalse(runtime["executionEnabled"])
        self.assertFalse(runtime["chatReady"])
        self.assertFalse(runtime["fullAgentReady"])
        self.assertFalse(runtime["toolExecutionEnabled"])
        self.assertEqual(runtime["modelOptions"], [])
        self.assertEqual(runtime["reasoningOptions"], [])
        self.assertTrue(
            all(not row["ready"] for row in runtime["capabilityModes"])
        )

        created = self.bridge.full_agent_create_thread(
            {
                "agentId": "manager",
                "title": "live default",
                "model": None,
                "reasoning": None,
                "mode": "chat",
            }
        )["thread"]
        self.assertEqual(created["model"], "gpt-6-sol")
        self.assertEqual(created["reasoning"], "low")
        astra = self.bridge.full_agent_create_thread(
            {
                "agentId": "manager",
                "title": "model-specific default",
                "model": "gpt-6-astra",
                "reasoning": None,
                "mode": "chat",
            }
        )["thread"]
        self.assertEqual(astra["reasoning"], "xhigh")
        with self.assertRaises(self.bridge.RequestError) as caught:
            self.bridge.full_agent_create_thread(
                {
                    "agentId": "manager",
                    "title": "unavailable model",
                    "model": "gpt-5.6-sol",
                    "reasoning": "medium",
                    "mode": "chat",
                }
            )
        self.assertEqual(caught.exception.status, 422)
        self.assertEqual(
            (caught.exception.response_payload or {}).get("code"),
            "model_unavailable",
        )

    def test_gpt_5_6_sol_uses_its_live_low_reasoning_default(self) -> None:
        live_catalog = {
            "ok": True,
            "models": [
                {
                    "model": "gpt-5.6-sol",
                    "displayName": "GPT-5.6 Sol",
                    "isDefault": True,
                    "defaultReasoningEffort": "low",
                    "supportedReasoningEfforts": ["low", "medium", "high"],
                }
            ],
        }
        with mock.patch.object(self.gateway, "models", return_value=live_catalog):
            catalog = self.bridge.full_agent_runtime_models()
            created = self.bridge.full_agent_create_thread(
                {
                    "agentId": "manager",
                    "title": "live gpt-5.6 default",
                    "model": None,
                    "reasoning": None,
                    "mode": "chat",
                }
            )["thread"]

        self.assertEqual(catalog["models"][0]["defaultReasoningEffort"], "low")
        self.assertEqual(created["model"], "gpt-5.6-sol")
        self.assertEqual(created["reasoning"], "low")

    def test_thread_crud_returns_exact_public_fields_and_rejects_shape_drift(self) -> None:
        created = self._create_thread(agent_id="manager", mode="chat")
        self.assertEqual(set(created), self.THREAD_FIELDS_WITH_EVENTS)
        self.assertEqual(created["agentId"], "manager")
        self.assertEqual(created["lifecycle"], "idle")
        self.assertFalse(created["toolExecutionEnabled"])
        self.assertNotIn("backendThreadId", created)

        listed = self.bridge.full_agent_list_threads("manager")
        self.assertEqual(set(listed), {"ok", "threads"})
        self.assertEqual(len(listed["threads"]), 1)
        self.assertEqual(
            set(listed["threads"][0]), self.THREAD_FIELDS_WITHOUT_EVENTS
        )

        fetched = self.bridge.full_agent_get_thread(created["id"])["thread"]
        self.assertEqual(set(fetched), self.THREAD_FIELDS_WITH_EVENTS)

        updated = self.bridge.full_agent_update_thread(
            created["id"],
            {
                "model": "gpt-6-astra",
                "reasoning": "xhigh",
                "mode": "chat",
                "expectedRevision": created["revision"],
            },
        )["thread"]
        self.assertEqual(set(updated), self.THREAD_FIELDS_WITH_EVENTS)
        self.assertEqual(updated["model"], "gpt-6-astra")
        self.assertEqual(updated["reasoning"], "xhigh")
        self.assertEqual(updated["mode"], "chat")
        self.assertFalse(updated["toolExecutionEnabled"])

        with self.assertRaises(self.bridge.RequestError) as stale_settings:
            self.bridge.full_agent_update_thread(
                created["id"],
                {
                    "model": "gpt-6-sol",
                    "reasoning": "medium",
                    "mode": "chat",
                    "expectedRevision": created["revision"],
                },
            )
        self.assertEqual(stale_settings.exception.status, 409)
        self.assertEqual(stale_settings.exception.code, "revision_conflict")

        archived = self.bridge.full_agent_archive_thread(
            created["id"],
            {"archived": True, "expectedRevision": updated["revision"]},
        )["thread"]
        self.assertEqual(set(archived), self.THREAD_FIELDS_WITH_EVENTS)
        self.assertTrue(archived["archived"])
        self.assertEqual(archived["lifecycle"], "archived")
        self.assertEqual(self.bridge.full_agent_list_threads("manager")["threads"], [])
        self.assertEqual(
            len(
                self.bridge.full_agent_list_threads(
                    "manager", include_archived=True
                )["threads"]
            ),
            1,
        )
        unarchived = self.bridge.full_agent_archive_thread(
            created["id"],
            {"archived": False, "expectedRevision": archived["revision"]},
        )["thread"]
        self.assertFalse(unarchived["archived"])
        self.assertEqual(unarchived["lifecycle"], "idle")
        self.assertEqual(
            [row["id"] for row in self.bridge.full_agent_list_threads("manager")["threads"]],
            [created["id"]],
        )

        with self.assertRaises(self.bridge.RequestError) as create_error:
            self.bridge.full_agent_create_thread(
                {
                    "agentId": "manager",
                    "title": "bad",
                    "model": "gpt-6-sol",
                    "reasoning": "medium",
                    "mode": "chat",
                    "accessToken": "must-not-be-accepted",
                }
            )
        self.assertEqual(create_error.exception.status, 422)
        with self.assertRaises(self.bridge.RequestError) as update_error:
            self.bridge.full_agent_update_thread(
                created["id"],
                {"model": "gpt-6-sol", "reasoning": "medium"},
            )
        self.assertEqual(update_error.exception.status, 422)
        with self.assertRaises(self.bridge.RequestError) as archive_error:
            self.bridge.full_agent_archive_thread(created["id"], {"force": True})
        self.assertEqual(archive_error.exception.status, 422)

    def test_chat_turn_finishes_with_mission_report_and_audit(self) -> None:
        cases = (("chat", "ceo", "Explain the current architecture", "chat-turn-0001"),)
        for mode, agent_id, message, key in cases:
            with self.subTest(mode=mode):
                thread = self._create_thread(
                    agent_id=agent_id,
                    mode=mode,
                    title=f"{mode} success",
                )
                queued, finished = self._request_and_wait(
                    thread["id"], message=message, key=key
                )
                self.assertEqual(queued["lifecycle"], "queued")
                self.assertEqual(finished["status"], "idle")
                self.assertEqual(finished["lifecycle"], "idle")
                self.assertEqual(finished["turnCount"], 1)
                self.assertIsNone(finished["activeTurn"])
                assistant_events = [
                    row for row in finished["events"] if row["role"] == "assistant"
                ]
                self.assertEqual(len(assistant_events), 1)
                self.assertEqual(
                    assistant_events[0]["content"], f"fake {mode} reply"
                )
                tool_events = [
                    row for row in finished["events"] if row["role"] == "tool"
                ]
                self.assertEqual(len(tool_events), 0)

                mission = self.bridge.find_mission(queued["missionId"])
                self.assertIsNotNone(mission)
                self.assertEqual(mission["status"], "completed")
                self.assertEqual(mission["owner"], agent_id)
                self.assertEqual(len(mission["reportIds"]), 1)
                report_path = (
                    self.bridge.RUNTIME_REPORTS_DIR
                    / f"{mission['reportIds'][0]}.json"
                )
                self.assertTrue(report_path.is_file())
                report = json.loads(report_path.read_text(encoding="utf-8"))
                self.assertEqual(report["linkedMissionId"], mission["id"])
                self.assertEqual(report["ownerAgentId"], agent_id)
                self.assertEqual(report["status"], "ready")
                self.assertEqual(report["metrics"]["mode"], mode)
                self.assertEqual(report["metrics"]["turnStatus"], "completed")

                related_audits = [
                    row
                    for row in self._audit_rows()
                    if row.get("missionId") == mission["id"]
                ]
                audit_types = {row.get("type") for row in related_audits}
                self.assertTrue(
                    {
                        "mission.created",
                        "full_agent.turn_queued",
                        "report.created",
                        "full_agent.turn_completed",
                    }.issubset(audit_types)
                )

        starts = self.gateway.calls_for("turn_start")
        self.assertEqual(len(starts), 1)
        by_mode = {row["policy"]["mode"]: row for row in starts}
        self.assertIn("Do not use tools or change files", by_mode["chat"]["prompt"])
        self.assertTrue(all(row["wait"] is False for row in starts))

    def test_worker_rechecks_authenticated_ready_gateway_before_dispatch(self) -> None:
        thread = self._create_thread(agent_id="ceo", mode="chat")
        unauthenticated = {
            "ok": False,
            "status": "auth_required",
            "process": {"status": "ready"},
            "authentication": {
                "authenticated": False,
                "requiresOpenaiAuth": True,
                "accountType": None,
            },
        }
        with mock.patch.object(
            self.gateway,
            "status",
            return_value=unauthenticated,
        ):
            queued, finished = self._request_and_wait(
                thread["id"],
                message="Do not dispatch without current authentication proof",
                key="dispatch-auth-proof-0001",
            )

        replay = self.bridge.full_agent_request_turn(
            thread["id"],
            {
                "message": "Do not dispatch without current authentication proof",
                "idempotencyKey": "dispatch-auth-proof-0001",
            },
        )
        self.assertEqual(finished["status"], "idle")
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["turn"]["status"], "failed")
        self.assertEqual(replay["turn"]["errorCode"], "auth_required")
        self.assertEqual(len(self.gateway.calls_for("thread_start")), 0)
        self.assertEqual(len(self.gateway.calls_for("thread_resume")), 0)
        self.assertEqual(len(self.gateway.calls_for("turn_start")), 0)
        mission = self.bridge.find_mission(queued["missionId"])
        self.assertEqual(mission["status"], "failed")

    def test_worker_rejects_empty_allowlisted_live_catalog_before_dispatch(self) -> None:
        thread = self._create_thread(agent_id="ceo", mode="chat")
        unapproved_catalog = {
            "ok": True,
            "models": [
                {
                    "model": "untrusted-model",
                    "displayName": "Not backend approved",
                    "isDefault": True,
                    "supportedReasoningEfforts": ["medium"],
                }
            ],
        }
        with mock.patch.object(
            self.gateway,
            "models",
            return_value=unapproved_catalog,
        ):
            queued, _finished = self._request_and_wait(
                thread["id"],
                message="Do not dispatch without an allowlisted live model",
                key="dispatch-model-proof-0001",
            )

        replay = self.bridge.full_agent_request_turn(
            thread["id"],
            {
                "message": "Do not dispatch without an allowlisted live model",
                "idempotencyKey": "dispatch-model-proof-0001",
            },
        )
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["turn"]["status"], "failed")
        self.assertEqual(
            replay["turn"]["errorCode"],
            "model_catalog_unavailable",
        )
        self.assertEqual(len(self.gateway.calls_for("thread_start")), 0)
        self.assertEqual(len(self.gateway.calls_for("thread_resume")), 0)
        self.assertEqual(len(self.gateway.calls_for("turn_start")), 0)
        mission = self.bridge.find_mission(queued["missionId"])
        self.assertEqual(mission["status"], "failed")

    def test_missing_mission_evidence_cannot_publish_turn_completed(self) -> None:
        thread = self._create_thread(agent_id="ceo", mode="chat")
        original_terminalize = self.bridge._full_agent_update_mission_terminal

        def omit_success_evidence(mission_id, **kwargs):
            if kwargs.get("succeeded") is True:
                return None
            return original_terminalize(mission_id, **kwargs)

        with mock.patch.object(
            self.bridge,
            "_full_agent_update_mission_terminal",
            side_effect=omit_success_evidence,
        ):
            queued, _finished = self._request_and_wait(
                thread["id"],
                message="Require durable lineage before declaring success",
                key="missing-evidence-turn-0001",
            )
            self._wait_for(lambda: not self.bridge.FULL_AGENT_ACTIVE_TURNS)

        replay = self.bridge.full_agent_request_turn(
            thread["id"],
            {
                "message": "Require durable lineage before declaring success",
                "idempotencyKey": "missing-evidence-turn-0001",
            },
        )
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["turn"]["status"], "failed")
        self.assertEqual(replay["turn"]["errorCode"], "mission_evidence_missing")
        mission = self.bridge.find_mission(queued["missionId"])
        self.assertEqual(mission["status"], "failed")
        self.assertEqual(len(mission["reportIds"]), 1)
        related = [
            row
            for row in self._audit_rows()
            if row.get("missionId") == queued["missionId"]
        ]
        self.assertFalse(
            any(row.get("type") == "full_agent.turn_completed" for row in related)
        )
        self.assertTrue(
            any(row.get("type") == "full_agent.turn_failed" for row in related)
        )

    def test_turn_idempotency_never_duplicates_gateway_mission_report_or_audit(self) -> None:
        thread = self._create_thread(agent_id="ceo", mode="chat")
        payload = {
            "message": "Give one bounded answer",
            "idempotencyKey": "idempotent-turn-0001",
        }
        first = self.bridge.full_agent_request_turn(thread["id"], payload)
        self._wait_for(
            lambda: self.bridge.full_agent_get_thread(thread["id"])["thread"][
                "activeTurn"
            ]
            is None
        )
        replay = self.bridge.full_agent_request_turn(thread["id"], payload)

        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["turn"]["id"], first["turn"]["id"])
        self.assertEqual(replay["turn"]["status"], "completed")
        self.assertEqual(len(self.gateway.calls_for("thread_start")), 1)
        self.assertEqual(len(self.gateway.calls_for("turn_start")), 1)
        self.assertEqual(len(self.bridge.load_missions()), 1)
        self.assertEqual(len(list(self.bridge.RUNTIME_REPORTS_DIR.glob("*.json"))), 1)
        audits = self._audit_rows()
        self.assertEqual(
            sum(row.get("type") == "full_agent.turn_queued" for row in audits), 1
        )
        self.assertEqual(
            sum(row.get("type") == "full_agent.turn_completed" for row in audits),
            1,
        )

    def test_full_agent_response_redacts_local_paths_but_preserves_public_urls(self) -> None:
        https_url = "https://docs.example.com/guide/setup?next=/api/help"
        api_path = "/api/agent-runtime/threads/fat_demo/artifacts/art_demo"
        leaked_paths = (
            "C:/Users/META/project/report.txt",
            r"D:\private\project\report.txt",
            r"\\server\share\private\report.txt",
            "//server/share/private/report.txt",
            "file:///C:/Users/META/private/report.txt",
            "file://server/share/private/report.txt",
            "/mnt/c/Users/META/private/report.txt",
            "/var/lib/metafx/private/report.txt",
            "/workspace/customer/private/report.txt",
        )
        self.gateway.reply_text = "\n".join((*leaked_paths, https_url, api_path))
        thread = self._create_thread(agent_id="ceo", mode="chat")
        queued, finished = self._request_and_wait(
            thread["id"],
            message="Return a bounded path-redaction fixture",
            key="full-agent-path-redaction-0001",
        )
        assistant = [
            event for event in finished["events"] if event.get("role") == "assistant"
        ][-1]
        reply = assistant["content"]
        self.assertGreaterEqual(reply.count("[REDACTED_PATH]"), len(leaked_paths))
        for leaked in leaked_paths:
            self.assertNotIn(leaked, reply)
        self.assertIn(https_url, reply)
        self.assertIn(api_path, reply)

        runtime = self.bridge._full_agent_runtime()
        runtime.append_event(
            thread["id"],
            role="system",
            content="legacy diagnostic at /private/legacy/runtime/error.log",
            event_type="system_notice",
            metadata={"diagnostic": "file:///tmp/private-error.txt"},
            idempotency_key="legacy-path-redaction-fixture",
        )
        public = self.bridge.full_agent_get_thread(thread["id"])["thread"]
        public_json = json.dumps(public)
        self.assertNotIn("/private/legacy/runtime/error.log", public_json)
        self.assertNotIn("file:///tmp/private-error.txt", public_json)
        self.assertIn("[REDACTED_PATH]", public_json)

        runtime.append_event(
            thread["id"],
            role="assistant",
            content=f"legacy replay /srv/private/result.txt {https_url}",
            event_type="message",
            metadata={"turnId": queued["turn"]["id"]},
            idempotency_key="legacy-replay-path-redaction-fixture",
        )
        replay = self.bridge.full_agent_request_turn(
            thread["id"],
            {
                "message": "Return a bounded path-redaction fixture",
                "idempotencyKey": "full-agent-path-redaction-0001",
            },
        )
        self.assertTrue(replay["idempotentReplay"])
        self.assertNotIn("/srv/private/result.txt", replay["reply"])
        self.assertIn("[REDACTED_PATH]", replay["reply"])
        self.assertIn(https_url, replay["reply"])

    def test_idempotent_replay_reply_is_bound_to_the_original_turn(self) -> None:
        thread = self._create_thread(agent_id="ceo", mode="chat")
        first_payload = {
            "message": "Return the first distinct answer",
            "idempotencyKey": "replay-original-turn-0001",
        }
        self.gateway.reply_text = "first persisted reply"
        first, _ = self._request_and_wait(
            thread["id"],
            message=first_payload["message"],
            key=first_payload["idempotencyKey"],
            timeout=15,
        )

        self.gateway.reply_text = "second persisted reply"
        self._request_and_wait(
            thread["id"],
            message="Return the second distinct answer",
            key="replay-original-turn-0002",
            timeout=15,
        )
        runtime = self.bridge._full_agent_runtime()
        for index in range(205):
            runtime.append_event(
                thread["id"],
                role="system",
                content=f"bounded filler event {index}",
                event_type="system_notice",
                metadata={"filler": index},
                idempotency_key=f"replay-filler:{index}",
            )
        recent = runtime.get_thread(thread["id"])
        self.assertFalse(
            any(
                event.get("role") == "assistant"
                and event.get("metadata", {}).get("turnId") == first["turn"]["id"]
                for event in recent["events"]
            )
        )

        replay = self.bridge.full_agent_request_turn(thread["id"], first_payload)
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["turn"]["id"], first["turn"]["id"])
        self.assertEqual(replay["reply"], "first persisted reply")

    def test_chat_rejects_gateway_tool_activity_and_failed_replay_uses_its_error(self) -> None:
        thread = self._create_thread(agent_id="ceo", mode="chat")
        self.gateway.reply_text = "unrelated earlier assistant reply"
        self._request_and_wait(
            thread["id"],
            message="Create an earlier successful answer",
            key="tool-guard-prior-turn-0001",
        )

        self.gateway.chat_items = [
            {"type": "commandExecution", "status": "completed"}
        ]
        self.gateway.reply_text = "must not be persisted"
        failed_payload = {
            "message": "This chat must remain tool free",
            "idempotencyKey": "tool-guard-failed-turn-0001",
        }
        queued, finished = self._request_and_wait(
            thread["id"],
            message=failed_payload["message"],
            key=failed_payload["idempotencyKey"],
        )

        failed_turn = next(
            turn for turn in finished["events"]
            if turn.get("metadata", {}).get("turnId") == queued["turn"]["id"]
            and turn.get("type") == "error"
        )
        self.assertEqual(
            failed_turn["metadata"]["errorCode"],
            "unexpected_tool_activity",
        )
        self.assertFalse(
            any(
                event.get("role") in {"assistant", "tool"}
                and event.get("metadata", {}).get("turnId") == queued["turn"]["id"]
                for event in finished["events"]
            )
        )
        mission = self.bridge.find_mission(queued["missionId"])
        self.assertEqual(mission["status"], "failed")
        self.assertEqual(mission["errorCode"], "unexpected_tool_activity")
        self.assertEqual(len(mission["reportIds"]), 1)

        replay = self.bridge.full_agent_request_turn(thread["id"], failed_payload)
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["turn"]["status"], "failed")
        self.assertEqual(
            replay["reply"],
            self.bridge._full_agent_error_message("unexpected_tool_activity"),
        )
        self.assertNotEqual(replay["reply"], "unrelated earlier assistant reply")

    def test_chat_rejects_truncated_gateway_item_projection(self) -> None:
        thread = self._create_thread(agent_id="ceo", mode="chat")
        self.gateway.chat_items = [
            {"type": "reasoning", "status": "completed"}
        ]
        self.gateway.chat_items_truncated = True
        queued, finished = self._request_and_wait(
            thread["id"],
            message="Do not certify an incomplete item projection",
            key="tool-guard-truncated-items-0001",
        )

        errors = [
            event
            for event in finished["events"]
            if event.get("type") == "error"
            and event.get("metadata", {}).get("turnId") == queued["turn"]["id"]
        ]
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors[0]["metadata"]["errorCode"],
            "unexpected_tool_activity",
        )
        mission = self.bridge.find_mission(queued["missionId"])
        self.assertEqual(mission["status"], "failed")
        self.assertEqual(mission["errorCode"], "unexpected_tool_activity")

    def test_workspace_fails_closed_until_interactive_approval_broker_exists(self) -> None:
        with self.assertRaises(self.bridge.RequestError) as caught:
            self._create_thread(agent_id="ea_developer", mode="workspace")
        self.assertEqual(caught.exception.status, 409)
        self.assertEqual(
            (caught.exception.response_payload or {}).get("code"),
            "approval_broker_required",
        )
        self.assertEqual(len(self.gateway.calls_for("thread_start")), 0)
        self.assertEqual(len(self.gateway.calls_for("turn_start")), 0)
        self.assertEqual(self.bridge.load_missions(), [])

    def test_workspace_turn_publishes_only_its_bounded_output_artifacts(self) -> None:
        self.gateway.generated_output = (
            "deliverable.md",
            b"# Verified workspace deliverable",
        )
        with (
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_INTERACTIVE_APPROVAL_BROKER_ENABLED",
                True,
            ),
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_EXECUTABLE_MODES",
                frozenset({"chat", "workspace"}),
            ),
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_WORKSPACE_ROOTS",
                (self.workspace_dir,),
            ),
        ):
            thread = self._create_thread(agent_id="ea_developer", mode="workspace")
            queued, finished = self._request_and_wait(
                thread["id"],
                message="Create one Markdown deliverable in the provided output directory.",
                key="workspace-output-artifact-0001",
            )

            assistant = [
                event
                for event in finished["events"]
                if event.get("role") == "assistant"
                and event.get("metadata", {}).get("turnId") == queued["turn"]["id"]
            ]
            self.assertEqual(len(assistant), 1)
            artifacts = assistant[0]["metadata"]["artifacts"]
            self.assertEqual(len(artifacts), 1)
            artifact = artifacts[0]
            self.assertEqual(artifact["name"], "deliverable.md")
            self.assertEqual(artifact["direction"], "output")
            self.assertEqual(artifact["kind"], "text")
            self.assertTrue(artifact["available"])
            self.assertNotIn("path", artifact)
            self.assertNotIn(str(self.root), json.dumps(artifact))

            binding = self.bridge._full_agent_artifact_private_binding(artifact["id"])
            self.assertEqual(binding["threadId"], thread["id"])
            self.assertEqual(binding["turnId"], queued["turn"]["id"])
            resolved = self.bridge.full_agent_resolve_artifact(
                thread["id"], artifact["id"]
            )
            self.assertIsNotNone(resolved)
            self.assertEqual(resolved[0].read_bytes(), self.gateway.generated_output[1])
            with self.assertRaises(self.bridge.FullAgentArtifactError):
                self.bridge._full_agent_artifact_store().resolve(
                    thread["id"], "turn_wrong_owner", artifact["id"]
                )

            replay = self.bridge.full_agent_request_turn(
                thread["id"],
                {
                    "message": "Create one Markdown deliverable in the provided output directory.",
                    "idempotencyKey": "workspace-output-artifact-0001",
                },
            )
            self.assertTrue(replay["idempotentReplay"])
            self.assertEqual(replay["artifacts"], artifacts)

            relevant_audit = [
                row
                for row in self._audit_rows()
                if row.get("turnId") == queued["turn"]["id"]
                and row.get("type")
                in {
                    "full_agent.artifact_published",
                    "full_agent.output_workspace_cleaned",
                }
            ]
            published_audit = [
                row
                for row in relevant_audit
                if row.get("type") == "full_agent.artifact_published"
            ]
            self.assertEqual(len(published_audit), 1)
            self.assertEqual(published_audit[0]["artifactId"], artifact["id"])
            self.assertEqual(published_audit[0]["expiresAt"], artifact["expiresAt"])
            self.assertTrue(
                any(
                    row.get("type") == "full_agent.output_workspace_cleaned"
                    for row in relevant_audit
                )
            )
            external_json = json.dumps(
                {"assistant": assistant[0], "replay": replay, "audit": relevant_audit}
            )
            self.assertNotIn(str(self.root), external_json)
            self.assertNotIn("sourcePath", external_json)

        prompt = self.gateway.calls_for("turn_start")[0]["prompt"]
        self.assertIn("Files outside that exact per-turn directory will not be published", prompt)
        self.assertNotIn(thread["id"], prompt)
        self.assertNotIn(queued["turn"]["id"], prompt)
        output_match = re.search(r"below `([^`]+)`", prompt)
        self.assertIsNotNone(output_match)
        output_root = self.workspace_dir.joinpath(*Path(output_match.group(1)).parts)
        self.assertFalse(output_root.exists())

    def test_output_scan_rejects_excess_file_count_before_publication(self) -> None:
        with mock.patch.object(
            self.bridge,
            "FULL_AGENT_WORKSPACE_ROOTS",
            (self.workspace_dir,),
        ):
            turn_root, relative = self.bridge._full_agent_workspace_output_directory(
                "fat_output_scan_thread",
                "turn_output_scan_0001",
            )
        self.assertTrue(relative.startswith(".full-agent-outputs/"))
        (turn_root / "one.txt").write_text("one\n", encoding="utf-8")
        (turn_root / "two.txt").write_text("two\n", encoding="utf-8")
        with (
            mock.patch.object(
                self.bridge, "FULL_AGENT_MAX_OUTPUT_ARTIFACTS_PER_TURN", 1
            ),
            self.assertRaises(self.bridge.FullAgentArtifactError) as caught,
        ):
            self.bridge._full_agent_output_files(turn_root)
        self.assertEqual(caught.exception.code, "too_many_output_artifacts")
        self.assertFalse(
            any((self.runtime_dir / "full-agent-media").glob("art_*.meta.json"))
        )

    def test_attachment_batch_clone_failure_keeps_every_draft_reusable(self) -> None:
        thread = self._create_thread(agent_id="manager", mode="chat")
        png = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
            "AAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        uploaded = [
            self.bridge.full_agent_upload_attachment(
                thread["id"],
                {
                    "fileName": f"chart-{index}.png",
                    "mediaType": "image/png",
                    "dataBase64": png,
                },
            )["attachment"]
            for index in range(2)
        ]
        resolved = self.bridge._full_agent_resolve_turn_attachments(
            thread, [item["id"] for item in uploaded]
        )
        store = self.bridge._full_agent_artifact_store()
        original_save = store.save_upload
        target_calls = 0

        def fail_second_target(*args, **kwargs):
            nonlocal target_calls
            if len(args) > 1 and args[1] == "turn_batch_target_0001":
                target_calls += 1
                if target_calls == 2:
                    raise self.bridge.FullAgentArtifactError(
                        "atomic_finalize_failed", "simulated clone failure", status=500
                    )
            return original_save(*args, **kwargs)

        with mock.patch.object(store, "save_upload", side_effect=fail_second_target):
            with self.assertRaises(self.bridge.FullAgentArtifactError):
                self.bridge._full_agent_bind_turn_attachments(
                    thread["id"], "turn_batch_target_0001", resolved
                )

        for item in uploaded:
            binding = self.bridge._full_agent_artifact_private_binding(item["id"])
            path, metadata = store.resolve(
                thread["id"], binding["turnId"], item["id"]
            )
            self.assertTrue(path.is_file())
            self.assertEqual(metadata["state"], "ready")
        ready_target = []
        for metadata_path in store.root.glob("att_*.meta.json"):
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata.get("turnId") == "turn_batch_target_0001":
                ready_target.append(metadata)
        self.assertEqual(ready_target, [])

    def test_output_batch_failure_publishes_no_partial_audit_or_artifact(self) -> None:
        with mock.patch.object(
            self.bridge, "FULL_AGENT_WORKSPACE_ROOTS", (self.workspace_dir,)
        ):
            turn_root, _relative = self.bridge._full_agent_workspace_output_directory(
                "fat_output_batch_thread", "turn_output_batch_0001"
            )
        (turn_root / "first.txt").write_text("safe\n", encoding="utf-8")
        (turn_root / "second.pdf").write_bytes(b"not a pdf")

        with self.assertRaises(self.bridge.FullAgentArtifactError) as failed:
            self.bridge._full_agent_publish_turn_outputs(
                "fat_output_batch_thread", "turn_output_batch_0001", turn_root
            )

        self.assertIn(
            failed.exception.code, {"invalid_file_content", "artifact_changed"}
        )
        self.assertFalse(turn_root.exists())
        self.assertEqual(
            [
                row
                for row in self._audit_rows()
                if row.get("type") == "full_agent.artifact_published"
            ],
            [],
        )
        self.assertEqual(
            list((self.runtime_dir / "full-agent-media").glob("art_*.meta.json")),
            [],
        )

    def test_cancel_requested_blocks_accept_before_any_durable_approval_evidence(self) -> None:
        runtime, thread, local_turn_id, request, _pending = (
            self._seed_workspace_approval_state(
                suffix="cancel-race-1",
                cancel_requested=True,
            )
        )
        with (
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_INTERACTIVE_APPROVAL_BROKER_ENABLED",
                True,
            ),
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_EXECUTABLE_MODES",
                frozenset({"chat", "workspace"}),
            ),
        ):
            accepted = self.bridge._full_agent_approval_resolved(
                "fgw-cancel-race-1",
                request,
                {
                    "decision": "accept_once",
                    "idempotencyKey": "approval-cancel-race-accept-1",
                    "reason": "user_approved_once",
                },
            )
            self.assertFalse(accepted)
            self.assertEqual(
                [
                    row
                    for row in self._audit_rows()
                    if row.get("type") == "full_agent.approval_decided"
                ],
                [],
            )
            self.assertFalse(
                any(
                    event.get("type") == "approval_decision"
                    for event in runtime.get_thread(thread["id"], include_events=True)[
                        "events"
                    ]
                )
            )

            declined = self.bridge._full_agent_approval_resolved(
                "fgw-cancel-race-1",
                request,
                {
                    "decision": "decline",
                    "idempotencyKey": "stop-request-cancel-race-1",
                    "reason": "user_interrupt",
                },
            )
            self.assertTrue(declined)
        decisions = [
            row
            for row in self._audit_rows()
            if row.get("type") == "full_agent.approval_decided"
        ]
        self.assertEqual([row.get("decision") for row in decisions], ["decline"])
        self.assertIsNone(
            self.bridge.FULL_AGENT_ACTIVE_TURNS[local_turn_id]["pendingApproval"]
        )
        self.bridge.FULL_AGENT_ACTIVE_TURNS.pop(local_turn_id, None)

    def test_audit_commit_is_authoritative_when_runtime_projection_fails(self) -> None:
        runtime, _thread, local_turn_id, request, _pending = (
            self._seed_workspace_approval_state(suffix="audit-first-1")
        )
        with (
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_INTERACTIVE_APPROVAL_BROKER_ENABLED",
                True,
            ),
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_EXECUTABLE_MODES",
                frozenset({"chat", "workspace"}),
            ),
            mock.patch.object(
                runtime,
                "append_event",
                side_effect=RuntimeError("projection unavailable"),
            ),
        ):
            resolved = self.bridge._full_agent_approval_resolved(
                "fgw-audit-first-1",
                request,
                {
                    "decision": "accept_once",
                    "idempotencyKey": "approval-audit-first-1",
                    "reason": "user_approved_once",
                },
            )
        self.assertTrue(resolved)
        decisions = [
            row
            for row in self._audit_rows()
            if row.get("type") == "full_agent.approval_decided"
        ]
        self.assertEqual([row.get("decision") for row in decisions], ["accept_once"])
        self.assertIsNone(
            self.bridge.FULL_AGENT_ACTIVE_TURNS[local_turn_id]["pendingApproval"]
        )
        self.bridge.FULL_AGENT_ACTIVE_TURNS.pop(local_turn_id, None)

    def test_audit_failure_forces_decline_without_approved_runtime_evidence(self) -> None:
        runtime, thread, local_turn_id, request, _pending = (
            self._seed_workspace_approval_state(suffix="audit-failure-1")
        )
        original_append_event = runtime.append_event
        with (
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_INTERACTIVE_APPROVAL_BROKER_ENABLED",
                True,
            ),
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_EXECUTABLE_MODES",
                frozenset({"chat", "workspace"}),
            ),
            mock.patch.object(
                self.bridge,
                "append_audit_once",
                side_effect=RuntimeError("audit fsync failed"),
            ),
            mock.patch.object(
                runtime,
                "append_event",
                wraps=original_append_event,
            ) as append_event,
        ):
            resolved = self.bridge._full_agent_approval_resolved(
                "fgw-audit-failure-1",
                request,
                {
                    "decision": "accept_once",
                    "idempotencyKey": "approval-audit-failure-1",
                    "reason": "user_approved_once",
                },
            )
        self.assertFalse(resolved)
        append_event.assert_not_called()
        self.assertEqual(self._audit_rows(), [])
        self.assertFalse(
            any(
                event.get("type") == "approval_decision"
                for event in runtime.get_thread(thread["id"], include_events=True)[
                    "events"
                ]
            )
        )
        self.assertIsNotNone(
            self.bridge.FULL_AGENT_ACTIVE_TURNS[local_turn_id]["pendingApproval"]
        )
        self.bridge.FULL_AGENT_ACTIVE_TURNS.pop(local_turn_id, None)

    def test_non_chat_modes_are_rejected_at_create_and_turn_boundaries(self) -> None:
        for mode in ("workspace", "computer", "full"):
            with self.subTest(mode=mode):
                with self.assertRaises(self.bridge.RequestError) as caught:
                    self._create_thread(agent_id="manager", mode=mode)
                self.assertEqual(caught.exception.status, 409)
                self.assertEqual(
                    (caught.exception.response_payload or {}).get("code"),
                    "approval_broker_required",
                )

                legacy = self.bridge._full_agent_runtime().create_thread(
                    "manager",
                    title=f"legacy {mode}",
                    model="gpt-6-sol",
                    reasoning="medium",
                    mode=mode,
                )["thread"]
                rejected = self.bridge.full_agent_request_turn(
                    legacy["id"],
                    {
                        "message": "Try unavailable capability",
                        "idempotencyKey": f"legacy-{mode}-turn-0001",
                    },
                )
                self.assertEqual(rejected["status"], "failed")
                self.assertEqual(rejected["lifecycle"], "failed")
                self.assertIn("ยังไม่พร้อม", rejected["reply"])
        self.assertEqual(len(self.gateway.calls_for("turn_start")), 0)
        self.assertEqual(self.bridge.load_missions(), [])

    def test_interrupt_reaches_gateway_and_finishes_fail_closed(self) -> None:
        self.gateway.block_waits = True
        thread = self._create_thread(agent_id="ceo", mode="chat")
        queued = self.bridge.full_agent_request_turn(
            thread["id"],
            {
                "message": "Explain one bounded architecture detail",
                "idempotencyKey": "interrupt-turn-0001",
            },
        )
        self.assertTrue(self.gateway.wait_entered.wait(3))
        self._wait_for(
            lambda: bool(
                self.bridge.FULL_AGENT_ACTIVE_TURNS.get(queued["turn"]["id"], {}).get(
                    "gatewayTurnId"
                )
            )
        )

        interrupted = self.bridge.full_agent_interrupt_thread(thread["id"], {})
        self.assertEqual(interrupted["status"], "interrupt_requested")
        self.assertTrue(interrupted["adapterConfirmed"])
        self.assertEqual(interrupted["turnId"], queued["turn"]["id"])
        self._wait_for(lambda: not self.bridge.FULL_AGENT_ACTIVE_TURNS)

        replay = self.bridge.full_agent_request_turn(
            thread["id"],
            {
                "message": "Explain one bounded architecture detail",
                "idempotencyKey": "interrupt-turn-0001",
            },
        )
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["turn"]["status"], "failed")
        self.assertEqual(replay["turn"]["errorCode"], "turn_interrupted")
        self.assertEqual(len(self.gateway.calls_for("turn_interrupt")), 1)
        mission = self.bridge.find_mission(queued["missionId"])
        self.assertEqual(mission["status"], "failed")
        self.assertEqual(len(mission["reportIds"]), 1)
        report = json.loads(
            (
                self.bridge.RUNTIME_REPORTS_DIR / f"{mission['reportIds'][0]}.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["metrics"]["errorCode"], "turn_interrupted")

    def test_interrupt_declines_pending_approval_before_sdk_interrupt(self) -> None:
        order_gateway = ApprovalOrderGateway()
        self.gateway = order_gateway
        runtime, thread, local_turn_id, _request, pending = (
            self._seed_workspace_approval_state(suffix="stop-order-1")
        )
        del runtime
        with (
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_GATEWAY_INSTANCE",
                order_gateway,
            ),
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_GATEWAY_GENERATION",
                pending["gatewayGeneration"],
            ),
        ):
            interrupted = self.bridge.full_agent_interrupt_thread(thread["id"], {})
        self.assertEqual(interrupted["status"], "interrupt_requested")
        ordered_methods = [
            row["method"]
            for row in order_gateway.calls
            if row["method"] in {"approval_resolve", "turn_interrupt"}
        ]
        self.assertEqual(ordered_methods, ["approval_resolve", "turn_interrupt"])
        resolution = order_gateway.calls_for("approval_resolve")[0]
        self.assertEqual(resolution["decision"], "decline")
        self.assertTrue(
            self.bridge.FULL_AGENT_ACTIVE_TURNS[local_turn_id]["cancelRequested"]
        )
        self.bridge.FULL_AGENT_ACTIVE_TURNS.pop(local_turn_id, None)

    def test_interrupt_marks_cancel_before_runtime_persistence_can_race_accept(self) -> None:
        order_gateway = ApprovalOrderGateway()
        self.gateway = order_gateway
        runtime, thread, local_turn_id, request, pending = (
            self._seed_workspace_approval_state(suffix="stop-race-1")
        )
        original_request_interrupt = runtime.request_interrupt
        accept_result: list[bool] = []

        def request_interrupt_with_accept_race(*args: object, **kwargs: object) -> dict:
            accept_result.append(
                self.bridge._full_agent_approval_resolved(
                    pending["gatewayGeneration"],
                    request,
                    {
                        "decision": "accept_once",
                        "idempotencyKey": "approval-stop-race-accept-1",
                        "reason": "user_approved_once",
                    },
                )
            )
            return original_request_interrupt(*args, **kwargs)

        with (
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_GATEWAY_INSTANCE",
                order_gateway,
            ),
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_GATEWAY_GENERATION",
                pending["gatewayGeneration"],
            ),
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_INTERACTIVE_APPROVAL_BROKER_ENABLED",
                True,
            ),
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_EXECUTABLE_MODES",
                frozenset({"chat", "workspace"}),
            ),
            mock.patch.object(
                runtime,
                "request_interrupt",
                side_effect=request_interrupt_with_accept_race,
            ),
        ):
            interrupted = self.bridge.full_agent_interrupt_thread(thread["id"], {})

        self.assertEqual(interrupted["status"], "interrupt_requested")
        self.assertEqual(accept_result, [False])
        decisions = [
            row
            for row in self._audit_rows()
            if row.get("type") == "full_agent.approval_decided"
        ]
        self.assertFalse(any(row.get("decision") == "accept_once" for row in decisions))
        decline_requests = [
            row
            for row in self._audit_rows()
            if row.get("type") == "full_agent.pending_approval_decline_requested"
        ]
        self.assertEqual(len(decline_requests), 1)
        self.assertTrue(decline_requests[0].get("resolved"))
        ordered_methods = [
            row["method"]
            for row in order_gateway.calls
            if row["method"] in {"approval_resolve", "turn_interrupt"}
        ]
        self.assertEqual(ordered_methods, ["approval_resolve", "turn_interrupt"])
        self.bridge.FULL_AGENT_ACTIVE_TURNS.pop(local_turn_id, None)

    def test_interrupt_quarantines_instead_of_interrupting_when_decline_is_pending(self) -> None:
        pending_gateway = PendingApprovalOrderGateway()
        self.gateway = pending_gateway
        _runtime, thread, local_turn_id, _request, pending = (
            self._seed_workspace_approval_state(suffix="stop-pending-1")
        )
        with (
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_GATEWAY_INSTANCE",
                pending_gateway,
            ),
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_GATEWAY_GENERATION",
                pending["gatewayGeneration"],
            ),
        ):
            interrupted = self.bridge.full_agent_interrupt_thread(thread["id"], {})
            self.assertIsNone(self.bridge.FULL_AGENT_GATEWAY_INSTANCE)
        self.assertEqual(interrupted["status"], "interrupt_requested")
        self.assertEqual(len(pending_gateway.calls_for("approval_resolve")), 1)
        self.assertEqual(pending_gateway.calls_for("turn_interrupt"), [])
        self.assertEqual(len(pending_gateway.calls_for("close")), 1)
        interrupt_audits = [
            row
            for row in self._audit_rows()
            if row.get("type") == "full_agent.interrupt_requested"
        ]
        self.assertEqual(len(interrupt_audits), 1)
        self.assertFalse(interrupt_audits[0].get("pendingApprovalDeclined"))
        quarantine_audits = [
            row
            for row in self._audit_rows()
            if row.get("type") == "full_agent.gateway_quarantined"
        ]
        self.assertEqual(len(quarantine_audits), 1)
        self.bridge.FULL_AGENT_ACTIVE_TURNS.pop(local_turn_id, None)

    def test_unconfirmed_timeout_quarantines_gateway_and_blocks_unsafe_reuse(self) -> None:
        stuck_gateway = UnconfirmedCloseGateway()
        stuck_gateway.block_waits = True
        self.gateway = stuck_gateway
        self.bridge.FULL_AGENT_GATEWAY_INSTANCE = stuck_gateway
        runtime = self.bridge._full_agent_runtime()
        thread = self._create_thread(agent_id="ceo", mode="chat")

        original_clear = runtime.clear_backend_thread_id
        with (
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_TURN_TIMEOUT_SECONDS",
                0.03,
            ),
            mock.patch.object(
                self.bridge,
                "FULL_AGENT_INTERRUPT_GRACE_SECONDS",
                0.03,
            ),
            mock.patch.object(
                runtime,
                "clear_backend_thread_id",
                wraps=original_clear,
            ) as clear_binding,
        ):
            first = self.bridge.full_agent_request_turn(
                thread["id"],
                {
                    "message": "Wait forever so timeout quarantine is exercised",
                    "idempotencyKey": "timeout-quarantine-turn-0001",
                },
            )
            self.assertTrue(stuck_gateway.wait_entered.wait(1))
            self._wait_for(lambda: not self.bridge.FULL_AGENT_ACTIVE_TURNS)

            first_replay = self.bridge.full_agent_request_turn(
                thread["id"],
                {
                    "message": "Wait forever so timeout quarantine is exercised",
                    "idempotencyKey": "timeout-quarantine-turn-0001",
                },
            )
            self.assertTrue(first_replay["idempotentReplay"])
            self.assertEqual(first_replay["turn"]["status"], "failed")
            self.assertEqual(first_replay["turn"]["errorCode"], "turn_timeout")

        starts = stuck_gateway.calls_for("thread_start")
        self.assertEqual(len(starts), 1)
        backend_thread_id = starts[0]["threadId"]
        clear_binding.assert_called_once_with(
            thread["id"],
            expected_backend_thread_id=backend_thread_id,
        )
        self.assertIsNone(runtime.get_backend_thread_id(thread["id"]))
        self.assertEqual(len(stuck_gateway.calls_for("turn_interrupt")), 1)
        self.assertEqual(len(stuck_gateway.calls_for("close")), 1)
        self.assertIsNone(self.bridge.FULL_AGENT_GATEWAY_INSTANCE)
        self.assertTrue(self.bridge.FULL_AGENT_GATEWAY_QUARANTINED)

        quarantine_audits = [
            row
            for row in self._audit_rows()
            if row.get("type") == "full_agent.gateway_quarantined"
        ]
        self.assertEqual(len(quarantine_audits), 1)
        self.assertFalse(quarantine_audits[0]["closed"])
        first_mission = self.bridge.find_mission(first["missionId"])
        self.assertEqual(first_mission["status"], "failed")
        self.assertEqual(
            json.loads(
                (
                    self.bridge.RUNTIME_REPORTS_DIR
                    / f"{first_mission['reportIds'][0]}.json"
                ).read_text(encoding="utf-8")
            )["metrics"]["errorCode"],
            "turn_timeout",
        )

        # Capacity may be released after the local Turn reaches a durable
        # failure, but the unconfirmed app-server must never be recreated or
        # reused.  The global quarantine is the second fail-closed boundary.
        with mock.patch.object(
            self.bridge,
            "_load_full_agent_gateway_module",
            side_effect=AssertionError("quarantine must reject before gateway load"),
        ):
            with self.assertRaises(self.bridge.RequestError) as direct_access:
                self.bridge._full_agent_gateway()
            self.assertEqual(direct_access.exception.status, 503)
            self.assertEqual(
                (direct_access.exception.response_payload or {}).get("code"),
                "gateway_quarantined",
            )

            second = self.bridge.full_agent_request_turn(
                thread["id"],
                {
                    "message": "A later turn must not reuse the timed-out gateway",
                    "idempotencyKey": "timeout-quarantine-turn-0002",
                },
            )
            self._wait_for(lambda: not self.bridge.FULL_AGENT_ACTIVE_TURNS)
            second_replay = self.bridge.full_agent_request_turn(
                thread["id"],
                {
                    "message": "A later turn must not reuse the timed-out gateway",
                    "idempotencyKey": "timeout-quarantine-turn-0002",
                },
            )

        self.assertEqual(second["status"], "queued")
        self.assertTrue(second_replay["idempotentReplay"])
        self.assertEqual(second_replay["turn"]["status"], "failed")
        self.assertEqual(
            second_replay["turn"]["errorCode"],
            "app_server_unavailable",
        )
        self.assertEqual(len(stuck_gateway.calls_for("thread_start")), 1)
        self.assertEqual(len(stuck_gateway.calls_for("turn_start")), 1)
        self.assertIsNone(self.bridge.FULL_AGENT_GATEWAY_INSTANCE)
        self.assertTrue(self.bridge.FULL_AGENT_GATEWAY_QUARANTINED)

    def test_restart_reconciliation_fails_orphaned_active_turn_and_audits_it(self) -> None:
        runtime = self.bridge._full_agent_runtime()
        thread = runtime.create_thread(
            "manager",
            title="orphaned turn",
            model="gpt-6-sol",
            reasoning="medium",
            mode="chat",
        )["thread"]
        requested = runtime.request_turn(
            thread["id"],
            content="Persist this before restart",
            idempotency_key="restart-turn-0001",
        )
        runtime.update_turn_state(
            thread["id"], requested["turn"]["id"], status="running"
        )
        self.bridge.FULL_AGENT_RUNTIME_RECONCILED = False

        reconciled = self.bridge._full_agent_runtime().get_thread(thread["id"])
        self.assertEqual(reconciled["status"], "idle")
        self.assertIsNone(reconciled["activeTurn"])
        errors = [row for row in reconciled["events"] if row["type"] == "error"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["metadata"]["errorCode"], "bridge_restarted")
        replay = runtime.request_turn(
            thread["id"],
            content="Persist this before restart",
            idempotency_key="restart-turn-0001",
        )
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["turn"]["status"], "failed")
        self.assertEqual(replay["turn"]["errorCode"], "bridge_restarted")
        reconciliations = [
            row
            for row in self._audit_rows()
            if row.get("type") == "full_agent.restart_reconciled"
        ]
        self.assertEqual(len(reconciliations), 1)
        self.assertEqual(reconciliations[0]["recoveredTurns"], 1)
        self.assertEqual(reconciliations[0]["recoveredMissions"], 0)
        self.assertEqual(reconciliations[0]["missingMissions"], 1)
        self.assertEqual(len(self.gateway.calls), 0)

    def test_restart_reconciliation_terminalizes_every_linked_full_agent_mission(self) -> None:
        seeded = [
            self._seed_interrupted_full_agent_turn(
                agent_id="ceo",
                tool_id="agent_collaboration",
                key="restart-linked-ceo-0001",
            ),
            self._seed_interrupted_full_agent_turn(
                agent_id="manager",
                tool_id="codex_cli_task",
                key="restart-linked-manager-0001",
            ),
        ]
        self.bridge.FULL_AGENT_RUNTIME_RECONCILED = False

        reconciled_runtime = self.bridge._full_agent_runtime()

        for runtime, thread, requested, mission, message in seeded:
            self.assertIs(runtime, reconciled_runtime)
            replay = runtime.request_turn(
                thread["id"],
                content=message,
                idempotency_key=(
                    "restart-linked-ceo-0001"
                    if thread["agentId"] == "ceo"
                    else "restart-linked-manager-0001"
                ),
            )
            self.assertTrue(replay["idempotentReplay"])
            self.assertEqual(replay["turn"]["status"], "failed")
            self.assertEqual(replay["turn"]["errorCode"], "bridge_restarted")

            recovered_mission = self.bridge.find_mission(mission["id"])
            self.assertEqual(recovered_mission["status"], "failed")
            self.assertEqual(recovered_mission["phase"], "failed")
            self.assertEqual(recovered_mission["errorCode"], "bridge_restarted")
            self.assertTrue(recovered_mission["completedAt"])
            self.assertEqual(len(recovered_mission["reportIds"]), 1)
            report = json.loads(
                (
                    self.bridge.RUNTIME_REPORTS_DIR
                    / f"{recovered_mission['reportIds'][0]}.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(report["linkedMissionId"], mission["id"])
            self.assertEqual(report["status"], "blocked")
            self.assertEqual(report["metrics"]["turnStatus"], "failed")
            self.assertEqual(report["metrics"]["errorCode"], "bridge_restarted")

        audits = self._audit_rows()
        failed_mission_ids = {
            row.get("missionId")
            for row in audits
            if row.get("type") == "full_agent.turn_failed"
        }
        self.assertEqual(
            failed_mission_ids,
            {row[3]["id"] for row in seeded},
        )
        reconciliations = [
            row for row in audits if row.get("type") == "full_agent.restart_reconciled"
        ]
        self.assertEqual(len(reconciliations), 1)
        self.assertEqual(reconciliations[0]["recoveredTurns"], 2)
        self.assertEqual(reconciliations[0]["recoveredMissions"], 2)
        self.assertEqual(reconciliations[0]["reportFallbacks"], 0)
        self.assertEqual(reconciliations[0]["missingMissions"], 0)
        self.assertEqual(len(self.gateway.calls), 0)

    def test_restart_reconciliation_preserves_completed_mission_evidence(self) -> None:
        runtime, thread, requested, mission, message = (
            self._seed_interrupted_full_agent_turn(
                agent_id="manager",
                tool_id="codex_cli_task",
                key="restart-completed-commit-0001",
            )
        )
        turn_id = requested["turn"]["id"]
        runtime.append_event(
            thread["id"],
            role="assistant",
            content="completed reply persisted before restart",
            event_type="message",
            metadata={"turnId": turn_id, "missionId": mission["id"]},
            idempotency_key=f"assistant:{turn_id}",
        )
        evidence = self.bridge._full_agent_update_mission_terminal(
            mission["id"],
            succeeded=True,
            code="completed",
            summary="Codex App Server ทำ Turn เสร็จและบันทึกคำตอบใน Thread แล้ว",
            thread=thread,
            duration_ms=2468,
        )
        self.assertIsInstance(evidence, dict)
        report_ids = list(self.bridge.find_mission(mission["id"])["reportIds"])
        self.bridge.FULL_AGENT_RUNTIME_RECONCILED = False

        self.bridge._full_agent_runtime()

        replay = runtime.request_turn(
            thread["id"],
            content=message,
            idempotency_key="restart-completed-commit-0001",
        )
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["turn"]["id"], turn_id)
        self.assertEqual(replay["turn"]["status"], "completed")
        self.assertIsNone(replay["turn"]["errorCode"])
        recovered_thread = runtime.get_thread(thread["id"])
        replies = [
            event.get("content")
            for event in recovered_thread["events"]
            if event.get("role") == "assistant"
            and event.get("metadata", {}).get("turnId") == turn_id
        ]
        self.assertEqual(replies, ["completed reply persisted before restart"])
        recovered_mission = self.bridge.find_mission(mission["id"])
        self.assertEqual(recovered_mission["status"], "completed")
        self.assertEqual(recovered_mission["phase"], "completed")
        self.assertIsNone(recovered_mission["errorCode"])
        self.assertEqual(recovered_mission["reportIds"], report_ids)
        self.assertEqual(len(list(self.bridge.RUNTIME_REPORTS_DIR.glob("*.json"))), 1)
        report = json.loads(
            (
                self.bridge.RUNTIME_REPORTS_DIR / f"{report_ids[0]}.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["metrics"]["turnStatus"], "completed")
        audits = self._audit_rows()
        self.assertEqual(
            sum(
                row.get("type") == "full_agent.turn_completed"
                and row.get("missionId") == mission["id"]
                for row in audits
            ),
            1,
        )
        self.assertFalse(
            any(
                row.get("type") == "full_agent.turn_failed"
                and row.get("missionId") == mission["id"]
                for row in audits
            )
        )
        reconciliation = next(
            row for row in audits if row.get("type") == "full_agent.restart_reconciled"
        )
        self.assertEqual(reconciliation["recoveredCompletedTurns"], 1)
        self.assertEqual(reconciliation["recoveredFailedTurns"], 0)
        self.assertEqual(len(self.gateway.calls), 0)

    def test_restart_reconciliation_fails_mission_when_report_creation_fails(self) -> None:
        runtime, thread, requested, mission, message = (
            self._seed_interrupted_full_agent_turn(
                agent_id="manager",
                tool_id="codex_cli_task",
                key="restart-report-failure-0001",
            )
        )
        self.bridge.FULL_AGENT_RUNTIME_RECONCILED = False

        with mock.patch.object(
            self.bridge,
            "create_report",
            side_effect=OSError("report storage unavailable"),
        ):
            reconciled = self.bridge._full_agent_runtime().get_thread(thread["id"])

        self.assertEqual(reconciled["status"], "idle")
        replay = runtime.request_turn(
            thread["id"],
            content=message,
            idempotency_key="restart-report-failure-0001",
        )
        self.assertEqual(replay["turn"]["status"], "failed")
        self.assertEqual(replay["turn"]["errorCode"], "bridge_restarted")
        recovered_mission = self.bridge.find_mission(mission["id"])
        self.assertEqual(recovered_mission["status"], "failed")
        self.assertEqual(recovered_mission["phase"], "failed")
        self.assertEqual(recovered_mission["errorCode"], "bridge_restarted")
        self.assertTrue(recovered_mission["completedAt"])
        self.assertEqual(recovered_mission["reportIds"], [])

        audits = self._audit_rows()
        report_failures = [
            row
            for row in audits
            if row.get("type") == "full_agent.report_failed"
            and row.get("missionId") == mission["id"]
        ]
        self.assertEqual(len(report_failures), 1)
        self.assertEqual(report_failures[0]["errorCode"], "bridge_restarted")
        reconciliations = [
            row for row in audits if row.get("type") == "full_agent.restart_reconciled"
        ]
        self.assertEqual(len(reconciliations), 1)
        self.assertEqual(reconciliations[0]["recoveredTurns"], 1)
        self.assertEqual(reconciliations[0]["recoveredMissions"], 0)
        self.assertEqual(reconciliations[0]["reportFallbacks"], 1)
        self.assertEqual(reconciliations[0]["missingMissions"], 0)
        self.assertEqual(len(self.gateway.calls), 0)

    def test_restart_reconciliation_reuses_committed_mission_evidence(self) -> None:
        runtime, thread, requested, mission, message = (
            self._seed_interrupted_full_agent_turn(
                agent_id="manager",
                tool_id="codex_cli_task",
                key="restart-partial-commit-0001",
            )
        )
        turn_id = requested["turn"]["id"]
        evidence = self.bridge._full_agent_update_mission_terminal(
            mission["id"],
            succeeded=False,
            code="bridge_restarted",
            summary=self.bridge._full_agent_error_message("bridge_restarted"),
            thread=thread,
            duration_ms=4321,
        )
        self.assertIsInstance(evidence, dict)
        before = self.bridge.find_mission(mission["id"])
        report_ids = list(before["reportIds"])
        failed_audits_before = [
            row
            for row in self._audit_rows()
            if row.get("type") == "full_agent.turn_failed"
            and row.get("missionId") == mission["id"]
        ]
        self.assertEqual(len(failed_audits_before), 1)
        self.bridge.FULL_AGENT_RUNTIME_RECONCILED = False

        self.bridge._full_agent_runtime()

        replay = runtime.request_turn(
            thread["id"],
            content=message,
            idempotency_key="restart-partial-commit-0001",
        )
        self.assertEqual(replay["turn"]["id"], turn_id)
        self.assertEqual(replay["turn"]["status"], "failed")
        self.assertEqual(replay["turn"]["errorCode"], "bridge_restarted")
        after = self.bridge.find_mission(mission["id"])
        self.assertEqual(after["reportIds"], report_ids)
        self.assertEqual(
            len(list(self.bridge.RUNTIME_REPORTS_DIR.glob("*.json"))),
            1,
        )
        failed_audits_after = [
            row
            for row in self._audit_rows()
            if row.get("type") == "full_agent.turn_failed"
            and row.get("missionId") == mission["id"]
        ]
        self.assertEqual(len(failed_audits_after), 1)
        self.assertEqual(len(self.gateway.calls), 0)

    def test_restart_reconciliation_heals_crash_after_mission_before_terminal_audit(self) -> None:
        runtime, thread, requested, mission, message = (
            self._seed_interrupted_full_agent_turn(
                agent_id="manager",
                tool_id="codex_cli_task",
                key="restart-partial-audit-0001",
            )
        )
        turn_id = requested["turn"]["id"]
        original_append_once = self.bridge.append_audit_once

        def crash_before_terminal_audit(event: dict) -> bool:
            if event.get("type") == "full_agent.turn_failed":
                raise OSError("simulated crash before terminal audit")
            return original_append_once(event)

        with mock.patch.object(
            self.bridge,
            "append_audit_once",
            side_effect=crash_before_terminal_audit,
        ):
            with self.assertRaises(OSError):
                self.bridge._full_agent_update_mission_terminal(
                    mission["id"],
                    succeeded=False,
                    code="bridge_restarted",
                    summary=self.bridge._full_agent_error_message("bridge_restarted"),
                    thread=thread,
                )

        partially_recovered = self.bridge.find_mission(mission["id"])
        self.assertEqual(partially_recovered["status"], "failed")
        self.assertEqual(partially_recovered["errorCode"], "bridge_restarted")
        self.assertEqual(len(partially_recovered["reportIds"]), 1)
        report_ids = list(partially_recovered["reportIds"])
        self.assertEqual(len(list(self.bridge.RUNTIME_REPORTS_DIR.glob("*.json"))), 1)
        self.assertFalse(
            any(
                row.get("type") == "full_agent.turn_failed"
                and row.get("missionId") == mission["id"]
                for row in self._audit_rows()
            )
        )
        self.bridge.FULL_AGENT_RUNTIME_RECONCILED = False

        self.bridge._full_agent_runtime()

        replay = runtime.request_turn(
            thread["id"],
            content=message,
            idempotency_key="restart-partial-audit-0001",
        )
        self.assertEqual(replay["turn"]["id"], turn_id)
        self.assertEqual(replay["turn"]["status"], "failed")
        self.assertEqual(replay["turn"]["errorCode"], "bridge_restarted")
        healed_mission = self.bridge.find_mission(mission["id"])
        self.assertEqual(healed_mission["reportIds"], report_ids)
        self.assertEqual(len(list(self.bridge.RUNTIME_REPORTS_DIR.glob("*.json"))), 1)
        failed_audits = [
            row
            for row in self._audit_rows()
            if row.get("type") == "full_agent.turn_failed"
            and row.get("missionId") == mission["id"]
        ]
        self.assertEqual(len(failed_audits), 1)
        self.assertEqual(
            failed_audits[0]["reportId"],
            report_ids[0],
        )
        self.assertEqual(len(self.gateway.calls), 0)

    def test_legacy_workspace_policy_is_read_only_and_requires_explicit_approval(self) -> None:
        thread = self.bridge._full_agent_runtime().create_thread(
            "ea_developer",
            title="legacy workspace",
            model="gpt-6-sol",
            reasoning="medium",
            mode="workspace",
        )["thread"]
        policy = self.bridge._full_agent_policy(thread)
        self.assertEqual(
            set(policy),
            {
                "agentId",
                "mode",
                "model",
                "reasoningEffort",
                "workspaceRoots",
                "sandbox",
                "approvalMode",
                "externalEffects",
                "autoExternalEffects",
            },
        )
        self.assertEqual(policy["sandbox"], "read-only")
        self.assertEqual(policy["approvalMode"], "explicit")
        self.assertEqual(policy["externalEffects"], "approval-required")
        self.assertFalse(policy["autoExternalEffects"])
        self.assertTrue(policy["workspaceRoots"])
        allowed_top_level = {"workspace", "frontend", "docs", "assets-source"}
        project_root = self.bridge.PROJECT_ROOT.resolve()
        for value in policy["workspaceRoots"]:
            root = Path(value).resolve()
            self.assertNotEqual(root, project_root)
            self.assertTrue(root.is_relative_to(project_root))
            self.assertIn(root.relative_to(project_root).parts[0], allowed_top_level)
        encoded = json.dumps(policy, sort_keys=True).casefold()
        self.assertNotIn("danger-full-access", encoded)
        self.assertNotIn("networkallowed", encoded.replace("_", ""))
        self.assertNotIn("websearch", encoded.replace("_", ""))
        self.assertNotIn("externalapps", encoded.replace("_", ""))
        self.assertNotIn("computer_use", encoded)
        self.assertNotIn("mcp", encoded)
        self.assertNotIn("plugin", encoded)


if __name__ == "__main__":
    unittest.main()
