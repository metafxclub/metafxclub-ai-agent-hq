import {useCallback,useEffect,useMemo,useRef,useState} from 'react';
import {IconSearch,IconX,IconPlayerPause,IconPlayerPlay,IconRotateClockwise,IconInfoCircle,IconExternalLink,IconClock,IconArrowUpRight,IconArrowDownRight,IconMinus,IconLink,IconUsers,IconAdjustmentsHorizontal,IconNews,IconCircleFilled} from '@tabler/icons-react';
import {OrbitalScene} from './OrbitalScene.jsx';
import {SentimentPreview} from './SentimentPreview.jsx';
import {getSentimentColor} from './SentimentNode.js';
import {PAIRS} from './data.js';
import {getSentiment,getNewsForSymbol,getEventScenarios,getCorrelations,getAvailableEdges,thaiDay,formatThaiStamp,eventTime,sourceStatus} from './market-data.js';
import {useMarketData} from './useMarketData.js';
import {assetUrl} from './asset-url.js';
import {handleUniverseKey} from './embed-interaction.js';

import {getNewsExplainer} from './news-explainers.js';
import {correlationTone,correlationColor} from './correlation-network.js';
import {useInspectorPresence} from './useInspectorPresence.js';

const FILTERS=[['all','ทั้งหมด',32],['forex','Forex',28],['metals','Metals',2],['oil','Oil',2]];
const SENTIMENT_GRADIENT=`linear-gradient(90deg,${[0,10,20,35,50,65,80,90,100].map(long=>`${getSentimentColor({available:true,long,short:100-long}).color} ${long}%`).join(',')})`;
function AssetSearch({symbol,onSelect}){
 const[query,setQuery]=useState(''),[open,setOpen]=useState(false),[active,setActive]=useState(0);const host=useRef(null),input=useRef(null);
 const matches=PAIRS.filter(p=>`${p.symbol} ${p.name}`.toLowerCase().includes(query.trim().toLowerCase()));
 useEffect(()=>{const close=e=>{if(!e.composedPath().includes(host.current))setOpen(false);};document.addEventListener('pointerdown',close);return()=>document.removeEventListener('pointerdown',close);},[]);
 const pick=value=>{onSelect(value);setOpen(false);setQuery('');input.current?.focus();};
 return <div className="asset-search" ref={host}><IconSearch size={18}/><input ref={input} value={query} role="combobox" aria-label="ค้นหาสินทรัพย์ 32 รายการ" aria-expanded={open} aria-controls={open?'asset-options':undefined} aria-autocomplete="list" aria-activedescendant={open&&matches[active]?`asset-${matches[active].symbol}`:undefined} placeholder="ค้นหาสินทรัพย์ เช่น EURUSD" onFocus={()=>setOpen(true)} onChange={e=>{setQuery(e.target.value);setActive(0);setOpen(true);}} onKeyDown={e=>{if(e.key==='Escape'){e.stopPropagation();setOpen(false);}if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();setOpen(true);setActive(i=>Math.max(0,Math.min(matches.length-1,i+(e.key==='ArrowDown'?1:-1))));}if(e.key==='Enter'&&open&&matches[active]){e.preventDefault();pick(matches[active].symbol);}}}/>{open&&<div className="asset-results" id="asset-options" role="listbox" aria-label="ผลค้นหาสินทรัพย์"><div className="result-heading">{matches.length} สินทรัพย์</div>{matches.map((p,i)=><button key={p.symbol} id={`asset-${p.symbol}`} role="option" aria-selected={p.symbol===symbol} className={i===active?'active':''} onPointerMove={()=>setActive(i)} onClick={()=>pick(p.symbol)}><strong>{p.symbol}</strong><small>{p.assetClass.toUpperCase()}</small></button>)}{!matches.length&&<p className="empty-search">ไม่พบสินทรัพย์ ลองค้นหาด้วยชื่อคู่เงิน</p>}</div>}</div>;
}
function NewsRail({symbol,news,eventId,onEvent,highOnly,setHighOnly,inactive,day,onDay,source}){
 const visible=highOnly?news.filter(e=>e.impact==='high'):news;
 const groups=Object.values(visible.reduce((out,e)=>{const key=`${e.dayThai||thaiDay(e.time)}|${e.timeKind||e.timePrecision||'timed'}|${eventTime(e)}`;out[key]??={key,event:e,events:[]};out[key].events.push(e);return out;},{}));
 const coverage=source.availableDays?.find(entry=>entry.dayThai===day);
 const hasSnapshot=Boolean(source.lastSuccessAt),sourceProblem=!['ready','ok','fresh','empty','cached','partial'].includes(source.status);
 const covered=coverage?.fullyCovered===true;
 const dayCount=coverage?.count??getNewsForSymbol(null,day).length;
 const calendarCount=source.coverage?.cachedSourceCount??source.coverage?.sourceCount??source.calendarEvents?.length??0;
 const dayStatus=!hasSnapshot?sourceStatus(source):!coverage?'อยู่นอกช่วงข้อมูล':covered?'ครอบคลุมวันที่เลือก':'ครอบคลุมวันบางส่วน';
 const emptyTitle=!hasSnapshot?'ยังโหลดปฏิทินไม่สำเร็จ':!coverage?'วันที่นี้อยู่นอกช่วงข้อมูล':sourceProblem?'ยังยืนยันข่าวรอบล่าสุดไม่ได้':!covered?'ยังยืนยันข่าวครบวันไม่ได้':highOnly&&news.length?'ไม่มีข่าวสำคัญในตัวกรองนี้':symbol&&dayCount?'ไม่มีข่าวตรงกับสินทรัพย์ที่เลือก':'ไม่มีเหตุการณ์ในวันที่เลือก';
 const emptyNote=!hasSnapshot?'รอการเชื่อมต่อแหล่งข่าว':!coverage?'เลือกวันอื่นจากปฏิทิน โดยข้อมูลที่ดึงไว้ยังคงเปิดอ่านได้':sourceProblem?'แสดงเฉพาะข้อมูลรอบที่เก็บไว้ ตรวจสถานะแหล่งข่าวด้านบน':!covered?'แหล่งข้อมูลครอบคลุมวันนี้เพียงบางช่วง จึงไม่ถือว่าไม่มีข่าวทั้งวัน':highOnly&&news.length?'ปิดตัวกรองเพื่อดูทุกระดับความสำคัญ':symbol&&dayCount?'เลือกภาพรวมเพื่อดูข่าวทั้งหมดของวันนี้':'แหล่งข่าวส่งปฏิทินมาแล้ว และไม่มีรายการสำหรับวันนี้';
 return <aside className="news-rail" aria-label="ข่าวที่เกี่ยวข้อง" inert={inactive}>
  <header className="news-heading"><p className="eyebrow">YOUR DAILY BRIEFING</p><h1>{symbol?'ข่าวที่เกี่ยวข้อง':'ข่าวภาพรวม'} <span>{visible.length} เหตุการณ์</span></h1><h2>{symbol||'MARKET BRIEF'}<small>{symbol?(PAIRS.find(p=>p.symbol===symbol)?.assetClass==='forex'?`${symbol.slice(0,3)} + ${symbol.slice(3)}`:'ข่าว USD ที่เกี่ยวข้อง'):'เลือกดาวเพื่อกรองข่าว'}</small></h2><p className="time-zone"><IconClock size={15}/>เวลาไทย · Asia/Bangkok</p>
   <div className="news-date-controls"><label htmlFor="calendar-day" className="sr-only">วันที่ปฏิทินข่าว เวลาไทย</label><input id="calendar-day" type="date" value={day} onChange={e=>e.target.value&&onDay(e.target.value)}/><button onClick={()=>onDay(thaiDay())}>วันนี้</button></div>
   <div className="news-filter"><span className="sample-mini">{highOnly?'ข่าวสำคัญ':'ทุกระดับความสำคัญ'}</span><button aria-pressed={highOnly} onClick={()=>setHighOnly(v=>!v)}>เฉพาะข่าวสำคัญ</button></div>
   <div className="news-source-status" role="status"><a href={source.sourceUrl||'https://www.forexfactory.com/calendar'} target="_blank" rel="noopener noreferrer">{source.source||'Forex Factory'}<IconExternalLink size={11}/></a><span>{dayStatus}{sourceProblem&&hasSnapshot?` · ${sourceStatus(source)}`:''}</span><small>วันที่เลือก {dayCount} · ในช่วงที่ดึงไว้ {calendarCount} รายการ<br/>เป็นรายการจากแหล่งนี้ อาจไม่ครอบคลุมทุกข่าวตลาด</small></div>
   {source.error==='http_429'&&<p className="news-retry-notice">ต้นทางจำกัดการเรียก · ใช้ปฏิทินรอบที่เก็บไว้<br/>ลองใหม่ {formatThaiStamp(source.nextAttemptAt)} เวลาไทย</p>}
  </header>
  <div className="news-list">{groups.map(g=><section className="news-time-group" key={g.key}><div className="time-heading"><IconCircleFilled size={10}/><time dateTime={g.event.time||undefined}>{eventTime(g.event)}</time><span>{g.events.length>1?`${g.events.length} เหตุการณ์`:g.events[0].currency}</span></div><div className="events-at-time">{g.events.map(e=><button key={e.id} id={`news-${e.id}`} className={`news-event ${e.id===eventId?'selected':''}`} aria-expanded={e.id===eventId} aria-controls={e.id===eventId?'news-popover':undefined} onClick={()=>onEvent(e.id)}><span className="event-currency">{e.currency}</span><span className="event-title">{e.title}</span><span className={`impact ${e.impact}`} title={`ความสำคัญ ${e.impactLabel||'ไม่ระบุ'}`}><IconCircleFilled size={8}/><span className="sr-only">{e.impactLabel||'ไม่ระบุ'}</span></span></button>)}</div></section>)}{!visible.length&&<div className="empty-news"><IconNews size={28}/><h3>{emptyTitle}</h3><p>{emptyNote}</p></div>}</div>
  <footer className="news-round"><IconClock size={19}/><div>ปฏิทินอัปเดตวันละครั้ง<small>ดึงสำเร็จ {formatThaiStamp(source.lastSuccessAt)}<br/>กำหนดการที่เก็บไว้ อาจมีการเปลี่ยนภายหลัง</small></div></footer>
 </aside>;
}
function NewsPopover({event,symbol,onClose,onLearnMore,explainerOpen}){
 const close=useRef(null);useEffect(()=>{close.current?.focus({preventScroll:true});},[event.id]);const scenarios=symbol?getEventScenarios(event,symbol):[];
 const hasFigures=event.numeric||[event.forecast,event.previous].some(value=>value!==null&&value!==undefined&&value!=='—');
 return <section className="news-popover" id="news-popover" role={explainerOpen?"region":"dialog"} aria-modal={explainerOpen?undefined:false} aria-labelledby="news-title"><header><div className="popup-meta"><span className="currency-tag">{event.currency}</span><time dateTime={event.time||undefined}>{event.dayThai||thaiDay(event.time)} · {eventTime(event)} · ไทย</time></div><button ref={close} className="icon-button" aria-label="ปิดบทวิเคราะห์ข่าว" onClick={onClose}><IconX size={20}/></button></header><div className="popup-scroll"><h2 id="news-title">{event.title}</h2>{event.summary&&<p className="news-summary">{event.summary}</p>}<button id="news-learn-more" className="news-learn-more" aria-expanded={explainerOpen} aria-controls={explainerOpen?'news-explainer':undefined} onClick={onLearnMore}><IconInfoCircle size={16}/>อ่านเพิ่มเติม · ข่าวนี้หมายถึงอะไร</button>{hasFigures&&<div className="event-figures"><div><small>คาดการณ์</small><strong>{event.forecast??'—'}</strong></div><div><small>ครั้งก่อน</small><strong>{event.previous??'—'}</strong></div></div>}<p className="actual-status">ผลจริง: {event.actual===null||event.actual===undefined?'แหล่งนี้ไม่ส่งผลจริง':String(event.actual)}</p>{scenarios.length>0?<><div className="scenario-heading">ฉากทัศน์ต่อ <strong>{symbol}</strong><span>หากผลออกมา…</span></div><div className="scenario-list">{scenarios.map(s=><div className={`scenario ${s.direction}`} key={s.key}><div><span className="scenario-icon">{s.direction==='up'?<IconArrowUpRight size={18}/>:s.direction==='down'?<IconArrowDownRight size={18}/>:<IconMinus size={18}/>}</span><strong>{s.label}</strong></div><p>{s.summary}</p></div>)}</div><p className="scenario-note">{scenarios[0].note}<br/>ข่าวเดียวไม่พอสรุปทิศทางระยะยาว</p></>:<p className="overview-news-hint">{symbol?'ยังไม่มีฉากทัศน์ทิศทางที่รองรับสำหรับข่าวและสินทรัพย์นี้':'เลือกคู่เงินเพื่อดูฉากทัศน์ เมื่อข่าวมีตัวเลขคาดการณ์ที่รองรับ'}</p>}{event.datePrecisionNote&&<p className="scenario-note">{event.datePrecisionNote}</p>}</div><footer>{event.sourceUrl?<a href={event.sourceUrl} target="_blank" rel="noopener noreferrer">{event.sourceName}<IconExternalLink size={14}/></a>:<span>{event.sourceName||'ไม่ระบุแหล่งข่าว'}</span>}<span>ปฏิทินรอบรายวัน</span></footer></section>;
}
function NewsExplainer({event,onClose}) {
 const close=useRef(null),info=getNewsExplainer(event);
 useEffect(()=>{close.current?.focus({preventScroll:true});if(matchMedia('(max-width:740px)').matches)close.current?.closest('.news-explainer')?.scrollIntoView({block:'nearest'});},[event.id]);
 return <aside className="news-explainer" id="news-explainer" role="region" aria-labelledby="explainer-title">
  <header><div><p className="eyebrow">UNDERSTAND THE EVENT</p><h2 id="explainer-title">{info.title}</h2></div><button ref={close} className="icon-button" aria-label="ปิดคำอธิบายข่าว" onClick={onClose}><IconX size={19}/></button></header>
  <div className="explainer-points">{info.lines.map((line,i)=><p key={i}><span>{String(i+1).padStart(2,'0')}</span>{line}</p>)}</div>
  <footer><a href={info.sourceUrl} target="_blank" rel="noopener noreferrer">{info.sourceName}<IconExternalLink size={14}/></a><small>คำอธิบายตัวชี้วัด · ตรวจผลจริงจากแหล่งประกาศ</small></footer>
 </aside>;
}
function NewsReader({event,symbol,explainerOpen,onClose,onLearnMore,onCloseExplainer,embedded=false}) {
 const panels=useRef(null);
 useEffect(()=>{if(!explainerOpen||embedded)return;const old=document.body.style.overflow;document.body.style.overflow='hidden';return()=>{document.body.style.overflow=old;};},[explainerOpen,embedded]);
 const keepReadingFocus=e=>{
  if(!explainerOpen||e.key!=='Tab')return;
  const items=[...panels.current.querySelectorAll('button:not(:disabled),a[href],[tabindex="0"]')].filter(el=>el.getClientRects().length);
  const first=items[0],last=items.at(-1);
  if(e.shiftKey&&panels.current.getRootNode().activeElement===first){e.preventDefault();last?.focus();}
  else if(!e.shiftKey&&panels.current.getRootNode().activeElement===last){e.preventDefault();first?.focus();}
 };
 return <div className={`news-reading-layer ${explainerOpen?'is-expanded':''}`}>
  {explainerOpen&&<button className="news-reading-backdrop" aria-label="ปิดอ่านเพิ่มเติมและกลับสู่ข่าว" tabIndex={-1} onClick={onCloseExplainer}/>}
  <div ref={panels} className="news-reading-panels" role={explainerOpen?'dialog':undefined} aria-modal={explainerOpen||undefined} aria-label={explainerOpen?'อ่านข่าวและคำอธิบายเพิ่มเติม':undefined} onKeyDown={keepReadingFocus}>
   <NewsPopover event={event} symbol={symbol} onClose={onClose} explainerOpen={explainerOpen} onLearnMore={onLearnMore}/>
   {explainerOpen&&<NewsExplainer event={event} onClose={onCloseExplainer}/>}
  </div>
 </div>;
}
function SentimentCard({pair,source}) {
 const s=getSentiment(pair.symbol), tone=getSentimentColor(s);
 const total=s.long+s.short,visualLong=s.available?s.long/total*100:null;
 const price=v=>typeof v==='number'&&Number.isFinite(v)?v.toFixed(pair.assetClass==='metals'||pair.assetClass==='oil'?2:pair.symbol.endsWith('JPY')?3:5):'—';
 return <section className="sentiment-card" aria-label={`Sentiment ${pair.symbol}`}>
  <header><IconUsers size={19}/><div><h2>COMMUNITY SENTIMENT</h2><small>Myfxbook · {sourceStatus(source)}</small></div></header>
  {s.available?<><div className="sentiment-ratio"><div className="short"><small>SHORT</small><strong>{s.short}<span>%</span></strong></div><div className="ratio-caption">สัดส่วนสถานะ<br/>ของชุมชน</div><div className="long"><small>LONG</small><strong>{s.long}<span>%</span></strong></div></div>
  <div className="average-prices"><div><small>ราคา Short เฉลี่ย</small><strong className="short">{price(s.avgShort)}</strong></div><div><small>ราคา Long เฉลี่ย</small><strong className="long">{price(s.avgLong)}</strong></div></div></>:<div className="no-sentiment"><IconInfoCircle size={22}/><strong>ยังไม่มีข้อมูล Sentiment</strong><span>ไม่แทนค่าที่ขาดหายด้วย Short/Long 50/50</span></div>}
  {s.available&&<div className="stellar-color-key" aria-label="ระดับสีดาวตามสัดส่วน Sentiment"><div className="stellar-color-scale" style={{background:SENTIMENT_GRADIENT}}><i style={{left:`${visualLong}%`,background:tone.color}}/></div><div><span>SHORT 100%</span><span>50 / 50</span><span>LONG 100%</span></div></div>}
  {s.available&&Math.abs(total-100)>.000001&&<p className="rounding-note">ตัวเลขจากแหล่งข้อมูลรวม {total}% จากการปัดเศษ · ปรับเฉพาะตำแหน่งสีให้ครบ 100%</p>}
  <div className="sentiment-source-meta"><span>ดึงสำเร็จ {formatThaiStamp(source.lastSuccessAt)}</span>{s.available&&<span>ข้อมูลรายการนี้ {formatThaiStamp(s.asOf)}</span>}{s.available&&s.avgLong===null&&s.avgShort===null&&<span>แหล่งข้อมูลไม่มีราคาเฉลี่ยของรายการนี้</span>}</div>
  <p>สีดาว = สัดส่วนสถานะของชุมชน ไม่ใช่แนวโน้มราคา</p>
 </section>;
}
function StellarInspector({pair,motionClock,playing,speed,connection,onClose,onClearConnection,onSelect,relatedCount,correlationsVisible,filter,onConnectionSelect,dataRevision,market}) {
 const scroll=useRef(null);
 useEffect(()=>{if(scroll.current)scroll.current.scrollTop=0;},[pair.symbol]);
 const rows=getCorrelations(pair.symbol).filter(row=>filter==='all'||PAIRS.find(p=>p.symbol===row.symbol)?.assetClass===filter);
 const selectedCounterpart=connection&&(connection.source===pair.symbol?connection.target:connection.source);
 return <aside className="stellar-inspector" aria-label={`รายละเอียด ${pair.symbol}`}>
  <header className="inspector-heading"><div><p className="eyebrow">STELLAR OBSERVATORY</p><h2>{pair.symbol}<span>{pair.assetClass.toUpperCase()}</span></h2></div><button className="icon-button" aria-label="ปิดรายละเอียดดาว" onClick={onClose}><IconX size={19}/></button></header>
  <div className="inspector-scroll" ref={scroll}><div className="stellar-hero"><SentimentPreview symbol={pair.symbol} motionClock={motionClock} playing={playing} motionSpeed={speed} dataRevision={dataRevision}/><span className="stellar-caption">{pair.name}</span></div>
   <SentimentCard pair={pair} source={market.sentiment}/>
   <section className="connection-detail" aria-label="รายละเอียดเส้น Correlation"><div className="connection-title"><IconLink size={16}/><h3>CORRELATION</h3>{connection&&<button className="icon-button" aria-label="ล้างเส้นที่เลือก" onClick={onClearConnection}><IconX size={15}/></button>}</div>
    {connection?<><div className="connection-pair"><button onClick={()=>onSelect(connection.source)}>{connection.source}</button><IconLink size={15}/><button onClick={()=>onSelect(connection.target)}>{connection.target}</button></div><div className={`connection-value ${correlationTone(connection.value)}`} style={{color:correlationColor(connection.value)}}><strong>{connection.value>=0?'+':''}{Math.round(connection.value*100)}<small>%</small></strong><span>{correlationTone(connection.value)==='neutral'?'สัมพันธ์อ่อน / ใกล้ศูนย์':connection.value>0?'สัมพันธ์ในทิศทางเดียวกัน':'สัมพันธ์ในทิศทางตรงข้าม'}</span></div><p>MT5 · Pearson จากผลตอบแทน H1 ที่ปิดแล้ว<br/>{connection.samples} ช่วงตรงกัน · สิ้นสุด {formatThaiStamp(connection.endAt)}</p></>:<p className="connection-empty">{correlationsVisible?<>เน้น {relatedCount} เส้นที่มีข้อมูลของ {pair.symbol}<br/>{relatedCount?'กดชื่อบนเส้น หรือเลือกจากรายการด้านล่าง':'ยังไม่มีราคาที่เพียงพอและตรงช่วงเวลา'}</>:<>ซ่อนเส้นอยู่ · เปิด Correlation<br/>เพื่อดูความสัมพันธ์กับดาวอื่น</>}</p>}
    <p className="correlation-source-meta">MT5 · {sourceStatus(market.correlations)}{market.correlations.marketStatus==='market_closed'?' · ตลาดปิด':''}<br/>แท่งข้อมูลล่าสุด {formatThaiStamp(market.correlations.asOf)}</p>
    <div className="correlation-list-heading"><strong>คู่ที่สัมพันธ์ <span>{rows.length}</span></strong><small>เรียงตามความสัมพันธ์มาก → น้อย</small></div>
    <div key={`${pair.symbol}:${filter}`} className="correlation-list" role="region" aria-label={`รายการ Correlation ของ ${pair.symbol}`} tabIndex={0}>
     {rows.map(row=><button key={row.symbol} className={`correlation-row ${correlationTone(row.value)}`} style={{'--correlation-color':correlationColor(row.value)}} aria-label={`${pair.symbol} กับ ${row.symbol} ${row.value>=0?'+':''}${Math.round(row.value*100)}%`} aria-pressed={selectedCounterpart===row.symbol} onClick={()=>onConnectionSelect({source:pair.symbol,target:row.symbol,value:row.value})}><span className="correlation-symbol">{row.symbol}</span><span className="correlation-meter"><i style={{width:`${Math.abs(row.value)*100}%`}}/></span><strong>{row.value>=0?'+':''}{Math.round(row.value*100)}%</strong></button>)}
    </div><p className="list-scroll-hint">{rows.length?'กดคู่ที่มีข้อมูลเพื่อเน้นเส้นบนกาแล็กซี่':'ไม่มีเส้นที่คำนวณได้สำหรับสินทรัพย์นี้'}</p>
   </section>
   <p className="inspector-note"><span className="gold-key">จุดสีทอง</span> = ดาวที่เชื่อมกับดาวที่เลือก<br/>แสงวิ่งบนเส้นเมื่อ Correlation &gt; +70% หรือ &lt; −70%<br/>ความสัมพันธ์ย้อนหลัง ไม่ใช่การคาดการณ์ราคา<br/>โมชั่นใช้ประกอบภาพ ไม่ใช่คำสั่งซื้อขาย</p>
  </div>
 </aside>;
}
export function App({assetBase='/',marketUrl='/api/market',setupUrl='/connect',embedded=false,requireHeartbeat=false}={}) {
 const appRoot=useRef(null);
 const market=useMarketData({marketUrl,requireHeartbeat});
 const[symbol,setSymbol]=useState(null),[filter,setFilter]=useState('all'),[eventId,setEventId]=useState(null),[highOnly,setHighOnly]=useState(false);
 const[day,setDay]=useState(()=>thaiDay()),previousToday=useRef(thaiDay());
 const[playing,setPlaying]=useState(true),[speed,setSpeed]=useState(1),[reduced,setReduced]=useState(()=>matchMedia('(prefers-reduced-motion: reduce)').matches);
 const[correlationsVisible,setCorrelationsVisible]=useState(true),[resetKey,setResetKey]=useState(0),[status,setStatus]=useState('loading'),[settings,setSettings]=useState(false);
 const[inspectorOpen,setInspectorOpen]=useState(false),[connection,setConnection]=useState(null),[explainerOpen,setExplainerOpen]=useState(false);
 const motionClock=useRef({value:0}),pair=PAIRS.find(p=>p.symbol===symbol)||null,news=useMemo(()=>getNewsForSymbol(symbol,day),[symbol,day,market.revision]);
 const availableEdges=useMemo(()=>getAvailableEdges(filter),[filter,market.revision]);
 const liveConnection=connection?availableEdges.find(edge=>(edge.source===connection.source&&edge.target===connection.target)||(edge.source===connection.target&&edge.target===connection.source))||null:null;
 const {displayPair,expanded}=useInspectorPresence(inspectorOpen,pair,reduced);
 const event=news.find(e=>e.id===eventId);
 const reading=Boolean(event&&explainerOpen);
 const visibleCount=PAIRS.filter(p=>filter==='all'||p.assetClass===filter).length,possibleEdges=visibleCount*(visibleCount-1)/2,edgeCount=availableEdges.length;
 const relatedCount=availableEdges.filter(edge=>edge.source===symbol||edge.target===symbol).length;
 const missingSymbols=(market.correlations.instruments||[]).filter(item=>item.status==='missing').map(item=>item.symbol);
 const changeDay=value=>{setDay(value);setEventId(null);setExplainerOpen(false);};
 const pick=useCallback(value=>{setSymbol(value);setInspectorOpen(true);setConnection(null);setEventId(null);setExplainerOpen(false);setFilter(current=>current!=='all'&&PAIRS.find(p=>p.symbol===value)?.assetClass!==current?'all':current);},[]);
 const pickConnection=useCallback(value=>{setSymbol(current=>current===value.source||current===value.target?current:value.source);setConnection(value);setInspectorOpen(true);setCorrelationsVisible(true);setEventId(null);setExplainerOpen(false);},[]);
 const closeNews=useCallback(()=>{const id=event?.id;setEventId(null);setExplainerOpen(false);requestAnimationFrame(()=>appRoot.current?.getRootNode().getElementById(`news-${id}`)?.focus({preventScroll:true}));},[event?.id]);
 const closeExplainer=useCallback(()=>{setExplainerOpen(false);requestAnimationFrame(()=>appRoot.current?.getRootNode().getElementById('news-learn-more')?.focus({preventScroll:true}));},[]);
 const closeInspector=useCallback(()=>{setInspectorOpen(false);requestAnimationFrame(()=>appRoot.current?.getRootNode().getElementById('open-stellar-inspector')?.focus({preventScroll:true}));},[]);
 const ready=useCallback(()=>setStatus('ready'),[]),error=useCallback(()=>setStatus('error'),[]);
 const changeFilter=value=>{setFilter(value);setConnection(null);if(pair&&value!=='all'&&pair.assetClass!==value){setSymbol(null);setInspectorOpen(false);setEventId(null);setExplainerOpen(false);}};
 const reset=()=>{setFilter('all');setSymbol(null);setInspectorOpen(false);setConnection(null);setEventId(null);setExplainerOpen(false);setSettings(false);setCorrelationsVisible(true);setResetKey(k=>k+1);setPlaying(true);};
 useEffect(()=>{const today=thaiDay(),previous=previousToday.current;if(today!==previous){setDay(current=>current===previous?today:current);previousToday.current=today;}},[market.revision]);
 useEffect(()=>{const media=matchMedia('(prefers-reduced-motion: reduce)'),listener=e=>setReduced(e.matches);media.addEventListener('change',listener);return()=>media.removeEventListener('change',listener);},[]);
 useEffect(()=>{if(!embedded)document.title='Metafxclub · Sentiment Universe';},[embedded]);
 const handleKey=e=>handleUniverseKey(e,{embedded,root:appRoot.current,explainerOpen,eventOpen:Boolean(event),settingsOpen:settings,inspectorOpen,closeExplainer,closeNews,closeSettings:()=>setSettings(false),closeInspector,toggleMotion:()=>setPlaying(p=>!p)});
 const serviceProblem=['offline','stale'].includes(market.connection);
 const setupNeeded=[market.sentiment,market.correlations].some(source=>['needs_configuration','auth_error','auth_failed','authentication_failed'].includes(source.status));
 const serviceMessage=market.connection==='stale'?'บริการข้อมูลหยุดอัปเดต · แสดงข้อมูลรอบที่เก็บไว้':market.connection==='offline'?'ยังเชื่อมบริการข้อมูลไม่ได้ · แสดงข้อมูลรอบที่เก็บไว้':'เชื่อมบัญชี Myfxbook และเลือก MT5 ของเครื่องนี้ครั้งแรก';
 return <div ref={appRoot} onKeyDown={handleKey} className={`app-shell ${reduced?'reduce-motion':''}`}>
  <header className="app-header" inert={reading}><a className="brand" href="#universe" aria-label="Metafxclub กลับภาพรวม" onClick={e=>{e.preventDefault();reset();}}><img src={assetUrl(assetBase,'metafx-mark.png')} alt=""/><span>METAFXCLUB</span></a><div className="product-title">SENTIMENT UNIVERSE</div><div className="asset-filters" role="group" aria-label="กรองกลุ่มสินทรัพย์">{FILTERS.map(([key,label,count])=><button key={key} className={filter===key?'current':''} aria-pressed={filter===key} onClick={()=>changeFilter(key)}>{label} <span>{count}</span></button>)}</div><AssetSearch symbol={symbol} onSelect={pick}/><a className="demo-badge live-connect" href={setupUrl} target="_blank" rel="noopener noreferrer" title={`Myfxbook · ${sourceStatus(market.sentiment)}`}>ตั้งค่า Myfxbook / MT5 <IconExternalLink size={12}/></a></header>
  <main className={`app-main ${expanded?'has-inspector':''}`} id="universe">
   <NewsRail inactive={reading} symbol={symbol} news={news} eventId={event?.id} onEvent={id=>{setEventId(id===event?.id?null:id);setExplainerOpen(false);}} highOnly={highOnly} setHighOnly={setHighOnly} day={day} onDay={changeDay} source={market.news}/>
   <div className="galaxy-stage" inert={reading}><div className="scene-host" tabIndex={-1}><OrbitalScene assetBase={assetBase} pairs={PAIRS} selectedSymbol={symbol} filter={filter} axis="free" reducedMotion={reduced} playing={playing&&!reduced} motionSpeed={speed} motionClock={motionClock} resetKey={resetKey} correlationsVisible={correlationsVisible} selectedCorrelation={liveConnection} dataRevision={market.revision} onCorrelationSelect={pickConnection} onSelect={pick} onReady={ready} onError={error}/></div>
    {(serviceProblem||setupNeeded)&&<section className="connection-notice" aria-label="สถานะแหล่งข้อมูล"><div role="status"><strong>{serviceMessage}</strong>{serviceProblem&&<small>ตรวจบริการในเครื่อง · ข้อมูลต้นทางสำเร็จล่าสุด Myfxbook {formatThaiStamp(market.sentiment.lastSuccessAt)}</small>}</div><a href={setupUrl} target="_blank" rel="noopener noreferrer">เปิดการตั้งค่า <IconExternalLink size={13}/></a></section>}
    {status!=='ready'&&<div className="scene-status" role="status">{status==='error'?'เปิดมุมมอง 3D ไม่สำเร็จ ยังเลือกสินทรัพย์จากช่องค้นหาได้':'กำลังเตรียมกาแล็กซี่…'}</div>}
    <div className="scene-topbar">{pair?<button id="open-stellar-inspector" className="view-label" aria-label={`เปิดรายละเอียด ${symbol}`} aria-expanded={inspectorOpen} onClick={()=>setInspectorOpen(true)}>{pair.clusterId} / <strong>{symbol}</strong></button>:<div className="view-label overview-label">ภาพรวม <strong>{visibleCount} สินทรัพย์</strong></div>}<div className="view-tools"><button className="tool-button" aria-pressed={correlationsVisible} onClick={()=>{setCorrelationsVisible(v=>!v);setConnection(null);}}><IconLink size={16}/>Correlation <span>{correlationsVisible?edgeCount:0}</span></button><button className="icon-button" aria-label={playing&&!reduced?'หยุดโมชั่นทั้งหมด':'เริ่มโมชั่น'} disabled={reduced} onClick={()=>setPlaying(v=>!v)}>{playing&&!reduced?<IconPlayerPause size={19}/>:<IconPlayerPlay size={19}/>}</button><button className="icon-button" aria-label="ตั้งค่าการเคลื่อนไหว" aria-expanded={settings} onClick={()=>setSettings(v=>!v)}><IconAdjustmentsHorizontal size={19}/></button></div></div>
    {settings&&<section className="view-settings" aria-label="ตั้งค่าการเคลื่อนไหว"><header><strong>การเคลื่อนไหว</strong><button className="icon-button" aria-label="ปิดการตั้งค่า" onClick={()=>setSettings(false)}><IconX size={18}/></button></header><label>ความเร็ว<select aria-label="ความเร็วโมชั่น" value={speed} onChange={e=>setSpeed(Number(e.target.value))}><option value="0.5">0.5×</option><option value="1">1×</option><option value="1.8">1.8×</option></select></label><label>ลดการเคลื่อนไหว<input type="checkbox" checked={reduced} onChange={e=>setReduced(e.target.checked)}/></label><p>โมชั่นเป็นภาพประกอบ ไม่ใช่การส่งคำสั่งเทรด</p></section>}
    <div className="scene-bottom"><div className="camera-controls" role="group" aria-label="ควบคุมมุมมอง"><button className="reset-overview" aria-label="รีเซต กลับภาพรวมไม่เลือกสินทรัพย์" onClick={reset}><IconRotateClockwise size={17}/><span>รีเซต</span></button></div><span className="scene-hint">ลากซ้ายหมุน · ลากขวาเลื่อน · ล้อเมาส์ซูม</span></div>
    {correlationsVisible&&<div className="correlation-legend" aria-label="คำอธิบายสีเส้น Correlation"><span><IconLink size={14}/>{symbol?`${symbol} · เน้น ${relatedCount} / ${edgeCount} เส้น`:`คำนวณได้ ${edgeCount} / ${possibleEdges} เส้น`}</span><div className="correlation-color-bands">
     <b style={{color:correlationColor(0)}}><i style={{background:correlationColor(0)}}/>เหลือง −30% ถึง +30%</b><small>ใกล้ 0% ช่วง ±10% สว่างขึ้น</small>
     <b style={{color:correlationColor(.6)}}><i style={{background:correlationColor(.6)}}/>เขียว +40 ถึง &lt;80%</b><b style={{color:correlationColor(.9)}}><i style={{background:correlationColor(.9)}}/>เข้ม +80 ถึง +100%</b>
     <b style={{color:correlationColor(-.6)}}><i style={{background:correlationColor(-.6)}}/>แดง −40 ถึง &gt;−80%</b><b style={{color:correlationColor(-.9)}}><i style={{background:correlationColor(-.9)}}/>เข้ม −80 ถึง −100%</b>
    </div><small>ช่วง ±30–40% ไล่สีต่อเนื่อง</small><small>{symbol?'จุดทอง = ดาวที่เชื่อมกับดาวที่เลือก':'เน้นเส้นที่ความสัมพันธ์ตั้งแต่ ±60%'}</small><small>แสงวิ่งเฉพาะ &gt; +70% หรือ &lt; −70%</small><small className="live-correlation-status">MT5 · {sourceStatus(market.correlations)}{market.correlations.marketStatus==='market_closed'?' · ตลาดปิด':''}<br/>H1 ล่าสุด {formatThaiStamp(market.correlations.asOf)}{missingSymbols.length>0&&<><br/>{missingSymbols.join(', ')} ยังไม่มีข้อมูล H1 ที่ใช้คำนวณจาก MT5</>}</small></div>}
   </div>
   <div className={`inspector-dock ${expanded?'is-open':''}`} aria-hidden={!inspectorOpen||reading} inert={!inspectorOpen||reading} data-state={expanded?'open':displayPair?'closing':'closed'}>{displayPair&&<StellarInspector pair={displayPair} motionClock={motionClock} playing={playing&&!reduced&&inspectorOpen} speed={speed} connection={liveConnection} dataRevision={market.revision} market={market} onClose={closeInspector} onClearConnection={()=>setConnection(null)} onSelect={pick} relatedCount={relatedCount} correlationsVisible={correlationsVisible} filter={filter} onConnectionSelect={pickConnection}/>}</div>
   {event&&<NewsReader embedded={embedded} event={event} symbol={symbol} explainerOpen={explainerOpen} onClose={closeNews} onLearnMore={()=>setExplainerOpen(v=>!v)} onCloseExplainer={closeExplainer}/>}
  </main>
  <footer className="app-footer" inert={reading}><span><IconInfoCircle size={15}/>คลิกดาวดูเส้นเชื่อม · ลากซ้ายหมุน · ลากขวาเลื่อน · ล้อเมาส์ซูม</span><span className="live-flow-status" role="status">{serviceProblem?serviceMessage:market.connection==='loading'?'กำลังเชื่อมบริการข้อมูล':`Myfxbook ${sourceStatus(market.sentiment)} · MT5 ${market.correlations.coverage?.available??0}/32 · ปฏิทิน ${market.news.status==='empty'?'พร้อม':sourceStatus(market.news)}`} · ไม่มีการส่งคำสั่งเทรด</span></footer><div className="sr-only" aria-live="polite">{symbol?`เลือก ${symbol}`:'ภาพรวม ยังไม่เลือกสินทรัพย์'} มีข่าว {news.length} เหตุการณ์</div>
 </div>;
}
