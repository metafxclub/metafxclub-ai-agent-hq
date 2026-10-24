"""No-tools corrective generation must receive the exact immutable source context."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import test_ea_factory_runner_sandbox as sandbox_support
import test_ea_factory_pending_remove_classification as pending_remove_support


class EaFactorySourceRepairContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = sandbox_support.load_runner()
        cls.brief = cls.runner.normalize_strategy_brief(
            copy.deepcopy(sandbox_support.EaFactoryRunnerSandboxTests.COMPACT_BRIEF)
        )

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.relative = "ea-factory/ea-build-context-fixture/Source"
        self.source = self.root / "workspace" / self.relative
        self.source.mkdir(parents=True)
        self.path = self.source / "strategy-spec-v01.json"
        self.spec = {
            "schemaVersion": "ea-factory-strategy-spec-v3",
            "strategySchemaVersion": self.runner.EA_STRATEGY_BRIEF_SCHEMA_VERSION,
            "buildId": "ea-build-context-fixture",
            "sourceRecordId": "ea-source-context-fixture",
            "recordDigest": "a" * 64,
            "targetPlatform": "mt5",
            "artifactKind": "expert_advisor",
            "immutable": True,
            "strategyBrief": copy.deepcopy(self.brief),
            "strategyBriefDigest": self.runner.compute_strategy_brief_digest(self.brief),
        }
        self.prompt = self.write_spec_and_prompt()
        for name, value in (("PROJECT_ROOT", self.root), ("AUTO_WORKSPACE_ROOT", self.root / "workspace")):
            patch = mock.patch.object(self.runner, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def write_spec_and_prompt(self):
        raw = json.dumps(self.spec, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.path.write_bytes(raw)
        self.spec_digest = hashlib.sha256(raw).hexdigest()
        return (
            "[EA_FACTORY_BUILD_ID:ea-build-context-fixture]"
            f"[EA_FACTORY_SOURCE_RECORD_DIGEST:{'a' * 64}]"
            f"[EA_FACTORY_STRATEGY_SPEC_DIGEST:{self.spec_digest}]"
            "[EA_FACTORY_PLATFORM:mt5] "
            f"Read {self.relative}/strategy-spec-v01.json and generate source."
        )

    def context(self):
        return self.runner._ea_factory_source_semantic_repair_context(self.prompt, self.relative)

    def repair_prompt(self, context):
        return self.runner.build_ea_factory_source_semantic_repair_prompt(
            self.prompt,
            ["ea_ontick_lifecycle_missing_or_ambiguous", "ea_signal_none_sentinel_invalid"],
            validated_strategy_context=context,
        )

    def test_context_contains_complete_exact_brief_and_all_binding_digests(self):
        before = self.path.read_bytes()
        context = self.context()
        self.assertEqual(context["schemaVersion"], "ea-factory-source-repair-input-v1")
        self.assertEqual(context["buildId"], self.spec["buildId"])
        self.assertEqual(context["platform"], "mt5")
        self.assertEqual(context["artifactKind"], "expert_advisor")
        self.assertEqual(context["sourceRecordDigest"], self.spec["recordDigest"])
        self.assertEqual(context["strategySpecDigest"], self.spec_digest)
        self.assertEqual(context["strategyBriefDigest"], self.spec["strategyBriefDigest"])
        self.assertEqual(context["strategyBrief"], self.spec["strategyBrief"])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual([p.name for p in self.source.iterdir()], ["strategy-spec-v01.json"])

    def test_repair_prompt_embeds_full_data_and_keeps_no_tools_and_semantic_rules(self):
        context = self.context()
        prompt = self.repair_prompt(context)
        compact = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
        self.assertIn(compact, prompt)
        self.assertIn(self.runner.EA_FACTORY_EXPERT_ADVISOR_SEMANTIC_RULES, prompt)
        self.assertIn("fileName and content", prompt)
        self.assertIn("No Markdown, explanation, extra fields, tools", prompt)
        self.assertIn("untrusted strategy data", prompt)
        self.assertNotIn("Re-read the same\nimmutable strategy-spec-v01.json", prompt)

    def test_initial_and_corrective_guidance_preserve_pending_stop_guard_sequence(self):
        before = self.path.read_bytes()
        context = self.context()
        initial = self.runner.build_prompt(
            self.prompt, "ea_developer", "mission-guidance", "specialist_balanced", 7000,
            execution_mode="auto_guarded", read_only_work=True,
            result_profile="ea_factory_source_generation", scoped_workspace_write_root=self.source,
            validated_strategy_context=context,
        )
        corrective = self.repair_prompt(context)
        for prompt in (initial, corrective):
            with self.subTest(corrective=prompt is corrective):
                self.assertIn(self.runner.EA_FACTORY_MT5_PENDING_STOP_REMOVE_HELPER, prompt)
                self.assertIn("Only when the immutable MT5 brief requires pending-stop", prompt)
                self.assertIn("TRADE_ACTION_MODIFY remains unsupported", prompt)
                self.assertIn("The caller must stop on false or an ambiguous result", prompt)
                self.assertIn("confirm the old pending ticket is", prompt)
                self.assertIn("Recount live positions PLUS pending", prompt)
                self.assertIn("Never reuse stale sizing/margin/cap results", prompt)
                self.assertIn("exact configured positive Magic input used by the actual", prompt)
                self.assertIn("ForeignMagic, a constant alias, or a shadowing", prompt)
                self.assertIn("do not introduce pending", prompt.lower())
                self.assertIn("Removing one ticket alone does not prove the complete", prompt)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(context["strategyBrief"], self.spec["strategyBrief"])
        self.assertIn("No Markdown, explanation, extra fields, tools", corrective)

    def test_emitted_remove_pattern_matches_real_classifier_and_keeps_other_sends_guarded(self):
        analyzer = pending_remove_support.BRIEF
        pending_remove_support.PendingRemoveClassificationTests.setUpClass()
        control = pending_remove_support.PendingRemoveClassificationTests()
        helper = self.runner.EA_FACTORY_MT5_PENDING_STOP_REMOVE_HELPER
        source = control.combined(helper)
        self.assertTrue(control.analysis(source)["complete"])
        self.assertEqual(control.entry_count(source), 1)
        code = analyzer._indicator_lexical_views(source)[0]
        self.assertEqual(analyzer._mql_trade_side_effect_call_names(code).count("ordersend"), 2)
        self.assertIn("return(cancelResult.retcode == TRADE_RETCODE_DONE);", helper)
        for mutation in (
            helper.replace("TRADE_ACTION_REMOVE", "TRADE_ACTION_MODIFY"),
            helper.replace("if(OrderGetInteger(ORDER_MAGIC) != MagicNumber) return(false);", ""),
            helper.replace("cancelRequest.order = ticket;", "cancelRequest.order = otherTicket;"),
        ):
            with self.subTest(mutation=mutation):
                changed = control.combined(mutation)
                self.assertEqual(control.entry_count(changed), 2)
                self.assertFalse(control.analysis(changed)["complete"])

    def test_changed_spec_bytes_fail_before_any_context_is_returned(self):
        self.path.write_bytes(self.path.read_bytes() + b" ")
        with self.assertRaises(ValueError):
            self.context()

    def test_different_build_platform_digest_or_root_fails_closed(self):
        for replacement in (
            self.prompt.replace("EA_FACTORY_BUILD_ID:ea-build-context-fixture", "EA_FACTORY_BUILD_ID:ea-build-other"),
            self.prompt.replace("EA_FACTORY_PLATFORM:mt5", "EA_FACTORY_PLATFORM:mt4"),
            self.prompt.replace("EA_FACTORY_SOURCE_RECORD_DIGEST:" + "a" * 64, "EA_FACTORY_SOURCE_RECORD_DIGEST:" + "b" * 64),
            self.prompt.replace(self.spec_digest, "c" * 64),
        ):
            with self.subTest(prompt=replacement), self.assertRaises(ValueError):
                self.runner._ea_factory_source_semantic_repair_context(replacement, self.relative)
        with self.assertRaises(ValueError):
            self.runner._ea_factory_source_semantic_repair_context(self.prompt, "ea-factory/ea-build-other/Source")

    def test_rehashed_but_invalid_spec_identity_and_legacy_schema_still_rejected(self):
        original = copy.deepcopy(self.spec)
        for field, value in (
            ("immutable", False), ("buildId", "ea-build-other"),
            ("targetPlatform", "mt4"), ("recordDigest", "b" * 64),
            ("schemaVersion", "ea-factory-strategy-spec-v2"),
        ):
            with self.subTest(field=field):
                self.spec = copy.deepcopy(original)
                self.spec[field] = value
                self.prompt = self.write_spec_and_prompt()
                with self.assertRaises(ValueError):
                    self.context()

    def test_mutated_brief_with_old_digest_is_not_repair_context(self):
        self.spec["strategyBrief"]["moneyManagement"] = "Use fixed lot 9.0 instead of the original rule."
        self.prompt = self.write_spec_and_prompt()
        with self.assertRaises(ValueError):
            self.context()

    def test_builder_rejects_missing_or_cross_attempt_context(self):
        with self.assertRaises(ValueError):
            self.repair_prompt(None)
        original = self.context()
        for field, value in (
            ("buildId", "ea-build-other"), ("platform", "mt4"),
            ("sourceRecordDigest", "b" * 64), ("strategySpecDigest", "b" * 64),
            ("strategyBriefDigest", "c" * 64),
        ):
            context = copy.deepcopy(original)
            context[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.repair_prompt(context)

    def test_lexical_semantic_error_carries_exact_context_without_source_write(self):
        source = (
            '#property strict\n'
            '#property description "EA_STRATEGY_BRIEF_SHA256:' + self.spec["strategyBriefDigest"] + '"\n'
            '#define SIGNAL_NONE 0\nvoid OnTick(int ignored) {}\n'
        )
        with self.assertRaises(self.runner.EAFactorySourceSemanticValidationError) as caught:
            self.runner.preflight_ea_factory_source_semantics(
                json.dumps({"fileName": "Rejected.mq5", "content": source}), self.prompt, self.relative,
            )
        self.assertEqual(caught.exception.validated_strategy_context, self.context())
        self.assertEqual([p.name for p in self.source.iterdir()], ["strategy-spec-v01.json"])

    def test_oversized_context_fails_instead_of_truncating_the_immutable_brief(self):
        original = self.context()
        before = self.path.read_bytes()
        with mock.patch.object(self.runner, "EA_FACTORY_SEMANTIC_REPAIR_CONTEXT_MAX_CHARS", 128):
            with self.assertRaises(ValueError):
                self.context()
            with self.assertRaises(ValueError):
                self.repair_prompt(original)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.context(), original)

    def test_raw_sheet_brief_preserves_original_digest_semantics_and_full_text(self):
        fields = self.runner.EA_STRATEGY_BRIEF_CONTENT_FIELDS
        self.spec["strategyBrief"] = {"schemaVersion": self.runner.EA_STRATEGY_BRIEF_SCHEMA_VERSION,
                                      **{field: self.spec["strategyBrief"][field] for field in fields}}
        # The existing compact Sheet projection retains the upstream digest;
        # the immutable whole-spec SHA binds its exact projected A-J text.
        self.prompt = self.write_spec_and_prompt()
        context = self.context()
        self.assertEqual(context["strategyBrief"], self.spec["strategyBrief"])
        self.assertEqual(context["strategySpecText"].encode("utf-8"), self.path.read_bytes())
        self.assertIn(json.dumps(context, ensure_ascii=False, separators=(",", ":")), self.repair_prompt(context))

    def test_mutated_packet_bytes_or_brief_cannot_be_resealed_under_old_spec_digest(self):
        original = self.context()
        for field, value in (
            ("strategySpecText", original["strategySpecText"] + " "),
            ("strategyBrief", {**original["strategyBrief"], "exitRules": "Changed protection rule."}),
        ):
            context = copy.deepcopy(original)
            context[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.repair_prompt(context)

    def test_raw_sheet_fallback_rejects_malformed_brief_even_with_matching_packet_hashes(self):
        fields = self.runner.EA_STRATEGY_BRIEF_CONTENT_FIELDS
        self.spec["strategyBrief"] = {"schemaVersion": self.runner.EA_STRATEGY_BRIEF_SCHEMA_VERSION,
                                      **{field: self.spec["strategyBrief"][field] for field in fields}}
        self.prompt = self.write_spec_and_prompt()
        original = self.context()
        for mutate in (
            lambda brief: brief.update({"entryRules": ""}),
            lambda brief: brief.update({"entryRules": ["not a compact cell"]}),
            lambda brief: brief.update({"entryRules": "x" * 8001}),
            lambda brief: brief.update({"unexpected": "extra field"}),
            lambda brief: brief.pop("exitRules"),
        ):
            context = copy.deepcopy(original)
            mutate(context["strategyBrief"])
            spec = json.loads(context["strategySpecText"])
            spec["strategyBrief"] = context["strategyBrief"]
            context["strategySpecText"] = json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            context["strategySpecDigest"] = hashlib.sha256(context["strategySpecText"].encode("utf-8")).hexdigest()
            matching_prompt = self.prompt.replace(self.spec_digest, context["strategySpecDigest"])
            with self.assertRaises(ValueError):
                self.runner.build_ea_factory_source_semantic_repair_prompt(
                    matching_prompt, ["ea_signal_none_sentinel_invalid"],
                    validated_strategy_context=context,
                )


if __name__ == "__main__":
    unittest.main()
