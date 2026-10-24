"""Pure frontend probes. No bridge import, HTTP, runtime writes, or real jobs."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RadarDisplayTruthFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8-sig")
        cls.node = shutil.which("node")
        if not cls.node:
            raise unittest.SkipTest("Node is required for pure frontend probes")

    def function(self, name):
        start = self.source.index("function " + name + "(")
        if self.source[max(0, start - 6):start] == "async ":
            start -= 6
        end = self.source.find("\nfunction ", start + 1)
        return self.source[start:end if end >= 0 else len(self.source)]

    def probe(self, body):
        names = [
            "safeDashboardDisplayText", "workflowDomainObject", "workflowDomainArray", "workflowReportRows",
            "indicatorScoutObjectRows", "indicatorScoutSourceRows", "normalizeIndicatorScoutToolKind",
            "indicatorScoutToolKindLabel", "indicatorScoutSafeScreenshotUrl", "indicatorScoutTimestamp",
            "indicatorScoutBangkokDateKey", "filterIndicatorScoutToday", "filterIndicatorScoutRollingSevenDays",
            "radarAttemptPresentation", "normalizeRadarAttempts", "radarReadStatusMessage",
            "normalizeRadarSchedule", "normalizeRadarServiceHealth", "normalizeRadarRunStatus",
            "normalizeRadarPublicationPolicy", "radarPublicationCountLabel",
            "radarBangkokMinuteOfDay", "getRadarTodayRunState", "normalizeIndicatorScoutDomain",
            "createRadarRailTruthCard", "createBackendOwnedDailyScheduleCard", "createRadarTodayRunNotice",
            "createRadarAttemptHistory", "renderIndicatorScoutPanel", "loadPropReport", "pollOpenPropReport",
        ]
        prefix = r"""
const assert=require('node:assert/strict');
const INDICATOR_SCOUT_DEFAULT_TIME='09:00',INDICATOR_SCOUT_TIMEZONE='Asia/Bangkok',INDICATOR_SCOUT_EXPECTED_BATCH_SIZE=3;
const INDICATOR_SCOUT_PROP_ID='left_audit_crystals',PROP_REPORT_FETCH_TIMEOUT_MS=20000,OPEN_PROP_REPORT_POLL_TTL_MS=1000;
const EA_FACTORY_PROP_ID='right_server_racks',EA_OPTIMIZATION_LAB_PROP_ID='terminal_workstation';
const EA_OPTIMIZATION_LAB_ACTIVE_POLL_MS=1000,EA_OPTIMIZATION_LAB_IDLE_POLL_MS=1000;
const now='2026-10-23T03:08:00Z';
const runAt='2026-10-23T02:02:02.556867+00:00';
const state={propReports:{},propReportLoadedAt:{},propReportLoadState:{},panelObject:null,
 modal:{open:true,type:'prop',id:INDICATOR_SCOUT_PROP_ID},eaFactoryReadModel:{},eaOptimizationLabReadModel:{}};
const propReportInFlight=new Map();let rendered=[];
let fetchHandler=async()=>{throw new Error('simulated read failure; no HTTP')};
const fetchJson=(...args)=>fetchHandler(...args);const renderOperationalSidebars=()=>{};const selectObject=()=>{};
const eaOptimizationLabSessionIsActive=()=>false;
const researchSheetConsumerPresentation=()=>({detail:'fixture',label:'fixture'});
const researchSheetHubConfiguredReference=()=>'';const formatThaiDateTime=value=>String(value);
const getSafeExternalHttpUrl=value=>/^https?:\/\//.test(String(value||''))?String(value):'';
const getSafeReportImageUrl=()=>'';const formatDashboardValue=value=>String(value);
const document={visibilityState:'visible',hasFocus:()=>true,activeElement:{matches:()=>false},createElement:tag=>({
 tag,dataset:{},children:[],textContent:'',append(...nodes){this.children.push(...nodes)},appendChild(node){this.children.push(node)},
 setAttribute(name,value){this[name]=value},get childElementCount(){return this.children.length}})};
const createWorkflowTruthEmpty=text=>{const node=document.createElement('p');node.textContent=text;return node};
const textOf=node=>[node.textContent||'',...(node.children||[]).map(textOf)].join(' ');
const sample=()=>({updatedAt:'2026-10-23T03:00:00Z',missions:[],workflowDashboard:{actions:[],
 schedule:{effectiveEnabled:true,lastRunAt:runAt,lastRunStatus:'queued',lastResultKind:'scheduled_completion_retry_deferred',
 lastMissionId:'radar-current',runsReservedToday:1,status:'daily_limit_reached',nextRunAt:'2026-10-24T02:00:00Z'},
 radarWebsiteTool:{schemaVersion:'radar-website-tool-v1',expectedBatchSize:6,todayEntries:[],sevenDayEntries:[],
 serviceHealth:{status:'running',lastRunAt:runAt,activeMissionId:'radar-current',automaticCorrectiveRetry:{
 supported:true,status:'queued',sameMission:true,sameDailyReservation:true,newDailyReservation:false}}}}});
