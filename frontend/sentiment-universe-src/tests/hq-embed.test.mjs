import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {normalizeEmbedOptions} from '../src/embed-options.js';
import {assetUrl} from '../src/asset-url.js';
import {marketHeartbeat,applyMarketSnapshot,getMarketSnapshot,getSentiment} from '../src/market-data.js';
import {startMarketPolling} from '../src/market-poller.js';
import {handleUniverseKey} from '../src/embed-interaction.js';

test('Escape closes explainer, then news, then inspector without closing outer HQ dialog',()=>{
 const closed=[];const state={explainerOpen:true,eventOpen:true,inspectorOpen:true,closeExplainer:()=>{closed.push('explainer');state.explainerOpen=false;},closeNews:()=>{closed.push('news');state.eventOpen=false;},closeInspector:()=>{closed.push('inspector');state.inspectorOpen=false;}};
 for(const name of ['explainer','news','inspector']){
  let prevented=0,stopped=0;const event={key:'Escape',preventDefault:()=>prevented++,stopPropagation:()=>stopped++};
  assert.equal(handleUniverseKey(event,state),true);assert.equal(closed.at(-1),name);assert.equal(prevented,1);assert.equal(stopped,1);
 }
 assert.equal(handleUniverseKey({key:'Escape'},state),false); // The next Escape may close HQ.
});
test('embedded Tab reads ShadowRoot focus and excludes inert controls',()=>{
 let active;const rootNode={get activeElement(){return active;}};
 const element=inert=>({closest:()=>inert?{}:null,getClientRects:()=>[{}],focus(){active=this;}});
 const first=element(false),inert=element(true),last=element(false);active=last;
 const root={querySelectorAll:()=>[first,inert,last],getRootNode:()=>rootNode};
 let stopped=0,prevented=0;const event={key:'Tab',shiftKey:false,stopPropagation:()=>stopped++,preventDefault:()=>prevented++};
 handleUniverseKey(event,{embedded:true,root});assert.equal(active,first);assert.equal(stopped,1);assert.equal(prevented,1);
 handleUniverseKey({...event,shiftKey:true},{embedded:true,root});assert.equal(active,last);
});

test('HQ assets and mirror stay same-origin; setup is a separate loopback page',()=>{
 const result=normalizeEmbedOptions({},'http://127.0.0.1:4186');
 assert.equal(result.marketUrl,'http://127.0.0.1:4186/frontend/public/sentiment-universe/market.json');
 assert.equal(result.setupUrl,'http://127.0.0.1:4197/connect');assert.equal(result.requireHeartbeat,true);
 assert.equal(assetUrl(result.assetBase,'nebula-depth-v1.png'),'http://127.0.0.1:4186/frontend/public/sentiment-universe/assets/nebula-depth-v1.png');
 assert.throws(()=>normalizeEmbedOptions({marketUrl:'https://foreign.example/market'},'http://127.0.0.1:4186'));
 assert.throws(()=>normalizeEmbedOptions({setupUrl:'http://remote.example/connect'},'http://127.0.0.1:4186'));
 assert.throws(()=>normalizeEmbedOptions({setupUrl:'http://user:password@127.0.0.1:4197/connect'},'http://127.0.0.1:4186'));
});
test('heartbeat detects stopped mirror despite fresh-looking generatedAt; does not age source timestamps',()=>{
 const now=Date.parse('2026-10-24T12:00:00Z');
 assert.equal(marketHeartbeat({generatedAt:new Date(now).toISOString()},now,true).connection,'stale');
 assert.equal(marketHeartbeat({mirror:{publishedAt:'2026-10-24T11:58:00Z'}},now,true).connection,'online');
 assert.equal(marketHeartbeat({mirror:{publishedAt:'2026-10-24T11:57:59Z'}},now,true).connection,'stale');
 assert.equal(marketHeartbeat({mirror:{publishedAt:'2026-10-24T12:00:31Z'}},now,true).connection,'stale');
 assert.equal(marketHeartbeat({mirror:{publishedAt:'2026-10-24T12:00:00'}},now,true).connection,'stale');
 const data={schemaVersion:1,mode:'live',mirror:{publishedAt:'2026-10-24T11:50:00Z'},sentiment:{status:'ready',lastSuccessAt:'2026-10-24T11:40:00Z',items:[{symbol:'EURUSD',available:true,long:70,short:30}]},correlations:{status:'market_closed',items:[]},news:{events:[],calendarEvents:[]}};
 applyMarketSnapshot(data,{requireHeartbeat:true,now});
 assert.equal(getMarketSnapshot().connection,'stale');assert.equal(getSentiment('EURUSD').long,70);
 assert.equal(getMarketSnapshot().sentiment.lastSuccessAt,data.sentiment.lastSuccessAt);
 assert.equal(getMarketSnapshot().correlations.status,'market_closed');
});
const flush=()=>new Promise(resolve=>setImmediate(resolve));
test('unmount aborts pending fetch, suppresses late response and does not schedule another poll',async()=>{
 let resolveRequest,signal;const timers=new Map();let id=0,received=0,failed=0;
 const stop=startMarketPolling({url:'/mirror.json',onData:()=>received++,onFailure:()=>failed++,fetchImpl:(_url,options)=>{signal=options.signal;return new Promise(resolve=>resolveRequest=resolve);},schedule:(fn,ms)=>{timers.set(++id,{fn,ms});return id;},cancel:key=>timers.delete(key)});
 assert.equal(timers.size,1);stop();assert.equal(signal.aborted,true);
 resolveRequest({ok:true,json:async()=>({})});await flush();
 assert.equal(received,0);assert.equal(failed,0);assert.equal(timers.size,0);
});
test('poller waits for completion before scheduling next request and preserves failure backoff',async()=>{
 const timers=new Map();let id=0,calls=0,failures=0;
 const stop=startMarketPolling({url:'/mirror.json',onData:()=>{},onFailure:()=>failures++,fetchImpl:async()=>{calls++;return {ok:false};},schedule:(fn,ms)=>{timers.set(++id,{fn,ms});return id;},cancel:key=>timers.delete(key)});
 await flush();assert.equal(calls,1);assert.equal(failures,1);assert.equal(timers.size,1);assert.equal([...timers.values()][0].ms,30000);stop();assert.equal(timers.size,0);
});

