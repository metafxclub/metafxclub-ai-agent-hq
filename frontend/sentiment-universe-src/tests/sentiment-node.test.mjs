import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {createSentimentNode,createSentimentResources,updateSentimentNode,getSentimentPhase,getSentimentColor,setSentimentViewport,setSentimentData,disposeSentimentGraph,SENTIMENT_RADIUS} from '../src/SentimentNode.js';
import {getSentiment} from '../src/sentiment-data.js';
test('stellar plasma has a 3D core and depth-distributed corona without a torus or pie outline',()=>{
 const resources=createSentimentResources(),node=createSentimentNode(getSentiment('EURUSD'),resources);assert.equal(node.ringCount,0);assert.equal(node.core.geometry.type,'SphereGeometry');assert.deepEqual(node.composition,{long:68,short:32});
 let hasTorus=false;node.group.traverse(object=>{if(object.geometry?.type==='TorusGeometry')hasTorus=true;});assert.equal(hasTorus,false);
 const positions=node.particles.geometry.attributes.position;assert.ok(Array.from(positions.array).every(Number.isFinite));const depths=Array.from({length:positions.count},(_,index)=>positions.getZ(index));assert.ok(Math.max(...depths)>.2&&Math.min(...depths)<-.2);for(let i=0;i<positions.count;i++)assert.ok(Math.hypot(positions.getX(i),positions.getY(i),positions.getZ(i))<=SENTIMENT_RADIUS);disposeSentimentGraph(node.group,resources);
});
test('unknown composition stays explicit and never generates an invented split',()=>{
 for(const input of[getSentiment('WTI'),null,{available:true,long:45,short:45},{available:true,long:-1,short:101},{available:true,long:100.005,short:0},{available:true,long:0,short:100.005},{available:true,long:400,short:0}]){const resources=createSentimentResources(),node=createSentimentNode(input,resources);assert.equal(node.available,false);assert.equal(node.composition,null);assert.equal(node.bead.visible,false);assert.equal(node.core.material.uniforms.muted.value,1);disposeSentimentGraph(node.group,resources);}
});
test('shared-clock pause freezes all transforms, filaments, and shader time',()=>{
 const resources=createSentimentResources(),node=createSentimentNode(getSentiment('EURUSD'),resources,.4),initial=node.bead.position.toArray();updateSentimentNode(node,5);assert.notDeepEqual(node.bead.position.toArray(),initial);
 const snapshot=()=>({position:node.bead.position.toArray(),plane:node.plane.rotation.toArray(),core:node.core.rotation.toArray(),particles:node.particles.rotation.toArray(),flow:node.flow.rotation.toArray(),filaments:node.filaments.map(item=>Array.from(item.mesh.geometry.attributes.position.array)),shaderTimes:[node.core,node.glow,node.particles,node.flow].map(item=>item.material.uniforms.time.value)});
 const paused=snapshot();updateSentimentNode(node,5);assert.deepEqual(snapshot(),paused);updateSentimentNode(node,6);assert.notDeepEqual(snapshot(),paused);assert.deepEqual(node.composition,{long:68,short:32});disposeSentimentGraph(node.group,resources);
});
test('all generated geometry stays finite through long running and invalid clock input',()=>{
 const resources=createSentimentResources(),node=createSentimentNode(getSentiment('EURUSD'),resources,getSentimentPhase('EURUSD'));
 for(const time of[0,60,86400,NaN,Infinity]){updateSentimentNode(node,time);node.group.traverse(object=>{if(object.geometry?.attributes.position)assert.ok(Array.from(object.geometry.attributes.position.array).every(Number.isFinite));assert.ok(object.position.toArray().every(Number.isFinite));assert.ok(object.rotation.toArray().slice(0,3).every(Number.isFinite));});}
 setSentimentViewport(node,420);assert.equal(node.particles.material.uniforms.viewportHeight.value,420);assert.equal(getSentimentPhase(' eurusd '),getSentimentPhase('EURUSD'));disposeSentimentGraph(node.group,resources);
});
test('cleanup disposes shared geometry exactly once and every node material',()=>{
 const resources=createSentimentResources(),root=new THREE.Group();root.add(createSentimentNode(getSentiment('EURUSD'),resources).group);root.add(createSentimentNode(getSentiment('USDJPY'),resources).group);const tracked=new Map();root.traverse(object=>{for(const resource of[object.geometry,object.material].filter(Boolean)){if(!tracked.has(resource)){tracked.set(resource,0);resource.addEventListener('dispose',()=>tracked.set(resource,tracked.get(resource)+1));}}});disposeSentimentGraph(root,resources);assert.ok(tracked.size>20);for(const count of tracked.values())assert.equal(count,1);
});