const domainOf=(report={},load={})=>normalizeIndicatorScoutDomain(report.workflowDashboard||{},report,load);
const renderGameModal=()=>{const domain=domainOf(state.propReports[INDICATOR_SCOUT_PROP_ID]||{},state.propReportLoadState[INDICATOR_SCOUT_PROP_ID]||{});
 rendered.push(getRadarTodayRunState(domain,now).state)};
"""
        script = prefix + "\n" + "\n".join(self.function(name) for name in names)
        script += "\n(async()=>{\n" + body + "\nprocess.stdout.write(JSON.stringify({ok:true}));})().catch(e=>{console.error(e);process.exitCode=1});"
        result = subprocess.run([self.node, "-"], input=script, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_cold_loading_is_unknown_not_zero_or_never_run(self):
        self.probe("""
const domain=domainOf({}, {status:'loading'}), run=getRadarTodayRunState(domain,now);
assert.equal(run.state,'data_loading');assert.doesNotMatch(run.title,/เลยเวลา/);
const rail=textOf(createRadarRailTruthCard({domainData:{indicatorScout:domain}}));
assert.doesNotMatch(rail,/ยังไม่เคยรัน|0 รายการ/);assert.match(rail,/ยังยืนยันไม่ได้/);
assert.equal(textOf(createRadarTodayRunNotice(domain)).includes('0/6'),false);
assert.doesNotMatch(textOf(createRadarTodayRunNotice(domain)),/วันนี้ยังไม่เริ่ม/);
assert.doesNotMatch(textOf(createBackendOwnedDailyScheduleCard({domainData:{indicatorScout:domain}})),/ยังไม่เคยรัน/);
""")

    def test_cold_error_has_explicit_error_and_unknown_count(self):
        self.probe("""
const domain=domainOf({}, {status:'error'}),run=getRadarTodayRunState(domain,now);
assert.equal(run.state,'data_error');assert.match(run.detail,/โหลดสถานะ Radar ไม่สำเร็จ/);
const container=document.createElement('main');renderIndicatorScoutPanel(container,'discoveries',domain);
assert.equal(textOf(container).includes('0/6'),false);assert.doesNotMatch(textOf(container),/ยังไม่เคยรัน|เลยเวลา 09/);
assert.match(textOf(container),/รอข้อมูล/);
""")

    def test_cached_error_preserves_data_and_labels_it_old(self):
        self.probe("""
const report=sample(),before=JSON.stringify(report),domain=domainOf(report,{status:'error'});
assert.equal(domain.readState.hasData,true);assert.equal(getRadarTodayRunState(domain,now).state,'queued');
assert.match(radarReadStatusMessage(domain),/ข้อมูลเดิม.*2026-10-23.*โหลดข้อมูลล่าสุดไม่สำเร็จ/);
assert.equal(JSON.stringify(report),before);
""")

    def test_cached_refresh_displays_refresh_notice(self):
        self.probe("""
const domain=domainOf(sample(),{status:'loading'});
assert.match(radarReadStatusMessage(domain),/ข้อมูลเดิม.*กำลังโหลดข้อมูลล่าสุด/);
""")

    def test_failed_first_poll_renders_error_even_without_report(self):
        self.probe("""
await pollOpenPropReport({force:true});
assert.equal(state.propReportLoadState[INDICATOR_SCOUT_PROP_ID].status,'error');
assert.equal(state.propReports[INDICATOR_SCOUT_PROP_ID],undefined);
assert.deepEqual(rendered,['data_loading','data_error']);
""")

    def test_later_poll_recovers_after_first_read_failure(self):
        self.probe("""
await pollOpenPropReport({force:true});const report=sample();fetchHandler=async()=>report;
await pollOpenPropReport({force:true});
assert.equal(state.propReportLoadState[INDICATOR_SCOUT_PROP_ID].status,'ready');
assert.equal(state.propReports[INDICATOR_SCOUT_PROP_ID],report);assert.equal(rendered.at(-1),'queued');
""")

    def test_failed_refresh_keeps_cached_payload_and_renders_stale_state(self):
        self.probe("""
