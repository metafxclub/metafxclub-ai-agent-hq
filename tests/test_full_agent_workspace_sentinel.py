from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify-full-agent-workspace-sentinel.py"
BRIDGE = ROOT / "backend" / "local-runner" / "bridge_server.py"
SPEC = importlib.util.spec_from_file_location("full_agent_workspace_sentinel", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
sentinel = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sentinel
SPEC.loader.exec_module(sentinel)


class FakeGateway:
    def __init__(self, cwd: Path, controller, *, behavior: str = "valid") -> None:
        self.cwd = cwd
        self.controller = controller
        self.behavior = behavior
        self.thread_counter = 0
        self.decision_event = threading.Event()
        self.decision = None
        controller.set_resolver(self.resolve)

    def resolve(self, _request, decision: str) -> bool:
        self.decision = decision
        self.decision_event.set()
        return True

    def status(self):
        return {
            "ok": True,
            "status": "ready",
            "approvalBrokerReady": True,
            "deferredServerRequestsSupported": True,
            "approvalReplayDurable": True,
        }

    def models(self):
        return {
            "ok": True,
            "models": [
                {
                    "id": "test-model",
                    "model": "test-model",
                    "supportedReasoningEfforts": ["medium"],
                }
            ],
        }

    def thread_start(self, policy):
        self.thread_counter += 1
        return {"thread": {"id": f"thread-sentinel-{self.thread_counter}"}, "policy": policy}

    def turn_start(self, thread_id, _prompt, *, policy_value, wait):
        case_dir = Path(policy_value["workspaceRoots"][0])
        target = case_dir / sentinel.SENTINEL_FILE_NAME
        if self.behavior == "preapproval_mutation" and case_dir.name == "accept":
            target.write_bytes(sentinel.SENTINEL_BYTES)
        if self.behavior != "no_approval":
            request = {
                "requestId": f"request-{thread_id}",
                "requestDigest": "a" * 64,
                "decisionNonce": "nonce",
                "method": "item/fileChange/requestApproval",
                "actionType": "file_change",
                "threadId": thread_id,
                "turnId": f"turn-{thread_id}",
                "itemId": f"item-{thread_id}",
            }
            self.decision = None
            self.decision_event.clear()
            self.controller.on_pending(request)
            self.decision_event.wait(2)
        if self.decision == "accept_once":
            target.write_bytes(
                b"WRONG\n" if self.behavior == "wrong_bytes" else sentinel.SENTINEL_BYTES
            )
            if self.behavior == "extra_file":
                (case_dir / "unexpected.txt").write_text("extra", encoding="utf-8")
        return {
            "ok": self.decision == "accept_once",
            "status": "completed" if self.decision == "accept_once" else "failed",
            "wait": wait,
        }

    def close(self):
        return None


class WorkspaceSentinelTests(unittest.TestCase):
    def run_with_behavior(self, behavior: str):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            created = []

            def factory(cwd, controller):
                created.append(cwd)
                return FakeGateway(cwd, controller, behavior=behavior)

            report = sentinel.run_workspace_sentinel(
                workspace,
                live=True,
                gateway_factory=factory,
            )
            remaining = list(workspace.iterdir())
            serialized = json.dumps(report, sort_keys=True)
            return report, remaining, serialized, str(workspace), created

    def test_default_is_inert_without_live_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            called = False

            def forbidden_factory(_cwd, _controller):
                nonlocal called
                called = True
                raise AssertionError("gateway must not start")

            report = sentinel.run_workspace_sentinel(
                workspace,
                gateway_factory=forbidden_factory,
            )
            self.assertFalse(called)
            self.assertEqual(report["status"], "not_run")
            self.assertEqual(report["reasonCode"], "live_flag_required")
            self.assertEqual(list(workspace.iterdir()), [])

    def test_decline_and_accept_once_happy_path(self):
        report, remaining, serialized, workspace, _created = self.run_with_behavior("valid")
        self.assertTrue(report["ok"])
        self.assertEqual(report["reasonCode"], "verified")
        self.assertEqual([item["name"] for item in report["checks"]], ["decline", "accept_once"])
        self.assertTrue(all(item["approvalRequested"] for item in report["checks"]))
        self.assertTrue(all(not item["preApprovalMutation"] for item in report["checks"]))
        self.assertTrue(report["checks"][0]["filesystemVerified"])
        self.assertTrue(report["checks"][1]["exactBytesVerified"])
        self.assertEqual(remaining, [])
        self.assertNotIn(workspace, serialized)
        self.assertEqual(
            {tuple(item) for row in report["approvalMetadata"] for item in [row["keys"]]},
            {(
                "actionType",
                "decisionNonce",
                "itemId",
                "method",
                "requestDigest",
                "requestId",
                "threadId",
                "turnId",
            )},
        )

    def test_no_approval_request_fails_closed(self):
        report, remaining, serialized, workspace, _created = self.run_with_behavior("no_approval")
        self.assertFalse(report["ok"])
        self.assertEqual(report["reasonCode"], "workspace_sentinel_check_failed")
        self.assertTrue(all(not item["approvalRequested"] for item in report["checks"]))
        self.assertEqual(remaining, [])
        self.assertNotIn(workspace, serialized)
        self.assertNotIn("decisionNonce", serialized)

    def test_failed_attestation_cannot_enable_production_workspace_gate(self):
        source = BRIDGE.read_text(encoding="utf-8")
        self.assertIn('FULL_AGENT_EXECUTABLE_MODES = frozenset({"chat"})', source)
        self.assertIn("FULL_AGENT_INTERACTIVE_APPROVAL_BROKER_ENABLED = False", source)
        self.assertNotIn("bridge_server.py", SCRIPT.read_text(encoding="utf-8"))

    def test_preapproval_mutation_fails_closed(self):
        report, remaining, _serialized, _workspace, _created = self.run_with_behavior("preapproval_mutation")
        self.assertFalse(report["ok"])
        accept = next(item for item in report["checks"] if item["name"] == "accept_once")
        self.assertTrue(accept["preApprovalMutation"])
        self.assertFalse(accept["ok"])
        self.assertEqual(remaining, [])

    def test_wrong_bytes_and_extra_file_fail_closed(self):
        for behavior in ("wrong_bytes", "extra_file"):
            with self.subTest(behavior=behavior):
                report, remaining, _serialized, _workspace, _created = self.run_with_behavior(behavior)
                self.assertFalse(report["ok"])
                accept = next(item for item in report["checks"] if item["name"] == "accept_once")
                self.assertFalse(accept["ok"])
                self.assertEqual(remaining, [])

    def test_unready_interactive_transport_fails_before_turns(self):
        class UnreadyGateway(FakeGateway):
            def status(self):
                value = dict(super().status())
                value["approvalBrokerReady"] = False
                value["deferredServerRequestsSupported"] = False
                return value

            def thread_start(self, _policy):
                raise AssertionError("turn must not start")

        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            report = sentinel.run_workspace_sentinel(
                workspace,
                live=True,
                gateway_factory=lambda cwd, controller: UnreadyGateway(cwd, controller),
            )
            self.assertFalse(report["ok"])
            self.assertEqual(report["reasonCode"], "interactive_approval_transport_unavailable")
            self.assertEqual(
                [(item["name"], item["attempted"]) for item in report["checks"]],
                [("decline", False), ("accept_once", False)],
            )
            self.assertEqual(list(workspace.iterdir()), [])

    def test_cleanup_never_follows_link_outside_verified_run_root(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            outside = workspace / "outside.txt"
            outside.write_text("must survive", encoding="utf-8")
            run_root = workspace / f"{sentinel.RUN_PREFIX}link-test"
            run_root.mkdir()
            link = run_root / "outside-link.txt"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"symlinks unavailable: {error.__class__.__name__}")
            self.assertEqual(sentinel._entry_snapshot(run_root), [("outside-link.txt", "link")])
            self.assertTrue(sentinel._cleanup_inside_workspace(run_root, workspace))
            self.assertTrue(outside.is_file())
            self.assertEqual(outside.read_text(encoding="utf-8"), "must survive")


if __name__ == "__main__":
    unittest.main()