const rgb = hex => [1, 3, 5].map(index => Number.parseInt(hex.slice(index, index + 2), 16));
const colorAt = long => getSentimentColor({ available: true, long, short: 100 - long });

test('increasing majority produces ordered green/red dominance and deeper 90-percent colors', () => {
  for (const [values, component, bias] of [[[60, 70, 80, 90, 100], 1, 'long'], [[40, 30, 20, 10, 0], 0, 'short']]) {
    let previousShare = 0, previousStrength = 0;
    for (const value of values) {
      const appearance = colorAt(value), channels = rgb(appearance.color);
      const dominantShare = channels[component] / channels.reduce((sum, channel) => sum + channel, 0);
      assert.equal(appearance.bias, bias);
      assert.ok(dominantShare > previousShare);
      assert.ok(appearance.strength > previousStrength);
      previousShare = dominantShare; previousStrength = appearance.strength;
    }
  }
  const green80 = rgb(colorAt(80).color), red80 = rgb(colorAt(20).color);
  assert.ok(green80[1] > green80[0] * 6);
  assert.ok(red80[0] > red80[1] * 5);
  assert.ok(rgb(colorAt(90).color)[1] < green80[1]);
  assert.ok(rgb(colorAt(10).color)[0] < red80[0]);
  // Adjacent percentages interpolate instead of jumping to a binary status.
  const near = [79.9, 80, 80.1].map(value => rgb(colorAt(value).color));
  assert.ok(near.every(channels => channels.every((channel, index) => Math.abs(channel - green80[index]) < 3)));
});

test('balanced positioning is subdued but remains visibly distinct from unavailable gray', () => {
  const neutral = colorAt(50), missing = getSentimentColor(getSentiment('WTI'));
  assert.equal(neutral.bias, 'neutral'); assert.equal(neutral.dominance, 50);
  assert.equal(neutral.strength, 0); assert.equal(neutral.available, true);
  assert.ok(neutral.brightness < colorAt(80).brightness);
  assert.equal(missing.bias, 'unavailable'); assert.equal(missing.available, false); assert.equal(missing.dominance, null);
  assert.notEqual(neutral.color, missing.color);
  const gray = rgb(missing.color); assert.ok(Math.max(...gray) - Math.min(...gray) <= 10);
  for (const invalid of [null, { available: true, long: NaN, short: 50 }, { available: true, long: 100.005, short: 0 }, { available: true, long: 0, short: 100.005 }, { available: true, long: 400, short: 0 }]) assert.equal(getSentimentColor(invalid).available, false);
  assert.equal(colorAt(0).available, true);
  assert.equal(colorAt(100).available, true);
});

test('scene and preview factory colors agree on every plasma layer without cross-selection tint leaks', () => {
  const resources = createSentimentResources(), root = new THREE.Group();
  for (const symbol of ['GBPUSD', 'USDJPY', 'EURCHF', 'WTI']) {
    const expected = getSentimentColor(getSentiment(symbol));
    const sceneNode = createSentimentNode(getSentiment(symbol), resources, getSentimentPhase(symbol));
    const previewNode = createSentimentNode(getSentiment(symbol), resources, getSentimentPhase(symbol));
    root.add(sceneNode.group, previewNode.group);
    for (const node of [sceneNode, previewNode]) {
      assert.deepEqual(node.appearance, expected);
      for (const part of [node.core, node.glow, node.particles, node.flow]) {
        assert.equal(`#${part.material.uniforms.coronaTint.value.getHexString()}`, expected.corona);
        assert.equal(`#${part.material.uniforms.coreTint.value.getHexString()}`, expected.core);
      }
      assert.equal(`#${node.bead.material.color.getHexString()}`, expected.highlight);
    }
  }
  const colorsBefore = root.children.map(group => group.children[0].children[1].material.uniforms.coreTint.value.getHexString());
  assert.notEqual(colorsBefore[0], colorsBefore[2]);
  const tracked = new Map();
  root.traverse(object => {
    for (const resource of [object.geometry, object.material].filter(Boolean)) {
      if (tracked.has(resource)) continue;
      tracked.set(resource, 0); resource.addEventListener('dispose', () => tracked.set(resource, tracked.get(resource) + 1));
    }
  });
  disposeSentimentGraph(root, resources);
  for (const count of tracked.values()) assert.equal(count, 1);
});

