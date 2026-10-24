import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { IconChevronDown, IconCircle, IconCircleFilled, IconFocus2, IconInfoCircle, IconMaximize, IconMinimize, IconMouse, IconPlayerPause, IconPlayerPlay, IconRotateClockwise, IconSearch, IconSettings, IconStar, IconStarFilled, IconX } from '@tabler/icons-react';
import '@fontsource/rajdhani/400.css';
import '@fontsource/rajdhani/500.css';
import '@fontsource/rajdhani/600.css';
import '@fontsource/rajdhani/700.css';
import '@fontsource/sarabun/400.css';
import '@fontsource/sarabun/500.css';
import '@fontsource/sarabun/600.css';
import { OrbitalScene } from './OrbitalScene.jsx';
import { NucleusPreview } from './NucleusPreview.jsx';
import { PAIRS, STATE_META, HORIZONS } from './data.js';

const RING_NAMES = ['วงโคจรสั้น', 'วงโคจรกลาง', 'วงโคจรยาว'];
const HORIZON_NAMES = ['สั้น', 'กลาง', 'ยาว'];
const FILTERS = [{ key: 'all', label: 'ทั้งหมด' }, { key: 'forex', label: 'Forex' }, { key: 'metals', label: 'Metals' }, { key: 'oil', label: 'Oil' }];

function useCanvas(draw, dependencies) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return undefined;
    const paint = () => {
      const { width, height } = canvas.getBoundingClientRect();
      if (width < 1 || height < 1) return;
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
      const context = canvas.getContext('2d');
      if (!context) return;
      context.setTransform(ratio, 0, 0, ratio, 0, 0); context.clearRect(0, 0, width, height);
      draw(context, width, height);
    };
    const observer = new ResizeObserver(paint);
    observer.observe(canvas); paint();
    return () => observer.disconnect();
  }, dependencies);
  return ref;
}

function HorizonRing({ state, index }) {
  const ref = useCanvas((context, width, height) => {
    const cx = width / 2, cy = height / 2, radius = Math.min(width, height) * .32;
    context.strokeStyle = '#224456'; context.lineWidth = .8; context.beginPath(); context.arc(cx, cy, radius + 7, 0, Math.PI * 2); context.stroke();
    context.strokeStyle = STATE_META[state]?.color || STATE_META.unknown.color; context.lineWidth = 2.5;
    if (state === 'unknown') context.setLineDash([3, 4]);
    context.beginPath(); context.arc(cx, cy, radius, 0, Math.PI * 2); context.stroke(); context.setLineDash([]);
    context.lineWidth = 2; context.beginPath(); context.arc(cx, cy, radius + 7, -Math.PI / 2, -Math.PI / 2 + (index + 1) * .38); context.stroke();
  }, [state, index]);
  return <canvas className="horizon-ring" ref={ref} aria-hidden="true" />;
}

function Sparkline({ values, state, horizon, symbol }) {
  const color = STATE_META[state]?.color || '#91a7bb';
  const ref = useCanvas((context, width, height) => {
    context.strokeStyle = '#0b1d2a'; context.lineWidth = 0.45;
    for (let x = 0; x <= width; x += 20) { context.beginPath(); context.moveTo(x, 0); context.lineTo(x, height); context.stroke(); }
    for (let y = 0; y <= height; y += 15) { context.beginPath(); context.moveTo(0, y); context.lineTo(width, y); context.stroke(); }
    if (state === 'unknown' || !values?.length) {
      context.fillStyle = color; context.font = '12px Sarabun, sans-serif'; context.textAlign = 'center';
      context.fillText('ยังไม่มีข้อมูลตัวอย่าง', width / 2, height / 2 + 4); return;
    }
    const minimum = Math.min(...values), span = Math.max(Math.max(...values) - minimum, 1);
    const points = values.map((value, index) => [(index / Math.max(values.length - 1, 1)) * width, height - 7 - ((value - minimum) / span) * (height - 14)]);
    context.beginPath(); context.moveTo(points[0][0], height); points.forEach(([x, y]) => context.lineTo(x, y));
    context.lineTo(width, height); context.closePath(); context.fillStyle = `${color}12`; context.fill();
    context.beginPath(); points.forEach(([x, y], index) => index ? context.lineTo(x, y) : context.moveTo(x, y));
    context.strokeStyle = color; context.lineWidth = 1.5; context.shadowColor = color; context.shadowBlur = 4; context.stroke();
  }, [values, state]);
  return <canvas ref={ref} className="sparkline" role="img" aria-label={`กราฟจำลอง ${symbol} ระยะ${horizon} ${STATE_META[state]?.labelThai || 'ไม่มีข้อมูล'} ไม่ใช่ราคาจริง`} />;
}

