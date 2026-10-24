import { PAIRS } from './data.js';

const CATALOG = new Map(PAIRS.map(pair => [pair.symbol, pair]));
const emptySentiment = () => ({available:false,long:null,short:null,avgLong:null,avgShort:null,asOf:null});
let snapshot = {schemaVersion:1,mode:'live',generatedAt:null,connection:'loading',revision:0,
 sentiment:{source:'Myfxbook',status:'loading',items:[]},
 correlations:{source:'MT5',status:'loading',items:[]},
 news:{source:'Forex Factory',status:'loading',events:[],calendarEvents:[]}};
const listeners = new Set();
export const subscribeMarket = callback => {listeners.add(callback);return()=>listeners.delete(callback);};
export const getMarketSnapshot = () => snapshot;
export const getMarketRevision = () => snapshot.revision;
const coefficient = value => typeof value==='number'&&Number.isFinite(value)&&Math.abs(value)<=1;
const numberOrNull = value => typeof value==='number'&&Number.isFinite(value)?value:null;
const safeUrl = value => {try {const url=new URL(value);return url.protocol==='https:'&&!url.username&&!url.password?url.href:null;}catch{return null;}};

// A mirror heartbeat measures the local service, not freshness of Myfxbook/MT5/news.
export function marketHeartbeat(input, now=Date.now(), required=false) {
 const raw=input?.mirror?.publishedAt;
 if(!required&&!raw)return {connection:'online',heartbeatAt:null};
 const time=typeof raw==='string'&&/(Z|[+-]\d{2}:\d{2})$/.test(raw)?Date.parse(raw):NaN;
 return {connection:Number.isFinite(time)&&now-time<=120000&&time-now<=30000?'online':'stale',heartbeatAt:Number.isFinite(time)?raw:null};
}
export function applyMarketSnapshot(input,{requireHeartbeat=false,now=Date.now()}={}) {
 if(input?.schemaVersion!==1||input?.mode!=='live'||!Array.isArray(input.sentiment?.items)||!Array.isArray(input.correlations?.items)||!Array.isArray(input.news?.events))throw new Error('invalid_market_snapshot');
 const sentiments=input.sentiment.items.filter(row=>CATALOG.has(row.symbol)).map(row=>{
  const long=numberOrNull(row.long),short=numberOrNull(row.short);
  const valid=row.available===true&&long!==null&&short!==null&&long>=0&&long<=100&&short>=0&&short<=100&&Math.abs(long+short-100)<=2;
  return {...row,available:valid,long:valid?long:null,short:valid?short:null,avgLong:numberOrNull(row.avgLong),avgShort:numberOrNull(row.avgShort)};
 });
 const seen = new Set();
 const correlations=input.correlations.items.filter(row=>CATALOG.has(row.source)&&CATALOG.has(row.target)&&row.source!==row.target).filter(row=>{const key=[row.source,row.target].sort().join('|');if(seen.has(key))return false;seen.add(key);return true;}).map(row=>({...row,value:coefficient(row.value)?row.value:null}));
 const normalizeEvents=rows=>Array.isArray(rows)?rows.filter(row=>row&&typeof row.id==='string'&&typeof row.title==='string'&&!row.mock).map(row=>({...row,currency:String(row.currency||'').toUpperCase(),sourceUrl:safeUrl(row.sourceUrl),forecast:row.forecast??'—',previous:row.previous??'—',actual:row.actual??null,mock:false})):[];
 snapshot={...input,...marketHeartbeat(input,now,requireHeartbeat),revision:snapshot.revision+1,
  sentiment:{...input.sentiment,items:sentiments},correlations:{...input.correlations,items:correlations},
  news:{...input.news,events:normalizeEvents(input.news.events),calendarEvents:normalizeEvents(input.news.calendarEvents)}};
 listeners.forEach(callback=>callback());
}
export function markMarketOffline(){snapshot={...snapshot,connection:'offline'};listeners.forEach(callback=>callback());}
export function getSentiment(symbol){return snapshot.sentiment.items.find(row=>row.symbol===symbol)||emptySentiment();}
export function getCorrelations(symbol){return snapshot.correlations.items.filter(row=>coefficient(row.value)&&(row.source===symbol||row.target===symbol)).map(row=>({...row,symbol:row.source===symbol?row.target:row.source})).sort((a,b)=>Math.abs(b.value)-Math.abs(a.value)||a.symbol.localeCompare(b.symbol));}
export function getAvailableEdges(filter='all'){return snapshot.correlations.items.filter(row=>coefficient(row.value)&&(filter==='all'||(CATALOG.get(row.source)?.assetClass===filter&&CATALOG.get(row.target)?.assetClass===filter)));}
export function thaiDay(iso=new Date().toISOString()){const date=new Date(iso);return Number.isFinite(date.getTime())?new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Bangkok',year:'numeric',month:'2-digit',day:'2-digit'}).format(date):'';}
export function formatThaiTime(iso){if(typeof iso!=='string'||!/(Z|[+-]\d{2}:\d{2})$/.test(iso))return '—';const d=new Date(iso);return Number.isFinite(d.getTime())?new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Bangkok',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(d):'—';}
export function formatThaiStamp(iso){if(!iso)return 'ยังไม่มี';const d=new Date(iso);return Number.isFinite(d.getTime())?new Intl.DateTimeFormat('th-TH',{timeZone:'Asia/Bangkok',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(d):'ยังไม่มี';}
export function eventTime(event){const precision=event.timePrecision||event.timeKind;return precision==='date'||precision==='all_day'?'ทั้งวัน':precision==='tentative'?'รอยืนยันเวลา':event.timeLabel||formatThaiTime(event.time);}
export function getNewsForSymbol(symbol,day=thaiDay()){
 const all=snapshot.news.calendarEvents.length?snapshot.news.calendarEvents:snapshot.news.events;
 const pair=CATALOG.get(symbol), currencies=pair?.assetClass==='forex'?[symbol.slice(0,3),symbol.slice(3)]:['USD'];
 return all.filter(event=>(event.dayThai||thaiDay(event.time))===day&&(!symbol||currencies.includes(event.currency)||event.currency==='ALL')).sort((a,b)=>(a.time||'9999').localeCompare(b.time||'9999')||a.id.localeCompare(b.id));
}
export function getEventScenarios(event,symbol){
 const pair=CATALOG.get(symbol);
 if(!pair||pair.assetClass!=='forex'||!['activity','employment','unemployment','inflation','confidence','growth','rates','retail'].includes(event.metric)||!Number.isFinite(event.forecastValue)||!event.numeric)return [];
 const side=event.currency===symbol.slice(0,3)?1:event.currency===symbol.slice(3)?-1:0;
 if(!side)return [];
 const polarity=event.metric==='unemployment'?-1:1;
 return [{key:'below',label:'ต่ำกว่าคาด',delta:-1},{key:'inline',label:'ใกล้เคียงคาด',delta:0},{key:'above',label:'สูงกว่าคาด',delta:1}].map(({delta,...item})=>{
  const direction=delta*polarity*side;
  return {...item,direction:direction>0?'up':direction<0?'down':'neutral',summary:direction>0?`อาจหนุน ${symbol} ↑`:direction<0?`อาจกดดัน ${symbol} ↓`:'ยังไม่ชี้ทิศ ต้องดูรายละเอียดและข่าวอื่นร่วมด้วย',note:event.metric==='inflation'?'ขึ้นกับการปรับคาดการณ์ดอกเบี้ย ไม่ใช่ผลตายตัว':'ฉากทัศน์พื้นฐานตามเงื่อนไข ไม่ใช่คำแนะนำซื้อขาย'};
 });
}
export function sourceStatus(source){const status=source?.status;return ({loading:'กำลังเชื่อมต่อ',ready:'พร้อม',ok:'พร้อม',fresh:'พร้อม',empty:'ไม่มีข่าววันนี้ในปฏิทิน',partial:'ข้อมูลบางส่วน',stale:'ข้อมูลเก่า',error:'เชื่อมต่อไม่สำเร็จ',needs_configuration:'รอเชื่อมบัญชี',auth_error:'ตรวจบัญชีอีกครั้ง',auth_failed:'ตรวจบัญชีอีกครั้ง',authentication_failed:'ตรวจบัญชีอีกครั้ง',rate_limited:'รอรอบโควต้า',provider_unavailable:'แหล่งข้อมูลยังไม่พร้อม',unavailable:'ยังไม่มีข้อมูล',market_closed:'ตลาดปิด',not_covered:'วันที่อยู่นอกช่วงข้อมูล',cached:'ข้อมูลจากรอบล่าสุด'})[status]||status||'ยังไม่มีข้อมูล';}
