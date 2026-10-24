import { PAIRS } from './data.js';

// Isolated design fixtures. Nothing in this module queries a service or represents
// a live position, measured correlation, actual calendar, or trading signal.
export const DEMO_LABEL = 'ข้อมูลสมมติสำหรับทดลองหน้าตา';
export const DEMO_DATE = '2026-10-24';
export const SENTIMENT_AS_OF = '2026-10-24T03:15:00Z';
export const SENTIMENT_AS_OF_LABEL = 'ตัวอย่างข้อมูล ณ 10:15 น. เวลาไทย';
export const NEWS_FETCHED_AT = '2026-10-24T01:00:00Z';
export const NEWS_ANALYZED_AT = '2026-10-24T01:05:00Z';
export const NEWS_ROUND_LABEL = 'รอบตัวอย่าง 08:00 น. · วิเคราะห์วันละครั้ง';
export const ACTUAL_UNAVAILABLE_LABEL = 'ยังไม่มีผลจริงในรอบรายวันนี้';
export const CORRELATION_LABEL = 'Correlation ตัวอย่าง · ไม่ได้คำนวณจากราคาจริง';
export const SCENARIO_NOTE = 'ฉากทัศน์ตามเงื่อนไข · ไม่ใช่สัญญาณซื้อขาย';

const CATALOG = new Map(PAIRS.map((pair) => [pair.symbol, pair]));
const USD_PER_UNIT = { EUR: 1.082, GBP: 1.28, AUD: 0.66, NZD: 0.61, CAD: 0.73, CHF: 1.14, JPY: 0.0067, USD: 1 };

function hash(text) {
  let result = 2166136261;
  for (const character of text) result = Math.imul(result ^ character.charCodeAt(0), 16777619);
  return result >>> 0;
}

function normalizeSymbol(symbol) {
  return typeof symbol === 'string' ? symbol.trim().toUpperCase() : '';
}

export function getSentiment(symbol) {
  const name = normalizeSymbol(symbol);
  const pair = CATALOG.get(name);
  if (!pair || pair.assetClass === 'oil') {
    return { long: null, short: null, avgLong: null, avgShort: null, available: false, asOf: null };
  }
  if (name === 'EURUSD') {
    return { long: 68, short: 32, avgLong: 1.08620, avgShort: 1.07910, available: true, asOf: SENTIMENT_AS_OF };
  }
  // Deliberate color-scale examples, still fictional community compositions.
  const demoLong = { GBPUSD: 88, USDJPY: 9, AUDJPY: 82, EURJPY: 16, EURCHF: 50 };
  const long = demoLong[name] ?? 24 + hash(`sentiment:${name}`) % 53;
  const center = name === 'XAUUSD' ? 2725 : name === 'XAGUSD' ? 33.4 : USD_PER_UNIT[name.slice(0, 3)] / USD_PER_UNIT[name.slice(3)];
  const digits = pair.assetClass === 'metals' ? 2 : name.endsWith('JPY') ? 3 : 5;
  const offset = 0.001 + (hash(`average:${name}`) % 60) / 10000;
  return {
    long,
    short: 100 - long,
    avgLong: Number((center * (1 + offset)).toFixed(digits)),
    avgShort: Number((center * (1 - offset * 0.8)).toFixed(digits)),
    available: true,
    asOf: SENTIMENT_AS_OF,
  };
}

const EXAMPLE_CORRELATIONS = new Map([
  ['EURUSD|GBPUSD', 0.86],
  ['EURUSD|USDCHF', -0.81],
  ['EURUSD|XAUUSD', 0.12],
]);

function sampleCorrelation(first, second) {
  const key = [first, second].sort().join('|');
  return EXAMPLE_CORRELATIONS.get(key) ?? Number((((hash(`correlation:${key}`) % 189) - 94) / 100).toFixed(2));
}

// Symmetric coefficients demonstrate edge color/weight only. These fixture values
// are not Pearson estimates and must not be used for portfolio calculations.
export function getCorrelations(symbol) {
  const name = normalizeSymbol(symbol);
  if (!CATALOG.has(name)) return [];
  return PAIRS.filter((pair) => pair.symbol !== name)
    .map((pair) => ({ symbol: pair.symbol, value: sampleCorrelation(name, pair.symbol) }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value) || a.symbol.localeCompare(b.symbol));
}

