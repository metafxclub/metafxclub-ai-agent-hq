from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import tempfile
import threading
import time
import unittest
import zlib
from contextlib import ExitStack
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_ea_factory_one_click_backend",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EaFactoryOneClickBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        # One-click tests exercise behavior after the global header has already
        # locked both terminals.  The lock gate itself is covered explicitly
        # below; every other test gets one current context for the requested
        # platform and must not depend on Council ``activePlatform``.
        self.original_require_top_header_locks = (
            self.bridge._ea_factory_require_top_header_locks
        )
        self.global_platform_context = mock.patch.object(
            self.bridge,
            "_ea_factory_require_top_header_locks",
            side_effect=self._dual_locked_platform_context,
        )
        self.global_platform_context.start()
        self.current_terminal_binding = mock.patch.object(
            self.bridge,
            "_ea_factory_one_click_terminal_binding_current",
            return_value=True,
        )
        self.current_terminal_binding.start()

    def tearDown(self) -> None:
        self.current_terminal_binding.stop()
        self.global_platform_context.stop()

    def _dual_locked_platform_context(
        self,
        platform: object,
        *,
        require_all_platforms: bool = True,
    ) -> dict | None:
        normalized = str(platform or "").strip().lower()
        if normalized not in {"mt4", "mt5"}:
            return None
        candidate_id = "mtc-one-click-terminal"
        return {
            "record": {
                "candidateId": candidate_id,
                "platform": normalized,
                "available": True,
                "runningState": "platform_running_detected",
            },
            "token": {
                "candidateId": candidate_id,
                "platform": normalized,
                "selectionRevision": 7,
            },
        }

    def test_mt5_read_validation_preserves_existing_set_and_never_repairs_evidence(self) -> None:
        source = b"input double Lots = 0.01;\ninput int MagicNumber = 4186;\nvoid OnTick(){}\n"
        with tempfile.TemporaryDirectory() as temporary:
            build_dir = Path(temporary).resolve()
            (build_dir / "Sets").mkdir()
            context = {
                "buildDir": build_dir,
                "sourceBytes": source,
                "sourceDigest": hashlib.sha256(source).hexdigest(),
            }
            manifest = self.bridge._ea_factory_mt5_optimization_input_manifest(context)
            reference = self.bridge._ea_factory_write_mt5_set_reference(
                context, "read-only-proof.set", manifest, []
            )
            path = build_dir / reference["relativePath"]
            original = path.read_bytes()
            original_mtime = path.stat().st_mtime_ns
            with mock.patch.object(self.bridge.os, "open", side_effect=AssertionError("Read validation must not attempt creation")):
                observed = self.bridge._ea_factory_write_mt5_set_reference(
                    context, "read-only-proof.set", manifest, [], materialize=False
                )
            self.assertEqual(observed, reference)
            self.assertEqual(path.stat().st_mtime_ns, original_mtime)
            self.assertEqual(path.read_bytes(), original)

            for changed_payload in (b"tampered input set", None):
                with self.subTest(changed_payload=changed_payload):
                    if changed_payload is None:
                        path.unlink()
                    else:
                        path.write_bytes(changed_payload)
                    with mock.patch.object(self.bridge.os, "open", side_effect=AssertionError("Missing proof must not be regenerated")):
                        with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                            self.bridge._ea_factory_write_mt5_set_reference(
                                context, "read-only-proof.set", manifest, [], materialize=False
                            )
                    self.assertEqual(caught.exception.code, "immutable_set_conflict")
                    self.assertEqual(path.read_bytes() if path.exists() else None, changed_payload)

    def test_mt5_read_binding_propagates_read_only_and_rejects_missing_set(self) -> None:
        source = b"input double Lots = 0.01;\nvoid OnTick(){}\n"
        with tempfile.TemporaryDirectory() as temporary:
            build_dir = Path(temporary).resolve()
            (build_dir / "Sets").mkdir()
            context = {"buildDir": build_dir, "sourceBytes": source, "sourceDigest": hashlib.sha256(source).hexdigest()}
            with (
                mock.patch.object(self.bridge, "_ea_factory_mt5_input_context", return_value=context),
                mock.patch.object(self.bridge, "_ea_factory_mt5_tester_input_preset", return_value={}),
                mock.patch.object(self.bridge, "_ea_factory_mt5_tester_fixed_overrides", return_value={}),
                mock.patch.object(self.bridge, "_ea_factory_mt5_compiled_deployment_binding", return_value={}) as deployment,
                mock.patch.object(self.bridge.os, "open", side_effect=AssertionError("Validation must not create a missing set")),
            ):
                with self.assertRaises(self.bridge.RequestError):
                    self.bridge._ea_factory_mt5_backtest_input_binding(
                        {}, "ea-visible-read-only", {}, materialize=False
                    )
                deployment.assert_not_called()
            self.assertEqual(list((build_dir / "Sets").iterdir()), [])

    def test_one_click_rejects_mt_work_before_side_effects_when_dual_locks_missing(
        self,
    ) -> None:
        build = self.build()
        state = self.state(build)
        with (
            mock.patch.object(
                self.bridge,
                "_global_metatrader_platform_context",
                return_value=None,
            ) as global_context,
            mock.patch.object(
                self.bridge,
                "_ea_factory_require_top_header_locks",
                side_effect=self.original_require_top_header_locks,
            ) as lock_gate,
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_metaeditor_target_context",
            ) as resolve_target,
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_one_click_thread",
            ) as start,
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ) as write,
            self.assertRaises(self.bridge.RequestError) as raised,
        ):
            self.bridge.run_ea_factory_build_one_click(
                build["id"],
                {"idempotencyKey": "one-click-lock-gate"},
            )

        self.assertEqual(raised.exception.status, 409)
        self.assertEqual(
            raised.exception.code,
            "global_metatrader_locks_incomplete",
        )
        lock_gate.assert_called_once_with("mt4")
        global_context.assert_called_once_with("mt4", require_all_platforms=True)
        resolve_target.assert_not_called()
        start.assert_not_called()
        write.assert_not_called()

    def test_compile_result_contract_accepts_canonical_and_native_mt5_rows(self) -> None:
        accepted = (
            "Result: 0 errors, 0 warnings",
            "0 errors, 0 warnings, 785 ms elapsed, cpu='AVX2 + FMA3'",
        )
        for line in accepted:
            with self.subTest(line=line):
                self.assertIsNotNone(
                    self.bridge.EA_FACTORY_ZERO_COMPILE_RESULT.fullmatch(line)
                )
        for line in (
            "Result: 1 errors, 0 warnings",
            "0 errors, 1 warnings",
            "0 errors, 0 warnings, accepted without native evidence",
        ):
            with self.subTest(rejected=line):
                self.assertIsNone(
                    self.bridge.EA_FACTORY_ZERO_COMPILE_RESULT.fullmatch(line)
                )

    def test_visible_capability_failure_preserves_machine_reason_code(self) -> None:
        capability = {
            "ready": False,
            "reasonCode": "mt5_tester_controls_not_verified",
        }
        request = {
            "stageId": "backtest_recheck",
            "platform": "mt5",
            "terminalBinding": {},
            "visibleOperation": {},
            "resolvedTarget": {},
            "testerSettings": {},
        }
        with (
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                return_value=capability,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_STRATEGY_TESTER_HANDLER",
                lambda **_kwargs: {},
            ),
            self.assertRaises(self.bridge.RequestError) as raised,
        ):
            self.bridge._ea_factory_invoke_visible_front_office_handler_unlocked(
                request
            )
        self.assertEqual(raised.exception.status, 409)
        self.assertEqual(
            raised.exception.code,
            "mt5_tester_controls_not_verified",
        )
        self.assertTrue(raised.exception.retryable)

    def _default_tester_settings_at(
        self,
        now_utc: datetime,
        *,
        build: dict | None = None,
    ) -> dict:
        selected_build = build or self.build()
        if build is None:
            selected_build["platform"] = "mt5"
        binary_suffix = (
            ".ex5" if selected_build.get("platform") == "mt5" else ".ex4"
        )
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_backtest_binary",
                return_value={"fileName": "Rolling_Window" + binary_suffix},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_mt4_tester_input_preset",
                return_value=None,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_mt5_tester_input_preset",
                return_value=None,
            ),
        ):
            return self.bridge._ea_factory_default_tester_settings(
                selected_build,
                now_utc=now_utc,
            )

    def test_default_tester_settings_use_previous_utc_day_for_90_inclusive_days(self) -> None:
        settings = self._default_tester_settings_at(
            datetime(2026, 10, 15, 23, 59, 59, tzinfo=timezone.utc)
        )

        self.assertTrue(settings["useDate"])
        self.assertEqual(settings["fromDate"], "2026-07-17")
        self.assertEqual(settings["toDate"], "2026-10-14")
        start = date.fromisoformat(settings["fromDate"])
        end = date.fromisoformat(settings["toDate"])
        self.assertEqual((end - start).days + 1, 90)

    def test_default_tester_settings_normalize_to_utc_before_previous_day(self) -> None:
        settings = self._default_tester_settings_at(
            datetime(
                2026,
                10,
                15,
                0,
                30,
                tzinfo=timezone(timedelta(hours=7)),
            )
        )

        self.assertEqual(settings["toDate"], "2026-10-13")
        self.assertEqual(settings["fromDate"], "2026-07-16")

    def test_default_tester_settings_handle_leap_day_in_90_day_window(self) -> None:
        settings = self._default_tester_settings_at(
            datetime(2024, 3, 1, 12, 0, tzinfo=timezone.utc)
        )

        self.assertEqual(settings["toDate"], "2024-02-29")
        self.assertEqual(settings["fromDate"], "2023-12-02")
        start = date.fromisoformat(settings["fromDate"])
        end = date.fromisoformat(settings["toDate"])
        self.assertEqual((end - start).days + 1, 90)

    def test_default_tester_settings_preserve_mt4_full_history_contract(self) -> None:
        build = self.build()

        settings = self._default_tester_settings_at(
            datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc),
            build=build,
        )

        self.assertEqual(settings["expertFileName"], "Rolling_Window.ex4")
        self.assertFalse(settings["useDate"])
        self.assertIsNone(settings["fromDate"])
        self.assertIsNone(settings["toDate"])

    def _resolved_tester_settings(
        self,
        *,
        use_date: bool,
        from_date: str | None,
        to_date: str | None,
    ) -> dict:
        return {
            "schemaVersion": self.bridge.EA_FACTORY_RESOLVED_TESTER_SETTINGS_SCHEMA_VERSION,
            "expertFileName": "Rolling_Window.ex5",
            "symbol": "XAUUSD",
            "period": "H1",
            "model": "every_tick",
            "spread": "current",
            "useDate": use_date,
            "fromDate": from_date,
            "toDate": to_date,
            "deposit": 10_000.0,
            "visualMode": True,
            "optimizationEnabled": False,
            "shutdownTerminalAfterTest": False,
        }

    def test_resolved_tester_settings_accept_exact_mt5_90_day_request(self) -> None:
        request = {
            "useDate": True,
            "fromDate": "2026-07-17",
            "toDate": "2026-10-14",
        }
        resolved = self._resolved_tester_settings(
            use_date=True,
            from_date="2026-07-17",
            to_date="2026-10-14",
        )

        self.assertTrue(
            self.bridge._ea_factory_resolved_tester_settings_valid(
                resolved,
                expert_file_name="Rolling_Window.ex5",
                expected_request_settings=request,
            )
        )
        self.assertTrue(
            self.bridge._ea_factory_resolved_tester_settings_valid(
                resolved,
                expert_file_name="Rolling_Window.ex5",
            )
        )

    def test_resolved_tester_settings_reject_mismatch_and_malformed_window(self) -> None:
        request = {
            "useDate": True,
            "fromDate": "2026-07-17",
            "toDate": "2026-10-14",
        }
        mismatched = self._resolved_tester_settings(
            use_date=True,
            from_date="2026-07-18",
            to_date="2026-10-14",
        )
        malformed = self._resolved_tester_settings(
            use_date=True,
            from_date="2026-10-15",
            to_date="2025-10-14",
        )

        self.assertFalse(
            self.bridge._ea_factory_resolved_tester_settings_valid(
                mismatched,
                expert_file_name="Rolling_Window.ex5",
                expected_request_settings=request,
            )
        )
        self.assertFalse(
            self.bridge._ea_factory_resolved_tester_settings_valid(
                malformed,
                expert_file_name="Rolling_Window.ex5",
                expected_request_settings={
                    "useDate": True,
                    "fromDate": "2026-10-15",
                    "toDate": "2025-10-14",
                },
            )
        )

    def test_resolved_tester_settings_preserve_legacy_optimization_baseline(self) -> None:
        legacy_request = {
            "useDate": False,
            "fromDate": None,
            "toDate": None,
        }
        resolved = self._resolved_tester_settings(
            use_date=False,
            from_date=None,
            to_date=None,
        )

        self.assertTrue(
            self.bridge._ea_factory_resolved_tester_settings_valid(
                resolved,
                expert_file_name="Rolling_Window.ex5",
                expected_request_settings=legacy_request,
            )
        )
        self.assertTrue(
            self.bridge._ea_factory_resolved_tester_settings_valid(
                resolved,
                expert_file_name="Rolling_Window.ex5",
            )
        )

    def test_default_tester_settings_reservation_anchor_keeps_request_digest_stable(self) -> None:
        build = self.build()
        build["platform"] = "mt5"
        build["oneClickRun"] = {
            "visibleAction": {
                "stageId": "backtest_recheck",
                "reservedAt": "2024-03-01T00:00:00Z",
            },
            "terminalBinding": {
                "platform": "mt5",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
        }
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_backtest_binary",
                return_value={
                    "fileId": "compiled-binary",
                    "fileName": "Rolling_Window.ex5",
                    "sha256": "a" * 64,
                },
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_mt5_tester_input_preset",
                return_value=None,
            ),
        ):
            first = self.bridge._ea_factory_default_tester_settings(build)
            second = self.bridge._ea_factory_default_tester_settings(build)
            request = {
                "visibleOperation": {"operationId": "ea-visible-test"},
                "testerSettings": copy.deepcopy(first),
            }
            result = {
                "artifactSpecifications": [
                    {"alias": "tester_settings"},
                ],
                "metrics": {},
            }
            artifact_rows = [
                {
                    "fileId": "settings-proof",
                    "relativePath": "Screenshots/settings.png",
                    "byteSize": 2048,
                    "sha256": "b" * 64,
                    "stageId": "backtest_recheck",
                    "reportId": "report-test",
                    "artifactKind": "screenshot_evidence",
                }
            ]
            metrics = self.bridge._ea_factory_visible_result_metrics(
                build,
                "backtest_recheck",
                request,
                result,
                artifact_rows,
            )

        expected_digest = self.bridge.payload_digest(
            "ea-factory-tester-settings-request-v1",
            first,
        )
        self.assertEqual(first, second)
        self.assertEqual(first["fromDate"], "2023-12-02")
        self.assertEqual(first["toDate"], "2024-02-29")
        self.assertEqual(metrics["testerSettingsRequestDigest"], expected_digest)
        self.assertEqual(
            self.bridge.payload_digest(
                "ea-factory-tester-settings-request-v1",
                second,
            ),
            expected_digest,
        )

    def build(self) -> dict:
        stages = []
        for stage_id in self.bridge.EA_FACTORY_STAGE_IDS:
            completed = stage_id == "strategy_spec"
            stages.append({
                "id": stage_id,
                "status": "completed" if completed else "pending",
                "missionId": "mission-spec" if completed else None,
                "reportId": "report-spec" if completed else None,
                "blockedReasonCode": None,
                "evidenceVerified": completed,
                "requestIdempotencyKey": None,
                "requestDigest": None,
                "missionIdempotencyKey": None,
                "manualRetryCount": 0,
                "manualRetryHistory": [],
                "artifacts": [],
                "updatedAt": "2026-09-11T00:00:00Z",
            })
        return {
            "schemaVersion": "ea-factory-build-v1",
            "id": "ea-build-one-click-test",
            "sourceRecordId": "deep-source-one-click",
            "sourceRecordDigest": "a" * 64,
            "createRequestDigest": "b" * 64,
            "coverageStatus": "compact_current",
            "coverageUpgradeRequired": False,
            "platform": "mt4",
            "artifactKind": "expert_advisor",
            "brief": "",
            "status": "ready",
            "workspace": {"folderNames": []},
            "stages": stages,
            "versions": [],
            "createdAt": "2026-09-11T00:00:00Z",
            "updatedAt": "2026-09-11T00:00:00Z",
        }

    def state(self, build: dict) -> dict:
        return {
            "schemaVersion": self.bridge.EA_FACTORY_STATE_SCHEMA_VERSION,
            "sourceSnapshots": [],
            "builds": [build],
            "createReservations": [],
            "updatedAt": None,
        }

    def backtest_restart_build(self, *, status: str = "failed") -> dict:
        build = self.build()
        for stage in build["stages"]:
            if stage["id"] in {
                "strategy_spec",
                "generate_source",
                "source_review",
                "compile_validate",
            }:
                stage.update({
                    "status": "completed",
                    "missionId": f"mission-{stage['id']}",
                    "reportId": f"report-{stage['id']}",
                    "evidenceVerified": True,
                })
            elif stage["id"] == "backtest_recheck":
                stage.update({
                    "status": "pending",
                    "missionId": "mission-old-backtest",
                    "reportId": None,
                    "evidenceVerified": False,
                })
        build["workspace"]["strategySpecDigest"] = "e" * 64
        build["versions"] = [{
            "version": 4,
            "fileName": "Guarded_Backtest.mq4",
            "sourceFile": "Source/Guarded_Backtest.mq4",
            "versionFile": "EA_Versions/Guarded_Backtest-v04.mq4",
            "sourceDigest": "d" * 64,
        }]
        now = "2026-10-15T00:00:00Z"
        terminal_statuses = {"failed", "cancelled"}
        build["oneClickRun"] = {
            "schemaVersion": self.bridge.EA_FACTORY_ONE_CLICK_SCHEMA_VERSION,
            "runId": "ea-run-old-backtest",
            "idempotencyKey": "one-click-old-backtest",
            "requestDigest": self.bridge._ea_factory_one_click_request_digest(build),
            "status": status,
            "currentStageId": "backtest_recheck",
            "terminalBinding": {
                "platform": "mt4",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "failureCode": "visible_backtest_failed" if status in terminal_statuses else None,
            "messageTh": "รอบเดิมหยุดก่อนมีหลักฐาน Backtest ที่ผ่าน Gate",
            "startedAt": now,
            "updatedAt": now,
            "completedAt": now if status in terminal_statuses else None,
        }
        return build

    def backtest_restart_mt5_manifest_fixture(
        self,
        root: Path,
    ) -> tuple[dict, list[dict], Path]:
        build = self.backtest_restart_build()
        build["platform"] = "mt5"
        build["versions"] = [{
            "version": 4,
            "fileName": "Guarded_Backtest.mq5",
            "sourceFile": "Source/Guarded_Backtest.mq5",
            "versionFile": "EA_Versions/Guarded_Backtest-v04.mq5",
            "sourceDigest": "d" * 64,
        }]
        build_dir = root / "workspace" / "ea-factory" / build["id"]
        for folder_name in ("EA_Versions", "Reports", "Screenshots"):
            (build_dir / folder_name).mkdir(parents=True, exist_ok=True)
        binary_path = build_dir / "EA_Versions" / "Guarded_Backtest-v04.ex5"
        binary_path.write_bytes(b"compiled mt5 regression fixture")
        (build_dir / "Reports" / "compile.txt").write_text(
            "Result: 0 errors, 0 warnings\n",
            encoding="utf-8",
        )
        (build_dir / "Reports" / "compile-receipt.json").write_text(
            json.dumps({"result": "0 errors, 0 warnings"}),
            encoding="utf-8",
        )
        (build_dir / "Screenshots" / "compile.png").write_bytes(
            b"\x89PNG\r\n\x1a\ncompile evidence"
        )
        compile_stage = next(
            row for row in build["stages"] if row["id"] == "compile_validate"
        )
        registered = self.bridge._ea_factory_register_artifacts(
            build,
            [
                {
                    "relativePath": "EA_Versions/Guarded_Backtest-v04.ex5",
                    "stageId": "compile_validate",
                    "reportId": compile_stage["reportId"],
                    "artifactKind": "compile_evidence",
                },
                {
                    "relativePath": "Screenshots/compile.png",
                    "stageId": "compile_validate",
                    "reportId": compile_stage["reportId"],
                    "artifactKind": "screenshot_evidence",
                },
                {
                    "relativePath": "Reports/compile.txt",
                    "stageId": "compile_validate",
                    "reportId": compile_stage["reportId"],
                    "artifactKind": "compile_evidence",
                },
                {
                    "relativePath": "Reports/compile-receipt.json",
                    "stageId": "compile_validate",
                    "reportId": compile_stage["reportId"],
                    "artifactKind": "compile_evidence",
                },
            ],
        )
        compile_stage["artifacts"] = [row["fileId"] for row in registered]
        return build, registered, binary_path

    def backtest_restart_contract(self, digest: str = "f" * 64) -> dict:
        return {
            "schemaVersion": "ea-factory-backtest-restart-contract-v1",
            "buildId": "ea-build-one-click-test",
            "versions": [{"sourceDigest": "d" * 64}],
            "compileEvidence": {"artifacts": [{"sha256": "a" * 64}]},
            "contractDigest": digest,
        }

    def backtest_restart_patch_stack(
        self,
        state: dict,
        *,
        contract_side_effect: object = None,
        coordinator_alive: bool = False,
        terminal_current: bool = True,
    ) -> tuple[ExitStack, dict[str, mock.Mock]]:
        stack = ExitStack()
        contract = self.backtest_restart_contract()
        contract_patch = (
            mock.patch.object(
                self.bridge,
                "_ea_factory_backtest_restart_contract",
                side_effect=contract_side_effect,
            )
            if contract_side_effect is not None
            else mock.patch.object(
                self.bridge,
                "_ea_factory_backtest_restart_contract",
                return_value=contract,
            )
        )
        handles = {
            "write": stack.enter_context(
                mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked")
            ),
            "start": stack.enter_context(
                mock.patch.object(
                    self.bridge,
                    "_start_ea_factory_one_click_thread",
                    return_value=True,
                )
            ),
            "idle": stack.enter_context(
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_backtest_restart_idle_probe",
                    return_value={"testerStartState": "Start"},
                )
            ),
            "advance": stack.enter_context(
                mock.patch.object(self.bridge, "advance_ea_factory_build")
            ),
            "ai": stack.enter_context(
                mock.patch.object(self.bridge, "run_dashboard_workflow_action")
            ),
        }
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            )
        )
        stack.enter_context(mock.patch.object(self.bridge, "load_missions", return_value=[]))
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "_ea_factory_active_worker_payload",
                return_value=None,
            )
        )
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "_ea_factory_any_one_click_coordinator_alive",
                return_value=coordinator_alive,
            )
        )
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_terminal_binding_current",
                return_value=terminal_current,
            )
        )
        stack.enter_context(contract_patch)
        stack.enter_context(mock.patch.object(self.bridge, "append_audit"))
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_read_model",
                side_effect=lambda row: {
                    "runId": row["oneClickRun"]["runId"],
                    "status": row["oneClickRun"]["status"],
                },
            )
        )
        return stack, handles

    def restart_revalidation_fixture(
        self,
        root: Path,
        reports_dir: Path,
    ) -> tuple[dict, dict, dict]:
        compact_values = {
            "record_id": "restart-history-row-001",
            "system_name": "Restart history EMA crossover",
            "system_overview": (
                "Closed-bar trend system for a selected liquid market and timeframe."
            ),
            "entry_rules": (
                "Buy on a confirmed EMA fast cross above slow; sell on the inverse."
            ),
            "recovery_rules": "No recovery, grid, martingale, averaging, or hedging.",
            "exit_rules": (
                "Close on the opposite signal with bounded stop loss and take profit."
            ),
            "money_management": (
                "Use a positive fixed lot and at most one managed position."
            ),
            "order_execution": (
                "Use market buy and sell orders on a new confirmed bar."
            ),
            "display_requirements": (
                "Display system name, signal, Balance, Equity, and Spread."
            ),
            "additional_notes": "Compile and backtest separately before use.",
        }
        record = self.bridge._ea_factory_normalize_record(
            compact_values,
            source_kind="verified_deep_research_sheet",
            source_key="sheet-restart-history",
        )
        self.assertIsInstance(record, dict)
        build_id = "ea-build-restart-history-revalidation"
        workspace = self.bridge._ea_factory_create_build_workspace(
            build_id,
            record,
            "mt4",
            "expert_advisor",
        )
        strategy_mission = {"id": "mission-restart-history-spec"}
        strategy_report = {"id": "report-restart-history-spec"}
        now = "2026-10-15T00:00:00Z"
        build = {
            "schemaVersion": "ea-factory-build-v1",
            "id": build_id,
            "sourceRecordId": record["sourceRecordId"],
            "sourceDisplayName": record["displayName"],
            "sourceRecordDigest": record["recordDigest"],
            "sourceReportId": strategy_report["id"],
            "sourceMissionId": strategy_mission["id"],
            "platform": "mt4",
            "artifactKind": "expert_advisor",
            "brief": "",
            "status": "ready",
            "workspace": workspace,
            "stages": self.bridge._ea_factory_initial_stages(
                "mt4",
                strategy_mission,
                strategy_report,
                "expert_advisor",
            ),
            "versions": [],
            "createIdempotencyKey": None,
            "createIdempotencyKeys": [],
            "createRequestDigest": self.bridge._ea_factory_create_request_digest(
                record["sourceRecordId"],
                "mt4",
                "",
                "expert_advisor",
            ),
            "createdAt": now,
            "updatedAt": now,
        }
        strategy_artifacts = self.bridge._ea_factory_register_artifacts(
            build,
            [{
                "relativePath": workspace["strategySpecFile"],
                "stageId": "strategy_spec",
                "reportId": strategy_report["id"],
                "artifactKind": "strategy_spec",
            }],
        )
        self.bridge._ea_factory_stage_row(build, "strategy_spec")["artifacts"] = [
            row["fileId"] for row in strategy_artifacts
        ]

        spec_path = (
            root
            / "workspace"
            / "ea-factory"
            / build_id
            / "Source"
            / "strategy-spec-v01.json"
        )
        spec = self.bridge.read_json(spec_path, None)
        source_text = f'''#property strict
#property description "EA_STRATEGY_BRIEF_SHA256:{spec["strategyBriefDigest"]}"
#define SIGNAL_NONE -1
input double FixedLot = 0.01;
input int MagicNumber = 4186001;
int OnInit() {{ return(INIT_SUCCEEDED); }}
int CountManagedPositions() {{
  int count = 0;
  for(int pos=OrdersTotal()-1; pos>=0; pos--) {{
    if(!OrderSelect(pos, SELECT_BY_POS, MODE_TRADES)) continue;
    if(OrderSymbol() == Symbol() && OrderMagicNumber() == MagicNumber) count++;
  }}
  return(count);
}}
bool CloseOpposite(const int signal) {{
  for(int pos=OrdersTotal()-1; pos>=0; pos--) {{
    if(!OrderSelect(pos, SELECT_BY_POS, MODE_TRADES)) continue;
    bool opposite = (signal == OP_BUY && OrderType() == OP_SELL)
                 || (signal == OP_SELL && OrderType() == OP_BUY);
    if(opposite && !OrderClose(OrderTicket(), OrderLots(),
                              OrderType() == OP_BUY ? Bid : Ask, 3)) return(false);
  }}
  return(true);
}}
void OnTick() {{
  static datetime lastBar = 0;
  datetime currentBar = Time[0];
  if(currentBar <= 0 || currentBar == lastBar) return;
  lastBar = currentBar;
  if(Bars < 3 || FixedLot <= 0.0) return;
  int signal = SIGNAL_NONE;
  if(Close[2] <= Open[2] && Close[1] > Open[1]) signal = OP_BUY;
  if(Close[2] >= Open[2] && Close[1] < Open[1]) signal = OP_SELL;
  Comment("Restart history EMA crossover signal=", signal,
          " Balance=", AccountBalance(), " Equity=", AccountEquity(),
          " Spread=", MarketInfo(Symbol(), MODE_SPREAD));
  if(signal == SIGNAL_NONE || !CloseOpposite(signal)) return;
  if(CountManagedPositions() >= 1) return;
  double entryPrice = signal == OP_BUY ? Ask : Bid;
  double stopLoss = signal == OP_BUY ? entryPrice - 100 * Point : entryPrice + 100 * Point;
  double takeProfit = signal == OP_BUY ? entryPrice + 200 * Point : entryPrice - 200 * Point;
  OrderSend(Symbol(), signal, FixedLot, entryPrice, 3, stopLoss, takeProfit,
            "Restart lineage", MagicNumber, 0);
}}
'''
        build_dir = root / "workspace" / "ea-factory" / build_id
        source_path = build_dir / "Source" / "RestartLineage.mq4"
        version_path = build_dir / "EA_Versions" / "RestartLineage_v01.mq4"
        source_path.write_text(source_text, encoding="utf-8", newline="\n")
        version_path.write_text(source_text, encoding="utf-8", newline="\n")
        source_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        coverage = self.bridge.build_compact_ea_source_manifest(
            source_text,
            strategy_brief=spec["strategyBrief"],
            strategy_brief_digest=spec["strategyBriefDigest"],
            strategy_spec_digest=workspace["strategySpecDigest"],
            source_digest=source_digest,
            target_platform="mt4",
        )
        self.assertTrue(coverage["complete"], coverage)
        generation_report_id = "report-restart-history-generation"
        build["versions"] = [{
            "version": 1,
            "fileName": version_path.name,
            "sourceDigest": source_digest,
            "sourceFile": "Source/RestartLineage.mq4",
            "versionFile": "EA_Versions/RestartLineage_v01.mq4",
            "sourceReportId": generation_report_id,
            "immutable": True,
            "createdAt": now,
        }]
        build["blueprintCoverageManifest"] = copy.deepcopy(coverage)
        source_artifacts = self.bridge._ea_factory_register_artifacts(
            build,
            [
                {
                    "relativePath": "Source/RestartLineage.mq4",
                    "stageId": "generate_source",
                    "reportId": generation_report_id,
                    "artifactKind": "generated_source",
                },
                {
                    "relativePath": "EA_Versions/RestartLineage_v01.mq4",
                    "stageId": "generate_source",
                    "reportId": generation_report_id,
                    "artifactKind": "immutable_version",
                },
            ],
        )
        generation_stage = self.bridge._ea_factory_stage_row(
            build,
            "generate_source",
        )
        generation_stage.update({
            "status": "completed",
            "missionId": "mission-restart-history-generation",
            "reportId": generation_report_id,
            "evidenceVerified": True,
            "artifacts": [row["fileId"] for row in source_artifacts],
            "blueprintCoverageManifest": copy.deepcopy(coverage),
        })
        self.bridge._ea_factory_stage_row(build, "source_review").update({
            "status": "completed",
            "missionId": "mission-restart-history-review",
            "reportId": "report-restart-history-review",
            "evidenceVerified": True,
        })

        original_run = {
            "schemaVersion": self.bridge.EA_FACTORY_ONE_CLICK_SCHEMA_VERSION,
            "runId": "ea-run-restart-history-original",
            "idempotencyKey": "restart-history-original-0001",
            "requestDigest": self.bridge._ea_factory_one_click_request_digest(build),
            "status": "failed",
            "currentStageId": "backtest_recheck",
            "terminalBinding": {
                "platform": "mt4",
                "candidateId": "mtc-restart-history-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "failureCode": "visible_backtest_failed",
            "messageTh": "รอบเดิมหยุดก่อน Backtest สำเร็จ",
            "startedAt": now,
            "updatedAt": now,
            "completedAt": now,
        }
        build["oneClickRun"] = original_run
        operation_id = self.bridge._ea_factory_one_click_visible_operation_id(
            build,
            original_run,
            "compile_validate",
        )
        binary_path = build_dir / "EA_Versions" / "RestartLineage_v01.ex4"
        binary_path.write_bytes(b"compiled restart history fixture")
        binary_digest = hashlib.sha256(binary_path.read_bytes()).hexdigest()
        screenshot_path = build_dir / "Screenshots" / "compile-restart.png"
        screenshot_path.write_bytes(b"\x89PNG\r\n\x1a\nrestart history")
        log_path = build_dir / "Reports" / "compile-restart.txt"
        result_line = "Result: 0 errors, 0 warnings"
        log_path.write_text(
            f"{result_line}\n{source_digest}\n{binary_digest}\n",
            encoding="utf-8",
        )
        receipt_path = build_dir / "Reports" / "compile-restart.json"
        receipt_path.write_text("{}\n", encoding="utf-8")
        compile_report_id = "report-restart-history-compile"
        compile_artifacts = self.bridge._ea_factory_register_artifacts(
            build,
            [
                {
                    "relativePath": "EA_Versions/RestartLineage_v01.ex4",
                    "stageId": "compile_validate",
                    "reportId": compile_report_id,
                    "artifactKind": "compile_evidence",
                },
                {
                    "relativePath": "Screenshots/compile-restart.png",
                    "stageId": "compile_validate",
                    "reportId": compile_report_id,
                    "artifactKind": "screenshot_evidence",
                },
                {
                    "relativePath": "Reports/compile-restart.txt",
                    "stageId": "compile_validate",
                    "reportId": compile_report_id,
                    "artifactKind": "compile_evidence",
                },
                {
                    "relativePath": "Reports/compile-restart.json",
                    "stageId": "compile_validate",
                    "reportId": compile_report_id,
                    "artifactKind": "compile_evidence",
                },
            ],
        )
        by_path = {
            row["relativePath"]: row for row in compile_artifacts
        }
        process_binding = {
            "schemaVersion": "ea-factory-front-office-process-binding-v1",
            "observedAt": now,
            "stageId": "compile_validate",
            "terminalCandidateId": "mtc-restart-history-terminal",
            "terminalSelectionRevision": 7,
            "terminalBindingDigest": "c" * 64,
            "terminalProcessId": 123,
            "terminalExecutableSha256": "4" * 64,
            "terminalWindowHandle": 456,
            "terminalWindowOwnerProcessId": 123,
            "terminalWindowTitleSha256": "5" * 64,
            "terminalWindowClassSha256": "6" * 64,
            "frontOfficeKind": "metaeditor",
            "frontOfficeProcessId": 124,
            "frontOfficeExecutableSha256": "7" * 64,
            "frontOfficeWindowHandle": 457,
            "frontOfficeWindowOwnerProcessId": 124,
            "frontOfficeWindowTitleSha256": "8" * 64,
            "frontOfficeWindowClassSha256": "9" * 64,
            "processBindingDigest": "",
        }
        process_binding["processBindingDigest"] = (
            self.bridge._ea_factory_front_office_process_binding_digest(
                process_binding
            )
        )
        stage_manifest_digest = (
            self.bridge._ea_factory_visible_stage_manifest_digest(
                compile_artifacts
            )
        )
        metrics = {
            "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "operationId": operation_id,
            "eaFactoryStage": "compile_validate",
            "platform": "mt4",
            "terminalCandidateId": "mtc-restart-history-terminal",
            "terminalSelectionRevision": 7,
            "terminalBindingDigest": "c" * 64,
            "processBinding": copy.deepcopy(process_binding),
            "processBindingDigest": process_binding["processBindingDigest"],
            "postProcessBinding": copy.deepcopy(process_binding),
            "postProcessBindingDigest": process_binding["processBindingDigest"],
            "capabilityCheckedAt": now,
            "liveTradingExecuted": False,
            "autoTradingToggled": False,
            "autoTradingStateBefore": True,
            "autoTradingStateAfter": True,
            "chartAttached": False,
            "terminalClosedByAdapter": False,
            "terminalStillRunning": True,
            "terminalStillOpen": True,
            "processId": 124,
            "windowHandle": 457,
            "evidenceArtifactIds": [
                row["fileId"] for row in compile_artifacts
            ],
            "stageArtifactManifestDigest": stage_manifest_digest,
            "sourceDigest": source_digest,
            "compiledBinaryFileId": by_path[
                "EA_Versions/RestartLineage_v01.ex4"
            ]["fileId"],
            "compiledBinarySha256": binary_digest,
            "visibleWindowEvidenceFileId": by_path[
                "Screenshots/compile-restart.png"
            ]["fileId"],
            "visibleWindowEvidenceSha256": by_path[
                "Screenshots/compile-restart.png"
            ]["sha256"],
            "compileLogFileId": by_path["Reports/compile-restart.txt"][
                "fileId"
            ],
            "compileLogSha256": by_path["Reports/compile-restart.txt"][
                "sha256"
            ],
            "adapterReceiptFileId": by_path[
                "Reports/compile-restart.json"
            ]["fileId"],
            "adapterReceiptSha256": by_path[
                "Reports/compile-restart.json"
            ]["sha256"],
            "resultLine": result_line,
            "visibleMetaEditor": True,
            "compileVerified": True,
            "compileExecuted": True,
            "recoveredExistingReceipt": False,
            "zeroErrors": True,
            "zeroWarnings": True,
            "backtestExecuted": False,
        }
        compile_stage = self.bridge._ea_factory_stage_row(
            build,
            "compile_validate",
        )
        compile_stage.update({
            "status": "completed",
            "missionId": "mission-restart-history-compile",
            "reportId": compile_report_id,
            "evidenceVerified": True,
            "artifacts": [row["fileId"] for row in compile_artifacts],
            "visibleEvidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "visibleOperationId": operation_id,
            "visibleEvidenceDigest": stage_manifest_digest,
            "terminalExecutableSha256": "4" * 64,
            "frontOfficeExecutableSha256": "7" * 64,
        })
        compile_report = {
            "id": compile_report_id,
            "status": "ready",
            "linkedMissionId": compile_stage["missionId"],
            "metrics": metrics,
        }
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / f"{compile_report_id}.json").write_text(
            json.dumps(compile_report),
            encoding="utf-8",
        )
        return build, compile_stage, compile_report

    def compact_ea_manifest(self, source_digest: str = "d" * 64) -> dict:
        manifest = {
            "schemaVersion": self.bridge.EA_SOURCE_MANIFEST_SCHEMA_VERSION,
            "coverageMode": "compact_brief_digest_bound_structural_ea_review",
            "artifactKind": "expert_advisor",
            "targetPlatform": "mt4",
            "strategyBriefDigest": "1" * 64,
            "strategySpecDigest": "2" * 64,
            "sourceDigest": source_digest,
            "checks": {"completeStaticSourceContract": True},
            "coveredFields": list(self.bridge.COMPACT_SHEET_FIELDS),
            "missingFields": [],
            "findings": [],
            "complete": True,
        }
        manifest["manifestDigest"] = hashlib.sha256(json.dumps(
            manifest,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        return manifest

    def target(self) -> tuple[dict, dict]:
        return (
            {
                "record": {"runningState": "platform_running_detected"},
                "token": {},
            },
            {
                "platform": "mt4",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
        )

    def test_can_slim_tester_preset_requires_certified_v2_source_profile(self) -> None:
        build = self.build()
        with tempfile.TemporaryDirectory() as temporary:
            build_root = Path(temporary)
            versions = build_root / "EA_Versions"
            versions.mkdir()
            source_path = versions / "CAN_SLIM.mq4"
            source_text = (
                'const string CERTIFIED_PROFILE_VERSION = "can-slim-mt4-certified-v3";\n'
                "input double InpStopLossPercent = 7.5;\n"
                "input double RewardRiskRatio = 2;\n"
                "input double RiskPercent = 1;\n"
                "input int ExecutionBufferPoints = 2;\n"
                "input int SlippagePoints = 3;\n"
                "input int MaxOpenPositionsPerSymbolMagic = 1;\n"
                "input int MagicNumber = 4186001;\n"
                "input int DailyMAPeriod = 50;\n"
                "input int WeeklyMAPeriod = 50;\n"
                "input int FiftyTwoWeekLookback = 52;\n"
                "input bool FundamentalCriteriaConfirmed = false;\n"
                "input bool ExternalBenchmarkUptrendConfirmed = false;\n"
                "input int MaxSpreadPoints = 30;\n"
                "void OnTick(){\n"
                "  if(!FundamentalCriteriaConfirmed) return;\n"
                "  if(!ExternalBenchmarkUptrendConfirmed) return;\n"
                "}\n"
            )
            source_path.write_text(source_text, encoding="utf-8")
            build["versions"] = [{
                "sourceDigest": hashlib.sha256(source_path.read_bytes()).hexdigest(),
                "versionFile": "EA_Versions/CAN_SLIM.mq4",
            }]
            with mock.patch.object(
                self.bridge,
                "_ea_factory_build_directory",
                return_value=build_root,
            ):
                preset = self.bridge._ea_factory_can_slim_tester_input_preset(build)
                self.assertIsInstance(preset, dict)
                self.assertEqual(preset["scope"], "mt4_strategy_tester_only")
                self.assertTrue(preset["liveSourceDefaultsPreserved"])
                self.assertFalse(preset["liveTradingAllowed"])
                self.assertTrue(preset["fullCertifiedInputSnapshot"])
                self.assertEqual(len(preset["assumptions"]), 13)
                self.assertEqual(
                    [
                        item["testerValue"]
                        for item in preset["assumptions"]
                        if item["inputName"]
                        in self.bridge.EA_FACTORY_CAN_SLIM_SIMULATION_INPUT_NAMES
                    ],
                    [True, True],
                )
                self.assertEqual(
                    next(
                        item["testerValue"]
                        for item in preset["assumptions"]
                        if item["inputName"] == "MaxSpreadPoints"
                    ),
                    30,
                )

                spoofed_text = source_text.replace(
                    "  if(!ExternalBenchmarkUptrendConfirmed) return;\n",
                    "",
                )
                source_path.write_text(spoofed_text, encoding="utf-8")
                build["versions"][-1]["sourceDigest"] = hashlib.sha256(
                    source_path.read_bytes()
                ).hexdigest()
                self.assertIsNone(
                    self.bridge._ea_factory_can_slim_tester_input_preset(build)
                )

                comment_spoof_text = source_text.replace(
                    "  if(!ExternalBenchmarkUptrendConfirmed) return;\n",
                    "  // if(!ExternalBenchmarkUptrendConfirmed) return;\n",
                )
                source_path.write_text(comment_spoof_text, encoding="utf-8")
                build["versions"][-1]["sourceDigest"] = hashlib.sha256(
                    source_path.read_bytes()
                ).hexdigest()
                self.assertIsNone(
                    self.bridge._ea_factory_can_slim_tester_input_preset(build)
                )

                legacy_text = source_text.replace(
                    "can-slim-mt4-certified-v3",
                    "can-slim-mt4-certified-v1",
                )
                source_path.write_text(legacy_text, encoding="utf-8")
                build["versions"][-1]["sourceDigest"] = hashlib.sha256(
                    source_path.read_bytes()
                ).hexdigest()
                self.assertIsNone(
                    self.bridge._ea_factory_can_slim_tester_input_preset(build)
                )

    def test_generic_mt4_tester_preset_resets_every_input_and_simulates_only_proven_external_gate(self) -> None:
        build = self.build()
        with tempfile.TemporaryDirectory() as temporary:
            build_root = Path(temporary)
            versions = build_root / "EA_Versions"
            versions.mkdir()
            source_path = versions / "EMA_CROSS.mq4"
            source_text = (
                "input int FastPeriod = 10;\n"
                "input int SlowPeriod = 60;\n"
                "input double FixedLot = 0.01;\n"
                "input bool TradeOnNewBar = true;\n"
                "input bool EligibilityConfirmed = false;\n"
                "input bool EnableTrading = false;\n"
                "input bool ExternalLiveTradingEnabled = false;\n"
                "void OnTick(){\n"
                "  if(!EligibilityConfirmed) return;\n"
                "  if(!ExternalLiveTradingEnabled) return;\n"
                "}\n"
            )
            source_path.write_text(source_text, encoding="utf-8")
            build["versions"] = [{
                "sourceDigest": hashlib.sha256(source_path.read_bytes()).hexdigest(),
                "versionFile": "EA_Versions/EMA_CROSS.mq4",
            }]
            with mock.patch.object(
                self.bridge,
                "_ea_factory_build_directory",
                return_value=build_root,
            ):
                preset = self.bridge._ea_factory_mt4_tester_input_preset(build)
                self.assertEqual(len(preset["assumptions"]), 7)
                self.assertEqual(
                    preset["simulationInputNames"],
                    ["EligibilityConfirmed"],
                )
                by_name = {
                    item["inputName"]: item for item in preset["assumptions"]
                }
                self.assertEqual(by_name["FastPeriod"]["testerValue"], 10)
                self.assertEqual(by_name["FixedLot"]["testerValue"], 0.01)
                self.assertTrue(by_name["TradeOnNewBar"]["testerValue"])
                self.assertTrue(by_name["EligibilityConfirmed"]["testerValue"])
                self.assertFalse(by_name["EnableTrading"]["testerValue"])
                self.assertFalse(
                    by_name["ExternalLiveTradingEnabled"]["testerValue"]
                )
                self.assertRegex(preset["presetDigest"], r"^[0-9a-f]{64}$")

                source_path.write_text(
                    'input string Label = "unsupported";\nvoid OnTick(){}\n',
                    encoding="utf-8",
                )
                build["versions"][-1]["sourceDigest"] = hashlib.sha256(
                    source_path.read_bytes()
                ).hexdigest()
                with self.assertRaises(self.bridge.RequestError) as blocked:
                    self.bridge._ea_factory_mt4_tester_input_preset(build)
                self.assertEqual(blocked.exception.status, 409)

                source_path.write_text("void OnTick(){}\n", encoding="utf-8")
                build["versions"][-1]["sourceDigest"] = hashlib.sha256(
                    source_path.read_bytes()
                ).hexdigest()
                self.assertIsNone(
                    self.bridge._ea_factory_mt4_tester_input_preset(build)
                )

    def test_backtest_capability_requires_trade_row_evidence_not_logic_claim(self) -> None:
        capability = {
            "ready": True,
            "freshProcessProbe": True,
            "foregroundInteraction": True,
            "visibleEvidenceCapture": True,
            "terminalSelectionBound": True,
            "liveTradingAllowed": False,
            "terminalProcessMayRemainOpen": True,
            "processAndWindowBinding": True,
            "idempotentOperationBinding": True,
            "durableReceiptRecovery": True,
            "terminalShutdownAllowed": False,
            "autoTradingMayBeToggled": False,
            "chartAttachmentAllowed": False,
            "visibleStrategyTester": True,
            "visualModeRequired": True,
            "logicRecheckEvidence": True,
        }
        self.assertFalse(
            self.bridge._ea_factory_front_office_capability_ready(
                capability,
                "backtest_recheck",
            )
        )
        capability["testerTradeRowsEvidence"] = True
        self.assertTrue(
            self.bridge._ea_factory_front_office_capability_ready(
                capability,
                "backtest_recheck",
            )
        )

    def test_start_pins_terminal_and_dispatches_one_worker(self) -> None:
        build = self.build()
        state = self.state(build)
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write_state,
            mock.patch.object(self.bridge, "_ea_factory_metaeditor_target_context", return_value=self.target()),
            mock.patch.object(self.bridge, "_start_ea_factory_one_click_thread", return_value=True) as start,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            result = self.bridge.run_ea_factory_build_one_click(
                build["id"],
                {"idempotencyKey": "one-click-ui-001"},
            )
        self.assertEqual(result["kind"], "ea_factory_one_click_started")
        self.assertTrue(result["workerStarted"])
        self.assertEqual(result["oneClickRun"]["status"], "queued")
        self.assertFalse(result["oneClickRun"]["liveTradingAllowed"])
        self.assertTrue(result["oneClickRun"]["visualModeRequired"])
        binding = build["oneClickRun"]["terminalBinding"]
        self.assertEqual(binding["candidateId"], "mtc-one-click-terminal")
        self.assertEqual(binding["selectionRevision"], 7)
        self.assertEqual(binding["bindingDigest"], "c" * 64)
        write_state.assert_called_once()
        start.assert_called_once()
        self.assertEqual(start.call_args.args, (build["id"],))
        self.assertEqual(
            start.call_args.kwargs["expected_run_snapshot"]["runId"],
            build["oneClickRun"]["runId"],
        )
        validated = self.bridge._ea_factory_revalidated_one_click_run(build)
        self.assertEqual(validated["currentStageId"], "generate_source")

    def test_fresh_build_starts_after_atomic_strategy_spec(self) -> None:
        build = self.build()
        self.assertEqual(
            self.bridge._ea_factory_build_current_stage_id(build),
            "generate_source",
        )
        self.assertEqual(build["stages"][0]["id"], "strategy_spec")
        self.assertEqual(build["stages"][0]["status"], "completed")

    def test_same_key_resumes_visible_pause_but_different_key_is_rejected(self) -> None:
        build = self.build()
        now = "2026-09-11T00:00:00Z"
        build["oneClickRun"] = {
            "schemaVersion": self.bridge.EA_FACTORY_ONE_CLICK_SCHEMA_VERSION,
            "runId": "ea-run-one-click-test",
            "idempotencyKey": "one-click-ui-001",
            "requestDigest": self.bridge._ea_factory_one_click_request_digest(build),
            "status": "awaiting_visible_terminal",
            "currentStageId": "compile_validate",
            "terminalBinding": {
                "platform": "mt4",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "failureCode": None,
            "messageTh": "waiting",
            "startedAt": now,
            "updatedAt": now,
            "completedAt": None,
        }
        state = self.state(build)
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
            mock.patch.object(self.bridge, "_start_ea_factory_one_click_thread", return_value=True),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            resumed = self.bridge.run_ea_factory_build_one_click(
                build["id"],
                {"idempotencyKey": "one-click-ui-001"},
            )
            with self.assertRaises(self.bridge.RequestError) as error:
                self.bridge.run_ea_factory_build_one_click(
                    build["id"],
                    {"idempotencyKey": "another-owner"},
                )
        self.assertEqual(resumed["kind"], "ea_factory_one_click_resumed")
        self.assertEqual(build["oneClickRun"]["status"], "queued")
        self.assertEqual(error.exception.status, 409)

    def test_same_key_resumes_after_backend_heals_rejected_stage_evidence(self) -> None:
        build = self.build()
        for stage in build["stages"]:
            if stage["id"] == "generate_source":
                stage.update({
                    "status": "completed",
                    "missionId": f"mission-{stage['id']}",
                    "reportId": f"report-{stage['id']}",
                    "blockedReasonCode": None,
                    "evidenceVerified": True,
                })
            elif stage["id"] == "source_review":
                stage.update({
                    "status": "blocked",
                    "missionId": "mission-source_review",
                    "reportId": None,
                    "blockedReasonCode": "source_review_evidence_invalid",
                    "evidenceVerified": False,
                })
        now = "2026-09-11T00:00:00Z"
        build["oneClickRun"] = {
            "schemaVersion": self.bridge.EA_FACTORY_ONE_CLICK_SCHEMA_VERSION,
            "runId": "ea-run-one-click-healed-evidence",
            "idempotencyKey": "one-click-ui-healed-001",
            "requestDigest": self.bridge._ea_factory_one_click_request_digest(build),
            "status": "blocked",
            "currentStageId": "source_review",
            "terminalBinding": {
                "platform": "mt4",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "failureCode": "source_review_evidence_invalid",
            "messageTh": "blocked by older validator",
            "startedAt": now,
            "updatedAt": now,
            "completedAt": now,
        }
        state = self.state(build)

        def heal_review(candidate, **_kwargs):
            review = next(
                row for row in candidate["stages"] if row["id"] == "source_review"
            )
            review.update({
                "status": "completed",
                "reportId": "report-source_review",
                "blockedReasonCode": None,
                "evidenceVerified": True,
            })
            candidate["status"] = "ready"
            return True

        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(
                self.bridge,
                "_ea_factory_sync_build_status",
                side_effect=heal_review,
            ) as sync_status,
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write_state,
            mock.patch.object(self.bridge, "_start_ea_factory_one_click_thread", return_value=True) as start,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            resumed = self.bridge.run_ea_factory_build_one_click(
                build["id"],
                {"idempotencyKey": "one-click-ui-healed-001"},
            )
        self.assertEqual(resumed["kind"], "ea_factory_one_click_resumed")
        self.assertTrue(resumed["workerStarted"])
        self.assertEqual(build["oneClickRun"]["status"], "queued")
        self.assertEqual(build["oneClickRun"]["currentStageId"], "compile_validate")
        self.assertIsNone(build["oneClickRun"]["failureCode"])
        self.assertIsNone(build["oneClickRun"]["completedAt"])
        write_state.assert_called_once()
        start.assert_called_once()
        self.assertEqual(start.call_args.args, (build["id"],))
        self.assertEqual(
            start.call_args.kwargs["expected_run_snapshot"]["runId"],
            build["oneClickRun"]["runId"],
        )
        sync_status.assert_called_once_with(build, ingest_sources=True)

        uncertain = copy.deepcopy(build)
        uncertain["oneClickRun"].update({
            "status": "blocked",
            "currentStageId": "source_review",
            "failureCode": "source_review_evidence_invalid",
            "visibleAction": {
                "stageId": "compile_validate",
                "operationId": "ea-visible-uncertain",
                "state": "uncertain",
            },
        })
        uncertain_state = self.state(uncertain)
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=uncertain_state),
            mock.patch.object(
                self.bridge,
                "_ea_factory_sync_build_status",
                side_effect=heal_review,
            ),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as uncertain_write,
            mock.patch.object(self.bridge, "_start_ea_factory_one_click_thread") as uncertain_start,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            replayed = self.bridge.run_ea_factory_build_one_click(
                uncertain["id"],
                {"idempotencyKey": "one-click-ui-healed-001"},
            )
        self.assertEqual(replayed["kind"], "ea_factory_one_click_replayed")
        self.assertFalse(replayed["workerStarted"])
        uncertain_write.assert_called_once()
        uncertain_start.assert_not_called()

    def _legacy_same_key_resumes_revalidated_mt5_handoff_without_stage_replay(self) -> None:
        build = self.build()
        build["platform"] = "mt5"
        build["status"] = "completed"
        for stage in build["stages"]:
            stage.update({
                "status": "completed",
                "missionId": stage.get("missionId") or f"mission-{stage['id']}",
                "reportId": stage.get("reportId") or f"report-{stage['id']}",
                "blockedReasonCode": None,
                "evidenceVerified": True,
            })
        now = "2026-10-15T13:54:39Z"
        build["oneClickRun"] = {
            "schemaVersion": self.bridge.EA_FACTORY_ONE_CLICK_SCHEMA_VERSION,
            "runId": "ea-run-repaired-mt5-handoff",
            "idempotencyKey": "one-click-repaired-handoff-001",
            "requestDigest": self.bridge._ea_factory_one_click_request_digest(build),
            "status": "failed",
            "currentStageId": None,
            "terminalBinding": {
                "platform": "mt5",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "failureCode": "verified_baseline_settings_required",
            "messageTh": "older verifier rejected a valid baseline",
            "startedAt": now,
            "updatedAt": now,
            "completedAt": now,
        }
        original_run_id = build["oneClickRun"]["runId"]
        original_stages = copy.deepcopy(build["stages"])
        state = self.state(build)
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_sync_build_status",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_repaired_optimization_handoff_available",
                return_value=True,
            ) as revalidate,
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ) as write_state,
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_one_click_thread",
                return_value=True,
            ) as start,
            mock.patch.object(self.bridge, "advance_ea_factory_build") as advance,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            resumed = self.bridge.run_ea_factory_build_one_click(
                build["id"],
                {"idempotencyKey": "one-click-repaired-handoff-001"},
            )

        self.assertEqual(resumed["kind"], "ea_factory_one_click_resumed")
        self.assertTrue(resumed["workerStarted"])
        self.assertEqual(build["oneClickRun"]["runId"], original_run_id)
        self.assertEqual(build["oneClickRun"]["status"], "queued")
        self.assertIsNone(build["oneClickRun"]["currentStageId"])
        self.assertIsNone(build["oneClickRun"]["failureCode"])
        self.assertIsNone(build["oneClickRun"]["completedAt"])
        self.assertEqual(build["stages"], original_stages)
        revalidate.assert_called_once_with(build, mock.ANY)
        write_state.assert_called_once()
        start.assert_called_once()
        advance.assert_not_called()

        failed_build = copy.deepcopy(build)
        failed_build["oneClickRun"].update({
            "status": "failed",
            "failureCode": "verified_baseline_settings_required",
            "completedAt": now,
        })
        failed_state = self.state(failed_build)
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=failed_state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_sync_build_status",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_repaired_optimization_handoff_available",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_one_click_thread",
            ) as blocked_start,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            replayed = self.bridge.run_ea_factory_build_one_click(
                failed_build["id"],
                {"idempotencyKey": "one-click-repaired-handoff-001"},
            )
        self.assertEqual(replayed["kind"], "ea_factory_one_click_replayed")
        self.assertFalse(replayed["workerStarted"])
        blocked_start.assert_not_called()

    def _legacy_repaired_mt5_handoff_read_model_requires_full_revalidation(self) -> None:
        build = self.build()
        build["platform"] = "mt5"
        build["status"] = "completed"
        for stage in build["stages"]:
            stage.update({"status": "completed", "evidenceVerified": True})
        now = "2026-10-15T13:54:39Z"
        run = {
            "status": "failed",
            "currentStageId": None,
            "failureCode": "verified_baseline_settings_required",
            "terminalBinding": {
                "platform": "mt5",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "completedAt": now,
        }
        backtest_stage = next(
            stage for stage in build["stages"] if stage["id"] == "backtest_recheck"
        )
        backtest_stage["visibleOperationId"] = "ea-visible-repaired-handoff"
        run["visibleAction"] = {
            "stageId": "backtest_recheck",
            "operationId": "ea-visible-repaired-handoff",
            "state": "completed",
            "attemptCount": 3,
        }
        build["oneClickRun"] = run
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_terminal_binding_current",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_build_context",
                return_value={"build": {"id": build["id"]}},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_mt5_optimization_input_manifest",
                return_value={"entries": [{"inputName": "SafeRange"}]},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_source_bound_auto_optimization_ranges",
                return_value=[{
                    "name": "SafeRange",
                    "kind": "numeric",
                    "start": "1",
                    "step": "1",
                    "stop": "2",
                }],
            ),
        ):
            self.assertTrue(
                self.bridge._ea_factory_one_click_repaired_optimization_handoff_available(
                    build,
                    run,
                )
            )
            run["failureCode"] = "source_bound_optimization_ranges_unavailable"
            self.assertTrue(
                self.bridge._ea_factory_one_click_repaired_optimization_handoff_available(
                    build,
                    run,
                )
            )
            run["failureCode"] = "verified_baseline_settings_required"
        run["visibleAction"]["state"] = "uncertain"
        with mock.patch.object(
            self.bridge,
            "_ea_factory_optimization_build_context",
        ) as context:
            self.assertFalse(
                self.bridge._ea_factory_one_click_repaired_optimization_handoff_available(
                    build,
                    run,
                )
            )
        context.assert_not_called()
        run["visibleAction"]["state"] = "completed"
        run["visibleAction"]["operationId"] = "ea-visible-wrong-operation"
        with mock.patch.object(
            self.bridge,
            "_ea_factory_optimization_build_context",
        ) as context:
            self.assertFalse(
                self.bridge._ea_factory_one_click_repaired_optimization_handoff_available(
                    build,
                    run,
                )
            )
        context.assert_not_called()
        run["visibleAction"]["operationId"] = "ea-visible-repaired-handoff"
        run["failureCode"] = "immutable_source_invalid"
        with mock.patch.object(
            self.bridge,
            "_ea_factory_optimization_build_context",
        ) as context:
            self.assertFalse(
                self.bridge._ea_factory_one_click_repaired_optimization_handoff_available(
                    build,
                    run,
                )
            )
        context.assert_not_called()

    def test_mt5_factory_completes_at_final_report_without_optimizer_handoff(self) -> None:
        build = self.build()
        build["platform"] = "mt5"
        build["status"] = "completed"
        for stage in build["stages"]:
            stage.update({
                "status": "completed",
                "evidenceVerified": True,
                "missionId": stage.get("missionId") or f"mission-{stage['id']}",
                "reportId": stage.get("reportId") or f"report-{stage['id']}",
            })
        build["oneClickRun"] = self._run(build, current_stage=None)
        build["oneClickRun"]["status"] = "running"
        state = self.state(build)
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_sync_build_status",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ) as write_state,
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_ea_factory_report_rows_snapshot",
                return_value=[],
            ),
        ):
            action = self.bridge._ea_factory_one_click_next_action(build["id"])

        self.assertEqual(action["kind"], "completed")
        self.assertEqual(build["oneClickRun"]["status"], "completed")
        self.assertEqual(
            build["oneClickRun"]["completionBoundary"],
            "final_report",
        )
        self.assertFalse(build["oneClickRun"]["optimizationIncluded"])
        self.assertNotIn("optimizationHandoff", build["oneClickRun"])
        write_state.assert_called_once()

    def test_factory_read_model_drops_legacy_optimizer_fields(self) -> None:
        build = self.build()
        build["platform"] = "mt5"
        build["status"] = "completed"
        for stage in build["stages"]:
            stage.update({"status": "completed", "evidenceVerified": True})
        build["oneClickRun"] = self._run(build, current_stage=None)
        build["oneClickRun"].update({
            "status": "completed",
            "optimizationProgressPercent": 75,
            "optimizationHandoff": {
                "sessionId": "legacy-optimization-session",
                "state": "failed",
            },
        })

        model = self.bridge._ea_factory_one_click_read_model(build)

        self.assertEqual(model["status"], "completed")
        self.assertEqual(model["completionBoundary"], "final_report")
        self.assertFalse(model["optimizationIncluded"])
        self.assertNotIn("optimizationHandoff", model)
        self.assertNotIn("optimizationProgressPercent", model)
        self.assertFalse(model["canResume"])
        self.assertIsNone(model["resumeKind"])
        self.assertEqual(model["progressPercent"], 100)

    def test_coordinator_advances_only_next_pending_stage(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="generate_source")
        state = self.state(build)
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status", return_value=False),
        ):
            action = self.bridge._ea_factory_one_click_next_action(build["id"])
        self.assertEqual(action["kind"], "advance")
        self.assertEqual(action["stageId"], "generate_source")
        self.assertEqual(build["oneClickRun"]["status"], "running")

    def test_terminal_stage_pauses_without_visible_adapter_and_does_not_mutate_stage(self) -> None:
        build = self.build()
        for stage in build["stages"]:
            if stage["id"] in {"generate_source", "source_review"}:
                stage["status"] = "completed"
                stage["evidenceVerified"] = True
        compile_stage = next(row for row in build["stages"] if row["id"] == "compile_validate")
        build["oneClickRun"] = self._run(build, current_stage="compile_validate")
        state = self.state(build)
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status", return_value=False),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_visible_gate",
                return_value={"ready": False, "reasonCode": "visible_terminal_adapter_not_connected"},
            ),
        ):
            action = self.bridge._ea_factory_one_click_next_action(build["id"])
        self.assertEqual(action["kind"], "awaiting_visible_terminal")
        self.assertEqual(build["oneClickRun"]["status"], "awaiting_visible_terminal")
        self.assertEqual(compile_stage["status"], "pending")
        self.assertIsNone(compile_stage["missionId"])
        self.assertFalse(compile_stage["evidenceVerified"])

    def test_visible_gate_rejects_old_hidden_compile_adapter(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="compile_validate")
        with (
            mock.patch.object(self.bridge, "_ea_factory_one_click_terminal_binding_current", return_value=True),
            mock.patch.object(self.bridge, "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER", None),
            mock.patch.object(self.bridge, "EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER", None),
        ):
            gate = self.bridge._ea_factory_one_click_visible_gate(build, "compile_validate")
        self.assertFalse(gate["ready"])
        self.assertEqual(gate["reasonCode"], "visible_terminal_adapter_not_connected")

    def test_adapter_platform_support_is_explicit_and_fail_closed(self) -> None:
        class Mt4OnlyAdapter:
            supported_platforms = frozenset({"mt4"})

            def capability_provider(self, **_kwargs):
                return {}

        adapter = Mt4OnlyAdapter()
        with mock.patch.object(
            self.bridge,
            "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
            adapter.capability_provider,
        ):
            self.assertEqual(
                self.bridge._ea_factory_front_office_supported_platforms(),
                frozenset({"mt4"}),
            )
        with mock.patch.object(
            self.bridge,
            "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
            lambda **_kwargs: {},
        ):
            self.assertEqual(
                self.bridge._ea_factory_front_office_supported_platforms(),
                frozenset(),
            )

        class OverclaimingAdapter:
            supported_platforms = frozenset({"mt4", "mt5"})

            def capability_provider(self, **_kwargs):
                return {}

        overclaiming = OverclaimingAdapter()
        with mock.patch.object(
            self.bridge,
            "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
            overclaiming.capability_provider,
        ):
            self.assertEqual(
                self.bridge._ea_factory_front_office_supported_platforms(),
                frozenset({"mt4", "mt5"}),
            )

    def test_mt5_one_click_reserves_exact_running_terminal_and_worker(self) -> None:
        build = self.build()
        build["platform"] = "mt5"
        state = self.state(build)
        context, target = self.target()
        context["record"]["platform"] = "mt5"
        target["platform"] = "mt5"
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_metaeditor_target_context",
                return_value=(context, target),
            ) as resolve_target,
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_one_click_thread",
                return_value=True,
            ) as start,
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            result = self.bridge.run_ea_factory_build_one_click(
                build["id"],
                {"idempotencyKey": "one-click-ui-001"},
            )
        self.assertEqual(result["kind"], "ea_factory_one_click_started")
        self.assertTrue(result["workerStarted"])
        self.assertEqual(build["oneClickRun"]["terminalBinding"]["platform"], "mt5")
        resolve_target.assert_called_once_with("mt5")
        start.assert_called_once()
        write.assert_called_once()

    def test_mt4_one_click_requires_terminal_process_already_running(self) -> None:
        build = self.build()
        state = self.state(build)
        stopped_context, target = self.target()
        stopped_context["record"]["runningState"] = "not_running_detected"
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_metaeditor_target_context",
                return_value=(stopped_context, target),
            ),
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_one_click_thread",
            ) as start,
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write,
        ):
            with self.assertRaises(self.bridge.RequestError) as error:
                self.bridge.run_ea_factory_build_one_click(
                    build["id"],
                    {"idempotencyKey": "one-click-ui-001"},
                )
        self.assertEqual(error.exception.status, 409)
        self.assertIn("must already be running", str(error.exception))
        start.assert_not_called()
        write.assert_not_called()
        self.assertNotIn("oneClickRun", build)

    def test_persisted_mt5_one_click_advances_through_same_phase_gate(self) -> None:
        build = self.build()
        build["platform"] = "mt5"
        build["oneClickRun"] = self._run(build, current_stage="generate_source")
        build["oneClickRun"]["terminalBinding"]["platform"] = "mt5"
        state = self.state(build)
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ) as write,
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status") as sync,
        ):
            action = self.bridge._ea_factory_one_click_next_action(build["id"])
        self.assertEqual(action["kind"], "advance")
        self.assertEqual(action["stageId"], "generate_source")
        self.assertNotEqual(build["oneClickRun"]["status"], "blocked")
        sync.assert_called_once()
        write.assert_called_once()

    def test_source_invalid_output_uses_existing_bounded_retry_path(self) -> None:
        build = self.build()
        source = next(row for row in build["stages"] if row["id"] == "generate_source")
        source.update({
            "status": "blocked",
            "blockedReasonCode": "invalid_output",
            "missionId": "mission-source-failed",
            "manualRetryCount": 1,
            "manualRetryHistory": [{"attempt": 1}],
        })
        build["oneClickRun"] = self._run(build, current_stage="generate_source")
        state = self.state(build)
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status", return_value=False),
        ):
            action = self.bridge._ea_factory_one_click_next_action(build["id"])
        self.assertEqual(action["kind"], "retry_source")
        self.assertEqual(action["failedMissionId"], "mission-source-failed")
        self.assertEqual(action["attempt"], 2)

    def test_same_run_key_restarts_stale_running_source_retry_coordinator(self) -> None:
        build = self.build()
        build["platform"] = "mt5"
        build["status"] = "attention_required"
        source = next(
            row for row in build["stages"] if row["id"] == "generate_source"
        )
        source.update({
            "status": "failed",
            "blockedReasonCode": "invalid_output",
            "missionId": "mission-source-invalid-output",
            "manualRetryCount": 0,
            "manualRetryHistory": [],
        })
        build["oneClickRun"] = self._run(
            build,
            current_stage="generate_source",
        )
        build["oneClickRun"]["status"] = "running"
        build["oneClickRun"]["terminalBinding"]["platform"] = "mt5"
        build["oneClickRun"]["requestDigest"] = (
            self.bridge._ea_factory_one_click_request_digest(build)
        )
        state = self.state(build)

        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_ea_factory_active_worker_payload",
                return_value=None,
            ),
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_one_click_thread",
                return_value=True,
            ) as start,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            replay = self.bridge.run_ea_factory_build_one_click(
                build["id"],
                {"idempotencyKey": "one-click-ui-001"},
            )
        self.assertEqual(replay["kind"], "ea_factory_one_click_replayed")
        self.assertTrue(replay["idempotentReplay"])
        self.assertTrue(replay["workerStarted"])
        start.assert_called_once()
        self.assertEqual(build["oneClickRun"]["status"], "running")
        self.assertEqual(
            build["oneClickRun"]["currentStageId"],
            "generate_source",
        )

        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
            mock.patch.object(
                self.bridge,
                "_ea_factory_sync_build_status",
                return_value=False,
            ),
        ):
            action = self.bridge._ea_factory_one_click_next_action(build["id"])
        self.assertEqual(action["kind"], "retry_source")
        self.assertEqual(
            action["failedMissionId"],
            "mission-source-invalid-output",
        )
        self.assertEqual(action["attempt"], 1)

    def test_model_unavailable_stops_without_blind_retry_and_explains_reason(self) -> None:
        build = self.build()
        source = next(row for row in build["stages"] if row["id"] == "generate_source")
        source.update({
            "status": "failed",
            "blockedReasonCode": "model_unavailable",
            "missionId": "mission-source-model-unavailable",
            "manualRetryCount": 0,
            "manualRetryHistory": [],
        })
        build["oneClickRun"] = self._run(build, current_stage="generate_source")
        state = self.state(build)
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status", return_value=False),
        ):
            action = self.bridge._ea_factory_one_click_next_action(build["id"])

        self.assertEqual(action["kind"], "blocked")
        self.assertEqual(action["reasonCode"], "model_unavailable")
        self.assertEqual(build["oneClickRun"]["status"], "failed")
        self.assertFalse(build["oneClickRun"].get("canRetry", False))
        self.assertIn("ไม่รองรับบัญชีเครื่องนี้", build["oneClickRun"]["messageTh"])

    def test_restart_at_reserved_visible_stage_pauses_without_replaying_ui(self) -> None:
        build = self.build()
        for stage in build["stages"]:
            if stage["id"] in {"generate_source", "source_review"}:
                stage["status"] = "completed"
                stage["evidenceVerified"] = True
        build["oneClickRun"] = self._run(build, current_stage="compile_validate")
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        state = self.state(build)
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write_state,
            mock.patch.object(self.bridge, "_start_ea_factory_one_click_thread") as start,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            resumed = self.bridge.resume_interrupted_ea_factory_one_click_runs()
        self.assertEqual(resumed, 0)
        start.assert_not_called()
        write_state.assert_called_once()
        self.assertEqual(build["oneClickRun"]["status"], "awaiting_visible_terminal")
        self.assertEqual(build["oneClickRun"]["visibleAction"]["state"], "uncertain")
        self.assertTrue(
            build["oneClickRun"]["visibleAction"]["requiresExplicitResume"]
        )

    def test_visible_failure_pauses_and_same_key_retries_same_operation(self) -> None:
        build = self.build()
        for stage in build["stages"]:
            if stage["id"] in {"generate_source", "source_review"}:
                stage["status"] = "completed"
                stage["evidenceVerified"] = True
        build["oneClickRun"] = self._run(build, current_stage="compile_validate")
        build["oneClickRun"]["status"] = "running"
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        operation_id = build["oneClickRun"]["visibleAction"]["operationId"]
        state = self.state(build)
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_next_action",
                return_value={
                    "kind": "advance",
                    "stageId": "compile_validate",
                    "runId": build["oneClickRun"]["runId"],
                },
            ),
            mock.patch.object(
                self.bridge,
                "advance_ea_factory_build",
                side_effect=self.bridge.RequestError(
                    "visible failure",
                    503,
                    code="compile_verification_failed",
                ),
            ),
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            self.bridge._ea_factory_one_click_worker(
                build["id"],
                copy.deepcopy(build["oneClickRun"]),
            )
        self.assertEqual(build["oneClickRun"]["status"], "awaiting_visible_terminal")
        self.assertEqual(build["oneClickRun"]["visibleAction"]["state"], "uncertain")
        self.assertEqual(
            build["oneClickRun"]["visibleAction"]["lastFailureCode"],
            "compile_verification_failed",
        )

        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
            mock.patch.object(self.bridge, "_start_ea_factory_one_click_thread", return_value=True),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            retried = self.bridge.run_ea_factory_build_one_click(
                build["id"],
                {"idempotencyKey": "one-click-ui-001"},
            )
        self.assertEqual(retried["kind"], "ea_factory_one_click_resumed")
        self.assertEqual(
            build["oneClickRun"]["visibleAction"]["operationId"],
            operation_id,
        )
        self.assertEqual(build["oneClickRun"]["visibleAction"]["attemptCount"], 2)

    def test_finish_persists_uncertain_visible_state_when_immutable_version_is_missing(self) -> None:
        build = self.build()
        create_sheet_binding = {
            "recordId": "deep-one-click-sheet",
            "sourceRecordId": build["sourceRecordId"],
            "recordDigest": build["sourceRecordDigest"],
            "catalogDigest": "c" * 64,
            "snapshotDigest": "d" * 64,
            "configRevision": 7,
        }
        build["createSheetBinding"] = create_sheet_binding
        build["createRequestDigest"] = self.bridge._ea_factory_create_request_digest(
            build["sourceRecordId"],
            build["platform"],
            build["brief"],
            build["artifactKind"],
            create_sheet_binding,
        )
        build["versions"] = [{
            "version": 1,
            "fileName": "MissingEA.mq4",
            "sourceDigest": "d" * 64,
            "sourceFile": "Source/MissingEA.mq4",
            "versionFile": "EA_Versions/MissingEA_v01.mq4",
            "sourceReportId": "report-source-missing",
            "immutable": True,
            "createdAt": "2026-09-11T00:00:00Z",
        }]
        build["oneClickRun"] = self._run(
            build,
            current_stage="compile_validate",
        )
        build["oneClickRun"]["status"] = "running"
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        state = self.state(build)
        original_stages = copy.deepcopy(build["stages"])
        original_versions = copy.deepcopy(build["versions"])
        audit_events = []
        message_th = (
            "ตรวจผล Compile ไม่สำเร็จ ระบบหยุดไว้ก่อน "
            "และจะไม่กด Compile ซ้ำจนกว่าจะยืนยันผลเดิม"
        )

        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "ea-factory-state.json"
            backup_path = state_path.with_name(f"{state_path.name}.bak")
            backup_path.write_text("known-good-backup", encoding="utf-8")
            state_path.write_text(
                json.dumps(state, ensure_ascii=False),
                encoding="utf-8",
            )
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_state_path",
                    return_value=state_path,
                ),
                mock.patch.object(
                    self.bridge,
                    "_load_ea_factory_state_unlocked",
                    side_effect=self.bridge.DataIntegrityError(
                        "EA Factory immutable source versions failed integrity validation."
                    ),
                ),
                mock.patch.object(
                    self.bridge,
                    "_invalidate_ea_factory_state_cache",
                ),
                mock.patch.object(
                    self.bridge,
                    "_invalidate_ea_factory_read_model_cache",
                ),
                mock.patch.object(
                    self.bridge,
                    "append_audit",
                    side_effect=audit_events.append,
                ),
            ):
                self.bridge._ea_factory_one_click_finish(
                    build["id"],
                    expected_run_snapshot=copy.deepcopy(build["oneClickRun"]),
                    status="awaiting_visible_terminal",
                    current_stage_id="compile_validate",
                    failure_code="compile_verification_failed",
                    message_th=message_th,
                )

            stored = json.loads(state_path.read_text(encoding="utf-8"))
            backup_after = backup_path.read_text(encoding="utf-8")

        stored_build = stored["builds"][0]
        stored_run = stored_build["oneClickRun"]
        self.assertEqual(stored_run["status"], "awaiting_visible_terminal")
        self.assertIsNone(stored_run["failureCode"])
        self.assertEqual(stored_run["messageTh"], message_th)
        self.assertIsNone(stored_run["completedAt"])
        self.assertEqual(stored_run["visibleAction"]["state"], "uncertain")
        self.assertEqual(
            stored_run["visibleAction"]["lastFailureCode"],
            "compile_verification_failed",
        )
        self.assertTrue(
            stored_run["visibleAction"]["requiresExplicitResume"]
        )
        self.assertEqual(stored_build["stages"], original_stages)
        self.assertEqual(stored_build["versions"], original_versions)
        self.assertEqual(backup_after, "known-good-backup")
        self.assertTrue(audit_events[-1]["statePersisted"])
        self.assertEqual(
            audit_events[-1]["persistenceMode"],
            "fail_closed_raw_terminal_patch",
        )
        self.assertEqual(
            audit_events[-1]["finishExceptionClass"],
            "DataIntegrityError",
        )
        self.assertEqual(audit_events[-1]["visibleActionState"], "uncertain")

    def test_finish_falls_back_to_audit_without_leaving_worker_exception(self) -> None:
        audit_events = []
        message_th = "ระบบหยุดงานเพื่อความปลอดภัย กรุณาตรวจ Build ก่อนเริ่มใหม่"
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                side_effect=RuntimeError("primary state load failed"),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_finish_from_raw_state_unlocked",
                side_effect=self.bridge.DataIntegrityError(
                    "raw state is unsafe to update"
                ),
            ),
            mock.patch.object(
                self.bridge,
                "append_audit",
                side_effect=audit_events.append,
            ),
        ):
            self.bridge._ea_factory_one_click_finish(
                "ea-build-one-click-test",
                expected_run_snapshot={},
                status="blocked",
                current_stage_id="generate_source",
                failure_code="one_click_worker_exception",
                message_th=message_th,
            )

        self.assertEqual(len(audit_events), 1)
        self.assertFalse(audit_events[0]["statePersisted"])
        self.assertEqual(audit_events[0]["persistenceMode"], "audit_only")
        self.assertEqual(
            audit_events[0]["finishExceptionClass"],
            "DataIntegrityError",
        )
        self.assertEqual(audit_events[0]["messageTh"], message_th)
        self.assertFalse(audit_events[0]["liveTradingAllowed"])

    def test_next_action_integrity_error_finishes_before_audit_io(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(
            build,
            current_stage="generate_source",
        )
        expected_run = copy.deepcopy(build["oneClickRun"])
        call_order = []

        def finish(*_args, **_kwargs):
            call_order.append("finish")

        def failed_audit(_event):
            call_order.append("audit")
            raise OSError("audit disk unavailable")

        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_next_action",
                side_effect=self.bridge.DataIntegrityError(
                    "EA Factory immutable source versions failed integrity validation."
                ),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_finish",
                side_effect=finish,
            ) as finish_call,
            mock.patch.object(
                self.bridge,
                "append_audit",
                side_effect=failed_audit,
            ),
        ):
            self.bridge._ea_factory_one_click_worker(
                build["id"],
                expected_run,
            )

        self.assertEqual(call_order, ["finish", "audit"])
        finish_call.assert_called_once()
        finish_kwargs = finish_call.call_args.kwargs
        self.assertEqual(finish_kwargs["expected_run_snapshot"], expected_run)
        self.assertEqual(finish_kwargs["status"], "failed")
        self.assertEqual(finish_kwargs["current_stage_id"], "generate_source")
        self.assertEqual(
            finish_kwargs["failure_code"],
            "one_click_state_integrity_failed",
        )

    def test_stale_callback_cannot_downgrade_newer_raw_run(self) -> None:
        build = self.build()
        build["createRequestDigest"] = self.bridge._ea_factory_create_request_digest(
            build["sourceRecordId"],
            build["platform"],
            build["brief"],
            build["artifactKind"],
        )
        build["oneClickRun"] = self._run(
            build,
            current_stage="generate_source",
        )
        expected_old_run = copy.deepcopy(build["oneClickRun"])
        self.bridge._ea_factory_one_click_update(
            build["oneClickRun"],
            status="running",
            current_stage_id="generate_source",
            failure_code=None,
            message_th="งานรอบใหม่กำลังทำขั้นสร้าง Source",
        )
        state = self.state(build)
        audit_events = []

        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "ea-factory-state.json"
            state_path.write_text(
                json.dumps(state, ensure_ascii=False),
                encoding="utf-8",
            )
            before = state_path.read_bytes()
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_state_path",
                    return_value=state_path,
                ),
                mock.patch.object(
                    self.bridge,
                    "_load_ea_factory_state_unlocked",
                    side_effect=self.bridge.DataIntegrityError(
                        "EA Factory immutable source versions failed integrity validation."
                    ),
                ),
                mock.patch.object(
                    self.bridge,
                    "append_audit",
                    side_effect=audit_events.append,
                ),
            ):
                self.bridge._ea_factory_one_click_finish(
                    build["id"],
                    expected_run_snapshot=expected_old_run,
                    status="failed",
                    current_stage_id="generate_source",
                    failure_code="one_click_coordinator_failed",
                    message_th="callback เก่าต้องไม่ปิดงานรอบใหม่",
                )
            after = state_path.read_bytes()

        self.assertEqual(after, before)
        self.assertEqual(build["oneClickRun"]["status"], "running")
        self.assertFalse(audit_events[-1]["statePersisted"])
        self.assertEqual(audit_events[-1]["persistenceMode"], "audit_only")
        self.assertEqual(
            audit_events[-1]["finishExceptionClass"],
            "DataIntegrityError",
        )

    def test_integrity_failure_get_returns_actionable_fail_closed_result(self) -> None:
        handler = object.__new__(self.bridge.BridgeHandler)
        handler.path = "/api/props/right_server_racks/ea-factory"
        handler.validate_local_request = mock.Mock(return_value=None)
        handler.send_json = mock.Mock()
        with mock.patch.object(
            self.bridge,
            "ea_factory_read_model",
            side_effect=self.bridge.DataIntegrityError(
                "EA Factory immutable source versions failed integrity validation."
            ),
        ):
            handler._do_GET_guarded()

        handler.send_json.assert_called_once()
        result = handler.send_json.call_args.args[0]
        self.assertEqual(handler.send_json.call_args.kwargs["status"], 409)
        self.assertNotIn("_httpStatus", result)
        self.assertEqual(result["kind"], "ea_factory_integrity_blocked")
        self.assertEqual(result["code"], "ea_factory_artifact_integrity_failed")
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["oneClick"]["commandsAllowed"])
        self.assertEqual(result["oneClick"]["visibleActionState"], "uncertain")
        self.assertTrue(result["oneClick"]["requiresExplicitRecovery"])
        self.assertIn("หลักฐานหรือสัญญาของ Build", result["messageTh"])
        self.assertIn("ไม่ผ่านการตรวจสอบกับรุ่นปัจจุบัน", result["messageTh"])
        self.assertNotIn("สูญหาย", result["messageTh"])
        self.assertNotIn("ถูกเปลี่ยนแปลง", result["messageTh"])
        self.assertFalse(result["liveTradingAllowed"])
        self.assertNotIn("eaFactory", result)

    def test_visible_handler_receives_immutable_request_dto(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="compile_validate")
        build["oneClickRun"]["status"] = "running"
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        operation_id = build["oneClickRun"]["visibleAction"]["operationId"]
        request = {
            "stageId": "compile_validate",
            "platform": "mt4",
            "runSnapshotDigest": "a" * 64,
            "terminalBinding": copy.deepcopy(
                build["oneClickRun"]["terminalBinding"]
            ),
            "visibleOperation": copy.deepcopy(build["oneClickRun"]["visibleAction"]),
        }

        def complete(**kwargs):
            self.assertNotIn("runSnapshotDigest", kwargs["request"])
            kwargs["request"]["visibleOperation"]["operationId"] = "mutated-copy"
            return {
                "schemaVersion": self.bridge.EA_FACTORY_VISIBLE_RESULT_SCHEMA_VERSION,
                "operationId": operation_id,
                "metrics": {
                    "compileVerified": True,
                    "processId": 123,
                    "processBinding": {
                        "terminalProcessId": 123,
                        "terminalWindowOwnerProcessId": 123,
                        "frontOfficeProcessId": 456,
                        "frontOfficeWindowOwnerProcessId": 456,
                    },
                },
                "artifactSpecifications": [
                    {
                        "alias": "compiled_binary",
                        "relativePath": "EA_Versions/test.ex4",
                        "artifactKind": "compile_evidence",
                    },
                    {
                        "alias": "visible_window",
                        "relativePath": "Screenshots/compile.png",
                        "artifactKind": "screenshot_evidence",
                    },
                    {
                        "alias": "compile_log",
                        "relativePath": "Reports/compile.txt",
                        "artifactKind": "compile_evidence",
                    },
                    {
                        "alias": "adapter_receipt",
                        "relativePath": "Reports/compile-receipt.json",
                        "artifactKind": "compile_evidence",
                    },
                ],
            }

        handler = mock.Mock(side_effect=complete)
        with (
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER",
                handler,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                return_value={
                    "ready": True,
                    "freshProcessProbe": True,
                    "foregroundInteraction": True,
                    "visibleEvidenceCapture": True,
                    "terminalSelectionBound": True,
                    "liveTradingAllowed": False,
                    "terminalProcessMayRemainOpen": True,
                    "processAndWindowBinding": True,
                    "idempotentOperationBinding": True,
                    "durableReceiptRecovery": True,
                    "terminalShutdownAllowed": False,
                    "autoTradingMayBeToggled": False,
                    "chartAttachmentAllowed": False,
                    "visibleMetaEditorCompile": True,
                },
            ),
        ):
            result = self.bridge._ea_factory_invoke_visible_front_office_handler(request)
        call = handler.call_args.kwargs
        self.assertEqual(
            call["request"]["visibleOperation"]["operationId"],
            "mutated-copy",
        )
        self.assertEqual(
            request["visibleOperation"]["operationId"],
            operation_id,
        )
        self.assertEqual(request["runSnapshotDigest"], "a" * 64)
        self.assertTrue(result["metrics"]["compileVerified"])
        self.assertEqual(result["metrics"]["processId"], 123)

    def test_visible_handler_rejects_non_contract_sensitive_metric(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="compile_validate")
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        operation_id = build["oneClickRun"]["visibleAction"]["operationId"]
        request = {
            "stageId": "compile_validate",
            "platform": "mt4",
            "terminalBinding": copy.deepcopy(
                build["oneClickRun"]["terminalBinding"]
            ),
            "visibleOperation": copy.deepcopy(build["oneClickRun"]["visibleAction"]),
        }
        raw = {
            "schemaVersion": self.bridge.EA_FACTORY_VISIBLE_RESULT_SCHEMA_VERSION,
            "operationId": operation_id,
            "metrics": {"compileVerified": True, "accountNumber": 123456},
            "artifactSpecifications": [
                {"alias": "compiled_binary", "relativePath": "EA_Versions/test.ex4", "artifactKind": "compile_evidence"},
                {"alias": "visible_window", "relativePath": "Screenshots/compile.png", "artifactKind": "screenshot_evidence"},
                {"alias": "compile_log", "relativePath": "Reports/compile.txt", "artifactKind": "compile_evidence"},
                {"alias": "adapter_receipt", "relativePath": "Reports/compile-receipt.json", "artifactKind": "compile_evidence"},
            ],
        }
        capability = {
            "ready": True,
            "freshProcessProbe": True,
            "foregroundInteraction": True,
            "visibleEvidenceCapture": True,
            "terminalSelectionBound": True,
            "liveTradingAllowed": False,
            "terminalProcessMayRemainOpen": True,
            "processAndWindowBinding": True,
            "idempotentOperationBinding": True,
            "durableReceiptRecovery": True,
            "terminalShutdownAllowed": False,
            "autoTradingMayBeToggled": False,
            "chartAttachmentAllowed": False,
            "visibleMetaEditorCompile": True,
        }
        with (
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER",
                return_value=raw,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                return_value=capability,
            ),
        ):
            with self.assertRaises(self.bridge.RequestError) as raised:
                self.bridge._ea_factory_invoke_visible_front_office_handler(request)
        self.assertEqual(raised.exception.status, 503)
        self.assertIn("invalid result envelope", str(raised.exception))

    def test_visible_private_metric_storage_preserves_only_positive_numeric_pids(self) -> None:
        stored = self.bridge._ea_factory_visible_metrics_storage({
            "processId": 123,
            "processBinding": {
                "terminalProcessId": 123,
                "terminalWindowOwnerProcessId": 123,
                "frontOfficeProcessId": 456,
                "frontOfficeWindowOwnerProcessId": 456,
            },
            "postProcessBinding": {"terminalProcessId": 123},
            "accountNumber": 999999,
            "password": "not-a-real-password",
        })
        self.assertEqual(stored["processId"], 123)
        self.assertEqual(stored["processBinding"]["frontOfficeProcessId"], 456)
        self.assertEqual(stored["accountNumber"], "[REDACTED_SECRET]")
        self.assertEqual(stored["password"], "[REDACTED_SECRET]")
        for invalid in (0, -1, True, "123"):
            self.assertEqual(
                self.bridge._ea_factory_visible_metrics_storage(
                    {"processId": invalid}
                )["processId"],
                "[REDACTED_SECRET]",
            )

    def test_trusted_visible_report_round_trip_retains_private_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            reports = Path(temporary) / "reports"
            reports.mkdir()
            payload = {
                "id": "report-eaf-visible-round-trip",
                "type": "ea_compile_report",
                "linkedMissionId": "mission-eaf-visible-round-trip",
                "status": "ready",
                "metrics": {
                    "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
                    "operationId": "ea-visible-round-trip",
                    "processId": 123,
                    "windowHandle": 456,
                    "processBinding": {
                        "terminalProcessId": 123,
                        "terminalWindowOwnerProcessId": 123,
                        "frontOfficeProcessId": 789,
                        "frontOfficeWindowOwnerProcessId": 789,
                    },
                    "postProcessBinding": {
                        "terminalProcessId": 123,
                        "terminalWindowOwnerProcessId": 123,
                        "frontOfficeProcessId": 789,
                        "frontOfficeWindowOwnerProcessId": 789,
                    },
                },
            }
            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", reports),
                mock.patch.object(self.bridge, "append_audit"),
            ):
                report = self.bridge.create_report(
                    payload,
                    queue_research_sheet=False,
                    _trusted_visible_process_identity=True,
                )
                persisted = self.bridge.read_json(
                    reports / "report-eaf-visible-round-trip.json",
                    None,
                )
            self.assertEqual(persisted, report)
            self.assertEqual(report["metrics"]["processId"], 123)
            self.assertEqual(
                report["metrics"]["processBinding"]["frontOfficeProcessId"],
                789,
            )
            public = self.bridge.report_read_model_item(report)
            self.assertNotIn("processId", public["metrics"])
            self.assertNotIn("processBinding", public["metrics"])

    def test_trusted_visible_report_round_trip_preserves_104_metric_contract(self) -> None:
        required_tail = {
            "staticSixGroupSourceContractVerified": True,
            "logicRecheck": {"verified": True},
            "logicRecheckDigest": "a" * 64,
            "logicRecheckVerified": True,
        }
        metrics = {
            "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "operationId": "ea-visible-104-metric-round-trip",
        }
        metrics.update({
            f"boundedMetric{index:03d}": index
            for index in range(97)
        })
        metrics["password"] = "not-a-real-password"
        metrics.update(required_tail)
        self.assertEqual(len(metrics), 104)
        self.assertEqual(list(metrics)[100:], list(required_tail))

        with tempfile.TemporaryDirectory() as temporary:
            reports = Path(temporary) / "reports"
            reports.mkdir()
            payload = {
                "id": "report-eaf-visible-104-metric-round-trip",
                "type": "ea_build_report",
                "linkedMissionId": "mission-eaf-visible-104-metric-round-trip",
                "status": "ready",
                "metrics": metrics,
            }
            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", reports),
                mock.patch.object(self.bridge, "append_audit"),
            ):
                report = self.bridge.create_report(
                    payload,
                    queue_research_sheet=False,
                    _trusted_visible_process_identity=True,
                )
                persisted = self.bridge.read_json(
                    reports / "report-eaf-visible-104-metric-round-trip.json",
                    None,
                )

        self.assertEqual(persisted, report)
        self.assertEqual(len(report["metrics"]), 104)
        self.assertEqual(list(report["metrics"])[100:], list(required_tail))
        self.assertEqual(report["metrics"]["password"], "[REDACTED_SECRET]")
        self.assertTrue(report["safety"]["secretRedacted"])
        for key, value in required_tail.items():
            self.assertEqual(report["metrics"][key], value)

    def test_trusted_visible_report_rejects_lossy_or_over_limit_metrics(self) -> None:
        exact_limit = self.bridge.EA_FACTORY_VISIBLE_METRICS_COLLECTION_LIMIT
        over_limit_metrics = {
            "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "operationId": "ea-visible-over-limit-metrics",
        }
        over_limit_metrics.update({
            f"boundedMetric{index:03d}": index
            for index in range(exact_limit - 1)
        })
        self.assertEqual(len(over_limit_metrics), exact_limit + 1)
        lossy_key_metrics = {
            "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "operationId": "ea-visible-lossy-metric-key",
            "x" * 121: "must-not-be-persisted",
        }
        nested_overlong_key_metrics = {
            "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "operationId": "ea-visible-nested-overlong-metric-key",
            "outer": {"x" * 121: "must-not-be-persisted"},
        }
        nested_colliding_key_metrics = {
            "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "operationId": "ea-visible-nested-colliding-metric-keys",
            "outer": {
                ("x" * 120) + "a": "first-must-not-be-persisted",
                ("x" * 120) + "b": "second-must-not-be-persisted",
            },
        }
        nested_non_string_key_metrics = {
            "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "operationId": "ea-visible-nested-non-string-metric-key",
            "outer": {1: "must-not-be-persisted"},
        }

        with tempfile.TemporaryDirectory() as temporary:
            reports = Path(temporary) / "reports"
            reports.mkdir()
            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", reports),
                mock.patch.object(self.bridge, "append_audit"),
            ):
                for report_id, metrics in (
                    ("report-eaf-visible-over-limit", over_limit_metrics),
                    ("report-eaf-visible-lossy-key", lossy_key_metrics),
                    (
                        "report-eaf-visible-nested-overlong-key",
                        nested_overlong_key_metrics,
                    ),
                    (
                        "report-eaf-visible-nested-colliding-keys",
                        nested_colliding_key_metrics,
                    ),
                    (
                        "report-eaf-visible-nested-non-string-key",
                        nested_non_string_key_metrics,
                    ),
                ):
                    with self.subTest(report_id=report_id):
                        with self.assertRaises(self.bridge.DataIntegrityError):
                            self.bridge.create_report(
                                {
                                    "id": report_id,
                                    "type": "ea_build_report",
                                    "status": "ready",
                                    "metrics": metrics,
                                },
                                queue_research_sheet=False,
                                _trusted_visible_process_identity=True,
                            )
                        self.assertFalse((reports / f"{report_id}.json").exists())

    def test_visible_retry_limit_allows_receipt_only_recovery_without_increment(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="compile_validate")
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        action = build["oneClickRun"]["visibleAction"]
        action.update({
            "attemptCount": self.bridge.EA_FACTORY_ONE_CLICK_VISIBLE_RETRY_LIMIT,
            "state": "uncertain",
            "requiresExplicitResume": True,
        })
        build["oneClickRun"]["status"] = "awaiting_visible_terminal"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            summaries = root / "Summaries"
            summaries.mkdir()
            receipt = summaries / (
                f"{action['operationId']}-compile-receipt.json"
            )
            receipt.write_text("{}", encoding="utf-8")
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_build_directory",
                    return_value=root,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_file_catalog",
                    return_value=[],
                ),
            ):
                self.assertTrue(
                    self.bridge._ea_factory_one_click_reserve_visible_action(
                        build,
                        build["oneClickRun"],
                        "compile_validate",
                        explicit_resume=True,
                    )
                )
                self.assertEqual(
                    action["attemptCount"],
                    self.bridge.EA_FACTORY_ONE_CLICK_VISIBLE_RETRY_LIMIT,
                )
                action.update({
                    "state": "uncertain",
                    "requiresExplicitResume": True,
                })
                model = self.bridge._ea_factory_one_click_read_model(build)
                self.assertTrue(model["canResume"])

            receipt.unlink()
            action.update({
                "state": "uncertain",
                "requiresExplicitResume": True,
            })
            with mock.patch.object(
                self.bridge,
                "_ea_factory_build_directory",
                return_value=root,
            ):
                self.assertFalse(
                    self.bridge._ea_factory_one_click_reserve_visible_action(
                        build,
                        build["oneClickRun"],
                        "compile_validate",
                        explicit_resume=True,
                    )
                )

    def test_mt5_compile_prestart_recovery_requires_exact_pre_f7_checkpoint(self) -> None:
        build = self.build()
        build["platform"] = "mt5"
        build["oneClickRun"] = self._run(build, current_stage="compile_validate")
        run = build["oneClickRun"]
        run["status"] = "awaiting_visible_terminal"
        run["terminalBinding"] = {
            "platform": "mt5",
            "candidateId": "mtc-one-click-terminal",
            "selectionRevision": 7,
            "bindingDigest": "c" * 64,
        }
        self.assertTrue(
            self.bridge._ea_factory_one_click_reserve_visible_action(
                build,
                run,
                "compile_validate",
            )
        )
        action = run["visibleAction"]
        action.update({
            "attemptCount": self.bridge.EA_FACTORY_ONE_CLICK_VISIBLE_RETRY_LIMIT,
            "state": "uncertain",
            "lastFailureCode": "mt5_metaeditor_compile_result_not_ready",
            "requiresExplicitResume": True,
        })
        operation_id = action["operationId"]
        token = operation_id.removeprefix("ea-visible-")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_root = root / "build"
            data_root = root / "terminal-data"
            for name in ("EA_Versions", "Reports", "Screenshots", "Summaries"):
                (build_root / name).mkdir(parents=True, exist_ok=True)
            version_path = build_root / "EA_Versions" / "ExactMT5_v01.mq5"
            version_path.write_text("#property strict\nvoid OnTick(){}\n", encoding="utf-8")
            source_digest = hashlib.sha256(version_path.read_bytes()).hexdigest()
            build["versions"] = [{
                "version": 1,
                "fileName": version_path.name,
                "versionFile": f"EA_Versions/{version_path.name}",
                "sourceDigest": source_digest,
                "immutable": True,
            }]
            work_root = (
                data_root
                / "MQL5"
                / "Experts"
                / "Metafxclub"
                / "AgentHQ"
                / operation_id
            )
            work_root.mkdir(parents=True)
            working_source = work_root / f"agenthq_{token}.mq5"
            working_source.write_bytes(version_path.read_bytes())
            expected_intent = {
                "schemaVersion": "ea-factory-visible-front-office-action-intent-v1",
                "operationId": operation_id,
                "stageId": "compile_validate",
                "terminalCandidateId": "mtc-one-click-terminal",
                "terminalSelectionRevision": 7,
                "terminalBindingDigest": "c" * 64,
                "sourceDigest": source_digest,
                "platform": "mt5",
            }
            intent_path = (
                build_root / "Summaries" / f"{operation_id}-compile-intent.json"
            )
            intent_path.write_text(
                json.dumps(expected_intent, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            resolved_target = {
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
                "platform": "mt5",
                "dataPath": str(data_root),
            }

            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_build_directory",
                    return_value=build_root,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_one_click_terminal_binding_current",
                    return_value=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_visible_adapter_target_resolver",
                    return_value=resolved_target,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_file_catalog",
                    return_value=[],
                ),
            ):
                self.assertTrue(
                    self.bridge._ea_factory_one_click_compile_prestart_recovery_available(
                        build, "compile_validate", action
                    )
                )
                model = self.bridge._ea_factory_one_click_read_model(build)
                self.assertTrue(model["canResume"])
                self.assertEqual(
                    model["visibleAction"]["attemptLimit"],
                    self.bridge.EA_FACTORY_ONE_CLICK_PRESTART_RECOVERY_LIMIT,
                )

                working_source.write_text("changed", encoding="utf-8")
                self.assertFalse(
                    self.bridge._ea_factory_one_click_compile_prestart_recovery_available(
                        build, "compile_validate", action
                    )
                )
                working_source.write_bytes(version_path.read_bytes())

                working_binary = working_source.with_suffix(".ex5")
                working_binary.write_bytes(b"not-a-real-binary")
                self.assertFalse(
                    self.bridge._ea_factory_one_click_compile_prestart_recovery_available(
                        build, "compile_validate", action
                    )
                )
                working_binary.unlink()

                intent_path.write_text("{}", encoding="utf-8")
                self.assertFalse(
                    self.bridge._ea_factory_one_click_compile_prestart_recovery_available(
                        build, "compile_validate", action
                    )
                )
                intent_path.write_text(
                    json.dumps(expected_intent, sort_keys=True, separators=(",", ":")),
                    encoding="utf-8",
                )

                self.assertTrue(
                    self.bridge._ea_factory_one_click_reserve_visible_action(
                        build,
                        run,
                        "compile_validate",
                        explicit_resume=True,
                    )
                )
                self.assertEqual(
                    action["attemptCount"],
                    self.bridge.EA_FACTORY_ONE_CLICK_PRESTART_RECOVERY_LIMIT,
                )
                action.update({
                    "state": "uncertain",
                    "lastFailureCode": "mt5_metaeditor_compile_result_not_ready",
                    "requiresExplicitResume": True,
                })
                self.assertFalse(
                    self.bridge._ea_factory_one_click_reserve_visible_action(
                        build,
                        run,
                        "compile_validate",
                        explicit_resume=True,
                    )
                )

    def test_mt5_backtest_prestart_recovery_is_exact_and_allows_one_fourth_attempt(self) -> None:
        build = self.build()
        build["platform"] = "mt5"
        build["versions"] = [{
            "version": 1,
            "fileName": "ExactMT5_v01.mq5",
            "versionFile": "EA_Versions/ExactMT5_v01.mq5",
            "sourceDigest": "d" * 64,
            "immutable": True,
        }]
        build["oneClickRun"] = self._run(
            build,
            current_stage="backtest_recheck",
        )
        run = build["oneClickRun"]
        run["terminalBinding"]["platform"] = "mt5"
        self.assertTrue(
            self.bridge._ea_factory_one_click_reserve_visible_action(
                build,
                run,
                "backtest_recheck",
            )
        )
        action = run["visibleAction"]
        action.update({
            "attemptCount": self.bridge.EA_FACTORY_ONE_CLICK_VISIBLE_RETRY_LIMIT,
            "state": "uncertain",
            "lastFailureCode": "mt5_tester_controls_not_verified",
            "requiresExplicitResume": True,
        })
        run["status"] = "awaiting_visible_terminal"
        operation_id = action["operationId"]
        binding = run["terminalBinding"]
        binary = {
            "fileName": "ExactMT5_v01.ex5",
            "relativePath": "EA_Versions/ExactMT5_v01.ex5",
            "sha256": "e" * 64,
        }
        tester_settings = {
            "schemaVersion": self.bridge.EA_FACTORY_TESTER_SETTINGS_SCHEMA_VERSION,
            "expertFileName": binary["fileName"],
            "visualMode": True,
        }
        manifest = {"manifestDigest": "a" * 64}
        expected_entries = [{
            "ordinal": 0,
            "inputName": "RiskPercent",
            "current": "1.0",
            "start": "1.0",
            "step": "0.0",
            "stop": "1.0",
            "enabled": False,
        }]
        preset_bytes = self.bridge._ea_factory_mt5_set_payload(expected_entries)
        compiled_deployment = {
            "deploymentRef": "mt5deploy_exact",
            "bindingDigest": "f" * 64,
        }
        relative_preset = f"Sets/{operation_id}-tester-input-preset.set"
        preset_core = {
            "schemaVersion": "ea-factory-mt5-set-ref-v1",
            "relativePath": relative_preset,
            "sha256": hashlib.sha256(preset_bytes).hexdigest(),
            "inputManifestDigest": manifest["manifestDigest"],
            "entryCount": len(expected_entries),
            "expectedReadbackEntries": expected_entries,
            "expectedReadbackEntriesDigest": (
                self.bridge._ea_factory_optimization_json_sha256(expected_entries)
            ),
        }
        preset_ref_digest = self.bridge._ea_factory_optimization_json_sha256(
            preset_core
        )
        identity_suffix = self.bridge.payload_digest(
            "ea-factory-visible-front-office-stage-v1",
            build["id"],
            "backtest_recheck",
            operation_id,
        )[:24]
        intent = {
            "schemaVersion": "ea-factory-visible-front-office-action-intent-v1",
            "operationId": operation_id,
            "stageId": "backtest_recheck",
            "terminalCandidateId": binding["candidateId"],
            "terminalSelectionRevision": binding["selectionRevision"],
            "terminalBindingDigest": binding["bindingDigest"],
            "sourceDigest": build["versions"][0]["sourceDigest"],
            "compiledBinarySha256": binary["sha256"],
            "compiledDeploymentRef": compiled_deployment["deploymentRef"],
            "compiledDeploymentDigest": compiled_deployment["bindingDigest"],
            "inputBindingRefDigest": preset_ref_digest,
            "optimizationSetRefDigest": None,
            "baselinePresetRefDigest": None,
            "optimizationMode": None,
            "optimizationCriterion": None,
            "platform": "mt5",
        }
        safety = {
            "liveTradingAllowed": False,
            "autoTradingMayBeToggled": False,
            "chartAttachmentAllowed": False,
            "terminalShutdownAllowed": False,
            "visualModeRequired": True,
            "optimizationAllowed": False,
        }
        action_request = {
            "schemaVersion": "ea-factory-visible-mt5-action-request-v1",
            "operationId": operation_id,
            "stageId": "backtest_recheck",
            "buildId": build["id"],
            "missionId": f"mission-eaf-{identity_suffix}",
            "reportId": f"report-eaf-{identity_suffix}",
            "terminalCandidateId": binding["candidateId"],
            "terminalSelectionRevision": binding["selectionRevision"],
            "terminalBindingDigest": binding["bindingDigest"],
            "sourceDigest": build["versions"][0]["sourceDigest"],
            "compiledBinarySha256": binary["sha256"],
            "testerSettingsDigest": (
                self.bridge._ea_factory_canonical_json_sha256(tester_settings)
            ),
            "optimizationRangesDigest": None,
            "optimizationSetDigest": None,
            "compiledDeploymentDigest": compiled_deployment["bindingDigest"],
            "inputBindingRefDigest": preset_ref_digest,
            "optimizationSetRefDigest": None,
            "baselinePresetRefDigest": None,
            "optimizationMode": None,
            "optimizationCriterion": None,
            "safetyPolicyDigest": self.bridge._ea_factory_canonical_json_sha256(
                safety
            ),
        }
        action_request["actionRequestDigest"] = (
            self.bridge._ea_factory_canonical_json_sha256(action_request)
        )

        with tempfile.TemporaryDirectory() as temporary:
            build_root = Path(temporary)
            for name in ("Summaries", "Screenshots", "Reports", "Sets"):
                (build_root / name).mkdir()
            intent_path = build_root / "Summaries" / (
                f"{operation_id}-backtest-intent.json"
            )
            action_path = build_root / "Summaries" / (
                f"{operation_id}-backtest-action.json"
            )
            preset_path = build_root / "Sets" / (
                f"{operation_id}-tester-input-preset.set"
            )
            intent_path.write_text(
                json.dumps(intent, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            action_path.write_text(
                json.dumps(action_request, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            preset_path.write_bytes(preset_bytes)

            patches = (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_build_directory",
                    return_value=build_root,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_one_click_terminal_binding_current",
                    return_value=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_mt5_input_context",
                    return_value={"build": build},
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_mt5_optimization_input_manifest",
                    return_value=manifest,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_mt5_tester_input_preset",
                    return_value={},
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_mt5_tester_fixed_overrides",
                    return_value={},
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_mt5_expected_set_entries",
                    return_value=expected_entries,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_backtest_binary",
                    return_value=binary,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_default_tester_settings",
                    return_value=tester_settings,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_mt5_compiled_deployment_binding",
                    return_value=compiled_deployment,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_file_catalog",
                    return_value=[],
                ),
            )
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8], patches[9], patches[10]:
                self.assertTrue(
                    self.bridge._ea_factory_one_click_mt5_prestart_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                self.assertTrue(
                    self.bridge._ea_factory_one_click_prestart_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                model = self.bridge._ea_factory_one_click_read_model(build)
                self.assertTrue(model["canResume"])
                self.assertEqual(
                    model["visibleAction"]["attemptLimit"],
                    self.bridge.EA_FACTORY_ONE_CLICK_PRESTART_RECOVERY_LIMIT,
                )

                forbidden_paths = (
                    build_root / "Summaries" / f"{operation_id}-backtest-start-boundary.json",
                    build_root / "Summaries" / f"{operation_id}-backtest-start-boundary.json.dispatch-confirmed",
                    build_root / "Summaries" / f"{operation_id}-backtest-receipt.json",
                    build_root / "Summaries" / f"{operation_id}-backtest-ui.json",
                    build_root / "Summaries" / f"{operation_id}-backtest-ui-backtest.json",
                    build_root / "Summaries" / f"{operation_id}-backtest-completion-checkpoint.json",
                    build_root / "Summaries" / f"{operation_id}-backtest-expert-catalog-refresh-boundary.json",
                    build_root / "Screenshots" / f"{operation_id}-backtest-settings.png",
                    build_root / "Screenshots" / f"{operation_id}-backtest-result.png",
                    build_root / "Screenshots" / f"{operation_id}-backtest-report.png",
                    build_root / "Screenshots" / f"{operation_id}-tester-input-preset.png",
                    build_root / "Reports" / f"{operation_id}-backtest-mt5.htm",
                    build_root / "Reports" / f"{operation_id}-backtest-mt5-viewer.htm",
                    build_root / "Sets" / f"{operation_id}-tester-input-readback.set",
                )
                for forbidden_path in forbidden_paths:
                    with self.subTest(forbidden_artifact=forbidden_path.name):
                        forbidden_path.write_bytes(b"post-start-evidence")
                        self.assertFalse(
                            self.bridge._ea_factory_one_click_mt5_prestart_recovery_available(
                                build,
                                "backtest_recheck",
                                action,
                            )
                        )
                        forbidden_path.unlink()

                preset_path.write_bytes(preset_bytes + b"Changed=1||1||0||1||N\r\n")
                self.assertFalse(
                    self.bridge._ea_factory_one_click_mt5_prestart_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                preset_path.write_bytes(preset_bytes)

                changed_action = dict(action_request)
                changed_action["missionId"] = "mission-tampered"
                action_path.write_text(
                    json.dumps(changed_action, sort_keys=True, separators=(",", ":")),
                    encoding="utf-8",
                )
                self.assertFalse(
                    self.bridge._ea_factory_one_click_mt5_prestart_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                action_path.write_text(
                    json.dumps(action_request, sort_keys=True, separators=(",", ":")),
                    encoding="utf-8",
                )

                self.assertTrue(
                    self.bridge._ea_factory_one_click_reserve_visible_action(
                        build,
                        run,
                        "backtest_recheck",
                        explicit_resume=True,
                    )
                )
                self.assertEqual(
                    action["attemptCount"],
                    self.bridge.EA_FACTORY_ONE_CLICK_PRESTART_RECOVERY_LIMIT,
                )

    def test_visible_retry_budget_allows_only_one_gated_prestart_recovery(self) -> None:
        self.assertEqual(self.bridge.EA_FACTORY_ONE_CLICK_VISIBLE_RETRY_LIMIT, 3)
        self.assertEqual(self.bridge.EA_FACTORY_ONE_CLICK_PRESTART_RECOVERY_LIMIT, 4)
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="backtest_recheck")
        self.assertTrue(
            self.bridge._ea_factory_one_click_reserve_visible_action(
                build,
                build["oneClickRun"],
                "backtest_recheck",
            )
        )
        action = build["oneClickRun"]["visibleAction"]
        action.update({
            "attemptCount": self.bridge.EA_FACTORY_ONE_CLICK_VISIBLE_RETRY_LIMIT,
            "state": "uncertain",
            "lastFailureCode": "tester_input_file_name_identity_invalid",
            "requiresExplicitResume": True,
        })
        build["oneClickRun"]["status"] = "awaiting_visible_terminal"
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_durable_receipt_recovery_available",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_prestart_recovery_available",
                return_value=True,
            ),
        ):
            self.assertTrue(
                self.bridge._ea_factory_one_click_reserve_visible_action(
                    build,
                    build["oneClickRun"],
                    "backtest_recheck",
                    explicit_resume=True,
                )
            )
        self.assertEqual(
            action["attemptCount"],
            self.bridge.EA_FACTORY_ONE_CLICK_PRESTART_RECOVERY_LIMIT,
        )

        action.update({
            "state": "uncertain",
            "lastFailureCode": "tester_input_file_name_identity_invalid",
            "requiresExplicitResume": True,
        })
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_durable_receipt_recovery_available",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_prestart_recovery_available",
                return_value=True,
            ),
        ):
            self.assertFalse(
                self.bridge._ea_factory_one_click_reserve_visible_action(
                    build,
                    build["oneClickRun"],
                    "backtest_recheck",
                    explicit_resume=True,
                )
            )
        self.assertEqual(
            action["attemptCount"],
            self.bridge.EA_FACTORY_ONE_CLICK_PRESTART_RECOVERY_LIMIT,
        )

    def test_mt5_durable_receipt_request_is_forced_to_no_start_recovery(self) -> None:
        build = self.build()
        build["platform"] = "mt5"
        build["oneClickRun"] = self._run(
            build,
            current_stage="backtest_recheck",
        )
        run = build["oneClickRun"]
        run["status"] = "running"
        self.assertTrue(
            self.bridge._ea_factory_one_click_reserve_visible_action(
                build,
                run,
                "backtest_recheck",
            )
        )
        stage = next(
            row for row in build["stages"] if row["id"] == "backtest_recheck"
        )
        with (
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                lambda **_kwargs: {},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_visible_handler",
                return_value=lambda **_kwargs: {},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_terminal_binding_current",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_resolved_front_office_target",
                return_value={},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_default_tester_settings",
                return_value={},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_mt5_backtest_input_binding",
                return_value=({}, {}, {}),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_durable_receipt_recovery_available",
                return_value=True,
            ),
        ):
            request = self.bridge._ea_factory_prepare_visible_front_office_request(
                build,
                stage,
            )
        self.assertEqual(request["safety"]["serviceAction"], "recover_round")
        self.assertTrue(request["safety"]["neverStart"])
        self.assertFalse(request["safety"]["liveTradingAllowed"])

    def test_prestart_recovery_gate_requires_exact_artifacts_and_no_start_boundary(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="backtest_recheck")
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "backtest_recheck",
        )
        run = build["oneClickRun"]
        action = run["visibleAction"]
        action.update({
            "attemptCount": self.bridge.EA_FACTORY_ONE_CLICK_VISIBLE_RETRY_LIMIT,
            "state": "uncertain",
            "lastFailureCode": "tester_input_file_name_identity_invalid",
            "requiresExplicitResume": True,
        })
        run["status"] = "awaiting_visible_terminal"
        operation_id = action["operationId"]
        binding = run["terminalBinding"]
        source_digest = "d" * 64
        binary = {
            "fileName": "Exact_EA_v01.ex4",
            "sha256": "e" * 64,
        }
        preset = {
            "sourceDigest": source_digest,
            "presetDigest": "f" * 64,
            "assumptions": [
                {
                    "inputName": "FixedLot",
                    "inputType": "double",
                    "testerValue": 0.01,
                },
                {
                    "inputName": "UseTrailing",
                    "inputType": "bool",
                    "testerValue": False,
                },
            ],
        }
        tester_settings = {
            "schemaVersion": self.bridge.EA_FACTORY_TESTER_SETTINGS_SCHEMA_VERSION,
            "expertFileName": binary["fileName"],
            "visualMode": True,
            "testerInputPreset": preset,
        }
        safety = {
            "liveTradingAllowed": False,
            "autoTradingMayBeToggled": False,
            "chartAttachmentAllowed": False,
            "terminalShutdownAllowed": False,
            "visualModeRequired": True,
            "optimizationAllowed": False,
        }
        identity_suffix = self.bridge.payload_digest(
            "ea-factory-visible-front-office-stage-v1",
            build["id"],
            "backtest_recheck",
            operation_id,
        )[:24]
        intent = {
            "schemaVersion": "ea-factory-visible-front-office-action-intent-v1",
            "operationId": operation_id,
            "stageId": "backtest_recheck",
            "sourceDigest": source_digest,
            "terminalCandidateId": binding["candidateId"],
            "terminalSelectionRevision": binding["selectionRevision"],
            "terminalBindingDigest": binding["bindingDigest"],
        }
        expert_ui_path = (
            f"Metafxclub\\AgentHQ\\{operation_id}\\Exact_EA_v01"
        )
        action_request = {
            "schemaVersion": "ea-factory-visible-backtest-action-request-v1",
            "protocolVersion": "durable-start-boundary-v1",
            "operationId": operation_id,
            "stageId": "backtest_recheck",
            "buildId": build["id"],
            "missionId": f"mission-eaf-{identity_suffix}",
            "reportId": f"report-eaf-{identity_suffix}",
            "terminalCandidateId": binding["candidateId"],
            "terminalSelectionRevision": binding["selectionRevision"],
            "terminalBindingDigest": binding["bindingDigest"],
            "sourceDigest": source_digest,
            "compiledBinarySha256": binary["sha256"],
            "expertFileName": binary["fileName"],
            "expertUiPathDigest": hashlib.sha256(
                expert_ui_path.encode("utf-8")
            ).hexdigest(),
            "testerSettingsDigest": self.bridge._ea_factory_canonical_json_sha256(
                tester_settings
            ),
            "testerInputPresetDigest": preset["presetDigest"],
            "safetyPolicyDigest": self.bridge._ea_factory_canonical_json_sha256(
                safety
            ),
        }
        action_request["actionRequestDigest"] = (
            self.bridge._ea_factory_canonical_json_sha256(action_request)
        )

        with tempfile.TemporaryDirectory() as temporary:
            build_root = Path(temporary)
            for name in ("Summaries", "Screenshots", "Reports", "Sets"):
                (build_root / name).mkdir()
            summaries = build_root / "Summaries"
            preset_path = build_root / "Sets" / (
                f"{operation_id}-tester-input-preset.set"
            )
            intent_path = summaries / f"{operation_id}-backtest-intent.json"
            request_path = summaries / (
                f"{operation_id}-backtest-action-request.json"
            )
            intent_path.write_text(
                json.dumps(intent, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            request_path.write_text(
                json.dumps(action_request, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            preset_path.write_bytes(
                b"FixedLot=0.01\r\nUseTrailing=false\r\n"
            )
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_build_directory",
                    return_value=build_root,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_backtest_binary",
                    return_value=binary,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_default_tester_settings",
                    return_value=tester_settings,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_file_catalog",
                    return_value=[],
                ),
            ):
                self.assertTrue(
                    self.bridge._ea_factory_one_click_prestart_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                model = self.bridge._ea_factory_one_click_read_model(build)
                self.assertTrue(model["canResume"])
                self.assertEqual(model["visibleAction"]["attemptLimit"], 4)

                legacy_report = build_root / "Reports" / (
                    f"{operation_id}-tester.html"
                )
                legacy_report.write_text("legacy partial report", encoding="utf-8")
                self.assertFalse(
                    self.bridge._ea_factory_one_click_prestart_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                legacy_report.unlink()

                preset_path.write_bytes(
                    b"FixedLot=0.02\r\nUseTrailing=false\r\n"
                )
                self.assertFalse(
                    self.bridge._ea_factory_one_click_prestart_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                preset_path.write_bytes(
                    b"FixedLot=0.01\r\nUseTrailing=false\r\n"
                )

                boundary = summaries / (
                    f"{operation_id}-backtest-start-boundary.json"
                )
                boundary.write_text("{}", encoding="utf-8")
                self.assertFalse(
                    self.bridge._ea_factory_one_click_prestart_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                blocked_model = self.bridge._ea_factory_one_click_read_model(build)
                self.assertFalse(blocked_model["canResume"])
                self.assertEqual(blocked_model["visibleAction"]["attemptLimit"], 3)

                expected_boundary = {
                    "schemaVersion": "ea-factory-tester-start-boundary-v1",
                    "operationId": operation_id,
                    "stageId": "backtest_recheck",
                    "actionRequestDigest": action_request["actionRequestDigest"],
                }
                boundary.write_text(
                    json.dumps(expected_boundary, sort_keys=True, separators=(",", ":")),
                    encoding="utf-8",
                )
                png = b"\x89PNG\r\n\x1a\n" + (b"\x00" * 1016)
                (build_root / "Screenshots" / f"{operation_id}-tester-settings.png").write_bytes(png)
                (build_root / "Screenshots" / f"{operation_id}-tester-input-preset.png").write_bytes(png)
                (build_root / "Sets" / f"{operation_id}-tester-input-readback.set").write_bytes(
                    b"FixedLot=0.01\r\nUseTrailing=false\r\n"
                )
                action.update({
                    "attemptCount": self.bridge.EA_FACTORY_ONE_CLICK_PRESTART_RECOVERY_LIMIT,
                    "state": "uncertain",
                    "lastFailureCode": "visible_ui_timeout",
                    "requiresExplicitResume": True,
                })
                self.assertTrue(
                    self.bridge._ea_factory_one_click_inflight_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                legacy_report.write_text("legacy partial report", encoding="utf-8")
                self.assertFalse(
                    self.bridge._ea_factory_one_click_inflight_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                legacy_report.unlink()
                for collection_failure in (
                    "control_1034_ambiguous",
                    "tester_settings_tab_unavailable",
                    "tester_settings_tab_strip_ambiguous",
                    "tester_settings_tab_strip_invalid",
                    "tester_settings_tab_scan_binding_changed",
                    "tester_settings_start_ambiguous",
                    "tester_settings_start_binding_mismatch",
                ):
                    action["lastFailureCode"] = collection_failure
                    self.assertTrue(
                        self.bridge._ea_factory_one_click_inflight_recovery_available(
                            build,
                            "backtest_recheck",
                            action,
                        ),
                        collection_failure,
                    )
                action["lastFailureCode"] = "visible_ui_timeout"
                inflight_model = self.bridge._ea_factory_one_click_read_model(build)
                self.assertTrue(inflight_model["canResume"])
                self.assertEqual(inflight_model["visibleAction"]["attemptLimit"], 4)
                self.assertTrue(
                    self.bridge._ea_factory_one_click_reserve_visible_action(
                        build,
                        run,
                        "backtest_recheck",
                        explicit_resume=True,
                    )
                )
                self.assertEqual(action["attemptCount"], 4)

                action.update({
                    "state": "uncertain",
                    "lastFailureCode": "visible_ui_timeout",
                    "requiresExplicitResume": True,
                })
                result_path = build_root / "Screenshots" / (
                    f"{operation_id}-tester-result.png"
                )
                report_proof_path = build_root / "Screenshots" / (
                    f"{operation_id}-tester-report.png"
                )
                report_path = build_root / "Reports" / (
                    f"{operation_id}-tester.htm"
                )
                collected_response_path = summaries / (
                    f"{operation_id}-backtest-ui-collected-recovery.json"
                )
                result_path.write_bytes(png)
                report_proof_path.write_bytes(png)
                valid_report = (
                    b"<!DOCTYPE html><html><body><table>"
                    + (b"x" * 1024)
                    + b"</table></body></html>"
                )
                report_path.write_bytes(valid_report)
                self.assertTrue(
                    self.bridge._ea_factory_one_click_collected_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                collected_model = self.bridge._ea_factory_one_click_read_model(build)
                self.assertTrue(collected_model["canResume"])
                self.assertTrue(
                    self.bridge._ea_factory_one_click_reserve_visible_action(
                        build,
                        run,
                        "backtest_recheck",
                        explicit_resume=True,
                    )
                )
                self.assertEqual(
                    action["attemptCount"],
                    self.bridge.EA_FACTORY_ONE_CLICK_PRESTART_RECOVERY_LIMIT,
                )
                action.update({
                    "state": "uncertain",
                    "lastFailureCode": "tester_report_path_not_committed",
                    "requiresExplicitResume": True,
                })

                for conflicting_output_path in (
                    summaries / f"{operation_id}-backtest-receipt.json",
                    summaries / f"{operation_id}-backtest-ui.json",
                    summaries / f"{operation_id}-backtest-ui-inflight-recovery.json",
                    summaries / f"{operation_id}-backtest-ui-completed-recovery.json",
                    collected_response_path,
                ):
                    conflicting_output_path.write_text("{}", encoding="utf-8")
                    self.assertFalse(
                        self.bridge._ea_factory_one_click_collected_recovery_available(
                            build,
                            "backtest_recheck",
                            action,
                        ),
                        conflicting_output_path.name,
                    )
                    conflicting_output_path.unlink()

                legacy_report.write_text("legacy partial report", encoding="utf-8")
                self.assertFalse(
                    self.bridge._ea_factory_one_click_collected_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                legacy_report.unlink()

                report_proof_path.unlink()
                self.assertFalse(
                    self.bridge._ea_factory_one_click_collected_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                report_proof_path.write_bytes(png)

                readback_path = build_root / "Sets" / (
                    f"{operation_id}-tester-input-readback.set"
                )
                readback_bytes = readback_path.read_bytes()
                readback_path.write_bytes(
                    b"FixedLot=0.02\r\nUseTrailing=false\r\n"
                )
                self.assertFalse(
                    self.bridge._ea_factory_one_click_collected_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                readback_path.write_bytes(readback_bytes)

                report_path.write_bytes(b"not-html" + (b"x" * 1024))
                self.assertFalse(
                    self.bridge._ea_factory_one_click_collected_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                report_path.write_bytes(valid_report)

                report_path.unlink()
                report_path.mkdir()
                self.assertFalse(
                    self.bridge._ea_factory_one_click_collected_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                report_path.rmdir()
                report_path.write_bytes(valid_report)

                boundary_epoch = boundary.stat().st_mtime
                too_old = boundary_epoch - 5
                os.utime(report_path, (too_old, too_old))
                self.assertFalse(
                    self.bridge._ea_factory_one_click_collected_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                future = time.time() + 120
                os.utime(report_path, (future, future))
                self.assertFalse(
                    self.bridge._ea_factory_one_click_collected_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                os.utime(report_path, None)

                result_path.unlink()
                report_proof_path.unlink()
                report_path.unlink()
                boundary.write_text("{}", encoding="utf-8")
                self.assertFalse(
                    self.bridge._ea_factory_one_click_inflight_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                boundary.unlink()

                action["lastFailureCode"] = "unknown_visible_failure"
                self.assertFalse(
                    self.bridge._ea_factory_one_click_prestart_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )

    def test_visible_front_office_actions_are_serialized_across_builds(self) -> None:
        operation_id = "ea-visible-333333333333333333333333"
        request = {
            "stageId": "compile_validate",
            "platform": "mt4",
            "terminalBinding": {
                "platform": "mt4",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "visibleOperation": {"operationId": operation_id},
        }
        capability = {
            "ready": True,
            "freshProcessProbe": True,
            "foregroundInteraction": True,
            "visibleEvidenceCapture": True,
            "terminalSelectionBound": True,
            "liveTradingAllowed": False,
            "terminalProcessMayRemainOpen": True,
            "processAndWindowBinding": True,
            "idempotentOperationBinding": True,
            "durableReceiptRecovery": True,
            "terminalShutdownAllowed": False,
            "autoTradingMayBeToggled": False,
            "chartAttachmentAllowed": False,
            "visibleMetaEditorCompile": True,
        }
        started = threading.Event()
        release = threading.Event()
        outcomes: list[object] = []

        def handler(*, request):
            started.set()
            self.assertTrue(release.wait(timeout=5))
            return {
                "schemaVersion": self.bridge.EA_FACTORY_VISIBLE_RESULT_SCHEMA_VERSION,
                "operationId": operation_id,
                "metrics": {"compileVerified": True},
                "artifactSpecifications": [
                    {"alias": "compiled_binary", "relativePath": "EA_Versions/test.ex4", "artifactKind": "compile_evidence"},
                    {"alias": "visible_window", "relativePath": "Screenshots/compile.png", "artifactKind": "screenshot_evidence"},
                    {"alias": "compile_log", "relativePath": "Reports/compile.txt", "artifactKind": "compile_evidence"},
                    {"alias": "adapter_receipt", "relativePath": "Reports/compile.json", "artifactKind": "compile_evidence"},
                ],
            }

        def first_worker():
            try:
                outcomes.append(
                    self.bridge._ea_factory_invoke_visible_front_office_handler(
                        copy.deepcopy(request)
                    )
                )
            except Exception as error:  # pragma: no cover - asserted below
                outcomes.append(error)

        provider = mock.Mock(return_value=capability)
        visible_handler = mock.Mock(side_effect=handler)
        with (
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER",
                visible_handler,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                provider,
            ),
        ):
            worker = threading.Thread(target=first_worker, daemon=True)
            worker.start()
            self.assertTrue(started.wait(timeout=5))
            with self.assertRaises(self.bridge.RequestError) as busy:
                self.bridge._ea_factory_invoke_visible_front_office_handler(
                    copy.deepcopy(request)
                )
            self.assertEqual(busy.exception.status, 409)
            release.set()
            worker.join(timeout=5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(outcomes), 1)
        self.assertIsInstance(outcomes[0], dict)
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(visible_handler.call_count, 1)

    def test_visible_adapter_failure_preserves_bounded_public_reason_code(self) -> None:
        operation_id = "ea-visible-444444444444444444444444"
        request = {
            "stageId": "compile_validate",
            "platform": "mt4",
            "terminalBinding": {
                "platform": "mt4",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "visibleOperation": {"operationId": operation_id},
        }
        capability = {
            "ready": True,
            "freshProcessProbe": True,
            "foregroundInteraction": True,
            "visibleEvidenceCapture": True,
            "terminalSelectionBound": True,
            "liveTradingAllowed": False,
            "terminalProcessMayRemainOpen": True,
            "processAndWindowBinding": True,
            "idempotentOperationBinding": True,
            "durableReceiptRecovery": True,
            "terminalShutdownAllowed": False,
            "autoTradingMayBeToggled": False,
            "chartAttachmentAllowed": False,
            "visibleMetaEditorCompile": True,
        }
        failure = self.bridge.VisibleTerminalAdapterError(
            "visible_ui_timeout",
            retryable=True,
        )
        with (
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER",
                side_effect=failure,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                return_value=capability,
            ),
        ):
            with self.assertRaises(self.bridge.RequestError) as raised:
                self.bridge._ea_factory_invoke_visible_front_office_handler(
                    request,
                )
        self.assertEqual(raised.exception.status, 503)
        self.assertEqual(raised.exception.code, "visible_ui_timeout")
        self.assertTrue(raised.exception.retryable)

    def test_visible_handler_owns_and_propagates_evidence_received_at(self) -> None:
        operation_id = "ea-visible-evidence-arrival-time"
        request = {
            "stageId": "compile_validate",
            "platform": "mt4",
            "terminalBinding": {
                "platform": "mt4",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "visibleOperation": {"operationId": operation_id},
        }
        capability = {
            "ready": True,
            "freshProcessProbe": True,
            "foregroundInteraction": True,
            "visibleEvidenceCapture": True,
            "terminalSelectionBound": True,
            "liveTradingAllowed": False,
            "terminalProcessMayRemainOpen": True,
            "processAndWindowBinding": True,
            "idempotentOperationBinding": True,
            "durableReceiptRecovery": True,
            "terminalShutdownAllowed": False,
            "autoTradingMayBeToggled": False,
            "chartAttachmentAllowed": False,
            "visibleMetaEditorCompile": True,
        }
        raw = {
            "schemaVersion": self.bridge.EA_FACTORY_VISIBLE_RESULT_SCHEMA_VERSION,
            "operationId": operation_id,
            "metrics": {"evidenceReceivedAt": "2099-01-01T00:00:00+00:00"},
            "artifactSpecifications": [
                {"alias": "compiled_binary", "relativePath": "EA_Versions/test.ex4", "artifactKind": "compile_evidence"},
                {"alias": "visible_window", "relativePath": "Screenshots/compile.png", "artifactKind": "screenshot_evidence"},
                {"alias": "compile_log", "relativePath": "Reports/compile.txt", "artifactKind": "compile_evidence"},
                {"alias": "adapter_receipt", "relativePath": "Reports/compile.json", "artifactKind": "compile_evidence"},
            ],
        }
        capability_time = "2026-10-15T08:26:00+00:00"
        received_time = "2026-10-15T08:26:09.924000+00:00"
        with (
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER",
                return_value=raw,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                return_value=capability,
            ),
            mock.patch.object(
                self.bridge,
                "utc_now",
                side_effect=[capability_time, received_time],
            ),
        ):
            result = self.bridge._ea_factory_invoke_visible_front_office_handler_unlocked(
                request
            )

        self.assertEqual(
            result["backendInvocation"],
            {
                "capabilityCheckedAt": capability_time,
                "evidenceReceivedAt": received_time,
            },
        )
        build = self.build()
        build["oneClickRun"] = self._run(
            build,
            current_stage="compile_validate",
        )
        artifact_rows = [
            {"fileId": f"ea-file-{index}", "sha256": str(index) * 64}
            for index in range(1, 5)
        ]
        stored = self.bridge._ea_factory_visible_result_metrics(
            build,
            "compile_validate",
            request,
            result,
            artifact_rows,
        )
        self.assertEqual(stored["evidenceReceivedAt"], received_time)
        self.assertNotEqual(
            stored["evidenceReceivedAt"],
            raw["metrics"]["evidenceReceivedAt"],
        )

    def test_post_process_freshness_uses_backend_receipt_time(self) -> None:
        now = self.bridge.datetime.now(self.bridge.timezone.utc)
        capability_checked_at = now - self.bridge.timedelta(seconds=40)
        evidence_received_at = now - self.bridge.timedelta(seconds=30)
        post_observed_at = evidence_received_at - self.bridge.timedelta(seconds=1)
        metrics = {
            "recoveredExistingReceipt": False,
            "evidenceReceivedAt": evidence_received_at.isoformat(),
        }
        post_binding = {"observedAt": post_observed_at.isoformat()}

        # Commit is already over 15 seconds after observation, but the bridge
        # received the evidence one second after it was observed.
        self.assertGreater(
            now - post_observed_at,
            self.bridge.timedelta(
                seconds=self.bridge.EA_FACTORY_FRONT_OFFICE_PROBE_FRESH_SECONDS
            ),
        )
        self.assertTrue(
            self.bridge._ea_factory_post_process_binding_fresh_on_receipt(
                metrics,
                post_binding,
                capability_checked_at,
                require_fresh=True,
            )
        )

        rejected = {
            "stale_on_arrival": (
                metrics,
                {
                    "observedAt": (
                        evidence_received_at
                        - self.bridge.timedelta(
                            seconds=self.bridge.EA_FACTORY_FRONT_OFFICE_PROBE_FRESH_SECONDS
                            + 1
                        )
                    ).isoformat()
                },
                capability_checked_at,
            ),
            "post_observation_future_of_receipt": (
                metrics,
                {
                    "observedAt": (
                        evidence_received_at + self.bridge.timedelta(seconds=3)
                    ).isoformat()
                },
                capability_checked_at,
            ),
            "receipt_time_future_of_backend": (
                {
                    **metrics,
                    "evidenceReceivedAt": (
                        now + self.bridge.timedelta(seconds=3)
                    ).isoformat(),
                },
                {"observedAt": now.isoformat()},
                capability_checked_at,
            ),
            "receipt_before_capability": (
                {
                    **metrics,
                    "evidenceReceivedAt": (
                        capability_checked_at - self.bridge.timedelta(seconds=1)
                    ).isoformat(),
                },
                {
                    "observedAt": (
                        capability_checked_at - self.bridge.timedelta(seconds=1)
                    ).isoformat()
                },
                capability_checked_at,
            ),
            "malformed_receipt_time": (
                {**metrics, "evidenceReceivedAt": "tampered"},
                post_binding,
                capability_checked_at,
            ),
        }
        for name, (candidate_metrics, candidate_binding, checked_at) in rejected.items():
            with self.subTest(case=name):
                self.assertFalse(
                    self.bridge._ea_factory_post_process_binding_fresh_on_receipt(
                        candidate_metrics,
                        candidate_binding,
                        checked_at,
                        require_fresh=True,
                    )
                )

        self.assertTrue(
            self.bridge._ea_factory_post_process_binding_fresh_on_receipt(
                {"recoveredExistingReceipt": True},
                {"observedAt": "2020-01-01T00:00:00+00:00"},
                capability_checked_at,
                require_fresh=True,
            )
        )

    def test_mt5_no_start_recovery_requires_exact_lifecycle_tuple(self) -> None:
        metrics = {
            "platform": "mt5",
            "backtestExecuted": False,
            "recoveredExistingReceipt": False,
            "recoveredWithoutStart": True,
            "startInvoked": False,
            "recoveryIssuedStart": False,
        }
        self.assertTrue(
            self.bridge._ea_factory_mt5_recovered_without_start_valid(metrics)
        )
        tampered_values = {
            "platform": "mt4",
            "backtestExecuted": True,
            "recoveredExistingReceipt": True,
            "recoveredWithoutStart": False,
            "startInvoked": True,
            "recoveryIssuedStart": True,
        }
        for field, value in tampered_values.items():
            with self.subTest(field=field):
                tampered = copy.deepcopy(metrics)
                tampered[field] = value
                self.assertFalse(
                    self.bridge._ea_factory_mt5_recovered_without_start_valid(
                        tampered
                    )
                )
        for field in metrics:
            with self.subTest(missing=field):
                missing = copy.deepcopy(metrics)
                missing.pop(field)
                self.assertFalse(
                    self.bridge._ea_factory_mt5_recovered_without_start_valid(
                        missing
                    )
                )

    def test_mt5_no_start_recovery_is_cross_bound_to_adapter_receipt(self) -> None:
        receipt = {
            "schemaVersion": "ea-factory-visible-front-office-receipt-v1",
            "operationId": "ea-visible-recovery-contract",
            "stageId": "backtest_recheck",
            "terminalCandidateId": "mtc-recovery-contract",
            "status": "verified",
            "processBindingDigest": "1" * 64,
            "postProcessBindingDigest": "2" * 64,
            "sourceDigest": "3" * 64,
            "compiledBinarySha256": "4" * 64,
            "visualMode": True,
            "optimizationEnabled": False,
            "shutdownTerminalAfterTest": False,
            "liveTradingExecuted": False,
            "recoveredWithoutStart": True,
            "startInvoked": False,
            "recoveryIssuedStart": False,
        }

        def valid(value: dict) -> bool:
            return self.bridge._ea_factory_visible_receipt_valid(
                json.dumps(value).encode("utf-8"),
                stage_id="backtest_recheck",
                operation_id="ea-visible-recovery-contract",
                terminal_candidate_id="mtc-recovery-contract",
                process_binding_digest="1" * 64,
                post_process_binding_digest="2" * 64,
                source_digest="3" * 64,
                compiled_binary_sha256="4" * 64,
                recovered_without_start=True,
                start_invoked=False,
                recovery_issued_start=False,
            )

        self.assertTrue(valid(receipt))
        for field, value in {
            "recoveredWithoutStart": False,
            "startInvoked": True,
            "recoveryIssuedStart": True,
        }.items():
            with self.subTest(field=field):
                tampered = copy.deepcopy(receipt)
                tampered[field] = value
                self.assertFalse(valid(tampered))

    def test_mt5_backtest_receipt_cryptographically_binds_completion_proof(self) -> None:
        operation_id = "ea-visible-mt5-completion-proof"
        binary_digest = "4" * 64
        expert_file_name = "BoundExpert.ex5"
        deployment_ref = "mt5deploy_" + "a" * 24
        deployment = {
            "deploymentRef": deployment_ref,
            "expertFileName": expert_file_name,
            "binarySha256": binary_digest,
            "bindingDigest": "b" * 64,
        }
        resolved_settings = {
            "expertFileName": expert_file_name,
            "symbol": "EURUSD",
            "period": "H1",
        }
        mt5_input_binding = {
            "inputManifestDigest": "c" * 64,
            "refDigest": "d" * 64,
            "expectedReadbackEntriesDigest": "e" * 64,
        }

        def text_sha256(value: str) -> str:
            return hashlib.sha256(value.encode("utf-8")).hexdigest()

        start_log_path = "1" * 64
        completion_log_path = "2" * 64
        start_source = "3" * 64
        completion_source = "5" * 64
        core_sources = sorted({start_source, completion_source})
        completion_thread = text_sha256(
            f"{completion_log_path}\n{completion_source}"
        )
        core_threads = [completion_thread]
        expert_ui_path = (
            "Metafxclub\\AgentHQ\\Deployments\\"
            f"{deployment_ref}\\{Path(expert_file_name).stem}"
        )
        expert_ui_path_digest = text_sha256(expert_ui_path)
        expert_symbol_period_digest = text_sha256("\n".join((
            expert_file_name,
            binary_digest,
            expert_ui_path_digest,
            resolved_settings["symbol"],
            resolved_settings["period"],
        )))
        log_identity_digest = text_sha256("\n".join((
            start_log_path,
            completion_log_path,
            start_source,
            completion_source,
        )))
        core_sources_digest = text_sha256("\n".join(core_sources))
        core_threads_digest = text_sha256("\n".join(core_threads))
        start_line_digest = "6" * 64
        completion_line_digest = "7" * 64
        start_ordinal = 41
        completion_ordinal = 9
        execution_thread_digest = text_sha256("\n".join((
            log_identity_digest,
            str(start_ordinal),
            str(completion_ordinal),
            core_threads_digest,
        )))
        run_identity_digest = text_sha256("\n".join((
            operation_id,
            "thread_finished",
            expert_symbol_period_digest,
            log_identity_digest,
            core_sources_digest,
            core_threads_digest,
            start_line_digest,
            completion_line_digest,
            str(start_ordinal),
            str(completion_ordinal),
            "",
        )))
        now = datetime.now(timezone.utc)
        evidence = {
            "schemaVersion": "ea-factory-mt5-tester-completion-evidence-v2",
            "source": "fresh_tester_log_completion",
            "boundaryCreatedAt": (now - timedelta(minutes=3)).isoformat(),
            "runStartedAt": (now - timedelta(minutes=2)).isoformat(),
            "runCompletedAt": (now - timedelta(minutes=1)).isoformat(),
            "startLineSha256": start_line_digest,
            "completionLineSha256": completion_line_digest,
            "completionMarker": "thread_finished",
            # Production may start in the terminal journal and finish in an
            # agent journal. The identity digests, not path equality, bind it.
            "startLogPathSha256": start_log_path,
            "completionLogPathSha256": completion_log_path,
            "startSourceSha256": start_source,
            "completionSourceSha256": completion_source,
            "coreSourceCount": len(core_sources),
            "coreSourceSha256s": core_sources,
            "coreSourcesSha256": core_sources_digest,
            "coreThreadCount": len(core_threads),
            "coreThreadIdentitySha256s": core_threads,
            "coreThreadIdentitiesSha256": core_threads_digest,
            "startLineOrdinal": start_ordinal,
            "completionLineOrdinal": completion_ordinal,
            "expertUiPathSha256": expert_ui_path_digest,
            "deployedExpertSha256": binary_digest,
            "expertSymbolPeriodSha256": expert_symbol_period_digest,
            "logIdentitySha256": log_identity_digest,
            "executionThreadIdentitySha256": execution_thread_digest,
            "runIdentitySha256": run_identity_digest,
            "completionPassCount": None,
            "coreDisconnectObserved": False,
            "verified": True,
        }

        def canonical_digest(value: object) -> str:
            return hashlib.sha256(json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")).hexdigest()

        evidence_digest = canonical_digest(evidence)
        resolved_digest = self.bridge.payload_digest(
            "ea-factory-resolved-tester-settings-v1",
            resolved_settings,
        )
        receipt = {
            "schemaVersion": "ea-factory-visible-front-office-receipt-v1",
            "operationId": operation_id,
            "stageId": "backtest_recheck",
            "platform": "mt5",
            "terminalCandidateId": "mtc-completion-proof",
            "status": "verified",
            "processBindingDigest": "8" * 64,
            "postProcessBindingDigest": "9" * 64,
            "sourceDigest": "0" * 64,
            "compiledBinarySha256": binary_digest,
            "resolvedTesterSettings": copy.deepcopy(resolved_settings),
            "resolvedTesterSettingsDigest": resolved_digest,
            "testerInputManifestDigest": mt5_input_binding[
                "inputManifestDigest"
            ],
            "testerInputPresetRefDigest": mt5_input_binding["refDigest"],
            "testerInputExpectedReadbackEntriesDigest": mt5_input_binding[
                "expectedReadbackEntriesDigest"
            ],
            "testerInputReadbackEntriesDigest": mt5_input_binding[
                "expectedReadbackEntriesDigest"
            ],
            "compiledDeploymentRef": deployment_ref,
            "compiledDeploymentDigest": deployment["bindingDigest"],
            "testerCompletionEvidence": copy.deepcopy(evidence),
            "testerCompletionEvidenceDigest": evidence_digest,
            "testerCompletionEvidenceCheckpointSha256": evidence_digest,
            "visualMode": True,
            "optimizationEnabled": False,
            "shutdownTerminalAfterTest": False,
            "liveTradingExecuted": False,
        }

        def valid(
            receipt_value: dict,
            *,
            metrics_evidence: object = evidence,
            metrics_digest: object = evidence_digest,
            metrics_checkpoint_digest: object = evidence_digest,
        ) -> bool:
            return self.bridge._ea_factory_visible_receipt_valid(
                json.dumps(receipt_value).encode("utf-8"),
                stage_id="backtest_recheck",
                operation_id=operation_id,
                terminal_candidate_id="mtc-completion-proof",
                process_binding_digest="8" * 64,
                post_process_binding_digest="9" * 64,
                source_digest="0" * 64,
                compiled_binary_sha256=binary_digest,
                resolved_tester_settings_digest=resolved_digest,
                resolved_tester_settings=resolved_settings,
                mt5_input_binding=mt5_input_binding,
                compiled_deployment=deployment,
                platform="mt5",
                tester_completion_evidence=metrics_evidence,
                tester_completion_evidence_digest=metrics_digest,
                tester_completion_evidence_checkpoint_sha256=(
                    metrics_checkpoint_digest
                ),
                expert_file_name=expert_file_name,
            )

        self.assertTrue(valid(receipt))

        for missing_field in (
            "testerCompletionEvidence",
            "testerCompletionEvidenceDigest",
            "testerCompletionEvidenceCheckpointSha256",
        ):
            with self.subTest(missing_receipt_field=missing_field):
                missing = copy.deepcopy(receipt)
                missing.pop(missing_field)
                self.assertFalse(valid(missing))

        stale_digest = copy.deepcopy(receipt)
        stale_digest["testerCompletionEvidence"]["completionLineSha256"] = (
            "f" * 64
        )
        self.assertFalse(valid(stale_digest))

        coherent_outer_digests = copy.deepcopy(receipt)
        coherent_outer_digests["testerCompletionEvidence"][
            "completionLineSha256"
        ] = "f" * 64
        forged_digest = canonical_digest(
            coherent_outer_digests["testerCompletionEvidence"]
        )
        coherent_outer_digests["testerCompletionEvidenceDigest"] = forged_digest
        coherent_outer_digests[
            "testerCompletionEvidenceCheckpointSha256"
        ] = forged_digest
        self.assertFalse(valid(
            coherent_outer_digests,
            metrics_evidence=coherent_outer_digests[
                "testerCompletionEvidence"
            ],
            metrics_digest=forged_digest,
            metrics_checkpoint_digest=forged_digest,
        ))

        checkpoint_tampered = copy.deepcopy(receipt)
        checkpoint_tampered[
            "testerCompletionEvidenceCheckpointSha256"
        ] = "f" * 64
        self.assertFalse(valid(
            checkpoint_tampered,
            metrics_checkpoint_digest="f" * 64,
        ))

        self.assertFalse(valid(
            receipt,
            metrics_evidence={**evidence, "verified": False},
        ))
        self.assertFalse(valid(receipt, metrics_evidence=None))
        self.assertFalse(valid(receipt, metrics_digest="f" * 64))
        self.assertFalse(valid(receipt, metrics_digest=None))
        self.assertFalse(valid(
            receipt,
            metrics_checkpoint_digest="f" * 64,
        ))
        self.assertFalse(valid(receipt, metrics_checkpoint_digest=None))

    def test_legacy_mt4_backtest_receipt_does_not_require_mt5_completion_proof(
        self,
    ) -> None:
        receipt = {
            "schemaVersion": "ea-factory-visible-front-office-receipt-v1",
            "operationId": "ea-visible-mt4-legacy-proof",
            "stageId": "backtest_recheck",
            "terminalCandidateId": "mtc-mt4-legacy-proof",
            "status": "verified",
            "processBindingDigest": "1" * 64,
            "postProcessBindingDigest": "2" * 64,
            "sourceDigest": "3" * 64,
            "compiledBinarySha256": "4" * 64,
            "visualMode": True,
            "optimizationEnabled": False,
            "shutdownTerminalAfterTest": False,
            "liveTradingExecuted": False,
        }
        self.assertTrue(self.bridge._ea_factory_visible_receipt_valid(
            json.dumps(receipt).encode("utf-8"),
            stage_id="backtest_recheck",
            operation_id="ea-visible-mt4-legacy-proof",
            terminal_candidate_id="mtc-mt4-legacy-proof",
            process_binding_digest="1" * 64,
            post_process_binding_digest="2" * 64,
            source_digest="3" * 64,
            compiled_binary_sha256="4" * 64,
            platform="mt4",
        ))

    def test_visible_receipt_allows_only_contract_owned_positive_process_ids(self) -> None:
        receipt = {
            "schemaVersion": "ea-factory-visible-front-office-receipt-v1",
            "operationId": "ea-visible-compile-receipt",
            "stageId": "compile_validate",
            "terminalCandidateId": "mtc-compile-receipt",
            "status": "verified",
            "processBindingDigest": "1" * 64,
            "postProcessBindingDigest": "2" * 64,
            "sourceDigest": "3" * 64,
            "compiledBinarySha256": "4" * 64,
            "processBinding": {
                "terminalProcessId": 102,
                "terminalWindowOwnerProcessId": 102,
                "frontOfficeProcessId": 103,
                "frontOfficeWindowOwnerProcessId": 103,
            },
            "postProcessBinding": {
                "terminalProcessId": 102,
                "terminalWindowOwnerProcessId": 102,
                "frontOfficeProcessId": 103,
                "frontOfficeWindowOwnerProcessId": 103,
            },
            "zeroErrors": True,
            "zeroWarnings": True,
            "liveTradingExecuted": False,
        }

        def valid(value: dict) -> bool:
            return self.bridge._ea_factory_visible_receipt_valid(
                json.dumps(value).encode("utf-8"),
                stage_id="compile_validate",
                operation_id="ea-visible-compile-receipt",
                terminal_candidate_id="mtc-compile-receipt",
                process_binding_digest="1" * 64,
                post_process_binding_digest="2" * 64,
                source_digest="3" * 64,
                compiled_binary_sha256="4" * 64,
            )

        self.assertTrue(valid(receipt))

        tampered_cases = {
            "string_pid": ("processBinding", "terminalProcessId", "102"),
            "zero_pid": ("processBinding", "frontOfficeProcessId", 0),
            "unknown_pid_key": ("processBinding", "workerProcessId", 104),
            "account_identifier": ("processBinding", "accountNumber", 123456),
            "public_metrics_pid": ("processBinding", "processId", 101),
        }
        for name, (container, field, value) in tampered_cases.items():
            with self.subTest(case=name):
                tampered = copy.deepcopy(receipt)
                tampered[container][field] = value
                self.assertFalse(valid(tampered))

    def test_backtest_evidence_accepts_consistent_zero_with_attention_and_nonzero(self) -> None:
        build = self.build()
        build["blueprintCoverageManifest"] = self.compact_ea_manifest()
        build["versions"] = [{
            "sourceDigest": "d" * 64,
            "versionFile": "EA_Versions/CAN_SLIM.mq4",
        }]
        stage = next(row for row in build["stages"] if row["id"] == "backtest_recheck")
        stage.update({
            "status": "completed",
            "evidenceVerified": True,
            "missionId": "mission-backtest",
            "reportId": "report-backtest",
            "artifacts": [
                "shot-settings",
                "shot-result",
                "shot-report-proof",
                "tester-report",
                "adapter-receipt",
            ],
            "terminalExecutableSha256": "4" * 64,
            "frontOfficeExecutableSha256": "4" * 64,
        })
        build["oneClickRun"] = self._run(build, current_stage="backtest_recheck")
        operation_id = self.bridge._ea_factory_one_click_visible_operation_id(
            build,
            build["oneClickRun"],
            "backtest_recheck",
        )
        manifest = [
            {"fileId": "binary", "fileName": "CAN_SLIM.ex4", "stageId": "compile_validate", "reportId": "report-compile", "artifactKind": "compile_evidence", "extension": ".ex4", "sha256": "e" * 64},
            {"fileId": "shot-settings", "stageId": "backtest_recheck", "reportId": "report-backtest", "artifactKind": "screenshot_evidence", "extension": ".png", "sha256": "1" * 64},
            {"fileId": "shot-result", "stageId": "backtest_recheck", "reportId": "report-backtest", "artifactKind": "screenshot_evidence", "extension": ".png", "sha256": "2" * 64},
            {"fileId": "shot-report-proof", "stageId": "backtest_recheck", "reportId": "report-backtest", "artifactKind": "screenshot_evidence", "extension": ".png", "sha256": "9" * 64},
            {"fileId": "tester-report", "stageId": "backtest_recheck", "reportId": "report-backtest", "artifactKind": "backtest_evidence", "extension": ".html", "sha256": "3" * 64},
            {"fileId": "adapter-receipt", "stageId": "backtest_recheck", "reportId": "report-backtest", "artifactKind": "backtest_evidence", "extension": ".json", "sha256": "a" * 64},
        ]
        stage_entries = manifest[1:]
        tester_request = {
            "schemaVersion": self.bridge.EA_FACTORY_TESTER_SETTINGS_SCHEMA_VERSION,
            "expertFileName": "CAN_SLIM.ex4",
            "symbolPolicy": "current_tester_selection_required",
            "period": "H1",
            "model": "every_tick",
            "spreadPolicy": "current",
            "useDate": False,
            "fromDate": None,
            "toDate": None,
            "depositPolicy": "current_tester_deposit",
            "visualMode": True,
            "optimizationEnabled": False,
            "shutdownTerminalAfterTest": False,
            "liveTradingAllowed": False,
        }
        tester_request_digest = self.bridge.payload_digest(
            "ea-factory-tester-settings-request-v1",
            tester_request,
        )
        stage["testerSettingsRequestDigest"] = tester_request_digest
        process_binding = {
            "schemaVersion": "ea-factory-front-office-process-binding-v1",
            "observedAt": "2026-09-11T00:00:00Z",
            "stageId": "backtest_recheck",
            "terminalCandidateId": "mtc-one-click-terminal",
            "terminalSelectionRevision": 7,
            "terminalBindingDigest": "c" * 64,
            "terminalProcessId": 123,
            "terminalExecutableSha256": "4" * 64,
            "terminalWindowHandle": 456,
            "terminalWindowOwnerProcessId": 123,
            "terminalWindowTitleSha256": "5" * 64,
            "terminalWindowClassSha256": "6" * 64,
            "frontOfficeKind": "strategy_tester",
            "frontOfficeProcessId": 123,
            "frontOfficeExecutableSha256": "4" * 64,
            "frontOfficeWindowHandle": 456,
            "frontOfficeWindowOwnerProcessId": 123,
            "frontOfficeWindowTitleSha256": "7" * 64,
            "frontOfficeWindowClassSha256": "8" * 64,
            "processBindingDigest": "",
        }
        process_binding["processBindingDigest"] = (
            self.bridge._ea_factory_front_office_process_binding_digest(
                process_binding
            )
        )
        metrics = {
            "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "operationId": operation_id,
            "eaFactoryStage": "backtest_recheck",
            "platform": "mt4",
            "terminalCandidateId": "mtc-one-click-terminal",
            "terminalSelectionRevision": 7,
            "terminalBindingDigest": "c" * 64,
            "processBinding": copy.deepcopy(process_binding),
            "processBindingDigest": process_binding["processBindingDigest"],
            "postProcessBinding": copy.deepcopy(process_binding),
            "postProcessBindingDigest": process_binding["processBindingDigest"],
            "liveTradingExecuted": False,
            "autoTradingToggled": False,
            "autoTradingStateBefore": True,
            "autoTradingStateAfter": True,
            "chartAttached": False,
            "terminalClosedByAdapter": False,
            "terminalStillRunning": True,
            "terminalStillOpen": True,
            "processId": 123,
            "windowHandle": 456,
            "capabilityCheckedAt": "2026-09-11T00:00:00Z",
            "evidenceArtifactIds": list(stage["artifacts"]),
            "stageArtifactManifestDigest": self.bridge._ea_factory_visible_stage_manifest_digest(stage_entries),
            "sourceDigest": "d" * 64,
            "compiledBinaryFileId": "binary",
            "compiledBinarySha256": "e" * 64,
            "visibleWindowEvidenceFileId": "shot-result",
            "visibleWindowEvidenceSha256": "2" * 64,
            "settingsScreenshotFileId": "shot-settings",
            "settingsScreenshotSha256": "1" * 64,
            "resultScreenshotFileId": "shot-result",
            "resultScreenshotSha256": "2" * 64,
            "reportScreenshotFileId": "shot-report-proof",
            "reportScreenshotSha256": "9" * 64,
            "testerReportFileId": "tester-report",
            "testerReportSha256": "3" * 64,
            "adapterReceiptFileId": "adapter-receipt",
            "adapterReceiptSha256": "a" * 64,
            "expertFileName": "CAN_SLIM.ex4",
            "testerSettingsRequestDigest": tester_request_digest,
            "resolvedTesterSettings": {
                "schemaVersion": self.bridge.EA_FACTORY_RESOLVED_TESTER_SETTINGS_SCHEMA_VERSION,
                "expertFileName": "CAN_SLIM.ex4",
                "symbol": "EURUSD",
                "period": "H1",
                "model": "every_tick",
                "spread": "current",
                "useDate": False,
                "fromDate": None,
                "toDate": None,
                "deposit": 10000.0,
                "visualMode": True,
                "optimizationEnabled": False,
                "shutdownTerminalAfterTest": False,
            },
            "visibleStrategyTester": True,
            "visualMode": True,
            "optimizationEnabled": False,
            "backtestVerified": True,
            "backtestExecuted": True,
            "recoveredExistingReceipt": False,
            "testerTradeRowsVerified": True,
            "fullDynamicSixGroupVerified": False,
            "zeroTrade": True,
            "mismatchedChartErrors": 0,
            "historyQualityIssue": False,
            "historyQualityVerified": True,
            "attentionRequired": True,
            "attentionReasonCode": "backtest_zero_trades",
            "executionOutcome": "completed_zero_trades",
            "performanceEvaluationAvailable": False,
            "tradeCount": 0,
            "buyTradeCount": 0,
            "sellTradeCount": 0,
            "tradeRowCount": 0,
        }
        metrics.update(
            self.bridge._ea_factory_logic_recheck_projection(build, metrics)
        )
        metrics["resolvedTesterSettingsDigest"] = self.bridge.payload_digest(
            "ea-factory-resolved-tester-settings-v1",
            metrics["resolvedTesterSettings"],
        )
        report = {
            "id": "report-backtest",
            "status": "ready",
            "linkedMissionId": "mission-backtest",
            "metrics": metrics,
        }
        with tempfile.TemporaryDirectory() as temporary:
            report_dir = Path(temporary)
            (report_dir / "report-backtest.json").write_text(
                json.dumps(report),
                encoding="utf-8",
            )
            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", report_dir),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_revalidated_artifact_manifest",
                    return_value=manifest,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_visible_artifact_payload",
                    return_value=b"verified",
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_visible_png_valid",
                    return_value=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_tester_report_matches",
                    return_value=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_visible_receipt_valid",
                    return_value=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_default_tester_settings",
                    return_value=copy.deepcopy(tester_request),
                ),
            ):
                self.assertTrue(
                    self.bridge._ea_factory_visible_front_office_evidence_valid(
                        build,
                        stage,
                        {"id": "mission-backtest"},
                        report,
                        expected_operation_id=operation_id,
                    )
                )
                metrics.update({
                    "zeroTrade": False,
                    "mismatchedChartErrors": 0,
                    "historyQualityIssue": False,
                    "historyQualityVerified": True,
                    "attentionRequired": False,
                    "attentionReasonCode": None,
                    "executionOutcome": "completed_with_trades",
                    "performanceEvaluationAvailable": True,
                    "tradeCount": 1,
                    "buyTradeCount": 1,
                    "sellTradeCount": 0,
                    "tradeRowCount": 1,
                    "testerTradeRowsVerified": True,
                    "fullDynamicSixGroupVerified": False,
                })
                valid_truth_projection = (
                    self.bridge._ea_factory_logic_recheck_projection(
                        build,
                        metrics,
                    )
                )
                metrics.update(valid_truth_projection)
                (report_dir / "report-backtest.json").write_text(
                    json.dumps(report),
                    encoding="utf-8",
                )
                self.assertTrue(
                    self.bridge._ea_factory_visible_front_office_evidence_valid(
                        build,
                        stage,
                        {"id": "mission-backtest"},
                        report,
                        expected_operation_id=operation_id,
                    )
                )

                metrics.update(
                    self.bridge._ea_factory_backtest_attention_fields(False, 17)
                )
                (report_dir / "report-backtest.json").write_text(
                    json.dumps(report),
                    encoding="utf-8",
                )
                self.assertTrue(
                    self.bridge._ea_factory_visible_front_office_evidence_valid(
                        build,
                        stage,
                        {"id": "mission-backtest"},
                        report,
                        expected_operation_id=operation_id,
                    )
                )
                metrics["performanceEvaluationAvailable"] = True
                (report_dir / "report-backtest.json").write_text(
                    json.dumps(report),
                    encoding="utf-8",
                )
                self.assertFalse(
                    self.bridge._ea_factory_visible_front_office_evidence_valid(
                        build,
                        stage,
                        {"id": "mission-backtest"},
                        report,
                        expected_operation_id=operation_id,
                    )
                )
                metrics.update(
                    self.bridge._ea_factory_backtest_attention_fields(False, 0)
                )

                metrics["logicRecheckDigest"] = "0" * 64
                (report_dir / "report-backtest.json").write_text(
                    json.dumps(report),
                    encoding="utf-8",
                )
                self.assertFalse(
                    self.bridge._ea_factory_visible_front_office_evidence_valid(
                        build,
                        stage,
                        {"id": "mission-backtest"},
                        report,
                        expected_operation_id=operation_id,
                    )
                )
                metrics.update(copy.deepcopy(valid_truth_projection))

                original_manifest_digest = build["blueprintCoverageManifest"][
                    "manifestDigest"
                ]
                build["blueprintCoverageManifest"]["manifestDigest"] = "0" * 64
                (report_dir / "report-backtest.json").write_text(
                    json.dumps(report),
                    encoding="utf-8",
                )
                self.assertFalse(
                    self.bridge._ea_factory_visible_front_office_evidence_valid(
                        build,
                        stage,
                        {"id": "mission-backtest"},
                        report,
                        expected_operation_id=operation_id,
                    )
                )
                build["blueprintCoverageManifest"][
                    "manifestDigest"
                ] = original_manifest_digest

                metrics["fullDynamicSixGroupVerified"] = True
                (report_dir / "report-backtest.json").write_text(
                    json.dumps(report),
                    encoding="utf-8",
                )
                self.assertFalse(
                    self.bridge._ea_factory_visible_front_office_evidence_valid(
                        build,
                        stage,
                        {"id": "mission-backtest"},
                        report,
                        expected_operation_id=operation_id,
                    )
                )
                metrics.update(copy.deepcopy(valid_truth_projection))

                # A legitimate visual test may take far longer than the
                # 15-second probe window. The immutable pre-action proof is
                # kept, while only the post-action proof must be fresh.
                commit_clock = self.bridge.datetime.now(self.bridge.timezone.utc)
                evidence_received_at = commit_clock - self.bridge.timedelta(
                    seconds=30
                )
                fresh_post = copy.deepcopy(process_binding)
                fresh_post["observedAt"] = (
                    evidence_received_at - self.bridge.timedelta(seconds=1)
                ).isoformat()
                fresh_post["processBindingDigest"] = ""
                fresh_post["processBindingDigest"] = (
                    self.bridge._ea_factory_front_office_process_binding_digest(
                        fresh_post
                    )
                )
                metrics["evidenceReceivedAt"] = evidence_received_at.isoformat()
                metrics["postProcessBinding"] = fresh_post
                metrics["postProcessBindingDigest"] = fresh_post[
                    "processBindingDigest"
                ]
                (report_dir / "report-backtest.json").write_text(
                    json.dumps(report),
                    encoding="utf-8",
                )
                self.assertTrue(
                    self.bridge._ea_factory_visible_front_office_evidence_valid(
                        build,
                        stage,
                        {"id": "mission-backtest"},
                        report,
                        expected_operation_id=operation_id,
                        require_fresh_process_proof=True,
                    )
                )

                for field, replacement in (
                    ("terminalWindowHandle", 999),
                    ("terminalWindowTitleSha256", "9" * 64),
                    ("frontOfficeWindowHandle", 998),
                    ("frontOfficeWindowClassSha256", "a" * 64),
                ):
                    with self.subTest(post_action_window_drift=field):
                        drifted_post = copy.deepcopy(fresh_post)
                        drifted_post[field] = replacement
                        drifted_post["processBindingDigest"] = ""
                        drifted_post["processBindingDigest"] = (
                            self.bridge._ea_factory_front_office_process_binding_digest(
                                drifted_post
                            )
                        )
                        metrics["postProcessBinding"] = drifted_post
                        metrics["postProcessBindingDigest"] = drifted_post[
                            "processBindingDigest"
                        ]
                        (report_dir / "report-backtest.json").write_text(
                            json.dumps(report),
                            encoding="utf-8",
                        )
                        self.assertFalse(
                            self.bridge._ea_factory_visible_front_office_evidence_valid(
                                build,
                                stage,
                                {"id": "mission-backtest"},
                                report,
                                expected_operation_id=operation_id,
                                require_fresh_process_proof=True,
                            )
                        )
                metrics["postProcessBinding"] = fresh_post
                metrics["postProcessBindingDigest"] = fresh_post[
                    "processBindingDigest"
                ]

    def test_invalid_visible_result_creates_no_success_mission_or_report(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(
            build,
            current_stage="compile_validate",
        )
        build["oneClickRun"]["status"] = "running"
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        stage = next(
            item for item in build["stages"]
            if item["id"] == "compile_validate"
        )
        stage["requestIdempotencyKey"] = "stage-request"
        request = {
            "buildId": build["id"],
            "stageId": "compile_validate",
            "terminalBinding": copy.deepcopy(
                build["oneClickRun"]["terminalBinding"]
            ),
            "visibleOperation": copy.deepcopy(
                build["oneClickRun"]["visibleAction"]
            ),
            "missionId": "mission-eaf-visible-test",
            "reportId": "report-eaf-visible-test",
            "resolvedTarget": {
                "terminalExecutableSha256": "1" * 64,
                "frontOfficeExecutableSha256": "2" * 64,
            },
        }
        result = {
            "metrics": {},
            "artifactSpecifications": [
                {"alias": "compiled_binary", "relativePath": "EA_Versions/a.ex4", "artifactKind": "compile_evidence"},
                {"alias": "visible_window", "relativePath": "Screenshots/a.png", "artifactKind": "screenshot_evidence"},
                {"alias": "compile_log", "relativePath": "Reports/a.txt", "artifactKind": "compile_evidence"},
                {"alias": "adapter_receipt", "relativePath": "Reports/a.json", "artifactKind": "compile_evidence"},
            ],
        }
        artifact_rows = [
            {
                "fileId": f"ea-file-{index}",
                "relativePath": item["relativePath"],
                "artifactKind": item["artifactKind"],
            }
            for index, item in enumerate(result["artifactSpecifications"], start=1)
        ]
        state = self.state(build)
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_register_artifacts",
                return_value=artifact_rows,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_visible_result_metrics",
                return_value={"stageArtifactManifestDigest": "3" * 64},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_terminal_binding_current",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_visible_front_office_evidence_valid",
                return_value=False,
            ),
            mock.patch.object(self.bridge, "create_mission") as create_mission,
            mock.patch.object(self.bridge, "create_report") as create_report,
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ) as write_state,
        ):
            with self.assertRaises(self.bridge.RequestError):
                self.bridge._ea_factory_commit_visible_front_office_result(
                    request,
                    result,
                )
        create_mission.assert_not_called()
        create_report.assert_not_called()
        write_state.assert_not_called()
        self.assertEqual(stage["status"], "pending")
        self.assertIsNone(stage["reportId"])

    def _commit_backtest_acceptance_case(
        self,
        *,
        metrics: dict,
        strategy_spec: dict | None,
        canonical_custom_ema_profile: bool = False,
    ) -> dict:
        build = self.backtest_restart_build(status="awaiting_visible_terminal")
        if canonical_custom_ema_profile:
            record = self.bridge._ea_factory_custom_source_record(
                copy.deepcopy(
                    self.bridge.EA_FACTORY_CUSTOM_EMA_SMOKE_PROFILE_PAYLOAD
                )
            )
            build.update({
                "platform": "mt5",
                "artifactKind": "expert_advisor",
                "sourceRecordId": record["sourceRecordId"],
                "sourceRecordDigest": record["recordDigest"],
            })
            strategy_spec = {
                "schemaVersion": "ea-factory-strategy-spec-v3",
                "buildId": build["id"],
                "sourceRecordId": record["sourceRecordId"],
                "recordDigest": record["recordDigest"],
                "sourceKind": record["sourceKind"],
                "sourceKey": record["sourceKey"],
                "core": copy.deepcopy(record["core"]),
                "artifactKind": "expert_advisor",
                "targetPlatform": "mt5",
                "language": "mql5",
                "strategySchemaVersion": (
                    self.bridge.EA_STRATEGY_BRIEF_SCHEMA_VERSION
                ),
                "strategyBrief": copy.deepcopy(record["strategyBrief"]),
                "strategyBriefDigest": record["strategyBriefDigest"],
                "immutable": True,
            }
            build["oneClickRun"]["terminalBinding"]["platform"] = "mt5"
            build["oneClickRun"]["requestDigest"] = (
                self.bridge._ea_factory_one_click_request_digest(build)
            )
        self.assertIsInstance(strategy_spec, dict)
        run = build["oneClickRun"]
        run["status"] = "running"
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            run,
            "backtest_recheck",
        )
        stage = next(
            row for row in build["stages"] if row["id"] == "backtest_recheck"
        )
        stage.update({
            "missionId": None,
            "reportId": None,
            "requestIdempotencyKey": "backtest-acceptance-stage-request",
            "missionIdempotencyKey": "backtest-acceptance-stage-mission",
        })
        request = {
            "schemaVersion": "ea-factory-visible-front-office-request-v1",
            "buildId": build["id"],
            "stageId": "backtest_recheck",
            "runSnapshotDigest": self.bridge.payload_digest(
                "ea-factory-one-click-run-snapshot-v1",
                run,
            ),
            "terminalBinding": copy.deepcopy(run["terminalBinding"]),
            "visibleOperation": copy.deepcopy(run["visibleAction"]),
            "missionId": "mission-backtest-acceptance",
            "reportId": "report-backtest-acceptance",
            "resolvedTarget": {
                "terminalExecutableSha256": "1" * 64,
                "frontOfficeExecutableSha256": "2" * 64,
            },
        }
        result = {"metrics": {}, "artifactSpecifications": []}
        state = self.state(build)
        complete_metrics = {
            "stageArtifactManifestDigest": "3" * 64,
            "attentionRequired": False,
            "attentionReasonCode": None,
            **copy.deepcopy(metrics),
        }
        mission = {"id": request["missionId"], "status": "running"}
        report = {
            "id": request["reportId"],
            "status": "ready",
            "linkedMissionId": request["missionId"],
            "metrics": copy.deepcopy(complete_metrics),
        }
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_register_artifacts",
                return_value=[],
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_visible_result_metrics",
                return_value=complete_metrics,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_review_strategy_spec",
                return_value=strategy_spec,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_terminal_binding_current",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_visible_front_office_evidence_valid",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_success_record_snapshot",
                return_value={
                    "missionIndex": None,
                    "mission": None,
                    "report": None,
                },
            ),
            mock.patch.object(
                self.bridge,
                "create_mission",
                return_value=mission,
            ),
            mock.patch.object(
                self.bridge,
                "create_report",
                return_value=report,
            ),
            mock.patch.object(self.bridge, "_ea_factory_complete_local_mission"),
            mock.patch.object(
                self.bridge,
                "_ea_factory_sync_build_status",
                return_value=False,
            ),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
        ):
            self.bridge._ea_factory_commit_visible_front_office_result(
                request,
                result,
            )
        return state["builds"][0]

    def test_zero_trade_backtest_stops_before_final_report(self) -> None:
        build = self._commit_backtest_acceptance_case(
            metrics={
                "zeroTrade": True,
                "tradeCount": 0,
                "tradeRowCount": 0,
                "buyTradeCount": 0,
                "sellTradeCount": 0,
                "historyQualityIssue": False,
            },
            strategy_spec={
                "sourceKind": "verified_deep_research_sheet",
                "strategyBrief": {"entryRules": "Long only"},
            },
        )

        run = build["oneClickRun"]
        final_stage = next(
            row for row in build["stages"] if row["id"] == "final_report"
        )
        self.assertEqual(run["status"], "failed")
        self.assertEqual(run["currentStageId"], "backtest_recheck")
        self.assertEqual(
            run["failureCode"],
            "backtest_acceptance_zero_trades",
        )
        self.assertIsNotNone(run["completedAt"])
        self.assertEqual(final_stage["status"], "pending")
        self.assertIsNone(final_stage["requestIdempotencyKey"])
        self.assertFalse(
            self.bridge._ea_factory_stage_can_advance(build, "final_report")
        )
        model = self.bridge._ea_factory_one_click_read_model(build)
        self.assertTrue(model["canRestartBacktest"])
        self.assertEqual(
            model["failureCode"],
            "backtest_acceptance_zero_trades",
        )
        self.assertEqual(
            self.bridge._ea_factory_revalidated_one_click_run(build)[
                "failureCode"
            ],
            "backtest_acceptance_zero_trades",
        )
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=self.state(build),
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_ea_factory_report_rows_snapshot",
                return_value=[],
            ),
        ):
            next_action = self.bridge._ea_factory_one_click_next_action(
                build["id"]
            )
        self.assertEqual(next_action["kind"], "stop")
        self.assertEqual(
            next_action["reasonCode"],
            "backtest_acceptance_zero_trades",
        )

    def test_bidirectional_custom_ema_requires_buy_and_sell_trades(self) -> None:
        build = self._commit_backtest_acceptance_case(
            metrics={
                "zeroTrade": False,
                "tradeCount": 3,
                "tradeRowCount": 3,
                "buyTradeCount": 3,
                "sellTradeCount": 0,
                "historyQualityIssue": False,
            },
            strategy_spec=None,
            canonical_custom_ema_profile=True,
        )

        run = build["oneClickRun"]
        self.assertEqual(run["status"], "failed")
        self.assertEqual(
            run["failureCode"],
            "backtest_acceptance_required_trade_direction_missing",
        )
        self.assertTrue(
            self.bridge._ea_factory_one_click_read_model(build)[
                "canRestartBacktest"
            ]
        )
        self.assertFalse(
            self.bridge._ea_factory_stage_can_advance(build, "final_report")
        )

    def test_history_quality_issue_stops_even_when_trades_exist(self) -> None:
        build = self._commit_backtest_acceptance_case(
            metrics={
                "zeroTrade": False,
                "tradeCount": 6,
                "tradeRowCount": 6,
                "buyTradeCount": 3,
                "sellTradeCount": 3,
                "historyQualityIssue": True,
            },
            strategy_spec={
                "sourceKind": "verified_deep_research_sheet",
                "strategyBrief": {"entryRules": "BUY and SELL"},
            },
        )

        self.assertEqual(build["oneClickRun"]["status"], "failed")
        self.assertEqual(
            build["oneClickRun"]["failureCode"],
            "backtest_acceptance_history_quality_issue",
        )
        self.assertFalse(
            self.bridge._ea_factory_stage_can_advance(build, "final_report")
        )

    def test_acceptance_rejected_backtest_can_use_existing_restart_endpoint(self) -> None:
        build = self._commit_backtest_acceptance_case(
            metrics={
                "zeroTrade": True,
                "tradeCount": 0,
                "tradeRowCount": 0,
                "buyTradeCount": 0,
                "sellTradeCount": 0,
                "historyQualityIssue": False,
            },
            strategy_spec={
                "sourceKind": "verified_deep_research_sheet",
                "strategyBrief": {"entryRules": "Long only"},
            },
        )
        previous_run_id = build["oneClickRun"]["runId"]
        state = self.state(build)
        stack, handles = self.backtest_restart_patch_stack(state)
        with stack:
            restarted = self.bridge.restart_ea_factory_build_backtest_only(
                build["id"],
                {
                    "runId": previous_run_id,
                    "idempotencyKey": "restart-after-acceptance-gate",
                },
            )

        self.assertEqual(restarted["kind"], "ea_factory_backtest_restarted")
        self.assertEqual(build["oneClickRun"]["status"], "queued")
        self.assertEqual(
            build["oneClickRun"]["currentStageId"],
            "backtest_recheck",
        )
        restarted_stage = next(
            row for row in build["stages"] if row["id"] == "backtest_recheck"
        )
        self.assertEqual(restarted_stage["status"], "pending")
        self.assertFalse(restarted_stage["evidenceVerified"])
        self.assertEqual(len(build["oneClickRunHistory"]), 1)
        self.assertEqual(
            build["oneClickRunHistory"][0]["backtestStage"]["status"],
            "completed",
        )
        self.assertTrue(
            build["oneClickRunHistory"][0]["backtestStage"][
                "evidenceVerified"
            ]
        )
        handles["start"].assert_called_once()

    def test_compliant_bidirectional_custom_ema_can_advance_to_final(self) -> None:
        build = self._commit_backtest_acceptance_case(
            metrics={
                "zeroTrade": False,
                "tradeCount": 4,
                "tradeRowCount": 4,
                "buyTradeCount": 2,
                "sellTradeCount": 2,
                "historyQualityIssue": False,
            },
            strategy_spec=None,
            canonical_custom_ema_profile=True,
        )

        self.assertEqual(build["oneClickRun"]["status"], "running")
        self.assertIsNone(build["oneClickRun"]["failureCode"])
        self.assertEqual(
            next(
                row
                for row in build["stages"]
                if row["id"] == "backtest_recheck"
            )["status"],
            "completed",
        )
        self.assertTrue(
            self.bridge._ea_factory_stage_can_advance(build, "final_report")
        )

    def test_generic_custom_source_is_not_forced_to_trade_both_directions(self) -> None:
        build = self.build()
        metrics = {
            "zeroTrade": False,
            "tradeCount": 2,
            "tradeRowCount": 2,
            "buyTradeCount": 2,
            "sellTradeCount": 0,
            "historyQualityIssue": False,
        }
        with mock.patch.object(
            self.bridge,
            "_ea_factory_review_strategy_spec",
            return_value={
                "sourceKind": "custom_operator",
                "strategyBrief": {
                    "systemName": "Long-only breakout",
                    "systemOverview": "One-direction breakout",
                    "entryRules": "BUY on a new high; never open SELL",
                },
            },
        ):
            self.assertIsNone(
                self.bridge._ea_factory_backtest_acceptance_failure(
                    build,
                    metrics,
                )
            )

    def test_final_report_invalid_visible_proof_creates_no_success_records(self) -> None:
        build = self.build()
        compile_stage = next(
            item for item in build["stages"]
            if item["id"] == "compile_validate"
        )
        compile_stage.update({
            "status": "completed",
            "evidenceVerified": True,
            "missionId": "mission-visible-compile",
            "reportId": "report-visible-compile",
            "visibleEvidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "visibleOperationId": "ea-visible-compile-final-check",
        })
        final_stage = next(
            item for item in build["stages"]
            if item["id"] == "final_report"
        )
        final_stage.update({
            "status": "pending",
            "missionIdempotencyKey": "final-idempotency",
        })
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "Summaries").mkdir()
            reports = root / "runtime-reports"
            reports.mkdir()
            (reports / "report-visible-compile.json").write_text(
                json.dumps({
                    "id": "report-visible-compile",
                    "status": "ready",
                    "metrics": {},
                }),
                encoding="utf-8",
            )
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_build_directory",
                    return_value=root,
                ),
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", reports),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_visible_front_office_evidence_valid",
                    return_value=False,
                ),
                mock.patch.object(self.bridge, "create_mission") as create_mission,
                mock.patch.object(self.bridge, "create_report") as create_report,
                mock.patch.object(self.bridge, "_ea_factory_complete_local_mission") as complete_mission,
            ):
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._ea_factory_complete_final_report(
                        build,
                        final_stage,
                    )
        create_mission.assert_not_called()
        create_report.assert_not_called()
        complete_mission.assert_not_called()
        self.assertEqual(final_stage["status"], "pending")
        self.assertIsNone(final_stage["reportId"])

    def test_visible_commit_faults_compensate_success_records(self) -> None:
        fault_points = (
            "create_report",
            "complete_mission",
            "second_evidence_check",
            "state_write",
        )
        for fault_point in fault_points:
            with self.subTest(fault_point=fault_point):
                build, state, request, result, artifact_rows = (
                    self._visible_commit_fixture()
                )
                mission = {"id": request["missionId"], "status": "running"}
                report = {
                    "id": request["reportId"],
                    "status": "ready",
                    "linkedMissionId": request["missionId"],
                    "metrics": {},
                }
                create_report_effect = (
                    RuntimeError("report write fault")
                    if fault_point == "create_report"
                    else (lambda *_args, **_kwargs: report)
                )
                complete_effect = (
                    RuntimeError("mission completion fault")
                    if fault_point == "complete_mission"
                    else None
                )
                evidence_effect = (
                    [True, False]
                    if fault_point == "second_evidence_check"
                    else [True, True]
                )
                write_effect = (
                    RuntimeError("factory state write fault")
                    if fault_point == "state_write"
                    else None
                )
                with (
                    mock.patch.object(
                        self.bridge,
                        "_load_ea_factory_state_unlocked",
                        return_value=state,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_register_artifacts",
                        return_value=artifact_rows,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_visible_result_metrics",
                        return_value={"stageArtifactManifestDigest": "3" * 64},
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_one_click_terminal_binding_current",
                        return_value=True,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_visible_front_office_evidence_valid",
                        side_effect=evidence_effect,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_success_record_snapshot",
                        return_value={
                            "missionIndex": None,
                            "mission": None,
                            "report": None,
                        },
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_restore_success_record_snapshot",
                    ) as restore,
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_visible_commit_is_durable",
                        return_value=False,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "create_mission",
                        return_value=mission,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "create_report",
                        side_effect=create_report_effect,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_complete_local_mission",
                        side_effect=complete_effect,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_sync_build_status",
                        return_value=False,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_write_ea_factory_state_unlocked",
                        side_effect=write_effect,
                    ),
                    mock.patch.object(self.bridge, "append_audit"),
                ):
                    with self.assertRaises((RuntimeError, self.bridge.RequestError)):
                        self.bridge._ea_factory_commit_visible_front_office_result(
                            request,
                            result,
                        )
                restore.assert_called_once()

    def test_success_record_snapshot_restore_removes_new_rows(self) -> None:
        mission_id = "mission-eaf-rollback-test"
        report_id = "report-eaf-rollback-test"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missions_path = root / "missions.json"
            reports_path = root / "reports"
            reports_path.mkdir()
            with (
                mock.patch.object(self.bridge, "MISSIONS_PATH", missions_path),
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", reports_path),
            ):
                self.bridge._invalidate_missions_read_cache()
                snapshot = self.bridge._ea_factory_success_record_snapshot(
                    mission_id,
                    report_id,
                )
                self.bridge.save_missions([
                    {"id": mission_id, "status": "completed"},
                ])
                self.bridge.write_json(
                    reports_path / f"{report_id}.json",
                    {"id": report_id, "status": "ready"},
                )
                self.bridge._ea_factory_restore_success_record_snapshot(
                    mission_id,
                    report_id,
                    snapshot,
                )
                self.assertEqual(self.bridge.load_missions(), [])
                self.assertFalse((reports_path / f"{report_id}.json").exists())
            self.bridge._invalidate_missions_read_cache()

    def test_visible_report_read_model_hides_pid_hwnd_and_full_bindings(self) -> None:
        report = {
            "id": "report-visible-private",
            "type": "ea_compile_report",
            "status": "ready",
            "metrics": {
                "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
                "operationId": "ea-visible-safe",
                "processId": 123,
                "windowHandle": 456,
                "processBinding": {"terminalProcessId": 123},
                "postProcessBinding": {"terminalProcessId": 123},
                "compiledBinarySha256": "a" * 64,
            },
        }
        model = self.bridge.report_read_model_item(report)
        self.assertNotIn("processId", model["metrics"])
        self.assertNotIn("windowHandle", model["metrics"])
        self.assertNotIn("processBinding", model["metrics"])
        self.assertNotIn("postProcessBinding", model["metrics"])
        self.assertEqual(model["metrics"]["compiledBinarySha256"], "a" * 64)

    def test_tester_set_parser_accepts_only_allowlisted_mt4_metadata_suffixes(self) -> None:
        defaults = {
            "InpStopLossPercent": 7.5,
            "RewardRiskRatio": 2.0,
            "RiskPercent": 1.0,
            "ExecutionBufferPoints": 2,
            "SlippagePoints": 3,
            "MaxOpenPositionsPerSymbolMagic": 1,
            "MagicNumber": 4186001,
            "DailyMAPeriod": 50,
            "WeeklyMAPeriod": 50,
            "FiftyTwoWeekLookback": 52,
            "FundamentalCriteriaConfirmed": False,
            "ExternalBenchmarkUptrendConfirmed": False,
            "MaxSpreadPoints": 30,
        }
        assumptions = []
        lines = []
        for name, input_type in self.bridge.EA_FACTORY_CAN_SLIM_CERTIFIED_INPUT_LAYOUT:
            simulation = name in self.bridge.EA_FACTORY_CAN_SLIM_SIMULATION_INPUT_NAMES
            tester_value = True if simulation else defaults[name]
            assumptions.append({
                "inputName": name,
                "inputType": input_type,
                "sourceDefault": defaults[name],
                "testerValue": tester_value,
                "reasonCode": (
                    "simulate_external_fact_for_historical_test_only"
                    if simulation
                    else "reset_to_certified_source_default_to_prevent_stale_tester_state"
                ),
            })
            token = self.bridge._ea_factory_input_value_token(
                tester_value,
                input_type,
            )
            lines.extend((
                f"{name}={token}",
                f"{name},F=0",
                f"{name},1={token}",
                f"{name},2={token}",
                f"{name},3=0",
            ))
        preset = {"assumptions": assumptions}
        realistic = ("\ufeff" + "\r\n".join(lines) + "\r\n").encode("utf-8")
        parsed = self.bridge._ea_factory_tester_set_values(realistic, preset)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["MaxSpreadPoints"], 30)
        self.assertTrue(parsed["FundamentalCriteriaConfirmed"])
        self.assertIsNone(
            self.bridge._ea_factory_tester_set_values(
                realistic + b"MaxSpreadPoints,X=30\r\n",
                preset,
            )
        )
        self.assertIsNone(
            self.bridge._ea_factory_tester_set_values(
                realistic + b"UnknownInput,F=0\r\n",
                preset,
            )
        )

    def test_png_evidence_must_be_real_and_nonblank(self) -> None:
        self.assertTrue(
            self.bridge._ea_factory_visible_png_valid(
                self._png_payload(solid=False)
            )
        )
        self.assertFalse(
            self.bridge._ea_factory_visible_png_valid(
                self._png_payload(solid=True)
            )
        )
        self.assertFalse(
            self.bridge._ea_factory_visible_png_valid(b"not-a-png")
        )

    def test_tester_report_counts_and_settings_are_cross_checked(self) -> None:
        settings = {
            "expertFileName": "CAN_SLIM.ex4",
            "symbol": "EURUSD",
            "period": "H1",
            "model": "every_tick",
            "deposit": 10000.0,
            "spread": "Current",
        }
        payload = (
            "<html><body><table>"
            "<tr><td>Expert</td><td>CAN_SLIM</td></tr>"
            "<tr><td>Symbol</td><td>EURUSD</td></tr>"
            "<tr><td>Period</td><td>H1</td></tr>"
            "<tr><td>Model</td><td>Every tick</td></tr>"
            "<tr><td>Spread</td><td>Current (12)</td></tr>"
            "<tr><td>Initial deposit</td><td>10000.00</td></tr>"
            "<tr><td>Mismatched chart errors</td><td>0</td></tr>"
            "<tr><td>Total trades</td><td>3</td></tr>"
            "<tr><td>Short positions (won %)</td><td>1</td></tr>"
            "<tr><td>Long positions (won %)</td><td>2</td></tr>"
            "</table></body></html>"
        ).encode("utf-8")
        self.assertTrue(
            self.bridge._ea_factory_tester_report_matches(
                payload,
                settings,
                trade_count=3,
                buy_trade_count=2,
                sell_trade_count=1,
                mismatched_chart_errors=0,
            )
        )
        self.assertFalse(
            self.bridge._ea_factory_tester_report_matches(
                payload,
                settings,
                trade_count=2,
                buy_trade_count=1,
                sell_trade_count=1,
                mismatched_chart_errors=0,
            )
        )
        wrong_symbol_with_decoy = payload.replace(
            b"<tr><td>Symbol</td><td>EURUSD</td></tr>",
            b"<tr><td>Symbol</td><td>GBPUSD</td></tr>"
            b"<tr><td>Comment</td><td>EURUSD</td></tr>",
        )
        self.assertFalse(
            self.bridge._ea_factory_tester_report_matches(
                wrong_symbol_with_decoy,
                settings,
                trade_count=3,
                buy_trade_count=2,
                sell_trade_count=1,
                mismatched_chart_errors=0,
            )
        )
        duplicate_symbol = payload.replace(
            b"<tr><td>Symbol</td><td>EURUSD</td></tr>",
            b"<tr><td>Symbol</td><td>EURUSD</td></tr>"
            b"<tr><td>Symbol</td><td>EURUSD</td></tr>",
        )
        self.assertFalse(
            self.bridge._ea_factory_tester_report_matches(
                duplicate_symbol,
                settings,
                trade_count=3,
                buy_trade_count=2,
                sell_trade_count=1,
                mismatched_chart_errors=0,
            )
        )

    def test_native_mt5_report_uses_strict_shared_payload_verifier(self) -> None:
        settings = {
            "schemaVersion": "ea-factory-resolved-tester-settings-v1",
            "expertFileName": "CertifiedCanSlimMT5_v01.ex5",
            "symbol": "EURUSD",
            "period": "H1",
            "model": "every_tick",
            "spread": "current",
            "useDate": True,
            "fromDate": "2026-07-17",
            "toDate": "2026-10-14",
            "deposit": 10000,
            "visualMode": True,
            "optimizationEnabled": False,
            "shutdownTerminalAfterTest": False,
        }
        preset = {
            "assumptions": [
                {
                    "inputName": "RiskPercent",
                    "inputType": "double",
                    "testerValue": 1.0,
                }
            ]
        }
        payload = b"""<html><head><title>Strategy Tester Report</title></head>
        <body><table>
        <tr><td>Strategy Tester Report</td></tr>
        <tr><td>RoboForex-Pro (Build 6230)</td></tr>
        <tr><td>Settings</td></tr>
        <tr><td>Expert:</td><td>CertifiedCanSlimMT5_v01</td></tr>
        <tr><td>Symbol:</td><td>EURUSD</td></tr>
        <tr><td>Period:</td><td>H1 (2026.07.17 - 2026.10.14)</td></tr>
        <tr><td>Inputs:</td><td>RiskPercent=1</td></tr>
        <tr><td>Results</td></tr>
        <tr><td>History Quality:</td><td>100%</td></tr>
        <tr><td>Bars:</td><td>1512</td><td>Ticks:</td><td>2811166</td>
            <td>Symbols:</td><td>0</td></tr>
        <tr><td>Total Net Profit:</td><td>0.00</td>
            <td>Balance Drawdown Absolute:</td><td>0.00</td>
            <td>Equity Drawdown Absolute:</td><td>0.00</td></tr>
        <tr><td>Gross Profit:</td><td>0.00</td>
            <td>Balance Drawdown Maximal:</td><td>0.00 (0.00%)</td>
            <td>Equity Drawdown Maximal:</td><td>0.00 (0.00%)</td></tr>
        <tr><td>Gross Loss:</td><td>0.00</td>
            <td>Balance Drawdown Relative:</td><td>0.00% (0.00)</td>
            <td>Equity Drawdown Relative:</td><td>0.00% (0.00)</td></tr>
        <tr><td>AHPR:</td><td>0.0000 (0.00%)</td>
            <td>OnTester result:</td><td>0</td></tr>
        <tr><td>Total Trades:</td><td>0</td>
            <td>Short Trades (won %):</td><td>0 (0.00%)</td>
            <td>Long Trades (won %):</td><td>0 (0.00%)</td></tr>
        <tr><td>Total Deals:</td><td>0</td></tr>
        </table></body></html>"""

        self.assertTrue(
            self.bridge._ea_factory_tester_report_matches(
                payload,
                settings,
                trade_count=0,
                buy_trade_count=0,
                sell_trade_count=0,
                mismatched_chart_errors=0,
                tester_input_preset=preset,
                platform="mt5",
            )
        )
        self.assertFalse(
            self.bridge._ea_factory_tester_report_matches(
                payload,
                settings,
                trade_count=1,
                buy_trade_count=1,
                sell_trade_count=0,
                mismatched_chart_errors=0,
                tester_input_preset=preset,
                platform="mt5",
            )
        )
        self.assertFalse(
            self.bridge._ea_factory_tester_report_matches(
                payload.replace(b"</head>", b"<script>1</script></head>"),
                settings,
                trade_count=0,
                buy_trade_count=0,
                sell_trade_count=0,
                mismatched_chart_errors=0,
                tester_input_preset=preset,
                platform="mt5",
            )
        )

    def test_tester_report_accepts_unique_mt4_title_when_expert_row_is_absent(self) -> None:
        settings = {
            "expertFileName": "CAN_SLIM_SourceOnly_v01.ex4",
            "symbol": "GBPUSD",
            "period": "H1",
            "model": "every_tick",
            "deposit": 10000.0,
            "spread": 20,
        }
        payload = (
            "<html><head><title>Strategy Tester: CAN_SLIM_SourceOnly_v01</title></head>"
            "<body><table>"
            "<tr><td>Symbol</td><td>GBPUSD</td></tr>"
            "<tr><td>Period</td><td>1 Hour (H1)</td></tr>"
            "<tr><td>Model</td><td>Every tick (most precise)</td></tr>"
            "<tr><td>Spread</td><td>20</td></tr>"
            "<tr><td>Initial deposit</td><td>10000.00</td></tr>"
            "<tr><td>Mismatched chart errors</td><td>0</td></tr>"
            "<tr><td>Total trades</td><td>0</td></tr>"
            "</table></body></html>"
        ).encode("utf-8")
        self.assertTrue(
            self.bridge._ea_factory_tester_report_matches(
                payload,
                settings,
                trade_count=0,
                buy_trade_count=0,
                sell_trade_count=0,
                mismatched_chart_errors=0,
            )
        )

    def test_tester_report_rejects_duplicate_title_when_expert_row_is_absent(self) -> None:
        settings = {
            "expertFileName": "CAN_SLIM_SourceOnly_v01.ex4",
            "symbol": "GBPUSD",
            "period": "H1",
            "model": "every_tick",
            "deposit": 10000.0,
            "spread": 20,
        }
        payload = (
            "<html><head><title>Strategy Tester: CAN_SLIM_SourceOnly_v01</title>"
            "<title>Strategy Tester: CAN_SLIM_SourceOnly_v01</title></head>"
            "<body><table>"
            "<tr><td>Symbol</td><td>GBPUSD</td></tr>"
            "<tr><td>Period</td><td>H1</td></tr>"
            "<tr><td>Model</td><td>Every tick</td></tr>"
            "<tr><td>Spread</td><td>20</td></tr>"
            "<tr><td>Initial deposit</td><td>10000.00</td></tr>"
            "<tr><td>Mismatched chart errors</td><td>0</td></tr>"
            "<tr><td>Total trades</td><td>0</td></tr>"
            "</table></body></html>"
        ).encode("utf-8")
        self.assertFalse(
            self.bridge._ea_factory_tester_report_matches(
                payload,
                settings,
                trade_count=0,
                buy_trade_count=0,
                sell_trade_count=0,
                mismatched_chart_errors=0,
            )
        )

    @staticmethod
    def _png_payload(*, solid: bool) -> bytes:
        width, height = 320, 180

        def chunk(kind: bytes, data: bytes) -> bytes:
            return (
                len(data).to_bytes(4, "big")
                + kind
                + data
                + (zlib.crc32(kind + data) & 0xFFFFFFFF).to_bytes(4, "big")
            )

        ihdr = (
            width.to_bytes(4, "big")
            + height.to_bytes(4, "big")
            + bytes((8, 2, 0, 0, 0))
        )
        scanlines = bytearray()
        for y in range(height):
            scanlines.append(0)
            for x in range(width):
                value = 17 if solid else (x + y * 3) % 256
                scanlines.extend((value, (value * 3) % 256, (value * 7) % 256))
        return (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(scanlines)))
            + chunk(b"IEND", b"")
        )

    def _run(self, build: dict, *, current_stage: str) -> dict:
        now = "2026-09-11T00:00:00Z"
        return {
            "schemaVersion": self.bridge.EA_FACTORY_ONE_CLICK_SCHEMA_VERSION,
            "runId": "ea-run-one-click-test",
            "idempotencyKey": "one-click-ui-001",
            "requestDigest": self.bridge._ea_factory_one_click_request_digest(build),
            "status": "queued",
            "currentStageId": current_stage,
            "terminalBinding": {
                "platform": "mt4",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "failureCode": None,
            "messageTh": "queued",
            "startedAt": now,
            "updatedAt": now,
            "completedAt": None,
        }

    def _visible_commit_fixture(self):
        build = self.build()
        build["oneClickRun"] = self._run(
            build,
            current_stage="compile_validate",
        )
        build["oneClickRun"]["status"] = "running"
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        stage = next(
            item for item in build["stages"]
            if item["id"] == "compile_validate"
        )
        stage.update({
            "requestIdempotencyKey": "stage-request",
            "missionIdempotencyKey": "stage-mission-key",
        })
        request = {
            "schemaVersion": "ea-factory-visible-front-office-request-v1",
            "buildId": build["id"],
            "stageId": "compile_validate",
            "runSnapshotDigest": self.bridge.payload_digest(
                "ea-factory-one-click-run-snapshot-v1",
                build["oneClickRun"],
            ),
            "terminalBinding": copy.deepcopy(
                build["oneClickRun"]["terminalBinding"]
            ),
            "visibleOperation": copy.deepcopy(
                build["oneClickRun"]["visibleAction"]
            ),
            "missionId": "mission-eaf-visible-fault",
            "reportId": "report-eaf-visible-fault",
            "resolvedTarget": {
                "terminalExecutableSha256": "1" * 64,
                "frontOfficeExecutableSha256": "2" * 64,
            },
        }
        result = {
            "metrics": {},
            "artifactSpecifications": [
                {"alias": "compiled_binary", "relativePath": "EA_Versions/a.ex4", "artifactKind": "compile_evidence"},
                {"alias": "visible_window", "relativePath": "Screenshots/a.png", "artifactKind": "screenshot_evidence"},
                {"alias": "compile_log", "relativePath": "Reports/a.txt", "artifactKind": "compile_evidence"},
                {"alias": "adapter_receipt", "relativePath": "Reports/a.json", "artifactKind": "compile_evidence"},
            ],
        }
        artifact_rows = [
            {
                "fileId": f"ea-file-fault-{index}",
                "relativePath": item["relativePath"],
                "artifactKind": item["artifactKind"],
            }
            for index, item in enumerate(
                result["artifactSpecifications"],
                start=1,
            )
        ]
        return build, self.state(build), request, result, artifact_rows

    def test_one_click_progress_is_local_and_counts_only_completed_gates(self) -> None:
        build = self.build()
        run = self._run(build, current_stage="generate_source")
        run["status"] = "running"
        build["oneClickRun"] = run

        queued = self.bridge._ea_factory_one_click_read_model(build)
        self.assertTrue(queued["canCancel"])
        self.assertEqual(queued["progressPercent"], 10)
        self.assertEqual(queued["progressStageIndex"], 0)
        self.assertEqual(queued["progressStageCount"], 5)
        self.assertEqual(queued["progressSource"], "durable_phase_gate")

        generate = next(
            row for row in build["stages"] if row["id"] == "generate_source"
        )
        generate["status"] = "completed"
        generate["evidenceVerified"] = True
        run["currentStageId"] = "source_review"
        advanced = self.bridge._ea_factory_one_click_read_model(build)
        self.assertEqual(advanced["progressPercent"], 30)
        self.assertEqual(advanced["progressStageIndex"], 1)

        run["status"] = "cancelled"
        run["failureCode"] = "operator_cancelled"
        run["completedAt"] = "2026-09-11T00:01:00Z"
        cancelled = self.bridge._ea_factory_one_click_read_model(build)
        self.assertFalse(cancelled["canCancel"])
        self.assertEqual(cancelled["progressPercent"], 20)
        self.assertEqual(cancelled["progressStageIndex"], 1)

    def test_cancel_targets_exact_run_mission_and_process_without_terminal_shutdown(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="generate_source")
        build["oneClickRun"]["status"] = "waiting_ai"
        state = self.state(build)
        cancel_event = threading.Event()

        class StoppedCoordinator:
            @staticmethod
            def is_alive():
                return False

        owned_mission = {"id": "mission-eaf-owned"}
        self.bridge.EA_FACTORY_ONE_CLICK_THREADS[build["id"]] = StoppedCoordinator()
        self.bridge.EA_FACTORY_ONE_CLICK_CANCEL_EVENTS[build["id"]] = cancel_event
        try:
            with (
                mock.patch.object(
                    self.bridge,
                    "_load_ea_factory_state_unlocked",
                    return_value=state,
                ),
                mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
                mock.patch.object(self.bridge, "load_missions", return_value=[]),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_active_stage_mission_for_cancel",
                    return_value=owned_mission,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_cancel_owned_mission",
                    return_value={
                        "missionId": owned_mission["id"],
                        "persisted": True,
                        "previousStatus": "running",
                    },
                ) as cancel_mission,
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_terminate_owned_mission_process",
                    return_value={
                        "missionProcessFound": True,
                        "missionProcessTerminated": True,
                    },
                ) as terminate_process,
                mock.patch.object(self.bridge, "append_audit"),
                mock.patch.object(self.bridge, "save_missions"),
            ):
                result = self.bridge.cancel_ea_factory_build_one_click(
                    build["id"],
                    {
                        "runId": build["oneClickRun"]["runId"],
                        "idempotencyKey": build["oneClickRun"]["idempotencyKey"],
                    },
                )
            self.assertTrue(cancel_event.is_set())
            self.assertEqual(result["kind"], "ea_factory_one_click_cancelled")
            self.assertEqual(result["oneClickRun"]["status"], "cancelled")
            self.assertFalse(result["cancelPending"])
            self.assertFalse(result["bridgeStopped"])
            self.assertFalse(result["terminalShutdownAllowed"])
            cancel_mission.assert_called_once_with(
                owned_mission["id"],
                build_id=build["id"],
                stage_id="generate_source",
            )
            terminate_process.assert_called_once_with(owned_mission["id"])
        finally:
            self.bridge.EA_FACTORY_ONE_CLICK_THREADS.pop(build["id"], None)
            self.bridge.EA_FACTORY_ONE_CLICK_CANCEL_EVENTS.pop(build["id"], None)
            self.bridge.EA_FACTORY_ONE_CLICK_CANCEL_CONTEXTS.pop(build["id"], None)

    def test_cancel_stays_pending_until_visible_coordinator_returns(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="compile_validate")
        build["oneClickRun"]["status"] = "running"
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        state = self.state(build)
        cancel_event = threading.Event()

        class RunningCoordinator:
            @staticmethod
            def is_alive():
                return True

        self.bridge.EA_FACTORY_ONE_CLICK_THREADS[build["id"]] = RunningCoordinator()
        self.bridge.EA_FACTORY_ONE_CLICK_CANCEL_EVENTS[build["id"]] = cancel_event
        try:
            with (
                mock.patch.object(
                    self.bridge,
                    "_load_ea_factory_state_unlocked",
                    return_value=state,
                ),
                mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
                mock.patch.object(self.bridge, "load_missions", return_value=[]),
                mock.patch.object(self.bridge, "append_audit"),
            ):
                pending = self.bridge.cancel_ea_factory_build_one_click(
                    build["id"],
                    {
                        "runId": build["oneClickRun"]["runId"],
                        "idempotencyKey": build["oneClickRun"]["idempotencyKey"],
                    },
                )
                self.assertEqual(
                    pending["kind"],
                    "ea_factory_one_click_cancel_pending",
                )
                self.assertEqual(pending["oneClickRun"]["status"], "cancelling")
                self.assertTrue(pending["cancelPending"])
                self.assertTrue(pending["visibleActionWasInFlight"])
                self.assertFalse(pending["visibleActionInterruptionConfirmed"])
                self.assertIsNone(build["oneClickRun"]["completedAt"])

                self.bridge.EA_FACTORY_ONE_CLICK_THREADS.pop(build["id"], None)
                self.bridge.EA_FACTORY_ONE_CLICK_CANCEL_EVENTS.pop(build["id"], None)
                finalized = (
                    self.bridge._ea_factory_finalize_one_click_cancel_after_worker(
                        build["id"],
                        build["oneClickRun"]["runId"],
                        coordinator_returned=True,
                        owned_process_stop_confirmed=True,
                    )
                )
            self.assertTrue(finalized)
            self.assertEqual(build["oneClickRun"]["status"], "cancelled")
            self.assertIsNotNone(build["oneClickRun"]["completedAt"])
        finally:
            self.bridge.EA_FACTORY_ONE_CLICK_THREADS.pop(build["id"], None)
            self.bridge.EA_FACTORY_ONE_CLICK_CANCEL_EVENTS.pop(build["id"], None)
            self.bridge.EA_FACTORY_ONE_CLICK_CANCEL_CONTEXTS.pop(build["id"], None)

    def test_cancel_rejects_stale_run_identity_without_mutation(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="generate_source")
        state = self.state(build)
        before = copy.deepcopy(build["oneClickRun"])
        with mock.patch.object(
            self.bridge,
            "_load_ea_factory_state_unlocked",
            return_value=state,
        ):
            with self.assertRaises(self.bridge.RequestError) as rejected:
                self.bridge.cancel_ea_factory_build_one_click(
                    build["id"],
                    {
                        "runId": "ea-run-stale-request",
                        "idempotencyKey": before["idempotencyKey"],
                    },
                )
        self.assertEqual(rejected.exception.status, 409)
        self.assertEqual(build["oneClickRun"], before)

    def test_cancelled_run_replay_is_idempotent(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="generate_source")
        self.bridge._ea_factory_one_click_update(
            build["oneClickRun"],
            status="cancelled",
            current_stage_id="generate_source",
            failure_code="operator_cancelled",
            message_th="cancelled",
        )
        state = self.state(build)
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(self.bridge, "append_audit"),
            mock.patch.object(
                self.bridge,
                "_ea_factory_terminate_owned_mission_process",
            ) as terminate_process,
        ):
            replay = self.bridge.cancel_ea_factory_build_one_click(
                build["id"],
                {
                    "runId": build["oneClickRun"]["runId"],
                    "idempotencyKey": build["oneClickRun"]["idempotencyKey"],
                },
            )
        self.assertEqual(replay["kind"], "ea_factory_one_click_cancel_replayed")
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["oneClickRun"]["status"], "cancelled")
        terminate_process.assert_not_called()

    def test_cancelled_visible_request_is_rejected_before_adapter_invocation(self) -> None:
        build, state, request, _result, _artifact_rows = (
            self._visible_commit_fixture()
        )
        self.bridge._ea_factory_one_click_update(
            build["oneClickRun"],
            status="cancelling",
            current_stage_id="compile_validate",
            failure_code=None,
            message_th="stopping",
        )
        provider = mock.Mock(return_value={"ready": True})
        handler = mock.Mock(return_value={})
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                provider,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER",
                handler,
            ),
        ):
            with self.assertRaises(self.bridge.RequestError) as rejected:
                self.bridge._ea_factory_invoke_visible_front_office_handler(request)
        self.assertEqual(rejected.exception.status, 409)
        provider.assert_not_called()
        handler.assert_not_called()

    def test_cancelled_run_snapshot_rejects_late_visible_commit(self) -> None:
        build, state, request, result, _artifact_rows = self._visible_commit_fixture()
        self.bridge._ea_factory_one_click_update(
            build["oneClickRun"],
            status="cancelling",
            current_stage_id="compile_validate",
            failure_code=None,
            message_th="stopping",
        )
        with mock.patch.object(
            self.bridge,
            "_load_ea_factory_state_unlocked",
            return_value=state,
        ):
            with self.assertRaises(self.bridge.RequestError) as rejected:
                self.bridge._ea_factory_commit_visible_front_office_result(
                    request,
                    result,
                )
        self.assertEqual(rejected.exception.status, 409)
        stage = next(
            row for row in build["stages"] if row["id"] == "compile_validate"
        )
        self.assertEqual(stage["status"], "pending")

    def test_backtest_only_restart_is_idempotent_and_preserves_source_compile(self) -> None:
        build = self.backtest_restart_build()
        state = self.state(build)
        source_before = copy.deepcopy(build["versions"])
        completed_before = {
            stage["id"]: copy.deepcopy(stage)
            for stage in build["stages"]
            if stage["id"] in {
                "strategy_spec",
                "generate_source",
                "source_review",
                "compile_validate",
            }
        }
        stack, handles = self.backtest_restart_patch_stack(state)
        with stack:
            first = self.bridge.restart_ea_factory_build_backtest_only(
                build["id"],
                {
                    "runId": "ea-run-old-backtest",
                    "idempotencyKey": "restart-backtest-0001",
                },
            )
            replay = self.bridge.restart_ea_factory_build_backtest_only(
                build["id"],
                {
                    "runId": "ea-run-old-backtest",
                    "idempotencyKey": "restart-backtest-0001",
                },
            )
            validated_history = (
                self.bridge._ea_factory_revalidated_backtest_restart_history(
                    build
                )
            )
            validated_run = self.bridge._ea_factory_revalidated_one_click_run(
                build
            )

        self.assertEqual(first["kind"], "ea_factory_backtest_restarted")
        self.assertEqual(replay["kind"], "ea_factory_backtest_restart_replayed")
        self.assertTrue(replay["idempotentReplay"])
        self.assertNotEqual(build["oneClickRun"]["runId"], "ea-run-old-backtest")
        self.assertEqual(build["oneClickRun"]["currentStageId"], "backtest_recheck")
        self.assertEqual(build["versions"], source_before)
        for stage_id, previous in completed_before.items():
            self.assertEqual(
                next(row for row in build["stages"] if row["id"] == stage_id),
                previous,
            )
        self.assertEqual(len(build["oneClickRunHistory"]), 1)
        self.assertEqual(len(validated_history), 1)
        self.assertEqual(validated_run["runId"], build["oneClickRun"]["runId"])
        archived = build["oneClickRunHistory"][0]
        self.assertEqual(archived["previousRun"]["runId"], "ea-run-old-backtest")
        self.assertEqual(
            archived["backtestStage"]["missionId"],
            "mission-old-backtest",
        )
        self.assertRegex(archived["archiveDigest"], r"^[0-9a-f]{64}$")
        handles["start"].assert_called_once()
        handles["idle"].assert_called_once()
        handles["advance"].assert_not_called()
        handles["ai"].assert_not_called()

    def test_backtest_restart_revalidation_rejects_current_key_tampering(
        self,
    ) -> None:
        build = self.backtest_restart_build()
        state = self.state(build)
        stack, _handles = self.backtest_restart_patch_stack(state)
        with stack:
            self.bridge.restart_ea_factory_build_backtest_only(
                build["id"],
                {
                    "runId": "ea-run-old-backtest",
                    "idempotencyKey": "restart-key-binding-0001",
                },
            )
            tampered = copy.deepcopy(build)
            tampered["oneClickRun"]["idempotencyKey"] = (
                "restart-key-tampered-9999"
            )

            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge._ea_factory_revalidated_one_click_run(tampered)
            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge._ea_factory_revalidated_backtest_restart_history(
                    tampered
                )

    def test_backtest_restart_revalidation_rejects_current_binding_tampering(
        self,
    ) -> None:
        build = self.backtest_restart_build()
        state = self.state(build)
        stack, _handles = self.backtest_restart_patch_stack(state)
        with stack:
            self.bridge.restart_ea_factory_build_backtest_only(
                build["id"],
                {
                    "runId": "ea-run-old-backtest",
                    "idempotencyKey": "restart-binding-leaf-0001",
                },
            )
            tampered = copy.deepcopy(build)
            current_run = tampered["oneClickRun"]
            current_run["terminalBinding"] = {
                "platform": "mt4",
                "candidateId": "mtc-different-terminal",
                "selectionRevision": 999,
                "bindingDigest": "9" * 64,
            }
            current_run["visibleAction"]["operationId"] = (
                self.bridge._ea_factory_one_click_visible_operation_id(
                    tampered,
                    current_run,
                    "backtest_recheck",
                )
            )

            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge._ea_factory_revalidated_one_click_run(tampered)
            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge._ea_factory_revalidated_backtest_restart_history(
                    tampered
                )

    def test_visible_action_stage_is_cross_bound_to_current_stage(self) -> None:
        build = self.backtest_restart_build(status="awaiting_visible_terminal")
        run = build["oneClickRun"]
        self.assertTrue(
            self.bridge._ea_factory_one_click_reserve_visible_action(
                build,
                run,
                "backtest_recheck",
            )
        )
        self.assertIsInstance(
            self.bridge._ea_factory_revalidated_one_click_run(build),
            dict,
        )

        mismatched = copy.deepcopy(build)
        mismatched["oneClickRun"]["currentStageId"] = "compile_validate"
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.bridge._ea_factory_revalidated_one_click_run(mismatched)

        advanced = copy.deepcopy(build)
        advanced_run = advanced["oneClickRun"]
        advanced_run["status"] = "queued"
        advanced_run["currentStageId"] = "final_report"
        advanced_run["visibleAction"]["state"] = "completed"
        backtest_stage = self.bridge._ea_factory_stage_row(
            advanced,
            "backtest_recheck",
        )
        backtest_stage.update({
            "status": "completed",
            "evidenceVerified": True,
        })
        self.assertIsInstance(
            self.bridge._ea_factory_revalidated_one_click_run(advanced),
            dict,
        )

    def test_backtest_restart_revalidation_rejects_coherent_leaf_stage_tampering(
        self,
    ) -> None:
        build = self.backtest_restart_build()
        state = self.state(build)
        stack, _handles = self.backtest_restart_patch_stack(state)
        with stack:
            self.bridge.restart_ea_factory_build_backtest_only(
                build["id"],
                {
                    "runId": "ea-run-old-backtest",
                    "idempotencyKey": "restart-leaf-stage-binding-0001",
                },
            )
            tampered = copy.deepcopy(build)
            current_run = tampered["oneClickRun"]
            current_run["currentStageId"] = "compile_validate"
            current_run["visibleAction"]["stageId"] = "compile_validate"
            current_run["visibleAction"]["operationId"] = (
                self.bridge._ea_factory_one_click_visible_operation_id(
                    tampered,
                    current_run,
                    "compile_validate",
                )
            )

            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge._ea_factory_revalidated_one_click_run(tampered)
            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge._ea_factory_revalidated_backtest_restart_history(
                    tampered
                )

            advanced = copy.deepcopy(build)
            advanced_run = advanced["oneClickRun"]
            advanced_run["status"] = "queued"
            advanced_run["currentStageId"] = "final_report"
            advanced_run["visibleAction"]["state"] = "completed"
            self.bridge._ea_factory_stage_row(
                advanced,
                "backtest_recheck",
            ).update({
                "status": "completed",
                "evidenceVerified": True,
            })
            self.assertIsInstance(
                self.bridge._ea_factory_revalidated_one_click_run(advanced),
                dict,
            )
            self.assertEqual(
                len(
                    self.bridge._ea_factory_revalidated_backtest_restart_history(
                        advanced
                    )
                ),
                1,
            )

    def test_backtest_only_restart_rejects_run_stage_mismatch(self) -> None:
        build = self.backtest_restart_build()
        build["oneClickRun"]["currentStageId"] = "compile_validate"
        state = self.state(build)
        stack, handles = self.backtest_restart_patch_stack(state)

        with stack, self.assertRaises(self.bridge.RequestError) as raised:
            self.bridge.restart_ea_factory_build_backtest_only(
                build["id"],
                {
                    "runId": "ea-run-old-backtest",
                    "idempotencyKey": "restart-stage-mismatch-0001",
                },
            )

        self.assertEqual(
            raised.exception.code,
            "backtest_restart_run_stage_mismatch",
        )
        handles["idle"].assert_not_called()
        handles["write"].assert_not_called()
        handles["start"].assert_not_called()

    def test_backtest_restart_history_rejects_digest_coherent_stage_tampering(
        self,
    ) -> None:
        build = self.backtest_restart_build()
        state = self.state(build)
        stack, _handles = self.backtest_restart_patch_stack(state)
        with stack:
            self.bridge.restart_ea_factory_build_backtest_only(
                build["id"],
                {
                    "runId": "ea-run-old-backtest",
                    "idempotencyKey": "restart-stage-binding-0001",
                },
            )
            tampered = copy.deepcopy(build)
            archive = tampered["oneClickRunHistory"][0]
            archive["previousRun"]["currentStageId"] = "compile_validate"
            archive["previousRunDigest"] = self.bridge.payload_digest(
                "ea-factory-archived-one-click-run-v1",
                archive["previousRun"],
            )
            archive["archiveDigest"] = (
                self.bridge._ea_factory_backtest_restart_archive_digest(archive)
            )
            tampered["oneClickRun"]["restartArchiveDigest"] = archive[
                "archiveDigest"
            ]

            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge._ea_factory_revalidated_backtest_restart_history(
                    tampered
                )

    def test_backtest_restart_history_rejects_digest_coherent_binding_hop(
        self,
    ) -> None:
        build = self.backtest_restart_build()
        state = self.state(build)
        stack, _handles = self.backtest_restart_patch_stack(state)
        with stack:
            first = self.bridge.restart_ea_factory_build_backtest_only(
                build["id"],
                {
                    "runId": "ea-run-old-backtest",
                    "idempotencyKey": "restart-binding-hop-0001",
                },
            )
            self.bridge._ea_factory_one_click_update(
                build["oneClickRun"],
                status="failed",
                current_stage_id="backtest_recheck",
                failure_code="visible_backtest_failed",
                message_th="first restarted Backtest stopped",
            )
            self.bridge.restart_ea_factory_build_backtest_only(
                build["id"],
                {
                    "runId": first["oneClickRun"]["runId"],
                    "idempotencyKey": "restart-binding-hop-0002",
                },
            )
            tampered = copy.deepcopy(build)
            second_archive = tampered["oneClickRunHistory"][1]
            intermediate_run = second_archive["previousRun"]
            changed_binding = {
                "platform": "mt4",
                "candidateId": "mtc-different-terminal",
                "selectionRevision": 999,
                "bindingDigest": "9" * 64,
            }
            intermediate_run["terminalBinding"] = copy.deepcopy(changed_binding)
            intermediate_run["visibleAction"]["operationId"] = (
                self.bridge._ea_factory_one_click_visible_operation_id(
                    tampered,
                    intermediate_run,
                    "backtest_recheck",
                )
            )
            second_archive["previousRunDigest"] = self.bridge.payload_digest(
                "ea-factory-archived-one-click-run-v1",
                intermediate_run,
            )
            second_archive["archiveDigest"] = (
                self.bridge._ea_factory_backtest_restart_archive_digest(
                    second_archive
                )
            )
            current_run = tampered["oneClickRun"]
            current_run["terminalBinding"] = copy.deepcopy(changed_binding)
            current_run["visibleAction"]["operationId"] = (
                self.bridge._ea_factory_one_click_visible_operation_id(
                    tampered,
                    current_run,
                    "backtest_recheck",
                )
            )
            current_run["restartArchiveDigest"] = second_archive[
                "archiveDigest"
            ]

            self.assertIsInstance(
                self.bridge._ea_factory_revalidated_one_click_run(tampered),
                dict,
            )
            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge._ea_factory_revalidated_backtest_restart_history(
                    tampered
                )

    def test_restart_revalidation_uses_archived_compile_run_and_current_backtest_run(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reports_dir = root / "data" / "runtime" / "reports"
            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                build, compile_stage, _compile_report = (
                    self.restart_revalidation_fixture(root, reports_dir)
                )
                original_run = copy.deepcopy(build["oneClickRun"])
                state = self.state(build)
                with (
                    mock.patch.object(
                        self.bridge,
                        "_load_ea_factory_state_unlocked",
                        return_value=state,
                    ),
                    mock.patch.object(self.bridge, "load_missions", return_value=[]),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_active_worker_payload",
                        return_value=None,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_any_one_click_coordinator_alive",
                        return_value=False,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_one_click_terminal_binding_current",
                        return_value=True,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_backtest_restart_idle_probe",
                        return_value={"testerStartState": "Start"},
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_start_ea_factory_one_click_thread",
                        return_value=True,
                    ),
                    mock.patch.object(self.bridge, "append_audit"),
                ):
                    restarted = (
                        self.bridge.restart_ea_factory_build_backtest_only(
                            build["id"],
                            {
                                "runId": original_run["runId"],
                                "idempotencyKey": (
                                    "restart-history-revalidation-0001"
                                ),
                            },
                        )
                    )

                current_run = copy.deepcopy(build["oneClickRun"])
                self.assertNotEqual(current_run["runId"], original_run["runId"])
                self.assertEqual(restarted["oneClickRun"]["runId"], current_run["runId"])
                self.assertEqual(len(build["oneClickRunHistory"]), 1)
                archived_run = build["oneClickRunHistory"][0]["previousRun"]
                self.assertEqual(archived_run, original_run)

                with (
                    mock.patch.object(
                        self.bridge,
                        "RUNTIME_REPORTS_DIR",
                        reports_dir,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_visible_png_valid",
                        return_value=True,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_visible_receipt_valid",
                        return_value=True,
                    ),
                ):
                    validated = self.bridge._ea_factory_revalidated_build(build)
                    read_model = self.bridge._ea_factory_one_click_read_model(
                        validated
                    )

                resolved_compile_run = (
                    self.bridge._ea_factory_visible_evidence_run_snapshot(
                        build,
                        compile_stage,
                        compile_stage["visibleOperationId"],
                    )
                )
                self.assertEqual(
                    resolved_compile_run["runId"],
                    original_run["runId"],
                )
                self.assertEqual(read_model["runId"], current_run["runId"])
                backtest_stage = self.bridge._ea_factory_stage_row(
                    build,
                    "backtest_recheck",
                )
                current_backtest_operation = current_run["visibleAction"][
                    "operationId"
                ]
                resolved_backtest_run = (
                    self.bridge._ea_factory_visible_evidence_run_snapshot(
                        build,
                        backtest_stage,
                        current_backtest_operation,
                    )
                )
                self.assertEqual(
                    resolved_backtest_run["runId"],
                    current_run["runId"],
                )
                archived_backtest_operation = (
                    self.bridge._ea_factory_one_click_visible_operation_id(
                        build,
                        original_run,
                        "backtest_recheck",
                    )
                )
                self.assertIsNone(
                    self.bridge._ea_factory_visible_evidence_run_snapshot(
                        build,
                        backtest_stage,
                        archived_backtest_operation,
                    )
                )

                tampered = copy.deepcopy(build)
                tampered["oneClickRunHistory"][0]["archiveDigest"] = "0" * 64
                with (
                    mock.patch.object(
                        self.bridge,
                        "RUNTIME_REPORTS_DIR",
                        reports_dir,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_visible_png_valid",
                        return_value=True,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_visible_receipt_valid",
                        return_value=True,
                    ),
                    self.assertRaises(self.bridge.DataIntegrityError),
                ):
                    self.bridge._ea_factory_revalidated_build(tampered)

                missing_history = copy.deepcopy(build)
                missing_history["oneClickRunHistory"] = []
                with (
                    mock.patch.object(
                        self.bridge,
                        "RUNTIME_REPORTS_DIR",
                        reports_dir,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_visible_png_valid",
                        return_value=True,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_visible_receipt_valid",
                        return_value=True,
                    ),
                    self.assertRaises(self.bridge.DataIntegrityError),
                ):
                    self.bridge._ea_factory_revalidated_build(missing_history)

    def test_backtest_restart_contract_accepts_real_mt5_compile_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                build, registered, binary_path = (
                    self.backtest_restart_mt5_manifest_fixture(root)
                )
                binary = next(
                    row for row in registered if row["extension"] == ".ex5"
                )

                contract = self.bridge._ea_factory_backtest_restart_contract(build)

                self.assertEqual(binary["artifactKind"], "compile_evidence")
                self.assertEqual(binary["stageId"], "compile_validate")
                self.assertEqual(
                    binary["reportId"],
                    next(
                        row
                        for row in build["stages"]
                        if row["id"] == "compile_validate"
                    )["reportId"],
                )
                self.assertIn(
                    binary["fileId"],
                    {
                        row["fileId"]
                        for row in contract["compileEvidence"]["artifacts"]
                    },
                )

                binary_path.write_bytes(b"tampered compiled mt5 fixture")
                with self.assertRaises(self.bridge.RequestError) as tampered:
                    self.bridge._ea_factory_backtest_restart_contract(build)
                self.assertEqual(
                    tampered.exception.code,
                    "backtest_restart_compile_digest_changed",
                )

    def test_backtest_restart_contract_rejects_non_binary_compile_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                build, registered, _binary_path = (
                    self.backtest_restart_mt5_manifest_fixture(root)
                )
                compile_stage = next(
                    row
                    for row in build["stages"]
                    if row["id"] == "compile_validate"
                )
                compile_log = next(
                    row
                    for row in registered
                    if row["relativePath"] == "Reports/compile.txt"
                )
                compile_stage["artifacts"] = [compile_log["fileId"]]

                with self.assertRaises(self.bridge.RequestError) as rejected:
                    self.bridge._ea_factory_backtest_restart_contract(build)

                self.assertEqual(
                    rejected.exception.code,
                    "backtest_restart_compile_digest_changed",
                )

    def test_backtest_restart_thread_start_failure_is_durable_and_retry_safe(self) -> None:
        build = self.backtest_restart_build()
        state = self.state(build)
        stack, handles = self.backtest_restart_patch_stack(state)
        handles["start"].side_effect = [RuntimeError("native thread unavailable"), True]

        with stack:
            failed_start = self.bridge.restart_ea_factory_build_backtest_only(
                build["id"],
                {
                    "runId": "ea-run-old-backtest",
                    "idempotencyKey": "restart-start-failure-0001",
                },
            )
            failed_run_id = build["oneClickRun"]["runId"]
            failed_snapshot = copy.deepcopy(build["oneClickRun"])

            replay = self.bridge.restart_ea_factory_build_backtest_only(
                build["id"],
                {
                    "runId": "ea-run-old-backtest",
                    "idempotencyKey": "restart-start-failure-0001",
                },
            )
            with self.assertRaises(self.bridge.RequestError) as reused_key:
                self.bridge.restart_ea_factory_build_backtest_only(
                    build["id"],
                    {
                        "runId": failed_run_id,
                        "idempotencyKey": "restart-start-failure-0001",
                    },
                )
            retry = self.bridge.restart_ea_factory_build_backtest_only(
                build["id"],
                {
                    "runId": failed_run_id,
                    "idempotencyKey": "restart-start-failure-0002",
                },
            )
            validated_history = (
                self.bridge._ea_factory_revalidated_backtest_restart_history(
                    build
                )
            )
            validated_run = self.bridge._ea_factory_revalidated_one_click_run(
                build
            )

        self.assertFalse(failed_start["workerStarted"])
        self.assertEqual(failed_snapshot["status"], "failed")
        self.assertEqual(
            failed_snapshot["failureCode"],
            "backtest_restart_worker_not_started",
        )
        self.assertIsNotNone(failed_snapshot["completedAt"])
        self.assertEqual(replay["kind"], "ea_factory_backtest_restart_replayed")
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(replay["oneClickRun"]["status"], "failed")
        self.assertFalse(replay["sourceRegenerated"])
        self.assertFalse(replay["compileRepeated"])
        self.assertEqual(reused_key.exception.code, "backtest_restart_key_reused")
        self.assertTrue(retry["workerStarted"])
        self.assertEqual(retry["oneClickRun"]["status"], "queued")
        self.assertEqual(len(build["oneClickRunHistory"]), 2)
        self.assertEqual(len(validated_history), 2)
        self.assertEqual(validated_run["runId"], build["oneClickRun"]["runId"])
        self.assertEqual(handles["start"].call_count, 2)
        # First commit + durable failure, then the fresh-key retry commit.
        self.assertEqual(handles["write"].call_count, 3)


    def test_backtest_restart_read_model_exposes_only_exact_terminal_state(self) -> None:
        build = self.backtest_restart_build()
        with mock.patch.object(
            self.bridge,
            "_ea_factory_file_catalog",
            return_value=[],
        ):
            model = self.bridge._ea_factory_one_click_read_model(build)
        self.assertTrue(model["canRestartBacktest"])
        self.assertEqual(
            model["restartBacktestEndpoint"],
            "/api/props/right_server_racks/ea-factory/builds/"
            "ea-build-one-click-test/restart-backtest",
        )
        build["oneClickRun"]["status"] = "running"
        build["oneClickRun"]["completedAt"] = None
        with mock.patch.object(
            self.bridge,
            "_ea_factory_file_catalog",
            return_value=[],
        ):
            active_model = self.bridge._ea_factory_one_click_read_model(build)
        self.assertFalse(active_model["canRestartBacktest"])

    def test_backtest_only_restart_rejects_active_cancelling_and_active_coordinator(self) -> None:
        expected_codes = {
            "queued": "backtest_restart_run_not_terminal",
            "running": "backtest_restart_run_not_terminal",
            "cancelling": "backtest_restart_cancellation_pending",
        }
        for status, expected_code in expected_codes.items():
            with self.subTest(status=status):
                build = self.backtest_restart_build(status=status)
                state = self.state(build)
                with mock.patch.object(
                    self.bridge,
                    "_load_ea_factory_state_unlocked",
                    return_value=state,
                ):
                    with self.assertRaises(self.bridge.RequestError) as raised:
                        self.bridge.restart_ea_factory_build_backtest_only(
                            build["id"],
                            {
                                "runId": "ea-run-old-backtest",
                                "idempotencyKey": f"restart-{status}-0001",
                            },
                        )
                self.assertEqual(raised.exception.status, 409)
                self.assertEqual(raised.exception.code, expected_code)

        build = self.backtest_restart_build()
        state = self.state(build)
        stack, handles = self.backtest_restart_patch_stack(
            state,
            coordinator_alive=True,
        )
        with stack, self.assertRaises(self.bridge.RequestError) as raised:
            self.bridge.restart_ea_factory_build_backtest_only(
                build["id"],
                {
                    "runId": "ea-run-old-backtest",
                    "idempotencyKey": "restart-coordinator-0001",
                },
            )
        self.assertEqual(raised.exception.code, "backtest_restart_worker_active")
        handles["write"].assert_not_called()
        handles["start"].assert_not_called()

    def test_backtest_only_restart_rejects_coverage_upgrade_required_build(self) -> None:
        build = self.backtest_restart_build()
        build["coverageUpgradeRequired"] = True
        build["status"] = "coverage_upgrade_required"
        state = self.state(build)
        with mock.patch.object(
            self.bridge,
            "_load_ea_factory_state_unlocked",
            return_value=state,
        ):
            with self.assertRaises(self.bridge.RequestError) as raised:
                self.bridge.restart_ea_factory_build_backtest_only(
                    build["id"],
                    {
                        "runId": "ea-run-old-backtest",
                        "idempotencyKey": "restart-coverage-upgrade-0001",
                    },
                )
        self.assertEqual(raised.exception.status, 409)
        self.assertEqual(
            raised.exception.code,
            "backtest_restart_coverage_upgrade_required",
        )

    def test_backtest_only_restart_rejects_stale_binding_touched_final_and_stop_state(self) -> None:
        build = self.backtest_restart_build()
        state = self.state(build)
        stack, handles = self.backtest_restart_patch_stack(
            state,
            terminal_current=False,
        )
        with stack, self.assertRaises(self.bridge.RequestError) as stale:
            self.bridge.restart_ea_factory_build_backtest_only(
                build["id"],
                {
                    "runId": "ea-run-old-backtest",
                    "idempotencyKey": "restart-stale-terminal-0001",
                },
            )
        self.assertEqual(stale.exception.code, "terminal_selection_changed")
        handles["write"].assert_not_called()

        touched = self.backtest_restart_build()
        final_stage = next(
            row for row in touched["stages"] if row["id"] == "final_report"
        )
        final_stage.update({
            "status": "failed",
            "missionId": "mission-final-touched",
            "blockedReasonCode": "final_failed",
        })
        touched_state = self.state(touched)
        stack, handles = self.backtest_restart_patch_stack(touched_state)
        with stack, self.assertRaises(self.bridge.RequestError) as final_error:
            self.bridge.restart_ea_factory_build_backtest_only(
                touched["id"],
                {
                    "runId": "ea-run-old-backtest",
                    "idempotencyKey": "restart-final-touched-0001",
                },
            )
        self.assertEqual(final_error.exception.code, "backtest_restart_stage_not_pristine")
        handles["write"].assert_not_called()

        stop_build = self.backtest_restart_build()
        with (
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                return_value={"ready": True, "testerStartState": "Stop"},
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_STRATEGY_TESTER_HANDLER",
                lambda **_kwargs: {},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_front_office_capability_ready",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_resolved_front_office_target",
                return_value={},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_default_tester_settings",
                return_value={},
            ),
            self.assertRaises(self.bridge.RequestError) as stop_error,
        ):
            self.bridge._ea_factory_backtest_restart_idle_probe(stop_build)
        self.assertEqual(stop_error.exception.code, "strategy_tester_still_running")

    def test_backtest_only_restart_rejects_source_or_compile_contract_drift(self) -> None:
        build = self.backtest_restart_build()
        state = self.state(build)
        first_contract = self.backtest_restart_contract("1" * 64)
        changed_contract = self.backtest_restart_contract("2" * 64)
        stack, handles = self.backtest_restart_patch_stack(
            state,
            contract_side_effect=[first_contract, changed_contract],
        )
        with stack, self.assertRaises(self.bridge.RequestError) as raised:
            self.bridge.restart_ea_factory_build_backtest_only(
                build["id"],
                {
                    "runId": "ea-run-old-backtest",
                    "idempotencyKey": "restart-contract-drift-0001",
                },
            )
        self.assertEqual(raised.exception.code, "backtest_restart_contract_changed")
        handles["write"].assert_not_called()
        handles["start"].assert_not_called()

    def test_backtest_restart_mints_distinct_artifact_paths_and_rejects_old_late_commit(self) -> None:
        build = self.backtest_restart_build()
        old_run = build["oneClickRun"]
        self.assertTrue(
            self.bridge._ea_factory_one_click_reserve_visible_action(
                build,
                old_run,
                "backtest_recheck",
            )
        )
        state = self.state(build)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            visible_patches = (
                mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                    lambda **_kwargs: {},
                ),
                mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_VISIBLE_STRATEGY_TESTER_HANDLER",
                    lambda **_kwargs: {},
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_one_click_terminal_binding_current",
                    return_value=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_build_directory",
                    return_value=root,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_resolved_front_office_target",
                    return_value={},
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_default_tester_settings",
                    return_value={},
                ),
            )
            with ExitStack() as visible_stack:
                for patcher in visible_patches:
                    visible_stack.enter_context(patcher)
                old_request = self.bridge._ea_factory_prepare_visible_front_office_request(
                    build,
                    next(
                        row
                        for row in build["stages"]
                        if row["id"] == "backtest_recheck"
                    ),
                )

                restart_stack, handles = self.backtest_restart_patch_stack(state)
                with restart_stack:
                    result = self.bridge.restart_ea_factory_build_backtest_only(
                        build["id"],
                        {
                            "runId": "ea-run-old-backtest",
                            "idempotencyKey": "restart-artifact-paths-0001",
                        },
                    )
                new_request = self.bridge._ea_factory_prepare_visible_front_office_request(
                    build,
                    next(
                        row
                        for row in build["stages"]
                        if row["id"] == "backtest_recheck"
                    ),
                )

            old_operation = old_request["visibleOperation"]["operationId"]
            new_operation = new_request["visibleOperation"]["operationId"]
            self.assertNotEqual(old_operation, new_operation)
            self.assertNotEqual(old_request["missionId"], new_request["missionId"])
            self.assertNotEqual(old_request["reportId"], new_request["reportId"])
            self.assertNotEqual(
                root / "Reports" / f"{old_operation}-tester.htm",
                root / "Reports" / f"{new_operation}-tester.htm",
            )
            self.assertEqual(result["oneClickRun"]["runId"], build["oneClickRun"]["runId"])
            handles["advance"].assert_not_called()
            handles["ai"].assert_not_called()

            with (
                mock.patch.object(
                    self.bridge,
                    "_load_ea_factory_state_unlocked",
                    return_value=state,
                ),
                self.assertRaises(self.bridge.RequestError) as stale,
            ):
                self.bridge._ea_factory_assert_visible_front_office_request_current(
                    old_request
                )
            self.assertEqual(stale.exception.status, 409)

    def test_production_visible_adapter_is_wired_fail_closed_at_runtime(self) -> None:
        class Adapter:
            supported_platforms = frozenset({"mt4"})

            def capability_provider(self, **_kwargs):
                return {"ready": False}

            def compile_handler(self, *, request):
                return request

            def backtest_handler(self, *, request):
                return request

        previous = (
            self.bridge.EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER,
            self.bridge.EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER,
            self.bridge.EA_FACTORY_VISIBLE_STRATEGY_TESTER_HANDLER,
            self.bridge.EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER,
        )
        adapter = Adapter()
        try:
            with (
                mock.patch.object(
                    self.bridge,
                    "create_production_visible_front_office_adapter",
                    return_value=adapter,
                ) as factory,
                mock.patch.object(
                    self.bridge,
                    "create_production_visible_front_office_adapter_mt5",
                    side_effect=RuntimeError("mt5 adapter unavailable"),
                ) as mt5_factory,
                mock.patch.object(self.bridge, "append_audit") as audit,
            ):
                configured = (
                    self.bridge.configure_ea_factory_visible_front_office_adapter()
                )
            self.assertTrue(configured)
            factory.assert_called_once_with(
                target_resolver=(
                    self.bridge._ea_factory_visible_adapter_target_resolver
                )
            )
            mt5_factory.assert_called_once_with(
                target_resolver=(
                    self.bridge._ea_factory_visible_adapter_target_resolver
                )
            )
            self.assertEqual(
                self.bridge._ea_factory_front_office_supported_platforms(),
                frozenset({"mt4"}),
            )
            self.assertIsNone(self.bridge.EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER)
            self.assertEqual(
                audit.call_args.args[0]["type"],
                "ea_factory.visible_front_office_adapter_configured",
            )
        finally:
            (
                self.bridge.EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER,
                self.bridge.EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER,
                self.bridge.EA_FACTORY_VISIBLE_STRATEGY_TESTER_HANDLER,
                self.bridge.EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER,
            ) = previous

    def test_visible_adapter_configuration_failure_clears_all_handlers(self) -> None:
        previous = (
            self.bridge.EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER,
            self.bridge.EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER,
            self.bridge.EA_FACTORY_VISIBLE_STRATEGY_TESTER_HANDLER,
            self.bridge.EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER,
        )
        try:
            self.bridge.EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER = lambda **_kwargs: {}
            self.bridge.EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER = lambda **_kwargs: {}
            self.bridge.EA_FACTORY_VISIBLE_STRATEGY_TESTER_HANDLER = lambda **_kwargs: {}
            self.bridge.EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER = lambda **_kwargs: {}
            with (
                mock.patch.object(
                    self.bridge,
                    "create_production_visible_front_office_adapter",
                    side_effect=RuntimeError("adapter setup failed"),
                ),
                mock.patch.object(self.bridge, "append_audit") as audit,
            ):
                configured = (
                    self.bridge.configure_ea_factory_visible_front_office_adapter()
                )
            self.assertFalse(configured)
            self.assertIsNone(
                self.bridge.EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER
            )
            self.assertIsNone(
                self.bridge.EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER
            )
            self.assertIsNone(
                self.bridge.EA_FACTORY_VISIBLE_STRATEGY_TESTER_HANDLER
            )
            self.assertIsNone(
                self.bridge.EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER
            )
            self.assertEqual(
                audit.call_args.args[0]["type"],
                "ea_factory.visible_front_office_adapter_unavailable",
            )
        finally:
            (
                self.bridge.EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER,
                self.bridge.EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER,
                self.bridge.EA_FACTORY_VISIBLE_STRATEGY_TESTER_HANDLER,
                self.bridge.EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER,
            ) = previous

    def test_visible_adapter_resolver_uses_only_current_backend_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            install = root / "terminal-install"
            data = root / "terminal-data"
            install.mkdir()
            (data / "MQL4").mkdir(parents=True)
            terminal = install / "terminal.exe"
            compiler = install / "metaeditor.exe"
            terminal.write_bytes(b"terminal")
            compiler.write_bytes(b"compiler")
            binding = {
                "platform": "mt4",
                "candidateId": "mtc-current-terminal",
                "selectionRevision": 9,
                "bindingDigest": "d" * 64,
            }
            context = {
                "record": {
                    "dataPath": str(data),
                    "localPath": str(data),
                }
            }
            target = {
                **binding,
                "installPath": install,
                "compilerPath": compiler,
            }
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_metaeditor_target_context",
                    return_value=(context, target),
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_path_is_link_or_reparse",
                    return_value=False,
                ),
            ):
                resolved = self.bridge._ea_factory_visible_adapter_target_resolver(
                    platform="mt4",
                    terminal_binding=copy.deepcopy(binding),
                )
                self.assertEqual(Path(resolved["terminalPath"]), terminal.resolve())
                self.assertEqual(Path(resolved["compilerPath"]), compiler.resolve())
                with self.assertRaises(
                    self.bridge.VisibleTerminalAdapterError
                ) as mismatch:
                    self.bridge._ea_factory_visible_adapter_target_resolver(
                        platform="mt4",
                        terminal_binding={**binding, "selectionRevision": 10},
                    )
            self.assertEqual(mismatch.exception.code, "terminal_binding_mismatch")


if __name__ == "__main__":
    unittest.main()
