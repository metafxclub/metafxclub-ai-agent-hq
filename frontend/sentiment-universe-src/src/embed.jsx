import React, {Component} from 'react';
import {createRoot} from 'react-dom/client';
import {App} from './AppSentiment.jsx';
import {normalizeEmbedOptions} from './embed-options.js';
import appStyles from './sentiment.css?inline';
import sceneStyles from './orbital-scene.css?inline';
import previewStyles from './sentiment-preview.css?inline';
import fontStyles from './fonts.css?inline';
import embedStyles from './embed.css?inline';

const mounted = new WeakMap();
let fontUsers = 0, fontElement;
class MountBoundary extends Component {
  state = {failed:false,attempt:0};
  static getDerivedStateFromError(){return {failed:true};}
  render(){return this.state.failed
    ? <section className="embed-error" role="alert"><h2>เปิดกาแล็กซี่ไม่สำเร็จ</h2><p>ตรวจการเชื่อมบริการข้อมูลในเครื่อง แล้วลองเปิดหน้านี้อีกครั้ง</p><div><button onClick={()=>this.setState(state=>({failed:false,attempt:state.attempt+1}))}>ลองอีกครั้ง</button><a href={this.props.options.setupUrl} target="_blank" rel="noopener noreferrer">ตั้งค่าแหล่งข้อมูล</a></div></section>
    : <App key={this.state.attempt} {...this.props.options}/>;}
}

/** Mount one read-only galaxy. Calling again on the same host reuses it. */
export function mountSentimentUniverse(host, options={}) {
  if (!host || host.nodeType!==1) throw new Error('mount_host_required');
  if (mounted.has(host)) return mounted.get(host);
  const normalized=normalizeEmbedOptions(options,host.ownerDocument.location.origin);
  const shadow=host.shadowRoot || host.attachShadow({mode:'open'});
  const style=host.ownerDocument.createElement('style');
  style.textContent=appStyles.replaceAll(':root',':host')+'\n'+sceneStyles+'\n'+previewStyles+'\n'+embedStyles;
  const container=host.ownerDocument.createElement('div');
  container.className='sentiment-embed-root';
  container.setAttribute('role','region');container.setAttribute('aria-label','Sentiment Universe · 32 สินทรัพย์');
  shadow.replaceChildren(style,container);
  // Font faces must be registered at document scope in Chromium; visual CSS stays isolated.
  if (!fontElement) {fontElement=host.ownerDocument.createElement('style');fontElement.dataset.sentimentFonts='true';fontElement.textContent=fontStyles.replaceAll('/frontend/public/sentiment-universe/',normalized.assetBase);host.ownerDocument.head.appendChild(fontElement);}
  fontUsers++;
  const root=createRoot(container);
  let disposed=false;
  const handle={unmount(){
    if(disposed)return;disposed=true;root.unmount();shadow.replaceChildren();mounted.delete(host);
    if(--fontUsers===0){fontElement?.remove();fontElement=null;}
  }};
  mounted.set(host,handle);
  root.render(<MountBoundary options={normalized}/>);
  return handle;
}
