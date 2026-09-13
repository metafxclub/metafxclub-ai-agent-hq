from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "backend" / "local-runner" / "ea_factory_visible_terminal.py"
POWERSHELL_PATH = MODULE_PATH.with_suffix(".ps1")


def load_module():
    spec = importlib.util.spec_from_file_location(
        "metafx_ea_factory_visible_terminal_test",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_png(path: Path) -> None:
    width = 32
    height = 32
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            row.extend(((x * 7) % 256, (y * 11) % 256, ((x + y) * 13) % 256))
        rows.append(bytes(row))

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    payload = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
        + chunk(b"IEND", b"")
    )
    # The production boundary also rejects implausibly tiny evidence files.
    if len(payload) < 1024:
        payload += b"\x00" * (1024 - len(payload))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def tester_value_token(value: object) -> str:
    return "true" if value is True else "false" if value is False else str(value)


def mt4_saved_set(preset: dict) -> bytes:
    lines = []
    for item in preset["assumptions"]:
        name = item["inputName"]
        token = tester_value_token(item["testerValue"])
        lines.extend(
            [
                f"{name}={token}",
                f"{name},F=0",
                f"{name},1={token}",
                f"{name},2={token}",
                f"{name},3={token}",
            ]
        )
    return ("\r\n".join(lines) + "\r\n").encode("utf-8-sig")


def tester_report(
    expert: str = "Strategy_v01",
    preset: dict | None = None,
    spread: str = "20",
    trade_sides: tuple[str, ...] = ("buy", "sell", "buy"),
    mismatched_chart_errors: int = 0,
) -> bytes:
    parameters = ""
    if preset is not None:
        values = []
        for item in preset["assumptions"]:
            token = tester_value_token(item["testerValue"])
            values.append(f"{item['inputName']}={token}")
        parameters = (
            "<tr><td>Parameters</td><td>" + "; ".join(values) + ";</td></tr>\n"
        )
    buy_count = trade_sides.count("buy")
    sell_count = trade_sides.count("sell")
    trade_rows = "\n".join(
        f"<tr><td>{index}</td><td>2026.01.{index:02d} 01:00</td>"
        f"<td>{side}</td><td>0.10</td></tr>"
        for index, side in enumerate(trade_sides, start=1)
    )
    return f"""<!doctype html><html><body><table>
<tr><td>Expert</td><td>{expert}</td></tr>
<tr><td>Symbol</td><td>EURUSD</td></tr>
<tr><td>Period</td><td>H1</td></tr>
<tr><td>Model</td><td>Every tick</td></tr>
<tr><td>Spread</td><td>{spread}</td></tr>
<tr><td>Initial deposit</td><td>10000.00</td></tr>
<tr><td>Mismatched chart errors</td><td>{mismatched_chart_errors}</td></tr>
    {parameters}<tr><td>Total trades</td><td>{len(trade_sides)}</td></tr>
    <tr><td>Short positions (won %)</td><td>{sell_count} (0%)</td></tr>
    <tr><td>Long positions (won %)</td><td>{buy_count} (0%)</td></tr>
    {trade_rows}
</table></body></html>""".encode("utf-8")


class MockVisibleRunner:
    def __init__(self, fixture: "AdapterFixture") -> None:
        self.fixture = fixture
        self.actions: list[str] = []
        self.payloads: list[dict] = []
        self.drift_post_pid = False
        self.drift_post_window = False
        self.pre_observation_age_seconds = 0
        self.tester_completion_observation = "stop_transition_observed"
        self.fast_completion_log_advanced_override: bool | None = None
        self.resolved_spread = "20"
        self.report_spread = "20"

    def binding(self, stage: str, *, post: bool = False) -> dict:
        observed = datetime.now(timezone.utc) + (
            timedelta(milliseconds=20)
            if post
            else -timedelta(seconds=self.pre_observation_age_seconds)
        )
        compile_stage = stage == "compile_validate"
        front_pid = 202 if compile_stage else 101
        if post and self.drift_post_pid:
            front_pid += 1
        return {
            "observedAt": observed.isoformat(),
            "terminalProcessId": 101,
            "terminalExecutablePath": str(self.fixture.terminal),
            "terminalWindowHandle": (
                1002 if post and self.drift_post_window else 1001
            ),
            "terminalWindowOwnerProcessId": 101,
            "terminalWindowTitle": "DemoPro - EURUSD,H1",
            "terminalWindowClass": "MetaQuotes::MetaTrader::4.00",
            "frontOfficeKind": "metaeditor" if compile_stage else "strategy_tester",
            "frontOfficeProcessId": front_pid,
            "frontOfficeExecutablePath": str(
                self.fixture.metaeditor if compile_stage else self.fixture.terminal
            ),
            "frontOfficeWindowHandle": 2002 if compile_stage else 3003,
            "frontOfficeWindowOwnerProcessId": front_pid,
            "frontOfficeWindowTitle": (
                "MetaEditor - [Strategy_v01.mq4]" if compile_stage else "Strategy Tester"
            ),
            "frontOfficeWindowClass": (
                "MetaQuotes::MetaEditor::5.00" if compile_stage else "AfxWnd42"
            ),
            "autoTradingState": False,
        }

    def __call__(self, payload: dict, *, response_path: Path, timeout_seconds: int) -> dict:
        action = str(payload["action"])
        self.actions.append(action)
        self.payloads.append(copy.deepcopy(payload))
        base = {
            "schemaVersion": "ea-factory-visible-powershell-result-v1",
            "ok": True,
            "action": action,
            "operationId": payload["operationId"],
        }
        if action == "probe":
            base["terminalProbe"] = {
                "observedAt": datetime.now(timezone.utc).isoformat(),
                "processId": 101,
                "executablePath": str(self.fixture.terminal),
                "windowHandle": 1001,
                "windowOwnerProcessId": 101,
                "windowTitle": "DemoPro - EURUSD,H1",
                "windowClass": "MetaQuotes::MetaTrader::4.00",
            }
            return base
        stage = "compile_validate" if "compile" in action else "backtest_recheck"
        base["processBinding"] = self.binding(stage)
        base["postProcessBinding"] = self.binding(stage, post=True)
        if action == "compile":
            Path(payload["binaryPath"]).write_bytes(b"compiled-ex4-v1")
            write_png(Path(payload["screenshotPath"]))
            base.update(
                {
                    "compileInvoked": True,
                    "exactSourceWindowVerified": True,
                    "compileWorkingCopyVerified": True,
                    "freshBinaryObserved": True,
                    "workingSourceSha256": sha256(Path(payload["sourcePath"])),
                    "workingBinarySha256": sha256(Path(payload["binaryPath"])),
                    "compileResultLine": "Result: 0 errors, 0 warnings",
                }
            )
        elif action == "recover_compile":
            base.update(
                {
                    "recoveredWithoutAction": True,
                    "exactSourceWindowVerified": True,
                    "compileWorkingCopyVerified": True,
                    "workingSourceSha256": sha256(Path(payload["sourcePath"])),
                    "workingBinarySha256": sha256(Path(payload["binaryPath"])),
                    "compileResultLine": "Result: 0 errors, 0 warnings",
                }
            )
        elif action == "recover_inflight_compile":
            binary_path = Path(payload["binaryPath"])
            if not binary_path.is_file():
                raise self.fixture.module.VisibleTerminalAdapterError(
                    "visible_compile_binary_not_fresh"
                )
            screenshot_reused = bool(payload["reuseExistingScreenshot"])
            if not screenshot_reused:
                write_png(Path(payload["screenshotPath"]))
            base.update(
                {
                    "compileInvoked": False,
                    "recoveredWithoutCompile": True,
                    "exactSourceWindowVerified": True,
                    "compileWorkingCopyVerified": True,
                    "freshBinaryObserved": True,
                    "screenshotReused": screenshot_reused,
                    "workingSourceSha256": sha256(Path(payload["sourcePath"])),
                    "workingBinarySha256": sha256(binary_path),
                    "compileResultLine": "Result: 0 errors, 0 warnings",
                }
            )
        elif action == "backtest":
            write_png(Path(payload["settingsScreenshotPath"]))
            preset = payload["testerSettings"].get("testerInputPreset")
            if preset is not None:
                write_png(Path(payload["inputPresetScreenshotPath"]))
                Path(payload["inputReadbackSetPath"]).write_bytes(mt4_saved_set(preset))
            boundary_path = Path(payload["startBoundaryPath"])
            boundary_path.parent.mkdir(parents=True, exist_ok=True)
            with boundary_path.open("xb") as handle:
                handle.write(payload["startBoundaryJson"].encode("utf-8"))
                handle.flush()
                os.fsync(handle.fileno())
            write_png(Path(payload["resultScreenshotPath"]))
            write_png(Path(payload["reportScreenshotPath"]))
            Path(payload["testerReportPath"]).write_bytes(
                tester_report(preset=preset, spread=self.report_spread)
            )
            base.update(
                {
                    "startInvoked": True,
                    "testerCompleted": True,
                    "testerCompletionObservation": self.tester_completion_observation,
                    "fastCompletionTesterLogAdvanced": (
                        self.fast_completion_log_advanced_override
                        if self.fast_completion_log_advanced_override is not None
                        else self.tester_completion_observation
                        == "fast_idle_evidence_required"
                    ),
                    "freshResultEvidenceCaptured": True,
                    "exactExpertVerified": True,
                    "selectedExpertReadback": payload["expertUiPath"],
                    "deployedExpertSha256": payload["expectedDeployedExpertSha256"],
                    "startBoundaryCommitted": True,
                    "startBoundarySha256": payload["startBoundarySha256"],
                    "actionRequestDigest": payload["actionRequestDigest"],
                    "testerInputPresetApplied": preset is not None,
                    "testerInputPresetReadbackVerified": preset is not None,
                    "inputPresetReadbackSaved": preset is not None,
                    "visualSpeedBefore": 20,
                    "visualSpeedAfter": 32,
                    "visualSpeedMaximum": 32,
                    "resolvedTesterSettings": {
                        "schemaVersion": "ea-factory-resolved-tester-settings-v1",
                        "expertFileName": payload["expertFileName"],
                        "symbol": "EURUSD",
                        "period": "H1",
                        "model": "every_tick",
                        "spread": self.resolved_spread,
                        "useDate": False,
                        "fromDate": None,
                        "toDate": None,
                        "deposit": None,
                        "visualMode": True,
                        "optimizationEnabled": False,
                        "shutdownTerminalAfterTest": False,
                    },
                }
            )
        elif action in {
            "recover_inflight_backtest",
            "recover_completed_backtest",
            "recover_collected_backtest",
        }:
            preset = payload["testerSettings"].get("testerInputPreset")
            collected_checkpoint = action == "recover_collected_backtest"
            completed_checkpoint = action in {
                "recover_completed_backtest",
                "recover_collected_backtest",
            }
            if not completed_checkpoint:
                write_png(Path(payload["resultScreenshotPath"]))
            if not collected_checkpoint:
                if not Path(payload["reportScreenshotPath"]).exists():
                    write_png(Path(payload["reportScreenshotPath"]))
                Path(payload["testerReportPath"]).write_bytes(
                    tester_report(preset=preset, spread=self.report_spread)
                )
            base.update(
                {
                    "recoveredWithoutStart": True,
                    "startInvoked": False,
                    "executionObservedRunning": not completed_checkpoint,
                    "completedResultCheckpointReused": completed_checkpoint,
                    "completedReportCheckpointReused": collected_checkpoint,
                    "testerCompleted": True,
                    "testerCompletionObservation": (
                        "recovery_collected_checkpoint_observed"
                        if collected_checkpoint
                        else (
                            "recovery_completed_checkpoint_observed"
                            if completed_checkpoint
                            else "recovery_stop_transition_observed"
                        )
                    ),
                    "fastCompletionTesterLogAdvanced": False,
                    "freshResultEvidenceCaptured": True,
                    "exactExpertVerified": True,
                    "selectedExpertReadback": payload["expertUiPath"],
                    "deployedExpertSha256": payload["expectedDeployedExpertSha256"],
                    "startBoundaryCommitted": True,
                    "startBoundarySha256": payload["startBoundarySha256"],
                    "actionRequestDigest": payload["actionRequestDigest"],
                    "testerInputPresetApplied": preset is not None,
                    "testerInputPresetReadbackVerified": preset is not None,
                    "inputPresetReadbackSaved": preset is not None,
                    "resolvedTesterSettings": {
                        "schemaVersion": "ea-factory-resolved-tester-settings-v1",
                        "expertFileName": payload["expertFileName"],
                        "symbol": "EURUSD",
                        "period": "H1",
                        "model": "every_tick",
                        "spread": self.resolved_spread,
                        "useDate": False,
                        "fromDate": None,
                        "toDate": None,
                        "deposit": None,
                        "visualMode": True,
                        "optimizationEnabled": False,
                        "shutdownTerminalAfterTest": False,
                    },
                }
            )
        elif action == "recover_backtest":
            base.update(
                {
                    "recoveredWithoutAction": True,
                    "exactExpertVerified": True,
                    "selectedExpertReadback": payload["expertUiPath"],
                    "deployedExpertSha256": payload["expectedDeployedExpertSha256"],
                    "settingsStillVerified": True,
                }
            )
        else:
            raise AssertionError(action)
        return base