const thaiTimeFormatter = new Intl.DateTimeFormat('en-GB', {
  timeZone: 'Asia/Bangkok', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
});

export function formatThaiTime(iso) {
  if (typeof iso !== 'string' || !/(Z|[+-]\d{2}:\d{2})$/.test(iso)) return '—';
  const date = new Date(iso);
  return Number.isFinite(date.getTime()) ? thaiTimeFormatter.format(date) : '—';
}

function event(values) {
  return Object.freeze({
    actual: null,
    actualLabel: ACTUAL_UNAVAILABLE_LABEL,
    mock: true,
    forecast: null,
    previous: null,
    forecastValue: null,
    previousValue: null,
    kind: 'numeric',
    numeric: true,
    ...values,
    impactLabel: values.impact === 'high' ? 'สูง' : 'ปานกลาง',
  });
}

// Fictional Saturday calendar used to review interaction, not a claim that these
// releases occur on this date. Sources below explain the event, not this schedule.
export const NEWS_EVENTS = Object.freeze([
  event({ id: 'demo-eur-confidence', currency: 'EUR', time: '2026-10-24T08:00:00Z', title: 'ความเชื่อมั่นผู้บริโภคยุโรป', summary: 'สำรวจมุมมองของผู้บริโภคต่อเศรษฐกิจและการใช้จ่าย', metric: 'confidence', impact: 'medium', forecast: '-12.0 จุด', previous: '-13.0 จุด', forecastValue: -12, previousValue: -13, unit: 'จุด', sourceName: 'European Commission · นิยามข่าว', sourceUrl: 'https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys_en' }),
  event({ id: 'demo-eur-pmi', currency: 'EUR', time: '2026-10-24T09:00:00Z', title: 'PMI ภาคธุรกิจยูโรโซน', summary: 'แบบสำรวจกิจกรรมธุรกิจ; สูงกว่า 50 จุดหมายถึงขยายตัวเมื่อเทียบเดือนก่อน', metric: 'activity', impact: 'high', forecast: '49.5 จุด', previous: '49.2 จุด', forecastValue: 49.5, previousValue: 49.2, unit: 'จุด', sourceName: 'S&P Global · นิยามข่าว', sourceUrl: 'https://www.pmi.spglobal.com/' }),
  event({ id: 'demo-us-cpi', currency: 'USD', time: '2026-10-24T13:30:00Z', title: 'CPI สหรัฐฯ รายเดือน', summary: 'การเปลี่ยนแปลงราคาสินค้าและบริการที่ผู้บริโภคจ่าย เทียบเดือนก่อน', metric: 'inflation', impact: 'high', forecast: '0.3%', previous: '0.2%', forecastValue: 0.3, previousValue: 0.2, unit: '%', sourceName: 'BLS · นิยามข่าว', sourceUrl: 'https://www.bls.gov/cpi/' }),
  event({ id: 'demo-us-core-cpi', currency: 'USD', time: '2026-10-24T13:30:00Z', title: 'Core CPI สหรัฐฯ รายเดือน', summary: 'เงินเฟ้อผู้บริโภคที่ไม่นับอาหารและพลังงาน ใช้ดูแรงกดดันราคาพื้นฐาน', metric: 'inflation', impact: 'high', forecast: '0.2%', previous: '0.3%', forecastValue: 0.2, previousValue: 0.3, unit: '%', sourceName: 'BLS · นิยามข่าว', sourceUrl: 'https://www.bls.gov/cpi/' }),
  event({ id: 'demo-ecb-speech', currency: 'EUR', time: '2026-10-24T14:00:00Z', title: 'ถ้อยแถลงผู้แทน ECB', summary: 'ติดตามท่าทีต่อเงินเฟ้อและดอกเบี้ย ไม่มีผลตัวเลขเทียบคาด', metric: 'speech', impact: 'high', kind: 'speech', numeric: false, sourceName: 'ECB · หน้าถ้อยแถลง', sourceUrl: 'https://www.ecb.europa.eu/press/key/html/index.en.html' }),
  event({ id: 'demo-fed-speech', currency: 'USD', time: '2026-10-24T14:30:00Z', title: 'ถ้อยแถลงผู้แทน Fed', summary: 'ดูว่าท่าทีเข้มหรือผ่อนคลายกว่าคาด ไม่มีค่าคาดการณ์ตัวเลข', metric: 'speech', impact: 'high', kind: 'speech', numeric: false, sourceName: 'Federal Reserve · หน้าถ้อยแถลง', sourceUrl: 'https://www.federalreserve.gov/newsevents/speeches.htm' }),
  event({ id: 'demo-gbp-unemployment', currency: 'GBP', time: '2026-10-24T06:00:00Z', title: 'อัตราว่างงานสหราชอาณาจักร', summary: 'สัดส่วนผู้ว่างงานในกำลังแรงงาน ค่าที่สูงขึ้นอาจสะท้อนตลาดแรงงานอ่อนลง', metric: 'unemployment', impact: 'high', forecast: '4.5%', previous: '4.4%', forecastValue: 4.5, previousValue: 4.4, unit: '%', sourceName: 'ONS · นิยามข่าว', sourceUrl: 'https://www.ons.gov.uk/employmentandlabourmarket/peoplenotinwork/unemployment' }),
  event({ id: 'demo-aud-employment', currency: 'AUD', time: '2026-10-24T00:30:00Z', title: 'การเปลี่ยนแปลงการจ้างงานออสเตรเลีย', summary: 'จำนวนผู้มีงานทำที่เปลี่ยนจากเดือนก่อน อ่านคู่การมีส่วนร่วมแรงงาน', metric: 'employment', impact: 'high', forecast: '25 พันคน', previous: '20 พันคน', forecastValue: 25, previousValue: 20, unit: 'พันคน', sourceName: 'ABS · นิยามข่าว', sourceUrl: 'https://www.abs.gov.au/statistics/labour/employment-and-unemployment' }),
  event({ id: 'demo-nzd-confidence', currency: 'NZD', time: '2026-10-24T00:00:00Z', title: 'ความเชื่อมั่นธุรกิจนิวซีแลนด์', summary: 'มุมมองภาคธุรกิจต่อเศรษฐกิจ ควรอ่านร่วมกับภาวะการเงิน', metric: 'confidence', impact: 'medium', forecast: '15 จุด', previous: '12 จุด', forecastValue: 15, previousValue: 12, unit: 'จุด', sourceName: 'ANZ · นิยามข่าว', sourceUrl: 'https://www.anz.co.nz/about-us/economic-markets-research/business-outlook/' }),
  event({ id: 'demo-cad-cpi', currency: 'CAD', time: '2026-10-24T12:30:00Z', title: 'CPI แคนาดารายเดือน', summary: 'การเปลี่ยนแปลงราคาสินค้าและบริการของผู้บริโภคแคนาดา', metric: 'inflation', impact: 'high', forecast: '0.2%', previous: '0.1%', forecastValue: 0.2, previousValue: 0.1, unit: '%', sourceName: 'Statistics Canada · นิยามข่าว', sourceUrl: 'https://www.statcan.gc.ca/en/subjects-start/prices_and_price_indexes/consumer_price_indexes' }),
  event({ id: 'demo-chf-speech', currency: 'CHF', time: '2026-10-24T07:00:00Z', title: 'ถ้อยแถลงผู้แทน SNB', summary: 'ติดตามมุมมองเงินเฟ้อและดอกเบี้ยสวิตเซอร์แลนด์ ไม่มีผลตัวเลข', metric: 'speech', impact: 'medium', kind: 'speech', numeric: false, sourceName: 'SNB · หน้านโยบายการเงิน', sourceUrl: 'https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy' }),
  event({ id: 'demo-jpy-cpi', currency: 'JPY', time: '2026-10-23T23:30:00Z', title: 'เงินเฟ้อญี่ปุ่นรายปี', summary: 'ราคาผู้บริโภคญี่ปุ่นเทียบปีก่อน อาจเปลี่ยนมุมมองดอกเบี้ย BOJ', metric: 'inflation', impact: 'high', forecast: '2.5%', previous: '2.4%', forecastValue: 2.5, previousValue: 2.4, unit: '%', sourceName: 'Statistics Bureau Japan · นิยามข่าว', sourceUrl: 'https://www.stat.go.jp/english/data/cpi/' }),
].sort((a, b) => Date.parse(a.time) - Date.parse(b.time)));

