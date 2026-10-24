"""Offline, extracted-function FX28 UI tests; no backend imports or live actions."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class Fx28TrendFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8-sig")
        cls.styles = (ROOT / "frontend/src/styles/main.css").read_text(encoding="utf-8-sig")
        cls.node = shutil.which("node")
        if not cls.node:
            raise RuntimeError("Node is required for offline FX28 display tests")

    def function(self, name):
        match = re.search(r"^(?:async )?function " + re.escape(name) + r"\(", self.source, re.M)
        end = re.search(r"^(?:async )?function ", self.source[match.end():], re.M)
        return self.source[match.start():match.end() + end.start()] if end else self.source[match.start():]

    def probe(self, body, timezone="UTC"):
        names = ["safeDashboardDisplayText", "fx28TrendText", "fx28TrendInstant", "fx28DailyAiAnalysis", "normalizeFx28Trend",
                 "fx28TrendStatusLabel", "fx28AiStatusLabel", "createFx28TrendMethod", "renderFx28TrendTable",
                 "createFx28TrendRail", "renderFx28TrendHistory", "fxNewsBangkokDateTimeLabel",
                 "createFxNewsCalendarBanner", "createFxNewsRailFact", "renderFxNewsBiasPanel", "renderFxNewsSettingsRail"]
        universe = re.search(r"const FX_BIAS_PAIR_UNIVERSE = Object.freeze\(\[[\s\S]*?\]\);", self.source).group()
        script = r"""
const assert=require('node:assert/strict');
const FX_NEWS_BIAS_PROP_ID='left_signal_cube';
let legacyGridCalls=0,newsHistoryCalls=0,oldStateCalls=0,postCalls=0;
const state={propReportLoadState:{},modal:{workflowAction:{inFlight:false,propId:'',message:''}}};
const document={createElement:tag=>({tag,dataset:{},children:[],textContent:'',attributes:{},
 append(...nodes){this.children.push(...nodes)},appendChild(node){this.children.push(node);return node},
 setAttribute(key,value){this.attributes[key]=value},addEventListener(){},get childElementCount(){return this.children.length}})};
const els={workflowSettingsRail:document.createElement('aside'),workflowSettingsRailTitle:document.createElement('h3'),workflowSettingsRailContent:document.createElement('div')};
const textOf=node=>[node.textContent||'',...(node.children||[]).map(textOf)].join(' ');
const find=(node,fn)=>[...(fn(node)?[node]:[]),...(node.children||[]).flatMap(child=>find(child,fn))];
const getSafeExternalHttpUrl=value=>typeof value==='string'&&/^https:\/\//.test(value)&&!value.includes('localhost')?value:'';
const createWorkflowExternalSource=(url,label)=>{if(!getSafeExternalHttpUrl(url))return null;const node=document.createElement('a');node.href=url;node.textContent=label;return node};
const createWorkflowTruthEmpty=text=>{const node=document.createElement('p');node.textContent=text;return node};
const createFxFreshnessBanner=freshness=>freshness?.stale?createWorkflowTruthEmpty('OLD_NEWS_STALE'):null;
const appendFxNewsBackendState=()=>oldStateCalls++;
const renderFxBiasGrid=()=>legacyGridCalls++;
const renderFxNewsHistory=host=>{newsHistoryCalls++;host.appendChild(createWorkflowTruthEmpty('NEWS_HISTORY_PRESERVED'))};
const normalizeFxNewsSchedule=()=>({enabled:false,times:[]});
const fxNewsServiceStatusLabel=value=>value||'unknown';
const postJson=()=>{postCalls++;throw new Error('No live actions allowed')};
const now='2026-10-23T06:00:00Z';
""" + universe + "\n" + "\n".join(self.function(name) for name in names) + r"""
function fixture(){return {schemaVersion:'fx28-trend-read-model-v1',status:'ready',snapshotId:'market-snapshot',
 updatedAt:now,dataAsOf:now,stale:false,summary:{evaluatedPairCount:28,totalPairCount:28},
 schedule:{priceRefreshMinutes:15,priceNextRunAt:'2026-10-23T06:15:00Z',aiTime:'08:00',timezone:'Asia/Bangkok',aiNextRunAt:'2026-10-24T01:00:00Z'},
 ai:{status:'waiting',updatedAt:null,reasonTh:'รอรอบวิเคราะห์รายวัน',quota:{status:'unknown',remainingPercent:null}},history:[],
 rows:FX_BIAS_PAIR_UNIVERSE.map((pair,i)=>({pair,brokerSymbol:pair+'.a',status:'ready',
 horizons:Object.fromEntries(['short','medium','long'].map((key,j)=>[key,{bias:['BULLISH','BEARISH','SIDEWAY'][j],status:'ready',reasonTh:'เหตุผลราคา '+key,
 timeframes:{short:['M15','H1'],medium:['H1','H4','D1'],long:['D1','W1']}[key],dataAsOf:now,metrics:{close:1.123,tickVolumeRatio:1.2}}])),
 priceSummaryTh:'ราคาปิดอยู่เหนือค่าเฉลี่ยระยะสั้น',tickVolumeSummaryTh:'ความถี่ Tick สูงกว่าค่าเฉลี่ย',newsSummaryTh:'ไม่พบข่าวตรงที่ต้องรอ Actual',
 sourceRefs:[{id:'bars-'+i,kind:'closed_bars',pair,timeframe:'M15',dataAsOf:now},{id:'news-'+i,kind:'news',title:'ข่าวที่ตรวจยืนยัน',url:'https://example.com/news'}]}))};}
