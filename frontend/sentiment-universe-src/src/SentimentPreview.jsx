import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { getSentiment } from './market-data.js';
import { createSentimentResources, createSentimentNode, getSentimentPhase, updateSentimentNode, setSentimentViewport, setSentimentData, disposeSentimentGraph } from './SentimentNode.js';

export function SentimentPreview({ symbol, playing, motionClock, motionSpeed=1, dataRevision=0, className='' }) {
  const host=useRef(null),refresh=useRef(null),playback=useRef({playing,motionSpeed});playback.current={playing,motionSpeed};
  useEffect(()=>{
    const container=host.current;if(!container)return;let renderer;
    try{renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,powerPreference:'low-power'});}catch{container.dataset.ready='false';return;}
    const pixelRatio=Math.min(window.devicePixelRatio||1,1.75);renderer.setPixelRatio(pixelRatio);renderer.setClearColor(0x000000,0);renderer.outputColorSpace=THREE.SRGBColorSpace;
    renderer.domElement.setAttribute('aria-hidden','true');container.prepend(renderer.domElement);
    const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(32,1,.1,20);camera.position.set(0,.05,2.65);camera.lookAt(0,0,0);
    const resources=createSentimentResources(),star=createSentimentNode(getSentiment(symbol),resources,getSentimentPhase(symbol));scene.add(star.group);
    let frame=0,width=0,height=0,dirty=true,lastTime=null,frozenTime=Number.isFinite(motionClock?.current?.value)?motionClock.current.value:0;
    const refreshData=()=>{setSentimentData(star,getSentiment(symbol));dirty=true;container.dataset.sentimentColor=star.appearance.color;container.dataset.sentimentBias=star.appearance.bias;container.dataset.sentimentDominance=String(star.appearance.dominance??'');container.dataset.sentimentAvailable=String(star.available);};refresh.current=refreshData;
    const resize=()=>{const bounds=container.getBoundingClientRect();width=bounds.width;height=bounds.height;if(width<1||height<1)return;renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix();setSentimentViewport(star,height*pixelRatio);dirty=true;};
    const observer=new ResizeObserver(resize);observer.observe(container);resize();
    function draw(){frame=requestAnimationFrame(draw);if(document.hidden||width<1||height<1)return;const sharedTime=motionClock?.current?.value;
      // The parent already applies motionSpeed. Never run or scale a second clock.
      if(playback.current.playing&&Number.isFinite(sharedTime))frozenTime=sharedTime;
      if(!dirty&&frozenTime===lastTime)return;lastTime=frozenTime;dirty=false;updateSentimentNode(star,frozenTime);renderer.render(scene,camera);
      container.dataset.motionTime=frozenTime.toFixed(6);container.dataset.beadPosition=star.bead.position.toArray().map(value=>value.toFixed(5)).join(',');}
    frame=requestAnimationFrame(draw);container.dataset.ready='true';container.dataset.orbits='0';container.dataset.sentimentColor=star.appearance.color;container.dataset.sentimentBias=star.appearance.bias;container.dataset.sentimentDominance=String(star.appearance.dominance??'');
    const contextLost=event=>{event.preventDefault();container.dataset.ready='false';};renderer.domElement.addEventListener('webglcontextlost',contextLost);
    return()=>{refresh.current=null;cancelAnimationFrame(frame);observer.disconnect();renderer.domElement.removeEventListener('webglcontextlost',contextLost);disposeSentimentGraph(scene,resources);renderer.dispose();renderer.forceContextLoss();renderer.domElement.remove();delete container.dataset.ready;};
  },[symbol,motionClock]);
  useEffect(()=>{refresh.current?.();},[dataRevision]);
  const sentiment=getSentiment(symbol);
  return <div ref={host} className={`sentiment-preview ${className}`} data-symbol={symbol} data-data-revision={dataRevision} role="img" aria-label={`ดาวพลาสมาสามมิติ ${symbol} ${sentiment.available?`Myfxbook Short ${sentiment.short}% Long ${sentiment.long}%`:'ยังไม่มีข้อมูล Myfxbook'}`}><span className="sentiment-preview-fallback">เปิดภาพดาว 3D ไม่สำเร็จ</span></div>;
}
