from __future__ import annotations

import copy
import importlib.util
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_ea_optimization_evidence_bridge",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load bridge module from {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EaOptimizationLabBackendEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    @contextmanager
    def isolated_execution_store(self):
        with tempfile.TemporaryDirectory() as directory:
            original_audit = self.bridge.AUDIT_PATH
            original_missions = self.bridge.MISSIONS_PATH
            try:
                self.bridge.AUDIT_PATH = Path(directory) / "audit.jsonl"
                self.bridge.MISSIONS_PATH = Path(directory) / "missions.json"
                yield
            finally:
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.MISSIONS_PATH = original_missions

    @staticmethod
    def evidence() -> dict:
        return {
            "sourceKind": "mt5_visible_run",
            "toolId": "run_optimization",
            "runId": "run-opt-001",
            "roundId": "round-001",
            "platform": "mt5",
            "terminalId": "terminal-mt5-a",
            "terminalCandidateId": "candidate-mt5-a",
            "backendVerificationId": "verification-opt-001",
            "visibleTester": {
                "verified": True,
                "settingsScreenshotAttachmentId": "attachment-settings-001",
                "resultsScreenshotAttachmentId": "attachment-results-001",
                "testerLogArtifactId": "artifact-tester-log-001",
            },
            "resultReport": {
                "artifactId": "artifact-result-report-001",
                "sha256": "d" * 64,
                "byteSize": 4096,
                "mediaType": "text/html",
            },
            "artifactManifest": {
                "artifactId": "artifact-manifest-001",
                "sha256": "e" * 64,
                "items": [
                    {
                        "artifactId": "artifact-result-report-001",
                        "sha256": "d" * 64,
                    }
                ],
            },
            # Caller-supplied booleans are intentionally not authoritative.
            "mtExecutionVerified": True,
            "optimizationProofVerified": True,
        }

    @classmethod
    def audit_event(cls) -> dict:
        source = cls.evidence()
        return {
            "type": "metatrader.execution_verified",
            "verificationId": source["backendVerificationId"],
            "missionId": "mission-opt-001",
            "toolId": source["toolId"],
            "runId": source["runId"],
            "roundId": source["roundId"],
            "platform": source["platform"],
            "terminalId": source["terminalId"],
            "terminalCandidateId": source["terminalCandidateId"],
            "status": "completed",
            "visibleApplicationProof": True,
            "liveTrading": False,
            "testShutdownTerminal": False,
            "mtExecutionVerified": True,
            "optimizationProofVerified": True,
            "compileArtifactSha256": "a" * 64,
            "visualBacktestImageSha256": "b" * 64,
            "optimizationArtifactSha256": "c" * 64,
            "visibleTester": copy.deepcopy(source["visibleTester"]),
            "resultReport": copy.deepcopy(source["resultReport"]),
            "artifactManifest": copy.deepcopy(source["artifactManifest"]),
        }

    def seed_verified_audit(self, event: dict | None = None) -> None:
        self.bridge.write_json(
            self.bridge.MISSIONS_PATH,
            {
                "missions": [
                    {
                        "id": "mission-opt-001",
                        "status": "completed",
                        "toolId": "run_optimization",
                    }
                ]
            },
        )
        self.bridge.append_audit(event or self.audit_event())

    def test_v2_evidence_is_analysis_only_without_backend_audit(self) -> None:
        result = self.bridge.report_execution_evidence_read_model(
            self.evidence(),
            "ea_experiment_report",
            "mission-opt-001",
        )

        self.assertFalse(result["mtExecutionVerified"])
        self.assertFalse(result["optimizationProofVerified"])
        self.assertEqual(result["sourceKind"], "analysis_only")
        self.assertIsNone(result["runId"])
        self.assertIsNone(result["roundId"])
        self.assertIsNone(result["terminalId"])
        self.assertFalse(result["visibleTester"]["verified"])
        self.assertIsNone(result["resultReport"]["sha256"])
        self.assertIsNone(result["artifactManifest"]["sha256"])

    def test_matching_v2_backend_audit_projects_only_verified_fields(self) -> None:
        with self.isolated_execution_store():
            self.seed_verified_audit()
            result = self.bridge.report_execution_evidence_read_model(
                self.evidence(),
                "ea_experiment_report",
                "mission-opt-001",
            )

            self.assertTrue(result["mtExecutionVerified"])
            self.assertTrue(result["optimizationProofVerified"])
            self.assertTrue(result["visualBacktestProofVerified"])
            self.assertEqual(result["sourceKind"], "mt5_visible_run")
            self.assertEqual(result["runId"], "run-opt-001")
            self.assertEqual(result["roundId"], "round-001")
            self.assertEqual(result["terminalId"], "terminal-mt5-a")
            self.assertTrue(result["visibleTester"]["verified"])
            self.assertEqual(result["resultReport"]["sha256"], "d" * 64)
            self.assertEqual(result["artifactManifest"]["sha256"], "e" * 64)

            # Stored reports are normalized again by the public read model.
            # The backend-derived projection must remain verifiable on that pass.
            second_projection = self.bridge.report_execution_evidence_read_model(
                result,
                "ea_experiment_report",
                "mission-opt-001",
            )
            self.assertTrue(second_projection["mtExecutionVerified"])
            self.assertEqual(second_projection["runId"], "run-opt-001")

    def test_v2_identity_hash_and_visible_tester_mismatches_fail_closed(self) -> None:
        mutations = (
            lambda source: source.__setitem__("runId", "run-forged"),
            lambda source: source.__setitem__("roundId", "round-forged"),
            lambda source: source.__setitem__("terminalId", "terminal-forged"),
            lambda source: source["resultReport"].__setitem__("sha256", "f" * 64),
            lambda source: source["artifactManifest"].__setitem__("sha256", "f" * 64),
            lambda source: source["visibleTester"].__setitem__("verified", False),
        )
        with self.isolated_execution_store():
            self.seed_verified_audit()
            for mutate in mutations:
                source = self.evidence()
                mutate(source)
                with self.subTest(source=source):
                    result = self.bridge.report_execution_evidence_read_model(
                        source,
                        "ea_experiment_report",
                        "mission-opt-001",
                    )
                    self.assertFalse(result["mtExecutionVerified"])
                    self.assertFalse(result["optimizationProofVerified"])

    def test_v2_rejects_terminal_shutdown_or_incomplete_proof(self) -> None:
        event_mutations = (
            lambda event: event.__setitem__("testShutdownTerminal", True),
            lambda event: event.__setitem__("mtExecutionVerified", False),
            lambda event: event.__setitem__("optimizationProofVerified", False),
            lambda event: event["visibleTester"].__setitem__("verified", False),
            lambda event: event["resultReport"].__setitem__("sha256", "not-a-digest"),
            lambda event: event["artifactManifest"].__setitem__("artifactId", None),
        )
        for mutate in event_mutations:
            with self.isolated_execution_store():
                event = self.audit_event()
                mutate(event)
                self.seed_verified_audit(event)
                result = self.bridge.report_execution_evidence_read_model(
                    self.evidence(),
                    "ea_experiment_report",
                    "mission-opt-001",
                )
                self.assertFalse(result["mtExecutionVerified"])
                self.assertFalse(result["optimizationProofVerified"])


if __name__ == "__main__":
    unittest.main()
