"""Execute the actual JS model against recorded, historical and legacy timings."""
import unittest

import test_council_completed_round_frontend as fixtures
from test_frontend_polling_stability import function_block


class CouncilRoundHealthFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.CouncilCompletedRoundFrontendTests.setUpClass()
        cls.main = fixtures.CouncilCompletedRoundFrontendTests.main

    def run_js(self, body):
        harness = fixtures.CouncilCompletedRoundFrontendTests()
        harness.run_js(r"""
const state = {codexRate: {snapshot: {primary: {remainingPercent: 90}}}};
const formatThaiDateTime = value => new Date(value).toISOString();
const start = '2026-10-27T01:00:00Z';
Date.now = () => Date.parse('2026-10-27T01:00:50Z');
const at = seconds => new Date(Date.parse(start) + seconds * 1000).toISOString();
const automation = {dailyRoundLimitEnabled:false, dailyRunCount:1};
function health(parent, runState='running', qualityPolicy={roundDeadlineSeconds:240, automaticTotalBudgetSeconds:300}) {
  return signalRoundHealthModel({aiTradeCouncil:{qualityPolicy}}, automation,
    {parent, state:runState, statusLabel:runState}).rows;
}
""" + function_block(self.main, "signalRoundHealthModel") + "\n" + body)

    def test_recorded_automatic_300_uses_admission_start_not_late_mission_creation(self):
        self.run_js(r"""
const rows = health({createdAt:at(20), expiresAt:at(900), analysisContext:{
  roundStartedAt:start, roundDeadlineAt:at(300),
  automation:{quotaAdmittedAt:start, triggerExpiresAt:at(300)}
}});
assert.equal(rows[0].value,'50 วินาที');
assert.equal(rows[1].value,at(300));
assert.equal(rows[1].detail,'กรอบเวลารอบ 300 วินาที • Backend');
assert.equal(rows[1].state,'complete');
""")

    def test_projected_delegation_survives_real_run_model_and_stops_age_at_completion(self):
        self.run_js(r"""
const {report, manual} = fixture();
manual.createdAt=at(20); manual.completedAt=at(90);
Object.assign(manual.delegation,{roundStartedAt:start, roundDeadlineAt:at(300),
  triggerMode:'auto_on_new_closed_bar',roundTimingSource:'recorded_round'});
report.aiTradeCouncil.decisionPipeline.currentRun={parent:manual,parentMissionId:manual.id,current:true};
const run=signalCouncilRunModel(report);
assert.equal(run.parent,manual);
const rows=signalRoundHealthModel(report,automation,run).rows;
assert.equal(rows[0].value,'90 วินาที');
assert.equal(rows[1].value,at(300));
assert.match(rows[1].detail,/300 วินาที/);
""")

    def test_old_60_second_admission_does_not_replace_recorded_240_second_round(self):
        self.run_js(r"""
const rows=health({createdAt:at(20),analysisContext:{roundStartedAt:at(20),roundDeadlineAt:at(260),
  automation:{quotaAdmittedAt:start,triggerExpiresAt:at(60)}}});
assert.equal(rows[0].value,'30 วินาที');
assert.equal(rows[1].value,at(260));
assert.equal(rows[1].detail,'กรอบเวลารอบ 240 วินาที • Backend');
""")

    def test_recorded_60_second_round_and_legacy_admission_only_remain_60(self):
        self.run_js(r"""
for(const parent of [
  {createdAt:at(20),delegation:{roundStartedAt:start,roundDeadlineAt:at(60),triggerMode:'auto_on_new_closed_bar'}},
  {createdAt:at(20),analysisContext:{automation:{quotaAdmittedAt:start,triggerExpiresAt:at(60)}}},
  {createdAt:at(20),delegation:{roundStartedAt:start,roundDeadlineAt:at(60),
    roundTimingSource:'legacy_admission_window',triggerMode:'auto_on_new_closed_bar'}},
]) {
  const rows=health(parent);
  assert.equal(rows[1].value,at(60)); assert.match(rows[1].detail,/60 วินาที/);
  assert.doesNotMatch(rows[1].detail,/300|240/);
}
""")

    def test_manual_legacy_fallback_and_generic_explicit_deadline_still_work(self):
        self.run_js(r"""
const fallback=health({createdAt:start});
assert.equal(fallback[1].value,at(240));
assert.equal(fallback[1].detail,'นโยบาย 240 วินาที • ข้อมูลรุ่นเดิม');
const explicit=health({createdAt:start,deadlineAt:at(180)});
assert.equal(explicit[1].value,at(180));
assert.equal(explicit[1].detail,'เวลาที่บันทึกจาก Backend');
const recorded=health({createdAt:start,delegation:{roundDeadlineSeconds:120}});
assert.equal(recorded[1].value,at(120));
""")

    def test_no_automatic_time_invention_and_invalid_or_missing_dates_do_not_crash(self):
        self.run_js(r"""
for(const parent of [null,{createdAt:'bad'},
  {createdAt:start,delegation:{triggerMode:'auto_on_new_closed_bar'}},
  {createdAt:start,analysisContext:{roundStartedAt:'bad',roundDeadlineAt:'bad',automation:{}}},
]) {
  const rows=health(parent);
  assert.equal(rows[1].state,'unavailable');
  assert.equal(rows[1].detail,'ไม่สร้างเวลาเส้นตายใน Frontend');
}
const valid=health({createdAt:'bad',analysisContext:{roundStartedAt:'bad',roundDeadlineAt:'bad'},
  delegation:{roundStartedAt:start,roundDeadlineAt:at(300)}});
assert.equal(valid[0].value,'50 วินาที'); assert.equal(valid[1].value,at(300));
""")

    def test_exact_deadline_is_expired_only_for_running_round(self):
        self.run_js(r"""
Date.now=()=>Date.parse(at(300));
const parent={createdAt:at(20),delegation:{roundStartedAt:start,roundDeadlineAt:at(300)}};
assert.equal(health(parent)[1].state,'blocked');
assert.equal(health({...parent,completedAt:at(80)},'completed')[1].state,'complete');
assert.equal(health({...parent,completedAt:at(80)},'completed')[0].value,'80 วินาที');
""")


if __name__ == '__main__':
    unittest.main()
