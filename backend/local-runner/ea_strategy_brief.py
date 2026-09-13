"""Trusted compact strategy-research contract for EA source generation.

The contract intentionally keeps the learner-facing research handoff small:
nine prose fields describe what an EA writer needs, while evidence URLs,
research time, and limitations remain integrity metadata.  A durable record id
is derived by the Backend after the report is accepted and is therefore not
part of model output.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import math
import re
from datetime import datetime
from typing import Mapping
from urllib.parse import urlsplit


SCHEMA_VERSION = "ea-strategy-brief/1.0.0"
INDICATOR_SOURCE_MANIFEST_SCHEMA_VERSION = (
    "ea-factory-compact-indicator-source-manifest/1.0.0"
)
EA_SOURCE_MANIFEST_SCHEMA_VERSION = (
    "ea-factory-compact-ea-source-manifest/1.1.0"
)

CONTENT_FIELDS = (
    "systemName",
    "systemOverview",
    "entryRules",
    "recoveryRules",
    "exitRules",
    "moneyManagement",
    "orderExecution",
    "displayRequirements",
    "additionalNotes",
)
COMPACT_SHEET_FIELDS = (
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
)

_ROOT_FIELDS = frozenset(
    {
        "schemaVersion",
        *CONTENT_FIELDS,
        "sourceLinks",
        "checkedAt",
        "limitations",
    }
)
_FIELD_LIMITS = {
    "systemName": 300,
    "systemOverview": 5000,
    "entryRules": 8000,
    "recoveryRules": 6000,
    "exitRules": 8000,
    "moneyManagement": 5000,
    "orderExecution": 4000,
    "displayRequirements": 3000,
    "additionalNotes": 4000,
}
IMPLEMENTATION_DEFAULT_POLICY_ID = "compact-ea-safe-inputs-v2"
LEGACY_IMPLEMENTATION_DEFAULT_POLICY_ID = "compact-ea-atr-risk-v1"
IMPLEMENTATION_DEFAULT_MARKER = "IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT"
RECOVERY_POSITION_CAP_BINDING_MARKER = (
    "RECOVERY_POSITION_CAP_DERIVED_FROM_RECOVERY_RULES"
)
LINDA_HOLY_GRAIL_CERTIFIED_PROFILE_VERSION = (
    "linda-holy-grail-mt4-certified-v3"
)
LINDA_HOLY_GRAIL_LEGACY_BRIEF_DIGEST = (
    "8aac40a413af9c5fde16bde846715df202da6f16f68b968b3a8530b92b27e538"
)
LINDA_HOLY_GRAIL_CERTIFIED_BRIEF_DIGEST = (
    "877de2f4dd4e6081fe7ea886eca309099da4e9c2134f433d9cd079f1b1f16a42"
)
LINDA_HOLY_GRAIL_DIRECTION_COMPONENT = "entryRules.direction"
LINDA_HOLY_GRAIL_DIRECTION_RULE = (
    f"[{IMPLEMENTATION_DEFAULT_MARKER}]"
    f"[POLICY={LINDA_HOLY_GRAIL_CERTIFIED_PROFILE_VERSION}]"
    f"[COMPONENT={LINDA_HOLY_GRAIL_DIRECTION_COMPONENT}] "
    "แหล่งข้อมูลระบุให้เทรดตามทิศทางเดิมแต่ไม่ได้กำหนดสูตรแยกขาขึ้น/ขาลง "
    "สำหรับ EA profile นี้ให้ operationalize ทิศทางเดิมด้วย slope ของ SMA(20) "
    "บนแท่งปิดเท่านั้น: Long ต้องมี "
    "smaCurrent=SMA20[SignalBarShift] > "
    "smaPrevious=SMA20[SignalBarShift+1]; Short ต้องมี smaCurrent < smaPrevious. "
    "ให้คงเงื่อนไข close อยู่เหนือ/ใต้ SMA และ pullback แตะหรือเข้าใกล้ SMA "
    "เดิมร่วมกัน กฎนี้ไม่ใช่ moving-average crossover และไม่เพิ่ม +DI/-DI"
)


def _implementation_default_tag(component: str) -> str:
    return (
        f"[{IMPLEMENTATION_DEFAULT_MARKER}]"
        f"[POLICY={IMPLEMENTATION_DEFAULT_POLICY_ID}]"
        f"[COMPONENT={component}]"
    )


def _has_implementation_default_policy_component(
    text: str,
    policy_id: str,
    *components: str,
) -> bool:
    """Recognize a complete versioned default tag without trusting loose marker text."""

    if not components:
        return False
    component_pattern = "|".join(re.escape(item) for item in components)
    return bool(re.search(
        rf"\[{re.escape(IMPLEMENTATION_DEFAULT_MARKER)}\]"
        rf"\[POLICY={re.escape(policy_id)}\]"
        rf"\[COMPONENT=(?:{component_pattern})\]",
        text,
        flags=re.IGNORECASE,
    ))


IMPLEMENTATION_DEFAULT_STOP_LOSS = (
    f"{_implementation_default_tag('stop_loss')} เมื่อแหล่งข้อมูลไม่ระบุ Stop Loss ให้ใช้ "
    "StopLossPoints=300 หน่วย broker points. ระยะ SL จริงต้องไม่น้อยกว่า StopLossPoints*Point "
    "และระยะขั้นต่ำของโบรกเกอร์บวก ExecutionBufferPoints=2 points; Buy วางใต้ราคาเข้าและ "
    "Sell วางเหนือราคาเข้า. StopLossPoints และ ExecutionBufferPoints ต้องเป็น EA inputs "
    "ที่ผู้ใช้แก้และ Optimize ได้; สำหรับโบรกเกอร์ 5 หลัก 10 points โดยทั่วไปเท่ากับ 1 pip"
)
IMPLEMENTATION_DEFAULT_TAKE_PROFIT = (
    f"{_implementation_default_tag('take_profit')} เมื่อแหล่งข้อมูลไม่ระบุ Take Profit ให้ใช้ "
    "TakeProfitPoints=600 หน่วย broker points. Buy วางเหนือราคาเข้าและ Sell วางใต้ราคาเข้า; "
    "TakeProfitPoints ต้องเป็น EA input ที่ผู้ใช้แก้และ Optimize ได้. ค่านี้เป็นค่าเริ่มต้น 2:1 "
    "เมื่อเทียบกับ SL เริ่มต้น 300 points ไม่ใช่ผลกำไรหรืออัตราส่วนที่พิสูจน์จากแหล่งข้อมูล"
)
IMPLEMENTATION_DEFAULT_TRAILING_STOP = (
    f"{_implementation_default_tag('trailing_stop')} เมื่อแหล่งข้อมูลไม่ระบุ ให้ตั้ง "
    "TrailingStop=false; เปิดใช้ได้เฉพาะเมื่อมีกฎต้นทางที่ทำตามได้หรือผู้ใช้ยืนยันค่าภายหลัง"
)
IMPLEMENTATION_DEFAULT_BREAK_EVEN = (
    f"{_implementation_default_tag('break_even')} เมื่อแหล่งข้อมูลไม่ระบุ ให้ตั้ง "
    "BreakEven=false; เปิดใช้ได้เฉพาะเมื่อมีกฎต้นทางที่ทำตามได้หรือผู้ใช้ยืนยันค่าภายหลัง"
)
IMPLEMENTATION_DEFAULT_PARTIAL_CLOSE = (
    f"{_implementation_default_tag('partial_close')} เมื่อแหล่งข้อมูลไม่ระบุ ให้ตั้ง "
    "PartialClose=false; เปิดใช้ได้เฉพาะเมื่อมีกฎต้นทางที่ทำตามได้หรือผู้ใช้ยืนยันค่าภายหลัง"
)
IMPLEMENTATION_DEFAULT_EXIT_MANAGEMENT = "\n".join(
    (
        IMPLEMENTATION_DEFAULT_TRAILING_STOP,
        IMPLEMENTATION_DEFAULT_BREAK_EVEN,
        IMPLEMENTATION_DEFAULT_PARTIAL_CLOSE,
    )
)
IMPLEMENTATION_DEFAULT_RECOVERY_RULES = (
    f"{_implementation_default_tag('recovery')} เมื่อแหล่งข้อมูลไม่มีระบบแก้ไม้ที่ครบและทำตามได้ "
    "ให้ใช้ RecoveryMode=none: ไม่เปิด Grid, Martingale, Averaging, Hedging, ไม่เพิ่มล็อตหลังขาดทุน, "
    "ไม่เพิ่มไม้ในสถานะที่ขาดทุน และไม่ retry ในแท่งเดิม หลังปิดสถานะต้องรอสัญญาณใหม่จากแท่งปิด"
)
IMPLEMENTATION_DEFAULT_RISK_SIZING = (
    f"{_implementation_default_tag('risk_sizing')} เมื่อแหล่งข้อมูลไม่ระบุขนาดความเสี่ยง/ล็อต ให้ใช้ "
    "PositionSizingMode=fixed_lot และ FixedLot=0.01 เป็นค่าเริ่มต้นธรรมดา. ทั้งสองค่าต้องเป็น "
    "EA inputs; ตรวจ MinLot, MaxLot, VolumeStep และ Margin ก่อนส่งคำสั่ง หาก FixedLot ไม่ valid "
    "ให้ข้ามสัญญาณ ห้ามยกล็อตขึ้นเป็น MinLot และห้ามเพิ่มล็อตหลังแพ้. โหมด percent_equity เป็น "
    "ตัวเลือกที่ผู้ใช้เปิดภายหลังได้ผ่าน RiskPercent input ตาม metadata แต่ไม่ใช่ค่าเริ่มต้น"
)
IMPLEMENTATION_DEFAULT_LOT_CALCULATION = (
    f"{_implementation_default_tag('lot_calculation')} เมื่อแหล่งข้อมูลระบุเปอร์เซ็นต์ความเสี่ยง "
    "แต่ไม่ระบุสูตรล็อต ให้คง RiskPercent จากแหล่งเดิม แล้วคำนวณ "
    "RiskMoney=Equity*RiskPercent/100 และ Lot=RiskMoney/LossPerLotAtSL จากระยะ SL จริง, "
    "TickSize และ TickValue; ปัดลงตาม VolumeStep และข้ามสัญญาณเมื่อคำนวณอย่างปลอดภัยไม่ได้"
)
IMPLEMENTATION_DEFAULT_POSITION_CAP = (
    f"{_implementation_default_tag('position_cap')} เมื่อแหล่งข้อมูลไม่ระบุจำนวนสถานะ ให้ใช้ "
    "MaxOpenPositionsPerSymbolMagic=1 โดยนับทั้งสถานะเปิดและคำสั่งรอของ Symbol+Magic เดียวกัน "
    "และใช้ blocking guard ก่อนส่งคำสั่งใหม่ทุกครั้ง"
)
IMPLEMENTATION_DEFAULT_CLOSED_BAR_EXECUTION = (
    f"{_implementation_default_tag('closed_bar_execution')} เมื่อแหล่งข้อมูลไม่ระบุจังหวะประมวลผล "
    "ให้ใช้ SignalBarShift=1 และ TradeOnNewBar=true: อ่านสัญญาณ/ราคา OHLC จากแท่งปิด [1] "
    "หรือเก่ากว่า และส่งคำสั่งได้เพียงครั้งเดียวบน tick แรกของแท่งใหม่. ตอนเริ่ม EA ให้จำเวลา "
    "แท่งปัจจุบันแล้ว return ก่อน เพื่อไม่เปิดย้อนหลังทันที. SignalBarShift และ TradeOnNewBar "
    "ต้องเป็น EA inputs แต่ค่า SignalBarShift ต่ำสุดคือ 1"
)
IMPLEMENTATION_DEFAULT_ORDER_EXECUTION = (
    f"{_implementation_default_tag('order_type')} เมื่อแหล่งข้อมูลไม่ระบุชนิดคำสั่ง ให้ใช้ "
    "Market order โดยยึดทิศทาง Buy/Sell และจังหวะเข้าจากกฎต้นทาง; หากต้นทางไม่ระบุทิศทางจึงรองรับ "
    "Market Buy/Sell ทั้งสองด้าน. ไม่สร้าง Buy Stop, Sell Stop, Buy Limit หรือ Sell Limit "
    "โดยอัตโนมัติ"
)
IMPLEMENTATION_DEFAULT_OPTIMIZATION_INPUTS = (
    f"{_implementation_default_tag('optimization_inputs')} "
    "INPUT_METADATA_VERSION=ea-optimization-inputs-v1. ใช้เฉพาะ component ที่ปรากฏใน "
    "DEFAULTED_COMPONENTS: FixedLot(double,default=0.01,start=0.01,step=0.01,stop=0.10); "
    "RiskPercent(double,optional percent_equity,default=1.0,start=0.25,step=0.25,stop=3.0); "
    "StopLossPoints(int,default=300,start=100,step=100,stop=1000); "
    "TakeProfitPoints(int,default=600,start=200,step=200,stop=2000); "
    "MaxOpenPositionsPerSymbolMagic(int,default=1,start=1,step=1,stop=3); "
    "SignalBarShift(int,default=1,optimize=false,min=1); TradeOnNewBar(bool,default=true,optimize=false); "
    "PositionSizingMode(enum,default=fixed_lot,values=fixed_lot|percent_equity,optimize=false). "
    "ค่าตัวเลขหรือหน่วยที่แหล่งข้อมูลระบุเองต้องคงเป็น authoritative input เดิมและห้ามถูก metadata "
    "ชุดนี้เขียนทับ; ช่วง Start/Step/Stop เป็นเพียงช่วงเริ่มต้นสำหรับทดสอบ ไม่ใช่ผล Optimize"
)
IMPLEMENTATION_DEFAULT_EXIT_RULES = "\n".join(
    (
        IMPLEMENTATION_DEFAULT_STOP_LOSS,
        IMPLEMENTATION_DEFAULT_TAKE_PROFIT,
        IMPLEMENTATION_DEFAULT_EXIT_MANAGEMENT,
    )
)
IMPLEMENTATION_DEFAULT_MONEY_MANAGEMENT = "\n".join(
    (
        IMPLEMENTATION_DEFAULT_RISK_SIZING,
        IMPLEMENTATION_DEFAULT_POSITION_CAP,
    )
)
_IMPLEMENTATION_COMPONENT_DEFAULTS = {
    "stop_loss": IMPLEMENTATION_DEFAULT_STOP_LOSS,
    "take_profit": IMPLEMENTATION_DEFAULT_TAKE_PROFIT,
    "trailing_stop": IMPLEMENTATION_DEFAULT_TRAILING_STOP,
    "break_even": IMPLEMENTATION_DEFAULT_BREAK_EVEN,
    "partial_close": IMPLEMENTATION_DEFAULT_PARTIAL_CLOSE,
    "recovery": IMPLEMENTATION_DEFAULT_RECOVERY_RULES,
    "risk_sizing": IMPLEMENTATION_DEFAULT_RISK_SIZING,
    "lot_calculation": IMPLEMENTATION_DEFAULT_LOT_CALCULATION,
    "position_cap": IMPLEMENTATION_DEFAULT_POSITION_CAP,
    "closed_bar_execution": IMPLEMENTATION_DEFAULT_CLOSED_BAR_EXECUTION,
    "order_type": IMPLEMENTATION_DEFAULT_ORDER_EXECUTION,
    "optimization_inputs": IMPLEMENTATION_DEFAULT_OPTIMIZATION_INPUTS,
}
IMPLEMENTATION_DEFAULT_NOTE = (
    f"[{IMPLEMENTATION_DEFAULT_MARKER}][POLICY={IMPLEMENTATION_DEFAULT_POLICY_ID}] "
    "ค่าที่ติดป้ายนี้เป็นสมมุติฐานการเขียน EA เพื่อให้ Source ทำงานต่อได้ ไม่ใช่ข้อเท็จจริงจาก "
    "แหล่งอ้างอิง ผู้ใช้เปลี่ยนเป็น Inputs ได้ และต้อง Compile, Backtest, Optimize และทดลองบัญชี "
    "Demo ก่อนพิจารณาใช้งานจริง"
)
IMPLEMENTATION_DEFAULT_LIMITATION = (
    f"[{IMPLEMENTATION_DEFAULT_MARKER}][POLICY={IMPLEMENTATION_DEFAULT_POLICY_ID}] "
    "องค์ประกอบบางส่วนเป็นค่าเริ่มต้นเชิงวิศวกรรมที่แหล่งข้อมูลไม่ได้ระบุ จึงต้องตรวจด้วย "
    "Compile, Backtest, Optimize และ Demo"
)
_ALL_IMPLEMENTATION_COMPONENT_NAMES = ",".join(_IMPLEMENTATION_COMPONENT_DEFAULTS)
IMPLEMENTATION_DEFAULT_FIELD_RESERVE = {
    "recoveryRules": len(IMPLEMENTATION_DEFAULT_RECOVERY_RULES) + 1,
    "exitRules": len(IMPLEMENTATION_DEFAULT_EXIT_RULES) + 1,
    "moneyManagement": max(
        len(IMPLEMENTATION_DEFAULT_RISK_SIZING)
        + 1
        + len(IMPLEMENTATION_DEFAULT_POSITION_CAP),
        len(IMPLEMENTATION_DEFAULT_LOT_CALCULATION)
        + 1
        + len(IMPLEMENTATION_DEFAULT_POSITION_CAP),
    ) + 1,
    "orderExecution": (
        len(IMPLEMENTATION_DEFAULT_ORDER_EXECUTION)
        + 1
        + len(IMPLEMENTATION_DEFAULT_CLOSED_BAR_EXECUTION)
        + 1
    ),
    "additionalNotes": (
        len(IMPLEMENTATION_DEFAULT_NOTE)
        + len(" DEFAULTED_COMPONENTS=")
        + len(_ALL_IMPLEMENTATION_COMPONENT_NAMES)
        + 1
        + len(IMPLEMENTATION_DEFAULT_OPTIMIZATION_INPUTS)
        + 1
    ),
}
IMPLEMENTATION_DEFAULT_OUTPUT_MAX_LENGTHS = {
    field: _FIELD_LIMITS[field] - reserve
    for field, reserve in IMPLEMENTATION_DEFAULT_FIELD_RESERVE.items()
}
IMPLEMENTATION_DEFAULT_POLICY_PROMPT = f"""
Mandatory EA-ready implementation-default policy (source facts always win per component):
- Never leave exitRules, moneyManagement, orderExecution, or recoveryRules as only unknown, unspecified, not_publicly_stated, or user must decide.
- Apply policy `{IMPLEMENTATION_DEFAULT_POLICY_ID}` component by component. Preserve every source-backed rule. For each missing component only, label the added text [{IMPLEMENTATION_DEFAULT_MARKER}][POLICY={IMPLEMENTATION_DEFAULT_POLICY_ID}][COMPONENT=<name>] so it is never represented as a source fact. Example: a sourced SL plus a missing TP receives only the TP default; it must never receive a second conflicting SL.
- Missing SL/TP: use editable broker-point inputs StopLossPoints=300 and TakeProfitPoints=600, enforce broker stop floor plus ExecutionBufferPoints=2, and keep source-backed values and units authoritative per component. Trailing, break-even, and partial close stay disabled unless sourced.
- Missing Money Management sizing: default to PositionSizingMode=fixed_lot and FixedLot=0.01 with broker volume/margin validation. Expose optional percent_equity mode with RiskPercent=1.0 metadata; if a source states a risk percentage but omits the lot formula, preserve that percentage and add only the labeled TickSize/TickValue lot-calculation default. Missing position cap: when complete recoveryRules states a maximum level/position count, bind MaxOpenPositionsPerSymbolMagic to at least that total so the position guard cannot disable the recovery path; otherwise use MaxOpenPositionsPerSymbolMagic=1. Count both live and pending orders for the same Symbol+Magic. Never round up or increase size after a loss.
- Missing order type: use Market while preserving every source-backed direction and timing rule. Missing execution timing: use SignalBarShift=1 and TradeOnNewBar=true, prime the current bar on startup, read only closed bars, and execute once on the first tick of a new bar. Do not invent pending orders or overwrite explicit intrabar/session timing.
- If the source explicitly states no recovery, preserve that fact and spell out RecoveryMode=none. If recovery is absent, or a source merely names Grid/Martingale/Averaging/Hedging without complete trigger, spacing, lot rule, level cap, basket exit, and reset/abort rules, keep it disabled: write the source mention, then add the labeled RecoveryMode=none implementation default. Do not silently implement an incomplete recovery system.
- Add versioned optimization input metadata to additionalNotes with FixedLot, optional RiskPercent, StopLossPoints, TakeProfitPoints, MaxOpenPositionsPerSymbolMagic, SignalBarShift, TradeOnNewBar and PositionSizingMode. Apply metadata defaults only to DEFAULTED_COMPONENTS; preserve source-backed values/units. Add [{IMPLEMENTATION_DEFAULT_MARKER}] to additionalNotes and limitations, state that these are user-configurable engineering assumptions, and require Compile, Backtest, Optimize, and Demo validation. Never claim assumed values came from the two public sources.
""".strip()
_DEFAULT_TEXT = {
    # Keep this historical normalization default byte-for-byte stable.  New
    # Runner results receive the versioned implementation policy through
    # ``apply_strategy_brief_implementation_defaults`` before digesting.
    "recoveryRules": (
        "แหล่งข้อมูลไม่ระบุระบบการแก้ไม้ จึงห้ามเพิ่ม Grid, Martingale, "
        "Averaging หรือ Hedging โดยอัตโนมัติ"
    ),
    "displayRequirements": (
        "ใช้หน้าจอมาตรฐาน: แสดงชื่อระบบ สถานะสัญญาณ Balance, Equity และ Spread"
    ),
    "additionalNotes": "ไม่มีหมายเหตุเพิ่มเติม",
}
_DEFAULT_LIMITATION = (
    "ข้อมูลนี้เป็นข้อกำหนดสำหรับสร้าง Source EA เท่านั้น ไม่ใช่ผล Compile, "
    "Backtest หรือการรับประกันกำไร"
)
_RESERVED_HOSTS = frozenset({"example.com", "example.org", "example.net"})
_RESERVED_SUFFIXES = (".example", ".invalid", ".test", ".localhost")
_COMMON_SECOND_LEVEL_SUFFIXES = frozenset(
    {"co.uk", "org.uk", "com.au", "net.au", "co.jp", "co.th", "com.sg", "com.hk"}
)


class StrategyBriefValidationError(ValueError):
    """A bounded list of stable validation issues for one compact brief."""

    def __init__(self, issues: list[dict[str, str]]):
        self.issues = [dict(item) for item in issues[:40]]
        codes = ", ".join(item.get("code", "BRIEF_INVALID") for item in self.issues[:8])
        super().__init__(
            "EA strategy brief is invalid" + (f": {codes}" if codes else "")
        )


def _issue(issues: list[dict[str, str]], code: str, path: str, message: str) -> None:
    issues.append({"code": code, "path": path, "message": message})


def _normalize_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    lines = [" ".join(line.split()) for line in value.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


_UNSPECIFIED_OPERATIONAL_MARKERS = (
    "not_publicly_stated",
    "not publicly stated",
    "not specified",
    "unspecified",
    "unknown",
    "source does not state",
    "sources do not state",
    "source did not state",
    "sources did not state",
    "not disclosed",
    "undisclosed",
    "no evidence found",
    "no evidence of",
    "not documented",
    "to be determined",
    "to be decided",
    "tbd",
    "unavailable",
    "not available",
    "unclear",
    "optional",
    "may be used",
    "should be considered",
    "แหล่งข้อมูลไม่ระบุ",
    "แหล่งไม่ระบุ",
    "ไม่พบข้อมูล",
    "ไม่มีข้อมูล",
    "ยังไม่ระบุ",
    "ยังไม่ชัดเจน",
    "ไม่ชัดเจน",
    "รอพิจารณา",
    "อาจใช้",
)
_DEFERRED_TO_USER_MARKERS = (
    "user input",
    "user-defined",
    "user defined",
    "user-selected",
    "user selected",
    "user decides",
    "user discretion",
    "user choice",
    "ผู้ใช้กำหนด",
    "ให้ผู้ใช้เลือก",
    "กำหนดเอง",
)
_OPERATIONAL_CLAUSE_SPLIT = re.compile(
    r"(?:[\r\n;•]+|(?<=[.!?])\s+|\s+(?:and|but|และ|แต่)\s+|,)"
)
_STOP_LOSS_ALIASES = (
    r"\bstop[ _-]?loss\w*",
    r"\bsl\b",
    r"\bhard[ -]?stop\b",
    r"\bprotective\s+stop\b",
    r"\binitial\s+stop\b",
    r"\b\d+(?:\.\d+)?[- ]?(?:pip|point|atr)[- ]+stop\b",
    r"ตัดขาดทุน",
    r"หยุดขาดทุน",
)
_TAKE_PROFIT_ALIASES = (
    r"\btake[ _-]?profit\w*",
    r"\btp\b",
    r"\bprofit\s+target\b",
    r"\btarget\s+profit\b",
    r"\breward\s+target\b",
    r"\btarget\s+(?:at|of)\b|\btarget\s*(?:=|:)",
    r"\b\d+(?:\.\d+)?[- ]?(?:pip|point|atr)[- ]+target\b",
    r"เป้ากำไร",
    r"เป้าหมายกำไร",
    r"ทำกำไร",
)
_TRAILING_STOP_ALIASES = (
    r"trailing[ _-]?stop",
    r"\btrail(?:s|ed|ing)?\b",
    r"เลื่อน.*(?:stop|\bsl\b|จุดตัดขาดทุน)",
)
_BREAK_EVEN_ALIASES = (
    r"break[ _-]?even",
    r"breakeven",
    r"(?:move|set|shift).{0,24}(?:stop|sl).{0,24}(?:to|at)\s*b/?e\b",
    r"คุ้มทุน",
)
_PARTIAL_CLOSE_ALIASES = (
    r"partial[ _-]?close",
    r"scale[ _-]?out",
    r"take\s+partial",
    r"take\s+(?:half|one[- ]?half|\d+(?:\.\d+)?\s*%)\s+off",
    r"close\s+(?:half|one[- ]?half|\d+(?:\.\d+)?\s*%)",
    r"แบ่งปิด",
    r"ปิดบางส่วน",
)
_MARKET_ORDER_ALIASES = (
    r"\bmarket\s+(?:buy|sell|order|execution)",
    r"\b(?:buy|sell)\s+at\s+market\b",
    r"\benter\s+at\s+market\b",
    r"คำสั่ง\s*market",
)
_PENDING_ORDER_ALIASES = (
    r"\bbuy[ -]?(?:stop|limit)\b",
    r"\bsell[ -]?(?:stop|limit)\b",
    r"\b(?:stop|limit)[ _-]?entry\b",
    r"\b(?:stop|limit)\s+order\b",
    r"\bpending\s+order\b",
    r"คำสั่ง\s*รอ",
)
_EXPLICIT_EXECUTION_TIMING_PATTERNS = (
    r"\bclosed[ -]?bar\b",
    r"\bcompleted[ -]?bar\b",
    r"\bfirst\s+tick\s+(?:of|on)\s+(?:a\s+)?new\s+bar\b",
    r"\bnew[ -]?bar\b",
    r"\bSignalBarShift\s*=\s*[1-9]\d*\b",
    r"\bTradeOnNewBar\s*=\s*(?:true|false)\b",
    r"\b(?:Open|High|Low|Close)\s*\[\s*[1-9]\d*\s*\]",
    r"\bbar\s*(?:shift\s*)?\[?\s*[1-9]\d*\s*\]?",
    r"\bintra[ -]?bar\b",
    r"\bcurrent[ -]?bar\b",
    r"\bbar\s*(?:shift\s*)?\[?\s*0\s*\]?",
    r"\b(?:Open|High|Low|Close)\s*\[\s*0\s*\]",
    r"\b(?:every|each|first)\s+tick\b",
    r"\bon\s*tick\b",
    r"\b(?:immediately|real[ -]?time)\b",
    r"\b(?:session|market)\s+(?:open|close)\b",
    r"\b\d{1,2}:\d{2}\b",
    r"แท่งปิด|แท่งที่ปิดแล้ว|แท่งใหม่|ทุก\s*tick|ทันที|ระหว่างแท่ง|เวลา\s*\d{1,2}[:.]\d{2}",
)


def _execution_timing_resolved(text: str) -> bool:
    """Return whether source prose explicitly chooses closed-bar or intrabar timing."""

    source_text = re.sub(r"\[[^\]\r\n]{0,240}\]", " ", text)
    return any(
        not _clause_is_unresolved(clause)
        and any(
            re.search(pattern, clause, flags=re.IGNORECASE)
            for pattern in _EXPLICIT_EXECUTION_TIMING_PATTERNS
        )
        for clause in _operational_clauses(source_text)
    )


def _component_default_present(text: str, component: str) -> bool:
    canonical = _IMPLEMENTATION_COMPONENT_DEFAULTS.get(component)
    return bool(canonical and canonical in text)


def _operational_clauses(text: str) -> list[str]:
    return [part.strip() for part in _OPERATIONAL_CLAUSE_SPLIT.split(text) if part.strip()]


def _clause_is_unresolved(text: str) -> bool:
    lowered = text.casefold()
    if any(marker in lowered for marker in _UNSPECIFIED_OPERATIONAL_MARKERS):
        return True
    if any(
        marker in lowered
        for marker in ("user decides", "user discretion", "user choice", "ให้ผู้ใช้เลือก")
    ):
        return True
    if re.search(
        r"(?:not|is not|isn't|was not|ไม่ได้|ไม่มี|ยังไม่).{0,40}"
        r"(?:stated|specified|documented|ระบุ|ข้อมูล)",
        lowered,
    ):
        return True
    return not re.search(r"\d", text) and any(
        marker in lowered for marker in _DEFERRED_TO_USER_MARKERS
    )


def _clause_explicitly_disables_component(
    clause: str,
    aliases: tuple[str, ...],
) -> bool:
    return any(
        re.search(
            rf"(?:\bno\b|\bwithout\b|\bnever\b|\bdo\s+not\b|"
            rf"ไม่(?:ใช้|ตั้ง|กำหนด|เปิด)|ไม่มี|ห้าม|ปิดใช้งาน)"
            rf".{{0,24}}(?:{alias})",
            clause,
            flags=re.IGNORECASE,
        )
        or re.search(
            rf"(?:{alias}).{{0,24}}(?:=\s*(?:none|false|off|disabled|0)\b|"
            r"\b(?:is\s+)?(?:disabled|off)\b|ไม่(?:ใช้|ตั้ง|กำหนด|เปิด)|ไม่มี|ปิดใช้งาน)",
            clause,
            flags=re.IGNORECASE,
        )
        for alias in aliases
    )


def _component_enabled_requested(text: str, aliases: tuple[str, ...]) -> bool:
    """Return True only for a positive, resolved request for one component."""

    source_text = re.sub(r"\[[^\]\r\n]{0,240}\]", " ", text)
    for clause in _operational_clauses(source_text):
        if not any(re.search(alias, clause, flags=re.IGNORECASE) for alias in aliases):
            continue
        if _clause_is_unresolved(clause):
            continue
        if _clause_explicitly_disables_component(clause, aliases):
            continue
        return True
    return False


_POSITION_CAP_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "single": 1,
    "หนึ่ง": 1,
    "สอง": 2,
    "สาม": 3,
    "สี่": 4,
    "ห้า": 5,
    "หก": 6,
    "เจ็ด": 7,
    "แปด": 8,
    "เก้า": 9,
    "สิบ": 10,
}


def _requested_position_cap(text: str) -> int | None:
    lowered = text.casefold()
    token = (
        r"one|two|three|four|five|six|seven|eight|nine|ten|single|"
        r"หนึ่ง|สอง|สาม|สี่|ห้า|หก|เจ็ด|แปด|เก้า|สิบ|\d+"
    )
    split_cap = re.search(
        rf"({token})\s+(?:open\s+)?positions?.{{0,32}}(?:and|plus|และ)\s+"
        rf"({token})\s+pending\s+orders?",
        lowered,
        flags=re.IGNORECASE,
    )
    if split_cap:
        values: list[int] = []
        for raw in split_cap.groups():
            try:
                values.append(int(raw))
            except ValueError:
                values.append(_POSITION_CAP_WORDS.get(raw.casefold(), 0))
        if all(value > 0 for value in values):
            return sum(values)
    patterns = (
        r"maxopenpositionspersymbolmagic\s*=\s*(\d+)",
        rf"(?:max(?:imum)?(?:\s+of)?|at\s+most|up\s+to|no\s+more\s+than)\s+({token})"
        r".{0,32}(?:positions?|trades?|orders?|สถานะ|ออเดอร์|ออร์เดอร์|ไม้)",
        rf"(?:max(?:imum)?\s+)?(?:open\s+)?(?:positions?|trades?|orders?)"
        rf"\s*(?:=|:|to)?\s*({token})\b",
        rf"maximum\s+(?:number\s+of\s+)?(?:open\s+)?(?:positions?|trades?|orders?)"
        rf"(?:\s+per\s+\w+)?\s+(?:is|=|:)\s*({token})\b",
        rf"(?:position|trade|order)\s+limit\s*(?:is|=|:)?\s*({token})\b",
        rf"({token}).{{0,32}}(?:positions?|trades?|orders?)"
        r".{0,24}(?:max(?:imum)?|at\s+a\s+time)",
        rf"(?:allow|permit)\s+({token}).{{0,24}}"
        r"(?:concurrent\s+)?(?:positions?|trades?|orders?)",
        rf"({token})\s+concurrent\s+(?:positions?|trades?|orders?)",
        rf"never\s+(?:hold|open|allow).{{0,24}}more\s+than\s+({token})"
        r".{0,24}(?:positions?|trades?|orders?)",
        rf"never\s+(?:hold|open|allow).{{0,24}}over\s+({token})"
        r".{0,24}(?:positions?|trades?|orders?)",
        rf"limit.{{0,32}}(?:positions?|trades?|orders?).{{0,16}}(?:to|at)\s+({token})",
        rf"limit.{{0,32}}(?:positions?|trades?|orders?).{{0,24}}no\s+more\s+than\s+({token})",
        rf"only\s+({token})\s+(?:simultaneous|concurrent)\s+(?:positions?|trades?|orders?)",
        rf"(?:สูงสุด|ไม่เกิน)\s*({token})\s*(?:สถานะ|ออเดอร์|ออร์เดอร์|ไม้|รายการ)",
        rf"(?:สถานะ|ออเดอร์|ออร์เดอร์|ไม้).{{0,24}}ไม่เกิน\s*({token})(?:\s*รายการ)?",
        rf"จำกัดจำนวน(?:สถานะ|ออเดอร์|ออร์เดอร์|ไม้)\s*({token})(?:\s*รายการ)?",
    )
    for pattern in patterns:
        match = re.search(pattern, lowered, flags=re.IGNORECASE)
        if not match:
            continue
        token = match.group(1).casefold()
        try:
            value = int(token)
        except ValueError:
            value = _POSITION_CAP_WORDS.get(token, 0)
        if value > 0:
            return value
    return None


def _component_has_resolved_rule(
    text: str,
    aliases: tuple[str, ...],
    details: str | None = None,
    *,
    allow_explicit_disable: bool = False,
) -> bool:
    # Bracketed provenance metadata is never itself evidence that an
    # operational component has a usable rule or numeric parameter.
    source_text = re.sub(r"\[[^\]\r\n]{0,240}\]", " ", text)
    matching = [
        clause
        for clause in _operational_clauses(source_text)
        if any(re.search(alias, clause, flags=re.IGNORECASE) for alias in aliases)
    ]
    for clause in matching:
        if _clause_is_unresolved(clause):
            continue
        if allow_explicit_disable and _clause_explicitly_disables_component(
            clause,
            aliases,
        ):
            return True
        if details is None or re.search(details, clause, flags=re.IGNORECASE):
            return True
    return False


def _recovery_explicit_none(text: str) -> bool:
    lowered = text.casefold()
    conditional_no_recovery = re.search(
        r"\bno\s+recovery\s+(?:on|until|before|for)\b|"
        r"(?:ยังไม่|ไม่).{0,16}แก้ไม้.{0,24}(?:จนกว่า|ก่อน|ครั้งแรก)",
        lowered,
    )
    later_recovery_enabled = _component_enabled_requested(
        text,
        (
            r"\bgrid\b",
            r"\bmartingale\b",
            r"\baverag(?:e|ing)\b",
            r"\bhedg(?:e|ing)\b",
            r"เพิ่มไม้|แก้ไม้|ถัวเฉลี่ย",
        ),
    )
    if conditional_no_recovery and later_recovery_enabled:
        return False
    missing_recovery_statement = re.search(
        r"\bno\s+recovery(?:\s+(?:section|rules?|method|strategy))?"
        r".{0,40}(?:available|provided|located|found|documented|described|stated|specified)\b|"
        r"(?:no|without).{0,24}recovery.{0,24}"
        r"(?:described|stated|specified|documented|found|information|details|evidence)|"
        r"\bno\b.{0,24}(?:evidence|documentation|documented|details|information)"
        r".{0,32}\brecovery\b|"
        r"\bno\s+documented\s+recovery\b|"
        r"(?:recovery).{0,24}(?:not|isn't|wasn't).{0,16}"
        r"(?:described|stated|specified|documented|found)|"
        r"ไม่พบ.{0,24}(?:ข้อมูล|หลักฐาน).{0,24}(?:แก้ไม้|recovery)",
        lowered,
    )
    explicit_no_recovery = re.search(
        r"(?:recovery\s*mode\s*=\s*none\b|"
        r"\brecovery\s*=\s*none\b|"
        r"\brecovery\s+(?:is\s+)?(?:disabled|off)\b|"
        r"\b(?:do\s+not|never)\s+(?:use\s+)?recovery\b|"
        r"\bdisable\s+recovery\b|"
        r"(?:\bno\b|\bwithout\b).{0,18}\brecovery\b(?!\s*(?:is\s+)?"
        r"(?:described|stated|specified|documented))|"
        r"ไม่มี(?:การ|ระบบ)?แก้ไม้|ไม่ใช้ระบบแก้ไม้|ไม่เปิดระบบแก้ไม้|"
        r"ห้ามแก้ไม้|ไม่แก้ไม้)",
        lowered,
    )
    disabled_modes = all(
        re.search(pattern, lowered)
        for pattern in (
            r"(?:\bno\b|\bwithout\b|ไม่ใช้|ไม่เปิด|ห้ามใช้).{0,18}\bgrid\b",
            r"(?:\bno\b|\bwithout\b|ไม่ใช้|ไม่เปิด|ห้ามใช้).{0,18}\bmartingale\b",
            r"(?:\bno\b|\bwithout\b|ไม่ใช้|ไม่เปิด|ห้ามใช้).{0,18}\baverag(?:e|ing)\b",
            r"(?:\bno\b|\bwithout\b|ไม่ใช้|ไม่เปิด|ห้ามใช้).{0,18}\bhedg(?:e|ing)\b",
        )
    )
    return bool(
        (explicit_no_recovery and not missing_recovery_statement) or disabled_modes
    )


def _paired_protection_resolution(text: str, detail: str) -> tuple[bool, bool]:
    """Resolve compact ``SL/TP`` shorthand without letting one side hide the other."""

    source = re.sub(r"\[[^\]\r\n]{0,240}\]", " ", text)
    stop_label = r"(?:\bstop[ _-]?loss\b|\bsl\b|\bhard[ -]?stop\b|\binitial\s+stop\b)"
    take_label = r"(?:\btake[ _-]?profit\b|\btp\b|\bprofit\s+target\b|\breward\s+target\b)"
    label = re.compile(
        rf"(?P<first>{stop_label})\s*(?:/|&|and|และ)\s*"
        rf"(?P<second>{take_label})|"
        rf"(?P<first_rev>{take_label})\s*(?:/|&|and|และ)\s*"
        rf"(?P<second_rev>{stop_label})",
        flags=re.IGNORECASE,
    )
    for match in label.finditer(source):
        tail = re.split(r"[;\r\n]", source[match.end() : match.end() + 240], maxsplit=1)[0]
        tail = re.sub(
            r"^\s*(?:(?:use|uses|using|are|is)|=|:|-)+\s*",
            "",
            tail,
            flags=re.IGNORECASE,
        )
        if not tail:
            continue
        values = [part.strip() for part in re.split(r"\s*(?:/|&|\band\b|และ)\s*", tail, maxsplit=1, flags=re.IGNORECASE)]
        if len(values) != 2:
            continue
        shared_unit_match = re.search(
            r"\b(?:atr|pips?|points?|risk.?reward|rr)\b|%|(?:แท่ง|จุด)",
            tail,
            flags=re.IGNORECASE,
        )
        shared_unit = shared_unit_match.group(0) if shared_unit_match else ""
        resolved = tuple(
            bool(
                value
                and not _clause_is_unresolved(value)
                and re.search(
                    detail,
                    f"{value} {shared_unit}" if shared_unit else value,
                    flags=re.IGNORECASE,
                )
            )
            for value in values
        )
        if match.group("first_rev"):
            return resolved[1], resolved[0]
        return resolved[0], resolved[1]
    return False, False


def _recovery_default_needed(text: str) -> bool:
    if _component_default_present(text, "recovery"):
        return False
    lowered = text.casefold()
    if _recovery_explicit_none(text):
        return False
    named_mode = re.search(
        r"(?:grid|martingale|averag(?:e|ing)|hedg(?:e|ing)|แก้ไม้|ถัวเฉลี่ย|"
        r"(?:add|open).{0,24}(?:position|order|trade)|scale[ _-]?in|เพิ่มไม้)",
        lowered,
    )
    if not named_mode:
        return True
    detail_groups = (
        r"(?:trigger|after.{0,16}loss|drawdown|เมื่อ.*ขาดทุน|เริ่มเมื่อ)",
        r"(?:spacing|distance|step|atr|pip|point|ระยะ|ห่าง)",
        r"(?:lot|volume|multiplier|คูณ|ขนาดล็อต)",
        r"(?:max(?:imum)?(?:\s+(?:levels?|orders?|positions?|trades?))?|"
        r"order\s+cap|level\s+cap|สูงสุด|จำนวนไม้)",
        r"(?:basket.{0,40}(?:take\s*profit|stop\s*loss|\btp\b|\bsl\b|"
        r"close|exit)|(?:take\s*profit|stop\s*loss|\btp\b|\bsl\b|close|exit)"
        r".{0,40}basket|ปิดตะกร้า|ตะกร้า.{0,24}(?:กำไร|ขาดทุน|ปิด))",
        r"(?:reset|abort|cooldown|เริ่มใหม่|ยกเลิก)",
    )
    clauses = _operational_clauses(text)

    detail_evidence = (
        r"(?:\d|each|every|first|consecutive|on\s+loss|เมื่อ|ทุกครั้ง)",
        r"(?:\d|atr|pip|point|tick|bar|แท่ง|จุด)",
        r"(?:\d|same|fixed|equal|multiplier|formula|สูตร|คงที่|เท่าเดิม|คูณ)",
        r"(?:\d|\bone\b|\bsingle\b|หนึ่ง)",
        r"(?:basket|ตะกร้า).*(?:\d|atr|pip|point|rr|risk.?reward|opposite|"
        r"signal|break.?even|close|exit|กำไร|ขาดทุน|ปิด)",
        r"(?:reset|abort|cooldown|basket\s+close|flat|เริ่มใหม่|ยกเลิก|ปิดตะกร้า)",
    )

    def resolved_detail(pattern: str, evidence_pattern: str) -> bool:
        for clause in clauses:
            if not re.search(pattern, clause, flags=re.IGNORECASE):
                continue
            if _clause_is_unresolved(clause):
                continue
            if not re.search(
                evidence_pattern,
                clause,
                flags=re.IGNORECASE,
            ):
                continue
            return True
        return False

    return not all(
        resolved_detail(pattern, detail_evidence[index])
        for index, pattern in enumerate(detail_groups)
    )


def _requested_recovery_position_cap(text: str) -> int | None:
    """Return the minimum total position cap required by complete recovery prose.

    Recovery is intentionally ignored when it is disabled or incomplete because
    the implementation-default layer will fail closed to ``RecoveryMode=none``.
    A phrase that explicitly says *additional* positions includes the original
    position in the returned total; ordinary ``max N levels`` is treated as the
    total level/position cap stated by the brief.
    """

    source = re.sub(r"\[[^\]\r\n]{0,240}\]", " ", _normalize_text(text))
    if (
        not source
        or _recovery_explicit_none(source)
        or _recovery_default_needed(source)
    ):
        return None
    recovery_requested = _component_enabled_requested(
        source,
        (
            r"\bgrid\w*\b",
            r"\bmartingale\w*\b",
            r"\baverag(?:e|ing)\w*\b",
            r"\bhedg(?:e|ing)\w*\b",
            r"(?:add|open)\s+(?:another|additional|extra|new)\s+"
            r"(?:position|order|trade)",
            r"scale[ _-]?in",
            r"เพิ่มไม้|แก้ไม้|ถัวเฉลี่ย",
        ),
    )
    if not recovery_requested:
        return None
    token = (
        r"one|two|three|four|five|six|seven|eight|nine|ten|single|"
        r"หนึ่ง|สอง|สาม|สี่|ห้า|หก|เจ็ด|แปด|เก้า|สิบ|\d+"
    )
    unit = (
        r"levels?|positions?|trades?|orders?|entries|สถานะ|ออเดอร์|"
        r"ออร์เดอร์|ไม้|ระดับ"
    )
    patterns = (
        rf"(?:max(?:imum)?|at\s+most|up\s+to|no\s+more\s+than|"
        rf"level\s+cap|position\s+cap|order\s+cap)\s*(?:=|:|is|of)?\s*"
        rf"({token})\s*((?:additional|extra)\s+)?(?:recovery\s+)?(?:{unit})",
        rf"(?:maximum\s+)?(?:recovery\s+)?(?:{unit})\s*"
        rf"(?:cap|limit|max(?:imum)?)?\s*(?:=|:|is|of)?\s*({token})\b()",
        rf"(?:สูงสุด|ไม่เกิน)\s*({token})\s*(เพิ่มอีก\s*)?(?:{unit})",
        rf"(?:{unit}).{{0,24}}(?:สูงสุด|ไม่เกิน)\s*({token})\b()",
    )
    lowered = source.casefold()
    for pattern in patterns:
        match = re.search(pattern, lowered, flags=re.IGNORECASE)
        if not match:
            continue
        raw_value = match.group(1).casefold()
        try:
            value = int(raw_value)
        except ValueError:
            value = _POSITION_CAP_WORDS.get(raw_value, 0)
        if value <= 0:
            continue
        explicitly_additional = bool(match.group(2))
        return value + 1 if explicitly_additional else value
    return None


def _recovery_position_cap_binding(position_cap: int) -> str:
    return (
        f"[{RECOVERY_POSITION_CAP_BINDING_MARKER}] "
        f"MaxOpenPositionsPerSymbolMagic={position_cap}; ค่านี้ผูกจากจำนวนไม้/ระดับสูงสุด "
        "ที่ระบุใน recoveryRules เพื่อไม่ให้ position guard ปิดกั้นระบบแก้ไม้ โดยนับทั้ง "
        "สถานะเปิดและคำสั่งรอของ Symbol+Magic เดียวกัน และต้องเป็น EA input"
    )


def _recovery_position_cap_conflict(
    recovery_text: str,
    money_management_text: str,
) -> tuple[int, int] | None:
    recovery_cap = _requested_recovery_position_cap(recovery_text)
    money_cap = _requested_position_cap(money_management_text)
    if (
        recovery_cap is not None
        and money_cap is not None
        and money_cap < recovery_cap
    ):
        return recovery_cap, money_cap
    return None


def _default_fragments_for_field(
    field: str,
    text: str,
    *,
    supporting_text: str = "",
) -> list[tuple[str, str]]:
    fragments: list[tuple[str, str]] = []
    if field == "exitRules":
        detail = (
            r"(?:\d+(?:\.\d+)?[- ]*(?:(?:x|times?)\s*)?(?:respectively\s*)?"
            r"(?:atr|pips?|points?|%|r\b)|"
            r"\d+(?:\.\d+)?\s*(?::|/|-?to-?)\s*\d+(?:\.\d+)?"
            r".{0,40}(?:reward|risk)|"
            r"(?:reward|risk).{0,40}\d+(?:\.\d+)?\s*"
            r"(?::|/|-?to-?)\s*\d+(?:\.\d+)?|"
            r"(?:atr|pips?|points?)(?:\s+multiples?)?\s*(?:=|:|x|times?)?\s*"
            r"\d+(?:\.\d+)?|"
            r"(?:stop[ _-]?loss\w*|\bsl\b|take[ _-]?profit\w*|\btp\b)\s*"
            r"(?:=|:)\s*\d+(?:\.\d+)?|"
            r"swing|(?:previous|prior|entry).{0,16}(?:high|low|price)|"
            r"(?:indicator|signal).{0,32}(?:value|cross|reverse|opposite)|"
            r"สัญญาณ|ราค(?:าเข้า|าสูงสุด|าต่ำสุด)|\d+(?:\.\d+)?\s*(?:แท่ง|จุด))"
        )
        paired_stop, paired_take = _paired_protection_resolution(text, detail)
        component_text = re.sub(
            r"(?:(?:\bstop[ _-]?loss\b|\bsl\b|\bhard[ -]?stop\b|\binitial\s+stop\b)"
            r"\s*(?:/|&|and|และ)\s*"
            r"(?:\btake[ _-]?profit\b|\btp\b|\bprofit\s+target\b|\breward\s+target\b)|"
            r"(?:\btake[ _-]?profit\b|\btp\b|\bprofit\s+target\b|\breward\s+target\b)"
            r"\s*(?:/|&|and|และ)\s*"
            r"(?:\bstop[ _-]?loss\b|\bsl\b|\bhard[ -]?stop\b|\binitial\s+stop\b))",
            " ",
            text,
            flags=re.IGNORECASE,
        )
        if not paired_stop and not _component_default_present(text, "stop_loss") and not _component_has_resolved_rule(
            component_text,
            _STOP_LOSS_ALIASES,
            detail,
            allow_explicit_disable=True,
        ):
            fragments.append(("stop_loss", IMPLEMENTATION_DEFAULT_STOP_LOSS))
        if not paired_take and not _component_default_present(text, "take_profit") and not _component_has_resolved_rule(
            component_text,
            _TAKE_PROFIT_ALIASES,
            detail,
            allow_explicit_disable=True,
        ):
            fragments.append(("take_profit", IMPLEMENTATION_DEFAULT_TAKE_PROFIT))
        exit_management_components = (
            (
                "trailing_stop",
                _TRAILING_STOP_ALIASES,
                IMPLEMENTATION_DEFAULT_TRAILING_STOP,
            ),
            (
                "break_even",
                _BREAK_EVEN_ALIASES,
                IMPLEMENTATION_DEFAULT_BREAK_EVEN,
            ),
            (
                "partial_close",
                _PARTIAL_CLOSE_ALIASES,
                IMPLEMENTATION_DEFAULT_PARTIAL_CLOSE,
            ),
        )
        for component, aliases, default_text in exit_management_components:
            if not _component_default_present(text, component) and not _component_has_resolved_rule(
                text,
                aliases,
                allow_explicit_disable=True,
            ):
                fragments.append((component, default_text))
    elif field == "moneyManagement":
        source_without_tags = re.sub(r"\[[^\]\r\n]{0,240}\]", " ", text)
        number_word = (
            r"(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|"
            r"หนึ่ง|สอง|สาม|สี่|ห้า|หก|เจ็ด|แปด|เก้า|สิบ)"
        )
        has_risk_sizing = any(
            not _clause_is_unresolved(clause)
            and re.search(
                r"(?:risk\s*percent\s*=\s*\d|riskpercent\s*=\s*\d|"
                rf"(?:risk|position\s+sizing|ความเสี่ยง|เสี่ยง).{{0,36}}{number_word}\s*(?:%|percent|เปอร์เซ็นต์)|"
                rf"{number_word}\s*(?:%|percent|เปอร์เซ็นต์)\s*(?:of\s+)?(?:equity|balance|ทุน)|"
                r"fixed.{0,24}\d+(?:\.\d+)?\s*lots?\b|"
                r"fixed\s+lots?\s*(?:=|:|of)?\s*\d+(?:\.\d+)?|"
                r"(?:ล็อตคงที่|ใช้ล็อต)\s*(?:=|:)?\s*\d+(?:\.\d+)?|"
                r"(?:lot\s+size|ขนาดล็อต)\s*(?:=|:|of)?\s*\d+(?:\.\d+)?|"
                r"(?:ใช้\s*)?\d+(?:\.\d+)?\s*ล็อต(?:คงที่)?(?:\s*ต่อไม้)?|"
                r"\d+(?:\.\d+)?\s*lots?\b|lot\s*=|สูตร.*ล็อต)",
                clause,
                flags=re.IGNORECASE,
            )
            for clause in _operational_clauses(source_without_tags)
        )
        if not _component_default_present(text, "risk_sizing") and not has_risk_sizing:
            fragments.append(("risk_sizing", IMPLEMENTATION_DEFAULT_RISK_SIZING))
        percentage_sizing = bool(re.search(
            rf"(?:risk|ความเสี่ยง|เสี่ยง).{{0,36}}{number_word}\s*(?:%|percent|เปอร์เซ็นต์)|"
            rf"{number_word}\s*(?:%|percent|เปอร์เซ็นต์)\s*(?:of\s+)?(?:equity|balance|ทุน)|"
            r"risk\s*percent|riskpercent",
            text,
            flags=re.IGNORECASE,
        ))
        has_lot_formula = any(
            not _clause_is_unresolved(clause)
            and re.search(
                r"(?:\blot\w*\s*=.{0,100}(?:risk\s*money|equity|balance|ทุน)"
                r".{0,100}/.{0,100}(?:loss\s*per\s*lot|stop\w*distance|"
                r"tick\s*value|tickvalue)|"
                r"(?:risk\s*money|equity|balance|ทุน).{0,100}/.{0,100}"
                r"(?:loss\s*per\s*lot|stop\w*distance|tick\s*value|tickvalue)|"
                r"(?:risk\s*money).{0,100}(?:loss\s*per\s*lot)|"
                r"(?:คำนวณ|สูตร).{0,32}ล็อต.{0,120}(?:ความเสี่ยง|ระยะ\s*sl|"
                r"tick\s*value).{0,120}(?:หาร|/))",
                clause,
                flags=re.IGNORECASE,
            )
            for clause in _operational_clauses(source_without_tags)
        )
        if (
            has_risk_sizing
            and percentage_sizing
            and not has_lot_formula
            and not _component_default_present(text, "risk_sizing")
            and not _component_default_present(text, "lot_calculation")
        ):
            fragments.append(("lot_calculation", IMPLEMENTATION_DEFAULT_LOT_CALCULATION))
        explicit_unlimited = bool(re.search(
            r"(?:unlimited|multiple|no\s+limit).{0,32}(?:positions?|trades?|orders?)|"
            r"(?:positions?|trades?|orders?).{0,24}(?:unlimited|multiple|no\s+limit)|"
            r"ไม่จำกัด.{0,24}(?:สถานะ|ออเดอร์|ออร์เดอร์|ไม้)",
            source_without_tags,
            flags=re.IGNORECASE,
        ))
        if (
            not _component_default_present(text, "position_cap")
            and _requested_position_cap(source_without_tags) is None
            and not explicit_unlimited
        ):
            recovery_position_cap = _requested_recovery_position_cap(
                supporting_text
            )
            fragments.append((
                "position_cap",
                _recovery_position_cap_binding(recovery_position_cap)
                if recovery_position_cap is not None
                else IMPLEMENTATION_DEFAULT_POSITION_CAP,
            ))
    elif field == "orderExecution":
        unresolved_choice = bool(
            re.search(
                r"(?:market.{0,24}(?:or|/)\s*pending|pending.{0,24}(?:or|/)\s*market)",
                text,
                flags=re.IGNORECASE,
            )
            and any(marker in text.casefold() for marker in _DEFERRED_TO_USER_MARKERS)
        )
        positive_order_type = bool(
            _component_enabled_requested(text, _MARKET_ORDER_ALIASES)
            or _component_enabled_requested(text, _PENDING_ORDER_ALIASES)
        )
        if not _component_default_present(text, "order_type") and (
            unresolved_choice or not positive_order_type
        ):
            fragments.append(("order_type", IMPLEMENTATION_DEFAULT_ORDER_EXECUTION))
        timing_text = "\n".join(
            part for part in (supporting_text, text) if part
        )
        if (
            not _component_default_present(text, "closed_bar_execution")
            and not _execution_timing_resolved(timing_text)
        ):
            fragments.append((
                "closed_bar_execution",
                IMPLEMENTATION_DEFAULT_CLOSED_BAR_EXECUTION,
            ))
    elif field == "recoveryRules" and _recovery_default_needed(text):
        fragments.append(("recovery", IMPLEMENTATION_DEFAULT_RECOVERY_RULES))
    return fragments


def apply_strategy_brief_implementation_defaults(value: object) -> object:
    """Add explicit EA defaults to one new Runner result without rewriting history.

    This function is intentionally called by the Runner before the canonical
    brief is projected.  ``normalize_strategy_brief`` itself remains stable so
    previously stored digest-bound rows do not change meaning after an update.
    """

    if not isinstance(value, Mapping):
        return value
    candidate = dict(value)
    for field in ("recoveryRules", "exitRules", "moneyManagement", "orderExecution"):
        source_text = _normalize_text(candidate.get(field))
        if (
            field == "recoveryRules"
            and _recovery_explicit_none(source_text)
            and not re.search(r"\bRecoveryMode\s*=\s*none\b", source_text, flags=re.IGNORECASE)
        ):
            source_text = f"RecoveryMode=none; {source_text}"
            candidate[field] = source_text
        fragments = _default_fragments_for_field(
            field,
            source_text,
            supporting_text=(
                _normalize_text(candidate.get("entryRules"))
                if field == "orderExecution"
                else _normalize_text(candidate.get("recoveryRules"))
                if field == "moneyManagement"
                else ""
            ),
        )
        if not fragments:
            continue
        additions = "\n".join(fragment for _component, fragment in fragments)
        candidate[field] = f"{source_text}\n{additions}" if source_text else additions
    component_fields = {
        "stop_loss": "exitRules",
        "take_profit": "exitRules",
        "trailing_stop": "exitRules",
        "break_even": "exitRules",
        "partial_close": "exitRules",
        "recovery": "recoveryRules",
        "risk_sizing": "moneyManagement",
        "lot_calculation": "moneyManagement",
        "position_cap": "moneyManagement",
        "closed_bar_execution": "orderExecution",
        "order_type": "orderExecution",
    }
    present_components = [
        component
        for component, canonical in _IMPLEMENTATION_COMPONENT_DEFAULTS.items()
        if component != "optimization_inputs"
        if canonical in _normalize_text(candidate.get(component_fields[component]))
    ]
    notes = _normalize_text(candidate.get("additionalNotes"))
    if present_components and IMPLEMENTATION_DEFAULT_OPTIMIZATION_INPUTS not in notes:
        notes_with_metadata = (
            f"{notes}\n{IMPLEMENTATION_DEFAULT_OPTIMIZATION_INPUTS}"
            if notes
            else IMPLEMENTATION_DEFAULT_OPTIMIZATION_INPUTS
        )
        if len(notes_with_metadata) <= _FIELD_LIMITS["additionalNotes"]:
            candidate["additionalNotes"] = notes_with_metadata
            notes = notes_with_metadata
    if present_components and IMPLEMENTATION_DEFAULT_OPTIMIZATION_INPUTS in notes:
        present_components.append("optimization_inputs")
    notes = _normalize_text(candidate.get("additionalNotes"))
    policy_prefix = (
        f"[{IMPLEMENTATION_DEFAULT_MARKER}]"
        f"[POLICY={IMPLEMENTATION_DEFAULT_POLICY_ID}]"
    )
    note_lines = [
        line
        for line in notes.splitlines()
        if not (policy_prefix in line and "DEFAULTED_COMPONENTS=" in line)
    ]
    notes_without_old_receipt = "\n".join(note_lines).strip()
    raw_limitations = candidate.get("limitations")
    limitations = list(raw_limitations) if isinstance(raw_limitations, (list, tuple)) else []
    limitations = [
        item
        for item in limitations
        if not (
            policy_prefix in _normalize_text(item)
            and "DEFAULTED_COMPONENTS=" in _normalize_text(item)
        )
    ]
    if not present_components:
        candidate["additionalNotes"] = notes_without_old_receipt
        candidate["limitations"] = limitations
        return candidate

    component_note = (
        f"{IMPLEMENTATION_DEFAULT_NOTE} DEFAULTED_COMPONENTS="
        + ",".join(present_components)
    )
    combined_notes = (
        f"{notes_without_old_receipt}\n{component_note}"
        if notes_without_old_receipt
        else component_note
    )
    if len(combined_notes) <= _FIELD_LIMITS["additionalNotes"]:
        candidate["additionalNotes"] = combined_notes

    limitation_receipt = (
        f"{IMPLEMENTATION_DEFAULT_LIMITATION} DEFAULTED_COMPONENTS="
        + ",".join(present_components)
    )
    if len(limitations) < 12:
        limitations.append(limitation_receipt)
    candidate["limitations"] = limitations or [limitation_receipt]
    return candidate


def _public_url_independence_key(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip() or any(char.isspace() for char in value):
        return None
    try:
        parsed = urlsplit(value.strip())
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or port not in {None, 80, 443}
    ):
        return None
    host = parsed.hostname.rstrip(".").lower()
    if (
        host in _RESERVED_HOSTS
        or any(host.endswith("." + reserved) for reserved in _RESERVED_HOSTS)
        or host.endswith(_RESERVED_SUFFIXES)
        or host == "localhost"
        or host.endswith((".local", ".internal"))
    ):
        return None
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None:
        return address.compressed if address.is_global else None
    labels = [part for part in host.split(".") if part]
    if labels and labels[0] == "www":
        labels = labels[1:]
    if len(labels) < 2 or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in labels):
        return None
    suffix = ".".join(labels[-2:])
    width = 3 if suffix in _COMMON_SECOND_LEVEL_SUFFIXES and len(labels) >= 3 else 2
    return ".".join(labels[-width:])


def _normalize_checked_at(value: object) -> str | None:
    text = _normalize_text(value)
    if not text or len(text) > 80:
        return None
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00" if text.endswith("Z") else text)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.isoformat()


def normalize_strategy_brief(value: object) -> dict:
    """Return the canonical compact brief or raise ``StrategyBriefValidationError``."""

    issues: list[dict[str, str]] = []
    if not isinstance(value, Mapping):
        raise StrategyBriefValidationError(
            [{"code": "BRIEF_TYPE", "path": "$", "message": "Strategy brief must be an object"}]
        )
    unexpected = sorted(str(key) for key in value if key not in _ROOT_FIELDS)
    missing = sorted(key for key in _ROOT_FIELDS if key not in value)
    if unexpected:
        _issue(issues, "BRIEF_FIELDS_UNEXPECTED", "$", f"Unexpected fields: {unexpected}")
    # Recovery/display/notes and limitations have conservative defaults so an
    # omitted optional behaviour never turns into an invented trading rule.
    defaultable = frozenset({*_DEFAULT_TEXT, "limitations"})
    missing_required = [key for key in missing if key not in defaultable]
    if missing_required:
        _issue(issues, "BRIEF_FIELDS_MISSING", "$", f"Missing fields: {missing_required}")
    if value.get("schemaVersion") != SCHEMA_VERSION:
        _issue(
            issues,
            "BRIEF_SCHEMA_VERSION_INVALID",
            "$.schemaVersion",
            f"schemaVersion must be {SCHEMA_VERSION}",
        )

    normalized: dict[str, object] = {"schemaVersion": SCHEMA_VERSION}
    for field in CONTENT_FIELDS:
        text = _normalize_text(value.get(field))
        if not text and field in _DEFAULT_TEXT:
            text = _DEFAULT_TEXT[field]
        if not text:
            _issue(issues, "BRIEF_TEXT_REQUIRED", f"$.{field}", f"{field} must be non-empty text")
        elif len(text) > _FIELD_LIMITS[field]:
            _issue(
                issues,
                "BRIEF_TEXT_TOO_LONG",
                f"$.{field}",
                f"{field} exceeds {_FIELD_LIMITS[field]} characters",
            )
        normalized[field] = text

    recovery_cap_conflict = _recovery_position_cap_conflict(
        str(normalized.get("recoveryRules") or ""),
        str(normalized.get("moneyManagement") or ""),
    )
    if recovery_cap_conflict is not None:
        recovery_cap, money_cap = recovery_cap_conflict
        _issue(
            issues,
            "BRIEF_RECOVERY_POSITION_CAP_CONFLICT",
            "$.moneyManagement",
            (
                "moneyManagement position cap "
                f"{money_cap} is below the {recovery_cap} total positions required "
                "by recoveryRules"
            ),
        )

    raw_links = value.get("sourceLinks")
    links = list(raw_links) if isinstance(raw_links, (list, tuple)) else []
    if len(links) != 2:
        _issue(issues, "BRIEF_SOURCE_LINK_COUNT", "$.sourceLinks", "sourceLinks must contain exactly two URLs")
    normalized_links: list[str] = []
    independence_keys: list[str] = []
    for index, raw_url in enumerate(links[:2]):
        url = raw_url.strip() if isinstance(raw_url, str) else ""
        key = _public_url_independence_key(url)
        if not key or len(url) > 1000:
            _issue(
                issues,
                "BRIEF_SOURCE_LINK_INVALID",
                f"$.sourceLinks[{index}]",
                "Source link must be a structurally public HTTP(S) URL",
            )
            continue
        normalized_links.append(url)
        independence_keys.append(key)
    if len(set(normalized_links)) != len(normalized_links):
        _issue(issues, "BRIEF_SOURCE_LINK_DUPLICATE", "$.sourceLinks", "Source links must be unique")
    if len(independence_keys) == 2 and len(set(independence_keys)) != 2:
        _issue(
            issues,
            "BRIEF_SOURCE_HOST_NOT_INDEPENDENT",
            "$.sourceLinks",
            "Source links must resolve to two independent public hosts",
        )
    normalized["sourceLinks"] = normalized_links

    checked_at = _normalize_checked_at(value.get("checkedAt"))
    if not checked_at:
        _issue(
            issues,
            "BRIEF_CHECKED_AT_INVALID",
            "$.checkedAt",
            "checkedAt must be an ISO 8601 timestamp with a UTC offset",
        )
    normalized["checkedAt"] = checked_at or ""

    raw_limitations = value.get("limitations")
    limitation_values = (
        list(raw_limitations)
        if isinstance(raw_limitations, (list, tuple))
        else []
    )
    normalized_limitations: list[str] = []
    for index, item in enumerate(limitation_values[:12]):
        text = _normalize_text(item)
        if not text or len(text) > 1200:
            _issue(
                issues,
                "BRIEF_LIMITATION_INVALID",
                f"$.limitations[{index}]",
                "Each limitation must be non-empty text no longer than 1200 characters",
            )
            continue
        if text not in normalized_limitations:
            normalized_limitations.append(text)
    if len(limitation_values) > 12:
        _issue(issues, "BRIEF_LIMITATIONS_TOO_MANY", "$.limitations", "At most 12 limitations are allowed")
    if not normalized_limitations:
        normalized_limitations = [_DEFAULT_LIMITATION]
    normalized["limitations"] = normalized_limitations

    if issues:
        raise StrategyBriefValidationError(issues)
    encoded = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > 48_000:
        raise StrategyBriefValidationError(
            [{"code": "BRIEF_TOO_LARGE", "path": "$", "message": "Canonical strategy brief exceeds 48,000 UTF-8 bytes"}]
        )
    return normalized


def compute_strategy_brief_digest(value: object) -> str:
    """Return a lowercase SHA-256 over canonical compact JSON."""

    normalized = normalize_strategy_brief(value)
    encoded = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def upgrade_linda_holy_grail_brief_for_certified_profile(value: object) -> dict:
    """Derive the v3 Linda profile only from the exact historical brief.

    This helper deliberately does not run from general brief normalization or
    historical Build/Spec verification.  New-source ingestion may call it
    before source identity is assigned, leaving all previously persisted
    evidence immutable and digest-readable.
    """

    normalized = normalize_strategy_brief(value)
    current_digest = compute_strategy_brief_digest(normalized)
    if current_digest == LINDA_HOLY_GRAIL_CERTIFIED_BRIEF_DIGEST:
        if LINDA_HOLY_GRAIL_DIRECTION_RULE not in normalized["entryRules"]:
            raise StrategyBriefValidationError([
                {
                    "code": "LINDA_CERTIFIED_PROFILE_DIGEST_COLLISION",
                    "path": "$.entryRules",
                    "message": "Certified Linda digest has no exact direction rule",
                }
            ])
        return normalized
    if (
        current_digest != LINDA_HOLY_GRAIL_LEGACY_BRIEF_DIGEST
        or normalized.get("systemName")
        != "Linda Bradford Raschke Holy Grail Pullback"
    ):
        return normalized
    upgraded = dict(normalized)
    upgraded["entryRules"] = (
        str(normalized["entryRules"]).rstrip()
        + "\n"
        + LINDA_HOLY_GRAIL_DIRECTION_RULE
    )
    upgraded = normalize_strategy_brief(upgraded)
    if (
        compute_strategy_brief_digest(upgraded)
        != LINDA_HOLY_GRAIL_CERTIFIED_BRIEF_DIGEST
    ):
        raise StrategyBriefValidationError([
            {
                "code": "LINDA_CERTIFIED_PROFILE_DIGEST_MISMATCH",
                "path": "$.entryRules",
                "message": "Derived Linda profile does not match its certified digest",
            }
        ])
    return upgraded


def linda_holy_grail_certified_profile_metadata(value: object) -> dict | None:
    """Return exact v3 profile evidence, never a heuristic classification."""

    try:
        normalized = normalize_strategy_brief(value)
    except StrategyBriefValidationError:
        return None
    if (
        normalized.get("systemName")
        != "Linda Bradford Raschke Holy Grail Pullback"
        or compute_strategy_brief_digest(normalized)
        != LINDA_HOLY_GRAIL_CERTIFIED_BRIEF_DIGEST
        or LINDA_HOLY_GRAIL_DIRECTION_RULE not in normalized["entryRules"]
    ):
        return None
    return {
        "profileVersion": LINDA_HOLY_GRAIL_CERTIFIED_PROFILE_VERSION,
        "derivedFromStrategyBriefDigest": LINDA_HOLY_GRAIL_LEGACY_BRIEF_DIGEST,
        "strategyBriefDigest": LINDA_HOLY_GRAIL_CERTIFIED_BRIEF_DIGEST,
        "classification": IMPLEMENTATION_DEFAULT_MARKER,
        "component": LINDA_HOLY_GRAIL_DIRECTION_COMPONENT,
        "rule": "SMA20_SLOPE",
        "longPredicate": "smaCurrent > smaPrevious",
        "shortPredicate": "smaCurrent < smaPrevious",
    }


def project_strategy_brief_contract(value: object) -> dict:
    """Project one brief into the exact Backend report-field envelope."""

    normalized = normalize_strategy_brief(value)
    return {
        "strategyBrief": normalized,
        "sourceDigest": compute_strategy_brief_digest(normalized),
        "sourceLinks": list(normalized["sourceLinks"]),
        "checkedAt": normalized["checkedAt"],
        "limitations": list(normalized["limitations"]),
    }


def _indicator_lexical_views(
    source_text: object,
) -> tuple[str, tuple[str, ...]] | None:
    """Return executable MQL plus trusted ``#property description`` values.

    Comments and ordinary string literals are blanked so neither can satisfy a
    structural source check.  Description strings remain available separately
    because they are compiled Indicator metadata and carry the immutable brief
    digest binding.
    """

    if not isinstance(source_text, str) or not source_text.strip():
        return None
    output = list(source_text)
    strings: list[tuple[int, str]] = []
    index = 0
    state = "code"
    string_start = -1
    string_value: list[str] = []
    while index < len(source_text):
        current = source_text[index]
        following = source_text[index + 1] if index + 1 < len(source_text) else ""
        if state == "code":
            if current == "/" and following == "/":
                output[index] = output[index + 1] = " "
                index += 2
                state = "line_comment"
                continue
            if current == "/" and following == "*":
                output[index] = output[index + 1] = " "
                index += 2
                state = "block_comment"
                continue
            if current == '"':
                string_start = index
                string_value = []
                output[index] = " "
                index += 1
                state = "string"
                continue
        elif state == "line_comment":
            if current in "\r\n":
                state = "code"
            else:
                output[index] = " "
            index += 1
            continue
        elif state == "block_comment":
            if current == "*" and following == "/":
                output[index] = output[index + 1] = " "
                index += 2
                state = "code"
                continue
            if current not in "\r\n":
                output[index] = " "
            index += 1
            continue
        elif state == "string":
            output[index] = " " if current not in "\r\n" else current
            if current == "\\" and index + 1 < len(source_text):
                string_value.append(source_text[index + 1])
                if source_text[index + 1] not in "\r\n":
                    output[index + 1] = " "
                index += 2
                continue
            if current == '"':
                strings.append((string_start, "".join(string_value)))
                state = "code"
                index += 1
                continue
            if current in "\r\n":
                return None
            string_value.append(current)
            index += 1
            continue
        index += 1
    if state not in {"code", "line_comment"}:
        return None
    code = "".join(output)
    descriptions: list[str] = []
    for start, value in strings:
        line_start = code.rfind("\n", 0, start) + 1
        if re.fullmatch(
            r"\s*#property\s+description\s*",
            code[line_start:start],
            flags=re.IGNORECASE,
        ):
            descriptions.append(value)
    return code, tuple(descriptions)


_MQL_EXECUTION_SAFETY_PATTERNS = (
    (
        "ea_unicode_source_control_forbidden",
        re.compile(r"[\ufeff\u200b-\u200f\u202a-\u202e\u2060-\u206f]"),
    ),
    (
        "ea_external_code_dependency_forbidden",
        re.compile(
            r"(?mi)^\s*#\s*(?:(?:import|include|resource)\b|"
            r"property\s+(?:library|tester_indicator|tester_library|tester_file)\b)"
            r"|\b(?:iCustom|IndicatorCreate)\b"
        ),
    ),
    (
        "ea_network_io_forbidden",
        re.compile(
            r"\b(?:WebRequest|Socket[A-Za-z0-9_]*)\b",
            flags=re.IGNORECASE,
        ),
    ),
    (
        "ea_host_io_forbidden",
        re.compile(
            r"\b(?:File[A-Za-z0-9_]*|Folder[A-Za-z0-9_]*|"
            r"Database[A-Za-z0-9_]*|Resource[A-Za-z0-9_]*|"
            r"WindowScreenShot|ChartScreenShot)\b",
            flags=re.IGNORECASE,
        ),
    ),
    (
        "ea_terminal_control_forbidden",
        re.compile(
            r"\b(?:TerminalClose|ExpertRemove|ChartOpen|ChartClose|"
            r"ChartApplyTemplate|ChartSaveTemplate|ChartSetSymbolPeriod|"
            r"ChartIndicatorAdd|ChartIndicatorDelete|ShellExecute(?:W|A)?|"
            r"ObjectDelete|ObjectsDeleteAll|EventSetTimer|EventSetMillisecondTimer|"
            r"TesterStop|TesterWithdrawal|"
            r"WinExec|CreateProcess(?:W|A)?|ExitProcess|system|"
            r"CustomSymbol[A-Za-z0-9_]*|CustomRates[A-Za-z0-9_]*|"
            r"CustomTicks[A-Za-z0-9_]*)\b",
            flags=re.IGNORECASE,
        ),
    ),
    (
        "ea_persistent_global_mutation_forbidden",
        re.compile(
            r"\b(?:GlobalVariableSet|GlobalVariableSetOnCondition|"
            r"GlobalVariableTemp|GlobalVariableDel|GlobalVariablesDeleteAll|"
            r"GlobalVariablesFlush)\b",
            flags=re.IGNORECASE,
        ),
    ),
    (
        "ea_external_notification_forbidden",
        re.compile(
            r"\b(?:SendMail|SendNotification|SendFTP)\b",
            flags=re.IGNORECASE,
        ),
    ),
    (
        "ea_async_trade_forbidden",
        re.compile(
            r"\bOrderSendAsync\s*\(",
            flags=re.IGNORECASE,
        ),
    ),
    (
        "ea_generic_order_open_forbidden",
        re.compile(
            r"\.\s*OrderOpen\s*\(",
            flags=re.IGNORECASE,
        ),
    ),
    (
        "ea_modal_or_blocking_call_forbidden",
        re.compile(
            r"\b(?:Alert|MessageBox|PlaySound|Sleep)\b",
            flags=re.IGNORECASE,
        ),
    ),
    (
        "ea_unbounded_loop_forbidden",
        re.compile(
            r"\b(?:while|do)\b",
            flags=re.IGNORECASE,
        ),
    ),
    (
        "ea_preprocessor_indirection_forbidden",
        re.compile(
            r"##|\\\r?\n|\r(?!\n)|"
            r"^\s*#\s*(?!(?:define\s+SIGNAL_NONE\s+-1\s*)$)(?:define|undef)\b",
            flags=re.IGNORECASE | re.MULTILINE,
        ),
    ),
    (
        "ea_conditional_compilation_forbidden",
        re.compile(
            r"^\s*#\s*(?:if|ifdef|ifndef|elif|else|endif)\b",
            flags=re.IGNORECASE | re.MULTILINE,
        ),
    ),
    (
        "ea_user_defined_object_lifecycle_forbidden",
        re.compile(
            r"\b(?:class|struct|new|delete)\b",
            flags=re.IGNORECASE,
        ),
    ),
)


def _mql_execution_safety_findings(code: str) -> list[str]:
    """Reject generated programs that can escape the local test-only lane.

    ``code`` must be the lexical view returned by
    :func:`_indicator_lexical_views`; comments and string literals are blanked
    before this denylist runs, so documentation cannot create a false positive
    or conceal an executable call.  Factory-generated programs are deliberately
    standalone: imported/included code cannot be inspected by the immutable
    single-file source manifest and is therefore rejected too.
    """

    if not isinstance(code, str) or not code:
        return ["ea_execution_safety_not_proven"]
    findings = [
        finding
        for finding, pattern in _MQL_EXECUTION_SAFETY_PATTERNS
        if pattern.search(code) is not None
    ]
    if _mql_constant_dead_branch_present(code):
        findings.append("ea_constant_dead_branch_forbidden")
    return list(dict.fromkeys(findings))


def _balanced_close(text: str, opening: int, opener: str, closer: str) -> int | None:
    if opening >= len(text) or text[opening] != opener:
        return None
    depth = 1
    cursor = opening + 1
    while cursor < len(text):
        if text[cursor] == opener:
            depth += 1
        elif text[cursor] == closer:
            depth -= 1
            if depth == 0:
                return cursor
        cursor += 1
    return None


def _mql_constant_dead_branch_present(code: str) -> bool:
    """Reject literal dead/always-taken ``if`` wrappers around safety proof.

    The compact source validator is intentionally conservative: generated EAs
    never need Boolean literals in executable ``if`` predicates.  Rejecting
    them prevents a required closed-bar, position-cap, or margin guard from
    appearing in text while being compiled into an unreachable branch.
    """

    for match in re.finditer(r"\bif\s*\(", code, flags=re.IGNORECASE):
        opening = code.find("(", match.start(), match.end())
        closing = _balanced_close(code, opening, "(", ")")
        if closing is None or closing - opening > 4096:
            return True
        condition = code[opening + 1 : closing]
        if re.search(r"\b(?:true|false)\b", condition, flags=re.IGNORECASE):
            return True
        literal_expression = re.sub(
            r"\bSIGNAL_NONE\b",
            "-1",
            condition,
            flags=re.IGNORECASE,
        )
        if re.fullmatch(
            r"[\s0-9.eE+\-*/%<>=!&|()]+",
            literal_expression,
        ):
            return True
        if re.search(
            r"(?<![A-Za-z_])(?:\d+(?:\.\d+)?|-\d+(?:\.\d+)?)\s*"
            r"(?:==|!=|<=|>=|<|>)\s*"
            r"(?:\d+(?:\.\d+)?|-\d+(?:\.\d+)?)(?![A-Za-z_])|"
            r"!+\s*\d+(?:\.\d+)?\b",
            literal_expression,
        ):
            return True
        compact = re.sub(r"\s+", "", condition)
        while compact.startswith("(") and compact.endswith(")"):
            nested_close = _balanced_close(compact, 0, "(", ")")
            if nested_close != len(compact) - 1:
                break
            compact = compact[1:-1]
        if re.fullmatch(r"[01](?:\.0+)?", compact):
            return True
        if re.search(
            r"(?:^|&&|\|\|)\(*0(?:\.0+)?\)*&&|"
            r"(?:^|&&|\|\|)\(*1(?:\.0+)?\)*\|\|",
            compact,
        ):
            return True
    return False


def _indicator_function_bodies(code: str, function_name: str) -> list[str] | None:
    depth = 0
    for character in code:
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth < 0:
                return None
    if depth:
        return None
    bodies: list[str] = []
    declaration = re.compile(
        r"\b(?:bool|int|void|double)\s+([A-Za-z_]\w*)\s*"
        r"\([^;{}]{0,1600}\)\s*\{",
        flags=re.IGNORECASE | re.DOTALL,
    )
    for match in declaration.finditer(code):
        if match.group(1).lower() != function_name.lower():
            continue
        opening = match.end() - 1
        closing = _balanced_close(code, opening, "{", "}")
        if closing is None:
            return None
        bodies.append(code[opening + 1 : closing])
    return bodies


def _indicator_if_regions(code: str) -> list[tuple[str, str]] | None:
    regions: list[tuple[str, str]] = []
    for match in re.finditer(r"\bif\s*\(", code, flags=re.IGNORECASE):
        opening = code.find("(", match.start(), match.end())
        closing = _balanced_close(code, opening, "(", ")")
        if closing is None:
            return None
        cursor = closing + 1
        while cursor < len(code) and code[cursor].isspace():
            cursor += 1
        if cursor >= len(code):
            return None
        if code[cursor] == "{":
            body_close = _balanced_close(code, cursor, "{", "}")
            if body_close is None:
                return None
            body = code[cursor + 1 : body_close]
        else:
            statement_close = code.find(";", cursor, min(len(code), cursor + 3000))
            if statement_close < 0:
                return None
            body = code[cursor : statement_close + 1]
        regions.append((code[opening + 1 : closing], body))
    return regions


def analyze_compact_indicator_source(
    source_text: object,
    *,
    strategy_brief_digest: object,
    strategy_spec_digest: object,
    source_digest: object,
    target_platform: object,
) -> dict:
    """Return fail-closed structural evidence for a v3 Custom Indicator.

    A prose brief cannot be proven semantically equivalent by regex.  This
    contract therefore makes the narrower truthful claim: the source is bound
    to the immutable brief digest, exposes visible Indicator buffers, writes at
    least two closed-bar conditional signals from ``OnCalculate``, and contains
    no trading API.  The subsequent read-only source review still evaluates the
    prose-to-code semantics.
    """

    brief_digest = str(strategy_brief_digest or "").strip().lower()
    spec_digest = str(strategy_spec_digest or "").strip().lower()
    actual_source_digest = str(source_digest or "").strip().lower()
    platform = str(target_platform or "").strip().lower()
    findings: list[str] = []
    checks = {
        "lexicallyUnambiguous": False,
        "executionSafety": False,
        "strategyBriefDigestBound": False,
        "indicatorDeclaration": False,
        "onCalculate": False,
        "indicatorBufferBinding": False,
        "visiblePlot": False,
        "conditionalSignalOutputs": False,
        "closedBarSignals": False,
        "tradingFunctionsAbsent": False,
    }
    if (
        re.fullmatch(r"[0-9a-f]{64}", brief_digest) is None
        or re.fullmatch(r"[0-9a-f]{64}", spec_digest) is None
        or re.fullmatch(r"[0-9a-f]{64}", actual_source_digest) is None
        or platform not in {"mt4", "mt5"}
    ):
        findings.append("indicator_compact_binding_invalid")

    lexical = _indicator_lexical_views(source_text)
    if lexical is None:
        findings.append("indicator_source_lexically_ambiguous")
        code = ""
        descriptions: tuple[str, ...] = ()
    else:
        checks["lexicallyUnambiguous"] = True
        code, descriptions = lexical

    execution_safety_findings = _mql_execution_safety_findings(code)
    checks["executionSafety"] = not execution_safety_findings
    findings.extend(execution_safety_findings)

    expected_marker = f"EA_STRATEGY_BRIEF_SHA256:{brief_digest}".lower()
    checks["strategyBriefDigestBound"] = any(
        expected_marker in " ".join(description.split()).lower()
        for description in descriptions
    )
    if not checks["strategyBriefDigestBound"]:
        findings.append("indicator_strategy_brief_digest_binding_missing")

    window_matches = re.findall(
        r"(?mi)^\s*#property\s+indicator_(?:chart_window|separate_window)\b",
        code,
    )
    buffer_count_matches = re.findall(
        r"(?mi)^\s*#property\s+indicator_buffers\s+(\d+)\b",
        code,
    )
    buffer_count = (
        int(buffer_count_matches[0])
        if len(buffer_count_matches) == 1 and buffer_count_matches[0].isdigit()
        else 0
    )
    checks["indicatorDeclaration"] = bool(
        len(window_matches) == 1 and 1 <= buffer_count <= 64
    )
    if not checks["indicatorDeclaration"]:
        findings.append("indicator_property_or_buffer_count_missing")

    on_calculate_bodies = _indicator_function_bodies(code, "OnCalculate")
    checks["onCalculate"] = bool(
        isinstance(on_calculate_bodies, list) and len(on_calculate_bodies) == 1
    )
    if not checks["onCalculate"]:
        findings.append("indicator_oncalculate_missing")
    on_calculate = on_calculate_bodies[0] if checks["onCalculate"] else ""

    declared_arrays = {
        match.group(1)
        for match in re.finditer(
            r"\bdouble\s+([A-Za-z_]\w*)\s*\[\s*\]\s*;",
            code,
            flags=re.IGNORECASE,
        )
    }
    buffer_bindings = [
        (int(match.group(1)), match.group(2))
        for match in re.finditer(
            r"\bSetIndexBuffer\s*\(\s*(\d+)\s*,\s*([A-Za-z_]\w*)\b",
            code,
            flags=re.IGNORECASE,
        )
    ]
    bound_names = {name for _index, name in buffer_bindings}
    bound_indices = {index for index, _name in buffer_bindings}
    checks["indicatorBufferBinding"] = bool(
        buffer_bindings
        and len(bound_indices) == len(buffer_bindings)
        and all(name in declared_arrays for name in bound_names)
        and all(0 <= index < buffer_count for index in bound_indices)
    )
    if not checks["indicatorBufferBinding"]:
        findings.append("indicator_buffer_binding_missing")

    visible_property = re.search(
        r"(?mi)^\s*#property\s+indicator_type\d+\s+DRAW_(?!NONE\b)[A-Z0-9_]+\b",
        code,
    )
    visible_runtime = re.search(
        r"\b(?:SetIndexStyle\s*\(\s*\d+\s*,\s*DRAW_(?!NONE\b)[A-Z0-9_]+|"
        r"PlotIndexSetInteger\s*\(\s*\d+\s*,\s*PLOT_DRAW_TYPE\s*,\s*DRAW_(?!NONE\b)[A-Z0-9_]+)",
        code,
        flags=re.IGNORECASE,
    )
    checks["visiblePlot"] = bool(visible_property or visible_runtime)
    if not checks["visiblePlot"]:
        findings.append("indicator_visible_plot_missing")

    assignment_pattern = re.compile(
        r"\b([A-Za-z_]\w*)\s*\[\s*([^\]]{1,120})\s*\]\s*=\s*([^;]{1,600});",
        flags=re.IGNORECASE,
    )

    def meaningful_assignments(fragment: str) -> list[tuple[str, str, str]]:
        rows: list[tuple[str, str, str]] = []
        for match in assignment_pattern.finditer(fragment):
            name, index_expr, value_expr = match.groups()
            normalized_value = re.sub(r"\s+", "", value_expr).lower()
            if name not in bound_names or normalized_value in {
                "empty_value", "null", "0", "0.0", "0.00",
            }:
                continue
            rows.append((name, index_expr.strip(), value_expr.strip()))
        return rows

    regions = _indicator_if_regions(on_calculate) if on_calculate else []
    if regions is None:
        findings.append("indicator_source_structure_unbalanced")
        regions = []
    signal_regions = [
        (condition, body, meaningful_assignments(body))
        for condition, body in regions
        if meaningful_assignments(body)
    ]
    signal_branch_count = len(signal_regions)
    checks["conditionalSignalOutputs"] = signal_branch_count >= 2
    if not checks["conditionalSignalOutputs"]:
        findings.append("indicator_entry_exit_signal_branches_missing")

    literal_zero_output = any(
        re.fullmatch(r"\(?\s*0\s*\)?", index_expr)
        for _name, index_expr, _value in meaningful_assignments(on_calculate)
    )
    forming_bar_read = bool(
        re.search(
            r"\b(?:open|high|low|close|time|tick_volume|volume|spread)\s*\[\s*0\s*\]",
            on_calculate,
            flags=re.IGNORECASE,
        )
    )
    historical_signal_reference = bool(
        re.search(
            r"(?:\[\s*[1-9]\d*\s*\]|\(\s*[1-9]\d*\s*\))",
            on_calculate,
        )
        or re.search(
            r"\bfor\s*\([^;]{0,400};\s*([A-Za-z_]\w*)\s*(?:>=\s*1|>\s*0)\s*;",
            on_calculate,
            flags=re.IGNORECASE,
        )
    )
    rates_guard = bool(
        re.search(
            r"\bif\s*\(\s*rates_total\s*<\s*[2-9]\d*\s*\)\s*(?:\{\s*)?return\b",
            on_calculate,
            flags=re.IGNORECASE,
        )
    )
    checks["closedBarSignals"] = bool(
        checks["conditionalSignalOutputs"]
        and historical_signal_reference
        and rates_guard
        and not literal_zero_output
        and not forming_bar_read
    )
    if not checks["closedBarSignals"]:
        findings.append("indicator_closed_bar_signal_guard_missing")

    forbidden = re.compile(
        r"\b(?:OnTick|start|OrderSend|OrderSendAsync|OrderClose|OrderCloseBy|"
        r"OrderModify|OrderDelete|OrderSelect|OrdersTotal|PositionOpen|"
        r"PositionClose|PositionModify|PositionSelect|PositionsTotal|"
        r"HistoryOrder\w*|HistoryDeal\w*)\s*\(|\b(?:CTrade|MqlTradeRequest)\b|"
        r"\.\s*(?:Buy|Sell|BuyLimit|SellLimit|BuyStop|SellStop|PositionOpen|"
        r"PositionClose|PositionModify|OrderOpen|OrderDelete)\s*\(",
        flags=re.IGNORECASE,
    )
    checks["tradingFunctionsAbsent"] = forbidden.search(code) is None
    if not checks["tradingFunctionsAbsent"]:
        findings.append("indicator_trading_function_forbidden")

    findings = list(dict.fromkeys(findings))
    return {
        "checks": checks,
        "findings": findings,
        "boundBufferCount": len(bound_names),
        "signalBranchCount": signal_branch_count,
        "complete": not findings and all(checks.values()),
    }


def build_compact_indicator_source_manifest(
    source_text: object,
    *,
    strategy_brief_digest: object,
    strategy_spec_digest: object,
    source_digest: object,
    target_platform: object,
) -> dict:
    """Build a digest-bound, non-semantic v3 Indicator evidence manifest."""

    brief_digest = str(strategy_brief_digest or "").strip().lower()
    spec_digest = str(strategy_spec_digest or "").strip().lower()
    actual_source_digest = str(source_digest or "").strip().lower()
    platform = str(target_platform or "").strip().lower()
    analysis = analyze_compact_indicator_source(
        source_text,
        strategy_brief_digest=brief_digest,
        strategy_spec_digest=spec_digest,
        source_digest=actual_source_digest,
        target_platform=platform,
    )
    result = {
        "schemaVersion": INDICATOR_SOURCE_MANIFEST_SCHEMA_VERSION,
        "coverageMode": "compact_brief_digest_bound_structural_signal_review",
        "artifactKind": "custom_indicator",
        "targetPlatform": platform,
        "strategyBriefDigest": brief_digest,
        "strategySpecDigest": spec_digest,
        "sourceDigest": actual_source_digest,
        "checks": analysis["checks"],
        "boundBufferCount": analysis["boundBufferCount"],
        "signalBranchCount": analysis["signalBranchCount"],
        "findings": analysis["findings"],
        "complete": analysis["complete"],
    }
    encoded = json.dumps(
        result,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    result["manifestDigest"] = hashlib.sha256(encoded).hexdigest()
    return result


def _compact_ea_brief_content(value: object) -> dict[str, str] | None:
    if not isinstance(value, Mapping):
        return None
    keys = set(value)
    compact_keys = {"schemaVersion", *CONTENT_FIELDS}
    if keys != compact_keys and keys != set(_ROOT_FIELDS):
        return None
    if value.get("schemaVersion") != SCHEMA_VERSION:
        return None
    content = {field: _normalize_text(value.get(field)) for field in CONTENT_FIELDS}
    if any(not text or len(text) > _FIELD_LIMITS[field] for field, text in content.items()):
        return None
    if _recovery_position_cap_conflict(
        content["recoveryRules"],
        content["moneyManagement"],
    ) is not None:
        return None
    return content


def _compact_ea_function_map(code: str) -> dict[str, list[str]] | None:
    depth = 0
    for character in code:
        depth += 1 if character == "{" else -1 if character == "}" else 0
        if depth < 0:
            return None
    if depth:
        return None
    functions: dict[str, list[str]] = {}
    declaration = re.compile(
        r"\b(?:void|int|bool|double|long|ulong|datetime|string|uint|float)\s+"
        r"([A-Za-z_]\w*)\s*\([^;{}]{0,2000}\)\s*\{",
        flags=re.IGNORECASE | re.DOTALL,
    )
    for match in declaration.finditer(code):
        closing = _balanced_close(code, match.end() - 1, "{", "}")
        if closing is None:
            return None
        functions.setdefault(match.group(1).lower(), []).append(
            code[match.end() : closing]
        )
    return functions


def _compact_ea_reachable_call_graph_acyclic(
    functions: dict[str, list[str]],
    roots: tuple[str, ...] = ("oninit", "ondeinit", "ontick"),
) -> bool:
    """Fail closed when a lifecycle-reachable local call cycle can hang MT4.

    MQL permits direct and mutual recursion.  A generated EA does not need it,
    and allowing it would let Source validation succeed before MetaEditor or
    Strategy Tester becomes stuck.  Only calls to functions declared in this
    single-file artifact participate in this bounded graph.
    """

    if not isinstance(functions, dict) or len(functions) > 128:
        return False
    local_names = set(functions)
    adjacency: dict[str, set[str]] = {}
    edge_count = 0
    for name, bodies in functions.items():
        called = {
            candidate.casefold()
            for body in bodies
            for candidate in re.findall(r"\b([A-Za-z_]\w*)\s*\(", body)
            if candidate.casefold() in local_names
        }
        edge_count += len(called)
        if edge_count > 1024:
            return False
        adjacency[name] = called

    # 0 = unseen, 1 = active DFS path, 2 = fully checked.
    colors: dict[str, int] = {}

    def visit(name: str) -> bool:
        color = colors.get(name, 0)
        if color == 1:
            return False
        if color == 2:
            return True
        colors[name] = 1
        if len(colors) > 128:
            return False
        for called in adjacency.get(name, set()):
            if not visit(called):
                return False
        colors[name] = 2
        return True

    return all(
        visit(str(root).casefold())
        for root in roots
        if str(root).casefold() in local_names
    )


def _compact_ea_for_loops_provably_bounded(code: str) -> bool:
    """Accept only simple monotonic counter ``for`` loops with literal bounds.

    Compact generated EAs need loops mainly to walk MT4 order indexes.  A
    literal comparator plus a matching ++/-- direction gives this safety gate
    a finite, inspectable subset; dynamic/compound conditions are rejected
    before any visible terminal action.
    """

    maximum_iterations = 10_000
    maximum_total_literal_iterations = 100_000
    total_literal_iterations = 0
    loops = list(re.finditer(r"\bfor\s*\(", code, flags=re.IGNORECASE))
    if len(loops) > 128:
        return False
    for loop in loops:
        opening = code.find("(", loop.start(), loop.end())
        closing = _balanced_close(code, opening, "(", ")")
        if closing is None or closing - opening > 4096:
            return False
        pieces = code[opening + 1 : closing].split(";")
        if len(pieces) != 3:
            return False
        initializer, condition, update = (piece.strip() for piece in pieces)
        init_match = re.fullmatch(
            r"int\s+(?P<counter>[A-Za-z_]\w*)\s*=\s*.+",
            initializer,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not init_match:
            return False
        counter = init_match.group("counter")
        initializer_expression = initializer[init_match.start("counter") + len(counter):]
        initializer_expression = initializer_expression.split("=", 1)[1].strip()
        condition_match = re.fullmatch(
            rf"\(*\s*{re.escape(counter)}\s*(?P<operator><=|<|>=|>)\s*"
            r"(?P<bound>-?\d+)\s*\)*",
            condition,
            flags=re.IGNORECASE,
        )
        if not condition_match:
            return False
        increment_match = re.fullmatch(
            rf"(?:\+\+\s*{re.escape(counter)}|{re.escape(counter)}\s*\+\+|"
            rf"{re.escape(counter)}\s*\+=\s*(?P<increment>[1-9]\d*))",
            update,
            flags=re.IGNORECASE,
        )
        decrement_match = re.fullmatch(
            rf"(?:--\s*{re.escape(counter)}|{re.escape(counter)}\s*--|"
            rf"{re.escape(counter)}\s*-=\s*(?P<decrement>[1-9]\d*))",
            update,
            flags=re.IGNORECASE,
        )
        increment = increment_match is not None
        decrement = decrement_match is not None
        operator = condition_match.group("operator")
        if not ((operator in {"<", "<="} and increment) or (
            operator in {">", ">="} and decrement
        )):
            return False
        bound = int(condition_match.group("bound"))
        literal_initializer = re.fullmatch(
            r"(?P<value>-?\d+)",
            initializer_expression,
        )
        if literal_initializer:
            initial = int(literal_initializer.group("value"))
            step_match = increment_match or decrement_match
            step_text = (
                (step_match.groupdict().get("increment") or "")
                if increment
                else (step_match.groupdict().get("decrement") or "")
            )
            step = int(step_text or "1")
            integer_minimum = -2_147_483_648
            integer_maximum = 2_147_483_647
            if not (
                integer_minimum <= initial <= integer_maximum
                and integer_minimum <= bound <= integer_maximum
                and 1 <= step <= maximum_iterations
            ):
                return False
            if operator == "<":
                iterations = max(0, (bound - initial + step - 1) // step)
            elif operator == "<=":
                iterations = max(0, (bound - initial) // step + 1)
            elif operator == ">":
                iterations = max(0, (initial - bound + step - 1) // step)
            else:
                iterations = max(0, (initial - bound) // step + 1)
            next_after_last = (
                initial + iterations * step
                if increment
                else initial - iterations * step
            )
            if (
                iterations < 1
                or iterations > maximum_iterations
                or not integer_minimum <= next_after_last <= integer_maximum
            ):
                return False
            total_literal_iterations += iterations
            if total_literal_iterations > maximum_total_literal_iterations:
                return False
        else:
            normalized_initializer = re.sub(r"\s+", "", initializer_expression)
            if (
                normalized_initializer.casefold()
                not in {"orderstotal()-1", "positionstotal()-1"}
                or not decrement
                or str(update).replace(" ", "").casefold()
                not in {f"{counter.casefold()}--", f"--{counter.casefold()}"}
                or not (
                    (operator == ">=" and bound == 0)
                    or (operator == ">" and bound == -1)
                )
            ):
                return False
        cursor = closing + 1
        while cursor < len(code) and code[cursor].isspace():
            cursor += 1
        if cursor >= len(code):
            return False
        # Generated EA loops must always be braced.  Otherwise a visually
        # top-level fail-closed guard can actually be the optional body of a
        # zero/finite iteration loop and falsely satisfy semantic evidence.
        if code[cursor] != "{":
            return False
        body_close = _balanced_close(code, cursor, "{", "}")
        if body_close is None or body_close - cursor > 128 * 1024:
            return False
        body = code[cursor + 1 : body_close]
        if re.search(r"\bfor\s*\(", body, flags=re.IGNORECASE):
            return False
        if re.search(
            rf"(?:\+\+|--)\s*\(*\s*\b{re.escape(counter)}\b\s*\)*|"
            rf"\(*\s*\b{re.escape(counter)}\b\s*\)*\s*"
            rf"(?:\+\+|--|(?:(?:<<|>>|[+\-*/%&|^]))?=(?!=))",
            body,
            flags=re.IGNORECASE,
        ):
            return False
        counter_call_allowlist = {
            "if",
            "switch",
            "orderselect",
            "positiongetticket",
            "ordergetticket",
            "historyordergetticket",
            "historydealgetticket",
        }
        for call in re.finditer(r"\b([A-Za-z_]\w*)\s*\(", body):
            call_opening = body.find("(", call.start(), call.end())
            call_closing = _balanced_close(body, call_opening, "(", ")")
            if call_closing is None:
                return False
            arguments = body[call_opening + 1 : call_closing]
            if (
                re.search(rf"\b{re.escape(counter)}\b", arguments, re.IGNORECASE)
                and call.group(1).casefold() not in counter_call_allowlist
            ):
                return False
    return True


def _compact_ea_global_code(code: str) -> str | None:
    """Blank ordinary function definitions, leaving only global-scope code."""

    output = list(code)
    declaration = re.compile(
        r"\b(?:void|int|bool|double|long|ulong|datetime|string|uint|float)\s+"
        r"[A-Za-z_]\w*\s*\([^;{}]{0,2000}\)\s*\{",
        flags=re.IGNORECASE | re.DOTALL,
    )
    for match in declaration.finditer(code):
        closing = _balanced_close(code, match.end() - 1, "{", "}")
        if closing is None:
            return None
        for index in range(match.start(), closing + 1):
            if output[index] not in "\r\n":
                output[index] = " "
    return "".join(output)


def _compact_ea_function_parameters(code: str) -> dict[str, tuple[str, ...]]:
    parameters: dict[str, tuple[str, ...]] = {}
    declaration = re.compile(
        r"\b(?:void|int|bool|double|long|ulong|datetime|string|uint|float)\s+"
        r"(?P<name>[A-Za-z_]\w*)\s*\((?P<parameters>[^;{}]{0,2000})\)\s*\{",
        flags=re.IGNORECASE | re.DOTALL,
    )
    for match in declaration.finditer(code):
        raw_parameters = _split_mql_arguments(match.group("parameters")) or []
        names: list[str] = []
        for raw_parameter in raw_parameters:
            without_default = raw_parameter.split("=", 1)[0]
            identifiers = re.findall(r"[A-Za-z_]\w*", without_default)
            if identifiers:
                names.append(identifiers[-1])
        parameters[match.group("name").casefold()] = tuple(names)
    return parameters


def _compact_ea_one_level_trade_bindings(
    code: str,
    functions: dict[str, list[str]],
    reachable: str,
) -> str:
    """Prepend fail-closed formal-to-actual aliases for one unambiguous trade wrapper."""

    parameter_map = _compact_ea_function_parameters(code)
    aliases: list[str] = []
    for function_name, bodies in functions.items():
        if function_name == "ontick" or not any(
            _mql_trade_call_records(body) for body in bodies
        ):
            continue
        parameters = parameter_map.get(function_name, ())
        if not parameters:
            continue
        wrapper_calls = _mql_named_call_records(reachable, (function_name,))
        # Multiple call sites require path-sensitive argument binding; leave
        # them unresolved so the structural gate fails closed.
        if len(wrapper_calls) != 1:
            continue
        arguments = [str(item) for item in wrapper_calls[0].get("arguments", [])]
        if len(arguments) != len(parameters):
            continue
        aliases.extend(
            f"{formal} = {actual};"
            for formal, actual in zip(parameters, arguments)
        )
    return "\n".join((*aliases, reachable)) if aliases else reachable


def _compact_ea_reachable_code(functions: dict[str, list[str]]) -> str:
    return _compact_ea_reachable_code_from(functions, ("ontick",))


def _compact_ea_reachable_code_from(
    functions: dict[str, list[str]],
    roots: tuple[str, ...],
) -> str:
    """Return each local function body reachable from bounded lifecycle roots once."""

    pending = [str(root or "").casefold() for root in roots if str(root or "").strip()]
    visited: set[str] = set()
    bodies: list[str] = []
    while pending and len(visited) < 128:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        for body in functions.get(name, []):
            bodies.append(body)
            for called in re.findall(r"\b([A-Za-z_]\w*)\s*\(", body):
                normalized = called.lower()
                if normalized in functions and normalized not in visited:
                    pending.append(normalized)
    return "\n".join(bodies)


_MQL_TRADE_SIDE_EFFECT_CALL_PATTERN = re.compile(
    r"\b(?P<direct>OrderSendAsync|OrderSend|OrderCloseBy|OrderClose|OrderModify|"
    r"OrderDelete|PositionOpen|PositionCloseBy|PositionClosePartial|"
    r"PositionClose|PositionModify)\s*\(|"
    r"\.\s*(?P<method>BuyStop|SellStop|BuyLimit|SellLimit|Buy|Sell|"
    r"PositionOpen|PositionCloseBy|PositionClosePartial|PositionClose|"
    r"PositionModify|OrderOpen|OrderModify|OrderDelete)\s*\(",
    flags=re.IGNORECASE,
)


def _mql_trade_side_effect_call_names(code: str) -> list[str]:
    """List executable trade-side-effect API names in lexical source order."""

    if not isinstance(code, str) or not code:
        return []
    names: list[str] = []
    for match in _MQL_TRADE_SIDE_EFFECT_CALL_PATTERN.finditer(code):
        names.append(str(match.group("direct") or match.group("method") or "").casefold())
        if len(names) >= 256:
            break
    return names


def _split_mql_arguments(value: str) -> list[str] | None:
    result: list[str] = []
    start = 0
    stack: list[str] = []
    closing_for = {"(": ")", "[": "]", "{": "}"}
    for index, character in enumerate(value):
        if character in closing_for:
            stack.append(closing_for[character])
        elif character in ")]}" :
            if not stack or stack.pop() != character:
                return None
        elif character == "," and not stack:
            result.append(value[start:index].strip())
            start = index + 1
        if len(stack) > 32:
            return None
    if stack:
        return None
    result.append(value[start:].strip())
    # Lexical preprocessing blanks string contents, so a valid string argument
    # appears empty here. Empty arguments are harmless for the numeric/type
    # positions inspected below; the compiler remains the authority on syntax.
    if len(result) > 20:
        return None
    return result


def _mql_fail_closed_return_conditions(
    code: str,
    *,
    allow_void_return: bool,
    top_level_only: bool = False,
) -> list[str]:
    """Extract bounded MQL if-conditions that immediately fail closed.

    The caller still decides whether the Boolean condition implies the required
    failure.  Parsing balanced parentheses here avoids treating nested function
    calls in margin guards as the end of the `if` condition.
    """

    normalized = " ".join(str(code or "").split())
    conditions: list[str] = []
    unbraced_controlled_starts = _mql_unbraced_controlled_statement_starts(
        normalized
    )
    for match in list(re.finditer(r"\bif\s*\(", normalized, re.IGNORECASE))[:256]:
        if top_level_only:
            if _mql_brace_depth_at(normalized, match.start()) != 0:
                continue
            if match.start() in unbraced_controlled_starts:
                continue
        opening = normalized.find("(", match.start(), match.end())
        closing = _balanced_close(normalized, opening, "(", ")")
        if closing is None or closing - opening > 2048:
            continue
        tail = normalized[closing + 1 : closing + 257]
        if allow_void_return:
            return_pattern = (
                r"^\s*(?:\{\s*)?return"
                r"(?:\s*\(?\s*0(?:\.0+)?\s*\)?)?\s*;"
            )
        else:
            return_pattern = (
                r"^\s*(?:\{\s*)?return\s*\(?\s*0(?:\.0+)?\s*\)?\s*;"
            )
        if re.search(return_pattern, tail, flags=re.IGNORECASE):
            conditions.append(normalized[opening + 1 : closing])
    return conditions


def _mql_unbraced_controlled_statement_starts(code: str) -> set[int]:
    """Locate statements whose execution depends on an unbraced control.

    Brace depth alone reports the nested statement in ``if(flag) if(...)`` as
    top-level.  Safety evidence must not come from that optional statement, so
    callers can exclude its exact lexical start while still permitting normal
    compact single-statement MQL elsewhere.
    """

    starts: set[int] = set()
    for match in list(re.finditer(
        r"\b(?:if|for|while|switch)\s*\(",
        str(code or ""),
        flags=re.IGNORECASE,
    ))[:512]:
        opening = code.find("(", match.start(), match.end())
        closing = _balanced_close(code, opening, "(", ")")
        if closing is None:
            continue
        cursor = closing + 1
        while cursor < len(code) and code[cursor].isspace():
            cursor += 1
        if cursor < len(code) and code[cursor] != "{":
            starts.add(cursor)
    return starts


def _mql_brace_depth_at(code: str, position: int) -> int:
    """Return lexical block depth before ``position`` or -1 when unbalanced."""

    depth = 0
    for character in code[: max(0, position)]:
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth < 0:
                return -1
    return depth


_MT4_TESTER_INPUT_TYPES = frozenset({"bool", "int", "double"})
_MT4_TESTER_INPUT_MAX_COUNT = 64


def _mql4_tester_input_contract_valid(code: str) -> bool:
    """Prove every MT4 tester input can be reset from one exact source line.

    The visible adapter deliberately supports only bounded scalar literals.  A
    generated EA that uses an enum, string, expression, grouped declaration,
    multiline declaration, duplicate name, ``sinput``, or function-local
    declaration must therefore fail the immutable static gate before any
    MetaEditor or Strategy Tester UI can be opened.
    """

    if not isinstance(code, str) or not code:
        return False
    tokens = list(re.finditer(r"(?i)\b(?:input|extern|sinput)\b", code))
    if len(tokens) > _MT4_TESTER_INPUT_MAX_COUNT:
        return False
    declarations: list[tuple[str, str, str]] = []
    seen_lines: set[int] = set()
    for token in tokens:
        line_start = code.rfind("\n", 0, token.start()) + 1
        line_end = code.find("\n", token.end())
        if line_end < 0:
            line_end = len(code)
        if line_start in seen_lines or _mql_brace_depth_at(code, line_start) != 0:
            return False
        seen_lines.add(line_start)
        declaration = re.fullmatch(
            r"[ \t]*(input|extern)[ \t]+([A-Za-z_][A-Za-z0-9_]*)"
            r"[ \t]+([A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*"
            r"([^;\r\n]+?)[ \t]*;[ \t]*",
            code[line_start:line_end].rstrip("\r"),
            flags=re.IGNORECASE,
        )
        if declaration is None:
            return False
        input_type = declaration.group(2).lower()
        if input_type not in _MT4_TESTER_INPUT_TYPES:
            return False
        declarations.append(
            (input_type, declaration.group(3), declaration.group(4).strip())
        )
    names = [name.casefold() for _kind, name, _literal in declarations]
    if len(names) != len(set(names)):
        return False
    for input_type, _name, literal in declarations:
        if input_type == "bool":
            if literal.casefold() not in {"true", "false", "0", "1"}:
                return False
        elif input_type == "int":
            if re.fullmatch(r"[+-]?\d+", literal) is None:
                return False
            value = int(literal)
            if not -2_147_483_648 <= value <= 2_147_483_647:
                return False
        else:
            if re.fullmatch(
                r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",
                literal,
            ) is None:
                return False
            if not math.isfinite(float(literal)):
                return False
    return True


def _mql_trade_call_records(code: str) -> list[dict[str, object]]:
    """Return bounded argument records for reachable MQL trade-entry calls."""

    patterns = (
        re.compile(r"\b(?P<name>OrderSend|PositionOpen)\s*\(", re.IGNORECASE),
        re.compile(
            r"\.\s*(?P<name>Buy|Sell|BuyStop|SellStop|BuyLimit|SellLimit)\s*\(",
            re.IGNORECASE,
        ),
    )
    records: list[dict[str, object]] = []
    for pattern in patterns:
        for match in pattern.finditer(code):
            opening = code.find("(", match.start(), match.end())
            closing = _balanced_close(code, opening, "(", ")")
            if closing is None:
                continue
            arguments = _split_mql_arguments(code[opening + 1 : closing])
            if arguments is None:
                continue
            records.append({
                "name": match.group("name").lower(),
                "arguments": arguments,
                "start": match.start(),
                "end": closing + 1,
            })
    records.sort(key=lambda item: (int(item["start"]), int(item["end"])))
    return records[:128]


def _mql_named_call_records(
    code: str,
    names: tuple[str, ...],
) -> list[dict[str, object]]:
    """Return bounded argument records for named reachable MQL calls."""

    name_pattern = "|".join(re.escape(name) for name in names)
    pattern = re.compile(
        rf"(?:\b|\.\s*)(?P<name>{name_pattern})\s*\(",
        flags=re.IGNORECASE,
    )
    records: list[dict[str, object]] = []
    for match in pattern.finditer(code):
        opening = code.find("(", match.start(), match.end())
        closing = _balanced_close(code, opening, "(", ")")
        if closing is None:
            continue
        arguments = _split_mql_arguments(code[opening + 1 : closing])
        if arguments is None:
            continue
        records.append({
            "name": match.group("name").lower(),
            "arguments": arguments,
            "start": match.start(),
            "end": closing + 1,
        })
    records.sort(key=lambda item: (int(item["start"]), int(item["end"])))
    return records[:128]


def _mql_reachable_display_evidence(
    source_text: object,
    lexical_code: str,
    reachable_code: str,
) -> str:
    """Return raw arguments for display calls proven reachable from OnTick.

    The lexical view has comments and string contents replaced byte-for-byte
    with whitespace.  We use it to find balanced calls and to match each call
    against the reachable call graph, then project the same offsets back onto
    the raw source.  This lets display labels count while comments and dead
    helper functions cannot satisfy the Strategy Brief by themselves.
    """

    if not isinstance(source_text, str) or not lexical_code or not reachable_code:
        return ""
    names = (
        "Comment",
        "ObjectCreate",
        "ObjectSetText",
        "ObjectSetString",
        "ChartSetString",
    )
    name_pattern = "|".join(re.escape(name) for name in names)
    pattern = re.compile(
        rf"(?:\b|\.\s*)(?P<name>{name_pattern})\s*\(",
        flags=re.IGNORECASE,
    )

    def call_spans(value: str) -> list[tuple[int, int, str]]:
        rows: list[tuple[int, int, str]] = []
        for match in list(pattern.finditer(value))[:128]:
            opening = value.find("(", match.start(), match.end())
            closing = _balanced_close(value, opening, "(", ")")
            if closing is None or closing - match.start() > 8192:
                continue
            snippet = re.sub(
                r"\s+",
                " ",
                value[match.start() : closing + 1],
            ).strip().casefold()
            rows.append((match.start(), closing + 1, snippet))
        return rows

    reachable_signatures = {
        signature for _start, _end, signature in call_spans(reachable_code)
    }
    raw_rows = [
        source_text[start:end]
        for start, end, signature in call_spans(lexical_code)
        if signature in reachable_signatures and 0 <= start < end <= len(source_text)
    ]
    return "\n".join(raw_rows)


def _compact_display_requirement_findings(
    display_requirements: object,
    system_name: object,
    display_evidence: str,
) -> list[str]:
    """Check only explicitly named display items against reachable UI calls."""

    requirements = " ".join(str(display_requirements or "").split())
    evidence = " ".join(str(display_evidence or "").split())
    if not requirements or not evidence:
        return ["ea_display_behavior_missing"]
    checks = (
        ("signal_state", r"\bsignal(?:\s*(?:state|status))?\b|สถานะสัญญาณ|สัญญาณ", r"\bsignal\w*\b|\bstate\w*\b|สถานะ"),
        ("balance", r"\bbalance\b|ยอดคงเหลือ", r"\b(?:account)?balance\b"),
        ("equity", r"\bequity\b|อิควิตี|เอควิตี", r"\b(?:account)?equity\b"),
        ("spread", r"\bspread\b|สเปรด", r"\bspread\w*\b|\bmode_spread\b|\bsymbol_spread\b"),
        ("symbol", r"\bsymbol\b|สัญลักษณ์", r"\bsymbol\w*\b|\b_symbol\b"),
        ("timeframe", r"\btime\s*frame\b|\btimeframe\b|กรอบเวลา|ไทม์เฟรม", r"\btime\s*frame\b|\btimeframe\b|\bperiod\s*\("),
        ("market_direction", r"\bmarket\s*direction\b|ทิศทางตลาด", r"\bmarket\w*(?:direction|trend|up|down)\w*\b|\b(?:direction|trend)\w*\b"),
        ("breakout_level", r"\bbreakout\s*level\b|ระดับ(?:การ)?เบรกเอาต์|จุดเบรกเอาต์", r"\bbreakout\w*\b"),
        ("stop_loss_percent", r"\bstop\s*loss\s*percent\b|\bstoplosspercent\b|\bsl\s*percent\b|เปอร์เซ็นต์(?:ของ)?\s*(?:stop\s*loss|sl)", r"\b(?:inp)?stoplosspercent\b|\bslpercent\b"),
        ("risk_percent", r"\brisk\s*percent\b|\briskpercent\b|เปอร์เซ็นต์ความเสี่ยง", r"\briskpercent\b|\brisk_percent\b"),
        ("recovery_mode", r"\brecovery\s*mode\b|\brecoverymode\b|โหมด(?:การ)?แก้ไม้", r"\brecovery\w*\b"),
    )
    missing = [
        name
        for name, requirement_pattern, evidence_pattern in checks
        if re.search(requirement_pattern, requirements, flags=re.IGNORECASE)
        and re.search(evidence_pattern, evidence, flags=re.IGNORECASE) is None
    ]
    if re.search(r"\bsystem\s*name\b|ชื่อระบบ|ชื่อกลยุทธ์", requirements, re.IGNORECASE):
        requested_name = " ".join(str(system_name or "").split()).casefold()
        normalized_evidence = evidence.casefold()
        name_tokens = [
            token
            for token in re.findall(r"[^\W_]+", requested_name, flags=re.UNICODE)
            if len(token) >= 3
            and token not in {"system", "strategy", "trading", "ระบบ", "กลยุทธ์"}
        ]
        has_named_variable = re.search(
            r"\bsystem\s*name\b|\bsystemname\b|\bstrategy\s*name\b",
            evidence,
            re.IGNORECASE,
        ) is not None
        has_name_token = any(token in normalized_evidence for token in name_tokens)
        if not requested_name or not (has_named_variable or has_name_token):
            missing.append("system_name")
    return [f"ea_display_required_field_missing:{name}" for name in missing]


def _compact_ea_trade_invocation_multiplicity_safe(
    functions: dict[str, list[str]],
) -> bool:
    """Prove that an opening helper cannot submit more orders than inspected.

    Reachable-code projection intentionally includes each helper body once.  A
    helper called twice (or from a loop) would otherwise look like one opening
    call to the cap validator while executing it multiple times at runtime.
    """

    if not isinstance(functions, dict) or len(functions.get("ontick", [])) != 1:
        return False
    local_names = set(functions)
    call_records: dict[str, list[tuple[str, int]]] = {}
    adjacency: dict[str, set[str]] = {}
    direct_trade_functions: set[str] = set()
    loop_ranges: dict[str, list[tuple[int, int]]] = {}
    for function_name, bodies in functions.items():
        body = "\n".join(bodies)
        records = [
            (match.group(1).casefold(), match.start())
            for match in re.finditer(r"\b([A-Za-z_]\w*)\s*\(", body)
            if match.group(1).casefold() in local_names
        ]
        call_records[function_name] = records
        adjacency[function_name] = {name for name, _position in records}
        if _mql_trade_call_records(body):
            direct_trade_functions.add(function_name)
        ranges: list[tuple[int, int]] = []
        for loop in re.finditer(r"\bfor\s*\(", body, flags=re.IGNORECASE):
            opening = body.find("(", loop.start(), loop.end())
            closing = _balanced_close(body, opening, "(", ")")
            if closing is None:
                return False
            cursor = closing + 1
            while cursor < len(body) and body[cursor].isspace():
                cursor += 1
            if cursor >= len(body) or body[cursor] != "{":
                return False
            body_close = _balanced_close(body, cursor, "{", "}")
            if body_close is None:
                return False
            ranges.append((cursor, body_close))
        loop_ranges[function_name] = ranges

    reachable: set[str] = set()
    pending = ["ontick"]
    while pending:
        function_name = pending.pop()
        if function_name in reachable:
            continue
        reachable.add(function_name)
        if len(reachable) > 128:
            return False
        pending.extend(adjacency.get(function_name, set()) - reachable)

    trade_reaching = direct_trade_functions.intersection(reachable)
    changed = True
    while changed:
        changed = False
        for function_name in reachable - trade_reaching:
            if adjacency.get(function_name, set()).intersection(trade_reaching):
                trade_reaching.add(function_name)
                changed = True

    def inside_loop(function_name: str, position: int) -> bool:
        return any(
            start < position < end
            for start, end in loop_ranges.get(function_name, [])
        )

    incoming_counts = {name: 0 for name in trade_reaching if name != "ontick"}
    for function_name in reachable:
        body = "\n".join(functions.get(function_name, []))
        for trade_record in _mql_trade_call_records(body):
            if inside_loop(function_name, int(trade_record.get("start") or 0)):
                return False
        for called, position in call_records.get(function_name, []):
            if called not in incoming_counts:
                continue
            incoming_counts[called] += 1
            if inside_loop(function_name, position):
                return False
    return all(count == 1 for count in incoming_counts.values())


def _mql_expression_is_nonzero(value: str) -> bool:
    normalized = " ".join(value.split())
    return bool(
        normalized
        and not re.fullmatch(
            r"(?:0+(?:\.0+)?|NULL|EMPTY_VALUE|WRONG_VALUE)",
            normalized,
            flags=re.IGNORECASE,
        )
    )


def _mql_expression_has_nonzero_value(value: str, code: str) -> bool:
    """Reject literal/assigned zero protection values while allowing calculations."""

    normalized = " ".join(value.split())
    if not _mql_expression_is_nonzero(normalized):
        return False
    if not re.fullmatch(r"[A-Za-z_]\w*", normalized):
        return True
    assignments = re.findall(
        rf"\b{re.escape(normalized)}\s*=(?!=)\s*([^;\r\n]+)",
        code,
        flags=re.IGNORECASE,
    )
    if not assignments:
        return True
    return _mql_expression_is_nonzero(assignments[-1])


def _mql_expression_dependency_text(value: str, code: str) -> str:
    """Expand bounded pre-call variable assignments used by one expression."""

    pending = [" ".join(value.split())]
    fragments: list[str] = []
    visited: set[str] = set()
    while pending and len(fragments) < 128:
        expression = pending.pop()
        if not expression or expression in visited:
            continue
        visited.add(expression)
        fragments.append(expression)
        for identifier in re.findall(r"\b[A-Za-z_]\w*\b", expression):
            if identifier.casefold() in {
                "true", "false", "null", "point", "ask", "bid", "symbol",
                "period", "mathmax", "mathmin", "mathabs", "normalizeDouble".casefold(),
            }:
                continue
            assignment_matches = list(re.finditer(
                rf"\b{re.escape(identifier)}\s*=(?!=)\s*([^;\r\n]+)",
                code,
                flags=re.IGNORECASE,
            ))
            if assignment_matches:
                assignments: list[tuple[str, bool]] = []
                for match in assignment_matches:
                    line_start = max(
                        code.rfind("\n", 0, match.start()),
                        code.rfind(";", 0, match.start()),
                    ) + 1
                    prefix = code[line_start:match.start()]
                    assignments.append((
                        match.group(1),
                        bool(re.search(r"\b(?:if|else)\b", prefix, re.IGNORECASE)),
                    ))
                last_unconditional = max(
                    (
                        index
                        for index, (_assigned, conditional) in enumerate(assignments)
                        if not conditional
                    ),
                    default=0,
                )
                pending.extend(
                    assigned
                    for assigned, _conditional in assignments[last_unconditional:]
                )
        if sum(len(item) for item in fragments) > 12000:
            break
    return "\n".join(fragments)


def _mql_dependency_with_input_bindings(dependency: str, code: str) -> str:
    fragments = [dependency]
    for identifier in set(re.findall(r"\b[A-Za-z_]\w*\b", dependency)):
        declaration = re.search(
            rf"\b(?:input|extern|const)\s+(?:double|float|int|long|uint|ulong)\s+"
            rf"{re.escape(identifier)}\s*=\s*([^;\r\n]+)",
            code,
            flags=re.IGNORECASE,
        )
        if declaration:
            fragments.append(f"{identifier}={declaration.group(1)}")
    return "\n".join(fragments)


def _protection_component_scope(
    clause: str,
    label: str,
    other_label: str,
) -> str | None:
    """Return only one component's clause slice so SL and TP cannot cross-feed."""

    component_match = re.search(label, clause, flags=re.IGNORECASE)
    if component_match is None:
        return None
    other_matches = list(re.finditer(other_label, clause, flags=re.IGNORECASE))
    if any(match.start() < component_match.start() for match in other_matches):
        return None
    next_other = next(
        (match for match in other_matches if match.start() > component_match.start()),
        None,
    )
    end = next_other.start() if next_other is not None else len(clause)
    return clause[component_match.start():end]


