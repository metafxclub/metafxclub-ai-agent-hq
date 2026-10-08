from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    ROOT / "artifacts" / "mt5-trade-gateway-v1.03-visible-compile-readiness"
)
MANIFEST_PATH = ARTIFACT_DIR / "MANIFEST.json"
CHECKSUMS_PATH = ARTIFACT_DIR / "SHA256SUMS.txt"
SOURCE_PATH = (
    ROOT / "integrations" / "mt5-trade-gateway" / "MetafxHQTradeGateway.mq5"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


class Mt5VisibleCompileArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_source_and_source_only_distribution_policy(self) -> None:
        self.assertEqual(
            self.manifest["sourceFile"],
            "integrations/mt5-trade-gateway/MetafxHQTradeGateway.mq5",
        )
        self.assertEqual(self.manifest["sourceSha256"], sha256(SOURCE_PATH))
        self.assertEqual(self.manifest["releasePolicy"], "source_only")
        self.assertFalse(self.manifest["compiledBinaryIncluded"])
        self.assertFalse(self.manifest["compiledBinaryEligibleForDistribution"])

    def test_visible_metaeditor64_compile_evidence_matches_exact_source(self) -> None:
        evidence = self.manifest["compileEvidence"]
        self.assertEqual(evidence["status"], "passed")
        self.assertEqual(evidence["mode"], "visible_metaeditor64_exact_source")
        self.assertEqual(evidence["errors"], 0)
        self.assertEqual(evidence["warnings"], 0)
        self.assertEqual(
            evidence["compiledSourceSha256"],
            self.manifest["sourceSha256"],
        )
        self.assertIs(evidence["currentSourceMatchesCompiledSource"], True)

    def test_compile_proof_hash_matches_manifest_and_file(self) -> None:
        evidence = self.manifest["compileEvidence"]
        proof_name = evidence["screenshot"]
        self.assertEqual(proof_name, "COMPILE_PROOF.png")
        proof_path = ARTIFACT_DIR / proof_name
        self.assertTrue(proof_path.is_file())
        self.assertEqual(evidence["screenshotSha256"], sha256(proof_path))

    def test_checksum_set_is_complete_and_every_entry_matches(self) -> None:
        entries: dict[str, str] = {}
        for line in CHECKSUMS_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            match = re.fullmatch(r"([0-9A-Fa-f]{64})  ([^\\/]+)", line)
            self.assertIsNotNone(match, f"Malformed checksum line: {line!r}")
            expected_hash, filename = match.groups()
            self.assertNotIn(filename, entries, f"Duplicate checksum: {filename}")
            entries[filename] = expected_hash.upper()

        expected_files = {
            path.name
            for path in ARTIFACT_DIR.iterdir()
            if path.is_file() and path.name != CHECKSUMS_PATH.name
        }
        self.assertEqual(set(entries), expected_files)
        for filename, expected_hash in entries.items():
            with self.subTest(filename=filename):
                self.assertEqual(sha256(ARTIFACT_DIR / filename), expected_hash)

    def test_no_compiled_mt5_binary_is_distributed(self) -> None:
        integration_dir = ROOT / "integrations" / "mt5-trade-gateway"
        for directory in (ARTIFACT_DIR, integration_dir):
            ex5_files = [
                path
                for path in directory.rglob("*")
                if path.is_file() and path.suffix.casefold() == ".ex5"
            ]
            self.assertEqual(ex5_files, [], f"EX5 must not be distributed in {directory}")

    def test_compile_proof_does_not_claim_demo_or_live_execution(self) -> None:
        safety = self.manifest["safety"]
        self.assertIs(safety["demoExecutionValidated"], False)
        self.assertIs(safety["liveExecutionValidated"], False)
        self.assertIs(safety["eaAttachedToChart"], False)
        self.assertIs(safety["algoTradingChanged"], False)
        self.assertIs(safety["orderOrTradeCommandSent"], False)


if __name__ == "__main__":
    unittest.main()
