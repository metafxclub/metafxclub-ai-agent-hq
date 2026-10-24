import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { HORIZONS, STATE_META } from './data.js';
import { createNucleusResources, createNucleus, getNucleusPhase, createGlow, updateNucleus, disposeNucleusGraph } from './NucleusNode.js';
import './nucleus-preview.css';

export function NucleusPreview({ pair, clockRef, labeled = false, className = '' }) {
  const host = useRef(null);
  useEffect(() => {
    const container = host.current;
    if (!container) return;
    let renderer;
    try { renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' }); }
    catch { container.dataset.ready = 'false'; return; }
    const pixelRatio = Math.min(window.devicePixelRatio || 1, 1.6);
    renderer.setPixelRatio(pixelRatio); renderer.setClearColor(0x000000, 0); renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.domElement.setAttribute('aria-hidden', 'true'); container.prepend(renderer.domElement);
    const scene = new THREE.Scene(), camera = new THREE.OrthographicCamera(-.78, .78, .9, -.9, .1, 15);
    camera.position.set(0, 0, 4); camera.lookAt(0, 0, 0);
    const resources = createNucleusResources(), nucleus = createNucleus(pair.states, resources, getNucleusPhase(pair.symbol));
    scene.add(nucleus.group);
    const core = new THREE.Mesh(new THREE.SphereGeometry(.045, 24, 16), new THREE.MeshBasicMaterial({ color: pair.symbol === 'XAUUSD' ? '#fff9e2' : '#f0fcff' }));
    scene.add(core);
    const coreGlow = new THREE.Points(resources.glow, createGlow(pair.symbol === 'XAUUSD' ? '#ffd57d' : '#67d1f2', (labeled ? 180 : 40) * pixelRatio)); scene.add(coreGlow);
    // Stable seed, rendered geometry: a compact particle corona, never market data.
    let seed = 2317; const random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
    const points = [];
    for (let i = 0; i < (labeled ? 1200 : 120); i++) {
      const r = .045 + Math.pow(random(), 2) * .37, theta = random() * Math.PI * 2, z = (random() - .5) * .23;
      points.push(Math.cos(theta) * r, Math.sin(theta) * r, z);
    }
    const corona = new THREE.Points(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(points, 3)), new THREE.PointsMaterial({ color: pair.symbol === 'XAUUSD' ? '#ffe1a0' : '#8edfff', size: .006, transparent: true, opacity: .65, depthWrite: false, blending: THREE.AdditiveBlending })); scene.add(corona);
    const mist = new THREE.Points(corona.geometry, createGlow(pair.symbol === 'XAUUSD' ? '#eab56b' : '#65c6e3', (labeled ? 20 : 6) * pixelRatio));
    mist.material.uniforms.strength.value = .025; scene.add(mist);
    const leaders = labeled ? document.createElement('canvas') : null;
    const context = leaders?.getContext('2d');
    if (leaders) { leaders.className = 'nucleus-leaders'; leaders.setAttribute('aria-hidden', 'true'); container.appendChild(leaders); }
    const beadPoint = new THREE.Vector3();
    let frame = 0, lastTime = -1, lastWidth = 0, lastHeight = 0;
    const resize = () => {
      const { width, height } = container.getBoundingClientRect();
      if (width < 1 || height < 1) return;
      lastWidth = width; lastHeight = height;
      renderer.setSize(width, height, false);
      if (leaders) { leaders.width = Math.round(width * pixelRatio); leaders.height = Math.round(height * pixelRatio); context?.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0); }
      const halfWidth = labeled ? .67 : .68, halfHeight = halfWidth * height / width;
      camera.left = -halfWidth; camera.right = halfWidth; camera.top = halfHeight; camera.bottom = -halfHeight; camera.updateProjectionMatrix(); lastTime = -1;
    };
    const observer = new ResizeObserver(resize); observer.observe(container); resize();
    function draw() {
      frame = requestAnimationFrame(draw);
      if (document.hidden || lastWidth < 1 || lastHeight < 1) return;
      const time = clockRef?.current?.value || 0;
      if (time === lastTime) return;
      lastTime = time; updateNucleus(nucleus, time, labeled ? pixelRatio * 1.6 : pixelRatio * .55);
      corona.rotation.z = mist.rotation.z = time * .05; coreGlow.material.uniforms.strength.value = 1.65 + Math.sin(time * .9) * .12;
      renderer.render(scene, camera);
      if (context) {
        context.clearRect(0, 0, lastWidth, lastHeight);
        const bounds = container.getBoundingClientRect();
        nucleus.orbits.forEach((orbit, i) => {
          const label = container.querySelector(`.nucleus-callout-${i}`)?.getBoundingClientRect(); if (!label) return;
          if (orbit.state === 'unknown') { beadPoint.set(orbit.profile.radius, 0, 0); orbit.plane.localToWorld(beadPoint); }
          else orbit.bead.getWorldPosition(beadPoint);
          beadPoint.project(camera);
          const x = (beadPoint.x * .5 + .5) * lastWidth, y = (-beadPoint.y * .5 + .5) * lastHeight;
          const left = label.left - bounds.left, right = label.right - bounds.left, bottom = label.bottom - bounds.top;
          const anchor = i === 1 ? left : right;
          context.strokeStyle = `${STATE_META[orbit.state].color}88`; context.lineWidth = .8;
          context.beginPath(); context.moveTo(i === 1 ? right : left, bottom); context.lineTo(anchor, bottom); context.lineTo((anchor + x) * .5, bottom); context.lineTo(x, y); context.stroke();
        });
      }
      container.dataset.motionTime = time.toFixed(6);
      container.dataset.beadPosition = nucleus.orbits[0].bead.position.toArray().map(v => v.toFixed(5)).join(',');
    }
    frame = requestAnimationFrame(draw); container.dataset.ready = 'true'; container.dataset.orbits = '3';
    return () => { cancelAnimationFrame(frame); observer.disconnect(); disposeNucleusGraph(scene); renderer.dispose(); renderer.forceContextLoss(); renderer.domElement.remove(); leaders?.remove(); delete container.dataset.ready; };
  }, [pair, clockRef, labeled]);
  const description = pair.states.map((state, i) => `${HORIZONS[i].timeframe} ${STATE_META[state]?.labelThai || 'ไม่มีข้อมูล'}`).join(', ');
  return <div className={`nucleus-preview ${labeled ? 'nucleus-preview-large' : 'nucleus-preview-small'} ${className}`} ref={host} role="img" aria-label={`นิวเคลียส ${pair.symbol}: ${description}`} data-symbol={pair.symbol}>
    {labeled && <div className="nucleus-callouts" aria-hidden="true">{[2, 1, 0].map(i => <span key={i} className={`nucleus-callout nucleus-callout-${i}`} style={{ color: STATE_META[pair.states[i]]?.color || STATE_META.unknown.color }}>{HORIZONS[i].timeframe}</span>)}</div>}
  </div>;
}
