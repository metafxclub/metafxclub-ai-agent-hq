import assert from 'node:assert/strict';
import test from 'node:test';
import { CLUSTERS, HORIZONS, PAIRS, STATE_META } from '../src/data.js';

const CURRENCIES = {
  AUD: 'AUSTRALIAN DOLLAR', CAD: 'CANADIAN DOLLAR', CHF: 'SWISS FRANC',
  EUR: 'EURO', GBP: 'BRITISH POUND', JPY: 'JAPANESE YEN',
  NZD: 'NEW ZEALAND DOLLAR', USD: 'US DOLLAR',
};

const EXPECTED_SYMBOLS = [
  'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD', 'CADCHF', 'CADJPY', 'CHFJPY',
  'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD',
  'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD', 'GBPUSD',
  'NZDCAD', 'NZDCHF', 'NZDJPY', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY',
];

function slope(values) {
  const middle = (values.length - 1) / 2;
  const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
  return values.reduce((sum, value, index) => sum + (index - middle) * (value - mean), 0)
    / values.reduce((sum, _, index) => sum + (index - middle) ** 2, 0);
}

test('the catalog preserves the original 28 FX pairs then appends four unique commodities', () => {
  assert.equal(PAIRS.length, 32);
  assert.deepEqual(PAIRS.map(({ symbol }) => symbol), [...EXPECTED_SYMBOLS, 'XAUUSD', 'XAGUSD', 'WTI', 'BRENT']);
  assert.equal(new Set(PAIRS.map(({ symbol }) => symbol)).size, 32);
});

test('every unordered combination of the eight currencies appears exactly once', () => {
  const codes = Object.keys(CURRENCIES);
  const expected = new Set(codes.flatMap((base, index) =>
    codes.slice(index + 1).map((quote) => [base, quote].sort().join('/'))));
  const actual = PAIRS.filter(({ assetClass }) => assetClass === 'forex')
    .map(({ symbol }) => [symbol.slice(0, 3), symbol.slice(3)].sort().join('/'));
  assert.equal(actual.length, expected.size);
  assert.deepEqual(new Set(actual), expected);
});

test('FX names and major/cross classification remain accurate', () => {
  for (const pair of PAIRS.filter(({ assetClass }) => assetClass === 'forex')) {
    const [base, quote] = [pair.symbol.slice(0, 3), pair.symbol.slice(3)];
    assert.equal(pair.name, `${CURRENCIES[base]} / ${CURRENCIES[quote]}`);
    assert.equal(pair.kind, base === 'USD' || quote === 'USD' ? 'MAJOR' : 'CROSS');
  }
  assert.equal(PAIRS.filter(({ kind }) => kind === 'MAJOR').length, 7);
});

test('commodity names, classes, and clusters do not inherit the USD currency group', () => {
  const expected = {
    XAUUSD: ['GOLD', 'metals', 'METALS'],
    XAGUSD: ['SILVER', 'metals', 'METALS'],
    WTI: ['WEST TEXAS INTERMEDIATE', 'oil', 'OIL'],
    BRENT: ['BRENT CRUDE OIL', 'oil', 'OIL'],
  };
  for (const [symbol, [name, assetClass, clusterId]] of Object.entries(expected)) {
    const instrument = PAIRS.find((pair) => pair.symbol === symbol);
    assert.equal(instrument.name, name);
    assert.equal(instrument.assetClass, assetClass);
    assert.equal(instrument.clusterId, clusterId);
    assert.equal(instrument.kind, clusterId);
  }
  assert.deepEqual(PAIRS.filter(({ assetClass }) => assetClass !== 'forex').map(({ symbol }) => symbol), Object.keys(expected));
});