export function getNewsForSymbol(symbol) {
  const name = normalizeSymbol(symbol);
  const pair = CATALOG.get(name);
  if (!pair || pair.assetClass === 'oil') return [];
  const currencies = pair.assetClass === 'metals' ? ['USD'] : [name.slice(0, 3), name.slice(3)];
  return NEWS_EVENTS.filter((item) => currencies.includes(item.currency));
}

function assetScenario(eventItem, symbol, currencyDirection) {
  const pair = CATALOG.get(normalizeSymbol(symbol));
  if (!pair || pair.assetClass === 'oil') return { direction: 'uncertain', summary: 'ยังสรุปทิศทางสินทรัพย์ไม่ได้จากข่าวนี้เพียงข่าวเดียว' };
  if (currencyDirection === 0) return { direction: 'neutral', summary: 'ยังไม่ชี้ทิศชัด ต้องดูรายละเอียดและข่าวอื่นร่วมด้วย' };
  if (pair.assetClass === 'metals') {
    if (eventItem.currency !== 'USD') return { direction: 'uncertain', summary: 'ข่าวนี้ไม่ได้ชี้ทิศทางโลหะโดยตรง' };
    return {
      direction: currencyDirection > 0 ? 'down' : 'up',
      summary: currencyDirection > 0 ? `อาจกดดัน ${pair.symbol} หากดอลลาร์หรือผลตอบแทนจริงสูงขึ้น` : `อาจหนุน ${pair.symbol} หากดอลลาร์หรือผลตอบแทนจริงลดลง`,
    };
  }
  const base = pair.symbol.slice(0, 3);
  const quote = pair.symbol.slice(3);
  if (![base, quote].includes(eventItem.currency)) return { direction: 'uncertain', summary: 'ข่าวนี้ไม่ตรงกับสกุลเงินในคู่ที่เลือก' };
  const direction = currencyDirection * (eventItem.currency === base ? 1 : -1) > 0 ? 'up' : 'down';
  return { direction, summary: `${direction === 'up' ? 'อาจหนุน' : 'อาจกดดัน'} ${pair.symbol} ${direction === 'up' ? '↑' : '↓'}` };
}

