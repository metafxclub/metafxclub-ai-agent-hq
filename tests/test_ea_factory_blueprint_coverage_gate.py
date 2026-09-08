from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BLUEPRINT_TEST = _load(
    "ea_factory_coverage_blueprint_fixture",
    ROOT / "tests" / "test_ea_research_blueprint_v2.py",
)
BRIDGE = _load(
    "ea_factory_coverage_bridge",
    ROOT / "backend" / "local-runner" / "bridge_server.py",
)
RUNNER = _load(
    "ea_factory_coverage_runner",
    ROOT / "runner" / "codex_cli_runner.py",
)


class EaFactoryBlueprintCoverageGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.blueprint = BRIDGE.normalize_ea_research_blueprint(
            BLUEPRINT_TEST.ready_blueprint(),
            require_ready=True,
        )
        self.blueprint_digest = BRIDGE.ea_research_blueprint_digest(
            self.blueprint
        )
        self.requirements = BRIDGE.ea_factory_coverage_requirements(
            self.blueprint,
            self.blueprint_digest,
        )

    def covered_source(self) -> str:
        marker_map = {
            key: {row["id"]: row["marker"] for row in rows}
            for key, rows in self.requirements["requiredMarkers"].items()
        }
        markers = [marker for rows in marker_map.values() for marker in rows.values()]
        declarations = "\n".join(
            f"const bool {marker} = true;" for marker in markers
        )
        tests = " && ".join(marker_map["testCaseIds"].values())
        return (
            "#property strict\n"
            "#define SIGNAL_NONE -1\n"
            "input int fast_period = 10;\n"
            "input int slow_period = 60;\n"
            "input double fixed_lot = 0.10;\n"
            "input double sl_pips = 30.0;\n"
            "input double tp_pips = 60.0;\n"
            f"{declarations}\n"
            "bool BlueprintCoverageSelfCheck() {\n"
            f"  return ({tests}) && (1.0 <= 1.0) && (1.1 > 1.0);\n"
            "}\n"
            "double FastValue(int shift) {\n"
            f"  if (!{marker_map['inputIds']['fast_period']} || !{marker_map['indicatorIds']['ema_fast']}) return 0.0;\n"
            "  return iMA(Symbol(), Period(), fast_period, 0, MODE_EMA, PRICE_CLOSE, shift);\n"
            "}\n"
            "double SlowValue(int shift) {\n"
            f"  if (!{marker_map['inputIds']['slow_period']} || !{marker_map['indicatorIds']['ema_slow']}) return 0.0;\n"
            "  return iMA(Symbol(), Period(), slow_period, 0, MODE_EMA, PRICE_CLOSE, shift);\n"
            "}\n"
            "bool EntrySignal() {\n"
            f"  return {marker_map['ruleIds']['ENTRY_BUY_001']} && "
            "FastValue(2) <= SlowValue(2) && FastValue(1) > SlowValue(1);\n"
            "}\n"
            "bool ExitSignal() {\n"
            f"  return {marker_map['ruleIds']['EXIT_BUY_001']} && "
            "FastValue(2) >= SlowValue(2) && FastValue(1) < SlowValue(1);\n"
            "}\n"
            "int OnInit() { return BlueprintCoverageSelfCheck() ? INIT_SUCCEEDED : INIT_FAILED; }\n"
            "void OnTick() {\n"
            "  int signal = SIGNAL_NONE;\n"
            f"  if ({marker_map['stateIds']['FLAT']} && OrdersTotal() == 0 && EntrySignal()) {{\n"
            "    double sl = Ask - sl_pips * Point;\n"
            "    double tp = Ask + tp_pips * Point;\n"
            f"    if ({marker_map['inputIds']['fixed_lot']} && {marker_map['inputIds']['sl_pips']} && {marker_map['inputIds']['tp_pips']})\n"
            "      signal = OrderSend(Symbol(), OP_BUY, fixed_lot, Ask, 3, sl, tp);\n"
            "  }\n"
            f"  if ({marker_map['stateIds']['LONG']} && OrdersTotal() > 0 && ExitSignal())\n"
            "    OrderClose(OrderTicket(), OrderLots(), Bid, 3);\n"
            "}\n"
        )

    def marker_sink_source(self) -> str:
        markers = [
            row["marker"]
            for category in self.requirements["requiredMarkers"].values()
            for row in category
        ]
        declarations = "\n".join(f"const bool {marker} = true;" for marker in markers)
        sink = " && ".join(markers)
        return (
            "#property strict\n#define SIGNAL_NONE -1\n"
            f"{declarations}\n"
            "int OnInit() { return(INIT_SUCCEEDED); }\n"
            f"void OnTick() {{ bool allMarkers = {sink}; int signal = SIGNAL_NONE; }}\n"
        )

    def covered_pine_source(self) -> str:
        marker_map = {
            key: {row["id"]: row["marker"] for row in rows}
            for key, rows in self.requirements["requiredMarkers"].items()
        }
        markers = [marker for rows in marker_map.values() for marker in rows.values()]
        declarations = "\n".join(f"bool {marker} = true" for marker in markers)
        inputs = " and ".join(marker_map["inputIds"].values())
        indicators = " and ".join(marker_map["indicatorIds"].values())
        states = marker_map["stateIds"]
        tests = " and ".join(marker_map["testCaseIds"].values())
        rules = marker_map["ruleIds"]
        return (
            "//@version=5\nstrategy(\"Covered EMA\", overlay=true)\n"
            f"{declarations}\n"
            "fastPeriod = input.int(10)\nslowPeriod = input.int(60)\n"
            "slPips = input.float(30.0)\ntpPips = input.float(60.0)\n"
            "fast = ta.ema(close, fastPeriod)\nslow = ta.ema(close, slowPeriod)\n"
            f"inputEvidence = {inputs} and fastPeriod > 0 and slowPeriod > fastPeriod\n"
            f"indicatorEvidence = {indicators} and not na(fast) and not na(slow)\n"
            f"testEvidence = {tests} and fast[2] <= slow[2] and fast[1] > slow[1]\n"
            f"entrySignal = {rules['ENTRY_BUY_001']} and fast[2] <= slow[2] and fast[1] > slow[1]\n"
            f"exitSignal = {rules['EXIT_BUY_001']} and fast[2] >= slow[2] and fast[1] < slow[1]\n"
            f"flatState = {states['FLAT']} and strategy.position_size == 0\n"
            f"longState = {states['LONG']} and strategy.position_size > 0\n"
            "if flatState and entrySignal and inputEvidence and indicatorEvidence and testEvidence\n"
            "    strategy.entry(\"Long\", strategy.long)\n"
            "    strategy.exit(\"Risk\", \"Long\", stop=close-slPips, limit=close+tpPips)\n"
            "if longState and exitSignal\n    strategy.close(\"Long\")\n"
        )

    def covered_mt5_source(self) -> str:
        return (
            "CTrade trade;\n"
            + self.covered_source()
            .replace(
                "signal = OrderSend(Symbol(), OP_BUY, fixed_lot, Ask, 3, sl, tp);",
                "signal = trade.Buy(fixed_lot, Symbol(), Ask, sl, tp) ? 0 : SIGNAL_NONE;",
            )
            .replace(
                "OrderClose(OrderTicket(), OrderLots(), Bid, 3);",
                "trade.PositionClose(Symbol());",
            )
        )

    def covered_raw_mt5_source(self) -> str:
        helpers = (
            "int SubmitEntry(double lots, double sl, double tp) {\n"
            "  MqlTradeRequest request = {}; MqlTradeResult result = {};\n"
            "  request.action = TRADE_ACTION_DEAL; request.type = ORDER_TYPE_BUY;\n"
            "  request.volume = lots; request.sl = sl; request.tp = tp;\n"
            "  return OrderSend(request, result) ? 0 : SIGNAL_NONE;\n"
            "}\n"
            "bool SubmitExit() {\n"
            "  MqlTradeRequest request = {}; MqlTradeResult result = {};\n"
            "  request.action = TRADE_ACTION_DEAL; request.position = 1;\n"
            "  request.type = ORDER_TYPE_SELL;\n"
            "  return OrderSend(request, result);\n"
            "}\n"
        )
        return (
            helpers
            + self.covered_source()
            .replace(
                "signal = OrderSend(Symbol(), OP_BUY, fixed_lot, Ask, 3, sl, tp);",
                "signal = SubmitEntry(fixed_lot, sl, tp);",
            )
            .replace(
                "OrderClose(OrderTicket(), OrderLots(), Bid, 3);",
                "SubmitExit();",
            )
        )

    def valid_trade_with_unrelated_marker_sink(self) -> str:
        markers = [
            row["marker"]
            for category in self.requirements["requiredMarkers"].values()
            for row in category
        ]
        declarations = "\n".join(f"const bool {marker} = true;" for marker in markers)
        sink = " && ".join(markers)
        return (
            "#property strict\n#define SIGNAL_NONE -1\n"
            f"{declarations}\n"
            "int OnInit() { return INIT_SUCCEEDED; }\n"
            "void OnTick() {\n"
            f"  bool unrelatedMarkerSink = {sink};\n"
            "  double fast2=iMA(Symbol(),Period(),10,0,MODE_EMA,PRICE_CLOSE,2);\n"
            "  double slow2=iMA(Symbol(),Period(),60,0,MODE_EMA,PRICE_CLOSE,2);\n"
            "  double fast1=iMA(Symbol(),Period(),10,0,MODE_EMA,PRICE_CLOSE,1);\n"
            "  double slow1=iMA(Symbol(),Period(),60,0,MODE_EMA,PRICE_CLOSE,1);\n"
            "  if (OrdersTotal()==0 && fast2<=slow2 && fast1>slow1) {\n"
            "    double sl=Ask-30*Point; double tp=Ask+60*Point;\n"
            "    OrderSend(Symbol(),OP_BUY,0.1,Ask,3,sl,tp);\n"
            "  }\n"
            "  if (OrdersTotal()>0 && fast2>=slow2 && fast1<slow1)\n"
            "    OrderClose(OrderTicket(),OrderLots(),Bid,3);\n"
            "}\n"
        )

    def runner_fixture(
        self,
        root: Path,
        build_id: str,
        platform: str = "mt4",
    ) -> tuple[str, Path, str]:
        relative = f"ea-factory/{build_id}/Source"
        source_root = root / "workspace" / relative
        source_root.mkdir(parents=True)
        record_digest = "a" * 64
        spec = {
            "schemaVersion": "ea-factory-strategy-spec-v2",
            "strategySchemaVersion": BRIDGE.EA_RESEARCH_SCHEMA_VERSION,
            "buildId": build_id,
            "sourceRecordId": "ea-source-coverage",
            "recordDigest": record_digest,
            "targetPlatform": platform,
            "eaImplementationBlueprint": self.blueprint,
            "eaBlueprintDigest": self.blueprint_digest,
            "eaReadyText": BRIDGE.render_ea_research_text(self.blueprint),
            "blueprintCoverageRequirements": self.requirements,
            "immutable": True,
        }
        spec_bytes = json.dumps(
            spec,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        (source_root / "strategy-spec-v01.json").write_bytes(spec_bytes)
        spec_digest = hashlib.sha256(spec_bytes).hexdigest()
        prompt = (
            f"[EA_FACTORY_BUILD_ID:{build_id}]"
            f"[EA_FACTORY_SOURCE_RECORD_DIGEST:{record_digest}]"
            f"[EA_FACTORY_STRATEGY_SPEC_DIGEST:{spec_digest}]"
            f"[EA_FACTORY_PLATFORM:{platform}] "
            f"Read ea-factory/{build_id}/Source/strategy-spec-v01.json."
        )
        return relative, source_root, prompt

    def test_markers_are_mql_safe_and_comments_or_strings_do_not_count(self) -> None:
        markers = [
            row["marker"]
            for category in self.requirements["requiredMarkers"].values()
            for row in category
        ]
        self.assertTrue(markers)
        self.assertLessEqual(max(map(len, markers)), 55)
        hidden = "\n".join(
            f'// {marker}\nstring fake_{index} = "{marker}";'
            for index, marker in enumerate(markers)
        )
        digest = hashlib.sha256(hidden.encode("utf-8")).hexdigest()
        manifest = BRIDGE.ea_factory_coverage_manifest(
            self.requirements,
            hidden,
            strategy_spec_digest="b" * 64,
            source_digest=digest,
            target_platform="mt4",
        )
        self.assertFalse(manifest["complete"])
        self.assertTrue(any(manifest["missing"].values()))

    def test_runner_rejects_marker_sink_without_trading_and_accepts_semantic_source(self) -> None:
        four_line_source = (
            "#property strict\n"
            "#define SIGNAL_NONE -1\n"
            "int OnInit() { return(INIT_SUCCEEDED); }\n"
            "void OnTick() { int signal = SIGNAL_NONE; }\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            relative, source_root, prompt = self.runner_fixture(
                root,
                "ea-build-coverage-runner",
            )
            with (
                mock.patch.object(RUNNER, "PROJECT_ROOT", root),
                mock.patch.object(RUNNER, "AUTO_WORKSPACE_ROOT", root / "workspace"),
            ):
                with self.assertRaisesRegex(ValueError, "does not cover every"):
                    RUNNER.materialize_ea_factory_source_result(
                        json.dumps({"fileName": "TinyEA.mq4", "content": four_line_source}),
                        prompt,
                        relative,
                    )
                self.assertFalse((source_root / "TinyEA.mq4").exists())

                with self.assertRaisesRegex(ValueError, "does not cover every"):
                    RUNNER.materialize_ea_factory_source_result(
                        json.dumps({
                            "fileName": "MarkerSinkEA.mq4",
                            "content": self.marker_sink_source(),
                        }),
                        prompt,
                        relative,
                    )
                self.assertFalse((source_root / "MarkerSinkEA.mq4").exists())

                result = RUNNER.materialize_ea_factory_source_result(
                    json.dumps({"fileName": "CoveredEA.mq4", "content": self.covered_source()}),
                    prompt,
                    relative,
                )
            values = {
                row["field"]: row["value"] for row in result["contractFields"]
            }
            manifest = json.loads(values["blueprintCoverageManifest"])
            self.assertTrue(manifest["complete"])
            self.assertEqual(manifest["expected"], manifest["observed"])
            self.assertTrue(all(not rows for rows in manifest["semanticMissing"].values()))
            self.assertEqual(manifest["capabilityMissing"], [])
            self.assertEqual(manifest["targetPlatform"], "mt4")
            self.assertLessEqual(len(values["blueprintCoverageManifest"]), 12000)
            self.assertTrue((source_root / "CoveredEA.mq4").is_file())

    def test_runner_propagates_mt5_into_semantic_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            relative, source_root, prompt = self.runner_fixture(
                root,
                "ea-build-coverage-runner-mt5",
                "mt5",
            )
            with (
                mock.patch.object(RUNNER, "PROJECT_ROOT", root),
                mock.patch.object(RUNNER, "AUTO_WORKSPACE_ROOT", root / "workspace"),
            ):
                result = RUNNER.materialize_ea_factory_source_result(
                    json.dumps({
                        "fileName": "CoveredRawEA.mq5",
                        "content": self.covered_raw_mt5_source(),
                    }),
                    prompt,
                    relative,
                )
            values = {row["field"]: row["value"] for row in result["contractFields"]}
            manifest = json.loads(values["blueprintCoverageManifest"])
            self.assertEqual(manifest["targetPlatform"], "mt5")
            self.assertTrue(manifest["complete"])
            self.assertTrue((source_root / "CoveredRawEA.mq5").is_file())

    def test_marker_sink_has_all_tokens_but_fails_semantic_capabilities(self) -> None:
        source = self.marker_sink_source()
        manifest = BRIDGE.ea_factory_coverage_manifest(
            self.requirements,
            source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertEqual(manifest["expected"], manifest["observed"])
        self.assertFalse(manifest["complete"])
        self.assertIn("REACHABLE_TRADE_ENTRY_MISSING", manifest["capabilityMissing"])
        self.assertIn("REACHABLE_TRADE_EXIT_MISSING", manifest["capabilityMissing"])
        self.assertTrue(any(manifest["semanticMissing"].values()))

    def test_unreachable_dummy_order_calls_do_not_satisfy_trade_paths(self) -> None:
        source = self.marker_sink_source() + (
            "\nvoid UnusedFakeTrading() {\n"
            "  double sl = 1.0; double tp = 2.0;\n"
            "  OrderSend(Symbol(), OP_BUY, 0.1, Ask, 3, sl, tp);\n"
            "  OrderClose(OrderTicket(), OrderLots(), Bid, 3);\n"
            "}\n"
        )
        manifest = BRIDGE.ea_factory_coverage_manifest(
            self.requirements,
            source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(manifest["complete"])
        self.assertFalse(manifest["capabilityEvidence"]["tradeEntry"])
        self.assertFalse(manifest["capabilityEvidence"]["tradeExit"])

    def test_valid_trading_with_unrelated_marker_sink_is_rejected(self) -> None:
        source = self.valid_trade_with_unrelated_marker_sink()
        manifest = BRIDGE.ea_factory_coverage_manifest(
            self.requirements,
            source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertEqual(manifest["expected"], manifest["observed"])
        self.assertTrue(manifest["capabilityEvidence"]["tradeEntry"])
        self.assertTrue(manifest["capabilityEvidence"]["tradeExit"])
        self.assertEqual(manifest["capabilityMissing"], [])
        self.assertFalse(manifest["complete"])
        self.assertEqual(
            manifest["semanticMissing"]["ruleIds"],
            self.requirements["requiredIds"]["ruleIds"],
        )

    def test_signal_helper_marker_assignment_sink_does_not_bind_trade_action(self) -> None:
        marker_map = {
            key: {row["id"]: row["marker"] for row in rows}
            for key, rows in self.requirements["requiredMarkers"].items()
        }
        cases = (
            (
                "ENTRY_BUY_001",
                (
                    f"  return {marker_map['ruleIds']['ENTRY_BUY_001']} && "
                    "FastValue(2) <= SlowValue(2) && FastValue(1) > SlowValue(1);"
                ),
                (
                    f"  bool unrelatedRuleMarker = {marker_map['ruleIds']['ENTRY_BUY_001']};\n"
                    "  return FastValue(2) <= SlowValue(2) && FastValue(1) > SlowValue(1);"
                ),
            ),
            (
                "EXIT_BUY_001",
                (
                    f"  return {marker_map['ruleIds']['EXIT_BUY_001']} && "
                    "FastValue(2) >= SlowValue(2) && FastValue(1) < SlowValue(1);"
                ),
                (
                    f"  bool unrelatedRuleMarker = {marker_map['ruleIds']['EXIT_BUY_001']};\n"
                    "  return FastValue(2) >= SlowValue(2) && FastValue(1) < SlowValue(1);"
                ),
            ),
        )
        for rule_id, old, replacement in cases:
            with self.subTest(rule_id=rule_id):
                source = self.covered_source().replace(old, replacement)
                self.assertNotEqual(source, self.covered_source())
                manifest = BRIDGE.ea_factory_coverage_manifest(
                    self.requirements,
                    source,
                    strategy_spec_digest="b" * 64,
                    source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
                    target_platform="mt4",
                )
                # The marker token remains in a reachable trading helper and
                # every trading capability is still present.  It nevertheless
                # does not control the helper result or the order branch.
                self.assertEqual(manifest["expected"], manifest["observed"])
                self.assertEqual(manifest["capabilityMissing"], [])
                self.assertFalse(manifest["complete"])
                self.assertIn(rule_id, manifest["semanticMissing"]["ruleIds"])

    def test_state_marker_assignment_sink_does_not_bind_trade_action(self) -> None:
        marker_map = {
            key: {row["id"]: row["marker"] for row in rows}
            for key, rows in self.requirements["requiredMarkers"].items()
        }
        source = self.covered_source().replace(
            f"  if ({marker_map['stateIds']['FLAT']} && OrdersTotal() == 0 && EntrySignal()) {{",
            (
                f"  bool unrelatedFlatStateMarker = {marker_map['stateIds']['FLAT']};\n"
                "  if (OrdersTotal() == 0 && EntrySignal()) {"
            ),
        ).replace(
            f"  if ({marker_map['stateIds']['LONG']} && OrdersTotal() > 0 && ExitSignal())",
            (
                f"  bool unrelatedLongStateMarker = {marker_map['stateIds']['LONG']};\n"
                "  if (OrdersTotal() > 0 && ExitSignal())"
            ),
        )
        manifest = BRIDGE.ea_factory_coverage_manifest(
            self.requirements,
            source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertEqual(manifest["expected"], manifest["observed"])
        self.assertEqual(manifest["capabilityMissing"], [])
        self.assertFalse(manifest["complete"])
        self.assertEqual(
            manifest["semanticMissing"]["stateIds"],
            ["FLAT", "LONG"],
        )

    def test_trade_action_token_without_reachable_order_send_is_rejected(self) -> None:
        source = self.covered_raw_mt5_source().replace(
            "return OrderSend(request, result) ? 0 : SIGNAL_NONE;",
            "return TRADE_ACTION_DEAL == request.action ? 0 : SIGNAL_NONE;",
        )
        manifest = BRIDGE.ea_factory_coverage_manifest(
            self.requirements,
            source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="mt5",
        )
        # The remaining OrderSend belongs only to the exit call-chain; the
        # entry branch has TRADE_ACTION_DEAL but no submission call.
        self.assertFalse(manifest["complete"])
        self.assertFalse(manifest["capabilityEvidence"]["tradeEntry"])
        self.assertIn("REACHABLE_TRADE_ENTRY_MISSING", manifest["capabilityMissing"])
        self.assertIn("ENTRY_BUY_001", manifest["semanticMissing"]["ruleIds"])

    def test_oncalculate_is_not_accepted_as_an_ea_trading_root(self) -> None:
        source = self.covered_source().replace("void OnTick()", "void OnCalculate()")
        manifest = BRIDGE.ea_factory_coverage_manifest(
            self.requirements,
            source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(manifest["complete"])
        self.assertIn(
            "REACHABLE_PROGRAM_ENTRY_MISSING",
            manifest["capabilityMissing"],
        )

    def test_mt5_ctrade_entry_and_exit_paths_are_recognized(self) -> None:
        source = self.covered_mt5_source()
        manifest = BRIDGE.ea_factory_coverage_manifest(
            self.requirements,
            source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="mt5",
        )
        self.assertTrue(manifest["complete"], manifest)
        self.assertTrue(manifest["capabilityEvidence"]["tradeEntry"])
        self.assertTrue(manifest["capabilityEvidence"]["tradeExit"])

        fake_source = source.replace("CTrade trade;", "FakeTrade trade;")
        fake_manifest = BRIDGE.ea_factory_coverage_manifest(
            self.requirements,
            fake_source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(fake_source.encode("utf-8")).hexdigest(),
            target_platform="mt5",
        )
        self.assertFalse(fake_manifest["complete"])
        self.assertIn(
            "REACHABLE_TRADE_ENTRY_MISSING",
            fake_manifest["capabilityMissing"],
        )

    def test_raw_mt5_request_order_send_call_chains_are_recognized(self) -> None:
        source = self.covered_raw_mt5_source()
        manifest = BRIDGE.ea_factory_coverage_manifest(
            self.requirements,
            source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="mt5",
        )
        self.assertTrue(manifest["complete"], manifest)
        self.assertEqual(manifest["targetPlatform"], "mt5")
        self.assertTrue(manifest["capabilityEvidence"]["tradeEntry"])
        self.assertTrue(manifest["capabilityEvidence"]["tradeExit"])

    def test_management_marker_must_guard_reachable_modify_action(self) -> None:
        blueprint = copy.deepcopy(self.blueprint)
        blueprint["orderManagement"]["rules"].append({
            "ruleId": "MANAGE_STOP_001",
            "phase": "management",
            "side": "buy",
            "enabled": True,
            "sourceStatus": "verified_fact",
            "sourceRefs": ["S1"],
            "expression": {"op": ">", "left": 2, "right": 1},
            "humanTextTh": "ขยับ stop เมื่อเงื่อนไขเป็นจริง",
        })
        modified_digest = hashlib.sha256(json.dumps(
            blueprint,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        requirements = BRIDGE.ea_factory_coverage_requirements(
            blueprint,
            modified_digest,
        )
        marker = next(
            row["marker"]
            for row in requirements["requiredMarkers"]["ruleIds"]
            if row["id"] == "MANAGE_STOP_001"
        )
        management = (
            f"const bool {marker} = true;\n"
            "void ManagePosition() {\n"
            f"  if ({marker} && OrdersTotal() > 0)\n"
            "    OrderModify(OrderTicket(), OrderOpenPrice(), Bid-10*Point, 0, 0);\n"
            "}\n"
        )
        source = management + self.covered_source().replace(
            "void OnTick() {\n",
            "void OnTick() {\n  ManagePosition();\n",
        )
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        manifest = BRIDGE.ea_factory_coverage_manifest(
            requirements,
            source,
            strategy_spec_digest="b" * 64,
            source_digest=digest,
            target_platform="mt4",
        )
        self.assertTrue(manifest["complete"], manifest)
        self.assertTrue(manifest["capabilityEvidence"]["tradeManagement"])

        unrelated = source.replace(
            f"if ({marker} && OrdersTotal() > 0)",
            f"bool unrelated = {marker};\n  if (OrdersTotal() > 0)",
        )
        unrelated_manifest = BRIDGE.ea_factory_coverage_manifest(
            requirements,
            unrelated,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(unrelated.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(unrelated_manifest["complete"])
        self.assertEqual(
            unrelated_manifest["semanticMissing"]["ruleIds"],
            ["MANAGE_STOP_001"],
        )

    def test_tradingview_requires_real_strategy_entry_exit_and_accepts_valid_paths(self) -> None:
        source = self.covered_pine_source()
        manifest = BRIDGE.ea_factory_coverage_manifest(
            self.requirements,
            source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="tradingview",
        )
        self.assertTrue(manifest["complete"], manifest)
        self.assertTrue(all(not rows for rows in manifest["semanticMissing"].values()))
        self.assertTrue(manifest["capabilityEvidence"]["tradeEntry"])
        self.assertTrue(manifest["capabilityEvidence"]["tradeExit"])

    def test_backend_rejects_missing_manifest_id_and_accepts_exact_recompute(self) -> None:
        build_id = "ea-build-coverage-backend"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with mock.patch.object(BRIDGE, "PROJECT_ROOT", root):
                source_record = {
                    "sourceRecordId": "ea-source-coverage",
                    "recordDigest": "a" * 64,
                    "sourceKind": "verified_deep_research_sheet",
                    "sourceKey": "deep-coverage",
                    "core": {},
                    "downstream": {},
                    "sourceUrls": ["https://example.com/strategy"],
                    "eaImplementationBlueprint": self.blueprint,
                    "eaBlueprintDigest": self.blueprint_digest,
                }
                workspace = BRIDGE._ea_factory_create_build_workspace(
                    build_id,
                    source_record,
                    "mt5",
                )
                source_path = (
                    root
                    / "workspace"
                    / "ea-factory"
                    / build_id
                    / "Source"
                    / "CoveredEA.mq5"
                )
                source_text = self.covered_raw_mt5_source()
                source_path.write_text(source_text, encoding="utf-8")
                source_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
                expected_manifest = BRIDGE.ea_factory_coverage_manifest(
                    self.requirements,
                    source_text,
                    strategy_spec_digest=workspace["strategySpecDigest"],
                    source_digest=source_digest,
                    target_platform="mt5",
                )
                stages = BRIDGE._ea_factory_initial_stages(
                    "mt4",
                    {"id": "mission-spec-coverage"},
                    {"id": "report-spec-coverage"},
                )
                build = {
                    "id": build_id,
                    "sourceReportId": "report-spec-coverage",
                    "sourceRecordId": "ea-source-coverage",
                    "sourceRecordDigest": "a" * 64,
                    "platform": "mt5",
                    "brief": "",
                    "workspace": workspace,
                    "stages": stages,
                    "versions": [],
                }
                values = {
                    "sourceFiles": json.dumps([
                        f"workspace/ea-factory/{build_id}/Source/CoveredEA.mq5"
                    ]),
                    "sourceDigest": source_digest,
                    "sourceRecordDigest": "a" * 64,
                    "strategySpecDigest": workspace["strategySpecDigest"],
                    "blueprintCoverageManifest": json.dumps(expected_manifest),
                    "platform": "mt5",
                }
                report = {
                    "id": "report-generation-coverage",
                    "type": "ea_build_report",
                    "linkedPropId": "right_server_racks",
                    "workflowContext": {
                        "propId": "right_server_racks",
                        "actionId": "build_strategy_code",
                    },
                    "metrics": {
                        "workflowOutput": {
                            "applicable": True,
                            "valid": True,
                            "expectedFields": list(BRIDGE.EA_FACTORY_STRUCTURED_SOURCE_OUTPUT_FIELDS),
                            "providedFields": list(BRIDGE.EA_FACTORY_STRUCTURED_SOURCE_OUTPUT_FIELDS),
                            "missingFields": [],
                            "expectedEvidenceKinds": list(BRIDGE.EA_FACTORY_STRUCTURED_SOURCE_EVIDENCE_KINDS),
                            "providedEvidenceKinds": list(BRIDGE.EA_FACTORY_STRUCTURED_SOURCE_EVIDENCE_KINDS),
                            "missingEvidenceKinds": [],
                            "values": values,
                        }
                    },
                }
                tampered = copy.deepcopy(expected_manifest)
                category = next(key for key, rows in tampered["observed"].items() if rows)
                tampered["observed"][category].pop()
                report["metrics"]["workflowOutput"]["values"][
                    "blueprintCoverageManifest"
                ] = json.dumps(tampered)
                with mock.patch.object(
                    BRIDGE,
                    "_ea_factory_report_binding_valid",
                    return_value=True,
                ):
                    self.assertFalse(
                        BRIDGE._ea_factory_generation_evidence_valid(
                            build,
                            report,
                            ingest_sources=False,
                        )
                    )
                    report["metrics"]["workflowOutput"]["values"][
                        "blueprintCoverageManifest"
                    ] = json.dumps(expected_manifest)
                    self.assertTrue(
                        BRIDGE._ea_factory_generation_evidence_valid(
                            build,
                            report,
                            ingest_sources=False,
                        )
                    )
                self.assertEqual(
                    build["blueprintCoverageManifest"],
                    expected_manifest,
                )
                self.assertEqual(expected_manifest["targetPlatform"], "mt5")

                # Even a Worker-supplied manifest recomputed from a file that
                # names every marker must fail when the actual immutable bytes
                # only contain a no-trade marker sink.
                sink_text = self.marker_sink_source()
                source_path.write_text(sink_text, encoding="utf-8")
                sink_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
                sink_manifest = BRIDGE.ea_factory_coverage_manifest(
                    self.requirements,
                    sink_text,
                    strategy_spec_digest=workspace["strategySpecDigest"],
                    source_digest=sink_digest,
                    target_platform="mt5",
                )
                self.assertFalse(sink_manifest["complete"])
                values["sourceDigest"] = sink_digest
                values["blueprintCoverageManifest"] = json.dumps(sink_manifest)
                with mock.patch.object(
                    BRIDGE,
                    "_ea_factory_report_binding_valid",
                    return_value=True,
                ):
                    self.assertFalse(
                        BRIDGE._ea_factory_generation_evidence_valid(
                            build,
                            report,
                            ingest_sources=False,
                        )
                    )


if __name__ == "__main__":
    unittest.main()
