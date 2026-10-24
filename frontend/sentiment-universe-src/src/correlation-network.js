export const CORRELATION_SEGMENTS = 20;
export const STRONG_CORRELATION_THRESHOLD = .70;
export const OVERVIEW_CORRELATION_THRESHOLD = .60;
export const NEUTRAL_CORRELATION_THRESHOLD = .30;
export const BRIGHT_YELLOW_CORRELATION_THRESHOLD = .10;
export const DEEP_CORRELATION_THRESHOLD = .80;

const PALETTE = {
  brightYellow: '#ffe66d', gold: '#dfb64f',
  positive: '#66dda0', deepPositive: '#18985b',
  negative: '#ff9292', deepNegative: '#c9384a', unavailable: '#778593',
};
const validCoefficient=value=>Number.isFinite(value)&&Math.abs(value)<=1;
function mixHex(first, second, amount) {
  const t=Math.max(0,Math.min(1,amount));
  const channel=offset=>Math.round(parseInt(first.slice(offset,offset+2),16)*(1-t)+parseInt(second.slice(offset,offset+2),16)*t).toString(16).padStart(2,'0');
  return `#${channel(1)}${channel(3)}${channel(5)}`;
}

export function correlationTone(value) {
  if (!validCoefficient(value)) return 'unavailable';
  if (Math.abs(value) <= NEUTRAL_CORRELATION_THRESHOLD) return 'neutral';
  return value > 0 ? 'positive' : 'negative';
}

export function correlationColor(value) {
  if (!validCoefficient(value)) return PALETTE.unavailable;
  const strength=Math.abs(value);
  if (strength <= BRIGHT_YELLOW_CORRELATION_THRESHOLD) return PALETTE.brightYellow;
  if (strength <= NEUTRAL_CORRELATION_THRESHOLD) return mixHex(PALETTE.brightYellow,PALETTE.gold,(strength-.10)/.20);
  const base=value>0?PALETTE.positive:PALETTE.negative;
  const deep=value>0?PALETTE.deepPositive:PALETTE.deepNegative;
  // The unspecified 30–40% gap changes gradually, without dropping an edge.
  if (strength < .40) return mixHex(PALETTE.gold,base,(strength-.30)/.10);
  if (strength < DEEP_CORRELATION_THRESHOLD) return mixHex(base,deep,(strength-.40)/.40);
  return deep;
}

// The overview emphasizes both signs at the same absolute strength. This
// controls the line attribute directly; it does not alter packet eligibility.
export function correlationOverviewStyle(value) {
  if (!validCoefficient(value)) return {strength:null,emphasized:false,opacity:0};
  const strength = Math.abs(value);
  const emphasized = strength >= OVERVIEW_CORRELATION_THRESHOLD;
  const opacity = emphasized
    ? .30 + .26 * (strength - OVERVIEW_CORRELATION_THRESHOLD) / (1 - OVERVIEW_CORRELATION_THRESHOLD)
    : strength <= .10 ? .24
    : strength <= .30 ? .16 + .08 * (.30-strength)/.20
    : .16 + .03 * (strength-.30)/.30;
  return { strength, emphasized, opacity };
}

export function correlationCounterpart(edge, symbol) {
  if (!edge || !symbol) return null;
  return edge.source === symbol ? edge.target : edge.target === symbol ? edge.source : null;
}

export function correlationLabelText(edge, symbol) {
  const counterpart = correlationCounterpart(edge, symbol);
  if (counterpart && !validCoefficient(edge.value)) return `${counterpart} ไม่มีข้อมูล`;
  return counterpart ? `${counterpart} ${edge.value > 0 ? '+' : ''}${Math.round(edge.value * 100)}%` : '';
}

export function correlationKey(source, target) {
  return [source, target].sort().join('|');
}

// One edge per unordered pair. A caller must supply observed coefficients;
// omitted data stays empty instead of silently creating sample relationships.
export function buildCorrelationNetwork(pairs, lookup = () => []) {
  const catalog = [...new Map(pairs.map(pair => [pair.symbol, pair])).values()];
  const edges = [];
  for (let sourceIndex = 0; sourceIndex < catalog.length; sourceIndex++) {
    const source = catalog[sourceIndex];
    const values = new Map(lookup(source.symbol).map(row => [row.symbol, row.value]));
    for (let targetIndex = sourceIndex + 1; targetIndex < catalog.length; targetIndex++) {
      const target = catalog[targetIndex], value = values.get(target.symbol);
      if (!Number.isFinite(value) || value < -1 || value > 1) continue;
      edges.push({ source: source.symbol, target: target.symbol, value,
        sourceClass: source.assetClass, targetClass: target.assetClass,
        key: correlationKey(source.symbol, target.symbol), index: edges.length });
    }
  }
  return edges;
}

export function visibleCorrelationEdges(edges, filter = 'all') {
  return filter === 'all' ? edges : edges.filter(edge => edge.sourceClass === filter && edge.targetClass === filter);
}

export function incidentCorrelationEdges(edges, symbol) {
  return symbol ? edges.filter(edge => edge.source === symbol || edge.target === symbol) : [];
}

export function strongCorrelationEdges(edges) {
  return edges.filter(edge => Math.abs(edge.value) > STRONG_CORRELATION_THRESHOLD);
}

export function correlationFlowProgress(time, index = 0) {
  const phase = index * .173;
  return ((time * (.12 + index % 5 * .013) + phase) % 1 + 1) % 1;
}

export function correlationCurveControl(start, end, index = 0) {
  const dx = end.x - start.x, dy = end.y - start.y, dz = end.z - start.z;
  const planar = Math.max(.01, Math.hypot(dx, dy));
  const bend = Math.min(4.6, Math.hypot(dx, dy, dz) * (.15 + index % 4 * .025));
  const sign = index % 2 ? 1 : -1;
  return {
    x: (start.x + end.x) * .5 - dy / planar * bend * sign,
    y: (start.y + end.y) * .5 + dx / planar * bend * sign,
    z: (start.z + end.z) * .5 + .45 + Math.sin(index * 1.31) * bend * .72,
  };
}

export function correlationCurvePoint(start, end, control, progress, output = {}) {
  const t = Math.max(0, Math.min(1, progress)), u = 1 - t, a = u * u, b = 2 * u * t, c = t * t;
  output.x = a * start.x + b * control.x + c * end.x;
  output.y = a * start.y + b * control.y + c * end.y;
  output.z = a * start.z + b * control.z + c * end.z;
  return output;
}

// LineSegments raycast indices refer to the first vertex of a tiny segment,
// not to a whole asset-to-asset edge.
export function correlationEdgeAtVertex(edges, vertexIndex, segments = CORRELATION_SEGMENTS) {
  if (!Number.isInteger(vertexIndex) || vertexIndex < 0) return null;
  return edges[Math.floor(vertexIndex / (segments * 2))] ?? null;
}
