import test from 'node:test';
import assert from 'node:assert/strict';
import {applyMarketSnapshot,getSentiment,getCorrelations,getAvailableEdges,getNewsForSymbol,getEventScenarios,formatThaiTime,thaiDay,eventTime,getMarketSnapshot,markMarketOffline} from '../src/market-data.js';

const base=()=>({schemaVersion:1,mode:'live',sentiment:{status:'ready',items:[]},correlations:{status:'ready',items:[]},news:{status:'ready',events:[],calendarEvents:[]}});
test('live unavailable never falls back to design percentages or correlations',()=>{
 applyMarketSnapshot(base());assert.equal(getSentiment('EURUSD').available,false);assert.equal(getSentiment('EURUSD').long,null);assert.deepEqual(getCorrelations('EURUSD'),[]);
});
test('official rounded shares preserved, invalid or missing values rejected',()=>{
 const data=base();data.sentiment.items=[{symbol:'EURUSD',available:true,long:55,short:44,avgLong:1.1,avgShort:1.2},{symbol:'GBPUSD',available:true,long:80,short:80},{symbol:'WTI',available:false,long:50,short:50}];applyMarketSnapshot(data);
 assert.equal(getSentiment('EURUSD').long,55);assert.equal(getSentiment('EURUSD').short,44);assert.equal(getSentiment('GBPUSD').available,false);assert.equal(getSentiment('WTI').long,null);
});
test('missing edge is not zero, zero is valid, duplicate edge not counted twice',()=>{
 const data=base();data.correlations.items=[{source:'EURUSD',target:'GBPUSD',value:0},{source:'GBPUSD',target:'EURUSD',value:0},{source:'EURUSD',target:'WTI',value:null},{source:'EURUSD',target:'XAUUSD',value:.8},{source:'EURUSD',target:'USDJPY',value:1.2}];applyMarketSnapshot(data);
 assert.equal(getAvailableEdges().length,2);assert.equal(getAvailableEdges('forex').length,1);assert.deepEqual(getCorrelations('EURUSD').map(r=>r.value),[.8,0]);assert.equal(getCorrelations('GBPUSD')[0].symbol,'EURUSD');
});
test('Thai date boundary keeps same-time events distinct and filters both currencies',()=>{
 const data=base();data.news.calendarEvents=[{id:'1',currency:'EUR',time:'2026-10-23T16:59:00Z',title:'A',mock:false},{id:'2',currency:'USD',time:'2026-10-23T17:00:00Z',title:'B',mock:false},{id:'3',currency:'USD',time:'2026-10-23T17:00:00Z',title:'C',mock:false},{id:'4',currency:'All',time:'2026-10-23T17:00:00Z',title:'D',mock:false},{id:'5',currency:'CAD',time:'2026-10-23T17:00:00Z',title:'E',mock:false}];applyMarketSnapshot(data);
 assert.equal(getNewsForSymbol('EURUSD','2026-10-23').length,1);assert.equal(getNewsForSymbol('EURUSD','2026-10-24').length,3);assert.equal(getNewsForSymbol(null,'2026-10-24').length,4);assert.equal(thaiDay('2026-10-23T17:00:00Z'),'2026-10-24');
});
test('source times with DST offsets become Thai; ambiguous time never invented',()=>{
 assert.equal(formatThaiTime('2026-10-23T08:30:00-04:00'),'19:30');assert.equal(formatThaiTime('2026-11-06T08:30:00-05:00'),'20:30');assert.equal(formatThaiTime('2026-10-23T08:30:00'),'—');assert.equal(eventTime({timePrecision:'tentative'}),'รอยืนยันเวลา');assert.equal(eventTime({timeKind:'all_day'}),'ทั้งวัน');
});
test('sample news and unsafe source links do not become live evidence',()=>{
 const data=base();data.news.events=[{id:'demo',title:'Fake',mock:true},{id:'live',title:'Live',currency:'USD',time:'2026-10-24T02:00Z',sourceUrl:'javascript:alert(1)'}];applyMarketSnapshot(data);
 assert.equal(getMarketSnapshot().news.events.length,1);assert.equal(getMarketSnapshot().news.events[0].sourceUrl,null);
});
test('unknown news and missing consensus never get directional predictions',()=>{
 assert.deepEqual(getEventScenarios({metric:'unknown',numeric:true,forecastValue:1,currency:'USD'},'EURUSD'),[]);
 assert.deepEqual(getEventScenarios({metric:'inflation',numeric:true,forecastValue:null,currency:'USD'},'EURUSD'),[]);
 assert.deepEqual(getEventScenarios({metric:'inflation',numeric:true,forecastValue:1,currency:'USD'},'XAUUSD'),[]);
});
test('conditional effects invert for quote currency and unemployment',()=>{
 const event={metric:'employment',numeric:true,forecastValue:1,currency:'USD'};assert.equal(getEventScenarios(event,'USDJPY')[2].direction,'up');assert.equal(getEventScenarios(event,'EURUSD')[2].direction,'down');assert.equal(getEventScenarios({...event,metric:'unemployment'},'USDJPY')[2].direction,'down');
});
test('offline preserves last known evidence with explicit connection status',()=>{
 const data=base();data.sentiment.items=[{symbol:'EURUSD',available:true,long:70,short:30}];applyMarketSnapshot(data);markMarketOffline();assert.equal(getMarketSnapshot().connection,'offline');assert.equal(getSentiment('EURUSD').long,70);
});
test('wrong envelope rejected instead of clearing established evidence',()=>{
 assert.throws(()=>applyMarketSnapshot({mode:'demo'}));assert.equal(getSentiment('EURUSD').long,70);
});
