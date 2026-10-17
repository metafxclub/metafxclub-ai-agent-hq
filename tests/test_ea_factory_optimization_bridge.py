from __future__ import annotations

import copy
import hashlib
import importlib.util
import http.client
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_ea_factory_optimization_bridge",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeSessionService:
    def __init__(self, session: dict) -> None:
        self.session = session
        self.created_with = None
        self.cancelled = []
        self.cancel_options = []

    def create(self, request: dict) -> dict:
        self.created_with = request
        return dict(self.session)

    def read(self, session_id: str) -> dict:
        if session_id != self.session["id"]:
            raise AssertionError(session_id)
        return dict(self.session)

    def cancel(self, session_id: str, **options) -> dict:
        self.cancelled.append(session_id)
        self.cancel_options.append(options)
        return dict(self.session)


class EaFactoryOptimizationBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        # Optimization Lab is a separate MT5 workflow, but it is still MT
        # work and therefore enters these focused tests with both top-header
        # platform locks already established.  The global-lock behavior itself
        # is covered by the dedicated global MetaTrader test module.
        def locked_context(platform: object) -> dict:
            normalized = str(platform or "").strip().lower()
            return {
                "record": {
                    "candidateId": f"mtc-{normalized}-selected",
                    "platform": normalized,
                },
                "token": {
                    "candidateId": f"mtc-{normalized}-selected",
                    "selectionRevision": 1,
                    "platform": normalized,
                },
            }

        patcher = mock.patch.object(
            self.bridge,
            "_ea_factory_require_top_header_locks",
            side_effect=locked_context,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def browser_payload(self, **overrides) -> dict:
        payload = {
            "buildId": "ea-build-mt5-verified",
            "idempotencyKey": "eaopt-idempotency-0001",
            "platform": "MT5",
            "symbol": "XAUUSD",
            "timeframe": "H1",
            "dateRange": {"from": "2025-01-01", "to": "2025-12-31"},
            "validation": {"method": "single_verified_run"},
            "roundCount": 1,
            "riskThresholds": {
                "targetProfitPercent": 10.0,
                "maxDrawdownPercent": 20.0,
                "minimumTrades": 25,
            },
            "ranges": [
                {
                    "name": "RiskMode",
                    "kind": "categorical",
                    "start": None,
                    "step": None,
                    "stop": None,
                    "values": [0, 1, 2],
                },
                {
                    "name": "StopLossPoints",
                    "kind": "numeric",
                    "start": 100,
                    "step": 50,
                    "stop": 300,
                    "values": [],
                },
            ],
        }
        payload.update(overrides)
        return payload

    @staticmethod
    def request(port: int, method: str, path: str, payload: dict | None = None):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if body is not None else {}
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        decoded = json.loads(response.read().decode("utf-8"))
        status = response.status
        connection.close()
        return status, decoded

    @staticmethod
    def build_context() -> dict:
        return {
            "build": {"id": "ea-build-mt5-verified"},
            "sourceDigest": "a" * 64,
            "sourceBytes": (
                b"input int RiskMode = 0;\n"
                b"input int StopLossPoints = 300;\n"
                b"void OnTick() {}\n"
            ),
            "baseline": {"sha256": "b" * 64},
        }

    @staticmethod
    def terminal_binding() -> dict:
        return {
            "candidateId": "mtc-mt5-selected",
            "platform": "mt5",
            "selectionRevision": 7,
            "bindingDigest": "c" * 64,
            "terminalRef": "mtterm_" + "d" * 24,
        }

    @staticmethod
    def one_click_optimization_session(
        *,
        session_id: str,
        state: str,
        progress_percent: float = 100.0,
        replayed: bool = False,
    ) -> dict:
        return {
            "id": session_id,
            "buildId": "ea-build-mt5-verified",
            "requestDigest": "d" * 64,
            "sourceDigest": "a" * 64,
            "baselineReportSha256": "b" * 64,
            "state": state,
            "stage": (
                "optimization_completed"
                if state == "completed"
                else "optimization_failed"
                if state == "failed"
                else "optimization_cancelled"
                if state == "cancelled"
                else "running_round"
            ),
            "progress": {"percent": progress_percent},
            "replayed": replayed,
        }

    def late_recovery_owner_fixture(
        self,
        suffix: str,
        *,
        started_at: str,
        run_status: str = "failed",
        prepared: bool = False,
    ) -> tuple[dict, dict, dict]:
        build_id = f"ea-build-late-{suffix}"
        run_id = "ea-run-" + suffix * 24
        session_id = "opts_" + suffix * 32
        session_state = "collecting" if prepared else "failed"
        session = {
            "id": session_id,
            "buildId": build_id,
            "requestDigest": suffix * 64,
            "sourceDigest": ("a" if suffix != "a" else "b") * 64,
            "baselineReportSha256": ("c" if suffix != "c" else "d") * 64,
            "state": session_state,
            "stage": "run_round",
            "progress": {"percent": 0.0},
            "recovery": {
                "lateCompletedResultRecoveryAvailable": not prepared,
                "lateCompletedResultRecoveryPending": prepared,
                "receiptPresent": True,
                "adapterCallInFlight": False,
            },
        }
        handoff = {
            "schemaVersion": self.bridge.EA_FACTORY_ONE_CLICK_OPTIMIZATION_HANDOFF_SCHEMA_VERSION,
            "sessionId": session_id,
            "buildId": build_id,
            "runId": run_id,
            "requestDigest": session["requestDigest"],
            "sourceDigest": session["sourceDigest"],
            "baselineReportSha256": session["baselineReportSha256"],
            "state": "failed",
            "stage": "run_round",
            "progressPercent": 0.0,
            "boundAt": "2026-10-16T00:00:00Z",
            "updatedAt": "2026-10-16T00:00:00Z",
        }
        run = {
            "schemaVersion": self.bridge.EA_FACTORY_ONE_CLICK_SCHEMA_VERSION,
            "runId": run_id,
            "idempotencyKey": f"late-recovery-{suffix}-001",
            "requestDigest": "f" * 64,
            "status": run_status,
            "currentStageId": None,
            "terminalBinding": self.terminal_binding(),
            "failureCode": "one_click_optimization_failed",
            "messageTh": "legacy discarded completion",
            "startedAt": started_at,
            "updatedAt": started_at,
            "completedAt": started_at if run_status == "failed" else None,
            "optimizationHandoff": handoff,
        }
        build = {
            "id": build_id,
            "platform": "mt5",
            "status": "completed",
            "oneClickRun": run,
            "stages": [],
        }
        return build, run, session

    def late_recovery_binding_fixture(self, session: dict) -> dict:
        ranges = [{
            "inputName": "StopLossPips",
            "start": "10",
            "step": "10",
            "stop": "20",
            "enabled": True,
            "sourceDefault": "30",
            "valueKind": "decimal",
        }]
        terminal = session["terminalBinding"]
        operation_id = session["recovery"]["operationId"]
        digest = lambda label: hashlib.sha256(label.encode("utf-8")).hexdigest()
        return {
            "type": "ea_factory.optimization.evidence_bound",
            "sessionId": session["id"],
            "operationId": operation_id,
            "roundId": session["round"]["id"],
            "buildId": session["buildId"],
            "sourceDigest": session["sourceDigest"],
            "baselineReportSha256": session["baselineReportSha256"],
            "baselineVisualBacktestSha256": digest("baseline-visual"),
            "compiledBinarySha256": digest("compiled-binary"),
            "inputManifestDigest": digest("input-manifest"),
            "optimizationSetRefDigest": digest("optimization-set-ref"),
            "optimizationExpectedReadbackEntriesDigest": digest(
                "optimization-readback-entries"
            ),
            "optimizationRanges": ranges,
            "optimizationRangesDigest": self.bridge._ea_factory_optimization_json_sha256(
                ranges
            ),
            "optimizationSymbolUniverse": None,
            "optimizationSymbolUniverseDigest": None,
            "baselinePresetRefDigest": digest("baseline-preset-ref"),
            "baselineExpectedReadbackEntriesDigest": digest(
                "baseline-readback-entries"
            ),
            "compiledDeploymentRef": "mt5deploy_" + "1" * 24,
            "compiledDeploymentDigest": digest("deployment"),
            "terminalCandidateId": terminal["candidateId"],
            "terminalSelectionRevision": terminal["selectionRevision"],
            "terminalBindingDigest": terminal["bindingDigest"],
            "settingsScreenshotSha256": digest("settings-shot"),
            "resultsScreenshotSha256": digest("results-shot"),
            "testerReportProofSha256": digest("tester-report-proof"),
            "optimizationCompletionCheckpointSha256": digest(
                "completion-checkpoint"
            ),
            "baselineReadbackSha256": digest("baseline-readback"),
            "baselineReadbackEntriesDigest": digest("baseline-entries"),
            "optimizationReadbackSha256": digest("optimization-readback"),
            "optimizationReportRef": "optreport_" + "2" * 24,
            "optimizationReportSha256": digest("optimization-report"),
            "optimizationReportByteSize": 4096,
            "adapterReceiptRef": "optmanifest_" + "3" * 24,
            "adapterReceiptSha256": digest("adapter-receipt"),
            "adapterReceiptByteSize": 1024,
            "testerSettingsSha256": self.bridge._ea_factory_optimization_json_sha256(
                session["testerSettings"]
            ),
            "visibleEvidenceSha256": digest("visible-evidence"),
            "liveTrading": False,
            "testShutdownTerminal": False,
        }

    def late_completed_publication_fixture(
        self,
    ) -> tuple[dict, dict, dict, dict]:
        session_id = "opts_" + "e" * 32
        base_mission_id, base_report_id = (
            self.bridge._ea_factory_optimization_terminal_report_ids(session_id)
        )
        result_rows = [
            {"pass": pass_number, "trades": 10 + pass_number}
            for pass_number in range(1, 5)
        ]
        ranges = [
            {
                "inputName": "StopLossPips",
                "start": "10",
                "step": "10",
                "stop": "20",
                "enabled": True,
                "sourceDefault": "30",
                "valueKind": "decimal",
            },
            {
                "inputName": "TakeProfitPips",
                "start": "20",
                "step": "20",
                "stop": "40",
                "enabled": True,
                "sourceDefault": "60",
                "valueKind": "decimal",
            },
        ]
        session = {
            "schemaVersion": 1,
            "id": session_id,
            "state": "completed",
            "stage": "complete",
            "buildId": "ea-build-mt5-verified",
            "sourceDigest": "a" * 64,
            "baselineReportSha256": "b" * 64,
            "platform": "mt5",
            "terminalBinding": self.terminal_binding(),
            "requestDigest": "d" * 64,
            "riskThresholds": {
                "targetProfitPercent": 10.0,
                "maxDrawdownPercent": 20.0,
                "minimumTrades": 25,
            },
            "round": {
                "index": 0,
                "number": 1,
                "count": 1,
                "id": "round-01",
                "combinationCount": 4,
            },
            "testerSettings": {
                "symbol": "XAUUSD",
                "period": "H1",
                "model": "every_tick",
                "useDate": True,
                "fromDate": "2025-01-01",
                "toDate": "2025-12-31",
                "optimizationMode": "fast_genetic",
                "criterion": "balance_max",
            },
            "progress": {
                "roundNumber": 1,
                "roundCount": 1,
                "passCount": 4,
                "returnedPassCount": 4,
                "percent": 100.0,
                "rowsTruncated": False,
            },
            "recovery": {
                "startBoundaryCommitted": True,
                "receiptPresent": True,
                "lateCompletedResultRecovered": True,
                "lateCompletedResultRecoveryProof": "completed_late_discarded",
                "lateCompletedResultRecoveryFailureCode": (
                    "session_deadline_exceeded"
                ),
            },
            "failure": None,
            "evidence": [{
                "roundId": "round-01",
                "roundNumber": 1,
                "combinationCount": 4,
                "passCount": 4,
                "returnedPassCount": 4,
                "rowsTruncated": False,
                "publicResultRowsTruncated": False,
                "analyzed": True,
                "resultRows": result_rows,
                "resultRowsSha256": "9" * 64,
                "warnings": [],
                "evidenceDocumentSha256": "e" * 64,
                "report": {
                    "ref": "optreport_" + "1" * 24,
                    "sha256": "1" * 64,
                    "byteSize": 100,
                },
                "manifest": {
                    "ref": "optmanifest_" + "2" * 24,
                    "sha256": "2" * 64,
                    "byteSize": 200,
                },
                "testerSettingsSha256": "3" * 64,
                "visibleEvidenceSha256": "4" * 64,
            }],
        }
        binding = {
            "operationId": "op_" + "4" * 40,
            "compiledBinarySha256": "5" * 64,
            "baselineVisualBacktestSha256": "6" * 64,
            "settingsScreenshotSha256": "7" * 64,
            "resultsScreenshotSha256": "8" * 64,
            "optimizationReportRef": "optreport_" + "1" * 24,
            "optimizationReportSha256": "1" * 64,
            "optimizationReportByteSize": 100,
            "adapterReceiptRef": "optmanifest_" + "2" * 24,
            "adapterReceiptSha256": "2" * 64,
            "adapterReceiptByteSize": 200,
            "optimizationRanges": ranges,
        }
        base_report = {
            "id": base_report_id,
            "type": "ea_experiment_report",
            "linkedMissionId": base_mission_id,
            "status": "failed",
            "summary": "legacy completion was discarded after timeout",
            "metrics": {
                "optimizationSession": {
                    "id": session_id,
                    "state": "failed",
                    "requestDigest": session["requestDigest"],
                    "buildId": session["buildId"],
                    "sourceDigest": session["sourceDigest"],
                    "baselineReportSha256": session["baselineReportSha256"],
                    "terminalBinding": copy.deepcopy(session["terminalBinding"]),
                },
                "failure": {"code": "session_deadline_exceeded"},
                "execution": {"available": False},
            },
            "executionEvidence": {
                "sourceKind": "analysis_only",
                "mtExecutionVerified": False,
                "optimizationProofVerified": False,
            },
            "artifacts": [],
        }
        base_mission = (
            self.bridge._ea_factory_optimization_publication_mission_projection(
                {
                    "createdAt": "2026-10-15T23:59:00Z",
                    "updatedAt": "2026-10-15T23:59:30Z",
                },
                mission_id=base_mission_id,
                session_id=session_id,
                idempotency_key=f"eaopt-report:{session_id}",
                status="failed",
                result=base_report["summary"],
                report_ids=[base_report_id],
                completed_at="2026-10-15T23:59:30Z",
                staging_contract=None,
            )
        )
        self.assertIsInstance(base_mission, dict)
        return session, binding, base_report, base_mission

    def source_manifest(self, source: str) -> dict:
        return self.bridge._ea_factory_mt5_optimization_input_manifest({
            "sourceBytes": source.encode("utf-8"),
            "sourceDigest": "a" * 64,
        })

    def custom_ema_pips_context(
        self,
        *,
        stop_declaration: str = "input double StopLossPips = 30.0;",
        take_declaration: str = "input double TakeProfitPips = 60.0;",
        source_kind: str = "custom_operator",
        platform: str = "mt5",
        artifact_kind: str = "expert_advisor",
        exit_rules: str | None = None,
    ) -> tuple[dict, dict]:
        payload = {
            "platform": "mt5",
            "artifactKind": "expert_advisor",
            "systemName": "EMA 10/60 Closed-Bar Smoke EA",
            "systemOverview": (
                "Deterministic MT5 smoke strategy using EMA 10 and EMA 60 "
                "on the chart symbol and timeframe."
            ),
            "entryRules": (
                "On one new bar only, BUY when EMA(10) at closed bar 2 is "
                "less than or equal to EMA(60) and EMA(10) at closed bar 1 "
                "is greater than EMA(60). SELL on the exact inverse closed-bar crossover."
            ),
            "recoveryRules": (
                "No recovery, grid, martingale, averaging, pyramiding, or hedging."
            ),
            "exitRules": exit_rules or (
                "StopLossPips and TakeProfitPips are positive EA inputs. "
                "Close an existing position on the opposite confirmed crossover "
                "before opening the reverse direction."
            ),
            "moneyManagement": (
                "Use one normalized tester-safe fixed lot of 0.01 and never hold "
                "more than one position for this symbol and magic number."
            ),
            "orderExecution": (
                "Use market orders in Strategy Tester only after closed-bar confirmation; "
                "normalize price and broker stop distance and reject invalid orders safely."
            ),
            "displayRequirements": (
                "Show fast and slow EMA values plus BUY signals, SELL signals, "
                "BUY orders, SELL orders, and the latest execution result."
            ),
            "additionalNotes": (
                "The acceptance loop must compile, run a Visual backtest, verify "
                "entry markers against the crossover, save the Backtest report, "
                "and produce the final condition-match summary. Optimization is out of scope."
            ),
        }
        record = self.bridge._ea_factory_custom_source_record(payload)
        source = (
            f"{stop_declaration}\n"
            f"{take_declaration}\n"
            "void OnTick() {}\n"
        )
        source_bytes = source.encode("utf-8")
        source_digest = hashlib.sha256(source_bytes).hexdigest()
        source_record_digest = str(record["recordDigest"])
        source_record_id = str(record["sourceRecordId"])
        build_id = "ea-build-custom-ema-smoke"
        strategy_spec = {
            "schemaVersion": "ea-factory-strategy-spec-v3",
            "buildId": build_id,
            "sourceRecordId": source_record_id,
            "recordDigest": source_record_digest,
            "sourceKind": source_kind,
            "sourceKey": str(record["sourceKey"]),
            "core": copy.deepcopy(record["core"]),
            "artifactKind": artifact_kind,
            "targetPlatform": platform,
            "language": "mql5",
            "strategySchemaVersion": self.bridge.EA_STRATEGY_BRIEF_SCHEMA_VERSION,
            "strategyBrief": copy.deepcopy(record["strategyBrief"]),
            "strategyBriefDigest": str(record["strategyBriefDigest"]),
            "immutable": True,
        }
        context = {
            "build": {
                "id": build_id,
                "platform": platform,
                "artifactKind": artifact_kind,
                "sourceRecordId": source_record_id,
                "sourceRecordDigest": source_record_digest,
                "workspace": {"strategySpecDigest": "c" * 64},
            },
            "sourceBytes": source_bytes,
            "sourceDigest": source_digest,
            "strategySpecDigest": "c" * 64,
            "strategySpec": strategy_spec,
            "baseline": {"sha256": "b" * 64},
            "baselineTesterSettings": {
                "symbol": "EURUSD",
                "period": "H1",
                "model": "every_tick",
                "useDate": True,
                "fromDate": "2025-01-01",
                "toDate": "2025-12-31",
            },
        }
        manifest = self.bridge._ea_factory_mt5_optimization_input_manifest(context)
        return context, manifest

    def test_browser_intent_maps_one_real_round_using_backend_bindings(self) -> None:
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_build_context",
                return_value=self.build_context(),
            ) as resolve_build,
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_terminal_binding",
                return_value=self.terminal_binding(),
            ) as resolve_terminal,
        ):
            result = self.bridge._ea_factory_optimization_create_request(
                self.browser_payload()
            )

        resolve_build.assert_called_once_with("ea-build-mt5-verified")
        resolve_terminal.assert_called_once_with()
        self.assertEqual(result["platform"], "mt5")
        self.assertEqual(result["sourceDigest"], "a" * 64)
        self.assertEqual(result["baselineReportSha256"], "b" * 64)
        self.assertEqual(result["terminalCandidateId"], "mtc-mt5-selected")
        self.assertEqual(result["terminalSelectionRevision"], 7)
        self.assertEqual(result["terminalBindingDigest"], "c" * 64)
        self.assertEqual(
            result["riskThresholds"],
            self.browser_payload()["riskThresholds"],
        )
        self.assertEqual(result["testerSettings"]["period"], "H1")
        self.assertEqual(len(result["rounds"]), 1)
        self.assertEqual(result["rounds"][0]["ranges"][0], {
            "name": "RiskMode",
            "kind": "categorical",
            "values": [0, 1, 2],
        })

    def test_browser_intent_rejects_repeated_ranges_disguised_as_rounds(self) -> None:
        with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
            self.bridge._ea_factory_optimization_create_request(
                self.browser_payload(roundCount=3)
            )
        self.assertEqual(caught.exception.code, "adaptive_rounds_not_implemented")

    def test_browser_intent_rejects_unimplemented_validation_method(self) -> None:
        with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
            self.bridge._ea_factory_optimization_create_request(
                self.browser_payload(validation={"method": "walk_forward"})
            )
        self.assertEqual(caught.exception.code, "validation_method_not_supported")

    def test_browser_intent_preserves_explicit_null_risk_thresholds(self) -> None:
        thresholds = {
            "targetProfitPercent": None,
            "maxDrawdownPercent": None,
            "minimumTrades": None,
        }
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_build_context",
                return_value=self.build_context(),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_terminal_binding",
                return_value=self.terminal_binding(),
            ),
        ):
            result = self.bridge._ea_factory_optimization_create_request(
                self.browser_payload(riskThresholds=thresholds)
            )

        self.assertEqual(result["riskThresholds"], thresholds)
        self.assertIsNot(result["riskThresholds"], thresholds)

    def test_browser_intent_rejects_unknown_risk_threshold_field(self) -> None:
        thresholds = dict(self.browser_payload()["riskThresholds"])
        thresholds["profitFactor"] = 1.5
        with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
            self.bridge._ea_factory_optimization_create_request(
                self.browser_payload(riskThresholds=thresholds)
            )
        self.assertEqual(caught.exception.code, "invalid_request")

    def test_browser_intent_rejects_non_numeric_risk_thresholds(self) -> None:
        invalid_rows = (
            {"targetProfitPercent": "10"},
            {"targetProfitPercent": True},
            {"targetProfitPercent": float("nan")},
            {"targetProfitPercent": 1_000_000.01},
            {"maxDrawdownPercent": "20"},
            {"maxDrawdownPercent": False},
            {"maxDrawdownPercent": float("inf")},
            {"maxDrawdownPercent": 100.01},
            {"minimumTrades": "25"},
            {"minimumTrades": True},
            {"minimumTrades": 25.0},
            {"minimumTrades": 250_001},
        )
        for override in invalid_rows:
            with self.subTest(override=override):
                thresholds = {
                    **self.browser_payload()["riskThresholds"],
                    **override,
                }
                with self.assertRaises(
                    self.bridge.OptimizationDomainError
                ) as caught:
                    self.bridge._ea_factory_optimization_create_request(
                        self.browser_payload(riskThresholds=thresholds)
                    )
                self.assertEqual(caught.exception.code, "invalid_request")

    def test_categorical_mode_is_encoded_as_one_linear_mt5_range(self) -> None:
        converted = self.bridge._ea_factory_optimization_adapter_ranges({
            "ranges": [{"name": "Mode", "kind": "categorical", "values": [0, 1, 2]}]
        })
        self.assertEqual(converted, [{
            "inputName": "Mode",
            "start": "0",
            "step": "1",
            "stop": "2",
            "enabled": True,
        }])

    def test_non_linear_categorical_mode_fails_closed(self) -> None:
        with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
            self.bridge._ea_factory_optimization_adapter_ranges({
                "ranges": [{"name": "Mode", "kind": "categorical", "values": [0, 1, 3]}]
            })
        self.assertEqual(caught.exception.code, "categorical_range_not_linear")

    def test_eligibility_rejects_non_mt5_build_before_filesystem_resolution(self) -> None:
        build = {
            "id": "ea-build-mt4-not-eligible",
            "platform": "mt4",
            "artifactKind": "expert_advisor",
            "status": "completed",
            "coverageUpgradeRequired": False,
            "stages": [],
        }
        with mock.patch.object(
            self.bridge,
            "_load_ea_factory_state_unlocked",
            return_value={"builds": [build]},
        ):
            with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                self.bridge._ea_factory_optimization_build_context(build["id"])
        self.assertEqual(caught.exception.code, "build_not_eligible")

    def test_build_context_accepts_digest_bound_tester_simulation_overrides(self) -> None:
        build_id = "ea-build-mt5-simulated-baseline"
        report_id = "report-eaf-simulated-baseline"
        source_bytes = (
            b"input bool FundamentalCriteriaConfirmed = false;\n"
            b"input int StopLossPoints = 300;\n"
            b"void OnTick() {}\n"
        )
        source_digest = hashlib.sha256(source_bytes).hexdigest()
        binary = {
            "fileName": "VerifiedEA.ex5",
            "relativePath": "EA_Versions/VerifiedEA.ex5",
            "extension": ".ex5",
            "immutable": True,
            "sha256": "9" * 64,
        }
        baseline = {
            "stageId": "backtest_recheck",
            "artifactKind": "backtest_evidence",
            "extension": ".htm",
            "immutable": True,
            "sha256": "8" * 64,
        }
        stages = [
            {
                "id": stage_id,
                "status": "completed",
                "evidenceVerified": True,
                **({"reportId": report_id} if stage_id == "backtest_recheck" else {}),
            }
            for stage_id in self.bridge.EA_FACTORY_STAGE_IDS
        ]
        build = {
            "id": build_id,
            "platform": "mt5",
            "artifactKind": "expert_advisor",
            "status": "completed",
            "coverageUpgradeRequired": False,
            "stages": stages,
            "versions": [{
                "fileName": "VerifiedEA.mq5",
                "versionFile": "EA_Versions/VerifiedEA.mq5",
                "sourceDigest": source_digest,
            }],
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_dir = root / build_id
            versions_dir = build_dir / "EA_Versions"
            source_dir = build_dir / "Source"
            reports_dir = root / "reports"
            versions_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            reports_dir.mkdir(parents=True)
            (versions_dir / "VerifiedEA.mq5").write_bytes(source_bytes)
            strategy_spec_path = source_dir / "strategy-spec-v01.json"
            strategy_spec_path.write_text(
                json.dumps({"strategyBrief": {"systemName": "Verified"}}),
                encoding="utf-8",
            )
            strategy_spec_digest = hashlib.sha256(
                strategy_spec_path.read_bytes()
            ).hexdigest()
            build["workspace"] = {
                "strategySpecFile": "Source/strategy-spec-v01.json",
                "strategySpecDigest": strategy_spec_digest,
            }
            strategy_spec_artifact = {
                "stageId": "strategy_spec",
                "artifactKind": "strategy_spec",
                "relativePath": "Source/strategy-spec-v01.json",
                "fileName": "strategy-spec-v01.json",
                "extension": ".json",
                "sha256": strategy_spec_digest,
                "immutable": True,
            }
            revalidated_manifest = [strategy_spec_artifact, baseline]
            manifest = self.bridge._ea_factory_mt5_optimization_input_manifest({
                "sourceBytes": source_bytes,
                "sourceDigest": source_digest,
            })
            preset_unsigned = {
                "schemaVersion": self.bridge.EA_FACTORY_TESTER_INPUT_PRESET_SCHEMA_VERSION,
                "mode": "full_immutable_source_snapshot_with_explicit_simulation_assumptions",
                "scope": "mt5_strategy_tester_only",
                "sourceDigest": source_digest,
                "inputManifestDigest": manifest["manifestDigest"],
                "assumptions": [{
                    "inputName": "FundamentalCriteriaConfirmed",
                    "inputType": "bool",
                    "sourceDefault": False,
                    "testerValue": True,
                    "reasonCode": (
                        "simulate_external_fundamental_confirmation_"
                        "for_historical_test_only"
                    ),
                }, {
                    "inputName": "StopLossPoints",
                    "inputType": "int",
                    "sourceDefault": 300,
                    "testerValue": 300,
                    "reasonCode": (
                        "reset_to_immutable_source_default_to_prevent_stale_tester_state"
                    ),
                }],
                "liveSourceDefaultsPreserved": True,
                "visibleExpertPropertiesRequired": True,
                "readbackRequired": True,
                "liveTradingAllowed": False,
                "fullCertifiedInputSnapshot": True,
                "simulationInputNames": ["FundamentalCriteriaConfirmed"],
            }
            preset = {
                **preset_unsigned,
                "presetDigest": self.bridge._ea_factory_canonical_json_sha256(
                    preset_unsigned
                ),
            }
            fixed_overrides = self.bridge._ea_factory_mt5_tester_fixed_overrides(
                preset,
                source_digest=source_digest,
                manifest=manifest,
            )
            expected_entries = self.bridge._ea_factory_mt5_expected_set_entries(
                manifest,
                [],
                fixed_current_overrides=fixed_overrides,
            )
            expected_entries_digest = (
                self.bridge._ea_factory_optimization_json_sha256(expected_entries)
            )
            preset_set_sha256 = hashlib.sha256(
                self.bridge._ea_factory_mt5_set_payload(expected_entries)
            ).hexdigest()
            resolved_preset = {
                "schemaVersion": (
                    self.bridge.EA_FACTORY_RESOLVED_TESTER_INPUT_PRESET_SCHEMA_VERSION
                ),
                "presetDigest": preset["presetDigest"],
                "sourceDigest": source_digest,
                "mode": preset["mode"],
                "scope": preset["scope"],
                "readback": [
                    {**row, "observedValue": row["testerValue"]}
                    for row in preset["assumptions"]
                ],
                "visibleExpertProperties": True,
                "inputsTabSelected": True,
                "sourceDefaultsPreserved": True,
                "appliedOnlyToStrategyTester": True,
                "notAppliedToLiveChart": True,
                "readbackVerified": True,
            }
            resolved_settings = {
                "schemaVersion": (
                    self.bridge.EA_FACTORY_RESOLVED_TESTER_SETTINGS_SCHEMA_VERSION
                ),
                "expertFileName": binary["fileName"],
                "symbol": "EURUSD",
                "period": "H1",
                "model": "every_tick",
                "spread": "current",
                "useDate": True,
                "fromDate": "2026-01-01",
                "toDate": "2026-06-30",
                "deposit": 10_000,
                "visualMode": True,
                "optimizationEnabled": False,
                "shutdownTerminalAfterTest": False,
            }
            report = {
                "status": "ready",
                "metrics": {
                    "sourceDigest": source_digest,
                    "compiledBinarySha256": binary["sha256"],
                    "testerReportSha256": baseline["sha256"],
                    "optimizationEnabled": False,
                    "backtestVerified": True,
                    "resultScreenshotSha256": "7" * 64,
                    "testerInputPresetApplied": True,
                    "testerInputPresetReadbackVerified": True,
                    "testerInputPresetReportVerified": True,
                    "testerInputPresetDigest": preset["presetDigest"],
                    "testerInputManifestDigest": manifest["manifestDigest"],
                    "testerInputExpectedReadbackEntriesDigest": (
                        expected_entries_digest
                    ),
                    "testerInputReadbackEntriesDigest": expected_entries_digest,
                    "inputPresetSetSha256": preset_set_sha256,
                    "inputReadbackSetSha256": "6" * 64,
                    "resolvedTesterInputPreset": resolved_preset,
                    "resolvedTesterInputPresetDigest": self.bridge.payload_digest(
                        self.bridge.EA_FACTORY_RESOLVED_TESTER_INPUT_PRESET_SCHEMA_VERSION,
                        resolved_preset,
                    ),
                    "resolvedTesterSettings": resolved_settings,
                },
            }
            report_path = reports_dir / f"{report_id}.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")

            with (
                mock.patch.object(
                    self.bridge,
                    "_load_ea_factory_state_unlocked",
                    return_value={"builds": [build]},
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_build_directory",
                    return_value=build_dir,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_revalidated_artifact_manifest",
                    return_value=revalidated_manifest,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_backtest_binary",
                    return_value=binary,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_mt5_tester_input_preset",
                    return_value=preset,
                ),
                mock.patch.object(
                    self.bridge,
                    "RUNTIME_REPORTS_DIR",
                    reports_dir,
                ),
            ):
                context = self.bridge._ea_factory_optimization_build_context(build_id)
                self.assertEqual(
                    context["baselineExpectedReadbackEntriesDigest"],
                    expected_entries_digest,
                )
                self.assertEqual(
                    context["baselineInputPresetSetSha256"],
                    preset_set_sha256,
                )
                self.assertEqual(
                    context["strategySpecDigest"],
                    strategy_spec_digest,
                )

                revalidated_manifest[:] = [baseline]
                with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                    self.bridge._ea_factory_optimization_build_context(build_id)
                self.assertEqual(
                    caught.exception.code,
                    "immutable_strategy_spec_required",
                )
                revalidated_manifest[:] = [strategy_spec_artifact, baseline]

                report["metrics"]["testerInputExpectedReadbackEntriesDigest"] = (
                    "0" * 64
                )
                report_path.write_text(json.dumps(report), encoding="utf-8")
                with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                    self.bridge._ea_factory_optimization_build_context(build_id)
                self.assertEqual(
                    caught.exception.code,
                    "verified_baseline_settings_required",
                )

    def test_mt5_fixed_overrides_require_canonical_source_bound_preset(self) -> None:
        source = (
            "input bool ExternalCriteriaConfirmed = false;\n"
            "void OnTick(){ if(!ExternalCriteriaConfirmed) return; }\n"
        ).encode("utf-8")
        source_digest = hashlib.sha256(source).hexdigest()
        manifest = self.bridge._ea_factory_mt5_optimization_input_manifest({
            "sourceBytes": source,
            "sourceDigest": source_digest,
        })
        unsigned = {
            "schemaVersion": self.bridge.EA_FACTORY_TESTER_INPUT_PRESET_SCHEMA_VERSION,
            "mode": "full_immutable_source_snapshot_with_explicit_simulation_assumptions",
            "scope": "mt5_strategy_tester_only",
            "sourceDigest": source_digest,
            "inputManifestDigest": manifest["manifestDigest"],
            "assumptions": [{
                "inputName": "ExternalCriteriaConfirmed",
                "inputType": "bool",
                "sourceDefault": False,
                "testerValue": True,
                "reasonCode": "simulate_external_manual_confirmation_for_historical_test_only",
            }],
            "liveSourceDefaultsPreserved": True,
            "visibleExpertPropertiesRequired": True,
            "readbackRequired": True,
            "liveTradingAllowed": False,
            "fullCertifiedInputSnapshot": True,
            "simulationInputNames": ["ExternalCriteriaConfirmed"],
        }

        def signed(value: dict) -> dict:
            core = copy.deepcopy(value)
            core.pop("presetDigest", None)
            return {
                **core,
                "presetDigest": self.bridge._ea_factory_canonical_json_sha256(core),
            }

        preset = signed(unsigned)
        self.assertEqual(
            self.bridge._ea_factory_mt5_tester_fixed_overrides(
                preset,
                source_digest=source_digest,
                manifest=manifest,
            ),
            {"ExternalCriteriaConfirmed": "true"},
        )

        malformed = copy.deepcopy(unsigned)
        malformed["assumptions"] = [None]
        mismatched_source = copy.deepcopy(unsigned)
        mismatched_source["sourceDigest"] = "f" * 64
        mismatched_manifest = copy.deepcopy(unsigned)
        mismatched_manifest["inputManifestDigest"] = "e" * 64
        duplicate_names = copy.deepcopy(unsigned)
        duplicate_names["simulationInputNames"] = [
            "ExternalCriteriaConfirmed",
            "ExternalCriteriaConfirmed",
        ]
        unknown_field = copy.deepcopy(unsigned)
        unknown_field["unexpected"] = True
        invalid_cases = [
            signed(malformed),
            {**preset, "presetDigest": "0" * 64},
            signed(mismatched_source),
            signed(mismatched_manifest),
            signed(duplicate_names),
            signed(unknown_field),
        ]
        for invalid in invalid_cases:
            with self.subTest(invalid=invalid):
                with self.assertRaises(
                    self.bridge.OptimizationDomainError
                ) as caught:
                    self.bridge._ea_factory_mt5_tester_fixed_overrides(
                        invalid,
                        source_digest=source_digest,
                        manifest=manifest,
                    )
                self.assertEqual(
                    caught.exception.code, "tester_input_override_invalid"
                )

    def test_terminal_binding_requires_current_selected_running_mt5(self) -> None:
        context = {
            "record": {
                "platform": "mt5",
                "runningState": "platform_running_detected",
            }
        }
        target = {
            "candidateId": "mtc-mt5-selected",
            "selectionRevision": 7,
            "bindingDigest": "c" * 64,
        }
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_metaeditor_target_context",
                return_value=(context, target),
            ),
            mock.patch.object(
                self.bridge,
                "_metatrader_candidate_record_is_current",
                return_value=True,
            ),
        ):
            result = self.bridge._ea_factory_optimization_terminal_binding()

        self.assertEqual(result["platform"], "mt5")
        self.assertEqual(result["candidateId"], target["candidateId"])
        self.assertEqual(result["selectionRevision"], 7)
        self.assertRegex(result["terminalRef"], r"^mtterm_[0-9a-f]{24}$")

    def test_bridge_maps_service_round_to_safe_visible_mt5_adapter_request(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            (Path(temporary) / "Sets").mkdir()
            source_bytes = (
                b"input bool FundamentalCriteriaConfirmed = false;\n"
                b"input int StopLossPoints = 300;\n"
                b"void OnTick() { if(!FundamentalCriteriaConfirmed) return; }\n"
            )
            input_manifest = self.bridge._ea_factory_mt5_optimization_input_manifest({
                "sourceBytes": source_bytes,
                "sourceDigest": "a" * 64,
            })
            preset_unsigned = {
                "schemaVersion": self.bridge.EA_FACTORY_TESTER_INPUT_PRESET_SCHEMA_VERSION,
                "mode": "full_immutable_source_snapshot_with_explicit_simulation_assumptions",
                "scope": "mt5_strategy_tester_only",
                "sourceDigest": "a" * 64,
                "inputManifestDigest": input_manifest["manifestDigest"],
                "assumptions": [{
                    "inputName": "FundamentalCriteriaConfirmed",
                    "inputType": "bool",
                    "sourceDefault": False,
                    "testerValue": True,
                    "reasonCode": (
                        "simulate_external_fundamental_confirmation_"
                        "for_historical_test_only"
                    ),
                }, {
                    "inputName": "StopLossPoints",
                    "inputType": "int",
                    "sourceDefault": 300,
                    "testerValue": 300,
                    "reasonCode": (
                        "reset_to_immutable_source_default_to_prevent_stale_tester_state"
                    ),
                }],
                "liveSourceDefaultsPreserved": True,
                "visibleExpertPropertiesRequired": True,
                "readbackRequired": True,
                "liveTradingAllowed": False,
                "fullCertifiedInputSnapshot": True,
                "simulationInputNames": ["FundamentalCriteriaConfirmed"],
            }
            baseline_preset = {
                **preset_unsigned,
                "presetDigest": self.bridge._ea_factory_canonical_json_sha256(
                    preset_unsigned
                ),
            }
            build_context = {
                "build": {"id": "ea-build-mt5-verified"},
                "buildDir": Path(temporary),
                "version": {
                    "fileName": "VerifiedEA.mq5",
                    "versionFile": "EA_Versions/VerifiedEA.mq5",
                    "sourceDigest": "a" * 64,
                },
                "sourceDigest": "a" * 64,
                "sourceBytes": source_bytes,
                "baseline": {"sha256": "b" * 64},
                "baselineInputPreset": baseline_preset,
                "binary": {
                    "fileName": "VerifiedEA.ex5",
                    "relativePath": "EA_Versions/VerifiedEA.ex5",
                    "sha256": "9" * 64,
                },
            }
            service_request = {
                "action": "start_round",
                "sessionId": "opts_" + "1" * 32,
                "buildId": "ea-build-mt5-verified",
                "platform": "mt5",
                "sourceDigest": "a" * 64,
                "baselineReportSha256": "b" * 64,
                "terminalBinding": self.terminal_binding(),
                "operation": {
                    "operationId": "op_" + "2" * 32,
                    "boundaryDocumentSha256": "e" * 64,
                },
                "round": {
                    "roundId": "round_" + "3" * 32,
                    "ranges": [
                        {
                            "name": "StopLossPoints",
                            "kind": "numeric",
                            "start": "100",
                            "step": "50",
                            "stop": "300",
                        }
                    ],
                },
                "testerSettings": {
                    "symbol": "XAUUSD",
                    "period": "H1",
                    "model": "every_tick",
                    "useDate": True,
                    "fromDate": "2025-01-01",
                    "toDate": "2025-12-31",
                    "optimizationMode": "fast_genetic",
                    "criterion": "balance_max",
                },
                "safety": {
                    "startAllowed": True,
                    "startExactlyOnce": True,
                    "neverStart": False,
                    "liveTradingAllowed": False,
                    "closeTerminalAllowed": False,
                    "testShutdownTerminal": False,
                },
            }
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_build_context",
                    return_value=build_context,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_target_resolver",
                    return_value=self.terminal_binding(),
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_write_optimization_set",
                    return_value=("Sets/inputs.set", "f" * 64),
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_visible_adapter_target_resolver",
                    return_value={"terminalFile": "opaque"},
                ),
            ):
                _context, request = (
                    self.bridge._ea_factory_optimization_adapter_request(
                        service_request
                    )
                )

        self.assertEqual(request["platform"], "mt5")
        self.assertEqual(request["stageId"], "optimize")
        self.assertEqual(request["optimizationIntent"]["ranges"][0]["inputName"], "StopLossPoints")
        self.assertEqual(
            request["optimizationIntent"]["ranges"][0]["sourceDefault"],
            "300",
        )
        self.assertEqual(
            request["optimizationIntent"]["ranges"][0]["valueKind"],
            "integer",
        )
        self.assertTrue(request["optimizationIntent"]["startOnce"])
        self.assertTrue(request["optimizationIntent"]["visibleInputsRequired"])
        self.assertEqual(
            request["optimizationIntent"]["testerInputPreset"],
            build_context["baselineInputPreset"],
        )
        self.assertEqual(
            request["optimizationIntent"]["testerInputPreset"][
                "simulationInputNames"
            ],
            ["FundamentalCriteriaConfirmed"],
        )
        manifest = request["optimizationIntent"]["inputManifest"]
        self.assertEqual(
            request["optimizationIntent"]["inputManifestDigest"],
            manifest["manifestDigest"],
        )
        self.assertEqual(manifest["entries"][0]["ordinal"], 0)
        set_ref = request["optimizationIntent"]["setRef"]
        self.assertEqual(set_ref["relativePath"], "Sets/inputs.set")
        self.assertEqual(set_ref["sha256"], "f" * 64)
        self.assertEqual(set_ref["entryCount"], len(manifest["entries"]))
        self.assertEqual(
            set_ref["expectedReadbackEntriesDigest"],
            self.bridge._ea_factory_optimization_json_sha256(
                set_ref["expectedReadbackEntries"]
            ),
        )
        baseline_ref = request["optimizationIntent"]["baselinePresetRef"]
        self.assertTrue(
            all(not row["enabled"] for row in baseline_ref["expectedReadbackEntries"])
        )
        baseline_rows = {
            row["inputName"]: row
            for row in baseline_ref["expectedReadbackEntries"]
        }
        self.assertEqual(
            baseline_rows["FundamentalCriteriaConfirmed"]["current"],
            "true",
        )
        optimized_rows = {
            row["inputName"]: row
            for row in set_ref["expectedReadbackEntries"]
        }
        self.assertEqual(
            optimized_rows["FundamentalCriteriaConfirmed"]["current"],
            "true",
        )
        deployment = request["compiledDeployment"]
        self.assertEqual(deployment["sourceSha256"], "a" * 64)
        self.assertEqual(deployment["binarySha256"], "9" * 64)
        self.assertTrue(deployment["reuseRequired"])
        self.assertRegex(deployment["deploymentRef"], r"^mt5deploy_[0-9a-f]{24}$")
        self.assertFalse(request["testerSettings"]["shutdownTerminalAfterTest"])
        self.assertFalse(request["testerSettings"]["liveTradingAllowed"])
        self.assertFalse(request["safety"]["autoTradingMayBeToggled"])
        self.assertFalse(request["safety"]["terminalShutdownAllowed"])
        self.assertTrue(request["safety"]["optimizationAllowed"])
        self.assertEqual(request["safety"]["serviceAction"], "start_round")
        self.assertFalse(request["safety"]["neverStart"])

    def test_bridge_simulation_guard_is_active_ontick_and_pre_entry_only(self) -> None:
        name = "ExternalCriteriaConfirmed"

        def guarded(source: str) -> bool:
            masked = self.bridge._ea_factory_mask_mql_comments_and_strings(source)
            self.assertIsNotNone(masked)
            return self.bridge._ea_factory_guarded_tester_simulation(masked, name)

        self.assertTrue(guarded(
            "void OnTick()\n"
            "{\n"
            "  ManageExistingPositions();\n"
            "  if(!ExternalCriteriaConfirmed) return;\n"
            "  SubmitEntry();\n"
            "}\n"
        ))
        self.assertFalse(guarded(
            "void Hidden()\n"
            "{\n"
            "  if(!ExternalCriteriaConfirmed) return;\n"
            "}\n"
            "void OnTick(){}\n"
        ))
        self.assertFalse(guarded(
            "void OnTick()\n"
            "{\n"
            "  trade.Buy(0.1);\n"
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

    def test_bridge_binds_all_symbols_market_watch_universe_digest(self) -> None:
        universe = {
            "schemaVersion": "ea-factory-mt5-symbol-universe-v1",
            "source": "native_spreadsheetml_symbol_column",
            "symbols": ["EURUSD", "GBPUSD"],
        }
        digest = self.bridge._ea_factory_optimization_json_sha256(universe)
        validated = self.bridge._ea_factory_validate_mt5_symbol_universe(
            universe,
            digest,
            mode="all_symbols_market_watch",
            result_rows=[
                {"Symbol": "EURUSD", "passNumber": 1},
                {"Symbol": "GBPUSD", "passNumber": 2},
            ],
            complete_result_rows=True,
        )
        self.assertEqual(validated, universe)
        with self.assertRaisesRegex(
            self.bridge.OptimizationDomainError,
            "did not prove the Market Watch symbol universe",
        ):
            self.bridge._ea_factory_validate_mt5_symbol_universe(
                None,
                None,
                mode="all_symbols_market_watch",
            )
        with self.assertRaisesRegex(
            self.bridge.OptimizationDomainError,
            "unexpected Market Watch symbol-universe evidence",
        ):
            self.bridge._ea_factory_validate_mt5_symbol_universe(
                universe,
                digest,
                mode="fast_genetic",
            )

    def test_recovery_action_propagates_never_start_to_visible_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            (Path(temporary) / "Sets").mkdir()
            source_bytes = (
                b"input int StopLossPoints = 300;\n"
                b"void OnTick() {}\n"
            )
            input_manifest = self.bridge._ea_factory_mt5_optimization_input_manifest({
                "sourceBytes": source_bytes,
                "sourceDigest": "a" * 64,
            })
            preset_unsigned = {
                "schemaVersion": self.bridge.EA_FACTORY_TESTER_INPUT_PRESET_SCHEMA_VERSION,
                "mode": "full_immutable_source_default_snapshot",
                "scope": "mt5_strategy_tester_only",
                "sourceDigest": "a" * 64,
                "inputManifestDigest": input_manifest["manifestDigest"],
                "assumptions": [{
                    "inputName": "StopLossPoints",
                    "inputType": "int",
                    "sourceDefault": 300,
                    "testerValue": 300,
                    "reasonCode": (
                        "reset_to_immutable_source_default_to_prevent_stale_tester_state"
                    ),
                }],
                "liveSourceDefaultsPreserved": True,
                "visibleExpertPropertiesRequired": True,
                "readbackRequired": True,
                "liveTradingAllowed": False,
                "fullCertifiedInputSnapshot": True,
                "simulationInputNames": [],
            }
            baseline_preset = {
                **preset_unsigned,
                "presetDigest": self.bridge._ea_factory_canonical_json_sha256(
                    preset_unsigned
                ),
            }
            context = {
                "build": {"id": "ea-build-mt5-verified"},
                "buildDir": Path(temporary),
                "version": {
                    "fileName": "VerifiedEA.mq5",
                    "versionFile": "EA_Versions/VerifiedEA.mq5",
                    "sourceDigest": "a" * 64,
                },
                "sourceDigest": "a" * 64,
                "sourceBytes": source_bytes,
                "baseline": {"sha256": "b" * 64},
                "baselineInputPreset": baseline_preset,
                "binary": {
                    "fileName": "VerifiedEA.ex5",
                    "relativePath": "EA_Versions/VerifiedEA.ex5",
                    "sha256": "9" * 64,
                },
            }
            service_request = {
                "action": "recover_round",
                "sessionId": "opts_" + "1" * 32,
                "buildId": "ea-build-mt5-verified",
                "platform": "mt5",
                "sourceDigest": "a" * 64,
                "baselineReportSha256": "b" * 64,
                "terminalBinding": self.terminal_binding(),
                "operation": {
                    "operationId": "op_" + "2" * 32,
                    "boundaryDocumentSha256": "e" * 64,
                },
                "round": {
                    "roundId": "round_" + "3" * 32,
                    "ranges": [{
                        "name": "StopLossPoints",
                        "kind": "numeric",
                        "start": "100",
                        "step": "50",
                        "stop": "300",
                    }],
                },
                "testerSettings": {
                    "symbol": "XAUUSD",
                    "period": "H1",
                    "model": "every_tick",
                    "useDate": True,
                    "fromDate": "2025-01-01",
                    "toDate": "2025-12-31",
                    "optimizationMode": "fast_genetic",
                    "criterion": "balance_max",
                },
                "safety": {
                    "startAllowed": False,
                    "startExactlyOnce": True,
                    "neverStart": True,
                    "liveTradingAllowed": False,
                    "closeTerminalAllowed": False,
                    "testShutdownTerminal": False,
                },
            }
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_build_context",
                    return_value=context,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_target_resolver",
                    return_value=self.terminal_binding(),
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_write_optimization_set",
                    return_value=("Sets/inputs.set", "f" * 64),
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_visible_adapter_target_resolver",
                    return_value={"terminalFile": "opaque"},
                ),
            ):
                _context, request = self.bridge._ea_factory_optimization_adapter_request(
                    service_request
                )

        self.assertTrue(request["safety"]["neverStart"])
        self.assertEqual(request["safety"]["serviceAction"], "recover_round")

    def test_busy_visible_front_office_proves_start_was_not_pressed(self) -> None:
        acquired = self.bridge.EA_FACTORY_VISIBLE_FRONT_OFFICE_ACTION_LOCK.acquire(
            blocking=False
        )
        self.assertTrue(acquired)
        try:
            result = self.bridge._ea_factory_optimization_handler({
                "action": "start_round",
                "operation": {"operationId": "op_" + "a" * 32},
                "terminalBinding": self.terminal_binding(),
            })
        finally:
            self.bridge.EA_FACTORY_VISIBLE_FRONT_OFFICE_ACTION_LOCK.release()
        self.assertEqual(result["status"], "before_start_retryable")
        self.assertEqual(result["reasonCode"], "visible_front_office_busy")
        self.assertRegex(result["notStartedProofSha256"], r"^[0-9a-f]{64}$")

    def test_busy_recovery_never_claims_another_safe_start(self) -> None:
        acquired = self.bridge.EA_FACTORY_VISIBLE_FRONT_OFFICE_ACTION_LOCK.acquire(
            blocking=False
        )
        self.assertTrue(acquired)
        try:
            result = self.bridge._ea_factory_optimization_handler({
                "action": "recover_round",
                "operation": {"operationId": "op_" + "a" * 32},
            })
        finally:
            self.bridge.EA_FACTORY_VISIBLE_FRONT_OFFICE_ACTION_LOCK.release()
        self.assertEqual(result, {
            "status": "unknown",
            "reasonCode": "visible_front_office_busy",
        })

    def test_prestart_set_validation_failure_is_retryable_not_unknown(self) -> None:
        operation_id = "op_" + "a" * 32
        session_id = "opts_" + "b" * 32
        request = {
            "action": "start_round",
            "sessionId": session_id,
            "operation": {
                "operationId": operation_id,
                "boundaryDocumentSha256": "d" * 64,
            },
            "terminalBinding": self.terminal_binding(),
        }
        adapter_request = {
            "terminalBinding": self.terminal_binding(),
            "visibleOperation": {"operationId": operation_id},
            "resolvedTarget": {},
            "testerSettings": {},
        }
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_adapter_request",
                return_value=({}, adapter_request),
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                return_value={"ready": True},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_front_office_capability_ready",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER",
                side_effect=self.bridge.VisibleTerminalAdapterError(
                    "mt5_set_reference_invalid"
                ),
            ),
            mock.patch.object(self.bridge, "append_audit") as append_audit,
        ):
            result = self.bridge._ea_factory_optimization_handler(request)

        self.assertEqual(result["status"], "before_start_retryable")
        self.assertEqual(result["reasonCode"], "mt5_set_reference_invalid")
        self.assertRegex(result["notStartedProofSha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            append_audit.call_args.args[0]["type"],
            "ea_factory.optimization.adapter_not_started",
        )
        self.assertIn(
            "visible_ui_tester_request_validation_failed",
            self.bridge.EA_FACTORY_OPTIMIZATION_PRESTART_ADAPTER_FAILURE_CODES,
        )
        self.assertIn(
            "mt5_symbol_readback_mismatch",
            self.bridge.EA_FACTORY_OPTIMIZATION_PRESTART_ADAPTER_FAILURE_CODES,
        )

    def test_legacy_prestart_failure_can_be_reclassified_only_with_exact_audit(self) -> None:
        operation_id = "op_" + "a" * 32
        session_id = "opts_" + "b" * 32
        request = {
            "action": "recover_round",
            "sessionId": session_id,
            "operation": {
                "operationId": operation_id,
                "boundaryDocumentSha256": "d" * 64,
            },
            "terminalBinding": self.terminal_binding(),
        }
        adapter_request = {
            "terminalBinding": self.terminal_binding(),
            "visibleOperation": {"operationId": operation_id},
            "resolvedTarget": {},
            "testerSettings": {},
        }
        exact_audit = [
            {
                "type": "ea_factory.optimization.start_boundary_committed",
                "sessionId": session_id,
                "operationId": operation_id,
                "attempt": 1,
            },
            {
                "type": "ea_factory.optimization.handler_invocation_claimed",
                "sessionId": session_id,
                "operationId": operation_id,
                "action": "start_round",
            },
            {
                "type": "ea_factory.optimization.adapter_recovery_required",
                "sessionId": session_id,
                "operationId": operation_id,
                "reasonCode": "mt5_symbol_readback_mismatch",
            },
        ]
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_adapter_request",
                return_value=({}, adapter_request),
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                return_value={"ready": True},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_front_office_capability_ready",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER",
                side_effect=self.bridge.VisibleTerminalAdapterError(
                    "mt5_tester_recovery_state_uncertain"
                ),
            ),
            mock.patch.object(
                self.bridge, "tail_jsonl", return_value=exact_audit
            ),
            mock.patch.object(self.bridge, "append_audit") as append_audit,
        ):
            result = self.bridge._ea_factory_optimization_handler(request)

        self.assertEqual(result["status"], "not_started")
        self.assertEqual(result["reasonCode"], "mt5_symbol_readback_mismatch")
        self.assertRegex(result["notStartedProofSha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            append_audit.call_args.args[0]["type"],
            "ea_factory.optimization.adapter_prestart_reclassified",
        )
        self.assertTrue(
            append_audit.call_args.args[0]["nativeBoundaryAbsent"]
        )
        self.assertEqual(
            append_audit.call_args.args[0]["nativeBoundaryAbsenceReasonCode"],
            "mt5_tester_recovery_state_uncertain",
        )

        wrong_audit = copy.deepcopy(exact_audit)
        wrong_audit[-1]["operationId"] = "op_" + "c" * 32
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_adapter_request",
                return_value=({}, adapter_request),
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                return_value={"ready": True},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_front_office_capability_ready",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER",
                side_effect=self.bridge.VisibleTerminalAdapterError(
                    "mt5_tester_recovery_state_uncertain"
                ),
            ),
            mock.patch.object(
                self.bridge, "tail_jsonl", return_value=wrong_audit
            ),
            mock.patch.object(self.bridge, "append_audit") as append_audit,
        ):
            result = self.bridge._ea_factory_optimization_handler(request)

        self.assertEqual(result["status"], "unknown")
        self.assertEqual(
            result["reasonCode"], "mt5_tester_recovery_state_uncertain"
        )
        self.assertNotIn("notStartedProofSha256", result)
        self.assertEqual(
            append_audit.call_args.args[0]["type"],
            "ea_factory.optimization.adapter_recovery_required",
        )

        duplicate_failure = copy.deepcopy(exact_audit)
        duplicate_failure.append(copy.deepcopy(exact_audit[-1]))
        with mock.patch.object(
            self.bridge, "tail_jsonl", return_value=duplicate_failure
        ):
            self.assertIsNone(
                self.bridge._ea_factory_optimization_prior_prestart_failure(
                    session_id, operation_id
                )
            )

        prior_recovery_attempts = copy.deepcopy(exact_audit)
        for suffix in ("1", "2"):
            prior_recovery_attempts.extend([
                {
                    "type": "ea_factory.optimization.handler_invocation_claimed",
                    "sessionId": session_id,
                    "operationId": operation_id,
                    "action": "recover_round",
                    "invocationId": "invoke_" + suffix * 32,
                },
                {
                    "type": "ea_factory.optimization.adapter_recovery_required",
                    "sessionId": session_id,
                    "operationId": operation_id,
                    "reasonCode": "mt5_tester_recovery_state_uncertain",
                },
                {
                    "type": "ea_factory.optimization.receipt_recovery_pending",
                    "sessionId": session_id,
                    "operationId": operation_id,
                },
            ])
        with mock.patch.object(
            self.bridge, "tail_jsonl", return_value=prior_recovery_attempts
        ):
            self.assertEqual(
                self.bridge._ea_factory_optimization_prior_prestart_failure(
                    session_id, operation_id
                ),
                "mt5_symbol_readback_mismatch",
            )

        receipt_after_failure = copy.deepcopy(prior_recovery_attempts)
        receipt_after_failure[-1]["receiptRef"] = "receipt_" + "f" * 24
        with mock.patch.object(
            self.bridge, "tail_jsonl", return_value=receipt_after_failure
        ):
            self.assertIsNone(
                self.bridge._ea_factory_optimization_prior_prestart_failure(
                    session_id, operation_id
                )
            )

        wrong_action = copy.deepcopy(exact_audit)
        wrong_action[1]["action"] = "recover_round"
        with mock.patch.object(
            self.bridge, "tail_jsonl", return_value=wrong_action
        ):
            self.assertIsNone(
                self.bridge._ea_factory_optimization_prior_prestart_failure(
                    session_id, operation_id
                )
            )

        strict_mode_audit = copy.deepcopy(exact_audit)
        strict_mode_audit[-1]["reasonCode"] = (
            "visible_ui_tester_request_validation_line_5376_failed"
        )
        with mock.patch.object(
            self.bridge, "tail_jsonl", return_value=strict_mode_audit
        ):
            self.assertEqual(
                self.bridge._ea_factory_optimization_prior_prestart_failure(
                    session_id, operation_id
                ),
                "visible_ui_tester_request_validation_line_5376_failed",
            )

    def test_legacy_baseline_save_ambiguity_requires_exact_cancel_quarantine_trace(
        self,
    ) -> None:
        operation_id = "op_" + "a" * 32
        session_id = "opts_" + "b" * 32
        reason = (
            "mt5_optimization_baseline_save_command_not_verified_dispatch_ambiguous"
        )
        self.assertIn(
            reason,
            self.bridge.EA_FACTORY_OPTIMIZATION_LEGACY_PRESTART_MIGRATION_CODES,
        )
        self.assertNotIn(
            reason,
            self.bridge.EA_FACTORY_OPTIMIZATION_PRESTART_ADAPTER_FAILURE_CODES,
        )
        exact_audit = [
            {
                "type": "ea_factory.optimization.start_boundary_committed",
                "sessionId": session_id,
                "operationId": operation_id,
                "attempt": 1,
            },
            {
                "type": "ea_factory.optimization.handler_invocation_claimed",
                "sessionId": session_id,
                "operationId": operation_id,
                "action": "start_round",
                "invocationId": "invoke_" + "1" * 32,
            },
            {
                "type": "ea_factory.optimization.adapter_recovery_required",
                "sessionId": session_id,
                "operationId": operation_id,
                "reasonCode": reason,
            },
            {
                "type": "ea_factory.optimization.receipt_recovery_pending",
                "sessionId": session_id,
                "operationId": operation_id,
            },
            {
                "type": "ea_factory.optimization.execution_quarantine_started",
                "sessionId": session_id,
                "reasonCode": "session_heartbeat_timeout",
            },
            {
                "type": "ea_factory.optimization.cancel_requested",
                "sessionId": session_id,
                "reasonCode": "user_cancelled",
            },
            {
                "type": "ea_factory.optimization.execution_stop_proof_pending",
                "sessionId": session_id,
                "reasonCode": "terminal_process_still_running",
            },
            {
                "type": "ea_factory.optimization.handler_invocation_claimed",
                "sessionId": session_id,
                "operationId": operation_id,
                "action": "recover_round",
                "invocationId": "invoke_" + "2" * 32,
            },
            {
                "type": "ea_factory.optimization.adapter_recovery_required",
                "sessionId": session_id,
                "operationId": operation_id,
                "reasonCode": "mt5_tester_recovery_state_uncertain",
            },
            {
                "type": (
                    "ea_factory.optimization."
                    "execution_quarantine_recovery_pending"
                ),
                "sessionId": session_id,
                "operationId": operation_id,
            },
        ]
        with mock.patch.object(
            self.bridge, "tail_jsonl", return_value=exact_audit
        ):
            self.assertEqual(
                self.bridge._ea_factory_optimization_prior_prestart_failure(
                    session_id, operation_id
                ),
                reason,
            )

        after_restart_and_current_claim = copy.deepcopy(exact_audit)
        after_restart_and_current_claim.extend([
            {
                "type": "ea_factory.optimization.restart_recovered",
                "sessionId": session_id,
                "receiptRecoveryRequired": True,
            },
            {
                "type": "ea_factory.optimization.handler_invocation_claimed",
                "sessionId": session_id,
                "operationId": operation_id,
                "action": "recover_round",
                "invocationId": "invoke_" + "3" * 32,
            },
        ])
        with mock.patch.object(
            self.bridge,
            "tail_jsonl",
            return_value=after_restart_and_current_claim,
        ):
            self.assertEqual(
                self.bridge._ea_factory_optimization_prior_prestart_failure(
                    session_id, operation_id
                ),
                reason,
            )

        invalid_traces = {}
        wrong_quarantine_reason = copy.deepcopy(exact_audit)
        wrong_quarantine_reason[4]["reasonCode"] = "session_deadline_exceeded"
        invalid_traces["wrong quarantine reason"] = wrong_quarantine_reason
        wrong_cancel_reason = copy.deepcopy(exact_audit)
        wrong_cancel_reason[5]["reasonCode"] = "operator_cancelled"
        invalid_traces["wrong cancel reason"] = wrong_cancel_reason
        wrong_stop_reason = copy.deepcopy(exact_audit)
        wrong_stop_reason[6]["reasonCode"] = "execution_state_unknown"
        invalid_traces["wrong stop proof reason"] = wrong_stop_reason
        wrong_order = copy.deepcopy(exact_audit)
        wrong_order[4], wrong_order[5] = wrong_order[5], wrong_order[4]
        invalid_traces["wrong metadata order"] = wrong_order
        duplicate_cancel = copy.deepcopy(exact_audit)
        duplicate_cancel.insert(6, copy.deepcopy(duplicate_cancel[5]))
        invalid_traces["duplicate cancel"] = duplicate_cancel
        duplicate_recovery_pending = copy.deepcopy(exact_audit)
        duplicate_recovery_pending.append(
            copy.deepcopy(duplicate_recovery_pending[-1])
        )
        invalid_traces["duplicate recovery pending"] = duplicate_recovery_pending
        wrong_recovery_reason = copy.deepcopy(exact_audit)
        wrong_recovery_reason[8]["reasonCode"] = "tester_start_boundary_missing"
        invalid_traces["wrong recovery reason"] = wrong_recovery_reason
        receipt_after_failure = copy.deepcopy(exact_audit)
        receipt_after_failure[-1]["receiptRef"] = "receipt_" + "f" * 24
        invalid_traces["receipt after failure"] = receipt_after_failure
        unexpected_event = copy.deepcopy(exact_audit)
        unexpected_event.append({
            "type": "ea_factory.optimization.worker_paused",
            "sessionId": session_id,
        })
        invalid_traces["unexpected event"] = unexpected_event

        for label, audit in invalid_traces.items():
            with self.subTest(label=label), mock.patch.object(
                self.bridge, "tail_jsonl", return_value=audit
            ):
                self.assertIsNone(
                    self.bridge._ea_factory_optimization_prior_prestart_failure(
                        session_id, operation_id
                    )
                )

    def test_legacy_baseline_save_reclassification_requires_native_boundary_absence(
        self,
    ) -> None:
        operation_id = "op_" + "a" * 32
        session_id = "opts_" + "b" * 32
        reason = (
            "mt5_optimization_baseline_save_command_not_verified_dispatch_ambiguous"
        )
        request = {
            "action": "recover_round",
            "sessionId": session_id,
            "operation": {
                "operationId": operation_id,
                "boundaryDocumentSha256": "d" * 64,
            },
            "terminalBinding": self.terminal_binding(),
        }
        adapter_request = {
            "terminalBinding": self.terminal_binding(),
            "visibleOperation": {"operationId": operation_id},
            "resolvedTarget": {},
            "testerSettings": {},
        }
        exact_audit = [
            {
                "type": "ea_factory.optimization.start_boundary_committed",
                "sessionId": session_id,
                "operationId": operation_id,
                "attempt": 1,
            },
            {
                "type": "ea_factory.optimization.handler_invocation_claimed",
                "sessionId": session_id,
                "operationId": operation_id,
                "action": "start_round",
                "invocationId": "invoke_" + "1" * 32,
            },
            {
                "type": "ea_factory.optimization.adapter_recovery_required",
                "sessionId": session_id,
                "operationId": operation_id,
                "reasonCode": reason,
            },
            {
                "type": "ea_factory.optimization.receipt_recovery_pending",
                "sessionId": session_id,
                "operationId": operation_id,
            },
            {
                "type": "ea_factory.optimization.execution_quarantine_started",
                "sessionId": session_id,
                "reasonCode": "session_heartbeat_timeout",
            },
            {
                "type": "ea_factory.optimization.cancel_requested",
                "sessionId": session_id,
                "reasonCode": "user_cancelled",
            },
            {
                "type": "ea_factory.optimization.execution_stop_proof_pending",
                "sessionId": session_id,
                "reasonCode": "terminal_process_still_running",
            },
            {
                "type": "ea_factory.optimization.handler_invocation_claimed",
                "sessionId": session_id,
                "operationId": operation_id,
                "action": "recover_round",
                "invocationId": "invoke_" + "2" * 32,
            },
            {
                "type": "ea_factory.optimization.adapter_recovery_required",
                "sessionId": session_id,
                "operationId": operation_id,
                "reasonCode": "mt5_tester_recovery_state_uncertain",
            },
            {
                "type": (
                    "ea_factory.optimization."
                    "execution_quarantine_recovery_pending"
                ),
                "sessionId": session_id,
                "operationId": operation_id,
            },
        ]

        def run(recovery_reason: str):
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_adapter_request",
                    return_value=({}, adapter_request),
                ),
                mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                    return_value={"ready": True},
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_front_office_capability_ready",
                    return_value=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER",
                    side_effect=self.bridge.VisibleTerminalAdapterError(
                        recovery_reason
                    ),
                ),
                mock.patch.object(
                    self.bridge, "tail_jsonl", return_value=exact_audit
                ),
                mock.patch.object(self.bridge, "append_audit") as append_audit,
            ):
                result = self.bridge._ea_factory_optimization_handler(request)
            return result, append_audit.call_args.args[0]

        migrated, migrated_audit = run("mt5_tester_recovery_state_uncertain")
        self.assertEqual(migrated["status"], "not_started")
        self.assertEqual(migrated["reasonCode"], reason)
        self.assertEqual(
            migrated_audit["type"],
            "ea_factory.optimization.adapter_prestart_reclassified",
        )
        self.assertTrue(migrated_audit["nativeBoundaryAbsent"])

        still_unknown, unknown_audit = run("tester_start_boundary_missing")
        self.assertEqual(still_unknown, {
            "status": "unknown",
            "reasonCode": "tester_start_boundary_missing",
        })
        self.assertEqual(
            unknown_audit["type"],
            "ea_factory.optimization.adapter_recovery_required",
        )

    def test_baseline_load_preflight_menu_change_is_current_prestart_retryable(
        self,
    ) -> None:
        operation_id = "op_" + "a" * 32
        session_id = "opts_" + "b" * 32
        reason = (
            "mt5_optimization_baseline_load_command_not_verified_"
            "preflight_menu_changed"
        )
        self.assertIn(
            reason,
            self.bridge.EA_FACTORY_OPTIMIZATION_PRESTART_ADAPTER_FAILURE_CODES,
        )
        self.assertIn(
            reason,
            self.bridge.EA_FACTORY_OPTIMIZATION_LEGACY_PRESTART_MIGRATION_CODES,
        )
        request = {
            "action": "start_round",
            "sessionId": session_id,
            "operation": {
                "operationId": operation_id,
                "boundaryDocumentSha256": "d" * 64,
            },
            "terminalBinding": self.terminal_binding(),
        }
        adapter_request = {
            "terminalBinding": self.terminal_binding(),
            "visibleOperation": {"operationId": operation_id},
            "resolvedTarget": {},
            "testerSettings": {},
        }

        def run(adapter_reason: str):
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_adapter_request",
                    return_value=({}, adapter_request),
                ),
                mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                    return_value={"ready": True},
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_front_office_capability_ready",
                    return_value=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER",
                    side_effect=self.bridge.VisibleTerminalAdapterError(
                        adapter_reason
                    ),
                ),
                mock.patch.object(self.bridge, "append_audit") as append_audit,
            ):
                result = self.bridge._ea_factory_optimization_handler(request)
            return result, append_audit.call_args.args[0]

        retryable, retryable_audit = run(reason)
        self.assertEqual(retryable["status"], "before_start_retryable")
        self.assertEqual(retryable["reasonCode"], reason)
        self.assertRegex(retryable["notStartedProofSha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            retryable_audit["type"],
            "ea_factory.optimization.adapter_not_started",
        )

        near_match = reason + "_suffix"
        still_unknown, unknown_audit = run(near_match)
        self.assertEqual(still_unknown, {
            "status": "unknown",
            "reasonCode": near_match,
        })
        self.assertEqual(
            unknown_audit["type"],
            "ea_factory.optimization.adapter_recovery_required",
        )

    def test_baseline_load_command_failure_is_legacy_migration_only(
        self,
    ) -> None:
        operation_id = "op_" + "a" * 32
        session_id = "opts_" + "b" * 32
        reason = "mt5_optimization_baseline_load_command_not_verified"
        self.assertIn(
            reason,
            self.bridge.EA_FACTORY_OPTIMIZATION_LEGACY_PRESTART_MIGRATION_CODES,
        )
        self.assertNotIn(
            reason,
            self.bridge.EA_FACTORY_OPTIMIZATION_PRESTART_ADAPTER_FAILURE_CODES,
        )
        request = {
            "action": "start_round",
            "sessionId": session_id,
            "operation": {
                "operationId": operation_id,
                "boundaryDocumentSha256": "d" * 64,
            },
            "terminalBinding": self.terminal_binding(),
        }
        adapter_request = {
            "terminalBinding": self.terminal_binding(),
            "visibleOperation": {"operationId": operation_id},
            "resolvedTarget": {},
            "testerSettings": {},
        }

        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_adapter_request",
                return_value=({}, adapter_request),
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                return_value={"ready": True},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_front_office_capability_ready",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER",
                side_effect=self.bridge.VisibleTerminalAdapterError(reason),
            ),
            mock.patch.object(self.bridge, "append_audit") as append_audit,
        ):
            result = self.bridge._ea_factory_optimization_handler(request)

        self.assertEqual(result, {"status": "unknown", "reasonCode": reason})
        self.assertEqual(
            append_audit.call_args.args[0]["type"],
            "ea_factory.optimization.adapter_recovery_required",
        )

    def test_legacy_baseline_load_command_failure_uses_strict_tail_grammar(
        self,
    ) -> None:
        operation_id = "op_" + "a" * 32
        session_id = "opts_" + "b" * 32
        reason = "mt5_optimization_baseline_load_command_not_verified"
        restart = {
            "type": "ea_factory.optimization.restart_recovered",
            "sessionId": session_id,
            "receiptRecoveryRequired": True,
        }
        quarantine = {
            "type": "ea_factory.optimization.execution_quarantine_started",
            "sessionId": session_id,
            "reasonCode": "session_heartbeat_timeout",
        }
        current_claim = {
            "type": "ea_factory.optimization.handler_invocation_claimed",
            "sessionId": session_id,
            "operationId": operation_id,
            "action": "recover_round",
            "invocationId": "invoke_" + "2" * 32,
        }

        def audit(failure_reason: str, *tail: dict) -> list[dict]:
            return [
                {
                    "type": "ea_factory.optimization.start_boundary_committed",
                    "sessionId": session_id,
                    "operationId": operation_id,
                    "attempt": 1,
                },
                {
                    "type": "ea_factory.optimization.handler_invocation_claimed",
                    "sessionId": session_id,
                    "operationId": operation_id,
                    "action": "start_round",
                    "invocationId": "invoke_" + "1" * 32,
                },
                {
                    "type": "ea_factory.optimization.adapter_recovery_required",
                    "sessionId": session_id,
                    "operationId": operation_id,
                    "reasonCode": failure_reason,
                },
                {
                    "type": "ea_factory.optimization.receipt_recovery_pending",
                    "sessionId": session_id,
                    "operationId": operation_id,
                },
                *copy.deepcopy(tail),
            ]

        valid_traces = {
            "receipt only": audit(reason),
            "two restarts": audit(reason, restart, restart),
            "quarantine three restarts and claim": audit(
                reason,
                quarantine,
                restart,
                restart,
                restart,
                current_claim,
            ),
        }
        for label, events in valid_traces.items():
            with self.subTest(valid=label), mock.patch.object(
                self.bridge, "tail_jsonl", return_value=events
            ):
                self.assertEqual(
                    self.bridge._ea_factory_optimization_prior_prestart_failure(
                        session_id, operation_id
                    ),
                    reason,
                )

        invalid_traces = {
            "near match": audit(reason + "_suffix"),
            "four restarts": audit(
                reason, restart, restart, restart, restart
            ),
            "quarantine alone": audit(reason, quarantine),
            "restart then quarantine": audit(reason, restart, quarantine),
        }
        for label, events in invalid_traces.items():
            with self.subTest(invalid=label), mock.patch.object(
                self.bridge, "tail_jsonl", return_value=events
            ):
                self.assertIsNone(
                    self.bridge._ea_factory_optimization_prior_prestart_failure(
                        session_id, operation_id
                    )
                )

    def test_legacy_baseline_load_requires_exact_bounded_recovery_trace(
        self,
    ) -> None:
        operation_id = "op_" + "a" * 32
        session_id = "opts_" + "b" * 32
        reason = (
            "mt5_optimization_baseline_load_command_not_verified_"
            "preflight_menu_changed"
        )
        base_audit = [
            {
                "type": "ea_factory.optimization.start_boundary_committed",
                "sessionId": session_id,
                "operationId": operation_id,
                "attempt": 1,
            },
            {
                "type": "ea_factory.optimization.handler_invocation_claimed",
                "sessionId": session_id,
                "operationId": operation_id,
                "action": "start_round",
                "invocationId": "invoke_" + "1" * 32,
            },
            {
                "type": "ea_factory.optimization.adapter_recovery_required",
                "sessionId": session_id,
                "operationId": operation_id,
                "reasonCode": reason,
            },
            {
                "type": "ea_factory.optimization.receipt_recovery_pending",
                "sessionId": session_id,
                "operationId": operation_id,
            },
        ]
        restart = {
            "type": "ea_factory.optimization.restart_recovered",
            "sessionId": session_id,
            "receiptRecoveryRequired": True,
        }
        quarantine = {
            "type": "ea_factory.optimization.execution_quarantine_started",
            "sessionId": session_id,
            "reasonCode": "session_heartbeat_timeout",
        }
        current_claim = {
            "type": "ea_factory.optimization.handler_invocation_claimed",
            "sessionId": session_id,
            "operationId": operation_id,
            "action": "recover_round",
            "invocationId": "invoke_" + "2" * 32,
        }
        valid_traces = {
            "receipt only": base_audit,
            "restart": [*base_audit, restart],
            "current claim": [*base_audit, current_claim],
            "restart then current claim": [
                *base_audit,
                restart,
                current_claim,
            ],
            "two restarts": [
                *base_audit,
                restart,
                restart,
            ],
            "three restarts then current claim": [
                *base_audit,
                restart,
                restart,
                restart,
                current_claim,
            ],
            "quarantine restart pair": [
                *base_audit,
                quarantine,
                restart,
            ],
            "quarantine then two restarts": [
                *base_audit,
                quarantine,
                restart,
                restart,
            ],
            "quarantine then three restarts and current claim": [
                *base_audit,
                quarantine,
                restart,
                restart,
                restart,
                current_claim,
            ],
            "quarantine restart pair then current claim": [
                *base_audit,
                quarantine,
                restart,
                current_claim,
            ],
        }
        for label, audit in valid_traces.items():
            with self.subTest(valid=label), mock.patch.object(
                self.bridge, "tail_jsonl", return_value=audit
            ):
                self.assertEqual(
                    self.bridge._ea_factory_optimization_prior_prestart_failure(
                        session_id, operation_id
                    ),
                    reason,
                )

        invalid_traces = {}
        missing_receipt_pending = copy.deepcopy(base_audit[:-1])
        invalid_traces["missing receipt pending"] = missing_receipt_pending
        duplicate_receipt_pending = copy.deepcopy(base_audit)
        duplicate_receipt_pending.append(
            copy.deepcopy(duplicate_receipt_pending[-1])
        )
        invalid_traces["duplicate receipt pending"] = duplicate_receipt_pending
        four_restarts = [
            *copy.deepcopy(base_audit),
            copy.deepcopy(restart),
            copy.deepcopy(restart),
            copy.deepcopy(restart),
            copy.deepcopy(restart),
        ]
        invalid_traces["four restarts"] = four_restarts
        quarantine_without_restart = [
            *copy.deepcopy(base_audit),
            copy.deepcopy(quarantine),
        ]
        invalid_traces["quarantine without restart"] = quarantine_without_restart
        quarantine_then_claim = [
            *copy.deepcopy(base_audit),
            copy.deepcopy(quarantine),
            copy.deepcopy(current_claim),
        ]
        invalid_traces["quarantine then claim"] = quarantine_then_claim
        duplicate_quarantine = [
            *copy.deepcopy(base_audit),
            copy.deepcopy(quarantine),
            copy.deepcopy(quarantine),
            copy.deepcopy(restart),
        ]
        invalid_traces["duplicate quarantine"] = duplicate_quarantine
        restart_then_quarantine = [
            *copy.deepcopy(base_audit),
            copy.deepcopy(restart),
            copy.deepcopy(quarantine),
        ]
        invalid_traces["restart then quarantine"] = restart_then_quarantine
        wrong_quarantine_reason = [
            *copy.deepcopy(base_audit),
            {
                **copy.deepcopy(quarantine),
                "reasonCode": "session_deadline_exceeded",
            },
            copy.deepcopy(restart),
        ]
        invalid_traces["wrong quarantine reason"] = wrong_quarantine_reason
        for field, value in (
            ("operationId", operation_id),
            ("action", "recover_round"),
            ("receiptRecoveryRequired", True),
            ("receiptRef", "receipt_" + "e" * 24),
        ):
            invalid_traces[f"quarantine field {field}"] = [
                *copy.deepcopy(base_audit),
                {**copy.deepcopy(quarantine), field: value},
                copy.deepcopy(restart),
            ]
        restart_after_claim = [
            *copy.deepcopy(base_audit),
            copy.deepcopy(current_claim),
            copy.deepcopy(restart),
        ]
        invalid_traces["wrong order"] = restart_after_claim
        restart_after_trailing_claim = [
            *copy.deepcopy(base_audit),
            copy.deepcopy(restart),
            copy.deepcopy(current_claim),
            copy.deepcopy(restart),
        ]
        invalid_traces["restart after trailing claim"] = (
            restart_after_trailing_claim
        )
        invalid_restart_proof = [
            *copy.deepcopy(base_audit),
            {**copy.deepcopy(restart), "receiptRecoveryRequired": False},
        ]
        invalid_traces["restart recovery false"] = invalid_restart_proof
        for field, value in (
            ("operationId", None),
            ("reasonCode", ""),
            ("action", None),
            ("receiptRef", "receipt_" + "d" * 24),
        ):
            invalid_traces[f"second restart field {field}"] = [
                *copy.deepcopy(base_audit),
                copy.deepcopy(restart),
                {**copy.deepcopy(restart), field: value},
            ]
        receipt_reference = copy.deepcopy(base_audit)
        receipt_reference[-1]["receiptRef"] = "receipt_" + "f" * 24
        invalid_traces["receipt reference"] = receipt_reference
        wrong_receipt_reason = copy.deepcopy(base_audit)
        wrong_receipt_reason[-1]["reasonCode"] = reason
        invalid_traces["receipt reason"] = wrong_receipt_reason
        wrong_claim_action = [
            *copy.deepcopy(base_audit),
            {**copy.deepcopy(current_claim), "action": "collect_round"},
        ]
        invalid_traces["wrong current action"] = wrong_claim_action
        unrelated_event = copy.deepcopy(base_audit)
        unrelated_event.append({
            "type": "ea_factory.optimization.worker_paused",
            "sessionId": session_id,
        })
        invalid_traces["unrelated event"] = unrelated_event
        near_match = copy.deepcopy(base_audit)
        near_match[2]["reasonCode"] = reason + "_suffix"
        invalid_traces["near-match reason"] = near_match

        for label, audit in invalid_traces.items():
            with self.subTest(invalid=label), mock.patch.object(
                self.bridge, "tail_jsonl", return_value=audit
            ):
                self.assertIsNone(
                    self.bridge._ea_factory_optimization_prior_prestart_failure(
                        session_id, operation_id
                    )
                )

    def test_legacy_baseline_load_reclassification_requires_native_boundary_absence(
        self,
    ) -> None:
        operation_id = "op_" + "a" * 32
        session_id = "opts_" + "b" * 32
        reasons = (
            "mt5_optimization_baseline_load_command_not_verified_"
            "preflight_menu_changed",
            "mt5_optimization_baseline_load_command_not_verified",
        )
        request = {
            "action": "recover_round",
            "sessionId": session_id,
            "operation": {
                "operationId": operation_id,
                "boundaryDocumentSha256": "d" * 64,
            },
            "terminalBinding": self.terminal_binding(),
        }
        adapter_request = {
            "terminalBinding": self.terminal_binding(),
            "visibleOperation": {"operationId": operation_id},
            "resolvedTarget": {},
            "testerSettings": {},
        }
        exact_audit = [
            {
                "type": "ea_factory.optimization.start_boundary_committed",
                "sessionId": session_id,
                "operationId": operation_id,
                "attempt": 1,
            },
            {
                "type": "ea_factory.optimization.handler_invocation_claimed",
                "sessionId": session_id,
                "operationId": operation_id,
                "action": "start_round",
                "invocationId": "invoke_" + "1" * 32,
            },
            {
                "type": "ea_factory.optimization.adapter_recovery_required",
                "sessionId": session_id,
                "operationId": operation_id,
                "reasonCode": reasons[0],
            },
            {
                "type": "ea_factory.optimization.receipt_recovery_pending",
                "sessionId": session_id,
                "operationId": operation_id,
            },
        ]

        def run(legacy_reason: str, recovery_reason: str):
            audit = copy.deepcopy(exact_audit)
            audit[2]["reasonCode"] = legacy_reason
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_adapter_request",
                    return_value=({}, adapter_request),
                ),
                mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                    return_value={"ready": True},
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_front_office_capability_ready",
                    return_value=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER",
                    side_effect=self.bridge.VisibleTerminalAdapterError(
                        recovery_reason
                    ),
                ),
                mock.patch.object(
                    self.bridge, "tail_jsonl", return_value=audit
                ),
                mock.patch.object(self.bridge, "append_audit") as append_audit,
            ):
                result = self.bridge._ea_factory_optimization_handler(request)
            return result, append_audit.call_args.args[0]

        for reason in reasons:
            with self.subTest(reason=reason):
                migrated, migrated_audit = run(
                    reason, "mt5_tester_recovery_state_uncertain"
                )
                self.assertEqual(migrated["status"], "not_started")
                self.assertEqual(migrated["reasonCode"], reason)
                self.assertEqual(
                    migrated_audit["type"],
                    "ea_factory.optimization.adapter_prestart_reclassified",
                )
                self.assertTrue(migrated_audit["nativeBoundaryAbsent"])

                still_unknown, unknown_audit = run(
                    reason, "tester_start_boundary_missing"
                )
                self.assertEqual(still_unknown, {
                    "status": "unknown",
                    "reasonCode": "tester_start_boundary_missing",
                })
                self.assertEqual(
                    unknown_audit["type"],
                    "ea_factory.optimization.adapter_recovery_required",
                )

    def test_create_response_exposes_worker_admission(self) -> None:
        session = {
            "id": "opts_" + "1" * 32,
            "state": "queued",
            "recovery": {"adapterCallInFlight": False},
            "cancelRequested": False,
        }
        service = FakeSessionService(session)
        normalized = {"idempotencyKey": "eaopt-idempotency-0001"}
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_service",
                return_value=service,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_create_request",
                return_value=normalized,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_require_fresh_capability",
                return_value={"ready": True},
            ) as require_capability,
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_optimization_worker",
                return_value=True,
            ) as start_worker,
            mock.patch.object(
                self.bridge,
                "ea_factory_optimization_read_model",
                return_value={"ok": True, "eaOptimizationLab": {}},
            ),
        ):
            result = self.bridge.create_ea_factory_optimization_session({})

        self.assertIs(service.created_with, normalized)
        require_capability.assert_called_once_with(normalized)
        start_worker.assert_called_once_with(session["id"])
        self.assertTrue(result["workerStarted"])
        self.assertEqual(result["session"]["sessionId"], session["id"])

    def test_create_passes_validated_risk_thresholds_to_service_without_drop(self) -> None:
        thresholds = {
            "targetProfitPercent": 10,
            "maxDrawdownPercent": 12.5,
            "minimumTrades": None,
        }
        session = {
            "id": "opts_" + "7" * 32,
            "state": "completed",
            "recovery": {"adapterCallInFlight": False},
            "cancelRequested": False,
        }
        service = FakeSessionService(session)
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_service",
                return_value=service,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_build_context",
                return_value=self.build_context(),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_terminal_binding",
                return_value=self.terminal_binding(),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_require_fresh_capability",
                return_value={"ready": True},
            ),
            mock.patch.object(
                self.bridge,
                "ea_factory_optimization_read_model",
                return_value={"ok": True, "eaOptimizationLab": {}},
            ),
        ):
            result = self.bridge.create_ea_factory_optimization_session(
                self.browser_payload(riskThresholds=thresholds)
            )

        self.assertTrue(result["ok"])
        self.assertEqual(service.created_with["riskThresholds"], thresholds)
        self.assertIsInstance(
            service.created_with["riskThresholds"]["targetProfitPercent"],
            int,
        )

    def test_create_rejects_unavailable_capability_before_consuming_active_slot(self) -> None:
        session = {
            "id": "opts_" + "9" * 32,
            "state": "queued",
            "recovery": {"adapterCallInFlight": False},
            "cancelRequested": False,
        }
        service = FakeSessionService(session)
        binding = self.terminal_binding()
        normalized = {
            "idempotencyKey": "eaopt-idempotency-capability-unavailable",
            "platform": binding["platform"],
            "terminalCandidateId": binding["candidateId"],
            "terminalSelectionRevision": binding["selectionRevision"],
            "terminalBindingDigest": binding["bindingDigest"],
        }
        unavailable = {
            "ready": False,
            "reasonCode": "mt5_optimization_capability_not_ready",
            **{
                key: binding[key]
                for key in (
                    "candidateId",
                    "platform",
                    "selectionRevision",
                    "bindingDigest",
                )
            },
        }
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_service",
                return_value=service,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_create_request",
                return_value=normalized,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_capability_provider",
                return_value=unavailable,
            ) as probe,
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_optimization_worker",
            ) as start_worker,
        ):
            with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                self.bridge.create_ea_factory_optimization_session({})

        self.assertEqual(
            caught.exception.code,
            "mt5_optimization_capability_not_ready",
        )
        probe.assert_called_once_with({
            "terminalBinding": {
                "candidateId": binding["candidateId"],
                "platform": binding["platform"],
                "selectionRevision": binding["selectionRevision"],
                "bindingDigest": binding["bindingDigest"],
            }
        })
        self.assertIsNone(service.created_with)
        start_worker.assert_not_called()

    def test_read_model_admission_requires_live_capability_not_only_connected_callables(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = self.bridge.EaFactoryOptimizationService(
                Path(temporary) / "optimization",
                target_resolver=lambda expected: expected,
                capability_provider=lambda _request: {"ready": True},
                optimization_handler=lambda _request: {"status": "unknown"},
            )
            unavailable = {
                "ready": False,
                "reasonCode": "mt5_optimization_capability_not_ready",
                **{
                    key: self.terminal_binding()[key]
                    for key in (
                        "candidateId",
                        "platform",
                        "selectionRevision",
                        "bindingDigest",
                    )
                },
            }
            with (
                mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_OPTIMIZATION_SERVICE",
                    service,
                ),
                mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER",
                    lambda _request: {},
                ),
                mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                    lambda **_request: {},
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_front_office_supported_platforms",
                    return_value={"mt5"},
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_eligible_builds",
                    return_value=[{
                        "buildId": "ea-build-mt5-verified",
                        "platform": "MT5",
                        "eligible": True,
                    }],
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_terminal_binding",
                    return_value=self.terminal_binding(),
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_capability_provider",
                    return_value=unavailable,
                ) as probe,
            ):
                model = self.bridge.ea_factory_optimization_read_model()[
                    "eaOptimizationLab"
                ]

        self.assertTrue(model["visibleAdapterConnected"])
        self.assertFalse(model["canStart"])
        self.assertEqual(model["adapterStatus"], "not_ready")
        self.assertFalse(model["adapter"]["capabilityReady"])
        self.assertEqual(
            [issue["code"] for issue in model["admission"]["issues"]],
            ["mt5_optimization_capability_not_ready"],
        )
        probe.assert_called_once()

    def test_resume_accepts_frontend_idempotency_and_empty_contract_body(self) -> None:
        session = {
            "id": "opts_" + "2" * 32,
            "state": "awaiting_visible_terminal",
            "recovery": {"adapterCallInFlight": False},
            "cancelRequested": False,
        }
        service = FakeSessionService(session)
        for body in ({}, {"idempotencyKey": "eaopt-resume-0001"}):
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_service",
                    return_value=service,
                ),
                mock.patch.object(
                    self.bridge,
                    "_start_ea_factory_optimization_worker",
                    return_value=True,
                ),
            ):
                result = self.bridge.resume_ea_factory_optimization_session(
                    session["id"], body
                )
            self.assertTrue(result["workerStarted"])

    def test_resume_worker_attempts_receipt_recovery_for_awaiting_session(self) -> None:
        session_id = "opts_" + "8" * 32

        class RecoveryService:
            def __init__(self) -> None:
                self.resume_calls = []

            def read(self, requested_session_id: str) -> dict:
                self.assert_session(requested_session_id)
                return {"id": session_id, "state": "awaiting_visible_terminal"}

            def resume(self, requested_session_id: str) -> dict:
                self.assert_session(requested_session_id)
                self.resume_calls.append(requested_session_id)
                return {"id": session_id, "state": "awaiting_visible_terminal"}

            @staticmethod
            def assert_session(requested_session_id: str) -> None:
                if requested_session_id != session_id:
                    raise AssertionError(requested_session_id)

        service = RecoveryService()
        with mock.patch.object(
            self.bridge,
            "_ea_factory_optimization_service",
            return_value=service,
        ):
            self.bridge._ea_factory_optimization_worker(session_id)

        self.assertEqual(service.resume_calls, [session_id])

    def test_cancel_starts_receipt_recovery_without_closing_terminal(self) -> None:
        session = {
            "id": "opts_" + "3" * 32,
            "state": "awaiting_visible_terminal",
            "recovery": {
                "adapterCallInFlight": False,
                "receiptRecoveryRequired": True,
            },
            "cancelRequested": True,
        }
        service = FakeSessionService(session)
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_service",
                return_value=service,
            ),
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_optimization_worker",
                return_value=True,
            ) as start_worker,
        ):
            result = self.bridge.cancel_ea_factory_optimization_session(
                session["id"], {}
            )

        self.assertTrue(result["ok"])
        self.assertEqual(service.cancelled, [session["id"]])
        self.assertEqual(
            service.cancel_options,
            [{"confirm_execution_stopped": True}],
        )
        start_worker.assert_called_once_with(session["id"])

    def test_service_configuration_recovers_durable_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with (
                mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_OPTIMIZATION_ROOT",
                    Path(temporary) / "optimization",
                ),
                mock.patch.object(
                    self.bridge,
                    "_start_ea_factory_optimization_worker",
                    return_value=False,
                ),
            ):
                result = self.bridge.configure_ea_factory_optimization_service()

        self.assertEqual(
            result,
            {
                "configured": True,
                "recovered": 0,
                "resumed": 0,
                "reconciledPublications": 0,
            },
        )
        self.assertIsInstance(
            self.bridge.EA_FACTORY_OPTIMIZATION_SERVICE,
            self.bridge.EaFactoryOptimizationService,
        )

    def test_service_configuration_reconciles_owner_before_recovered_worker(self) -> None:
        session = self.one_click_optimization_session(
            session_id="opts_" + "4" * 32,
            state="queued",
            progress_percent=0.0,
        )
        service = mock.Mock()
        service.recover_after_restart.return_value = [session]
        service.list.return_value = [session]
        events = []

        with (
            mock.patch.object(
                self.bridge,
                "EaFactoryOptimizationService",
                return_value=service,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_recovered_optimization_start_allowed",
                side_effect=lambda recovered: (
                    events.append(("reconcile", recovered["id"])) or True
                ),
            ) as reconcile,
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_optimization_worker",
                side_effect=lambda session_id: (
                    events.append(("start", session_id)) or True
                ),
            ) as start_worker,
        ):
            result = self.bridge.configure_ea_factory_optimization_service()

        self.assertEqual(
            events,
            [("reconcile", session["id"]), ("start", session["id"])],
        )
        self.assertEqual(
            result,
            {
                "configured": True,
                "recovered": 1,
                "resumed": 1,
                "reconciledPublications": 0,
            },
        )
        reconcile.assert_called_once_with(session)
        start_worker.assert_called_once_with(session["id"])

    def test_startup_reconciles_completed_publication_from_service_list_without_start(
        self,
    ) -> None:
        completed = self.one_click_optimization_session(
            session_id="opts_" + "a" * 32,
            state="completed",
            progress_percent=100.0,
        )
        service = mock.Mock()
        # recover_after_restart intentionally returns only active sessions.
        service.recover_after_restart.return_value = []
        service.list.return_value = [completed]
        events: list[tuple[str, str]] = []

        with (
            mock.patch.object(
                self.bridge,
                "EaFactoryOptimizationService",
                return_value=service,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_publish_terminal_report",
                side_effect=lambda session: (
                    events.append(("publish", session["id"]))
                    or {
                        "state": "completed",
                        "missionId": "mission-fix2",
                        "reportId": "report-fix2",
                    }
                ),
            ) as publish,
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_optimization_worker",
            ) as start_worker,
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_handler",
            ) as native_handler,
        ):
            result = self.bridge.configure_ea_factory_optimization_service()

        self.assertEqual(events, [("publish", completed["id"])])
        self.assertEqual(
            result,
            {
                "configured": True,
                "recovered": 0,
                "resumed": 0,
                "reconciledPublications": 1,
            },
        )
        publish.assert_called_once_with(completed)
        start_worker.assert_not_called()
        native_handler.assert_not_called()

    def test_crash_window_replay_binds_owner_without_starting_worker(self) -> None:
        session = self.one_click_optimization_session(
            session_id="opts_" + "5" * 32,
            state="queued",
            progress_percent=0.0,
        )
        run = {
            "runId": "ea-run-" + "6" * 24,
            "status": "running",
            "currentStageId": None,
        }
        state = {
            "builds": [{
                "id": session["buildId"],
                "platform": "mt5",
                "status": "completed",
                "oneClickRun": run,
            }]
        }
        bound = {
            "sessionId": session["id"],
            "requestDigest": session["requestDigest"],
            "sourceDigest": session["sourceDigest"],
            "baselineReportSha256": session["baselineReportSha256"],
        }

        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_build_current_stage_id",
                return_value=None,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_auto_optimization_handoff",
                return_value=session,
            ) as replay,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_bound_optimization_handoff",
                return_value=bound,
            ),
        ):
            allowed = self.bridge._ea_factory_recovered_optimization_start_allowed(
                session
            )

        self.assertTrue(allowed)
        replay.assert_called_once_with(
            session["buildId"],
            run,
            start_worker=False,
        )

    def test_restart_never_resumes_legacy_factory_optimizer_cancellation(
        self,
    ) -> None:
        session = self.one_click_optimization_session(
            session_id="opts_" + "6" * 32,
            state="running",
            progress_percent=40.0,
        )
        run = {
            "runId": "ea-run-" + "9" * 24,
            "status": "cancelling",
            "currentStageId": None,
            "optimizationHandoff": {
                "sessionId": session["id"],
                "buildId": session["buildId"],
                "requestDigest": session["requestDigest"],
                "sourceDigest": session["sourceDigest"],
                "baselineReportSha256": session["baselineReportSha256"],
            },
        }
        build = {
            "id": session["buildId"],
            "platform": "mt5",
            "status": "completed",
            "oneClickRun": run,
        }
        state = {"builds": [build]}
        service = mock.Mock()
        service.recover_after_restart.return_value = [session]
        service.list.return_value = [session]

        with (
            mock.patch.object(
                self.bridge,
                "EaFactoryOptimizationService",
                return_value=service,
            ),
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_optimization_worker",
            ) as start_optimizer,
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_handler",
            ) as native_handler,
        ):
            configured = self.bridge.configure_ea_factory_optimization_service()

        self.assertEqual(
            configured,
            {
                "configured": True,
                "recovered": 1,
                "resumed": 0,
                "reconciledPublications": 0,
            },
        )
        start_optimizer.assert_not_called()
        native_handler.assert_not_called()

        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_ea_factory_build_current_stage_id",
                return_value=None,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_active_worker_payload",
                return_value={
                    "buildId": session["buildId"],
                    "activeOperation": "mt5_optimization",
                    "optimizationSessionId": session["id"],
                },
            ),
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_one_click_thread",
                return_value=True,
            ) as start_cancel_monitor,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            resumed = self.bridge.resume_interrupted_ea_factory_one_click_runs()

        self.assertEqual(resumed, 0)
        start_cancel_monitor.assert_not_called()

    def test_execution_identity_binds_original_path_pid_lifetime_and_window(self) -> None:
        binding = self.terminal_binding()
        executable_digest = hashlib.sha256(b"terminal64.exe bytes").hexdigest()
        path_digest = hashlib.sha256(
            b"c:/program files/metatrader 5/terminal64.exe"
        ).hexdigest()
        with mock.patch.object(
            self.bridge,
            "_ea_factory_windows_process_snapshot",
            return_value={
                "status": "running",
                "processId": 41001,
                "createdAt100ns": 133700000000000000,
                "executablePathDigest": path_digest,
                "executableSha256": executable_digest,
            },
        ):
            identity = self.bridge._ea_factory_optimization_execution_identity(
                {
                    "processId": 41001,
                    "windowHandle": 92001,
                    "executableSha256": executable_digest,
                },
                binding,
            )

        self.assertIsInstance(identity, dict)
        self.assertEqual(identity["terminalProcessId"], 41001)
        self.assertEqual(identity["terminalProcessCreatedAt100ns"], 133700000000000000)
        self.assertEqual(identity["terminalWindowHandle"], 92001)
        self.assertEqual(identity["terminalExecutablePathDigest"], path_digest)
        core = dict(identity)
        identity_digest = core.pop("identitySha256")
        self.assertEqual(
            identity_digest,
            self.bridge._ea_factory_optimization_json_sha256(core),
        )

    def test_capability_fails_closed_without_recoverable_execution_identity(self) -> None:
        binding = self.terminal_binding()
        raw_capability = {
            "terminalProcessProbe": {
                "processId": 41001,
                "windowHandle": 92001,
                "executableSha256": "a" * 64,
            }
        }
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_target_resolver",
                return_value=binding,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_visible_adapter_target_resolver",
                return_value={},
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                lambda **_request: raw_capability,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER",
                lambda _request: {},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_front_office_supported_platforms",
                return_value={"mt5"},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_front_office_capability_ready",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_execution_identity",
                return_value=None,
            ) as capture_identity,
        ):
            result = self.bridge._ea_factory_optimization_capability_provider({
                "terminalBinding": binding,
            })

        self.assertFalse(result["ready"])
        self.assertEqual(
            result["reasonCode"],
            "optimization_execution_identity_unavailable",
        )
        self.assertNotIn("executionIdentity", result)
        capture_identity.assert_called_once_with(
            raw_capability["terminalProcessProbe"],
            binding,
        )

    def test_stop_prover_never_releases_same_process_or_live_tester_agent(self) -> None:
        identity = {
            "terminalProcessId": 41001,
            "terminalProcessCreatedAt100ns": 133700000000000000,
            "terminalExecutablePathDigest": "a" * 64,
            "terminalExecutableSha256": "b" * 64,
            "identitySha256": "c" * 64,
        }
        request = {
            "sessionId": "opts_" + "1" * 32,
            "operationId": "op_" + "2" * 32,
            "executionIdentity": identity,
        }
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_windows_process_snapshot",
                return_value={
                    "status": "running",
                    "createdAt100ns": identity["terminalProcessCreatedAt100ns"],
                    "executablePathDigest": identity["terminalExecutablePathDigest"],
                    "executableSha256": identity["terminalExecutableSha256"],
                },
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_windows_tester_agent_snapshot",
            ) as tester_probe,
        ):
            same_process = self.bridge._ea_factory_optimization_execution_stop_prover(
                request
            )
        self.assertEqual(same_process["status"], "execution_still_running")
        tester_probe.assert_not_called()

        # An in-place executable update must never be misclassified as a
        # replacement while the original PID lifetime is still alive.
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_windows_process_snapshot",
                return_value={
                    "status": "running",
                    "createdAt100ns": identity["terminalProcessCreatedAt100ns"],
                    "executablePathDigest": "d" * 64,
                    "executableSha256": "e" * 64,
                },
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_windows_tester_agent_snapshot",
            ) as drift_tester_probe,
        ):
            identity_drift = (
                self.bridge._ea_factory_optimization_execution_stop_prover(request)
            )
        self.assertEqual(identity_drift["status"], "execution_still_running")
        self.assertEqual(
            identity_drift["reasonCode"], "terminal_process_identity_drift"
        )
        drift_tester_probe.assert_not_called()

        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_windows_process_snapshot",
                return_value={
                    "status": "running",
                    "createdAt100ns": identity["terminalProcessCreatedAt100ns"] + 1,
                    "executablePathDigest": "d" * 64,
                    "executableSha256": identity["terminalExecutableSha256"],
                },
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_windows_tester_agent_snapshot",
                return_value={
                    "status": "running",
                    "reasonCode": "tester_process_still_running",
                    "count": 1,
                },
            ),
        ):
            tester_alive = self.bridge._ea_factory_optimization_execution_stop_prover(
                request
            )
        self.assertEqual(tester_alive["status"], "execution_still_running")
        self.assertEqual(tester_alive["reasonCode"], "tester_process_still_running")

    def test_stop_prover_releases_only_after_original_and_all_testers_are_absent(self) -> None:
        identity = {
            "terminalProcessId": 41001,
            "terminalProcessCreatedAt100ns": 133700000000000000,
            "terminalExecutablePathDigest": "a" * 64,
            "terminalExecutableSha256": "b" * 64,
            "identitySha256": "c" * 64,
        }
        request = {
            "sessionId": "opts_" + "1" * 32,
            "operationId": "op_" + "2" * 32,
            "executionIdentity": identity,
        }
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_windows_process_snapshot",
                return_value={
                    "status": "missing",
                    "reasonCode": "terminal_process_missing",
                },
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_windows_tester_agent_snapshot",
                return_value={
                    "status": "absent",
                    "reasonCode": "tester_processes_absent",
                    "count": 0,
                },
            ),
        ):
            stopped = self.bridge._ea_factory_optimization_execution_stop_prover(
                request
            )
        self.assertEqual(stopped["status"], "execution_stopped")
        self.assertEqual(stopped["reasonCode"], "terminal_process_stopped")
        self.assertRegex(stopped["proofSha256"], r"^[0-9a-f]{64}$")

    def test_cancelled_active_session_keeps_operator_stop_proof_retry_available(self) -> None:
        session = {
            "id": "opts_" + "4" * 32,
            "state": "awaiting_visible_terminal",
            "cancelRequested": True,
            "recovery": {
                "adapterCallInFlight": False,
                "executionIdentityCaptured": True,
                "executionStopProofPresent": False,
            },
        }
        public = self.bridge._ea_factory_optimization_public_session(session)
        self.assertTrue(public["canConfirmStopped"])
        self.assertTrue(public["canCancel"])

    def test_source_manifest_binds_exact_input_sinput_and_enum_defaults(self) -> None:
        manifest = self.source_manifest(
            "enum PositionSizingMode { fixed_lot=0, percent_equity=2 };\n"
            "input PositionSizingMode Mode = fixed_lot;\n"
            "input double FixedLot = .01;\n"
            "sinput int AuditOnly = 7;\n"
        )

        self.assertEqual(
            [entry["inputName"] for entry in manifest["entries"]],
            ["Mode", "FixedLot", "AuditOnly"],
        )
        self.assertEqual(manifest["entries"][0]["enumValues"], ["0", "2"])
        self.assertEqual(manifest["entries"][0]["setDefault"], "0")
        self.assertEqual(manifest["entries"][1]["setDefault"], "0.01")
        self.assertFalse(manifest["entries"][2]["optimizable"])
        self.assertRegex(manifest["manifestDigest"], r"^[0-9a-f]{64}$")

    def test_mt5_baseline_preset_resets_every_source_input_without_simulation(self) -> None:
        context = {
            "sourceBytes": (
                b"enum ModeKind { fixed_mode=0, risk_mode=2 };\n"
                b"input ModeKind Mode = fixed_mode;\n"
                b"input double FixedLot = 0.01;\n"
                b"sinput bool AuditOnly = true;\n"
            ),
            "sourceDigest": "a" * 64,
        }
        with mock.patch.object(
            self.bridge,
            "_ea_factory_mt5_input_context",
            return_value=context,
        ):
            preset = self.bridge._ea_factory_mt5_tester_input_preset({
                "platform": "mt5",
                "artifactKind": "expert_advisor",
            })

        self.assertEqual(preset["scope"], "mt5_strategy_tester_only")
        self.assertEqual(preset["inputManifestDigest"], self.source_manifest(
            context["sourceBytes"].decode("utf-8")
        )["manifestDigest"])
        self.assertEqual(preset["simulationInputNames"], [])
        manifest = self.source_manifest(context["sourceBytes"].decode("utf-8"))
        self.assertEqual(manifest["entries"][0]["enumValues"], ["0", "2"])
        self.assertEqual(manifest["entries"][2]["enumValues"], [])
        self.assertEqual(
            [row["inputName"] for row in preset["assumptions"]],
            ["Mode", "FixedLot", "AuditOnly"],
        )
        self.assertTrue(
            all(row["testerValue"] == row["sourceDefault"] for row in preset["assumptions"])
        )

    def test_compiled_deployment_rejects_binary_not_paired_with_source(self) -> None:
        context = {
            "build": {"id": "ea-build-mt5-verified"},
            "version": {"versionFile": "EA_Versions/VerifiedEA.mq5"},
            "sourceDigest": "a" * 64,
            "binary": {
                "fileName": "OtherEA.ex5",
                "relativePath": "EA_Versions/OtherEA.ex5",
                "sha256": "9" * 64,
            },
        }
        with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
            self.bridge._ea_factory_mt5_compiled_deployment_binding(
                context, self.terminal_binding()
            )
        self.assertEqual(caught.exception.code, "compiled_deployment_binding_invalid")

    def test_source_manifest_rejects_case_collisions_and_nonliteral_types(self) -> None:
        invalid_sources = (
            (
                "input int RiskMode = 0;\ninput int riskmode = 1;\n",
                "source_input_manifest_invalid",
            ),
            (
                "input string CommentText = \"unsafe\";\n",
                "source_input_manifest_invalid",
            ),
            (
                "input ENUM_TIMEFRAMES Period = PERIOD_H1;\n",
                "source_input_manifest_invalid",
            ),
            (
                "input int A = 1; input int B = 2;\n",
                "source_input_manifest_invalid",
            ),
        )
        for source, expected_code in invalid_sources:
            with self.subTest(source=source):
                with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                    self.source_manifest(source)
                self.assertEqual(caught.exception.code, expected_code)

    def test_ranges_require_exact_source_case_type_and_qualifier(self) -> None:
        manifest = self.source_manifest(
            "enum SparseMode { sparse_zero=0, sparse_two=2 };\n"
            "input SparseMode Mode = sparse_zero;\n"
            "input int StopLossPoints = 300;\n"
            "sinput int LockedInput = 1;\n"
        )
        invalid = (
            ({"name": "stoplosspoints", "kind": "numeric", "start": 100, "step": 50, "stop": 300}, "optimization_input_name_case_mismatch"),
            ({"name": "Unknown", "kind": "numeric", "start": 1, "step": 1, "stop": 2}, "optimization_input_not_in_source"),
            ({"name": "LockedInput", "kind": "numeric", "start": 1, "step": 1, "stop": 2}, "sinput_cannot_be_optimized"),
            ({"name": "StopLossPoints", "kind": "numeric", "start": 100.5, "step": 1, "stop": 101.5}, "integer_optimization_range_required"),
            ({"name": "Mode", "kind": "categorical", "values": [0, 1, 2]}, "enum_optimization_range_invalid"),
        )
        for row, expected_code in invalid:
            with self.subTest(row=row):
                with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                    self.bridge._ea_factory_validate_optimization_adapter_ranges(
                        {"ranges": [row]}, manifest
                    )
                self.assertEqual(caught.exception.code, expected_code)

        accepted = self.bridge._ea_factory_validate_optimization_adapter_ranges(
            {"ranges": [{"name": "Mode", "kind": "categorical", "values": [0, 2]}]},
            manifest,
        )
        self.assertEqual(accepted[0]["step"], "2")

    def test_full_set_is_immutable_and_readback_requires_every_source_input(self) -> None:
        manifest = self.source_manifest(
            "input bool Enabled = false;\n"
            "input double FixedLot = 0.01;\n"
            "sinput int AuditOnly = 7;\n"
        )
        ranges = self.bridge._ea_factory_validate_optimization_adapter_ranges(
            {"ranges": [{"name": "FixedLot", "kind": "numeric", "start": "0.01", "step": "0.01", "stop": "0.03"}]},
            manifest,
        )
        with tempfile.TemporaryDirectory() as temporary:
            build_dir = Path(temporary)
            (build_dir / "Sets").mkdir()
            relative, digest = self.bridge._ea_factory_write_optimization_set(
                {"buildDir": build_dir},
                "op_" + "1" * 32,
                ranges,
                manifest=manifest,
            )
            payload = (build_dir / relative).read_bytes()
            self.assertEqual(
                payload,
                b"Enabled=false||false||1||false||N\r\n"
                b"FixedLot=0.01||0.01||0.01||0.03||Y\r\n"
                b"AuditOnly=7||7||1||7||N\r\n",
            )
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
            self.assertTrue(
                self.bridge._ea_factory_optimization_readback_matches(
                    payload, manifest, ranges
                )
            )
            self.assertFalse(
                self.bridge._ea_factory_optimization_readback_matches(
                    payload.replace(b"AuditOnly=7||7||1||7||N\r\n", b""),
                    manifest,
                    ranges,
                )
            )
            self.assertFalse(
                self.bridge._ea_factory_optimization_readback_matches(
                    payload + b"Extra=1||1||1||1||N\r\n", manifest, ranges
                )
            )
            baseline_payload = (
                b"Enabled=false||false||1||false||N\r\n"
                b"FixedLot=0.01||0.01||1||0.01||N\r\n"
                b"AuditOnly=7||7||1||7||N\r\n"
            )
            self.assertTrue(
                self.bridge._ea_factory_optimization_readback_matches(
                    baseline_payload, manifest, []
                )
            )
            native_bool_baseline_payload = baseline_payload.replace(
                b"Enabled=false||false||1||false||N",
                b"Enabled=false||false||0||true||N",
            )
            self.assertTrue(
                self.bridge._ea_factory_optimization_readback_matches(
                    native_bool_baseline_payload, manifest, []
                )
            )
            self.assertFalse(
                self.bridge._ea_factory_optimization_readback_matches(
                    baseline_payload.replace(
                        b"FixedLot=0.01||0.01||1||0.01||N",
                        b"FixedLot=0.02||0.02||1||0.02||N",
                    ),
                    manifest,
                    [],
                )
            )
            self.bridge._ea_factory_write_optimization_set(
                {"buildDir": build_dir},
                "op_" + "1" * 32,
                ranges,
                manifest=manifest,
            )
            changed = [dict(ranges[0], stop="0.04")]
            with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                self.bridge._ea_factory_write_optimization_set(
                    {"buildDir": build_dir},
                    "op_" + "1" * 32,
                    changed,
                    manifest=manifest,
                )
            self.assertEqual(caught.exception.code, "immutable_set_conflict")

            override_relative, _override_digest = (
                self.bridge._ea_factory_write_optimization_set(
                    {"buildDir": build_dir},
                    "op_" + "2" * 32,
                    ranges,
                    manifest=manifest,
                    fixed_current_overrides={"Enabled": "true"},
                )
            )
            override_payload = (build_dir / override_relative).read_bytes()
            self.assertEqual(
                override_payload,
                b"Enabled=true||true||1||true||N\r\n"
                b"FixedLot=0.01||0.01||0.01||0.03||Y\r\n"
                b"AuditOnly=7||7||1||7||N\r\n",
            )
            self.assertTrue(
                self.bridge._ea_factory_optimization_readback_matches(
                    override_payload,
                    manifest,
                    ranges,
                    fixed_current_overrides={"Enabled": "true"},
                )
            )
            native_bool_override_payload = override_payload.replace(
                b"Enabled=true||true||1||true||N",
                b"Enabled=true||false||0||true||N",
            )
            self.assertTrue(
                self.bridge._ea_factory_optimization_readback_matches(
                    native_bool_override_payload,
                    manifest,
                    ranges,
                    fixed_current_overrides={"Enabled": "true"},
                )
            )
            for tampered_bool_row in (
                b"Enabled=false||false||0||true||N",
                b"Enabled=true||false||0||true||Y",
                b"Enabled=true||true||0||true||N",
                b"Enabled=true||false||1||true||N",
                b"Enabled=true||false||0||false||N",
                b"Enabled=true||0||false||1||N",
            ):
                with self.subTest(tampered_bool_row=tampered_bool_row):
                    self.assertFalse(
                        self.bridge._ea_factory_optimization_readback_matches(
                            native_bool_override_payload.replace(
                                b"Enabled=true||false||0||true||N",
                                tampered_bool_row,
                            ),
                            manifest,
                            ranges,
                            fixed_current_overrides={"Enabled": "true"},
                        )
                    )
            self.assertFalse(
                self.bridge._ea_factory_optimization_readback_matches(
                    override_payload,
                    manifest,
                    ranges,
                )
            )

    def test_artifact_alias_kind_extension_and_path_identity_are_exact(self) -> None:
        definitions = {
            "tester_settings": ("Screenshots/settings.png", "screenshot_evidence"),
            "baseline_input_readback": ("Sets/baseline-readback.set", "set_file"),
            "optimization_input_readback": ("Sets/readback.set", "set_file"),
            "optimization_completion_checkpoint": (
                "Summaries/completion-checkpoint.json",
                "optimization_evidence",
            ),
            "tester_result": ("Screenshots/result.png", "screenshot_evidence"),
            "tester_report_proof": ("Screenshots/report.png", "screenshot_evidence"),
            "optimization_report": ("Reports/result.xml", "optimization_evidence"),
            "adapter_receipt": ("Reports/receipt.json", "optimization_evidence"),
        }
        with tempfile.TemporaryDirectory() as temporary:
            build_dir = Path(temporary)
            rows = []
            for alias, (relative, kind) in definitions.items():
                path = build_dir / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(
                    b"<Workbook/>"
                    if alias == "optimization_report"
                    else b"{}"
                    if alias in {
                        "optimization_completion_checkpoint",
                        "adapter_receipt",
                    }
                    else alias.encode("ascii")
                )
                rows.append({"alias": alias, "relativePath": relative, "artifactKind": kind})
            result = self.bridge._ea_factory_optimization_artifacts(build_dir, rows)
            self.assertEqual(set(result), set(definitions))

            wrong_kind = [dict(item) for item in rows]
            wrong_kind[0]["artifactKind"] = "optimization_evidence"
            with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                self.bridge._ea_factory_optimization_artifacts(build_dir, wrong_kind)
            self.assertEqual(caught.exception.code, "adapter_evidence_invalid")

            duplicate_path = [dict(item) for item in rows]
            duplicate_path[1]["relativePath"] = duplicate_path[0]["relativePath"]
            with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                self.bridge._ea_factory_optimization_artifacts(build_dir, duplicate_path)
            self.assertEqual(caught.exception.code, "adapter_evidence_invalid")

            wrong_report_suffix = [dict(item) for item in rows]
            report_row = next(
                item for item in wrong_report_suffix
                if item["alias"] == "optimization_report"
            )
            report_row["relativePath"] = "Reports/result.html"
            oversized_html = build_dir / report_row["relativePath"]
            with oversized_html.open("wb") as handle:
                handle.truncate(
                    self.bridge.EA_FACTORY_MT5_OPTIMIZATION_EVIDENCE_MAX_BYTES + 1
                )
            with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                self.bridge._ea_factory_optimization_artifacts(
                    build_dir, wrong_report_suffix
                )
            self.assertEqual(caught.exception.code, "adapter_evidence_invalid")

            wrong_checkpoint_suffix = [dict(item) for item in rows]
            checkpoint_row = next(
                item for item in wrong_checkpoint_suffix
                if item["alias"] == "optimization_completion_checkpoint"
            )
            checkpoint_row["relativePath"] = "Summaries/completion-checkpoint.xml"
            (build_dir / checkpoint_row["relativePath"]).write_bytes(b"{}")
            with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                self.bridge._ea_factory_optimization_artifacts(
                    build_dir, wrong_checkpoint_suffix
                )
            self.assertEqual(caught.exception.code, "adapter_evidence_invalid")

    def test_optimization_xml_budget_is_alias_scoped_and_enforces_boundary(self) -> None:
        contract = self.bridge.EA_FACTORY_MT5_OPTIMIZATION_ARTIFACT_CONTRACT
        report_contract = contract["optimization_report"]
        self.assertEqual(report_contract[1], frozenset({".xml"}))
        self.assertEqual(
            report_contract[2],
            self.bridge.EA_FACTORY_MT5_OPTIMIZATION_XML_MAX_BYTES,
        )
        self.assertTrue(
            all(
                maximum_bytes
                <= self.bridge.EA_FACTORY_MT5_OPTIMIZATION_EVIDENCE_MAX_BYTES
                for alias, (_kind, _extensions, maximum_bytes) in contract.items()
                if alias != "optimization_report"
            )
        )

        definitions = {
            "tester_settings": ("Screenshots/settings.png", "screenshot_evidence"),
            "baseline_input_readback": ("Sets/baseline-readback.set", "set_file"),
            "optimization_input_readback": ("Sets/readback.set", "set_file"),
            "optimization_completion_checkpoint": (
                "Summaries/completion-checkpoint.json",
                "optimization_evidence",
            ),
            "tester_result": ("Screenshots/result.png", "screenshot_evidence"),
            "tester_report_proof": ("Screenshots/report.png", "screenshot_evidence"),
            "optimization_report": ("Reports/result.xml", "optimization_evidence"),
            "adapter_receipt": ("Reports/receipt.json", "optimization_evidence"),
        }
        with tempfile.TemporaryDirectory() as temporary:
            build_dir = Path(temporary)
            rows = []
            for alias, (relative, kind) in definitions.items():
                path = build_dir / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"12345678" if alias == "optimization_report" else b"x")
                rows.append({"alias": alias, "relativePath": relative, "artifactKind": kind})

            with mock.patch.dict(
                contract,
                {
                    "optimization_report": (
                        "optimization_evidence",
                        frozenset({".xml"}),
                        8,
                    )
                },
            ):
                accepted = self.bridge._ea_factory_optimization_artifacts(
                    build_dir, rows
                )
                self.assertEqual(
                    accepted["optimization_report"]["byteSize"], 8
                )
                (build_dir / "Reports/result.xml").write_bytes(b"123456789")
                with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                    self.bridge._ea_factory_optimization_artifacts(build_dir, rows)
                self.assertEqual(caught.exception.code, "adapter_evidence_missing")

    def test_completed_mt5_handler_binds_completion_checkpoint_digest(self) -> None:
        operation_id = "op_" + "2" * 32
        terminal = self.terminal_binding()
        source_digest = "a" * 64
        binary_digest = "9" * 64
        with tempfile.TemporaryDirectory() as temporary:
            build_dir = Path(temporary)
            definitions = {
                "tester_settings": ("Screenshots/settings.png", "screenshot_evidence"),
                "baseline_input_readback": ("Sets/baseline-readback.set", "set_file"),
                "optimization_input_readback": ("Sets/readback.set", "set_file"),
                "optimization_completion_checkpoint": (
                    "Summaries/completion-checkpoint.json",
                    "optimization_evidence",
                ),
                "tester_result": ("Screenshots/result.png", "screenshot_evidence"),
                "tester_report_proof": ("Screenshots/report.png", "screenshot_evidence"),
                "optimization_report": ("Reports/result.xml", "optimization_evidence"),
                "adapter_receipt": ("Reports/receipt.json", "optimization_evidence"),
            }
            payloads = {
                "tester_settings": b"settings",
                "baseline_input_readback": b"baseline",
                "optimization_input_readback": b"optimization",
                "optimization_completion_checkpoint": b'{"status":"completed"}',
                "tester_result": b"result",
                "tester_report_proof": b"proof",
                "optimization_report": b"<Workbook/>",
            }
            for alias, payload in payloads.items():
                path = build_dir / definitions[alias][0]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)

            def digest(alias: str) -> str:
                return self.bridge.hashlib.sha256(
                    (build_dir / definitions[alias][0]).read_bytes()
                ).hexdigest()

            optimization_intent = {
                "setDigest": "1" * 64,
                "rangesDigest": "2" * 64,
                "inputManifestDigest": "3" * 64,
                "setRef": {
                    "refDigest": "4" * 64,
                    "expectedReadbackEntriesDigest": "5" * 64,
                },
                "baselinePresetRef": {
                    "refDigest": "6" * 64,
                    "expectedReadbackEntriesDigest": "7" * 64,
                },
                "ranges": [{"inputName": "StopLossPoints"}],
            }
            compiled_deployment = {
                "deploymentRef": "mt5deploy_" + "8" * 24,
                "bindingDigest": "b" * 64,
            }
            adapter_request = {
                "visibleOperation": {"operationId": operation_id},
                "terminalBinding": terminal,
                "resolvedTarget": {},
                "testerSettings": {},
                "optimizationIntent": optimization_intent,
                "compiledDeployment": compiled_deployment,
            }
            adapter_receipt = {
                "operationId": operation_id,
                "stageId": "optimize",
                "platform": "mt5",
                "status": "verified",
                "sourceDigest": source_digest,
                "compiledBinarySha256": binary_digest,
                "terminalCandidateId": terminal["candidateId"],
                "optimizationSetSha256": optimization_intent["setDigest"],
                "optimizationRangesDigest": optimization_intent["rangesDigest"],
                "inputManifestDigest": optimization_intent["inputManifestDigest"],
                "optimizationSetRefDigest": optimization_intent["setRef"]["refDigest"],
                "optimizationExpectedReadbackEntriesDigest": (
                    optimization_intent["setRef"]["expectedReadbackEntriesDigest"]
                ),
                "baselinePresetRefDigest": optimization_intent["baselinePresetRef"]["refDigest"],
                "baselineExpectedReadbackEntriesDigest": (
                    optimization_intent["baselinePresetRef"]["expectedReadbackEntriesDigest"]
                ),
                "baselineReadbackSetSha256": digest("baseline_input_readback"),
                "baselineReadbackEntriesDigest": (
                    optimization_intent["baselinePresetRef"]["expectedReadbackEntriesDigest"]
                ),
                "compiledDeploymentRef": compiled_deployment["deploymentRef"],
                "compiledDeploymentDigest": compiled_deployment["bindingDigest"],
                "optimizationReadbackSetSha256": digest("optimization_input_readback"),
                "optimizationCompletionCheckpointSha256": digest(
                    "optimization_completion_checkpoint"
                ),
                "liveTradingExecuted": False,
                "autoTradingToggled": False,
                "terminalClosedByAdapter": False,
            }
            receipt_path = build_dir / definitions["adapter_receipt"][0]
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(
                json.dumps(adapter_receipt, sort_keys=True), encoding="utf-8"
            )
            artifact_rows = [
                {"alias": alias, "relativePath": relative, "artifactKind": kind}
                for alias, (relative, kind) in definitions.items()
            ]
            metrics = {
                "optimizationVerified": True,
                "visibleOptimization": True,
                "platform": "mt5",
                "terminalCandidateId": terminal["candidateId"],
                "terminalSelectionRevision": terminal["selectionRevision"],
                "terminalBindingDigest": terminal["bindingDigest"],
                "sourceDigest": source_digest,
                "liveTradingExecuted": False,
                "autoTradingToggled": False,
                "chartAttached": False,
                "terminalClosedByAdapter": False,
                "terminalStillRunning": True,
                "testerReportSha256": digest("optimization_report"),
                "settingsScreenshotSha256": digest("tester_settings"),
                "resultScreenshotSha256": digest("tester_result"),
                "reportScreenshotSha256": digest("tester_report_proof"),
                "optimizationCompletionCheckpointSha256": digest(
                    "optimization_completion_checkpoint"
                ),
                "optimizationPassCount": 2,
                "optimizationReturnedPassCount": 2,
                "optimizationResultRows": [{"pass": 1}, {"pass": 2}],
                "optimizationRowsTruncated": False,
                "resolvedTesterSettings": {"deposit": 10_000.0},
                "processBindingDigest": "c" * 64,
                "postProcessBindingDigest": "d" * 64,
            }
            raw = {
                "operationId": operation_id,
                "metrics": metrics,
                "artifactSpecifications": artifact_rows,
            }
            context = {
                "buildDir": build_dir,
                "sourceDigest": source_digest,
                "binary": {"sha256": binary_digest},
                "baselineVisualBacktestSha256": "e" * 64,
                "optimizationInputManifest": {"manifestDigest": "3" * 64},
            }
            request = {
                "action": "start_round",
                "sessionId": "opts_" + "1" * 32,
                "buildId": "ea-build-mt5-verified",
                "sourceDigest": source_digest,
                "baselineReportSha256": "f" * 64,
                "operation": {
                    "operationId": operation_id,
                    "boundaryDocumentSha256": "0" * 64,
                },
                "round": {
                    "roundId": "round_" + "3" * 32,
                    "ranges": [],
                },
                "testerSettings": {"symbol": "XAUUSD"},
            }
            provider = mock.Mock(return_value={"ready": True})
            visible_handler = mock.Mock(return_value=raw)
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_adapter_request",
                    return_value=(context, adapter_request),
                ),
                mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                    provider,
                ),
                mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_VISIBLE_OPTIMIZATION_HANDLER",
                    visible_handler,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_front_office_capability_ready",
                    return_value=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_readback_matches",
                    return_value=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_persist_evidence_binding",
                ) as persist_binding,
                mock.patch.object(self.bridge, "append_audit"),
            ):
                result = self.bridge._ea_factory_optimization_handler(request)
                self.assertEqual(result["status"], "completed")
                self.assertEqual(
                    persist_binding.call_args.args[0][
                        "optimizationCompletionCheckpointSha256"
                    ],
                    digest("optimization_completion_checkpoint"),
                )

                metrics["optimizationCompletionCheckpointSha256"] = "0" * 64
                with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                    self.bridge._ea_factory_optimization_handler(request)
                self.assertEqual(
                    caught.exception.code, "adapter_evidence_digest_mismatch"
                )

                metrics["optimizationCompletionCheckpointSha256"] = digest(
                    "optimization_completion_checkpoint"
                )
                adapter_receipt["optimizationCompletionCheckpointSha256"] = "0" * 64
                receipt_path.write_text(
                    json.dumps(adapter_receipt, sort_keys=True), encoding="utf-8"
                )
                with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                    self.bridge._ea_factory_optimization_handler(request)
                self.assertEqual(
                    caught.exception.code, "adapter_receipt_invalid"
                )

    def test_durable_evidence_binding_survives_audit_tail_eviction(self) -> None:
        session_id = "opts_" + "b" * 32
        terminal = self.terminal_binding()
        report = {"ref": "optreport_" + "1" * 24, "sha256": "1" * 64, "byteSize": 100}
        receipt = {"ref": "optmanifest_" + "2" * 24, "sha256": "2" * 64, "byteSize": 200}
        session = {
            "id": session_id,
            "state": "completed",
            "platform": "mt5",
            "buildId": "ea-build-mt5-verified",
            "sourceDigest": "a" * 64,
            "baselineReportSha256": "b" * 64,
            "terminalBinding": terminal,
            "evidence": [{
                "roundId": "round-01",
                "report": report,
                "manifest": receipt,
                "testerSettingsSha256": "3" * 64,
                "visibleEvidenceSha256": "4" * 64,
            }],
        }
        event = {
            "type": "ea_factory.optimization.evidence_bound",
            "sessionId": session_id,
            "operationId": "op_" + "c" * 32,
            "roundId": "round-01",
            "buildId": session["buildId"],
            "sourceDigest": session["sourceDigest"],
            "baselineReportSha256": session["baselineReportSha256"],
            "baselineVisualBacktestSha256": "5" * 64,
            "compiledBinarySha256": "6" * 64,
            "terminalCandidateId": terminal["candidateId"],
            "terminalSelectionRevision": terminal["selectionRevision"],
            "terminalBindingDigest": terminal["bindingDigest"],
            "settingsScreenshotSha256": "7" * 64,
            "resultsScreenshotSha256": "8" * 64,
            "testerReportProofSha256": "9" * 64,
            "optimizationCompletionCheckpointSha256": "d" * 64,
            "baselineReadbackSha256": "f" * 64,
            "baselineReadbackEntriesDigest": "e" * 64,
            "optimizationReadbackSha256": "a" * 64,
            "optimizationReportRef": report["ref"],
            "optimizationReportSha256": report["sha256"],
            "optimizationReportByteSize": report["byteSize"],
            "adapterReceiptRef": receipt["ref"],
            "adapterReceiptSha256": receipt["sha256"],
            "adapterReceiptByteSize": receipt["byteSize"],
            "testerSettingsSha256": "3" * 64,
            "visibleEvidenceSha256": "4" * 64,
            "inputManifestDigest": "b" * 64,
            "optimizationSetRefDigest": "c" * 64,
            "optimizationExpectedReadbackEntriesDigest": "d" * 64,
            "optimizationRanges": [{
                "inputName": "StopLossPoints",
                "start": "100",
                "step": "50",
                "stop": "300",
                "enabled": True,
                "sourceDefault": "300",
                "valueKind": "integer",
            }],
            "baselinePresetRefDigest": "e" * 64,
            "baselineExpectedReadbackEntriesDigest": "f" * 64,
            "compiledDeploymentRef": "mt5deploy_" + "1" * 24,
            "compiledDeploymentDigest": "0" * 64,
            "liveTrading": False,
            "testShutdownTerminal": False,
        }
        event["optimizationRangesDigest"] = (
            self.bridge._ea_factory_optimization_json_sha256(
                event["optimizationRanges"]
            )
        )
        with tempfile.TemporaryDirectory() as temporary:
            with (
                mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_OPTIMIZATION_ROOT",
                    Path(temporary) / "optimization",
                ),
                mock.patch.object(self.bridge, "tail_jsonl", return_value=[]),
            ):
                self.bridge._ea_factory_optimization_persist_evidence_binding(event)
                loaded = self.bridge._ea_factory_optimization_evidence_binding(session)

        self.assertEqual(loaded, event)

    def test_auto_ranges_are_limited_to_strategy_brief_default_receipt(self) -> None:
        from hq_backend.ea.ea_strategy_brief import apply_strategy_brief_implementation_defaults

        generated_brief = apply_strategy_brief_implementation_defaults({
            "systemName": "Generated defaults",
            "entryRules": "Buy on a closed bar.",
            "exitRules": "unknown",
            "moneyManagement": "unknown",
            "orderExecution": "unknown",
            "recoveryRules": "unknown",
            "additionalNotes": "source note",
            "limitations": [],
        })
        self.assertIsInstance(generated_brief, dict)
        receipt = generated_brief["limitations"][-1]
        manifest = self.source_manifest(
            "input double FixedLot = 0.01;\n"
            "input int StopLossPoints = 300;\n"
            "input int TakeProfitPoints = 600;\n"
            "input int MaxOpenPositionsPerSymbolMagic = 1;\n"
        )
        context = {
            "strategySpec": {
                "strategyBrief": generated_brief
            }
        }
        ranges = self.bridge._ea_factory_source_bound_auto_optimization_ranges(
            context, manifest
        )
        self.assertEqual(
            [item["name"] for item in ranges],
            [
                "FixedLot",
                "StopLossPoints",
                "TakeProfitPoints",
                "MaxOpenPositionsPerSymbolMagic",
            ],
        )

        compact_context = copy.deepcopy(context)
        compact_context["strategySpec"]["strategyBrief"].pop("limitations")
        compact_ranges = self.bridge._ea_factory_source_bound_auto_optimization_ranges(
            compact_context,
            manifest,
        )
        self.assertEqual(
            [item["name"] for item in compact_ranges],
            [
                "FixedLot",
                "StopLossPoints",
                "TakeProfitPoints",
                "MaxOpenPositionsPerSymbolMagic",
            ],
        )

        context["strategySpec"]["strategyBrief"]["limitations"] = []
        with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
            self.bridge._ea_factory_source_bound_auto_optimization_ranges(
                context, manifest
            )
        self.assertEqual(caught.exception.code, "source_bound_optimization_ranges_unavailable")

        duplicate_context = copy.deepcopy(compact_context)
        duplicate_context["strategySpec"]["strategyBrief"]["limitations"] = [
            receipt,
            receipt,
        ]
        with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
            self.bridge._ea_factory_source_bound_auto_optimization_ranges(
                duplicate_context,
                manifest,
            )
        self.assertEqual(caught.exception.code, "source_bound_optimization_ranges_unavailable")

        unknown_context = copy.deepcopy(compact_context)
        unknown_context["strategySpec"]["strategyBrief"]["additionalNotes"] = (
            unknown_context["strategySpec"]["strategyBrief"]["additionalNotes"].replace(
                "stop_loss,",
                "stop_loss,unknown_component,",
            )
        )
        with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
            self.bridge._ea_factory_source_bound_auto_optimization_ranges(
                unknown_context,
                manifest,
            )
        self.assertEqual(caught.exception.code, "source_bound_optimization_ranges_unavailable")

    def test_custom_ema_pips_ranges_are_digest_bound_and_four_passes(self) -> None:
        context, manifest = self.custom_ema_pips_context()

        ranges = self.bridge._ea_factory_source_bound_auto_optimization_ranges(
            context,
            manifest,
        )

        self.assertEqual(ranges, [
            {
                "name": "StopLossPips",
                "kind": "numeric",
                "start": "10",
                "step": "10",
                "stop": "20",
            },
            {
                "name": "TakeProfitPips",
                "kind": "numeric",
                "start": "20",
                "step": "20",
                "stop": "40",
            },
        ])
        self.assertNotIn("FixedLot", {item["name"] for item in ranges})
        pass_count = 1
        for item in ranges:
            pass_count *= (
                (int(item["stop"]) - int(item["start"]))
                // int(item["step"])
            ) + 1
        self.assertEqual(pass_count, 4)

        run = {
            "runId": "oneclick-custom-ema-smoke",
            "status": "running",
            "currentStageId": None,
            "terminalBinding": self.terminal_binding(),
        }
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_build_context",
                return_value=context,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_target_resolver",
                return_value=self.terminal_binding(),
            ),
        ):
            request = self.bridge._ea_factory_one_click_auto_optimization_request(
                context["build"]["id"],
                run,
            )
        self.assertEqual(request["rounds"], [{
            "label": "Source-bound MT5 auto optimization",
            "ranges": ranges,
        }])
        self.assertEqual(request["sourceDigest"], context["sourceDigest"])
        self.assertEqual(
            request["testerSettings"]["optimizationMode"],
            "slow_complete",
        )

    def test_custom_ema_pips_ranges_reject_wrong_defaults_and_input_kinds(self) -> None:
        cases = (
            (
                "wrong_stop_default",
                {"stop_declaration": "input double StopLossPips = 31.0;"},
            ),
            (
                "integer_stop",
                {"stop_declaration": "input int StopLossPips = 30;"},
            ),
            (
                "boolean_stop",
                {"stop_declaration": "input bool StopLossPips = true;"},
            ),
            (
                "unoptimizable_stop",
                {"stop_declaration": "sinput double StopLossPips = 30.0;"},
            ),
        )
        for label, options in cases:
            with self.subTest(label=label):
                context, manifest = self.custom_ema_pips_context(**options)
                with self.assertRaises(
                    self.bridge.OptimizationDomainError
                ) as caught:
                    self.bridge._ea_factory_source_bound_auto_optimization_ranges(
                        context,
                        manifest,
                    )
                self.assertEqual(
                    caught.exception.code,
                    "source_bound_optimization_ranges_unavailable",
                )

    def test_custom_ema_pips_ranges_reject_unbound_provenance_and_brief(self) -> None:
        cases = (
            (
                "non_custom_source",
                {"source_kind": "verified_deep_research"},
            ),
            (
                "wrong_platform",
                {"platform": "mt4"},
            ),
            (
                "wrong_artifact",
                {"artifact_kind": "custom_indicator"},
            ),
            (
                "missing_explicit_input_name",
                {
                    "exit_rules": (
                        "Use positive stop loss and take profit inputs. Close an "
                        "existing position on the opposite confirmed crossover."
                    )
                },
            ),
        )
        for label, options in cases:
            with self.subTest(label=label):
                context, manifest = self.custom_ema_pips_context(**options)
                with self.assertRaises(
                    self.bridge.OptimizationDomainError
                ) as caught:
                    self.bridge._ea_factory_source_bound_auto_optimization_ranges(
                        context,
                        manifest,
                    )
                self.assertEqual(
                    caught.exception.code,
                    "source_bound_optimization_ranges_unavailable",
                )

    def test_custom_ema_pips_ranges_reject_manifest_or_brief_digest_drift(self) -> None:
        context, manifest = self.custom_ema_pips_context()
        tampered_manifest = copy.deepcopy(manifest)
        tampered_manifest["manifestDigest"] = "f" * 64
        with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
            self.bridge._ea_factory_source_bound_auto_optimization_ranges(
                context,
                tampered_manifest,
            )
        self.assertEqual(
            caught.exception.code,
            "source_bound_optimization_ranges_unavailable",
        )

        tampered_brief = copy.deepcopy(context)
        tampered_brief["strategySpec"]["strategyBrief"]["entryRules"] = (
            "BUY and SELL without an EMA crossover."
        )
        with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
            self.bridge._ea_factory_source_bound_auto_optimization_ranges(
                tampered_brief,
                manifest,
            )
        self.assertEqual(
            caught.exception.code,
            "source_bound_optimization_ranges_unavailable",
        )

    def test_auto_ranges_recover_only_explicit_legacy_source_backed_stop_range(self) -> None:
        legacy_marker = (
            f"[{self.bridge.EA_STRATEGY_BRIEF_IMPLEMENTATION_DEFAULT_MARKER}]"
            f"[POLICY={self.bridge.EA_STRATEGY_BRIEF_LEGACY_IMPLEMENTATION_DEFAULT_POLICY_ID}]"
            "[COMPONENT=exitRules]"
        )
        source = (
            "input double InpStopLossPercent = 7.5;\n"
            "input double RiskPercent = 1.0;\n"
            "input int DailyMAPeriod = 50;\n"
            "int OnInit() {\n"
            "  if(InpStopLossPercent < 7 || InpStopLossPercent > 8) "
            "return INIT_PARAMETERS_INCORRECT;\n"
            "  return INIT_SUCCEEDED;\n"
            "}\n"
            "void OnTick() {\n"
            "  if(InpStopLossPercent < 7 || InpStopLossPercent > 8) return;\n"
            "  double entryPrice = 100.0;\n"
            "  double brokerFloor = 1.0;\n"
            "  double priceTick = 0.01;\n"
            "  double requestedStopDistance = "
            "entryPrice * InpStopLossPercent / 100.0;\n"
            "  double stopDistance = MathMax(brokerFloor, requestedStopDistance);\n"
            "  double stopLoss = NormalizePriceUpToTick("
            "entryPrice - stopDistance, priceTick);\n"
            "}\n"
        )
        source_digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        strategy_spec_digest = "b" * 64
        binding_patch = mock.patch.object(
            self.bridge,
            "EA_FACTORY_LEGACY_SOURCE_BOUND_OPTIMIZATION_BINDINGS",
            frozenset({(strategy_spec_digest, source_digest)}),
        )
        binding_patch.start()
        self.addCleanup(binding_patch.stop)
        context = {
            "sourceBytes": source.encode("utf-8"),
            "sourceDigest": source_digest,
            "strategySpecDigest": strategy_spec_digest,
            "strategySpec": {
                "strategyBrief": {
                    "systemName": "CAN SLIM",
                    "exitRules": (
                        "กฎจากแหล่งข้อมูล: ตัดขาดทุนทุกสถานะ Long ไม่เกิน "
                        "7%-8% ต่ำกว่าจุดซื้อ โดยใช้เป็น Stop Loss หลัก. "
                        + legacy_marker
                    ),
                    "additionalNotes": "Legacy Brief predates optimization metadata.",
                }
            }
        }
        manifest = self.source_manifest(source)

        ranges = self.bridge._ea_factory_source_bound_auto_optimization_ranges(
            context,
            manifest,
        )

        self.assertEqual(ranges, [{
            "name": "InpStopLossPercent",
            "kind": "numeric",
            "start": "7",
            "step": "0.5",
            "stop": "8",
        }])
        self.assertNotIn("RiskPercent", {item["name"] for item in ranges})
        self.assertNotIn("DailyMAPeriod", {item["name"] for item in ranges})

        malformed_current = copy.deepcopy(context)
        malformed_current["strategySpec"]["strategyBrief"]["additionalNotes"] = (
            f"[{self.bridge.EA_STRATEGY_BRIEF_IMPLEMENTATION_DEFAULT_MARKER}]"
            f"[POLICY={self.bridge.EA_STRATEGY_BRIEF_IMPLEMENTATION_DEFAULT_POLICY_ID}] "
            "INPUT_METADATA_VERSION=ea-optimization-inputs-v1"
        )
        with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
            self.bridge._ea_factory_source_bound_auto_optimization_ranges(
                malformed_current,
                manifest,
            )
        self.assertEqual(
            caught.exception.code,
            "source_bound_optimization_ranges_unavailable",
        )

        malformed_limitation = copy.deepcopy(context)
        malformed_limitation["strategySpec"]["strategyBrief"]["limitations"] = [
            "INPUT_METADATA_VERSION=ea-optimization-inputs-v1"
        ]
        with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
            self.bridge._ea_factory_source_bound_auto_optimization_ranges(
                malformed_limitation,
                manifest,
            )
        self.assertEqual(
            caught.exception.code,
            "source_bound_optimization_ranges_unavailable",
        )

        no_source_enforcement = copy.deepcopy(context)
        no_source_enforcement["sourceBytes"] = (
            "input double InpStopLossPercent = 7.5;\n"
            "void OnTick() {}\n"
        ).encode("utf-8")
        with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
            self.bridge._ea_factory_source_bound_auto_optimization_ranges(
                no_source_enforcement,
                manifest,
            )
        self.assertEqual(
            caught.exception.code,
            "source_bound_optimization_ranges_unavailable",
        )

        decoy_source = (
            "input double InpStopLossPercent = 7.5;\n"
            "void Decoy() {\n"
            "  if(InpStopLossPercent < 7 || InpStopLossPercent > 8) return;\n"
            "  double entryPrice = 100.0;\n"
            "  double brokerFloor = 1.0;\n"
            "  double priceTick = 0.01;\n"
            "  double requestedStopDistance = "
            "entryPrice * InpStopLossPercent / 100.0;\n"
            "  double stopDistance = MathMax(brokerFloor, requestedStopDistance);\n"
            "  double stopLoss = NormalizePriceUpToTick("
            "entryPrice - stopDistance, priceTick);\n"
            "}\n"
            "int OnInit() { return INIT_SUCCEEDED; }\n"
            "void OnTick() {}\n"
        )
        decoy_context = copy.deepcopy(context)
        decoy_context["sourceBytes"] = decoy_source.encode("utf-8")
        with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
            self.bridge._ea_factory_source_bound_auto_optimization_ranges(
                decoy_context,
                self.source_manifest(decoy_source),
            )
        self.assertEqual(
            caught.exception.code,
            "source_bound_optimization_ranges_unavailable",
        )

        sinput_source = source.replace(
            "input double InpStopLossPercent",
            "sinput double InpStopLossPercent",
            1,
        )
        sinput_context = copy.deepcopy(context)
        sinput_context["sourceBytes"] = sinput_source.encode("utf-8")
        with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
            self.bridge._ea_factory_source_bound_auto_optimization_ranges(
                sinput_context,
                self.source_manifest(sinput_source),
            )
        self.assertEqual(
            caught.exception.code,
            "source_bound_optimization_ranges_unavailable",
        )

    def test_one_click_auto_request_binds_exact_baseline_source_manifest_and_terminal(self) -> None:
        context = {
            **self.build_context(),
            "strategySpec": {"strategyBrief": {}},
            "baselineTesterSettings": {
                "symbol": "XAUUSD",
                "period": "H1",
                "model": "every_tick",
                "useDate": True,
                "fromDate": "2025-01-01",
                "toDate": "2025-12-31",
            },
        }
        run = {
            "runId": "oneclick-run-001",
            "status": "running",
            "currentStageId": None,
            "terminalBinding": self.terminal_binding(),
        }
        ranges = [{"name": "StopLossPoints", "kind": "numeric", "start": "100", "step": "100", "stop": "1000"}]
        with (
            mock.patch.object(self.bridge, "_ea_factory_optimization_build_context", return_value=context),
            mock.patch.object(self.bridge, "_ea_factory_optimization_target_resolver", return_value=self.terminal_binding()),
            mock.patch.object(self.bridge, "_ea_factory_source_bound_auto_optimization_ranges", return_value=ranges),
        ):
            request = self.bridge._ea_factory_one_click_auto_optimization_request(
                "ea-build-mt5-verified", run
            )

        self.assertEqual(request["sourceDigest"], context["sourceDigest"])
        self.assertEqual(request["baselineReportSha256"], context["baseline"]["sha256"])
        self.assertEqual(request["testerSettings"]["symbol"], "XAUUSD")
        self.assertEqual(
            request["testerSettings"]["optimizationMode"],
            "fast_genetic",
        )
        self.assertEqual(request["terminalBindingDigest"], self.terminal_binding()["bindingDigest"])
        self.assertEqual(request["rounds"][0]["ranges"], ranges)
        replay = self.bridge._ea_factory_optimization_json_sha256(request)
        self.assertEqual(replay, self.bridge._ea_factory_optimization_json_sha256(request))

    def test_factory_handoff_is_retired_before_service_or_state_side_effects(self) -> None:
        run = {"runId": "oneclick-run-001", "status": "running"}
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_auto_optimization_request",
            ) as build_request,
            mock.patch.object(self.bridge, "_ea_factory_optimization_service") as service,
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_optimization_worker",
            ) as start_worker,
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ) as write_state,
        ):
            with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                self.bridge._ea_factory_one_click_auto_optimization_handoff(
                    "ea-build-mt5-verified", run
                )

        self.assertEqual(caught.exception.code, "factory_optimization_boundary_retired")
        self.assertEqual(caught.exception.status, 409)
        self.assertIn("separate Optimization Lab", str(caught.exception))
        build_request.assert_not_called()
        service.assert_not_called()
        start_worker.assert_not_called()
        write_state.assert_not_called()

    def test_factory_handoff_never_publishes_a_legacy_optimizer_completion(
        self,
    ) -> None:
        run = {
            "runId": "oneclick-run-completed-legacy",
            "status": "completed",
            "optimizationHandoff": {
                "sessionId": "opts_" + "2" * 32,
                "state": "completed",
            },
        }
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_publish_terminal_report",
            ) as publish_report,
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_optimization_worker",
            ) as start_worker,
        ):
            with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                self.bridge._ea_factory_one_click_auto_optimization_handoff(
                    "ea-build-mt5-verified", run
                )

        self.assertEqual(caught.exception.code, "factory_optimization_boundary_retired")
        publish_report.assert_not_called()
        start_worker.assert_not_called()

    def test_one_click_worker_finishes_only_after_durable_optimization_handoff(self) -> None:
        run = {
            "runId": "oneclick-run-001",
            "status": "running",
            "currentStageId": None,
        }
        action = {
            "kind": "handoff_optimization",
            "_expectedRunSnapshot": run,
        }
        active = self.one_click_optimization_session(
            session_id="opts_" + "1" * 32,
            state="running",
            progress_percent=40.0,
        )
        completed = self.one_click_optimization_session(
            session_id=active["id"],
            state="completed",
        )
        service = mock.Mock()
        service.read.return_value = completed
        events = []
        with (
            mock.patch.object(self.bridge, "_ea_factory_one_click_next_action", return_value=action),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_auto_optimization_handoff",
                side_effect=lambda *_args: events.append("handoff") or active,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_sync_optimization_handoff",
                side_effect=lambda _build_id, _run_id, session: (
                    events.append("sync-" + str(session["state"])) or run
                ),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_certified_delivery_required",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_service",
                return_value=service,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_publish_terminal_report",
                side_effect=lambda *_args: events.append("publish") or {},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_finish",
                side_effect=lambda *_args, **_kwargs: events.append("finish"),
            ),
            mock.patch.object(self.bridge.time, "sleep"),
        ):
            self.bridge._ea_factory_one_click_worker("ea-build-mt5-verified")
        self.assertEqual(
            events,
            ["handoff", "sync-running", "sync-completed", "publish", "finish"],
        )
        service.read.assert_called_once_with(active["id"])

    def test_one_click_progress_reaches_100_at_factory_final_report_boundary(
        self,
    ) -> None:
        stages = [
            {"id": stage_id, "status": "completed"}
            for stage_id in self.bridge.EA_FACTORY_ONE_CLICK_STAGE_IDS
        ]
        run = {
            "status": "running",
            "currentStageId": None,
            "optimizationHandoff": {
                "progressPercent": 50.0,
            },
        }

        running = self.bridge._ea_factory_one_click_progress_projection(
            run,
            stages,
        )
        completed = self.bridge._ea_factory_one_click_progress_projection(
            {**run, "status": "completed"},
            stages,
        )

        self.assertEqual(running["progressPercent"], 100)
        self.assertNotIn("optimizationProgressPercent", running)
        self.assertEqual(completed["progressPercent"], 100)

    def test_mt5_one_click_progress_does_not_wait_for_optimizer_binding(
        self,
    ) -> None:
        stages = [
            {"id": stage_id, "status": "completed"}
            for stage_id in self.bridge.EA_FACTORY_ONE_CLICK_STAGE_IDS
        ]
        run = {
            "status": "running",
            "currentStageId": None,
            "terminalBinding": {"platform": "mt5"},
        }

        progress = self.bridge._ea_factory_one_click_progress_projection(
            run,
            stages,
        )

        self.assertEqual(progress["progressPercent"], 100)
        self.assertNotIn("optimizationProgressPercent", progress)

    def test_legacy_optimizer_failure_cannot_reduce_completed_factory_progress(
        self,
    ) -> None:
        stages = [
            {"id": stage_id, "status": "completed"}
            for stage_id in self.bridge.EA_FACTORY_ONE_CLICK_STAGE_IDS
        ]
        run = {
            "status": "failed",
            "currentStageId": None,
            "terminalBinding": {"platform": "mt5"},
            "optimizationHandoff": {
                "state": "failed",
                "progressPercent": 75.0,
            },
        }

        progress = self.bridge._ea_factory_one_click_progress_projection(
            run,
            stages,
        )

        self.assertEqual(progress["progressPercent"], 100)
        self.assertNotIn("optimizationProgressPercent", progress)

    def test_one_click_monitor_reuses_bound_session_without_duplicate_create(
        self,
    ) -> None:
        session_id = "opts_" + "7" * 32
        run = {
            "runId": "ea-run-" + "1" * 24,
            "status": "running",
            "currentStageId": None,
            "optimizationHandoff": {"sessionId": session_id},
        }
        action = {
            "kind": "monitor_optimization",
            "_expectedRunSnapshot": run,
        }
        completed = self.one_click_optimization_session(
            session_id=session_id,
            state="completed",
        )
        events = []
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_next_action",
                return_value=action,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_session_for_handoff",
                side_effect=lambda handoff: (
                    events.append("read-" + str(handoff["sessionId"]))
                    or completed
                ),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_auto_optimization_handoff",
            ) as create_session,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_sync_optimization_handoff",
                return_value=run,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_certified_delivery_required",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_publish_terminal_report",
                side_effect=lambda *_args: events.append("publish") or {},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_finish",
                side_effect=lambda *_args, **_kwargs: events.append("finish"),
            ),
        ):
            self.bridge._ea_factory_one_click_worker(
                "ea-build-mt5-verified"
            )

        create_session.assert_not_called()
        self.assertEqual(events, ["read-" + session_id, "publish", "finish"])

    def test_one_click_monitor_restarts_exact_worker_then_exposes_awaiting_state(
        self,
    ) -> None:
        session_id = "opts_" + "8" * 32
        run = {
            "runId": "ea-run-" + "2" * 24,
            "status": "running",
            "currentStageId": None,
            "optimizationHandoff": {"sessionId": session_id},
        }
        action = {
            "kind": "monitor_optimization",
            "_expectedRunSnapshot": run,
        }
        awaiting = self.one_click_optimization_session(
            session_id=session_id,
            state="awaiting_visible_terminal",
            progress_percent=65.0,
        )
        service = mock.Mock()
        service.read.return_value = awaiting

        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_next_action",
                return_value=action,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_session_for_handoff",
                return_value=awaiting,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_sync_optimization_handoff",
                return_value=run,
            ) as sync,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_certified_delivery_required",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_service",
                return_value=service,
            ),
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_optimization_worker",
                return_value=True,
            ) as start_worker,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_finish",
            ) as finish,
            mock.patch.object(self.bridge.time, "sleep"),
        ):
            self.bridge._ea_factory_one_click_worker(
                "ea-build-mt5-verified"
            )

        start_worker.assert_called_once_with(session_id)
        service.read.assert_called_once_with(session_id)
        self.assertEqual(sync.call_count, 2)
        finish.assert_called_once()
        self.assertEqual(
            finish.call_args.kwargs["status"],
            "awaiting_visible_terminal",
        )
        self.assertIsNone(finish.call_args.kwargs["failure_code"])

    def test_public_same_key_keeps_awaiting_legacy_optimizer_read_only(self) -> None:
        build_id = "ea-build-mt5-verified"
        session_id = "opts_" + "c" * 32
        request_digest = "e" * 64
        run = {
            "runId": "ea-run-" + "7" * 24,
            "idempotencyKey": "one-click-optimizer-resume-001",
            "requestDigest": request_digest,
            "status": "awaiting_visible_terminal",
            "currentStageId": None,
            "optimizationHandoff": {"sessionId": session_id},
        }
        build = {
            "id": build_id,
            "coverageStatus": "compact_current",
            "artifactKind": "expert_advisor",
            "platform": "mt5",
            "oneClickRun": run,
        }
        active = {
            "buildId": build_id,
            "activeOperation": "mt5_optimization",
            "optimizationSessionId": session_id,
            "optimizationState": "awaiting_visible_terminal",
        }

        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value={"builds": [build]},
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_request_digest",
                return_value=request_digest,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_active_worker_payload",
                return_value=active,
            ),
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ) as write_state,
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_one_click_thread",
                return_value=True,
            ) as start_worker,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_read_model",
                side_effect=lambda candidate: copy.deepcopy(
                    candidate["oneClickRun"]
                ),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_auto_optimization_handoff",
            ) as create_session,
            mock.patch.object(
                self.bridge,
                "advance_ea_factory_build",
            ) as advance_stage,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            result = self.bridge.run_ea_factory_build_one_click(
                build_id,
                {"idempotencyKey": run["idempotencyKey"]},
            )

        self.assertEqual(result["kind"], "ea_factory_legacy_optimization_history")
        self.assertFalse(result["workerStarted"])
        self.assertEqual(run["status"], "awaiting_visible_terminal")
        self.assertIsNone(run["currentStageId"])
        write_state.assert_not_called()
        start_worker.assert_not_called()
        create_session.assert_not_called()
        advance_stage.assert_not_called()

    def test_public_same_key_never_reopens_late_completed_optimizer(
        self,
    ) -> None:
        build, run, failed_session = self.late_recovery_owner_fixture(
            "d",
            started_at="2026-10-16T00:00:00Z",
        )
        build["coverageStatus"] = "compact_current"
        build["artifactKind"] = "expert_advisor"
        prepared_session = copy.deepcopy(failed_session)
        prepared_session["state"] = "collecting"
        prepared_session["attemptsByRound"] = [1]
        prepared_session["recovery"][
            "lateCompletedResultRecoveryAvailable"
        ] = False
        prepared_session["recovery"][
            "lateCompletedResultRecoveryPending"
        ] = True
        original_run_id = run["runId"]
        original_handoff = copy.deepcopy(run["optimizationHandoff"])
        state = {"builds": [build]}

        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_request_digest",
                return_value=run["requestDigest"],
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_active_worker_payload",
                return_value=None,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_late_completed_recovery_session",
                return_value=failed_session,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_prepare_late_completed_recovery",
                return_value=prepared_session,
            ) as prepare,
            mock.patch.object(
                self.bridge,
                "_ea_factory_sync_build_status",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ) as write_state,
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_one_click_thread",
                return_value=True,
            ) as start_worker,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_read_model",
                side_effect=lambda candidate: copy.deepcopy(
                    candidate["oneClickRun"]
                ),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_auto_optimization_handoff",
            ) as create_session,
            mock.patch.object(
                self.bridge,
                "advance_ea_factory_build",
            ) as advance_stage,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            result = self.bridge.run_ea_factory_build_one_click(
                build["id"],
                {"idempotencyKey": run["idempotencyKey"]},
            )

        self.assertEqual(result["kind"], "ea_factory_legacy_optimization_history")
        self.assertFalse(result["workerStarted"])
        self.assertEqual(run["runId"], original_run_id)
        self.assertEqual(run["status"], "failed")
        self.assertEqual(run["failureCode"], "one_click_optimization_failed")
        self.assertEqual(
            run["optimizationHandoff"]["sessionId"],
            failed_session["id"],
        )
        self.assertEqual(
            run["optimizationHandoff"]["boundAt"],
            original_handoff["boundAt"],
        )
        self.assertEqual(prepared_session["attemptsByRound"], [1])
        prepare.assert_not_called()
        write_state.assert_not_called()
        start_worker.assert_not_called()
        create_session.assert_not_called()
        advance_stage.assert_not_called()

    def test_completed_optimizer_finalization_retry_reuses_same_session(self) -> None:
        session_id = "opts_" + "9" * 32
        completed = self.one_click_optimization_session(
            session_id=session_id,
            state="completed",
        )
        run = {
            "runId": "ea-run-" + "3" * 24,
            "status": "running",
            "currentStageId": None,
            "optimizationHandoff": {
                "sessionId": session_id,
                "state": "completed",
            },
        }
        action = {
            "kind": "monitor_optimization",
            "_expectedRunSnapshot": run,
        }

        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_next_action",
                return_value=action,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_session_for_handoff",
                return_value=completed,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_sync_optimization_handoff",
                return_value=run,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_certified_delivery_required",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_publish_terminal_report",
                side_effect=[OSError("temporary report failure"), {}],
            ) as publish,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_finish",
            ) as finish,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_auto_optimization_handoff",
            ) as create_session,
            mock.patch.object(self.bridge, "append_audit"),
            mock.patch.object(self.bridge.time, "sleep"),
        ):
            self.bridge._ea_factory_one_click_worker(
                "ea-build-mt5-verified"
            )

        self.assertEqual(publish.call_count, 2)
        self.assertEqual(
            [call.kwargs["status"] for call in finish.call_args_list],
            ["running", "completed"],
        )
        create_session.assert_not_called()

    def test_completed_optimizer_sync_race_retries_without_cancelling_session(self) -> None:
        session_id = "opts_" + "d" * 32
        active = self.one_click_optimization_session(
            session_id=session_id,
            state="running",
            progress_percent=75.0,
        )
        completed = self.one_click_optimization_session(
            session_id=session_id,
            state="completed",
        )
        active_run = {
            "runId": "ea-run-" + "8" * 24,
            "status": "running",
            "currentStageId": None,
            "optimizationHandoff": {
                "sessionId": session_id,
                "state": "running",
            },
        }
        completed_run = copy.deepcopy(active_run)
        completed_run["optimizationHandoff"]["state"] = "completed"
        action = {
            "kind": "monitor_optimization",
            "_expectedRunSnapshot": active_run,
        }
        service = mock.Mock()
        service.read.return_value = completed

        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_next_action",
                return_value=action,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_session_for_handoff",
                side_effect=[active, completed],
            ) as bound_session,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_sync_optimization_handoff",
                side_effect=[
                    active_run,
                    OSError("temporary sync failure"),
                    completed_run,
                ],
            ) as sync,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_certified_delivery_required",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_service",
                return_value=service,
            ),
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_optimization_worker",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_publish_terminal_report",
                return_value={},
            ) as publish,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_cancel_bound_optimization",
            ) as cancel_session,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_finish",
            ) as finish,
            mock.patch.object(self.bridge, "append_audit"),
            mock.patch.object(self.bridge.time, "sleep"),
        ):
            self.bridge._ea_factory_one_click_worker(
                "ea-build-mt5-verified"
            )

        self.assertEqual(sync.call_count, 3)
        self.assertEqual(bound_session.call_count, 2)
        service.read.assert_called_once_with(session_id)
        publish.assert_called_once_with(completed)
        cancel_session.assert_not_called()
        self.assertEqual(
            [call.kwargs["status"] for call in finish.call_args_list],
            ["running", "completed"],
        )

    def test_retired_factory_handoff_fails_before_visible_ui_lock_admission(self) -> None:
        visible_lock = threading.Lock()
        visible_lock.acquire()
        request = {
            "terminalCandidateId": "mtc-mt5-selected",
            "platform": "mt5",
            "terminalSelectionRevision": 7,
            "terminalBindingDigest": "c" * 64,
        }
        try:
            with (
                mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_VISIBLE_FRONT_OFFICE_ACTION_LOCK",
                    visible_lock,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_one_click_auto_optimization_request",
                    return_value=request,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_capability_provider",
                ) as probe,
            ):
                with self.assertRaises(
                    self.bridge.OptimizationDomainError
                ) as caught:
                    self.bridge._ea_factory_one_click_auto_optimization_handoff(
                        "ea-build-mt5-verified",
                        {"runId": "ea-run-" + "4" * 24},
                    )
        finally:
            visible_lock.release()

        self.assertEqual(
            caught.exception.code,
            "factory_optimization_boundary_retired",
        )
        probe.assert_not_called()

    def test_one_click_handoff_revalidation_rejects_binding_tampering(
        self,
    ) -> None:
        run = {
            "runId": "ea-run-" + "1" * 24,
            "status": "running",
            "currentStageId": None,
        }
        build = {
            "id": "ea-build-mt5-verified",
            "platform": "mt5",
            "status": "completed",
            "oneClickRun": run,
        }
        session = self.one_click_optimization_session(
            session_id="opts_" + "2" * 32,
            state="running",
            progress_percent=25.0,
        )
        handoff = self.bridge._ea_factory_one_click_optimization_handoff_record(
            build,
            run,
            session,
        )
        self.assertEqual(
            self.bridge._ea_factory_one_click_revalidated_optimization_handoff(
                build,
                run,
                handoff,
            ),
            handoff,
        )

        tampered = copy.deepcopy(handoff)
        tampered["progressPercent"] = 101.0
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.bridge._ea_factory_one_click_revalidated_optimization_handoff(
                build,
                run,
                tampered,
            )

        service = mock.Mock()
        service.read.return_value = {**session, "requestDigest": "e" * 64}
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_service",
                return_value=service,
            ),
            self.assertRaises(self.bridge.DataIntegrityError),
        ):
            self.bridge._ea_factory_one_click_session_for_handoff(handoff)
        service.read.assert_called_once_with(session["id"])

    def test_one_click_cancel_targets_only_durably_bound_optimization(
        self,
    ) -> None:
        run = {
            "runId": "ea-run-" + "1" * 24,
            "status": "cancelling",
            "currentStageId": None,
        }
        build = {
            "id": "ea-build-mt5-verified",
            "platform": "mt5",
            "status": "completed",
            "oneClickRun": run,
        }
        active = self.one_click_optimization_session(
            session_id="opts_" + "3" * 32,
            state="running",
            progress_percent=40.0,
        )
        cancelled = self.one_click_optimization_session(
            session_id=active["id"],
            state="cancelled",
            progress_percent=40.0,
        )
        run["optimizationHandoff"] = (
            self.bridge._ea_factory_one_click_optimization_handoff_record(
                build,
                run,
                active,
            )
        )
        service = mock.Mock()
        service.read.return_value = active
        service.cancel.return_value = cancelled
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value={"builds": [build]},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_service",
                return_value=service,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_sync_optimization_handoff",
                return_value=run,
            ) as sync_handoff,
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_optimization_worker",
            ) as start_worker,
        ):
            result = self.bridge._ea_factory_one_click_cancel_bound_optimization(
                build["id"],
                run["runId"],
            )

        self.assertEqual(result["sessionId"], active["id"])
        self.assertEqual(result["state"], "cancelled")
        self.assertTrue(result["stopConfirmed"])
        service.read.assert_called_once_with(active["id"])
        service.cancel.assert_called_once_with(
            active["id"],
            reason="one_click_operator_cancelled",
            confirm_execution_stopped=True,
        )
        sync_handoff.assert_called_once_with(
            build["id"],
            run["runId"],
            cancelled,
        )
        start_worker.assert_not_called()

    def test_one_click_cancel_endpoint_combines_bound_optimizer_stop_proof(
        self,
    ) -> None:
        session_id = "opts_" + "6" * 32
        run = {
            "schemaVersion": self.bridge.EA_FACTORY_ONE_CLICK_SCHEMA_VERSION,
            "runId": "ea-run-" + "1" * 24,
            "idempotencyKey": "one-click-cancel-bound-001",
            "requestDigest": "d" * 64,
            "status": "running",
            "currentStageId": None,
            "terminalBinding": {
                "platform": "mt5",
                "candidateId": "mtc-mt5-selected",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "failureCode": None,
            "messageTh": "waiting for optimization",
            "startedAt": "2026-10-16T00:00:00Z",
            "updatedAt": "2026-10-16T00:00:00Z",
            "completedAt": None,
            "optimizationHandoff": {
                "sessionId": session_id,
                "progressPercent": 50.0,
            },
        }
        build = {
            "id": "ea-build-mt5-verified",
            "platform": "mt5",
            "status": "completed",
            "oneClickRun": run,
            "stages": [],
        }
        state = {"builds": [build]}
        cancel_result = {
            "sessionId": session_id,
            "state": "cancelled",
            "stopConfirmed": True,
        }
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_ONE_CLICK_THREADS",
                {},
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_ONE_CLICK_CANCEL_EVENTS",
                {},
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_ONE_CLICK_CANCEL_CONTEXTS",
                {},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_cancel_bound_optimization",
                return_value=cancel_result,
            ) as cancel_bound,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_session_for_handoff",
                return_value={"state": "cancelled"},
            ),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            response = self.bridge.cancel_ea_factory_build_one_click(
                build["id"],
                {
                    "runId": run["runId"],
                    "idempotencyKey": run["idempotencyKey"],
                },
            )

        cancel_bound.assert_called_once_with(build["id"], run["runId"])
        self.assertEqual(response["kind"], "ea_factory_one_click_cancelled")
        self.assertEqual(response["oneClickRun"]["status"], "cancelled")
        self.assertTrue(response["missionProcessStopConfirmed"])
        self.assertTrue(response["optimizationStopConfirmed"])
        self.assertTrue(response["ownedProcessStopConfirmed"])
        self.assertEqual(response["optimizationSessionId"], session_id)

    def test_active_worker_projection_blocks_on_durable_optimization(self) -> None:
        run = {
            "runId": "ea-run-" + "1" * 24,
            "status": "running",
            "currentStageId": None,
            "optimizationHandoff": {
                "sessionId": "opts_" + "4" * 32,
            },
        }
        build = {
            "id": "ea-build-mt5-verified",
            "sourceDisplayName": "Bound optimization",
            "oneClickRun": run,
            "stages": [],
        }
        with (
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_ONE_CLICK_THREADS",
                {},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_session_for_handoff",
                return_value={"state": "collecting"},
            ),
        ):
            busy = self.bridge._ea_factory_active_worker_payload(
                {"builds": [build]},
                [],
            )

        self.assertEqual(busy["activeOperation"], "mt5_optimization")
        self.assertEqual(
            busy["optimizationSessionId"],
            run["optimizationHandoff"]["sessionId"],
        )

    def test_restart_skips_exact_pending_legacy_optimization_cancellation(self) -> None:
        run = {
            "runId": "ea-run-" + "1" * 24,
            "status": "cancelling",
            "currentStageId": None,
            "startedAt": "2026-10-16T00:00:00Z",
            "optimizationHandoff": {
                "sessionId": "opts_" + "5" * 32,
            },
        }
        build = {
            "id": "ea-build-mt5-verified",
            "oneClickRun": run,
            "stages": [],
        }
        state = {"builds": [build]}
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
                return_value={
                    "activeOperation": "mt5_optimization",
                    "buildId": build["id"],
                    "optimizationSessionId": run["optimizationHandoff"]["sessionId"],
                    "optimizationState": "running",
                },
            ),
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_one_click_thread",
                return_value=True,
            ) as start_worker,
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ) as write_state,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            resumed = self.bridge.resume_interrupted_ea_factory_one_click_runs()

        self.assertEqual(resumed, 0)
        start_worker.assert_not_called()
        write_state.assert_not_called()

    def test_restart_does_not_prepare_late_legacy_optimizer_candidates(self) -> None:
        first_build, first_run, first_session = self.late_recovery_owner_fixture(
            "1",
            started_at="2026-10-16T00:00:00Z",
        )
        second_build, second_run, second_session = self.late_recovery_owner_fixture(
            "2",
            started_at="2026-10-16T00:01:00Z",
        )
        state = {"builds": [second_build, first_build]}

        def discover(build, _run):
            return (
                first_session
                if build["id"] == first_build["id"]
                else second_session
            )

        prepared_first = copy.deepcopy(first_session)
        prepared_first["state"] = "collecting"
        prepared_first["recovery"]["lateCompletedResultRecoveryAvailable"] = False
        prepared_first["recovery"]["lateCompletedResultRecoveryPending"] = True
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_late_completed_recovery_session",
                side_effect=discover,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_prepare_late_completed_recovery",
                return_value=prepared_first,
            ) as prepare,
            mock.patch.object(
                self.bridge,
                "_ea_factory_active_worker_payload",
                return_value=None,
            ),
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ) as write_state,
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_one_click_thread",
                return_value=True,
            ) as start_worker,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            resumed = self.bridge.resume_interrupted_ea_factory_one_click_runs()

        self.assertEqual(resumed, 0)
        prepare.assert_not_called()
        start_worker.assert_not_called()
        self.assertEqual(first_run["status"], "failed")
        self.assertEqual(
            first_run["optimizationHandoff"]["sessionId"],
            first_session["id"],
        )
        self.assertEqual(second_run["status"], "failed")
        self.assertEqual(second_run["failureCode"], "one_click_optimization_failed")
        write_state.assert_not_called()

    def test_restart_does_not_prepare_late_recovery_beside_unrelated_active_worker(
        self,
    ) -> None:
        late_build, late_run, late_session = self.late_recovery_owner_fixture(
            "3",
            started_at="2026-10-16T00:00:00Z",
        )
        unrelated_build = {
            "id": "ea-build-unrelated-active",
            "stages": [],
        }
        state = {"builds": [late_build, unrelated_build]}

        def active_for_build(single_state, _missions):
            only_build = single_state["builds"][0]
            if only_build["id"] == unrelated_build["id"]:
                return {
                    "buildId": unrelated_build["id"],
                    "activeOperation": "generate_source",
                }
            return None

        original_run = copy.deepcopy(late_run)
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_late_completed_recovery_session",
                side_effect=lambda build, _run: (
                    late_session if build["id"] == late_build["id"] else None
                ),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_prepare_late_completed_recovery",
            ) as prepare,
            mock.patch.object(
                self.bridge,
                "_ea_factory_active_worker_payload",
                side_effect=active_for_build,
            ),
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ) as write_state,
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_one_click_thread",
            ) as start_worker,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            resumed = self.bridge.resume_interrupted_ea_factory_one_click_runs()

        self.assertEqual(resumed, 0)
        prepare.assert_not_called()
        start_worker.assert_not_called()
        write_state.assert_not_called()
        self.assertEqual(late_run, original_run)

    def test_restart_skips_prepared_legacy_owner_and_resumes_ordinary_factory_run(
        self,
    ) -> None:
        ordinary_run = {
            "runId": "ea-run-" + "4" * 24,
            "status": "queued",
            "currentStageId": None,
            "startedAt": "2026-10-15T23:00:00Z",
        }
        ordinary_build = {
            "id": "ea-build-ordinary-interrupted",
            "oneClickRun": ordinary_run,
            "stages": [],
        }
        late_build, late_run, prepared_session = self.late_recovery_owner_fixture(
            "5",
            started_at="2026-10-16T00:00:00Z",
            prepared=True,
        )
        state = {"builds": [ordinary_build, late_build]}
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_late_completed_recovery_session",
                side_effect=lambda build, _run: (
                    prepared_session if build["id"] == late_build["id"] else None
                ),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_prepare_late_completed_recovery",
                return_value=prepared_session,
            ) as prepare,
            mock.patch.object(
                self.bridge,
                "_ea_factory_active_worker_payload",
                return_value=None,
            ),
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ),
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_one_click_thread",
                return_value=True,
            ) as start_worker,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            resumed = self.bridge.resume_interrupted_ea_factory_one_click_runs()

        self.assertEqual(resumed, 1)
        prepare.assert_not_called()
        start_worker.assert_called_once()
        self.assertEqual(start_worker.call_args.args[0], ordinary_build["id"])
        self.assertEqual(late_run["status"], "failed")

    def test_recovered_optimizer_worker_defers_prepared_late_one_click_owner(
        self,
    ) -> None:
        _build, _run, prepared_session = self.late_recovery_owner_fixture(
            "6",
            started_at="2026-10-16T00:00:00Z",
            prepared=True,
        )
        with mock.patch.object(
            self.bridge,
            "_load_ea_factory_state_unlocked",
        ) as load_state:
            allowed = self.bridge._ea_factory_recovered_optimization_start_allowed(
                prepared_session
            )
        self.assertFalse(allowed)
        load_state.assert_not_called()

    def test_late_recovery_requires_exact_canonical_bridge_evidence_binding(
        self,
    ) -> None:
        operation_id = "op_" + "4" * 40
        session = {
            "id": "opts_" + "7" * 32,
            "buildId": "ea-build-late-binding",
            "sourceDigest": "a" * 64,
            "baselineReportSha256": "b" * 64,
            "terminalBinding": self.terminal_binding(),
            "round": {"id": "round-01"},
            "testerSettings": {
                "symbol": "EURUSD",
                "period": "H1",
                "model": "every_tick",
                "optimizationMode": "slow_complete",
            },
            "recovery": {
                "operationId": operation_id,
                "receiptRef": "receipt_" + operation_id[3:],
            },
        }
        binding = self.late_recovery_binding_fixture(session)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with mock.patch.object(
                self.bridge,
                "EA_FACTORY_OPTIMIZATION_ROOT",
                root,
            ):
                path = self.bridge._ea_factory_optimization_binding_file(
                    session["id"],
                    session["round"]["id"],
                )
                self.assertFalse(
                    self.bridge._ea_factory_optimization_late_recovery_binding_valid(
                        session
                    )
                )
                path.write_text(
                    json.dumps(
                        binding,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    encoding="utf-8",
                )
                self.assertTrue(
                    self.bridge._ea_factory_optimization_late_recovery_binding_valid(
                        session
                    )
                )

                adversarial = (
                    ("sessionId", "opts_" + "8" * 32),
                    ("operationId", "op_" + "9" * 40),
                    ("roundId", "round-02"),
                    ("buildId", "ea-build-other"),
                    ("sourceDigest", "c" * 64),
                    ("baselineReportSha256", "d" * 64),
                    ("terminalCandidateId", "mtc-other"),
                    ("terminalSelectionRevision", 8),
                    ("terminalBindingDigest", "e" * 64),
                    ("liveTrading", True),
                    ("testShutdownTerminal", True),
                )
                for field, value in adversarial:
                    mutated = copy.deepcopy(binding)
                    mutated[field] = value
                    path.write_text(
                        json.dumps(
                            mutated,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                        encoding="utf-8",
                    )
                    self.assertFalse(
                        self.bridge._ea_factory_optimization_late_recovery_binding_valid(
                            session
                        ),
                        field,
                    )

                # Restore the exact binding, then prove the public service
                # receipt identity is independently required as well.
                path.write_text(
                    json.dumps(
                        binding,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    encoding="utf-8",
                )
                wrong_receipt = copy.deepcopy(session)
                wrong_receipt["recovery"]["receiptRef"] = "receipt_wrong"
                self.assertFalse(
                    self.bridge._ea_factory_optimization_late_recovery_binding_valid(
                        wrong_receipt
                    )
                )

    def test_restart_cancel_monitor_starts_with_pre_signalled_event_and_context(
        self,
    ) -> None:
        created = []

        class FakeThread:
            def __init__(self, *, target, args, name, daemon):
                self.target = target
                self.args = args
                self.name = name
                self.daemon = daemon
                self.started = False
                created.append(self)

            def is_alive(self):
                return False

            def start(self):
                self.started = True

        build_id = "ea-build-mt5-verified"
        run = {"runId": "ea-run-" + "1" * 24}
        with (
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_ONE_CLICK_THREADS",
                {},
            ) as threads,
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_ONE_CLICK_CANCEL_EVENTS",
                {},
            ) as events,
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_ONE_CLICK_CANCEL_CONTEXTS",
                {},
            ) as contexts,
            mock.patch.object(self.bridge.threading, "Thread", FakeThread),
            mock.patch.object(
                self.bridge,
                "_invalidate_ea_factory_read_model_cache",
            ),
        ):
            started = self.bridge._start_ea_factory_one_click_thread(
                build_id,
                expected_run_snapshot=run,
                cancel_requested=True,
            )

            self.assertTrue(started)
            self.assertTrue(created[0].started)
            self.assertIs(threads[build_id], created[0])
            self.assertTrue(events[build_id].is_set())
            self.assertEqual(contexts[build_id]["runId"], run["runId"])
            self.assertTrue(
                contexts[build_id]["missionProcessStopConfirmed"]
            )
            self.assertFalse(
                contexts[build_id]["optimizationStopConfirmed"]
            )
            self.assertFalse(contexts[build_id]["ownedProcessStopConfirmed"])

    def test_certified_one_click_waits_for_completed_optimization_before_delivery(self) -> None:
        run = {
            "runId": "ea-run-" + "1" * 24,
            "status": "running",
            "currentStageId": None,
        }
        action = {"kind": "handoff_optimization", "_expectedRunSnapshot": run}
        active = {
            "id": "opts_" + "1" * 32,
            "buildId": "ea-build-mt5-verified",
            "state": "running",
        }
        completed = {**active, "state": "completed", "requestDigest": "d" * 64}
        service = mock.Mock()
        service.read.return_value = completed
        events = []
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_next_action",
                return_value=action,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_auto_optimization_handoff",
                side_effect=lambda *_args: events.append("handoff") or active,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_sync_optimization_handoff",
                return_value=run,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_certified_delivery_required",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_service",
                return_value=service,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_publish_terminal_report",
                side_effect=lambda *_args: events.append("publish")
                or {
                    "missionId": "mission-eaopt-" + "2" * 24,
                    "reportId": "report-eaopt-" + "3" * 24,
                    "state": "completed",
                },
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_commit_certified_customer_delivery",
                side_effect=lambda *_args: events.append("delivery") or {},
            ) as delivery,
            mock.patch.object(self.bridge, "_ea_factory_one_click_finish") as finish,
            mock.patch.object(self.bridge.time, "sleep"),
        ):
            self.bridge._ea_factory_one_click_worker("ea-build-mt5-verified")

        self.assertEqual(events, ["handoff", "publish", "delivery"])
        service.read.assert_called_once_with(active["id"])
        delivery.assert_called_once()
        finish.assert_not_called()

    def test_late_completed_one_click_monitor_finishes_via_correction_without_start(
        self,
    ) -> None:
        session, _binding, base_report, base_mission = (
            self.late_completed_publication_fixture()
        )
        run = {
            "runId": "ea-run-" + "e" * 24,
            "status": "running",
            "currentStageId": None,
            "failureCode": None,
            "optimizationHandoff": {"sessionId": session["id"]},
        }
        action = {
            "kind": "monitor_optimization",
            "_expectedRunSnapshot": copy.deepcopy(run),
        }
        base_digest = self.bridge._report_snapshot_digest(base_report)
        suffix = self.bridge.payload_digest(
            "ea-factory-optimization-late-report-correction-v1",
            session["id"],
            base_digest,
        )[:24]
        correction = {
            "missionId": f"mission-eaoptfix-{suffix}",
            "reportId": f"report-eaoptfix-{suffix}",
            "state": "completed",
            "supersedesMissionId": base_mission["id"],
            "supersedesReportId": base_report["id"],
            "supersedesReportSha256": base_digest,
        }
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_next_action",
                return_value=action,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_session_for_handoff",
                return_value=session,
            ) as read_bound,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_sync_optimization_handoff",
                return_value=run,
            ) as sync,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_certified_delivery_required",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_publish_terminal_report",
                return_value=correction,
            ) as publish,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_auto_optimization_handoff",
            ) as create_session,
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_optimization_worker",
            ) as start_optimizer,
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_service",
            ) as optimization_service,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_finish",
            ) as finish,
        ):
            self.bridge._ea_factory_one_click_worker(session["buildId"])

        read_bound.assert_called_once_with(run["optimizationHandoff"])
        sync.assert_called_once_with(
            session["buildId"],
            run["runId"],
            session,
        )
        publish.assert_called_once_with(session)
        finish.assert_called_once_with(
            session["buildId"],
            expected_run_snapshot=run,
            status="completed",
            current_stage_id=None,
            failure_code=None,
            message_th=mock.ANY,
        )
        create_session.assert_not_called()
        start_optimizer.assert_not_called()
        optimization_service.assert_not_called()

    def test_certified_one_click_terminal_failure_never_delivers(self) -> None:
        run = {
            "runId": "ea-run-" + "1" * 24,
            "status": "running",
            "currentStageId": None,
        }
        action = {"kind": "handoff_optimization", "_expectedRunSnapshot": run}
        active = {
            "id": "opts_" + "1" * 32,
            "buildId": "ea-build-mt5-verified",
            "state": "running",
        }
        failed = {**active, "state": "failed"}
        service = mock.Mock()
        service.read.return_value = failed
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_next_action",
                return_value=action,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_auto_optimization_handoff",
                return_value=active,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_sync_optimization_handoff",
                return_value=run,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_certified_delivery_required",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_service",
                return_value=service,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_commit_certified_customer_delivery",
            ) as delivery,
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_publish_terminal_report",
            ) as publish,
            mock.patch.object(self.bridge, "_ea_factory_one_click_finish") as finish,
        ):
            self.bridge._ea_factory_one_click_worker("ea-build-mt5-verified")

        delivery.assert_not_called()
        publish.assert_not_called()
        finish.assert_called_once()
        self.assertEqual(finish.call_args.kwargs["status"], "failed")
        self.assertEqual(
            finish.call_args.kwargs["failure_code"],
            "one_click_optimization_failed",
        )

    def test_certified_one_click_terminal_cancelled_never_delivers(self) -> None:
        run = {
            "runId": "ea-run-" + "1" * 24,
            "status": "running",
            "currentStageId": None,
        }
        action = {"kind": "handoff_optimization", "_expectedRunSnapshot": run}
        active = {
            "id": "opts_" + "1" * 32,
            "buildId": "ea-build-mt5-verified",
            "state": "running",
        }
        service = mock.Mock()
        service.read.return_value = {**active, "state": "cancelled"}
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_next_action",
                return_value=action,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_auto_optimization_handoff",
                return_value=active,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_sync_optimization_handoff",
                return_value=run,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_certified_delivery_required",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_service",
                return_value=service,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_commit_certified_customer_delivery",
            ) as delivery,
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_publish_terminal_report",
            ) as publish,
            mock.patch.object(self.bridge, "_ea_factory_one_click_finish") as finish,
            mock.patch.object(self.bridge.time, "sleep"),
        ):
            self.bridge._ea_factory_one_click_worker("ea-build-mt5-verified")

        service.read.assert_called_once_with(active["id"])
        delivery.assert_not_called()
        publish.assert_not_called()
        finish.assert_called_once()
        self.assertEqual(finish.call_args.kwargs["status"], "failed")
        self.assertEqual(
            finish.call_args.kwargs["failure_code"],
            "one_click_optimization_cancelled",
        )

    def test_certified_one_click_cancel_signal_never_delivers(self) -> None:
        run = {
            "runId": "ea-run-" + "1" * 24,
            "status": "running",
            "currentStageId": None,
        }
        action = {"kind": "handoff_optimization", "_expectedRunSnapshot": run}
        active = {
            "id": "opts_" + "1" * 32,
            "buildId": "ea-build-mt5-verified",
            "state": "running",
        }
        cancel_event = mock.Mock()
        cancel_event.is_set.side_effect = [False, False, True]
        cancel_event.wait.return_value = True
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_next_action",
                return_value=action,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_auto_optimization_handoff",
                return_value=active,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_sync_optimization_handoff",
                return_value=run,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_certified_delivery_required",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_wait_for_bound_optimization_cancel",
                return_value=True,
            ) as wait_cancel,
            mock.patch.object(
                self.bridge,
                "_ea_factory_commit_certified_customer_delivery",
            ) as delivery,
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_publish_terminal_report",
            ) as publish,
            mock.patch.object(self.bridge, "_ea_factory_one_click_finish") as finish,
        ):
            self.bridge._ea_factory_one_click_worker(
                "ea-build-mt5-verified",
                cancel_event=cancel_event,
            )

        delivery.assert_not_called()
        publish.assert_not_called()
        finish.assert_not_called()
        wait_cancel.assert_called_once_with(
            "ea-build-mt5-verified",
            run["runId"],
            deadline=None,
        )
        cancel_event.wait.assert_called_once_with(
            self.bridge.EA_FACTORY_ONE_CLICK_POLL_SECONDS
        )

    def test_certified_one_click_timeout_never_delivers(self) -> None:
        run = {
            "runId": "ea-run-" + "1" * 24,
            "status": "running",
            "currentStageId": None,
        }
        action = {"kind": "handoff_optimization", "_expectedRunSnapshot": run}
        active = {
            "id": "opts_" + "1" * 32,
            "buildId": "ea-build-mt5-verified",
            "state": "running",
        }
        cancelled = {**active, "state": "cancelled"}
        service = mock.Mock()
        service.cancel.return_value = cancelled
        # Worker deadline, outer loop entry, inner loop exit.
        monotonic_values = iter([100.0, 100.0, 20000.0])
        with (
            mock.patch.object(
                self.bridge.time,
                "monotonic",
                side_effect=lambda: next(monotonic_values),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_next_action",
                return_value=action,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_auto_optimization_handoff",
                return_value=active,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_sync_optimization_handoff",
                return_value=run,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_certified_delivery_required",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_service",
                return_value=service,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_commit_certified_customer_delivery",
            ) as delivery,
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_publish_terminal_report",
            ) as publish,
            mock.patch.object(self.bridge, "_ea_factory_one_click_finish") as finish,
        ):
            self.bridge._ea_factory_one_click_worker("ea-build-mt5-verified")

        delivery.assert_not_called()
        publish.assert_not_called()
        finish.assert_called_once()
        self.assertEqual(finish.call_args.kwargs["status"], "failed")
        self.assertEqual(finish.call_args.kwargs["failure_code"], "one_click_timeout")
        service.cancel.assert_called_once_with(
            active["id"],
            reason="one_click_timeout",
            confirm_execution_stopped=True,
        )

    def test_timeout_keeps_exact_cancel_monitor_until_active_session_stops(self) -> None:
        session_id = "opts_" + "a" * 32
        run = {
            "runId": "ea-run-" + "5" * 24,
            "status": "running",
            "currentStageId": None,
            "optimizationHandoff": {
                "sessionId": session_id,
                "state": "running",
            },
        }
        terminal_run = copy.deepcopy(run)
        terminal_run["optimizationHandoff"]["state"] = "cancelled"
        action = {"kind": "handoff_optimization", "_expectedRunSnapshot": run}
        active = {
            "id": session_id,
            "buildId": "ea-build-mt5-verified",
            "state": "running",
        }
        service = mock.Mock()
        service.cancel.return_value = active
        monotonic_values = iter([100.0, 100.0, 20000.0])

        with (
            mock.patch.object(
                self.bridge.time,
                "monotonic",
                side_effect=lambda: next(monotonic_values),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_next_action",
                return_value=action,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_auto_optimization_handoff",
                return_value=active,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_sync_optimization_handoff",
                return_value=run,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_certified_delivery_required",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_service",
                return_value=service,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_cancel_bound_optimization",
                return_value={
                    "sessionId": session_id,
                    "state": "cancelled",
                    "stopConfirmed": True,
                    "runSnapshot": terminal_run,
                },
            ) as cancel_monitor,
            mock.patch.object(
                self.bridge,
                "_ea_factory_commit_certified_customer_delivery",
            ) as delivery,
            mock.patch.object(
                self.bridge,
                "_ea_factory_optimization_publish_terminal_report",
            ) as publish,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_finish",
            ) as finish,
        ):
            self.bridge._ea_factory_one_click_worker(
                "ea-build-mt5-verified"
            )

        delivery.assert_not_called()
        publish.assert_not_called()
        self.assertEqual(
            [call.kwargs["status"] for call in finish.call_args_list],
            ["cancelling", "failed"],
        )
        self.assertEqual(
            finish.call_args_list[-1].kwargs["failure_code"],
            "one_click_timeout",
        )
        service.cancel.assert_called_once_with(
            session_id,
            reason="one_click_timeout",
            confirm_execution_stopped=True,
        )
        cancel_monitor.assert_called_once_with(
            "ea-build-mt5-verified",
            run["runId"],
            reason="one_click_timeout",
        )

    def test_coordinator_error_stops_active_optimizer_before_terminal_failure(self) -> None:
        session_id = "opts_" + "b" * 32
        run = {
            "runId": "ea-run-" + "6" * 24,
            "status": "running",
            "currentStageId": None,
            "optimizationHandoff": {
                "sessionId": session_id,
                "state": "running",
            },
        }
        terminal_run = copy.deepcopy(run)
        terminal_run["optimizationHandoff"]["state"] = "cancelled"
        action = {
            "kind": "monitor_optimization",
            "_expectedRunSnapshot": run,
        }

        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_next_action",
                return_value=action,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_session_for_handoff",
                side_effect=RuntimeError("coordinator read failed"),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_cancel_bound_optimization",
                return_value={
                    "sessionId": session_id,
                    "state": "cancelled",
                    "stopConfirmed": True,
                    "runSnapshot": terminal_run,
                },
            ) as cancel_session,
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_finish",
            ) as finish,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            self.bridge._ea_factory_one_click_worker(
                "ea-build-mt5-verified"
            )

        self.assertEqual(
            [call.kwargs["status"] for call in finish.call_args_list],
            ["cancelling", "failed"],
        )
        self.assertEqual(
            finish.call_args_list[-1].kwargs["failure_code"],
            "one_click_coordinator_failed",
        )
        cancel_session.assert_called_once_with(
            "ea-build-mt5-verified",
            run["runId"],
            reason="one_click_coordinator_failed",
        )

    def test_certified_customer_delivery_contract_revalidates_both_reports(self) -> None:
        run = {
            "runId": "ea-run-" + "1" * 24,
            "status": "running",
            "currentStageId": None,
        }
        result_rows = [
            {"pass": pass_number, "trades": 10 + pass_number}
            for pass_number in range(1, 5)
        ]
        certified_round = {
            "index": 0,
            "number": 1,
            "count": 1,
            "id": "round-01",
            "combinationCount": 4,
        }
        certified_progress = {
            "roundNumber": 1,
            "roundCount": 1,
            "passCount": 4,
            "returnedPassCount": 4,
            "percent": 100.0,
            "rowsTruncated": False,
        }
        certified_ranges = [
            {
                "inputName": "StopLossPips",
                "start": "10",
                "step": "10",
                "stop": "20",
                "enabled": True,
                "sourceDefault": "30",
                "valueKind": "decimal",
            },
            {
                "inputName": "TakeProfitPips",
                "start": "20",
                "step": "20",
                "stop": "40",
                "enabled": True,
                "sourceDefault": "60",
                "valueKind": "decimal",
            },
        ]
        session = {
            "id": "opts_" + "2" * 32,
            "buildId": "ea-build-mt5-verified",
            "state": "completed",
            "requestDigest": "3" * 64,
            "sourceDigest": "4" * 64,
            "round": copy.deepcopy(certified_round),
            "progress": copy.deepcopy(certified_progress),
            "evidence": [{
                "roundId": "round-01",
                "roundNumber": 1,
                "combinationCount": 4,
                "passCount": 4,
                "returnedPassCount": 4,
                "rowsTruncated": False,
                "publicResultRowsTruncated": False,
                "analyzed": True,
                "resultRows": copy.deepcopy(result_rows),
                "resultRowsSha256": "a" * 64,
            }],
        }
        _optimization_mission_id, optimization_report_id = (
            self.bridge._ea_factory_optimization_terminal_report_ids(session["id"])
        )
        final_report_id = "report-eaf-" + "5" * 24
        final_stage = {
            "id": "final_report",
            "status": "completed",
            "missionId": "mission-eaf-" + "6" * 24,
            "reportId": final_report_id,
            "evidenceVerified": True,
            "summaryDigest": "7" * 64,
            "artifactManifestDigest": "8" * 64,
            "auditLineageId": "ea-lineage-" + "9" * 24,
        }
        build = {
            "id": session["buildId"],
            "platform": "mt5",
            "status": "completed",
            "oneClickRun": run,
            "stages": [final_stage],
        }
        final_report = {
            "id": final_report_id,
            "type": "ea_build_report",
            "status": "ready",
            "metrics": {
                "artifactManifestDigest": final_stage["artifactManifestDigest"],
                "auditLineageId": final_stage["auditLineageId"],
                "eaFactoryFinalSummary": {
                    "buildId": build["id"],
                    "immutable": True,
                    "executionEvidence": {
                        "compile": {"zeroErrors": True, "zeroWarnings": True},
                        "backtest": {
                            "visualMode": True,
                            "buyTradeCount": 3,
                            "sellTradeCount": 2,
                        },
                    },
                },
            },
        }
        optimization_report = {
            "id": optimization_report_id,
            "type": "ea_experiment_report",
            "linkedMissionId": _optimization_mission_id,
            "status": "ready",
            "metrics": {
                "optimizationSession": {
                    "id": session["id"],
                    "buildId": build["id"],
                    "state": "completed",
                    "requestDigest": session["requestDigest"],
                    "sourceDigest": session["sourceDigest"],
                    "round": copy.deepcopy(certified_round),
                    "progress": copy.deepcopy(certified_progress),
                },
                "plan": {"parameterRanges": copy.deepcopy(certified_ranges)},
                "results": {
                    "passCount": 4,
                    "returnedPassCount": 4,
                    "storedPassRowCount": 4,
                    "allPassRowsSha256": "a" * 64,
                    "allPassRows": copy.deepcopy(result_rows),
                    "allPassRowsTruncated": False,
                },
            },
            "executionEvidence": {
                "mtExecutionVerified": True,
                "optimizationProofVerified": True,
            },
        }
        publication = {
            "missionId": _optimization_mission_id,
            "reportId": optimization_report_id,
            "state": "completed",
        }
        with tempfile.TemporaryDirectory() as temporary:
            report_root = Path(temporary)
            (report_root / f"{final_report_id}.json").write_text(
                json.dumps(final_report),
                encoding="utf-8",
            )
            optimization_path = report_root / f"{optimization_report_id}.json"
            optimization_path.write_text(
                json.dumps(optimization_report),
                encoding="utf-8",
            )
            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", report_root),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_bidirectional_ema_smoke_required",
                    return_value=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_path_is_link_or_reparse",
                    return_value=False,
                ),
            ):
                contract = (
                    self.bridge._ea_factory_certified_customer_delivery_contract(
                        build,
                        run,
                        session,
                        publication,
                    )
                )
                self.assertTrue(contract["immutable"])
                self.assertTrue(contract["verification"]["buyAndSellObserved"])
                self.assertEqual(
                    contract["optimization"]["reportId"],
                    optimization_report_id,
                )

                optimization_report["metrics"]["optimizationSession"][
                    "requestDigest"
                ] = "f" * 64
                optimization_path.write_text(
                    json.dumps(optimization_report),
                    encoding="utf-8",
                )
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._ea_factory_certified_customer_delivery_contract(
                        build,
                        run,
                        session,
                        publication,
                    )

    def test_certified_delivery_accepts_only_exact_late_report_correction_lineage(
        self,
    ) -> None:
        session, binding, base_report, base_mission = (
            self.late_completed_publication_fixture()
        )
        run = {
            "runId": "ea-run-" + "e" * 24,
            "status": "running",
            "currentStageId": None,
        }
        final_report_id = "report-eaf-" + "f" * 24
        final_stage = {
            "id": "final_report",
            "status": "completed",
            "missionId": "mission-eaf-" + "f" * 24,
            "reportId": final_report_id,
            "evidenceVerified": True,
            "summaryDigest": "7" * 64,
            "artifactManifestDigest": "8" * 64,
            "auditLineageId": "ea-lineage-" + "9" * 24,
        }
        build = {
            "id": session["buildId"],
            "platform": "mt5",
            "status": "completed",
            "oneClickRun": run,
            "stages": [final_stage],
        }
        final_report = {
            "id": final_report_id,
            "type": "ea_build_report",
            "status": "ready",
            "metrics": {
                "artifactManifestDigest": final_stage["artifactManifestDigest"],
                "auditLineageId": final_stage["auditLineageId"],
                "eaFactoryFinalSummary": {
                    "buildId": build["id"],
                    "immutable": True,
                    "executionEvidence": {
                        "compile": {"zeroErrors": True, "zeroWarnings": True},
                        "backtest": {
                            "visualMode": True,
                            "buyTradeCount": 2,
                            "sellTradeCount": 2,
                        },
                    },
                },
            },
        }
        base_digest = self.bridge._report_snapshot_digest(base_report)
        correction_suffix = self.bridge.payload_digest(
            "ea-factory-optimization-late-report-correction-v1",
            session["id"],
            base_digest,
        )[:24]
        correction_report_id = f"report-eaoptfix-{correction_suffix}"
        correction_mission_id = f"mission-eaoptfix-{correction_suffix}"
        result_rows = copy.deepcopy(session["evidence"][0]["resultRows"])
        correction_report = {
            "id": correction_report_id,
            "type": "ea_experiment_report",
            "linkedMissionId": correction_mission_id,
            "status": "ready",
            "metrics": {
                "optimizationSession": {
                    "id": session["id"],
                    "buildId": session["buildId"],
                    "state": "completed",
                    "requestDigest": session["requestDigest"],
                    "sourceDigest": session["sourceDigest"],
                    "round": copy.deepcopy(session["round"]),
                    "progress": copy.deepcopy(session["progress"]),
                },
                "plan": {
                    "parameterRanges": copy.deepcopy(
                        binding["optimizationRanges"]
                    )
                },
                "results": {
                    "passCount": 4,
                    "returnedPassCount": 4,
                    "storedPassRowCount": 4,
                    "allPassRowsSha256": session["evidence"][0][
                        "resultRowsSha256"
                    ],
                    "allPassRows": result_rows,
                    "allPassRowsTruncated": False,
                },
                "reportCorrection": {
                    "schemaVersion": (
                        "ea-factory-optimization-report-correction-v1"
                    ),
                    "supersedesReportId": base_report["id"],
                    "supersedesMissionId": base_mission["id"],
                    "supersedesReportSha256": base_digest,
                    "recoveryProof": "completed_late_discarded",
                    "recoveryFailureCode": "session_deadline_exceeded",
                },
            },
            "executionEvidence": {
                "mtExecutionVerified": True,
                "optimizationProofVerified": True,
            },
        }
        publication = {
            "missionId": correction_mission_id,
            "reportId": correction_report_id,
            "state": "completed",
            "supersedesMissionId": base_mission["id"],
            "supersedesReportId": base_report["id"],
            "supersedesReportSha256": base_digest,
        }

        with tempfile.TemporaryDirectory() as temporary:
            report_root = Path(temporary)
            final_path = report_root / f"{final_report_id}.json"
            base_path = report_root / f"{base_report['id']}.json"
            correction_path = report_root / f"{correction_report_id}.json"

            def restore_reports() -> None:
                final_path.write_text(json.dumps(final_report), encoding="utf-8")
                base_path.write_text(json.dumps(base_report), encoding="utf-8")
                correction_path.write_text(
                    json.dumps(correction_report),
                    encoding="utf-8",
                )

            restore_reports()
            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", report_root),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_bidirectional_ema_smoke_required",
                    return_value=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_path_is_link_or_reparse",
                    return_value=False,
                ),
            ):
                contract = (
                    self.bridge._ea_factory_certified_customer_delivery_contract(
                        build,
                        run,
                        session,
                        publication,
                    )
                )
                self.assertEqual(
                    contract["optimization"]["reportId"],
                    correction_report_id,
                )

                base_path.unlink()
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._ea_factory_certified_customer_delivery_contract(
                        build,
                        run,
                        session,
                        publication,
                    )

                restore_reports()
                tampered_base = copy.deepcopy(base_report)
                tampered_base["metrics"]["optimizationSession"][
                    "buildId"
                ] = "ea-build-other"
                base_path.write_text(json.dumps(tampered_base), encoding="utf-8")
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._ea_factory_certified_customer_delivery_contract(
                        build,
                        run,
                        session,
                        publication,
                    )

                restore_reports()
                tampered_correction = copy.deepcopy(correction_report)
                tampered_correction["metrics"]["reportCorrection"][
                    "supersedesReportSha256"
                ] = "0" * 64
                correction_path.write_text(
                    json.dumps(tampered_correction),
                    encoding="utf-8",
                )
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._ea_factory_certified_customer_delivery_contract(
                        build,
                        run,
                        session,
                        publication,
                    )

                restore_reports()
                missing_digest_publication = copy.deepcopy(publication)
                missing_digest_publication.pop("supersedesReportSha256")
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._ea_factory_certified_customer_delivery_contract(
                        build,
                        run,
                        session,
                        missing_digest_publication,
                    )

    def test_certified_four_pass_evidence_rejects_partial_or_truncated_grid(self) -> None:
        rows = [{"pass": value} for value in range(1, 5)]
        round_row = {
            "index": 0,
            "number": 1,
            "count": 1,
            "id": "round-01",
            "combinationCount": 4,
        }
        progress = {
            "roundNumber": 1,
            "roundCount": 1,
            "passCount": 4,
            "returnedPassCount": 4,
            "percent": 100.0,
            "rowsTruncated": False,
        }
        session = {
            "round": copy.deepcopy(round_row),
            "progress": copy.deepcopy(progress),
            "evidence": [{
                "roundId": "round-01",
                "roundNumber": 1,
                "combinationCount": 4,
                "passCount": 4,
                "returnedPassCount": 4,
                "rowsTruncated": False,
                "publicResultRowsTruncated": False,
                "analyzed": True,
                "resultRows": copy.deepcopy(rows),
                "resultRowsSha256": "a" * 64,
            }],
        }
        metrics = {
            "optimizationSession": {
                "round": copy.deepcopy(round_row),
                "progress": copy.deepcopy(progress),
            },
            "plan": {
                "parameterRanges": [
                    {
                        "inputName": "StopLossPips",
                        "start": "10",
                        "step": "10",
                        "stop": "20",
                        "enabled": True,
                        "sourceDefault": "30",
                        "valueKind": "decimal",
                    },
                    {
                        "inputName": "TakeProfitPips",
                        "start": "20",
                        "step": "20",
                        "stop": "40",
                        "enabled": True,
                        "sourceDefault": "60",
                        "valueKind": "decimal",
                    },
                ]
            },
            "results": {
                "passCount": 4,
                "returnedPassCount": 4,
                "storedPassRowCount": 4,
                "allPassRowsSha256": "a" * 64,
                "allPassRows": copy.deepcopy(rows),
                "allPassRowsTruncated": False,
            },
        }
        self.assertTrue(
            self.bridge._ea_factory_certified_ema_four_pass_evidence_valid(
                session,
                metrics,
            )
        )

        mutations = (
            ("live_pass_count", lambda s, _m: s["progress"].update(passCount=3)),
            (
                "live_returned_count",
                lambda s, _m: s["evidence"][0].update(returnedPassCount=3),
            ),
            (
                "live_combination_count",
                lambda s, _m: s["round"].update(combinationCount=3),
            ),
            (
                "live_rows_truncated",
                lambda s, _m: s["evidence"][0].update(rowsTruncated=True),
            ),
            (
                "public_rows_truncated",
                lambda s, _m: s["evidence"][0].update(
                    publicResultRowsTruncated=True
                ),
            ),
            (
                "stored_pass_count",
                lambda _s, m: m["results"].update(passCount=3),
            ),
            (
                "stored_rows_truncated",
                lambda _s, m: m["results"].update(
                    allPassRowsTruncated=True
                ),
            ),
            (
                "wrong_ranges",
                lambda _s, m: m["plan"]["parameterRanges"][0].update(
                    stop="30"
                ),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                mutated_session = copy.deepcopy(session)
                mutated_metrics = copy.deepcopy(metrics)
                mutate(mutated_session, mutated_metrics)
                self.assertFalse(
                    self.bridge._ea_factory_certified_ema_four_pass_evidence_valid(
                        mutated_session,
                        mutated_metrics,
                    )
                )

    def test_certified_customer_delivery_completes_run_without_changing_build_status(self) -> None:
        run = {
            "runId": "ea-run-" + "1" * 24,
            "status": "running",
            "currentStageId": None,
        }
        build = {
            "id": "ea-build-mt5-verified",
            "platform": "mt5",
            "status": "completed",
            "oneClickRun": run,
            "stages": [{"id": "final_report", "status": "completed"}],
        }
        state = {"builds": [build]}
        session = {
            "id": "opts_" + "2" * 32,
            "buildId": build["id"],
            "state": "completed",
        }
        publication = {"state": "completed"}
        contract = {
            "schemaVersion": "ea-factory-certified-customer-delivery-v1",
            "buildId": build["id"],
            "immutable": True,
        }
        mission_id, report_id = self.bridge._ea_factory_certified_customer_delivery_ids(
            build["id"],
            run["runId"],
            session["id"],
        )
        mission = {"id": mission_id, "status": "running", "reportIds": []}
        stored_states = []

        with tempfile.TemporaryDirectory() as temporary:
            report_root = Path(temporary)

            def create_report(payload, **_kwargs):
                timestamp = "2026-10-16T00:00:00+00:00"
                report = {
                    **payload,
                    "safety": {
                        "containsSecret": False,
                        "publicShareable": False,
                    },
                    "createdAt": timestamp,
                    "updatedAt": timestamp,
                }
                self.bridge.write_json(report_root / f"{report_id}.json", report)
                return report

            def complete_mission(row, report, *_args, **_kwargs):
                row["status"] = "completed"
                row["reportIds"] = [report["id"]]

            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", report_root),
                mock.patch.object(
                    self.bridge,
                    "_load_ea_factory_state_unlocked",
                    return_value=state,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_certified_customer_delivery_contract",
                    return_value=contract,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_success_record_snapshot",
                    return_value={"missionIndex": None, "mission": None, "report": None},
                ),
                mock.patch.object(
                    self.bridge,
                    "create_mission",
                    return_value=mission,
                ),
                mock.patch.object(
                    self.bridge,
                    "create_report",
                    side_effect=create_report,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_complete_local_mission",
                    side_effect=complete_mission,
                ),
                mock.patch.object(
                    self.bridge,
                    "find_mission",
                    side_effect=lambda value: mission if value == mission_id else None,
                ),
                mock.patch.object(
                    self.bridge,
                    "_write_ea_factory_state_unlocked",
                    side_effect=lambda value: stored_states.append(copy.deepcopy(value)),
                ),
                mock.patch.object(self.bridge, "append_audit"),
            ):
                result = self.bridge._ea_factory_commit_certified_customer_delivery(
                    build["id"],
                    run,
                    session,
                    publication,
                )

        self.assertEqual(result["reportId"], report_id)
        self.assertEqual(stored_states[-1]["builds"][0]["status"], "completed")
        self.assertEqual(
            stored_states[-1]["builds"][0]["stages"],
            [{"id": "final_report", "status": "completed"}],
        )
        self.assertEqual(
            stored_states[-1]["builds"][0]["oneClickRun"]["status"],
            "completed",
        )

    def test_one_click_worker_defers_busy_handoff_without_false_completion(self) -> None:
        run = {
            "runId": "oneclick-run-001",
            "status": "running",
            "currentStageId": None,
        }
        action = {"kind": "handoff_optimization", "_expectedRunSnapshot": run}
        with (
            mock.patch.object(self.bridge, "_ea_factory_one_click_next_action", return_value=action),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_auto_optimization_handoff",
                side_effect=self.bridge.OptimizationDomainError(
                    "optimization_busy", "busy", status=409
                ),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_defer_optimization_handoff",
                return_value=True,
            ) as defer,
            mock.patch.object(self.bridge, "_ea_factory_one_click_finish") as finish,
        ):
            self.bridge._ea_factory_one_click_worker("ea-build-mt5-verified")
        defer.assert_called_once()
        finish.assert_not_called()

    def test_legacy_deferred_handoff_is_read_only_and_not_resumable(self) -> None:
        now = "2026-10-13T00:00:00Z"
        build = {
            "id": "ea-build-mt5-verified",
            "status": "completed",
            "platform": "mt5",
            "artifactKind": "expert_advisor",
            "createRequestDigest": "a" * 64,
            "sourceRecordDigest": "b" * 64,
            "stages": [],
        }
        run = {
            "schemaVersion": self.bridge.EA_FACTORY_ONE_CLICK_SCHEMA_VERSION,
            "runId": "ea-run-" + "1" * 24,
            "idempotencyKey": "oneclick-resume-001",
            "requestDigest": self.bridge._ea_factory_one_click_request_digest(build),
            "status": "running",
            "currentStageId": None,
            "terminalBinding": {
                "platform": "mt5",
                "candidateId": "mtc-mt5-selected",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "failureCode": None,
            "messageTh": "กำลังส่งต่อ Optimization",
            "startedAt": now,
            "updatedAt": now,
            "completedAt": None,
        }
        build["oneClickRun"] = run
        state = {"builds": [build]}
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_build_current_stage_id",
                return_value=None,
            ),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            deferred = self.bridge._ea_factory_one_click_defer_optimization_handoff(
                build["id"],
                expected_run_snapshot=copy.deepcopy(run),
                reason_code="optimization_busy",
            )

        self.assertTrue(deferred)
        write.assert_called_once_with(state)
        persisted = build["oneClickRun"]
        self.assertEqual(persisted["status"], "queued")
        self.assertIsNone(persisted["currentStageId"])
        self.assertEqual(persisted["failureCode"], "optimization_busy")
        self.assertIsNone(persisted["completedAt"])
        self.assertEqual(
            self.bridge._ea_factory_revalidated_one_click_run(build),
            persisted,
        )
        with mock.patch.object(
            self.bridge,
            "_ea_factory_file_catalog",
            return_value=[],
        ):
            read_model = self.bridge._ea_factory_one_click_read_model(build)
        self.assertFalse(read_model["canResume"])
        self.assertIsNone(read_model["resumeKind"])
        self.assertFalse(read_model["canRetry"])
        self.assertEqual(read_model["completionBoundary"], "final_report")
        self.assertFalse(read_model["optimizationIncluded"])

        with self.assertRaises(self.bridge.DataIntegrityError):
            self.bridge._ea_factory_one_click_defer_optimization_handoff(
                build["id"],
                expected_run_snapshot=copy.deepcopy(persisted),
                reason_code="unexpected_failure",
            )

    def test_completed_session_publishes_canonical_mission_report_after_exact_binding(self) -> None:
        session_id = "opts_" + "8" * 32
        mission_id, report_id = self.bridge._ea_factory_optimization_terminal_report_ids(
            session_id
        )
        session = {
            "schemaVersion": 1,
            "id": session_id,
            "state": "completed",
            "stage": "complete",
            "buildId": "ea-build-mt5-verified",
            "sourceDigest": "a" * 64,
            "baselineReportSha256": "b" * 64,
            "platform": "mt5",
            "terminalBinding": self.terminal_binding(),
            "requestDigest": "d" * 64,
            "riskThresholds": {
                "targetProfitPercent": 10.0,
                "maxDrawdownPercent": 20.0,
                "minimumTrades": 25,
            },
            "round": {"index": 0, "number": 1, "count": 1, "id": "round-01", "combinationCount": 101},
            "testerSettings": {
                "symbol": "XAUUSD",
                "period": "H1",
                "model": "every_tick",
                "useDate": True,
                "fromDate": "2025-01-01",
                "toDate": "2025-12-31",
                "optimizationMode": "fast_genetic",
                "criterion": "balance_max",
            },
            "progress": {"passCount": 101, "returnedPassCount": 101, "rowsTruncated": False},
            "recovery": {"startBoundaryCommitted": True, "receiptPresent": True},
            "failure": None,
            "evidence": [{
                "roundId": "round-01",
                "passCount": 101,
                "returnedPassCount": 101,
                "rowsTruncated": False,
                "resultRows": [
                    {"pass": index, "trades": 50}
                    for index in range(1, 102)
                ],
                "resultRowsSha256": "9" * 64,
                "publicResultRowsTruncated": False,
                "warnings": [],
                "evidenceDocumentSha256": "e" * 64,
                "report": {"ref": "optreport_" + "1" * 24, "sha256": "1" * 64, "byteSize": 100},
                "manifest": {"ref": "optmanifest_" + "2" * 24, "sha256": "2" * 64, "byteSize": 200},
                "testerSettingsSha256": "3" * 64,
                "visibleEvidenceSha256": "4" * 64,
                "analysis": {
                    "sessionId": session_id,
                    "roundId": "round-01",
                    "requestDigest": "d" * 64,
                    "sourceResultDocumentSha256": "e" * 64,
                    "sourceResultRowsSha256": "9" * 64,
                    "passCount": 101,
                    "returnedPassCount": 101,
                    "rowsTruncated": False,
                    "status": "available",
                    "reasonCode": None,
                    "unavailableReasons": [],
                    "riskThresholds": {
                        "targetProfitPercent": 10.0,
                        "maxDrawdownPercent": 20.0,
                        "minimumTrades": 25,
                    },
                    "profitablePassCount": 60,
                    "eligiblePassCount": 12,
                    "candidateGroups": {
                        "maxProfit": [{"pass": 7, "netProfit": 220.0, "drawdownPercent": 9.0, "trades": 80, "stability": 1.4, "parameters": {"StopLossPoints": 200}}],
                        "lowestDrawdown": [{"pass": 8, "netProfit": 150.0, "drawdownPercent": 5.0, "trades": 90, "stability": 1.2, "parameters": {"StopLossPoints": 150}}],
                        "mostStable": [{"pass": 9, "netProfit": 180.0, "drawdownPercent": 7.0, "trades": 85, "stability": 1.8, "parameters": {"StopLossPoints": 250}}],
                    },
                    "currentBands": [{"name": "StopLossPoints", "kind": "numeric", "start": "100", "step": "50", "stop": "300", "valueCount": 5}],
                    "nextParameterPlan": [{"name": "StopLossPoints", "kind": "numeric", "start": 150.0, "step": "50", "stop": 250.0, "reason": "verified eligible range"}],
                    "nextParameterPlanAvailable": True,
                    "nextParameterPlanReasonCode": None,
                },
            }],
        }
        analysis_sha256 = self.bridge._ea_factory_optimization_document_sha256(
            session["evidence"][0]["analysis"]
        )
        session["evidence"][0]["analysisSha256"] = analysis_sha256
        binding = {
            "operationId": "op_" + "5" * 40,
            "compiledBinarySha256": "5" * 64,
            "baselineVisualBacktestSha256": "6" * 64,
            "settingsScreenshotSha256": "7" * 64,
            "resultsScreenshotSha256": "8" * 64,
            "optimizationReportRef": "optreport_" + "1" * 24,
            "optimizationReportSha256": "1" * 64,
            "optimizationReportByteSize": 100,
            "adapterReceiptRef": "optmanifest_" + "2" * 24,
            "adapterReceiptSha256": "2" * 64,
            "adapterReceiptByteSize": 200,
            "optimizationRanges": [{
                "inputName": "StopLossPoints",
                "start": "100",
                "step": "50",
                "stop": "300",
                "enabled": True,
                "sourceDefault": "300",
                "valueKind": "integer",
            }],
        }
        fixed_time = "2026-10-16T00:00:00Z"
        mission = self.bridge._ea_factory_optimization_publication_mission_projection(
            {"createdAt": fixed_time, "updatedAt": fixed_time},
            mission_id=mission_id,
            session_id=session_id,
            idempotency_key=f"eaopt-report:{session_id}",
            status="running",
            result="",
            report_ids=[],
            completed_at=None,
            staging_contract=None,
        )
        self.assertIsInstance(mission, dict)
        mission_store = [copy.deepcopy(mission)]
        audit_rows = []
        created_reports = []
        saved_missions = []

        def create_mission(payload: dict, status: str = "queued", **kwargs):
            staging = kwargs.get("_trusted_optimization_publication_staging")
            created = self.bridge._ea_factory_optimization_publication_mission_projection(
                {"createdAt": fixed_time, "updatedAt": fixed_time},
                mission_id=payload["id"],
                session_id=session_id,
                idempotency_key=payload["idempotencyKey"],
                status=status,
                result="",
                report_ids=[],
                completed_at=None,
                staging_contract=staging,
            )
            mission_store[:] = [copy.deepcopy(created)]
            return copy.deepcopy(created)

        def append_once(row: dict) -> bool:
            matches = [
                item for item in audit_rows if item.get("eventId") == row.get("eventId")
            ]
            if matches:
                return False
            audit_rows.append({"time": fixed_time, **copy.deepcopy(row)})
            return True

        def save(rows: list[dict]):
            saved_missions.append(copy.deepcopy(rows))
            mission_store[:] = copy.deepcopy(rows)
        with tempfile.TemporaryDirectory() as temporary:
            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", Path(temporary)),
                mock.patch.object(self.bridge, "find_mission", return_value=None),
                mock.patch.object(
                    self.bridge,
                    "create_mission",
                    side_effect=create_mission,
                ) as create_mission,
                mock.patch.object(self.bridge, "_ea_factory_optimization_evidence_binding", return_value=binding),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_build_context",
                    return_value={
                        "sourceDigest": "a" * 64,
                        "baseline": {"sha256": "b" * 64},
                        "binary": {"sha256": "5" * 64},
                        "baselineVisualBacktestSha256": "6" * 64,
                    },
                ),
                mock.patch.object(
                    self.bridge,
                    "tail_jsonl",
                    side_effect=lambda *_args, **_kwargs: copy.deepcopy(audit_rows),
                ),
                mock.patch.object(self.bridge, "append_audit", side_effect=lambda row: audit_rows.append(row)),
                mock.patch.object(
                    self.bridge,
                    "append_audit_once",
                    side_effect=append_once,
                ),
                mock.patch.object(self.bridge, "utc_now", return_value=fixed_time),
                mock.patch.object(
                    self.bridge,
                    "create_report",
                    side_effect=lambda payload, **_kwargs: created_reports.append(payload) or {
                        **payload,
                        "executionEvidence": {
                            "mtExecutionVerified": True,
                            "optimizationProofVerified": True,
                        },
                    },
                ),
                mock.patch.object(
                    self.bridge,
                    "load_missions",
                    side_effect=lambda: copy.deepcopy(mission_store),
                ),
                mock.patch.object(self.bridge, "save_missions", side_effect=save),
            ):
                published = self.bridge._ea_factory_optimization_publish_terminal_report(
                    session
                )

        self.assertEqual(published, {"missionId": mission_id, "reportId": report_id, "state": "completed"})
        verification = next(
            row for row in audit_rows if row.get("type") == "metatrader.execution_verified"
        )
        self.assertEqual(verification["compileArtifactSha256"], "5" * 64)
        self.assertEqual(verification["visualBacktestImageSha256"], "6" * 64)
        self.assertEqual(verification["optimizationArtifactSha256"], "1" * 64)
        self.assertFalse(verification["liveTrading"])
        self.assertEqual(created_reports[0]["type"], "ea_experiment_report")
        self.assertEqual(created_reports[0]["linkedMissionId"], mission_id)
        self.assertEqual(created_reports[0]["metrics"]["optimizationSession"]["requestDigest"], "d" * 64)
        self.assertEqual(
            created_reports[0]["metrics"]["plan"]["parameterRanges"],
            binding["optimizationRanges"],
        )
        stored_results = created_reports[0]["metrics"]["results"]
        self.assertEqual(stored_results["returnedPassCount"], 101)
        self.assertEqual(stored_results["storedPassRowCount"], 100)
        self.assertEqual(len(stored_results["allPassRows"]), 100)
        self.assertTrue(stored_results["allPassRowsTruncated"])
        self.assertEqual(stored_results["allPassRowsSha256"], "9" * 64)
        self.assertEqual(stored_results["analysisStatus"], "available")
        self.assertEqual(stored_results["analysisSha256"], analysis_sha256)
        self.assertEqual(stored_results["analysisSourceRowsSha256"], "9" * 64)
        self.assertEqual(stored_results["profitablePassCount"], 60)
        self.assertEqual(stored_results["eligiblePassCount"], 12)
        self.assertEqual(
            stored_results["candidateGroups"]["maxProfit"][0]["pass"], 7
        )
        self.assertEqual(
            stored_results["nextParameterPlan"][0]["start"], 150.0
        )
        self.assertTrue(stored_results["nextParameterPlanAvailable"])
        self.assertEqual(
            created_reports[0]["metrics"]["plan"]["riskThresholds"],
            session["riskThresholds"],
        )
        self.assertEqual(created_reports[0]["executionEvidence"]["runId"], session_id)
        self.assertEqual(saved_missions[-1][0]["reportIds"], [report_id])
        self.assertEqual(create_mission.call_args.kwargs["status"], "running")

    def test_late_completed_report_correction_is_append_only_and_crash_idempotent(
        self,
    ) -> None:
        session, binding, base_report, base_mission = (
            self.late_completed_publication_fixture()
        )
        session["riskThresholds"] = None
        round_evidence = session["evidence"][0]
        round_evidence["analysis"] = {
            "sessionId": session["id"],
            "roundId": round_evidence["roundId"],
            "requestDigest": session["requestDigest"],
            "sourceResultDocumentSha256": round_evidence[
                "evidenceDocumentSha256"
            ],
            "sourceResultRowsSha256": round_evidence["resultRowsSha256"],
            "passCount": round_evidence["passCount"],
            "returnedPassCount": round_evidence["returnedPassCount"],
            "rowsTruncated": False,
            "status": "available",
            "reasonCode": None,
            "unavailableReasons": [],
            "riskThresholds": {
                "targetProfitPercent": None,
                "maxDrawdownPercent": None,
                "minimumTrades": None,
            },
            "profitablePassCount": 4,
            "eligiblePassCount": 4,
            "candidateGroups": {
                "maxProfit": [],
                "lowestDrawdown": [],
                "mostStable": [],
            },
            "currentBands": [],
            "nextParameterPlan": [],
            "nextParameterPlanAvailable": False,
            "nextParameterPlanReasonCode": None,
        }
        round_evidence["analysisSha256"] = (
            self.bridge._ea_factory_optimization_document_sha256(
                round_evidence["analysis"]
            )
        )
        base_report_id = base_report["id"]
        base_mission_id = base_mission["id"]
        mission_store = [copy.deepcopy(base_mission)]
        audit_rows = []
        created_reports = []
        save_calls = 0
        fail_after_report_once = True
        fixed_time = "2026-10-16T00:00:00Z"

        def find_mission(mission_id: str):
            found = next(
                (item for item in mission_store if item.get("id") == mission_id),
                None,
            )
            return copy.deepcopy(found) if isinstance(found, dict) else None

        def create_mission(payload: dict, status: str = "queued", **kwargs):
            existing = next(
                (
                    item
                    for item in mission_store
                    if item.get("idempotencyKey") == payload.get("idempotencyKey")
                ),
                None,
            )
            if isinstance(existing, dict):
                return copy.deepcopy(existing)
            staging = kwargs.get("_trusted_optimization_publication_staging")
            mission = self.bridge._ea_factory_optimization_publication_mission_projection(
                {"createdAt": fixed_time, "updatedAt": fixed_time},
                mission_id=payload["id"],
                session_id=session["id"],
                idempotency_key=payload["idempotencyKey"],
                status=status,
                result="",
                report_ids=[],
                completed_at=None,
                staging_contract=staging,
            )
            self.assertIsInstance(mission, dict)
            mission_store.append(copy.deepcopy(mission))
            return mission

        def load_missions():
            return copy.deepcopy(mission_store)

        def save_missions(rows: list[dict]) -> None:
            nonlocal save_calls, fail_after_report_once
            save_calls += 1
            if fail_after_report_once and save_calls == 2:
                fail_after_report_once = False
                raise OSError("simulated crash after correction Report commit")
            mission_store[:] = copy.deepcopy(rows)

        def append_audit_once(row: dict) -> bool:
            matches = [
                item for item in audit_rows if item.get("eventId") == row.get("eventId")
            ]
            if matches:
                comparable = [
                    {key: value for key, value in item.items() if key != "time"}
                    for item in matches
                ]
                if any(item != row for item in comparable):
                    raise self.bridge.DataIntegrityError("collision")
                return False
            audit_rows.append({"time": fixed_time, **copy.deepcopy(row)})
            return True

        with tempfile.TemporaryDirectory() as temporary:
            report_root = Path(temporary)
            base_path = report_root / f"{base_report_id}.json"
            base_path.write_text(
                json.dumps(base_report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            base_bytes = base_path.read_bytes()
            base_digest = self.bridge._report_snapshot_digest(base_report)

            def create_report(payload: dict, **kwargs):
                self.assertTrue(
                    kwargs.get("_trusted_optimization_terminal_publication")
                )
                verified_execution = (
                    self.bridge.report_execution_evidence_read_model(
                        payload["executionEvidence"],
                        payload["type"],
                        payload["linkedMissionId"],
                        allow_optimization_staging_mission=True,
                        optimization_staging_contract=kwargs.get(
                            "_trusted_optimization_publication_staging"
                        ),
                    )
                )
                stored = (
                    self.bridge._ea_factory_optimization_report_storage_projection(
                        payload,
                        execution_evidence=verified_execution,
                        created_at="2026-10-16T00:00:00Z",
                        updated_at="2026-10-16T00:00:00Z",
                    )
                )
                self.assertIsInstance(stored, dict)
                self.bridge.write_json(
                    report_root / f"{stored['id']}.json",
                    stored,
                )
                created_reports.append(copy.deepcopy(stored))
                return stored

            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", report_root),
                mock.patch.object(self.bridge, "find_mission", side_effect=find_mission),
                mock.patch.object(
                    self.bridge,
                    "create_mission",
                    side_effect=create_mission,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_evidence_binding",
                    return_value=binding,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_build_context",
                    return_value={
                        "sourceDigest": session["sourceDigest"],
                        "baseline": {
                            "sha256": session["baselineReportSha256"]
                        },
                        "binary": {"sha256": binding["compiledBinarySha256"]},
                        "baselineVisualBacktestSha256": binding[
                            "baselineVisualBacktestSha256"
                        ],
                    },
                ),
                mock.patch.object(
                    self.bridge,
                    "tail_jsonl",
                    side_effect=lambda *_args, **_kwargs: copy.deepcopy(audit_rows),
                ),
                mock.patch.object(
                    self.bridge,
                    "append_audit",
                    side_effect=lambda row: audit_rows.append(copy.deepcopy(row)),
                ),
                mock.patch.object(
                    self.bridge,
                    "append_audit_once",
                    side_effect=append_audit_once,
                ),
                mock.patch.object(self.bridge, "utc_now", return_value=fixed_time),
                mock.patch.object(
                    self.bridge,
                    "create_report",
                    side_effect=create_report,
                ),
                mock.patch.object(
                    self.bridge,
                    "load_missions",
                    side_effect=load_missions,
                ),
                mock.patch.object(
                    self.bridge,
                    "save_missions",
                    side_effect=save_missions,
                ),
            ):
                with self.assertRaisesRegex(
                    OSError,
                    "simulated crash after correction Report commit",
                ):
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        session
                    )

                self.assertEqual(base_path.read_bytes(), base_bytes)
                self.assertEqual(len(created_reports), 1)
                correction_report = created_reports[0]
                correction_report_id = correction_report["id"]
                correction_mission_id = correction_report["linkedMissionId"]
                self.assertTrue(correction_report_id.startswith("report-eaoptfix-"))
                self.assertTrue(
                    correction_mission_id.startswith("mission-eaoptfix-")
                )
                self.assertNotEqual(correction_report_id, base_report_id)
                correction = correction_report["metrics"]["reportCorrection"]
                self.assertEqual(correction["supersedesReportId"], base_report_id)
                self.assertEqual(
                    correction["supersedesMissionId"],
                    base_mission_id,
                )
                self.assertEqual(
                    correction["supersedesReportSha256"],
                    base_digest,
                )
                staged_correction_mission = next(
                    item
                    for item in mission_store
                    if item.get("id") == correction_mission_id
                )
                self.assertEqual(staged_correction_mission["status"], "running")
                self.assertEqual(staged_correction_mission["reportIds"], [])

                published = (
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        session
                    )
                )
                retried = (
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        session
                    )
                )

                expected = {
                    "missionId": correction_mission_id,
                    "reportId": correction_report_id,
                    "state": "completed",
                    "supersedesMissionId": base_mission_id,
                    "supersedesReportId": base_report_id,
                    "supersedesReportSha256": base_digest,
                }
                self.assertEqual(published, expected)
                self.assertEqual(retried, expected)
                self.assertEqual(len(created_reports), 1)
                self.assertEqual(base_path.read_bytes(), base_bytes)
                self.assertEqual(
                    next(
                        item
                        for item in mission_store
                        if item.get("id") == base_mission_id
                    ),
                    base_mission,
                )
                completed_correction_mission = next(
                    item
                    for item in mission_store
                    if item.get("id") == correction_mission_id
                )
                self.assertEqual(completed_correction_mission["status"], "completed")
                self.assertEqual(
                    completed_correction_mission["reportIds"],
                    [correction_report_id],
                )
                correction_audits = [
                    row
                    for row in audit_rows
                    if row.get("type")
                    == "ea_factory.optimization.late_completed_report_correction_published"
                ]
                self.assertEqual(len(correction_audits), 1)
                self.assertEqual(
                    correction_audits[0]["supersedesReportSha256"],
                    base_digest,
                )

                tampered_analysis_session = copy.deepcopy(session)
                tampered_analysis = tampered_analysis_session["evidence"][0][
                    "analysis"
                ]
                tampered_analysis["riskThresholds"][
                    "targetProfitPercent"
                ] = 1.0
                tampered_analysis_session["evidence"][0]["analysisSha256"] = (
                    self.bridge._ea_factory_optimization_document_sha256(
                        tampered_analysis
                    )
                )
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        tampered_analysis_session
                    )
                self.assertEqual(len(created_reports), 1)

                tampered = copy.deepcopy(correction_report)
                tampered["metrics"]["reportCorrection"][
                    "supersedesReportSha256"
                ] = "0" * 64
                self.bridge.write_json(
                    report_root / f"{correction_report_id}.json",
                    tampered,
                )
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        session
                    )

    def test_late_completed_report_correction_rejects_stale_base_identity(
        self,
    ) -> None:
        session, _binding, base_report, base_mission = (
            self.late_completed_publication_fixture()
        )
        self.assertIsNotNone(
            self.bridge._ea_factory_optimization_late_report_correction_lineage(
                session,
                base_report,
                base_mission,
            )
        )
        mutations = (
            (
                "report_build",
                lambda report, _mission: report["metrics"][
                    "optimizationSession"
                ].update(buildId="ea-build-other"),
            ),
            (
                "report_failure",
                lambda report, _mission: report["metrics"]["failure"].update(
                    code="other_failure"
                ),
            ),
            (
                "report_execution",
                lambda report, _mission: report["executionEvidence"].update(
                    mtExecutionVerified=True
                ),
            ),
            (
                "mission_report",
                lambda _report, mission: mission.update(reportIds=[]),
            ),
            (
                "mission_key",
                lambda _report, mission: mission.update(
                    idempotencyKey="eaopt-report:other"
                ),
            ),
            (
                "mission_owner",
                lambda _report, mission: mission.update(owner="other_agent"),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                candidate_report = copy.deepcopy(base_report)
                candidate_mission = copy.deepcopy(base_mission)
                mutate(candidate_report, candidate_mission)
                self.assertIsNone(
                    self.bridge._ea_factory_optimization_late_report_correction_lineage(
                        session,
                        candidate_report,
                        candidate_mission,
                    )
                )

    def test_publication_mission_transition_dual_event_crash_and_rollback_guards(
        self,
    ) -> None:
        fixed_time = "2026-10-16T02:00:00Z"

        for transition in ("staged", "terminalized"):
            for crash_window in ("none", "intent_before_save", "save_before_commit"):
                with self.subTest(transition=transition, crash_window=crash_window):
                    mission_id = f"mission-{transition}-{crash_window}"
                    report_id = f"report-{transition}-{crash_window}"
                    pre = {
                        "id": mission_id,
                        "status": "running",
                        "result": "" if transition == "staged" else None,
                        "reportIds": [],
                        "createdAt": fixed_time,
                        "updatedAt": fixed_time,
                        "completedAt": None,
                    }
                    post_status = "running" if transition == "staged" else "completed"
                    post_result = None if transition == "staged" else "verified"
                    post_report_ids = [] if transition == "staged" else [report_id]
                    mission_store = [copy.deepcopy(pre)]
                    audit_rows: list[dict] = []
                    saved: list[list[dict]] = []

                    def tail(*_args, **_kwargs):
                        self.assertFalse(
                            getattr(
                                self.bridge.MISSIONS_LOCK,
                                "_is_owned",
                                lambda: False,
                            )()
                        )
                        return copy.deepcopy(audit_rows)

                    def append_once(row: dict) -> bool:
                        self.assertFalse(
                            getattr(
                                self.bridge.MISSIONS_LOCK,
                                "_is_owned",
                                lambda: False,
                            )()
                        )
                        rows = [
                            item
                            for item in audit_rows
                            if item.get("eventId") == row.get("eventId")
                        ]
                        if rows:
                            comparable = [
                                {
                                    key: value
                                    for key, value in item.items()
                                    if key != "time"
                                }
                                for item in rows
                            ]
                            if any(item != row for item in comparable):
                                raise self.bridge.DataIntegrityError("collision")
                            return False
                        audit_rows.append({"time": fixed_time, **copy.deepcopy(row)})
                        return True

                    def load():
                        return copy.deepcopy(mission_store)

                    def save(rows: list[dict]):
                        saved.append(copy.deepcopy(rows))
                        mission_store[:] = copy.deepcopy(rows)

                    kwargs = {
                        "session_id": "opts_" + "7" * 32,
                        "report_id": report_id,
                        "transition": transition,
                        "post_status": post_status,
                        "post_result": post_result,
                        "post_report_ids": post_report_ids,
                        "staging_contract": None,
                        "correction_lineage": None,
                    }
                    with (
                        mock.patch.object(self.bridge, "tail_jsonl", side_effect=tail),
                        mock.patch.object(
                            self.bridge,
                            "append_audit_once",
                            side_effect=append_once,
                        ),
                        mock.patch.object(self.bridge, "load_missions", side_effect=load),
                        mock.patch.object(self.bridge, "save_missions", side_effect=save),
                        mock.patch.object(self.bridge, "utc_now", return_value=fixed_time),
                    ):
                        if crash_window != "none":
                            post, needs_save, committed = (
                                self.bridge._ea_factory_optimization_prepare_publication_mission_transition(
                                    pre,
                                    **{
                                        key: value
                                        for key, value in kwargs.items()
                                        if key != "correction_lineage"
                                    },
                                )
                            )
                            self.assertTrue(needs_save)
                            self.assertFalse(committed)
                            if crash_window == "save_before_commit":
                                mission_store[:] = [copy.deepcopy(post)]

                        committed_mission = self.bridge._ea_factory_optimization_commit_publication_mission_transition(
                            mission_id,
                            **kwargs,
                        )
                        self.assertEqual(mission_store[0], committed_mission)
                        self.assertEqual(
                            [row.get("type") for row in audit_rows],
                            [
                                "ea_factory.optimization.publication_mission_transition_authorized",
                                "ea_factory.optimization.publication_mission_transition_committed",
                            ],
                        )
                        save_count = len(saved)
                        replay = self.bridge._ea_factory_optimization_commit_publication_mission_transition(
                            mission_id,
                            **kwargs,
                        )
                        self.assertEqual(replay, committed_mission)
                        self.assertEqual(len(saved), save_count)

                        mission_store[:] = [copy.deepcopy(pre)]
                        with self.assertRaisesRegex(
                            self.bridge.DataIntegrityError,
                            "rolled back",
                        ):
                            self.bridge._ea_factory_optimization_commit_publication_mission_transition(
                                mission_id,
                                **kwargs,
                            )
                        self.assertEqual(len(saved), save_count)

        for collision_phase in ("intent", "commit"):
            with self.subTest(collision_phase=collision_phase):
                fixed = {
                    "id": f"mission-collision-{collision_phase}",
                    "status": "running",
                    "result": "",
                    "reportIds": [],
                    "createdAt": fixed_time,
                    "updatedAt": fixed_time,
                    "completedAt": None,
                }
                report_id = f"report-collision-{collision_phase}"
                session_id = "opts_" + "8" * 32
                mission_store = [copy.deepcopy(fixed)]
                audit_rows = []
                saved = []
                intent_id = self.bridge._ea_factory_optimization_publication_transition_event_id(
                    session_id,
                    fixed["id"],
                    report_id,
                    "staged",
                    None,
                )
                if collision_phase == "intent":
                    audit_rows.append({
                        "time": fixed_time,
                        "type": "wrong.type",
                        "eventId": intent_id,
                    })

                def tail_collision(*_args, **_kwargs):
                    return copy.deepcopy(audit_rows)

                def append_collision(row: dict) -> bool:
                    matches = [
                        item
                        for item in audit_rows
                        if item.get("eventId") == row.get("eventId")
                    ]
                    if matches:
                        raise self.bridge.DataIntegrityError("collision")
                    audit_rows.append({"time": fixed_time, **copy.deepcopy(row)})
                    return True

                with (
                    mock.patch.object(
                        self.bridge,
                        "tail_jsonl",
                        side_effect=tail_collision,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "append_audit_once",
                        side_effect=append_collision,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "load_missions",
                        side_effect=lambda: copy.deepcopy(mission_store),
                    ),
                    mock.patch.object(
                        self.bridge,
                        "save_missions",
                        side_effect=lambda rows: saved.append(copy.deepcopy(rows)),
                    ),
                    mock.patch.object(self.bridge, "utc_now", return_value=fixed_time),
                ):
                    if collision_phase == "commit":
                        post, _needs_save, _committed = (
                            self.bridge._ea_factory_optimization_prepare_publication_mission_transition(
                                fixed,
                                session_id=session_id,
                                report_id=report_id,
                                transition="staged",
                                post_status="running",
                                post_result=None,
                                post_report_ids=[],
                                staging_contract=None,
                            )
                        )
                        mission_store[:] = [copy.deepcopy(post)]
                        intent_row = next(
                            row for row in audit_rows if row.get("eventId") == intent_id
                        )
                        commit = self.bridge._ea_factory_optimization_publication_transition_commit_event(
                            intent_row
                        )
                        audit_rows.append({
                            "time": fixed_time,
                            "type": "wrong.type",
                            "eventId": commit["eventId"],
                        })
                    with self.assertRaises(self.bridge.DataIntegrityError):
                        self.bridge._ea_factory_optimization_commit_publication_mission_transition(
                            fixed["id"],
                            session_id=session_id,
                            report_id=report_id,
                            transition="staged",
                            post_status="running",
                            post_result=None,
                            post_report_ids=[],
                            staging_contract=None,
                            correction_lineage=None,
                        )
                    self.assertEqual(saved, [])

    def test_legacy_cleanup_manifest_is_one_exact_source_owned_chain(self) -> None:
        manifests = self.bridge.EA_FACTORY_OPTIMIZATION_LEGACY_CLEANUP_MANIFESTS
        self.assertIsInstance(manifests, tuple)
        self.assertEqual(len(manifests), 1)
        manifest = manifests[0]
        self.assertEqual(
            self.bridge._ea_factory_optimization_json_sha256(manifest),
            "1c37ed189d8dbd512005c0baa510c28f6d19dab2c30d84b8e4976064e6e505dd",
        )
        self.assertEqual(
            manifest["manifestId"],
            "eaopt-legacy-cleanup-opts-aa4d80a0cdb44817-v1",
        )
        self.assertEqual(
            manifest["sessionId"],
            "opts_aa4d80a0cdb44817b36b7552ac148985",
        )
        self.assertEqual(manifest["roundId"], "round-01")
        self.assertEqual(manifest["resultReportByteSize"], 5378)
        self.assertEqual(manifest["adapterReceiptByteSize"], 14190)
        self.assertEqual(
            len({row["sessionId"] for row in manifests}),
            len(manifests),
        )
        self.assertEqual(
            len({row["manifestId"] for row in manifests}),
            len(manifests),
        )
        for role in ("root", "parent", "successor"):
            mission = manifest["missions"][role]
            report = manifest["reports"][role]
            self.assertRegex(mission["sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(report["sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(
                self.bridge._ea_factory_optimization_normalized_timestamp(
                    mission["createdAt"]
                ),
                mission["createdAt"],
            )
            self.assertEqual(
                self.bridge._ea_factory_optimization_normalized_timestamp(
                    mission["updatedAt"]
                ),
                mission["updatedAt"],
            )
            self.assertEqual(
                self.bridge._ea_factory_optimization_normalized_timestamp(
                    report["createdAt"]
                ),
                report["createdAt"],
            )
            self.assertEqual(
                self.bridge._ea_factory_optimization_normalized_timestamp(
                    report["updatedAt"]
                ),
                report["updatedAt"],
            )

    def test_legacy_sanitized_correction_publishes_verified_fix2_append_only(
        self,
    ) -> None:
        session, binding, base_report, base_mission = (
            self.late_completed_publication_fixture()
        )
        base_report_id = base_report["id"]
        base_mission_id = base_mission["id"]
        mission_store = [copy.deepcopy(base_mission)]
        audit_rows: list[dict] = []
        phase = {
            "legacy": True,
            "crash_after_fix2_report": False,
            "crash_after_fix2_completion": False,
            "crash_after_parent_archive": False,
            "reject_post_completion_save": False,
        }
        report_calls: list[str] = []
        save_calls: list[list[dict]] = []
        real_create_report = self.bridge.create_report
        real_tail_jsonl = self.bridge.tail_jsonl
        fixed_time = "2026-10-16T00:00:00Z"
        base_report["createdAt"] = "2026-10-15T23:59:29Z"
        base_report["updatedAt"] = "2026-10-15T23:59:29Z"

        def find_mission(mission_id: str):
            found = next(
                (row for row in mission_store if row.get("id") == mission_id),
                None,
            )
            return copy.deepcopy(found) if isinstance(found, dict) else None

        def create_mission(payload: dict, status: str = "queued", **kwargs):
            existing = next(
                (
                    row
                    for row in mission_store
                    if row.get("idempotencyKey") == payload.get("idempotencyKey")
                ),
                None,
            )
            if isinstance(existing, dict):
                return copy.deepcopy(existing)
            staging = kwargs.get("_trusted_optimization_publication_staging")
            # Simulate only the already-shipped v1 bug.  That historical
            # Mission had no private marker; the v2 successor must have it.
            persisted_staging = (
                staging
                if (
                isinstance(staging, dict)
                and staging.get("publicationKind")
                == "late_completed_correction_repair"
                )
                else None
            )
            mission = (
                self.bridge._ea_factory_optimization_publication_mission_projection(
                    {
                        "createdAt": fixed_time,
                        "updatedAt": fixed_time,
                    },
                    mission_id=payload["id"],
                    session_id=session["id"],
                    idempotency_key=payload["idempotencyKey"],
                    status=status,
                    result="",
                    report_ids=[],
                    completed_at=None,
                    staging_contract=persisted_staging,
                )
            )
            self.assertIsInstance(mission, dict)
            mission_store.append(copy.deepcopy(mission))
            audit_rows.append({
                "time": fixed_time,
                "type": "mission.created",
                "missionId": mission["id"],
                "ownerAgentId": "optimization_agent",
                "toolId": "run_optimization",
                "targetId": "right_tool_console",
                "status": "running",
                "modelTier": mission["modelTier"],
                "budget": copy.deepcopy(mission["budget"]),
                "executionMode": "manual_guarded",
                "autoEligible": False,
                "requiresHumanApproval": False,
                "discussionOnly": False,
                "hardGateReasons": [],
            })
            return mission

        def load_missions():
            return copy.deepcopy(mission_store)

        def save_missions(rows: list[dict]) -> None:
            save_calls.append(copy.deepcopy(rows))
            if phase["reject_post_completion_save"]:
                raise AssertionError(
                    "idempotent completed replay must not rewrite Mission state"
                )
            if phase["crash_after_fix2_report"] and any(
                str(row.get("id") or "").startswith("mission-eaoptfix2-")
                and row.get("status") == "completed"
                for row in rows
            ):
                phase["crash_after_fix2_report"] = False
                raise OSError("simulated crash after fix2 Report commit")
            if phase["crash_after_fix2_completion"] and any(
                str(row.get("id") or "").startswith("mission-eaoptfix2-")
                and row.get("status") == "completed"
                for row in rows
            ):
                # Simulate an atomic v2 Mission commit followed by process
                # loss before the legacy parent cleanup begins.
                mission_store[:] = copy.deepcopy(rows)
                phase["crash_after_fix2_completion"] = False
                raise OSError("simulated crash after fix2 Mission completion")
            if phase["crash_after_parent_archive"] and any(
                str(row.get("id") or "").startswith("mission-eaoptfix-")
                and not str(row.get("id") or "").startswith(
                    "mission-eaoptfix2-"
                )
                and row.get("status") == "archived"
                for row in rows
            ):
                # Simulate an atomic Mission-store commit followed by process
                # loss before the deterministic supersession audit append.
                mission_store[:] = copy.deepcopy(rows)
                phase["crash_after_parent_archive"] = False
                raise OSError("simulated crash after legacy Mission archive")
            mission_store[:] = copy.deepcopy(rows)

        def append_audit_once(row: dict) -> bool:
            event_id = row.get("eventId")
            matching = [
                item for item in audit_rows if item.get("eventId") == event_id
            ]
            comparable = [
                {key: value for key, value in item.items() if key != "time"}
                for item in matching
            ]
            if any(item != row for item in comparable):
                raise self.bridge.DataIntegrityError(
                    "Idempotent audit event ID collided with different content."
                )
            if matching:
                return False
            audit_rows.append({"time": fixed_time, **copy.deepcopy(row)})
            return True

        def tail_audit(*_args, **kwargs) -> list[dict]:
            match_fields = kwargs.get("match_fields")
            rows = copy.deepcopy(audit_rows)
            if isinstance(match_fields, dict):
                rows = [
                    row
                    for row in rows
                    if all(row.get(key) == value for key, value in match_fields.items())
                ]
            return rows

        root_pre = copy.deepcopy(base_mission)
        root_pre.update({
            "status": "running",
            "result": None,
            "reportIds": [],
            "completedAt": None,
            "updatedAt": root_pre["createdAt"],
        })
        root_transition_at = base_mission["completedAt"]
        root_post = self.bridge._ea_factory_optimization_transition_post_mission(
            root_pre,
            transition="terminalized",
            transition_at=root_transition_at,
            post_status="failed",
            post_result=base_report["summary"],
            post_report_ids=[base_report_id],
        )
        self.assertEqual(root_post, base_mission)
        root_intent_id = (
            self.bridge._ea_factory_optimization_publication_transition_event_id(
                session["id"],
                base_mission_id,
                base_report_id,
                "terminalized",
                None,
            )
        )
        root_intent = {
            "time": root_transition_at,
            "type": "ea_factory.optimization.publication_mission_transition_authorized",
            "eventId": root_intent_id,
            "schemaVersion": "ea-factory-optimization-publication-mission-transition-v1",
            "sessionId": session["id"],
            "missionId": base_mission_id,
            "reportId": base_report_id,
            "transition": "terminalized",
            "stagingScopeDigest": None,
            "createdAt": root_pre["createdAt"],
            "preUpdatedAt": root_pre["updatedAt"],
            "transitionAt": root_transition_at,
            "preStatus": "running",
            "preResult": None,
            "preReportIds": [],
            "preCompletedAt": None,
            "postStatus": "failed",
            "postReportIds": [base_report_id],
            "postResultSha256": self.bridge._ea_factory_optimization_json_sha256(
                base_report["summary"]
            ),
            "preMissionSha256": self.bridge._ea_factory_optimization_json_sha256(
                root_pre
            ),
            "postMissionSha256": self.bridge._ea_factory_optimization_json_sha256(
                base_mission
            ),
            "liveTradingAllowed": False,
        }
        audit_rows.append(root_intent)
        root_commit = (
            self.bridge._ea_factory_optimization_publication_transition_commit_event(
                root_intent
            )
        )
        self.assertIsInstance(root_commit, dict)
        audit_rows.append({"time": root_transition_at, **root_commit})

        with tempfile.TemporaryDirectory() as temporary:
            report_root = Path(temporary)
            base_path = report_root / f"{base_report_id}.json"
            self.bridge.write_json(base_path, base_report)
            base_bytes = base_path.read_bytes()

            def create_report_dispatch(payload: dict, **kwargs):
                report_calls.append(payload["id"])
                if not phase["legacy"]:
                    return real_create_report(payload, **kwargs)
                unverified = self.bridge.report_execution_evidence_read_model(
                    {},
                    "ea_experiment_report",
                    payload["linkedMissionId"],
                )
                stored = (
                    self.bridge._ea_factory_optimization_report_storage_projection(
                        payload,
                        execution_evidence=unverified,
                        created_at=fixed_time,
                        updated_at=fixed_time,
                    )
                )
                self.assertIsInstance(stored, dict)
                self.bridge.write_json(
                    report_root / f"{payload['id']}.json",
                    stored,
                )
                return stored

            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", report_root),
                mock.patch.object(self.bridge, "find_mission", side_effect=find_mission),
                mock.patch.object(
                    self.bridge,
                    "create_mission",
                    side_effect=create_mission,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_evidence_binding",
                    return_value=binding,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_build_context",
                    return_value={
                        "sourceDigest": session["sourceDigest"],
                        "baseline": {"sha256": session["baselineReportSha256"]},
                        "binary": {"sha256": binding["compiledBinarySha256"]},
                        "baselineVisualBacktestSha256": binding[
                            "baselineVisualBacktestSha256"
                        ],
                    },
                ),
                mock.patch.object(
                    self.bridge,
                    "tail_jsonl",
                    side_effect=tail_audit,
                ),
                mock.patch.object(
                    self.bridge,
                    "append_audit",
                    side_effect=lambda row: audit_rows.append(copy.deepcopy(row)),
                ),
                mock.patch.object(
                    self.bridge,
                    "append_audit_once",
                    side_effect=append_audit_once,
                ),
                mock.patch.object(self.bridge, "utc_now", return_value=fixed_time),
                mock.patch.object(
                    self.bridge,
                    "create_report",
                    side_effect=create_report_dispatch,
                ),
                mock.patch.object(
                    self.bridge,
                    "load_missions",
                    side_effect=load_missions,
                ),
                mock.patch.object(
                    self.bridge,
                    "save_missions",
                    side_effect=save_missions,
                ),
                mock.patch.object(
                    self.bridge,
                    "_start_ea_factory_optimization_worker",
                ) as start_worker,
            ):
                canonical_root_mission = copy.deepcopy(base_mission)
                for label, mutate in (
                    ("title", lambda row: row.update(title="tampered")),
                    ("detail", lambda row: row.update(detail="tampered")),
                    ("risk", lambda row: row.update(risk="low")),
                    ("modelTier", lambda row: row.update(modelTier="manager_quality")),
                    (
                        "budget",
                        lambda row: row["budget"].update(timeoutSeconds=999),
                    ),
                    (
                        "approval",
                        lambda row: row["approval"].update(state="approved"),
                    ),
                    ("extra", lambda row: row.update(untrustedExtra=True)),
                ):
                    with self.subTest(root_mission_field=label):
                        tampered_root = copy.deepcopy(canonical_root_mission)
                        mutate(tampered_root)
                        mission_store[0] = tampered_root
                        save_count = len(save_calls)
                        audit_count = len(audit_rows)
                        with self.assertRaises(self.bridge.DataIntegrityError):
                            self.bridge._ea_factory_optimization_publish_terminal_report(
                                session
                            )
                        self.assertEqual(len(save_calls), save_count)
                        self.assertEqual(len(audit_rows), audit_count)
                        mission_store[0] = copy.deepcopy(canonical_root_mission)

                with self.assertRaisesRegex(
                    self.bridge.DataIntegrityError,
                    "lacks verified execution evidence",
                ):
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        session
                    )

                root_digest = self.bridge._report_snapshot_digest(base_report)
                parent_suffix = self.bridge.payload_digest(
                    "ea-factory-optimization-late-report-correction-v1",
                    session["id"],
                    root_digest,
                )[:24]
                parent_report_id = f"report-eaoptfix-{parent_suffix}"
                parent_mission_id = f"mission-eaoptfix-{parent_suffix}"
                parent_path = report_root / f"{parent_report_id}.json"
                parent_report = self.bridge.read_json(parent_path, None)
                self.assertIsInstance(parent_report, dict)
                parent_bytes = parent_path.read_bytes()
                parent_digest = self.bridge._report_snapshot_digest(parent_report)
                repair_suffix = self.bridge.payload_digest(
                    "ea-factory-optimization-late-report-correction-v2",
                    session["id"],
                    root_digest,
                    parent_digest,
                )[:24]
                repair_report_id = f"report-eaoptfix2-{repair_suffix}"
                repair_mission_id = f"mission-eaoptfix2-{repair_suffix}"

                phase["legacy"] = False
                phase["crash_after_fix2_report"] = True
                with self.assertRaisesRegex(
                    OSError,
                    "simulated crash after fix2 Report commit",
                ):
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        session
                    )
                repair_path = report_root / f"{repair_report_id}.json"
                self.assertTrue(repair_path.is_file())
                repair_bytes = repair_path.read_bytes()
                self.assertEqual(base_path.read_bytes(), base_bytes)
                self.assertEqual(parent_path.read_bytes(), parent_bytes)

                # A deterministic-ID preseed with both verification booleans
                # set must not be accepted on identity alone.  Full canonical
                # storage equality is required before the running Mission can
                # be finalized.
                staged_repair_mission = copy.deepcopy(
                    next(
                        row
                        for row in mission_store
                        if row.get("id") == repair_mission_id
                    )
                )
                self.assertEqual(staged_repair_mission["status"], "running")
                tampered_repair = self.bridge.read_json(repair_path, None)
                tampered_repair["summary"] = "preseeded tampered summary"
                self.assertTrue(
                    tampered_repair["executionEvidence"]["mtExecutionVerified"]
                )
                self.assertTrue(
                    tampered_repair["executionEvidence"][
                        "optimizationProofVerified"
                    ]
                )
                self.bridge.write_json(repair_path, tampered_repair)
                with self.assertRaisesRegex(
                    self.bridge.DataIntegrityError,
                    "Immutable optimization Report identity changed",
                ):
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        session
                    )
                self.assertEqual(
                    next(
                        row
                        for row in mission_store
                        if row.get("id") == repair_mission_id
                    ),
                    staged_repair_mission,
                )
                repair_path.write_bytes(repair_bytes)

                original_parent_mission = copy.deepcopy(
                    next(
                        row
                        for row in mission_store
                        if row.get("id") == parent_mission_id
                    )
                )
                for label, mutate in (
                    ("title", lambda row: row.update(title="tampered")),
                    ("detail", lambda row: row.update(detail="tampered")),
                    ("risk", lambda row: row.update(risk="low")),
                    ("modelTier", lambda row: row.update(modelTier="manager_quality")),
                    (
                        "budget",
                        lambda row: row["budget"].update(timeoutSeconds=999),
                    ),
                    (
                        "approval",
                        lambda row: row["approval"].update(state="approved"),
                    ),
                    (
                        "scopeDigest",
                        lambda row: row.update(idempotencyScopeDigest="0" * 64),
                    ),
                    (
                        "createdAt",
                        lambda row: row.update(createdAt="2026-10-15T00:00:00Z"),
                    ),
                    ("extra", lambda row: row.update(untrustedExtra=True)),
                ):
                    with self.subTest(parent_mission_field=label):
                        tampered_parent_mission = copy.deepcopy(
                            original_parent_mission
                        )
                        mutate(tampered_parent_mission)
                        parent_index = next(
                            index
                            for index, row in enumerate(mission_store)
                            if row.get("id") == parent_mission_id
                        )
                        mission_store[parent_index] = tampered_parent_mission
                        save_count = len(save_calls)
                        audit_count = len(audit_rows)
                        with self.assertRaises(self.bridge.DataIntegrityError):
                            self.bridge._ea_factory_optimization_publish_terminal_report(
                                session
                            )
                        self.assertEqual(len(save_calls), save_count)
                        self.assertEqual(len(audit_rows), audit_count)
                        self.assertEqual(
                            mission_store[parent_index],
                            tampered_parent_mission,
                        )
                        mission_store[parent_index] = copy.deepcopy(
                            original_parent_mission
                        )

                phase["crash_after_fix2_completion"] = True
                with self.assertRaisesRegex(
                    OSError,
                    "simulated crash after fix2 Mission completion",
                ):
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        session
                    )

                # The deployed ghost Mission predates publication-transition
                # attestations.  Freeze an exact synthetic allowlist entry from
                # this fully verified chain, remove every transition event, and
                # exercise the real one-shot legacy-manifest cleanup path below.
                completed_repair_mission = copy.deepcopy(
                    next(
                        row
                        for row in mission_store
                        if row.get("id") == repair_mission_id
                    )
                )
                self.assertEqual(completed_repair_mission["status"], "completed")
                completed_repair_report = self.bridge.read_json(repair_path, None)
                self.assertIsInstance(completed_repair_report, dict)
                successor_staging = completed_repair_mission[
                    "optimizationPublicationStaging"
                ]
                publication_binding = successor_staging["publicationBinding"]
                round_evidence = session["evidence"][0]

                def manifest_mission(row: dict) -> dict:
                    timestamps = (
                        self.bridge._ea_factory_optimization_timestamp_tuple(row)
                    )
                    self.assertIsInstance(timestamps, dict)
                    return {
                        "id": row["id"],
                        "sha256": (
                            self.bridge._ea_factory_optimization_json_sha256(row)
                        ),
                        **timestamps,
                    }

                def manifest_report(row: dict) -> dict:
                    timestamps = (
                        self.bridge._ea_factory_optimization_report_timestamp_tuple(
                            row
                        )
                    )
                    self.assertIsInstance(timestamps, dict)
                    return {
                        "id": row["id"],
                        "sha256": self.bridge._report_snapshot_digest(row),
                        **timestamps,
                    }

                legacy_manifest = {
                    "schemaVersion": (
                        "ea-factory-optimization-legacy-cleanup-manifest-v1"
                    ),
                    "manifestId": "eaopt-legacy-cleanup-synthetic-exact-v1",
                    "reason": "verified_execution_evidence_sanitized",
                    "sessionId": session["id"],
                    "buildId": session["buildId"],
                    "requestDigest": session["requestDigest"],
                    "sourceDigest": session["sourceDigest"],
                    "baselineReportSha256": session["baselineReportSha256"],
                    "operationId": publication_binding["operationId"],
                    "roundId": publication_binding["roundId"],
                    "terminalCandidateId": publication_binding[
                        "terminalCandidateId"
                    ],
                    "terminalSelectionRevision": publication_binding[
                        "terminalSelectionRevision"
                    ],
                    "terminalBindingDigest": publication_binding[
                        "terminalBindingDigest"
                    ],
                    "resultReportArtifactId": publication_binding[
                        "resultReportArtifactId"
                    ],
                    "resultReportSha256": publication_binding[
                        "resultReportSha256"
                    ],
                    "resultReportByteSize": publication_binding[
                        "resultReportByteSize"
                    ],
                    "adapterReceiptArtifactId": publication_binding[
                        "adapterReceiptArtifactId"
                    ],
                    "adapterReceiptSha256": publication_binding[
                        "adapterReceiptSha256"
                    ],
                    "adapterReceiptByteSize": round_evidence["manifest"][
                        "byteSize"
                    ],
                    "stagingScopeDigest": successor_staging["scopeDigest"],
                    "backendVerificationId": publication_binding[
                        "backendVerificationId"
                    ],
                    "verificationEventId": (
                        self.bridge._ea_factory_optimization_publication_verification_event_id(
                            publication_binding["backendVerificationId"],
                            repair_mission_id,
                            repair_report_id,
                            successor_staging["scopeDigest"],
                        )
                    ),
                    "missions": {
                        "root": manifest_mission(base_mission),
                        "parent": manifest_mission(original_parent_mission),
                        "successor": manifest_mission(completed_repair_mission),
                    },
                    "reports": {
                        "root": manifest_report(base_report),
                        "parent": manifest_report(parent_report),
                        "successor": manifest_report(completed_repair_report),
                    },
                }
                legacy_manifest_patch = mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_OPTIMIZATION_LEGACY_CLEANUP_MANIFESTS",
                    (copy.deepcopy(legacy_manifest),),
                )
                legacy_manifest_patch.start()
                self.addCleanup(legacy_manifest_patch.stop)
                # The deployed chain already contains the ordinary v2
                # publication audit.  Only the later ghost-parent cleanup was
                # missing, so preserve that exact pre-cleanup condition here.
                audit_rows.append({
                    "time": fixed_time,
                    "type": (
                        "ea_factory.optimization."
                        "late_completed_report_repair_published"
                    ),
                    "sessionId": session["id"],
                    "state": "completed",
                    "missionId": repair_mission_id,
                    "reportId": repair_report_id,
                    "verifiedExecution": True,
                    "liveTradingAllowed": False,
                })
                audit_rows[:] = [
                    row
                    for row in audit_rows
                    if row.get("type")
                    not in {
                        "ea_factory.optimization.publication_mission_transition_authorized",
                        "ea_factory.optimization.publication_mission_transition_committed",
                    }
                ]
                self.assertFalse(
                    any(
                        str(row.get("type") or "").startswith(
                            "ea_factory.optimization.publication_mission_transition"
                        )
                        for row in audit_rows
                    )
                )

                def manifest_provenance(
                    session_value: dict = session,
                    root_mission_value: dict = base_mission,
                    parent_mission_value: dict = original_parent_mission,
                    successor_mission_value: dict = completed_repair_mission,
                    root_report_value: dict = base_report,
                    parent_report_value: dict = parent_report,
                    successor_report_value: dict = completed_repair_report,
                    staging_value: dict = successor_staging,
                ):
                    return self.bridge._ea_factory_optimization_legacy_cleanup_manifest_provenance(
                        session_value,
                        root_mission_value,
                        parent_mission_value,
                        successor_mission_value,
                        root_report_value,
                        parent_report_value,
                        successor_report_value,
                        staging_value,
                    )

                expected_manifest_provenance = {
                    "schemaVersion": (
                        "ea-factory-optimization-mission-time-provenance-v1"
                    ),
                    "mode": "legacy_manifest",
                    "identity": legacy_manifest["manifestId"],
                    "digest": self.bridge._ea_factory_optimization_json_sha256(
                        legacy_manifest
                    ),
                }
                self.assertEqual(
                    manifest_provenance(),
                    expected_manifest_provenance,
                )
                save_count = len(save_calls)
                audit_count = len(audit_rows)

                bad_session = copy.deepcopy(session)
                bad_session["id"] = "opts_" + "0" * 32
                self.assertIsNone(manifest_provenance(session_value=bad_session))
                bad_session = copy.deepcopy(session)
                bad_session["cancelRequested"] = True
                self.assertIsNone(manifest_provenance(session_value=bad_session))
                bad_session = copy.deepcopy(session)
                bad_session["evidence"][0]["manifest"]["byteSize"] += 1
                self.assertIsNone(manifest_provenance(session_value=bad_session))

                for label, role, field, value in (
                    (
                        "root-updated",
                        "root",
                        "updatedAt",
                        "2099-01-01T00:00:00Z",
                    ),
                    (
                        "parent-created",
                        "parent",
                        "createdAt",
                        "2026-10-15T23:59:59Z",
                    ),
                    (
                        "successor-completed",
                        "successor",
                        "completedAt",
                        "2099-01-01T00:00:00Z",
                    ),
                    ("root-extra", "root", "untrustedExtra", True),
                ):
                    with self.subTest(legacy_manifest_mission=label):
                        mission_values = {
                            "root": copy.deepcopy(base_mission),
                            "parent": copy.deepcopy(original_parent_mission),
                            "successor": copy.deepcopy(
                                completed_repair_mission
                            ),
                        }
                        mission_values[role][field] = value
                        self.assertIsNone(
                            manifest_provenance(
                                root_mission_value=mission_values["root"],
                                parent_mission_value=mission_values["parent"],
                                successor_mission_value=mission_values[
                                    "successor"
                                ],
                            )
                        )

                for label, role, field, value in (
                    (
                        "root-updated",
                        "root",
                        "updatedAt",
                        "2099-01-01T00:00:00Z",
                    ),
                    (
                        "parent-created",
                        "parent",
                        "createdAt",
                        "2026-10-15T23:59:59Z",
                    ),
                    (
                        "successor-summary",
                        "successor",
                        "summary",
                        "tampered",
                    ),
                ):
                    with self.subTest(legacy_manifest_report=label):
                        report_values = {
                            "root": copy.deepcopy(base_report),
                            "parent": copy.deepcopy(parent_report),
                            "successor": copy.deepcopy(
                                completed_repair_report
                            ),
                        }
                        report_values[role][field] = value
                        self.assertIsNone(
                            manifest_provenance(
                                root_report_value=report_values["root"],
                                parent_report_value=report_values["parent"],
                                successor_report_value=report_values[
                                    "successor"
                                ],
                            )
                        )

                for label, mutate in (
                    (
                        "scope",
                        lambda row: row.update(scopeDigest="0" * 64),
                    ),
                    (
                        "operation",
                        lambda row: row["publicationBinding"].update(
                            operationId="op_" + "0" * 40
                        ),
                    ),
                    (
                        "receipt",
                        lambda row: row["publicationBinding"].update(
                            adapterReceiptSha256="0" * 64
                        ),
                    ),
                ):
                    with self.subTest(legacy_manifest_staging=label):
                        tampered_staging = copy.deepcopy(successor_staging)
                        mutate(tampered_staging)
                        self.assertIsNone(
                            manifest_provenance(
                                staging_value=tampered_staging
                            )
                        )

                with mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_OPTIMIZATION_LEGACY_CLEANUP_MANIFESTS",
                    (
                        copy.deepcopy(legacy_manifest),
                        copy.deepcopy(legacy_manifest),
                    ),
                ):
                    self.assertIsNone(manifest_provenance())
                tampered_manifest = copy.deepcopy(legacy_manifest)
                tampered_manifest["roundId"] = "round-02"
                with mock.patch.object(
                    self.bridge,
                    "EA_FACTORY_OPTIMIZATION_LEGACY_CLEANUP_MANIFESTS",
                    (tampered_manifest,),
                ):
                    self.assertIsNone(manifest_provenance())

                root_lineage = {
                    "schemaVersion": (
                        "ea-factory-optimization-report-correction-v1"
                    ),
                    "supersedesReportId": base_report_id,
                    "supersedesMissionId": base_mission_id,
                    "supersedesReportSha256": root_digest,
                    "reportId": parent_report_id,
                    "missionId": parent_mission_id,
                    "proof": "completed_late_discarded",
                    "failureCode": "session_deadline_exceeded",
                }
                repair_lineage = {
                    "schemaVersion": (
                        "ea-factory-optimization-report-correction-v2"
                    ),
                    "supersedesReportId": parent_report_id,
                    "supersedesMissionId": parent_mission_id,
                    "supersedesReportSha256": parent_digest,
                    "rootReportId": base_report_id,
                    "rootMissionId": base_mission_id,
                    "rootReportSha256": root_digest,
                    "reportId": repair_report_id,
                    "missionId": repair_mission_id,
                    "proof": "completed_late_discarded",
                    "failureCode": "session_deadline_exceeded",
                    "repairReason": "verified_execution_evidence_sanitized",
                }
                cleanup_args = (
                    session,
                    root_lineage,
                    repair_lineage,
                    base_mission,
                    original_parent_mission,
                    completed_repair_mission,
                    base_report,
                    parent_report,
                    completed_repair_report,
                    successor_staging,
                )
                self.assertEqual(
                    self.bridge._ea_factory_optimization_cleanup_timestamp_provenance(
                        *cleanup_args
                    ),
                    expected_manifest_provenance,
                )
                root_transition_event_id = (
                    self.bridge._ea_factory_optimization_publication_transition_event_id(
                        session["id"],
                        base_mission_id,
                        base_report_id,
                        "terminalized",
                        None,
                    )
                )
                audit_rows.append({
                    "time": fixed_time,
                    "type": "wrong.type",
                    "eventId": root_transition_event_id,
                })
                self.assertIsNone(
                    self.bridge._ea_factory_optimization_cleanup_timestamp_provenance(
                        *cleanup_args
                    )
                )
                audit_rows.pop()

                # Exercise the actual bounded JSONL scanner.  A row occupying
                # a reserved transition eventId must block the one-shot
                # manifest even when its type/content is wrong; match_fields
                # must keep that row out of the independent verification lookup.
                verification_audit = copy.deepcopy(
                    next(
                        row
                        for row in audit_rows
                        if row.get("type") == "metatrader.execution_verified"
                        and row.get("missionId") == repair_mission_id
                    )
                )
                verification_audit.setdefault("time", fixed_time)
                with tempfile.TemporaryDirectory() as audit_temporary:
                    audit_path = Path(audit_temporary) / "bridge-audit.jsonl"

                    def write_audit_file(rows: list[dict]) -> None:
                        audit_path.write_text(
                            "".join(
                                json.dumps(row, ensure_ascii=False) + "\n"
                                for row in rows
                            ),
                            encoding="utf-8",
                        )

                    write_audit_file([verification_audit])
                    with (
                        mock.patch.object(self.bridge, "AUDIT_PATH", audit_path),
                        mock.patch.object(
                            self.bridge,
                            "tail_jsonl",
                            side_effect=real_tail_jsonl,
                        ),
                    ):
                        self.assertEqual(
                            self.bridge._ea_factory_optimization_cleanup_timestamp_provenance(
                                *cleanup_args
                            ),
                            expected_manifest_provenance,
                        )
                        for collision in (
                            {
                                "time": fixed_time,
                                "type": "wrong.type",
                                "eventId": root_transition_event_id,
                            },
                            {
                                "time": fixed_time,
                                "type": (
                                    "ea_factory.optimization."
                                    "publication_mission_transition_authorized"
                                ),
                                "eventId": root_transition_event_id,
                                "sessionId": session["id"],
                            },
                        ):
                            with self.subTest(
                                reserved_transition_collision=collision["type"]
                            ):
                                write_audit_file(
                                    [verification_audit, collision]
                                )
                                self.assertIsNone(
                                    self.bridge._ea_factory_optimization_cleanup_timestamp_provenance(
                                        *cleanup_args
                                    )
                                )
                        write_audit_file([verification_audit])
                self.assertEqual(len(save_calls), save_count)
                self.assertEqual(len(audit_rows), audit_count)

                # The v2 Report and Mission commit may succeed immediately
                # before the process dies while archiving the ghost v1
                # Mission. Replay must keep the archive and append the one
                # missing deterministic audit without rewriting v2.
                phase["crash_after_parent_archive"] = True
                with self.assertRaisesRegex(
                    OSError,
                    "simulated crash after legacy Mission archive",
                ):
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        session
                    )
                crashed_parent = next(
                    row
                    for row in mission_store
                    if row.get("id") == parent_mission_id
                )
                self.assertEqual(crashed_parent["status"], "archived")
                self.assertFalse(
                    any(
                        row.get("type")
                        == "ea_factory.optimization.legacy_publication_superseded"
                        for row in audit_rows
                    )
                )
                self.assertEqual(
                    self.bridge._ea_factory_optimization_reconcile_terminal_publications_after_restart(
                        [session]
                    ),
                    1,
                )

                published = (
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        session
                    )
                )
                phase["reject_post_completion_save"] = True
                retried = (
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        session
                    )
                )
                phase["reject_post_completion_save"] = False
                self.assertEqual(published, retried)
                self.assertEqual(published["missionId"], repair_mission_id)
                self.assertEqual(published["reportId"], repair_report_id)
                self.assertEqual(
                    published["correctionSchemaVersion"],
                    "ea-factory-optimization-report-correction-v2",
                )
                self.assertEqual(published["rootReportId"], base_report_id)
                self.assertEqual(published["rootReportSha256"], root_digest)
                self.assertEqual(
                    published["supersedesReportId"], parent_report_id
                )
                self.assertEqual(
                    published["supersedesReportSha256"], parent_digest
                )
                self.assertEqual(repair_path.read_bytes(), repair_bytes)
                self.assertEqual(base_path.read_bytes(), base_bytes)
                self.assertEqual(parent_path.read_bytes(), parent_bytes)
                repair_report = self.bridge.read_json(repair_path, None)
                self.assertTrue(
                    repair_report["executionEvidence"]["mtExecutionVerified"]
                )
                self.assertTrue(
                    repair_report["executionEvidence"][
                        "optimizationProofVerified"
                    ]
                )
                self.assertEqual(
                    repair_report["metrics"]["reportCorrection"]["repairReason"],
                    "verified_execution_evidence_sanitized",
                )
                repair_mission = next(
                    row
                    for row in mission_store
                    if row.get("id") == repair_mission_id
                )
                self.assertEqual(repair_mission["status"], "completed")
                self.assertEqual(repair_mission["reportIds"], [repair_report_id])
                self.assertEqual(
                    repair_mission["optimizationPublicationStaging"][
                        "publicationBinding"
                    ]["operationId"],
                    binding["operationId"],
                )
                self.assertEqual(
                    report_calls.count(repair_report_id),
                    1,
                )
                self.assertTrue(
                    any(
                        row.get("type")
                        == "ea_factory.optimization.late_completed_report_repair_published"
                        for row in audit_rows
                    )
                )
                parent_mission = next(
                    row
                    for row in mission_store
                    if row.get("id") == parent_mission_id
                )
                self.assertEqual(parent_mission["status"], "archived")
                self.assertEqual(parent_mission["workStatus"], "superseded")
                self.assertEqual(
                    parent_mission["reportIds"],
                    [parent_report_id],
                )
                marker = parent_mission["optimizationPublicationSupersession"]
                self.assertEqual(marker["successorMissionId"], repair_mission_id)
                self.assertEqual(marker["successorReportId"], repair_report_id)
                self.assertEqual(marker["rootReportSha256"], root_digest)
                self.assertEqual(marker["parentReportSha256"], parent_digest)
                self.assertEqual(
                    marker["missionTimestampProvenance"],
                    {
                        "schemaVersion": (
                            "ea-factory-optimization-mission-time-provenance-v1"
                        ),
                        "mode": "legacy_manifest",
                        "identity": legacy_manifest["manifestId"],
                        "digest": (
                            self.bridge._ea_factory_optimization_json_sha256(
                                legacy_manifest
                            )
                        ),
                    },
                )
                runtime_rows, runtime_meta = self.bridge.mission_runtime_window(
                    [parent_mission],
                    100,
                )
                self.assertEqual(runtime_meta["actionableCount"], 0)
                self.assertEqual(runtime_rows[0]["status"], "archived")
                supersession_events = [
                    row
                    for row in audit_rows
                    if row.get("type")
                    == "ea_factory.optimization.legacy_publication_superseded"
                ]
                self.assertEqual(len(supersession_events), 1)

                canonical_successor_mission = copy.deepcopy(repair_mission)
                for label, mutate in (
                    ("title", lambda row: row.update(title="tampered")),
                    ("detail", lambda row: row.update(detail="tampered")),
                    ("risk", lambda row: row.update(risk="low")),
                    ("modelTier", lambda row: row.update(modelTier="manager_quality")),
                    (
                        "budget",
                        lambda row: row["budget"].update(timeoutSeconds=999),
                    ),
                    (
                        "approval",
                        lambda row: row["approval"].update(state="approved"),
                    ),
                    ("extra", lambda row: row.update(untrustedExtra=True)),
                ):
                    with self.subTest(successor_mission_field=label):
                        successor_index = next(
                            index
                            for index, row in enumerate(mission_store)
                            if row.get("id") == repair_mission_id
                        )
                        tampered_successor = copy.deepcopy(
                            canonical_successor_mission
                        )
                        mutate(tampered_successor)
                        mission_store[successor_index] = tampered_successor
                        save_count = len(save_calls)
                        audit_count = len(audit_rows)
                        with self.assertRaises(self.bridge.DataIntegrityError):
                            self.bridge._ea_factory_optimization_publish_terminal_report(
                                session
                            )
                        self.assertEqual(len(save_calls), save_count)
                        self.assertEqual(len(audit_rows), audit_count)
                        mission_store[successor_index] = copy.deepcopy(
                            canonical_successor_mission
                        )

                canonical_archived_parent = copy.deepcopy(parent_mission)
                for label, mutate in (
                    (
                        "markerDigest",
                        lambda row: row[
                            "optimizationPublicationSupersession"
                        ].update(successorReportSha256="0" * 64),
                    ),
                    ("archivedTitle", lambda row: row.update(title="tampered")),
                    ("archivedReportIds", lambda row: row.update(reportIds=[])),
                ):
                    with self.subTest(superseded_parent_field=label):
                        parent_index = next(
                            index
                            for index, row in enumerate(mission_store)
                            if row.get("id") == parent_mission_id
                        )
                        tampered_archived = copy.deepcopy(
                            canonical_archived_parent
                        )
                        mutate(tampered_archived)
                        mission_store[parent_index] = tampered_archived
                        save_count = len(save_calls)
                        with self.assertRaises(self.bridge.DataIntegrityError):
                            self.bridge._ea_factory_optimization_publish_terminal_report(
                                session
                            )
                        self.assertEqual(len(save_calls), save_count)
                        mission_store[parent_index] = copy.deepcopy(
                            canonical_archived_parent
                        )

                # A valid cleanup audit makes the archived state monotonic.
                # Reintroducing the exact historical running parent must fail,
                # not silently archive it a second time.
                parent_index = next(
                    index
                    for index, row in enumerate(mission_store)
                    if row.get("id") == parent_mission_id
                )
                reintroduced = (
                    self.bridge._ea_factory_optimization_restore_presupersession_mission(
                        canonical_archived_parent
                    )
                )
                self.assertIsInstance(reintroduced, dict)
                mission_store[parent_index] = reintroduced
                save_count = len(save_calls)
                with self.assertRaisesRegex(
                    self.bridge.DataIntegrityError,
                    "was reintroduced",
                ):
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        session
                    )
                self.assertEqual(len(save_calls), save_count)
                mission_store[parent_index] = copy.deepcopy(
                    canonical_archived_parent
                )

                for label, mutate in (
                    ("title", lambda row: row.update(title="tampered")),
                    ("summary", lambda row: row.update(summary="tampered")),
                    (
                        "testerSettings",
                        lambda row: row["metrics"]["testerSettings"].update(
                            symbol="EURUSD"
                        ),
                    ),
                    (
                        "plan",
                        lambda row: row["metrics"]["plan"].update(
                            symbol="EURUSD"
                        ),
                    ),
                    (
                        "resultRows",
                        lambda row: row["metrics"]["results"]["allPassRows"][
                            0
                        ].update(trades=999),
                    ),
                    (
                        "candidateGroups",
                        lambda row: row["metrics"]["results"][
                            "candidateGroups"
                        ]["maxProfit"].append({"pass": 999}),
                    ),
                    ("risks", lambda row: row["risks"].append("tampered")),
                    (
                        "safety",
                        lambda row: row["safety"].update(publicShareable=True),
                    ),
                ):
                    with self.subTest(parent_field=label):
                        tampered_parent = copy.deepcopy(parent_report)
                        mutate(tampered_parent)
                        self.bridge.write_json(parent_path, tampered_parent)
                        with self.assertRaises(self.bridge.DataIntegrityError):
                            self.bridge._ea_factory_optimization_publish_terminal_report(
                                session
                            )
                        parent_path.write_bytes(parent_bytes)

                run = {
                    "runId": "ea-run-" + "f" * 24,
                    "status": "running",
                    "currentStageId": None,
                }
                final_report_id = "report-final-verified"
                final_stage = {
                    "id": "final_report",
                    "status": "completed",
                    "evidenceVerified": True,
                    "reportId": final_report_id,
                    "summaryDigest": "a" * 64,
                    "artifactManifestDigest": "b" * 64,
                    "auditLineageId": "audit-lineage-verified",
                }
                build = {
                    "id": session["buildId"],
                    "platform": "mt5",
                    "status": "completed",
                    "oneClickRun": run,
                    "stages": [final_stage],
                }
                final_report = {
                    "id": final_report_id,
                    "type": "ea_build_report",
                    "status": "ready",
                    "metrics": {
                        "artifactManifestDigest": final_stage[
                            "artifactManifestDigest"
                        ],
                        "auditLineageId": final_stage["auditLineageId"],
                        "eaFactoryFinalSummary": {
                            "buildId": session["buildId"],
                            "immutable": True,
                            "executionEvidence": {
                                "compile": {
                                    "zeroErrors": True,
                                    "zeroWarnings": True,
                                },
                                "backtest": {
                                    "visualMode": True,
                                    "buyTradeCount": 1,
                                    "sellTradeCount": 1,
                                },
                            },
                        },
                    },
                }
                self.bridge.write_json(
                    report_root / f"{final_report_id}.json",
                    final_report,
                )
                with (
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_bidirectional_ema_smoke_required",
                        return_value=True,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_certified_ema_four_pass_evidence_valid",
                        return_value=True,
                    ),
                ):
                    delivery = (
                        self.bridge._ea_factory_certified_customer_delivery_contract(
                            build,
                            run,
                            session,
                            published,
                        )
                    )
                    self.assertEqual(
                        delivery["optimization"]["reportId"],
                        repair_report_id,
                    )

                    verification_index = next(
                        index
                        for index, row in enumerate(audit_rows)
                        if row.get("type") == "metatrader.execution_verified"
                        and row.get("missionId") == repair_mission_id
                    )
                    canonical_verification = copy.deepcopy(
                        audit_rows[verification_index]
                    )
                    for label, mutate in (
                        (
                            "eventType",
                            lambda row: row.update(type="wrong.type"),
                        ),
                        (
                            "operationId",
                            lambda row: row.update(operationId="op_" + "0" * 40),
                        ),
                        (
                            "buildId",
                            lambda row: row.update(buildId="ea-build-other"),
                        ),
                        (
                            "sourceDigest",
                            lambda row: row.update(sourceDigest="0" * 64),
                        ),
                        (
                            "baselineReportSha256",
                            lambda row: row.update(
                                baselineReportSha256="0" * 64
                            ),
                        ),
                        (
                            "stagingScope",
                            lambda row: row.update(
                                publicationStagingScopeDigest="0" * 64
                            ),
                        ),
                    ):
                        with self.subTest(verification_event_field=label):
                            tampered_event = copy.deepcopy(canonical_verification)
                            mutate(tampered_event)
                            audit_rows[verification_index] = tampered_event
                            with self.assertRaises(self.bridge.DataIntegrityError):
                                self.bridge._ea_factory_certified_customer_delivery_contract(
                                    build,
                                    run,
                                    session,
                                    published,
                                )
                            audit_rows[verification_index] = copy.deepcopy(
                                canonical_verification
                            )

                    supersession_index = next(
                        index
                        for index, row in enumerate(audit_rows)
                        if row.get("type")
                        == "ea_factory.optimization.legacy_publication_superseded"
                    )
                    canonical_supersession_event = copy.deepcopy(
                        audit_rows[supersession_index]
                    )
                    audit_rows[supersession_index]["sessionId"] = (
                        "opts_" + "0" * 32
                    )
                    with self.assertRaises(self.bridge.DataIntegrityError):
                        self.bridge._ea_factory_certified_customer_delivery_contract(
                            build,
                            run,
                            session,
                            published,
                        )
                    audit_rows[supersession_index] = canonical_supersession_event
                    audit_rows[supersession_index] = {
                        **copy.deepcopy(canonical_supersession_event),
                        "type": "wrong.type",
                    }
                    with self.assertRaises(self.bridge.DataIntegrityError):
                        self.bridge._ea_factory_certified_customer_delivery_contract(
                            build,
                            run,
                            session,
                            published,
                        )
                    audit_rows[supersession_index] = canonical_supersession_event
                    audit_rows.append(copy.deepcopy(canonical_supersession_event))
                    with self.assertRaises(self.bridge.DataIntegrityError):
                        self.bridge._ea_factory_certified_customer_delivery_contract(
                            build,
                            run,
                            session,
                            published,
                        )
                    audit_rows.pop()

                    parent_path.unlink()
                    with self.assertRaises(self.bridge.DataIntegrityError):
                        self.bridge._ea_factory_certified_customer_delivery_contract(
                            build,
                            run,
                            session,
                            published,
                        )
                    parent_path.write_bytes(parent_bytes)

                    tampered_publication = copy.deepcopy(published)
                    tampered_publication["rootReportSha256"] = "0" * 64
                    with self.assertRaises(self.bridge.DataIntegrityError):
                        self.bridge._ea_factory_certified_customer_delivery_contract(
                            build,
                            run,
                            session,
                            tampered_publication,
                        )

                    marker = copy.deepcopy(
                        repair_mission["optimizationPublicationStaging"]
                    )
                    next(
                        row
                        for row in mission_store
                        if row.get("id") == repair_mission_id
                    )["optimizationPublicationStaging"]["publicationBinding"][
                        "operationId"
                    ] = "op_" + "0" * 40
                    with self.assertRaises(self.bridge.DataIntegrityError):
                        self.bridge._ea_factory_certified_customer_delivery_contract(
                            build,
                            run,
                            session,
                            published,
                        )
                    next(
                        row
                        for row in mission_store
                        if row.get("id") == repair_mission_id
                    )["optimizationPublicationStaging"] = marker

                cancelled = copy.deepcopy(session)
                cancelled["cancelRequested"] = True
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        cancelled
                    )
                start_worker.assert_not_called()

    def test_analysis_risk_threshold_absence_normalization_is_exact(self) -> None:
        absent = {
            "targetProfitPercent": None,
            "maxDrawdownPercent": None,
            "minimumTrades": None,
        }
        matcher = self.bridge._ea_factory_optimization_risk_thresholds_match
        self.assertTrue(matcher(None, absent))
        self.assertTrue(matcher(absent, None))
        self.assertTrue(matcher(absent, copy.deepcopy(absent)))
        self.assertFalse(
            matcher(
                {**absent, "targetProfitPercent": 1.0},
                None,
            )
        )
        self.assertFalse(
            matcher(
                {key: value for key, value in absent.items() if key != "minimumTrades"},
                None,
            )
        )
        self.assertFalse(matcher({**absent, "unknown": None}, None))

    def test_public_analysis_projection_never_promotes_zero_trade_legacy_rows(self) -> None:
        analysis = {
            "status": "available",
            "reasonCode": None,
            "unavailableReasons": [],
            "profitablePassCount": 0,
            "eligiblePassCount": 2,
            "candidateGroups": {
                "maxProfit": [{"pass": 1}],
                "lowestDrawdown": [{"pass": 1}],
                "mostStable": [{"pass": 1}],
            },
            "nextParameterPlan": [{"name": "RiskPercent"}],
            "nextParameterPlanAvailable": True,
            "nextParameterPlanReasonCode": None,
        }
        rows = [
            {"pass": 1, "trades": 0, "profit": 0.0},
            {"pass": 2, "trades": 0, "profit": 0.0},
        ]

        projected = self.bridge._ea_factory_optimization_public_analysis_projection(
            analysis,
            rows,
        )

        self.assertEqual(projected["status"], "unavailable")
        self.assertEqual(projected["reasonCode"], "backtest_zero_trades")
        self.assertIsNone(projected["eligiblePassCount"])
        self.assertEqual(
            projected["candidateGroups"],
            {"maxProfit": [], "lowestDrawdown": [], "mostStable": []},
        )
        self.assertEqual(projected["nextParameterPlan"], [])
        self.assertFalse(projected["nextParameterPlanAvailable"])
        self.assertEqual(analysis["status"], "available")

    def test_terminal_report_publication_is_serialized(self) -> None:
        counter_lock = threading.Lock()
        active = 0
        peak = 0

        def publish(_session):
            nonlocal active, peak
            with counter_lock:
                active += 1
                peak = max(peak, active)
            time.sleep(0.03)
            with counter_lock:
                active -= 1
            return {"state": "completed"}

        with mock.patch.object(
            self.bridge,
            "_ea_factory_optimization_publish_terminal_report_unlocked",
            side_effect=publish,
        ):
            threads = [
                threading.Thread(
                    target=self.bridge._ea_factory_optimization_publish_terminal_report,
                    args=({"id": f"session-{index}"},),
                )
                for index in range(2)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=2)

        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(peak, 1)

    def test_completed_report_publication_rejects_build_binding_change(self) -> None:
        session = {
            "id": "opts_" + "9" * 32,
            "state": "completed",
            "buildId": "ea-build-mt5-verified",
            "sourceDigest": "a" * 64,
            "baselineReportSha256": "b" * 64,
            "platform": "mt5",
            "requestDigest": "d" * 64,
            "terminalBinding": self.terminal_binding(),
            "evidence": [{}],
        }
        mission_id, _report_id = self.bridge._ea_factory_optimization_terminal_report_ids(
            session["id"]
        )
        with tempfile.TemporaryDirectory() as temporary:
            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", Path(temporary)),
                mock.patch.object(self.bridge, "find_mission", return_value=None),
                mock.patch.object(
                    self.bridge,
                    "create_mission",
                    return_value={"id": mission_id},
                ) as create_mission,
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_evidence_binding",
                    return_value={
                        "compiledBinarySha256": "5" * 64,
                        "baselineVisualBacktestSha256": "6" * 64,
                    },
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_build_context",
                    return_value={
                        "sourceDigest": "f" * 64,
                        "baseline": {"sha256": "b" * 64},
                        "binary": {"sha256": "5" * 64},
                        "baselineVisualBacktestSha256": "6" * 64,
                    },
                ),
            ):
                with self.assertRaises(self.bridge.OptimizationDomainError) as caught:
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        session
                    )
        self.assertEqual(caught.exception.code, "optimization_report_build_binding_changed")
        create_mission.assert_not_called()

    def test_completed_report_rejects_stale_or_cross_session_analysis_binding(self) -> None:
        session = {
            "id": "opts_" + "6" * 32,
            "state": "completed",
            "buildId": "ea-build-mt5-verified",
            "sourceDigest": "a" * 64,
            "baselineReportSha256": "b" * 64,
            "platform": "mt5",
            "requestDigest": "d" * 64,
            "terminalBinding": self.terminal_binding(),
            "evidence": [{
                "roundId": "round-01",
                "passCount": 2,
                "returnedPassCount": 2,
                "rowsTruncated": False,
                "resultRowsSha256": "9" * 64,
                "analysis": {
                    "sessionId": "opts_" + "5" * 32,
                    "roundId": "round-01",
                    "sourceResultRowsSha256": "9" * 64,
                    "passCount": 2,
                    "returnedPassCount": 2,
                    "rowsTruncated": False,
                },
            }],
        }
        binding = {
            "operationId": "op_" + "7" * 40,
            "compiledBinarySha256": "5" * 64,
            "baselineVisualBacktestSha256": "6" * 64,
        }
        with tempfile.TemporaryDirectory() as temporary:
            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", Path(temporary)),
                mock.patch.object(self.bridge, "find_mission", return_value=None),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_evidence_binding",
                    return_value=binding,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_build_context",
                    return_value={
                        "sourceDigest": "a" * 64,
                        "baseline": {"sha256": "b" * 64},
                        "binary": {"sha256": "5" * 64},
                        "baselineVisualBacktestSha256": "6" * 64,
                    },
                ),
                mock.patch.object(self.bridge, "create_mission") as create_mission,
            ):
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        session
                    )
        create_mission.assert_not_called()

    def test_completed_report_failure_never_exposes_terminal_mission(self) -> None:
        session_id = "opts_" + "7" * 32
        mission_id, _report_id = self.bridge._ea_factory_optimization_terminal_report_ids(
            session_id
        )
        session = {
            "schemaVersion": 1,
            "id": session_id,
            "state": "completed",
            "stage": "complete",
            "buildId": "ea-build-mt5-verified",
            "sourceDigest": "a" * 64,
            "baselineReportSha256": "b" * 64,
            "platform": "mt5",
            "terminalBinding": self.terminal_binding(),
            "requestDigest": "d" * 64,
            "round": {
                "index": 0,
                "number": 1,
                "count": 1,
                "id": "round-01",
                "combinationCount": 2,
            },
            "testerSettings": {"symbol": "XAUUSD", "period": "H1"},
            "progress": {"passCount": 2, "returnedPassCount": 2},
            "recovery": {"startBoundaryCommitted": True},
            "failure": None,
            "evidence": [{
                "roundId": "round-01",
                "passCount": 2,
                "returnedPassCount": 2,
                "rowsTruncated": False,
                "resultRows": [{"pass": 1}, {"pass": 2}],
                "resultRowsSha256": "9" * 64,
                "publicResultRowsTruncated": False,
                "warnings": [],
                "evidenceDocumentSha256": "e" * 64,
            }],
        }
        binding = {
            "operationId": "op_" + "8" * 40,
            "compiledBinarySha256": "5" * 64,
            "baselineVisualBacktestSha256": "6" * 64,
            "settingsScreenshotSha256": "7" * 64,
            "resultsScreenshotSha256": "8" * 64,
            "optimizationReportRef": "optreport_" + "1" * 24,
            "optimizationReportSha256": "1" * 64,
            "optimizationReportByteSize": 100,
            "adapterReceiptRef": "optmanifest_" + "2" * 24,
            "adapterReceiptSha256": "2" * 64,
            "adapterReceiptByteSize": 200,
            "optimizationRanges": [{
                "inputName": "StopLossPoints",
                "start": "100",
                "step": "50",
                "stop": "300",
                "enabled": True,
                "sourceDefault": "300",
                "valueKind": "integer",
            }],
        }
        fixed_time = "2026-10-16T00:00:00Z"
        mission_store: list[dict] = []
        audit_rows: list[dict] = []
        saved_missions = []

        def create_mission_side_effect(
            payload: dict,
            status: str = "queued",
            **kwargs,
        ) -> dict:
            staging = kwargs.get("_trusted_optimization_publication_staging")
            mission = (
                self.bridge._ea_factory_optimization_publication_mission_projection(
                    {"createdAt": fixed_time, "updatedAt": fixed_time},
                    mission_id=mission_id,
                    session_id=session_id,
                    idempotency_key=payload["idempotencyKey"],
                    status=status,
                    result="",
                    report_ids=[],
                    completed_at=None,
                    staging_contract=staging,
                )
            )
            self.assertIsInstance(mission, dict)
            mission_store[:] = [copy.deepcopy(mission)]
            return copy.deepcopy(mission)

        def save_missions(rows: list[dict]) -> None:
            saved_missions.append(copy.deepcopy(rows))
            mission_store[:] = copy.deepcopy(rows)

        def append_audit_once(row: dict) -> bool:
            event_id = row.get("eventId")
            matching = [
                item for item in audit_rows if item.get("eventId") == event_id
            ]
            if matching:
                return False
            audit_rows.append({"time": fixed_time, **copy.deepcopy(row)})
            return True

        with tempfile.TemporaryDirectory() as temporary:
            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", Path(temporary)),
                mock.patch.object(
                    self.bridge,
                    "find_mission",
                    side_effect=lambda candidate: copy.deepcopy(
                        next(
                            (
                                row
                                for row in mission_store
                                if row.get("id") == candidate
                            ),
                            None,
                        )
                    ),
                ),
                mock.patch.object(
                    self.bridge,
                    "create_mission",
                    side_effect=create_mission_side_effect,
                ) as create_mission,
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_evidence_binding",
                    return_value=binding,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_optimization_build_context",
                    return_value={
                        "sourceDigest": "a" * 64,
                        "baseline": {"sha256": "b" * 64},
                        "binary": {"sha256": "5" * 64},
                        "baselineVisualBacktestSha256": "6" * 64,
                    },
                ),
                mock.patch.object(
                    self.bridge,
                    "tail_jsonl",
                    side_effect=lambda *_args, **_kwargs: copy.deepcopy(audit_rows),
                ),
                mock.patch.object(
                    self.bridge,
                    "append_audit",
                    side_effect=lambda row: audit_rows.append(copy.deepcopy(row)),
                ),
                mock.patch.object(
                    self.bridge,
                    "append_audit_once",
                    side_effect=append_audit_once,
                ),
                mock.patch.object(self.bridge, "utc_now", return_value=fixed_time),
                mock.patch.object(
                    self.bridge,
                    "create_report",
                    side_effect=OSError("report storage unavailable"),
                ),
                mock.patch.object(
                    self.bridge,
                    "load_missions",
                    side_effect=lambda: copy.deepcopy(mission_store),
                ),
                mock.patch.object(
                    self.bridge,
                    "save_missions",
                    side_effect=save_missions,
                ),
            ):
                with self.assertRaises(OSError):
                    self.bridge._ea_factory_optimization_publish_terminal_report(
                        session
                    )

        self.assertEqual(create_mission.call_args.kwargs["status"], "running")
        self.assertEqual(saved_missions[-1][0]["status"], "running")
        self.assertEqual(saved_missions[-1][0]["reportIds"], [])
        self.assertIsNone(saved_missions[-1][0]["completedAt"])
        self.assertTrue(
            any(row.get("type") == "metatrader.execution_verified" for row in audit_rows)
        )
        self.assertFalse(
            any(
                row.get("type")
                == "ea_factory.optimization.terminal_report_published"
                for row in audit_rows
            )
        )

    def test_private_report_commit_accepts_only_exact_running_optimization_mission(
        self,
    ) -> None:
        session_id = "opts_" + "6" * 32
        mission_id, report_id = self.bridge._ea_factory_optimization_terminal_report_ids(
            session_id
        )
        mission = {
            "id": mission_id,
            "status": "running",
            "idempotencyKey": f"eaopt-report:{session_id}",
            "owner": "optimization_agent",
            "requester": "backend",
            "toolId": "run_optimization",
            "targetId": "right_tool_console",
            "reportType": "ea_experiment_report",
        }
        terminal_binding = self.terminal_binding()
        source = {
            "sourceKind": "mt5_visible_run",
            "toolId": "run_optimization",
            "runId": session_id,
            "roundId": "round-01",
            "platform": "mt5",
            "terminalId": "mtterm_" + "1" * 24,
            "terminalCandidateId": terminal_binding["candidateId"],
            "backendVerificationId": "mtverify_" + "2" * 24,
            "visibleTester": {
                "verified": True,
                "settingsScreenshotAttachmentId": "optsettings_" + "3" * 24,
                "resultsScreenshotAttachmentId": "optresults_" + "4" * 24,
                "testerLogArtifactId": "optmanifest_" + "5" * 24,
            },
            "resultReport": {
                "artifactId": "optreport_" + "6" * 24,
                "sha256": "6" * 64,
                "byteSize": 100,
                "mediaType": "text/html",
            },
            "artifactManifest": {
                "artifactId": "optmanifest_" + "5" * 24,
                "sha256": "5" * 64,
                "items": [],
            },
        }
        event = {
            "type": "metatrader.execution_verified",
            "verificationId": source["backendVerificationId"],
            "missionId": mission_id,
            "toolId": "run_optimization",
            "runId": session_id,
            "roundId": "round-01",
            "platform": "mt5",
            "terminalId": source["terminalId"],
            "terminalCandidateId": source["terminalCandidateId"],
            "status": "completed",
            "visibleApplicationProof": True,
            "liveTrading": False,
            "testShutdownTerminal": False,
            "mtExecutionVerified": True,
            "optimizationProofVerified": True,
            "compileArtifactSha256": "7" * 64,
            "visualBacktestImageSha256": "8" * 64,
            "optimizationArtifactSha256": "6" * 64,
            "visibleTester": copy.deepcopy(source["visibleTester"]),
            "resultReport": copy.deepcopy(source["resultReport"]),
            "artifactManifest": copy.deepcopy(source["artifactManifest"]),
        }
        payload = {
            "id": report_id,
            "type": "ea_experiment_report",
            "title": "MT5 Optimization",
            "summary": "verified",
            "ownerAgentId": "optimization_agent",
            "linkedMissionId": mission_id,
            "status": "ready",
            "metrics": {
                "optimizationSession": {
                    "id": session_id,
                    "state": "completed",
                    "requestDigest": "9" * 64,
                    "buildId": "ea-build-mt5-verified",
                    "sourceDigest": "a" * 64,
                    "baselineReportSha256": "b" * 64,
                    "terminalBinding": copy.deepcopy(terminal_binding),
                    "round": {"id": "round-01"},
                }
            },
            "executionEvidence": source,
        }
        publication_binding = {
            "operationId": "op_" + "6" * 40,
            "roundId": "round-01",
            "buildId": "ea-build-mt5-verified",
            "requestDigest": "9" * 64,
            "sourceDigest": "a" * 64,
            "baselineReportSha256": "b" * 64,
            "terminalCandidateId": source["terminalCandidateId"],
            "terminalSelectionRevision": terminal_binding["selectionRevision"],
            "terminalBindingDigest": terminal_binding["bindingDigest"],
            "backendVerificationId": source["backendVerificationId"],
            "resultReportArtifactId": source["resultReport"]["artifactId"],
            "resultReportSha256": source["resultReport"]["sha256"],
            "resultReportByteSize": source["resultReport"]["byteSize"],
            "adapterReceiptArtifactId": source["artifactManifest"]["artifactId"],
            "adapterReceiptSha256": source["artifactManifest"]["sha256"],
        }
        staging_contract = (
            self.bridge._ea_factory_optimization_trusted_staging_contract(
                session_id,
                None,
                publication_binding,
            )
        )
        self.assertIsInstance(staging_contract, dict)
        mission["optimizationPublicationStaging"] = copy.deepcopy(staging_contract)
        event.update({
            "operationId": publication_binding["operationId"],
            "buildId": publication_binding["buildId"],
            "requestDigest": publication_binding["requestDigest"],
            "sourceDigest": publication_binding["sourceDigest"],
            "baselineReportSha256": publication_binding["baselineReportSha256"],
            "terminalSelectionRevision": publication_binding[
                "terminalSelectionRevision"
            ],
            "terminalBindingDigest": publication_binding["terminalBindingDigest"],
            "resultReportArtifactId": publication_binding[
                "resultReportArtifactId"
            ],
            "resultReportSha256": publication_binding["resultReportSha256"],
            "resultReportByteSize": publication_binding["resultReportByteSize"],
            "adapterReceiptArtifactId": publication_binding[
                "adapterReceiptArtifactId"
            ],
            "adapterReceiptSha256": publication_binding[
                "adapterReceiptSha256"
            ],
            "publicationReportId": report_id,
            "publicationStagingScopeDigest": staging_contract["scopeDigest"],
            "reportCorrection": None,
        })
        event["eventId"] = (
            self.bridge._ea_factory_optimization_publication_verification_event_id(
                source["backendVerificationId"],
                mission_id,
                report_id,
                staging_contract["scopeDigest"],
            )
        )
        with tempfile.TemporaryDirectory() as temporary:
            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", Path(temporary)),
                mock.patch.object(self.bridge, "find_mission", return_value=mission),
                mock.patch.object(
                    self.bridge,
                    "tail_jsonl",
                    return_value=[event],
                ) as audit_read,
                mock.patch.object(self.bridge, "append_audit"),
            ):
                ordinary = self.bridge.report_execution_evidence_read_model(
                    source,
                    "ea_experiment_report",
                    mission_id,
                )
                invalid_payload = copy.deepcopy(payload)
                invalid_payload["metrics"]["optimizationSession"]["id"] = None
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge.create_report(
                        invalid_payload,
                        queue_research_sheet=False,
                        _trusted_optimization_terminal_publication=True,
                    )
                report = self.bridge.create_report(
                    payload,
                    queue_research_sheet=False,
                    _trusted_optimization_terminal_publication=True,
                    _trusted_optimization_publication_staging=staging_contract,
                )
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge.create_report(
                        payload,
                        queue_research_sheet=False,
                        _trusted_optimization_terminal_publication=True,
                    )
                for field in (
                    "operationId",
                    "buildId",
                    "sourceDigest",
                    "terminalBindingDigest",
                    "resultReportSha256",
                    "adapterReceiptSha256",
                    "publicationStagingScopeDigest",
                ):
                    with self.subTest(audit_field=field):
                        tampered_event = copy.deepcopy(event)
                        tampered_event[field] = (
                            "0" * 64
                            if str(tampered_event.get(field) or "").count("_") == 0
                            else "op_" + "0" * 40
                        )
                        audit_read.return_value = [tampered_event]
                        with self.assertRaises(self.bridge.DataIntegrityError):
                            self.bridge.create_report(
                                payload,
                                queue_research_sheet=False,
                                _trusted_optimization_terminal_publication=True,
                                _trusted_optimization_publication_staging=(
                                    staging_contract
                                ),
                            )
                audit_read.return_value = [event]
                for field in (
                    "operationId",
                    "buildId",
                    "sourceDigest",
                    "terminalBindingDigest",
                    "resultReportSha256",
                    "adapterReceiptSha256",
                ):
                    with self.subTest(contract_field=field):
                        tampered_contract = copy.deepcopy(staging_contract)
                        tampered_contract["publicationBinding"][field] = (
                            "op_" + "0" * 40
                            if field == "operationId"
                            else "0" * 64
                        )
                        with self.assertRaises(self.bridge.DataIntegrityError):
                            self.bridge.create_report(
                                payload,
                                queue_research_sheet=False,
                                _trusted_optimization_terminal_publication=True,
                                _trusted_optimization_publication_staging=(
                                    tampered_contract
                                ),
                            )

        self.assertFalse(ordinary["mtExecutionVerified"])
        self.assertTrue(report["executionEvidence"]["mtExecutionVerified"])
        self.assertTrue(
            report["executionEvidence"]["optimizationProofVerified"]
        )

        # The exact publication event remains authoritative after it has been
        # evicted from the ordinary 400-row UI tail.  This exercises the real
        # bounded active+archive scanner rather than a mocked tail result.
        with tempfile.TemporaryDirectory() as audit_temporary:
            audit_path = Path(audit_temporary) / "bridge-audit.jsonl"
            audit_records = [copy.deepcopy(event)] + [
                {
                    "time": f"2026-10-16T00:00:{index % 60:02d}Z",
                    "type": "unrelated.audit.event",
                    "sequence": index,
                }
                for index in range(401)
            ]
            audit_path.write_text(
                "".join(
                    json.dumps(row, ensure_ascii=False) + "\n"
                    for row in audit_records
                ),
                encoding="utf-8",
            )
            with (
                mock.patch.object(self.bridge, "AUDIT_PATH", audit_path),
                mock.patch.object(self.bridge, "find_mission", return_value=mission),
            ):
                recovered = self.bridge.report_execution_evidence_read_model(
                    source,
                    "ea_experiment_report",
                    mission_id,
                    allow_optimization_staging_mission=True,
                    optimization_staging_contract=staging_contract,
                )
            self.assertTrue(recovered["mtExecutionVerified"])
            self.assertTrue(recovered["optimizationProofVerified"])

    def test_failed_session_publishes_failed_report_without_execution_claim(self) -> None:
        session = {
            "schemaVersion": 1,
            "id": "opts_" + "a" * 32,
            "state": "failed",
            "stage": "failed",
            "buildId": "ea-build-mt5-verified",
            "sourceDigest": "a" * 64,
            "baselineReportSha256": "b" * 64,
            "platform": "mt5",
            "requestDigest": "d" * 64,
            "terminalBinding": self.terminal_binding(),
            "testerSettings": {},
            "progress": {},
            "recovery": {"executionMayStillBeRunning": False},
            "failure": {"code": "terminal_binding_changed"},
            "evidence": [],
        }
        mission_id, report_id = self.bridge._ea_factory_optimization_terminal_report_ids(
            session["id"]
        )
        fixed_time = "2026-10-16T00:00:00Z"
        mission_store: list[dict] = []
        audit_rows: list[dict] = []
        created: list[dict] = []

        def create_mission_side_effect(
            payload: dict,
            status: str = "queued",
            **kwargs,
        ) -> dict:
            mission = (
                self.bridge._ea_factory_optimization_publication_mission_projection(
                    {"createdAt": fixed_time, "updatedAt": fixed_time},
                    mission_id=mission_id,
                    session_id=session["id"],
                    idempotency_key=payload["idempotencyKey"],
                    status=status,
                    result="",
                    report_ids=[],
                    completed_at=None,
                    staging_contract=kwargs.get(
                        "_trusted_optimization_publication_staging"
                    ),
                )
            )
            self.assertIsInstance(mission, dict)
            mission_store[:] = [copy.deepcopy(mission)]
            return copy.deepcopy(mission)

        def save_missions(rows: list[dict]) -> None:
            mission_store[:] = copy.deepcopy(rows)

        def append_audit_once(row: dict) -> bool:
            event_id = row.get("eventId")
            if any(item.get("eventId") == event_id for item in audit_rows):
                return False
            audit_rows.append({"time": fixed_time, **copy.deepcopy(row)})
            return True

        with tempfile.TemporaryDirectory() as temporary:
            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", Path(temporary)),
                mock.patch.object(
                    self.bridge,
                    "find_mission",
                    side_effect=lambda candidate: copy.deepcopy(
                        next(
                            (
                                row
                                for row in mission_store
                                if row.get("id") == candidate
                            ),
                            None,
                        )
                    ),
                ),
                mock.patch.object(
                    self.bridge,
                    "create_mission",
                    side_effect=create_mission_side_effect,
                ),
                mock.patch.object(
                    self.bridge,
                    "create_report",
                    side_effect=lambda payload, **_kwargs: (
                        created.append(copy.deepcopy(payload))
                        or copy.deepcopy(payload)
                    ),
                ),
                mock.patch.object(
                    self.bridge,
                    "load_missions",
                    side_effect=lambda: copy.deepcopy(mission_store),
                ),
                mock.patch.object(
                    self.bridge,
                    "save_missions",
                    side_effect=save_missions,
                ),
                mock.patch.object(
                    self.bridge,
                    "tail_jsonl",
                    side_effect=lambda *_args, **_kwargs: copy.deepcopy(audit_rows),
                ),
                mock.patch.object(
                    self.bridge,
                    "append_audit",
                    side_effect=lambda row: audit_rows.append(copy.deepcopy(row)),
                ),
                mock.patch.object(
                    self.bridge,
                    "append_audit_once",
                    side_effect=append_audit_once,
                ),
                mock.patch.object(self.bridge, "utc_now", return_value=fixed_time),
            ):
                published = self.bridge._ea_factory_optimization_publish_terminal_report(
                    session
                )

        self.assertEqual(
            published,
            {"missionId": mission_id, "reportId": report_id, "state": "failed"},
        )
        self.assertEqual(created[0]["status"], "failed")
        self.assertEqual(created[0]["executionEvidence"], {})
        self.assertFalse(created[0]["metrics"]["execution"]["available"])
        self.assertEqual(created[0]["artifacts"], [])
        self.assertEqual(mission_store[0]["status"], "failed")
        self.assertEqual(mission_store[0]["reportIds"], [report_id])

    def test_http_routes_dispatch_read_create_resume_and_cancel(self) -> None:
        session_id = "opts_" + "9" * 32
        read_result = {
            "ok": True,
            "eaOptimizationLab": {"schemaVersion": "ea-optimization-lab-v1"},
        }
        create_result = {
            "ok": True,
            "session": {"sessionId": session_id, "state": "queued"},
            "workerStarted": True,
        }
        resume_result = {
            "ok": True,
            "session": {"sessionId": session_id, "state": "running"},
            "workerStarted": True,
        }
        cancel_result = {
            "ok": True,
            "session": {"sessionId": session_id, "state": "cancelled"},
        }
        with (
            mock.patch.object(
                self.bridge,
                "ea_factory_optimization_read_model",
                return_value=read_result,
            ) as read,
            mock.patch.object(
                self.bridge,
                "create_ea_factory_optimization_session",
                return_value=create_result,
            ) as create,
            mock.patch.object(
                self.bridge,
                "resume_ea_factory_optimization_session",
                return_value=resume_result,
            ) as resume,
            mock.patch.object(
                self.bridge,
                "cancel_ea_factory_optimization_session",
                return_value=cancel_result,
            ) as cancel,
        ):
            server = self.bridge.BridgeHTTPServer(
                ("127.0.0.1", 0), self.bridge.BridgeHandler
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                status, body = self.request(
                    server.server_port, "GET", "/api/ea-optimization-lab"
                )
                self.assertEqual((status, body), (200, read_result))

                create_payload = self.browser_payload()
                status, body = self.request(
                    server.server_port,
                    "POST",
                    "/api/ea-optimization-lab/sessions",
                    create_payload,
                )
                self.assertEqual((status, body), (200, create_result))

                resume_payload = {"idempotencyKey": "eaopt-resume-http-0001"}
                status, body = self.request(
                    server.server_port,
                    "POST",
                    f"/api/ea-optimization-lab/sessions/{session_id}/resume",
                    resume_payload,
                )
                self.assertEqual((status, body), (200, resume_result))

                status, body = self.request(
                    server.server_port,
                    "POST",
                    f"/api/ea-optimization-lab/sessions/{session_id}/cancel",
                    {},
                )
                self.assertEqual((status, body), (200, cancel_result))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

        read.assert_called_once_with()
        create.assert_called_once_with(create_payload)
        resume.assert_called_once_with(session_id, resume_payload)
        cancel.assert_called_once_with(session_id, {})


if __name__ == "__main__":
    unittest.main()