function PairPicker({ selectedSymbol, onSelect, favorites, inputRef }) {
  const [open, setOpen] = useState(false), [query, setQuery] = useState(''), [favoritesOnly, setFavoritesOnly] = useState(false), [activeIndex, setActiveIndex] = useState(0);
  const wrapper = useRef(null);
  const matches = useMemo(() => PAIRS.filter((pair) => (!favoritesOnly || favorites.has(pair.symbol)) && `${pair.symbol} ${pair.name}`.toLowerCase().includes(query.trim().toLowerCase())), [query, favoritesOnly, favorites]);
  useEffect(() => setActiveIndex(0), [query, favoritesOnly, favorites]);
  useEffect(() => {
    const close = (event) => { if (!wrapper.current?.contains(event.target)) setOpen(false); };
    document.addEventListener('pointerdown', close); return () => document.removeEventListener('pointerdown', close);
  }, []);
  useEffect(() => { if (open) document.getElementById(`pair-option-${matches[activeIndex]?.symbol}`)?.scrollIntoView({ block: 'nearest' }); }, [activeIndex, open]);
  const select = (symbol) => { onSelect(symbol); inputRef.current?.focus(); setOpen(false); setQuery(''); };
  const onKeyDown = (event) => {
    if (event.key === 'Escape' && open) { setOpen(false); event.stopPropagation(); }
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') { event.preventDefault(); setOpen(true); setActiveIndex((index) => Math.max(0, Math.min(matches.length - 1, index + (event.key === 'ArrowDown' ? 1 : -1)))); }
    if (event.key === 'Enter' && open && matches[activeIndex]) { event.preventDefault(); select(matches[activeIndex].symbol); }
  };
  return <div className="pair-picker" ref={wrapper}>
    <div className={`search-field ${open ? 'is-open' : ''}`}><IconSearch size={20} stroke={1.5} aria-hidden="true" />
      <input ref={inputRef} value={query} onChange={(event) => { setQuery(event.target.value); setOpen(true); }} onFocus={() => setOpen(true)} onKeyDown={onKeyDown} aria-label={`ค้นหาสินทรัพย์ ${PAIRS.length} รายการ`} placeholder="ค้นหาสินทรัพย์" role="combobox" aria-autocomplete="list" aria-expanded={open} aria-controls={open ? 'pair-options' : undefined} aria-activedescendant={open && matches[activeIndex] ? `pair-option-${matches[activeIndex].symbol}` : undefined} autoComplete="off" spellCheck="false" />
      <button className="search-toggle" aria-label={open ? 'ปิดรายการสินทรัพย์' : 'เปิดรายการสินทรัพย์'} aria-expanded={open} onClick={() => setOpen((value) => !value)}><IconChevronDown size={15} stroke={1.8} aria-hidden="true" /></button>
    </div>
    {open && <div className="pair-menu"><div className="pair-menu-heading"><span>{matches.length} / {PAIRS.length} สินทรัพย์</span><button aria-pressed={favoritesOnly} onClick={() => setFavoritesOnly((value) => !value)}><IconStar size={14} aria-hidden="true" /> ที่ติดดาว</button></div>
      <div className="pair-options" id="pair-options" role="listbox" aria-label="สินทรัพย์ทั้งหมด">{matches.map((pair, index) => <button type="button" id={`pair-option-${pair.symbol}`} key={pair.symbol} role="option" aria-selected={selectedSymbol === pair.symbol} tabIndex={-1} className={`pair-option ${index === activeIndex ? 'is-active' : ''}`} onPointerMove={() => setActiveIndex(index)} onClick={() => select(pair.symbol)}>
        <span><strong>{pair.symbol}</strong><small>{pair.name}</small></span><span className="pair-dots" aria-hidden="true">{pair.states.map((state, i) => <IconCircleFilled key={i} size={7} style={{ color: STATE_META[state]?.color }} />)}</span>
      </button>)}{!matches.length && <div className="pair-empty"><p>{favoritesOnly ? 'ยังไม่มีสินทรัพย์ที่ติดดาวตรงกับคำค้น' : 'ไม่พบสินทรัพย์ที่ตรงกับคำค้น'}</p><button onClick={() => { setQuery(''); setFavoritesOnly(false); }}>แสดงทั้งหมด {PAIRS.length} สินทรัพย์</button></div>}</div><div className="pair-menu-foot">ค้นหาทุกกลุ่ม · สีเรียงตามระยะสั้น กลาง ยาว</div>
    </div>}
  </div>;
}

