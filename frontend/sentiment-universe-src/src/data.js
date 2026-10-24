// Prototype data only. These normalized traces are not prices, predictions,
// performance results, or data from the live trading system.

export const STATE_META = {
  up: { labelThai: 'ขาขึ้น', color: '#65e5c0' },
  range: { labelThai: 'ไซด์เวย์', color: '#e7be76' },
  down: { labelThai: 'ขาลง', color: '#ff819a' },
  unknown: { labelThai: 'ยังไม่มีข้อมูล', color: '#8190a8' },
};

export const HORIZONS = [
  { key: 'short', label: 'สั้น', timeframe: 'M15–H1', ring: 'วงใน' },
  { key: 'medium', label: 'กลาง', timeframe: 'H1–D1', ring: 'วงกลาง' },
  { key: 'long', label: 'ยาว', timeframe: 'D1–W1', ring: 'วงนอก' },
];

const CURRENCY_NAMES = {
  AUD: 'AUSTRALIAN DOLLAR',
  CAD: 'CANADIAN DOLLAR',
  CHF: 'SWISS FRANC',
  EUR: 'EURO',
  GBP: 'BRITISH POUND',
  JPY: 'JAPANESE YEN',
  NZD: 'NEW ZEALAND DOLLAR',
  USD: 'US DOLLAR',
};

const SYMBOLS = [
  'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD',
  'CADCHF', 'CADJPY', 'CHFJPY',
  'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD',
  'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD', 'GBPUSD',
  'NZDCAD', 'NZDCHF', 'NZDJPY', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY',
];

// Assign every FX pair once, including crosses such as EURGBP. Category
// assignment precedes currency assignment, so XAUUSD is never in USD.
const CURRENCY_PRECEDENCE = ['EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF'];

const INSTRUMENTS = [
  ...SYMBOLS.map((symbol) => ({
    symbol,
    name: `${CURRENCY_NAMES[symbol.slice(0, 3)]} / ${CURRENCY_NAMES[symbol.slice(3)]}`,
    kind: symbol.includes('USD') ? 'MAJOR' : 'CROSS',
    assetClass: 'forex',
    clusterId: CURRENCY_PRECEDENCE.find((currency) =>
      symbol.slice(0, 3) === currency || symbol.slice(3) === currency),
  })),
  { symbol: 'XAUUSD', name: 'GOLD', kind: 'METALS', assetClass: 'metals', clusterId: 'METALS' },
  { symbol: 'XAGUSD', name: 'SILVER', kind: 'METALS', assetClass: 'metals', clusterId: 'METALS' },
  { symbol: 'WTI', name: 'WEST TEXAS INTERMEDIATE', kind: 'OIL', assetClass: 'oil', clusterId: 'OIL' },
  { symbol: 'BRENT', name: 'BRENT CRUDE OIL', kind: 'OIL', assetClass: 'oil', clusterId: 'OIL' },
];

// An unavailable horizon has no synthetic trace. Keep missing data visibly
// different from the known sideways example throughout the interface.
const UNKNOWN_HORIZONS = new Set([
  'AUDNZD:long',
  'CADCHF:short',
  'EURCHF:medium',
  'GBPCHF:long',
  'NZDCAD:medium',
]);

function hash(text) {
  let value = 2166136261;
  for (const character of text) {
    value = Math.imul(value ^ character.charCodeAt(0), 16777619);
  }
  return value >>> 0;
}

function randomFrom(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let value = Math.imul(state ^ (state >>> 15), 1 | state);
    value ^= value + Math.imul(value ^ (value >>> 7), 61 | value);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

function mockTrace(symbol, horizon, state) {
  if (state === 'unknown') return [];
  const random = randomFrom(hash(`${symbol}:${horizon}:${state}`));
  const phase = random() * Math.PI * 2;
  const cycles = 2 + Math.floor(random() * 3);
  const drift = state === 'up' ? 9 : state === 'down' ? -9 : 0;
  const amplitude = state === 'range' ? 1.25 : 0.9;
  return Array.from({ length: 70 }, (_, index) => {
    const progress = index / 69;
    const envelope = Math.sin(Math.PI * progress);
    const wave = Math.sin(progress * Math.PI * 2 * cycles + phase);
    const noise = (random() - 0.5) * 0.45;
    return Number((100 + drift * progress + (wave * amplitude + noise) * envelope).toFixed(4));
  });
}

export const PAIRS = INSTRUMENTS.map((instrument) => {
  const { symbol } = instrument;
  const states = HORIZONS.map(({ key }) => {
    if (UNKNOWN_HORIZONS.has(`${symbol}:${key}`)) return 'unknown';
    return ['up', 'range', 'down'][hash(`${symbol}:${key}`) % 3];
  });
  if (symbol === 'EURUSD') states.splice(0, 3, 'up', 'range', 'down');
  if (symbol === 'XAUUSD') states.splice(0, 3, 'up', 'range', 'up');
  return {
    ...instrument,
    states,
    series: HORIZONS.map(({ key }, index) => mockTrace(symbol, key, states[index])),
  };
});

// Cluster colors identify categories only. STATE_META continues to define
// the independent short/medium/long trend colors on every instrument's rings.
export const CLUSTERS = [
  { id: 'EUR', label: 'EUR', assetClass: 'forex', color: '#56d9ed' },
  { id: 'GBP', label: 'GBP', assetClass: 'forex', color: '#dc91db' },
  { id: 'AUD', label: 'AUD', assetClass: 'forex', color: '#e4bd72' },
  { id: 'NZD', label: 'NZD', assetClass: 'forex', color: '#67d9d2' },
  { id: 'USD', label: 'USD', assetClass: 'forex', color: '#71abef' },
  { id: 'CAD', label: 'CAD', assetClass: 'forex', color: '#a89be0' },
  { id: 'CHF', label: 'CHF', assetClass: 'forex', color: '#bacbd8' },
  { id: 'METALS', label: 'METALS', assetClass: 'metals', color: '#e4c46f' },
  { id: 'OIL', label: 'OIL', assetClass: 'oil', color: '#da9b56' },
].map((cluster) => ({
  ...cluster,
  count: PAIRS.filter(({ clusterId }) => clusterId === cluster.id).length,
}));
