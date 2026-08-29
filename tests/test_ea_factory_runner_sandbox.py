from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = PROJECT_ROOT / "runner" / "codex_cli_runner.py"


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "ea_factory_scoped_runner_under_test", RUNNER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class EaFactoryRunnerSandboxTests(unittest.TestCase):
    SOURCE_CONTENT = (
        "#property strict\n"
        "#define SIGNAL_NONE -1\n"
        "int OnInit() { return(INIT_SUCCEEDED); }\n"
        "void OnTick() { int signal = SIGNAL_NONE; }\n"
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()

    def _runner_patches(self, root: Path, fake_chat):
        workspace = root / "workspace"
        return (
            mock.patch.object(self.runner, "PROJECT_ROOT", root),
            mock.patch.object(self.runner, "AUTO_WORKSPACE_ROOT", workspace),
            mock.patch.object(
                self.runner,
                "AUTO_ADDITIONAL_WRITE_ROOTS",
                (root / "frontend", root / "docs", root / "assets-source"),
            ),
            mock.patch.object(
                self.runner,
                "AUTO_WRITE_ROOT_LABELS",
                ("workspace", "frontend", "docs", "assets-source"),
            ),
            mock.patch.object(self.runner, "CODEX_RUNS_DIR", root / "runs"),
            mock.patch.object(self.runner, "CODEX_BIN", root / "codex.exe"),
            mock.patch.object(
                self.runner,
                "chat_status",
                return_value={"ok": True, "status": "ready"},
            ),
            mock.patch.object(
                self.runner,
                "run_chat_command",
                side_effect=fake_chat,
            ),
        )

    def _factory_fixture(
        self,
        root: Path,
        *,
        build_id: str = "ea-build-1234567890-abc123",
        platform: str = "mt4",
    ) -> tuple[str, Path, str, str, str]:
        relative = f"ea-factory/{build_id}/Source"
        source = root / "workspace" / Path(relative)
        source.mkdir(parents=True)
        source_record_digest = "a" * 64
        spec = {
            "schemaVersion": "ea-factory-strategy-spec-v1",
            "buildId": build_id,
            "recordDigest": source_record_digest,
            "targetPlatform": platform,
            "immutable": True,
            "core": {"system_name": "Runner smoke test"},
        }
        spec_bytes = json.dumps(
            spec,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        (source / "strategy-spec-v01.json").write_bytes(spec_bytes)
        spec_digest = hashlib.sha256(spec_bytes).hexdigest()
        prompt = (
            f"[EA_FACTORY_BUILD_ID:{build_id}]"
            f"[EA_FACTORY_SOURCE_RECORD_DIGEST:{source_record_digest}]"
            f"[EA_FACTORY_STRATEGY_SPEC_DIGEST:{spec_digest}]"
            f"[EA_FACTORY_PLATFORM:{platform}] "
            f"Read ea-factory/{build_id}/Source/strategy-spec-v01.json and generate source."
        )
        return relative, source, prompt, source_record_digest, spec_digest

    def _patch_roots(self, root: Path):
        return (
            mock.patch.object(self.runner, "PROJECT_ROOT", root),
            mock.patch.object(
                self.runner, "AUTO_WORKSPACE_ROOT", root / "workspace"
            ),
        )

    def test_structured_generation_keeps_codex_read_only_and_runner_writes(self) -> None:
        captured: dict[str, object] = {}

        def fake_chat(command, **kwargs):
            captured["command"] = [str(item) for item in command]
            captured["cwd"] = Path(kwargs["cwd"])
            captured["prompt"] = str(kwargs.get("stdin") or "")
            raw_final_path = Path(command[command.index("-o") + 1])
            raw_payload = json.dumps({
                "fileName": "SmokeFactoryEA.mq4",
                "content": self.SOURCE_CONTENT,
            })
            raw_final_path.write_text(raw_payload, encoding="utf-8")
            return {
                "ok": True,
                "exitCode": 0,
                "durationMs": 1,
                "processStarted": True,
                "processTreeTerminated": False,
                "stdout": raw_payload,
                "stderr": "",
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source, prompt, _record_digest, _spec_digest = (
                self._factory_fixture(root)
            )
            for extra in ("frontend", "docs", "assets-source"):
                (root / extra).mkdir()
            (root / "codex.exe").write_bytes(b"")
            patches = self._runner_patches(root, fake_chat)
            with (
                patches[0], patches[1], patches[2], patches[3],
                patches[4], patches[5], patches[6], patches[7],
            ):
                result = self.runner.run_codex(
                    prompt,
                    "ea_developer",
                    "mission-ea-factory-structured",
                    execution_mode="auto_guarded",
                    read_only_work=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )
                source_bytes = (source / "SmokeFactoryEA.mq4").read_bytes()
                stdout_artifact = (
                    root / result["artifacts"]["stdout"]
                ).read_text(encoding="utf-8")

        command = captured["command"]
        self.assertEqual(captured["cwd"], source)
        self.assertEqual(command[command.index("--cd") + 1], str(source))
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
        self.assertNotIn("--add-dir", command)
        self.assertTrue(result["ok"])
        self.assertEqual(result["requestedSandbox"], "read-only")
        self.assertEqual(result["sandbox"], "read-only")
        self.assertEqual(result["workingDirectory"], f"workspace/{relative}")
        self.assertEqual(result["writeRoots"], [])
        self.assertFalse(result["controlPlaneWritable"])
        self.assertFalse(result["projectCodeWritable"])
        self.assertEqual(source_bytes, self.SOURCE_CONTENT.encode("utf-8"))
        self.assertEqual(
            result["eaFactorySourceWriterVersion"],
            "ea-factory-structured-source-v1",
        )
        serialized_result = json.dumps(result, ensure_ascii=False)
        self.assertNotIn(self.SOURCE_CONTENT, serialized_result)
        self.assertNotIn(self.SOURCE_CONTENT, stdout_artifact)
        prompt_text = captured["prompt"]
        self.assertIn("Codex itself is running in a read-only OS sandbox", prompt_text)
        self.assertIn("containing only fileName and content", prompt_text)
        self.assertNotIn("only writable root", prompt_text)

    def test_materializer_writes_exact_file_and_digest_without_content_leak(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source, prompt, record_digest, spec_digest = (
                self._factory_fixture(root)
            )
            raw = json.dumps({
                "fileName": "ExactEA.mq4",
                "content": self.SOURCE_CONTENT,
            })
            patches = self._patch_roots(root)
            with patches[0], patches[1]:
                result = self.runner.materialize_ea_factory_source_result(
                    raw, prompt, relative
                )

            written = (source / "ExactEA.mq4").read_bytes()
            expected_digest = hashlib.sha256(
                self.SOURCE_CONTENT.encode("utf-8")
            ).hexdigest()
            values = {
                item["field"]: item["value"]
                for item in result["contractFields"]
            }

        self.assertEqual(written, self.SOURCE_CONTENT.encode("utf-8"))
        self.assertEqual(values["sourceDigest"], expected_digest)
        self.assertEqual(values["sourceRecordDigest"], record_digest)
        self.assertEqual(values["strategySpecDigest"], spec_digest)
        self.assertEqual(values["platform"], "mt4")
        self.assertEqual(
            json.loads(values["sourceFiles"]),
            [f"workspace/{relative}/ExactEA.mq4"],
        )
        self.assertEqual(
            result["evidenceKinds"],
            [
                "project_relative_source_path",
                "source_digest",
                "uncompiled_status",
            ],
        )
        self.assertNotIn(
            self.SOURCE_CONTENT, json.dumps(result, ensure_ascii=False)
        )

    def test_invalid_structured_outputs_never_write_a_source(self) -> None:
        oversized_content = (
            self.SOURCE_CONTENT
            + "//"
            + ("x" * self.runner.EA_FACTORY_SOURCE_MAX_CHARS)
        )
        invalid_payloads = {
            "filename_traversal": json.dumps({
                "fileName": "../evil.mq4", "content": self.SOURCE_CONTENT
            }),
            "nested_filename": json.dumps({
                "fileName": "nested/evil.mq4", "content": self.SOURCE_CONTENT
            }),
            "wrong_extension": json.dumps({
                "fileName": "WrongEA.mq5", "content": self.SOURCE_CONTENT
            }),
            "malformed_json": "{",
            "extra_field": json.dumps({
                "fileName": "ExtraEA.mq4",
                "content": self.SOURCE_CONTENT,
                "path": "elsewhere",
            }),
            "duplicate_key": (
                '{"fileName":"One.mq4","fileName":"Two.mq4",'
                f'"content":{json.dumps(self.SOURCE_CONTENT)}}}'
            ),
            "empty_content": json.dumps({
                "fileName": "EmptyEA.mq4", "content": "   \n"
            }),
            "malformed_content": json.dumps({
                "fileName": "MalformedEA.mq4",
                "content": "This is not MQL source.",
            }),
            "oversized_content": json.dumps({
                "fileName": "OversizedEA.mq4", "content": oversized_content
            }),
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source, prompt, _record_digest, _spec_digest = (
                self._factory_fixture(root)
            )
            patches = self._patch_roots(root)
            with patches[0], patches[1]:
                for label, raw in invalid_payloads.items():
                    with self.subTest(label=label):
                        with self.assertRaises(ValueError):
                            self.runner.materialize_ea_factory_source_result(
                                raw, prompt, relative
                            )
                        self.assertEqual(
                            {item.name for item in source.iterdir()},
                            {"strategy-spec-v01.json"},
                        )
                        self.assertFalse((root / "evil.mq4").exists())

    def test_binding_tamper_and_conflicting_destination_fail_without_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source, prompt, _record_digest, _spec_digest = (
                self._factory_fixture(root)
            )
            raw = json.dumps({
                "fileName": "BoundEA.mq4", "content": self.SOURCE_CONTENT
            })
            patches = self._patch_roots(root)
            with patches[0], patches[1]:
                with self.assertRaises(ValueError):
                    self.runner.materialize_ea_factory_source_result(
                        raw,
                        prompt.replace(
                            "EA_FACTORY_BUILD_ID:ea-build-1234567890-abc123",
                            "EA_FACTORY_BUILD_ID:ea-build-another",
                        ),
                        relative,
                    )
                self.assertFalse((source / "BoundEA.mq4").exists())
                (source / "BoundEA.mq4").write_text(
                    "different", encoding="utf-8"
                )
                with self.assertRaises(ValueError):
                    self.runner.materialize_ea_factory_source_result(
                        raw, prompt, relative
                    )
                self.assertEqual(
                    (source / "BoundEA.mq4").read_text(encoding="utf-8"),
                    "different",
                )

    def test_tampered_scoped_roots_fail_before_process_start(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace").mkdir()
            fake_chat = mock.Mock()
            patches = self._runner_patches(root, fake_chat)
            invalid = (
                "../ea-factory/ea-build-1/Source",
                "ea-factory\\ea-build-1\\Source",
                "ea-factory/ea-build-1/Source/",
                "ea-factory/not-a-build/Source",
                "ea-factory/ea-build-1/source",
                str((root / "workspace" / "ea-factory" / "ea-build-1" / "Source").resolve()),
            )
            with (
                patches[0], patches[1], patches[2], patches[3],
                patches[4], patches[5], patches[6], patches[7],
            ):
                results = [
                    self.runner.run_codex(
                        "Generate source.",
                        "ea_developer",
                        f"mission-invalid-{index}",
                        execution_mode="auto_guarded",
                        read_only_work=True,
                        result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                        scoped_workspace_write_root=value,
                    )
                    for index, value in enumerate(invalid)
                ]

        fake_chat.assert_not_called()
        for result in results:
            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "workspace_policy_invalid")
            self.assertFalse(result["processStarted"])

    def test_scoped_profile_rejects_write_search_and_other_execution_modes(self) -> None:
        relative = "ea-factory/ea-build-1234/Source"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / Path(relative)).mkdir(parents=True)
            fake_chat = mock.Mock()
            patches = self._runner_patches(root, fake_chat)
            with (
                patches[0], patches[1], patches[2], patches[3],
                patches[4], patches[5], patches[6], patches[7],
            ):
                writable = self.runner.run_codex(
                    "Generate source.", "ea_developer", "mission-scoped-writable",
                    execution_mode="auto_guarded",
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )
                searched = self.runner.run_codex(
                    "Generate source.", "ea_developer", "mission-scoped-search",
                    execution_mode="auto_guarded", read_only_work=True,
                    web_search=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )
                manual = self.runner.run_codex(
                    "Generate source.", "ea_developer", "mission-scoped-manual",
                    execution_mode="manual_guarded", read_only_work=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )
                legacy = self.runner.run_codex(
                    "Generate source.", "ea_developer", "mission-scoped-legacy",
                    execution_mode="auto_guarded",
                    scoped_workspace_write_root=relative,
                )
                missing_scope = self.runner.run_codex(
                    "Generate source.", "ea_developer", "mission-missing-scope",
                    execution_mode="auto_guarded", read_only_work=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                )

        fake_chat.assert_not_called()
        for result in (writable, searched, manual, legacy, missing_scope):
            self.assertEqual(result["status"], "workspace_policy_invalid")
            self.assertFalse(result["processStarted"])

    def test_scoped_source_rejects_linked_source_directory(self) -> None:
        relative = "ea-factory/ea-build-linked/Source"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "actual-source"
            target.mkdir()
            linked = root / "workspace" / Path(relative)
            linked.parent.mkdir(parents=True)
            try:
                os.symlink(target, linked, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"directory symlink unavailable: {error}")
            fake_chat = mock.Mock()
            patches = self._runner_patches(root, fake_chat)
            with (
                patches[0], patches[1], patches[2], patches[3],
                patches[4], patches[5], patches[6], patches[7],
            ):
                result = self.runner.run_codex(
                    "Generate source.",
                    "ea_developer",
                    "mission-scoped-link",
                    execution_mode="auto_guarded",
                    read_only_work=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )

        fake_chat.assert_not_called()
        self.assertEqual(result["status"], "workspace_policy_invalid")
        self.assertFalse(result["processStarted"])


if __name__ == "__main__":
    unittest.main()
