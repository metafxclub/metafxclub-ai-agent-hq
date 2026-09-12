from __future__ import annotations

import copy
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "backend" / "local-runner" / "ea_factory_visible_terminal.py"
HELPERS_PATH = ROOT / "tests" / "test_ea_factory_visible_terminal.py"


def load_file(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CollectedBacktestRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_file("metafx_collected_recovery", MODULE_PATH)
        cls.helpers = load_file("metafx_visible_test_helpers", HELPERS_PATH)

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.fixture = self.helpers.AdapterFixture(
            Path(self.temporary.name),
            self.module,
        )
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def prime(self, adapter, request: dict) -> None:
        with mock.patch.object(
            self.module,
            "_powershell_executable",
            return_value=Path(os.environ.get("COMSPEC") or self.fixture.terminal),
        ):
            capability = adapter.capability_provider(
                platform=request["platform"],
                stage_id=request["stageId"],
                terminal_binding=request["terminalBinding"],
                visible_operation=request["visibleOperation"],
                resolved_target=request["resolvedTarget"],
                tester_settings=request.get("testerSettings"),
            )
        self.assertTrue(capability["ready"])

    def make_adapter(self, *, omit_report_reuse_proof: bool = False):
        actions: list[str] = []
        response_names: list[str] = []
        failed_after_report = False

        def runner(
            payload: dict,
            *,
            response_path: Path,
            timeout_seconds: int,
        ) -> dict:
            nonlocal failed_after_report
            action = str(payload["action"])
            actions.append(action)
            response_names.append(response_path.name)
            if action == "probe":
                return self.fixture.runner(
                    payload,
                    response_path=response_path,
                    timeout_seconds=timeout_seconds,
                )
            if action == "backtest" and not failed_after_report:
                failed_after_report = True
                self.helpers.write_png(Path(payload["settingsScreenshotPath"]))
                boundary = Path(payload["startBoundaryPath"])
                boundary.write_text(payload["startBoundaryJson"], encoding="utf-8")
                self.helpers.write_png(Path(payload["resultScreenshotPath"]))
                self.helpers.write_png(Path(payload["reportScreenshotPath"]))
                Path(payload["testerReportPath"]).write_bytes(
                    self.helpers.tester_report()
                )
                raise RuntimeError("simulated crash after report collection")
            if action != "recover_collected_backtest":
                raise AssertionError(action)
            result = {
                "schemaVersion": "ea-factory-visible-powershell-result-v1",
                "ok": True,
                "action": action,
                "operationId": payload["operationId"],
                "processBinding": self.fixture.runner.binding("backtest_recheck"),
                "postProcessBinding": self.fixture.runner.binding(
                    "backtest_recheck",
                    post=True,
                ),
                "recoveredWithoutStart": True,
                "startInvoked": False,
                "executionObservedRunning": False,
                "completedResultCheckpointReused": True,
                "completedReportCheckpointReused": True,
                "testerCompleted": True,
                "testerCompletionObservation": (
                    "recovery_collected_checkpoint_observed"
                ),
                "fastCompletionTesterLogAdvanced": False,
                "freshResultEvidenceCaptured": True,
                "exactExpertVerified": True,
                "selectedExpertReadback": payload["expertUiPath"],
                "deployedExpertSha256": payload["expectedDeployedExpertSha256"],
                "startBoundaryCommitted": True,
                "startBoundarySha256": payload["startBoundarySha256"],
                "actionRequestDigest": payload["actionRequestDigest"],
                "testerInputPresetApplied": False,
                "testerInputPresetReadbackVerified": False,
                "inputPresetReadbackSaved": False,
                "resolvedTesterSettings": {
                    "schemaVersion": "ea-factory-resolved-tester-settings-v1",
                    "expertFileName": payload["expertFileName"],
                    "symbol": "EURUSD",
                    "period": "H1",
                    "model": "every_tick",
                    "spread": "20",
                    "useDate": False,
                    "fromDate": None,
                    "toDate": None,
                    "deposit": None,
                    "visualMode": True,
                    "optimizationEnabled": False,
                    "shutdownTerminalAfterTest": False,
                },
            }
            if omit_report_reuse_proof:
                result.pop("completedReportCheckpointReused")
            return result

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=runner,
        )
        return adapter, actions, response_names

    def test_complete_report_checkpoint_recovers_without_start_or_rewrite(self) -> None:
        adapter, actions, response_names = self.make_adapter()
        request = self.fixture.request("backtest_recheck")
        operation_id = request["visibleOperation"]["operationId"]
        report = (
            self.fixture.workspace / "Reports" / f"{operation_id}-tester.htm"
        )
        result_image = (
            self.fixture.workspace
            / "Screenshots"
            / f"{operation_id}-tester-result.png"
        )
        report_image = (
            self.fixture.workspace
            / "Screenshots"
            / f"{operation_id}-tester-report.png"
        )

        self.prime(adapter, request)
        with self.assertRaisesRegex(RuntimeError, "after report collection"):
            adapter.backtest_handler(request=request)
        checkpoints = {
            path: (self.helpers.sha256(path), path.stat().st_mtime_ns)
            for path in (report, result_image, report_image)
        }

        self.prime(adapter, request)
        recovered = adapter.backtest_handler(request=request)

        self.assertEqual(actions.count("backtest"), 1)
        self.assertEqual(actions.count("recover_collected_backtest"), 1)
        self.assertIn(
            f"{operation_id}-backtest-ui-collected-recovery.json",
            response_names,
        )
        self.assertTrue(recovered["metrics"]["recoveredCollectedBacktest"])
        self.assertTrue(
            recovered["metrics"]["completedReportCheckpointReused"]
        )
        self.assertFalse(recovered["metrics"]["recoveryIssuedStart"])
        for path, (digest, mtime_ns) in checkpoints.items():
            self.assertEqual(self.helpers.sha256(path), digest)
            self.assertEqual(path.stat().st_mtime_ns, mtime_ns)

    def test_collected_recovery_requires_explicit_report_reuse_proof(self) -> None:
        adapter, actions, _response_names = self.make_adapter(
            omit_report_reuse_proof=True
        )
        request = self.fixture.request("backtest_recheck")

        self.prime(adapter, request)
        with self.assertRaisesRegex(RuntimeError, "after report collection"):
            adapter.backtest_handler(request=request)
        self.prime(adapter, request)
        with self.assertRaises(self.module.VisibleTerminalAdapterError) as error:
            adapter.backtest_handler(request=request)

        self.assertEqual(error.exception.code, "visible_backtest_result_invalid")
        self.assertEqual(actions.count("backtest"), 1)
        self.assertEqual(actions.count("recover_collected_backtest"), 1)

    def test_legacy_html_blocks_otherwise_complete_collected_recovery(self) -> None:
        adapter, actions, _response_names = self.make_adapter()
        request = self.fixture.request("backtest_recheck")
        operation_id = request["visibleOperation"]["operationId"]

        self.prime(adapter, request)
        with self.assertRaisesRegex(RuntimeError, "after report collection"):
            adapter.backtest_handler(request=request)
        legacy = (
            self.fixture.workspace / "Reports" / f"{operation_id}-tester.html"
        )
        legacy.write_text("legacy ambiguous report", encoding="utf-8")

        self.prime(adapter, request)
        with self.assertRaises(self.module.VisibleTerminalAdapterError) as error:
            adapter.backtest_handler(request=request)

        self.assertEqual(error.exception.code, "visible_action_state_uncertain")
        self.assertEqual(actions.count("recover_collected_backtest"), 0)


if __name__ == "__main__":
    unittest.main()
