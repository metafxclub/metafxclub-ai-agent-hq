import * as THREE from 'three';

// Stellar motion is an illustration, never order flow or a forecast.
export const SENTIMENT_COLORS = { long: '#13d976', short: '#cf1732', neutral: '#8c9bb5', unavailable: '#65656b' };
export const SENTIMENT_RADIUS = .58;
const TAU = Math.PI * 2;

function mixHex(from, to, amount) {
  const t = Math.max(0, Math.min(1, amount));
  const components = [1, 3, 5].map(index => {
    const first = Number.parseInt(from.slice(index, index + 2), 16);
    const second = Number.parseInt(to.slice(index, index + 2), 16);
    return Math.round(first + (second - first) * t).toString(16).padStart(2, '0');
  });
  return `#${components.join('')}`;
}

const LONG_COLORS = ['#8c9bb5', '#7fbaa4', '#3fc991', '#13d976', '#05b85c', '#009e4c'];
const SHORT_COLORS = ['#8c9bb5', '#ba8e99', '#db6678', '#cf1732', '#ad1028', '#940b20'];

// A deterministic, continuous visual scale for community positioning. It does
// not label the price trend: e.g. 80% short means red, not a sell recommendation.
export function getSentimentColor(sentiment) {
  const total = sentiment?.long + sentiment?.short;
  const available = sentiment?.available === true && Number.isFinite(sentiment.long) && Number.isFinite(sentiment.short)
    && sentiment.long >= 0 && sentiment.long <= 100 && sentiment.short >= 0 && sentiment.short <= 100
    && total > 0 && Math.abs(total - 100) <= 2;
  if (!available) {
    return { available: false, bias: 'unavailable', strength: 0, dominance: null, color: SENTIMENT_COLORS.unavailable,
      core: '#74747a', corona: '#65656b', particles: '#77777e', highlight: '#98989f', brightness: .4 };
  }
  // Published percentages may sum to 99/101 after provider rounding. Normalize
  // only the visual share; keep the original figures in node.composition/UI.
  const visualLong = sentiment.long / total * 100;
  const bias = sentiment.long === sentiment.short ? 'neutral' : sentiment.long > sentiment.short ? 'long' : 'short';
  const strength = Math.abs(visualLong - 50) / 50;
  const position = Math.min(5, strength * 5), index = Math.min(4, Math.floor(position));
  const palette = bias === 'short' ? SHORT_COLORS : LONG_COLORS;
  const color = mixHex(palette[index], palette[index + 1], position - index);
  return { available: true, bias, strength, dominance: Math.max(visualLong, 100 - visualLong), color,
    core: mixHex(color, '#ffffff', .09), corona: color, particles: color,
    highlight: mixHex(color, '#ffffff', .25), brightness: .62 + strength * .38 };
}

