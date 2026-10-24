import assert from 'node:assert/strict';
import test from 'node:test';
import * as THREE from 'three';
import { PAIRS, STATE_META } from '../src/data.js';
import { advanceMotion } from '../src/motion.js';
import { createNucleusResources, createNucleus, getNucleusPhase, updateNucleus, disposeNucleusGraph } from '../src/NucleusNode.js';

function fixture(t, states = ['up', 'range', 'down'], phase = 0) {
  const resources = createNucleusResources();
  const nucleus = createNucleus(states, resources, phase);
  t.after(() => disposeNucleusGraph(nucleus.group));
  return { resources, nucleus };
}

const snapshot = nucleus => nucleus.orbits.map(({ frame, plane, bead, trail }) => ({
  frame: frame.quaternion.toArray(), plane: plane.quaternion.toArray(),
  bead: bead.position.toArray(), trail: trail.quaternion.toArray(),
}));

test('the three horizon planes remain distinct instead of collapsing into concentric rings', t => {
  const { nucleus } = fixture(t);
  assert.equal(nucleus.orbits.length, 3);
  for (const time of [0, 3, 60, 3600, 86400]) {
    updateNucleus(nucleus, time);
    nucleus.group.updateMatrixWorld(true);
    const normals = nucleus.orbits.map(({ plane }) =>
      new THREE.Vector3(0, 0, 1).applyQuaternion(plane.getWorldQuaternion(new THREE.Quaternion())));
    normals.forEach(normal => assert.ok(normal.toArray().every(Number.isFinite)));
    for (let a = 0; a < normals.length; a++) {
      for (let b = a + 1; b < normals.length; b++) {
        assert.ok(Math.abs(normals[a].dot(normals[b])) < .98,
          `horizons ${a}/${b} must have distinguishable orbital planes at ${time}`);
      }
    }
  }
});

test('beads stay attached to their actual torus track and tails follow in either direction', t => {
  const { nucleus } = fixture(t, ['up', 'range', 'down'], 1.7);
  for (const time of [0, 1 / 60, 1, 100, 86400]) {
    updateNucleus(nucleus, time);
    for (const { bead, line, trail, profile } of nucleus.orbits) {
      const radius = line.geometry.parameters.radius;
      assert.ok(bead.position.toArray().every(Number.isFinite));
      assert.ok(Math.abs(bead.position.length() - radius) < 1e-10);
      assert.equal(bead.position.z, 0, 'the bead belongs to its tilted local plane');
      const headAngle = trail.rotation.z + (profile.rate > 0 ? trail.geometry.parameters.arc : 0);
      const trailHead = new THREE.Vector3(Math.cos(headAngle) * radius, Math.sin(headAngle) * radius, 0);
      assert.ok(trailHead.distanceTo(bead.position) < 1e-9, 'the trail must meet the moving bead');
    }
  }
});

test('paused or hidden clocks freeze every nucleus transform, including after a size change', t => {
  const { nucleus } = fixture(t);
  let time = 19.125;
  updateNucleus(nucleus, time);
  const frozen = snapshot(nucleus);
  for (const state of [{ playing: false }, { playing: true, hidden: true }, { playing: true, dragging: true }]) {
    time = advanceMotion(time, 86400, { speed: 1.8, ...state });
    updateNucleus(nucleus, time, 2);
    assert.deepEqual(snapshot(nucleus), frozen);
  }
  const resumed = advanceMotion(time, 1 / 60, { playing: true });
  updateNucleus(nucleus, resumed);
  assert.notDeepEqual(snapshot(nucleus), frozen);
  assert.ok(nucleus.orbits.every(({ bead }, index) =>
    bead.position.distanceTo(new THREE.Vector3(...frozen[index].bead)) < .02),
  'resume advances one fresh frame, without a long-pause position jump');
});