test('provider rounding normalizes only visual share and preserves supplied percentages', () => {
  for (const [long, short] of [[44,55],[51,50],[49,49],[51,51]]) {
    const resources=createSentimentResources(),raw={available:true,long,short};
    const node=createSentimentNode(raw,resources);
    assert.equal(node.available,true);assert.deepEqual(node.composition,{long,short});
    const expected=colorAt(long/(long+short)*100);
    assert.equal(node.appearance.bias,expected.bias);assert.equal(node.appearance.color,expected.color);
    assert.equal(node.particles.material.uniforms.longFraction.value,long/(long+short));
    disposeSentimentGraph(node.group,resources);
  }
  for(const raw of[{available:true,long:44,short:53},{available:true,long:55,short:48},{available:true,long:0,short:0}])assert.equal(getSentimentColor(raw).available,false);
});

test('live refresh keeps node geometry, motion phase and shared neighbors intact', () => {
  const resources=createSentimentResources(),initial={available:true,long:70,short:30};
  const left=createSentimentNode(initial,resources,.7),right=createSentimentNode(initial,resources,.9);
  const root=new THREE.Group();root.add(left.group,right.group);
  updateSentimentNode(left,32);updateSentimentNode(right,32);
  const identity={group:left.group,coreGeometry:left.core.geometry,particles:left.particles.geometry};
  const motion={bead:left.bead.position.toArray(),core:left.core.rotation.toArray(),plane:left.plane.rotation.toArray(),time:left.core.material.uniforms.time.value,phase:left.phase};
  const neighborMaterial=right.filaments[0].mesh.material,neighborTint=neighborMaterial.color.getHexString();
  assert.equal(left.filaments[0].mesh.material,neighborMaterial);
  setSentimentData(left,{available:true,long:20,short:80});
  assert.equal(left.appearance.bias,'short');assert.equal(right.appearance.bias,'long');
  assert.equal(right.filaments[0].mesh.material,neighborMaterial);assert.equal(neighborMaterial.color.getHexString(),neighborTint);
  assert.notEqual(left.filaments[0].mesh.material,neighborMaterial);
  assert.equal(left.group,identity.group);assert.equal(left.core.geometry,identity.coreGeometry);assert.equal(left.particles.geometry,identity.particles);
  assert.deepEqual({bead:left.bead.position.toArray(),core:left.core.rotation.toArray(),plane:left.plane.rotation.toArray(),time:left.core.material.uniforms.time.value,phase:left.phase},motion);
  for(const part of[left.core,left.glow,left.particles,left.flow])assert.equal(`#${part.material.uniforms.coronaTint.value.getHexString()}`,left.appearance.corona);
  const detached=left.filaments.map(({mesh})=>mesh.material);
  setSentimentData(left,{available:false,long:null,short:null});
  assert.equal(left.available,false);assert.equal(left.bead.visible,false);assert.equal(left.composition,null);assert.equal(left.core.material.uniforms.muted.value,1);
  assert.deepEqual(left.filaments.map(({mesh})=>mesh.material),detached);
  setSentimentData(left,{available:true,long:55,short:44});
  assert.equal(left.available,true);assert.equal(left.bead.visible,true);assert.equal(left.core.material.uniforms.muted.value,0);
  assert.deepEqual(left.composition,{long:55,short:44});assert.equal(right.appearance.bias,'long');
  disposeSentimentGraph(root,resources);
});

test('cleanup includes detached shared filament materials exactly once after live updates',()=>{
  const resources=createSentimentResources(),root=new THREE.Group();
  const node=createSentimentNode({available:true,long:50,short:50},resources);root.add(node.group);
  const originals=[...resources.filamentMaterials.values()];setSentimentData(node,{available:true,long:75,short:25});
  const tracked=new Map();
  const track=resource=>{if(!tracked.has(resource)){tracked.set(resource,0);resource.addEventListener('dispose',()=>tracked.set(resource,tracked.get(resource)+1));}};
  originals.forEach(track);root.traverse(object=>[object.geometry,object.material].filter(Boolean).forEach(track));
  disposeSentimentGraph(root,resources);for(const count of tracked.values())assert.equal(count,1);
});
