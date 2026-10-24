import assert from 'node:assert/strict';
import test from 'node:test';
import { advanceMotion, connectionVisible, MOTION_SPEEDS, starOrbit } from '../src/motion.js';

const close = (actual, expected, message) => assert.ok(Math.abs(actual - expected) < 1e-10,
  `${message}: expected ${expected}, received ${actual}`);

test('manual pause and effective reduced motion freeze the shared animation clock', () => {
  // App represents either explicit pause or reduced motion as playing=false.
  for (const speed of MOTION_SPEEDS) {
    let time = 12.375;
    for (const delta of [1 / 60, 0.05, 12, 86400]) {
      time = advanceMotion(time, delta, { playing: false, speed });
      assert.equal(time, 12.375);
    }
  }
});

test('hidden pages and pointer drags freeze animation without changing the clock', () => {
  for (const state of [{ hidden: true }, { dragging: true }, { hidden: true, dragging: true }]) {
    assert.equal(advanceMotion(7.5, 60, { playing: true, speed: 1.8, ...state }), 7.5);
  }
});

test('resume advances one fresh frame instead of replaying time spent paused or hidden', () => {
  let time = advanceMotion(2, 1 / 60, { playing: true });
  const beforePause = time;
  time = advanceMotion(time, 86400, { playing: false });
  time = advanceMotion(time, 86400, { playing: true, hidden: true });
  assert.equal(time, beforePause);
  time = advanceMotion(time, 1 / 60, { playing: true });
  close(time, beforePause + 1 / 60, 'fresh frame after resume');
});

test('all offered speeds produce proportional progress across normal frames', () => {
  assert.deepEqual(MOTION_SPEEDS, [0.5, 1, 1.8]);
  for (const speed of MOTION_SPEEDS) {
    let time = 0;
    for (let frame = 0; frame < 600; frame++) time = advanceMotion(time, 1 / 60, { playing: true, speed });
    close(time, 10 * speed, `ten seconds at ${speed}x`);
  }
});

test('long frames are bounded and invalid or negative frame durations cannot corrupt time', () => {
  for (const speed of MOTION_SPEEDS) {
    close(advanceMotion(4, 10, { playing: true, speed }), 4 + 0.05 * speed, 'bounded long frame');
    for (const delta of [-1, 0, NaN, Infinity, -Infinity, undefined, '0.01']) {
      assert.equal(advanceMotion(4, delta, { playing: true, speed }), 4, `invalid duration ${delta}`);
    }
  }
});

test('unsupported speeds fall back to normal speed rather than reversing or exploding motion', () => {
  for (const speed of [0, -1, 100, NaN, Infinity, null, '1.8']) {
    close(advanceMotion(3, 0.02, { playing: true, speed }), 3.02, `unsupported speed ${speed}`);
  }
});

test('stellar trajectories remain deterministic, finite, and inside their local envelopes over long sessions', () => {
  for (const radius of [0, 0.384, 1.4, 2.925, 3.9]) {
    for (const eccentricity of [0.72, 0.81, 0.9]) {
      for (const phase of [0, 1.7, 8]) {
        for (const rate of [-0.037, 0.019, 0.028, 0.037]) {
          for (const time of [0, 1 / 60, 4, 60, 3600, 86400]) {
            const args = [radius, 0.38, eccentricity, phase, time, rate];
            const position = starOrbit(...args);
            assert.deepEqual(position, starOrbit(...args));
            assert.ok(position.every(Number.isFinite));
            const [x, y, z] = position;
            const localRadius = Math.hypot(x, y / eccentricity);
            assert.ok(localRadius >= radius * 0.925 - 1e-10 && localRadius <= radius * 1.075 + 1e-10,
              'stars must stay inside the known camera envelope');
            assert.ok(z >= -0.04 - 1e-10 && z <= 0.32 + 1e-10);
          }
        }
      }
    }
  }
});

test('stars move independently within a galaxy instead of remaining fixed under its group rotation', () => {
  const initial = starOrbit(1.2, 0, 0.72, 1.7, 0, 0.019);
  const slow = starOrbit(1.2, 0, 0.72, 1.7, 10, 0.019);
  const fast = starOrbit(1.2, 0, 0.72, 1.7, 10, 0.037);
  const reverse = starOrbit(1.2, 0, 0.72, 1.7, 10, -0.037);
  const angle = ([x, y]) => Math.atan2(y / 0.72, x);
  assert.notDeepEqual(slow, initial);
  assert.ok(angle(fast) > angle(slow) && angle(slow) > 0);
  assert.ok(angle(reverse) < 0);
  assert.ok(Math.hypot(fast[0] - slow[0], fast[1] - slow[1]) > 0.1);
  assert.notEqual(slow[2], initial[2], 'motion also has shallow depth variation');
});

test('even a small one-member cluster has visible local movement', () => {
  const start = starOrbit(0.384, 0.38, 0.72, 6, 0, 0.019);
  const later = starOrbit(0.384, 0.38, 0.72, 6, 4, 0.019);
  assert.ok(Math.hypot(...later.map((value, i) => value - start[i])) > 0.01);
});

test('connections only remain visible when both endpoints survive the category filter', () => {
  const classes = ['forex', 'metals', 'oil'];
  for (const a of classes) {
    for (const b of classes) {
      assert.equal(connectionVisible(a, b, 'all'), true);
      for (const filter of classes) {
        const expected = new Set([a, b]).size === 1 && a === filter;
        assert.equal(connectionVisible(a, b, filter), expected, `${a} to ${b}, filter ${filter}`);
        assert.equal(connectionVisible(b, a, filter), expected, 'visibility is endpoint-order independent');
      }
      assert.equal(connectionVisible(a, b, 'unsupported'), false);
    }
  }
});
