from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge(name: str):
    spec = importlib.util.spec_from_file_location(name, BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BridgeStructuredTransportRegressionTests(unittest.TestCase):
    """Protect typed Runner receipts from text-level redaction corruption."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge("metafx_bridge_structured_transport_regressions")

    def _run_command_output(
        self,
        stdout: str,
        *,
        guarded: bool,
        output_limit: int,
        returncode: int = 0,
    ) -> dict:
        """Exercise both manual and auto/tree-guarded command paths."""

        if not guarded:
            completed = SimpleNamespace(
                returncode=returncode,
                stdout=stdout,
                stderr="",
            )
            with mock.patch.object(
                self.bridge.subprocess,
                "run",
                return_value=completed,
            ):
                return self.bridge.run_safe_command(
                    ["fixture-runner", "--structured-output"],
                    output_limit=output_limit,
                    structured_json_output=True,
                )

        process = mock.Mock()
        process.pid = 43210
        process.returncode = returncode
        process.communicate.return_value = (stdout, "")
        process.poll.return_value = 0
        process.wait.return_value = 0
        job_holder = {"handle": 1, "closed": False}
        with (
            mock.patch.object(
                self.bridge.subprocess,
                "Popen",
                return_value=process,
            ),
            mock.patch.object(
                self.bridge,
                "_create_windows_kill_job",
                return_value=job_holder,
            ),
            mock.patch.object(
                self.bridge,
                "_resume_windows_process",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_close_windows_kill_job",
                return_value=True,
            ),
        ):
            return self.bridge.run_safe_command(
                ["fixture-runner", "--structured-output"],
                output_limit=output_limit,
                kill_process_tree_on_timeout=True,
                structured_json_output=True,
            )

    @staticmethod
    def _field_map(envelope: dict) -> dict[str, str]:
        return {
            str(item["field"]): str(item["value"])
            for item in envelope.get("contractFields", [])
        }

    @staticmethod
    def _explicit_output_rejection(result: dict) -> bool:
        description = json.dumps(result, ensure_ascii=False).lower()
        return (
            result.get("ok") is False
            and str(result.get("exitCode")) != "0"
            and "output" in description
            and any(
                marker in description
                for marker in ("limit", "large", "oversize", "exceed")
            )
        )

    def _assert_not_leaked_through_json_escaping(
        self,
        result: dict,
        sensitive_value: str,
    ) -> None:
        """Check the raw value at every common nested-JSON escape depth."""

        probe = json.dumps(result, ensure_ascii=False)
        for _ in range(6):
            self.assertNotIn(sensitive_value, probe)
            probe = probe.replace(r"\\", "\\")

    def test_nested_newlines_and_digest_round_trip_in_manual_and_auto_paths(self) -> None:
        brief = {
            "schemaVersion": "ea-strategy-brief/1.0.0",
            "systemName": "Closed-bar RSI System",
            "systemOverview": (
                "บรรทัดแรกอธิบายระบบ\n"
                "บรรทัดที่สองยืนยันว่าต้องใช้แท่งปิดเท่านั้น\n"
                "บรรทัดที่สามกำหนดให้ค่า Input ปรับได้"
            ),
            "entryRules": "Buy เมื่อ RSI ต่ำกว่า 20\nSell เมื่อ RSI สูงกว่า 80",
            "exitRules": "ออกด้วย SL, TP หรือสัญญาณตรงข้าม",
        }
        encoded_brief = json.dumps(
            brief,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        source_digest = hashlib.sha256(encoded_brief.encode("utf-8")).hexdigest()
        envelope = {
            "status": "completed",
            "summary": "สร้าง Strategy Brief ครบแล้ว",
            "contractFields": [
                {"field": "strategyBrief", "value": encoded_brief},
                {"field": "sourceDigest", "value": source_digest},
            ],
            "evidenceKinds": ["public_web_source"],
            "evidence": [],
        }
        stdout = json.dumps(
            envelope,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        # The nested JSON string necessarily contains ``\\\\n`` in the outer
        # transport.  It must never be mistaken for a Windows UNC path.
        self.assertIn(r"\\n", stdout)
        for guarded in (False, True):
            with self.subTest(
                execution_path="auto_tree_guarded" if guarded else "manual",
            ):
                result = self._run_command_output(
                    stdout,
                    guarded=guarded,
                    output_limit=len(stdout) + 256,
                )
                self.assertTrue(result["ok"], result)
                transported = json.loads(result["output"])
                fields = self._field_map(transported)
                self.assertEqual(fields["strategyBrief"], encoded_brief)
                self.assertEqual(fields["sourceDigest"], source_digest)
                self.assertEqual(json.loads(fields["strategyBrief"]), brief)
                self.assertEqual(
                    hashlib.sha256(fields["strategyBrief"].encode("utf-8")).hexdigest(),
                    fields["sourceDigest"],
                )
                self.assertNotIn("[REDACTED_PATH]", result["output"])

    def test_valid_near_limit_nested_json_survives_escape_expansion(self) -> None:
        encoded_brief = json.dumps(
            {"additionalNotes": '"' * 28_000},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        envelope = {
            "ok": True,
            "status": "completed",
            "contractFields": [
                {"field": "strategyBrief", "value": encoded_brief},
                {
                    "field": "sourceDigest",
                    "value": hashlib.sha256(encoded_brief.encode("utf-8")).hexdigest(),
                },
            ],
        }
        stdout = json.dumps(envelope, ensure_ascii=False, separators=(",", ":"))
        self.assertGreater(len(stdout), 74_000)
        self.assertLess(len(stdout), 128_000)

        for guarded in (False, True):
            with self.subTest(guarded=guarded):
                result = self._run_command_output(
                    stdout,
                    guarded=guarded,
                    output_limit=128_000,
                )
                self.assertTrue(result["ok"], result)
                transported = json.loads(result["output"])
                fields = self._field_map(transported)
                self.assertEqual(fields["strategyBrief"], encoded_brief)
                self.assertEqual(
                    hashlib.sha256(fields["strategyBrief"].encode("utf-8")).hexdigest(),
                    fields["sourceDigest"],
                )

    def test_real_paths_and_secrets_are_sanitized_or_rejected_without_leaking(self) -> None:
        unc_path = r"\\student-pc\private-share\brief.json"
        drive_path = r"C:\Users\Student\Desktop\brief.json"
        secret_value = "sk-" + ("A" * 32)
        diagnostics = {
            "uncPath": unc_path,
            "drivePath": drive_path,
            "apiKey": secret_value,
        }
        encoded_diagnostics = json.dumps(
            diagnostics,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        envelope = {
            "status": "completed",
            "summary": "Runner diagnostics",
            "contractFields": [
                {"field": "diagnostics", "value": encoded_diagnostics},
            ],
            "evidenceKinds": [],
            "evidence": [],
        }
        stdout = json.dumps(
            envelope,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        for guarded in (False, True):
            with self.subTest(
                execution_path="auto_tree_guarded" if guarded else "manual",
            ):
                result = self._run_command_output(
                    stdout,
                    guarded=guarded,
                    output_limit=len(stdout) + 256,
                )
                self._assert_not_leaked_through_json_escaping(result, unc_path)
                self._assert_not_leaked_through_json_escaping(result, drive_path)
                self._assert_not_leaked_through_json_escaping(result, secret_value)

                if result.get("ok") is False:
                    self.assertNotEqual(str(result.get("exitCode")), "0")
                    continue

                transported = json.loads(result["output"])
                encoded_value = self._field_map(transported)["diagnostics"]
                sanitized = json.loads(encoded_value)
                sanitized_text = json.dumps(sanitized, ensure_ascii=False)
                self.assertIn("[REDACTED_PATH]", sanitized_text)
                self.assertIn("[REDACTED_SECRET]", sanitized_text)

    def test_oversized_structured_output_is_explicitly_rejected_not_clipped(self) -> None:
        envelope = {
            "status": "completed",
            "summary": "oversized fixture",
            "contractFields": [
                {"field": "strategyBrief", "value": "x" * 4096},
            ],
            "evidenceKinds": [],
            "evidence": [],
        }
        stdout = json.dumps(envelope, separators=(",", ":"))
        self.assertGreater(len(stdout), 512)

        for guarded in (False, True):
            with self.subTest(
                execution_path="auto_tree_guarded" if guarded else "manual",
            ):
                result = self._run_command_output(
                    stdout,
                    guarded=guarded,
                    output_limit=512,
                )
                self.assertTrue(self._explicit_output_rejection(result), result)
                # If an implementation returns JSON in the diagnostic message,
                # it must still be complete JSON rather than a clipped fragment.
                output = str(result.get("output") or "")
                if output.lstrip().startswith("{"):
                    json.loads(output)

    def test_duplicate_nonfinite_and_protected_field_names_fail_closed(self) -> None:
        attacks = {
            "duplicate_key": '{"ok":true,"ok":false}',
            "nan": '{"ok":true,"value":NaN}',
            "infinity": '{"ok":true,"value":Infinity}',
            "protected_key_path": json.dumps(
                {r"C:\\Users\\Student\\secret.txt": "value"},
                separators=(",", ":"),
            ),
        }
        for guarded in (False, True):
            for name, stdout in attacks.items():
                with self.subTest(guarded=guarded, attack=name):
                    result = self._run_command_output(
                        stdout,
                        guarded=guarded,
                        output_limit=1024,
                    )
                    self.assertFalse(result["ok"], result)
                    self.assertNotEqual(str(result.get("exitCode")), "0")
                    serialized = json.dumps(result, ensure_ascii=False)
                    self.assertNotIn(r"C:\\Users\\Student", serialized)

    def test_sensitive_metadata_requires_exact_boolean_contract(self) -> None:
        valid_envelope = {
            "ok": True,
            "status": "completed",
            "usage": {"secretRedacted": True},
            "safety": {
                "containsSecret": False,
                "frontendSecrets": False,
            },
        }
        invalid_envelopes = {
            "contains_secret_true": {"containsSecret": True},
            "contains_secret_integer_zero": {"contains_secret": 0},
            "frontend_secrets_true": {"frontendSecrets": True},
            "frontend_secrets_text_false": {"frontend_secrets": "false"},
            "secret_redacted_text": {"secretRedacted": "false"},
            "secret_redacted_integer": {"secret_redacted": 0},
            "secret_redacted_opaque_value": {
                "secretRedacted": "opaque-sensitive-value-123",
            },
        }

        for guarded in (False, True):
            with self.subTest(guarded=guarded, metadata="valid"):
                stdout = json.dumps(valid_envelope, separators=(",", ":"))
                result = self._run_command_output(
                    stdout,
                    guarded=guarded,
                    output_limit=2048,
                )
                self.assertTrue(result["ok"], result)
                self.assertEqual(json.loads(result["output"]), valid_envelope)

            for name, metadata in invalid_envelopes.items():
                with self.subTest(guarded=guarded, metadata=name):
                    stdout = json.dumps(
                        {"ok": True, "status": "completed", "safety": metadata},
                        separators=(",", ":"),
                    )
                    result = self._run_command_output(
                        stdout,
                        guarded=guarded,
                        output_limit=2048,
                    )
                    self.assertFalse(result["ok"], result)
                    self.assertEqual(result["exitCode"], "structured_output_unsafe")
                    rejection = json.loads(result["output"])
                    self.assertIs(rejection["ok"], False)
                    self.assertEqual(
                        rejection["status"],
                        "structured_output_unsafe",
                    )
                    self.assertNotIn(
                        "opaque-sensitive-value-123",
                        json.dumps(result, ensure_ascii=False),
                    )

    def test_nonzero_process_cannot_make_transport_successful(self) -> None:
        stdout = json.dumps(
            {"ok": True, "status": "completed", "summary": "forged success"},
            separators=(",", ":"),
        )
        for guarded in (False, True):
            with self.subTest(guarded=guarded):
                result = self._run_command_output(
                    stdout,
                    guarded=guarded,
                    output_limit=1024,
                    returncode=7,
                )
                self.assertFalse(result["ok"], result)
                self.assertEqual(result["exitCode"], 7)
                self.assertEqual(result["processExitCode"], 7)

    def _assert_structured_process_failure(
        self,
        result: dict,
        status: str,
        *protected_values: str,
    ) -> None:
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["exitCode"], status)
        self.assertLessEqual(len(result["output"]), 1024)
        payload = json.loads(result["output"])
        self.assertIs(payload["ok"], False)
        self.assertEqual(payload["status"], status)
        self.assertEqual(payload["workStatus"], "failed")
        self.assertTrue(payload["message"])
        serialized = json.dumps(result, ensure_ascii=False)
        for protected_value in protected_values:
            self.assertNotIn(protected_value, serialized)

    def test_structured_early_failures_are_json_in_guarded_and_plain_paths(self) -> None:
        protected_path = r"C:\Users\Student\private\runner.exe"
        protected_secret = "sk-" + ("Z" * 32)
        diagnostic = f"failure at {protected_path}; api_key={protected_secret}"
        cases = (
            (PermissionError(diagnostic), "permission_denied"),
            (FileNotFoundError(diagnostic), "not_found"),
            (RuntimeError(diagnostic), "exception"),
            (
                self.bridge.subprocess.TimeoutExpired(
                    ["fixture-runner", protected_path, protected_secret],
                    1,
                ),
                "timeout",
            ),
        )

        for guarded in (False, True):
            for error, expected_status in cases:
                # The guarded timeout is raised by Popen.communicate(), not by
                # Popen itself, and is exercised with a live process mock below.
                if guarded and expected_status == "timeout":
                    continue
                with self.subTest(guarded=guarded, status=expected_status):
                    target = "Popen" if guarded else "run"
                    with mock.patch.object(
                        self.bridge.subprocess,
                        target,
                        side_effect=error,
                    ):
                        result = self.bridge.run_safe_command(
                            ["fixture-runner", "--structured-output"],
                            timeout=1,
                            output_limit=1024,
                            kill_process_tree_on_timeout=guarded,
                            structured_json_output=True,
                        )
                    self._assert_structured_process_failure(
                        result,
                        expected_status,
                        protected_path,
                        protected_secret,
                    )

    def test_guarded_timeout_and_cancellation_return_json_failures(self) -> None:
        timeout_process = mock.Mock()
        timeout_process.pid = 43211
        timeout_process.communicate.side_effect = (
            self.bridge.subprocess.TimeoutExpired("fixture-runner", 1),
            ("", ""),
        )
        timeout_process.poll.return_value = 0
        job_holder = {"handle": 1, "closed": False}
        with (
            mock.patch.object(
                self.bridge.subprocess,
                "Popen",
                return_value=timeout_process,
            ),
            mock.patch.object(
                self.bridge,
                "_create_windows_kill_job",
                return_value=job_holder,
            ),
            mock.patch.object(
                self.bridge,
                "_resume_windows_process",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_terminate_command_process_tree",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_close_windows_kill_job",
                return_value=True,
            ),
        ):
            timeout_result = self.bridge.run_safe_command(
                ["fixture-runner", "--structured-output"],
                timeout=1,
                output_limit=1024,
                kill_process_tree_on_timeout=True,
                structured_json_output=True,
            )
        self._assert_structured_process_failure(timeout_result, "timeout")
        self.assertTrue(timeout_result["processStarted"])
        self.assertTrue(timeout_result["processTreeTerminated"])

        cancel_event = self.bridge.threading.Event()
        cancel_event.set()
        termination_observed = self.bridge.threading.Event()
        cancel_process = mock.Mock()
        cancel_process.pid = 43212
        cancel_process.poll.return_value = 0

        def terminate_for_cancel(_process, _job_holder):
            termination_observed.set()
            return True

        def communicate_after_cancel(*, input=None, timeout=None):
            self.assertTrue(termination_observed.wait(2))
            return "", ""

        cancel_process.communicate.side_effect = communicate_after_cancel
        with (
            mock.patch.object(
                self.bridge.subprocess,
                "Popen",
                return_value=cancel_process,
            ),
            mock.patch.object(
                self.bridge,
                "_create_windows_kill_job",
                return_value=job_holder,
            ),
            mock.patch.object(
                self.bridge,
                "_resume_windows_process",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_terminate_command_process_tree",
                side_effect=terminate_for_cancel,
            ),
            mock.patch.object(
                self.bridge,
                "_close_windows_kill_job",
                return_value=True,
            ),
        ):
            cancel_result = self.bridge.run_safe_command(
                ["fixture-runner", "--structured-output"],
                timeout=1,
                output_limit=1024,
                kill_process_tree_on_timeout=True,
                cancel_event=cancel_event,
                structured_json_output=True,
            )
        self._assert_structured_process_failure(cancel_result, "cancelled")
        self.assertTrue(cancel_result["processStarted"])
        self.assertTrue(cancel_result["processTreeTerminated"])


if __name__ == "__main__":
    unittest.main()