test('catalog horizons retain their trend colors and missing data never shows an active bead', t => {
  const resources = createNucleusResources(), scene = new THREE.Group();
  t.after(() => disposeNucleusGraph(scene));
  for (const pair of PAIRS) {
    const nucleus = createNucleus(pair.states, resources);
    scene.add(nucleus.group);
    for (const time of [0, 9, 86400]) {
      updateNucleus(nucleus, time);
      nucleus.orbits.forEach(({ line, halo, bead, trail }, i) => {
        const state = pair.states[i], expected = new THREE.Color(STATE_META[state].color).getHexString();
        for (const mesh of [line, halo, bead, trail]) assert.equal(mesh.material.color.getHexString(), expected);
        assert.equal(bead.visible, state !== 'unknown', `${pair.symbol} horizon ${i}`);
        assert.equal(trail.visible, state !== 'unknown', `${pair.symbol} horizon ${i}`);
        assert.equal(line.visible, true, 'missing data keeps its neutral reference orbit');
      });
    }
  }
});

test('absent, invalid and prototype-like trend states behave as missing data', t => {
  const resources = createNucleusResources(), scene = new THREE.Group();
  t.after(() => disposeNucleusGraph(scene));
  for (const states of [undefined, null, [], [null, 'invalid', undefined], ['constructor', '__proto__', 'toString']]) {
    const nucleus = createNucleus(states, resources);
    scene.add(nucleus.group);
    updateNucleus(nucleus, 25);
    nucleus.orbits.forEach(({ state, line, bead, trail }) => {
      assert.equal(state, 'unknown');
      assert.equal(line.material.color.getHexString(), new THREE.Color(STATE_META.unknown.color).getHexString());
      assert.equal(bead.visible, false);
      assert.equal(trail.visible, false);
    });
  }
});

test('the same asset has matching nucleus positions in scene and inspector at any shared clock time', t => {
  const resources = createNucleusResources(), scene = new THREE.Group();
  t.after(() => disposeNucleusGraph(scene));
  const phases = PAIRS.map(({ symbol }) => getNucleusPhase(symbol));
  assert.equal(new Set(phases).size, PAIRS.length, 'assets retain varied orbital phases');
  assert.ok(phases.every(phase => Number.isFinite(phase) && phase >= 0 && phase < Math.PI * 2));
  for (const pair of PAIRS) {
    const main = createNucleus(pair.states, resources, getNucleusPhase(pair.symbol));
    const expanded = createNucleus(pair.states, resources, getNucleusPhase(` ${pair.symbol.toLowerCase()} `));
    scene.add(main.group, expanded.group);
    for (const time of [0, 1.5, 190, 86400]) {
      updateNucleus(main, time, .55);
      updateNucleus(expanded, time, 1.6);
      assert.deepEqual(snapshot(main), snapshot(expanded), `${pair.symbol}: inspector must match scene`);
    }
  }
});

test('shared geometry does not couple different assets or resize their tracks', t => {
  const resources = createNucleusResources(), scene = new THREE.Group();
  t.after(() => disposeNucleusGraph(scene));
  const a = createNucleus(['up', 'unknown', 'down'], resources, .3);
  const b = createNucleus(['down', 'range', 'up'], resources, 2);
  scene.add(a.group, b.group);
  const original = snapshot(b);
  const geometry = resources.tracks.map(track => Array.from(track.attributes.position.array));
  updateNucleus(a, 70, 3);
  assert.deepEqual(snapshot(b), original, 'moving one instance must not move another');
  resources.tracks.forEach((track, i) => {
    assert.equal(a.orbits[i].line.geometry, b.orbits[i].line.geometry);
    assert.notEqual(a.orbits[i].line.material, b.orbits[i].line.material);
    assert.deepEqual(Array.from(track.attributes.position.array), geometry[i]);
  });
});

test('cleanup disposes all unique GPU resources once even when many assets share geometry', () => {
  const resources = createNucleusResources(), scene = new THREE.Group();
  for (const pair of PAIRS) scene.add(createNucleus(pair.states, resources).group);
  const counters = new Map();
  scene.traverse(object => {
    const items = [object.geometry, ...(Array.isArray(object.material) ? object.material : [object.material])].filter(Boolean);
    for (const item of items) {
      if (counters.has(item)) continue;
      counters.set(item, 0);
      item.addEventListener('dispose', () => counters.set(item, counters.get(item) + 1));
    }
  });
  assert.ok(counters.size > 0);
  disposeNucleusGraph(scene);
  for (const [resource, count] of counters) assert.equal(count, 1, `${resource.type} must be disposed exactly once`);
});
