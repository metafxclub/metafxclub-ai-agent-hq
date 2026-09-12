from __future__ import annotations

import importlib.util
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "backend" / "local-runner" / "ea_strategy_brief.py"
RUNNER_PATH = ROOT / "runner" / "codex_cli_runner.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "metafx_ea_strategy_brief_test_support",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BRIEF = load_module()


def valid_brief() -> dict:
    return {
        "schemaVersion": BRIEF.SCHEMA_VERSION,
        "systemName": "EMA crossover",
        "systemOverview": (
            "Trend following for user-selected liquid markets and timeframe."
        ),
        "entryRules": (
            "Buy when fast[2] <= slow[2] and fast[1] > slow[1]; Sell uses the "
            "inverse closed-bar crossover."
        ),
        "recoveryRules": (
            "RecoveryMode=none; no Grid, Martingale, Averaging, Hedging, "
            "adding to losers, loss-based lot escalation, or same-bar retry."
        ),
        "exitRules": (
            "Close on the opposite signal; StopLoss=1.5*ATR(14)[1]; "
            "TakeProfit=3.0*ATR(14)[1]; TrailingStop=false; "
            "BreakEven=false; PartialClose=false."
        ),
        "moneyManagement": (
            "RiskPercent=1.0% of Equity; calculate Lot=RiskMoney/LossPerLotAtSL "
            "using TickSize and TickValue, round down to VolumeStep, and allow "
            "maximum one open or pending position per Symbol+Magic."
        ),
        "orderExecution": (
            "Send a Market Buy or Market Sell once on the first tick of a new "
            "bar after a closed-bar [1] signal."
        ),
        "displayRequirements": (
            "Show system name, signal state, Balance, Equity and Spread."
        ),
        "additionalNotes": "ไม่มีหมายเหตุเพิ่มเติม",
        "sourceLinks": [
            "https://www.investopedia.com/terms/m/movingaverage.asp",
            "https://www.babypips.com/learn/forex/moving-averages",
        ],
        "checkedAt": "2026-09-10T12:00:00+07:00",
        "limitations": [
            "Research-only specification; no compile or backtest evidence."
        ],
    }


