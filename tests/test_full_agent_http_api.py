from __future__ import annotations

import base64
import contextlib
import http.client
import importlib.util
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeGateway:
    """Loopback-test double; it never launches Codex or opens the network."""

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
        self.reply_text: str | None = None

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
                    "supportedReasoningEfforts": ["low", "medium", "high"],
                    "inputModalities": ["text", "image"],
                },
                {
                    "model": "gpt-6-astra",
                    "displayName": "GPT-6 Astra",
                    "isDefault": False,
                    "supportedReasoningEfforts": ["medium", "high", "xhigh"],
                    "inputModalities": ["text", "image"],
                },
                {
                    "model": "not-allowlisted",
                    "displayName": "Must not reach the browser",
                    "isDefault": False,
                    "supportedReasoningEfforts": ["medium"],
                },
            ],
        }

    def thread_start(self, policy_value: dict) -> dict:
        with self._lock:
            self._thread_counter += 1
            thread_id = f"fake-thread-{self._thread_counter:04d}"
        self._record("thread_start", policy=dict(policy_value), threadId=thread_id)
        return {"ok": True, "thread": {"id": thread_id}}

    def thread_resume(self, thread_id: str, policy_value: dict) -> dict:
        self._record("thread_resume", threadId=thread_id, policy=dict(policy_value))
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
            turn_id = f"fake-turn-{self._turn_counter:04d}"
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
        turn = self._turns[turn_id]
        mode = str((turn.get("policy") or {}).get("mode") or "chat")
        return {
            "ok": True,
            "status": "completed",
            "turn": {
                "id": turn_id,
                "status": "completed",
                "assistantText": self.reply_text or f"persisted fake {mode} reply",
                "items": (
                    [{"type": "commandExecution", "status": "completed"}]
                    if mode == "workspace"
                    else []
                ),
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


class FullAgentHttpApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge("metafx_full_agent_http_api_tests")

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.runtime_dir = self.root / "runtime"
        self.gateway = FakeGateway()
        self.stack = contextlib.ExitStack()
        for name, value in {
            "RUNTIME_DIR": self.runtime_dir,
            "MISSIONS_PATH": self.runtime_dir / "missions.json",
            "AUDIT_PATH": self.runtime_dir / "bridge-audit.jsonl",
            "RUNTIME_REPORTS_DIR": self.runtime_dir / "reports",
            "FULL_AGENT_RUNTIME_DIR": self.runtime_dir / "full-agent-runtime",
            "FULL_AGENT_ARTIFACTS_DIR": self.runtime_dir / "full-agent-media",
        }.items():
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
            mock.patch.object(
                self.bridge, "FULL_AGENT_GATEWAY_INSTANCE", self.gateway
            )
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

        bridge_handler = self.bridge.BridgeHandler

        class QuietBridgeHandler(bridge_handler):
            def log_message(self, _format: str, *args: object) -> None:
                del args

        class JoinableBridgeHTTPServer(self.bridge.BridgeHTTPServer):
            daemon_threads = False
            block_on_close = True

        self.server = JoinableBridgeHTTPServer(
            ("127.0.0.1", 0),
            QuietBridgeHandler,
        )
        self.server_thread = threading.Thread(
            target=self.server.serve_forever,
            name="full-agent-http-test-server",
            daemon=True,
        )
        self.server_thread.start()
        self.origin = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.gateway.wait_gate.set()
        self._wait_for(
            lambda: not self.bridge.FULL_AGENT_ACTIVE_TURNS,
            timeout=3,
            fail=False,
        )
        self.server.shutdown()
        self.server_thread.join(timeout=5)
        self.server.server_close()
        server_stopped = not self.server_thread.is_alive()
        self.stack.close()
        self.temp.cleanup()
        self.assertTrue(server_stopped, "Full Agent HTTP test server did not stop")

    def _wait_for(
        self,
        predicate,
        *,
        timeout: float = 5,
        fail: bool = True,
    ) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return True
            time.sleep(0.01)
        if fail:
            self.fail("Timed out waiting for Full Agent HTTP state")
        return False

    def request(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
        *,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], dict]:
        body = None
        request_headers = dict(headers or {})
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
            request_headers["Content-Length"] = str(len(body))
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            int(self.server.server_port),
            timeout=5,
        )
        try:
            connection.request(method, path, body=body, headers=request_headers)
            response = connection.getresponse()
            raw = response.read()
            status = int(response.status)
            response_headers = {key.lower(): value for key, value in response.getheaders()}
        finally:
            connection.close()
        decoded = json.loads(raw.decode("utf-8")) if raw else {}
        return status, response_headers, decoded

    def request_bytes(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            int(self.server.server_port),
            timeout=5,
        )
        try:
            connection.request(method, path, headers=dict(headers or {}))
            response = connection.getresponse()
            raw = response.read()
            status = int(response.status)
            response_headers = {
                key.lower(): value for key, value in response.getheaders()
            }
        finally:
            connection.close()
        return status, response_headers, raw

    def create_thread(
        self,
        *,
        agent_id: str = "manager",
        mode: str = "chat",
    ) -> dict:
        status, _headers, body = self.request(
            "POST",
            "/api/agent-runtime/threads",
            {
                "agentId": agent_id,
                "title": f"HTTP {mode} integration",
                "model": "gpt-6-sol",
                "reasoning": "medium",
                "mode": mode,
            },
            headers={"Origin": self.origin},
        )
        self.assertEqual(status, 201, body)
        self.assertTrue(body["ok"])
        return body["thread"]

    def poll_thread_until_idle(self, thread_id: str) -> dict:
        latest: dict = {}

        def finished() -> bool:
            nonlocal latest
            status, _headers, body = self.request(
                "GET",
                f"/api/agent-runtime/threads/{thread_id}",
                headers={"Origin": self.origin},
            )
            self.assertEqual(status, 200, body)
            latest = body["thread"]
            return latest.get("activeTurn") is None

        self._wait_for(finished)
        return latest

    def test_status_models_and_loopback_origin_security_headers(self) -> None:
        status, headers, body = self.request(
            "GET",
            "/api/agent-runtime/status",
            headers={"Origin": self.origin},
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertTrue(body["runtime"]["executionEnabled"])
        self.assertEqual(body["runtime"]["responseStringLimitChars"], 32768)
        self.assertEqual(headers["x-metafx-response-string-limit"], "32768")
        self.assertEqual(headers["cache-control"], "no-store")
        self.assertEqual(
            headers["x-bridge-policy"], "local-runner-no-frontend-secrets"
        )
        self.assertEqual(headers["x-content-type-options"], "nosniff")
        self.assertEqual(headers["x-frame-options"], "DENY")
        self.assertEqual(headers["referrer-policy"], "no-referrer")
        self.assertEqual(headers["cross-origin-resource-policy"], "same-origin")
        self.assertIn("connect-src 'self'", headers["content-security-policy"])

        model_status, _headers, models = self.request(
            "GET",
            "/api/agent-runtime/models",
            headers={"Origin": self.origin},
        )
        self.assertEqual(model_status, 200)
        self.assertEqual(
            [row["id"] for row in models["models"]],
            ["gpt-6-sol", "gpt-6-astra"],
        )
        self.assertNotIn("not-allowlisted", json.dumps(models))

        rejected_status, rejected_headers, rejected = self.request(
            "GET",
            "/api/agent-runtime/status",
            headers={"Origin": "https://attacker.invalid"},
        )
        self.assertEqual(rejected_status, 403)
        self.assertFalse(rejected["ok"])
        self.assertIn("Cross-origin requests", rejected["error"])
        self.assertEqual(rejected_headers["x-frame-options"], "DENY")

        cross_site_status, _headers, cross_site = self.request(
            "GET",
            "/api/agent-runtime/status",
            headers={"Sec-Fetch-Site": "cross-site"},
        )
        self.assertEqual(cross_site_status, 403)
        self.assertFalse(cross_site["ok"])
        self.assertIn("Cross-site requests", cross_site["error"])

    def test_full_agent_mutations_require_exact_hq_origin_and_json(self) -> None:
        payload = {
            "agentId": "manager",
            "title": "transport guard",
            "model": "gpt-6-sol",
            "reasoning": "medium",
            "mode": "chat",
        }
        missing_origin_status, _headers, missing_origin = self.request(
            "POST",
            "/api/agent-runtime/threads",
            payload,
        )
        self.assertEqual(missing_origin_status, 403, missing_origin)
        self.assertEqual(missing_origin.get("code"), "same_origin_required")

        alias_origin_status, _headers, alias_origin = self.request(
            "POST",
            "/api/agent-runtime/threads",
            payload,
            headers={"Origin": f"http://localhost:{self.server.server_port}"},
        )
        self.assertEqual(alias_origin_status, 403, alias_origin)
        self.assertEqual(alias_origin.get("code"), "same_origin_required")

        wrong_media_status, _headers, wrong_media = self.request(
            "POST",
            "/api/agent-runtime/threads",
            payload,
            headers={
                "Origin": self.origin,
                "Content-Type": "text/plain",
            },
        )
        self.assertEqual(wrong_media_status, 415, wrong_media)
        self.assertEqual(wrong_media.get("code"), "invalid_transport")

    def test_dormant_approval_routes_are_no_store_and_decision_is_csrf_bound(self) -> None:
        thread = self.create_thread(agent_id="manager", mode="chat")
        thread_id = thread["id"]
        pending_status, pending_headers, pending = self.request(
            "GET",
            f"/api/agent-runtime/threads/{thread_id}/approvals/pending",
            headers={"Origin": self.origin},
        )
        self.assertEqual(pending_status, 200, pending)
        self.assertEqual(pending_headers.get("cache-control"), "no-store")
        self.assertEqual(pending.get("status"), "ready")
        self.assertIsNone(pending.get("approval"))

        nonce = "b" * 32
        request_id = "request-http-approval-1"
        payload = {
            "threadId": thread_id,
            "turnId": "turn-http-approval-1",
            "missionId": "mission-http-approval-1",
            "gatewayThreadId": "gateway-thread-http-1",
            "gatewayTurnId": "gateway-turn-http-1",
            "gatewayGeneration": "fgw-http-approval-1",
            "itemId": "item-http-approval-1",
            "requestDigest": "a" * 64,
            "decisionNonce": nonce,
            "decision": "decline",
            "idempotencyKey": "approval-http-decision-1",
        }
        path = (
            f"/api/agent-runtime/threads/{thread_id}/approvals/"
            f"{request_id}/resolve"
        )
        rejected_status, rejected_headers, rejected = self.request(
            "POST",
            path,
            payload,
            headers={
                "Origin": self.origin,
                "Sec-Fetch-Site": "same-origin",
                # Deliberately omit Sec-Fetch-Mode.
                "X-Metafx-Approval-Version": "1",
                "X-Metafx-Approval-Nonce": nonce,
            },
        )
        self.assertEqual(rejected_status, 403, rejected)
        self.assertEqual(rejected_headers.get("cache-control"), "no-store")

        wrong_origin_status, _headers, wrong_origin = self.request(
            "POST",
            path,
            payload,
            headers={
                "Origin": f"http://localhost:{self.server.server_port}",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "X-Metafx-Approval-Version": "1",
                "X-Metafx-Approval-Nonce": nonce,
            },
        )
        self.assertEqual(wrong_origin_status, 403, wrong_origin)

        dormant_status, dormant_headers, dormant = self.request(
            "POST",
            path,
            payload,
            headers={
                "Origin": self.origin,
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "X-Metafx-Approval-Version": "1",
                "X-Metafx-Approval-Nonce": nonce,
            },
        )
        self.assertEqual(dormant_status, 409, dormant)
        self.assertEqual(dormant_headers.get("cache-control"), "no-store")
        self.assertEqual(dormant.get("code"), "approval_broker_required")

    def test_http_response_redacts_local_paths_without_corrupting_links(self) -> None:
        safe_url = "https://docs.example.com/setup/path"
        safe_api = "/api/agent-runtime/threads/fat_demo/artifacts/art_demo"
        self.gateway.reply_text = (
            "C:/Users/META/private.txt | //server/share/private.txt | "
            "file:///tmp/private.txt | /mnt/c/Users/META/private.txt | "
            f"/opt/metafx/private.txt | {safe_url} | {safe_api}"
        )
        thread = self.create_thread(agent_id="manager", mode="chat")
        status, _headers, queued = self.request(
            "POST",
            f"/api/agent-runtime/threads/{thread['id']}/turn",
            {
                "message": "Return the response-path fixture.",
                "idempotencyKey": "http-path-redaction-0001",
            },
            headers={"Origin": self.origin},
        )
        self.assertEqual(status, 202, queued)
        finished = self.poll_thread_until_idle(thread["id"])
        reply = [
            event for event in finished["events"] if event.get("role") == "assistant"
        ][-1]["content"]
        self.assertGreaterEqual(reply.count("[REDACTED_PATH]"), 5)
        self.assertNotIn("C:/Users/META/private.txt", reply)
        self.assertNotIn("//server/share/private.txt", reply)
        self.assertNotIn("file:///tmp/private.txt", reply)
        self.assertNotIn("/mnt/c/Users/META/private.txt", reply)
        self.assertNotIn("/opt/metafx/private.txt", reply)
        self.assertIn(safe_url, reply)
        self.assertIn(safe_api, reply)

    def test_http_thread_history_preserves_valid_reply_above_generic_limit(self) -> None:
        reply = "BEGIN|" + ("x" * 24990) + "|END"
        self.gateway.reply_text = reply
        thread = self.create_thread(agent_id="manager", mode="chat")
        status, _headers, queued = self.request(
            "POST",
            f"/api/agent-runtime/threads/{thread['id']}/turn",
            {
                "message": "Return the bounded long-response fixture.",
                "idempotencyKey": "http-long-response-0001",
            },
            headers={"Origin": self.origin},
        )
        self.assertEqual(status, 202, queued)
        self.poll_thread_until_idle(thread["id"])

        detail_status, detail_headers, detail = self.request(
            "GET",
            f"/api/agent-runtime/threads/{thread['id']}",
            headers={"Origin": self.origin},
        )
        self.assertEqual(detail_status, 200, detail)
        self.assertEqual(detail_headers["x-metafx-response-string-limit"], "32768")
        assistant_events = [
            event
            for event in detail["thread"]["events"]
            if event.get("role") == "assistant"
        ]
        self.assertEqual(assistant_events[-1]["content"], reply)
        self.assertTrue(assistant_events[-1]["content"].endswith("|END"))

    def test_http_thread_lifecycle_persists_async_assistant_result(self) -> None:
        thread = self.create_thread()
        thread_id = thread["id"]

        list_status, _headers, listed = self.request(
            "GET",
            "/api/agent-runtime/threads?agentId=manager&includeArchived=false",
            headers={"Origin": self.origin},
        )
        self.assertEqual(list_status, 200)
        self.assertEqual([row["id"] for row in listed["threads"]], [thread_id])

        detail_status, _headers, detail = self.request(
            "GET",
            f"/api/agent-runtime/threads/{thread_id}",
            headers={"Origin": self.origin},
        )
        self.assertEqual(detail_status, 200)
        self.assertEqual(detail["thread"]["eventCount"], 0)

        settings_status, _headers, settings = self.request(
            "POST",
            f"/api/agent-runtime/threads/{thread_id}/settings",
            {
                "model": "gpt-6-astra",
                "reasoning": "high",
                "mode": "chat",
                "expectedRevision": thread["revision"],
            },
            headers={"Origin": self.origin},
        )
        self.assertEqual(settings_status, 200)
        self.assertEqual(settings["thread"]["model"], "gpt-6-astra")
        self.assertEqual(settings["thread"]["reasoning"], "high")

        turn_status, _headers, queued = self.request(
            "POST",
            f"/api/agent-runtime/threads/{thread_id}/turn",
            {
                "message": "Return one bounded HTTP integration reply.",
                "idempotencyKey": "http-turn-0001",
            },
            headers={"Origin": self.origin},
        )
        self.assertEqual(turn_status, 202)
        self.assertEqual(queued["status"], "queued")
        finished = self.poll_thread_until_idle(thread_id)
        self.assertEqual(finished["turnCount"], 1)
        assistant_events = [
            event for event in finished["events"] if event.get("role") == "assistant"
        ]
        self.assertEqual(len(assistant_events), 1)
        self.assertEqual(
            assistant_events[0]["content"], "persisted fake chat reply"
        )
        self.assertTrue(self.gateway.calls_for("turn_start"))
        self.assertTrue(self.gateway.calls_for("turn_wait"))

        archive_status, _headers, archived = self.request(
            "POST",
            f"/api/agent-runtime/threads/{thread_id}/archive",
            {"archived": True, "expectedRevision": finished["revision"]},
            headers={"Origin": self.origin},
        )
        self.assertEqual(archive_status, 200)
        self.assertTrue(archived["thread"]["archived"])

        _status, _headers, visible = self.request(
            "GET",
            "/api/agent-runtime/threads?agentId=manager&includeArchived=false",
            headers={"Origin": self.origin},
        )
        self.assertEqual(visible["threads"], [])
        _status, _headers, all_threads = self.request(
            "GET",
            "/api/agent-runtime/threads?agentId=manager&includeArchived=true",
            headers={"Origin": self.origin},
        )
        self.assertEqual([row["id"] for row in all_threads["threads"]], [thread_id])

        unarchive_status, _headers, unarchived = self.request(
            "POST",
            f"/api/agent-runtime/threads/{thread_id}/archive",
            {
                "archived": False,
                "expectedRevision": archived["thread"]["revision"],
            },
            headers={"Origin": self.origin},
        )
        self.assertEqual(unarchive_status, 200)
        self.assertFalse(unarchived["thread"]["archived"])
        _status, _headers, restored = self.request(
            "GET",
            "/api/agent-runtime/threads?agentId=manager&includeArchived=false",
            headers={"Origin": self.origin},
        )
        self.assertEqual([row["id"] for row in restored["threads"]], [thread_id])

    def test_png_attachment_upload_turn_and_download_are_thread_bound_and_path_opaque(
        self,
    ) -> None:
        png_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
            "AAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        thread = self.create_thread(agent_id="manager", mode="chat")
        thread_id = thread["id"]

        upload_status, _upload_headers, uploaded = self.request(
            "POST",
            f"/api/agent-runtime/threads/{thread_id}/attachments",
            {
                "fileName": "chart.png",
                "mediaType": "image/png",
                "dataBase64": base64.b64encode(png_bytes).decode("ascii"),
            },
            headers={"Origin": self.origin},
        )
        self.assertEqual(upload_status, 201, uploaded)
        attachment = uploaded["attachment"]
        attachment_id = attachment["id"]
        self.assertEqual(attachment["kind"], "image")
        self.assertEqual(attachment["mediaType"], "image/png")
        self.assertNotIn("path", attachment)
        self.assertNotIn(str(self.root), json.dumps(uploaded))
        self.assertEqual(
            attachment["downloadUrl"],
            f"/api/agent-runtime/threads/{thread_id}/artifacts/{attachment_id}",
        )
        self.assertEqual(attachment["previewUrl"], attachment["downloadUrl"])

        draft = self.bridge._full_agent_artifact_private_binding(attachment_id)
        self.assertEqual(draft["threadId"], thread_id)
        self.assertTrue(draft["turnId"].startswith("turn_upload_"))

        download_status, download_headers, downloaded = self.request_bytes(
            "GET",
            attachment["downloadUrl"],
            headers={"Origin": self.origin},
        )
        self.assertEqual(download_status, 200)
        self.assertEqual(downloaded, png_bytes)
        self.assertEqual(download_headers["content-type"], "image/png")
        self.assertEqual(download_headers["x-content-type-options"], "nosniff")

        foreign_thread = self.create_thread(agent_id="manager", mode="chat")
        foreign_status, _foreign_headers, foreign = self.request(
            "GET",
            (
                f"/api/agent-runtime/threads/{foreign_thread['id']}"
                f"/artifacts/{attachment_id}"
            ),
            headers={"Origin": self.origin},
        )
        self.assertEqual(foreign_status, 404, foreign)
        self.assertFalse(foreign["ok"])

        turn_status, _turn_headers, queued = self.request(
            "POST",
            f"/api/agent-runtime/threads/{thread_id}/turn",
            {
                "message": "Describe this chart without using tools.",
                "idempotencyKey": "http-image-turn-0001",
                "attachmentIds": [attachment_id],
            },
            headers={"Origin": self.origin},
        )
        self.assertEqual(turn_status, 202, queued)
        self.assertNotIn(str(self.root), json.dumps(queued))
        finished = self.poll_thread_until_idle(thread_id)
        self.assertNotIn(str(self.root), json.dumps(finished))

        turn_calls = self.gateway.calls_for("turn_start")
        self.assertEqual(len(turn_calls), 1)
        input_items = turn_calls[0]["inputItems"]
        self.assertEqual(len(input_items), 1)
        self.assertEqual(input_items[0]["type"], "localImage")
        internal_path = Path(input_items[0]["path"])
        self.assertTrue(internal_path.is_relative_to(self.runtime_dir / "full-agent-media"))
        self.assertEqual(internal_path.read_bytes(), png_bytes)
        bound_attachment_id = internal_path.stem
        bound = self.bridge._full_agent_artifact_private_binding(bound_attachment_id)
        self.assertEqual(bound["threadId"], thread_id)
        self.assertEqual(bound["turnId"], queued["turn"]["id"])
        self.assertNotEqual(draft["turnId"], bound["turnId"])
        with self.assertRaises(self.bridge.FullAgentArtifactError):
            self.bridge._full_agent_artifact_store().resolve(
                thread_id,
                queued["turn"]["id"],
                attachment_id,
            )
        with self.assertRaises(self.bridge.FullAgentArtifactError):
            self.bridge._full_agent_artifact_private_binding(attachment_id)
        consumed_status, _consumed_headers, consumed = self.request(
            "GET",
            attachment["downloadUrl"],
            headers={"Origin": self.origin},
        )
        self.assertEqual(consumed_status, 404, consumed)
        self.assertFalse(consumed["ok"])

        audit_rows = [
            json.loads(line)
            for line in self.bridge.AUDIT_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        rebound_rows = [
            row
            for row in audit_rows
            if row.get("type") == "full_agent.attachment_bound"
            and row.get("turnId") == queued["turn"]["id"]
        ]
        self.assertEqual(len(rebound_rows), 1)
        self.assertEqual(rebound_rows[0]["attachmentId"], bound_attachment_id)
        self.assertEqual(rebound_rows[0]["sourceAttachmentId"], attachment_id)
        self.assertTrue(rebound_rows[0]["sourceConsumedAt"])
        aggregate_rows = [
            row
            for row in audit_rows
            if row.get("type") == "full_agent.turn_attachments_bound"
            and row.get("turnId") == queued["turn"]["id"]
        ]
        self.assertEqual(len(aggregate_rows), 1)
        self.assertEqual(aggregate_rows[0]["attachmentIds"], [bound_attachment_id])
        self.assertNotIn(attachment_id, aggregate_rows[0]["attachmentIds"])
        queued_rows = [
            row
            for row in audit_rows
            if row.get("type") == "full_agent.turn_queued"
            and row.get("turnId") == queued["turn"]["id"]
        ]
        self.assertEqual(len(queued_rows), 1)
        self.assertEqual(queued_rows[0]["attachmentIds"], [bound_attachment_id])
        self.assertNotIn(attachment_id, queued_rows[0]["attachmentIds"])

        user_events = [
            event
            for event in finished["events"]
            if event.get("role") == "user"
            and (event.get("metadata") or {}).get("turnId") == queued["turn"]["id"]
        ]
        self.assertEqual(len(user_events), 1)
        persisted_ids = [
            item.get("id")
            for item in (user_events[0].get("metadata") or {}).get("attachments", [])
        ]
        self.assertEqual(persisted_ids, [bound_attachment_id])
        self.assertNotIn(attachment_id, persisted_ids)

        audit_json = json.dumps(rebound_rows + aggregate_rows + queued_rows)
        self.assertNotIn(str(self.root), audit_json)
        self.assertNotIn("sourcePath", audit_json)
        self.assertNotIn("localPath", audit_json)
        self.assertTrue(
            all(row.get("filesystemPathExposed") is False for row in rebound_rows + aggregate_rows)
        )
        self.assertNotIn(str(internal_path), json.dumps(queued))
        self.assertNotIn(str(internal_path), json.dumps(finished))

    def test_chat_turn_rejects_uploaded_non_image_before_gateway_dispatch(self) -> None:
        thread = self.create_thread(agent_id="manager", mode="chat")
        thread_id = thread["id"]
        upload_status, _headers, uploaded = self.request(
            "POST",
            f"/api/agent-runtime/threads/{thread_id}/attachments",
            {
                "fileName": "notes.txt",
                "mediaType": "text/plain",
                "dataBase64": base64.b64encode(b"bounded notes\n").decode("ascii"),
            },
            headers={"Origin": self.origin},
        )
        self.assertEqual(upload_status, 201, uploaded)

        turn_status, _turn_headers, rejected = self.request(
            "POST",
            f"/api/agent-runtime/threads/{thread_id}/turn",
            {
                "message": "Read the attached notes.",
                "idempotencyKey": "http-text-turn-0001",
                "attachmentIds": [uploaded["attachment"]["id"]],
            },
            headers={"Origin": self.origin},
        )
        self.assertEqual(turn_status, 409, rejected)
        self.assertEqual(rejected["code"], "attachment_requires_full_access")
        self.assertEqual(self.gateway.calls_for("turn_start"), [])

    def test_http_interrupt_reaches_fake_gateway_and_finishes_fail_closed(self) -> None:
        self.gateway.block_waits = True
        thread = self.create_thread(agent_id="manager", mode="chat")
        thread_id = thread["id"]
        turn_status, _headers, queued = self.request(
            "POST",
            f"/api/agent-runtime/threads/{thread_id}/turn",
            {
                "message": "Explain one bounded architecture detail.",
                "idempotencyKey": "http-interrupt-0001",
            },
            headers={"Origin": self.origin},
        )
        self.assertEqual(turn_status, 202)
        self.assertEqual(queued["status"], "queued")
        self.assertTrue(self.gateway.wait_entered.wait(3))

        interrupt_status, _headers, interrupted = self.request(
            "POST",
            f"/api/agent-runtime/threads/{thread_id}/interrupt",
            {},
            headers={"Origin": self.origin},
        )
        self.assertEqual(interrupt_status, 202)
        self.assertEqual(interrupted["status"], "interrupt_requested")
        self.assertTrue(interrupted["adapterConfirmed"])

        finished = self.poll_thread_until_idle(thread_id)
        self.assertEqual(finished["status"], "idle")
        self.assertIsNone(finished["activeTurn"])
        error_events = [
            event for event in finished["events"] if event.get("type") == "error"
        ]
        self.assertEqual(len(error_events), 1)
        self.assertEqual(error_events[0]["metadata"]["errorCode"], "turn_interrupted")
        self.assertEqual(len(self.gateway.calls_for("turn_interrupt")), 1)


if __name__ == "__main__":
    unittest.main()
