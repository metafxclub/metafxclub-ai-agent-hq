"""Offline DOM probes for actual 0..3 Radar results and preserved legacy reports."""
import unittest
from pathlib import Path

import test_radar_display_truth_frontend as display_truth


class RadarPublicationV2FrontendTests(unittest.TestCase):
    setUpClass = classmethod(display_truth.RadarDisplayTruthFrontendTests.setUpClass.__func__)
    function = display_truth.RadarDisplayTruthFrontendTests.function

    def probe(self, body):
        setup = r"""
const v2={version:2,mode:'up_to_maximum',maximumItemCount:3,minimumItemCount:0};
const v1={version:1,mode:'exact_count',maximumItemCount:6,minimumItemCount:6};
function resultReport(count,{legacy=false,verifiedEmpty=false,status='completed',readyCount=1}={}) {
 const report=sample();
 const rows=Array.from({length:count},(_,id)=>({recordId:'item-'+id,reportId:'ready-report',
  checkedAt:runAt,toolName:'Tool '+id,sourceUrl:'https://example.com/tool/'+id,
  verificationStatus:'verified',duplicateStatus:'unique',publicationVersion:legacy?1:2,toolKind:'tool'}));
 Object.assign(report.workflowDashboard.schedule,{lastRunStatus:status,lastResultKind:status,lastMissionId:'radar-current'});
 Object.assign(report.workflowDashboard.radarWebsiteTool,{expectedBatchSize:3,publicationPolicy:v2,
  todayPublicationPolicy:legacy?v1:v2,today:{publicationPolicy:legacy?v1:v2,verifiedEmpty,
   verifiedReadyBatchCount:readyCount,status:verifiedEmpty?'verified_empty':status},todayEntries:rows,sevenDayEntries:[...rows],
  serviceHealth:{status,lastRunAt:runAt}});
 return report;
}
globalThis.createIndicatorScoutCard=item=>{const node=document.createElement('article');node.className='fixture-radar-card';node.textContent=item.title;return node};
globalThis.formatIndicatorScoutHistoryDay=()=> 'วันทดสอบ';
const findNodes=(node,predicate)=>[...(predicate(node)?[node]:[]),...(node.children||[]).flatMap(child=>findNodes(child,predicate))];
"""
        display_truth.RadarDisplayTruthFrontendTests.probe(self, setup + body)

    def test_new_default_policy_is_maximum_three_without_minimum(self):
        self.assertIn("const INDICATOR_SCOUT_EXPECTED_BATCH_SIZE = 3;", self.source)
        self.probe(r"""
const policy=normalizeRadarPublicationPolicy();
assert.equal(policy.version,2);assert.equal(policy.maximumItemCount,3);assert.equal(policy.minimumItemCount,0);
assert.equal(policy.legacy,false);assert.equal(policy.valid,true);
""")

    def test_zero_verified_completion_is_success_without_error(self):
        self.probe(r"""
const report=resultReport(0,{verifiedEmpty:true}),before=JSON.stringify(report),domain=domainOf(report);
const run=getRadarTodayRunState(domain,now),notice=textOf(createRadarTodayRunNotice(domain));
assert.equal(domain.verifiedEmpty,true);assert.equal(run.state,'verified_empty');assert.equal(run.tone,'ready');
assert.match(run.title,/ไม่พบรายการใหม่/);assert.equal(run.error,'');assert.match(notice,/0 รายการ/);
assert.doesNotMatch(notice,/0\/3|หาให้ครบ/);assert.equal(JSON.stringify(report),before);
""")

    def test_one_verified_result_is_published_without_filling_to_three(self):
        self.probe(r"""
const domain=domainOf(resultReport(1)),run=getRadarTodayRunState(domain,now);
assert.equal(domain.todayEntries.length,1);assert.equal(run.state,'verified_results');assert.match(run.title,/1 รายการ/);
assert.doesNotMatch(run.title+run.detail,/ให้ครบ|ไม่สมบูรณ์/);
const host=document.createElement('main');renderIndicatorScoutPanel(host,'discoveries',domain);
assert.equal(findNodes(host,n=>n.className==='fixture-radar-card').length,1);assert.match(textOf(host),/สูงสุด 3 รายการต่อวัน/);
""")

    def test_two_verified_results_are_published_as_two(self):
        self.probe(r"""
const domain=domainOf(resultReport(2));assert.equal(domain.todayEntries.length,2);
assert.equal(getRadarTodayRunState(domain,now).state,'verified_results');
assert.match(radarPublicationCountLabel(domain,2),/^2 รายการ/);assert.doesNotMatch(radarPublicationCountLabel(domain,2),/2\/3/);
""")

    def test_three_verified_results_are_published_as_three(self):
        self.probe(r"""
const domain=domainOf(resultReport(3));assert.equal(domain.todayEntries.length,3);
assert.equal(getRadarTodayRunState(domain,now).state,'verified_results');
const host=document.createElement('main');renderIndicatorScoutPanel(host,'discoveries',domain);
assert.equal(findNodes(host,n=>n.className==='fixture-radar-card').length,3);
""")

    def test_four_new_results_are_rejected_without_silently_truncating(self):
        self.probe(r"""
const report=resultReport(4),before=JSON.stringify(report),domain=domainOf(report);
assert.equal(domain.publicationValidationError,true);assert.equal(domain.todayEntries.length,0);
assert.equal(getRadarTodayRunState(domain,now).state,'publication_invalid');
const host=document.createElement('main');renderIndicatorScoutPanel(host,'discoveries',domain);
assert.equal(findNodes(host,n=>n.className==='fixture-radar-card').length,0);assert.match(textOf(host),/รอข้อมูลที่ยืนยัน/);
assert.equal(JSON.stringify(report),before);
""")

    def test_empty_failed_run_does_not_become_no_new_success(self):
        self.probe(r"""
const domain=domainOf(resultReport(0,{status:'failed',readyCount:0}));
const run=getRadarTodayRunState(domain,now);assert.equal(domain.verifiedEmpty,false);
assert.equal(run.state,'corrective_failed');assert.equal(run.tone,'error');assert.doesNotMatch(run.title,/ไม่พบรายการใหม่/);
""")

    def test_completed_zero_without_verified_empty_proof_waits_for_result(self):
        self.probe(r"""
const domain=domainOf(resultReport(0)),run=getRadarTodayRunState(domain,now);
assert.equal(domain.verifiedEmpty,false);assert.equal(run.state,'awaiting_result');assert.equal(run.tone,'waiting');
assert.match(run.detail,/ยังไม่มีหลักฐานยืนยันผลว่าง/);
""")

    def test_verified_empty_flag_without_ready_batch_cannot_mark_success(self):
        self.probe(r"""
const domain=domainOf(resultReport(0,{verifiedEmpty:true,readyCount:0}));
assert.equal(domain.verifiedEmpty,false);assert.equal(getRadarTodayRunState(domain,now).state,'awaiting_result');
""")

    def test_verified_empty_report_has_precedence_over_stale_active_markers(self):
        self.probe(r"""
const report=resultReport(0,{verifiedEmpty:true});
Object.assign(report.workflowDashboard.radarWebsiteTool.serviceHealth,{status:'running',activeMissionId:'stale'});
const run=getRadarTodayRunState(domainOf(report),now);assert.equal(run.state,'verified_empty');
""")

    def test_legacy_six_today_remains_visible_under_new_current_policy(self):
        self.probe(r"""
const report=resultReport(6,{legacy:true}),before=JSON.stringify(report),domain=domainOf(report);
assert.equal(domain.publicationPolicy.maximumItemCount,3);assert.equal(domain.todayPublicationPolicy.maximumItemCount,6);
assert.equal(domain.todayEntries.length,6);assert.equal(getRadarTodayRunState(domain,now).state,'verified_results');
const host=document.createElement('main');renderIndicatorScoutPanel(host,'discoveries',domain);
assert.equal(findNodes(host,n=>n.className==='fixture-radar-card').length,6);
assert.match(textOf(host),/กติกาเดิม 6 รายการ/);assert.doesNotMatch(textOf(host),/6\/3/);assert.equal(JSON.stringify(report),before);
""")

    def test_legacy_six_history_is_not_truncated_by_new_one_item_report(self):
        self.probe(r"""
const report=resultReport(1),legacy=resultReport(6,{legacy:true}).workflowDashboard.radarWebsiteTool.todayEntries;
legacy.forEach((item,id)=>{item.reportId='old-report';item.recordId='old-'+id;item.checkedAt='2026-10-22T02:02:00Z'});
report.workflowDashboard.radarWebsiteTool.sevenDayEntries.push(...legacy);
const domain=domainOf(report);assert.equal(domain.todayEntries.length,1);assert.equal(domain.sevenDayEntries.length,7);
const host=document.createElement('main');renderIndicatorScoutPanel(host,'history',domain);
assert.equal(findNodes(host,n=>n.className==='fixture-radar-card').length,7);assert.match(textOf(host),/มีรายงานตามกติกาเดิม/);
""")

    def test_categories_allow_any_mix_including_github_tools(self):
        self.probe(r"""
for(const kinds of [['ea','ea','ea'],['indicator','indicator','indicator'],['tool','tool','tool'],['ea','indicator','tool']]) {
 const report=resultReport(3);report.workflowDashboard.radarWebsiteTool.todayEntries.forEach((item,id)=>{
  item.toolKind=kinds[id];if(kinds[id]==='tool')item.sourceUrl='https://github.com/example/technology-'+id;
 });
 const domain=domainOf(report);assert.deepEqual(domain.todayEntries.map(item=>item.toolKind),kinds);
 assert.equal(getRadarTodayRunState(domain,now).state,'verified_results');
}
""")

    def test_loading_error_and_stale_cache_stay_distinct_from_verified_empty(self):
        self.probe(r"""
assert.equal(getRadarTodayRunState(domainOf({}, {status:'loading'}),now).state,'data_loading');
assert.equal(getRadarTodayRunState(domainOf({}, {status:'error'}),now).state,'data_error');
for(const status of ['loading','error']) {
 const domain=domainOf(resultReport(2),{status}),host=document.createElement('main');
 renderIndicatorScoutPanel(host,'discoveries',domain);assert.equal(domain.todayEntries.length,2);
 assert.match(textOf(host),/กำลังแสดงข้อมูลเดิม/);assert.equal(getRadarTodayRunState(domain,now).state,'verified_results');
}
""")

    def test_retry_copy_does_not_require_three_valid_items(self):
        self.probe(r"""
const report=resultReport(0,{status:'running',readyCount:0});
report.workflowDashboard.radarWebsiteTool.serviceHealth={status:'running',activeMissionId:'radar-current',
 automaticCorrectiveRetry:{supported:true,status:'running',sameMission:true,sameDailyReservation:true,newDailyReservation:false}};
const run=getRadarTodayRunState(domainOf(report),now);assert.equal(run.state,'corrective_running');
assert.doesNotMatch(run.title,/ให้ครบ/);assert.match(run.detail,/ไม่ต้องหาให้ครบ 3/);
""")

    def test_canonical_projection_mismatch_is_not_a_smaller_success(self):
        self.probe(r"""
const report=resultReport(3);report.workflowDashboard.radarWebsiteTool.sevenDayEntries=report.workflowDashboard.radarWebsiteTool.sevenDayEntries.slice(0,2);
const domain=domainOf(report);assert.equal(domain.publicationValidationError,true);assert.equal(domain.todayEntries.length,0);
assert.equal(getRadarTodayRunState(domain,now).state,'publication_invalid');
""")

    def test_unknown_policy_or_wrong_maximum_is_not_accepted(self):
        self.probe(r"""
for(const policy of [{...v2,version:99},{...v2,maximumItemCount:4},{...v2,minimumItemCount:1}]) {
 const report=resultReport(1);report.workflowDashboard.radarWebsiteTool.todayPublicationPolicy=policy;
 const domain=domainOf(report);assert.equal(domain.todayEntries.length,0);assert.equal(getRadarTodayRunState(domain,now).state,'publication_invalid');
}
""")

    def test_three_columns_use_available_radar_width_then_two_and_one(self):
        styles = (Path(display_truth.ROOT) / "frontend/src/styles/main.css").read_text(encoding="utf-8")
        start = styles.index(".workflow-radar-website-tool .workflow-indicator-grid.workflow-radar-grid")
        end = styles.index(".workflow-indicator-card.workflow-radar-card", start)
        rules = styles[start:end]
        self.assertIn("container: radar-results / inline-size", styles)
        self.assertIn("width: 100%", rules)
        self.assertIn("repeat(3, minmax(0, 1fr))", rules)
        self.assertIn("@container radar-results (max-width: 1000px)", rules)
        self.assertIn("repeat(2, minmax(0, 1fr))", rules)
        self.assertIn("@container radar-results (max-width: 620px)", rules)
        self.assertIn("grid-template-columns: minmax(0, 1fr)", rules)


if __name__ == "__main__":
    unittest.main()
