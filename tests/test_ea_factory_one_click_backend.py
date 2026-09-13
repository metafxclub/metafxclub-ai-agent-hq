from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import tempfile
import threading
import time
import unittest
import zlib
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_ea_factory_one_click_backend",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EaFactoryOneClickBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def build(self) -> dict:
        stages = []
        for stage_id in self.bridge.EA_FACTORY_STAGE_IDS:
            completed = stage_id == "strategy_spec"
            stages.append({
                "id": stage_id,
                "status": "completed" if completed else "pending",
                "missionId": "mission-spec" if completed else None,
                "reportId": "report-spec" if completed else None,
                "blockedReasonCode": None,
                "evidenceVerified": completed,
                "requestIdempotencyKey": None,
                "requestDigest": None,
                "missionIdempotencyKey": None,
                "manualRetryCount": 0,
                "manualRetryHistory": [],
                "artifacts": [],
                "updatedAt": "2026-09-11T00:00:00Z",
            })
        return {
            "schemaVersion": "ea-factory-build-v1",
            "id": "ea-build-one-click-test",
            "sourceRecordId": "deep-source-one-click",
            "sourceRecordDigest": "a" * 64,
            "createRequestDigest": "b" * 64,
            "coverageStatus": "compact_current",
            "coverageUpgradeRequired": False,
            "platform": "mt4",
            "artifactKind": "expert_advisor",
            "brief": "",
            "status": "ready",
            "workspace": {"folderNames": []},
            "stages": stages,
            "versions": [],
            "createdAt": "2026-09-11T00:00:00Z",
            "updatedAt": "2026-09-11T00:00:00Z",
        }

    def state(self, build: dict) -> dict:
        return {
            "schemaVersion": self.bridge.EA_FACTORY_STATE_SCHEMA_VERSION,
            "sourceSnapshots": [],
            "builds": [build],
            "createReservations": [],
            "updatedAt": None,
        }

    def compact_ea_manifest(self, source_digest: str = "d" * 64) -> dict:
        manifest = {
            "schemaVersion": self.bridge.EA_SOURCE_MANIFEST_SCHEMA_VERSION,
            "coverageMode": "compact_brief_digest_bound_structural_ea_review",
            "artifactKind": "expert_advisor",
            "targetPlatform": "mt4",
            "strategyBriefDigest": "1" * 64,
            "strategySpecDigest": "2" * 64,
            "sourceDigest": source_digest,
            "checks": {"completeStaticSourceContract": True},
            "coveredFields": list(self.bridge.COMPACT_SHEET_FIELDS),
            "missingFields": [],
            "findings": [],
            "complete": True,
        }
        manifest["manifestDigest"] = hashlib.sha256(json.dumps(
            manifest,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        return manifest

    def target(self) -> tuple[dict, dict]:
        return (
            {
                "record": {"runningState": "platform_running_detected"},
                "token": {},
            },
            {
                "platform": "mt4",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
        )

    def test_can_slim_tester_preset_requires_certified_v2_source_profile(self) -> None:
        build = self.build()
        with tempfile.TemporaryDirectory() as temporary:
            build_root = Path(temporary)
            versions = build_root / "EA_Versions"
            versions.mkdir()
            source_path = versions / "CAN_SLIM.mq4"
            source_text = (
                'const string CERTIFIED_PROFILE_VERSION = "can-slim-mt4-certified-v3";\n'
                "input double InpStopLossPercent = 7.5;\n"
                "input double RewardRiskRatio = 2;\n"
                "input double RiskPercent = 1;\n"
                "input int ExecutionBufferPoints = 2;\n"
                "input int SlippagePoints = 3;\n"
                "input int MaxOpenPositionsPerSymbolMagic = 1;\n"
                "input int MagicNumber = 4186001;\n"
                "input int DailyMAPeriod = 50;\n"
                "input int WeeklyMAPeriod = 50;\n"
                "input int FiftyTwoWeekLookback = 52;\n"
                "input bool FundamentalCriteriaConfirmed = false;\n"
                "input bool ExternalBenchmarkUptrendConfirmed = false;\n"
                "input int MaxSpreadPoints = 30;\n"
                "void OnTick(){\n"
                "  if(!FundamentalCriteriaConfirmed) return;\n"
                "  if(!ExternalBenchmarkUptrendConfirmed) return;\n"
                "}\n"
            )
            source_path.write_text(source_text, encoding="utf-8")
            build["versions"] = [{
                "sourceDigest": hashlib.sha256(source_path.read_bytes()).hexdigest(),
                "versionFile": "EA_Versions/CAN_SLIM.mq4",
            }]
            with mock.patch.object(
                self.bridge,
                "_ea_factory_build_directory",
                return_value=build_root,
            ):
                preset = self.bridge._ea_factory_can_slim_tester_input_preset(build)
                self.assertIsInstance(preset, dict)
                self.assertEqual(preset["scope"], "mt4_strategy_tester_only")
                self.assertTrue(preset["liveSourceDefaultsPreserved"])
                self.assertFalse(preset["liveTradingAllowed"])
                self.assertTrue(preset["fullCertifiedInputSnapshot"])
                self.assertEqual(len(preset["assumptions"]), 13)
                self.assertEqual(
                    [
                        item["testerValue"]
                        for item in preset["assumptions"]
                        if item["inputName"]
                        in self.bridge.EA_FACTORY_CAN_SLIM_SIMULATION_INPUT_NAMES
                    ],
                    [True, True],
                )
                self.assertEqual(
                    next(
                        item["testerValue"]
                        for item in preset["assumptions"]
                        if item["inputName"] == "MaxSpreadPoints"
                    ),
                    30,
                )

                spoofed_text = source_text.replace(
                    "  if(!ExternalBenchmarkUptrendConfirmed) return;\n",
                    "",
                )
                source_path.write_text(spoofed_text, encoding="utf-8")
                build["versions"][-1]["sourceDigest"] = hashlib.sha256(
                    source_path.read_bytes()
                ).hexdigest()
                self.assertIsNone(
                    self.bridge._ea_factory_can_slim_tester_input_preset(build)
                )

                comment_spoof_text = source_text.replace(
                    "  if(!ExternalBenchmarkUptrendConfirmed) return;\n",
                    "  // if(!ExternalBenchmarkUptrendConfirmed) return;\n",
                )
                source_path.write_text(comment_spoof_text, encoding="utf-8")
                build["versions"][-1]["sourceDigest"] = hashlib.sha256(
                    source_path.read_bytes()
                ).hexdigest()
                self.assertIsNone(
                    self.bridge._ea_factory_can_slim_tester_input_preset(build)
                )

                legacy_text = source_text.replace(
                    "can-slim-mt4-certified-v3",
                    "can-slim-mt4-certified-v1",
                )
                source_path.write_text(legacy_text, encoding="utf-8")
                build["versions"][-1]["sourceDigest"] = hashlib.sha256(
                    source_path.read_bytes()
                ).hexdigest()
                self.assertIsNone(
                    self.bridge._ea_factory_can_slim_tester_input_preset(build)
                )

    def test_generic_mt4_tester_preset_resets_every_input_and_simulates_only_proven_external_gate(self) -> None:
        build = self.build()
        with tempfile.TemporaryDirectory() as temporary:
            build_root = Path(temporary)
            versions = build_root / "EA_Versions"
            versions.mkdir()
            source_path = versions / "EMA_CROSS.mq4"
            source_text = (
                "input int FastPeriod = 10;\n"
                "input int SlowPeriod = 60;\n"
                "input double FixedLot = 0.01;\n"
                "input bool TradeOnNewBar = true;\n"
                "input bool EligibilityConfirmed = false;\n"
                "input bool EnableTrading = false;\n"
                "input bool ExternalLiveTradingEnabled = false;\n"
                "void OnTick(){\n"
                "  if(!EligibilityConfirmed) return;\n"
                "  if(!ExternalLiveTradingEnabled) return;\n"
                "}\n"
            )
            source_path.write_text(source_text, encoding="utf-8")
            build["versions"] = [{
                "sourceDigest": hashlib.sha256(source_path.read_bytes()).hexdigest(),
                "versionFile": "EA_Versions/EMA_CROSS.mq4",
            }]
            with mock.patch.object(
                self.bridge,
                "_ea_factory_build_directory",
                return_value=build_root,
            ):
                preset = self.bridge._ea_factory_mt4_tester_input_preset(build)
                self.assertEqual(len(preset["assumptions"]), 7)
                self.assertEqual(
                    preset["simulationInputNames"],
                    ["EligibilityConfirmed"],
                )
                by_name = {
                    item["inputName"]: item for item in preset["assumptions"]
                }
                self.assertEqual(by_name["FastPeriod"]["testerValue"], 10)
                self.assertEqual(by_name["FixedLot"]["testerValue"], 0.01)
                self.assertTrue(by_name["TradeOnNewBar"]["testerValue"])
                self.assertTrue(by_name["EligibilityConfirmed"]["testerValue"])
                self.assertFalse(by_name["EnableTrading"]["testerValue"])
                self.assertFalse(
                    by_name["ExternalLiveTradingEnabled"]["testerValue"]
                )
                self.assertRegex(preset["presetDigest"], r"^[0-9a-f]{64}$")

                source_path.write_text(
                    'input string Label = "unsupported";\nvoid OnTick(){}\n',
                    encoding="utf-8",
                )
                build["versions"][-1]["sourceDigest"] = hashlib.sha256(
                    source_path.read_bytes()
                ).hexdigest()
                with self.assertRaises(self.bridge.RequestError) as blocked:
                    self.bridge._ea_factory_mt4_tester_input_preset(build)
                self.assertEqual(blocked.exception.status, 409)

                source_path.write_text("void OnTick(){}\n", encoding="utf-8")
                build["versions"][-1]["sourceDigest"] = hashlib.sha256(
                    source_path.read_bytes()
                ).hexdigest()
                self.assertIsNone(
                    self.bridge._ea_factory_mt4_tester_input_preset(build)
                )

    def test_backtest_capability_requires_trade_row_evidence_not_logic_claim(self) -> None:
        capability = {
            "ready": True,
            "freshProcessProbe": True,
            "foregroundInteraction": True,
            "visibleEvidenceCapture": True,
            "terminalSelectionBound": True,
            "liveTradingAllowed": False,
            "terminalProcessMayRemainOpen": True,
            "processAndWindowBinding": True,
            "idempotentOperationBinding": True,
            "durableReceiptRecovery": True,
            "terminalShutdownAllowed": False,
            "autoTradingMayBeToggled": False,
            "chartAttachmentAllowed": False,
            "visibleStrategyTester": True,
            "visualModeRequired": True,
            "logicRecheckEvidence": True,
        }
        self.assertFalse(
            self.bridge._ea_factory_front_office_capability_ready(
                capability,
                "backtest_recheck",
            )
        )
        capability["testerTradeRowsEvidence"] = True
        self.assertTrue(
            self.bridge._ea_factory_front_office_capability_ready(
                capability,
                "backtest_recheck",
            )
        )

    def test_start_pins_terminal_and_dispatches_one_worker(self) -> None:
        build = self.build()
        state = self.state(build)
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write_state,
            mock.patch.object(self.bridge, "_ea_factory_metaeditor_target_context", return_value=self.target()),
            mock.patch.object(self.bridge, "_start_ea_factory_one_click_thread", return_value=True) as start,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            result = self.bridge.run_ea_factory_build_one_click(
                build["id"],
                {"idempotencyKey": "one-click-ui-001"},
            )
        self.assertEqual(result["kind"], "ea_factory_one_click_started")
        self.assertTrue(result["workerStarted"])
        self.assertEqual(result["oneClickRun"]["status"], "queued")
        self.assertFalse(result["oneClickRun"]["liveTradingAllowed"])
        self.assertTrue(result["oneClickRun"]["visualModeRequired"])
        binding = build["oneClickRun"]["terminalBinding"]
        self.assertEqual(binding["candidateId"], "mtc-one-click-terminal")
        self.assertEqual(binding["selectionRevision"], 7)
        self.assertEqual(binding["bindingDigest"], "c" * 64)
        write_state.assert_called_once()
        start.assert_called_once()
        self.assertEqual(start.call_args.args, (build["id"],))
        self.assertEqual(
            start.call_args.kwargs["expected_run_snapshot"]["runId"],
            build["oneClickRun"]["runId"],
        )
        validated = self.bridge._ea_factory_revalidated_one_click_run(build)
        self.assertEqual(validated["currentStageId"], "generate_source")

    def test_fresh_build_starts_after_atomic_strategy_spec(self) -> None:
        build = self.build()
        self.assertEqual(
            self.bridge._ea_factory_build_current_stage_id(build),
            "generate_source",
        )
        self.assertEqual(build["stages"][0]["id"], "strategy_spec")
        self.assertEqual(build["stages"][0]["status"], "completed")

    def test_same_key_resumes_visible_pause_but_different_key_is_rejected(self) -> None:
        build = self.build()
        now = "2026-09-11T00:00:00Z"
        build["oneClickRun"] = {
            "schemaVersion": self.bridge.EA_FACTORY_ONE_CLICK_SCHEMA_VERSION,
            "runId": "ea-run-one-click-test",
            "idempotencyKey": "one-click-ui-001",
            "requestDigest": self.bridge._ea_factory_one_click_request_digest(build),
            "status": "awaiting_visible_terminal",
            "currentStageId": "compile_validate",
            "terminalBinding": {
                "platform": "mt4",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "failureCode": None,
            "messageTh": "waiting",
            "startedAt": now,
            "updatedAt": now,
            "completedAt": None,
        }
        state = self.state(build)
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
            mock.patch.object(self.bridge, "_start_ea_factory_one_click_thread", return_value=True),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            resumed = self.bridge.run_ea_factory_build_one_click(
                build["id"],
                {"idempotencyKey": "one-click-ui-001"},
            )
            with self.assertRaises(self.bridge.RequestError) as error:
                self.bridge.run_ea_factory_build_one_click(
                    build["id"],
                    {"idempotencyKey": "another-owner"},
                )
        self.assertEqual(resumed["kind"], "ea_factory_one_click_resumed")
        self.assertEqual(build["oneClickRun"]["status"], "queued")
        self.assertEqual(error.exception.status, 409)

    def test_same_key_resumes_after_backend_heals_rejected_stage_evidence(self) -> None:
        build = self.build()
        for stage in build["stages"]:
            if stage["id"] == "generate_source":
                stage.update({
                    "status": "completed",
                    "missionId": f"mission-{stage['id']}",
                    "reportId": f"report-{stage['id']}",
                    "blockedReasonCode": None,
                    "evidenceVerified": True,
                })
            elif stage["id"] == "source_review":
                stage.update({
                    "status": "blocked",
                    "missionId": "mission-source_review",
                    "reportId": None,
                    "blockedReasonCode": "source_review_evidence_invalid",
                    "evidenceVerified": False,
                })
        now = "2026-09-11T00:00:00Z"
        build["oneClickRun"] = {
            "schemaVersion": self.bridge.EA_FACTORY_ONE_CLICK_SCHEMA_VERSION,
            "runId": "ea-run-one-click-healed-evidence",
            "idempotencyKey": "one-click-ui-healed-001",
            "requestDigest": self.bridge._ea_factory_one_click_request_digest(build),
            "status": "blocked",
            "currentStageId": "source_review",
            "terminalBinding": {
                "platform": "mt4",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "failureCode": "source_review_evidence_invalid",
            "messageTh": "blocked by older validator",
            "startedAt": now,
            "updatedAt": now,
            "completedAt": now,
        }
        state = self.state(build)

        def heal_review(candidate, **_kwargs):
            review = next(
                row for row in candidate["stages"] if row["id"] == "source_review"
            )
            review.update({
                "status": "completed",
                "reportId": "report-source_review",
                "blockedReasonCode": None,
                "evidenceVerified": True,
            })
            candidate["status"] = "ready"
            return True

        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(
                self.bridge,
                "_ea_factory_sync_build_status",
                side_effect=heal_review,
            ) as sync_status,
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write_state,
            mock.patch.object(self.bridge, "_start_ea_factory_one_click_thread", return_value=True) as start,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            resumed = self.bridge.run_ea_factory_build_one_click(
                build["id"],
                {"idempotencyKey": "one-click-ui-healed-001"},
            )
        self.assertEqual(resumed["kind"], "ea_factory_one_click_resumed")
        self.assertTrue(resumed["workerStarted"])
        self.assertEqual(build["oneClickRun"]["status"], "queued")
        self.assertEqual(build["oneClickRun"]["currentStageId"], "compile_validate")
        self.assertIsNone(build["oneClickRun"]["failureCode"])
        self.assertIsNone(build["oneClickRun"]["completedAt"])
        write_state.assert_called_once()
        start.assert_called_once()
        self.assertEqual(start.call_args.args, (build["id"],))
        self.assertEqual(
            start.call_args.kwargs["expected_run_snapshot"]["runId"],
            build["oneClickRun"]["runId"],
        )
        sync_status.assert_called_once_with(build, ingest_sources=True)

        uncertain = copy.deepcopy(build)
        uncertain["oneClickRun"].update({
            "status": "blocked",
            "currentStageId": "source_review",
            "failureCode": "source_review_evidence_invalid",
            "visibleAction": {
                "stageId": "compile_validate",
                "operationId": "ea-visible-uncertain",
                "state": "uncertain",
            },
        })
        uncertain_state = self.state(uncertain)
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=uncertain_state),
            mock.patch.object(
                self.bridge,
                "_ea_factory_sync_build_status",
                side_effect=heal_review,
            ),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as uncertain_write,
            mock.patch.object(self.bridge, "_start_ea_factory_one_click_thread") as uncertain_start,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            replayed = self.bridge.run_ea_factory_build_one_click(
                uncertain["id"],
                {"idempotencyKey": "one-click-ui-healed-001"},
            )
        self.assertEqual(replayed["kind"], "ea_factory_one_click_replayed")
        self.assertFalse(replayed["workerStarted"])
        uncertain_write.assert_called_once()
        uncertain_start.assert_not_called()

    def test_coordinator_advances_only_next_pending_stage(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="generate_source")
        state = self.state(build)
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status", return_value=False),
        ):
            action = self.bridge._ea_factory_one_click_next_action(build["id"])
        self.assertEqual(action["kind"], "advance")
        self.assertEqual(action["stageId"], "generate_source")
        self.assertEqual(build["oneClickRun"]["status"], "running")

    def test_terminal_stage_pauses_without_visible_adapter_and_does_not_mutate_stage(self) -> None:
        build = self.build()
        for stage in build["stages"]:
            if stage["id"] in {"generate_source", "source_review"}:
                stage["status"] = "completed"
                stage["evidenceVerified"] = True
        compile_stage = next(row for row in build["stages"] if row["id"] == "compile_validate")
        build["oneClickRun"] = self._run(build, current_stage="compile_validate")
        state = self.state(build)
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status", return_value=False),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_visible_gate",
                return_value={"ready": False, "reasonCode": "visible_terminal_adapter_not_connected"},
            ),
        ):
            action = self.bridge._ea_factory_one_click_next_action(build["id"])
        self.assertEqual(action["kind"], "awaiting_visible_terminal")
        self.assertEqual(build["oneClickRun"]["status"], "awaiting_visible_terminal")
        self.assertEqual(compile_stage["status"], "pending")
        self.assertIsNone(compile_stage["missionId"])
        self.assertFalse(compile_stage["evidenceVerified"])

    def test_visible_gate_rejects_old_hidden_compile_adapter(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="compile_validate")
        with (
            mock.patch.object(self.bridge, "_ea_factory_one_click_terminal_binding_current", return_value=True),
            mock.patch.object(self.bridge, "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER", None),
            mock.patch.object(self.bridge, "EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER", None),
        ):
            gate = self.bridge._ea_factory_one_click_visible_gate(build, "compile_validate")
        self.assertFalse(gate["ready"])
        self.assertEqual(gate["reasonCode"], "visible_terminal_adapter_not_connected")

    def test_adapter_platform_support_is_explicit_and_fail_closed(self) -> None:
        class Mt4OnlyAdapter:
            supported_platforms = frozenset({"mt4"})

            def capability_provider(self, **_kwargs):
                return {}

        adapter = Mt4OnlyAdapter()
        with mock.patch.object(
            self.bridge,
            "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
            adapter.capability_provider,
        ):
            self.assertEqual(
                self.bridge._ea_factory_front_office_supported_platforms(),
                frozenset({"mt4"}),
            )
        with mock.patch.object(
            self.bridge,
            "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
            lambda **_kwargs: {},
        ):
            self.assertEqual(
                self.bridge._ea_factory_front_office_supported_platforms(),
                frozenset(),
            )

        class OverclaimingAdapter:
            supported_platforms = frozenset({"mt4", "mt5"})

            def capability_provider(self, **_kwargs):
                return {}

        overclaiming = OverclaimingAdapter()
        with mock.patch.object(
            self.bridge,
            "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
            overclaiming.capability_provider,
        ):
            self.assertEqual(
                self.bridge._ea_factory_front_office_supported_platforms(),
                frozenset({"mt4"}),
            )

    def test_mt5_one_click_is_rejected_before_terminal_or_worker_action(self) -> None:
        build = self.build()
        build["platform"] = "mt5"
        state = self.state(build)
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_metaeditor_target_context",
            ) as resolve_target,
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_one_click_thread",
            ) as start,
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write,
        ):
            with self.assertRaises(self.bridge.RequestError) as error:
                self.bridge.run_ea_factory_build_one_click(
                    build["id"],
                    {"idempotencyKey": "one-click-ui-001"},
                )
        self.assertEqual(error.exception.status, 409)
        self.assertIn("manual stage-by-stage MT5", str(error.exception))
        resolve_target.assert_not_called()
        start.assert_not_called()
        write.assert_not_called()
        self.assertNotIn("oneClickRun", build)

    def test_mt4_one_click_requires_terminal_process_already_running(self) -> None:
        build = self.build()
        state = self.state(build)
        stopped_context, target = self.target()
        stopped_context["record"]["runningState"] = "not_running_detected"
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_metaeditor_target_context",
                return_value=(stopped_context, target),
            ),
            mock.patch.object(
                self.bridge,
                "_start_ea_factory_one_click_thread",
            ) as start,
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write,
        ):
            with self.assertRaises(self.bridge.RequestError) as error:
                self.bridge.run_ea_factory_build_one_click(
                    build["id"],
                    {"idempotencyKey": "one-click-ui-001"},
                )
        self.assertEqual(error.exception.status, 409)
        self.assertIn("must already be running", str(error.exception))
        start.assert_not_called()
        write.assert_not_called()
        self.assertNotIn("oneClickRun", build)

    def test_persisted_mt5_one_click_is_blocked_without_dispatch(self) -> None:
        build = self.build()
        build["platform"] = "mt5"
        build["oneClickRun"] = self._run(build, current_stage="generate_source")
        build["oneClickRun"]["terminalBinding"]["platform"] = "mt5"
        state = self.state(build)
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ) as write,
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status") as sync,
        ):
            action = self.bridge._ea_factory_one_click_next_action(build["id"])
        self.assertEqual(action["kind"], "blocked")
        self.assertEqual(
            action["reasonCode"],
            "one_click_visible_mt5_not_implemented",
        )
        self.assertEqual(build["oneClickRun"]["status"], "blocked")
        sync.assert_not_called()
        write.assert_called_once()

    def test_source_invalid_output_uses_existing_bounded_retry_path(self) -> None:
        build = self.build()
        source = next(row for row in build["stages"] if row["id"] == "generate_source")
        source.update({
            "status": "blocked",
            "blockedReasonCode": "invalid_output",
            "missionId": "mission-source-failed",
            "manualRetryCount": 1,
            "manualRetryHistory": [{"attempt": 1}],
        })
        build["oneClickRun"] = self._run(build, current_stage="generate_source")
        state = self.state(build)
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status", return_value=False),
        ):
            action = self.bridge._ea_factory_one_click_next_action(build["id"])
        self.assertEqual(action["kind"], "retry_source")
        self.assertEqual(action["failedMissionId"], "mission-source-failed")
        self.assertEqual(action["attempt"], 2)

    def test_restart_at_reserved_visible_stage_pauses_without_replaying_ui(self) -> None:
        build = self.build()
        for stage in build["stages"]:
            if stage["id"] in {"generate_source", "source_review"}:
                stage["status"] = "completed"
                stage["evidenceVerified"] = True
        build["oneClickRun"] = self._run(build, current_stage="compile_validate")
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        state = self.state(build)
        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write_state,
            mock.patch.object(self.bridge, "_start_ea_factory_one_click_thread") as start,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            resumed = self.bridge.resume_interrupted_ea_factory_one_click_runs()
        self.assertEqual(resumed, 0)
        start.assert_not_called()
        write_state.assert_called_once()
        self.assertEqual(build["oneClickRun"]["status"], "awaiting_visible_terminal")
        self.assertEqual(build["oneClickRun"]["visibleAction"]["state"], "uncertain")
        self.assertTrue(
            build["oneClickRun"]["visibleAction"]["requiresExplicitResume"]
        )

    def test_visible_failure_pauses_and_same_key_retries_same_operation(self) -> None:
        build = self.build()
        for stage in build["stages"]:
            if stage["id"] in {"generate_source", "source_review"}:
                stage["status"] = "completed"
                stage["evidenceVerified"] = True
        build["oneClickRun"] = self._run(build, current_stage="compile_validate")
        build["oneClickRun"]["status"] = "running"
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        operation_id = build["oneClickRun"]["visibleAction"]["operationId"]
        state = self.state(build)
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_next_action",
                return_value={
                    "kind": "advance",
                    "stageId": "compile_validate",
                    "runId": build["oneClickRun"]["runId"],
                },
            ),
            mock.patch.object(
                self.bridge,
                "advance_ea_factory_build",
                side_effect=self.bridge.RequestError(
                    "visible failure",
                    503,
                    code="compile_verification_failed",
                ),
            ),
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            self.bridge._ea_factory_one_click_worker(
                build["id"],
                copy.deepcopy(build["oneClickRun"]),
            )
        self.assertEqual(build["oneClickRun"]["status"], "awaiting_visible_terminal")
        self.assertEqual(build["oneClickRun"]["visibleAction"]["state"], "uncertain")
        self.assertEqual(
            build["oneClickRun"]["visibleAction"]["lastFailureCode"],
            "compile_verification_failed",
        )

        with (
            mock.patch.object(self.bridge, "_load_ea_factory_state_unlocked", return_value=state),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked"),
            mock.patch.object(self.bridge, "_start_ea_factory_one_click_thread", return_value=True),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            retried = self.bridge.run_ea_factory_build_one_click(
                build["id"],
                {"idempotencyKey": "one-click-ui-001"},
            )
        self.assertEqual(retried["kind"], "ea_factory_one_click_resumed")
        self.assertEqual(
            build["oneClickRun"]["visibleAction"]["operationId"],
            operation_id,
        )
        self.assertEqual(build["oneClickRun"]["visibleAction"]["attemptCount"], 2)

    def test_finish_persists_uncertain_visible_state_when_immutable_version_is_missing(self) -> None:
        build = self.build()
        build["createRequestDigest"] = self.bridge._ea_factory_create_request_digest(
            build["sourceRecordId"],
            build["platform"],
            build["brief"],
            build["artifactKind"],
        )
        build["versions"] = [{
            "version": 1,
            "fileName": "MissingEA.mq4",
            "sourceDigest": "d" * 64,
            "sourceFile": "Source/MissingEA.mq4",
            "versionFile": "EA_Versions/MissingEA_v01.mq4",
            "sourceReportId": "report-source-missing",
            "immutable": True,
            "createdAt": "2026-09-11T00:00:00Z",
        }]
        build["oneClickRun"] = self._run(
            build,
            current_stage="compile_validate",
        )
        build["oneClickRun"]["status"] = "running"
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        state = self.state(build)
        original_stages = copy.deepcopy(build["stages"])
        original_versions = copy.deepcopy(build["versions"])
        audit_events = []
        message_th = (
            "ตรวจผล Compile ไม่สำเร็จ ระบบหยุดไว้ก่อน "
            "และจะไม่กด Compile ซ้ำจนกว่าจะยืนยันผลเดิม"
        )

        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "ea-factory-state.json"
            backup_path = state_path.with_name(f"{state_path.name}.bak")
            backup_path.write_text("known-good-backup", encoding="utf-8")
            state_path.write_text(
                json.dumps(state, ensure_ascii=False),
                encoding="utf-8",
            )
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_state_path",
                    return_value=state_path,
                ),
                mock.patch.object(
                    self.bridge,
                    "_load_ea_factory_state_unlocked",
                    side_effect=self.bridge.DataIntegrityError(
                        "EA Factory immutable source versions failed integrity validation."
                    ),
                ),
                mock.patch.object(
                    self.bridge,
                    "_invalidate_ea_factory_state_cache",
                ),
                mock.patch.object(
                    self.bridge,
                    "_invalidate_ea_factory_read_model_cache",
                ),
                mock.patch.object(
                    self.bridge,
                    "append_audit",
                    side_effect=audit_events.append,
                ),
            ):
                self.bridge._ea_factory_one_click_finish(
                    build["id"],
                    expected_run_snapshot=copy.deepcopy(build["oneClickRun"]),
                    status="awaiting_visible_terminal",
                    current_stage_id="compile_validate",
                    failure_code="compile_verification_failed",
                    message_th=message_th,
                )

            stored = json.loads(state_path.read_text(encoding="utf-8"))
            backup_after = backup_path.read_text(encoding="utf-8")

        stored_build = stored["builds"][0]
        stored_run = stored_build["oneClickRun"]
        self.assertEqual(stored_run["status"], "awaiting_visible_terminal")
        self.assertIsNone(stored_run["failureCode"])
        self.assertEqual(stored_run["messageTh"], message_th)
        self.assertIsNone(stored_run["completedAt"])
        self.assertEqual(stored_run["visibleAction"]["state"], "uncertain")
        self.assertEqual(
            stored_run["visibleAction"]["lastFailureCode"],
            "compile_verification_failed",
        )
        self.assertTrue(
            stored_run["visibleAction"]["requiresExplicitResume"]
        )
        self.assertEqual(stored_build["stages"], original_stages)
        self.assertEqual(stored_build["versions"], original_versions)
        self.assertEqual(backup_after, "known-good-backup")
        self.assertTrue(audit_events[-1]["statePersisted"])
        self.assertEqual(
            audit_events[-1]["persistenceMode"],
            "fail_closed_raw_terminal_patch",
        )
        self.assertEqual(
            audit_events[-1]["finishExceptionClass"],
            "DataIntegrityError",
        )
        self.assertEqual(audit_events[-1]["visibleActionState"], "uncertain")

    def test_finish_falls_back_to_audit_without_leaving_worker_exception(self) -> None:
        audit_events = []
        message_th = "ระบบหยุดงานเพื่อความปลอดภัย กรุณาตรวจ Build ก่อนเริ่มใหม่"
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                side_effect=RuntimeError("primary state load failed"),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_finish_from_raw_state_unlocked",
                side_effect=self.bridge.DataIntegrityError(
                    "raw state is unsafe to update"
                ),
            ),
            mock.patch.object(
                self.bridge,
                "append_audit",
                side_effect=audit_events.append,
            ),
        ):
            self.bridge._ea_factory_one_click_finish(
                "ea-build-one-click-test",
                expected_run_snapshot={},
                status="blocked",
                current_stage_id="generate_source",
                failure_code="one_click_worker_exception",
                message_th=message_th,
            )

        self.assertEqual(len(audit_events), 1)
        self.assertFalse(audit_events[0]["statePersisted"])
        self.assertEqual(audit_events[0]["persistenceMode"], "audit_only")
        self.assertEqual(
            audit_events[0]["finishExceptionClass"],
            "DataIntegrityError",
        )
        self.assertEqual(audit_events[0]["messageTh"], message_th)
        self.assertFalse(audit_events[0]["liveTradingAllowed"])

    def test_next_action_integrity_error_finishes_before_audit_io(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(
            build,
            current_stage="generate_source",
        )
        expected_run = copy.deepcopy(build["oneClickRun"])
        call_order = []

        def finish(*_args, **_kwargs):
            call_order.append("finish")

        def failed_audit(_event):
            call_order.append("audit")
            raise OSError("audit disk unavailable")

        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_next_action",
                side_effect=self.bridge.DataIntegrityError(
                    "EA Factory immutable source versions failed integrity validation."
                ),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_finish",
                side_effect=finish,
            ) as finish_call,
            mock.patch.object(
                self.bridge,
                "append_audit",
                side_effect=failed_audit,
            ),
        ):
            self.bridge._ea_factory_one_click_worker(
                build["id"],
                expected_run,
            )

        self.assertEqual(call_order, ["finish", "audit"])
        finish_call.assert_called_once()
        finish_kwargs = finish_call.call_args.kwargs
        self.assertEqual(finish_kwargs["expected_run_snapshot"], expected_run)
        self.assertEqual(finish_kwargs["status"], "failed")
        self.assertEqual(finish_kwargs["current_stage_id"], "generate_source")
        self.assertEqual(
            finish_kwargs["failure_code"],
            "one_click_state_integrity_failed",
        )

    def test_stale_callback_cannot_downgrade_newer_raw_run(self) -> None:
        build = self.build()
        build["createRequestDigest"] = self.bridge._ea_factory_create_request_digest(
            build["sourceRecordId"],
            build["platform"],
            build["brief"],
            build["artifactKind"],
        )
        build["oneClickRun"] = self._run(
            build,
            current_stage="generate_source",
        )
        expected_old_run = copy.deepcopy(build["oneClickRun"])
        self.bridge._ea_factory_one_click_update(
            build["oneClickRun"],
            status="running",
            current_stage_id="generate_source",
            failure_code=None,
            message_th="งานรอบใหม่กำลังทำขั้นสร้าง Source",
        )
        state = self.state(build)
        audit_events = []

        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "ea-factory-state.json"
            state_path.write_text(
                json.dumps(state, ensure_ascii=False),
                encoding="utf-8",
            )
            before = state_path.read_bytes()
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_state_path",
                    return_value=state_path,
                ),
                mock.patch.object(
                    self.bridge,
                    "_load_ea_factory_state_unlocked",
                    side_effect=self.bridge.DataIntegrityError(
                        "EA Factory immutable source versions failed integrity validation."
                    ),
                ),
                mock.patch.object(
                    self.bridge,
                    "append_audit",
                    side_effect=audit_events.append,
                ),
            ):
                self.bridge._ea_factory_one_click_finish(
                    build["id"],
                    expected_run_snapshot=expected_old_run,
                    status="failed",
                    current_stage_id="generate_source",
                    failure_code="one_click_coordinator_failed",
                    message_th="callback เก่าต้องไม่ปิดงานรอบใหม่",
                )
            after = state_path.read_bytes()

        self.assertEqual(after, before)
        self.assertEqual(build["oneClickRun"]["status"], "running")
        self.assertFalse(audit_events[-1]["statePersisted"])
        self.assertEqual(audit_events[-1]["persistenceMode"], "audit_only")
        self.assertEqual(
            audit_events[-1]["finishExceptionClass"],
            "DataIntegrityError",
        )

    def test_integrity_failure_get_returns_actionable_fail_closed_result(self) -> None:
        handler = object.__new__(self.bridge.BridgeHandler)
        handler.path = "/api/props/right_server_racks/ea-factory"
        handler.validate_local_request = mock.Mock(return_value=None)
        handler.send_json = mock.Mock()
        with mock.patch.object(
            self.bridge,
            "ea_factory_read_model",
            side_effect=self.bridge.DataIntegrityError(
                "EA Factory immutable source versions failed integrity validation."
            ),
        ):
            handler._do_GET_guarded()

        handler.send_json.assert_called_once()
        result = handler.send_json.call_args.args[0]
        self.assertEqual(handler.send_json.call_args.kwargs["status"], 409)
        self.assertNotIn("_httpStatus", result)
        self.assertEqual(result["kind"], "ea_factory_integrity_blocked")
        self.assertEqual(result["code"], "ea_factory_artifact_integrity_failed")
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["oneClick"]["commandsAllowed"])
        self.assertEqual(result["oneClick"]["visibleActionState"], "uncertain")
        self.assertTrue(result["oneClick"]["requiresExplicitRecovery"])
        self.assertIn("ไฟล์หลักฐาน", result["messageTh"])
        self.assertIn("ไม่แน่นอน", result["messageTh"])
        self.assertNotIn("eaFactory", result)

    def test_visible_handler_receives_immutable_request_dto(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="compile_validate")
        build["oneClickRun"]["status"] = "running"
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        operation_id = build["oneClickRun"]["visibleAction"]["operationId"]
        request = {
            "stageId": "compile_validate",
            "platform": "mt4",
            "terminalBinding": copy.deepcopy(
                build["oneClickRun"]["terminalBinding"]
            ),
            "visibleOperation": copy.deepcopy(build["oneClickRun"]["visibleAction"]),
        }

        def complete(**kwargs):
            kwargs["request"]["visibleOperation"]["operationId"] = "mutated-copy"
            return {
                "schemaVersion": self.bridge.EA_FACTORY_VISIBLE_RESULT_SCHEMA_VERSION,
                "operationId": operation_id,
                "metrics": {
                    "compileVerified": True,
                    "processId": 123,
                    "processBinding": {
                        "terminalProcessId": 123,
                        "terminalWindowOwnerProcessId": 123,
                        "frontOfficeProcessId": 456,
                        "frontOfficeWindowOwnerProcessId": 456,
                    },
                },
                "artifactSpecifications": [
                    {
                        "alias": "compiled_binary",
                        "relativePath": "EA_Versions/test.ex4",
                        "artifactKind": "compile_evidence",
                    },
                    {
                        "alias": "visible_window",
                        "relativePath": "Screenshots/compile.png",
                        "artifactKind": "screenshot_evidence",
                    },
                    {
                        "alias": "compile_log",
                        "relativePath": "Reports/compile.txt",
                        "artifactKind": "compile_evidence",
                    },
                    {
                        "alias": "adapter_receipt",
                        "relativePath": "Reports/compile-receipt.json",
                        "artifactKind": "compile_evidence",
                    },
                ],
            }

        handler = mock.Mock(side_effect=complete)
        with (
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER",
                handler,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                return_value={
                    "ready": True,
                    "freshProcessProbe": True,
                    "foregroundInteraction": True,
                    "visibleEvidenceCapture": True,
                    "terminalSelectionBound": True,
                    "liveTradingAllowed": False,
                    "terminalProcessMayRemainOpen": True,
                    "processAndWindowBinding": True,
                    "idempotentOperationBinding": True,
                    "durableReceiptRecovery": True,
                    "terminalShutdownAllowed": False,
                    "autoTradingMayBeToggled": False,
                    "chartAttachmentAllowed": False,
                    "visibleMetaEditorCompile": True,
                },
            ),
        ):
            result = self.bridge._ea_factory_invoke_visible_front_office_handler(request)
        call = handler.call_args.kwargs
        self.assertEqual(
            call["request"]["visibleOperation"]["operationId"],
            "mutated-copy",
        )
        self.assertEqual(
            request["visibleOperation"]["operationId"],
            operation_id,
        )
        self.assertTrue(result["metrics"]["compileVerified"])
        self.assertEqual(result["metrics"]["processId"], 123)

    def test_visible_handler_rejects_non_contract_sensitive_metric(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="compile_validate")
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        operation_id = build["oneClickRun"]["visibleAction"]["operationId"]
        request = {
            "stageId": "compile_validate",
            "platform": "mt4",
            "terminalBinding": copy.deepcopy(
                build["oneClickRun"]["terminalBinding"]
            ),
            "visibleOperation": copy.deepcopy(build["oneClickRun"]["visibleAction"]),
        }
        raw = {
            "schemaVersion": self.bridge.EA_FACTORY_VISIBLE_RESULT_SCHEMA_VERSION,
            "operationId": operation_id,
            "metrics": {"compileVerified": True, "accountNumber": 123456},
            "artifactSpecifications": [
                {"alias": "compiled_binary", "relativePath": "EA_Versions/test.ex4", "artifactKind": "compile_evidence"},
                {"alias": "visible_window", "relativePath": "Screenshots/compile.png", "artifactKind": "screenshot_evidence"},
                {"alias": "compile_log", "relativePath": "Reports/compile.txt", "artifactKind": "compile_evidence"},
                {"alias": "adapter_receipt", "relativePath": "Reports/compile-receipt.json", "artifactKind": "compile_evidence"},
            ],
        }
        capability = {
            "ready": True,
            "freshProcessProbe": True,
            "foregroundInteraction": True,
            "visibleEvidenceCapture": True,
            "terminalSelectionBound": True,
            "liveTradingAllowed": False,
            "terminalProcessMayRemainOpen": True,
            "processAndWindowBinding": True,
            "idempotentOperationBinding": True,
            "durableReceiptRecovery": True,
            "terminalShutdownAllowed": False,
            "autoTradingMayBeToggled": False,
            "chartAttachmentAllowed": False,
            "visibleMetaEditorCompile": True,
        }
        with (
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER",
                return_value=raw,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                return_value=capability,
            ),
        ):
            with self.assertRaises(self.bridge.RequestError) as raised:
                self.bridge._ea_factory_invoke_visible_front_office_handler(request)
        self.assertEqual(raised.exception.status, 503)
        self.assertIn("invalid result envelope", str(raised.exception))

    def test_visible_private_metric_storage_preserves_only_positive_numeric_pids(self) -> None:
        stored = self.bridge._ea_factory_visible_metrics_storage({
            "processId": 123,
            "processBinding": {
                "terminalProcessId": 123,
                "terminalWindowOwnerProcessId": 123,
                "frontOfficeProcessId": 456,
                "frontOfficeWindowOwnerProcessId": 456,
            },
            "postProcessBinding": {"terminalProcessId": 123},
            "accountNumber": 999999,
            "password": "not-a-real-password",
        })
        self.assertEqual(stored["processId"], 123)
        self.assertEqual(stored["processBinding"]["frontOfficeProcessId"], 456)
        self.assertEqual(stored["accountNumber"], "[REDACTED_SECRET]")
        self.assertEqual(stored["password"], "[REDACTED_SECRET]")
        for invalid in (0, -1, True, "123"):
            self.assertEqual(
                self.bridge._ea_factory_visible_metrics_storage(
                    {"processId": invalid}
                )["processId"],
                "[REDACTED_SECRET]",
            )

    def test_trusted_visible_report_round_trip_retains_private_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            reports = Path(temporary) / "reports"
            reports.mkdir()
            payload = {
                "id": "report-eaf-visible-round-trip",
                "type": "ea_compile_report",
                "linkedMissionId": "mission-eaf-visible-round-trip",
                "status": "ready",
                "metrics": {
                    "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
                    "operationId": "ea-visible-round-trip",
                    "processId": 123,
                    "windowHandle": 456,
                    "processBinding": {
                        "terminalProcessId": 123,
                        "terminalWindowOwnerProcessId": 123,
                        "frontOfficeProcessId": 789,
                        "frontOfficeWindowOwnerProcessId": 789,
                    },
                    "postProcessBinding": {
                        "terminalProcessId": 123,
                        "terminalWindowOwnerProcessId": 123,
                        "frontOfficeProcessId": 789,
                        "frontOfficeWindowOwnerProcessId": 789,
                    },
                },
            }
            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", reports),
                mock.patch.object(self.bridge, "append_audit"),
            ):
                report = self.bridge.create_report(
                    payload,
                    queue_research_sheet=False,
                    _trusted_visible_process_identity=True,
                )
                persisted = self.bridge.read_json(
                    reports / "report-eaf-visible-round-trip.json",
                    None,
                )
            self.assertEqual(persisted, report)
            self.assertEqual(report["metrics"]["processId"], 123)
            self.assertEqual(
                report["metrics"]["processBinding"]["frontOfficeProcessId"],
                789,
            )
            public = self.bridge.report_read_model_item(report)
            self.assertNotIn("processId", public["metrics"])
            self.assertNotIn("processBinding", public["metrics"])

    def test_trusted_visible_report_round_trip_preserves_104_metric_contract(self) -> None:
        required_tail = {
            "staticSixGroupSourceContractVerified": True,
            "logicRecheck": {"verified": True},
            "logicRecheckDigest": "a" * 64,
            "logicRecheckVerified": True,
        }
        metrics = {
            "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "operationId": "ea-visible-104-metric-round-trip",
        }
        metrics.update({
            f"boundedMetric{index:03d}": index
            for index in range(97)
        })
        metrics["password"] = "not-a-real-password"
        metrics.update(required_tail)
        self.assertEqual(len(metrics), 104)
        self.assertEqual(list(metrics)[100:], list(required_tail))

        with tempfile.TemporaryDirectory() as temporary:
            reports = Path(temporary) / "reports"
            reports.mkdir()
            payload = {
                "id": "report-eaf-visible-104-metric-round-trip",
                "type": "ea_build_report",
                "linkedMissionId": "mission-eaf-visible-104-metric-round-trip",
                "status": "ready",
                "metrics": metrics,
            }
            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", reports),
                mock.patch.object(self.bridge, "append_audit"),
            ):
                report = self.bridge.create_report(
                    payload,
                    queue_research_sheet=False,
                    _trusted_visible_process_identity=True,
                )
                persisted = self.bridge.read_json(
                    reports / "report-eaf-visible-104-metric-round-trip.json",
                    None,
                )

        self.assertEqual(persisted, report)
        self.assertEqual(len(report["metrics"]), 104)
        self.assertEqual(list(report["metrics"])[100:], list(required_tail))
        self.assertEqual(report["metrics"]["password"], "[REDACTED_SECRET]")
        self.assertTrue(report["safety"]["secretRedacted"])
        for key, value in required_tail.items():
            self.assertEqual(report["metrics"][key], value)

    def test_trusted_visible_report_rejects_lossy_or_over_limit_metrics(self) -> None:
        exact_limit = self.bridge.EA_FACTORY_VISIBLE_METRICS_COLLECTION_LIMIT
        over_limit_metrics = {
            "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "operationId": "ea-visible-over-limit-metrics",
        }
        over_limit_metrics.update({
            f"boundedMetric{index:03d}": index
            for index in range(exact_limit - 1)
        })
        self.assertEqual(len(over_limit_metrics), exact_limit + 1)
        lossy_key_metrics = {
            "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "operationId": "ea-visible-lossy-metric-key",
            "x" * 121: "must-not-be-persisted",
        }
        nested_overlong_key_metrics = {
            "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "operationId": "ea-visible-nested-overlong-metric-key",
            "outer": {"x" * 121: "must-not-be-persisted"},
        }
        nested_colliding_key_metrics = {
            "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "operationId": "ea-visible-nested-colliding-metric-keys",
            "outer": {
                ("x" * 120) + "a": "first-must-not-be-persisted",
                ("x" * 120) + "b": "second-must-not-be-persisted",
            },
        }
        nested_non_string_key_metrics = {
            "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "operationId": "ea-visible-nested-non-string-metric-key",
            "outer": {1: "must-not-be-persisted"},
        }

        with tempfile.TemporaryDirectory() as temporary:
            reports = Path(temporary) / "reports"
            reports.mkdir()
            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", reports),
                mock.patch.object(self.bridge, "append_audit"),
            ):
                for report_id, metrics in (
                    ("report-eaf-visible-over-limit", over_limit_metrics),
                    ("report-eaf-visible-lossy-key", lossy_key_metrics),
                    (
                        "report-eaf-visible-nested-overlong-key",
                        nested_overlong_key_metrics,
                    ),
                    (
                        "report-eaf-visible-nested-colliding-keys",
                        nested_colliding_key_metrics,
                    ),
                    (
                        "report-eaf-visible-nested-non-string-key",
                        nested_non_string_key_metrics,
                    ),
                ):
                    with self.subTest(report_id=report_id):
                        with self.assertRaises(self.bridge.DataIntegrityError):
                            self.bridge.create_report(
                                {
                                    "id": report_id,
                                    "type": "ea_build_report",
                                    "status": "ready",
                                    "metrics": metrics,
                                },
                                queue_research_sheet=False,
                                _trusted_visible_process_identity=True,
                            )
                        self.assertFalse((reports / f"{report_id}.json").exists())

    def test_visible_retry_limit_allows_receipt_only_recovery_without_increment(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="compile_validate")
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        action = build["oneClickRun"]["visibleAction"]
        action.update({
            "attemptCount": self.bridge.EA_FACTORY_ONE_CLICK_VISIBLE_RETRY_LIMIT,
            "state": "uncertain",
            "requiresExplicitResume": True,
        })
        build["oneClickRun"]["status"] = "awaiting_visible_terminal"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            summaries = root / "Summaries"
            summaries.mkdir()
            receipt = summaries / (
                f"{action['operationId']}-compile-receipt.json"
            )
            receipt.write_text("{}", encoding="utf-8")
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_build_directory",
                    return_value=root,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_file_catalog",
                    return_value=[],
                ),
            ):
                self.assertTrue(
                    self.bridge._ea_factory_one_click_reserve_visible_action(
                        build,
                        build["oneClickRun"],
                        "compile_validate",
                        explicit_resume=True,
                    )
                )
                self.assertEqual(
                    action["attemptCount"],
                    self.bridge.EA_FACTORY_ONE_CLICK_VISIBLE_RETRY_LIMIT,
                )
                action.update({
                    "state": "uncertain",
                    "requiresExplicitResume": True,
                })
                model = self.bridge._ea_factory_one_click_read_model(build)
                self.assertTrue(model["canResume"])

            receipt.unlink()
            action.update({
                "state": "uncertain",
                "requiresExplicitResume": True,
            })
            with mock.patch.object(
                self.bridge,
                "_ea_factory_build_directory",
                return_value=root,
            ):
                self.assertFalse(
                    self.bridge._ea_factory_one_click_reserve_visible_action(
                        build,
                        build["oneClickRun"],
                        "compile_validate",
                        explicit_resume=True,
                    )
                )

    def test_visible_retry_budget_allows_only_one_gated_prestart_recovery(self) -> None:
        self.assertEqual(self.bridge.EA_FACTORY_ONE_CLICK_VISIBLE_RETRY_LIMIT, 3)
        self.assertEqual(self.bridge.EA_FACTORY_ONE_CLICK_PRESTART_RECOVERY_LIMIT, 4)
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="backtest_recheck")
        self.assertTrue(
            self.bridge._ea_factory_one_click_reserve_visible_action(
                build,
                build["oneClickRun"],
                "backtest_recheck",
            )
        )
        action = build["oneClickRun"]["visibleAction"]
        action.update({
            "attemptCount": self.bridge.EA_FACTORY_ONE_CLICK_VISIBLE_RETRY_LIMIT,
            "state": "uncertain",
            "lastFailureCode": "tester_input_file_name_identity_invalid",
            "requiresExplicitResume": True,
        })
        build["oneClickRun"]["status"] = "awaiting_visible_terminal"
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_durable_receipt_recovery_available",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_prestart_recovery_available",
                return_value=True,
            ),
        ):
            self.assertTrue(
                self.bridge._ea_factory_one_click_reserve_visible_action(
                    build,
                    build["oneClickRun"],
                    "backtest_recheck",
                    explicit_resume=True,
                )
            )
        self.assertEqual(
            action["attemptCount"],
            self.bridge.EA_FACTORY_ONE_CLICK_PRESTART_RECOVERY_LIMIT,
        )

        action.update({
            "state": "uncertain",
            "lastFailureCode": "tester_input_file_name_identity_invalid",
            "requiresExplicitResume": True,
        })
        with (
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_durable_receipt_recovery_available",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_prestart_recovery_available",
                return_value=True,
            ),
        ):
            self.assertFalse(
                self.bridge._ea_factory_one_click_reserve_visible_action(
                    build,
                    build["oneClickRun"],
                    "backtest_recheck",
                    explicit_resume=True,
                )
            )
        self.assertEqual(
            action["attemptCount"],
            self.bridge.EA_FACTORY_ONE_CLICK_PRESTART_RECOVERY_LIMIT,
        )

    def test_prestart_recovery_gate_requires_exact_artifacts_and_no_start_boundary(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(build, current_stage="backtest_recheck")
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "backtest_recheck",
        )
        run = build["oneClickRun"]
        action = run["visibleAction"]
        action.update({
            "attemptCount": self.bridge.EA_FACTORY_ONE_CLICK_VISIBLE_RETRY_LIMIT,
            "state": "uncertain",
            "lastFailureCode": "tester_input_file_name_identity_invalid",
            "requiresExplicitResume": True,
        })
        run["status"] = "awaiting_visible_terminal"
        operation_id = action["operationId"]
        binding = run["terminalBinding"]
        source_digest = "d" * 64
        binary = {
            "fileName": "Exact_EA_v01.ex4",
            "sha256": "e" * 64,
        }
        preset = {
            "sourceDigest": source_digest,
            "presetDigest": "f" * 64,
            "assumptions": [
                {
                    "inputName": "FixedLot",
                    "inputType": "double",
                    "testerValue": 0.01,
                },
                {
                    "inputName": "UseTrailing",
                    "inputType": "bool",
                    "testerValue": False,
                },
            ],
        }
        tester_settings = {
            "schemaVersion": self.bridge.EA_FACTORY_TESTER_SETTINGS_SCHEMA_VERSION,
            "expertFileName": binary["fileName"],
            "visualMode": True,
            "testerInputPreset": preset,
        }
        safety = {
            "liveTradingAllowed": False,
            "autoTradingMayBeToggled": False,
            "chartAttachmentAllowed": False,
            "terminalShutdownAllowed": False,
            "visualModeRequired": True,
            "optimizationAllowed": False,
        }
        identity_suffix = self.bridge.payload_digest(
            "ea-factory-visible-front-office-stage-v1",
            build["id"],
            "backtest_recheck",
            operation_id,
        )[:24]
        intent = {
            "schemaVersion": "ea-factory-visible-front-office-action-intent-v1",
            "operationId": operation_id,
            "stageId": "backtest_recheck",
            "sourceDigest": source_digest,
            "terminalCandidateId": binding["candidateId"],
            "terminalSelectionRevision": binding["selectionRevision"],
            "terminalBindingDigest": binding["bindingDigest"],
        }
        expert_ui_path = (
            f"Metafxclub\\AgentHQ\\{operation_id}\\Exact_EA_v01"
        )
        action_request = {
            "schemaVersion": "ea-factory-visible-backtest-action-request-v1",
            "protocolVersion": "durable-start-boundary-v1",
            "operationId": operation_id,
            "stageId": "backtest_recheck",
            "buildId": build["id"],
            "missionId": f"mission-eaf-{identity_suffix}",
            "reportId": f"report-eaf-{identity_suffix}",
            "terminalCandidateId": binding["candidateId"],
            "terminalSelectionRevision": binding["selectionRevision"],
            "terminalBindingDigest": binding["bindingDigest"],
            "sourceDigest": source_digest,
            "compiledBinarySha256": binary["sha256"],
            "expertFileName": binary["fileName"],
            "expertUiPathDigest": hashlib.sha256(
                expert_ui_path.encode("utf-8")
            ).hexdigest(),
            "testerSettingsDigest": self.bridge._ea_factory_canonical_json_sha256(
                tester_settings
            ),
            "testerInputPresetDigest": preset["presetDigest"],
            "safetyPolicyDigest": self.bridge._ea_factory_canonical_json_sha256(
                safety
            ),
        }
        action_request["actionRequestDigest"] = (
            self.bridge._ea_factory_canonical_json_sha256(action_request)
        )

        with tempfile.TemporaryDirectory() as temporary:
            build_root = Path(temporary)
            for name in ("Summaries", "Screenshots", "Reports", "Sets"):
                (build_root / name).mkdir()
            summaries = build_root / "Summaries"
            preset_path = build_root / "Sets" / (
                f"{operation_id}-tester-input-preset.set"
            )
            intent_path = summaries / f"{operation_id}-backtest-intent.json"
            request_path = summaries / (
                f"{operation_id}-backtest-action-request.json"
            )
            intent_path.write_text(
                json.dumps(intent, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            request_path.write_text(
                json.dumps(action_request, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            preset_path.write_bytes(
                b"FixedLot=0.01\r\nUseTrailing=false\r\n"
            )
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_build_directory",
                    return_value=build_root,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_backtest_binary",
                    return_value=binary,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_default_tester_settings",
                    return_value=tester_settings,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_file_catalog",
                    return_value=[],
                ),
            ):
                self.assertTrue(
                    self.bridge._ea_factory_one_click_prestart_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                model = self.bridge._ea_factory_one_click_read_model(build)
                self.assertTrue(model["canResume"])
                self.assertEqual(model["visibleAction"]["attemptLimit"], 4)

                legacy_report = build_root / "Reports" / (
                    f"{operation_id}-tester.html"
                )
                legacy_report.write_text("legacy partial report", encoding="utf-8")
                self.assertFalse(
                    self.bridge._ea_factory_one_click_prestart_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                legacy_report.unlink()

                preset_path.write_bytes(
                    b"FixedLot=0.02\r\nUseTrailing=false\r\n"
                )
                self.assertFalse(
                    self.bridge._ea_factory_one_click_prestart_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                preset_path.write_bytes(
                    b"FixedLot=0.01\r\nUseTrailing=false\r\n"
                )

                boundary = summaries / (
                    f"{operation_id}-backtest-start-boundary.json"
                )
                boundary.write_text("{}", encoding="utf-8")
                self.assertFalse(
                    self.bridge._ea_factory_one_click_prestart_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                blocked_model = self.bridge._ea_factory_one_click_read_model(build)
                self.assertFalse(blocked_model["canResume"])
                self.assertEqual(blocked_model["visibleAction"]["attemptLimit"], 3)

                expected_boundary = {
                    "schemaVersion": "ea-factory-tester-start-boundary-v1",
                    "operationId": operation_id,
                    "stageId": "backtest_recheck",
                    "actionRequestDigest": action_request["actionRequestDigest"],
                }
                boundary.write_text(
                    json.dumps(expected_boundary, sort_keys=True, separators=(",", ":")),
                    encoding="utf-8",
                )
                png = b"\x89PNG\r\n\x1a\n" + (b"\x00" * 1016)
                (build_root / "Screenshots" / f"{operation_id}-tester-settings.png").write_bytes(png)
                (build_root / "Screenshots" / f"{operation_id}-tester-input-preset.png").write_bytes(png)
                (build_root / "Sets" / f"{operation_id}-tester-input-readback.set").write_bytes(
                    b"FixedLot=0.01\r\nUseTrailing=false\r\n"
                )
                action.update({
                    "attemptCount": self.bridge.EA_FACTORY_ONE_CLICK_PRESTART_RECOVERY_LIMIT,
                    "state": "uncertain",
                    "lastFailureCode": "visible_ui_timeout",
                    "requiresExplicitResume": True,
                })
                self.assertTrue(
                    self.bridge._ea_factory_one_click_inflight_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                legacy_report.write_text("legacy partial report", encoding="utf-8")
                self.assertFalse(
                    self.bridge._ea_factory_one_click_inflight_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                legacy_report.unlink()
                for collection_failure in (
                    "control_1034_ambiguous",
                    "tester_settings_tab_unavailable",
                    "tester_settings_tab_strip_ambiguous",
                    "tester_settings_tab_strip_invalid",
                    "tester_settings_tab_scan_binding_changed",
                    "tester_settings_start_ambiguous",
                    "tester_settings_start_binding_mismatch",
                ):
                    action["lastFailureCode"] = collection_failure
                    self.assertTrue(
                        self.bridge._ea_factory_one_click_inflight_recovery_available(
                            build,
                            "backtest_recheck",
                            action,
                        ),
                        collection_failure,
                    )
                action["lastFailureCode"] = "visible_ui_timeout"
                inflight_model = self.bridge._ea_factory_one_click_read_model(build)
                self.assertTrue(inflight_model["canResume"])
                self.assertEqual(inflight_model["visibleAction"]["attemptLimit"], 4)
                self.assertTrue(
                    self.bridge._ea_factory_one_click_reserve_visible_action(
                        build,
                        run,
                        "backtest_recheck",
                        explicit_resume=True,
                    )
                )
                self.assertEqual(action["attemptCount"], 4)

                action.update({
                    "state": "uncertain",
                    "lastFailureCode": "visible_ui_timeout",
                    "requiresExplicitResume": True,
                })
                result_path = build_root / "Screenshots" / (
                    f"{operation_id}-tester-result.png"
                )
                report_proof_path = build_root / "Screenshots" / (
                    f"{operation_id}-tester-report.png"
                )
                report_path = build_root / "Reports" / (
                    f"{operation_id}-tester.htm"
                )
                collected_response_path = summaries / (
                    f"{operation_id}-backtest-ui-collected-recovery.json"
                )
                result_path.write_bytes(png)
                report_proof_path.write_bytes(png)
                valid_report = (
                    b"<!DOCTYPE html><html><body><table>"
                    + (b"x" * 1024)
                    + b"</table></body></html>"
                )
                report_path.write_bytes(valid_report)
                self.assertTrue(
                    self.bridge._ea_factory_one_click_collected_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                collected_model = self.bridge._ea_factory_one_click_read_model(build)
                self.assertTrue(collected_model["canResume"])
                self.assertTrue(
                    self.bridge._ea_factory_one_click_reserve_visible_action(
                        build,
                        run,
                        "backtest_recheck",
                        explicit_resume=True,
                    )
                )
                self.assertEqual(
                    action["attemptCount"],
                    self.bridge.EA_FACTORY_ONE_CLICK_PRESTART_RECOVERY_LIMIT,
                )
                action.update({
                    "state": "uncertain",
                    "lastFailureCode": "tester_report_path_not_committed",
                    "requiresExplicitResume": True,
                })

                for conflicting_output_path in (
                    summaries / f"{operation_id}-backtest-receipt.json",
                    summaries / f"{operation_id}-backtest-ui.json",
                    summaries / f"{operation_id}-backtest-ui-inflight-recovery.json",
                    summaries / f"{operation_id}-backtest-ui-completed-recovery.json",
                    collected_response_path,
                ):
                    conflicting_output_path.write_text("{}", encoding="utf-8")
                    self.assertFalse(
                        self.bridge._ea_factory_one_click_collected_recovery_available(
                            build,
                            "backtest_recheck",
                            action,
                        ),
                        conflicting_output_path.name,
                    )
                    conflicting_output_path.unlink()

                legacy_report.write_text("legacy partial report", encoding="utf-8")
                self.assertFalse(
                    self.bridge._ea_factory_one_click_collected_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                legacy_report.unlink()

                report_proof_path.unlink()
                self.assertFalse(
                    self.bridge._ea_factory_one_click_collected_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                report_proof_path.write_bytes(png)

                readback_path = build_root / "Sets" / (
                    f"{operation_id}-tester-input-readback.set"
                )
                readback_bytes = readback_path.read_bytes()
                readback_path.write_bytes(
                    b"FixedLot=0.02\r\nUseTrailing=false\r\n"
                )
                self.assertFalse(
                    self.bridge._ea_factory_one_click_collected_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                readback_path.write_bytes(readback_bytes)

                report_path.write_bytes(b"not-html" + (b"x" * 1024))
                self.assertFalse(
                    self.bridge._ea_factory_one_click_collected_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                report_path.write_bytes(valid_report)

                report_path.unlink()
                report_path.mkdir()
                self.assertFalse(
                    self.bridge._ea_factory_one_click_collected_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                report_path.rmdir()
                report_path.write_bytes(valid_report)

                boundary_epoch = boundary.stat().st_mtime
                too_old = boundary_epoch - 5
                os.utime(report_path, (too_old, too_old))
                self.assertFalse(
                    self.bridge._ea_factory_one_click_collected_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                future = time.time() + 120
                os.utime(report_path, (future, future))
                self.assertFalse(
                    self.bridge._ea_factory_one_click_collected_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                os.utime(report_path, None)

                result_path.unlink()
                report_proof_path.unlink()
                report_path.unlink()
                boundary.write_text("{}", encoding="utf-8")
                self.assertFalse(
                    self.bridge._ea_factory_one_click_inflight_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )
                boundary.unlink()

                action["lastFailureCode"] = "unknown_visible_failure"
                self.assertFalse(
                    self.bridge._ea_factory_one_click_prestart_recovery_available(
                        build,
                        "backtest_recheck",
                        action,
                    )
                )

    def test_visible_front_office_actions_are_serialized_across_builds(self) -> None:
        operation_id = "ea-visible-333333333333333333333333"
        request = {
            "stageId": "compile_validate",
            "platform": "mt4",
            "terminalBinding": {
                "platform": "mt4",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "visibleOperation": {"operationId": operation_id},
        }
        capability = {
            "ready": True,
            "freshProcessProbe": True,
            "foregroundInteraction": True,
            "visibleEvidenceCapture": True,
            "terminalSelectionBound": True,
            "liveTradingAllowed": False,
            "terminalProcessMayRemainOpen": True,
            "processAndWindowBinding": True,
            "idempotentOperationBinding": True,
            "durableReceiptRecovery": True,
            "terminalShutdownAllowed": False,
            "autoTradingMayBeToggled": False,
            "chartAttachmentAllowed": False,
            "visibleMetaEditorCompile": True,
        }
        started = threading.Event()
        release = threading.Event()
        outcomes: list[object] = []

        def handler(*, request):
            started.set()
            self.assertTrue(release.wait(timeout=5))
            return {
                "schemaVersion": self.bridge.EA_FACTORY_VISIBLE_RESULT_SCHEMA_VERSION,
                "operationId": operation_id,
                "metrics": {"compileVerified": True},
                "artifactSpecifications": [
                    {"alias": "compiled_binary", "relativePath": "EA_Versions/test.ex4", "artifactKind": "compile_evidence"},
                    {"alias": "visible_window", "relativePath": "Screenshots/compile.png", "artifactKind": "screenshot_evidence"},
                    {"alias": "compile_log", "relativePath": "Reports/compile.txt", "artifactKind": "compile_evidence"},
                    {"alias": "adapter_receipt", "relativePath": "Reports/compile.json", "artifactKind": "compile_evidence"},
                ],
            }

        def first_worker():
            try:
                outcomes.append(
                    self.bridge._ea_factory_invoke_visible_front_office_handler(
                        copy.deepcopy(request)
                    )
                )
            except Exception as error:  # pragma: no cover - asserted below
                outcomes.append(error)

        provider = mock.Mock(return_value=capability)
        visible_handler = mock.Mock(side_effect=handler)
        with (
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER",
                visible_handler,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                provider,
            ),
        ):
            worker = threading.Thread(target=first_worker, daemon=True)
            worker.start()
            self.assertTrue(started.wait(timeout=5))
            with self.assertRaises(self.bridge.RequestError) as busy:
                self.bridge._ea_factory_invoke_visible_front_office_handler(
                    copy.deepcopy(request)
                )
            self.assertEqual(busy.exception.status, 409)
            release.set()
            worker.join(timeout=5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(outcomes), 1)
        self.assertIsInstance(outcomes[0], dict)
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(visible_handler.call_count, 1)

    def test_visible_adapter_failure_preserves_bounded_public_reason_code(self) -> None:
        operation_id = "ea-visible-444444444444444444444444"
        request = {
            "stageId": "compile_validate",
            "platform": "mt4",
            "terminalBinding": {
                "platform": "mt4",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "visibleOperation": {"operationId": operation_id},
        }
        capability = {
            "ready": True,
            "freshProcessProbe": True,
            "foregroundInteraction": True,
            "visibleEvidenceCapture": True,
            "terminalSelectionBound": True,
            "liveTradingAllowed": False,
            "terminalProcessMayRemainOpen": True,
            "processAndWindowBinding": True,
            "idempotentOperationBinding": True,
            "durableReceiptRecovery": True,
            "terminalShutdownAllowed": False,
            "autoTradingMayBeToggled": False,
            "chartAttachmentAllowed": False,
            "visibleMetaEditorCompile": True,
        }
        failure = self.bridge.VisibleTerminalAdapterError(
            "visible_ui_timeout",
            retryable=True,
        )
        with (
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER",
                side_effect=failure,
            ),
            mock.patch.object(
                self.bridge,
                "EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER",
                return_value=capability,
            ),
        ):
            with self.assertRaises(self.bridge.RequestError) as raised:
                self.bridge._ea_factory_invoke_visible_front_office_handler(
                    request,
                )
        self.assertEqual(raised.exception.status, 503)
        self.assertEqual(raised.exception.code, "visible_ui_timeout")
        self.assertTrue(raised.exception.retryable)

    def test_backtest_evidence_accepts_consistent_zero_with_attention_and_nonzero(self) -> None:
        build = self.build()
        build["blueprintCoverageManifest"] = self.compact_ea_manifest()
        build["versions"] = [{
            "sourceDigest": "d" * 64,
            "versionFile": "EA_Versions/CAN_SLIM.mq4",
        }]
        stage = next(row for row in build["stages"] if row["id"] == "backtest_recheck")
        stage.update({
            "status": "completed",
            "evidenceVerified": True,
            "missionId": "mission-backtest",
            "reportId": "report-backtest",
            "artifacts": [
                "shot-settings",
                "shot-result",
                "shot-report-proof",
                "tester-report",
                "adapter-receipt",
            ],
            "terminalExecutableSha256": "4" * 64,
            "frontOfficeExecutableSha256": "4" * 64,
        })
        build["oneClickRun"] = self._run(build, current_stage="backtest_recheck")
        operation_id = self.bridge._ea_factory_one_click_visible_operation_id(
            build,
            build["oneClickRun"],
            "backtest_recheck",
        )
        manifest = [
            {"fileId": "binary", "fileName": "CAN_SLIM.ex4", "stageId": "compile_validate", "reportId": "report-compile", "artifactKind": "compile_evidence", "extension": ".ex4", "sha256": "e" * 64},
            {"fileId": "shot-settings", "stageId": "backtest_recheck", "reportId": "report-backtest", "artifactKind": "screenshot_evidence", "extension": ".png", "sha256": "1" * 64},
            {"fileId": "shot-result", "stageId": "backtest_recheck", "reportId": "report-backtest", "artifactKind": "screenshot_evidence", "extension": ".png", "sha256": "2" * 64},
            {"fileId": "shot-report-proof", "stageId": "backtest_recheck", "reportId": "report-backtest", "artifactKind": "screenshot_evidence", "extension": ".png", "sha256": "9" * 64},
            {"fileId": "tester-report", "stageId": "backtest_recheck", "reportId": "report-backtest", "artifactKind": "backtest_evidence", "extension": ".html", "sha256": "3" * 64},
            {"fileId": "adapter-receipt", "stageId": "backtest_recheck", "reportId": "report-backtest", "artifactKind": "backtest_evidence", "extension": ".json", "sha256": "a" * 64},
        ]
        stage_entries = manifest[1:]
        tester_request = {
            "schemaVersion": self.bridge.EA_FACTORY_TESTER_SETTINGS_SCHEMA_VERSION,
            "expertFileName": "CAN_SLIM.ex4",
            "symbolPolicy": "current_tester_selection_required",
            "period": "H1",
            "model": "every_tick",
            "spreadPolicy": "current",
            "useDate": False,
            "fromDate": None,
            "toDate": None,
            "depositPolicy": "current_tester_deposit",
            "visualMode": True,
            "optimizationEnabled": False,
            "shutdownTerminalAfterTest": False,
            "liveTradingAllowed": False,
        }
        tester_request_digest = self.bridge.payload_digest(
            "ea-factory-tester-settings-request-v1",
            tester_request,
        )
        stage["testerSettingsRequestDigest"] = tester_request_digest
        process_binding = {
            "schemaVersion": "ea-factory-front-office-process-binding-v1",
            "observedAt": "2026-09-11T00:00:00Z",
            "stageId": "backtest_recheck",
            "terminalCandidateId": "mtc-one-click-terminal",
            "terminalSelectionRevision": 7,
            "terminalBindingDigest": "c" * 64,
            "terminalProcessId": 123,
            "terminalExecutableSha256": "4" * 64,
            "terminalWindowHandle": 456,
            "terminalWindowOwnerProcessId": 123,
            "terminalWindowTitleSha256": "5" * 64,
            "terminalWindowClassSha256": "6" * 64,
            "frontOfficeKind": "strategy_tester",
            "frontOfficeProcessId": 123,
            "frontOfficeExecutableSha256": "4" * 64,
            "frontOfficeWindowHandle": 456,
            "frontOfficeWindowOwnerProcessId": 123,
            "frontOfficeWindowTitleSha256": "7" * 64,
            "frontOfficeWindowClassSha256": "8" * 64,
            "processBindingDigest": "",
        }
        process_binding["processBindingDigest"] = (
            self.bridge._ea_factory_front_office_process_binding_digest(
                process_binding
            )
        )
        metrics = {
            "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "operationId": operation_id,
            "eaFactoryStage": "backtest_recheck",
            "platform": "mt4",
            "terminalCandidateId": "mtc-one-click-terminal",
            "terminalSelectionRevision": 7,
            "terminalBindingDigest": "c" * 64,
            "processBinding": copy.deepcopy(process_binding),
            "processBindingDigest": process_binding["processBindingDigest"],
            "postProcessBinding": copy.deepcopy(process_binding),
            "postProcessBindingDigest": process_binding["processBindingDigest"],
            "liveTradingExecuted": False,
            "autoTradingToggled": False,
            "autoTradingStateBefore": True,
            "autoTradingStateAfter": True,
            "chartAttached": False,
            "terminalClosedByAdapter": False,
            "terminalStillRunning": True,
            "terminalStillOpen": True,
            "processId": 123,
            "windowHandle": 456,
            "capabilityCheckedAt": "2026-09-11T00:00:00Z",
            "evidenceArtifactIds": list(stage["artifacts"]),
            "stageArtifactManifestDigest": self.bridge._ea_factory_visible_stage_manifest_digest(stage_entries),
            "sourceDigest": "d" * 64,
            "compiledBinaryFileId": "binary",
            "compiledBinarySha256": "e" * 64,
            "visibleWindowEvidenceFileId": "shot-result",
            "visibleWindowEvidenceSha256": "2" * 64,
            "settingsScreenshotFileId": "shot-settings",
            "settingsScreenshotSha256": "1" * 64,
            "resultScreenshotFileId": "shot-result",
            "resultScreenshotSha256": "2" * 64,
            "reportScreenshotFileId": "shot-report-proof",
            "reportScreenshotSha256": "9" * 64,
            "testerReportFileId": "tester-report",
            "testerReportSha256": "3" * 64,
            "adapterReceiptFileId": "adapter-receipt",
            "adapterReceiptSha256": "a" * 64,
            "expertFileName": "CAN_SLIM.ex4",
            "testerSettingsRequestDigest": tester_request_digest,
            "resolvedTesterSettings": {
                "schemaVersion": self.bridge.EA_FACTORY_RESOLVED_TESTER_SETTINGS_SCHEMA_VERSION,
                "expertFileName": "CAN_SLIM.ex4",
                "symbol": "EURUSD",
                "period": "H1",
                "model": "every_tick",
                "spread": "current",
                "useDate": False,
                "fromDate": None,
                "toDate": None,
                "deposit": 10000.0,
                "visualMode": True,
                "optimizationEnabled": False,
                "shutdownTerminalAfterTest": False,
            },
            "visibleStrategyTester": True,
            "visualMode": True,
            "optimizationEnabled": False,
            "backtestVerified": True,
            "backtestExecuted": True,
            "recoveredExistingReceipt": False,
            "testerTradeRowsVerified": True,
            "fullDynamicSixGroupVerified": False,
            "zeroTrade": True,
            "mismatchedChartErrors": 0,
            "historyQualityIssue": False,
            "historyQualityVerified": True,
            "attentionRequired": True,
            "attentionReasonCode": "backtest_zero_trades",
            "executionOutcome": "completed_zero_trades",
            "performanceEvaluationAvailable": False,
            "tradeCount": 0,
            "buyTradeCount": 0,
            "sellTradeCount": 0,
            "tradeRowCount": 0,
        }
        metrics.update(
            self.bridge._ea_factory_logic_recheck_projection(build, metrics)
        )
        metrics["resolvedTesterSettingsDigest"] = self.bridge.payload_digest(
            "ea-factory-resolved-tester-settings-v1",
            metrics["resolvedTesterSettings"],
        )
        report = {
            "id": "report-backtest",
            "status": "ready",
            "linkedMissionId": "mission-backtest",
            "metrics": metrics,
        }
        with tempfile.TemporaryDirectory() as temporary:
            report_dir = Path(temporary)
            (report_dir / "report-backtest.json").write_text(
                json.dumps(report),
                encoding="utf-8",
            )
            with (
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", report_dir),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_revalidated_artifact_manifest",
                    return_value=manifest,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_visible_artifact_payload",
                    return_value=b"verified",
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_visible_png_valid",
                    return_value=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_tester_report_matches",
                    return_value=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_visible_receipt_valid",
                    return_value=True,
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_default_tester_settings",
                    return_value=copy.deepcopy(tester_request),
                ),
            ):
                self.assertTrue(
                    self.bridge._ea_factory_visible_front_office_evidence_valid(
                        build,
                        stage,
                        {"id": "mission-backtest"},
                        report,
                        expected_operation_id=operation_id,
                    )
                )
                metrics.update({
                    "zeroTrade": False,
                    "mismatchedChartErrors": 0,
                    "historyQualityIssue": False,
                    "historyQualityVerified": True,
                    "attentionRequired": False,
                    "attentionReasonCode": None,
                    "executionOutcome": "completed_with_trades",
                    "performanceEvaluationAvailable": True,
                    "tradeCount": 1,
                    "buyTradeCount": 1,
                    "sellTradeCount": 0,
                    "tradeRowCount": 1,
                    "testerTradeRowsVerified": True,
                    "fullDynamicSixGroupVerified": False,
                })
                valid_truth_projection = (
                    self.bridge._ea_factory_logic_recheck_projection(
                        build,
                        metrics,
                    )
                )
                metrics.update(valid_truth_projection)
                (report_dir / "report-backtest.json").write_text(
                    json.dumps(report),
                    encoding="utf-8",
                )
                self.assertTrue(
                    self.bridge._ea_factory_visible_front_office_evidence_valid(
                        build,
                        stage,
                        {"id": "mission-backtest"},
                        report,
                        expected_operation_id=operation_id,
                    )
                )

                metrics.update(
                    self.bridge._ea_factory_backtest_attention_fields(False, 17)
                )
                (report_dir / "report-backtest.json").write_text(
                    json.dumps(report),
                    encoding="utf-8",
                )
                self.assertTrue(
                    self.bridge._ea_factory_visible_front_office_evidence_valid(
                        build,
                        stage,
                        {"id": "mission-backtest"},
                        report,
                        expected_operation_id=operation_id,
                    )
                )
                metrics["performanceEvaluationAvailable"] = True
                (report_dir / "report-backtest.json").write_text(
                    json.dumps(report),
                    encoding="utf-8",
                )
                self.assertFalse(
                    self.bridge._ea_factory_visible_front_office_evidence_valid(
                        build,
                        stage,
                        {"id": "mission-backtest"},
                        report,
                        expected_operation_id=operation_id,
                    )
                )
                metrics.update(
                    self.bridge._ea_factory_backtest_attention_fields(False, 0)
                )

                metrics["logicRecheckDigest"] = "0" * 64
                (report_dir / "report-backtest.json").write_text(
                    json.dumps(report),
                    encoding="utf-8",
                )
                self.assertFalse(
                    self.bridge._ea_factory_visible_front_office_evidence_valid(
                        build,
                        stage,
                        {"id": "mission-backtest"},
                        report,
                        expected_operation_id=operation_id,
                    )
                )
                metrics.update(copy.deepcopy(valid_truth_projection))

                original_manifest_digest = build["blueprintCoverageManifest"][
                    "manifestDigest"
                ]
                build["blueprintCoverageManifest"]["manifestDigest"] = "0" * 64
                (report_dir / "report-backtest.json").write_text(
                    json.dumps(report),
                    encoding="utf-8",
                )
                self.assertFalse(
                    self.bridge._ea_factory_visible_front_office_evidence_valid(
                        build,
                        stage,
                        {"id": "mission-backtest"},
                        report,
                        expected_operation_id=operation_id,
                    )
                )
                build["blueprintCoverageManifest"][
                    "manifestDigest"
                ] = original_manifest_digest

                metrics["fullDynamicSixGroupVerified"] = True
                (report_dir / "report-backtest.json").write_text(
                    json.dumps(report),
                    encoding="utf-8",
                )
                self.assertFalse(
                    self.bridge._ea_factory_visible_front_office_evidence_valid(
                        build,
                        stage,
                        {"id": "mission-backtest"},
                        report,
                        expected_operation_id=operation_id,
                    )
                )
                metrics.update(copy.deepcopy(valid_truth_projection))

                # A legitimate visual test may take far longer than the
                # 15-second probe window. The immutable pre-action proof is
                # kept, while only the post-action proof must be fresh.
                fresh_post = copy.deepcopy(process_binding)
                fresh_post["observedAt"] = self.bridge.utc_now()
                fresh_post["processBindingDigest"] = ""
                fresh_post["processBindingDigest"] = (
                    self.bridge._ea_factory_front_office_process_binding_digest(
                        fresh_post
                    )
                )
                metrics["postProcessBinding"] = fresh_post
                metrics["postProcessBindingDigest"] = fresh_post[
                    "processBindingDigest"
                ]
                (report_dir / "report-backtest.json").write_text(
                    json.dumps(report),
                    encoding="utf-8",
                )
                self.assertTrue(
                    self.bridge._ea_factory_visible_front_office_evidence_valid(
                        build,
                        stage,
                        {"id": "mission-backtest"},
                        report,
                        expected_operation_id=operation_id,
                        require_fresh_process_proof=True,
                    )
                )

                for field, replacement in (
                    ("terminalWindowHandle", 999),
                    ("terminalWindowTitleSha256", "9" * 64),
                    ("frontOfficeWindowHandle", 998),
                    ("frontOfficeWindowClassSha256", "a" * 64),
                ):
                    with self.subTest(post_action_window_drift=field):
                        drifted_post = copy.deepcopy(fresh_post)
                        drifted_post[field] = replacement
                        drifted_post["processBindingDigest"] = ""
                        drifted_post["processBindingDigest"] = (
                            self.bridge._ea_factory_front_office_process_binding_digest(
                                drifted_post
                            )
                        )
                        metrics["postProcessBinding"] = drifted_post
                        metrics["postProcessBindingDigest"] = drifted_post[
                            "processBindingDigest"
                        ]
                        (report_dir / "report-backtest.json").write_text(
                            json.dumps(report),
                            encoding="utf-8",
                        )
                        self.assertFalse(
                            self.bridge._ea_factory_visible_front_office_evidence_valid(
                                build,
                                stage,
                                {"id": "mission-backtest"},
                                report,
                                expected_operation_id=operation_id,
                                require_fresh_process_proof=True,
                            )
                        )
                metrics["postProcessBinding"] = fresh_post
                metrics["postProcessBindingDigest"] = fresh_post[
                    "processBindingDigest"
                ]

    def test_invalid_visible_result_creates_no_success_mission_or_report(self) -> None:
        build = self.build()
        build["oneClickRun"] = self._run(
            build,
            current_stage="compile_validate",
        )
        build["oneClickRun"]["status"] = "running"
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        stage = next(
            item for item in build["stages"]
            if item["id"] == "compile_validate"
        )
        stage["requestIdempotencyKey"] = "stage-request"
        request = {
            "buildId": build["id"],
            "stageId": "compile_validate",
            "terminalBinding": copy.deepcopy(
                build["oneClickRun"]["terminalBinding"]
            ),
            "visibleOperation": copy.deepcopy(
                build["oneClickRun"]["visibleAction"]
            ),
            "missionId": "mission-eaf-visible-test",
            "reportId": "report-eaf-visible-test",
            "resolvedTarget": {
                "terminalExecutableSha256": "1" * 64,
                "frontOfficeExecutableSha256": "2" * 64,
            },
        }
        result = {
            "metrics": {},
            "artifactSpecifications": [
                {"alias": "compiled_binary", "relativePath": "EA_Versions/a.ex4", "artifactKind": "compile_evidence"},
                {"alias": "visible_window", "relativePath": "Screenshots/a.png", "artifactKind": "screenshot_evidence"},
                {"alias": "compile_log", "relativePath": "Reports/a.txt", "artifactKind": "compile_evidence"},
                {"alias": "adapter_receipt", "relativePath": "Reports/a.json", "artifactKind": "compile_evidence"},
            ],
        }
        artifact_rows = [
            {
                "fileId": f"ea-file-{index}",
                "relativePath": item["relativePath"],
                "artifactKind": item["artifactKind"],
            }
            for index, item in enumerate(result["artifactSpecifications"], start=1)
        ]
        state = self.state(build)
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=state,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_register_artifacts",
                return_value=artifact_rows,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_visible_result_metrics",
                return_value={"stageArtifactManifestDigest": "3" * 64},
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_one_click_terminal_binding_current",
                return_value=True,
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_visible_front_office_evidence_valid",
                return_value=False,
            ),
            mock.patch.object(self.bridge, "create_mission") as create_mission,
            mock.patch.object(self.bridge, "create_report") as create_report,
            mock.patch.object(
                self.bridge,
                "_write_ea_factory_state_unlocked",
            ) as write_state,
        ):
            with self.assertRaises(self.bridge.RequestError):
                self.bridge._ea_factory_commit_visible_front_office_result(
                    request,
                    result,
                )
        create_mission.assert_not_called()
        create_report.assert_not_called()
        write_state.assert_not_called()
        self.assertEqual(stage["status"], "pending")
        self.assertIsNone(stage["reportId"])

    def test_final_report_invalid_visible_proof_creates_no_success_records(self) -> None:
        build = self.build()
        compile_stage = next(
            item for item in build["stages"]
            if item["id"] == "compile_validate"
        )
        compile_stage.update({
            "status": "completed",
            "evidenceVerified": True,
            "missionId": "mission-visible-compile",
            "reportId": "report-visible-compile",
            "visibleEvidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
            "visibleOperationId": "ea-visible-compile-final-check",
        })
        final_stage = next(
            item for item in build["stages"]
            if item["id"] == "final_report"
        )
        final_stage.update({
            "status": "pending",
            "missionIdempotencyKey": "final-idempotency",
        })
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "Summaries").mkdir()
            reports = root / "runtime-reports"
            reports.mkdir()
            (reports / "report-visible-compile.json").write_text(
                json.dumps({
                    "id": "report-visible-compile",
                    "status": "ready",
                    "metrics": {},
                }),
                encoding="utf-8",
            )
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_build_directory",
                    return_value=root,
                ),
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", reports),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_visible_front_office_evidence_valid",
                    return_value=False,
                ),
                mock.patch.object(self.bridge, "create_mission") as create_mission,
                mock.patch.object(self.bridge, "create_report") as create_report,
                mock.patch.object(self.bridge, "_ea_factory_complete_local_mission") as complete_mission,
            ):
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._ea_factory_complete_final_report(
                        build,
                        final_stage,
                    )
        create_mission.assert_not_called()
        create_report.assert_not_called()
        complete_mission.assert_not_called()
        self.assertEqual(final_stage["status"], "pending")
        self.assertIsNone(final_stage["reportId"])

    def test_visible_commit_faults_compensate_success_records(self) -> None:
        fault_points = (
            "create_report",
            "complete_mission",
            "second_evidence_check",
            "state_write",
        )
        for fault_point in fault_points:
            with self.subTest(fault_point=fault_point):
                build, state, request, result, artifact_rows = (
                    self._visible_commit_fixture()
                )
                mission = {"id": request["missionId"], "status": "running"}
                report = {
                    "id": request["reportId"],
                    "status": "ready",
                    "linkedMissionId": request["missionId"],
                    "metrics": {},
                }
                create_report_effect = (
                    RuntimeError("report write fault")
                    if fault_point == "create_report"
                    else (lambda *_args, **_kwargs: report)
                )
                complete_effect = (
                    RuntimeError("mission completion fault")
                    if fault_point == "complete_mission"
                    else None
                )
                evidence_effect = (
                    [True, False]
                    if fault_point == "second_evidence_check"
                    else [True, True]
                )
                write_effect = (
                    RuntimeError("factory state write fault")
                    if fault_point == "state_write"
                    else None
                )
                with (
                    mock.patch.object(
                        self.bridge,
                        "_load_ea_factory_state_unlocked",
                        return_value=state,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_register_artifacts",
                        return_value=artifact_rows,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_visible_result_metrics",
                        return_value={"stageArtifactManifestDigest": "3" * 64},
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_one_click_terminal_binding_current",
                        return_value=True,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_visible_front_office_evidence_valid",
                        side_effect=evidence_effect,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_success_record_snapshot",
                        return_value={
                            "missionIndex": None,
                            "mission": None,
                            "report": None,
                        },
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_restore_success_record_snapshot",
                    ) as restore,
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_visible_commit_is_durable",
                        return_value=False,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "create_mission",
                        return_value=mission,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "create_report",
                        side_effect=create_report_effect,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_complete_local_mission",
                        side_effect=complete_effect,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_ea_factory_sync_build_status",
                        return_value=False,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_write_ea_factory_state_unlocked",
                        side_effect=write_effect,
                    ),
                    mock.patch.object(self.bridge, "append_audit"),
                ):
                    with self.assertRaises((RuntimeError, self.bridge.RequestError)):
                        self.bridge._ea_factory_commit_visible_front_office_result(
                            request,
                            result,
                        )
                restore.assert_called_once()

    def test_success_record_snapshot_restore_removes_new_rows(self) -> None:
        mission_id = "mission-eaf-rollback-test"
        report_id = "report-eaf-rollback-test"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missions_path = root / "missions.json"
            reports_path = root / "reports"
            reports_path.mkdir()
            with (
                mock.patch.object(self.bridge, "MISSIONS_PATH", missions_path),
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", reports_path),
            ):
                self.bridge._invalidate_missions_read_cache()
                snapshot = self.bridge._ea_factory_success_record_snapshot(
                    mission_id,
                    report_id,
                )
                self.bridge.save_missions([
                    {"id": mission_id, "status": "completed"},
                ])
                self.bridge.write_json(
                    reports_path / f"{report_id}.json",
                    {"id": report_id, "status": "ready"},
                )
                self.bridge._ea_factory_restore_success_record_snapshot(
                    mission_id,
                    report_id,
                    snapshot,
                )
                self.assertEqual(self.bridge.load_missions(), [])
                self.assertFalse((reports_path / f"{report_id}.json").exists())
            self.bridge._invalidate_missions_read_cache()

    def test_visible_report_read_model_hides_pid_hwnd_and_full_bindings(self) -> None:
        report = {
            "id": "report-visible-private",
            "type": "ea_compile_report",
            "status": "ready",
            "metrics": {
                "evidenceMode": self.bridge.EA_FACTORY_VISIBLE_EVIDENCE_MODE,
                "operationId": "ea-visible-safe",
                "processId": 123,
                "windowHandle": 456,
                "processBinding": {"terminalProcessId": 123},
                "postProcessBinding": {"terminalProcessId": 123},
                "compiledBinarySha256": "a" * 64,
            },
        }
        model = self.bridge.report_read_model_item(report)
        self.assertNotIn("processId", model["metrics"])
        self.assertNotIn("windowHandle", model["metrics"])
        self.assertNotIn("processBinding", model["metrics"])
        self.assertNotIn("postProcessBinding", model["metrics"])
        self.assertEqual(model["metrics"]["compiledBinarySha256"], "a" * 64)

    def test_tester_set_parser_accepts_only_allowlisted_mt4_metadata_suffixes(self) -> None:
        defaults = {
            "InpStopLossPercent": 7.5,
            "RewardRiskRatio": 2.0,
            "RiskPercent": 1.0,
            "ExecutionBufferPoints": 2,
            "SlippagePoints": 3,
            "MaxOpenPositionsPerSymbolMagic": 1,
            "MagicNumber": 4186001,
            "DailyMAPeriod": 50,
            "WeeklyMAPeriod": 50,
            "FiftyTwoWeekLookback": 52,
            "FundamentalCriteriaConfirmed": False,
            "ExternalBenchmarkUptrendConfirmed": False,
            "MaxSpreadPoints": 30,
        }
        assumptions = []
        lines = []
        for name, input_type in self.bridge.EA_FACTORY_CAN_SLIM_CERTIFIED_INPUT_LAYOUT:
            simulation = name in self.bridge.EA_FACTORY_CAN_SLIM_SIMULATION_INPUT_NAMES
            tester_value = True if simulation else defaults[name]
            assumptions.append({
                "inputName": name,
                "inputType": input_type,
                "sourceDefault": defaults[name],
                "testerValue": tester_value,
                "reasonCode": (
                    "simulate_external_fact_for_historical_test_only"
                    if simulation
                    else "reset_to_certified_source_default_to_prevent_stale_tester_state"
                ),
            })
            token = self.bridge._ea_factory_input_value_token(
                tester_value,
                input_type,
            )
            lines.extend((
                f"{name}={token}",
                f"{name},F=0",
                f"{name},1={token}",
                f"{name},2={token}",
                f"{name},3=0",
            ))
        preset = {"assumptions": assumptions}
        realistic = ("\ufeff" + "\r\n".join(lines) + "\r\n").encode("utf-8")
        parsed = self.bridge._ea_factory_tester_set_values(realistic, preset)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["MaxSpreadPoints"], 30)
        self.assertTrue(parsed["FundamentalCriteriaConfirmed"])
        self.assertIsNone(
            self.bridge._ea_factory_tester_set_values(
                realistic + b"MaxSpreadPoints,X=30\r\n",
                preset,
            )
        )
        self.assertIsNone(
            self.bridge._ea_factory_tester_set_values(
                realistic + b"UnknownInput,F=0\r\n",
                preset,
            )
        )

    def test_png_evidence_must_be_real_and_nonblank(self) -> None:
        self.assertTrue(
            self.bridge._ea_factory_visible_png_valid(
                self._png_payload(solid=False)
            )
        )
        self.assertFalse(
            self.bridge._ea_factory_visible_png_valid(
                self._png_payload(solid=True)
            )
        )
        self.assertFalse(
            self.bridge._ea_factory_visible_png_valid(b"not-a-png")
        )

    def test_tester_report_counts_and_settings_are_cross_checked(self) -> None:
        settings = {
            "expertFileName": "CAN_SLIM.ex4",
            "symbol": "EURUSD",
            "period": "H1",
            "model": "every_tick",
            "deposit": 10000.0,
            "spread": "Current",
        }
        payload = (
            "<html><body><table>"
            "<tr><td>Expert</td><td>CAN_SLIM</td></tr>"
            "<tr><td>Symbol</td><td>EURUSD</td></tr>"
            "<tr><td>Period</td><td>H1</td></tr>"
            "<tr><td>Model</td><td>Every tick</td></tr>"
            "<tr><td>Spread</td><td>Current (12)</td></tr>"
            "<tr><td>Initial deposit</td><td>10000.00</td></tr>"
            "<tr><td>Mismatched chart errors</td><td>0</td></tr>"
            "<tr><td>Total trades</td><td>3</td></tr>"
            "<tr><td>Short positions (won %)</td><td>1</td></tr>"
            "<tr><td>Long positions (won %)</td><td>2</td></tr>"
            "</table></body></html>"
        ).encode("utf-8")
        self.assertTrue(
            self.bridge._ea_factory_tester_report_matches(
                payload,
                settings,
                trade_count=3,
                buy_trade_count=2,
                sell_trade_count=1,
                mismatched_chart_errors=0,
            )
        )
        self.assertFalse(
            self.bridge._ea_factory_tester_report_matches(
                payload,
                settings,
                trade_count=2,
                buy_trade_count=1,
                sell_trade_count=1,
                mismatched_chart_errors=0,
            )
        )
        wrong_symbol_with_decoy = payload.replace(
            b"<tr><td>Symbol</td><td>EURUSD</td></tr>",
            b"<tr><td>Symbol</td><td>GBPUSD</td></tr>"
            b"<tr><td>Comment</td><td>EURUSD</td></tr>",
        )
        self.assertFalse(
            self.bridge._ea_factory_tester_report_matches(
                wrong_symbol_with_decoy,
                settings,
                trade_count=3,
                buy_trade_count=2,
                sell_trade_count=1,
                mismatched_chart_errors=0,
            )
        )
        duplicate_symbol = payload.replace(
            b"<tr><td>Symbol</td><td>EURUSD</td></tr>",
            b"<tr><td>Symbol</td><td>EURUSD</td></tr>"
            b"<tr><td>Symbol</td><td>EURUSD</td></tr>",
        )
        self.assertFalse(
            self.bridge._ea_factory_tester_report_matches(
                duplicate_symbol,
                settings,
                trade_count=3,
                buy_trade_count=2,
                sell_trade_count=1,
                mismatched_chart_errors=0,
            )
        )

    def test_tester_report_accepts_unique_mt4_title_when_expert_row_is_absent(self) -> None:
        settings = {
            "expertFileName": "CAN_SLIM_SourceOnly_v01.ex4",
            "symbol": "GBPUSD",
            "period": "H1",
            "model": "every_tick",
            "deposit": 10000.0,
            "spread": 20,
        }
        payload = (
            "<html><head><title>Strategy Tester: CAN_SLIM_SourceOnly_v01</title></head>"
            "<body><table>"
            "<tr><td>Symbol</td><td>GBPUSD</td></tr>"
            "<tr><td>Period</td><td>1 Hour (H1)</td></tr>"
            "<tr><td>Model</td><td>Every tick (most precise)</td></tr>"
            "<tr><td>Spread</td><td>20</td></tr>"
            "<tr><td>Initial deposit</td><td>10000.00</td></tr>"
            "<tr><td>Mismatched chart errors</td><td>0</td></tr>"
            "<tr><td>Total trades</td><td>0</td></tr>"
            "</table></body></html>"
        ).encode("utf-8")
        self.assertTrue(
            self.bridge._ea_factory_tester_report_matches(
                payload,
                settings,
                trade_count=0,
                buy_trade_count=0,
                sell_trade_count=0,
                mismatched_chart_errors=0,
            )
        )

    def test_tester_report_rejects_duplicate_title_when_expert_row_is_absent(self) -> None:
        settings = {
            "expertFileName": "CAN_SLIM_SourceOnly_v01.ex4",
            "symbol": "GBPUSD",
            "period": "H1",
            "model": "every_tick",
            "deposit": 10000.0,
            "spread": 20,
        }
        payload = (
            "<html><head><title>Strategy Tester: CAN_SLIM_SourceOnly_v01</title>"
            "<title>Strategy Tester: CAN_SLIM_SourceOnly_v01</title></head>"
            "<body><table>"
            "<tr><td>Symbol</td><td>GBPUSD</td></tr>"
            "<tr><td>Period</td><td>H1</td></tr>"
            "<tr><td>Model</td><td>Every tick</td></tr>"
            "<tr><td>Spread</td><td>20</td></tr>"
            "<tr><td>Initial deposit</td><td>10000.00</td></tr>"
            "<tr><td>Mismatched chart errors</td><td>0</td></tr>"
            "<tr><td>Total trades</td><td>0</td></tr>"
            "</table></body></html>"
        ).encode("utf-8")
        self.assertFalse(
            self.bridge._ea_factory_tester_report_matches(
                payload,
                settings,
                trade_count=0,
                buy_trade_count=0,
                sell_trade_count=0,
                mismatched_chart_errors=0,
            )
        )

    @staticmethod
    def _png_payload(*, solid: bool) -> bytes:
        width, height = 320, 180

        def chunk(kind: bytes, data: bytes) -> bytes:
            return (
                len(data).to_bytes(4, "big")
                + kind
                + data
                + (zlib.crc32(kind + data) & 0xFFFFFFFF).to_bytes(4, "big")
            )

        ihdr = (
            width.to_bytes(4, "big")
            + height.to_bytes(4, "big")
            + bytes((8, 2, 0, 0, 0))
        )
        scanlines = bytearray()
        for y in range(height):
            scanlines.append(0)
            for x in range(width):
                value = 17 if solid else (x + y * 3) % 256
                scanlines.extend((value, (value * 3) % 256, (value * 7) % 256))
        return (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(scanlines)))
            + chunk(b"IEND", b"")
        )

    def _run(self, build: dict, *, current_stage: str) -> dict:
        now = "2026-09-11T00:00:00Z"
        return {
            "schemaVersion": self.bridge.EA_FACTORY_ONE_CLICK_SCHEMA_VERSION,
            "runId": "ea-run-one-click-test",
            "idempotencyKey": "one-click-ui-001",
            "requestDigest": self.bridge._ea_factory_one_click_request_digest(build),
            "status": "queued",
            "currentStageId": current_stage,
            "terminalBinding": {
                "platform": "mt4",
                "candidateId": "mtc-one-click-terminal",
                "selectionRevision": 7,
                "bindingDigest": "c" * 64,
            },
            "failureCode": None,
            "messageTh": "queued",
            "startedAt": now,
            "updatedAt": now,
            "completedAt": None,
        }

    def _visible_commit_fixture(self):
        build = self.build()
        build["oneClickRun"] = self._run(
            build,
            current_stage="compile_validate",
        )
        build["oneClickRun"]["status"] = "running"
        self.bridge._ea_factory_one_click_reserve_visible_action(
            build,
            build["oneClickRun"],
            "compile_validate",
        )
        stage = next(
            item for item in build["stages"]
            if item["id"] == "compile_validate"
        )
        stage.update({
            "requestIdempotencyKey": "stage-request",
            "missionIdempotencyKey": "stage-mission-key",
        })
        request = {
            "buildId": build["id"],
            "stageId": "compile_validate",
            "terminalBinding": copy.deepcopy(
                build["oneClickRun"]["terminalBinding"]
            ),
            "visibleOperation": copy.deepcopy(
                build["oneClickRun"]["visibleAction"]
            ),
            "missionId": "mission-eaf-visible-fault",
            "reportId": "report-eaf-visible-fault",
            "resolvedTarget": {
                "terminalExecutableSha256": "1" * 64,
                "frontOfficeExecutableSha256": "2" * 64,
            },
        }
        result = {
            "metrics": {},
            "artifactSpecifications": [
                {"alias": "compiled_binary", "relativePath": "EA_Versions/a.ex4", "artifactKind": "compile_evidence"},
                {"alias": "visible_window", "relativePath": "Screenshots/a.png", "artifactKind": "screenshot_evidence"},
                {"alias": "compile_log", "relativePath": "Reports/a.txt", "artifactKind": "compile_evidence"},
                {"alias": "adapter_receipt", "relativePath": "Reports/a.json", "artifactKind": "compile_evidence"},
            ],
        }
        artifact_rows = [
            {
                "fileId": f"ea-file-fault-{index}",
                "relativePath": item["relativePath"],
                "artifactKind": item["artifactKind"],
            }
            for index, item in enumerate(
                result["artifactSpecifications"],
                start=1,
            )
        ]
        return build, self.state(build), request, result, artifact_rows

    def test_production_visible_adapter_is_wired_fail_closed_at_runtime(self) -> None:
        class Adapter:
            supported_platforms = frozenset({"mt4"})

            def capability_provider(self, **_kwargs):
                return {"ready": False}

            def compile_handler(self, *, request):
                return request

            def backtest_handler(self, *, request):
                return request

        previous = (
            self.bridge.EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER,
            self.bridge.EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER,
            self.bridge.EA_FACTORY_VISIBLE_STRATEGY_TESTER_HANDLER,
        )
        adapter = Adapter()
        try:
            with (
                mock.patch.object(
                    self.bridge,
                    "create_production_visible_front_office_adapter",
                    return_value=adapter,
                ) as factory,
                mock.patch.object(self.bridge, "append_audit") as audit,
            ):
                configured = (
                    self.bridge.configure_ea_factory_visible_front_office_adapter()
                )
            self.assertTrue(configured)
            factory.assert_called_once_with(
                target_resolver=(
                    self.bridge._ea_factory_visible_adapter_target_resolver
                )
            )
            self.assertIs(
                self.bridge.EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER.__self__,
                adapter,
            )
            self.assertEqual(
                self.bridge._ea_factory_front_office_supported_platforms(),
                frozenset({"mt4"}),
            )
            self.assertEqual(
                audit.call_args.args[0]["type"],
                "ea_factory.visible_front_office_adapter_configured",
            )
        finally:
            (
                self.bridge.EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER,
                self.bridge.EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER,
                self.bridge.EA_FACTORY_VISIBLE_STRATEGY_TESTER_HANDLER,
            ) = previous

    def test_visible_adapter_configuration_failure_clears_all_handlers(self) -> None:
        previous = (
            self.bridge.EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER,
            self.bridge.EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER,
            self.bridge.EA_FACTORY_VISIBLE_STRATEGY_TESTER_HANDLER,
        )
        try:
            self.bridge.EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER = lambda **_kwargs: {}
            self.bridge.EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER = lambda **_kwargs: {}
            self.bridge.EA_FACTORY_VISIBLE_STRATEGY_TESTER_HANDLER = lambda **_kwargs: {}
            with (
                mock.patch.object(
                    self.bridge,
                    "create_production_visible_front_office_adapter",
                    side_effect=RuntimeError("adapter setup failed"),
                ),
                mock.patch.object(self.bridge, "append_audit") as audit,
            ):
                configured = (
                    self.bridge.configure_ea_factory_visible_front_office_adapter()
                )
            self.assertFalse(configured)
            self.assertIsNone(
                self.bridge.EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER
            )
            self.assertIsNone(
                self.bridge.EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER
            )
            self.assertIsNone(
                self.bridge.EA_FACTORY_VISIBLE_STRATEGY_TESTER_HANDLER
            )
            self.assertEqual(
                audit.call_args.args[0]["type"],
                "ea_factory.visible_front_office_adapter_unavailable",
            )
        finally:
            (
                self.bridge.EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER,
                self.bridge.EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER,
                self.bridge.EA_FACTORY_VISIBLE_STRATEGY_TESTER_HANDLER,
            ) = previous

    def test_visible_adapter_resolver_uses_only_current_backend_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            install = root / "terminal-install"
            data = root / "terminal-data"
            install.mkdir()
            (data / "MQL4").mkdir(parents=True)
            terminal = install / "terminal.exe"
            compiler = install / "metaeditor.exe"
            terminal.write_bytes(b"terminal")
            compiler.write_bytes(b"compiler")
            binding = {
                "platform": "mt4",
                "candidateId": "mtc-current-terminal",
                "selectionRevision": 9,
                "bindingDigest": "d" * 64,
            }
            context = {
                "record": {
                    "dataPath": str(data),
                    "localPath": str(data),
                }
            }
            target = {
                **binding,
                "installPath": install,
                "compilerPath": compiler,
            }
            with (
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_metaeditor_target_context",
                    return_value=(context, target),
                ),
                mock.patch.object(
                    self.bridge,
                    "_ea_factory_path_is_link_or_reparse",
                    return_value=False,
                ),
            ):
                resolved = self.bridge._ea_factory_visible_adapter_target_resolver(
                    platform="mt4",
                    terminal_binding=copy.deepcopy(binding),
                )
                self.assertEqual(Path(resolved["terminalPath"]), terminal.resolve())
                self.assertEqual(Path(resolved["compilerPath"]), compiler.resolve())
                with self.assertRaises(
                    self.bridge.VisibleTerminalAdapterError
                ) as mismatch:
                    self.bridge._ea_factory_visible_adapter_target_resolver(
                        platform="mt4",
                        terminal_binding={**binding, "selectionRevision": 10},
                    )
            self.assertEqual(mismatch.exception.code, "terminal_binding_mismatch")


if __name__ == "__main__":
    unittest.main()
