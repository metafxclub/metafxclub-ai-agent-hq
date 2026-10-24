import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { CLUSTERS } from './data.js';
import { advanceMotion, starOrbit } from './motion.js';
import { createFlowStream } from './FlowStream.js';
import { createSentimentResources, createSentimentNode, getSentimentPhase, updateSentimentNode, setSentimentViewport, setSentimentData, disposeSentimentGraph } from './SentimentNode.js';
import { getSentiment, getCorrelations } from './market-data.js';
import { buildCorrelationNetwork, visibleCorrelationEdges, correlationEdgeAtVertex, correlationKey, CORRELATION_SEGMENTS, incidentCorrelationEdges, strongCorrelationEdges, correlationFlowProgress, correlationCurveControl, correlationCurvePoint, correlationOverviewStyle, correlationCounterpart, correlationLabelText, OVERVIEW_CORRELATION_THRESHOLD, correlationTone, correlationColor, NEUTRAL_CORRELATION_THRESHOLD, BRIGHT_YELLOW_CORRELATION_THRESHOLD, DEEP_CORRELATION_THRESHOLD } from './correlation-network.js';
import {assetUrl} from './asset-url.js';

// Galaxy positions are composition only; links require supplied market data.
const LAYOUT = {
  CHF: { center: [-9.6, 3.7, -.5], radius: 1.6, tilt: .95, turn: -.25 },
  EUR: { center: [.6, 1.1, .5], radius: 3.9, tilt: .92, turn: .18 },
  GBP: { center: [-7.5, -3.0, .4], radius: 2.9, tilt: .98, turn: .08 },
  USD: { center: [-1.1, 6.3, -.4], radius: 2.9, tilt: .96, turn: -.1 },
  AUD: { center: [11.5, 4.8, -.6], radius: 3.2, tilt: .93, turn: -.15 },
  CAD: { center: [14.3, -.2, .1], radius: 1.8, tilt: .94, turn: .2 },
  NZD: { center: [12.8, -5.2, .3], radius: 2.9, tilt: .95, turn: -.15 },
  METALS: { center: [5.2, -10.4, 1], radius: 2.7, tilt: .98, turn: -.1 },
  OIL: { center: [-1.9, -9.2, .2], radius: 2.2, tilt: .98, turn: .04 },
};
const REPRESENTATIVES = new Set(['CHFJPY','EURUSD','EURGBP','GBPUSD','USDJPY','USDCAD','AUDUSD','CADJPY','NZDUSD','XAUUSD','XAGUSD','WTI','BRENT']);
const PORTRAIT_CENTERS = { EUR:[-4.8,10.5,.5],GBP:[4.8,10.5,.4],USD:[-4.8,5.2,-.4],AUD:[4.8,5.2,-.6],METALS:[0,0,1],CHF:[-4.1,-4.8,-.5],CAD:[4.8,-5.4,.1],NZD:[-4.8,-10.7,.3],OIL:[4.8,-10.7,.2] };
const COMPACT_CENTERS = { CHF:[-6.2,1.0,-.5],EUR:[0,6.8,.5],USD:[7.4,6.8,-.4],GBP:[-9.5,-2.7,.4],METALS:[0,0,1],AUD:[7.4,.1,-.6],OIL:[-7.1,-6.8,.2],NZD:[0,-6.8,.3],CAD:[7.4,-6.8,.1] };
const TAU = Math.PI * 2;
function randomGenerator(seed) { return () => { seed=(seed*1664525+1013904223)>>>0; return seed/4294967296; }; }

