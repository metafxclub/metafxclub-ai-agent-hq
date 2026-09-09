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

    @staticmethod
    def semantic_markers(
        requirements: dict,
        kind: str,
        identity: str | None = None,
    ) -> list[str]:
        marker_by_id = {
            row["id"]: row["marker"]
            for row in requirements["requiredMarkers"]["semanticDigests"]
        }
        return [
            marker_by_id[row["id"]]
            for row in requirements["semanticProfile"]["semanticBindings"]
            if row["kind"] == kind
            and (identity is None or row["identity"] == identity)
        ]

    @staticmethod
    def joined_markers(markers: list[str]) -> str:
        return " && ".join(markers) if markers else "true"

    @staticmethod
    def semantic_binding_ids(requirements: dict, kind: str) -> list[str]:
        return [
            row["id"]
            for row in requirements["semanticProfile"]["semanticBindings"]
            if row["kind"] == kind
        ]

    @staticmethod
    def top_digest_marker(requirements: dict) -> str:
        return requirements["requiredMarkers"]["blueprintDigests"][0]["marker"]

    def refresh_only_top_digest_marker(
        self,
        source: str,
        old_requirements: dict,
        new_requirements: dict,
    ) -> str:
        old_marker = self.top_digest_marker(old_requirements)
        new_marker = self.top_digest_marker(new_requirements)
        self.assertNotEqual(old_marker, new_marker)
        refreshed = source.replace(old_marker, new_marker)
        self.assertNotEqual(refreshed, source)
        return refreshed

    def covered_source(self, requirements: dict | None = None) -> str:
        requirements = requirements or self.requirements
        marker_map = {
            key: {row["id"]: row["marker"] for row in rows}
            for key, rows in requirements["requiredMarkers"].items()
        }
        markers = [marker for rows in marker_map.values() for marker in rows.values()]
        declarations = "\n".join(
            f"const bool {marker} = true;" for marker in markers
        )
        tests = list(marker_map["testCaseIds"].values())
        tests.extend(self.semantic_markers(requirements, "test_vector"))
        initialization_semantics: list[str] = []
        for kind in (
            "bar_semantics",
            "execution_contract",
            "pseudocode",
        ):
            initialization_semantics.extend(self.semantic_markers(requirements, kind))
        tests.extend(initialization_semantics)
        tests_expression = self.joined_markers(tests)
        blueprint_digest = next(iter(marker_map["blueprintDigests"].values()))
        fast_indicator_semantics = self.joined_markers(
            self.semantic_markers(requirements, "indicator", "ema_fast")
        )
        slow_indicator_semantics = self.joined_markers(
            self.semantic_markers(requirements, "indicator", "ema_slow")
        )
        entry_semantics = self.joined_markers(
            self.semantic_markers(requirements, "risk_sizing")
            + self.semantic_markers(requirements, "protection")
        )
        flat_state_semantics = self.joined_markers(
            self.semantic_markers(requirements, "state_transition", "FLAT")
        )
        long_state_semantics = self.joined_markers(
            self.semantic_markers(requirements, "state_transition", "LONG")
        )
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
            f"  return {blueprint_digest} && ({tests_expression}) && (1.0 <= 1.0) && (1.1 > 1.0);\n"
            "}\n"
            "double FastValue(int shift) {\n"
            f"  if (!{marker_map['inputIds']['fast_period']} || !{marker_map['indicatorIds']['ema_fast']} || !{fast_indicator_semantics}) return 0.0;\n"
            "  return iMA(Symbol(), Period(), fast_period, 0, MODE_EMA, PRICE_CLOSE, shift);\n"
            "}\n"
            "double SlowValue(int shift) {\n"
            f"  if (!{marker_map['inputIds']['slow_period']} || !{marker_map['indicatorIds']['ema_slow']} || !{slow_indicator_semantics}) return 0.0;\n"
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
            f"  if ({marker_map['stateIds']['FLAT']} && {flat_state_semantics} && OrdersTotal() == 0 && EntrySignal()) {{\n"
            "    double sl = Ask - sl_pips * Point;\n"
            "    double tp = Ask + tp_pips * Point;\n"
            f"    if ({marker_map['inputIds']['fixed_lot']} && {marker_map['inputIds']['sl_pips']} && {marker_map['inputIds']['tp_pips']} && {entry_semantics})\n"
            "      signal = OrderSend(Symbol(), OP_BUY, fixed_lot, Ask, 3, sl, tp);\n"
            "  }\n"
            f"  if ({marker_map['stateIds']['LONG']} && {long_state_semantics} && OrdersTotal() > 0 && ExitSignal())\n"
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
        tests = list(marker_map["testCaseIds"].values())
        tests.extend(self.semantic_markers(self.requirements, "test_vector"))
        tests_expression = " and ".join(tests)
        rules = marker_map["ruleIds"]
        blueprint_digest = next(iter(marker_map["blueprintDigests"].values()))
        initialization_semantics: list[str] = []
        for kind in ("bar_semantics", "execution_contract", "pseudocode"):
            initialization_semantics.extend(self.semantic_markers(self.requirements, kind))
        blueprint_semantics = " and ".join(initialization_semantics)
        risk_semantics = " and ".join(
            self.semantic_markers(self.requirements, "risk_sizing")
            + self.semantic_markers(self.requirements, "protection")
        )
        fast_semantics = " and ".join(
            self.semantic_markers(self.requirements, "indicator", "ema_fast")
        )
        slow_semantics = " and ".join(
            self.semantic_markers(self.requirements, "indicator", "ema_slow")
        )
        flat_semantics = " and ".join(
            self.semantic_markers(self.requirements, "state_transition", "FLAT")
        )
        long_semantics = " and ".join(
            self.semantic_markers(self.requirements, "state_transition", "LONG")
        )
        return (
            "//@version=5\nstrategy(\"Covered EMA\", overlay=true)\n"
            f"{declarations}\n"
            "fastPeriod = input.int(10)\nslowPeriod = input.int(60)\n"
            "slPips = input.float(30.0)\ntpPips = input.float(60.0)\n"
            "fast = ta.ema(close, fastPeriod)\nslow = ta.ema(close, slowPeriod)\n"
            f"inputEvidence = {inputs} and fastPeriod > 0 and slowPeriod > fastPeriod\n"
            f"indicatorEvidence = {indicators} and {fast_semantics} and {slow_semantics} and not na(fast) and not na(slow)\n"
            f"testEvidence = {tests_expression} and fast[2] <= slow[2] and fast[1] > slow[1]\n"
            f"blueprintEvidence = {blueprint_digest} and {blueprint_semantics} and fast[2] <= slow[2]\n"
            f"entrySignal = {rules['ENTRY_BUY_001']} and fast[2] <= slow[2] and fast[1] > slow[1]\n"
            f"exitSignal = {rules['EXIT_BUY_001']} and fast[2] >= slow[2] and fast[1] < slow[1]\n"
            f"flatState = {states['FLAT']} and {flat_semantics} and strategy.position_size == 0\n"
            f"longState = {states['LONG']} and {long_semantics} and strategy.position_size > 0\n"
            f"riskEvidence = {risk_semantics} and close > 0\n"
            "if blueprintEvidence and flatState and entrySignal and inputEvidence and indicatorEvidence and testEvidence and riskEvidence\n"
            "    strategy.entry(\"Long\", strategy.long)\n"
            "    strategy.exit(\"Risk\", \"Long\", stop=close-slPips, limit=close+tpPips)\n"
            "if longState and exitSignal\n    strategy.close(\"Long\")\n"
        )

    def covered_mt5_source(self, requirements: dict | None = None) -> str:
        return (
            "CTrade trade;\n"
            + self.covered_source(requirements)
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

    def requirements_for(self, blueprint: dict) -> tuple[dict, str, dict]:
        normalized = BRIDGE.normalize_ea_research_blueprint(
            blueprint,
            require_ready=True,
        )
        digest = BRIDGE.ea_research_blueprint_digest(normalized)
        return (
            normalized,
            digest,
            BRIDGE.ea_factory_coverage_requirements(normalized, digest),
        )

    def covered_recovery_source(self, requirements: dict) -> str:
        recovery_marker = next(
            row["marker"]
            for row in requirements["requiredMarkers"]["ruleIds"]
            if row["id"] == "RECOVERY_LEVEL_001"
        )
        recovery_state_marker = next(
            row["marker"]
            for row in requirements["requiredMarkers"]["stateIds"]
            if row["id"] == "RECOVERY"
        )
        recovery_semantic = self.semantic_markers(
            requirements,
            "recovery_safety",
        )[0]
        recovery_state_semantic = self.semantic_markers(
            requirements,
            "state_transition",
            "RECOVERY",
        )[0]
        long_state_semantic = self.semantic_markers(
            requirements,
            "state_transition",
            "LONG",
        )[0]
        recovery_helper = (
            "bool RecoverySignal() {\n"
            f"  return {recovery_state_marker} && {recovery_state_semantic} && "
            f"{long_state_semantic} && {recovery_marker} && {recovery_semantic} && "
            "OrdersTotal() > 0 && OrdersTotal() < 3 && fixed_lot * 2.0 <= 0.4 "
            "&& fixed_lot * OrdersTotal() <= 1.0 && AccountProfit() <= -10.0 "
            "&& AccountEquity() >= AccountBalance() * 0.80;\n"
            "}\n"
            "bool RecoveryExitSignal() {\n"
            f"  return {recovery_semantic} && OrdersTotal() > 0 && "
            "(AccountProfit() >= 10.0 || AccountProfit() <= -50.0 "
            "|| AccountEquity() <= AccountBalance() * 0.80);\n"
            "}\n"
        )
        return recovery_helper + self.covered_source(requirements).replace(
            "void OnTick() {\n",
            (
                "void OnTick() {\n"
                "  if (RecoveryExitSignal())\n"
                "    OrderClose(OrderTicket(), OrderLots(), Bid, 3);\n"
                "  if (RecoverySignal())\n"
                "    OrderSend(Symbol(), OP_BUY, fixed_lot * 2.0, Ask, 3, 0, 0);\n"
            ),
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
        self.assertEqual(
            self.requirements["schemaVersion"],
            "ea-factory-blueprint-coverage-requirements-v3",
        )
        self.assertEqual(
            self.requirements["requiredIds"]["blueprintDigests"],
            [self.blueprint_digest],
        )
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

    def test_blueprint_digest_marker_must_control_initialization_self_check(self) -> None:
        digest_marker = self.requirements["requiredMarkers"]["blueprintDigests"][0][
            "marker"
        ]
        source = self.covered_source().replace(
            f"return {digest_marker} && (",
            f"bool ignoredBlueprint = {digest_marker};\n  return (",
        )
        manifest = BRIDGE.ea_factory_coverage_manifest(
            self.requirements,
            source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertIn(
            self.blueprint_digest,
            manifest["semanticMissing"]["blueprintDigests"],
        )
        self.assertFalse(manifest["complete"])

        on_tick_only = self.covered_source().replace(
            f"return {digest_marker} && (",
            "return (",
        ).replace(
            "void OnTick() {\n",
            f"void OnTick() {{\n  bool lateBlueprintCheck = {digest_marker};\n",
        )
        late_manifest = BRIDGE.ea_factory_coverage_manifest(
            self.requirements,
            on_tick_only,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(on_tick_only.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertIn(
            self.blueprint_digest,
            late_manifest["semanticMissing"]["blueprintDigests"],
        )

    def test_canonical_blueprint_mutations_invalidate_stale_generated_source(self) -> None:
        mutations = {
            "risk-cap": lambda value: value["riskAndSizing"].update(
                maxTotalLots=0.9
            ),
            "stop-loss-formula": lambda value: value["tpSl"]["stopLoss"].update(
                valueInputRef="tp_pips"
            ),
            "indicator-parameters": lambda value: value["indicators"][0][
                "parameters"
            ].update(period={"inputRef": "slow_period"}),
            "indicator-timeframe": lambda value: value["indicators"][0].update(
                timeframe="execution"
            ),
            "indicator-applied-price": lambda value: value["indicators"][0].update(
                appliedPrice="open"
            ),
            "precedence": lambda value: value["precedence"].__setitem__(
                2,
                "trailing_management",
            ),
            "pseudocode": lambda value: value["pseudocode"]["lines"].__setitem__(
                0,
                value["pseudocode"]["lines"][0] + " Use the exact broker tick size.",
            ),
        }
        stale_source = self.covered_source()
        stale_marker = self.requirements["requiredMarkers"]["blueprintDigests"][0][
            "marker"
        ]
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                changed = copy.deepcopy(self.blueprint)
                mutate(changed)
                _normalized, changed_digest, requirements = self.requirements_for(changed)
                changed_marker = requirements["requiredMarkers"]["blueprintDigests"][0][
                    "marker"
                ]
                self.assertNotEqual(changed_digest, self.blueprint_digest)
                self.assertNotEqual(changed_marker, stale_marker)
                manifest = BRIDGE.ea_factory_coverage_manifest(
                    requirements,
                    stale_source,
                    strategy_spec_digest="b" * 64,
                    source_digest=hashlib.sha256(stale_source.encode("utf-8")).hexdigest(),
                    target_platform="mt4",
                )
                self.assertEqual(
                    manifest["missing"]["blueprintDigests"],
                    [changed_digest],
                )
                self.assertFalse(manifest["complete"])

    def test_subtree_digest_markers_reject_top_level_only_refresh(self) -> None:
        def mutate_state(value: dict) -> None:
            value["stateMachine"][0]["transitions"][0]["whenRuleIds"].append(
                "EXIT_BUY_001"
            )

        def mutate_test_vector(value: dict) -> None:
            row = next(
                item
                for item in value["testCases"]
                if item["caseId"] == "entry-buy-positive"
            )
            row["given"]["fast2"] = 0.9

        mutations = {
            "risk-cap": (
                "risk_sizing",
                lambda value: value["riskAndSizing"].update(maxTotalLots=0.9),
            ),
            "protection-formula": (
                "protection",
                lambda value: value["tpSl"]["stopLoss"].update(
                    valueInputRef="tp_pips"
                ),
            ),
            "indicator-timeframe-parameters-buffer": (
                "indicator",
                lambda value: value["indicators"][0].update(appliedPrice="open"),
            ),
            "state-transition-rule-vector": ("state_transition", mutate_state),
            "test-given-vector": ("test_vector", mutate_test_vector),
            "pseudocode": (
                "pseudocode",
                lambda value: value["pseudocode"]["lines"].__setitem__(
                    0,
                    value["pseudocode"]["lines"][0]
                    + " Normalize once more before submitting.",
                ),
            ),
            "execution-precedence": (
                "execution_contract",
                lambda value: value["precedence"].__setitem__(
                    2,
                    "position_management_exact",
                ),
            ),
        }
        stale_source = self.covered_source()
        for label, (binding_kind, mutate) in mutations.items():
            with self.subTest(label=label):
                changed = copy.deepcopy(self.blueprint)
                mutate(changed)
                _normalized, _digest, requirements = self.requirements_for(changed)
                refreshed = self.refresh_only_top_digest_marker(
                    stale_source,
                    self.requirements,
                    requirements,
                )
                manifest = BRIDGE.ea_factory_coverage_manifest(
                    requirements,
                    refreshed,
                    strategy_spec_digest="b" * 64,
                    source_digest=hashlib.sha256(refreshed.encode("utf-8")).hexdigest(),
                    target_platform="mt4",
                )
                self.assertEqual(manifest["missing"]["blueprintDigests"], [])
                self.assertTrue(
                    set(self.semantic_binding_ids(requirements, binding_kind))
                    .intersection(manifest["semanticMissing"]["semanticDigests"]),
                    manifest,
                )
                self.assertFalse(manifest["complete"])

    def test_requirements_reject_digest_not_computed_from_exact_blueprint(self) -> None:
        with self.assertRaisesRegex(ValueError, "coverage binding is invalid"):
            BRIDGE.ea_factory_coverage_requirements(self.blueprint, "f" * 64)

    def test_manifest_fails_closed_on_resigned_malformed_semantic_binding(self) -> None:
        mutations = {
            "empty-actions": lambda row: row.update(actions=[]),
            "digest-id-mismatch": lambda row: row.update(digest="0" * 64),
            "unsupported-kind": lambda row: row.update(kind="opaque_claim"),
        }
        source = self.covered_source()
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                requirements = copy.deepcopy(self.requirements)
                mutate(requirements["semanticProfile"]["semanticBindings"][0])
                unsigned = copy.deepcopy(requirements)
                unsigned.pop("requirementsDigest")
                requirements["requirementsDigest"] = hashlib.sha256(
                    json.dumps(
                        unsigned,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                ).hexdigest()
                with self.assertRaisesRegex(ValueError, "semantic bindings"):
                    BRIDGE.ea_factory_coverage_manifest(
                        requirements,
                        source,
                        strategy_spec_digest="b" * 64,
                        source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
                        target_platform="mt4",
                    )

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
            f"if ({marker_map['stateIds']['FLAT']} &&",
            "if (true &&",
            1,
        ).replace(
            f"if ({marker_map['stateIds']['LONG']} &&",
            "if (true &&",
            1,
        ).replace(
            "void OnTick() {\n",
            (
                "void OnTick() {\n"
                f"  bool unrelatedFlatStateMarker = {marker_map['stateIds']['FLAT']};\n"
                f"  bool unrelatedLongStateMarker = {marker_map['stateIds']['LONG']};\n"
            ),
            1,
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
            "phase": "modify",
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
        role = next(
            row
            for row in requirements["semanticProfile"]["ruleRoles"]
            if row["id"] == "MANAGE_STOP_001"
        )
        self.assertEqual(role["phase"], "modify")
        self.assertEqual(role["action"], "management")
        self.assertTrue(requirements["semanticProfile"]["requiresManagement"])
        marker = next(
            row["marker"]
            for row in requirements["requiredMarkers"]["ruleIds"]
            if row["id"] == "MANAGE_STOP_001"
        )
        management = (
            "void ManagePosition() {\n"
            f"  if ({marker} && OrdersTotal() > 0)\n"
            "    OrderModify(OrderTicket(), OrderOpenPrice(), Bid-10*Point, 0, 0);\n"
            "}\n"
        )
        source = management + self.covered_source(requirements).replace(
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

    def test_enabled_recovery_rule_requires_reachable_recovery_entry(self) -> None:
        missing_rule_blueprint = copy.deepcopy(self.blueprint)
        missing_rule_blueprint["recovery"].update(
            enabled=True,
            mode="martingale",
        )
        missing_rule_digest = hashlib.sha256(
            json.dumps(
                missing_rule_blueprint,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        missing_rule_requirements = BRIDGE.ea_factory_coverage_requirements(
            missing_rule_blueprint,
            missing_rule_digest,
        )
        missing_rule_source = self.covered_source(missing_rule_requirements)
        missing_rule_manifest = BRIDGE.ea_factory_coverage_manifest(
            missing_rule_requirements,
            missing_rule_source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(
                missing_rule_source.encode("utf-8")
            ).hexdigest(),
            target_platform="mt4",
        )
        self.assertIn(
            "BLUEPRINT_RECOVERY_RULE_MISSING",
            missing_rule_manifest["capabilityMissing"],
        )

        active = BLUEPRINT_TEST.activate_martingale_recovery(
            copy.deepcopy(self.blueprint)
        )
        normalized, _digest, requirements = self.requirements_for(active)
        profile = requirements["semanticProfile"]
        role = next(
            row
            for row in profile["ruleRoles"]
            if row["id"] == "RECOVERY_LEVEL_001"
        )
        self.assertEqual(role["phase"], "recovery")
        self.assertEqual(role["action"], "recovery")
        self.assertEqual(profile["recoveryRuleIds"], ["RECOVERY_LEVEL_001"])
        self.assertTrue(profile["requiresRecovery"])

        source = self.covered_recovery_source(requirements)
        manifest = BRIDGE.ea_factory_coverage_manifest(
            requirements,
            source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertTrue(manifest["complete"], manifest)

        no_recovery_action = source.replace(
            "OrderSend(Symbol(), OP_BUY, fixed_lot * 2.0, Ask, 3, 0, 0);",
            "bool recoveryWasObserved = true;",
        )
        rejected = BRIDGE.ea_factory_coverage_manifest(
            requirements,
            no_recovery_action,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(no_recovery_action.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(rejected["complete"])
        self.assertIn(
            "RECOVERY_LEVEL_001",
            rejected["semanticMissing"]["ruleIds"],
        )

        no_recovery_exit = source.replace(
            "  if (RecoveryExitSignal())\n"
            "    OrderClose(OrderTicket(), OrderLots(), Bid, 3);\n",
            "",
            1,
        )
        exit_rejected = BRIDGE.ea_factory_coverage_manifest(
            requirements,
            no_recovery_exit,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(no_recovery_exit.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(exit_rejected["complete"])
        self.assertTrue(
            set(self.semantic_binding_ids(requirements, "recovery_safety")).intersection(
                exit_rejected["semanticMissing"]["semanticDigests"]
            ),
            exit_rejected,
        )

        safety_mutations = {
            "direction": lambda value: value["recovery"].update(direction="opposite"),
            "spacing": lambda value: value["recovery"]["spacing"].update(value=30.0),
            "max-levels": lambda value: value["recovery"].update(maxLevels=4),
            "lot-formula": lambda value: value["recovery"]["lotFormula"].update(
                multiplier=1.5
            ),
            "lot-cap": lambda value: value["recovery"].update(lotCap=0.35),
            "basket-take-profit": lambda value: value["recovery"][
                "basketTakeProfit"
            ].update(value=11.0),
            "basket-stop-loss": lambda value: value["recovery"][
                "basketStopLoss"
            ].update(value=55.0),
            "equity-stop": lambda value: value["recovery"].update(
                equityStopPercent=15.0
            ),
            "basket-lot-cap": lambda value: value["recovery"].update(
                maxBasketLots=1.2
            ),
            "drawdown-cap": lambda value: value["recovery"].update(
                maxDrawdownPercent=25.0
            ),
            "reset-condition": lambda value: value["recovery"][
                "resetCondition"
            ]["right"].update(value=1),
            "abort-condition": lambda value: value["recovery"][
                "abortCondition"
            ]["right"].update(value=25.0),
            "reentry-policy": lambda value: value["recovery"][
                "reentryPolicy"
            ].update(sameSignalRequired=False),
        }
        for label, mutate in safety_mutations.items():
            with self.subTest(recovery_safety=label):
                changed = copy.deepcopy(normalized)
                mutate(changed)
                _changed, _changed_digest, changed_requirements = self.requirements_for(
                    changed
                )
                refreshed = self.refresh_only_top_digest_marker(
                    source,
                    requirements,
                    changed_requirements,
                )
                stale = BRIDGE.ea_factory_coverage_manifest(
                    changed_requirements,
                    refreshed,
                    strategy_spec_digest="b" * 64,
                    source_digest=hashlib.sha256(refreshed.encode("utf-8")).hexdigest(),
                    target_platform="mt4",
                )
                self.assertEqual(stale["missing"]["blueprintDigests"], [])
                self.assertTrue(
                    set(
                        self.semantic_binding_ids(
                            changed_requirements,
                            "recovery_safety",
                        )
                    ).intersection(stale["semanticMissing"]["semanticDigests"]),
                    stale,
                )
                self.assertFalse(stale["complete"])

        hedging = copy.deepcopy(normalized)
        hedging["recovery"].update(mode="hedging", direction="opposite")
        hedging["recovery"]["hedgeLifecycle"] = {
            "openTrigger": copy.deepcopy(hedging["recovery"]["trigger"]),
            "closeTrigger": copy.deepcopy(hedging["recovery"]["resetCondition"]),
            "maxConcurrentHedges": 1,
            "closeOrder": "hedge_first",
            "lotFormula": copy.deepcopy(hedging["recovery"]["lotFormula"]),
            "sourceStatus": "verified_fact",
            "sourceRefs": ["S1"],
        }
        hedging_normalized, _hedging_digest, hedging_requirements = (
            self.requirements_for(hedging)
        )
        hedging_source = self.covered_recovery_source(hedging_requirements)
        hedging_manifest = BRIDGE.ea_factory_coverage_manifest(
            hedging_requirements,
            hedging_source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(hedging_source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertTrue(hedging_manifest["complete"], hedging_manifest)
        for label, mutate in {
            "hedge-cap": lambda value: value["recovery"]["hedgeLifecycle"].update(
                maxConcurrentHedges=2
            ),
            "hedge-close-order": lambda value: value["recovery"][
                "hedgeLifecycle"
            ].update(closeOrder="original_first"),
        }.items():
            with self.subTest(recovery_safety=label):
                changed = copy.deepcopy(hedging_normalized)
                mutate(changed)
                _changed, _changed_digest, changed_requirements = self.requirements_for(
                    changed
                )
                refreshed = self.refresh_only_top_digest_marker(
                    hedging_source,
                    hedging_requirements,
                    changed_requirements,
                )
                stale = BRIDGE.ea_factory_coverage_manifest(
                    changed_requirements,
                    refreshed,
                    strategy_spec_digest="b" * 64,
                    source_digest=hashlib.sha256(refreshed.encode("utf-8")).hexdigest(),
                    target_platform="mt4",
                )
                self.assertEqual(stale["missing"]["blueprintDigests"], [])
                self.assertTrue(
                    set(
                        self.semantic_binding_ids(
                            changed_requirements,
                            "recovery_safety",
                        )
                    ).intersection(stale["semanticMissing"]["semanticDigests"]),
                    stale,
                )
                self.assertFalse(stale["complete"])

    def test_pending_rule_requires_pending_order_submission_not_market_entry(self) -> None:
        blueprint = copy.deepcopy(self.blueprint)
        pending_rule = {
            "ruleId": "PENDING_PLACE_001",
            "phase": "modify",
            "side": "buy",
            "enabled": True,
            "sourceStatus": "verified_fact",
            "sourceRefs": ["S1"],
            "expression": {"op": ">", "left": 2, "right": 1},
            "humanTextTh": "วาง Buy Limit เมื่อเงื่อนไขที่ยืนยันแล้วเป็นจริง",
        }
        blueprint["orderManagement"]["pendingOrders"].update(
            enabled=True,
            trigger=copy.deepcopy(pending_rule["expression"]),
            action={"kind": "place_pending"},
            parameters={
                "orderType": "limit",
                "entryPrice": {
                    "method": "offset_pips",
                    "reference": "ask",
                    "direction": "below",
                    "value": 10.0,
                },
                "expiry": {"mode": "gtc"},
            },
            rules=[pending_rule],
        )
        digest = hashlib.sha256(
            json.dumps(
                blueprint,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        requirements = BRIDGE.ea_factory_coverage_requirements(blueprint, digest)
        profile = requirements["semanticProfile"]
        role = next(
            row
            for row in profile["ruleRoles"]
            if row["id"] == "PENDING_PLACE_001"
        )
        self.assertEqual(role["phase"], "modify")
        self.assertEqual(role["action"], "pending")
        self.assertEqual(profile["pendingRuleIds"], ["PENDING_PLACE_001"])
        self.assertTrue(profile["requiresPendingOrder"])

        marker = next(
            row["marker"]
            for row in requirements["requiredMarkers"]["ruleIds"]
            if row["id"] == "PENDING_PLACE_001"
        )
        pending_feature_marker = self.semantic_markers(
            requirements,
            "management_feature",
            "pendingOrders",
        )[0]
        helper = (
            "bool PendingSignal() {\n"
            f"  return {marker} && {pending_feature_marker} && "
            "OrdersTotal() == 0 && FastValue(1) > SlowValue(1);\n"
            "}\n"
        )
        source = helper + self.covered_source(requirements).replace(
            "void OnTick() {\n",
            (
                "void OnTick() {\n"
                "  if (PendingSignal())\n"
                "    OrderSend(Symbol(), OP_BUYLIMIT, fixed_lot, Bid-10*Point, 3, 0, 0);\n"
            ),
        )
        manifest = BRIDGE.ea_factory_coverage_manifest(
            requirements,
            source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertTrue(manifest["complete"], manifest)

        self.assertTrue(manifest["capabilityEvidence"]["pendingOrder"])

        market_only = source.replace("OP_BUYLIMIT", "OP_BUY")
        rejected = BRIDGE.ea_factory_coverage_manifest(
            requirements,
            market_only,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(market_only.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(rejected["complete"])
        self.assertIn("REACHABLE_PENDING_ORDER_MISSING", rejected["capabilityMissing"])
        self.assertIn("PENDING_PLACE_001", rejected["semanticMissing"]["ruleIds"])

    def test_pending_state_transition_alone_requires_pending_order_path(self) -> None:
        blueprint = copy.deepcopy(self.blueprint)
        blueprint["stateMachine"][0]["transitions"][0]["to"] = "PENDING"
        blueprint["stateMachine"].append(
            {
                "state": "PENDING",
                "transitions": [
                    {"to": "LONG", "whenRuleIds": ["ENTRY_BUY_001"]}
                ],
            }
        )
        digest = hashlib.sha256(
            json.dumps(
                blueprint,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        requirements = BRIDGE.ea_factory_coverage_requirements(blueprint, digest)
        self.assertTrue(requirements["semanticProfile"]["requiresPendingOrder"])
        pending_state_marker = next(
            row["marker"]
            for row in requirements["requiredMarkers"]["stateIds"]
            if row["id"] == "PENDING"
        )
        source = self.covered_source(requirements).replace(
            "&& OrdersTotal() == 0 && EntrySignal())",
            f"&& {pending_state_marker} && OrdersTotal() == 0 && EntrySignal())",
        )
        manifest = BRIDGE.ea_factory_coverage_manifest(
            requirements,
            source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(manifest["complete"])
        self.assertEqual(
            requirements["semanticProfile"]["pendingStateIds"],
            ["FLAT", "PENDING"],
        )
        self.assertEqual(
            manifest["semanticMissing"]["stateIds"],
            ["FLAT", "PENDING"],
        )
        self.assertIn("REACHABLE_PENDING_ORDER_MISSING", manifest["capabilityMissing"])

    def test_non_market_entry_rule_is_bound_to_pending_order_action(self) -> None:
        blueprint = copy.deepcopy(self.blueprint)
        blueprint["entry"]["buy"]["orderType"] = "limit"
        blueprint["execution"]["entryOrderType"] = "limit"
        digest = hashlib.sha256(
            json.dumps(
                blueprint,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        requirements = BRIDGE.ea_factory_coverage_requirements(blueprint, digest)
        role = next(
            row
            for row in requirements["semanticProfile"]["ruleRoles"]
            if row["id"] == "ENTRY_BUY_001"
        )
        self.assertEqual(role["action"], "pending")
        self.assertTrue(requirements["semanticProfile"]["requiresEntry"])
        self.assertTrue(requirements["semanticProfile"]["requiresPendingOrder"])
        market_source = self.covered_source(requirements)
        manifest = BRIDGE.ea_factory_coverage_manifest(
            requirements,
            market_source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(market_source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(manifest["complete"])
        self.assertIn("ENTRY_BUY_001", manifest["semanticMissing"]["ruleIds"])
        self.assertIn("REACHABLE_PENDING_ORDER_MISSING", manifest["capabilityMissing"])

    def test_enabled_management_feature_requires_reachable_modify_path(self) -> None:
        blueprint = copy.deepcopy(self.blueprint)
        blueprint["orderManagement"]["breakEven"].update(enabled=True)
        digest = hashlib.sha256(
            json.dumps(
                blueprint,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        requirements = BRIDGE.ea_factory_coverage_requirements(blueprint, digest)
        profile = requirements["semanticProfile"]
        self.assertEqual(profile["enabledManagementFeatures"], ["breakEven"])
        self.assertTrue(profile["requiresManagement"])
        source = self.covered_source(requirements)
        manifest = BRIDGE.ea_factory_coverage_manifest(
            requirements,
            source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(manifest["complete"])
        self.assertIn(
            "REACHABLE_TRADE_MANAGEMENT_MISSING",
            manifest["capabilityMissing"],
        )

    def test_management_action_and_parameters_have_action_bound_subtree_digest(self) -> None:
        blueprint = copy.deepcopy(self.blueprint)
        trigger = BLUEPRINT_TEST.once_per_bar_with_position()
        rule = {
            "ruleId": "SCALE_OUT_001",
            "phase": "modify",
            "side": "buy",
            "enabled": True,
            "evaluationEvent": "new_closed_bar",
            "sourceStatus": "verified_fact",
            "sourceRefs": ["S1"],
            "expression": copy.deepcopy(trigger),
            "humanTextTh": "ปิดบางส่วนหนึ่งครั้งต่อแท่งปิด",
        }
        blueprint["orderManagement"]["scaleOut"].update(
            enabled=True,
            trigger=copy.deepcopy(trigger),
            action={"kind": "close_partial"},
            parameters={"closePercent": 50},
            rules=[rule],
            cadence="new_closed_bar",
            idempotent=True,
            precedence=40,
        )
        blueprint["testCases"].append(
            {
                "caseId": "scale-out-lifecycle",
                "kind": "lifecycle",
                "ruleIds": ["SCALE_OUT_001"],
                "given": {"position": "long", "lots": 0.1},
                "when": "a new closed bar is processed",
                "expected": {"lots": 0.05},
            }
        )
        blueprint["pseudocode"]["lines"].append(
            "When SCALE_OUT_001 is true, close 50 percent of the managed position once."
        )
        normalized, _digest, requirements = self.requirements_for(blueprint)
        rule_marker = next(
            row["marker"]
            for row in requirements["requiredMarkers"]["ruleIds"]
            if row["id"] == "SCALE_OUT_001"
        )
        feature_marker = self.semantic_markers(
            requirements,
            "management_feature",
            "scaleOut",
        )[0]
        helper = (
            "bool ScaleOutSignal() {\n"
            f"  return {rule_marker} && {feature_marker} && OrdersTotal() > 0;\n"
            "}\n"
        )
        source = self.covered_mt5_source(requirements).replace(
            "CTrade trade;\n",
            "CTrade trade;\n" + helper,
            1,
        ).replace(
            "void OnTick() {\n",
            (
                "void OnTick() {\n"
                "  if (ScaleOutSignal())\n"
                "    trade.PositionClosePartial(Symbol(), fixed_lot / 2.0);\n"
            ),
            1,
        )
        manifest = BRIDGE.ea_factory_coverage_manifest(
            requirements,
            source,
            strategy_spec_digest="b" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="mt5",
        )
        self.assertTrue(manifest["complete"], manifest)

        for label, replacement in {
            "modify-instead-of-partial": (
                "trade.PositionModify(Symbol(), Bid - 10 * _Point, 0);"
            ),
            "full-close-instead-of-partial": "trade.PositionClose(Symbol());",
        }.items():
            with self.subTest(wrong_management_action=label):
                wrong_action_source = source.replace(
                    "trade.PositionClosePartial(Symbol(), fixed_lot / 2.0);",
                    replacement,
                    1,
                )
                self.assertNotEqual(wrong_action_source, source)
                wrong_action_manifest = BRIDGE.ea_factory_coverage_manifest(
                    requirements,
                    wrong_action_source,
                    strategy_spec_digest="b" * 64,
                    source_digest=hashlib.sha256(
                        wrong_action_source.encode("utf-8")
                    ).hexdigest(),
                    target_platform="mt5",
                )
                self.assertFalse(wrong_action_manifest["complete"])
                self.assertTrue(
                    set(
                        self.semantic_binding_ids(
                            requirements,
                            "management_feature",
                        )
                    ).intersection(
                        wrong_action_manifest["semanticMissing"]["semanticDigests"]
                    ),
                    wrong_action_manifest,
                )

        mutations = {
            "parameters": lambda value: value["orderManagement"]["scaleOut"][
                "parameters"
            ].update(closePercent=40),
            "action": lambda value: value["orderManagement"]["scaleOut"][
                "action"
            ].update(kind="close_position"),
        }
        for label, mutate in mutations.items():
            with self.subTest(management_semantic=label):
                changed = copy.deepcopy(normalized)
                mutate(changed)
                _changed, _changed_digest, changed_requirements = self.requirements_for(
                    changed
                )
                refreshed = self.refresh_only_top_digest_marker(
                    source,
                    requirements,
                    changed_requirements,
                )
                stale = BRIDGE.ea_factory_coverage_manifest(
                    changed_requirements,
                    refreshed,
                    strategy_spec_digest="b" * 64,
                    source_digest=hashlib.sha256(refreshed.encode("utf-8")).hexdigest(),
                    target_platform="mt5",
                )
                self.assertEqual(stale["missing"]["blueprintDigests"], [])
                self.assertTrue(
                    set(
                        self.semantic_binding_ids(
                            changed_requirements,
                            "management_feature",
                        )
                    ).intersection(stale["semanticMissing"]["semanticDigests"]),
                    stale,
                )
                self.assertFalse(stale["complete"])

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