const report=sample();state.propReports[INDICATOR_SCOUT_PROP_ID]=report;
await pollOpenPropReport({force:true});assert.equal(state.propReports[INDICATOR_SCOUT_PROP_ID],report);
const domain=domainOf(report,state.propReportLoadState[INDICATOR_SCOUT_PROP_ID]);
assert.match(radarReadStatusMessage(domain),/ข้อมูลเดิม/);assert.equal(rendered.at(-1),'queued');
""")

    def test_queued_repair_is_waiting_not_running(self):
        self.probe("""
const run=getRadarTodayRunState(domainOf(sample()),now);
assert.equal(run.state,'queued');assert.equal(run.tone,'waiting');assert.match(run.title,/รอคิว/);
""")

    def test_quota_waiting_uses_actual_attempt_reason(self):
        self.probe("""
const report=sample();report.missions=[{id:'radar-current',status:'queued',workStatus:'quota_deferred',
 reasonCode:'provider_rate_limited',nextAttemptAt:'2026-10-23T04:00:00Z',updatedAt:runAt}];
const run=getRadarTodayRunState(domainOf(report),now);
assert.equal(run.state,'quota_waiting');assert.equal(run.tone,'waiting');
assert.match(run.title,/รอโควตา/);assert.equal(run.nextAttemptAt,'2026-10-23T04:00:00Z');
""")

    def test_deferred_repair_displays_next_attempt(self):
        self.probe("""
const report=sample();Object.assign(report.workflowDashboard.radarWebsiteTool.serviceHealth.automaticCorrectiveRetry,
 {status:'deferred',nextAttemptAt:'2026-10-23T04:00:00Z'});
const run=getRadarTodayRunState(domainOf(report),now);
assert.equal(run.state,'deferred');assert.equal(run.nextAttemptAt,'2026-10-23T04:00:00Z');assert.equal(run.tone,'waiting');
""")

    def test_actual_runner_capacity_wait_is_distinct_from_codex_quota(self):
        self.probe("""
const report=sample();report.missions=[{id:'radar-current',status:'queued',dispatchState:'deferred',
 runnerStatus:'corrective_open_hourly_capacity_insufficient',reasonCode:null,blocker:null,result:'',
 nextAttemptAt:'2026-10-23T04:04:58Z',updatedAt:runAt}];
const domain=domainOf(report),run=getRadarTodayRunState(domain,now),attempt=domain.attemptHistory[0];
assert.equal(run.state,'hourly_capacity_waiting');assert.equal(run.tone,'waiting');
assert.match(run.title,/ช่องรันรายชั่วโมงของ HQ/);assert.match(run.detail,/ภายใน HQ/);
assert.doesNotMatch(run.detail,/Codex|ผู้ให้บริการ/);
assert.equal(run.nextAttemptAt,'2026-10-23T04:04:58Z');
assert.equal(attempt.reasonCode,'corrective_open_hourly_capacity_insufficient');
assert.match(textOf(createRadarAttemptHistory(domain)),/ช่องรันรายชั่วโมง.*HQ/);
""")

    def test_observed_running_attempt_overrides_old_queued_marker(self):
        self.probe("""
const report=sample();report.missions=[{id:'radar-current',status:'running',startedAt:runAt}];
const run=getRadarTodayRunState(domainOf(report),now);assert.equal(run.state,'corrective_running');assert.equal(run.tone,'running');
""")

    def test_failed_attempt_overrides_stale_active_marker(self):
        self.probe("""
const report=sample();report.missions=[{id:'radar-current',status:'failed',errorCode:'mission_prompt_too_large'}];
const run=getRadarTodayRunState(domainOf(report),now);
assert.equal(run.state,'corrective_failed');assert.match(run.detail,/ยาวเกินขอบเขต/);
""")

    def test_attempt_history_reveals_failure_without_fake_discoveries(self):
        self.probe("""
const report=sample();report.missions=[{id:'radar-failed',status:'failed',errorCode:'mission_prompt_too_large',createdAt:runAt},
 {id:'radar-current',status:'queued',result:'{"secret":"do not display raw result"}',createdAt:runAt}];
const before=JSON.stringify(report),domain=domainOf(report),container=document.createElement('main');
renderIndicatorScoutPanel(container,'history_7_days',domain);
assert.equal(domain.todayEntries.length,0);assert.equal(domain.sevenDayEntries.length,0);
assert.match(textOf(container),/ประวัติการทำงาน.*รอบติดขัด.*ยาวเกินขอบเขต/);
assert.doesNotMatch(textOf(container),/do not display raw result/);assert.equal(JSON.stringify(report),before);
""")

    def test_verified_six_results_remain_separate_from_attempts(self):
        self.probe("""