function particles(positions, colors, sizes, opacity=1, maxSize=48, clock={value:0}, shear=0) {
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
  geometry.setAttribute('aSize',new THREE.Float32BufferAttribute(sizes,1));
  const material=new THREE.ShaderMaterial({
    transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,vertexColors:true,
    uniforms:{ opacity:{value:opacity},pixelScale:{value:1},maxSize:{value:maxSize},time:clock,shear:{value:shear} },
    vertexShader:`attribute float aSize; varying vec3 vColor; varying float vShimmer;
      uniform float pixelScale; uniform float maxSize; uniform float time; uniform float shear;
      void main(){ vColor=color;
      float a=sin(time*0.14)*shear*5.0/(0.8+length(position.xy)*0.55);
      vec3 warped=vec3(mat2(cos(a),sin(a),-sin(a),cos(a))*position.xy,position.z);
      warped.z+=sin(time*0.38+length(position.xy)*2.0)*abs(shear)*2.5;
      vShimmer=0.82+0.18*sin(time*0.9+position.x*4.0+position.y*7.0);
      vec4 p=modelViewMatrix*vec4(warped,1.0);
      gl_PointSize=clamp(aSize*pixelScale*420.0/max(2.0,-p.z),0.65,maxSize);
      gl_Position=projectionMatrix*p; }`,
    fragmentShader:`varying vec3 vColor; varying float vShimmer; uniform float opacity;
      void main(){ float r=length(gl_PointCoord-0.5)*2.0;
      if(r>1.0) discard; float glow=pow(1.0-r,2.4);
      gl_FragColor=vec4(vColor,glow*opacity*vShimmer);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
      }`,
  });
  return new THREE.Points(geometry,material);
}
function path(points,color,opacity=.2) {
  return new THREE.Line(new THREE.BufferGeometry().setFromPoints(points),new THREE.LineBasicMaterial({color,transparent:true,opacity,depthWrite:false}));
}
export function OrbitalScene({assetBase='/',pairs,selectedSymbol,axis='free',playing=true,reducedMotion=false,motionSpeed=1,motionClock,filter='all',correlationsVisible=true,selectedCorrelation=null,resetKey=0,focusKey=0,dataRevision=0,onSelect,onCorrelationSelect,onReady,onError}) {
  const host=useRef(null),engine=useRef(null),current=useRef(null);
  current.current={selectedSymbol,axis,playing,reducedMotion,motionSpeed,filter,correlationsVisible,selectedCorrelation,dataRevision,onSelect,onCorrelationSelect,onReady,onError};
  useEffect(()=>{
    const container=host.current; if(!container)return;
    let renderer;
    try { renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,powerPreference:'high-performance'}); }
    catch { current.current.onError?.('เบราว์เซอร์นี้เปิด WebGL ไม่สำเร็จ กรุณาลอง Chrome หรือ Edge');return; }
    renderer.setClearColor('#020810',1);renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,1.6));renderer.outputColorSpace=THREE.SRGBColorSpace;
    const canvas=renderer.domElement;canvas.className='orbital-webgl';canvas.tabIndex=0;
    canvas.setAttribute('aria-label','จักรวาล 32 สินทรัพย์ ลากซ้ายเพื่อหมุน ลากขวาเพื่อเลื่อนมุมมอง เลื่อนล้อเพื่อซูม');canvas.setAttribute('role','application');container.appendChild(canvas);
    const overlay=document.createElement('canvas');overlay.className='orbital-leaders';overlay.setAttribute('aria-hidden','true');container.appendChild(overlay);
    const context=overlay.getContext('2d');
    const labelLayer=document.createElement('div');labelLayer.className='orbital-label-layer';container.appendChild(labelLayer);
    const bindActivation=(button,activate)=>{
      // Orbiting labels can move between pointerdown and click. Capture intent
      // at pointerdown; keyboard/assistive activation still uses native click.
      button.addEventListener('pointerdown',event=>{
        if(event.button!==0)return;
        event.preventDefault();event.stopPropagation();button.focus({preventScroll:true});
        activate();
      });
      button.addEventListener('click',event=>{
        if(event.detail!==0)return;
        activate();
      });
    };
    const bindSelection=(button,getSymbol)=>bindActivation(button,()=>{const symbol=getSymbol();if(symbol)current.current.onSelect?.(symbol);});
    const scene=new THREE.Scene(),universe=new THREE.Group();scene.add(universe);
    const camera=new THREE.PerspectiveCamera(43,1,.1,220);camera.position.set(0,0,37);camera.lookAt(0,0,0);
    const materialsToScale=[],clusters=[],nodes=[],clock=motionClock?.current||{value:0};const rnd=randomGenerator(20261024);
    const addParticles=(group,p,c,s,opacity,maxSize,shear=0)=>{const cloud=particles(p,c,s,opacity,maxSize,clock,shear);group.add(cloud);materialsToScale.push(cloud.material);return cloud;};
    const addFlow=(group,curve,color,options)=>{const flow=createFlowStream(curve,color,clock,options);group.add(flow);materialsToScale.push(flow.material);return flow;};

    // Distant stars and wisps behind nine foreground galaxies.
    const bp=[],bc=[],bs=[];
    for(let i=0;i<16000;i++){
      bp.push((rnd()-.5)*75,(rnd()-.5)*42,-9-rnd()*25);const b=.1+Math.pow(rnd(),5)*.8;
      bc.push(.3*b,.58*b,b);bs.push(.065+Math.pow(rnd(),8)*1.08);
    }
    addParticles(scene,bp,bc,bs,.86);
    const np=[],nc=[],ns=[];
    for(let i=0;i<2800;i++){
      const t=rnd()*TAU,band=i%3;np.push(Math.sin(t)*(17+rnd()*2),Math.cos(t*1.4+band)*8+(rnd()-.5)*2,-8-rnd()*8);
      nc.push(.06,.13,.28);ns.push(.6+rnd()*2.8);
    }
    addParticles(scene,np,nc,ns,.15,100);
    // Real image texture on separated depth planes, below the live WebGL stars.
    let nebulaDisposed=false;
    const nebulaTexture=new THREE.TextureLoader().load(assetUrl(assetBase,'nebula-depth-v1.png'),()=>{
      if(nebulaDisposed)nebulaTexture.dispose();else container.dataset.nebula='ready';
    },undefined,()=>{container.dataset.nebula='unavailable';});
    nebulaTexture.colorSpace=THREE.SRGBColorSpace;
    const nebulaLayers=[{z:-20,w:84,h:48,x:-2,y:2,angle:-.12,opacity:1},{z:-12,w:66,h:40,x:7,y:-4,angle:.22,opacity:.56},{z:-6,w:42,h:26,x:-11,y:3,angle:-.48,opacity:.225}].map((spec,i)=>{
      const material=new THREE.ShaderMaterial({transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,
        uniforms:{map:{value:nebulaTexture},opacity:{value:spec.opacity}},
        vertexShader:`varying vec2 vUv; void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
        fragmentShader:`varying vec2 vUv; uniform sampler2D map; uniform float opacity;
          void main(){vec3 c=texture2D(map,vUv).rgb;float edge=smoothstep(0.0,.15,vUv.x)*smoothstep(0.0,.15,vUv.y)*(1.0-smoothstep(.85,1.0,vUv.x))*(1.0-smoothstep(.85,1.0,vUv.y));gl_FragColor=vec4(c,opacity*edge);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
          }`});
      const mesh=new THREE.Mesh(new THREE.PlaneGeometry(spec.w,spec.h),material);mesh.position.set(spec.x,spec.y,spec.z);mesh.rotation.z=spec.angle;scene.add(mesh);return{mesh,spec,index:i};
    });
    const hitGeometry=new THREE.SphereGeometry(.46,8,6),hitMaterial=new THREE.MeshBasicMaterial({visible:false});
    const sentimentResources=createSentimentResources();

    CLUSTERS.forEach((meta,clusterIndex)=>{
      const layout=LAYOUT[meta.id],members=pairs.filter(p=>p.clusterId===meta.id);
      const group=new THREE.Group();group.position.fromArray(layout.center);universe.add(group);
      const plane=new THREE.Group();plane.rotation.set(layout.tilt,0,layout.turn);group.add(plane);
      const spin=new THREE.Group();plane.add(spin);
      const eccentricity=.72+(clusterIndex%3)*.09,spinRate=(.036+clusterIndex%4*.009)*(clusterIndex%3===1?-1:1);
      const color=new THREE.Color(meta.color),silver=new THREE.Color('#d8e7ff'),oilBlue=new THREE.Color('#8bbaff');
      const p=[],c=[],s=[],fogP=[],fogC=[],fogS=[];
      // Fine spiral arms, diffuse dust and sparse bright knots.
      const count=Math.round(2700+layout.radius*1250);
      for(let i=0;i<count;i++){
        const r=Math.pow(rnd(),.68)*layout.radius,arm=i%3;
        const a=r/layout.radius*4.9+arm*TAU/3+(rnd()-.5)*(.3+r*.12);
        const skew=1+.13*Math.sin(a*2+clusterIndex),scatter=i%5===0?.7:.22;
        const x=Math.cos(a)*r*skew+(rnd()-.5)*scatter,y=Math.sin(a)*r*eccentricity+(rnd()-.5)*scatter,z=(rnd()-.5)*.22+Math.sin(a*2+r)*.12;
        p.push(x,y,z);const white=i%29===0,light=.24+rnd()*.67;
        const tint=meta.id==='METALS'&&x>.3?silver:meta.id==='OIL'&&x>.2?oilBlue:color;
        c.push((white?.85:tint.r)*light,(white?.94:tint.g)*light,(white?1:tint.b)*light);
        s.push(.045+Math.pow(rnd(),5)*.32+(i%181===0?.75:0));
        if(i%9===0){fogP.push(x,y,z-.1);fogC.push(tint.r,tint.g,tint.b);fogS.push(.7+rnd()*1.1);}
      }
      addParticles(spin,p,c,s,1.04,48,spinRate*.65);addParticles(spin,fogP,fogC,fogS,.07,85,spinRate*.65);
      // Open, uneven spiral filaments rather than concentric planetary orbits.
      for(let j=0;j<3;j++){
        const points=Array.from({length:100},(_,k)=>{const r=(.16+k/99*.84)*layout.radius,a=r/layout.radius*4.9+j*TAU/3;return new THREE.Vector3(Math.cos(a)*r*(1+.13*Math.sin(a*2+clusterIndex)),Math.sin(a)*r*eccentricity,Math.sin(a*2+r)*.12);});
        spin.add(path(points,meta.color,.16));
        addFlow(spin,new THREE.CatmullRomCurve3(points),meta.color,{rate:.11+j*.025,phase:j/3+clusterIndex*.07});
      }
      const caption=document.createElement('div');caption.className='galaxy-cluster-label';caption.style.setProperty('--cluster-color',meta.color);
      const title=document.createElement('strong');title.textContent=meta.label;const countLabel=document.createElement('span');countLabel.textContent=` · ${members.length}`;
      caption.append(title,countLabel);labelLayer.appendChild(caption);
      const labelPoint=new THREE.Vector3(layout.radius*-.15,meta.id==='METALS'?1:layout.radius*.62+.35,.1);
      const cluster={meta,layout,group,layoutTarget:group.position.clone(),plane,spin,spinRate,phase:clusterIndex*.8,caption,labelPoint,members,visible:true};clusters.push(cluster);
      members.forEach((pair,index)=>{
        const node=new THREE.Group();
        const angle=index/Math.max(1,members.length)*TAU+.38+clusterIndex*.3;
        const radius=layout.radius*(members.length===1?.3:members.length===2?.65:.62+(index%2)*.23);
        const phase=index*1.7+clusterIndex,rate=(.019+(index%3)*.009)*(spinRate<0?-1:1);
        node.position.fromArray(starOrbit(radius,angle,eccentricity,phase,0,rate));spin.add(node);
        const hit=new THREE.Mesh(hitGeometry,hitMaterial);hit.userData.symbol=pair.symbol;node.add(hit);
        const sentiment=getSentiment(pair.symbol);
        const nucleus=createSentimentNode(sentiment,sentimentResources,getSentimentPhase(pair.symbol)),rings=nucleus.group;node.add(rings);
        const label=document.createElement('button');label.className='orbital-node-label';label.textContent=pair.symbol;
        label.setAttribute('aria-label',`เลือกสินทรัพย์ ${pair.symbol} ${sentiment.available?`Short ${sentiment.short}% Long ${sentiment.long}%`:'ไม่มีข้อมูล Sentiment'}`);label.dataset.symbol=pair.symbol;
        label.title=sentiment.available?`${pair.symbol} · Short ${sentiment.short}% / Long ${sentiment.long}% · Myfxbook`:`${pair.symbol} · ยังไม่มีข้อมูล Myfxbook`;
        bindSelection(label,()=>pair.symbol);labelLayer.appendChild(label);
        nodes.push({pair,cluster,group:node,rings,nucleus,sentiment,hit,label,radius,angle,eccentricity,phase,rate,depthOffset:Math.sin(index*2.4)*.4,point:new THREE.Vector3()});
      });
    });
    // Reserve the complete network so an initially empty live feed can populate
    // later without rebuilding the scene or discarding the user's camera.
    let correlationEdges=buildCorrelationNetwork(pairs,getCorrelations);
    const maxCorrelationEdges=pairs.length*(pairs.length-1)/2,nodeBySymbol=new Map(nodes.map(node=>[node.pair.symbol,node]));
    const verticesPerEdge=CORRELATION_SEGMENTS*2;
    const correlationGeometry=new THREE.BufferGeometry();
    const correlationPositions=new THREE.BufferAttribute(new Float32Array(maxCorrelationEdges*verticesPerEdge*3),3).setUsage(THREE.DynamicDrawUsage);
    const correlationValues=new THREE.BufferAttribute(new Float32Array(maxCorrelationEdges*verticesPerEdge),1);
    const correlationIds=new THREE.BufferAttribute(new Float32Array(maxCorrelationEdges*verticesPerEdge),1);
    const correlationIncident=new THREE.BufferAttribute(new Float32Array(maxCorrelationEdges*verticesPerEdge),1);
    const correlationOpacity=new THREE.BufferAttribute(new Float32Array(maxCorrelationEdges*verticesPerEdge),1);
    const correlationColors=new THREE.BufferAttribute(new Float32Array(maxCorrelationEdges*verticesPerEdge*3),3);
    correlationGeometry.setAttribute('position',correlationPositions);correlationGeometry.setAttribute('aValue',correlationValues);correlationGeometry.setAttribute('aEdge',correlationIds);correlationGeometry.setAttribute('aIncident',correlationIncident);correlationGeometry.setAttribute('aOverviewOpacity',correlationOpacity);
    correlationGeometry.setAttribute('aCorrelationColor',correlationColors);
    correlationGeometry.boundingSphere=new THREE.Sphere(new THREE.Vector3(),180);
    // Alpha blending preserves gold/green/red hues where many curves cross;
    // additive blending accumulated into pale, nearly white knots.
    const correlationMaterial=new THREE.ShaderMaterial({transparent:true,depthWrite:false,blending:THREE.NormalBlending,
      uniforms:{selectedEdge:{value:-1},hasSelection:{value:0}},
      vertexShader:`attribute float aValue;attribute float aEdge;attribute float aIncident;attribute float aOverviewOpacity;attribute vec3 aCorrelationColor;uniform float selectedEdge;varying float vValue;varying float vSelected;varying float vIncident;varying float vOverviewOpacity;varying vec3 vCorrelationColor;
        void main(){vValue=aValue;vIncident=aIncident;vOverviewOpacity=aOverviewOpacity;vCorrelationColor=aCorrelationColor;vSelected=1.-step(.5,abs(aEdge-selectedEdge));gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
      fragmentShader:`varying float vValue;varying float vSelected;varying float vIncident;varying float vOverviewOpacity;varying vec3 vCorrelationColor;uniform float hasSelection;
        void main(){float strength=abs(vValue);vec3 tint=vCorrelationColor;
          float alpha=vOverviewOpacity*mix(1.,.13,hasSelection);
          alpha=mix(alpha,.24+pow(strength,1.4)*.52,vIncident);
          gl_FragColor=vec4(tint,mix(alpha,.94,vSelected));
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`});
    const correlationNetwork=new THREE.LineSegments(correlationGeometry,correlationMaterial);correlationNetwork.frustumCulled=false;scene.add(correlationNetwork);
    let visibleEdges=[],incidentEdges=[],flowEdges=[],correlationStats={neutral:0,positive:0,negative:0,minOpacity:0,maxOpacity:0};
    const edgeControls=new Map(),connectionStrength=new Map();
    const correlationLabels=Array.from({length:Math.max(0,pairs.length-1)},()=>{
      const label=document.createElement('button');label.className='orbital-correlation-label';label.hidden=true;labelLayer.appendChild(label);
      label.type='button';
      return {label,edge:null,progress:null,offset:null,width:104};
    });
    // These labels are reassigned when the selected star/filter changes. Resolve
    // the visible edge at event time, rather than retaining a record in 31 handlers.
    let pointerActivatedLabel=null,correlationActivationCount=0;
    const correlationButton=event=>{
      const button=event.target.closest?.('.orbital-correlation-label');
      return button&&labelLayer.contains(button)&&!button.hidden?button:null;
    };
    const activateCorrelationLabel=(button,event)=>{
      const key=correlationKey(button.dataset.source,button.dataset.target);
      const edge=visibleEdges.find(candidate=>candidate.key===key);
      container.dataset.correlationLabelEvent=event.type;
      container.dataset.correlationLabelCallback=String(typeof current.current.onCorrelationSelect==='function');
      if(!edge)return;
      container.dataset.lastPickedCorrelation=edge.key;
      container.dataset.correlationActivationCount=String(++correlationActivationCount);
      current.current.onCorrelationSelect?.({source:edge.source,target:edge.target,value:edge.value});
    };
    const onCorrelationPointerDown=event=>{
      const button=correlationButton(event);if(!button||event.button!==0)return;
      event.preventDefault();event.stopPropagation();button.focus({preventScroll:true});
      pointerActivatedLabel=button;activateCorrelationLabel(button,event);
    };
    const onCorrelationClick=event=>{
      const button=correlationButton(event);if(!button)return;
      event.preventDefault();event.stopPropagation();
      const alreadyActivated=event.detail>0&&pointerActivatedLabel===button;
      pointerActivatedLabel=null;if(!alreadyActivated)activateCorrelationLabel(button,event);
    };
    const onCorrelationKeyDown=event=>{
      const button=correlationButton(event);if(!button||!['Enter',' '].includes(event.key)||event.repeat)return;
      event.preventDefault();event.stopPropagation();pointerActivatedLabel=null;activateCorrelationLabel(button,event);
    };
    labelLayer.addEventListener('pointerdown',onCorrelationPointerDown,true);
    labelLayer.addEventListener('click',onCorrelationClick,true);
    labelLayer.addEventListener('keydown',onCorrelationKeyDown,true);
    const packetGeometry=new THREE.BufferGeometry(),packetPositions=new THREE.BufferAttribute(new Float32Array(maxCorrelationEdges*3),3).setUsage(THREE.DynamicDrawUsage);
    const packetValues=new THREE.BufferAttribute(new Float32Array(maxCorrelationEdges),1),packetEmphasis=new THREE.BufferAttribute(new Float32Array(maxCorrelationEdges),1);
    const packetColors=new THREE.BufferAttribute(new Float32Array(maxCorrelationEdges*3),3);
    packetGeometry.setAttribute('position',packetPositions);packetGeometry.setAttribute('aValue',packetValues);packetGeometry.setAttribute('aEmphasis',packetEmphasis);
    packetGeometry.setAttribute('aCorrelationColor',packetColors);
    const packetMaterial=new THREE.ShaderMaterial({transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,
      uniforms:{pixelScale:{value:1}},
      vertexShader:`attribute float aEmphasis;attribute vec3 aCorrelationColor;uniform float pixelScale;varying float vEmphasis;varying vec3 vCorrelationColor;
        void main(){vCorrelationColor=aCorrelationColor;vEmphasis=aEmphasis;vec4 p=modelViewMatrix*vec4(position,1.);gl_Position=projectionMatrix*p;gl_PointSize=clamp((4.+aEmphasis*4.)*pixelScale,3.,18.);}`,
      fragmentShader:`varying vec3 vCorrelationColor;varying float vEmphasis;void main(){float r=length(gl_PointCoord-.5)*2.;if(r>1.)discard;
        vec3 tint=vCorrelationColor;float core=pow(1.-r,2.);
        gl_FragColor=vec4(mix(tint,vec3(1.,.97,.8),pow(1.-r,5.)*.25),core*vEmphasis);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`});
    const packets=new THREE.Points(packetGeometry,packetMaterial);packets.frustumCulled=false;scene.add(packets);materialsToScale.push(packetMaterial);
    const haloGeometry=new THREE.BufferGeometry(),haloPositions=new THREE.BufferAttribute(new Float32Array(nodes.length*3),3).setUsage(THREE.DynamicDrawUsage),haloStrength=new THREE.BufferAttribute(new Float32Array(nodes.length),1);
    haloGeometry.setAttribute('position',haloPositions);haloGeometry.setAttribute('aStrength',haloStrength);
    const haloMaterial=new THREE.ShaderMaterial({transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,
      uniforms:{pixelScale:{value:1}},
      vertexShader:`attribute float aStrength;uniform float pixelScale;varying float vStrength;void main(){vStrength=aStrength;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);gl_PointSize=(7.+aStrength*4.)*pixelScale;}`,
      fragmentShader:`varying float vStrength;void main(){float r=length(gl_PointCoord-.5)*2.;if(r>1.||vStrength<.01)discard;gl_FragColor=vec4(1.,.75,.27,pow(1.-r,2.7)*vStrength*.7);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`});
    const connectionHalos=new THREE.Points(haloGeometry,haloMaterial);connectionHalos.frustumCulled=false;scene.add(connectionHalos);materialsToScale.push(haloMaterial);
    // Sparse comets sweep the gaps; not status indicators or live transactions.
    const meteors=new THREE.Group();universe.add(meteors);
    const meteorStreams=Array.from({length:5},(_,i)=>{
      const curve=new THREE.QuadraticBezierCurve3(new THREE.Vector3(-19+i*1.8,7-i*3,-4-i),new THREE.Vector3(-2+i*2,5-i*2,-2-i),new THREE.Vector3(18-i,3-i*2,-4-i));
      return addFlow(meteors,curve,i%2?'#8facf9':'#62c9f2',{rate:.06+i*.008,phase:.07+i*.19,meteor:true});
    });
    const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
    const worldAxes={x:new THREE.Vector3(1,0,0),y:new THREE.Vector3(0,1,0),z:new THREE.Vector3(0,0,1)};
    const q=new THREE.Quaternion(),parentQ=new THREE.Quaternion(),pickProjected=new THREE.Vector3();
    let width=1,height=1,frame=0,disposed=false,dragging=null,hover=null,layoutInitialized=false;
    const meteorTargetScale=new THREE.Vector3(1,1,1);
    let lastTime=performance.now(),lastDom=0,zoom=1,lastFilter=null,focusCluster=null,pendingFocus=false,lastCorrelationKey='',lastDataRevision=null;
    const viewCenter=new THREE.Vector3(),targetCenter=new THREE.Vector3(),panOffset=new THREE.Vector3();let desiredDistance=37,initialView=true;
    const rotate=(dx,dy)=>{
      const mode=current.current.axis;
      if(mode==='free'){universe.quaternion.premultiply(q.setFromAxisAngle(worldAxes.y,dx*.004));universe.quaternion.premultiply(q.setFromAxisAngle(worldAxes.x,dy*.004));}
      else universe.quaternion.premultiply(q.setFromAxisAngle(worldAxes[mode]||worldAxes.z,(dx+dy*.65)*.005));
      universe.quaternion.normalize();
    };
    const pan=(dx,dy)=>{
      const worldPerPixel=2*Math.tan(THREE.MathUtils.degToRad(camera.fov*.5))*camera.position.distanceTo(viewCenter)/height;
      panOffset.x-=dx*worldPerPixel;panOffset.y+=dy*worldPerPixel;
    };
    const setPointerRay=event=>{
      const rect=canvas.getBoundingClientRect();pointer.set(((event.clientX-rect.left)/rect.width)*2-1,-((event.clientY-rect.top)/rect.height)*2+1);raycaster.setFromCamera(pointer,camera);
    };
    const pick=event=>{
      setPointerRay(event);
      return raycaster.intersectObjects(nodes.filter(n=>n.cluster.visible).map(n=>n.hit),false)[0]?.object.userData.symbol||null;
    };
    const pickCorrelation=event=>{
      if(!correlationNetwork.visible||!visibleEdges.length)return null;
      setPointerRay(event);
      const worldPerPixel=2*Math.tan(THREE.MathUtils.degToRad(camera.fov*.5))*camera.position.distanceTo(viewCenter)/height;
      raycaster.params.Line.threshold=worldPerPixel*4;
      const intersections=raycaster.intersectObject(correlationNetwork,false);
      let closest=null,closestPixels=5;
      for(const hit of intersections){
        pickProjected.copy(hit.point).project(camera);
        const pixels=Math.hypot((pickProjected.x-pointer.x)*width*.5,(pickProjected.y-pointer.y)*height*.5);
        if(pixels<closestPixels){closestPixels=pixels;closest=correlationEdgeAtVertex(visibleEdges,hit.index);}
      }
      return closest;
    };
    const onDown=event=>{
      if(event.button!==0&&event.button!==2&&event.pointerType!=='touch')return;
      if(event.button===0&&event.target.closest?.('button'))return;
      event.preventDefault();canvas.focus({preventScroll:true});
      const symbol=event.button===0?pick(event):null;
      dragging={id:event.pointerId,x:event.clientX,y:event.clientY,button:event.button,travel:0,symbol,correlation:event.button===0&&!symbol?pickCorrelation(event):null};
      canvas.setPointerCapture(event.pointerId);canvas.classList.add('is-dragging');
    };
    const onMove=event=>{
      if(dragging&&event.pointerId===dragging.id){const dx=event.clientX-dragging.x,dy=event.clientY-dragging.y;dragging.travel+=Math.abs(dx)+Math.abs(dy);if(dragging.button===2)pan(dx,dy);else rotate(dx,dy);dragging.x=event.clientX;dragging.y=event.clientY;}
      else{hover=pick(event);canvas.style.cursor=hover?'pointer':current.current.correlationsVisible?'crosshair':'grab';}
    };
    const onUp=event=>{
      if(!dragging||event.pointerId!==dragging.id)return;
      if(dragging.button===0&&dragging.travel<6){
        if(dragging.symbol)current.current.onSelect?.(dragging.symbol);
        else if(dragging.correlation){const {source,target,value}=dragging.correlation;container.dataset.lastPickedCorrelation=correlationKey(source,target);current.current.onCorrelationSelect?.({source,target,value});}
      }
      if(canvas.hasPointerCapture(event.pointerId))canvas.releasePointerCapture(event.pointerId);dragging=null;canvas.classList.remove('is-dragging');
    };
    const onCancel=()=>{dragging=null;canvas.classList.remove('is-dragging');};
    const contextMenu=event=>event.preventDefault();
    const wheel=event=>{event.preventDefault();zoom=THREE.MathUtils.clamp(zoom*Math.exp(event.deltaY*.0007),.42,1.7);};
    const keyboard=event=>{
      const directions={ArrowLeft:[-14,0],ArrowRight:[14,0],ArrowUp:[0,-14],ArrowDown:[0,14]};
      if(directions[event.key]){event.preventDefault();if(event.shiftKey)pan(...directions[event.key]);else rotate(...directions[event.key]);}
      else if(['+','=','-'].includes(event.key)){event.preventDefault();zoom=THREE.MathUtils.clamp(zoom*(event.key==='-'?1.08:.92),.42,1.7);}
    };
    const onContextLost=event=>{event.preventDefault();current.current.onError?.('ฉากสามมิติหยุดชั่วคราว กรุณาโหลดหน้าใหม่เพื่อเชื่อมต่อกราฟิกอีกครั้ง');};
    container.addEventListener('pointerdown',onDown);container.addEventListener('pointermove',onMove);container.addEventListener('pointerup',onUp);container.addEventListener('pointercancel',onCancel);
    container.addEventListener('contextmenu',contextMenu);container.addEventListener('wheel',wheel,{passive:false});canvas.addEventListener('keydown',keyboard);canvas.addEventListener('webglcontextlost',onContextLost);
    const resize=()=>{
      const rect=container.getBoundingClientRect();width=Math.max(1,rect.width);height=Math.max(1,rect.height);
      const compact=width>=640&&width/height<1.24;
      container.dataset.framing=width<640?'portrait':compact?'compact':'wide';
      // A panel width transition can cross a framing breakpoint mid-animation.
      // Move toward the new composition instead of teleporting all nine groups.
      clusters.forEach(c=>{
        c.layoutTarget.fromArray(width<640?PORTRAIT_CENTERS[c.meta.id]:compact?COMPACT_CENTERS[c.meta.id]:c.layout.center);
        if(!layoutInitialized||current.current.reducedMotion)c.group.position.copy(c.layoutTarget);
      });
      meteorTargetScale.set(width<640?.5:1,width<640?1.7:1,1);
      if(!layoutInitialized||current.current.reducedMotion)meteors.scale.copy(meteorTargetScale);
      layoutInitialized=true;
      renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix();const pixelRatio=Math.min(window.devicePixelRatio||1,1.6);
      overlay.width=width*pixelRatio;overlay.height=height*pixelRatio;overlay.style.width=`${width}px`;overlay.style.height=`${height}px`;context?.setTransform(pixelRatio,0,0,pixelRatio,0,0);
      materialsToScale.forEach(m=>{m.uniforms.pixelScale.value=height/720*pixelRatio;});
      nodes.forEach(node=>setSentimentViewport(node.nucleus,height*pixelRatio));
    };
    const observer=new ResizeObserver(resize);observer.observe(container);resize();
    const fitCamera=()=>{
      const box=new THREE.Box3(),point=new THREE.Vector3();
      clusters.filter(c=>c.visible&&(!focusCluster||c.meta.id===focusCluster)).forEach(c=>{
        const r=c.layout.radius;
        for(const x of[-r*1.12,r*1.12])for(const y of[-r*.7,r*.74+.35])for(const z of[-r*.65,r*.65]){point.set(x,y,z);c.group.localToWorld(point);box.expandByPoint(point);}
      });
      if(box.isEmpty())return;
      const size=box.getSize(new THREE.Vector3());box.getCenter(targetCenter);if(width>=640&&current.current.filter==='all'&&!focusCluster)targetCenter.y+=1.05;targetCenter.add(panOffset);const halfFov=Math.tan(THREE.MathUtils.degToRad(camera.fov*.5));
      const verticalPadding=height/Math.max(240,height-160),horizontalPadding=width/Math.max(240,width-40);
      const fit=Math.max(size.y/(2*halfFov)*verticalPadding,size.x/(2*halfFov*camera.aspect)*horizontalPadding);desiredDistance=(fit*(width<640?1.08:1.025)+size.z*.5)*zoom;
      if(initialView){viewCenter.copy(targetCenter);camera.position.set(targetCenter.x,targetCenter.y,targetCenter.z+desiredDistance);initialView=false;}
    };
    const project=p=>({x:(p.x*.5+.5)*width,y:(-p.y*.5+.5)*height});
    function updateLabels(){
      context?.clearRect(0,0,width,height);const occupied=[],projected=new THREE.Vector3();
      const fits=(x,y,w,h)=>x>=8&&x+w<=width-8&&y>=65&&y+h<=height-124&&!occupied.some(box=>x<box.x+box.w+4&&x+w>box.x-4&&y<box.y+box.h+3&&y+h>box.y-3);
      const leader=(anchor,box,color)=>{
        if(!context)return;
        const endX=Math.max(box.x,Math.min(box.x+box.w,anchor.x)),endY=Math.max(box.y,Math.min(box.y+box.h,anchor.y));
        if(Math.hypot(endX-anchor.x,endY-anchor.y)<12)return;
        context.beginPath();context.strokeStyle=color;context.lineWidth=.7;context.moveTo(anchor.x,anchor.y);context.lineTo(endX,endY);context.stroke();
      };
      clusters.forEach(c=>{
        projected.copy(c.labelPoint);c.group.localToWorld(projected);projected.project(camera);const p=project(projected);
        const captionWidth=width<640?72:108;
        const visible=c.visible&&projected.z<1&&p.x>12&&p.x<width-12&&p.y>70&&p.y<height-120;c.caption.hidden=!visible;
        if(visible){const x=Math.min(p.x,width-captionWidth-8);c.caption.style.transform=`translate3d(${x.toFixed(1)}px,${(p.y-20).toFixed(1)}px,0)`;occupied.push({x,y:p.y-20,w:captionWidth,h:30});}
      });
      const selected=current.current.selectedSymbol;
      const ordered=[...nodes].sort((a,b)=>a.pair.symbol===selected?-1:b.pair.symbol===selected?1:0);
      ordered.forEach(n=>{
        n.group.getWorldPosition(n.point);projected.copy(n.point).project(camera);const p=project(projected),active=n.pair.symbol===selected;
        const selectedEdge=current.current.selectedCorrelation;
        const connected=connectionStrength.has(n.pair.symbol);
        const featured=active||connected||n.pair.symbol===hover||selectedEdge?.source===n.pair.symbol||selectedEdge?.target===n.pair.symbol||(width>=640&&REPRESENTATIVES.has(n.pair.symbol))||focusCluster||current.current.filter!=='all';
        const visible=n.cluster.visible&&featured&&projected.z<1&&p.x>6&&p.x<width-8&&p.y>65&&p.y<height-110;n.label.hidden=!visible;if(!visible)return;
        const lw=active?82:width<640?58:66,lh=active?27:24;
        const offsets=[...(n.labelOffset?[n.labelOffset]:[]),{x:17,y:-29},{x:-lw-17,y:-29},{x:17,y:13},{x:-lw-17,y:13}];
        for(const radius of[36,58,84,112,144])for(let turn=0;turn<8;turn++){
          const angle=turn*TAU/8;offsets.push({x:Math.cos(angle)*radius-lw*.5,y:Math.sin(angle)*radius-lh*.5});
        }
        const offset=offsets.find(candidate=>fits(p.x+candidate.x,p.y+candidate.y,lw,lh));
        n.label.hidden=!offset;if(!offset)return;
        n.labelOffset=offset;const box={x:p.x+offset.x,y:p.y+offset.y,w:lw,h:lh};occupied.push(box);
        leader(p,box,connected?'#d7b77366':'#93b3c74d');
        n.label.style.transform=`translate3d(${box.x.toFixed(1)}px,${box.y.toFixed(1)}px,0)`;n.label.classList.toggle('is-selected',active);n.label.classList.toggle('is-connected',connected&&!active);n.label.setAttribute('aria-pressed',String(active));
      });
      correlationLabels.forEach((record,index)=>{
        const {label,edge}=record;if(!edge){label.hidden=true;return;}
        const start=nodeBySymbol.get(edge.source).point,end=nodeBySymbol.get(edge.target).point,control=edgeControls.get(edge.key);
        if(!control){label.hidden=true;return;}
        const direction=edge.source===selected?1:-1;
        const base=.5+direction*(.08+(index%5)*.055);
        const lw=record.width,lh=22;
        const offsets=[...(record.offset?[record.offset]:[]),{x:0,y:0},{x:0,y:-24},{x:0,y:24},{x:-lw*.45,y:-24},{x:lw*.45,y:24},{x:-lw*.45,y:24},{x:lw*.45,y:-24}];
        let placement=null;
        for(let attempt=0;attempt<16;attempt++){
          const candidate=attempt-1;
          const progress=attempt===0&&record.progress!==null?record.progress:THREE.MathUtils.clamp(base+(candidate%2?1:-1)*Math.ceil(Math.max(0,candidate)/2)*.045,.14,.86);
          correlationCurvePoint(start,end,control,progress,projected);projected.project(camera);const p=project(projected);
          if(projected.z>=1)continue;
          const offset=offsets.find(candidate=>fits(p.x-lw*.5+candidate.x,p.y-lh*.5+candidate.y,lw,lh));
          if(offset){placement={x:p.x-lw*.5+offset.x,y:p.y-lh*.5+offset.y,progress,offset,anchor:p};break;}
        }
        label.hidden=!placement;
        if(placement){
          record.progress=placement.progress;record.offset=placement.offset;
          label.style.transform=`translate3d(${placement.x.toFixed(1)}px,${placement.y.toFixed(1)}px,0)`;
          const box={x:placement.x,y:placement.y,w:lw,h:lh};occupied.push(box);leader(placement.anchor,box,`${correlationColor(edge.value)}66`);
        }
        label.classList.toggle('is-selected',current.current.selectedCorrelation&&edge.key===correlationKey(current.current.selectedCorrelation.source,current.current.selectedCorrelation.target));
      });
    }
    function configureCorrelations(){
      visibleEdges=current.current.correlationsVisible?visibleCorrelationEdges(correlationEdges,current.current.filter):[];
      incidentEdges=incidentCorrelationEdges(visibleEdges,current.current.selectedSymbol);
      const incidentKeys=new Set(incidentEdges.map(edge=>edge.key));
      flowEdges=strongCorrelationEdges(visibleEdges);
      correlationMaterial.uniforms.hasSelection.value=incidentEdges.length?1:0;
      connectionStrength.clear();
      incidentEdges.forEach(edge=>connectionStrength.set(edge.source===current.current.selectedSymbol?edge.target:edge.source,Math.abs(edge.value)));
      correlationNetwork.visible=visibleEdges.length>0;
      correlationGeometry.setDrawRange(0,visibleEdges.length*verticesPerEdge);
      correlationStats={neutral:0,positive:0,negative:0,minOpacity:visibleEdges.length?Infinity:0,maxOpacity:0};
      visibleEdges.forEach((edge,index)=>{
        const start=index*verticesPerEdge;
        const style=correlationOverviewStyle(edge.value),color=new THREE.Color(correlationColor(edge.value));
        correlationStats[correlationTone(edge.value)]++;
        correlationStats.minOpacity=Math.min(correlationStats.minOpacity,style.opacity);correlationStats.maxOpacity=Math.max(correlationStats.maxOpacity,style.opacity);
        correlationValues.array.fill(edge.value,start,start+verticesPerEdge);
        correlationIds.array.fill(edge.index,start,start+verticesPerEdge);
        correlationIncident.array.fill(incidentKeys.has(edge.key)?1:0,start,start+verticesPerEdge);
        correlationOpacity.array.fill(style.opacity,start,start+verticesPerEdge);
        for(let vertex=start;vertex<start+verticesPerEdge;vertex++)correlationColors.setXYZ(vertex,color.r,color.g,color.b);
      });
      correlationValues.needsUpdate=true;correlationIds.needsUpdate=true;correlationIncident.needsUpdate=true;correlationOpacity.needsUpdate=true;correlationColors.needsUpdate=true;
      correlationLabels.forEach((record,index)=>{
        const edge=incidentEdges[index];if(record.edge?.key!==edge?.key){record.progress=null;record.offset=null;}record.edge=edge||null;record.label.hidden=!edge;
        if(!edge)return;
        record.label.textContent=correlationLabelText(edge,current.current.selectedSymbol);
        if(context)context.font='600 12px Rajdhani, sans-serif';
        record.width=Math.max(94,Math.ceil(context?.measureText(record.label.textContent).width||record.label.textContent.length*6.2)+14);
        record.label.style.setProperty('--correlation-color',correlationColor(edge.value));record.label.dataset.tone=correlationTone(edge.value);
        record.label.title=`${edge.source} ↔ ${edge.target} · ${Math.round(edge.value*100)}% · คำนวณจากราคาปิด MT5`;
        record.label.setAttribute('aria-label',record.label.title);record.label.dataset.source=edge.source;record.label.dataset.target=edge.target;record.label.dataset.correlation=String(edge.value);record.label.dataset.counterpart=correlationCounterpart(edge,current.current.selectedSymbol);
      });
      packets.visible=flowEdges.length>0;packetGeometry.setDrawRange(0,flowEdges.length);
      flowEdges.forEach((edge,index)=>{const color=new THREE.Color(correlationColor(edge.value));packetColors.setXYZ(index,color.r,color.g,color.b);packetValues.setX(index,edge.value);packetEmphasis.setX(index,incidentEdges.length?(incidentKeys.has(edge.key)?1:.14):.75);});
      packetValues.needsUpdate=true;packetEmphasis.needsUpdate=true;packetColors.needsUpdate=true;
      nodes.forEach((node,index)=>{
        const strength=connectionStrength.get(node.pair.symbol),active=node.pair.symbol===current.current.selectedSymbol&&incidentEdges.length>0;
        haloStrength.setX(index,node.cluster.visible?(active?.95:strength===undefined?0:.45+strength*.5):0);
      });
      haloStrength.needsUpdate=true;connectionHalos.visible=incidentEdges.length>0;
    }
    function updateCorrelationGeometry(time){
      if(!visibleEdges.length)return;
      nodes.forEach(node=>node.group.getWorldPosition(node.point));
      const positions=correlationPositions.array;
      visibleEdges.forEach((edge,index)=>{
        const start=nodeBySymbol.get(edge.source).point,end=nodeBySymbol.get(edge.target).point;
        const control=correlationCurveControl(start,end,edge.index);edgeControls.set(edge.key,control);
        let offset=index*verticesPerEdge*3;
        for(let segment=0;segment<CORRELATION_SEGMENTS;segment++){
          for(let endpoint=0;endpoint<2;endpoint++){
            const t=(segment+endpoint)/CORRELATION_SEGMENTS,u=1-t,a=u*u,b=2*u*t,c=t*t;
            positions[offset++]=a*start.x+b*control.x+c*end.x;
            positions[offset++]=a*start.y+b*control.y+c*end.y;
            positions[offset++]=a*start.z+b*control.z+c*end.z;
          }
        }
      });
      correlationPositions.needsUpdate=true;
      const packetPoint=new THREE.Vector3();
      flowEdges.forEach((edge,index)=>{
        correlationCurvePoint(nodeBySymbol.get(edge.source).point,nodeBySymbol.get(edge.target).point,edgeControls.get(edge.key),correlationFlowProgress(time,edge.index),packetPoint);
        packetPositions.setXYZ(index,packetPoint.x,packetPoint.y,packetPoint.z);
      });
      packetPositions.needsUpdate=true;
      const markerOffset=new THREE.Vector3(.40,.32,.04).applyQuaternion(camera.quaternion);
      nodes.forEach((node,index)=>haloPositions.setXYZ(index,node.point.x+markerOffset.x,node.point.y+markerOffset.y,node.point.z+markerOffset.z));haloPositions.needsUpdate=true;
    }
    function refreshData(){
      nodes.forEach(node=>{
        const sentiment=getSentiment(node.pair.symbol);node.sentiment=sentiment;setSentimentData(node.nucleus,sentiment);
        node.label.setAttribute('aria-label',`เลือกสินทรัพย์ ${node.pair.symbol} ${sentiment.available?`Short ${sentiment.short}% Long ${sentiment.long}%`:'ยังไม่มีข้อมูล Myfxbook'}`);
        node.label.title=sentiment.available?`${node.pair.symbol} · Short ${sentiment.short}% / Long ${sentiment.long}% · Myfxbook${sentiment.asOf?` · รับข้อมูล ${sentiment.asOf}`:''}`:`${node.pair.symbol} · ยังไม่มีข้อมูล Myfxbook`;
        node.label.dataset.sentimentAvailable=String(sentiment.available);node.label.dataset.sentimentColor=node.nucleus.appearance.color;
      });
      correlationEdges=buildCorrelationNetwork(pairs,getCorrelations);edgeControls.clear();
      // Never retain a mouse-down edge value across a new market snapshot.
      if(dragging?.correlation)dragging.correlation=correlationEdges.find(edge=>edge.key===dragging.correlation.key)||null;
      configureCorrelations();lastCorrelationKey='';lastDataRevision=current.current.dataRevision;
      container.dataset.dataRevision=String(lastDataRevision);
    }
    const reset=()=>{universe.quaternion.identity();panOffset.set(0,0,0);focusCluster=null;pendingFocus=false;zoom=1;};
    // Apply after a simultaneous category change, so cross-category search keeps its focus.
    const focus=()=>{pendingFocus=true;};
    engine.current={reset,focus,refreshData};const visibility=()=>{lastTime=performance.now();};document.addEventListener('visibilitychange',visibility);
    function animate(now){
      if(disposed)return;frame=requestAnimationFrame(animate);const dt=Math.max(0,Math.min(.05,(now-lastTime)/1000));lastTime=now;if(document.hidden||width<2||height<2)return;
      if(lastFilter!==current.current.filter){
        lastFilter=current.current.filter;focusCluster=null;zoom=1;
        clusters.forEach(c=>{c.visible=lastFilter==='all'||c.meta.assetClass===lastFilter;c.group.visible=c.visible;});
        meteors.visible=lastFilter==='all';
      }
      if(lastDataRevision!==current.current.dataRevision)refreshData();
      const networkKey=`${current.current.filter}:${current.current.correlationsVisible}:${current.current.selectedSymbol}`;
      if(networkKey!==lastCorrelationKey){configureCorrelations();lastCorrelationKey=networkKey;}
      const selectedEdge=current.current.selectedCorrelation;
      correlationMaterial.uniforms.selectedEdge.value=selectedEdge?correlationEdges.find(edge=>edge.key===correlationKey(selectedEdge.source,selectedEdge.target))?.index??-1:-1;
      if(pendingFocus){focusCluster=nodes.find(n=>n.pair.symbol===current.current.selectedSymbol)?.pair.clusterId||null;zoom=1;pendingFocus=false;}
      if(!current.current.selectedSymbol)focusCluster=null;
      clock.value=advanceMotion(clock.value,dt,{playing:current.current.playing&&!current.current.reducedMotion,dragging:Boolean(dragging),speed:current.current.motionSpeed});
      const time=clock.value;
      // Layout motion follows UI time, so opening a panel still eases while the
      // market choreography is paused. Reduced motion snaps both layout/camera.
      const layoutEase=current.current.reducedMotion?1:1-Math.exp(-dt*9);
      meteors.scale.lerp(meteorTargetScale,layoutEase);
      nebulaLayers.forEach(({mesh,spec,index})=>{
        mesh.position.x=spec.x+Math.sin(time*.018+index)*1.2+universe.quaternion.y*(index+1)*1.3;
        mesh.position.y=spec.y+Math.sin(time*.012+index)*.65-universe.quaternion.x*(index+1)*.9;
        mesh.rotation.z=spec.angle+Math.sin(time*.009+index)*.025;
      });
      clusters.forEach(c=>{
        c.group.position.lerp(c.layoutTarget,layoutEase);
        if(c.group.position.distanceToSquared(c.layoutTarget)<.000001)c.group.position.copy(c.layoutTarget);
        c.spin.rotation.z=time*c.spinRate;
        c.plane.rotation.x=c.layout.tilt+Math.sin(time*.17+c.phase)*.055;
        c.plane.rotation.z=c.layout.turn+Math.sin(time*.12+c.phase)*.035;
      });
      nodes.forEach(n=>{n.group.position.fromArray(starOrbit(n.radius,n.angle,n.eccentricity,n.phase,time,n.rate));n.group.position.z+=n.depthOffset;});
      universe.updateMatrixWorld(true);fitCamera();const ease=current.current.reducedMotion?1:1-Math.exp(-dt*6);viewCenter.lerp(targetCenter,ease);
      camera.position.x+=(viewCenter.x-camera.position.x)*ease;camera.position.y+=(viewCenter.y-camera.position.y)*ease;camera.position.z+=(viewCenter.z+desiredDistance-camera.position.z)*ease;
      camera.lookAt(viewCenter);camera.updateMatrixWorld();
      nodes.forEach(n=>{
        const active=n.pair.symbol===current.current.selectedSymbol,featured=REPRESENTATIVES.has(n.pair.symbol);
        n.rings.scale.setScalar(active?1.22:featured?1.08:.92);
        n.hit.scale.setScalar(active?1.2:1);
        n.group.getWorldQuaternion(parentQ);n.rings.quaternion.copy(parentQ.invert()).multiply(camera.quaternion);
        updateSentimentNode(n.nucleus,time);
      });
      scene.updateMatrixWorld(true);updateCorrelationGeometry(time);
      renderer.render(scene,camera);updateLabels();
      if(now-lastDom>160){
        const connectedNames=new Set(nodes.filter(node=>!node.label.hidden&&connectionStrength.has(node.pair.symbol)).map(node=>node.pair.symbol));
        correlationLabels.filter(record=>!record.label.hidden).forEach(record=>connectedNames.add(record.label.dataset.counterpart));
        Object.assign(container.dataset,{
        rotation:universe.quaternion.toArray().map(v=>v.toFixed(5)).join(','),orbit:clusters[1].spin.rotation.z.toFixed(6),motionTime:time.toFixed(6),motionSpeed:String(current.current.motionSpeed),distance:camera.position.z.toFixed(3),selected:current.current.selectedSymbol||'',selectionMode:current.current.selectedSymbol?'selected':'overview',
        axis:current.current.axis,playing:String(current.current.playing),visibleCount:String(nodes.filter(n=>n.cluster.visible).length),clusterCount:String(clusters.filter(c=>c.visible).length),focus:focusCluster||'overview',
        reducedMotion:String(current.current.reducedMotion),layoutMoving:String(clusters.some(c=>c.group.position.distanceToSquared(c.layoutTarget)>.000001)),layoutDistance:clusters.reduce((sum,c)=>sum+c.group.position.distanceTo(c.layoutTarget),0).toFixed(4),chfCenter:clusters.find(c=>c.meta.id==='CHF').group.position.toArray().map(value=>value.toFixed(4)).join(','),
        connectionCount:String(visibleEdges.length),correlationCount:String(visibleEdges.length),correlationTotal:String(correlationEdges.length),correlationDrawCalls:String(correlationNetwork.visible?1:0),selectedCorrelation:selectedEdge?correlationKey(selectedEdge.source,selectedEdge.target):'',cometCount:String(meteors.visible?meteorStreams.length:0),starPosition:nodes[0].group.position.toArray().map(v=>v.toFixed(5)).join(','),
        selectedEdgeCount:String(incidentEdges.length),correlationLabelCount:String(correlationLabels.filter(record=>!record.label.hidden).length),correlationLabelTotal:String(incidentEdges.length),highlightedEndpointCount:String(connectionStrength.size),flowCount:String(flowEdges.length),selectedFlowCount:String(strongCorrelationEdges(incidentEdges).length),flowProgress:flowEdges.length?correlationFlowProgress(time,flowEdges[0].index).toFixed(6):'',flowDrawCalls:String(packets.visible?1:0),pan:panOffset.toArray().map(value=>value.toFixed(4)).join(','),panX:panOffset.x.toFixed(4),panY:panOffset.y.toFixed(4),cameraControls:'left-rotate,right-pan',
        overviewThreshold:String(OVERVIEW_CORRELATION_THRESHOLD),overviewStrongCount:String(visibleEdges.filter(edge=>correlationOverviewStyle(edge.value).emphasized).length),visibleNameCount:String(nodes.filter(node=>!node.label.hidden).length),connectedNameCount:String(connectedNames.size),
        neutralThreshold:String(NEUTRAL_CORRELATION_THRESHOLD),correlationNeutralCount:String(correlationStats.neutral),correlationPositiveCount:String(correlationStats.positive),correlationNegativeCount:String(correlationStats.negative),correlationOpacityMin:correlationStats.minOpacity.toFixed(4),correlationOpacityMax:correlationStats.maxOpacity.toFixed(4),correlationBrightYellowCount:String(visibleEdges.filter(edge=>Math.abs(edge.value)<=BRIGHT_YELLOW_CORRELATION_THRESHOLD).length),correlationDeepCount:String(visibleEdges.filter(edge=>Math.abs(edge.value)>=DEEP_CORRELATION_THRESHOLD).length),correlationBlending:'normal',
        nucleusOrbits:String(nodes[0]?.nucleus.ringCount??0),sentimentRings:String(nodes[0]?.nucleus.ringCount??0),selectedLong:String(getSentiment(current.current.selectedSymbol).long??''),selectedShort:String(getSentiment(current.current.selectedSymbol).short??''),beadPosition:nodes.find(n=>n.pair.symbol===current.current.selectedSymbol)?.nucleus.bead.position.toArray().map(v=>v.toFixed(5)).join(',')||'',nebulaLayers:String(nebulaLayers.length),
      });lastDom=now;}
    }
    frame=requestAnimationFrame(animate);container.dataset.ready='true';container.dataset.nodeCount=String(nodes.length);current.current.onReady?.();
    return()=>{
      disposed=true;cancelAnimationFrame(frame);observer.disconnect();document.removeEventListener('visibilitychange',visibility);
      container.removeEventListener('pointerdown',onDown);container.removeEventListener('pointermove',onMove);container.removeEventListener('pointerup',onUp);container.removeEventListener('pointercancel',onCancel);
      container.removeEventListener('wheel',wheel);container.removeEventListener('contextmenu',contextMenu);canvas.removeEventListener('keydown',keyboard);canvas.removeEventListener('webglcontextlost',onContextLost);
      labelLayer.removeEventListener('pointerdown',onCorrelationPointerDown,true);labelLayer.removeEventListener('click',onCorrelationClick,true);labelLayer.removeEventListener('keydown',onCorrelationKeyDown,true);
      nebulaDisposed=true;nebulaTexture.dispose();disposeSentimentGraph(scene,sentimentResources);renderer.dispose();renderer.forceContextLoss();canvas.remove();overlay.remove();labelLayer.remove();engine.current=null;delete container.dataset.ready;
    };
  },[pairs]);
  useEffect(()=>{if(resetKey)engine.current?.reset();},[resetKey]);useEffect(()=>{if(focusKey)engine.current?.focus();},[focusKey]);
  return <div ref={host} className="orbital-canvas-wrap" data-testid="orbital-scene" />;
}
export default OrbitalScene;
