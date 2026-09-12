from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = PROJECT_ROOT / "runner" / "codex_cli_runner.py"
BLUEPRINT_FIXTURE_PATH = PROJECT_ROOT / "tests" / "test_ea_research_blueprint_v2.py"


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "ea_factory_scoped_runner_under_test", RUNNER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_ready_blueprint() -> dict:
    spec = importlib.util.spec_from_file_location(
        "ea_factory_runner_ready_blueprint_fixture",
        BLUEPRINT_FIXTURE_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ready_blueprint()


class EaFactoryRunnerSandboxTests(unittest.TestCase):
    COMPACT_BRIEF = {
        "schemaVersion": "ea-strategy-brief/1.0.0",
        "systemName": "Runner compact contract smoke test",
        "systemOverview": "EMA cross Expert Advisor for MT4 or MT5.",
        "entryRules": (
            "Buy when the fast EMA crosses above the slow EMA on confirmed closed "
            "bars [2] and [1]; sell on the inverse cross."
        ),
        "recoveryRules": (
            "No automatic recovery, grid, martingale, averaging, or hedging."
        ),
        "exitRules": (
            "Close on the opposite signal and protect every trade with stop loss, "
            "take profit, and trailing stop."
        ),
        "moneyManagement": "Use fixed lot sizing and reject a non-positive lot.",
        "orderExecution": "Send market buy or sell orders after the confirmed closed bar.",
        "displayRequirements": "Display system state, balance, equity, and spread.",
        "additionalNotes": "EMA periods and protection distances are inputs.",
        "sourceLinks": [
            "https://www.metatrader4.com/en/trading-platform/help",
            "https://www.mql5.com/en/docs",
        ],
        "checkedAt": "2026-09-10T09:00:00+07:00",
        "limitations": ["Source-only test fixture; no performance claim."],
    }
    SOURCE_CONTENT = ""

    @staticmethod
    def _compact_ea_source(brief_digest: str) -> str:
        return f"""#property strict
#property description \"EA_STRATEGY_BRIEF_SHA256:{brief_digest}\"
#define SIGNAL_NONE -1
input double FixedLot = 0.10;
int OnInit() {{ return(INIT_SUCCEEDED); }}
void OnTick() {{
  static datetime lastBar = 0;
  datetime currentBar = iTime(Symbol(), Period(), 0);
  if(currentBar <= 0 || currentBar == lastBar) return;
  lastBar = currentBar;
  double fast2 = iMA(Symbol(), Period(), 10, 0, MODE_EMA, PRICE_CLOSE, 2);
  double slow2 = iMA(Symbol(), Period(), 60, 0, MODE_EMA, PRICE_CLOSE, 2);
  double fast1 = iMA(Symbol(), Period(), 10, 0, MODE_EMA, PRICE_CLOSE, 1);
  double slow1 = iMA(Symbol(), Period(), 60, 0, MODE_EMA, PRICE_CLOSE, 1);
  int signal = SIGNAL_NONE;
  if(fast2 <= slow2 && fast1 > slow1) signal = 0;
  if(fast2 >= slow2 && fast1 < slow1) signal = 1;
  if(FixedLot <= 0) return;
  double sl = 30 * Point;
  double tp = 60 * Point;
  double trailingStopDistance = 30 * Point;
  if(OrdersTotal() > 0 && signal != SIGNAL_NONE) {{
    OrderClose(OrderTicket(), OrderLots(), Bid, 3);
  }}
  if(OrdersTotal() == 0 && signal == 0) {{
    OrderSend(Symbol(), OP_BUY, FixedLot, Ask, 3, Ask-sl, Ask+tp);
  }}
  if(OrdersTotal() == 0 && signal == 1) {{
    OrderSend(Symbol(), OP_SELL, FixedLot, Bid, 3, Bid+sl, Bid-tp);
  }}
  if(OrdersTotal() > 0) {{
    OrderModify(OrderTicket(), OrderOpenPrice(), Bid-trailingStopDistance, Bid+tp, 0);
  }}
  Comment(\"Runner compact EA\", AccountBalance(), AccountEquity(), MarketInfo(Symbol(), MODE_SPREAD));
}}
"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()
        cls.STRATEGY_BRIEF = cls.runner.normalize_strategy_brief(
            cls.COMPACT_BRIEF
        )
        cls.STRATEGY_BRIEF_DIGEST = cls.runner.compute_strategy_brief_digest(
            cls.STRATEGY_BRIEF
        )
        cls.SOURCE_CONTENT = cls._compact_ea_source(cls.STRATEGY_BRIEF_DIGEST)

    @classmethod
    def _can_slim_legacy_brief(cls) -> dict:
        brief = dict(cls.STRATEGY_BRIEF)
        brief.update({
            "systemName": "CAN SLIM",
            "entryRules": (
                "Buy/Long เมื่อเงื่อนไข C-A-N-S-L-I, EPS earnings growth และ "
                "institutional sponsorship "
                "ผ่านเกณฑ์ข้อมูลภายนอก พร้อม Close[1] ทะลุ breakout level และ "
                "market filter เป็นขาขึ้น โดยใช้แท่งปิด [2] และ [1]. Sell/Short "
                "entry ไม่มีในแหล่งข้อมูลและไม่ควรเปิด Sell/Short เป็น entry ใหม่."
            ),
            "recoveryRules": (
                "[IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT]"
                "[POLICY=compact-ea-atr-risk-v1][COMPONENT=recoveryRules] "
                "RecoveryMode=none, ไม่เพิ่มไม้แก้ ไม่ถัวเฉลี่ย ไม่ Martingale, "
                "Grid หรือ Hedging"
            ),
            "exitRules": (
                "ตัดขาดทุนทุกสถานะ Long ไม่เกิน 7%-8% ต่ำกว่าจุดซื้อเป็น Stop Loss; "
                "ปิด Long เมื่อ market direction เป็นขาลง. "
                "[IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT]"
                "[POLICY=compact-ea-atr-risk-v1][COMPONENT=exitRules] "
                "Take Profit ใช้ RewardRiskRatio=2.0 จากระยะ Stop Loss จริง. "
                "TrailingStop=false, BreakEven=false, PartialClose=false"
            ),
            "moneyManagement": (
                "[IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT]"
                "[POLICY=compact-ea-atr-risk-v1][COMPONENT=moneyManagement] "
                "percent-equity sizing RiskPercent=1.0 จากระยะ SL จริง; ใช้ "
                "TickSize/TickValue, round down ตาม VolumeStep, ตรวจ margin และ "
                "ตั้ง MaxOpenPositionsPerSymbolMagic=1"
            ),
            "orderExecution": (
                "[IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT]"
                "[POLICY=compact-ea-atr-risk-v1][COMPONENT=orderExecution] "
                "ใช้ Market order สำหรับ Buy/Long บน first tick ของแท่งใหม่จาก "
                "closed bar [1], ไม่ใช้ bar 0, ไม่สร้าง pending order และไม่เปิด "
                "Sell/Short entry; ตรวจ spread และ broker stop floor"
            ),
            "displayRequirements": (
                "ใช้ Comment แสดง SystemName, SignalState, Balance, Equity, Spread, "
                "Symbol, Timeframe, MarketDirection, BreakoutLevel, "
                "StopLossPercent, RiskPercent และ RecoveryMode=none"
            ),
        })
        return cls.runner.normalize_strategy_brief(brief)

    def _runner_patches(self, root: Path, fake_chat):
        workspace = root / "workspace"
        return (
            mock.patch.object(self.runner, "PROJECT_ROOT", root),
            mock.patch.object(self.runner, "AUTO_WORKSPACE_ROOT", workspace),
            mock.patch.object(
                self.runner,
                "AUTO_ADDITIONAL_WRITE_ROOTS",
                (root / "frontend", root / "docs", root / "assets-source"),
            ),
            mock.patch.object(
                self.runner,
                "AUTO_WRITE_ROOT_LABELS",
                ("workspace", "frontend", "docs", "assets-source"),
            ),
            mock.patch.object(self.runner, "CODEX_RUNS_DIR", root / "runs"),
            mock.patch.object(self.runner, "CODEX_BIN", root / "codex.exe"),
            mock.patch.object(
                self.runner,
                "chat_status",
                return_value={"ok": True, "status": "ready"},
            ),
            mock.patch.object(
                self.runner,
                "run_chat_command",
                side_effect=fake_chat,
            ),
        )

    def _factory_fixture(
        self,
        root: Path,
        *,
        build_id: str = "ea-build-1234567890-abc123",
        platform: str = "mt4",
        strategy_brief: dict | None = None,
    ) -> tuple[str, Path, str, str, str]:
        relative = f"ea-factory/{build_id}/Source"
        source = root / "workspace" / Path(relative)
        source.mkdir(parents=True)
        source_record_digest = "a" * 64
        bound_strategy_brief = strategy_brief or self.STRATEGY_BRIEF
        bound_strategy_brief_digest = self.runner.compute_strategy_brief_digest(
            bound_strategy_brief
        )
        spec = {
            "schemaVersion": "ea-factory-strategy-spec-v3",
            "strategySchemaVersion": self.runner.EA_STRATEGY_BRIEF_SCHEMA_VERSION,
            "buildId": build_id,
            "sourceRecordId": "ea-source-runner-smoke",
            "recordDigest": source_record_digest,
            "artifactKind": "expert_advisor",
            "targetPlatform": platform,
            "strategyBrief": bound_strategy_brief,
            "strategyBriefDigest": bound_strategy_brief_digest,
            "immutable": True,
        }
        spec_bytes = json.dumps(
            spec,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        (source / "strategy-spec-v01.json").write_bytes(spec_bytes)
        spec_digest = hashlib.sha256(spec_bytes).hexdigest()
        prompt = (
            f"[EA_FACTORY_BUILD_ID:{build_id}]"
            f"[EA_FACTORY_SOURCE_RECORD_DIGEST:{source_record_digest}]"
            f"[EA_FACTORY_STRATEGY_SPEC_DIGEST:{spec_digest}]"
            f"[EA_FACTORY_PLATFORM:{platform}] "
            f"Read ea-factory/{build_id}/Source/strategy-spec-v01.json and generate source."
        )
        return relative, source, prompt, source_record_digest, spec_digest

    def _patch_roots(self, root: Path):
        return (
            mock.patch.object(self.runner, "PROJECT_ROOT", root),
            mock.patch.object(
                self.runner, "AUTO_WORKSPACE_ROOT", root / "workspace"
            ),
        )

    def _indicator_factory_fixture(
        self,
        root: Path,
        *,
        build_id: str,
    ) -> tuple[str, Path, str, dict]:
        relative = f"ea-factory/{build_id}/Source"
        source = root / "workspace" / Path(relative)
        source.mkdir(parents=True)
        source_record_digest = "a" * 64
        strategy_spec = {
            "schemaVersion": "ea-factory-strategy-spec-v3",
            "strategySchemaVersion": self.runner.EA_STRATEGY_BRIEF_SCHEMA_VERSION,
            "buildId": build_id,
            "sourceRecordId": "ea-source-indicator-compact",
            "recordDigest": source_record_digest,
            "artifactKind": "custom_indicator",
            "targetPlatform": "mt4",
            "immutable": True,
            "strategyBrief": self.STRATEGY_BRIEF,
            "strategyBriefDigest": self.STRATEGY_BRIEF_DIGEST,
        }
        spec_bytes = json.dumps(
            strategy_spec,
            ensure_ascii=False,
            indent=2,
        ).encode("utf-8")
        (source / "strategy-spec-v01.json").write_bytes(spec_bytes)
        spec_digest = hashlib.sha256(spec_bytes).hexdigest()
        prompt = (
            f"[EA_FACTORY_BUILD_ID:{build_id}]"
            f"[EA_FACTORY_SOURCE_RECORD_DIGEST:{source_record_digest}]"
            f"[EA_FACTORY_STRATEGY_SPEC_DIGEST:{spec_digest}]"
            "[EA_FACTORY_PLATFORM:mt4]"
            "[EA_FACTORY_ARTIFACT_KIND:custom_indicator] "
            f"Read ea-factory/{build_id}/Source/strategy-spec-v01.json and generate source."
        )
        return relative, source, prompt, self.STRATEGY_BRIEF_DIGEST

    @staticmethod
    def _exact_indicator_source(brief_digest: str) -> str:
        return f"""
#property strict
#property description \"EA_STRATEGY_BRIEF_SHA256:{brief_digest}\"
#property indicator_chart_window
#property indicator_buffers 1
#property indicator_type1 DRAW_ARROW
double SignalBuffer[];
double FastValue(int shift) {{
  return iMA(Symbol(), Period(), 10, 0, MODE_EMA, PRICE_CLOSE, shift);
}}
double SlowValue(int shift) {{
  return iMA(Symbol(), Period(), 60, 0, MODE_EMA, PRICE_CLOSE, shift);
}}
int OnInit() {{
  SetIndexBuffer(0, SignalBuffer);
  SetIndexStyle(0, DRAW_ARROW);
  return(INIT_SUCCEEDED);
}}
int OnCalculate(const int rates_total, const int prev_calculated,
                const datetime &time[], const double &open[],
                const double &high[], const double &low[],
                const double &close[], const long &tick_volume[],
                const long &volume[], const int &spread[]) {{
  if(rates_total < 3) return(0);
  SignalBuffer[1] = EMPTY_VALUE;
  bool entrySignal = FastValue(2) <= SlowValue(2)
                     && FastValue(1) > SlowValue(1);
  if(entrySignal) SignalBuffer[1] = low[1];
  bool exitSignal = FastValue(2) >= SlowValue(2)
                    && FastValue(1) < SlowValue(1);
  if(exitSignal) SignalBuffer[1] = high[1];
  return(rates_total);
}}
"""

    def test_structured_generation_keeps_codex_read_only_and_runner_writes(self) -> None:
        captured: dict[str, object] = {}

        def fake_chat(command, **kwargs):
            captured["command"] = [str(item) for item in command]
            captured["cwd"] = Path(kwargs["cwd"])
            captured["prompt"] = str(kwargs.get("stdin") or "")
            raw_final_path = Path(command[command.index("-o") + 1])
            raw_payload = json.dumps({
                "fileName": "SmokeFactoryEA.mq4",
                "content": self.SOURCE_CONTENT,
            })
            raw_final_path.write_text(raw_payload, encoding="utf-8")
            return {
                "ok": True,
                "exitCode": 0,
                "durationMs": 1,
                "processStarted": True,
                "processTreeTerminated": False,
                "stdout": raw_payload,
                "stderr": "",
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source, prompt, _record_digest, _spec_digest = (
                self._factory_fixture(root)
            )
            for extra in ("frontend", "docs", "assets-source"):
                (root / extra).mkdir()
            (root / "codex.exe").write_bytes(b"")
            patches = self._runner_patches(root, fake_chat)
            with (
                patches[0], patches[1], patches[2], patches[3],
                patches[4], patches[5], patches[6], patches[7],
            ):
                result = self.runner.run_codex(
                    prompt,
                    "ea_developer",
                    "mission-ea-factory-structured",
                    execution_mode="auto_guarded",
                    read_only_work=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )
                source_bytes = (source / "SmokeFactoryEA.mq4").read_bytes()
                stdout_artifact = (
                    root / result["artifacts"]["stdout"]
                ).read_text(encoding="utf-8")

        command = captured["command"]
        self.assertEqual(captured["cwd"], source)
        self.assertEqual(command[command.index("--cd") + 1], str(source))
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
        self.assertNotIn("--add-dir", command)
        self.assertTrue(result["ok"])
        self.assertEqual(result["requestedSandbox"], "read-only")
        self.assertEqual(result["sandbox"], "read-only")
        self.assertEqual(result["workingDirectory"], f"workspace/{relative}")
        self.assertEqual(result["writeRoots"], [])
        self.assertFalse(result["controlPlaneWritable"])
        self.assertFalse(result["projectCodeWritable"])
        self.assertEqual(source_bytes, self.SOURCE_CONTENT.encode("utf-8"))
        self.assertEqual(
            result["eaFactorySourceWriterVersion"],
            "ea-factory-structured-source-v2",
        )
        serialized_result = json.dumps(result, ensure_ascii=False)
        self.assertNotIn(self.SOURCE_CONTENT, serialized_result)
        self.assertNotIn(self.SOURCE_CONTENT, stdout_artifact)
        prompt_text = captured["prompt"]
        self.assertIn("Codex itself is running in a read-only OS sandbox", prompt_text)
        self.assertIn("containing only fileName and content", prompt_text)
        self.assertNotIn("only writable root", prompt_text)

    def test_source_prompt_requires_complete_optimization_ready_a_to_j_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source, prompt, _record_digest, _spec_digest = (
                self._factory_fixture(root)
            )
            patches = self._patch_roots(root)
            with patches[0], patches[1]:
                wrapped = self.runner.build_prompt(
                    prompt,
                    "ea_developer",
                    "mission-ea-factory-prompt-contract",
                    "specialist_fast",
                    7000,
                    execution_mode="auto_guarded",
                    read_only_work=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=source,
                )

        required_fragments = (
            "Strategy Brief A-J field as immutable behavior",
            "PositionSizingMode",
            "FIXED_LOT=0",
            "RISK_PERCENT_EQUITY=1",
            "FixedLot=0.01",
            "RiskPercent=1.0",
            "StopLossPoints=300",
            "TakeProfitPoints=600",
            "MaxOpenPositionsPerSymbolMagic=1",
            "SignalBarShift=1",
            "TradeOnNewBar=true",
            "RecoveryMode=RECOVERY_NONE",
            "single-line `input bool|int|double Name = literal;`",
            "at most\n  64 total inputs",
            "Fundamental, External, Eligibility, Screen, or Criteria",
            "if(!ExternalEligibilityConfirmed) return;",
            "confirmed shifts [2] and [1]",
            "OrderSymbol()==Symbol()",
            "OrderMagicNumber()==MagicNumber",
            "AccountEquity() * RiskPercent / 100.0",
            "MODE_TICKSIZE",
            "MODE_TICKVALUE",
            "MODE_LOTSTEP",
            "MODE_MINLOT",
            "MathFloor",
            "AccountFreeMarginCheck",
            "lot<=0",
            "Comment/ObjectCreate/ChartSetString",
            "no external code directive",
            "WebRequest/Socket APIs",
            "File/Folder/Database/Resource APIs",
            "TerminalClose/ExpertRemove",
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, wrapped)

    def test_source_preflight_rejects_host_side_effect_before_materialization(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source_root, prompt, _record_digest, _spec_digest = (
                self._factory_fixture(root)
            )
            unsafe_source = self.SOURCE_CONTENT.replace(
                "void OnTick() {",
                'void OnTick() {\n  FileDelete("outside.txt");\n  TerminalClose(0);',
                1,
            )
            raw = json.dumps({
                "fileName": "UnsafeHostSideEffect.mq4",
                "content": unsafe_source,
            })
            patches = self._patch_roots(root)
            with patches[0], patches[1]:
                with self.assertRaises(
                    self.runner.EAFactorySourceSemanticValidationError
                ) as raised:
                    self.runner.preflight_ea_factory_source_semantics(
                        raw,
                        prompt,
                        relative,
                    )

            self.assertIn("ea_host_io_forbidden", raised.exception.findings)
            self.assertIn("ea_terminal_control_forbidden", raised.exception.findings)
            self.assertEqual(
                {item.name for item in source_root.iterdir()},
                {"strategy-spec-v01.json"},
            )

    def test_policy_guidance_keeps_can_slim_long_only_and_pending_disabled(self) -> None:
        brief = dict(self.STRATEGY_BRIEF)
        brief["entryRules"] = (
            "Buy/Long after a confirmed closed-bar breakout. Sell/Short entry is "
            "not supported; ไม่ควรเปิด Sell/Short เป็น entry ใหม่."
        )
        brief["orderExecution"] = (
            "[IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT]"
            "[POLICY=compact-ea-atr-risk-v1][COMPONENT=orderExecution] "
            "ใช้ Market order สำหรับ Buy/Long และไม่สร้าง pending order."
        )
        brief["exitRules"] = (
            "ตัดขาดทุน Long 7%-8% ต่ำกว่าจุดซื้อเป็น Stop Loss; "
            "[IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT]"
            "[POLICY=compact-ea-atr-risk-v1][COMPONENT=exitRules] "
            "Take Profit ใช้ RewardRiskRatio=2.0 จากระยะ Stop Loss จริง."
        )
        brief["moneyManagement"] = (
            "[IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT]"
            "[POLICY=compact-ea-atr-risk-v1][COMPONENT=moneyManagement] "
            "percent-equity sizing RiskPercent=1.0 จากระยะ SL จริง"
        )

        guidance = self.runner._ea_factory_source_policy_guidance(brief)

        self.assertIn("Direction is long-only", guidance)
        self.assertIn("Market OP_BUY only", guidance)
        self.assertIn("never invent an OP_SELL/Short entry", guidance)
        self.assertIn("Pending orders are explicitly disabled", guidance)
        self.assertIn("StopLossPercent=7.5", guidance)
        self.assertIn("outside 7-8", guidance)
        self.assertIn("percent-equity only", guidance)
        self.assertIn("It is a TP multiplier, never a 2R stop", guidance)
        self.assertNotIn("Both Buy and Sell entries are explicitly present", guidance)

    def test_can_slim_repair_scaffold_is_certified_by_exact_manifest(self) -> None:
        self.assertEqual(
            self.runner.EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST,
            "6567a573402477fef5eb5fe09c29181963a168736e6dcf8facaa38d006d70275",
        )
        self.assertEqual(
            self.runner.EA_FACTORY_CAN_SLIM_CERTIFIED_SPEC_DIGEST,
            "7412b865cfde1309a29739c14e6a744afdefbbb68d512c8f7ecd94d17ee2233e",
        )
        brief = self._can_slim_legacy_brief()
        brief_digest = self.runner.compute_strategy_brief_digest(brief)
        spec_digest = "7" * 64

        # A merely similar CAN SLIM record cannot use the production fallback.
        self.assertNotEqual(
            brief_digest,
            self.runner.EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST,
        )
        self.assertEqual(
            self.runner._build_ea_factory_source_semantic_repair_scaffold(
                brief,
                strategy_brief_digest=brief_digest,
                strategy_spec_digest=spec_digest,
                target_platform="mt4",
            ),
            "",
        )
        with (
            mock.patch.object(
                self.runner,
                "EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST",
                brief_digest,
            ),
            mock.patch.object(
                self.runner,
                "EA_FACTORY_CAN_SLIM_CERTIFIED_SPEC_DIGEST",
                spec_digest,
            ),
        ):
            scaffold = self.runner._build_ea_factory_source_semantic_repair_scaffold(
                brief,
                strategy_brief_digest=brief_digest,
                strategy_spec_digest=spec_digest,
                target_platform="mt4",
            )
            mission_attested = (
                self.runner._ea_factory_can_slim_scaffold_meets_mission(scaffold)
            )

        self.assertTrue(scaffold)
        self.assertTrue(mission_attested)
        self.assertLessEqual(
            len(scaffold),
            self.runner.EA_FACTORY_SEMANTIC_REPAIR_SCAFFOLD_MAX_CHARS,
        )
        self.assertIn(f"EA_STRATEGY_BRIEF_SHA256:{brief_digest}", scaffold)
        self.assertIn("if(!FundamentalCriteriaConfirmed)", scaffold)
        self.assertIn("if(currentSpread > MaxSpreadPoints) return;", scaffold)
        self.assertIn("AccountEquity() * RiskPercent / 100.0", scaffold)
        self.assertIn("if(lastBar == 0) { lastBar = currentBar; return; }", scaffold)
        self.assertIn("worstCaseDistance = stopDistance + executionDistance", scaffold)
        self.assertIn("PERIOD_D1", scaffold)
        self.assertIn("PERIOD_W1", scaffold)
        self.assertIn("FiftyTwoWeekLookback = 52", scaffold)
        self.assertIn("ExternalBenchmarkUptrendConfirmed = false", scaffold)
        self.assertIn("NormalizePriceDownToTick", scaffold)
        self.assertIn("NormalizePriceUpToTick", scaffold)
        self.assertIn('" MarketDirection="', scaffold)
        self.assertIn('" BreakoutLevel="', scaffold)
        self.assertIn('" StopLossPercent="', scaffold)
        self.assertIn("gMarketDirection = marketDown ? \"Down\" : \"Up\";", scaffold)
        self.assertIn("gBreakoutLevel = fiftyTwoWeekHigh;", scaffold)
        self.assertNotIn(brief["entryRules"], scaffold)
        manifest = self.runner.build_compact_ea_source_manifest(
            scaffold,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest=spec_digest,
            source_digest=hashlib.sha256(scaffold.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertTrue(manifest["complete"], manifest)
        self.assertTrue(all(manifest["checks"].values()), manifest)
        mission_guard_mutations = {
            "first_attach_prime": (
                "if(lastBar == 0) { lastBar = currentBar; return; }",
                "if(lastBar == 0) lastBar = currentBar;",
            ),
            "worst_case_execution_cost": (
                "worstCaseDistance = stopDistance + executionDistance",
                "worstCaseDistance = stopDistance",
            ),
            "finite_guards": ("MathIsValidNumber", "MissingFiniteGuard"),
            "tick_normalization": (
                "NormalizePriceDownToTick",
                "MissingPriceDownNormalization",
            ),
            "weekly_filter": ("PERIOD_W1", "PERIOD_H4"),
            "external_benchmark_gate": (
                "if(!ExternalBenchmarkUptrendConfirmed) return;",
                "",
            ),
            "unsafe_on_init_inputs": (
                "if(ExecutionBufferPoints < 0 || SlippagePoints < 0 || MaxSpreadPoints < 0)",
                "if(ExecutionBufferPoints < 0 || MaxSpreadPoints < 0)",
            ),
            "bid_relative_broker_floor": (
                "protectiveStopDistance < brokerFloor",
                "protectiveStopDistance < 0",
            ),
        }
        for label, (required, replacement) in mission_guard_mutations.items():
            with self.subTest(label=label):
                mutated = scaffold.replace(required, replacement)
                self.assertNotEqual(mutated, scaffold)
                self.assertFalse(
                    self.runner._ea_factory_can_slim_scaffold_meets_mission(
                        mutated
                    )
                )

    def test_can_slim_certified_scaffold_rebinds_to_each_fresh_spec_digest(self) -> None:
        brief = self._can_slim_legacy_brief()
        brief_digest = self.runner.compute_strategy_brief_digest(brief)
        first_spec_digest = "1" * 64
        second_spec_digest = "2" * 64
        with mock.patch.object(
            self.runner,
            "EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST",
            brief_digest,
        ):
            first = self.runner._build_ea_factory_source_semantic_repair_scaffold(
                brief,
                strategy_brief_digest=brief_digest,
                strategy_spec_digest=first_spec_digest,
                target_platform="mt4",
            )
            second = self.runner._build_ea_factory_source_semantic_repair_scaffold(
                brief,
                strategy_brief_digest=brief_digest,
                strategy_spec_digest=second_spec_digest,
                target_platform="mt4",
            )

        self.assertTrue(first)
        self.assertTrue(second)
        # The source is bound to the immutable Brief.  The per-Build Spec
        # binding belongs to the signed coverage manifest, so a fresh Build
        # does not require changing executable strategy semantics.
        self.assertEqual(first, second)
        manifest_digests = []
        for source, spec_digest in (
            (first, first_spec_digest),
            (second, second_spec_digest),
        ):
            manifest = self.runner.build_compact_ea_source_manifest(
                source,
                strategy_brief=brief,
                strategy_brief_digest=brief_digest,
                strategy_spec_digest=spec_digest,
                source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
                target_platform="mt4",
            )
            self.assertTrue(manifest["complete"], manifest)
            self.assertEqual(manifest["strategySpecDigest"], spec_digest)
            manifest_digests.append(manifest["manifestDigest"])
            with mock.patch.object(
                self.runner,
                "EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST",
                brief_digest,
            ):
                self.assertTrue(
                    self.runner._ea_factory_can_slim_scaffold_meets_mission(source)
                )
        self.assertNotEqual(*manifest_digests)

    def test_certified_scaffold_is_omitted_for_mixed_policy_or_mt5(self) -> None:
        brief = self._can_slim_legacy_brief()
        brief_digest = self.runner.compute_strategy_brief_digest(brief)
        spec_digest = "8" * 64
        with (
            mock.patch.object(
                self.runner,
                "EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST",
                brief_digest,
            ),
            mock.patch.object(
                self.runner,
                "EA_FACTORY_CAN_SLIM_CERTIFIED_SPEC_DIGEST",
                spec_digest,
            ),
        ):
            self.assertEqual(
                self.runner._build_ea_factory_source_semantic_repair_scaffold(
                    brief,
                    strategy_brief_digest=brief_digest,
                    strategy_spec_digest=spec_digest,
                    target_platform="mt5",
                ),
                "",
            )
        mixed = dict(brief)
        mixed["orderExecution"] = mixed["orderExecution"].replace(
            "compact-ea-atr-risk-v1",
            "compact-ea-safe-inputs-v2",
        )
        mixed_digest = self.runner.compute_strategy_brief_digest(mixed)
        with (
            mock.patch.object(
                self.runner,
                "EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST",
                mixed_digest,
            ),
            mock.patch.object(
                self.runner,
                "EA_FACTORY_CAN_SLIM_CERTIFIED_SPEC_DIGEST",
                spec_digest,
            ),
        ):
            self.assertEqual(
                self.runner._build_ea_factory_source_semantic_repair_scaffold(
                    mixed,
                    strategy_brief_digest=mixed_digest,
                    strategy_spec_digest=spec_digest,
                    target_platform="mt4",
                ),
                "",
            )
        different_system = dict(brief)
        different_system["systemName"] = "Different long-only breakout system"
        different_digest = self.runner.compute_strategy_brief_digest(
            different_system
        )
        with (
            mock.patch.object(
                self.runner,
                "EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST",
                different_digest,
            ),
            mock.patch.object(
                self.runner,
                "EA_FACTORY_CAN_SLIM_CERTIFIED_SPEC_DIGEST",
                spec_digest,
            ),
        ):
            self.assertEqual(
                self.runner._build_ea_factory_source_semantic_repair_scaffold(
                    different_system,
                    strategy_brief_digest=different_digest,
                    strategy_spec_digest=spec_digest,
                    target_platform="mt4",
                ),
                "",
            )

    def test_exact_profile_preflight_rejects_comment_spoofed_guard_mutations(self) -> None:
        brief = self._can_slim_legacy_brief()
        brief_digest = self.runner.compute_strategy_brief_digest(brief)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source_root, prompt, _record_digest, spec_digest = (
                self._factory_fixture(root, strategy_brief=brief)
            )
            patches = self._patch_roots(root)
            with (
                patches[0],
                patches[1],
                mock.patch.object(
                    self.runner,
                    "EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST",
                    brief_digest,
                ),
                mock.patch.object(
                    self.runner,
                    "EA_FACTORY_CAN_SLIM_CERTIFIED_SPEC_DIGEST",
                    spec_digest,
                ),
            ):
                scaffold = self.runner._build_ea_factory_source_semantic_repair_scaffold(
                    brief,
                    strategy_brief_digest=brief_digest,
                    strategy_spec_digest=spec_digest,
                    target_platform="mt4",
                )
                mutations = {
                    "first_attach": (
                        "if(lastBar == 0) { lastBar = currentBar; return; }",
                        "if(lastBar == 0) lastBar = currentBar;",
                    ),
                    "worst_case_cost": (
                        "worstCaseDistance = stopDistance + executionDistance",
                        "worstCaseDistance = stopDistance",
                    ),
                    "bid_relative_stop": (
                        "protectiveStopDistance = liveBid - stopLoss",
                        "protectiveStopDistance = entryPrice - stopLoss",
                    ),
                }
                for label, (required, unsafe) in mutations.items():
                    with self.subTest(label=label):
                        candidate = scaffold.replace(required, unsafe)
                        candidate += f"\n// spoofed required fragment: {required}\n"
                        raw = json.dumps({
                            "fileName": f"CommentSpoof{label}.mq4",
                            "content": candidate,
                        })
                        with self.assertRaises(
                            self.runner.EAFactorySourceSemanticValidationError
                        ) as raised:
                            self.runner.preflight_ea_factory_source_semantics(
                                raw,
                                prompt,
                                relative,
                            )
                        self.assertIn(
                            "ea_explicit_mission_guardrails_missing",
                            raised.exception.findings,
                        )

            self.assertEqual(
                {item.name for item in source_root.iterdir()},
                {"strategy-spec-v01.json"},
            )

    def test_repair_prompt_injects_certified_scaffold_as_trusted_baseline(self) -> None:
        scaffold = self.SOURCE_CONTENT
        prompt = self.runner.build_ea_factory_source_semantic_repair_prompt(
            "ORIGINAL_TRUSTED_PROMPT",
            ["ea_closed_bar_execution_guard_missing"],
            certified_scaffold=scaffold,
        )

        self.assertIn("Validator-certified structural baseline", prompt)
        self.assertIn("same digest-bound Strategy Brief", prompt)
        self.assertIn(scaffold, prompt)
        self.assertRegex(
            prompt,
            r"\[BEGIN_TRUSTED_EA_SCAFFOLD_[0-9A-F]{24}\]",
        )
        self.assertRegex(
            prompt,
            r"\[END_TRUSTED_EA_SCAFFOLD_[0-9A-F]{24}\]",
        )

    def test_semantic_repair_recipes_cover_every_source_gate_finding(self) -> None:
        repairable_findings = {
            "ea_strategy_brief_digest_binding_missing",
            "ea_ontick_lifecycle_missing_or_ambiguous",
            "ea_tester_input_contract_unsupported",
            "ea_signal_none_sentinel_invalid",
            "ea_reachable_conditional_entry_missing",
            "ea_closed_bar_execution_guard_missing",
            "ea_exit_or_protection_path_missing",
            "ea_risk_percent_equity_path_missing",
            "ea_lot_calculation_safety_missing",
            "ea_position_cap_guard_missing",
            "ea_money_management_path_missing",
            "ea_order_execution_mode_missing",
            "ea_external_entry_gate_missing",
            "ea_entry_gate_precedes_exit_management",
            "ea_spread_guard_missing",
            "ea_explicit_mission_guardrails_missing",
            "ea_recovery_policy_mismatch",
            "ea_display_behavior_missing",
            "ea_source_lexically_ambiguous",
            "ea_execution_safety_not_proven",
            "ea_external_code_dependency_forbidden",
            "ea_network_io_forbidden",
            "ea_host_io_forbidden",
            "ea_terminal_control_forbidden",
            "ea_persistent_global_mutation_forbidden",
            "ea_external_notification_forbidden",
            "ea_modal_or_blocking_call_forbidden",
            "ea_preprocessor_indirection_forbidden",
        }
        self.assertTrue(
            repairable_findings.issubset(
                self.runner.EA_FACTORY_SOURCE_SEMANTIC_REPAIR_RECIPES
            )
        )

    def test_exact_profile_preflight_rejects_generic_complete_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, _source, prompt, _record_digest, spec_digest = (
                self._factory_fixture(root)
            )
            raw = json.dumps({
                "fileName": "GenericButComplete.mq4",
                "content": self.SOURCE_CONTENT,
            })
            patches = self._patch_roots(root)
            with (
                patches[0],
                patches[1],
                mock.patch.object(
                    self.runner,
                    "EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST",
                    self.STRATEGY_BRIEF_DIGEST,
                ),
                mock.patch.object(
                    self.runner,
                    "EA_FACTORY_CAN_SLIM_CERTIFIED_SPEC_DIGEST",
                    spec_digest,
                ),
            ):
                with self.assertRaises(
                    self.runner.EAFactorySourceSemanticValidationError
                ) as raised:
                    self.runner.preflight_ea_factory_source_semantics(
                        raw,
                        prompt,
                        relative,
                    )

        self.assertEqual(
            raised.exception.findings,
            ["ea_explicit_mission_guardrails_missing"],
        )
        self.assertEqual(
            raised.exception.validated_candidate["fileName"],
            "GenericButComplete.mq4",
        )
        self.assertEqual(raised.exception.repair_scaffold, "")

    def test_semantic_repair_prompt_omits_candidate_beyond_context_bound(self) -> None:
        marker = "OVERSIZED_CANDIDATE_MARKER"
        prompt = self.runner.build_ea_factory_source_semantic_repair_prompt(
            "ORIGINAL_TRUSTED_PROMPT",
            ["ea_display_behavior_missing"],
            validated_candidate={
                "fileName": "Oversized.mq4",
                "content": marker + "x" * (
                    self.runner.EA_FACTORY_SEMANTIC_REPAIR_SOURCE_MAX_CHARS + 1
                ),
            },
            policy_guidance="TRUSTED_POLICY_GUIDANCE",
        )

        self.assertNotIn(marker, prompt)
        self.assertIn("candidate was omitted", prompt)
        self.assertIn("TRUSTED_POLICY_GUIDANCE", prompt)

    def test_semantic_failure_gets_one_bounded_revision_before_materialization(self) -> None:
        invalid_source = self.SOURCE_CONTENT.replace(
            "  if(currentBar <= 0 || currentBar == lastBar) return;\n"
            "  lastBar = currentBar;",
            "  lastBar = currentBar;",
        )
        calls: list[dict[str, object]] = []

        def fake_chat(command, **kwargs):
            call_number = len(calls) + 1
            calls.append({
                "command": [str(item) for item in command],
                "prompt": str(kwargs.get("stdin") or ""),
            })
            raw_final_path = Path(command[command.index("-o") + 1])
            raw_payload = json.dumps({
                "fileName": (
                    "RejectedSemanticEA.mq4"
                    if call_number == 1
                    else "RepairedSemanticEA.mq4"
                ),
                "content": invalid_source if call_number == 1 else self.SOURCE_CONTENT,
            })
            raw_final_path.write_text(raw_payload, encoding="utf-8")
            return {
                "ok": True,
                "exitCode": 0,
                "durationMs": 1,
                "processStarted": True,
                "processTreeTerminated": False,
                "stdout": raw_payload,
                "stderr": "",
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source, prompt, _record_digest, _spec_digest = (
                self._factory_fixture(root)
            )
            for extra in ("frontend", "docs", "assets-source"):
                (root / extra).mkdir()
            (root / "codex.exe").write_bytes(b"")
            patches = self._runner_patches(root, fake_chat)
            with (
                patches[0], patches[1], patches[2], patches[3],
                patches[4], patches[5], patches[6], patches[7],
                mock.patch.object(
                    self.runner,
                    "require_fresh_corrective_verifier_quota",
                    return_value={"status": "ready"},
                ),
            ):
                result = self.runner.run_codex(
                    prompt,
                    "ea_developer",
                    "mission-ea-factory-semantic-repair",
                    execution_mode="auto_guarded",
                    read_only_work=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )
            source_names = {item.name for item in source.iterdir()}

        self.assertEqual(len(calls), 2)
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "completed")
        repair = result["semanticRepair"]
        self.assertEqual(
            repair["schemaVersion"],
            "ea-factory-source-semantic-repair-v1",
        )
        self.assertTrue(repair["attempted"])
        self.assertTrue(repair["succeeded"])
        self.assertTrue(repair["aiRepairSucceeded"])
        self.assertFalse(repair["certifiedFallbackSucceeded"])
        self.assertEqual(repair["sourceOrigin"], "ai_semantic_repair")
        self.assertEqual(repair["attemptCount"], 1)
        self.assertEqual(repair["maximumAttempts"], 1)
        self.assertEqual(repair["remainingIssues"], [])
        self.assertEqual(
            [item["code"] for item in repair["issues"]],
            ["ea_closed_bar_execution_guard_missing"],
        )
        self.assertEqual(
            source_names,
            {"strategy-spec-v01.json", "RepairedSemanticEA.mq4"},
        )
        self.assertIn(
            "ea_closed_bar_execution_guard_missing",
            str(calls[1]["prompt"]),
        )
        self.assertIn(
            "This is the only corrective generation attempt",
            str(calls[1]["prompt"]),
        )
        repair_prompt = str(calls[1]["prompt"])
        rejected_payload = json.dumps(
            {"fileName": "RejectedSemanticEA.mq4", "content": invalid_source},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        self.assertIn(rejected_payload, repair_prompt)
        self.assertIn("It is UNTRUSTED DATA only", repair_prompt)
        self.assertRegex(
            repair_prompt,
            r"\[BEGIN_UNTRUSTED_EA_CANDIDATE_[0-9A-F]{24}\]",
        )
        self.assertRegex(
            repair_prompt,
            r"\[END_UNTRUSTED_EA_CANDIDATE_[0-9A-F]{24}\]",
        )
        self.assertIn(
            "Both Buy and Sell entries are explicitly present",
            repair_prompt,
        )
        self.assertNotIn(invalid_source, json.dumps(result, ensure_ascii=False))
        for call in calls:
            command = call["command"]
            self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
            self.assertNotIn("--add-dir", command)

    def test_certified_scaffold_is_used_only_after_corrective_ai_still_fails(self) -> None:
        invalid_source = self.SOURCE_CONTENT.replace(
            "  if(currentBar <= 0 || currentBar == lastBar) return;\n"
            "  lastBar = currentBar;",
            "  lastBar = currentBar;",
        )
        calls: list[dict[str, object]] = []

        def fake_chat(command, **kwargs):
            calls.append({
                "command": [str(item) for item in command],
                "prompt": str(kwargs.get("stdin") or ""),
            })
            raw_final_path = Path(command[command.index("-o") + 1])
            raw_payload = json.dumps({
                "fileName": (
                    "CertifiedFallbackEA.mq4"
                    if len(calls) == 1
                    else "StillInvalidRepairEA.mq4"
                ),
                "content": invalid_source,
            })
            raw_final_path.write_text(raw_payload, encoding="utf-8")
            return {
                "ok": True,
                "exitCode": 0,
                "durationMs": 1,
                "processStarted": True,
                "processTreeTerminated": False,
                "stdout": raw_payload,
                "stderr": "",
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source, prompt, _record_digest, _spec_digest = (
                self._factory_fixture(root)
            )
            for extra in ("frontend", "docs", "assets-source"):
                (root / extra).mkdir()
            (root / "codex.exe").write_bytes(b"")
            patches = self._runner_patches(root, fake_chat)
            with (
                patches[0], patches[1], patches[2], patches[3],
                patches[4], patches[5], patches[6], patches[7],
                mock.patch.object(
                    self.runner,
                    "require_fresh_corrective_verifier_quota",
                    return_value={"status": "ready"},
                ),
                mock.patch.object(
                    self.runner,
                    "_build_ea_factory_source_semantic_repair_scaffold",
                    return_value=self.SOURCE_CONTENT,
                ),
                mock.patch.object(
                    self.runner,
                    "_ea_factory_can_slim_scaffold_meets_mission",
                    return_value=True,
                ),
            ):
                result = self.runner.run_codex(
                    prompt,
                    "ea_developer",
                    "mission-ea-factory-certified-fallback",
                    execution_mode="auto_guarded",
                    read_only_work=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )
            source_names = {item.name for item in source.iterdir()}
            written = (source / "CertifiedFallbackEA.mq4").read_text(
                encoding="utf-8"
            )

        self.assertEqual(len(calls), 2)
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["semanticRepair"]["succeeded"])
        self.assertTrue(result["semanticRepair"]["certifiedScaffoldProvided"])
        self.assertTrue(result["semanticRepair"]["certifiedScaffoldUsed"])
        self.assertFalse(result["semanticRepair"]["aiRepairSucceeded"])
        self.assertTrue(result["semanticRepair"]["certifiedFallbackSucceeded"])
        self.assertEqual(
            result["semanticRepair"]["sourceOrigin"],
            "backend_certified_fallback",
        )
        self.assertEqual(
            result["semanticRepair"]["certifiedFallbackProfileVersion"],
            self.runner.EA_FACTORY_CAN_SLIM_CERTIFIED_PROFILE_VERSION,
        )
        self.assertEqual(result["semanticRepair"]["remainingIssues"], [])
        self.assertEqual(
            [
                item["code"]
                for item in result["semanticRepair"][
                    "correctiveModelRemainingIssues"
                ]
            ],
            ["ea_closed_bar_execution_guard_missing"],
        )
        self.assertEqual(
            source_names,
            {"strategy-spec-v01.json", "CertifiedFallbackEA.mq4"},
        )
        self.assertEqual(written, self.SOURCE_CONTENT)
        self.assertIn(self.SOURCE_CONTENT, str(calls[1]["prompt"]))
        self.assertNotIn(self.SOURCE_CONTENT, json.dumps(result, ensure_ascii=False))

    def test_semantic_revision_is_never_retried_twice_or_materialized_when_invalid(self) -> None:
        invalid_source = self.SOURCE_CONTENT.replace(
            "  if(currentBar <= 0 || currentBar == lastBar) return;\n"
            "  lastBar = currentBar;",
            "  lastBar = currentBar;",
        )
        call_count = 0

        def fake_chat(command, **kwargs):
            nonlocal call_count
            call_count += 1
            raw_final_path = Path(command[command.index("-o") + 1])
            raw_payload = json.dumps({
                "fileName": f"StillInvalid{call_count}.mq4",
                "content": invalid_source,
            })
            raw_final_path.write_text(raw_payload, encoding="utf-8")
            return {
                "ok": True,
                "exitCode": 0,
                "durationMs": 1,
                "processStarted": True,
                "processTreeTerminated": False,
                "stdout": raw_payload,
                "stderr": "",
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source, prompt, _record_digest, _spec_digest = (
                self._factory_fixture(root)
            )
            for extra in ("frontend", "docs", "assets-source"):
                (root / extra).mkdir()
            (root / "codex.exe").write_bytes(b"")
            patches = self._runner_patches(root, fake_chat)
            with (
                patches[0], patches[1], patches[2], patches[3],
                patches[4], patches[5], patches[6], patches[7],
                mock.patch.object(
                    self.runner,
                    "require_fresh_corrective_verifier_quota",
                    return_value={"status": "ready"},
                ),
            ):
                result = self.runner.run_codex(
                    prompt,
                    "ea_developer",
                    "mission-ea-factory-semantic-terminal",
                    execution_mode="auto_guarded",
                    read_only_work=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )
            source_names = {item.name for item in source.iterdir()}

        self.assertEqual(call_count, 2)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["status"], "invalid_output")
        self.assertTrue(result["semanticRepair"]["attempted"])
        self.assertFalse(result["semanticRepair"]["succeeded"])
        self.assertEqual(result["semanticRepair"]["attemptCount"], 1)
        self.assertEqual(
            [item["code"] for item in result["semanticRepair"]["remainingIssues"]],
            ["ea_closed_bar_execution_guard_missing"],
        )
        self.assertIn(
            "ea_closed_bar_execution_guard_missing",
            result["structuredOutputError"],
        )
        self.assertEqual(source_names, {"strategy-spec-v01.json"})

    def test_exact_profile_rejects_primary_and_repaired_ai_without_mission_guards(self) -> None:
        call_count = 0

        def fake_chat(command, **kwargs):
            nonlocal call_count
            call_count += 1
            raw_final_path = Path(command[command.index("-o") + 1])
            raw_payload = json.dumps({
                "fileName": f"GenericCandidate{call_count}.mq4",
                "content": self.SOURCE_CONTENT,
            })
            raw_final_path.write_text(raw_payload, encoding="utf-8")
            return {
                "ok": True,
                "exitCode": 0,
                "durationMs": 1,
                "processStarted": True,
                "processTreeTerminated": False,
                "stdout": raw_payload,
                "stderr": "",
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source, prompt, _record_digest, spec_digest = (
                self._factory_fixture(root)
            )
            for extra in ("frontend", "docs", "assets-source"):
                (root / extra).mkdir()
            (root / "codex.exe").write_bytes(b"")
            patches = self._runner_patches(root, fake_chat)
            with (
                patches[0], patches[1], patches[2], patches[3],
                patches[4], patches[5], patches[6], patches[7],
                mock.patch.object(
                    self.runner,
                    "require_fresh_corrective_verifier_quota",
                    return_value={"status": "ready"},
                ),
                mock.patch.object(
                    self.runner,
                    "EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST",
                    self.STRATEGY_BRIEF_DIGEST,
                ),
                mock.patch.object(
                    self.runner,
                    "EA_FACTORY_CAN_SLIM_CERTIFIED_SPEC_DIGEST",
                    spec_digest,
                ),
            ):
                result = self.runner.run_codex(
                    prompt,
                    "ea_developer",
                    "mission-ea-factory-exact-mission-terminal",
                    execution_mode="auto_guarded",
                    read_only_work=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )
            source_names = {item.name for item in source.iterdir()}

        self.assertEqual(call_count, 2)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["status"], "invalid_output")
        self.assertEqual(result["semanticRepair"]["attemptCount"], 1)
        self.assertFalse(result["semanticRepair"]["succeeded"])
        self.assertFalse(result["semanticRepair"]["aiRepairSucceeded"])
        self.assertFalse(result["semanticRepair"]["certifiedFallbackSucceeded"])
        self.assertEqual(result["semanticRepair"]["sourceOrigin"], "none")
        self.assertEqual(
            [
                item["code"]
                for item in result["semanticRepair"]["remainingIssues"]
            ],
            ["ea_explicit_mission_guardrails_missing"],
        )
        self.assertEqual(source_names, {"strategy-spec-v01.json"})

    def test_materializer_writes_exact_file_and_digest_without_content_leak(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source, prompt, record_digest, spec_digest = (
                self._factory_fixture(root)
            )
            raw = json.dumps({
                "fileName": "ExactEA.mq4",
                "content": self.SOURCE_CONTENT,
            })
            patches = self._patch_roots(root)
            with patches[0], patches[1]:
                result = self.runner.materialize_ea_factory_source_result(
                    raw, prompt, relative
                )

            written = (source / "ExactEA.mq4").read_bytes()
            expected_digest = hashlib.sha256(
                self.SOURCE_CONTENT.encode("utf-8")
            ).hexdigest()
            values = {
                item["field"]: item["value"]
                for item in result["contractFields"]
            }

        self.assertEqual(written, self.SOURCE_CONTENT.encode("utf-8"))
        self.assertEqual(values["sourceDigest"], expected_digest)
        self.assertEqual(values["sourceRecordDigest"], record_digest)
        self.assertEqual(values["strategySpecDigest"], spec_digest)
        self.assertEqual(values["platform"], "mt4")
        self.assertEqual(
            json.loads(values["sourceFiles"]),
            [f"workspace/{relative}/ExactEA.mq4"],
        )
        self.assertEqual(
            result["evidenceKinds"],
            [
                "project_relative_source_path",
                "source_digest",
                "uncompiled_status",
            ],
        )
        self.assertNotIn(
            self.SOURCE_CONTENT, json.dumps(result, ensure_ascii=False)
        )

    def test_indicator_materializer_binds_rules_to_buffers_and_rejects_marker_sink(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source_root, prompt, brief_digest = self._indicator_factory_fixture(
                root,
                build_id="ea-build-indicator-valid",
            )
            indicator_source = self._exact_indicator_source(brief_digest)
            raw = json.dumps({
                "fileName": "BoundIndicator.mq4",
                "content": indicator_source,
            })
            patches = self._patch_roots(root)
            with patches[0], patches[1]:
                result = self.runner.materialize_ea_factory_source_result(
                    raw,
                    prompt,
                    relative,
                )
            values = {
                item["field"]: item["value"]
                for item in result["contractFields"]
            }
            manifest = json.loads(values["blueprintCoverageManifest"])
            profile = json.loads(values["strategyProfile"])
            checklist = json.loads(values["compileChecklist"])
            self.assertTrue(manifest["complete"])
            self.assertTrue(manifest["checks"]["strategyBriefDigestBound"])
            self.assertTrue(manifest["checks"]["conditionalSignalOutputs"])
            self.assertEqual(profile["artifactKind"], "custom_indicator")
            self.assertFalse(profile["backtestApplicable"])
            self.assertIn("do_not_attach_or_trade", checklist)
            self.assertTrue((source_root / "BoundIndicator.mq4").is_file())

            sink_relative, sink_root, sink_prompt, sink_brief_digest = (
                self._indicator_factory_fixture(
                    root,
                    build_id="ea-build-indicator-sink",
                )
            )
            sink_source = self._exact_indicator_source(sink_brief_digest)
            sink_source = sink_source.replace(
                "SignalBuffer[1] = EMPTY_VALUE;",
                "SignalBuffer[1] = EMPTY_VALUE; int markerSink = 0;",
            ).replace(
                "SignalBuffer[1] = low[1];",
                "markerSink = 1;",
            ).replace(
                "SignalBuffer[1] = high[1];",
                "markerSink = 2;",
            )
            sink_raw = json.dumps({
                "fileName": "SinkIndicator.mq4",
                "content": sink_source,
            })
            patches = self._patch_roots(root)
            with patches[0], patches[1]:
                with self.assertRaisesRegex(
                    ValueError,
                    "failed digest-bound structural signal review",
                ):
                    self.runner.materialize_ea_factory_source_result(
                        sink_raw,
                        sink_prompt,
                        sink_relative,
                    )
            self.assertEqual(
                {item.name for item in sink_root.iterdir()},
                {"strategy-spec-v01.json"},
            )

    def test_indicator_materializer_defers_prose_math_semantics_to_review(self) -> None:
        mutations = {
            "arbitrary": (
                "FastValue(2) <= SlowValue(2)\n                     && FastValue(1) > SlowValue(1)",
                "close[2] <= open[2] && close[1] > open[1]",
            ),
            "swapped": (
                "FastValue(2) <= SlowValue(2)\n                     && FastValue(1) > SlowValue(1)",
                "SlowValue(2) <= FastValue(2) && SlowValue(1) > FastValue(1)",
            ),
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for label, (expected, replacement) in mutations.items():
                relative, source_root, prompt, brief_digest = (
                    self._indicator_factory_fixture(
                        root,
                        build_id=f"ea-build-indicator-{label}",
                    )
                )
                content = self._exact_indicator_source(brief_digest).replace(
                    expected,
                    replacement,
                )
                self.assertNotEqual(content, self._exact_indicator_source(brief_digest))
                patches = self._patch_roots(root)
                with patches[0], patches[1]:
                    result = self.runner.materialize_ea_factory_source_result(
                        json.dumps({
                            "fileName": f"ReviewPending{label.title()}.mq4",
                            "content": content,
                        }),
                        prompt,
                        relative,
                    )
                values = {
                    row["field"]: row["value"]
                    for row in result["contractFields"]
                }
                manifest = json.loads(values["blueprintCoverageManifest"])
                self.assertTrue(manifest["complete"])
                self.assertTrue(
                    (source_root / f"ReviewPending{label.title()}.mq4").is_file()
                )

    def test_invalid_structured_outputs_never_write_a_source(self) -> None:
        oversized_content = (
            self.SOURCE_CONTENT
            + "//"
            + ("x" * self.runner.EA_FACTORY_SOURCE_MAX_CHARS)
        )
        invalid_payloads = {
            "filename_traversal": json.dumps({
                "fileName": "../evil.mq4", "content": self.SOURCE_CONTENT
            }),
            "nested_filename": json.dumps({
                "fileName": "nested/evil.mq4", "content": self.SOURCE_CONTENT
            }),
            "wrong_extension": json.dumps({
                "fileName": "WrongEA.mq5", "content": self.SOURCE_CONTENT
            }),
            "malformed_json": "{",
            "extra_field": json.dumps({
                "fileName": "ExtraEA.mq4",
                "content": self.SOURCE_CONTENT,
                "path": "elsewhere",
            }),
            "duplicate_key": (
                '{"fileName":"One.mq4","fileName":"Two.mq4",'
                f'"content":{json.dumps(self.SOURCE_CONTENT)}}}'
            ),
            "empty_content": json.dumps({
                "fileName": "EmptyEA.mq4", "content": "   \n"
            }),
            "malformed_content": json.dumps({
                "fileName": "MalformedEA.mq4",
                "content": "This is not MQL source.",
            }),
            "oversized_content": json.dumps({
                "fileName": "OversizedEA.mq4", "content": oversized_content
            }),
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source, prompt, _record_digest, _spec_digest = (
                self._factory_fixture(root)
            )
            patches = self._patch_roots(root)
            with patches[0], patches[1]:
                for label, raw in invalid_payloads.items():
                    with self.subTest(label=label):
                        with self.assertRaises(ValueError):
                            self.runner.materialize_ea_factory_source_result(
                                raw, prompt, relative
                            )
                        self.assertEqual(
                            {item.name for item in source.iterdir()},
                            {"strategy-spec-v01.json"},
                        )
                        self.assertFalse((root / "evil.mq4").exists())

    def test_binding_tamper_and_conflicting_destination_fail_without_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source, prompt, _record_digest, _spec_digest = (
                self._factory_fixture(root)
            )
            raw = json.dumps({
                "fileName": "BoundEA.mq4", "content": self.SOURCE_CONTENT
            })
            patches = self._patch_roots(root)
            with patches[0], patches[1]:
                with self.assertRaises(ValueError):
                    self.runner.materialize_ea_factory_source_result(
                        raw,
                        prompt.replace(
                            "EA_FACTORY_BUILD_ID:ea-build-1234567890-abc123",
                            "EA_FACTORY_BUILD_ID:ea-build-another",
                        ),
                        relative,
                    )
                self.assertFalse((source / "BoundEA.mq4").exists())
                (source / "BoundEA.mq4").write_text(
                    "different", encoding="utf-8"
                )
                with self.assertRaises(ValueError):
                    self.runner.materialize_ea_factory_source_result(
                        raw, prompt, relative
                    )
                self.assertEqual(
                    (source / "BoundEA.mq4").read_text(encoding="utf-8"),
                    "different",
                )

    def test_tampered_scoped_roots_fail_before_process_start(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace").mkdir()
            fake_chat = mock.Mock()
            patches = self._runner_patches(root, fake_chat)
            invalid = (
                "../ea-factory/ea-build-1/Source",
                "ea-factory\\ea-build-1\\Source",
                "ea-factory/ea-build-1/Source/",
                "ea-factory/not-a-build/Source",
                "ea-factory/ea-build-1/source",
                str((root / "workspace" / "ea-factory" / "ea-build-1" / "Source").resolve()),
            )
            with (
                patches[0], patches[1], patches[2], patches[3],
                patches[4], patches[5], patches[6], patches[7],
            ):
                results = [
                    self.runner.run_codex(
                        "Generate source.",
                        "ea_developer",
                        f"mission-invalid-{index}",
                        execution_mode="auto_guarded",
                        read_only_work=True,
                        result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                        scoped_workspace_write_root=value,
                    )
                    for index, value in enumerate(invalid)
                ]

        fake_chat.assert_not_called()
        for result in results:
            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "workspace_policy_invalid")
            self.assertFalse(result["processStarted"])

    def test_scoped_profile_rejects_write_search_and_other_execution_modes(self) -> None:
        relative = "ea-factory/ea-build-1234/Source"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / Path(relative)).mkdir(parents=True)
            fake_chat = mock.Mock()
            patches = self._runner_patches(root, fake_chat)
            with (
                patches[0], patches[1], patches[2], patches[3],
                patches[4], patches[5], patches[6], patches[7],
            ):
                writable = self.runner.run_codex(
                    "Generate source.", "ea_developer", "mission-scoped-writable",
                    execution_mode="auto_guarded",
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )
                searched = self.runner.run_codex(
                    "Generate source.", "ea_developer", "mission-scoped-search",
                    execution_mode="auto_guarded", read_only_work=True,
                    web_search=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )
                manual = self.runner.run_codex(
                    "Generate source.", "ea_developer", "mission-scoped-manual",
                    execution_mode="manual_guarded", read_only_work=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )
                legacy = self.runner.run_codex(
                    "Generate source.", "ea_developer", "mission-scoped-legacy",
                    execution_mode="auto_guarded",
                    scoped_workspace_write_root=relative,
                )
                missing_scope = self.runner.run_codex(
                    "Generate source.", "ea_developer", "mission-missing-scope",
                    execution_mode="auto_guarded", read_only_work=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                )

        fake_chat.assert_not_called()
        for result in (writable, searched, manual, legacy, missing_scope):
            self.assertEqual(result["status"], "workspace_policy_invalid")
            self.assertFalse(result["processStarted"])

    def test_scoped_source_rejects_linked_source_directory(self) -> None:
        relative = "ea-factory/ea-build-linked/Source"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "actual-source"
            target.mkdir()
            linked = root / "workspace" / Path(relative)
            linked.parent.mkdir(parents=True)
            try:
                os.symlink(target, linked, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"directory symlink unavailable: {error}")
            fake_chat = mock.Mock()
            patches = self._runner_patches(root, fake_chat)
            with (
                patches[0], patches[1], patches[2], patches[3],
                patches[4], patches[5], patches[6], patches[7],
            ):
                result = self.runner.run_codex(
                    "Generate source.",
                    "ea_developer",
                    "mission-scoped-link",
                    execution_mode="auto_guarded",
                    read_only_work=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )

        fake_chat.assert_not_called()
        self.assertEqual(result["status"], "workspace_policy_invalid")
        self.assertFalse(result["processStarted"])


if __name__ == "__main__":
    unittest.main()