const report=sample(),rows=Array.from({length:6},(_,i)=>({id:'item-'+i,reportId:'report-ok',toolName:'Tool '+i,
 checkedAt:runAt,sourceUrl:'https://example.com/'+i,verificationStatus:'verified',duplicateStatus:'unique'}));
Object.assign(report.workflowDashboard.radarWebsiteTool,{todayEntries:rows,sevenDayEntries:rows});
report.missions=[{id:'failed-older',status:'failed',errorCode:'mission_prompt_too_large'}];
const domain=domainOf(report);assert.equal(domain.todayEntries.length,6);assert.equal(domain.attemptHistory.length,1);
assert.equal(getRadarTodayRunState(domain,now).state,'verified_results');
""")

    def test_history_attempt_window_includes_boundary_but_excludes_old_future_and_undated(self):
        self.probe("""
const cutoff=Date.parse(now)-7*24*60*60*1000;
const rows=[{id:'boundary',status:'failed',updatedAt:new Date(cutoff).toISOString(),result:'exact-boundary-visible'},
 {id:'old',status:'failed',updatedAt:new Date(cutoff-1).toISOString(),result:'old-attempt-hidden'},
 {id:'future',status:'failed',updatedAt:new Date(Date.parse(now)+1).toISOString(),result:'future-attempt-hidden'},
 {id:'undated',status:'failed',result:'undated-attempt-hidden'}];
const attempts=normalizeRadarAttempts(rows),before=JSON.stringify(attempts);
const text=textOf(createRadarAttemptHistory({attemptHistory:attempts},Date.parse(now)));
assert.match(text,/exact-boundary-visible/);assert.doesNotMatch(text,/old-attempt-hidden|future-attempt-hidden|undated-attempt-hidden/);
assert.equal(JSON.stringify(attempts),before);assert.match(text,/7 วันล่าสุด/);
""")

    def test_history_attempt_time_prefers_update_then_creation_without_completed_time_fallback(self):
        self.probe("""
const old='2026-10-15T02:00:00Z',recent='2026-10-22T02:00:00Z';
const attempts=normalizeRadarAttempts([
 {id:'updated',status:'failed',createdAt:old,updatedAt:recent,result:'recent-update-visible'},
 {id:'created',status:'failed',createdAt:recent,updatedAt:'invalid',result:'creation-fallback-visible'},
 {id:'completed-only',status:'failed',completedAt:recent,result:'completed-only-hidden'}]);
const text=textOf(createRadarAttemptHistory({attemptHistory:attempts},Date.parse(now)));
assert.match(text,/recent-update-visible/);assert.match(text,/creation-fallback-visible/);
assert.doesNotMatch(text,/completed-only-hidden/);
""")

    def test_history_filter_does_not_remove_old_current_attempt_from_today_truth(self):
        self.probe("""
const report=sample();report.missions=[{id:'radar-current',status:'queued',dispatchState:'deferred',
 runnerStatus:'corrective_open_hourly_capacity_insufficient',updatedAt:'2026-10-15T02:00:00Z'}];
const domain=domainOf(report);assert.equal(domain.attemptHistory.length,1);
assert.doesNotMatch(textOf(createRadarAttemptHistory(domain,Date.parse(now))),/ช่องรันรายชั่วโมง/);
assert.equal(getRadarTodayRunState(domain,now).state,'hourly_capacity_waiting');
assert.equal(domain.attemptHistory.length,1);
""")

    def test_known_failure_reasons_override_generic_local_runner_blocker(self):
        self.probe("""
const blocker={causeTh:'Local Runner หยุดงานรอบนี้ไว้เพื่อไม่ให้ผลที่ไม่ครบถูกนำไปใช้ต่อ'};
const attempts=normalizeRadarAttempts([
 {id:'rate',status:'failed',reasonCode:'rate_limited',blocker},
 {id:'quarantine',status:'blocked',reasonCode:'radar_retry_quarantined',blocker},
 {id:'other',status:'failed',reasonCode:'unknown_failure',blocker}]);
assert.equal(attempts[0].reason.includes('ขีดจำกัดคำขอ (Rate limit)'),true);
assert.match(attempts[1].reason,/หยุดลองซ้ำอัตโนมัติ.*เกินขอบเขต/);
assert.doesNotMatch(attempts[0].reason+attempts[1].reason,/Local Runner/);
assert.equal(attempts[0].state,'failed');assert.equal(attempts[1].state,'failed');
assert.equal(attempts[2].reason,blocker.causeTh);
""")

    def test_completed_history_removes_exact_trailing_machine_receipt_from_actual_result(self):
        self.probe("""
