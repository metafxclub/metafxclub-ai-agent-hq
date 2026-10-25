from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
LOCAL_RUNNER = ROOT / "backend" / "local-runner"
MODULE_PATH = ROOT / "backend" / "local-runner" / "hq_backend" / "ea" / "ea_factory_visible_terminal_mt5.py"
PS_PATH = MODULE_PATH.with_suffix(".ps1")
INTERACTIVE_UI_TEST_ENV = "METAFX_RUN_INTERACTIVE_UI_TESTS"


def interactive_ui_tests_enabled(environment: dict[str, str] | None = None) -> bool:
    values = os.environ if environment is None else environment
    return values.get(INTERACTIVE_UI_TEST_ENV) == "1"


def require_interactive_ui_test(test_case: unittest.TestCase) -> None:
    if not interactive_ui_tests_enabled():
        test_case.skipTest(
            "Interactive Windows UI harness is opt-in; set "
            f"{INTERACTIVE_UI_TEST_ENV}=1 to run it"
        )


def load_module():
    spec = importlib.util.spec_from_file_location(
        "metafx_ea_factory_visible_terminal_mt5_test", MODULE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    runner = str(LOCAL_RUNNER)
    added = runner not in sys.path
    if added:
        sys.path.insert(0, runner)
    try:
        spec.loader.exec_module(module)
    finally:
        if added:
            sys.path.remove(runner)
    return module


mt5 = load_module()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def png_bytes() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + (b"visible-mt5-evidence" * 80)


def native_mt5_report_html(
    *,
    expert: str = "Strategy",
    symbol: str = "EURUSD",
    period: str = "H1",
    inputs: str = "RiskPercent=1; MaxTrades=1; UseGuard=true",
    trades: int = 2,
    long_trades: int = 1,
    short_trades: int = 1,
    total_deals: int | None = None,
    extra_head: str = "",
    extra_main_rows: str = "",
    secondary_tables: str = "",
) -> str:
    if total_deals is None:
        total_deals = trades * 2
    return f"""<html><head><title>Strategy Tester Report</title>{extra_head}</head>
    <body><table>
    <tr><td>Strategy Tester Report</td></tr>
    <tr><td>RoboForex-Pro (Build 6230)</td></tr>
    <tr><td>Settings</td></tr>
    <tr><td>Expert:</td><td>{expert}</td></tr>
    <tr><td>Symbol:</td><td>{symbol}</td></tr>
    <tr><td>Period:</td><td>{period}</td></tr>
    <tr><td>Inputs:</td><td>{inputs}</td></tr>
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
    <tr><td>Total Trades:</td><td>{trades}</td>
        <td>Short Trades (won %):</td><td>{short_trades} (0.00%)</td>
        <td>Long Trades (won %):</td><td>{long_trades} (0.00%)</td></tr>
    <tr><td>Total Deals:</td><td>{total_deals}</td></tr>
    {extra_main_rows}</table>{secondary_tables}</body></html>"""


def completion_evidence(
    *,
    operation_id: str,
    expert_file_name: str,
    expert_ui_path: str,
    deployed_expert_sha256: str,
    symbol: str,
    period: str,
    optimize: bool,
    pass_count: int | None,
) -> dict:
    observed_at = datetime.now(timezone.utc).isoformat()
    marker = "optimization_finished" if optimize else "thread_finished"
    start_log_path_sha256 = "a" * 64
    completion_log_path_sha256 = "a" * 64
    start_source_sha256 = sha256_bytes(b"Tester")
    completion_source_sha256 = (
        start_source_sha256 if optimize else sha256_bytes(b"Core 1")
    )
    core_source_sha256s = [sha256_bytes(b"Core 1")]
    core_sources_sha256 = sha256_bytes(
        "\n".join(core_source_sha256s).encode("utf-8")
    )
    core_thread_identity_sha256s = [
        sha256_bytes(
            f"{completion_log_path_sha256}\n{core_source_sha256s[0]}".encode(
                "utf-8"
            )
        )
    ]
    core_thread_identities_sha256 = sha256_bytes(
        "\n".join(core_thread_identity_sha256s).encode("utf-8")
    )
    start_line_sha256 = "d" * 64
    completion_line_sha256 = "e" * 64
    start_line_ordinal = 10
    completion_line_ordinal = 20
    expert_ui_path_sha256 = sha256_bytes(expert_ui_path.encode("utf-8"))
    expert_symbol_period_sha256 = sha256_bytes(
        "\n".join(
            (
                expert_file_name,
                deployed_expert_sha256,
                expert_ui_path_sha256,
                symbol,
                period,
            )
        ).encode("utf-8")
    )
    log_identity_sha256 = sha256_bytes(
        "\n".join(
            (
                start_log_path_sha256,
                completion_log_path_sha256,
                start_source_sha256,
                completion_source_sha256,
            )
        ).encode("utf-8")
    )
    execution_thread_identity_sha256 = sha256_bytes(
        (
            f"{log_identity_sha256}\n{start_line_ordinal}\n"
            f"{completion_line_ordinal}\n{core_thread_identities_sha256}"
        ).encode("utf-8")
    )
    run_identity_sha256 = mt5._tester_completion_identity_digest(
        operation_id=operation_id,
        completion_marker=marker,
        expert_symbol_period_sha256=expert_symbol_period_sha256,
        log_identity_sha256=log_identity_sha256,
        core_sources_sha256=core_sources_sha256,
        core_thread_identities_sha256=core_thread_identities_sha256,
        start_line_sha256=start_line_sha256,
        completion_line_sha256=completion_line_sha256,
        start_line_ordinal=start_line_ordinal,
        completion_line_ordinal=completion_line_ordinal,
        completion_pass_count=pass_count,
    )
    return {
        "schemaVersion": mt5.TESTER_COMPLETION_EVIDENCE_SCHEMA,
        "source": "fresh_tester_log_completion",
        "boundaryCreatedAt": observed_at,
        "runStartedAt": observed_at,
        "runCompletedAt": observed_at,
        "startLineSha256": start_line_sha256,
        "completionLineSha256": completion_line_sha256,
        "completionMarker": marker,
        "startLogPathSha256": start_log_path_sha256,
        "completionLogPathSha256": completion_log_path_sha256,
        "startSourceSha256": start_source_sha256,
        "completionSourceSha256": completion_source_sha256,
        "coreSourceCount": 1,
        "coreSourceSha256s": core_source_sha256s,
        "coreSourcesSha256": core_sources_sha256,
        "coreThreadCount": 1,
        "coreThreadIdentitySha256s": core_thread_identity_sha256s,
        "coreThreadIdentitiesSha256": core_thread_identities_sha256,
        "startLineOrdinal": start_line_ordinal,
        "completionLineOrdinal": completion_line_ordinal,
        "expertUiPathSha256": expert_ui_path_sha256,
        "deployedExpertSha256": deployed_expert_sha256,
        "expertSymbolPeriodSha256": expert_symbol_period_sha256,
        "logIdentitySha256": log_identity_sha256,
        "executionThreadIdentitySha256": execution_thread_identity_sha256,
        "runIdentitySha256": run_identity_sha256,
        "completionPassCount": pass_count,
        "coreDisconnectObserved": False,
        "verified": True,
    }


def strategy_execution_profile(source_digest: str) -> dict:
    core = {
        "schemaVersion": mt5.STRATEGY_EXECUTION_PROFILE_SCHEMA,
        "profileId": mt5.CERTIFIED_EMA_SMOKE_PROFILE_ID,
        "sourceDigest": source_digest,
        "proofRequired": True,
        "fastPeriod": 10,
        "slowPeriod": 60,
        "previousShift": 2,
        "currentShift": 1,
        "requiredDirections": ["BUY", "SELL"],
    }
    return {
        **core,
        "profileDigest": sha256_bytes(mt5._canonical_json(core)),
    }


def strategy_execution_proof(
    profile: dict,
    *,
    operation_id: str = "ea-visible-" + ("1" * 24),
    symbol: str = "EURUSD",
    period: str = "H1",
) -> dict:
    rows = [
        {
            "seq": 1,
            "direction": "BUY",
            "closedBarTime": 1_700_000_000,
            "fast2": 1.0,
            "fast1": 2.0,
            "slow2": 1.0,
            "slow1": 1.5,
            "deal": 1001,
        },
        {
            "seq": 2,
            "direction": "SELL",
            "closedBarTime": 1_700_003_600,
            "fast2": 2.0,
            "fast1": 1.0,
            "slow2": 2.0,
            "slow1": 1.5,
            "deal": 1002,
        },
    ]
    line_hashes = [sha256_bytes(f"event-{index}".encode()) for index in range(7)]
    sequences = []
    for index, row in enumerate(rows):
        sequences.append({
            **row,
            "signalLineSha256": line_hashes[index * 3],
            "pendingLineSha256": line_hashes[index * 3 + 1],
            "entryLineSha256": line_hashes[index * 3 + 2],
        })
    return {
        "schemaVersion": mt5.STRATEGY_EXECUTION_PROOF_SCHEMA,
        "profileId": profile["profileId"],
        "sourceDigest": profile["sourceDigest"],
        "operationId": operation_id,
        "symbol": symbol,
        "period": period,
        "eventCount": 7,
        "signalCount": 2,
        "entryCount": 2,
        "rejectedCount": 0,
        "orphanCount": 0,
        "pendingCount": 0,
        "dataUnavailableCount": 0,
        "buySignalCount": 1,
        "sellSignalCount": 1,
        "buyEntryCount": 1,
        "sellEntryCount": 1,
        "sequences": sequences,
        "telemetryLineSha256s": line_hashes,
        "telemetryDigest": sha256_bytes("\n".join(line_hashes).encode()),
        "finalLineSha256": line_hashes[-1],
        "verified": True,
    }


def optimization_spreadsheetml(
    rows: list[tuple[object, object, object, object, object]],
    *,
    prefixed: bool = False,
    title: str = "SampleEA EURUSD,H1",
) -> str:
    ss = "ss:" if prefixed else ""
    workbook = f"{ss}Workbook"
    namespace = (
        'xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"'
        if prefixed
        else 'xmlns="urn:schemas-microsoft-com:office:spreadsheet" '
        'xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"'
    )
    header = ("Pass", "Result", "Profit", "Trades", "RiskPercent")
    header_cells = "".join(
        f'<{ss}Cell><{ss}Data ss:Type="String">{value}</{ss}Data></{ss}Cell>'
        for value in header
    )
    data_rows = []
    for row in rows:
        cells = "".join(
            f'<{ss}Cell><{ss}Data ss:Type="Number">{value}</{ss}Data></{ss}Cell>'
            for value in row
        )
        data_rows.append(f"<{ss}Row>{cells}</{ss}Row>")
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f"<{workbook} {namespace} xmlns:o=\"urn:schemas-microsoft-com:office:office\">"
        f"<o:DocumentProperties><o:Title>{title}</o:Title>"
        "<o:Author>MetaQuotes Ltd.</o:Author>"
        "<o:Company>Copyright 2000-2026, MetaQuotes Ltd.</o:Company>"
        "</o:DocumentProperties>"
        f'<{ss}Worksheet ss:Name="Tester Optimizator Results"><{ss}Table>'
        f"<{ss}Row>{header_cells}</{ss}Row>"
        + "".join(data_rows)
        + f"</{ss}Table></{ss}Worksheet></{workbook}>"
    )


def typed_optimization_spreadsheetml(
    headers: list[str],
    rows: list[list[tuple[str, object]]],
    *,
    title: str = "SampleEA EURUSD,H1",
) -> str:
    header_cells = "".join(
        f'<Cell><Data ss:Type="String">{value}</Data></Cell>'
        for value in headers
    )
    data_rows = []
    for row in rows:
        cells = "".join(
            f'<Cell><Data ss:Type="{value_type}">{value}</Data></Cell>'
            for value_type, value in row
        )
        data_rows.append(f"<Row>{cells}</Row>")
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" '
        'xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet" '
        'xmlns:o="urn:schemas-microsoft-com:office:office">'
        f"<o:DocumentProperties><o:Title>{title}</o:Title>"
        "<o:Author>MetaQuotes Ltd.</o:Author>"
        "<o:Company>Copyright 2000-2026, MetaQuotes Ltd.</o:Company>"
        "</o:DocumentProperties>"
        '<Worksheet ss:Name="Tester Optimizator Results"><Table>'
        f"<Row>{header_cells}</Row>"
        + "".join(data_rows)
        + "</Table></Worksheet></Workbook>"
    )


def optimization_verifier_context(
    root: Path,
    report: Path,
    *,
    start: str,
    step: str,
    stop: str,
    mode: str = "fast_genetic",
    input_name: str = "RiskPercent",
    value_kind: str = "decimal",
    source_default: str | None = None,
    enum_values: list[str] | None = None,
) -> dict:
    source_default = start if source_default is None else source_default
    enum_values = [] if enum_values is None else enum_values
    set_path = root / "inputs.set"
    set_path.write_text(
        f"{input_name}={source_default}||{start}||{step}||{stop}||Y\n",
        encoding="ascii",
    )
    ranges = [
        {
            "inputName": input_name,
            "start": start,
            "step": step,
            "stop": stop,
            "enabled": True,
        }
    ]
    return {
        "platform": "mt5",
        "optimizationReportPath": report,
        "resolvedTesterSettings": {
            "expertFileName": "SampleEA.ex5",
            "symbol": "EURUSD",
            "period": "H1",
            "useDate": False,
        },
        "optimizationIntent": {
            "setPath": str(set_path),
            "setDigest": sha256_bytes(set_path.read_bytes()),
            "ranges": ranges,
            "rangesDigest": sha256_bytes(mt5._canonical_json(ranges)),
            "mode": mode,
            "inputManifest": {
                "entries": [
                    {
                        "inputName": input_name,
                        "valueKind": value_kind,
                        "setDefault": source_default,
                        "enumValues": enum_values,
                    }
                ]
            },
        },
    }


class FakeVisibleRunner:
    def __init__(self, fixture: "Mt5AdapterFixture") -> None:
        self.fixture = fixture
        self.actions: list[str] = []
        self.payloads: list[dict] = []
        self.fail_after_first_boundary = False
        self.failed_after_boundary = False
        self.fail_after_boundary_before_dispatch = False
        self.failed_before_dispatch = False
        self.expert_catalog_refresh_attempted = False
        self.fail_after_first_refresh_boundary = False
        self.failed_after_refresh_boundary = False
        self.expert_catalog_refresh_dispatch_count = 0
        self.fail_after_result_checkpoint = False
        self.failed_after_result_checkpoint = False
        self.mutate_completed_result_checkpoint = False
        self.fail_after_report_checkpoint = False
        self.failed_after_report_checkpoint = False
        self.fail_compile_before_binary = False
        self.failed_compile_before_binary = False
        self.tester_start_dispatch_count = 0

    def binding(self, stage_id: str) -> dict:
        compile_stage = stage_id == "compile_validate"
        front_path = self.fixture.compiler if compile_stage else self.fixture.terminal
        front_pid = 202 if compile_stage else 101
        front_handle = 20202 if compile_stage else 10101
        return {
            "observedAt": datetime.now(timezone.utc).isoformat(),
            "terminalProcessId": 101,
            "terminalExecutablePath": str(self.fixture.terminal),
            "terminalWindowHandle": 10101,
            "terminalWindowOwnerProcessId": 101,
            "terminalWindowTitle": "MetaTrader 5 - Test Account",
            "terminalWindowClass": "MetaQuotes::MetaTrader::5.00",
            "frontOfficeKind": "metaeditor" if compile_stage else "strategy_tester",
            "frontOfficeProcessId": front_pid,
            "frontOfficeExecutablePath": str(front_path),
            "frontOfficeWindowHandle": front_handle,
            "frontOfficeWindowOwnerProcessId": front_pid,
            "frontOfficeWindowTitle": "MetaEditor 5" if compile_stage else "MetaTrader 5 - Test Account",
            "frontOfficeWindowClass": "MetaEditor::5.00" if compile_stage else "MetaQuotes::MetaTrader::5.00",
            "autoTradingState": True,
        }

    def probe(self, payload: dict) -> dict:
        stage_id = payload.get("stageId")
        return {
            "schemaVersion": mt5.POWERSHELL_RESULT_SCHEMA,
            "ok": True,
            "action": "probe",
            "operationId": payload["operationId"],
            "terminalProbe": {
                "observedAt": datetime.now(timezone.utc).isoformat(),
                "processId": 101,
                "executablePath": str(self.fixture.terminal),
                "windowHandle": 10101,
                "windowOwnerProcessId": 101,
                "windowTitle": "MetaTrader 5 - Test Account",
                "windowClass": "MetaQuotes::MetaTrader::5.00",
            },
            "automationControlsVerified": payload.get("requiredAutomationIds") or {},
            "testerStartState": (
                "Start"
                if stage_id in {"backtest_recheck", "optimize"}
                else None
            ),
        }

    def post_probe(self, payload: dict) -> dict:
        stage_id = payload.get("stageId")
        return {
            "schemaVersion": mt5.POWERSHELL_RESULT_SCHEMA,
            "ok": True,
            "action": "post_probe",
            "operationId": payload["operationId"],
            "terminalProbe": {
                "observedAt": datetime.now(timezone.utc).isoformat(),
                "processId": 101,
                "executablePath": str(self.fixture.terminal),
                "windowHandle": 10101,
                "windowOwnerProcessId": 101,
                "windowTitle": "MetaTrader 5 - Test Account",
                "windowClass": "MetaQuotes::MetaTrader::5.00",
            },
            "testerStartState": "Start",
            "processBinding": self.binding(stage_id),
            "pythonObservedDurationMs": 1,
        }

    def __call__(self, payload: dict, *, response_path: Path, timeout_seconds: int) -> dict:
        del response_path, timeout_seconds
        self.payloads.append(copy.deepcopy(payload))
        action = payload["action"]
        self.actions.append(action)
        if action == "probe":
            return self.probe(payload)
        if action == "post_probe":
            return self.post_probe(payload)
        if action in {"compile", "recover_compile"}:
            if self.fail_compile_before_binary and not self.failed_compile_before_binary:
                self.failed_compile_before_binary = True
                raise RuntimeError("simulated_compile_readiness_failure")
            binary = Path(payload["binaryPath"])
            binary.write_bytes(b"EX5\x00verified")
            Path(payload["screenshotPath"]).write_bytes(png_bytes())
            binding = self.binding("compile_validate")
            return {
                "schemaVersion": mt5.POWERSHELL_RESULT_SCHEMA,
                "ok": True,
                "action": action,
                "operationId": payload["operationId"],
                "compileInvoked": True,
                "recoveryRecompile": action == "recover_compile",
                "exactSourceWindowVerified": True,
                "compileWorkingCopyVerified": True,
                "freshBinaryObserved": True,
                "workingSourceSha256": payload["expectedSourceDigest"],
                "workingBinarySha256": sha256_bytes(binary.read_bytes()),
                "compileResultLine": "Result: 0 errors, 0 warnings",
                "compileResultBeforeSha256": "b" * 64,
                "compileResultAfterSha256": "c" * 64,
                "compileResultRowCount": 1,
                "processBinding": binding,
                "postProcessBinding": dict(binding, observedAt=datetime.now(timezone.utc).isoformat()),
            }
        if action in {
            "backtest",
            "collect_backtest",
            "recover_completed_backtest",
            "recover_collected_backtest",
            "optimize",
            "collect_optimization",
            "recover_completed_optimization",
            "recover_collected_optimization",
        }:
            collecting = action not in {"backtest", "optimize"}
            recovery_state = (
                "in_flight"
                if action in {"collect_backtest", "collect_optimization"}
                else (
                    "completed"
                    if action
                    in {
                        "recover_completed_backtest",
                        "recover_completed_optimization",
                    }
                    else ("collected" if action.startswith("recover_collected_") else "none")
                )
            )
            refresh_boundary_preexisting = False
            if self.expert_catalog_refresh_attempted:
                refresh_boundary = Path(payload["expertCatalogRefreshBoundaryPath"])
                refresh_boundary_preexisting = refresh_boundary.exists()
                if not refresh_boundary.exists():
                    refresh_boundary.write_text(
                        payload["expertCatalogRefreshBoundaryJson"], encoding="utf-8"
                    )
                    self.expert_catalog_refresh_dispatch_count += 1
                    if (
                        self.fail_after_first_refresh_boundary
                        and not self.failed_after_refresh_boundary
                    ):
                        self.failed_after_refresh_boundary = True
                        raise RuntimeError(
                            "simulated_ui_disconnect_after_refresh_boundary"
                        )
            settings_path = Path(payload["settingsScreenshotPath"])
            if not settings_path.exists():
                settings_path.write_bytes(png_bytes())
            if not collecting:
                self.tester_start_dispatch_count += 1
                Path(payload["startBoundaryPath"]).write_text(
                    payload["startBoundaryJson"], encoding="utf-8"
                )
                if (
                    self.fail_after_boundary_before_dispatch
                    and not self.failed_before_dispatch
                ):
                    self.failed_before_dispatch = True
                    raise RuntimeError(
                        "simulated_disconnect_after_post_before_dispatch_receipt"
                    )
                dispatch_payload = {
                    "schemaVersion": "ea-factory-mt5-start-dispatch-v1",
                    "operationId": payload["operationId"],
                    "actionRequestDigest": payload["actionRequestDigest"],
                    "startBoundarySha256": payload["startBoundarySha256"],
                    "confirmedAt": datetime.now(timezone.utc).isoformat(),
                }
                dispatch_path = Path(str(payload["startBoundaryPath"]) + ".dispatch-confirmed")
                dispatch_path.write_bytes(mt5._canonical_json(dispatch_payload))
                if self.fail_after_first_boundary and not self.failed_after_boundary:
                    self.failed_after_boundary = True
                    raise RuntimeError("simulated_ui_disconnect_after_durable_boundary")
            if recovery_state in {"none", "in_flight"}:
                Path(payload["resultScreenshotPath"]).write_bytes(png_bytes())
            optimize = payload["stageId"] == "optimize"
            expert = Path(payload["expertFileName"]).stem
            if optimize:
                title = f"{expert} EURUSD,H1"
                if payload["testerSettings"]["useDate"]:
                    title += " " + str(payload["testerSettings"]["fromDate"]).replace("-", ".")
                    title += "-" + str(payload["testerSettings"]["toDate"]).replace("-", ".")
                if payload["optimizationIntent"]["mode"] == "all_symbols_market_watch":
                    report = typed_optimization_spreadsheetml(
                        ["Pass", "Result", "Profit", "Trades", "Symbol", "RiskPercent"],
                        [
                            [("Number", 1), ("Number", 120.5), ("Number", 120.5), ("Number", 8), ("String", "EURUSD"), ("Number", 1)],
                            [("Number", 2), ("Number", 210), ("Number", 210), ("Number", 12), ("String", "GBPUSD"), ("Number", 1)],
                        ],
                        title=title,
                    )
                else:
                    report = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
                  xmlns:o="urn:schemas-microsoft-com:office:office"
                  xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
                <o:DocumentProperties><o:Title>{title}</o:Title><o:Author>MetaQuotes Ltd.</o:Author>
                <o:Company>Copyright 2000-2026, MetaQuotes Ltd.</o:Company></o:DocumentProperties>
                <Worksheet ss:Name="Tester Optimizator Results"><Table>
                <Row><Cell><Data ss:Type="String">Pass</Data></Cell><Cell><Data ss:Type="String">Result</Data></Cell>
                <Cell><Data ss:Type="String">Profit</Data></Cell><Cell><Data ss:Type="String">Trades</Data></Cell>
                <Cell><Data ss:Type="String">RiskPercent</Data></Cell></Row>
                <Row><Cell><Data ss:Type="Number">1</Data></Cell><Cell><Data ss:Type="Number">120.5</Data></Cell>
                <Cell><Data ss:Type="Number">120.5</Data></Cell><Cell><Data ss:Type="Number">8</Data></Cell>
                <Cell><Data ss:Type="Number">0.5</Data></Cell></Row>
                <Row><Cell><Data ss:Type="Number">2</Data></Cell><Cell><Data ss:Type="Number">210.0</Data></Cell>
                <Cell><Data ss:Type="Number">210.0</Data></Cell><Cell><Data ss:Type="Number">12</Data></Cell>
                <Cell><Data ss:Type="Number">1.0</Data></Cell></Row>
                <Row><Cell><Data ss:Type="Number">3</Data></Cell><Cell><Data ss:Type="Number">315.25</Data></Cell>
                <Cell><Data ss:Type="Number">315.25</Data></Cell><Cell><Data ss:Type="Number">17</Data></Cell>
                <Cell><Data ss:Type="Number">1.5</Data></Cell></Row>
                <Row><Cell><Data ss:Type="Number">4</Data></Cell><Cell><Data ss:Type="Number">390.0</Data></Cell>
                <Cell><Data ss:Type="Number">390.0</Data></Cell><Cell><Data ss:Type="Number">20</Data></Cell>
                <Cell><Data ss:Type="Number">2.0</Data></Cell></Row>
                </Table></Worksheet></Workbook>"""
                baseline_source = Path(payload["optimizationIntent"]["baselinePresetRef"]["path"])
                baseline_readback = Path(payload["baselineInputReadbackSetPath"])
                baseline_readback.write_bytes(baseline_source.read_bytes())
                baseline_readback_digest = sha256_bytes(baseline_readback.read_bytes())
                source_set = Path(payload["optimizationIntent"]["setPath"])
                readback = Path(payload["inputReadbackSetPath"])
                readback.write_bytes(source_set.read_bytes())
                readback_digest = sha256_bytes(readback.read_bytes())
            else:
                report = native_mt5_report_html(expert=expert)
                preset_source = Path(payload["inputPresetRef"]["path"])
                preset_readback = Path(payload["inputPresetReadbackSetPath"])
                preset_readback.write_bytes(preset_source.read_bytes())
                Path(payload["inputPresetScreenshotPath"]).write_bytes(png_bytes())
                preset_readback_digest = sha256_bytes(preset_readback.read_bytes())
                readback_digest = None
                baseline_readback_digest = None
            dispatch_path = Path(str(payload["startBoundaryPath"]) + ".dispatch-confirmed")
            dispatch_digest = sha256_bytes(dispatch_path.read_bytes())
            completion_checkpoint_digest = None
            if optimize:
                cache_root = Path(payload["dataPath"]) / "Tester" / "cache"
                cache_root.mkdir(parents=True, exist_ok=True)
                if payload["testerSettings"]["useDate"]:
                    cache_from = str(payload["testerSettings"]["fromDate"]).replace("-", "")
                    cache_to = str(payload["testerSettings"]["toDate"]).replace("-", "")
                else:
                    cache_from, cache_to = "20200101", "20200102"
                cache_path = cache_root / (
                    f"{expert}.EURUSD.{payload['testerSettings']['period']}."
                    f"{cache_from}.{cache_to}.00.{('A' * 32)}.opt"
                )
                if not cache_path.exists():
                    embedded = "Experts\\" + payload["expertUiPath"] + ".ex5"
                    cache_payload = (
                        "TesterOptCache\0"
                        + expert
                        + "\0"
                        + embedded
                        + "\0EURUSD\0demo (hedging)\0USD\0RiskPercent\0"
                    ).encode("utf-16-le")
                    cache_path.write_bytes(cache_payload + (b"\x00" * max(0, 1024 - len(cache_payload))))
                completion_checkpoint, completion_checkpoint_digest = (
                    mt5._ensure_optimization_completion_checkpoint(
                        checkpoint_path=Path(
                            payload["optimizationCompletionCheckpointPath"]
                        ),
                        allow_create=True,
                        operation_id=payload["operationId"],
                        action_digest=payload["actionRequestDigest"],
                        boundary_digest=payload["startBoundarySha256"],
                        dispatch_digest=dispatch_digest,
                        data_path=Path(payload["dataPath"]),
                        expert_file_name=payload["expertFileName"],
                        expert_ui_path=payload["expertUiPath"],
                        deployed_expert_sha256=payload[
                            "expectedDeployedExpertSha256"
                        ],
                        policy=payload["testerSettings"],
                        dispatch_path=dispatch_path,
                        tester_settings_sha256=sha256_bytes(
                            Path(payload["settingsScreenshotPath"]).read_bytes()
                        ),
                        tester_result_sha256=sha256_bytes(
                            Path(payload["resultScreenshotPath"]).read_bytes()
                        ),
                    )
                )
            if (
                self.fail_after_result_checkpoint
                and not self.failed_after_result_checkpoint
            ):
                self.failed_after_result_checkpoint = True
                raise RuntimeError("simulated_disconnect_after_result_checkpoint")
            if self.mutate_completed_result_checkpoint and recovery_state == "completed":
                Path(payload["resultScreenshotPath"]).write_bytes(
                    png_bytes() + b"changed-after-recovery-classification"
                )
            if recovery_state != "collected":
                Path(payload["testerReportPath"]).write_text(report, encoding="utf-8")
                Path(payload["reportScreenshotPath"]).write_bytes(png_bytes())
            report_path = Path(payload["testerReportPath"])
            report_digest = sha256_bytes(report_path.read_bytes())
            report_stat = report_path.stat()
            if (
                self.fail_after_report_checkpoint
                and not self.failed_after_report_checkpoint
            ):
                self.failed_after_report_checkpoint = True
                raise RuntimeError("simulated_disconnect_after_report_checkpoint")
            binding = self.binding(payload["stageId"])
            completed_at = datetime.now(timezone.utc)
            completion_pass_count = (
                2
                if optimize
                and payload["optimizationIntent"]["mode"]
                == "all_symbols_market_watch"
                else (4 if optimize else None)
            )
            tester_completion_evidence = completion_evidence(
                operation_id=payload["operationId"],
                expert_file_name=payload["expertFileName"],
                expert_ui_path=payload["expertUiPath"],
                deployed_expert_sha256=payload["expectedDeployedExpertSha256"],
                symbol="EURUSD",
                period=payload["testerSettings"]["period"],
                optimize=optimize,
                pass_count=completion_pass_count,
            )
            resolved = {
                "schemaVersion": mt5.RESOLVED_TESTER_SCHEMA,
                "expertFileName": payload["expertFileName"],
                "symbol": "EURUSD",
                "period": payload["testerSettings"]["period"],
                "model": payload["testerSettings"]["model"],
                "spread": "current",
                "useDate": payload["testerSettings"]["useDate"],
                "fromDate": payload["testerSettings"]["fromDate"],
                "toDate": payload["testerSettings"]["toDate"],
                "deposit": 10000.0,
                "visualMode": not optimize,
                "optimizationEnabled": optimize,
                "shutdownTerminalAfterTest": False,
            }
            requested_strategy_profile = payload.get("strategyExecutionProfile")
            execution_proof = (
                strategy_execution_proof(
                    requested_strategy_profile,
                    operation_id=payload["operationId"],
                    symbol="EURUSD",
                    period=payload["testerSettings"]["period"],
                )
                if not optimize and isinstance(requested_strategy_profile, dict)
                else None
            )
            refresh_recovered = bool(
                self.expert_catalog_refresh_attempted
                and (collecting or refresh_boundary_preexisting)
            )
            return {
                "schemaVersion": mt5.POWERSHELL_RESULT_SCHEMA,
                "ok": True,
                "action": action,
                "operationId": payload["operationId"],
                "startInvoked": not collecting,
                "recoveredWithoutStart": collecting,
                "executionObservedRunning": recovery_state in {"none", "in_flight"},
                "completedResultCheckpointReused": recovery_state
                in {"completed", "collected"},
                "completedReportCheckpointReused": recovery_state == "collected",
                "testerCompleted": True,
                "testerCompletionObservation": {
                    "none": "start_stop_transition_observed",
                    "in_flight": "recovery_stop_transition_observed",
                    "completed": "recovery_completed_checkpoint_observed",
                    "collected": "recovery_collected_checkpoint_observed",
                }[recovery_state],
                "freshResultEvidenceCaptured": True,
                "testerRunTransitionObserved": True,
                "testerRunTransitionEvidence": {
                    "none": "polled_stop_then_start",
                    "in_flight": "polled_stop_then_start",
                    "completed": "completed_result_checkpoint_after_dispatch",
                    "collected": "collected_report_checkpoint_after_dispatch",
                }[recovery_state],
                "testerCompletionEvidence": tester_completion_evidence,
                "strategyExecutionProof": execution_proof,
                "reportFormat": "spreadsheetml" if optimize else "html",
                "reportTabName": "Optimization Results" if optimize else "Backtest",
                "exactExpertVerified": True,
                "selectedExpertReadback": payload["expertUiPath"],
                "expertCatalogRefreshEvidence": {
                    "schemaVersion": mt5.EXPERT_CATALOG_REFRESH_SCHEMA,
                    "attempted": self.expert_catalog_refresh_attempted,
                    "recoveredAfterBoundary": refresh_recovered,
                    "commandCount": 1 if self.expert_catalog_refresh_attempted else 0,
                    "commandName": (
                        "Refresh" if self.expert_catalog_refresh_attempted else None
                    ),
                    "boundarySha256": (
                        payload["expertCatalogRefreshBoundarySha256"]
                        if self.expert_catalog_refresh_attempted
                        else None
                    ),
                    "navigatorPaneAutomationId": "32845",
                    "navigatorTreeAutomationId": "10064",
                    "expertNodeName": "Expert Advisors",
                    "refreshMenuAutomationId": None,
                    "refreshMenuName": "Refresh",
                    "refreshMenuProvider": "native_hmenu",
                    "refreshMenuWindowClass": "#32768",
                    "refreshMenuNativeCommandId": 33416,
                    "refreshMenuDispatchMethod": "targeted_menu_keyboard",
                    "matchCountBefore": (
                        1
                        if refresh_recovered
                        else (0 if self.expert_catalog_refresh_attempted else 1)
                    ),
                    "matchCountAfter": 1,
                    "selectedExpertReadback": payload["expertUiPath"],
                    "idleStateBefore": "Start",
                    "idleStateImmediatelyBeforeRefresh": (
                        "Start"
                        if self.expert_catalog_refresh_attempted
                        and not refresh_recovered
                        else None
                    ),
                    "idleStateAfter": "Start",
                    "algoTradingStateBefore": True,
                    "algoTradingStateAfter": True,
                    "terminalProcessId": payload["expectedTerminalProcessId"],
                    "terminalWindowHandle": payload["expectedTerminalWindowHandle"],
                    "elapsedMs": 100,
                    "verified": True,
                },
                "deployedExpertSha256": payload["expectedDeployedExpertSha256"],
                "startBoundaryCommitted": True,
                "startBoundarySha256": payload["startBoundarySha256"],
                "actionRequestDigest": payload["actionRequestDigest"],
                "dispatchConfirmationSha256": dispatch_digest,
                "optimizationCompletionCheckpointSha256": (
                    completion_checkpoint_digest if optimize else None
                ),
                "reportCreatedFresh": True,
                "reportSha256": report_digest,
                "reportByteSize": report_stat.st_size,
                "reportCreatedAt": datetime.fromtimestamp(report_stat.st_ctime, timezone.utc).isoformat(),
                "reportLastWriteAt": datetime.fromtimestamp(report_stat.st_mtime, timezone.utc).isoformat(),
                "autoTradingToggled": False,
                "chartAttached": False,
                "liveTradingExecuted": False,
                "terminalClosedByAdapter": False,
                "automationControlsVerified": {
                    **payload["requiredAutomationIds"],
                    **(
                        {
                            "criterion": payload[
                                "optimizationCriterionAutomationId"
                            ]
                        }
                        if optimize
                        else {}
                    ),
                },
                "optimizationRangesApplied": optimize,
                "optimizationRangesReadbackVerified": optimize,
                "inputReadbackSetSha256": readback_digest,
                "optimizationReadbackEntriesDigest": (
                    payload["optimizationIntent"]["setRef"]["expectedReadbackEntriesDigest"]
                    if optimize else None
                ),
                "baselineReadbackSetSha256": baseline_readback_digest,
                "baselineReadbackEntriesDigest": (
                    payload["optimizationIntent"]["baselinePresetRef"]["expectedReadbackEntriesDigest"]
                    if optimize else None
                ),
                "inputPresetSetSha256": (
                    payload["inputPresetRef"]["sha256"] if not optimize else None
                ),
                "inputPresetReadbackSetSha256": (
                    preset_readback_digest if not optimize else None
                ),
                "inputPresetReadbackEntriesDigest": (
                    payload["inputPresetRef"]["expectedReadbackEntriesDigest"]
                    if not optimize else None
                ),
                "resolvedTesterSettings": resolved,
                "processBinding": binding,
                "postProcessBinding": dict(binding, observedAt=datetime.now(timezone.utc).isoformat()),
            }
        raise AssertionError(action)


class Mt5AdapterFixture:
    def __init__(self, root: Path) -> None:
        self.workspace = root / "workspace"
        self.install = root / "install"
        self.data = root / "data"
        self.workspace.mkdir()
        self.install.mkdir()
        (self.data / "MQL5" / "Experts").mkdir(parents=True)
        (self.workspace / "EA_Versions").mkdir()
        self.terminal = self.install / "terminal64.exe"
        self.compiler = self.install / "MetaEditor64.exe"
        self.terminal.write_bytes(b"terminal64-test")
        self.compiler.write_bytes(b"metaeditor64-test")
        self.source = self.workspace / "EA_Versions" / "Strategy.mq5"
        self.source.write_text(
            "#property strict\n"
            "input double RiskPercent=1.0;\n"
            "input int MaxTrades=1;\n"
            "sinput bool UseGuard=true;\n"
            "void OnTick(){}\n",
            encoding="utf-8",
        )
        self.binding = {
            "candidateId": "mtc-test-mt5",
            "selectionRevision": 1,
            "bindingDigest": "a" * 64,
            "platform": "mt5",
        }
        self.target = {
            **self.binding,
            "installPath": str(self.install),
            "dataPath": str(self.data),
            "terminalPath": str(self.terminal),
            "compilerPath": str(self.compiler),
        }
        self.runner = FakeVisibleRunner(self)
        self.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.target,
            powershell_runner=self.runner,
        )

    def manifest(self) -> dict:
        core = {
            "schemaVersion": mt5.INPUT_MANIFEST_SCHEMA,
            "sourceDigest": sha256_bytes(self.source.read_bytes()),
            "entries": [
                {
                    "ordinal": 0, "qualifier": "input", "declaredType": "double",
                    "inputName": "RiskPercent", "valueKind": "decimal",
                    "setDefault": "1", "enumValues": [], "optimizable": True,
                },
                {
                    "ordinal": 1, "qualifier": "input", "declaredType": "int",
                    "inputName": "MaxTrades", "valueKind": "integer",
                    "setDefault": "1", "enumValues": [], "optimizable": True,
                },
                {
                    "ordinal": 2, "qualifier": "sinput", "declaredType": "bool",
                    "inputName": "UseGuard", "valueKind": "bool",
                    "setDefault": "true", "enumValues": [], "optimizable": False,
                },
            ],
        }
        return {**core, "manifestDigest": sha256_bytes(mt5._canonical_json(core))}

    def set_reference(
        self,
        file_name: str,
        ranges: dict[str, tuple[str, str, str]],
        *,
        manifest: dict | None = None,
        fixed_current_overrides: dict[str, str] | None = None,
    ) -> dict:
        manifest = copy.deepcopy(manifest) if manifest is not None else self.manifest()
        overrides = dict(fixed_current_overrides or {})
        entries = []
        lines = []
        for entry in manifest["entries"]:
            name = entry["inputName"]
            default = entry["setDefault"]
            current = overrides.pop(name, default)
            selected = ranges.get(name)
            start, step, stop = selected if selected else (current, "1", current)
            enabled = selected is not None
            entries.append(
                {
                    "ordinal": entry["ordinal"], "inputName": name,
                    "qualifier": entry["qualifier"], "declaredType": entry["declaredType"],
                    "valueKind": entry["valueKind"], "current": current,
                    "start": start, "step": step, "stop": stop, "enabled": enabled,
                }
            )
            lines.append(f"{name}={current}||{start}||{step}||{stop}||{'Y' if enabled else 'N'}")
        if overrides:
            raise AssertionError(f"Unknown fixed-current overrides: {sorted(overrides)}")
        path = self.workspace / "Sets" / file_name
        path.parent.mkdir(exist_ok=True)
        payload = ("\r\n".join(lines) + "\r\n").encode("ascii")
        path.write_bytes(payload)
        core = {
            "schemaVersion": mt5.SET_REF_SCHEMA,
            "relativePath": f"Sets/{file_name}",
            "sha256": sha256_bytes(payload),
            "inputManifestDigest": manifest["manifestDigest"],
            "entryCount": len(entries),
            "expectedReadbackEntries": entries,
            "expectedReadbackEntriesDigest": sha256_bytes(mt5._canonical_json(entries)),
        }
        return {**core, "refDigest": sha256_bytes(mt5._canonical_json(core))}

    def compiled_deployment(self) -> dict:
        binary = self.source.with_suffix(".ex5")
        core = {
            "schemaVersion": mt5.COMPILED_DEPLOYMENT_SCHEMA,
            "deploymentRef": "mt5deploy_" + "d" * 24,
            "sourceRelativePath": "EA_Versions/Strategy.mq5",
            "sourceSha256": sha256_bytes(self.source.read_bytes()),
            "binaryRelativePath": "EA_Versions/Strategy.ex5",
            "binarySha256": sha256_bytes(binary.read_bytes()),
            "expertFileName": "Strategy.ex5",
            "terminalCandidateId": self.binding["candidateId"],
            "terminalSelectionRevision": self.binding["selectionRevision"],
            "terminalBindingDigest": self.binding["bindingDigest"],
            "reuseRequired": True,
        }
        return {**core, "bindingDigest": sha256_bytes(mt5._canonical_json(core))}

    def tester_input_preset(self) -> dict:
        manifest = self.manifest()
        assumptions = [
            {
                "inputName": "RiskPercent", "inputType": "double",
                "sourceDefault": 1.0, "testerValue": 1.0,
                "reasonCode": "reset_to_immutable_source_default_to_prevent_stale_tester_state",
            },
            {
                "inputName": "MaxTrades", "inputType": "int",
                "sourceDefault": 1, "testerValue": 1,
                "reasonCode": "reset_to_immutable_source_default_to_prevent_stale_tester_state",
            },
            {
                "inputName": "UseGuard", "inputType": "bool",
                "sourceDefault": True, "testerValue": True,
                "reasonCode": "reset_to_immutable_source_default_to_prevent_stale_tester_state",
            },
        ]
        unsigned = {
            "schemaVersion": mt5.TESTER_INPUT_PRESET_SCHEMA,
            "mode": "full_immutable_source_default_snapshot",
            "scope": "mt5_strategy_tester_only",
            "sourceDigest": manifest["sourceDigest"],
            "inputManifestDigest": manifest["manifestDigest"],
            "assumptions": assumptions,
            "liveSourceDefaultsPreserved": True,
            "visibleExpertPropertiesRequired": True,
            "readbackRequired": True,
            "liveTradingAllowed": False,
            "fullCertifiedInputSnapshot": True,
            "simulationInputNames": [],
        }
        return {**unsigned, "presetDigest": sha256_bytes(mt5._canonical_json(unsigned))}

    def request(self, stage_id: str, token: str) -> dict:
        source_digest = sha256_bytes(self.source.read_bytes())
        request = {
            "schemaVersion": mt5.REQUEST_SCHEMA,
            "buildId": "build-mt5-test",
            "stageId": stage_id,
            "platform": "mt5",
            "artifactKind": "expert_advisor",
            "workspaceRoot": str(self.workspace),
            "versions": [
                {
                    "versionFile": "EA_Versions/Strategy.mq5",
                    "sourceDigest": source_digest,
                }
            ],
            "terminalBinding": self.binding,
            "visibleOperation": {
                "operationId": f"ea-visible-{token:0>24}"[-35:],
                "stageId": stage_id,
                "state": "reserved",
                "requiresExplicitResume": False,
            },
            "missionId": "mission-mt5-test",
            "reportId": "report-mt5-test",
            "safety": {
                "liveTradingAllowed": False,
                "autoTradingMayBeToggled": False,
                "chartAttachmentAllowed": False,
                "terminalShutdownAllowed": False,
                "optimizationAllowed": stage_id == "optimize",
                "visualModeRequired": stage_id == "backtest_recheck",
                "neverStart": False,
                "serviceAction": "start_round",
            },
            "resolvedTarget": self.target,
        }
        if stage_id in {"backtest_recheck", "optimize"}:
            request["compiledDeployment"] = self.compiled_deployment()
            request["testerSettings"] = {
                "schemaVersion": mt5.TESTER_SETTINGS_SCHEMA,
                "expertFileName": "Strategy.ex5",
                "symbolPolicy": "explicit",
                "symbol": "EURUSD",
                "period": "H1",
                "model": "every_tick",
                "spreadPolicy": "current",
                "useDate": False,
                "fromDate": None,
                "toDate": None,
                "depositPolicy": "current_tester_deposit",
                "visualMode": stage_id == "backtest_recheck",
                "optimizationEnabled": stage_id == "optimize",
                "shutdownTerminalAfterTest": False,
                "liveTradingAllowed": False,
            }
            if stage_id == "backtest_recheck":
                request["testerSettings"]["testerInputPreset"] = self.tester_input_preset()
                request["mt5InputManifest"] = self.manifest()
                request["mt5InputBinding"] = self.set_reference(
                    "tester-input-preset.set", {}
                )
        if stage_id == "optimize":
            set_ref = self.set_reference(
                "optimization.set", {"RiskPercent": ("0.5", "0.5", "2")}
            )
            baseline_ref = self.set_reference("optimization-baseline.set", {})
            ranges = [
                {
                    "inputName": "RiskPercent",
                    "start": "0.5",
                    "step": "0.5",
                    "stop": "2",
                    "enabled": True,
                }
            ]
            request["optimizationIntent"] = {
                "schemaVersion": mt5.OPTIMIZATION_INTENT_SCHEMA,
                "sourceDigest": source_digest,
                "inputManifest": self.manifest(),
                "inputManifestDigest": self.manifest()["manifestDigest"],
                "testerInputPreset": self.tester_input_preset(),
                "setFile": set_ref["relativePath"],
                "setDigest": set_ref["sha256"],
                "setRef": set_ref,
                "baselinePresetRef": baseline_ref,
                "ranges": ranges,
                "rangesDigest": sha256_bytes(mt5._canonical_json(ranges)),
                "visibleInputsRequired": True,
                "reportRequired": True,
                "startOnce": True,
                "mode": "fast_genetic",
                "criterion": "balance_max",
            }
        return request

    def prepare_compiled_binary(self) -> None:
        self.source.with_suffix(".ex5").write_bytes(b"EX5\x00verified")

    def capability(self, request: dict) -> dict:
        result = self.adapter.capability_provider(
            platform="mt5",
            stage_id=request["stageId"],
            terminal_binding=request["terminalBinding"],
            visible_operation=request["visibleOperation"],
            resolved_target=request["resolvedTarget"],
            tester_settings=request.get("testerSettings"),
        )
        assert result["ready"], result
        return result


class TestVisibleTerminalMt5(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="metafx-mt5-visible-test-")
        # Hosted Windows runners expose the temporary root through an 8.3
        # alias such as RUNNER~1. Production resolves the workspace root
        # (_resolved_directory) before validating optimization intents, so
        # keep the fixture canonical for the direct _validate_* tests too.
        self.fixture = Mt5AdapterFixture(Path(self.temporary.name).resolve(strict=True))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_parse_utc_accepts_powershell_round_trip_fractions_on_every_python(self) -> None:
        # PowerShell ToString("o") emits seven fractional digits; Python 3.10
        # only parses three or six, so the adapter must normalize itself.
        parsed = mt5._parse_utc("2026-10-17T16:23:22.6133192Z")
        self.assertEqual(parsed.tzinfo, timezone.utc)
        self.assertEqual(parsed.microsecond, 613319)
        self.assertEqual(
            mt5._parse_utc("2026-10-17T16:23:22.6133192+00:00"), parsed
        )
        self.assertEqual(
            mt5._parse_utc("2026-10-17T16:23:22.6Z").microsecond, 600000
        )
        self.assertEqual(
            mt5._parse_utc("2026-10-17T16:23:22Z"),
            datetime(2026, 10, 17, 16, 23, 22, tzinfo=timezone.utc),
        )
        self.assertEqual(
            mt5._parse_utc("2026-10-17T16:23:22.6133192123Z").microsecond, 613319
        )
        for invalid in (
            "",
            "2026-10-17T16:23:22.6133192",
            "2026-10-17T16:23:22.61x3192Z",
            "not-a-time",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(
                    mt5.VisibleTerminalAdapterError,
                    "process_observation_time_invalid",
                ):
                    mt5._parse_utc(invalid)

    def test_certified_ema_strategy_execution_proof_is_bidirectional_and_exact(self) -> None:
        source_digest = "a" * 64
        profile = strategy_execution_profile(source_digest)
        validated_profile = mt5._validate_strategy_execution_profile(
            profile,
            stage_id="backtest_recheck",
            source_digest=source_digest,
        )
        proof = strategy_execution_proof(profile)
        validated, digest = mt5._validate_strategy_execution_proof(
            proof,
            profile=validated_profile,
            operation_id=proof["operationId"],
            symbol="EURUSD",
            period="H1",
        )
        self.assertEqual(validated, proof)
        self.assertEqual(digest, sha256_bytes(mt5._canonical_json(proof)))

    def test_certified_ema_strategy_execution_proof_rejects_mutations(self) -> None:
        source_digest = "b" * 64
        profile = strategy_execution_profile(source_digest)
        baseline = strategy_execution_proof(profile)
        mutations = {
            "missing_sell": lambda row: row.update({
                "sellSignalCount": 0,
                "sellEntryCount": 0,
            }),
            "wrong_buy_cross": lambda row: row["sequences"][0].update({
                "fast1": 0.5,
            }),
            "entry_without_pending_order": lambda row: row["sequences"][0].update({
                "pendingLineSha256": row["telemetryLineSha256s"][2],
            }),
            "rejected_signal": lambda row: row.update({"rejectedCount": 1}),
            "duplicate_deal": lambda row: row["sequences"][1].update({"deal": 1001}),
            "report_identity_drift": lambda row: row.update({"symbol": "XAUUSD"}),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                candidate = copy.deepcopy(baseline)
                mutate(candidate)
                with self.assertRaisesRegex(
                    mt5.VisibleTerminalAdapterError,
                    "strategy_execution_proof_invalid",
                ):
                    mt5._validate_strategy_execution_proof(
                        candidate,
                        profile=profile,
                        operation_id=baseline["operationId"],
                        symbol="EURUSD",
                        period="H1",
                    )

    def test_generic_backtest_rejects_unrequested_strategy_execution_proof(self) -> None:
        profile = strategy_execution_profile("c" * 64)
        proof = strategy_execution_proof(profile)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "unexpected_strategy_execution_proof",
        ):
            mt5._validate_strategy_execution_proof(
                proof,
                profile=None,
                operation_id=proof["operationId"],
                symbol="EURUSD",
                period="H1",
            )

    def test_powershell_binds_certified_strategy_execution_proof_to_closed_run(self) -> None:
        text = PS_PATH.read_text(encoding="utf-8")
        self.assertIn("function Assert-CertifiedEmaSmokeExecutionProof", text)
        self.assertIn("Test-LogRecordInClosedRunWindow", text)
        self.assertIn("function Get-CertifiedEmaSmokeTelemetryJson", text)
        self.assertIn("$expectedTelemetrySource", text)
        self.assertIn("$expertLeaf ($symbol,$period)", text)
        self.assertIn(" {3}EMA_SMOKE_V1 ", text)
        self.assertIn("RegexOptions]::CultureInvariant", text)
        self.assertIn("Rejected and orphan_entry are never valid", text)
        self.assertIn("strategyExecutionProof = $script:StrategyExecutionProof", text)

    def test_native_mt5_disabled_bool_range_normalization_is_readback_only(self) -> None:
        self.assertFalse(mt5._semantic_input_value_equal("invalid", "invalid", "bool"))
        reference = self.fixture.set_reference("native-disabled-bool.set", {})
        readback = self.fixture.workspace / "Sets" / "native-disabled-bool-readback.set"
        readback.write_bytes(
            (
                "; saved by MetaTrader 5\r\n"
                "RiskPercent=1||1||1||1||N\r\n"
                "MaxTrades=1||1||1||1||N\r\n"
                "UseGuard=true||false||0||true||N\r\n"
            ).encode("utf-16")
        )

        self.assertEqual(
            mt5._assert_set_matches_expected(
                readback,
                reference["expectedReadbackEntries"],
                allow_native_disabled_bool_range=True,
            ),
            reference["expectedReadbackEntriesDigest"],
        )
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError, "mt5_set_readback_mismatch"
        ):
            mt5._assert_set_matches_expected(
                readback, reference["expectedReadbackEntries"]
            )

    def test_native_mt5_disabled_bool_range_normalization_remains_fail_closed(self) -> None:
        reference = self.fixture.set_reference("native-bool-tamper.set", {})
        readback = self.fixture.workspace / "Sets" / "native-bool-tamper-readback.set"
        cases = {
            "current_value_drift": "UseGuard=false||false||0||true||N",
            "enabled_flag_drift": "UseGuard=true||false||0||true||Y",
            "noncanonical_start": "UseGuard=true||true||0||true||N",
            "noncanonical_step": "UseGuard=true||false||1||true||N",
            "noncanonical_stop": "UseGuard=true||false||0||false||N",
        }
        for name, bool_row in cases.items():
            with self.subTest(name=name):
                readback.write_text(
                    "RiskPercent=1||1||1||1||N\n"
                    "MaxTrades=1||1||1||1||N\n"
                    f"{bool_row}\n",
                    encoding="ascii",
                )
                with self.assertRaisesRegex(
                    mt5.VisibleTerminalAdapterError, "mt5_set_readback_mismatch"
                ):
                    mt5._assert_set_matches_expected(
                        readback,
                        reference["expectedReadbackEntries"],
                        allow_native_disabled_bool_range=True,
                    )

        readback.write_text(
            "RiskPercent=1||2||1||1||N\n"
            "MaxTrades=1||1||1||1||N\n"
            "UseGuard=true||false||0||true||N\n",
            encoding="ascii",
        )
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError, "mt5_set_readback_mismatch"
        ):
            mt5._assert_set_matches_expected(
                readback,
                reference["expectedReadbackEntries"],
                allow_native_disabled_bool_range=True,
            )

    def test_compile_publishes_common_bridge_evidence(self) -> None:
        request = self.fixture.request("compile_validate", "1")
        self.fixture.capability(request)
        result = self.fixture.adapter.compile_handler(request=request)
        metrics = result["metrics"]
        self.assertEqual(self.fixture.adapter.supported_platforms, frozenset({"mt5"}))
        self.assertEqual(metrics["evidenceMode"], "visible_front_office_v1")
        self.assertTrue(metrics["visibleMetaEditor"])
        self.assertEqual(metrics["resultLine"], "Result: 0 errors, 0 warnings")
        self.assertTrue(metrics["zeroErrors"])
        self.assertTrue(metrics["zeroWarnings"])
        self.assertFalse(metrics["backtestExecuted"])
        expected_binding_keys = {
            "schemaVersion", "observedAt", "stageId", "terminalCandidateId",
            "terminalSelectionRevision", "terminalBindingDigest", "terminalProcessId",
            "terminalExecutableSha256", "terminalWindowHandle", "terminalWindowOwnerProcessId",
            "terminalWindowTitleSha256", "terminalWindowClassSha256", "frontOfficeKind",
            "frontOfficeProcessId", "frontOfficeExecutableSha256", "frontOfficeWindowHandle",
            "frontOfficeWindowOwnerProcessId", "frontOfficeWindowTitleSha256",
            "frontOfficeWindowClassSha256", "processBindingDigest",
        }
        self.assertEqual(set(metrics["processBinding"]), expected_binding_keys)
        receipt_path = self.fixture.workspace / next(
            item["relativePath"] for item in result["artifactSpecifications"]
            if item["alias"] == "adapter_receipt"
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["processBindingDigest"], metrics["processBindingDigest"])
        self.assertEqual(receipt["postProcessBindingDigest"], metrics["postProcessBindingDigest"])

    def test_compile_recovery_recompiles_when_pre_f7_failure_left_no_binary(self) -> None:
        request = self.fixture.request("compile_validate", "49")
        self.fixture.capability(request)
        self.fixture.runner.fail_compile_before_binary = True
        with self.assertRaisesRegex(RuntimeError, "simulated_compile_readiness_failure"):
            self.fixture.adapter.compile_handler(request=request)

        operation_id = request["visibleOperation"]["operationId"]
        working_root = (
            self.fixture.data
            / "MQL5"
            / "Experts"
            / "Metafxclub"
            / "AgentHQ"
            / operation_id
        )
        self.assertTrue((working_root / f"agenthq_{operation_id[11:]}.mq5").is_file())
        self.assertFalse((working_root / f"agenthq_{operation_id[11:]}.ex5").exists())

        result = self.fixture.adapter.compile_handler(request=request)

        self.assertEqual(self.fixture.runner.actions[-1], "recover_compile")
        self.assertTrue(result["metrics"]["compileVerified"])
        self.assertTrue(result["metrics"]["recoveryRecompile"])

    def test_compile_verifier_accepts_exact_live_metaeditor_summary(self) -> None:
        binary = self.fixture.source.with_suffix(".ex5")
        binary.write_bytes(b"EX5\x00live-summary")
        source_digest = sha256_bytes(self.fixture.source.read_bytes())
        binary_digest = sha256_bytes(binary.read_bytes())
        verified = mt5.verify_visible_metaeditor_compile_mt5(
            {
                "platform": "mt5",
                "sourcePath": self.fixture.source,
                "binaryPath": binary,
                "sourceDigest": source_digest,
                "compiledDigest": binary_digest,
                "visibleUiResult": {
                    "compileResultLine": (
                        "0 errors, 0 warnings, 499 ms elapsed, "
                        "cpu='AVX2 + FMA3'"
                    ),
                    "freshBinaryObserved": True,
                    "compileResultBeforeSha256": "b" * 64,
                    "compileResultAfterSha256": "c" * 64,
                },
            }
        )
        self.assertTrue(verified["compileVerified"])
        self.assertEqual(
            verified["compileResultLine"],
            "Result: 0 errors, 0 warnings",
        )
        self.assertEqual(
            verified["nativeCompileResultLine"],
            "0 errors, 0 warnings, 499 ms elapsed, cpu='AVX2 + FMA3'",
        )

    def test_backtest_metrics_and_receipt_are_fail_closed_and_bridge_shaped(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("backtest_recheck", "2")
        capability = self.fixture.capability(request)
        self.assertEqual(capability["automationIds"]["deposit"], "10489")
        self.assertEqual(capability["automationIds"]["visualMode"], "10490")
        self.assertNotIn("criterion", capability["automationIds"])
        self.assertNotIn("criterion", mt5.BACKTEST_TESTER_AUTOMATION_IDS)
        self.assertEqual(mt5.BACKTEST_TESTER_AUTOMATION_IDS["visualMode"], "10490")
        self.assertEqual(mt5.REQUIRED_TESTER_AUTOMATION_IDS["criterion"], "10507")
        self.assertTrue(capability["testerTradeRowsEvidence"])
        self.assertEqual(capability["testerStartState"], "Start")
        result = self.fixture.adapter.backtest_handler(request=request)
        backtest_payload = next(
            payload
            for payload in reversed(self.fixture.runner.payloads)
            if payload.get("action") == "backtest"
        )
        self.assertNotIn("criterion", backtest_payload["requiredAutomationIds"])
        self.assertEqual(
            backtest_payload["requiredAutomationIds"]["visualMode"],
            "10490",
        )
        self.assertEqual(
            backtest_payload["requiredAutomationIds"],
            mt5.BACKTEST_TESTER_AUTOMATION_IDS,
        )
        self.assertIsNone(
            backtest_payload.get("optimizationCriterionAutomationId")
        )
        metrics = result["metrics"]
        self.assertEqual(
            self.fixture.runner.actions[-3:],
            ["probe", "backtest", "post_probe"],
        )
        self.assertEqual(self.fixture.runner.tester_start_dispatch_count, 1)
        self.assertGreaterEqual(
            datetime.fromisoformat(metrics["postProcessBinding"]["observedAt"]),
            datetime.fromisoformat(metrics["processBinding"]["observedAt"]),
        )
        self.assertEqual(metrics["tradeCount"], 2)
        self.assertEqual(metrics["tradeRowCount"], 2)
        self.assertEqual(metrics["buyTradeCount"], 1)
        self.assertEqual(metrics["sellTradeCount"], 1)
        self.assertEqual(metrics["mismatchedChartErrors"], 0)
        self.assertTrue(metrics["testerTradeRowsVerified"])
        self.assertEqual(metrics["resolvedTesterSettings"]["deposit"], 10000.0)
        self.assertTrue(metrics["backtestExecuted"])
        self.assertFalse(metrics["attentionRequired"])
        self.assertEqual(metrics["testerReportFormat"], "html")
        self.assertEqual(metrics["testerReportTabName"], "Backtest")
        self.assertFalse(metrics["expertCatalogRefreshEvidence"]["attempted"])
        self.assertEqual(metrics["expertCatalogRefreshEvidence"]["commandCount"], 0)
        self.assertRegex(metrics["expertCatalogRefreshEvidenceDigest"], r"^[0-9a-f]{64}$")
        receipt_path = self.fixture.workspace / next(
            item["relativePath"] for item in result["artifactSpecifications"]
            if item["alias"] == "adapter_receipt"
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["reportFormat"], "html")
        self.assertEqual(receipt["reportTabName"], "Backtest")
        self.assertEqual(receipt["resolvedTesterSettingsDigest"], metrics["resolvedTesterSettingsDigest"])
        self.assertTrue(receipt["testerInputPresetReportVerified"])
        self.assertEqual(
            receipt["testerInputReadbackEntriesDigest"],
            request["mt5InputBinding"]["expectedReadbackEntriesDigest"],
        )
        actions_before_replay = list(self.fixture.runner.actions)
        replay = self.fixture.adapter.backtest_handler(request=request)
        self.assertTrue(replay["metrics"]["recoveredExistingReceipt"])
        self.assertFalse(replay["metrics"]["backtestExecuted"])
        self.assertEqual(self.fixture.runner.actions, actions_before_replay)

    def test_backtest_retains_certified_strategy_execution_proof_end_to_end(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("backtest_recheck", "ab12")
        profile = strategy_execution_profile(
            request["versions"][0]["sourceDigest"]
        )
        request["strategyExecutionProfile"] = profile
        self.fixture.capability(request)

        result = self.fixture.adapter.backtest_handler(request=request)
        backtest_payload = next(
            payload
            for payload in reversed(self.fixture.runner.payloads)
            if payload.get("action") == "backtest"
        )
        expected_proof = strategy_execution_proof(
            profile,
            operation_id=request["visibleOperation"]["operationId"],
            symbol=request["testerSettings"]["symbol"],
            period=request["testerSettings"]["period"],
        )
        expected_proof_digest = sha256_bytes(
            mt5._canonical_json(expected_proof)
        )

        self.assertEqual(backtest_payload["strategyExecutionProfile"], profile)
        metrics = result["metrics"]
        self.assertEqual(metrics["strategyExecutionProfile"], profile)
        self.assertEqual(metrics["strategyExecutionProof"], expected_proof)
        self.assertEqual(
            metrics["strategyExecutionProofDigest"],
            expected_proof_digest,
        )
        self.assertEqual(metrics["tradeCount"], expected_proof["entryCount"])
        self.assertEqual(
            metrics["buyTradeCount"], expected_proof["buyEntryCount"]
        )
        self.assertEqual(
            metrics["sellTradeCount"], expected_proof["sellEntryCount"]
        )

        receipt_path = self.fixture.workspace / next(
            item["relativePath"]
            for item in result["artifactSpecifications"]
            if item["alias"] == "adapter_receipt"
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["strategyExecutionProfile"], profile)
        self.assertEqual(receipt["strategyExecutionProof"], expected_proof)
        self.assertEqual(
            receipt["strategyExecutionProofDigest"],
            expected_proof_digest,
        )
        self.assertEqual(
            receipt["tradeCount"], receipt["strategyExecutionProof"]["entryCount"]
        )
        self.assertEqual(
            receipt["buyTradeCount"],
            receipt["strategyExecutionProof"]["buyEntryCount"],
        )
        self.assertEqual(
            receipt["sellTradeCount"],
            receipt["strategyExecutionProof"]["sellEntryCount"],
        )

    def test_backtest_rejects_non_idle_final_post_process_probe(self) -> None:
        self.fixture.prepare_compiled_binary()
        base_runner = self.fixture.runner
        def stop_after_verification(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            response = base_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "post_probe":
                response = copy.deepcopy(response)
                response["testerStartState"] = "Stop"
            return response

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=stop_after_verification,
        )
        request = self.fixture.request("backtest_recheck", "74")
        self.fixture.capability(request)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_tester_post_process_probe_invalid",
        ):
            self.fixture.adapter.backtest_handler(request=request)
        self.assertEqual(base_runner.tester_start_dispatch_count, 1)
        self.assertFalse(
            any(
                (self.fixture.workspace / "Summaries").glob(
                    "*-backtest-receipt.json"
                )
            )
        )

    def test_backtest_rejects_final_post_process_algo_trading_flip(self) -> None:
        self.fixture.prepare_compiled_binary()
        base_runner = self.fixture.runner

        def flip_algo_state(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            response = base_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "post_probe":
                response = copy.deepcopy(response)
                response["processBinding"]["autoTradingState"] = False
            return response

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=flip_algo_state,
        )
        request = self.fixture.request("backtest_recheck", "75")
        self.fixture.capability(request)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "process_binding_drift",
        ):
            self.fixture.adapter.backtest_handler(request=request)
        self.assertEqual(base_runner.tester_start_dispatch_count, 1)
        self.assertFalse(
            any(
                (self.fixture.workspace / "Summaries").glob(
                    "*-backtest-receipt.json"
                )
            )
        )

    def test_backtest_rejects_extra_final_post_process_probe_field(self) -> None:
        self.fixture.prepare_compiled_binary()
        base_runner = self.fixture.runner

        def add_unsigned_field(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            response = base_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "post_probe":
                response = copy.deepcopy(response)
                response["unexpected"] = True
            return response

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=add_unsigned_field,
        )
        request = self.fixture.request("backtest_recheck", "76")
        self.fixture.capability(request)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_tester_post_process_probe_invalid",
        ):
            self.fixture.adapter.backtest_handler(request=request)
        self.assertEqual(base_runner.tester_start_dispatch_count, 1)
        self.assertFalse(
            any(
                (self.fixture.workspace / "Summaries").glob(
                    "*-backtest-receipt.json"
                )
            )
        )

    def test_backtest_accepts_local_duration_on_final_post_process_probe(self) -> None:
        self.fixture.prepare_compiled_binary()
        base_runner = self.fixture.runner

        def add_local_transport_duration(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            response = base_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "post_probe":
                response = copy.deepcopy(response)
                response["pythonObservedDurationMs"] = 17
            return response

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=add_local_transport_duration,
        )
        request = self.fixture.request("backtest_recheck", "77")
        self.fixture.capability(request)
        result = self.fixture.adapter.backtest_handler(request=request)
        self.assertEqual(
            result["metrics"]["postProcessBinding"]["terminalProcessId"],
            101,
        )
        self.assertEqual(base_runner.tester_start_dispatch_count, 1)

    def test_backtest_rejects_invalid_local_duration_on_final_post_process_probe(self) -> None:
        self.fixture.prepare_compiled_binary()
        base_runner = self.fixture.runner

        def add_invalid_local_transport_duration(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            response = base_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "post_probe":
                response = copy.deepcopy(response)
                response["pythonObservedDurationMs"] = True
            return response

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=add_invalid_local_transport_duration,
        )
        request = self.fixture.request("backtest_recheck", "78")
        self.fixture.capability(request)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_tester_post_process_probe_invalid",
        ):
            self.fixture.adapter.backtest_handler(request=request)
        self.assertEqual(base_runner.tester_start_dispatch_count, 1)

    def test_backtest_receipt_replay_reparses_report_and_rejects_tampered_counts(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("backtest_recheck", "73")
        self.fixture.capability(request)
        result = self.fixture.adapter.backtest_handler(request=request)
        receipt_path = self.fixture.workspace / next(
            item["relativePath"]
            for item in result["artifactSpecifications"]
            if item["alias"] == "adapter_receipt"
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt.update(
            {
                "tradeCount": 4,
                "tradeRowCount": 4,
                "buyTradeCount": 2,
                "sellTradeCount": 2,
            }
        )
        receipt_path.write_bytes(mt5._canonical_json(receipt))
        actions_before = list(self.fixture.runner.actions)

        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "visible_receipt_evidence_mismatch",
        ):
            self.fixture.adapter.backtest_handler(request=request)

        self.assertEqual(self.fixture.runner.actions, actions_before)

    def test_receipt_replay_invokes_report_verifier_again(self) -> None:
        self.fixture.prepare_compiled_binary()
        verifier_calls = 0

        def counting_verifier(context: dict) -> dict:
            nonlocal verifier_calls
            verifier_calls += 1
            return mt5.verify_mt5_tester_report(context)

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=self.fixture.runner,
            backtest_verifier=counting_verifier,
        )
        request = self.fixture.request("backtest_recheck", "74")
        self.fixture.capability(request)
        self.fixture.adapter.backtest_handler(request=request)
        self.fixture.adapter.backtest_handler(request=request)

        self.assertEqual(verifier_calls, 2)

    def test_receipt_replay_rejects_coherently_tampered_completion_evidence(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("backtest_recheck", "77")
        self.fixture.capability(request)
        result = self.fixture.adapter.backtest_handler(request=request)
        receipt_path = self.fixture.workspace / next(
            item["relativePath"]
            for item in result["artifactSpecifications"]
            if item["alias"] == "adapter_receipt"
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        evidence = receipt["testerCompletionEvidence"]
        evidence["startLineSha256"] = "1" * 64
        evidence["runIdentitySha256"] = mt5._tester_completion_identity_digest(
            operation_id=receipt["operationId"],
            completion_marker=evidence["completionMarker"],
            expert_symbol_period_sha256=evidence["expertSymbolPeriodSha256"],
            log_identity_sha256=evidence["logIdentitySha256"],
            core_sources_sha256=evidence["coreSourcesSha256"],
            core_thread_identities_sha256=evidence[
                "coreThreadIdentitiesSha256"
            ],
            start_line_sha256=evidence["startLineSha256"],
            completion_line_sha256=evidence["completionLineSha256"],
            start_line_ordinal=evidence["startLineOrdinal"],
            completion_line_ordinal=evidence["completionLineOrdinal"],
            completion_pass_count=evidence["completionPassCount"],
        )
        receipt["testerCompletionEvidenceDigest"] = sha256_bytes(
            mt5._canonical_json(evidence)
        )
        receipt_path.write_bytes(mt5._canonical_json(receipt))
        actions_before = list(self.fixture.runner.actions)

        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "tester_completion_evidence_checkpoint_invalid",
        ):
            self.fixture.adapter.backtest_handler(request=request)
        self.assertEqual(self.fixture.runner.actions, actions_before)

    def test_receipt_replay_rejects_report_changed_by_verifier(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("backtest_recheck", "76")
        self.fixture.capability(request)
        self.fixture.adapter.backtest_handler(request=request)

        def mutating_verifier(context: dict) -> dict:
            verified = mt5.verify_mt5_tester_report(context)
            report = Path(context["testerReportPath"])
            metadata = report.stat(follow_symlinks=False)
            payload = report.read_bytes()
            mutated = payload.replace(b"Total Deals", b"Total Dealx", 1)
            self.assertNotEqual(mutated, payload)
            report.write_bytes(mutated)
            os.utime(
                report,
                ns=(metadata.st_atime_ns, metadata.st_mtime_ns),
            )
            return verified

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=self.fixture.runner,
            backtest_verifier=mutating_verifier,
        )
        self.fixture.capability(request)
        actions_before = list(self.fixture.runner.actions)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "visible_receipt_report_reverification_failed",
        ):
            self.fixture.adapter.backtest_handler(request=request)
        self.assertEqual(self.fixture.runner.actions, actions_before)

    def test_capability_exposes_verified_active_tester_start_state(self) -> None:
        self.fixture.prepare_compiled_binary()
        base_runner = self.fixture.runner

        def active_probe(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            response = base_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "probe":
                response = dict(response)
                response["testerStartState"] = "Stop"
            return response

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=active_probe,
        )
        request = self.fixture.request("backtest_recheck", "52")
        capability = self.fixture.capability(request)
        self.assertTrue(capability["ready"], capability)
        self.assertEqual(capability["testerStartState"], "Stop")

    def test_capability_rejects_unverified_tester_start_state(self) -> None:
        self.fixture.prepare_compiled_binary()
        base_runner = self.fixture.runner

        def ambiguous_probe(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            response = base_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "probe":
                response = dict(response)
                response["testerStartState"] = "Idle"
            return response

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=ambiguous_probe,
        )
        request = self.fixture.request("backtest_recheck", "53")
        capability = self.fixture.adapter.capability_provider(
            platform="mt5",
            stage_id=request["stageId"],
            terminal_binding=request["terminalBinding"],
            visible_operation=request["visibleOperation"],
            resolved_target=request["resolvedTarget"],
            tester_settings=request.get("testerSettings"),
        )
        self.assertFalse(capability["ready"])
        self.assertEqual(
            capability["reasonCode"], "mt5_tester_start_state_unverified"
        )

    def test_backtest_accepts_exact_legacy_results_tab(self) -> None:
        self.fixture.prepare_compiled_binary()
        base_runner = self.fixture.runner

        def legacy_results(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            response = base_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                response = dict(response)
                response["reportTabName"] = "Results"
            return response

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=legacy_results,
        )
        request = self.fixture.request("backtest_recheck", "54")
        self.fixture.capability(request)
        result = self.fixture.adapter.backtest_handler(request=request)
        self.assertEqual(result["metrics"]["testerReportTabName"], "Results")

    def test_completion_evidence_is_bound_to_stage_and_rejects_disconnect(self) -> None:
        evidence = completion_evidence(
            operation_id="ea-visible-" + ("a" * 24),
            expert_file_name="Strategy.ex5",
            expert_ui_path="Metafxclub\\AgentHQ\\Strategy",
            deployed_expert_sha256="f" * 64,
            symbol="EURUSD",
            period="H1",
            optimize=True,
            pass_count=4,
        )
        expected = {
            "expected_operation_id": "ea-visible-" + ("a" * 24),
            "expected_expert_file_name": "Strategy.ex5",
            "expected_expert_ui_path": "Metafxclub\\AgentHQ\\Strategy",
            "expected_deployed_expert_sha256": "f" * 64,
            "expected_symbol": "EURUSD",
            "expected_period": "H1",
        }
        validated, _ = mt5._validate_tester_completion_evidence(
            evidence, expected_marker="optimization_finished", **expected
        )
        self.assertEqual(validated["completionPassCount"], 4)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_tester_clean_completion_unverified",
        ):
            mt5._validate_tester_completion_evidence(
                evidence, expected_marker="thread_finished", **expected
            )
        mismatched_expectations = {
            "operation": ("expected_operation_id", "ea-visible-" + ("b" * 24)),
            "expert": ("expected_expert_file_name", "Strategy-v2.ex5"),
            "ui_path": (
                "expected_expert_ui_path",
                "Metafxclub\\AgentHQ\\OtherStrategy",
            ),
            "binary": ("expected_deployed_expert_sha256", "e" * 64),
            "symbol": ("expected_symbol", "GBPUSD"),
            "period": ("expected_period", "H12"),
        }
        for label, (field, wrong_value) in mismatched_expectations.items():
            with self.subTest(identity=label), self.assertRaisesRegex(
                mt5.VisibleTerminalAdapterError,
                "mt5_tester_clean_completion_unverified",
            ):
                wrong_expected = dict(expected)
                wrong_expected[field] = wrong_value
                mt5._validate_tester_completion_evidence(
                    evidence,
                    expected_marker="optimization_finished",
                    **wrong_expected,
                )
        for label, mutation in (
            (
                "source_pair",
                {"completionSourceSha256": sha256_bytes(b"Agent")},
            ),
            ("non_increasing_ordinal", {"completionLineOrdinal": 10}),
            ("cross_log_global_completion", {"completionLogPathSha256": "b" * 64}),
            ("core_thread", {"coreThreadIdentitySha256s": ["c" * 64]}),
        ):
            with self.subTest(evidence=label), self.assertRaisesRegex(
                mt5.VisibleTerminalAdapterError,
                "mt5_tester_clean_completion_unverified",
            ):
                tampered = copy.deepcopy(evidence)
                tampered.update(mutation)
                mt5._validate_tester_completion_evidence(
                    tampered,
                    expected_marker="optimization_finished",
                    **expected,
                )
        evidence = completion_evidence(
            operation_id=expected["expected_operation_id"],
            expert_file_name=expected["expected_expert_file_name"],
            expert_ui_path=expected["expected_expert_ui_path"],
            deployed_expert_sha256=expected["expected_deployed_expert_sha256"],
            symbol=expected["expected_symbol"],
            period=expected["expected_period"],
            optimize=False,
            pass_count=None,
        )
        evidence["coreDisconnectObserved"] = True
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_tester_clean_completion_unverified",
        ):
            mt5._validate_tester_completion_evidence(
                evidence, expected_marker="thread_finished", **expected
            )

    def test_backtest_rejects_near_match_report_tab(self) -> None:
        self.fixture.prepare_compiled_binary()
        base_runner = self.fixture.runner

        def near_match(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            response = base_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                response = dict(response)
                response["reportTabName"] = "Backtest Results"
            return response

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=near_match,
        )
        request = self.fixture.request("backtest_recheck", "55")
        self.fixture.capability(request)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError, "visible_backtest_result_invalid"
        ):
            self.fixture.adapter.backtest_handler(request=request)

    def test_stop_start_transition_without_clean_log_evidence_fails_closed(self) -> None:
        self.fixture.prepare_compiled_binary()
        base_runner = self.fixture.runner

        def no_completion_evidence(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            response = base_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "backtest":
                response = dict(response)
                response["testerCompletionEvidence"] = None
            return response

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=no_completion_evidence,
        )
        request = self.fixture.request("backtest_recheck", "56")
        self.fixture.capability(request)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_tester_clean_completion_unverified",
        ):
            self.fixture.adapter.backtest_handler(request=request)

    def test_backtest_accepts_exact_native_disabled_bool_readback_normalization(self) -> None:
        self.fixture.prepare_compiled_binary()
        base_runner = self.fixture.runner

        def native_bool_readback(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = base_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload.get("action") == "backtest":
                readback = Path(payload["inputPresetReadbackSetPath"])
                source_text = Path(payload["inputPresetRef"]["path"]).read_text(
                    encoding="ascii"
                )
                native_text = source_text.replace(
                    "UseGuard=true||true||1||true||N",
                    "UseGuard=true||false||0||true||N",
                )
                self.assertNotEqual(native_text, source_text)
                readback.write_bytes(
                    ("; saved by MetaTrader 5\r\n" + native_text).encode("utf-16")
                )
                result["inputPresetReadbackSetSha256"] = sha256_bytes(
                    readback.read_bytes()
                )
            return result

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=native_bool_readback,
        )
        request = self.fixture.request("backtest_recheck", "51")
        self.fixture.capability(request)

        result = self.fixture.adapter.backtest_handler(request=request)

        self.assertTrue(result["metrics"]["backtestExecuted"])
        self.assertEqual(
            result["metrics"]["testerInputReadbackEntriesDigest"],
            request["mt5InputBinding"]["expectedReadbackEntriesDigest"],
        )

    def test_backtest_rejects_action_result_with_omitted_visual_mode_evidence(self) -> None:
        self.fixture.prepare_compiled_binary()
        base_runner = self.fixture.runner

        def omitted_visual_mode(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = base_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload.get("action") == "backtest":
                result = copy.deepcopy(result)
                result["automationControlsVerified"].pop("visualMode")
            return result

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=omitted_visual_mode,
        )
        request = self.fixture.request("backtest_recheck", "70")
        self.fixture.capability(request)

        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "visible_backtest_result_invalid",
        ):
            self.fixture.adapter.backtest_handler(request=request)

    def test_guarded_false_inputs_are_historical_test_only_and_set_bound(self) -> None:
        source_code = """input bool FundamentalCriteriaConfirmed=false;
input bool ExternalBenchmarkUptrendConfirmed=false;
input bool EnableTrading=false;
void OnTick()
{
   if(!FundamentalCriteriaConfirmed) return;
   if(ExternalBenchmarkUptrendConfirmed == false) { return; }
   if(!EnableTrading) return;
}
"""
        source_digest = sha256_bytes(source_code.encode("utf-8"))
        entries = []
        for ordinal, name in enumerate(
            (
                "FundamentalCriteriaConfirmed",
                "ExternalBenchmarkUptrendConfirmed",
                "EnableTrading",
            )
        ):
            entries.append(
                {
                    "ordinal": ordinal,
                    "qualifier": "input",
                    "declaredType": "bool",
                    "inputName": name,
                    "valueKind": "bool",
                    "setDefault": "false",
                    "enumValues": [],
                    "optimizable": True,
                }
            )
        manifest_core = {
            "schemaVersion": mt5.INPUT_MANIFEST_SCHEMA,
            "sourceDigest": source_digest,
            "entries": entries,
        }
        manifest = {
            **manifest_core,
            "manifestDigest": sha256_bytes(mt5._canonical_json(manifest_core)),
        }
        assumptions = [
            {
                "inputName": "FundamentalCriteriaConfirmed",
                "inputType": "bool",
                "sourceDefault": False,
                "testerValue": True,
                "reasonCode": "simulate_external_fundamental_confirmation_for_historical_test_only",
            },
            {
                "inputName": "ExternalBenchmarkUptrendConfirmed",
                "inputType": "bool",
                "sourceDefault": False,
                "testerValue": True,
                "reasonCode": "simulate_external_benchmark_uptrend_for_historical_test_only",
            },
            {
                "inputName": "EnableTrading",
                "inputType": "bool",
                "sourceDefault": False,
                "testerValue": False,
                "reasonCode": "reset_to_immutable_source_default_to_prevent_stale_tester_state",
            },
        ]
        preset_unsigned = {
            "schemaVersion": mt5.TESTER_INPUT_PRESET_SCHEMA,
            "mode": "full_immutable_source_snapshot_with_explicit_simulation_assumptions",
            "scope": "mt5_strategy_tester_only",
            "sourceDigest": source_digest,
            "inputManifestDigest": manifest["manifestDigest"],
            "assumptions": assumptions,
            "liveSourceDefaultsPreserved": True,
            "visibleExpertPropertiesRequired": True,
            "readbackRequired": True,
            "liveTradingAllowed": False,
            "fullCertifiedInputSnapshot": True,
            "simulationInputNames": [
                "FundamentalCriteriaConfirmed",
                "ExternalBenchmarkUptrendConfirmed",
            ],
        }
        preset = {
            **preset_unsigned,
            "presetDigest": sha256_bytes(mt5._canonical_json(preset_unsigned)),
        }
        validated = mt5._validate_tester_input_preset(
            preset, manifest, source_code
        )
        self.assertEqual(
            validated["simulationInputNames"],
            [
                "FundamentalCriteriaConfirmed",
                "ExternalBenchmarkUptrendConfirmed",
            ],
        )
        binding = {
            "inputManifestDigest": manifest["manifestDigest"],
            "expectedReadbackEntries": [
                {
                    "ordinal": ordinal,
                    "inputName": declared["inputName"],
                    "qualifier": declared["qualifier"],
                    "declaredType": declared["declaredType"],
                    "valueKind": declared["valueKind"],
                    "current": "true" if ordinal < 2 else "false",
                    "start": "true" if ordinal < 2 else "false",
                    "step": "1",
                    "stop": "true" if ordinal < 2 else "false",
                    "enabled": False,
                }
                for ordinal, declared in enumerate(entries)
            ],
        }
        mt5._validate_backtest_binding_against_manifest_and_preset(
            binding, manifest, preset
        )

        binding["expectedReadbackEntries"][0]["current"] = "false"
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError, "mt5_input_binding_invalid"
        ):
            mt5._validate_backtest_binding_against_manifest_and_preset(
                binding, manifest, preset
            )

    def test_simulation_guard_must_be_real_code_and_never_a_trading_switch(self) -> None:
        manifest = self.fixture.manifest()
        preset = self.fixture.tester_input_preset()
        source_code = self.fixture.source.read_text(encoding="utf-8")
        mt5._validate_tester_input_preset(preset, manifest, source_code)

        guarded_source = source_code.replace(
            "sinput bool UseGuard=true;",
            "sinput bool ExternalCriteriaConfirmed=false;\n"
            "// if(!ExternalCriteriaConfirmed) return;",
        )
        guarded_manifest = copy.deepcopy(manifest)
        guarded_manifest["sourceDigest"] = sha256_bytes(guarded_source.encode("utf-8"))
        guarded_manifest["entries"][2]["inputName"] = "ExternalCriteriaConfirmed"
        guarded_manifest["entries"][2]["setDefault"] = "false"
        guarded_core = {
            "schemaVersion": mt5.INPUT_MANIFEST_SCHEMA,
            "sourceDigest": guarded_manifest["sourceDigest"],
            "entries": guarded_manifest["entries"],
        }
        guarded_manifest["manifestDigest"] = sha256_bytes(
            mt5._canonical_json(guarded_core)
        )
        tampered = copy.deepcopy(preset)
        tampered["sourceDigest"] = guarded_manifest["sourceDigest"]
        tampered["inputManifestDigest"] = guarded_manifest["manifestDigest"]
        tampered["assumptions"][2]["inputName"] = "ExternalCriteriaConfirmed"
        tampered["assumptions"][2]["sourceDefault"] = False
        tampered["assumptions"][2]["testerValue"] = True
        tampered["assumptions"][2]["reasonCode"] = (
            "simulate_external_manual_confirmation_for_historical_test_only"
        )
        tampered["mode"] = (
            "full_immutable_source_snapshot_with_explicit_simulation_assumptions"
        )
        tampered["simulationInputNames"] = ["ExternalCriteriaConfirmed"]
        tampered_unsigned = {
            key: value for key, value in tampered.items() if key != "presetDigest"
        }
        tampered["presetDigest"] = sha256_bytes(
            mt5._canonical_json(tampered_unsigned)
        )
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError, "tester_input_preset_invalid"
        ):
            mt5._validate_tester_input_preset(
                tampered, guarded_manifest, guarded_source
            )

        forbidden_source = guarded_source.replace(
            "ExternalCriteriaConfirmed", "EnableTrading"
        )
        forbidden_manifest = copy.deepcopy(guarded_manifest)
        forbidden_manifest["sourceDigest"] = sha256_bytes(
            forbidden_source.encode("utf-8")
        )
        forbidden_manifest["entries"][2]["inputName"] = "EnableTrading"
        forbidden_core = {
            "schemaVersion": mt5.INPUT_MANIFEST_SCHEMA,
            "sourceDigest": forbidden_manifest["sourceDigest"],
            "entries": forbidden_manifest["entries"],
        }
        forbidden_manifest["manifestDigest"] = sha256_bytes(
            mt5._canonical_json(forbidden_core)
        )
        forbidden_preset = copy.deepcopy(tampered)
        forbidden_preset["sourceDigest"] = forbidden_manifest["sourceDigest"]
        forbidden_preset["inputManifestDigest"] = forbidden_manifest["manifestDigest"]
        forbidden_preset["assumptions"][2]["inputName"] = "EnableTrading"
        forbidden_preset["simulationInputNames"] = ["EnableTrading"]
        forbidden_unsigned = {
            key: value
            for key, value in forbidden_preset.items()
            if key != "presetDigest"
        }
        forbidden_preset["presetDigest"] = sha256_bytes(
            mt5._canonical_json(forbidden_unsigned)
        )
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError, "tester_input_preset_invalid"
        ):
            mt5._validate_tester_input_preset(
                forbidden_preset, forbidden_manifest, forbidden_source
            )

    def test_simulation_guard_must_be_active_ontick_before_entry(self) -> None:
        name = "ExternalCriteriaConfirmed"

        def guarded(source: str) -> bool:
            masked = mt5._mask_mql_comments_and_strings(source)
            self.assertIsNotNone(masked)
            return mt5._guarded_tester_simulation(masked, name)

        self.assertTrue(guarded(
            "void OnTick()\n"
            "{\n"
            "  ManageExistingPositions();\n"
            "  if(!ExternalCriteriaConfirmed) return;\n"
            "  SubmitEntry();\n"
            "}\n"
        ))
        self.assertFalse(guarded(
            "void Unused(){ if(!ExternalCriteriaConfirmed) return; }\n"
            "void OnTick(){}\n"
        ))
        self.assertFalse(guarded(
            "void OnTimer()\n"
            "{\n"
            "  if(!ExternalCriteriaConfirmed) return;\n"
            "}\n"
            "void OnTick(){}\n"
        ))
        self.assertFalse(guarded(
            "void OnTick()\n"
            "{\n"
            "#if 0\n"
            "  if(!ExternalCriteriaConfirmed) return;\n"
            "#endif\n"
            "}\n"
        ))
        self.assertFalse(guarded(
            "void OnTick()\n"
            "{\n"
            "  trade.Buy(0.1);\n"
            "  if(!ExternalCriteriaConfirmed) return;\n"
            "}\n"
        ))
        self.assertFalse(guarded(
            "void OnTick()\n"
            "{\n"
            "  if(DebugMode)\n"
            "    if(!ExternalCriteriaConfirmed) return;\n"
            "}\n"
        ))
        self.assertFalse(guarded(
            "void OnTick()\n"
            "{\n"
            "  trade.BuyStop(0.1, 1.2);\n"
            "  if(!ExternalCriteriaConfirmed) return;\n"
            "}\n"
        ))
        self.assertFalse(guarded(
            "bool OpenNewTrade(){ return trade.Buy(0.1); }\n"
            "void OnTick()\n"
            "{\n"
            "  OpenNewTrade();\n"
            "  if(!ExternalCriteriaConfirmed) return;\n"
            "}\n"
        ))
        self.assertFalse(guarded(
            "bool OpenNewTrade(){ MqlTradeRequest r={}; MqlTradeResult o={}; "
            "return OrderSend(r,o); }\n"
            "void OnTick()\n"
            "{\n"
            "  OpenNewTrade();\n"
            "  if(!ExternalCriteriaConfirmed) return;\n"
            "}\n"
        ))
        self.assertFalse(guarded(
            "void OnTick(){ if(!ExternalCriteriaConfirmed) return; }\n"
            "void OnTimer(){ trade.Buy(0.1); }\n"
        ))
        self.assertFalse(guarded(
            "void OnTick()\n"
            "{\n"
            "  if(\n"
            "    DebugMode)\n"
            "    if(!ExternalCriteriaConfirmed) return;\n"
            "}\n"
        ))
        self.assertTrue(guarded(
            "bool CloseExisting(ulong ticket){ MqlTradeRequest r={}; "
            "MqlTradeResult o={}; r.position=ticket; return OrderSend(r,o); }\n"
            "void OnTick()\n"
            "{\n"
            "  CloseExisting(1);\n"
            "  if(!ExternalCriteriaConfirmed) return;\n"
            "  SubmitEntry();\n"
            "}\n"
        ))

    def test_backtest_requires_original_source_input_manifest(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("backtest_recheck", "58")
        self.fixture.capability(request)
        request.pop("mt5InputManifest")
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError, "mt5_input_manifest_invalid"
        ):
            self.fixture.adapter.backtest_handler(request=request)

    def test_backtest_rejects_resigned_manifest_default_drift_from_source(
        self,
    ) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("backtest_recheck", "58ab")
        self.fixture.capability(request)
        manifest = copy.deepcopy(request["mt5InputManifest"])
        manifest["entries"][2]["setDefault"] = "false"
        core = {
            "schemaVersion": manifest["schemaVersion"],
            "sourceDigest": manifest["sourceDigest"],
            "entries": manifest["entries"],
        }
        manifest["manifestDigest"] = sha256_bytes(mt5._canonical_json(core))
        request["mt5InputManifest"] = manifest
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_input_manifest_source_mismatch",
        ):
            self.fixture.adapter.backtest_handler(request=request)

    def test_native_mt5_report_rejects_executable_script_even_with_valid_table(self) -> None:
        report = self.fixture.workspace / "native-mt5-report.htm"
        report.write_text(
            native_mt5_report_html(
                extra_head=(
                    '<script>document.addEventListener("DOMContentLoaded",()=>' 
                    'document.querySelector("table").remove())</script>'
                )
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError, "mt5_tester_report_html_invalid"
        ):
            mt5.verify_mt5_tester_report(
                {
                    "platform": "mt5",
                    "testerReportPath": report,
                    "resolvedTesterSettings": {
                        "expertFileName": "Strategy.ex5",
                        "symbol": "EURUSD",
                        "period": "H1",
                    },
                    "testerInputPreset": self.fixture.tester_input_preset(),
                }
            )

    def test_broker_branded_native_mt5_report_without_product_literal_is_accepted(self) -> None:
        report = self.fixture.workspace / "broker-native-mt5-report.htm"
        report.write_text(
            """<html><head><title>Strategy Tester Report</title>
            <meta name="generator" content="strategy tester"></head><body><table>
            <tr><td>Strategy Tester Report</td></tr>
            <tr><td>RoboForex-Pro (Build 6230)</td></tr>
            <tr><td>Settings</td></tr>
            <tr><td>Expert:</td><td>Strategy</td></tr>
            <tr><td>Symbol:</td><td>EURUSD</td></tr>
            <tr><td>Period:</td><td>H1 (2026.07.17 - 2026.10.14)</td></tr>
            <tr><td>Inputs:</td><td>RiskPercent=1; MaxTrades=1; UseGuard=true</td></tr>
            <tr><td>Results</td></tr>
            <tr><td>History Quality:</td><td>100%</td></tr>
            <tr><td>Bars:</td><td>1512</td><td>Ticks:</td><td>2811166</td>
                <td>Symbols:</td><td>0</td></tr>
            <tr><td>Balance Drawdown Absolute:</td><td>0.00</td>
                <td>Equity Drawdown Absolute:</td><td>0.00</td></tr>
            <tr><td>Balance Drawdown Maximal:</td><td>0.00 (0.00%)</td>
                <td>Equity Drawdown Maximal:</td><td>0.00 (0.00%)</td></tr>
            <tr><td>Balance Drawdown Relative:</td><td>0.00% (0.00)</td>
                <td>Equity Drawdown Relative:</td><td>0.00% (0.00)</td></tr>
            <tr><td>OnTester result:</td><td>0</td></tr>
            <tr><td>Total Trades:</td><td>0</td>
                <td>Short Trades (won %):</td><td>0 (0.00%)</td>
                <td>Long Trades (won %):</td><td>0 (0.00%)</td></tr>
            <tr><td>Total Deals:</td><td>0</td></tr>
            </table></body></html>""",
            encoding="utf-8",
        )
        verified = mt5.verify_mt5_tester_report(
            {
                "platform": "mt5",
                "testerReportPath": report,
                "resolvedTesterSettings": {
                    "expertFileName": "Strategy.ex5",
                    "symbol": "EURUSD",
                    "period": "H1",
                },
                "testerInputPreset": self.fixture.tester_input_preset(),
            }
        )
        self.assertTrue(verified["backtestVerified"])
        self.assertEqual(verified["tradeCount"], 0)

    def test_mt4_shaped_report_without_mt5_signature_is_rejected(self) -> None:
        report = self.fixture.workspace / "mt4-shaped-report.htm"
        report.write_text(
            """<html><body><table>
            <tr><td>Strategy Tester Report</td></tr>
            <tr><td>Broker-Demo (Build 1450)</td></tr>
            <tr><td>Expert:</td><td>Strategy</td></tr>
            <tr><td>Symbol:</td><td>EURUSD</td></tr>
            <tr><td>Period:</td><td>H1</td></tr>
            <tr><td>Inputs:</td><td>RiskPercent=1; MaxTrades=1; UseGuard=true</td></tr>
            <tr><td>Bars in test:</td><td>1512</td></tr>
            <tr><td>Ticks modelled:</td><td>2811166</td></tr>
            <tr><td>Modelling quality:</td><td>90.00%</td></tr>
            <tr><td>Total Trades:</td><td>0</td>
                <td>Short Trades (won %):</td><td>0 (0.00%)</td>
                <td>Long Trades (won %):</td><td>0 (0.00%)</td></tr>
            </table></body></html>""",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_tester_report_(?:identity_mismatch|html_invalid)",
        ):
            mt5.verify_mt5_tester_report(
                {
                    "platform": "mt5",
                    "testerReportPath": report,
                    "resolvedTesterSettings": {
                        "expertFileName": "Strategy.ex5",
                        "symbol": "EURUSD",
                        "period": "H1",
                    },
                    "testerInputPreset": self.fixture.tester_input_preset(),
                }
            )

    def test_broker_report_accepts_multiline_inputs_and_exact_date_binding(self) -> None:
        report = self.fixture.workspace / "broker-multiline-inputs.htm"
        report.write_text(
            native_mt5_report_html(period="H1 (2026.07.17 - 2026.10.14)").replace(
                "<tr><td>Inputs:</td><td>RiskPercent=1; MaxTrades=1; UseGuard=true</td></tr>",
                "<tr><td>Inputs:</td><td>RiskPercent=1</td></tr>"
                "<tr><td></td><td>MaxTrades=1</td></tr>"
                "<tr><td></td><td>UseGuard=true</td></tr>",
            ),
            encoding="utf-8",
        )
        context = {
            "platform": "mt5",
            "testerReportPath": report,
            "resolvedTesterSettings": {
                "expertFileName": "Strategy.ex5",
                "symbol": "EURUSD",
                "period": "H1",
                "useDate": True,
                "fromDate": "2026-07-17",
                "toDate": "2026-10-14",
            },
            "testerInputPreset": self.fixture.tester_input_preset(),
        }
        self.assertTrue(mt5.verify_mt5_tester_report(context)["backtestVerified"])
        context["resolvedTesterSettings"]["toDate"] = "2026-10-13"
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_tester_report_identity_mismatch",
        ):
            mt5.verify_mt5_tester_report(context)

    def test_mt4_script_and_secondary_label_bag_cannot_spoof_mt5_contract(self) -> None:
        report = self.fixture.workspace / "mt4-spoofed-as-mt5.htm"
        label_bag = """<table><tr><td>Settings</td></tr><tr><td>Results</td></tr>
        <tr><td>History Quality</td><td>100%</td></tr>
        <tr><td>Bars</td><td>1</td><td>Ticks</td><td>1</td><td>Symbols</td><td>1</td></tr>
        <tr><td>Balance Drawdown Absolute</td><td>0</td><td>Equity Drawdown Absolute</td><td>0</td></tr>
        <tr><td>Balance Drawdown Maximal</td><td>0 (0%)</td><td>Equity Drawdown Maximal</td><td>0 (0%)</td></tr>
        <tr><td>Balance Drawdown Relative</td><td>0% (0)</td><td>Equity Drawdown Relative</td><td>0% (0)</td></tr>
        <tr><td>OnTester result</td><td>0</td></tr><tr><td>Total Deals</td><td>0</td></tr></table>"""
        report.write_text(
            """<html><head><script>MetaTrader 5</script></head><body><table>
            <tr><td>Strategy Tester Report</td></tr><tr><td>Broker (Build 1450)</td></tr>
            <tr><td>Expert</td><td>Strategy</td></tr><tr><td>Symbol</td><td>EURUSD</td></tr>
            <tr><td>Period</td><td>H1</td></tr><tr><td>Parameters</td>
            <td>RiskPercent=1; MaxTrades=1; UseGuard=true</td></tr>
            <tr><td>Bars in test</td><td>10</td></tr><tr><td>Ticks modelled</td><td>10</td></tr>
            <tr><td>Modelling quality</td><td>90.00%</td></tr>
            <tr><td>Total Trades</td><td>0</td><td>Short Trades (won %)</td><td>0 (0%)</td>
            <td>Long Trades (won %)</td><td>0 (0%)</td></tr></table>"""
            + label_bag
            + "</body></html>",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_tester_report_(?:identity_mismatch|html_invalid)",
        ):
            mt5.verify_mt5_tester_report(
                {
                    "platform": "mt5",
                    "testerReportPath": report,
                    "resolvedTesterSettings": {
                        "expertFileName": "Strategy.ex5",
                        "symbol": "EURUSD",
                        "period": "H1",
                    },
                    "testerInputPreset": self.fixture.tester_input_preset(),
                }
            )

    def test_mt5_contract_rejects_identity_prefix_duplicate_and_spoof_rows(self) -> None:
        report = self.fixture.workspace / "invalid-mt5-identity.htm"
        context = {
            "platform": "mt5",
            "testerReportPath": report,
            "resolvedTesterSettings": {
                "expertFileName": "Strategy.ex5",
                "symbol": "EURUSD",
                "period": "H1",
            },
            "testerInputPreset": self.fixture.tester_input_preset(),
        }
        cases = {
            "expert_prefix": native_mt5_report_html(expert="Strategy Old"),
            "symbol_suffix": native_mt5_report_html(symbol="EURUSDm"),
            "period_prefix": native_mt5_report_html(period="H12"),
            "period_arbitrary_suffix": native_mt5_report_html(period="H1 current"),
            "duplicate_expert": native_mt5_report_html().replace(
                "<tr><td>Expert:</td><td>Strategy</td></tr>",
                "<tr><td>Expert:</td><td>Strategy</td></tr>"
                "<tr><td>Expert:</td><td>WrongStrategy</td></tr>",
            ),
            "embedded_conflicting_expert": native_mt5_report_html().replace(
                "<tr><td>Results</td></tr>",
                "<tr><td>Results</td></tr>"
                "<tr><td>Other</td><td>x</td><td>Expert</td><td>WrongStrategy</td></tr>",
            ),
            "script_identity_spoof": native_mt5_report_html(
                expert="WrongStrategy",
                extra_head="<script>Expert: Strategy Symbol: EURUSD Period: H1</script>",
            ),
        }
        for name, payload in cases.items():
            with self.subTest(name=name):
                report.write_text(payload, encoding="utf-8")
                with self.assertRaisesRegex(
                    mt5.VisibleTerminalAdapterError,
                    "mt5_tester_report_(?:identity_mismatch|html_invalid)",
                ):
                    mt5.verify_mt5_tester_report(context)

    def test_mt5_contract_rejects_hidden_missing_duplicate_and_reordered_evidence(self) -> None:
        report = self.fixture.workspace / "invalid-mt5-structure.htm"
        context = {
            "platform": "mt5",
            "testerReportPath": report,
            "resolvedTesterSettings": {
                "expertFileName": "Strategy.ex5",
                "symbol": "EURUSD",
                "period": "H1",
            },
            "testerInputPreset": self.fixture.tester_input_preset(),
        }
        base = native_mt5_report_html()
        cases = {
            "missing_metric": base.replace("History Quality:", "History Quality Missing:"),
            "malformed_metric": base.replace("<td>100%</td>", "<td>101%</td>", 1),
            "duplicate_metric": base.replace(
                "<tr><td>Total Deals:</td><td>4</td></tr>",
                "<tr><td>Total Deals:</td><td>4</td></tr>"
                "<tr><td>Total Deals:</td><td>4</td></tr>",
            ),
            "mt4_marker": base.replace(
                "<tr><td>Results</td></tr>",
                "<tr><td>Results</td></tr><tr><td>Bars in test:</td><td>1</td></tr>",
            ),
            "wrong_order": base.replace(
                "<tr><td>Settings</td></tr>", "<tr><td>Settings Moved</td></tr>",
            ).replace(
                "<tr><td>Results</td></tr>",
                "<tr><td>Settings</td></tr><tr><td>Results</td></tr>",
            ),
            "hidden_required_metric": base.replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr hidden><td>History Quality:</td><td>100%</td></tr>',
            ),
            "aria_hidden_required_metric": base.replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr aria-hidden="true"><td>History Quality:</td><td>100%</td></tr>',
            ),
            "css_hidden_required_metric": base.replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr style="display: none"><td>History Quality:</td><td>100%</td></tr>',
            ),
            "unquoted_opacity_required_metric": base.replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr style=opacity:0><td>History Quality:</td><td>100%</td></tr>',
            ),
            "unquoted_filter_required_metric": base.replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr style=filter:opacity(0)><td>History Quality:</td><td>100%</td></tr>',
            ),
            "escaped_opacity_required_metric": base.replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr style="opac\\69ty:0"><td>History Quality:</td><td>100%</td></tr>',
            ),
            "scale_zero_required_metric": base.replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr style="scale:0"><td>History Quality:</td><td>100%</td></tr>',
            ),
            "zoom_zero_required_metric": base.replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr style="zoom:0"><td>History Quality:</td><td>100%</td></tr>',
            ),
            "closed_details_main_table": "<html><body><details>" + base.split(
                "<body>", 1
            )[1].split("</body>", 1)[0] + "</details></body></html>",
            "closed_dialog_main_table": "<html><body><dialog>" + base.split(
                "<body>", 1
            )[1].split("</body>", 1)[0] + "</dialog></body></html>",
            **{
                f"non_rendered_{tag}_main_table": (
                    f"<html><body><{tag}>"
                    + base.split("<body>", 1)[1].split("</body>", 1)[0]
                    + f"</{tag}></body></html>"
                )
                for tag in (
                    "iframe", "canvas", "object", "textarea", "select",
                    "datalist", "video", "audio",
                )
            },
            "double_encoded_required_label": base.replace(
                "History Quality:", "History Quality&amp;colon;", 1
            ),
            "black_background_required_row": base.replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr bgcolor="#000000"><td>History Quality:</td><td>100%</td></tr>',
            ),
            "huge_colspan_required_value": base.replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr><td>History Quality:</td><td colspan="999999999">100%</td></tr>',
            ),
            "huge_table_spacing": base.replace(
                "<body><table>", '<body><table cellspacing="999999999">', 1
            ),
            "second_main_table": base.replace(
                "</body>",
                "<table><tr><td>Strategy Tester Report</td></tr></table></body>",
            ),
        }
        for name, payload in cases.items():
            with self.subTest(name=name):
                report.write_text(payload, encoding="utf-8")
                with self.assertRaisesRegex(
                    mt5.VisibleTerminalAdapterError,
                    "mt5_tester_report_(?:identity_mismatch|html_invalid)",
                ):
                    mt5.verify_mt5_tester_report(context)

    def test_mt5_contract_never_uses_product_literal_or_out_of_table_preset(self) -> None:
        report = self.fixture.workspace / "invalid-mt5-external-evidence.htm"
        context = {
            "platform": "mt5",
            "testerReportPath": report,
            "resolvedTesterSettings": {
                "expertFileName": "Strategy.ex5",
                "symbol": "EURUSD",
                "period": "H1",
            },
            "testerInputPreset": self.fixture.tester_input_preset(),
        }
        incomplete = """<html><body><h1>MetaTrader 5</h1><table>
        <tr><td>Strategy Tester Report</td></tr><tr><td>Broker (Build 6230)</td></tr>
        <tr><td>Settings</td></tr><tr><td>Expert</td><td>Strategy</td></tr>
        <tr><td>Symbol</td><td>EURUSD</td></tr><tr><td>Period</td><td>H1</td></tr>
        <tr><td>Inputs</td><td>RiskPercent=1; MaxTrades=1; UseGuard=true</td></tr>
        <tr><td>Results</td></tr></table></body></html>"""
        report.write_text(incomplete, encoding="utf-8")
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_tester_report_(?:identity_mismatch|html_invalid)",
        ):
            mt5.verify_mt5_tester_report(context)

        for name, (payload, error_code) in {
            "script": (native_mt5_report_html(
                inputs="RiskPercent=9; MaxTrades=9; UseGuard=false",
                extra_head=(
                    "<script>Inputs: RiskPercent=1; MaxTrades=1; "
                    "UseGuard=true</script>"
                ),
            ), "mt5_tester_report_html_invalid"),
            "secondary_table": (native_mt5_report_html(
                inputs="RiskPercent=9; MaxTrades=9; UseGuard=false",
                secondary_tables=(
                    "<table><tr><td>Inputs</td><td>RiskPercent=1; "
                    "MaxTrades=1; UseGuard=true</td></tr></table>"
                ),
            ), "mt5_tester_report_identity_mismatch"),
        }.items():
            with self.subTest(name=name):
                report.write_text(payload, encoding="utf-8")
                with self.assertRaisesRegex(
                    mt5.VisibleTerminalAdapterError,
                    error_code,
                ):
                    mt5.verify_mt5_tester_report(context)

    def test_mt5_contract_accepts_bound_shape_with_compact_or_future_build_heading(self) -> None:
        report = self.fixture.workspace / "native-mt5-build-heading.htm"
        context = {
            "platform": "mt5",
            "testerReportPath": report,
            "resolvedTesterSettings": {
                "expertFileName": "Strategy.ex5",
                "symbol": "EURUSD",
                "period": "H1",
            },
            "testerInputPreset": self.fixture.tester_input_preset(),
        }
        for heading in ("RoboForex-Pro(Build 6230)", "FutureBroker (Build 7000)"):
            with self.subTest(heading=heading):
                payload = native_mt5_report_html().replace(
                    "RoboForex-Pro (Build 6230)", heading
                )
                report.write_text(payload, encoding="utf-8")
                self.assertTrue(
                    mt5.verify_mt5_tester_report(context)["backtestVerified"]
                )

    def test_mt5_contract_enforces_global_proof_uniqueness(self) -> None:
        report = self.fixture.workspace / "duplicate-mt5-proof.htm"
        context = {
            "platform": "mt5",
            "testerReportPath": report,
            "resolvedTesterSettings": {
                "expertFileName": "Strategy.ex5",
                "symbol": "EURUSD",
                "period": "H1",
            },
            "testerInputPreset": self.fixture.tester_input_preset(),
        }
        cases = {
            "identity_after_results": native_mt5_report_html(
                extra_main_rows="<tr><td>Expert</td><td>WrongStrategy</td></tr>"
            ),
            "metric_before_results": native_mt5_report_html().replace(
                "<tr><td>Results</td></tr>",
                "<tr><td>Total Deals</td><td>4</td></tr>"
                "<tr><td>Results</td></tr>",
            ),
            "identity_in_secondary_table": native_mt5_report_html(
                secondary_tables=(
                    "<table><tr><td>Expert</td><td>WrongStrategy</td></tr></table>"
                )
            ),
            "metric_in_secondary_table": native_mt5_report_html(
                secondary_tables=(
                    "<table><tr><td>Total Trades</td><td>999</td></tr></table>"
                )
            ),
        }
        for name, payload in cases.items():
            with self.subTest(name=name):
                report.write_text(payload, encoding="utf-8")
                with self.assertRaisesRegex(
                    mt5.VisibleTerminalAdapterError,
                    "mt5_tester_report_identity_mismatch",
                ):
                    mt5.verify_mt5_tester_report(context)

    def test_mt5_trade_summary_accepts_canonical_space_grouping(self) -> None:
        report = self.fixture.workspace / "space-grouped-mt5-report.htm"
        report.write_text(
            native_mt5_report_html(
                trades="1 000",
                short_trades="500",
                long_trades="500",
                total_deals="2 000",
            ),
            encoding="utf-8",
        )
        verified = mt5.verify_mt5_tester_report(
            {
                "platform": "mt5",
                "testerReportPath": report,
                "resolvedTesterSettings": {
                    "expertFileName": "Strategy.ex5",
                    "symbol": "EURUSD",
                    "period": "H1",
                },
                "testerInputPreset": self.fixture.tester_input_preset(),
            }
        )
        self.assertEqual(verified["tradeCount"], 1_000)
        self.assertEqual(verified["buyTradeCount"], 500)
        self.assertEqual(verified["sellTradeCount"], 500)

    def test_mt5_contract_rejects_css_hidden_and_malformed_numeric_proof(self) -> None:
        report = self.fixture.workspace / "invalid-mt5-proof-value.htm"
        context = {
            "platform": "mt5",
            "testerReportPath": report,
            "resolvedTesterSettings": {
                "expertFileName": "Strategy.ex5",
                "symbol": "EURUSD",
                "period": "H1",
            },
            "testerInputPreset": self.fixture.tester_input_preset(),
        }
        base = native_mt5_report_html()
        cases = {
            "css_class_hidden": (base.replace(
                "<head><title>Strategy Tester Report</title>",
                "<head><title>Strategy Tester Report</title>"
                "<style>.proof-hidden { display: none; }</style>",
            ).replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr class="proof-hidden"><td>History Quality:</td><td>100%</td></tr>',
            ), "mt5_tester_report_html_invalid"),
            "css_class_opacity_zero": (base.replace(
                "<head><title>Strategy Tester Report</title>",
                "<head><title>Strategy Tester Report</title>"
                "<style>.proof { opacity: 0; }</style>",
            ).replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr class="proof"><td>History Quality:</td><td>100%</td></tr>',
            ), "mt5_tester_report_html_invalid"),
            "css_escaped_property": (base.replace(
                "<head><title>Strategy Tester Report</title>",
                "<head><title>Strategy Tester Report</title>"
                "<style>.proof { opac\\69ty: 0; }</style>",
            ).replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr class="proof"><td>History Quality:</td><td>100%</td></tr>',
            ), "mt5_tester_report_html_invalid"),
            "css_tiny_font": (base.replace(
                "<head><title>Strategy Tester Report</title>",
                "<head><title>Strategy Tester Report</title>"
                "<style>.proof { font: 0.0001px Arial; }</style>",
            ).replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr class="proof"><td>History Quality:</td><td>100%</td></tr>',
            ), "mt5_tester_report_html_invalid"),
            "css_symbol_font": (base.replace(
                "<head><title>Strategy Tester Report</title>",
                "<head><title>Strategy Tester Report</title>"
                "<style>.proof { font: 10pt Wingdings; }</style>",
            ).replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr class="proof"><td>History Quality:</td><td>100%</td></tr>',
            ), "mt5_tester_report_html_invalid"),
            "inline_zero_line_height": (base.replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr><td style="font:10pt/0 Arial">History Quality:</td>'
                '<td>100%</td></tr>',
            ), "mt5_tester_report_html_invalid"),
            "inline_tiny_line_height": (base.replace(
                "<tr><td>History Quality:</td><td>100%</td></tr>",
                '<tr><td style="font:6px/0.0001px Arial">History Quality:</td>'
                '<td>100%</td></tr>',
            ), "mt5_tester_report_html_invalid"),
            "malformed_grouping": (base.replace(
                "<td>Bars:</td><td>1512</td>",
                "<td>Bars:</td><td>1, ,</td>",
            ), "mt5_tester_report_identity_mismatch"),
            "mixed_grouping": (base.replace(
                "<td>Bars:</td><td>1512</td>",
                "<td>Bars:</td><td>1,000 000</td>",
            ), "mt5_tester_report_identity_mismatch"),
            "negative_drawdown": (base.replace(
                "<td>Balance Drawdown Absolute:</td><td>0.00</td>",
                "<td>Balance Drawdown Absolute:</td><td>-1.00</td>",
            ), "mt5_tester_report_identity_mismatch"),
        }
        for name, (payload, error_code) in cases.items():
            with self.subTest(name=name):
                report.write_text(payload, encoding="utf-8")
                with self.assertRaisesRegex(
                    mt5.VisibleTerminalAdapterError,
                    error_code,
                ):
                    mt5.verify_mt5_tester_report(context)

    def test_html_report_parser_rejects_malformed_suppression_and_overflow(self) -> None:
        report = self.fixture.workspace / "invalid-mt5-html.htm"
        proof = native_mt5_report_html()
        cases = {
            "closing_void_escape": (
                "<html><body><div hidden><br></br>" + proof + "</div></body></html>"
            ),
            "mismatched_suppression": (
                "<html><body><div hidden></span>" + proof + "</div></body></html>"
            ),
            "proof_table_inside_body_title": (
                "<html><head><title>Report</title></head><body><title>"
                + proof.split("<body>", 1)[1].split("</body>", 1)[0]
                + "</title></body></html>"
            ),
            "cell_overflow": (
                "<html><body><table><tr>"
                + ("<td>x</td>" * 97)
                + "</tr></table></body></html>"
            ),
            "table_overflow": (
                "<html><body>" + ("<table><tr><td>x</td></tr></table>" * 129)
                + "</body></html>"
            ),
            "row_overflow": (
                "<html><body><table>"
                + ("<tr><td>x</td></tr>" * 10_001)
                + "</table></body></html>"
            ),
        }
        for name, payload in cases.items():
            with self.subTest(name=name):
                report.write_text(payload, encoding="utf-8")
                with self.assertRaisesRegex(
                    mt5.VisibleTerminalAdapterError,
                    "mt5_tester_report_html_invalid",
                ):
                    mt5._html_report_evidence(report)

    def test_native_mt5_trade_summary_rejects_duplicate_or_unbalanced_totals(self) -> None:
        report = self.fixture.workspace / "invalid-native-mt5-report.htm"
        context = {
            "platform": "mt5",
            "testerReportPath": report,
            "resolvedTesterSettings": {
                "expertFileName": "Strategy.ex5",
                "symbol": "EURUSD",
                "period": "H1",
            },
            "testerInputPreset": self.fixture.tester_input_preset(),
        }
        common = native_mt5_report_html().replace(
            '<tr><td>Total Trades:</td><td>2</td>\n'
            '        <td>Short Trades (won %):</td><td>1 (0.00%)</td>\n'
            '        <td>Long Trades (won %):</td><td>1 (0.00%)</td></tr>',
            "{summary}",
        )
        cases = (
            (
                "<tr><td>Total Trades</td><td>2</td>"
                "<td>Short Trades (won %)</td><td>1 (50.00%)</td>"
                "<td>Long Trades (won %)</td><td>1 (50.00%)</td></tr>"
                "<tr><td>Total Trades</td><td>2</td></tr>",
                "mt5_tester_report_identity_mismatch",
            ),
            (
                "<tr><td>Total Trades</td><td>3</td>"
                "<td>Short Trades (won %)</td><td>1 (50.00%)</td>"
                "<td>Long Trades (won %)</td><td>1 (50.00%)</td></tr>",
                "mt5_tester_report_trade_rows_mismatch",
            ),
        )
        for summary, error_code in cases:
            with self.subTest(error_code=error_code):
                report.write_text(common.format(summary=summary), encoding="utf-8")
                with self.assertRaisesRegex(
                    mt5.VisibleTerminalAdapterError, error_code
                ):
                    mt5.verify_mt5_tester_report(context)

    def test_catalog_refresh_boundary_and_evidence_are_durable_and_tamper_evident(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "38")
        self.fixture.runner.expert_catalog_refresh_attempted = True
        self.fixture.capability(request)
        result = self.fixture.adapter.optimization_handler(request=request)
        evidence = result["metrics"]["expertCatalogRefreshEvidence"]
        self.assertTrue(evidence["attempted"])
        self.assertFalse(evidence["recoveredAfterBoundary"])
        self.assertEqual(evidence["commandCount"], 1)
        self.assertEqual(evidence["commandName"], "Refresh")
        self.assertEqual(evidence["navigatorPaneAutomationId"], "32845")
        self.assertEqual(evidence["navigatorTreeAutomationId"], "10064")
        self.assertIsNone(evidence["refreshMenuAutomationId"])
        self.assertEqual(evidence["refreshMenuProvider"], "native_hmenu")
        self.assertEqual(evidence["refreshMenuWindowClass"], "#32768")
        self.assertEqual(evidence["refreshMenuNativeCommandId"], 33416)
        self.assertEqual(evidence["refreshMenuDispatchMethod"], "targeted_menu_keyboard")
        self.assertEqual(evidence["idleStateImmediatelyBeforeRefresh"], "Start")
        self.assertEqual(evidence["terminalProcessId"], 101)
        self.assertEqual(evidence["terminalWindowHandle"], 10101)
        self.assertEqual(
            evidence["algoTradingStateBefore"], evidence["algoTradingStateAfter"]
        )
        self.assertRegex(evidence["boundarySha256"], r"^[0-9a-f]{64}$")
        summaries = self.fixture.workspace / "Summaries"
        refresh_boundary = next(
            summaries.glob("*-optimization-expert-catalog-refresh-boundary.json")
        )
        receipt_path = self.fixture.workspace / next(
            item["relativePath"]
            for item in result["artifactSpecifications"]
            if item["alias"] == "adapter_receipt"
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(
            receipt["expertCatalogRefreshBoundarySha256"],
            sha256_bytes(refresh_boundary.read_bytes()),
        )
        actions_before_recovery = list(self.fixture.runner.actions)
        recovered = self.fixture.adapter.optimization_handler(request=request)
        self.assertTrue(recovered["metrics"]["recoveredExistingReceipt"])
        self.assertFalse(recovered["metrics"]["optimizationExecuted"])
        self.assertEqual(self.fixture.runner.actions, actions_before_recovery)
        receipt_bytes = receipt_path.read_bytes()
        tampered_receipt = json.loads(receipt_bytes.decode("utf-8"))
        tampered_receipt["expertCatalogRefreshEvidence"]["terminalProcessId"] = 999
        receipt_path.write_bytes(mt5._canonical_json(tampered_receipt))
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_expert_catalog_refresh_evidence_invalid",
        ):
            self.fixture.adapter.optimization_handler(request=request)
        receipt_path.write_bytes(receipt_bytes)
        refresh_boundary.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_expert_catalog_refresh_boundary_(?:invalid|mismatch)",
        ):
            self.fixture.adapter.optimization_handler(request=request)

    def test_durable_boundary_retry_collects_without_second_start(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("backtest_recheck", "3")
        self.fixture.capability(request)
        self.fixture.runner.fail_after_first_boundary = True
        with self.assertRaisesRegex(RuntimeError, "simulated_ui_disconnect"):
            self.fixture.adapter.backtest_handler(request=request)
        result = self.fixture.adapter.backtest_handler(request=request)
        self.assertEqual(
            [action for action in self.fixture.runner.actions if action not in {"probe", "post_probe"}],
            ["backtest", "collect_backtest"],
        )
        self.assertTrue(result["metrics"]["recoveredWithoutStart"])
        self.assertFalse(result["metrics"]["backtestExecuted"])
        self.assertFalse(result["metrics"]["startInvoked"])

    def test_boundary_without_dispatch_fails_closed_without_second_runner_invocation(
        self,
    ) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("backtest_recheck", "58")
        self.fixture.capability(request)
        self.fixture.runner.fail_after_boundary_before_dispatch = True

        with self.assertRaisesRegex(
            RuntimeError,
            "simulated_disconnect_after_post_before_dispatch_receipt",
        ):
            self.fixture.adapter.backtest_handler(request=request)

        summaries = self.fixture.workspace / "Summaries"
        boundary = next(summaries.glob("*-backtest-start-boundary.json"))
        dispatch = Path(str(boundary) + ".dispatch-confirmed")
        self.assertFalse(dispatch.exists())
        self.assertEqual(self.fixture.runner.tester_start_dispatch_count, 1)
        actions_before = list(self.fixture.runner.actions)

        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "tester_start_dispatch_unconfirmed",
        ):
            self.fixture.adapter.backtest_handler(request=request)

        self.assertEqual(self.fixture.runner.actions, actions_before)
        self.assertEqual(self.fixture.runner.tester_start_dispatch_count, 1)
        self.assertFalse(dispatch.exists())

    def test_boundary_without_dispatch_rejects_preexisting_result_checkpoint(
        self,
    ) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("backtest_recheck", "59")
        self.fixture.capability(request)
        self.fixture.runner.fail_after_boundary_before_dispatch = True
        with self.assertRaisesRegex(RuntimeError, "before_dispatch_receipt"):
            self.fixture.adapter.backtest_handler(request=request)
        result_path = next(
            (self.fixture.workspace / "Screenshots").glob(
                "*-backtest-result.png"
            ),
            None,
        )
        if result_path is None:
            result_path = (
                self.fixture.workspace
                / "Screenshots"
                / "forged-backtest-result.png"
            )
            # Use the exact operation path from the failed request payload.
            start_payload = next(
                payload
                for payload in reversed(self.fixture.runner.payloads)
                if payload.get("action") == "backtest"
            )
            result_path = Path(start_payload["resultScreenshotPath"])
        result_path.write_bytes(png_bytes())
        actions_before = list(self.fixture.runner.actions)

        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "tester_start_dispatch_unconfirmed",
        ):
            self.fixture.adapter.backtest_handler(request=request)

        self.assertEqual(self.fixture.runner.actions, actions_before)
        self.assertEqual(self.fixture.runner.tester_start_dispatch_count, 1)

    def test_boundary_without_dispatch_never_recovers_optimization(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "5a")
        self.fixture.capability(request)
        self.fixture.runner.fail_after_boundary_before_dispatch = True
        with self.assertRaisesRegex(RuntimeError, "before_dispatch_receipt"):
            self.fixture.adapter.optimization_handler(request=request)
        actions_before = list(self.fixture.runner.actions)

        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "tester_start_dispatch_unconfirmed",
        ):
            self.fixture.adapter.optimization_handler(request=request)

        self.assertEqual(self.fixture.runner.actions, actions_before)
        self.assertEqual(self.fixture.runner.tester_start_dispatch_count, 1)

    def test_completed_idle_backtest_recovers_report_without_second_start(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("backtest_recheck", "53")
        self.fixture.capability(request)
        self.fixture.runner.fail_after_result_checkpoint = True
        with self.assertRaisesRegex(
            RuntimeError, "simulated_disconnect_after_result_checkpoint"
        ):
            self.fixture.adapter.backtest_handler(request=request)
        screenshots = self.fixture.workspace / "Screenshots"
        settings_path = next(screenshots.glob("*-backtest-settings.png"))
        result_path = next(screenshots.glob("*-backtest-result.png"))
        settings_before = (
            sha256_bytes(settings_path.read_bytes()),
            settings_path.stat().st_mtime_ns,
        )
        result_before = (
            sha256_bytes(result_path.read_bytes()),
            result_path.stat().st_mtime_ns,
        )

        result = self.fixture.adapter.backtest_handler(request=request)

        actions = [
            action for action in self.fixture.runner.actions if action not in {"probe", "post_probe"}
        ]
        self.assertEqual(actions, ["backtest", "recover_completed_backtest"])
        recovery_payload = next(
            payload
            for payload in reversed(self.fixture.runner.payloads)
            if payload.get("action") == "recover_completed_backtest"
        )
        self.assertTrue(recovery_payload["neverStart"])
        self.assertEqual(recovery_payload["serviceAction"], "recover_round")
        metrics = result["metrics"]
        self.assertTrue(metrics["recoveredWithoutStart"])
        self.assertFalse(metrics["startInvoked"])
        self.assertFalse(metrics["backtestExecuted"])
        self.assertFalse(metrics["executionObservedRunning"])
        self.assertTrue(metrics["completedResultCheckpointReused"])
        self.assertFalse(metrics["completedReportCheckpointReused"])
        self.assertFalse(metrics["recoveryIssuedStart"])
        self.assertEqual(
            metrics["testerCompletionObservation"],
            "recovery_completed_checkpoint_observed",
        )
        self.assertEqual(
            metrics["testerRunTransitionEvidence"],
            "completed_result_checkpoint_after_dispatch",
        )
        self.assertEqual(
            settings_before,
            (sha256_bytes(settings_path.read_bytes()), settings_path.stat().st_mtime_ns),
        )
        self.assertEqual(
            result_before,
            (sha256_bytes(result_path.read_bytes()), result_path.stat().st_mtime_ns),
        )
        self.assertEqual(
            len(
                [
                    action
                    for action in self.fixture.runner.actions
                    if action in {"backtest", "optimize"}
                ]
            ),
            1,
        )
        self.assertEqual(self.fixture.runner.tester_start_dispatch_count, 1)
        self.assertTrue(
            any(
                (self.fixture.workspace / "Summaries").glob(
                    "*-backtest-tester-completion-evidence.json"
                )
            )
        )

    def test_completed_backtest_recovery_rejects_checkpoint_changed_during_call(
        self,
    ) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("backtest_recheck", "54")
        self.fixture.capability(request)
        self.fixture.runner.fail_after_result_checkpoint = True
        with self.assertRaisesRegex(
            RuntimeError, "simulated_disconnect_after_result_checkpoint"
        ):
            self.fixture.adapter.backtest_handler(request=request)
        self.fixture.runner.mutate_completed_result_checkpoint = True

        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_tester_recovery_checkpoint_mismatch",
        ):
            self.fixture.adapter.backtest_handler(request=request)

        actions = [
            action for action in self.fixture.runner.actions if action not in {"probe", "post_probe"}
        ]
        self.assertEqual(actions, ["backtest", "recover_completed_backtest"])
        recovery_payload = next(
            payload
            for payload in reversed(self.fixture.runner.payloads)
            if payload.get("action") == "recover_completed_backtest"
        )
        self.assertTrue(recovery_payload["neverStart"])
        self.assertEqual(recovery_payload["serviceAction"], "recover_round")
        self.assertEqual(self.fixture.runner.tester_start_dispatch_count, 1)
        self.assertFalse(
            any(
                (self.fixture.workspace / "Summaries").glob(
                    "*-backtest-receipt.json"
                )
            )
        )

    def test_recovery_rejects_semantically_equal_rewritten_start_boundary(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("backtest_recheck", "49")
        self.fixture.capability(request)
        self.fixture.runner.fail_after_first_boundary = True
        with self.assertRaisesRegex(RuntimeError, "simulated_ui_disconnect"):
            self.fixture.adapter.backtest_handler(request=request)
        boundary = next(
            (self.fixture.workspace / "Summaries").glob("*-start-boundary.json")
        )
        payload = json.loads(boundary.read_text(encoding="utf-8"))
        boundary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        actions_before = list(self.fixture.runner.actions)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "tester_start_boundary_mismatch",
        ):
            self.fixture.adapter.backtest_handler(request=request)
        self.assertEqual(self.fixture.runner.actions, actions_before)

    def test_recovery_rejects_hardlinked_start_boundary_and_dispatch(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "50")
        self.fixture.capability(request)
        self.fixture.runner.fail_after_first_boundary = True
        with self.assertRaisesRegex(RuntimeError, "simulated_ui_disconnect"):
            self.fixture.adapter.optimization_handler(request=request)
        boundary = next(
            (self.fixture.workspace / "Summaries").glob("*-start-boundary.json")
        )
        boundary_bytes = boundary.read_bytes()
        dispatch = Path(str(boundary) + ".dispatch-confirmed")
        boundary_alias = boundary.with_name("start-boundary-hardlink.json")
        try:
            os.link(boundary, boundary_alias)
        except OSError as error:
            self.skipTest(f"hard links unavailable: {error}")
        actions_before = list(self.fixture.runner.actions)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "tester_start_boundary_mismatch",
        ):
            self.fixture.adapter.optimization_handler(request=request)
        self.assertEqual(self.fixture.runner.actions, actions_before)
        boundary_alias.unlink()
        boundary.write_bytes(boundary_bytes)
        dispatch_alias = dispatch.with_name("dispatch-hardlink.dispatch-confirmed")
        os.link(dispatch, dispatch_alias)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "tester_start_dispatch_unconfirmed",
        ):
            self.fixture.adapter.optimization_handler(request=request)
        self.assertEqual(self.fixture.runner.actions, actions_before)

    def test_refresh_boundary_retry_never_dispatches_refresh_twice(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "39")
        self.fixture.runner.expert_catalog_refresh_attempted = True
        self.fixture.runner.fail_after_first_refresh_boundary = True
        self.fixture.capability(request)
        with self.assertRaisesRegex(
            RuntimeError, "simulated_ui_disconnect_after_refresh_boundary"
        ):
            self.fixture.adapter.optimization_handler(request=request)
        summaries = self.fixture.workspace / "Summaries"
        refresh_boundaries = list(
            summaries.glob("*-optimization-expert-catalog-refresh-boundary.json")
        )
        self.assertEqual(len(refresh_boundaries), 1)
        self.assertEqual(self.fixture.runner.expert_catalog_refresh_dispatch_count, 1)
        self.assertEqual(
            list(summaries.glob("*-optimization-start-boundary.json")), []
        )
        result = self.fixture.adapter.optimization_handler(request=request)
        self.assertEqual(self.fixture.runner.expert_catalog_refresh_dispatch_count, 1)
        self.assertEqual(
            [action for action in self.fixture.runner.actions if action not in {"probe", "post_probe"}],
            ["optimize", "optimize"],
        )
        evidence = result["metrics"]["expertCatalogRefreshEvidence"]
        self.assertTrue(evidence["attempted"])
        self.assertTrue(evidence["recoveredAfterBoundary"])
        self.assertEqual(evidence["commandCount"], 1)
        self.assertEqual(evidence["matchCountAfter"], 1)

    def test_never_start_without_boundary_fails_before_start_capable_action(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "30")
        request["safety"]["neverStart"] = True
        request["safety"]["serviceAction"] = "collect_round"
        self.fixture.capability(request)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_tester_recovery_state_uncertain",
        ):
            self.fixture.adapter.optimization_handler(request=request)
        self.assertNotIn("optimize", self.fixture.runner.actions)
        self.assertNotIn("collect_optimization", self.fixture.runner.actions)

    def test_never_start_must_be_an_exact_boolean(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("backtest_recheck", "31")
        request["safety"]["neverStart"] = 1
        request["safety"]["serviceAction"] = "collect_round"
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "visible_request_safety_invalid",
        ):
            self.fixture.adapter.backtest_handler(request=request)
        self.assertEqual(self.fixture.runner.actions, [])

    def test_optimization_requires_dynamic_service_safety_pair(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "34")
        request["safety"].pop("neverStart")
        request["safety"].pop("serviceAction")
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "visible_request_safety_invalid",
        ):
            self.fixture.adapter.optimization_handler(request=request)
        self.assertEqual(self.fixture.runner.actions, [])

    def test_durable_dispatch_confirmation_does_not_expire_by_age(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "dispatch-confirmed.json"
            operation_id = "ea-visible-" + ("d" * 24)
            action_digest = "a" * 64
            boundary_digest = "b" * 64
            payload = {
                "schemaVersion": "ea-factory-mt5-start-dispatch-v1",
                "operationId": operation_id,
                "actionRequestDigest": action_digest,
                "startBoundarySha256": boundary_digest,
                "confirmedAt": (
                    datetime.now(timezone.utc) - timedelta(days=30)
                ).isoformat(),
            }
            path.write_bytes(mt5._canonical_json(payload))
            self.assertEqual(
                mt5._validate_dispatch_confirmation(
                    path,
                    operation_id=operation_id,
                    action_digest=action_digest,
                    boundary_digest=boundary_digest,
                ),
                sha256_bytes(path.read_bytes()),
            )

    def test_same_operation_start_then_collect_keeps_durable_identity(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "32")
        self.fixture.capability(request)
        self.fixture.runner.fail_after_first_boundary = True
        with self.assertRaisesRegex(RuntimeError, "simulated_ui_disconnect"):
            self.fixture.adapter.optimization_handler(request=request)
        request["safety"]["neverStart"] = True
        request["safety"]["serviceAction"] = "collect_round"
        result = self.fixture.adapter.optimization_handler(request=request)
        self.assertEqual(
            [action for action in self.fixture.runner.actions if action not in {"probe", "post_probe"}],
            ["optimize", "collect_optimization"],
        )
        self.assertTrue(result["metrics"]["recoveredWithoutStart"])
        self.assertFalse(result["metrics"]["optimizationExecuted"])
        self.assertFalse(result["metrics"]["startInvoked"])
        summaries = self.fixture.workspace / "Summaries"
        action_path = next(summaries.glob("*-optimization-action.json"))
        boundary_path = next(summaries.glob("*-optimization-start-boundary.json"))
        action_payload = json.loads(action_path.read_text(encoding="utf-8"))
        boundary_payload = json.loads(boundary_path.read_text(encoding="utf-8"))
        self.assertEqual(
            action_payload["actionRequestDigest"],
            boundary_payload["actionRequestDigest"],
        )

    def test_completed_idle_optimization_reuses_signed_result_checkpoint(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "41")
        self.fixture.capability(request)
        self.fixture.runner.fail_after_result_checkpoint = True
        with self.assertRaisesRegex(
            RuntimeError, "simulated_disconnect_after_result_checkpoint"
        ):
            self.fixture.adapter.optimization_handler(request=request)
        screenshots = self.fixture.workspace / "Screenshots"
        settings_path = next(screenshots.glob("*-optimization-settings.png"))
        result_path = next(screenshots.glob("*-optimization-result.png"))
        settings_before = (sha256_bytes(settings_path.read_bytes()), settings_path.stat().st_mtime_ns)
        result_before = (sha256_bytes(result_path.read_bytes()), result_path.stat().st_mtime_ns)

        result = self.fixture.adapter.optimization_handler(request=request)

        self.assertEqual(
            [action for action in self.fixture.runner.actions if action not in {"probe", "post_probe"}],
            ["optimize", "recover_completed_optimization"],
        )
        metrics = result["metrics"]
        self.assertTrue(metrics["recoveredWithoutStart"])
        self.assertFalse(metrics["startInvoked"])
        self.assertFalse(metrics["optimizationExecuted"])
        self.assertFalse(metrics["executionObservedRunning"])
        self.assertTrue(metrics["completedResultCheckpointReused"])
        self.assertFalse(metrics["completedReportCheckpointReused"])
        self.assertFalse(metrics["recoveryIssuedStart"])
        self.assertEqual(
            metrics["testerCompletionObservation"],
            "recovery_completed_checkpoint_observed",
        )
        self.assertEqual(
            metrics["testerRunTransitionEvidence"],
            "completed_result_checkpoint_after_dispatch",
        )
        self.assertEqual(
            settings_before,
            (sha256_bytes(settings_path.read_bytes()), settings_path.stat().st_mtime_ns),
        )
        self.assertEqual(
            result_before,
            (sha256_bytes(result_path.read_bytes()), result_path.stat().st_mtime_ns),
        )
        aliases = {item["alias"] for item in result["artifactSpecifications"]}
        self.assertIn("optimization_completion_checkpoint", aliases)
        self.assertEqual(metrics["testerReportFormat"], "spreadsheetml")
        self.assertEqual(metrics["testerReportTabName"], "Optimization Results")

    def test_collected_optimization_reuses_report_and_proof_without_export(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "42")
        self.fixture.capability(request)
        self.fixture.runner.fail_after_report_checkpoint = True
        with self.assertRaisesRegex(
            RuntimeError, "simulated_disconnect_after_report_checkpoint"
        ):
            self.fixture.adapter.optimization_handler(request=request)
        report = next((self.fixture.workspace / "Reports").glob("*.xml"))
        proof = next(
            (self.fixture.workspace / "Screenshots").glob("*-optimization-report.png")
        )
        report_before = (sha256_bytes(report.read_bytes()), report.stat().st_mtime_ns)
        proof_before = (sha256_bytes(proof.read_bytes()), proof.stat().st_mtime_ns)

        result = self.fixture.adapter.optimization_handler(request=request)

        self.assertEqual(
            [action for action in self.fixture.runner.actions if action not in {"probe", "post_probe"}],
            ["optimize", "recover_collected_optimization"],
        )
        metrics = result["metrics"]
        self.assertTrue(metrics["completedResultCheckpointReused"])
        self.assertTrue(metrics["completedReportCheckpointReused"])
        self.assertFalse(metrics["executionObservedRunning"])
        self.assertEqual(
            metrics["testerCompletionObservation"],
            "recovery_collected_checkpoint_observed",
        )
        self.assertEqual(
            metrics["testerRunTransitionEvidence"],
            "collected_report_checkpoint_after_dispatch",
        )
        self.assertEqual(
            report_before,
            (sha256_bytes(report.read_bytes()), report.stat().st_mtime_ns),
        )
        self.assertEqual(
            proof_before,
            (sha256_bytes(proof.read_bytes()), proof.stat().st_mtime_ns),
        )

    def test_completed_result_without_cache_lineage_fails_before_recovery_ui(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "43")
        self.fixture.capability(request)
        self.fixture.runner.fail_after_result_checkpoint = True
        with self.assertRaisesRegex(RuntimeError, "result_checkpoint"):
            self.fixture.adapter.optimization_handler(request=request)
        summaries = self.fixture.workspace / "Summaries"
        next(summaries.glob("*-completion-checkpoint.json")).unlink()
        for cache in (self.fixture.data / "Tester" / "cache").glob("*.opt"):
            cache.unlink()
        actions_before = list(self.fixture.runner.actions)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_optimization_completion_lineage_invalid",
        ):
            self.fixture.adapter.optimization_handler(request=request)
        self.assertEqual(self.fixture.runner.actions, actions_before)

    def test_completed_result_rejects_cache_modified_before_dispatch(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "48")
        self.fixture.capability(request)
        self.fixture.runner.fail_after_result_checkpoint = True
        with self.assertRaisesRegex(RuntimeError, "result_checkpoint"):
            self.fixture.adapter.optimization_handler(request=request)
        summaries = self.fixture.workspace / "Summaries"
        next(summaries.glob("*-completion-checkpoint.json")).unlink()
        dispatch = next(summaries.glob("*.dispatch-confirmed"))
        cache = next((self.fixture.data / "Tester" / "cache").glob("*.opt"))
        stale_ns = dispatch.stat().st_mtime_ns - 5_000_000_000
        os.utime(cache, ns=(stale_ns, stale_ns))
        actions_before = list(self.fixture.runner.actions)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_optimization_completion_lineage_invalid",
        ):
            self.fixture.adapter.optimization_handler(request=request)
        self.assertEqual(self.fixture.runner.actions, actions_before)

    def test_legacy_completed_result_mints_then_validates_durable_checkpoint(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "44")
        self.fixture.capability(request)
        self.fixture.runner.fail_after_result_checkpoint = True
        with self.assertRaisesRegex(RuntimeError, "result_checkpoint"):
            self.fixture.adapter.optimization_handler(request=request)
        checkpoint = next(
            (self.fixture.workspace / "Summaries").glob("*-completion-checkpoint.json")
        )
        checkpoint.unlink()

        result = self.fixture.adapter.optimization_handler(request=request)
        checkpoint_payload = json.loads(checkpoint.read_text(encoding="utf-8"))

        self.assertEqual(
            checkpoint_payload["operationId"], request["visibleOperation"]["operationId"]
        )
        self.assertEqual(
            checkpoint_payload["schemaVersion"],
            mt5.OPTIMIZATION_COMPLETION_CHECKPOINT_SCHEMA,
        )
        self.assertEqual(
            checkpoint_payload["optimizationCacheLineage"]["expertFileName"],
            "Strategy.ex5",
        )
        self.assertEqual(
            checkpoint_payload["optimizationCacheLineage"]["symbol"], "EURUSD"
        )
        self.assertEqual(
            result["metrics"]["optimizationCompletionCheckpointSha256"],
            sha256_bytes(checkpoint.read_bytes()),
        )
        actions_before = list(self.fixture.runner.actions)
        recovered = self.fixture.adapter.optimization_handler(request=request)
        self.assertTrue(recovered["metrics"]["recoveredExistingReceipt"])
        self.assertFalse(recovered["metrics"]["optimizationExecuted"])
        self.assertEqual(self.fixture.runner.actions, actions_before)

    def test_receipt_replay_rejects_hardlinked_completion_checkpoint(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "47")
        self.fixture.capability(request)
        self.fixture.adapter.optimization_handler(request=request)
        checkpoint = next(
            (self.fixture.workspace / "Summaries").glob(
                "*-completion-checkpoint.json"
            )
        )
        alias = checkpoint.with_name("completion-checkpoint-hardlink.json")
        try:
            os.link(checkpoint, alias)
        except OSError as error:
            self.skipTest(f"hard links unavailable: {error}")
        actions_before = list(self.fixture.runner.actions)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_tester_recovery_checkpoint_invalid",
        ):
            self.fixture.adapter.optimization_handler(request=request)
        self.assertEqual(self.fixture.runner.actions, actions_before)

    def test_legacy_one_click_request_may_omit_dynamic_recovery_pair(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("backtest_recheck", "33")
        request["safety"].pop("neverStart")
        request["safety"].pop("serviceAction")
        self.fixture.capability(request)
        result = self.fixture.adapter.backtest_handler(request=request)
        self.assertTrue(result["metrics"]["backtestExecuted"])

    def test_optimization_uses_immutable_ranges_and_real_report(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "4")
        capability = self.fixture.capability(request)
        self.assertTrue(capability["visibleOptimization"])
        self.assertNotIn("visualMode", capability["automationIds"])
        result = self.fixture.adapter.optimization_handler(request=request)
        optimization_payload = next(
            payload
            for payload in reversed(self.fixture.runner.payloads)
            if payload.get("action") == "optimize"
        )
        self.assertEqual(
            optimization_payload["requiredAutomationIds"],
            mt5.OPTIMIZATION_TESTER_AUTOMATION_IDS,
        )
        self.assertNotIn("criterion", optimization_payload["requiredAutomationIds"])
        self.assertNotIn("visualMode", optimization_payload["requiredAutomationIds"])
        self.assertEqual(
            optimization_payload["optimizationCriterionAutomationId"],
            "10507",
        )
        metrics = result["metrics"]
        self.assertTrue(metrics["optimizationVerified"])
        self.assertTrue(metrics["optimizationExecuted"])
        self.assertEqual(metrics["testerReportFormat"], "spreadsheetml")
        self.assertEqual(metrics["testerReportTabName"], "Optimization Results")
        self.assertEqual(metrics["optimizationPassCount"], 4)
        self.assertEqual(metrics["optimizationReturnedPassCount"], 4)
        self.assertFalse(metrics["optimizationRowsTruncated"])
        self.assertEqual(metrics["optimizationResultRows"][0]["passNumber"], 1)
        self.assertEqual(metrics["optimizationResultRows"][3]["RiskPercent"], 2.0)
        aliases = {item["alias"] for item in result["artifactSpecifications"]}
        self.assertIn("optimization_report", aliases)
        self.assertIn("optimization_input_readback", aliases)
        self.assertIn("baseline_input_readback", aliases)
        receipt_path = self.fixture.workspace / next(
            item["relativePath"]
            for item in result["artifactSpecifications"]
            if item["alias"] == "adapter_receipt"
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["reportFormat"], "spreadsheetml")
        self.assertEqual(receipt["reportTabName"], "Optimization Results")

    def test_optimization_receipt_replay_reparses_report_and_rejects_tampered_rows(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "75")
        self.fixture.capability(request)
        result = self.fixture.adapter.optimization_handler(request=request)
        receipt_path = self.fixture.workspace / next(
            item["relativePath"]
            for item in result["artifactSpecifications"]
            if item["alias"] == "adapter_receipt"
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["optimizationResultRows"][0]["Profit"] = 999999.0
        receipt_path.write_bytes(mt5._canonical_json(receipt))
        actions_before = list(self.fixture.runner.actions)

        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "visible_receipt_optimization_evidence_mismatch",
        ):
            self.fixture.adapter.optimization_handler(request=request)

        self.assertEqual(self.fixture.runner.actions, actions_before)

    def test_optimization_rejects_action_result_with_tampered_criterion_evidence(self) -> None:
        self.fixture.prepare_compiled_binary()
        base_runner = self.fixture.runner

        def tampered_criterion(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            result = base_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload.get("action") == "optimize":
                result = copy.deepcopy(result)
                result["automationControlsVerified"]["criterion"] = "10490"
            return result

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=tampered_criterion,
        )
        request = self.fixture.request("optimize", "71")
        self.fixture.capability(request)

        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "visible_optimization_result_invalid",
        ):
            self.fixture.adapter.optimization_handler(request=request)

    def test_all_symbols_universe_is_bound_through_receipt_and_replay(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "61")
        request["optimizationIntent"]["mode"] = "all_symbols_market_watch"
        self.fixture.capability(request)
        result = self.fixture.adapter.optimization_handler(request=request)
        metrics = result["metrics"]
        universe = metrics["optimizationSymbolUniverse"]
        self.assertEqual(universe["symbols"], ["EURUSD", "GBPUSD"])
        self.assertEqual(
            metrics["optimizationSymbolUniverseDigest"],
            sha256_bytes(mt5._canonical_json(universe)),
        )
        receipt_path = self.fixture.workspace / next(
            item["relativePath"]
            for item in result["artifactSpecifications"]
            if item["alias"] == "adapter_receipt"
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["optimizationSymbolUniverse"], universe)
        self.assertEqual(
            receipt["optimizationSymbolUniverseDigest"],
            metrics["optimizationSymbolUniverseDigest"],
        )
        actions_before = list(self.fixture.runner.actions)
        replay = self.fixture.adapter.optimization_handler(request=request)
        self.assertTrue(replay["metrics"]["recoveredExistingReceipt"])
        self.assertFalse(replay["metrics"]["optimizationExecuted"])
        self.assertEqual(self.fixture.runner.actions, actions_before)

    def test_optimization_rejects_wrong_report_wire_identity(self) -> None:
        self.fixture.prepare_compiled_binary()
        base_runner = self.fixture.runner

        def wrong_report_identity(
            payload: dict, *, response_path: Path, timeout_seconds: int
        ) -> dict:
            response = base_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "optimize":
                response = dict(response)
                response["reportFormat"] = "html"
                response["reportTabName"] = "Results"
            return response

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=wrong_report_identity,
        )
        request = self.fixture.request("optimize", "45")
        self.fixture.capability(request)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "visible_optimization_result_invalid",
        ):
            self.fixture.adapter.optimization_handler(request=request)

    def test_receipt_replay_rejects_wrong_report_wire_identity(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("backtest_recheck", "46")
        self.fixture.capability(request)
        result = self.fixture.adapter.backtest_handler(request=request)
        receipt_path = self.fixture.workspace / next(
            item["relativePath"]
            for item in result["artifactSpecifications"]
            if item["alias"] == "adapter_receipt"
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["reportFormat"] = "spreadsheetml"
        receipt["reportTabName"] = "Optimization Results"
        receipt_path.write_bytes(mt5._canonical_json(receipt))
        actions_before = list(self.fixture.runner.actions)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "visible_receipt_evidence_mismatch",
        ):
            self.fixture.adapter.backtest_handler(request=request)
        self.assertEqual(self.fixture.runner.actions, actions_before)

    def test_completed_start_response_is_consumed_without_collect_or_second_start(self) -> None:
        self.fixture.prepare_compiled_binary()
        base_runner = self.fixture.runner

        def durable_runner(payload: dict, *, response_path: Path, timeout_seconds: int) -> dict:
            raw = base_runner(
                payload,
                response_path=response_path,
                timeout_seconds=timeout_seconds,
            )
            if payload["action"] == "optimize":
                durable_path = mt5._powershell_action_response_path(
                    response_path, "optimize"
                )
                durable_path.write_bytes(mt5._canonical_json(raw))
                returned = dict(raw)
                returned["durableStartResponseSha256"] = sha256_bytes(
                    durable_path.read_bytes()
                )
                return returned
            return raw

        verifier_calls = 0

        def crash_once(context: dict) -> dict:
            nonlocal verifier_calls
            verifier_calls += 1
            if verifier_calls == 1:
                raise RuntimeError("simulated_python_crash_before_receipt_commit")
            return mt5.verify_mt5_optimization_report(context)

        self.fixture.adapter = mt5.create_production_visible_front_office_adapter_mt5(
            target_resolver=lambda **_: self.fixture.target,
            powershell_runner=durable_runner,
            optimization_verifier=crash_once,
        )
        request = self.fixture.request("optimize", "35")
        self.fixture.capability(request)
        with self.assertRaisesRegex(RuntimeError, "simulated_python_crash"):
            self.fixture.adapter.optimization_handler(request=request)
        result = self.fixture.adapter.optimization_handler(request=request)
        self.assertEqual(
            [action for action in base_runner.actions if action not in {"probe", "post_probe"}],
            ["optimize"],
        )
        self.assertTrue(result["metrics"]["recoveredWithoutStart"])
        self.assertFalse(result["metrics"]["optimizationExecuted"])
        self.assertFalse(result["metrics"]["startInvoked"])
        summaries = self.fixture.workspace / "Summaries"
        self.assertFalse(next(summaries.glob("*-ui-optimize.json"), None))

    def test_optimization_rejects_tampered_set_before_ui_action(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "5")
        set_path = self.fixture.workspace / request["optimizationIntent"]["setFile"]
        set_path.write_text("RiskPercent=99||1||1||100||Y\n", encoding="ascii")
        self.fixture.capability(request)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "optimization_set_(?:reference_invalid|changed)",
        ):
            self.fixture.adapter.optimization_handler(request=request)
        self.assertNotIn("optimize", self.fixture.runner.actions)

    def test_optimization_rejects_signed_nonselected_input_drift(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "36")
        self.fixture.capability(request)
        intent = request["optimizationIntent"]
        set_ref = intent["setRef"]
        set_path = self.fixture.workspace / set_ref["relativePath"]
        lines = set_path.read_text(encoding="ascii").splitlines()
        lines[1] = "MaxTrades=2||2||1||2||N"
        payload = ("\r\n".join(lines) + "\r\n").encode("ascii")
        set_path.write_bytes(payload)
        changed_entries = [dict(entry) for entry in set_ref["expectedReadbackEntries"]]
        changed_entries[1].update(current="2", start="2", stop="2")
        core = {
            "schemaVersion": set_ref["schemaVersion"],
            "relativePath": set_ref["relativePath"],
            "sha256": sha256_bytes(payload),
            "inputManifestDigest": set_ref["inputManifestDigest"],
            "entryCount": set_ref["entryCount"],
            "expectedReadbackEntries": changed_entries,
            "expectedReadbackEntriesDigest": sha256_bytes(
                mt5._canonical_json(changed_entries)
            ),
        }
        intent["setRef"] = {
            **core,
            "refDigest": sha256_bytes(mt5._canonical_json(core)),
        }
        intent["setDigest"] = core["sha256"]
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "(?:optimization_set_reference_invalid|mt5_set_reference_invalid)",
        ):
            self.fixture.adapter.optimization_handler(request=request)
        self.assertNotIn("optimize", self.fixture.runner.actions)

    def test_compiled_deployment_rejects_binary_drift_before_ui_action(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "37")
        self.fixture.capability(request)
        self.fixture.source.with_suffix(".ex5").write_bytes(b"EX5\x00tampered")
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "compiled_deployment_binding_invalid",
        ):
            self.fixture.adapter.optimization_handler(request=request)
        self.assertNotIn("optimize", self.fixture.runner.actions)

    def test_bridge_enum_and_bool_manifest_shape_is_accepted(self) -> None:
        source_digest = "f" * 64
        core = {
            "schemaVersion": mt5.INPUT_MANIFEST_SCHEMA,
            "sourceDigest": source_digest,
            "entries": [
                {
                    "ordinal": 0,
                    "qualifier": "input",
                    "declaredType": "ENUM_MODE",
                    "inputName": "Mode",
                    "valueKind": "enum",
                    "setDefault": "1",
                    "enumValues": ["0", "1", "2"],
                    "optimizable": True,
                },
                {
                    "ordinal": 1,
                    "qualifier": "sinput",
                    "declaredType": "bool",
                    "inputName": "UseGuard",
                    "valueKind": "bool",
                    "setDefault": "true",
                    "enumValues": [],
                    "optimizable": False,
                },
            ],
        }
        manifest = {
            **core,
            "manifestDigest": sha256_bytes(mt5._canonical_json(core)),
        }
        self.assertEqual(
            mt5._validate_input_manifest(manifest, source_digest), manifest
        )

    def test_bridge_typed_range_metadata_is_bound_to_manifest(self) -> None:
        self.fixture.prepare_compiled_binary()
        request = self.fixture.request("optimize", "typed-range-metadata")
        intent = request["optimizationIntent"]
        intent["ranges"][0].update(
            sourceDefault="1",
            valueKind="decimal",
        )
        intent["rangesDigest"] = sha256_bytes(
            mt5._canonical_json(intent["ranges"])
        )
        validated = mt5._validate_optimization_intent(
            intent,
            self.fixture.workspace,
            sha256_bytes(self.fixture.source.read_bytes()),
            self.fixture.source.read_text(encoding="utf-8"),
        )
        self.assertEqual(validated["ranges"][0]["valueKind"], "decimal")
        tampered = json.loads(json.dumps(intent))
        tampered["ranges"][0]["valueKind"] = "integer"
        tampered["rangesDigest"] = sha256_bytes(
            mt5._canonical_json(tampered["ranges"])
        )
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "optimization_set_reference_invalid",
        ):
            mt5._validate_optimization_intent(
                tampered,
                self.fixture.workspace,
                sha256_bytes(self.fixture.source.read_bytes()),
                self.fixture.source.read_text(encoding="utf-8"),
            )

    def test_optimization_reuses_only_source_bound_tester_simulation_overrides(
        self,
    ) -> None:
        source_code = (
            "#property strict\n"
            "input double RiskPercent=1.0;\n"
            "input int MaxTrades=1;\n"
            "sinput bool ExternalCriteriaConfirmed=false;\n"
            "void OnTick()\n"
            "{\n"
            "   if(!ExternalCriteriaConfirmed) return;\n"
            "}\n"
        )
        self.fixture.source.write_text(source_code, encoding="utf-8")
        source_digest = sha256_bytes(source_code.encode("utf-8"))
        manifest = self.fixture.manifest()
        manifest["entries"][2].update(
            inputName="ExternalCriteriaConfirmed",
            setDefault="false",
        )
        manifest_core = {
            "schemaVersion": mt5.INPUT_MANIFEST_SCHEMA,
            "sourceDigest": source_digest,
            "entries": manifest["entries"],
        }
        manifest = {
            **manifest_core,
            "manifestDigest": sha256_bytes(mt5._canonical_json(manifest_core)),
        }
        assumptions = [
            {
                "inputName": "RiskPercent",
                "inputType": "double",
                "sourceDefault": 1.0,
                "testerValue": 1.0,
                "reasonCode": (
                    "reset_to_immutable_source_default_to_prevent_stale_tester_state"
                ),
            },
            {
                "inputName": "MaxTrades",
                "inputType": "int",
                "sourceDefault": 1,
                "testerValue": 1,
                "reasonCode": (
                    "reset_to_immutable_source_default_to_prevent_stale_tester_state"
                ),
            },
            {
                "inputName": "ExternalCriteriaConfirmed",
                "inputType": "bool",
                "sourceDefault": False,
                "testerValue": True,
                "reasonCode": (
                    "simulate_external_manual_confirmation_for_historical_test_only"
                ),
            },
        ]
        preset_unsigned = {
            "schemaVersion": mt5.TESTER_INPUT_PRESET_SCHEMA,
            "mode": (
                "full_immutable_source_snapshot_with_explicit_simulation_assumptions"
            ),
            "scope": "mt5_strategy_tester_only",
            "sourceDigest": source_digest,
            "inputManifestDigest": manifest["manifestDigest"],
            "assumptions": assumptions,
            "liveSourceDefaultsPreserved": True,
            "visibleExpertPropertiesRequired": True,
            "readbackRequired": True,
            "liveTradingAllowed": False,
            "fullCertifiedInputSnapshot": True,
            "simulationInputNames": ["ExternalCriteriaConfirmed"],
        }
        preset = {
            **preset_unsigned,
            "presetDigest": sha256_bytes(mt5._canonical_json(preset_unsigned)),
        }
        fixed_overrides = {"ExternalCriteriaConfirmed": "true"}
        ranges = [{
            "inputName": "RiskPercent",
            "start": "0.5",
            "step": "0.5",
            "stop": "2",
            "enabled": True,
        }]
        set_ref = self.fixture.set_reference(
            "optimization-with-simulation.set",
            {"RiskPercent": ("0.5", "0.5", "2")},
            manifest=manifest,
            fixed_current_overrides=fixed_overrides,
        )
        baseline_ref = self.fixture.set_reference(
            "optimization-baseline-with-simulation.set",
            {},
            manifest=manifest,
            fixed_current_overrides=fixed_overrides,
        )
        intent = {
            "schemaVersion": mt5.OPTIMIZATION_INTENT_SCHEMA,
            "sourceDigest": source_digest,
            "inputManifest": manifest,
            "inputManifestDigest": manifest["manifestDigest"],
            "testerInputPreset": preset,
            "setFile": set_ref["relativePath"],
            "setDigest": set_ref["sha256"],
            "setRef": set_ref,
            "baselinePresetRef": baseline_ref,
            "ranges": ranges,
            "rangesDigest": sha256_bytes(mt5._canonical_json(ranges)),
            "visibleInputsRequired": True,
            "reportRequired": True,
            "startOnce": True,
            "mode": "fast_genetic",
            "criterion": "balance_max",
        }

        validated = mt5._validate_optimization_intent(
            intent,
            self.fixture.workspace,
            source_digest,
            source_code,
        )
        self.assertEqual(
            validated["testerInputPreset"]["simulationInputNames"],
            ["ExternalCriteriaConfirmed"],
        )
        self.assertEqual(
            validated["setRef"]["expectedReadbackEntries"][2]["current"],
            "true",
        )
        self.assertEqual(
            validated["baselinePresetRef"]["expectedReadbackEntries"][2][
                "current"
            ],
            "true",
        )

        unbound_ref = self.fixture.set_reference(
            "optimization-with-unbound-source-default.set",
            {"RiskPercent": ("0.5", "0.5", "2")},
            manifest=manifest,
        )
        tampered = copy.deepcopy(intent)
        tampered["setFile"] = unbound_ref["relativePath"]
        tampered["setDigest"] = unbound_ref["sha256"]
        tampered["setRef"] = unbound_ref
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_set_reference_invalid",
        ):
            mt5._validate_optimization_intent(
                tampered,
                self.fixture.workspace,
                source_digest,
                source_code,
            )

        resigned = copy.deepcopy(intent)
        resigned_manifest = copy.deepcopy(manifest)
        resigned_manifest["entries"][2]["setDefault"] = "true"
        resigned_core = {
            "schemaVersion": mt5.INPUT_MANIFEST_SCHEMA,
            "sourceDigest": source_digest,
            "entries": resigned_manifest["entries"],
        }
        resigned_manifest["manifestDigest"] = sha256_bytes(
            mt5._canonical_json(resigned_core)
        )
        resigned["inputManifest"] = resigned_manifest
        resigned["inputManifestDigest"] = resigned_manifest["manifestDigest"]
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_input_manifest_source_mismatch",
        ):
            mt5._validate_optimization_intent(
                resigned,
                self.fixture.workspace,
                source_digest,
                source_code,
            )

    def test_mt4_target_and_mql4_source_are_rejected(self) -> None:
        request = self.fixture.request("compile_validate", "6")
        mt4_terminal = self.fixture.install / "terminal.exe"
        mt4_terminal.write_bytes(b"terminal4-test")
        bad_target = dict(request["resolvedTarget"], terminalPath=str(mt4_terminal))
        request["resolvedTarget"] = bad_target
        capability = self.fixture.adapter.capability_provider(
            platform="mt5",
            stage_id="compile_validate",
            terminal_binding=request["terminalBinding"],
            visible_operation=request["visibleOperation"],
            resolved_target=bad_target,
        )
        self.assertFalse(capability["ready"])

    def test_resolved_target_executable_digests_are_stage_aware(self) -> None:
        terminal_digest = sha256_bytes(self.fixture.terminal.read_bytes())
        compiler_digest = sha256_bytes(self.fixture.compiler.read_bytes())

        compile_request = self.fixture.request("compile_validate", "a1")
        compile_request["resolvedTarget"] = {
            **compile_request["resolvedTarget"],
            "terminalExecutableSha256": terminal_digest,
            "frontOfficeExecutableSha256": compiler_digest,
        }
        compile_capability = self.fixture.adapter.capability_provider(
            platform="mt5",
            stage_id="compile_validate",
            terminal_binding=compile_request["terminalBinding"],
            visible_operation=compile_request["visibleOperation"],
            resolved_target=compile_request["resolvedTarget"],
        )
        self.assertTrue(compile_capability["ready"], compile_capability)

        self.fixture.prepare_compiled_binary()
        backtest_request = self.fixture.request("backtest_recheck", "a2")
        backtest_request["resolvedTarget"] = {
            **backtest_request["resolvedTarget"],
            "terminalExecutableSha256": terminal_digest,
            "frontOfficeExecutableSha256": terminal_digest,
        }
        backtest_capability = self.fixture.adapter.capability_provider(
            platform="mt5",
            stage_id="backtest_recheck",
            terminal_binding=backtest_request["terminalBinding"],
            visible_operation=backtest_request["visibleOperation"],
            resolved_target=backtest_request["resolvedTarget"],
            tester_settings=backtest_request["testerSettings"],
        )
        self.assertTrue(backtest_capability["ready"], backtest_capability)

        wrong_backtest_target = {
            **backtest_request["resolvedTarget"],
            "frontOfficeExecutableSha256": compiler_digest,
        }
        rejected = self.fixture.adapter.capability_provider(
            platform="mt5",
            stage_id="backtest_recheck",
            terminal_binding=backtest_request["terminalBinding"],
            visible_operation=backtest_request["visibleOperation"],
            resolved_target=wrong_backtest_target,
            tester_settings=backtest_request["testerSettings"],
        )
        self.assertFalse(rejected["ready"])
        self.assertEqual(
            rejected["reasonCode"],
            "terminal_target_executable_digest_mismatch",
        )

    def test_powershell_declares_exact_ids_and_never_launches_or_closes_terminal(self) -> None:
        text = PS_PATH.read_text(encoding="utf-8")
        self.assertEqual(
            mt5.CERTIFIED_EMA_SMOKE_PROFILE_ID,
            "custom-ema-10-60-closed-bar-smoke-mt5-v3",
        )
        self.assertIn(
            '"custom-ema-10-60-closed-bar-smoke-mt5-v3"',
            text,
        )
        self.assertNotIn(
            '"custom-ema-10-60-closed-bar-smoke-mt5-v2"',
            text,
        )
        for token in ("10489", "10491", "10492", "10507", "16790", "32846"):
            self.assertIn(token, json.dumps(mt5.REQUIRED_TESTER_AUTOMATION_IDS))
        self.assertIn(
            'Select-BoundTesterComboMapped $Request "optimization"', text
        )
        self.assertIn('Select-BoundTesterComboMapped $Request "forward"', text)
        self.assertIn("Get-PositiveDecimal $controls.deposit", text)
        self.assertIn("function Get-NativeTesterDateText", text)
        self.assertIn("Get-NativeTesterDateText ([string]$Request.testerSettings.fromDate)", text)
        self.assertIn("Focus-UniqueResultsTable", text)
        self.assertIn("Read-And-VerifyConfiguredTester $Request $Optimize", text)
        self.assertIn("idle_after_dispatch_clean_log_completion", text)
        self.assertIn("MetafxMt5StartEventMonitor", text)
        self.assertIn("Invoke-TesterStartOnce $start", text)
        start_block = text[text.index("function Invoke-TesterStartOnce"):text.index("function Wait-TesterCompletion")]
        self.assertLess(
            start_block.index("Read-TesterStartState"),
            start_block.index("$Monitor.PostStartOnce("),
        )
        self.assertNotIn("Invoke-NativeMessage", start_block)
        self.assertNotIn("SendMessageTimeout", start_block)
        self.assertNotIn("DoEvents", start_block)
        self.assertIn("PostButtonClickIfTextExact", text)
        native_post = text[
            text.index("public static void PostButtonClickIfTextExact") : text.index(
                "public static IntPtr FindOwnedDialogExact"
            )
        ]
        self.assertEqual(native_post.count("PostMessage(button, BM_CLICK"), 1)
        self.assertNotIn("SendMessageTimeout", native_post)
        self.assertIn("GetDlgCtrlID(button) != expectedControlId", native_post)
        self.assertIn("GetForegroundWindow() != expectedRoot", native_post)
        self.assertIn("buttonThreadId != rootThreadId", native_post)
        self.assertIn('String.Equals(ReadWindowTextExact(button), expectedText, StringComparison.Ordinal)', text)
        start_state = text[
            text.index("function Read-TesterStartState") : text.index(
                "function New-TesterStartMonitor"
            )
        ]
        stable_state = text[
            text.index("function Wait-TesterStartStateStable") : text.index(
                "function New-TesterStartMonitor"
            )
        ]
        wait_state = text[
            text.index("function Wait-TesterCompletion") : text.index(
                "function Get-SharedUnicodeLogText"
            )
        ]
        self.assertIn("[System.StringComparison]::Ordinal", start_state)
        self.assertNotIn(".Trim()", start_state)
        self.assertNotIn("-match", wait_state)
        self.assertNotIn("-notmatch", wait_state)
        self.assertIn("$Monitor.SawStop", wait_state)
        self.assertIn('return "idle_after_dispatch_clean_log_completion"', wait_state)
        self.assertIn("Assert-TesterCleanCompletion $Request $Optimize $Configured", wait_state)
        self.assertLess(
            wait_state.index("$eventState = Wait-TesterStartStateStable"),
            wait_state.index('return "native_event_stop_then_start"'),
        )
        self.assertIn("$ExpectedHandle", stable_state)
        self.assertIn("Read-TesterStartState $Start $Code $ExpectedHandle", stable_state)
        self.assertIn("[System.Windows.Forms.Application]::DoEvents()", stable_state)
        self.assertIn("Start-Sleep -Milliseconds 25", stable_state)
        self.assertNotIn("Invoke-TesterStartOnce", stable_state)
        self.assertNotIn("PostButtonClickIfTextExact", stable_state)
        self.assertNotIn("Get-BoundTesterControlSet", stable_state)
        monitor_block = text[
            text.index("public sealed class MetafxMt5StartEventMonitor") : text.index(
                '"@\nAdd-Type @"',
                text.index("public sealed class MetafxMt5StartEventMonitor"),
            )
        ]
        self.assertNotIn(".Trim()", monitor_block)
        self.assertIn("if (!armed) return;", monitor_block)
        self.assertIn("public void PostStartOnce(", monitor_block)
        self.assertIn("lock (this)", monitor_block)
        self.assertLess(
            monitor_block.index("armed = true;"),
            monitor_block.index("MetafxMt5VisibleNative.PostButtonClickIfTextExact("),
        )
        self.assertNotIn("PostButtonClickIfTextExact", start_block)
        invoke_block = text[
            text.index("Write-StartBoundary $Request") : text.index(
                "Capture-BoundTerminalWindow $Request ([string]$Request.resultScreenshotPath)"
            )
        ]
        self.assertLess(
            invoke_block.index("Write-StartBoundary $Request"),
            invoke_block.index("Assert-StartBoundary $Request"),
        )
        self.assertLess(
            invoke_block.index("Assert-StartBoundary $Request"),
            invoke_block.index("Invoke-TesterStartOnce $start"),
        )
        self.assertLess(
            invoke_block.index("Invoke-TesterStartOnce $start"),
            invoke_block.index("Write-DispatchConfirmation $Request"),
        )
        self.assertLess(
            invoke_block.index("Write-DispatchConfirmation $Request"),
            invoke_block.index("Wait-TesterCompletion $start"),
        )
        tester_branch_start = text.index(
            '    if ($RecoveryMode -ceq "none") {',
            text.index("function Invoke-Tester("),
        )
        in_flight_start = text.index(
            '} elseif ($RecoveryMode -ceq "in_flight") {',
            tester_branch_start,
        )
        in_flight_block = text[
            in_flight_start : text.index("    } else {", in_flight_start)
        ]
        self.assertLess(
            in_flight_block.index("Read-And-VerifyConfiguredTester"),
            in_flight_block.index("Assert-TesterCleanCompletion"),
        )
        self.assertLess(
            in_flight_block.index("Assert-TesterCleanCompletion"),
            in_flight_block.index("Capture-BoundTerminalWindow"),
        )
        self.assertIn(
            "$dispatchConfirmationSha256 = if ($recovering) { Assert-DispatchConfirmation $Request } else { $null }",
            text,
        )
        self.assertIn("GetFileInformationByHandle", text)
        self.assertIn("GetFileLinkCount($stream.SafeFileHandle.DangerousGetHandle()) -ne 1", text)
        self.assertIn("if ($recovering) { [void](Assert-StartBoundary $Request) }", text)
        self.assertIn('"recover_completed_backtest" { $result = Invoke-Tester $request $false "completed" }', text)
        self.assertIn('"recover_completed_optimization" { $result = Invoke-Tester $request $true "completed" }', text)
        self.assertIn('"recover_collected_optimization" { $result = Invoke-Tester $request $true "collected" }', text)
        self.assertNotIn("recover_unconfirmed_completed_backtest", text)
        self.assertNotIn("unconfirmed_completed", text)
        self.assertNotIn("boundary_without_receipt_clean_log_completion", text)
        self.assertNotIn("recovery_unconfirmed_clean_log_observed", text)
        recovery_only_block = text[
            in_flight_start : text.index("    return [ordered]@{", in_flight_start)
        ]
        self.assertNotIn("Write-DispatchConfirmation", recovery_only_block)
        python_text = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("recover_unconfirmed_completed_backtest", python_text)
        self.assertNotIn("unconfirmed_completed", python_text)
        self.assertNotIn("allow_missing_dispatch_for_completed_backtest", python_text)
        self.assertNotIn("boundary_without_receipt_clean_log_completion", python_text)
        self.assertNotIn("recovery_unconfirmed_clean_log_observed", python_text)
        self.assertNotIn("METAFX_LOCAL_MT5_DIAGNOSTIC", text)
        self.assertNotIn("METAFX_VISIBLE_DEBUG", text)
        self.assertNotIn('SendWait("^o")', text)
        self.assertIn('@("Backtest", "Results")', text)
        self.assertIn("Resolve-TesterReportTabNameExact", text)
        self.assertNotIn('@("Optimization Results", "Optimization Graph")', text)
        self.assertIn("Assert-TesterCleanCompletion $Request $Optimize $configured", text)
        self.assertIn('source = "fresh_tester_log_completion"', text)
        self.assertIn('schemaVersion = "ea-factory-mt5-tester-completion-evidence-v2"', text)
        self.assertIn("startLogPathSha256 = $startLogPathSha256", text)
        self.assertIn("completionLogPathSha256 = $completionLogPathSha256", text)
        self.assertIn("startSourceSha256 = $startSourceSha256", text)
        self.assertIn("executionThreadIdentitySha256 = $executionThreadIdentitySha256", text)
        self.assertNotIn("executionSource =", text)
        self.assertIn("if (-not $Optimize -and $boundThreadFinish)", text)
        self.assertIn("if ($disconnectObserved) { Fail $code }", text)
        tester_function_start = text.index("function Invoke-Tester(")
        self.assertLess(
            text.index(
                "$completionEvidence = Assert-TesterCleanCompletion $Request $Optimize $configured",
                tester_function_start,
            ),
            text.index(
                "$tabNames = @((Resolve-TesterReportTabNameExact",
                tester_function_start,
            ),
        )
        self.assertIn("Global\\MetafxclubEaFactoryMt5-$OperationId", text)
        self.assertIn("Global\\MetafxclubEaFactoryMt5Terminal-$hash", text)
        self.assertNotRegex(text, r"Start-Process\s+-FilePath\s+\$TerminalPath")
        self.assertNotIn("Stop-Process", text)
        self.assertNotIn("taskkill", text.casefold())

    def test_powershell_start_state_stabilizer_retries_transient_provider_lag_without_dispatch(self) -> None:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        quoted_path = str(PS_PATH).replace("'", "''")
        harness = rf"""
$ErrorActionPreference = 'Stop'
$text = Get-Content -Raw '{quoted_path}'
$helperStart = $text.IndexOf('function Wait-TesterStartStateStable')
$helperEnd = $text.IndexOf('function New-TesterStartMonitor', $helperStart)
if ($helperStart -lt 0 -or $helperEnd -le $helperStart) {{ throw 'stabilizer source missing' }}
$helper = $text.Substring($helperStart, $helperEnd - $helperStart)
# This is a convergence/deadline fixture, not a native UI or wall-clock test.
# Hosted runner scheduling and the first exception's JIT cost must not consume
# the 500 ms simulated provider-lag budget before the fourth mocked read.
$clockToken = '[DateTime]::UtcNow'
$pumpToken = '[System.Windows.Forms.Application]::DoEvents()'
if ([regex]::Matches($helper, [regex]::Escape($clockToken)).Count -ne 2 -or
    [regex]::Matches($helper, [regex]::Escape($pumpToken)).Count -ne 1 -or
    [regex]::Matches($helper, [regex]::Escape('Start-Sleep -Milliseconds 25')).Count -ne 1) {{
    throw 'stabilizer fixture clock seams changed'
}}
$helper = $helper.Replace('[System.Windows.Automation.AutomationElement]', '[object]')
$helper = $helper.Replace($clockToken, '$script:now')
$helper = $helper.Replace($pumpToken, 'Invoke-TestMessagePump')
function Fail([string]$Code) {{ throw $Code }}
function Reset-TestClock {{
    $script:now = [DateTime]::Parse('2026-01-01T00:00:00Z').ToUniversalTime()
    $script:reads = 0; $script:waits = 0; $script:pumps = 0
}}
function Start-Sleep([int]$Milliseconds) {{
    if ($Milliseconds -ne 25) {{ throw 'stabilizer wait interval changed' }}
    $script:waits++
    $script:now = $script:now.AddMilliseconds($Milliseconds)
}}
function Invoke-TestMessagePump {{ $script:pumps++ }}
$script:dispatches = 0
function Invoke-TesterStartOnce {{ $script:dispatches++; throw 'unexpected_dispatch' }}
$script:mode = 'lag'
function Read-TesterStartState($Control, [string]$Code, [IntPtr]$ExpectedHandle) {{
    $script:reads++
    if ($ExpectedHandle -ne [IntPtr]123) {{ throw 'binding_changed' }}
    if ($script:mode -ceq 'foreign_error') {{ throw 'provider_unexpected_error' }}
    if ($script:mode -ceq 'lag' -and $script:reads -le 3) {{ throw $Code }}
    if ($script:mode -ceq 'stop') {{ return 'Stop' }}
    return 'Start'
}}
Invoke-Expression $helper
Reset-TestClock
$started = $script:now
$observed = Wait-TesterStartStateStable $null 'mt5_tester_start_state_unverified' ([IntPtr]123) 'Start' 500
$lagReads = $script:reads
$lagElapsed = ($script:now - $started).TotalMilliseconds
$lagWaits = $script:waits; $lagPumps = $script:pumps
$script:mode = 'stop'; Reset-TestClock
$started = $script:now
$rejected = $false
try {{
    [void](Wait-TesterStartStateStable $null 'mt5_tester_start_state_unverified' ([IntPtr]123) 'Start' 75)
}} catch {{
    $rejected = $_.Exception.Message -ceq 'mt5_tester_start_state_unverified'
}}
$stopReads = $script:reads; $stopWaits = $script:waits; $stopPumps = $script:pumps
$stopElapsed = ($script:now - $started).TotalMilliseconds
$script:mode = 'lag'; Reset-TestClock
$bindingRejected = $false
try {{
    [void](Wait-TesterStartStateStable $null 'mt5_tester_start_state_unverified' ([IntPtr]124) 'Start' 500)
}} catch {{ $bindingRejected = $_.Exception.Message -ceq 'binding_changed' }}
$bindingReads = $script:reads; $bindingWaits = $script:waits
$script:mode = 'foreign_error'; Reset-TestClock
$foreignRejected = $false
try {{
    [void](Wait-TesterStartStateStable $null 'mt5_tester_start_state_unverified' ([IntPtr]123) 'Start' 500)
}} catch {{ $foreignRejected = $_.Exception.Message -ceq 'provider_unexpected_error' }}
[ordered]@{{
    observed = $observed; lagReads = $lagReads; lagElapsed = $lagElapsed
    lagWaits = $lagWaits; lagPumps = $lagPumps
    rejected = $rejected; stopReads = $stopReads; stopElapsed = $stopElapsed
    stopWaits = $stopWaits; stopPumps = $stopPumps
    bindingRejected = $bindingRejected; bindingReads = $bindingReads; bindingWaits = $bindingWaits
    foreignRejected = $foreignRejected; foreignReads = $script:reads; foreignWaits = $script:waits
    dispatches = $script:dispatches
}} | ConvertTo-Json -Compress
"""
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Sta",
                "-EncodedCommand",
                base64.b64encode(harness.encode("utf-16le")).decode("ascii"),
            ],
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        observed = json.loads(completed.stdout.strip())
        self.assertEqual(observed["observed"], "Start")
        self.assertEqual(observed["lagReads"], 4)
        self.assertEqual(observed["lagElapsed"], 75)
        self.assertEqual(observed["lagWaits"], 3)
        self.assertEqual(observed["lagPumps"], 3)
        self.assertTrue(observed["rejected"])
        self.assertEqual(observed["stopReads"], 3)
        self.assertEqual(observed["stopElapsed"], 75)
        self.assertEqual(observed["stopWaits"], 3)
        self.assertEqual(observed["stopPumps"], 3)
        self.assertTrue(observed["bindingRejected"])
        self.assertEqual(observed["bindingReads"], 1)
        self.assertEqual(observed["bindingWaits"], 0)
        self.assertTrue(observed["foreignRejected"])
        self.assertEqual(observed["foreignReads"], 1)
        self.assertEqual(observed["foreignWaits"], 0)
        self.assertEqual(observed["dispatches"], 0)

    def test_powershell_clean_completion_pairing_rejects_cross_log_source_and_run(self) -> None:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        text = PS_PATH.read_text(encoding="utf-8")
        pairing = text[
            text.index("function Get-SharedUnicodeLogText") : text.index(
                "function Read-And-VerifyConfiguredTester"
            )
        ]
        harness = (
            'function Fail([string]$Code) { throw $Code }\n'
            + pairing
            + r'''
function Invoke-PairCase([string]$Root, [string]$Mode) {
    $dataPath = Join-Path $Root ("$Mode-" + [Guid]::NewGuid().ToString("N"))
    $logRoot = Join-Path $dataPath "Tester\logs"
    [void](New-Item -ItemType Directory -Path $logRoot -Force)
    $terminalIdentity = [System.IO.Path]::GetFileName($dataPath)
    $agentBase = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine(
        [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::ApplicationData),
        "MetaQuotes", "Tester"
    ))
    $agentLogRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($agentBase, $terminalIdentity))
    if (-not $agentLogRoot.StartsWith($agentBase + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw "unsafe-test-path" }
    $boundary = Join-Path $Root "$Mode-boundary.json"
    [System.IO.File]::WriteAllText($boundary, "{}")
    $local = [DateTime]::Now.AddSeconds(2)
    $today = $local.ToString("yyyyMMdd")
    $tomorrow = $local.AddDays(1).ToString("yyyyMMdd")
    $startTime = $local.ToString("HH:mm:ss.fff")
    $coreTime = $local.AddMilliseconds(500).ToString("HH:mm:ss.fff")
    $finishTime = $local.AddSeconds(1).ToString("HH:mm:ss.fff")
    $expertUiPath = "Metafxclub\AgentHQ\Strategy"
    $isBacktestCrossLog = $Mode -ceq "backtest_cross_log"
    $isBacktest = $isBacktestCrossLog -or $Mode -ceq "backtest_wrong_core"
    $startPeriod = if ($Mode -ceq "period_suffix") { "H12" } else { "H1" }
    $startExpert = if ($Mode -ceq "expert_suffix") { "Experts\$($expertUiPath).ex5.bak" } else { "Experts\$($expertUiPath).ex5" }
    $startMessage = if ($isBacktest) {
        "visual testing of $startExpert on EURUSD,$startPeriod from 2026.01.01"
    } else {
        "optimization of $startExpert on EURUSD,$startPeriod from 2026.01.01"
    }
    $start = "AA`t0`t$startTime`tTester`t$startMessage"
    $core = "CC`t0`t$coreTime`tCore 1`ttesting of $startExpert on EURUSD,$startPeriod"
    $finishSource = if ($Mode -ceq "backtest_wrong_core") { "Core 2" } elseif ($isBacktest) { "Core 1" } elseif ($Mode -ceq "source") { "Agent" } else { "Tester" }
    $finishMessage = if ($isBacktest) {
        "$startExpert on EURUSD,$startPeriod thread finished"
    } else {
        "optimization finished, total passes 4"
    }
    $finish = "BB`t0`t$finishTime`t$finishSource`t$finishMessage"
    if ($Mode -ceq "split") {
        [System.IO.File]::WriteAllText((Join-Path $logRoot "$today.log"), "$start`r`n$core`r`n", [System.Text.Encoding]::Unicode)
        [System.IO.File]::WriteAllText((Join-Path $logRoot "$tomorrow.log"), "$finish`r`n", [System.Text.Encoding]::Unicode)
    } elseif ($isBacktest) {
        [void](New-Item -ItemType Directory -Path $agentLogRoot -Force)
        [System.IO.File]::WriteAllText((Join-Path $logRoot "$today.log"), "$start`r`n", [System.Text.Encoding]::Unicode)
        [System.IO.File]::WriteAllText((Join-Path $agentLogRoot "$today.log"), "$core`r`n$finish`r`n", [System.Text.Encoding]::Unicode)
    } else {
        $lines = if ($Mode -ceq "duplicate") { @($start, $core, $start, $finish) } else { @($start, $core, $finish) }
        [System.IO.File]::WriteAllText((Join-Path $logRoot "$today.log"), (($lines -join "`r`n") + "`r`n"), [System.Text.Encoding]::Unicode)
    }
    $request = [pscustomobject]@{
        startBoundaryPath = $boundary
        dataPath = $dataPath
        expertUiPath = $expertUiPath
        expertFileName = "Strategy.ex5"
        expectedDeployedExpertSha256 = ("f" * 64)
        operationId = ("ea-visible-" + ("a" * 24))
        testerSettings = [pscustomobject]@{ period = "H1" }
    }
    $configured = [pscustomobject]@{ symbol = "EURUSD" }
    try {
        try {
            $evidence = Assert-TesterCleanCompletion $request (-not $isBacktest) $configured
            if ($Mode -ceq "exact" -or $isBacktestCrossLog) { return $evidence }
            return "unexpected-success"
        } catch { return [string]$_.Exception.Message }
    } finally {
        if ([System.IO.Directory]::Exists($agentLogRoot)) { [System.IO.Directory]::Delete($agentLogRoot, $true) }
    }
}
$root = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), ("metafx-completion-" + [Guid]::NewGuid().ToString("N")))
[void](New-Item -ItemType Directory -Path $root -Force)
try {
    @(
        (Invoke-PairCase $root "exact"),
        (Invoke-PairCase $root "backtest_cross_log"),
        (Invoke-PairCase $root "backtest_wrong_core"),
        (Invoke-PairCase $root "split"),
        (Invoke-PairCase $root "source"),
        (Invoke-PairCase $root "duplicate"),
        (Invoke-PairCase $root "expert_suffix"),
        (Invoke-PairCase $root "period_suffix")
    ) | ConvertTo-Json -Compress
} finally { Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue }
'''
        )
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "& ([scriptblock]::Create([Console]::In.ReadToEnd()))",
            ],
            input=harness,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        results = json.loads(completed.stdout.strip())
        self.assertEqual(
            results[2:],
            [
                "mt5_tester_clean_completion_unverified",
                "mt5_tester_clean_completion_unverified",
                "mt5_tester_clean_completion_unverified",
                "mt5_tester_clean_completion_unverified",
                "mt5_tester_clean_completion_unverified",
                "mt5_tester_clean_completion_unverified",
            ],
        )
        exact, _ = mt5._validate_tester_completion_evidence(
            results[0],
            expected_marker="optimization_finished",
            expected_operation_id="ea-visible-" + ("a" * 24),
            expected_expert_file_name="Strategy.ex5",
            expected_expert_ui_path="Metafxclub\\AgentHQ\\Strategy",
            expected_deployed_expert_sha256="f" * 64,
            expected_symbol="EURUSD",
            expected_period="H1",
        )
        cross_log, _ = mt5._validate_tester_completion_evidence(
            results[1],
            expected_marker="thread_finished",
            expected_operation_id="ea-visible-" + ("a" * 24),
            expected_expert_file_name="Strategy.ex5",
            expected_expert_ui_path="Metafxclub\\AgentHQ\\Strategy",
            expected_deployed_expert_sha256="f" * 64,
            expected_symbol="EURUSD",
            expected_period="H1",
        )
        self.assertEqual(exact["completionPassCount"], 4)
        self.assertNotEqual(
            cross_log["startLogPathSha256"],
            cross_log["completionLogPathSha256"],
        )

    def test_powershell_build_6230_optimization_completion_binds_every_local_pass(self) -> None:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        text = PS_PATH.read_text(encoding="utf-8")
        pairing = text[
            text.index("function Get-SharedUnicodeLogText") : text.index(
                "function Read-And-VerifyConfiguredTester"
            )
        ]
        harness = (
            'function Fail([string]$Code) { throw $Code }\n'
            + pairing
            + r'''
function Invoke-ModernOptimizationCase([string]$Root, [string]$Mode) {
    $dataPath = Join-Path $Root ("$Mode-" + [Guid]::NewGuid().ToString("N"))
    $coordinatorRoot = Join-Path $dataPath "Tester\logs"
    [void](New-Item -ItemType Directory -Path $coordinatorRoot -Force)
    $terminalIdentity = [System.IO.Path]::GetFileName($dataPath)
    $testerBase = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine(
        [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::ApplicationData),
        "MetaQuotes", "Tester"
    ))
    $terminalAgentRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($testerBase, $terminalIdentity))
    if (-not $terminalAgentRoot.StartsWith($testerBase + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw "unsafe-test-path" }
    $boundary = Join-Path $Root "$Mode-boundary.json"
    [System.IO.File]::WriteAllText($boundary, "{}")
    $local = [DateTime]::Now.AddSeconds(1)
    $today = $local.ToString("yyyyMMdd")
    $expertUiPath = "Metafxclub\AgentHQ\Strategy"
    $embeddedExpert = "Experts\$($expertUiPath).ex5"
    $startTime = $local.ToString("HH:mm:ss.fff")
    $optimizationTime = $local.AddMilliseconds(100).ToString("HH:mm:ss.fff")
    $finishTime = $local.AddSeconds(2).ToString("HH:mm:ss.fff")
    $passCount = if ($Mode -ceq "wrong_pass_count") { 4 } else { 3 }
    $coordinatorLines = @(
        "AA`t0`t$startTime`tTester`t$embeddedExpert on EURUSD,H1 from 2026.07.17 00:00 to 2026.10.14 00:00",
        "AB`t0`t$optimizationTime`tTester`tcomplete optimization started"
    )
    if ($Mode -ceq "duplicate_start") {
        $coordinatorLines += "AC`t0`t$optimizationTime`tTester`t$embeddedExpert on EURUSD,H1 from 2026.07.18 00:00 to 2026.10.14 00:00"
    }
    $coordinatorLines += "AD`t0`t$finishTime`tTester`toptimization finished, total passes $passCount"
    [System.IO.File]::WriteAllText(
        (Join-Path $coordinatorRoot "$today.log"),
        (($coordinatorLines -join "`r`n") + "`r`n"),
        [System.Text.Encoding]::Unicode
    )
    $crossThreadResult = $null
    for ($index = 0; $index -lt 3; $index++) {
        $port = 3001 + $index
        $agentRoot = Join-Path $terminalAgentRoot "Agent-127.0.0.1-$port\logs"
        [void](New-Item -ItemType Directory -Path $agentRoot -Force)
        $agentExpert = if ($Mode -ceq "wrong_identity" -and $index -eq 2) { "Experts\Metafxclub\AgentHQ\Other.ex5" } else { $embeddedExpert }
        $passId = if ($Mode -ceq "pass_gap" -and $index -eq 2) {
            3
        } elseif ($Mode -ceq "oversized_pass" -and $index -eq 2) {
            "999999999999999999999999"
        } else {
            $index
        }
        $addedTime = $local.AddMilliseconds(500 + ($index * 10)).ToString("HH:mm:ss.fff")
        $historyTime = $local.AddMilliseconds(600 + ($index * 10)).ToString("HH:mm:ss.fff")
        $passTime = $local.AddMilliseconds(700 + ($index * 10)).ToString("HH:mm:ss.fff")
        $resultTime = $local.AddMilliseconds(1600 + ($index * 10)).ToString("HH:mm:ss.fff")
        $threadFinishTime = $local.AddMilliseconds(2100 + ($index * 10)).ToString("HH:mm:ss.fff")
        $agentLines = @(
            "BA`t0`t$addedTime`tTester`texpert file added: $embeddedExpert. 33001 bytes loaded"
        )
        if (-not ($Mode -ceq "missing_period" -and $index -eq 2)) {
            $historyPeriod = if ($Mode -ceq "wrong_period" -and $index -eq 2) { "H12" } else { "H1" }
            $agentLines += "BH`t0`t$historyTime`tHistory`tEURUSD,${historyPeriod}: history cache allocated for 11060 bars and contains 9534 bars from 2025.01.02 10:00 to 2026.07.16 23:00"
        }
        $passSource = if ($Mode -ceq "wrong_start_source" -and $index -eq 1) { "Runtime" } else { "Tester" }
        $agentLines += "BB`t0`t$passTime`t$passSource`toptimization pass $passId started"
        if ($Mode -ceq "fatal" -and $index -eq 1) {
            $agentLines += "BC`t0`t$passTime`tRuntime`tcritical error in tester worker"
        }
        if (-not ($Mode -ceq "missing_pass" -and $index -eq 2) -and
            -not ($Mode -ceq "cross_thread_result" -and $index -eq 2)) {
            $resultPassId = if ($Mode -ceq "wrong_result_pass" -and $index -eq 2) { $passId + 1 } else { $passId }
            $resultValue = if ($Mode -ceq "malformed_result" -and $index -eq 1) {
                "28oops"
            } elseif ($Mode -ceq "nonfinite_result" -and $index -eq 1) {
                "1e999"
            } else {
                "28"
            }
            $resultMessage = if ($Mode -in @(
                "exact_ontester", "malformed_result", "nonfinite_result",
                "wrong_result_pass", "cross_thread_result",
                "extra_malformed_result", "wrong_result_source"
            )) {
                "$resultPassId OnTester result $resultValue : passed in 0:00:00.800"
            } else {
                "$resultPassId : passed in 0:00:00.800"
            }
            $resultSource = if ($Mode -ceq "wrong_result_source" -and $index -eq 1) { "Runtime" } else { "Tester" }
            $agentLines += "BD`t0`t$resultTime`t$resultSource`t$resultMessage"
            if ($Mode -ceq "extra_malformed_result" -and $index -eq 1) {
                $agentLines += "BZ`t0`t$resultTime`tTester`t$passId OnTester result 28oops : passed in 0:00:00.800"
            }
        } elseif ($Mode -ceq "cross_thread_result" -and $index -eq 2) {
            $crossThreadResult = "BD`t0`t$resultTime`tTester`t$passId OnTester result 28 : passed in 0:00:00.800"
        }
        if ($Mode -ceq "duplicate_pass" -and $index -eq 1) {
            $agentLines += "BE`t0`t$resultTime`tTester`t$passId : passed in 0:00:00.801"
        }
        $agentLines += "BF`t0`t$resultTime`tTester`toptimization finished"
        $finishSymbol = if ($Mode -ceq "wrong_finish_symbol" -and $index -eq 2) { "GBPUSD" } else { "EURUSD" }
        $agentLines += "BG`t0`t$threadFinishTime`tTester`toptimize $agentExpert on $finishSymbol thread finished"
        [System.IO.File]::WriteAllText(
            (Join-Path $agentRoot "$today.log"),
            (($agentLines -join "`r`n") + "`r`n"),
            [System.Text.Encoding]::Unicode
        )
    }
    if ($Mode -ceq "cross_thread_result") {
        $otherAgentRoot = Join-Path $terminalAgentRoot "Agent-127.0.0.1-3999\logs"
        [void](New-Item -ItemType Directory -Path $otherAgentRoot -Force)
        [System.IO.File]::WriteAllText(
            (Join-Path $otherAgentRoot "$today.log"),
            "$crossThreadResult`r`n",
            [System.Text.Encoding]::Unicode
        )
    }
    $request = [pscustomobject]@{
        startBoundaryPath = $boundary
        dataPath = $dataPath
        expertUiPath = $expertUiPath
        expertFileName = "Strategy.ex5"
        expectedDeployedExpertSha256 = ("f" * 64)
        operationId = ("ea-visible-" + ("a" * 24))
        testerSettings = [pscustomobject]@{ period = "H1" }
    }
    $configured = [pscustomobject]@{ symbol = "EURUSD" }
    try {
        try {
            $evidence = Assert-TesterCleanCompletion $request $true $configured
            if ($Mode -in @("exact", "exact_ontester")) { return $evidence }
            return "unexpected-success"
        } catch { return [string]$_.Exception.Message }
    } finally {
        if ([System.IO.Directory]::Exists($terminalAgentRoot)) { [System.IO.Directory]::Delete($terminalAgentRoot, $true) }
    }
}
$root = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), ("metafx-opt6230-" + [Guid]::NewGuid().ToString("N")))
[void](New-Item -ItemType Directory -Path $root -Force)
try {
    @(
        (Invoke-ModernOptimizationCase $root "exact"),
        (Invoke-ModernOptimizationCase $root "exact_ontester"),
        (Invoke-ModernOptimizationCase $root "missing_pass"),
        (Invoke-ModernOptimizationCase $root "duplicate_pass"),
        (Invoke-ModernOptimizationCase $root "wrong_identity"),
        (Invoke-ModernOptimizationCase $root "wrong_pass_count"),
        (Invoke-ModernOptimizationCase $root "duplicate_start"),
        (Invoke-ModernOptimizationCase $root "pass_gap"),
        (Invoke-ModernOptimizationCase $root "fatal"),
        (Invoke-ModernOptimizationCase $root "missing_period"),
        (Invoke-ModernOptimizationCase $root "wrong_period"),
        (Invoke-ModernOptimizationCase $root "wrong_finish_symbol"),
        (Invoke-ModernOptimizationCase $root "malformed_result"),
        (Invoke-ModernOptimizationCase $root "nonfinite_result"),
        (Invoke-ModernOptimizationCase $root "wrong_result_pass"),
        (Invoke-ModernOptimizationCase $root "cross_thread_result"),
        (Invoke-ModernOptimizationCase $root "extra_malformed_result"),
        (Invoke-ModernOptimizationCase $root "wrong_result_source"),
        (Invoke-ModernOptimizationCase $root "wrong_start_source"),
        (Invoke-ModernOptimizationCase $root "oversized_pass")
    ) | ConvertTo-Json -Compress
} finally { Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue }
'''
        )
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "& ([scriptblock]::Create([Console]::In.ReadToEnd()))",
            ],
            input=harness,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        results = json.loads(completed.stdout.strip())
        self.assertEqual(
            results[2:],
            ["mt5_tester_clean_completion_unverified"] * 18,
        )
        for raw_evidence in results[:2]:
            evidence, _ = mt5._validate_tester_completion_evidence(
                raw_evidence,
                expected_marker="optimization_finished",
                expected_operation_id="ea-visible-" + ("a" * 24),
                expected_expert_file_name="Strategy.ex5",
                expected_expert_ui_path="Metafxclub\\AgentHQ\\Strategy",
                expected_deployed_expert_sha256="f" * 64,
                expected_symbol="EURUSD",
                expected_period="H1",
            )
            self.assertEqual(evidence["completionPassCount"], 3)
            self.assertGreaterEqual(evidence["coreThreadCount"], 3)
            self.assertFalse(evidence["coreDisconnectObserved"])

    def test_powershell_modern_agent_log_completion_is_exact_and_fail_closed(self) -> None:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        text = PS_PATH.read_text(encoding="utf-8")
        pairing = text[
            text.index("function Get-SharedUnicodeLogText") : text.index(
                "function Read-And-VerifyConfiguredTester"
            )
        ]
        harness = (
            'function Fail([string]$Code) { throw $Code }\n'
            + pairing
            + r'''
function Invoke-ModernAgentCase([string]$Root, [string]$Mode) {
    $dataPath = Join-Path $Root ("$Mode-" + [Guid]::NewGuid().ToString("N"))
    $coordinatorLogRoot = Join-Path $dataPath "Tester\logs"
    [void](New-Item -ItemType Directory -Path $coordinatorLogRoot -Force)
    $terminalIdentity = [System.IO.Path]::GetFileName($dataPath)
    $testerBase = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine(
        [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::ApplicationData),
        "MetaQuotes", "Tester"
    ))
    $terminalAgentRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($testerBase, $terminalIdentity))
    if (-not $terminalAgentRoot.StartsWith($testerBase + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw "unsafe-test-path" }
    $agentLogRoot = Join-Path $terminalAgentRoot "Agent-127.0.0.1-3000\logs"
    $otherAgentLogRoot = Join-Path $terminalAgentRoot "Agent-127.0.0.1-3001\logs"
    [void](New-Item -ItemType Directory -Path $agentLogRoot -Force)
    $boundary = Join-Path $Root "$Mode-boundary.json"
    [System.IO.File]::WriteAllText($boundary, "{}")
    $local = if ($Mode -ceq "stale") { [DateTime]::Now.AddMinutes(-2) } else { [DateTime]::Now.AddSeconds(2) }
    $today = $local.ToString("yyyyMMdd")
    $coordinatorTime = $local.ToString("HH:mm:ss.fff")
    $agentStartTime = $local.AddMilliseconds(100).ToString("HH:mm:ss.fff")
    $eventTime = $local.AddMilliseconds(250).ToString("HH:mm:ss.fff")
    $finishTime = $local.AddMilliseconds(500).ToString("HH:mm:ss.fff")
    $expertUiPath = "Metafxclub\AgentHQ\Strategy"
    $embeddedExpert = "Experts\$($expertUiPath).ex5"
    $coordinatorStart = "AA`t0`t$coordinatorTime`tTester`tvisual testing of $embeddedExpert on EURUSD,H1 from 2026.07.17 to 2026.10.14"
    $normalClose = "BB`t0`t$eventTime`tCore 01`tconnection closed"
    [System.IO.File]::WriteAllText(
        (Join-Path $coordinatorLogRoot "$today.log"),
        "$coordinatorStart`r`n$normalClose`r`n",
        [System.Text.Encoding]::Unicode
    )
    $agentStart = "CC`t0`t$agentStartTime`tTester`tEURUSD,H1: testing of $embeddedExpert from 2026.07.17 to 2026.10.14 started with inputs:"
    $secondStart = "DD`t0`t$eventTime`tTester`tEURUSD,H1: testing of $embeddedExpert from 2026.07.18 to 2026.10.14 started with inputs:"
    $otherRunStart = "DI`t0`t$eventTime`tTester`tGBPUSD,M15: testing of Experts\Metafxclub\AgentHQ\Other.ex5 from 2026.07.18 to 2026.10.14 started with inputs:"
    $fatal = "EE`t0`t$eventTime`tRuntime`tcritical error in tester worker"
    $disconnected = "FF`t0`t$eventTime`tNetwork`tagent disconnected"
    $finishIdentity = if ($Mode -ceq "wrong_identity") { "Experts\Metafxclub\AgentHQ\Other.ex5" } else { $embeddedExpert }
    $finishInfix = if ($Mode -ceq "forged_infix") { " forged" } else { "" }
    $finish = "GG`t0`t$finishTime`tTester`ttest $finishIdentity on EURUSD,H1$finishInfix thread finished"
    $agentLines = @($agentStart)
    if ($Mode -ceq "two_starts") { $agentLines += $secondStart }
    if ($Mode -ceq "intervening_other_run") { $agentLines += $otherRunStart }
    if ($Mode -ceq "fatal") { $agentLines += $fatal }
    if ($Mode -ceq "disconnected") { $agentLines += $disconnected }
    $agentLines += "HH`t0`t$eventTime`tTester`tfinal balance 10000.00 USD"
    if ($Mode -ceq "cross_path") {
        [void](New-Item -ItemType Directory -Path $otherAgentLogRoot -Force)
        [System.IO.File]::WriteAllText(
            (Join-Path $otherAgentLogRoot "$today.log"),
            "$finish`r`n",
            [System.Text.Encoding]::Unicode
        )
    } else {
        $agentLines += $finish
    }
    [System.IO.File]::WriteAllText(
        (Join-Path $agentLogRoot "$today.log"),
        (($agentLines -join "`r`n") + "`r`n"),
        [System.Text.Encoding]::Unicode
    )
    $request = [pscustomobject]@{
        startBoundaryPath = $boundary
        dataPath = $dataPath
        expertUiPath = $expertUiPath
        expertFileName = "Strategy.ex5"
        expectedDeployedExpertSha256 = ("f" * 64)
        operationId = ("ea-visible-" + ("a" * 24))
        testerSettings = [pscustomobject]@{ period = "H1" }
    }
    $configured = [pscustomobject]@{ symbol = "EURUSD" }
    try {
        try {
            $evidence = Assert-TesterCleanCompletion $request $false $configured
            if ($Mode -ceq "exact") { return $evidence }
            return "unexpected-success"
        } catch { return [string]$_.Exception.Message }
    } finally {
        if ([System.IO.Directory]::Exists($terminalAgentRoot)) { [System.IO.Directory]::Delete($terminalAgentRoot, $true) }
    }
}
$root = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), ("metafx-modern-agent-completion-" + [Guid]::NewGuid().ToString("N")))
[void](New-Item -ItemType Directory -Path $root -Force)
try {
    @(
        (Invoke-ModernAgentCase $root "exact"),
        (Invoke-ModernAgentCase $root "two_starts"),
        (Invoke-ModernAgentCase $root "intervening_other_run"),
        (Invoke-ModernAgentCase $root "cross_path"),
        (Invoke-ModernAgentCase $root "stale"),
        (Invoke-ModernAgentCase $root "fatal"),
        (Invoke-ModernAgentCase $root "disconnected"),
        (Invoke-ModernAgentCase $root "forged_infix"),
        (Invoke-ModernAgentCase $root "wrong_identity")
    ) | ConvertTo-Json -Compress
} finally { Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue }
'''
        )
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "& ([scriptblock]::Create([Console]::In.ReadToEnd()))",
            ],
            input=harness,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        results = json.loads(completed.stdout.strip())
        self.assertEqual(
            results[1:],
            ["mt5_tester_clean_completion_unverified"] * 8,
        )
        self.assertIsInstance(results[0], dict, results)
        exact, _ = mt5._validate_tester_completion_evidence(
            results[0],
            expected_marker="thread_finished",
            expected_operation_id="ea-visible-" + ("a" * 24),
            expected_expert_file_name="Strategy.ex5",
            expected_expert_ui_path="Metafxclub\\AgentHQ\\Strategy",
            expected_deployed_expert_sha256="f" * 64,
            expected_symbol="EURUSD",
            expected_period="H1",
        )
        self.assertEqual(exact["startLogPathSha256"], exact["completionLogPathSha256"])
        self.assertEqual(exact["startSourceSha256"], exact["completionSourceSha256"])
        self.assertEqual(exact["coreThreadCount"], 1)

    def test_powershell_screenshots_bind_signed_root_and_validate_dimensions(self) -> None:
        text = PS_PATH.read_text(encoding="utf-8")
        capture = text[
            text.index("function Capture-Window") : text.index(
                "function Get-AlgoTradingState"
            )
        ]
        load = text[
            text.index("function Load-And-VerifyInputSet") : text.index(
                "function Get-BoundTerminalRoot"
            )
        ]
        invoke = text[
            text.index("function Invoke-Tester(") : text.index('$request = $null')
        ]

        self.assertNotIn("Process.MainWindowHandle", capture)
        self.assertIn('$null -eq $Window', capture)
        self.assertIn("ExpectedHandle", capture)
        self.assertIn("Set-Foreground $Process $Window", capture)
        self.assertIn("[MetafxMt5VisibleNative]::IsWindow($handle)", capture)
        self.assertIn("[MetafxMt5VisibleNative]::IsWindowVisible($handle)", capture)
        self.assertIn("[MetafxMt5VisibleNative]::IsWindowEnabled($handle)", capture)
        self.assertIn("(Get-NativeOwner $handle) -ne $Process.Id", capture)
        self.assertIn("GetAncestor($handle, [MetafxMt5VisibleNative]::GA_ROOT)", capture)
        self.assertIn("GetWindowRect($handle, [ref]$rect)", capture)
        self.assertIn("GetWindowRect($handle, [ref]$postRect)", capture)
        self.assertIn("$postRect.Left -ne $rect.Left", capture)
        self.assertIn("$postRect.Bottom -ne $rect.Bottom", capture)
        self.assertIn("[System.Drawing.Image]::FromFile($Path)", capture)
        self.assertIn("$savedImage.Width -ne $width", capture)
        self.assertIn("$savedImage.Height -ne $height", capture)
        self.assertIn("[System.Drawing.Imaging.ImageFormat]::Png.Guid", capture)
        self.assertIn(
            "Capture-Window $TerminalProcess $Path $captureRoot "
            "([IntPtr]$script:TerminalRootHandle)",
            capture,
        )
        self.assertIn(
            "Capture-Window $TerminalProcess $ScreenshotPath $captureRoot "
            "([IntPtr]$script:TerminalRootHandle)",
            load,
        )
        # Settings, normal result, confirmed in-flight recovered result, and
        # report proof. Receipt-less recovery is fail-closed before capture.
        self.assertEqual(invoke.count("Capture-BoundTerminalWindow $Request"), 4)
        self.assertNotIn(
            "Capture-Window $TerminalProcess ([string]$Request.", invoke
        )

    def test_powershell_capture_window_uses_exact_root_and_fails_closed(self) -> None:
        require_interactive_ui_test(self)
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            screenshot = root / "bound-root.png"
            wrong_screenshot = root / "wrong-root.png"
            null_screenshot = root / "null-root.png"
            text = PS_PATH.read_text(encoding="utf-8")
            fragments = "\n".join(
                (
                    text[
                        text.index("function Fail(") : text.index(
                            "function Resolve-PopupDispatchFailureCode"
                        )
                    ],
                    text[
                        text.index("function Get-NativeOwner(") : text.index(
                            "function Assert-NativeControl("
                        )
                    ],
                    text[
                        text.index("function Set-Foreground(") : text.index(
                            "function Get-AlgoTradingState("
                        )
                    ],
                )
            )
            quoted_path = str(PS_PATH).replace("'", "''")
            screenshot_ps = str(screenshot).replace("'", "''")
            wrong_ps = str(wrong_screenshot).replace("'", "''")
            null_ps = str(null_screenshot).replace("'", "''")
            fragments_b64 = base64.b64encode(fragments.encode()).decode("ascii")
            harness = rf"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$text = Get-Content -Raw '{quoted_path}'
$marker = 'Add-Type @"'
$start = $text.IndexOf($marker) + $marker.Length
$end = $text.IndexOf('"@', $start)
if ($start -lt $marker.Length -or $end -lt 0) {{ throw 'native helper source missing' }}
Add-Type -TypeDefinition $text.Substring($start, $end - $start) -Language CSharp -ErrorAction Stop
$fragments = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{fragments_b64}'))
Invoke-Expression $fragments
$rootForm = New-Object System.Windows.Forms.Form
$otherForm = New-Object System.Windows.Forms.Form
$rootForm.Text = 'Signed MT5 Root Screenshot Harness'
$rootForm.Width = 640; $rootForm.Height = 480
$otherForm.Text = 'Transient Owned Window'
$otherForm.Width = 200; $otherForm.Height = 150
$label = New-Object System.Windows.Forms.Label
$label.Text = ('SIGNED ROOT ' * 80)
$label.Dock = [System.Windows.Forms.DockStyle]::Fill
$rootForm.Controls.Add($label)
$rootForm.Show(); $otherForm.Show()
[System.Windows.Forms.Application]::DoEvents()
try {{
  $process = [System.Diagnostics.Process]::GetCurrentProcess()
  $boundRoot = [System.Windows.Automation.AutomationElement]::FromHandle($rootForm.Handle)
  Capture-Window $process '{screenshot_ps}' $boundRoot ([IntPtr]$rootForm.Handle)
  $rect = [MetafxMt5VisibleNative+RECT]::new()
  if (-not [MetafxMt5VisibleNative]::GetWindowRect($rootForm.Handle, [ref]$rect)) {{ throw 'root rect unavailable' }}
  $image = [System.Drawing.Image]::FromFile('{screenshot_ps}')
  try {{ $width = $image.Width; $height = $image.Height }} finally {{ $image.Dispose() }}
  $mismatchRejected = $false
  try {{
    Capture-Window $process '{wrong_ps}' $boundRoot ([IntPtr]$otherForm.Handle)
  }} catch {{
    $mismatchRejected = $_.Exception.Message -ceq 'visible_screenshot_window_binding_mismatch'
  }}
  $nullRejected = $false
  try {{
    Capture-Window $process '{null_ps}' $null ([IntPtr]$rootForm.Handle)
  }} catch {{
    $nullRejected = $_.Exception.Message -ceq 'visible_screenshot_window_binding_missing'
  }}
  [ordered]@{{
    width = $width
    height = $height
    expectedWidth = ($rect.Right - $rect.Left)
    expectedHeight = ($rect.Bottom - $rect.Top)
    mismatchRejected = $mismatchRejected
    nullRejected = $nullRejected
    wrongFileCreated = [System.IO.File]::Exists('{wrong_ps}')
    nullFileCreated = [System.IO.File]::Exists('{null_ps}')
  }} | ConvertTo-Json -Compress
}} finally {{
  $otherForm.Close(); $rootForm.Close()
  $otherForm.Dispose(); $rootForm.Dispose()
}}
"""
            completed = subprocess.run(
                [
                    powershell,
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Sta",
                    "-EncodedCommand",
                    base64.b64encode(harness.encode("utf-16le")).decode("ascii"),
                ],
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            observed = json.loads(completed.stdout.strip())
            self.assertGreaterEqual(observed["width"], 320)
            self.assertGreaterEqual(observed["height"], 240)
            self.assertEqual(observed["width"], observed["expectedWidth"])
            self.assertEqual(observed["height"], observed["expectedHeight"])
            self.assertTrue(observed["mismatchRejected"])
            self.assertTrue(observed["nullRejected"])
            self.assertFalse(observed["wrongFileCreated"])
            self.assertFalse(observed["nullFileCreated"])

    def test_powershell_report_export_binds_native_results_list_and_popup_exactly(self) -> None:
        text = PS_PATH.read_text(encoding="utf-8")
        native = text[
            text.index("static void AssertExactListBinding") : text.index(
                "public static void DismissPopupMenuExact"
            )
        ]
        binding = text[
            text.index("function Get-ExactTesterResultsList") : text.index(
                "function Focus-UniqueResultsTable"
            )
        ]
        focus = text[
            text.index("function Focus-UniqueResultsTable") : text.index(
                "function Invoke-TesterResultsReportCommandExact"
            )
        ]
        command = text[
            text.index("function Invoke-TesterResultsReportCommandExact") : text.index(
                "function Save-VisibleReport"
            )
        ]
        save = text[
            text.index("function Save-VisibleReport") : text.index(
                "function Test-Mt5SetValueEquivalent"
            )
        ]

        self.assertIn('"SysListView32"', native)
        self.assertIn("expectedControlId", native)
        self.assertIn("GetDlgCtrlID(list) != expectedControlId", native)
        self.assertIn("GetAncestor(list, GA_ROOT) != expectedRoot", native)
        self.assertIn("GetGUIThreadInfo", native)
        self.assertIn("info.hwndFocus != list", native)
        self.assertIn("AttachThreadInput", native)
        self.assertIn("public static void FocusListExact", native)
        self.assertIn("public static void AssertListFocusExact", native)
        self.assertIn("public static void OpenListContextMenuExact", native)
        self.assertIn("PostMessage(list, WM_CONTEXTMENU, list, new IntPtr(-1))", native)
        self.assertNotIn("SendInput", native)
        self.assertNotIn("SetCursorPos", native)

        self.assertIn('$ExpectedTabName -cnotin @("Backtest", "Results", "Optimization Results")', binding)
        self.assertIn("Assert-TesterTabSelectedExact $tabs $ExpectedTabName", binding)
        self.assertIn('Read-TesterStartState $start "mt5_tester_not_idle"', binding)
        self.assertIn('ClassNameProperty,\n        "SysListView32"', binding)
        self.assertIn('$ExpectedTabName -ceq "Optimization Results"', binding)
        self.assertIn("10511", binding)
        self.assertIn("$observedControlId -ne $requiredControlId", binding)
        self.assertIn("controlId = $observedControlId", binding)
        self.assertNotIn("IsKeyboardFocusable", binding)

        self.assertIn("FocusListExact", focus)
        self.assertIn("AssertListFocusExact", focus)
        self.assertIn("Get-ExactTesterResultsList", focus)
        self.assertIn("immediate.listHandle", focus)

        self.assertIn("OpenListContextMenuExact", command)
        self.assertIn("CapturePopupMenuTokenExact", command)
        self.assertIn('"Export to XML (MS Office Excel)"', command)
        self.assertIn("33543", command)
        self.assertNotIn("expectedCommandId = if ($ExpectedTabName -ceq \"Optimization Results\") { 33553 }", command)
        self.assertIn('"HTML (Internet Explorer)"', command)
        self.assertIn("33420", command)
        self.assertIn('$expectedParentText = if ($ExpectedTabName -ceq "Optimization Results") { $null } else { "Report" }', command)
        self.assertIn("AssertPopupSubmenuCommandFromTokenExact", command)
        self.assertIn("InvokePopupSubmenuCommandExact", command)
        self.assertNotIn('-cin @("Save as Report", "Save Report")', command)
        self.assertIn("Get-ExactTesterResultsList", command)
        self.assertIn("AssertListFocusExact", command)
        self.assertIn("FindOwnedDialogExact", command)
        self.assertEqual(command.count("FindOwnedDialogExact"), 2)
        self.assertIn('"$($Code)_dispatch_preexisting_dialog"', command)
        self.assertIn("Get-ExactNativePopupMenuHost 0", command)
        self.assertIn("AssertPopupMenuCommandFromTokenExact", command)
        self.assertIn("InvokePopupMenuCommandExact", command)
        self.assertIn("DismissPopupMenuExact", command)
        self.assertIn(
            'Wait-ExactOwnedFileDialog @("Save As", "Save") '
            '"$($Code)_dispatch_unconfirmed"',
            command,
        )
        self.assertIn("return $confirmedDialog", command)
        self.assertEqual(command.count("$popupToken = $null"), 2)
        self.assertGreater(
            command.rindex("$popupToken = $null"),
            command.index("InvokePopupSubmenuCommandExact"),
        )
        self.assertLess(
            command.rindex("$popupToken = $null"),
            command.index("Wait-ExactOwnedFileDialog"),
        )
        self.assertLess(
            command.index("FindOwnedDialogExact"),
            command.index("OpenListContextMenuExact"),
        )
        self.assertLess(
            command.rindex("FindOwnedDialogExact"),
            command.index("InvokePopupMenuCommandExact"),
        )
        self.assertLess(
            command.index("Get-ExactTesterResultsList $Request $ExpectedTabName $Code"),
            command.index("InvokePopupMenuCommandExact"),
        )
        self.assertIn("$dispatchAttempted = $true", command)
        self.assertIn(
            "if ($null -ne $popupToken -and -not $dispatchAttempted)", command
        )

        self.assertIn("Focus-UniqueResultsTable $Request $expectedTabName", save)
        self.assertIn(
            "[IntPtr]$dialog = Invoke-TesterResultsReportCommandExact", save
        )
        self.assertNotIn(
            'Wait-ExactOwnedFileDialog @("Save As", "Save") '
            '"mt5_report_save_dialog_missing"',
            save,
        )
        self.assertIn('if ($expectedTabName -ceq "Optimization Results") { @(".xml") }', save)
        self.assertIn('if ($expectedTabName -ceq "Optimization Results") { 536870912L }', save)
        self.assertIn('"spreadsheetml"', save)
        self.assertIn('"html"', save)
        self.assertNotIn('SendWait("+{F10}")', save)
        self.assertNotIn("ControlType]::MenuItem", save)
        self.assertNotIn("Invoke-Exact $menuItem", save)
        self.assertIn(
            "Save-VisibleReport $Request $TerminalProcess $tabs $tabNames "
            "([string]$Request.testerReportExportPath) "
            "([string]$Request.testerReportPath)",
            text,
        )
        self.assertIn("reportFormat = [string]$reportEvidence.format", text)
        self.assertIn("reportTabName = [string]$reportEvidence.tabName", text)
        self.assertIn(
            'Get-StableCheckpointFile $Path $extension 1 $maximumBytes "mt5_tester_recovery_checkpoint_invalid" $false $true',
            text,
        )
        self.assertIn(
            'Get-StableCheckpointFile $ExportPath $extension 1 $maximumBytes "mt5_report_not_created" $false $true',
            save,
        )
        self.assertIn(
            "[System.IO.File]::Copy($ExportPath, $ArtifactPath, $false)",
            save,
        )
        self.assertIn(
            'Get-StableCheckpointFile $ArtifactPath $extension 1 $maximumBytes "mt5_report_artifact_not_created" $false $false',
            save,
        )
        self.assertIn(
            "if ([string]$artifactCheckpoint.sha256 -cne $digest)",
            save,
        )
        png_checkpoint = text[
            text.index("function Get-ExistingPngCheckpoint") : text.index(
                "function Get-ExistingReportEvidence"
            )
        ]
        self.assertNotIn("$true", png_checkpoint)
        self.assertNotIn("Stop-Process", save)
        self.assertNotIn("WM_CLOSE", save)

    def test_powershell_nested_report_submenu_identity_is_fail_closed(self) -> None:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        quoted_path = str(PS_PATH).replace("'", "''")
        harness = rf"""
$ErrorActionPreference = 'Stop'
$text = Get-Content -Raw '{quoted_path}'
$marker = 'Add-Type @"'
$start = $text.IndexOf($marker) + $marker.Length
$end = $text.IndexOf('"@', $start)
if ($start -lt $marker.Length -or $end -lt 0) {{ throw 'native helper source missing' }}
Add-Type -TypeDefinition $text.Substring($start, $end - $start) -Language CSharp -ErrorAction Stop
$menuSource = @'
using System;
using System.Runtime.InteropServices;
public static class MetafxNestedMenuHarness {{
  const uint MF_STRING = 0x0000;
  const uint MF_GRAYED = 0x0001;
  [DllImport("user32.dll", SetLastError=true)] static extern IntPtr CreatePopupMenu();
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool AppendMenu(IntPtr menu, uint flags, UIntPtr id, string text);
  [DllImport("user32.dll", SetLastError=true)] public static extern bool DestroyMenu(IntPtr menu);
  public static IntPtr Create(uint[] ids, string[] texts, bool[] enabled) {{
    if (ids == null || texts == null || enabled == null || ids.Length != texts.Length || ids.Length != enabled.Length)
      throw new InvalidOperationException("nested_menu_arguments_invalid");
    IntPtr menu = CreatePopupMenu();
    if (menu == IntPtr.Zero) throw new InvalidOperationException("nested_menu_create_failed");
    for (int index = 0; index < ids.Length; index++)
      if (!AppendMenu(menu, MF_STRING | (enabled[index] ? 0u : MF_GRAYED), (UIntPtr)ids[index], texts[index])) {{
        DestroyMenu(menu);
        throw new InvalidOperationException("nested_menu_append_failed");
      }}
    return menu;
  }}
}}
'@
Add-Type -TypeDefinition $menuSource -Language CSharp -ErrorAction Stop
$snapshotType = [MetafxMt5VisibleNative].GetNestedType('MENUITEMSNAPSHOT', [Reflection.BindingFlags]::Public)
$method = [MetafxMt5VisibleNative].GetMethod(
  'FindPopupSubmenuCommandExact',
  [Reflection.BindingFlags]::NonPublic -bor [Reflection.BindingFlags]::Static
)
if ($null -eq $snapshotType -or $null -eq $method) {{ throw 'nested submenu verifier missing' }}
function New-ParentArray([IntPtr]$submenu, [string[]]$texts, [bool[]]$hasSubmenus) {{
  $items = [Array]::CreateInstance($snapshotType, $texts.Length)
  for ($index = 0; $index -lt $texts.Length; $index++) {{
    $item = [Activator]::CreateInstance($snapshotType)
    $item.Position = $index
    $item.CommandId = [uint32]0
    $item.Text = $texts[$index]
    $item.State = [uint32]0
    $item.IsEnabled = $true
    $item.IsSeparator = $false
    $item.HasSubmenu = $hasSubmenus[$index]
    $item.SubmenuHandle = if ($hasSubmenus[$index]) {{ $submenu }} else {{ [IntPtr]::Zero }}
    $item.ItemData = [UIntPtr]::Zero
    $item.TextLength = [uint32]$texts[$index].Length
    $items.SetValue($item, $index)
  }}
  return ,$items
}}
function Invoke-NestedVerifier([Array]$parents, [string]$parentText, [string]$commandText, [uint32]$commandId) {{
  $arguments = [object[]]::new(4)
  $arguments[0] = $parents
  $arguments[1] = $parentText
  $arguments[2] = $commandText
  $arguments[3] = $commandId
  try {{ return $method.Invoke($null, $arguments) }}
  catch [Reflection.TargetInvocationException] {{ throw $_.Exception.InnerException }}
}}
function Test-Rejected([scriptblock]$operation) {{
  try {{ [void](& $operation); return $false }} catch {{ return $true }}
}}
$menus = @()
try {{
  $validMenu = [MetafxNestedMenuHarness]::Create(
    [uint32[]]@(33419,33420),
    [string[]]@('Open XML (MS Office Excel 2007)','HTML (Internet Explorer)'),
    [bool[]]@($true,$true)
  )
  $menus += $validMenu
  # Build 6230 legitimately contains both a display-mode leaf named Report
  # and a distinct export submenu named Report.  Only the submenu is eligible.
  $validParents = New-ParentArray $validMenu @('Report','Report') @($false,$true)
  $valid = Invoke-NestedVerifier $validParents 'Report' 'HTML (Internet Explorer)' ([uint32]33420)
  $wrongParentRejected = Test-Rejected {{ Invoke-NestedVerifier $validParents 'report' 'HTML (Internet Explorer)' ([uint32]33420) }}
  $wrongCaptionRejected = Test-Rejected {{ Invoke-NestedVerifier $validParents 'Report' 'HTML (Internet Explorer) forged' ([uint32]33420) }}
  $wrongIdRejected = Test-Rejected {{ Invoke-NestedVerifier $validParents 'Report' 'HTML (Internet Explorer)' ([uint32]33419) }}
  $caseVariantRejected = Test-Rejected {{ Invoke-NestedVerifier $validParents 'Report' 'html (Internet Explorer)' ([uint32]33420) }}
  $duplicateParent = New-ParentArray $validMenu @('Report','Report','Report') @($false,$true,$true)
  $duplicateParentRejected = Test-Rejected {{ Invoke-NestedVerifier $duplicateParent 'Report' 'HTML (Internet Explorer)' ([uint32]33420) }}
  $forgedLeaf = New-ParentArray $validMenu @('HTML (Internet Explorer)') @($false)
  $forgedTopLevelLeafRejected = Test-Rejected {{ Invoke-NestedVerifier $forgedLeaf 'Report' 'HTML (Internet Explorer)' ([uint32]33420) }}

  $duplicateTextMenu = [MetafxNestedMenuHarness]::Create(
    [uint32[]]@(33420,33421),
    [string[]]@('HTML (Internet Explorer)','HTML (Internet Explorer)'),
    [bool[]]@($true,$true)
  )
  $menus += $duplicateTextMenu
  $duplicateTextParents = New-ParentArray $duplicateTextMenu @('Report') @($true)
  $duplicateTextRejected = Test-Rejected {{ Invoke-NestedVerifier $duplicateTextParents 'Report' 'HTML (Internet Explorer)' ([uint32]33420) }}

  $duplicateIdMenu = [MetafxNestedMenuHarness]::Create(
    [uint32[]]@(33420,33420),
    [string[]]@('HTML (Internet Explorer)','Forged export'),
    [bool[]]@($true,$true)
  )
  $menus += $duplicateIdMenu
  $duplicateIdParents = New-ParentArray $duplicateIdMenu @('Report') @($true)
  $duplicateIdRejected = Test-Rejected {{ Invoke-NestedVerifier $duplicateIdParents 'Report' 'HTML (Internet Explorer)' ([uint32]33420) }}

  $disabledMenu = [MetafxNestedMenuHarness]::Create(
    [uint32[]]@(33420),
    [string[]]@('HTML (Internet Explorer)'),
    [bool[]]@($false)
  )
  $menus += $disabledMenu
  $disabledParents = New-ParentArray $disabledMenu @('Report') @($true)
  $disabledRejected = Test-Rejected {{ Invoke-NestedVerifier $disabledParents 'Report' 'HTML (Internet Explorer)' ([uint32]33420) }}

  [ordered]@{{
    validText=[string]$valid.Text
    validId=[long]$valid.CommandId
    wrongParentRejected=$wrongParentRejected
    wrongCaptionRejected=$wrongCaptionRejected
    wrongIdRejected=$wrongIdRejected
    caseVariantRejected=$caseVariantRejected
    duplicateParentRejected=$duplicateParentRejected
    forgedTopLevelLeafRejected=$forgedTopLevelLeafRejected
    duplicateTextRejected=$duplicateTextRejected
    duplicateIdRejected=$duplicateIdRejected
    disabledRejected=$disabledRejected
  }} | ConvertTo-Json -Compress
}} finally {{
  foreach ($menu in $menus) {{ if ($menu -ne [IntPtr]::Zero) {{ [void][MetafxNestedMenuHarness]::DestroyMenu($menu) }} }}
}}
"""
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Sta",
                "-EncodedCommand",
                base64.b64encode(harness.encode("utf-16le")).decode("ascii"),
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        observed = json.loads(completed.stdout.strip())
        self.assertEqual(observed["validText"], "HTML (Internet Explorer)")
        self.assertEqual(observed["validId"], 33420)
        for key, value in observed.items():
            if key.endswith("Rejected"):
                self.assertTrue(value, key)

    def test_powershell_submenu_materialization_is_narrow_and_fail_closed(self) -> None:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        quoted_path = str(PS_PATH).replace("'", "''")
        harness = rf"""
$ErrorActionPreference = 'Stop'
$text = Get-Content -Raw '{quoted_path}'
$marker = 'Add-Type @"'
$start = $text.IndexOf($marker) + $marker.Length
$end = $text.IndexOf('"@', $start)
if ($start -lt $marker.Length -or $end -lt 0) {{ throw 'native helper source missing' }}
Add-Type -TypeDefinition $text.Substring($start, $end - $start) -Language CSharp -ErrorAction Stop
$snapshotType = [MetafxMt5VisibleNative].GetNestedType('MENUITEMSNAPSHOT', [Reflection.BindingFlags]::Public)
$compare = [MetafxMt5VisibleNative].GetMethod(
  'SamePopupSubmenuItemAfterOpen',
  [Reflection.BindingFlags]::NonPublic -bor [Reflection.BindingFlags]::Static
)
if ($null -eq $snapshotType -or $null -eq $compare) {{ throw 'submenu materialization comparator missing' }}
function New-Snapshot([string]$textValue, [uint32]$commandId, [uint32]$state, [UInt64]$itemData) {{
  $item = [Activator]::CreateInstance($snapshotType)
  $item.Position = 1
  $item.CommandId = $commandId
  $item.Text = $textValue
  $item.State = $state
  $item.IsEnabled = ($state -band 3) -eq 0
  $item.IsSeparator = $false
  $item.HasSubmenu = $false
  $item.SubmenuHandle = [IntPtr]::Zero
  $item.ItemData = [UIntPtr]$itemData
  $item.TextLength = [uint32]$textValue.Length
  return $item
}}
function Test-Compare([object]$before, [object]$after) {{
  return [bool]$compare.Invoke($null, [object[]]@($before, $after))
}}
$before = New-Snapshot 'HTML (Internet Explorer)' ([uint32]33420) 0 0
$materialized = New-Snapshot 'HTML (Internet Explorer)' ([uint32]33420) 0 65666
$sameZero = New-Snapshot 'HTML (Internet Explorer)' ([uint32]33420) 0 0
$sameNonzeroBefore = New-Snapshot 'HTML (Internet Explorer)' ([uint32]33420) 0 65666
$sameNonzeroAfter = New-Snapshot 'HTML (Internet Explorer)' ([uint32]33420) 0 65666
$changedNonzero = New-Snapshot 'HTML (Internet Explorer)' ([uint32]33420) 0 65711
$highlightOnly = New-Snapshot 'HTML (Internet Explorer)' ([uint32]33420) 128 65666
$wrongText = New-Snapshot 'HTML (Internet Explorer) forged' ([uint32]33420) 0 65666
$wrongId = New-Snapshot 'HTML (Internet Explorer)' ([uint32]33419) 0 65666
$disabled = New-Snapshot 'HTML (Internet Explorer)' ([uint32]33420) 3 65666
$wrongLength = New-Snapshot 'HTML (Internet Explorer)' ([uint32]33420) 0 65666
$wrongLength.TextLength = [uint32]23
[ordered]@{{
  zeroToNonzeroAccepted = Test-Compare $before $materialized
  sameZeroAccepted = Test-Compare $before $sameZero
  sameNonzeroAccepted = Test-Compare $sameNonzeroBefore $sameNonzeroAfter
  highlightOnlyAccepted = Test-Compare $before $highlightOnly
  changedNonzeroRejected = -not (Test-Compare $sameNonzeroBefore $changedNonzero)
  wrongTextRejected = -not (Test-Compare $before $wrongText)
  wrongIdRejected = -not (Test-Compare $before $wrongId)
  disabledRejected = -not (Test-Compare $before $disabled)
  wrongLengthRejected = -not (Test-Compare $before $wrongLength)
}} | ConvertTo-Json -Compress
"""
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "& ([scriptblock]::Create([Console]::In.ReadToEnd()))",
            ],
            input=harness,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        observed = json.loads(completed.stdout.strip())
        for key, value in observed.items():
            self.assertTrue(value, key)

    def test_powershell_popup_token_rebind_accepts_only_highlight_drift(self) -> None:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        quoted_path = str(PS_PATH).replace("'", "''")
        harness = rf"""
$ErrorActionPreference = 'Stop'
$text = Get-Content -Raw '{quoted_path}'
$marker = 'Add-Type @"'
$start = $text.IndexOf($marker) + $marker.Length
$end = $text.IndexOf('"@', $start)
if ($start -lt $marker.Length -or $end -lt 0) {{ throw 'native helper source missing' }}
Add-Type -TypeDefinition $text.Substring($start, $end - $start) -Language CSharp -ErrorAction Stop
$flags = [Reflection.BindingFlags]::NonPublic -bor [Reflection.BindingFlags]::Static
$snapshotType = [MetafxMt5VisibleNative].GetNestedType('MENUITEMSNAPSHOT', [Reflection.BindingFlags]::Public)
$tokenType = [MetafxMt5VisibleNative].GetNestedType('POPUPMENUTOKEN', [Reflection.BindingFlags]::Public)
$compare = [MetafxMt5VisibleNative].GetMethod('SamePopupMenuTokenIgnoringHighlight', $flags)
if ($null -eq $snapshotType -or $null -eq $tokenType -or $null -eq $compare) {{
  throw 'popup token comparator missing'
}}
function New-Snapshot(
  [int]$position = 0,
  [uint32]$commandId = 33160,
  [string]$textValue = 'Load',
  [uint32]$state = 0,
  [bool]$enabled = $true,
  [bool]$separator = $false,
  [bool]$hasSubmenu = $false,
  [long]$submenuHandle = 0,
  [UInt64]$itemData = 41,
  [uint32]$textLength = 4
) {{
  $item = [Activator]::CreateInstance($snapshotType)
  $item.Position = $position
  $item.CommandId = $commandId
  $item.Text = $textValue
  $item.State = $state
  $item.IsEnabled = $enabled
  $item.IsSeparator = $separator
  $item.HasSubmenu = $hasSubmenu
  $item.SubmenuHandle = [IntPtr]$submenuHandle
  $item.ItemData = [UIntPtr]$itemData
  $item.TextLength = $textLength
  return $item
}}
function New-Token(
  [object]$item,
  [long]$popupWindow = 101,
  [long]$menuHandle = 202,
  [long]$commandOwner = 303,
  [uint32]$menuThreadId = 404,
  [int]$itemCount = 1
) {{
  $token = [Activator]::CreateInstance($tokenType)
  $token.PopupWindow = [IntPtr]$popupWindow
  $token.MenuHandle = [IntPtr]$menuHandle
  $token.CommandOwner = [IntPtr]$commandOwner
  $token.MenuThreadId = $menuThreadId
  $items = [Array]::CreateInstance($snapshotType, $itemCount)
  for ($index = 0; $index -lt $itemCount; $index++) {{ $items.SetValue($item, $index) }}
  $token.Items = $items
  return $token
}}
function Test-Same([object]$left, [object]$right) {{
  $arguments = [object[]]::new(2)
  $arguments[0] = $left
  $arguments[1] = $right
  return [bool]$compare.Invoke($null, $arguments)
}}
$base = New-Token (New-Snapshot)
$highlighted = New-Token (New-Snapshot -state 128)
$nullItems = New-Token (New-Snapshot)
$nullItems.Items = $null
[ordered]@{{
  identicalAccepted = Test-Same $base (New-Token (New-Snapshot))
  highlightOnlyAccepted = Test-Same $base $highlighted
  highlightOnlyReverseAccepted = Test-Same $highlighted $base
  nullRejected = -not (Test-Same $base $null)
  nullItemsRejected = -not (Test-Same $base $nullItems)
  nullItemRejected = -not (Test-Same $base (New-Token $null))
  popupWindowRejected = -not (Test-Same $base (New-Token (New-Snapshot) -popupWindow 102))
  menuHandleRejected = -not (Test-Same $base (New-Token (New-Snapshot) -menuHandle 203))
  commandOwnerRejected = -not (Test-Same $base (New-Token (New-Snapshot) -commandOwner 304))
  menuThreadRejected = -not (Test-Same $base (New-Token (New-Snapshot) -menuThreadId 405))
  itemCountRejected = -not (Test-Same $base (New-Token (New-Snapshot) -itemCount 2))
  positionRejected = -not (Test-Same $base (New-Token (New-Snapshot -position 1)))
  commandIdRejected = -not (Test-Same $base (New-Token (New-Snapshot -commandId 33159)))
  textRejected = -not (Test-Same $base (New-Token (New-Snapshot -textValue 'Save')))
  nonHighlightStateRejected = -not (Test-Same $base (New-Token (New-Snapshot -state 1)))
  enabledRejected = -not (Test-Same $base (New-Token (New-Snapshot -enabled $false)))
  separatorRejected = -not (Test-Same $base (New-Token (New-Snapshot -separator $true)))
  submenuFlagRejected = -not (Test-Same $base (New-Token (New-Snapshot -hasSubmenu $true)))
  submenuHandleRejected = -not (Test-Same $base (New-Token (New-Snapshot -submenuHandle 44)))
  itemDataRejected = -not (Test-Same $base (New-Token (New-Snapshot -itemData 42)))
  textLengthRejected = -not (Test-Same $base (New-Token (New-Snapshot -textLength 5)))
  highlightPlusIdentityRejected = -not (Test-Same $base (New-Token (New-Snapshot -state 128 -itemData 42)))
}} | ConvertTo-Json -Compress
"""
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "& ([scriptblock]::Create([Console]::In.ReadToEnd()))",
            ],
            input=harness,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        observed = json.loads(completed.stdout.strip())
        for key, value in observed.items():
            self.assertTrue(value, key)

        native = PS_PATH.read_text(encoding="utf-8")
        rebind = native[
            native.index("public static POPUPMENUTOKEN RebindPopupMenuTokenIgnoringHighlightExact") : native.index(
                "static MENUITEMSNAPSHOT FindPopupMenuCommandExact"
            )
        ]
        rebound_assert = native[
            native.index("static void AssertReboundPopupMenuTokenIdentityExact") : native.index(
                "public static MENUITEMSNAPSHOT AssertPopupMenuCommandExact(IntPtr"
            )
        ]
        rebound_dispatch = native[
            native.index("public static MENUITEMSNAPSHOT InvokePopupMenuCommandFromReboundTokenExact") : native.index(
                "public static MENUITEMSNAPSHOT InvokePopupMenuCommandExact(IntPtr"
            )
        ]
        self.assertEqual(rebind.count("CapturePopupMenuTokenExact"), 1)
        self.assertIn("SamePopupMenuTokenIgnoringHighlight(expected, current)", rebind)
        self.assertNotIn("SamePopupMenuToken(expected, current)", rebind)
        self.assertIn("AssertReboundPopupMenuTokenIdentityExact", rebound_assert)
        self.assertIn("FindPopupMenuCommandExact(current.Items", rebound_assert)
        self.assertNotIn("CapturePopupMenuTokenExact", rebound_assert)
        self.assertIn("AssertReboundPopupMenuTokenIdentityExact", rebound_dispatch)
        self.assertIn("InvokePopupMenuCommandCurrentTokenExact(current", rebound_dispatch)
        self.assertNotIn("CapturePopupMenuTokenExact", rebound_dispatch)
        self.assertNotIn("for (", rebound_dispatch)
        self.assertNotIn("while (", rebound_dispatch)

    def test_powershell_popup_dispatch_failure_reason_mapping_is_exact(self) -> None:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        text = PS_PATH.read_text(encoding="utf-8")
        resolver = text[
            text.index("function Resolve-PopupDispatchFailureCode") : text.index(
                "function Enter-OperationMutex"
            )
        ]
        command = text[
            text.index("function Invoke-TesterResultsReportCommandExact") : text.index(
                "function Save-VisibleReport"
            )
        ]
        inputs_command = text[
            text.index("function Invoke-TesterInputsContextCommandExact") : text.index(
                "function Restore-TesterSettingsTabExact"
            )
        ]
        self.assertIn('Resolve-PopupDispatchFailureCode $_ $Code "popup_bind"', command)
        self.assertIn('Resolve-PopupDispatchFailureCode $_ $Code "preflight"', command)
        self.assertIn('Resolve-PopupDispatchFailureCode $_ $Code "dispatch"', command)
        self.assertNotIn('catch { Fail "$($Code)_dispatch_ambiguous" }', command)
        self.assertIn(
            'Resolve-PopupDispatchFailureCode $_ $Code "popup_bind"', inputs_command
        )
        self.assertEqual(
            inputs_command.count(
                'Resolve-PopupDispatchFailureCode $_ $Code "preflight"'
            ),
            2,
        )
        self.assertIn(
            'Resolve-PopupDispatchFailureCode $_ $Code "dispatch"', inputs_command
        )
        self.assertNotIn(
            'catch { Fail "$($Code)_dispatch_ambiguous" }', inputs_command
        )
        expected_reasons = {
            "mt5_popup_menu_changed",
            "mt5_popup_menu_class_invalid",
            "mt5_popup_menu_command_dispatch_ambiguous",
            "mt5_popup_menu_command_invalid",
            "mt5_popup_menu_command_owner_invalid",
            "mt5_popup_menu_handle_changed",
            "mt5_popup_menu_handle_invalid",
            "mt5_popup_menu_item_count_invalid",
            "mt5_popup_menu_item_invalid",
            "mt5_popup_menu_item_rect_invalid",
            "mt5_popup_menu_layout_invalid",
            "mt5_popup_menu_owner_invalid",
            "mt5_popup_menu_selection_failed",
            "mt5_popup_menu_text_invalid",
            "mt5_popup_menu_token_invalid",
            "mt5_popup_submenu_changed",
            "mt5_popup_submenu_handle_invalid",
            "mt5_popup_submenu_host_ambiguous",
            "mt5_popup_submenu_invalid",
            "mt5_popup_submenu_open_failed",
        }
        mapped_reasons = set(re.findall(r'"(mt5_popup_[^"]+)"\s*\{', resolver))
        self.assertEqual(mapped_reasons, expected_reasons)
        native_dispatch = text[
            text.index("static IntPtr AssertPopupMenuOwner") : text.index(
                "public static MENUITEMSNAPSHOT InvokePopupMenuCommandExact(IntPtr"
            )
        ]
        thrown_reasons = set(
            re.findall(
                r'InvalidOperationException\("(mt5_popup_[^"]+)"\)',
                native_dispatch,
            )
        )
        self.assertEqual(thrown_reasons, expected_reasons)

        resolver_b64 = base64.b64encode(resolver.encode("utf-16le")).decode("ascii")
        harness = rf"""
$ErrorActionPreference = 'Stop'
$resolver = [System.Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('{resolver_b64}'))
Invoke-Expression $resolver
function New-Record([System.Exception]$exception) {{
  return [System.Management.Automation.ErrorRecord]::new(
    $exception, 'popup-test', [System.Management.Automation.ErrorCategory]::NotSpecified, $null
  )
}}
function Resolve-Test([System.Exception]$exception, [string]$stage) {{
  return Resolve-PopupDispatchFailureCode (New-Record $exception) 'report_code' $stage
}}
function Resolve-BaselineTest([System.Exception]$exception, [string]$stage) {{
  return Resolve-PopupDispatchFailureCode (New-Record $exception) 'mt5_optimization_baseline_save_command_not_verified' $stage
}}
$known = [System.InvalidOperationException]::new('mt5_popup_submenu_changed')
$selection = [System.InvalidOperationException]::new('mt5_popup_menu_selection_failed')
$wrappedKnown = [System.Management.Automation.MethodInvocationException]::new('wrapped', $known)
$ambiguous = [System.Management.Automation.MethodInvocationException]::new(
  'wrapped', [System.InvalidOperationException]::new('mt5_popup_menu_command_dispatch_ambiguous')
)
$overdeep = [System.Management.Automation.MethodInvocationException]::new(
  'one', [System.Reflection.TargetInvocationException]::new(
    [System.Management.Automation.MethodInvocationException]::new('three', $known)
  )
)
$knownWithInner = [System.InvalidOperationException]::new(
  'mt5_popup_submenu_changed', [System.Exception]::new('forged inner')
)
[ordered]@{{
  wrappedKnown = Resolve-Test $wrappedKnown 'dispatch'
  directKnown = Resolve-Test $known 'preflight'
  trueAmbiguous = Resolve-Test $ambiguous 'dispatch'
  baselineSelection = Resolve-BaselineTest $selection 'dispatch'
  baselineAmbiguous = Resolve-BaselineTest $ambiguous 'dispatch'
  wrongStageAmbiguous = Resolve-Test $ambiguous 'preflight'
  uppercase = Resolve-Test ([System.InvalidOperationException]::new('MT5_POPUP_SUBMENU_CHANGED')) 'dispatch'
  whitespace = Resolve-Test ([System.InvalidOperationException]::new('mt5_popup_submenu_changed ')) 'dispatch'
  suffix = Resolve-Test ([System.InvalidOperationException]::new('mt5_popup_submenu_changed_forged')) 'dispatch'
  substring = Resolve-Test ([System.InvalidOperationException]::new('prefix mt5_popup_submenu_changed')) 'dispatch'
  wrongType = Resolve-Test ([System.ArgumentException]::new('mt5_popup_submenu_changed')) 'dispatch'
  overdeep = Resolve-Test $overdeep 'dispatch'
  knownWithInner = Resolve-Test $knownWithInner 'dispatch'
  invalidStage = Resolve-Test $known 'DISPATCH'
}} | ConvertTo-Json -Compress
"""
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-EncodedCommand",
                base64.b64encode(harness.encode("utf-16le")).decode("ascii"),
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        observed = json.loads(completed.stdout.strip())
        self.assertEqual(observed["wrappedKnown"], "report_code_dispatch_submenu_changed")
        self.assertEqual(observed["directKnown"], "report_code_preflight_submenu_changed")
        self.assertEqual(observed["trueAmbiguous"], "report_code_dispatch_ambiguous")
        self.assertEqual(
            observed["baselineSelection"],
            "mt5_optimization_baseline_save_command_not_verified_dispatch_selection_failed",
        )
        self.assertEqual(
            observed["baselineAmbiguous"],
            "mt5_optimization_baseline_save_command_not_verified_dispatch_ambiguous",
        )
        self.assertEqual(observed["wrongStageAmbiguous"], "report_code_preflight_unexpected")
        self.assertEqual(observed["invalidStage"], "report_code_dispatch_unexpected")
        for key in (
            "uppercase",
            "whitespace",
            "suffix",
            "substring",
            "wrongType",
            "overdeep",
            "knownWithInner",
        ):
            self.assertEqual(observed[key], "report_code_dispatch_unexpected", key)

    def test_powershell_report_reader_allows_writer_without_weakening_generic_checkpoints(self) -> None:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        with tempfile.TemporaryDirectory(prefix="mt5-ps-report-share-") as temporary:
            report = Path(temporary) / "optimization.xml"
            report.write_bytes(b"<Workbook><Row>stable</Row></Workbook>")
            quoted_script = str(PS_PATH).replace("'", "''")
            quoted_report = str(report).replace("'", "''")
            expected_digest = sha256_bytes(report.read_bytes())
            harness = rf"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$text = Get-Content -Raw '{quoted_script}'
$marker = 'Add-Type @"'
$nativeStart = $text.IndexOf($marker) + $marker.Length
$nativeEnd = $text.IndexOf('"@', $nativeStart)
if ($nativeStart -lt $marker.Length -or $nativeEnd -lt 0) {{ throw 'native helper source missing' }}
Add-Type -TypeDefinition $text.Substring($nativeStart, $nativeEnd - $nativeStart) -Language CSharp -ReferencedAssemblies @('System.Windows.Forms.dll','System.Drawing.dll') -ErrorAction Stop
function Fail([string]$Code) {{ throw [System.InvalidOperationException]::new($Code) }}
$stableStart = $text.IndexOf('function Get-StableCheckpointFile')
$stableEnd = $text.IndexOf('function Get-ExistingPngCheckpoint', $stableStart)
Invoke-Expression $text.Substring($stableStart, $stableEnd - $stableStart)
$path = '{quoted_report}'
$writer = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::ReadWrite)
try {{
    $reportEvidence = Get-StableCheckpointFile $path '.xml' 1 536870912 'report_reader_rejected_writer' $false $true
    $strictRejected = $false
    try {{
        [void](Get-StableCheckpointFile $path '.xml' 1 536870912 'strict_checkpoint_rejected' $false $false)
    }} catch {{
        if ([string]$_.Exception.Message -cne 'strict_checkpoint_rejected') {{ throw }}
        $strictRejected = $true
    }}
    [ordered]@{{
        sha256 = [string]$reportEvidence.sha256
        byteSize = [long]$reportEvidence.byteSize
        strictRejected = [bool]$strictRejected
    }} | ConvertTo-Json -Compress
}} finally {{
    $writer.Dispose()
}}
"""
            completed = subprocess.run(
                [
                    powershell,
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-EncodedCommand",
                    base64.b64encode(harness.encode("utf-16le")).decode("ascii"),
                ],
                text=True,
                capture_output=True,
                timeout=60,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            evidence = json.loads(completed.stdout.strip())
            self.assertEqual(evidence["sha256"], expected_digest)
            self.assertEqual(evidence["byteSize"], report.stat().st_size)
            self.assertTrue(evidence["strictRejected"])

    def test_powershell_native_results_list_focus_is_exact_and_id_guarded(self) -> None:
        require_interactive_ui_test(self)
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        quoted_path = str(PS_PATH).replace("'", "''")
        harness = rf"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class ResultsListHarnessNative {{
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  public static extern IntPtr CreateWindowEx(uint exStyle, string className, string title, uint style,
    int x, int y, int width, int height, IntPtr parent, IntPtr menu, IntPtr instance, IntPtr parameter);
}}
'@
$text = Get-Content -Raw '{quoted_path}'
$marker = 'Add-Type @"'
$start = $text.IndexOf($marker) + $marker.Length
$end = $text.IndexOf('"@', $start)
if ($start -lt $marker.Length -or $end -lt 0) {{ throw 'native helper source missing' }}
Add-Type -TypeDefinition $text.Substring($start, $end - $start) -Language CSharp -ReferencedAssemblies @('System.Windows.Forms.dll','System.Drawing.dll') -ErrorAction Stop
$form = New-Object System.Windows.Forms.Form
$form.Text = 'Signed MT5 Root'
$form.ShowInTaskbar = $false
$form.Show()
[System.Windows.Forms.Application]::DoEvents()
try {{
    [IntPtr]$list = [ResultsListHarnessNative]::CreateWindowEx(
        0, 'SysListView32', '', [uint32]0x50010001,
        0, 0, 400, 200, $form.Handle, [IntPtr]10511, [IntPtr]::Zero, [IntPtr]::Zero
    )
    if ($list -eq [IntPtr]::Zero) {{ throw 'native results list creation failed' }}
    [uint32]$foregroundPid = 0
    [IntPtr]$foreground = [MetafxMt5VisibleNative]::GetForegroundWindow()
    [uint32]$foregroundThread = [MetafxMt5VisibleNative]::GetWindowThreadProcessId($foreground, [ref]$foregroundPid)
    [uint32]$currentThread = [MetafxMt5VisibleNative]::GetCurrentThreadId()
    $attached = $false
    try {{
        if ($foregroundThread -ne 0 -and $foregroundThread -ne $currentThread) {{
            $attached = [MetafxMt5VisibleNative]::AttachThreadInput($currentThread, $foregroundThread, $true)
        }}
        [void][MetafxMt5VisibleNative]::ShowWindowAsync($form.Handle, 9)
        [void][MetafxMt5VisibleNative]::BringWindowToTop($form.Handle)
        [void][MetafxMt5VisibleNative]::SetForegroundWindow($form.Handle)
        [void][MetafxMt5VisibleNative]::SetActiveWindow($form.Handle)
        [void][MetafxMt5VisibleNative]::SetFocus($form.Handle)
        [System.Windows.Forms.Application]::DoEvents()
    }} finally {{
        if ($attached) {{ [void][MetafxMt5VisibleNative]::AttachThreadInput($currentThread, $foregroundThread, $false) }}
    }}
    [MetafxMt5VisibleNative]::FocusListExact($list, [uint32]$PID, $form.Handle, 10511)
    [MetafxMt5VisibleNative]::AssertListFocusExact($list, [uint32]$PID, $form.Handle, 10511)
    $wrongIdRejected = $false
    try {{
        [MetafxMt5VisibleNative]::AssertListFocusExact($list, [uint32]$PID, $form.Handle, 10512)
    }} catch {{
        $message = if ($null -ne $_.Exception.InnerException) {{ $_.Exception.InnerException.Message }} else {{ $_.Exception.Message }}
        $wrongIdRejected = $message -ceq 'mt5_results_list_invalid'
    }}
    if (-not $wrongIdRejected) {{ throw 'wrong results-list control id was accepted' }}
    'results-list-focus-ok'
}} finally {{
    $form.Close()
    $form.Dispose()
}}
"""
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Sta",
                "-EncodedCommand",
                base64.b64encode(harness.encode("utf-16le")).decode("ascii"),
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "results-list-focus-ok")

    def test_powershell_start_boundary_helper_rejects_hardlink(self) -> None:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        with tempfile.TemporaryDirectory(prefix="mt5-ps-boundary-") as temporary:
            boundary = Path(temporary) / "start-boundary.json"
            boundary.write_bytes(b'{"operationId":"test"}')
            alias = Path(temporary) / "start-boundary-alias.json"
            try:
                os.link(boundary, alias)
            except OSError as error:
                self.skipTest(f"hard links unavailable: {error}")
            quoted_script = str(PS_PATH).replace("'", "''")
            quoted_boundary = str(boundary).replace("'", "''")
            digest = sha256_bytes(boundary.read_bytes())
            harness = rf"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$text = Get-Content -Raw '{quoted_script}'
$marker = 'Add-Type @"'
$nativeStart = $text.IndexOf($marker) + $marker.Length
$nativeEnd = $text.IndexOf('"@', $nativeStart)
if ($nativeStart -lt $marker.Length -or $nativeEnd -lt 0) {{ throw 'native helper source missing' }}
Add-Type -TypeDefinition $text.Substring($nativeStart, $nativeEnd - $nativeStart) -Language CSharp -ReferencedAssemblies @('System.Windows.Forms.dll','System.Drawing.dll') -ErrorAction Stop
function Fail([string]$Code) {{ throw [System.InvalidOperationException]::new($Code) }}
$stableStart = $text.IndexOf('function Get-StableCheckpointFile')
$stableEnd = $text.IndexOf('function Get-ExistingPngCheckpoint', $stableStart)
$assertStart = $text.IndexOf('function Assert-StartBoundary')
$assertEnd = $text.IndexOf('function Get-ExpertCatalogRefreshBoundaryPath', $assertStart)
Invoke-Expression $text.Substring($stableStart, $stableEnd - $stableStart)
Invoke-Expression $text.Substring($assertStart, $assertEnd - $assertStart)
$request = [pscustomobject]@{{
    startBoundaryPath = '{quoted_boundary}'
    startBoundarySha256 = '{digest}'
}}
try {{
    [void](Assert-StartBoundary $request)
    throw 'hardlinked boundary accepted'
}} catch {{
    if ([string]$_.Exception.Message -cne 'tester_start_boundary_mismatch') {{ throw }}
}}
'start-boundary-hardlink-rejected'
"""
            completed = subprocess.run(
                [
                    powershell,
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-EncodedCommand",
                    base64.b64encode(harness.encode("utf-16le")).decode("ascii"),
                ],
                text=True,
                capture_output=True,
                timeout=60,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                completed.stdout.strip(), "start-boundary-hardlink-rejected"
            )

    def test_powershell_start_post_is_exact_nonblocking_and_one_shot(self) -> None:
        require_interactive_ui_test(self)
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        quoted_script = str(PS_PATH).replace("'", "''")
        harness = rf"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$text = Get-Content -Raw '{quoted_script}'
$marker = 'Add-Type @"'
$nativeStart = $text.IndexOf($marker) + $marker.Length
$nativeEnd = $text.IndexOf('"@', $nativeStart)
if ($nativeStart -lt $marker.Length -or $nativeEnd -lt 0) {{ throw 'native helper source missing' }}
Add-Type -TypeDefinition $text.Substring($nativeStart, $nativeEnd - $nativeStart) -Language CSharp -ReferencedAssemblies @('System.Windows.Forms.dll','System.Drawing.dll') -ErrorAction Stop
Add-Type -ReferencedAssemblies @('System.Windows.Forms.dll','System.Drawing.dll') -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;
public sealed class StartDispatchHarnessForm : Form {{
  const int WM_COMMAND = 0x0111;
  const int WS_CHILD = 0x40000000;
  const int WS_VISIBLE = 0x10000000;
  const int BS_PUSHBUTTON = 0x00000000;
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  static extern IntPtr CreateWindowEx(int exStyle, string className, string text, int style,
    int x, int y, int width, int height, IntPtr parent, IntPtr menu, IntPtr instance, IntPtr parameter);
  [DllImport("user32.dll", SetLastError=true)]
  public static extern bool EnableWindow(IntPtr window, bool enabled);
  public IntPtr StartButton {{ get; private set; }}
  public int StartClickCount {{ get; private set; }}
  protected override void OnHandleCreated(EventArgs e) {{
    base.OnHandleCreated(e);
    StartButton = CreateWindowEx(0, "Button", "Start", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
      10, 10, 100, 28, Handle, (IntPtr)16790, IntPtr.Zero, IntPtr.Zero);
    if (StartButton == IntPtr.Zero) throw new InvalidOperationException("raw button creation failed");
  }}
  protected override void WndProc(ref Message message) {{
    if (message.Msg == WM_COMMAND && ((long)message.WParam & 0xffffL) == 16790L &&
        (((long)message.WParam >> 16) & 0xffffL) == 0L) {{
      StartClickCount++;
      Thread.Sleep(2100);
    }}
    base.WndProc(ref message);
  }}
}}
'@
function Assert-Rejected([scriptblock]$Call) {{
    $rejected = $false
    try {{ & $Call }} catch {{ $rejected = $true }}
    if (-not $rejected) {{ throw 'forged start identity accepted' }}
}}
function Focus-Exact([System.Windows.Forms.Form]$Target) {{
    [IntPtr]$foreground = [MetafxMt5VisibleNative]::GetForegroundWindow()
    [uint32]$foregroundPid = 0
    [uint32]$foregroundThread = if ($foreground -ne [IntPtr]::Zero) {{ [MetafxMt5VisibleNative]::GetWindowThreadProcessId($foreground, [ref]$foregroundPid) }} else {{ 0 }}
    [uint32]$currentThread = [MetafxMt5VisibleNative]::GetCurrentThreadId()
    $attached = $false
    try {{
        if ($foregroundThread -ne 0 -and $foregroundThread -ne $currentThread) {{
            $attached = [MetafxMt5VisibleNative]::AttachThreadInput($currentThread, $foregroundThread, $true)
        }}
        [void][MetafxMt5VisibleNative]::ShowWindowAsync($Target.Handle, 9)
        [void][MetafxMt5VisibleNative]::BringWindowToTop($Target.Handle)
        [void][MetafxMt5VisibleNative]::SetForegroundWindow($Target.Handle)
        [void][MetafxMt5VisibleNative]::SetActiveWindow($Target.Handle)
        [void][MetafxMt5VisibleNative]::SetFocus($Target.Handle)
        [System.Windows.Forms.Application]::DoEvents()
    }} finally {{
        if ($attached) {{ [void][MetafxMt5VisibleNative]::AttachThreadInput($currentThread, $foregroundThread, $false) }}
    }}
    if ([MetafxMt5VisibleNative]::GetForegroundWindow() -ne $Target.Handle) {{ throw 'synthetic foreground unavailable' }}
}}
$form = [StartDispatchHarnessForm]::new()
$form.Text = 'Start dispatch harness'
$other = [System.Windows.Forms.Form]::new()
$other.Text = 'Wrong root'
try {{
    $form.Show()
    $other.Show()
    [System.Windows.Forms.Application]::DoEvents()
    [IntPtr]$button = $form.StartButton
    [uint32]$pid = [System.Diagnostics.Process]::GetCurrentProcess().Id
    Focus-Exact $form
    Assert-Rejected {{ [MetafxMt5VisibleNative]::PostButtonClickIfTextExact($button, $pid, $form.Handle, 16791, 'Start') }}
    Assert-Rejected {{ [MetafxMt5VisibleNative]::PostButtonClickIfTextExact($button, $pid, $form.Handle, 16790, 'Start ') }}
    Assert-Rejected {{ [MetafxMt5VisibleNative]::PostButtonClickIfTextExact($button, $pid, $other.Handle, 16790, 'Start') }}
    Focus-Exact $other
    Assert-Rejected {{ [MetafxMt5VisibleNative]::PostButtonClickIfTextExact($button, $pid, $form.Handle, 16790, 'Start') }}
    Focus-Exact $form
    [void][StartDispatchHarnessForm]::EnableWindow($button, $false)
    Assert-Rejected {{ [MetafxMt5VisibleNative]::PostButtonClickIfTextExact($button, $pid, $form.Handle, 16790, 'Start') }}
    [void][StartDispatchHarnessForm]::EnableWindow($button, $true)
    Focus-Exact $form
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    [MetafxMt5VisibleNative]::PostButtonClickIfTextExact($button, $pid, $form.Handle, 16790, 'Start')
    $timer.Stop()
    if ($timer.ElapsedMilliseconds -ge 500) {{ throw 'start post blocked in button handler' }}
    if ($form.StartClickCount -ne 0) {{ throw 'start handler ran synchronously' }}
    [System.Windows.Forms.Application]::DoEvents()
    [System.Windows.Forms.Application]::DoEvents()
    if ($form.StartClickCount -ne 1) {{ throw "unexpected start count $($form.StartClickCount)" }}
    'start-post-one-shot-ok'
}} finally {{
    $other.Close()
    $other.Dispose()
    $form.Close()
    $form.Dispose()
}}
"""
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Sta",
                "-EncodedCommand",
                base64.b64encode(harness.encode("utf-16le")).decode("ascii"),
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "start-post-one-shot-ok")

    def test_powershell_catalog_refresh_is_idle_guarded_once_and_pointer_safe(self) -> None:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        text = PS_PATH.read_text(encoding="utf-8")
        refresh = text[
            text.index("function Invoke-Mt5ExpertCatalogRefresh"):
            text.index("function Select-ExpertWithCatalogRefresh")
        ]
        selector = text[
            text.index("function Select-ExpertWithCatalogRefresh"):
            text.index("function Configure-Tester")
        ]
        collect_start = text.index("function Read-And-VerifyConfiguredTester")
        collect = text[
            collect_start:
            text.index("function Invoke-Tester([object]", collect_start)
        ]
        self.assertIn('Get-ControlByIdPresent $root "32845"', refresh)
        self.assertIn('Get-ControlByIdPresent $navigator "10064"', refresh)
        self.assertIn(
            'Find-UiaRootTreeItemExact $tree "Expert Advisors"', refresh
        )
        self.assertIn("SelectRootOrSingleRootChildExact", refresh)
        self.assertIn("ReadSelectedRootOrSingleRootChildExact", refresh)
        self.assertIn("FocusTreeExact", refresh)
        self.assertGreaterEqual(refresh.count("AssertTreeFocusExact"), 1)
        self.assertNotIn("$tree.SetFocus()", refresh)
        self.assertLess(
            refresh.index("$selectedReadback"),
            refresh.index("FocusTreeExact"),
        )
        self.assertIn("AssertSelectedTreeContextExact", refresh)
        context_guard = refresh.rindex("AssertSelectedTreeContextExact")
        menu_send = refresh.index('[System.Windows.Forms.SendKeys]::SendWait("+{F10}")')
        self.assertLess(context_guard, menu_send)
        between_context_and_menu = refresh[context_guard:menu_send]
        self.assertNotIn("Read-TesterStartState", between_context_and_menu)
        self.assertNotIn("Start-Sleep", between_context_and_menu)
        self.assertNotIn("SetFocus", between_context_and_menu)
        after_menu_open = refresh[menu_send:]
        self.assertNotIn("$TerminalProcess.MainWindowHandle", after_menu_open)
        self.assertGreaterEqual(
            after_menu_open.count(
                "Get-BoundTesterControlSet $Request $boundRootHandle $false"
            ),
            2,
        )
        self.assertIn("Get-ExactNativePopupMenuHost", refresh)
        self.assertIn("CapturePopupMenuTokenExact", refresh)
        self.assertGreaterEqual(refresh.count("AssertPopupMenuCommandFromTokenExact"), 2)
        self.assertIn("AssertPopupMenuTokenExact", refresh)
        self.assertIn('"Refresh",', refresh)
        self.assertIn("[uint32]33416", refresh)
        self.assertIn("InvokePopupMenuCommandExact", refresh)
        self.assertNotIn("Invoke-Exact $matches[0]", refresh)
        self.assertLess(
            refresh.index("$beforeBoundary = Get-BoundTesterControlSet"),
            refresh.index("Write-ExpertCatalogRefreshBoundary $Request"),
        )
        self.assertLess(
            refresh.index("Write-ExpertCatalogRefreshBoundary $Request"),
            refresh.rindex("Read-TesterStartState"),
        )
        self.assertLess(
            refresh.rindex("Read-TesterStartState"),
            refresh.index("InvokePopupMenuCommandExact"),
        )
        self.assertEqual(selector.count("Invoke-Mt5ExpertCatalogRefresh"), 1)
        self.assertIn("Assert-ExpertCatalogRefreshBoundary $Request", selector)
        self.assertIn(
            "$recoveredAfterBoundary = [System.IO.File]::Exists($boundaryPath)",
            selector,
        )
        self.assertIn(
            "if ($beforeMatches.Count -eq 0 -and -not $refreshAttempted)",
            selector,
        )
        self.assertIn("Inject-NativeComboExpertExact", selector)
        self.assertIn("$injectionAttempted = $false", selector)
        self.assertIn(
            "if ($injectionAttempted) { Fail \"mt5_expert_catalog_injection_duplicate_attempt\" }",
            selector,
        )
        self.assertLess(
            selector.index("Assert-ExpertCatalogRefreshBoundary $Request"),
            selector.index("Invoke-Mt5ExpertCatalogRefresh $Request"),
        )
        self.assertIn("Normalize-TesterSettingsTabExact $Request", selector)
        self.assertGreaterEqual(selector.count("Get-BoundTesterControlSet $Request"), 2)
        self.assertIn("Select-NativeComboExact", selector)
        self.assertIn("Read-UiaComboSelectionExact", selector)
        self.assertIn("CB_SHOWDROPDOWN", text)
        close_dropdown = text[
            text.index("function Close-NativeComboDropDownExact") : text.index(
                "function Invoke-NativeComboAddStringExact"
            )
        ]
        self.assertIn("CB_SHOWDROPDOWN", close_dropdown)
        self.assertIn("VK_F4", close_dropdown)
        self.assertIn("CB_GETDROPPEDSTATE", close_dropdown)
        self.assertIn("Send-BalancedKey", close_dropdown)
        self.assertIn("CB_ADDSTRING", text)
        self.assertIn("CB_DELETESTRING", text)
        self.assertIn("Restore-NativeComboAfterInjectionFailure", text)
        self.assertIn("SMTO_ERRORONEXIT", text)
        self.assertIn("algoTradingStateBefore", selector)
        self.assertIn("idleStateImmediatelyBeforeRefresh", selector)
        self.assertIn("terminalWindowHandle", selector)
        self.assertIn("elapsedMs", selector)
        self.assertNotIn("Write-StartBoundary", selector)
        self.assertNotIn("Invoke-Mt5ExpertCatalogRefresh", collect)
        self.assertIn("Get-BoundVisualModeControl $Request", collect)
        self.assertIn(
            'Get-Toggle $visualBound.visual "mt5_visual_mode_readback_mismatch"',
            collect,
        )
        self.assertNotIn("Set-ToggleExact", collect)
        self.assertNotIn("ref SYSTEMTIME", text)
        self.assertNotIn("ref TVITEM", text)
        self.assertIn("VirtualAllocEx", text)
        self.assertIn("WriteProcessMemory", text)
        self.assertIn("ReadProcessMemory", text)
        self.assertIn("VirtualFreeEx", text)
        self.assertIn("AssertRemoteOwner(window, expectedProcessId, expectedRoot)", text)
        self.assertIn(
            "SendRemoteDateMessage(window, DTM_SETSYSTEMTIME, (IntPtr)GDT_VALID, remote)",
            text,
        )
        self.assertIn(
            "SendRemoteDateMessage(window, DTM_GETSYSTEMTIME, IntPtr.Zero, remote)",
            text,
        )

        self.assertNotRegex(
            text,
            r"SendMessageTimeout\([^;]+DTM_(?:GET|SET)SYSTEMTIME[^;]+(?:local|ref\s+SYSTEMTIME)",
        )
        native = text[
            text.index("public static class MetafxMt5VisibleNative") : text.index(
                "public sealed class MetafxMt5StartEventMonitor"
            )
        ]
        popup_helper = native[
            native.index("static IntPtr AssertPopupMenuOwner") : native.index(
                "public static void OpenInputsContextMenuExact"
            )
        ]
        popup_invoke = popup_helper[
            popup_helper.index(
                "static MENUITEMSNAPSHOT InvokePopupMenuCommandCurrentTokenExact"
            ) : popup_helper.index(
                "public static MENUITEMSNAPSHOT InvokePopupMenuCommandExact(POPUPMENUTOKEN"
            )
        ]
        submenu_invoke = popup_helper[
            popup_helper.index(
                "public static MENUITEMSNAPSHOT InvokePopupSubmenuCommandExact"
            ) : popup_helper.index(
                "public static MENUITEMSNAPSHOT AssertPopupMenuCommandFromTokenExact"
            )
        ]
        self.assertIn("MN_GETHMENU", popup_helper)
        self.assertIn("GetMenuItemInfo", popup_helper)
        self.assertIn("GetMenuItemRect", popup_helper)
        self.assertIn("MN_SELECTITEM", popup_helper)
        self.assertIn("WM_KEYDOWN", popup_helper)
        self.assertIn("VK_RETURN", popup_helper)
        self.assertNotIn("SendInput", popup_helper)
        self.assertNotIn("SetCursorPos", popup_helper)
        self.assertIn("hwndMenuOwner", popup_helper)
        self.assertIn("CapturePopupMenuTokenExact", popup_helper)
        self.assertIn("AssertPopupMenuTokenExact", popup_helper)
        self.assertIn("MIIM_DATA", popup_helper)
        self.assertIn("const uint capacity = 512", popup_helper)
        self.assertIn("second.cch != first.cch", popup_helper)
        self.assertIn("third.cch != second.cch", popup_helper)
        self.assertIn("SubmenuHandle", popup_helper)
        self.assertIn("ItemData", popup_helper)
        self.assertIn("GetPopupMenuHandleExact(menuWindow", popup_helper)
        self.assertNotIn("GetMenuString", popup_helper)
        self.assertIn(
            "PostMessage(menuWindow, WM_KEYDOWN, (IntPtr)VK_RETURN, (IntPtr)1)",
            popup_helper,
        )
        self.assertIn(
            "PostMessage(menuWindow, WM_KEYUP, (IntPtr)VK_RETURN,",
            popup_helper,
        )
        self.assertIn("unchecked((int)0xC0000001)", popup_invoke)
        self.assertIn(
            "&& IsWindow(menuWindow) && IsWindowVisible(menuWindow)",
            popup_invoke,
        )
        self.assertEqual(
            popup_invoke.count(
                "PostMessage(menuWindow, WM_KEYDOWN, (IntPtr)VK_RETURN"
            ),
            1,
        )
        self.assertEqual(
            popup_invoke.count("PostMessage(menuWindow, WM_KEYUP, (IntPtr)VK_RETURN"),
            1,
        )
        self.assertLess(
            popup_invoke.index("PostMessage(menuWindow, WM_KEYDOWN"),
            popup_invoke.index("PostMessage(menuWindow, WM_KEYUP"),
        )
        self.assertLess(
            popup_invoke.index("PostMessage(menuWindow, WM_KEYUP"),
            popup_invoke.index("DateTime deadline"),
        )
        self.assertEqual(
            submenu_invoke.count(
                "SendMessageTimeout(current.PopupWindow, WM_KEYDOWN, (IntPtr)VK_RIGHT"
            ),
            1,
        )
        self.assertEqual(
            submenu_invoke.count(
                "SendMessageTimeout(current.PopupWindow, WM_KEYUP, (IntPtr)VK_RIGHT"
            ),
            1,
        )
        self.assertLess(
            submenu_invoke.index("WM_KEYDOWN, (IntPtr)VK_RIGHT"),
            submenu_invoke.index("WM_KEYUP, (IntPtr)VK_RIGHT"),
        )
        self.assertIn("leafDispatchAttempted = true", submenu_invoke)
        self.assertIn("if (!leafDispatchAttempted &&", submenu_invoke)
        self.assertNotRegex(
            popup_helper,
            r"SendMessageTimeout\(menuWindow,\s*WM_KEYDOWN,\s*\(IntPtr\)VK_RETURN",
        )
        self.assertNotIn('SendWait("{ESC}")', refresh)
        self.assertNotRegex(
            popup_helper,
            r"SendMessageTimeout\([^;]+(?:GetMenuItemInfo|GetMenuItemRect)[^;]+",
        )
        self.assertIn(
            "SendRemoteTreeMessage(tree, TVM_GETITEMW, IntPtr.Zero, itemRemote)",
            native,
        )
        self.assertIn(
            "SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_NEXT, current)",
            native,
        )
        self.assertIn("WriteRemoteExact(process, itemRemote", native)
        self.assertIn("ReadRemoteExact(process, textRemote", native)
        self.assertIn("MAX_ROOT_TREE_ITEMS = 256", native)
        listing = native[
            native.index("public static string[] ListRootTreeItemTexts") : native.index(
                "public static string[] ListSingleRootDirectChildItemTexts"
            )
        ]
        self.assertIn("TVM_GETNEXTITEM", listing)
        self.assertIn("TVGN_ROOT", listing)
        self.assertIn("TVGN_NEXT", listing)
        self.assertIn("ReadTreeItemText", listing)
        self.assertIn("AssertRemoteTree", listing)
        self.assertIn("mt5_tree_traversal_cycle", listing)
        self.assertIn("mt5_tree_traversal_limit", listing)
        self.assertNotIn("TVM_SELECTITEM", listing)
        self.assertNotIn("TVGN_CARET", listing)
        self.assertNotIn("SetFocus", listing)
        self.assertNotIn("SendKeys", listing)
        child_listing = native[
            native.index("public static string[] ListSingleRootDirectChildItemTexts") : native.index(
                "public static string SelectRootOrSingleRootChildExact"
            )
        ]
        self.assertIn("TVGN_CHILD", child_listing)
        self.assertIn("TVGN_NEXT", child_listing)
        self.assertIn("ReadTreeItemText", child_listing)
        self.assertIn("AssertRemoteTree", child_listing)
        self.assertIn("mt5_tree_traversal_cycle", child_listing)
        self.assertIn("mt5_tree_traversal_limit", child_listing)
        self.assertNotIn("TVM_SELECTITEM", child_listing)
        self.assertNotIn("TVGN_CARET", child_listing)
        self.assertNotIn("SetFocus", child_listing)
        self.assertNotIn("SendKeys", child_listing)
        exact_selector = native[
            native.index("public static string SelectRootOrSingleRootChildExact") : native.index(
                "public static string ReadSelectedRootOrSingleRootChildExact"
            )
        ]
        self.assertIn("TVM_SELECTITEM", exact_selector)
        self.assertIn("TVGN_PARENT", exact_selector)
        focus_helper = native[
            native.index("public static void AssertTreeFocusExact") : native.index(
                "public static string SelectRootTreeItemExact"
            )
        ]
        self.assertIn("GetGUIThreadInfo", focus_helper)
        self.assertIn("AttachThreadInput(currentThread, targetThread, true)", focus_helper)
        self.assertIn("SetFocus(tree)", focus_helper)
        self.assertIn("info.hwndActive != expectedRoot", focus_helper)
        self.assertIn("info.hwndFocus != tree", focus_helper)
        self.assertIn("GetForegroundWindow() != expectedRoot", focus_helper)
        self.assertIn("targetThread != rootThread", focus_helper)
        self.assertIn("IntPtr.Size == 8 ? 72 : 48", focus_helper)
        self.assertIn("AssertSelectedTreeContextExact", focus_helper)
        self.assertIn("AttachThreadInput(currentThread, targetThread, false)", focus_helper)
        self.assertGreaterEqual(focus_helper.count("AssertRemoteTree"), 3)
        self.assertNotRegex(
            native,
            r"SendRemoteTreeMessage\([^;]+TVM_GETITEMW[^;]+(?:local|ref\s+TVITEM)",
        )
        get_value = text[
            text.index("function Get-Value") : text.index("function Set-ValueExact")
        ]
        set_value = text[
            text.index("function Set-ValueExact") : text.index(
                "function Get-SelectedComboText"
            )
        ]
        self.assertLess(
            get_value.index('if ($className -ceq "SysDateTimePick32")'),
            get_value.index("TryGetCurrentPattern"),
        )
        self.assertLess(
            set_value.index('if ($className -ceq "SysDateTimePick32")'),
            set_value.index("TryGetCurrentPattern"),
        )

        decision = text[
            text.index("function Get-ExpertCatalogDecision"):
            text.index("function Invoke-Mt5ExpertCatalogRefresh")
        ]
        harness = (
            'function Fail([string]$Code) { throw $Code }\n'
            + decision
            + "\n$cases = @(@('Start',0,$false),@('Start',1,$false),"
            + "@('Start',0,$true),@('Start',2,$false),@('Stop',0,$false))\n"
            + "$out = @($cases | ForEach-Object { try { Get-ExpertCatalogDecision $_[0] $_[1] $_[2] } catch { $_.Exception.Message } })\n"
            + "$out | ConvertTo-Json -Compress\n"
        )
        completed = subprocess.run(
            [powershell, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", harness],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(completed.stdout.strip(), completed.stderr)
        self.assertEqual(
            json.loads(completed.stdout.strip()),
            [
                "refresh",
                "select",
                "mt5_expert_catalog_refresh_timeout",
                "mt5_expert_catalog_ambiguous",
                "mt5_tester_not_idle",
            ],
        )

    def test_powershell_all_targeted_keys_are_balanced_with_exact_release_bits(self) -> None:
        text = PS_PATH.read_text(encoding="utf-8")
        native = text[
            text.index("public static class MetafxMt5VisibleNative") : text.index(
                "public sealed class MetafxMt5StartEventMonitor"
            )
        ]
        submenu = native[
            native.index("public static MENUITEMSNAPSHOT InvokePopupSubmenuCommandExact") : native.index(
                "public static MENUITEMSNAPSHOT AssertPopupMenuCommandFromTokenExact"
            )
        ]
        dismiss = native[
            native.index("public static void DismissPopupMenuExact") : native.index(
                "static IntPtr OpenTreeProcess"
            )
        ]
        balanced = text[
            text.index("function Send-BalancedKey") : text.index(
                "function Read-NativeText"
            )
        ]

        for block in (submenu, dismiss):
            self.assertEqual(block.count("WM_KEYDOWN, (IntPtr)VK_ESCAPE"), 1)
            self.assertEqual(block.count("WM_KEYUP, (IntPtr)VK_ESCAPE"), 1)
            self.assertLess(
                block.index("WM_KEYDOWN, (IntPtr)VK_ESCAPE"),
                block.index("WM_KEYUP, (IntPtr)VK_ESCAPE"),
            )
            self.assertIn("new IntPtr(unchecked((int)0xC0000001))", block)

        self.assertIn("[IntPtr]$keyDownLParam = [IntPtr]1", balanced)
        self.assertIn(
            "[IntPtr]$keyUpLParam = [IntPtr]([int]-1073741823)", balanced
        )
        self.assertEqual(balanced.count("WM_KEYDOWN"), 1)
        self.assertEqual(balanced.count("WM_KEYUP"), 1)
        down = (
            "PostMessage($Handle, [MetafxMt5VisibleNative]::WM_KEYDOWN, "
            "[IntPtr]$VirtualKey, $keyDownLParam)"
        )
        up = (
            "PostMessage($Handle, [MetafxMt5VisibleNative]::WM_KEYUP, "
            "[IntPtr]$VirtualKey, $keyUpLParam)"
        )
        self.assertIn(down, balanced)
        self.assertIn(up, balanced)
        self.assertLess(balanced.index(down), balanced.index(up))

    def test_powershell_inputs_context_requires_exact_focus_and_stage_codes(self) -> None:
        text = PS_PATH.read_text(encoding="utf-8")
        native_open = text[
            text.index("public static void OpenInputsContextMenuExact") : text.index(
                "static void AssertExactListBinding"
            )
        ]
        binding = text[
            text.index("function Get-ExactTesterInputsList") : text.index(
                "function Invoke-TesterInputsContextCommandExact"
            )
        ]
        command = text[
            text.index("function Invoke-TesterInputsContextCommandExact") : text.index(
                "function Restore-TesterSettingsTabExact"
            )
        ]

        native_focus = (
            "AssertListFocusExact(list, expectedProcessId, expectedRoot, 10494);"
        )
        native_context = (
            "PostMessage(list, WM_CONTEXTMENU, list, new IntPtr(-1))"
        )
        self.assertIn(native_focus, native_open)
        self.assertIn(native_context, native_open)
        self.assertLess(native_open.index(native_focus), native_open.index(native_context))
        self.assertEqual(native_open.count(native_context), 1)

        for exact_binding_proof in (
            "Root.Current.NativeWindowHandle",
            "Root.Current.ProcessId",
            "$rootHandle -ne [IntPtr]$script:TerminalRootHandle",
            "$rootProcessId -ne $TerminalProcess.Id",
            "(Get-NativeOwner $rootHandle) -ne $TerminalProcess.Id",
            "GetAncestor($rootHandle, [MetafxMt5VisibleNative]::GA_ROOT) -ne $rootHandle",
            "(Get-NativeOwner $handle) -ne $TerminalProcess.Id",
            "GetAncestor($handle, [MetafxMt5VisibleNative]::GA_ROOT) -ne $rootHandle",
        ):
            self.assertIn(exact_binding_proof, binding)

        for failure_code in (
            '"$($Code)_inputs_binding_failed"',
            '"$($Code)_inputs_foreground_failed"',
            '"$($Code)_inputs_focus_failed"',
            '"$($Code)_inputs_focus_readback_failed"',
            '"$($Code)_inputs_context_menu_failed"',
            '"$($Code)_inputs_popup_failed"',
            '"$($Code)_inputs_control_rebind_failed"',
        ):
            self.assertIn(failure_code, command)

        foreground = command.index("try { Set-Foreground $TerminalProcess $root }")
        focus = command.index("[MetafxMt5VisibleNative]::FocusListExact(")
        focus_readback = command.index(
            "[MetafxMt5VisibleNative]::AssertListFocusExact("
        )
        context = command.index("[MetafxMt5VisibleNative]::OpenInputsContextMenuExact(")
        popup = command.index("Get-ExactNativePopupMenuHost 3000 $popupCode")
        self.assertLess(foreground, focus)
        self.assertLess(focus, focus_readback)
        self.assertLess(focus_readback, context)
        self.assertLess(context, popup)
        self.assertEqual(command.count("[MetafxMt5VisibleNative]::FocusListExact("), 1)
        self.assertEqual(
            command.count("[MetafxMt5VisibleNative]::AssertListFocusExact("), 1
        )
        self.assertEqual(
            command.count("[MetafxMt5VisibleNative]::OpenInputsContextMenuExact("),
            1,
        )
        self.assertIn("catch { Fail $foregroundCode }", command)
        self.assertIn("catch { Fail $focusCode }", command)
        self.assertIn("catch { Fail $focusReadbackCode }", command)
        self.assertIn("catch { Fail $contextCode }", command)
        self.assertIn("Get-ExactNativePopupMenuHost 0 $popupCode", command)
        self.assertIn(
            "Get-TesterResultTabs $immediateRoot $Request.requiredAutomationIds $controlRebindCode",
            command,
        )
        self.assertIn(
            "Get-ExactTesterInputsList $immediateRoot $immediateTabs $controlRebindCode",
            command,
        )
        self.assertEqual(
            command.count("RebindPopupMenuTokenIgnoringHighlightExact"), 2
        )
        self.assertEqual(
            command.count("AssertPopupMenuCommandFromReboundTokenExact"), 2
        )
        self.assertEqual(
            command.count(
                "[void][MetafxMt5VisibleNative]::InvokePopupMenuCommandFromReboundTokenExact("
            ),
            1,
        )
        for forbidden_start_path in (
            "Invoke-TesterStartOnce",
            "PostButtonClickIfTextExact",
            "BM_CLICK",
            "Write-StartBoundary",
        ):
            self.assertNotIn(forbidden_start_path, command)

    def test_powershell_mt5_inputs_tab_flow_is_exact_rebound_and_start_free(self) -> None:
        text = PS_PATH.read_text(encoding="utf-8")
        native_inputs = text[
            text.index("public static void OpenInputsContextMenuExact") : text.index(
                "static IntPtr OpenTreeProcess"
            )
        ]
        command = text[
            text.index("function Invoke-TesterInputsContextCommandExact") : text.index(
                "function Restore-TesterSettingsTabExact"
            )
        ]
        load = text[
            text.index("function Load-And-VerifyInputSet") : text.index(
                "function Get-BoundTerminalRoot"
            )
        ]
        set_reference = text[
            text.index("function Test-Mt5NativeDisabledBoolRangeEquivalent") : text.index(
                "function Assert-TesterTabSelectedExact"
            )
        ]
        dialog_control = text[
            text.index("function Get-ExactOwnedDialogControl") : text.index(
                "function Enter-ExactFileDialogPath"
            )
        ]
        dialog_path = text[
            text.index("function Enter-ExactFileDialogPath") : text.index(
                "function Close-ExactOwnedFileDialogAfterFailure"
            )
        ]
        configure = text[
            text.index("function Configure-Tester") : text.index(
                "function Read-TesterStartState"
            )
        ]
        configured_readback_start = text.index(
            "function Read-And-VerifyConfiguredTester"
        )
        configured_readback = text[
            configured_readback_start : text.index(
                "function Invoke-Tester([object]", configured_readback_start
            )
        ]
        criterion_binding = text[
            text.index("function Get-BoundOptimizationCriterion") : text.index(
                "function Get-MinimalBoundTesterControlSet"
            )
        ]
        required = text[
            text.index("function Assert-RequiredControls") : text.index(
                "function Write-StartBoundary"
            )
        ]
        invoke_tester = text[
            text.index("function Invoke-Tester") : text.index('$request = $null')
        ]
        get_value = text[
            text.index("function Get-Value") : text.index("function Set-ValueExact")
        ]
        set_value = text[
            text.index("function Set-ValueExact") : text.index(
                "function Get-SelectedComboText"
            )
        ]
        probe_dispatch = text[text.index('$request = $null') :]
        post_probe_dispatch = text[
            text.index('        "post_probe" {') : text.index(
                '        "compile" {', text.index('        "post_probe" {')
            )
        ]

        self.assertIn("PostMessage(list, WM_CONTEXTMENU, list, new IntPtr(-1))", native_inputs)
        self.assertIn('[string]$request.action -ceq "probe"', probe_dispatch)
        self.assertIn("Add-Member -NotePropertyName expectedTerminalProcessId", probe_dispatch)
        self.assertIn("Add-Member -NotePropertyName expectedTerminalWindowHandle", probe_dispatch)
        self.assertIn('Fail "mt5_terminal_binding_missing"', probe_dispatch)
        self.assertIn(
            "Get-MinimalBoundTesterControlSet $request ([IntPtr]$script:TerminalRootHandle) $false",
            post_probe_dispatch,
        )
        self.assertEqual(post_probe_dispatch.count("Read-TesterStartState"), 2)
        self.assertEqual(post_probe_dispatch.count("Get-AlgoTradingState"), 2)
        self.assertIn(
            'New-Binding $TerminalProcess "strategy_tester" $autoTradingState $minimal.root',
            post_probe_dispatch,
        )
        self.assertIn(
            "New-BoundProbe $TerminalProcess $minimal.root",
            post_probe_dispatch,
        )
        self.assertIn('$testerStartState -cne "Start"', post_probe_dispatch)
        self.assertIn('$testerStartStateAfter -cne "Start"', post_probe_dispatch)
        for mutating_command in (
            "Assert-RequiredControls",
            "Normalize-TesterSettingsTabExact",
            "Select-TesterTabExact",
            "Select-ComboMapped",
            "Close-NativeComboDropDownExact",
            "Invoke-TesterStartOnce",
            "Write-StartBoundary",
            "Set-Foreground",
            "Invoke-Exact",
        ):
            self.assertNotIn(mutating_command, post_probe_dispatch)
        self.assertNotIn("SendMessageTimeout(list, WM_CONTEXTMENU", native_inputs)
        self.assertIn('($ExpectedName -cne "Load" -or $ExpectedCommandId -ne 33160)', command)
        self.assertIn('($ExpectedName -cne "Save" -or $ExpectedCommandId -ne 33159)', command)
        self.assertIn(
            '[string[]]$expectedDialogNames = if ($ExpectedName -ceq "Load")',
            command,
        )
        self.assertIn("Get-ExactTesterInputsList", command)
        self.assertIn("Read-TesterStartState", command)
        self.assertEqual(command.count("FindOwnedDialogExact"), 2)
        self.assertLess(
            command.index("FindOwnedDialogExact"),
            command.index("OpenInputsContextMenuExact"),
        )
        self.assertLess(
            command.rindex("FindOwnedDialogExact"),
            command.rindex("RebindPopupMenuTokenIgnoringHighlightExact"),
        )
        self.assertIn('"$($Code)_dispatch_preexisting_dialog"', command)
        self.assertIn("Get-ExactNativePopupMenuHost 0 $popupCode", command)
        self.assertNotIn("AssertPopupMenuCommandFromTokenExact", command)
        self.assertEqual(
            command.count("RebindPopupMenuTokenIgnoringHighlightExact"), 2
        )
        self.assertEqual(
            command.count(
                "$popupToken = [MetafxMt5VisibleNative]::RebindPopupMenuTokenIgnoringHighlightExact("
            ),
            2,
        )
        self.assertEqual(
            command.count("AssertPopupMenuCommandFromReboundTokenExact"), 2
        )
        self.assertIn("InvokePopupMenuCommandFromReboundTokenExact", command)
        self.assertEqual(
            command.count(
                "[void][MetafxMt5VisibleNative]::InvokePopupMenuCommandFromReboundTokenExact("
            ),
            1,
        )
        self.assertNotIn(
            "[void][MetafxMt5VisibleNative]::InvokePopupMenuCommandExact(", command
        )
        self.assertLess(
            command.index("$dispatchAttempted = $true"),
            command.index("InvokePopupMenuCommandFromReboundTokenExact"),
        )
        first_rebind = command.index("RebindPopupMenuTokenIgnoringHighlightExact")
        second_rebind = command.rindex("RebindPopupMenuTokenIgnoringHighlightExact")
        first_proof = command.index("AssertPopupMenuCommandFromReboundTokenExact")
        second_proof = command.rindex("AssertPopupMenuCommandFromReboundTokenExact")
        self.assertLess(first_rebind, first_proof)
        self.assertLess(first_proof, second_rebind)
        self.assertLess(second_rebind, second_proof)
        self.assertLess(
            second_proof, command.index("$dispatchAttempted = $true")
        )
        self.assertIn(
            'Resolve-PopupDispatchFailureCode $_ $Code "popup_bind"', command
        )
        self.assertEqual(
            command.count('Resolve-PopupDispatchFailureCode $_ $Code "preflight"'),
            2,
        )
        self.assertIn('Resolve-PopupDispatchFailureCode $_ $Code "dispatch"', command)
        self.assertNotIn('catch { Fail "$($Code)_dispatch_ambiguous" }', command)
        self.assertNotIn("while (", command)
        self.assertNotIn("for (", command)
        self.assertIn(
            'Wait-ExactOwnedFileDialog $expectedDialogNames "$($Code)_dispatch_unconfirmed"',
            command,
        )
        self.assertIn("return $confirmedDialog", command)
        self.assertEqual(command.count("$popupToken = $null"), 2)
        self.assertLess(
            command.rindex("$popupToken = $null"),
            command.index("Wait-ExactOwnedFileDialog"),
        )
        self.assertIn("$primaryMenuError = $_", command)
        self.assertIn("$dispatchAttempted = $true", command)
        self.assertIn(
            "if ($null -ne $popupToken -and -not $dispatchAttempted)", command
        )
        self.assertIn(
            'if ($null -eq $primaryMenuError) { Fail "$($Code)_cleanup_failed" }',
            command,
        )
        self.assertNotIn("Write-StartBoundary", command)
        self.assertNotIn("Invoke-TesterStartOnce", command)

        self.assertIn('Select-TesterTabExact $Request $settings.root $Request.requiredAutomationIds "Inputs"', load)
        self.assertIn(
            '$activeDialog = Invoke-TesterInputsContextCommandExact $Request "Load" 33160',
            load,
        )
        self.assertIn(
            '$activeDialog = Invoke-TesterInputsContextCommandExact $Request "Save" 33159',
            load,
        )
        self.assertEqual(
            load.count('Invoke-TesterInputsContextCommandExact $Request "Load" 33160'),
            1,
        )
        self.assertEqual(
            load.count('Invoke-TesterInputsContextCommandExact $Request "Save" 33159'),
            1,
        )
        self.assertNotIn('Wait-ExactOwnedFileDialog @("Open")', load)
        self.assertNotIn('Wait-ExactOwnedFileDialog @("Save As", "Save")', load)
        self.assertIn("Close-ExactOwnedFileDialogAfterFailure", load)
        self.assertIn("Restore-TesterSettingsTabExact", load)
        self.assertIn("Get-BoundTerminalRoot", load)
        self.assertIn("Assert-Mt5SetReference", load)
        self.assertIn(
            'Assert-Mt5SetReference $Reference $readback "$($Code)_readback_mismatch" $false $true',
            load,
        )
        self.assertIn(
            'Assert-Mt5SetReference $Reference $readback "$($Code)_preexisting_readback_mismatch" $false $true',
            load,
        )
        self.assertIn(
            "Assert-Mt5SetReference $Reference $setPath $Code",
            load,
        )
        self.assertIn("$existingReadbackSha", load)
        self.assertIn("preexisting_readback_mismatch", load)
        self.assertNotIn("Get-ExactNamedControl $Root", load)
        self.assertNotIn("Invoke-TesterStartOnce", load)
        self.assertNotIn("Write-StartBoundary", load)

        self.assertIn("AllowNativeDisabledBoolRangeNormalization", set_reference)
        self.assertIn("Test-Mt5NativeDisabledBoolRangeEquivalent", set_reference)
        self.assertIn("$Actual.current", set_reference)
        self.assertIn("$Expected.current", set_reference)
        self.assertIn('"false" "bool"', set_reference)
        self.assertIn('"0" "bool"', set_reference)
        self.assertIn('"true" "bool"', set_reference)
        self.assertEqual(configured_readback.count("$false $true"), 3)

        self.assertIn("FindDialogControlExact", dialog_control)
        self.assertIn("GetWindowTextExact", dialog_control)
        self.assertIn("[uint32]$TerminalProcess.Id", dialog_control)
        self.assertNotIn("Get-All $Dialog", dialog_control)
        self.assertIn("if ($isOpen) { 1148 } else { 1001 }", dialog_path)
        self.assertIn('Get-ExactOwnedDialogControl $Dialog $fileNameControlId "Edit"', dialog_path)
        self.assertIn('Get-ExactOwnedDialogControl $Dialog 1 "Button"', dialog_path)

        self.assertIn("Normalize-TesterSettingsTabExact $Request", required)
        self.assertIn("Select-SymbolComboExact $controls.symbol", configure)
        self.assertIn("Assert-SymbolComboCommittedExact $controls.symbol", configure)
        symbol_selector = text[
            text.index("function Select-SymbolComboExact") : text.index(
                "function Set-NativeComboText"
            )
        ]
        self.assertIn("CB_GETCOUNT", symbol_selector)
        self.assertIn("Assert-SymbolComboCommittedExact", symbol_selector)
        self.assertIn("CB_SETCURSEL", symbol_selector)
        self.assertIn("CBN_SELCHANGE", symbol_selector)
        self.assertLess(
            symbol_selector.index("Read-NativeCombo $Control"),
            symbol_selector.index("PostMessage"),
        )
        after_symbol_notification = symbol_selector[
            symbol_selector.index("PostMessage") :
        ]
        self.assertNotIn("Read-NativeCombo $Control", after_symbol_notification)
        self.assertNotIn("$Control.Current", after_symbol_notification)
        self.assertIn("Restore-TesterSettingsTabExact $Request", configure)
        self.assertIn(
            "$criterionId = [string]$Request.optimizationCriterionAutomationId",
            criterion_binding,
        )
        self.assertNotIn("$Request.requiredAutomationIds.criterion", criterion_binding)
        self.assertNotIn(
            "Find-ControlByIdPresent $root $criterionId", criterion_binding
        )
        self.assertIn(
            '[IntPtr]$optimizationHandle = Assert-NativeControl $bound.controls.optimization "ComboBox" $Code',
            criterion_binding,
        )
        self.assertIn(
            "$settingsParentHandle = [MetafxMt5VisibleNative]::GetParent($optimizationHandle)",
            criterion_binding,
        )
        self.assertIn("FindChildControlExact(", criterion_binding)
        self.assertIn("$settingsParentHandle,", criterion_binding)
        self.assertIn("[uint32]$TerminalProcess.Id,", criterion_binding)
        self.assertIn("[IntPtr]$script:TerminalRootHandle,", criterion_binding)
        self.assertIn("10507,", criterion_binding)
        self.assertIn('"ComboBox"', criterion_binding)
        self.assertIn(
            "$AllowOffscreenReadback -or -not $criterion.Current.IsOffscreen",
            criterion_binding,
        )
        self.assertIn(
            "GetDlgCtrlID($criterionHandle) -ne 10507", criterion_binding
        )
        self.assertIn(
            "GetParent($criterionHandle) -ne $settingsParentHandle",
            criterion_binding,
        )
        native_child_binding = text[
            text.index("public static IntPtr FindChildControlExact") : text.index(
                "static void AssertRemoteOwner"
            )
        ]
        self.assertIn("GetParent(window) == parent", native_child_binding)
        self.assertIn("GetAncestor(window, GA_ROOT) == expectedRoot", native_child_binding)
        self.assertIn("GetDlgCtrlID(window) == expectedId", native_child_binding)
        self.assertIn("matches.Count != 1", native_child_binding)
        self.assertIn("IsWindowVisible(window)", native_child_binding)
        self.assertIn("IsWindowEnabled(window)", native_child_binding)
        self.assertIn(
            'Get-BoundOptimizationCriterion $Request "mt5_criterion_control_not_verified" $true',
            configured_readback,
        )
        self.assertNotIn("Select-ComboMapped", configured_readback)
        self.assertIn(
            '$visualId = [string]$Request.requiredAutomationIds.visualMode',
            criterion_binding,
        )
        self.assertIn('if ($visualId -cne "10490")', criterion_binding)
        self.assertIn('Assert-NativeControl $visual "Button"', criterion_binding)
        self.assertIn('GetDlgCtrlID($visualHandle) -ne 10490', criterion_binding)
        self.assertIn('($visualStyle -band 15) -ne 3', criterion_binding)
        self.assertIn(
            'GetParent($visualHandle) -ne [MetafxMt5VisibleNative]::GetParent($optimizationHandle)',
            criterion_binding,
        )
        self.assertNotIn('@("Visualization", "Visual mode")', configure)
        self.assertIn("Get-BoundVisualModeControl $Request", configure)
        self.assertGreaterEqual(
            configure.count("Get-BoundVisualModeControl $Request"),
            1,
        )
        self.assertIn(
            'Set-ToggleExact $visualBound.visual $true "mt5_visual_mode_readback_mismatch"',
            configure,
        )
        self.assertLess(
            configure.index("$inputEvidence = Load-And-VerifyInputSet"),
            configure.index("$finalBound = Restore-TesterSettingsTabExact"),
        )
        self.assertLess(
            configure.index("$finalBound = Restore-TesterSettingsTabExact"),
            configure.index(
                'Set-ToggleExact $visualBound.visual $true "mt5_visual_mode_readback_mismatch"'
            ),
        )
        self.assertLess(
            configure.index("$inputEvidence = Load-And-VerifyInputSet"),
            configure.index("$finalBound = Restore-TesterSettingsTabExact"),
        )
        self.assertLess(
            configure.index("$finalBound = Restore-TesterSettingsTabExact"),
            configure.index("$visualBound = Get-BoundVisualModeControl"),
        )
        self.assertIn("Get-BoundVisualModeControl $Request", configured_readback)
        self.assertIn("Get-Toggle $visualBound.visual", configured_readback)
        self.assertNotIn("Set-ToggleExact", configured_readback)
        self.assertNotIn('@("Visualization", "Visual mode")', configured_readback)
        self.assertLess(
            configure.index(
                '$optimizationSelection = Select-BoundTesterComboMapped $Request "optimization"'
            ),
            configure.index(
                '$criterionSelection = Select-BoundTesterComboMapped $Request "criterion"'
            ),
        )
        self.assertIn(
            "if ($Optimize) { $verifiedIds[\"criterion\"] = $criterionId }",
            invoke_tester,
        )
        self.assertIn(
            '} elseif (-not $hasCriterionId -or $null -ne $Request.optimizationCriterionAutomationId) {',
            invoke_tester,
        )
        self.assertIn(
            '$visualModeId = if ($hasVisualModeId) { [string]$Request.requiredAutomationIds.visualMode } else { $null }',
            invoke_tester,
        )
        self.assertIn(
            '$hasVisualModeId = $null -ne $Request.requiredAutomationIds.PSObject.Properties["visualMode"]',
            invoke_tester,
        )
        self.assertNotIn(
            '$visualModeId = [string]$Request.requiredAutomationIds.visualMode',
            invoke_tester,
        )
        self.assertLess(
            get_value.index('if ($className -ceq "ComboBox")'),
            get_value.index("TryGetCurrentPattern"),
        )
        self.assertLess(
            set_value.index('if ($className -ceq "ComboBox")'),
            set_value.index("TryGetCurrentPattern"),
        )
        self.assertNotIn("Set-NativeComboText", set_value)
        self.assertNotIn("function Wait-Dialog", text)
        self.assertNotIn("function Enter-DialogPath", text)

    def test_powershell_optimization_contract_allows_intentionally_absent_visual_mode(self) -> None:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        text = PS_PATH.read_text(encoding="utf-8")
        invoke_tester = text[
            text.index("function Invoke-Tester([object]") : text.index("$request = $null")
        ]
        harness = r'''
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
function Fail([string]$Code) { throw $Code }
function Get-FullExistingFile { throw "reached_post_contract_validation" }
''' + invoke_tester + r'''
$request = [pscustomobject]@{
    neverStart = $false
    serviceAction = "start_round"
    optimizationCriterionAutomationId = "10507"
    requiredAutomationIds = [pscustomobject]@{}
    deployedExpertPath = "missing.ex5"
    expectedDeployedExpertSha256 = ("a" * 64)
}
$results = @()
try {
    [void](Invoke-Tester $request $true "none")
    $results += "unexpected-success"
} catch {
    $results += [string]$_.Exception.Message
}
$request.PSObject.Properties.Remove("optimizationCriterionAutomationId")
try {
    [void](Invoke-Tester $request $true "none")
    $results += "unexpected-success"
} catch {
    $results += [string]$_.Exception.Message
}
$results | ConvertTo-Json -Compress
'''
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "& ([scriptblock]::Create([Console]::In.ReadToEnd()))",
            ],
            input=harness,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            json.loads(completed.stdout.strip()),
            ["reached_post_contract_validation", "visible_ui_request_contract_invalid"],
        )
        self.assertIn(
            '$checkpoint -ceq "tester_request_validation"',
            text,
        )
        self.assertIn(
            '"visible_ui_tester_request_validation_failed"',
            text,
        )

    def test_powershell_symbol_combo_accepts_only_exact_current_text_when_catalog_is_empty(self) -> None:
        require_interactive_ui_test(self)
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        quoted_path = str(PS_PATH).replace("'", "''")
        harness = rf'''
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class SymbolComboHarnessNative {{
  [DllImport("user32.dll", EntryPoint="SetWindowLongPtrW", SetLastError=true)]
  public static extern IntPtr SetWindowLongPtr(IntPtr hWnd, int nIndex, IntPtr value);
}}
'@
$text = Get-Content -Raw '{quoted_path}'
$marker = 'Add-Type @"'
$nativeStart = $text.IndexOf($marker) + $marker.Length
$nativeEnd = $text.IndexOf('"@', $nativeStart)
if ($nativeStart -lt $marker.Length -or $nativeEnd -lt 0) {{ throw 'native helper source missing' }}
Add-Type -TypeDefinition $text.Substring($nativeStart, $nativeEnd - $nativeStart) -Language CSharp -ErrorAction Stop
$helperStart = $text.IndexOf('function Get-NativeClass')
$helperEnd = $text.IndexOf('function Set-NativeComboText', $helperStart)
if ($helperStart -lt 0 -or $helperEnd -le $helperStart) {{ throw 'symbol combo helper source missing' }}
function Fail([string]$Code) {{ throw $Code }}
Invoke-Expression $text.Substring($helperStart, $helperEnd - $helperStart)
function Assert-NativeControl($Control, [string]$ExpectedClass, [string]$Code) {{
    return [IntPtr][long]$Control.Current.NativeWindowHandle
}}
$form = New-Object System.Windows.Forms.Form
$combo = New-Object System.Windows.Forms.ComboBox
$combo.DropDownStyle = [System.Windows.Forms.ComboBoxStyle]::DropDown
$combo.AccessibleName = 'EURUSD'
$combo.Text = 'EURUSD'
$form.Controls.Add($combo)
$form.Show()
[System.Windows.Forms.Application]::DoEvents()
try {{
    [void][SymbolComboHarnessNative]::SetWindowLongPtr($combo.Handle, -12, [IntPtr]10486)
    $TerminalProcess = Get-Process -Id $PID
    $script:TerminalRootHandle = $form.Handle
    $control = [System.Windows.Automation.AutomationElement]::FromHandle($combo.Handle)
    $selected = Select-SymbolComboExact $control @('EURUSD') 'mt5_symbol_readback_mismatch'
    $verified = Assert-SymbolComboCommittedExact $control @('EURUSD') 'mt5_symbol_readback_mismatch'
    $count = (Invoke-NativeMessage $combo.Handle ([MetafxMt5VisibleNative]::CB_GETCOUNT) 0 0 'probe_failed').ToInt32()
    $combo.Text = 'XAUUSD'
    [System.Windows.Forms.Application]::DoEvents()
    $wrong = try {{
        [void](Select-SymbolComboExact $control @('EURUSD') 'mt5_symbol_readback_mismatch')
        'unexpected-success'
    }} catch {{
        [string]$_.Exception.Message
    }}
    [pscustomobject]@{{
        selected = [string]$selected
        verified = [string]$verified
        count = [int]$count
        wrong = [string]$wrong
    }} | ConvertTo-Json -Compress
}} finally {{
    $form.Close()
    $form.Dispose()
}}
'''
        completed = subprocess.run(
            [powershell, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", harness],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            json.loads(completed.stdout.strip()),
            {
                "selected": "EURUSD",
                "verified": "EURUSD",
                "count": 0,
                "wrong": "mt5_symbol_readback_mismatch",
            },
        )

    def test_powershell_native_disabled_bool_readback_rule_is_fail_closed(self) -> None:
        powershell = shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is required")
        text = PS_PATH.read_text(encoding="utf-8")
        value_equivalence = text[
            text.index("function Test-Mt5SetValueEquivalent") : text.index(
                "function Get-Mt5SetRows"
            )
        ]
        set_assertion = text[
            text.index("function Test-Mt5NativeDisabledBoolRangeEquivalent") : text.index(
                "function Assert-TesterTabSelectedExact"
            )
        ]
        harness = (
            '$ErrorActionPreference = "Stop"\n'
            'function Fail([string]$Code) { throw $Code }\n'
            'function Get-FullExistingFile([string]$Path, [string]$Extension, [string]$Code) { return $Path }\n'
            'function Get-Sha256([string]$Path) { return ("a" * 64) }\n'
            '$script:Rows = @()\n'
            'function Get-Mt5SetRows([string]$Path, [string]$Code) { return @($script:Rows) }\n'
            + value_equivalence
            + set_assertion
            + '\n$expected = [pscustomobject]@{ ordinal=0; inputName="UseGuard"; valueKind="bool"; current="true"; start="true"; step="1"; stop="true"; enabled=$false }\n'
            + '$reference = [pscustomobject]@{ schemaVersion="ea-factory-mt5-set-ref-v1"; sha256=("b" * 64); entryCount=1; expectedReadbackEntries=@($expected) }\n'
            + 'function Invoke-Case([object]$Actual, [bool]$Allow) { $script:Rows=@($Actual); try { [void](Assert-Mt5SetReference $reference "readback.set" "rejected" $false $Allow); return "accepted" } catch { return $_.Exception.Message } }\n'
            + '$canonical = [pscustomobject]@{ inputName="UseGuard"; current="true"; start="false"; step="0"; stop="true"; enabled=$false }\n'
            + '$currentDrift = [pscustomobject]@{ inputName="UseGuard"; current="false"; start="false"; step="0"; stop="true"; enabled=$false }\n'
            + '$enabledDrift = [pscustomobject]@{ inputName="UseGuard"; current="true"; start="false"; step="0"; stop="true"; enabled=$true }\n'
            + '$rangeDrift = [pscustomobject]@{ inputName="UseGuard"; current="true"; start="true"; step="0"; stop="true"; enabled=$false }\n'
            + '$out = @((Invoke-Case $canonical $true),(Invoke-Case $canonical $false),(Invoke-Case $currentDrift $true),(Invoke-Case $enabledDrift $true),(Invoke-Case $rangeDrift $true))\n'
            + '$out | ConvertTo-Json -Compress\n'
        )
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                harness,
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            json.loads(completed.stdout.strip()),
            ["accepted", "rejected", "rejected", "rejected", "rejected"],
        )

    def test_powershell_tester_pane_shell_is_not_treated_as_ready_content(self) -> None:
        text = PS_PATH.read_text(encoding="utf-8")
        pane_content = text[
            text.index("function Test-TesterPaneContentVisible") : text.index(
                "function Ensure-TesterPaneVisible"
            )
        ]
        pane_reveal = text[
            text.index("function Ensure-TesterPaneVisible") : text.index(
                "function Ensure-TesterSingleModeReady"
            )
        ]
        normalize = text[
            text.index("function Normalize-TesterSettingsTabExact") : text.index(
                "function Get-ExpertCatalogDecision"
            )
        ]
        stable = text[
            text.index("function Get-BoundStableTesterControlSet") : text.index(
                "function Select-BoundTesterComboMapped"
            )
        ]
        rebound_combo = text[
            text.index("function Select-BoundTesterComboMapped") : text.index(
                "function Normalize-TesterSettingsTabExact"
            )
        ]
        required = text[
            text.index("function Assert-RequiredControls") : text.index(
                "function Write-StartBoundary"
            )
        ]

        self.assertIn(
            "Find-ControlByIdPresent $Root ([string]$Required.testerPane)",
            pane_content,
        )
        self.assertIn(
            "Find-ControlByIdPresent $pane ([string]$Required.start)",
            pane_content,
        )
        self.assertIn('Find-ControlByIdPresent $pane "10887"', pane_content)
        self.assertIn('Find-ControlByIdPresent $launcher "3734"', pane_content)
        self.assertIn('Find-ControlByIdPresent $launcher "10888"', pane_content)
        self.assertEqual(
            pane_reveal.count("Test-TesterPaneContentVisible $Required $activeRoot"),
            3,
        )
        self.assertNotIn(
            "Find-ControlByIdPresent $activeRoot $paneId",
            pane_reveal,
        )
        reveal_command = (
            "[MetafxMt5VisibleNative]::InvokeTesterRevealMenuExact("
            "[uint32]$TerminalProcess.Id, $signedRoot)"
        )
        self.assertIn(reveal_command, pane_reveal)
        self.assertNotIn("[System.Windows.Forms.SendKeys]::SendWait", pane_reveal)
        self.assertLess(
            pane_reveal.index("Test-TesterPaneContentVisible $Required $activeRoot"),
            pane_reveal.index(reveal_command),
        )
        self.assertLess(
            pane_reveal.index(reveal_command),
            pane_reveal.rindex("Test-TesterPaneContentVisible $Required $activeRoot"),
        )
        self.assertIn("Get-BoundTerminalRoot $Request $signedRoot", pane_reveal)
        self.assertIn("Set-Foreground $TerminalProcess $activeRoot", pane_reveal)
        self.assertIn(
            "[MetafxMt5VisibleNative]::GetForegroundWindow() -ne $signedRoot",
            pane_reveal,
        )
        self.assertNotIn("$TerminalProcess.MainWindowHandle", pane_reveal)
        self.assertIn(
            'if ([string]$property.Name -cin @("visualMode", "criterion")) { continue }',
            stable,
        )
        self.assertIn(
            "Get-BoundStableTesterControlSet $Request $ExpectedRootHandle $false",
            normalize,
        )
        self.assertIn(
            "Get-BoundTesterControlSet $Request $ExpectedRootHandle $false",
            normalize,
        )
        self.assertIn(
            '$hasVisualMode = $Request.requiredAutomationIds.PSObject.Properties.Name -ccontains "visualMode"',
            normalize,
        )
        self.assertIn('Get-OptimizationUiNames "disabled"', normalize)
        self.assertIn(
            "Get-SelectedComboText $bound.controls.optimization $Code",
            normalize,
        )
        self.assertIn(
            'Select-BoundTesterComboMapped $Request "optimization" $disabledNames $Code',
            normalize,
        )
        self.assertIn(
            "Assert-ComboCommittedExact $bound.controls.optimization $disabledNames $Code",
            normalize,
        )
        self.assertIn(
            "Find-ControlByIdPresent $reboundRoot $visualId",
            normalize,
        )
        self.assertLess(
            normalize.index("Get-BoundStableTesterControlSet"),
            normalize.index("Get-SelectedComboText $bound.controls.optimization"),
        )
        self.assertLess(
            normalize.index("Get-SelectedComboText $bound.controls.optimization"),
            normalize.index('Select-BoundTesterComboMapped $Request "optimization"'),
        )
        self.assertLess(
            normalize.index('Select-BoundTesterComboMapped $Request "optimization"'),
            normalize.index("Get-BoundTesterControlSet"),
        )
        self.assertIn(
            "Get-BoundStableTesterControlSet $Request ([IntPtr]$script:TerminalRootHandle) $false",
            rebound_combo,
        )
        self.assertIn("[System.Windows.Forms.Application]::DoEvents()", rebound_combo)
        self.assertIn("Assert-ComboCommittedExact", rebound_combo)
        self.assertLess(
            rebound_combo.index("Select-ComboMapped"),
            rebound_combo.rindex("Get-BoundStableTesterControlSet"),
        )
        self.assertIn(
            "Normalize-TesterSettingsTabExact $Request ([IntPtr]$script:TerminalRootHandle) $true",
            required,
        )

    def test_powershell_async_combo_selection_rebinds_every_settings_control(self) -> None:
        text = PS_PATH.read_text(encoding="utf-8")
        native_select = text[
            text.index("function Select-NativeComboExact") : text.index(
                "function Assert-SymbolComboCommittedExact"
            )
        ]
        rebound = text[
            text.index("function Select-BoundTesterComboMapped") : text.index(
                "function Normalize-TesterSettingsTabExact"
            )
        ]
        configure = text[
            text.index("function Configure-Tester") : text.index(
                "function Read-TesterStartState"
            )
        ]
        expert = text[
            text.index("function Select-ExpertWithCatalogRefresh") : text.index(
                "function Configure-Tester"
            )
        ]
        generic_setter = text[
            text.index("function Set-ValueExact") : text.index(
                "function Get-SelectedComboText"
            )
        ]

        notification = native_select.index(
            "[MetafxMt5VisibleNative]::PostMessage($parent"
        )
        after_notification = native_select[notification:]
        self.assertNotIn("Read-NativeCombo $Control", after_notification)
        self.assertNotIn("Close-NativeComboDropDownExact $Control", after_notification)
        self.assertNotIn("Start-Sleep", after_notification)
        self.assertIn("return $submitted", after_notification)
        self.assertIn('if ($className -ceq "ComboBox")', generic_setter)
        self.assertNotIn("Select-NativeComboExact", generic_setter)
        self.assertIn("Get-BoundStableTesterControlSet", rebound)
        self.assertIn("Assert-ComboCommittedExact", rebound)
        self.assertLess(
            rebound.index("Select-ComboMapped"),
            rebound.rindex("Get-BoundStableTesterControlSet"),
        )
        for control_name in (
            "timeframe",
            "modelling",
            "useDate",
            "optimization",
            "forward",
            "criterion",
        ):
            self.assertIn(
                f'Select-BoundTesterComboMapped $Request "{control_name}"',
                configure,
            )
        self.assertLess(
            expert.index("Select-NativeComboExact $activeControls.expert"),
            expert.index("Get-BoundTesterControlSet $Request", expert.index("$reboundSelection")),
        )
        self.assertLess(
            expert.index("Get-BoundTesterControlSet $Request", expert.index("$reboundSelection")),
            expert.index("Read-UiaComboSelectionExact $candidate.controls.expert"),
        )

    def test_powershell_mt5_launcher_selects_exact_single_mode_once_before_settings(self) -> None:
        text = PS_PATH.read_text(encoding="utf-8")
        launcher = text[
            text.index("function Ensure-TesterSingleModeReady") : text.index(
                "function Get-ExactNamedControl"
            )
        ]
        bound = text[
            text.index("function Get-BoundTesterControlSet") : text.index(
                "function Normalize-TesterSettingsTabExact"
            )
        ]

        self.assertIn('Find-ControlByIdPresent $Root ([string]$required.start)', launcher)
        self.assertIn('Get-ControlByIdPresent $testerPane "10887"', launcher)
        self.assertIn('Get-ControlByIdPresent $launcher "3734"', launcher)
        self.assertIn('Get-ControlByIdPresent $launcher "10888"', launcher)
        self.assertIn('[string]$singleLabel.Current.Name -cne "Single"', launcher)
        self.assertIn('Assert-NativeControl $launcher "#32770"', launcher)
        self.assertIn('Assert-NativeControl $singleButton "Button"', launcher)
        self.assertIn('Assert-NativeControl $singleLabel "Static"', launcher)
        self.assertIn("GetParent($launcherHandle) -ne $testerPaneHandle", launcher)
        self.assertIn("GetParent($buttonHandle) -ne $launcherHandle", launcher)
        self.assertIn("GetParent($labelHandle) -ne $launcherHandle", launcher)
        self.assertEqual(launcher.count("Invoke-Exact $singleButton $code"), 1)
        self.assertIn("Get-BoundTerminalRoot $Request", launcher)
        self.assertIn("Get-TesterResultTabs $reboundRoot $required $code", launcher)
        self.assertNotIn("Invoke-TesterStartOnce", launcher)
        self.assertNotIn("Write-StartBoundary", launcher)
        self.assertGreaterEqual(bound.count("Ensure-TesterSingleModeReady $Request $root"), 2)

    def test_powershell_exact_expert_combo_injection_rejects_duplicates_and_rolls_back(self) -> None:
        require_interactive_ui_test(self)
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        quoted_path = str(PS_PATH).replace("'", "''")
        harness = rf"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class ComboHarnessNative {{
  [DllImport("user32.dll", EntryPoint="SetWindowLongPtrW", SetLastError=true)]
  public static extern IntPtr SetWindowLongPtr(IntPtr hWnd, int nIndex, IntPtr value);
}}
'@
$text = Get-Content -Raw '{quoted_path}'
$marker = 'Add-Type @"'
$nativeStart = $text.IndexOf($marker) + $marker.Length
$nativeEnd = $text.IndexOf('"@', $nativeStart)
if ($nativeStart -lt $marker.Length -or $nativeEnd -lt 0) {{ throw 'native helper source missing' }}
Add-Type -TypeDefinition $text.Substring($nativeStart, $nativeEnd - $nativeStart) -Language CSharp -ErrorAction Stop
$helperStart = $text.IndexOf('function Get-NativeClass')
$helperEnd = $text.IndexOf('function Select-NativeComboExact', $helperStart)
if ($helperStart -lt 0 -or $helperEnd -le $helperStart) {{ throw 'combo helper source missing' }}
function Fail([string]$Code) {{ throw $Code }}
function Read-TesterStartState($Control, [string]$Code) {{ return 'Start' }}
Invoke-Expression $text.Substring($helperStart, $helperEnd - $helperStart)
# WinForms wraps its local test ComboBox in a versioned class name, whereas
# production has a native `ComboBox`.  Keep the message-path test local and
# deterministic; the static production assertions above retain the exact
# owner/root/class guard in Assert-NativeControl.
function Assert-NativeControl($Control, [string]$ExpectedClass, [string]$Code) {{
    return [IntPtr][long]$Control.Current.NativeWindowHandle
}}
function Assert-ExpertCatalogRefreshBoundary($Request) {{ return ('a' * 64) }}
function Get-BoundTesterControlSet($Request) {{
    $script:control = [System.Windows.Automation.AutomationElement]::FromHandle($script:combo.Handle)
    $script:rootElement = [System.Windows.Automation.AutomationElement]::FromHandle($script:form.Handle)
    return [ordered]@{{ root = $script:rootElement; controls = [ordered]@{{ expert = $script:control; start = $script:control }} }}
}}
$mode = [string]$env:METAFX_COMBO_HARNESS_MODE
$expected = 'Metafxclub\AgentHQ\Expected.ex5'
$form = New-Object System.Windows.Forms.Form
$combo = New-Object System.Windows.Forms.ComboBox
$combo.DropDownStyle = [System.Windows.Forms.ComboBoxStyle]::DropDownList
[void]$combo.Items.Add('Existing.ex5')
$duplicateMode = $mode -ceq 'duplicate'
if ($duplicateMode) {{
    [void]$combo.Items.Add($expected)
    [void]$combo.Items.Add($expected)
}}
$combo.SelectedIndex = 0
$form.Controls.Add($combo)
$form.Show()
[System.Windows.Forms.Application]::DoEvents()
try {{
    [void][ComboHarnessNative]::SetWindowLongPtr($combo.Handle, -12, [IntPtr]10485)
    $TerminalProcess = Get-Process -Id $PID
    $script:TerminalRootHandle = $form.Handle
    $script:form = $form
    $script:combo = $combo
    $bound = Get-BoundTesterControlSet ([pscustomobject]@{{}})
    $beforeCount = (Invoke-NativeMessage $combo.Handle ([MetafxMt5VisibleNative]::CB_GETCOUNT) 0 0 'combo_probe_failed').ToInt32()
    if ($mode -ceq 'add_rejected') {{
        function Invoke-NativeComboAddStringExact($Control, [string]$Value, [string]$Code) {{ Fail 'synthetic_add_rejected' }}
    }}
    # This local WinForms control shares the PowerShell STA thread.  Sending
    # its parent a notification while synchronously querying in-process UIA
    # can deadlock the synthetic provider, so this harness isolates the
    # add/select/delete state machine; production notification binding remains
    # covered by the static exact parent/root/control-id assertions.
    function Send-NativeComboSelectionChange($Control, [string]$Code) {{ return }}
    if ($mode -ceq 'rollback') {{
        function Read-UiaComboSelectionExact($Control, [string[]]$ExpectedNames, [string]$Code) {{ Fail 'synthetic_uia_failure' }}
    }} else {{
        function Read-UiaComboSelectionExact($Control, [string[]]$ExpectedNames, [string]$Code) {{ return Read-NativeCombo $Control $Code }}
    }}
    $outcome = 'success'
    $errorCode = $null
    $result = $null
    try {{
        $result = Inject-NativeComboExpertExact ([pscustomobject]@{{}}) $expected @($expected)
    }} catch {{
        $outcome = 'error'
        $errorCode = [string]$_.Exception.Message
    }}
    $bound = Get-BoundTesterControlSet ([pscustomobject]@{{}})
    $afterCount = (Invoke-NativeMessage $combo.Handle ([MetafxMt5VisibleNative]::CB_GETCOUNT) 0 0 'combo_probe_failed').ToInt32()
    $selectedAfter = Read-NativeCombo $bound.controls.expert 'combo_probe_failed'
    $afterMatches = @(Get-NativeComboExactMatches $bound.controls.expert @($expected) 'combo_probe_failed')
    [pscustomobject]@{{
        mode = $mode
        outcome = $outcome
        errorCode = $errorCode
        beforeCount = $beforeCount
        afterCount = $afterCount
        selectedAfter = $selectedAfter
        expectedMatches = $afterMatches.Count
        exactReadback = if ($null -ne $result) {{ [string]$result.selected }} else {{ $null }}
    }} | ConvertTo-Json -Compress
}} finally {{
    $form.Close()
    $form.Dispose()
}}
"""
        cases = {
            "success": {
                "outcome": "success",
                "errorCode": None,
                "beforeCount": 1,
                "afterCount": 2,
                "selectedAfter": "Metafxclub\\AgentHQ\\Expected.ex5",
                "expectedMatches": 1,
                "exactReadback": "Metafxclub\\AgentHQ\\Expected.ex5",
            },
            "add_rejected": {
                "outcome": "error",
                "errorCode": "synthetic_add_rejected",
                "beforeCount": 1,
                "afterCount": 1,
                "selectedAfter": "Existing.ex5",
                "expectedMatches": 0,
                "exactReadback": None,
            },
            "rollback": {
                "outcome": "error",
                "errorCode": "synthetic_uia_failure",
                "beforeCount": 1,
                "afterCount": 1,
                "selectedAfter": "Existing.ex5",
                "expectedMatches": 0,
                "exactReadback": None,
            },
            "duplicate": {
                "outcome": "error",
                "errorCode": "mt5_expert_catalog_injection_precondition_failed",
                "beforeCount": 3,
                "afterCount": 3,
                "selectedAfter": "Existing.ex5",
                "expectedMatches": 2,
                "exactReadback": None,
            },
        }
        for mode, expected in cases.items():
            with self.subTest(mode=mode):
                environment = os.environ.copy()
                environment["METAFX_COMBO_HARNESS_MODE"] = mode
                completed = subprocess.run(
                    [powershell, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", harness],
                    text=True,
                    capture_output=True,
                    timeout=60,
                    check=False,
                    env=environment,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertTrue(completed.stdout.strip(), completed.stderr)
                actual = json.loads(completed.stdout.strip())
                self.assertEqual(actual.pop("mode"), mode)
                self.assertEqual(actual, expected)

    def test_powershell_uia_exact_readback_accepts_no_pattern_pane_provider(self) -> None:
        require_interactive_ui_test(self)
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        quoted_path = str(PS_PATH).replace("'", "''")
        harness = rf"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
$text = Get-Content -Raw '{quoted_path}'
$marker = 'Add-Type @"'
$nativeStart = $text.IndexOf($marker) + $marker.Length
$nativeEnd = $text.IndexOf('"@', $nativeStart)
Add-Type -TypeDefinition $text.Substring($nativeStart, $nativeEnd - $nativeStart) -Language CSharp -ErrorAction Stop
$helperStart = $text.IndexOf('function Get-NativeClass')
$helperEnd = $text.IndexOf('function Select-NativeComboExact', $helperStart)
function Fail([string]$Code) {{ throw $Code }}
Invoke-Expression $text.Substring($helperStart, $helperEnd - $helperStart)
function Assert-ExactExpertCombo($Control, [string]$Code) {{ return [IntPtr][long]$Control.Current.NativeWindowHandle }}
$expected = 'Metafxclub\AgentHQ\Expected.ex5'
$form = New-Object System.Windows.Forms.Form
$pane = New-Object System.Windows.Forms.Panel
$pane.AccessibleName = $expected
$pane.Text = $expected
$form.Controls.Add($pane)
$form.Show()
[System.Windows.Forms.Application]::DoEvents()
try {{
    $element = [System.Windows.Automation.AutomationElement]::FromHandle($pane.Handle)
    $patterns = @($element.GetSupportedPatterns())
    $value = Read-UiaComboSelectionExact $element @($expected) 'uia_readback_failed'
    [pscustomobject]@{{
        controlType = [string]$element.Current.ControlType.ProgrammaticName
        patternCount = $patterns.Count
        providerName = [string]$element.Current.Name
        value = [string]$value
    }} | ConvertTo-Json -Compress
}} finally {{
    $form.Close()
    $form.Dispose()
}}
"""
        completed = subprocess.run(
            [powershell, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", harness],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(completed.stdout.strip(), completed.stderr)
        self.assertEqual(
            json.loads(completed.stdout.strip()),
            {
                "controlType": "ControlType.Pane",
                "patternCount": 0,
                "providerName": "Metafxclub\\AgentHQ\\Expected.ex5",
                "value": "Metafxclub\\AgentHQ\\Expected.ex5",
            },
        )

    def test_powershell_remote_date_helper_roundtrips_without_local_pointer(self) -> None:
        require_interactive_ui_test(self)
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        quoted_path = str(PS_PATH).replace("'", "''")
        harness = rf"""
Add-Type -AssemblyName System.Windows.Forms
$text = Get-Content -Raw '{quoted_path}'
$marker = 'Add-Type @"'
$start = $text.IndexOf($marker) + $marker.Length
$end = $text.IndexOf('"@', $start)
if ($start -lt $marker.Length -or $end -lt 0) {{ throw 'native helper source missing' }}
Add-Type -TypeDefinition $text.Substring($start, $end - $start) -Language CSharp -ErrorAction Stop
$form = New-Object System.Windows.Forms.Form
$picker = New-Object System.Windows.Forms.DateTimePicker
$picker.Format = [System.Windows.Forms.DateTimePickerFormat]::Custom
$picker.CustomFormat = 'yyyy.MM.dd'
$form.Controls.Add($picker)
$form.Show()
[System.Windows.Forms.Application]::DoEvents()
try {{
    [MetafxMt5VisibleNative]::SetRemoteDate($picker.Handle, [uint32]$PID, $form.Handle, 2026, 10, 13)
    $actual = [MetafxMt5VisibleNative]::GetRemoteDate($picker.Handle, [uint32]$PID, $form.Handle)
    $wrongOwnerRejected = $false
    try {{
        [void][MetafxMt5VisibleNative]::GetRemoteDate($picker.Handle, [uint32]($PID + 1), $form.Handle)
    }} catch {{
        $wrongOwnerRejected = $_.Exception.InnerException.Message -ceq 'mt5_date_control_owner_invalid'
    }}
    if (-not $wrongOwnerRejected) {{ throw 'remote date owner guard missing' }}
    $actual
}} finally {{
    $form.Close()
    $form.Dispose()
}}
"""
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Sta",
                "-EncodedCommand",
                base64.b64encode(harness.encode("utf-16le")).decode("ascii"),
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "2026.10.13")

    def test_powershell_signed_terminal_binding_ignores_transient_main_window_handle_drift(self) -> None:
        require_interactive_ui_test(self)
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        text = PS_PATH.read_text(encoding="utf-8")
        self.assertIn(
            '$pre = New-Binding $TerminalProcess "strategy_tester" $autoBefore $TerminalRoot',
            text,
        )
        self.assertIn(
            '$post = New-Binding $TerminalProcess "strategy_tester" $autoAfter $TerminalRoot',
            text,
        )
        fragments = "\n".join(
            (
                text[text.index("function Fail("):text.index("function Enter-OperationMutex(")],
                text[
                    text.index("function Get-ExactTerminal("):
                    text.index("function Get-Root(")
                ],
                text[text.index("function Get-Root("):text.index("function Get-All(")],
                text[text.index("function Get-NativeOwner("):text.index("function Assert-NativeControl(")],
                text[
                    text.index("function Get-BoundTerminalRoot("):
                    text.index("function Get-BoundTesterControlSet(")
                ],
                text[
                    text.index("function New-Binding("):
                    text.index("function Assert-RequiredControls(")
                ],
            )
        )
        quoted_path = str(PS_PATH).replace("'", "''")
        fragments_b64 = base64.b64encode(fragments.encode()).decode("ascii")
        harness = rf"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
$text = Get-Content -Raw '{quoted_path}'
$marker = 'Add-Type @"'
$start = $text.IndexOf($marker) + $marker.Length
$end = $text.IndexOf('"@', $start)
if ($start -lt $marker.Length -or $end -lt 0) {{ throw 'native helper source missing' }}
Add-Type -TypeDefinition $text.Substring($start, $end - $start) -Language CSharp -ErrorAction Stop
$fragments = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{fragments_b64}'))
Invoke-Expression $fragments
$rootForm = New-Object System.Windows.Forms.Form
$driftForm = New-Object System.Windows.Forms.Form
$childButton = New-Object System.Windows.Forms.Button
$rootForm.Text = 'Signed MT5 Root'
$driftForm.Text = 'Transient Popup MainWindowHandle'
$childButton.Text = 'Not a signed root'
$rootForm.Controls.Add($childButton)
$rootForm.Show(); $driftForm.Show()
[System.Windows.Forms.Application]::DoEvents()
try {{
  $syntheticTerminalPath = 'C:\Synthetic MT5\terminal64.exe'
  $TerminalProcess = [pscustomobject]@{{
    Id = [int]$PID
    HasExited = $false
    Path = $syntheticTerminalPath
    MainWindowHandle = [IntPtr]$driftForm.Handle
  }}
  $TerminalProcess | Add-Member -MemberType ScriptMethod -Name Refresh -Value {{ }}
  function Get-Process {{
    param([string]$Name, [object]$ErrorAction)
    return @($TerminalProcess)
  }}
  $script:TerminalRootHandle = [IntPtr]$rootForm.Handle
  $request = [pscustomobject]@{{
    expectedTerminalProcessId = [int]$PID
    expectedTerminalWindowHandle = [long]$rootForm.Handle.ToInt64()
  }}
  $selected = Get-ExactTerminal `
    $syntheticTerminalPath `
    ([int]$PID) `
    ([long]$rootForm.Handle.ToInt64())
  $childWindowCode = $null
  try {{
    [void](Get-ExactTerminal `
      $syntheticTerminalPath `
      ([int]$PID) `
      ([long]$childButton.Handle.ToInt64()))
  }} catch {{
    $childWindowCode = [string]$_.Exception.Message
  }}
  $bound = Get-BoundTerminalRoot $request ([IntPtr]$rootForm.Handle)
  $script:TerminalRoot = $bound
  $binding = New-Binding `
    ([System.Diagnostics.Process]::GetCurrentProcess()) `
    'strategy_tester' `
    $false `
    $bound
  [ordered]@{{
    expectedProcessId = [int]$PID
    selectedProcessId = [int]$selected.Id
    childWindowCode = $childWindowCode
    dynamicMainWindowHandle = [long]$TerminalProcess.MainWindowHandle.ToInt64()
    expectedRootHandle = [long]$rootForm.Handle.ToInt64()
    boundRootHandle = [long]$bound.Current.NativeWindowHandle
    boundProcessId = [int]$bound.Current.ProcessId
    bindingTerminalWindowTitle = [string]$binding.terminalWindowTitle
  }} | ConvertTo-Json -Compress
}} finally {{
  $driftForm.Close(); $rootForm.Close()
  $driftForm.Dispose(); $rootForm.Dispose()
}}
"""
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Sta",
                "-Command",
                "& ([scriptblock]::Create([Console]::In.ReadToEnd()))",
            ],
            input=harness,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        observed = json.loads(completed.stdout.strip())
        self.assertNotEqual(
            observed["dynamicMainWindowHandle"], observed["expectedRootHandle"]
        )
        self.assertEqual(observed["selectedProcessId"], observed["expectedProcessId"])
        self.assertEqual(observed["childWindowCode"], "mt5_terminal_window_changed")
        self.assertEqual(observed["boundRootHandle"], observed["expectedRootHandle"])
        self.assertEqual(observed["boundProcessId"], observed["expectedProcessId"])
        self.assertEqual(observed["bindingTerminalWindowTitle"], "Signed MT5 Root")

    def test_powershell_remote_tree_helper_selects_exact_root_cross_process(self) -> None:
        require_interactive_ui_test(self)
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ready = root / "tree-ready.json"
            stop = root / "tree-stop"
            ready_ps = str(ready).replace("'", "''")
            stop_ps = str(stop).replace("'", "''")
            child_native = r"""
using System;
using System.Runtime.InteropServices;
public static class MetafxTreeHarnessNative {
  const int WS_CHILD = 0x40000000;
  const int WS_VISIBLE = 0x10000000;
  const int WS_TABSTOP = 0x00010000;
  const int TVS_HASBUTTONS = 0x0001;
  const int TVS_HASLINES = 0x0002;
  const int TVS_LINESATROOT = 0x0004;
  const int TVM_INSERTITEMW = 0x1132;
  const uint TVIF_TEXT = 0x0001;
  static readonly IntPtr TVI_ROOT = new IntPtr(-65536);
  static readonly IntPtr TVI_LAST = new IntPtr(-65534);
  [StructLayout(LayoutKind.Sequential)] struct TVITEM {
    public uint mask; public IntPtr hItem; public uint state; public uint stateMask;
    public IntPtr pszText; public int cchTextMax; public int iImage; public int iSelectedImage;
    public int cChildren; public IntPtr lParam;
  }
  [StructLayout(LayoutKind.Sequential)] struct TVINSERTSTRUCT {
    public IntPtr hParent; public IntPtr hInsertAfter; public TVITEM item;
  }
  [DllImport("comctl32.dll")] static extern void InitCommonControls();
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  static extern IntPtr CreateWindowEx(int exStyle, string className, string name, int style,
    int x, int y, int width, int height, IntPtr parent, IntPtr menu, IntPtr instance, IntPtr parameter);
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  static extern IntPtr SendMessage(IntPtr window, int message, IntPtr wParam, ref TVINSERTSTRUCT value);
  static IntPtr Add(IntPtr tree, IntPtr parent, string text) {
    IntPtr local = Marshal.StringToHGlobalUni(text);
    try {
      TVINSERTSTRUCT value = new TVINSERTSTRUCT {
        hParent = parent, hInsertAfter = TVI_LAST,
        item = new TVITEM { mask = TVIF_TEXT, pszText = local, cchTextMax = text.Length + 1 }
      };
      IntPtr item = SendMessage(tree, TVM_INSERTITEMW, IntPtr.Zero, ref value);
      if (item == IntPtr.Zero) throw new InvalidOperationException("tree_harness_insert_failed");
      return item;
    } finally { Marshal.FreeHGlobal(local); }
  }
  public static IntPtr Create(IntPtr parent) {
    InitCommonControls();
    IntPtr tree = CreateWindowEx(0, "SysTreeView32", "",
      WS_CHILD | WS_VISIBLE | WS_TABSTOP | TVS_HASBUTTONS | TVS_HASLINES | TVS_LINESATROOT,
      0, 0, 380, 260, parent, (IntPtr)10064, IntPtr.Zero, IntPtr.Zero);
    if (tree == IntPtr.Zero) throw new InvalidOperationException("tree_harness_create_failed");
    IntPtr accounts = Add(tree, TVI_ROOT, "Accounts");
    Add(tree, accounts, "Expert Advisors");
    Add(tree, TVI_ROOT, "Expert Advisors");
    Add(tree, TVI_ROOT, "Indicators");
    Add(tree, TVI_ROOT, "Duplicate Root");
    Add(tree, TVI_ROOT, "Duplicate Root");
    return tree;
  }
  public static IntPtr CreateNested(IntPtr parent) {
    InitCommonControls();
    IntPtr tree = CreateWindowEx(0, "SysTreeView32", "",
      WS_CHILD | WS_VISIBLE | WS_TABSTOP | TVS_HASBUTTONS | TVS_HASLINES | TVS_LINESATROOT,
      0, 0, 380, 260, parent, (IntPtr)10065, IntPtr.Zero, IntPtr.Zero);
    if (tree == IntPtr.Zero) throw new InvalidOperationException("tree_harness_create_failed");
    IntPtr broker = Add(tree, TVI_ROOT, "RoboForex MT5");
    Add(tree, broker, "Accounts");
    Add(tree, broker, "Expert Advisors");
    Add(tree, broker, "Indicators");
    Add(tree, broker, "Duplicate Child");
    Add(tree, broker, "Duplicate Child");
    return tree;
  }
}
"""
            child_native_b64 = base64.b64encode(child_native.encode()).decode("ascii")
            child_script = rf"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$nativeSource = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{child_native_b64}'))
Add-Type -TypeDefinition $nativeSource -Language CSharp -ErrorAction Stop
$form = New-Object System.Windows.Forms.Form
$form.Text = 'Metafx Tree Harness'
$form.ShowInTaskbar = $false
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
$form.Location = [System.Drawing.Point]::new(-30000, -30000)
$form.Size = [System.Drawing.Size]::new(400, 300)
$form.Show()
$treeHandle = [MetafxTreeHarnessNative]::Create($form.Handle)
$nestedTreeHandle = [MetafxTreeHarnessNative]::CreateNested($form.Handle)
[System.Windows.Forms.Application]::DoEvents()
$payload = [ordered]@{{ processId=$PID; rootHandle=$form.Handle.ToInt64(); treeHandle=$treeHandle.ToInt64(); nestedTreeHandle=$nestedTreeHandle.ToInt64() }}
[System.IO.File]::WriteAllText('{ready_ps}', ($payload | ConvertTo-Json -Compress), [System.Text.UTF8Encoding]::new($false))
while (-not [System.IO.File]::Exists('{stop_ps}')) {{
    [System.Windows.Forms.Application]::DoEvents()
    Start-Sleep -Milliseconds 20
}}
$form.Close()
$form.Dispose()
"""
            child = subprocess.Popen(
                [
                    powershell,
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Sta",
                    "-EncodedCommand",
                    base64.b64encode(child_script.encode("utf-16le")).decode("ascii"),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                deadline = time.monotonic() + 15
                while not ready.exists() and time.monotonic() < deadline:
                    if child.poll() is not None:
                        stdout, stderr = child.communicate(timeout=1)
                        self.fail(
                            f"Tree harness exited early: {stdout!r} {stderr!r}"
                        )
                    time.sleep(0.05)
                self.assertTrue(ready.exists(), "Tree harness did not publish handles")
                handles = json.loads(ready.read_text(encoding="utf-8"))
                quoted_path = str(PS_PATH).replace("'", "''")
                parent_script = rf"""
$text = Get-Content -Raw '{quoted_path}'
$marker = 'Add-Type @"'
$start = $text.IndexOf($marker) + $marker.Length
$end = $text.IndexOf('"@', $start)
if ($start -lt $marker.Length -or $end -lt 0) {{ throw 'native helper source missing' }}
Add-Type -TypeDefinition $text.Substring($start, $end - $start) -Language CSharp -ErrorAction Stop
$tree = [IntPtr][long]{int(handles['treeHandle'])}
$nestedTree = [IntPtr][long]{int(handles['nestedTreeHandle'])}
$root = [IntPtr][long]{int(handles['rootHandle'])}
$pidValue = [uint32]{int(handles['processId'])}
$preListingSelected = [MetafxMt5VisibleNative]::SelectRootTreeItemExact($tree, $pidValue, $root, 'Accounts')
$labels = [MetafxMt5VisibleNative]::ListRootTreeItemTexts($tree, $pidValue, $root)
$postListingSelected = [MetafxMt5VisibleNative]::ReadSelectedRootTreeItemExact($tree, $pidValue, $root, 'Accounts')
$nestedRoots = [MetafxMt5VisibleNative]::ListRootTreeItemTexts($nestedTree, $pidValue, $root)
$preChildListingSelected = [MetafxMt5VisibleNative]::SelectRootOrSingleRootChildExact($nestedTree, $pidValue, $root, 'Accounts')
$nestedChildren = [MetafxMt5VisibleNative]::ListSingleRootDirectChildItemTexts($nestedTree, $pidValue, $root)
$postChildListingSelected = [MetafxMt5VisibleNative]::ReadSelectedRootOrSingleRootChildExact($nestedTree, $pidValue, $root, 'Accounts')
if ($preListingSelected -cne 'Accounts' -or $postListingSelected -cne 'Accounts' -or
    $preChildListingSelected -cne 'Accounts' -or $postChildListingSelected -cne 'Accounts') {{
    throw 'read-only listing changed the selected tree item'
}}
$wrongOwnerRejected = $false
try {{
    [void][MetafxMt5VisibleNative]::ListRootTreeItemTexts($tree, [uint32]($pidValue + 1), $root)
}} catch {{
    $wrongOwnerRejected = $_.Exception.InnerException.Message -ceq 'mt5_date_control_owner_invalid'
}}
if (-not $wrongOwnerRejected) {{ throw 'wrong tree owner was not rejected' }}
$wrongClassRejected = $false
try {{
    [void][MetafxMt5VisibleNative]::ListRootTreeItemTexts($root, $pidValue, $root)
}} catch {{
    $wrongClassRejected = $_.Exception.InnerException.Message -ceq 'mt5_tree_control_invalid'
}}
if (-not $wrongClassRejected) {{ throw 'wrong tree class was not rejected' }}
$selected = [MetafxMt5VisibleNative]::SelectRootTreeItemExact($tree, $pidValue, $root, 'Expert Advisors')
$readback = [MetafxMt5VisibleNative]::ReadSelectedRootTreeItemExact($tree, $pidValue, $root, 'Expert Advisors')
$nestedSelected = [MetafxMt5VisibleNative]::SelectRootOrSingleRootChildExact($nestedTree, $pidValue, $root, 'Expert Advisors')
$nestedReadback = [MetafxMt5VisibleNative]::ReadSelectedRootOrSingleRootChildExact($nestedTree, $pidValue, $root, 'Expert Advisors')
$ambiguousRejected = $false
try {{
    [void][MetafxMt5VisibleNative]::SelectRootTreeItemExact($tree, $pidValue, $root, 'Duplicate Root')
}} catch {{
    $ambiguousRejected = $_.Exception.InnerException.Message -ceq 'mt5_tree_item_ambiguous'
}}
if (-not $ambiguousRejected) {{ throw 'ambiguous root tree item was not rejected' }}
$ambiguousChildRejected = $false
try {{
    [void][MetafxMt5VisibleNative]::SelectRootOrSingleRootChildExact($nestedTree, $pidValue, $root, 'Duplicate Child')
}} catch {{
    $ambiguousChildRejected = $_.Exception.InnerException.Message -ceq 'mt5_tree_item_ambiguous'
}}
if (-not $ambiguousChildRejected) {{ throw 'ambiguous direct child tree item was not rejected' }}
$targetThreadOwner = [uint32]0
$targetThread = [MetafxMt5VisibleNative]::GetWindowThreadProcessId($root, [ref]$targetThreadOwner)
if ($targetThreadOwner -ne $pidValue -or $targetThread -eq 0) {{ throw 'tree harness target thread invalid' }}
[void][MetafxMt5VisibleNative]::SetForegroundWindow($root)
if ([MetafxMt5VisibleNative]::GetForegroundWindow() -ne $root) {{
    $currentThread = [MetafxMt5VisibleNative]::GetCurrentThreadId()
    $foreground = [MetafxMt5VisibleNative]::GetForegroundWindow()
    $foregroundOwner = [uint32]0
    $foregroundThread = if ($foreground -ne [IntPtr]::Zero) {{ [MetafxMt5VisibleNative]::GetWindowThreadProcessId($foreground, [ref]$foregroundOwner) }} else {{ 0 }}
    $attachedForeground = $false
    $attachedTarget = $false
    try {{
        if ($foregroundThread -gt 0 -and $foregroundThread -ne $currentThread -and $foregroundThread -ne $targetThread) {{
            $attachedForeground = [MetafxMt5VisibleNative]::AttachThreadInput($currentThread, $foregroundThread, $true)
        }}
        if ($targetThread -ne $currentThread) {{
            $attachedTarget = [MetafxMt5VisibleNative]::AttachThreadInput($currentThread, $targetThread, $true)
        }}
        [void][MetafxMt5VisibleNative]::BringWindowToTop($root)
        [void][MetafxMt5VisibleNative]::SetForegroundWindow($root)
        [void][MetafxMt5VisibleNative]::SetActiveWindow($root)
    }} finally {{
        if ($attachedTarget) {{ [void][MetafxMt5VisibleNative]::AttachThreadInput($currentThread, $targetThread, $false) }}
        if ($attachedForeground) {{ [void][MetafxMt5VisibleNative]::AttachThreadInput($currentThread, $foregroundThread, $false) }}
    }}
}}
$focusDeadline = [DateTime]::UtcNow.AddSeconds(3)
while ([MetafxMt5VisibleNative]::GetForegroundWindow() -ne $root -and [DateTime]::UtcNow -lt $focusDeadline) {{
    [void][MetafxMt5VisibleNative]::SetForegroundWindow($root)
    Start-Sleep -Milliseconds 25
}}
if ([MetafxMt5VisibleNative]::GetForegroundWindow() -ne $root) {{ throw 'tree harness foreground failed' }}
[MetafxMt5VisibleNative]::FocusTreeExact($nestedTree, $pidValue, $root)
[MetafxMt5VisibleNative]::AssertTreeFocusExact($nestedTree, $pidValue, $root)
[MetafxMt5VisibleNative]::AssertSelectedTreeContextExact($nestedTree, $pidValue, $root, 'Expert Advisors')
$focusWrongClassRejected = $false
try {{
    [MetafxMt5VisibleNative]::FocusTreeExact($root, $pidValue, $root)
}} catch {{
    $focusWrongClassRejected = $_.Exception.InnerException.Message -ceq 'mt5_tree_control_invalid'
}}
if (-not $focusWrongClassRejected) {{ throw 'focus helper accepted wrong native class' }}
[MetafxMt5VisibleNative]::FocusTreeExact($tree, $pidValue, $root)
$sendInvoked = $false
$focusTheftRejected = $false
try {{
    [MetafxMt5VisibleNative]::AssertSelectedTreeContextExact($nestedTree, $pidValue, $root, 'Expert Advisors')
    $sendInvoked = $true
}} catch {{
    $focusTheftRejected = $_.Exception.InnerException.Message -ceq 'mt5_tree_focus_readback_failed'
}}
if (-not $focusTheftRejected -or $sendInvoked) {{ throw 'focus theft did not prevent guarded dispatch' }}
"$([string]::Join(';', $labels))|$([string]::Join(';', $nestedRoots))|$([string]::Join(';', $nestedChildren))|$selected|$readback|$nestedSelected|$nestedReadback|focus-exact|focus-theft-rejected"
"""
                completed = subprocess.run(
                    [
                        powershell,
                        "-NoLogo",
                        "-NoProfile",
                        "-NonInteractive",
                        "-Sta",
                        "-EncodedCommand",
                        base64.b64encode(parent_script.encode("utf-16le")).decode(
                            "ascii"
                        ),
                    ],
                    text=True,
                    capture_output=True,
                    timeout=30,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(
                    completed.stdout.strip(),
                    "Accounts;Expert Advisors;Indicators;Duplicate Root;Duplicate Root|RoboForex MT5|Accounts;Expert Advisors;Indicators;Duplicate Child;Duplicate Child|Expert Advisors|Expert Advisors|Expert Advisors|Expert Advisors|focus-exact|focus-theft-rejected",
                )
            finally:
                stop.write_text("stop", encoding="utf-8")
                try:
                    child_stdout, child_stderr = child.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    child.terminate()
                    child_stdout, child_stderr = child.communicate(timeout=5)
                if child.returncode not in {0, None}:
                    self.fail(
                        f"Tree harness failed: {child_stdout!r} {child_stderr!r}"
                    )

    def test_desktop_harnesses_skip_before_process_launch_without_opt_in(self) -> None:
        harness_names = (
            "capture_window_uses_exact_root_and_fails_closed",
            "native_results_list_focus_is_exact_and_id_guarded",
            "start_post_is_exact_nonblocking_and_one_shot",
            "symbol_combo_accepts_only_exact_current_text_when_catalog_is_empty",
            "exact_expert_combo_injection_rejects_duplicates_and_rolls_back",
            "uia_exact_readback_accepts_no_pattern_pane_provider",
            "remote_date_helper_roundtrips_without_local_pointer",
            "signed_terminal_binding_ignores_transient_main_window_handle_drift",
            "remote_tree_helper_selects_exact_root_cross_process",
            "native_popup_selects_exact_item_with_return_command_menu",
        )
        with (
            mock.patch.dict(os.environ, {}, clear=True),
            mock.patch.object(
                shutil, "which", side_effect=AssertionError("PowerShell lookup before opt-in")
            ),
            mock.patch.object(
                subprocess, "run", side_effect=AssertionError("Process launched before opt-in")
            ),
            mock.patch.object(
                subprocess, "Popen", side_effect=AssertionError("Process launched before opt-in")
            ),
        ):
            for harness_name in harness_names:
                with self.subTest(harness=harness_name):
                    case = type(self)(f"test_powershell_{harness_name}")
                    with self.assertRaisesRegex(unittest.SkipTest, "Interactive Windows UI harness is opt-in"):
                        getattr(case, case._testMethodName)()

    def test_interactive_popup_harness_is_explicitly_opt_in(self) -> None:
        self.assertEqual(INTERACTIVE_UI_TEST_ENV, "METAFX_RUN_INTERACTIVE_UI_TESTS")
        self.assertFalse(interactive_ui_tests_enabled({}))
        self.assertFalse(
            interactive_ui_tests_enabled({INTERACTIVE_UI_TEST_ENV: "true"})
        )
        self.assertTrue(interactive_ui_tests_enabled({INTERACTIVE_UI_TEST_ENV: "1"}))
        popup_source = inspect.getsource(
            type(self).test_powershell_native_popup_selects_exact_item_with_return_command_menu
        )
        self.assertLess(
            popup_source.index("require_interactive_ui_test(self)"),
            popup_source.index('shutil.which("powershell.exe")'),
        )
        self.assertIn("WM_CANCELMODE", popup_source)
        self.assertIn("System.Threading.Timer", popup_source)
        self.assertIn("$testRunnerProcessId", popup_source)
        self.assertIn("Get-Process -Id $testRunnerProcessId", popup_source)
        self.assertIn("SaveFileDialog", popup_source)
        self.assertIn("FindOwnedDialogExact", popup_source)
        self.assertIn("MaterializeSubmenuItemData", popup_source)
        self.assertNotIn("TPM_NONOTIFY", popup_source)

    def test_powershell_native_popup_selects_exact_item_with_return_command_menu(self) -> None:
        require_interactive_ui_test(self)
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ready = root / "popup-ready.json"
            open_signal = root / "popup-open"
            result_path = root / "popup-result.txt"
            stop = root / "popup-stop"
            child_native = r"""
using System;
using System.Runtime.InteropServices;
using System.Windows.Forms;
public sealed class MetafxPopupHarnessForm : Form {
  const int WM_COMMAND = 0x0111;
  const int WM_INITMENUPOPUP = 0x0117;
  public uint LastCommand { get; private set; }
  protected override void WndProc(ref Message message) {
    if (message.Msg == WM_INITMENUPOPUP) {
      MetafxPopupHarnessNative.MaterializeSubmenuItemData(message.WParam);
    }
    if (message.Msg == WM_COMMAND) {
      uint command = (uint)(message.WParam.ToInt64() & 0xffffL);
      LastCommand = command;
      if (command == 33420) {
        using (SaveFileDialog dialog = new SaveFileDialog()) {
          dialog.Title = "Save As";
          dialog.FileName = "ReportTester-52021307.html";
          dialog.Filter = "HTML Files (*.html)|*.html";
          dialog.ShowDialog(this);
        }
        return;
      }
    }
    base.WndProc(ref message);
  }
}
public static class MetafxPopupHarnessNative {
  const uint WM_NULL = 0x0000;
  const uint WM_CANCELMODE = 0x001F;
  const uint MF_STRING = 0x0000;
  const uint MF_POPUP = 0x0010;
  const uint MF_SEPARATOR = 0x0800;
  [StructLayout(LayoutKind.Sequential)] struct RECT { public int Left, Top, Right, Bottom; }
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct MENUITEMINFO {
    public uint cbSize; public uint fMask; public uint fType; public uint fState; public uint wID;
    public IntPtr hSubMenu; public IntPtr hbmpChecked; public IntPtr hbmpUnchecked;
    public UIntPtr dwItemData; public IntPtr dwTypeData; public uint cch; public IntPtr hbmpItem;
  }
  [DllImport("user32.dll", SetLastError=true)] static extern IntPtr CreatePopupMenu();
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool AppendMenu(IntPtr menu, uint flags, UIntPtr id, string text);
  [DllImport("user32.dll", SetLastError=true)] static extern bool DestroyMenu(IntPtr menu);
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool SetMenuItemInfo(IntPtr menu, uint item, bool byPosition, ref MENUITEMINFO info);
  [DllImport("user32.dll", SetLastError=true)] static extern uint TrackPopupMenuEx(IntPtr menu, uint flags, int x, int y, IntPtr owner, IntPtr parameters);
  [DllImport("user32.dll", SetLastError=true)] static extern bool GetWindowRect(IntPtr window, out RECT rect);
  [DllImport("user32.dll", SetLastError=true)] public static extern bool SetForegroundWindow(IntPtr window);
  [DllImport("user32.dll", SetLastError=true)] static extern bool BringWindowToTop(IntPtr window);
  [DllImport("user32.dll", SetLastError=true)] static extern bool PostMessage(IntPtr window, uint message, IntPtr wParam, IntPtr lParam);
  [DllImport("user32.dll", SetLastError=true)] static extern IntPtr SetActiveWindow(IntPtr window);
  [DllImport("user32.dll", SetLastError=true)] static extern IntPtr SetFocus(IntPtr window);
  [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll", SetLastError=true)] static extern uint GetWindowThreadProcessId(IntPtr window, out uint processId);
  [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
  [DllImport("user32.dll", SetLastError=true)] static extern bool AttachThreadInput(uint sourceThread, uint targetThread, bool attach);
  public static void MaterializeSubmenuItemData(IntPtr menu) {
    const uint MIIM_DATA = 0x00000020;
    MENUITEMINFO first = new MENUITEMINFO { cbSize=(uint)Marshal.SizeOf(typeof(MENUITEMINFO)), fMask=MIIM_DATA, dwItemData=(UIntPtr)65711 };
    MENUITEMINFO second = new MENUITEMINFO { cbSize=(uint)Marshal.SizeOf(typeof(MENUITEMINFO)), fMask=MIIM_DATA, dwItemData=(UIntPtr)65666 };
    // The parent menu has four entries; the two-entry leaf is the exact
    // submenu.  Updating by position there reproduces build 6230's lazy
    // zero -> nonzero dwItemData materialization when it becomes visible.
    SetMenuItemInfo(menu, 0, true, ref first);
    SetMenuItemInfo(menu, 1, true, ref second);
  }
  static void ForceForeground(IntPtr owner) {
    DateTime deadline = DateTime.UtcNow.AddSeconds(2);
    do {
      IntPtr foreground = GetForegroundWindow(); uint ignored = 0;
      uint foregroundThread = foreground == IntPtr.Zero ? 0 : GetWindowThreadProcessId(foreground, out ignored);
      uint currentThread = GetCurrentThreadId(); bool attached = false;
      if (foregroundThread != 0 && foregroundThread != currentThread)
        attached = AttachThreadInput(currentThread, foregroundThread, true);
      try { BringWindowToTop(owner); SetForegroundWindow(owner); SetActiveWindow(owner); SetFocus(owner); }
      finally { if (attached) AttachThreadInput(currentThread, foregroundThread, false); }
      if (GetForegroundWindow() == owner) return;
      System.Threading.Thread.Sleep(25);
    } while (DateTime.UtcNow < deadline);
    throw new InvalidOperationException("popup_harness_foreground_failed");
  }
  public static uint ShowReturnCommandMenu(MetafxPopupHarnessForm owner) {
    IntPtr menu = CreatePopupMenu();
    IntPtr submenu = CreatePopupMenu();
    if (menu == IntPtr.Zero || submenu == IntPtr.Zero) throw new InvalidOperationException("popup_harness_create_failed");
    bool submenuAttached = false;
    try {
      if (!AppendMenu(submenu, MF_STRING, (UIntPtr)33419, "Open XML (MS Office Excel 2007)") ||
          !AppendMenu(submenu, MF_STRING, (UIntPtr)33420, "HTML (Internet Explorer)") ||
          !AppendMenu(menu, MF_STRING, (UIntPtr)33417, "Other") ||
          !AppendMenu(menu, MF_STRING, (UIntPtr)33418, "Report") ||
          !AppendMenu(menu, MF_SEPARATOR, UIntPtr.Zero, String.Empty) ||
          !AppendMenu(menu, MF_POPUP, (UIntPtr)(ulong)submenu.ToInt64(), "Report"))
        throw new InvalidOperationException("popup_harness_append_failed");
      submenuAttached = true;
      RECT rect;
      if (!GetWindowRect(owner.Handle, out rect)) throw new InvalidOperationException("popup_harness_rect_failed");
      // Desktop focus can cancel a test popup before the controller binds it.
      // WM_NULL resets TrackPopupMenu state before a bounded reopen attempt.
      DateTime deadline = DateTime.UtcNow.AddSeconds(5);
      do {
        ForceForeground(owner.Handle);
        int menuActive = 1;
        System.Threading.Timer watchdog = new System.Threading.Timer(delegate(object state) {
          if (System.Threading.Interlocked.CompareExchange(ref menuActive, 1, 1) == 1)
            PostMessage(owner.Handle, WM_CANCELMODE, IntPtr.Zero, IntPtr.Zero);
        }, null, 10000, System.Threading.Timeout.Infinite);
        uint command;
        try {
          command = TrackPopupMenuEx(menu, 0, rect.Left + 40, rect.Top + 40, owner.Handle, IntPtr.Zero);
        } finally {
          System.Threading.Interlocked.Exchange(ref menuActive, 0);
          watchdog.Dispose();
        }
        if (!PostMessage(owner.Handle, WM_NULL, IntPtr.Zero, IntPtr.Zero))
          throw new InvalidOperationException("popup_harness_post_track_failed");
        if (command != 0 && owner.LastCommand != 0) return owner.LastCommand;
        System.Threading.Thread.Sleep(25);
      } while (DateTime.UtcNow < deadline);
      return 0;
    } finally {
      DestroyMenu(menu);
      if (!submenuAttached) DestroyMenu(submenu);
    }
  }
}
"""
            native_b64 = base64.b64encode(child_native.encode()).decode("ascii")
            child_script = rf"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$nativeSource = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{native_b64}'))
Add-Type -TypeDefinition $nativeSource -Language CSharp -ReferencedAssemblies @('System.Windows.Forms.dll','System.Drawing.dll') -ErrorAction Stop
$form = New-Object MetafxPopupHarnessForm
$form.Text = 'Metafx Popup Harness'
$form.ShowInTaskbar = $false
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
$form.Location = [System.Drawing.Point]::new(80, 80)
$form.Size = [System.Drawing.Size]::new(360, 220)
$form.Show()
$form.Activate()
[void][MetafxPopupHarnessNative]::SetForegroundWindow($form.Handle)
[System.Windows.Forms.Application]::DoEvents()
[System.IO.File]::WriteAllText('{str(ready).replace("'", "''")}', ([ordered]@{{processId=$PID;rootHandle=$form.Handle.ToInt64()}} | ConvertTo-Json -Compress), [System.Text.UTF8Encoding]::new($false))
$testRunnerProcessId = {os.getpid()}
while (-not [System.IO.File]::Exists('{str(open_signal).replace("'", "''")}')) {{
  if ($null -eq (Get-Process -Id $testRunnerProcessId -ErrorAction SilentlyContinue)) {{ break }}
  [System.Windows.Forms.Application]::DoEvents(); Start-Sleep -Milliseconds 10
}}
if ([System.IO.File]::Exists('{str(open_signal).replace("'", "''")}')) {{
  $command = [MetafxPopupHarnessNative]::ShowReturnCommandMenu($form)
  [System.IO.File]::WriteAllText('{str(result_path).replace("'", "''")}', [string]$command, [System.Text.UTF8Encoding]::new($false))
  while (-not [System.IO.File]::Exists('{str(stop).replace("'", "''")}')) {{
    if ($null -eq (Get-Process -Id $testRunnerProcessId -ErrorAction SilentlyContinue)) {{ break }}
    [System.Windows.Forms.Application]::DoEvents(); Start-Sleep -Milliseconds 10
  }}
}}
$form.Close(); $form.Dispose()
"""
            child = subprocess.Popen(
                [
                    powershell,
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Sta",
                    "-EncodedCommand",
                    base64.b64encode(child_script.encode("utf-16le")).decode("ascii"),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                deadline = time.monotonic() + 15
                while not ready.exists() and time.monotonic() < deadline:
                    if child.poll() is not None:
                        stdout, stderr = child.communicate(timeout=1)
                        self.fail(f"Popup harness exited early: {stdout!r} {stderr!r}")
                    time.sleep(0.05)
                self.assertTrue(ready.exists(), "Popup harness did not publish handles")
                handles = json.loads(ready.read_text(encoding="utf-8"))
                quoted_path = str(PS_PATH).replace("'", "''")
                quoted_open_signal = str(open_signal).replace("'", "''")
                parent_script = rf"""
$ErrorActionPreference = 'Stop'
$finderSource = @'
using System;
using System.Runtime.InteropServices;
public static class MetafxPopupHarnessFinder {{
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  public static extern IntPtr FindWindowEx(IntPtr parent, IntPtr childAfter, string className, string windowName);
}}
'@
Add-Type -TypeDefinition $finderSource -Language CSharp -ErrorAction Stop
$text = Get-Content -Raw '{quoted_path}'
$marker = 'Add-Type @"'
$start = $text.IndexOf($marker) + $marker.Length
$end = $text.IndexOf('"@', $start)
if ($start -lt $marker.Length -or $end -lt 0) {{ throw 'native helper source missing' }}
Add-Type -TypeDefinition $text.Substring($start, $end - $start) -Language CSharp -ErrorAction Stop
$pidValue = [uint32]{int(handles['processId'])}
$rootHandle = [IntPtr][long]{int(handles['rootHandle'])}
[System.IO.File]::WriteAllText('{quoted_open_signal}', 'open', [System.Text.UTF8Encoding]::new($false))
$foregroundDeadline = [DateTime]::UtcNow.AddSeconds(2)
while ([MetafxMt5VisibleNative]::GetForegroundWindow() -ne $rootHandle -and [DateTime]::UtcNow -lt $foregroundDeadline) {{ Start-Sleep -Milliseconds 20 }}
if ([MetafxMt5VisibleNative]::GetForegroundWindow() -ne $rootHandle) {{ throw 'popup harness root not foreground' }}
$deadline = [DateTime]::UtcNow.AddSeconds(5)
$matches = @()
do {{
  # The native system-menu host is not exposed by UI Automation reliably on
  # every interactive Windows desktop, so discover its HWND natively.
  $matches = @()
  $candidate = [IntPtr]::Zero
  while ($true) {{
    $candidate = [MetafxPopupHarnessFinder]::FindWindowEx([IntPtr]::Zero, $candidate, '#32768', $null)
    if ($candidate -eq [IntPtr]::Zero) {{ break }}
    $candidatePid = [uint32]0
    [void][MetafxMt5VisibleNative]::GetWindowThreadProcessId($candidate, [ref]$candidatePid)
    if ($candidatePid -eq $pidValue -and [MetafxMt5VisibleNative]::IsWindowVisible($candidate)) {{ $matches += $candidate }}
  }}
  if ($matches.Count -eq 1) {{ break }}
  Start-Sleep -Milliseconds 20
}} while ([DateTime]::UtcNow -lt $deadline)
if ($matches.Count -ne 1) {{ throw "popup harness menu count $($matches.Count)" }}
$popup = [IntPtr]$matches[0]
$token = [MetafxMt5VisibleNative]::CapturePopupMenuTokenExact($popup, $pidValue, $rootHandle)
$wrongParentRejected = $false
try {{ [void][MetafxMt5VisibleNative]::AssertPopupSubmenuCommandFromTokenExact($token, $pidValue, $rootHandle, 'report', 'HTML (Internet Explorer)', [uint32]33420) }} catch {{ $wrongParentRejected = $true }}
if (-not $wrongParentRejected) {{ throw 'popup exact parent guard missing' }}
$wrongTextRejected = $false
try {{ [void][MetafxMt5VisibleNative]::AssertPopupSubmenuCommandFromTokenExact($token, $pidValue, $rootHandle, 'Report', 'HTML (Internet Explorer) forged', [uint32]33420) }} catch {{ $wrongTextRejected = $true }}
if (-not $wrongTextRejected) {{ throw 'popup exact child text guard missing' }}
$wrongIdRejected = $false
try {{ [void][MetafxMt5VisibleNative]::AssertPopupSubmenuCommandFromTokenExact($token, $pidValue, $rootHandle, 'Report', 'HTML (Internet Explorer)', [uint32]33419) }} catch {{ $wrongIdRejected = $true }}
if (-not $wrongIdRejected) {{ throw 'popup exact child id guard missing' }}
$selected = [MetafxMt5VisibleNative]::InvokePopupSubmenuCommandExact($token, $pidValue, $rootHandle, 'Report', 'HTML (Internet Explorer)', [uint32]33420)
$dialogDeadline = [DateTime]::UtcNow.AddSeconds(5)
[IntPtr]$dialog = [IntPtr]::Zero
do {{
  $dialog = [MetafxMt5VisibleNative]::FindOwnedDialogExact($pidValue, $rootHandle, [string[]]@('Save As'))
  if ($dialog -ne [IntPtr]::Zero) {{ break }}
  Start-Sleep -Milliseconds 20
}} while ([DateTime]::UtcNow -lt $dialogDeadline)
if ($dialog -eq [IntPtr]::Zero) {{ throw 'popup exact command did not open owned Save As dialog' }}
[IntPtr]$wrongTitle = [MetafxMt5VisibleNative]::FindOwnedDialogExact($pidValue, $rootHandle, [string[]]@('Save As forged'))
if ($wrongTitle -ne [IntPtr]::Zero) {{ throw 'popup command accepted wrong dialog title' }}
if ([MetafxMt5VisibleNative]::GetWindow($dialog, [MetafxMt5VisibleNative]::GW_OWNER) -ne $rootHandle) {{
  throw 'popup command dialog owner changed'
}}
if (-not [MetafxMt5VisibleNative]::PostMessage($dialog, [MetafxMt5VisibleNative]::WM_COMMAND, [IntPtr]2, [IntPtr]::Zero)) {{
  throw 'popup command dialog cancel failed'
}}
$dialogCloseDeadline = [DateTime]::UtcNow.AddSeconds(5)
while ([MetafxMt5VisibleNative]::IsWindow($dialog) -and [DateTime]::UtcNow -lt $dialogCloseDeadline) {{ Start-Sleep -Milliseconds 20 }}
if ([MetafxMt5VisibleNative]::IsWindow($dialog)) {{ throw 'popup command dialog remained open' }}
[ordered]@{{position=[int]$selected.Position;text=[string]$selected.Text;commandId=[long]$selected.CommandId;enabled=[bool]$selected.IsEnabled;ownedSaveDialog=$true;wrongTitleRejected=$true}} | ConvertTo-Json -Compress
"""
                completed = subprocess.run(
                    [
                        powershell,
                        "-NoLogo",
                        "-NoProfile",
                        "-NonInteractive",
                        "-Sta",
                        "-EncodedCommand",
                        base64.b64encode(parent_script.encode("utf-16le")).decode("ascii"),
                    ],
                    text=True,
                    capture_output=True,
                    timeout=30,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                selected = json.loads(completed.stdout.strip())
                self.assertEqual(selected["position"], 1)
                self.assertEqual(selected["text"], "HTML (Internet Explorer)")
                self.assertEqual(selected["commandId"], 33420)
                self.assertTrue(selected["enabled"])
                self.assertTrue(selected["ownedSaveDialog"])
                self.assertTrue(selected["wrongTitleRejected"])
                deadline = time.monotonic() + 5
                while not result_path.exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue(result_path.exists(), "Popup menu did not return a command")
                self.assertEqual(result_path.read_text(encoding="utf-8"), "33420")
            finally:
                stop.write_text("stop", encoding="utf-8")
                try:
                    child_stdout, child_stderr = child.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    child.terminate()
                    child_stdout, child_stderr = child.communicate(timeout=5)
                if child.returncode not in {0, None}:
                    self.fail(
                        f"Popup harness failed: {child_stdout!r} {child_stderr!r}"
                    )

    def test_powershell_native_compile_result_and_clipboard_are_fail_closed(self) -> None:
        text = PS_PATH.read_text(encoding="utf-8")
        native = text[
            text.index("public static class MetafxMetaEditorCompileNative"):
            text.index("public static class MetafxMt5TabNative")
        ]
        parser = text[
            text.index("function Get-TrustedCompileSuccessRow"):
            text.index("function Find-CompileResult")
        ]
        result = text[
            text.index("function Find-CompileResult"):
            text.index("function Invoke-Compile")
        ]
        self.assertIn("SnapshotClipboard()", native)
        self.assertIn("Clipboard.SetDataObject(snapshot.Data, true)", native)
        self.assertIn("for (int attempt = 0; attempt < 100; attempt++)", native)
        self.assertIn("if (clipboardMutated) RestoreClipboard(original)", native)
        snapshot = native[
            native.index("static ClipboardSnapshot SnapshotClipboard"):
            native.index("static void RestoreClipboard")
        ]
        self.assertIn("bool clipboardObserved = false", snapshot)
        self.assertIn(
            "source = Clipboard.GetDataObject(); clipboardObserved = true; break;",
            snapshot,
        )
        self.assertLess(
            snapshot.index("if (!clipboardObserved) throw"),
            snapshot.index("if (source == null) return"),
        )
        copy = native[native.index("public static string CopyLastVisibleRow"):]
        self.assertLess(
            copy.index("SnapshotClipboard()"),
            copy.index("Message(root, WM_COMMAND, ID_EDIT_COPY"),
        )
        self.assertIn('AutomationIdProperty, "10047"', result)
        self.assertIn('AutomationIdProperty, "10065"', result)
        self.assertIn('[string]$tabNames[$index] -ceq "Errors"', result)
        self.assertLess(
            result.index('AutomationIdProperty, "10047"'),
            result.index('[MetafxMt5TabNative]::SelectExact($tabsHandle, "Errors")'),
        )
        self.assertLess(
            result.index('[MetafxMt5TabNative]::SelectExact($tabsHandle, "Errors")'),
            result.index('AutomationIdProperty, "10065"'),
        )
        self.assertIn(
            '[MetafxMt5VisibleNative]::GetParent($candidateHandle)', result
        )
        self.assertIn(
            '[MetafxMt5VisibleNative]::GetParent([IntPtr]$_.Current.NativeWindowHandle) -eq $toolboxHandle',
            result,
        )
        self.assertIn("CopyLastVisibleRow($rootHandle, $listHandle)", result)
        self.assertIn('$rawCopied.Split([char]"`t")', parser)
        self.assertIn("$fields.Count -ne 4", parser)
        self.assertIn(
            "-not [string]::IsNullOrWhiteSpace([string]$fields[1])", parser
        )
        self.assertIn(
            "-not [string]::IsNullOrWhiteSpace([string]$fields[2])", parser
        )
        self.assertIn(
            '([string]$fields[3]).Trim() -cne "0"',
            parser,
        )
        self.assertIn("$trustedSuccess = Get-TrustedCompileSuccessRow $rawCopied", result)
        self.assertIn(
            "if ($RequireSuccess -and $null -eq $trustedSuccess)", result
        )
        self.assertIn('GetBytes("$rowCount`n$rawCopied")', result)
        self.assertIn("0\\s+errors?,\\s*0\\s+warnings?", parser)

    def test_powershell_compile_success_parser_accepts_only_exact_native_summary(self) -> None:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        text = PS_PATH.read_text(encoding="utf-8")
        parser = text[
            text.index("function Get-TrustedCompileSuccessRow"):
            text.index("function Find-CompileResult")
        ]
        cases = [
            "0 errors, 0 warnings, 467 ms elapsed, cpu='AVX2 + FMA3'\t\t\t0\r\n",
            "0 errors, 0 warnings\t\t\t0\tunexpected\r\n",
            "0 errors, 0 warnings\tSmoke.mq5\t12\t0\r\n",
            "undeclared identifier\tSmoke.mq5\t12\t9\r\n",
        ]
        encoded_cases = [
            base64.b64encode(case.encode("utf-8")).decode("ascii")
            for case in cases
        ]
        harness = (
            parser
            + "\n$cases = @('"
            + "','".join(encoded_cases)
            + "')\n"
            + "$out = @($cases | ForEach-Object { "
            + "$row = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($_)); "
            + "$null -ne (Get-TrustedCompileSuccessRow $row) })\n"
            + "$out | ConvertTo-Json -Compress\n"
        )
        completed = subprocess.run(
            [powershell, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", "-"],
            input=harness,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout.strip()), [True, False, False, False])

    def test_powershell_compile_wait_binds_readiness_freshness_and_exact_failures(self) -> None:
        text = PS_PATH.read_text(encoding="utf-8")
        wait = text[
            text.index("function Wait-CompileResult"):
            text.index("function Invoke-Compile")
        ]
        invoke = text[
            text.index("function Invoke-Compile"):
            text.index("function Select-TabExact")
        ]

        self.assertIn("$observed = Find-CompileResult $Root $Editor $RequireSuccess", wait)
        self.assertIn(
            'catch [System.InvalidOperationException]',
            wait,
        )
        self.assertIn(
            'if ([string]$_.Exception.Message -cne "mt5_metaeditor_compile_result_unverified") { throw }',
            wait,
        )
        self.assertIn("[string]$observed.snapshotSha256 -cne $DifferentFromSha256", wait)
        self.assertIn(
            "if ([long]$observed.captureTimestampTicks -lt $deadlineTicks) { return $observed }",
            wait,
        )
        self.assertIn("$TimeoutCode -cnotmatch '^[a-z0-9_]{3,100}$'", wait)
        self.assertIn("$DifferentFromSha256 -cnotmatch '^[a-f0-9]{64}$'", wait)
        self.assertIn('Fail "mt5_metaeditor_compile_wait_contract_invalid"', wait)
        self.assertIn("Fail $TimeoutCode", wait)

        pre_wait = (
            '$compileBefore = Wait-CompileResult $editorWindow $editor $false $null 10 '
            '"mt5_metaeditor_compile_result_not_ready"'
        )
        post_wait = (
            '$compileAfter = Wait-CompileResult $editorWindow $editor $true '
            '([string]$compileBefore.snapshotSha256) 10 '
            '"mt5_metaeditor_compile_result_not_fresh"'
        )
        self.assertIn(pre_wait, invoke)
        self.assertIn(post_wait, invoke)
        self.assertLess(invoke.index(pre_wait), invoke.index("[System.IO.File]::Delete($binary)"))
        self.assertLess(
            invoke.index("mt5_compile_binary_not_fresh"),
            invoke.index(post_wait),
        )
        self.assertNotIn("$compileBefore = Find-CompileResult", invoke)
        self.assertNotIn("$compileAfter = Find-CompileResult", invoke)

        rebind = (
            "$editorBinding = Assert-MetaEditorSourceBindingUnchanged "
            "$editorBinding ([string]$Request.compilerPath) $source"
        )
        self.assertIn(rebind, invoke)
        self.assertLess(invoke.index(post_wait), invoke.index(rebind))
        self.assertLess(invoke.index(rebind), invoke.index("Capture-Window $editor"))

    def test_powershell_compile_post_f7_source_rebind_is_read_only_and_exact(self) -> None:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        text = PS_PATH.read_text(encoding="utf-8")
        helper = text[
            text.index("function Assert-MetaEditorSourceBindingUnchanged"):
            text.index("function Get-Or-StartMetaEditor")
        ]
        self.assertNotIn("Start-Process", helper)
        helper_b64 = base64.b64encode(helper.encode("utf-8")).decode("ascii")
        harness = rf"""
$ErrorActionPreference = 'Stop'
function Fail([string]$Code) {{ throw [System.InvalidOperationException]::new($Code) }}
$helperSource = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{helper_b64}'))
Invoke-Expression $helperSource
function New-Binding([int]$PidValue, [int64]$HandleValue) {{
    return [pscustomobject]@{{
        Process = [pscustomobject]@{{ Id = $PidValue }}
        Window = [pscustomobject]@{{ Current = [pscustomobject]@{{ NativeWindowHandle = $HandleValue }} }}
    }}
}}
$script:Mode = ''
function Find-MetaEditorSourceBinding([string]$CompilerPath, [string]$SourcePath) {{
    switch ($script:Mode) {{
        'same' {{ return New-Binding 101 202 }}
        'null' {{ return $null }}
        'pid' {{ return New-Binding 102 202 }}
        'hwnd' {{ return New-Binding 101 203 }}
        'ambiguous' {{ throw [System.InvalidOperationException]::new('mt5_metaeditor_source_window_ambiguous') }}
    }}
}}
$original = New-Binding 101 202
$out = [ordered]@{{}}
foreach ($mode in @('same', 'null', 'pid', 'hwnd', 'ambiguous')) {{
    $script:Mode = $mode
    try {{
        $value = Assert-MetaEditorSourceBindingUnchanged $original 'C:\MetaEditor64.exe' 'C:\Smoke.mq5'
        $out[$mode] = "ok:$($value.Process.Id):$($value.Window.Current.NativeWindowHandle)"
    }} catch {{
        $out[$mode] = [string]$_.Exception.Message
    }}
}}
$out | ConvertTo-Json -Compress
"""
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-EncodedCommand",
                base64.b64encode(harness.encode("utf-16le")).decode("ascii"),
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout.strip())
        self.assertEqual(result["same"], "ok:101:202")
        self.assertEqual(result["null"], "mt5_metaeditor_source_window_changed")
        self.assertEqual(result["pid"], "mt5_metaeditor_source_window_changed")
        self.assertEqual(result["hwnd"], "mt5_metaeditor_source_window_changed")
        self.assertEqual(
            result["ambiguous"], "mt5_metaeditor_source_window_ambiguous"
        )

    def test_powershell_compile_wait_retries_only_exact_transients_and_fails_closed(self) -> None:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        text = PS_PATH.read_text(encoding="utf-8")
        wait = text[
            text.index("function Wait-CompileResult"):
            text.index("function Invoke-Compile")
        ]
        wait_b64 = base64.b64encode(wait.encode("utf-8")).decode("ascii")
        harness = rf"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
function Fail([string]$Code) {{ throw [System.InvalidOperationException]::new($Code) }}
$waitSource = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{wait_b64}'))
Invoke-Expression $waitSource
$script:ProbeMode = ''
$script:ProbeCount = 0
$script:ObservedRequireSuccess = @()
$staleDigest = 'b' * 64
$freshDigest = 'c' * 64
function Find-CompileResult(
    [System.Windows.Automation.AutomationElement]$Root,
    [System.Diagnostics.Process]$Editor,
    [bool]$RequireSuccess
) {{
    $script:ProbeCount++
    $script:ObservedRequireSuccess += $RequireSuccess
    switch ($script:ProbeMode) {{
        'transient' {{
            if ($script:ProbeCount -lt 3) {{
                throw [System.InvalidOperationException]::new('mt5_metaeditor_compile_result_unverified')
            }}
            return [ordered]@{{ rowCount = 2; snapshotSha256 = ('a' * 64); resultLine = $null; captureTimestampTicks = [Diagnostics.Stopwatch]::GetTimestamp() }}
        }}
        'stale' {{
            if ($script:ProbeCount -lt 3) {{
                return [ordered]@{{ rowCount = 3; snapshotSha256 = $staleDigest; resultLine = '0 errors, 0 warnings'; captureTimestampTicks = [Diagnostics.Stopwatch]::GetTimestamp() }}
            }}
            return [ordered]@{{ rowCount = 3; snapshotSha256 = $freshDigest; resultLine = '0 errors, 0 warnings'; captureTimestampTicks = [Diagnostics.Stopwatch]::GetTimestamp() }}
        }}
        'nonretryable' {{
            throw [System.InvalidOperationException]::new('mt5_metaeditor_control_owner_changed')
        }}
        'timeout' {{
            throw [System.InvalidOperationException]::new('mt5_metaeditor_compile_result_unverified')
        }}
        'late_success' {{
            Start-Sleep -Milliseconds 1200
            return [ordered]@{{ rowCount = 3; snapshotSha256 = $freshDigest; resultLine = '0 errors, 0 warnings'; captureTimestampTicks = [Diagnostics.Stopwatch]::GetTimestamp() }}
        }}
        default {{ throw [System.InvalidOperationException]::new('unexpected_probe_mode') }}
    }}
}}

$script:ProbeMode = 'transient'; $script:ProbeCount = 0; $script:ObservedRequireSuccess = @()
$transient = Wait-CompileResult $null $null $false $null 2 'mt5_metaeditor_compile_result_not_ready'
$transientCount = $script:ProbeCount
$transientRequireSuccess = @($script:ObservedRequireSuccess)

$script:ProbeMode = 'stale'; $script:ProbeCount = 0; $script:ObservedRequireSuccess = @()
$fresh = Wait-CompileResult $null $null $true $staleDigest 2 'mt5_metaeditor_compile_result_not_fresh'
$staleCount = $script:ProbeCount
$staleRequireSuccess = @($script:ObservedRequireSuccess)

$script:ProbeMode = 'nonretryable'; $script:ProbeCount = 0
$nonretryableCode = $null
try {{
    [void](Wait-CompileResult $null $null $false $null 2 'mt5_metaeditor_compile_result_not_ready')
}} catch {{
    $nonretryableCode = [string]$_.Exception.Message
}}
$nonretryableCount = $script:ProbeCount

$script:ProbeMode = 'timeout'; $script:ProbeCount = 0
$timeoutCode = $null
try {{
    [void](Wait-CompileResult $null $null $false $null 1 'mt5_metaeditor_compile_result_not_ready')
}} catch {{
    $timeoutCode = [string]$_.Exception.Message
}}
$timeoutCount = $script:ProbeCount

$script:ProbeMode = 'late_success'; $script:ProbeCount = 0
$lateSuccessCode = $null
try {{
    [void](Wait-CompileResult $null $null $true $staleDigest 1 'mt5_metaeditor_compile_result_not_fresh')
}} catch {{
    $lateSuccessCode = [string]$_.Exception.Message
}}
$lateSuccessCount = $script:ProbeCount

$script:ProbeCount = 0
$invalidTimeoutCode = $null
try {{
    [void](Wait-CompileResult $null $null $false $null 0 'mt5_metaeditor_compile_result_not_ready')
}} catch {{
    $invalidTimeoutCode = [string]$_.Exception.Message
}}
$invalidDigestCode = $null
try {{
    [void](Wait-CompileResult $null $null $false ('D' * 64) 1 'mt5_metaeditor_compile_result_not_ready')
}} catch {{
    $invalidDigestCode = [string]$_.Exception.Message
}}
$invalidCodeCode = $null
try {{
    [void](Wait-CompileResult $null $null $false $null 1 'MT5_METAEDITOR_COMPILE_RESULT_NOT_READY')
}} catch {{
    $invalidCodeCode = [string]$_.Exception.Message
}}

[ordered]@{{
    transientDigest = [string]$transient.snapshotSha256
    transientCount = [int]$transientCount
    transientRequireSuccess = @($transientRequireSuccess)
    freshDigest = [string]$fresh.snapshotSha256
    staleCount = [int]$staleCount
    staleRequireSuccess = @($staleRequireSuccess)
    nonretryableCode = $nonretryableCode
    nonretryableCount = [int]$nonretryableCount
    timeoutCode = $timeoutCode
    timeoutCount = [int]$timeoutCount
    lateSuccessCode = $lateSuccessCode
    lateSuccessCount = [int]$lateSuccessCount
    invalidTimeoutCode = $invalidTimeoutCode
    invalidDigestCode = $invalidDigestCode
    invalidCodeCode = $invalidCodeCode
    invalidContractProbeCount = [int]$script:ProbeCount
}} | ConvertTo-Json -Compress
"""
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-EncodedCommand",
                base64.b64encode(harness.encode("utf-16le")).decode("ascii"),
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(completed.stdout.strip(), completed.stderr)
        result = json.loads(completed.stdout.strip())
        self.assertEqual(result["transientDigest"], "a" * 64)
        self.assertEqual(result["transientCount"], 3)
        self.assertEqual(result["transientRequireSuccess"], [False, False, False])
        self.assertEqual(result["freshDigest"], "c" * 64)
        self.assertEqual(result["staleCount"], 3)
        self.assertEqual(result["staleRequireSuccess"], [True, True, True])
        self.assertEqual(
            result["nonretryableCode"],
            "mt5_metaeditor_control_owner_changed",
        )
        self.assertEqual(result["nonretryableCount"], 1)
        self.assertEqual(
            result["timeoutCode"],
            "mt5_metaeditor_compile_result_not_ready",
        )
        self.assertGreaterEqual(result["timeoutCount"], 2)
        self.assertEqual(
            result["lateSuccessCode"],
            "mt5_metaeditor_compile_result_not_fresh",
        )
        self.assertEqual(result["lateSuccessCount"], 1)
        self.assertEqual(
            result["invalidTimeoutCode"],
            "mt5_metaeditor_compile_wait_contract_invalid",
        )
        self.assertEqual(
            result["invalidDigestCode"],
            "mt5_metaeditor_compile_wait_contract_invalid",
        )
        self.assertEqual(
            result["invalidCodeCode"],
            "mt5_metaeditor_compile_wait_contract_invalid",
        )
        self.assertEqual(result["invalidContractProbeCount"], 0)

    def test_powershell_transport_recovers_completed_response_and_blocks_orphan_replay(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = root / "operation-ui.json"
            payload = {
                "action": "collect_optimization",
                "operationId": "ea-visible-" + ("a" * 24),
            }
            actual_response = root / "operation-ui-collect_optimization.json"
            actual_response.write_text(
                json.dumps(
                    {
                        "schemaVersion": mt5.POWERSHELL_RESULT_SCHEMA,
                        "ok": True,
                        "action": payload["action"],
                        "operationId": payload["operationId"],
                    }
                ),
                encoding="utf-8",
            )
            recovered = mt5._default_powershell_runner(
                payload, response_path=base, timeout_seconds=10
            )
            self.assertTrue(recovered["recoveredPowerShellResponse"])
            self.assertFalse(actual_response.exists())

            request_path = root / "operation-ui-collect_optimization-request.json"
            request_path.write_bytes(mt5._canonical_json(payload))
            with self.assertRaisesRegex(
                mt5.VisibleTerminalAdapterError,
                "visible_ui_request_in_flight_or_orphaned",
            ):
                mt5._default_powershell_runner(
                    payload, response_path=base, timeout_seconds=10
                )

    def test_streaming_optimization_verifier_validates_5001_complete_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "optimization.xml"
            report.write_text(
                optimization_spreadsheetml(
                    [
                        (number, number * 10, number * 10, number, number)
                        for number in range(1, 5_002)
                    ]
                ),
                encoding="utf-8",
            )
            context = optimization_verifier_context(
                root, report, start="1", step="1", stop="5001", mode="complete"
            )

            verified = mt5.verify_mt5_optimization_report(context)

            self.assertEqual(verified["optimizationPassCount"], 5_001)
            self.assertEqual(verified["optimizationReturnedPassCount"], 5_000)
            self.assertTrue(verified["optimizationRowsTruncated"])
            self.assertEqual(verified["optimizationResultRows"][0]["passNumber"], 1)
            self.assertEqual(
                verified["optimizationResultRows"][-1]["RiskPercent"], 5_000
            )

    def test_streaming_optimization_verifier_rejects_bad_row_after_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "optimization.xml"
            rows = [
                (number, number, number, number, number)
                for number in range(1, 5_001)
            ]
            rows.append((5_001, 5_001, 5_001, 5_001, 1))
            report.write_text(optimization_spreadsheetml(rows), encoding="utf-8")
            context = optimization_verifier_context(
                root,
                report,
                start="1",
                step="1",
                stop="5001",
                mode="fast_genetic",
            )

            with self.assertRaisesRegex(
                mt5.VisibleTerminalAdapterError,
                "mt5_optimization_result_duplicate_combination",
            ):
                mt5.verify_mt5_optimization_report(context)

    def test_streaming_optimization_verifier_uses_exact_decimal_grid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "optimization.xml"
            report.write_text(
                optimization_spreadsheetml(
                    [
                        (1, 1, 1, 1, "0.1000000000000000000000000000001"),
                        (2, 2, 2, 2, "0.2"),
                    ]
                ),
                encoding="utf-8",
            )
            context = optimization_verifier_context(
                root, report, start="0.1", step="0.1", stop="0.2"
            )

            with self.assertRaisesRegex(
                mt5.VisibleTerminalAdapterError,
                "mt5_optimization_result_range_mismatch",
            ):
                mt5.verify_mt5_optimization_report(context)

    def test_streaming_optimization_verifier_accepts_native_bool_and_enum_strings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bool_report = root / "bool.xml"
            bool_report.write_text(
                typed_optimization_spreadsheetml(
                    ["Pass", "Result", "Profit", "Trades", "UseGuard"],
                    [
                        [("Number", 1), ("Number", 10), ("Number", 10), ("Number", 1), ("String", "false")],
                        [("Number", 2), ("Number", 20), ("Number", 20), ("Number", 2), ("String", "true")],
                    ],
                ),
                encoding="utf-8",
            )
            bool_context = optimization_verifier_context(
                root,
                bool_report,
                start="0",
                step="1",
                stop="1",
                input_name="UseGuard",
                value_kind="bool",
                source_default="false",
            )
            self.assertEqual(
                mt5.verify_mt5_optimization_report(bool_context)[
                    "optimizationPassCount"
                ],
                2,
            )

            enum_report = root / "enum.xml"
            enum_report.write_text(
                typed_optimization_spreadsheetml(
                    ["Pass", "Result", "Profit", "Trades", "Mode"],
                    [
                        [("Number", 1), ("Number", 10), ("Number", 10), ("Number", 1), ("String", "0")],
                        [("Number", 2), ("Number", 20), ("Number", 20), ("Number", 2), ("String", "2")],
                    ],
                ),
                encoding="utf-8",
            )
            enum_context = optimization_verifier_context(
                root,
                enum_report,
                start="0",
                step="1",
                stop="2",
                input_name="Mode",
                value_kind="enum",
                source_default="1",
                enum_values=["0", "1", "2"],
            )
            self.assertEqual(
                mt5.verify_mt5_optimization_report(enum_context)[
                    "optimizationPassCount"
                ],
                2,
            )

    def test_streaming_optimization_verifier_rejects_typed_cells_outside_manifest_domain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "enum-invalid.xml"
            report.write_text(
                typed_optimization_spreadsheetml(
                    ["Pass", "Result", "Profit", "Trades", "Mode"],
                    [
                        [("Number", 1), ("Number", 10), ("Number", 10), ("Number", 1), ("String", "0")],
                        [("Number", 2), ("Number", 20), ("Number", 20), ("Number", 2), ("String", "3")],
                    ],
                ),
                encoding="utf-8",
            )
            context = optimization_verifier_context(
                root,
                report,
                start="0",
                step="1",
                stop="2",
                input_name="Mode",
                value_kind="enum",
                source_default="1",
                enum_values=["0", "1", "2"],
            )
            with self.assertRaisesRegex(
                mt5.VisibleTerminalAdapterError,
                "mt5_optimization_result_range_mismatch",
            ):
                mt5.verify_mt5_optimization_report(context)

    def test_all_symbols_market_watch_binds_native_symbol_universe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "all-symbols.xml"
            report.write_text(
                typed_optimization_spreadsheetml(
                    ["Pass", "Result", "Profit", "Trades", "Symbol", "RiskPercent"],
                    [
                        [("Number", 1), ("Number", 10), ("Number", 10), ("Number", 1), ("String", "GBPUSD"), ("Number", 1)],
                        [("Number", 2), ("Number", 20), ("Number", 20), ("Number", 2), ("String", "EURUSD"), ("Number", 1)],
                    ],
                ),
                encoding="utf-8",
            )
            context = optimization_verifier_context(
                root,
                report,
                start="0.5",
                step="0.5",
                stop="2",
                mode="all_symbols_market_watch",
                source_default="1",
            )
            verified = mt5.verify_mt5_optimization_report(context)
            universe = verified["optimizationSymbolUniverse"]
            self.assertEqual(universe["symbols"], ["EURUSD", "GBPUSD"])
            self.assertEqual(
                verified["optimizationSymbolUniverseDigest"],
                sha256_bytes(mt5._canonical_json(universe)),
            )

    def test_all_symbols_market_watch_fails_closed_without_exact_universe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missing_symbol_report = root / "missing-symbol.xml"
            missing_symbol_report.write_text(
                optimization_spreadsheetml(
                    [(1, 10, 10, 1, 1), (2, 20, 20, 2, 1)]
                ),
                encoding="utf-8",
            )
            missing_context = optimization_verifier_context(
                root,
                missing_symbol_report,
                start="0.5",
                step="0.5",
                stop="2",
                mode="all_symbols_market_watch",
                source_default="1",
            )
            with self.assertRaisesRegex(
                mt5.VisibleTerminalAdapterError,
                "mt5_optimization_symbol_universe_unverified",
            ):
                mt5.verify_mt5_optimization_report(missing_context)

            duplicate_report = root / "duplicate-symbol.xml"
            duplicate_report.write_text(
                typed_optimization_spreadsheetml(
                    ["Pass", "Result", "Profit", "Trades", "Symbol", "RiskPercent"],
                    [
                        [("Number", 1), ("Number", 10), ("Number", 10), ("Number", 1), ("String", "EURUSD"), ("Number", 1)],
                        [("Number", 2), ("Number", 20), ("Number", 20), ("Number", 2), ("String", "EURUSD"), ("Number", 1)],
                    ],
                ),
                encoding="utf-8",
            )
            duplicate_context = optimization_verifier_context(
                root,
                duplicate_report,
                start="0.5",
                step="0.5",
                stop="2",
                mode="all_symbols_market_watch",
                source_default="1",
            )
            with self.assertRaisesRegex(
                mt5.VisibleTerminalAdapterError,
                "mt5_optimization_result_duplicate_combination",
            ):
                mt5.verify_mt5_optimization_report(duplicate_context)

    def test_streaming_optimization_verifier_rejects_duplicate_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "optimization.xml"
            report.write_text(
                optimization_spreadsheetml(
                    [(1, 1, 1, 1, 1), (1, 2, 2, 2, 2)]
                ),
                encoding="utf-8",
            )
            context = optimization_verifier_context(
                root, report, start="1", step="1", stop="2"
            )

            with self.assertRaisesRegex(
                mt5.VisibleTerminalAdapterError,
                "mt5_optimization_result_duplicate_pass",
            ):
                mt5.verify_mt5_optimization_report(context)

    def test_streaming_optimization_verifier_accepts_prefixed_qnames(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "optimization.xml"
            report.write_text(
                optimization_spreadsheetml(
                    [(1, 10, 10, 1, 1), (2, 20, 20, 2, 2)],
                    prefixed=True,
                ),
                encoding="utf-8",
            )
            context = optimization_verifier_context(
                root, report, start="1", step="1", stop="2", mode="complete"
            )

            verified = mt5.verify_mt5_optimization_report(context)

            self.assertEqual(verified["optimizationPassCount"], 2)
            self.assertFalse(verified["optimizationRowsTruncated"])

    def test_streaming_optimization_verifier_accepts_native_empty_numeric_metric(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "optimization.xml"
            payload = optimization_spreadsheetml(
                [(1, 10, 10, 1, 1), (2, 20, 20, 2, 2)]
            )
            payload = payload.replace(
                '<Data ss:Type="Number">10</Data></Cell><Cell><Data ss:Type="Number">10</Data>',
                '<Data ss:Type="Number">10</Data></Cell><Cell><Data ss:Type="String"></Data>',
                1,
            )
            report.write_text(payload, encoding="utf-8")
            context = optimization_verifier_context(
                root, report, start="1", step="1", stop="2", mode="complete"
            )

            verified = mt5.verify_mt5_optimization_report(context)

            self.assertEqual(verified["optimizationPassCount"], 2)
            self.assertEqual(verified["optimizationResultRows"][0]["profit"], "")

    def test_streaming_optimization_verifier_rejects_nonempty_string_numeric_metric(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "optimization.xml"
            payload = optimization_spreadsheetml(
                [(1, 10, 10, 1, 1), (2, 20, 20, 2, 2)]
            )
            payload = payload.replace(
                '<Data ss:Type="Number">10</Data></Cell><Cell><Data ss:Type="Number">10</Data>',
                '<Data ss:Type="Number">10</Data></Cell><Cell><Data ss:Type="String">not-a-number</Data>',
                1,
            )
            report.write_text(payload, encoding="utf-8")
            context = optimization_verifier_context(
                root, report, start="1", step="1", stop="2", mode="complete"
            )

            with self.assertRaisesRegex(
                mt5.VisibleTerminalAdapterError,
                "mt5_optimization_result_row_invalid",
            ):
                mt5.verify_mt5_optimization_report(context)

    def test_complete_optimization_requires_every_grid_combination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "optimization.xml"
            report.write_text(
                optimization_spreadsheetml(
                    [(1, 10, 10, 1, 1), (2, 20, 20, 2, 2)]
                ),
                encoding="utf-8",
            )
            context = optimization_verifier_context(
                root, report, start="1", step="1", stop="3", mode="complete"
            )

            with self.assertRaisesRegex(
                mt5.VisibleTerminalAdapterError,
                "mt5_optimization_pass_count_invalid",
            ):
                mt5.verify_mt5_optimization_report(context)

    def test_optimization_grid_contract_is_capped_at_100000(self) -> None:
        grid, count = mt5._optimization_range_grid(
            {
                "ranges": [
                    {
                        "inputName": "RiskPercent",
                        "start": "1",
                        "step": "1",
                        "stop": "100000",
                    }
                ]
            }
        )
        self.assertEqual(count, 100_000)
        self.assertEqual(grid[0][-1], 100_000)
        with self.assertRaisesRegex(
            mt5.VisibleTerminalAdapterError,
            "mt5_optimization_range_lineage_invalid",
        ):
            mt5._optimization_range_grid(
                {
                    "ranges": [
                        {
                            "inputName": "RiskPercent",
                            "start": "1",
                            "step": "1",
                            "stop": "100001",
                        }
                    ]
                }
            )

    def test_streaming_optimization_verifier_rejects_bad_types_indices_and_size(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            valid = optimization_spreadsheetml(
                [(1, 10, 10, 1, 1), (2, 20, 20, 2, 2)]
            )
            corruptions = {
                "wrong_type": valid.replace(
                    '<Data ss:Type="Number">2</Data></Cell></Row></Table>',
                    '<Data ss:Type="String">2</Data></Cell></Row></Table>',
                    1,
                ),
                "sparse_index": valid.replace(
                    '<Row><Cell><Data ss:Type="Number">1</Data>',
                    '<Row><Cell ss:Index="1"><Data ss:Type="Number">1</Data>',
                    1,
                ),
                "overlength": optimization_spreadsheetml(
                    [(1, "1" * 513, 10, 1, 1), (2, 20, 20, 2, 2)]
                ),
                "trailing_element": valid + "<trailing />",
            }
            for name, payload in corruptions.items():
                with self.subTest(name=name):
                    report = root / f"{name}.xml"
                    report.write_text(payload, encoding="utf-8")
                    context = optimization_verifier_context(
                        root, report, start="1", step="1", stop="2"
                    )
                    with self.assertRaises(mt5.VisibleTerminalAdapterError):
                        mt5.verify_mt5_optimization_report(context)

    def test_streaming_optimization_verifier_rejects_formula_and_entities(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            valid = optimization_spreadsheetml(
                [(1, 10, 10, 1, 1), (2, 20, 20, 2, 2)]
            )
            formula_report = root / "formula.xml"
            formula_report.write_text(
                valid.replace(
                    '<Row><Cell><Data ss:Type="Number">1</Data>',
                    '<Row><Cell ss:Formula="=1"><Data ss:Type="Number">1</Data>',
                    1,
                ),
                encoding="utf-8",
            )
            entity_report = root / "entity.xml"
            entity_report.write_text(
                valid.replace(
                    '<Workbook ',
                    '<!DOCTYPE Workbook [<!ENTITY bad "1">]><Workbook ',
                    1,
                ),
                encoding="utf-8",
            )
            for report in (formula_report, entity_report):
                with self.subTest(report=report.name):
                    context = optimization_verifier_context(
                        root, report, start="1", step="1", stop="2"
                    )
                    with self.assertRaises(mt5.VisibleTerminalAdapterError):
                        mt5.verify_mt5_optimization_report(context)

    def test_optimization_cache_timestamp_lineage_accepts_reused_inode(self) -> None:
        dispatch = 50_000_000_000
        self.assertTrue(
            mt5._optimization_cache_timestamps_valid(
                cache_ctime_ns=dispatch - 46_700_000,
                cache_mtime_ns=dispatch + 15_300_000_000,
                dispatch_mtime_ns=dispatch,
            )
        )
        self.assertTrue(
            mt5._optimization_cache_timestamps_valid(
                cache_ctime_ns=dispatch - 86_400_000_000_000,
                cache_mtime_ns=dispatch + 1,
                dispatch_mtime_ns=dispatch,
            )
        )
        self.assertFalse(
            mt5._optimization_cache_timestamps_valid(
                cache_ctime_ns=dispatch - 1,
                cache_mtime_ns=dispatch - 1,
                dispatch_mtime_ns=dispatch,
            )
        )

    def test_powershell_optimization_cache_uses_post_dispatch_write_for_reused_inode(self) -> None:
        text = PS_PATH.read_text(encoding="utf-8")
        lineage = text[
            text.index("function Get-OptimizationCacheLineage"):
            text.index("function Get-OptimizationCacheLineageDigest")
        ]
        self.assertIn(
            "$candidate.item.LastWriteTimeUtc -lt $dispatchItem.LastWriteTimeUtc",
            lineage,
        )
        self.assertNotIn(
            "$candidate.item.CreationTimeUtc -lt $dispatchItem.LastWriteTimeUtc",
            lineage,
        )

    def test_powershell_report_command_candidates_stay_array_in_strict_mode(self) -> None:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")
        text = PS_PATH.read_text(encoding="utf-8")
        start = text.index("        $commands = @(\n", text.index("function Invoke-TesterResultsReportCommandExact"))
        end = text.index("        if ($commands.Count -ne 1)", start)
        filter_block = text[start:end]
        harness = """
Set-StrictMode -Version Latest
$ExpectedTabName = "Optimization Results"
$expectedCommandText = "Export to XML (MS Office Excel)"
[uint32]$expectedCommandId = 33543
$popupToken = [pscustomobject]@{ Items = @(
  [pscustomobject]@{ Text = $expectedCommandText; CommandId = [uint32]33543; IsEnabled = $true; IsSeparator = $false; HasSubmenu = $false },
  [pscustomobject]@{ Text = "Export Optimization Cache File"; CommandId = [uint32]33553; IsEnabled = $true; IsSeparator = $false; HasSubmenu = $false }
) }
""" + filter_block + "\n@($commands).Count\n"
        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-EncodedCommand",
                base64.b64encode(harness.encode("utf-16le")).decode("ascii"),
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "1")

    def test_optimization_cache_lineage_accepts_start_created_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data_path = Path(temporary) / "data"
            cache_root = data_path / "Tester" / "cache"
            cache_root.mkdir(parents=True)
            cache = cache_root / (
                "SampleEA.EURUSD.H1.20200101.20200102.00."
                + ("A" * 32)
                + ".opt"
            )
            embedded = "Experts\\Metafx\\SampleEA.ex5"
            payload = (
                "TesterOptCache\0SampleEA\0"
                + embedded
                + "\0EURUSD\0demo (hedging)\0USD\0RiskPercent\0"
            ).encode("utf-16-le")
            cache.write_bytes(payload + (b"\x00" * max(0, 1024 - len(payload))))
            cache_created = cache.stat().st_ctime_ns
            dispatch = Path(temporary) / "dispatch-confirmed.json"
            dispatch.write_text("{}", encoding="utf-8")
            dispatch_time = cache_created + 46_700_000
            os.utime(dispatch, ns=(dispatch_time, dispatch_time))
            cache_finished = dispatch_time + 15_300_000_000
            os.utime(cache, ns=(cache_finished, cache_finished))

            lineage = mt5._optimization_cache_lineage(
                data_path=data_path,
                expert_file_name="SampleEA.ex5",
                expert_ui_path="Metafx/SampleEA",
                deployed_expert_sha256="d" * 64,
                policy={
                    "symbol": "EURUSD",
                    "period": "H1",
                    "useDate": False,
                    "fromDate": None,
                    "toDate": None,
                },
                dispatch_path=dispatch,
            )

            self.assertEqual(lineage["relativePath"], cache.relative_to(data_path).as_posix())
            self.assertEqual(lineage["embeddedExpertPath"], embedded)

    def test_optimization_report_without_explicit_total_never_infers_displayed_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "optimization.xml"
            report.write_text(
                """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
                  xmlns:o="urn:schemas-microsoft-com:office:office"
                  xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
                <o:DocumentProperties><o:Title>SampleEA EURUSD,H1</o:Title>
                <o:Author>MetaQuotes Ltd.</o:Author><o:Company>MetaQuotes Ltd.</o:Company></o:DocumentProperties>
                <Worksheet ss:Name="Tester Optimizator Results"><Table>
                <Row><Cell><Data ss:Type="String">Pass</Data></Cell><Cell><Data ss:Type="String">Result</Data></Cell>
                <Cell><Data ss:Type="String">Profit</Data></Cell><Cell><Data ss:Type="String">Trades</Data></Cell>
                <Cell><Data ss:Type="String">RiskPercent</Data></Cell></Row>
                <Row><Cell><Data ss:Type="String">not-a-pass</Data></Cell><Cell><Data ss:Type="Number">1</Data></Cell>
                <Cell><Data ss:Type="Number">1</Data></Cell><Cell><Data ss:Type="Number">1</Data></Cell>
                <Cell><Data ss:Type="Number">1</Data></Cell></Row>
                <Row><Cell><Data ss:Type="String">still-not-a-pass</Data></Cell><Cell><Data ss:Type="Number">2</Data></Cell>
                <Cell><Data ss:Type="Number">2</Data></Cell><Cell><Data ss:Type="Number">1</Data></Cell>
                <Cell><Data ss:Type="Number">2</Data></Cell></Row>
                </Table></Worksheet></Workbook>""",
                encoding="utf-8",
            )
            set_path = root / "inputs.set"
            set_path.write_text("RiskPercent=1||1||1||2||Y\n", encoding="ascii")
            context = {
                "platform": "mt5",
                "optimizationReportPath": report,
                "resolvedTesterSettings": {
                    "expertFileName": "SampleEA.ex5",
                    "symbol": "EURUSD",
                    "period": "H1",
                },
                "optimizationIntent": {
                    "setPath": str(set_path),
                    "setDigest": sha256_bytes(set_path.read_bytes()),
                    "ranges": [{"inputName": "RiskPercent", "start": "1", "step": "1", "stop": "2", "enabled": True}],
                    "rangesDigest": "b" * 64,
                    "mode": "fast_genetic",
                },
            }
            with self.assertRaisesRegex(
                mt5.VisibleTerminalAdapterError,
                "mt5_optimization_result_row_invalid",
            ):
                mt5.verify_mt5_optimization_report(context)

    def test_optimization_report_rejects_single_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "optimization.xml"
            report.write_text(
                """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
                  xmlns:o="urn:schemas-microsoft-com:office:office"
                  xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
                <o:DocumentProperties><o:Title>SampleEA EURUSD,H1</o:Title>
                <o:Author>MetaQuotes Ltd.</o:Author><o:Company>MetaQuotes Ltd.</o:Company></o:DocumentProperties>
                <Worksheet ss:Name="Tester Optimizator Results"><Table>
                <Row><Cell><Data ss:Type="String">Pass</Data></Cell><Cell><Data ss:Type="String">Result</Data></Cell>
                <Cell><Data ss:Type="String">Profit</Data></Cell><Cell><Data ss:Type="String">Trades</Data></Cell>
                <Cell><Data ss:Type="String">RiskPercent</Data></Cell></Row>
                <Row><Cell><Data ss:Type="Number">1</Data></Cell><Cell><Data ss:Type="Number">1</Data></Cell>
                <Cell><Data ss:Type="Number">1</Data></Cell><Cell><Data ss:Type="Number">1</Data></Cell>
                <Cell><Data ss:Type="Number">1</Data></Cell></Row>
                </Table></Worksheet></Workbook>""",
                encoding="utf-8",
            )
            set_path = root / "inputs.set"
            set_path.write_text("RiskPercent=1||1||1||1||Y\n", encoding="ascii")
            context = {
                "platform": "mt5",
                "optimizationReportPath": report,
                "resolvedTesterSettings": {
                    "expertFileName": "SampleEA.ex5",
                    "symbol": "EURUSD",
                    "period": "H1",
                },
                "optimizationIntent": {
                    "setPath": str(set_path),
                    "setDigest": sha256_bytes(set_path.read_bytes()),
                    "ranges": [{"inputName": "RiskPercent", "start": "1", "step": "1", "stop": "1", "enabled": True}],
                    "rangesDigest": "b" * 64,
                    "mode": "fast_genetic",
                },
            }
            with self.assertRaisesRegex(
                mt5.VisibleTerminalAdapterError,
                "mt5_optimization_pass_count_invalid",
            ):
                mt5.verify_mt5_optimization_report(context)


if __name__ == "__main__":
    unittest.main()
