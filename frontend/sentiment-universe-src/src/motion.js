// Visual choreography only. None of these values describe market activity.
export const MOTION_SPEEDS = [0.5, 1, 1.8];

export function advanceMotion(time, delta, { playing, hidden = false, dragging = false, speed = 1 }) {
  if (!playing || hidden || dragging) return time;
  const safeSpeed = MOTION_SPEEDS.includes(speed) ? speed : 1;
  return time + Math.max(0, Math.min(0.05, Number.isFinite(delta) ? delta : 0)) * safeSpeed;
}

export function starOrbit(radius, angle, eccentricity, phase, time, rate) {
  const theta = angle + time * rate;
  const r = radius * (1 + 0.075 * Math.sin(time * 0.32 + phase));
  return [Math.cos(theta) * r, Math.sin(theta) * r * eccentricity,
    0.14 + Math.sin(theta * 2 + phase) * 0.18];
}

export function connectionVisible(a, b, filter) {
  return filter === 'all' || (a === filter && b === filter);
}
