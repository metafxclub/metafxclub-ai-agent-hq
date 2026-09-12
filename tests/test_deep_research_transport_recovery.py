from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
RUNNER_PATH = PROJECT_ROOT / "runner" / "codex_cli_runner.py"
BRIEF_FIXTURE_PATH = PROJECT_ROOT / "tests" / "test_ea_strategy_brief.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DeepResearchTransportRecoveryTests(unittest.TestCase):
    """Bind deterministic recovery to one exact failed run and its artifacts."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module(
            "metafx_deep_research_transport_recovery_bridge",
            BRIDGE_PATH,
        )
        cls.runner = load_module(
            "metafx_deep_research_transport_recovery_runner",
            RUNNER_PATH,
        )
        cls.brief_fixture = load_module(
            "metafx_deep_research_transport_recovery_brief_fixture",
            BRIEF_FIXTURE_PATH,
        )

    @staticmethod
    def source_urls() -> list[str]:
        return [
            "https://tradingfinder.com/education/trading-strategy/",
            "https://forex-station.com/strategy-library-t8475202.html",
        ]

    def _direct_payload(self, *, summary: str = "Verified research is complete.") -> dict:
        urls = self.source_urls()
        brief = self.brief_fixture.valid_brief()
        brief["sourceLinks"] = list(urls)
        brief["systemOverview"] += (
            "\nThe EA must expose its risk and exit assumptions as editable Inputs."
        )
        return {
            "status": "completed",
            "summary": summary,
            "findings": ["The compact Strategy Brief passed semantic validation."],
            "nextSteps": ["Ask the user to review before saving to Google Sheet."],
            "evidence": [
                {
                    "label": f"Bound source {index}",
                    "url": url,
                    "note": "Opened by the original guarded research run",
                }
                for index, url in enumerate(urls, start=1)
            ],
            "blockedCapability": "",
            "research": brief,
            "evidenceKinds": [
                "at_least_two_source_urls",
                "checked_at",
                "limitations",
                "source_digest",
            ],
        }

    def _canonical_artifacts(self) -> tuple[str, str, dict]:
        direct = json.dumps(
            self._direct_payload(),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        parsed = self.runner.parse_work_result(
            direct,
            64_000,
            "trading_system_research",
        )
        formatted = self.runner.format_work_report(parsed, 64_000)
        recovered = self.runner.recover_ea_research_transport_result(
            formatted,
            direct,
            64_000,
        )
        return direct, formatted, recovered

    def _context(self) -> dict:
        urls = self.source_urls()
        source_report_id = "source-report-recovery-1"
        source_record_id = "source-record-recovery-1"
        source = {
            "reportId": source_report_id,
            "recordId": source_record_id,
            "sourceKind": "verified_catalog_record",
            "sourcePropId": "codex_mcp_portal",
            "sourceMissionId": "source-mission-recovery-1",
            "type": "trading_system_discovery_report",
            "status": "ready",
            "agentTransfer": None,
            "structuredPayload": {
                "sourceUrls": list(urls),
            },
        }
        form = {
            "sourceReportId": source_report_id,
            "sourceRecordId": source_record_id,
            "brief": "Expand only the selected verified trading system.",
            "timezone": "Asia/Bangkok",
        }
        profile = self.bridge._trusted_workflow_plugin_profile(
            "left_server_racks",
            "deep_research_system",
            form,
        )
        context = self.bridge._dashboard_workflow_lineage(
            "left_server_racks",
            "deep_research_system",
            form,
            source,
            plugin_profile=profile,
        )
        self.assertIsNotNone(self.bridge._workflow_context_storage(context))
        return context

    @contextmanager
    def _isolated_runtime(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runtime = root / "data" / "runtime"
            reports = runtime / "reports"
            runs = runtime / "codex-runs"
            reports.mkdir(parents=True)
            runs.mkdir(parents=True)
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", root),
                mock.patch.object(self.bridge, "RUNTIME_DIR", runtime),
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", reports),
                mock.patch.object(
                    self.bridge,
                    "AUDIT_PATH",
                    runtime / "bridge-audit.jsonl",
                ),
            ):
                yield root, runtime, reports, runs

    def _fixture(
        self,
        root: Path,
        reports: Path,
        runs: Path,
        *,
        agent_message: str | None = None,
    ) -> tuple[dict, dict, dict]:
        direct, formatted, recovered = self._canonical_artifacts()
        stdout_message = direct if agent_message is None else agent_message
        run_id = "run-deep-research-recovery-1"
        final_reference = f"data/runtime/codex-runs/{run_id}.final.md"
        final_path = runs / f"{run_id}.final.md"
        stdout_path = runs / f"{run_id}.stdout.log"
        final_path.write_text(formatted, encoding="utf-8", newline="")
        stdout_event = {
            "type": "item.completed",
            "item": {
                "id": "agent-message-recovery-1",
                "type": "agent_message",
                "text": stdout_message,
            },
        }
        stdout_path.write_text(
            json.dumps(stdout_event, ensure_ascii=False, separators=(",", ":"))
            + "\n",
            encoding="utf-8",
            newline="",
        )

        context = self._context()
        valid_contract = self.bridge.validate_dashboard_workflow_output_contract(
            {
                "workflowContext": context,
                "budget": {"outputLimitChars": 64_000},
            },
            recovered,
        )
        self.assertTrue(valid_contract["valid"], valid_contract)
        failed_contract = copy.deepcopy(valid_contract)
        failed_contract["valid"] = False
        failed_contract["failureCode"] = (
            "trading_system_research_output_contract_invalid"
        )
        failed_contract["entryErrors"] = [
            "STRATEGY_BRIEF_PROJECTION_MISMATCH:sourceDigest"
        ]
        failed_contract["missingFields"] = ["strategyBrief"]
        failed_contract["providedFields"] = [
            field
            for field in failed_contract.get("providedFields", [])
            if field != "strategyBrief"
        ]
        failed_contract["values"].pop("strategyBrief", None)

        mission_id = "mission-deep-research-recovery-1"
        original_report_id = "auto-report-deep-research-recovery-1"
        mission_failed_at = "2026-01-01T00:00:00+00:00"
        original_report_created_at = "2026-01-01T00:00:01+00:00"
        mission = {
            "id": mission_id,
            "title": "Deep Research transport failure fixture",
            "owner": "mission_archivist",
            "status": "blocked",
            "phase": (
                "auto_guarded_trading_system_research_output_contract_invalid"
            ),
            "workStatus": "trading_system_research_output_contract_invalid",
            "errorCode": "trading_system_research_output_contract_invalid",
            "targetId": "left_server_racks",
            "toolId": "codex_web_research",
            "reportType": "trading_system_research_report",
            "requiresHumanApproval": False,
            "approval": {"required": False, "state": "not_required"},
            "workflowContext": copy.deepcopy(context),
            "workflowOutputContract": copy.deepcopy(failed_contract),
            "reportIds": [original_report_id],
            "artifactPath": final_reference,
            "createdAt": "2025-12-31T23:59:00+00:00",
            "updatedAt": mission_failed_at,
            "heartbeatAt": mission_failed_at,
            "completedAt": mission_failed_at,
            "execution": {
                "processStarted": True,
                "workingDirectory": "workspace",
                "writeRoots": [],
                "controlPlaneWritable": False,
                "webSearchEnabled": True,
                "webSearchUsed": True,
                "webSearchEvidenceVerified": True,
                "resultProfile": "trading_system_research",
                "completedAt": mission_failed_at,
            },
        }
        original_report = {
            "id": original_report_id,
            "type": "trading_system_research_report",
            "title": mission["title"],
            "summary": "The Runner result was damaged only by transport redaction.",
            "ownerAgentId": mission["owner"],
            "linkedMissionId": mission_id,
            "linkedPropId": "left_server_racks",
            "status": "blocked",
            "findings": [],
            "metrics": {"workflowOutput": copy.deepcopy(failed_contract)},
            "risks": ["trading_system_research_output_contract_invalid"],
            "nextActions": [],
            "evidence": copy.deepcopy(recovered["evidence"]),
            "artifacts": [final_reference],
            "workflowContext": copy.deepcopy(context),
            "createdAt": original_report_created_at,
            "updatedAt": original_report_created_at,
        }
        (reports / f"{original_report_id}.json").write_text(
            json.dumps(
                original_report,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        return mission, original_report, recovered

    def _deterministic_runner(self, calls: list[dict]):
        def run(command, **kwargs):
            request = json.loads(str(kwargs.get("input_text") or "{}"))
            calls.append(
                {
                    "command": [str(item) for item in command],
                    "request": copy.deepcopy(request),
                    "structuredJsonOutput": kwargs.get("structured_json_output"),
                }
            )
            try:
                result = self.runner.recover_ea_research_transport_result(
                    request.get("formattedReport"),
                    request.get("agentMessage"),
                    64_000,
                )
            except (TypeError, ValueError) as exc:
                return {
                    "ok": False,
                    "exitCode": "invalid_output",
                    "output": json.dumps(
                        {
                            "ok": False,
                            "status": "invalid_output",
                            "error": str(exc),
                        },
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                }
            return {
                "ok": True,
                "exitCode": 0,
                "output": json.dumps(
                    result,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            }

        return run

    def test_exact_failed_candidate_and_local_artifacts_are_accepted(self) -> None:
        with self._isolated_runtime() as (root, _runtime, reports, runs):
            mission, original_report, _recovered = self._fixture(
                root,
                reports,
                runs,
            )

            artifacts = self.bridge._deep_research_transport_recovery_artifacts(
                mission["artifactPath"]
            )
            candidate = self.bridge._deep_research_transport_recovery_candidate(
                mission
            )

        self.assertIsNotNone(artifacts)
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["missionId"], mission["id"])
        self.assertEqual(candidate["originalReportId"], original_report["id"])
        self.assertEqual(
            candidate["originalReportDigest"],
            self.bridge._report_snapshot_digest(original_report),
        )
        self.assertEqual(candidate["requiredUrls"], self.source_urls())
        self.assertEqual(
            artifacts["formattedReportSha256"],
            hashlib.sha256(artifacts["formattedReport"].encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            artifacts["agentMessageSha256"],
            hashlib.sha256(artifacts["agentMessage"].encode("utf-8")).hexdigest(),
        )

    def test_near_miss_failed_missions_are_rejected_before_recovery(self) -> None:
        with self._isolated_runtime() as (root, _runtime, reports, runs):
            mission, _original_report, _recovered = self._fixture(
                root,
                reports,
                runs,
            )
            mutations = {
                "different_entry_error": lambda row: row[
                    "workflowOutputContract"
                ].update(
                    {
                        "entryErrors": [
                            "STRATEGY_BRIEF_PROJECTION_MISMATCH:checkedAt"
                        ]
                    }
                ),
                "extra_report_identity": lambda row: row["reportIds"].append(
                    "auto-report-unrelated"
                ),
                "web_search_not_verified": lambda row: row["execution"].update(
                    {"webSearchEvidenceVerified": False}
                ),
                "wrong_failure_phase": lambda row: row.update(
                    {"phase": "auto_guarded_failed"}
                ),
                "wrong_owner": lambda row: row.update({"owner": "manager"}),
            }

            for name, mutate in mutations.items():
                near_miss = copy.deepcopy(mission)
                mutate(near_miss)
                with self.subTest(name=name):
                    self.assertIsNone(
                        self.bridge._deep_research_transport_recovery_candidate(
                            near_miss
                        )
                    )

    def test_matching_final_and_stdout_create_ready_valid_unqueued_report(self) -> None:
        with self._isolated_runtime() as (root, _runtime, reports, runs):
            mission, _original_report, _recovered = self._fixture(
                root,
                reports,
                runs,
            )
            candidate = self.bridge._deep_research_transport_recovery_candidate(
                mission
            )
            self.assertIsNotNone(candidate)
            runner_calls: list[dict] = []
            with (
                mock.patch.object(
                    self.bridge,
                    "run_safe_command",
                    side_effect=self._deterministic_runner(runner_calls),
                ),
                mock.patch.object(
                    self.bridge,
                    "ensure_runtime_dir",
                    side_effect=lambda: reports.mkdir(parents=True, exist_ok=True),
                ),
                mock.patch.object(self.bridge, "append_audit"),
                mock.patch.object(
                    self.bridge,
                    "_deep_research_report_is_human_confirmed",
                    return_value=False,
                ),
                mock.patch.object(
                    self.bridge,
                    "_research_sheet_queue_report",
                ) as sheet_queue,
            ):
                recovered_values = (
                    self.bridge._deep_research_transport_recovered_report(
                        mission,
                        candidate,
                    )
                )

            self.assertIsNotNone(recovered_values)
            report, output_contract, receipt = recovered_values
            self.assertEqual(report["status"], "ready")
            self.assertEqual(report["linkedMissionId"], mission["id"])
            self.assertTrue(output_contract["valid"], output_contract)
            self.assertEqual(output_contract["missingFields"], [])
            self.assertEqual(output_contract["entryErrors"], [])
            self.assertFalse(receipt["aiRerun"])
            self.assertFalse(receipt["webSearchRerun"])
            self.assertFalse(receipt["externalWrites"])
            self.assertFalse(receipt["googleSheetQueued"])
            self.assertEqual(
                report["metrics"]["transportRecovery"],
                receipt,
            )
            sheet_queue.assert_not_called()
            self.assertEqual(len(runner_calls), 1)
            call = runner_calls[0]
            self.assertTrue(call["structuredJsonOutput"])
            self.assertIn(
                "--recover-ea-research-transport-stdin",
                call["command"],
            )
            self.assertNotIn("--web-search", call["command"])
            self.assertNotIn("--model", call["command"])
            self.assertEqual(
                call["request"]["formattedReport"],
                candidate["artifacts"]["formattedReport"],
            )
            self.assertEqual(
                call["request"]["agentMessage"],
                candidate["artifacts"]["agentMessage"],
            )

    def test_mismatched_final_and_stdout_fail_closed_without_report_or_sheet(self) -> None:
        mismatched_direct = json.dumps(
            self._direct_payload(summary="A different result must never recover."),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        with self._isolated_runtime() as (root, _runtime, reports, runs):
            mission, _original_report, _recovered = self._fixture(
                root,
                reports,
                runs,
                agent_message=mismatched_direct,
            )
            # Artifact syntax and Mission lineage are both valid.  The exact
            # cross-representation comparison must still reject the pair.
            candidate = self.bridge._deep_research_transport_recovery_candidate(
                mission
            )
            self.assertIsNotNone(candidate)
            report_count_before = len(list(reports.glob("*.json")))
            runner_calls: list[dict] = []
            with (
                mock.patch.object(
                    self.bridge,
                    "run_safe_command",
                    side_effect=self._deterministic_runner(runner_calls),
                ),
                mock.patch.object(self.bridge, "append_audit"),
                mock.patch.object(
                    self.bridge,
                    "_research_sheet_queue_report",
                ) as sheet_queue,
            ):
                recovered_values = (
                    self.bridge._deep_research_transport_recovered_report(
                        mission,
                        candidate,
                    )
                )

            self.assertIsNone(recovered_values)
            self.assertEqual(len(runner_calls), 1)
            self.assertEqual(
                len(list(reports.glob("*.json"))),
                report_count_before,
            )
            sheet_queue.assert_not_called()

    def test_crash_replay_reuses_only_the_exact_derived_report(self) -> None:
        with self._isolated_runtime() as (root, _runtime, reports, runs):
            mission, _original_report, _recovered = self._fixture(
                root,
                reports,
                runs,
            )
            candidate = self.bridge._deep_research_transport_recovery_candidate(
                mission
            )
            self.assertIsNotNone(candidate)
            runner_calls: list[dict] = []
            with (
                mock.patch.object(
                    self.bridge,
                    "run_safe_command",
                    side_effect=self._deterministic_runner(runner_calls),
                ),
                mock.patch.object(
                    self.bridge,
                    "ensure_runtime_dir",
                    side_effect=lambda: reports.mkdir(parents=True, exist_ok=True),
                ),
                mock.patch.object(self.bridge, "append_audit"),
            ):
                first = self.bridge._deep_research_transport_recovered_report(
                    mission,
                    candidate,
                )
                self.assertIsNotNone(first)
                second = self.bridge._deep_research_transport_recovered_report(
                    mission,
                    candidate,
                )
                self.assertIsNotNone(second)
                self.assertEqual(second[0], first[0])

                recovered_path = reports / f"{first[0]['id']}.json"
                exact_report = json.loads(recovered_path.read_text(encoding="utf-8"))
                mutations = {
                    "summary": lambda row: row.update({"summary": "TAMPERED"}),
                    "evidence": lambda row: row["evidence"][0].update(
                        {"url": "https://attacker.invalid/"}
                    ),
                    "strategy_brief": lambda row: row["metrics"][
                        "strategyBrief"
                    ].update({"systemName": "TAMPERED"}),
                    "workflow_context": lambda row: row["workflowContext"].update(
                        {"inputDigest": "0" * 64}
                    ),
                    "recovery_receipt": lambda row: row["metrics"][
                        "transportRecovery"
                    ].update({"agentMessageSha256": "0" * 64}),
                    "correlated_backdated_timestamps": lambda row: (
                        row.update(
                            {
                                "createdAt": "2001-01-01T00:00:00+00:00",
                                "updatedAt": "2001-01-01T00:00:00+00:00",
                            }
                        ),
                        row["metrics"]["transportRecovery"].update(
                            {"recoveredAt": "2001-01-01T00:00:00+00:00"}
                        ),
                        row["metrics"]["workflowOutput"].update(
                            {"checkedAt": "2001-01-01T00:00:00+00:00"}
                        ),
                    ),
                    "correlated_future_timestamps": lambda row: (
                        row.update(
                            {
                                "createdAt": "2099-01-01T00:00:00+00:00",
                                "updatedAt": "2099-01-01T00:00:00+00:00",
                            }
                        ),
                        row["metrics"]["transportRecovery"].update(
                            {"recoveredAt": "2099-01-01T00:00:00+00:00"}
                        ),
                        row["metrics"]["workflowOutput"].update(
                            {"checkedAt": "2099-01-01T00:00:00+00:00"}
                        ),
                    ),
                    "correlated_in_window_timestamps": lambda row: (
                        row.update(
                            {
                                "createdAt": "2026-01-01T00:00:02+00:00",
                                "updatedAt": "2026-01-01T00:00:02+00:00",
                            }
                        ),
                        row["metrics"]["transportRecovery"].update(
                            {"recoveredAt": "2026-01-01T00:00:02+00:00"}
                        ),
                        row["metrics"]["workflowOutput"].update(
                            {"checkedAt": "2026-01-01T00:00:02+00:00"}
                        ),
                    ),
                }
                for name, mutate in mutations.items():
                    tampered = copy.deepcopy(exact_report)
                    mutate(tampered)
                    recovered_path.write_text(
                        json.dumps(
                            tampered,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                        encoding="utf-8",
                    )
                    with self.subTest(name=name):
                        self.assertIsNone(
                            self.bridge._deep_research_transport_recovered_report(
                                mission,
                                candidate,
                            )
                        )
                    recovered_path.write_text(
                        json.dumps(
                            exact_report,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                        encoding="utf-8",
                    )

    def test_audit_is_idempotent_when_mission_save_fails_then_restarts(self) -> None:
        with self._isolated_runtime() as (root, runtime, reports, runs):
            mission, _original_report, _recovered = self._fixture(
                root,
                reports,
                runs,
            )
            runner_calls: list[dict] = []
            with (
                mock.patch.object(
                    self.bridge,
                    "run_safe_command",
                    side_effect=self._deterministic_runner(runner_calls),
                ),
                mock.patch.object(
                    self.bridge,
                    "load_missions",
                    return_value=[copy.deepcopy(mission)],
                ),
                mock.patch.object(
                    self.bridge,
                    "save_missions",
                    side_effect=OSError("simulated mission-store failure"),
                ),
                mock.patch.object(self.bridge, "refresh_parent_mission"),
            ):
                with self.assertRaises(OSError):
                    self.bridge.reconcile_deep_research_transport_failures()

            audit_path = runtime / "bridge-audit.jsonl"
            first_events = [
                json.loads(line)
                for line in audit_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                sum(
                    event.get("type")
                    == "mission.deep_research_transport_recovery_prepared"
                    for event in first_events
                ),
                1,
            )
            self.assertFalse(
                any(
                    event.get("type")
                    == "mission.deep_research_transport_recovered"
                    for event in first_events
                )
            )

            saved: list[list[dict]] = []
            with (
                mock.patch.object(
                    self.bridge,
                    "run_safe_command",
                    side_effect=self._deterministic_runner(runner_calls),
                ),
                mock.patch.object(
                    self.bridge,
                    "load_missions",
                    return_value=[copy.deepcopy(mission)],
                ),
                mock.patch.object(
                    self.bridge,
                    "save_missions",
                    side_effect=lambda rows: saved.append(copy.deepcopy(rows)),
                ),
                mock.patch.object(self.bridge, "refresh_parent_mission"),
            ):
                self.assertEqual(
                    self.bridge.reconcile_deep_research_transport_failures(),
                    1,
                )

            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0][0]["status"], "completed")
            second_events = [
                json.loads(line)
                for line in audit_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                sum(
                    event.get("type")
                    == "mission.deep_research_transport_recovery_prepared"
                    for event in second_events
                ),
                1,
            )
            self.assertEqual(
                sum(
                    event.get("type")
                    == "mission.deep_research_transport_recovered"
                    for event in second_events
                ),
                1,
            )

            with (
                mock.patch.object(
                    self.bridge,
                    "load_missions",
                    return_value=copy.deepcopy(saved[0]),
                ),
                mock.patch.object(self.bridge, "save_missions") as save_again,
            ):
                self.assertEqual(
                    self.bridge.reconcile_deep_research_transport_failures(),
                    0,
                )
            save_again.assert_not_called()
            final_events = [
                json.loads(line)
                for line in audit_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                sum(
                    event.get("type")
                    == "mission.deep_research_transport_recovered"
                    for event in final_events
                ),
                1,
            )
            recovered_event = next(
                event
                for event in final_events
                if event.get("type")
                == "mission.deep_research_transport_recovered"
            )
            colliding_event = {
                key: value for key, value in recovered_event.items() if key != "time"
            }
            colliding_event["recoveredAt"] = "2026-01-01T00:00:02+00:00"
            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge.append_audit_once(colliding_event)
            with audit_path.open("ab") as handle:
                handle.write(b'{"type":"partial-crash-tail"')
            canonical_event = {
                key: value for key, value in recovered_event.items() if key != "time"
            }
            self.assertFalse(self.bridge.append_audit_once(canonical_event))
            repaired_audit_bytes = audit_path.read_bytes()
            self.assertTrue(repaired_audit_bytes.endswith(b"\n"))
            for line in repaired_audit_bytes.decode("utf-8").splitlines():
                self.assertIsInstance(json.loads(line), dict)

    def test_completed_mission_repairs_a_crash_before_completion_audit(self) -> None:
        with self._isolated_runtime() as (root, runtime, reports, runs):
            mission, _original_report, _recovered = self._fixture(
                root,
                reports,
                runs,
            )
            runner_calls: list[dict] = []
            saved: list[list[dict]] = []
            real_append_once = self.bridge.append_audit_once

            def fail_completion_audit(event: dict) -> bool:
                if event.get("type") == "mission.deep_research_transport_recovered":
                    raise OSError("simulated completion-audit failure")
                return real_append_once(event)

            with (
                mock.patch.object(
                    self.bridge,
                    "run_safe_command",
                    side_effect=self._deterministic_runner(runner_calls),
                ),
                mock.patch.object(
                    self.bridge,
                    "load_missions",
                    return_value=[copy.deepcopy(mission)],
                ),
                mock.patch.object(
                    self.bridge,
                    "save_missions",
                    side_effect=lambda rows: saved.append(copy.deepcopy(rows)),
                ),
                mock.patch.object(
                    self.bridge,
                    "append_audit_once",
                    side_effect=fail_completion_audit,
                ),
                mock.patch.object(self.bridge, "refresh_parent_mission"),
            ):
                with self.assertRaises(OSError):
                    self.bridge.reconcile_deep_research_transport_failures()

            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0][0]["status"], "completed")
            audit_path = runtime / "bridge-audit.jsonl"
            interrupted_events = [
                json.loads(line)
                for line in audit_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertFalse(
                any(
                    event.get("type")
                    == "mission.deep_research_transport_recovered"
                    for event in interrupted_events
                )
            )

            recovered_report_id = saved[0][0]["reportIds"][0]
            recovered_path = reports / f"{recovered_report_id}.json"
            exact_report = json.loads(recovered_path.read_text(encoding="utf-8"))
            tampered_report = copy.deepcopy(exact_report)
            tampered_report["summary"] = "TAMPERED BEFORE AUDIT REPAIR"
            recovered_path.write_text(
                json.dumps(
                    tampered_report,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
            self.assertIsNone(
                self.bridge._completed_deep_research_transport_recovery_audit_item(
                    saved[0][0]
                )
            )
            recovered_path.write_text(
                json.dumps(
                    exact_report,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )

            forged_time = "2026-01-01T00:00:02+00:00"
            correlated_mission = copy.deepcopy(saved[0][0])
            correlated_report = copy.deepcopy(exact_report)
            correlated_mission.update(
                {
                    "updatedAt": forged_time,
                    "heartbeatAt": forged_time,
                    "completedAt": forged_time,
                }
            )
            correlated_mission["execution"].update(
                {"heartbeatAt": forged_time, "completedAt": forged_time}
            )
            correlated_mission["workflowOutputContract"]["checkedAt"] = forged_time
            correlated_mission["deterministicTransportRecovery"][
                "recoveredAt"
            ] = forged_time
            correlated_report.update(
                {"createdAt": forged_time, "updatedAt": forged_time}
            )
            correlated_report["metrics"]["workflowOutput"][
                "checkedAt"
            ] = forged_time
            correlated_report["metrics"]["transportRecovery"][
                "recoveredAt"
            ] = forged_time
            correlated_mission["deterministicTransportRecovery"][
                "recoveredReportDigest"
            ] = self.bridge._report_snapshot_digest(correlated_report)
            recovered_path.write_text(
                json.dumps(
                    correlated_report,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
            self.assertIsNone(
                self.bridge._completed_deep_research_transport_recovery_audit_item(
                    correlated_mission
                )
            )

            transaction_mission = copy.deepcopy(saved[0][0])
            transaction_report = copy.deepcopy(exact_report)
            forged_transaction_id = "recovery-tx-" + "f" * 32
            forged_transaction_digest = "f" * 64
            transaction_mission["deterministicTransportRecovery"].update(
                {
                    "recoveryTransactionId": forged_transaction_id,
                    "recoveryTransactionDigest": forged_transaction_digest,
                }
            )
            transaction_report["metrics"]["transportRecovery"].update(
                {
                    "recoveryTransactionId": forged_transaction_id,
                    "recoveryTransactionDigest": forged_transaction_digest,
                }
            )
            transaction_mission["deterministicTransportRecovery"][
                "recoveredReportDigest"
            ] = self.bridge._report_snapshot_digest(transaction_report)
            recovered_path.write_text(
                json.dumps(
                    transaction_report,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
            self.assertIsNone(
                self.bridge._completed_deep_research_transport_recovery_audit_item(
                    transaction_mission
                )
            )
            recovered_path.write_text(
                json.dumps(
                    exact_report,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )

            with (
                mock.patch.object(
                    self.bridge,
                    "load_missions",
                    return_value=copy.deepcopy(saved[0]),
                ),
                mock.patch.object(self.bridge, "save_missions") as save_again,
            ):
                self.assertEqual(
                    self.bridge.reconcile_deep_research_transport_failures(),
                    0,
                )
            save_again.assert_not_called()
            repaired_events = [
                json.loads(line)
                for line in audit_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                sum(
                    event.get("type")
                    == "mission.deep_research_transport_recovered"
                    for event in repaired_events
                ),
                1,
            )
if __name__ == "__main__":
    unittest.main()