const result='ตรวจครบ 6 หน้าแบบ read-only; workflowReceipt='+JSON.stringify({procedureId:'backend-readonly-indicator-scout',
 procedureKind:'backend_procedure',loaded:true,version:'backend-v1'});
const input={id:'radar-current',status:'completed',result,updatedAt:runAt};
const attempts=normalizeRadarAttempts([input]),text=textOf(createRadarAttemptHistory({attemptHistory:attempts},Date.parse(now)));
assert.equal(attempts[0].reason,'ตรวจครบ 6 หน้าแบบ read-only');assert.match(text,/ตรวจครบ 6 หน้า/);
assert.doesNotMatch(text,/workflowReceipt|procedureId|backend-v1/);
assert.equal(input.result,result);assert.equal(attempts[0].state,'completed');
""")

    def test_receipt_cleanup_preserves_failed_reason_and_does_not_remove_following_errors(self):
        self.probe("""
const receipt='workflowReceipt='+JSON.stringify({procedureId:'backend-readonly-indicator-scout',
 procedureKind:'backend_procedure',loaded:false,version:'backend-v1'});
const [failed,diagnostic,unrelated]=normalizeRadarAttempts([
 {id:'failed',status:'failed',result:'อ่านหน้าเว็บไม่สำเร็จ; '+receipt},
 {id:'diagnostic',status:'failed',result:receipt+'; ข้อผิดพลาด: เว็บไซต์ปิดการเข้าถึง'},
 {id:'unrelated',status:'failed',result:'อ่านหน้าเว็บไม่สำเร็จ; payload={"error":"timeout"}'}]);
assert.equal(failed.reason,'อ่านหน้าเว็บไม่สำเร็จ');assert.equal(failed.state,'failed');
assert.match(diagnostic.reason,/ข้อผิดพลาด: เว็บไซต์ปิดการเข้าถึง/);
assert.equal(unrelated.reason,'อ่านหน้าเว็บไม่สำเร็จ; payload={"error":"timeout"}');
""")

    def test_rendered_seven_day_tab_filters_attempts_without_changing_verified_results(self):
        self.probe("""
const report=sample();report.missions=[
 {id:'old',status:'failed',createdAt:new Date(Date.now()-8*24*60*60*1000).toISOString(),result:'old-rendered-attempt-hidden'},
 {id:'recent',status:'failed',createdAt:new Date(Date.now()-60*1000).toISOString(),result:'recent-rendered-attempt-visible'}];
const domain=domainOf(report),container=document.createElement('main');
renderIndicatorScoutPanel(container,'history_7_days',domain);
assert.match(textOf(container),/recent-rendered-attempt-visible/);
assert.doesNotMatch(textOf(container),/old-rendered-attempt-hidden/);
assert.equal(domain.attemptHistory.length,2);assert.equal(domain.sevenDayEntries.length,0);
""")

    def test_partial_batch_never_becomes_verified_six(self):
        self.probe("""
const report=sample(),rows=Array.from({length:3},(_,i)=>({id:'item-'+i,reportId:'report-partial',toolName:'Tool '+i,
 checkedAt:runAt,sourceUrl:'https://example.com/'+i}));
Object.assign(report.workflowDashboard.radarWebsiteTool,{todayEntries:rows,sevenDayEntries:rows});
assert.equal(domainOf(report).todayEntries.length,0);
""")

    def test_authoritative_never_run_is_still_distinct_from_missing_data(self):
        self.probe("""
const report=sample();report.workflowDashboard.schedule={lastRunAt:null,lastRunStatus:'never'};
report.workflowDashboard.radarWebsiteTool.serviceHealth={};
const domain=domainOf(report);assert.equal(domain.readState.hasData,true);
assert.equal(getRadarTodayRunState(domain,now).state,'delayed');
assert.match(textOf(createRadarRailTruthCard({domainData:{indicatorScout:domain}})),/ยังไม่เคยรัน/);
""")

    def test_empty_schedule_object_is_not_evidence_of_never_run(self):
        self.probe("""
const domain=domainOf({workflowDashboard:{schedule:{}}},{status:'ready'});
assert.equal(domain.readState.hasData,false);assert.equal(getRadarTodayRunState(domain,now).state,'data_loading');
""")

    def test_other_dashboard_failure_does_not_trigger_radar_render(self):
        self.probe("""
await loadPropReport('left_signal_cube');assert.equal(rendered.length,0);
assert.equal(state.propReportLoadState.left_signal_cube.status,'error');
""")


if __name__ == "__main__":
    unittest.main()
