import test from 'node:test';
import assert from 'node:assert/strict';
import { PAIRS } from '../src/data.js';
import {
  getSentiment, getCorrelations, formatThaiTime, getNewsForSymbol,
  getEventScenarios, NEWS_EVENTS, DEMO_LABEL, ACTUAL_UNAVAILABLE_LABEL,
} from '../src/sentiment-data.js';

test('32 unique assets retain valid deterministic sentiment or explicit missing data', () => {
  assert.equal(PAIRS.length, 32);
  assert.equal(new Set(PAIRS.map((pair) => pair.symbol)).size, 32);
  for (const pair of PAIRS) {
    const sentiment = getSentiment(pair.symbol);
    assert.deepEqual(sentiment, getSentiment(pair.symbol));
    if (pair.assetClass === 'oil') {
      assert.equal(sentiment.available, false);
      for (const key of ['long', 'short', 'avgLong', 'avgShort', 'asOf']) assert.equal(sentiment[key], null);
    } else {
      assert.equal(sentiment.available, true);
      assert.equal(sentiment.long + sentiment.short, 100);
      assert.ok(sentiment.long >= 0 && sentiment.long <= 100);
      assert.ok(sentiment.avgLong > 0 && sentiment.avgShort > 0);
    }
  }
  assert.equal(getSentiment('not-an-asset').available, false);
  assert.equal(getSentiment('EURUSD').long, 68);
  assert.equal(getSentiment('EURUSD').short, 32);
  assert.equal(getSentiment('EURUSD').avgLong, 1.0862);
  assert.equal(getSentiment('EURUSD').avgShort, 1.0791);
  assert.match(DEMO_LABEL, /สมมติ/);
});

test('sample edge values are bounded, symmetric, exclude self, and keep requested examples', () => {
  for (const pair of PAIRS) {
    const entries = getCorrelations(pair.symbol);
    assert.equal(entries.length, 31);
    assert.equal(new Set(entries.map((entry) => entry.symbol)).size, 31);
    for (const entry of entries) {
      assert.notEqual(entry.symbol, pair.symbol);
      assert.ok(entry.value >= -1 && entry.value <= 1);
      assert.equal(entry.value, getCorrelations(entry.symbol).find((other) => other.symbol === pair.symbol).value);
    }
  }
  const eurusd = new Map(getCorrelations('EURUSD').map((entry) => [entry.symbol, entry.value]));
  assert.equal(eurusd.get('GBPUSD'), 0.86);
  assert.equal(eurusd.get('USDCHF'), -0.81);
  assert.equal(eurusd.get('XAUUSD'), 0.12);
  assert.deepEqual(getCorrelations('UNKNOWN'), []);
});

test('event times convert explicitly to Bangkok and reject ambiguous input', () => {
  assert.equal(formatThaiTime('2026-10-24T13:30:00Z'), '20:30');
  assert.equal(formatThaiTime('2026-10-23T23:30:00Z'), '06:30');
  assert.equal(formatThaiTime('2026-10-24T16:30:00+03:00'), '20:30');
  assert.equal(formatThaiTime('2026-10-24T13:30:00'), '—');
  assert.equal(formatThaiTime('not-a-time'), '—');
  assert.equal(formatThaiTime(null), '—');
});

test('news includes both currencies, preserves simultaneous events, and is not fabricated for missing categories', () => {
  const events = getNewsForSymbol('EURUSD');
  assert.equal(events.length, 6);
  assert.equal(new Set(events.map((item) => item.id)).size, 6);
  assert.deepEqual([...new Set(events.map((item) => item.currency))].sort(), ['EUR', 'USD']);
  assert.deepEqual(events.map((item) => formatThaiTime(item.time)), ['15:00', '16:00', '20:30', '20:30', '21:00', '21:30']);
  assert.ok(events.every((item, index) => index === 0 || Date.parse(events[index - 1].time) <= Date.parse(item.time)));
  assert.equal(new Set(NEWS_EVENTS.map((item) => item.id)).size, NEWS_EVENTS.length);
  assert.ok(NEWS_EVENTS.every((item) => item.actual === null && item.mock));
  assert.match(ACTUAL_UNAVAILABLE_LABEL, /รอบรายวัน/);
  assert.ok(getNewsForSymbol('EURJPY').some((item) => item.currency === 'JPY'));
  assert.ok(getNewsForSymbol('XAUUSD').every((item) => item.currency === 'USD'));
  assert.deepEqual(getNewsForSymbol('WTI'), []);
  assert.deepEqual(getNewsForSymbol('BRENT'), []);
  assert.deepEqual(getNewsForSymbol('UNKNOWN'), []);
});

test('numeric scenarios reverse when affected currency changes from quote to base', () => {
  const cpi = NEWS_EVENTS.find((item) => item.id === 'demo-us-cpi');
  const quote = getEventScenarios(cpi, 'EURUSD');
  const base = getEventScenarios(cpi, 'USDJPY');
  assert.deepEqual(quote.map((item) => item.direction), ['up', 'neutral', 'down']);
  assert.deepEqual(base.map((item) => item.direction), ['down', 'neutral', 'up']);
  assert.ok(quote.every((item) => item.summary.includes('อาจ') || item.direction === 'neutral'));
  assert.equal(getEventScenarios(cpi, 'EURJPY')[0].direction, 'uncertain');
});

test('unemployment polarity differs from inflation and speeches contain no fake forecasts', () => {
  const unemployment = NEWS_EVENTS.find((item) => item.id === 'demo-gbp-unemployment');
  assert.deepEqual(getEventScenarios(unemployment, 'GBPUSD').map((item) => item.direction), ['up', 'neutral', 'down']);
  const speech = NEWS_EVENTS.find((item) => item.id === 'demo-fed-speech');
  assert.equal(speech.forecast, null);
  assert.equal(speech.previous, null);
  assert.equal(speech.numeric, false);
  const scenarios = getEventScenarios(speech, 'EURUSD');
  assert.deepEqual(scenarios.map((item) => item.key), ['hawkish', 'neutral', 'dovish']);
  assert.deepEqual(scenarios.map((item) => item.direction), ['down', 'neutral', 'up']);
  assert.ok(scenarios.every((item) => !item.condition.includes('null')));
});

test('metal outcomes are conditional and oil does not acquire a made-up directional forecast', () => {
  const cpi = NEWS_EVENTS.find((item) => item.id === 'demo-us-cpi');
  const gold = getEventScenarios(cpi, 'XAUUSD');
  assert.match(gold[0].summary, /อาจ.*หาก/);
  assert.equal(gold[0].direction, 'up');
  assert.ok(getEventScenarios(cpi, 'WTI').every((item) => item.direction === 'uncertain'));
  assert.deepEqual(getEventScenarios(null, 'EURUSD'), []);
});

test('fictional catalog demonstrates both strong majorities and exact balance without changing EURUSD', () => {
  assert.equal(getSentiment('GBPUSD').long, 88);
  assert.equal(getSentiment('AUDJPY').long, 82);
  assert.equal(getSentiment('USDJPY').short, 91);
  assert.equal(getSentiment('EURJPY').short, 84);
  assert.equal(getSentiment('EURCHF').long, 50);
  assert.equal(getSentiment('EURCHF').short, 50);
  assert.equal(getSentiment('EURUSD').long, 68);
});