def _requested_protection_value(text: str, component: str) -> tuple[float, str] | None:
    if component == "stop":
        label = r"(?:stop[ _-]?loss\w*|\bsl\b|hard[ -]?stop|initial\s+stop|ตัดขาดทุน|หยุดขาดทุน)"
        trailing_label = r"(?:stop|sl|ตัดขาดทุน|หยุดขาดทุน)"
        other_label = r"(?:take[ _-]?profit\w*|\btp\b|profit\s+target|reward\s+target|เป้ากำไร|เป้าหมายกำไร)"
    else:
        label = r"(?:take[ _-]?profit\w*|\btp\b|profit\s+target|reward\s+target|เป้ากำไร|เป้าหมายกำไร)"
        trailing_label = r"(?:target|take[ _-]?profit|tp|เป้ากำไร|เป้าหมายกำไร)"
        other_label = r"(?:stop[ _-]?loss\w*|\bsl\b|hard[ -]?stop|initial\s+stop|ตัดขาดทุน|หยุดขาดทุน)"
        for clause in _operational_clauses(text):
            if not re.search(label, clause, flags=re.IGNORECASE):
                continue
            reward_input = re.search(
                r"\bRewardRiskRatio\s*=\s*(\d+(?:\.\d+)?)\b",
                clause,
                flags=re.IGNORECASE,
            )
            if reward_input and float(reward_input.group(1)) > 0:
                return float(reward_input.group(1)), "r"
        for clause in _operational_clauses(text):
            scoped = _protection_component_scope(
                clause,
                label,
                other_label,
            )
            if scoped is None:
                continue
            descriptor = re.search(
                r"(?P<reward_first>reward\s*(?:/|-?to-?)\s*risk)|"
                r"(?P<risk_first>risk\s*(?:/|-?to-?)\s*reward)",
                scoped,
                flags=re.IGNORECASE,
            )
            pair = re.search(
                r"(?P<first>\d+(?:\.\d+)?)\s*(?::|/|-?to-?)\s*"
                r"(?P<second>\d+(?:\.\d+)?)",
                scoped,
                flags=re.IGNORECASE,
            )
            if descriptor and pair:
                first = float(pair.group("first"))
                second = float(pair.group("second"))
                if first > 0 and second > 0:
                    reward_multiple = (
                        first / second
                        if descriptor.group("reward_first")
                        else second / first
                    )
                    if reward_multiple > 0:
                        return reward_multiple, "r"
    unit = r"(atr|pips?|points?|r)\b"
    patterns = (
        rf"{label}.{{0,48}}?(\d+(?:\.\d+)?)\s*(?:\*|x|times?)?\s*{unit}",
        rf"{label}.{{0,48}}?{unit}\s*(?:\*|x|times?)?\s*(\d+(?:\.\d+)?)",
        rf"(\d+(?:\.\d+)?)[ -]*{unit}.{{0,24}}{trailing_label}",
        rf"{unit}\s*(?:\*|x|times?)?\s*(\d+(?:\.\d+)?).{{0,24}}{trailing_label}",
    )
    for clause in _operational_clauses(text):
        scoped = _protection_component_scope(
            clause,
            label,
            other_label,
        )
        if scoped is None:
            continue
        for index, pattern in enumerate(patterns):
            match = re.search(pattern, scoped, flags=re.IGNORECASE)
            if match:
                if index in {0, 2}:
                    value, matched_unit = match.group(1), match.group(2)
                else:
                    matched_unit, value = match.group(1), match.group(2)
                return float(value), matched_unit.casefold().rstrip("s")
        assignment = re.search(
            rf"{label}\s*(?:=|:)\s*(\d+(?:\.\d+)?)",
            scoped,
            flags=re.IGNORECASE,
        )
        if assignment:
            inferred_unit = "point" if re.search(r"points?", assignment.group(0), re.IGNORECASE) else "raw"
            return float(assignment.group(1)), inferred_unit
    return None


