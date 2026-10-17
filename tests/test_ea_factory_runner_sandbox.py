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
LINDA_LEGACY_BRIEF_FIXTURE_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "linda_holy_grail_legacy_brief_v2.json"
)


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


def load_linda_legacy_brief() -> dict:
    return json.loads(LINDA_LEGACY_BRIEF_FIXTURE_PATH.read_text(encoding="utf-8"))


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
    def _linda_holy_grail_certified_brief(cls) -> dict:
        return cls.runner.upgrade_linda_holy_grail_brief_for_certified_profile(
            load_linda_legacy_brief()
        )

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

    @classmethod
    def _linda_holy_grail_brief(cls) -> dict:
        marker = "[IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT]"
        policy = "[POLICY=compact-ea-safe-inputs-v2]"
        brief = dict(cls.STRATEGY_BRIEF)
        brief.update({
            "systemName": "Linda Bradford Raschke Holy Grail Pullback",
            "entryRules": (
                "Buy: use a confirmed closed bar [1], ADX(14), SMA(20), "
                "ADX[1] > 30 AND ADX[1] > ADX[2], then place a buy stop "
                "above the signal high after a pullback to SMA(20). Sell: use "
                "the inverse trend and pullback rule and place a sell stop below "
                "the signal low. Cancel an untriggered order after 3 days."
            ),
            "recoveryRules": (
                f"{marker}{policy}[COMPONENT=recoveryRules] RecoveryMode=none; "
                "no grid, martingale, averaging, hedging, recovery orders, or "
                "lot increase after a loss."
            ),
            "exitRules": (
                "Buy Stop Loss is below the pullback swing low and Sell Stop "
                "Loss is above the pullback swing high. Move protection with "
                "successive swing lows or successive swing highs. "
                f"{marker}{policy}[COMPONENT=exitRules] Use StopLossPoints=300 "
                "only as fallback with ExecutionBufferPoints=2 and use "
                "TakeProfitPoints=600 as an editable default. "
                f"{marker}{policy}[COMPONENT=take_profit] TakeProfitPoints=600 "
                "broker points above Buy entry or below Sell entry. "
                f"{marker}{policy}[COMPONENT=trailing_stop] TrailingStop=false. "
                f"{marker}{policy}[COMPONENT=break_even] BreakEven=false. "
                f"{marker}{policy}[COMPONENT=partial_close] PartialClose=false."
            ),
            "moneyManagement": (
                f"{marker}{policy}[COMPONENT=moneyManagement] "
                "PositionSizingMode=fixed_lot and FixedLot=0.01 by default; "
                "optional percent_equity uses RiskPercent=1.0 and validates "
                "broker min/max/step volume and margin. Set "
                "MaxOpenPositionsPerSymbolMagic=1 and count live and pending "
                "orders for the same Symbol+Magic. "
                f"{marker}{policy}[COMPONENT=lot_calculation] "
                "RiskMoney=Equity*RiskPercent/100 and "
                "Lot=RiskMoney/LossPerLotAtSL from actual stop distance, "
                "TickSize and TickValue, rounded down by VolumeStep."
            ),
            "orderExecution": (
                "กฎจากแหล่งข้อมูลระบุการวาง pending order: Buy ใช้ buy stop "
                "เหนือ high ของแท่งที่แตะ 20-SMA และ Sell ใช้ sell stop ใต้ low "
                "ของแท่งที่แตะ 20-SMA พร้อมยกเลิกหากไม่ถูก trigger ภายใน 3 วัน "
                "จึงต้องรักษากฎ pending stop order นี้ไว้ ไม่แปลงเป็น Market order "
                "สำหรับ entry หลัก "
                f"{marker}{policy}[COMPONENT=orderExecution] "
                "เฉพาะส่วน timing ที่แหล่งไม่ได้ระบุสำหรับ EA ให้ใช้ "
                "SignalBarShift=1, TradeOnNewBar=true, prime current bar on "
                "startup, อ่านเฉพาะแท่งปิด และประมวลผลหนึ่งครั้งบน first tick "
                "ของแท่งใหม่ Pending order ต้องผูก MagicNumber, Symbol, "
                "timeframe/input profile และ expiration/cancel logic ตาม 3 วัน "
                "หรือจำนวนแท่งที่สอดคล้องกับ timeframe ที่ผู้ใช้เลือก โดยไม่ใช้ "
                "bar 0 ในการยืนยันสัญญาณ"
            ),
            "displayRequirements": (
                f"{marker}{policy}[COMPONENT=displayRequirements] Display system "
                "name, signal state, balance, equity, spread, ADX(14), SMA(20), "
                "live plus pending count, Symbol+Magic and TradeOnNewBar state."
            ),
            "additionalNotes": (
                f"{marker}{policy}[COMPONENT=optimization_inputs] Inputs remain "
                "user-editable and require Compile, Backtest and Demo validation."
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

    def _custom_ema_factory_fixture(
        self,
        root: Path,
        *,
        build_id: str = "ea-build-custom-ema-certified-runner",
        spec_overrides: dict | None = None,
    ) -> tuple[str, Path, str, dict, str]:
        relative = f"ea-factory/{build_id}/Source"
        source = root / "workspace" / Path(relative)
        source.mkdir(parents=True)
        spec = {
            "schemaVersion": "ea-factory-strategy-spec-v3",
            "strategySchemaVersion": self.runner.EA_STRATEGY_BRIEF_SCHEMA_VERSION,
            "buildId": build_id,
            "sourceRecordId": self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_SOURCE_RECORD_ID,
            "recordDigest": self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_SOURCE_RECORD_DIGEST,
            "sourceKind": "custom_operator",
            "sourceKey": self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_SOURCE_KEY,
            "core": json.loads(json.dumps(
                self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_CORE,
                ensure_ascii=False,
            )),
            "artifactKind": "expert_advisor",
            "targetPlatform": "mt5",
            "language": "mql5",
            "strategyBrief": json.loads(json.dumps(
                self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_BRIEF,
                ensure_ascii=False,
            )),
            "strategyBriefDigest": self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_BRIEF_DIGEST,
            "immutable": True,
        }
        if spec_overrides:
            spec.update(spec_overrides)
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
            "[EA_FACTORY_SOURCE_RECORD_DIGEST:"
            f"{spec['recordDigest']}]"
            f"[EA_FACTORY_STRATEGY_SPEC_DIGEST:{spec_digest}]"
            "[EA_FACTORY_PLATFORM:mt5] "
            f"Read ea-factory/{build_id}/Source/strategy-spec-v01.json and generate source."
        )
        return relative, source, prompt, spec, spec_digest

    def _patch_roots(self, root: Path):
        return (
            mock.patch.object(self.runner, "PROJECT_ROOT", root),
            mock.patch.object(
                self.runner, "AUTO_WORKSPACE_ROOT", root / "workspace"
            ),
        )

    def _source_review_prompt(
        self,
        *,
        build_id: str = "ea-build-1792035402024-35116e",
        spec_byte_size: int = 31 * 1024,
        source_text: str | None = None,
    ) -> tuple[str, dict, str, str]:
        spec = {
            "schemaVersion": "ea-factory-strategy-spec-v3",
            "buildId": build_id,
            "targetPlatform": "mt5",
            "recordDigest": "a" * 64,
            "immutable": True,
            "reviewFixturePadding": "",
        }
        empty_spec = json.dumps(
            spec,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        padding_size = spec_byte_size - len(empty_spec.encode("utf-8"))
        self.assertGreater(padding_size, 0)
        spec["reviewFixturePadding"] = "x" * padding_size
        spec_text = json.dumps(
            spec,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        self.assertEqual(len(spec_text.encode("utf-8")), spec_byte_size)

        if source_text is None:
            source_prefix = "#property strict\nvoid OnTick() {}\n// review fixture\n"
            source_text = source_prefix + (
                "x" * (16054 - len(source_prefix.encode("utf-8")))
            )
        source_bytes = source_text.encode("utf-8")
        spec_bytes = spec_text.encode("utf-8")
        packet = {
            "schemaVersion": "ea-factory-source-review-input-v1",
            "buildId": build_id,
            "platform": "mt5",
            "artifactKind": "expert_advisor",
            "generationReportId": "report-worker-generation",
            "complete": True,
            "sourceContextTruncated": False,
            "strategySpecDigest": hashlib.sha256(spec_bytes).hexdigest(),
            "strategySpecByteSize": len(spec_bytes),
            "strategySpecContent": spec_text,
            "sources": [{
                "fileName": "strategy.mq5",
                "sourceDigest": hashlib.sha256(source_bytes).hexdigest(),
                "byteSize": len(source_bytes),
                "content": source_text,
            }],
        }
        encoded = json.dumps(
            packet,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        prompt = (
            "Review the complete Backend-bound Source and Strategy Spec.\n"
            f"{self.runner.EA_FACTORY_SOURCE_REVIEW_PACKET_START}\n"
            f"{encoded}\n"
            f"{self.runner.EA_FACTORY_SOURCE_REVIEW_PACKET_END}"
        )
        return prompt, packet, spec_text, source_text

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

    def test_source_review_packet_accepts_complete_live_sized_inputs(self) -> None:
        prompt, expected, spec_text, source_text = self._source_review_prompt()

        packet = self.runner.validate_ea_factory_source_review_prompt(prompt)
        output_schema = self.runner.build_work_output_schema(
            12000,
            self.runner.EA_FACTORY_SOURCE_REVIEW_RESULT_PROFILE,
        )
        bounded = self.runner.bound_mission_prompt(
            prompt,
            self.runner.EA_FACTORY_SOURCE_REVIEW_RESULT_PROFILE,
            execution_mode="auto_guarded",
        )

        self.assertEqual(packet, expected)
        self.assertEqual(bounded, prompt)
        self.assertEqual(len(spec_text.encode("utf-8")), 31 * 1024)
        self.assertEqual(len(source_text.encode("utf-8")), 16054)
        self.assertFalse(packet["sourceContextTruncated"])
        self.assertEqual(
            output_schema["properties"]["status"]["enum"],
            ["completed"],
        )
        self.assertEqual(
            output_schema["properties"]["contractFields"]["minItems"],
            len(self.runner.EA_FACTORY_SOURCE_REVIEW_CONTRACT_FIELDS),
        )
        self.assertEqual(
            output_schema["properties"]["evidenceKinds"]["minItems"],
            3,
        )

    def test_source_review_packet_digest_and_packet_bounds_fail_closed(self) -> None:
        prompt, packet, _spec_text, _source_text = self._source_review_prompt()

        def wrap(value: dict) -> str:
            encoded = json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            return (
                "Review source.\n"
                f"{self.runner.EA_FACTORY_SOURCE_REVIEW_PACKET_START}\n"
                f"{encoded}\n"
                f"{self.runner.EA_FACTORY_SOURCE_REVIEW_PACKET_END}"
            )

        invalid_packets = []
        wrong_source_digest = json.loads(json.dumps(packet))
        wrong_source_digest["sources"][0]["sourceDigest"] = "0" * 64
        invalid_packets.append(wrong_source_digest)
        wrong_source_size = json.loads(json.dumps(packet))
        wrong_source_size["sources"][0]["byteSize"] += 1
        invalid_packets.append(wrong_source_size)
        wrong_spec_digest = json.loads(json.dumps(packet))
        wrong_spec_digest["strategySpecDigest"] = "0" * 64
        invalid_packets.append(wrong_spec_digest)
        truncated = json.loads(json.dumps(packet))
        truncated["sourceContextTruncated"] = True
        invalid_packets.append(truncated)

        for index, invalid in enumerate(invalid_packets):
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.runner.validate_ea_factory_source_review_prompt(wrap(invalid))

        self.assertGreater(len(prompt), self.runner.MISSION_PROMPT_MAX_CHARS)
        with self.assertRaises(ValueError):
            self.runner.bound_mission_prompt(prompt, "general")

        oversized_source = "\n" * 200000
        oversized_prompt, _packet, _spec, _source = self._source_review_prompt(
            source_text=oversized_source
        )
        self.assertGreater(
            len(oversized_prompt),
            self.runner.EA_FACTORY_SOURCE_REVIEW_PACKET_MAX_CHARS,
        )
        with self.assertRaises(ValueError):
            self.runner.validate_ea_factory_source_review_prompt(
                oversized_prompt
            )

    def test_source_review_packet_rejects_parsed_keys_and_quoted_multiword_secrets(self) -> None:
        _prompt, base_packet, base_spec_text, base_source_text = (
            self._source_review_prompt()
        )

        def wrap(spec_text: str, source_text: str) -> str:
            packet = json.loads(json.dumps(base_packet))
            spec_bytes = spec_text.encode("utf-8")
            source_bytes = source_text.encode("utf-8")
            packet["strategySpecContent"] = spec_text
            packet["strategySpecByteSize"] = len(spec_bytes)
            packet["strategySpecDigest"] = hashlib.sha256(spec_bytes).hexdigest()
            packet["sources"][0]["content"] = source_text
            packet["sources"][0]["byteSize"] = len(source_bytes)
            packet["sources"][0]["sourceDigest"] = hashlib.sha256(
                source_bytes
            ).hexdigest()
            encoded = json.dumps(
                packet,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            return (
                "Review source.\n"
                f"{self.runner.EA_FACTORY_SOURCE_REVIEW_PACKET_START}\n"
                f"{encoded}\n"
                f"{self.runner.EA_FACTORY_SOURCE_REVIEW_PACKET_END}"
            )

        escaped_key_spec = base_spec_text.replace(
            "{",
            '{"pass\\u0077ord":null,',
            1,
        )
        free_text_spec = json.loads(base_spec_text)
        free_text_spec["additionalNotes"] = (
            'password = "a b c d e f g h"'
        )
        free_text_spec_text = json.dumps(
            free_text_spec,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        embedded_key_spec = json.loads(base_spec_text)
        embedded_key_spec["authorizationHeader"] = None
        embedded_key_spec_text = json.dumps(
            embedded_key_spec,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        quoted_source = (
            base_source_text[:-80]
            + 'input string password = "a b c d e f g h";\n'
        )
        attacks = {
            "escaped_sensitive_spec_key": (
                escaped_key_spec,
                base_source_text,
            ),
            "embedded_sensitive_spec_key": (
                embedded_key_spec_text,
                base_source_text,
            ),
            "quoted_secret_in_spec_text": (
                free_text_spec_text,
                base_source_text,
            ),
            "quoted_secret_in_source": (
                base_spec_text,
                quoted_source,
            ),
        }
        for name, (spec_text, source_text) in attacks.items():
            with self.subTest(name=name):
                self.assertFalse(
                    self.runner.contains_potential_secret(
                        spec_text if name != "quoted_secret_in_source" else source_text
                    )
                )
                prompt = wrap(spec_text, source_text)
                with self.assertRaises(ValueError):
                    self.runner.validate_ea_factory_source_review_prompt(prompt)

                result = self.runner.run_codex(
                    prompt,
                    "ea_developer",
                    f"mission-source-review-{name}",
                    result_profile=(
                        self.runner.EA_FACTORY_SOURCE_REVIEW_RESULT_PROFILE
                    ),
                    execution_mode="auto_guarded",
                    read_only_work=True,
                )
                self.assertFalse(result["ok"])
                self.assertEqual(result["status"], "source_review_input_invalid")
                self.assertFalse(result["processStarted"])

    def test_source_review_profile_rejects_secret_and_broader_execution(self) -> None:
        prompt, _packet, _spec, source_text = self._source_review_prompt()
        secret_prompt, _packet, _spec, _source = self._source_review_prompt(
            source_text=(
                source_text[:-60]
                + '// api_key = "source-review-secret-1234567890"\n'
            )
        )
        fake_chat = mock.Mock()

        cases = (
            ("secret", secret_prompt, {}, "source_review_input_invalid"),
            ("manual", prompt, {"execution_mode": "manual_guarded", "read_only_work": True}, "workspace_policy_invalid"),
            ("writable", prompt, {"execution_mode": "auto_guarded"}, "workspace_policy_invalid"),
            ("web", prompt, {"execution_mode": "auto_guarded", "read_only_work": True, "web_search": True}, "workspace_policy_invalid"),
            ("scoped", prompt, {
                "execution_mode": "auto_guarded",
                "read_only_work": True,
                "scoped_workspace_write_root": "ea-factory/ea-build-1/Source",
            }, "workspace_policy_invalid"),
        )
        for label, case_prompt, kwargs, expected_status in cases:
            with self.subTest(label=label):
                result = self.runner.run_codex(
                    case_prompt,
                    "ea_developer",
                    f"mission-source-review-{label}",
                    result_profile=(
                        self.runner.EA_FACTORY_SOURCE_REVIEW_RESULT_PROFILE
                    ),
                    **kwargs,
                )
                self.assertFalse(result["ok"])
                self.assertEqual(result["status"], expected_status)
                self.assertFalse(result["processStarted"])

        fake_chat.assert_not_called()

    def test_source_review_runs_packet_only_with_shell_features_disabled(self) -> None:
        prompt, packet, _spec_text, source_text = self._source_review_prompt()
        captured: dict[str, object] = {}
        contract_values = {
            "sourceDigest": packet["sources"][0]["sourceDigest"],
            "sourceRecordDigest": "a" * 64,
            "strategySpecDigest": packet["strategySpecDigest"],
            "platform": "mt5",
            "strategyCoverage": json.dumps({
                "coveredFields": ["system_name"],
                "uncoveredFields": [],
            }),
            "issues": "[]",
            "severity": "none",
            "lineReferences": "[]",
            "riskNotes": "Static review only.",
            "repairPlan": "No repair required.",
            "compileStatus": "source_only",
        }
        raw_payload = json.dumps({
            "status": "completed",
            "summary": "Complete packet-only static review.",
            "findings": [],
            "nextSteps": ["Compile separately in the visible adapter."],
            "evidence": [],
            "blockedCapability": "",
            "contractFields": [
                {"field": field, "value": contract_values[field]}
                for field in self.runner.EA_FACTORY_SOURCE_REVIEW_CONTRACT_FIELDS
            ],
            "evidenceKinds": [
                "source_digest",
                "review_scope",
                "compile_status_truth",
            ],
        })

        def fake_chat(command, **kwargs):
            captured["command"] = [str(item) for item in command]
            captured["cwd"] = Path(kwargs["cwd"])
            captured["prompt"] = str(kwargs.get("stdin") or "")
            raw_final_path = Path(command[command.index("-o") + 1])
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
            (root / "codex.exe").write_bytes(b"")
            patches = self._runner_patches(root, fake_chat)
            with (
                patches[0], patches[1], patches[2], patches[3],
                patches[4], patches[5], patches[6], patches[7],
            ):
                result = self.runner.run_codex(
                    prompt,
                    "ea_developer",
                    "mission-source-review-live-sized",
                    execution_mode="auto_guarded",
                    read_only_work=True,
                    result_profile=(
                        self.runner.EA_FACTORY_SOURCE_REVIEW_RESULT_PROFILE
                    ),
                )

        command = captured["command"]
        disabled = {
            command[index + 1]
            for index, value in enumerate(command[:-1])
            if value == "--disable"
        }
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
        self.assertNotIn("--add-dir", command)
        self.assertIn("shell_tool", disabled)
        self.assertIn("shell_snapshot", disabled)
        self.assertEqual(captured["cwd"], root / "workspace")
        wrapped_prompt = str(captured["prompt"])
        self.assertEqual(
            wrapped_prompt.count(
                self.runner.EA_FACTORY_SOURCE_REVIEW_PACKET_START
            ),
            1,
        )
        self.assertIn("packet-only static Source Review mode", wrapped_prompt)
        self.assertIn(
            "Do not search for, open, or read any repository",
            wrapped_prompt,
        )
        encoded = wrapped_prompt.split(
            self.runner.EA_FACTORY_SOURCE_REVIEW_PACKET_START,
            1,
        )[1].split(
            self.runner.EA_FACTORY_SOURCE_REVIEW_PACKET_END,
            1,
        )[0].strip()
        transported = json.loads(encoded)
        self.assertEqual(transported["sources"][0]["content"], source_text)

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

    def test_can_slim_mt5_scaffold_is_certified_and_mutations_fail_closed(self) -> None:
        brief = self._can_slim_legacy_brief()
        brief_digest = self.runner.compute_strategy_brief_digest(brief)
        spec_digest = "5" * 64

        # Similar records cannot opt themselves into the reviewed fallback.
        self.assertNotEqual(
            brief_digest,
            self.runner.EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST,
        )
        self.assertEqual(
            self.runner._build_ea_factory_source_semantic_repair_scaffold(
                brief,
                strategy_brief_digest=brief_digest,
                strategy_spec_digest=spec_digest,
                target_platform="mt5",
            ),
            "",
        )

        with mock.patch.object(
            self.runner,
            "EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST",
            brief_digest,
        ):
            scaffold = self.runner._build_ea_factory_source_semantic_repair_scaffold(
                brief,
                strategy_brief_digest=brief_digest,
                strategy_spec_digest=spec_digest,
                target_platform="mt5",
            )
            mission_attested = (
                self.runner._ea_factory_can_slim_mt5_scaffold_meets_mission(
                    scaffold
                )
            )
            profile = self.runner._ea_factory_certified_scaffold_profile(
                brief_digest,
                scaffold,
            )

        self.assertTrue(scaffold)
        self.assertTrue(mission_attested)
        self.assertEqual(
            profile,
            self.runner.EA_FACTORY_CAN_SLIM_MT5_CERTIFIED_PROFILE_VERSION,
        )
        self.assertLessEqual(
            len(scaffold),
            self.runner.EA_FACTORY_SEMANTIC_REPAIR_SCAFFOLD_MAX_CHARS,
        )
        self.assertIn(f"EA_STRATEGY_BRIEF_SHA256:{brief_digest}", scaffold)
        self.assertIn("MqlTradeRequest entryRequest = {};", scaffold)
        self.assertIn("MqlTradeRequest closeRequest = {};", scaffold)
        self.assertIn("closeRequest.position = positionTicket;", scaffold)
        self.assertIn("PositionSelectByTicket(positionTicket)", scaffold)
        self.assertIn("PositionGetInteger(POSITION_TYPE) != POSITION_TYPE_BUY", scaffold)
        self.assertIn("OrderCalcMargin(ORDER_TYPE_BUY", scaffold)
        self.assertIn("SYMBOL_TRADE_TICK_VALUE_LOSS", scaffold)
        self.assertIn("FundamentalCriteriaConfirmed", scaffold)
        self.assertIn("ExternalBenchmarkUptrendConfirmed", scaffold)
        self.assertIn("MaxOpenPositionsPerSymbolMagic", scaffold)
        self.assertNotIn("#include", scaffold)
        self.assertNotIn("CTrade", scaffold)

        def scoped_function_source(signature: str) -> str:
            start = scaffold.index(signature)
            opening = scaffold.index("{", start)
            depth = 0
            for cursor in range(opening, len(scaffold)):
                if scaffold[cursor] == "{":
                    depth += 1
                elif scaffold[cursor] == "}":
                    depth -= 1
                    if depth == 0:
                        return scaffold[start : cursor + 1]
            self.fail(f"unterminated scaffold function: {signature}")

        # Live Source Review found safety gaps that the certified fallback must
        # close in executable code, not merely mention in comments or helpers.
        self.assertIn("const double MAX_RISK_PERCENT = 2.0;", scaffold)
        self.assertIn("RiskPercent > MAX_RISK_PERCENT", scaffold)
        self.assertNotIn("RiskPercent > 100", scaffold)
        self.assertIn(
            "if(brokerFloor > requestedStopDistance) return;",
            scaffold,
        )
        self.assertIn(
            "stopDistance = MathMax(brokerFloor, requestedStopDistance)",
            scaffold,
        )
        self.assertIn("if(stopDistance > requestedStopDistance) return;", scaffold)
        self.assertIn(
            "NormalizePriceUpToTick(entryPrice - stopDistance, priceTick)",
            scaffold,
        )
        self.assertIn(
            "actualStopDistance > requestedStopDistance",
            scaffold,
        )
        self.assertIn(
            "maximumStopDistance = entryPrice * 8.0 / 100.0",
            scaffold,
        )
        self.assertIn(
            "actualStopDistance > maximumStopDistance) return;",
            scaffold,
        )
        self.assertIn("brokerStopFloor < 0", scaffold)
        self.assertIn("brokerFreezeFloor < 0", scaffold)
        self.assertIn(
            "!MathIsValidNumber(brokerStopFloor) || brokerStopFloor < 0",
            scaffold,
        )
        self.assertIn(
            "!MathIsValidNumber(brokerFreezeFloor) || brokerFreezeFloor < 0",
            scaffold,
        )
        self.assertNotIn("brokerStopFloor <= 0", scaffold)
        self.assertNotIn("brokerFreezeFloor <= 0", scaffold)
        stop_query_index = scaffold.index(
            "SYMBOL_TRADE_STOPS_LEVEL"
        )
        freeze_query_index = scaffold.index(
            "SYMBOL_TRADE_FREEZE_LEVEL",
            stop_query_index,
        )
        self.assertIn(
            "if(GetLastError() != 0) return;",
            scaffold[stop_query_index:freeze_query_index],
        )
        self.assertIn(
            "if(GetLastError() != 0) return;",
            scaffold[freeze_query_index:],
        )

        self.assertIn("int ResolveEntryFillingMode()", scaffold)
        self.assertIn("int ResolveCloseFillingMode()", scaffold)
        self.assertNotIn("int ResolveFillingMode()", scaffold)
        self.assertNotIn("&fillingMode", scaffold)
        self.assertIn("SYMBOL_TRADE_EXEMODE", scaffold)
        self.assertIn(
            "executionMode == SYMBOL_TRADE_EXECUTION_REQUEST",
            scaffold,
        )
        self.assertIn(
            "executionMode == SYMBOL_TRADE_EXECUTION_INSTANT",
            scaffold,
        )
        entry_filling_helper = scoped_function_source(
            "int ResolveEntryFillingMode()"
        )
        close_filling_helper = scoped_function_source(
            "int ResolveCloseFillingMode()"
        )
        self.assertIn("ORDER_FILLING_FOK", entry_filling_helper)
        self.assertIn("ORDER_FILLING_IOC", entry_filling_helper)
        self.assertIn("ORDER_FILLING_FOK", close_filling_helper)
        self.assertIn("ORDER_FILLING_IOC", close_filling_helper)
        self.assertNotIn("ORDER_FILLING_RETURN", scaffold)
        self.assertIn(
            "entryRequest.type_filling = (ENUM_ORDER_TYPE_FILLING)entryFillingMode;",
            scaffold,
        )
        self.assertIn(
            "closeRequest.type_filling = (ENUM_ORDER_TYPE_FILLING)closeFillingMode;",
            scaffold,
        )

        self.assertIn("const int MAX_CLOSE_RETRY_ATTEMPTS = 3;", scaffold)
        self.assertIn("int gCloseRetryCount", scaffold)
        self.assertIn("ulong gPendingCloseTicket", scaffold)
        self.assertIn("ulong gPendingCloseIdentifier", scaffold)
        self.assertIn("ulong gPendingCloseOrderTicket", scaffold)
        self.assertIn("ulong gPendingCloseDealTicket", scaffold)
        self.assertIn("double gPendingClosePreSendVolume", scaffold)
        self.assertIn("bool gCloseRetryAuthorized", scaffold)
        self.assertIn("if(gPendingCloseIdentifier != 0)", scaffold)
        self.assertIn("CloseManagedLong(gPendingCloseIdentifier)", scaffold)
        self.assertNotIn("CloseManagedLong(gPendingCloseTicket)", scaffold)
        self.assertNotIn("CloseManagedLong(managedTicket)", scaffold)
        self.assertIn(
            "gCloseRetryCount >= MAX_CLOSE_RETRY_ATTEMPTS",
            scaffold,
        )
        on_tick = scoped_function_source("void OnTick()")
        pending_close_start = on_tick.index("if(gPendingCloseIdentifier != 0)")
        exit_mode_start = on_tick.index("if(gExitModeActive)", pending_close_start)
        pending_close_block = on_tick[pending_close_start:exit_mode_start]
        pending_selector_index = pending_close_block.index(
            "SelectManagedLongByIdentifier(gPendingCloseIdentifier)"
        )
        pending_history_index = pending_close_block.index(
            "CloseHistoryProvesExit(gPendingCloseIdentifier)",
            pending_selector_index,
        )
        pending_ticket_reset_index = pending_close_block.index(
            "gPendingCloseTicket = 0;",
            pending_history_index,
        )
        pending_send_index = pending_close_block.index(
            "CloseManagedLong(gPendingCloseIdentifier)",
            pending_ticket_reset_index,
        )
        self.assertIn(
            "gPositionLookupReliable && !gPositionIdentifierVisible",
            pending_close_block[pending_selector_index:pending_history_index],
        )
        ambiguous_reconcile_start = pending_close_block.index(
            "if(!gCloseRetryAuthorized)"
        )
        ambiguous_reconcile_end = pending_close_block.index(
            "CloseManagedLong(gPendingCloseIdentifier)",
            ambiguous_reconcile_start,
        )
        ambiguous_reconcile_block = pending_close_block[
            ambiguous_reconcile_start:ambiguous_reconcile_end
        ]
        for required in (
            "PendingCloseOrderIsTerminal()",
            "MathIsValidNumber(observedVolume) && observedVolume > 0",
            "MathIsValidNumber(observedStep) && observedStep > 0",
            "MathIsValidNumber(gPendingClosePreSendVolume)",
            "observedVolume < gPendingClosePreSendVolume - observedEpsilon",
            "gCloseRetryCount = 0;",
            "gCloseRetryAfter = 0;",
            "gCloseRetryAuthorized = true;",
            'SetStatusComment("ExitAttention"',
            "return;",
        ):
            with self.subTest(ambiguous_close_reconciliation=required):
                self.assertIn(required, ambiguous_reconcile_block)
        ambiguous_terminal_index = ambiguous_reconcile_block.index(
            "PendingCloseOrderIsTerminal()"
        )
        ambiguous_monotonic_index = ambiguous_reconcile_block.index(
            "observedVolume < gPendingClosePreSendVolume - observedEpsilon"
        )
        ambiguous_retry_index = ambiguous_reconcile_block.index(
            "gCloseRetryAuthorized = true;", ambiguous_monotonic_index
        )
        ambiguous_count_reset_index = ambiguous_reconcile_block.index(
            "gCloseRetryCount = 0;", ambiguous_monotonic_index
        )
        ambiguous_backoff_reset_index = ambiguous_reconcile_block.index(
            "gCloseRetryAfter = 0;", ambiguous_monotonic_index
        )
        self.assertLess(ambiguous_terminal_index, ambiguous_monotonic_index)
        self.assertLess(ambiguous_monotonic_index, ambiguous_count_reset_index)
        self.assertLess(ambiguous_count_reset_index, ambiguous_backoff_reset_index)
        self.assertLess(ambiguous_backoff_reset_index, ambiguous_retry_index)
        self.assertLess(pending_selector_index, pending_history_index)
        self.assertLess(pending_history_index, pending_ticket_reset_index)
        self.assertLess(pending_ticket_reset_index, pending_send_index)
        self.assertNotIn(
            "if(!PositionSelectByTicket(gPendingCloseTicket))",
            pending_close_block,
        )

        exit_mode_block = on_tick[
            exit_mode_start : on_tick.index("static datetime lastBar", exit_mode_start)
        ]
        exit_identifier_read_index = exit_mode_block.index(
            "PositionGetInteger(POSITION_IDENTIFIER)"
        )
        exit_identifier_store_index = exit_mode_block.index(
            "gPendingCloseIdentifier = nextManagedIdentifier"
        )
        exit_next_return_index = exit_mode_block.index(
            "return;", exit_identifier_store_index
        )
        exit_mode_clear_index = exit_mode_block.index(
            "gExitModeActive = false", exit_next_return_index
        )
        self.assertLess(exit_identifier_read_index, exit_identifier_store_index)
        self.assertLess(exit_identifier_store_index, exit_next_return_index)
        self.assertLess(exit_next_return_index, exit_mode_clear_index)

        manage_existing_start = on_tick.index(
            "// Manage existing Longs before any entry-only external or broker gate."
        )
        entry_reconcile_gate_index = on_tick.index(
            "if(entryReconcileBlocked) return;", manage_existing_start
        )
        manage_existing_block = on_tick[
            manage_existing_start:entry_reconcile_gate_index
        ]
        managed_identifier_read_index = manage_existing_block.index(
            "PositionGetInteger(POSITION_IDENTIFIER)"
        )
        managed_identifier_store_index = manage_existing_block.index(
            "gPendingCloseIdentifier = managedIdentifier"
        )
        exit_mode_enable_index = manage_existing_block.index(
            "gExitModeActive = true"
        )
        self.assertLess(managed_identifier_read_index, managed_identifier_store_index)
        self.assertLess(exit_mode_enable_index, managed_identifier_store_index)
        self.assertNotIn("CloseManagedLong(", manage_existing_block)
        self.assertLess(pending_close_start, exit_mode_start)
        self.assertLess(exit_mode_start, manage_existing_start)
        self.assertLess(manage_existing_start, entry_reconcile_gate_index)

        close_helper = scoped_function_source(
            "bool CloseManagedLong(ulong positionIdentifier)"
        )
        self.assertNotIn("for(", close_helper)
        self.assertEqual(close_helper.count("OrderSend(closeRequest, closeResult)"), 1)
        self.assertIn(
            "if(!SelectManagedLongByIdentifier(positionIdentifier))",
            close_helper,
        )
        close_send_index = close_helper.index(
            "OrderSend(closeRequest, closeResult)"
        )
        pre_send_volume_index = close_helper.index(
            "gPendingClosePreSendVolume = positionVolume", 0, close_send_index
        )
        retry_disable_index = close_helper.rindex(
            "gCloseRetryAuthorized = false;", 0, close_send_index
        )
        close_order_capture_index = close_helper.index(
            "gPendingCloseOrderTicket = closeResult.order", close_send_index
        )
        close_deal_capture_index = close_helper.index(
            "gPendingCloseDealTicket = closeResult.deal",
            close_order_capture_index,
        )
        self.assertLess(pre_send_volume_index, retry_disable_index)
        self.assertLess(retry_disable_index, close_send_index)
        self.assertLess(close_send_index, close_order_capture_index)
        self.assertLess(close_order_capture_index, close_deal_capture_index)
        partial_close_index = close_helper.index(
            "if(closeResult.retcode == TRADE_RETCODE_DONE_PARTIAL)",
            close_send_index,
        )
        done_close_index = close_helper.index(
            "if(!SelectManagedLongByIdentifier(positionIdentifier)) {",
            partial_close_index,
        )
        partial_close_block = close_helper[
            partial_close_index:done_close_index
        ]
        self.assertIn(
            "partialRemainingVolume = PositionGetDouble(POSITION_VOLUME)",
            partial_close_block,
        )
        self.assertIn(
            "!MathIsValidNumber(partialRemainingVolume) || "
            "partialRemainingVolume <= 0",
            " ".join(partial_close_block.split()),
        )
        partial_monotonic_index = partial_close_block.index(
            "partialRemainingVolume >= positionVolume"
        )
        partial_retry_index = partial_close_block.index(
            "gCloseRetryAuthorized = true;",
            partial_monotonic_index,
        )
        partial_terminal_index = partial_close_block.index(
            "PendingCloseOrderIsTerminal()", partial_monotonic_index
        )
        self.assertLess(partial_monotonic_index, partial_retry_index)
        self.assertLess(partial_monotonic_index, partial_terminal_index)
        self.assertLess(partial_terminal_index, partial_retry_index)
        self.assertIn("return(false);", partial_close_block)
        self.assertNotIn("return(true);", partial_close_block)
        done_lookup_guard_index = close_helper.index(
            "if(!gPositionLookupReliable || gPositionIdentifierVisible) "
            "return(false);",
            done_close_index,
        )
        done_history_index = close_helper.index(
            "if(!CloseHistoryProvesExit(positionIdentifier)) return(false);",
            done_lookup_guard_index,
        )
        done_identifier_reset_index = close_helper.index(
            "gPendingCloseIdentifier = 0;",
            done_history_index,
        )
        remaining_volume_index = close_helper.index(
            "remainingVolume = PositionGetDouble(POSITION_VOLUME)",
            done_identifier_reset_index,
        )
        remaining_guard_index = close_helper.index(
            "remainingVolume >= positionVolume",
            remaining_volume_index,
        )
        remaining_retry_index = close_helper.index(
            "gCloseRetryAuthorized = true;",
            remaining_guard_index,
        )
        remaining_terminal_index = close_helper.index(
            "PendingCloseOrderIsTerminal()", remaining_guard_index
        )
        self.assertLess(done_close_index, done_lookup_guard_index)
        self.assertLess(done_lookup_guard_index, done_history_index)
        self.assertLess(done_history_index, done_identifier_reset_index)
        self.assertLess(close_send_index, remaining_volume_index)
        self.assertLess(remaining_volume_index, remaining_guard_index)
        self.assertLess(remaining_guard_index, remaining_terminal_index)
        self.assertLess(remaining_terminal_index, remaining_retry_index)
        self.assertLess(remaining_guard_index, remaining_retry_index)

        safe_no_execution_helper = scoped_function_source(
            "bool IsSafeNoExecutionTradeRetcode(uint retcode)"
        )
        for ambiguous_retcode in (
            "TRADE_RETCODE_PLACED",
            "TRADE_RETCODE_TIMEOUT",
            "TRADE_RETCODE_CONNECTION",
            "TRADE_RETCODE_LOCKED",
            "TRADE_RETCODE_CLOSE_ORDER_EXIST",
        ):
            with self.subTest(non_retryable_close_retcode=ambiguous_retcode):
                self.assertNotIn(ambiguous_retcode, safe_no_execution_helper)
        terminal_close_order_helper = scoped_function_source(
            "bool PendingCloseOrderIsTerminal()"
        )
        for required in (
            "gPendingCloseOrderTicket == 0",
            "OrdersTotal()",
            "OrderGetTicket(orderIndex)",
            "activeOrderTicket == gPendingCloseOrderTicket",
            "HistoryOrderSelect(gPendingCloseOrderTicket)",
            "ORDER_TYPE_SELL",
            "ORDER_MAGIC",
            "ORDER_SYMBOL",
            "ORDER_POSITION_ID",
            "gPendingCloseIdentifier",
            "ORDER_STATE_FILLED",
            "ORDER_STATE_CANCELED",
        ):
            with self.subTest(terminal_close_order_guard=required):
                self.assertIn(required, terminal_close_order_helper)
        close_history_helper = scoped_function_source(
            "bool CloseHistoryProvesExit(ulong positionIdentifier)"
        )
        for required in (
            "gPendingCloseOrderTicket != 0",
            "ResolveDealFromOrder(",
            "gPendingCloseOrderTicket, ORDER_TYPE_SELL",
            "DEAL_TYPE_SELL, DEAL_ENTRY_OUT",
            "HistoryDealSelect(gPendingCloseDealTicket)",
            "DEAL_POSITION_ID",
            "DEAL_TYPE_SELL",
            "DEAL_ENTRY_OUT",
            "DEAL_MAGIC",
            "DEAL_SYMBOL",
            "DEAL_VOLUME",
            "PendingCloseOrderIsTerminal()",
            "HistorySelectByPosition(positionIdentifier)",
            "cumulativeCloseVolume += dealVolume",
            "volumeEpsilon = MathMax(0.00000001, volumeStep * 0.000001)",
            "cumulativeCloseVolume + volumeEpsilon >= "
            "gPendingClosePreSendVolume",
        ):
            with self.subTest(close_history_evidence=required):
                self.assertIn(required, close_history_helper)
        safe_retry_helper = scoped_function_source(
            "bool SafeCloseRejectAllowsRetry(ulong resultOrder"
        )
        for required in (
            "if(resultOrder != 0 || resultDeal != 0) return(false);",
            "SelectManagedLongByIdentifier(positionIdentifier)",
            "MathAbs(currentVolume - previousVolume) <= volumeEpsilon",
        ):
            with self.subTest(safe_retry_guard=required):
                self.assertIn(required, safe_retry_helper)
        self.assertNotIn("retcode", safe_retry_helper)
        self.assertNotIn("TRADE_RETCODE_", safe_retry_helper)
        self.assertIn(
            "if(gCloseRetryCount >= MAX_CLOSE_RETRY_ATTEMPTS ||\n"
            "TimeCurrent() < gCloseRetryAfter) return(false);",
            close_helper,
        )
        self.assertIn(
            "gCloseRetryCount++;\n"
            "gCloseRetryAfter = TimeCurrent() + CLOSE_RETRY_BACKOFF_SECONDS;",
            close_helper,
        )
        self.assertEqual(
            close_helper.count(
                "SafeCloseRejectAllowsRetry(\n"
                "closeResult.order, closeResult.deal, positionIdentifier,\n"
                "positionVolume)"
            ),
            2,
        )

        risk_volume_helper = scoped_function_source(
            "double CalculateRiskVolume(double entryPrice"
        )
        for required in (
            "!MathIsValidNumber(riskMoney) || riskMoney <= 0",
            "!MathIsValidNumber(worstCaseLoss) || worstCaseLoss > riskMoney",
            "!MathIsValidNumber(marginRequired) || marginRequired <= 0",
            "!MathIsValidNumber(freeMargin) || freeMargin < 0",
            "if(marginRequired > freeMargin) return(0);",
        ):
            with self.subTest(finite_risk_input=required):
                self.assertIn(required, risk_volume_helper)

        on_init_start = scaffold.index("int OnInit()")
        on_init_end = scaffold.index("void OnDeinit", on_init_start)
        on_init = scaffold[on_init_start:on_init_end]
        weekly_failure_index = on_init.index(
            "if(gWeeklyMAHandle == INVALID_HANDLE)"
        )
        daily_release_index = on_init.index(
            "IndicatorRelease(gDailyMAHandle);",
            weekly_failure_index,
        )
        daily_reset_index = on_init.index(
            "gDailyMAHandle = INVALID_HANDLE;",
            daily_release_index,
        )
        init_failure_index = on_init.index(
            "return(INIT_FAILED);",
            daily_reset_index,
        )
        self.assertLess(weekly_failure_index, daily_release_index)
        self.assertLess(daily_release_index, daily_reset_index)
        self.assertLess(daily_reset_index, init_failure_index)

        selector_helper = scoped_function_source(
            "bool SelectManagedLongByIdentifier(ulong positionIdentifier)"
        )
        for required in (
            "PositionGetInteger(POSITION_IDENTIFIER)",
            "PositionGetString(POSITION_SYMBOL) != _Symbol",
            "PositionGetInteger(POSITION_MAGIC) != MagicNumber",
            "PositionGetInteger(POSITION_TYPE) != POSITION_TYPE_BUY",
            "gResolvedManagedTicket = currentTicket",
        ):
            with self.subTest(identifier_selector_guard=required):
                self.assertIn(required, selector_helper)

        reconcile_helper = scoped_function_source(
            "bool ReconcileManagedLong(ulong resultDealTicket"
        )
        for required in (
            "resultDealTicket",
            "HistoryDealSelect(resultDealTicket)",
            "DEAL_TYPE_BUY",
            "DEAL_ENTRY_IN",
            "DEAL_MAGIC",
            "DEAL_SYMBOL",
            "DEAL_POSITION_ID",
            "gPendingEntryPositionIdentifier = positionIdentifier",
            "SelectManagedLongByIdentifier(positionIdentifier)",
            "POSITION_VOLUME",
            "POSITION_PRICE_OPEN",
            "POSITION_SL",
            "POSITION_TP",
            "volumeEpsilon = MathMax(0.00000001, volumeStep * 0.000001)",
            "priceEpsilon = MathMax(0.00000001, priceTick * 0.000001)",
            "MathAbs(positionVolume - expectedVolume) > volumeEpsilon",
            "MathAbs(positionOpenPrice - dealPrice) > priceEpsilon",
            "MathAbs(positionStopLoss - expectedStopLoss) > priceEpsilon",
            "MathAbs(positionTakeProfit - expectedTakeProfit) > priceEpsilon",
            "OrderCalcProfit(ORDER_TYPE_BUY",
            "!MathIsValidNumber(actualRiskMoney) || actualRiskMoney <= 0",
            "actualRiskMoney > gPendingEntryRiskLimit",
        ):
            with self.subTest(reconciliation_field=required):
                self.assertIn(required, reconcile_helper)
        self.assertNotIn("resultOrderTicket", reconcile_helper)
        self.assertNotIn("positionTicket != resultOrderTicket", reconcile_helper)

        order_history_helper = scoped_function_source(
            "ulong ResolveDealFromOrder(ulong orderTicket, long expectedOrderType"
        )
        for required in (
            "HistoryOrderSelect(orderTicket)",
            "ORDER_STATE_FILLED",
            "expectedOrderType",
            "ORDER_MAGIC",
            "ORDER_SYMBOL",
            "ORDER_POSITION_ID",
            "HistorySelectByPosition(positionIdentifier)",
            "HistoryDealGetTicket(dealIndex)",
            "DEAL_ORDER) != orderTicket",
            "expectedDealType",
            "expectedDealEntry",
        ):
            with self.subTest(order_history_reconciliation=required):
                self.assertIn(required, order_history_helper)

        delayed_entry_helper = scoped_function_source(
            "bool ResolvePendingEntryWithoutDeal()"
        )
        for required in (
            "PositionsTotal()",
            "PositionGetTicket(positionIndex)",
            "PositionGetString(POSITION_SYMBOL) != _Symbol",
            "PositionGetInteger(POSITION_MAGIC) != MagicNumber",
            "PositionGetInteger(POSITION_TYPE) != POSITION_TYPE_BUY",
            "PositionGetInteger(POSITION_IDENTIFIER)",
            "discoveredIdentifier != positionIdentifier",
            "gPendingEntryPositionIdentifier = discoveredIdentifier",
        ):
            with self.subTest(delayed_entry_discovery=required):
                self.assertIn(required, delayed_entry_helper)

        for pending_state in (
            "ulong gPendingEntryOrderTicket",
            "ulong gPendingEntryDealTicket",
            "ulong gPendingEntryPositionIdentifier",
            "double gPendingEntryVolume",
            "double gPendingEntryStopLoss",
            "double gPendingEntryTakeProfit",
        ):
            with self.subTest(persisted_entry_evidence=pending_state):
                self.assertIn(pending_state, scaffold)

        compact_scaffold = " ".join(scaffold.split())
        entry_send_index = compact_scaffold.index(
            "OrderSend(entryRequest, entryResult)"
        )
        entry_unresolved_index = compact_scaffold.rindex(
            "gEntrySubmissionUnresolved = true", 0, entry_send_index
        )
        pending_volume_store_index = compact_scaffold.index(
            "gPendingEntryVolume = tradeVolume", entry_unresolved_index
        )
        pending_stop_store_index = compact_scaffold.index(
            "gPendingEntryStopLoss = stopLoss", pending_volume_store_index
        )
        pending_take_store_index = compact_scaffold.index(
            "gPendingEntryTakeProfit = takeProfit", pending_stop_store_index
        )
        pending_order_capture_index = compact_scaffold.index(
            "gPendingEntryOrderTicket = entryResult.order", entry_send_index
        )
        pending_deal_capture_index = compact_scaffold.index(
            "gPendingEntryDealTicket = entryResult.deal",
            pending_order_capture_index,
        )
        entry_done_index = compact_scaffold.index(
            "entryResult.retcode != TRADE_RETCODE_DONE",
            entry_send_index,
        )
        entry_order_index = compact_scaffold.index(
            "entryResult.order == 0",
            entry_done_index,
        )
        entry_deal_index = compact_scaffold.index(
            "entryResult.deal == 0",
            entry_order_index,
        )
        entry_volume_index = compact_scaffold.index(
            "MathAbs(entryResult.volume - tradeVolume) > entryVolumeEpsilon",
            entry_deal_index,
        )
        self.assertIn(
            "!MathIsValidNumber(entryResult.volume) || entryResult.volume <= 0",
            compact_scaffold[entry_deal_index:entry_volume_index],
        )
        self.assertIn(
            "!MathIsValidNumber(entryResult.price) || entryResult.price <= 0",
            compact_scaffold[entry_deal_index:entry_volume_index],
        )
        entry_reconcile_index = compact_scaffold.index(
            "ReconcileManagedLong(entryResult.deal, tradeVolume, stopLoss, "
            "takeProfit)",
            entry_volume_index,
        )
        entry_pending_index = compact_scaffold.index(
            'SetStatusComment("EntryPending"',
            entry_reconcile_index,
        )
        long_open_index = compact_scaffold.index(
            'SetStatusComment("LongOpen"',
            entry_pending_index,
        )
        self.assertLess(entry_unresolved_index, pending_volume_store_index)
        self.assertLess(pending_volume_store_index, pending_stop_store_index)
        self.assertLess(pending_stop_store_index, pending_take_store_index)
        self.assertLess(pending_take_store_index, entry_send_index)
        self.assertLess(entry_send_index, pending_order_capture_index)
        self.assertLess(pending_order_capture_index, pending_deal_capture_index)
        self.assertLess(pending_deal_capture_index, entry_done_index)
        self.assertLess(entry_send_index, entry_done_index)
        self.assertLess(entry_done_index, entry_order_index)
        self.assertLess(entry_order_index, entry_deal_index)
        self.assertLess(entry_deal_index, entry_volume_index)
        self.assertLess(entry_volume_index, entry_reconcile_index)
        self.assertLess(entry_reconcile_index, entry_pending_index)
        self.assertLess(entry_pending_index, long_open_index)
        self.assertNotIn("ReconcileManagedLong(entryResult.order", compact_scaffold)

        pending_entry_start = on_tick.index("if(gEntrySubmissionUnresolved)")
        pending_entry_block = on_tick[pending_entry_start:pending_close_start]
        pending_order_resolve_index = pending_entry_block.index(
            "ResolveDealFromOrder("
        )
        delayed_position_resolve_index = pending_entry_block.index(
            "ResolvePendingEntryWithoutDeal()", pending_order_resolve_index
        )
        pending_deal_reconcile_index = pending_entry_block.index(
            "ReconcileManagedLong(gPendingEntryDealTicket, gPendingEntryVolume",
            delayed_position_resolve_index,
        )
        self.assertIn("gPendingEntryOrderTicket", pending_entry_block)
        self.assertIn(
            "gPendingEntryOrderTicket, ORDER_TYPE_BUY,",
            pending_entry_block,
        )
        self.assertIn("DEAL_TYPE_BUY, DEAL_ENTRY_IN", pending_entry_block)
        self.assertIn(
            "if(resolvedDeal != 0) gPendingEntryDealTicket = resolvedDeal;",
            pending_entry_block,
        )
        self.assertIn(
            "gPendingCloseIdentifier = mismatchIdentifier",
            pending_entry_block,
        )
        self.assertIn("gExitModeActive = true", pending_entry_block)
        self.assertLess(pending_order_resolve_index, delayed_position_resolve_index)
        self.assertLess(delayed_position_resolve_index, pending_deal_reconcile_index)
        self.assertNotIn("if(entryReconcileBlocked) return;", pending_entry_block)

        safe_no_execution_compact = " ".join(safe_no_execution_helper.split())
        self.assertNotIn("TRADE_RETCODE_PLACED", safe_no_execution_compact)
        unresolved_failure_start = compact_scaffold.index(
            "if(!buySucceeded || entryResult.retcode != TRADE_RETCODE_DONE",
            entry_send_index,
        )
        unresolved_failure_end = compact_scaffold.index(
            "double entryVolumeEpsilon", unresolved_failure_start
        )
        unresolved_failure_block = compact_scaffold[
            unresolved_failure_start:unresolved_failure_end
        ]
        self.assertIn(
            "if(entryResult.order == 0 && entryResult.deal == 0 && "
            "IsSafeNoExecutionTradeRetcode(entryResult.retcode)) "
            "ClearPendingEntryState();",
            unresolved_failure_block,
        )

        manifest = self.runner.build_compact_ea_source_manifest(
            scaffold,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest=spec_digest,
            source_digest=hashlib.sha256(scaffold.encode("utf-8")).hexdigest(),
            target_platform="mt5",
        )
        self.assertTrue(manifest["complete"], manifest)
        self.assertTrue(all(manifest["checks"].values()), manifest)
        self.assertTrue(manifest["checks"]["referenceParametersAbsent"], manifest)
        self.assertTrue(manifest["checks"]["positionCapExecution"], manifest)

        mission_guard_mutations = {
            "hedging_account_operator_required": (
                "if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != "
                "ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)\n"
                "return(INIT_FAILED);",
                "if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) == "
                "ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)\n"
                "return(INIT_FAILED);",
            ),
            "hedging_account_mode_required": (
                "if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != "
                "ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)\n"
                "return(INIT_FAILED);",
                "if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != "
                "ACCOUNT_MARGIN_MODE_RETAIL_NETTING)\n"
                "return(INIT_FAILED);",
            ),
            "hedging_account_failure_required": (
                "if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != "
                "ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)\n"
                "return(INIT_FAILED);",
                "if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != "
                "ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)\n"
                "return(INIT_SUCCEEDED);",
            ),
            "hedging_account_guard_required": (
                "if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != "
                "ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)\n"
                "return(INIT_FAILED);",
                "",
            ),
            "hedging_account_comment_spoof_rejected": (
                "if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != "
                "ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)\n"
                "return(INIT_FAILED);",
                "/* if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != "
                "ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)\n"
                "return(INIT_FAILED); */",
            ),
            "position_reselection": (
                "if(gCloseRetryCount >= MAX_CLOSE_RETRY_ATTEMPTS ||\n"
                "TimeCurrent() < gCloseRetryAfter) return(false);\n"
                "if(!SelectManagedLongByIdentifier(positionIdentifier)) {",
                "if(gCloseRetryCount >= MAX_CLOSE_RETRY_ATTEMPTS ||\n"
                "TimeCurrent() < gCloseRetryAfter) return(false);\n"
                "if(false) {",
            ),
            "symbol_scope": (
                "if(PositionGetString(POSITION_SYMBOL) != _Symbol) return(false);",
                "if(false) return(false);",
            ),
            "magic_scope": (
                "if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) return(false);",
                "if(false) return(false);",
            ),
            "long_type_scope": (
                "if(PositionGetInteger(POSITION_TYPE) != POSITION_TYPE_BUY) return(false);",
                "if(false) return(false);",
            ),
            "close_volume_from_position": (
                "double positionVolume = PositionGetDouble(POSITION_VOLUME);\n"
                "if(!MathIsValidNumber(positionVolume) || positionVolume <= 0) return(false);",
                "double positionVolume = 0.10;\n"
                "if(!MathIsValidNumber(positionVolume) || positionVolume <= 0) return(false);",
            ),
            "fundamental_gate": (
                "if(!FundamentalCriteriaConfirmed) return;",
                "",
            ),
            "margin_gate": (
                "OrderCalcMargin(ORDER_TYPE_BUY, _Symbol, volume, entryPrice, marginRequired)",
                "MissingMarginCheck(ORDER_TYPE_BUY, _Symbol, volume, entryPrice, marginRequired)",
            ),
            "risk_percent_hard_cap": (
                "const double MAX_RISK_PERCENT = 2.0;",
                "const double MAX_RISK_PERCENT = 100.0;",
            ),
            "requested_stop_not_expanded": (
                "if(brokerFloor > requestedStopDistance) return;",
                "if(brokerFloor > requestedStopDistance) requestedStopDistance = brokerFloor;",
            ),
            "requested_stop_distance_bound": (
                "actualStopDistance < brokerFloor || actualStopDistance > requestedStopDistance",
                "actualStopDistance < brokerFloor",
            ),
            "calculated_stop_distance_bound": (
                "if(stopDistance > requestedStopDistance) return;",
                "if(stopDistance > requestedStopDistance) {}",
            ),
            "absolute_eight_percent_stop_bound": (
                "actualStopDistance > maximumStopDistance) return;",
                "actualStopDistance > maximumStopDistance) {}",
            ),
            "zero_stop_floor_is_valid": (
                "brokerStopFloor < 0",
                "brokerStopFloor <= 0",
            ),
            "zero_freeze_floor_is_valid": (
                "brokerFreezeFloor < 0",
                "brokerFreezeFloor <= 0",
            ),
            "stop_floor_must_be_finite": (
                "if(!MathIsValidNumber(brokerStopFloor) || brokerStopFloor < 0) return;",
                "if(brokerStopFloor < 0) return;",
            ),
            "freeze_floor_must_be_finite": (
                "if(!MathIsValidNumber(brokerFreezeFloor) || brokerFreezeFloor < 0) return;",
                "if(brokerFreezeFloor < 0) return;",
            ),
            "entry_filling_uses_resolved_mode": (
                "entryRequest.type_filling = (ENUM_ORDER_TYPE_FILLING)entryFillingMode;",
                "entryRequest.type_filling = ORDER_FILLING_RETURN;",
            ),
            "entry_filling_requires_ioc_fallback": (
                "if((fillingFlags & SYMBOL_FILLING_IOC) == SYMBOL_FILLING_IOC)\n"
                "return((int)ORDER_FILLING_IOC);\n"
                "return(-1);",
                "return(-1);",
            ),
            "close_filling_uses_resolved_mode": (
                "closeRequest.type_filling = (ENUM_ORDER_TYPE_FILLING)closeFillingMode;",
                "closeRequest.type_filling = ORDER_FILLING_RETURN;",
            ),
            "close_filling_rejects_return": (
                "if((fillingFlags & SYMBOL_FILLING_IOC) == SYMBOL_FILLING_IOC)\n"
                "return((int)ORDER_FILLING_IOC);\n"
                "return(-1);",
                "if((fillingFlags & SYMBOL_FILLING_IOC) == SYMBOL_FILLING_IOC)\n"
                "return((int)ORDER_FILLING_IOC);\n"
                "return((int)ORDER_FILLING_RETURN);",
            ),
            "bounded_close_retry": (
                "const int MAX_CLOSE_RETRY_ATTEMPTS = 3;",
                "const int MAX_CLOSE_RETRY_ATTEMPTS = 30;",
            ),
            "close_retry_backoff_gate": (
                "if(gCloseRetryCount >= MAX_CLOSE_RETRY_ATTEMPTS ||\n"
                "TimeCurrent() < gCloseRetryAfter) return(false);",
                "if(gCloseRetryCount >= MAX_CLOSE_RETRY_ATTEMPTS) return(false);",
            ),
            "close_retry_deadline_after_send": (
                "gCloseRetryCount++;\n"
                "gCloseRetryAfter = TimeCurrent() + CLOSE_RETRY_BACKOFF_SECONDS;",
                "gCloseRetryCount++;\n"
                "if(false) gCloseRetryAfter = TimeCurrent() + CLOSE_RETRY_BACKOFF_SECONDS;",
            ),
            "close_retry_ignores_retcode_whitelists": (
                "if(resultOrder != 0 || resultDeal != 0) return(false);",
                "if(!IsSafeNoExecutionTradeRetcode(TRADE_RETCODE_TIMEOUT)) return(false);\n"
                "if(resultOrder != 0 || resultDeal != 0) return(false);",
            ),
            "close_retry_requires_zero_result_identity": (
                "if(resultOrder != 0 || resultDeal != 0) return(false);",
                "if(false) return(false);",
            ),
            "both_close_failure_paths_require_state_proof": (
                "if(SafeCloseRejectAllowsRetry(\n"
                "closeResult.order, closeResult.deal, positionIdentifier,\n"
                "positionVolume))",
                "if(false)",
            ),
            "pending_identifier_reconciliation": (
                "if(!SelectManagedLongByIdentifier(gPendingCloseIdentifier)) {\n"
                "if(gPositionLookupReliable && !gPositionIdentifierVisible &&\n"
                "CloseHistoryProvesExit(gPendingCloseIdentifier)) {",
                "if(!SelectManagedLongByIdentifier(gPendingCloseIdentifier)) {\n"
                "if(gPositionLookupReliable && !gPositionIdentifierVisible) {",
            ),
            "close_order_history_consumed": (
                "gPendingCloseDealTicket = ResolveDealFromOrder(\n"
                "gPendingCloseOrderTicket, ORDER_TYPE_SELL,\n"
                "DEAL_TYPE_SELL, DEAL_ENTRY_OUT);",
                "gPendingCloseDealTicket = 0;",
            ),
            "close_order_evidence_persisted": (
                "if(closeResult.order != 0) gPendingCloseOrderTicket = closeResult.order;",
                "if(closeResult.order != 0) gPendingCloseOrderTicket = 0;",
            ),
            "close_deal_evidence_persisted": (
                "if(closeResult.deal != 0) gPendingCloseDealTicket = closeResult.deal;",
                "if(closeResult.deal != 0) gPendingCloseDealTicket = 0;",
            ),
            "ambiguous_close_requires_monotonic_progress": (
                "observedVolume < gPendingClosePreSendVolume - observedEpsilon",
                "observedVolume <= gPendingClosePreSendVolume",
            ),
            "terminal_order_before_ambiguous_retry": (
                "if(PendingCloseOrderIsTerminal() &&\n"
                "MathIsValidNumber(observedVolume)",
                "if(MathIsValidNumber(observedVolume)",
            ),
            "ambiguous_progress_resets_retry_count": (
                "observedVolume < gPendingClosePreSendVolume - observedEpsilon) {\n"
                "gCloseRetryCount = 0;",
                "observedVolume < gPendingClosePreSendVolume - observedEpsilon) {\n"
                "if(false) gCloseRetryCount = 0;",
            ),
            "ambiguous_progress_resets_retry_backoff": (
                "gCloseRetryCount = 0;\n"
                "gCloseRetryAfter = 0;\n"
                "gCloseRetryAuthorized = true;",
                "gCloseRetryCount = 0;\n"
                "if(false) gCloseRetryAfter = 0;\n"
                "gCloseRetryAuthorized = true;",
            ),
            "active_close_order_is_not_terminal": (
                "if(activeOrderTicket == gPendingCloseOrderTicket) return(false);",
                "if(activeOrderTicket == gPendingCloseOrderTicket) continue;",
            ),
            "close_history_requires_terminal_order": (
                "if(!PendingCloseOrderIsTerminal()) return(false);",
                "if(false) return(false);",
            ),
            "close_history_requires_cumulative_coverage": (
                "return(MathIsValidNumber(cumulativeCloseVolume) &&\n"
                "cumulativeCloseVolume + volumeEpsilon >= gPendingClosePreSendVolume);",
                "return(closeVolume > 0);",
            ),
            "managed_identifier_not_ticket": (
                "gPendingCloseIdentifier = managedIdentifier;",
                "gPendingCloseIdentifier = managedTicket;",
            ),
            "drain_all_managed_longs_cross_tick": (
                "SetStatusComment(\"ExitSignal\", SymbolInfoInteger(_Symbol, SYMBOL_SPREAD));\n"
                "gExitModeActive = true;\n"
                "gPendingCloseTicket = managedTicket;",
                "SetStatusComment(\"ExitSignal\", SymbolInfoInteger(_Symbol, SYMBOL_SPREAD));\n"
                "gExitModeActive = false;\n"
                "gPendingCloseTicket = managedTicket;",
            ),
            "remaining_position_verification": (
                "double remainingVolume = PositionGetDouble(POSITION_VOLUME);",
                "double remainingVolume = 0;",
            ),
            "partial_close_must_reduce_volume": (
                "if(partialRemainingVolume >= positionVolume) return(false);",
                "if(partialRemainingVolume >= positionVolume) {}",
            ),
            "terminal_order_before_partial_retry": (
                "if(PendingCloseOrderIsTerminal()) {\n"
                "gCloseRetryAuthorized = true;\n"
                "gCloseRetryCount = 0;\n"
                "gCloseRetryAfter = 0;\n"
                "}",
                "if(true) {\n"
                "gCloseRetryAuthorized = true;\n"
                "gCloseRetryCount = 0;\n"
                "gCloseRetryAfter = 0;\n"
                "}",
            ),
            "terminal_order_before_remaining_retry": (
                "if(remainingVolume >= positionVolume) return(false);\n"
                "if(PendingCloseOrderIsTerminal()) {\n"
                "gCloseRetryAuthorized = true;\n"
                "gCloseRetryCount = 0;\n"
                "gCloseRetryAfter = 0;\n"
                "}",
                "if(remainingVolume >= positionVolume) return(false);\n"
                "if(true) {\n"
                "gCloseRetryAuthorized = true;\n"
                "gCloseRetryCount = 0;\n"
                "gCloseRetryAfter = 0;\n"
                "}",
            ),
            "ambiguous_placed_close_not_retryable": (
                "retcode == TRADE_RETCODE_PRICE_OFF);",
                "retcode == TRADE_RETCODE_PRICE_OFF ||\n"
                "         retcode == TRADE_RETCODE_PLACED);",
            ),
            "close_order_exists_not_retryable": (
                "retcode == TRADE_RETCODE_PRICE_OFF);",
                "retcode == TRADE_RETCODE_PRICE_OFF ||\n"
                "         retcode == TRADE_RETCODE_CLOSE_ORDER_EXIST);",
            ),
            "close_done_only": (
                "if(remainingVolume >= positionVolume) return(false);\n"
                "if(PendingCloseOrderIsTerminal()) {\n"
                "gCloseRetryAuthorized = true;\n"
                "gCloseRetryCount = 0;\n"
                "gCloseRetryAfter = 0;\n"
                "}\n"
                "return(false);",
                "if(remainingVolume >= positionVolume) return(false);\n"
                "if(PendingCloseOrderIsTerminal()) {\n"
                "gCloseRetryAuthorized = true;\n"
                "gCloseRetryCount = 0;\n"
                "gCloseRetryAfter = 0;\n"
                "}\n"
                "return(true);",
            ),
            "init_handle_cleanup": (
                "IndicatorRelease(gDailyMAHandle);\n"
                "gDailyMAHandle = INVALID_HANDLE;\n"
                "return(INIT_FAILED);",
                "return(INIT_FAILED);",
            ),
            "entry_done_only": (
                "entryResult.retcode != TRADE_RETCODE_DONE",
                "entryResult.retcode != TRADE_RETCODE_DONE_PARTIAL",
            ),
            "entry_result_identity": (
                "entryResult.order == 0",
                "false",
            ),
            "entry_deal_identity": (
                "entryResult.deal == 0",
                "false",
            ),
            "entry_result_volume": (
                "MathAbs(entryResult.volume - tradeVolume) > entryVolumeEpsilon",
                "false",
            ),
            "entry_result_price": (
                "!MathIsValidNumber(entryResult.price) || entryResult.price <= 0",
                "false",
            ),
            "margin_requirement_must_be_finite": (
                "if(!MathIsValidNumber(marginRequired) || marginRequired <= 0) return(0);",
                "if(marginRequired <= 0) return(0);",
            ),
            "free_margin_must_be_finite": (
                "if(!MathIsValidNumber(freeMargin) || freeMargin < 0) return(0);",
                "if(freeMargin < 0) return(0);",
            ),
            "entry_state_reconciliation": (
                "if(!ReconcileManagedLong(entryResult.deal, tradeVolume,\n"
                "stopLoss, takeProfit))",
                "if(false)",
            ),
            "entry_reconcile_uses_deal_not_order": (
                "ReconcileManagedLong(entryResult.deal, tradeVolume,",
                "ReconcileManagedLong(entryResult.order, tradeVolume,",
            ),
            "deal_position_identifier": (
                "resultDealTicket, DEAL_POSITION_ID);",
                "resultDealTicket, DEAL_ORDER);",
            ),
            "reconciled_position_risk_limit": (
                "gPendingEntryRiskLimit <= 0 || actualRiskMoney > gPendingEntryRiskLimit)",
                "gPendingEntryRiskLimit <= 0)",
            ),
            "old_ticket_equality_rejected": (
                "if(!SelectManagedLongByIdentifier(positionIdentifier)) return(false);",
                "if(gResolvedManagedTicket != resultDealTicket) return(false);",
            ),
            "pending_order_history_consumed": (
                "ulong resolvedDeal = ResolveDealFromOrder(\n"
                "gPendingEntryOrderTicket, ORDER_TYPE_BUY,\n"
                "DEAL_TYPE_BUY, DEAL_ENTRY_IN);",
                "ulong resolvedDeal = 0;",
            ),
            "delayed_entry_without_result_is_discovered": (
                "if(gPendingEntryDealTicket == 0)\n"
                "ResolvePendingEntryWithoutDeal();",
                "if(gPendingEntryDealTicket == 0) {}",
            ),
            "delayed_entry_identifier_is_persisted": (
                "gPendingEntryPositionIdentifier = discoveredIdentifier;",
                "gPendingEntryPositionIdentifier = 0;",
            ),
            "pending_order_evidence_persisted": (
                "if(entryResult.order != 0) gPendingEntryOrderTicket = entryResult.order;",
                "if(entryResult.order != 0) gPendingEntryOrderTicket = 0;",
            ),
            "pending_deal_evidence_persisted": (
                "if(entryResult.deal != 0) gPendingEntryDealTicket = entryResult.deal;",
                "if(entryResult.deal != 0) gPendingEntryDealTicket = 0;",
            ),
            "pending_entry_gate_after_exit_management": (
                "if(gPendingCloseIdentifier != 0) {",
                "if(entryReconcileBlocked) return;\n"
                "  if(gPendingCloseIdentifier != 0) {",
            ),
        }
        with mock.patch.object(
            self.runner,
            "EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST",
            brief_digest,
        ):
            for label, (required, replacement) in mission_guard_mutations.items():
                with self.subTest(attestation=label):
                    mutated = scaffold.replace(required, replacement, 1)
                    self.assertNotEqual(mutated, scaffold)
                    self.assertFalse(
                        self.runner._ea_factory_can_slim_mt5_scaffold_meets_mission(
                            mutated
                        )
                    )

        # A raw SELL request is a close only when it is explicitly bound to a
        # nonzero position.  Otherwise it is classified as a prohibited Short
        # entry and invalidates the immutable MT5 manifest.
        close_request_mutations = {
            "zero_position": (
                "closeRequest.position = positionTicket;",
                "closeRequest.position = 0;",
            ),
            "missing_position": (
                "closeRequest.position = positionTicket;",
                "",
            ),
            "non_deal_action": (
                "closeRequest.action = TRADE_ACTION_DEAL;",
                "closeRequest.action = TRADE_ACTION_PENDING;",
            ),
            "uninvoked_close": (
                "CloseManagedLong(gPendingCloseIdentifier)",
                "NoClose(gPendingCloseIdentifier)",
            ),
        }
        for label, (required, replacement) in close_request_mutations.items():
            with self.subTest(manifest=label):
                mutated = scaffold.replace(required, replacement, 1)
                self.assertNotEqual(mutated, scaffold)
                mutated_manifest = self.runner.build_compact_ea_source_manifest(
                    mutated,
                    strategy_brief=brief,
                    strategy_brief_digest=brief_digest,
                    strategy_spec_digest=spec_digest,
                    source_digest=hashlib.sha256(
                        mutated.encode("utf-8")
                    ).hexdigest(),
                    target_platform="mt5",
                )
                self.assertFalse(mutated_manifest["complete"], mutated_manifest)
                self.assertFalse(
                    mutated_manifest["checks"]["exitAndProtectionExecution"],
                    mutated_manifest,
                )

    def test_can_slim_mt5_startup_recovery_gate_mutations_fail_closed(self) -> None:
        """The certified MT5 fallback must recover restart state fail-closed."""

        brief = self._can_slim_legacy_brief()
        brief_digest = self.runner.compute_strategy_brief_digest(brief)
        spec_digest = "7" * 64
        with mock.patch.object(
            self.runner,
            "EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST",
            brief_digest,
        ):
            scaffold = self.runner._build_ea_factory_source_semantic_repair_scaffold(
                brief,
                strategy_brief_digest=brief_digest,
                strategy_spec_digest=spec_digest,
                target_platform="mt5",
            )
            self.assertTrue(scaffold)
            self.assertTrue(
                self.runner._ea_factory_can_slim_mt5_scaffold_meets_mission(
                    scaffold
                )
            )

            def mutate_startup_scope(required: str, replacement: str) -> str:
                signature = "bool ValidateStartupManagedInventory()"
                start = scaffold.index(signature)
                opening = scaffold.index("{", start)
                depth = 0
                end = -1
                for cursor in range(opening, len(scaffold)):
                    if scaffold[cursor] == "{":
                        depth += 1
                    elif scaffold[cursor] == "}":
                        depth -= 1
                        if depth == 0:
                            end = cursor + 1
                            break
                self.assertGreater(end, opening)
                startup_scope = scaffold[start:end]
                self.assertIn(required, startup_scope)
                mutated_scope = startup_scope.replace(required, replacement, 1)
                self.assertNotEqual(mutated_scope, startup_scope)
                return scaffold[:start] + mutated_scope + scaffold[end:]

            startup_scope_mutations = {
                "active_symbol_magic_order_quarantine": (
                    "if(OrderGetString(ORDER_SYMBOL) == _Symbol &&\n"
                    "OrderGetInteger(ORDER_MAGIC) == MagicNumber) return(false);",
                    "if(OrderGetString(ORDER_SYMBOL) == _Symbol &&\n"
                    "OrderGetInteger(ORDER_MAGIC) == MagicNumber) continue;",
                ),
                "order_inventory_scan_must_be_reliable": (
                    "if(orderTicket == 0) return(false);",
                    "if(orderTicket == 0) continue;",
                ),
                "position_inventory_ticket_must_be_reliable": (
                    "if(positionTicket == 0) return(false);",
                    "if(positionTicket == 0) continue;",
                ),
                "position_inventory_reselection_must_be_reliable": (
                    "if(!PositionSelectByTicket(positionTicket)) return(false);",
                    "if(!PositionSelectByTicket(positionTicket)) continue;",
                ),
                "startup_inventory_is_buy_only": (
                    "if(PositionGetInteger(POSITION_TYPE) != POSITION_TYPE_BUY) return(false);",
                    "if(PositionGetInteger(POSITION_TYPE) != POSITION_TYPE_BUY) continue;",
                ),
                "startup_inventory_requires_stable_identifier": (
                    "if(identifier == 0 || !MathIsValidNumber(volume) || volume <= 0 ||",
                    "if(false || !MathIsValidNumber(volume) || volume <= 0 ||",
                ),
                "startup_inventory_volume_is_finite_and_positive": (
                    "!MathIsValidNumber(volume) || volume <= 0",
                    "volume < 0",
                ),
                "startup_inventory_open_price_is_finite_and_positive": (
                    "!MathIsValidNumber(openPrice) || openPrice <= 0",
                    "openPrice < 0",
                ),
                "startup_inventory_stop_is_finite_positive_and_below_open": (
                    "!MathIsValidNumber(stopLoss) || stopLoss <= 0 || stopLoss >= openPrice",
                    "stopLoss >= openPrice",
                ),
                "startup_inventory_target_is_finite_and_above_open": (
                    "!MathIsValidNumber(takeProfit) || takeProfit <= openPrice",
                    "takeProfit <= openPrice",
                ),
                "startup_inventory_stop_percent_cap": (
                    "stopPercent > MathMin(8.0, InpStopLossPercent)",
                    "stopPercent > 100.0",
                ),
                "startup_inventory_order_calc_profit_proof": (
                    "if(!OrderCalcProfit(ORDER_TYPE_BUY, _Symbol, volume,\n"
                    "openPrice, stopLoss, stopProfit)) return(false);",
                    "stopProfit = -1.0;",
                ),
                "startup_inventory_risk_cap": (
                    "riskMoney > riskLimit",
                    "riskMoney < 0",
                ),
                "startup_inventory_position_count_cap": (
                    "if(scopedPositions > MaxOpenPositionsPerSymbolMagic) return(false);",
                    "if(false) return(false);",
                ),
            }
            for label, (required, replacement) in startup_scope_mutations.items():
                with self.subTest(startup_scope=label):
                    mutated = mutate_startup_scope(required, replacement)
                    self.assertFalse(
                        self.runner._ea_factory_can_slim_mt5_scaffold_meets_mission(
                            mutated
                        )
                    )

            startup_gate = "bool startupOk = ValidateStartupManagedInventory();\n"
            startup_hold = (
                "if(!startupOk) { SetStatusComment(\"RecoveryAttention\", "
                "statusSpread); return; }\n"
            )
            first_attach_gate = (
                "if(lastBar == 0) { lastBar = currentBar; "
                "if(startupOk) return; }\n"
            )
            self.assertIn(startup_gate, scaffold)
            self.assertIn(startup_hold, scaffold)
            self.assertIn(first_attach_gate, scaffold)
            self.assertNotIn("gStartupInventoryChecked", scaffold)
            gate_mutations = {
                "startup_inventory_call_cannot_be_skipped": scaffold.replace(
                    startup_gate,
                    "bool startupOk = true;\n",
                    1,
                ),
                "startup_inventory_hold_cannot_be_removed": scaffold.replace(
                    startup_hold,
                    "",
                    1,
                ),
                "startup_inventory_hold_cannot_be_inverted": scaffold.replace(
                    startup_hold,
                    startup_hold.replace("if(!startupOk)", "if(startupOk)"),
                    1,
                ),
                "startup_inventory_hold_comment_spoof_rejected": scaffold.replace(
                    startup_hold,
                    "/* " + startup_hold.rstrip() + " */\n",
                    1,
                ),
                "startup_inventory_first_attach_must_manage_invalid_state": (
                    scaffold.replace(
                        first_attach_gate,
                        "if(lastBar == 0) { lastBar = currentBar; return; }\n",
                        1,
                    )
                ),
                "startup_inventory_hold_after_management": scaffold.replace(
                    startup_hold,
                    "",
                    1,
                ).replace(
                    "// Manage existing Longs before any entry-only external "
                    "or broker gate.\n",
                    startup_hold
                    + "// Manage existing Longs before any entry-only external "
                    "or broker gate.\n",
                    1,
                ),
            }
            for label, anchor in (
                ("startup_gate_precedes_pending_entry", "if(gEntrySubmissionUnresolved) {\n"),
                ("startup_gate_precedes_pending_close", "if(gPendingCloseIdentifier != 0) {\n"),
                ("startup_gate_precedes_new_bar", "if(currentBar == lastBar) return;\n"),
            ):
                self.assertIn(anchor, scaffold)
                without_gate = scaffold.replace(startup_gate, "", 1)
                gate_mutations[label] = without_gate.replace(
                    anchor,
                    anchor + startup_gate,
                    1,
                )
            for label, mutated in gate_mutations.items():
                with self.subTest(startup_gate=label):
                    self.assertNotEqual(mutated, scaffold)
                    self.assertFalse(
                        self.runner._ea_factory_can_slim_mt5_scaffold_meets_mission(
                            mutated
                        )
                    )

    def test_can_slim_mt5_scaffold_rejects_unreviewed_profiles(self) -> None:
        brief = self._can_slim_legacy_brief()
        brief_digest = self.runner.compute_strategy_brief_digest(brief)
        spec_digest = "9" * 64

        mixed = dict(brief)
        mixed["orderExecution"] = mixed["orderExecution"].replace(
            "compact-ea-atr-risk-v1",
            "compact-ea-safe-inputs-v2",
        )
        different_system = dict(brief)
        different_system["systemName"] = "Different long-only breakout system"

        candidates = {
            "mixed_policy": mixed,
            "different_system": different_system,
        }
        for label, candidate in candidates.items():
            candidate_digest = self.runner.compute_strategy_brief_digest(candidate)
            with self.subTest(label=label), mock.patch.object(
                self.runner,
                "EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST",
                candidate_digest,
            ):
                self.assertEqual(
                    self.runner._build_ea_factory_source_semantic_repair_scaffold(
                        candidate,
                        strategy_brief_digest=candidate_digest,
                        strategy_spec_digest=spec_digest,
                        target_platform="mt5",
                    ),
                    "",
                )

        with mock.patch.object(
            self.runner,
            "EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST",
            brief_digest,
        ):
            self.assertEqual(
                self.runner._build_ea_factory_source_semantic_repair_scaffold(
                    brief,
                    strategy_brief_digest="0" * 64,
                    strategy_spec_digest=spec_digest,
                    target_platform="mt5",
                ),
                "",
            )
            self.assertEqual(
                self.runner._build_ea_factory_source_semantic_repair_scaffold(
                    brief,
                    strategy_brief_digest=brief_digest,
                    strategy_spec_digest=spec_digest,
                    target_platform="tradingview",
                ),
                "",
            )

    def test_can_slim_mt5_fresh_spec_scaffold_passes_full_preflight(self) -> None:
        brief = dict(self._can_slim_legacy_brief())
        brief["moneyManagement"] += (
            " และนับสถานะเปิดกับคำสั่งรอของ Symbol+Magic เดียวกัน"
        )
        brief = self.runner.normalize_strategy_brief(brief)
        brief_digest = self.runner.compute_strategy_brief_digest(brief)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source_root, prompt, _record_digest, spec_digest = (
                self._factory_fixture(
                    root,
                    platform="mt5",
                    strategy_brief=brief,
                )
            )
            self.assertNotEqual(
                spec_digest,
                self.runner.EA_FACTORY_CAN_SLIM_CERTIFIED_SPEC_DIGEST,
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
            ):
                scaffold = (
                    self.runner._build_ea_factory_can_slim_mt5_source_semantic_repair_scaffold(
                        brief,
                        strategy_brief_digest=brief_digest,
                        strategy_spec_digest=spec_digest,
                        target_platform="mt5",
                    )
                )
                self.assertTrue(scaffold)
                self.runner.preflight_ea_factory_source_semantics(
                    json.dumps({
                        "fileName": "FreshCanSlimMT5.mq5",
                        "content": scaffold,
                    }),
                    prompt,
                    relative,
                )

            self.assertEqual(
                {item.name for item in source_root.iterdir()},
                {"strategy-spec-v01.json"},
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

    def test_linda_holy_grail_scaffold_passes_every_immutable_gate(self) -> None:
        self.assertEqual(
            self.runner.EA_FACTORY_LINDA_HOLY_GRAIL_CERTIFIED_BRIEF_DIGEST,
            "877de2f4dd4e6081fe7ea886eca309099da4e9c2134f433d9cd079f1b1f16a42",
        )
        legacy_brief = self.runner.normalize_strategy_brief(
            load_linda_legacy_brief()
        )
        self.assertEqual(
            self.runner.compute_strategy_brief_digest(legacy_brief),
            self.runner.EA_FACTORY_LINDA_HOLY_GRAIL_LEGACY_BRIEF_DIGEST,
        )
        brief = self._linda_holy_grail_certified_brief()
        brief_digest = self.runner.compute_strategy_brief_digest(brief)
        self.assertEqual(
            brief_digest,
            self.runner.EA_FACTORY_LINDA_HOLY_GRAIL_CERTIFIED_BRIEF_DIGEST,
        )
        self.assertIn(
            self.runner.EA_FACTORY_LINDA_HOLY_GRAIL_DIRECTION_RULE,
            brief["entryRules"],
        )
        spec_digest = "6" * 64
        scaffold = self.runner._build_ea_factory_source_semantic_repair_scaffold(
            brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest=spec_digest,
            target_platform="mt4",
        )
        attested = self.runner._ea_factory_linda_holy_grail_scaffold_meets_mission(
            scaffold
        )
        profile = self.runner._ea_factory_certified_scaffold_profile(
            brief_digest,
            scaffold,
        )

        self.assertTrue(scaffold)
        self.assertTrue(attested)
        self.assertEqual(
            profile,
            self.runner.EA_FACTORY_LINDA_HOLY_GRAIL_CERTIFIED_PROFILE_VERSION,
        )
        self.assertLessEqual(
            len(scaffold),
            self.runner.EA_FACTORY_SEMANTIC_REPAIR_SCAFFOLD_MAX_CHARS,
        )
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
        self.assertIn("ADXPeriod = 14", scaffold)
        self.assertIn("SMAPeriod = 20", scaffold)
        self.assertIn("OrderDelete(OrderTicket())", scaffold)
        self.assertIn("OrderModify(OrderTicket()", scaffold)
        self.assertIn("CERTIFIED_SELL_STOP_ORDER = 5", scaffold)
        self.assertIn("iTime(Symbol(), timeframe, 0)", scaffold)
        self.assertNotIn("Time[0]", scaffold)
        self.assertIn(
            "MODE_MAIN, SignalBarShift + 1)",
            scaffold,
        )
        self.assertIn(
            "MODE_SMA, PRICE_CLOSE, SignalBarShift + 1)",
            scaffold,
        )
        self.assertIn(
            'CERTIFIED_DIRECTION_RULE = "IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT:SMA20_SLOPE"',
            scaffold,
        )
        self.assertIn(
            "bool directionalUptrend = smaCurrent > smaPrevious;",
            scaffold,
        )
        self.assertIn(
            "bool directionalDowntrend = smaCurrent < smaPrevious;",
            scaffold,
        )
        self.assertIn(
            "bool longPullback = directionalUptrend && signalClose > smaCurrent",
            scaffold,
        )
        self.assertIn(
            "bool shortPullback = directionalDowntrend && signalClose < smaCurrent",
            scaffold,
        )
        self.assertIn("input int PendingExpirationDays = 3;", scaffold)
        self.assertIn("PendingExpirationDays * 86400", scaffold)
        self.assertIn(
            "if(PendingExpirationDays > 3650) return(INIT_PARAMETERS_INCORRECT);",
            scaffold,
        )
        self.assertIn(
            "long expirationSeconds = (long)PendingExpirationDays * 86400;",
            scaffold,
        )
        self.assertNotIn("PendingExpirationBars", scaffold)
        self.assertNotIn("PeriodSeconds(timeframe)", scaffold)
        self.assertIn("MagicNumber <= 0", scaffold)
        self.assertIn(
            "int marginSide = signal == OP_BUYSTOP ? OP_BUY : OP_SELL;",
            scaffold,
        )
        self.assertIn(
            "gOrderLot = ValidateFixedLot(FixedLot, marginSide);",
            scaffold,
        )
        self.assertIn(
            "gOrderLot = CalculateRiskLot(entryPrice, stopLoss, currentSpread,",
            scaffold,
        )
        risk_helper = scaffold.split("double CalculateRiskLot(", 1)[1].split(
            "\n}\n\nint ManageExistingOrders", 1
        )[0]
        self.assertNotIn("FixedLot", risk_helper)
        self.assertIn(
            "double executionCostDistance = (spreadPoints + slippagePoints) * Point;",
            risk_helper,
        )
        self.assertIn(
            "AccountFreeMarginCheck(Symbol(), marginSide, gOrderLot)",
            scaffold,
        )
        self.assertIn("MODE_FREEZELEVEL", scaffold)
        self.assertIn(
            "MathMax(stopLevel, freezeLevel) + ExecutionBufferPoints",
            scaffold,
        )
        self.assertIn("string BuildManagedProfileTag(int timeframe)", scaffold)
        self.assertIn(
            "StringFind(OrderComment(), managedProfileTag, 0) != 0",
            scaffold,
        )
        self.assertIn(
            "string orderComment = BuildManagedProfileTag(timeframe);",
            scaffold,
        )
        self.assertNotIn("MathMax(requestedEntry", scaffold)
        self.assertNotIn("MathMin(requestedEntry", scaffold)
        self.assertIn("OrdersHistoryTotal()", scaffold)
        self.assertIn(
            "const int CERTIFIED_ORDER_HISTORY_RECORDS = 10000;",
            scaffold,
        )
        self.assertIn(
            "gManagedHistoryTruncated = historyTotal > CERTIFIED_ORDER_HISTORY_RECORDS;",
            scaffold,
        )
        self.assertIn('SetStatusComment("History Review Required"', scaffold)
        self.assertIn("OrderType() != OP_BUY && OrderType() != OP_SELL", scaffold)
        self.assertIn("gAdxRearmRequired = true;", scaffold)
        self.assertEqual(
            scaffold.count(
                "if(CountManagedOrders() >= MaxOpenPositionsPerSymbolMagic) return;"
            ),
            2,
        )
        submitting_index = scaffold.index('SetStatusComment("Submitting Buy Stop"')
        send_index = scaffold.index("OrderSend(")
        failed_index = scaffold.index('SetStatusComment("Order Failed"')
        pending_index = scaffold.index(
            'SetStatusComment("Pending Buy Stop"',
            send_index,
        )
        self.assertLess(submitting_index, send_index)
        self.assertLess(send_index, failed_index)
        self.assertLess(failed_index, pending_index)
        self.assertIn("MT4 MODE_TICKSIZE is expressed in points", scaffold)
        self.assertEqual(scaffold.count("OrderSend("), 1)

        mission_guard_mutations = {
            "first_attach_prime": (
                "if(lastBar == 0) { lastBar = currentBar; return; }",
                "if(lastBar == 0) lastBar = currentBar;",
            ),
            "adx_rising": (
                "adxCurrent > ADXThreshold && adxCurrent > adxPrevious",
                "adxCurrent > ADXThreshold",
            ),
            "selected_timeframe_bar_clock": (
                "iTime(Symbol(), timeframe, 0)",
                "Time[0]",
            ),
            "signal_shift_alignment": (
                "MODE_MAIN, SignalBarShift + 1)",
                "MODE_MAIN, 2)",
            ),
            "direction_profile_metadata": (
                'CERTIFIED_DIRECTION_RULE = "IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT:SMA20_SLOPE"',
                'CERTIFIED_DIRECTION_RULE = "SMA20_SLOPE"',
            ),
            "sma_direction_shift_alignment": (
                "MODE_SMA, PRICE_CLOSE, SignalBarShift + 1)",
                "MODE_SMA, PRICE_CLOSE, 2)",
            ),
            "long_direction_filter": (
                "bool longPullback = directionalUptrend && signalClose > smaCurrent",
                "bool longPullback = signalClose > smaCurrent",
            ),
            "short_direction_filter": (
                "bool shortPullback = directionalDowntrend && signalClose < smaCurrent",
                "bool shortPullback = signalClose < smaCurrent",
            ),
            "pending_expiry": (
                "long expirationSeconds = (long)PendingExpirationDays * 86400;",
                "long expirationSeconds = (long)PendingExpirationDays * PeriodSeconds(timeframe);",
            ),
            "pending_expiry_upper_bound": (
                "if(PendingExpirationDays > 3650) return(INIT_PARAMETERS_INCORRECT);",
                "if(PendingExpirationDays > 36500) return(INIT_PARAMETERS_INCORRECT);",
            ),
            "manual_order_magic_guard": (
                "MagicNumber <= 0",
                "MagicNumber < 0",
            ),
            "pending_margin_side": (
                "int marginSide = signal == OP_BUYSTOP ? OP_BUY : OP_SELL;",
                "int marginSide = signal;",
            ),
            "fixed_lot_is_separate": (
                "gOrderLot = ValidateFixedLot(FixedLot, marginSide);",
                "gOrderLot = FixedLot;",
            ),
            "fixed_lot_must_be_step_aligned_before_normalization": (
                "double requestedStepUnits = requestedLot / volumeStep;",
                "double requestedStepUnits = MathRound(requestedLot / volumeStep);",
            ),
            "fixed_lot_cannot_round_up": (
                "if(lot > requestedLot + volumeStep * 0.0000001) return(0);",
                "if(lot < requestedLot - volumeStep * 0.0000001) return(0);",
            ),
            "risk_lot_uses_market_margin_side": (
                "SlippagePoints, marginSide);",
                "SlippagePoints, signal);",
            ),
            "risk_includes_execution_cost": (
                "double executionCostDistance = (spreadPoints + slippagePoints) * Point;",
                "double executionCostDistance = 0;",
            ),
            "final_margin_uses_market_side": (
                "AccountFreeMarginCheck(Symbol(), marginSide, gOrderLot)",
                "AccountFreeMarginCheck(Symbol(), signal, gOrderLot)",
            ),
            "freeze_level_modify_floor": (
                "MathMax(stopLevel, freezeLevel) + ExecutionBufferPoints",
                "stopLevel + ExecutionBufferPoints",
            ),
            "profile_bound_management": (
                "StringFind(OrderComment(), managedProfileTag, 0) != 0",
                "StringFind(OrderComment(), managedProfileTag, 0) == 0",
            ),
            "profile_bound_order_comment": (
                "string orderComment = BuildManagedProfileTag(timeframe);",
                'string orderComment = "Linda Holy Grail";',
            ),
            "profile_binds_selected_timeframe": (
                "long profileHash = timeframe;",
                "long profileHash = SignalTimeframe;",
            ),
            "history_excludes_pending_cancel": (
                "if(OrderType() != OP_BUY && OrderType() != OP_SELL) continue;",
                "if(OrderType() != OP_BUYSTOP && OrderType() != OP_SELLSTOP) continue;",
            ),
            "truncated_history_fails_closed": (
                'SetStatusComment("History Review Required", adxCurrent, smaCurrent,',
                'SetStatusComment("Waiting Trend", adxCurrent, smaCurrent,',
            ),
            "history_rearm": (
                "gAdxRearmRequired = true;",
                "gAdxRearmRequired = false;",
            ),
            "same_bar_close_cannot_rearm": (
                "adxCurrent <= ADXThreshold &&\n       latestClosedBar > gLastProcessedManagedCloseTime",
                "adxCurrent <= ADXThreshold",
            ),
            "buy_no_chase": (
                "entryPrice = NormalizePriceUpToTick(requestedEntry, priceTick);",
                "entryPrice = NormalizePriceUpToTick(MathMax(requestedEntry, Ask + brokerFloor), priceTick);",
            ),
            "sell_no_chase": (
                "entryPrice = NormalizePriceDownToTick(requestedEntry, priceTick);",
                "entryPrice = NormalizePriceDownToTick(MathMin(requestedEntry, Bid - brokerFloor), priceTick);",
            ),
            "mt4_tick_size_units": (
                "double priceTick = tickSize * Point;",
                "double priceTick = tickSize;",
            ),
            "swing_management": (
                "bool modifySucceeded = OrderModify(",
                "bool modifySucceeded = MissingOrderModify(",
            ),
            "risk_budget": (
                "double riskMoney = AccountEquity() * RiskPercent / 100.0;",
                "double riskMoney = AccountEquity();",
            ),
            "sell_stop_mode": (
                "const int CERTIFIED_SELL_STOP_ORDER = 5;",
                "const int CERTIFIED_SELL_STOP_ORDER = 1;",
            ),
        }
        with mock.patch.object(
            self.runner,
            "EA_FACTORY_LINDA_HOLY_GRAIL_CERTIFIED_BRIEF_DIGEST",
            brief_digest,
        ):
            for label, (required, replacement) in mission_guard_mutations.items():
                with self.subTest(label=label):
                    mutated = scaffold.replace(required, replacement)
                    self.assertNotEqual(mutated, scaffold)
                    self.assertFalse(
                        self.runner._ea_factory_linda_holy_grail_scaffold_meets_mission(
                            mutated
                        )
                    )

        last_cap = scaffold.rfind(
            "if(CountManagedOrders() >= MaxOpenPositionsPerSymbolMagic) return;"
        )
        cap_removed = scaffold[:last_cap] + scaffold[
            last_cap
            + len(
                "if(CountManagedOrders() >= MaxOpenPositionsPerSymbolMagic) return;"
            ):
        ]
        self.assertFalse(
            self.runner._ea_factory_linda_holy_grail_scaffold_meets_mission(
                cap_removed
            )
        )

        status_reordered = scaffold.replace(
            'SetStatusComment("Submitting Buy Stop", adxCurrent, smaCurrent, currentSpread, CountManagedOrders());',
            'SetStatusComment("Pending Buy Stop", adxCurrent, smaCurrent, currentSpread, CountManagedOrders());',
            1,
        )
        self.assertFalse(
            self.runner._ea_factory_linda_holy_grail_scaffold_meets_mission(
                status_reordered
            )
        )

    def test_linda_holy_grail_scaffold_is_exact_profile_and_mt4_only(self) -> None:
        brief = self._linda_holy_grail_certified_brief()
        brief_digest = self.runner.compute_strategy_brief_digest(brief)
        spec_digest = "5" * 64
        self.assertEqual(
            self.runner._build_ea_factory_source_semantic_repair_scaffold(
                brief,
                strategy_brief_digest=brief_digest,
                strategy_spec_digest=spec_digest,
                target_platform="mt5",
            ),
            "",
        )
        legacy_brief = self.runner.normalize_strategy_brief(
            load_linda_legacy_brief()
        )
        self.assertEqual(
            self.runner._build_ea_factory_source_semantic_repair_scaffold(
                legacy_brief,
                strategy_brief_digest=(
                    self.runner.EA_FACTORY_LINDA_HOLY_GRAIL_LEGACY_BRIEF_DIGEST
                ),
                strategy_spec_digest=spec_digest,
                target_platform="mt4",
            ),
            "",
        )
        wrong_digest = hashlib.sha256(b"different-linda-brief").hexdigest()
        self.assertEqual(
            self.runner._build_ea_factory_source_semantic_repair_scaffold(
                brief,
                strategy_brief_digest=wrong_digest,
                strategy_spec_digest=spec_digest,
                target_platform="mt4",
            ),
            "",
        )
        different_system = dict(brief)
        different_system["systemName"] = "Different Holy Grail variant"
        different_digest = self.runner.compute_strategy_brief_digest(
            different_system
        )
        self.assertEqual(
            self.runner._build_ea_factory_source_semantic_repair_scaffold(
                different_system,
                strategy_brief_digest=different_digest,
                strategy_spec_digest=spec_digest,
                target_platform="mt4",
            ),
            "",
        )

    def test_linda_exact_profile_preflight_requires_the_certified_source(self) -> None:
        brief = self._linda_holy_grail_certified_brief()
        brief_digest = self.runner.compute_strategy_brief_digest(brief)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source_root, prompt, _record_digest, spec_digest = (
                self._factory_fixture(root, strategy_brief=brief)
            )
            patches = self._patch_roots(root)
            with patches[0], patches[1]:
                scaffold = self.runner._build_ea_factory_source_semantic_repair_scaffold(
                    brief,
                    strategy_brief_digest=brief_digest,
                    strategy_spec_digest=spec_digest,
                    target_platform="mt4",
                )
                accepted = json.dumps(
                    {"fileName": "LindaHolyGrail.mq4", "content": scaffold}
                )
                self.runner.preflight_ea_factory_source_semantics(
                    accepted,
                    prompt,
                    relative,
                )
                mutated = scaffold.replace(
                    "long expirationSeconds = (long)PendingExpirationDays * 86400;",
                    "long expirationSeconds = (long)PendingExpirationDays * PeriodSeconds(timeframe);",
                )
                spoofed = mutated + (
                    "\n// long expirationSeconds = (long)PendingExpirationDays * 86400;\n"
                )
                with self.assertRaises(
                    self.runner.EAFactorySourceSemanticValidationError
                ) as raised:
                    self.runner.preflight_ea_factory_source_semantics(
                        json.dumps({
                            "fileName": "SpoofedLindaHolyGrail.mq4",
                            "content": spoofed,
                        }),
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

    def test_certified_scaffold_is_omitted_for_mixed_or_different_profiles(self) -> None:
        brief = self._can_slim_legacy_brief()
        brief_digest = self.runner.compute_strategy_brief_digest(brief)
        spec_digest = "8" * 64
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

    def test_can_slim_mt5_certified_scaffold_is_provided_and_used(self) -> None:
        brief = self._can_slim_legacy_brief()
        brief_digest = self.runner.compute_strategy_brief_digest(brief)
        calls: list[dict[str, object]] = []

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source, prompt, _record_digest, spec_digest = (
                self._factory_fixture(
                    root,
                    platform="mt5",
                    strategy_brief=brief,
                )
            )
            with mock.patch.object(
                self.runner,
                "EA_FACTORY_CAN_SLIM_CERTIFIED_BRIEF_DIGEST",
                brief_digest,
            ):
                scaffold = (
                    self.runner._build_ea_factory_source_semantic_repair_scaffold(
                        brief,
                        strategy_brief_digest=brief_digest,
                        strategy_spec_digest=spec_digest,
                        target_platform="mt5",
                    )
                )
            self.assertTrue(scaffold)
            invalid_source = scaffold.replace(
                "if(currentBar == lastBar) return;",
                "if(currentBar == lastBar) {}",
                1,
            )
            self.assertNotEqual(invalid_source, scaffold)

            def fake_chat(command, **kwargs):
                calls.append({
                    "command": [str(item) for item in command],
                    "prompt": str(kwargs.get("stdin") or ""),
                })
                raw_final_path = Path(command[command.index("-o") + 1])
                raw_payload = json.dumps({
                    "fileName": "generation-unavailable.mq5",
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
                    brief_digest,
                ),
            ):
                result = self.runner.run_codex(
                    prompt,
                    "ea_developer",
                    "mission-ea-factory-can-slim-mt5-certified-fallback",
                    execution_mode="auto_guarded",
                    read_only_work=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )
            written = (source / "CertifiedCanSlimMT5.mq5").read_text(
                encoding="utf-8"
            )
            self.assertFalse((source / "generation-unavailable.mq5").exists())
            contract_values = {
                item["field"]: item["value"]
                for item in result["contractFields"]
            }

        self.assertEqual(len(calls), 2)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["status"], "completed")
        repair = result["semanticRepair"]
        self.assertTrue(repair["attempted"])
        self.assertTrue(repair["succeeded"])
        self.assertTrue(repair["certifiedScaffoldProvided"])
        self.assertTrue(repair["certifiedScaffoldUsed"])
        self.assertFalse(repair["aiRepairSucceeded"])
        self.assertTrue(repair["certifiedFallbackSucceeded"])
        self.assertEqual(repair["sourceOrigin"], "backend_certified_fallback")
        self.assertEqual(
            repair["certifiedFallbackProfileVersion"],
            self.runner.EA_FACTORY_CAN_SLIM_MT5_CERTIFIED_PROFILE_VERSION,
        )
        self.assertEqual(repair["remainingIssues"], [])
        self.assertEqual(
            json.loads(contract_values["sourceFiles"]),
            [f"workspace/{relative}/CertifiedCanSlimMT5.mq5"],
        )
        self.assertEqual(written, scaffold)
        self.assertIn(scaffold, str(calls[1]["prompt"]))
        self.assertNotIn(scaffold, json.dumps(result, ensure_ascii=False))

    def test_custom_ema_certified_scaffold_replaces_two_invalid_ai_sources(self) -> None:
        calls: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source, prompt, strategy_spec, spec_digest = (
                self._custom_ema_factory_fixture(root)
            )
            trusted_profile = (
                self.runner._ea_factory_trusted_custom_ema_smoke_profile(
                    strategy_spec
                )
            )
            scaffold = self.runner._build_ea_factory_source_semantic_repair_scaffold(
                strategy_spec["strategyBrief"],
                strategy_brief_digest=strategy_spec["strategyBriefDigest"],
                strategy_spec_digest=spec_digest,
                target_platform="mt5",
                source_record_digest=strategy_spec["recordDigest"],
                trusted_custom_ema_smoke_profile=trusted_profile,
            )
            self.assertTrue(scaffold)
            invalid_source = scaffold.replace(spec_digest, "b" * 64, 1)
            self.assertNotEqual(invalid_source, scaffold)
            generic_manifest = self.runner.build_compact_ea_source_manifest(
                invalid_source,
                strategy_brief=strategy_spec["strategyBrief"],
                strategy_brief_digest=strategy_spec["strategyBriefDigest"],
                strategy_spec_digest=spec_digest,
                source_digest=hashlib.sha256(
                    invalid_source.encode("utf-8")
                ).hexdigest(),
                target_platform="mt5",
            )
            self.assertFalse(generic_manifest["complete"], generic_manifest)

            raw_invalid = json.dumps({
                "fileName": "AIProposedCustomEma.mq5",
                "content": invalid_source,
            })
            root_patches = self._patch_roots(root)
            with (
                root_patches[0],
                root_patches[1],
                self.assertRaises(
                    self.runner.EAFactorySourceSemanticValidationError
                ) as preflight_error,
            ):
                self.runner.preflight_ea_factory_source_semantics(
                    raw_invalid,
                    prompt,
                    relative,
                )
            self.assertIn(
                "ea_explicit_mission_guardrails_missing",
                preflight_error.exception.findings,
            )
            self.assertEqual(
                preflight_error.exception.repair_scaffold_profile,
                self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_CERTIFIED_PROFILE_VERSION,
            )

            def fake_chat(command, **kwargs):
                calls.append({
                    "command": [str(item) for item in command],
                    "prompt": str(kwargs.get("stdin") or ""),
                })
                raw_final_path = Path(command[command.index("-o") + 1])
                raw_final_path.write_text(raw_invalid, encoding="utf-8")
                return {
                    "ok": True,
                    "exitCode": 0,
                    "durationMs": 1,
                    "processStarted": True,
                    "processTreeTerminated": False,
                    "stdout": raw_invalid,
                    "stderr": "",
                }

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
                    "mission-ea-factory-custom-ema-certified-fallback",
                    execution_mode="auto_guarded",
                    read_only_work=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )
            certified_path = (
                source
                / self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_CERTIFIED_FILE_NAME
            )
            written = certified_path.read_text(encoding="utf-8")
            source_names = {item.name for item in source.iterdir()}
            contract_values = {
                item["field"]: item["value"]
                for item in result["contractFields"]
            }

        self.assertEqual(len(calls), 2)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["status"], "completed")
        repair = result["semanticRepair"]
        self.assertTrue(repair["attempted"])
        self.assertTrue(repair["succeeded"])
        self.assertTrue(repair["certifiedScaffoldProvided"])
        self.assertTrue(repair["certifiedScaffoldUsed"])
        self.assertFalse(repair["aiRepairSucceeded"])
        self.assertTrue(repair["certifiedFallbackSucceeded"])
        self.assertEqual(repair["sourceOrigin"], "backend_certified_fallback")
        self.assertEqual(
            repair["certifiedFallbackProfileVersion"],
            self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_CERTIFIED_PROFILE_VERSION,
        )
        self.assertEqual(repair["remainingIssues"], [])
        self.assertEqual(
            source_names,
            {
                "strategy-spec-v01.json",
                self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_CERTIFIED_FILE_NAME,
            },
        )
        self.assertEqual(written, scaffold)
        self.assertEqual(
            json.loads(contract_values["sourceFiles"]),
            [
                "workspace/"
                f"{relative}/{self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_CERTIFIED_FILE_NAME}"
            ],
        )
        self.assertIn(scaffold, str(calls[1]["prompt"]))
        self.assertNotIn(scaffold, json.dumps(result, ensure_ascii=False))

    def test_custom_ema_certified_fallback_survives_corrective_process_failures(
        self,
    ) -> None:
        cases = (
            (
                "timeout",
                {
                    "ok": False,
                    "status": "timeout",
                    "exitCode": None,
                    "durationMs": 15000,
                    "processStarted": True,
                    "processTreeTerminated": True,
                    "stdout": "",
                    "stderr": "corrective process timed out",
                },
                None,
                None,
            ),
            (
                "launch_failed",
                {
                    "ok": False,
                    "status": "launch_failed",
                    "exitCode": None,
                    "durationMs": 1,
                    "processStarted": False,
                    "processTreeTerminated": False,
                    "stdout": "",
                    "stderr": "corrective process did not launch",
                },
                None,
                None,
            ),
            (
                "malformed_json",
                {
                    "ok": True,
                    "status": "completed",
                    "exitCode": 0,
                    "durationMs": 1,
                    "processStarted": True,
                    "processTreeTerminated": False,
                    "stdout": '{"fileName":',
                    "stderr": "",
                },
                '{"fileName":',
                None,
            ),
            (
                "insufficient_deadline",
                None,
                None,
                70,
            ),
        )
        for case_name, repair_result, repair_output, timeout in cases:
            with self.subTest(case=case_name), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                relative, source, prompt, strategy_spec, spec_digest = (
                    self._custom_ema_factory_fixture(
                        root,
                        build_id=f"ea-build-custom-ema-{case_name}",
                    )
                )
                trusted_profile = (
                    self.runner._ea_factory_trusted_custom_ema_smoke_profile(
                        strategy_spec
                    )
                )
                scaffold = (
                    self.runner._build_ea_factory_source_semantic_repair_scaffold(
                        strategy_spec["strategyBrief"],
                        strategy_brief_digest=strategy_spec["strategyBriefDigest"],
                        strategy_spec_digest=spec_digest,
                        target_platform="mt5",
                        source_record_digest=strategy_spec["recordDigest"],
                        trusted_custom_ema_smoke_profile=trusted_profile,
                    )
                )
                self.assertTrue(scaffold)
                invalid_source = scaffold.replace(spec_digest, "b" * 64, 1)
                raw_invalid = json.dumps({
                    "fileName": "AIProposedCustomEma.mq5",
                    "content": invalid_source,
                })
                calls: list[dict[str, object]] = []

                def fake_chat(command, **kwargs):
                    calls.append({
                        "command": [str(item) for item in command],
                        "prompt": str(kwargs.get("stdin") or ""),
                    })
                    raw_final_path = Path(command[command.index("-o") + 1])
                    if len(calls) == 1:
                        raw_final_path.write_text(raw_invalid, encoding="utf-8")
                        return {
                            "ok": True,
                            "status": "completed",
                            "exitCode": 0,
                            "durationMs": 1,
                            "processStarted": True,
                            "processTreeTerminated": False,
                            "stdout": raw_invalid,
                            "stderr": "",
                        }
                    self.assertIsNotNone(repair_result)
                    if repair_output is not None:
                        raw_final_path.write_text(repair_output, encoding="utf-8")
                    return dict(repair_result)

                for extra in ("frontend", "docs", "assets-source"):
                    (root / extra).mkdir()
                (root / "codex.exe").write_bytes(b"")
                patches = self._runner_patches(root, fake_chat)
                run_kwargs = {}
                if timeout is not None:
                    run_kwargs["timeout"] = timeout
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
                        f"mission-ea-factory-custom-ema-{case_name}",
                        execution_mode="auto_guarded",
                        read_only_work=True,
                        result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                        scoped_workspace_write_root=relative,
                        **run_kwargs,
                    )
                certified_path = (
                    source
                    / self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_CERTIFIED_FILE_NAME
                )
                written = certified_path.read_text(encoding="utf-8")
                source_names = {item.name for item in source.iterdir()}

                self.assertEqual(len(calls), 1 if timeout is not None else 2)
                self.assertTrue(result["ok"], result)
                self.assertEqual(result["status"], "completed")
                repair = result["semanticRepair"]
                self.assertTrue(repair["attempted"])
                self.assertTrue(repair["succeeded"])
                self.assertTrue(repair["certifiedScaffoldProvided"])
                self.assertTrue(repair["certifiedScaffoldUsed"])
                self.assertFalse(repair["aiRepairSucceeded"])
                self.assertTrue(repair["certifiedFallbackSucceeded"])
                self.assertEqual(
                    repair["sourceOrigin"],
                    "backend_certified_fallback",
                )
                self.assertEqual(
                    repair["certifiedFallbackProfileVersion"],
                    self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_CERTIFIED_PROFILE_VERSION,
                )
                self.assertEqual(repair["remainingIssues"], [])
                if case_name in {"timeout", "launch_failed"}:
                    self.assertEqual(repair["repairProcessStatus"], case_name)
                elif case_name == "malformed_json":
                    self.assertIn("repairOutputError", repair)
                else:
                    self.assertEqual(
                        repair["repairProcessStatus"],
                        "skipped_insufficient_deadline",
                    )
                self.assertEqual(
                    source_names,
                    {
                        "strategy-spec-v01.json",
                        self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_CERTIFIED_FILE_NAME,
                    },
                )
                self.assertEqual(written, scaffold)
                self.assertNotIn(scaffold, json.dumps(result, ensure_ascii=False))

    def test_corrective_failures_never_enable_custom_ema_fallback_for_other_lineage(
        self,
    ) -> None:
        for case_name in ("generic", "untrusted_custom_ema_lineage"):
            with self.subTest(case=case_name), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                if case_name == "generic":
                    relative, source, prompt, _record_digest, _spec_digest = (
                        self._factory_fixture(
                            root,
                            build_id="ea-build-generic-timeout-no-ema-fallback",
                        )
                    )
                    invalid_source = self.SOURCE_CONTENT.replace(
                        "  if(currentBar <= 0 || currentBar == lastBar) return;\n"
                        "  lastBar = currentBar;",
                        "  lastBar = currentBar;",
                        1,
                    )
                    file_name = "GenericStillInvalid.mq4"
                else:
                    relative, source, prompt, strategy_spec, spec_digest = (
                        self._custom_ema_factory_fixture(
                            root,
                            build_id="ea-build-untrusted-ema-timeout-no-fallback",
                            spec_overrides={"sourceKey": "custom-operator-near-match"},
                        )
                    )
                    self.assertIsNone(
                        self.runner._ea_factory_trusted_custom_ema_smoke_profile(
                            strategy_spec
                        )
                    )
                    invalid_source = (
                        self.runner._render_ea_factory_custom_ema_smoke_certified_source(
                            source_record_digest=strategy_spec["recordDigest"],
                            strategy_spec_digest=spec_digest,
                            strategy_brief_digest=strategy_spec[
                                "strategyBriefDigest"
                            ],
                        ).replace(
                            "#define SIGNAL_NONE -1",
                            "#define SIGNAL_IDLE -1",
                            1,
                        )
                    )
                    file_name = "UntrustedLineageStillInvalid.mq5"
                raw_invalid = json.dumps({
                    "fileName": file_name,
                    "content": invalid_source,
                })
                calls = []

                def fake_chat(command, **kwargs):
                    calls.append([str(item) for item in command])
                    raw_final_path = Path(command[command.index("-o") + 1])
                    if len(calls) == 1:
                        raw_final_path.write_text(raw_invalid, encoding="utf-8")
                        return {
                            "ok": True,
                            "status": "completed",
                            "exitCode": 0,
                            "durationMs": 1,
                            "processStarted": True,
                            "processTreeTerminated": False,
                            "stdout": raw_invalid,
                            "stderr": "",
                        }
                    return {
                        "ok": False,
                        "status": "timeout",
                        "exitCode": None,
                        "durationMs": 15000,
                        "processStarted": True,
                        "processTreeTerminated": True,
                        "stdout": "",
                        "stderr": "corrective process timed out",
                    }

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
                        f"mission-ea-factory-{case_name}-no-fallback",
                        execution_mode="auto_guarded",
                        read_only_work=True,
                        result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                        scoped_workspace_write_root=relative,
                    )
                source_names = {item.name for item in source.iterdir()}

                self.assertEqual(len(calls), 2)
                self.assertFalse(result["ok"], result)
                self.assertEqual(result["status"], "invalid_output")
                repair = result["semanticRepair"]
                self.assertTrue(repair["attempted"])
                self.assertFalse(repair["succeeded"])
                self.assertFalse(repair["certifiedScaffoldProvided"])
                self.assertFalse(repair["certifiedScaffoldUsed"])
                self.assertFalse(repair["certifiedFallbackSucceeded"])
                self.assertEqual(repair["sourceOrigin"], "none")
                self.assertEqual(repair["repairProcessStatus"], "timeout")
                self.assertEqual(source_names, {"strategy-spec-v01.json"})
                self.assertFalse(
                    (
                        source
                        / self.runner.EA_FACTORY_CUSTOM_EMA_SMOKE_CERTIFIED_FILE_NAME
                    ).exists()
                )

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

    def test_safe_lexical_source_failures_receive_one_bounded_revision(self) -> None:
        invalid_candidates = {
            "missing_ontick": self.SOURCE_CONTENT.replace(
                "void OnTick()", "void TickWithoutLifecycle()", 1
            ),
            "missing_signal_none": self.SOURCE_CONTENT.replace(
                "#define SIGNAL_NONE -1", "#define NO_SIGNAL -1", 1
            ),
        }
        expected_findings = {
            "missing_ontick": "ea_ontick_lifecycle_missing_or_ambiguous",
            "missing_signal_none": "ea_signal_none_sentinel_invalid",
        }
        for case_name, invalid_source in invalid_candidates.items():
            with self.subTest(case=case_name), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                relative, source, prompt, _record_digest, _spec_digest = (
                    self._factory_fixture(root)
                )
                for extra in ("frontend", "docs", "assets-source"):
                    (root / extra).mkdir()
                (root / "codex.exe").write_bytes(b"")
                calls = []

                def fake_chat(command, **kwargs):
                    calls.append(list(command))
                    raw_final_path = Path(command[command.index("-o") + 1])
                    raw_payload = json.dumps({
                        "fileName": "RecoveredEA.mq4",
                        "content": invalid_source if len(calls) == 1 else self.SOURCE_CONTENT,
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
                        f"mission-ea-factory-{case_name}",
                        execution_mode="auto_guarded",
                        read_only_work=True,
                        result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                        scoped_workspace_write_root=relative,
                    )

                self.assertEqual(len(calls), 2)
                self.assertTrue(result["ok"], result)
                self.assertEqual(result["status"], "completed")
                self.assertTrue(result["semanticRepair"]["attempted"])
                self.assertTrue(result["semanticRepair"]["succeeded"])
                self.assertEqual(
                    result["semanticRepair"]["issues"][0]["code"],
                    expected_findings[case_name],
                )
                self.assertTrue((source / "RecoveredEA.mq4").is_file())

    def test_unsupported_model_failure_is_safe_and_actionable(self) -> None:
        rejected_model_message = (
            "The 'gpt-retired' model is not supported when using Codex "
            "with a ChatGPT account."
        )

        def fake_chat(_command, **_kwargs):
            return {
                "ok": False,
                "exitCode": 1,
                "durationMs": 2,
                "processStarted": True,
                "processTreeTerminated": False,
                "stdout": "",
                "stderr": rejected_model_message,
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative, source, prompt, _record_digest, _spec_digest = (
                self._factory_fixture(root, platform="mt5")
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
                    "mission-ea-factory-model-unavailable",
                    execution_mode="auto_guarded",
                    read_only_work=True,
                    result_profile=self.runner.EA_FACTORY_SOURCE_RESULT_PROFILE,
                    scoped_workspace_write_root=relative,
                )
                stderr_path = root / result["artifacts"]["stderr"]
                persisted_stderr = stderr_path.read_text(encoding="utf-8")
                source_names = {item.name for item in source.iterdir()}

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "model_unavailable")
        self.assertIn("ไม่รองรับบัญชี Codex", result["finalMessage"])
        self.assertNotIn("gpt-retired", json.dumps(result, ensure_ascii=False))
        self.assertEqual(
            persisted_stderr,
            "EA Factory structured source diagnostics withheld by Local Runner.",
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
