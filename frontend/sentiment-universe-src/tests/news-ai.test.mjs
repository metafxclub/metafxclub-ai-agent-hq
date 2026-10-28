import test from 'node:test';
import assert from 'node:assert/strict';
import {applyMarketSnapshot,getMarketSnapshot,getNewsForSymbol,getEventAi,getNewsAiState,getEventScenarios,thaiDay,eventTime} from '../src/market-data.js';
import {getNewsExplainer} from '../src/news-explainers.js';

const scenario=(direction,textTh)=>({direction,textTh});
function fixture(){
 const generatedAt=new Date().toISOString(),dayThai=thaiDay(generatedAt),inputDigest='a'.repeat(64);
 const event={id:'us-pmi',dayThai,time:generatedAt,currency:'USD',title:'PMI สหรัฐฯ',metric:'activity',numeric:true,forecastValue:50,forecast:'50',previous:'49',actual:null,summary:'คำอธิบายพื้นฐาน',sourceName:'Calendar',sourceUrl:'https://www.forexfactory.com/calendar',mock:false};
 event.ai={status:'ready',dayThai,generatedAt,inputDigest,eventId:event.id,summaryTh:'AI อธิบายข่าวตามเงื่อนไขและข้อมูลปฏิทินวันนี้',explanationTh:['สำรวจทิศทางกิจกรรมทางธุรกิจ','ค่าดัชนี 50 แบ่งการขยายและการหดตัว','เทียบกับค่าคาดการณ์และเดือนก่อน','การตอบสนองขึ้นกับนโยบายและภาวะตลาด'],scenarios:{currency:{below:scenario('down','USD อาจถูกกดดันหากกิจกรรมต่ำกว่าคาด'),inline:scenario('unknown','ยังไม่ชี้ทิศทาง USD'),above:scenario('up','USD อาจได้แรงหนุนผ่านคาดการณ์ดอกเบี้ย')},XAUUSD:{below:scenario('up','ทองอาจได้แรงหนุนเมื่อ USD และผลตอบแทนจริงลดลง'),inline:scenario('unknown','ทองยังขึ้นกับปัจจัยอื่น'),above:scenario('mixed','แรงกดดันจากดอกเบี้ยอาจหักล้างความต้องการสินทรัพย์ปลอดภัย')},XAGUSD:{below:scenario('mixed','เงินอาจเผชิญอุปสงค์อุตสาหกรรมอ่อนลงแม้ USD อ่อน'),inline:scenario('unknown','ติดตามอุปสงค์อุตสาหกรรมด้วย'),above:scenario('up','อุปสงค์อุตสาหกรรมอาจช่วยหนุนราคาเงิน')}},horizonNotesTh:{short:'อาจผันผวนหลังประกาศ',medium:'ดูความต่อเนื่องของเศรษฐกิจและดอกเบี้ย',long:'ข่าวเดียวไม่ยืนยันทิศทางระยะยาว'},caveatTh:'ฉากทัศน์ตามเงื่อนไข ไม่ใช่สัญญาณซื้อขาย',sourceRefs:[{name:'S&P Global',url:'https://www.spglobal.com/market-intelligence/en/solutions/products/pmi'}]};
 const data={schemaVersion:1,mode:'live',sentiment:{items:[]},correlations:{items:[]},news:{status:'ready',events:[event],calendarEvents:[event],aiAnalysis:{status:'ready',dayThai,generatedAt,inputDigest}}};
 return {data,event};
}

test('current ready batch displays verified event summary, bounded explainer and source provenance',()=>{
 const {data,event}=fixture();applyMarketSnapshot(data);
 assert.equal(getNewsAiState().status,'ready');assert.equal(getEventAi(event).summaryTh,event.ai.summaryTh);
 const info=getNewsExplainer(event);assert.equal(info.origin,'ai');assert.equal(info.lines.length,4);assert.deepEqual(info.sourceRefs,event.ai.sourceRefs);assert.equal(info.generatedAt,data.news.aiAnalysis.generatedAt);
 info.lines[0]='mutated';assert.notEqual(getNewsExplainer(event).lines[0],'mutated');assert.equal(event.actual,null);
});

test('Forex quote currency reverses only direction; AI explanation remains the original currency channel',()=>{
 const {data,event}=fixture();applyMarketSnapshot(data);
 const usd=getEventScenarios(event,'USDJPY'),eur=getEventScenarios(event,'EURUSD');
 assert.equal(usd[2].direction,'up');assert.equal(eur[2].direction,'down');assert.equal(eur[2].detail,usd[2].detail);assert.match(eur[2].detail,/USD/);assert.match(eur[2].summary,/EURUSD/);
 assert.equal(eur[1].direction,'unknown');assert.deepEqual(getEventScenarios(event,'EURJPY'),[]);
});

test('gold and silver use their own explicit scenarios, including conflicting forces, never a USD inverse',()=>{
 const {data,event}=fixture();applyMarketSnapshot(data);
 const gold=getEventScenarios(event,'XAUUSD'),silver=getEventScenarios(event,'XAGUSD');
 assert.equal(gold[2].direction,'mixed');assert.equal(silver[2].direction,'up');assert.match(gold[2].detail,/ดอกเบี้ย/);assert.match(silver[2].detail,/อุตสาหกรรม/);assert.deepEqual(getEventScenarios(event,'WTI'),[]);
 event.ai.scenarios.XAUUSD=null;assert.deepEqual(getEventScenarios(event,'XAUUSD'),[]);assert.equal(getEventScenarios(event,'XAGUSD').length,3);
 event.currency='EUR';assert.deepEqual(getEventScenarios(event,'XAGUSD'),[]);
});