class AdapterFixture:
    def __init__(self, root: Path, module) -> None:
        self.module = module
        self.root = root
        self.install = root / "RoboForex MT4 Terminal"
        self.data = root / "MetaQuotes" / "Terminal" / "ABC"
        self.workspace = root / "workspace"
        self.install.mkdir(parents=True)
        (self.data / "MQL4" / "Experts").mkdir(parents=True)
        for folder in ("EA_Versions", "Reports", "Screenshots", "Summaries", "Source"):
            (self.workspace / folder).mkdir(parents=True)
        self.terminal = self.install / "terminal.exe"
        self.metaeditor = self.install / "metaeditor.exe"
        self.terminal.write_bytes(b"terminal-image-v1")
        self.metaeditor.write_bytes(b"metaeditor-image-v1")
        self.source = self.workspace / "EA_Versions" / "Strategy_v01.mq4"
        self.source.write_text("#property strict\nvoid OnTick(){}\n", encoding="utf-8")
        self.binding = {
            "platform": "mt4",
            "candidateId": "mtc-robo-mt4",
            "selectionRevision": 7,
            "bindingDigest": "a" * 64,
        }
        self.target = {
            "terminalPath": str(self.terminal),
            "compilerPath": str(self.metaeditor),
            "installPath": str(self.install),
            "dataPath": str(self.data),
            "terminalExecutableSha256": sha256(self.terminal),
            "frontOfficeExecutableSha256": sha256(self.metaeditor),
        }
        self.runner = MockVisibleRunner(self)

    def request(self, stage: str, *, platform: str = "mt4") -> dict:
        operation = (
            "ea-visible-111111111111111111111111"
            if stage == "compile_validate"
            else "ea-visible-222222222222222222222222"
        )
        request = {
            "schemaVersion": "ea-factory-visible-front-office-request-v1",
            "buildId": "ea-build-visible-test",
            "stageId": stage,
            "platform": platform,
            "artifactKind": "expert_advisor",
            "workspaceRoot": str(self.workspace),
            "versions": [
                {
                    "versionFile": "EA_Versions/Strategy_v01.mq4",
                    "sourceDigest": sha256(self.source),
                }
            ],
            "terminalBinding": {**self.binding, "platform": platform},
            "resolvedTarget": copy.deepcopy(self.target),
            "visibleOperation": {
                "operationId": operation,
                "stageId": stage,
                "state": "reserved",
                "requiresExplicitResume": False,
            },
            "missionId": "mission-visible-test",
            "reportId": "report-visible-test",
            "safety": {
                "liveTradingAllowed": False,
                "autoTradingMayBeToggled": False,
                "chartAttachmentAllowed": False,
                "terminalShutdownAllowed": False,
                "optimizationAllowed": False,
                "visualModeRequired": stage == "backtest_recheck",
            },
            "capabilityCheckedAt": datetime.now(timezone.utc).isoformat(),
        }
        if stage == "backtest_recheck":
            request["testerSettings"] = {
                "schemaVersion": "ea-factory-tester-settings-v1",
                "expertFileName": "Strategy_v01.ex4",
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
        return request

    def adapter(self, *, backtest_verifier=None):
        return self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=(
                backtest_verifier or self.module.verify_mt4_tester_report
            ),
            powershell_runner=self.runner,
        )

    def enable_can_slim_tester_preset(self, request: dict) -> dict:
        self.source.write_text(
            '#property strict\n'
            'const string CERTIFIED_PROFILE_VERSION = "can-slim-mt4-certified-v3";\n'
            'input double InpStopLossPercent = 7.5;\n'
            'input double RewardRiskRatio = 2;\n'
            'input double RiskPercent = 1;\n'
            'input int ExecutionBufferPoints = 2;\n'
            'input int SlippagePoints = 3;\n'
            'input int MaxOpenPositionsPerSymbolMagic = 1;\n'
            'input int MagicNumber = 4186001;\n'
            'input int DailyMAPeriod = 50;\n'
            'input int WeeklyMAPeriod = 50;\n'
            'input int FiftyTwoWeekLookback = 52;\n'
            'input bool FundamentalCriteriaConfirmed = false;\n'
            'input bool ExternalBenchmarkUptrendConfirmed = false;\n'
            'input int MaxSpreadPoints = 30;\n'
            'void OnTick(){\n'
            '  if(!FundamentalCriteriaConfirmed) return;\n'
            '  if(!ExternalBenchmarkUptrendConfirmed) return;\n'
            '}\n',
            encoding="utf-8",
        )
        source_digest = sha256(self.source)
        request["versions"][0]["sourceDigest"] = source_digest
        assumptions = self.module._can_slim_certified_input_snapshot(
            self.source.read_text(encoding="utf-8")
        )
        if assumptions is None:
            raise AssertionError("CAN SLIM test source did not match certified profile")
        unsigned = {
            "schemaVersion": "ea-factory-tester-input-preset-v1",
            "mode": "full_certified_input_snapshot_with_explicit_simulation_assumptions",
            "scope": "mt4_strategy_tester_only",
            "sourceDigest": source_digest,
            "assumptions": copy.deepcopy(assumptions),
            "liveSourceDefaultsPreserved": True,
            "visibleExpertPropertiesRequired": True,
            "readbackRequired": True,
            "liveTradingAllowed": False,
            "fullCertifiedInputSnapshot": True,
            "simulationInputNames": list(
                self.module.CAN_SLIM_SIMULATION_INPUT_NAMES
            ),
        }
        request["testerSettings"]["testerInputPreset"] = {
            **unsigned,
            "presetDigest": hashlib.sha256(
                json.dumps(
                    unsigned,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
        }
        return request

    def enable_generic_tester_preset(
        self,
        request: dict,
        source_text: str,
    ) -> dict:
        self.source.write_text(source_text, encoding="utf-8")
        source_digest = sha256(self.source)
        request["versions"][0]["sourceDigest"] = source_digest
        assumptions = self.module._mt4_source_input_snapshot(source_text)
        if not assumptions:
            raise AssertionError("generic test source did not expose supported Inputs")
        unsigned = {
            "schemaVersion": "ea-factory-tester-input-preset-v1",
            "mode": "full_certified_input_snapshot_with_explicit_simulation_assumptions",
            "scope": "mt4_strategy_tester_only",
            "sourceDigest": source_digest,
            "assumptions": copy.deepcopy(assumptions),
            "liveSourceDefaultsPreserved": True,
            "visibleExpertPropertiesRequired": True,
            "readbackRequired": True,
            "liveTradingAllowed": False,
            "fullCertifiedInputSnapshot": True,
            "simulationInputNames": self.module._tester_simulation_input_names(
                assumptions
            ),
        }
        request["testerSettings"]["testerInputPreset"] = {
            **unsigned,
            "presetDigest": hashlib.sha256(
                json.dumps(
                    unsigned,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
        }
        return request


class VisibleTerminalAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.fixture = AdapterFixture(Path(self.temporary.name), self.module)

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

    def test_capability_is_fresh_read_only_mt4_and_mt5_is_fail_closed(self) -> None:
        adapter = self.fixture.adapter()
        operation = self.fixture.request("compile_validate")["visibleOperation"]
        with mock.patch.object(
            self.module,
            "_powershell_executable",
            return_value=Path(os.environ.get("COMSPEC") or self.fixture.terminal),
        ):
            ready = adapter.capability_provider(
                platform="mt4",
                stage_id="compile_validate",
                terminal_binding=self.fixture.binding,
                visible_operation=operation,
                resolved_target=self.fixture.target,
                tester_settings=None,
            )
            blocked = adapter.capability_provider(
                platform="mt5",
                stage_id="compile_validate",
                terminal_binding={**self.fixture.binding, "platform": "mt5"},
                visible_operation=operation,
                resolved_target=self.fixture.target,
                tester_settings=None,
            )
        self.assertTrue(ready["ready"])
        self.assertTrue(ready["freshProcessProbe"])
        self.assertEqual(adapter.supported_platforms, frozenset({"mt4"}))
        self.assertFalse(blocked["ready"])
        self.assertEqual(blocked["reasonCode"], "mt5_visible_adapter_not_verified")
        self.assertEqual(self.fixture.runner.actions, ["probe"])

    def test_compile_success_and_retry_recovers_without_second_compile(self) -> None:
        adapter = self.fixture.adapter()
        request = self.fixture.request("compile_validate")
        immutable_source_before = self.fixture.source.read_bytes()
        self.prime(adapter, request)
        first = adapter.compile_handler(request=request)
        self.prime(adapter, request)
        second = adapter.compile_handler(request=request)
        self.assertEqual(
            self.fixture.runner.actions,
            ["probe", "compile", "probe", "recover_compile"],
        )
        self.assertTrue(first["metrics"]["compileExecuted"])
        self.assertTrue(first["metrics"]["compileWorkingCopyVerified"])
        self.assertTrue(first["metrics"]["compiledBinaryPublishedFromWorkingCopy"])
        self.assertTrue(first["metrics"]["immutableSourcePreserved"])
        self.assertFalse(first["metrics"]["recoveredExistingReceipt"])
        self.assertFalse(second["metrics"]["compileExecuted"])
        self.assertTrue(second["metrics"]["recoveredExistingReceipt"])
        self.assertEqual(self.fixture.source.read_bytes(), immutable_source_before)
        operation_id = request["visibleOperation"]["operationId"]
        expected_working_source = (
            self.fixture.data
            / "MQL4"
            / "Experts"
            / "Metafxclub"
            / "AgentHQ"
            / operation_id
            / f"agenthq_{operation_id.removeprefix('ea-visible-')}.mq4"
        ).resolve()
        compile_payload = next(
            payload
            for payload in self.fixture.runner.payloads
            if payload["action"] == "compile"
        )
        recovery_payload = next(
            payload
            for payload in self.fixture.runner.payloads
            if payload["action"] == "recover_compile"
        )
        self.assertEqual(Path(compile_payload["sourcePath"]), expected_working_source)
        self.assertEqual(
            Path(compile_payload["binaryPath"]),
            expected_working_source.with_suffix(".ex4"),
        )
        self.assertEqual(recovery_payload["sourcePath"], compile_payload["sourcePath"])
        self.assertEqual(recovery_payload["binaryPath"], compile_payload["binaryPath"])
        self.assertNotEqual(Path(compile_payload["sourcePath"]), self.fixture.source)
        self.assertEqual(expected_working_source.read_bytes(), immutable_source_before)
        self.assertEqual(
            expected_working_source.with_suffix(".ex4").read_bytes(),
            self.fixture.source.with_suffix(".ex4").read_bytes(),
        )
        self.assertEqual(
            {item["alias"] for item in second["artifactSpecifications"]},
            {"compiled_binary", "visible_window", "compile_log", "adapter_receipt"},
        )
        log_path = self.fixture.workspace / next(
            item["relativePath"]
            for item in first["artifactSpecifications"]
            if item["alias"] == "compile_log"
        )
        text = log_path.read_text(encoding="utf-8")
        self.assertIn("sourceDigest:", text)
        self.assertIn("compiledBinarySha256:", text)
        self.assertIn("compileWorkingCopyRelativePathSha256:", text)
        self.assertIn("compiledBinaryPublishedFromWorkingCopy: true", text)
        self.assertIn("immutableSourcePreserved: true", text)
        self.assertIn("Result: 0 errors, 0 warnings", text)
        recovery_receipt = self.fixture.workspace / next(
            item["relativePath"]
            for item in second["artifactSpecifications"]
            if item["alias"] == "adapter_receipt"
        )
        payload = json.loads(recovery_receipt.read_text(encoding="utf-8"))
        self.assertEqual(
            payload["schemaVersion"],
            "ea-factory-visible-front-office-receipt-v1",
        )
        self.assertTrue(payload["compiledBinaryPublishedFromWorkingCopy"])
        self.assertTrue(payload["immutableSourcePreserved"])
        self.assertEqual(
            payload["compileWorkingBinarySha256"],
            sha256(self.fixture.source.with_suffix(".ex4")),
        )

    def test_compile_publication_digest_is_backtest_deployment_lineage(self) -> None:
        adapter = self.fixture.adapter()
        compile_request = self.fixture.request("compile_validate")
        self.prime(adapter, compile_request)
        compiled = adapter.compile_handler(request=compile_request)

        backtest_request = self.fixture.request("backtest_recheck")
        self.prime(adapter, backtest_request)
        backtested = adapter.backtest_handler(request=backtest_request)

        backtest_payload = next(
            payload
            for payload in self.fixture.runner.payloads
            if payload["action"] == "backtest"
        )
        self.assertEqual(
            backtest_payload["expectedDeployedExpertSha256"],
            compiled["metrics"]["compiledBinarySha256"],
        )
        self.assertEqual(
            backtested["metrics"]["compiledBinarySha256"],
            compiled["metrics"]["compiledBinarySha256"],
        )
        self.assertEqual(
            sha256(Path(backtest_payload["deployedExpertPath"])),
            compiled["metrics"]["compiledBinarySha256"],
        )

    def test_compile_result_is_rejected_without_fresh_binary_artifact(self) -> None:
        original_runner = self.fixture.runner

        def missing_binary_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "compile":
                Path(payload["binaryPath"]).unlink()
            return result

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=missing_binary_runner,
        )
        request = self.fixture.request("compile_validate")
        self.prime(adapter, request)

        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "compile_verifier_binary_missing",
        ):
            adapter.compile_handler(request=request)

    def test_compile_result_is_rejected_without_persisted_screenshot(self) -> None:
        original_runner = self.fixture.runner

        def missing_screenshot_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "compile":
                Path(payload["screenshotPath"]).unlink()
            return result

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=missing_screenshot_runner,
        )
        request = self.fixture.request("compile_validate")
        self.prime(adapter, request)

        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "evidence_file_unavailable",
        ):
            adapter.compile_handler(request=request)

    def test_compile_never_touches_deleted_immutable_source(self) -> None:
        original_runner = self.fixture.runner

        def deleting_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "compile":
                self.fixture.source.unlink()
            return result

        adapter = self.fixture.adapter()
        adapter._powershell_runner = deleting_runner
        request = self.fixture.request("compile_validate")
        self.prime(adapter, request)
        with self.assertRaises(self.module.VisibleTerminalAdapterError) as error:
            adapter.compile_handler(request=request)
        self.assertEqual(
            error.exception.code,
            "immutable_source_missing_during_visible_compile",
        )
        self.assertFalse(self.fixture.source.with_suffix(".ex4").exists())

    def test_working_source_hardlink_is_rejected(self) -> None:
        original_runner = self.fixture.runner

        def hardlink_source_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "compile":
                working_source = Path(payload["sourcePath"])
                working_source.unlink()
                os.link(self.fixture.source, working_source)
            return result

        adapter = self.fixture.adapter()
        adapter._powershell_runner = hardlink_source_runner
        request = self.fixture.request("compile_validate")
        self.prime(adapter, request)
        with self.assertRaises(self.module.VisibleTerminalAdapterError) as error:
            adapter.compile_handler(request=request)
        self.assertEqual(
            error.exception.code,
            "compile_working_source_hardlink_rejected",
        )
        self.assertFalse(self.fixture.source.with_suffix(".ex4").exists())

    def test_working_binary_hardlink_is_rejected(self) -> None:
        original_runner = self.fixture.runner

        def hardlink_binary_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "compile":
                working_binary = Path(payload["binaryPath"])
                os.link(working_binary, working_binary.with_suffix(".alias"))
            return result

        adapter = self.fixture.adapter()
        adapter._powershell_runner = hardlink_binary_runner
        request = self.fixture.request("compile_validate")
        self.prime(adapter, request)
        with self.assertRaises(self.module.VisibleTerminalAdapterError) as error:
            adapter.compile_handler(request=request)
        self.assertEqual(
            error.exception.code,
            "compile_working_binary_hardlink_rejected",
        )
        self.assertFalse(self.fixture.source.with_suffix(".ex4").exists())

    def test_compile_working_root_reparse_is_rejected_before_mutation(self) -> None:
        experts = self.fixture.data / "MQL4" / "Experts"
        outside = self.fixture.root / "outside-working-root"
        outside.mkdir()
        link = experts / "Metafxclub"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"directory symlink unavailable: {error}")
        adapter = self.fixture.adapter()
        request = self.fixture.request("compile_validate")
        self.prime(adapter, request)
        with self.assertRaises(self.module.VisibleTerminalAdapterError) as error:
            adapter.compile_handler(request=request)
        self.assertEqual(error.exception.code, "compile_working_copy_path_unsafe")
        self.assertEqual(list(outside.iterdir()), [])

    def test_published_binary_collision_is_not_overwritten(self) -> None:
        published = self.fixture.source.with_suffix(".ex4")
        published.write_bytes(b"existing-different-binary")
        adapter = self.fixture.adapter()
        request = self.fixture.request("compile_validate")
        self.prime(adapter, request)
        with self.assertRaises(self.module.VisibleTerminalAdapterError) as error:
            adapter.compile_handler(request=request)
        self.assertEqual(error.exception.code, "compiled_binary_publish_collision")
        self.assertEqual(published.read_bytes(), b"existing-different-binary")

    def test_long_visible_operation_keeps_pre_binding_but_requires_fresh_post_binding(self) -> None:
        adapter = self.fixture.adapter()
        request = self.fixture.request("compile_validate")
        self.fixture.runner.pre_observation_age_seconds = 65
        self.prime(adapter, request)
        result = adapter.compile_handler(request=request)
        self.assertTrue(result["metrics"]["compileVerified"])
        self.assertEqual(self.fixture.runner.actions, ["probe", "compile"])

    def test_terminal_title_chart_suffix_change_preserves_stable_process_binding(self) -> None:
        stable = "63441916: RoboForex-DemoPro - Demo Account - RoboForex Ltd"
        before_title = f"{stable} - [XAUUSD,M5]"
        after_title = f"{stable} - [GBPUSD,H1 (visual)]"
        before = self.fixture.runner.binding("backtest_recheck")
        after = self.fixture.runner.binding("backtest_recheck", post=True)
        before["terminalWindowTitle"] = before_title
        after["terminalWindowTitle"] = after_title
        target = {**self.fixture.target, **self.fixture.binding}

        process_binding, post_binding = self.module._binding_pair(
            {
                "processBinding": before,
                "postProcessBinding": after,
            },
            target=target,
            stage_id="backtest_recheck",
            maximum_operation_seconds=30,
        )

        expected_digest = self.module._terminal_window_title_identity_digest(before_title)
        self.assertEqual(
            self.module._terminal_window_title_identity(before_title),
            (stable, True),
        )
        self.assertEqual(
            self.module._terminal_window_title_identity(after_title),
            (stable, True),
        )
        self.assertEqual(process_binding["terminalWindowTitleSha256"], expected_digest)
        self.assertEqual(
            post_binding["terminalWindowTitleSha256"],
            expected_digest,
        )
        self.assertNotEqual(expected_digest, self.module._sha256_text(before_title))
        self.assertEqual(process_binding["terminalCandidateId"], "mtc-robo-mt4")
        self.assertEqual(process_binding["terminalSelectionRevision"], 7)
        self.assertEqual(process_binding["terminalBindingDigest"], "a" * 64)
        self.assertNotIn("terminalStableWindowTitleSha256", process_binding)

    def test_terminal_title_stable_prefix_drift_is_rejected(self) -> None:
        stable = "63441916: RoboForex-DemoPro - Demo Account - RoboForex Ltd"
        changed_prefixes = (
            "73441916: RoboForex-DemoPro - Demo Account - RoboForex Ltd",
            "63441916: RoboForex-Pro - Demo Account - RoboForex Ltd",
            "63441916: RoboForex-DemoPro - Live Account - RoboForex Ltd",
        )
        target = {**self.fixture.target, **self.fixture.binding}
        for changed in changed_prefixes:
            with self.subTest(changed=changed):
                before = self.fixture.runner.binding("backtest_recheck")
                after = self.fixture.runner.binding("backtest_recheck", post=True)
                before["terminalWindowTitle"] = f"{stable} - [XAUUSD,M5]"
                after["terminalWindowTitle"] = f"{changed} - [GBPUSD,H1 (visual)]"
                with self.assertRaises(self.module.VisibleTerminalAdapterError) as error:
                    self.module._binding_pair(
                        {
                            "processBinding": before,
                            "postProcessBinding": after,
                        },
                        target=target,
                        stage_id="backtest_recheck",
                        maximum_operation_seconds=30,
                    )
                self.assertEqual(error.exception.code, "process_binding_drift")

    def test_terminal_title_parser_rejects_ambiguous_or_unsafe_shapes(self) -> None:
        self.assertEqual(
            self.module._terminal_window_title_identity("DemoPro - EURUSD,H1"),
            ("DemoPro - EURUSD,H1", False),
        )
        invalid_titles = (
            None,
            "",
            " ",
            " Prefix",
            "Prefix ",
            "Prefix\n",
            "Prefix\u202e",
            "Prefix - []",
            "Prefix - [ ]",
            "Prefix - [XAUUSD,M5",
            "Prefix - XAUUSD,M5]",
            "Prefix - [XAUUSD,M5]]",
            "Prefix - [X[AU]USD,M5]",
            "Prefix - [one] - [two]",
            "Prefix - [XAU\nUSD,M5]",
            "Prefix - [XAU\u202eUSD,M5]",
            "A" * (self.module.MAX_TERMINAL_WINDOW_TITLE_CHARS + 1),
            "A" * (self.module.MAX_TERMINAL_STABLE_TITLE_CHARS + 1) + " - [X]",
            "Prefix - [" + "X" * (self.module.MAX_TERMINAL_CHART_SUFFIX_CHARS + 1) + "]",
        )
        for title in invalid_titles:
            with self.subTest(title=repr(title)[:80]):
                with self.assertRaises(self.module.VisibleTerminalAdapterError) as error:
                    self.module._terminal_window_title_identity(title)
                self.assertEqual(
                    error.exception.code,
                    "process_binding_terminal_title_invalid",
                )

    def test_terminal_title_one_sided_suffix_or_exact_title_drift_is_rejected(self) -> None:
        stable = "63441916: RoboForex-DemoPro - Demo Account - RoboForex Ltd"
        title_pairs = (
            (f"{stable} - [XAUUSD,M5]", stable),
            (stable, f"{stable} - [GBPUSD,H1 (visual)]"),
            ("DemoPro - EURUSD,H1", "DemoPro - GBPUSD,H1"),
        )
        target = {**self.fixture.target, **self.fixture.binding}
        for before_title, after_title in title_pairs:
            with self.subTest(before=before_title, after=after_title):
                before = self.fixture.runner.binding("backtest_recheck")
                after = self.fixture.runner.binding("backtest_recheck", post=True)
                before["terminalWindowTitle"] = before_title
                after["terminalWindowTitle"] = after_title
                with self.assertRaises(self.module.VisibleTerminalAdapterError) as error:
                    self.module._binding_pair(
                        {
                            "processBinding": before,
                            "postProcessBinding": after,
                        },
                        target=target,
                        stage_id="backtest_recheck",
                        maximum_operation_seconds=30,
                    )
                self.assertEqual(error.exception.code, "process_binding_drift")

    def test_process_binding_still_rejects_all_non_title_identity_drift(self) -> None:
        target = {**self.fixture.target, **self.fixture.binding}
        raw = self.fixture.runner.binding("backtest_recheck")
        base = self.module._fresh_raw_binding(
            raw,
            target=target,
            stage_id="backtest_recheck",
        )
        compared_fields = (
            "terminalProcessId",
            "frontOfficeProcessId",
            "terminalWindowHandle",
            "frontOfficeWindowHandle",
            "terminalExecutableSha256",
            "frontOfficeExecutableSha256",
            "terminalWindowClassSha256",
            "frontOfficeWindowTitleSha256",
            "frontOfficeWindowClassSha256",
            "frontOfficeKind",
        )
        for field in compared_fields:
            with self.subTest(field=field):
                post = copy.deepcopy(base)
                post[field] = (
                    int(post[field]) + 1
                    if isinstance(post[field], int)
                    else ("b" * 64 if str(post[field]) != "b" * 64 else "c" * 64)
                )
                with mock.patch.object(
                    self.module,
                    "_fresh_raw_binding",
                    side_effect=[copy.deepcopy(base), post],
                ):
                    with self.assertRaises(self.module.VisibleTerminalAdapterError) as error:
                        self.module._binding_pair(
                            {
                                "processBinding": {"autoTradingState": False},
                                "postProcessBinding": {"autoTradingState": False},
                            },
                            target=target,
                            stage_id="backtest_recheck",
                            maximum_operation_seconds=30,
                        )
                self.assertEqual(error.exception.code, "process_binding_drift")

        after = self.fixture.runner.binding("backtest_recheck", post=True)
        after["autoTradingState"] = True
        with self.assertRaises(self.module.VisibleTerminalAdapterError) as error:
            self.module._binding_pair(
                {
                    "processBinding": raw,
                    "postProcessBinding": after,
                },
                target=target,
                stage_id="backtest_recheck",
                maximum_operation_seconds=30,
            )
        self.assertEqual(error.exception.code, "process_binding_drift")

    def test_recreated_terminal_window_is_rejected_even_with_same_process(self) -> None:
        adapter = self.fixture.adapter()
        request = self.fixture.request("compile_validate")
        self.fixture.runner.drift_post_window = True
        self.prime(adapter, request)
        with self.assertRaises(self.module.VisibleTerminalAdapterError) as error:
            adapter.compile_handler(request=request)
        self.assertEqual(error.exception.code, "process_binding_drift")

    def test_incomplete_compile_intent_reconciles_without_second_compile(self) -> None:
        calls: list[str] = []

        def crashing_runner(payload: dict, *, response_path: Path, timeout_seconds: int):
            action = str(payload["action"])
            calls.append(action)
            if action == "probe":
                return self.fixture.runner(
                    payload,
                    response_path=response_path,
                    timeout_seconds=timeout_seconds,
                )
            if action == "recover_inflight_compile":
                return self.fixture.runner(
                    payload,
                    response_path=response_path,
                    timeout_seconds=timeout_seconds,
                )
            raise RuntimeError("simulated process loss after durable intent")

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=crashing_runner,
        )
        request = self.fixture.request("compile_validate")
        self.prime(adapter, request)
        with self.assertRaises(RuntimeError):
            adapter.compile_handler(request=request)
        with self.assertRaises(self.module.VisibleTerminalAdapterError) as retry:
            adapter.compile_handler(request=request)
        self.assertEqual(retry.exception.code, "visible_compile_binary_not_fresh")
        self.assertEqual(calls.count("compile"), 1)
        self.assertEqual(calls.count("recover_inflight_compile"), 1)

    def test_timeout_after_binary_recovers_without_second_compile(self) -> None:
        calls: list[str] = []
        first_compile = True

        def timeout_after_binary_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            nonlocal first_compile
            action = str(payload["action"])
            calls.append(action)
            if action == "compile" and first_compile:
                first_compile = False
                Path(payload["binaryPath"]).write_bytes(b"compiled-after-timeout")
                raise RuntimeError("simulated wrapper timeout after Compile")
            return self.fixture.runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=timeout_after_binary_runner,
        )
        request = self.fixture.request("compile_validate")
        immutable_before = self.fixture.source.read_bytes()
        self.prime(adapter, request)
        with self.assertRaisesRegex(RuntimeError, "wrapper timeout"):
            adapter.compile_handler(request=request)

        self.prime(adapter, request)
        recovered = adapter.compile_handler(request=request)

        self.assertEqual(calls.count("compile"), 1)
        self.assertEqual(calls.count("recover_inflight_compile"), 1)
        self.assertTrue(recovered["metrics"]["compileExecuted"])
        self.assertFalse(recovered["metrics"]["compileIssuedByCurrentAttempt"])
        self.assertTrue(recovered["metrics"]["recoveredInflightCompile"])
        self.assertEqual(self.fixture.source.read_bytes(), immutable_before)
        self.assertEqual(
            self.fixture.source.with_suffix(".ex4").read_bytes(),
            b"compiled-after-timeout",
        )

    def test_partial_timeout_artifact_is_not_published_or_recompiled(self) -> None:
        calls: list[str] = []

        def partial_artifact_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            action = str(payload["action"])
            calls.append(action)
            if action == "probe":
                return self.fixture.runner(
                    payload,
                    response_path=response_path,
                    timeout_seconds=timeout_seconds,
                )
            if action == "compile":
                Path(payload["binaryPath"]).write_bytes(b"partial")
                raise RuntimeError("simulated timeout with partial artifact")
            if action == "recover_inflight_compile":
                raise self.module.VisibleTerminalAdapterError(
                    "metaeditor_compile_result_unreadable"
                )
            raise AssertionError(action)

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=partial_artifact_runner,
        )
        request = self.fixture.request("compile_validate")
        self.prime(adapter, request)
        with self.assertRaisesRegex(RuntimeError, "partial artifact"):
            adapter.compile_handler(request=request)
        self.prime(adapter, request)
        with self.assertRaises(self.module.VisibleTerminalAdapterError) as error:
            adapter.compile_handler(request=request)
        self.assertEqual(error.exception.code, "metaeditor_compile_result_unreadable")
        self.assertEqual(calls.count("compile"), 1)
        self.assertEqual(calls.count("recover_inflight_compile"), 1)
        self.assertFalse(self.fixture.source.with_suffix(".ex4").exists())

    def test_recovery_screenshot_checkpoint_is_reused_after_crash(self) -> None:
        calls: list[dict] = []
        initial_failed = False
        recovery_failed = False

        def checkpoint_crash_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            nonlocal initial_failed, recovery_failed
            calls.append(copy.deepcopy(payload))
            action = str(payload["action"])
            if action == "compile" and not initial_failed:
                initial_failed = True
                Path(payload["binaryPath"]).write_bytes(b"compiled-checkpoint")
                raise RuntimeError("lost after compile")
            result = self.fixture.runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if action == "recover_inflight_compile" and not recovery_failed:
                recovery_failed = True
                raise RuntimeError("lost after recovery screenshot")
            return result

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=checkpoint_crash_runner,
        )
        request = self.fixture.request("compile_validate")
        self.prime(adapter, request)
        with self.assertRaisesRegex(RuntimeError, "after compile"):
            adapter.compile_handler(request=request)
        self.prime(adapter, request)
        with self.assertRaisesRegex(RuntimeError, "recovery screenshot"):
            adapter.compile_handler(request=request)
        self.prime(adapter, request)
        recovered = adapter.compile_handler(request=request)

        compile_calls = [item for item in calls if item["action"] == "compile"]
        recovery_calls = [
            item for item in calls if item["action"] == "recover_inflight_compile"
        ]
        self.assertEqual(len(compile_calls), 1)
        self.assertEqual(len(recovery_calls), 2)
        self.assertFalse(recovery_calls[0]["reuseExistingScreenshot"])
        self.assertTrue(recovery_calls[1]["reuseExistingScreenshot"])
        self.assertTrue(recovered["metrics"]["compileExecuted"])
        self.assertTrue(recovered["metrics"]["recoveredInflightCompile"])
        self.assertTrue(recovered["metrics"]["compileScreenshotReusedExactEvidence"])

    def test_compile_log_checkpoint_is_reused_after_receipt_crash(self) -> None:
        adapter = self.fixture.adapter()
        request = self.fixture.request("compile_validate")
        original_write = self.module._write_exclusive
        crashed = False

        def crash_before_receipt(path: Path, payload: bytes, code: str) -> None:
            nonlocal crashed
            if code == "visible_receipt_already_exists" and not crashed:
                crashed = True
                raise RuntimeError("lost before compile receipt")
            original_write(path, payload, code)

        self.prime(adapter, request)
        with mock.patch.object(
            self.module,
            "_write_exclusive",
            side_effect=crash_before_receipt,
        ):
            with self.assertRaisesRegex(RuntimeError, "compile receipt"):
                adapter.compile_handler(request=request)

        self.prime(adapter, request)
        recovered = adapter.compile_handler(request=request)

        self.assertEqual(self.fixture.runner.actions.count("compile"), 1)
        self.assertEqual(
            self.fixture.runner.actions.count("recover_inflight_compile"),
            1,
        )
        self.assertTrue(recovered["metrics"]["compileLogReusedExactBytes"])
        self.assertTrue(recovered["metrics"]["compileScreenshotReusedExactEvidence"])

    def test_backtest_pre_start_intent_retries_same_operation_safely(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        calls: list[str] = []
        failed_before_start = False

        def pre_start_crash_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            nonlocal failed_before_start
            action = str(payload["action"])
            calls.append(action)
            if action == "backtest" and not failed_before_start:
                failed_before_start = True
                # The durable intent has already been written, but no UI
                # evidence exists yet, so Start cannot have been invoked.
                raise RuntimeError("simulated loss before Strategy Tester Start")
            return self.fixture.runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=pre_start_crash_runner,
        )
        request = self.fixture.request("backtest_recheck")
        operation_id = request["visibleOperation"]["operationId"]
        intent_path = (
            self.fixture.workspace
            / "Summaries"
            / f"{operation_id}-backtest-intent.json"
        )
        settings_path = (
            self.fixture.workspace
            / "Screenshots"
            / f"{operation_id}-tester-settings.png"
        )
        result_path = (
            self.fixture.workspace
            / "Screenshots"
            / f"{operation_id}-tester-result.png"
        )
        report_path = (
            self.fixture.workspace
            / "Reports"
            / f"{operation_id}-tester.htm"
        )

        self.prime(adapter, request)
        with self.assertRaisesRegex(RuntimeError, "before Strategy Tester Start"):
            adapter.backtest_handler(request=request)
        self.assertTrue(intent_path.is_file())
        self.assertFalse(settings_path.exists())
        self.assertFalse(result_path.exists())
        self.assertFalse(report_path.exists())

        self.prime(adapter, request)
        result = adapter.backtest_handler(request=request)

        self.assertEqual(result["operationId"], operation_id)
        self.assertTrue(result["metrics"]["reusedPreStartIntent"])
        self.assertTrue(result["metrics"]["backtestExecuted"])
        self.assertEqual(calls, ["probe", "backtest", "probe", "backtest"])

    def test_legacy_html_report_blocks_a_new_or_recovery_backtest(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        adapter = self.fixture.adapter()
        request = self.fixture.request("backtest_recheck")
        operation_id = request["visibleOperation"]["operationId"]
        legacy_report = (
            self.fixture.workspace
            / "Reports"
            / f"{operation_id}-tester.html"
        )
        legacy_report.write_text("legacy partial report", encoding="utf-8")
        self.prime(adapter, request)

        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "visible_action_state_uncertain",
        ):
            adapter.backtest_handler(request=request)

    def test_backtest_retry_with_prestart_settings_replays_before_boundary(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        calls: list[str] = []
        failed_after_settings = False

        def settings_then_crash_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            nonlocal failed_after_settings
            action = str(payload["action"])
            calls.append(action)
            if action == "backtest" and not failed_after_settings:
                failed_after_settings = True
                # Settings evidence is pre-Start under the durable marker
                # protocol and can be recreated while the marker is absent.
                write_png(Path(payload["settingsScreenshotPath"]))
                raise RuntimeError("simulated loss at Strategy Tester Start boundary")
            return self.fixture.runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=settings_then_crash_runner,
        )
        request = self.fixture.request("backtest_recheck")
        operation_id = request["visibleOperation"]["operationId"]
        settings_path = (
            self.fixture.workspace
            / "Screenshots"
            / f"{operation_id}-tester-settings.png"
        )

        self.prime(adapter, request)
        with self.assertRaisesRegex(RuntimeError, "Start boundary"):
            adapter.backtest_handler(request=request)
        self.assertTrue(settings_path.is_file())

        self.prime(adapter, request)
        result = adapter.backtest_handler(request=request)

        self.assertTrue(result["metrics"]["backtestExecuted"])
        self.assertEqual(calls.count("backtest"), 2)

    def test_backtest_start_boundary_recovers_inflight_without_second_start(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        calls: list[str] = []

        def boundary_then_crash_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            action = str(payload["action"])
            calls.append(action)
            if action == "probe":
                return self.fixture.runner(
                    payload,
                    response_path=response_path,
                    timeout_seconds=timeout_seconds,
                )
            if action == "backtest":
                write_png(Path(payload["settingsScreenshotPath"]))
                boundary = Path(payload["startBoundaryPath"])
                boundary.write_text(payload["startBoundaryJson"], encoding="utf-8")
                raise RuntimeError("simulated process loss after durable boundary")
            if action == "recover_inflight_backtest":
                return self.fixture.runner(
                    payload,
                    response_path=response_path,
                    timeout_seconds=timeout_seconds,
                )
            raise AssertionError(action)

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=boundary_then_crash_runner,
        )
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)
        with self.assertRaisesRegex(RuntimeError, "durable boundary"):
            adapter.backtest_handler(request=request)

        self.prime(adapter, request)
        recovered = adapter.backtest_handler(request=request)

        self.assertTrue(recovered["metrics"]["recoveredInflightBacktest"])
        self.assertFalse(recovered["metrics"]["recoveryIssuedStart"])
        self.assertEqual(recovered["metrics"]["tradeCount"], 3)
        self.assertEqual(calls.count("backtest"), 1)
        self.assertEqual(calls.count("recover_inflight_backtest"), 1)

    def test_completed_result_checkpoint_collects_report_without_second_start(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        calls: list[str] = []

        def result_then_crash_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            action = str(payload["action"])
            calls.append(action)
            if action == "probe":
                return self.fixture.runner(
                    payload,
                    response_path=response_path,
                    timeout_seconds=timeout_seconds,
                )
            if action == "backtest":
                write_png(Path(payload["settingsScreenshotPath"]))
                boundary = Path(payload["startBoundaryPath"])
                boundary.write_text(payload["startBoundaryJson"], encoding="utf-8")
                write_png(Path(payload["resultScreenshotPath"]))
                raise RuntimeError("simulated report collection failure")
            if action == "recover_completed_backtest":
                return self.fixture.runner(
                    payload,
                    response_path=response_path,
                    timeout_seconds=timeout_seconds,
                )
            raise AssertionError(action)

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=result_then_crash_runner,
        )
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)
        with self.assertRaisesRegex(RuntimeError, "report collection failure"):
            adapter.backtest_handler(request=request)

        result_checkpoint = (
            self.fixture.workspace
            / "Screenshots"
            / "ea-visible-222222222222222222222222-tester-result.png"
        )
        checkpoint_digest = sha256(result_checkpoint)
        checkpoint_mtime = result_checkpoint.stat().st_mtime_ns

        self.prime(adapter, request)
        recovered = adapter.backtest_handler(request=request)

        self.assertFalse(recovered["metrics"]["recoveredInflightBacktest"])
        self.assertTrue(recovered["metrics"]["recoveredCompletedBacktest"])
        self.assertFalse(recovered["metrics"]["recoveryIssuedStart"])
        self.assertEqual(recovered["metrics"]["tradeCount"], 3)
        self.assertEqual(calls.count("backtest"), 1)
        self.assertEqual(calls.count("recover_completed_backtest"), 1)
        self.assertEqual(calls.count("recover_inflight_backtest"), 0)
        self.assertEqual(sha256(result_checkpoint), checkpoint_digest)
        self.assertEqual(result_checkpoint.stat().st_mtime_ns, checkpoint_mtime)

    def test_backtest_retry_rejects_changed_policy_bound_to_same_operation(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        failed = False

        def pre_start_crash_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            nonlocal failed
            if payload["action"] == "backtest" and not failed:
                failed = True
                raise RuntimeError("pre-start")
            return self.fixture.runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=pre_start_crash_runner,
        )
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)
        with self.assertRaisesRegex(RuntimeError, "pre-start"):
            adapter.backtest_handler(request=request)

        changed = copy.deepcopy(request)
        changed["testerSettings"]["period"] = "D1"
        self.prime(adapter, changed)
        with self.assertRaises(self.module.VisibleTerminalAdapterError) as retry:
            adapter.backtest_handler(request=changed)
        self.assertEqual(retry.exception.code, "backtest_action_request_mismatch")

    def test_inflight_recovery_fails_closed_when_running_state_is_unproven(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        calls: list[str] = []

        def runner(payload: dict, *, response_path: Path, timeout_seconds: int) -> dict:
            action = str(payload["action"])
            calls.append(action)
            if action == "probe":
                return self.fixture.runner(
                    payload,
                    response_path=response_path,
                    timeout_seconds=timeout_seconds,
                )
            if action == "backtest":
                write_png(Path(payload["settingsScreenshotPath"]))
                boundary = Path(payload["startBoundaryPath"])
                boundary.write_text(payload["startBoundaryJson"], encoding="utf-8")
                raise RuntimeError("lost after boundary")
            if action == "recover_inflight_backtest":
                raise self.module.VisibleTerminalAdapterError(
                    "tester_recovery_execution_unproven"
                )
            raise AssertionError(action)

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=runner,
        )
        request = self.fixture.request("backtest_recheck")
        operation_id = request["visibleOperation"]["operationId"]
        self.prime(adapter, request)
        with self.assertRaisesRegex(RuntimeError, "lost after boundary"):
            adapter.backtest_handler(request=request)
        self.prime(adapter, request)
        with self.assertRaises(self.module.VisibleTerminalAdapterError) as error:
            adapter.backtest_handler(request=request)
        self.assertEqual(error.exception.code, "tester_recovery_execution_unproven")
        self.assertEqual(calls.count("backtest"), 1)
        self.assertEqual(calls.count("recover_inflight_backtest"), 1)
        self.assertFalse(
            (
                self.fixture.workspace
                / "Summaries"
                / f"{operation_id}-backtest-receipt.json"
            ).exists()
        )

    def test_backtest_success_and_retry_recovers_without_second_start(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        adapter = self.fixture.adapter()
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)
        first = adapter.backtest_handler(request=request)
        self.prime(adapter, request)
        second = adapter.backtest_handler(request=request)
        self.assertEqual(
            self.fixture.runner.actions,
            ["probe", "backtest", "probe", "recover_backtest"],
        )
        self.assertEqual(first["metrics"]["tradeCount"], 3)
        self.assertEqual(first["metrics"]["buyTradeCount"], 2)
        self.assertEqual(first["metrics"]["sellTradeCount"], 1)
        self.assertEqual(first["metrics"]["resolvedTesterSettings"]["deposit"], 10000.0)
        self.assertEqual(first["metrics"]["resolvedTesterSettings"]["spread"], 20)
        self.assertTrue(second["metrics"]["recoveredExistingReceipt"])
        self.assertFalse(second["metrics"]["backtestExecuted"])
        self.assertRegex(second["metrics"]["expertUiPathDigest"], r"^[0-9a-f]{64}$")

    def test_can_slim_tester_preset_is_source_bound_visible_and_read_back(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        adapter = self.fixture.adapter()
        request = self.fixture.enable_can_slim_tester_preset(
            self.fixture.request("backtest_recheck")
        )
        self.prime(adapter, request)

        result = adapter.backtest_handler(request=request)

        metrics = result["metrics"]
        self.assertTrue(metrics["testerInputPresetApplied"])
        self.assertTrue(metrics["testerInputPresetReadbackVerified"])
        self.assertTrue(metrics["testerInputPresetReportVerified"])
        self.assertTrue(metrics["simulationAssumptionsExplicit"])
        self.assertTrue(
            metrics["resolvedTesterInputPreset"]["appliedOnlyToStrategyTester"]
        )
        self.assertTrue(metrics["resolvedTesterInputPreset"]["notAppliedToLiveChart"])
        self.assertEqual(
            [row["inputName"] for row in metrics["resolvedTesterInputPreset"]["readback"]],
            [name for name, _kind in self.module.CAN_SLIM_CERTIFIED_INPUT_LAYOUT],
        )
        readback = {
            row["inputName"]: row
            for row in metrics["resolvedTesterInputPreset"]["readback"]
        }
        self.assertEqual(len(readback), 13)
        self.assertEqual(readback["MaxSpreadPoints"]["sourceDefault"], 30)
        self.assertEqual(readback["MaxSpreadPoints"]["observedValue"], 30)
        self.assertEqual(readback["RiskPercent"]["sourceDefault"], 1.0)
        self.assertEqual(readback["RiskPercent"]["observedValue"], 1.0)
        self.assertTrue(
            all(
                readback[name]["sourceDefault"] is False
                and readback[name]["testerValue"] is True
                and readback[name]["observedValue"] is True
                for name in self.module.CAN_SLIM_SIMULATION_INPUT_NAMES
            )
        )
        self.assertEqual(
            {item["alias"] for item in result["artifactSpecifications"]},
            {
                "tester_settings",
                "tester_input_preset",
                "tester_input_preset_set",
                "tester_input_readback_set",
                "tester_result",
                "tester_report_proof",
                "tester_report",
                "adapter_receipt",
            },
        )
        self.assertIn(
            "input bool FundamentalCriteriaConfirmed = false;",
            self.fixture.source.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "input bool ExternalBenchmarkUptrendConfirmed = false;",
            self.fixture.source.read_text(encoding="utf-8"),
        )
        self.prime(adapter, request)
        recovered = adapter.backtest_handler(request=request)
        self.assertTrue(recovered["metrics"]["recoveredExistingReceipt"])
        self.assertTrue(recovered["metrics"]["testerInputPresetReadbackVerified"])
        self.assertEqual(
            self.fixture.runner.actions,
            ["probe", "backtest", "probe", "recover_backtest"],
        )

    def test_generic_mt4_inputs_are_fully_reset_and_only_guarded_external_gate_is_simulated(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        adapter = self.fixture.adapter()
        request = self.fixture.enable_generic_tester_preset(
            self.fixture.request("backtest_recheck"),
            """#property strict
input int FastPeriod = 10;
input int SlowPeriod = 60;
input double FixedLot = 0.01;
input bool TradeOnNewBar = true;
input bool EligibilityConfirmed = false;
input bool EnableTrading = false;
input bool ExternalLiveTradingEnabled = false;
void OnTick(){
  if(!EligibilityConfirmed) return;
  if(!ExternalLiveTradingEnabled) return;
}
""",
        )
        self.prime(adapter, request)

        result = adapter.backtest_handler(request=request)

        preset = request["testerSettings"]["testerInputPreset"]
        self.assertEqual(preset["simulationInputNames"], ["EligibilityConfirmed"])
        self.assertEqual(len(preset["assumptions"]), 7)
        by_name = {item["inputName"]: item for item in preset["assumptions"]}
        self.assertEqual(by_name["FastPeriod"]["testerValue"], 10)
        self.assertEqual(by_name["FixedLot"]["testerValue"], 0.01)
        self.assertTrue(by_name["TradeOnNewBar"]["testerValue"])
        self.assertTrue(by_name["EligibilityConfirmed"]["testerValue"])
        self.assertFalse(by_name["EnableTrading"]["testerValue"])
        self.assertFalse(by_name["ExternalLiveTradingEnabled"]["testerValue"])
        self.assertTrue(result["metrics"]["testerInputPresetReportVerified"])
        self.assertEqual(
            len(result["metrics"]["resolvedTesterInputPreset"]["readback"]),
            7,
        )

    def test_generic_mt4_input_contract_rejects_unsupported_or_ambiguous_declarations_before_ui(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        adapter = self.fixture.adapter()
        invalid_sources = (
            'input string Label = "unsafe";\nvoid OnTick(){}\n',
            "input int Period = 10 + 2;\nvoid OnTick(){}\n",
            "input int A = 1; input int B = 2;\nvoid OnTick(){}\n",
            "input int Same = 1;\ninput int same = 2;\nvoid OnTick(){}\n",
            "input int\nPeriod = 14;\nvoid OnTick(){}\n",
        )
        for source_text in invalid_sources:
            with self.subTest(source_text=source_text):
                self.fixture.source.write_text(source_text, encoding="utf-8")
                request = self.fixture.request("backtest_recheck")
                request["versions"][0]["sourceDigest"] = sha256(self.fixture.source)
                self.prime(adapter, request)
                before = list(self.fixture.runner.actions)
                with self.assertRaisesRegex(
                    self.module.VisibleTerminalAdapterError,
                    "tester_input_source_contract_unsupported",
                ):
                    adapter.backtest_handler(request=request)
                self.assertNotIn("backtest", self.fixture.runner.actions[len(before) :])

    def test_external_name_without_executable_guard_is_reset_false_not_simulated(self) -> None:
        source = (
            "input bool ExternalApproval = false;\n"
            "/* if(!ExternalApproval) return; */\n"
            "void OnTick(){}\n"
        )
        snapshot = self.module._mt4_source_input_snapshot(source)
        self.assertEqual(len(snapshot), 1)
        self.assertFalse(snapshot[0]["sourceDefault"])
        self.assertFalse(snapshot[0]["testerValue"])
        self.assertEqual(self.module._tester_simulation_input_names(snapshot), [])

    def test_can_slim_source_requires_exact_digest_bound_tester_preset(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        adapter = self.fixture.adapter()
        missing = self.fixture.request("backtest_recheck")
        missing = self.fixture.enable_can_slim_tester_preset(missing)
        missing["testerSettings"].pop("testerInputPreset")
        self.prime(adapter, missing)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "tester_input_preset_required",
        ):
            adapter.backtest_handler(request=missing)

        invalid = self.fixture.enable_can_slim_tester_preset(
            self.fixture.request("backtest_recheck")
        )
        invalid["testerSettings"]["testerInputPreset"]["presetDigest"] = "0" * 64
        self.prime(adapter, invalid)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "tester_input_preset_invalid",
        ):
            adapter.backtest_handler(request=invalid)

        missing_guard = self.fixture.enable_can_slim_tester_preset(
            self.fixture.request("backtest_recheck")
        )
        guarded_source = self.fixture.source.read_text(encoding="utf-8")
        self.fixture.source.write_text(
            guarded_source.replace(
                "  if(!ExternalBenchmarkUptrendConfirmed) return;\n",
                "",
            ),
            encoding="utf-8",
        )
        missing_guard["versions"][0]["sourceDigest"] = sha256(self.fixture.source)
        self.prime(adapter, missing_guard)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "tester_input_preset_(?:invalid|source_profile_mismatch)",
        ):
            adapter.backtest_handler(request=missing_guard)

        comment_spoof = self.fixture.enable_can_slim_tester_preset(
            self.fixture.request("backtest_recheck")
        )
        source_with_comment_guard = self.fixture.source.read_text(encoding="utf-8")
        self.fixture.source.write_text(
            source_with_comment_guard.replace(
                "  if(!ExternalBenchmarkUptrendConfirmed) return;\n",
                "  // if(!ExternalBenchmarkUptrendConfirmed) return;\n",
            ),
            encoding="utf-8",
        )
        comment_spoof["versions"][0]["sourceDigest"] = sha256(self.fixture.source)
        self.prime(adapter, comment_spoof)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "tester_input_preset_(?:invalid|source_profile_mismatch)",
        ):
            adapter.backtest_handler(request=comment_spoof)

    def test_can_slim_tester_preset_rejects_false_saved_readback(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def false_readback_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                Path(payload["inputReadbackSetPath"]).write_text(
                    "FundamentalCriteriaConfirmed=true\n"
                    "ExternalBenchmarkUptrendConfirmed=false\n",
                    encoding="utf-8",
                )
            return result

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=false_readback_runner,
        )
        request = self.fixture.enable_can_slim_tester_preset(
            self.fixture.request("backtest_recheck")
        )
        self.prime(adapter, request)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "tester_input_(?:preset_readback_mismatch|readback_unexpected_input)",
        ):
            adapter.backtest_handler(request=request)

    def test_can_slim_tester_preset_rejects_stale_numeric_saved_readback(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def stale_numeric_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                readback = Path(payload["inputReadbackSetPath"])
                text = readback.read_text(encoding="utf-8-sig")
                readback.write_text(
                    text.replace("MaxSpreadPoints=30", "MaxSpreadPoints=300", 1),
                    encoding="utf-8",
                )
            return result

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=stale_numeric_runner,
        )
        request = self.fixture.enable_can_slim_tester_preset(
            self.fixture.request("backtest_recheck")
        )
        self.prime(adapter, request)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "tester_input_preset_readback_mismatch",
        ):
            adapter.backtest_handler(request=request)

    def test_backtest_rejects_input_preset_mutated_after_visible_runner(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def mutate_preset_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                Path(payload["inputPresetSetPath"]).write_bytes(b"tampered=true\r\n")
            return result

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=mutate_preset_runner,
        )
        request = self.fixture.enable_can_slim_tester_preset(
            self.fixture.request("backtest_recheck")
        )
        self.prime(adapter, request)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "tester_input_preset_set_mismatch",
        ):
            adapter.backtest_handler(request=request)

    def test_can_slim_tester_preset_rejects_unapproved_set_metadata_suffix(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def unknown_metadata_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                readback = Path(payload["inputReadbackSetPath"])
                text = readback.read_text(encoding="utf-8-sig")
                readback.write_text(
                    text + "MaxSpreadPoints,X=30\n",
                    encoding="utf-8",
                )
            return result

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=unknown_metadata_runner,
        )
        request = self.fixture.enable_can_slim_tester_preset(
            self.fixture.request("backtest_recheck")
        )
        self.prime(adapter, request)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "tester_input_readback_unexpected_input",
        ):
            adapter.backtest_handler(request=request)

    def test_can_slim_tester_report_must_echo_all_preset_parameters(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def stale_report_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                stale = copy.deepcopy(payload["testerSettings"]["testerInputPreset"])
                next(
                    item
                    for item in stale["assumptions"]
                    if item["inputName"] == "MaxSpreadPoints"
                )["testerValue"] = 300
                Path(payload["testerReportPath"]).write_bytes(
                    tester_report(preset=stale)
                )
            return result

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=stale_report_runner,
        )
        request = self.fixture.enable_can_slim_tester_preset(
            self.fixture.request("backtest_recheck")
        )
        self.prime(adapter, request)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "tester_report_parameter_mismatch",
        ):
            adapter.backtest_handler(request=request)

    def test_tester_report_accepts_current_spread_with_parenthesized_value(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        self.fixture.runner.resolved_spread = "Current"
        self.fixture.runner.report_spread = "Current (12)"
        adapter = self.fixture.adapter()
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)

        result = adapter.backtest_handler(request=request)

        self.assertEqual(result["metrics"]["resolvedTesterSettings"]["spread"], 12)

    def test_tester_report_requires_one_exact_expert_metadata_row(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def wrong_expert_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                path = Path(payload["testerReportPath"])
                report = path.read_text(encoding="utf-8")
                report = report.replace(
                    "<tr><td>Expert</td><td>Strategy_v01</td></tr>",
                    "<tr><td>Expert</td><td>Other_EA</td></tr>"
                    "<tr><td>Comment</td><td>Strategy_v01</td></tr>",
                )
                path.write_text(report, encoding="utf-8")
            return result

        adapter = self.fixture.adapter(backtest_verifier=self.module.verify_mt4_tester_report)
        adapter._powershell_runner = wrong_expert_runner
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "tester_report_settings_mismatch",
        ):
            adapter.backtest_handler(request=request)

    def test_standard_mt4_report_title_can_identify_expert_without_metadata_row(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def standard_mt4_report_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                path = Path(payload["testerReportPath"])
                report = path.read_text(encoding="utf-8")
                report = report.replace(
                    "<!doctype html><html><body>",
                    "<!doctype html><html><head>"
                    "<title>Strategy Tester: Strategy_v01</title>"
                    "</head><body>",
                ).replace(
                    "<tr><td>Expert</td><td>Strategy_v01</td></tr>\n",
                    "",
                )
                path.write_text(report, encoding="utf-8")
            return result

        adapter = self.fixture.adapter(
            backtest_verifier=self.module.verify_mt4_tester_report
        )
        adapter._powershell_runner = standard_mt4_report_runner
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)

        result = adapter.backtest_handler(request=request)

        self.assertTrue(result["metrics"]["backtestVerified"])
        self.assertEqual(result["metrics"]["tradeCount"], 3)

    def test_expert_title_fallback_requires_one_exact_strategy_tester_title(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def ambiguous_title_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                path = Path(payload["testerReportPath"])
                report = path.read_text(encoding="utf-8")
                report = report.replace(
                    "<!doctype html><html><body>",
                    "<!doctype html><html><head>"
                    "<title>Strategy Tester: Strategy_v01</title>"
                    "<title>Strategy Tester: Strategy_v01</title>"
                    "</head><body>",
                ).replace(
                    "<tr><td>Expert</td><td>Strategy_v01</td></tr>\n",
                    "",
                )
                path.write_text(report, encoding="utf-8")
            return result

        adapter = self.fixture.adapter(
            backtest_verifier=self.module.verify_mt4_tester_report
        )
        adapter._powershell_runner = ambiguous_title_runner
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "tester_report_settings_mismatch",
        ):
            adapter.backtest_handler(request=request)

    def test_tester_report_rejects_duplicate_expert_metadata_rows(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def duplicate_expert_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                path = Path(payload["testerReportPath"])
                report = path.read_text(encoding="utf-8")
                report = report.replace(
                    "<tr><td>Expert</td><td>Strategy_v01</td></tr>",
                    "<tr><td>Expert</td><td>Strategy_v01</td></tr>"
                    "<tr><td>Expert Advisor</td><td>Strategy_v01</td></tr>",
                )
                path.write_text(report, encoding="utf-8")
            return result

        adapter = self.fixture.adapter(backtest_verifier=self.module.verify_mt4_tester_report)
        adapter._powershell_runner = duplicate_expert_runner
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "tester_report_settings_mismatch",
        ):
            adapter.backtest_handler(request=request)

    def test_tester_report_requires_exact_symbol_period_and_model_rows(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def decoy_metadata_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                path = Path(payload["testerReportPath"])
                report = path.read_text(encoding="utf-8")
                report = report.replace(
                    "<tr><td>Symbol</td><td>EURUSD</td></tr>",
                    "<tr><td>Symbol</td><td>GBPUSD</td></tr>",
                ).replace(
                    "<tr><td>Period</td><td>H1</td></tr>",
                    "<tr><td>Period</td><td>M15</td></tr>",
                ).replace(
                    "<tr><td>Model</td><td>Every tick</td></tr>",
                    "<tr><td>Model</td><td>Open prices only</td></tr>"
                    "<tr><td>Comment</td><td>EURUSD H1 Every tick</td></tr>",
                )
                path.write_text(report, encoding="utf-8")
            return result

        adapter = self.fixture.adapter()
        adapter._powershell_runner = decoy_metadata_runner
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "tester_report_settings_mismatch",
        ):
            adapter.backtest_handler(request=request)

    def test_tester_report_rejects_duplicate_symbol_metadata_rows(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def duplicate_symbol_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                path = Path(payload["testerReportPath"])
                report = path.read_text(encoding="utf-8").replace(
                    "<tr><td>Symbol</td><td>EURUSD</td></tr>",
                    "<tr><td>Symbol</td><td>EURUSD</td></tr>"
                    "<tr><td>Symbol</td><td>EURUSD</td></tr>",
                )
                path.write_text(report, encoding="utf-8")
            return result

        adapter = self.fixture.adapter()
        adapter._powershell_runner = duplicate_symbol_runner
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "tester_report_settings_mismatch",
        ):
            adapter.backtest_handler(request=request)

    def test_fast_backtest_completion_uses_full_evidence_and_exact_binding(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        self.fixture.runner.tester_completion_observation = (
            "fast_idle_evidence_required"
        )
        adapter = self.fixture.adapter()
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)

        result = adapter.backtest_handler(request=request)

        self.assertTrue(result["metrics"]["backtestVerified"])
        self.assertTrue(result["metrics"]["fastCompletionFallbackUsed"])
        self.assertEqual(
            result["metrics"]["testerCompletionObservation"],
            "fast_idle_evidence_required",
        )
        self.assertEqual(result["metrics"]["tradeCount"], 3)
        self.assertEqual(
            result["metrics"]["processBinding"]["terminalWindowHandle"],
            result["metrics"]["postProcessBinding"]["terminalWindowHandle"],
        )

    def test_fast_backtest_completion_rejects_missing_tester_report(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        self.fixture.runner.tester_completion_observation = (
            "fast_idle_evidence_required"
        )
        original_runner = self.fixture.runner

        def missing_report_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                Path(payload["testerReportPath"]).unlink()
            return result

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=missing_report_runner,
        )
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)

        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "evidence_file_unavailable",
        ):
            adapter.backtest_handler(request=request)

    def test_fast_backtest_completion_rejects_missing_result_screenshot(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        self.fixture.runner.tester_completion_observation = (
            "fast_idle_evidence_required"
        )
        original_runner = self.fixture.runner

        def missing_result_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                Path(payload["resultScreenshotPath"]).unlink()
            return result

        adapter = self.module.create_visible_front_office_adapter(
            target_resolver=lambda **_kwargs: copy.deepcopy(self.fixture.target),
            compile_verifier=self.module.verify_visible_metaeditor_compile,
            backtest_verifier=self.module.verify_mt4_tester_report,
            powershell_runner=missing_result_runner,
        )
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)

        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "evidence_file_unavailable",
        ):
            adapter.backtest_handler(request=request)

    def test_fast_backtest_completion_rejects_exact_binding_drift(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        self.fixture.runner.tester_completion_observation = (
            "fast_idle_evidence_required"
        )
        self.fixture.runner.drift_post_window = True
        adapter = self.fixture.adapter()
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)

        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "process_binding_drift",
        ):
            adapter.backtest_handler(request=request)

    def test_fast_backtest_completion_rejects_missing_log_advance(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        self.fixture.runner.tester_completion_observation = (
            "fast_idle_evidence_required"
        )
        self.fixture.runner.fast_completion_log_advanced_override = False
        adapter = self.fixture.adapter()
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)

        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "visible_backtest_result_invalid",
        ):
            adapter.backtest_handler(request=request)

    def test_backtest_rejects_unrecognized_completion_observation(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        self.fixture.runner.tester_completion_observation = "idle_only"
        adapter = self.fixture.adapter()
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)

        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "visible_backtest_result_invalid",
        ):
            adapter.backtest_handler(request=request)

    def test_backtest_rejects_basename_only_expert_readback(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def basename_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                result["selectedExpertReadback"] = payload["expertFileName"]
            return result

        adapter = self.fixture.adapter()
        adapter._powershell_runner = basename_runner
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "visible_backtest_result_invalid",
        ):
            adapter.backtest_handler(request=request)

    def test_backtest_rejects_deployed_expert_digest_claim_mismatch(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def digest_claim_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                result["deployedExpertSha256"] = "0" * 64
            return result

        adapter = self.fixture.adapter()
        adapter._powershell_runner = digest_claim_runner
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "visible_backtest_result_invalid",
        ):
            adapter.backtest_handler(request=request)

    def test_zero_trade_report_is_verified_as_completed_with_attention(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def zero_trade_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                Path(payload["testerReportPath"]).write_bytes(
                    tester_report(trade_sides=())
                )
            return result

        adapter = self.fixture.adapter()
        adapter._powershell_runner = zero_trade_runner
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)
        first = adapter.backtest_handler(request=request)
        self.assertTrue(first["metrics"]["backtestVerified"])
        self.assertTrue(first["metrics"]["backtestExecuted"])
        self.assertTrue(first["metrics"]["testerTradeRowsVerified"])
        self.assertTrue(first["metrics"]["zeroTrade"])
        self.assertTrue(first["metrics"]["attentionRequired"])
        self.assertFalse(first["metrics"]["performanceEvaluationAvailable"])
        self.assertEqual(
            first["metrics"]["attentionReasonCode"],
            "backtest_zero_trades",
        )
        self.assertEqual(first["metrics"]["executionOutcome"], "completed_zero_trades")

        self.prime(adapter, request)
        recovered = adapter.backtest_handler(request=request)
        self.assertTrue(recovered["metrics"]["recoveredExistingReceipt"])
        self.assertFalse(recovered["metrics"]["backtestExecuted"])
        self.assertTrue(recovered["metrics"]["zeroTrade"])
        self.assertTrue(recovered["metrics"]["attentionRequired"])
        self.assertFalse(recovered["metrics"]["performanceEvaluationAvailable"])
        self.assertEqual(
            self.fixture.runner.actions,
            ["probe", "backtest", "probe", "recover_backtest"],
        )

    def test_mismatched_chart_errors_complete_with_attention_not_failure(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def history_warning_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                Path(payload["testerReportPath"]).write_bytes(
                    tester_report(mismatched_chart_errors=1357)
                )
            return result

        adapter = self.fixture.adapter()
        adapter._powershell_runner = history_warning_runner
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)
        result = adapter.backtest_handler(request=request)

        metrics = result["metrics"]
        self.assertEqual(metrics["tradeCount"], 3)
        self.assertEqual(metrics["mismatchedChartErrors"], 1357)
        self.assertTrue(metrics["historyQualityIssue"])
        self.assertFalse(metrics["historyQualityVerified"])
        self.assertTrue(metrics["attentionRequired"])
        self.assertFalse(metrics["performanceEvaluationAvailable"])
        self.assertEqual(
            metrics["attentionReasonCode"],
            "backtest_history_quality_errors",
        )
        self.assertEqual(
            metrics["executionOutcome"],
            "completed_with_trades_history_quality_errors",
        )

    def test_zero_trade_and_history_errors_have_one_deterministic_reason(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def combined_attention_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                Path(payload["testerReportPath"]).write_bytes(
                    tester_report(trade_sides=(), mismatched_chart_errors=1357)
                )
            return result

        adapter = self.fixture.adapter()
        adapter._powershell_runner = combined_attention_runner
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)
        result = adapter.backtest_handler(request=request)

        metrics = result["metrics"]
        self.assertTrue(metrics["zeroTrade"])
        self.assertTrue(metrics["historyQualityIssue"])
        self.assertEqual(
            metrics["attentionReasonCode"],
            "backtest_zero_trades_and_history_quality_errors",
        )
        self.assertEqual(
            metrics["executionOutcome"],
            "completed_zero_trades_with_history_quality_errors",
        )
        self.assertFalse(metrics["performanceEvaluationAvailable"])

    def test_mismatched_chart_error_metadata_must_be_unique_and_numeric(self) -> None:
        for mutation in ("missing", "malformed", "duplicate"):
            with self.subTest(mutation=mutation):
                parser = self.module._TesterTableParser()
                report = tester_report().decode("utf-8")
                row = "<tr><td>Mismatched chart errors</td><td>0</td></tr>"
                if mutation == "missing":
                    report = report.replace(row, "")
                elif mutation == "malformed":
                    report = report.replace(row, row.replace(">0<", ">unknown<"))
                else:
                    report = report.replace(row, row + row)
                parser.feed(report)
                with self.assertRaisesRegex(
                    self.module.VisibleTerminalAdapterError,
                    "tester_mismatched_chart_errors_unverified",
                ):
                    self.module._report_mismatched_chart_errors(parser.rows)

    def test_zero_trade_report_rejects_a_stray_trade_row(self) -> None:
        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        original_runner = self.fixture.runner

        def inconsistent_runner(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = original_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                report = tester_report(trade_sides=()).replace(
                    b"</table>",
                    b"<tr><td>1</td><td>2026.01.01</td><td>buy</td></tr></table>",
                )
                Path(payload["testerReportPath"]).write_bytes(report)
            return result

        adapter = self.fixture.adapter()
        adapter._powershell_runner = inconsistent_runner
        request = self.fixture.request("backtest_recheck")
        self.prime(adapter, request)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "tester_trade_rows_unverified",
        ):
            adapter.backtest_handler(request=request)

    def test_process_pid_drift_fails_closed(self) -> None:
        self.fixture.runner.drift_post_pid = True
        adapter = self.fixture.adapter()
        request = self.fixture.request("compile_validate")
        self.prime(adapter, request)
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "process_binding_owner_mismatch|process_binding_drift",
        ):
            adapter.compile_handler(request=request)

    def test_traversal_and_deployment_collision_fail_before_start(self) -> None:
        adapter = self.fixture.adapter()
        request = self.fixture.request("compile_validate")
        self.prime(adapter, request)
        request["versions"][0]["versionFile"] = "../Strategy_v01.mq4"
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "source_path_invalid",
        ):
            adapter.compile_handler(request=request)

        self.fixture.source.with_suffix(".ex4").write_bytes(b"compiled-ex4-v1")
        backtest = self.fixture.request("backtest_recheck")
        self.prime(adapter, backtest)
        operation = backtest["visibleOperation"]["operationId"]
        collision = (
            self.fixture.data
            / "MQL4"
            / "Experts"
            / "Metafxclub"
            / "AgentHQ"
            / operation
            / "Strategy_v01.ex4"
        )
        collision.parent.mkdir(parents=True)
        collision.write_bytes(b"different-binary")
        with self.assertRaisesRegex(
            self.module.VisibleTerminalAdapterError,
            "expert_deployment_collision",
        ):
            adapter.backtest_handler(request=backtest)
        self.assertNotIn("backtest", self.fixture.runner.actions)

    def test_missing_powershell_script_has_stable_fail_closed_code(self) -> None:
        with mock.patch.object(self.module, "__file__", str(Path(self.temporary.name) / "missing.py")):
            with self.assertRaisesRegex(
                self.module.VisibleTerminalAdapterError,
                "visible_ui_script_missing",
            ):
                self.module._default_powershell_runner(
                    {"platform": "mt4"},
                    response_path=Path(self.temporary.name) / "response.json",
                    timeout_seconds=10,
                )

    def test_backtest_process_timeout_includes_post_wait_evidence_margin(self) -> None:
        response = Path(self.temporary.name) / "ui-response.json"
        observed: dict[str, int] = {}

        def fake_run(*_args, **kwargs):
            observed["timeout"] = int(kwargs["timeout"])
            response.write_text('{"ok":true}', encoding="utf-8")
            return mock.Mock(returncode=0, stdout=b"", stderr=b"")

        with (
            mock.patch.object(
                self.module,
                "_powershell_executable",
                return_value=Path("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"),
            ),
            mock.patch.object(self.module.subprocess, "run", side_effect=fake_run),
        ):
            result = self.module._default_powershell_runner(
                {"platform": "mt4"},
                response_path=response,
                timeout_seconds=self.module.DEFAULT_BACKTEST_TIMEOUT_SECONDS,
            )
        self.assertTrue(result["ok"])
        self.assertEqual(
            observed["timeout"],
            self.module.DEFAULT_BACKTEST_TIMEOUT_SECONDS
            + self.module.POWERSHELL_COMPLETION_MARGIN_SECONDS,
        )

    def test_compile_wrapper_grace_preserves_inner_timeout_failure_code(self) -> None:
        response = Path(self.temporary.name) / "compile-ui-response.json"
        observed: dict[str, int] = {}

        def fake_run(*_args, **kwargs):
            observed["timeout"] = int(kwargs["timeout"])
            response.write_text(
                json.dumps(
                    {
                        "ok": False,
                        "reasonCode": "visible_compile_binary_not_fresh",
                    }
                ),
                encoding="utf-8",
            )
            return mock.Mock(returncode=1, stdout=b"", stderr=b"")

        with (
            mock.patch.object(
                self.module,
                "_powershell_executable",
                return_value=Path(
                    "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
                ),
            ),
            mock.patch.object(self.module.subprocess, "run", side_effect=fake_run),
        ):
            with self.assertRaises(self.module.VisibleTerminalAdapterError) as error:
                self.module._default_powershell_runner(
                    {"platform": "mt4", "action": "compile"},
                    response_path=response,
                    timeout_seconds=self.module.DEFAULT_UI_TIMEOUT_SECONDS,
                )
        self.assertEqual(error.exception.code, "visible_compile_binary_not_fresh")
        self.assertEqual(
            observed["timeout"],
            self.module.DEFAULT_UI_TIMEOUT_SECONDS
            + self.module.POWERSHELL_COMPILE_COMPLETION_MARGIN_SECONDS,
        )
        self.assertGreater(
            observed["timeout"],
            self.module.DEFAULT_UI_TIMEOUT_SECONDS,
        )

    def test_powershell_contract_has_bounded_visible_safety_controls(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        for prohibited in (
            "DTM_SETSYSTEMTIME",
            "keybd_event",
            "mouse_event",
            "System.Windows.Forms.SendKeys",
        ):
            self.assertNotIn(prohibited, source)
        self.assertNotRegex(source, r"(?m)^\s*public static extern IntPtr SendMessage\(")
        for required in (
            "SendMessageTimeout",
            '"1128"',
            '"6217"',
            '"1029"',
            '"1400"',
            '"1034"',
            '"1025"',
            '"12320"',
            '"1357"',
            '"4011"',
            '"4012"',
            "recover_compile",
            "recover_inflight_compile",
            "recover_inflight_backtest",
            "recover_completed_backtest",
            "recover_collected_backtest",
            "recover_backtest",
            "Get-ExistingVisibleProcess",
            "Read-MetaEditorCompileResult",
            "Get-ComboRuntimeInfo",
            "Convert-ComboMessageInteger",
            'return "fast_idle_evidence_required"',
            "Test-TesterLogAdvanced",
            "fastCompletionTesterLogAdvanced",
            "freshResultEvidenceCaptured",
            "testerInputPresetApplied",
            "testerInputPresetReadbackVerified",
            "inputPresetReadbackSaved",
            "Test-TesterInputReadbackSet",
            "Write-DurableStartBoundary",
            "Assert-DeployedExpertDigest",
            "Assert-CompileWorkingCopy",
            "Assert-SingleFileLink",
            "Assert-NoReparsePathComponents",
            "GetFileLinkCount",
            '"agenthq_{0}.mq4"',
            "compileWorkingCopyVerified = $true",
            "workingSourceSha256",
            "workingBinarySha256",
            "FileMode]::CreateNew",
            "FileOptions]::WriteThrough",
            "Flush($true)",
            "MetafxVisibleMsaa",
            "CB_SETCURSEL",
            "CB_SHOWDROPDOWN",
            "CountExactPath",
            "SelectUniqueExactPath",
            "IsUniqueExactPathSelected",
            "SendInput",
            "MOUSEEVENTF_LEFTDOWN",
            "MOUSEEVENTF_LEFTUP",
            "MOUSEEVENTF_RIGHTDOWN",
            "MOUSEEVENTF_RIGHTUP",
            "GetCursorPos",
            "SetCursorPos",
            "SendMouseClick",
            "Get-CursorSnapshot",
            "Restore-CursorSnapshot",
            "Invoke-PhysicalMouseClickAtScreenPoint",
            "PostMessage",
            "GetMenuItemRect",
            "TCM_GETCURSEL",
            "Set-NativeEditTextExact",
            "[object]$Preset",
            "AttachThreadInput",
            "BringWindowToTop",
            "$Window.SetFocus()",
            "$attachedTarget",
            "$attachedForeground",
        ):
            self.assertIn(required, source)
        self.assertGreaterEqual(source.count("compileWorkingCopyVerified = $true"), 3)
        self.assertGreaterEqual(source.count("workingSourceSha256 ="), 3)
        self.assertGreaterEqual(source.count("workingBinarySha256 ="), 3)

        unique_start = source.index("function Get-UniqueControl(")
        unique_end = source.index("\nfunction ", unique_start + 1)
        unique_contract = source[unique_start:unique_end]
        self.assertIn("$owned.Count -eq 0", unique_contract)
        self.assertIn('"control_{0}_unavailable"', unique_contract)
        self.assertIn("$owned.Count -gt 1", unique_contract)
        self.assertIn('"control_{0}_ambiguous"', unique_contract)

        recovery_start = source.index(
            'if ($request.action -in @(\n'
            '        "recover_inflight_backtest",\n'
            '        "recover_completed_backtest",\n'
            '        "recover_collected_backtest"'
        )
        recovery_end = source.index(
            'if ($request.action -eq "recover_backtest")',
            recovery_start,
        )
        recovery = source[recovery_start:recovery_end]
        self.assertNotIn("Invoke-StartButton", recovery)
        self.assertNotIn("TBM_SETPOS", recovery)
        self.assertIn('$startName -ne "Stop"', recovery)
        self.assertIn('$startName -ne "Start"', recovery)
        self.assertIn("Wait-TesterComplete", recovery)
        self.assertIn("Save-WindowPng", recovery)
        self.assertIn("Save-TesterReport", recovery)
        self.assertIn("recoveredWithoutStart = $true", recovery)
        self.assertIn("executionObservedRunning = -not $completedCheckpoint", recovery)
        self.assertIn("completedResultCheckpointReused = $completedCheckpoint", recovery)
        self.assertIn("completedReportCheckpointReused = $collectedCheckpoint", recovery)
        self.assertIn(
            "if (-not $collectedCheckpoint) {\n            Save-TesterReport",
            recovery,
        )
        self.assertIn('"recovery_collected_checkpoint_observed"', recovery)
        self.assertIn('GetExtension($reportPath)', recovery)
        self.assertIn('ChangeExtension($reportPath, ".html")', recovery)
        self.assertIn('".htm"', recovery)
        self.assertIn("tester_completed_recovery_log_unverified", recovery)
        speed_start = source.index("function Set-TesterVisualSpeedMaximum(")
        speed_end = source.index("\nfunction ", speed_start + 1)
        speed = source[speed_start:speed_end]
        self.assertIn('Find-DescendantsById $TesterPane "1401"', speed)
        self.assertIn('ClassName -eq "msctls_trackbar32"', speed)
        self.assertIn("RangeValuePattern]::Pattern", speed)
        self.assertIn("$range.SetValue($maximum - 1)", speed)
        self.assertIn("$range.SetValue($maximum)", speed)
        self.assertIn("tester_visual_speed_not_applied", speed)
        normal_start = source.index('if ($request.action -eq "backtest")')
        speed_call = source.index("Set-TesterVisualSpeedMaximum", normal_start)
        boundary_write = source.index("Write-DurableStartBoundary", speed_call)
        self.assertLess(speed_call, boundary_write)
        for retired_mouse_message in (
            "WM_RBUTTONDOWN",
            "WM_RBUTTONUP",
            "WM_MOUSEMOVE",
            "ScreenToClient",
        ):
            self.assertNotIn(retired_mouse_message, source)
        native_tab_start = source.index("function Invoke-ExactNativeTesterTabClick(")
        native_tab_end = source.index("\nfunction ", native_tab_start + 1)
        native_tab = source[native_tab_start:native_tab_end]
        self.assertEqual(source.count("[MetafxVisibleNative]::WM_LBUTTONDOWN"), 1)
        self.assertEqual(source.count("[MetafxVisibleNative]::WM_LBUTTONUP"), 1)
        self.assertIn("[IntPtr]$ExpectedTesterHandle", native_tab)
        self.assertIn("[IntPtr]$ExpectedTerminalHandle", native_tab)
        self.assertIn("$testerHandle -ne $ExpectedTesterHandle", native_tab)
        self.assertIn("GA_ROOT", native_tab)
        self.assertIn("$ExpectedTerminalHandle", native_tab)
        self.assertIn('Get-WindowClass $TabHandle) -ne "AfxWnd140s"', native_tab)
        self.assertIn("GetDlgCtrlID($TabHandle) -ne 1137", native_tab)
        self.assertIn("GetDlgCtrlID($testerHandle) -ne 83", native_tab)
        self.assertIn("[MetafxVisibleNative]::WS_DISABLED", native_tab)
        self.assertIn("$ClientX -gt 32767", native_tab)
        self.assertIn("SendMessageTimeout", native_tab)
        self.assertIn("SMTO_ABORTIFHUNG", native_tab)
        self.assertNotIn("PostMessage", native_tab)
        self.assertNotIn("SendMouseClick", native_tab)
        send_click_start = source.index("public static bool SendMouseClick")
        send_click_end = source.index("\n    }", send_click_start) + len("\n    }")
        send_click = source[send_click_start:send_click_end]
        self.assertIn("INPUT[] inputs = new INPUT[2]", send_click)
        self.assertIn("MOUSEEVENTF_LEFTDOWN", send_click)
        self.assertIn("MOUSEEVENTF_LEFTUP", send_click)
        self.assertIn("MOUSEEVENTF_RIGHTDOWN", send_click)
        self.assertIn("MOUSEEVENTF_RIGHTUP", send_click)
        self.assertIn("== (uint)inputs.Length", send_click)

        restore_start = source.index("function Restore-CursorSnapshot(")
        restore_end = source.index("\nfunction ", restore_start + 1)
        restore = source[restore_start:restore_end]
        self.assertIn("SetCursorPos", restore)
        self.assertIn("GetCursorPos", restore)
        self.assertIn("cursor_restore_failed", restore)
        self.assertIn("cursor_restore_mismatch", restore)
        self.assertRegex(
            source,
            r"Apply-TesterInputPreset\s+`[\s\S]{0,500}\$preset\s+`",
        )
        self.assertNotIn("$assumptions.Count -ne 13", source)
        self.assertNotIn('$expectedNames = @(\n                "InpStopLossPercent"', source)
        self.assertIn("$assumptions.Count -gt 64", source)
        self.assertIn("EnableTrading|TradingEnabled|AllowTrading", source)
        self.assertIn("deposit = $null", source)
        self.assertIn(
            "$runtime.nativeListAvailable -and $runtime.hasStrings -and",
            source,
        )
        self.assertIn("$count -eq 0", source)
        self.assertIn("nativeListAvailable = $false", source)
        self.assertIn("$raw -eq -1 -or $raw -eq 4294967295", source)
        self.assertIn('"expert_combo_count_invalid"', source)

    def test_powershell_backtest_commits_durable_boundary_before_start(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        branch_start = source.index('if ($request.action -eq "backtest")')
        branch = source[branch_start:]
        settings = branch.index("Save-WindowPng $terminal.Window $settingsPath")
        boundary = branch.index("Write-DurableStartBoundary")
        second_digest = branch.rindex("Assert-DeployedExpertDigest", 0, boundary)
        start = branch.index("Invoke-StartButton $tester")
        wait = branch.index("Wait-TesterComplete")
        durable_result = branch.index(
            "Save-WindowPng $terminal.Window $resultPath",
            wait,
        )
        save_report = branch.index("Save-TesterReport", durable_result)
        self.assertLess(settings, boundary)
        self.assertLess(settings, second_digest)
        self.assertLess(second_digest, boundary)
        self.assertLess(boundary, start)
        self.assertLess(start, wait)
        self.assertLess(wait, durable_result)
        self.assertLess(durable_result, save_report)
        self.assertEqual(branch.count("Invoke-StartButton $tester"), 1)
        start_helper_start = source.index("function Invoke-StartButton(")
        start_helper_end = source.index("\nfunction ", start_helper_start + 1)
        start_contract = source[start_helper_start:start_helper_end]
        self.assertIn("PostMessage", start_contract)
        self.assertIn("BM_CLICK", start_contract)
        self.assertIn("tester_start_post_failed", start_contract)
        self.assertNotIn("Invoke-TargetMessage", start_contract)
        self.assertIn("$StopAlreadyObserved", source)
        self.assertNotIn("catch { $stillPresent = $false }", source)
        apply_start = source.index("function Apply-TesterInputPreset(")
        apply_end = source.index("\nfunction ", apply_start + 1)
        apply_contract = source[apply_start:apply_end]
        self.assertIn("IsWindow($propertiesHandle)", apply_contract)
        self.assertNotRegex(apply_contract, r"catch\s*\{[\s\S]*?testerInputPresetApplied\s*=\s*\$true")

    def test_powershell_backtest_reactivates_settings_before_idle_and_refresh(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        branch_start = source.index('if ($request.action -eq "backtest")')
        branch = source[branch_start:]

        ensure_visible = branch.index("Ensure-TesterVisible $terminal")
        no_modal = branch.index("Assert-NoModal", ensure_visible)
        settings_checkpoint = branch.index(
            '$checkpoint = "tester_settings_surface"', no_modal
        )
        select_settings = branch.index(
            "$tester = Select-TesterSettingsTab", settings_checkpoint
        )
        idle_checkpoint = branch.index('$checkpoint = "tester_idle"', select_settings)
        start_readback = branch.index("Get-TesterStartButton", idle_checkpoint)
        refresh = branch.index("Refresh-ExpertInventory", start_readback)

        self.assertLess(ensure_visible, no_modal)
        self.assertLess(no_modal, settings_checkpoint)
        self.assertLess(settings_checkpoint, select_settings)
        self.assertLess(select_settings, idle_checkpoint)
        self.assertLess(idle_checkpoint, start_readback)
        self.assertLess(start_readback, refresh)
        self.assertNotIn("catch", branch[settings_checkpoint:idle_checkpoint])
        self.assertNotIn("Get-TesterPane", branch[settings_checkpoint:idle_checkpoint])

    def test_powershell_refreshes_the_exact_operation_not_a_stale_basename(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        refresh_start = source.index("function Refresh-ExpertInventory(")
        refresh_end = source.index("\nfunction ", refresh_start + 1)
        contract = source[refresh_start:refresh_end]
        self.assertIn("[string]$ExpectedUiPath", contract)
        self.assertIn("$operationFolder", contract)
        self.assertIn("TrySelectUniqueExactNameCenter", contract)
        self.assertIn("TVM_GETNEXTITEM", contract)
        self.assertIn("TVGN_CARET", contract)
        self.assertIn("TVM_ENSUREVISIBLE", contract)
        self.assertIn("navigator_refresh_selection_unavailable", contract)
        self.assertLess(
            contract.index("TVM_ENSUREVISIBLE"),
            contract.index("TrySelectUniqueExactNameCenter"),
        )
        self.assertRegex(
            contract,
            r'TrySelectUniqueExactNameCenter\([\s\S]{0,180}"Expert Advisors"[\s\S]{0,80}0x24',
        )
        self.assertIn("Get-CursorSnapshot", contract)
        self.assertIn("Invoke-PhysicalMouseClickAtScreenPoint", contract)
        self.assertIn('"right"', contract)
        self.assertIn("finally", contract)
        self.assertIn(
            'Restore-CursorSnapshot $cursorSnapshot "navigator_refresh"',
            contract,
        )
        self.assertIn("Invoke-ExactPopupMenuItem", contract)
        self.assertIn('"Refresh"', contract)
        self.assertNotIn("$postedRefresh", contract)
        self.assertNotRegex(
            contract,
            r"TerminalWindow\.Current\.NativeWindowHandle[\s\S]{0,160}WM_COMMAND",
        )
        self.assertIn(
            "CountExactName($treeHandle, $operationFolder)",
            contract,
        )
        self.assertNotIn("CountExactName($treeHandle, $expertStem)", contract)
        self.assertLess(
            contract.index("Get-CursorSnapshot"),
            contract.index("Invoke-PhysicalMouseClickAtScreenPoint"),
        )
        self.assertLess(
            contract.index("Invoke-PhysicalMouseClickAtScreenPoint"),
            contract.index("Wait-UniqueOwnedPopupHandle"),
        )
        self.assertLess(
            contract.index('Restore-CursorSnapshot $cursorSnapshot "navigator_refresh"'),
            contract.rindex("CountExactName($treeHandle, $operationFolder)"),
        )
        branch_start = source.index('if ($request.action -eq "backtest")')
        branch = source[branch_start:]
        self.assertRegex(
            branch,
            r"Refresh-ExpertInventory[\s\S]{0,220}\$request\.expertUiPath",
        )
        self.assertLess(
            branch.index("Refresh-ExpertInventory"),
            branch.index("Select-ExactExpert"),
        )

    def test_powershell_commits_exact_expert_through_the_visible_exact_tree_path(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        msaa_start = source.index("public static class MetafxVisibleMsaa")
        msaa_end = source.index('"@ -ReferencedAssemblies @("Accessibility.dll")', msaa_start)
        msaa_contract = source[msaa_start:msaa_end]
        self.assertIn("ReadHierarchyLevel", msaa_contract)
        self.assertIn("ReadFlatTreeItems", msaa_contract)
        self.assertIn("get_accValue", msaa_contract)
        self.assertIn("MaximumNodes", msaa_contract)
        self.assertIn("MaximumDepth", msaa_contract)
        self.assertIn(
            "while (stack.Count > 0 && stack[stack.Count - 1].Level >= level)",
            msaa_contract,
        )
        self.assertIn("candidate.Level != baseLevel + offset", msaa_contract)
        self.assertNotIn("NAVDIR_LEFT", msaa_contract)
        self.assertNotIn("accNavigate", msaa_contract)

        select_start = source.index("function Select-ExactExpert(")
        select_end = source.index("\nfunction ", select_start + 1)
        contract = source[select_start:select_end]
        self.assertIn("CB_SHOWDROPDOWN", contract)
        self.assertIn('"SysTreeView32"', contract)
        self.assertIn('[string[]]@("Metafxclub")', contract)
        self.assertIn('[string[]]@("Metafxclub", "AgentHQ")', contract)
        self.assertIn(
            '[string[]]@("Metafxclub", "AgentHQ", $operationFolder)',
            contract,
        )
        self.assertIn(
            '$expertPath = @("Metafxclub", "AgentHQ", $operationFolder, $FileName)',
            contract,
        )
        self.assertIn("CountExactPath($pickerHandle, $expertPath)", contract)
        self.assertIn("foreach ($folderPrefix in $folderPrefixes)", contract)
        self.assertIn("CountExactPath($pickerHandle, $prefixPath)", contract)
        self.assertIn("SelectUniqueExactPath($pickerHandle, $prefixPath)", contract)
        self.assertIn("IsUniqueExactPathSelected($pickerHandle, $prefixPath)", contract)
        self.assertIn("$attemptsRemaining--", contract)
        self.assertIn('Stop-Adapter "expert_picker_folder_ambiguous"', contract)
        self.assertIn('Stop-Adapter "expert_picker_folder_unavailable"', contract)
        self.assertIn('Stop-Adapter "expert_picker_leaf_ambiguous"', contract)
        self.assertIn('Stop-Adapter "expert_picker_leaf_unavailable"', contract)
        self.assertIn("Send-BalancedKey $pickerHandle 0x27", contract)
        self.assertIn("SelectUniqueExactPath($pickerHandle, $expertPath)", contract)
        self.assertIn("IsUniqueExactPathSelected($pickerHandle, $expertPath)", contract)
        self.assertIn("Send-BalancedKey $pickerHandle 0x0D", contract)
        self.assertIn("Dismiss-OwnedPopup $pickerHandle", contract)
        self.assertNotIn("Set-NativeEditTextExact", contract)
        self.assertNotIn("$readback.edit", contract)
        self.assertLess(
            contract.index("CB_SHOWDROPDOWN"),
            contract.index("foreach ($folderPrefix in $folderPrefixes)"),
        )
        self.assertLess(
            contract.index("foreach ($folderPrefix in $folderPrefixes)"),
            contract.index("SelectUniqueExactPath($pickerHandle, $expertPath)"),
        )
        self.assertLess(
            contract.index("IsUniqueExactPathSelected($pickerHandle, $expertPath)"),
            contract.index("Send-BalancedKey $pickerHandle 0x0D"),
        )

    def test_powershell_materializes_lazy_picker_prefixes_before_leaf_selection(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        select_start = source.index("function Select-ExactExpert(")
        select_end = source.index("\nfunction ", select_start + 1)
        contract = source[select_start:select_end]

        root_prefix = contract.index('[string[]]@("Metafxclub")')
        agent_prefix = contract.index('[string[]]@("Metafxclub", "AgentHQ")')
        operation_prefix = contract.index(
            '[string[]]@("Metafxclub", "AgentHQ", $operationFolder)'
        )
        prefix_loop = contract.index("foreach ($folderPrefix in $folderPrefixes)")
        expand_prefix = contract.index("Send-BalancedKey $pickerHandle 0x27")
        leaf_loop = contract.index("[bool]$leafSelected = $false")

        self.assertLess(root_prefix, agent_prefix)
        self.assertLess(agent_prefix, operation_prefix)
        self.assertLess(operation_prefix, prefix_loop)
        self.assertLess(prefix_loop, expand_prefix)
        self.assertLess(expand_prefix, leaf_loop)
        self.assertEqual(contract.count("[int]$attemptsRemaining = $MaximumSteps"), 1)
        self.assertEqual(contract.count("$attemptsRemaining--"), 2)
        self.assertEqual(contract.count("Send-BalancedKey $pickerHandle 0x27"), 1)
        self.assertIn("Start-Sleep -Milliseconds 50", contract[prefix_loop:expand_prefix])
        self.assertNotIn('CountExactName($pickerHandle, $FileName)', contract)
        self.assertNotIn('SelectUniqueExact($pickerHandle, $FileName)', contract)
        self.assertNotIn('"Loading"', contract)

    def test_powershell_modal_buttons_are_posted_then_observed(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        helper_start = source.index("function Invoke-ExactButton(")
        helper_end = source.index("\nfunction ", helper_start + 1)
        helper = source[helper_start:helper_end]
        self.assertIn("PostMessage", helper)
        self.assertIn("BM_CLICK", helper)
        self.assertIn("[MetafxVisibleNative]::WS_DISABLED", helper)
        self.assertNotIn("$button.Current.IsEnabled", helper)
        self.assertIn("$button.Current.IsOffscreen", helper)
        self.assertIn('"{0}_post_failed"', helper)
        self.assertNotIn("Invoke-TargetMessage", helper)

        apply_start = source.index("function Apply-TesterInputPreset(")
        apply_end = source.index("\nfunction ", apply_start + 1)
        contract = source[apply_start:apply_end]
        properties_click = contract.index('"1025" @("Expert properties")')
        properties_wait = contract.index("Wait-UniqueOwnedDialog")
        load_click = contract.index('"4011" @("Load")')
        load_wait = contract.index("Invoke-FileDialogPath", load_click)
        save_click = contract.index('"4012" @("Save")')
        save_wait = contract.index("Invoke-FileDialogPath", save_click)
        self.assertLess(properties_click, properties_wait)
        self.assertLess(load_click, load_wait)
        self.assertLess(save_click, save_wait)
        properties_handle = contract.index("[IntPtr]$propertiesHandle")
        guarded_work = contract.index("try {", properties_handle)
        cleanup = contract.index(
            "Close-ExactOwnedFileDialogAfterFailure",
            save_wait,
        )
        rethrow = contract.index("throw", cleanup)
        self.assertLess(properties_handle, guarded_work)
        self.assertLess(guarded_work, load_click)
        self.assertLess(load_wait, save_click)
        self.assertLess(save_wait, cleanup)
        self.assertLess(cleanup, rethrow)
        self.assertIn("$properties `", contract[cleanup:rethrow])
        self.assertIn("$propertiesHandle `", contract[cleanup:rethrow])
        self.assertIn("$ProcessId)", contract[cleanup:rethrow])
        self.assertNotIn("throw $", contract[cleanup:])

    def test_powershell_selects_inputs_tab_by_semantic_name_across_mt4_variants(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        helper_start = source.index("function Select-ExpertInputsTab(")
        helper_end = source.index("\nfunction ", helper_start + 1)
        contract = source[helper_start:helper_end]
        self.assertIn("$count -lt 2 -or $count -gt 8", contract)
        self.assertNotIn("$count -ne 2", contract)
        self.assertIn("ControlType]::TabItem", contract)
        self.assertIn('"Inputs"', contract)
        self.assertIn("SelectionItemPattern]::Pattern", contract)
        self.assertIn("$inputSelection.Select()", contract)
        self.assertIn("$inputSelection.Current.IsSelected", contract)
        self.assertIn('Get-UniqueControl $Dialog "1357"', contract)
        self.assertNotIn("Send-BalancedKey $tabHandle 0x27", contract)

    def test_powershell_reads_owner_draw_symbol_from_the_selected_item(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        reader_start = source.index("function Read-CurrentSymbol(")
        reader_end = source.index("\nfunction ", reader_start + 1)
        contract = source[reader_start:reader_end]
        self.assertIn("SelectionPattern", contract)
        self.assertIn("GetSelection()", contract)
        self.assertIn("$selected[0].Current.Name", contract)
        self.assertNotIn("$combo.Current.Name).Trim()", contract)

        recovery_start = source.index('if ($request.action -eq "recover_backtest")')
        recovery_end = source.index('if ($request.action -eq "compile")', recovery_start)
        recovery = source[recovery_start:recovery_end]
        self.assertIn(
            'Read-SelectedNativeComboValue $tester ([int]$terminal.Process.Id) "1228"',
            recovery,
        )
        self.assertIn(
            'Read-SelectedNativeComboValue $tester ([int]$terminal.Process.Id) "4027"',
            recovery,
        )

    def test_receipt_recovery_reactivates_settings_without_starting_again(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        recovery_start = source.index('if ($request.action -eq "recover_backtest")')
        recovery_end = source.index(
            'if ($request.action -eq "compile")',
            recovery_start,
        )
        recovery = source[recovery_start:recovery_end]

        self.assertEqual(recovery.count("Select-TesterSettingsTab"), 2)
        first_settings = recovery.index("Select-TesterSettingsTab")
        start_readback = recovery.index("Get-TesterStartButton", first_settings)
        expert_readback = recovery.index("Read-ExpertSelection", start_readback)
        post_terminal = recovery.index("$terminalPost = Get-ExistingVisibleProcess")
        second_settings = recovery.index("Select-TesterSettingsTab", post_terminal)
        post_binding = recovery.index("New-RawBinding", second_settings)
        self.assertLess(first_settings, start_readback)
        self.assertLess(start_readback, expert_readback)
        self.assertLess(post_terminal, second_settings)
        self.assertLess(second_settings, post_binding)

        for forbidden in (
            "Invoke-StartButton",
            "Start Strategy Tester",
            "startInvoked = $true",
            "executionObservedRunning = $true",
        ):
            self.assertNotIn(forbidden, recovery)
        self.assertIn("recoveredWithoutAction = $true", recovery)
        self.assertIn("settingsStillVerified = $true", recovery)

    def test_powershell_validates_period_and_model_selected_items_not_labels(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        select_start = source.index("function Select-ComboListItem(")
        select_end = source.index("\nfunction ", select_start + 1)
        contract = source[select_start:select_end]
        self.assertIn("SelectionPattern", contract)
        self.assertIn("$selectionPattern.Current.GetSelection()", contract)
        self.assertIn("$selectedItems[0].Current.Name", contract)
        self.assertIn("$uiaReadback.Equals($actual", contract)
        self.assertNotIn("$combo.Current.Name).Trim()", contract)
        self.assertIn("$notificationPosted", contract)
        self.assertNotIn("SendMessageTimeout(\n        $parent", contract)

    def test_powershell_saves_report_from_an_exact_visible_report_row(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        tab_helper_start = source.index("function Get-UniqueVisibleTesterTabStrip(")
        tab_helper_end = source.index("\nfunction ", tab_helper_start + 1)
        tab_helper = source[tab_helper_start:tab_helper_end]
        self.assertIn('Find-DescendantsById $TesterPane "1137"', tab_helper)
        self.assertIn('[string]$candidate.Current.ClassName -eq "AfxWnd140s"', tab_helper)
        self.assertIn('(Get-WindowClass $candidateHandle) -eq "AfxWnd140s"', tab_helper)
        self.assertIn("$tabStripsByHandle", tab_helper)
        self.assertIn("[MetafxVisibleNative]::WS_DISABLED", tab_helper)
        self.assertNotIn("$candidate.Current.IsEnabled", tab_helper)
        self.assertIn("Get-WindowOwner", tab_helper)
        self.assertIn("GetDlgCtrlID($testerHandle) -ne 83", tab_helper)
        self.assertIn("GetDlgCtrlID($candidateHandle) -eq 1137", tab_helper)
        self.assertIn("GetParent($candidateHandle) -eq $testerHandle", tab_helper)
        self.assertIn("GetWindowRect", tab_helper)
        self.assertIn("IsWindowVisible($candidateHandle)", tab_helper)

        select_start = source.index("function Select-TesterReportTab(")
        select_end = source.index("\nfunction ", select_start + 1)
        select_contract = source[select_start:select_end]
        self.assertGreaterEqual(
            select_contract.count("Get-UniqueVisibleTesterTabStrip"), 2
        )
        self.assertIn("$currentTester = Get-TesterPane", select_contract)
        self.assertIn("$currentBinding.TabWidth", select_contract)
        self.assertIn("$currentBinding.TabHeight", select_contract)
        self.assertIn("$scanRightClient", select_contract)
        self.assertIn("$clientX", select_contract)
        self.assertIn("$clientY", select_contract)
        self.assertIn("Invoke-ExactNativeTesterTabClick", select_contract)
        self.assertNotIn("Invoke-PhysicalMouseClickAtScreenPoint", select_contract)
        self.assertNotIn("Get-CursorSnapshot", select_contract)
        self.assertNotIn("Restore-CursorSnapshot", select_contract)
        self.assertIn("$reportDeadline", select_contract)
        self.assertIn("Start-Sleep -Milliseconds 75", select_contract)
        self.assertIn("Get-VisibleTesterReportLists", select_contract)
        self.assertNotIn("$currentTesterHandle -ne $testerHandle", select_contract)
        self.assertNotIn("$currentTabRect", select_contract)
        self.assertNotIn("$scanX", select_contract)
        self.assertIn("Test-ForegroundWindowBinding", select_contract)
        self.assertNotIn("SelectUniqueExactName($testerHandle, \"Results\")", select_contract)

        visible_start = source.index("function Get-VisibleTesterReportLists(")
        visible_end = source.index("\nfunction ", visible_start + 1)
        visible_contract = source[visible_start:visible_end]
        self.assertIn('Find-DescendantsById $TesterPane "33213"', visible_contract)
        self.assertIn('ClassName -ne "SysListView32"', visible_contract)
        self.assertIn("GetDlgCtrlID($candidateHandle) -ne 33213", visible_contract)
        self.assertIn("GetParent($candidateHandle) -ne $testerHandle", visible_contract)
        self.assertIn("GetWindowRect($candidateHandle", visible_contract)
        self.assertIn("IsWindow($candidateHandle)", visible_contract)
        self.assertIn("LVS_TYPEMASK", visible_contract)
        self.assertIn("LVS_REPORT", visible_contract)
        self.assertNotIn(
            "[MetafxVisibleNative]::GetForegroundWindow() -ne",
            select_contract,
        )

        save_start = source.index("function Save-TesterReport(")
        save_end = source.index("\n$request = $null", save_start + 1)
        contract = source[save_start:save_end]
        self.assertIn("Select-TesterReportTab", contract)
        self.assertIn("[string]$ReportScreenshotPath", contract)
        self.assertIn("Assert-ExistingPngEvidence", contract)
        self.assertIn("Save-WindowPng $TerminalWindow $ReportScreenshotPath", contract)
        self.assertIn("TrySelectFirstFullyVisibleRoleCenter", contract)
        self.assertIn("0x22", contract)
        self.assertIn("Get-CursorSnapshot", contract)
        self.assertIn("Invoke-PhysicalMouseClickAtScreenPoint", contract)
        self.assertIn('"right"', contract)
        self.assertIn("finally", contract)
        self.assertIn(
            'Restore-CursorSnapshot $cursorSnapshot "tester_save_report"',
            contract,
        )
        self.assertIn("Invoke-ExactPopupMenuItem", contract)
        self.assertIn('"Save as Report"', contract)
        self.assertNotIn("$postedSave", contract)
        self.assertNotRegex(
            contract,
            r"TerminalWindow\.Current\.NativeWindowHandle[\s\S]{0,160}WM_COMMAND",
        )
        self.assertIn("IsWindow($dialogHandle)", contract)
        self.assertIn("IsWindowVisible($dialogHandle)", contract)
        self.assertIn("(Get-Item -LiteralPath $ReportPath).Length -gt 256", contract)
        self.assertNotIn("WM_CONTEXTMENU", contract)
        self.assertIn("$currentLists = @(Get-VisibleTesterReportLists", contract)
        self.assertIn("$currentTesterHandle -ne $testerHandle", contract)
        self.assertIn("$currentListHandle -ne $listHandle", contract)
        self.assertIn('(Get-WindowClass $listHandle) -ne "SysListView32"', contract)
        self.assertIn("GetParent($listHandle) -ne $currentTesterHandle", contract)
        self.assertIn("GetDlgCtrlID($listHandle) -ne 33213", contract)
        self.assertIn("IsWindowVisible($listHandle)", contract)
        self.assertIn("LVS_TYPEMASK", contract)
        self.assertIn("$anchorX -lt $currentListRect.Left", contract)
        self.assertIn("Test-ForegroundWindowBinding", contract)
        foreground_start = source.index("function Test-ForegroundWindowBinding(")
        foreground_end = source.index("\nfunction ", foreground_start + 1)
        foreground_contract = source[foreground_start:foreground_end]
        self.assertIn("GetForegroundWindow()", foreground_contract)
        self.assertIn("GetAncestor", foreground_contract)
        self.assertIn("GA_ROOT", foreground_contract)
        self.assertIn("Get-WindowOwner $foreground", foreground_contract)
        self.assertIn("$foregroundRoot -eq $expectedRoot", foreground_contract)
        self.assertLess(
            contract.index("Select-TesterReportTab"),
            contract.index("Save-WindowPng $TerminalWindow $ReportScreenshotPath"),
        )
        self.assertLess(
            contract.index("Save-WindowPng $TerminalWindow $ReportScreenshotPath"),
            contract.index("Invoke-PhysicalMouseClickAtScreenPoint"),
        )
        self.assertLess(
            contract.index("$currentLists = @(Get-VisibleTesterReportLists"),
            contract.index("Invoke-PhysicalMouseClickAtScreenPoint"),
        )
        self.assertLess(
            contract.index("Get-CursorSnapshot"),
            contract.index("Invoke-PhysicalMouseClickAtScreenPoint"),
        )
        self.assertLess(
            contract.index("Invoke-PhysicalMouseClickAtScreenPoint"),
            contract.index("Wait-UniqueOwnedPopupHandle"),
        )
        self.assertLess(
            contract.index('Restore-CursorSnapshot $cursorSnapshot "tester_save_report"'),
            contract.index("Wait-UniqueOwnedDialog"),
        )
        self.assertIn(
            'Get-FileDialogFileNameBinding `',
            contract,
        )
        self.assertIn('"tester_save_filename"', contract)
        self.assertIn("Set-FileDialogFileNameExact", contract)
        self.assertIn('Stop-Adapter "tester_report_path_not_committed"', contract)

        popup_start = source.index("function Invoke-ExactPopupMenuItem(")
        popup_end = source.index("\nfunction ", popup_start + 1)
        popup = source[popup_start:popup_end]
        self.assertIn("GetMenuItemRect", popup)
        self.assertIn("GetWindowRect", popup)
        self.assertIn("Invoke-PhysicalMouseClickAtScreenPoint", popup)
        self.assertIn('"left"', popup)
        self.assertIn("IsWindowVisible($PopupHandle)", popup)
        self.assertIn("Dismiss-OwnedPopup", popup)
        self.assertNotIn("WM_LBUTTON", popup)
        self.assertNotIn("WM_MOUSEMOVE", popup)
        self.assertNotIn("ScreenToClient", popup)
        self.assertLess(
            popup.index("GetMenuItemRect"),
            popup.index("Invoke-PhysicalMouseClickAtScreenPoint"),
        )

    def test_powershell_reactivates_exact_settings_surface_around_report_collection(
        self,
    ) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")

        surface_start = source.index("function Get-VisibleTesterSettingsSurface(")
        surface_end = source.index("\nfunction ", surface_start + 1)
        surface = source[surface_start:surface_end]
        for automation_id, class_name in (
            ("1034", "Button"),
            ("1128", "ComboBox"),
            ("1347", "ComboBox"),
            ("1228", "ComboBox"),
            ("4027", "ComboBox"),
            ("1023", "Button"),
            ("1029", "Button"),
            ("1400", "Button"),
        ):
            self.assertIn(f'"{automation_id}"', surface)
            self.assertIn(f'"{class_name}"', surface)
        self.assertIn("Get-WindowOwner", surface)
        self.assertIn("GetDlgCtrlID", surface)
        self.assertIn("GetParent($settingsParent) -ne $testerHandle", surface)
        self.assertIn('(Get-WindowClass $settingsParent) -ne "AfxWnd140s"', surface)
        self.assertIn("IsWindowVisible", surface)
        self.assertIn("[MetafxVisibleNative]::WS_DISABLED", surface)
        self.assertNotIn("$_.Current.IsEnabled", surface)
        self.assertIn("$_.Current.IsOffscreen", surface)
        self.assertIn("GetWindowRect($settingsParent", surface)
        self.assertIn("tester_settings_surface_ambiguous", surface)
        self.assertIn('Find-DescendantsById $expertCombo "6217"', surface)
        self.assertIn("GetParent([IntPtr]$_.Current.NativeWindowHandle) -eq $expertComboHandle", surface)
        self.assertIn('Find-DescendantsById $TesterPane "1001"', surface)
        self.assertIn("GetDlgCtrlID($spreadComboHandle) -ne 1207", surface)
        self.assertIn("GetParent($spreadComboHandle) -ne $settingsParent", surface)

        select_start = source.index("function Select-TesterSettingsTab(")
        select_end = source.index("\nfunction ", select_start + 1)
        select_contract = source[select_start:select_end]
        self.assertIn("Get-VisibleTesterSettingsSurface", select_contract)
        self.assertGreaterEqual(
            select_contract.count("Get-UniqueVisibleTesterTabStrip"), 2
        )
        self.assertIn("$currentTester = Get-TesterPane", select_contract)
        self.assertIn("$currentBinding.TabWidth", select_contract)
        self.assertIn("$currentBinding.TabHeight", select_contract)
        self.assertIn("$scanRightClient", select_contract)
        self.assertIn("$clientX", select_contract)
        self.assertIn("$clientY", select_contract)
        self.assertNotIn("$currentTesterHandle -ne $testerHandle", select_contract)
        self.assertNotIn("$currentTabRect", select_contract)
        self.assertIn("Test-ForegroundWindowBinding", select_contract)
        self.assertIn("Invoke-ExactNativeTesterTabClick", select_contract)
        self.assertNotIn("Invoke-PhysicalMouseClickAtScreenPoint", select_contract)
        self.assertNotIn("Get-CursorSnapshot", select_contract)
        self.assertNotIn("Restore-CursorSnapshot", select_contract)

        recovery_start = source.index(
            'if ($request.action -in @(\n'
            '        "recover_inflight_backtest",\n'
            '        "recover_completed_backtest",\n'
            '        "recover_collected_backtest"'
        )
        recovery_end = source.index(
            'if ($request.action -eq "recover_backtest")',
            recovery_start,
        )
        recovery = source[recovery_start:recovery_end]
        self.assertEqual(recovery.count("Select-TesterSettingsTab"), 2)
        first_settings = recovery.index("Select-TesterSettingsTab")
        start_readback = recovery.index("Get-TesterStartButton", first_settings)
        save_report = recovery.index("Save-TesterReport", start_readback)
        second_settings = recovery.index("Select-TesterSettingsTab", save_report)
        expert_drift = recovery.index("Read-ExpertSelection", second_settings)
        self.assertLess(first_settings, start_readback)
        self.assertLess(start_readback, save_report)
        self.assertLess(save_report, second_settings)
        self.assertLess(second_settings, expert_drift)

    def test_powershell_targets_only_the_exact_file_name_edit(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        native_label_start = source.index("function Test-NativeFileNameLabel(")
        native_label_end = source.index("\nfunction ", native_label_start + 1)
        native_label = source[native_label_start:native_label_end]
        self.assertIn("$normalized.IndexOf([char]0x26)", native_label)
        self.assertIn(
            "$normalized.IndexOf([char]0x26, $acceleratorIndex + 1)",
            native_label,
        )
        self.assertIn("$normalized.Remove($acceleratorIndex, 1)", native_label)
        self.assertIn("return Test-FileNameLabel $normalized", native_label)

        helper_start = source.index("function Get-FileDialogFileNameBinding(")
        helper_end = source.index("\nfunction ", helper_start + 1)
        helper = source[helper_start:helper_end]
        self.assertIn('Find-DescendantsById $Dialog "1001"', helper)
        self.assertIn('Find-DescendantsById $Dialog "1148"', helper)
        self.assertIn('Find-DescendantsById $Dialog "1152"', helper)
        self.assertIn('[string]$candidate.Current.ClassName -ne "Edit"', helper)
        self.assertIn("$candidate.Current.ProcessId", helper)
        self.assertIn("Get-WindowOwner $candidateHandle", helper)
        self.assertIn("IsWindowVisible($candidateHandle)", helper)
        self.assertIn("$candidate.Current.IsEnabled", helper)
        self.assertIn("$candidate.Current.IsOffscreen", helper)
        self.assertIn("GetDlgCtrlID($candidateHandle)", helper)
        self.assertIn('Get-WindowClass $parentHandle) -in @("ComboBox", "ComboBoxEx32")', helper)
        self.assertIn('FileNameControlHost', helper)
        self.assertIn('[System.Windows.Automation.ControlType]::ComboBox', helper)
        self.assertIn("Test-FileNameLabel", helper)
        self.assertIn('Find-DescendantsById $Dialog "1090"', helper)
        self.assertIn("$eligibleByHandle[$key]", helper)
        self.assertNotIn('foreach ($automationId in @(\"1148\", \"1001\"))', helper)

        nested_start = helper.index('$nativeId -eq 1148')
        classic_start = helper.index('# A classic common dialog', nested_start)
        nested = helper[nested_start:classic_start]
        self.assertIn('[string]$candidate.Current.AutomationId -eq "1148"', nested)
        self.assertIn(
            '$candidate.Current.ControlType -eq '
            '[System.Windows.Automation.ControlType]::Pane',
            nested,
        )
        self.assertIn('(Get-WindowClass $comboHandle) -eq "ComboBox"', nested)
        self.assertIn('GetDlgCtrlID($comboHandle) -eq 1148', nested)
        self.assertIn('(Get-WindowClass $comboExHandle) -eq "ComboBoxEx32"', nested)
        self.assertIn('GetDlgCtrlID($comboExHandle) -eq 1148', nested)
        self.assertIn('GetParent($comboExHandle) -eq $dialogHandle', nested)
        self.assertGreaterEqual(
            nested.count('[System.Windows.Automation.ControlType]::Pane'),
            3,
        )
        self.assertIn('[string]$comboHost.Current.AutomationId -eq "1148"', nested)
        self.assertIn('[string]$comboExHost.Current.AutomationId -eq "1148"', nested)
        self.assertNotIn(
            '$comboHost.Current.ControlType -eq '
            '[System.Windows.Automation.ControlType]::ComboBox',
            nested,
        )
        self.assertNotIn(
            '$comboExHost.Current.ControlType -eq '
            '[System.Windows.Automation.ControlType]::ComboBox',
            nested,
        )
        self.assertIn('[string]$_.Current.AutomationId -eq "1090"', nested)
        self.assertIn('GetDlgCtrlID(', nested)
        self.assertIn(') -eq 1090', nested)
        self.assertIn('Test-NativeFileNameLabel', nested)
        self.assertIn('Test-FileNameLabel ([string]$_.Current.Name)', nested)
        self.assertIn('Kind = "nested_1148"', nested)
        self.assertNotIn('$nativeId -eq 1001', nested)

        modern_start = helper.index('$nativeId -eq 1001')
        modern = helper[modern_start:nested_start]
        self.assertIn(
            '[string]$fileNameHost.Current.AutomationId -in '
            '@("FileNameControlHost", "1148")',
            modern,
        )
        self.assertIn('Test-FileNameLabel ([string]$candidate.Current.Name)', modern)
        self.assertNotIn('Kind = "nested_1148"', modern)

        setter_start = source.index("function Set-FileDialogFileNameExact(")
        setter_end = source.index("\nfunction ", setter_start + 1)
        setter = source[setter_start:setter_end]
        self.assertIn("Restore-Foreground $Binding.Dialog", setter)
        self.assertIn("Invoke-PhysicalMouseClickAtScreenPoint", setter)
        self.assertIn("AutomationElement]::FocusedElement", setter)
        self.assertIn("Select-AllFileDialogEditTextExact", setter)
        self.assertIn("TypeFocusedText($Value)", setter)
        self.assertIn("SendVirtualKeyPress", setter)
        self.assertIn("[MetafxVisibleNative]::VK_TAB", setter)
        self.assertIn("Test-ForegroundWindowBinding", setter)
        self.assertIn("$Binding.FileNameHost", setter)
        self.assertIn("$Binding.Edit", setter)
        self.assertNotIn("$valuePattern.SetValue($Value)", setter)
        self.assertNotIn("Set-NativeEditTextExact", setter)
        self.assertIn("Read-Win32TextExact $editHandle", setter)
        self.assertIn("Read-AutomationValueExact $Binding.Edit", setter)
        self.assertIn("$hostNativeValue", setter)
        self.assertIn("$hostAutomationValue", setter)
        self.assertIn('$bindingKind -eq "nested_1148"', setter)
        self.assertIn('"native_nested_1148"', setter)
        self.assertIn('GetDlgCtrlID($editHandle) -ne 1148', setter)
        self.assertIn('GetDlgCtrlID($fileNameHostHandle) -ne 1148', setter)
        self.assertIn('GetDlgCtrlID($fileNameOuterHostHandle) -ne 1148', setter)
        self.assertIn('GetParent($fileNameOuterHostHandle) -ne $dialogHandle', setter)
        self.assertIn('Test-NativeFileNameLabel', setter)
        self.assertGreaterEqual(
            setter.count('[System.Windows.Automation.ControlType]::Pane'),
            3,
        )
        self.assertIn(
            'has no guaranteed ValuePattern',
            setter,
        )
        nested_readback = setter[setter.index(
            '} elseif ($bindingKind -eq "nested_1148") {'
        ):]
        self.assertNotIn(
            'Read-AutomationValueExact $Binding.Edit',
            nested_readback,
        )
        self.assertNotIn(
            'Read-AutomationValueExact $Binding.FileNameOuterHost',
            setter,
        )
        self.assertNotIn(
            '$Binding.Edit.Current.ControlType -ne '
            '[System.Windows.Automation.ControlType]::Edit',
            setter,
        )
        self.assertIn("public static bool TypeFocusedText", source)
        self.assertNotIn("public static bool ReplaceFocusedText", source)
        self.assertNotIn("VK_CONTROL", source)
        self.assertNotIn("VK_A", source)
        self.assertIn("KEYEVENTF_UNICODE", source)
        self.assertIn("Marshal.SizeOf(typeof(UNIVERSALINPUT))", source)
        self.assertIn("function Get-FileSha256Hex", source)
        self.assertNotIn("Get-FileHash", source)

        load_start = source.index("function Invoke-FileDialogPath(")
        load_end = source.index("\nfunction ", load_start + 1)
        load = source[load_start:load_end]
        self.assertIn(
            'Wait-FileDialogFileNameBinding `',
            load,
        )
        self.assertIn('"tester_input_file_name"', load)
        self.assertIn("Set-FileDialogFileNameExact", load)
        self.assertNotIn('Get-UniqueControl $dialog "1001"', load)
        self.assertIn("Invoke-ExactNativeDialogButton", load)
        self.assertIn("$fileNameBinding.Dialog `", load)
        self.assertNotIn("Invoke-ExactButton $dialog", load)
        self.assertIn("Close-ExactOwnedFileDialogAfterFailure", load)
        self.assertIn("throw", load)
        self.assertNotIn("throw $originalFailure", load)

    def test_native_file_dialog_fallback_requires_exact_bounded_unique_shape(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")

        native_start = source.index("public static class MetafxVisibleNative")
        native_end = source.index('"@', native_start)
        native = source[native_start:native_end]
        for required in (
            "GW_HWNDNEXT = 2",
            "GW_CHILD = 5",
            "GetWindow(IntPtr hWnd, uint command)",
            "IsWindowEnabled(IntPtr hWnd)",
            "GetGUIThreadInfo(uint threadId",
            "GetFocusedWindowFor(IntPtr target)",
        ):
            self.assertIn(required, native)

        children_start = source.index("function Get-BoundedNativeDirectChildren(")
        children_end = source.index("\nfunction ", children_start + 1)
        children = source[children_start:children_end]
        self.assertIn("[MetafxVisibleNative]::GW_CHILD", children)
        self.assertIn("[MetafxVisibleNative]::GW_HWNDNEXT", children)
        self.assertIn("$index -lt 256", children)
        self.assertIn("GetParent($current) -ne $ParentHandle", children)
        self.assertIn("_native_children_limit_exceeded", children)

        assert_start = source.index("function Assert-NativeNested1148Binding(")
        assert_end = source.index("\nfunction ", assert_start + 1)
        exact_assert = source[assert_start:assert_end]
        for required in (
            "IsWindow([IntPtr]$handle)",
            "IsWindowVisible([IntPtr]$handle)",
            "IsWindowEnabled([IntPtr]$handle)",
            "Get-WindowOwner ([IntPtr]$handle)",
            '(Get-WindowClass $dialogHandle) -ne "#32770"',
            '(Get-WindowClass $outerHandle) -ne "ComboBoxEx32"',
            '(Get-WindowClass $comboHandle) -ne "ComboBox"',
            '(Get-WindowClass $editHandle) -ne "Edit"',
            '(Get-WindowClass $labelHandle) -ne "Static"',
            "GetDlgCtrlID($outerHandle) -ne 1148",
            "GetDlgCtrlID($comboHandle) -ne 1148",
            "GetDlgCtrlID($editHandle) -ne 1148",
            "GetDlgCtrlID($labelHandle) -ne 1090",
            "GetParent($outerHandle) -ne $dialogHandle",
            "GetParent($comboHandle) -ne $outerHandle",
            "GetParent($editHandle) -ne $comboHandle",
            "GetParent($labelHandle) -ne $dialogHandle",
            "Test-NativeFileNameLabel (Read-Win32Text $labelHandle)",
            "GetWindowRect($dialogHandle",
            "GetWindowRect($editHandle",
            "$editRect.Left -lt $dialogRect.Left",
            "$editRect.Right -gt $dialogRect.Right",
        ):
            self.assertIn(required, exact_assert)

        fallback_start = source.index(
            "function Get-ExactNativeFileDialogFileNameBinding("
        )
        fallback_end = source.index("\nfunction ", fallback_start + 1)
        fallback = source[fallback_start:fallback_end]
        outer = fallback.index(
            "Get-NativeDirectChildrenById $dialogHandle 1148"
        )
        combo = fallback.index(
            "Get-NativeDirectChildrenById $outerHandle 1148"
        )
        edit = fallback.index(
            "Get-NativeDirectChildrenById $comboHandle 1148"
        )
        label = fallback.index(
            "Get-NativeDirectChildrenById $dialogHandle 1090"
        )
        bind = fallback.index('Kind = "native_nested_1148"')
        final_assert = fallback.index("Assert-NativeNested1148Binding")
        self.assertLess(outer, combo)
        self.assertLess(combo, edit)
        self.assertLess(edit, label)
        self.assertLess(label, bind)
        self.assertLess(bind, final_assert)
        self.assertEqual(fallback.count("_native_control_ambiguous"), 3)
        self.assertEqual(fallback.count("_native_label_ambiguous"), 1)
        self.assertGreaterEqual(fallback.count(".Count -eq 0) { return $null }"), 4)
        self.assertNotIn(' 1001 ', fallback)
        self.assertNotIn(' 1152 ', fallback)
        self.assertNotIn("Find-DescendantsById", fallback)
        for mutation in (
            "PostMessage",
            "TypeFocusedText",
            "Restore-Foreground",
            "Invoke-PhysicalMouseClickAtScreenPoint",
        ):
            self.assertNotIn(mutation, fallback)
            self.assertNotIn(mutation, exact_assert)

        binding_start = source.index("function Get-FileDialogFileNameBinding(")
        binding_end = source.index("\nfunction ", binding_start + 1)
        binding = source[binding_start:binding_end]
        fallback_call = binding.index("Get-ExactNativeFileDialogFileNameBinding")
        unavailable = binding.index(
            'Stop-Adapter ("{0}_control_unavailable" -f $FailureCode)',
            fallback_call,
        )
        self.assertLess(fallback_call, unavailable)

        native_button_start = source.index("function Invoke-ExactNativeDialogButton(")
        native_button_end = source.index("\nfunction ", native_button_start + 1)
        native_button = source[native_button_start:native_button_end]
        for required in (
            "Get-NativeDirectChildrenById $dialogHandle $ControlId",
            "$buttons.Count -gt 1",
            "$buttons.Count -eq 0",
            "IsWindow($buttonHandle)",
            "IsWindowVisible($buttonHandle)",
            "IsWindowEnabled($buttonHandle)",
            "Get-WindowOwner $buttonHandle",
            '(Get-WindowClass $buttonHandle) -ne "Button"',
            "GetDlgCtrlID($buttonHandle) -ne $ControlId",
            "GetParent($buttonHandle) -ne $dialogHandle",
            "Test-NativeAllowedName (Read-Win32Text $buttonHandle)",
            "PostMessage",
            "BM_CLICK",
        ):
            self.assertIn(required, native_button)
        self.assertNotIn("Find-DescendantsById", native_button)
        action_assert = native_button.index("Assert-NativeNested1148Binding")
        button_lookup = native_button.index(
            "Get-NativeDirectChildrenById $dialogHandle $ControlId"
        )
        button_post = native_button.index("PostMessage")
        self.assertLess(action_assert, button_lookup)
        self.assertLess(button_lookup, button_post)

    def test_native_file_dialog_fallback_avoids_laggy_uia_semantics(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        fallback_start = source.index(
            "function Get-ExactNativeFileDialogFileNameBinding("
        )
        fallback_end = source.index("\nfunction ", fallback_start + 1)
        fallback = source[fallback_start:fallback_end]
        for prohibited in (
            ".Current.Name",
            ".Current.AutomationId",
            ".Current.ControlType",
            ".Current.IsOffscreen",
            ".Current.IsEnabled",
        ):
            self.assertNotIn(prohibited, fallback)
        self.assertNotIn("AutomationElement]::FromHandle", fallback)
        self.assertIn("Edit = $null", fallback)
        self.assertIn("FileNameHost = $null", fallback)
        self.assertIn("FileNameOuterHost = $null", fallback)
        self.assertIn("FileNameLabel = $null", fallback)

        setter_start = source.index("function Set-FileDialogFileNameExact(")
        setter_end = source.index("\nfunction ", setter_start + 1)
        setter = source[setter_start:setter_end]
        native_pre_start = setter.index(
            '} elseif ($bindingKind -eq "native_nested_1148") {'
        )
        native_pre_end = setter.index("Restore-Foreground", native_pre_start)
        native_pre = setter[native_pre_start:native_pre_end]
        self.assertIn("Assert-NativeNested1148Binding", native_pre)
        for prohibited in (
            ".Current.Name",
            ".Current.AutomationId",
            ".Current.ControlType",
            ".Current.IsOffscreen",
            ".Current.IsEnabled",
        ):
            self.assertNotIn(prohibited, native_pre)

        click = setter.index("Invoke-PhysicalMouseClickAtScreenPoint")
        native_focus = setter.index(
            '$bindingKind -eq "native_nested_1148"',
            click,
        )
        focused_native = setter.index("GetFocusedWindowFor($editHandle)", native_focus)
        focused_uia = setter.index("AutomationElement]::FocusedElement", focused_native)
        pre_keyboard_assert = setter.index(
            "Assert-NativeNested1148Binding",
            focused_uia,
        )
        selection = setter.index(
            "Select-AllFileDialogEditTextExact",
            pre_keyboard_assert,
        )
        typing_boundary = setter.index(
            "Assert-FileDialogEditMutationBoundary",
            selection,
        )
        keyboard = setter.index("TypeFocusedText($Value)", typing_boundary)
        precommit_wait = setter.index(
            "Wait-ExactFileDialogPreCommitValue",
            keyboard,
        )
        commit = setter.index("SendVirtualKeyPress", precommit_wait)
        post_commit_assert = setter.index(
            "Assert-NativeNested1148Binding",
            commit,
        )
        boundary_start = source.index("function Assert-FileDialogEditMutationBoundary(")
        boundary_end = source.index("\nfunction ", boundary_start + 1)
        boundary = source[boundary_start:boundary_end]
        self.assertIn("Assert-NativeNested1148Binding", boundary)
        self.assertIn("GetFocusedWindowFor($editHandle)", boundary)
        self.assertLess(click, native_focus)
        self.assertLess(native_focus, focused_native)
        self.assertLess(focused_native, focused_uia)
        self.assertLess(focused_uia, pre_keyboard_assert)
        self.assertLess(pre_keyboard_assert, selection)
        self.assertLess(selection, typing_boundary)
        self.assertLess(typing_boundary, keyboard)
        self.assertLess(keyboard, precommit_wait)
        self.assertLess(precommit_wait, commit)
        self.assertLess(commit, post_commit_assert)
        self.assertIn(
            '$bindingKind -notin @("nested_1148", "native_nested_1148")',
            setter,
        )

    def test_post_tab_basename_requires_exact_folder_and_target_snapshot(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        self.assertIn("CDM_GETFOLDERPATH = 0x0466", source)

        folder_start = source.index("function Read-CommonDialogFolderPathExact(")
        folder_end = source.index("\nfunction ", folder_start + 1)
        folder = source[folder_start:folder_end]
        for required in (
            "IsWindow($DialogHandle)",
            "IsWindowVisible($DialogHandle)",
            "IsWindowEnabled($DialogHandle)",
            "Get-WindowOwner $DialogHandle",
            '(Get-WindowClass $DialogHandle) -ne "#32770"',
            "SendMessageTimeout",
            "[MetafxVisibleNative]::CDM_GETFOLDERPATH",
            "$reportedLength -le 0",
            "$reportedLength -ge $capacity",
            "[System.IO.Path]::IsPathRooted($observed)",
            "[System.IO.Directory]::Exists($full)",
        ):
            self.assertIn(required, folder)

        setter_start = source.index("function Set-FileDialogFileNameExact(")
        setter_end = source.index("\nfunction ", setter_start + 1)
        setter = source[setter_start:setter_end]
        snapshot = setter.index(
            "[bool]$targetExistedBefore = [System.IO.File]::Exists($Value)"
        )
        snapshot_hash = setter.index(
            "$targetSha256Before = Get-FileSha256Hex $Value",
            snapshot,
        )
        first_mutation = setter.index("Restore-Foreground")
        keyboard = setter.index("TypeFocusedText($Value)")
        precommit_wait = setter.index(
            "Wait-ExactFileDialogPreCommitValue",
            keyboard,
        )
        commit = setter.index("SendVirtualKeyPress", precommit_wait)
        postcommit_read = setter.index(
            "$editNativeValue = Read-Win32TextExact $editHandle",
            commit,
        )
        snapshot_verify = setter.index(
            '(Get-FileSha256Hex $Value),',
            postcommit_read,
        )
        full_path_gate = setter.index(
            "$postCommitIsExactFullPath = [string]::Equals(",
            snapshot_verify,
        )
        basename_gate = setter.index(
            "$postCommitIsExactBasename = $false",
            full_path_gate,
        )
        exact_basename = setter.index(
            "$expectedFileName,",
            basename_gate,
        )
        folder_readback = setter.index(
            "Read-CommonDialogFolderPathExact",
            exact_basename,
        )
        exact_folder = setter.index(
            "$postCommitIsExactBasename = Test-SamePath",
            folder_readback,
        )
        mismatch = setter.index(
            'Stop-Adapter ("{0}_edit_readback_mismatch" -f $FailureCode)',
            exact_folder,
        )
        self.assertLess(snapshot, snapshot_hash)
        self.assertLess(snapshot_hash, first_mutation)
        self.assertLess(keyboard, precommit_wait)
        self.assertLess(precommit_wait, commit)
        self.assertLess(commit, postcommit_read)
        self.assertLess(postcommit_read, snapshot_verify)
        self.assertLess(snapshot_verify, full_path_gate)
        self.assertLess(full_path_gate, basename_gate)
        self.assertLess(basename_gate, exact_basename)
        self.assertLess(exact_basename, folder_readback)
        self.assertLess(folder_readback, exact_folder)
        self.assertLess(exact_folder, mismatch)
        self.assertIn(
            '[System.IO.File]::Exists($Value) -or\n'
            '        [System.IO.Directory]::Exists($Value)',
            setter,
        )
        self.assertIn('"{0}_target_snapshot_changed"', setter)
        self.assertNotIn("Trim('\\\"')", setter)
        self.assertNotIn('Replace("\\\"", "")', setter)

    def test_native_edit_existing_wildcard_is_selected_before_unicode_typing(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        self.assertIn("public const int EM_GETSEL = 0x00B0;", source)
        self.assertIn("public const int EM_SETSEL = 0x00B1;", source)

        typing_start = source.index("public static bool TypeFocusedText(string value)")
        typing_end = source.index("\n    public static ", typing_start + 1)
        typing = source[typing_start:typing_end]
        self.assertIn("value.Length * 2", typing)
        self.assertIn("UnicodeKey(character, 0)", typing)
        self.assertIn("UnicodeKey(character, KEYEVENTF_KEYUP)", typing)
        self.assertIn("SendKeyboardInput", typing)
        self.assertNotIn("VK_CONTROL", typing)
        self.assertNotIn("VK_A", typing)
        self.assertNotIn("EM_SETSEL", typing)
        self.assertNotIn("EM_GETSEL", typing)

        reader_start = source.index("function Read-Win32TextExact(")
        reader_end = source.index("\nfunction ", reader_start + 1)
        reader = source[reader_start:reader_end]
        self.assertIn("WM_GETTEXTLENGTH", reader)
        self.assertIn("WM_GETTEXT", reader)
        self.assertIn("$length -lt 0", reader)
        self.assertNotIn("$length -le 0", reader)
        self.assertIn("return $buffer.ToString()", reader)
        self.assertNotIn(".Trim()", reader)

        selection_start = source.index("function Select-AllFileDialogEditTextExact(")
        selection_end = source.index("\nfunction ", selection_start + 1)
        selection = source[selection_start:selection_end]
        self.assertIn("[int]$initialLength = $initialValue.Length", selection)
        self.assertNotIn('"*.set"', selection)
        first_boundary = selection.index("Assert-FileDialogEditMutationBoundary")
        initial_read = selection.index("Read-Win32TextExact $editHandle", first_boundary)
        second_boundary = selection.index(
            "Assert-FileDialogEditMutationBoundary",
            initial_read,
        )
        set_selection = selection.index("[MetafxVisibleNative]::EM_SETSEL", second_boundary)
        third_boundary = selection.index(
            "Assert-FileDialogEditMutationBoundary",
            set_selection,
        )
        get_selection = selection.index("[MetafxVisibleNative]::EM_GETSEL", third_boundary)
        selection_start_decode = selection.index(
            "$selectionStart =",
            get_selection,
        )
        selection_end_decode = selection.index(
            "$selectionEnd =",
            selection_start_decode,
        )
        selection_minimum = selection.index(
            "$selectionMinimum =",
            selection_end_decode,
        )
        selection_maximum = selection.index(
            "$selectionMaximum =",
            selection_minimum,
        )
        fourth_boundary = selection.index(
            "Assert-FileDialogEditMutationBoundary",
            selection_maximum,
        )
        exact_selection = selection.index(
            "$selectionStart -eq 0xFFFF",
            fourth_boundary,
        )
        self.assertLess(first_boundary, initial_read)
        self.assertLess(initial_read, second_boundary)
        self.assertLess(second_boundary, set_selection)
        self.assertLess(set_selection, third_boundary)
        self.assertLess(third_boundary, get_selection)
        self.assertLess(get_selection, selection_start_decode)
        self.assertLess(selection_start_decode, selection_end_decode)
        self.assertLess(selection_end_decode, selection_minimum)
        self.assertLess(selection_minimum, selection_maximum)
        self.assertLess(selection_maximum, fourth_boundary)
        self.assertLess(fourth_boundary, exact_selection)
        for required in (
            "[IntPtr]::Zero,\n        [IntPtr](-1)",
            "SMTO_ABORTIFHUNG",
            "$selectionCall -eq [IntPtr]::Zero",
            '"{0}_selection_message_timeout"',
            "$packedSelection -band 0xFFFF",
            "($packedSelection -shr 16) -band 0xFFFF",
            "[Math]::Min($selectionStart, $selectionEnd)",
            "[Math]::Max($selectionStart, $selectionEnd)",
            "$selectionEnd -eq 0xFFFF",
            "$selectionStart -gt $initialLength",
            "$selectionEnd -gt $initialLength",
            "$selectionMinimum -ne 0",
            "$selectionMaximum -ne $initialLength",
            "$initialLength",
            "Get-Sha256Hex $initialBytes",
            ".Substring(0, 12)",
            "_cedit",
            "$diagnosticCode.Length -gt 80",
            "^[a-z0-9_]{3,80}$",
            '"{0}_selection_not_applied"',
        ):
            self.assertIn(required, selection)
        self.assertNotIn("$initialLength -le 0", selection)
        self.assertNotIn("$initialLength -eq 0", selection)
        selection_cases = (
            (0, 5, 5, True),
            (5, 0, 5, True),
            (1, 5, 5, False),
            (0, 4, 5, False),
            (0, 0, 5, False),
            (0, 0, 0, True),
            (6, 0, 5, False),
            (0xFFFF, 0, 5, False),
        )
        for start, end, initial_length, expected in selection_cases:
            with self.subTest(
                start=start,
                end=end,
                initial_length=initial_length,
            ):
                accepted = (
                    start != 0xFFFF
                    and end != 0xFFFF
                    and start <= initial_length
                    and end <= initial_length
                    and min(start, end) == 0
                    and max(start, end) == initial_length
                )
                self.assertEqual(accepted, expected)
        for forbidden in (
            "TypeFocusedText",
            "SendVirtualKeyPress",
            "VK_TAB",
            "Invoke-ExactButton",
            "Invoke-ExactNativeDialogButton",
            "PostMessage",
            "BM_CLICK",
            "Start Strategy Tester",
            "WM_SETTEXT",
            "$initialValue,",
        ):
            self.assertNotIn(forbidden, selection)

        setter_start = source.index("function Set-FileDialogFileNameExact(")
        setter_end = source.index("\nfunction ", setter_start + 1)
        setter = source[setter_start:setter_end]
        selection_call = setter.index("Select-AllFileDialogEditTextExact")
        typing_boundary = setter.index(
            "Assert-FileDialogEditMutationBoundary",
            selection_call,
        )
        typing_call = setter.index("TypeFocusedText($Value)", typing_boundary)
        exact_wait = setter.index("Wait-ExactFileDialogPreCommitValue", typing_call)
        commit = setter.index("SendVirtualKeyPress", exact_wait)
        self.assertLess(selection_call, typing_boundary)
        self.assertLess(typing_boundary, typing_call)
        self.assertLess(typing_call, exact_wait)
        self.assertLess(exact_wait, commit)
        self.assertNotIn("ReplaceFocusedText", setter)

    def test_precommit_readback_waits_for_exact_full_path_and_fails_closed(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        wait_start = source.index("function Wait-ExactFileDialogPreCommitValue(")
        wait_end = source.index("\nfunction ", wait_start + 1)
        wait = source[wait_start:wait_end]
        boundary_start = source.index("function Assert-FileDialogEditMutationBoundary(")
        boundary_end = source.index("\nfunction ", boundary_start + 1)
        boundary = source[boundary_start:boundary_end]

        deadline = wait.index("[DateTime]::UtcNow.AddSeconds(5)")
        loop = wait.index("do {", deadline)
        boundary_call = wait.index("Assert-FileDialogEditMutationBoundary", loop)
        stage = wait.index('"precommit"', boundary_call)
        readback = wait.index("Read-Win32TextExact $editHandle", stage)
        exact = wait.index("$ExpectedValue,", readback)
        success = wait.index("return", exact)
        deadline_gate = wait.index("[DateTime]::UtcNow -ge $deadline", success)
        delay = wait.index("Start-Sleep -Milliseconds 50", deadline_gate)
        timeout_diagnostic = wait.index("$lastObserved.Length", delay)
        self.assertLess(loop, boundary_call)
        self.assertLess(boundary_call, stage)
        self.assertLess(stage, readback)
        self.assertLess(readback, exact)
        self.assertLess(exact, success)
        self.assertLess(success, deadline_gate)
        self.assertLess(deadline_gate, delay)
        self.assertLess(delay, timeout_diagnostic)
        self.assertNotIn("Stop-Adapter", wait[readback:delay])

        for required in (
            "IsWindow($dialogHandle)",
            "IsWindowVisible($dialogHandle)",
            "IsWindowEnabled($dialogHandle)",
            "Get-WindowOwner $dialogHandle",
            '(Get-WindowClass $dialogHandle) -ne "#32770"',
            "IsWindow($editHandle)",
            "IsWindowVisible($editHandle)",
            "IsWindowEnabled($editHandle)",
            "Get-WindowOwner $editHandle",
            '(Get-WindowClass $editHandle) -ne "Edit"',
            "Test-NativeWindowDescendantOf $editHandle $dialogHandle",
            '"{0}_{1}_binding_changed"',
            '"{0}_{1}_focus_changed"',
            "Assert-NativeNested1148Binding",
            "GetFocusedWindowFor($editHandle)",
            "[System.Windows.Automation.AutomationElement]::FocusedElement",
            "Test-ForegroundWindowBinding",
            "Assert-FileDialogTargetSnapshot",
        ):
            self.assertIn(required, boundary)
        for required in (
            "[System.StringComparison]::OrdinalIgnoreCase",
            "$ExpectedValue.Length",
            "Get-Sha256Hex $observedBytes",
            ".Substring(0, 12)",
            "_cedit_timeout",
            "$diagnosticCode.Length -gt 80",
            "^[a-z0-9_]{3,80}$",
            '"{0}_precommit_readback_timeout"',
        ):
            self.assertIn(required, wait)
        for forbidden in (
            "SendVirtualKeyPress",
            "Invoke-ExactButton",
            "Invoke-ExactNativeDialogButton",
            "PostMessage",
            "BM_CLICK",
            "VK_TAB",
            "Start Strategy Tester",
            "Trim('\\\"')",
            'Replace("\\\"", "")',
        ):
            self.assertNotIn(forbidden, wait)

        setter_start = source.index("function Set-FileDialogFileNameExact(")
        setter_end = source.index("\nfunction ", setter_start + 1)
        setter = source[setter_start:setter_end]
        keyboard = setter.index("TypeFocusedText($Value)")
        bounded_wait = setter.index("Wait-ExactFileDialogPreCommitValue", keyboard)
        commit = setter.index("SendVirtualKeyPress", bounded_wait)
        self.assertLess(keyboard, bounded_wait)
        self.assertLess(bounded_wait, commit)
        self.assertNotIn(
            "Start-Sleep -Milliseconds 100",
            setter[keyboard:commit],
        )

    def test_file_dialog_binding_wait_retries_only_exact_unavailable_signal(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        wait_start = source.index("function Wait-FileDialogFileNameBinding(")
        wait_end = source.index("\nfunction ", wait_start + 1)
        wait = source[wait_start:wait_end]

        expected_handle = wait.index(
            "[IntPtr]$expectedDialogHandle = "
            "[IntPtr]$Dialog.Current.NativeWindowHandle"
        )
        expected_pid = wait.index("[int]$expectedProcessId = $ProcessId")
        deadline = wait.index("[DateTime]::UtcNow.AddSeconds(10)")
        rebind = wait.index(
            "[System.Windows.Automation.AutomationElement]::FromHandle("
        )
        native_window = wait.index(
            "[MetafxVisibleNative]::IsWindow($expectedDialogHandle)",
            rebind,
        )
        handle_readback = wait.index(
            "[IntPtr]$freshDialog.Current.NativeWindowHandle "
            "-ne $expectedDialogHandle"
        )
        class_readback = wait.index(
            '[string]$freshDialog.Current.ClassName -ne "#32770"'
        )
        pid_readback = wait.index(
            "[int]$freshDialog.Current.ProcessId -ne $expectedProcessId"
        )
        native_class = wait.index(
            '(Get-WindowClass $expectedDialogHandle) -ne "#32770"',
            pid_readback,
        )
        native_owner = wait.index(
            "(Get-WindowOwner $expectedDialogHandle) -ne $expectedProcessId",
            native_class,
        )
        native_visible = wait.index(
            "[MetafxVisibleNative]::IsWindowVisible($expectedDialogHandle)",
            native_owner,
        )
        offscreen_readback = wait.index(
            "[bool]$freshDialog.Current.IsOffscreen"
        )
        lookup = wait.index("return Get-FileDialogFileNameBinding `")
        fresh_lookup = wait.index("$freshDialog `", lookup)
        pid_lookup = wait.index("$expectedProcessId `", fresh_lookup)
        exact_signal = wait.index(
            '"METAFX_VISIBLE:{0}_control_unavailable" -f $FailureCode'
        )
        exact_compare = wait.index("[System.StringComparison]::Ordinal")
        immediate_rethrow = wait.index("throw", exact_compare)
        bounded_rethrow = wait.index(
            "if ([DateTime]::UtcNow -ge $deadline) { throw }",
            immediate_rethrow,
        )
        sleep = wait.index("Start-Sleep -Milliseconds 100", bounded_rethrow)
        terminal_failure = wait.index(
            'Stop-Adapter ("{0}_control_unavailable" -f $FailureCode)',
            sleep,
        )

        self.assertLess(expected_handle, expected_pid)
        self.assertLess(expected_pid, deadline)
        self.assertLess(deadline, rebind)
        self.assertLess(rebind, native_window)
        self.assertLess(native_window, handle_readback)
        self.assertLess(handle_readback, class_readback)
        self.assertLess(class_readback, pid_readback)
        self.assertLess(pid_readback, native_class)
        self.assertLess(native_class, native_owner)
        self.assertLess(native_owner, native_visible)
        self.assertLess(native_visible, offscreen_readback)
        self.assertLess(offscreen_readback, lookup)
        self.assertLess(lookup, fresh_lookup)
        self.assertLess(fresh_lookup, pid_lookup)
        self.assertLess(exact_signal, exact_compare)
        self.assertLess(exact_compare, immediate_rethrow)
        self.assertLess(immediate_rethrow, bounded_rethrow)
        self.assertLess(bounded_rethrow, sleep)
        self.assertLess(sleep, terminal_failure)
        self.assertNotIn("control_ambiguous", wait)
        self.assertNotIn("Restore-Foreground", wait)
        self.assertNotIn("Invoke-", wait)
        self.assertNotIn(
            "Get-FileDialogFileNameBinding $Dialog $ProcessId",
            wait,
        )

    def test_distributed_powershell_adapter_is_ascii_and_ps51_parseable(self) -> None:
        source_bytes = POWERSHELL_PATH.read_bytes()
        self.assertTrue(
            source_bytes.isascii(),
            "The no-BOM distributed adapter must remain ASCII-safe for Windows PowerShell 5.1",
        )
        if os.name != "nt":
            return
        powershell = shutil.which("powershell.exe")
        if powershell is None:
            self.skipTest("Windows PowerShell 5.1 is unavailable")
        escaped_path = str(POWERSHELL_PATH).replace("'", "''")
        command = (
            "$tokens=$null;$errors=$null;"
            "[void][System.Management.Automation.Language.Parser]::ParseFile("
            f"'{escaped_path}',[ref]$tokens,[ref]$errors);"
            "if($errors.Count){$errors|ForEach-Object{$_.ToString()}|Write-Error;exit 1}"
        )
        completed = subprocess.run(
            [powershell, "-NoLogo", "-NoProfile", "-Command", command],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            completed.stdout + completed.stderr,
        )

    def test_file_dialog_failure_cleanup_revalidates_exact_modal(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        helper_start = source.index(
            "function Close-ExactOwnedFileDialogAfterFailure("
        )
        helper_end = source.index("\nfunction ", helper_start + 1)
        helper = source[helper_start:helper_end]
        for required in (
            "$ExpectedDialogHandle",
            'ClassName -ne "#32770"',
            "Get-WindowOwner $ExpectedDialogHandle",
            'Get-WindowClass $ExpectedDialogHandle) -ne "#32770"',
            'Find-DescendantsById $Dialog "2"',
            'ClassName -eq "Button"',
            "GetDlgCtrlID",
            "PostMessage",
            "BM_CLICK",
            "IsWindowVisible",
        ):
            self.assertIn(required, helper)

        save_start = source.index("function Save-TesterReport(")
        save_end = source.index("\n$request = $null", save_start + 1)
        save = source[save_start:save_end]
        self.assertIn("Close-ExactOwnedFileDialogAfterFailure", save)
        self.assertIn("throw", save)
        self.assertNotIn("throw $originalFailure", save)

    def test_metaeditor_owner_data_compile_fallback_has_exact_fail_closed_shape(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        helper_start = source.index("function Get-MetaEditorCompileToolboxState(")
        reader_start = source.index("function Read-MetaEditorCompileResult(")
        reader_end = source.index("\nfunction ", reader_start + 1)
        contract = source[helper_start:reader_end]

        for required in (
            "SysListView32",
            '"10065"',
            "LVM_GETITEMCOUNT",
            "ControlType]::HeaderItem",
            "ControlType]::DataItem",
            '"Description"',
            '"File"',
            '"Line"',
            '"Column"',
            "Current.ProcessId",
            "Current.IsOffscreen",
            "NativeWindowHandle",
            "Get-WindowOwner",
            "Get-MetaEditorCompileToolboxState",
            'Stop-Adapter "metaeditor_compile_diagnostics_present"',
            'Stop-Adapter "metaeditor_compile_result_unreadable"',
        ):
            self.assertIn(required, contract)

        self.assertRegex(
            contract,
            r"(?s)\.Count\s*-ne\s*4.{0,500}metaeditor_compile_result_unreadable",
        )
        self.assertRegex(
            contract,
            r"(?s)-gt\s*2.{0,500}metaeditor_compile_diagnostics_present",
        )
        self.assertRegex(
            contract,
            r"(?s)-lt\s*2.{0,500}metaeditor_compile_result_unreadable",
        )
        self.assertRegex(
            contract,
            r"(?is)(?:stable|previous).{0,500}Start-Sleep|Start-Sleep.{0,500}(?:stable|previous)",
        )

    def test_compile_acceptance_requires_fresh_binary_then_persisted_screenshot(self) -> None:
        source = POWERSHELL_PATH.read_text(encoding="utf-8")
        compile_start = source.index('if ($request.action -eq "compile")')
        compile_end = source.index(
            'if ($request.action -eq "backtest")',
            compile_start + 1,
        )
        compile_branch = source[compile_start:compile_end]

        fresh_guard = compile_branch.index(
            'if (-not $freshBinary) { Stop-Adapter "visible_compile_binary_not_fresh" }'
        )
        result_reader = compile_branch.index("Read-MetaEditorCompileResult")
        screenshot = compile_branch.index("Save-WindowPng $editor.Window $screenshotPath")
        success_result = compile_branch.index("Write-JsonResult $result 0")

        self.assertLess(fresh_guard, result_reader)
        self.assertLess(result_reader, screenshot)
        self.assertLess(screenshot, success_result)


if __name__ == "__main__":
    unittest.main()
