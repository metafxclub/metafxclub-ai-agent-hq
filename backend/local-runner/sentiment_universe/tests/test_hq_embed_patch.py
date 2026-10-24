import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hq_patch',ROOT/'scripts'/'patch-hq-sentiment.py')
patch=importlib.util.module_from_spec(spec);spec.loader.exec_module(patch)

BASE='''const FX_NEWS_BIAS_PROP_ID = "left_signal_cube";
const PROP_DISPLAY = {
  left_signal_cube: "ศูนย์แนวโน้ม 28 คู่เงินและข่าว Forex",
};
const anchors = {
  left_signal_cube: { x: 24.2, y: 66.0, label: "ศูนย์แนวโน้ม 28 คู่เงินและข่าว Forex" },
};
const identity = {
    labelTh: "FX BIAS CENTER",
    eyebrowTh: "ภาพรวม 28 คู่เงิน ข่าว และช่วงเวลาที่ EA ควรระวัง",
};
function getEquipmentPurpose(subject) { return {
    [FX_NEWS_BIAS_PROP_ID]: "ติดตามข่าวและแนวโน้ม 28 คู่เงินในระยะสั้น กลาง และยาว พร้อมกำหนดเวลาอัปเดตข่าว โดยไม่ส่งคำสั่งเทรด",
}[subject.id]; }
function getPropertyRole(subject) {
  return state.propReports[subject.id]?.propertyRole || null;
}
function gameModalFocusableElements() {
  if (!els.gameModal) return [];
  return existingFocusList();
}
function renderWorkflowDashboard(subject, propertyRole, report = {}) { existingWorkflow(); }
function openGameModal(type, id, tab = "chat") { existingModal(); }
function closeGameModal() { existingClose(); }
async function pollOpenPropReport({ force = false, signal = null } = {}) { existingPoll(); }
async function loadPropReport(propId, { signal = null, forceFresh = false, shouldApply = null } = {}) { existingRead(); }
async function saveFxNewsSchedule(form) { existingSchedule(); }
async function refreshFxNewsDirect() { existingRefresh(); }
function renderSignalConsensusDashboard() { /* Council must remain identical. */ return tradingState; }
'''

class PatchTests(unittest.TestCase):
    def test_patch_preserves_existing_bodies_and_is_idempotent(self):
        result=patch.patch_text(BASE)
        for body in ('existingWorkflow();','existingModal();','existingClose();','existingPoll();','existingRead();','existingSchedule();','existingRefresh();'):
            self.assertEqual(result.count(body),1)
        self.assertIn(BASE.split('function renderSignalConsensusDashboard')[1],result)
        self.assertEqual(result.count('// SENTIMENT_UNIVERSE_HOOK'),7)
        self.assertEqual(patch.patch_text(result),result)
        self.assertIn('Sentiment Universe · 32 สินทรัพย์',result)
        self.assertIn('Oil แสดงเมื่อมีข้อมูลที่ใช้ได้',result)
        self.assertIn('SENTIMENT_UNIVERSE_FOCUS_V1',result)
    def test_unknown_baseline_fails_without_partial_result(self):
        with self.assertRaises(ValueError):patch.patch_text(BASE.replace('existingRead();','existingRead();') .replace('async function refreshFxNewsDirect()', 'async function renamedRefresh()'))
    def test_partial_patch_is_rejected(self):
        with self.assertRaises(ValueError):patch.patch_text(BASE+'\n'+patch.MARKER)

if __name__=='__main__':unittest.main()
