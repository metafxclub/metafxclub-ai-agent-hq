import * as THREE from 'three';
import { STATE_META } from './data.js';

// Horizon identity is radius + plane + label; color always comes from trend state.
export const ORBIT_PROFILES = [
  { radius: .42, tilt: 1.12, turn: .04, rate: .72, phase: 2.2 },
  { radius: .50, tilt: 1.06, turn: -.62, rate: -.53, phase: .65 },
  { radius: .58, tilt: 1.10, turn: 1.25, rate: .39, phase: 1.4 },
];

// The scene and inspector use the same phase for an asset, independent of order.
export function getNucleusPhase(symbol = '') {
  const key = String(symbol ?? '').trim().toUpperCase();
  if (!key) return 0;
  let hash = 2166136261;
  for (const character of key) hash = Math.imul(hash ^ character.charCodeAt(0), 16777619);
  return (hash >>> 0) / 4294967296 * Math.PI * 2;
}

export function createNucleusResources() {
  return {
    tracks: ORBIT_PROFILES.map(p => new THREE.TorusGeometry(p.radius, .0065, 5, 96)),
    halos: ORBIT_PROFILES.map(p => new THREE.TorusGeometry(p.radius, .015, 5, 96)),
    trails: ORBIT_PROFILES.map(p => new THREE.TorusGeometry(p.radius, .007, 5, 20, .30)),
    bead: new THREE.SphereGeometry(.028, 12, 8),
    glow: new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0], 3)),
  };
}

export function createGlow(color, size = 18) {
  return new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { tint: { value: new THREE.Color(color) }, size: { value: size }, strength: { value: 1 } },
    vertexShader: `uniform float size; void main() { gl_PointSize=size; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
    fragmentShader: `uniform vec3 tint; uniform float strength;
      void main() { float r=length(gl_PointCoord-.5)*2.0; if(r>1.0) discard;
        gl_FragColor=vec4(tint,pow(1.0-r,2.5)*strength);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
}

export function createNucleus(states, resources, phase = 0) {
  const group = new THREE.Group();
  const orbits = ORBIT_PROFILES.map((profile, i) => {
    const frame = new THREE.Group(), plane = new THREE.Group();
    frame.rotation.z = profile.turn; plane.rotation.x = profile.tilt;
    frame.add(plane); group.add(frame);
    const candidate = states?.[i];
    const state = Object.hasOwn(STATE_META, candidate) ? candidate : 'unknown';
    const color = STATE_META[state].color;
    const line = new THREE.Mesh(resources.tracks[i], new THREE.MeshBasicMaterial({ color, transparent: true, opacity: state === 'unknown' ? .45 : .92, depthWrite: false }));
    const halo = new THREE.Mesh(resources.halos[i], new THREE.MeshBasicMaterial({ color, transparent: true, opacity: .09, depthWrite: false, blending: THREE.AdditiveBlending }));
    const trail = new THREE.Mesh(resources.trails[i], new THREE.MeshBasicMaterial({ color, transparent: true, opacity: .52, depthWrite: false, blending: THREE.AdditiveBlending }));
    const bead = new THREE.Mesh(resources.bead, new THREE.MeshBasicMaterial({ color }));
    const glow = new THREE.Points(resources.glow, createGlow(color, 14)); bead.add(glow);
    plane.add(line, halo, trail, bead);
    // No animated beacon on a missing-data orbit.
    bead.visible = trail.visible = state !== 'unknown';
    return { frame, plane, line, halo, trail, bead, glow, profile, state };
  });
  const nucleus = { group, orbits, phase };
  updateNucleus(nucleus, 0);
  return nucleus;
}

export function updateNucleus(nucleus, time, pixelScale = 1) {
  nucleus.orbits.forEach(({ frame, plane, bead, trail, glow, profile }, i) => {
    const angle = time * profile.rate + profile.phase + nucleus.phase;
    frame.rotation.z = profile.turn + Math.sin(time * .09 + i) * .075;
    plane.rotation.x = profile.tilt + Math.sin(time * .12 + i * 1.7) * .06;
    bead.position.set(Math.cos(angle) * profile.radius, Math.sin(angle) * profile.radius, 0);
    trail.rotation.z = angle - (profile.rate > 0 ? .30 : 0);
    glow.material.uniforms.size.value = 14 * pixelScale;
  });
}

export function disposeNucleusGraph(scene) {
  const geometries = new Set(), materials = new Set();
  scene.traverse(object => {
    if (object.geometry) geometries.add(object.geometry);
    if (object.material) (Array.isArray(object.material) ? object.material : [object.material]).forEach(m => materials.add(m));
  });
  geometries.forEach(g => g.dispose()); materials.forEach(m => m.dispose());
}