def _requested_stop_percentage_range(text: str) -> tuple[float, float] | None:
    """Read a source-backed price-percent stop without borrowing TP prose."""

    stop_label = (
        r"(?:stop[ _-]?loss\w*|\bsl\b|hard[ -]?stop|initial\s+stop|"
        r"ตัดขาดทุน|หยุดขาดทุน)"
    )
    take_label = (
        r"(?:take[ _-]?profit\w*|\btp\b|profit\s+target|reward\s+target|"
        r"เป้ากำไร|เป้าหมายกำไร)"
    )
    for clause in _operational_clauses(text):
        scoped = _protection_component_scope(
            clause,
            stop_label,
            take_label,
        )
        if scoped is None:
            continue
        range_match = re.search(
            r"(?P<low>\d+(?:\.\d+)?)\s*%\s*(?:-|–|—|to|ถึง)\s*"
            r"(?P<high>\d+(?:\.\d+)?)\s*%",
            scoped,
            flags=re.IGNORECASE,
        )
        if range_match:
            low = float(range_match.group("low"))
            high = float(range_match.group("high"))
            if 0 < low <= high < 100:
                return low, high
        scalar_match = re.search(
            r"(?P<value>\d+(?:\.\d+)?)\s*%",
            scoped,
            flags=re.IGNORECASE,
        )
        if scalar_match:
            value = float(scalar_match.group("value"))
            if 0 < value < 100:
                return value, value
    return None


