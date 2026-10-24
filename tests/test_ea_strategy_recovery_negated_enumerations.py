"""Recovery-list negation must neither invent modes nor hide positive rules."""
from __future__ import annotations

import hashlib
import unittest

import test_ea_strategy_brief as support
import test_ea_factory_mt5_generation_architecture as architecture


BRIEF = support.BRIEF
MODES = ("grid", "martingale", "averaging", "hedging")
NEGATIVE_LIST = "No grid, martingale, averaging, pyramiding, recovery, hedging or pending orders."
CONDITIONAL_DEFAULT = (
    "Follow only recovery rules explicitly written by the operator. "
    "If none are specified, recovery, grid, martingale, averaging and pyramiding are disabled. "
)
# The exact operator prose that exposed the bug, kept portable without a live
# Runtime dependency. It is specification data, not an instruction to this test.
OPERATOR_REQUIREMENTS = (
    "Create a new MQL5 Expert Advisor for Strategy Tester only. Use EMA 10 and EMA 60, MODE_EMA, PRICE_CLOSE on the chart symbol and timeframe. "
    "Evaluate once per new bar, using only completed bars 2 and 1. BUY when fast EMA at bar 2 <= slow EMA at bar 2 and fast EMA at bar 1 > slow EMA at bar 1. "
    "SELL when fast EMA at bar 2 >= slow EMA at bar 2 and fast EMA at bar 1 < slow EMA at bar 1. Use iMA handles and CopyBuffer correctly; do not trade until data is ready. "
    "Expose positive adjustable Inputs StopLossPips=30.0 and TakeProfitPips=60.0. Convert pips correctly for 3/5-digit symbols and normalize broker price, tick size, stop distance and volume. "
    "Use fixed lot 0.01 and at most one position for this symbol and magic number. On a confirmed opposite crossover, close only this EA position; open the reverse only after closure succeeds. "
    "Reject invalid orders safely. " + NEGATIVE_LIST + " Show EMA values, confirmed BUY/SELL signals, executed entries, rejected requests and latest result for visual checking. "
    "Refuse execution outside Strategy Tester. Compile, run one Visual Backtest, verify actual entries, save the real Report and finish. No Optimization, live trading or deployment."
)
EXACT_RECOVERY_RULES = CONDITIONAL_DEFAULT + "Operator requirements: " + OPERATOR_REQUIREMENTS


def required_modes(text):
    return {mode for mode in MODES if BRIEF._component_enabled_requested(text, (rf"\b{mode}\b",))}


