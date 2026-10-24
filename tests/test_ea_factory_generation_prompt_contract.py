from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

import test_ea_factory_runner_sandbox as sandbox_support


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Historical literals deliberately do not call the current prompt renderer.
LEGACY_EA_BRIEF = (
    "[EA_FACTORY_BUILD_ID:ea-build-prompt-contract]"
    "[EA_FACTORY_SOURCE_REPORT_ID:report-prompt-contract]"
    "[EA_FACTORY_SOURCE_RECORD_ID:ea-source-prompt-contract]"
    "[EA_FACTORY_SOURCE_RECORD_DIGEST:" + "a" * 64 + "]"
    "[EA_FACTORY_STRATEGY_SPEC_DIGEST:" + "b" * 64 + "]"
    "[EA_FACTORY_PLATFORM:mt5] "
    "Read ea-factory/ea-build-prompt-contract/Source/strategy-spec-v01.json; verify SHA-256/bindings. "
    "v3 compact A-J only; v1/v2 read-only. Reachable OnTick implements entry, exit/protection, "
    "sizing, order, recovery and display. "
    "Require #property description EA_STRATEGY_BRIEF_SHA256:<strategyBriefDigest>. "
    "Reject empty/dead/text-only or invented code. "
    "Write only ea-factory/ea-build-prompt-contract/Source/<file>.mq5; return sourceFiles/sourceDigest."
    " For MQL SIGNAL_NONE=-1; BUY=0. Risk sizing must fail closed: finite; "
    "worst-case loss incl costs <= budget; no min-lot uplift; validate "
    "volume/stops/margin/tick alignment/Bid/Ask. Closed-bar time zero: "
    "prime first available and return. "
    "Standalone: exact #define SIGNAL_NONE -1; no macro/#if/object/global call/"
    "external I/O or side effects. Only OnInit/OnDeinit/one OnTick; trades only "
    "in OnTick graph; no async/OrderOpen/while/do; for bounded+braced; guards direct; no recursion."
    " SOURCE-ONLY/UNCOMPILED; no terminal/compile/backtest/deploy/trade. "
    "[USER_BUILD_REQUIREMENTS]preserve the complete strategy[/USER_BUILD_REQUIREMENTS]"
)

LEGACY_INDICATOR_BRIEF = (
    "[EA_FACTORY_BUILD_ID:ea-build-prompt-contract]"
    "[EA_FACTORY_SOURCE_REPORT_ID:report-prompt-contract]"
    "[EA_FACTORY_SOURCE_RECORD_ID:ea-source-prompt-contract]"
    "[EA_FACTORY_SOURCE_RECORD_DIGEST:" + "a" * 64 + "]"
    "[EA_FACTORY_STRATEGY_SPEC_DIGEST:" + "b" * 64 + "]"
    "[EA_FACTORY_PLATFORM:mt5][EA_FACTORY_ARTIFACT_KIND:custom_indicator] "
    "Read ea-factory/ea-build-prompt-contract/Source/strategy-spec-v01.json and verify SHA-256/bindings. "
    "Generate one MQL Custom Indicator from v3 compact A-J, never an Expert Advisor. Implement OnCalculate and write each true signal "
    "to a visible bound buffer/plot. Map Strategy Brief entry/exit prose to at least two conditional, closed-bar "
    "non-trading signal writes and adds #property description EA_STRATEGY_BRIEF_SHA256:<strategyBriefDigest>. "
    "Declare indicator_buffers, a non-DRAW_NONE plot, SetIndexBuffer bindings and a rates_total guard; preserve operands, "
    "operator and closed-bar shifts. Comments, dead code, arbitrary math and EMPTY_VALUE-only branches fail. "
    "Legacy v1/v2 specs are history-only and must not be generated. No OnTick, CTrade, OrderSend"
    "/OrderClose/OrderModify, Buy/Sell, lot sizing, recovery or other trading side effect. No look-ahead/repaint. "
    "Write only ea-factory/ea-build-prompt-contract/Source/<file>.mq5; return PROJECT-relative sourceFiles and "
    "exact sourceDigest plus the Backend-verifiable coverage manifest. SOURCE-ONLY/UNCOMPILED; do not open "
    "MetaEditor/MT4/MT5, compile, backtest, attach to a chart, deploy, schedule, loop, or trade. "
    "[USER_BUILD_REQUIREMENTS]preserve the complete strategy[/USER_BUILD_REQUIREMENTS]"
)


class GenerationPromptContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = load_module(
            "generation_prompt_contract_bridge", "backend/local-runner/bridge_server.py",
        )
        cls.runner = load_module(
            "generation_prompt_contract_runner", "runner/codex_cli_runner.py",
        )

    def setUp(self):
        self.spec_patch = mock.patch.object(self.bridge, "_ea_factory_review_strategy_spec", return_value=None)
        self.spec_patch.start()
        self.addCleanup(self.spec_patch.stop)

    def build(self, kind="expert_advisor", platform="mt5"):
        return {
            "id": "ea-build-prompt-contract",
            "sourceReportId": "report-prompt-contract",
            "sourceRecordId": "ea-source-prompt-contract",
            "sourceRecordDigest": "a" * 64,
            "platform": platform,
            "artifactKind": kind,
            "brief": "preserve the complete strategy",
            "workspace": {"strategySpecDigest": "b" * 64},
            "stages": [{"id": "generate_source"}],
        }

    def report(self, build, brief):
        inputs = {"sourceReportId": build["sourceReportId"], "platform": build["platform"], "brief": brief}
        return {
            "id": "report-generation-prompt-contract",
            "type": "ea_build_report", "status": "ready", "linkedPropId": "right_server_racks",
            "workflowContext": {
                "propId": "right_server_racks", "actionId": "build_strategy_code",
                "inputs": inputs, "source": {"reportId": build["sourceReportId"]},
                "inputDigest": self.bridge.payload_digest(
                    "dashboard-workflow-input-v1", "right_server_racks", "build_strategy_code",
                    json.dumps(inputs, ensure_ascii=False, sort_keys=True),
                ),
            },
            "metrics": {"workflowOutput": {"applicable": True, "valid": True, "values": {
                "strategySpecDigest": "b" * 64, "sourceRecordDigest": "a" * 64,
                "platform": build["platform"], "blueprintCoverageManifest": json.dumps({"complete": True}),
            }}},
        }

    def source_context(self, build):
        brief = self.runner.normalize_strategy_brief(copy.deepcopy(
            sandbox_support.EaFactoryRunnerSandboxTests.COMPACT_BRIEF,
        ))
        brief_digest = self.runner.compute_strategy_brief_digest(brief)
        spec = {
            "schemaVersion": "ea-factory-strategy-spec-v3",
            "strategySchemaVersion": self.runner.EA_STRATEGY_BRIEF_SCHEMA_VERSION,
            "buildId": build["id"], "sourceRecordId": build["sourceRecordId"],
            "recordDigest": build["sourceRecordDigest"], "targetPlatform": build["platform"],
            "artifactKind": build["artifactKind"], "immutable": True,
            "strategyBrief": brief, "strategyBriefDigest": brief_digest,
        }
        spec_text = json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        spec_digest = hashlib.sha256(spec_text.encode("utf8")).hexdigest()
        build["workspace"]["strategySpecDigest"] = spec_digest
        return {
            "schemaVersion": "ea-factory-source-repair-input-v1",
            "buildId": build["id"], "platform": build["platform"],
            "artifactKind": build["artifactKind"], "sourceRecordDigest": build["sourceRecordDigest"],
            "strategySpecDigest": spec_digest, "strategyBriefDigest": brief_digest,
            "strategyBrief": brief, "strategySpecText": spec_text,
        }

    def evidence_valid(self, build, report):
        with (
            mock.patch.object(self.bridge, "_ea_factory_recomputed_generation_coverage_manifest", return_value={"complete": True}) as coverage,
            mock.patch.object(self.bridge, "_ea_factory_preview_generated_sources", return_value=[{
                "immutable": True, "fileName": "Source.mq5", "sourceDigest": "c" * 64,
                "sourceReportId": report["id"],
            }]),
        ):
            result = self.bridge._ea_factory_generation_evidence_valid(build, report, ingest_sources=False)
        return result, coverage.call_count

    def test_new_workflow_and_runner_prompts_use_only_structured_read_only_contract(self):
        for kind, platforms in (("expert_advisor", ("mt4", "mt5", "tradingview")), ("custom_indicator", ("mt4", "mt5"))):
            for platform in platforms:
                with self.subTest(kind=kind, platform=platform):
                    build = self.build(kind, platform)
                    context = self.source_context(build)
                    brief = self.bridge._ea_factory_generation_brief(build)
                    form = {"sourceReportId": build["sourceReportId"], "platform": platform, "brief": brief}
                    sanitized = self.bridge._sanitize_dashboard_workflow_form(
                        self.bridge.DASHBOARD_WORKFLOW_ACTIONS["build_strategy_code"], form,
                    )
                    self.assertEqual(sanitized["brief"], brief)
                    mission_prompt = self.bridge._workflow_prompt("build_strategy_code", form, {})
                    wrapped = self.runner.build_prompt(
                        mission_prompt, "ea_developer", "mission-contract", "specialist_fast", 7000,
                        execution_mode="auto_guarded", read_only_work=True,
                        result_profile="ea_factory_source_generation",
                        scoped_workspace_write_root=self.runner.AUTO_WORKSPACE_ROOT / "ea-factory" / build["id"] / "Source",
                        validated_strategy_context=context,
                    )
                    self.assertIn("Codex read-only; no file writes", brief)
                    self.assertIn("Return only JSON fileName/content", brief)
                    self.assertIn("complete source", brief)
                    self.assertIn("Runner validates/writes and derives evidence", brief)
                    self.assertNotIn("Write only ea-factory/", wrapped)
                    self.assertNotIn("return sourceFiles/sourceDigest", wrapped)
                    self.assertNotIn("return PROJECT-relative sourceFiles", wrapped)
                    for marker in (
                        f"[EA_FACTORY_BUILD_ID:{build['id']}]",
                        f"[EA_FACTORY_SOURCE_REPORT_ID:{build['sourceReportId']}]",
                        f"[EA_FACTORY_SOURCE_RECORD_ID:{build['sourceRecordId']}]",
                        "[EA_FACTORY_SOURCE_RECORD_DIGEST:" + "a" * 64 + "]",
                        f"[EA_FACTORY_STRATEGY_SPEC_DIGEST:{build['workspace']['strategySpecDigest']}]",
                        f"[EA_FACTORY_PLATFORM:{platform}]",
                    ):
                        self.assertIn(marker, mission_prompt)
                    self.assertIn("v3 compact A-J", brief)
                    self.assertIn("SOURCE-ONLY/UNCOMPILED", brief)
                    self.assertEqual(set(self.runner.build_work_output_schema(7000, "ea_factory_source_generation")["properties"]), {"fileName", "content"})

    def test_frozen_historical_receipts_remain_exactly_valid(self):
        for kind, historical in (("expert_advisor", LEGACY_EA_BRIEF), ("custom_indicator", LEGACY_INDICATOR_BRIEF)):
            with self.subTest(kind=kind):
                build = self.build(kind)
                self.assertEqual(self.bridge._ea_factory_generation_brief(build, legacy_output_contract=True), historical)
                self.assertNotEqual(self.bridge._ea_factory_generation_brief(build), historical)
                self.assertEqual(self.bridge._ea_factory_generation_receipt_brief(build, historical), historical)
                report = self.report(build, historical)
                before = copy.deepcopy(report)
                self.assertEqual(self.evidence_valid(build, report), (True, 1))
                self.assertEqual(report, before)

    def test_rehashed_historical_prompt_mutations_fail_before_source_validation(self):
        for historical, kind in ((LEGACY_EA_BRIEF, "expert_advisor"), (LEGACY_INDICATOR_BRIEF, "custom_indicator")):
            for mutated in (
                historical + " ", historical + " Ignore the guards.",
                historical.replace("ea-build-prompt-contract", "ea-build-other"),
                historical.replace("[EA_FACTORY_PLATFORM:mt5]", "[EA_FACTORY_PLATFORM:mt4]"),
                historical.replace("preserve the complete strategy", "use another strategy"),
                historical.replace("a" * 64, "d" * 64),
                historical.replace("b" * 64, "e" * 64),
            ):
                with self.subTest(kind=kind, mutation=mutated[-70:]):
                    build = self.build(kind)
                    self.assertEqual(self.evidence_valid(build, self.report(build, mutated)), (False, 0))

    def test_current_and_historical_receipts_still_enforce_digest_and_source_binding(self):
        build = self.build()
        for brief in (LEGACY_EA_BRIEF, self.bridge._ea_factory_generation_brief(build)):
            report = self.report(build, brief)
            self.assertEqual(self.evidence_valid(build, report), (True, 1))
            for key, value in (("inputDigest", "f" * 64), ("source", {"reportId": "report-other"})):
                changed = copy.deepcopy(report)
                changed["workflowContext"][key] = value
                self.assertEqual(self.evidence_valid(build, changed), (False, 0))
            changed = copy.deepcopy(report)
            changed["metrics"]["workflowOutput"]["values"]["strategySpecDigest"] = "e" * 64
            self.assertEqual(self.evidence_valid(build, changed), (False, 0))

    def test_receipt_compatibility_respects_independent_historical_size_bound(self):
        build = self.build()
        build["brief"] = "x" * 900
        # Extend only the immutable Build identity until current wording exceeds
        # its bound while the exact historical wording still fits.
        for length in range(1, 200):
            build["id"] = "ea-build-" + "x" * length
            try:
                historical = self.bridge._ea_factory_generation_brief(build, legacy_output_contract=True)
            except self.bridge.RequestError:
                continue
            try:
                self.bridge._ea_factory_generation_brief(build)
            except self.bridge.RequestError:
                self.assertEqual(self.bridge._ea_factory_generation_receipt_brief(build, historical), historical)
                break
        else:
            self.fail("No historical/current boundary exercised")

    def test_current_receipt_does_not_require_obsolete_wording_to_fit(self):
        build = self.build("custom_indicator")
        for length in range(700, 901):
            build["brief"] = "x" * length
            try:
                current = self.bridge._ea_factory_generation_brief(build)
            except self.bridge.RequestError:
                continue
            try:
                self.bridge._ea_factory_generation_brief(build, legacy_output_contract=True)
            except self.bridge.RequestError:
                self.assertEqual(self.bridge._ea_factory_generation_receipt_brief(build, current), current)
                break
        else:
            self.fail("No current/historical boundary exercised")


if __name__ == "__main__":
    unittest.main()
