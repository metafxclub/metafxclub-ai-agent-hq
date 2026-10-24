"""Portable integrity tests for distributed MT4 source, binary and native proof."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/mt4-ai-council-ea-v2.18-enum-fail-closed-readiness"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class Mt4CompileProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ART / "MANIFEST.json").read_text(encoding="utf-8"))

    def test_all_distributed_current_sources_match_compiled_source_and_version(self):
        source = ART / self.manifest["sourceFile"]
        self.assertEqual(source.read_bytes(), (ROOT / "integrations/mt4-trade-gateway/MetafxHQTradeGateway.mq4").read_bytes())
        self.assertEqual(sha(source), self.manifest["sourceSha256"])
        self.assertEqual(source.stat().st_size, self.manifest["sourceBytes"])
        text = source.read_text(encoding="utf-8")
        self.assertIn('#property version   "2.20"', text)
        self.assertIn('EA_VERSION = "2.20"', text)
        self.assertEqual(self.manifest["packageVersion"], "2.20")
        self.assertEqual(self.manifest["schemaVersion"], "metafx-hq-mt4-ea-artifact-v2")

    def test_binary_and_compile_log_are_bound_to_exact_source(self):
        binary = ART / self.manifest["binaryFile"]
        self.assertEqual(sha(binary), self.manifest["binarySha256"])
        self.assertEqual(binary.stat().st_size, self.manifest["binaryBytes"])
        proof = self.manifest["compileEvidence"]
        self.assertEqual(proof["compiledSourceSha256"], self.manifest["sourceSha256"])
        self.assertIs(proof["currentSourceMatchesCompiledSource"], True)
        self.assertEqual(sha(ART / proof["log"]), proof["logSha256"])
        log = (ART / proof["log"]).read_text(encoding="utf-8")
        self.assertIn("Result: 0 errors, 0 warnings, 128 msec elapsed", log)
        self.assertEqual((proof["errors"], proof["warnings"], proof["elapsedMs"]), (0, 0, 128))
        self.assertEqual(proof["compilerSignatureStatus"], "Valid")
        self.assertEqual(proof["mode"], "isolated_metaeditor_cli_exact_source")
        self.assertEqual(proof["processExitCode"], 1)

    def test_every_public_distribution_file_is_hashed(self):
        expected = {"MetafxHQTradeGateway.mq4", "MetafxHQTradeGateway.ex4", "README_TH.md", "AUDIT_TH.md", "BUILD_LOG.txt", "COMPILE_LOG.log", "MANIFEST.json"}
        entries = {}
        for line in (ART / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
            checksum, name = line.split("  ", 1)
            self.assertNotIn(name, entries)
            self.assertEqual(sha(ART / name), checksum)
            entries[name] = checksum
        self.assertEqual(set(entries), expected)
        self.assertFalse((ART / "COMPILE_PROOF.png").exists())

    def test_public_proof_has_no_machine_paths_or_native_attachment_claim(self):
        proof = self.manifest["compileEvidence"]
        self.assertNotIn("screenshot", proof)
        self.assertRegex(proof["nativeLogSha256"], r"^[A-F0-9]{64}$")
        for path in (ART / "COMPILE_LOG.log", ART / "MANIFEST.json", ART / "BUILD_LOG.txt"):
            self.assertNotRegex(path.read_text(encoding="utf-8"), r"(?<![A-Za-z])[A-Za-z]:[/\\]")
        for key in ("eaAttachedToChart", "algoTradingChanged", "orderOrTradeCommandSent", "demoExecutionValidated", "liveExecutionValidated", "nativeAttachmentValidated"):
            self.assertIs(self.manifest["safety"][key], False, key)
        self.assertIn("FILE_COMMON", self.manifest["safety"]["nativeAttachmentLimitation"])


if __name__ == "__main__":
    unittest.main()
