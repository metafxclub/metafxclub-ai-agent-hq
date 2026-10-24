import * as THREE from 'three';

// Geometry stays on the GPU. Only the shared, pausable clock changes each frame.
export function createFlowStream(curve, color, clock, { rate = 0.13, phase = 0, meteor = false } = {}) {
  const points = curve.getPoints(180);
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  geometry.setAttribute('aProgress', new THREE.Float32BufferAttribute(points.map((_, i) => i / 180), 1));
  const material = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { time: clock, tint: { value: new THREE.Color(color) }, rate: { value: rate },
      phase: { value: phase }, pixelScale: { value: 1 }, meteor: { value: meteor ? 1 : 0 } },
    vertexShader: `attribute float aProgress; uniform float time; uniform float rate;
      uniform float phase; uniform float pixelScale; uniform float meteor;
      varying float vLight; varying float vHead;
      void main() {
        float cycle = fract(time * rate + phase);
        float head = cycle * mix(1.3, 3.5, meteor) - 0.08;
        float behind = head - aProgress;
        vLight = exp(-max(behind, 0.0) * mix(22.0, 13.0, meteor)) * step(0.0, behind) * step(behind, 0.26);
        vLight *= smoothstep(0.0, 0.04, aProgress) * (1.0 - smoothstep(0.92, 1.0, aProgress));
        vHead = exp(-abs(behind) * 140.0);
        vec4 p = modelViewMatrix * vec4(position, 1.0);
        gl_Position = projectionMatrix * p;
        gl_PointSize = clamp((0.15 + vHead * 0.42) * pixelScale * 420.0 / max(2.0, -p.z), 1.0, 25.0);
      }`,
    fragmentShader: `uniform vec3 tint; varying float vLight; varying float vHead;
      void main() {
        float r = length(gl_PointCoord - 0.5) * 2.0;
        if (r > 1.0 || vLight < 0.008) discard;
        gl_FragColor = vec4(mix(tint, vec3(0.9, 0.97, 1.0), vHead * 0.8), pow(1.0-r, 1.6) * vLight);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
  return new THREE.Points(geometry, material);
}
