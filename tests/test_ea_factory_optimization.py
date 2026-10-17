from __future__ import annotations

import concurrent.futures
import hashlib
import importlib.util
import json
import os
import stat
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    PROJECT_ROOT
    / "backend"
    / "local-runner"
    / "hq_backend"
    / "ea"
    / "ea_factory_optimization.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "ea_factory_optimization_test_module", MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeClock:
    def __init__(self, value: float = 1_800_000_000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class CrashAfterStart(BaseException):
    pass


class OptimizationFixture:
    def __init__(self, test: unittest.TestCase, module) -> None:
        self.test = test
        self.module = module
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve(strict=True)
        self.clock = FakeClock()
        self.platform = "mt5"
        self.candidate_id = "mtc-" + "m" * 26
        self.revision = 7
        self.binding_digest = hashlib.sha256(b"mt5-binding-v7").hexdigest()
        self.terminal_ref = "terminal_" + "t" * 24
        self.ready = True
        self.capability_reason = None
        self.handler_calls: list[dict] = []
        self.handler_results: list[object] = []
        self.receipts: dict[str, dict] = {}
        self.audits: list[dict] = []
        self.resolve_barrier: threading.Barrier | None = None
        self.include_execution_identity = False
        self.stop_proof_results: list[object] = []
        self.stop_proof_calls: list[dict] = []

    def cleanup(self) -> None:
        self.temp.cleanup()

    def request(
        self,
        *,
        key: str = "optimization-request-0001",
        platform: str | None = None,
        rounds: list[dict] | None = None,
        **updates,
    ) -> dict:
        selected_platform = platform or self.platform
        request = {
            "idempotencyKey": key,
            "buildId": "build-safe-v01",
            "sourceDigest": hashlib.sha256(b"source-v01").hexdigest(),
            "baselineReportSha256": hashlib.sha256(b"visual-baseline").hexdigest(),
            "platform": selected_platform,
            "terminalCandidateId": self.candidate_id,
            "terminalSelectionRevision": self.revision,
            "terminalBindingDigest": self.binding_digest,
            "testerSettings": {
                "symbol": "XAUUSD",
                "period": "H1",
                "model": "every_tick_based_on_real_ticks",
                "useDate": True,
                "fromDate": "2025-01-01",
                "toDate": "2025-12-31",
                "optimizationMode": "fast_genetic",
                "criterion": "recovery_factor_max",
            },
            "rounds": rounds
            or [
                {
                    "label": "Balanced modes",
                    "ranges": [
                        {
                            "name": "RiskPercent",
                            "kind": "numeric",
                            "start": 0.5,
                            "step": 0.5,
                            "stop": 1.0,
                        },
                        {
                            "name": "EntryMode",
                            "kind": "categorical",
                            "values": ["safe", "balanced"],
                        },
                    ],
                }
            ],
        }
        request.update(updates)
        return request

    def resolver(self, expected: dict) -> dict:
        if self.resolve_barrier is not None:
            self.resolve_barrier.wait(timeout=5)
        return {
            "candidateId": self.candidate_id,
            "platform": self.platform,
            "selectionRevision": self.revision,
            "bindingDigest": self.binding_digest,
            "terminalRef": self.terminal_ref,
        }

    def capability(self, request: dict) -> dict:
        self.test.assertFalse(request["liveTradingAllowed"])
        self.test.assertFalse(request["testShutdownTerminal"])
        self.test.assertFalse(request["closeTerminalAllowed"])
        result = {
            "ready": self.ready,
            "platform": self.platform,
            "candidateId": self.candidate_id,
            "selectionRevision": self.revision,
            "bindingDigest": self.binding_digest,
        }
        if self.capability_reason is not None:
            result["reasonCode"] = self.capability_reason
        if self.include_execution_identity:
            identity = {
                "schemaVersion": self.module.EXECUTION_IDENTITY_SCHEMA,
                "terminalCandidateId": self.candidate_id,
                "terminalSelectionRevision": self.revision,
                "terminalBindingDigest": self.binding_digest,
                "terminalProcessId": 42001,
                "terminalProcessCreatedAt100ns": 133700000000000000,
                "terminalWindowHandle": 88001,
                "terminalExecutablePathDigest": hashlib.sha256(
                    b"c:/program files/metatrader 5/terminal64.exe"
                ).hexdigest(),
                "terminalExecutableSha256": hashlib.sha256(
                    b"terminal64.exe"
                ).hexdigest(),
                "capturedAt": self.clock(),
            }
            identity["identitySha256"] = self.module._sha256_json(identity)
            result["executionIdentity"] = identity
        return result

    def stop_prover(self, request: dict) -> dict:
        self.stop_proof_calls.append(request)
        self.test.assertEqual(request["action"], "prove_execution_stopped")
        self.test.assertFalse(request["liveTradingAllowed"])
        self.test.assertFalse(request["closeTerminalAllowed"])
        self.test.assertFalse(request["testShutdownTerminal"])
        if not self.stop_proof_results:
            raise AssertionError("No fake execution-stop proof queued")
        result = self.stop_proof_results.pop(0)
        if isinstance(result, BaseException):
            raise result
        if callable(result):
            return result(request)
        return result

    def handler(self, request: dict) -> dict:
        self.handler_calls.append(request)
        self.test.assertFalse(request["safety"]["liveTradingAllowed"])
        self.test.assertFalse(request["safety"]["closeTerminalAllowed"])
        self.test.assertFalse(request["safety"]["testShutdownTerminal"])
        if not self.handler_results:
            raise AssertionError("No fake handler result queued")
        result = self.handler_results.pop(0)
        if isinstance(result, BaseException):
            raise result
        if callable(result):
            return result(request)
        return result

    def service(self, **kwargs):
        return self.module.EaFactoryOptimizationService(
            self.root,
            target_resolver=self.resolver,
            capability_provider=self.capability,
            optimization_handler=self.handler,
            execution_stop_prover=self.stop_prover,
            audit_callback=self.audits.append,
            clock=self.clock,
            heartbeat_timeout_seconds=120,
            session_deadline_seconds=600,
            **kwargs,
        )

    def receipt(self, request: dict, *, platform: str | None = None) -> dict:
        operation = request["operation"]
        binding = request["terminalBinding"]
        if platform is None and operation["operationId"] in self.receipts:
            return dict(self.receipts[operation["operationId"]])
        receipt = {
            "schemaVersion": 1,
            "operationId": operation["operationId"],
            "roundId": request["round"]["roundId"],
            "receiptRef": "receipt_" + operation["operationId"][3:],
            "startBoundarySha256": operation["boundaryDocumentSha256"],
            "platform": platform or request["platform"],
            "terminalCandidateId": binding["candidateId"],
            "terminalSelectionRevision": binding["selectionRevision"],
            "terminalBindingDigest": binding["bindingDigest"],
            "startedAt": self.clock(),
        }
        if platform is None:
            self.receipts[operation["operationId"]] = dict(receipt)
        return receipt

    def evidence(
        self,
        request: dict,
        *,
        receipt: dict | None = None,
        pass_count: int = 4,
        returned_count: int | None = None,
        truncated: bool | None = None,
        rows: list[dict] | None = None,
        platform: str | None = None,
        report_digest: str | None = None,
        tester_settings_digest: str | None = None,
    ) -> dict:
        receipt = receipt or self.receipt(request)
        returned_count = pass_count if returned_count is None else returned_count
        truncated = returned_count < pass_count if truncated is None else truncated
        if rows is None:
            rows = [
                {
                    "pass": index + 1,
                    "profit": float(100 + index),
                    "mode": "safe" if index % 2 == 0 else "balanced",
                }
                for index in range(max(0, returned_count))
            ]
        binding = request["terminalBinding"]
        return {
            "schemaVersion": 1,
            "operationId": request["operation"]["operationId"],
            "roundId": request["round"]["roundId"],
            "receiptRef": receipt["receiptRef"],
            "platform": platform or request["platform"],
            "terminalCandidateId": binding["candidateId"],
            "terminalSelectionRevision": binding["selectionRevision"],
            "terminalBindingDigest": binding["bindingDigest"],
            "passCount": pass_count,
            "returnedPassCount": returned_count,
            "rowsTruncated": truncated,
            "resultRows": rows,
            "report": {
                "ref": "report_" + "r" * 24,
                "sha256": report_digest or hashlib.sha256(b"report-v1").hexdigest(),
                "byteSize": 4096,
            },
            "manifest": {
                "ref": "manifest_" + "m" * 24,
                "sha256": hashlib.sha256(b"manifest-v1").hexdigest(),
                "byteSize": 1024,
            },
            "testerSettingsSha256": tester_settings_digest
            or hashlib.sha256(
                json.dumps(
                    request["testerSettings"],
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
            "visibleEvidenceSha256": hashlib.sha256(b"visible-screenshot").hexdigest(),
            "initialDeposit": 10_000.0,
            "testShutdownTerminal": False,
            "liveTrading": False,
            "warnings": [],
        }

    def completed_result(self, request: dict, **evidence_updates) -> dict:
        receipt = self.receipt(request)
        return {
            "status": "completed",
            "receipt": receipt,
            "evidence": self.evidence(
                request, receipt=receipt, **evidence_updates
            ),
        }

    def started_result(self, request: dict, *, progress: float = 1.0) -> dict:
        return {
            "status": "started",
            "receipt": self.receipt(request),
            "progressPercent": progress,
            "passCount": 0,
        }

    def advance_to_run_round(self, service, session_id: str) -> None:
        first = service.resume(session_id)
        self.test.assertEqual(first["stage"], "prepare_ranges")
        second = service.resume(session_id)
        self.test.assertEqual(second["stage"], "run_round")

    def complete_one_round(self, service, session_id: str) -> dict:
        self.handler_results.append(lambda request: self.completed_result(request))
        self.advance_to_run_round(service, session_id)
        after_handler = service.resume(session_id)
        self.test.assertEqual(after_handler["stage"], "verify_report")
        self.test.assertEqual(service.resume(session_id)["stage"], "analyze")
        self.test.assertEqual(service.resume(session_id)["stage"], "complete")
        return service.resume(session_id)

    def finish_verified_round(self, service, session_id: str) -> dict:
        current = service.read(session_id)
        self.test.assertEqual(current["state"], "running")
        self.test.assertEqual(current["stage"], "verify_report")
        self.test.assertEqual(service.resume(session_id)["stage"], "analyze")
        self.test.assertEqual(service.resume(session_id)["stage"], "complete")
        completed = service.resume(session_id)
        self.test.assertEqual(completed["state"], "completed")
        return completed

    def legacy_completed_late_discard(self, service, session_id: str) -> dict:
        """Create the exact terminal shape emitted by the deployed old policy."""

        self.handler_results.append(
            lambda request: self.started_result(request, progress=20)
        )
        self.advance_to_run_round(service, session_id)
        started = service.resume(session_id)
        self.test.assertEqual(started["state"], "collecting")
        self.clock.advance(601)
        quarantined = service.read(session_id)
        self.test.assertTrue(
            quarantined["failure"]["executionMayStillBeRunning"]
        )
        self.handler_results.append(lambda request: self.completed_result(request))
        original = service._process_execution_quarantine_result

        def deployed_discard_policy(store, session, action, result):
            if action in {"recover_round", "collect_round"} and result.get(
                "status"
            ) == "completed":
                service._attach_receipt(session, result["receipt"])
                service._validate_evidence(session, result["evidence"])
                event = service._finalize_quarantined_failure_record(
                    session,
                    self.clock(),
                    proof="completed_late_discarded",
                )
                service._save_unlocked(store)
                service._audit(event)
                return
            return original(store, session, action, result)

        with mock.patch.object(
            service,
            "_process_execution_quarantine_result",
            side_effect=deployed_discard_policy,
        ):
            terminal = service.resume(session_id)
        self.test.assertEqual(terminal["state"], "failed")
        self.test.assertTrue(
            terminal["recovery"]["lateCompletedResultRecoveryAvailable"]
        )
        return terminal


class EaFactoryOptimizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def setUp(self) -> None:
        self.fixture = OptimizationFixture(self, self.module)

    def tearDown(self) -> None:
        self.fixture.cleanup()

    def assert_error(self, code: str, call, *, status: int | None = None):
        with self.assertRaises(self.module.OptimizationDomainError) as raised:
            call()
        self.assertEqual(raised.exception.code, code)
        if status is not None:
            self.assertEqual(raised.exception.status, status)
        return raised.exception

    def test_public_api_and_complete_mt5_categorical_mode_round(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.assertEqual(created["state"], "queued")
        self.assertEqual(created["stage"], "validate_baseline")
        self.assertFalse(created["replayed"])
        self.assertFalse(created["liveTradingAllowed"])
        self.assertFalse(created["testShutdownTerminal"])

        completed = self.fixture.complete_one_round(service, created["id"])
        self.assertEqual(completed["state"], "completed")
        self.assertEqual(completed["stage"], "complete")
        self.assertEqual(completed["evidence"][0]["passCount"], 4)
        self.assertEqual(len(completed["evidence"][0]["resultRows"]), 4)
        self.assertFalse(
            completed["evidence"][0]["publicResultRowsTruncated"]
        )
        self.assertEqual(
            completed["evidence"][0]["resultRowsSha256"],
            hashlib.sha256(
                json.dumps(
                    completed["evidence"][0]["resultRows"],
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
        )
        self.assertEqual(completed["round"]["combinationCount"], 4)
        handler_request = self.fixture.handler_calls[0]
        self.assertEqual(handler_request["action"], "start_round")
        self.assertEqual(handler_request["platform"], "mt5")
        self.assertEqual(
            handler_request["testerSettings"],
            self.fixture.request()["testerSettings"],
        )
        self.assertEqual(completed["testerSettings"], handler_request["testerSettings"])
        mode = handler_request["round"]["ranges"][1]
        self.assertEqual(mode["kind"], "categorical")
        self.assertEqual(mode["values"], ["safe", "balanced"])
        self.assertTrue(handler_request["safety"]["startAllowed"])
        self.assertNotIn(str(self.fixture.root), json.dumps(handler_request))
        self.assertNotIn("idempotencyKey", json.dumps(handler_request))
        self.assertTrue(any(row["type"] == "session_completed" for row in self.fixture.audits))

    def test_idempotent_replay_conflict_and_single_active_busy(self) -> None:
        service = self.fixture.service()
        request = self.fixture.request()
        first = service.create(request)
        self.fixture.platform = "mt4"
        replay = service.create(dict(request))
        self.assertEqual(replay["id"], first["id"])
        self.assertTrue(replay["replayed"])
        self.fixture.platform = "mt5"

        conflict = dict(request)
        conflict["sourceDigest"] = hashlib.sha256(b"different source").hexdigest()
        self.assert_error(
            "idempotency_conflict", lambda: service.create(conflict), status=409
        )
        self.assert_error(
            "optimization_busy",
            lambda: service.create(self.fixture.request(key="optimization-request-0002")),
            status=409,
        )

    def test_list_returns_validated_public_sessions_newest_first(self) -> None:
        service = self.fixture.service()
        first = service.create(self.fixture.request())
        self.fixture.clock.advance(1)
        service.cancel(first["id"])
        self.fixture.clock.advance(1)
        second = service.create(
            self.fixture.request(key="optimization-request-list-0002")
        )
        listed = service.list()
        self.assertEqual([item["id"] for item in listed], [second["id"], first["id"]])
        self.assertEqual(listed[0]["testerSettings"], second["testerSettings"])
        self.assertNotIn("request", listed[0])
        self.assertNotIn("idempotencyKey", json.dumps(listed))

    def test_concurrent_create_admits_exactly_one_session(self) -> None:
        service = self.fixture.service()
        barrier = threading.Barrier(2)

        def create(index: int):
            barrier.wait(timeout=5)
            try:
                return ("ok", service.create(self.fixture.request(key=f"concurrent-key-000{index}")))
            except self.module.OptimizationDomainError as error:
                return (error.code, None)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(create, (1, 2)))
        self.assertEqual(sum(kind == "ok" for kind, _ in results), 1)
        self.assertEqual(sum(kind == "optimization_busy" for kind, _ in results), 1)

    def test_queued_cancel_is_immediate_and_terminal_cancel_is_idempotent(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        cancelled = service.cancel(created["id"], reason="operator_cancelled")
        self.assertEqual(cancelled["state"], "cancelled")
        self.assertTrue(cancelled["cancelRequested"])
        again = service.cancel(created["id"], reason="different_reason")
        self.assertEqual(again["state"], "cancelled")
        self.assertEqual(again["cancelReason"], "operator_cancelled")
        self.assertEqual(self.fixture.handler_calls, [])

    def test_cancel_after_start_collects_evidence_without_stopping_or_restarting(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: self.fixture.started_result(request, progress=10)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        started = service.resume(created["id"])
        self.assertEqual(started["state"], "collecting")
        pending = service.cancel(created["id"], reason="operator_cancelled")
        self.assertEqual(pending["state"], "collecting")
        self.assertTrue(pending["cancelRequested"])

        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request)
        )
        collected = service.resume(created["id"])
        self.assertEqual(collected["stage"], "verify_report")
        cancelled = service.resume(created["id"])
        self.assertEqual(cancelled["state"], "cancelled")
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls],
            ["start_round", "collect_round"],
        )
        self.assertFalse(self.fixture.handler_calls[1]["safety"]["startAllowed"])
        self.assertTrue(self.fixture.handler_calls[1]["safety"]["neverStart"])

    def test_timeout_marks_failed_and_releases_single_active_slot(self) -> None:
        service = self.fixture.service()
        first = service.create(self.fixture.request())
        self.fixture.clock.advance(121)
        second = service.create(self.fixture.request(key="optimization-request-0002"))
        self.assertNotEqual(second["id"], first["id"])
        expired = service.read(first["id"])
        self.assertEqual(expired["state"], "failed")
        self.assertEqual(expired["failure"]["code"], "session_heartbeat_timeout")

    def test_heartbeat_timeout_after_start_quarantines_and_adapter_failure_is_not_proof(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: self.fixture.started_result(request, progress=10)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        service.resume(created["id"])

        self.fixture.clock.advance(121)
        quarantined = service.read(created["id"])
        self.assertIn(quarantined["state"], self.module.ACTIVE_STATES)
        self.assertEqual(
            quarantined["failure"]["code"], "session_heartbeat_timeout"
        )
        self.assertTrue(quarantined["failure"]["executionMayStillBeRunning"])
        self.assert_error(
            "optimization_busy",
            lambda: service.create(
                self.fixture.request(key="optimization-request-heartbeat-busy")
            ),
            status=409,
        )

        self.fixture.handler_results.append(
            lambda request: {
                "status": "failed",
                "reasonCode": "visible_ui_timeout",
                "receipt": self.fixture.receipt(request),
            }
        )
        still_quarantined = service.resume(created["id"])
        self.assertIn(still_quarantined["state"], self.module.ACTIVE_STATES)
        self.assertTrue(
            still_quarantined["failure"]["executionMayStillBeRunning"]
        )
        self.assert_error(
            "optimization_busy",
            lambda: service.create(
                self.fixture.request(key="optimization-request-failed-not-proof")
            ),
            status=409,
        )

        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request)
        )
        recovered = service.resume(created["id"])
        self.assertEqual(recovered["state"], "running")
        self.assertEqual(recovered["stage"], "verify_report")
        self.assertIsNone(recovered["failure"])
        self.assertEqual(len(recovered["evidence"]), 1)
        terminal = self.fixture.finish_verified_round(service, created["id"])
        self.assertEqual(terminal["state"], "completed")
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls],
            ["start_round", "collect_round", "collect_round"],
        )

    def test_terminal_revision_or_digest_change_fails_closed(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.revision += 1
        error = self.assert_error(
            "terminal_binding_changed", lambda: service.resume(created["id"]), status=409
        )
        self.assertIn("changed", str(error))
        self.assertEqual(service.read(created["id"])["state"], "failed")

    def test_binding_change_after_start_keeps_slot_until_old_operation_is_terminal(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: self.fixture.started_result(request, progress=10)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        service.resume(created["id"])

        self.fixture.revision += 1
        self.assert_error(
            "terminal_binding_changed", lambda: service.resume(created["id"]), status=409
        )
        quarantined = service.read(created["id"])
        self.assertIn(quarantined["state"], self.module.ACTIVE_STATES)
        self.assertEqual(quarantined["failure"]["code"], "terminal_binding_changed")
        self.assertTrue(quarantined["failure"]["executionMayStillBeRunning"])
        self.assert_error(
            "optimization_busy",
            lambda: service.create(
                self.fixture.request(key="optimization-request-binding-busy")
            ),
            status=409,
        )

        self.fixture.revision -= 1
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request)
        )
        recovered = service.resume(created["id"])
        self.assertEqual(recovered["state"], "running")
        self.assertEqual(recovered["stage"], "verify_report")
        self.assertIsNone(recovered["failure"])
        self.assertEqual(len(recovered["evidence"]), 1)
        terminal = self.fixture.finish_verified_round(service, created["id"])
        self.assertEqual(terminal["state"], "completed")
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls],
            ["start_round", "collect_round"],
        )

    def test_operator_cancel_releases_replaced_terminal_only_after_stopped_proof(self) -> None:
        self.fixture.include_execution_identity = True
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: self.fixture.started_result(request, progress=10)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        started = service.resume(created["id"])
        self.assertTrue(started["recovery"]["executionIdentityCaptured"])

        self.fixture.revision += 1
        self.assert_error(
            "terminal_binding_changed", lambda: service.resume(created["id"]), status=409
        )

        def still_running(request):
            return {
                "status": "execution_still_running",
                "reasonCode": "terminal_process_still_running",
                "observedAt": self.fixture.clock(),
                "identitySha256": request["executionIdentity"]["identitySha256"],
            }

        self.fixture.stop_proof_results.append(still_running)
        pending = service.cancel(
            created["id"],
            reason="operator_cancelled",
            confirm_execution_stopped=True,
        )
        self.assertIn(pending["state"], self.module.ACTIVE_STATES)
        self.assertTrue(pending["cancelRequested"])
        self.assertFalse(pending["recovery"]["executionStopProofPresent"])
        self.assert_error(
            "optimization_busy",
            lambda: service.create(
                self.fixture.request(key="optimization-request-proof-still-running")
            ),
            status=409,
        )

        def stopped(request):
            return {
                "status": "execution_stopped",
                "reasonCode": "terminal_process_replaced",
                "observedAt": self.fixture.clock(),
                "identitySha256": request["executionIdentity"]["identitySha256"],
                "proofSha256": hashlib.sha256(
                    b"original terminal and tester agents stopped"
                ).hexdigest(),
            }

        self.fixture.stop_proof_results.append(stopped)
        cancelled = service.cancel(
            created["id"],
            reason="operator_cancelled",
            confirm_execution_stopped=True,
        )
        self.assertEqual(cancelled["state"], "cancelled")
        self.assertTrue(cancelled["recovery"]["executionStopProofPresent"])
        self.assertFalse(cancelled["failure"]["executionMayStillBeRunning"])
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls], ["start_round"]
        )
        replacement = service.create(
            self.fixture.request(key="optimization-request-after-stopped-proof")
        )
        self.assertEqual(replacement["state"], "queued")

    def test_invalid_execution_stop_proof_never_releases_active_slot(self) -> None:
        self.fixture.include_execution_identity = True
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: self.fixture.started_result(request, progress=10)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        service.resume(created["id"])
        self.fixture.revision += 1
        self.assert_error(
            "terminal_binding_changed", lambda: service.resume(created["id"]), status=409
        )
        self.fixture.stop_proof_results.append(
            lambda request: {
                "status": "execution_stopped",
                "reasonCode": "terminal_process_replaced",
                "observedAt": self.fixture.clock(),
                "identitySha256": hashlib.sha256(b"wrong identity").hexdigest(),
                "proofSha256": hashlib.sha256(b"unbound proof").hexdigest(),
            }
        )
        pending = service.cancel(
            created["id"], confirm_execution_stopped=True
        )
        self.assertIn(pending["state"], self.module.ACTIVE_STATES)
        self.assertFalse(pending["recovery"]["executionStopProofPresent"])
        self.assert_error(
            "optimization_busy",
            lambda: service.create(
                self.fixture.request(key="optimization-request-invalid-stop-proof")
            ),
            status=409,
        )

    def test_adapter_failed_after_start_is_ambiguous_until_completed_proof(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: {
                "status": "failed",
                "reasonCode": "visible_ui_timeout",
                "receipt": self.fixture.receipt(request),
            }
        )
        self.fixture.advance_to_run_round(service, created["id"])
        self.assert_error(
            "visible_ui_timeout", lambda: service.resume(created["id"]), status=409
        )
        quarantined = service.read(created["id"])
        self.assertIn(quarantined["state"], self.module.ACTIVE_STATES)
        self.assertTrue(quarantined["failure"]["executionMayStillBeRunning"])

        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request)
        )
        recovered = service.resume(created["id"])
        self.assertEqual(recovered["state"], "running")
        self.assertEqual(recovered["stage"], "verify_report")
        self.assertIsNone(recovered["failure"])
        self.assertEqual(len(recovered["evidence"]), 1)
        terminal = self.fixture.finish_verified_round(service, created["id"])
        self.assertEqual(terminal["state"], "completed")
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls],
            ["start_round", "collect_round"],
        )

    def test_platform_isolation_applies_to_resolver_and_handler_evidence(self) -> None:
        self.fixture.platform = "mt4"
        service = self.fixture.service()
        self.assert_error(
            "terminal_platform_mismatch",
            lambda: service.create(self.fixture.request(platform="mt5")),
            status=409,
        )

        self.fixture.platform = "mt5"
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request, platform="mt4")
        )
        self.fixture.advance_to_run_round(service, created["id"])
        self.assert_error(
            "evidence_binding_mismatch", lambda: service.resume(created["id"]), status=409
        )
        quarantined = service.read(created["id"])
        self.assertIn(quarantined["state"], self.module.ACTIVE_STATES)
        self.assertTrue(quarantined["failure"]["executionMayStillBeRunning"])
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request)
        )
        recovered = service.resume(created["id"])
        self.assertEqual(recovered["state"], "running")
        self.assertEqual(recovered["stage"], "verify_report")
        self.assertIsNone(recovered["failure"])
        self.assertEqual(len(recovered["evidence"]), 1)
        terminal = self.fixture.finish_verified_round(service, created["id"])
        self.assertEqual(terminal["state"], "completed")

    def test_capability_wait_does_not_call_handler_and_can_resume(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.ready = False
        self.fixture.capability_reason = "tester_not_visible"
        waiting = service.resume(created["id"])
        self.assertEqual(waiting["state"], "awaiting_visible_terminal")
        self.assertEqual(self.fixture.handler_calls, [])
        self.fixture.ready = True
        resumed = service.resume(created["id"])
        self.assertEqual(resumed["stage"], "prepare_ranges")

    def test_frontend_paths_secrets_and_live_controls_are_rejected(self) -> None:
        service = self.fixture.service()
        for field, value, code in (
            ("sourcePath", r"C:\\Users\\student\\unsafe.mq5", "invalid_request"),
            ("liveTrading", True, "live_trading_forbidden"),
            ("testShutdownTerminal", True, "live_trading_forbidden"),
        ):
            with self.subTest(field=field):
                request = self.fixture.request()
                request[field] = value
                self.assert_error(code, lambda request=request: service.create(request))

        path_value = self.fixture.request()
        path_value["rounds"][0]["ranges"][1]["values"] = [r"C:\\secret.set"]
        self.assert_error("path_not_allowed", lambda: service.create(path_value))

        secret_value = self.fixture.request()
        secret_value["rounds"][0]["ranges"][1]["values"] = [
            "sk-abcdefghijklmnop"
        ]
        self.assert_error("secret_not_allowed", lambda: service.create(secret_value))

    def test_mode_must_be_categorical_and_range_limits_are_enforced(self) -> None:
        service = self.fixture.service()
        request = self.fixture.request()
        request["rounds"][0]["ranges"][1] = {
            "name": "EntryMode",
            "kind": "numeric",
            "start": 1,
            "step": 1,
            "stop": 2,
        }
        self.assert_error(
            "mode_range_must_be_categorical", lambda: service.create(request)
        )

        too_many = self.fixture.request()
        too_many["rounds"][0]["ranges"] = [
            {
                "name": "HugeRange",
                "kind": "numeric",
                "start": 0,
                "step": 1,
                "stop": self.module.MAX_COMBINATIONS_PER_ROUND,
            }
        ]
        self.assert_error("range_too_large", lambda: service.create(too_many))

        huge_exponent = self.fixture.request()
        huge_exponent["rounds"][0]["ranges"][0]["start"] = "1e999999999"
        self.assert_error("invalid_request", lambda: service.create(huge_exponent))

        singleton = self.fixture.request()
        singleton["rounds"][0]["ranges"] = [
            {
                "name": "RiskPercent",
                "kind": "numeric",
                "start": 1,
                "step": 1,
                "stop": 1,
            }
        ]
        self.assert_error(
            "optimization_requires_multiple_combinations",
            lambda: service.create(singleton),
            status=422,
        )

    def test_tester_settings_are_exact_bounded_and_date_consistent(self) -> None:
        service = self.fixture.service()

        missing = self.fixture.request()
        del missing["testerSettings"]["criterion"]
        self.assert_error("invalid_request", lambda: service.create(missing), status=422)

        cases = (
            ("period", "S1"),
            ("model", "invented_model"),
            ("optimizationMode", "live"),
            ("criterion", "unknown_metric"),
            ("symbol", r"C:\\XAUUSD"),
        )
        for field, value in cases:
            with self.subTest(field=field):
                request = self.fixture.request()
                request["testerSettings"][field] = value
                self.assert_error(
                    "invalid_tester_settings"
                    if field != "symbol"
                    else "path_not_allowed",
                    lambda request=request: service.create(request),
                    status=422,
                )

        reverse_dates = self.fixture.request()
        reverse_dates["testerSettings"]["fromDate"] = "2026-02-01"
        reverse_dates["testerSettings"]["toDate"] = "2026-01-31"
        self.assert_error(
            "invalid_tester_settings",
            lambda: service.create(reverse_dates),
            status=422,
        )

        bad_date = self.fixture.request()
        bad_date["testerSettings"]["fromDate"] = "2025-02-30"
        self.assert_error(
            "invalid_tester_settings", lambda: service.create(bad_date), status=422
        )

        inconsistent = self.fixture.request()
        inconsistent["testerSettings"].update(
            {"useDate": False, "fromDate": "2025-01-01", "toDate": None}
        )
        self.assert_error(
            "invalid_tester_settings",
            lambda: service.create(inconsistent),
            status=422,
        )

        no_dates = self.fixture.request()
        no_dates["testerSettings"].update(
            {"useDate": False, "fromDate": None, "toDate": None}
        )
        created = service.create(no_dates)
        self.assertFalse(created["testerSettings"]["useDate"])
        self.assertIsNone(created["testerSettings"]["fromDate"])
        self.assertIsNone(created["testerSettings"]["toDate"])

    def test_risk_thresholds_are_exact_canonical_durable_and_forwarded(self) -> None:
        service = self.fixture.service()
        request = self.fixture.request(
            riskThresholds={
                "targetProfitPercent": 25,
                "maxDrawdownPercent": 12.5,
                "minimumTrades": 30,
            }
        )
        created = service.create(request)
        expected = {
            "targetProfitPercent": 25.0,
            "maxDrawdownPercent": 12.5,
            "minimumTrades": 30,
        }
        self.assertEqual(created["riskThresholds"], expected)

        self.fixture.handler_results.append(
            lambda handler_request: self.fixture.started_result(handler_request)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        service.resume(created["id"])
        self.assertEqual(self.fixture.handler_calls[0]["riskThresholds"], expected)
        restarted = self.fixture.service()
        self.assertEqual(restarted.read(created["id"])["riskThresholds"], expected)

        invalid_thresholds = (
            {
                "targetProfitPercent": True,
                "maxDrawdownPercent": 10,
                "minimumTrades": 1,
            },
            {
                "targetProfitPercent": 10,
                "maxDrawdownPercent": 100.01,
                "minimumTrades": 1,
            },
            {
                "targetProfitPercent": 10,
                "maxDrawdownPercent": 10,
                "minimumTrades": 0,
            },
            {
                "targetProfitPercent": 10,
                "maxDrawdownPercent": 10,
                "minimumTrades": 1,
                "unexpected": 1,
            },
        )
        for index, thresholds in enumerate(invalid_thresholds):
            with self.subTest(index=index):
                bad = self.fixture.request(
                    key=f"invalid-risk-thresholds-{index:02d}",
                    riskThresholds=thresholds,
                )
                self.assert_error(
                    "invalid_request", lambda bad=bad: service.create(bad), status=422
                )

    def test_analysis_enforces_all_risk_thresholds_and_is_idempotent(self) -> None:
        service = self.fixture.service()
        request = self.fixture.request(
            key="optimization-analysis-thresholds",
            riskThresholds={
                "targetProfitPercent": 0.75,
                "maxDrawdownPercent": 10,
                "minimumTrades": 50,
            },
        )
        rows = [
            {
                "pass": 1,
                "profit": 100.0,
                "drawdownPercent": 8.0,
                "trades": 60,
                "profitFactor": 1.4,
                "sharpeRatio": 1.2,
                "RiskPercent": 0.5,
                "EntryMode": "safe",
            },
            {
                "pass": 2,
                "profit": 60.0,
                "drawdownPercent": 6.0,
                "trades": 70,
                "profitFactor": 1.2,
                "sharpeRatio": 1.0,
                "RiskPercent": 0.5,
                "EntryMode": "balanced",
            },
            {
                "pass": 3,
                "profit": 120.0,
                "drawdownPercent": 12.0,
                "trades": 80,
                "profitFactor": 1.5,
                "sharpeRatio": 1.3,
                "RiskPercent": 1.0,
                "EntryMode": "safe",
            },
            {
                "pass": 4,
                "profit": 90.0,
                "drawdownPercent": 7.0,
                "trades": 40,
                "profitFactor": 1.3,
                "sharpeRatio": 1.1,
                "RiskPercent": 1.0,
                "EntryMode": "balanced",
            },
        ]
        created = service.create(request)
        self.fixture.handler_results.append(
            lambda handler_request: self.fixture.completed_result(
                handler_request, rows=rows
            )
        )
        self.fixture.advance_to_run_round(service, created["id"])
        self.assertEqual(service.resume(created["id"])["stage"], "verify_report")
        self.assertEqual(service.resume(created["id"])["stage"], "analyze")
        analyzed = service.resume(created["id"])
        self.assertEqual(analyzed["stage"], "complete")
        analysis = analyzed["evidence"][0]["analysis"]
        self.assertEqual(analysis["status"], "available")
        self.assertEqual(analysis["profitablePassCount"], 4)
        self.assertEqual(analysis["eligiblePassCount"], 1)
        for group in ("maxProfit", "lowestDrawdown", "mostStable"):
            self.assertEqual([row["pass"] for row in analysis["candidateGroups"][group]], [1])
        self.assertEqual(
            analysis["nextParameterPlan"],
            [
                {
                    "name": "RiskPercent",
                    "kind": "numeric",
                    "start": 0.5,
                    "step": "0.5",
                    "stop": 0.5,
                    "reason": "Range of verified passes that meet every risk threshold.",
                },
                {
                    "name": "EntryMode",
                    "kind": "categorical",
                    "values": ["safe"],
                    "reason": "Values from verified passes that meet every risk threshold.",
                },
            ],
        )
        digest = analyzed["evidence"][0]["analysisSha256"]
        self.assertRegex(digest, r"^[0-9a-f]{64}$")

        completed = service.resume(created["id"])
        self.assertEqual(completed["state"], "completed")
        self.assertEqual(completed["evidence"][0]["analysisSha256"], digest)
        restarted = self.fixture.service()
        self.assertEqual(restarted.read(created["id"])["evidence"][0]["analysis"], analysis)
        replay = restarted.resume(created["id"])
        self.assertEqual(replay["evidence"][0]["analysisSha256"], digest)

    def test_analysis_fails_closed_for_truncation_missing_metrics_and_bad_grid(self) -> None:
        cases = (
            (
                "truncated",
                dict(pass_count=4, returned_count=2, truncated=True),
                [
                    {"pass": 1, "profit": 100.0, "drawdownPercent": 5.0, "trades": 50, "sharpeRatio": 1.0, "RiskPercent": 0.5, "EntryMode": "safe"},
                    {"pass": 2, "profit": 90.0, "drawdownPercent": 6.0, "trades": 55, "sharpeRatio": 0.9, "RiskPercent": 1.0, "EntryMode": "balanced"},
                ],
                "verified_result_rows_truncated",
            ),
            (
                "missing-drawdown",
                {},
                [
                    {"pass": index + 1, "profit": 100.0 + index, "trades": 50 + index, "sharpeRatio": 1.0, "RiskPercent": 0.5 if index < 2 else 1.0, "EntryMode": "safe" if index % 2 == 0 else "balanced"}
                    for index in range(4)
                ],
                "drawdown_percent_metric_missing",
            ),
            (
                "bad-grid",
                {},
                [
                    {"pass": index + 1, "profit": 100.0 + index, "drawdownPercent": 5.0, "trades": 50 + index, "sharpeRatio": 1.0, "RiskPercent": 0.75 if index == 0 else (0.5 if index < 2 else 1.0), "EntryMode": "safe" if index % 2 == 0 else "balanced"}
                    for index in range(4)
                ],
                "optimized_parameter_value_out_of_range",
            ),
        )
        for case_index, (label, evidence_args, rows, reason) in enumerate(cases):
            with self.subTest(label=label):
                root = self.fixture.root / f"analysis-fail-closed-{case_index}"
                service = self.module.EaFactoryOptimizationService(
                    root,
                    target_resolver=self.fixture.resolver,
                    capability_provider=self.fixture.capability,
                    optimization_handler=self.fixture.handler,
                    clock=self.fixture.clock,
                    heartbeat_timeout_seconds=120,
                    session_deadline_seconds=600,
                )
                created = service.create(
                    self.fixture.request(
                        key=f"optimization-analysis-fail-{case_index}",
                        riskThresholds={
                            "targetProfitPercent": 0.5,
                            "maxDrawdownPercent": 10,
                            "minimumTrades": 25,
                        },
                    )
                )
                self.fixture.handler_results.append(
                    lambda handler_request, rows=rows, evidence_args=evidence_args: self.fixture.completed_result(
                        handler_request, rows=rows, **evidence_args
                    )
                )
                self.fixture.advance_to_run_round(service, created["id"])
                service.resume(created["id"])
                service.resume(created["id"])
                analyzed = service.resume(created["id"])["evidence"][0]["analysis"]
                self.assertEqual(analyzed["status"], "unavailable")
                self.assertIn(reason, analyzed["unavailableReasons"])
                self.assertEqual(analyzed["candidateGroups"]["maxProfit"], [])
                self.assertEqual(analyzed["nextParameterPlan"], [])
                self.assertFalse(analyzed["nextParameterPlanAvailable"])

    def test_handler_request_contains_only_opaque_backend_managed_references(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: self.fixture.started_result(request)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        service.resume(created["id"])
        request = self.fixture.handler_calls[0]
        serialized = json.dumps(request, sort_keys=True)
        self.assertNotIn(str(self.fixture.root), serialized)
        self.assertNotRegex(serialized, r"[A-Za-z]:\\")
        self.assertNotIn("path", serialized.casefold())
        self.assertTrue(request["workspaceRef"].startswith("optw_"))
        self.assertTrue(request["operation"]["boundaryRef"].startswith("boundary_"))

    def test_completed_evidence_must_match_exact_tester_settings(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(
                request,
                tester_settings_digest=hashlib.sha256(
                    b"different-tester-settings"
                ).hexdigest(),
            )
        )
        self.fixture.advance_to_run_round(service, created["id"])
        self.assert_error(
            "tester_settings_mismatch",
            lambda: service.resume(created["id"]),
            status=409,
        )
        quarantined = service.read(created["id"])
        self.assertIn(quarantined["state"], self.module.ACTIVE_STATES)
        self.assertTrue(quarantined["failure"]["executionMayStillBeRunning"])
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request)
        )
        recovered = service.resume(created["id"])
        self.assertEqual(recovered["state"], "running")
        self.assertEqual(recovered["stage"], "verify_report")
        self.assertIsNone(recovered["failure"])
        self.assertEqual(len(recovered["evidence"]), 1)
        terminal = self.fixture.finish_verified_round(service, created["id"])
        self.assertEqual(terminal["state"], "completed")

    def test_before_start_proof_allows_bounded_retry_with_new_operation(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        proof = hashlib.sha256(b"visible proof no Start").hexdigest()
        self.fixture.handler_results.extend(
            [
                {
                    "status": "before_start_retryable",
                    "notStartedProofSha256": proof,
                    "reasonCode": "layout_not_ready",
                },
                lambda request: self.fixture.started_result(request),
            ]
        )
        self.fixture.advance_to_run_round(service, created["id"])
        waiting = service.resume(created["id"])
        self.assertTrue(waiting["recovery"]["beforeStartRetryAllowed"])
        started = service.resume(created["id"])
        self.assertEqual(started["state"], "collecting")
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls],
            ["start_round", "start_round"],
        )
        self.assertNotEqual(
            self.fixture.handler_calls[0]["operation"]["operationId"],
            self.fixture.handler_calls[1]["operation"]["operationId"],
        )

    def test_transient_claim_audit_failure_rolls_back_before_dispatch(self) -> None:
        service = self.fixture.service()
        failed = {"handler_invocation_claimed": False}

        def flaky_audit(event):
            if (
                event["type"] == "handler_invocation_claimed"
                and not failed["handler_invocation_claimed"]
            ):
                failed["handler_invocation_claimed"] = True
                raise RuntimeError("transient audit sink failure")
            self.fixture.audits.append(event)

        service._audit_callback = flaky_audit
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: self.fixture.started_result(request)
        )
        self.fixture.advance_to_run_round(service, created["id"])

        self.assert_error(
            "audit_callback_failed", lambda: service.resume(created["id"]), status=503
        )
        rolled_back = service.read(created["id"])
        self.assertEqual(self.fixture.handler_calls, [])
        self.assertFalse(rolled_back["recovery"]["adapterCallInFlight"])
        self.assertTrue(rolled_back["recovery"]["beforeStartRetryAllowed"])

        resumed = service.resume(created["id"])
        self.assertEqual(resumed["state"], "collecting")
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls], ["start_round"]
        )
        durable = json.loads((self.fixture.root / self.module.STORE_FILENAME).read_text())
        event_types = durable["sessions"][0]["eventLog"]
        self.assertTrue(
            any(
                event["type"] == "undispatched_handler_claim_rolled_back"
                for event in event_types
            )
        )

    def test_transient_boundary_audit_failure_is_safe_before_start_retryable(self) -> None:
        service = self.fixture.service()
        failed = False

        def flaky_audit(event):
            nonlocal failed
            if event["type"] == "start_boundary_committed" and not failed:
                failed = True
                raise RuntimeError("transient audit sink failure")
            self.fixture.audits.append(event)

        service._audit_callback = flaky_audit
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: self.fixture.started_result(request)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        self.assert_error(
            "audit_callback_failed", lambda: service.resume(created["id"]), status=503
        )
        rolled_back = service.read(created["id"])
        self.assertEqual(self.fixture.handler_calls, [])
        self.assertFalse(rolled_back["recovery"]["adapterCallInFlight"])
        self.assertTrue(rolled_back["recovery"]["beforeStartRetryAllowed"])
        resumed = service.resume(created["id"])
        self.assertEqual(resumed["state"], "collecting")
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls], ["start_round"]
        )

    def test_collect_claim_audit_failure_never_reopens_start_boundary(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.extend([
            lambda request: self.fixture.started_result(request),
            lambda request: self.fixture.completed_result(request),
        ])
        self.fixture.advance_to_run_round(service, created["id"])
        collecting = service.resume(created["id"])
        self.assertEqual(collecting["state"], "collecting")
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls], ["start_round"]
        )

        failed = False

        def flaky_audit(event):
            nonlocal failed
            if (
                event["type"] == "handler_invocation_claimed"
                and event.get("action") == "collect_round"
                and not failed
            ):
                failed = True
                raise RuntimeError("transient audit sink failure")
            self.fixture.audits.append(event)

        service._audit_callback = flaky_audit
        self.assert_error(
            "audit_callback_failed", lambda: service.resume(created["id"]), status=503
        )
        rolled_back = service.read(created["id"])
        self.assertEqual(rolled_back["state"], "collecting")
        self.assertFalse(rolled_back["recovery"]["beforeStartRetryAllowed"])
        self.assertTrue(rolled_back["recovery"]["receiptRecoveryRequired"])
        self.assertFalse(rolled_back["recovery"]["adapterCallInFlight"])
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls], ["start_round"]
        )

        recovered = service.resume(created["id"])
        self.assertEqual(recovered["stage"], "verify_report")
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls],
            ["start_round", "collect_round"],
        )

    def test_ordinary_handler_interruption_requires_receipt_recovery(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(RuntimeError("adapter disconnected"))
        self.fixture.advance_to_run_round(service, created["id"])
        self.assert_error(
            "handler_interrupted", lambda: service.resume(created["id"]), status=503
        )
        waiting = service.read(created["id"])
        self.assertTrue(waiting["recovery"]["receiptRecoveryRequired"])

        self.fixture.handler_results.append(
            lambda request: self.fixture.started_result(request)
        )
        recovered = service.resume(created["id"])
        self.assertEqual(recovered["state"], "collecting")
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls],
            ["start_round", "recover_round"],
        )
        self.assertTrue(self.fixture.handler_calls[1]["safety"]["neverStart"])

    def test_crash_after_start_boundary_never_replays_start_after_restart(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(CrashAfterStart())
        self.fixture.advance_to_run_round(service, created["id"])
        with self.assertRaises(CrashAfterStart):
            service.resume(created["id"])
        durable = service.read(created["id"])
        self.assertTrue(durable["recovery"]["startBoundaryCommitted"])
        self.assertTrue(durable["recovery"]["receiptRecoveryRequired"])

        restarted = self.fixture.service()
        recovered = restarted.recover_after_restart()
        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0]["state"], "awaiting_visible_terminal")
        self.fixture.handler_results.append(
            lambda request: self.fixture.started_result(request)
        )
        restarted.resume(created["id"])
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls],
            ["start_round", "recover_round"],
        )

    def test_orphan_receipt_is_recovered_after_state_commit_crash(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: self.fixture.started_result(request)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        original_save = service._save_unlocked

        def crash_when_receipt_attached(store):
            session = store["sessions"][0]
            operation = session.get("currentOperation")
            if isinstance(operation, dict) and isinstance(operation.get("receipt"), dict):
                raise CrashAfterStart()
            return original_save(store)

        with mock.patch.object(service, "_save_unlocked", side_effect=crash_when_receipt_attached):
            with self.assertRaises(CrashAfterStart):
                service.resume(created["id"])
        restarted = self.fixture.service()
        state = restarted.recover_after_restart()[0]
        self.assertTrue(state["recovery"]["receiptPresent"])
        self.assertEqual(state["state"], "collecting")

    def test_orphan_completed_result_recovers_to_report_verification(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        original_save = service._save_unlocked

        def crash_after_result_document(store):
            if store["sessions"][0]["roundResults"]:
                raise CrashAfterStart()
            return original_save(store)

        with mock.patch.object(
            service, "_save_unlocked", side_effect=crash_after_result_document
        ):
            with self.assertRaises(CrashAfterStart):
                service.resume(created["id"])

        restarted = self.fixture.service()
        recovered = restarted.recover_after_restart()[0]
        self.assertEqual(recovered["state"], "running")
        self.assertEqual(recovered["stage"], "verify_report")
        self.assertEqual(len(recovered["evidence"]), 1)
        self.assertFalse(recovered["recovery"]["adapterCallInFlight"])

    def test_expired_orphan_completed_result_is_accepted_without_replaying_start(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        original_save = service._save_unlocked

        def crash_after_result_document(store):
            if store["sessions"][0]["roundResults"]:
                raise CrashAfterStart()
            return original_save(store)

        with mock.patch.object(
            service, "_save_unlocked", side_effect=crash_after_result_document
        ):
            with self.assertRaises(CrashAfterStart):
                service.resume(created["id"])

        self.fixture.clock.advance(601)
        restarted = self.fixture.service()
        recovered_rows = restarted.recover_after_restart()
        self.assertEqual(len(recovered_rows), 1)
        recovered = recovered_rows[0]
        self.assertEqual(recovered["id"], created["id"])
        self.assertEqual(recovered["state"], "running")
        self.assertEqual(recovered["stage"], "verify_report")
        self.assertIsNone(recovered["failure"])
        self.assertEqual(len(recovered["evidence"]), 1)
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls], ["start_round"]
        )
        terminal = self.fixture.finish_verified_round(restarted, created["id"])
        self.assertEqual(terminal["state"], "completed")
        replacement = restarted.create(
            self.fixture.request(key="optimization-request-after-orphan-proof")
        )
        self.assertEqual(replacement["state"], "queued")

    def test_in_progress_collection_updates_heartbeat_and_never_starts_again(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.extend(
            [
                lambda request: self.fixture.started_result(request, progress=5),
                lambda request: {
                    "status": "in_progress",
                    "receipt": self.fixture.receipt(request),
                    "progressPercent": 50,
                    "passCount": 2,
                },
                lambda request: self.fixture.completed_result(request),
            ]
        )
        self.fixture.advance_to_run_round(service, created["id"])
        service.resume(created["id"])
        first_heartbeat = service.read(created["id"])["heartbeatAt"]
        self.fixture.clock.advance(30)
        progress = service.resume(created["id"])
        self.assertEqual(progress["progress"]["percent"], 50)
        self.assertEqual(progress["progress"]["passCount"], 2)
        self.assertNotEqual(progress["heartbeatAt"], first_heartbeat)
        service.resume(created["id"])
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls],
            ["start_round", "collect_round", "collect_round"],
        )

    def test_long_handler_does_not_block_read_cancel_or_duplicate_start(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        entered = threading.Event()
        release = threading.Event()

        def blocked_handler(request: dict) -> dict:
            entered.set()
            if not release.wait(timeout=5):
                raise RuntimeError("test handler release timed out")
            return self.fixture.started_result(request, progress=5)

        self.fixture.handler_results.append(blocked_handler)
        self.fixture.advance_to_run_round(service, created["id"])
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            running = pool.submit(service.resume, created["id"])
            self.assertTrue(entered.wait(timeout=2))
            self.fixture.clock.advance(121)
            read_state = pool.submit(service.read, created["id"]).result(timeout=1)
            self.assertIn(read_state["state"], self.module.ACTIVE_STATES)
            self.assertTrue(read_state["recovery"]["adapterCallInFlight"])

            concurrent_resume = pool.submit(service.resume, created["id"]).result(
                timeout=1
            )
            self.assertTrue(
                concurrent_resume["recovery"]["adapterCallInFlight"]
            )
            self.assertEqual(len(self.fixture.handler_calls), 1)

            cancelled = pool.submit(
                service.cancel, created["id"], reason="operator_cancelled"
            ).result(timeout=1)
            self.assertTrue(cancelled["cancelRequested"])
            release.set()
            committed = running.result(timeout=2)

        self.assertFalse(committed["recovery"]["adapterCallInFlight"])
        self.assertTrue(committed["cancelRequested"])
        self.assertEqual(committed["state"], "collecting")
        self.assertEqual(len(self.fixture.handler_calls), 1)

    def test_in_flight_handler_still_obeys_absolute_session_deadline(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        entered = threading.Event()
        release = threading.Event()

        def blocked_handler(request: dict) -> dict:
            entered.set()
            if not release.wait(timeout=5):
                raise RuntimeError("test handler release timed out")
            return self.fixture.completed_result(request)

        self.fixture.handler_results.append(blocked_handler)
        self.fixture.advance_to_run_round(service, created["id"])
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            running = pool.submit(service.resume, created["id"])
            self.assertTrue(entered.wait(timeout=2))
            self.fixture.clock.advance(601)
            quarantined = service.read(created["id"])
            self.assertIn(quarantined["state"], self.module.ACTIVE_STATES)
            self.assertEqual(
                quarantined["failure"]["code"], "session_deadline_exceeded"
            )
            self.assertTrue(
                quarantined["failure"]["executionMayStillBeRunning"]
            )
            self.assertTrue(quarantined["recovery"]["adapterCallInFlight"])
            self.assert_error(
                "optimization_busy",
                lambda: service.create(
                    self.fixture.request(key="optimization-request-quarantined")
                ),
                status=409,
            )
            release.set()
            expired = running.result(timeout=2)

        self.assertEqual(expired["state"], "failed")
        self.assertEqual(expired["failure"]["code"], "session_deadline_exceeded")
        self.assertFalse(expired["failure"]["executionMayStillBeRunning"])
        self.assertFalse(expired["recovery"]["adapterCallInFlight"])
        self.assertEqual(expired["evidence"], [])
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls], ["start_round"]
        )
        replacement = service.create(
            self.fixture.request(key="optimization-request-after-deadline")
        )
        self.assertEqual(replacement["state"], "queued")

    def test_deadline_quarantine_accepts_exact_receipt_recovery_without_replaying_start(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: self.fixture.started_result(request, progress=20)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        started = service.resume(created["id"])
        self.assertEqual(started["state"], "collecting")

        self.fixture.clock.advance(601)
        quarantined = service.read(created["id"])
        self.assertTrue(quarantined["failure"]["executionMayStillBeRunning"])
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request)
        )
        recovered = service.resume(created["id"])

        self.assertEqual(recovered["state"], "running")
        self.assertEqual(recovered["stage"], "verify_report")
        self.assertIsNone(recovered["failure"])
        self.assertEqual(len(recovered["evidence"]), 1)
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls],
            ["start_round", "collect_round"],
        )
        self.assertFalse(self.fixture.handler_calls[1]["safety"]["startAllowed"])
        self.assertTrue(self.fixture.handler_calls[1]["safety"]["neverStart"])
        terminal = self.fixture.finish_verified_round(service, created["id"])
        self.assertEqual(terminal["state"], "completed")
        replacement = service.create(
            self.fixture.request(key="optimization-request-after-recovery-proof")
        )
        self.assertEqual(replacement["state"], "queued")

    def test_restart_keeps_deadline_orphan_quarantined_until_terminal_proof(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(CrashAfterStart())
        self.fixture.advance_to_run_round(service, created["id"])
        with self.assertRaises(CrashAfterStart):
            service.resume(created["id"])

        self.fixture.clock.advance(601)
        restarted = self.fixture.service()
        active = restarted.recover_after_restart()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["id"], created["id"])
        self.assertTrue(active[0]["failure"]["executionMayStillBeRunning"])
        self.assert_error(
            "optimization_busy",
            lambda: restarted.create(
                self.fixture.request(key="optimization-request-restart-busy")
            ),
            status=409,
        )

        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request)
        )
        recovered = restarted.resume(created["id"])
        self.assertEqual(recovered["state"], "running")
        self.assertEqual(recovered["stage"], "verify_report")
        self.assertIsNone(recovered["failure"])
        self.assertEqual(len(recovered["evidence"]), 1)
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls],
            ["start_round", "recover_round"],
        )
        self.assertFalse(self.fixture.handler_calls[1]["safety"]["startAllowed"])
        self.assertTrue(self.fixture.handler_calls[1]["safety"]["neverStart"])
        terminal = self.fixture.finish_verified_round(restarted, created["id"])
        self.assertEqual(terminal["state"], "completed")

    def test_completed_requires_nonempty_passes_and_rows(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(
                request, pass_count=0, returned_count=0, rows=[]
            )
        )
        self.fixture.advance_to_run_round(service, created["id"])
        self.assert_error(
            "optimization_zero_pass", lambda: service.resume(created["id"]), status=502
        )
        quarantined = service.read(created["id"])
        self.assertIn(quarantined["state"], self.module.ACTIVE_STATES)
        self.assertTrue(quarantined["failure"]["executionMayStillBeRunning"])
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request)
        )
        recovered = service.resume(created["id"])
        self.assertEqual(recovered["state"], "running")
        self.assertEqual(recovered["stage"], "verify_report")
        self.assertIsNone(recovered["failure"])
        self.assertEqual(len(recovered["evidence"]), 1)
        terminal = self.fixture.finish_verified_round(service, created["id"])
        self.assertEqual(terminal["state"], "completed")

        fresh_root = self.fixture.root / "second-store"
        second = self.module.EaFactoryOptimizationService(
            fresh_root,
            target_resolver=self.fixture.resolver,
            capability_provider=self.fixture.capability,
            optimization_handler=self.fixture.handler,
            clock=self.fixture.clock,
            heartbeat_timeout_seconds=120,
            session_deadline_seconds=600,
        )
        other = second.create(self.fixture.request(key="optimization-request-empty"))
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(
                request, pass_count=1, returned_count=1, rows=[]
            )
        )
        self.fixture.advance_to_run_round(second, other["id"])
        self.assert_error(
            "optimization_result_invalid", lambda: second.resume(other["id"]), status=502
        )

        third_root = self.fixture.root / "third-store"
        third = self.module.EaFactoryOptimizationService(
            third_root,
            target_resolver=self.fixture.resolver,
            capability_provider=self.fixture.capability,
            optimization_handler=self.fixture.handler,
            clock=self.fixture.clock,
            heartbeat_timeout_seconds=120,
            session_deadline_seconds=600,
        )
        single = third.create(
            self.fixture.request(key="optimization-request-single-pass")
        )
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(
                request,
                pass_count=1,
                returned_count=1,
                rows=[{"pass": 1, "profit": 1.0}],
            )
        )
        self.fixture.advance_to_run_round(third, single["id"])
        self.assert_error(
            "optimization_insufficient_passes",
            lambda: third.resume(single["id"]),
            status=502,
        )

    def test_completed_preserves_empty_native_metric_without_rejecting_evidence(self) -> None:
        """MT5 uses an empty cell for undefined metrics such as zero-trade PF."""

        service = self.fixture.service()
        created = service.create(
            self.fixture.request(key="optimization-native-empty-metric")
        )
        rows = [
            {
                "passNumber": index,
                "profit": 0.0,
                "equityDrawdownPercent": 0.0,
                "trades": 0,
                "profitFactor": "",
                "sharpeRatio": 0,
                "RiskPercent": risk,
                "EntryMode": mode,
            }
            for index, (risk, mode) in enumerate(
                (
                    (0.5, "safe"),
                    (0.5, "balanced"),
                    (1.0, "safe"),
                    (1.0, "balanced"),
                )
            )
        ]
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request, rows=rows)
        )
        self.fixture.advance_to_run_round(service, created["id"])

        self.assertEqual(service.resume(created["id"])["stage"], "verify_report")
        self.assertEqual(service.resume(created["id"])["stage"], "analyze")
        self.assertEqual(service.resume(created["id"])["stage"], "complete")
        completed = service.resume(created["id"])

        self.assertEqual(completed["state"], "completed")
        self.assertEqual(
            [row["profitFactor"] for row in completed["evidence"][0]["resultRows"]],
            ["", "", "", ""],
        )
        analysis = completed["evidence"][0]["analysis"]
        self.assertEqual(analysis["status"], "unavailable")
        self.assertEqual(analysis["reasonCode"], "backtest_zero_trades")
        self.assertEqual(analysis["profitablePassCount"], 0)
        self.assertIsNone(analysis["eligiblePassCount"])
        self.assertEqual(
            analysis["candidateGroups"],
            {"maxProfit": [], "lowestDrawdown": [], "mostStable": []},
        )
        self.assertEqual(analysis["nextParameterPlan"], [])
        self.assertFalse(analysis["nextParameterPlanAvailable"])

    def test_analysis_excludes_zero_trade_rows_from_candidates_and_next_plan(self) -> None:
        service = self.fixture.service()
        created = service.create(
            self.fixture.request(key="optimization-mixed-trade-counts")
        )
        rows = [
            {
                "pass": 1,
                "profit": 500.0,
                "drawdownPercent": 1.0,
                "trades": 0,
                "sharpeRatio": 5.0,
                "RiskPercent": 0.5,
                "EntryMode": "safe",
            },
            {
                "pass": 2,
                "profit": 50.0,
                "drawdownPercent": 6.0,
                "trades": 10,
                "sharpeRatio": 1.2,
                "RiskPercent": 0.5,
                "EntryMode": "balanced",
            },
            {
                "pass": 3,
                "profit": 700.0,
                "drawdownPercent": 0.5,
                "trades": 0,
                "sharpeRatio": 7.0,
                "RiskPercent": 1.0,
                "EntryMode": "safe",
            },
            {
                "pass": 4,
                "profit": 40.0,
                "drawdownPercent": 4.0,
                "trades": 15,
                "sharpeRatio": 1.0,
                "RiskPercent": 1.0,
                "EntryMode": "balanced",
            },
        ]
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request, rows=rows)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        service.resume(created["id"])
        service.resume(created["id"])
        analyzed = service.resume(created["id"])["evidence"][0]["analysis"]

        self.assertEqual(analyzed["status"], "available")
        self.assertEqual(analyzed["eligiblePassCount"], 2)
        for group in ("maxProfit", "lowestDrawdown", "mostStable"):
            self.assertEqual(
                {candidate["pass"] for candidate in analyzed["candidateGroups"][group]},
                {2, 4},
            )
        self.assertEqual(analyzed["nextParameterPlan"][0]["start"], 0.5)
        self.assertEqual(analyzed["nextParameterPlan"][0]["stop"], 1.0)
        self.assertEqual(analyzed["nextParameterPlan"][1]["values"], ["balanced"])

    def test_analysis_requires_trade_metric_even_without_minimum_trade_threshold(self) -> None:
        service = self.fixture.service()
        created = service.create(
            self.fixture.request(key="optimization-missing-trades-no-threshold")
        )
        rows = [
            {
                "pass": index + 1,
                "profit": 100.0 + index,
                "drawdownPercent": 5.0,
                "sharpeRatio": 1.0,
                "RiskPercent": risk,
                "EntryMode": mode,
                **({"trades": 10} if index else {}),
            }
            for index, (risk, mode) in enumerate(
                (
                    (0.5, "safe"),
                    (0.5, "balanced"),
                    (1.0, "safe"),
                    (1.0, "balanced"),
                )
            )
        ]
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request, rows=rows)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        service.resume(created["id"])
        service.resume(created["id"])
        analyzed = service.resume(created["id"])["evidence"][0]["analysis"]

        self.assertEqual(analyzed["status"], "unavailable")
        self.assertEqual(analyzed["reasonCode"], "trades_metric_missing_or_invalid")
        self.assertEqual(analyzed["candidateGroups"]["maxProfit"], [])
        self.assertFalse(analyzed["nextParameterPlanAvailable"])

    def test_analysis_policy_version_replays_legacy_zero_trade_document(self) -> None:
        service = self.fixture.service()
        created = service.create(
            self.fixture.request(key="optimization-legacy-analysis-policy")
        )
        rows = [
            {
                "pass": index + 1,
                "profit": 0.0,
                "drawdownPercent": 0.0,
                "trades": 0,
                "sharpeRatio": 0.0,
                "RiskPercent": risk,
                "EntryMode": mode,
            }
            for index, (risk, mode) in enumerate(
                (
                    (0.5, "safe"),
                    (0.5, "balanced"),
                    (1.0, "safe"),
                    (1.0, "balanced"),
                )
            )
        ]
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request, rows=rows)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        service.resume(created["id"])
        service.resume(created["id"])

        with service._locked():
            store = service._load_store_unlocked()
            session = next(item for item in store["sessions"] if item["id"] == created["id"])
            result = session["roundResults"][0]
            verified_result = service._verified_result_document(session, result)
            legacy = service._build_round_analysis(
                session,
                result,
                verified_result,
                analysis_policy_version=1,
            )
            self.assertNotIn("analysisPolicyVersion", legacy)
            self.assertEqual(legacy["status"], "available")
            legacy_ref = "analysis_legacy_round_01"
            legacy_digest = service._write_immutable_document(
                session["workspaceRef"],
                legacy_ref,
                legacy,
            )
            legacy_result = dict(result)
            legacy_result.update({
                "analysisRef": legacy_ref,
                "analysisSha256": legacy_digest,
                "analyzed": True,
            })
            replayed = service._verified_analysis_document(
                session,
                legacy_result,
                verified_result,
            )

        self.assertEqual(replayed, legacy)
        current = service._build_round_analysis(session, result, verified_result)
        self.assertEqual(
            current["analysisPolicyVersion"],
            self.module.ANALYSIS_POLICY_VERSION,
        )
        self.assertEqual(current["status"], "unavailable")
        self.assertEqual(current["reasonCode"], "backtest_zero_trades")

    def test_valid_truncation_is_preserved_and_false_truncation_is_rejected(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(
                request,
                pass_count=4,
                returned_count=2,
                truncated=True,
                rows=[{"pass": 1, "profit": 10.5}, {"pass": 2, "profit": 9.0}],
            )
        )
        self.fixture.advance_to_run_round(service, created["id"])
        accepted = service.resume(created["id"])
        self.assertTrue(accepted["progress"]["rowsTruncated"])
        self.assertEqual(accepted["evidence"][0]["returnedPassCount"], 2)

        root = self.fixture.root / "invalid-truncation"
        invalid = self.module.EaFactoryOptimizationService(
            root,
            target_resolver=self.fixture.resolver,
            capability_provider=self.fixture.capability,
            optimization_handler=self.fixture.handler,
            clock=self.fixture.clock,
            heartbeat_timeout_seconds=120,
            session_deadline_seconds=600,
        )
        session = invalid.create(self.fixture.request(key="optimization-request-truncate"))
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(
                request,
                pass_count=4,
                returned_count=2,
                truncated=False,
                rows=[{"pass": 1}, {"pass": 2}],
            )
        )
        self.fixture.advance_to_run_round(invalid, session["id"])
        self.assert_error(
            "optimization_truncation_invalid",
            lambda: invalid.resume(session["id"]),
            status=502,
        )

    def test_public_result_rows_are_hash_verified_and_independently_bounded(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        rows = [
            {"pass": index + 1, "profit": float(10 - index), "mode": "safe"}
            for index in range(4)
        ]
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request, rows=rows)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        with mock.patch.object(self.module, "MAX_PUBLIC_RESULT_ROWS", 2):
            accepted = service.resume(created["id"])
            published = accepted["evidence"][0]
            self.assertEqual(published["resultRows"], rows[:2])
            self.assertTrue(published["publicResultRowsTruncated"])
            self.assertEqual(
                published["resultRowsSha256"],
                hashlib.sha256(
                    json.dumps(
                        rows,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                ).hexdigest(),
            )
            self.assertRegex(published["evidenceDocumentSha256"], r"^[0-9a-f]{64}$")

    def test_store_and_immutable_result_tamper_are_detected(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        store_path = self.fixture.root / self.module.STORE_FILENAME
        raw = json.loads(store_path.read_text(encoding="utf-8"))
        raw["sessions"][0]["stage"] = "complete"
        store_path.write_text(json.dumps(raw), encoding="utf-8")
        self.assert_error("store_tampered", lambda: service.read(created["id"]), status=500)

        separate = OptimizationFixture(self, self.module)
        self.addCleanup(separate.cleanup)
        other_service = separate.service()
        other = other_service.create(separate.request())
        separate.handler_results.append(lambda request: separate.completed_result(request))
        separate.advance_to_run_round(other_service, other["id"])
        other_service.resume(other["id"])
        durable = json.loads(
            (separate.root / self.module.STORE_FILENAME).read_text(encoding="utf-8")
        )
        session = durable["sessions"][0]
        result = session["roundResults"][0]
        result_path = (
            separate.root
            / self.module.WORKSPACES_DIRECTORY
            / session["workspaceRef"]
            / f"{result['documentRef']}.json"
        )
        with contextlib_suppress_permission_error():
            os.chmod(result_path, stat.S_IWRITE | stat.S_IREAD)
        result_path.write_text("{}\n", encoding="utf-8")
        self.assert_error(
            "evidence_tampered", lambda: other_service.read(other["id"]), status=500
        )

        strict = OptimizationFixture(self, self.module)
        self.addCleanup(strict.cleanup)
        strict_service = strict.service()
        strict_created = strict_service.create(strict.request())
        strict_store_path = strict.root / self.module.STORE_FILENAME
        strict_raw = json.loads(strict_store_path.read_text(encoding="utf-8"))
        strict_raw["sessions"][0]["progress"]["unexpected"] = True
        strict_raw["integritySha256"] = strict_service._store_integrity(strict_raw)
        strict_store_path.write_text(
            json.dumps(strict_raw, sort_keys=True) + "\n", encoding="utf-8"
        )
        self.assert_error(
            "store_corrupt", lambda: strict_service.read(strict_created["id"]), status=500
        )

    def test_report_hash_is_immutable_and_handler_path_fields_are_rejected(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            {
                "status": "unknown",
                "reasonCode": "waiting",
                "reportPath": r"C:\\unsafe\\report.htm",
            }
        )
        self.fixture.advance_to_run_round(service, created["id"])
        self.assert_error("unsafe_field", lambda: service.resume(created["id"]), status=422)

    def test_malformed_handler_result_quarantines_until_terminal_proof(self) -> None:
        service = self.fixture.service()
        created = service.create(self.fixture.request())
        self.fixture.handler_results.append(
            {"status": "unknown", "unexpected": "field"}
        )
        self.fixture.advance_to_run_round(service, created["id"])
        self.assert_error("invalid_request", lambda: service.resume(created["id"]), status=422)
        failed = service.read(created["id"])
        self.assertIn(failed["state"], self.module.ACTIVE_STATES)
        self.assertTrue(failed["failure"]["executionMayStillBeRunning"])
        self.assertFalse(failed["recovery"]["adapterCallInFlight"])
        self.assert_error(
            "optimization_busy",
            lambda: service.create(
                self.fixture.request(key="optimization-request-malformed-busy")
            ),
            status=409,
        )
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request)
        )
        recovered = service.resume(created["id"])
        self.assertEqual(recovered["state"], "running")
        self.assertEqual(recovered["stage"], "verify_report")
        self.assertIsNone(recovered["failure"])
        self.assertEqual(len(recovered["evidence"]), 1)
        terminal = self.fixture.finish_verified_round(service, created["id"])
        self.assertEqual(terminal["state"], "completed")
        replacement = service.create(
            self.fixture.request(key="optimization-request-after-malformed")
        )
        self.assertEqual(replacement["state"], "queued")

    def test_legacy_discard_reopens_exact_session_and_preserves_recovery_provenance(
        self,
    ) -> None:
        service = self.fixture.service()
        created = service.create(
            self.fixture.request(key="optimization-request-legacy-discard")
        )
        discarded = self.fixture.legacy_completed_late_discard(
            service,
            created["id"],
        )
        self.assertEqual(
            discarded["failure"]["code"],
            "session_deadline_exceeded",
        )
        handler_count = len(self.fixture.handler_calls)
        generic_replay = service.resume(created["id"])
        self.assertEqual(generic_replay["state"], "failed")
        self.assertEqual(len(self.fixture.handler_calls), handler_count)

        prepared = service.prepare_late_completed_recovery(created["id"])
        self.assertEqual(prepared["state"], "collecting")
        self.assertTrue(
            prepared["recovery"]["lateCompletedResultRecoveryPending"]
        )
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request)
        )
        accepted = service.resume(created["id"])
        self.assertEqual(accepted["state"], "running")
        self.assertEqual(accepted["stage"], "verify_report")
        self.assertEqual(len(accepted["evidence"]), 1)
        completed = self.fixture.finish_verified_round(service, created["id"])
        self.assertTrue(completed["recovery"]["lateCompletedResultRecovered"])
        self.assertEqual(
            completed["recovery"]["lateCompletedResultRecoveryProof"],
            "completed_late_discarded",
        )
        self.assertEqual(
            completed["recovery"]["lateCompletedResultRecoveryFailureCode"],
            "session_deadline_exceeded",
        )
        actions = [call["action"] for call in self.fixture.handler_calls]
        self.assertEqual(actions.count("start_round"), 1)
        self.assertEqual(actions, ["start_round", "collect_round", "collect_round"])
        self.assertTrue(all(
            call["safety"]["neverStart"]
            for call in self.fixture.handler_calls[1:]
        ))
        with service._locked():
            raw = service._load_store_unlocked()
        stored = next(row for row in raw["sessions"] if row["id"] == created["id"])
        self.assertEqual(stored["attemptsByRound"], [1])
        event_types = [event["type"] for event in stored["eventLog"]]
        self.assertIn("late_completed_result_revalidation_started", event_types)
        self.assertIn("execution_quarantine_completed_accepted", event_types)
        self.assertIn("session_completed", event_types)

    def test_late_discard_prepare_is_idempotent_but_rejects_other_active_session(
        self,
    ) -> None:
        service = self.fixture.service()
        created = service.create(
            self.fixture.request(key="optimization-request-legacy-concurrent")
        )
        self.fixture.legacy_completed_late_discard(service, created["id"])

        barrier = threading.Barrier(2)

        def prepare_same_session():
            barrier.wait(timeout=5)
            return service.prepare_late_completed_recovery(created["id"])

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            prepared_rows = list(pool.map(lambda _index: prepare_same_session(), range(2)))
        self.assertEqual({row["id"] for row in prepared_rows}, {created["id"]})
        self.assertTrue(all(
            row["recovery"]["lateCompletedResultRecoveryPending"]
            for row in prepared_rows
        ))
        with service._locked():
            store = service._load_store_unlocked()
        target = next(row for row in store["sessions"] if row["id"] == created["id"])
        self.assertEqual(
            sum(
                event.get("type") == "late_completed_result_revalidation_started"
                for event in target["eventLog"]
            ),
            1,
        )
        self.assertEqual(target["attemptsByRound"], [1])

        # Recreate an independently recoverable terminal row, then prove a
        # different active session owns the process-wide slot.
        isolated = OptimizationFixture(self, self.module)
        self.addCleanup(isolated.cleanup)
        isolated_service = isolated.service()
        target_created = isolated_service.create(
            isolated.request(key="optimization-request-legacy-busy-target")
        )
        isolated.legacy_completed_late_discard(
            isolated_service,
            target_created["id"],
        )
        other = isolated_service.create(
            isolated.request(key="optimization-request-other-active")
        )
        self.assertEqual(other["state"], "queued")
        error = self.assert_error(
            "optimization_busy",
            lambda: isolated_service.prepare_late_completed_recovery(
                target_created["id"]
            ),
            status=409,
        )
        self.assertIn("active slot", str(error))
        unchanged = isolated_service.read(target_created["id"])
        self.assertEqual(unchanged["state"], "failed")
        self.assertTrue(
            unchanged["recovery"]["lateCompletedResultRecoveryAvailable"]
        )

    def test_post_evidence_finalization_ignores_old_deadline_but_has_heartbeat_lease(
        self,
    ) -> None:
        service = self.fixture.service()
        created = service.create(
            self.fixture.request(key="optimization-request-finalization-lease")
        )
        self.fixture.handler_results.append(
            lambda request: self.fixture.started_result(request, progress=20)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        service.resume(created["id"])
        self.fixture.clock.advance(601)
        service.read(created["id"])
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request)
        )
        accepted = service.resume(created["id"])
        self.assertEqual(accepted["stage"], "verify_report")
        self.assertEqual(service.read(created["id"])["state"], "running")

        self.fixture.clock.advance(121)
        expired = service.read(created["id"])
        self.assertEqual(expired["state"], "failed")
        self.assertEqual(expired["failure"]["code"], "session_heartbeat_timeout")
        self.assertFalse(expired["failure"]["executionMayStillBeRunning"])
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls],
            ["start_round", "collect_round"],
        )

    def test_cancel_wins_over_exact_late_completed_recovery(self) -> None:
        service = self.fixture.service()
        created = service.create(
            self.fixture.request(key="optimization-request-cancel-late-result")
        )
        self.fixture.handler_results.append(
            lambda request: self.fixture.started_result(request, progress=20)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        service.resume(created["id"])
        self.fixture.clock.advance(601)
        service.read(created["id"])
        pending_cancel = service.cancel(
            created["id"],
            reason="operator_cancelled",
        )
        self.assertTrue(pending_cancel["cancelRequested"])
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request)
        )
        cancelled = service.resume(created["id"])
        self.assertEqual(cancelled["state"], "cancelled")
        self.assertEqual(cancelled["evidence"], [])
        self.assertEqual(
            [call["action"] for call in self.fixture.handler_calls],
            ["start_round", "collect_round"],
        )

    def test_multiple_rounds_require_evidence_for_each_round(self) -> None:
        rounds = [
            {
                "ranges": [
                    {"name": "Mode", "kind": "categorical", "values": ["a", "b"]}
                ]
            },
            {
                "ranges": [
                    {"name": "Period", "kind": "numeric", "start": 10, "step": 10, "stop": 20}
                ]
            },
        ]
        service = self.fixture.service()
        created = service.create(self.fixture.request(rounds=rounds))
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request, pass_count=2)
        )
        self.fixture.advance_to_run_round(service, created["id"])
        service.resume(created["id"])
        service.resume(created["id"])
        next_round = service.resume(created["id"])
        self.assertEqual(next_round["round"]["number"], 2)
        self.assertEqual(next_round["stage"], "prepare_ranges")
        self.fixture.handler_results.append(
            lambda request: self.fixture.completed_result(request, pass_count=2)
        )
        self.assertEqual(service.resume(created["id"])["stage"], "run_round")
        self.assertEqual(service.resume(created["id"])["stage"], "verify_report")
        self.assertEqual(service.resume(created["id"])["stage"], "analyze")
        self.assertEqual(service.resume(created["id"])["stage"], "complete")
        completed = service.resume(created["id"])
        self.assertEqual(completed["state"], "completed")
        self.assertEqual(len(completed["evidence"]), 2)


class contextlib_suppress_permission_error:
    def __enter__(self):
        return self

    def __exit__(self, exception_type, _exception, _traceback):
        return exception_type is PermissionError


if __name__ == "__main__":
    unittest.main()
