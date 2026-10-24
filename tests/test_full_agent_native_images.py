"""Native image delivery regressions; no processes, model calls or real paths."""
from __future__ import annotations

import base64
import json
import unittest
from pathlib import Path
from unittest import mock

import test_codex_app_server_gateway as gateway_tests
import test_full_agent_bridge_api as bridge_tests

gateway_module = gateway_tests.gateway_module


PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


class GeneratedImageProvenanceTests(unittest.TestCase):
    setUp = gateway_tests.SdkGatewayTests.setUp
    tearDown = gateway_tests.SdkGatewayTests.tearDown

    def finished(self, *, mode="workspace"):
        self.gateway.thread_start({**self.policy, "mode": mode})
        started = self.gateway.turn_start("thread-1", "Create image", wait=False)
        self.turn_id = started["turn"]["id"]
        self.image_path = str(Path(self.workspace) / "native-private.png")
        self.image_item = {"id": "image-1", "type": "imageGeneration", "status": "completed", "savedPath": self.image_path}
        self.raw_turn = {"id": self.turn_id, "status": "completed", "items": [self.image_item]}
        self.response = {"thread": {"id": "thread-1", "turns": [self.raw_turn]}}
        self.client.thread_read = mock.Mock(return_value=self.response)
        self.gateway.turn_wait(self.turn_id, thread_id="thread-1")

    def collect(self):
        staged = []
        count = self.gateway.collect_completed_image_outputs(
            "thread-1", self.turn_id, stage_image=lambda item, source: staged.append((item, source)),
        )
        return count, staged

    def test_only_exact_current_native_image_is_collected_and_paths_stay_private(self):
        self.finished()
        self.response["thread"]["turns"].insert(0, {
            "id": "older-turn", "status": "completed", "items": [{**self.image_item, "savedPath": "C:/older-private.png"}],
        })
        self.raw_turn["items"] += [
            {"id": "text", "type": "agentMessage", "text": "generated image", "savedPath": "C:/spoofed.png"},
            {"id": "view", "type": "imageView", "path": "C:/view-only.png"},
            {"id": "generic", "type": "fileOutput", "savedPath": "C:/generic.png"},
            {**self.image_item, "id": "failed-image", "status": "failed", "savedPath": "C:/failed.png"},
        ]
        self.assertEqual(self.collect(), (1, [("image-1", self.image_path)]))
        public = json.dumps(self.gateway.thread_read("thread-1"))
        self.assertNotIn(self.image_path, public)
        self.assertNotIn("older-private", public)
        self.assertNotIn("spoofed.png", public)

    def test_cross_thread_or_duplicate_turn_provenance_fails_before_staging(self):
        for mutation in ("foreign-thread", "duplicate-turn", "missing-turn", "not-completed"):
            with self.subTest(mutation=mutation):
                self.finished()
                if mutation == "foreign-thread":
                    self.response["thread"]["id"] = "thread-foreign"
                elif mutation == "duplicate-turn":
                    self.response["thread"]["turns"].append(dict(self.raw_turn))
                elif mutation == "missing-turn":
                    self.response["thread"]["turns"] = []
                else:
                    self.raw_turn["status"] = "inProgress"
                stage = mock.Mock()
                with self.assertRaises(gateway_module.PolicyViolation) as caught:
                    self.gateway.collect_completed_image_outputs("thread-1", self.turn_id, stage_image=stage)
                self.assertEqual(caught.exception.code, "image_provenance_mismatch")
                stage.assert_not_called()

    def test_old_turn_rejected_after_new_turn_started(self):
        self.finished()
        self.gateway.turn_start("thread-1", "Next task", wait=False)
        with self.assertRaises(gateway_module.PolicyViolation):
            self.collect()

    def test_completed_turn_rejected_after_resume_or_chat_mode(self):
        self.finished()
        self.gateway.thread_resume("thread-1", self.policy)
        with self.assertRaises(gateway_module.PolicyViolation):
            self.collect()
        self.finished(mode="chat")
        with self.assertRaises(gateway_module.PolicyViolation):
            self.collect()

    def test_wrong_turn_id_is_rejected_without_reading_history(self):
        self.finished()
        self.client.thread_read.reset_mock()
        with self.assertRaises(gateway_module.PolicyViolation):
            self.gateway.collect_completed_image_outputs("thread-1", "unrelated-turn", stage_image=mock.Mock())
        self.client.thread_read.assert_not_called()

    def test_closed_gateway_loses_completed_image_provenance(self):
        self.finished()
        self.gateway.close()
        self.client.thread_read.reset_mock()
        with self.assertRaises(gateway_module.PolicyViolation):
            self.collect()
        self.client.thread_read.assert_not_called()

    def test_incomplete_duplicate_and_excessive_image_evidence_stages_nothing(self):
        for mutation in ("missing-path", "duplicate-id", "failure", "limit"):
            with self.subTest(mutation=mutation):
                self.finished()
                if mutation == "missing-path":
                    self.image_item.pop("savedPath")
                elif mutation == "duplicate-id":
                    self.raw_turn["items"].append(dict(self.image_item))
                elif mutation == "failure":
                    self.image_item["failure"] = {"message": "failed"}
                else:
                    self.raw_turn["items"] = [{**self.image_item, "id": f"image-{i}"} for i in range(13)]
                stage = mock.Mock()
                with self.assertRaises(gateway_module.PolicyViolation):
                    self.gateway.collect_completed_image_outputs("thread-1", self.turn_id, stage_image=stage)
                stage.assert_not_called()

    def test_collector_is_not_an_externally_callable_json_operation(self):
        with self.assertRaises(gateway_module.GatewayError) as caught:
            gateway_module.process_json_request({"operation": "collect_completed_image_outputs"}, self.gateway)
        self.assertEqual(caught.exception.code, "unsupported_operation")