test('nonnumeric events and missing consensus keep explanation without inventing directional scenarios',()=>{
 for(const changes of [{numeric:false,kind:'speech'},{forecastValue:null},{forecastValue:NaN}]){
  const {data,event}=fixture();Object.assign(event,changes);applyMarketSnapshot(data);
  assert.equal(getNewsExplainer(event).origin,'ai');assert.deepEqual(getEventScenarios(event,'EURUSD'),[]);assert.deepEqual(getEventScenarios(event,'XAUUSD'),[]);assert.equal(event.actual,null);
 }
});

test('pending, running and failure states preserve all calendar events and explicitly use dictionary fallback',()=>{
 for(const status of ['pending','queued','running','failed','blocked','interrupted','stale','empty']){
  const {data,event}=fixture();data.news.aiAnalysis.status=status;applyMarketSnapshot(data);
  assert.equal(getNewsAiState().status,status);assert.equal(getEventAi(event),null);assert.equal(getNewsExplainer(event).origin,'dictionary');assert.equal(getNewsForSymbol('EURUSD').length,1);
  assert.equal(getEventScenarios(event,'EURUSD')[2].origin,'dictionary');assert.deepEqual(getEventScenarios(event,'XAUUSD'),[]);
 }
});

test('wrong event ID, calendar digest, batch date or generation receipt cannot be presented as ready AI',()=>{
 for(const mutate of [e=>e.ai.eventId='different',e=>e.ai.inputDigest='b'.repeat(64),e=>e.ai.dayThai='2000-01-01',e=>e.ai.generatedAt='2000-01-01T00:00:00Z']){
  const {data,event}=fixture();mutate(event);applyMarketSnapshot(data);assert.equal(getEventAi(event),null);assert.equal(getNewsExplainer(event).origin,'dictionary');
 }
 const {data,event}=fixture();delete data.news.aiAnalysis.dayThai;applyMarketSnapshot(data);assert.equal(getNewsAiState().status,'stale');assert.equal(getEventAi(event),null);
});

test('Thai midnight and future timestamps invalidate yesterday or not-yet-generated analysis',()=>{
 const {data,event}=fixture();const now=Date.parse('2026-10-27T17:00:00Z');
 Object.assign(data.news.aiAnalysis,{dayThai:'2026-10-27',generatedAt:'2026-10-27T16:59:00Z'});Object.assign(event,{dayThai:'2026-10-27'});Object.assign(event.ai,data.news.aiAnalysis);
 assert.equal(getNewsAiState(data.news,'2026-10-27',now).status,'stale');assert.equal(getEventAi(event,data.news,now),null);
 Object.assign(data.news.aiAnalysis,{dayThai:'2026-10-28',generatedAt:'2026-10-27T17:01:00Z'});assert.equal(getNewsAiState(data.news,'2026-10-28',now).status,'stale');
 data.news.aiAnalysis.generatedAt='2026-10-28T00:00:00';assert.equal(getNewsAiState(data.news,'2026-10-28',now).status,'stale');
});

test('malformed prose, references or scenario enums fail closed instead of entering the popup',()=>{
 for(const mutate of [a=>a.explanationTh.push('fifth'),a=>a.explanationTh=[],a=>a.summaryTh='x'.repeat(401),a=>a.sourceRefs[0].url='javascript:alert(1)',a=>a.sourceRefs[0].url='https://user:password@example.com/',a=>a.scenarios.XAUUSD.above.direction='buy',a=>delete a.horizonNotesTh.medium]){
  const {data,event}=fixture();mutate(event.ai);applyMarketSnapshot(data);assert.equal(getEventAi(event),null);assert.equal(getNewsExplainer(event).origin,'dictionary');
 }
});

test('ready batch missing one event never adopts another event analysis',()=>{
 const {data,event}=fixture();const other={...event,id:'another',title:'ข่าวอื่น'};delete other.ai;data.news.events.push(other);data.news.calendarEvents.push(other);applyMarketSnapshot(data);
 assert.equal(getNewsExplainer(other).origin,'dictionary');assert.equal(getNewsExplainer(event).origin,'ai');assert.equal(getNewsForSymbol('EURUSD').length,2);
});

test('multiple simultaneous releases and tentative USD events remain visible to both metals',()=>{
 const {data,event}=fixture();data.news.calendarEvents=Array.from({length:75},(_,i)=>({...event,id:`event-${i}`,currency:i%3===0?'EUR':'USD'}));data.news.calendarEvents.push({...event,id:'tentative',time:null,timeKind:'tentative'});applyMarketSnapshot(data);
 assert.equal(getNewsForSymbol('EURUSD').length,76);assert.equal(getNewsForSymbol('XAUUSD').length,51);assert.equal(getNewsForSymbol('XAGUSD').length,51);assert.equal(eventTime(getNewsForSymbol('XAUUSD').at(-1)),'รอยืนยันเวลา');assert.equal(getMarketSnapshot().news.status,'ready');
});