def _requested_atr_period_shift(
    text: str,
    component: str,
) -> tuple[int, int] | None:
    label = (
        r"(?:stop[ _-]?loss\w*|\bsl\b|hard[ -]?stop|initial\s+stop|ตัดขาดทุน|หยุดขาดทุน)"
        if component == "stop"
        else r"(?:take[ _-]?profit\w*|\btp\b|profit\s+target|reward\s+target|เป้ากำไร|เป้าหมายกำไร)"
    )
    for clause in _operational_clauses(text):
        if not re.search(label, clause, flags=re.IGNORECASE):
            continue
        match = re.search(
            r"\bATR\s*\(\s*(\d+)\s*\)\s*\[\s*(\d+)\s*\]",
            clause,
            flags=re.IGNORECASE,
        )
        if match:
            return int(match.group(1)), int(match.group(2))
    return None


def _atr_period_shift_dependency_valid(
    requirement: tuple[int, int] | None,
    dependency: str,
    code: str,
) -> bool:
    if requirement is None:
        return True
    period, shift = requirement
    context = _mql_dependency_with_input_bindings(dependency, code)
    for match in re.finditer(
        r"\biATR\s*\([^,;\r\n]+,[^,;\r\n]+,\s*"
        r"(?P<period>\d+|[A-Za-z_]\w*)\s*,\s*"
        r"(?P<shift>\d+|[A-Za-z_]\w*)\s*\)",
        context,
        flags=re.IGNORECASE,
    ):
        period_token = match.group("period")
        shift_token = match.group("shift")
        period_valid = (
            period_token.isdigit() and int(period_token) == period
        ) or _numeric_input_matches(code, period_token, float(period))
        shift_valid = (
            shift_token.isdigit() and int(shift_token) == shift
        ) or _numeric_input_matches(code, shift_token, float(shift))
        if period_valid and shift_valid:
            return True
    return False


