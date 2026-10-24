import test from 'node:test';
import assert from 'node:assert/strict';
import { PAIRS } from '../src/data.js';
import { getCorrelations } from '../src/sentiment-data.js';
import { buildCorrelationNetwork, visibleCorrelationEdges, correlationEdgeAtVertex, correlationKey, CORRELATION_SEGMENTS, incidentCorrelationEdges, strongCorrelationEdges, correlationFlowProgress, correlationCurveControl, correlationCurvePoint, correlationOverviewStyle, correlationCounterpart, correlationLabelText, correlationTone, correlationColor } from '../src/correlation-network.js';

const network = buildCorrelationNetwork(PAIRS, getCorrelations);

test('missing lookup never produces fixture relationships', () => {
  assert.deepEqual(buildCorrelationNetwork(PAIRS), []);
});

test('32 assets produce exactly 496 unique undirected sample correlations, including oil', () => {
  assert.equal(network.length, 32 * 31 / 2);
  assert.equal(new Set(network.map(edge => edge.key)).size, 496);
  assert.ok(network.every(edge => edge.source !== edge.target));
  assert.ok(network.some(edge => edge.key === 'BRENT|WTI'));
  for (const edge of network) {
    assert.equal(edge.value, getCorrelations(edge.target).find(row => row.symbol === edge.source).value);
  }
});

test('category filtering keeps only edges with both endpoints visible', () => {
  assert.equal(visibleCorrelationEdges(network, 'forex').length, 378);
  assert.equal(visibleCorrelationEdges(network, 'metals').length, 1);
  assert.equal(visibleCorrelationEdges(network, 'oil').length, 1);
  for (const filter of ['forex', 'metals', 'oil']) {
    assert.ok(visibleCorrelationEdges(network, filter).every(edge => edge.sourceClass === filter && edge.targetClass === filter));
  }
});

test('each raycast segment maps to exactly its visible edge after filtering', () => {
  const stride = CORRELATION_SEGMENTS * 2;
  for (const edges of [network, visibleCorrelationEdges(network, 'forex'), visibleCorrelationEdges(network, 'oil')]) {
    edges.forEach((edge, index) => {
      assert.equal(correlationEdgeAtVertex(edges, index * stride), edge);
      assert.equal(correlationEdgeAtVertex(edges, index * stride + stride - 2), edge);
    });
    assert.equal(correlationEdgeAtVertex(edges, edges.length * stride), null);
  }
  assert.equal(correlationEdgeAtVertex(network, -1), null);
});

test('duplicate catalog entries do not duplicate lines and reverse selection keys match', () => {
  assert.equal(buildCorrelationNetwork([...PAIRS, PAIRS[0]], getCorrelations).length, 496);
  assert.equal(correlationKey('GBPUSD', 'EURUSD'), correlationKey('EURUSD', 'GBPUSD'));
});

test('selected asset emphasizes all incident edges without losing the unrelated network', () => {
  assert.equal(incidentCorrelationEdges(network, 'EURUSD').length, 31);
  assert.equal(incidentCorrelationEdges(visibleCorrelationEdges(network, 'forex'), 'EURUSD').length, 27);
  assert.equal(incidentCorrelationEdges(visibleCorrelationEdges(network, 'metals'), 'XAUUSD').length, 1);
  assert.equal(incidentCorrelationEdges(visibleCorrelationEdges(network, 'metals'), 'EURUSD').length, 0);
  assert.equal(incidentCorrelationEdges(network, null).length, 0);
  assert.equal(network.length, 496);
});

test('light packets exist strictly above absolute 0.70, in both directions', () => {
  const edges = [-.71, -.70, 0, .70, .71].map(value => ({ value }));
  assert.deepEqual(strongCorrelationEdges(edges).map(edge => edge.value), [-.71, .71]);
  const paused = correlationFlowProgress(5, 7);
  assert.equal(correlationFlowProgress(5, 7), paused);
  assert.notEqual(correlationFlowProgress(5.2, 7), paused);
  assert.ok(correlationFlowProgress(10000, 7) >= 0 && correlationFlowProgress(10000, 7) < 1);
});

test('overview emphasizes both signs at 60 percent while retaining all edges and the stricter flow threshold', () => {
  for (const value of [0, .25, .599, .60, .70, .86, 1]) {
    const style = correlationOverviewStyle(value);
    assert.deepEqual(style, correlationOverviewStyle(-value));
    assert.equal(style.emphasized, value >= .60);
    assert.ok(style.opacity >= .16 && style.opacity <= .56);
  }
  assert.ok(correlationOverviewStyle(.60).opacity > correlationOverviewStyle(.599).opacity * 1.5);
  assert.equal(strongCorrelationEdges([{value:.60},{value:.70}]).length, 0);
  assert.equal(incidentCorrelationEdges(network, null).length, 0);
  assert.equal(visibleCorrelationEdges(network, 'all').length, 496);
  assert.equal(correlationOverviewStyle(NaN).emphasized, false);
});