function lifecycleHarness(){
 const byId=new Map();
 class Element{
  constructor(){this.children=[];this.parentNode=null;this.isConnected=true;this.classList={add(){},remove(){}};}
  setAttribute(){} addEventListener(){}
  appendChild(node){this.children.push(node);node.parentNode=this;if(node.id)byId.set(node.id,node);return node;}
  replaceChildren(...nodes){this.children.forEach(node=>{node.parentNode=null;node.isConnected=false;});this.children=[];nodes.forEach(node=>this.appendChild(node));}
  remove(){this.isConnected=false;if(this.parentNode){this.parentNode.children=this.parentNode.children.filter(node=>node!==this);this.parentNode=null;}}
 }
 let resolveImport,imports=0,mounts=0,unmounts=0;
 const context={document:{getElementById:id=>byId.get(id),createElement:()=>new Element(),head:new Element()},els:{workflowDashboardContent:new Element(),gameModal:new Element()},state:{modal:{open:true,type:'prop',id:'left_signal_cube'}},FX_NEWS_BIAS_PROP_ID:'left_signal_cube',loadModule:()=>{imports++;return new Promise(resolve=>resolveImport=resolve);}};
 vm.createContext(context);
 const script=fs.readFileSync(new URL('../scripts/hq-embed-runtime.js',import.meta.url),'utf8').replace('import(moduleUrl)','loadModule(moduleUrl)');
 vm.runInContext(script+'\nglobalThis.api={render:renderSentimentUniverse,dispose:disposeSentimentUniverse};',context);
 return {...context,resolve:()=>resolveImport({mountSentimentUniverse:()=>{mounts++;return {unmount:()=>unmounts++};}}),counts:()=>({imports,mounts,unmounts})};
}
test('HQ repeated renders preserve the same mounted galaxy; close cleans it once',async()=>{
 const h=lifecycleHarness();h.api.render();const host=h.els.workflowDashboardContent.children[0];h.api.render();assert.equal(h.els.workflowDashboardContent.children[0],host);assert.equal(h.counts().imports,1);
 h.resolve();await flush();h.api.render();assert.equal(h.counts().mounts,1);h.api.dispose();h.api.dispose();assert.equal(h.counts().unmounts,1);
});
test('closing during module load prevents late mount, reopening can reuse the loaded module',async()=>{
 const h=lifecycleHarness();h.api.render();h.api.dispose();h.state.modal.open=false;h.resolve();await flush();assert.equal(h.counts().mounts,0);
 h.state.modal.open=true;h.api.render();await flush();assert.equal(h.counts().mounts,1);assert.equal(h.counts().imports,1);h.api.dispose();
});