function PreviewDialog({ type, onClose, reducedMotion, onReducedMotionChange, motionSpeed, onMotionSpeedChange, fullscreen, onFullscreen }) {
  const ref = useRef(null);
  useEffect(() => { const dialog = ref.current; dialog?.showModal(); return () => dialog?.close(); }, []);
  return <dialog className="preview-dialog" ref={ref} aria-labelledby="dialog-title" onCancel={onClose} onClick={(event) => { if (event.target === ref.current) onClose(); }}><section className="dialog-content">
    <header><div><span className="eyebrow">CONSTELLATION ARCHIPELAGO</span><h2 id="dialog-title">{type === 'settings' ? 'ตั้งค่ามุมมอง' : 'สำรวจ Market Universe'}</h2></div><button className="icon-button" aria-label="ปิดหน้าต่าง" onClick={onClose}><IconX size={22} /></button></header>
    {type === 'settings' ? <><label className="setting-row"><span><strong>ความเร็วโมชั่น</strong><small>ปรับการหมุน ดาวเคลื่อนที่ และแสงบนเส้นเชื่อมพร้อมกัน</small></span><select aria-label="ความเร็วโมชั่น" value={motionSpeed} onChange={(event) => onMotionSpeedChange(Number(event.target.value))}><option value="0.5">นุ่มนวล · 0.5×</option><option value="1">ต่อเนื่อง · 1×</option><option value="1.8">คึกคัก · 1.8×</option></select></label><label className="setting-row"><span><strong>ลดการเคลื่อนไหว</strong><small>หยุดโมชั่นทุกชั้น ยังลากสำรวจและเลือกสินทรัพย์ได้</small></span><input type="checkbox" checked={reducedMotion} onChange={(event) => onReducedMotionChange(event.target.checked)} /></label><button className="dialog-action" onClick={onFullscreen}>{fullscreen ? <IconMinimize size={19} /> : <IconMaximize size={19} />}{fullscreen ? 'ออกจากเต็มหน้าจอ' : 'เปิดเต็มหน้าจอ'}</button><p className="dialog-note">แกน X / Y / Z ควบคุมมุมมองเท่านั้น ตำแหน่งและระยะห่างของดาวไม่ได้แทนค่าทางการเงิน</p></>
      : <><p>สำรวจ {PAIRS.length} สินทรัพย์ในกลุ่ม Forex, Metals และ Oil คลิกดาวหรือค้นหาเพื่อเปิดแผงรายละเอียดด้านข้าง พร้อมนิวเคลียสขยายและวงโคจรไขว้สามช่วงเวลา บนมือถือแผงจะอยู่ใต้ฉาก กราฟระยะสั้น กลาง และยาวยังอยู่ด้านล่าง ฉากและจุดบนวงโคจรเคลื่อนไหวต่อระหว่างอ่าน กดพักเพื่อหยุดโมชั่นทั้งหมด หรือปรับความเร็วในตั้งค่ามุมมอง</p><div className="help-rows"><span>คลิกดาว / ชื่อ</span><strong>เปิดรายละเอียดสินทรัพย์</strong><span>Esc / ปุ่มปิดแผง</span><strong>กลับไปสำรวจ โดยคงสินทรัพย์ที่เลือก</strong><span>คลิกขวาค้างแล้วลาก</span><strong>หมุนมุมมอง</strong><span>เลื่อนล้อเมาส์</span><strong>ซูมเข้า / ออก</strong><span>X / Y / Z · Free</span><strong>เลือกแกน / หมุนอิสระ</strong><span>R / F</span><strong>รีเซ็ตทั้งหมด / โฟกัสและเปิดรายละเอียด</strong><span>/ · Space</span><strong>ค้นหา / หยุดหรือเริ่มโมชั่น</strong></div><div className="help-horizons">{HORIZONS.map((horizon, index) => <span key={horizon.key}><strong>{RING_NAMES[index]}</strong>{horizon.timeframe}</span>)}</div><div className="state-legend">{Object.entries(STATE_META).map(([state, meta]) => <span key={state}><IconCircle size={16} style={{ color: meta.color }} />{meta.labelThai}</span>)}</div><p className="dialog-note">บนจอสัมผัส ลากหนึ่งนิ้วเพื่อหมุนและแตะเพื่อเลือก กลุ่มดาวเป็นการจัดหมวดหมู่ เส้นเชื่อม แสงวิ่ง และดาวตกเป็นโมชั่นประกอบ ไม่ได้แสดงความสัมพันธ์ของราคา การส่งคำสั่ง หรือสถานะการทำงานของระบบจริง ข้อมูลและกราฟทั้งหมดเป็นข้อมูลตัวอย่าง ไม่มี API ตลาดจริง การเรียก AI หรือคำสั่งเทรด</p></>}
  </section></dialog>;
}