function dailyFixture(){const raw=fixture(),digest='a'.repeat(64),snapshotId='fx28-'+digest.slice(0,24);
 raw.ai={...raw.ai,status:'completed',snapshotId,marketDate:'2026-10-22',collectedAt:'2026-10-22T01:00:00Z',
 summaryTh:'สรุปรายวันที่ยืนยันแล้ว',newsSources:[{id:'news:official',url:'https://example.com/official',title:'ประกาศทางการ'}],
 analysis:{snapshotId,snapshotDigest:digest,marketDate:'2026-10-22',
 pairExplanations:FX_BIAS_PAIR_UNIVERSE.map(pair=>({pair,...Object.fromEntries(['short','medium','long'].map(key=>[key,{reasonTh:'คำอธิบายรายวัน '+pair+' '+key,sourceRefs:['price:'+pair+':H1']}]))})),
 newsContext:[{sourceRef:'news:official',summaryTh:'ธนาคารกลางเผยแพร่ผลประกาศ'}],limitations:[]}};return raw;}
(async()=>{
""" + body + "\nassert.equal(postCalls,0);process.stdout.write(JSON.stringify({ok:true}));})().catch(e=>{console.error(e);process.exitCode=1});"
        env = os.environ.copy()
        env["TZ"] = timezone
        result = subprocess.run([self.node, "-"], input=script, text=True, encoding="utf-8", capture_output=True, env=env, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_all_twenty_eight_pairs_keep_canonical_order_and_three_horizons(self):
        self.probe(r"""
const raw=fixture(),before=JSON.stringify(raw);raw.rows.reverse();const model=normalizeFx28Trend(raw);
assert.deepEqual(model.rows.map(row=>row.pair),FX_BIAS_PAIR_UNIVERSE);assert.equal(model.rows.length,28);
assert.equal(model.readyPairCount,28);assert.equal(model.partialPairCount,0);
for(const row of model.rows)assert.deepEqual(Object.keys(row.horizons),['short','medium','long']);
raw.rows.reverse();assert.equal(JSON.stringify(raw),before);
""")

    def test_missing_pairs_are_unknown_and_never_default_sideway(self):
        self.probe(r"""
const raw=fixture();raw.rows=raw.rows.slice(0,1);const model=normalizeFx28Trend(raw);
assert.equal(model.rows.length,28);assert.equal(model.readyPairCount,1);
for(const row of model.rows.slice(1))for(const horizon of Object.values(row.horizons))assert.equal(horizon.bias,'INSUFFICIENT_DATA');
""")

    def test_unknown_or_ambiguous_bias_enum_does_not_become_sideway(self):
        self.probe(r"""
for(const bias of ['HOLD','neutral','BUY','bullish','BULLISH|BEARISH','']){
 const raw=fixture();raw.rows[0].horizons.short.bias=bias;
 assert.equal(normalizeFx28Trend(raw).rows[0].horizons.short.bias,'INSUFFICIENT_DATA');
}
""")

    def test_partial_horizons_display_only_confirmed_directions(self):
        self.probe(r"""
const raw=fixture();raw.rows[0].status='partial';raw.rows[0].horizons.medium.status='insufficient_data';raw.rows[0].horizons.long.status='error';
const row=normalizeFx28Trend(raw).rows[0];assert.equal(row.status,'partial');assert.equal(row.horizons.short.bias,'BULLISH');
assert.equal(row.horizons.medium.bias,'INSUFFICIENT_DATA');assert.equal(row.horizons.long.bias,'INSUFFICIENT_DATA');
""")

    def test_stale_snapshot_suppresses_current_direction_and_displays_date(self):
        self.probe(r"""
const raw=fixture();raw.stale=true;const model=normalizeFx28Trend(raw),host=document.createElement('main');
assert.equal(model.readyPairCount,0);assert.equal(model.rows[0].horizons.short.bias,'INSUFFICIENT_DATA');
renderFx28TrendTable(host,raw);assert.match(textOf(host),/ข้อมูลราคาเก่า/);assert.match(textOf(host),/23/);
assert.equal(find(host,n=>n.className==='fx28-trend-badge'&&n.dataset.bias==='BULLISH').length,0);
""")

    def test_horizon_staleness_is_independent_for_each_timeframe(self):
        self.probe(r"""
const raw=fixture();raw.rows[0].horizons.short.status='stale';const row=normalizeFx28Trend(raw).rows[0];
assert.equal(row.horizons.short.status,'stale');assert.equal(row.horizons.short.bias,'INSUFFICIENT_DATA');
assert.equal(row.horizons.long.bias,'SIDEWAY');assert.equal(row.status,'partial');
""")

    def test_missing_naive_or_invalid_observation_time_cannot_authorize_direction(self):
        self.probe(r"""
for(const dataAsOf of [null,'2026-10-23T13:00:00','not-a-date']){
 const raw=fixture();raw.rows[0].horizons.short.dataAsOf=dataAsOf;
 assert.equal(normalizeFx28Trend(raw).rows[0].horizons.short.bias,'INSUFFICIENT_DATA');
}
assert.equal(fx28TrendInstant('2026-10-23T13:00:00+07:00'),'2026-10-23T13:00:00+07:00');
""")

    def test_missing_or_wrong_timeframes_do_not_show_fabricated_range(self):
        self.probe(r"""
for(const timeframes of [[],['W1'],['invalid']]){
 const raw=fixture();raw.rows[0].horizons.short.timeframes=timeframes;
 assert.equal(normalizeFx28Trend(raw).rows[0].horizons.short.bias,'INSUFFICIENT_DATA');
}
""")

    def test_global_error_unknown_schema_and_missing_snapshot_fail_closed(self):
        self.probe(r"""
for(const mutate of [r=>r.status='error',r=>r.schemaVersion='future-v9',r=>r.snapshotId='']){
 const raw=fixture();mutate(raw);const model=normalizeFx28Trend(raw);
 assert.equal(model.rows.length,28);assert.equal(model.readyPairCount,0);
 assert.equal(model.rows[0].horizons.short.bias,'INSUFFICIENT_DATA');
}
""")

    def test_duplicate_pair_does_not_overwrite_with_directional_result(self):
        self.probe(r"""
const raw=fixture();raw.rows.push({...raw.rows[0]});const model=normalizeFx28Trend(raw);
assert.equal(model.rows.length,28);assert.equal(model.rows[0].status,'error');assert.equal(model.readyPairCount,27);
assert.match(model.rows[0].horizons.short.reasonTh,/คู่เงินซ้ำ/);
""")

    def test_price_trends_stay_visible_when_news_is_stale_or_actual_is_missing(self):
        self.probe(r"""
const host=document.createElement('main');renderFxNewsBiasPanel(host,'pair_bias',{fxTrend:fixture(),freshness:{fxBias:{stale:true},marketNews:{stale:true}},pairBias:[]});
assert.equal(legacyGridCalls,0);assert.equal(oldStateCalls,0);assert.doesNotMatch(textOf(host),/OLD_NEWS_STALE/);
assert.equal(find(host,n=>n.className==='fx28-trend-badge'&&n.dataset.bias==='BULLISH').length,28);
assert.match(textOf(host),/ไม่พบข่าวตรงที่ต้องรอ Actual/);
""")

    def test_codex_waiting_deferred_failed_or_running_does_not_hide_prices(self):
        self.probe(r"""
for(const status of ['waiting','queued','deferred','failed','running']){
 const raw=fixture();raw.ai.status=status;const model=normalizeFx28Trend(raw);assert.equal(model.readyPairCount,28);
 const host=document.createElement('main');renderFx28TrendTable(host,raw);assert.match(textOf(host),/28\/28/);
}
""")

    def test_table_has_six_clear_columns_twenty_eight_rows_and_full_rationale(self):
        self.probe(r"""
const host=document.createElement('main');renderFx28TrendTable(host,fixture());
const table=find(host,n=>n.className==='fx28-trend-table')[0],head=find(table,n=>n.tag==='thead')[0],body=find(table,n=>n.tag==='tbody')[0];
assert.equal(head.children[0].children.length,6);assert.equal(body.children.length,28);
assert.match(textOf(head),/M15–H1/);assert.match(textOf(head),/H1–D1/);assert.match(textOf(head),/D1–W1/);
assert.match(textOf(body.children[0]),/ราคาปิดอยู่เหนือ/);assert.match(textOf(body.children[0]),/ความถี่ Tick/);assert.match(textOf(body.children[0]),/ข่าว/);
assert.match(textOf(body.children[0]),/AUDCAD\.a/);assert.equal(find(host,n=>n.className==='workflow-fx-bias-card').length,0);
""")

    def test_cold_loading_and_error_are_explicit_without_success_claim(self):
        self.probe(r"""
for(const status of ['loading','error']){
 const host=document.createElement('main');renderFx28TrendTable(host,{}, {status});
 assert.match(textOf(host),status==='error'?/โหลดแนวโน้มล่าสุดไม่สำเร็จ/:/กำลังโหลดแนวโน้ม 28 คู่เงิน/);
 assert.match(textOf(host),/0\/28/);assert.equal(find(host,n=>n.className==='fx28-trend-badge'&&n.dataset.bias!=='INSUFFICIENT_DATA').length,0);
}
""")

    def test_cached_refresh_error_preserves_dated_result_and_labels_old_read(self):
        self.probe(r"""
for(const status of ['loading','error']){
 const host=document.createElement('main');renderFx28TrendTable(host,fixture(),{status});
 assert.match(textOf(host),/กำลังแสดงผลจากรอบก่อน/);assert.match(textOf(host),/28\/28/);
}
""")

    def test_timestamp_is_always_thai_regardless_browser_timezone(self):
        for timezone in ("UTC", "America/New_York", "Asia/Tokyo"):
            with self.subTest(timezone=timezone):
                self.probe("assert.match(fxNewsBangkokDateTimeLabel(now),/13:00/);", timezone=timezone)

    def test_fresh_read_of_prior_week_closed_bar_is_not_presented_as_old_update(self):
        self.probe(r"""
const raw=fixture(),weekly='2026-10-17T21:00:00Z';raw.dataAsOf=weekly;
raw.rows[0].horizons.long.dataAsOf=weekly;raw.rows[0].sourceRefs.push({kind:'closed_bars',timeframe:'W1',dataAsOf:weekly});
const host=document.createElement('main');renderFx28TrendTable(host,raw);
const header=find(host,n=>n.className==='fx28-trend-header')[0];
assert.match(textOf(header),/อัปเดตข้อมูลล่าสุด.*23/);assert.doesNotMatch(textOf(header),/18 ต.ค./);
assert.equal(normalizeFx28Trend(raw).readyPairCount,28);
const firstRow=find(host,n=>n.tag==='tbody')[0].children[0];
assert.match(textOf(firstRow.children[3]),/แท่งปิด.*18/);
assert.match(textOf(firstRow.children[5]),/23/);assert.doesNotMatch(textOf(firstRow.children[5]),/18 ต.ค./);
assert.match(textOf(firstRow.children[4]),/W1.*18/);
assert.match(textOf(createFx28TrendRail(raw)),/อัปเดตราคาล่าสุด.*23/);
""")

    def test_mixed_timeframe_sideway_does_not_claim_flat_market(self):
        self.probe(r"""
const raw=fixture();raw.rows[0].horizons.long.reasonTh='ทิศทางแต่ละกรอบยังไม่สอดคล้อง หรือราคาอยู่ในช่วงแกว่ง';
const host=document.createElement('main');renderFx28TrendTable(host,raw);
const badge=find(host,n=>n.className==='fx28-trend-badge'&&n.dataset.bias==='SIDEWAY')[0];
assert.equal(textOf(badge),'↔ ไซด์เวย์');assert.match(badge.title,/ยังไม่สอดคล้อง/);
assert.match(textOf(createFx28TrendMethod()),/ไม่ได้ยืนยันว่าตลาดนิ่ง/);
""")

    def test_sidebar_shows_actual_price_interval_daily_codex_and_unknown_quota(self):
        self.probe(r"""
const raw=fixture(),text=textOf(createFx28TrendRail(raw));
assert.match(text,/ทุก 15 นาที/);assert.match(text,/08:00 น. เวลาไทย/);assert.match(text,/รอยืนยันโควตาปัจจุบัน/);assert.doesNotMatch(text,/คงเหลือ 0%/);
raw.schedule.priceRefreshMinutes=30;raw.schedule.aiTime='09:10';const updated=textOf(createFx28TrendRail(raw));
assert.match(updated,/ทุก 30 นาที/);assert.match(updated,/09:10 น. เวลาไทย/);
""")

    def test_stale_quota_percentage_does_not_look_current_or_ready(self):
        self.probe(r"""
const raw=fixture();raw.ai.status='deferred';raw.ai.quota={status:'stale',remainingPercent:83,reasonTh:'รออ่านโควตารอบใหม่'};
const text=textOf(createFx28TrendRail(raw));assert.doesNotMatch(text,/83%/);assert.match(text,/รอยืนยันโควตาปัจจุบัน/);assert.match(text,/พักรอโควตา/);
raw.ai.quota={status:'ready',remainingPercent:83};assert.match(textOf(createFx28TrendRail(raw)),/คงเหลือ 83%/);
""")

    def test_completed_daily_ai_summary_is_dated_and_independent_of_prices(self):
        self.probe(r"""
const raw=fixture();raw.ai={...raw.ai,status:'completed',summaryTh:'ค่าเงินตอบสนองต่อข้อมูลเศรษฐกิจที่ประกาศแล้ว',marketDate:'2026-10-23'};
const text=textOf(createFx28TrendRail(raw));
assert.match(text,/บทวิเคราะห์รายวัน • 2026-10-23/);assert.match(text,/ค่าเงินตอบสนอง/);
assert.match(text,/แนวโน้มราคาในตารางอัปเดตแยก/);assert.match(text,/โควตาตอนรับงานนี้/);assert.equal(normalizeFx28Trend(raw).readyPairCount,28);
""")

    def test_incomplete_or_machine_daily_ai_summary_is_not_displayed_as_completed(self):
        self.probe(r"""
for(const status of ['waiting','running','failed','deferred']){
 const raw=fixture();raw.ai={...raw.ai,status,summaryTh:'OLD_DAILY_RESULT',marketDate:'2026-10-23'};
 assert.doesNotMatch(textOf(createFx28TrendRail(raw)),/OLD_DAILY_RESULT/);
}
const raw=fixture();raw.ai={...raw.ai,status:'completed',summaryTh:'{"private":"schema"}'};
assert.doesNotMatch(textOf(createFx28TrendRail(raw)),/private|schema/);
""")

    def test_daily_pair_explanations_are_discoverable_dated_and_separate_from_current_prices(self):
        self.probe(r"""
const raw=dailyFixture(),host=document.createElement('main');renderFx28TrendTable(host,raw);
const daily=find(host,n=>n.className==='fx28-ai-pair-explanation');assert.equal(daily.length,28);
assert.equal(daily[0].tag,'details');assert.notEqual(daily[0].open,true);
assert.match(textOf(daily[0].children[0]),/คำอธิบาย Codex รายวัน • 2026-10-22/);
assert.match(textOf(daily[0]),/อิงชุดข้อมูล ณ .*22.*08:00/);assert.match(textOf(daily[0]),/แยกจากแนวโน้มราคาปัจจุบัน/);
for(const key of ['short','medium','long'])assert.match(textOf(daily[0]),new RegExp('AUDCAD '+key));
const row=find(host,n=>n.tag==='tbody')[0].children[0];
assert.doesNotMatch(textOf(row.children[1]),/เหตุผลราคา short|คำอธิบายรายวัน/);assert.match(textOf(row.children[4]),/เหตุผลราคา short/);
assert.equal(find(host,n=>n.className==='fx28-trend-badge'&&n.dataset.bias==='BULLISH').length,28);
assert.match(textOf(row.children[5]),/23/);
""")

    def test_daily_explanations_require_all_unique_pairs_and_exact_daily_identity(self):
        self.probe(r"""
for(const mutate of [
 r=>r.ai.analysis.pairExplanations.pop(),
 r=>r.ai.analysis.pairExplanations[27]=r.ai.analysis.pairExplanations[0],
 r=>r.ai.analysis.pairExplanations[0].pair='XAUUSD',
 r=>r.ai.analysis.marketDate='2026-10-21',
 r=>r.ai.analysis.snapshotId='fx28-'+ 'b'.repeat(24),
 r=>r.ai.analysis.snapshotDigest='b'.repeat(64),
 r=>r.ai.analysis.pairExplanations[0].short.reasonTh='{"private":"schema"}',
 r=>delete r.ai.analysis.pairExplanations[0].long,
 r=>r.ai.status='running'
]){
 const raw=dailyFixture();mutate(raw);const host=document.createElement('main');renderFx28TrendTable(host,raw);
 assert.equal(find(host,n=>n.className==='fx28-ai-pair-explanation').length,0);
 assert.equal(normalizeFx28Trend(raw).readyPairCount,28);
}
""")

    def test_daily_official_news_requires_matching_bound_ref_and_safe_link(self):
        self.probe(r"""
const raw=dailyFixture(),rail=createFx28TrendRail(raw),news=find(rail,n=>n.className==='fx28-ai-daily-news')[0];
assert.match(textOf(news),/2026-10-22/);assert.match(textOf(news),/ธนาคารกลางเผยแพร่ผลประกาศ/);
assert.equal(find(news,n=>n.tag==='a')[0].href,'https://example.com/official');
for(const mutate of [r=>r.ai.newsSources[0].id='news:other',r=>r.ai.newsSources[0].url='javascript:alert(1)',r=>delete r.ai.newsSources]){
 const other=dailyFixture();mutate(other);assert.equal(find(createFx28TrendRail(other),n=>n.className==='fx28-ai-daily-news').length,0);
}
""")

    def test_daily_retry_attempts_and_time_are_truthful_without_extra_actions(self):
        self.probe(r"""
for(const status of ['failed','deferred']){
 const raw=fixture();raw.ai={...raw.ai,status,attemptCount:1,maximumAttempts:2,nextAttemptAt:'2026-10-23T06:05:00Z'};
 const text=textOf(createFx28TrendRail(raw));assert.match(text,/ความพยายามรอบรายวัน.*1\/2 ครั้ง/);assert.match(text,/ลองรอบรายวันใหม่.*13:05/);
}
const raw=fixture();raw.ai={...raw.ai,status:'failed',attemptCount:NaN,maximumAttempts:2,nextAttemptAt:'2026-10-23T13:05:00'};
const text=textOf(createFx28TrendRail(raw));assert.doesNotMatch(text,/NaN|ลองรอบรายวันใหม่|ความพยายามรอบรายวัน/);
""")

    def test_trend_history_is_bounded_and_preserves_existing_news_history(self):
        self.probe(r"""
const raw=fixture();raw.history=Array.from({length:20},(_,i)=>({snapshotId:'history-'+i,updatedAt:now,dataAsOf:now,evaluatedPairCount:i,status:'partial'}));
const host=document.createElement('main');renderFxNewsBiasPanel(host,'history',{fxTrend:raw,freshness:{fxBias:{stale:false}}});
assert.equal(find(host,n=>n.className==='fx28-trend-history')[0].children.length,15);assert.equal(newsHistoryCalls,1);assert.match(textOf(host),/NEWS_HISTORY_PRESERVED/);
assert.doesNotMatch(textOf(host),/history-0/);
""")

    def test_method_is_collapsed_and_explains_tick_activity_honestly(self):
        self.probe(r"""
const method=createFx28TrendMethod();assert.equal(method.tag,'details');assert.notEqual(method.open,true);
assert.match(textOf(method),/ความถี่การเปลี่ยนแปลงราคาที่ Broker/);assert.match(textOf(method),/ไม่ใช่ยอดซื้อขายสุทธิหรือปริมาณซื้อขายรวมทั้งตลาด/);
assert.match(textOf(method),/ราคาอาจพร้อมก่อนบทวิเคราะห์รายวัน/);
""")

    def test_machine_objects_and_unsafe_source_links_do_not_leak_into_ui(self):
        self.probe(r"""
const raw=fixture();raw.rows[0].priceSummaryTh={token:'secret'};raw.rows[0].newsSummaryTh='{"internal":"schema"}';
raw.rows[0].sourceRefs=[{kind:'news',title:'bad source',url:'javascript:alert(1)'}];
const host=document.createElement('main');renderFx28TrendTable(host,raw);const text=textOf(host);
assert.doesNotMatch(text,/secret|internal|\[object Object\]/);assert.equal(find(host,n=>n.tag==='a'&&String(n.href).startsWith('javascript:')).length,0);
assert.equal(find(host,n=>n.tag==='script').length,0);
""")

    def test_settings_rail_separates_news_controls_from_price_and_ai_schedule(self):
        self.probe(r"""
renderFxNewsSettingsRail({domainData:{fxNewsBias:{fxTrend:fixture(),schedule:{enabled:true,times:['00:00','12:00']},service:{sources:[]}}}},{id:'fx-news'});
const text=textOf(els.workflowSettingsRailContent);assert.match(text,/รอบราคาและบทวิเคราะห์ Codex/);assert.match(text,/รอบข่าวเศรษฐกิจ \(แยกจากราคา\)/);
assert.match(text,/08:00/);assert.match(text,/ทุก 15 นาที/);assert.equal(els.workflowSettingsRailTitle.textContent,'รอบอัปเดตและสถานะ');
""")

    def test_normalizer_passthrough_does_not_couple_trends_to_news_gates(self):
        block = self.function("normalizeFxNewsBiasDomain")
        self.assertIn("fxTrend: workflowDomainObject(backend.fxTrend, backend.domainData?.fxTrend, legacyRoot.fxTrend)", block)
        panel = self.function("renderFxNewsBiasPanel")
        self.assertIn('tabId === "pair_bias" && domain.fxTrend ? null', panel)
        self.assertIn("renderFxNewsHistory(section, domain)", panel)
        self.assertIn("renderFxBiasGrid(section, domain.pairBias, domain.pairAssessmentSummary)", panel)

    def test_compact_horizon_cells_keep_full_reasons_in_expandable_details(self):
        self.probe(r"""
const raw=dailyFixture(),host=document.createElement('main');renderFx28TrendTable(host,raw);
const row=find(host,n=>n.tag==='tbody')[0].children[0];
for(const [index,key] of [[1,'short'],[2,'medium'],[3,'long']]){
 const cell=row.children[index];assert.equal(cell.children.length,2);
 assert.equal(cell.children[0].className,'fx28-trend-badge');assert.equal(cell.children[1].className,'fx28-trend-bar-time');
 assert.match(cell.children[0].title,new RegExp('เหตุผลราคา '+key));assert.match(textOf(cell.children[1]),/แท่งปิด.*23/);
}
const rationale=row.children[4],priceDetails=rationale.children.find(n=>n.tag==='details'&&!n.className);
for(const key of ['short','medium','long'])assert.match(textOf(priceDetails),new RegExp('เหตุผลราคา '+key));
assert.match(textOf(rationale.children[0]),/ราคา: .*ราคาปิดอยู่เหนือ/);
assert.match(textOf(rationale),/Tick Volume: .*ความถี่ Tick/);assert.match(textOf(rationale),/ข่าว: /);
assert.equal(find(rationale,n=>n.className==='fx28-ai-pair-explanation').length,1);
""")

    def test_styles_are_scoped_full_width_sticky_and_scrollable(self):
        start = self.styles.index(".workflow-fx-news-bias .fx28-trend-panel")
        end = self.styles.index(".workflow-fx-bias-grid", start)
        styles = self.styles[start:end]
        self.assertIn("width: 100%", styles)
        self.assertIn("overflow: auto", styles)
        self.assertIn("position: sticky", styles)
        self.assertIn("left: 0", styles)
        self.assertIn("top: 0", styles)
        self.assertIn("font-size: 13px", styles)
        self.assertIn("padding: 8px 12px", styles)
        self.assertTrue(all(float(size) >= 12 for size in re.findall(r"font-size:\s*([\d.]+)px", styles)))
        self.assertNotIn("signal-consensus", styles)
        self.assertNotIn("workflow-radar", styles)


if __name__ == "__main__":
    unittest.main()
