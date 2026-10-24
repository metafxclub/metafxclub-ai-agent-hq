import test from 'node:test';
import assert from 'node:assert/strict';
import { NEWS_EVENTS } from '../src/sentiment-data.js';
import { getNewsExplainer } from '../src/news-explainers.js';

const eventById = id => NEWS_EVENTS.find(event => event.id === id);
const textFor = id => getNewsExplainer(eventById(id)).lines.join(' ');
const sourceHosts = new Set(['www.spglobal.com', 'economy-finance.ec.europa.eu', 'www.anz.co.nz', 'www.bls.gov', 'www.statcan.gc.ca', 'www.stat.go.jp', 'www.ons.gov.uk', 'www.abs.gov.au', 'www.ecb.europa.eu', 'www.federalreserve.gov', 'www.snb.ch']);

test('every existing event gets four concise Thai points and a primary source', () => {
  for (const event of NEWS_EVENTS) {
    const result = getNewsExplainer(event);
    assert.equal(result.lines.length, 4);
    assert.notEqual(result.title, 'อ่านข่าวเศรษฐกิจอย่างไร', event.id);
    assert.ok(result.lines.every(line => typeof line === 'string' && line.length > 0 && line.length <= 75 && /[ก-๙]/.test(line)));
    const source = new URL(result.sourceUrl);
    assert.equal(source.protocol, 'https:');
    assert.ok(sourceHosts.has(source.hostname), source.hostname);
    assert.ok(result.sourceName.length > 0);
    assert.doesNotMatch(result.lines.join(' '), /จะขึ้นแน่นอน|จะลงแน่นอน|รับประกัน|BUY|SELL/);
  }
});

test('PMI distinguishes index levels, month-on-month direction, and forecast comparison', () => {
  const text = textFor('demo-eur-pmi');
  assert.match(text, /ไม่ใช่ %/);
  assert.match(text, /50 = คงเดิม/);
  assert.match(text, /สูงกว่า = ขยาย/);
  assert.match(text, /ต่ำกว่า = หดจากเดือนก่อน/);
  assert.match(text, /ดีขึ้นแต่ยังต่ำกว่า 50 = ยังหดตัว/);
  assert.match(text, /คาด/);
});

test('inflation definitions distinguish core, monthly changes, and Japanese annual readings', () => {
  assert.match(textFor('demo-us-core-cpi'), /ไม่นับอาหารและพลังงาน/);
  assert.match(textFor('demo-us-cpi'), /m\/m เทียบเดือนก่อน/);
  assert.match(textFor('demo-us-cpi'), /ไม่ใช่ราคาลด/);
  assert.match(textFor('demo-jpy-cpi'), /เดือนเดียวกันปีก่อน ไม่ใช่เดือนก่อน/);
  assert.equal(new URL(getNewsExplainer(eventById('demo-jpy-cpi')).sourceUrl).hostname, 'www.stat.go.jp');
  assert.equal(new URL(getNewsExplainer(eventById('demo-cad-cpi')).sourceUrl).hostname, 'www.statcan.gc.ca');
});

test('labour and confidence explainers avoid mixing denominators or treating bigger as always better', () => {
  assert.match(textFor('demo-gbp-unemployment'), /หารกำลังแรงงาน ไม่ใช่ประชากรทั้งหมด/);
  assert.match(textFor('demo-gbp-unemployment'), /สูงขึ้นอาจสะท้อนแรงงานอ่อนลง/);
  assert.match(textFor('demo-aud-employment'), /จำนวนผู้มีงานทำ/);
  assert.match(textFor('demo-eur-confidence'), /ไม่ใช่อัตราโตของยอดขาย/);
  assert.match(textFor('demo-nzd-confidence'), /ไม่ใช่ GDP/);
});

test('speeches remain qualitative and educational content never adopts mock actual values', () => {
  for (const id of ['demo-ecb-speech', 'demo-fed-speech', 'demo-chf-speech']) {
    const event = eventById(id), result = getNewsExplainer(event);
    assert.match(result.lines.join(' '), /มติ/);
    assert.match(result.lines.join(' '), /อาจ/);
    assert.deepEqual(result, getNewsExplainer({ ...event, actual: 999, forecast: 998, previous: 997, time: '1900-01-01T00:00:00Z' }));
  }
});

test('unknown events have a bounded fallback and returned arrays cannot corrupt later panels', () => {
  for (const event of [null, undefined, {}, { title: '<script>bad()</script>', metric: 'unknown' }]) {
    const result = getNewsExplainer(event);
    assert.equal(result.title, 'อ่านข่าวเศรษฐกิจอย่างไร');
    assert.equal(result.lines.length, 4);
    assert.doesNotMatch(JSON.stringify(result), /<script>/);
  }
  const event = eventById('demo-eur-pmi'), first = getNewsExplainer(event);
  first.lines[0] = 'changed locally';
  assert.notEqual(getNewsExplainer(event).lines[0], first.lines[0]);
  assert.equal(event.actual, null);
});