export function App() {
  const [selectedSymbol, setSelectedSymbol] = useState('XAUUSD'), [filter, setFilter] = useState('all'), [axis, setAxis] = useState('free');
  const [reducedMotion, setReducedMotion] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const [playing, setPlaying] = useState(() => !window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const [motionSpeed, setMotionSpeed] = useState(1);
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [resetKey, setResetKey] = useState(0), [focusKey, setFocusKey] = useState(0), [favorites, setFavorites] = useState(() => new Set());
  const [dialog, setDialog] = useState(null), [fullscreen, setFullscreen] = useState(false), [sceneStatus, setSceneStatus] = useState('loading'), [toast, setToast] = useState('');
  const searchRef = useRef(null), sceneRef = useRef(null), motionClock = useRef({ value: 0 });
  const pair = PAIRS.find((item) => item.symbol === selectedSymbol) || PAIRS[0];
  const isPlaying = playing && !reducedMotion;
  const sceneReady = useCallback(() => setSceneStatus('ready'), []), sceneError = useCallback(() => setSceneStatus('error'), []);
  const selectFromScene = useCallback((symbol) => { setSelectedSymbol(symbol); setInspectorOpen(true); }, []);
  const closeInspector = useCallback(() => { setInspectorOpen(false); sceneRef.current?.focus({ preventScroll: true }); }, []);
  const pickPair = (symbol) => {
    const selected = PAIRS.find((item) => item.symbol === symbol);
    if (!selected) return;
    if (filter !== 'all' && selected.assetClass !== filter) setFilter('all');
    setSelectedSymbol(symbol); setInspectorOpen(true); setFocusKey((key) => key + 1);
  };
  const changeFilter = (value) => {
    setFilter(value);
    if (value !== 'all' && pair.assetClass !== value) {
      const first = PAIRS.find((item) => item.assetClass === value);
      if (first) setSelectedSymbol(first.symbol);
    }
  };
  const focus = useCallback(() => { setInspectorOpen(true); setFocusKey((key) => key + 1); }, []);
  const reset = useCallback(() => { setInspectorOpen(false); setFilter('all'); setAxis('free'); setResetKey((key) => key + 1); setPlaying(!reducedMotion); }, [reducedMotion]);
  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const listener = (event) => { setReducedMotion(event.matches); if (event.matches) setPlaying(false); };
    media.addEventListener('change', listener); return () => media.removeEventListener('change', listener);
  }, []);
  useEffect(() => { const listener = () => setFullscreen(Boolean(document.fullscreenElement)); document.addEventListener('fullscreenchange', listener); return () => document.removeEventListener('fullscreenchange', listener); }, []);
  useEffect(() => { if (!toast) return undefined; const timeout = window.setTimeout(() => setToast(''), 4500); return () => window.clearTimeout(timeout); }, [toast]);
  useEffect(() => {
    const keydown = (event) => {
      if (event.key === 'Escape' && inspectorOpen && !dialog) { event.preventDefault(); closeInspector(); return; }
      if (dialog || event.altKey || event.ctrlKey || event.metaKey || /INPUT|TEXTAREA|SELECT/.test(event.target.tagName) || event.target.isContentEditable) return;
      const key = event.key.toLowerCase();
      if (['x', 'y', 'z'].includes(key)) setAxis(key);
      if (key === 'r') reset();
      if (key === 'f') focus();
      if (key === '/') { event.preventDefault(); searchRef.current?.focus(); }
      if (key === ' ' && event.target.tagName !== 'BUTTON' && !reducedMotion) { event.preventDefault(); setPlaying((value) => !value); }
    };
    window.addEventListener('keydown', keydown); return () => window.removeEventListener('keydown', keydown);
  }, [dialog, inspectorOpen, reducedMotion, reset, focus, closeInspector]);
  const toggleFullscreen = async () => { try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); } catch { setToast('เบราว์เซอร์นี้ยังไม่อนุญาตโหมดเต็มหน้าจอ'); } };
  const toggleFavorite = () => setFavorites((current) => { const next = new Set(current); if (next.has(pair.symbol)) next.delete(pair.symbol); else next.add(pair.symbol); return next; });
  const assetName = { XAUUSD: 'GOLD', XAGUSD: 'SILVER', WTI: 'WEST TEXAS INTERMEDIATE', BRENT: 'BRENT CRUDE' }[pair.symbol] || pair.name;
  return <div className={`app-shell ${reducedMotion ? 'reduce-motion' : ''}`}>
    <header className="app-header">
      <a className="brand" href="#overview" aria-label="Metafxclub ภาพรวม"><img src="/assets/metafx-mark.png" alt="" /><span>METAFXCLUB</span></a>
      <div className="product-title">MARKET UNIVERSE <span className="title-divider">/</span><span className="asset-count"><strong>{PAIRS.length}</strong> สินทรัพย์</span></div>
      <div className="header-controls"><nav className="asset-filters" aria-label="กรองกลุ่มสินทรัพย์">{FILTERS.map((item) => <button key={item.key} aria-pressed={filter === item.key} className={filter === item.key ? 'is-current' : ''} onClick={() => changeFilter(item.key)}>{item.label} <span>{item.key === 'all' ? PAIRS.length : PAIRS.filter((asset) => asset.assetClass === item.key).length}</span></button>)}</nav>
        <PairPicker selectedSymbol={selectedSymbol} onSelect={pickPair} favorites={favorites} inputRef={searchRef} />
        <div className="rotation-control"><span role="status">{reducedMotion ? 'ลดการเคลื่อนไหว' : isPlaying ? <>โมชั่นอัตโนมัติ <i>·</i> <strong>{motionSpeed}×</strong></> : 'พักโมชั่นทั้งหมด'}</span><button className="rotation-toggle" aria-label={isPlaying ? 'หยุดโมชั่นทั้งหมด' : 'เริ่มโมชั่นอัตโนมัติ'} aria-pressed={isPlaying} disabled={reducedMotion} title={reducedMotion ? 'ปิดโหมดลดการเคลื่อนไหวในตั้งค่าก่อน' : isPlaying ? 'หยุดโมชั่นทั้งหมด (Space)' : 'เริ่มโมชั่นอัตโนมัติ (Space)'} onClick={() => setPlaying((value) => !value)}>{isPlaying ? <IconPlayerPause size={18} stroke={1.5} /> : <IconPlayerPlay size={18} stroke={1.5} />}</button></div>
      </div>
    </header>
    <main className="app-main" id="overview">
      <section className={`galaxy-panel ${inspectorOpen ? 'is-inspecting' : ''}`} aria-label={`สำรวจ ${PAIRS.length} สินทรัพย์แบบสามมิติ`}>
        <div className="galaxy-stage">
        <div className="scene-host" ref={sceneRef} tabIndex={0} aria-label="มุมมองสามมิติ ใช้ X Y Z เลือกแกน R รีเซ็ต F โฟกัส หรือเลือกสินทรัพย์จากช่องค้นหา"><OrbitalScene pairs={PAIRS} selectedSymbol={selectedSymbol} axis={axis} playing={isPlaying} motionSpeed={motionSpeed} motionClock={motionClock} filter={filter} resetKey={resetKey} focusKey={focusKey} onSelect={selectFromScene} onReady={sceneReady} onError={sceneError} /></div>
        {sceneStatus !== 'ready' && <div className="scene-status" role="status"><IconInfoCircle size={23} stroke={1.2} /><span>{sceneStatus === 'error' ? 'ไม่สามารถแสดงภาพ 3D ในเบราว์เซอร์นี้ได้' : 'กำลังเตรียม Market Universe'}</span><small>{sceneStatus === 'error' ? 'ยังเลือกดูสินทรัพย์และกราฟตัวอย่างจากช่องค้นหาได้' : `${PAIRS.length} สินทรัพย์ · 3 ช่วงเวลา`}</small></div>}
        <div className="scene-controls" role="group" aria-label="ควบคุมมุมมอง"><div className="axis-control"><span className="axis-label">มุมมอง</span><div className="axis-buttons" role="group" aria-label="เลือกแกนหมุน">{['free', 'x', 'y', 'z'].map((value) => <button key={value} className={`axis-button ${axis === value ? 'is-selected' : ''}`} aria-pressed={axis === value} title={value === 'free' ? 'หมุนอิสระ' : `หมุนตามแกน ${value.toUpperCase()}`} onClick={() => setAxis(value)}>{value === 'free' ? 'Free' : value.toUpperCase()}</button>)}</div></div><button className="reset-button" title="แสดงทั้งหมดและเริ่มหมุนใหม่ (R)" aria-label="รีเซ็ตมุมมอง แสดงทั้งหมดและเริ่มหมุนใหม่" onClick={reset}><IconRotateClockwise size={20} stroke={1.5} /><span>รีเซ็ต</span></button></div>
        <div className="scene-utilities"><button className="icon-button" title={`โฟกัส ${pair.symbol} (F)`} aria-label={`โฟกัส ${pair.symbol}`} aria-controls={inspectorOpen ? 'asset-detail-drawer' : undefined} aria-expanded={inspectorOpen} onClick={focus}><IconFocus2 size={20} stroke={1.4} /></button><button className="icon-button" title="ตั้งค่ามุมมอง" aria-label="ตั้งค่ามุมมอง" onClick={() => setDialog('settings')}><IconSettings size={20} stroke={1.4} /></button></div>
        </div>
        {inspectorOpen && <aside className="asset-drawer" id="asset-detail-drawer" aria-labelledby="asset-drawer-title">
          <header className="asset-drawer-header"><div><h2 id="asset-drawer-title">{pair.symbol}</h2><p>{assetName} <span>/ {pair.assetClass?.toUpperCase() || pair.kind}</span></p></div><button className="icon-button drawer-close" aria-label="ปิดรายละเอียดสินทรัพย์" title="ปิดรายละเอียด (Esc)" onClick={closeInspector}><IconX size={24} stroke={1.3} /></button></header>
          <NucleusPreview pair={pair} clockRef={motionClock} labeled className="drawer-nucleus" />
          <div className="drawer-horizons">{HORIZONS.map((horizon, index) => {
            const meta = STATE_META[pair.states[index]] || STATE_META.unknown;
            return <div className="drawer-horizon" key={horizon.key} aria-label={`${RING_NAMES[index]} ${horizon.timeframe} ${meta.labelThai}`}><IconCircle size={25} stroke={2.1} style={{ color: meta.color }} aria-hidden="true" /><span><small>ระยะ{HORIZON_NAMES[index]}</small><strong>{horizon.timeframe}</strong></span><b style={{ color: meta.color }}>{meta.labelThai}</b></div>;
          })}</div>
          <p className="drawer-caption">สามวงโคจร · สามช่วงเวลา</p>
        </aside>}
      </section>
      <aside className="inspector" aria-label={`รายละเอียดสินทรัพย์ ${pair.symbol}`}>
        <div className="asset-identity"><NucleusPreview pair={pair} clockRef={motionClock} className="ring-preview" /><div className="pair-heading"><div className="pair-title"><h1>{pair.symbol}</h1><button className={`icon-button favorite-button ${favorites.has(pair.symbol) ? 'is-favorite' : ''}`} aria-label={`${favorites.has(pair.symbol) ? 'เลิกติดดาว' : 'ติดดาว'} ${pair.symbol}`} aria-pressed={favorites.has(pair.symbol)} title="ติดดาวสินทรัพย์สำหรับค้นหา" onClick={toggleFavorite}>{favorites.has(pair.symbol) ? <IconStarFilled size={23} /> : <IconStar size={23} stroke={1.4} />}</button></div><div className="pair-subheading"><span title={assetName}>{assetName}</span><span className="pair-kind">{pair.assetClass?.toUpperCase() || pair.kind}</span></div></div></div>
        <div className="horizons">{HORIZONS.map((horizon, index) => {
          const state = pair.states[index], meta = STATE_META[state] || STATE_META.unknown;
          return <section className="horizon-panel" key={horizon.key} aria-label={`${RING_NAMES[index]} ระยะ${horizon.label}`}><div className="horizon-heading"><HorizonRing state={state} index={index} /><h2>{horizon.label}</h2><span className="horizon-dot" aria-hidden="true">·</span><span className="timeframe">{horizon.timeframe}</span><span className="horizon-dot" aria-hidden="true">·</span><span className="direction" style={{ color: meta.color }}>{meta.labelThai}</span></div><Sparkline values={pair.series[index]} state={state} horizon={HORIZON_NAMES[index]} symbol={pair.symbol} /></section>;
        })}</div>
      </aside>
    </main>
    <footer className="app-footer"><button className="interaction-help" onClick={() => setDialog('help')} aria-label="ดูวิธีใช้งานและความหมายของวงแหวน"><IconMouse size={15} stroke={1.3} /><span className="desktop-instructions">คลิกขวาลากเพื่อหมุน · เลื่อนเพื่อซูม · คลิกดาวเพื่อเลือก</span><span className="mobile-instructions">ลากเพื่อหมุน · แตะดาวเพื่อเลือก</span></button><span className="demo-label">ข้อมูลตัวอย่างสำหรับงานออกแบบ <button className="icon-button" title="ข้อมูลต้นแบบและวิธีใช้" aria-label="ข้อมูลต้นแบบและวิธีใช้" onClick={() => setDialog('help')}><IconInfoCircle size={18} stroke={1.3} /></button></span></footer>
    <div className="sr-only" aria-live="polite">เลือก {pair.symbol} ระยะสั้น {STATE_META[pair.states[0]]?.labelThai} ระยะกลาง {STATE_META[pair.states[1]]?.labelThai} ระยะยาว {STATE_META[pair.states[2]]?.labelThai}</div>
    {toast && <div className="toast" role="status">{toast}</div>}
    {dialog && <PreviewDialog type={dialog} onClose={() => setDialog(null)} reducedMotion={reducedMotion} onReducedMotionChange={(value) => { setReducedMotion(value); if (value) setPlaying(false); }} motionSpeed={motionSpeed} onMotionSpeedChange={setMotionSpeed} fullscreen={fullscreen} onFullscreen={toggleFullscreen} />}
  </div>;
}
