from __future__ import annotations

import copy
import hashlib
import importlib.util
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
RUNNER_PATH = PROJECT_ROOT / "runner" / "codex_cli_runner.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "ea_factory_custom_ema_profile_gate_bridge",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "ea_factory_custom_ema_profile_gate_runner",
        RUNNER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EaFactoryCustomEmaProfileGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()
        cls.runner = load_runner()

    @classmethod
    def canonical_source(cls) -> str:
        record = cls.bridge._ea_factory_custom_source_record(
            copy.deepcopy(cls.bridge.EA_FACTORY_CUSTOM_EMA_SMOKE_PROFILE_PAYLOAD)
        )
        return cls.runner._render_ea_factory_custom_ema_smoke_certified_source(
            source_record_digest=record["recordDigest"],
            strategy_spec_digest="a" * 64,
            strategy_brief_digest=record["strategyBriefDigest"],
        )

    def certified_manifest(self, source_digest: str = "b" * 64) -> dict:
        manifest = {
            "schemaVersion": (
                self.bridge.EA_FACTORY_CERTIFIED_EMA_SMOKE_MANIFEST_SCHEMA
            ),
            "coverageMode": (
                self.bridge.EA_FACTORY_CERTIFIED_EMA_SMOKE_COVERAGE_MODE
            ),
            "artifactKind": "expert_advisor",
            "targetPlatform": "mt5",
            "strategyBriefDigest": "c" * 64,
            "strategySpecDigest": "d" * 64,
            "sourceDigest": source_digest,
            "checks": {
                "bindingValid": True,
                "strategyBriefContract": True,
                "certifiedProfileSource": True,
                "testerOnly": True,
                "closedBarRetrySafe": True,
                "brokerExecutionSafe": True,
                "positionInvariant": True,
                "actualEntryProof": True,
                "structuredTelemetry": True,
                "pendingEntryCorrelation": True,
                "zeroBasedRequestIdentity": True,
            },
            "coveredFields": list(
                self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS
            ),
            "missingFields": [],
            "findings": [],
            "complete": True,
        }
        manifest["manifestDigest"] = (
            self.bridge._ea_factory_canonical_json_sha256(manifest)
        )
        return manifest

    def test_logic_recheck_accepts_only_current_sealed_certified_manifest(self) -> None:
        source_digest = "b" * 64
        build = {
            "platform": "mt5",
            "blueprintCoverageManifest": self.certified_manifest(source_digest),
        }
        metrics = {
            "sourceDigest": source_digest,
            "testerTradeRowsVerified": True,
            "tradeCount": 28,
            "tradeRowCount": 28,
            "buyTradeCount": 14,
            "sellTradeCount": 14,
        }

        projection = self.bridge._ea_factory_logic_recheck_projection(
            build,
            metrics,
        )
        self.assertTrue(projection["staticTenColumnSourceContractVerified"])
        self.assertTrue(projection["staticSixGroupSourceContractVerified"])
        self.assertTrue(projection["testerTradeRowsVerified"])
        self.assertTrue(projection["logicRecheckVerified"])

        mutations = []
        missing_zero_id = self.certified_manifest(source_digest)
        missing_zero_id["checks"].pop("zeroBasedRequestIdentity")
        mutations.append(missing_zero_id)

        false_zero_id = self.certified_manifest(source_digest)
        false_zero_id["checks"]["zeroBasedRequestIdentity"] = False
        mutations.append(false_zero_id)

        wrong_mode = self.certified_manifest(source_digest)
        wrong_mode["coverageMode"] = (
            self.bridge.EA_FACTORY_LEGACY_CERTIFIED_EMA_SMOKE_COVERAGE_MODE
        )
        mutations.append(wrong_mode)

        wrong_schema = self.certified_manifest(source_digest)
        wrong_schema["schemaVersion"] = (
            self.bridge.EA_FACTORY_LEGACY_CERTIFIED_EMA_SMOKE_MANIFEST_SCHEMA
        )
        mutations.append(wrong_schema)

        bad_digest = self.certified_manifest(source_digest)
        bad_digest["manifestDigest"] = "0" * 64
        mutations.append(bad_digest)

        for mutated in mutations:
            if mutated is not bad_digest:
                unsigned = {
                    key: value
                    for key, value in mutated.items()
                    if key != "manifestDigest"
                }
                mutated["manifestDigest"] = (
                    self.bridge._ea_factory_canonical_json_sha256(unsigned)
                )
            with self.subTest(
                schema=mutated.get("schemaVersion"),
                mode=mutated.get("coverageMode"),
                checks=mutated.get("checks"),
            ):
                invalid = self.bridge._ea_factory_logic_recheck_projection(
                    {"platform": "mt5", "blueprintCoverageManifest": mutated},
                    metrics,
                )
                self.assertFalse(
                    invalid["staticTenColumnSourceContractVerified"]
                )
                self.assertFalse(
                    invalid["staticSixGroupSourceContractVerified"]
                )
                self.assertFalse(invalid["logicRecheckVerified"])

    def spec_and_build(self, build_id: str = "ea-build-custom-ema-gate"):
        record = self.bridge._ea_factory_custom_source_record(
            copy.deepcopy(self.bridge.EA_FACTORY_CUSTOM_EMA_SMOKE_PROFILE_PAYLOAD)
        )
        spec = {
            "schemaVersion": "ea-factory-strategy-spec-v3",
            "buildId": build_id,
            "sourceRecordId": record["sourceRecordId"],
            "recordDigest": record["recordDigest"],
            "sourceKind": record["sourceKind"],
            "sourceKey": record["sourceKey"],
            "core": copy.deepcopy(record["core"]),
            "artifactKind": "expert_advisor",
            "targetPlatform": "mt5",
            "language": "mql5",
            "strategySchemaVersion": self.bridge.EA_STRATEGY_BRIEF_SCHEMA_VERSION,
            "strategyBrief": copy.deepcopy(record["strategyBrief"]),
            "strategyBriefDigest": record["strategyBriefDigest"],
            "immutable": True,
        }
        build = {
            "id": build_id,
            "platform": "mt5",
            "artifactKind": "expert_advisor",
            "sourceRecordId": record["sourceRecordId"],
            "sourceRecordDigest": record["recordDigest"],
            "workspace": {"strategySpecDigest": "a" * 64},
        }
        return record, spec, build

    def strategy_execution_profile(
        self,
        *,
        source_digest: str = "b" * 64,
    ) -> tuple[dict, dict, dict]:
        _record, spec, build = self.spec_and_build(
            build_id="ea-build-custom-ema-execution-proof"
        )
        build["versions"] = [{
            "sourceDigest": source_digest,
            "immutable": True,
        }]
        with mock.patch.object(
            self.bridge,
            "_ea_factory_review_strategy_spec",
            return_value=spec,
        ):
            profile = self.bridge._ea_factory_strategy_execution_profile(build)
        self.assertIsInstance(profile, dict)
        return profile, spec, build

    def strategy_execution_proof(
        self,
        profile: dict,
        *,
        directions: tuple[str, ...] = ("BUY", "SELL"),
        operation_id: str = "ea-visible-custom-ema-proof",
        symbol: str = "EURUSD",
        period: str = "H1",
    ) -> dict:
        line_hashes = [
            hashlib.sha256(f"telemetry-line-{index}".encode("utf-8")).hexdigest()
            for index in range((len(directions) * 3) + 1)
        ]
        sequences = []
        for index, direction in enumerate(directions):
            if direction == "BUY":
                fast2, fast1, slow2, slow1 = 1.0, 2.0, 1.0, 1.0
            else:
                fast2, fast1, slow2, slow1 = 2.0, 1.0, 2.0, 2.0
            sequences.append({
                "seq": index + 1,
                "direction": direction,
                "closedBarTime": 1_800_000_000 + index,
                "fast2": fast2,
                "fast1": fast1,
                "slow2": slow2,
                "slow1": slow1,
                "deal": 9_000 + index,
                "signalLineSha256": line_hashes[index * 3],
                "pendingLineSha256": line_hashes[index * 3 + 1],
                "entryLineSha256": line_hashes[index * 3 + 2],
            })
        buy_count = directions.count("BUY")
        sell_count = directions.count("SELL")
        signal_count = len(directions)
        return {
            "schemaVersion": (
                self.bridge.EA_FACTORY_STRATEGY_EXECUTION_PROOF_SCHEMA_VERSION
            ),
            "profileId": profile["profileId"],
            "sourceDigest": profile["sourceDigest"],
            "operationId": operation_id,
            "symbol": symbol,
            "period": period,
            "eventCount": (signal_count * 3) + 1,
            "signalCount": signal_count,
            "entryCount": signal_count,
            "rejectedCount": 0,
            "orphanCount": 0,
            "pendingCount": 0,
            "dataUnavailableCount": 0,
            "buySignalCount": buy_count,
            "sellSignalCount": sell_count,
            "buyEntryCount": buy_count,
            "sellEntryCount": sell_count,
            "sequences": sequences,
            "telemetryLineSha256s": line_hashes,
            "telemetryDigest": hashlib.sha256(
                "\n".join(line_hashes).encode("utf-8")
            ).hexdigest(),
            "finalLineSha256": line_hashes[-1],
            "verified": True,
        }

    def test_certified_build_generates_exact_strategy_execution_profile(self) -> None:
        source_digest = "c" * 64
        profile, _spec, _build = self.strategy_execution_profile(
            source_digest=source_digest,
        )
        self.assertEqual(
            profile,
            {
                "schemaVersion": (
                    self.bridge.EA_FACTORY_STRATEGY_EXECUTION_PROFILE_SCHEMA_VERSION
                ),
                "profileId": self.bridge.EA_FACTORY_CERTIFIED_EMA_SMOKE_PROFILE_ID,
                "sourceDigest": source_digest,
                "proofRequired": True,
                "fastPeriod": 10,
                "slowPeriod": 60,
                "previousShift": 2,
                "currentShift": 1,
                "requiredDirections": ["BUY", "SELL"],
                "profileDigest": profile["profileDigest"],
            },
        )
        profile_core = {
            key: value
            for key, value in profile.items()
            if key != "profileDigest"
        }
        expected_digest = hashlib.sha256(
            self.bridge.json.dumps(
                profile_core,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(profile["profileDigest"], expected_digest)

    def test_strategy_execution_proof_accepts_exact_buy_and_sell_crossovers(self) -> None:
        profile, _spec, _build = self.strategy_execution_profile()
        proof = self.strategy_execution_proof(profile)
        digest = self.bridge._ea_factory_strategy_execution_proof_digest(
            proof,
            profile=profile,
            operation_id=proof["operationId"],
            symbol=proof["symbol"],
            period=proof["period"],
        )
        expected = hashlib.sha256(
            self.bridge.json.dumps(
                proof,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(digest, expected)

    def test_strategy_execution_proof_rejects_wrong_crossover(self) -> None:
        profile, _spec, _build = self.strategy_execution_profile()
        proof = self.strategy_execution_proof(profile)
        proof["sequences"][0]["fast1"] = proof["sequences"][0]["slow1"]
        self.assertIsNone(
            self.bridge._ea_factory_strategy_execution_proof_digest(
                proof,
                profile=profile,
                operation_id=proof["operationId"],
                symbol=proof["symbol"],
                period=proof["period"],
            )
        )

    def test_strategy_execution_proof_rejects_missing_direction(self) -> None:
        profile, _spec, _build = self.strategy_execution_profile()
        proof = self.strategy_execution_proof(profile, directions=("BUY",))
        self.assertIsNone(
            self.bridge._ea_factory_strategy_execution_proof_digest(
                proof,
                profile=profile,
                operation_id=proof["operationId"],
                symbol=proof["symbol"],
                period=proof["period"],
            )
        )

    def test_strategy_execution_proof_rejects_self_consistent_line_tamper(self) -> None:
        profile, _spec, _build = self.strategy_execution_profile()
        proof = self.strategy_execution_proof(profile)
        proof["telemetryLineSha256s"][0] = hashlib.sha256(
            b"tampered-telemetry-line"
        ).hexdigest()
        proof["telemetryDigest"] = hashlib.sha256(
            "\n".join(proof["telemetryLineSha256s"]).encode("utf-8")
        ).hexdigest()
        self.assertIsNone(
            self.bridge._ea_factory_strategy_execution_proof_digest(
                proof,
                profile=profile,
                operation_id=proof["operationId"],
                symbol=proof["symbol"],
                period=proof["period"],
            )
        )

    def test_exact_profile_and_source_pass_deterministic_verifier(self) -> None:
        record, spec, build = self.spec_and_build()
        source = self.canonical_source().replace(
            "bound-by-test",
            record["strategyBriefDigest"],
        )
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        profile = self.bridge._ea_factory_trusted_custom_ema_smoke_profile(
            spec,
            build=build,
        )
        findings = self.bridge._ea_factory_custom_ema_smoke_source_findings(
            spec,
            source,
            build=build,
            source_digest=digest,
        )
        self.assertEqual(
            profile["profileId"],
            "custom-ema-10-60-closed-bar-smoke-mt5-v3",
        )
        self.assertEqual(findings, [])

        generic_manifest = self.bridge.build_compact_ea_source_manifest(
            source,
            strategy_brief=record["strategyBrief"],
            strategy_brief_digest=record["strategyBriefDigest"],
            strategy_spec_digest=build["workspace"]["strategySpecDigest"],
            source_digest=digest,
            target_platform="mt5",
        )
        certified_manifest = (
            self.bridge._ea_factory_custom_ema_certified_coverage_manifest(
                generic_manifest,
                strategy_spec=spec,
                source_text=source,
                build=build,
                source_digest=digest,
            )
        )
        self.assertIsNotNone(certified_manifest)
        self.assertTrue(certified_manifest["complete"])
        self.assertEqual(certified_manifest["findings"], [])
        self.assertTrue(certified_manifest["checks"]["structuredTelemetry"])
        self.assertTrue(certified_manifest["checks"]["pendingEntryCorrelation"])
        self.assertTrue(certified_manifest["checks"]["zeroBasedRequestIdentity"])

    def test_canonical_primary_proof_stream_matches_strict_runtime_parser_schema(self) -> None:
        source = self.canonical_source()
        primary_events = re.findall(
            r'EMA_SMOKE_V1 \{\\"event\\":\\"([^"\\]+)\\"',
            source,
        )
        self.assertEqual(
            sorted(set(primary_events)),
            ["entry", "final", "orphan_entry", "pending", "rejected", "signal"],
        )
        self.assertIn(
            'EMA_SMOKE_V1 {\\"event\\":\\"entry\\",\\"seq\\":%I64u,'
            '\\"direction\\":\\"%s\\",\\"closed_bar_time\\":%I64d,'
            '\\"deal\\":%I64u}',
            source,
        )
        for audit_event in (
            "accepted",
            "order_finalized",
            "entry_fill",
            "entry_fill_late",
            "entry_complete",
            "entry_identity",
        ):
            with self.subTest(audit_event=audit_event):
                self.assertNotIn(
                    f'EMA_SMOKE_V1 {{\\"event\\":\\"{audit_event}\\"',
                    source,
                )
                self.assertIn(
                    f'EMA_SMOKE_AUDIT_V1 {{\\"event\\":\\"{audit_event}\\"',
                    source,
                )

    def test_bridge_reconstructs_the_exact_bound_renderer_source(self) -> None:
        _record, spec, build = self.spec_and_build()
        self.assertEqual(
            self.bridge._ea_factory_custom_ema_expected_certified_source(
                spec,
                build,
            ),
            self.canonical_source(),
        )

    def test_certified_profile_rejects_noncanonical_bypass_mutations(self) -> None:
        record, spec, build = self.spec_and_build()
        source = self.canonical_source()
        mutations = {
            "disabled-tester-guard": source.replace(
                "if(MQLInfoInteger(MQL_TESTER) == 0) return(INIT_FAILED);",
                "if(false && MQLInfoInteger(MQL_TESTER) == 0) return(INIT_FAILED);",
                1,
            ),
            "normalize-volume-early-return": source.replace(
                "double NormalizeFixedVolume()\n{",
                "double NormalizeFixedVolume()\n{\n   return(0.02);",
                1,
            ),
            "count-managed-early-return": source.replace(
                "int CountManagedPositions()\n{",
                "int CountManagedPositions()\n{\n   return(0);",
                1,
            ),
            "normalize-price-early-return": source.replace(
                "double NormalizePriceDirectional(const double price, const bool roundUp)\n{",
                "double NormalizePriceDirectional(const double price, const bool roundUp)\n{\n   return(price);",
                1,
            ),
            "trade-retcode-unconditional-true": source.replace(
                "   return(retcode == TRADE_RETCODE_DONE ||\n"
                "          retcode == TRADE_RETCODE_DONE_PARTIAL ||\n"
                "          retcode == TRADE_RETCODE_PLACED);",
                "   if(retcode == TRADE_RETCODE_DONE ||\n"
                "      retcode == TRADE_RETCODE_DONE_PARTIAL ||\n"
                "      retcode == TRADE_RETCODE_PLACED) {}\n"
                "   return(true);",
                1,
            ),
            "spaced-forbidden-side-effect": source.replace(
                "void OnTick()\n{",
                "void OnTick()\n{\n   ExpertRemove ();",
                1,
            ),
        }
        for label, mutation in mutations.items():
            with self.subTest(label=label):
                self.assertNotEqual(mutation, source)
                digest = hashlib.sha256(mutation.encode("utf-8")).hexdigest()
                findings = self.bridge._ea_factory_custom_ema_smoke_source_findings(
                    spec,
                    mutation,
                    build=build,
                    source_digest=digest,
                )
                self.assertIn("custom_ema_certified_source_mismatch", findings)
                generic_manifest = self.bridge.build_compact_ea_source_manifest(
                    mutation,
                    strategy_brief=record["strategyBrief"],
                    strategy_brief_digest=record["strategyBriefDigest"],
                    strategy_spec_digest=build["workspace"]["strategySpecDigest"],
                    source_digest=digest,
                    target_platform="mt5",
                )
                self.assertIsNone(
                    self.bridge._ea_factory_custom_ema_certified_coverage_manifest(
                        generic_manifest,
                        strategy_spec=spec,
                        source_text=mutation,
                        build=build,
                        source_digest=digest,
                    )
                )

    def test_runner_certified_scaffold_is_full_lineage_and_digest_bound(self) -> None:
        record, spec, build = self.spec_and_build(
            build_id="ea-build-custom-ema-certified-runner"
        )
        strategy_spec_digest = build["workspace"]["strategySpecDigest"]
        runner_profile = self.runner._ea_factory_trusted_custom_ema_smoke_profile(
            spec
        )
        bridge_profile = self.bridge._ea_factory_trusted_custom_ema_smoke_profile(
            spec,
            build=build,
        )

        self.assertEqual(runner_profile, bridge_profile)
        self.assertEqual(
            self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_BRIEF,
            record["strategyBrief"],
        )
        self.assertEqual(
            self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_CORE,
            record["core"],
        )
        source = self.runner._build_ea_factory_source_semantic_repair_scaffold(
            spec["strategyBrief"],
            strategy_brief_digest=spec["strategyBriefDigest"],
            strategy_spec_digest=strategy_spec_digest,
            target_platform="mt5",
            source_record_digest=spec["recordDigest"],
            trusted_custom_ema_smoke_profile=runner_profile,
        )
        self.assertTrue(source)
        self.assertIn(
            f'EA_SOURCE_RECORD_SHA256:{record["recordDigest"]}',
            source,
        )
        self.assertIn(
            f"EA_STRATEGY_SPEC_SHA256:{strategy_spec_digest}",
            source,
        )
        self.assertIn(
            f'EA_STRATEGY_BRIEF_SHA256:{record["strategyBriefDigest"]}',
            source,
        )
        file_name, validated_source, source_bytes = (
            self.runner._validate_ea_factory_generated_source(
                self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_CERTIFIED_FILE_NAME,
                source,
                ".mq5",
                "expert_advisor",
            )
        )
        self.assertEqual(file_name, "CertifiedCustomEmaSmokeMT5.mq5")
        self.assertEqual(validated_source, source)
        self.assertEqual(source_bytes, source.encode("utf-8"))
        source_digest = hashlib.sha256(source_bytes).hexdigest()
        generic_manifest = self.runner.build_compact_ea_source_manifest(
            source,
            strategy_brief=spec["strategyBrief"],
            strategy_brief_digest=spec["strategyBriefDigest"],
            strategy_spec_digest=strategy_spec_digest,
            source_digest=source_digest,
            target_platform="mt5",
        )
        certified_manifest = (
            self.runner._ea_factory_custom_ema_certified_coverage_manifest(
                source,
                strategy_brief=spec["strategyBrief"],
                strategy_brief_digest=spec["strategyBriefDigest"],
                strategy_spec_digest=strategy_spec_digest,
                source_digest=source_digest,
                target_platform="mt5",
                source_record_digest=spec["recordDigest"],
            )
        )
        self.assertIsNotNone(certified_manifest)
        self.assertTrue(certified_manifest["complete"], certified_manifest)
        bridge_certified_manifest = (
            self.bridge._ea_factory_custom_ema_certified_coverage_manifest(
                generic_manifest,
                strategy_spec=spec,
                source_text=source,
                build=build,
                source_digest=source_digest,
            )
        )
        self.assertEqual(bridge_certified_manifest, certified_manifest)
        self.assertEqual(
            self.bridge._ea_factory_custom_ema_smoke_source_findings(
                spec,
                source,
                build=build,
                source_digest=source_digest,
            ),
            [],
        )
        self.assertEqual(
            self.runner._ea_factory_certified_scaffold_profile(
                spec["strategyBriefDigest"],
                source,
                source_record_digest=spec["recordDigest"],
                strategy_spec_digest=strategy_spec_digest,
            ),
            self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_CERTIFIED_PROFILE_VERSION,
        )

    def test_runner_fallback_rejects_near_profiles_and_scaffold_mutations(self) -> None:
        record, spec, build = self.spec_and_build(
            build_id="ea-build-custom-ema-certified-adversarial"
        )
        strategy_spec_digest = build["workspace"]["strategySpecDigest"]
        profile = self.runner._ea_factory_trusted_custom_ema_smoke_profile(spec)
        source = self.runner._build_ea_factory_source_semantic_repair_scaffold(
            spec["strategyBrief"],
            strategy_brief_digest=spec["strategyBriefDigest"],
            strategy_spec_digest=strategy_spec_digest,
            target_platform="mt5",
            source_record_digest=spec["recordDigest"],
            trusted_custom_ema_smoke_profile=profile,
        )
        self.assertTrue(source)

        profile_mutations = []
        for field, replacement in (
            ("sourceKind", "verified_deep_research_sheet"),
            ("sourceRecordId", "ea-source-name-only-spoof"),
            ("sourceKey", "custom-operator-name-only-spoof"),
            ("recordDigest", "0" * 64),
            ("targetPlatform", "mt4"),
            ("artifactKind", "custom_indicator"),
            ("language", "mql4"),
        ):
            mutated = copy.deepcopy(spec)
            mutated[field] = replacement
            profile_mutations.append(mutated)
        brief_mutation = copy.deepcopy(spec)
        brief_mutation["strategyBrief"]["systemName"] += " spoof"
        profile_mutations.append(brief_mutation)
        core_mutation = copy.deepcopy(spec)
        core_mutation["core"]["record_id"] = "custom-spoof"
        profile_mutations.append(core_mutation)
        for ordinal, mutated_spec in enumerate(profile_mutations):
            with self.subTest(profile_mutation=ordinal):
                self.assertIsNone(
                    self.runner._ea_factory_trusted_custom_ema_smoke_profile(
                        mutated_spec
                    )
                )
                self.assertEqual(
                    self.runner._build_ea_factory_source_semantic_repair_scaffold(
                        mutated_spec["strategyBrief"],
                        strategy_brief_digest=mutated_spec["strategyBriefDigest"],
                        strategy_spec_digest=strategy_spec_digest,
                        target_platform=mutated_spec.get("targetPlatform"),
                        source_record_digest=mutated_spec.get("recordDigest"),
                        trusted_custom_ema_smoke_profile=None,
                    ),
                    "",
                )

        source_mutations = (
            source.replace(strategy_spec_digest, "b" * 64, 1),
            source.replace(record["recordDigest"], "c" * 64, 1),
            source.replace(record["strategyBriefDigest"], "d" * 64, 1),
            source.replace("const double FixedLot = 0.01;", "const double FixedLot = 0.02;", 1),
            source + "\nvoid HiddenBackdoor() {}\n",
        )
        for ordinal, mutated_source in enumerate(source_mutations):
            with self.subTest(source_mutation=ordinal):
                self.assertNotEqual(mutated_source, source)
                self.assertEqual(
                    self.runner._ea_factory_certified_scaffold_profile(
                        spec["strategyBriefDigest"],
                        mutated_source,
                        source_record_digest=spec["recordDigest"],
                        strategy_spec_digest=strategy_spec_digest,
                    ),
                    "",
                )

    def test_profile_recognizer_rejects_name_only_and_lineage_mutations(self) -> None:
        _record, spec, build = self.spec_and_build()
        mutations = []
        wrong_kind = copy.deepcopy(spec)
        wrong_kind["sourceKind"] = "verified_deep_research_sheet"
        mutations.append((wrong_kind, build))
        wrong_digest = copy.deepcopy(spec)
        wrong_digest["recordDigest"] = "0" * 64
        mutations.append((wrong_digest, build))
        wrong_brief = copy.deepcopy(spec)
        wrong_brief["strategyBrief"]["entryRules"] += " Name-only spoof."
        mutations.append((wrong_brief, build))
        wrong_platform = copy.deepcopy(spec)
        wrong_platform["targetPlatform"] = "mt4"
        mutations.append((wrong_platform, build))
        wrong_build = copy.deepcopy(build)
        wrong_build["sourceRecordDigest"] = "1" * 64
        mutations.append((spec, wrong_build))
        for ordinal, (mutated_spec, mutated_build) in enumerate(mutations):
            with self.subTest(ordinal=ordinal):
                self.assertIsNone(
                    self.bridge._ea_factory_trusted_custom_ema_smoke_profile(
                        mutated_spec,
                        build=mutated_build,
                    )
                )

    def test_semantic_mutations_fail_closed(self) -> None:
        _record, spec, build = self.spec_and_build()
        source = self.canonical_source()
        mutations = {
            "ema-period": source.replace("const int FastPeriod = 10;", "const int FastPeriod = 11;"),
            "forming-bar": source.replace(
                "CopyBuffer(fastHandle, 0, 2, 1, fastBar2)",
                "CopyBuffer(fastHandle, 0, 0, 1, fastBar2)",
            ),
            "unchecked-copy": source.replace(
                "if(CopyBuffer(fastHandle, 0, 2, 1, fastBar2) != 1 ||",
                "if(CopyBuffer(fastHandle, 0, 2, 1, fastBar2) == 1 ||",
            ),
            "buy-not-exact": source.replace(
                "fastBar2[0] <= slowBar2[0]",
                "fastBar2[0] < slowBar2[0]",
            ),
            "extra-signal-assignment": source.replace(
                "signal = ORDER_TYPE_SELL;",
                "signal = ORDER_TYPE_SELL; signal = ORDER_TYPE_BUY;",
            ),
            "tester-not-fail-closed": source.replace(
                "MQLInfoInteger(MQL_TESTER) == 0",
                "MQLInfoInteger(MQL_TESTER) == 1",
            ),
            "closed-bar-guard": source.replace(
                "Bars(_Symbol, _Period) < 61",
                "Bars(_Symbol, _Period) < 60",
            ),
            "closed-price-not-fail-closed": source.replace(
                "confirmedClose <= 0.0",
                "confirmedClose < 0.0",
            ),
            "new-bar-inverted": source.replace(
                "currentBar == lastBar",
                "currentBar != lastBar",
            ),
            "sl-default": source.replace(
                "StopLossPips = 30.0",
                "StopLossPips = 31.0",
            ),
            "extra-input": source.replace(
                "input double TakeProfitPips = 60.0;",
                "input double TakeProfitPips = 60.0;\ninput bool UnsafeMode = true;",
            ),
            "wrong-signed-sl": source.replace(
                "MathMin(entryPrice - requestedSLDistance, tick.bid - brokerMinimum)",
                "MathMax(entryPrice + requestedSLDistance, tick.bid - brokerMinimum)",
            ),
            "sl-distance-offset": source.replace(
                "const double requestedSLDistance = StopLossPips * pip;",
                "const double requestedSLDistance = StopLossPips * pip + pip;",
            ),
            "sl-based-on-wrong-market-side": source.replace(
                "const double entryPrice = signal == ORDER_TYPE_BUY ? tick.ask : tick.bid;",
                "const double entryPrice = signal == ORDER_TYPE_BUY ? tick.bid : tick.ask;",
            ),
            "lot-not-fixed": source.replace(
                "const double FixedLot = 0.01;",
                "const double FixedLot = 0.02;",
            ),
            "lot-input": source.replace(
                "const double FixedLot = 0.01;",
                "input double FixedLot = 0.01;",
            ),
            "lot-multiplied-at-open": source.replace(
                "openRequest.volume = normalizedVolume;",
                "openRequest.volume = normalizedVolume * 2.0;",
            ),
            "lot-not-fail-closed": source.replace(
                "if(FixedLot <= 0.0) return;",
                "if(FixedLot < 0.0) return;",
            ),
            "volume-step-bypassed": source.replace(
                "MathRound(FixedLot / step) * step",
                "FixedLot",
            ),
            "tick-rounding-bypassed": source.replace(
                "MathCeil(ticks - 1e-9) * tickSize",
                "price",
            ),
            "stop-level-bypassed": source.replace(
                "SYMBOL_TRADE_STOPS_LEVEL",
                "SYMBOL_SPREAD",
            ),
            "freeze-level-bypassed": source.replace(
                "SYMBOL_TRADE_FREEZE_LEVEL",
                "SYMBOL_SPREAD",
            ),
            "filling-bypassed": source.replace(
                "openRequest.type_filling = filling;",
                "openRequest.type_filling = ORDER_FILLING_RETURN;",
            ),
            "trade-retcode-always-accepted": source.replace(
                "   return(retcode == TRADE_RETCODE_DONE ||\n"
                "          retcode == TRADE_RETCODE_DONE_PARTIAL ||\n"
                "          retcode == TRADE_RETCODE_PLACED);",
                "   if(retcode == TRADE_RETCODE_DONE ||\n"
                "      retcode == TRADE_RETCODE_DONE_PARTIAL ||\n"
                "      retcode == TRADE_RETCODE_PLACED) {}\n"
                "   return(true);",
                1,
            ),
            "position-cap": source.replace(
                "const int PositionCap = 1;",
                "const int PositionCap = 2;",
            ),
            "close-direction": source.replace(
                "closeSellRequest.type = ORDER_TYPE_BUY;",
                "closeSellRequest.type = ORDER_TYPE_SELL;",
            ),
            "close-send-unchecked": source.replace(
                "if(!OrderSend(closeSellRequest, closeSellResult) ||",
                "if(OrderSend(closeSellRequest, closeSellResult) ||",
            ),
            "close-retcode-unchecked": source.replace(
                "!TradeRetcodeAccepted(closeSellResult.retcode)",
                "TradeRetcodeAccepted(closeSellResult.retcode)",
            ),
            "close-not-checked": source.replace(
                "if(!CloseOpposite(signal))",
                "if(CloseOpposite(signal))",
            ),
            "no-zero-recount": source.replace(
                "if(CountManagedPositions() != 0)",
                "if(CountManagedPositions() < 0)",
            ),
            "count-not-magic-scoped": source.replace(
                "PositionGetInteger(POSITION_MAGIC) == MagicNumber) count++;",
                "PositionGetInteger(POSITION_MAGIC) >= 0) count++;",
                1,
            ),
            "count-not-symbol-scoped": source.replace(
                "PositionGetString(POSITION_SYMBOL) == _Symbol &&",
                "PositionGetString(POSITION_SYMBOL) != \"\" &&",
                1,
            ),
            "extra-unscoped-count": source.replace(
                "int count = 0;",
                "int count = 0; count++;",
                1,
            ),
            "actual-entry-counter-removed": source.replace(
                "if(direction == ORDER_TYPE_BUY) buyEntryCount++;",
                "if(direction == ORDER_TYPE_BUY) rejectedRequestCount++;",
            ),
            "signal-sequence-not-monotonic": source.replace(
                "const ulong signalSeq = ++signalSequence;",
                "const ulong signalSeq = signalSequence;",
            ),
            "signal-telemetry-not-ema-bound": source.replace(
                "      fastBar2[0],\n      fastBar1[0],\n"
                "      slowBar2[0],\n      slowBar1[0]",
                "      fastBar1[0],\n      fastBar2[0],\n"
                "      slowBar1[0],\n      slowBar2[0]",
                1,
            ),
            "signal-telemetry-period-spoof": source.replace(
                '"fast_period\\\":%d,\\\"slow_period\\\":%d,',
                '"fast_period\\\":11,\\\"slow_period\\\":60,',
                1,
            ),
            "pending-sequence-not-set": source.replace(
                "pendingSignalSeq = seq;",
                "pendingSignalSeq = 0;",
                1,
            ),
            "pending-direction-not-set": source.replace(
                "pendingSignalDirection = direction;",
                "pendingSignalDirection = (ENUM_ORDER_TYPE)SIGNAL_NONE;",
                1,
            ),
            "pending-set-after-send": source.replace(
                "   SetPendingSignal(signalSeq, signal, closedBarTime);\n"
                "   ResetLastError();\n"
                "   const bool sent = OrderSend(openRequest, openResult);",
                "   ResetLastError();\n"
                "   const bool sent = OrderSend(openRequest, openResult);\n"
                "   SetPendingSignal(signalSeq, signal, closedBarTime);",
                1,
            ),
            "accepted-identity-not-required": source.replace(
                "(orderTicket == 0 && dealTicket == 0)",
                "(orderTicket == 0 && dealTicket == 0 && requestId == 0)",
                1,
            ),
            "valid-zero-request-id-rejected": source.replace(
                "if(pendingSignalSeq != seq ||\n"
                "      (orderTicket == 0 && dealTicket == 0)) return(false);",
                "if(pendingSignalSeq != seq || requestId == 0 ||\n"
                "      (orderTicket == 0 && dealTicket == 0)) return(false);",
                1,
            ),
            "request-identity-not-bound": source.replace(
                "pendingRequestId = requestId;",
                "pendingRequestId = 0;",
                1,
            ),
            "request-bound-flag-not-set": source.replace(
                "pendingRequestIdentityBound = true;",
                "pendingRequestIdentityBound = false;",
                1,
            ),
            "request-callback-bound-flag-bypassed": source.replace(
                "pendingSignalSeq != 0 && pendingRequestIdentityBound &&",
                "pendingSignalSeq != 0 && true &&",
                1,
            ),
            "deal-bound-flag-bypassed": source.replace(
                "pendingSignalSeq == 0 || !pendingRequestIdentityBound ||",
                "pendingSignalSeq == 0 || false ||",
                1,
            ),
            "split-fill-counted-as-new-entry": source.replace(
                "if(!pendingEntryCounted)",
                "if(true)",
                1,
            ),
            "completed-order-split-fill-not-correlated": source.replace(
                "if(MatchCompletedOrder(\n",
                "if(false && MatchCompletedOrder(\n",
                1,
            ),
            "accepted-order-identity-bypassed": source.replace(
                "dealOrder != 0 && dealOrder == pendingOrderTicket;",
                "dealOrder != 0 && pendingSignalDirection == direction;",
                1,
            ),
            "accepted-deal-identity-bypassed": source.replace(
                "transaction.deal == pendingAcceptedDealTicket;",
                "pendingSignalDirection == direction;",
                1,
            ),
            "orphan-entry-count-removed": source.replace(
                "      orphanEntryCount++;",
                "      dataUnavailableCount++;",
                1,
            ),
            "entry-not-correlated-to-pending-direction": source.replace(
                "pendingSignalDirection != direction || dealOrder == 0",
                "dealOrder == 0",
                1,
            ),
            "deinit-pending-not-rejected": source.replace(
                'RejectSignal(seq, direction, closedBarTime, "deinit_pending");',
                "ClearPendingSignal();",
                1,
            ),
            "final-omits-orphan": source.replace(
                '\\"orphan\\\":%d,',
                "",
                1,
            ),
            "transient-commits-bar": source.replace(
                "   double fastBar2[1];",
                "   lastBar = currentBar;\n   double fastBar2[1];",
                1,
            ).replace(
                "   lastBar = currentBar;\n   ENUM_ORDER_TYPE",
                "   ENUM_ORDER_TYPE",
                1,
            ),
        }
        for label, mutation in mutations.items():
            with self.subTest(label=label):
                self.assertNotEqual(mutation, source, label)
                digest = hashlib.sha256(mutation.encode("utf-8")).hexdigest()
                findings = self.bridge._ea_factory_custom_ema_smoke_source_findings(
                    spec,
                    mutation,
                    build=build,
                    source_digest=digest,
                )
                self.assertIsInstance(findings, list)
                self.assertTrue(findings, label)

    def test_stable_findings_name_the_failed_repair_area(self) -> None:
        _record, spec, build = self.spec_and_build()
        source = self.canonical_source()
        cases = (
            (
                source.replace(
                    "if(CopyBuffer(fastHandle, 0, 2, 1, fastBar2) != 1 ||",
                    "if(CopyBuffer(fastHandle, 0, 2, 1, fastBar2) == 1 ||",
                ),
                "custom_ema_closed_bar_buffers_invalid",
            ),
            (
                source.replace(
                    "openRequest.volume = normalizedVolume;",
                    "openRequest.volume = normalizedVolume * 2.0;",
                ),
                "custom_ema_fixed_lot_invalid",
            ),
            (
                source.replace(
                    "const double requestedSLDistance = StopLossPips * pip;",
                    "const double requestedSLDistance = StopLossPips * pip + pip;",
                ),
                "custom_ema_signed_pip_stops_invalid",
            ),
            (
                source.replace(
                    "currentBar == lastBar",
                    "currentBar != lastBar",
                ),
                "custom_ema_closed_bar_guard_invalid",
            ),
            (
                source.replace(
                    "int count = 0;",
                    "int count = 0; count++;",
                    1,
                ),
                "custom_ema_position_scope_invalid",
            ),
            (
                source.replace(
                    "      fastBar2[0],\n      fastBar1[0],\n"
                    "      slowBar2[0],\n      slowBar1[0]",
                    "      fastBar1[0],\n      fastBar2[0],\n"
                    "      slowBar1[0],\n      slowBar2[0]",
                    1,
                ),
                "custom_ema_structured_signal_telemetry_invalid",
            ),
            (
                source.replace(
                    "pendingSignalSeq = seq;",
                    "pendingSignalSeq = 0;",
                    1,
                ),
                "custom_ema_pending_correlation_invalid",
            ),
            (
                source.replace(
                    "pendingSignalDirection != direction || dealOrder == 0",
                    "dealOrder == 0",
                    1,
                ),
                "custom_ema_actual_entry_proof_invalid",
            ),
            (
                source.replace('\\"orphan\\\":%d,', "", 1),
                "custom_ema_final_telemetry_invalid",
            ),
            (
                source.replace(
                    "   return(retcode == TRADE_RETCODE_DONE ||\n"
                    "          retcode == TRADE_RETCODE_DONE_PARTIAL ||\n"
                    "          retcode == TRADE_RETCODE_PLACED);",
                    "   return(true);",
                    1,
                ),
                "custom_ema_trade_retcode_contract_invalid",
            ),
        )
        for mutation, expected in cases:
            with self.subTest(expected=expected):
                digest = hashlib.sha256(mutation.encode("utf-8")).hexdigest()
                findings = self.bridge._ea_factory_custom_ema_smoke_source_findings(
                    spec,
                    mutation,
                    build=build,
                    source_digest=digest,
                )
                self.assertIn(expected, findings)

    def test_copybuffer_transient_does_not_commit_the_bar_and_is_retryable(self) -> None:
        _record, spec, build = self.spec_and_build()
        source = self.canonical_source()
        on_tick = source[source.index("void OnTick()") : source.index("void OnTradeTransaction(")]
        first_copy = on_tick.index(
            "CopyBuffer(fastHandle, 0, 2, 1, fastBar2)"
        )
        ready_validation = on_tick.index("slowBar1[0] == EMPTY_VALUE")
        commit = on_tick.index("lastBar = currentBar;")
        signal = on_tick.index(
            "ENUM_ORDER_TYPE signal = (ENUM_ORDER_TYPE)SIGNAL_NONE;"
        )
        self.assertLess(first_copy, ready_validation)
        self.assertLess(ready_validation, commit)
        self.assertLess(commit, signal)
        self.assertEqual(source.count('lastOutcome = "data_unavailable";'), 2)
        self.assertIn('lastOutcome = "no_signal";', source)

        early_commit = source.replace(
            "   double fastBar2[1];",
            "   lastBar = currentBar;\n   double fastBar2[1];",
            1,
        ).replace("   lastBar = currentBar;\n   ENUM_ORDER_TYPE", "   ENUM_ORDER_TYPE", 1)
        findings = self.bridge._ea_factory_custom_ema_smoke_source_findings(
            spec,
            early_commit,
            build=build,
            source_digest=hashlib.sha256(early_commit.encode("utf-8")).hexdigest(),
        )
        self.assertIn("custom_ema_closed_bar_guard_invalid", findings)

        collapsed_outcome = source.replace(
            'lastOutcome = "data_unavailable";',
            'lastOutcome = "no_signal";',
            1,
        )
        findings = self.bridge._ea_factory_custom_ema_smoke_source_findings(
            spec,
            collapsed_outcome,
            build=build,
            source_digest=hashlib.sha256(collapsed_outcome.encode("utf-8")).hexdigest(),
        )
        self.assertIn("custom_ema_data_retry_invalid", findings)

    def test_telemetry_and_pending_contract_cannot_be_spoofed_by_comments_or_strings(self) -> None:
        _record, spec, build = self.spec_and_build()
        source = self.canonical_source()
        signal_literal = (
            'EMA_SMOKE_V1 {\\"event\\":\\"signal\\",\\"seq\\":%I64u,'
            '\\"direction\\":\\"%s\\",\\"closed_bar_time\\":%I64d,'
            '\\"fast_period\\":%d,\\"slow_period\\":%d,'
            '\\"previous_shift\\":2,\\"current_shift\\":1,'
            '\\"fast_2\\":%.10f,\\"fast_1\\":%.10f,'
            '\\"slow_2\\":%.10f,\\"slow_1\\":%.10f}'
        )
        executable_spoof = source.replace(
            signal_literal,
            signal_literal.replace("EMA_SMOKE_V1", "EMA_SMOKE_BAD"),
            1,
        ).replace(
            "   PrintFormat(\n"
            '      "EMA_SMOKE_BAD',
            f'   string telemetrySpoof = "{signal_literal}";\n'
            "   PrintFormat(\n"
            '      "EMA_SMOKE_BAD',
            1,
        )
        pending_comment_spoof = source.replace(
            "pendingSignalSeq = seq;",
            "pendingSignalSeq = 0; // pendingSignalSeq = seq;",
            1,
        )
        for mutation, expected in (
            (
                executable_spoof,
                "custom_ema_structured_signal_telemetry_invalid",
            ),
            (
                pending_comment_spoof,
                "custom_ema_pending_correlation_invalid",
            ),
        ):
            with self.subTest(expected=expected):
                self.assertNotEqual(mutation, source)
                findings = self.bridge._ea_factory_custom_ema_smoke_source_findings(
                    spec,
                    mutation,
                    build=build,
                    source_digest=hashlib.sha256(mutation.encode("utf-8")).hexdigest(),
                )
                self.assertIn(expected, findings)

    def test_source_digest_is_part_of_the_profile_evidence(self) -> None:
        _record, spec, build = self.spec_and_build()
        findings = self.bridge._ea_factory_custom_ema_smoke_source_findings(
            spec,
            self.canonical_source(),
            build=build,
            source_digest="0" * 64,
        )
        self.assertIn("custom_ema_source_digest_mismatch", findings)

    def test_generation_retry_and_review_prompts_match_the_verifier_shape(self) -> None:
        _record, spec, build = self.spec_and_build()
        build.update({
            "sourceReportId": "report-custom-ema-source",
            "versions": [{"sourceDigest": "b" * 64, "immutable": True}],
            "stages": [{
                "id": "generate_source",
                "reportId": "report-custom-ema-generation",
            }],
        })
        with mock.patch.object(
            self.bridge,
            "_ea_factory_review_strategy_spec",
            return_value=spec,
        ):
            generation = self.bridge._ea_factory_generation_brief(build)
            review = self.bridge._ea_factory_review_brief(build)

        self.assertLessEqual(len(generation), 2400)
        self.assertIn("also retry", generation)
        self.assertIn("four checked CopyBuffer 2/1 reads", generation)
        self.assertIn("commit last-bar only after finite/non-EMPTY data", generation)
        self.assertIn("Exact BUY <=/> and SELL >=/<", generation)
        self.assertIn("Count positions+orders by _Symbol+Magic", generation)
        self.assertIn("Close inverse with checked send/retcode", generation)
        self.assertIn("broker-safe volume, tick, stops, filling", generation)
        self.assertIn("No include/external dependency", generation)
        self.assertLessEqual(len(review), 2400)
        self.assertIn("EMA10/60 CopyBuffer 2/1 in OnTick", review)
        self.assertIn("last-bar commit only after ready finite samples", review)
        self.assertIn("same-line inverse signals", review)
        self.assertIn("broker-safe volume, tick, stop-level and filling", review)
        self.assertIn("positions+orders scoped _Symbol+Magic", review)
        self.assertIn("literal inverse close requests", review)
        self.assertIn("recount zero before reverse", review)

    def test_static_review_surfaces_stable_profile_finding_before_compile(self) -> None:
        record, spec, build = self.spec_and_build()
        source = self.canonical_source().replace(
            "bound-by-test",
            record["strategyBriefDigest"],
        )
        unsafe = source.replace(
            "MQLInfoInteger(MQL_TESTER) == 0",
            "MQLInfoInteger(MQL_TESTER) == 1",
        )
        with mock.patch.object(
            self.bridge,
            "_ea_factory_review_strategy_spec",
            return_value=spec,
        ):
            self.assertEqual(
                self.bridge._ea_factory_compact_ea_static_review_findings(
                    build,
                    source,
                ),
                [],
            )
            findings = self.bridge._ea_factory_compact_ea_static_review_findings(
                build,
                unsafe,
            )
        self.assertIn("custom_ema_tester_guard_missing", findings)

    def test_build_revalidation_accepts_only_exact_certified_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                record = self.bridge._ea_factory_custom_source_record(
                    copy.deepcopy(
                        self.bridge.EA_FACTORY_CUSTOM_EMA_SMOKE_PROFILE_PAYLOAD
                    )
                )
                build_id = "ea-build-custom-ema-revalidation"
                workspace = self.bridge._ea_factory_create_build_workspace(
                    build_id,
                    record,
                    "mt5",
                    "expert_advisor",
                )
                strategy_mission = {"id": "mission-custom-ema-revalidation-spec"}
                strategy_report = {"id": "report-custom-ema-revalidation-spec"}
                now = "2026-10-16T00:00:00Z"
                build = {
                    "schemaVersion": "ea-factory-build-v1",
                    "id": build_id,
                    "sourceRecordId": record["sourceRecordId"],
                    "sourceDisplayName": record["displayName"],
                    "sourceRecordDigest": record["recordDigest"],
                    "sourceReportId": strategy_report["id"],
                    "sourceMissionId": strategy_mission["id"],
                    "platform": "mt5",
                    "artifactKind": "expert_advisor",
                    "brief": "",
                    "status": "ready",
                    "workspace": workspace,
                    "stages": self.bridge._ea_factory_initial_stages(
                        "mt5",
                        strategy_mission,
                        strategy_report,
                        "expert_advisor",
                    ),
                    "versions": [],
                    "createIdempotencyKey": None,
                    "createIdempotencyKeys": [],
                    "createRequestDigest": (
                        self.bridge._ea_factory_create_request_digest(
                            record["sourceRecordId"],
                            "mt5",
                            "",
                            "expert_advisor",
                        )
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
                self.bridge._ea_factory_stage_row(build, "strategy_spec")[
                    "artifacts"
                ] = [row["fileId"] for row in strategy_artifacts]

                build_dir = root / "workspace" / "ea-factory" / build_id
                spec_path = build_dir / "Source" / "strategy-spec-v01.json"
                spec = self.bridge.read_json(spec_path, None)
                source = self.canonical_source().replace(
                    "EA_STRATEGY_SPEC_SHA256:" + ("a" * 64),
                    "EA_STRATEGY_SPEC_SHA256:" + workspace["strategySpecDigest"],
                )
                source_path = build_dir / "Source" / "CertifiedCustomEmaSmokeMT5.mq5"
                version_path = (
                    build_dir
                    / "EA_Versions"
                    / "CertifiedCustomEmaSmokeMT5_v01.mq5"
                )
                source_path.write_text(source, encoding="utf-8", newline="\n")
                version_path.write_text(source, encoding="utf-8", newline="\n")
                source_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()

                generic_manifest = self.bridge.build_compact_ea_source_manifest(
                    source,
                    strategy_brief=spec["strategyBrief"],
                    strategy_brief_digest=spec["strategyBriefDigest"],
                    strategy_spec_digest=workspace["strategySpecDigest"],
                    source_digest=source_digest,
                    target_platform="mt5",
                )
                self.assertFalse(generic_manifest["complete"], generic_manifest)
                certified_manifest = (
                    self.bridge._ea_factory_custom_ema_certified_coverage_manifest(
                        generic_manifest,
                        strategy_spec=spec,
                        source_text=source,
                        build=build,
                        source_digest=source_digest,
                    )
                )
                self.assertIsNotNone(certified_manifest)
                self.assertTrue(certified_manifest["complete"])

                generation_report_id = "report-custom-ema-revalidation-generation"
                build["versions"] = [{
                    "version": 1,
                    "fileName": version_path.name,
                    "sourceDigest": source_digest,
                    "sourceFile": f"Source/{source_path.name}",
                    "versionFile": f"EA_Versions/{version_path.name}",
                    "sourceReportId": generation_report_id,
                    "immutable": True,
                    "createdAt": now,
                }]
                build["blueprintCoverageManifest"] = copy.deepcopy(
                    certified_manifest
                )
                source_artifacts = self.bridge._ea_factory_register_artifacts(
                    build,
                    [
                        {
                            "relativePath": f"Source/{source_path.name}",
                            "stageId": "generate_source",
                            "reportId": generation_report_id,
                            "artifactKind": "generated_source",
                        },
                        {
                            "relativePath": f"EA_Versions/{version_path.name}",
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
                    "missionId": "mission-custom-ema-revalidation-generation",
                    "reportId": generation_report_id,
                    "evidenceVerified": True,
                    "artifacts": [row["fileId"] for row in source_artifacts],
                    "blueprintCoverageManifest": copy.deepcopy(
                        certified_manifest
                    ),
                })

                validated = self.bridge._ea_factory_revalidated_build(build)

                self.assertEqual(validated["coverageStatus"], "compact_current")
                self.assertFalse(validated["coverageUpgradeRequired"])
                self.assertEqual(
                    validated["blueprintCoverageManifest"],
                    certified_manifest,
                )

                legacy_manifest = copy.deepcopy(certified_manifest)
                legacy_manifest["schemaVersion"] = (
                    self.bridge.EA_FACTORY_LEGACY_CERTIFIED_EMA_SMOKE_MANIFEST_SCHEMA
                )
                legacy_manifest["coverageMode"] = (
                    self.bridge.EA_FACTORY_LEGACY_CERTIFIED_EMA_SMOKE_COVERAGE_MODE
                )
                legacy_manifest["checks"].pop("zeroBasedRequestIdentity")
                legacy_manifest.pop("manifestDigest")
                legacy_manifest["manifestDigest"] = (
                    self.bridge._ea_factory_canonical_json_sha256(
                        legacy_manifest
                    )
                )
                self.assertTrue(
                    self.bridge._ea_factory_legacy_certified_ema_smoke_manifest_valid(
                        legacy_manifest,
                        strategy_brief_digest=spec["strategyBriefDigest"],
                        strategy_spec_digest=workspace["strategySpecDigest"],
                        source_digest=source_digest,
                        target_platform="mt5",
                    )
                )
                legacy_build = copy.deepcopy(build)
                legacy_build["blueprintCoverageManifest"] = copy.deepcopy(
                    legacy_manifest
                )
                self.bridge._ea_factory_stage_row(
                    legacy_build,
                    "generate_source",
                )["blueprintCoverageManifest"] = copy.deepcopy(legacy_manifest)
                validated_legacy = self.bridge._ea_factory_revalidated_build(
                    legacy_build
                )
                self.assertTrue(validated_legacy["coverageUpgradeRequired"])
                self.assertEqual(
                    validated_legacy["coverageStatus"],
                    "coverage_upgrade_required",
                )
                self.assertFalse(
                    self.bridge._ea_factory_stage_can_advance(
                        validated_legacy,
                        "source_review",
                    )
                )
                tampered_legacy = copy.deepcopy(legacy_manifest)
                tampered_legacy["checks"]["pendingEntryCorrelation"] = False
                self.assertFalse(
                    self.bridge._ea_factory_legacy_certified_ema_smoke_manifest_valid(
                        tampered_legacy,
                        strategy_brief_digest=spec["strategyBriefDigest"],
                        strategy_spec_digest=workspace["strategySpecDigest"],
                        source_digest=source_digest,
                        target_platform="mt5",
                    )
                )

                mutated_source = source.replace(
                    "MQLInfoInteger(MQL_TESTER) == 0",
                    "MQLInfoInteger(MQL_TESTER) == 1",
                    1,
                )
                self.assertNotEqual(mutated_source, source)
                source_path.write_text(
                    mutated_source,
                    encoding="utf-8",
                    newline="\n",
                )
                version_path.write_text(
                    mutated_source,
                    encoding="utf-8",
                    newline="\n",
                )
                mutated_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
                mutated_build = copy.deepcopy(build)
                mutated_build["versions"][0]["sourceDigest"] = mutated_digest
                mutated_manifest = self.bridge.build_compact_ea_source_manifest(
                    mutated_source,
                    strategy_brief=spec["strategyBrief"],
                    strategy_brief_digest=spec["strategyBriefDigest"],
                    strategy_spec_digest=workspace["strategySpecDigest"],
                    source_digest=mutated_digest,
                    target_platform="mt5",
                )
                self.assertFalse(mutated_manifest["complete"], mutated_manifest)
                self.assertIsNone(
                    self.bridge._ea_factory_custom_ema_certified_coverage_manifest(
                        mutated_manifest,
                        strategy_spec=spec,
                        source_text=mutated_source,
                        build=mutated_build,
                        source_digest=mutated_digest,
                    )
                )
                mutated_build["blueprintCoverageManifest"] = copy.deepcopy(
                    mutated_manifest
                )
                mutated_generation_stage = self.bridge._ea_factory_stage_row(
                    mutated_build,
                    "generate_source",
                )
                mutated_generation_stage["blueprintCoverageManifest"] = copy.deepcopy(
                    mutated_manifest
                )
                mutated_build["artifactManifest"] = [
                    copy.deepcopy(strategy_artifacts[0])
                ]
                mutated_build["artifactManifestDigest"] = (
                    self.bridge._ea_factory_artifact_manifest_digest(
                        mutated_build["artifactManifest"]
                    )
                )
                mutated_source_artifacts = self.bridge._ea_factory_register_artifacts(
                    mutated_build,
                    [
                        {
                            "relativePath": f"Source/{source_path.name}",
                            "stageId": "generate_source",
                            "reportId": generation_report_id,
                            "artifactKind": "generated_source",
                        },
                        {
                            "relativePath": f"EA_Versions/{version_path.name}",
                            "stageId": "generate_source",
                            "reportId": generation_report_id,
                            "artifactKind": "immutable_version",
                        },
                    ],
                )
                mutated_generation_stage["artifacts"] = [
                    row["fileId"] for row in mutated_source_artifacts
                ]
                with self.assertRaisesRegex(
                    self.bridge.DataIntegrityError,
                    "compact Expert Advisor source evidence is invalid",
                ):
                    self.bridge._ea_factory_revalidated_build(mutated_build)

    def test_generation_and_review_recompute_both_apply_profile_gate(self) -> None:
        source = self.canonical_source()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                record = self.bridge._ea_factory_custom_source_record(
                    copy.deepcopy(
                        self.bridge.EA_FACTORY_CUSTOM_EMA_SMOKE_PROFILE_PAYLOAD
                    )
                )
                source = source.replace(
                    "bound-by-test",
                    record["strategyBriefDigest"],
                )
                build_id = "ea-build-custom-ema-integration"
                workspace = self.bridge._ea_factory_create_build_workspace(
                    build_id,
                    record,
                    "mt5",
                    "expert_advisor",
                )
                source = source.replace(
                    "EA_STRATEGY_SPEC_SHA256:" + ("a" * 64),
                    "EA_STRATEGY_SPEC_SHA256:" + workspace["strategySpecDigest"],
                )
                build = {
                    "id": build_id,
                    "platform": "mt5",
                    "artifactKind": "expert_advisor",
                    "sourceRecordId": record["sourceRecordId"],
                    "sourceRecordDigest": record["recordDigest"],
                    "workspace": workspace,
                    "versions": [],
                }
                source_path = (
                    root / "workspace" / "ea-factory" / build_id
                    / "Source" / "CustomEmaSmoke.mq5"
                )
                source_path.write_bytes(source.encode("utf-8"))
                source_digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
                spec = self.bridge.read_json(
                    source_path.parent / "strategy-spec-v01.json",
                    None,
                )

                def manifest_for(digest: str) -> dict:
                    return {
                        "complete": True,
                        "sourceDigest": digest,
                        "strategySpecDigest": workspace["strategySpecDigest"],
                        "strategyBriefDigest": record["strategyBriefDigest"],
                        "targetPlatform": "mt5",
                        "artifactKind": "expert_advisor",
                        "coveredFields": list(
                            self.bridge.RESEARCH_SHEET_DEEP_WRITE_HEADERS
                        ),
                        "missingFields": [],
                        "findings": [],
                    }

                relative_source = source_path.relative_to(root).as_posix()
                report = {
                    "metrics": {
                        "workflowOutput": {
                            "values": {"sourceDigest": source_digest}
                        }
                    }
                }
                with (
                    mock.patch.object(
                        self.bridge,
                        "_verified_ea_factory_source_references",
                        return_value=[relative_source],
                    ),
                    mock.patch.object(
                        self.bridge,
                        "build_compact_ea_source_manifest",
                        return_value=manifest_for(source_digest),
                    ) as analyzer,
                ):
                    generated = (
                        self.bridge._ea_factory_recomputed_generation_coverage_manifest(
                            build,
                            report,
                        )
                    )
                self.assertIsNotNone(generated)
                analyzer.assert_called_once()

                build["versions"] = [{
                    "sourceDigest": source_digest,
                    "immutable": True,
                }]
                source_entry = {
                    "artifactKind": "generated_source",
                    "folder": "Source",
                    "extension": ".mq5",
                    "sha256": source_digest,
                    "fileName": source_path.name,
                }
                with (
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_review_artifact_snapshot_valid",
                        return_value=True,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_review_strategy_spec",
                        return_value=spec,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_revalidated_artifact_manifest",
                        return_value=[source_entry],
                    ),
                    mock.patch.object(
                        self.bridge,
                        "build_compact_ea_source_manifest",
                        return_value=manifest_for(source_digest),
                    ) as analyzer,
                ):
                    reviewed = (
                        self.bridge._ea_factory_recomputed_compact_review_manifest(
                            build
                        )
                    )
                self.assertIsNotNone(reviewed)
                analyzer.assert_called_once()

                unsafe = source.replace(
                    "MQLInfoInteger(MQL_TESTER) == 0",
                    "MQLInfoInteger(MQL_TESTER) == 1",
                )
                source_path.write_bytes(unsafe.encode("utf-8"))
                unsafe_digest = hashlib.sha256(unsafe.encode("utf-8")).hexdigest()
                report["metrics"]["workflowOutput"]["values"][
                    "sourceDigest"
                ] = unsafe_digest
                with (
                    mock.patch.object(
                        self.bridge,
                        "_verified_ea_factory_source_references",
                        return_value=[relative_source],
                    ),
                    mock.patch.object(
                        self.bridge,
                        "build_compact_ea_source_manifest",
                        return_value=manifest_for(unsafe_digest),
                    ),
                ):
                    self.assertIsNone(
                        self.bridge._ea_factory_recomputed_generation_coverage_manifest(
                            build,
                            report,
                        )
                    )

                build["versions"] = [{
                    "sourceDigest": unsafe_digest,
                    "immutable": True,
                }]
                unsafe_entry = {**source_entry, "sha256": unsafe_digest}
                with (
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_review_artifact_snapshot_valid",
                        return_value=True,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_review_strategy_spec",
                        return_value=spec,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_revalidated_artifact_manifest",
                        return_value=[unsafe_entry],
                    ),
                    mock.patch.object(
                        self.bridge,
                        "build_compact_ea_source_manifest",
                        return_value=manifest_for(unsafe_digest),
                    ),
                ):
                    self.assertIsNone(
                        self.bridge._ea_factory_recomputed_compact_review_manifest(
                            build
                        )
                    )


if __name__ == "__main__":
    unittest.main()
