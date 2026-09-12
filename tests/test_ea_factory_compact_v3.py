from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
RUNNER_PATH = PROJECT_ROOT / "runner" / "codex_cli_runner.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compact_a_j_row() -> dict[str, str]:
    return {
        "record_id": "strategy-brief-row-001",
        "system_name": "EMA closed-bar crossover",
        "system_overview": (
            "Trend-following system for a user-selected liquid market and timeframe."
        ),
        "entry_rules": (
            "Buy when fast EMA[2] <= slow EMA[2] and fast EMA[1] > slow EMA[1]; "
            "Sell uses the inverse closed-bar crossover."
        ),
        "recovery_rules": "No recovery, grid, martingale, averaging, or hedging.",
        "exit_rules": (
            "Close on the opposite crossover; stop loss and take profit are bounded "
            "user inputs."
        ),
        "money_management": (
            "Use a user-selected fixed lot with one managed position maximum."
        ),
        "order_execution": (
            "Use market Buy or Sell orders only after a confirmed closed-bar signal."
        ),
        "display_requirements": (
            "Display system name, signal state, Balance, Equity, and Spread."
        ),
        "additional_notes": (
            "Research specification only; compile and backtest separately."
        ),
    }


class EAFactoryCompactV3IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module("ea_factory_compact_v3_bridge", BRIDGE_PATH)
        cls.runner = load_module("ea_factory_compact_v3_runner", RUNNER_PATH)

    def _record(self) -> dict:
        record = self.bridge._ea_factory_normalize_record(
            compact_a_j_row(),
            source_kind="verified_deep_research_sheet",
            source_key="sheet-compact-v3-test",
        )
        self.assertIsInstance(record, dict)
        self.assertTrue(record["buildReady"])
        self.assertIsInstance(record["strategyBrief"], dict)
        self.assertRegex(record["strategyBriefDigest"], r"^[0-9a-f]{64}$")
        return record

    def _create_initial_build(
        self,
        root: Path,
        artifact_kind: str,
    ) -> tuple[dict, dict]:
        record = self._record()
        build_id = f"ea-build-compact-v3-{artifact_kind}"
        platform = "mt4"
        workspace = self.bridge._ea_factory_create_build_workspace(
            build_id,
            record,
            platform,
            artifact_kind,
        )
        strategy_mission = {"id": f"mission-spec-{artifact_kind}"}
        strategy_report = {"id": f"report-spec-{artifact_kind}"}
        brief = ""
        now = self.bridge.utc_now()
        build = {
            "schemaVersion": "ea-factory-build-v1",
            "id": build_id,
            "sourceRecordId": record["sourceRecordId"],
            "sourceDisplayName": record["displayName"],
            "sourceRecordDigest": record["recordDigest"],
            "sourceReportId": strategy_report["id"],
            "sourceMissionId": strategy_mission["id"],
            "platform": platform,
            "artifactKind": artifact_kind,
            "brief": brief,
            "status": "ready",
            "workspace": workspace,
            "stages": self.bridge._ea_factory_initial_stages(
                platform,
                strategy_mission,
                strategy_report,
                artifact_kind,
            ),
            "versions": [],
            "createIdempotencyKey": None,
            "createIdempotencyKeys": [],
            "createRequestDigest": self.bridge._ea_factory_create_request_digest(
                record["sourceRecordId"],
                platform,
                brief,
                artifact_kind,
            ),
            "createdAt": now,
            "updatedAt": now,
        }
        artifacts = self.bridge._ea_factory_register_artifacts(
            build,
            [
                {
                    "relativePath": workspace["strategySpecFile"],
                    "stageId": "strategy_spec",
                    "reportId": strategy_report["id"],
                    "artifactKind": "strategy_spec",
                }
            ],
        )
        self.bridge._ea_factory_stage_row(build, "strategy_spec")["artifacts"] = [
            item["fileId"] for item in artifacts
        ]
        return record, build

    @staticmethod
    def _compact_indicator_source(brief_digest: str) -> str:
        return f'''#property strict
#property indicator_chart_window
#property indicator_buffers 2
#property indicator_type1 DRAW_ARROW
#property indicator_type2 DRAW_ARROW
#property description "EA_STRATEGY_BRIEF_SHA256:{brief_digest}"
double EntryBuffer[];
double ExitBuffer[];
int OnInit() {{
  SetIndexBuffer(0, EntryBuffer);
  SetIndexBuffer(1, ExitBuffer);
  return(INIT_SUCCEEDED);
}}
int OnCalculate(const int rates_total, const int prev_calculated,
                const datetime &time[], const double &open[],
                const double &high[], const double &low[],
                const double &close[], const long &tick_volume[],
                const long &volume[], const int &spread[]) {{
  if(rates_total < 3) return(0);
  EntryBuffer[1] = EMPTY_VALUE;
  ExitBuffer[1] = EMPTY_VALUE;
  bool entrySignal = close[2] <= open[2] && close[1] > open[1];
  if(entrySignal) EntryBuffer[1] = low[1];
  bool exitSignal = close[2] >= open[2] && close[1] < open[1];
  if(exitSignal) ExitBuffer[1] = high[1];
  return(rates_total);
}}
'''

    @staticmethod
    def _compact_ea_source(brief_digest: str) -> str:
        return f'''#property strict
#property description "EA_STRATEGY_BRIEF_SHA256:{brief_digest}"
#define SIGNAL_NONE -1
input double FixedLot = 0.01;
input int MagicNumber = 4186001;
int OnInit() {{ return(INIT_SUCCEEDED); }}
int CountManagedPositions() {{
  int count = 0;
  for(int pos=OrdersTotal()-1; pos>=0; pos--) {{
    if(!OrderSelect(pos, SELECT_BY_POS, MODE_TRADES)) continue;
    if(OrderSymbol() == Symbol() && OrderMagicNumber() == MagicNumber) count++;
  }}
  return(count);
}}
bool CloseOpposite(const int signal) {{
  for(int pos=OrdersTotal()-1; pos>=0; pos--) {{
    if(!OrderSelect(pos, SELECT_BY_POS, MODE_TRADES)) continue;
    bool opposite = (signal == OP_BUY && OrderType() == OP_SELL)
                 || (signal == OP_SELL && OrderType() == OP_BUY);
    if(opposite && !OrderClose(OrderTicket(), OrderLots(),
                              OrderType() == OP_BUY ? Bid : Ask, 3)) return(false);
  }}
  return(true);
}}
void OnTick() {{
  static datetime lastBar = 0;
  datetime currentBar = Time[0];
  if(currentBar <= 0 || currentBar == lastBar) return;
  lastBar = currentBar;
  if(Bars < 3 || FixedLot <= 0.0) return;
  int signal = SIGNAL_NONE;
  if(Close[2] <= Open[2] && Close[1] > Open[1]) signal = OP_BUY;
  if(Close[2] >= Open[2] && Close[1] < Open[1]) signal = OP_SELL;
  Comment("EMA closed-bar crossover signal=", signal,
          " Balance=", AccountBalance(), " Equity=", AccountEquity(),
          " Spread=", MarketInfo(Symbol(), MODE_SPREAD));
  if(signal == SIGNAL_NONE || !CloseOpposite(signal)) return;
  if(CountManagedPositions() >= 1) return;
  double entryPrice = signal == OP_BUY ? Ask : Bid;
  double stopLoss = signal == OP_BUY ? entryPrice - 100 * Point : entryPrice + 100 * Point;
  double takeProfit = signal == OP_BUY ? entryPrice + 200 * Point : entryPrice - 200 * Point;
  OrderSend(Symbol(), signal, FixedLot, entryPrice, 3, stopLoss, takeProfit, "Compact A-J", MagicNumber, 0);
}}
'''

    def _generation_report(
        self,
        build: dict,
        contract_values: dict[str, str],
    ) -> dict:
        inputs = {
            "sourceReportId": build["sourceReportId"],
            "platform": build["platform"],
            "brief": self.bridge._ea_factory_generation_brief(build),
        }
        return {
            "id": "report-compact-indicator-generation",
            "type": "ea_build_report",
            "status": "ready",
            "linkedPropId": "right_server_racks",
            "workflowContext": {
                "propId": "right_server_racks",
                "actionId": "build_strategy_code",
                "inputDigest": self.bridge.payload_digest(
                    "dashboard-workflow-input-v1",
                    "right_server_racks",
                    "build_strategy_code",
                    json.dumps(inputs, ensure_ascii=False, sort_keys=True),
                ),
                "inputs": inputs,
                "source": {"reportId": build["sourceReportId"]},
            },
            "metrics": {
                "workflowOutput": {
                    "applicable": True,
                    "valid": True,
                    "expectedFields": list(contract_values),
                    "providedFields": list(contract_values),
                    "missingFields": [],
                    "expectedEvidenceKinds": ["project_relative_source_path"],
                    "providedEvidenceKinds": ["project_relative_source_path"],
                    "missingEvidenceKinds": [],
                    "values": contract_values,
                }
            },
        }

    def _review_report(self, build: dict) -> dict:
        generation = self.bridge._ea_factory_stage_row(build, "generate_source")
        inputs = {
            "sourceReportId": generation["reportId"],
            "platform": build["platform"],
            "brief": self.bridge._ea_factory_review_brief(build),
        }
        covered_fields = [
            "record_id",
            "system_name",
            "system_overview",
            "entry_rules",
            "recovery_rules",
            "exit_rules",
            "money_management",
            "order_execution",
            "display_requirements",
            "additional_notes",
        ]
        return {
            "id": "report-compact-indicator-review",
            "type": "ea_build_report",
            "status": "ready",
            "linkedPropId": "right_server_racks",
            "workflowContext": {
                "propId": "right_server_racks",
                "actionId": "review_source_code",
                "inputDigest": self.bridge.payload_digest(
                    "dashboard-workflow-input-v1",
                    "right_server_racks",
                    "review_source_code",
                    json.dumps(inputs, ensure_ascii=False, sort_keys=True),
                ),
                "inputs": inputs,
                "source": {"reportId": generation["reportId"]},
            },
            "metrics": {
                "workflowOutput": {
                    "applicable": True,
                    "valid": True,
                    "values": {
                        "sourceDigest": build["versions"][0]["sourceDigest"],
                        "compileStatus": "source_only",
                        "sourceRecordDigest": build["sourceRecordDigest"],
                        "strategySpecDigest": build["workspace"]["strategySpecDigest"],
                        "platform": build["platform"],
                        "strategyCoverage": json.dumps({
                            "coveredFields": covered_fields,
                            "uncoveredFields": [],
                        }),
                        "severity": "no_issue",
                        "reviewStatus": "review_passed",
                        "issues": "[]",
                    },
                }
            },
        }

    def test_a_j_workspace_and_build_revalidate_for_ea_and_indicator(self) -> None:
        for artifact_kind in ("expert_advisor", "custom_indicator"):
            with self.subTest(artifact_kind=artifact_kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                    _record, build = self._create_initial_build(root, artifact_kind)
                    spec_path = (
                        root
                        / "workspace"
                        / "ea-factory"
                        / build["id"]
                        / "Source"
                        / "strategy-spec-v01.json"
                    )
                    spec = self.bridge.read_json(spec_path, None)
                    validated = self.bridge._ea_factory_revalidated_build(build)

                self.assertEqual(spec["schemaVersion"], "ea-factory-strategy-spec-v3")
                self.assertEqual(spec["artifactKind"], artifact_kind)
                self.assertEqual(
                    spec["strategySchemaVersion"],
                    self.bridge.EA_STRATEGY_BRIEF_SCHEMA_VERSION,
                )
                self.assertNotIn("eaImplementationBlueprint", spec)
                self.assertEqual(validated["coverageStatus"], "compact_current")
                if artifact_kind == "custom_indicator":
                    self.assertEqual(
                        self.bridge._ea_factory_stage_row(
                            validated,
                            "backtest_recheck",
                        )["status"],
                        "not_applicable",
                    )

    def test_runner_v3_binding_accepts_ea_and_indicator(self) -> None:
        for artifact_kind in ("expert_advisor", "custom_indicator"):
            with self.subTest(artifact_kind=artifact_kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                    _record, build = self._create_initial_build(root, artifact_kind)
                    prompt = self.bridge._ea_factory_generation_brief(build)
                    source_root = (
                        root
                        / "workspace"
                        / "ea-factory"
                        / build["id"]
                        / "Source"
                    )
                    binding = self.runner._ea_factory_source_generation_binding(
                        prompt,
                        f"ea-factory/{build['id']}/Source",
                        source_root,
                    )

                self.assertEqual(
                    binding["strategySpecSchemaVersion"],
                    "ea-factory-strategy-spec-v3",
                )
                self.assertEqual(binding["artifactKind"], artifact_kind)
                self.assertIsNone(binding["coverageRequirements"])
                self.assertIn("v3 compact A-J", prompt)
                self.assertNotIn("v1: A-M", prompt)
                self.assertNotIn("v2: use", prompt)
                with (
                    mock.patch.object(self.runner, "PROJECT_ROOT", root),
                    mock.patch.object(
                        self.runner,
                        "AUTO_WORKSPACE_ROOT",
                        root / "workspace",
                    ),
                ):
                    runner_prompt = self.runner.build_prompt(
                        prompt,
                        "ea-developer",
                        "mission-compact-v3-prompt",
                        "standard",
                        12000,
                        result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                        scoped_workspace_write_root=source_root,
                    )
                self.assertIn(
                    "current Factory accepts only Strategy Spec v3 compact A-J",
                    runner_prompt,
                )
                self.assertNotIn("For Strategy Spec v1", runner_prompt)
                self.assertNotIn("For Strategy Spec v2", runner_prompt)
                if artifact_kind == "custom_indicator":
                    self.assertIn(
                        "[EA_FACTORY_ARTIFACT_KIND:custom_indicator]",
                        prompt,
                    )
                else:
                    self.assertNotIn("[EA_FACTORY_ARTIFACT_KIND:", prompt)

    def test_compact_ea_generation_and_review_use_exact_a_j_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                _record, build = self._create_initial_build(root, "expert_advisor")
                spec = self.bridge.read_json(
                    root
                    / "workspace"
                    / "ea-factory"
                    / build["id"]
                    / "Source"
                    / "strategy-spec-v01.json",
                    None,
                )
                relative_root = f"ea-factory/{build['id']}/Source"
                generation_prompt = self.bridge._ea_factory_generation_brief(build)
                with (
                    mock.patch.object(self.runner, "PROJECT_ROOT", root),
                    mock.patch.object(self.runner, "AUTO_WORKSPACE_ROOT", root / "workspace"),
                ):
                    materialized = self.runner.materialize_ea_factory_source_result(
                        json.dumps({
                            "fileName": "CompactStrategy.mq4",
                            "content": self._compact_ea_source(
                                spec["strategyBriefDigest"]
                            ),
                        }),
                        generation_prompt,
                        relative_root,
                    )
                contract_values = {
                    row["field"]: row["value"]
                    for row in materialized["contractFields"]
                }
                generated_manifest = json.loads(
                    contract_values["blueprintCoverageManifest"]
                )
                self.assertEqual(
                    generated_manifest["schemaVersion"],
                    self.bridge.EA_SOURCE_MANIFEST_SCHEMA_VERSION,
                )
                self.assertEqual(
                    generated_manifest["coveredFields"],
                    list(compact_a_j_row()),
                )
                self.assertEqual(generated_manifest["missingFields"], [])
                self.assertTrue(generated_manifest["complete"])
                generation_report = self._generation_report(build, contract_values)
                self.assertTrue(
                    self.bridge._ea_factory_generation_evidence_valid(
                        build,
                        generation_report,
                        ingest_sources=True,
                    )
                )
                generation_stage = self.bridge._ea_factory_stage_row(
                    build,
                    "generate_source",
                )
                generation_stage.update({
                    "status": "completed",
                    "missionId": "mission-compact-ea-generation",
                    "reportId": generation_report["id"],
                    "evidenceVerified": True,
                })
                self.assertEqual(
                    self.bridge._ea_factory_mql_static_review_findings(build),
                    [],
                )
                review_brief = self.bridge._ea_factory_review_brief(build)
                self.assertIn("Audit exact Strategy Brief A-J coverage only", review_brief)
                self.assertNotIn("Audit A-M coverage", review_brief)
                review_report = self._review_report(build)
                self.assertTrue(
                    self.bridge._ea_factory_review_evidence_valid(
                        build,
                        review_report,
                    )
                )
                extra_coverage = copy.deepcopy(review_report)
                extra_value = json.loads(
                    extra_coverage["metrics"]["workflowOutput"]["values"][
                        "strategyCoverage"
                    ]
                )
                extra_value["coveredFields"].append("unexpected_k")
                extra_coverage["metrics"]["workflowOutput"]["values"][
                    "strategyCoverage"
                ] = json.dumps(extra_value)
                self.assertTrue(
                    self.bridge._ea_factory_review_evidence_valid(
                        build,
                        extra_coverage,
                        static_findings=[],
                    ),
                    "Compact EA coverage is recomputed from immutable Source, not trusted Worker JSON",
                )
                worker_misread = copy.deepcopy(review_report)
                worker_values = worker_misread["metrics"]["workflowOutput"]["values"]
                worker_values.update({
                    "sourceDigest": (
                        "source-only review used EA_STRATEGY_BRIEF_SHA256: "
                        + spec["strategyBriefDigest"]
                    ),
                    "sourceRecordDigest": "Worker did not echo this identity cleanly",
                    "strategySpecDigest": "Worker did not echo this identity cleanly",
                    "platform": "MT4 source-only review",
                    "strategyCoverage": json.dumps({
                        "coveredFields": [
                            "system_name",
                            "entry_rules",
                            "recovery_rules",
                            "exit_rules",
                            "money_management",
                            "order_execution",
                        ],
                        "uncoveredFields": [
                            "record_id",
                            "system_overview",
                            "display_requirements",
                            "additional_notes",
                        ],
                    }),
                    "severity": "medium",
                    "reviewStatus": "review_completed_with_advisories",
                    "issues": json.dumps([
                        {
                            "severity": "medium",
                            "message": "External facts use fail-closed operator inputs",
                        }
                    ]),
                })
                backend_manifest = (
                    self.bridge._ea_factory_recomputed_compact_review_manifest(build)
                )
                self.assertEqual(
                    backend_manifest["sourceDigest"],
                    build["versions"][0]["sourceDigest"],
                )
                self.assertEqual(
                    backend_manifest["coveredFields"],
                    list(compact_a_j_row()),
                )
                self.assertTrue(
                    self.bridge._ea_factory_review_evidence_valid(
                        build,
                        worker_misread,
                        static_findings=[],
                    ),
                    "Worker digest prose and coverage misclassification cannot override Backend proof",
                )
                blocking_worker = copy.deepcopy(worker_misread)
                blocking_values = blocking_worker["metrics"]["workflowOutput"]["values"]
                blocking_values["severity"] = "critical"
                blocking_values["issues"] = json.dumps([
                    {
                        "severity": "critical",
                        "message": "Unsafe order path requires repair",
                    }
                ])
                self.assertFalse(
                    self.bridge._ea_factory_review_evidence_valid(
                        build,
                        blocking_worker,
                        static_findings=[],
                    ),
                    "High-severity qualitative Worker findings remain blocking",
                )
                review_stage = self.bridge._ea_factory_stage_row(
                    build,
                    "source_review",
                )
                review_stage.update({
                    "status": "completed",
                    "missionId": "mission-compact-ea-review",
                    "reportId": review_report["id"],
                    "evidenceVerified": True,
                })
                self.assertTrue(
                    self.bridge._ea_factory_stage_can_advance(
                        build,
                        "compile_validate",
                    )
                )
                self.bridge._ea_factory_revalidated_build(build)
                tampered = copy.deepcopy(build)
                tampered["blueprintCoverageManifest"]["coveredFields"].append(
                    "unexpected_k"
                )
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._ea_factory_revalidated_build(tampered)

    def test_sealed_compact_v1_build_remains_readable_but_requires_rebuild(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                _record, build = self._create_initial_build(root, "expert_advisor")
                spec = self.bridge.read_json(
                    root
                    / "workspace"
                    / "ea-factory"
                    / build["id"]
                    / "Source"
                    / "strategy-spec-v01.json",
                    None,
                )
                relative_root = f"ea-factory/{build['id']}/Source"
                with (
                    mock.patch.object(self.runner, "PROJECT_ROOT", root),
                    mock.patch.object(
                        self.runner,
                        "AUTO_WORKSPACE_ROOT",
                        root / "workspace",
                    ),
                ):
                    materialized = self.runner.materialize_ea_factory_source_result(
                        json.dumps({
                            "fileName": "LegacyCompactStrategy.mq4",
                            "content": self._compact_ea_source(
                                spec["strategyBriefDigest"]
                            ),
                        }),
                        self.bridge._ea_factory_generation_brief(build),
                        relative_root,
                    )
                contract_values = {
                    row["field"]: row["value"]
                    for row in materialized["contractFields"]
                }
                generation_report = self._generation_report(build, contract_values)
                self.assertTrue(
                    self.bridge._ea_factory_generation_evidence_valid(
                        build,
                        generation_report,
                        ingest_sources=True,
                    )
                )
                generation_stage = self.bridge._ea_factory_stage_row(
                    build,
                    "generate_source",
                )
                generation_stage.update({
                    "status": "completed",
                    "missionId": "mission-legacy-compact-generation",
                    "reportId": generation_report["id"],
                    "evidenceVerified": True,
                })

                legacy_manifest = copy.deepcopy(
                    build["blueprintCoverageManifest"]
                )
                legacy_manifest["schemaVersion"] = (
                    self.bridge.EA_FACTORY_LEGACY_COMPACT_EA_SOURCE_MANIFEST_V1
                )
                unsigned = copy.deepcopy(legacy_manifest)
                unsigned.pop("manifestDigest", None)
                legacy_manifest["manifestDigest"] = (
                    self.bridge._ea_factory_canonical_json_sha256(unsigned)
                )
                build["blueprintCoverageManifest"] = copy.deepcopy(
                    legacy_manifest
                )
                generation_stage["blueprintCoverageManifest"] = copy.deepcopy(
                    legacy_manifest
                )

                validated = self.bridge._ea_factory_revalidated_build(build)
                self.assertTrue(validated["coverageUpgradeRequired"])
                self.assertEqual(
                    validated["coverageStatus"],
                    "coverage_upgrade_required",
                )
                self.assertFalse(
                    self.bridge._ea_factory_stage_can_advance(
                        validated,
                        "source_review",
                    )
                )

                tampered = copy.deepcopy(build)
                tampered["blueprintCoverageManifest"]["sourceDigest"] = "0" * 64
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._ea_factory_revalidated_build(tampered)

    def test_compact_ea_generation_rejects_empty_unbound_and_oncalculate_source_without_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                _record, build = self._create_initial_build(root, "expert_advisor")
                spec = self.bridge.read_json(
                    root
                    / "workspace"
                    / "ea-factory"
                    / build["id"]
                    / "Source"
                    / "strategy-spec-v01.json",
                    None,
                )
                marker = spec["strategyBriefDigest"]
                cases = {
                    "EmptyLifecycle.mq4": (
                        '#property strict\n'
                        f'#property description "EA_STRATEGY_BRIEF_SHA256:{marker}"\n'
                        '#define SIGNAL_NONE -1\nvoid OnTick() {}\n'
                    ),
                    "WrongBinding.mq4": self._compact_ea_source("0" * 64),
                    "IndicatorEntry.mq4": (
                        '#property strict\n#define SIGNAL_NONE -1\n'
                        f'#property description "EA_STRATEGY_BRIEF_SHA256:{marker}"\n'
                        'int OnCalculate(){ return(0); }\n'
                    ),
                    "DeadHelper.mq4": (
                        '#property strict\n#define SIGNAL_NONE -1\n'
                        f'#property description "EA_STRATEGY_BRIEF_SHA256:{marker}"\n'
                        'void PlaceTrade(){ OrderSend(Symbol(),OP_BUY,0.1,Ask,3,0,0); }\n'
                        'void OnTick() {}\n'
                    ),
                    "MissingCapGuard.mq4": self._compact_ea_source(marker).replace(
                        "  if(CountManagedPositions() >= 1) return;\n",
                        "",
                    ),
                    "WrongCapZero.mq4": self._compact_ea_source(marker).replace(
                        "CountManagedPositions() >= 1",
                        "CountManagedPositions() == 0",
                    ),
                    "WrongCapFive.mq4": self._compact_ea_source(marker).replace(
                        "CountManagedPositions() >= 1",
                        "CountManagedPositions() > 5",
                    ),
                }
                prompt = self.bridge._ea_factory_generation_brief(build)
                relative_root = f"ea-factory/{build['id']}/Source"
                source_dir = (
                    root / "workspace" / "ea-factory" / build["id"] / "Source"
                )
                with (
                    mock.patch.object(self.runner, "PROJECT_ROOT", root),
                    mock.patch.object(
                        self.runner,
                        "AUTO_WORKSPACE_ROOT",
                        root / "workspace",
                    ),
                ):
                    for file_name, source in cases.items():
                        with self.subTest(file_name=file_name):
                            with self.assertRaises(ValueError):
                                self.runner.materialize_ea_factory_source_result(
                                    json.dumps({
                                        "fileName": file_name,
                                        "content": source,
                                    }),
                                    prompt,
                                    relative_root,
                                )
                            self.assertFalse((source_dir / file_name).exists())

    def test_legacy_factory_create_and_advance_are_read_only_without_mutation(self) -> None:
        record = self._record()
        legacy_record = copy.deepcopy(record)
        legacy_record.pop("strategyBrief", None)
        legacy_record.pop("strategyBriefDigest", None)
        self.assertFalse(
            self.bridge._ea_factory_current_compact_source_valid(legacy_record)
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._ea_factory_create_build_workspace(
                        "ea-build-legacy-read-only",
                        legacy_record,
                        "mt4",
                    )
                self.assertFalse(
                    (root / "workspace" / "ea-factory" / "ea-build-legacy-read-only").exists()
                )

        empty_state = self.bridge._empty_ea_factory_state()
        with (
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value=copy.deepcopy(empty_state),
            ),
            mock.patch.object(
                self.bridge,
                "_ea_factory_source_catalog",
                return_value=[legacy_record],
            ),
            mock.patch.object(self.bridge, "_write_ea_factory_state_unlocked") as write_state,
            mock.patch.object(self.bridge, "_ea_factory_create_build_workspace") as create_workspace,
        ):
            with self.assertRaises(self.bridge.RequestError) as create_error:
                self.bridge.create_ea_factory_build({
                    "sourceRecordId": legacy_record["sourceRecordId"],
                    "platform": "mt4",
                    "artifactKind": "expert_advisor",
                    "idempotencyKey": "legacy-create-read-only",
                })
            self.assertEqual(create_error.exception.status, 422)
            write_state.assert_not_called()
            create_workspace.assert_not_called()

        legacy_build = {
            "id": "ea-build-legacy-read-only",
            "coverageStatus": "current",
            "coverageUpgradeRequired": False,
        }
        with (
            mock.patch.object(
                self.bridge,
                "_load_ea_factory_state_unlocked",
                return_value={"builds": [legacy_build]},
            ),
            mock.patch.object(self.bridge, "_ea_factory_sync_build_status") as sync_status,
        ):
            with self.assertRaises(self.bridge.RequestError) as advance_error:
                self.bridge.advance_ea_factory_build(
                    legacy_build["id"],
                    {"stageId": "generate_source"},
                )
            self.assertEqual(advance_error.exception.status, 409)
            sync_status.assert_not_called()

    def test_compact_source_and_review_contract_reject_extra_fields(self) -> None:
        record = self._record()
        extra_record = copy.deepcopy(record)
        extra_record["strategyBrief"]["unexpectedK"] = "not A-J"
        self.assertFalse(
            self.bridge._ea_factory_current_compact_source_valid(extra_record)
        )

    def test_compact_indicator_generation_and_review_advance_to_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                _record, build = self._create_initial_build(root, "custom_indicator")
                spec_path = (
                    root
                    / "workspace"
                    / "ea-factory"
                    / build["id"]
                    / "Source"
                    / "strategy-spec-v01.json"
                )
                spec = self.bridge.read_json(spec_path, None)
                source = self._compact_indicator_source(spec["strategyBriefDigest"])
                relative_root = f"ea-factory/{build['id']}/Source"
                prompt = self.bridge._ea_factory_generation_brief(build)
                with (
                    mock.patch.object(self.runner, "PROJECT_ROOT", root),
                    mock.patch.object(self.runner, "AUTO_WORKSPACE_ROOT", root / "workspace"),
                ):
                    materialized = self.runner.materialize_ea_factory_source_result(
                        json.dumps({
                            "fileName": "CompactSignals.mq4",
                            "content": source,
                        }),
                        prompt,
                        relative_root,
                    )
                contract_values = {
                    row["field"]: row["value"]
                    for row in materialized["contractFields"]
                }
                generated_manifest = json.loads(
                    contract_values["blueprintCoverageManifest"]
                )
                self.assertEqual(
                    generated_manifest["schemaVersion"],
                    self.bridge.INDICATOR_SOURCE_MANIFEST_SCHEMA_VERSION,
                )
                self.assertTrue(generated_manifest["complete"])
                self.assertEqual(generated_manifest["signalBranchCount"], 2)

                generation_report = self._generation_report(build, contract_values)
                self.assertTrue(
                    self.bridge._ea_factory_generation_evidence_valid(
                        build,
                        generation_report,
                        ingest_sources=True,
                    )
                )
                generation_stage = self.bridge._ea_factory_stage_row(
                    build,
                    "generate_source",
                )
                generation_stage.update({
                    "status": "completed",
                    "missionId": "mission-compact-indicator-generation",
                    "reportId": generation_report["id"],
                    "evidenceVerified": True,
                })
                self.assertEqual(
                    self.bridge._ea_factory_mql_static_review_findings(build),
                    [],
                )
                review_report = self._review_report(build)
                self.assertTrue(
                    self.bridge._ea_factory_review_evidence_valid(
                        build,
                        review_report,
                    )
                )
                review_stage = self.bridge._ea_factory_stage_row(
                    build,
                    "source_review",
                )
                review_stage.update({
                    "status": "completed",
                    "missionId": "mission-compact-indicator-review",
                    "reportId": review_report["id"],
                    "evidenceVerified": True,
                })
                self.assertTrue(
                    self.bridge._ea_factory_stage_can_advance(
                        build,
                        "compile_validate",
                    )
                )
                self.bridge._ea_factory_revalidated_build(build)

    def test_compact_indicator_source_checks_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                _record, build = self._create_initial_build(root, "custom_indicator")
                spec = self.bridge.read_json(
                    root
                    / "workspace"
                    / "ea-factory"
                    / build["id"]
                    / "Source"
                    / "strategy-spec-v01.json",
                    None,
                )
                source = self._compact_indicator_source(spec["strategyBriefDigest"])
                cases = {
                    "missing-brief-binding": source.replace(
                        spec["strategyBriefDigest"],
                        "0" * 64,
                    ),
                    "forming-bar-output": source.replace(
                        "EntryBuffer[1] = low[1]",
                        "EntryBuffer[0] = low[0]",
                    ),
                    "one-signal-branch": source.replace(
                        "if(exitSignal) ExitBuffer[1] = high[1];",
                        "ExitBuffer[1] = EMPTY_VALUE;",
                    ),
                    "trading-api": source + "\nvoid SendTrade(){ OrderSend(Symbol(),OP_BUY,0.1,Ask,3,0,0); }\n",
                    "hidden-plot": source.replace("DRAW_ARROW", "DRAW_NONE"),
                }
                for label, unsafe_source in cases.items():
                    with self.subTest(label=label):
                        findings = self.bridge._ea_factory_indicator_static_review_findings(
                            build,
                            unsafe_source,
                        )
                        self.assertTrue(findings, label)
                        with (
                            mock.patch.object(self.runner, "PROJECT_ROOT", root),
                            mock.patch.object(
                                self.runner,
                                "AUTO_WORKSPACE_ROOT",
                                root / "workspace",
                            ),
                        ):
                            with self.assertRaises(ValueError):
                                self.runner.materialize_ea_factory_source_result(
                                    json.dumps({
                                        "fileName": f"Unsafe{label.replace('-', '')}.mq4",
                                        "content": unsafe_source,
                                    }),
                                    self.bridge._ea_factory_generation_brief(build),
                                    f"ea-factory/{build['id']}/Source",
                                )

    def test_compact_indicator_review_rejects_legacy_coverage_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.object(self.bridge, "PROJECT_ROOT", root):
                _record, build = self._create_initial_build(root, "custom_indicator")
                spec = self.bridge.read_json(
                    root
                    / "workspace"
                    / "ea-factory"
                    / build["id"]
                    / "Source"
                    / "strategy-spec-v01.json",
                    None,
                )
                source = self._compact_indicator_source(spec["strategyBriefDigest"])
                source_path = (
                    root
                    / "workspace"
                    / "ea-factory"
                    / build["id"]
                    / "Source"
                    / "CompactSignals.mq4"
                )
                version_path = source_path.parent.parent / "EA_Versions" / "CompactSignals_v01.mq4"
                source_path.write_text(source, encoding="utf-8")
                version_path.write_text(source, encoding="utf-8")
                source_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
                build["versions"] = [{
                    "version": 1,
                    "fileName": source_path.name,
                    "sourceDigest": source_digest,
                    "sourceFile": "Source/CompactSignals.mq4",
                    "versionFile": "EA_Versions/CompactSignals_v01.mq4",
                    "sourceReportId": "report-compact-indicator-generation",
                    "immutable": True,
                }]
                self.bridge._ea_factory_register_artifacts(
                    build,
                    [
                        {
                            "relativePath": "Source/CompactSignals.mq4",
                            "stageId": "generate_source",
                            "reportId": "report-compact-indicator-generation",
                            "artifactKind": "generated_source",
                        },
                        {
                            "relativePath": "EA_Versions/CompactSignals_v01.mq4",
                            "stageId": "generate_source",
                            "reportId": "report-compact-indicator-generation",
                            "artifactKind": "immutable_version",
                        },
                    ],
                )
                generation = self.bridge._ea_factory_stage_row(build, "generate_source")
                generation.update({
                    "status": "completed",
                    "reportId": "report-compact-indicator-generation",
                    "evidenceVerified": True,
                })
                report = self._review_report(build)
                report["metrics"]["workflowOutput"]["values"]["strategyCoverage"] = (
                    json.dumps({
                        "coveredFields": [
                            "record_id",
                            "system_name",
                            "strategy_family",
                            "symbols_market",
                            "timeframe",
                            "entry_rules",
                            "exit_rules",
                            "indicators",
                            "special_conditions",
                        ],
                        "uncoveredFields": [],
                    })
                )
                self.assertFalse(
                    self.bridge._ea_factory_review_evidence_valid(
                        copy.deepcopy(build),
                        report,
                        static_findings=[],
                    )
                )


if __name__ == "__main__":
    unittest.main()