function colorUniforms(appearance) {
  return { coreTint: { value: new THREE.Color(appearance.core) }, coronaTint: { value: new THREE.Color(appearance.corona) },
    particleTint: { value: new THREE.Color(appearance.particles) }, highlightTint: { value: new THREE.Color(appearance.highlight) },
    brightness: { value: appearance.brightness } };
}
export function getSentimentPhase(symbol = '') {
  let hash = 2166136261;
  for (const character of String(symbol).trim().toUpperCase()) hash = Math.imul(hash ^ character.charCodeAt(0), 16777619);
  return (hash >>> 0) / 4294967296 * TAU;
}
function randomGenerator(seed) {
  let value = seed >>> 0;
  return () => { value = (Math.imul(value, 1664525) + 1013904223) >>> 0; return value / 4294967296; };
}
function particleGeometry(count, flow = false) {
  const random = randomGenerator(flow ? 76183 : 42851), positions = [], sizes = [], seeds = [];
  for (let index = 0; index < count; index++) {
    const angle = random() * TAU;
    if (flow) {
      const radius = .22 + random() * .27;
      positions.push(Math.cos(angle) * radius, Math.sin(angle) * radius * .56, (random() - .5) * .09 + Math.sin(angle * 3) * .045);
    } else {
      const radius = .135 + Math.pow(random(), 2.1) * .42;
      const vertical = random() * 2 - 1, radial = Math.sqrt(1 - vertical * vertical);
      positions.push(Math.cos(angle) * radial * radius, Math.sin(angle) * radial * radius, vertical * radius);
    }
    sizes.push((flow ? .005 : .007) + random() * (flow ? .011 : .021)); seeds.push(random());
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('aSize', new THREE.Float32BufferAttribute(sizes, 1));
  geometry.setAttribute('aSeed', new THREE.Float32BufferAttribute(seeds, 1));
  geometry.computeBoundingSphere(); return geometry;
}
export function createSentimentResources() {
  return {
    core: new THREE.SphereGeometry(.148, 28, 20), bead: new THREE.SphereGeometry(.012, 8, 6),
    particles: particleGeometry(480), flow: particleGeometry(130, true), filamentMaterials: new Map(),
    glow: new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0], 3)),
  };
}
function plasmaMaterial(appearance) {
  return new THREE.ShaderMaterial({
    uniforms: { time: { value: 0 }, phase: { value: 0 }, muted: { value: appearance.available ? 0 : 1 }, ...colorUniforms(appearance) },
    vertexShader: `uniform float time; uniform float phase; varying vec3 surface; varying vec3 viewNormal; varying vec3 viewPosition;
      void main(){surface=position;
        float wave=sin(position.x*42.0+time*.8+phase)*sin(position.y*38.0-time*.61)*sin(position.z*45.0+time*.43);
        vec3 p=position+normal*(wave*.006); vec4 mv=modelViewMatrix*vec4(p,1.0);
        viewNormal=normalize(normalMatrix*normal);viewPosition=-mv.xyz;gl_Position=projectionMatrix*mv;}`,
    fragmentShader: `uniform float time;uniform float phase;uniform float muted;uniform float brightness;uniform vec3 coreTint;uniform vec3 coronaTint;uniform vec3 highlightTint;varying vec3 surface;varying vec3 viewNormal;varying vec3 viewPosition;
      void main(){float facing=max(0.0,dot(normalize(viewNormal),normalize(viewPosition)));
        float cells=sin(surface.x*68.0+sin(surface.z*41.0+time*.6))*sin(surface.y*59.0-time*.7+phase);
        float veins=pow(1.0-abs(sin(surface.x*31.0+surface.y*36.0+sin(surface.z*53.0+time*.3))),8.0);
        vec3 tint=mix(coronaTint*.55,coreTint,pow(facing,.8));
        tint=mix(tint,highlightTint,clamp(cells*.10+veins*.22+.08,0.0,.4));
        tint*=.65+brightness*.35;gl_FragColor=vec4(tint,1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
}
function dustMaterial(appearance, longFraction, opacity) {
  return new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: {time:{value:0},phase:{value:0},viewportHeight:{value:900},alpha:{value:opacity},available:{value:appearance.available?1:0},longFraction:{value:longFraction},...colorUniforms(appearance)},
    vertexShader: `attribute float aSize;attribute float aSeed;uniform float time;uniform float phase;uniform float viewportHeight;varying float seed;varying float radius;
      void main(){seed=aSeed;radius=length(position);vec3 p=position*(1.0+sin(time*.46+aSeed*15.0+phase)*.045);
        p+=vec3(sin(time*.16+aSeed*22.0),cos(time*.19+aSeed*17.0),sin(time*.13+aSeed*31.0))*.009;
        vec4 mv=modelViewMatrix*vec4(p,1.0);float divisor=projectionMatrix[2][3]<-.5?max(.1,-mv.z):1.0;
        gl_PointSize=clamp(aSize*viewportHeight*projectionMatrix[1][1]/divisor,1.0,26.0);gl_Position=projectionMatrix*mv;}`,
    fragmentShader: `uniform float time;uniform float alpha;uniform float brightness;uniform vec3 particleTint;uniform vec3 highlightTint;varying float seed;varying float radius;
      void main(){float r=length(gl_PointCoord-.5)*2.0;if(r>1.0)discard;
        vec3 stellar=mix(highlightTint,particleTint,smoothstep(.13,.32,radius));
        float envelope=pow(1.0-r,2.0)*(0.66+.34*sin(seed*31.0+time*.7));gl_FragColor=vec4(stellar,envelope*alpha*(.55+brightness*.45));
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
}
function glowMaterial(appearance) {
  return new THREE.ShaderMaterial({
    transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,
    uniforms:{viewportHeight:{value:900},time:{value:0},available:{value:appearance.available?1:0},...colorUniforms(appearance)},
    vertexShader:`uniform float viewportHeight;void main(){vec4 mv=modelViewMatrix*vec4(position,1.0);float divisor=projectionMatrix[2][3]<-.5?max(.1,-mv.z):1.0;gl_PointSize=1.26*viewportHeight*projectionMatrix[1][1]/divisor;gl_Position=projectionMatrix*mv;}`,
    fragmentShader:`uniform float time;uniform float brightness;uniform vec3 coronaTint;uniform vec3 coreTint;void main(){vec2 p=(gl_PointCoord-.5)*2.0;float r=length(p);if(r>1.0)discard;
      float angle=atan(p.y,p.x);float wisps=1.0+sin(angle*5.0+time*.12)*.12+sin(angle*9.0-time*.09)*.06;
      float haze=exp(-r*r*12.0)*pow(1.0-r,1.3)*wisps;vec3 color=mix(coronaTint,coreTint,exp(-r*r*36.0));
      gl_FragColor=vec4(color,haze*(.30+brightness*.24));
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`,
  });
}
function createFilament(index, appearance, resources) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(49 * 3), 3));
  const tint=index%3?appearance.corona:appearance.highlight;
  const key=`${tint}:${index%2}`;
  if(!resources.filamentMaterials.has(key))resources.filamentMaterials.set(key,new THREE.LineBasicMaterial({color:tint,transparent:true,opacity:(index%2?.12:.2)*appearance.brightness,depthWrite:false,blending:THREE.AdditiveBlending}));
  const material=resources.filamentMaterials.get(key);
  const mesh = new THREE.Line(geometry, material);mesh.rotation.set(index*.93,index*.71,index*1.13);return {mesh,index};
}
export function createSentimentNode(sentiment, resources, phase = 0) {
  const group=new THREE.Group(),plane=new THREE.Group();group.add(plane);
  const appearance=getSentimentColor(sentiment),valid=appearance.available;
  const longFraction=valid?sentiment.long/(sentiment.long+sentiment.short):.5;
  const core=new THREE.Mesh(resources.core,plasmaMaterial(appearance)),glow=new THREE.Points(resources.glow,glowMaterial(appearance));
  const particles=new THREE.Points(resources.particles,dustMaterial(appearance,longFraction,.72)),flow=new THREE.Points(resources.flow,dustMaterial(appearance,longFraction,.3));flow.rotation.x=.65;
  const filaments=Array.from({length:6},(_,index)=>createFilament(index,appearance,resources));
  const bead=new THREE.Mesh(resources.bead,new THREE.MeshBasicMaterial({color:appearance.highlight,transparent:true,opacity:.65,depthWrite:false,blending:THREE.AdditiveBlending}));bead.visible=valid;
  plane.add(glow,core,particles,flow,...filaments.map(item=>item.mesh),bead);
  const node={group,plane,core,glow,particles,flow,filaments,bead,phase,appearance,available:valid,ringCount:0,segments:[],composition:valid?{long:sentiment.long,short:sentiment.short}:null};updateSentimentNode(node,0);return node;
}
// Refresh market data without changing geometry, transforms, clock or camera.
// Filament materials are shared by initial color; detach them once before tinting
// so updating one instrument cannot recolor another instrument's filaments.
export function setSentimentData(node, sentiment) {
  const appearance = getSentimentColor(sentiment), valid = appearance.available;
  if (!node.ownsFilamentMaterials) {
    node.filaments.forEach(({mesh}) => { mesh.material = mesh.material.clone(); });
    node.ownsFilamentMaterials = true;
  }
  node.appearance = appearance; node.available = valid;
  node.composition = valid ? {long:sentiment.long, short:sentiment.short} : null;
  const tints = {coreTint:appearance.core, coronaTint:appearance.corona, particleTint:appearance.particles, highlightTint:appearance.highlight};
  for (const part of [node.core, node.glow, node.particles, node.flow]) {
    const uniforms = part.material.uniforms;
    for (const [key, color] of Object.entries(tints)) if (uniforms[key]) uniforms[key].value.set(color);
    if (uniforms.brightness) uniforms.brightness.value = appearance.brightness;
    if (uniforms.available) uniforms.available.value = valid ? 1 : 0;
    if (uniforms.muted) uniforms.muted.value = valid ? 0 : 1;
    if (uniforms.longFraction) uniforms.longFraction.value = valid ? sentiment.long / (sentiment.long + sentiment.short) : .5;
  }
  node.bead.visible = valid; node.bead.material.color.set(appearance.highlight);
  node.filaments.forEach(({mesh,index}) => {
    mesh.material.color.set(index % 3 ? appearance.corona : appearance.highlight);
    mesh.material.opacity = (index % 2 ? .12 : .2) * appearance.brightness;
  });
}
export function updateSentimentNode(node,time) {
  const safeTime=Number.isFinite(time)?time:0,phase=Number.isFinite(node.phase)?node.phase:0;
  node.plane.rotation.set(.16+Math.sin(safeTime*.09+phase)*.06,safeTime*.055+phase,-.16);
  node.core.rotation.set(safeTime*.047,safeTime*.09+phase,0);
  node.particles.rotation.set(safeTime*.035,safeTime*-.067,safeTime*.045);node.flow.rotation.z=safeTime*.13+phase;
  for(const object of [node.core,node.glow,node.particles,node.flow]){object.material.uniforms.time.value=safeTime;if(object.material.uniforms.phase)object.material.uniforms.phase.value=phase;}
  for(const{mesh,index}of node.filaments){const positions=mesh.geometry.attributes.position,lift=.12+index*.021;
    for(let point=0;point<positions.count;point++){const progress=point/(positions.count-1),angle=progress*Math.PI,envelope=Math.sin(angle),ripple=Math.sin(progress*17+safeTime*.21+phase+index)*.009*envelope;
      positions.setXYZ(point,Math.cos(angle)*(.085+index*.004),.09+envelope*lift+ripple,Math.sin(progress*8+index+safeTime*.13)*.025*envelope);}
    positions.needsUpdate=true;if(!mesh.geometry.boundingSphere)mesh.geometry.boundingSphere=new THREE.Sphere(new THREE.Vector3(),.4);
  }
  const angle=safeTime*.35+phase,radius=.21+Math.sin(safeTime*.17+phase)*.025;
  node.bead.position.set(Math.cos(angle)*radius,Math.sin(angle)*radius*.52,Math.sin(angle*1.7)*.06);
}
export function setSentimentViewport(node,height){const value=Number.isFinite(height)&&height>0?height:900;for(const object of[node.glow,node.particles,node.flow])object.material.uniforms.viewportHeight.value=value;}
export function disposeSentimentGraph(root,resources){
  const geometries=new Set(),materials=new Set();root.traverse(object=>{if(object.geometry)geometries.add(object.geometry);if(object.material)(Array.isArray(object.material)?object.material:[object.material]).forEach(material=>materials.add(material));});
  if(resources){Object.values(resources).forEach(value=>{if(value?.isBufferGeometry)geometries.add(value);});resources.filamentMaterials?.forEach(material=>materials.add(material));}geometries.forEach(geometry=>geometry.dispose());materials.forEach(material=>material.dispose());
}