class EAStrategyBriefTests(unittest.TestCase):
    def test_fixed_lot_parser_handles_common_english_and_thai_phrases(self) -> None:
        phrases = (
            "Fixed position size: 0.10 lots",
            "Position size is 0.10 lots",
            "Position sizing is 0.10 lots fixed",
            "0.10 lots fixed per trade",
            "ขนาดล็อต 0.10 ต่อไม้",
            "ขนาดล็อตคงที่เท่ากับ 0.10 ล็อตต่อไม้",
            "ใช้ 0.10 ล็อตคงที่ต่อไม้",
        )
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assertEqual(BRIEF._requested_fixed_lot(phrase), 0.10)

    def test_thai_risk_and_value_first_fixed_lot_are_preserved(self) -> None:
        thai_risk = valid_brief()
        thai_risk["moneyManagement"] = "เสี่ยง 2% ต่อไม้; เปิดได้สูงสุด 1 ไม้"
        risk_result = BRIEF.apply_strategy_brief_implementation_defaults(thai_risk)
        self.assertEqual(BRIEF._requested_risk_percentage(risk_result["moneyManagement"]), 2.0)
        self.assertNotIn("COMPONENT=risk_sizing", risk_result["moneyManagement"])
        self.assertNotIn("RiskPercent=1.0", risk_result["moneyManagement"])
        self.assertIn("COMPONENT=lot_calculation", risk_result["moneyManagement"])

        for fixed_text in (
            "Position sizing is 0.10 lots fixed; max one open position per Symbol+Magic.",
            "ใช้ 0.10 ล็อตคงที่ต่อไม้; เปิดได้สูงสุด 1 ไม้ต่อ Symbol+Magic",
        ):
            with self.subTest(fixed_text=fixed_text):
                fixed = valid_brief()
                fixed["moneyManagement"] = fixed_text
                fixed_result = BRIEF.apply_strategy_brief_implementation_defaults(fixed)
                self.assertEqual(BRIEF._requested_fixed_lot(fixed_result["moneyManagement"]), 0.10)
                self.assertNotIn("COMPONENT=risk_sizing", fixed_result["moneyManagement"])
                self.assertNotIn("RiskPercent=1.0", fixed_result["moneyManagement"])

    def test_source_protection_value_parser_handles_common_notation(self) -> None:
        cases = (
            ("StopLoss=1.5*ATR(14)[1]", "stop", (1.5, "atr")),
            ("Initial stop ATR*1.5", "stop", (1.5, "atr")),
            ("profit target 2R", "take", (2.0, "r")),
            ("Hard stop 20 pips", "stop", (20.0, "pip")),
            ("TakeProfitPoints=400", "take", (400.0, "point")),
        )
        for text, component, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(
                    BRIEF._requested_protection_value(text, component),
                    expected,
                )

    def test_reward_risk_ratio_is_preserved_without_borrowing_stop_value(self) -> None:
        cases = (
            ("Hard stop 20 pips; profit target uses reward-to-risk 3:1.", 3.0),
            ("Take profit at a 3-to-1 reward/risk ratio.", 3.0),
            ("Take profit uses risk-to-reward ratio 1:3.", 3.0),
        )
        for exit_rules, expected in cases:
            with self.subTest(exit_rules=exit_rules):
                self.assertEqual(
                    BRIEF._requested_protection_value(exit_rules, "take"),
                    (expected, "r"),
                )
                source = valid_brief()
                source["exitRules"] = exit_rules
                resolved = BRIEF.apply_strategy_brief_implementation_defaults(source)
                self.assertNotIn("COMPONENT=take_profit", resolved["exitRules"])
                self.assertNotIn("RewardRiskRatio=2.0", resolved["exitRules"])

        shared_clause = "Stop Loss uses the prior swing low and Take Profit uses 2R"
        self.assertIsNone(BRIEF._requested_protection_value(shared_clause, "stop"))
        self.assertEqual(
            BRIEF._requested_protection_value(shared_clause, "take"),
            (2.0, "r"),
        )
        self.assertIsNone(BRIEF._requested_stop_percentage_range(
            "Stop Loss uses the prior swing low and Take Profit is 5% above entry"
        ))

    def test_installed_can_slim_percent_stop_and_two_r_target_are_component_scoped(self) -> None:
        exit_rules = (
            "กฎจากแหล่งข้อมูล: ตัดขาดทุนทุกสถานะ Long ไม่เกิน 7%-8% ต่ำกว่าจุดซื้อ "
            "โดยใช้เป็น Stop Loss หลักของระบบ CAN SLIM; หากตลาดรวมเปลี่ยนเป็นขาลงหรือ"
            "สัญญาณ Market direction ไม่สนับสนุน ให้ลดหรือออกจากสถานะ Long เพราะแหล่ง "
            "Macro Ops ระบุว่าหุ้นส่วนใหญ่มีแนวโน้มไปตามตลาดรวม. ไม่พบ Take Profit "
            "แบบตัวเลขจากสองแหล่งนี้ จึงเติมเฉพาะส่วน TP: "
            "[IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT][POLICY=compact-ea-atr-risk-v1]"
            "[COMPONENT=exitRules] Take Profit ใช้ RewardRiskRatio=2.0 จากระยะ Stop Loss "
            "จริงที่ป้องกันอยู่หลังคำนวณจากจุดซื้อถึง SL 7%-8%; หาก broker floor หรือ"
            "ข้อจำกัดคำสั่งทำให้ระยะ SL จริงเปลี่ยน ให้ TP คำนวณจากระยะ SL จริงนั้น "
            "สูตร 2R เป็น authoritative สำหรับค่าเริ่มต้นนี้ ส่วน TakeProfitATR=3.0 "
            "เป็นค่า nominal/display-only ไม่ใช่ TP input อิสระ. TrailingStop=false, "
            "BreakEven=false และ PartialClose=false เพราะไม่พบกฎจากแหล่งข้อมูล"
        )
        money_management = (
            "แหล่งข้อมูลให้กฎ stop loss 7%-8% แต่ไม่พบ maxRiskPerTrade, position sizing "
            "formula, daily/equity stop หรือ max open positions ที่ครบถ้วน ดังนั้น "
            "[IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT][POLICY=compact-ea-atr-risk-v1]"
            "[COMPONENT=moneyManagement] ให้ใช้ percent-equity sizing โดย RiskPercent=1.0 "
            "ต่อสถานะ คำนวณขนาดล็อตจากความเสียหายจริงต่อ 1 lot ที่ระยะ SL จริง โดยใช้ "
            "TickSize/TickValue แล้ว round down ตาม VolumeStep เท่านั้น ไม่ round up "
            "และไม่เพิ่มขนาดหลังขาดทุน; หาก TickSize, TickValue, margin, stop distance "
            "หรือ minimum volume ไม่ valid ให้ข้าม trade. ตั้ง "
            "MaxOpenPositionsPerSymbolMagic=1 โดยนับทั้ง live orders และ pending orders "
            "ของ Symbol+Magic เดียวกัน. Daily equity stop ไม่พบจากแหล่ง จึงไม่ตั้งเป็น"
            "ข้อเท็จจริงต้นทางและควรเป็น input ที่ผู้ใช้ทดสอบเองหากต้องการ"
        )
        self.assertIsNone(BRIEF._requested_protection_value(exit_rules, "stop"))
        self.assertEqual(BRIEF._requested_stop_percentage_range(exit_rules), (7.0, 8.0))
        self.assertEqual(BRIEF._requested_protection_value(exit_rules, "take"), (2.0, "r"))
        self.assertEqual(BRIEF._requested_risk_percentage(money_management), 1.0)

        brief = valid_brief()
        brief.update({
            "systemName": "CAN SLIM",
            "entryRules": (
                "Buy/Long เมื่อ EPS earnings growth และ institutional sponsorship "
                "ผ่านเกณฑ์จากข้อมูลภายนอก พร้อมกับ Close[1] ทะลุ breakout level "
                "และ market filter เป็นขาขึ้น "
                "โดยใช้เฉพาะแท่งปิด [2] และ [1]. Sell/Short entry ไม่มีในแหล่งข้อมูล "
                "และไม่ควรเปิด Sell/Short เป็น entry ใหม่."
            ),
            "recoveryRules": (
                "[IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT]"
                "[POLICY=compact-ea-atr-risk-v1][COMPONENT=recoveryRules] "
                "RecoveryMode=none, ไม่เพิ่มไม้แก้, ไม่ถัวเฉลี่ย และไม่เปิดคำสั่ง "
                "recovery หลังขาดทุน"
            ),
            "exitRules": exit_rules,
            "moneyManagement": money_management,
            "orderExecution": (
                "[IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT]"
                "[POLICY=compact-ea-atr-risk-v1][COMPONENT=orderExecution] ใช้ Market "
                "order สำหรับ Buy/Long เมื่อเกิดสัญญาณจากแท่งปิด [1] และส่งคำสั่งบน "
                "first tick ของแท่งใหม่หนึ่งครั้งต่อหนึ่งสัญญาณ ไม่ใช้ bar 0 เพื่อยืนยัน"
                "สัญญาณ ไม่สร้าง pending order และไม่เปิด Sell/Short entry ก่อนเปิด "
                "ออเดอร์ให้ตรวจ spread, broker stop floor และ ExecutionBufferPoints=2"
            ),
            "displayRequirements": (
                "ใช้ Comment แสดง SystemName=CAN SLIM, SignalState, Balance, Equity, "
                "Spread, Symbol, Timeframe, MarketDirection, BreakoutLevel, "
                "StopLossPercent, RiskPercent และ RecoveryMode=none"
            ),
        })
        brief = BRIEF.normalize_strategy_brief(brief)
        brief_digest = BRIEF.compute_strategy_brief_digest(brief)
        source = f'''#property strict
#property description "EA_STRATEGY_BRIEF_SHA256:{brief_digest}"
#define SIGNAL_NONE -1
input double InpStopLossPercent = 7.5;
input double RewardRiskRatio = 2.0;
input double RiskPercent = 1.0;
input int ExecutionBufferPoints = 2;
input int MaxOpenPositionsPerSymbolMagic = 1;
input int MagicNumber = 4186001;
input bool FundamentalCriteriaConfirmed = false;
input int MaxSpreadPoints = 30;
int OnInit() {{ return(INIT_SUCCEEDED); }}
int CountManagedPositions() {{
  int count = 0;
  for(int i=OrdersTotal()-1; i>=0; i--) {{
    if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
    if(OrderSymbol() == Symbol() && OrderMagicNumber() == MagicNumber) count++;
  }}
  return(count);
}}
double CalculateRiskLot(double entryPrice, double stopLoss) {{
  double tickSize = MarketInfo(Symbol(), MODE_TICKSIZE);
  double tickValue = MarketInfo(Symbol(), MODE_TICKVALUE);
  double volumeStep = MarketInfo(Symbol(), MODE_LOTSTEP);
  double minimumLot = MarketInfo(Symbol(), MODE_MINLOT);
  double maximumLot = MarketInfo(Symbol(), MODE_MAXLOT);
  double stopDistance = MathAbs(entryPrice - stopLoss);
  if(tickSize <= 0 || tickValue <= 0 || volumeStep <= 0 || stopDistance <= 0) return(0);
  if(minimumLot <= 0 || maximumLot <= 0) return(0);
  double riskMoney = AccountEquity() * RiskPercent / 100.0;
  double lossPerLotAtSL = (stopDistance / tickSize) * tickValue;
  if(lossPerLotAtSL <= 0) return(0);
  double lot = MathFloor((riskMoney / lossPerLotAtSL) / volumeStep) * volumeStep;
  if(lot < minimumLot || lot > maximumLot) return(0);
  if(AccountFreeMarginCheck(Symbol(), OP_BUY, lot) <= 0) return(0);
  return(lot);
}}
void OnTick() {{
  static datetime lastBar = 0;
  datetime currentBar = Time[0];
  if(currentBar <= 0 || currentBar == lastBar) return;
  lastBar = currentBar;
  if(Bars < 53) return;
  double marketMA1 = iMA(Symbol(), Period(), 50, 0, MODE_SMA, PRICE_CLOSE, 1);
  double marketMA2 = iMA(Symbol(), Period(), 50, 0, MODE_SMA, PRICE_CLOSE, 2);
  bool marketDown = Close[1] < marketMA1 && marketMA1 <= marketMA2;
  for(int i=OrdersTotal()-1; i>=0; i--) {{
    if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
    if(OrderSymbol() == Symbol() && OrderMagicNumber() == MagicNumber &&
       OrderType() == OP_BUY && marketDown) {{
      OrderClose(OrderTicket(), OrderLots(), Bid, 3);
    }}
  }}
  if(InpStopLossPercent < 7.0 || InpStopLossPercent > 8.0) return;
  if(!FundamentalCriteriaConfirmed) return;
  double currentSpread = MarketInfo(Symbol(), MODE_SPREAD);
  if(currentSpread > MaxSpreadPoints) return;
  double breakoutLevel = High[2];
  int signal = SIGNAL_NONE;
  if(Close[1] > breakoutLevel && Close[1] > marketMA1 && marketMA1 > marketMA2)
    signal = OP_BUY;
  if(signal == SIGNAL_NONE) return;
  if(CountManagedPositions() >= MaxOpenPositionsPerSymbolMagic) return;
  double entryPrice = Ask;
  double brokerFloor = (MarketInfo(Symbol(), MODE_STOPLEVEL) + ExecutionBufferPoints) * Point;
  double stopDistance = MathMax(entryPrice * InpStopLossPercent / 100.0, brokerFloor);
  if(stopDistance <= 0) return;
  double stopLoss = entryPrice - stopDistance;
  double takeProfit = entryPrice + stopDistance * RewardRiskRatio;
  double lot = CalculateRiskLot(entryPrice, stopLoss);
  if(lot <= 0) return;
  Comment("CAN SLIM SignalState=BuySignal Balance=", AccountBalance(),
          " Equity=", AccountEquity(), " Spread=", MarketInfo(Symbol(), MODE_SPREAD),
          " Symbol=", Symbol(), " Timeframe=", Period(), " MarketDirection=up",
          " BreakoutLevel=", breakoutLevel, " StopLossPercent=", InpStopLossPercent,
          " RiskPercent=", RiskPercent, " RecoveryMode=none");
  OrderSend(Symbol(), OP_BUY, lot, entryPrice, 3, stopLoss, takeProfit,
            "CAN SLIM", MagicNumber, 0);
}}
'''
        analysis = BRIEF.analyze_compact_ea_source(
            source,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertTrue(analysis["complete"], analysis)
        self.assertTrue(analysis["checks"]["testerInputContract"])
        self.assertTrue(analysis["checks"]["exitAndProtectionExecution"])
        self.assertTrue(analysis["checks"]["moneyManagementExecution"])
        self.assertTrue(analysis["checks"]["orderExecution"])

        missing_display_field = source.replace(
            '" BreakoutLevel=", breakoutLevel, ',
            "",
            1,
        ) + '\n// Comment(" BreakoutLevel=", breakoutLevel); comment spoof\n'
        missing_display_analysis = BRIEF.analyze_compact_ea_source(
            missing_display_field,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(
                missing_display_field.encode("utf-8")
            ).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(missing_display_analysis["checks"]["displayBehavior"])
        self.assertFalse(missing_display_analysis["complete"])
        self.assertIn(
            "ea_display_required_field_missing:breakout_level",
            missing_display_analysis["findings"],
        )

        unsupported_input_replacements = (
            'input string Label = "unsupported";',
            "input int MaxSpreadPoints = 20 + 10;",
            "input int MaxSpreadPoints = 30; input int SlippagePoints = 3;",
            "input int\nMaxSpreadPoints = 30;",
            "sinput int MaxSpreadPoints = 30;",
            "input int MagicNumber = 4186001;",
        )
        for replacement in unsupported_input_replacements:
            with self.subTest(tester_input=replacement):
                rejected_source = source.replace(
                    "input int MaxSpreadPoints = 30;",
                    replacement,
                    1,
                )
                rejected = BRIEF.analyze_compact_ea_source(
                    rejected_source,
                    strategy_brief=brief,
                    strategy_brief_digest=brief_digest,
                    strategy_spec_digest="1" * 64,
                    source_digest=hashlib.sha256(
                        rejected_source.encode("utf-8")
                    ).hexdigest(),
                    target_platform="mt4",
                )
                self.assertFalse(rejected["checks"]["testerInputContract"])
                self.assertFalse(rejected["complete"])
                self.assertIn(
                    "ea_tester_input_contract_unsupported",
                    rejected["findings"],
                )

        missing_percent_range_guard = source.replace(
            "  if(InpStopLossPercent < 7.0 || InpStopLossPercent > 8.0) return;\n",
            "",
        )
        missing_percent_range_analysis = BRIEF.analyze_compact_ea_source(
            missing_percent_range_guard,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(missing_percent_range_guard.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(missing_percent_range_analysis["checks"]["exitAndProtectionExecution"])
        self.assertIn("ea_exit_or_protection_path_missing", missing_percent_range_analysis["findings"])

        missing_external_gate = source.replace(
            "  if(!FundamentalCriteriaConfirmed) return;\n",
            "",
        )
        missing_external_gate_analysis = BRIEF.analyze_compact_ea_source(
            missing_external_gate,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(missing_external_gate.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(
            missing_external_gate_analysis["checks"]["entryExecution"],
            missing_external_gate_analysis,
        )
        self.assertIn("ea_external_entry_gate_missing", missing_external_gate_analysis["findings"])

        gate_before_management = source.replace(
            "  if(InpStopLossPercent < 7.0 || InpStopLossPercent > 8.0) return;\n"
            "  if(!FundamentalCriteriaConfirmed) return;\n",
            "",
        ).replace(
            "  if(Bars < 53) return;\n",
            (
                "  if(InpStopLossPercent < 7.0 || InpStopLossPercent > 8.0) return;\n"
                "  if(!FundamentalCriteriaConfirmed) return;\n"
                "  if(Bars < 53) return;\n"
            ),
        )
        gate_before_management_analysis = BRIEF.analyze_compact_ea_source(
            gate_before_management,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(gate_before_management.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(
            gate_before_management_analysis["checks"]["exitAndProtectionExecution"]
        )
        self.assertIn(
            "ea_entry_gate_precedes_exit_management",
            gate_before_management_analysis["findings"],
        )

        impossible_percent_guard = source.replace(
            "InpStopLossPercent < 7.0 || InpStopLossPercent > 8.0",
            "InpStopLossPercent < 7.0 && InpStopLossPercent > 8.0",
        )
        impossible_percent_analysis = BRIEF.analyze_compact_ea_source(
            impossible_percent_guard,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(impossible_percent_guard.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(impossible_percent_analysis["checks"]["exitAndProtectionExecution"])

        conjunctive_dependency_guard = source.replace(
            "tickSize <= 0 || tickValue <= 0 || volumeStep <= 0 || stopDistance <= 0",
            "tickSize <= 0 && tickValue <= 0 && volumeStep <= 0 && stopDistance <= 0",
        )
        conjunctive_dependency_analysis = BRIEF.analyze_compact_ea_source(
            conjunctive_dependency_guard,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(conjunctive_dependency_guard.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(conjunctive_dependency_analysis["checks"]["lotCalculationSafety"])

        impossible_lot_guard = source.replace(
            "lot < minimumLot || lot > maximumLot",
            "lot < minimumLot && lot > maximumLot",
        )
        impossible_lot_analysis = BRIEF.analyze_compact_ea_source(
            impossible_lot_guard,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(impossible_lot_guard.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(impossible_lot_analysis["checks"]["lotCalculationSafety"])

        conjunctive_margin_guard = source.replace(
            "AccountFreeMarginCheck(Symbol(), OP_BUY, lot) <= 0",
            "AccountFreeMarginCheck(Symbol(), OP_BUY, lot) <= 0 && lot < 0",
        )
        conjunctive_margin_analysis = BRIEF.analyze_compact_ea_source(
            conjunctive_margin_guard,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(conjunctive_margin_guard.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(conjunctive_margin_analysis["checks"]["lotCalculationSafety"])

        missing_maximum_lot = source.replace(
            "  double maximumLot = MarketInfo(Symbol(), MODE_MAXLOT);\n",
            "",
        ).replace(
            "  if(minimumLot <= 0 || maximumLot <= 0) return(0);",
            "  if(minimumLot <= 0) return(0);",
        ).replace(
            "  if(lot < minimumLot || lot > maximumLot) return(0);",
            "  if(lot < minimumLot) return(0);",
        )
        missing_maximum_lot_analysis = BRIEF.analyze_compact_ea_source(
            missing_maximum_lot,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(missing_maximum_lot.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(missing_maximum_lot_analysis["checks"]["lotCalculationSafety"])

        zero_broker_floor = source.replace(
            "double brokerFloor = (MarketInfo(Symbol(), MODE_STOPLEVEL) + ExecutionBufferPoints) * Point;",
            "double brokerFloor = 0;",
        )
        zero_broker_floor_analysis = BRIEF.analyze_compact_ea_source(
            zero_broker_floor,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(zero_broker_floor.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(zero_broker_floor_analysis["checks"]["exitAndProtectionExecution"])

        missing_broker_buffer = source.replace(
            "(MarketInfo(Symbol(), MODE_STOPLEVEL) + ExecutionBufferPoints) * Point",
            "MarketInfo(Symbol(), MODE_STOPLEVEL) * Point",
        )
        missing_broker_buffer_analysis = BRIEF.analyze_compact_ea_source(
            missing_broker_buffer,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(missing_broker_buffer.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(missing_broker_buffer_analysis["checks"]["exitAndProtectionExecution"])

        missing_spread_guard = source.replace(
            "  double currentSpread = MarketInfo(Symbol(), MODE_SPREAD);\n"
            "  if(currentSpread > MaxSpreadPoints) return;\n",
            "",
        )
        missing_spread_guard_analysis = BRIEF.analyze_compact_ea_source(
            missing_spread_guard,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(missing_spread_guard.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(missing_spread_guard_analysis["checks"]["orderExecution"])
        self.assertIn("ea_spread_guard_missing", missing_spread_guard_analysis["findings"])

        neutralized_broker_floor = source.replace(
            ") * Point;\n  double stopDistance",
            ") * Point * 0;\n  double stopDistance",
        )
        neutralized_broker_floor_analysis = BRIEF.analyze_compact_ea_source(
            neutralized_broker_floor,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(neutralized_broker_floor.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(
            neutralized_broker_floor_analysis["checks"]["exitAndProtectionExecution"]
        )

        scaled_maximum_lot = source.replace(
            "MarketInfo(Symbol(), MODE_MAXLOT);",
            "MarketInfo(Symbol(), MODE_MAXLOT) * 1000;",
        )
        scaled_maximum_lot_analysis = BRIEF.analyze_compact_ea_source(
            scaled_maximum_lot,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(scaled_maximum_lot.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(scaled_maximum_lot_analysis["checks"]["lotCalculationSafety"])

        neutralized_spread = source.replace(
            "MarketInfo(Symbol(), MODE_SPREAD);",
            "MarketInfo(Symbol(), MODE_SPREAD) * 0;",
        )
        neutralized_spread_analysis = BRIEF.analyze_compact_ea_source(
            neutralized_spread,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(neutralized_spread.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(neutralized_spread_analysis["checks"]["orderExecution"])

        scaled_tick_value = source.replace(
            "MarketInfo(Symbol(), MODE_TICKVALUE);",
            "MarketInfo(Symbol(), MODE_TICKVALUE) * 100;",
        )
        scaled_tick_value_analysis = BRIEF.analyze_compact_ea_source(
            scaled_tick_value,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(scaled_tick_value.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(scaled_tick_value_analysis["checks"]["lotCalculationSafety"])

        multiline_guard_source = source.replace(
            "if(tickSize <= 0 || tickValue <= 0 || volumeStep <= 0 || stopDistance <= 0) return(0);",
            (
                "if(tickSize <= 0 || tickValue <= 0 ||\n"
                "     volumeStep <= 0 || stopDistance <= 0)\n"
                "    return(0);"
            ),
        )
        multiline_guard_analysis = BRIEF.analyze_compact_ea_source(
            multiline_guard_source,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(multiline_guard_source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertTrue(multiline_guard_analysis["complete"], multiline_guard_analysis)
        self.assertTrue(multiline_guard_analysis["checks"]["riskSizingExecution"])
        self.assertTrue(multiline_guard_analysis["checks"]["lotCalculationSafety"])
        self.assertTrue(multiline_guard_analysis["checks"]["moneyManagementExecution"])

        unexpected_sell_source = source.replace(
            '            "CAN SLIM", MagicNumber, 0);',
            (
                '            "CAN SLIM", MagicNumber, 0);\n'
                '  if(Close[1] < marketMA1)\n'
                '    OrderSend(Symbol(), OP_SELL, lot, Bid, 3, Bid + stopDistance,\n'
                '              Bid - stopDistance * RewardRiskRatio,\n'
                '              "CAN SLIM short", MagicNumber, 0);'
            ),
        )
        unexpected_sell_analysis = BRIEF.analyze_compact_ea_source(
            unexpected_sell_source,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(unexpected_sell_source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(unexpected_sell_analysis["checks"]["orderExecution"])
        self.assertIn("ea_order_execution_mode_missing", unexpected_sell_analysis["findings"])

        opposite_signal_source = source.replace(
            "  if(Close[1] > breakoutLevel && Close[1] > marketMA1 && marketMA1 > marketMA2)\n"
            "    signal = OP_BUY;",
            (
                "  if(Close[1] > breakoutLevel && Close[1] > marketMA1 && marketMA1 > marketMA2)\n"
                "    signal = OP_BUY;\n"
                "  if(Close[1] < marketMA1) signal = OP_SELL;"
            ),
        )
        opposite_signal_analysis = BRIEF.analyze_compact_ea_source(
            opposite_signal_source,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(opposite_signal_source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(opposite_signal_analysis["checks"]["orderExecution"])
        self.assertIn("ea_order_execution_mode_missing", opposite_signal_analysis["findings"])

        two_r_stop = source.replace(
            "entryPrice * InpStopLossPercent / 100.0",
            "entryPrice * RewardRiskRatio / 100.0",
        )
        rejected = BRIEF.analyze_compact_ea_source(
            two_r_stop,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(two_r_stop.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(rejected["checks"]["exitAndProtectionExecution"])
        self.assertIn("ea_exit_or_protection_path_missing", rejected["findings"])

    def test_projection_is_exact_and_record_id_remains_backend_derived(self) -> None:
        source = valid_brief()
        projected = BRIEF.project_strategy_brief_contract(source)

        self.assertEqual(
            list(projected),
            [
                "strategyBrief",
                "sourceDigest",
                "sourceLinks",
                "checkedAt",
                "limitations",
            ],
        )
        self.assertEqual(
            tuple(
                key
                for key in projected["strategyBrief"]
                if key in BRIEF.CONTENT_FIELDS
            ),
            BRIEF.CONTENT_FIELDS,
        )
        self.assertNotIn("record_id", projected["strategyBrief"])
        self.assertEqual(
            projected["sourceDigest"],
            BRIEF.compute_strategy_brief_digest(source),
        )
        self.assertRegex(projected["sourceDigest"], r"^[0-9a-f]{64}$")

    def test_digest_uses_normalized_text(self) -> None:
        left = valid_brief()
        right = valid_brief()
        right["systemName"] = "  EMA   crossover  "

        self.assertEqual(
            BRIEF.compute_strategy_brief_digest(left),
            BRIEF.compute_strategy_brief_digest(right),
        )

    def test_safe_optional_defaults_do_not_invent_recovery(self) -> None:
        source = valid_brief()
        for field in (
            "recoveryRules",
            "displayRequirements",
            "additionalNotes",
            "limitations",
        ):
            source.pop(field)

        normalized = BRIEF.normalize_strategy_brief(source)

        self.assertIn("ห้ามเพิ่ม Grid", normalized["recoveryRules"])
        self.assertIn("Balance", normalized["displayRequirements"])
        self.assertEqual(normalized["additionalNotes"], "ไม่มีหมายเหตุเพิ่มเติม")
        self.assertTrue(normalized["limitations"])

    def test_implementation_defaults_are_labeled_and_idempotent(self) -> None:
        source = valid_brief()
        source.update({
            "recoveryRules": "not_publicly_stated",
            "exitRules": "not_publicly_stated",
            "moneyManagement": "not_publicly_stated",
            "orderExecution": "not_publicly_stated",
        })

        first = BRIEF.apply_strategy_brief_implementation_defaults(source)
        second = BRIEF.apply_strategy_brief_implementation_defaults(first)

        self.assertEqual(second, first)
        for field in (
            "recoveryRules",
            "exitRules",
            "moneyManagement",
            "orderExecution",
        ):
            self.assertIn(BRIEF.IMPLEMENTATION_DEFAULT_MARKER, first[field])
        self.assertIn("StopLossPoints=300", first["exitRules"])
        self.assertIn("TakeProfitPoints=600", first["exitRules"])
        self.assertIn("PositionSizingMode=fixed_lot", first["moneyManagement"])
        self.assertIn("FixedLot=0.01", first["moneyManagement"])
        self.assertIn("MaxOpenPositionsPerSymbolMagic=1", first["moneyManagement"])
        self.assertIn("RecoveryMode=none", first["recoveryRules"])
        self.assertNotIn("COMPONENT=closed_bar_execution", first["orderExecution"])
        self.assertIn("INPUT_METADATA_VERSION=ea-optimization-inputs-v1", first["additionalNotes"])
        self.assertIn("RiskPercent(double,optional percent_equity", first["additionalNotes"])
        self.assertIn("DEFAULTED_COMPONENTS=", first["additionalNotes"])
        self.assertTrue(
            any(
                BRIEF.IMPLEMENTATION_DEFAULT_MARKER in limitation
                for limitation in first["limitations"]
            )
        )

    def test_preexisting_canonical_default_gets_missing_receipts(self) -> None:
        source = valid_brief()
        source["exitRules"] = (
            "TakeProfit=40 pips; TrailingStop=false; BreakEven=false; "
            "PartialClose=false.\n" + BRIEF.IMPLEMENTATION_DEFAULT_STOP_LOSS
        )
        source["additionalNotes"] = "Source note."
        source["limitations"] = ["Source limitation."]

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertIn("DEFAULTED_COMPONENTS=stop_loss", result["additionalNotes"])
        self.assertTrue(
            any(
                "DEFAULTED_COMPONENTS=stop_loss" in item
                for item in result["limitations"]
            )
        )

    def test_receipts_update_to_union_when_a_later_component_is_defaulted(self) -> None:
        source = valid_brief()
        source["exitRules"] = "not_publicly_stated"
        first = BRIEF.apply_strategy_brief_implementation_defaults(source)
        first["recoveryRules"] = "not_publicly_stated"

        result = BRIEF.apply_strategy_brief_implementation_defaults(first)

        receipt_lines = [
            line
            for line in result["additionalNotes"].splitlines()
            if "DEFAULTED_COMPONENTS=" in line
        ]
        self.assertEqual(len(receipt_lines), 1)
        self.assertIn("stop_loss", receipt_lines[0])
        self.assertIn("recovery", receipt_lines[0])
        limitation_receipts = [
            item for item in result["limitations"] if "DEFAULTED_COMPONENTS=" in item
        ]
        self.assertEqual(len(limitation_receipts), 1)
        self.assertIn("recovery", limitation_receipts[0])

    def test_partial_exit_adds_only_missing_take_profit(self) -> None:
        source = valid_brief()
        source["exitRules"] = (
            "Source-backed StopLoss=swing_low[1]; "
            "Take Profit not_publicly_stated; TrailingStop=false."
        )

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertIn("StopLoss=swing_low[1]", result["exitRules"])
        self.assertIn("TakeProfitPoints=600", result["exitRules"])
        self.assertNotIn("StopLossPoints=300", result["exitRules"])
        self.assertNotIn("COMPONENT=trailing_stop", result["exitRules"])
        self.assertIn("COMPONENT=break_even", result["exitRules"])
        self.assertIn("COMPONENT=partial_close", result["exitRules"])

    def test_hard_stop_and_profit_target_do_not_receive_atr_protection(self) -> None:
        source = valid_brief()
        source["exitRules"] = (
            "Hard stop 20 pips; profit target 40 pips; TrailingStop=false; "
            "BreakEven=false; PartialClose=false."
        )

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertNotIn("StopLossPoints=300", result["exitRules"])
        self.assertNotIn("TakeProfitPoints=600", result["exitRules"])
        self.assertNotIn("COMPONENT=stop_loss", result["exitRules"])
        self.assertNotIn("COMPONENT=take_profit", result["exitRules"])

    def test_maximum_concurrent_trades_does_not_receive_position_cap_one(self) -> None:
        source = valid_brief()
        source["moneyManagement"] = (
            "RiskPercent=0.5% of Equity with the lot size calculated from "
            "TickSize and TickValue; maximum 3 concurrent trades per "
            "Symbol+Magic."
        )

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertIn("maximum 3 concurrent trades", result["moneyManagement"])
        self.assertNotIn(
            "MaxOpenPositionsPerSymbolMagic=1",
            result["moneyManagement"],
        )
        self.assertNotIn("COMPONENT=position_cap", result["moneyManagement"])

    def test_partial_money_management_preserves_source_risk(self) -> None:
        source = valid_brief()
        source["moneyManagement"] = (
            "Source-backed RiskPercent=0.5%; max positions not_publicly_stated."
        )

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertIn("RiskPercent=0.5%", result["moneyManagement"])
        self.assertIn("COMPONENT=lot_calculation", result["moneyManagement"])
        self.assertIn("MaxOpenPositionsPerSymbolMagic=1", result["moneyManagement"])
        self.assertNotIn("RiskPercent=1.0", result["moneyManagement"])

    def test_recovery_policy_distinguishes_none_incomplete_and_complete(self) -> None:
        source = valid_brief()
        explicit_none = BRIEF.apply_strategy_brief_implementation_defaults(source)
        self.assertNotIn(
            BRIEF.IMPLEMENTATION_DEFAULT_MARKER,
            explicit_none["recoveryRules"],
        )

        incomplete = valid_brief()
        incomplete["recoveryRules"] = "Source mentions Grid recovery."
        incomplete_result = BRIEF.apply_strategy_brief_implementation_defaults(
            incomplete
        )
        self.assertIn("Source mentions Grid", incomplete_result["recoveryRules"])
        self.assertIn("RecoveryMode=none", incomplete_result["recoveryRules"])
        self.assertIn(
            BRIEF.IMPLEMENTATION_DEFAULT_MARKER,
            incomplete_result["recoveryRules"],
        )

        complete = valid_brief()
        complete_rule = (
            "RecoveryMode=grid_martingale; trigger=100 adverse points; "
            "spacing=100 points; lot multiplier=1.2; max=3 levels; "
            "basket TP=20 points; reset after basket close."
        )
        complete["recoveryRules"] = complete_rule
        complete_result = BRIEF.apply_strategy_brief_implementation_defaults(complete)
        self.assertEqual(complete_result["recoveryRules"], complete_rule)
        self.assertNotIn(
            BRIEF.IMPLEMENTATION_DEFAULT_MARKER,
            complete_result["recoveryRules"],
        )

    def test_complete_recovery_derives_matching_money_management_cap(self) -> None:
        source = valid_brief()
        source["recoveryRules"] = (
            "RecoveryMode=grid_martingale; trigger=100 adverse points; "
            "spacing=100 points; lot multiplier=1.2; max=3 levels; "
            "basket TP=20 points; reset after basket close."
        )
        source["moneyManagement"] = "Use fixed lot 0.01."

        first = BRIEF.apply_strategy_brief_implementation_defaults(source)
        second = BRIEF.apply_strategy_brief_implementation_defaults(first)

        self.assertEqual(second, first)
        self.assertIn(
            BRIEF.RECOVERY_POSITION_CAP_BINDING_MARKER,
            first["moneyManagement"],
        )
        self.assertIn(
            "MaxOpenPositionsPerSymbolMagic=3",
            first["moneyManagement"],
        )
        self.assertNotIn(
            BRIEF.IMPLEMENTATION_DEFAULT_POSITION_CAP,
            first["moneyManagement"],
        )
        normalized = BRIEF.normalize_strategy_brief(first)
        self.assertEqual(
            BRIEF._requested_position_cap(normalized["moneyManagement"]),
            3,
        )

    def test_recovery_and_money_management_cap_conflict_fails_closed(self) -> None:
        source = valid_brief()
        source["recoveryRules"] = (
            "RecoveryMode=grid; trigger=100 adverse points; spacing=100 points; "
            "same fixed lot; max=3 levels; basket TP=20 points; reset after "
            "basket close."
        )
        source["moneyManagement"] = (
            "FixedLot=0.01; MaxOpenPositionsPerSymbolMagic=1."
        )

        with self.assertRaises(BRIEF.StrategyBriefValidationError) as caught:
            BRIEF.normalize_strategy_brief(source)

        issue = next(
            item
            for item in caught.exception.issues
            if item["code"] == "BRIEF_RECOVERY_POSITION_CAP_CONFLICT"
        )
        self.assertEqual(issue["path"], "$.moneyManagement")
        self.assertIn("1 is below", issue["message"])
        self.assertIn("3 total positions", issue["message"])

        candidate_source = "#property strict\nvoid OnTick() {}\n"
        analysis = BRIEF.analyze_compact_ea_source(
            candidate_source,
            strategy_brief=source,
            strategy_brief_digest="1" * 64,
            strategy_spec_digest="2" * 64,
            source_digest=hashlib.sha256(
                candidate_source.encode("utf-8")
            ).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(analysis["checks"]["strategyBriefContract"])
        self.assertIn("ea_compact_strategy_brief_invalid", analysis["findings"])

    def test_explicit_pending_order_is_not_replaced_by_market_order(self) -> None:
        source = valid_brief()
        pending_rule = (
            "Buy Stop 10 points above previous high; Sell Stop 10 points below "
            "previous low; expire after 3 bars; one pending per Symbol+Magic."
        )
        source["orderExecution"] = pending_rule

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertEqual(result["orderExecution"], pending_rule)
        self.assertNotIn("COMPONENT=order_type", result["orderExecution"])

    def test_stop_entry_pending_order_is_not_replaced_by_market_order(self) -> None:
        source = valid_brief()
        pending_rule = (
            "Use a stop-entry pending order above the signal-bar high for Buy "
            "and below the signal-bar low for Sell; cancel after 3 bars."
        )
        source["orderExecution"] = pending_rule

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertEqual(result["orderExecution"], pending_rule)
        self.assertNotIn("Market Buy", result["orderExecution"])
        self.assertNotIn("COMPONENT=order_type", result["orderExecution"])

    def test_explicit_no_recovery_strategy_does_not_receive_recovery_default(self) -> None:
        source = valid_brief()
        source["recoveryRules"] = (
            "No recovery strategy; do not use Grid, Martingale, Averaging, "
            "Hedging, adding to losers, or loss-based lot escalation."
        )

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertIn("RecoveryMode=none", result["recoveryRules"])
        self.assertIn("No recovery strategy", result["recoveryRules"])
        self.assertNotIn(
            BRIEF.IMPLEMENTATION_DEFAULT_MARKER,
            result["recoveryRules"],
        )
        self.assertNotIn("COMPONENT=recovery", result["recoveryRules"])

    def test_no_grid_alone_still_receives_safe_no_recovery_default(self) -> None:
        source = valid_brief()
        source["recoveryRules"] = "No Grid."

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertIn("No Grid", result["recoveryRules"])
        self.assertIn("RecoveryMode=none", result["recoveryRules"])
        self.assertIn("COMPONENT=recovery", result["recoveryRules"])

    def test_paired_atr_stop_loss_and_take_profit_are_both_preserved(self) -> None:
        for paired_rule in (
            "SL/TP use 1.5 and 3.0 times ATR(14)[1]; TrailingStop=false; BreakEven=false; Partial Close=false.",
            "Hard stop and profit target are 1.5 ATR and 3.0 ATR respectively; trailing off; break-even off; partial close off.",
            "Stop loss and profit target use ATR multiples 1.5 and 3.0 respectively; trailing off; break-even off; partial close off.",
        ):
            with self.subTest(paired_rule=paired_rule):
                source = valid_brief()
                source["exitRules"] = paired_rule
                result = BRIEF.apply_strategy_brief_implementation_defaults(source)
                self.assertEqual(result["exitRules"], paired_rule)
                self.assertNotIn("COMPONENT=stop_loss", result["exitRules"])
                self.assertNotIn("COMPONENT=take_profit", result["exitRules"])

    def test_partial_exit_components_default_only_the_unresolved_component(self) -> None:
        source = valid_brief()
        source["exitRules"] = (
            "StopLoss=20 pips; TakeProfit=40 pips; trailing stop activates "
            "after 30 pips and trails by 10 pips; BreakEven "
            "not_publicly_stated; PartialClose=50% at 1R."
        )

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertNotIn("COMPONENT=stop_loss", result["exitRules"])
        self.assertNotIn("COMPONENT=take_profit", result["exitRules"])
        self.assertNotIn("COMPONENT=trailing_stop", result["exitRules"])
        self.assertIn("COMPONENT=break_even", result["exitRules"])
        self.assertNotIn("COMPONENT=partial_close", result["exitRules"])
        self.assertIn("BreakEven=false", result["exitRules"])

    def test_natural_language_exit_management_is_preserved(self) -> None:
        source = valid_brief()
        source["exitRules"] = (
            "Hard stop 20 pips and profit target 40 pips; move stop to BE at "
            "1R; take half off at 1R; trail the remainder by 1 ATR."
        )

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        for component in (
            "stop_loss",
            "take_profit",
            "trailing_stop",
            "break_even",
            "partial_close",
        ):
            self.assertNotIn(f"COMPONENT={component}", result["exitRules"])

    def test_stop_entry_without_pending_word_is_preserved(self) -> None:
        source = valid_brief()
        source["orderExecution"] = (
            "Use stop-entry orders 10 pips beyond the breakout and cancel "
            "unfilled orders after 3 bars."
        )

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertEqual(result["orderExecution"], source["orderExecution"])
        self.assertNotIn("COMPONENT=order_type", result["orderExecution"])

    def test_common_money_management_wording_is_preserved_component_wise(self) -> None:
        cases = (
            ("Use a fixed lot 0.10; maximum three concurrent trades.", False),
            ("Trade 0.10 lots per signal; maximum three concurrent trades.", False),
            ("Use RiskPercent=0.5%; at most 3 open trades.", True),
        )
        for money_management, needs_formula in cases:
            with self.subTest(money_management=money_management):
                source = valid_brief()
                source["moneyManagement"] = money_management
                result = BRIEF.apply_strategy_brief_implementation_defaults(source)
                self.assertNotIn("RiskPercent=1.0", result["moneyManagement"])
                self.assertNotIn(
                    "MaxOpenPositionsPerSymbolMagic=1",
                    result["moneyManagement"],
                )
                self.assertEqual(
                    "COMPONENT=lot_calculation" in result["moneyManagement"],
                    needs_formula,
                )

    def test_unresolved_lot_formula_receives_only_formula_default(self) -> None:
        source = valid_brief()
        source["moneyManagement"] = (
            "RiskPercent=0.5% of Equity; TickValue formula not specified; "
            "maximum 2 positions."
        )

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertIn("COMPONENT=lot_calculation", result["moneyManagement"])
        self.assertNotIn("RiskPercent=1.0", result["moneyManagement"])
        self.assertNotIn("COMPONENT=position_cap", result["moneyManagement"])

    def test_unresolved_lot_size_receives_safe_fixed_lot_default(self) -> None:
        for money_management in (
            "Lot=to be decided; maximum 1 trade.",
            "Lot=unknown; maximum 1 trade.",
        ):
            with self.subTest(money_management=money_management):
                source = valid_brief()
                source["moneyManagement"] = money_management
                result = BRIEF.apply_strategy_brief_implementation_defaults(source)
                self.assertIn("COMPONENT=risk_sizing", result["moneyManagement"])
                self.assertIn("PositionSizingMode=fixed_lot", result["moneyManagement"])
                self.assertIn("FixedLot=0.01", result["moneyManagement"])

    def test_missing_details_receive_ea_safe_optimization_inputs(self) -> None:
        source = valid_brief()
        source.update({
            "entryRules": "Buy when the fast average crosses above the slow average.",
            "recoveryRules": "not_publicly_stated",
            "exitRules": "not_publicly_stated",
            "moneyManagement": "not_publicly_stated",
            "orderExecution": "not_publicly_stated",
            "additionalNotes": "Source note must remain.",
        })

        first = BRIEF.apply_strategy_brief_implementation_defaults(source)
        second = BRIEF.apply_strategy_brief_implementation_defaults(first)

        self.assertEqual(second, first)
        self.assertEqual(first["entryRules"], source["entryRules"])
        self.assertIn("StopLossPoints=300", first["exitRules"])
        self.assertIn("TakeProfitPoints=600", first["exitRules"])
        self.assertIn("PositionSizingMode=fixed_lot", first["moneyManagement"])
        self.assertIn("FixedLot=0.01", first["moneyManagement"])
        self.assertIn("MaxOpenPositionsPerSymbolMagic=1", first["moneyManagement"])
        self.assertIn("RecoveryMode=none", first["recoveryRules"])
        self.assertIn("SignalBarShift=1", first["orderExecution"])
        self.assertIn("TradeOnNewBar=true", first["orderExecution"])
        self.assertIn("Source note must remain.", first["additionalNotes"])
        self.assertIn("INPUT_METADATA_VERSION=ea-optimization-inputs-v1", first["additionalNotes"])
        for metadata in (
            "FixedLot(double,default=0.01,start=0.01,step=0.01,stop=0.10)",
            "RiskPercent(double,optional percent_equity,default=1.0,start=0.25,step=0.25,stop=3.0)",
            "StopLossPoints(int,default=300,start=100,step=100,stop=1000)",
            "TakeProfitPoints(int,default=600,start=200,step=200,stop=2000)",
            "MaxOpenPositionsPerSymbolMagic(int,default=1,start=1,step=1,stop=3)",
        ):
            self.assertIn(metadata, first["additionalNotes"])
        self.assertNotIn("StopLossATR=", first["exitRules"])
        self.assertNotIn("TakeProfitATR=", first["exitRules"])

    def test_explicit_source_values_and_intrabar_timing_are_not_overwritten(self) -> None:
        source = valid_brief()
        source.update({
            "entryRules": "Evaluate every tick; Buy when Close[0] rises above EMA[0].",
            "exitRules": (
                "Source-backed StopLoss=20 pips; TakeProfit=45 pips; "
                "TrailingStop=false; BreakEven=false; PartialClose=false."
            ),
            "moneyManagement": (
                "Source-backed RiskPercent=0.5% of Equity; maximum 3 concurrent "
                "positions per Symbol+Magic."
            ),
            "orderExecution": "Evaluate intrabar and send Buy Stop 10 pips above High[0].",
        })

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertIn("StopLoss=20 pips", result["exitRules"])
        self.assertIn("TakeProfit=45 pips", result["exitRules"])
        self.assertNotIn("StopLossPoints=300", result["exitRules"])
        self.assertNotIn("TakeProfitPoints=600", result["exitRules"])
        self.assertIn("RiskPercent=0.5%", result["moneyManagement"])
        self.assertIn("maximum 3 concurrent positions", result["moneyManagement"])
        self.assertNotIn("FixedLot=0.01", result["moneyManagement"])
        self.assertNotIn("MaxOpenPositionsPerSymbolMagic=1", result["moneyManagement"])
        self.assertIn("Buy Stop 10 pips", result["orderExecution"])
        self.assertNotIn("SignalBarShift=1", result["orderExecution"])
        self.assertNotIn("TradeOnNewBar=true", result["orderExecution"])
        self.assertIn("INPUT_METADATA_VERSION=ea-optimization-inputs-v1", result["additionalNotes"])

    def test_isolated_broker_tokens_do_not_count_as_lot_formula(self) -> None:
        for money_management in (
            "Risk 2% of Equity; TickValue is provided by broker; max 1 trade.",
            "Risk 2% of Equity; VolumeStep=0.01; max 1 trade.",
        ):
            with self.subTest(money_management=money_management):
                source = valid_brief()
                source["moneyManagement"] = money_management
                result = BRIEF.apply_strategy_brief_implementation_defaults(source)
                self.assertIn("COMPONENT=lot_calculation", result["moneyManagement"])

    def test_common_position_cap_phrases_are_preserved(self) -> None:
        for money_management in (
            "Fixed lot 0.10; Maximum positions per symbol is 3.",
            "Fixed lot 0.10; Maximum number of open positions is 3.",
            "Fixed lot 0.10; The position limit is 3.",
            "Fixed lot 0.10; Never hold over 3 positions.",
            "ล็อตคงที่ 0.10; จำกัดจำนวนออเดอร์ 3 รายการ",
        ):
            with self.subTest(money_management=money_management):
                source = valid_brief()
                source["moneyManagement"] = money_management
                result = BRIEF.apply_strategy_brief_implementation_defaults(source)
                self.assertNotIn("COMPONENT=position_cap", result["moneyManagement"])
                self.assertNotIn(
                    "MaxOpenPositionsPerSymbolMagic=1",
                    result["moneyManagement"],
                )

    def test_incomplete_recovery_without_basket_exit_is_disabled(self) -> None:
        for recovery_rules in (
            "Martingale after 2 losses; spacing 100 points; lot multiplier 2; "
            "max 3 levels; each order has stop loss 50 points; reset after all positions close.",
            "Grid starts after a loss; spacing 1 ATR; lot multiplier 1.2; "
            "level 3 uses a filter; take profit on each trade; reset when flat.",
        ):
            with self.subTest(recovery_rules=recovery_rules):
                source = valid_brief()
                source["recoveryRules"] = recovery_rules
                result = BRIEF.apply_strategy_brief_implementation_defaults(source)
                self.assertIn("COMPONENT=recovery", result["recoveryRules"])
                self.assertIn("RecoveryMode=none", result["recoveryRules"])

    def test_unresolved_order_choice_receives_market_default(self) -> None:
        for order_text in (
            "Pending order type not disclosed.",
            "Use market or pending orders; user decides.",
            "Pending orders are disabled.",
            "Do not use pending orders.",
            "No Buy Stop or Sell Stop.",
        ):
            with self.subTest(order_text=order_text):
                source = valid_brief()
                source["orderExecution"] = order_text
                result = BRIEF.apply_strategy_brief_implementation_defaults(source)
                self.assertIn("COMPONENT=order_type", result["orderExecution"])
                self.assertIn("Market Buy/Sell", result["orderExecution"])

    def test_missing_order_type_preserves_source_direction_and_timing(self) -> None:
        source = valid_brief()
        source["entryRules"] = "Long-only; buy breakout; never sell short."
        source["orderExecution"] = (
            "Enter immediately intrabar when Ask breaks the prior high; "
            "order type not specified."
        )

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertIn("COMPONENT=order_type", result["orderExecution"])
        self.assertIn("ยึดทิศทาง Buy/Sell และจังหวะเข้าจากกฎต้นทาง", result["orderExecution"])
        self.assertIn("immediately intrabar", result["orderExecution"])

    def test_missing_recovery_evidence_is_not_misread_as_explicit_none(self) -> None:
        for recovery_text in (
            "No evidence of a recovery strategy was found.",
            "No documented recovery strategy.",
            "No recovery rules were found in the two sources.",
            "No recovery section is available in either source.",
            "No recovery method was provided by the sources.",
            "No recovery rules could be located.",
            "No Grid; Martingale values are user discretion; section 2.",
        ):
            with self.subTest(recovery_text=recovery_text):
                source = valid_brief()
                source["recoveryRules"] = recovery_text
                result = BRIEF.apply_strategy_brief_implementation_defaults(source)
                self.assertIn("COMPONENT=recovery", result["recoveryRules"])
                self.assertIn("RecoveryMode=none", result["recoveryRules"])

    def test_source_explicit_no_recovery_remains_source_derived(self) -> None:
        for recovery_text in (
            "No recovery is used by this system.",
            "Do not use recovery.",
            "Disable recovery.",
            "Recovery=none.",
            "Recovery is disabled.",
            "Never use recovery.",
            "ห้ามแก้ไม้",
        ):
            with self.subTest(recovery_text=recovery_text):
                source = valid_brief()
                source["recoveryRules"] = recovery_text
                result = BRIEF.apply_strategy_brief_implementation_defaults(source)
                self.assertTrue(
                    result["recoveryRules"].startswith("RecoveryMode=none")
                )
                self.assertNotIn("COMPONENT=recovery", result["recoveryRules"])

    def test_conditional_no_recovery_does_not_disable_later_recovery(self) -> None:
        for recovery_text in (
            "No recovery on the first loss; after 2 consecutive losses use Martingale with spacing 100 points, lot multiplier 2, max 3 levels, basket TP 50 points, reset after basket close.",
            "No recovery until drawdown reaches 10%; then add Grid after drawdown, spacing 100 points, same lot, max 3 levels, basket TP 50 points, reset after basket close.",
        ):
            with self.subTest(recovery_text=recovery_text):
                source = valid_brief()
                source["recoveryRules"] = recovery_text
                result = BRIEF.apply_strategy_brief_implementation_defaults(source)
                self.assertFalse(result["recoveryRules"].startswith("RecoveryMode=none"))
                self.assertNotIn("COMPONENT=recovery", result["recoveryRules"])

    def test_paired_protection_shorthand_resolves_each_side_independently(self) -> None:
        for exit_text in (
            "SL/TP: SL=20 pips; TP not specified; TrailingStop=false; BreakEven=false; PartialClose=false.",
            "Stop Loss / Take Profit = 20 pips / not specified; TrailingStop=false; BreakEven=false; PartialClose=false.",
        ):
            with self.subTest(exit_text=exit_text):
                source = valid_brief()
                source["exitRules"] = exit_text
                result = BRIEF.apply_strategy_brief_implementation_defaults(source)
                self.assertNotIn("COMPONENT=stop_loss", result["exitRules"])
                self.assertIn("COMPONENT=take_profit", result["exitRules"])

    def test_source_money_management_wording_is_not_overwritten(self) -> None:
        cases = (
            ("Risk per trade is 2 percent of account equity; allow one trade at a time.", True),
            ("Risk per trade is two percent of Equity; maximum 3 positions.", True),
            ("ใช้ล็อตคงที่ 0.10 และเปิดพร้อมกันไม่เกิน 3 ไม้ต่อ Symbol+Magic", False),
            ("never hold more than 3 positions; fixed lot 0.10", False),
            ("limit total open positions to 3; fixed lot 0.10", False),
            ("three concurrent trades; fixed lot 0.10", False),
            ("A maximum of 3 positions may be open at once; fixed lot 0.10", False),
            ("Maximum open positions: 3; fixed lot 0.10", False),
            ("Limit concurrent trades to no more than 3; fixed lot 0.10", False),
            ("Only 3 simultaneous positions; fixed lot 0.10", False),
            ("Allow one open position and one pending order per symbol; fixed lot 0.10", False),
        )
        for money_text, formula_default_expected in cases:
            with self.subTest(money_text=money_text):
                source = valid_brief()
                source["moneyManagement"] = money_text
                result = BRIEF.apply_strategy_brief_implementation_defaults(source)
                self.assertNotIn("COMPONENT=risk_sizing", result["moneyManagement"])
                self.assertNotIn("COMPONENT=position_cap", result["moneyManagement"])
                self.assertEqual(
                    "COMPONENT=lot_calculation" in result["moneyManagement"],
                    formula_default_expected,
                )
        self.assertEqual(
            BRIEF._requested_position_cap(
                "Allow one open position and one pending order per symbol."
            ),
            2,
        )

    def test_thai_exit_components_are_preserved(self) -> None:
        source = valid_brief()
        source["exitRules"] = (
            "ตั้งจุดหยุดขาดทุน 200 จุด และเป้าหมายกำไร 400 จุด; "
            "เลื่อนจุดตัดขาดทุนตามหลังราคา 100 จุด; ปิดบางส่วน 50% ที่ 1R; "
            "BreakEven=false."
        )

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        for component in (
            "stop_loss",
            "take_profit",
            "trailing_stop",
            "break_even",
            "partial_close",
        ):
            self.assertNotIn(f"COMPONENT={component}", result["exitRules"])

    def test_detailed_unnamed_recovery_is_preserved(self) -> None:
        source = valid_brief()
        recovery = (
            "After 2 losses add another position every 100 points; multiply lot "
            "by 1.2; maximum 3 levels; basket TP 50 points and SL 150 points; "
            "reset after the basket closes."
        )
        source["recoveryRules"] = recovery

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertEqual(result["recoveryRules"], recovery)
        self.assertNotIn("COMPONENT=recovery", result["recoveryRules"])

    def test_plain_english_be_word_does_not_hide_break_even_default(self) -> None:
        source = valid_brief()
        source["exitRules"] = (
            "StopLoss=20 pips; TakeProfit=40 pips; position should be closed on "
            "the opposite signal; TrailingStop=false; PartialClose=false."
        )

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertIn("COMPONENT=break_even", result["exitRules"])
        self.assertIn("BreakEven=false", result["exitRules"])

    def test_vague_exit_language_receives_all_missing_component_defaults(self) -> None:
        source = valid_brief()
        source["exitRules"] = (
            "Stop loss and take profit are to be determined by price action; "
            "trailing stop details unavailable; break-even should be considered; "
            "partial close optional."
        )

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        for component in (
            "stop_loss",
            "take_profit",
            "trailing_stop",
            "break_even",
            "partial_close",
        ):
            self.assertIn(f"COMPONENT={component}", result["exitRules"])

    def test_unbound_exit_counts_do_not_hide_protection_defaults(self) -> None:
        cases = (
            ("Apply a stop loss to all 2 positions; take profit not specified.", "stop_loss"),
            ("Place stop loss after bar 1 closes; take profit not specified.", "stop_loss"),
            ("Stop loss uses indicator buffer 1; take profit not specified.", "stop_loss"),
            ("Apply profit target to all 2 positions; stop loss not specified.", "take_profit"),
        )
        for exit_text, component in cases:
            with self.subTest(exit_text=exit_text):
                source = valid_brief()
                source["exitRules"] = exit_text
                result = BRIEF.apply_strategy_brief_implementation_defaults(source)
                self.assertIn(f"COMPONENT={component}", result["exitRules"])

    def test_additional_source_exit_notations_are_not_overwritten(self) -> None:
        for exit_text in (
            "StopLossPoints=200; TakeProfitPoints=400; TrailingStop=false; BreakEven=false; PartialClose=false.",
            "Initial stop 20 pips; reward target 2R; TrailingStop=false; BreakEven=false; PartialClose=false.",
            "Hard-stop at 20 pips; target at 2R; TrailingStop=false; BreakEven=false; PartialClose=false.",
            "20-pip stop / 40-pip target; TrailingStop=false; BreakEven=false; PartialClose=false.",
        ):
            with self.subTest(exit_text=exit_text):
                source = valid_brief()
                source["exitRules"] = exit_text
                result = BRIEF.apply_strategy_brief_implementation_defaults(source)
                self.assertNotIn("COMPONENT=stop_loss", result["exitRules"])
                self.assertNotIn("COMPONENT=take_profit", result["exitRules"])

    def test_explicit_unlimited_or_multiple_positions_are_not_replaced_by_cap_one(self) -> None:
        for cap_text in (
            "Use a fixed lot 0.10 and allow unlimited concurrent trades.",
            "Use a fixed lot 0.10 and allow multiple positions.",
        ):
            with self.subTest(cap_text=cap_text):
                source = valid_brief()
                source["moneyManagement"] = cap_text
                result = BRIEF.apply_strategy_brief_implementation_defaults(source)
                self.assertNotIn("COMPONENT=position_cap", result["moneyManagement"])
                self.assertNotIn("MaxOpenPositionsPerSymbolMagic=1", result["moneyManagement"])

    def test_complete_recovery_can_use_deterministic_non_numeric_phrases(self) -> None:
        source = valid_brief()
        recovery = (
            "Martingale after each loss; spacing=100 points; same lot; max=3; "
            "basket closes on opposite signal; reset after basket close."
        )
        source["recoveryRules"] = recovery

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertEqual(result["recoveryRules"], recovery)
        self.assertNotIn("COMPONENT=recovery", result["recoveryRules"])

    def test_current_points_v2_defaults_require_bound_inputs_and_broker_floor(self) -> None:
        brief = valid_brief()
        brief.update({
            "recoveryRules": "not_publicly_stated",
            "exitRules": "not_publicly_stated",
            "moneyManagement": "not_publicly_stated",
            "orderExecution": "not_publicly_stated",
        })
        brief = BRIEF.normalize_strategy_brief(
            BRIEF.apply_strategy_brief_implementation_defaults(brief)
        )
        brief_digest = BRIEF.compute_strategy_brief_digest(brief)
        source = f'''#property strict
#property description "EA_STRATEGY_BRIEF_SHA256:{brief_digest}"
#define SIGNAL_NONE -1
input double FixedLot = 0.01;
input int StopLossPoints = 300;
input int TakeProfitPoints = 600;
input int ExecutionBufferPoints = 2;
input int MaxOpenPositionsPerSymbolMagic = 1;
input int MagicNumber = 4186001;
int OnInit() {{ return(INIT_SUCCEEDED); }}
int CountManagedPositions() {{
  int count = 0;
  for(int i=OrdersTotal()-1; i>=0; i--) {{
    if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
    if(OrderSymbol() == Symbol() && OrderMagicNumber() == MagicNumber) count++;
  }}
  return(count);
}}
void OnTick() {{
  static datetime lastBar = 0;
  datetime currentBar = Time[0];
  if(currentBar <= 0 || currentBar == lastBar) return;
  lastBar = currentBar;
  if(Bars < 3) return;
  double fast2 = iMA(Symbol(), Period(), 10, 0, MODE_EMA, PRICE_CLOSE, 2);
  double fast1 = iMA(Symbol(), Period(), 10, 0, MODE_EMA, PRICE_CLOSE, 1);
  double slow2 = iMA(Symbol(), Period(), 60, 0, MODE_EMA, PRICE_CLOSE, 2);
  double slow1 = iMA(Symbol(), Period(), 60, 0, MODE_EMA, PRICE_CLOSE, 1);
  int signal = SIGNAL_NONE;
  if(fast2 <= slow2 && fast1 > slow1) signal = OP_BUY;
  if(fast2 >= slow2 && fast1 < slow1) signal = OP_SELL;
  if(signal == SIGNAL_NONE) return;
  if(CountManagedPositions() >= MaxOpenPositionsPerSymbolMagic) return;
  double minimumLot = MarketInfo(Symbol(), MODE_MINLOT);
  double maximumLot = MarketInfo(Symbol(), MODE_MAXLOT);
  double volumeStep = MarketInfo(Symbol(), MODE_LOTSTEP);
  if(FixedLot <= 0 || minimumLot <= 0 || maximumLot <= 0 || volumeStep <= 0) return;
  if(FixedLot < minimumLot || FixedLot > maximumLot) return;
  if(MathAbs(FixedLot / volumeStep - MathFloor(FixedLot / volumeStep + 0.5)) > 0.000001) return;
  if(AccountFreeMarginCheck(Symbol(), signal, FixedLot) <= 0) return;
  double entryPrice = signal == OP_BUY ? Ask : Bid;
  double brokerFloor = (MarketInfo(Symbol(), MODE_STOPLEVEL) + ExecutionBufferPoints) * Point;
  double stopDistance = MathMax(StopLossPoints * Point, brokerFloor);
  double takeDistance = MathMax(TakeProfitPoints * Point, brokerFloor);
  if(stopDistance <= 0 || takeDistance <= 0) return;
  double stopLoss = signal == OP_BUY ? entryPrice - stopDistance : entryPrice + stopDistance;
  double takeProfit = signal == OP_BUY ? entryPrice + takeDistance : entryPrice - takeDistance;
  Comment("EMA crossover signal=", signal, " Balance=", AccountBalance(),
          " Equity=", AccountEquity(), " Spread=", MarketInfo(Symbol(), MODE_SPREAD));
  OrderSend(Symbol(), signal, FixedLot, entryPrice, 3, stopLoss, takeProfit,
            "points-v2", MagicNumber, 0);
}}
'''

        def analyze(candidate: str) -> dict:
            return BRIEF.analyze_compact_ea_source(
                candidate,
                strategy_brief=brief,
                strategy_brief_digest=brief_digest,
                strategy_spec_digest="1" * 64,
                source_digest=hashlib.sha256(candidate.encode("utf-8")).hexdigest(),
                target_platform="mt4",
            )

        analysis = analyze(source)
        self.assertTrue(analysis["complete"], analysis)
        self.assertTrue(analysis["checks"]["exitAndProtectionExecution"])
        self.assertTrue(analysis["checks"]["moneyManagementExecution"])
        self.assertTrue(analysis["checks"]["riskSizingExecution"])
        self.assertTrue(analysis["checks"]["executionSafety"])

        unsafe_cases = (
            (
                "external_import",
                '#import "kernel32.dll"\nint GetTickCount();\n#import\n',
                "ea_external_code_dependency_forbidden",
                True,
            ),
            (
                "external_include",
                '#include <stdlib.mqh>\n',
                "ea_external_code_dependency_forbidden",
                True,
            ),
            (
                "embedded_resource",
                '#resource "\\\\Files\\\\payload.bin"\n',
                "ea_external_code_dependency_forbidden",
                True,
            ),
            (
                "tester_indicator_dependency",
                '#property tester_indicator "unreviewed.ex4"\n',
                "ea_external_code_dependency_forbidden",
                True,
            ),
            (
                "tester_library_dependency",
                '#property tester_library "unreviewed.dll"\n',
                "ea_external_code_dependency_forbidden",
                True,
            ),
            (
                "custom_indicator_dependency",
                'double unsafeValue = iCustom(Symbol(), Period(), "unreviewed", 0, 1);',
                "ea_external_code_dependency_forbidden",
                False,
            ),
            (
                "host_file_delete",
                'FileDelete("unsafe.txt");',
                "ea_host_io_forbidden",
                False,
            ),
            (
                "host_screenshot_write",
                'WindowScreenShot("unsafe.gif", 640, 480);',
                "ea_host_io_forbidden",
                False,
            ),
            (
                "network_web_request",
                'WebRequest("GET", "https://invalid.test", "", 1, body, result, headers);',
                "ea_network_io_forbidden",
                False,
            ),
            (
                "network_socket",
                "int unsafeSocket = SocketCreate();",
                "ea_network_io_forbidden",
                False,
            ),
            (
                "terminal_close",
                "TerminalClose(0);",
                "ea_terminal_control_forbidden",
                False,
            ),
            (
                "expert_remove",
                "ExpertRemove();",
                "ea_terminal_control_forbidden",
                False,
            ),
            (
                "template_mutation",
                'ChartApplyTemplate(0, "unsafe.tpl");',
                "ea_terminal_control_forbidden",
                False,
            ),
            (
                "tester_withdrawal",
                "TesterWithdrawal(10.0);",
                "ea_terminal_control_forbidden",
                False,
            ),
            (
                "timer_registration",
                "EventSetTimer(1);",
                "ea_terminal_control_forbidden",
                False,
            ),
            (
                "object_deletion",
                'ObjectDelete(0, "unsafe");',
                "ea_terminal_control_forbidden",
                False,
            ),
            (
                "persistent_global_mutation",
                'GlobalVariableSet("unsafe", 1.0);',
                "ea_persistent_global_mutation_forbidden",
                False,
            ),
            (
                "external_notification",
                'SendNotification("unsafe");',
                "ea_external_notification_forbidden",
                False,
            ),
            (
                "blocking_sleep",
                "Sleep(1000);",
                "ea_modal_or_blocking_call_forbidden",
                False,
            ),
        )
        for label, injected, prepend in (
            (label, injected, prepend)
            for label, injected, _finding, prepend in unsafe_cases
        ):
            finding = next(
                expected
                for candidate_label, _candidate, expected, _prepend in unsafe_cases
                if candidate_label == label
            )
            candidate = (
                injected + source
                if prepend
                else source.replace(
                    "void OnTick() {",
                    "void OnTick() {\n  " + injected,
                    1,
                )
            )
            with self.subTest(unsafe=label):
                rejected = analyze(candidate)
                self.assertFalse(rejected["checks"]["executionSafety"])
                self.assertFalse(rejected["complete"])
                self.assertIn(finding, rejected["findings"])

        macro_alias_cases = (
            ("host", "FileDelete", 'SAFE_CALL("x");', "ea_host_io_forbidden"),
            ("network", "WebRequest", "SAFE_CALL();", "ea_network_io_forbidden"),
            ("terminal", "TerminalClose", "SAFE_CALL(0);", "ea_terminal_control_forbidden"),
            ("notification", "SendNotification", 'SAFE_CALL("x");', "ea_external_notification_forbidden"),
            ("blocking", "Sleep", "SAFE_CALL(1);", "ea_modal_or_blocking_call_forbidden"),
            ("global", "GlobalVariableSet", 'SAFE_CALL("x", 1);', "ea_persistent_global_mutation_forbidden"),
            ("template", "ChartApplyTemplate", 'SAFE_CALL(0, "x");', "ea_terminal_control_forbidden"),
        )
        for label, forbidden_identifier, call, finding in macro_alias_cases:
            candidate = (
                f"#define SAFE_CALL {forbidden_identifier}\n"
                + source.replace(
                    "void OnTick() {",
                    "void OnTick() {\n  " + call,
                    1,
                )
            )
            with self.subTest(macro_alias=label):
                rejected = analyze(candidate)
                self.assertFalse(rejected["checks"]["executionSafety"])
                self.assertIn(finding, rejected["findings"])

        token_paste = (
            "#define JOIN_UNSAFE(a,b) a ## b\n"
            + source.replace(
                "void OnTick() {",
                "void OnTick() {\n  JOIN_UNSAFE(Fi,leDelete)(\"x\");",
                1,
            )
        )
        token_paste_analysis = analyze(token_paste)
        self.assertFalse(token_paste_analysis["checks"]["executionSafety"])
        self.assertIn(
            "ea_preprocessor_indirection_forbidden",
            token_paste_analysis["findings"],
        )

        macro_event_alias = (
            "#define HIDDEN_EVT OnTrade\n"
            + source.replace(
                "void OnTick() {",
                "void OnTick() {\n  if(false) OpenTradeFromBothEvents();",
                1,
            )
            + "\nvoid HIDDEN_EVT() { OpenTradeFromBothEvents(); }\n"
            + "void OpenTradeFromBothEvents() { OrderSend(Symbol(), OP_BUY, 99, "
            + "Ask, 3, Ask-Point, Ask+Point, \"macro event\", 1, 0); }\n"
        )
        macro_event_analysis = analyze(macro_event_alias)
        self.assertFalse(macro_event_analysis["checks"]["executionSafety"])
        self.assertFalse(macro_event_analysis["complete"])
        self.assertIn(
            "ea_preprocessor_indirection_forbidden",
            macro_event_analysis["findings"],
        )

        return_type_event_alias = (
            "#define RET void\n"
            + source
            + "\nRET OnTrade() { OrderSend(Symbol(), OP_BUY, 99, Ask, 3, "
            + "Ask-Point, Ask+Point, \"typed macro event\", 1, 0); }\n"
        )
        return_type_event_analysis = analyze(return_type_event_alias)
        self.assertFalse(return_type_event_analysis["checks"]["executionSafety"])
        self.assertFalse(return_type_event_analysis["checks"]["expertAdvisorLifecycle"])
        self.assertIn(
            "ea_preprocessor_indirection_forbidden",
            return_type_event_analysis["findings"],
        )

        continued_event_alias = (
            "#define HIDDEN_EVT \\\nOnTrade\n" + source
        )
        continued_event_analysis = analyze(continued_event_alias)
        self.assertFalse(continued_event_analysis["checks"]["executionSafety"])
        self.assertIn(
            "ea_preprocessor_indirection_forbidden",
            continued_event_analysis["findings"],
        )

        bare_cr_trade_alias = source.replace(
            "input double FixedLot = 0.01;\n",
            "input double FixedLot = 0.01;\r#define DO_TRADE OrderSend\r",
            1,
        ).replace(
            "int OnInit() { return(INIT_SUCCEEDED); }",
            "int OnInit() { DO_TRADE(Symbol(), OP_BUY, 99, Ask, 3, Ask-Point, "
            "Ask+Point, \"bare cr\", 1, 0); return(INIT_SUCCEEDED); }",
            1,
        )
        bare_cr_analysis = analyze(bare_cr_trade_alias)
        self.assertFalse(bare_cr_analysis["checks"]["executionSafety"])
        self.assertIn(
            "ea_preprocessor_indirection_forbidden",
            bare_cr_analysis["findings"],
        )

        bom_cases = (
            "\ufeff#define SAFE_TRADE OrderSend\n" + source.replace(
                "int OnInit() { return(INIT_SUCCEEDED); }",
                "int OnInit() { SAFE_TRADE(Symbol(), OP_BUY, 99, Ask, 3, "
                "Ask-Point, Ask+Point, \"bom\", 1, 0); return(INIT_SUCCEEDED); }",
                1,
            ),
            "\ufeff#include <stdlib.mqh>\n" + source,
            "\ufeff#property tester_file \"payload.dat\"\n" + source,
        )
        for bom_source in bom_cases:
            with self.subTest(bom=hashlib.sha256(bom_source.encode()).hexdigest()[:8]):
                rejected = analyze(bom_source)
                self.assertFalse(rejected["checks"]["executionSafety"])
                self.assertFalse(rejected["complete"])
                self.assertIn(
                    "ea_unicode_source_control_forbidden",
                    rejected["findings"],
                )

        unbounded_loop_cases = (
            "while(true) { }",
            "while(1) { }",
            "do { } while(true);",
            "while(+1) { }",
            "while(!!true) { }",
            "while(1==1) { }",
            "while(2>1) { }",
            "while(true||false) { }",
            "while(!false) { }",
        )
        for unbounded_loop in unbounded_loop_cases:
            with self.subTest(unbounded_loop=unbounded_loop):
                candidate = source.replace(
                    "int OnInit() { return(INIT_SUCCEEDED); }",
                    f"int OnInit() {{ {unbounded_loop} return(INIT_SUCCEEDED); }}",
                    1,
                )
                rejected = analyze(candidate)
                self.assertFalse(rejected["checks"]["executionSafety"])
                self.assertFalse(rejected["complete"])
                self.assertIn(
                    "ea_unbounded_loop_forbidden",
                    rejected["findings"],
                )

        unproven_for_loop_cases = (
            "for(;;) { }",
            "for(int i=0; true; i++) { }",
            "for(int i=0; 1==1; i++) { }",
            "for(int i=0; i<MaxOpenPositionsPerSymbolMagic; i++) { }",
            "for(int i=0; i<10; i--) { }",
            "for(int i=2147483647; i>=0; i--) { }",
            "for(int i=0; i<2147483647; i++) { }",
            "for(int i=AccountBalance(); i>=0; i--) { }",
            "for(uint i=10; i>=0; i--) { }",
            "for(int i=2147483640; i<=2147483647; i++) { }",
            "for(int i=-2147483640; i>=-2147483648; i--) { }",
            "for(long i=9223372036854775800; i<=9223372036854775807; i++) { }",
            "for(long i=-9223372036854775800; i>=-9223372036854775808; i--) { }",
            "for(int i=2147483640; i<2147483645; i+=10) { }",
            "for(int i=0; i<1000; i++) { for(int j=0; j<1000; j++) { } }",
        )
        for unproven_loop in unproven_for_loop_cases:
            with self.subTest(unproven_for=unproven_loop):
                candidate = source.replace(
                    "int OnInit() { return(INIT_SUCCEEDED); }",
                    f"int OnInit() {{ {unproven_loop} return(INIT_SUCCEEDED); }}",
                    1,
                )
                rejected = analyze(candidate)
                self.assertFalse(rejected["checks"]["boundedLoopStructure"])
                self.assertFalse(rejected["complete"])
                self.assertIn(
                    "ea_for_loop_bounds_not_proven",
                    rejected["findings"],
                )

        for counter_mutation in (
            "i=1;",
            "if(i==0) i=1;",
            "i++;",
            "(i)=10;",
            "((i))=10;",
            "(i)++;",
            "(i)+=1;",
            "i|=1;",
            "ZeroMemory(i);",
        ):
            with self.subTest(for_body_counter_mutation=counter_mutation):
                candidate = source.replace(
                    "for(int i=OrdersTotal()-1; i>=0; i--) {",
                    "for(int i=OrdersTotal()-1; i>=0; i--) {\n    "
                    + counter_mutation,
                    1,
                )
                rejected = analyze(candidate)
                self.assertFalse(rejected["checks"]["boundedLoopStructure"])
                self.assertFalse(rejected["complete"])
                self.assertIn(
                    "ea_for_loop_bounds_not_proven",
                    rejected["findings"],
                )

        reference_helper_source = source.replace(
            "for(int i=OrdersTotal()-1; i>=0; i--) {",
            "for(int i=OrdersTotal()-1; i>=0; i--) {\n    ResetCounter(i);",
            1,
        ) + "\nvoid ResetCounter(int &counter) { counter=1; }\n"
        reference_helper_analysis = analyze(reference_helper_source)
        self.assertFalse(
            reference_helper_analysis["checks"]["referenceParametersAbsent"]
        )
        self.assertFalse(reference_helper_analysis["complete"])
        self.assertIn(
            "ea_reference_parameter_forbidden",
            reference_helper_analysis["findings"],
        )

        critical_guard_fragments = (
            (
                "if(currentBar <= 0 || currentBar == lastBar) return;\n"
                "  lastBar = currentBar;",
                "closed_bar",
            ),
            (
                "if(CountManagedPositions() >= MaxOpenPositionsPerSymbolMagic) return;",
                "position_cap",
            ),
            (
                "if(AccountFreeMarginCheck(Symbol(), signal, FixedLot) <= 0) return;",
                "margin",
            ),
        )
        for guard, label in critical_guard_fragments:
            with self.subTest(conditional_compilation=label):
                candidate = source.replace(
                    guard,
                    f"#if 0\n  {guard}\n  #endif",
                    1,
                )
                rejected = analyze(candidate)
                self.assertFalse(rejected["checks"]["executionSafety"])
                self.assertFalse(rejected["complete"])
                self.assertIn(
                    "ea_conditional_compilation_forbidden",
                    rejected["findings"],
                )

        constant_dead_guard_cases = (
            source.replace(
                critical_guard_fragments[0][0],
                f"if(false) {{ {critical_guard_fragments[0][0]} }}",
                1,
            ),
            source.replace(
                critical_guard_fragments[1][0],
                f"if(false) {{ {critical_guard_fragments[1][0]} }}",
                1,
            ),
            source.replace(
                critical_guard_fragments[2][0],
                f"if(false) {{ {critical_guard_fragments[2][0]} }}",
                1,
            ),
            source.replace(
                critical_guard_fragments[1][0],
                "if(false && CountManagedPositions() >= "
                "MaxOpenPositionsPerSymbolMagic) return;",
                1,
            ),
            source.replace(
                critical_guard_fragments[2][0],
                "if(false && AccountFreeMarginCheck(Symbol(), signal, "
                "FixedLot) <= 0) return;",
                1,
            ),
            *(
                source.replace(
                    critical_guard_fragments[1][0],
                    f"if({condition}) {{ {critical_guard_fragments[1][0]} }}",
                    1,
                )
                for condition in (
                    "1==0",
                    "0==1",
                    "1<0",
                    "2<1",
                    "SIGNAL_NONE!=-1",
                    "!1",
                    "!!0",
                    "(1-1)",
                    "0.0==1.0",
                )
            ),
        )
        for dead_source in constant_dead_guard_cases:
            with self.subTest(dead_branch=hashlib.sha256(dead_source.encode()).hexdigest()[:8]):
                rejected = analyze(dead_source)
                self.assertFalse(rejected["checks"]["executionSafety"])
                self.assertFalse(rejected["complete"])
                self.assertIn(
                    "ea_constant_dead_branch_forbidden",
                    rejected["findings"],
                )

        recursive_cases = (
            source.replace(
                "int OnInit() { return(INIT_SUCCEEDED); }",
                "int OnInit() { Recurse(); return(INIT_SUCCEEDED); }",
                1,
            ) + "\nvoid Recurse() { Recurse(); }\n",
            source.replace(
                "void OnTick() {",
                "void OnTick() {\n  Recurse();",
                1,
            ) + "\nvoid Recurse() { Recurse(); }\n",
            source.replace(
                "int OnInit() { return(INIT_SUCCEEDED); }",
                "int OnInit() { First(); return(INIT_SUCCEEDED); }",
                1,
            ) + "\nvoid First() { Second(); }\nvoid Second() { First(); }\n",
        )
        for recursive_source in recursive_cases:
            with self.subTest(recursion=hashlib.sha256(recursive_source.encode()).hexdigest()[:8]):
                rejected = analyze(recursive_source)
                self.assertFalse(
                    rejected["checks"]["reachableCallGraphAcyclic"]
                )
                self.assertFalse(rejected["complete"])
                self.assertIn(
                    "ea_reachable_call_cycle_forbidden",
                    rejected["findings"],
                )

        hidden_constructor = source + (
            "\nclass Evil { public: Evil() { OrderSend(Symbol(), OP_BUY, 99, "
            "Ask, 3, Ask-Point, Ask+Point, \"ctor\", 1, 0); } };\n"
            "Evil globalEvil;\n"
        )
        hidden_constructor_analysis = analyze(hidden_constructor)
        self.assertFalse(hidden_constructor_analysis["checks"]["executionSafety"])
        self.assertIn(
            "ea_user_defined_object_lifecycle_forbidden",
            hidden_constructor_analysis["findings"],
        )

        global_initializer = source + "\ndouble globalProbe = AccountBalance();\n"
        global_initializer_analysis = analyze(global_initializer)
        self.assertFalse(
            global_initializer_analysis["checks"]["globalExecutableCallsAbsent"]
        )
        self.assertFalse(global_initializer_analysis["complete"])
        self.assertIn(
            "ea_global_executable_call_forbidden",
            global_initializer_analysis["findings"],
        )

        documentation_only = source.replace(
            '"EMA crossover signal="',
            '"docs #import FileDelete WebRequest TerminalClose ExpertRemove Sleep="',
        ) + (
            "\n// #include <unsafe.mqh> FileDelete(\"x\"); WebRequest(); "
            "TerminalClose(0); ExpertRemove(); Sleep(1);\n"
        )
        documentation_analysis = analyze(documentation_only)
        self.assertTrue(
            documentation_analysis["checks"]["executionSafety"],
            documentation_analysis,
        )
        self.assertFalse(documentation_analysis["checks"]["displayBehavior"])
        self.assertFalse(documentation_analysis["complete"], documentation_analysis)
        self.assertIn(
            "ea_display_required_field_missing:system_name",
            documentation_analysis["findings"],
        )

        alternate_trade_path_cases = (
            (
                "timer_handler",
                "void OnTimer() { OrderSend(Symbol(), OP_BUY, 99, Ask, 3, Ask-Point, Ask+Point, \"timer\", 1, 0); }",
            ),
            (
                "deinit_handler",
                "void OnDeinit(const int reason) { OrderSend(Symbol(), OP_BUY, 99, Ask, 3, Ask-Point, Ask+Point, \"deinit\", 1, 0); }",
            ),
            (
                "chart_handler",
                "void OnChartEvent(const int id,const long &l,const double &d,const string &s) { OrderSend(Symbol(), OP_BUY, 99, Ask, 3, Ask-Point, Ask+Point, \"chart\", 1, 0); }",
            ),
            (
                "tester_handler",
                "double OnTester() { OrderSend(Symbol(), OP_BUY, 99, Ask, 3, Ask-Point, Ask+Point, \"tester\", 1, 0); return(0); }",
            ),
            (
                "dead_helper",
                "void EmergencyTrade() { OrderSend(Symbol(), OP_BUY, 99, Ask, 3, Ask-Point, Ask+Point, \"dead\", 1, 0); }",
            ),
        )
        for label, extra_source in alternate_trade_path_cases:
            with self.subTest(alternate_trade_path=label):
                rejected = analyze(source + "\n" + extra_source + "\n")
                self.assertFalse(rejected["checks"]["tradeCallGraphExclusive"])
                self.assertFalse(rejected["complete"])
                self.assertIn(
                    "ea_trade_call_outside_ontick_forbidden",
                    rejected["findings"],
                )

        shared_trade_helper = source.replace(
            "int OnInit() { return(INIT_SUCCEEDED); }",
            "int OnInit() { EmergencyTrade(); return(INIT_SUCCEEDED); }",
        ) + (
            "\nvoid EmergencyTrade() { OrderSend(Symbol(), OP_BUY, 99, Ask, 3, "
            "Ask-Point, Ask+Point, \"shared\", 1, 0); }\n"
        )
        shared_trade_helper = shared_trade_helper.replace(
            "void OnTick() {",
            "void OnTick() {\n  if(false) EmergencyTrade();",
            1,
        )
        shared_trade_analysis = analyze(shared_trade_helper)
        self.assertFalse(shared_trade_analysis["checks"]["tradeCallGraphExclusive"])
        self.assertIn(
            "ea_trade_call_outside_ontick_forbidden",
            shared_trade_analysis["findings"],
        )

        for original, replacement in (
            ("input int StopLossPoints = 300;", "input int StopLossPoints = 301;"),
            ("input int TakeProfitPoints = 600;", "input int TakeProfitPoints = 601;"),
            ("MathMax(StopLossPoints * Point, brokerFloor)", "StopLossPoints * Point"),
            ("MathMax(TakeProfitPoints * Point, brokerFloor)", "TakeProfitPoints * Point"),
        ):
            with self.subTest(replacement=replacement):
                rejected = analyze(source.replace(original, replacement))
                self.assertFalse(rejected["checks"]["exitAndProtectionExecution"])
                self.assertIn("ea_exit_or_protection_path_missing", rejected["findings"])

        atr_v1_source = source.replace(
            "input int StopLossPoints = 300;\ninput int TakeProfitPoints = 600;",
            "input int ATRPeriod = 14;\ninput double StopLossATR = 1.5;\n"
            "input double RewardRiskRatio = 2.0;",
        ).replace(
            "double stopDistance = MathMax(StopLossPoints * Point, brokerFloor);",
            "double atr = iATR(Symbol(), Period(), ATRPeriod, 1);\n"
            "  double stopDistance = MathMax(StopLossATR * atr, brokerFloor);",
        ).replace(
            "double takeDistance = MathMax(TakeProfitPoints * Point, brokerFloor);",
            "double takeDistance = stopDistance * RewardRiskRatio;",
        )
        self.assertFalse(analyze(atr_v1_source)["checks"]["exitAndProtectionExecution"])

        optional_guard_prefix = (
            "input bool EnforceSafety = false;\n"
            "input double FixedLot = 0.01;"
        )
        adversarial_optional_guards = (
            (
                "lot_positive_guard",
                (
                    "if(FixedLot <= 0 || minimumLot <= 0 || maximumLot <= 0 || "
                    "volumeStep <= 0) return;"
                ),
                "moneyManagementExecution",
                "ea_money_management_path_missing",
            ),
            (
                "position_cap_guard",
                (
                    "if(CountManagedPositions() >= "
                    "MaxOpenPositionsPerSymbolMagic) return;"
                ),
                "positionCapExecution",
                "ea_position_cap_guard_missing",
            ),
            (
                "fixed_lot_margin_guard",
                (
                    "if(AccountFreeMarginCheck(Symbol(), signal, FixedLot) <= 0) "
                    "return;"
                ),
                "moneyManagementExecution",
                "ea_margin_guard_not_fail_closed",
            ),
            (
                "new_bar_guard",
                "if(currentBar <= 0 || currentBar == lastBar) return;",
                "closedBarExecution",
                "ea_closed_bar_execution_guard_missing",
            ),
        )
        for label, guard, expected_check, expected_finding in adversarial_optional_guards:
            for wrapper_style, wrapped_guard in (
                ("braced", f"if(EnforceSafety) {{ {guard} }}"),
                ("unbraced", f"if(EnforceSafety) {guard}"),
            ):
                with self.subTest(
                    optional_safety_guard=label,
                    wrapper_style=wrapper_style,
                ):
                    self.assertIn(guard, source)
                    candidate = source.replace(
                        "input double FixedLot = 0.01;",
                        optional_guard_prefix,
                        1,
                    ).replace(
                        guard,
                        wrapped_guard,
                        1,
                    )
                    rejected = analyze(candidate)
                    self.assertFalse(rejected["complete"], rejected)
                    self.assertFalse(rejected["checks"][expected_check], rejected)
                    self.assertIn(expected_finding, rejected["findings"])

    def test_mt5_ordersendasync_is_forbidden_even_when_reachable_and_bounded(self) -> None:
        brief = valid_brief()
        brief.update({
            "recoveryRules": "not_publicly_stated",
            "exitRules": "not_publicly_stated",
            "moneyManagement": "not_publicly_stated",
            "orderExecution": "not_publicly_stated",
        })
        brief = BRIEF.normalize_strategy_brief(
            BRIEF.apply_strategy_brief_implementation_defaults(brief)
        )
        brief_digest = BRIEF.compute_strategy_brief_digest(brief)
        source = f'''#property strict
#property description "EA_STRATEGY_BRIEF_SHA256:{brief_digest}"
#define SIGNAL_NONE -1
input double FixedLot = 0.01;
input int StopLossPoints = 300;
input int TakeProfitPoints = 600;
input int ExecutionBufferPoints = 2;
input int MaxOpenPositionsPerSymbolMagic = 1;
input int MagicNumber = 4186001;
int OnInit() {{ return(INIT_SUCCEEDED); }}
int CountManagedPositions() {{
  int count = 0;
  for(int i=PositionsTotal()-1; i>=0; i--) {{
    ulong positionTicket = PositionGetTicket(i);
    if(positionTicket > 0 && PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == MagicNumber) count++;
  }}
  for(int j=OrdersTotal()-1; j>=0; j--) {{
    ulong orderTicket = OrderGetTicket(j);
    if(orderTicket > 0 && OrderGetString(ORDER_SYMBOL) == _Symbol && OrderGetInteger(ORDER_MAGIC) == MagicNumber) count++;
  }}
  return(count);
}}
void OnTick() {{
  static datetime lastBar = 0;
  datetime currentBar = iTime(_Symbol, _Period, 0);
  if(currentBar <= 0 || currentBar == lastBar) return;
  lastBar = currentBar;
  if(Bars(_Symbol, _Period) < 3) return;
  double fast2 = iClose(_Symbol, _Period, 2);
  double fast1 = iClose(_Symbol, _Period, 1);
  double slow2 = iOpen(_Symbol, _Period, 2);
  double slow1 = iOpen(_Symbol, _Period, 1);
  ENUM_ORDER_TYPE signal = (ENUM_ORDER_TYPE)SIGNAL_NONE;
  if(fast2 <= slow2 && fast1 > slow1) signal = ORDER_TYPE_BUY;
  if(fast2 >= slow2 && fast1 < slow1) signal = ORDER_TYPE_SELL;
  if((int)signal == SIGNAL_NONE) return;
  if(CountManagedPositions() >= MaxOpenPositionsPerSymbolMagic) return;
  double minimumLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
  double maximumLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
  double volumeStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
  if(FixedLot <= 0 || minimumLot <= 0 || maximumLot <= 0 || volumeStep <= 0) return;
  if(FixedLot < minimumLot || FixedLot > maximumLot) return;
  if(MathAbs(FixedLot / volumeStep - MathFloor(FixedLot / volumeStep + 0.5)) > 0.000001) return;
  double entryPrice = signal == ORDER_TYPE_BUY ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
  double marginRequired = 0;
  if(!OrderCalcMargin(signal, _Symbol, FixedLot, entryPrice, marginRequired)) return;
  double brokerFloor = (SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) + ExecutionBufferPoints) * _Point;
  double stopDistance = MathMax(StopLossPoints * _Point, brokerFloor);
  double takeDistance = MathMax(TakeProfitPoints * _Point, brokerFloor);
  if(stopDistance <= 0 || takeDistance <= 0) return;
  double stopLoss = signal == ORDER_TYPE_BUY ? entryPrice - stopDistance : entryPrice + stopDistance;
  double takeProfit = signal == ORDER_TYPE_BUY ? entryPrice + takeDistance : entryPrice - takeDistance;
  MqlTradeRequest request = {{}};
  MqlTradeResult result = {{}};
  request.action = TRADE_ACTION_DEAL;
  request.symbol = _Symbol;
  request.magic = MagicNumber;
  request.type = signal;
  request.volume = FixedLot;
  request.price = entryPrice;
  request.sl = stopLoss;
  request.tp = takeProfit;
  Comment("EMA signal=", (int)signal,
          " Balance=", AccountInfoDouble(ACCOUNT_BALANCE),
          " Equity=", AccountInfoDouble(ACCOUNT_EQUITY),
          " Spread=", SymbolInfoInteger(_Symbol, SYMBOL_SPREAD));
  OrderSend(request, result);
}}
'''

        def analyze(candidate: str) -> dict:
            return BRIEF.analyze_compact_ea_source(
                candidate,
                strategy_brief=brief,
                strategy_brief_digest=brief_digest,
                strategy_spec_digest="1" * 64,
                source_digest=hashlib.sha256(candidate.encode("utf-8")).hexdigest(),
                target_platform="mt5",
            )

        baseline = analyze(source)
        self.assertTrue(baseline["complete"], baseline)
        for label, replacement in (
            (
                "single",
                "OrderSend(request, result);\n  OrderSendAsync(request, result);",
            ),
            (
                "bounded_loop",
                "OrderSend(request, result);\n"
                "  for(int k=0; k<2; k++) { OrderSendAsync(request, result); }",
            ),
        ):
            with self.subTest(async_trade=label):
                rejected = analyze(
                    source.replace("OrderSend(request, result);", replacement, 1)
                )
                self.assertFalse(rejected["checks"]["executionSafety"], rejected)
                self.assertFalse(rejected["complete"], rejected)
                self.assertIn("ea_async_trade_forbidden", rejected["findings"])

        extra_order_open = analyze(source.replace(
            "OrderSend(request, result);",
            "OrderSend(request, result);\n"
            "  trade.OrderOpen(_Symbol, ORDER_TYPE_BUY_STOP, FixedLot, "
            "entryPrice + 100 * _Point, entryPrice - 300 * _Point, "
            "entryPrice + 600 * _Point);",
            1,
        ))
        self.assertFalse(extra_order_open["complete"], extra_order_open)

        helper_source = source.replace(
            "input int MagicNumber = 4186001;",
            "input int MagicNumber = 4186001;\n"
            "ENUM_ORDER_TYPE queuedSignal;\n"
            "double queuedEntryPrice, queuedStopLoss, queuedTakeProfit;",
            1,
        ).replace(
            "OrderSend(request, result);",
            "queuedSignal = signal; queuedEntryPrice = entryPrice;\n"
            "  queuedStopLoss = stopLoss; queuedTakeProfit = takeProfit;\n"
            "  SendManagedOrder();\n"
            "  SendManagedOrder();",
            1,
        ) + '''
void SendManagedOrder() {
  MqlTradeRequest queuedRequest = {};
  MqlTradeResult queuedResult = {};
  queuedRequest.action = TRADE_ACTION_DEAL;
  queuedRequest.symbol = _Symbol;
  queuedRequest.magic = MagicNumber;
  queuedRequest.type = queuedSignal;
  queuedRequest.volume = FixedLot;
  queuedRequest.price = queuedEntryPrice;
  queuedRequest.sl = queuedStopLoss;
  queuedRequest.tp = queuedTakeProfit;
  OrderSend(queuedRequest, queuedResult);
}
'''
        for label, candidate in (
            ("twice", helper_source),
            (
                "bounded_loop",
                helper_source.replace(
                    "SendManagedOrder();\n  SendManagedOrder();",
                    "for(int k=0; k<2; k++) { SendManagedOrder(); }",
                    1,
                ),
            ),
        ):
            with self.subTest(repeated_trade_helper=label):
                repeated = analyze(candidate)
                self.assertFalse(repeated["complete"], repeated)
                self.assertFalse(repeated["checks"]["positionCapExecution"], repeated)
                self.assertIn("ea_position_cap_guard_missing", repeated["findings"])

    def test_legacy_atr_defaults_remain_fail_closed_and_source_bound(self) -> None:
        brief = valid_brief()
        legacy_stop_tag = (
            f"[{BRIEF.IMPLEMENTATION_DEFAULT_MARKER}]"
            f"[POLICY={BRIEF.LEGACY_IMPLEMENTATION_DEFAULT_POLICY_ID}]"
            "[COMPONENT=stop_loss]"
        )
        legacy_take_tag = (
            f"[{BRIEF.IMPLEMENTATION_DEFAULT_MARKER}]"
            f"[POLICY={BRIEF.LEGACY_IMPLEMENTATION_DEFAULT_POLICY_ID}]"
            "[COMPONENT=take_profit]"
        )
        brief.update({
            "recoveryRules": "not_publicly_stated",
            "exitRules": (
                f"{legacy_stop_tag} StopLossATR=1.5 with ATRPeriod=14 at "
                "closed shift [1] and ExecutionBufferPoints=2 above broker floor; "
                f"{legacy_take_tag} TakeProfit=2R using RewardRiskRatio=2.0 from "
                "actual protected stop distance; TrailingStop=false; "
                "BreakEven=false; PartialClose=false."
            ),
            "moneyManagement": valid_brief()["moneyManagement"],
            "orderExecution": "not_publicly_stated",
        })
        brief = BRIEF.normalize_strategy_brief(
            BRIEF.apply_strategy_brief_implementation_defaults(brief)
        )
        brief_digest = BRIEF.compute_strategy_brief_digest(brief)
        source = f'''#property strict
#property description "EA_STRATEGY_BRIEF_SHA256:{brief_digest}"
#define SIGNAL_NONE -1
input double RiskPercent = 1.0;
input int ATRPeriod = 14;
input double StopLossATR = 1.5;
input double RewardRiskRatio = 2.0;
input int ExecutionBufferPoints = 2;
input int MagicNumber = 4186001;
int OnInit() {{ return(INIT_SUCCEEDED); }}
int CountManagedPositions() {{
  int count = 0;
  for(int i=OrdersTotal()-1; i>=0; i--) {{
    if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
    if(OrderSymbol() == Symbol() && OrderMagicNumber() == MagicNumber) count++;
  }}
  return(count);
}}
double CalculateRiskLot(double entryPrice, double stopLoss, int signal) {{
  double tickSize = MarketInfo(Symbol(), MODE_TICKSIZE);
  double tickValue = MarketInfo(Symbol(), MODE_TICKVALUE);
  double volumeStep = MarketInfo(Symbol(), MODE_LOTSTEP);
  double minimumLot = MarketInfo(Symbol(), MODE_MINLOT);
  double maximumLot = MarketInfo(Symbol(), MODE_MAXLOT);
  double stopDistance = MathAbs(entryPrice - stopLoss);
  if(tickSize <= 0 || tickValue <= 0 || volumeStep <= 0 || minimumLot <= 0 ||
     maximumLot <= 0 || stopDistance <= 0) return(0);
  double riskMoney = AccountEquity() * RiskPercent / 100.0;
  double lossPerLotAtSL = (stopDistance / tickSize) * tickValue;
  if(lossPerLotAtSL <= 0) return(0);
  double lot = MathFloor((riskMoney / lossPerLotAtSL) / volumeStep) * volumeStep;
  if(lot < minimumLot || lot > maximumLot) return(0);
  if(AccountFreeMarginCheck(Symbol(), signal, lot) <= 0) return(0);
  return(lot);
}}
void OnTick() {{
  static datetime lastBar = 0;
  datetime currentBar = Time[0];
  if(currentBar <= 0 || currentBar == lastBar) return;
  lastBar = currentBar;
  if(Bars < 3) return;
  int signal = SIGNAL_NONE;
  if(Close[2] <= Open[2] && Close[1] > Open[1]) signal = OP_BUY;
  if(Close[2] >= Open[2] && Close[1] < Open[1]) signal = OP_SELL;
  if(signal == SIGNAL_NONE) return;
  double entryPrice = signal == OP_BUY ? Ask : Bid;
  double atr = iATR(Symbol(), Period(), ATRPeriod, 1);
  double brokerFloor = (MarketInfo(Symbol(), MODE_STOPLEVEL) + ExecutionBufferPoints) * Point;
  double protectedDistance = MathMax(StopLossATR * atr, brokerFloor);
  if(atr <= 0 || protectedDistance <= 0) return;
  double stopLoss = signal == OP_BUY ? entryPrice - protectedDistance : entryPrice + protectedDistance;
  double takeProfit = signal == OP_BUY ? entryPrice + protectedDistance * RewardRiskRatio : entryPrice - protectedDistance * RewardRiskRatio;
  double lot = CalculateRiskLot(entryPrice, stopLoss, signal);
  if(lot <= 0.0 || CountManagedPositions() >= 1) return;
  Comment("signal=", signal, " Balance=", AccountBalance(), " Equity=", AccountEquity());
  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, "Default policy", MagicNumber, 0);
}}
'''
        source_digest = hashlib.sha256(source.encode("utf-8")).hexdigest()

        def analyze_bound(candidate_source: str, bound_brief: dict) -> dict:
            bound_digest = BRIEF.compute_strategy_brief_digest(bound_brief)
            rebound_source = source.replace(
                f"EA_STRATEGY_BRIEF_SHA256:{brief_digest}",
                f"EA_STRATEGY_BRIEF_SHA256:{bound_digest}",
            )
            if candidate_source != source:
                rebound_source = candidate_source.replace(
                    f"EA_STRATEGY_BRIEF_SHA256:{brief_digest}",
                    f"EA_STRATEGY_BRIEF_SHA256:{bound_digest}",
                )
            return BRIEF.analyze_compact_ea_source(
                rebound_source,
                strategy_brief=bound_brief,
                strategy_brief_digest=bound_digest,
                strategy_spec_digest="1" * 64,
                source_digest=hashlib.sha256(rebound_source.encode("utf-8")).hexdigest(),
                target_platform="mt4",
            )

        analysis = BRIEF.analyze_compact_ea_source(
            source,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=source_digest,
            target_platform="mt4",
        )

        lexical_code = BRIEF._indicator_lexical_views(source)[0]
        reachable_code = BRIEF._compact_ea_reachable_code(
            BRIEF._compact_ea_function_map(lexical_code)
        )
        execution_evidence = BRIEF._mql_trade_execution_evidence(
            BRIEF._mql_trade_call_records(reachable_code),
            reachable_code,
        )
        self.assertTrue(
            analysis["checks"]["exitAndProtectionExecution"],
            {
                "analysis": analysis,
                "stop_dependencies": execution_evidence[1],
                "take_dependencies": execution_evidence[2],
                "stop_tied": BRIEF._dependency_satisfies_protection_value(
                    (1.5, "atr"), execution_evidence[1][0], lexical_code
                ),
                "take_tied": BRIEF._dependency_satisfies_protection_value(
                    (2.0, "r"), execution_evidence[2][0], lexical_code
                ),
            },
        )
        self.assertTrue(analysis["checks"]["orderExecution"])
        self.assertTrue(analysis["checks"]["recoveryPolicy"])
        self.assertTrue(analysis["checks"]["positionCapExecution"])
        self.assertTrue(analysis["checks"]["riskSizingExecution"])
        self.assertTrue(analysis["checks"]["lotCalculationSafety"])
        self.assertNotIn("ea_exit_or_protection_path_missing", analysis["findings"])
        self.assertNotIn("ea_order_execution_mode_missing", analysis["findings"])
        self.assertNotIn("ea_recovery_policy_mismatch", analysis["findings"])

        unsafe_source = source.replace(" || CountManagedPositions() >= 1", "")
        unsafe_analysis = BRIEF.analyze_compact_ea_source(
            unsafe_source,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(unsafe_source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(unsafe_analysis["checks"]["positionCapExecution"])
        self.assertIn("ea_position_cap_guard_missing", unsafe_analysis["findings"])

        fixed_lot_source = source.replace(
            "double lot = CalculateRiskLot(entryPrice, stopLoss, signal);",
            "double lot = 0.01;",
        )
        fixed_lot_analysis = BRIEF.analyze_compact_ea_source(
            fixed_lot_source,
            strategy_brief=brief,
            strategy_brief_digest=brief_digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(fixed_lot_source.encode("utf-8")).hexdigest(),
            target_platform="mt4",
        )
        self.assertFalse(fixed_lot_analysis["checks"]["riskSizingExecution"])
        self.assertFalse(fixed_lot_analysis["checks"]["lotCalculationSafety"])
        self.assertFalse(fixed_lot_analysis["checks"]["moneyManagementExecution"])
        self.assertIn(
            "ea_risk_percent_equity_path_missing",
            fixed_lot_analysis["findings"],
        )

        zero_protection_source = source.replace(
            "3, stopLoss, takeProfit,",
            "3, 0, 0,",
        )
        zero_protection_analysis = analyze_bound(zero_protection_source, brief)
        self.assertFalse(
            zero_protection_analysis["checks"]["exitAndProtectionExecution"]
        )

        pending_only_source = source.replace(
            "signal = OP_BUY;",
            "signal = OP_BUYSTOP;",
        ).replace(
            "signal = OP_SELL;",
            "signal = OP_SELLSTOP;",
        )
        pending_only_analysis = analyze_bound(pending_only_source, brief)
        self.assertFalse(pending_only_analysis["checks"]["orderExecution"])

        negative_pending_brief = dict(brief)
        negative_pending_brief["orderExecution"] = (
            "Buy Stop is disabled; use Market Buy/Sell."
        )
        self.assertTrue(
            analyze_bound(source, negative_pending_brief)["checks"]["orderExecution"]
        )

        pending_brief = dict(brief)
        pending_brief["orderExecution"] = (
            "No Buy Stop; use Sell Stop 10 pips below the signal low."
        )
        self.assertFalse(
            analyze_bound(source, pending_brief)["checks"]["orderExecution"]
        )

        mixed_brief = dict(brief)
        mixed_brief["orderExecution"] = (
            "Use both Market Buy/Sell and Buy Stop orders."
        )
        self.assertFalse(
            analyze_bound(source, mixed_brief)["checks"]["orderExecution"]
        )

        point_protection_brief = dict(brief)
        point_protection_brief["exitRules"] = (
            "StopLossPoints=200; TakeProfitPoints=400; TrailingStop=false; "
            "BreakEven=false; PartialClose=false."
        )
        self.assertFalse(
            analyze_bound(source, point_protection_brief)["checks"]
            ["exitAndProtectionExecution"]
        )
        point_protection_source = source.replace(
            "double protectedDistance = MathMax(StopLossATR * atr, brokerFloor);",
            "double protectedDistance = 200 * Point;",
        ).replace(
            "double takeProfit = signal == OP_BUY ? entryPrice + protectedDistance * RewardRiskRatio : entryPrice - protectedDistance * RewardRiskRatio;",
            "double takeProfit = signal == OP_BUY ? entryPrice + 400 * Point : entryPrice - 400 * Point;",
        )
        self.assertTrue(
            analyze_bound(point_protection_source, point_protection_brief)["checks"]
            ["exitAndProtectionExecution"]
        )

        source_percent_brief = dict(brief)
        source_percent_brief["moneyManagement"] = (
            "Risk per trade is 1 percent of Equity; calculate Lot from "
            "RiskMoney/LossPerLotAtSL using TickSize, TickValue and VolumeStep; "
            "allow one trade at a time per Symbol+Magic."
        )
        source_percent_safe = analyze_bound(source, source_percent_brief)
        self.assertTrue(source_percent_safe["checks"]["riskSizingExecution"])
        self.assertTrue(source_percent_safe["checks"]["lotCalculationSafety"])
        source_percent_fixed = analyze_bound(fixed_lot_source, source_percent_brief)
        self.assertFalse(source_percent_fixed["checks"]["riskSizingExecution"])
        self.assertFalse(source_percent_fixed["checks"]["lotCalculationSafety"])

        overwritten_lot_source = source.replace(
            "double lot = CalculateRiskLot(entryPrice, stopLoss, signal);",
            "double lot = CalculateRiskLot(entryPrice, stopLoss, signal);\n"
            "  lot = 10.0;",
        )
        overwritten_lot_analysis = analyze_bound(
            overwritten_lot_source,
            source_percent_brief,
        )
        self.assertFalse(overwritten_lot_analysis["checks"]["riskSizingExecution"])
        self.assertFalse(overwritten_lot_analysis["checks"]["lotCalculationSafety"])

        unsafe_return_source = source.replace("return(lot);", "return(10.0);")
        unsafe_return_analysis = analyze_bound(unsafe_return_source, source_percent_brief)
        self.assertFalse(unsafe_return_analysis["checks"]["riskSizingExecution"])
        self.assertFalse(unsafe_return_analysis["checks"]["lotCalculationSafety"])

        clamped_minimum_source = source.replace(
            "if(lot < minimumLot || lot > maximumLot) return(0);",
            "if(lot > maximumLot) return(0);\n  lot = MathMax(lot, minimumLot);",
        )
        clamped_minimum_analysis = analyze_bound(
            clamped_minimum_source,
            source_percent_brief,
        )
        self.assertFalse(clamped_minimum_analysis["checks"]["riskSizingExecution"])
        self.assertFalse(clamped_minimum_analysis["checks"]["lotCalculationSafety"])

        nonzero_invalid_fallback_source = source.replace(
            "if(tickSize <= 0 || tickValue <= 0 || volumeStep <= 0 || minimumLot <= 0 ||\n"
            "     maximumLot <= 0 || stopDistance <= 0) return(0);",
            "if(tickSize <= 0 || tickValue <= 0 || volumeStep <= 0 || minimumLot <= 0 ||\n"
            "     maximumLot <= 0 || stopDistance <= 0) return(0.01);",
        )
        nonzero_invalid_fallback_analysis = analyze_bound(
            nonzero_invalid_fallback_source,
            source_percent_brief,
        )
        self.assertFalse(
            nonzero_invalid_fallback_analysis["checks"]["riskSizingExecution"]
        )
        self.assertFalse(
            nonzero_invalid_fallback_analysis["checks"]["lotCalculationSafety"]
        )

        ignored_margin_result_source = source.replace(
            "if(AccountFreeMarginCheck(Symbol(), signal, lot) <= 0) return(0);",
            "double marginProbe = AccountFreeMarginCheck(Symbol(), signal, lot);",
        )
        ignored_margin_result_analysis = analyze_bound(
            ignored_margin_result_source,
            source_percent_brief,
        )
        self.assertFalse(ignored_margin_result_analysis["checks"]["riskSizingExecution"])
        self.assertFalse(ignored_margin_result_analysis["checks"]["lotCalculationSafety"])

        wrong_margin_volume_source = source.replace(
            "AccountFreeMarginCheck(Symbol(), signal, lot)",
            "AccountFreeMarginCheck(Symbol(), signal, 0.01)",
        )
        wrong_margin_volume_analysis = analyze_bound(
            wrong_margin_volume_source,
            source_percent_brief,
        )
        self.assertFalse(wrong_margin_volume_analysis["checks"]["riskSizingExecution"])
        self.assertFalse(wrong_margin_volume_analysis["checks"]["lotCalculationSafety"])

        unsafe_early_lot_return_source = source.replace(
            "double CalculateRiskLot(double entryPrice, double stopLoss, int signal) {",
            "double CalculateRiskLot(double entryPrice, double stopLoss, int signal) {\n"
            "  if(Bars > 0) return(10.0);",
        )
        unsafe_early_lot_return_analysis = analyze_bound(
            unsafe_early_lot_return_source,
            source_percent_brief,
        )
        self.assertFalse(
            unsafe_early_lot_return_analysis["checks"]["riskSizingExecution"]
        )
        self.assertFalse(
            unsafe_early_lot_return_analysis["checks"]["lotCalculationSafety"]
        )

        normalized_safe_lot_source = source.replace(
            "return(lot);",
            "return(NormalizeDouble(lot, 2));",
        )
        normalized_safe_lot_analysis = analyze_bound(
            normalized_safe_lot_source,
            source_percent_brief,
        )
        self.assertTrue(normalized_safe_lot_analysis["checks"]["riskSizingExecution"])
        self.assertTrue(normalized_safe_lot_analysis["checks"]["lotCalculationSafety"])

        risk_pct_source = source.replace("RiskPercent", "RiskPct")
        risk_pct_analysis = analyze_bound(risk_pct_source, source_percent_brief)
        self.assertTrue(risk_pct_analysis["checks"]["riskSizingExecution"])
        self.assertTrue(risk_pct_analysis["checks"]["lotCalculationSafety"])

        fixed_lot_brief = dict(brief)
        fixed_lot_brief["moneyManagement"] = (
            "Fixed lot 0.10; maximum one open or pending position per Symbol+Magic."
        )
        fixed_point_one_source = source.replace(
            "double lot = CalculateRiskLot(entryPrice, stopLoss, signal);",
            "double lot = 0.10;",
        )
        self.assertTrue(
            analyze_bound(fixed_point_one_source, fixed_lot_brief)["checks"]
            ["moneyManagementExecution"]
        )
        wrong_fixed_lot_source = fixed_point_one_source.replace(
            "double lot = 0.10;", "double lot = 0.01;"
        )
        self.assertFalse(
            analyze_bound(wrong_fixed_lot_source, fixed_lot_brief)["checks"]
            ["moneyManagementExecution"]
        )
        multiplied_fixed_lot_source = fixed_point_one_source.replace(
            "input double RiskPercent = 1.0;",
            "input double RiskPercent = 1.0;\ninput double FixedLot = 0.10;",
        ).replace("double lot = 0.10;", "double lot = FixedLot * 2;")
        self.assertFalse(
            analyze_bound(multiplied_fixed_lot_source, fixed_lot_brief)["checks"]
            ["moneyManagementExecution"]
        )

        thai_risk_brief = dict(brief)
        thai_risk_brief["moneyManagement"] = (
            "เสี่ยง 2% ต่อไม้; เปิดได้สูงสุด 1 ไม้ต่อ Symbol+Magic; "
            "คำนวณล็อตจาก Equity, ระยะ SL จริง, TickSize และ TickValue"
        )
        self.assertFalse(
            analyze_bound(source, thai_risk_brief)["checks"]["moneyManagementExecution"]
        )

        for fixed_text in (
            "Position sizing is 0.10 lots fixed; max one open position per Symbol+Magic.",
            "ใช้ 0.10 ล็อตคงที่ต่อไม้; เปิดได้สูงสุด 1 ไม้ต่อ Symbol+Magic",
        ):
            with self.subTest(fixed_text=fixed_text):
                value_first_fixed_brief = dict(brief)
                value_first_fixed_brief["moneyManagement"] = fixed_text
                wrong_value_first_fixed_source = source.replace(
                    "double lot = CalculateRiskLot(entryPrice, stopLoss, signal);",
                    "double lot = 10.0;",
                )
                self.assertFalse(
                    analyze_bound(
                        wrong_value_first_fixed_source,
                        value_first_fixed_brief,
                    )["checks"]["moneyManagementExecution"]
                )

        arbitrary_default_protection = source.replace(
            "double atr = iATR(Symbol(), Period(), ATRPeriod, 1);",
            "double atr = 1 * Point;",
        )
        self.assertFalse(
            analyze_bound(arbitrary_default_protection, brief)["checks"]
            ["exitAndProtectionExecution"]
        )

        independent_atr_target_source = source.replace(
            "input double RewardRiskRatio = 2.0;",
            "input double RewardRiskRatio = 2.0;\ninput double TakeProfitATR = 3.0;",
        ).replace(
            "protectedDistance * RewardRiskRatio",
            "TakeProfitATR * atr",
        )
        self.assertFalse(
            analyze_bound(independent_atr_target_source, brief)["checks"]
            ["exitAndProtectionExecution"]
        )

        local_default_inputs = source.replace("input int ATRPeriod", "int ATRPeriod").replace(
            "input double StopLossATR", "double StopLossATR"
        ).replace(
            "input double RewardRiskRatio", "double RewardRiskRatio"
        ).replace(
            "input int ExecutionBufferPoints", "int ExecutionBufferPoints"
        )
        self.assertFalse(
            analyze_bound(local_default_inputs, brief)["checks"]
            ["exitAndProtectionExecution"]
        )

        for declaration in (
            "double StopLossATR = 99.0;",
            "double RewardRiskRatio = 99.0;",
            "int ExecutionBufferPoints = 999;",
        ):
            with self.subTest(shadowed_default=declaration):
                shadowed_source = source.replace(
                    "  double entryPrice = signal == OP_BUY ? Ask : Bid;",
                    "  double entryPrice = signal == OP_BUY ? Ask : Bid;\n"
                    f"  {declaration}",
                )
                self.assertFalse(
                    analyze_bound(shadowed_source, brief)["checks"]
                    ["exitAndProtectionExecution"]
                )

        unused_default_mutations = (
            ("iATR(Symbol(), Period(), ATRPeriod, 1)", "iATR(Symbol(), Period(), 14, 1)"),
            ("StopLossATR * atr", "1.5 * atr"),
            (
                "MarketInfo(Symbol(), MODE_STOPLEVEL) + ExecutionBufferPoints",
                "MarketInfo(Symbol(), MODE_STOPLEVEL) + 2",
            ),
            ("protectedDistance * RewardRiskRatio", "protectedDistance * 2.0"),
        )
        for original, replacement in unused_default_mutations:
            with self.subTest(unused_default_input=original):
                unused_input_source = source.replace(original, replacement)
                self.assertFalse(
                    analyze_bound(unused_input_source, brief)["checks"]
                    ["exitAndProtectionExecution"]
                )

        shadowed_risk_source = source.replace(
            "double CalculateRiskLot(double entryPrice, double stopLoss, int signal)",
            "double CalculateRiskLot(double entryPrice, double stopLoss, int signal, double RiskPercent)",
        ).replace(
            "CalculateRiskLot(entryPrice, stopLoss, signal);",
            "CalculateRiskLot(entryPrice, stopLoss, signal, 50.0);",
        )
        shadowed_risk_analysis = analyze_bound(
            shadowed_risk_source,
            source_percent_brief,
        )
        self.assertFalse(shadowed_risk_analysis["checks"]["riskSizingExecution"])
        self.assertFalse(shadowed_risk_analysis["checks"]["moneyManagementExecution"])

        scaled_risk_money_source = source.replace(
            "AccountEquity() * RiskPercent / 100.0;",
            "AccountEquity() * RiskPercent / 100.0 * 10.0;",
        )
        scaled_risk_money_analysis = analyze_bound(
            scaled_risk_money_source,
            source_percent_brief,
        )
        self.assertFalse(scaled_risk_money_analysis["checks"]["riskSizingExecution"])
        self.assertFalse(scaled_risk_money_analysis["checks"]["moneyManagementExecution"])

        reversed_protection_source = source.replace(
            "signal == OP_BUY ? entryPrice - protectedDistance : entryPrice + protectedDistance",
            "signal == OP_BUY ? entryPrice + protectedDistance : entryPrice - protectedDistance",
        ).replace(
            "signal == OP_BUY ? entryPrice + protectedDistance * RewardRiskRatio : entryPrice - protectedDistance * RewardRiskRatio",
            "signal == OP_BUY ? entryPrice - protectedDistance * RewardRiskRatio : entryPrice + protectedDistance * RewardRiskRatio",
        )
        self.assertFalse(
            analyze_bound(reversed_protection_source, brief)["checks"]
            ["exitAndProtectionExecution"]
        )

        mixed_protection_source = source.replace(
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);",
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);\n"
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, 0, 0, \"Unprotected\", MagicNumber, 0);",
        )
        self.assertFalse(
            analyze_bound(mixed_protection_source, brief)["checks"]
            ["exitAndProtectionExecution"]
        )

        unrelated_modify_source = source.replace(
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);",
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, 0, 0, \"Naked\", MagicNumber, 0);\n"
            "  double unrelatedStop = entryPrice - protectedDistance;\n"
            "  double unrelatedTake = entryPrice + protectedDistance * RewardRiskRatio;\n"
            "  OrderModify(123, entryPrice, unrelatedStop, unrelatedTake, 0);",
        )
        self.assertFalse(
            analyze_bound(unrelated_modify_source, brief)["checks"]
            ["exitAndProtectionExecution"]
        )

        two_r_brief = dict(brief)
        two_r_brief["exitRules"] = (
            "Hard stop 20 points; profit target 2R; TrailingStop=false; "
            "BreakEven=false; PartialClose=false."
        )
        two_r_source = source.replace(
            "double protectedDistance = MathMax(StopLossATR * atr, brokerFloor);",
            "double protectedDistance = 20 * Point;",
        ).replace(
            "protectedDistance * RewardRiskRatio",
            "protectedDistance * 2",
        )
        self.assertTrue(
            analyze_bound(two_r_source, two_r_brief)["checks"]
            ["exitAndProtectionExecution"]
        )
        fake_two_r_source = two_r_source.replace(
            "protectedDistance * 2", "protectedDistance + 2 * Point"
        )
        self.assertFalse(
            analyze_bound(fake_two_r_source, two_r_brief)["checks"]
            ["exitAndProtectionExecution"]
        )

        decoy_default_two_r_source = source.replace(
            "protectedDistance * RewardRiskRatio",
            "protectedDistance * 99 + 2 * Point",
        )
        self.assertFalse(
            analyze_bound(decoy_default_two_r_source, brief)["checks"]
            ["exitAndProtectionExecution"]
        )

        decoy_default_atr_source = source.replace(
            "MathMax(StopLossATR * atr, brokerFloor)",
            "MathMax(99 * atr + StopLossATR * 0, brokerFloor)",
        )
        self.assertFalse(
            analyze_bound(decoy_default_atr_source, brief)["checks"]
            ["exitAndProtectionExecution"]
        )

        pip_protection_brief = dict(brief)
        pip_protection_brief["exitRules"] = (
            "Hard stop 20 pips; take profit 40 pips; TrailingStop=false; "
            "BreakEven=false; PartialClose=false."
        )
        wrong_pip_distance_source = source.replace(
            "  double entryPrice = signal == OP_BUY ? Ask : Bid;",
            "  double entryPrice = signal == OP_BUY ? Ask : Bid;\n"
            "  double pipSize = (Digits == 3 || Digits == 5) ? 10 * Point : Point;",
        ).replace(
            "double protectedDistance = MathMax(StopLossATR * atr, brokerFloor);",
            "double protectedDistance = 50 * pipSize + 20 * Point;",
        ).replace(
            "double takeProfit = signal == OP_BUY ? entryPrice + protectedDistance * RewardRiskRatio : entryPrice - protectedDistance * RewardRiskRatio;",
            "double takeDistance = 70 * pipSize + 40 * Point;\n"
            "  double takeProfit = signal == OP_BUY ? entryPrice + takeDistance : entryPrice - takeDistance;",
        )
        self.assertFalse(
            analyze_bound(wrong_pip_distance_source, pip_protection_brief)["checks"]
            ["exitAndProtectionExecution"]
        )

        source_atr_details_brief = dict(brief)
        source_atr_details_brief["exitRules"] = (
            "StopLoss=1.5*ATR(14)[1]; profit target 2R; TrailingStop=false; "
            "BreakEven=false; PartialClose=false."
        )
        wrong_source_atr_details = source.replace(
            "iATR(Symbol(), Period(), ATRPeriod, 1)",
            "iATR(Symbol(), Period(), 50, 0)",
        )
        self.assertFalse(
            analyze_bound(wrong_source_atr_details, source_atr_details_brief)["checks"]
            ["exitAndProtectionExecution"]
        )

        disabled_management_but_active_source = source.replace(
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);",
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);\n"
            "  double trailingStop = OrderOpenPrice();\n"
            "  OrderModify(123, 0, trailingStop, takeProfit, 0);",
        )
        self.assertFalse(
            analyze_bound(disabled_management_but_active_source, brief)["checks"]
            ["exitAndProtectionExecution"]
        )

        read_only_bar_time_source = source.replace(
            "  static datetime lastBar = 0;\n"
            "  datetime currentBar = Time[0];\n"
            "  if(currentBar <= 0 || currentBar == lastBar) return;\n"
            "  lastBar = currentBar;",
            "  datetime observedBar = Time[0];",
        )
        self.assertFalse(
            analyze_bound(read_only_bar_time_source, brief)["checks"]
            ["closedBarExecution"]
        )
        post_entry_current_bar_source = source.replace(
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);",
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);\n"
            "  double displayOnly = Close[0];",
        )
        self.assertTrue(
            analyze_bound(post_entry_current_bar_source, brief)["checks"]
            ["closedBarExecution"]
        )

        global_bar_state_source = source.replace(
            "int OnInit() { return(INIT_SUCCEEDED); }",
            "datetime lastBar = 0;\nint OnInit() { return(INIT_SUCCEEDED); }",
        ).replace("  static datetime lastBar = 0;\n", "")
        self.assertTrue(
            analyze_bound(global_bar_state_source, brief)["checks"]
            ["closedBarExecution"]
        )

        uninitialized_static_bar_state_source = source.replace(
            "  static datetime lastBar = 0;",
            "  static datetime lastBar;",
        )
        self.assertTrue(
            analyze_bound(uninitialized_static_bar_state_source, brief)["checks"]
            ["closedBarExecution"]
        )

        uninitialized_global_bar_state_source = source.replace(
            "int OnInit() { return(INIT_SUCCEEDED); }",
            "datetime lastBar;\nint OnInit() { return(INIT_SUCCEEDED); }",
        ).replace("  static datetime lastBar = 0;\n", "")
        self.assertTrue(
            analyze_bound(uninitialized_global_bar_state_source, brief)["checks"]
            ["closedBarExecution"]
        )

        if_else_assignment_source = source.replace(
            "  if(Close[2] >= Open[2] && Close[1] < Open[1]) signal = OP_SELL;",
            "  else signal = OP_SELL;",
        ).replace(
            "  double stopLoss = signal == OP_BUY ? entryPrice - protectedDistance : entryPrice + protectedDistance;",
            "  double stopLoss = 0;\n"
            "  if(signal == OP_BUY) stopLoss = entryPrice - protectedDistance;\n"
            "  else stopLoss = entryPrice + protectedDistance;",
        ).replace(
            "  double takeProfit = signal == OP_BUY ? entryPrice + protectedDistance * RewardRiskRatio : entryPrice - protectedDistance * RewardRiskRatio;",
            "  double takeProfit = 0;\n"
            "  if(signal == OP_BUY) takeProfit = entryPrice + protectedDistance * RewardRiskRatio;\n"
            "  else takeProfit = entryPrice - protectedDistance * RewardRiskRatio;",
        )
        if_else_assignment_analysis = analyze_bound(if_else_assignment_source, brief)
        if_else_code = BRIEF._indicator_lexical_views(if_else_assignment_source)[0]
        if_else_reachable = BRIEF._compact_ea_reachable_code(
            BRIEF._compact_ea_function_map(if_else_code)
        )
        if_else_evidence = BRIEF._mql_trade_execution_evidence(
            BRIEF._mql_trade_call_records(if_else_reachable),
            if_else_reachable,
        )
        self.assertTrue(if_else_assignment_analysis["checks"]["orderExecution"])
        self.assertTrue(
            if_else_assignment_analysis["checks"]["exitAndProtectionExecution"],
            {
                "analysis": if_else_assignment_analysis,
                "stops": if_else_evidence[1],
                "takes": if_else_evidence[2],
                "directions": {
                    f"{side}_{component}": BRIEF._mql_dependency_has_signed_distance(
                        if_else_evidence[1 if component == "stop" else 2][0],
                        side=side,
                        component=component,
                    )
                    for side in ("buy", "sell")
                    for component in ("stop", "take")
                },
            },
        )

        positive_new_bar_helper_source = source.replace(
            "void OnTick() {",
            "void ExecuteSignal() {",
        ).replace(
            "  static datetime lastBar = 0;\n"
            "  datetime currentBar = Time[0];\n"
            "  if(currentBar <= 0 || currentBar == lastBar) return;\n"
            "  lastBar = currentBar;\n",
            "",
        ) + """
bool IsNewBar() {
  static datetime lastBar = 0;
  datetime currentBar = Time[0];
  if(currentBar <= 0 || currentBar == lastBar) return(false);
  lastBar = currentBar;
  return(true);
}
void OnTick() {
  if(IsNewBar()) ExecuteSignal();
}
"""
        positive_new_bar_analysis = analyze_bound(positive_new_bar_helper_source, brief)
        self.assertTrue(
            positive_new_bar_analysis["checks"]["closedBarExecution"],
            positive_new_bar_analysis,
        )

        wrapped_trade_source = source.replace(
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);",
            "  OpenTrade(signal, lot, entryPrice, stopLoss, takeProfit);",
        ) + """
void OpenTrade(int orderType, double volume, double price, double sl, double tp) {
  OrderSend(Symbol(), orderType, volume, price, 3, sl, tp, "Wrapped", MagicNumber, 0);
}
"""
        wrapped_trade_analysis = analyze_bound(
            wrapped_trade_source,
            source_percent_brief,
        )
        for check_name in (
            "exitAndProtectionExecution",
            "moneyManagementExecution",
            "orderExecution",
        ):
            with self.subTest(wrapped_trade_check=check_name):
                self.assertTrue(
                    wrapped_trade_analysis["checks"][check_name],
                    wrapped_trade_analysis,
                )

        for label, replacement in (
            (
                "same_helper_called_twice",
                "  OpenTrade(signal, lot, entryPrice, stopLoss, takeProfit);\n"
                "  OpenTrade(signal, lot, entryPrice, stopLoss, takeProfit);",
            ),
            (
                "trade_helper_called_from_loop",
                "  for(int duplicateEntry=0; duplicateEntry<2; duplicateEntry++) {\n"
                "    OpenTrade(signal, lot, entryPrice, stopLoss, takeProfit);\n"
                "  }",
            ),
        ):
            with self.subTest(trade_helper_multiplicity=label):
                duplicated = wrapped_trade_source.replace(
                    "  OpenTrade(signal, lot, entryPrice, stopLoss, takeProfit);",
                    replacement,
                    1,
                )
                duplicated_analysis = analyze_bound(
                    duplicated,
                    source_percent_brief,
                )
                self.assertFalse(
                    duplicated_analysis["checks"]["positionCapExecution"],
                    duplicated_analysis,
                )
                self.assertFalse(duplicated_analysis["complete"], duplicated_analysis)
                self.assertIn(
                    "ea_position_cap_guard_missing",
                    duplicated_analysis["findings"],
                )

        managed_exit_brief = dict(brief)
        managed_exit_brief["exitRules"] = (
            "StopLoss=20 pips; TakeProfit=40 pips; trail by 10 pips; "
            "move SL to break-even at 1R; partial close 50% at 1R."
        )
        aggregate_only_source = source.replace(
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);",
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);\n"
            "  OrderModify(123, 0, 0, 0, 0);\n"
            "  OrderClose(123, OrderLots(), Bid, 3);",
        )
        self.assertFalse(
            analyze_bound(aggregate_only_source, managed_exit_brief)["checks"]
            ["exitAndProtectionExecution"]
        )

        both_pending_brief = dict(brief)
        both_pending_brief["orderExecution"] = (
            "Buy Stop 10 pips above the high and Sell Stop 10 pips below the low."
        )
        buy_stop_only_source = source.replace(
            "signal = OP_BUY;",
            "signal = OP_BUYSTOP;",
        ).replace(
            "signal = OP_SELL;",
            "signal = OP_BUYSTOP;",
        )
        self.assertFalse(
            analyze_bound(buy_stop_only_source, both_pending_brief)["checks"]
            ["orderExecution"]
        )

        generic_stop_brief = dict(brief)
        generic_stop_brief["orderExecution"] = (
            "Use a stop-entry order after a confirmed breakout."
        )
        limit_instead_of_stop_source = source.replace(
            "signal = OP_BUY;", "signal = OP_BUYLIMIT;"
        ).replace(
            "signal = OP_SELL;", "signal = OP_SELLLIMIT;"
        )
        self.assertFalse(
            analyze_bound(limit_instead_of_stop_source, generic_stop_brief)["checks"]
            ["orderExecution"]
        )

        pending_stop_order_brief = dict(brief)
        pending_stop_order_brief["orderExecution"] = (
            "Place a pending stop order 10 points above previous high."
        )
        stop_order_as_limit_source = source.replace(
            "signal = OP_BUY;", "signal = OP_BUYLIMIT;"
        ).replace(
            "signal = OP_SELL;", "signal = OP_BUYLIMIT;"
        ).replace(
            "double entryPrice = signal == OP_BUY ? Ask : Bid;",
            "double entryPrice = High[1] + 10 * Point;",
        )
        self.assertFalse(
            analyze_bound(stop_order_as_limit_source, pending_stop_order_brief)["checks"]
            ["orderExecution"]
        )

        pending_limit_order_brief = dict(brief)
        pending_limit_order_brief["orderExecution"] = (
            "Place a pending limit order 10 points below Ask."
        )
        limit_order_as_stop_source = source.replace(
            "signal = OP_BUY;", "signal = OP_BUYSTOP;"
        ).replace(
            "signal = OP_SELL;", "signal = OP_BUYSTOP;"
        ).replace(
            "double entryPrice = signal == OP_BUY ? Ask : Bid;",
            "double entryPrice = Ask - 10 * Point;",
        )
        self.assertFalse(
            analyze_bound(limit_order_as_stop_source, pending_limit_order_brief)["checks"]
            ["orderExecution"]
        )

        pending_atr_brief = dict(brief)
        pending_atr_brief["orderExecution"] = (
            "Use Buy Stop 1 ATR above previous high."
        )
        pending_atr_as_points_source = source.replace(
            "signal = OP_BUY;", "signal = OP_BUYSTOP;"
        ).replace(
            "signal = OP_SELL;", "signal = OP_BUYSTOP;"
        ).replace(
            "double entryPrice = signal == OP_BUY ? Ask : Bid;",
            "double entryPrice = High[1] + 99 * Point;",
        )
        self.assertFalse(
            analyze_bound(pending_atr_as_points_source, pending_atr_brief)["checks"]
            ["orderExecution"]
        )

        wrong_pending_price_source = source.replace(
            "signal = OP_BUY;", "signal = OP_BUYSTOP;"
        ).replace(
            "signal = OP_SELL;", "signal = OP_SELLSTOP;"
        ).replace(
            "double entryPrice = signal == OP_BUY ? Ask : Bid;",
            "double entryPrice = signal == OP_BUYSTOP ? Low[1] - 10 * Point : High[1] + 10 * Point;",
        )
        self.assertFalse(
            analyze_bound(wrong_pending_price_source, both_pending_brief)["checks"]
            ["orderExecution"]
        )

        raw_point_for_pip_source = source.replace(
            "signal = OP_BUY;", "signal = OP_BUYSTOP;"
        ).replace(
            "signal = OP_SELL;", "signal = OP_SELLSTOP;"
        ).replace(
            "double entryPrice = signal == OP_BUY ? Ask : Bid;",
            "double entryPrice = signal == OP_BUYSTOP ? High[1] + 10 * Point : Low[1] - 10 * Point;",
        )
        self.assertFalse(
            analyze_bound(raw_point_for_pip_source, both_pending_brief)["checks"]
            ["orderExecution"]
        )
        scaled_pip_source = raw_point_for_pip_source.replace(
            "  double entryPrice = signal == OP_BUYSTOP ? High[1] + 10 * Point : Low[1] - 10 * Point;",
            "  double pipSize = (Digits == 3 || Digits == 5) ? 10 * Point : Point;\n"
            "  double entryPrice = signal == OP_BUYSTOP ? High[1] + 10 * pipSize : Low[1] - 10 * pipSize;",
        )
        scaled_pip_analysis = analyze_bound(scaled_pip_source, both_pending_brief)
        self.assertTrue(
            scaled_pip_analysis["checks"]["orderExecution"],
            scaled_pip_analysis,
        )

        overwritten_order_type_source = source.replace(
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);",
            "  int chosenType = OP_BUYSTOP;\n"
            "  chosenType = OP_BUYLIMIT;\n"
            "  OrderSend(Symbol(), chosenType, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);",
        )
        buy_stop_brief = dict(brief)
        buy_stop_brief["orderExecution"] = "Use Buy Stop orders after a breakout."
        self.assertFalse(
            analyze_bound(overwritten_order_type_source, buy_stop_brief)["checks"]
            ["orderExecution"]
        )

        buy_limit_brief = dict(brief)
        buy_limit_brief["orderExecution"] = "Use Buy Limit 20 points below Ask."
        wrong_buy_limit_price_source = source.replace(
            "signal = OP_SELL;", "signal = OP_BUYLIMIT;"
        ).replace(
            "signal = OP_BUY;", "signal = OP_BUYLIMIT;"
        ).replace(
            "double entryPrice = signal == OP_BUY ? Ask : Bid;",
            "double entryPrice = Ask + 20 * Point;",
        )
        self.assertFalse(
            analyze_bound(wrong_buy_limit_price_source, buy_limit_brief)["checks"]
            ["orderExecution"]
        )

        paired_stop_brief = dict(brief)
        paired_stop_brief["orderExecution"] = (
            "Use Buy/Sell Stop orders 10 points beyond prior high/low."
        )
        sell_stop_only_source = source.replace(
            "signal = OP_BUY;", "signal = OP_SELLSTOP;"
        ).replace(
            "signal = OP_SELL;", "signal = OP_SELLSTOP;"
        )
        self.assertFalse(
            analyze_bound(sell_stop_only_source, paired_stop_brief)["checks"]
            ["orderExecution"]
        )
        inverted_paired_stop_source = source.replace(
            "signal = OP_BUY;", "signal = OP_BUYSTOP;"
        ).replace(
            "signal = OP_SELL;", "signal = OP_SELLSTOP;"
        ).replace(
            "double entryPrice = signal == OP_BUY ? Ask : Bid;",
            "double entryPrice = signal == OP_BUYSTOP ? Low[1] - 10 * Point : High[1] + 10 * Point;",
        )
        self.assertFalse(
            analyze_bound(inverted_paired_stop_source, paired_stop_brief)["checks"]
            ["orderExecution"]
        )
        correct_paired_stop_source = inverted_paired_stop_source.replace(
            "signal == OP_BUYSTOP ? Low[1] - 10 * Point : High[1] + 10 * Point",
            "signal == OP_BUYSTOP ? High[1] + 10 * Point : Low[1] - 10 * Point",
        )
        self.assertTrue(
            analyze_bound(correct_paired_stop_source, paired_stop_brief)["checks"]
            ["orderExecution"]
        )

        hidden_loss_escalation_source = source.replace(
            "  double lot = CalculateRiskLot(entryPrice, stopLoss, signal);",
            "  double lot = CalculateRiskLot(entryPrice, stopLoss, signal);\n"
            "  if(lossCount > 0) lot *= 2;",
        )
        self.assertFalse(
            analyze_bound(hidden_loss_escalation_source, brief)["checks"]
            ["recoveryPolicy"]
        )

        indirect_loss_escalation_source = source.replace(
            "  double lot = CalculateRiskLot(entryPrice, stopLoss, signal);",
            "  double lot = CalculateRiskLot(entryPrice, stopLoss, signal);\n"
            "  if(!PreviousOutcomePositive()) lot *= 2.0;",
        ) + """
bool PreviousOutcomePositive() {
  return(OrderProfit() + OrderSwap() + OrderCommission() >= 0);
}
"""
        self.assertFalse(
            analyze_bound(indirect_loss_escalation_source, brief)["checks"]
            ["recoveryPolicy"]
        )

        ordinary_loss_analytics_source = source.replace(
            "  Comment(\"signal=\", signal, \" Balance=\", AccountBalance(), \" Equity=\", AccountEquity());",
            "  int lossCount = 0;\n"
            "  Comment(\"signal=\", signal, \" lossCount=\", lossCount, \" Balance=\", AccountBalance(), \" Equity=\", AccountEquity());",
        ).replace(
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);",
            "  if(signal == OP_BUY) OrderSend(Symbol(), OP_BUY, lot, entryPrice, 3, stopLoss, takeProfit, \"Buy\", MagicNumber, 0);\n"
            "  if(signal == OP_SELL) OrderSend(Symbol(), OP_SELL, lot, entryPrice, 3, stopLoss, takeProfit, \"Sell\", MagicNumber, 0);",
        )
        self.assertTrue(
            analyze_bound(ordinary_loss_analytics_source, brief)["checks"]
            ["recoveryPolicy"]
        )

        fake_cap_counter_source = source.replace(
            "    if(OrderSymbol() == Symbol() && OrderMagicNumber() == MagicNumber) count++;",
            "    string unusedSymbol = Symbol();\n"
            "    int unusedMagic = MagicNumber;",
        )
        self.assertFalse(
            analyze_bound(fake_cap_counter_source, brief)["checks"]
            ["positionCapExecution"]
        )

        bypassed_cap_counter_source = source.replace(
            "int CountManagedPositions() {",
            "int CountManagedPositions() {\n  if(Bars > 0) return(0);",
        )
        bypassed_cap_analysis = analyze_bound(bypassed_cap_counter_source, brief)
        self.assertFalse(bypassed_cap_analysis["checks"]["positionCapExecution"])
        self.assertFalse(bypassed_cap_analysis["checks"]["moneyManagementExecution"])

        duplicate_entry_source = source.replace(
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);",
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);\n"
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Duplicate\", MagicNumber, 0);",
        )
        duplicate_entry_analysis = analyze_bound(duplicate_entry_source, brief)
        self.assertFalse(duplicate_entry_analysis["checks"]["positionCapExecution"])
        self.assertFalse(duplicate_entry_analysis["checks"]["recoveryPolicy"])

        looped_entry_source = source.replace(
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);",
            "  for(int attempt=0; attempt<3; attempt++) "
            "OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Retry\", MagicNumber, 0);",
        )
        looped_entry_analysis = analyze_bound(looped_entry_source, brief)
        self.assertFalse(looped_entry_analysis["checks"]["positionCapExecution"])
        self.assertFalse(looped_entry_analysis["checks"]["recoveryPolicy"])

        unnamed_recovery_brief = dict(brief)
        unnamed_recovery_brief["recoveryRules"] = (
            "After 2 losses add another position every 100 points; same lot; "
            "max 3 levels; basket TP 50 points and SL 150 points; reset after "
            "basket close."
        )
        unnamed_recovery_brief["moneyManagement"] = unnamed_recovery_brief[
            "moneyManagement"
        ].replace(
            "maximum one open or pending position",
            "maximum three open or pending positions",
        )
        self.assertFalse(
            analyze_bound(source, unnamed_recovery_brief)["checks"]["recoveryPolicy"]
        )

        martingale_brief = dict(brief)
        martingale_brief["recoveryRules"] = (
            "Martingale after each loss; spacing 100 points; lot multiplier 2; "
            "max 3 levels; basket TP 50 points and SL 150 points; reset after "
            "basket close."
        )
        martingale_brief["moneyManagement"] = martingale_brief[
            "moneyManagement"
        ].replace(
            "maximum one open or pending position",
            "maximum three open or pending positions",
        )
        empty_martingale_source = source.replace(
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);",
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);\n"
            "  Martingale();",
        ) + "\nvoid Martingale() {}\n"
        self.assertFalse(
            analyze_bound(empty_martingale_source, martingale_brief)["checks"]
            ["recoveryPolicy"]
        )

        long_only_raw = dict(brief)
        long_only_raw["entryRules"] = (
            "Long-only; buy immediately intrabar when Ask breaks the prior high; "
            "never sell short."
        )
        long_only_raw["orderExecution"] = "Order type not specified."
        long_only_brief = BRIEF.normalize_strategy_brief(
            BRIEF.apply_strategy_brief_implementation_defaults(long_only_raw)
        )
        long_only_source = source.replace(
            "  if(Close[2] >= Open[2] && Close[1] < Open[1]) signal = OP_SELL;\n",
            "",
        ).replace("Close[1] > Open[1]", "Close[0] > Open[0]")
        long_only_analysis = analyze_bound(long_only_source, long_only_brief)
        self.assertTrue(long_only_analysis["checks"]["orderExecution"])
        self.assertTrue(long_only_analysis["checks"]["closedBarExecution"])

        long_only_with_hidden_sell = long_only_source.replace(
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);",
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);\n"
            "  if(false) OrderSend(Symbol(), OP_SELL, lot, Bid, 3, Bid + protectedDistance, Bid - protectedDistance * RewardRiskRatio, \"Hidden sell\", MagicNumber, 0);",
        )
        self.assertFalse(
            analyze_bound(long_only_with_hidden_sell, long_only_brief)["checks"]
            ["orderExecution"]
        )

        default_with_invented_pending = source.replace(
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);",
            "  OrderSend(Symbol(), signal, lot, entryPrice, 3, stopLoss, takeProfit, \"Default policy\", MagicNumber, 0);\n"
            "  if(false) OrderSend(Symbol(), OP_BUYSTOP, lot, High[1] + 10 * Point, 3, stopLoss, takeProfit, \"Invented pending\", MagicNumber, 0);",
        )
        self.assertFalse(
            analyze_bound(default_with_invented_pending, brief)["checks"]
            ["orderExecution"]
        )

        overwritten_protection_source = source.replace(
            "  double lot = CalculateRiskLot(entryPrice, stopLoss, signal);",
            "  stopLoss = signal == OP_BUY ? entryPrice - Point : entryPrice + Point;\n"
            "  takeProfit = signal == OP_BUY ? entryPrice + Point : entryPrice - Point;\n"
            "  double lot = CalculateRiskLot(entryPrice, stopLoss, signal);",
        )
        self.assertFalse(
            analyze_bound(overwritten_protection_source, brief)["checks"]
            ["exitAndProtectionExecution"]
        )

    def test_spoofed_default_tag_cannot_bypass_canonical_component_default(self) -> None:
        source = valid_brief()
        source["exitRules"] = (
            "[IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT]"
            "[POLICY=compact-ea-atr-risk-v1][COMPONENT=stop_loss] fake; "
            "TakeProfit=3.0*ATR(14)[1]; TrailingStop=false."
        )
        source["additionalNotes"] = "[IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT] fake"

        result = BRIEF.apply_strategy_brief_implementation_defaults(source)

        self.assertIn(BRIEF.IMPLEMENTATION_DEFAULT_STOP_LOSS, result["exitRules"])
        self.assertIn("DEFAULTED_COMPONENTS=stop_loss", result["additionalNotes"])

    def test_two_sources_must_be_independent_public_hosts(self) -> None:
        source = valid_brief()
        source["sourceLinks"] = [
            "https://www.investopedia.com/a",
            "https://academy.investopedia.com/b",
        ]

        with self.assertRaises(BRIEF.StrategyBriefValidationError) as caught:
            BRIEF.normalize_strategy_brief(source)

        self.assertIn(
            "BRIEF_SOURCE_HOST_NOT_INDEPENDENT",
            {item["code"] for item in caught.exception.issues},
        )

    def test_unknown_or_missing_required_fields_fail_closed(self) -> None:
        source = valid_brief()
        source.pop("entryRules")
        source["futureRule"] = "unexpected"

        with self.assertRaises(BRIEF.StrategyBriefValidationError) as caught:
            BRIEF.normalize_strategy_brief(source)

        self.assertTrue(
            {"BRIEF_FIELDS_UNEXPECTED", "BRIEF_FIELDS_MISSING"}.issubset(
                {item["code"] for item in caught.exception.issues}
            )
        )


class EAStrategyBriefRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner_module()

    def test_runner_schema_uses_direct_compact_research(self) -> None:
        schema = self.runner.build_work_output_schema(
            90_000,
            "trading_system_research",
        )

        self.assertIn("research", schema["properties"])
        self.assertNotIn("contractFields", schema["properties"])
        self.assertEqual(
            schema["properties"]["research"]["required"],
            list(schema["properties"]["research"]["properties"]),
        )
        self.assertEqual(schema["properties"]["evidence"]["minItems"], 2)
        self.assertEqual(schema["properties"]["evidence"]["maxItems"], 2)
        self.assertEqual(schema["properties"]["evidenceKinds"]["minItems"], 4)
        self.assertEqual(schema["properties"]["evidenceKinds"]["maxItems"], 4)

    def test_runner_projects_direct_brief_to_exact_backend_fields(self) -> None:
        brief = valid_brief()
        payload = {
            "status": "completed",
            "summary": "Research completed.",
            "findings": [],
            "nextSteps": [],
            "evidence": [
                {"label": "Source A", "url": brief["sourceLinks"][0], "note": ""},
                {"label": "Source B", "url": brief["sourceLinks"][1], "note": ""},
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

        parsed = self.runner.parse_work_result(
            json.dumps(payload),
            90_000,
            "trading_system_research",
        )

        self.assertEqual(
            [item["field"] for item in parsed["contractFields"]],
            list(self.runner.TRADING_SYSTEM_RESEARCH_CONTRACT_FIELDS),
        )
        self.assertEqual(
            self.runner.TRADING_SYSTEM_RESEARCH_CONTRACT_FIELDS,
            (
                "strategyBrief",
                "sourceDigest",
                "sourceLinks",
                "checkedAt",
                "limitations",
            ),
        )

    def test_runner_schema_reserves_space_for_all_post_parse_defaults(self) -> None:
        schema = self.runner.build_work_output_schema(
            90_000,
            "trading_system_research",
        )
        research_schema = schema["properties"]["research"]
        brief = valid_brief()
        for field in (
            "recoveryRules",
            "exitRules",
            "moneyManagement",
            "orderExecution",
        ):
            limit = research_schema["properties"][field]["maxLength"]
            prefix = "not_publicly_stated "
            brief[field] = prefix + ("x" * (limit - len(prefix)))
        notes_limit = research_schema["properties"]["additionalNotes"]["maxLength"]
        brief["additionalNotes"] = "n" * notes_limit
        brief["limitations"] = [f"Source limitation {index}." for index in range(11)]
        payload = {
            "status": "completed",
            "summary": "Research completed.",
            "findings": [],
            "nextSteps": [],
            "evidence": [
                {"label": "Source A", "url": brief["sourceLinks"][0], "note": ""},
                {"label": "Source B", "url": brief["sourceLinks"][1], "note": ""},
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

        parsed = self.runner.parse_work_result(
            json.dumps(payload),
            90_000,
            "trading_system_research",
        )

        projected = {
            item["field"]: item["value"] for item in parsed["contractFields"]
        }
        restored = json.loads(projected["strategyBrief"])
        self.assertIn("StopLossPoints=300", restored["exitRules"])
        self.assertIn("RecoveryMode=none", restored["recoveryRules"])
        self.assertLessEqual(len(restored["exitRules"]), 8000)
        self.assertLessEqual(len(restored["moneyManagement"]), 5000)
        self.assertEqual(len(restored["limitations"]), 12)


def load_runner_module():
    spec = importlib.util.spec_from_file_location(
        "metafx_ea_strategy_brief_runner",
        RUNNER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    unittest.main()
