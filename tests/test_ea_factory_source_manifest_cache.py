"""Cache only successful pure analysis, never filesystem or Run authority."""
from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


class EaFactorySourceManifestCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "factory_source_manifest_cache_bridge",
            ROOT / "backend/local-runner/bridge_server.py",
        )
        cls.bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.bridge)

    def setUp(self):
        self.bridge.EA_FACTORY_COMPACT_MANIFEST_CACHE.clear()
        self.arguments = {
            "strategy_brief": {"systemName": "Exact analysis fixture", "entryRules": "Closed bar"},
            "strategy_brief_digest": "a" * 64,
            "strategy_spec_digest": "b" * 64,
            "source_digest": "c" * 64,
            "target_platform": "mt5",
        }
        self.source = "// Exact source text\nvoid OnTick() {}"
        self.success = {"complete": True, "checks": {"bindingValid": True}, "findings": []}

    def analyze(self, source=None, **overrides):
        return self.bridge._ea_factory_compact_source_manifest(
            self.source if source is None else source, **{**self.arguments, **overrides},
        )

    def test_identical_content_reuses_pure_analysis_and_returns_defensive_copies(self):
        with mock.patch.object(self.bridge, "build_compact_ea_source_manifest", return_value=self.success) as analyzer:
            first = self.analyze()
            first["checks"]["bindingValid"] = False
            first["findings"].append("caller edit")
            second = self.analyze()
            second["findings"].append("second edit")
            third = self.analyze()
        analyzer.assert_called_once()
        self.assertTrue(second["checks"]["bindingValid"])
        self.assertEqual(third["findings"], [])
        self.assertIsNot(second, third)
        # Only content hashes are retained, not raw source/brief strings.
        cache_key = next(iter(self.bridge.EA_FACTORY_COMPACT_MANIFEST_CACHE))
        self.assertNotIn(self.source, cache_key)
        self.assertNotIn("Exact analysis fixture", str(cache_key))

    def test_changed_source_brief_each_digest_and_platform_recompute(self):
        changes = [
            {"strategy_brief": {**self.arguments["strategy_brief"], "entryRules": "Different"}},
            {"strategy_brief_digest": "d" * 64},
            {"strategy_spec_digest": "e" * 64},
            {"source_digest": "f" * 64},
            {"target_platform": "mt4"},
        ]
        with mock.patch.object(self.bridge, "build_compact_ea_source_manifest", return_value=self.success) as analyzer:
            self.analyze()
            self.analyze(self.source + "\n// byte changed", source_digest=self.arguments["source_digest"])
            for change in changes:
                self.analyze(**change)
            self.analyze()
        self.assertEqual(analyzer.call_count, 7)

    def test_schema_and_analyzer_identity_are_part_of_cached_contract(self):
        with mock.patch.object(self.bridge, "build_compact_ea_source_manifest", return_value=self.success) as first:
            self.analyze()
            with mock.patch.object(self.bridge, "EA_SOURCE_MANIFEST_SCHEMA_VERSION", "future-schema"):
                self.analyze()
            self.analyze()
        self.assertEqual(first.call_count, 2)
        with mock.patch.object(self.bridge, "build_compact_ea_source_manifest", return_value=self.success) as second:
            self.analyze()
        second.assert_called_once()

    def test_cache_has_bounded_lru_eviction(self):
        with (
            mock.patch.object(self.bridge, "EA_FACTORY_COMPACT_MANIFEST_CACHE_MAX_ENTRIES", 2),
            mock.patch.object(self.bridge, "build_compact_ea_source_manifest", return_value=self.success) as analyzer,
        ):
            self.analyze("first")
            self.analyze("second")
            self.analyze("first")
            self.analyze("third")
            self.assertEqual(len(self.bridge.EA_FACTORY_COMPACT_MANIFEST_CACHE), 2)
            self.analyze("first")
            self.analyze("second")
        self.assertEqual(analyzer.call_count, 4)
        self.assertEqual(len(self.bridge.EA_FACTORY_COMPACT_MANIFEST_CACHE), 2)

    def test_failed_analysis_and_exceptions_are_never_cached(self):
        for outcome in ({"complete": False}, {"complete": 1}, None):
            with self.subTest(outcome=outcome), mock.patch.object(
                self.bridge, "build_compact_ea_source_manifest", return_value=outcome,
            ) as analyzer:
                self.assertEqual(self.analyze(), outcome)
                self.assertEqual(self.analyze(), outcome)
                self.assertEqual(analyzer.call_count, 2)
                self.assertEqual(self.bridge.EA_FACTORY_COMPACT_MANIFEST_CACHE, {})
        with mock.patch.object(self.bridge, "build_compact_ea_source_manifest", side_effect=ValueError("rejected")) as analyzer:
            for _ in range(2):
                with self.assertRaisesRegex(ValueError, "rejected"):
                    self.analyze()
        self.assertEqual(analyzer.call_count, 2)
        self.assertEqual(self.bridge.EA_FACTORY_COMPACT_MANIFEST_CACHE, {})

    def test_oversized_or_non_json_inputs_keep_original_analyzer_semantics(self):
        mutations = [
            ("x" * (256 * 1024 + 1), {}),
            ("ก" * 100000, {}),
            (self.source, {"strategy_brief": {"field": "x" * (128 * 1024 + 1)}}),
            (self.source, {"strategy_brief": {"field": ("tuple",)}}),
            (self.source, {"strategy_brief": {"field": float("nan")}}),
            (self.source, {"strategy_brief": None}),
        ]
        for source, changes in mutations:
            with self.subTest(changes=tuple(changes)), mock.patch.object(
                self.bridge, "build_compact_ea_source_manifest", return_value=self.success,
            ) as analyzer:
                self.analyze(source, **changes)
                self.analyze(source, **changes)
                self.assertEqual(analyzer.call_count, 2)
                self.assertEqual(analyzer.call_args.args[0], source)
                if "strategy_brief" in changes:
                    self.assertIs(analyzer.call_args.kwargs["strategy_brief"], changes["strategy_brief"])
        self.assertEqual(self.bridge.EA_FACTORY_COMPACT_MANIFEST_CACHE, {})

    def test_brief_snapshot_and_caller_results_cannot_mutate_cached_identity(self):
        observed = []
        def analyzer(source, **arguments):
            observed.append(copy.deepcopy(arguments["strategy_brief"]))
            arguments["strategy_brief"]["entryRules"] = "mutation inside analyzer"
            return copy.deepcopy(self.success)
        original = copy.deepcopy(self.arguments["strategy_brief"])
        with mock.patch.object(self.bridge, "build_compact_ea_source_manifest", side_effect=analyzer) as call:
            self.analyze()
            self.analyze()
        call.assert_called_once()
        self.assertEqual(observed, [original])
        self.assertEqual(self.arguments["strategy_brief"], original)

    def test_real_failed_source_analysis_is_unchanged_and_not_promoted_to_proof(self):
        analyzer = self.bridge.build_compact_ea_source_manifest
        expected = analyzer(self.source, **self.arguments)
        self.assertFalse(expected["complete"])
        with mock.patch.object(self.bridge, "build_compact_ea_source_manifest", wraps=analyzer) as call:
            self.assertEqual(self.analyze(), expected)
            self.assertEqual(self.analyze(), expected)
        self.assertEqual(call.call_count, 2)
        self.assertEqual(self.bridge.EA_FACTORY_COMPACT_MANIFEST_CACHE, {})


if __name__ == "__main__":
    unittest.main()