class RecoveryEnumerationParsingTests(unittest.TestCase):
    def test_exact_repeated_custom_prose_does_not_require_forbidden_modes(self):
        for text in (EXACT_RECOVERY_RULES, EXACT_RECOVERY_RULES + "\n" + EXACT_RECOVERY_RULES):
            self.assertEqual(required_modes(text), set())
            self.assertTrue(BRIEF._recovery_explicit_none(text))

    def test_prefix_and_suffix_lists_keep_negation_for_each_name(self):
        for text in (
            NEGATIVE_LIST,
            "No automatic recovery, grid, martingale, averaging, or hedging.",
            "Without grid, martingale, averaging or hedging.",
            "Do not use grid, martingale, averaging and hedging.",
            "Grid, martingale, averaging and hedging are disabled.",
            "ไม่เปิด Grid, Martingale, Averaging และ Hedging.",
        ):
            with self.subTest(text=text):
                self.assertEqual(required_modes(text), set())
                self.assertTrue(BRIEF._recovery_explicit_none(text))

    def test_conditional_default_does_not_override_explicit_positive(self):
        self.assertFalse(BRIEF._recovery_explicit_none(CONDITIONAL_DEFAULT))
        self.assertEqual(required_modes(CONDITIONAL_DEFAULT), set())
        for mode in MODES:
            text = CONDITIONAL_DEFAULT + f"Operator requirements: Use {mode} after 2 losses."
            self.assertEqual(required_modes(text), {mode})
            self.assertFalse(BRIEF._recovery_explicit_none(text))

    def test_positive_and_mixed_requirements_survive_normalization(self):
        self.assertEqual(required_modes("Use grid, martingale, averaging and hedging."), set(MODES))
        self.assertEqual(required_modes("No grid, martingale, but use hedging after 2 losses."), {"hedging"})
        self.assertEqual(required_modes("No grid, martingale. Use averaging after drawdown."), {"averaging"})

    def test_numeric_assignment_and_conditional_tails_are_not_erased(self):
        for text, mode in (
            ("No grid, martingale at 2 losses.", "martingale"),
            ("No grid, martingale=true.", "martingale"),
            ("No grid, martingale, averaging, hedging until the third loss.", "hedging"),
            ("Grid, martingale and hedging are disabled unless loss reaches 3.", "grid"),
        ):
            self.assertIn(mode, required_modes(text), text)

    def test_missing_evidence_is_not_an_operator_prohibition(self):
        for text in ("No recovery rules were found.", "No documented recovery strategy."):
            self.assertFalse(BRIEF._recovery_explicit_none(text))

    def test_existing_implementation_default_does_not_create_positive_modes(self):
        self.assertEqual(required_modes(BRIEF.IMPLEMENTATION_DEFAULT_RECOVERY_RULES), set())
        self.assertTrue(BRIEF._recovery_explicit_none(BRIEF.IMPLEMENTATION_DEFAULT_RECOVERY_RULES))
        for text in (BRIEF.IMPLEMENTATION_DEFAULT_RECOVERY_RULES, "RecoveryMode=none, ไม่เพิ่มไม้แก้, ไม่ถัวเฉลี่ย และไม่เปิดคำสั่ง recovery หลังขาดทุน"):
            self.assertFalse(BRIEF._component_enabled_requested(text, (r"เพิ่มไม้|แก้ไม้|ถัวเฉลี่ย",)))

    def test_legacy_thai_missing_evidence_and_slash_lists_remain_nonaffirmative(self):
        for text in (
            "แหล่งข้อมูลไม่พบกฎ Recovery, Grid, Martingale, Averaging หรือ Hedging ที่มี trigger, spacing, lot rule, level cap, basket exit และ reset/abort ครบถ้วน ดังนั้น RecoveryMode=none, ไม่เพิ่มไม้แก้, ไม่ถัวเฉลี่ย, ไม่ Martingale, ไม่ Grid, ไม่ Hedging และไม่เปิดคำสั่ง recovery หลังขาดทุน",
            "แหล่งข้อมูลทั้งสองไม่ได้ระบุระบบ recovery ที่ครบองค์ประกอบ เช่น trigger, spacing, lot rule, level cap, basket exit และ reset/abort rules และไม่ได้ระบุว่าใช้ Grid, Martingale, Averaging หรือ Hedging ดังนั้นไม่ควรสร้าง recovery เพิ่มเอง ให้ตั้ง RecoveryMode=none, ไม่เปิด Grid/Martingale/Averaging/Hedging, ไม่มีการเพิ่ม lot หลังขาดทุน, ไม่มี basket recovery และ reset สถานะ recovery เป็น none หลัง position ปิดตาม SL/TP",
            "RecoveryMode=none, ไม่เพิ่มไม้แก้ ไม่ถัวเฉลี่ย ไม่ Martingale, Grid หรือ Hedging",
            "แหล่งข้อมูลไม่ได้ระบุ recovery แบบ Grid, Martingale, Averaging หรือ Hedging และ record ระบุ RecoveryMethod=none จึงคง RecoveryMode=none เป็นข้อเท็จจริงเชิงระบบ ไม่มีการเพิ่มไม้แก้ ไม่มีการเพิ่ม lot หลังขาดทุน และไม่มี basket exit",
        ):
            self.assertEqual(required_modes(text), set())
            self.assertTrue(BRIEF._recovery_explicit_none(text))
            self.assertEqual(required_modes(text + "; Use grid after two losses."), {"grid"})


class RecoveryEnumerationSourceGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        architecture.EaFactoryMt5GenerationArchitectureTests.setUpClass()

    def setUp(self):
        self.fixture = architecture.EaFactoryMt5GenerationArchitectureTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def analyze(self, recovery_rules, *, unsafe=False):
        brief, old_digest, source = self.fixture.example()
        brief["recoveryRules"] = recovery_rules
        digest = BRIEF.compute_strategy_brief_digest(brief)
        source = source.replace(old_digest, digest)
        if unsafe:
            source = source.replace(
                "if(!OrderSend(openingRequest, openingResult))",
                "for(int recoveryLevel=0; recoveryLevel<3; recoveryLevel++) OrderSend(openingRequest, openingResult);\n  if(!OrderSend(openingRequest, openingResult))",
            )
        return BRIEF.analyze_compact_ea_source(
            source, strategy_brief=brief, strategy_brief_digest=digest,
            strategy_spec_digest="1" * 64,
            source_digest=hashlib.sha256(source.encode()).hexdigest(), target_platform="mt5",
        )

    def test_ordinary_source_passes_exact_custom_recovery_prose(self):
        result = self.analyze(EXACT_RECOVERY_RULES)
        self.assertTrue(result["complete"], result["findings"])

    def test_unrequested_repeated_entry_stays_rejected(self):
        result = self.analyze(EXACT_RECOVERY_RULES, unsafe=True)
        self.assertFalse(result["complete"])
        self.assertIn("ea_recovery_policy_mismatch", result["findings"])

    def test_conflicting_or_positive_recovery_cannot_accept_plain_ema(self):
        for text in (
            NEGATIVE_LIST + " Use martingale after 2 losses.",
            CONDITIONAL_DEFAULT + "Use grid after a loss; spacing 100 points; same lot; max 3 levels; basket TP 50 points; reset after basket close.",
            "No grid, martingale, averaging, hedging until the third loss.",
        ):
            with self.subTest(text=text):
                result = self.analyze(text)
                self.assertFalse(result["complete"])
                self.assertIn("ea_recovery_policy_mismatch", result["findings"])


if __name__ == "__main__":
    unittest.main()