export function getEventScenarios(eventItem, symbol) {
  if (!eventItem || !['numeric', 'speech'].includes(eventItem.kind)) return [];
  if (eventItem.kind === 'speech') {
    return [
      { key: 'hawkish', label: 'เข้มกว่าคาด', condition: 'เน้นคุมเงินเฟ้อ / ดอกเบี้ยสูงนาน', currencyDirection: 1 },
      { key: 'neutral', label: 'ใกล้เคียงเดิม', condition: 'ไม่มีข้อมูลใหม่เหนือความคาดหมาย', currencyDirection: 0 },
      { key: 'dovish', label: 'ผ่อนคลายกว่าคาด', condition: 'ให้น้ำหนักการชะลอตัว / ลดดอกเบี้ย', currencyDirection: -1 },
    ].map(({ currencyDirection, ...item }) => ({ ...item, ...assetScenario(eventItem, symbol, currencyDirection), note: 'ขึ้นกับว่าตลาดตีความนโยบายเปลี่ยนไปเพียงใด' }));
  }
  // Higher unemployment has the opposite first-order interpretation to stronger
  // activity/employment. Inflation scenarios are conditional on rate repricing.
  const polarity = eventItem.metric === 'unemployment' ? -1 : 1;
  const note = eventItem.metric === 'inflation'
    ? 'หากตลาดปรับคาดการณ์ดอกเบี้ยตามเงินเฟ้อ; ข่าวอื่นอาจหักล้าง'
    : eventItem.metric === 'unemployment'
      ? 'ต้องดูการมีส่วนร่วมแรงงานและค่าจ้างด้วย'
      : 'หากตลาดตีความว่าภาวะเศรษฐกิจเปลี่ยนไป; ข่าวอื่นอาจหักล้าง';
  return [
    { key: 'below', label: 'ต่ำกว่าคาด', condition: `< ${eventItem.forecast}`, currencyDirection: -polarity },
    { key: 'inline', label: 'ใกล้เคียงคาด', condition: `≈ ${eventItem.forecast}`, currencyDirection: 0 },
    { key: 'above', label: 'สูงกว่าคาด', condition: `> ${eventItem.forecast}`, currencyDirection: polarity },
  ].map(({ currencyDirection, ...item }) => ({ ...item, ...assetScenario(eventItem, symbol, currencyDirection), note }));
}