test('every instrument belongs to exactly one of nine complete deterministic clusters', () => {
  const expected = {
    EUR: ['EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD'],
    GBP: ['GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD', 'GBPUSD'],
    AUD: ['AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD'],
    NZD: ['NZDCAD', 'NZDCHF', 'NZDJPY', 'NZDUSD'],
    USD: ['USDCAD', 'USDCHF', 'USDJPY'],
    CAD: ['CADCHF', 'CADJPY'],
    CHF: ['CHFJPY'],
    METALS: ['XAUUSD', 'XAGUSD'],
    OIL: ['WTI', 'BRENT'],
  };
  assert.deepEqual(CLUSTERS.map(({ id }) => id), Object.keys(expected));
  assert.deepEqual(CLUSTERS.map(({ count }) => count), [7, 6, 5, 4, 3, 2, 1, 2, 2]);
  assert.equal(CLUSTERS.reduce((sum, { count }) => sum + count, 0), 32);
  for (const cluster of CLUSTERS) {
    const members = PAIRS.filter(({ clusterId }) => clusterId === cluster.id);
    assert.deepEqual(members.map(({ symbol }) => symbol), expected[cluster.id]);
    assert.equal(cluster.count, members.length);
    assert.equal(cluster.label, cluster.id);
    assert.match(cluster.color, /^#[0-9a-f]{6}$/i);
    assert.ok(members.every(({ assetClass }) => assetClass === cluster.assetClass));
    assert.deepEqual(Object.keys(cluster).sort(), ['assetClass', 'color', 'count', 'id', 'label']);
  }
  assert.equal(PAIRS.find(({ symbol }) => symbol === 'EURGBP').clusterId, 'EUR');
  for (const instrument of PAIRS) {
    assert.equal(CLUSTERS.filter(({ id }) => id === instrument.clusterId).length, 1);
    assert.deepEqual(Object.keys(instrument).sort(), ['assetClass', 'clusterId', 'kind', 'name', 'series', 'states', 'symbol']);
  }
});

test('horizon indexes map consistently to inner, middle, and outer rings', () => {
  assert.deepEqual(HORIZONS, [
    { key: 'short', label: 'สั้น', timeframe: 'M15–H1', ring: 'วงใน' },
    { key: 'medium', label: 'กลาง', timeframe: 'H1–D1', ring: 'วงกลาง' },
    { key: 'long', label: 'ยาว', timeframe: 'D1–W1', ring: 'วงนอก' },
  ]);
  assert.deepEqual(PAIRS.find(({ symbol }) => symbol === 'EURUSD').states, ['up', 'range', 'down']);
  assert.deepEqual(PAIRS.find(({ symbol }) => symbol === 'XAUUSD').states, ['up', 'range', 'up']);
});

test('all four states have distinct Thai text and valid color metadata', () => {
  assert.deepEqual(Object.keys(STATE_META).sort(), ['down', 'range', 'unknown', 'up']);
  assert.equal(new Set(Object.values(STATE_META).map(({ labelThai }) => labelThai)).size, 4);
  assert.equal(new Set(Object.values(STATE_META).map(({ color }) => color)).size, 4);
  for (const { labelThai, color } of Object.values(STATE_META)) {
    assert.match(labelThai, /[\u0e00-\u0e7f]/);
    assert.match(color, /^#[0-9a-f]{6}$/i);
  }
});

test('known horizons contain 70 finite values and unknown horizons contain no invented data', () => {
  let unavailable = 0;
  for (const pair of PAIRS) {
    assert.equal(pair.states.length, 3);
    assert.equal(pair.series.length, 3);
    pair.states.forEach((state, index) => {
      assert.ok(Object.hasOwn(STATE_META, state), `${pair.symbol}: ${state}`);
      const values = pair.series[index];
      assert.ok(Array.isArray(values));
      if (state === 'unknown') {
        unavailable += 1;
        assert.deepEqual(values, [], `${pair.symbol}: unknown is not sideways`);
      } else {
        assert.equal(values.length, 70);
        assert.ok(values.every(Number.isFinite));
      }
    });
  }
  assert.equal(unavailable, 5);
  for (const [symbol, index] of [['AUDNZD', 2], ['CADCHF', 0], ['EURCHF', 1], ['GBPCHF', 2], ['NZDCAD', 1]]) {
    const pair = PAIRS.find((instrument) => instrument.symbol === symbol);
    assert.equal(pair.states[index], 'unknown');
    assert.deepEqual(pair.series[index], []);
  }
});

test('the direction, displacement, and variation of each trace agree with its label', () => {
  for (const pair of PAIRS) {
    pair.states.forEach((state, index) => {
      const values = pair.series[index];
      if (state === 'unknown') return;
      const change = values.at(-1) - values[0];
      const gradient = slope(values);
      const context = `${pair.symbol}/${HORIZONS[index].key}/${state}`;
      assert.equal(values[0], 100, `${context}: normalized prototype baseline`);
      assert.ok(Math.max(...values) - Math.min(...values) > 1, `${context}: visible variation`);
      if (state === 'up') {
        assert.ok(change >= 8 && gradient > 0.08, context);
      } else if (state === 'down') {
        assert.ok(change <= -8 && gradient < -0.08, context);
      } else {
        assert.ok(Math.abs(change) < 0.1 && Math.abs(gradient) < 0.025, context);
        assert.ok(Math.max(...values) - Math.min(...values) < 4, context);
      }
    });
  }
});

test('reloading the data module reproduces identical seeded traces', async () => {
  const reloaded = await import('../src/data.js?deterministic-reload');
  assert.deepEqual(reloaded.PAIRS, PAIRS);
  assert.deepEqual(reloaded.HORIZONS, HORIZONS);
  assert.deepEqual(reloaded.STATE_META, STATE_META);
  assert.deepEqual(reloaded.CLUSTERS, CLUSTERS);
  const knownTraces = PAIRS.flatMap(({ series }) => series.filter((values) => values.length));
  assert.equal(new Set(knownTraces.map((values) => JSON.stringify(values))).size, knownTraces.length);
});
