from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_ea_factory_followup_hardening",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EaFactoryFollowupHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def valid_values(self) -> dict:
        return {
            "record_id": "followup-system-001",
            "system_name": "Follow-up Verified System",
            "strategy_family": "trend_following",
            "symbols_market": "EURUSD / Forex",
            "timeframe": "H1",
            "entry_rules": "Enter only after a confirmed trend signal",
            "exit_rules": "Exit only after the opposite confirmed signal",
            "stop_loss": "fixed 100 points",
            "take_profit": "fixed 200 points",
            "recovery": "none",
            "lot_risk": "1 percent fixed fractional",
            "indicators": "EMA 20 and EMA 50",
            "special_conditions": "one position at a time",
            "source_urls": "https://example.org/followup-system",
            "verification_status": "verified",
            "backtest_status": "not_run",
            "backtest_report": "",
            "optimization_status": "not_run",
            "optimization_report": "",
            "issues": "none",
            "next_action": "build",
            "target_platform": "mt4",
            "updated_at": "2026-08-24T09:00:00+07:00",
        }

    def writer_ready_status(self) -> dict:
        return {
            "status": "ready",
            "stale": False,
            "refreshInProgress": False,
            "eaFactorySourceWriter": {
                "version": self.bridge.EA_FACTORY_STRUCTURED_SOURCE_WRITER_VERSION,
                "resultProfile": self.bridge.EA_FACTORY_SOURCE_RESULT_PROFILE,
                "codexSandbox": "read-only",
                "atomicWriter": True,
                "outputFields": list(
                    self.bridge.EA_FACTORY_STRUCTURED_SOURCE_OUTPUT_FIELDS
                ),
                "evidenceKinds": list(
                    self.bridge.EA_FACTORY_STRUCTURED_SOURCE_EVIDENCE_KINDS
                ),
            },
        }

    def normalized_record(self, *, source_key: str = "sheet-followup") -> dict:
        record = self.bridge._ea_factory_normalize_record(
            self.valid_values(),
            source_kind="google_sheet_public_csv",
            source_key=source_key,
            source_report_id="report-source-followup",
            source_mission_id="mission-source-followup",
        )
        self.assertIsInstance(record, dict)
        self.assertTrue(record["buildReady"])
        return record

    def empty_state(self) -> dict:
        return {
            "schemaVersion": self.bridge.EA_FACTORY_STATE_SCHEMA_VERSION,
            "sourceSnapshots": [],
            "builds": [],
            "createReservations": [],
            "updatedAt": None,
        }

    def workspace_stub(self, build_id: str) -> dict:
        return {
            "storageScope": "repo_managed_workspace",
            "workspaceId": f"ea-workspace-{build_id}",
            "folderNames": list(self.bridge.EA_FACTORY_BUILD_FOLDER_NAMES),
            "strategySpecFile": "Source/strategy-spec-v01.json",
            "strategySpecDigest": "d" * 64,
            "rawFilesystemPathExposed": False,
        }

    @staticmethod
    def strategy_stage_entities() -> tuple[dict, dict]:
        mission = {
            "id": "mission-followup-strategy-spec",
            "status": "completed",
        }
        report = {
            "id": "report-followup-strategy-spec",
            "status": "ready",
        }
        return mission, report

    def factory_generation_fixture(self, build_id: str = "ea-build-false-approval") -> tuple[dict, dict, str, dict]:
        stages = self.bridge._ea_factory_initial_stages(
            "mt4",
            {"id": "mission-false-approval-spec"},
            {"id": "report-false-approval-spec"},
        )
        build = {
            "id": build_id,
            "platform": "mt4",
            "sourceRecordId": "ea-source-false-approval",
            "sourceRecordDigest": "a" * 64,
            "sourceReportId": "report-false-approval-spec",
            "brief": "TEST BUILD ONLY - ห้าม Deploy และห้ามเทรดจริง",
            "workspace": self.workspace_stub(build_id),
            "status": "ready",
            "stages": stages,
        }
        stage = self.bridge._ea_factory_stage_row(build, "generate_source")
        stage.update({
            "requestIdempotencyKey": "false-approval-browser-key",
            "requestDigest": self.bridge._ea_factory_advance_request_digest(
                build,
                "generate_source",
            ),
            "startedAt": "2026-08-24T03:00:00+00:00",
            "missionIdempotencyKey": self.bridge._ea_factory_stage_mission_idempotency_key(
                build_id,
                "generate_source",
                "false-approval-browser-key",
            ),
        })
        brief = self.bridge._ea_factory_generation_brief(build)
        transfer = {
            "mode": self.bridge.DASHBOARD_WORKFLOW_TRANSFER_MODE,
            "sourceReportId": build["sourceReportId"],
            "sourcePropId": "left_server_racks",
            "sourceMissionId": "mission-source-false-approval",
            "transferAgentId": "ea_developer",
            "sourceOwnerAgentId": "mission_archivist",
            "targetPropId": "right_server_racks",
            "handoffMissionId": "mission-handoff-false-approval",
            "status": "recorded",
        }
        source = {
            "reportId": build["sourceReportId"],
            "sourceKind": "report",
            "sourcePropId": "left_server_racks",
            "sourceMissionId": transfer["sourceMissionId"],
            "transferAgentId": transfer["transferAgentId"],
            "type": "trading_system_research_report",
            "status": "ready",
            "agentTransfer": transfer,
        }
        form = {
            "sourceReportId": build["sourceReportId"],
            "platform": "mt4",
            "brief": brief,
        }
        profile = self.bridge._trusted_workflow_plugin_profile(
            "right_server_racks",
            "build_strategy_code",
            form,
        )
        lineage = self.bridge._dashboard_workflow_lineage(
            "right_server_racks",
            "build_strategy_code",
            form,
            source,
            trigger_source="backend",
            plugin_profile=profile,
        )
        return build, stage, brief, lineage

    def legacy_false_approval_mission(
        self,
        build: dict,
        stage: dict,
        brief: str,
        lineage: dict,
    ) -> dict:
        budget = {
            "tokenBudget": 12000,
            "timeoutSeconds": 120,
            "outputLimitChars": 7000,
            "rateReservePercent": 15,
        }
        profile = self.bridge._trusted_workflow_plugin_profile(
            "right_server_racks",
            "build_strategy_code",
            lineage["inputs"],
        )
        detail = self.bridge._workflow_prompt(
            "build_strategy_code",
            lineage["inputs"],
            lineage.get("source"),
            profile,
        )
        mission = {
            "id": "mission-false-approval",
            "title": "Factory source",
            "detail": detail,
            "owner": "ea_developer",
            "requester": "human",
            "parentMissionId": None,
            "subtaskIds": [],
            "toolId": "codex_cli_task",
            "targetId": "right_server_racks",
            "status": "waiting_approval",
            "risk": "high",
            "modelTier": "specialist_balanced",
            "reportType": "ea_build_report",
            "idempotencyKey": stage["missionIdempotencyKey"],
            "budget": budget,
            "workflowContext": lineage,
            "approval": {
                "required": True,
                "id": "approval-false-positive",
                "state": "pending",
                "gateMode": "human_review",
                "requiredActors": self.bridge.required_approval_actors("high"),
                "decisions": [],
                "expiresAt": self.bridge.utc_after(60),
                "consumedAt": None,
                "payloadDigest": None,
            },
            "requiresHumanApproval": True,
            "executionMode": "manual_guarded",
            "autoEligible": False,
            "attemptCount": 0,
            "result": "",
            "artifactPath": None,
            "reportIds": [],
            "createdAt": "2026-08-24T03:00:00+00:00",
            "updatedAt": "2026-08-24T03:00:00+00:00",
            "completedAt": None,
        }
        mission["idempotencyScopeDigest"] = (
            self.bridge._mission_request_scope_digest(
                mission["requester"],
                mission["toolId"],
                mission["owner"],
                mission["detail"],
                mission["targetId"],
                "high",
                mission["modelTier"],
                mission["budget"],
                mission["reportType"],
                None,
            )
        )
        mission["approval"]["payloadDigest"] = self.bridge.mission_payload_digest(
            mission
        )
        return mission

    def factory_review_fixture(
        self,
        build_id: str = "ea-build-worker-review",
    ) -> tuple[dict, str, dict]:
        build, _stage, _brief, _lineage = self.factory_generation_fixture(
            build_id
        )
        generation_stage = self.bridge._ea_factory_stage_row(
            build,
            "generate_source",
        )
        generation_stage.update({
            "status": "completed",
            "missionId": "mission-worker-generation",
            "reportId": "report-worker-generation",
            "evidenceVerified": True,
        })
        build["versions"] = [{
            "versionId": "v01",
            "sourceDigest": "e" * 64,
        }]
        brief = self.bridge._ea_factory_review_brief(build)
        transfer = {
            "mode": self.bridge.DASHBOARD_WORKFLOW_TRANSFER_MODE,
            "sourceReportId": "report-worker-generation",
            "sourcePropId": "right_server_racks",
            "sourceMissionId": "mission-worker-generation",
            "transferAgentId": "ea_developer",
            "sourceOwnerAgentId": "ea_developer",
            "targetPropId": "right_server_racks",
            "handoffMissionId": "mission-worker-review-handoff",
            "status": "recorded",
        }
        source = {
            "reportId": "report-worker-generation",
            "sourceKind": "report",
            "sourcePropId": "right_server_racks",
            "sourceMissionId": "mission-worker-generation",
            "transferAgentId": transfer["transferAgentId"],
            "type": "ea_build_report",
            "status": "ready",
            "agentTransfer": transfer,
        }
        form = {
            "sourceReportId": source["reportId"],
            "platform": "mt4",
            "brief": brief,
        }
        profile = self.bridge._trusted_workflow_plugin_profile(
            "right_server_racks",
            "review_source_code",
            form,
        )
        lineage = self.bridge._dashboard_workflow_lineage(
            "right_server_racks",
            "review_source_code",
            form,
            source,
            trigger_source="backend",
            plugin_profile=profile,
        )
        return build, brief, lineage

    @staticmethod
    def strict_mql_review_requirements() -> str:
        return (
            "MT4 D1 breakout volume 1.45; separate BUY/SELL signal counters; "
            "Risk<=1%, SL7.5%, TP22.5%; normalized-lot recheck zero tolerance; "
            "finite stop/freeze/Point; reset/reject margin errors; reject missing prior volume; "
            "disclose gap/proxy limits; trading default false"
        )

    @staticmethod
    def compliant_strict_mql_source() -> str:
        return """#property strict
#property description "CANSLIM proxy limitations apply; market gaps may exceed the risk budget and loss cap."
input double InpBreakoutVolumeMultiplier = 1.45;
input double InpStopLossPercent = 7.5;
input double InpTakeProfitPercent = 22.5;
input bool InpAllowTrading = false;
long g_buySignalCount = 0;
long g_sellSignalCount = 0;
bool IsFinite(double value) { return(value == value); }
bool ValidateInputs()
{
   if(!IsFinite(InpBreakoutVolumeMultiplier) || InpBreakoutVolumeMultiplier != 1.45) return(false);
   if(!IsFinite(InpStopLossPercent) || InpStopLossPercent != 7.5) return(false);
   if(!IsFinite(InpTakeProfitPercent) || InpTakeProfitPercent != 22.5) return(false);
   return(true);
}
bool PriorVolumeReady()
{
   double priorVolume = (double)iVolume(Symbol(), PERIOD_D1, 1);
   if(!IsFinite(priorVolume) || priorVolume <= 0.0) return(false);
   double volumeSum = 0.0;
   volumeSum += priorVolume;
   return(volumeSum > 0.0);
}
void OnTick()
{
   int buySignal = 0;
   int sellSignal = 1;
   if(buySignal == 0) g_buySignalCount++;
   if(sellSignal == 1) g_sellSignalCount++;
   if(!InpAllowTrading) return;
   double stopLevel = (double)MarketInfo(Symbol(), MODE_STOPLEVEL);
   double freezeLevel = (double)MarketInfo(Symbol(), MODE_FREEZELEVEL);
   if(!IsFinite(Point) || Point <= 0.0 || !IsFinite(stopLevel) || stopLevel < 0.0 ||
      !IsFinite(freezeLevel) || freezeLevel < 0.0) return;
   double recheckedWorstLoss = 10.0;
   double riskBudget = 10.0;
   if(!IsFinite(recheckedWorstLoss) || recheckedWorstLoss > riskBudget) return;
   ResetLastError();
   double remainingMargin = AccountFreeMarginCheck(Symbol(), OP_BUY, 0.01);
   int marginError = GetLastError();
   if(marginError != 0 || !IsFinite(remainingMargin)) return;
}
"""

    def test_strict_mql_static_review_accepts_only_canonical_safe_source(self) -> None:
        findings = self.bridge._ea_factory_mql_static_review_findings_for_text(
            self.compliant_strict_mql_source(),
            self.strict_mql_review_requirements(),
        )
        self.assertEqual(findings, [])

    def test_strict_mql_static_review_blocks_each_live_v6_violation(self) -> None:
        baseline = self.compliant_strict_mql_source()
        mutations = (
            (
                "exact_volume_multiplier_not_enforced",
                baseline.replace(
                    "InpBreakoutVolumeMultiplier != 1.45",
                    "InpBreakoutVolumeMultiplier < 1.45 || InpBreakoutVolumeMultiplier > 10.0",
                ),
            ),
            (
                "exact_stop_loss_not_enforced",
                baseline.replace(
                    "InpStopLossPercent != 7.5",
                    "InpStopLossPercent <= 0.0 || InpStopLossPercent > 50.0",
                ),
            ),
            (
                "exact_take_profit_not_enforced",
                baseline.replace(
                    "InpTakeProfitPercent != 22.5",
                    "InpTakeProfitPercent <= 0.0 || InpTakeProfitPercent > 200.0",
                ),
            ),
            (
                "zero_tolerance_risk_recheck_missing",
                baseline.replace(
                    "recheckedWorstLoss > riskBudget",
                    "recheckedWorstLoss > riskBudget + 0.00000001",
                ),
            ),
            (
                "buy_signal_counter_missing",
                baseline.replace("if(buySignal == 0) g_buySignalCount++;", ""),
            ),
            (
                "sell_signal_counter_missing",
                baseline.replace("if(sellSignal == 1) g_sellSignalCount++;", ""),
            ),
            (
                "margin_error_reset_not_immediate",
                baseline.replace(
                    "ResetLastError();\n   double remainingMargin",
                    "ResetLastError();\n   double stalePrice = Bid;\n   double remainingMargin",
                ),
            ),
            (
                "gap_risk_disclosure_missing",
                baseline.replace(
                    '#property description "CANSLIM proxy limitations apply; market gaps may exceed the risk budget and loss cap."',
                    '#property description "CANSLIM proxy limitations apply."\n'
                    '// gap risk may exceed budget\nstring spoof = "gap risk may exceed budget";',
                ),
            ),
            (
                "stop_level_finite_nonnegative_guard_missing",
                baseline.replace("!IsFinite(stopLevel) || stopLevel < 0.0 ||", "stopLevel < 0.0 ||"),
            ),
            (
                "freeze_level_finite_nonnegative_guard_missing",
                baseline.replace("!IsFinite(freezeLevel) || freezeLevel < 0.0", "freezeLevel < 0.0"),
            ),
            (
                "point_finite_positive_guard_missing",
                baseline.replace("!IsFinite(Point) || Point <= 0.0 ||", "Point <= 0.0 ||"),
            ),
            (
                "zero_volume_not_rejected",
                baseline.replace("priorVolume <= 0.0", "priorVolume < 0.0"),
            ),
        )
        for expected_finding, source in mutations:
            with self.subTest(expected_finding=expected_finding):
                findings = self.bridge._ea_factory_mql_static_review_findings_for_text(
                    source,
                    self.strict_mql_review_requirements(),
                )
                self.assertIn(expected_finding, findings)

    def test_market_level_usage_activates_guards_without_literal_freeze_brief(self) -> None:
        requirements = "finite tick/lot, tick-aligned live-Bid stops"
        unguarded = self.compliant_strict_mql_source().replace(
            "!IsFinite(Point) || Point <= 0.0 || !IsFinite(stopLevel) || stopLevel < 0.0 ||\n"
            "      !IsFinite(freezeLevel) || freezeLevel < 0.0",
            "Point <= 0.0 || stopLevel < 0.0 || freezeLevel < 0.0",
        )
        findings = self.bridge._ea_factory_mql_static_review_findings_for_text(
            unguarded,
            requirements,
        )
        self.assertIn("stop_level_finite_nonnegative_guard_missing", findings)
        self.assertIn("freeze_level_finite_nonnegative_guard_missing", findings)
        self.assertIn("point_finite_positive_guard_missing", findings)

        guarded_alias = self.compliant_strict_mql_source().replace(
            "if(!IsFinite(Point) || Point <= 0.0 || !IsFinite(stopLevel)",
            "double pointSize = Point;\n"
            "   if(!IsFinite(pointSize) || pointSize <= 0.0 || !IsFinite(stopLevel)",
        )
        alias_findings = self.bridge._ea_factory_mql_static_review_findings_for_text(
            guarded_alias,
            requirements,
        )
        self.assertNotIn("stop_level_finite_nonnegative_guard_missing", alias_findings)
        self.assertNotIn("freeze_level_finite_nonnegative_guard_missing", alias_findings)
        self.assertNotIn("point_finite_positive_guard_missing", alias_findings)

    def test_deterministic_static_finding_overrides_forged_review_pass(self) -> None:
        build, _brief, _lineage = self.factory_review_fixture(
            "ea-build-static-review-block",
        )
        with mock.patch.object(
            self.bridge,
            "_ea_factory_review_artifact_snapshot_valid",
            return_value=True,
        ):
            self.assertFalse(
                self.bridge._ea_factory_review_evidence_valid(
                    build,
                    {"id": "report-forged-review-pass"},
                    static_findings=["zero_tolerance_risk_recheck_missing"],
                )
            )

    def test_static_review_reads_only_manifest_bound_source_and_immutable_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_id = "ea-build-static-manifest-pair"
            build_dir = root / "workspace" / "ea-factory" / build_id
            source_dir = build_dir / "Source"
            version_dir = build_dir / "EA_Versions"
            source_dir.mkdir(parents=True)
            version_dir.mkdir(parents=True)
            source_path = source_dir / "StrictEA.mq4"
            version_path = version_dir / "StrictEA_v01.mq4"
            build = {
                "id": build_id,
                "platform": "mt4",
                "brief": self.strict_mql_review_requirements(),
            }

            def bind(payload: str) -> None:
                source_path.write_text(payload, encoding="utf-8")
                version_path.write_text(payload, encoding="utf-8")
                manifest = [
                    self.bridge._ea_factory_artifact_descriptor(
                        build_id,
                        "Source/StrictEA.mq4",
                        stage_id="generate_source",
                        report_id="report-static-generation",
                        artifact_kind="generated_source",
                    ),
                    self.bridge._ea_factory_artifact_descriptor(
                        build_id,
                        "EA_Versions/StrictEA_v01.mq4",
                        stage_id="generate_source",
                        report_id="report-static-generation",
                        artifact_kind="immutable_version",
                    ),
                ]
                self.assertTrue(all(isinstance(item, dict) for item in manifest))
                manifest.sort(key=lambda item: (item["folder"], item["fileName"]))
                build["artifactManifest"] = manifest
                build["artifactManifestDigest"] = (
                    self.bridge._ea_factory_artifact_manifest_digest(manifest)
                )

            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                bind(self.compliant_strict_mql_source())
                self.assertEqual(
                    self.bridge._ea_factory_mql_static_review_findings(build),
                    [],
                )
                bind(
                    self.compliant_strict_mql_source().replace(
                        "recheckedWorstLoss > riskBudget",
                        "recheckedWorstLoss > riskBudget + 1e-8",
                    )
                )
                self.assertIn(
                    "zero_tolerance_risk_recheck_missing",
                    self.bridge._ea_factory_mql_static_review_findings(build),
                )

    def test_reconcile_revokes_legacy_review_evidence_when_static_source_fails(self) -> None:
        build, _brief, _lineage = self.factory_review_fixture(
            "ea-build-revoke-old-review-pass",
        )
        stage = self.bridge._ea_factory_stage_row(build, "source_review")
        stage.update({
            "status": "completed",
            "missionId": "mission-old-review-pass",
            "reportId": "report-old-review-pass",
            "evidenceVerified": True,
        })
        mission = {
            "id": "mission-old-review-pass",
            "status": "completed",
            "reportIds": ["report-old-review-pass"],
            "updatedAt": "2026-08-24T05:00:00+00:00",
        }
        report = {
            "id": "report-old-review-pass",
            "status": "ready",
            "linkedMissionId": mission["id"],
        }
        with mock.patch.object(
            self.bridge,
            "_ea_factory_mql_static_review_findings",
            return_value=["zero_tolerance_risk_recheck_missing"],
        ):
            changed = self.bridge._ea_factory_sync_build_status(
                build,
                missions=[mission],
                reports=[report],
                ingest_sources=False,
            )
        self.assertTrue(changed)
        self.assertEqual(stage["status"], "blocked")
        self.assertEqual(stage["blockedReasonCode"], "review_findings_require_new_version")
        self.assertFalse(stage["evidenceVerified"])
        self.assertEqual(build["status"], "attention_required")

    def test_source_review_receives_bounded_non_truncating_budget_and_exact_user_scope(self) -> None:
        build, brief, _lineage = self.factory_review_fixture(
            "ea-build-review-envelope",
        )
        self.assertIn("[USER_BUILD_REQUIREMENTS]", brief)
        self.assertIn(build["brief"], brief)
        self.assertIn("do not run a shell/hash command", brief)
        self.assertIn("compileStatus must be exactly source_only", brief)
        self.assertIn("unmodeled slippage/spread", brief)
        self.assertIn("stale first bar", brief)
        self.assertNotIn("open terminals", brief)
        self.assertLessEqual(len(brief), 2400)

        settings = self.bridge._default_dashboard_workflow_settings()
        settings["agentPreferences"].update({
            "outputLimitChars": 7000,
            "timeoutSeconds": 120,
        })
        preferences = self.bridge._dashboard_workflow_execution_preferences(
            "review_source_code",
            settings,
        )
        self.assertEqual(preferences["outputLimitChars"], 12000)
        self.assertEqual(preferences["timeoutSeconds"], 180)

    def test_source_review_preserves_maximum_accepted_build_brief(self) -> None:
        build, _brief, _lineage = self.factory_review_fixture(
            "ea-build-review-max-brief",
        )
        requirements = ("strict fixed risk closed bar evidence " * 30)[:900].strip()
        build["brief"] = requirements

        review_brief = self.bridge._ea_factory_review_brief(build)

        self.assertLessEqual(len(review_brief), 2400)
        self.assertIn(
            f"[USER_BUILD_REQUIREMENTS]{requirements}[/USER_BUILD_REQUIREMENTS]",
            review_brief,
        )
        self.assertIn("Trusted Backend rehashes", review_brief)
        self.assertIn("compileStatus must be exactly source_only", review_brief)

    def create_factory_worker_mission(
        self,
        action_id: str,
        brief: str,
        lineage: dict,
        idempotency_key: str,
    ) -> dict:
        self.assertEqual(lineage["inputs"]["brief"], brief)
        profile = self.bridge._trusted_workflow_plugin_profile(
            "right_server_racks",
            action_id,
            lineage["inputs"],
        )
        prompt = self.bridge._workflow_prompt(
            action_id,
            lineage["inputs"],
            lineage.get("source"),
            profile,
        )
        return self.bridge.create_mission({
            "prompt": prompt,
            "agentId": "ea_developer",
            "requester": "human",
            "toolId": "codex_cli_task",
            "targetId": "right_server_racks",
            "risk": "low",
            "modelTier": "specialist_balanced",
            "reportType": "ea_build_report",
            "budget": {
                "tokenBudget": 12000,
                "timeoutSeconds": 120,
                "outputLimitChars": 7000,
                "rateReservePercent": 15,
            },
            "idempotencyKey": idempotency_key,
        }, status="queued", allow_model_override=True, allow_budget_override=True, workflow_context=lineage)

    def legacy_writer_failure_fixture(
        self,
        build_id: str = "ea-build-legacy-writer",
    ) -> tuple[dict, dict, dict, dict]:
        build, stage, _brief, _lineage = self.factory_generation_fixture(
            build_id
        )
        build_dir = self.bridge._ea_factory_build_root() / build_id
        for folder_name in self.bridge.EA_FACTORY_BUILD_FOLDER_NAMES:
            (build_dir / folder_name).mkdir(parents=True, exist_ok=True)
        spec_path = build_dir / "Source" / "strategy-spec-v01.json"
        spec_path.write_text(
            json.dumps({"fixture": build_id}, sort_keys=True),
            encoding="utf-8",
        )
        spec_digest = self.bridge._ea_factory_file_sha256(spec_path)
        build["workspace"] = {
            **self.workspace_stub(build_id),
            "strategySpecDigest": spec_digest,
        }
        strategy_artifact = self.bridge._ea_factory_artifact_descriptor(
            build_id,
            "Source/strategy-spec-v01.json",
            stage_id="strategy_spec",
            report_id=build["sourceReportId"],
            artifact_kind="strategy_spec",
        )
        self.assertIsInstance(strategy_artifact, dict)
        build["artifactManifest"] = [strategy_artifact]
        build["artifactManifestDigest"] = (
            self.bridge._ea_factory_artifact_manifest_digest(
                build["artifactManifest"]
            )
        )
        build["versions"] = []
        self.bridge._ea_factory_stage_row(build, "strategy_spec")[
            "artifacts"
        ] = [strategy_artifact["fileId"]]

        brief = self.bridge._ea_factory_generation_brief(build)
        transfer = {
            "mode": self.bridge.DASHBOARD_WORKFLOW_TRANSFER_MODE,
            "sourceReportId": build["sourceReportId"],
            "sourcePropId": "left_server_racks",
            "sourceMissionId": "mission-source-legacy-writer",
            "transferAgentId": "ea_developer",
            "sourceOwnerAgentId": "mission_archivist",
            "targetPropId": "right_server_racks",
            "handoffMissionId": "mission-handoff-legacy-writer",
            "status": "recorded",
        }
        source = {
            "reportId": build["sourceReportId"],
            "sourceKind": "report",
            "sourcePropId": "left_server_racks",
            "sourceMissionId": transfer["sourceMissionId"],
            "transferAgentId": transfer["transferAgentId"],
            "type": "trading_system_research_report",
            "status": "ready",
            "agentTransfer": transfer,
        }
        form = {
            "sourceReportId": build["sourceReportId"],
            "platform": build["platform"],
            "brief": brief,
        }
        profile = self.bridge._trusted_workflow_plugin_profile(
            "right_server_racks",
            "build_strategy_code",
            form,
        )
        lineage = self.bridge._dashboard_workflow_lineage(
            "right_server_racks",
            "build_strategy_code",
            form,
            source,
            trigger_source="backend",
            plugin_profile=profile,
        )
        mission = self.create_factory_worker_mission(
            "build_strategy_code",
            brief,
            lineage,
            stage["missionIdempotencyKey"],
        )
        mission_id = mission["id"]
        report_id = "auto-report-legacy-writer"
        artifact_reference = (
            "data/runtime/codex-runs/run-legacy-writer.final.md"
        )
        receipt = {
            "applicable": True,
            "valid": False,
            "failureCode": None,
            "procedureId": profile["pluginSkillId"],
            "expectedFields": list(
                self.bridge.EA_FACTORY_STRUCTURED_SOURCE_OUTPUT_FIELDS
            ),
            "providedFields": [
                "sourceRecordDigest",
                "strategySpecDigest",
                "platform",
            ],
            "missingFields": ["sourceFiles", "sourceDigest"],
            "values": {
                "sourceRecordDigest": build["sourceRecordDigest"],
                "strategySpecDigest": spec_digest,
                "platform": build["platform"],
            },
            "expectedEvidenceKinds": list(
                self.bridge.EA_FACTORY_STRUCTURED_SOURCE_EVIDENCE_KINDS
            ),
            "providedEvidenceKinds": [],
            "missingEvidenceKinds": list(
                self.bridge.EA_FACTORY_STRUCTURED_SOURCE_EVIDENCE_KINDS
            ),
        }
        old_execution = copy.deepcopy(mission["execution"])
        old_execution.update({
            "dispatchState": "blocked",
            "workerId": "mission-worker-legacy-writer",
            "leaseId": "lease-legacy-writer",
            "startedAt": "2026-08-24T01:53:43+07:00",
            "heartbeatAt": "2026-08-24T01:54:11+07:00",
            "completedAt": "2026-08-24T01:54:11+07:00",
            "processStarted": True,
            "processTreeTerminated": False,
            "authorizationConsumedAt": "2026-08-24T01:53:43+07:00",
            "authorizationConsumedLeaseId": "lease-legacy-writer",
            "workingDirectory": f"workspace/ea-factory/{build_id}/Source",
            "writeRoots": [],
            "controlPlaneWritable": False,
            "webSearchEnabled": False,
            "webSearchMode": "disabled",
            "webSearchUsed": False,
            "webSearchEvidenceVerified": False,
            "automaticRetry": False,
        })
        mission.update({
            "status": "blocked",
            "phase": "auto_guarded_blocked",
            "workStatus": "blocked",
            "errorCode": "blocked",
            "blockedCapability": "filesystem_write",
            "attemptCount": 1,
            "result": "legacy read-only Runner could not create source",
            "artifactPath": artifact_reference,
            "reportIds": [report_id],
            "workflowOutputContract": receipt,
            "evidence": [],
            "structuredOutputError": "",
            "webSearchUsed": False,
            "webSearchEvidenceVerified": False,
            "execution": old_execution,
            "updatedAt": "2026-08-24T01:54:11+07:00",
            "completedAt": "2026-08-24T01:54:11+07:00",
        })
        self.bridge.save_missions([mission])
        stage.update({
            "status": "queued",
            "missionId": mission_id,
            "reportId": None,
            "evidenceVerified": False,
            "artifacts": [],
        })
        report = {
            "id": report_id,
            "type": "ea_build_report",
            "title": "Legacy writer failure",
            "summary": mission["result"],
            "ownerAgentId": "ea_developer",
            "linkedMissionId": mission_id,
            "linkedPropId": "right_server_racks",
            "status": "blocked",
            "findings": [],
            "metrics": {"workflowOutput": receipt},
            "nextActions": [],
            "evidence": [],
            "artifacts": [artifact_reference],
            "risks": ["blocked"],
            "workflowContext": lineage,
            "createdAt": "2026-08-24T01:54:11+07:00",
            "updatedAt": "2026-08-24T01:54:11+07:00",
        }
        self.bridge.write_json(
            self.bridge.RUNTIME_REPORTS_DIR / f"{report_id}.json",
            report,
        )
        exact_directory = f"workspace/ea-factory/{build_id}/Source"
        for event in (
            {
                "type": "mission.auto_claimed",
                "missionId": mission_id,
                "attemptCount": 1,
            },
            {
                "type": "mission.auto_run_start",
                "missionId": mission_id,
                "requestedSandbox": "workspace-write",
                "workingDirectory": exact_directory,
                "writeRoots": [exact_directory],
                "controlPlaneWritable": False,
                "eaFactoryBuildId": build_id,
                "eaFactoryStageId": "generate_source",
            },
            {
                "type": "mission.auto_run_end",
                "missionId": mission_id,
                "status": "blocked",
                "workingDirectory": exact_directory,
                "writeRoots": [],
                "controlPlaneWritable": False,
                "workflowOutputContractValid": False,
                "automaticRetry": False,
            },
        ):
            self.bridge.append_audit(event)
        return build, stage, mission, report

    def startup_reconcile_legacy_writer_stage(
        self,
        build: dict,
        stage: dict,
        mission: dict,
    ) -> None:
        strategy_stage = self.bridge._ea_factory_stage_row(
            build,
            "strategy_spec",
        )
        strategy_mission = {
            "id": strategy_stage["missionId"],
            "status": "completed",
            "reportIds": [strategy_stage["reportId"]],
            "updatedAt": strategy_stage["updatedAt"],
        }
        strategy_report = {
            "id": strategy_stage["reportId"],
            "status": "ready",
            "linkedMissionId": strategy_stage["missionId"],
        }
        changed = self.bridge._ea_factory_sync_build_status(
            build,
            missions=[strategy_mission, mission],
            reports=[strategy_report],
            ingest_sources=False,
        )
        self.assertTrue(changed)
        self.assertEqual(stage["status"], "blocked")
        self.assertEqual(stage["blockedReasonCode"], "blocked")
        self.assertEqual(stage["updatedAt"], mission["updatedAt"])
        self.assertEqual(build["status"], "attention_required")

    def rebind_legacy_writer_authorized_packet(self, mission: dict) -> None:
        budget = mission.get("budget")
        self.assertIsInstance(budget, dict)
        mission["idempotencyScopeDigest"] = (
            self.bridge._mission_request_scope_digest(
                str(mission.get("requester") or ""),
                str(mission.get("toolId") or ""),
                str(mission.get("owner") or ""),
                str(mission.get("detail") or ""),
                str(mission.get("targetId") or ""),
                str(mission.get("risk") or ""),
                str(mission.get("modelTier") or ""),
                budget,
                str(mission.get("reportType") or ""),
                self.bridge.safe_reference(mission.get("parentMissionId")),
            )
        )
        mission["execution"]["authorizationPayloadDigest"] = (
            self.bridge.mission_payload_digest(mission)
        )

    def missing_mission_visibility_fixture(
        self,
        stage_id: str,
        status: str,
        started_at: str,
    ) -> tuple[dict, dict, list[dict], list[dict]]:
        build, _generation, _brief, _lineage = self.factory_generation_fixture(
            f"ea-build-visibility-{stage_id}-{status}"
        )
        stage = self.bridge._ea_factory_stage_row(build, stage_id)
        request_key = f"visibility-{stage_id}-{status}"
        stage.update({
            "status": status,
            "missionId": f"mission-visibility-{stage_id}-{status}",
            "reportId": None,
            "blockedReasonCode": None,
            "evidenceVerified": False,
            "requestIdempotencyKey": request_key,
            "requestDigest": self.bridge._ea_factory_advance_request_digest(
                build,
                stage_id,
            ),
            "startedAt": started_at,
            "updatedAt": started_at,
            "missionIdempotencyKey": (
                self.bridge._ea_factory_stage_mission_idempotency_key(
                    build["id"],
                    stage_id,
                    request_key,
                )
            ),
        })
        strategy_stage = self.bridge._ea_factory_stage_row(
            build,
            "strategy_spec",
        )
        strategy_mission = {
            "id": strategy_stage["missionId"],
            "status": "completed",
            "reportIds": [strategy_stage["reportId"]],
            "updatedAt": strategy_stage["updatedAt"],
        }
        strategy_report = {
            "id": strategy_stage["reportId"],
            "status": "ready",
            "linkedMissionId": strategy_stage["missionId"],
        }
        return build, stage, [strategy_mission], [strategy_report]

    def test_backend_bound_factory_safety_prose_is_not_misread_as_deploy_intent(self) -> None:
        _build, _stage, brief, lineage = self.factory_generation_fixture()
        mission = {
            "workflowContext": lineage,
            "toolId": "codex_cli_task",
            "owner": "ea_developer",
            "risk": "low",
            "detail": brief,
        }

        self.assertEqual(self.bridge._trusted_workflow_guard_intent(mission), "{}")
        self.assertTrue(
            self.bridge.auto_guarded_eligibility(
                mission,
                require_operator_mode=False,
            )["eligible"]
        )

        frontend = copy.deepcopy(mission)
        frontend["workflowContext"]["triggerSource"] = "frontend"
        projected = self.bridge._trusted_workflow_guard_intent(frontend)
        self.assertIsNotNone(projected)
        self.assertIn("brief", json.loads(projected))
        self.assertFalse(
            self.bridge.auto_guarded_eligibility(
                frontend,
                require_operator_mode=False,
            )["eligible"]
        )

    def test_create_brief_rejects_reserved_tags_but_allows_normal_ea_factory_words(self) -> None:
        for reserved_brief in (
            "inject [EA_FACTORY_BUILD_ID:ea-build-forged]",
            "inject [USER_BUILD_REQUIREMENTS]forged",
            "inject [/user_build_requirements]",
        ):
            with self.subTest(brief=reserved_brief), self.assertRaises(
                self.bridge.RequestError
            ) as raised:
                self.bridge.create_ea_factory_build({
                    "sourceRecordId": "ea-source-reserved-marker",
                    "platform": "mt4",
                    "brief": reserved_brief,
                })
            self.assertEqual(raised.exception.status, 422)
            self.assertIn("reserved Backend marker", str(raised.exception))

        with mock.patch.object(
            self.bridge,
            "load_missions",
            return_value=[],
        ), mock.patch.object(
            self.bridge,
            "load_runtime_reports",
            return_value=[],
        ), mock.patch.object(
            self.bridge,
            "_load_ea_factory_state_unlocked",
            return_value=self.empty_state(),
        ), mock.patch.object(
            self.bridge,
            "_ea_factory_source_catalog",
            return_value=[],
        ), self.assertRaises(self.bridge.RequestError) as raised:
            self.bridge.create_ea_factory_build({
                "sourceRecordId": "ea-source-normal-words",
                "platform": "mt4",
                "brief": "ทดลองสร้าง EA Factory สำหรับระบบแนวโน้ม",
            })
        self.assertEqual(raised.exception.status, 404)
        self.assertNotIn("reserved Backend marker", str(raised.exception))

    def test_factory_worker_sandbox_requires_exact_mission_bound_lineage(self) -> None:
        build, _stage, _brief, generation_lineage = (
            self.factory_generation_fixture("ea-build-worker-generate")
        )
        _review_build, _review_brief, review_lineage = (
            self.factory_review_fixture("ea-build-worker-review")
        )
        generation = {
            "workflowContext": generation_lineage,
            "toolId": "codex_cli_task",
            "owner": "ea_developer",
        }
        review = {
            "workflowContext": review_lineage,
            "toolId": "codex_cli_task",
            "owner": "ea_developer",
        }

        generation_scope = (
            self.bridge._trusted_backend_ea_factory_worker_sandbox(generation)
        )
        review_scope = self.bridge._trusted_backend_ea_factory_worker_sandbox(
            review
        )
        expected_root = f"ea-factory/{build['id']}/Source"
        self.assertEqual(generation_scope["stageId"], "generate_source")
        self.assertEqual(
            generation_scope["scopedWorkspaceWriteRoot"],
            expected_root,
        )
        self.assertEqual(generation_scope["writeRoots"], [expected_root])
        self.assertTrue(generation_scope["readOnly"])
        self.assertEqual(
            generation_scope["resultProfile"],
            self.bridge.EA_FACTORY_SOURCE_RESULT_PROFILE,
        )
        self.assertEqual(review_scope["stageId"], "source_review")
        self.assertTrue(review_scope["readOnly"])
        self.assertEqual(review_scope["writeRoots"], [])

        for field, value in (
            ("owner", "manager"),
            ("toolId", "manager_mission"),
        ):
            tampered = copy.deepcopy(generation)
            tampered[field] = value
            with self.subTest(field=field):
                self.assertIsNone(
                    self.bridge._trusted_backend_ea_factory_worker_sandbox(
                        tampered
                    )
                )
        tampered = copy.deepcopy(generation)
        tampered["workflowContext"]["inputDigest"] = "f" * 64
        self.assertIsNone(
            self.bridge._trusted_backend_ea_factory_worker_sandbox(tampered)
        )
        tampered = copy.deepcopy(generation)
        duplicate_marker = (
            f"[EA_FACTORY_BUILD_ID:{build['id']}]"
            + tampered["workflowContext"]["inputs"]["brief"]
        )
        tampered["workflowContext"]["inputs"]["brief"] = duplicate_marker
        tampered["workflowContext"]["inputDigest"] = self.bridge.payload_digest(
            "dashboard-workflow-input-v1",
            "right_server_racks",
            "build_strategy_code",
            json.dumps(
                tampered["workflowContext"]["inputs"],
                ensure_ascii=False,
                sort_keys=True,
            ),
        )
        self.assertIsNone(
            self.bridge._trusted_backend_ea_factory_worker_sandbox(tampered)
        )

    def test_factory_worker_commands_and_audit_use_exact_stage_sandboxes(self) -> None:
        build, _stage, generation_brief, generation_lineage = (
            self.factory_generation_fixture("ea-build-worker-command")
        )
        _review_build, review_brief, review_lineage = (
            self.factory_review_fixture("ea-build-worker-review-command")
        )
        captured_commands: list[list[str]] = []

        def fake_runner(command, **_kwargs):
            captured_commands.append([str(item) for item in command])
            return {
                "ok": False,
                "exitCode": 1,
                "processStarted": False,
                "output": json.dumps({"ok": False, "status": "failed"}),
            }

        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            self.bridge,
            "MISSIONS_PATH",
            Path(temporary) / "missions.json",
        ), mock.patch.object(
            self.bridge,
            "AUDIT_PATH",
            Path(temporary) / "bridge-audit.jsonl",
        ), mock.patch.object(
            self.bridge,
            "load_operator_mode_record",
            return_value={"mode": "auto_guarded"},
        ):
            generation = self.create_factory_worker_mission(
                "build_strategy_code",
                generation_brief,
                generation_lineage,
                "ea-factory-worker-generate",
            )
            review = self.create_factory_worker_mission(
                "review_source_code",
                review_brief,
                review_lineage,
                "ea-factory-worker-review",
            )
            with mock.patch.object(
                self.bridge,
                "bridge_status",
                return_value={"codex": self.writer_ready_status()},
            ), mock.patch.object(
                self.bridge,
                "codex_rate_limits",
                return_value={
                    "ok": True,
                    "stale": False,
                    "limitReached": False,
                    "remainingPercent": 80,
                },
            ), mock.patch.object(
                self.bridge,
                "_collaboration_quota_gate",
                return_value={"allowed": True, "reason": "ready"},
            ), mock.patch.object(
                self.bridge,
                "check_rate_limit",
                return_value=(True, 0),
            ), mock.patch.object(
                self.bridge,
                "run_safe_command",
                side_effect=fake_runner,
            ), mock.patch.object(
                self.bridge,
                "finish_auto_mission",
            ), mock.patch.object(
                self.bridge,
                "heartbeat_auto_mission",
            ), mock.patch.object(
                self.bridge,
                "update_mission_worker_state",
            ), mock.patch.object(
                self.bridge,
                "invalidate_codex_rate_limit_cache",
            ), mock.patch.object(
                self.bridge,
                "append_audit",
            ) as audit:
                self.bridge.process_auto_mission("worker-generate", generation)
                self.bridge.process_auto_mission("worker-review", review)

        self.assertEqual(len(captured_commands), 2)
        generation_command, review_command = captured_commands
        scoped_root = f"ea-factory/{build['id']}/Source"
        self.assertIn("--read-only-work", generation_command)
        self.assertIn("--scoped-workspace-write-root", generation_command)
        self.assertEqual(
            generation_command[
                generation_command.index("--scoped-workspace-write-root") + 1
            ],
            scoped_root,
        )
        self.assertIn("--read-only-work", review_command)
        self.assertNotIn("--scoped-workspace-write-root", review_command)
        self.assertIn("--result-profile", generation_command)
        self.assertEqual(
            generation_command[generation_command.index("--result-profile") + 1],
            self.bridge.EA_FACTORY_SOURCE_RESULT_PROFILE,
        )
        starts = [
            call.args[0]
            for call in audit.call_args_list
            if call.args and call.args[0].get("type") == "mission.auto_run_start"
        ]
        self.assertEqual(len(starts), 2)
        self.assertEqual(
            starts[0]["workingDirectory"],
            f"workspace/{scoped_root}",
        )
        self.assertEqual(
            starts[0]["writeRoots"],
            [f"workspace/{scoped_root}"],
        )
        self.assertEqual(starts[0]["eaFactoryStageId"], "generate_source")
        self.assertEqual(starts[1]["requestedSandbox"], "read-only")
        self.assertEqual(starts[1]["workingDirectory"], "workspace")
        self.assertEqual(starts[1]["writeRoots"], [])
        self.assertEqual(starts[1]["eaFactoryStageId"], "source_review")

    def test_factory_worker_tampered_owner_tool_or_input_digest_never_starts_runner(self) -> None:
        _build, _stage, brief, lineage = self.factory_generation_fixture(
            "ea-build-worker-tamper"
        )
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            self.bridge,
            "MISSIONS_PATH",
            Path(temporary) / "missions.json",
        ), mock.patch.object(
            self.bridge,
            "load_operator_mode_record",
            return_value={"mode": "auto_guarded"},
        ):
            mission = self.create_factory_worker_mission(
                "build_strategy_code",
                brief,
                lineage,
                "ea-factory-worker-tamper",
            )

        cases = []
        tampered = copy.deepcopy(mission)
        tampered["owner"] = "manager"
        cases.append(("owner", tampered, "auto_claim_identity_changed"))
        tampered = copy.deepcopy(mission)
        tampered["toolId"] = "manager_mission"
        cases.append(("tool", tampered, "auto_claim_identity_changed"))
        tampered = copy.deepcopy(mission)
        tampered["workflowContext"]["inputDigest"] = "f" * 64
        cases.append(("inputDigest", tampered, "ea_factory_worker_scope_invalid"))
        tampered = copy.deepcopy(mission)
        tampered["workflowContext"]["inputDigest"] = "malformed-digest"
        cases.append(("malformedInputDigest", tampered, "ea_factory_worker_scope_invalid"))

        for label, claimed, expected_code in cases:
            claimed["status"] = "running"
            claimed["execution"] = {"leaseId": f"lease-{label}"}
            with self.subTest(label=label), mock.patch.object(
                self.bridge,
                "bridge_status",
                return_value={"codex": self.writer_ready_status()},
            ), mock.patch.object(
                self.bridge,
                "codex_rate_limits",
                return_value={
                    "ok": True,
                    "stale": False,
                    "limitReached": False,
                    "remainingPercent": 80,
                },
            ), mock.patch.object(
                self.bridge,
                "_collaboration_quota_gate",
                return_value={"allowed": True, "reason": "ready"},
            ), mock.patch.object(
                self.bridge,
                "check_rate_limit",
                return_value=(True, 0),
            ), mock.patch.object(
                self.bridge,
                "claim_auto_mission",
                return_value=claimed,
            ), mock.patch.object(
                self.bridge,
                "run_safe_command",
            ) as runner, mock.patch.object(
                self.bridge,
                "finish_auto_mission",
            ) as finish, mock.patch.object(
                self.bridge,
                "update_mission_worker_state",
            ), mock.patch.object(
                self.bridge,
                "invalidate_codex_rate_limit_cache",
            ):
                self.bridge.process_auto_mission(f"worker-{label}", mission)

            runner.assert_not_called()
            finish.assert_called_once()
            runner_receipt = finish.call_args.args[2]
            self.assertFalse(runner_receipt["processStarted"])
            self.assertEqual(runner_receipt["exitCode"], expected_code)

    def test_exact_waiting_factory_stage_is_recovered_without_approval(self) -> None:
        build, stage, brief, lineage = self.factory_generation_fixture()
        mission = self.legacy_false_approval_mission(
            build,
            stage,
            brief,
            lineage,
        )
        old_scope_digest = mission["idempotencyScopeDigest"]

        with tempfile.TemporaryDirectory() as temporary, (
            mock.patch.object(
                self.bridge,
                "MISSIONS_PATH",
                Path(temporary) / "missions.json",
            )
        ), mock.patch.object(
            self.bridge,
            "AUDIT_PATH",
            Path(temporary) / "bridge-audit.jsonl",
        ), mock.patch.object(
            self.bridge,
            "load_operator_mode_record",
            return_value={"mode": "auto_guarded"},
        ):
            self.bridge.save_missions([mission])
            recovered = self.bridge._ea_factory_recover_false_approval_stage_mission(
                build,
                stage,
                "build_strategy_code",
                brief,
            )
            stored = self.bridge.find_mission(mission["id"])
            audits = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)

        self.assertEqual(recovered["id"], mission["id"])
        self.assertEqual(stored, recovered)
        self.assertEqual(recovered["status"], "queued")
        self.assertEqual(recovered["executionMode"], "auto_guarded")
        self.assertTrue(recovered["autoEligible"])
        self.assertFalse(recovered["requiresHumanApproval"])
        self.assertFalse(recovered["approval"]["required"])
        self.assertEqual(recovered["approval"]["state"], "not_required")
        self.assertNotEqual(recovered["idempotencyScopeDigest"], old_scope_digest)
        history = recovered["approvalMigrationHistory"][-1]
        self.assertEqual(
            history["kind"],
            "ea_factory_false_positive_approval_recovery",
        )
        self.assertEqual(history["previousIdempotencyScopeDigest"], old_scope_digest)
        self.assertEqual(
            history["replacementIdempotencyScopeDigest"],
            recovered["idempotencyScopeDigest"],
        )
        self.assertEqual(audits[-1]["missionId"], mission["id"])

    def test_exact_legacy_writer_failure_requeues_same_mission_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary) / "project"
            runtime_dir = project_root / "data" / "runtime"
            reports_dir = runtime_dir / "reports"
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_dir),
                mock.patch.object(
                    self.bridge,
                    "RUNTIME_REPORTS_DIR",
                    reports_dir,
                ),
                mock.patch.object(
                    self.bridge,
                    "MISSIONS_PATH",
                    runtime_dir / "missions.json",
                ),
                mock.patch.object(
                    self.bridge,
                    "AUDIT_PATH",
                    runtime_dir / "bridge-audit.jsonl",
                ),
                mock.patch.object(
                    self.bridge,
                    "load_operator_mode_record",
                    return_value={"mode": "auto_guarded"},
                ),
                mock.patch.object(
                    self.bridge,
                    "detect_codex",
                    return_value=self.writer_ready_status(),
                ) as detect,
            ):
                build, stage, mission, report = (
                    self.legacy_writer_failure_fixture()
                )
                old_authorization_id = mission["execution"]["authorizationId"]
                prior_report_digest = self.bridge.payload_digest(
                    "ea-factory-invalid-writer-report-v1",
                    report,
                )
                recovered = (
                    self.bridge._ea_factory_recover_legacy_runner_writer_failure(
                        build,
                        stage,
                    )
                )
                stored = self.bridge.find_mission(mission["id"])
                report_after = self.bridge.read_json(
                    reports_dir / f"{report['id']}.json",
                    None,
                )
                second = (
                    self.bridge._ea_factory_recover_legacy_runner_writer_failure(
                        build,
                        stage,
                    )
                )
                audits = self.bridge.tail_jsonl(
                    self.bridge.AUDIT_PATH,
                    limit=20,
                )

        detect.assert_called_once_with(force=True)
        self.assertIsNotNone(recovered)
        self.assertIsNone(second)
        self.assertEqual(recovered["id"], mission["id"])
        self.assertEqual(stored, recovered)
        self.assertEqual(recovered["status"], "queued")
        self.assertEqual(recovered["attemptCount"], 0)
        self.assertEqual(recovered["reportIds"], [])
        self.assertIsNone(recovered["artifactPath"])
        self.assertEqual(
            recovered["runnerWriterRecoveryVersion"],
            self.bridge.EA_FACTORY_RUNNER_WRITER_RECOVERY_VERSION,
        )
        self.assertEqual(
            stage["runnerWriterRecoveryVersion"],
            self.bridge.EA_FACTORY_RUNNER_WRITER_RECOVERY_VERSION,
        )
        history = recovered["runnerWriterRecoveryHistory"]
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["previousReportId"], report["id"])
        self.assertEqual(
            history[0]["previousReportDigest"],
            prior_report_digest,
        )
        self.assertEqual(history[0]["remainingAttempts"], 0)
        self.assertNotEqual(
            recovered["execution"]["authorizationId"],
            old_authorization_id,
        )
        self.assertFalse(recovered["execution"]["processStarted"])
        self.assertTrue(recovered["execution"]["automaticRetry"])
        self.assertEqual(
            recovered["execution"]["resultProfile"],
            self.bridge.EA_FACTORY_SOURCE_RESULT_PROFILE,
        )
        self.assertEqual(report_after, report)
        self.assertEqual(report_after["status"], "blocked")
        self.assertFalse(report_after["metrics"]["workflowOutput"]["valid"])
        recovery_events = [
            row
            for row in audits
            if row.get("type")
            == "ea_factory.runner_writer_recovery_requeued"
        ]
        self.assertEqual(len(recovery_events), 1)
        self.assertEqual(recovery_events[0]["missionId"], mission["id"])

    def test_startup_reconciled_blocked_stage_requeues_same_mission(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary) / "project"
            runtime_dir = project_root / "data" / "runtime"
            reports_dir = runtime_dir / "reports"
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_dir),
                mock.patch.object(
                    self.bridge,
                    "RUNTIME_REPORTS_DIR",
                    reports_dir,
                ),
                mock.patch.object(
                    self.bridge,
                    "MISSIONS_PATH",
                    runtime_dir / "missions.json",
                ),
                mock.patch.object(
                    self.bridge,
                    "AUDIT_PATH",
                    runtime_dir / "bridge-audit.jsonl",
                ),
                mock.patch.object(
                    self.bridge,
                    "load_operator_mode_record",
                    return_value={"mode": "auto_guarded"},
                ),
                mock.patch.object(
                    self.bridge,
                    "detect_codex",
                    return_value=self.writer_ready_status(),
                ) as detect,
            ):
                build, stage, mission, _report = (
                    self.legacy_writer_failure_fixture(
                        "ea-build-startup-reconciled-writer"
                    )
                )
                self.startup_reconcile_legacy_writer_stage(
                    build,
                    stage,
                    mission,
                )
                recovered = (
                    self.bridge._ea_factory_recover_legacy_runner_writer_failure(
                        build,
                        stage,
                    )
                )
                stored = self.bridge.find_mission(mission["id"])

        detect.assert_called_once_with(force=True)
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered["id"], mission["id"])
        self.assertEqual(stored, recovered)
        self.assertEqual(recovered["status"], "queued")
        self.assertEqual(
            recovered["runnerWriterRecoveryVersion"],
            self.bridge.EA_FACTORY_RUNNER_WRITER_RECOVERY_VERSION,
        )

    def test_startup_reconciled_blocked_stage_tamper_never_requeues(self) -> None:
        tamper_cases = (
            "blocked_reason",
            "updated_at",
            "build_status",
            "stage_artifact",
        )
        for case in tamper_cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                project_root = Path(temporary) / "project"
                runtime_dir = project_root / "data" / "runtime"
                reports_dir = runtime_dir / "reports"
                with (
                    mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                    mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_dir),
                    mock.patch.object(
                        self.bridge,
                        "RUNTIME_REPORTS_DIR",
                        reports_dir,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "MISSIONS_PATH",
                        runtime_dir / "missions.json",
                    ),
                    mock.patch.object(
                        self.bridge,
                        "AUDIT_PATH",
                        runtime_dir / "bridge-audit.jsonl",
                    ),
                    mock.patch.object(
                        self.bridge,
                        "load_operator_mode_record",
                        return_value={"mode": "auto_guarded"},
                    ),
                    mock.patch.object(
                        self.bridge,
                        "detect_codex",
                        return_value=self.writer_ready_status(),
                    ) as detect,
                ):
                    build, stage, mission, _report = (
                        self.legacy_writer_failure_fixture(
                            f"ea-build-startup-reconciled-tamper-{case}"
                        )
                    )
                    self.startup_reconcile_legacy_writer_stage(
                        build,
                        stage,
                        mission,
                    )
                    if case == "blocked_reason":
                        stage["blockedReasonCode"] = "stage_blocked"
                    elif case == "updated_at":
                        stage["updatedAt"] = "2026-08-24T01:54:12+07:00"
                    elif case == "build_status":
                        build["status"] = "ready"
                    else:
                        stage["artifacts"] = [
                            build["artifactManifest"][0]["fileId"]
                        ]
                    before = copy.deepcopy(
                        self.bridge.find_mission(mission["id"])
                    )
                    recovered = (
                        self.bridge._ea_factory_recover_legacy_runner_writer_failure(
                            build,
                            stage,
                        )
                    )
                    after = self.bridge.find_mission(mission["id"])

                self.assertIsNone(recovered)
                self.assertEqual(after, before)
                detect.assert_not_called()

    def test_legacy_source_projection_drift_recovers_with_exact_authorized_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary) / "project"
            runtime_dir = project_root / "data" / "runtime"
            reports_dir = runtime_dir / "reports"
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_dir),
                mock.patch.object(
                    self.bridge,
                    "RUNTIME_REPORTS_DIR",
                    reports_dir,
                ),
                mock.patch.object(
                    self.bridge,
                    "MISSIONS_PATH",
                    runtime_dir / "missions.json",
                ),
                mock.patch.object(
                    self.bridge,
                    "AUDIT_PATH",
                    runtime_dir / "bridge-audit.jsonl",
                ),
                mock.patch.object(
                    self.bridge,
                    "load_operator_mode_record",
                    return_value={"mode": "auto_guarded"},
                ),
                mock.patch.object(
                    self.bridge,
                    "detect_codex",
                    return_value=self.writer_ready_status(),
                ) as detect,
            ):
                build, stage, mission, _report = (
                    self.legacy_writer_failure_fixture(
                        "ea-build-authorized-source-projection-drift"
                    )
                )
                self.startup_reconcile_legacy_writer_stage(
                    build,
                    stage,
                    mission,
                )
                rich_source_metadata = json.dumps({
                    "reportId": build["sourceReportId"],
                    "status": "ready",
                    "metrics": {
                        "eaFactoryStrategySpec": {
                            "core": {"entry_rules": "authorized legacy report projection"},
                            "recordDigest": build["sourceRecordDigest"],
                        },
                    },
                }, ensure_ascii=False, sort_keys=True)
                mission["detail"] = mission["detail"].replace(
                    "[UNTRUSTED_SOURCE_REPORT_END]",
                    rich_source_metadata + "\n[UNTRUSTED_SOURCE_REPORT_END]",
                    1,
                )
                self.rebind_legacy_writer_authorized_packet(mission)
                context = self.bridge._workflow_context_storage(
                    mission["workflowContext"]
                )
                reconstructed = self.bridge._workflow_prompt(
                    "build_strategy_code",
                    context["inputs"],
                    context.get("source"),
                    self.bridge._trusted_workflow_plugin_profile(
                        "right_server_racks",
                        "build_strategy_code",
                        context["inputs"],
                    ),
                )
                self.assertNotEqual(mission["detail"], reconstructed)
                self.assertTrue(
                    self.bridge._ea_factory_legacy_writer_authorized_packet_valid(
                        mission
                    )
                )
                self.bridge.save_missions([mission])
                recovered = (
                    self.bridge._ea_factory_recover_legacy_runner_writer_failure(
                        build,
                        stage,
                    )
                )

        detect.assert_called_once_with(force=True)
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered["id"], mission["id"])
        self.assertEqual(recovered["status"], "queued")

    def test_legacy_writer_authorization_packet_tamper_fails_before_detect(self) -> None:
        tamper_cases = (
            "detail_without_authorization_digest",
            "authorization_payload_digest",
        )
        for case in tamper_cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                project_root = Path(temporary) / "project"
                runtime_dir = project_root / "data" / "runtime"
                reports_dir = runtime_dir / "reports"
                with (
                    mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                    mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_dir),
                    mock.patch.object(
                        self.bridge,
                        "RUNTIME_REPORTS_DIR",
                        reports_dir,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "MISSIONS_PATH",
                        runtime_dir / "missions.json",
                    ),
                    mock.patch.object(
                        self.bridge,
                        "AUDIT_PATH",
                        runtime_dir / "bridge-audit.jsonl",
                    ),
                    mock.patch.object(
                        self.bridge,
                        "load_operator_mode_record",
                        return_value={"mode": "auto_guarded"},
                    ),
                    mock.patch.object(
                        self.bridge,
                        "detect_codex",
                        return_value=self.writer_ready_status(),
                    ) as detect,
                ):
                    build, stage, mission, _report = (
                        self.legacy_writer_failure_fixture(
                            f"ea-build-authorized-packet-tamper-{case}"
                        )
                    )
                    self.startup_reconcile_legacy_writer_stage(
                        build,
                        stage,
                        mission,
                    )
                    if case == "detail_without_authorization_digest":
                        mission["detail"] += "\nUNAUTHORIZED DETAIL TAMPER"
                        old_authorization_digest = mission["execution"][
                            "authorizationPayloadDigest"
                        ]
                        self.rebind_legacy_writer_authorized_packet(mission)
                        mission["execution"]["authorizationPayloadDigest"] = (
                            old_authorization_digest
                        )
                    else:
                        mission["execution"]["authorizationPayloadDigest"] = (
                            "0" * 64
                        )
                    self.bridge.save_missions([mission])
                    before = copy.deepcopy(
                        self.bridge.find_mission(mission["id"])
                    )
                    recovered = (
                        self.bridge._ea_factory_recover_legacy_runner_writer_failure(
                            build,
                            stage,
                        )
                    )
                    after = self.bridge.find_mission(mission["id"])

                self.assertIsNone(recovered)
                self.assertEqual(after, before)
                detect.assert_not_called()

    def test_sync_keeps_recent_async_stage_non_terminal_during_visibility_grace(self) -> None:
        for stage_id in ("generate_source", "source_review"):
            for status in ("queued", "running"):
                with self.subTest(stage_id=stage_id, status=status):
                    started_at = datetime.now(timezone.utc).isoformat()
                    build, stage, missions, reports = (
                        self.missing_mission_visibility_fixture(
                            stage_id,
                            status,
                            started_at,
                        )
                    )
                    changed = self.bridge._ea_factory_sync_build_status(
                        build,
                        missions=missions,
                        reports=reports,
                        ingest_sources=False,
                    )

                    self.assertTrue(changed)
                    self.assertEqual(stage["status"], status)
                    self.assertIsNone(stage["blockedReasonCode"])
                    self.assertEqual(stage["updatedAt"], started_at)
                    self.assertEqual(build["status"], "in_progress")

    def test_sync_blocks_missing_async_stage_after_visibility_grace_expires(self) -> None:
        expired_at = (
            datetime.now(timezone.utc)
            - timedelta(
                seconds=(
                    self.bridge.EA_FACTORY_MISSION_VISIBILITY_GRACE_SECONDS
                    + 1
                )
            )
        ).isoformat()
        for stage_id in ("generate_source", "source_review"):
            for status in ("queued", "running"):
                with self.subTest(stage_id=stage_id, status=status):
                    build, stage, missions, reports = (
                        self.missing_mission_visibility_fixture(
                            stage_id,
                            status,
                            expired_at,
                        )
                    )
                    changed = self.bridge._ea_factory_sync_build_status(
                        build,
                        missions=missions,
                        reports=reports,
                        ingest_sources=False,
                    )

                    self.assertTrue(changed)
                    self.assertEqual(stage["status"], "blocked")
                    self.assertEqual(
                        stage["blockedReasonCode"],
                        "stage_mission_missing",
                    )
                    self.assertEqual(build["status"], "attention_required")

    def test_legacy_writer_recovery_rejects_generic_filesystem_failures(self) -> None:
        tamper_cases = (
            "audit_scope",
            "valid_report",
            "source_created",
            "second_recovery",
        )
        for case in tamper_cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                project_root = Path(temporary) / "project"
                runtime_dir = project_root / "data" / "runtime"
                reports_dir = runtime_dir / "reports"
                with (
                    mock.patch.object(self.bridge, "PROJECT_ROOT", project_root),
                    mock.patch.object(self.bridge, "RUNTIME_DIR", runtime_dir),
                    mock.patch.object(
                        self.bridge,
                        "RUNTIME_REPORTS_DIR",
                        reports_dir,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "MISSIONS_PATH",
                        runtime_dir / "missions.json",
                    ),
                    mock.patch.object(
                        self.bridge,
                        "AUDIT_PATH",
                        runtime_dir / "bridge-audit.jsonl",
                    ),
                    mock.patch.object(
                        self.bridge,
                        "load_operator_mode_record",
                        return_value={"mode": "auto_guarded"},
                    ),
                    mock.patch.object(
                        self.bridge,
                        "detect_codex",
                        return_value=self.writer_ready_status(),
                    ),
                ):
                    build, stage, mission, report = (
                        self.legacy_writer_failure_fixture(
                            f"ea-build-writer-reject-{case}"
                        )
                    )
                    if case == "audit_scope":
                        rows = self.bridge.tail_jsonl(
                            self.bridge.AUDIT_PATH,
                            limit=20,
                        )
                        for row in rows:
                            if row.get("type") == "mission.auto_run_start":
                                row["writeRoots"] = ["workspace"]
                        self.bridge.AUDIT_PATH.unlink()
                        for row in rows:
                            self.bridge.append_audit(row)
                    elif case == "valid_report":
                        report["status"] = "ready"
                        report["metrics"]["workflowOutput"]["valid"] = True
                        self.bridge.write_json(
                            reports_dir / f"{report['id']}.json",
                            report,
                        )
                    elif case == "source_created":
                        source_path = (
                            self.bridge._ea_factory_build_root()
                            / build["id"]
                            / "Source"
                            / "unexpected.mq4"
                        )
                        source_path.write_text("// unexpected", encoding="utf-8")
                    else:
                        mission["runnerWriterRecoveryVersion"] = 1
                        self.bridge.save_missions([mission])

                    before = copy.deepcopy(
                        self.bridge.find_mission(mission["id"])
                    )
                    recovered = (
                        self.bridge._ea_factory_recover_legacy_runner_writer_failure(
                            build,
                            stage,
                        )
                    )
                    after = self.bridge.find_mission(mission["id"])

                self.assertIsNone(recovered)
                self.assertEqual(after, before)

    def test_advance_invokes_writer_recovery_before_reconciliation_replay(self) -> None:
        build, stage, _brief, _lineage = self.factory_generation_fixture(
            "ea-build-writer-replay-order"
        )
        stage.update({
            "status": "queued",
            "missionId": "mission-writer-replay-order",
        })
        state = {
            "schemaVersion": self.bridge.EA_FACTORY_STATE_SCHEMA_VERSION,
            "sourceSnapshots": [],
            "builds": [build],
            "createReservations": [],
            "updatedAt": None,
        }
        recovered_mission = {
            "id": stage["missionId"],
            "status": "queued",
        }
        call_order: list[str] = []

        def recover(*_args, **_kwargs):
            call_order.append("recover")
            stage["runnerWriterRecoveryVersion"] = 1
            return recovered_mission

        def reconcile(*_args, **_kwargs):
            call_order.append("reconcile")
            return True

        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_recover_legacy_runner_writer_failure",
                side_effect=recover,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_sync_build_status",
                side_effect=reconcile,
            ),
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ) as write_state,
            mock.patch.object(
                self.bridge,
                "load_missions",
                return_value=[recovered_mission],
            ),
            mock.patch.object(
                self.bridge,
                "run_dashboard_workflow_action",
            ) as dispatch,
            mock.patch.object(
                self.bridge,
                "ea_factory_read_model",
                return_value={"builds": [{"id": build["id"]}]},
            ),
            mock.patch.object(
                self.bridge,
                "mission_read_model_item",
                side_effect=lambda row: row,
            ),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            result = self.bridge.advance_ea_factory_build(
                build["id"],
                {
                    "stageId": "generate_source",
                    "idempotencyKey": "new-browser-retry-key",
                },
            )

        self.assertEqual(call_order[:2], ["recover", "reconcile"])
        dispatch.assert_not_called()
        self.assertTrue(result["idempotentReplay"])
        self.assertEqual(
            result["kind"],
            "ea_factory_runner_writer_recovery_requeued",
        )
        self.assertGreaterEqual(write_state.call_count, 1)

    def test_factory_recovery_rejects_tampered_approval_or_scope_digest(self) -> None:
        build, stage, brief, lineage = self.factory_generation_fixture(
            "ea-build-recovery-digest-tamper"
        )
        cases = []
        tampered = self.legacy_false_approval_mission(
            build,
            stage,
            brief,
            lineage,
        )
        tampered["approval"]["payloadDigest"] = "f" * 64
        cases.append(("approvalPayloadDigest", tampered))
        tampered = self.legacy_false_approval_mission(
            build,
            stage,
            brief,
            lineage,
        )
        tampered["idempotencyScopeDigest"] = "f" * 64
        cases.append(("requestScopeDigest", tampered))

        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            self.bridge,
            "MISSIONS_PATH",
            Path(temporary) / "missions.json",
        ), mock.patch.object(
            self.bridge,
            "AUDIT_PATH",
            Path(temporary) / "bridge-audit.jsonl",
        ), mock.patch.object(
            self.bridge,
            "load_operator_mode_record",
            return_value={"mode": "auto_guarded"},
        ):
            for label, mission in cases:
                with self.subTest(label=label):
                    mission["id"] = f"mission-{label.lower()}"
                    self.bridge.save_missions([mission])
                    recovered = (
                        self.bridge._ea_factory_recover_false_approval_stage_mission(
                            build,
                            stage,
                            "build_strategy_code",
                            brief,
                        )
                    )
                    stored = self.bridge.find_mission(mission["id"])
                    self.assertIsNone(recovered)
                    self.assertEqual(stored["status"], "waiting_approval")
                    self.assertTrue(stored["approval"]["required"])

    def test_factory_recovery_accepts_only_exact_startup_archive_and_no_execution(self) -> None:
        build, stage, brief, lineage = self.factory_generation_fixture(
            "ea-build-startup-archive"
        )
        mission = self.legacy_false_approval_mission(
            build,
            stage,
            brief,
            lineage,
        )
        mission["id"] = "mission-startup-archive"
        mission["approval"]["payloadDigest"] = self.bridge.mission_payload_digest(
            mission
        )

        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            self.bridge,
            "MISSIONS_PATH",
            Path(temporary) / "missions.json",
        ), mock.patch.object(
            self.bridge,
            "AUDIT_PATH",
            Path(temporary) / "bridge-audit.jsonl",
        ), mock.patch.object(
            self.bridge,
            "load_operator_mode_record",
            return_value={"mode": "auto_guarded"},
        ):
            self.bridge.save_missions([mission])
            self.assertEqual(self.bridge.reconcile_stale_approval_missions(), 1)
            archived = self.bridge.find_mission(mission["id"])
            self.assertEqual(archived["status"], "archived")
            recovered = self.bridge._ea_factory_recover_false_approval_stage_mission(
                build,
                stage,
                "build_strategy_code",
                brief,
            )
            self.assertEqual(recovered["status"], "queued")
            self.assertEqual(
                recovered["approvalMigrationHistory"][-1]["previousStatus"],
                "archived",
            )
            self.assertNotIn("approvalMigration", recovered)

            tampered = self.legacy_false_approval_mission(
                build,
                stage,
                brief,
                lineage,
            )
            tampered["id"] = "mission-execution-started"
            tampered["execution"] = {"processStarted": True}
            self.bridge.save_missions([tampered])
            rejected = self.bridge._ea_factory_recover_false_approval_stage_mission(
                build,
                stage,
                "build_strategy_code",
                brief,
            )
            stored = self.bridge.find_mission(tampered["id"])

        self.assertIsNone(rejected)
        self.assertEqual(stored["status"], "waiting_approval")
        self.assertTrue(stored["execution"]["processStarted"])

    def test_advance_retry_recovers_same_legacy_mission_before_dispatch(self) -> None:
        build, stage, brief, lineage = self.factory_generation_fixture(
            "ea-build-live-retry"
        )
        mission = self.legacy_false_approval_mission(
            build,
            stage,
            brief,
            lineage,
        )
        mission["id"] = "mission-live-retry"
        mission["approval"]["payloadDigest"] = self.bridge.mission_payload_digest(
            mission
        )
        state = {
            "schemaVersion": self.bridge.EA_FACTORY_STATE_SCHEMA_VERSION,
            "sourceSnapshots": [],
            "builds": [build],
            "createReservations": [],
            "updatedAt": None,
        }
        returned_model = {"builds": [{"id": build["id"]}]}

        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            self.bridge,
            "MISSIONS_PATH",
            Path(temporary) / "missions.json",
        ), mock.patch.object(
            self.bridge,
            "AUDIT_PATH",
            Path(temporary) / "bridge-audit.jsonl",
        ), mock.patch.object(
            self.bridge,
            "load_operator_mode_record",
            return_value={"mode": "auto_guarded"},
        ), mock.patch.object(
            self.bridge,
            "_load_ea_factory_state_unlocked",
            return_value=state,
        ), mock.patch.object(
            self.bridge,
            "_ea_factory_sync_build_status",
            return_value=False,
        ), mock.patch.object(
            self.bridge,
            "_write_ea_factory_state_unlocked",
        ), mock.patch.object(
            self.bridge,
            "deliver_dashboard_report",
            return_value={"mission": {"id": "mission-transfer-live-retry"}},
        ), mock.patch.object(
            self.bridge,
            "run_dashboard_workflow_action",
        ) as dispatch, mock.patch.object(
            self.bridge,
            "ea_factory_read_model",
            return_value=returned_model,
        ), mock.patch.object(
            self.bridge,
            "mission_read_model_item",
            side_effect=lambda item: item,
        ):
            self.bridge.save_missions([mission])
            result = self.bridge.advance_ea_factory_build(
                build["id"],
                {
                    "stageId": "generate_source",
                    "idempotencyKey": "a-different-browser-retry-key",
                },
            )
            stored = self.bridge.find_mission(mission["id"])

        dispatch.assert_not_called()
        self.assertEqual(result["mission"]["id"], mission["id"])
        self.assertEqual(result["mission"]["status"], "queued")
        self.assertEqual(stored["status"], "queued")
        self.assertEqual(stage["missionId"], mission["id"])
        self.assertEqual(stage["status"], "queued")

    def test_get_visible_late_source_and_create_share_same_800_report_catalog(self) -> None:
        record = self.normalized_record(source_key="sheet-late-source")
        late_report = {"id": "report-late-visible-source"}
        all_reports = [
            {"id": f"report-unrelated-{index:03d}"}
            for index in range(self.bridge.EA_FACTORY_SOURCE_REPORT_LIMIT - 1)
        ] + [late_report]
        mission_rows = [{"id": "mission-shared-catalog-snapshot"}]
        catalog_calls: list[dict] = []

        def load_reports(*, limit: int) -> list[dict]:
            return all_reports if limit == self.bridge.EA_FACTORY_SOURCE_REPORT_LIMIT else all_reports[:limit]

        def source_catalog(*, state, reports, missions) -> list[dict]:
            catalog_calls.append(
                {
                    "state": state,
                    "reports": reports,
                    "missions": missions,
                }
            )
            return [record] if late_report in reports and missions is mission_rows else []

        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=self.empty_state(),
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=mission_rows) as load_missions,
            mock.patch.object(self.bridge, "load_runtime_reports", side_effect=load_reports) as load_runtime_reports,
            mock.patch.object(self.bridge, "_ea_factory_source_catalog", side_effect=source_catalog),
            mock.patch.object(
                self.bridge,
                "peek_metatrader_status",
                return_value={"status": "not_checked", "candidates": []},
            ),
            mock.patch.object(
                self.bridge,
                "_metatrader_selection_read_model",
                return_value={"candidates": [], "selectedCandidate": None, "adapterReady": False},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_terminal_gate",
                return_value={"required": True, "ready": False, "adapterReady": False},
            ),
        ):
            read_model = self.bridge.ea_factory_read_model()

        self.assertEqual(
            [item["sourceRecordId"] for item in read_model["sourceCatalog"]["records"]],
            [record["sourceRecordId"]],
        )
        load_missions.assert_called_once_with(shared_snapshot=True)
        load_runtime_reports.assert_called_once_with(
            limit=self.bridge.EA_FACTORY_SOURCE_REPORT_LIMIT,
        )
        self.assertEqual(self.bridge.EA_FACTORY_SOURCE_REPORT_LIMIT, 800)
        self.assertIs(catalog_calls[0]["reports"], all_reports)
        self.assertIs(catalog_calls[0]["missions"], mission_rows)

        build_id = "ea-build-late-visible-source"
        mission, report = self.strategy_stage_entities()
        create_state = self.empty_state()
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=create_state,
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=mission_rows) as create_load_missions,
            mock.patch.object(self.bridge, "load_runtime_reports", side_effect=load_reports) as create_load_reports,
            mock.patch.object(self.bridge, "_ea_factory_source_catalog", side_effect=source_catalog),
            mock.patch.object(self.bridge, "safe_id", return_value=build_id),
            mock.patch.object(
                self.bridge,
                "_ea_factory_create_build_workspace",
                return_value=self.workspace_stub(build_id),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_source_report",
                return_value=(mission, report),
            ),
            mock.patch.object(self.bridge, "_ea_factory_register_artifacts", return_value=[]),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
            mock.patch.object(self.bridge, "append_audit"),
            mock.patch.object(
                self.bridge,
                "ea_factory_read_model",
                return_value={"builds": [{"id": build_id}]},
            ),
            mock.patch.object(self.bridge, "mission_read_model_item", side_effect=lambda item: item),
        ):
            created = self.bridge.create_ea_factory_build(
                {
                    "sourceRecordId": record["sourceRecordId"],
                    "platform": "mt4",
                    "brief": "late visible source",
                    "idempotencyKey": "create-late-visible-source",
                }
            )

        self.assertEqual(created["kind"], "ea_factory_build_created")
        self.assertEqual(created["build"]["id"], build_id)
        create_load_missions.assert_called_once_with(shared_snapshot=True)
        create_load_reports.assert_called_once_with(
            limit=self.bridge.EA_FACTORY_SOURCE_REPORT_LIMIT,
        )
        self.assertIs(catalog_calls[1]["reports"], all_reports)
        self.assertIs(catalog_calls[1]["missions"], mission_rows)
        self.assertEqual(
            catalog_calls[0]["reports"],
            catalog_calls[1]["reports"],
        )

    def test_create_incomplete_reservation_new_key_reuses_build_id_and_aliases(self) -> None:
        record = self.normalized_record(source_key="sheet-reservation-recovery")
        build_id = "ea-build-reservation-recovery"
        brief = "recover exact create reservation"
        request_digest = self.bridge._ea_factory_create_request_digest(
            record["sourceRecordId"],
            "mt4",
            brief,
        )
        reservation = {
            "idempotencyKey": "create-original-key",
            "idempotencyKeys": ["create-original-key"],
            "requestDigest": request_digest,
            "buildId": build_id,
            "sourceRecordId": record["sourceRecordId"],
            "sourceRecordDigest": record["recordDigest"],
            "platform": "mt4",
            "brief": brief,
            "status": "reserved",
            "createdAt": "2026-08-24T02:00:00+00:00",
        }
        state = self.empty_state()
        state["createReservations"] = [reservation]
        mission, report = self.strategy_stage_entities()

        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
            mock.patch.object(self.bridge, "_ea_factory_source_catalog", return_value=[record]),
            mock.patch.object(
                self.bridge,
                "_ea_factory_create_build_workspace",
                return_value=self.workspace_stub(build_id),
            ) as create_workspace,
            mock.patch.object(
                self.bridge,
                "_ea_factory_source_report",
                return_value=(mission, report),
            ),
            mock.patch.object(self.bridge, "_ea_factory_register_artifacts", return_value=[]),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write_state,
            mock.patch.object(self.bridge, "append_audit"),
            mock.patch.object(
                self.bridge,
                "ea_factory_read_model",
                return_value={"builds": [{"id": build_id}]},
            ),
            mock.patch.object(self.bridge, "mission_read_model_item", side_effect=lambda item: item),
        ):
            result = self.bridge.create_ea_factory_build(
                {
                    "sourceRecordId": record["sourceRecordId"],
                    "platform": "mt4",
                    "brief": brief,
                    "idempotencyKey": "create-retry-new-key",
                }
            )

        self.assertEqual(result["kind"], "ea_factory_build_created")
        self.assertEqual(result["build"]["id"], build_id)
        create_workspace.assert_called_once()
        self.assertEqual(create_workspace.call_args.args[0], build_id)
        self.assertEqual(len(state["builds"]), 1)
        persisted_build = state["builds"][0]
        self.assertEqual(persisted_build["id"], build_id)
        self.assertEqual(persisted_build["createIdempotencyKey"], "create-original-key")
        self.assertEqual(
            persisted_build["createIdempotencyKeys"],
            ["create-original-key", "create-retry-new-key"],
        )
        self.assertEqual(persisted_build["createRequestDigest"], request_digest)
        self.assertEqual(state["createReservations"], [])
        self.assertGreaterEqual(write_state.call_count, 2)

    def test_create_incomplete_reservation_changed_source_digest_fails_closed(self) -> None:
        record = self.normalized_record(source_key="sheet-reservation-source-change")
        brief = "source must remain immutable"
        state = self.empty_state()
        state["createReservations"] = [{
            "idempotencyKey": "create-before-source-change",
            "idempotencyKeys": ["create-before-source-change"],
            "requestDigest": self.bridge._ea_factory_create_request_digest(
                record["sourceRecordId"],
                "mt4",
                brief,
            ),
            "buildId": "ea-build-before-source-change",
            "sourceRecordId": record["sourceRecordId"],
            "sourceRecordDigest": "f" * 64,
            "platform": "mt4",
            "brief": brief,
            "status": "reserved",
            "createdAt": "2026-08-24T02:00:00+00:00",
        }]

        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
            mock.patch.object(self.bridge, "_ea_factory_source_catalog", return_value=[record]),
            mock.patch.object(self.bridge, "_ea_factory_create_build_workspace") as create_workspace,
            mock.patch.object(self.bridge, "_ea_factory_source_report") as source_report,
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write_state,
        ):
            with self.assertRaises(self.bridge.RequestError) as raised:
                self.bridge.create_ea_factory_build(
                    {
                        "sourceRecordId": record["sourceRecordId"],
                        "platform": "mt4",
                        "brief": brief,
                        "idempotencyKey": "create-after-source-change",
                    }
                )

        self.assertEqual(raised.exception.status, 409)
        create_workspace.assert_not_called()
        source_report.assert_not_called()
        write_state.assert_not_called()
        self.assertEqual(state["builds"], [])

    def test_create_without_client_key_reserves_auto_identity_before_side_effect(self) -> None:
        record = self.normalized_record(source_key="sheet-auto-create-recovery")
        build_id = "ea-build-auto-create-recovery"
        brief = "recover omitted client key"
        state = self.empty_state()
        common_patches = (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
            mock.patch.object(self.bridge, "_ea_factory_source_catalog", return_value=[record]),
        )
        with (
            common_patches[0],
            common_patches[1],
            common_patches[2],
            common_patches[3],
            mock.patch.object(self.bridge, "safe_id", return_value=build_id),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write_state,
            mock.patch.object(
                self.bridge,
                "_ea_factory_create_build_workspace",
                side_effect=RuntimeError("simulated crash after durable reservation"),
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "simulated crash"):
                self.bridge.create_ea_factory_build({
                    "sourceRecordId": record["sourceRecordId"],
                    "platform": "mt4",
                    "brief": brief,
                })

        write_state.assert_called_once_with(state)
        self.assertEqual(len(state["createReservations"]), 1)
        reservation = state["createReservations"][0]
        self.assertEqual(reservation["buildId"], build_id)
        self.assertTrue(reservation["idempotencyKey"].startswith("ea-factory:auto-create:"))
        self.assertEqual(
            reservation["requestDigest"],
            self.bridge._ea_factory_create_request_digest(
                record["sourceRecordId"],
                "mt4",
                brief,
            ),
        )

        mission, report = self.strategy_stage_entities()
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
            mock.patch.object(self.bridge, "_ea_factory_source_catalog", return_value=[record]),
            mock.patch.object(self.bridge, "safe_id") as allocate_new_id,
            mock.patch.object(
                self.bridge,
                "_ea_factory_create_build_workspace",
                return_value=self.workspace_stub(build_id),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_source_report",
                return_value=(mission, report),
            ),
            mock.patch.object(self.bridge, "_ea_factory_register_artifacts", return_value=[]),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
            mock.patch.object(self.bridge, "append_audit"),
            mock.patch.object(
                self.bridge,
                "ea_factory_read_model",
                return_value={"builds": [{"id": build_id}]},
            ),
            mock.patch.object(self.bridge, "mission_read_model_item", side_effect=lambda item: item),
        ):
            recovered = self.bridge.create_ea_factory_build({
                "sourceRecordId": record["sourceRecordId"],
                "platform": "mt4",
                "brief": brief,
            })

        allocate_new_id.assert_not_called()
        self.assertEqual(recovered["build"]["id"], build_id)
        self.assertEqual(state["createReservations"], [])
        self.assertEqual(
            state["builds"][0]["createIdempotencyKey"],
            reservation["idempotencyKey"],
        )

    def test_pending_advance_retry_new_key_preserves_original_reservation_and_mission_key(self) -> None:
        build_id = "ea-build-pending-advance-retry"
        stages = self.bridge._ea_factory_initial_stages(
            "mt4",
            {"id": "mission-pending-strategy-spec"},
            {"id": "report-pending-strategy-spec"},
        )
        build = {
            "id": build_id,
            "platform": "mt4",
            "sourceRecordDigest": "a" * 64,
            "sourceReportId": "report-pending-strategy-spec",
            "brief": "pending advance recovery",
            "createRequestDigest": "b" * 64,
            "status": "ready",
            "stages": stages,
        }
        stage = self.bridge._ea_factory_stage_row(build, "generate_source")
        original_key = "advance-original-key"
        original_started_at = "2026-08-24T02:10:00+00:00"
        original_digest = self.bridge._ea_factory_advance_request_digest(
            build,
            "generate_source",
        )
        original_mission_key = self.bridge._ea_factory_stage_mission_idempotency_key(
            build_id,
            "generate_source",
            original_key,
        )
        stage.update({
            "status": "pending",
            "requestIdempotencyKey": original_key,
            "requestDigest": original_digest,
            "startedAt": original_started_at,
            "missionIdempotencyKey": original_mission_key,
        })
        state = {
            "schemaVersion": self.bridge.EA_FACTORY_STATE_SCHEMA_VERSION,
            "sourceSnapshots": [],
            "builds": [build],
            "createReservations": [],
            "updatedAt": None,
        }
        returned_model = {"builds": [{"id": build_id}]}

        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status", return_value=False),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write_state,
            mock.patch.object(
                self.bridge,
                "deliver_dashboard_report",
                return_value={"mission": {"id": "mission-transfer-pending-retry"}},
            ),
            mock.patch.object(
                self.bridge,
                "run_dashboard_workflow_action",
                return_value={
                    "ok": True,
                    "mission": {
                        "id": "mission-generation-pending-retry",
                        "status": "queued",
                    },
                },
            ) as dispatch,
            mock.patch.object(self.bridge, "_ea_factory_generation_brief", return_value="bound generation brief"),
            mock.patch.object(
                self.bridge,
                "_ea_factory_recover_false_approval_stage_mission",
                return_value=None,
            ),
            mock.patch.object(self.bridge, "append_audit"),
            mock.patch.object(self.bridge, "ea_factory_read_model", return_value=returned_model),
            mock.patch.object(self.bridge, "mission_read_model_item", side_effect=lambda item: item),
        ):
            result = self.bridge.advance_ea_factory_build(
                build_id,
                {
                    "stageId": "generate_source",
                    "idempotencyKey": "advance-new-browser-key",
                },
            )

        self.assertFalse(result["idempotentReplay"])
        self.assertEqual(result["kind"], "ea_factory_stage_dispatched")
        dispatched_request = dispatch.call_args.args[1]
        self.assertEqual(dispatched_request["idempotencyKey"], original_mission_key)
        self.assertEqual(stage["requestIdempotencyKey"], original_key)
        self.assertEqual(stage["requestDigest"], original_digest)
        self.assertEqual(stage["startedAt"], original_started_at)
        self.assertEqual(stage["missionIdempotencyKey"], original_mission_key)
        self.assertGreaterEqual(write_state.call_count, 2)

    def test_build_read_model_projects_adapter_attention_without_mutating_durable_status(self) -> None:
        cases = (
            ("mt4", "compile_validate"),
            ("mt5", "backtest_recheck"),
        )
        for platform, current_stage_id in cases:
            with self.subTest(platform=platform, stage=current_stage_id):
                stages = self.bridge._ea_factory_initial_stages(
                    platform,
                    {"id": f"mission-spec-{platform}"},
                    {"id": f"report-spec-{platform}"},
                )
                for stage in stages:
                    if stage["id"] == current_stage_id:
                        break
                    stage["status"] = "completed"
                    stage["evidenceVerified"] = True
                build = {
                    "id": f"ea-build-{platform}-adapter-attention",
                    "sourceRecordId": f"ea-source-{platform}-adapter-attention",
                    "sourceDisplayName": "Adapter attention projection",
                    "sourceRecordDigest": "a" * 64,
                    "platform": platform,
                    "brief": "read model only",
                    "status": "ready",
                    "workspace": {
                        "workspaceId": f"ea-workspace-{platform}-adapter-attention",
                        "folderNames": list(self.bridge.EA_FACTORY_BUILD_FOLDER_NAMES),
                        "strategySpecFile": "Source/strategy-spec-v01.json",
                        "rawFilesystemPathExposed": False,
                    },
                    "stages": stages,
                    "versions": [],
                    "createdAt": "2026-08-24T02:00:00+00:00",
                    "updatedAt": "2026-08-24T02:00:00+00:00",
                }
                durable_before = copy.deepcopy(build)
                with (
                    mock.patch.object(self.bridge, "_ea_factory_file_catalog", return_value=[]),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_terminal_gate",
                        return_value={
                            "required": True,
                            "ready": False,
                            "adapterReady": False,
                            "reasonCode": "terminal_execution_adapter_not_connected",
                        },
                    ),
                ):
                    projected = self.bridge._ea_factory_build_read_model(build)

                self.assertEqual(projected["status"], "attention_required")
                self.assertEqual(build, durable_before)
                self.assertEqual(build["status"], "ready")
                self.assertEqual(
                    self.bridge._ea_factory_stage_row(build, current_stage_id)["status"],
                    "pending",
                )

    def test_only_persisted_manifest_artifact_can_resolve_for_download(self) -> None:
        build_id = "ea-build-manifest-download-gate"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_dir = root / "workspace" / "ea-factory" / build_id
            for folder_name in self.bridge.EA_FACTORY_BUILD_FOLDER_NAMES:
                (build_dir / folder_name).mkdir(parents=True, exist_ok=True)
            registered_path = build_dir / "Reports" / "registered.json"
            rogue_path = build_dir / "Reports" / "rogue.json"
            registered_path.write_text('{"status":"registered"}\n', encoding="utf-8")
            rogue_path.write_text('{"status":"rogue"}\n', encoding="utf-8")
            build = {
                "id": build_id,
                "artifactManifest": [],
                "artifactManifestDigest": None,
            }

            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                registered = self.bridge._ea_factory_register_artifacts(
                    build,
                    [{
                        "relativePath": "Reports/registered.json",
                        "stageId": "final_report",
                        "reportId": "report-manifest-download-gate",
                        "artifactKind": "final_summary_json",
                    }],
                )[0]
                rogue = self.bridge._ea_factory_artifact_descriptor(
                    build_id,
                    "Reports/rogue.json",
                    stage_id="final_report",
                    report_id="report-manifest-download-gate",
                    artifact_kind="final_summary_json",
                )
                self.assertIsInstance(rogue, dict)
                self.assertEqual(registered["extension"], ".json")
                self.assertEqual(rogue["extension"], ".json")
                self.assertIn(".json", self.bridge.EA_FACTORY_DOWNLOAD_MEDIA_TYPES)

                state = {
                    "schemaVersion": self.bridge.EA_FACTORY_STATE_SCHEMA_VERSION,
                    "sourceSnapshots": [],
                    "builds": [build],
                    "createReservations": [],
                    "updatedAt": None,
                }
                with mock.patch.object(
                    self.bridge,
                    "_load_ea_factory_state_unlocked",
                    return_value=state,
                ):
                    self.assertIsNone(
                        self.bridge.resolve_ea_factory_file(
                            build_id,
                            str(rogue["fileId"]),
                        )
                    )
                    resolved = self.bridge.resolve_ea_factory_file(
                        build_id,
                        str(registered["fileId"]),
                    )

                self.assertIsNotNone(resolved)
                resolved_path, media_type, download_name = resolved
                self.assertEqual(resolved_path, registered_path.resolve(strict=True))
                self.assertEqual(media_type, "application/json")
                self.assertEqual(download_name, registered_path.name)
                catalog = self.bridge._ea_factory_file_catalog(build)
                self.assertEqual(
                    [item["fileId"] for item in catalog],
                    [registered["fileId"]],
                )
                self.assertNotIn("relativePath", catalog[0])
                self.assertEqual(
                    set(catalog[0]),
                    {
                        "fileId",
                        "fileName",
                        "folder",
                        "extension",
                        "byteSize",
                        "sha256",
                        "stageId",
                        "reportId",
                        "artifactKind",
                        "immutable",
                        "downloadUrl",
                    },
                )


if __name__ == "__main__":
    unittest.main()