class NativeImageGateway(bridge_tests.FakeGateway):
    def __init__(self):
        super().__init__()
        self.native_images = []

    def turn_wait(self, turn_id, *, thread_id=None):
        result = super().turn_wait(turn_id, thread_id=thread_id)
        if result["status"] == "completed":
            result["turn"]["items"] += [{"id": item, "type": "imageGeneration", "status": "completed", "pathHidden": True} for item, _source in self.native_images]
            if self.reply_text == "":
                result["turn"]["assistantText"] = ""
        return result

    def collect_completed_image_outputs(self, thread_id, turn_id, *, stage_image):
        self._record("collect_completed_image_outputs", threadId=thread_id, turnId=turn_id)
        assert self._turns[turn_id]["threadId"] == thread_id
        for item, source in self.native_images:
            stage_image(item, source)
        return len(self.native_images)


class NativeImagePublicationTests(unittest.TestCase):
    setUpClass = classmethod(bridge_tests.FullAgentBridgeApiTests.setUpClass.__func__)
    tearDown = bridge_tests.FullAgentBridgeApiTests.tearDown
    _wait_for = bridge_tests.FullAgentBridgeApiTests._wait_for
    _create_thread = bridge_tests.FullAgentBridgeApiTests._create_thread
    _request_and_wait = bridge_tests.FullAgentBridgeApiTests._request_and_wait
    _audit_rows = bridge_tests.FullAgentBridgeApiTests._audit_rows

    def setUp(self):
        bridge_tests.FullAgentBridgeApiTests.setUp(self)
        self.gateway = NativeImageGateway()
        self.gateway.workspace_root = self.workspace_dir
        self.stack.enter_context(mock.patch.object(self.bridge, "FULL_AGENT_GATEWAY_INSTANCE", self.gateway))
        self.source = self.root / "native-private-output.png"
        self.source.write_bytes(PNG_BYTES)
        self.gateway.native_images = [("native-image-1", str(self.source))]

    def run_native(self, key="native-image-output-0001"):
        thread = self._create_thread(mode="full")
        queued, finished = self._request_and_wait(thread["id"], message="Create an image", key=key)
        return thread, queued, finished

    def test_native_image_only_turn_publishes_usable_immutable_output_and_replay(self):
        self.gateway.reply_text = ""
        thread, queued, finished = self.run_native()
        self.assertIsNone(finished["activeTurn"])
        assistant = [event for event in finished["events"] if event.get("role") == "assistant"][-1]
        artifacts = assistant["metadata"]["artifacts"]
        self.assertEqual(len(artifacts), 1)
        artifact = artifacts[0]
        self.assertEqual(artifact["mediaType"], "image/png")
        self.assertEqual(artifact["kind"], "image")
        self.assertTrue(artifact["name"].startswith("generated-image-"))
        self.assertEqual(self.bridge.full_agent_resolve_artifact(thread["id"], artifact["id"])[0].read_bytes(), PNG_BYTES)
        self.assertTrue(self.source.exists())
        public_and_audit = json.dumps([finished, self._audit_rows()])
        self.assertNotIn(str(self.source), public_and_audit)
        self.assertNotIn(self.source.name, public_and_audit)
        replay = self.bridge.full_agent_request_turn(thread["id"], {"message": "Create an image", "idempotencyKey": "native-image-output-0001"})
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["status"], "completed")
        self.assertEqual(replay["artifacts"], artifacts)
        self.assertEqual(len(self.gateway.calls_for("collect_completed_image_outputs")), 1)
        self.assertEqual(len(self.gateway.calls_for("turn_start")), 1)
        self.assertTrue(any(row.get("type") == "full_agent.native_images_staged" for row in self._audit_rows()))

    def test_invalid_image_batch_publishes_nothing_and_never_leaks_path(self):
        fake = self.root / "private-fake.png"
        fake.write_bytes(b"not an image")
        self.gateway.native_images.append(("invalid-image", str(fake)))
        thread, _queued, finished = self.run_native()
        replay = self.bridge.full_agent_request_turn(thread["id"], {"message": "Create an image", "idempotencyKey": "native-image-output-0001"})
        self.assertEqual(replay["status"], "failed")
        self.assertFalse(any(row.get("type") == "full_agent.artifact_published" for row in self._audit_rows()))
        self.assertNotIn(str(fake), json.dumps([finished, self._audit_rows()]))
        self.assertTrue(self.source.exists())

    def bound_output(self):
        thread = self._create_thread(mode="full")
        turn_id = "image-test-turn"
        root, _ = self.bridge._full_agent_workspace_output_directory(thread["id"], turn_id)
        self.bridge.FULL_AGENT_ACTIVE_TURNS[turn_id] = {"threadId": thread["id"], "gatewayThreadId": "gateway-thread", "gatewayTurnId": "gateway-turn", "cancelRequested": False}
        self.gateway._turns["gateway-turn"] = {"threadId": "gateway-thread"}
        return thread["id"], turn_id, root

    def collect(self, thread_id, turn_id, root):
        return self.bridge._full_agent_collect_native_image_outputs(self.gateway, thread_id, turn_id, "gateway-thread", "gateway-turn", root)

    def test_cross_turn_destination_and_active_bindings_rejected(self):
        thread_id, turn_id, root = self.bound_output()
        original = dict(self.bridge.FULL_AGENT_ACTIVE_TURNS[turn_id])
        for key, value in (("threadId", "different-thread"), ("gatewayThreadId", "different-gateway"), ("gatewayTurnId", "different-turn"), ("cancelRequested", True)):
            with self.subTest(key=key):
                self.bridge.FULL_AGENT_ACTIVE_TURNS[turn_id] = {**original, key: value}
                with self.assertRaises(self.bridge.FullAgentArtifactError):
                    self.collect(thread_id, turn_id, root)
        self.bridge.FULL_AGENT_ACTIVE_TURNS[turn_id] = original
        other_root, _ = self.bridge._full_agent_workspace_output_directory(thread_id, "other-turn")
        with self.assertRaises(self.bridge.FullAgentArtifactError):
            self.collect(thread_id, turn_id, other_root)
        self.assertFalse(self.gateway.calls_for("collect_completed_image_outputs"))

    def test_reparse_source_or_parent_is_rejected(self):
        thread_id, turn_id, root = self.bound_output()
        actual = self.bridge._full_agent_path_is_link_or_reparse
        for unsafe in (self.source, self.source.parent):
            with self.subTest(unsafe=unsafe.name), mock.patch.object(self.bridge, "_full_agent_path_is_link_or_reparse", side_effect=lambda path: Path(path) == unsafe or actual(path)):
                with self.assertRaises(self.bridge.FullAgentArtifactError):
                    self.collect(thread_id, turn_id, root)
        self.assertEqual(list(root.iterdir()), [])

    def test_relative_traversal_missing_directory_and_wrong_mime_are_rejected(self):
        thread_id, turn_id, root = self.bound_output()
        wrong_suffix = self.root / "wrong.jpg"
        wrong_suffix.write_bytes(PNG_BYTES)
        folder = self.root / "directory.png"
        folder.mkdir()
        inputs = ["relative.png", str(self.root / "missing.png"), str(folder), str(wrong_suffix), str(self.root / ".." / self.root.name / self.source.name)]
        for source in inputs:
            with self.subTest(source=source):
                self.gateway.native_images = [("native-image-1", source)]
                with self.assertRaises(self.bridge.FullAgentArtifactError):
                    self.collect(thread_id, turn_id, root)
        self.assertEqual(list(root.iterdir()), [])

    def test_size_limit_is_enforced_before_copy(self):
        thread_id, turn_id, root = self.bound_output()
        with mock.patch.object(self.bridge, "MAX_REPORT_IMAGE_BYTES", len(PNG_BYTES) - 1):
            with self.assertRaises(self.bridge.FullAgentArtifactError):
                self.collect(thread_id, turn_id, root)
        self.assertEqual(list(root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