def _requested_fixed_lot(text: str) -> float | None:
    match = re.search(
        r"(?:fixed\s+(?:lot|volume)|fixedlot|ล็อตคงที่|ใช้ล็อต)"
        r"\s*(?:size\s*)?(?:=|:|of)?\s*(\d+(?:\.\d+)?)|"
        r"\b(?:lot\s*size|lots?|volume)\s*(?:=|:)\s*(\d+(?:\.\d+)?)|"
        r"\b(?:trade|open|use)\s+(\d+(?:\.\d+)?)\s+lots?\b|"
        r"\bfixed\s+position\s+size\s*(?:=|:|is|of)?\s*"
        r"(\d+(?:\.\d+)?)\s*lots?\b|"
        r"\bposition\s+size\s+(?:is|=|:)\s*(\d+(?:\.\d+)?)\s*lots?\b|"
        r"\bposition\s+sizing\s+(?:is|=|:)\s*(\d+(?:\.\d+)?)\s*lots?"
        r"(?:\s+fixed\b)?|"
        r"\b(\d+(?:\.\d+)?)\s*lots?\s+(?:fixed|per\s+(?:trade|order|signal))\b|"
        r"ขนาดล็อต\s*(?:คงที่\s*)?(?:เท่ากับ|=|:)?\s*(\d+(?:\.\d+)?)"
        r"(?:\s*ล็อต)?(?:\s*ต่อไม้)?|"
        r"(?:ใช้\s*)?(\d+(?:\.\d+)?)\s*ล็อตคงที่(?:\s*ต่อไม้)?",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return float(next(value for value in match.groups() if value is not None))


def _requested_risk_percentage(text: str) -> float | None:
    match = re.search(
        r"\bRiskPercent\s*=\s*(\d+(?:\.\d+)?)\s*(?:%|percent|เปอร์เซ็นต์)?|"
        r"(?:risk(?:\s*percent)?|ความเสี่ยง|เสี่ยง)\s*"
        r"(?:=|:|per\s+trade\s+is)?"
        r"\s*(\d+(?:\.\d+)?)\s*(?:%|percent|เปอร์เซ็นต์)|"
        r"(\d+(?:\.\d+)?)\s*(?:%|percent|เปอร์เซ็นต์)"
        r"\s*(?:of\s+)?(?:equity|balance|ทุน)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return float(next(value for value in match.groups() if value is not None))


def _requested_management_value(
    text: str,
    component: str,
) -> tuple[float, str] | None:
    label = {
        "trailing": r"(?:trail(?:ing)?(?:[ _-]?stop)?|ระยะเลื่อน)",
        "break_even": r"(?:break[ _-]?even|breakeven|คุ้มทุน)",
    }[component]
    for clause in _operational_clauses(text):
        if not re.search(label, clause, flags=re.IGNORECASE):
            continue
        match = re.search(
            rf"{label}.{{0,64}}?(\d+(?:\.\d+)?)\s*(atr|pips?|points?|r)\b|"
            rf"(\d+(?:\.\d+)?)\s*(atr|pips?|points?|r)\b.{{0,48}}{label}",
            clause,
            flags=re.IGNORECASE,
        )
        if match:
            value = match.group(1) or match.group(3)
            unit = match.group(2) or match.group(4)
            return float(value), unit.casefold().rstrip("s")
    return None


def _numeric_input_matches(code: str, name: str, expected: float) -> bool:
    match = re.search(
        rf"\b(?:input|extern)\s+(?:double|float|int|long|uint|ulong)\s+"
        rf"{re.escape(name)}\s*=\s*(-?\d+(?:\.\d+)?)",
        code,
        flags=re.IGNORECASE,
    )
    if not match or abs(float(match.group(1)) - expected) > 1e-9:
        return False
    declarations = list(re.finditer(
        rf"\b(?:(?P<storage>input|extern)\s+)?"
        rf"(?:double|float|int|long|uint|ulong)\s+{re.escape(name)}\b",
        code,
        flags=re.IGNORECASE,
    ))
    # A same-named local/formal declaration disconnects the runtime expression
    # from the audited EA input even when the correct input remains in the file.
    return bool(
        declarations
        and all(item.group("storage") for item in declarations)
    )


def _fixed_lot_dependency_matches(
    dependency: str,
    code: str,
    expected: float,
) -> bool:
    root = dependency.splitlines()[0].strip() if dependency else ""
    if re.fullmatch(r"-?\d+(?:\.\d+)?", root):
        return abs(float(root) - expected) <= 1e-9
    wrapper = re.fullmatch(
        r"(?:NormalizeDouble\s*\(\s*)?(?P<name>[A-Za-z_]\w*)"
        r"(?:\s*,\s*\d+\s*\))?",
        root,
        flags=re.IGNORECASE,
    )
    if not wrapper:
        return False
    name = wrapper.group("name")
    binding = re.search(
        rf"\b(?:input|extern|const)?\s*(?:double|float)\s+{re.escape(name)}"
        rf"\s*=\s*(-?\d+(?:\.\d+)?)\s*;",
        code,
        flags=re.IGNORECASE,
    )
    return bool(binding and abs(float(binding.group(1)) - expected) <= 1e-9)


def _mql_dependency_has_signed_distance(
    dependency: str,
    *,
    side: str,
    component: str,
) -> bool:
    """Recognize bounded price +/- distance or prior-extreme protection."""

    compact = " ".join(dependency.split())
    structured = "\n".join(
        " ".join(line.split()) for line in dependency.splitlines()
    )
    base = r"(?:entry\w*|open\w*price|ask|bid|price)"
    distance = (
        r"(?:protected\w*|stop\w*distance|take\w*distance|target\w*distance|"
        r"(?:sl|tp)\w*|\w*atr\w*|\w*pips?\w*|\w*points?\w*|"
        r"\d+(?:\.\d+)?\s*\*\s*Point)"
    )
    expects_minus = (side == "buy" and component == "stop") or (
        side == "sell" and component == "take"
    )
    operator = r"-" if expects_minus else r"\+"
    relation_pattern = rf"\b{base}\b\s*{operator}\s*{distance}"
    ternaries = list(re.finditer(
        r"(?P<condition>[^?;]{0,120}\b[A-Za-z_]\w*\s*==\s*"
        r"(?:OP_|ORDER_TYPE_)(?P<kind>BUY|SELL)(?:_?(?:STOP|LIMIT))?\b[^?;]{0,40})"
        r"\?(?P<yes>[^:;]{0,500}):(?P<no>[^;\r\n]{0,500})",
        structured,
        flags=re.IGNORECASE,
    ))
    relevant_ternaries = [
        ternary
        for ternary in ternaries
        if re.search(
            rf"\b{base}\b\s*(?:\+|-)\s*{distance}",
            f"{ternary.group('yes')} {ternary.group('no')}",
            flags=re.IGNORECASE,
        )
    ]
    if relevant_ternaries:
        for ternary in relevant_ternaries:
            condition_side = ternary.group("kind").casefold()
            branch = ternary.group("yes") if condition_side == side else ternary.group("no")
            if re.search(relation_pattern, branch, flags=re.IGNORECASE):
                return True
        return False
    if re.search(relation_pattern, compact, re.IGNORECASE):
        return True
    if component == "stop":
        extreme = r"\bLow\s*\[\s*[1-9]\d*\s*\]" if side == "buy" else r"\bHigh\s*\[\s*[1-9]\d*\s*\]"
    else:
        extreme = r"\bHigh\s*\[\s*[1-9]\d*\s*\]" if side == "buy" else r"\bLow\s*\[\s*[1-9]\d*\s*\]"
    return bool(re.search(extreme, compact, flags=re.IGNORECASE))


def _stateful_new_bar_guard(
    code: str,
    first_trade_start: int,
    persistent_states: tuple[str, ...] = (),
) -> bool:
    pretrade = code if first_trade_start < 0 else code[:first_trade_start]
    unbraced_controlled_starts = _mql_unbraced_controlled_statement_starts(
        pretrade
    )
    state_names = list(persistent_states)
    state_names.extend(
        state_match.group("state")
        for state_match in re.finditer(
            r"\bstatic\s+datetime\s+(?P<state>[A-Za-z_]\w*)"
            r"\s*(?:=\s*[^;]+)?;",
            pretrade,
            flags=re.IGNORECASE,
        )
    )
    for state in dict.fromkeys(state_names):
        time_sources = [
            r"Time\s*\[\s*0\s*\]",
            r"iTime\s*\([^,;\r\n]+,[^,;\r\n]+,\s*0\s*\)",
        ]
        current_names = {""}
        for time_source in time_sources:
            current_names.update(
                match.group("current")
                for match in re.finditer(
                    rf"\b(?:datetime\s+)?(?P<current>[A-Za-z_]\w*)\s*=\s*{time_source}",
                    pretrade,
                    flags=re.IGNORECASE,
                )
            )
        for current in current_names:
            current_pattern = (
                rf"(?:{re.escape(current)}|Time\s*\[\s*0\s*\]|"
                rf"iTime\s*\([^,;\r\n]+,[^,;\r\n]+,\s*0\s*\))"
                if current
                else r"(?:Time\s*\[\s*0\s*\]|iTime\s*\([^,;\r\n]+,[^,;\r\n]+,\s*0\s*\))"
            )
            compares = list(re.finditer(
                rf"\bif\s*\((?:(?!\bif\s*\()[^;{{}}\r\n]){{0,240}}"
                rf"(?:\b{re.escape(state)}\b"
                rf"(?:(?!\bif\s*\()[^;{{}}\r\n]){{0,80}}(?:==|>=)\s*{current_pattern}|"
                rf"{current_pattern}(?:(?!\bif\s*\()[^;{{}}\r\n]){{0,80}}"
                rf"(?:==|<=)\s*\b{re.escape(state)}\b)"
                rf"(?:(?!\bif\s*\()[^;{{}}\r\n]){{0,120}}\)\s*"
                rf"(?:\{{\s*)?return\b",
                pretrade,
                flags=re.IGNORECASE,
            ))
            updates = list(re.finditer(
                rf"\b{re.escape(state)}\s*=\s*{current_pattern}\s*;",
                pretrade,
                flags=re.IGNORECASE,
            ))
            for compare in compares:
                if (
                    _mql_brace_depth_at(pretrade, compare.start()) != 0
                    or compare.start() in unbraced_controlled_starts
                    or "&&" in compare.group(0)
                ):
                    continue
                if any(
                    compare.start() < update.start()
                    and _mql_brace_depth_at(pretrade, update.start()) == 0
                    and update.start() not in unbraced_controlled_starts
                    for update in updates
                ):
                    return True
    return False


def _pending_price_requirement(
    text: str,
    mode: str,
) -> tuple[str, str, float | None, str | None] | None:
    labels = {
        "buy_stop": r"buy[ -]?stop",
        "sell_stop": r"sell[ -]?stop",
        "buy_limit": r"buy[ -]?limit",
        "sell_limit": r"sell[ -]?limit",
    }
    label = labels[mode]
    generic_label = (
        r"(?:stop[ _-]?entry|(?:pending\s+)?stop\s+order)"
        if mode.endswith("_stop")
        else r"(?:limit[ _-]?entry|(?:pending\s+)?limit\s+order)"
    )
    sentence = next(
        (
            clause
            for clause in _operational_clauses(text)
            if re.search(
                rf"\b(?:{label}|{generic_label})\b",
                clause,
                flags=re.IGNORECASE,
            )
        ),
        "",
    )
    if not sentence and mode in {"buy_stop", "sell_stop"}:
        paired_sentence = next(
            (
                clause
                for clause in _operational_clauses(text)
                if re.search(
                    r"\bbuy\s*(?:/|and|&)\s*sell\s+stops?\b|"
                    r"\bsell\s*(?:/|and|&)\s*buy\s+stops?\b",
                    clause,
                    flags=re.IGNORECASE,
                )
                and re.search(
                    r"\b(?:beyond|outside)\b.{0,48}\b(?:prior|previous|signal)?\s*"
                    r"high\s*/\s*low\b",
                    clause,
                    flags=re.IGNORECASE,
                )
            ),
            "",
        )
        if paired_sentence:
            offset_match = re.search(
                r"(\d+(?:\.\d+)?)\s*(pips?|points?|atr)\b",
                paired_sentence,
                flags=re.IGNORECASE,
            )
            offset = float(offset_match.group(1)) if offset_match else None
            unit = (
                "pip" if offset_match and offset_match.group(2).casefold().startswith("pip")
                else "atr" if offset_match and offset_match.group(2).casefold() == "atr"
                else "point" if offset_match else None
            )
            return (
                "high" if mode == "buy_stop" else "low",
                "+" if mode == "buy_stop" else "-",
                offset,
                unit,
            )
    if not sentence:
        return None
    expected = {
        "buy_stop": (("high", "ask"), "+"),
        "sell_stop": (("low", "bid"), "-"),
        "buy_limit": (("low", "ask"), "-"),
        "sell_limit": (("high", "bid"), "+"),
    }[mode]
    references, operator = expected
    direction_word = "above" if operator == "+" else "below"
    reference = next((candidate for candidate in references if re.search(
        rf"\b{direction_word}\b.{{0,48}}\b(?:prior|previous|signal(?:[ -]?bar)?)?\s*{candidate}\b|"
        rf"\b(?:prior|previous|signal(?:[ -]?bar)?)?\s*{candidate}\b.{{0,48}}\b{direction_word}\b",
        sentence,
        flags=re.IGNORECASE,
    )), "")
    if not reference:
        return None
    offset_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(pips?|points?|atr)\b",
        sentence,
        flags=re.IGNORECASE,
    )
    offset = float(offset_match.group(1)) if offset_match else None
    unit = (
        "pip" if offset_match and offset_match.group(2).casefold().startswith("pip")
        else "atr" if offset_match and offset_match.group(2).casefold() == "atr"
        else "point" if offset_match else None
    )
    return reference, operator, offset, unit


def _pending_price_semantics_valid(
    order_text: str,
    call_evidence: list[dict[str, object]],
    code: str,
) -> bool:
    for mode in ("buy_stop", "sell_stop", "buy_limit", "sell_limit"):
        requirement = _pending_price_requirement(order_text, mode)
        if requirement is None:
            continue
        reference, operator, offset, offset_unit = requirement
        candidates = [
            str(item.get("price") or "")
            for item in call_evidence
            if mode in set(item.get("modes") or ())
        ]
        if not candidates:
            return False
        for dependency in candidates:
            context = _mql_dependency_with_input_bindings(dependency, code)
            compact = " ".join(context.split())
            ternary = re.search(
                r"\b[A-Za-z_]\w*\s*==\s*(?:OP_|ORDER_TYPE_)"
                r"(?P<kind>BUY|SELL)(?P<subtype>_?STOP|_?LIMIT)?\b[^?;]{0,40}"
                r"\?(?P<yes>[^:;]{0,500}):(?P<no>[^;\r\n]{0,500})",
                compact,
                flags=re.IGNORECASE,
            )
            if ternary:
                condition_mode = (
                    ternary.group("kind").casefold()
                    + "_"
                    + str(ternary.group("subtype") or "").strip("_").casefold()
                ).rstrip("_")
                context = (
                    ternary.group("yes")
                    if condition_mode == mode
                    else ternary.group("no")
                )
            reference_pattern = (
                rf"\b{reference}\s*\[\s*[1-9]\d*\s*\]|"
                rf"\bi{reference}\s*\([^;\r\n]+,\s*[1-9]\d*\s*\)"
                if reference in {"high", "low"}
                else rf"\b{reference}\b"
            )
            distance_pattern = (
                r"(?:\d+(?:\.\d+)?|[A-Za-z_]\w*)\s*\*?\s*"
                r"(?:_?Point\b|SYMBOL_POINT|[A-Za-z_]\w*)"
            )
            relation_pattern = (
                rf"(?:{reference_pattern})\s*{re.escape(operator)}\s*{distance_pattern}"
            )
            if not re.search(relation_pattern, context, flags=re.IGNORECASE):
                return False
            if offset is not None:
                if not _dependency_satisfies_protection_value(
                    (offset, str(offset_unit or "point")),
                    context,
                    code,
                ):
                    return False
    return True


def _dependency_satisfies_protection_value(
    requirement: tuple[float, str] | None,
    dependency: str,
    code: str,
) -> bool:
    if requirement is None:
        return True
    value, unit = requirement
    context = _mql_dependency_with_input_bindings(dependency, code)
    literal = f"{value:g}"

    def scalar_matches(token: str) -> bool:
        candidate = token.strip()
        if re.fullmatch(r"-?\d+(?:\.\d+)?", candidate):
            return abs(float(candidate) - value) <= 1e-9
        if not re.fullmatch(r"[A-Za-z_]\w*", candidate):
            return False
        assignments = re.findall(
            rf"\b{re.escape(candidate)}\s*=(?!=)\s*"
            r"(-?\d+(?:\.\d+)?)\s*(?:;|$)",
            code,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if assignments:
            return abs(float(assignments[-1]) - value) <= 1e-9
        return _numeric_input_matches(code, candidate, value)

    operand = r"(?:-?\d+(?:\.\d+)?|[A-Za-z_]\w*)"
    multiplication_pairs = list(re.finditer(
        rf"(?P<left>{operand})\s*\*\s*(?P<right>{operand})",
        context,
        flags=re.IGNORECASE,
    ))

    def pair_is_effective(match: re.Match[str]) -> bool:
        prefix = context[max(0, match.start() - 24):match.start()]
        suffix = context[match.end():min(len(context), match.end() + 24)]
        return not (
            re.search(r"(?:^|[^\w.])0(?:\.0+)?\s*\*\s*$", prefix)
            or re.match(r"\s*\*\s*0(?:\.0+)?(?:[^\w.]|$)", suffix)
        )

    def tied_multiplier(unit_operand: re.Pattern[str]) -> bool:
        for match in multiplication_pairs:
            if not pair_is_effective(match):
                continue
            left = match.group("left")
            right = match.group("right")
            if unit_operand.fullmatch(left) and scalar_matches(right):
                return True
            if unit_operand.fullmatch(right) and scalar_matches(left):
                return True
        return False

    if unit == "atr":
        atr_operand = re.compile(
            r"(?:atr\w*|[A-Za-z_]\w*atr\w*)",
            re.IGNORECASE,
        )
        if tied_multiplier(atr_operand):
            return True
        direct_atr = re.search(
            rf"\biATR\s*\([^)]*\)\s*\*\s*(?P<right>{operand})|"
            rf"(?P<left>{operand})\s*\*\s*\biATR\s*\([^)]*\)",
            context,
            flags=re.IGNORECASE,
        )
        return bool(
            direct_atr
            and scalar_matches(direct_atr.group("right") or direct_atr.group("left"))
        )
    if unit == "r":
        return tied_multiplier(re.compile(
            r"(?:protected|actual|stop)\w*(?:distance|loss)\w*",
            re.IGNORECASE,
        ))
    if unit == "pip":
        pip_names = re.findall(
            r"\b(?:pip\w*|[A-Za-z_]\w*pip\w*)\b",
            context,
            re.IGNORECASE,
        )
        if not pip_names:
            return False
        pip_scale_valid = any(re.search(
            rf"\b{re.escape(name)}\s*=\s*[^;\r\n]{{0,160}}"
            rf"(?:Digits|_Digits|SYMBOL_DIGITS)[^;\r\n]{{0,160}}"
            rf"(?:10(?:\.0+)?\s*\*\s*_?Point|_?Point\s*\*\s*10(?:\.0+)?)",
            code,
            flags=re.IGNORECASE,
        ) for name in pip_names)
        return bool(
            pip_scale_valid
            and tied_multiplier(re.compile(
                r"(?:pip\w*|[A-Za-z_]\w*pip\w*)",
                re.IGNORECASE,
            ))
        )
    if unit == "point":
        return tied_multiplier(re.compile(
            r"(?:_?Point|SYMBOL_POINT|[A-Za-z_]\w*point\w*)",
            re.IGNORECASE,
        ))
    return bool(re.search(
        rf"(?<![\d.]){re.escape(literal)}(?:\.0+)?(?![\d.])",
        context,
    ))


def _dependency_satisfies_stop_percentage_range(
    requirement: tuple[float, float] | None,
    dependency: str,
    code: str,
) -> bool:
    """Bind a percent stop to entry price and an optimization-ready input."""

    if requirement is None:
        return True
    low, high = requirement
    context = _mql_dependency_with_input_bindings(dependency, code)
    percent_names = set(re.findall(
        r"\b(?:Inp(?:ut)?_?)?(?:StopLossPercent|StopPercent|SLPercent)\b",
        context,
        flags=re.IGNORECASE,
    ))
    if not percent_names:
        return False
    compact = re.sub(r"[\s()]", "", context)
    base = r"(?:entry\w*|open\w*price|ask|bid|price)"

    def numeric_literal_pattern(value: float) -> str:
        rendered = f"{value:g}"
        if float(value).is_integer():
            return rf"{int(value)}(?:\.0+)?"
        whole, fractional = rendered.split(".", 1)
        return rf"{re.escape(whole)}\.{re.escape(fractional)}0*"

    fail_closed_conditions = _mql_fail_closed_return_conditions(
        code,
        allow_void_return=True,
    )
    for name in percent_names:
        declaration = re.search(
            rf"\b(?:input|extern)\s+(?:double|float)\s+{re.escape(name)}"
            rf"\s*=\s*(?P<value>\d+(?:\.\d+)?)\s*;",
            code,
            flags=re.IGNORECASE,
        )
        if declaration is None:
            continue
        selected = float(declaration.group("value"))
        if selected < low - 1e-9 or selected > high + 1e-9:
            continue
        token = re.escape(name)
        formula_bound = bool(re.search(
            rf"(?:{base}\*{token}/100(?:\.0+)?|"
            rf"{token}\*{base}/100(?:\.0+)?|"
            rf"{token}/100(?:\.0+)?\*{base}|"
            rf"{base}\*{token}\*0\.0*1|"
            rf"{token}\*0\.0*1\*{base})",
            compact,
            flags=re.IGNORECASE,
        ))
        if not formula_bound:
            continue
        low_literal = numeric_literal_pattern(low)
        high_literal = numeric_literal_pattern(high)
        rejects_below = False
        rejects_above = False
        for condition in fail_closed_conditions:
            # Every invalid region must independently imply the return.  A
            # conjunction such as x<low && x>high is impossible and therefore
            # cannot be accepted as a range guard.  OR-only compounds are safe.
            if "&&" in condition:
                continue
            rejects_below = bool(
                rejects_below
                or re.search(
                    rf"\b{token}\b\s*<=?\s*{low_literal}\b|"
                    rf"\b{low_literal}\b\s*>=?\s*{token}\b",
                    condition,
                    flags=re.IGNORECASE,
                )
            )
            rejects_above = bool(
                rejects_above
                or re.search(
                    rf"\b{token}\b\s*>=?\s*{high_literal}\b|"
                    rf"\b{high_literal}\b\s*<=?\s*{token}\b",
                    condition,
                    flags=re.IGNORECASE,
                )
            )
        if rejects_below and rejects_above:
            return True
    return False


def _mql_order_modes_for_expression(value: str, code: str) -> set[str]:
    modes: set[str] = set()
    resolved_variables: set[str] = set()

    def collect(candidate: str) -> None:
        variants = (
            ("buy_stop", r"\b(?:OP_BUYSTOP|ORDER_TYPE_BUY_STOP)\b"),
            ("sell_stop", r"\b(?:OP_SELLSTOP|ORDER_TYPE_SELL_STOP)\b"),
            ("buy_limit", r"\b(?:OP_BUYLIMIT|ORDER_TYPE_BUY_LIMIT)\b"),
            ("sell_limit", r"\b(?:OP_SELLLIMIT|ORDER_TYPE_SELL_LIMIT)\b"),
            ("market_buy", r"\b(?:OP_BUY|ORDER_TYPE_BUY)\b"),
            ("market_sell", r"\b(?:OP_SELL|ORDER_TYPE_SELL)\b"),
        )
        for variant, pattern in variants:
            if not re.search(pattern, candidate, flags=re.IGNORECASE):
                continue
            modes.add(variant)
            modes.add("market" if variant.startswith("market_") else "pending")
            if variant.endswith("_stop"):
                modes.add("stop_entry")
            if variant.endswith("_limit"):
                modes.add("limit_entry")

    def resolve_variable(normalized: str) -> None:
        normalized_key = normalized.casefold()
        if normalized_key in resolved_variables:
            return
        resolved_variables.add(normalized_key)
        assignments: list[tuple[str, bool]] = []
        for match in re.finditer(
            rf"\b{re.escape(normalized)}\s*=(?!=)\s*([^;\r\n]+)",
            code,
            flags=re.IGNORECASE,
        ):
            line_start = max(code.rfind("\n", 0, match.start()), code.rfind(";", 0, match.start())) + 1
            prefix = code[line_start:match.start()]
            assignments.append((
                match.group(1),
                bool(re.search(r"\b(?:if|else)\b", prefix, re.IGNORECASE)),
            ))
        last_unconditional = max(
            (index for index, (_value, conditional) in enumerate(assignments) if not conditional),
            default=0,
        )
        for assigned, _conditional in assignments[last_unconditional:]:
            collect(assigned)
            nested = " ".join(assigned.split())
            if re.fullmatch(r"[A-Za-z_]\w*", nested):
                resolve_variable(nested)

    collect(value)
    normalized = " ".join(value.split())
    if re.fullmatch(r"[A-Za-z_]\w*", normalized):
        resolve_variable(normalized)
    return modes


def _mql_trade_execution_evidence(
    records: list[dict[str, object]],
    code: str,
) -> tuple[set[str], list[str], list[str], list[dict[str, object]]]:
    """Return modes, protection dependencies, and per-call argument evidence."""

    modes: set[str] = set()
    stop_dependencies: list[str] = []
    take_dependencies: list[str] = []
    call_evidence: list[dict[str, object]] = []
    for record in records:
        name = str(record.get("name") or "").lower()
        arguments = [str(item) for item in record.get("arguments", [])]
        before_call = code[: int(record.get("start") or 0)]
        record_modes: set[str] = set()
        volume_expression = ""
        price_expression = ""
        stop_expression = ""
        take_expression = ""
        if name in {"buy", "sell"}:
            record_modes.update(("market", f"market_{name}"))
        elif name in {"buystop", "sellstop", "buylimit", "selllimit"}:
            specific_mode = {
                "buystop": "buy_stop",
                "sellstop": "sell_stop",
                "buylimit": "buy_limit",
                "selllimit": "sell_limit",
            }[name]
            record_modes.update(("pending", specific_mode))
            record_modes.add(
                "stop_entry" if specific_mode.endswith("_stop") else "limit_entry"
            )
        elif name in {"ordersend", "positionopen"} and len(arguments) >= 2:
            if name == "ordersend" and len(arguments) == 2:
                request_name = " ".join(arguments[0].split())
                if re.fullmatch(r"[A-Za-z_]\w*", request_name):
                    def last_request_assignment(field: str) -> str:
                        assigned = re.findall(
                            rf"\b{re.escape(request_name)}\s*\.\s*{field}\s*"
                            rf"=(?!=)\s*([^;\r\n]+)",
                            before_call,
                            flags=re.IGNORECASE,
                        )
                        return assigned[-1] if assigned else ""

                    type_expression = last_request_assignment("type")
                    record_modes.update(
                        _mql_order_modes_for_expression(type_expression, before_call)
                    )
                    volume_expression = last_request_assignment("volume")
                    price_expression = last_request_assignment("price")
                    stop_expression = last_request_assignment("sl")
                    take_expression = last_request_assignment("tp")
                    stop_dependency = (
                        _mql_expression_dependency_text(stop_expression, before_call)
                        if _mql_expression_has_nonzero_value(stop_expression, before_call)
                        else ""
                    )
                    take_dependency = (
                        _mql_expression_dependency_text(take_expression, before_call)
                        if _mql_expression_has_nonzero_value(take_expression, before_call)
                        else ""
                    )
                    if stop_dependency:
                        stop_dependencies.append(stop_dependency)
                    if take_dependency:
                        take_dependencies.append(take_dependency)
                    call_evidence.append({
                        "name": name,
                        "modes": record_modes,
                        "volume": _mql_expression_dependency_text(
                            volume_expression, before_call
                        ),
                        "price": _mql_expression_dependency_text(
                            price_expression, before_call
                        ),
                        "stop": stop_dependency,
                        "take": take_dependency,
                        "start": int(record.get("start") or 0),
                    })
                    modes.update(record_modes)
                continue
            record_modes.update(
                _mql_order_modes_for_expression(arguments[1], before_call)
            )

        stop_index: int | None = None
        take_index: int | None = None
        volume_index: int | None = None
        price_index: int | None = None
        if name == "ordersend" and len(arguments) >= 7:
            volume_index, price_index, stop_index, take_index = 2, 3, 5, 6
        elif name == "positionopen" and len(arguments) >= 6:
            volume_index, price_index, stop_index, take_index = 2, 3, 4, 5
        elif name in {"buy", "sell", "buystop", "sellstop", "buylimit", "selllimit"} and len(arguments) >= 5:
            volume_index = 0
            price_index = 2 if name in {"buy", "sell"} else 1
            stop_index, take_index = 3, 4
        if stop_index is not None and take_index is not None:
            volume_expression = arguments[volume_index] if volume_index is not None else ""
            price_expression = arguments[price_index] if price_index is not None else ""
            stop_expression = arguments[stop_index]
            take_expression = arguments[take_index]
            stop_dependency = ""
            take_dependency = ""
            if _mql_expression_has_nonzero_value(arguments[stop_index], before_call):
                stop_dependency = _mql_expression_dependency_text(
                    arguments[stop_index], before_call
                )
                stop_dependencies.append(stop_dependency)
            if _mql_expression_has_nonzero_value(arguments[take_index], before_call):
                take_dependency = _mql_expression_dependency_text(
                    arguments[take_index], before_call
                )
                take_dependencies.append(take_dependency)
            call_evidence.append({
                "name": name,
                "modes": record_modes,
                "volume": _mql_expression_dependency_text(
                    volume_expression, before_call
                ),
                "price": _mql_expression_dependency_text(price_expression, before_call),
                "stop": stop_dependency,
                "take": take_dependency,
                "start": int(record.get("start") or 0),
            })
            modes.update(record_modes)
    return modes, stop_dependencies, take_dependencies, call_evidence


def analyze_compact_ea_source(
    source_text: object,
    *,
    strategy_brief: object,
    strategy_brief_digest: object,
    strategy_spec_digest: object,
    source_digest: object,
    target_platform: object,
) -> dict:
    """Build fail-closed structural/semantic evidence for one v3 EA."""

    brief_digest = str(strategy_brief_digest or "").strip().lower()
    spec_digest = str(strategy_spec_digest or "").strip().lower()
    declared_source_digest = str(source_digest or "").strip().lower()
    platform = str(target_platform or "").strip().lower()
    brief = _compact_ea_brief_content(strategy_brief)
    findings: list[str] = []
    checks = {
        "bindingValid": False,
        "strategyBriefContract": brief is not None,
        "lexicallyUnambiguous": False,
        "testerInputContract": False,
        "executionSafety": False,
        "strategyBriefDigestBound": False,
        "expertAdvisorLifecycle": False,
        "reachableCallGraphAcyclic": False,
        "boundedLoopStructure": False,
        "referenceParametersAbsent": False,
        "globalExecutableCallsAbsent": False,
        "tradeCallGraphExclusive": False,
        "signalNoneSentinel": False,
        "closedBarExecution": False,
        "entryExecution": False,
        "exitAndProtectionExecution": False,
        "moneyManagementExecution": False,
        "riskSizingExecution": False,
        "lotCalculationSafety": False,
        "positionCapExecution": False,
        "orderExecution": False,
        "recoveryPolicy": False,
        "displayBehavior": False,
    }
    if brief is None:
        findings.append("ea_compact_strategy_brief_invalid")
    computed_source_digest = ""
    if isinstance(source_text, str):
        try:
            computed_source_digest = hashlib.sha256(
                source_text.encode("utf-8", errors="strict")
            ).hexdigest()
        except UnicodeEncodeError:
            pass
    checks["bindingValid"] = bool(
        re.fullmatch(r"[0-9a-f]{64}", brief_digest)
        and re.fullmatch(r"[0-9a-f]{64}", spec_digest)
        and re.fullmatch(r"[0-9a-f]{64}", declared_source_digest)
        and declared_source_digest == computed_source_digest
        and platform in {"mt4", "mt5"}
    )
    if not checks["bindingValid"]:
        findings.append("ea_compact_binding_invalid")

    lexical = _indicator_lexical_views(source_text)
    if lexical is None:
        findings.append("ea_source_lexically_ambiguous")
        code = ""
        descriptions: tuple[str, ...] = ()
    else:
        checks["lexicallyUnambiguous"] = True
        code, descriptions = lexical
    checks["testerInputContract"] = bool(
        platform != "mt4" or _mql4_tester_input_contract_valid(code)
    )
    if not checks["testerInputContract"]:
        findings.append("ea_tester_input_contract_unsupported")
    execution_safety_findings = _mql_execution_safety_findings(code)
    checks["executionSafety"] = not execution_safety_findings
    findings.extend(execution_safety_findings)
    marker = f"EA_STRATEGY_BRIEF_SHA256:{brief_digest}".lower()
    checks["strategyBriefDigestBound"] = any(
        marker in " ".join(description.split()).lower()
        for description in descriptions
    )
    if not checks["strategyBriefDigestBound"]:
        findings.append("ea_strategy_brief_digest_binding_missing")

    functions = _compact_ea_function_map(code) if code else None
    event_name_pattern = (
        r"OnInit|OnDeinit|OnStart|OnTick|OnTimer|OnTrade|"
        r"OnTradeTransaction|OnBookEvent|OnChartEvent|OnCalculate|"
        r"OnTester|OnTesterInit|OnTesterPass|OnTesterDeinit|init|deinit|start"
    )
    event_handler_occurrences = [
        str(name or "").casefold()
        for name in re.findall(
            rf"\b({event_name_pattern})\s*\(",
            code,
            flags=re.IGNORECASE,
        )
    ]
    canonical_event_handlers = [
        str(name or "").casefold()
        for name in re.findall(
            rf"\b(?:void|int|double)\s+({event_name_pattern})\s*\(",
            code,
            flags=re.IGNORECASE,
        )
    ]
    allowed_event_handlers = {"oninit", "ondeinit", "ontick"}
    checks["expertAdvisorLifecycle"] = bool(
        isinstance(functions, dict)
        and len(functions.get("ontick", [])) == 1
        and len(re.findall(r"\bvoid\s+OnTick\s*\(", code, re.IGNORECASE)) == 1
        and len(re.findall(r"\b(?:void|int)\s+OnInit\s*\(", code, re.IGNORECASE)) <= 1
        and len(re.findall(r"\bvoid\s+OnDeinit\s*\(", code, re.IGNORECASE)) <= 1
        and sorted(event_handler_occurrences) == sorted(canonical_event_handlers)
        and event_handler_occurrences.count("ontick") == 1
        and event_handler_occurrences.count("oninit") <= 1
        and event_handler_occurrences.count("ondeinit") <= 1
        and set(event_handler_occurrences).issubset(allowed_event_handlers)
    )
    if not checks["expertAdvisorLifecycle"]:
        findings.append("ea_ontick_lifecycle_missing_or_ambiguous")
    checks["reachableCallGraphAcyclic"] = bool(
        isinstance(functions, dict)
        and _compact_ea_reachable_call_graph_acyclic(functions)
    )
    if not checks["reachableCallGraphAcyclic"]:
        findings.append("ea_reachable_call_cycle_forbidden")
    checks["boundedLoopStructure"] = bool(
        code and _compact_ea_for_loops_provably_bounded(code)
    )
    if not checks["boundedLoopStructure"]:
        findings.append("ea_for_loop_bounds_not_proven")
    checks["referenceParametersAbsent"] = bool(
        code
        and re.search(
            r"\b(?:void|int|bool|double|long|ulong|datetime|string|uint|float)\s+"
            r"[A-Za-z_]\w*\s*\([^;{}]{0,2000}&[^;{}]{0,2000}\)\s*\{",
            code,
            flags=re.IGNORECASE | re.DOTALL,
        )
        is None
    )
    if not checks["referenceParametersAbsent"]:
        findings.append("ea_reference_parameter_forbidden")
    global_code = _compact_ea_global_code(code) if code else None
    checks["globalExecutableCallsAbsent"] = bool(
        isinstance(global_code, str)
        and re.search(r"\b[A-Za-z_]\w*\s*\(", global_code) is None
    )
    if not checks["globalExecutableCallsAbsent"]:
        findings.append("ea_global_executable_call_forbidden")
    on_tick_reachable = _compact_ea_reachable_code(functions or {})
    lifecycle_reachable = _compact_ea_reachable_code_from(
        functions or {},
        ("oninit", "ondeinit"),
    )
    all_trade_side_effects = _mql_trade_side_effect_call_names(code)
    on_tick_trade_side_effects = _mql_trade_side_effect_call_names(on_tick_reachable)
    lifecycle_trade_side_effects = _mql_trade_side_effect_call_names(lifecycle_reachable)
    checks["tradeCallGraphExclusive"] = bool(
        checks["expertAdvisorLifecycle"]
        and sorted(all_trade_side_effects) == sorted(on_tick_trade_side_effects)
        and not lifecycle_trade_side_effects
    )
    if not checks["tradeCallGraphExclusive"]:
        findings.append("ea_trade_call_outside_ontick_forbidden")
    reachable = on_tick_reachable
    reachable = _compact_ea_one_level_trade_bindings(
        code,
        functions or {},
        reachable,
    )
    checks["signalNoneSentinel"] = bool(
        re.search(r"\bSIGNAL_NONE\b\s*(?:=|\s)\s*-1\b", code)
    )
    if not checks["signalNoneSentinel"]:
        findings.append("ea_signal_none_sentinel_invalid")

    trade_calls = _mql_trade_call_records(reachable)
    (
        implemented_order_modes,
        trade_stop_dependencies,
        trade_take_dependencies,
        trade_argument_evidence,
    ) = (
        _mql_trade_execution_evidence(
        trade_calls,
        reachable,
        )
    )
    first_open_trade_start = min(
        (int(record["start"]) for record in trade_calls),
        default=-1,
    )
    has_stop = bool(trade_stop_dependencies)
    has_take = bool(trade_take_dependencies)
    open_trade = bool(trade_calls)
    checks["entryExecution"] = bool(
        open_trade and re.search(r"\bif\s*\(", reachable, flags=re.IGNORECASE)
    )
    if not checks["entryExecution"]:
        findings.append("ea_reachable_conditional_entry_missing")

    content = brief or {field: "" for field in CONTENT_FIELDS}
    source_order_execution = content["orderExecution"].replace(
        IMPLEMENTATION_DEFAULT_ORDER_EXECUTION,
        "",
    )
    entry_text = " ".join((content["entryRules"], source_order_execution)).lower()
    exit_text = content["exitRules"].lower()
    money_text = content["moneyManagement"].lower()
    recovery_text = content["recoveryRules"].lower()
    explicit_closed_bar_timing = bool(re.search(
        r"(?:closed[- ]?bar|confirmed[- ]?bar|แท่งปิด|\[\s*[12]\s*\])",
        entry_text,
        flags=re.IGNORECASE,
    ))
    explicit_intrabar_timing = bool(re.search(
        r"(?:intra[ -]?bar|every\s+tick|current\s+bar|forming\s+bar|"
        r"immediate(?:ly)?|ระหว่างแท่ง|ทุก\s*tick|แท่งปัจจุบัน|ทันที)",
        entry_text,
        flags=re.IGNORECASE,
    ))
    order_default_present = IMPLEMENTATION_DEFAULT_ORDER_EXECUTION.lower() in (
        content["orderExecution"].lower()
    )
    closed_bar_required = bool(
        explicit_closed_bar_timing
        or (order_default_present and not explicit_intrabar_timing)
    )
    historical_read = bool(re.search(
        r"\b(?:Open|High|Low|Close|Volume)\s*\[\s*[1-9]\d*\s*\]|"
        r"\bi(?:Open|High|Low|Close|MA|RSI|ATR)\s*\([^;]{0,500},\s*[1-9]\d*\s*\)",
        reachable,
        flags=re.IGNORECASE,
    ))
    entry_path_code = (
        reachable if first_open_trade_start < 0 else reachable[:first_open_trade_start]
    )
    order_execution_text = content["orderExecution"]
    spread_guard_required = _component_enabled_requested(
        order_execution_text,
        (r"\bspread\b", r"สเปรด"),
    )
    spread_guard_valid = not spread_guard_required
    spread_limit_name = ""
    if spread_guard_required:
        spread_limit_match = re.search(
            r"\b(?:input|extern)\s+(?:int|double|float)\s+"
            r"(?P<name>(?:Max(?:imum)?|Allowed)?Spread(?:Limit)?Points?)\s*=\s*"
            r"(?P<value>\d+(?:\.\d+)?)\s*;",
            code,
            flags=re.IGNORECASE,
        )
        if spread_limit_match and float(spread_limit_match.group("value")) > 0:
            spread_limit_name = spread_limit_match.group("name")
            spread_variables = re.findall(
                r"\b([A-Za-z_]\w*)\s*=(?!=)\s*"
                r"(?:MarketInfo\s*\([^;]{0,180}\bMODE_SPREAD\b[^;]{0,80}\)|"
                r"SymbolInfoInteger\s*\([^;]{0,180}\bSYMBOL_SPREAD\b[^;]{0,80}\))"
                r"\s*;",
                entry_path_code,
                flags=re.IGNORECASE,
            )
            spread_guard_valid = any(
                "&&" not in condition
                and any(
                    re.search(
                        rf"\b{re.escape(spread_variable)}\b\s*>\s*"
                        rf"\b{re.escape(spread_limit_name)}\b|"
                        rf"\b{re.escape(spread_limit_name)}\b\s*<\s*"
                        rf"\b{re.escape(spread_variable)}\b",
                        condition,
                        flags=re.IGNORECASE,
                    )
                    for spread_variable in spread_variables
                )
                for condition in _mql_fail_closed_return_conditions(
                    entry_path_code,
                    allow_void_return=True,
                    top_level_only=True,
                )
            )
        if not spread_guard_valid:
            findings.append("ea_spread_guard_missing")
    external_entry_data_required = bool(re.search(
        r"\bEPS\b|\bearnings?\s+(?:growth|rank|increase)|"
        r"\bshares?\s+outstanding\b|\binstitutional\s+sponsorship\b|"
        r"\bfundamental(?:s|\s+data)?\b|ยอดขาย(?:เติบโต|โต)|กำไร(?:รายปี|ไตรมาส)",
        entry_text,
        flags=re.IGNORECASE,
    ))
    external_gate_valid = not external_entry_data_required
    external_gate_names: list[str] = []
    if external_entry_data_required:
        normalized_entry_path = " ".join(entry_path_code.split())
        unbraced_entry_starts = _mql_unbraced_controlled_statement_starts(
            normalized_entry_path
        )
        external_gate_names = re.findall(
            r"\b(?:input|extern)\s+bool\s+"
            r"((?:[A-Za-z_]\w*)?(?:Fundamental|External|Eligibility|Screen|Criteria)"
            r"(?:[A-Za-z_]\w*)?)\s*=\s*false\s*;",
            code,
            flags=re.IGNORECASE,
        )
        external_gate_valid = any(
            _mql_brace_depth_at(normalized_entry_path, gate_match.start()) == 0
            and gate_match.start() not in unbraced_entry_starts
            for gate_name in external_gate_names
            for gate_match in re.finditer(
                rf"\bif\s*\(\s*(?:!\s*{re.escape(gate_name)}\b|"
                rf"{re.escape(gate_name)}\b\s*==\s*false\b|"
                rf"false\b\s*==\s*{re.escape(gate_name)}\b)\s*\)"
                r"\s*(?:\{\s*)?return\b",
                normalized_entry_path,
                flags=re.IGNORECASE,
            )
        )
        if not external_gate_valid:
            checks["entryExecution"] = False
            findings.append("ea_external_entry_gate_missing")
    forming_price_read = bool(re.search(
        r"\b(?:Open|High|Low|Close|Volume)\s*\[\s*0\s*\]",
        entry_path_code,
        flags=re.IGNORECASE,
    ))
    on_tick_declaration = re.search(
        r"\b(?:void|int)\s+OnTick\s*\(",
        code,
        flags=re.IGNORECASE,
    )
    global_prefix = code[: on_tick_declaration.start()] if on_tick_declaration else ""
    global_bar_states = tuple(re.findall(
        r"\bdatetime\s+([A-Za-z_]\w*)\s*(?:=\s*(?:0|NULL))?\s*;",
        global_prefix,
        flags=re.IGNORECASE,
    ))
    new_bar_guard = _stateful_new_bar_guard(
        reachable,
        first_open_trade_start,
        global_bar_states,
    )
    if not new_bar_guard:
        pretrade = reachable if first_open_trade_start < 0 else reachable[:first_open_trade_start]
        trade_function_names = {
            function_name
            for function_name, helper_bodies in (functions or {}).items()
            if any(_mql_trade_call_records(body) for body in helper_bodies)
        }
        for helper_name, helper_bodies in (functions or {}).items():
            if not any(_stateful_new_bar_guard(body, -1) for body in helper_bodies):
                continue
            if re.search(
                rf"\bif\s*\(\s*!\s*{re.escape(helper_name)}\s*\(\s*\)\s*\)"
                rf"\s*(?:\{{\s*)?return\b",
                pretrade,
                flags=re.IGNORECASE,
            ):
                new_bar_guard = True
                break
            if trade_function_names:
                trade_target = "|".join(
                    re.escape(name) for name in sorted(trade_function_names)
                )
                if re.search(
                    rf"\bif\s*\(\s*{re.escape(helper_name)}\s*\(\s*\)\s*\)"
                    rf"\s*(?:\{{[^{{}}]{{0,1200}})?\b(?:{trade_target})\s*\(",
                    pretrade,
                    flags=re.IGNORECASE,
                ):
                    new_bar_guard = True
                    break
    checks["closedBarExecution"] = bool(
        not closed_bar_required
        or (historical_read and new_bar_guard and not forming_price_read)
    )
    if not checks["closedBarExecution"]:
        findings.append("ea_closed_bar_execution_guard_missing")

    close_calls = _mql_named_call_records(
        reachable,
        ("OrderClose", "OrderCloseBy", "PositionClose", "PositionClosePartial"),
    )
    modify_calls = _mql_named_call_records(
        reachable,
        ("OrderModify", "PositionModify"),
    )
    has_close = bool(close_calls)
    modify_stop_expressions: list[str] = []
    modify_take_expressions: list[str] = []
    for record in modify_calls:
        arguments = [str(item) for item in record.get("arguments", [])]
        name = str(record.get("name") or "").lower()
        stop_index, take_index = (
            (2, 3) if name == "ordermodify" else (1, 2)
        )
        if len(arguments) <= take_index:
            continue
        before_call = reachable[: int(record.get("start") or 0)]
        if _mql_expression_has_nonzero_value(arguments[stop_index], before_call):
            modify_stop_expressions.append(_mql_expression_dependency_text(
                arguments[stop_index], before_call
            ))
        if _mql_expression_has_nonzero_value(arguments[take_index], before_call):
            modify_take_expressions.append(_mql_expression_dependency_text(
                arguments[take_index], before_call
            ))
    has_modify = bool(modify_stop_expressions or modify_take_expressions)
    has_stop = has_stop or bool(modify_stop_expressions)
    has_take = has_take or bool(modify_take_expressions)
    trailing_requested = _component_enabled_requested(
        exit_text,
        _TRAILING_STOP_ALIASES,
    )
    break_even_requested = _component_enabled_requested(
        exit_text,
        _BREAK_EVEN_ALIASES,
    )
    partial_close_requested = _component_enabled_requested(
        exit_text,
        _PARTIAL_CLOSE_ALIASES,
    )
    generic_close_requested = bool(re.search(
        r"(?:\bclose\b.{0,80}\bopposite\b|\bopposite\b.{0,80}\bclose\b|"
        r"\b(?:close|exit)\s+(?:the\s+)?(?:position|trade|order)s?\b|"
        r"(?:ปิด|ลด|ออกจาก)(?:สถานะ|ออเดอร์|ออร์เดอร์|ไม้|คำสั่ง)|"
        r"สัญญาณ.*ตรงข้าม|ตรงข้าม.*สัญญาณ)",
        exit_text,
        flags=re.IGNORECASE,
    ))
    entry_gate_preserves_exit_management = True
    if generic_close_requested:
        on_tick_bodies = (functions or {}).get("ontick", [])
        on_tick_body = on_tick_bodies[0] if len(on_tick_bodies) == 1 else ""
        percent_gate_names = re.findall(
            r"\b(?:input|extern)\s+(?:double|float)\s+"
            r"((?:Inp(?:ut)?_?)?(?:StopLossPercent|StopPercent|SLPercent))\b",
            code,
            flags=re.IGNORECASE,
        )
        gate_names = tuple(dict.fromkeys((*external_gate_names, *percent_gate_names)))
        if spread_limit_name:
            gate_names = tuple(dict.fromkeys((*gate_names, spread_limit_name)))
        gate_positions: list[int] = []
        if gate_names and on_tick_body:
            gate_name_pattern = "|".join(re.escape(name) for name in gate_names)
            for gate_match in re.finditer(
                r"\bif\s*\((?P<condition>[^;]{1,720})\)\s*(?:\{\s*)?return\b",
                on_tick_body,
                flags=re.IGNORECASE,
            ):
                if re.search(
                    rf"\b(?:{gate_name_pattern})\b",
                    gate_match.group("condition"),
                    flags=re.IGNORECASE,
                ):
                    gate_positions.append(gate_match.start())
        if gate_positions:
            management_positions = [
                int(record.get("start") or 0)
                for record in _mql_named_call_records(
                    on_tick_body,
                    ("OrderClose", "OrderCloseBy", "PositionClose", "PositionClosePartial"),
                )
            ]
            management_helpers = {
                helper_name
                for helper_name, helper_bodies in (functions or {}).items()
                if helper_name != "ontick"
                and any(
                    _mql_named_call_records(
                        helper_body,
                        ("OrderClose", "OrderCloseBy", "PositionClose", "PositionClosePartial"),
                    )
                    for helper_body in helper_bodies
                )
            }
            for helper_name in management_helpers:
                management_positions.extend(
                    match.start()
                    for match in re.finditer(
                        rf"\b{re.escape(helper_name)}\s*\(",
                        on_tick_body,
                        flags=re.IGNORECASE,
                    )
                )
            entry_gate_preserves_exit_management = bool(
                management_positions
                and max(management_positions) < min(gate_positions)
            )
    modification_text = "\n".join(modify_stop_expressions)
    trailing_implemented = bool(
        modify_stop_expressions
        and re.search(
            r"trail(?:ing)?|trailing[ _-]?stop|ระยะเลื่อน|เลื่อน.*(?:stop|sl)",
            modification_text,
            flags=re.IGNORECASE,
        )
    )
    break_even_implemented = bool(
        modify_stop_expressions
        and (
            re.search(
                r"break[ _-]?even|breakeven|คุ้มทุน",
                modification_text,
                flags=re.IGNORECASE,
            )
            or re.search(
                r"OrderOpenPrice\s*\(|POSITION_PRICE_OPEN",
                modification_text,
                flags=re.IGNORECASE,
            )
        )
    )
    partial_close_implemented = False
    partial_volume_dependencies: list[str] = []
    for record in close_calls:
        name = str(record.get("name") or "").lower()
        arguments = [str(item) for item in record.get("arguments", [])]
        before_call = reachable[: int(record.get("start") or 0)]
        if name in {"positionclosepartial", "orderclose"} and len(arguments) >= 2:
            volume_expression = arguments[1]
            volume_dependency = _mql_expression_dependency_text(
                volume_expression,
                before_call,
            )
            partial_volume_dependencies.append(volume_dependency)
            partial_close_implemented = bool(re.search(
                r"(?:OrderLots\s*\(\s*\)|POSITION_VOLUME|"
                r"PositionGetDouble\s*\(\s*POSITION_VOLUME\s*\)|\b\w*(?:volume|lots?)\w*\b)"
                r".{0,80}(?:\*\s*0\.[0-9]*[1-9]|/\s*[2-9]\d*)",
                volume_dependency,
                flags=re.IGNORECASE,
            ))
        if partial_close_implemented:
            break
    trailing_disabled = bool(
        IMPLEMENTATION_DEFAULT_TRAILING_STOP.lower() in exit_text
        or re.search(
            r"(?:trailing[ _-]?stop|trail(?:ing)?)\s*(?:=|:)\s*(?:false|off|disabled|0)\b|"
            r"(?:no|without|disable)\s+(?:a\s+)?trail(?:ing)?",
            exit_text,
            flags=re.IGNORECASE,
        )
    )
    break_even_disabled = bool(
        IMPLEMENTATION_DEFAULT_BREAK_EVEN.lower() in exit_text
        or re.search(
            r"(?:break[ _-]?even|breakeven)\s*(?:=|:)\s*(?:false|off|disabled|0)\b|"
            r"(?:no|without|disable)\s+(?:break[ _-]?even|breakeven)",
            exit_text,
            flags=re.IGNORECASE,
        )
    )
    partial_close_disabled = bool(
        IMPLEMENTATION_DEFAULT_PARTIAL_CLOSE.lower() in exit_text
        or re.search(
            r"partial[ _-]?close\s*(?:=|:)\s*(?:false|off|disabled|0)\b|"
            r"(?:no|without|disable)\s+partial[ _-]?close",
            exit_text,
            flags=re.IGNORECASE,
        )
    )
    trailing_requirement = _requested_management_value(exit_text, "trailing")
    trailing_value_valid = bool(
        trailing_requirement is None
        or _dependency_satisfies_protection_value(
            trailing_requirement,
            modification_text,
            code,
        )
    )
    partial_percent = re.search(
        r"(?:partial[ _-]?close|take\s+partial|close\s+partial).{0,48}"
        r"(\d+(?:\.\d+)?)\s*%|"
        r"(\d+(?:\.\d+)?)\s*%.{0,48}(?:partial[ _-]?close|take\s+partial)",
        exit_text,
        flags=re.IGNORECASE,
    )
    partial_value_valid = True
    if partial_percent:
        requested_fraction = float(partial_percent.group(1) or partial_percent.group(2)) / 100.0
        fraction_literal = f"{requested_fraction:g}"
        reciprocal = round(1.0 / requested_fraction) if requested_fraction > 0 else 0
        partial_value_valid = bool(
            partial_volume_dependencies
            and all(
                re.search(
                    rf"\*\s*{re.escape(fraction_literal)}(?:0+)?\b|"
                    rf"/\s*{reciprocal}\b",
                    dependency,
                    flags=re.IGNORECASE,
                )
                for dependency in partial_volume_dependencies
            )
        )
    exit_management_policy_valid = bool(
        not (trailing_disabled and trailing_implemented)
        and not (break_even_disabled and break_even_implemented)
        and not (partial_close_disabled and partial_close_implemented)
        and trailing_value_valid
        and partial_value_valid
    )
    needs_stop = (
        IMPLEMENTATION_DEFAULT_STOP_LOSS.lower() in exit_text
        or _component_enabled_requested(
            exit_text,
            _STOP_LOSS_ALIASES,
        )
    )
    needs_take = (
        IMPLEMENTATION_DEFAULT_TAKE_PROFIT.lower() in exit_text
        or _component_enabled_requested(
            exit_text,
            _TAKE_PROFIT_ALIASES,
        )
    )
    points_v2_stop_default_required = (
        IMPLEMENTATION_DEFAULT_STOP_LOSS.lower() in exit_text
    )
    points_v2_take_default_required = (
        IMPLEMENTATION_DEFAULT_TAKE_PROFIT.lower() in exit_text
    )
    legacy_default_tag = _has_implementation_default_policy_component(
        exit_text,
        LEGACY_IMPLEMENTATION_DEFAULT_POLICY_ID,
        "exitRules",
        "stop_loss",
        "take_profit",
    )
    legacy_atr_stop_default_required = bool(
        legacy_default_tag
        and re.search(r"\bStopLossATR\s*=\s*1\.5\b", exit_text, re.IGNORECASE)
        and re.search(r"\bATRPeriod\s*=\s*14\b|\bATR\s*\(\s*14\s*\)", exit_text, re.IGNORECASE)
    )
    legacy_two_r_take_default_required = bool(
        legacy_default_tag
        and re.search(r"\bRewardRiskRatio\s*=\s*2(?:\.0+)?\b", exit_text, re.IGNORECASE)
    )
    default_stop_required = bool(
        points_v2_stop_default_required or legacy_atr_stop_default_required
    )
    default_take_required = bool(
        points_v2_take_default_required or legacy_two_r_take_default_required
    )
    stop_dependency_text = "\n".join(
        (*trade_stop_dependencies, *modify_stop_expressions)
    )
    take_dependency_text = "\n".join(
        (*trade_take_dependencies, *modify_take_expressions)
    )
    atr_closed_bar = bool(
        re.search(
            r"\biATR\s*\([^;\r\n]{0,240}(?:ATRPeriod|\b14\b)"
            r"[^;\r\n]{0,120},\s*1\s*\)|"
            r"\biATR\s*\([^;\r\n]{0,240}(?:ATRPeriod|\b14\b)[^;\r\n]{0,120}\)"
            r"[^;\r\n]{0,400}\bCopyBuffer\s*\([^;\r\n]{0,160},\s*1\s*,",
            stop_dependency_text,
            flags=re.IGNORECASE,
        )
    )
    broker_floor_bound_to_stop = bool(
        re.search(
            r"MODE_STOPLEVEL|SYMBOL_TRADE_STOPS_LEVEL",
            stop_dependency_text,
            flags=re.IGNORECASE,
        )
        and re.search(r"\b\w*buffer\w*\b", stop_dependency_text, flags=re.IGNORECASE)
        and re.search(r"\bMathMax\s*\(", stop_dependency_text, flags=re.IGNORECASE)
    )
    broker_floor_formula_valid = bool(re.search(
        r"\b(?:double|float)\s+[A-Za-z_]\w*(?:floor|minimum)[A-Za-z_]*\w*\s*="
        r"\s*\(\s*(?:"
        r"MarketInfo\s*\([^;]{0,220}\bMODE_STOPLEVEL\b[^;]{0,100}\)|"
        r"SymbolInfoInteger\s*\([^;]{0,220}\bSYMBOL_TRADE_STOPS_LEVEL\b[^;]{0,100}\)"
        r")\s*\+\s*ExecutionBufferPoints\s*\)\s*\*\s*(?:_?Point)\s*;",
        code,
        flags=re.IGNORECASE,
    ))
    broker_floor_required = bool(re.search(
        r"\bbroker\s+(?:stop|freeze)\s+floor\b|\bMODE_STOPLEVEL\b|"
        r"\bSYMBOL_TRADE_STOPS_LEVEL\b|ระยะขั้นต่ำของโบรกเกอร์",
        f"{exit_text}\n{order_execution_text}",
        flags=re.IGNORECASE,
    ))
    broker_buffer_required = bool(re.search(
        r"\bExecutionBufferPoints\b",
        f"{exit_text}\n{order_execution_text}",
        flags=re.IGNORECASE,
    ))
    broker_floor_semantics = bool(
        not broker_floor_required
        or (
            broker_floor_bound_to_stop
            and broker_floor_formula_valid
            and (
                not broker_buffer_required
                or _numeric_input_matches(code, "ExecutionBufferPoints", 2.0)
            )
        )
    )
    if points_v2_stop_default_required:
        stop_default_inputs = bool(
            _numeric_input_matches(code, "StopLossPoints", 300.0)
            and _numeric_input_matches(code, "ExecutionBufferPoints", 2.0)
        )
        stop_default_semantics = bool(
            stop_default_inputs
            and all(
                re.search(
                    rf"\b{re.escape(input_name)}\b",
                    stop_dependency_text,
                    flags=re.IGNORECASE,
                )
                for input_name in ("StopLossPoints", "ExecutionBufferPoints")
            )
            and _dependency_satisfies_protection_value(
                (300.0, "point"),
                stop_dependency_text,
                code,
            )
            and broker_floor_bound_to_stop
        )
    elif legacy_atr_stop_default_required:
        stop_default_inputs = bool(
            _numeric_input_matches(code, "ATRPeriod", 14.0)
            and _numeric_input_matches(code, "StopLossATR", 1.5)
            and _numeric_input_matches(code, "ExecutionBufferPoints", 2.0)
        )
        stop_default_semantics = bool(
            stop_default_inputs
            and atr_closed_bar
            and all(
                re.search(
                    rf"\b{re.escape(input_name)}\b",
                    stop_dependency_text,
                    flags=re.IGNORECASE,
                )
                for input_name in (
                    "ATRPeriod",
                    "StopLossATR",
                    "ExecutionBufferPoints",
                )
            )
            and _dependency_satisfies_protection_value(
                (1.5, "atr"),
                stop_dependency_text,
                code,
            )
            and broker_floor_bound_to_stop
        )
    else:
        stop_default_inputs = True
        stop_default_semantics = True

    if points_v2_take_default_required:
        take_default_inputs = _numeric_input_matches(
            code,
            "TakeProfitPoints",
            600.0,
        )
        take_default_semantics = bool(
            take_default_inputs
            and re.search(
                r"\bTakeProfitPoints\b",
                take_dependency_text,
                flags=re.IGNORECASE,
            )
            and _dependency_satisfies_protection_value(
                (600.0, "point"),
                take_dependency_text,
                code,
            )
            and re.search(
                r"MODE_STOPLEVEL|SYMBOL_TRADE_STOPS_LEVEL",
                take_dependency_text,
                flags=re.IGNORECASE,
            )
            and re.search(r"\b\w*buffer\w*\b", take_dependency_text, flags=re.IGNORECASE)
            and re.search(r"\bMathMax\s*\(", take_dependency_text, flags=re.IGNORECASE)
        )
    elif legacy_two_r_take_default_required:
        take_default_inputs = _numeric_input_matches(code, "RewardRiskRatio", 2.0)
        take_default_semantics = bool(
            take_default_inputs
            and re.search(
                r"\bRewardRiskRatio\b",
                take_dependency_text,
                flags=re.IGNORECASE,
            )
            and _dependency_satisfies_protection_value(
                (2.0, "r"),
                take_dependency_text,
                code,
            )
        )
    else:
        take_default_inputs = True
        take_default_semantics = True
    source_stop_percentage_range = (
        None if default_stop_required else _requested_stop_percentage_range(exit_text)
    )
    source_stop_requirement = (
        None
        if default_stop_required or source_stop_percentage_range is not None
        else _requested_protection_value(exit_text, "stop")
    )
    source_take_requirement = (
        None if default_take_required else _requested_protection_value(exit_text, "take")
    )
    source_stop_atr_details = (
        None if default_stop_required else _requested_atr_period_shift(exit_text, "stop")
    )
    source_take_atr_details = (
        None if default_take_required else _requested_atr_period_shift(exit_text, "take")
    )
    raw_trade_stop_dependencies = [
        str(item.get("stop") or "")
        for item in trade_argument_evidence
    ]
    raw_trade_take_dependencies = [
        str(item.get("take") or "")
        for item in trade_argument_evidence
    ]
    # A later, unrelated OrderModify/PositionModify call is not proof that every
    # newly opened trade receives its required initial protection.  Compact EA
    # handoff therefore fails closed unless SL and TP are bound to each actual
    # opening call.  This avoids accepting a naked order because some other
    # ticket happens to be modified elsewhere in the source.
    stop_evidence_dependencies = raw_trade_stop_dependencies or [stop_dependency_text]
    take_evidence_dependencies = raw_trade_take_dependencies or [take_dependency_text]
    source_stop_semantics = bool(
        not needs_stop
        or all(
            bool(dependency)
            and _dependency_satisfies_protection_value(
                source_stop_requirement,
                dependency,
                code,
            )
            and _dependency_satisfies_stop_percentage_range(
                source_stop_percentage_range,
                dependency,
                code,
            )
            and _atr_period_shift_dependency_valid(
                source_stop_atr_details,
                dependency,
                code,
            )
            for dependency in stop_evidence_dependencies
        )
    )
    source_stop_semantics = bool(source_stop_semantics and broker_floor_semantics)
    source_take_semantics = bool(
        not needs_take
        or all(
            bool(dependency)
            and _dependency_satisfies_protection_value(
                source_take_requirement,
                dependency,
                code,
            )
            and _atr_period_shift_dependency_valid(
                source_take_atr_details,
                dependency,
                code,
            )
            for dependency in take_evidence_dependencies
        )
    )

    def call_protection_direction_valid(component: str) -> bool:
        required = needs_stop if component == "stop" else needs_take
        if not required:
            return True
        for item in trade_argument_evidence:
            modes = set(item.get("modes") or ())
            sides = {
                "buy"
                for mode in modes
                if mode in {"market_buy", "buy_stop", "buy_limit"}
            } | {
                "sell"
                for mode in modes
                if mode in {"market_sell", "sell_stop", "sell_limit"}
            }
            dependency = str(item.get(component) or "")
            if not dependency:
                return False
            if sides and not all(
                _mql_dependency_has_signed_distance(
                    dependency,
                    side=side,
                    component=component,
                )
                for side in sides
            ):
                return False
        return bool(trade_argument_evidence)

    stop_direction_valid = call_protection_direction_valid("stop")
    take_direction_valid = call_protection_direction_valid("take")
    checks["exitAndProtectionExecution"] = bool(
        (not generic_close_requested or has_close)
        and (not trailing_requested or trailing_implemented)
        and (not break_even_requested or break_even_implemented)
        and (not partial_close_requested or partial_close_implemented)
        and exit_management_policy_valid
        and (not needs_stop or has_stop)
        and (not needs_take or has_take)
        and stop_default_semantics
        and take_default_semantics
        and source_stop_semantics
        and source_take_semantics
        and stop_direction_valid
        and take_direction_valid
        and entry_gate_preserves_exit_management
        and (has_close or has_modify or has_stop or has_take)
    )
    if not checks["exitAndProtectionExecution"]:
        findings.append("ea_exit_or_protection_path_missing")
    if not entry_gate_preserves_exit_management:
        findings.append("ea_entry_gate_precedes_exit_management")

    def call_volume_guarded(item: dict[str, object]) -> bool:
        dependency = str(item.get("volume") or "")
        # Dependency expansion is ordered from the actual trade argument toward
        # its assignments.  A one-level trade wrapper therefore starts with a
        # short alias chain such as ``volume -> lot -> CalculateRiskLot(...)``.
        # Accept the guard on either alias, but stop at the first expression so
        # an unrelated guarded sizing intermediate cannot satisfy this check.
        guarded_candidates: list[str] = []
        for line in dependency.splitlines():
            candidate = line.strip()
            if not re.fullmatch(r"[A-Za-z_]\w*", candidate):
                break
            guarded_candidates.append(candidate)
        if not guarded_candidates:
            return False
        before_call = reachable[: int(item.get("start") or 0)]
        return any(
            "&&" not in condition
            and re.search(
                rf"\b{re.escape(candidate)}\b\s*(?:<=|==|<)\s*"
                rf"0(?:\.0+)?\b",
                condition,
                flags=re.IGNORECASE,
            )
            is not None
            for candidate in guarded_candidates
            for condition in _mql_fail_closed_return_conditions(
                before_call,
                allow_void_return=True,
                top_level_only=True,
            )
        )

    base_money_management_execution = bool(
        money_text
        and trade_argument_evidence
        and all(call_volume_guarded(item) for item in trade_argument_evidence)
    )
    percentage_token = (
        r"(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|"
        r"หนึ่ง|สอง|สาม|สี่|ห้า|หก|เจ็ด|แปด|เก้า|สิบ)"
    )
    # The canonical fixed-lot default advertises ``RiskPercent`` only as an
    # optional, disabled-by-default mode.  Do not mistake that metadata for a
    # source request that makes the percentage-risk implementation mandatory.
    source_money_text = money_text.replace(
        IMPLEMENTATION_DEFAULT_RISK_SIZING.lower(),
        " ",
    )
    percentage_risk_requested = bool(re.search(
        rf"(?:risk|ความเสี่ยง|เสี่ยง).{{0,48}}{percentage_token}\s*(?:%|percent|เปอร์เซ็นต์)|"
        rf"{percentage_token}\s*(?:%|percent|เปอร์เซ็นต์)\s*(?:of\s+)?(?:equity|balance|ทุน)|"
        r"\bRiskPercent\s*=",
        source_money_text,
        flags=re.IGNORECASE,
    ))
    risk_sizing_required = bool(
        IMPLEMENTATION_DEFAULT_LOT_CALCULATION.lower() in money_text
        or percentage_risk_requested
    )
    lot_calculation_required = bool(
        risk_sizing_required
        or IMPLEMENTATION_DEFAULT_LOT_CALCULATION.lower() in money_text
    )
    requested_risk_percent = _requested_risk_percentage(source_money_text)
    requested_fixed_lot = _requested_fixed_lot(money_text)
    canonical_fixed_lot_input_valid = bool(
        IMPLEMENTATION_DEFAULT_RISK_SIZING.lower() not in money_text
        or _numeric_input_matches(code, "FixedLot", 0.01)
    )
    equity_read = bool(re.search(
        r"\bAccountEquity\s*\(\s*\)|"
        r"\bAccountInfoDouble\s*\(\s*ACCOUNT_EQUITY\s*\)",
        reachable,
        flags=re.IGNORECASE,
    ))
    risk_percent_name = r"(?:RiskPercent|RiskPct|RiskPercentage|RiskPerTradePercent)"
    risk_percent_used = bool(
        re.search(rf"\b{risk_percent_name}\b", reachable, flags=re.IGNORECASE)
        and re.search(
            rf"\b{risk_percent_name}\b.{{0,80}}/\s*100(?:\.0+)?\b|"
            rf"/\s*100(?:\.0+)?\b.{{0,80}}\b{risk_percent_name}\b",
            reachable,
            flags=re.IGNORECASE,
        )
    )
    canonical_risk_inputs_valid = bool(
        IMPLEMENTATION_DEFAULT_RISK_SIZING.lower() not in money_text
        or _numeric_input_matches(code, "RiskPercent", 1.0)
    )
    source_risk_input_valid = True
    if (
        requested_risk_percent is not None
        and IMPLEMENTATION_DEFAULT_RISK_SIZING.lower() not in money_text
    ):
        source_risk_match = re.search(
            rf"\b(?:input|extern)\s+(?:double|float)\s+"
            rf"(?P<risk_name>{risk_percent_name})"
            rf"\s*=\s*{requested_risk_percent:g}(?:\.0+)?\b",
            code,
            flags=re.IGNORECASE,
        )
        source_risk_input_valid = bool(
            source_risk_match
            and _numeric_input_matches(
                code,
                source_risk_match.group("risk_name"),
                requested_risk_percent,
            )
        )
    tick_value_read = bool(re.search(
        r"\bMODE_TICKVALUE\b|\bSYMBOL_TRADE_TICK_VALUE(?:_LOSS|_PROFIT)?\b",
        reachable,
        flags=re.IGNORECASE,
    ))
    tick_size_read = bool(re.search(
        r"\bMODE_TICKSIZE\b|\bSYMBOL_TRADE_TICK_SIZE\b",
        reachable,
        flags=re.IGNORECASE,
    ))
    volume_step_read = bool(re.search(
        r"\bMODE_LOTSTEP\b|\bSYMBOL_VOLUME_STEP\b",
        reachable,
        flags=re.IGNORECASE,
    ))
    minimum_volume_read = bool(re.search(
        r"\bMODE_MINLOT\b|\bSYMBOL_VOLUME_MIN\b",
        reachable,
        flags=re.IGNORECASE,
    ))
    maximum_volume_read = bool(re.search(
        r"\bMODE_MAXLOT\b|\bSYMBOL_VOLUME_MAX\b",
        reachable,
        flags=re.IGNORECASE,
    ))
    margin_guard = bool(re.search(
        r"\b(?:AccountFreeMarginCheck|OrderCalcMargin|OrderCheck)\s*\(",
        reachable,
        flags=re.IGNORECASE,
    ))
    stop_distance_used = bool(re.search(
        r"\b(?:stop\w*(?:distance|loss)|sl\w*)\b",
        reachable,
        flags=re.IGNORECASE,
    ))
    floor_rounding = bool(re.search(r"\bMathFloor\s*\(", reachable, flags=re.IGNORECASE))
    safe_sizing_functions: set[str] = set()
    for function_name, bodies in (functions or {}).items():
        body = "\n".join(bodies)
        # Codex commonly formats compound fail-closed guards across multiple
        # physical lines.  Collapse only whitespace for guard recognition so
        # an otherwise identical safe guard is not rejected because of its
        # presentation.  Semicolons and all executable tokens remain intact,
        # which keeps the bounded fail-closed checks below conservative.
        guard_body = " ".join(body.split())
        zero_return_conditions = _mql_fail_closed_return_conditions(
            guard_body,
            allow_void_return=False,
            top_level_only=True,
        )

        def raw_broker_metric_bound(
            variable_pattern: str,
            mt4_constant: str,
            mt5_constant: str,
        ) -> bool:
            # The broker value must be assigned directly.  Token-presence with
            # arithmetic decoration (for example MODE_TICKVALUE*100 or
            # MODE_MAXLOT*1000) is not authoritative safety evidence.
            return bool(re.search(
                rf"\b(?:double|float)\s+(?:{variable_pattern})\w*\s*=(?!=)\s*(?:"
                rf"MarketInfo\s*\([^;]{{0,260}}\b{mt4_constant}\b[^;]{{0,120}}\)|"
                rf"SymbolInfoDouble\s*\([^;]{{0,260}}\b{mt5_constant}\b[^;]{{0,120}}\)"
                r")\s*;",
                body,
                flags=re.IGNORECASE,
            ))

        raw_tick_size_bound = raw_broker_metric_bound(
            r"tickSize",
            "MODE_TICKSIZE",
            "SYMBOL_TRADE_TICK_SIZE",
        )
        raw_tick_value_bound = raw_broker_metric_bound(
            r"tickValue",
            "MODE_TICKVALUE",
            "SYMBOL_TRADE_TICK_VALUE(?:_LOSS|_PROFIT)?",
        )
        raw_volume_step_bound = raw_broker_metric_bound(
            r"(?:volumeStep|lotStep)",
            "MODE_LOTSTEP",
            "SYMBOL_VOLUME_STEP",
        )
        raw_minimum_volume_bound = raw_broker_metric_bound(
            r"(?:minimumLot|minLot|minimumVolume|minVolume)",
            "MODE_MINLOT",
            "SYMBOL_VOLUME_MIN",
        )
        raw_maximum_volume_bound = raw_broker_metric_bound(
            r"(?:maximumLot|maxLot|maximumVolume|maxVolume)",
            "MODE_MAXLOT",
            "SYMBOL_VOLUME_MAX",
        )

        exact_risk_money_formula = False
        for risk_formula_match in re.finditer(
            r"\b(?:riskMoney|riskAmount)\w*\s*=(?!=)\s*([^;\r\n]+)",
            body,
            flags=re.IGNORECASE,
        ):
            formula = risk_formula_match.group(1)
            formula = re.sub(
                r"\bAccountEquity\s*\(\s*\)|"
                r"\bAccountInfoDouble\s*\(\s*ACCOUNT_EQUITY\s*\)",
                "E",
                formula,
                flags=re.IGNORECASE,
            )
            formula = re.sub(
                rf"\b{risk_percent_name}\b",
                "R",
                formula,
                flags=re.IGNORECASE,
            )
            compact_formula = re.sub(r"[\s()]", "", formula)
            if re.fullmatch(
                r"(?:E\*R|R\*E)/100(?:\.0+)?|"
                r"(?:E\*R|R\*E)\*0\.0*1|"
                r"(?:E|R)\*(?:R|E)/100(?:\.0+)?",
                compact_formula,
                flags=re.IGNORECASE,
            ):
                exact_risk_money_formula = True
                break

        def invalid_value_returns_zero(variable_pattern: str) -> bool:
            return any(
                "&&" not in condition
                and re.search(
                    rf"\b(?:{variable_pattern})\w*\b\s*(?:<=|==)\s*"
                    r"0(?:\.0+)?\b",
                    condition,
                    flags=re.IGNORECASE,
                )
                for condition in zero_return_conditions
            )

        margin_failure_returns_zero = any(
            "&&" not in condition
            and (
                re.search(
                    r"(?:AccountFreeMarginCheck|OrderCalcMargin|OrderCheck)\s*\("
                    r"[\s\S]{0,600}\)\s*(?:<=\s*0(?:\.0+)?\b|==\s*false\b)",
                    condition,
                    flags=re.IGNORECASE,
                )
                or re.search(
                    r"!\s*(?:OrderCalcMargin|OrderCheck)\s*\(",
                    condition,
                    flags=re.IGNORECASE,
                )
            )
            for condition in zero_return_conditions
        )
        return_dependencies: list[str] = []
        safe_return_roots: set[str] = set()
        for return_match in re.finditer(
            r"\breturn\s*(?P<value>[^;\r\n]{1,500})\s*;",
            body,
            flags=re.IGNORECASE,
        ):
            returned = return_match.group("value").strip()
            while returned.startswith("(") and returned.endswith(")"):
                returned = returned[1:-1].strip()
            if returned.casefold() in {"true", "false", "null"}:
                continue
            if re.fullmatch(r"[-+]?0(?:\.0+)?", returned):
                continue
            simple_root = re.fullmatch(r"[A-Za-z_]\w*", returned)
            if simple_root:
                safe_return_roots.add(simple_root.group(0))
            else:
                safe_return_roots.update(
                    identifier
                    for identifier in re.findall(r"\b[A-Za-z_]\w*\b", returned)
                    if identifier.casefold() not in {
                        "normalizedouble",
                        "mathfloor",
                        "mathmin",
                        "mathmax",
                    }
                )
            return_dependencies.append(_mql_expression_dependency_text(
                returned,
                body[: return_match.start()],
            ))

        def safe_return_path(dependency: str) -> bool:
            return bool(
                re.search(r"\bMathFloor\s*\(", dependency, re.IGNORECASE)
                and re.search(rf"\b{risk_percent_name}\b", dependency, re.IGNORECASE)
                and re.search(
                    r"\b(?:riskMoney|equity|balance)\w*\b.{0,160}/.{0,160}"
                    r"\b(?:lossPerLot|stop\w*distance|tickValue)\w*\b",
                    " ".join(dependency.split()),
                    re.IGNORECASE,
                )
                and re.search(
                    r"\b(?:volumeStep|lotStep)\w*\b",
                    dependency,
                    re.IGNORECASE,
                )
            )

        safe_return_dependency = (
            "\n".join(return_dependencies)
            if return_dependencies and all(safe_return_path(item) for item in return_dependencies)
            else ""
        )
        margin_volume_bound = False
        for margin_record in _mql_named_call_records(
            body,
            ("AccountFreeMarginCheck", "OrderCalcMargin", "OrderCheck"),
        ):
            arguments = [str(item) for item in margin_record.get("arguments", [])]
            margin_name = str(margin_record.get("name") or "").casefold()
            volume_index = 2 if margin_name in {
                "accountfreemargincheck",
                "ordercalcmargin",
            } else 0
            if len(arguments) <= volume_index:
                continue
            before_margin = body[: int(margin_record.get("start") or 0)]
            margin_volume_dependency = _mql_expression_dependency_text(
                arguments[volume_index],
                before_margin,
            )
            if any(
                re.search(
                    rf"\b{re.escape(root)}\b",
                    margin_volume_dependency,
                    flags=re.IGNORECASE,
                )
                for root in safe_return_roots
            ):
                margin_volume_bound = True
                break
        minimum_skip_guard = any(
            "&&" not in condition
            and re.search(
                r"\b(?:lot|volume)\w*\b\s*<\s*"
                r"\b(?:minimum|min)\w*(?:lot|volume)\w*\b",
                condition,
                flags=re.IGNORECASE,
            )
            for condition in zero_return_conditions
        )
        maximum_skip_guard = any(
            "&&" not in condition
            and re.search(
                r"\b(?:lot|volume)\w*\b\s*>\s*"
                r"\b(?:maximum|max)\w*(?:lot|volume)\w*\b",
                condition,
                flags=re.IGNORECASE,
            )
            for condition in zero_return_conditions
        )
        if (
            safe_return_dependency
            and
            re.search(
                r"\bAccountEquity\s*\(\s*\)|"
                r"\bAccountInfoDouble\s*\(\s*ACCOUNT_EQUITY\s*\)",
                body,
                flags=re.IGNORECASE,
            )
            and re.search(rf"\b{risk_percent_name}\b", body, flags=re.IGNORECASE)
            and exact_risk_money_formula
            and re.search(
                r"\bMODE_TICKVALUE\b|\bSYMBOL_TRADE_TICK_VALUE(?:_LOSS|_PROFIT)?\b",
                body,
                flags=re.IGNORECASE,
            )
            and re.search(r"\bMODE_TICKSIZE\b|\bSYMBOL_TRADE_TICK_SIZE\b", body, re.IGNORECASE)
            and re.search(r"\bMODE_LOTSTEP\b|\bSYMBOL_VOLUME_STEP\b", body, re.IGNORECASE)
            and re.search(r"\bMODE_MINLOT\b|\bSYMBOL_VOLUME_MIN\b", body, re.IGNORECASE)
            and re.search(r"\bMODE_MAXLOT\b|\bSYMBOL_VOLUME_MAX\b", body, re.IGNORECASE)
            and raw_tick_size_bound
            and raw_tick_value_bound
            and raw_volume_step_bound
            and raw_minimum_volume_bound
            and raw_maximum_volume_bound
            and re.search(r"\bMathFloor\s*\(", body, flags=re.IGNORECASE)
            and invalid_value_returns_zero(r"tickSize")
            and invalid_value_returns_zero(r"tickValue")
            and invalid_value_returns_zero(r"(?:volumeStep|lotStep)")
            and invalid_value_returns_zero(r"stop\w*distance")
            and invalid_value_returns_zero(r"lossPerLot")
            and invalid_value_returns_zero(r"(?:maximumLot|maxLot|maximumVolume|maxVolume)")
            and margin_failure_returns_zero
            and margin_volume_bound
            and minimum_skip_guard
            and maximum_skip_guard
            and not re.search(
                r"\bMathMax\s*\([^;\r\n]{0,120}\b(?:minimum|min)\w*(?:lot|volume)\w*\b|"
                r"\bMathMax\s*\(\s*\b(?:minimum|min)\w*(?:lot|volume)\w*\b",
                body,
                flags=re.IGNORECASE,
            )
        ):
            safe_sizing_functions.add(function_name)
    volume_dependencies = [
        str(item.get("volume") or "")
        for item in trade_argument_evidence
    ]
    risk_volume_binding_valid = bool(
        not risk_sizing_required
        or (
            volume_dependencies
            and all(
                any(
                    re.search(
                        rf"\b{re.escape(function_name)}\s*\(",
                        dependency,
                        flags=re.IGNORECASE,
                    )
                    for function_name in safe_sizing_functions
                )
                for dependency in volume_dependencies
            )
        )
    )

    def call_has_top_level_margin_guard(item: dict[str, object]) -> bool:
        dependency = str(item.get("volume") or "")
        volume_aliases: list[str] = []
        for line in dependency.splitlines():
            candidate = line.strip()
            if not re.fullmatch(r"[A-Za-z_]\w*", candidate):
                break
            volume_aliases.append(candidate)
        if not volume_aliases:
            return False
        before_call = reachable[: int(item.get("start") or 0)]
        conditions = _mql_fail_closed_return_conditions(
            before_call,
            allow_void_return=True,
            top_level_only=True,
        )
        for condition in conditions:
            if "&&" in condition:
                continue
            for margin_record in _mql_named_call_records(
                condition,
                ("AccountFreeMarginCheck", "OrderCalcMargin", "OrderCheck"),
            ):
                margin_name = str(margin_record.get("name") or "").casefold()
                arguments = [str(value) for value in margin_record.get("arguments", [])]
                volume_index = 2 if margin_name in {
                    "accountfreemargincheck",
                    "ordercalcmargin",
                } else 0
                if len(arguments) <= volume_index:
                    continue
                volume_argument = arguments[volume_index]
                if not any(
                    re.search(
                        rf"\b{re.escape(alias)}\b",
                        volume_argument,
                        flags=re.IGNORECASE,
                    )
                    for alias in volume_aliases
                ):
                    continue
                start = int(margin_record.get("start") or 0)
                end = int(margin_record.get("end") or 0)
                prefix = condition[max(0, start - 8):start]
                suffix = condition[end:end + 96]
                if (
                    re.search(r"!\s*$", prefix)
                    or re.match(
                        r"\s*(?:<=|<|==)\s*(?:0(?:\.0+)?|false)\b",
                        suffix,
                        flags=re.IGNORECASE,
                    )
                ):
                    return True
        return False

    margin_dominance_required = bool(
        IMPLEMENTATION_DEFAULT_RISK_SIZING.lower() in money_text
        or margin_guard
    )
    if risk_sizing_required:
        margin_guard_dominates_entry = bool(
            safe_sizing_functions and risk_volume_binding_valid
        )
    else:
        margin_guard_dominates_entry = bool(
            trade_argument_evidence
            and all(
                call_has_top_level_margin_guard(item)
                for item in trade_argument_evidence
            )
        )
    fixed_lot_binding_valid = True
    if requested_fixed_lot is not None:
        fixed_lot_binding_valid = bool(
            volume_dependencies
            and all(
                _fixed_lot_dependency_matches(
                    dependency,
                    code,
                    requested_fixed_lot,
                )
                for dependency in volume_dependencies
            )
        )
    checks["riskSizingExecution"] = bool(
        not risk_sizing_required
        or (
            equity_read
            and risk_percent_used
            and canonical_risk_inputs_valid
            and source_risk_input_valid
            and risk_volume_binding_valid
        )
    )
    checks["lotCalculationSafety"] = bool(
        not lot_calculation_required
        or (
            tick_value_read
            and tick_size_read
            and volume_step_read
        and minimum_volume_read
        and maximum_volume_read
        and margin_guard
            and stop_distance_used
            and floor_rounding
            and risk_volume_binding_valid
        )
    )
    requested_position_cap = _requested_position_cap(money_text)
    position_cap_required = requested_position_cap is not None
    counter_atom = (
        r"(?:(?P<count_fn>\b(?:count|get|open|managed|active)\w*"
        r"(?:position|order|trade)\w*)\s*\([^;\r\n]{0,120}\)|"
        r"(?P<builtin_count>\b(?:positions?|orders?)total)\s*\(\s*\)|"
        r"(?P<count_var>\b\w*(?:position|order|trade)\w*(?:count|total)\w*\b))"
    )
    cap_guard_match = None
    if requested_position_cap is not None:
        literal_threshold = (
            rf"(?:>=\s*{requested_position_cap}\b|"
            rf">\s*{requested_position_cap - 1}\b)"
        )
        # Do not let an outer optional wrapper satisfy the cap merely because
        # its regex span reaches a nested ``if(Count... >= cap)``.  Braces and
        # another ``if(`` terminate the direct condition scan.
        guard_prefix = (
            r"\bif\s*\((?:(?!\bif\s*\()[^;{}\r\n]){0,360}"
            + counter_atom
            + r"\s*"
        )
        guard_suffix = r"[^;\r\n]{0,160}\)\s*(?:\{\s*)?return\b"
        cap_guard_match = re.search(
            guard_prefix + literal_threshold + guard_suffix,
            reachable,
            flags=re.IGNORECASE,
        )
        if cap_guard_match is None:
            variable_match = re.search(
                guard_prefix
                + r">=\s*(?P<cap_var>[A-Za-z_]\w*)\b"
                + guard_suffix,
                reachable,
                flags=re.IGNORECASE,
            )
            if variable_match is not None:
                cap_var = variable_match.group("cap_var")
                declaration = re.search(
                    rf"\b(?:input|extern|const)?\s*(?:int|long)\s+"
                    rf"{re.escape(cap_var)}\s*=\s*{requested_position_cap}\b",
                    code,
                    flags=re.IGNORECASE,
                )
                if declaration is not None:
                    cap_guard_match = variable_match
    position_cap_guard = bool(
        cap_guard_match
        and first_open_trade_start >= 0
        and cap_guard_match.start() < first_open_trade_start
        and _mql_brace_depth_at(reachable, cap_guard_match.start()) == 0
        and cap_guard_match.start()
        not in _mql_unbraced_controlled_statement_starts(reachable)
        and "&&" not in cap_guard_match.group(0)
    )
    scoped_cap_required = "symbol+magic" in money_text
    counter_body = ""
    if cap_guard_match is not None and cap_guard_match.groupdict().get("count_fn"):
        count_function_name = str(cap_guard_match.group("count_fn") or "").lower()
        counter_body = "\n".join((functions or {}).get(count_function_name, []))
    scope_text = counter_body if counter_body else ""
    scoped_increment_match = re.search(
        r"\bif\s*\([^;\r\n]{0,500}(?:OrderSymbol\s*\(|POSITION_SYMBOL|Symbol\s*\(\s*\))"
        r"[^;\r\n]{0,500}(?:OrderMagicNumber\s*\(|POSITION_MAGIC|MagicNumber|magic\w*)"
        r"[^;\r\n]{0,240}\)\s*(?:\{[^{}]{0,500})?"
        r"\b(?:count|total|result|managed\w*)\w*\s*(?:\+\+|\+=\s*1\b)|"
        r"\bif\s*\([^;\r\n]{0,500}(?:OrderMagicNumber\s*\(|POSITION_MAGIC|MagicNumber|magic\w*)"
        r"[^;\r\n]{0,500}(?:OrderSymbol\s*\(|POSITION_SYMBOL|Symbol\s*\(\s*\))"
        r"[^;\r\n]{0,240}\)\s*(?:\{[^{}]{0,500})?"
        r"\b(?:count|total|result|managed\w*)\w*\s*(?:\+\+|\+=\s*1\b)",
        scope_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    scoped_increment = bool(scoped_increment_match)
    counter_bypass_return = bool(
        scoped_increment_match
        and re.search(
            r"\breturn\b",
            scope_text[:scoped_increment_match.start()],
            flags=re.IGNORECASE,
        )
    )
    scoped_cap_evidence = bool(
        scope_text
        and re.search(
            r"(?:OrderSymbol\s*\(|POSITION_SYMBOL|Symbol\s*\(\s*\))",
            scope_text,
            flags=re.IGNORECASE,
        )
        and re.search(
            r"(?:OrderMagicNumber\s*\(|POSITION_MAGIC|MagicNumber|magic\w*)",
            scope_text,
            flags=re.IGNORECASE,
        )
        and scoped_increment
        and not counter_bypass_return
        and re.search(
            r"\breturn\s*\(\s*(?:count|total|result|managed\w*)\w*\s*\)|"
            r"\breturn\s+(?:count|total|result|managed\w*)\w*\s*;",
            scope_text,
            flags=re.IGNORECASE,
        )
        and (
            re.search(r"\bOrdersTotal\s*\(", scope_text, flags=re.IGNORECASE)
            if platform == "mt4"
            else bool(
                re.search(r"\bPositionsTotal\s*\(", scope_text, flags=re.IGNORECASE)
                and re.search(r"\bOrdersTotal\s*\(", scope_text, flags=re.IGNORECASE)
            )
        )
    )
    specific_trade_mode_sets = [
        set(item.get("modes") or ()).intersection({
            "market_buy",
            "market_sell",
            "buy_stop",
            "sell_stop",
            "buy_limit",
            "sell_limit",
        })
        for item in trade_argument_evidence
    ]
    repeated_same_mode_call = any(
        bool(left.intersection(right))
        for index, left in enumerate(specific_trade_mode_sets)
        for right in specific_trade_mode_sets[index + 1:]
    )
    repeated_entry_loop = bool(re.search(
        r"\b(?:for|while)\s*\([^;{}\r\n]{0,500}(?:;[^;{}\r\n]{0,500};"
        r"[^){}\r\n]{0,500})?\)\s*(?:\{[^{}]{0,1600})?"
        r"\b(?:OrderSend|PositionOpen|Buy|Sell|BuyStop|SellStop|BuyLimit|SellLimit)\s*\(|"
        r"\bdo\s*\{[^{}]{0,1600}"
        r"\b(?:OrderSend|PositionOpen|Buy|Sell|BuyStop|SellStop|BuyLimit|SellLimit)\s*\(",
        reachable,
        flags=re.IGNORECASE | re.DOTALL,
    ))
    per_call_cap_safe = bool(
        not repeated_same_mode_call
        and not repeated_entry_loop
        and isinstance(functions, dict)
        and _compact_ea_trade_invocation_multiplicity_safe(functions)
    )
    checks["positionCapExecution"] = bool(
        not position_cap_required
        or (
            position_cap_guard
            and per_call_cap_safe
            and (not scoped_cap_required or scoped_cap_evidence)
        )
    )
    checks["moneyManagementExecution"] = bool(
        base_money_management_execution
        and checks["riskSizingExecution"]
        and checks["lotCalculationSafety"]
        and checks["positionCapExecution"]
        and fixed_lot_binding_valid
        and canonical_fixed_lot_input_valid
        and (
            not margin_dominance_required
            or margin_guard_dominates_entry
        )
    )
    if not checks["riskSizingExecution"]:
        findings.append("ea_risk_percent_equity_path_missing")
    if not checks["lotCalculationSafety"]:
        findings.append("ea_lot_calculation_safety_missing")
    if not checks["positionCapExecution"]:
        findings.append("ea_position_cap_guard_missing")
    if margin_dominance_required and not margin_guard_dominates_entry:
        findings.append("ea_margin_guard_not_fail_closed")
    if not checks["moneyManagementExecution"]:
        findings.append("ea_money_management_path_missing")

    order_text = order_execution_text
    direction_text = " ".join((content["entryRules"], source_order_execution))
    long_only = bool(re.search(
        r"\blong[ -]?only\b|\bbuy[ -]?only\b|\bnever\s+(?:sell|short)\b|"
        r"\b(?:do\s+not|should\s+not|must\s+not)\s+(?:open\s+)?(?:sell|short)\b|"
        r"ซื้ออย่างเดียว|buy\s*อย่างเดียว|ไม่(?:ควร\s*)?(?:เปิด|ใช้)\s*sell|ห้าม\s*sell",
        direction_text,
        flags=re.IGNORECASE,
    ))
    short_only = bool(re.search(
        r"\bshort[ -]?only\b|\bsell[ -]?only\b|\bnever\s+(?:buy|long)\b|"
        r"\b(?:do\s+not|should\s+not|must\s+not)\s+(?:open\s+)?(?:buy|long)\b|"
        r"ขายอย่างเดียว|sell\s*อย่างเดียว|ไม่(?:ควร\s*)?(?:เปิด|ใช้)\s*buy|ห้าม\s*buy",
        direction_text,
        flags=re.IGNORECASE,
    ))
    if IMPLEMENTATION_DEFAULT_ORDER_EXECUTION.lower() in order_text.lower():
        source_buy = _component_enabled_requested(direction_text, (r"\bbuy\b", r"\blong\b", r"ซื้อ"))
        source_sell = _component_enabled_requested(direction_text, (r"\bsell\b", r"\bshort\b", r"ขาย"))
        if long_only and not short_only:
            required_order_modes = {"market_buy"}
        elif short_only and not long_only:
            required_order_modes = {"market_sell"}
        elif source_buy and not source_sell:
            required_order_modes = {"market_buy"}
        elif source_sell and not source_buy:
            required_order_modes = {"market_sell"}
        else:
            required_order_modes = {"market_buy", "market_sell"}
    else:
        required_order_modes: set[str] = set()
        source_order_text = re.sub(r"\[[^\]\r\n]{0,240}\]", " ", order_text)
        explicit_variants = (
            ("market_buy", (r"\bmarket\s+buy\b", r"\bbuy\s+at\s+market\b")),
            ("market_sell", (r"\bmarket\s+sell\b", r"\bsell\s+at\s+market\b")),
            ("buy_stop", (r"\bbuy[ -]?stop\b",)),
            ("sell_stop", (r"\bsell[ -]?stop\b",)),
            ("buy_limit", (r"\bbuy[ -]?limit\b",)),
            ("sell_limit", (r"\bsell[ -]?limit\b",)),
        )
        for mode, aliases in explicit_variants:
            if _component_enabled_requested(order_text, aliases):
                required_order_modes.add(mode)
        if re.search(
            r"\bbuy\s*(?:/|and|&)\s*sell\s+stops?\b|"
            r"\bsell\s*(?:/|and|&)\s*buy\s+stops?\b",
            source_order_text,
            flags=re.IGNORECASE,
        ):
            required_order_modes.update(("buy_stop", "sell_stop"))
        if re.search(
            r"\bbuy\s*(?:/|and|&)\s*sell\s+limits?\b|"
            r"\bsell\s*(?:/|and|&)\s*buy\s+limits?\b",
            source_order_text,
            flags=re.IGNORECASE,
        ):
            required_order_modes.update(("buy_limit", "sell_limit"))
        if _component_enabled_requested(
            order_text,
            (
                r"\bstop[ _-]?entry\b",
                r"\bpending\s+stop\s+entr(?:y|ies)\b",
                r"\b(?:pending\s+)?stop\s+orders?\b",
            ),
        ):
            required_order_modes.add("stop_entry")
        if _component_enabled_requested(
            order_text,
            (
                r"\blimit[ _-]?entry\b",
                r"\bpending\s+limit\s+entr(?:y|ies)\b",
                r"\b(?:pending\s+)?limit\s+orders?\b",
            ),
        ):
            required_order_modes.add("limit_entry")
        market_pair = bool(re.search(
            r"\bmarket\s+buy\b.{0,24}\b(?:market\s+)?sell\b|"
            r"\bmarket\s+sell\b.{0,24}\b(?:market\s+)?buy\b",
            source_order_text,
            flags=re.IGNORECASE,
        ))
        if market_pair:
            required_order_modes.update(("market_buy", "market_sell"))
        if (
            _component_enabled_requested(order_text, _MARKET_ORDER_ALIASES)
            and not any(mode.startswith("market_") for mode in required_order_modes)
        ):
            required_order_modes.add("market")
        if (
            _component_enabled_requested(order_text, _PENDING_ORDER_ALIASES)
            and not any(
                mode in {"buy_stop", "sell_stop", "buy_limit", "sell_limit"}
                for mode in required_order_modes
            )
            and not {"stop_entry", "limit_entry"}.intersection(required_order_modes)
        ):
            required_order_modes.add("pending")
        if not required_order_modes:
            required_order_modes = {"market_buy", "market_sell"}
    specific_order_modes = {
        "market_buy",
        "market_sell",
        "buy_stop",
        "sell_stop",
        "buy_limit",
        "sell_limit",
    }
    allowed_specific_order_modes = {
        mode for mode in required_order_modes if mode in specific_order_modes
    }
    prohibited_specific_order_modes: set[str] = set()
    if long_only and not short_only:
        prohibited_specific_order_modes.update(("market_sell", "sell_stop", "sell_limit"))
    elif short_only and not long_only:
        prohibited_specific_order_modes.update(("market_buy", "buy_stop", "buy_limit"))
    if "market" in required_order_modes:
        if long_only and not short_only:
            allowed_specific_order_modes.add("market_buy")
        elif short_only and not long_only:
            allowed_specific_order_modes.add("market_sell")
        else:
            allowed_specific_order_modes.update(("market_buy", "market_sell"))
    if "pending" in required_order_modes:
        if long_only and not short_only:
            allowed_specific_order_modes.update(("buy_stop", "buy_limit"))
        elif short_only and not long_only:
            allowed_specific_order_modes.update(("sell_stop", "sell_limit"))
        else:
            allowed_specific_order_modes.update(
                ("buy_stop", "sell_stop", "buy_limit", "sell_limit")
            )
    if "stop_entry" in required_order_modes:
        if long_only and not short_only:
            allowed_specific_order_modes.add("buy_stop")
        elif short_only and not long_only:
            allowed_specific_order_modes.add("sell_stop")
        else:
            allowed_specific_order_modes.update(("buy_stop", "sell_stop"))
    if "limit_entry" in required_order_modes:
        if long_only and not short_only:
            allowed_specific_order_modes.add("buy_limit")
        elif short_only and not long_only:
            allowed_specific_order_modes.add("sell_limit")
        else:
            allowed_specific_order_modes.update(("buy_limit", "sell_limit"))
    allowed_specific_order_modes.difference_update(prohibited_specific_order_modes)
    direction_requirement_conflict = bool(
        required_order_modes.intersection(prohibited_specific_order_modes)
    )
    entry_signal_names: set[str] = set()
    for signal_pattern in (
        r"\b([A-Za-z_]\w*)\s*(?:==|!=)\s*SIGNAL_NONE\b",
        r"\bSIGNAL_NONE\s*(?:==|!=)\s*([A-Za-z_]\w*)\b",
    ):
        entry_signal_names.update(re.findall(
            signal_pattern,
            entry_path_code,
            flags=re.IGNORECASE,
        ))
    prohibited_signal_tokens = ""
    if long_only and not short_only:
        prohibited_signal_tokens = r"(?:OP_SELL|ORDER_TYPE_SELL)"
    elif short_only and not long_only:
        prohibited_signal_tokens = r"(?:OP_BUY|ORDER_TYPE_BUY)"
    prohibited_entry_signal_assignment = bool(
        prohibited_signal_tokens
        and any(
            re.search(
                rf"\b{re.escape(signal_name)}\b\s*=(?!=)\s*{prohibited_signal_tokens}\b",
                entry_path_code,
                flags=re.IGNORECASE,
            )
            for signal_name in entry_signal_names
        )
    )
    unexpected_specific_order_modes = (
        implemented_order_modes.intersection(specific_order_modes)
        - allowed_specific_order_modes
    )
    checks["orderExecution"] = bool(
        open_trade
        and required_order_modes.issubset(implemented_order_modes)
        and not unexpected_specific_order_modes
        and not (long_only and short_only)
        and not direction_requirement_conflict
        and not prohibited_entry_signal_assignment
        and spread_guard_valid
        and _pending_price_semantics_valid(
            order_text,
            trade_argument_evidence,
            code,
        )
    )
    if not checks["orderExecution"]:
        findings.append("ea_order_execution_mode_missing")

    recovery_modes = {
        "grid": r"\bgrid\w*\b",
        "martingale": r"\bmartingale\w*\b",
        "averaging": r"\baverag\w*\b",
        "hedging": r"\bhedg\w*\b",
    }
    recovery_prohibited = bool(
        IMPLEMENTATION_DEFAULT_RECOVERY_RULES.lower() in recovery_text
        or _recovery_explicit_none(recovery_text)
    )
    implemented_modes = {
        name
        for name, pattern in recovery_modes.items()
        if _component_enabled_requested(reachable, (pattern,))
    }
    required_modes = {
        name
        for name, pattern in recovery_modes.items()
        if _component_enabled_requested(recovery_text, (pattern,))
    }
    generic_recovery_requested = _component_enabled_requested(
        recovery_text,
        (
            r"(?:add|open)\s+(?:another|additional|new)\s+(?:position|order|trade)",
            r"scale[ _-]?in",
            r"เพิ่มไม้|แก้ไม้|ถัวเฉลี่ย",
        ),
    )
    recovery_trigger_implemented = bool(re.search(
        r"\b(?:OrderProfit|HistoryOrderGetDouble|PositionGetDouble)\s*\(|"
        r"\b(?:POSITION_PROFIT|DEAL_PROFIT)\b|"
        r"\b(?:drawdown\w*|lossCount\w*|lossStreak\w*|consecutiveLoss\w*|lastLoss\w*)\b|"
        r"ขาดทุน|ดรอดาวน์",
        reachable,
        flags=re.IGNORECASE,
    ))
    recovery_inventory_implemented = bool(re.search(
        r"\b(?:OrdersTotal|PositionsTotal)\s*\(",
        reachable,
        flags=re.IGNORECASE,
    ))
    recovery_additional_entry_implemented = False
    for trade_record in trade_calls:
        trade_start = int(trade_record.get("start") or 0)
        nearby = reachable[max(0, trade_start - 1600):trade_start]
        if re.search(
            r"\bif\s*\([^);\r\n]{0,320}(?:loss|drawdown|adverse|"
            r"grid\w*step|spacing|profit\w*\s*<\s*0)"
            r"[^);\r\n]{0,240}\)[\s\S]{0,900}$",
            nearby,
            flags=re.IGNORECASE,
        ):
            recovery_additional_entry_implemented = True
            break
    loss_based_lot_escalation = bool(re.search(
        r"\bif\s*\([^);\r\n]{0,240}(?:lossCount|lossStreak|consecutiveLoss|"
        r"lastLoss|drawdown|profit\w*\s*<\s*0)"
        r"[^);\r\n]{0,160}\)(?:(?!\bif\s*\()[\s\S]){0,300}"
        r"\b(?:lot|volume)\w*\b\s*"
        r"(?:\*=\s*(?:[1-9]\d*|\d+\.\d*[1-9])|=\s*[^;\r\n]{0,80}\*)",
        reachable,
        flags=re.IGNORECASE | re.DOTALL,
    ))
    outcome_helper_names = {
        function_name
        for function_name, bodies in (functions or {}).items()
        if re.search(
            r"\b(?:OrderProfit|OrderSwap|OrderCommission|HistoryOrderGetDouble|"
            r"HistoryDealGetDouble|PositionGetDouble)\s*\(|"
            r"\b(?:POSITION_PROFIT|DEAL_PROFIT)\b",
            "\n".join(bodies),
            flags=re.IGNORECASE,
        )
    }
    helper_outcome_condition = (
        r"(?:"
        + "|".join(re.escape(name) for name in sorted(outcome_helper_names))
        + r")\s*\("
        if outcome_helper_names
        else r"(?!)"
    )
    helper_based_lot_escalation = bool(re.search(
        rf"\bif\s*\([^;\r\n]{{0,300}}{helper_outcome_condition}"
        r"[^;\r\n]{0,200}\)\s*(?:\{\s*)?[^{};\r\n]{0,240}"
        r"\b(?:lot|volume)\w*\b\s*"
        r"(?:\*=\s*(?:[1-9]\d*|\d+\.\d*[1-9])|=\s*[^;\r\n]{0,80}\*)",
        reachable,
        flags=re.IGNORECASE,
    ))
    helper_based_additional_entry = False
    if outcome_helper_names:
        for trade_record in trade_calls:
            trade_start = int(trade_record.get("start") or 0)
            nearby = reachable[max(0, trade_start - 1200):trade_start]
            if re.search(
                rf"\bif\s*\([^;\r\n]{{0,300}}{helper_outcome_condition}"
                r"[^;\r\n]{0,200}\)[\s\S]{0,700}$",
                nearby,
                flags=re.IGNORECASE,
            ):
                helper_based_additional_entry = True
                break
    recovery_runtime_evidence = bool(
        recovery_trigger_implemented
        and recovery_inventory_implemented
        and (
            recovery_additional_entry_implemented
            or loss_based_lot_escalation
            or helper_based_lot_escalation
            or helper_based_additional_entry
        )
    )
    recovery_price_dependencies = "\n".join(
        str(item.get("price") or "")
        for item in trade_argument_evidence[1:]
    )
    recovery_volume_dependencies = "\n".join(
        str(item.get("volume") or "")
        for item in trade_argument_evidence[1:]
    )
    recovery_spacing_implemented = bool(re.search(
        r"(?:spacing|distance|step|grid\w*step|atr|pip|point).{0,120}"
        r"(?:OrderOpenPrice|POSITION_PRICE_OPEN|entry\w*|price)|"
        r"(?:OrderOpenPrice|POSITION_PRICE_OPEN|entry\w*|price).{0,120}"
        r"(?:spacing|distance|step|grid\w*step|atr|pip|point)",
        recovery_price_dependencies or reachable,
        flags=re.IGNORECASE,
    ))
    same_lot_requested = bool(re.search(
        r"\b(?:same|fixed|equal)\s+(?:lot|volume)\b|ล็อต(?:เดิม|เท่าเดิม|คงที่)",
        recovery_text,
        flags=re.IGNORECASE,
    ))
    recovery_lot_rule_implemented = bool(
        re.search(
            r"\b(?:lot|volume)\w*\b.{0,80}(?:\*|MathPow\s*\()|"
            r"(?:\*|MathPow\s*\().{0,80}\b(?:lot|volume)\w*\b|"
            r"\b(?:OrderLots|PositionGetDouble)\s*\(",
            recovery_volume_dependencies,
            flags=re.IGNORECASE,
        )
        or (
            same_lot_requested
            and re.search(
                r"\b(?:base|initial|fixed|same)?\w*(?:lot|volume)\w*\b",
                recovery_volume_dependencies,
                flags=re.IGNORECASE,
            )
        )
    )
    recovery_level_cap_implemented = bool(re.search(
        r"\b(?:level|order|position|trade)\w*(?:count|total|level)?\w*\b"
        r"\s*(?:<|<=|>=|>)\s*(?:\d+|Max\w+)|"
        r"\b(?:OrdersTotal|PositionsTotal)\s*\(\s*\)\s*(?:<|<=)\s*(?:\d+|Max\w+)",
        reachable,
        flags=re.IGNORECASE,
    ))
    recovery_basket_exit_implemented = bool(
        close_calls
        and re.search(
            r"\b(?:basket|total|aggregate|combined)\w*(?:profit|loss|pnl)?\w*\b|"
            r"(?:profit|loss|pnl).{0,48}(?:target|limit)",
            reachable,
            flags=re.IGNORECASE,
        )
    )
    recovery_reset_implemented = bool(re.search(
        r"\b(?:recovery|grid|martingale|loss|level|step|basket)\w*"
        r"(?:count|level|state|index|streak)?\w*\s*=\s*0\b|"
        r"\b(?:reset|abort)\w*\s*\(",
        reachable,
        flags=re.IGNORECASE,
    ))
    recovery_detail_runtime = bool(
        recovery_spacing_implemented
        and recovery_lot_rule_implemented
        and recovery_level_cap_implemented
        and recovery_basket_exit_implemented
        and recovery_reset_implemented
    )
    if not recovery_runtime_evidence:
        implemented_modes = set()
    checks["recoveryPolicy"] = bool(
        not implemented_modes
        and not recovery_runtime_evidence
        and not repeated_entry_loop
        and not repeated_same_mode_call
        if recovery_prohibited
        else (
            required_modes.issubset(implemented_modes)
            and recovery_runtime_evidence
            and recovery_detail_runtime
        )
        if required_modes or generic_recovery_requested
        else True
    )
    if not checks["recoveryPolicy"]:
        findings.append("ea_recovery_policy_mismatch")

    display_evidence = _mql_reachable_display_evidence(
        source_text,
        code,
        reachable,
    )
    display_findings = _compact_display_requirement_findings(
        brief.get("displayRequirements") if isinstance(brief, dict) else "",
        brief.get("systemName") if isinstance(brief, dict) else "",
        display_evidence,
    )
    checks["displayBehavior"] = not display_findings
    findings.extend(display_findings)

    findings = list(dict.fromkeys(findings))
    field_checks = {
        "record_id": checks["strategyBriefContract"] and checks["strategyBriefDigestBound"],
        "system_name": checks["strategyBriefContract"] and checks["strategyBriefDigestBound"],
        "system_overview": checks["strategyBriefContract"] and checks["expertAdvisorLifecycle"],
        "entry_rules": checks["entryExecution"] and checks["closedBarExecution"],
        "recovery_rules": checks["recoveryPolicy"],
        "exit_rules": checks["exitAndProtectionExecution"],
        "money_management": checks["moneyManagementExecution"],
        "order_execution": checks["orderExecution"],
        "display_requirements": checks["displayBehavior"],
        "additional_notes": checks["strategyBriefContract"] and checks["strategyBriefDigestBound"],
    }
    return {
        "checks": checks,
        "findings": findings,
        "coveredFields": [field for field in COMPACT_SHEET_FIELDS if field_checks[field]],
        "missingFields": [field for field in COMPACT_SHEET_FIELDS if not field_checks[field]],
        "complete": not findings and all(checks.values()),
    }


def build_compact_ea_source_manifest(
    source_text: object,
    *,
    strategy_brief: object,
    strategy_brief_digest: object,
    strategy_spec_digest: object,
    source_digest: object,
    target_platform: object,
) -> dict:
    brief_digest = str(strategy_brief_digest or "").strip().lower()
    spec_digest = str(strategy_spec_digest or "").strip().lower()
    actual_source_digest = str(source_digest or "").strip().lower()
    platform = str(target_platform or "").strip().lower()
    analysis = analyze_compact_ea_source(
        source_text,
        strategy_brief=strategy_brief,
        strategy_brief_digest=brief_digest,
        strategy_spec_digest=spec_digest,
        source_digest=actual_source_digest,
        target_platform=platform,
    )
    result = {
        "schemaVersion": EA_SOURCE_MANIFEST_SCHEMA_VERSION,
        "coverageMode": "compact_brief_digest_bound_structural_ea_review",
        "artifactKind": "expert_advisor",
        "targetPlatform": platform,
        "strategyBriefDigest": brief_digest,
        "strategySpecDigest": spec_digest,
        "sourceDigest": actual_source_digest,
        "checks": analysis["checks"],
        "coveredFields": analysis["coveredFields"],
        "missingFields": analysis["missingFields"],
        "findings": analysis["findings"],
        "complete": analysis["complete"],
    }
    encoded = json.dumps(
        result,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    result["manifestDigest"] = hashlib.sha256(encoded).hexdigest()
    return result


__all__ = [
    "SCHEMA_VERSION",
    "COMPACT_SHEET_FIELDS",
    "CONTENT_FIELDS",
    "EA_SOURCE_MANIFEST_SCHEMA_VERSION",
    "INDICATOR_SOURCE_MANIFEST_SCHEMA_VERSION",
    "LINDA_HOLY_GRAIL_CERTIFIED_BRIEF_DIGEST",
    "LINDA_HOLY_GRAIL_CERTIFIED_PROFILE_VERSION",
    "LINDA_HOLY_GRAIL_DIRECTION_COMPONENT",
    "LINDA_HOLY_GRAIL_DIRECTION_RULE",
    "LINDA_HOLY_GRAIL_LEGACY_BRIEF_DIGEST",
    "StrategyBriefValidationError",
    "analyze_compact_ea_source",
    "analyze_compact_indicator_source",
    "build_compact_ea_source_manifest",
    "build_compact_indicator_source_manifest",
    "normalize_strategy_brief",
    "compute_strategy_brief_digest",
    "linda_holy_grail_certified_profile_metadata",
    "project_strategy_brief_contract",
    "upgrade_linda_holy_grail_brief_for_certified_profile",
]
