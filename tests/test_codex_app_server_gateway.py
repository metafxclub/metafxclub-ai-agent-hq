from __future__ import annotations

import importlib.util
import base64
import io
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GATEWAY_PATH = PROJECT_ROOT / "runner" / "codex_app_server_gateway.py"
RUNTIME_PATH = PROJECT_ROOT / "backend" / "local-runner" / "full_agent_runtime.py"


def load_gateway():
    spec = importlib.util.spec_from_file_location("metafx_codex_app_server_gateway", GATEWAY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {GATEWAY_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gateway_module = load_gateway()


def load_runtime_module():
    spec = importlib.util.spec_from_file_location(
        "metafx_full_agent_runtime_gateway_tests", RUNTIME_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {RUNTIME_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runtime_module = load_runtime_module()


def model_catalog() -> list[dict]:
    return [
        {
            "id": "gpt-safe",
            "model": "gpt-safe",
            "displayName": "GPT Safe",
            "description": "Safe fixture",
            "isDefault": True,
            "hidden": False,
            "defaultReasoningEffort": "medium",
            "supportedReasoningEfforts": ["low", "medium", "high"],
            "inputModalities": ["text", "image"],
            "supportsPersonality": True,
        }
    ]


class FakeClient:
    def __init__(self) -> None:
        self.started = False
        self.closed = False
        self.calls: list[tuple] = []
        self.turn_count = 0
        self.turn_ids: list[str] = []
        self.registered_turns: set[str] = set()

    def start(self) -> None:
        self.started = True

    def initialize(self) -> dict:
        self.calls.append(("initialize",))
        return {
            "serverInfo": {"name": "codex", "version": "0.155.0"},
            "userAgent": "must-not-be-required",
            "platformFamily": "windows",
            "platformOs": "windows",
            "accessToken": "must-not-leak",
        }

    def close(self) -> None:
        self.closed = True

    def account_read(self, params=None) -> dict:
        self.calls.append(("account_read", params))
        return {
            "account": {
                "type": "chatgpt",
                "email": "private@example.test",
                "planType": "plus",
                "accessToken": "must-not-leak",
            },
            "requiresOpenaiAuth": True,
            "refreshToken": "must-not-leak",
        }

    def model_list(self, include_hidden: bool = False) -> dict:
        self.calls.append(("model_list", include_hidden))
        return {"data": model_catalog(), "accountToken": "must-not-leak"}

    def request(self, method: str, params: dict, *, response_model: type) -> dict:
        self.calls.append(("request", method, params, response_model))
        if method == "mcpServerStatus/list":
            return {
                "data": [
                    {
                        "name": "local-tools",
                        "authStatus": "authenticated",
                        "tools": {
                            "read_file": {
                                "title": "Read file",
                                "description": "Read a workspace file",
                                "inputSchema": {"secret": "must-not-leak"},
                            }
                        },
                        "resources": [{"uri": "secret://not-returned"}],
                        "resourceTemplates": [],
                        "authorization": "must-not-leak",
                    }
                ]
            }
        if method == "plugin/list":
            return {
                "marketplaces": [
                    {
                        "name": "local",
                        "path": "C:/private/plugin.json",
                        "plugins": [
                            {
                                "id": "safe-plugin",
                                "name": "Safe Plugin",
                                "version": "1.2.3",
                                "enabled": True,
                                "installed": True,
                                "availability": "AVAILABLE",
                                "authPolicy": "ON_DEMAND",
                                "source": {"path": "C:/private"},
                            }
                        ],
                    }
                ]
            }
        raise AssertionError(method)

    def thread_start(self, params: dict) -> dict:
        self.calls.append(("thread_start", params))
        return {
            "thread": {
                "id": "thread-1",
                "name": "EA work",
                "preview": "Build safely",
                "status": "idle",
                "createdAt": 1,
                "updatedAt": 2,
                "recencyAt": 2,
                "modelProvider": "openai",
                "ephemeral": False,
                "cwd": "C:/private/workspace",
                "path": "C:/private/thread.jsonl",
                "turns": [],
            }
        }

    def thread_resume(self, thread_id: str, params: dict) -> dict:
        self.calls.append(("thread_resume", thread_id, params))
        return {
            "thread": {
                "id": thread_id,
                "name": "Resumed",
                "preview": "Continue",
                "status": "idle",
                "createdAt": 1,
                "updatedAt": 3,
                "modelProvider": "openai",
                "ephemeral": False,
                "turns": [],
            }
        }

    def thread_read(self, thread_id: str, include_turns: bool = False) -> dict:
        self.calls.append(("thread_read", thread_id, include_turns))
        return {
            "thread": {
                "id": thread_id,
                "name": "Read",
                "preview": "Prompt",
                "status": "idle",
                "createdAt": 1,
                "updatedAt": 4,
                "modelProvider": "openai",
                "ephemeral": False,
                "turns": (
                    [self._completed_turn(turn_id) for turn_id in self.turn_ids]
                    if self.turn_ids
                    else [self._completed_turn("turn-read")]
                ) if include_turns else [],
                "path": "C:/must/not/leak.jsonl",
            }
        }

    def thread_list(self, params: dict) -> dict:
        self.calls.append(("thread_list", params))
        return {
            "data": [
                {
                    "id": "thread-1",
                    "name": "Listed",
                    "preview": "Safe preview",
                    "status": "idle",
                    "createdAt": 1,
                    "updatedAt": 4,
                    "modelProvider": "openai",
                    "ephemeral": False,
                    "turns": [],
                }
            ],
            "nextCursor": "cursor-2",
        }

    @staticmethod
    def _completed_turn(turn_id: str) -> dict:
        return {
            "id": turn_id,
            "status": "completed",
            "startedAt": 10,
            "completedAt": 12,
            "durationMs": 2000,
            "items": [
                {
                    "id": "message-1",
                    "type": "agentMessage",
                    "text": "Finished safely. Bearer top-secret-token-value",
                    "phase": "final",
                },
                {
                    "id": "tool-1",
                    "type": "commandExecution",
                    "status": "completed",
                    "command": "type C:\\private\\password.txt",
                    "aggregatedOutput": "client_secret=top-secret",
                    "cwd": "C:/private",
                    "durationMs": 25,
                },
            ],
        }

    def turn_start(self, thread_id: str, prompt: str, params: dict) -> dict:
        self.turn_count += 1
        turn_id = f"turn-{self.turn_count}"
        self.turn_ids.append(turn_id)
        self.calls.append(("turn_start", thread_id, prompt, params))
        return {
            "turn": {
                "id": turn_id,
                "status": "inProgress",
                "startedAt": 10,
                "items": [],
            }
        }

    def wait_for_turn_completed(self, turn_id: str) -> dict:
        self.calls.append(("turn_wait", turn_id))
        return {"threadId": "thread-1", "turn": self._completed_turn(turn_id)}

    def register_turn_notifications(self, turn_id: str) -> None:
        self.calls.append(("turn_register", turn_id))
        self.registered_turns.add(turn_id)

    def unregister_turn_notifications(self, turn_id: str) -> None:
        self.calls.append(("turn_unregister", turn_id))
        self.registered_turns.discard(turn_id)

    def turn_interrupt(self, thread_id: str, turn_id: str) -> dict:
        self.calls.append(("turn_interrupt", thread_id, turn_id))
        return {"turnId": turn_id, "authorization": "must-not-leak"}


class CapturingFactory:
    def __init__(self, client: FakeClient | None = None) -> None:
        self.client = client or FakeClient()
        self.kwargs: dict | None = None

    def __call__(self, **kwargs):
        self.kwargs = kwargs
        return self.client


class ModeAndPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = str(Path(self.temp.name).resolve())

    def tearDown(self) -> None:
        self.temp.cleanup()

    def request(self, **overrides):
        value = {
            "agentId": "ea_developer",
            "mode": "workspace",
            "model": "gpt-safe",
            "reasoningEffort": "medium",
            "cwd": self.workspace,
            "approvalMode": "deny_all",
            "externalEffects": "approval-required",
            "autoExternalEffects": False,
        }
        value.update(overrides)
        return value

    def test_mode_matrix_is_monotonic_and_truthful(self) -> None:
        chat = gateway_module.get_mode_profile("chat")
        workspace = gateway_module.get_mode_profile("workspace")
        computer = gateway_module.get_mode_profile("computer_use")
        full = gateway_module.get_mode_profile("full_agent")

        self.assertLess(chat.enabled_capabilities, workspace.enabled_capabilities)
        self.assertLess(workspace.enabled_capabilities, computer.enabled_capabilities)
        self.assertLess(computer.enabled_capabilities, full.enabled_capabilities)
        self.assertNotIn("shell", chat.enabled_capabilities)
        self.assertIn("computer_use", computer.enabled_capabilities)
        self.assertIn("mcp", full.enabled_capabilities)
        self.assertFalse(chat.feature_overrides["shell_tool"])
        self.assertTrue(full.feature_overrides["plugins"])

    def test_safe_workspace_policy_uses_never_and_never_danger_full_access(self) -> None:
        policy = gateway_module.validate_thread_policy(
            self.request(),
            model_catalog=model_catalog(),
        )

        self.assertEqual(policy.approval_mode, gateway_module.ApprovalMode.DENY_ALL)
        self.assertEqual(policy.approval_policy, "never")
        self.assertEqual(policy.sandbox, "workspace-write")
        self.assertNotEqual(policy.sandbox, "danger-full-access")
        self.assertTrue(policy.feature_overrides["shell_tool"])
        self.assertFalse(policy.feature_overrides["plugins"])

    def test_policy_accepts_workspace_roots_or_cwd_alias(self) -> None:
        by_cwd = gateway_module.validate_thread_policy(self.request())
        by_roots = gateway_module.validate_thread_policy(
            self.request(cwd=None, workspaceRoots=[self.workspace])
        )
        self.assertEqual(by_cwd.workspace_roots, by_roots.workspace_roots)

    def test_danger_full_access_is_always_denied(self) -> None:
        with self.assertRaisesRegex(gateway_module.PolicyViolation, "prohibited") as caught:
            gateway_module.validate_thread_policy(
                self.request(sandbox="danger-full-access")
            )
        self.assertEqual(caught.exception.code, "danger_full_access_denied")

    def test_automatic_external_effects_are_always_denied(self) -> None:
        with self.assertRaises(gateway_module.PolicyViolation) as caught:
            gateway_module.validate_thread_policy(
                self.request(autoExternalEffects=True)
            )
        self.assertEqual(caught.exception.code, "automatic_external_effects_denied")

    def test_full_agent_requires_explicit_approval(self) -> None:
        with self.assertRaises(gateway_module.PolicyViolation) as caught:
            gateway_module.validate_thread_policy(
                self.request(mode="full_agent", approvalMode="deny_all")
            )
        self.assertEqual(caught.exception.code, "explicit_approval_required")

        policy = gateway_module.validate_thread_policy(
            self.request(mode="full_agent", approvalMode="explicit")
        )
        self.assertEqual(policy.approval_policy, "on-request")
        self.assertEqual(policy.external_effects, "approval-required")

    def test_mode_cannot_escalate_capability(self) -> None:
        with self.assertRaises(gateway_module.PolicyViolation) as caught:
            gateway_module.validate_thread_policy(
                self.request(
                    mode="chat",
                    sandbox="read-only",
                    requestedCapabilities=[
                        "conversation",
                        "history",
                        "model_selection",
                        "shell",
                    ],
                )
            )
        self.assertEqual(caught.exception.code, "capability_not_allowed")

    def test_model_and_reasoning_must_match_catalog(self) -> None:
        with self.assertRaises(gateway_module.PolicyViolation) as model_error:
            gateway_module.validate_thread_policy(
                self.request(model="gpt-missing"),
                model_catalog=model_catalog(),
            )
        self.assertEqual(model_error.exception.code, "model_unavailable")

        with self.assertRaises(gateway_module.PolicyViolation) as effort_error:
            gateway_module.validate_thread_policy(
                self.request(reasoningEffort="xhigh"),
                model_catalog=model_catalog(),
            )
        self.assertEqual(effort_error.exception.code, "reasoning_unavailable")

    def test_drive_or_filesystem_root_is_denied(self) -> None:
        filesystem_root = str(Path(self.workspace).anchor)
        with self.assertRaises(gateway_module.PolicyViolation) as caught:
            gateway_module.validate_thread_policy(
                self.request(cwd=filesystem_root)
            )
        self.assertEqual(caught.exception.code, "workspace_too_broad")


class LaunchAndDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_default_factory_uses_bounded_deferred_reader_only_when_enabled(self) -> None:
        sdk_module = types.ModuleType("openai_codex")
        sdk_module.__path__ = []
        client_module = types.ModuleType("openai_codex.client")

        class StubCodexConfig:
            def __init__(self, **kwargs) -> None:
                self.kwargs = kwargs

        class StubCodexClient:
            def __init__(self, config, *, approval_handler) -> None:
                self.config = config
                self.approval_handler = approval_handler
                self.closed = False

            def close(self) -> None:
                self.closed = True

        sdk_module.CodexConfig = StubCodexConfig
        client_module.CodexClient = StubCodexClient
        with mock.patch.dict(
            sys.modules,
            {
                "openai_codex": sdk_module,
                "openai_codex.client": client_module,
            },
        ):
            deferred = gateway_module._default_client_factory(
                approval_handler=gateway_module.fail_closed_approval_handler,
                codex_bin=None,
                cwd=str(self.root),
                environment={},
                deferred_server_requests_supported=True,
            )
            ordinary = gateway_module._default_client_factory(
                approval_handler=gateway_module.fail_closed_approval_handler,
                codex_bin=None,
                cwd=str(self.root),
                environment={},
                deferred_server_requests_supported=False,
            )
            try:
                self.assertIsInstance(
                    deferred, gateway_module._DeferredServerRequestReaderMixin
                )
                self.assertNotIsInstance(
                    ordinary, gateway_module._DeferredServerRequestReaderMixin
                )
                self.assertEqual(deferred._MAX_SERVER_REQUEST_WORKERS, 4)
            finally:
                deferred.close()
                ordinary.close()

    def test_stdio_launch_is_process_authenticated_and_strict(self) -> None:
        spec = gateway_module.build_app_server_launch_spec(
            "codex.exe",
            transport="stdio",
            cwd=self.root,
            environment={"PATH": "safe", "MY_ACCESS_TOKEN": "secret"},
        )
        self.assertEqual(spec.endpoint, "stdio://")
        self.assertEqual(spec.auth_mode, "process_stdio")
        self.assertIn("--strict-config", spec.argv)
        self.assertIn('sandbox_mode="read-only"', spec.argv)
        self.assertNotIn("danger-full-access", spec.argv)
        self.assertEqual(spec.environment["MY_ACCESS_TOKEN"], "")
        public = spec.to_dict()
        self.assertNotIn("environment", public)
        self.assertIn("environmentKeys", public)

    def test_loopback_websocket_requires_capability_token_and_digest(self) -> None:
        token_file = self.root / "runtime" / "app-server.token"
        digest = hashlib_for_test(b"token")
        spec = gateway_module.build_app_server_launch_spec(
            "codex.exe",
            transport="loopback_ws",
            host="127.0.0.1",
            port=44186,
            token_file=token_file,
            token_sha256=digest,
            cwd=self.root,
        )
        self.assertEqual(spec.endpoint, "ws://127.0.0.1:44186")
        self.assertEqual(spec.auth_mode, "capability-token")
        self.assertIn("--ws-auth", spec.argv)
        self.assertIn(digest, spec.argv)

    def test_public_or_unauthenticated_websocket_is_denied(self) -> None:
        with self.assertRaises(gateway_module.PolicyViolation) as public_error:
            gateway_module.build_app_server_launch_spec(
                "codex.exe",
                transport="loopback_ws",
                host="0.0.0.0",
                port=44186,
                token_file=self.root / "token",
                token_sha256="a" * 64,
                cwd=self.root,
            )
        self.assertEqual(public_error.exception.code, "public_bind_denied")

        with self.assertRaises(gateway_module.PolicyViolation) as auth_error:
            gateway_module.build_app_server_launch_spec(
                "codex.exe",
                transport="loopback_ws",
                port=44186,
                cwd=self.root,
            )
        self.assertEqual(auth_error.exception.code, "authentication_required")

    def test_discovery_uses_only_fixed_read_only_commands(self) -> None:
        commands: list[tuple[str, ...]] = []

        def probe(command: tuple[str, ...], timeout: int):
            commands.append(command)
            self.assertLessEqual(timeout, 15)
            if command[-1] == "--version":
                return gateway_module.ProbeResult(0, "codex-cli 0.155.0-alpha.9\n")
            if command[-2:] == ("app-server", "--help"):
                return gateway_module.ProbeResult(
                    0,
                    "Usage: codex app-server [OPTIONS]\n--listen stdio:// ws://IP:PORT\n"
                    "--stdio\n--ws-auth capability-token\n--ws-token-file PATH\n",
                )
            return gateway_module.ProbeResult(
                0,
                "shell_tool stable true\ncomputer_use stable true\n"
                "plugins stable false\nmalformed secret=value\n",
            )

        result = gateway_module.discover_codex_runtime(
            "codex.exe",
            probe_runner=probe,
            model_payload={"data": model_catalog()},
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.version, "0.155.0-alpha.9")
        self.assertTrue(result.capability_token_auth_supported)
        self.assertTrue(result.tool_capabilities["shell"])
        self.assertFalse(result.tool_capabilities["plugins"])
        self.assertEqual(result.models[0]["model"], "gpt-safe")
        self.assertEqual(
            commands,
            [
                ("codex.exe", "--version"),
                ("codex.exe", "app-server", "--help"),
                ("codex.exe", "features", "list"),
            ],
        )


def hashlib_for_test(value: bytes) -> str:
    import hashlib

    return hashlib.sha256(value).hexdigest()


class SanitizationAndStateTests(unittest.TestCase):
    def test_unlabeled_provider_secret_shapes_are_detected(self) -> None:
        google_oauth_secret = "GOC" + "SPX-" + ("A" * 28)
        telegram_bot_token = str(123456789) + ":" + ("A" * 35)
        self.assertTrue(gateway_module.contains_potential_secret(google_oauth_secret))
        self.assertTrue(gateway_module.contains_potential_secret(telegram_bot_token))
        self.assertFalse(
            gateway_module.contains_potential_secret(
                "Discuss Google OAuth and Telegram configuration without credentials."
            )
        )

    def test_account_projection_is_minimal_and_fails_closed(self) -> None:
        known = gateway_module.project_account_authentication(
            {
                "account": {
                    "type": "chatgpt",
                    "email": "private@example.test",
                    "planType": "plus",
                },
                "requiresOpenaiAuth": True,
                "accessToken": "must-not-leak",
            }
        )
        self.assertEqual(
            known,
            {
                "authenticated": True,
                "requiresOpenaiAuth": True,
                "accountType": "chatgpt",
            },
        )
        self.assertNotIn("private@example.test", json.dumps(known))

        unknown = gateway_module.project_account_authentication(
            {
                "account": {"type": "future-provider", "email": "private@example.test"},
                "requiresOpenaiAuth": "false",
            }
        )
        self.assertEqual(
            unknown,
            {
                "authenticated": False,
                "requiresOpenaiAuth": True,
                "accountType": None,
            },
        )

        no_auth_needed = gateway_module.project_account_authentication(
            {"account": None, "requiresOpenaiAuth": False}
        )
        self.assertTrue(no_auth_needed["authenticated"])

    def test_event_parser_redacts_secrets_and_rejects_invalid_shape(self) -> None:
        event = gateway_module.parse_app_server_event(
            json.dumps(
                {
                    "method": "turn/completed",
                    "params": {
                        "message": "Bearer abcdefghijklmnop",
                        "clientSecret": "raw-secret",
                        "nested": {"api_key": "sk-abcdefghijklmnop"},
                    },
                }
            )
        )
        encoded = json.dumps(event)
        self.assertNotIn("abcdefghijklmnop", encoded)
        self.assertNotIn("raw-secret", encoded)
        self.assertIn("[REDACTED]", encoded)

        with self.assertRaises(gateway_module.GatewayError):
            gateway_module.parse_app_server_event("[]")

    def test_turn_projection_keeps_assistant_text_but_drops_tool_payload(self) -> None:
        projected = gateway_module._project_turn(FakeClient._completed_turn("turn-1"))
        encoded = json.dumps(projected)
        self.assertIn("Finished safely", projected["assistantText"])
        self.assertIn("[REDACTED]", projected["assistantText"])
        self.assertNotIn("password.txt", encoded)
        self.assertNotIn("top-secret", encoded)
        self.assertNotIn("aggregatedOutput", encoded)
        self.assertEqual(projected["items"][1]["status"], "completed")
        self.assertFalse(projected["itemsTruncated"])
        self.assertEqual(projected["itemCount"], len(projected["items"]))

    def test_turn_projection_marks_truncation_fail_closed(self) -> None:
        raw_items = [
            {"id": f"reason-{index}", "type": "reasoning", "summary": ["safe"]}
            for index in range(gateway_module.MAX_COLLECTION_ITEMS)
        ]
        raw_items.append(
            {"id": "hidden-command", "type": "commandExecution", "status": "completed"}
        )
        projected = gateway_module._project_turn(
            {"id": "turn-truncated", "status": "completed", "items": raw_items}
        )

        self.assertTrue(projected["itemsTruncated"])
        self.assertEqual(projected["itemCount"], len(raw_items))
        self.assertEqual(len(projected["items"]), gateway_module.MAX_COLLECTION_ITEMS)
        self.assertFalse(
            any(item.get("type") == "commandExecution" for item in projected["items"])
        )
        malformed = gateway_module._project_turn(
            {"id": "turn-malformed", "status": "completed", "items": {"hidden": True}}
        )
        self.assertTrue(malformed["itemsTruncated"])
        self.assertEqual(malformed["items"], [])

    def test_process_and_session_transitions_fail_closed(self) -> None:
        state = gateway_module.GatewayProcessState()
        state = state.transition("starting")
        state = state.transition("ready")
        with self.assertRaises(gateway_module.GatewayError):
            state.transition("stopped")

        with tempfile.TemporaryDirectory() as temp:
            policy = gateway_module.validate_thread_policy(
                {
                    "agentId": "manager",
                    "mode": "workspace",
                    "model": "gpt-safe",
                    "cwd": temp,
                    "approvalMode": "deny_all",
                }
            )
        session = gateway_module.ThreadSessionState(
            "thread-1",
            "manager",
            gateway_module.SessionStatus.IDLE,
            policy,
        )
        session = session.transition("running", active_turn_id="turn-1", event_sequence=1)
        with self.assertRaises(gateway_module.GatewayError):
            session.transition("idle", event_sequence=1)

    def test_all_server_approval_requests_fail_closed(self) -> None:
        handler = gateway_module.fail_closed_approval_handler
        self.assertEqual(
            handler("item/commandExecution/requestApproval", {}),
            {"decision": "decline"},
        )
        self.assertEqual(
            handler("item/fileChange/requestApproval", {}),
            {"decision": "decline"},
        )
        self.assertEqual(
            handler("item/permissions/requestApproval", {}),
            {"permissions": {}, "scope": "turn"},
        )
        self.assertEqual(
            handler("mcpServer/elicitation/request", {}),
            {"action": "decline", "content": None},
        )
        self.assertEqual(
            handler("item/tool/requestUserInput", {}),
            {"answers": {}},
        )
        self.assertFalse(handler("item/tool/call", {})["success"])
        with self.assertRaises(gateway_module.PolicyViolation) as unknown:
            handler("unknown/request", {})
        self.assertEqual(unknown.exception.code, "unsupported_server_request")

    def test_explicit_approval_is_one_shot_and_timeout_declines(self) -> None:
        broker = gateway_module.ExplicitApprovalBroker(timeout_seconds=1)
        result: dict = {}

        def ask():
            result.update(
                broker.handler(
                    "item/commandExecution/requestApproval",
                    {
                        "threadId": "thread-approval-1",
                        "turnId": "turn-approval-1",
                        "itemId": "item-approval-1",
                        "startedAtMs": 1,
                        "kind": "command",
                        "availableDecisions": ["accept", "decline"],
                        "command": "rg bounded_target .",
                    },
                )
            )

        worker = threading.Thread(target=ask)
        worker.start()
        deadline = time.time() + 1
        pending = []
        while time.time() < deadline and not pending:
            pending = broker.list_pending()
            time.sleep(0.01)
        self.assertEqual(len(pending), 1)
        approval = pending[0]
        resolve_kwargs = {
            "idempotency_key": "approval-decision-1",
            "thread_id": approval["threadId"],
            "turn_id": approval["turnId"],
            "item_id": approval["itemId"],
            "request_digest": approval["requestDigest"],
            "decision_nonce": approval["decisionNonce"],
        }
        self.assertTrue(
            broker.resolve(
                approval["requestId"],
                "accept_once",
                **resolve_kwargs,
            )
        )
        worker.join(2)
        self.assertEqual(result, {"decision": "accept"})
        self.assertTrue(
            broker.resolve(
                approval["requestId"],
                "accept_once",
                **resolve_kwargs,
            )
        )
        with self.assertRaises(gateway_module.PolicyViolation) as conflict:
            broker.resolve(
                approval["requestId"],
                "decline",
                **resolve_kwargs,
            )
        self.assertEqual(conflict.exception.code, "approval_decision_conflict")

    def test_oversized_or_hidden_suffix_commands_fail_closed(self) -> None:
        broker = gateway_module.ExplicitApprovalBroker(timeout_seconds=1)
        base = {
            "threadId": "thread-digest-1",
            "turnId": "turn-digest-1",
            "itemId": "item-digest-1",
            "startedAtMs": 1,
            "kind": "command",
            "availableDecisions": ["accept", "decline"],
        }
        commands = (
            "rg safe " + ("a" * 17_000) + "x",
            "rg safe " + ("a" * 2_100) + " ; rm hidden-target",
            "rg safe\nrm hidden-target",
            "rg safe\u202erm hidden-target",
        )
        for index, command in enumerate(commands):
            with self.subTest(index=index):
                response = broker.handler(
                    "item/commandExecution/requestApproval",
                    {**base, "itemId": f"item-digest-{index}", "command": command},
                )
                self.assertEqual(response, {"decision": "decline"})
                self.assertEqual(broker.list_pending(), [])

        hidden_actions = broker.handler(
            "item/commandExecution/requestApproval",
            {
                **base,
                "itemId": "item-digest-actions",
                "command": "rg safe .",
                "commandActions": [{"type": "unknown-hidden-action"}],
            },
        )
        self.assertEqual(hidden_actions, {"decision": "decline"})
        self.assertEqual(broker.list_pending(), [])

    def test_high_risk_command_never_enters_pending_queue(self) -> None:
        broker = gateway_module.ExplicitApprovalBroker(timeout_seconds=1)
        response = broker.handler(
            "item/commandExecution/requestApproval",
            {
                "threadId": "thread-risk-1",
                "turnId": "turn-risk-1",
                "itemId": "item-risk-1",
                "startedAtMs": 1,
                "kind": "command",
                "availableDecisions": ["accept", "decline"],
                "command": "git push origin main",
            },
        )
        self.assertEqual(response, {"decision": "decline"})
        self.assertEqual(broker.list_pending(), [])

    def test_wrapper_and_indirect_commands_never_enter_pending_queue(self) -> None:
        commands = (
            "cmd /c del important.txt",
            "powershell -NoProfile -Command Remove-Item important.txt",
            "git -c credential.helper= push origin main",
            "python -c \"import os; os.remove('important.txt')\"",
            "py cleanup.py",
            "bash -c 'curl https://example.invalid'",
        )
        for index, command in enumerate(commands):
            with self.subTest(command=command):
                broker = gateway_module.ExplicitApprovalBroker(timeout_seconds=1)
                response = broker.handler(
                    "item/commandExecution/requestApproval",
                    {
                        "threadId": f"thread-indirect-{index}",
                        "turnId": f"turn-indirect-{index}",
                        "itemId": f"item-indirect-{index}",
                        "startedAtMs": 1,
                        "kind": "command",
                        "availableDecisions": ["accept", "decline"],
                        "command": command,
                    },
                )
                self.assertEqual(response, {"decision": "decline"})
                self.assertEqual(broker.list_pending(), [])

    def test_absolute_and_unc_path_commands_are_not_approvable(self) -> None:
        base = {
            "threadId": "thread-path-1",
            "turnId": "turn-path-1",
            "itemId": "item-path-1",
            "startedAtMs": 1,
            "kind": "command",
            "availableDecisions": ["accept", "decline"],
            "cwd": r"C:\Users\private-user\Secret Workspace",
            "reason": r"Review C:\Users\private-user\Secret Workspace\plan.txt",
        }
        commands = (
            r'rg target "C:\Users\private-user\Secret Workspace\plan.txt"',
            r'rg target "\\server\private share\plan.txt"',
            "rg target '/home/private user/plan.txt'",
            r'C:\Windows\System32\cmd.exe /c echo pwned',
            r'C:\Python311\python.exe -c "open(\'workspace\\x.txt\',\'w\').write(\'x\')"',
        )
        for index, command in enumerate(commands):
            with self.subTest(command=command):
                broker = gateway_module.ExplicitApprovalBroker(timeout_seconds=1)
                self.assertEqual(
                    broker._command_summary(command),
                    "[COMMAND_REDACTED_ABSOLUTE_PATH]",
                )
                response = broker.handler(
                    "item/commandExecution/requestApproval",
                    {**base, "itemId": f"item-path-{index}", "command": command},
                )
                self.assertEqual(response, {"decision": "decline"})
                self.assertEqual(broker.list_pending(), [])

    def test_opaque_file_change_approval_fails_closed(self) -> None:
        broker = gateway_module.ExplicitApprovalBroker(timeout_seconds=1)
        response = broker.handler(
            "item/fileChange/requestApproval",
            {
                "threadId": "thread-file-1",
                "turnId": "turn-file-1",
                "itemId": "item-file-1",
                "startedAtMs": 1,
                "reason": "Apply hidden patch content",
                "grantRoot": None,
            },
        )
        self.assertEqual(response, {"decision": "decline"})
        self.assertEqual(broker.list_pending(), [])

    def test_file_change_approval_requires_exact_cached_review_and_workspace_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            workspace = root / "workspace"
            workspace.mkdir()
            journal = runtime_module.FullAgentApprovalJournal(root / "journal")
            broker = gateway_module.ExplicitApprovalBroker(
                timeout_seconds=2,
                approval_journal=journal,
            )
            broker.bind_thread_workspace("thread-file-safe", [str(workspace)])
            projection = gateway_module._trusted_file_change_projection(
                {
                    "threadId": "thread-file-safe",
                    "turnId": "turn-file-safe",
                    "itemId": "item-file-safe",
                    "changes": [
                        {
                            "path": "notes.txt",
                            "kind": {"type": "add"},
                            "diff": "@@ -0,0 +1 @@\n+hello\n",
                        }
                    ],
                }
            )
            result: dict = {}
            worker = threading.Thread(
                target=lambda: result.update(
                    broker.handler(
                        "item/fileChange/requestApproval",
                        {
                            "threadId": "thread-file-safe",
                            "turnId": "turn-file-safe",
                            "itemId": "item-file-safe",
                            "startedAtMs": 1,
                            "reason": "bounded patch",
                            "grantRoot": None,
                            gateway_module._INTERNAL_FILE_CHANGE_PROJECTION: projection,
                        },
                    )
                )
            )
            worker.start()
            deadline = time.time() + 1
            pending = []
            while time.time() < deadline and not pending:
                pending = broker.list_pending()
                time.sleep(0.01)
            self.assertEqual(len(pending), 1)
            request = pending[0]
            self.assertEqual(request["fileChanges"][0]["path"], "notes.txt")
            self.assertEqual(request["fileChanges"][0]["kind"], "add")
            self.assertEqual(request["fileChanges"][0]["diff"], "@@ -0,0 +1 @@\n+hello\n")
            self.assertEqual(len(request["requestDigest"]), 64)
            self.assertNotEqual(request["requestDigest"], request["sdkRequestDigest"])
            self.assertTrue(
                broker.resolve(
                    request["requestId"],
                    "decline",
                    idempotency_key="file-change-decline-1",
                    thread_id=request["threadId"],
                    turn_id=request["turnId"],
                    item_id=request["itemId"],
                    request_digest=request["requestDigest"],
                    decision_nonce=request["decisionNonce"],
                )
            )
            worker.join(2)
            self.assertEqual(result, {"decision": "decline"})
            journal_text = (root / "journal" / runtime_module.APPROVAL_JOURNAL_FILENAME).read_text(
                encoding="utf-8"
            )
            self.assertNotIn("notes.txt", journal_text)
            self.assertNotIn("+hello", journal_text)

    def test_file_change_review_rejects_unbounded_sensitive_or_non_relative_input(self) -> None:
        base = {
            "threadId": "thread-file-invalid",
            "turnId": "turn-file-invalid",
            "itemId": "item-file-invalid",
        }
        invalid_changes = (
            [{"path": "../outside.txt", "kind": {"type": "add"}, "diff": "+x\n"}],
            [{"path": r"C:\\private\\outside.txt", "kind": {"type": "add"}, "diff": "+x\n"}],
            [{"path": "safe.txt", "kind": {"type": "add"}, "diff": "+api_key=abcd1234\n"}],
            [
                {
                    "path": "safe.txt",
                    "kind": {"type": "add"},
                    "diff": "+" + ("x" * (gateway_module.MAX_APPROVAL_DIFF_BYTES_PER_FILE + 1)),
                }
            ],
        )
        for changes in invalid_changes:
            with self.subTest(changes=changes[0]["path"]):
                with self.assertRaises(gateway_module.PolicyViolation):
                    gateway_module._trusted_file_change_projection({**base, "changes": changes})

    def test_resolve_waits_for_terminal_callback_instead_of_timing_out_false(self) -> None:
        callback_entered = threading.Event()
        callback_release = threading.Event()

        def on_resolved(_request, _outcome):
            callback_entered.set()
            callback_release.wait(2)
            return True

        broker = gateway_module.ExplicitApprovalBroker(
            timeout_seconds=2,
            resolution_wait_seconds=1,
            on_resolved=on_resolved,
        )
        protocol_result: dict = {}
        handler_thread = threading.Thread(
            target=lambda: protocol_result.update(
                broker.handler(
                    "item/commandExecution/requestApproval",
                    {
                        "threadId": "thread-wait-1",
                        "turnId": "turn-wait-1",
                        "itemId": "item-wait-1",
                        "startedAtMs": 1,
                        "kind": "command",
                        "availableDecisions": ["accept", "decline"],
                        "command": "rg bounded_target .",
                    },
                )
            ),
        )
        handler_thread.start()
        deadline = time.time() + 1
        pending = []
        while time.time() < deadline and not pending:
            pending = broker.list_pending()
            time.sleep(0.01)
        self.assertEqual(len(pending), 1)
        approval = pending[0]
        resolve_result: dict = {}
        resolver = threading.Thread(
            target=lambda: resolve_result.update(
                value=broker.resolve(
                    approval["requestId"],
                    "accept_once",
                    idempotency_key="approval-wait-1",
                    thread_id=approval["threadId"],
                    turn_id=approval["turnId"],
                    item_id=approval["itemId"],
                    request_digest=approval["requestDigest"],
                    decision_nonce=approval["decisionNonce"],
                )
            ),
        )
        resolver.start()
        self.assertTrue(callback_entered.wait(1))
        time.sleep(0.05)
        self.assertTrue(resolver.is_alive(), "resolve returned before callback reached a terminal outcome")
        callback_release.set()
        resolver.join(2)
        handler_thread.join(2)
        self.assertFalse(resolver.is_alive())
        self.assertFalse(handler_thread.is_alive())
        self.assertTrue(resolve_result["value"])
        self.assertEqual(protocol_result, {"decision": "accept"})

    def test_resolve_reports_pending_not_false_while_accept_may_still_commit(self) -> None:
        callback_entered = threading.Event()
        callback_release = threading.Event()

        def on_resolved(_request, _outcome):
            callback_entered.set()
            callback_release.wait(2)
            return True

        broker = gateway_module.ExplicitApprovalBroker(
            timeout_seconds=2,
            resolution_wait_seconds=0.05,
            on_resolved=on_resolved,
        )
        protocol_result: dict = {}
        handler_thread = threading.Thread(
            target=lambda: protocol_result.update(
                broker.handler(
                    "item/commandExecution/requestApproval",
                    {
                        "threadId": "thread-pending-1",
                        "turnId": "turn-pending-1",
                        "itemId": "item-pending-1",
                        "startedAtMs": 1,
                        "kind": "command",
                        "availableDecisions": ["accept", "decline"],
                        "command": "rg bounded_target .",
                    },
                )
            ),
        )
        handler_thread.start()
        deadline = time.time() + 1
        pending = []
        while time.time() < deadline and not pending:
            pending = broker.list_pending()
            time.sleep(0.01)
        self.assertEqual(len(pending), 1)
        approval = pending[0]
        kwargs = {
            "idempotency_key": "approval-pending-1",
            "thread_id": approval["threadId"],
            "turn_id": approval["turnId"],
            "item_id": approval["itemId"],
            "request_digest": approval["requestDigest"],
            "decision_nonce": approval["decisionNonce"],
        }
        self.assertIsNone(
            broker.resolve(approval["requestId"], "accept_once", **kwargs)
        )
        self.assertTrue(callback_entered.is_set())
        self.assertNotEqual(protocol_result, {"decision": "decline"})
        callback_release.set()
        handler_thread.join(2)
        self.assertFalse(handler_thread.is_alive())
        self.assertEqual(protocol_result, {"decision": "accept"})
        self.assertTrue(
            broker.resolve(approval["requestId"], "accept_once", **kwargs)
        )

    def test_durable_approval_replay_survives_broker_restart_without_raw_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            journal = runtime_module.FullAgentApprovalJournal(Path(temp).resolve())
            broker = gateway_module.ExplicitApprovalBroker(
                timeout_seconds=2,
                approval_journal=journal,
            )
            protocol_result: dict = {}
            worker = threading.Thread(
                target=lambda: protocol_result.update(
                    broker.handler(
                        "item/commandExecution/requestApproval",
                        {
                            "threadId": "thread-durable-1",
                            "turnId": "turn-durable-1",
                            "itemId": "item-durable-1",
                            "startedAtMs": 1,
                            "kind": "command",
                            "availableDecisions": ["accept", "decline"],
                            "command": "rg bounded_target .",
                        },
                    )
                )
            )
            worker.start()
            deadline = time.time() + 1
            pending = []
            while time.time() < deadline and not pending:
                pending = broker.list_pending()
                time.sleep(0.01)
            self.assertEqual(len(pending), 1)
            approval = pending[0]
            kwargs = {
                "idempotency_key": "approval-durable-key-1",
                "thread_id": approval["threadId"],
                "turn_id": approval["turnId"],
                "item_id": approval["itemId"],
                "request_digest": approval["requestDigest"],
                "decision_nonce": approval["decisionNonce"],
            }
            self.assertTrue(
                broker.resolve(approval["requestId"], "accept_once", **kwargs)
            )
            worker.join(2)
            self.assertEqual(protocol_result, {"decision": "accept"})

            raw = (Path(temp) / runtime_module.APPROVAL_JOURNAL_FILENAME).read_text(
                encoding="utf-8"
            )
            self.assertNotIn(approval["decisionNonce"], raw)
            self.assertNotIn("approval-durable-key-1", raw)
            self.assertNotIn("rg bounded_target", raw)

            restarted = gateway_module.ExplicitApprovalBroker(
                timeout_seconds=2,
                approval_journal=runtime_module.FullAgentApprovalJournal(
                    Path(temp).resolve()
                ),
            )
            self.assertTrue(
                restarted.resolve(
                    approval["requestId"], "accept_once", **kwargs
                )
            )
            with self.assertRaises(gateway_module.PolicyViolation) as conflict:
                restarted.resolve(approval["requestId"], "decline", **kwargs)
            self.assertEqual(conflict.exception.code, "approval_decision_conflict")

    def test_recovered_unfinished_approval_cannot_be_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            first = runtime_module.FullAgentApprovalJournal(root)
            broker = gateway_module.ExplicitApprovalBroker(
                timeout_seconds=2,
                approval_journal=first,
            )
            pending = broker._build_pending(
                "item/commandExecution/requestApproval",
                {
                    "threadId": "thread-restart-1",
                    "turnId": "turn-restart-1",
                    "itemId": "item-restart-1",
                    "startedAtMs": 1,
                    "kind": "command",
                    "availableDecisions": ["accept", "decline"],
                    "command": "rg bounded_target .",
                },
            )
            first.register_pending(
                pending.public_request,
                expires_epoch=pending.expires_epoch,
            )
            restarted = gateway_module.ExplicitApprovalBroker(
                timeout_seconds=2,
                approval_journal=runtime_module.FullAgentApprovalJournal(root),
            )
            self.assertFalse(
                restarted.resolve(
                    pending.request_id,
                    "accept_once",
                    idempotency_key="approval-restart-key-1",
                    thread_id=pending.thread_id,
                    turn_id=pending.turn_id,
                    item_id=pending.item_id,
                    request_digest=pending.request_digest,
                    decision_nonce=pending.decision_nonce,
                )
            )
            self.assertEqual(restarted.list_pending(), [])

    def test_durable_register_or_terminal_commit_failure_never_accepts(self) -> None:
        class RegisterFails:
            def register_pending(self, _request, *, expires_epoch):
                del expires_epoch
                raise RuntimeError("disk unavailable")

        published: list[dict] = []
        register_broker = gateway_module.ExplicitApprovalBroker(
            timeout_seconds=1,
            approval_journal=RegisterFails(),
            on_pending=lambda request: published.append(dict(request)),
        )
        self.assertEqual(
            register_broker.handler(
                "item/commandExecution/requestApproval",
                {
                    "threadId": "thread-register-fail",
                    "turnId": "turn-register-fail",
                    "itemId": "item-register-fail",
                    "startedAtMs": 1,
                    "kind": "command",
                    "availableDecisions": ["accept", "decline"],
                    "command": "rg bounded_target .",
                },
            ),
            {"decision": "decline"},
        )
        self.assertEqual(published, [])
        self.assertEqual(register_broker.list_pending(), [])

        with tempfile.TemporaryDirectory() as temp:
            real = runtime_module.FullAgentApprovalJournal(Path(temp).resolve())

            class CommitFails:
                register_pending = real.register_pending
                claim_decision = real.claim_decision

                @staticmethod
                def commit_resolution(*_args, **_kwargs):
                    raise RuntimeError("fsync failed")

            broker = gateway_module.ExplicitApprovalBroker(
                timeout_seconds=2,
                approval_journal=CommitFails(),
            )
            protocol_result: dict = {}
            worker = threading.Thread(
                target=lambda: protocol_result.update(
                    broker.handler(
                        "item/commandExecution/requestApproval",
                        {
                            "threadId": "thread-commit-fail",
                            "turnId": "turn-commit-fail",
                            "itemId": "item-commit-fail",
                            "startedAtMs": 1,
                            "kind": "command",
                            "availableDecisions": ["accept", "decline"],
                            "command": "rg bounded_target .",
                        },
                    )
                )
            )
            worker.start()
            deadline = time.time() + 1
            pending = []
            while time.time() < deadline and not pending:
                pending = broker.list_pending()
                time.sleep(0.01)
            approval = pending[0]
            self.assertFalse(
                broker.resolve(
                    approval["requestId"],
                    "accept_once",
                    idempotency_key="approval-commit-fail-key",
                    thread_id=approval["threadId"],
                    turn_id=approval["turnId"],
                    item_id=approval["itemId"],
                    request_digest=approval["requestDigest"],
                    decision_nonce=approval["decisionNonce"],
                )
            )
            worker.join(2)
            self.assertEqual(protocol_result, {"decision": "decline"})


class DeferredServerRequestReaderTests(unittest.TestCase):
    class _Router:
        def __init__(self) -> None:
            self.responses: list[dict] = []
            self.notifications: list[object] = []
            self.failures: list[BaseException] = []
            self.response_seen = threading.Event()

        def route_response(self, message: dict) -> None:
            self.responses.append(dict(message))
            self.response_seen.set()

        def route_notification(self, notification: object) -> None:
            self.notifications.append(notification)

        def fail_all(self, error: BaseException) -> None:
            self.failures.append(error)

    class _Harness(gateway_module._DeferredServerRequestReaderMixin):
        def __init__(self, *, max_workers: int = 4) -> None:
            self._MAX_SERVER_REQUEST_WORKERS = max_workers
            self.messages: queue.Queue = queue.Queue()
            self.writes: list[dict] = []
            self.write_seen = threading.Event()
            self.handler_entered = threading.Event()
            self.handler_release = threading.Event()
            self.raise_from_handler = False
            self._router = DeferredServerRequestReaderTests._Router()

        def _read_message(self) -> dict:
            value = self.messages.get(timeout=2)
            if value is None:
                raise EOFError("fixture complete")
            return value

        def _handle_server_request(self, message: dict) -> dict:
            self.handler_entered.set()
            if self.raise_from_handler:
                raise RuntimeError("private failure")
            self.handler_release.wait(2)
            return {"decision": "decline"}

        def _write_message(self, payload: dict) -> None:
            self.writes.append(dict(payload))
            self.write_seen.set()

        @staticmethod
        def _coerce_notification(method: str, params: object) -> tuple:
            return method, params

    def test_reader_routes_client_response_while_approval_worker_waits(self) -> None:
        client = self._Harness()
        reader = threading.Thread(target=client._reader_loop, daemon=True)
        reader.start()
        client.messages.put(
            {
                "id": "server-request-1",
                "method": "item/commandExecution/requestApproval",
                "params": {"threadId": "thread-1"},
            }
        )
        self.assertTrue(client.handler_entered.wait(1))
        client.messages.put({"id": "client-interrupt-1", "result": {"ok": True}})
        self.assertTrue(
            client._router.response_seen.wait(1),
            "sole reader stopped routing while approval waited",
        )
        self.assertEqual(client._router.responses[0]["id"], "client-interrupt-1")
        self.assertEqual(client.writes, [])
        client.handler_release.set()
        self.assertTrue(client.write_seen.wait(1))
        self.assertEqual(
            client.writes[0],
            {"id": "server-request-1", "result": {"decision": "decline"}},
        )
        client.messages.put(None)
        reader.join(2)
        self.assertFalse(reader.is_alive())

    def test_reader_worker_capacity_and_handler_errors_fail_closed(self) -> None:
        client = self._Harness(max_workers=1)
        reader = threading.Thread(target=client._reader_loop, daemon=True)
        reader.start()
        client.messages.put(
            {"id": "server-request-blocked", "method": "approval", "params": {}}
        )
        self.assertTrue(client.handler_entered.wait(1))
        client.messages.put(
            {"id": "server-request-over-capacity", "method": "approval", "params": {}}
        )
        deadline = time.time() + 1
        while time.time() < deadline and not client.writes:
            time.sleep(0.01)
        self.assertEqual(client.writes[0]["id"], "server-request-over-capacity")
        self.assertEqual(client.writes[0]["error"]["code"], -32001)
        client.handler_release.set()
        deadline = time.time() + 1
        while time.time() < deadline and len(client.writes) < 2:
            time.sleep(0.01)
        client.messages.put(None)
        reader.join(2)
        self.assertEqual(len(client.writes), 2)

        failing = self._Harness()
        failing.raise_from_handler = True
        failing_reader = threading.Thread(target=failing._reader_loop, daemon=True)
        failing_reader.start()
        failing.messages.put(
            {"id": "server-request-error", "method": "unknown/request", "params": {}}
        )
        self.assertTrue(failing.write_seen.wait(1))
        self.assertEqual(failing.writes[0]["error"]["code"], -32601)
        self.assertNotIn("private failure", json.dumps(failing.writes))
        failing.messages.put({"id": "later-client-response", "result": {"ok": True}})
        self.assertTrue(failing._router.response_seen.wait(1))
        failing.messages.put(None)
        failing_reader.join(2)

    def test_patch_updated_projection_is_exact_bound_single_use_and_poisoned_fail_closed(self) -> None:
        client = self._Harness()
        patch = {
            "threadId": "thread-patch-1",
            "turnId": "turn-patch-1",
            "itemId": "item-patch-1",
            "changes": [
                {
                    "path": "src/safe.txt",
                    "kind": {"type": "add"},
                    "diff": "@@ -0,0 +1 @@\n+safe\n",
                }
            ],
        }
        client._capture_file_change_patch(patch)
        request = {
            "id": "approval-patch-1",
            "method": "item/fileChange/requestApproval",
            "params": {
                "threadId": "thread-patch-1",
                "turnId": "turn-patch-1",
                "itemId": "item-patch-1",
                "startedAtMs": 1,
                gateway_module._INTERNAL_FILE_CHANGE_PROJECTION: "untrusted-json-value",
            },
        }
        prepared = client._server_request_with_projection(request)
        trusted = prepared["params"][gateway_module._INTERNAL_FILE_CHANGE_PROJECTION]
        self.assertIsInstance(trusted, gateway_module._TrustedFileChangeProjection)
        self.assertEqual(trusted.thread_id, "thread-patch-1")
        self.assertNotIn(
            gateway_module._INTERNAL_FILE_CHANGE_PROJECTION,
            client._server_request_with_projection(request)["params"],
            "one patch notification must not authorize two requests",
        )

        # A later malformed update for the same binding invalidates, rather
        # than falling back to, an earlier valid projection.
        client._capture_file_change_patch(patch)
        client._capture_file_change_patch(
            {
                **patch,
                "changes": [
                    {"path": "../outside.txt", "kind": {"type": "add"}, "diff": "+x\n"}
                ],
            }
        )
        self.assertNotIn(
            gateway_module._INTERNAL_FILE_CHANGE_PROJECTION,
            client._server_request_with_projection(request)["params"],
        )

        client._capture_file_change_patch(patch)
        mismatched = {
            **request,
            "params": {**request["params"], "turnId": "turn-patch-other"},
        }
        self.assertNotIn(
            gateway_module._INTERNAL_FILE_CHANGE_PROJECTION,
            client._server_request_with_projection(mismatched)["params"],
        )


class SdkGatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = str(Path(self.temp.name).resolve())
        self.client = FakeClient()
        self.factory = CapturingFactory(self.client)
        self.gateway = gateway_module.CodexAppServerGateway(
            cwd=self.workspace,
            client_factory=self.factory,
            model_catalog=model_catalog(),
        )
        self.policy = {
            "agentId": "ea_developer",
            "mode": "workspace",
            "model": "gpt-safe",
            "reasoningEffort": "medium",
            "cwd": self.workspace,
            "approvalMode": "deny_all",
        }

    def tearDown(self) -> None:
        self.gateway.close()
        self.temp.cleanup()

    def test_client_factory_always_receives_explicit_fail_closed_handler(self) -> None:
        status = self.gateway.status()
        self.assertTrue(status["ok"])
        self.assertEqual(status["status"], "ready")
        self.assertEqual(
            status["authentication"],
            {
                "authenticated": True,
                "requiresOpenaiAuth": True,
                "accountType": "chatgpt",
            },
        )
        self.assertIsNotNone(self.factory.kwargs)
        handler = self.factory.kwargs["approval_handler"]
        self.assertIs(handler, gateway_module.fail_closed_approval_handler)
        self.assertEqual(
            handler("item/commandExecution/requestApproval", {}),
            {"decision": "decline"},
        )
        self.assertEqual(status["approvalHandler"], "explicit_fail_closed")
        self.assertFalse(status["automaticExternalEffects"])
        encoded = json.dumps(status)
        self.assertNotIn("accessToken", encoded)
        self.assertNotIn("private@example.test", encoded)
        self.assertNotIn("planType", encoded)
        self.assertNotIn("must-not-leak", encoded)

    def test_stock_sdk_never_wires_blocking_interactive_broker(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            journal = runtime_module.FullAgentApprovalJournal(Path(temp).resolve())
            broker = gateway_module.ExplicitApprovalBroker(
                timeout_seconds=1,
                approval_journal=journal,
            )
            client = FakeClient()
            factory = CapturingFactory(client)
            gateway = gateway_module.CodexAppServerGateway(
                cwd=self.workspace,
                client_factory=factory,
                approval_broker=broker,
                model_catalog=model_catalog(),
            )
            try:
                status = gateway.status()
                self.assertFalse(status["approvalBrokerReady"])
                self.assertTrue(status["approvalReplayDurable"])
                self.assertFalse(status["deferredServerRequestsSupported"])
                self.assertEqual(status["approvalHandler"], "explicit_fail_closed")
                handler = factory.kwargs["approval_handler"]
                started = time.monotonic()
                self.assertEqual(
                    handler(
                        "item/commandExecution/requestApproval",
                        {"threadId": "thread-no-deadlock"},
                    ),
                    {"decision": "decline"},
                )
                self.assertLess(time.monotonic() - started, 0.25)
                gateway.thread_start(self.policy)
                turn_start_calls_before = sum(
                    call[0] == "turn_start" for call in client.calls
                )
                with self.assertRaises(gateway_module.PolicyViolation) as caught:
                    gateway.turn_start(
                        "thread-1",
                        "Do not run while deferred approvals are unsupported",
                        policy_value={**self.policy, "approvalMode": "explicit"},
                    )
                self.assertEqual(caught.exception.code, "approval_broker_required")
                self.assertEqual(
                    sum(call[0] == "turn_start" for call in client.calls),
                    turn_start_calls_before,
                )
            finally:
                gateway.close()

    def test_deferred_transport_flag_wires_only_durable_broker(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            journal = runtime_module.FullAgentApprovalJournal(Path(temp).resolve())
            durable = gateway_module.ExplicitApprovalBroker(
                timeout_seconds=1,
                approval_journal=journal,
            )
            factory = CapturingFactory(FakeClient())
            gateway = gateway_module.CodexAppServerGateway(
                cwd=self.workspace,
                client_factory=factory,
                approval_broker=durable,
                deferred_server_requests_supported=True,
                model_catalog=model_catalog(),
            )
            try:
                status = gateway.status()
                self.assertTrue(status["approvalBrokerReady"])
                self.assertTrue(status["approvalReplayDurable"])
                self.assertTrue(status["deferredServerRequestsSupported"])
                self.assertEqual(status["approvalHandler"], "explicit_one_shot")
                self.assertTrue(
                    factory.kwargs["deferred_server_requests_supported"]
                )
                handler = factory.kwargs["approval_handler"]
                self.assertIs(getattr(handler, "__self__", None), durable)
            finally:
                gateway.close()

            volatile = gateway_module.ExplicitApprovalBroker(timeout_seconds=1)
            volatile_factory = CapturingFactory(FakeClient())
            volatile_gateway = gateway_module.CodexAppServerGateway(
                cwd=self.workspace,
                client_factory=volatile_factory,
                approval_broker=volatile,
                deferred_server_requests_supported=True,
                model_catalog=model_catalog(),
            )
            try:
                volatile_status = volatile_gateway.status()
                self.assertFalse(volatile_status["approvalBrokerReady"])
                self.assertFalse(
                    volatile_factory.kwargs["deferred_server_requests_supported"]
                )
                self.assertIs(
                    volatile_factory.kwargs["approval_handler"],
                    gateway_module.fail_closed_approval_handler,
                )
            finally:
                volatile_gateway.close()

    def test_status_reports_auth_required_without_exposing_account_fields(self) -> None:
        with mock.patch.object(
            self.client,
            "account_read",
            return_value={
                "account": None,
                "requiresOpenaiAuth": True,
                "email": "private@example.test",
                "accessToken": "must-not-leak",
            },
        ):
            status = self.gateway.status()

        self.assertFalse(status["ok"])
        self.assertEqual(status["status"], "auth_required")
        self.assertEqual(
            status["authentication"],
            {
                "authenticated": False,
                "requiresOpenaiAuth": True,
                "accountType": None,
            },
        )
        encoded = json.dumps(status)
        self.assertNotIn("private@example.test", encoded)
        self.assertNotIn("must-not-leak", encoded)

    def test_models_mcp_and_plugins_are_allowlist_projected(self) -> None:
        with mock.patch.object(gateway_module, "_sdk_response_model", return_value=dict):
            models = self.gateway.models()
            mcp = self.gateway.mcp_status()
            plugins = self.gateway.plugins()

        self.assertEqual(models["models"][0]["model"], "gpt-safe")
        self.assertEqual(mcp["servers"][0]["toolCount"], 1)
        self.assertEqual(mcp["servers"][0]["tools"][0]["name"], "read_file")
        self.assertEqual(plugins["plugins"][0]["id"], "safe-plugin")
        encoded = json.dumps({"mcp": mcp, "plugins": plugins})
        self.assertNotIn("must-not-leak", encoded)
        self.assertNotIn("C:/private", encoded)

    def test_thread_start_enforces_safe_policy_in_sdk_params(self) -> None:
        result = self.gateway.thread_start(self.policy)
        self.assertEqual(result["thread"]["id"], "thread-1")
        call = next(call for call in self.client.calls if call[0] == "thread_start")
        params = call[1]
        self.assertEqual(params["approvalPolicy"], "never")
        self.assertEqual(params["sandbox"], "workspace-write")
        self.assertNotEqual(params["sandbox"], "danger-full-access")
        self.assertTrue(params["config"]["features"]["shell_tool"])
        self.assertFalse(params["config"]["features"]["plugins"])
        self.assertEqual(result["policy"]["autoExternalEffects"], False)

    def test_thread_start_discovers_model_catalog_before_trusting_selection(self) -> None:
        fresh_client = FakeClient()
        fresh_gateway = gateway_module.CodexAppServerGateway(
            cwd=self.workspace,
            client_factory=CapturingFactory(fresh_client),
        )
        try:
            result = fresh_gateway.thread_start(self.policy)
        finally:
            fresh_gateway.close()
        self.assertEqual(result["thread"]["id"], "thread-1")
        call_names = [call[0] for call in fresh_client.calls]
        self.assertLess(call_names.index("model_list"), call_names.index("thread_start"))

    def test_thread_start_fails_closed_when_discovered_model_catalog_is_empty(self) -> None:
        fresh_client = FakeClient()

        def empty_model_list(include_hidden: bool = False) -> dict:
            fresh_client.calls.append(("model_list", include_hidden))
            return {"data": []}

        fresh_gateway = gateway_module.CodexAppServerGateway(
            cwd=self.workspace,
            client_factory=CapturingFactory(fresh_client),
        )
        try:
            with mock.patch.object(
                fresh_client,
                "model_list",
                side_effect=empty_model_list,
            ):
                with self.assertRaises(gateway_module.PolicyViolation) as caught:
                    fresh_gateway.thread_start(self.policy)
        finally:
            fresh_gateway.close()

        self.assertEqual(caught.exception.code, "model_catalog_unavailable")
        self.assertTrue(any(call[0] == "model_list" for call in fresh_client.calls))
        self.assertFalse(any(call[0] == "thread_start" for call in fresh_client.calls))

    def test_thread_start_fails_closed_when_model_catalog_request_fails(self) -> None:
        fresh_client = FakeClient()

        def unavailable_model_list(include_hidden: bool = False) -> dict:
            fresh_client.calls.append(("model_list", include_hidden))
            raise RuntimeError("private provider failure")

        fresh_gateway = gateway_module.CodexAppServerGateway(
            cwd=self.workspace,
            client_factory=CapturingFactory(fresh_client),
        )
        try:
            with mock.patch.object(
                fresh_client,
                "model_list",
                side_effect=unavailable_model_list,
            ):
                with self.assertRaises(gateway_module.GatewayError) as caught:
                    fresh_gateway.thread_start(self.policy)
        finally:
            fresh_gateway.close()

        self.assertEqual(caught.exception.code, "model_catalog_unavailable")
        self.assertNotIn("private provider failure", caught.exception.message)
        self.assertFalse(any(call[0] == "thread_start" for call in fresh_client.calls))

    def test_turn_start_wait_returns_sanitized_assistant_text(self) -> None:
        self.gateway.thread_start(self.policy)
        result = self.gateway.turn_start("thread-1", "Write safe tests", wait=True)

        self.assertEqual(result["status"], "completed")
        terminal = result["completed"]
        self.assertIn("Finished safely", terminal["turn"]["assistantText"])
        encoded = json.dumps(terminal)
        self.assertNotIn("password.txt", encoded)
        self.assertNotIn("client_secret", encoded)
        turn_call = next(call for call in self.client.calls if call[0] == "turn_start")
        params = turn_call[3]
        self.assertEqual(params["approvalPolicy"], "never")
        self.assertEqual(params["sandboxPolicy"]["type"], "workspaceWrite")
        self.assertNotEqual(params["sandboxPolicy"]["type"], "dangerFullAccess")
        self.assertTrue(any(call[0] == "thread_read" for call in self.client.calls))
        self.assertFalse(any(call[0] == "turn_wait" for call in self.client.calls))
        self.assertFalse(self.client.registered_turns)

    def test_turn_wait_registers_before_snapshot_then_uses_notification_wait(self) -> None:
        self.gateway.thread_start(self.policy)
        started = self.gateway.turn_start("thread-1", "Wait for completion", wait=False)
        turn_id = started["turn"]["id"]

        original_read = self.client.thread_read

        def in_progress_read(thread_id: str, include_turns: bool = False) -> dict:
            response = original_read(thread_id, include_turns)
            response["thread"]["turns"] = [
                {
                    "id": turn_id,
                    "status": "inProgress",
                    "startedAt": 10,
                    "items": [],
                }
            ]
            return response

        with mock.patch.object(self.client, "thread_read", side_effect=in_progress_read):
            completed = self.gateway.turn_wait(turn_id, thread_id="thread-1")

        self.assertEqual(completed["status"], "completed")
        names = [call[0] for call in self.client.calls]
        self.assertLess(names.index("turn_register"), names.index("thread_read"))
        self.assertLess(names.index("thread_read"), names.index("turn_wait"))
        self.assertFalse(self.client.registered_turns)

    def test_turn_wait_falls_back_when_new_thread_snapshot_is_temporarily_unreadable(self) -> None:
        self.gateway.thread_start(self.policy)
        started = self.gateway.turn_start("thread-1", "Wait for completion", wait=False)
        turn_id = started["turn"]["id"]

        with mock.patch.object(
            self.client,
            "thread_read",
            side_effect=RuntimeError("temporary empty rollout"),
        ):
            completed = self.gateway.turn_wait(turn_id, thread_id="thread-1")

        self.assertTrue(completed["ok"])
        self.assertEqual(completed["status"], "completed")
        names = [call[0] for call in self.client.calls]
        self.assertLess(names.index("turn_register"), names.index("turn_wait"))
        self.assertFalse(self.client.registered_turns)

    def test_thread_resume_rejects_running_and_stopping_sessions(self) -> None:
        self.gateway.thread_start(self.policy)
        started = self.gateway.turn_start("thread-1", "First turn", wait=False)

        with self.assertRaises(gateway_module.GatewayError) as running_error:
            self.gateway.thread_resume("thread-1", self.policy)
        self.assertEqual(running_error.exception.code, "thread_busy")

        self.gateway.turn_interrupt("thread-1", started["turn"]["id"])
        with self.assertRaises(gateway_module.GatewayError) as stopping_error:
            self.gateway.thread_resume("thread-1", self.policy)
        self.assertEqual(stopping_error.exception.code, "thread_busy")
        self.assertFalse(any(call[0] == "thread_resume" for call in self.client.calls))

        current = self.gateway.sessions["thread-1"]
        self.gateway.sessions["thread-1"] = gateway_module.ThreadSessionState(
            thread_id=current.thread_id,
            agent_id=current.agent_id,
            status=gateway_module.SessionStatus.WAITING_APPROVAL,
            policy=current.policy,
            active_turn_id=started["turn"]["id"],
        )
        with self.assertRaises(gateway_module.GatewayError) as waiting_error:
            self.gateway.thread_resume("thread-1", self.policy)
        self.assertEqual(waiting_error.exception.code, "thread_busy")
        self.assertFalse(any(call[0] == "thread_resume" for call in self.client.calls))

    def test_turn_start_rechecks_owner_inside_session_lock(self) -> None:
        self.gateway.thread_start(self.policy)
        current = self.gateway.sessions["thread-1"]
        self.gateway.sessions["thread-1"] = gateway_module.ThreadSessionState(
            thread_id=current.thread_id,
            agent_id="manager",
            status=gateway_module.SessionStatus.IDLE,
            policy=current.policy,
        )

        with self.assertRaises(gateway_module.PolicyViolation) as caught:
            self.gateway.turn_start("thread-1", "Must not cross Agent ownership")

        self.assertEqual(caught.exception.code, "thread_owner_mismatch")
        self.assertFalse(any(call[0] == "turn_start" for call in self.client.calls))


class StructuredMediaTests(unittest.TestCase):
    PNG_BYTES = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    )

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name).resolve()
        self.managed = self.workspace / "managed-artifacts"
        self.managed.mkdir()
        self.image = self.managed / "chart.png"
        self.image.write_bytes(self.PNG_BYTES)
        self.client = FakeClient()
        self.gateway = gateway_module.CodexAppServerGateway(
            cwd=str(self.workspace),
            client_factory=CapturingFactory(self.client),
            model_catalog=model_catalog(),
            attachment_roots=[self.managed],
        )
        self.policy = {
            "agentId": "technical_consultant",
            "mode": "chat",
            "model": "gpt-safe",
            "reasoningEffort": "medium",
            "cwd": str(self.workspace),
            "approvalMode": "deny_all",
        }

    def tearDown(self) -> None:
        self.gateway.close()
        self.temp.cleanup()

    def test_status_truthfully_advertises_managed_media_capability(self) -> None:
        status = self.gateway.status()

        self.assertTrue(status["attachments"]["configured"])
        self.assertEqual(
            status["attachments"]["inputTypes"],
            ["text", "image", "localImage"],
        )
        self.assertTrue(status["attachments"]["artifactProjection"])
        self.assertFalse(status["automaticExternalEffects"])

    def test_status_without_explicit_root_stays_text_only(self) -> None:
        gateway = gateway_module.CodexAppServerGateway(
            cwd=str(self.workspace),
            client_factory=CapturingFactory(FakeClient()),
            model_catalog=model_catalog(),
        )
        try:
            status = gateway.status()
        finally:
            gateway.close()

        self.assertFalse(status["attachments"]["configured"])
        self.assertEqual(status["attachments"]["inputTypes"], ["text", "image"])
        self.assertFalse(status["attachments"]["artifactProjection"])

    def test_constructor_rejects_relative_attachment_root(self) -> None:
        with self.assertRaises(gateway_module.PolicyViolation) as caught:
            gateway_module.CodexAppServerGateway(
                cwd=str(self.workspace),
                client_factory=CapturingFactory(FakeClient()),
                model_catalog=model_catalog(),
                attachment_roots=["relative/uploads"],
            )

        self.assertEqual(caught.exception.code, "invalid_attachment_root")

    def test_local_image_is_validated_and_sent_as_structured_sdk_input(self) -> None:
        self.gateway.thread_start(self.policy)
        self.gateway.turn_start(
            "thread-1",
            "Read this chart",
            input_items=[
                {"type": "localImage", "path": str(self.image), "detail": "high"}
            ],
        )

        turn_call = next(call for call in self.client.calls if call[0] == "turn_start")
        sdk_input = turn_call[2]
        self.assertEqual(sdk_input[0], {"type": "text", "text": "Read this chart"})
        self.assertEqual(sdk_input[1]["type"], "localImage")
        self.assertEqual(Path(sdk_input[1]["path"]), self.image.resolve())
        self.assertEqual(sdk_input[1]["detail"], "high")
        self.assertNotEqual(turn_call[3]["sandboxPolicy"]["type"], "dangerFullAccess")

    def test_local_image_outside_managed_root_is_denied_before_sdk_call(self) -> None:
        outside = self.workspace / "outside.png"
        outside.write_bytes(self.PNG_BYTES)
        self.gateway.thread_start(self.policy)

        with self.assertRaises(gateway_module.PolicyViolation) as caught:
            self.gateway.turn_start(
                "thread-1",
                "Read this chart",
                input_items=[{"type": "localImage", "path": str(outside)}],
            )

        self.assertEqual(caught.exception.code, "invalid_local_image")
        self.assertFalse(any(call[0] == "turn_start" for call in self.client.calls))

    def test_local_image_extension_must_match_magic_bytes(self) -> None:
        fake = self.managed / "fake.png"
        fake.write_bytes(b"not a png")
        self.gateway.thread_start(self.policy)

        with self.assertRaises(gateway_module.PolicyViolation) as caught:
            self.gateway.turn_start(
                "thread-1",
                "Read this chart",
                input_items=[{"type": "localImage", "path": str(fake)}],
            )

        self.assertEqual(caught.exception.code, "invalid_local_image_type")

    def test_linked_local_image_is_denied(self) -> None:
        self.gateway.thread_start(self.policy)
        with mock.patch.object(gateway_module, "_is_link_or_reparse", return_value=True):
            with self.assertRaises(gateway_module.PolicyViolation) as caught:
                self.gateway.turn_start(
                    "thread-1",
                    "Read this chart",
                    input_items=[{"type": "localImage", "path": str(self.image)}],
                )

        self.assertEqual(caught.exception.code, "invalid_local_image")

    def test_inline_image_accepts_valid_data_url_and_rejects_remote_url(self) -> None:
        data_url = "data:image/png;base64," + base64.b64encode(self.PNG_BYTES).decode("ascii")
        sdk_input, image_count = gateway_module.validate_turn_input(
            "Read this chart",
            [{"type": "image", "url": data_url, "detail": "original"}],
            attachment_roots=(self.managed,),
        )
        self.assertEqual(image_count, 1)
        self.assertEqual(sdk_input[1]["url"], data_url)
        self.assertEqual(sdk_input[1]["detail"], "original")

        with self.assertRaises(gateway_module.PolicyViolation) as caught:
            gateway_module.validate_turn_input(
                "Read this chart",
                [{"type": "image", "url": "https://example.test/private.png"}],
                attachment_roots=(self.managed,),
            )
        self.assertEqual(caught.exception.code, "remote_image_blocked")

    def test_unknown_structured_fields_and_excess_images_are_denied(self) -> None:
        with self.assertRaises(gateway_module.PolicyViolation) as extra_error:
            gateway_module.validate_turn_input(
                "Read this chart",
                [{"type": "localImage", "path": str(self.image), "secret": "x"}],
                attachment_roots=(self.managed,),
            )
        self.assertEqual(extra_error.exception.code, "invalid_turn_input")

        items = [
            {"type": "localImage", "path": str(self.image)}
            for _ in range(gateway_module.MAX_TURN_INPUT_IMAGES + 1)
        ]
        with self.assertRaises(gateway_module.PolicyViolation) as count_error:
            gateway_module.validate_turn_input(
                "Read these charts",
                items,
                attachment_roots=(self.managed,),
            )
        self.assertEqual(count_error.exception.code, "too_many_input_images")

    def test_image_input_fails_closed_for_text_only_model(self) -> None:
        text_only_catalog = model_catalog()
        text_only_catalog[0]["inputModalities"] = ["text"]
        client = FakeClient()
        gateway = gateway_module.CodexAppServerGateway(
            cwd=str(self.workspace),
            client_factory=CapturingFactory(client),
            model_catalog=text_only_catalog,
            attachment_roots=[self.managed],
        )
        try:
            gateway.thread_start(self.policy)
            with self.assertRaises(gateway_module.PolicyViolation) as caught:
                gateway.turn_start(
                    "thread-1",
                    "Read this chart",
                    input_items=[{"type": "localImage", "path": str(self.image)}],
                )
        finally:
            gateway.close()

        self.assertEqual(caught.exception.code, "unsupported_model_modality")
        self.assertFalse(any(call[0] == "turn_start" for call in client.calls))

    def test_image_view_projects_opaque_metadata_without_absolute_path(self) -> None:
        projected = gateway_module._project_turn(
            {
                "id": "turn-media",
                "status": "completed",
                "items": [
                    {"id": "image-1", "type": "imageView", "path": str(self.image)},
                    {
                        "id": "tool-1",
                        "type": "commandExecution",
                        "status": "completed",
                        "aggregatedOutput": "client_secret=must-not-leak",
                        "cwd": str(self.workspace),
                    },
                ],
            },
            artifact_projector=self.gateway._project_artifact,
        )

        item = projected["items"][0]
        artifact = item["artifact"]
        self.assertFalse(item["pathHidden"])
        self.assertTrue(artifact["artifactRef"].startswith("artifact-"))
        self.assertEqual(artifact["basename"], "chart.png")
        self.assertEqual(artifact["mediaType"], "image/png")
        self.assertEqual(artifact["byteSize"], len(self.PNG_BYTES))
        self.assertEqual(self.gateway.resolve_artifact(artifact["artifactRef"]), self.image)
        encoded = json.dumps(projected)
        self.assertNotIn(str(self.workspace), encoded)
        self.assertNotIn("must-not-leak", encoded)
        self.assertNotIn("aggregatedOutput", encoded)

    def test_file_artifact_metadata_supports_slides_and_detects_mutation(self) -> None:
        slides = self.managed / "lesson.pptx"
        slides.write_bytes(b"PK\x03\x04safe-slide-fixture")
        projected = gateway_module._project_thread_item(
            {
                "id": "file-1",
                "type": "artifactOutput",
                "status": "completed",
                "outputPath": str(slides),
                "rawOutput": "must-not-leak",
            },
            artifact_projector=self.gateway._project_artifact,
        )
        artifact = projected["artifact"]

        self.assertEqual(artifact["mediaType"], "application/vnd.openxmlformats-officedocument.presentationml.presentation")
        self.assertEqual(artifact["kind"], "file")
        self.assertNotIn(str(slides), json.dumps(projected))
        slides.write_bytes(b"PK\x03\x04changed")
        with self.assertRaises(gateway_module.GatewayError) as caught:
            self.gateway.resolve_artifact(artifact["artifactRef"])
        self.assertEqual(caught.exception.code, "artifact_stale")

    def test_unmanaged_output_path_is_hidden_and_secret_filename_is_masked(self) -> None:
        outside = self.workspace / "outside.png"
        outside.write_bytes(self.PNG_BYTES)
        hidden = gateway_module._project_thread_item(
            {"id": "image-out", "type": "imageView", "path": str(outside)},
            artifact_projector=self.gateway._project_artifact,
        )
        self.assertTrue(hidden["pathHidden"])
        self.assertIsNone(hidden["artifact"])
        self.assertNotIn(str(outside), json.dumps(hidden))

        secret_name = self.managed / "client_secret.png"
        secret_name.write_bytes(self.PNG_BYTES)
        masked = gateway_module._project_thread_item(
            {"id": "image-safe", "type": "imageView", "path": str(secret_name)},
            artifact_projector=self.gateway._project_artifact,
        )
        self.assertEqual(masked["artifact"]["basename"], "artifact.png")

    def test_process_json_request_forwards_input_items(self) -> None:
        self.gateway.thread_start(self.policy)
        gateway_module.process_json_request(
            {
                "operation": "turn_start",
                "threadId": "thread-1",
                "prompt": "Read this chart",
                "inputItems": [{"type": "localImage", "path": str(self.image)}],
            },
            self.gateway,
        )
        turn_call = next(call for call in self.client.calls if call[0] == "turn_start")
        self.assertEqual(turn_call[2][1]["type"], "localImage")


class SdkGatewayLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = str(Path(self.temp.name).resolve())
        self.client = FakeClient()
        self.factory = CapturingFactory(self.client)
        self.gateway = gateway_module.CodexAppServerGateway(
            cwd=self.workspace,
            client_factory=self.factory,
            model_catalog=model_catalog(),
        )
        self.policy = {
            "agentId": "ea_developer",
            "mode": "workspace",
            "model": "gpt-safe",
            "reasoningEffort": "medium",
            "cwd": self.workspace,
            "approvalMode": "deny_all",
        }

    def tearDown(self) -> None:
        self.gateway.close()
        self.temp.cleanup()

    def test_stale_waiter_does_not_clear_newer_active_turn(self) -> None:
        self.gateway.thread_start(self.policy)
        started = self.gateway.turn_start("thread-1", "First turn", wait=False)
        stale_turn_id = started["turn"]["id"]
        current = self.gateway.sessions["thread-1"]
        self.gateway.sessions["thread-1"] = gateway_module.ThreadSessionState(
            thread_id=current.thread_id,
            agent_id=current.agent_id,
            status=gateway_module.SessionStatus.RUNNING,
            policy=current.policy,
            active_turn_id="turn-newer",
        )

        completed = self.gateway.turn_wait(stale_turn_id, thread_id="thread-1")

        self.assertEqual(completed["status"], "completed")
        session = self.gateway.sessions["thread-1"]
        self.assertEqual(session.status, gateway_module.SessionStatus.RUNNING)
        self.assertEqual(session.active_turn_id, "turn-newer")

    def test_busy_thread_is_rejected_before_second_model_call(self) -> None:
        self.gateway.thread_start(self.policy)
        self.gateway.turn_start("thread-1", "First turn", wait=False)
        with self.assertRaises(gateway_module.GatewayError) as caught:
            self.gateway.turn_start("thread-1", "Second turn", wait=False)
        self.assertEqual(caught.exception.code, "thread_busy")
        calls = [call for call in self.client.calls if call[0] == "turn_start"]
        self.assertEqual(len(calls), 1)

    def test_explicit_mode_cannot_run_without_interactive_broker(self) -> None:
        explicit_policy = {
            **self.policy,
            "mode": "full_agent",
            "approvalMode": "explicit",
        }
        self.gateway.thread_start(explicit_policy)
        with self.assertRaises(gateway_module.PolicyViolation) as caught:
            self.gateway.turn_start("thread-1", "Use a tool")
        self.assertEqual(caught.exception.code, "approval_broker_required")
        self.assertFalse(any(call[0] == "turn_start" for call in self.client.calls))

    def test_json_dispatch_supports_thread_and_turn_operations(self) -> None:
        started = gateway_module.process_json_request(
            {"operation": "thread_start", "policy": self.policy},
            self.gateway,
        )
        self.assertEqual(started["status"], "created")
        read = gateway_module.process_json_request(
            {"operation": "thread_read", "threadId": "thread-1", "includeTurns": True},
            self.gateway,
        )
        self.assertEqual(read["thread"]["id"], "thread-1")
        self.assertIn("assistantText", read["thread"]["turns"][0])

    def test_jsonl_keeps_one_client_for_async_start_wait_and_interrupt_surface(self) -> None:
        requests = [
            {"operation": "thread_start", "policy": self.policy},
            {
                "operation": "turn_start",
                "threadId": "thread-1",
                "prompt": "Run bounded work",
                "wait": False,
            },
            {
                "operation": "turn_wait",
                "threadId": "thread-1",
                "turnId": "turn-1",
            },
        ]
        source = io.StringIO(
            "".join(json.dumps(item) + "\n" for item in requests)
        )
        destination = io.StringIO()

        exit_code = gateway_module.serve_json_lines(
            source,
            destination,
            self.gateway,
        )

        self.assertEqual(exit_code, 0)
        responses = [json.loads(line) for line in destination.getvalue().splitlines()]
        self.assertEqual([item["status"] for item in responses], ["created", "running", "completed"])
        self.assertEqual(
            [call[0] for call in self.client.calls].count("initialize"),
            1,
        )
        self.assertIn("Finished safely", responses[-1]["turn"]["assistantText"])

    def test_jsonl_unicode_response_round_trips_through_cp1252_stdout(self) -> None:
        message = "พร้อมใช้งาน 🚫"
        source = io.BytesIO(
            (
                json.dumps(
                    {"operation": "status", "label": message},
                    ensure_ascii=False,
                )
                + "\n"
            ).encode("utf-8")
        )
        raw_destination = io.BytesIO()
        destination = io.TextIOWrapper(
            raw_destination,
            encoding="cp1252",
            errors="strict",
            write_through=True,
        )

        with mock.patch.object(
            gateway_module,
            "process_json_request",
            return_value={"ok": True, "status": "ready", "message": message},
        ) as process_request:
            exit_code = gateway_module.serve_json_lines(
                source,
                destination,
                self.gateway,
            )

        self.assertEqual(exit_code, 0)
        wire = raw_destination.getvalue().decode("ascii")
        self.assertIn("\\u", wire)
        self.assertEqual(json.loads(wire)["message"], message)
        self.assertEqual(process_request.call_args.args[0]["label"], message)

    def test_close_stops_client_and_process_state(self) -> None:
        self.gateway.status()
        self.gateway.close()
        self.assertTrue(self.client.closed)
        self.assertEqual(
            self.gateway.process_state.status,
            gateway_module.ProcessStatus.STOPPED,
        )


if __name__ == "__main__":
    unittest.main()
