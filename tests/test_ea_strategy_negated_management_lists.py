"""Negated lists must not create contradictory required exit features."""
import importlib.util
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1]/'backend/local-runner/hq_backend/ea/ea_strategy_brief.py'
spec = importlib.util.spec_from_file_location('negated_management_brief',PATH)
brief = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brief)


class NegatedManagementListsTests(unittest.TestCase):
    def test_thai_immutable_elder_exit_list_is_not_a_positive_request(self):
        text = ('แหล่งข้อมูลไม่ได้ระบุ Take Profit เป็นตัวเลข และไม่ได้ระบุ trailing exit, '
                'break-even หรือ partial close หลังเข้า position '
                '[IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT][COMPONENT=exitRules] '
                'สำหรับส่วน TP ที่ขาด ให้ใช้ TakeProfitPoints=600; '
                'Trailing=false, BreakEven=false และ PartialClose=false เว้นแต่ผู้ใช้เพิ่มกฎใหม่หลังทดสอบ')
        for aliases in (brief._TRAILING_STOP_ALIASES,brief._BREAK_EVEN_ALIASES,brief._PARTIAL_CLOSE_ALIASES):
            self.assertFalse(brief._component_enabled_requested(text,aliases))

    def test_english_list_preserves_negation_across_comma_and_or(self):
        for text in ('Source does not specify trailing stop, break-even or partial close.',
                     'Sources do not state trailing exit, break-even, and partial close.',
                     'Source did not define break-even and partial close.'):
            for aliases in (brief._BREAK_EVEN_ALIASES,brief._PARTIAL_CLOSE_ALIASES):
                with self.subTest(text=text,aliases=aliases):
                    self.assertFalse(brief._component_enabled_requested(text,aliases))

    def test_later_positive_requirements_are_not_erased(self):
        prefix='ไม่ได้ระบุ trailing exit, break-even หรือ partial close; '
        for rule,aliases in [('BreakEven=true',brief._BREAK_EVEN_ALIASES),
                             ('partial close 50% at 2R',brief._PARTIAL_CLOSE_ALIASES),
                             ('trailing stop 20 pips',brief._TRAILING_STOP_ALIASES)]:
            self.assertTrue(brief._component_enabled_requested(prefix+rule,aliases))

    def test_ambiguous_numeric_or_enabled_clause_is_still_required(self):
        for rule,aliases in [('break-even at 10 pips',brief._BREAK_EVEN_ALIASES),
                             ('PartialClose=true',brief._PARTIAL_CLOSE_ALIASES)]:
            self.assertTrue(brief._component_enabled_requested('ไม่ได้ระบุ trailing exit, '+rule,aliases))

    def test_affirmative_lists_remain_required(self):
        for aliases in (brief._TRAILING_STOP_ALIASES,brief._BREAK_EVEN_ALIASES,brief._PARTIAL_CLOSE_ALIASES):
            self.assertTrue(brief._component_enabled_requested('Use trailing stop, break-even and partial close.',aliases))