test('yellow center, gold boundary, green/red and deep colors include their exact thresholds', () => {
  for (const value of [-.30,-.10,-.001,0,.001,.10,.30]) {
    assert.equal(correlationTone(value), 'neutral');
  }
  for (const value of [.300001,.40,.60,.80,1]) {
    assert.equal(correlationTone(value), 'positive');
    assert.equal(correlationTone(-value), 'negative');
  }
  for (const value of [-.10,0,.10]) assert.equal(correlationColor(value),'#ffe66d');
  for (const value of [-.30,.30]) assert.equal(correlationColor(value),'#dfb64f');
  assert.equal(correlationColor(.40),'#66dda0');
  assert.equal(correlationColor(-.40),'#ff9292');
  for (const value of [.80,1]) assert.equal(correlationColor(value),'#18985b');
  for (const value of [-.80,-1]) assert.equal(correlationColor(value),'#c9384a');
  const luminance=hex=>[1,3,5].reduce((sum,offset,index)=>sum+parseInt(hex.slice(offset,offset+2),16)*[.2126,.7152,.0722][index],0);
  assert.ok(luminance(correlationColor(.10))>luminance(correlationColor(.30)));
  assert.ok(luminance(correlationColor(.80))<luminance(correlationColor(.40)));
  assert.ok(luminance(correlationColor(-.80))<luminance(correlationColor(-.40)));
  assert.ok(correlationOverviewStyle(.10).opacity>correlationOverviewStyle(.30).opacity);
});

test('30–40 percent gaps interpolate without missing values or an abrupt color jump', () => {
  for(const sign of[-1,1]) {
    assert.equal(correlationColor(sign*.300001),correlationColor(sign*.30));
    assert.equal(correlationColor(sign*.399999),correlationColor(sign*.40));
    const middle=correlationColor(sign*.35);
    assert.notEqual(middle,correlationColor(sign*.30));
    assert.notEqual(middle,correlationColor(sign*.40));
    for(let percent=30;percent<=40;percent++) assert.match(correlationColor(sign*percent/100),/^#[0-9a-f]{6}$/);
  }
});

test('missing or invalid coefficients are unavailable rather than a yellow zero', () => {
  const catalog=PAIRS.slice(0,2);
  for(const value of[null,undefined,NaN,Infinity,-Infinity,'0',1.01,-1.01]) {
    assert.equal(correlationTone(value),'unavailable');
    assert.equal(correlationColor(value),'#778593');
    assert.deepEqual(correlationOverviewStyle(value),{strength:null,emphasized:false,opacity:0});
    assert.equal(buildCorrelationNetwork(catalog,()=>[{symbol:catalog[1].symbol,value}]).length,0);
  }
  assert.equal(correlationTone(0),'neutral');
  assert.equal(buildCorrelationNetwork(catalog,()=>[{symbol:catalog[1].symbol,value:0}]).length,1);
  assert.equal(correlationLabelText({source:'EURUSD',target:'GBPUSD',value:null},'EURUSD'),'GBPUSD ไม่มีข้อมูล');
});

test('overview tone assignment preserves every edge and gives even zero correlation a readable baseline', () => {
  const counts = {neutral:0,positive:0,negative:0};
  for (const edge of visibleCorrelationEdges(network, 'all')) {
    counts[correlationTone(edge.value)]++;
    assert.ok(correlationOverviewStyle(edge.value).opacity >= .16);
  }
  assert.equal(Object.values(counts).reduce((sum, count) => sum + count, 0), 496);
  assert.ok(Object.values(counts).every(count => count > 0));
  assert.equal(correlationOverviewStyle(0).opacity, .24);
  assert.equal(incidentCorrelationEdges(network, null).length, 0);
  assert.equal(new Set(network.map(edge => edge.key)).size, 496);
});

test('selected connection labels identify the other endpoint with its signed coefficient', () => {
  const edge = {source:'EURUSD',target:'GBPUSD',value:.86};
  assert.equal(correlationCounterpart(edge, 'EURUSD'), 'GBPUSD');
  assert.equal(correlationLabelText(edge, 'EURUSD'), 'GBPUSD +86%');
  assert.equal(correlationLabelText(edge, 'GBPUSD'), 'EURUSD +86%');
  assert.equal(correlationLabelText({...edge,value:-.81}, 'EURUSD'), 'GBPUSD -81%');
  assert.equal(correlationLabelText(edge, null), '');
  assert.equal(correlationLabelText(edge, 'USDJPY'), '');
});

test('spatial curves preserve moving endpoints and create a non-straight path', () => {
  const start = { x: -4, y: 2, z: 0 }, end = { x: 6, y: 4, z: 1 };
  const control = correlationCurveControl(start, end, 3);
  assert.deepEqual(correlationCurvePoint(start, end, control, 0), start);
  assert.deepEqual(correlationCurvePoint(start, end, control, 1), end);
  assert.notDeepEqual(correlationCurvePoint(start, end, control, .5), { x: 1, y: 3, z: .5 });
  end.x = 8;
  assert.equal(correlationCurvePoint(start, end, correlationCurveControl(start, end, 3), 1).x, 8);
});
